#!/usr/bin/env python3
"""Build the current manuscript and copy its PDF into backups/."""
import argparse
import fcntl
import re
import subprocess
from datetime import datetime, timezone
from itertools import count
from pathlib import Path

root = Path(__file__).resolve().parent
parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument("unit", nargs="?", help="optional label, e.g. 3.2")
args = parser.parse_args()
if args.unit and not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9._-]{0,39}", args.unit):
    parser.error("use 1-40 letters, digits, dots, underscores or hyphens")
sources = list(root.glob("foundations_*.tex"))
if len(sources) != 1:
    parser.error("expected exactly one foundations_*.tex beside this script")
source = sources[0]
build = root / "scaffold" / "pdf-build"
build.mkdir(parents=True, exist_ok=True)
pdf = build / source.with_suffix(".pdf").name

with (build / "build.lock").open("a") as lock:
    fcntl.flock(lock, fcntl.LOCK_EX)
    original = source.read_bytes()
    previous = pdf.stat().st_mtime_ns if pdf.exists() else None
    try:
        run = subprocess.run(
            ["latexmk", "-norc", "-pdf", "-g", "-interaction=nonstopmode",
             "-halt-on-error", f"-outdir={build}", source.name],
            cwd=root, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
            text=True, errors="replace",
        )
    except FileNotFoundError:
        raise SystemExit("latexmk is required on PATH.") from None
    if run.returncode:
        raise SystemExit(run.stdout[-6000:])
    if source.read_bytes() != original:
        raise SystemExit("The source changed during compilation. Run again.")
    if not pdf.exists() or pdf.stat().st_mtime_ns == previous:
        raise SystemExit("No fresh PDF was produced. No backup was written.")
    data = pdf.read_bytes()
    if not data.startswith(b"%PDF-") or not data.rstrip().endswith(b"%%EOF"):
        raise SystemExit("The build did not produce a complete PDF.")

backups = root / "backups"
backups.mkdir(exist_ok=True)
base = f"foundations_{args.unit}" if args.unit else "foundations"
stamp = datetime.now(timezone.utc).strftime("%Y_%m_%d_%H_%M")
for n in count(1):
    suffix = "" if n == 1 else f"_{n}"
    target = backups / f"{base}{suffix}_{stamp}.pdf"
    try:
        with target.open("xb") as out:
            out.write(data)
    except FileExistsError:
        continue
    print(target)
    break
