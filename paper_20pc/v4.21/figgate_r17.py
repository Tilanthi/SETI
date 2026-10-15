#!/usr/bin/env python3
"""THE FIGURE GATE: every included figure is legible, scaled 1, and reproducible.

    python3 figgate_r17.py [--drive N]

Three clauses, over the `\\includegraphics` closure of the manuscript and
nothing else -- a glob would sweep `figures/` and reach the eight built-but-
unused files, which are not in the article:

  G1  FLOOR.   The smallest line of running text drawn in each figure prints
      at or above `FLOOR` pt on the page, AFTER `\\includegraphics` has scaled
      the artwork.  Nothing in this build measured that until round 17: six of
      eleven figures were below 6 pt and one had been emitted at the full text
      width and placed in a single column, which left its labels at half size
      in the printed paper for several versions.
  G2  SCALE.   The drawn width is the width the float gives it, so the scale
      is 1 and the type on the page is the type the generator chose.  A
      figure may declare a deliberate fraction; it then has to declare it.
  G3  EPOCH.   Every included figure carries the build's own
      `SOURCE_DATE_EPOCH`.  ★ FOUR shipped figures did not: two held the wall
      clock and two held a bespoke epoch of 1 700 000 000 -- reproducible, but
      not the build's, so `cleanregen` would have reported them either way.
      The cause is general and will recur: **a generator run by hand does not
      inherit `make_all.sh`'s `export SOURCE_DATE_EPOCH`**, and every agent
      runs generators by hand.

★ The clause module is `figfloor_r17.py`, the same one the figure generators
themselves call, so this gate and the generators cannot drift apart in what
they measure.  `LIMIT` is 6.0 and not 6.5 deliberately: ten of the eleven are
at 6.40 or better, and a gate that fails on the day it is installed gets
whitelisted, which is a way of having no gate.

Drives (each must FAIL):
  1  the floor raised above the best figure in the paper   -> G1
  2  a figure's expected scale declared wrong             -> G2
  3  the required epoch changed                           -> G3
  4  the closure emptied                                  -> the anti-vacuity
     clause, because a gate that measures no figure passes every paper
"""
import os
import re
import sys

import pymupdf

import figfloor_r17 as ff
import manuscript

HERE = os.path.dirname(os.path.abspath(__file__))
FLOOR = 6.0
EPOCH = 'D:20200101000000Z'


def main(argv):
    drive = 0
    for i, a in enumerate(argv):
        if a == '--drive':
            drive = int(argv[i + 1])
    floor = 99.0 if drive == 1 else FLOOR
    epoch = 'D:19990101000000Z' if drive == 3 else EPOCH

    flat = manuscript.flat()
    inc = re.findall(r'\\includegraphics\s*(\[[^\]]*\])?\s*\{([^}]+)\}', flat)
    seen, rows = set(), []
    for opt, name in inc:
        rel = name if name.endswith('.pdf') else name + '.pdf'
        if rel in seen:
            continue
        seen.add(rel)
        path = os.path.join(HERE, rel)
        if not os.path.exists(path):
            rows.append((rel, None, None, None, 'MISSING FROM DISK'))
            continue
        # ★ figfloor's own signatures, read from the module rather than
        #   assumed: placement -> (env, frac, base_pt, target_pt, opt) and
        #   lines_pt -> (lines, spans, width_pt, height_pt, creationDate).
        #   My first version treated both as scalars and died on a tuple --
        #   which is the right failure: a gate that guessed would have
        #   compared the wrong thing and passed.
        env, frac, base, target, _opt = ff.placement(HERE, rel, src=flat)
        lines, _spans, wid, _hei, cd = ff.lines_pt(path)
        # the size on the PAGE: the drawn size times the scale the float
        # applies, which is what a reader sees
        scale = target / wid if wid else None
        mn = min((s for s, _txt, _bb in lines), default=None)
        mn = mn * scale if (mn is not None and scale) else mn
        rows.append((rel, dict(env=env, frac=frac, scale=scale,
                               target=target, drawn=wid), mn, cd, ''))
    if drive == 4:
        rows = []

    fails = []
    if len(rows) < 5:
        fails.append('G4 the closure holds only %d figure(s); a gate that '
                     'measures no figure passes every paper' % len(rows))
    for rel, place, mn, cd, note in rows:
        if note:
            fails.append('G0 %s %s' % (rel, note))
            continue
        scale = place.get('scale') if isinstance(place, dict) else None
        # ★ the DECLARED scale is 1: the canvas is to be the width the float
        #   gives it, so the type on the page is the type the generator chose.
        #   A figure drawn at another width is magnified or shrunk and its
        #   labels with it -- which is how a full-text-width drawing placed in
        #   one column printed its labels at half size.
        want = 1.0
        if mn is not None and mn < floor:
            fails.append('G1 %-26s smallest line %.2f pt, below %.1f'
                         % (rel, mn, floor))
        if scale is not None:
            tgt = (want or 1.0) * (1.10 if drive == 2 else 1.0)
            if abs(scale / tgt - 1.0) > 0.02:
                fails.append('G2 %-26s drawn at x%.4f of the width the float '
                             'gives it, against a declared %.4f'
                             % (rel, scale, tgt))
        if not str(cd).startswith(epoch):
            fails.append('G3 %-26s creation date %r is not the build epoch %r'
                         % (rel, cd, epoch))

    print('figgate: %d figure(s) in the \\includegraphics closure, floor '
          '%.1f pt, epoch %s' % (len(rows), floor, epoch))
    for rel, place, mn, cd, note in rows:
        print('  %-26s %s  min %s pt  %s'
              % (rel,
                 ('x%.4f' % place['scale']) if isinstance(place, dict)
                 and place.get('scale') else '   -   ',
                 ('%5.2f' % mn) if mn is not None else '  -  ',
                 'epoch ok' if str(cd).startswith(EPOCH) else 'EPOCH %r' % cd))
    for f in fails:
        print('  FAIL ' + f)
    print('figgate: %d FAIL' % len(fails))
    if drive and not fails:
        print('  DRIVE %d DID NOT FAIL -- the clause it exercises is vacuous'
              % drive)
        return 2
    return 1 if fails else 0


if __name__ == '__main__':
    sys.exit(main(sys.argv))
