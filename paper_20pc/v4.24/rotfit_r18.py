#!/usr/bin/env python3
"""THE LANDSCAPE FLOAT MUST BE ON THE PAGE.  (round 18)

    python3 rotfit_r18.py [paper.pdf] [--drive N]

★★★★ WHY THIS EXISTS.  The crossing ledger is a `sidewaystable*`, and
`rotating` places a rotated double float inside `\\hbox to \\hsize`.  Under this
revtex-derived class `\\hsize` is still the COLUMN width when that box is
placed, so the float was centred on column one instead of on the page.  In the
build shipped before this round the ledger's caption began at x = -5.9 pt --
off the left edge of the paper, with the first word or two missing from every
line of a nineteen-line caption -- and 133 pt of the page's width stood empty
on the right.

**Nothing in the build could see it.**  Rotation hides the overflow from
`Overfull \\hbox`; `pdflatex` reported no error, no warning and no overfull box;
the suite passed six consecutive times on that PDF.  A defect that is invisible
to every gate is exactly the defect that reaches a reader, so this measures the
one thing that matters: ink on the page, against the text block.

Clauses:
  R1  INK IN THE BLOCK.  On every page carrying rotated text, all ink -- text
      blocks and rules alike -- lies inside the text block, within TOL.
  R2  NOT VACUOUS.  At least `MINROT` page carries rotated text.  Without this
      clause the gate passes a paper whose landscape table has vanished, which
      is a worse failure than the one it was written for.
  R3  THE BLOCK IS WHERE THE CLASS PUTS IT.  The text block used by R1 is not
      typed: it is measured from the upright pages' own body text and then
      checked against the class's geometry, so a change of class cannot leave
      this gate measuring a page that does not exist.

Drives (each must FAIL on its own):
  1  the allowed block narrowed by 200 pt            -> R1
  2  a rotated page counted where the paper has none -> R2
     (it used to DISABLE the detector, which fired R2 while the expectation
      was "at least one"; against a declared zero that drive passes, and a
      drive that stops driving is a failure dressed as a pass)
  3  the measured block asserted against wrong class geometry -> R3
"""
import os
import sys
from collections import Counter

import pymupdf

HERE = os.path.dirname(os.path.abspath(__file__))
TOL = 1.0                       # pt: a rule's own line width, no more
# ★★★ v4.21: THE CROSSING LEDGER IS UPRIGHT AND THIS PAPER HAS NO LANDSCAPE
# FLOAT AT ALL, so the expected count is DECLARED rather than assumed to be
# at least one.  Two-sided on purpose: a rotated page appearing is as much a
# change as a rotated page vanishing, and R1 measures the ink on any that do.
NROT_EXPECTED = 0               # was 1, the crossing ledger (sidewaystable*)
CLASS_LEFT, CLASS_RIGHT = 50.74, 561.99      # openjournal.cls, 513.12 pt wide
CLASS_TOP, CLASS_BOT = 43.84, 737.60
GEOM_TOL = 2.0


def main(argv):
    drive = 0
    pdf = None
    for i, a in enumerate(argv):
        if a == '--drive':
            drive = int(argv[i + 1])
        elif a.endswith('.pdf'):
            pdf = a
    if pdf is None:
        cand = [f for f in os.listdir(HERE)
                if f.startswith('technosignatures_') and f.endswith('.pdf')]
        if len(cand) != 1:
            print('rotfit: FAIL expected exactly one manuscript pdf, found %s'
                  % cand)
            return 1
        pdf = os.path.join(HERE, cand[0])
    doc = pymupdf.open(pdf)

    # R3 -- the text block, measured from the upright pages themselves.
    lefts, rights = Counter(), Counter()
    for p in doc:
        for blk in p.get_text('dict')['blocks']:
            if blk['type'] != 0:
                continue
            up = [ln for ln in blk['lines'] if abs(ln['dir'][1]) < 0.5]
            if len(up) < 3:
                continue
            lefts[round(blk['bbox'][0], 1)] += 1
            rights[round(blk['bbox'][2], 1)] += 1
    left = min(k for k, n in lefts.items() if n >= 5)
    right = max(k for k, n in rights.items() if n >= 5)
    want_l, want_r = CLASS_LEFT, CLASS_RIGHT
    if drive == 3:
        want_l, want_r = 72.0, 540.0
    bad = []
    if abs(left - want_l) > GEOM_TOL or abs(right - want_r) > GEOM_TOL:
        bad.append('R3 the body text measures %.2f--%.2f pt where the class '
                   'puts it at %.2f--%.2f' % (left, right, want_l, want_r))
    print('rotfit R3 text block measured from %d upright blocks: '
          '%.2f--%.2f pt (class %.2f--%.2f)'
          % (sum(lefts.values()), left, right, CLASS_LEFT, CLASS_RIGHT))

    lo, hi = left - TOL, right + TOL
    if drive == 1:
        lo, hi = lo + 100, hi - 100

    nrot = 0
    for p in doc:
        d = p.get_text('dict')
        rot, x0, x1, y0, y1 = 0, 1e9, -1e9, 1e9, -1e9
        for blk in d['blocks']:
            if blk['type'] != 0:
                continue
            for ln in blk['lines']:
                if abs(ln['dir'][1]) > 0.5:
                    rot += 1
            if drive == 2:        # R2: a rotated page where there is none
                rot += 10
            if blk['bbox'][1] > CLASS_BOT - 10:
                continue                      # the folio line, below the block
            x0, x1 = min(x0, blk['bbox'][0]), max(x1, blk['bbox'][2])
            y0, y1 = min(y0, blk['bbox'][1]), max(y1, blk['bbox'][3])
        if rot < 10:
            continue
        nrot += 1
        for dr in p.get_drawings():
            r = dr['rect']
            x0, x1 = min(x0, r.x0), max(x1, r.x1)
            y0, y1 = min(y0, r.y0), max(y1, r.y1)
        ok = x0 >= lo and x1 <= hi
        print('rotfit R1 p.%-3d rotated lines %-4d ink x %.2f--%.2f pt  %s'
              % (p.number + 1, rot, x0, x1, 'ok' if ok else 'OUTSIDE THE PAGE'))
        if not ok:
            bad.append('R1 p.%d: ink runs from %.2f to %.2f pt against a text '
                       'block of %.2f--%.2f -- %.2f pt of the float is off the '
                       'block, and at the left edge that is off the paper'
                       % (p.number + 1, x0, x1, lo, hi,
                          max(lo - x0, 0) + max(x1 - hi, 0)))
    if nrot != NROT_EXPECTED:
        bad.append('R2 %d page(s) carry rotated text against the declared %d. '
                   'A gate that measures no landscape float passes every '
                   'paper, so the count is declared in both directions: if a '
                   'landscape float has been added, set NROT_EXPECTED and '
                   'read R1 above for its geometry; if one has vanished, it '
                   'has vanished.' % (nrot, NROT_EXPECTED))
    print('rotfit: %d landscape page(s); %s'
          % (nrot, 'PASS' if not bad else 'FAIL'))
    for b in bad:
        print('   ' + b)
    return 1 if bad else 0


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
