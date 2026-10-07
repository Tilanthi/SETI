#!/usr/bin/env python3
"""Rendered abstract length, as arXiv would count it.

arXiv's 1920-character limit applies to the plain-text abstract pasted into the
submission form.  The closest available proxy is the typeset abstract with line
breaks collapsed to single spaces.
"""
import re
import sys

import pymupdf

import manuscript
# ★ The manuscript's filename carries the version, so hard-coding it here made
# this tool silently follow a stale file at every version bump -- and twice it
# failed LATE, at the end of a full run, because nothing reaches it earlier.
# `manuscript.main_file()` asserts there is exactly one manuscript .tex in the
# directory and returns it, so a bump is now a rename and nothing else.
V = (sys.argv[1] if len(sys.argv) > 1
     else manuscript.main_file()[:-4] + '.pdf')
txt = pymupdf.open(V)[0].get_text()
a = txt.index("ABSTRACT") + len("ABSTRACT")
b = txt.index("Subject headings")
s = re.sub(r"\s+", " ", txt[a:b]).strip()
print(f"rendered abstract: {len(s)} characters, {len(s.split())} words "
      f"(arXiv limit 1920, headroom {1920 - len(s)})")
if "--chars" in sys.argv:
    print(s)
