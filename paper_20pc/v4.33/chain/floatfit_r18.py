#!/usr/bin/env python3
r"""A FLOAT TOO LARGE FOR ITS PAGE IS A BUILD FAILURE.  (round 18)

    python3 floatfit_r18.py [paper.pdf] [--log paper.log] [--drive N]

★★★★ WHY THIS EXISTS, and why it is not the overfull-box gate.

`latexlog` fails the build on `Overfull \hbox` and `Overfull \vbox`, because
Glenn saw an 0.8 pt overfull vbox printed as a table over the paragraph
beneath it.  `LaTeX Warning: Float too large for page by X pt` is a different
message, it was in no gate, and **two of them fired on every build of v4.19**:

  * Table 3, the terminology table, overran its column by **54.38 pt**, and in
    the PDF that overrun is ink down to y = 788.3 pt on a 792 pt page --
    **3.7 pt from the physical bottom edge of the paper**, 50 pt below the
    text block and straight through where a folio would sit;
  * Table A2, the survey ledger's second part, overran by **21.94 pt**.

Neither produced an error, an overfull box, or a mark in any gate: the paper
was printing a table off the bottom of the page and the suite passed.  That is
the same family as the clipped landscape caption `rotfit_r18.py` was written
for -- ink outside the area a reader's page can hold -- so this gate measures
both the warning and the ink.

Clauses:
  F1  THE LOG.  No `Float too large for page` anywhere in it.  This is the
      authoritative signal: LaTeX itself says the float did not fit.
  F2  THE PAPER.  No ink -- text, rule, or placed figure -- comes within
      EDGE pt of any physical edge of any page.  EDGE is a printer's safety
      band, not a tuned number: a page trimmed or bound loses a few points,
      and a caption at x = -5.9 pt or a table at y = 788.3 pt on a 792 pt page
      is off the paper whatever the text block is.  F2 is measured against the
      MEDIA BOX, so it cannot be defeated by a change of class geometry, and
      it catches the cases that reach the PDF without a warning at all.
  F3  NOT VACUOUS.  The log must report a page count, it must equal the PDF's,
      and every page must carry ink that F2 actually measured.  Without this a
      gate reading a stale or empty log passes anything -- which is how this
      tree acquired twenty gates that could not fail.

Drives (each must FAIL on its own):
  1  one synthetic `Float too large` line added to a copy of the log  -> F1
  2  the safety band widened to 60 pt, so real ink is outside it      -> F2
  3  the page count hidden from the log copy                          -> F3
★ And the proof that matters: run against the build this round started from
  (`referee_r18/appread/BEFORE_v419.{pdf,log}`) it reports both floats and the
  788.3 pt ink, and exits 1.
"""
import os
import re
import sys

import numpy as np
import pymupdf

HERE = os.path.dirname(os.path.abspath(__file__))
EDGE = 20.0             # pt of printer's safety band at every physical edge


def ink_bbox(page):
    """Every piece of ink on the page, measured as PIXELS.

    ★ The object model is the wrong instrument here and the reason is on
    record: every figure in this paper is a PDF drawing placed as a Form
    XObject, `get_image_info()` sees nothing at all for those, `get_drawings()`
    does not enter a form's own content stream, and the bbox in
    `get_xobjects()` is in the FORM's coordinates -- `geomfp.py` uses it for
    size and explicitly not for position.  A gate built on any of those would
    report "no ink anywhere near the edge" for a figure printed off the page,
    which is this project's commonest defect.  Rendering the page and finding
    the non-white pixels makes no assumption about what put them there: text,
    rule, glyph, figure and rotated caption are all simply ink.  At 72 dpi one
    pixel is one point, which is the precision the warning itself reports.
    """
    pix = page.get_pixmap(dpi=72, colorspace=pymupdf.csGRAY)
    a = np.frombuffer(pix.samples, dtype=np.uint8).reshape(pix.height,
                                                           pix.width)
    ys, xs = np.where(a < 250)
    if not len(xs):
        return None
    sx = page.rect.width / pix.width
    sy = page.rect.height / pix.height
    return (page.rect.x0 + xs.min() * sx, page.rect.y0 + ys.min() * sy,
            page.rect.x0 + (xs.max() + 1) * sx,
            page.rect.y0 + (ys.max() + 1) * sy)


def main(argv):
    drive = 0
    pdf = log = None
    for i, a in enumerate(argv):
        if a == '--drive':
            drive = int(argv[i + 1])
        elif a == '--log':
            log = argv[i + 1]
        elif a.endswith('.pdf'):
            pdf = a
    if pdf is None:
        cand = [f for f in os.listdir(HERE)
                if f.startswith('technosignatures_') and f.endswith('.pdf')]
        if len(cand) != 1:
            print('floatfit: FAIL expected exactly one manuscript pdf, '
                  'found %s' % cand)
            return 1
        pdf = os.path.join(HERE, cand[0])
    if log is None:
        log = pdf[:-4] + '.log'
    if not os.path.exists(log):
        print('floatfit: FAIL no log beside the pdf (%s): a float gate with no '
              'log is a gate that cannot fail' % log)
        return 1

    txt = open(log, errors='ignore').read()
    if drive == 1:
        txt += '\nLaTeX Warning: Float too large for page by 9.9pt on input '\
               'line 1.\n'
    if drive == 3:
        txt = txt.replace('Output written', 'Output suppressed')
    band = EDGE if drive != 2 else 60.0

    bad = []
    # ---------------------------------------------------------------- F1
    fl = re.findall(r'Float too large for page by [0-9.]+ *pt[^\n]*', txt)
    print('floatfit F1 log: %d "Float too large for page" warning(s)'
          % len(fl))
    for f in fl:
        print('    ' + f.strip())
        bad.append('F1 ' + f.strip())

    # ---------------------------------------------------------------- F2/F3
    doc = pymupdf.open(pdf)
    pg = re.findall(r'Output written[^(]*\((\d+) pages', re.sub(r'\s+', ' ',
                                                                txt))
    measured, worst = 0, []
    for p in doc:
        mb = p.rect
        bb = ink_bbox(p)
        if bb is None:
            bad.append('F3 p.%d carries no ink this gate can measure'
                       % (p.number + 1))
            continue
        measured += 1
        x0, y0, x1, y1 = bb
        clear = min(x0 - mb.x0, y0 - mb.y0, mb.x1 - x1, mb.y1 - y1)
        worst.append((clear, p.number + 1, bb))
        if clear < band:
            bad.append('F2 p.%d: ink runs x %.1f--%.1f, y %.1f--%.1f on a '
                       '%.0fx%.0f pt page -- %.1f pt from the paper\'s edge, '
                       'inside the %.0f pt safety band'
                       % (p.number + 1, x0, x1, y0, y1, mb.width, mb.height,
                          clear, band))
    worst.sort()
    for clear, n, bb in worst[:3]:
        print('floatfit F2 closest to an edge: p.%-3d %.1f pt clear '
              '(ink y to %.1f)' % (n, clear, bb[3]))
    print('floatfit F3 pages: log %s, pdf %d, measured %d'
          % (pg or 'NOT REPORTED', doc.page_count, measured))
    if not pg:
        bad.append('F3 the log reports no page count: it is stale, truncated '
                   'or from a failed run, and nothing above was checked '
                   'against the document that was built')
    elif int(pg[-1]) != doc.page_count:
        bad.append('F3 the log built %s pages and the pdf holds %d: the two '
                   'are not the same build' % (pg[-1], doc.page_count))
    if doc.page_count < 2 or measured != doc.page_count:
        bad.append('F3 measured %d of %d pages' % (measured, doc.page_count))

    print('floatfit: %s' % ('ALL CLAUSES PASS' if not bad
                            else '%d FAIL' % len(bad)))
    for b in bad:
        print('   ' + b)
    return 1 if bad else 0


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
