#!/usr/bin/env python3
"""Phase 0 of the round-9 rewrite: split the monolithic manuscript into one
file per section, leaving a main .tex that is a preamble plus \\input lines.

The split is defined by a table of 1-based line boundaries over the ORIGINAL
file.  Before anything is written the script asserts that the chunks, in
order, reproduce the original file byte for byte -- so the only way the PDF
can change is through \\input itself, and that is what the byte-identity test
of the PDF then measures.

Every \\input is written with a trailing % so TeX does not insert the
end-of-line space that would otherwise follow the closing brace.  Section
files are therefore concatenated by TeX exactly as they were adjacent lines.

Run once, from this directory.  Idempotent only in the sense that it refuses
to run twice (it checks for sections/).
"""
import hashlib
import os
import sys

import manuscript
# ★ The manuscript's filename carries the version, so hard-coding it here made
# this tool silently follow a stale file at every version bump -- and twice it
# failed LATE, at the end of a full run, because nothing reaches it earlier.
# `manuscript.main_file()` asserts there is exactly one manuscript .tex in the
# directory and returns it, so a bump is now a rename and nothing else.
SRC = manuscript.main_file()
OUT = "sections"

# (first_line, last_line, kind, name)
#   kind 'main'    -> stays in the main file verbatim
#   kind 'section' -> moves to sections/<name>.tex, replaced by \input
PLAN = [
    (1,    180,  "main",    None),                      # preamble, title, authors
    (181,  222,  "section", "abstract"),                # abstract + keywords
    (223,  223,  "main",    None),                      # \enlargethispage (layout)
    (224,  312,  "section", "01_intro"),
    (313,  408,  "section", "02_background"),
    (409,  554,  "section", "03_sample"),
    (555,  1133, "section", "04_method"),
    (1134, 1969, "section", "05_results"),
    (1970, 2114, "section", "05b_stack"),
    (2115, 2393, "section", "05c_limits"),
    (2394, 2649, "section", "06_discussion"),
    (2650, 2759, "section", "07_conclusions"),
    (2760, 2831, "section", "08_backmatter"),
    (2832, 2833, "main",    None),                      # \appendix
    (2834, 2890, "section", "app_00_overview"),
    (2891, 3469, "section", "app_A_reproducibility"),
    (3470, 3560, "section", "app_B_figofmerit"),
    (3561, 3683, "section", "app_C_spatialnorm"),
    (3684, 4005, "section", "app_D_externalchecks"),
    (4006, 4130, "section", "app_E_notation"),
    (4131, 4383, "section", "app_F_freqconventions"),
    (4384, 4794, "section", "app_G_injection"),
    (4795, 4842, "section", "app_H_pertarget"),
    (4843, 4907, "section", "app_I_linemask"),
    (4908, 5384, "section", "app_J_falsealarm"),
    (5385, 6138, "section", "app_K_provenance"),
    (6139, 6313, "section", "app_L_recommendations"),
    (6314, 6683, "section", "app_M_repaired"),
    (6684, 6872, "section", "app_N_rfi"),
    (6873, None, "main",    None),                       # bibliography, \end{document}
]

raw = open(SRC, encoding="utf-8").read()
lines = raw.split("\n")
# raw.split('\n') yields one trailing '' for a file ending in a newline; keep
# the exact token list and rebuild with '\n'.join so reassembly is exact.
NL = len(lines)

chunks = []
for first, last, kind, name in PLAN:
    lo = first - 1
    hi = NL if last is None else last
    chunks.append((lo, hi, kind, name))

# --- assertion 1: the plan is a contiguous, non-overlapping cover ---------
assert chunks[0][0] == 0, chunks[0]
for (a, b, _, _), (c, d, _, _) in zip(chunks, chunks[1:]):
    assert b == c, ("gap or overlap at", b, c)
assert chunks[-1][1] == NL, (chunks[-1][1], NL)

# --- assertion 2: reassembly is byte-exact -------------------------------
reassembled = "\n".join(sum([lines[a:b] for a, b, _, _ in chunks], []))
assert reassembled == raw, "chunking is not byte-exact"

# --- assertion 3: no chunk ends on a line that would change tokenisation --
# A chunk whose last line ends in an unterminated comment (%) or inside a
# braced group would be joined differently after the split.
for a, b, kind, name in chunks:
    if kind != "section":
        continue
    tail = lines[b - 1]
    assert not tail.rstrip().endswith("%"), (name, "ends in a comment", tail)
    body = "\n".join(lines[a:b])
    assert body.count("{") == body.count("}"), (name, "unbalanced braces")

if os.path.isdir(OUT):
    sys.exit("%s/ already exists -- refusing to re-split" % OUT)
os.makedirs(OUT)

main = []
for a, b, kind, name in chunks:
    if kind == "main":
        main.extend(lines[a:b])
    else:
        text = "\n".join(lines[a:b])
        with open(os.path.join(OUT, name + ".tex"), "w", encoding="utf-8") as fh:
            fh.write(text + "\n")
        main.append("\\input{%s/%s}%%" % (OUT, name))

with open(SRC, "w", encoding="utf-8") as fh:
    fh.write("\n".join(main))

print("split: %d section files, main now %d lines (was %d)"
      % (sum(1 for c in chunks if c[2] == "section"), len(main), NL))
print("orig sha256 %s" % hashlib.sha256(raw.encode()).hexdigest()[:16])
