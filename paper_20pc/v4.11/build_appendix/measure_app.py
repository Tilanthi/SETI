#!/usr/bin/env python3
"""Measure the appendices in COLUMN POINTS, never in whole pages.

Whole-page counting cannot detect an appendix edit here: the document held at
60 pp through a complete rewrite of section 1.  A page of this class is two
columns of H points; a block's position has to count the column it sits in.
The appendix extent is measured from the first appendix head to the
REFERENCES head, which is the first thing after the last appendix.
"""
import re
import sys
import pymupdf

TOP, BOT = 43.8, 737.6
H = BOT - TOP
XMID = 340.0
PP = 2 * H


def load(path):
    return pymupdf.open(path)


def pos(pg, y, x):
    return (pg - 1) * PP + (0 if x < XMID else 1) * H + (y - TOP)


def heads(doc):
    """Every appendix-level head and the REFERENCES head, in document order."""
    out = []
    for p in doc:
        for b in sorted(p.get_text("blocks"), key=lambda b: (b[0] > XMID, b[1])):
            t = b[4].strip().replace("\n", " ")
            if re.match(r"^(APPENDIX|REFERENCES)\b", t) or \
               re.match(r"^[A-Z][A-Z][A-Z \-,'’:$\\]{10,}$", t):
                out.append((pos(p.number + 1, b[1], b[0]), t[:70]))
    return out


if __name__ == "__main__":
    doc = load(sys.argv[1])
    hh = heads(doc)
    # the appendix block runs from the first head at or after \appendix to
    # REFERENCES.  Anchor on the first head whose text is in the keep list,
    # or on APPENDIX itself.
    anchor = next((i for i, (_, t) in enumerate(hh)
                   if t.startswith("APPENDIX")), None)
    refs = next((p for p, t in hh if t.startswith("REFERENCES")), None)
    print("pages (for reference only): %d" % doc.page_count)
    if anchor is None or refs is None:
        for p, t in hh:
            print("  %9.1f  %s" % (p, t))
        raise SystemExit("could not find the APPENDIX / REFERENCES anchors")
    start = hh[anchor][0]
    print("appendix extent: %.1f -> %.1f = %.1f column-pt = %.3f pp"
          % (start, refs, refs - start, (refs - start) / PP))
    # per-appendix, using the heads between the anchor and REFERENCES
    seq = [(p, t) for p, t in hh[anchor:] if p <= refs]
    for i, (p, t) in enumerate(seq):
        nxt = seq[i + 1][0] if i + 1 < len(seq) else refs
        print("  %8.1f %+7.1f pt  %.3f pp  %s" % (p, nxt - p, (nxt - p) / PP, t))
