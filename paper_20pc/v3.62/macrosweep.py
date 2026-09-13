#!/usr/bin/env python3
"""Unused-macro sweep.

Collects every \newcommand defined in the survey_numbers*.tex macro files and
reports which are never referenced by the manuscript or by any \input fragment
it pulls in.  Usage:  python3 macrosweep.py [--all]
"""
import glob, re, sys, os

HERE = os.path.dirname(os.path.abspath(__file__))
os.chdir(HERE)

MACFILES = sorted(glob.glob("survey_numbers*.tex"))
MAIN = "technosignatures_40pc_v3.62.tex"
# everything the manuscript \inputs, plus the manuscript itself
src = open(MAIN, encoding="utf-8").read()
inputs = re.findall(r"\\input\{([^}]+)\}", src)
consumers = [MAIN] + [f if f.endswith(".tex") else f + ".tex" for f in inputs]
consumers = [c for c in consumers if os.path.exists(c) and c not in MACFILES]

body = "\n".join(open(c, encoding="utf-8").read() for c in consumers)
# strip full-line comments so a commented-out use does not count
body = re.sub(r"(?<!\\)%.*", "", body)

defs = {}
for mf in MACFILES:
    txt = open(mf, encoding="utf-8").read()
    for m in re.finditer(r"\\newcommand\{?\\([A-Za-z]+)\}?\{(.*)\}\s*$", txt, re.M):
        defs[m.group(1)] = (mf, m.group(2))

unused = []
for name, (mf, val) in sorted(defs.items()):
    if not re.search(r"\\" + name + r"(?![A-Za-z])", body):
        unused.append((name, mf, val))

print(f"macros defined: {len(defs)}   consumers: {len(consumers)}   unused: {len(unused)}")
for name, mf, val in unused:
    print(f"  UNUSED  \\{name:24s} = {val[:46]:48s} [{mf}]")
