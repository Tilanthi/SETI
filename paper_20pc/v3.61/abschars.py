#!/usr/bin/env python3
"""Rendered abstract length, as arXiv would count it.

arXiv's 1920-character limit applies to the plain-text abstract pasted into the
submission form.  The closest available proxy is the typeset abstract with line
breaks collapsed to single spaces.
"""
import re
import sys

import pymupdf

V = sys.argv[1] if len(sys.argv) > 1 else "technosignatures_40pc_v3.61.pdf"
txt = pymupdf.open(V)[0].get_text()
a = txt.index("ABSTRACT") + len("ABSTRACT")
b = txt.index("Subject headings")
s = re.sub(r"\s+", " ", txt[a:b]).strip()
print(f"rendered abstract: {len(s)} characters, {len(s.split())} words "
      f"(arXiv limit 1920, headroom {1920 - len(s)})")
if "--chars" in sys.argv:
    print(s)
