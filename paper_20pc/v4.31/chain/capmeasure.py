#!/usr/bin/env python3
"""Measure every caption's length in PRINTED LINES, on the built page.

WHY THIS FILE EXISTS (round 25, Blocker 3 and Blocker 4)

    The author's instruction about captions is explicit and repeated:

        "The table captions are too long -- they should be no more than
         about 3 lines ... If you need the extra text, it has to go into
         the main paper ... but it cannot stay as it is."

    He named eleven tables by hand.  Round 25 shortened them, verified the
    result **in characters**, and shipped three of those eleven at 16, 16 and
    15 printed lines -- because a character count cannot express a limit
    stated in lines, any more than a source-line count can express a page
    budget.  Two of fourteen table captions were inside the limit on the
    build that was handed back as compliant.

    ★★★★ AND IT WAS THE ONLY CONSTRAINT IN THIS BUILD WITH NO GATE AT ALL.
    `gate.sh` runs 38 suites.  The author's most explicit and most often
    repeated instruction was enforced by nobody, so it could not go red, and
    a hand-back could record it as met while the page disagreed.  That is
    what this file is for.

HOW IT MEASURES, AND THE THREE TRAPS IT AVOIDS

 1. ★ A PRINTED LINE IS A BASELINE, NOT AN EXTRACTOR LINE.  `get_text`
    splits a justified line at a wide inter-word gap and returns two "lines"
    at the same y, and it splits a line again wherever a span changes font
    (every inline $\\sigma_\\varpi/\\varpi$ does this).  Counting extractor
    lines therefore overcounts.  This counts DISTINCT BASELINES, quantised
    to 1 pt, which is the number of lines a reader sees.

 2. ★★ A TABLE CAPTION ENDS AT THE TOP RULE, AND THE RULE IS ON THE PAGE.
    The caption and the first body row are set in the same font at the same
    left margin, so no font or indentation test separates them; a naive scan
    runs on into the tabular and reports a 40-line caption.  The boundary is
    drawn, not written: this takes the first horizontal rule below the label
    whose x-range overlaps the caption's own column.  A table with no rule
    at all is an error here rather than a zero.

 3. ★ A CAPTION IS CONFINED TO ITS COLUMN.  Tables 5 and 6 begin at the SAME
    y on the same page, one per column.  Any measurement that bands by y
    alone merges them.  Every line is tested against the caption's own x
    band.

WHAT IT PINS

    THE LIMIT, never today's line counts.  `--limit N` (default 3) is the
    author's number; the pass/fail list is recomputed from the page every
    run.  A caption that needs to exceed it must be named in
    `capmeasure_allow.txt` WITH A WRITTEN REASON on the same line -- an
    exception that cannot be justified in a sentence is not an exception --
    and the gate fails if an allowance exists for a caption that is now
    inside the limit, so the allow list cannot quietly become a licence.

    ★ This is the discipline round 24 and round 25 arrived at the hard way:
    five gates were found pinning the exact wording they protected, one of
    them the clause a referee had asked us to change.  A gate may pin that a
    caption is short.  It may not pin what the caption says.

Usage:
    capmeasure.py [manuscript.pdf] [--limit 3] [--figlimit 6] [--all]
    capmeasure.py --selfdrive        # lengthen one caption, show the FAIL
"""
import argparse
import os
import re
import sys

import pymupdf

HERE = os.path.dirname(os.path.abspath(__file__))

AP = argparse.ArgumentParser()
AP.add_argument('pdf', nargs='?')
AP.add_argument('--limit', type=int, default=3,
                help="the author's limit on a table caption, in printed lines")
AP.add_argument('--figlimit', type=int, default=6,
                help='the limit applied to figure captions, which Referee 1 '
                     'asked be shortened without naming a number')
AP.add_argument('--all', action='store_true',
                help='print every caption, not only those over the limit')
AP.add_argument('--selfdrive', action='store_true',
                help='demonstrate that this gate can fail: measure against a '
                     'limit of 0, which every caption must exceed')
ARGS = AP.parse_args()

if ARGS.pdf:
    PDF = ARGS.pdf
else:
    sys.path.insert(0, HERE)
    import manuscript
    PDF = os.path.join(HERE, manuscript.main_file()[:-4] + '.pdf')

DOC = pymupdf.open(PDF)

#: Caption font size.  Derived from the document rather than typed: the body
#: is the largest size that appears on more than half the pages, and a
#: caption is set smaller than the body.  A typed 7.97 would go silently
#: vacuous the day the class changes its caption size.
_sizes: dict = {}
for _p in DOC:
    for _b in _p.get_text('dict')['blocks']:
        if _b.get('type'):
            continue
        for _l in _b['lines']:
            for _s in _l['spans']:
                _sizes[round(_s['size'], 2)] = _sizes.get(
                    round(_s['size'], 2), 0) + len(_s['text'])
BODY = max(_sizes, key=lambda k: _sizes[k])
#: ★ The caption size is the one BELOW the body that carries the most text,
#: not the largest one below it: this document also sets section headings,
#: table column heads and footnotes smaller than the body, and taking the
#: largest of those picked an 8.97 pt run of 3,543 characters over the
#: 7.97 pt run of 27,270 that is actually the captions -- after which the
#: label test matched nothing and the gate reported no captions at all.
#: It asserted rather than passing, which is the only reason this was a
#: five-minute defect.
CAPSZ = sorted((_sizes[s], s) for s in _sizes if s < BODY - 0.5)
assert CAPSZ and CAPSZ[-1][0] > 2000, (
    'no font smaller than the %.2f pt body carries enough text to be the '
    'caption size: the font test would pass vacuously' % BODY)
CAP = CAPSZ[-1][1]

TABLAB = re.compile(r'^(?:TABLE|Table)\s+([A-F]?\d+)$')
FIGLAB = re.compile(r'^(?:Fig\.|Figure)\s*([A-F]?\d+)\s*\.\s*[—–-]')


def _lines(page):
    """Every text line of a page as (y, x0, x1, maxsize, text)."""
    out = []
    for b in page.get_text('dict')['blocks']:
        if b.get('type'):
            continue
        for l in b['lines']:
            t = ''.join(s['text'] for s in l['spans'])
            if not t.strip():
                continue
            out.append((l['bbox'][1], l['bbox'][0], l['bbox'][2],
                        max(round(s['size'], 2) for s in l['spans']), t))
    out.sort()
    return out


def _rules(page):
    """Horizontal rules as (y, x0, x1).  A table's top rule is one of these."""
    out = []
    for d in page.get_drawings():
        r = d['rect']
        if r.width > 40 and r.height < 2.5:
            out.append((r.y0, r.x0, r.x1))
    out.sort()
    return out


def _band(page, x0, x1):
    """The column x band a caption at x0..x1 belongs to, as (lo, hi)."""
    mid = page.rect.width / 2.0
    if x1 < mid + 1.0:
        return (0.0, mid + 1.0)
    if x0 > mid - 1.0:
        return (mid - 1.0, page.rect.width)
    return (0.0, page.rect.width)          # a spanning (full-width) float


def _count(lines, text_only=True):
    """Printed lines = distinct baselines, 1 pt quantised; plus the text."""
    seen, chars, order = set(), [], []
    for y, x0, x1, sz, t in lines:
        k = round(y)
        if k not in seen:
            seen.add(k)
            order.append(k)
        chars.append(t)
    return len(seen), ' '.join(chars)


def _islabel(t):
    t = t.strip()
    return bool(TABLAB.match(t) or FIGLAB.match(t))


def _run(L, i, lo, hi, end):
    """The caption's own printed lines, starting at L[i].

    ★★ THREE HARD STOPS AND ONE SOFT ONE, and every one of them was put here
    by a caption this file measured wrongly without it:

      * the end of the band (a rule, for a table) -- Table 2, whose body rows
        are the same font at the same margin as its caption;
      * a font change -- Table A3, which has no rule at all;
      * THE NEXT CAPTION LABEL -- Fig. 7, a full-width caption whose column
        band therefore contains the whole page, so without this stop its run
        swallowed Tables 5 and 6 beneath it and reported 27 lines for 8;
      * and a vertical gap wider than 1.9 median leadings, which is the only
        test that catches a caption followed by something this file does not
        recognise.  ★ The gap threshold is taken from the MEDIAN leading of
        the run and not from its first gap: Fig. 7's first gap is 10.08 pt
        against a median 8.33, and at 1.8 x 10.08 the threshold exceeded the
        18 pt gap down to TABLE 5 by 0.16 pt.  A tolerance derived from one
        observation is not a tolerance.
    """
    run, prev = [L[i]], L[i][0]
    for q in L[i + 1:]:
        if q[0] >= end - 1.0:
            break
        if q[1] < lo - 1.0 or q[2] > hi + 1.0:
            continue
        if abs(q[3] - CAP) > 0.01:
            break
        if _islabel(q[4]):
            break
        if q[0] > prev + 0.5:
            prev = q[0]
        run.append(q)
    ys = sorted({round(q[0], 2) for q in run})
    if len(ys) > 2:
        gaps = sorted(ys[k + 1] - ys[k] for k in range(len(ys) - 1))
        med = gaps[len(gaps) // 2]
        cut = None
        for k in range(len(ys) - 1):
            if ys[k + 1] - ys[k] > 1.9 * med:
                cut = ys[k + 1]
                break
        if cut is not None:
            run = [q for q in run if q[0] < cut - 0.5]
    return run[1:]            # the label line is not a caption line


def table_captions():
    out = []
    for p in DOC:
        L = _lines(p)
        R = _rules(p)
        for i, (y, x0, x1, sz, t) in enumerate(L):
            m = TABLAB.match(t.strip())
            if not m or abs(sz - CAP) > 0.01:
                continue
            lo, hi = _band(p, x0, x1)
            below = [r for r in R if r[0] > y + 1.0
                     and min(r[2], hi) - max(r[1], lo) > 10.0]
            end = below[0][0] if below else 1e9
            run = _run(L, i, lo, hi, end)
            assert run, (
                'TABLE %s on page %d: no caption line was found between its '
                'label and the end of its caption.  That is an error and not '
                'a zero-line caption.' % (m.group(1), p.number + 1))
            n, txt = _count(run)
            out.append(dict(kind='Table', label=m.group(1),
                            page=p.number + 1, lines=n,
                            chars=len(txt), text=txt))
    return out


def figure_captions():
    out = []
    for p in DOC:
        L = _lines(p)
        for i, (y, x0, x1, sz, t) in enumerate(L):
            m = FIGLAB.match(t.strip())
            if not m or abs(sz - CAP) > 0.01:
                continue
            lo, hi = _band(p, x0, x1)
            #: A figure caption has no rule under it, so its end comes from
            #: the soft tests in `_run`.  The label line IS the first printed
            #: line of a figure caption -- `Fig. 7.-- The strongest ...` is
            #: text a reader reads -- so it is counted back in here, which is
            #: the one place the two kinds differ.
            run = [L[i]] + _run(L, i, lo, hi, 1e9)
            n, txt = _count(run)
            out.append(dict(kind='Fig.', label=m.group(1),
                            page=p.number + 1, lines=n,
                            chars=len(txt), text=txt))
    return out


def allowances():
    """name -> reason.  A line is `Table 2  reason...`; a reason is required."""
    p = os.path.join(HERE, 'capmeasure_allow.txt')
    out = {}
    if not os.path.isfile(p):
        return out
    for ln in open(p):
        ln = ln.split('#')[0].rstrip()
        if not ln.strip():
            continue
        m = re.match(r'(Table|Fig\.)\s+([A-F]?\d+)\s{2,}(\S.*)$', ln)
        if not m:
            raise SystemExit(
                'capmeasure_allow.txt: a line must read '
                '"<Table|Fig.> <label>  <written reason>", two spaces before '
                'the reason.  An exception that cannot be justified in a '
                'sentence is not an exception.  Offending line: %r' % ln)
        out['%s %s' % (m.group(1), m.group(2))] = m.group(3).strip()
    return out


def main():
    lim = 0 if ARGS.selfdrive else ARGS.limit
    flim = 0 if ARGS.selfdrive else ARGS.figlimit
    allow = {} if ARGS.selfdrive else allowances()
    caps = table_captions() + figure_captions()
    assert caps, ('capmeasure found no captions at all in %s: the font or '
                  'label test has gone vacuous, which would report every '
                  'caption compliant.' % PDF)
    ntab = sum(1 for c in caps if c['kind'] == 'Table')
    nfig = len(caps) - ntab
    fail, excused, used = [], [], set()
    print('capmeasure: %s -- %d table and %d figure captions, caption font '
          '%.2f pt against a %.2f pt body; limit %d printed line(s) for a '
          'table, %d for a figure'
          % (os.path.basename(PDF), ntab, nfig, CAP, BODY, lim, flim))
    for c in sorted(caps, key=lambda c: (c['kind'] != 'Table', c['page'])):
        name = '%s %s' % (c['kind'], c['label'])
        cap = lim if c['kind'] == 'Table' else flim
        over = c['lines'] > cap
        if over and name in allow:
            excused.append((name, c, allow[name]))
            used.add(name)
        elif over:
            fail.append((name, c, cap))
        if ARGS.all or over:
            print('   %-9s p.%-3d %3d printed line(s), %4d char(s)%s'
                  % (name, c['page'], c['lines'], c['chars'],
                     '' if not over else
                     ('  ALLOWED: ' + allow[name] if name in allow
                      else '  OVER by %d' % (c['lines'] - cap))))
    stale = sorted(set(allow) - used)
    for name in stale:
        print('   STALE ALLOWANCE: %s is inside the limit and does not need '
              'one.  An allow list that outlives its reason is a licence.'
              % name)
    print('capmeasure: %d caption(s) over the limit, %d allowed with a '
          'reason, %d stale allowance(s)' % (len(fail), len(excused),
                                             len(stale)))
    for name, c, cap in fail:
        print('   FAIL %s: %d printed lines against a limit of %d'
              % (name, c['lines'], cap))
    if ARGS.selfdrive:
        ok = bool(fail)
        print('capmeasure --selfdrive: %s -- measuring against a limit of 0 '
              '%s the gate, so it is able to go red'
              % ('PASS' if ok else 'FAIL', 'fails' if ok else 'does NOT fail'))
        return 0 if ok else 1
    return 1 if (fail or stale) else 0


if __name__ == '__main__':
    sys.exit(main())
