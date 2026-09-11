#!/usr/bin/env python3
"""Retire generated macros that the manuscript does not reference.

The v3.44 referee round found 31 of the 129 round-13 macros unused, six of
them the archive audit that never reached the reader.  Those are now used.
This step closes the remaining hygiene: it deletes, from the generated
`survey_numbers*.tex` files, every `\newcommand` that no `.tex` file in this
folder references.  The generators keep computing the quantities, so nothing
is lost and re-enabling one means deleting a name from the report below.

Run last in `make_all.sh`, after every generator has written its file.
It refuses to remove a macro that is referenced anywhere, so it cannot break
a build; run `macrosweep.py` afterwards to confirm zero orphans remain.
"""
import glob, os, re, sys

HERE = os.path.dirname(os.path.abspath(__file__))
os.chdir(HERE)

MACFILES = sorted(glob.glob("survey_numbers*.tex"))
CONSUMERS = [f for f in glob.glob("*.tex") + glob.glob("tables/*.tex")
             if os.path.basename(f) not in MACFILES]

body = ""
for c in CONSUMERS:
    body += re.sub(r"(?<!\\)%.*", "", open(c, encoding="utf-8").read()) + "\n"

used = set(re.findall(r"\\([A-Za-z]+)", body))

total = removed = 0
report = []
for mf in MACFILES:
    lines = open(mf, encoding="utf-8").read().splitlines(True)
    keep, drop = [], []
    for ln in lines:
        m = re.match(r"\\newcommand\{?\\([A-Za-z]+)\}?\{", ln)
        if m:
            total += 1
            if m.group(1) not in used:
                drop.append(m.group(1))
                continue
        keep.append(ln)
    if drop:
        removed += len(drop)
        report.append((mf, drop))
        with open(mf, "w", encoding="utf-8") as fh:
            fh.write("".join(keep))
            fh.write("%% retired by retire_macros.py (unreferenced): %s\n"
                     % ", ".join(sorted(drop)))

print("macros written %d, retired %d as unreferenced" % (total, removed))
for mf, drop in report:
    print("  %-32s %2d: %s" % (mf, len(drop), ", ".join(sorted(drop))))
