#!/usr/bin/env python3
"""Locate a manuscript label and find its explicit LaTeX references."""
import argparse
import re
from pathlib import Path

parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument("label", help="semantic label, e.g. prop:joint-action-law")
args = parser.parse_args()
sources = list(Path(__file__).resolve().parent.glob("foundations_*.tex"))
if len(sources) != 1:
    parser.error("expected exactly one foundations_*.tex beside this script")
source = sources[0]
lines = source.read_text(encoding="utf-8").splitlines()

key = re.escape(args.label)
definition = re.compile(r"\\label\s*\{" + key + r"\}")
reference = re.compile(
    r"\\(?:eqref|ref|pageref|nameref)\*?\s*\{" + key + r"\}"
    r"|\\hyperref\s*\[" + key + r"\]"
)
definitions = []
references = []
for number, line in enumerate(lines, 1):
    text = re.split(r"(?<!\\)%", line, maxsplit=1)[0]
    if definition.search(text):
        definitions.append(number)
    if reference.search(text):
        references.append((number, text.strip()))

if not definitions:
    parser.exit(1, f"No literal label {args.label!r} in {source.name}.\n")
print(f"{args.label} — {len(definitions)} definition(s)")
for number in definitions:
    print(f"  {source}:{number}")
print(f"\nExplicit reference lines: {len(references)}")
for number, text in references:
    print(f"  {source}:{number}  {text}")
