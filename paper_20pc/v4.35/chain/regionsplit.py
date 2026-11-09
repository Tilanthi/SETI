#!/usr/bin/env python3
"""Measure the page budget by region, COLUMN-AWARE.  The measurement of record.

WHY THIS FILE EXISTS (round 25, Ruling 11)

    `pagesplit.py` linearises a page as ONE column height:
    `flow = (page-1)*H + (y - TOP)`.  On a two-column page that is wrong by
    construction, because a boundary at the top of the RIGHT-hand column
    scores the same offset as one half-way down the LEFT.  Over four large
    regions it is tolerable; over a length pass it is not, and in round 25 it
    was not: run on a build that had demonstrably shrunk, `pagesplit` reported
    the main text GROWING and the back matter losing three quarters of itself,
    and taken at face value it would have reversed a correct cut.

    This file charges a two-column page as 2H of column material:

        flow = (page-1)*2H + column*H + (y - TOP)

    where `column` is 0 for the left column and 1 for the right, decided from
    the x of the block rather than from the page.  A full-width float is
    therefore charged at twice its height, which is what it costs the reader
    and what it costs the page budget -- the thing `pagesplit` undercharges by
    half.  A single-column page (the title page, and any page the class sets
    one-column) is charged as H.

    ★ THE PROJECT'S RULE AFTER THIS ROUND: no page claim is made from one
    tool.  This prints its own total beside `pagesplit.py`'s linearisation of
    the same PDF and the percentage they differ by, because three page-measuring
    tools in three rounds have each been wrong in a different way
    (`secbudget.json` stale, `secbudget.py` misattributing once a float moves,
    `pagesplit.py` column-blind).  Two numbers that agree are evidence; one
    number is an assertion.

Usage:  regionsplit.py [manuscript.pdf]
"""
import re
import sys

import pymupdf

import manuscript

V = (sys.argv[1] if len(sys.argv) > 1
     else manuscript.main_file()[:-4] + '.pdf')
doc = pymupdf.open(V)

TOP, BOT = 43.8, 737.6
H = BOT - TOP


def _page_width(p):
    return p.rect.width


def two_column(p):
    """A page is two-column where text blocks occupy two separated x bands.

    Decided from the blocks, never from the page number: the class sets the
    title page one-column, sets a full-width float's page one-column in part,
    and `\\onecolumn` may appear anywhere.  The test is whether any block
    starts right of the mid-line AND any block starts left of it while ending
    left of the mid-line -- i.e. there is material that does not span.
    """
    mid = _page_width(p) / 2.0
    left = right = False
    for b in p.get_text('blocks'):
        x0, x1 = b[0], b[2]
        if x1 < mid + 1.0:
            left = True
        elif x0 > mid - 1.0:
            right = True
    return left and right


def column_of(p, x0, x1):
    """0 for the left column, 1 for the right, 0 for a spanning block."""
    mid = _page_width(p) / 2.0
    if x0 > mid - 1.0:
        return 1
    return 0


PAGECOLS = {p.number + 1: (2 if two_column(p) else 1) for p in doc}


def _cum(pageno):
    """Column material before page `pageno` starts, in points."""
    return sum(PAGECOLS[q] * H for q in range(1, pageno))


def pos(pg, y, col=0):
    return _cum(pg) + col * H + (y - TOP)


def find(pattern):
    for p in doc:
        for b in p.get_text('blocks'):
            t = b[4].strip().replace('\n', ' ')
            if re.match(pattern, t):
                return p.number + 1, b[1], column_of(p, b[0], b[2])
    return None, None, None


pg_ack, y_ack, c_ack = find(r'ACKNOWLEDGEMENTS\b')
pg_app, y_app, c_app = find(r'APPENDICES\b|APPENDIX A\b|APPENDIX$')
pg_ref, y_ref, c_ref = find(r'REFERENCES\b')
for nm, pg in (('ACKNOWLEDGEMENTS', pg_ack), ('APPENDIX', pg_app),
               ('REFERENCES', pg_ref)):
    assert pg is not None, (
        'regionsplit: the %s heading was not found in %s, so the regions '
        'cannot be bounded.  A measurement that silently measures nothing '
        'reports a budget for a paper it never saw.' % (nm, V))

N = len(doc)
_last = doc[N - 1]
_lastcol = max(column_of(_last, b[0], b[2]) for b in _last.get_text('blocks'))
_lasty = max(b[3] for b in _last.get_text('blocks')
             if column_of(_last, b[0], b[2]) == _lastcol)
end = pos(N, _lasty, _lastcol)

marks = [('main text (S1-Conclusions)', 0.0, pos(pg_ack, y_ack, c_ack)),
         ('back matter', pos(pg_ack, y_ack, c_ack), pos(pg_app, y_app, c_app)),
         ('appendices', pos(pg_app, y_app, c_app), pos(pg_ref, y_ref, c_ref)),
         ('bibliography', pos(pg_ref, y_ref, c_ref), end)]

#: A "page" for the budget is a PRINTED page, i.e. 2H of column material
#: where the page is two-column.  The totals below are in printed pages, so
#: they are comparable with the referees' instructions and with the PDF's own
#: page count -- which is what the budget is about.
PP = 2.0 * H

print('%s: %d printed pages; column height %.0f pt; '
      '%d two-column page(s), %d one-column'
      % (V, N, H, sum(1 for v in PAGECOLS.values() if v == 2),
         sum(1 for v in PAGECOLS.values() if v == 1)))
for name, a, b in marks:
    print('  %-28s %5.2f pp  (%8.1f pt of column)' % (name, (b - a) / PP, b - a))
print('  %-28s %5.2f pp' % ('TOTAL', end / PP))

#: ★ the cross-check, printed every time.  `pagesplit.py`'s linearisation of
#: the same PDF, so that the two numbers are in one place and a disagreement
#: is visible at the moment the measurement is made rather than a round later.
_pl = {}
for name, pat in (('main text (S1-Conclusions)', None),):
    pass
_lin_end = (N - 1) * H + max(b[3] for b in doc[N - 1].get_text('blocks')) - TOP


def _linpos(pg, y):
    return (pg - 1) * H + (y - TOP)


_lin = [('main text (S1-Conclusions)', 0.0, _linpos(pg_ack, y_ack)),
        ('back matter', _linpos(pg_ack, y_ack), _linpos(pg_app, y_app)),
        ('appendices', _linpos(pg_app, y_app), _linpos(pg_ref, y_ref)),
        ('bibliography', _linpos(pg_ref, y_ref), _lin_end)]
print('  -- cross-check against the column-blind linearisation '
      '(pagesplit.py\'s) --')
for (name, a, b), (_n2, a2, b2) in zip(marks, _lin):
    mine, theirs = (b - a) / PP, (b2 - a2) / H
    d = 100.0 * (mine - theirs) / theirs if theirs else float('nan')
    print('  %-28s %5.2f pp here against %5.2f pp there  (%+6.1f %%)'
          % (name, mine, theirs, d))
print('  %-28s %5.2f pp here against %5.2f pp there; the PDF has %d'
      % ('TOTAL', end / PP, _lin_end / H, N))
