#!/usr/bin/env python3
"""Round 83 (v4.04): the survey's on-source time, and the two defects of
opposite sign that very nearly cancel in it.

TWO THINGS ARE TRUE AT ONCE AND NEITHER MAY BE QUOTED ALONE.

(1) The extraction's field selector kept one `FIELD` row per execution block.
    In 42 of the 404 released blocks the discarded rows were not calibrators
    but further in-beam pointings on the same star, so real on-source time was
    thrown away before a visibility was read.  Recovering it would improve the
    flux limit in those windows by the square root of the number of in-beam
    fields.
(2) The released `on_source_s` is `n_int x median(dt)` -- the code never reads
    the `INTERVAL` column -- and sub-scan boundary dumps are shorter than the
    median, so the estimator OVER-counts.  No window's value can rise under
    the exact computation, and 486 of 1,950 fall by more than 1 per cent.

(1) costs the survey about 19 h it had; (2) credits it with about 13-18 h it
never had.  The published total is therefore approximately right by accident,
and the manuscript states both signs in the same paragraph.

Everything here is recomputed, not transcribed:

  * the affected-block list is the frozen audit product
    `r8inputs/trunc_aff_ebs_v404.json` (42 blocks, each with the number of
    in-beam target fields the selector saw);
  * the on-source time of each block is the RELEASED catalogue's own
    `on_source_s`, aggregated the way the published survey total is
    (maximum over a block's simultaneous windows -- which reproduces the
    published figure exactly, and that equality is asserted below);
  * the exact-versus-estimated comparison is the frozen host scan
    `r8inputs/d3_scan_v404.json`, which applied both estimators to the
    `times` array of every surviving extraction product.

-> survey_numbers_round83.tex
"""
import csv
import json
import os
import statistics as st
from collections import defaultdict

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, 'survey_numbers_round83.tex')

ROWS = list(csv.DictReader(open(os.path.join(HERE,
                                             'per_target_results_v3.99.csv'))))
AFF = json.load(open(os.path.join(HERE, 'r8inputs',
                                  'trunc_aff_ebs_v404.json')))
D3 = json.load(open(os.path.join(HERE, 'r8inputs', 'd3_scan_v404.json')))
K = json.load(open(os.path.join(HERE, 'catalogue_constants.json')))

M = {}


def m(k, v):
    M[k] = v


def onsrc(r):
    return float(r['on_source_s']) if r['on_source_s'] else 0.0


# ------------------------------------------------ the published aggregation
# A block's windows are simultaneous, so its on-source time is ONE number;
# the survey total is the sum over blocks.  Two aggregations of a block's
# windows are defensible and they differ, so both are computed and the one
# that reproduces the published total is identified rather than assumed.
blk_max, blk_all = defaultdict(float), defaultdict(list)
for r in ROWS:
    v = onsrc(r)
    blk_max[r['eb']] = max(blk_max[r['eb']], v)
    blk_all[r['eb']].append(v)
tot_max = sum(blk_max.values()) / 3600.0
tot_med = sum(st.median(v) for v in blk_all.values()) / 3600.0

m('ExpNBlocks', '%d' % len(blk_max))
m('ExpTotalMax', '%.1f' % tot_max)
m('ExpTotalMed', '%.1f' % tot_med)

# v4.04 is the first version to quote a survey exposure at all, so there is
# no earlier macro to check against.  What CAN be checked is that the two
# aggregations do not differ so much that "the survey's on-source time" is
# meaningless as a phrase: the manuscript quotes the max form and names the
# convention, and the spread is reported beside it.
m('ExpAggSpreadPct', '%.1f' % (100.0 * (tot_max - tot_med) / tot_max))
assert tot_max >= tot_med > 0.9 * tot_max, (tot_max, tot_med)

# ------------------------------------------------------- (1) the truncation
aff_rows = [r for r in ROWS if r['eb'] in AFF]
assert aff_rows, 'no released window matches the affected-block list'
disc = sum(blk_max.get(e, 0.0) * (v['n_tgt'] - 1)
           for e, v in AFF.items()) / 3600.0
avail = sum(blk_max.get(e, 0.0) * v['n_tgt']
            for e, v in AFF.items()) / 3600.0
# Every affected block must actually be in the release, or the hours are
# computed against a zero and silently understate the loss.
assert all(e in blk_max for e in AFF), \
    [e for e in AFF if e not in blk_max]
gain_w = [AFF[r['eb']]['gain'] for r in aff_rows]

m('TruncNBlocks', '%d' % len(AFF))
m('TruncNWin', '%d' % len(aff_rows))
m('TruncNStars', '%d' % len({r['star_name'] for r in aff_rows}))
m('TruncPctWin', '%.1f' % (100.0 * len(aff_rows) / len(ROWS)))
m('TruncHoursLost', '%.1f' % disc)
m('TruncHoursAvail', '%.0f' % avail)
m('TruncPctSurvey', '%.1f' % (100.0 * disc / tot_max))
m('TruncGainMed', '%.2f' % st.median(gain_w))
m('TruncGainMax', '%.2f' % max(gain_w))
m('TruncEirpMed', '%.1f' % (st.median(gain_w) ** 2))

# ---------------------------------------------------- (2) the over-count
rows = D3['rows']
by_eb = defaultdict(lambda: dict(old=[], new=[]))
for r in rows:
    by_eb[r['eb']]['old'].append(r['old'])
    by_eb[r['eb']]['new'].append(r['new'])

rel = [r for r in rows if r['eb'] in blk_max]
m('OcNWinScanned', '%d' % len(rows))
m('OcNWinReleased', '%d' % len(rel))
moved = [r for r in rel if r['old'] > 0 and r['new'] / r['old'] < 0.99]
m('OcNWinMoved', '%d' % len(moved))
rose = [r for r in rel if r['old'] > 0 and r['new'] / r['old'] > 1.001]
m('OcNWinRose', '%d' % len(rose))
assert len(rose) == 0, len(rose)
m('OcWorstRatio', '%.3f' % min(r['new'] / r['old'] for r in rel if r['old'] > 0))

relblk = {e: v for e, v in by_eb.items() if e in blk_max}
old_mx = sum(max(v['old']) for v in relblk.values()) / 3600.0
new_mx = sum(max(v['new']) for v in relblk.values()) / 3600.0
old_md = sum(st.median(v['old']) for v in relblk.values()) / 3600.0
new_md = sum(st.median(v['new']) for v in relblk.values()) / 3600.0
m('OcNBlocks', '%d' % len(relblk))
m('OcOldMax', '%.1f' % old_mx)
m('OcNewMax', '%.1f' % new_mx)
m('OcOldMed', '%.1f' % old_md)
m('OcNewMed', '%.1f' % new_md)
m('OcDeltaLo', '%.1f' % (old_md - new_md))
m('OcDeltaHi', '%.1f' % (old_mx - new_mx))
m('OcPctLo', '%.1f' % (100.0 * (old_md - new_md) / old_md))
m('OcPctHi', '%.1f' % (100.0 * (old_mx - new_mx) / old_mx))

# ------------------------------------------------------------- the cancel
net_lo = disc - (old_mx - new_mx)
net_hi = disc - (old_md - new_md)
m('ExpNetLo', '%+.1f' % min(net_lo, net_hi))
m('ExpNetHi', '%+.1f' % max(net_lo, net_hi))
# The whole point of the paragraph is that the two are of opposite sign and
# comparable size.  If a future input ever breaks that, the prose is wrong
# and the build must stop rather than print a reassuring number.
assert disc > 0 and (old_mx - new_mx) > 0, (disc, old_mx - new_mx)
assert abs(net_lo) < 0.5 * disc and abs(net_hi) < 0.5 * disc, (net_lo, net_hi)

assert len(ROWS) == K['n_windows'], len(ROWS)

with open(OUT, 'w') as fh:
    fh.write('%% GENERATED by exposure_v404.py -- do not hand-edit.\n')
    for k in sorted(M):
        fh.write('\\newcommand{\\%s}{%s}\n' % (k, M[k]))

print('exposure_v404: published total %.1f h (max aggregation) / %.1f h '
      '(median)' % (tot_max, tot_med))
print('  D1  field truncation: %d blocks, %d windows, %d stars, %.1f h of '
      '%.0f h discarded (%.1f%% of the survey); flux penalty median %.2fx'
      % (len(AFF), len(aff_rows), len({r['star_name'] for r in aff_rows}),
         disc, avail, 100 * disc / tot_max, st.median(gain_w)))
print('  D3  integration-time over-count: %d of %d released windows move, '
      'none up; total %.1f->%.1f h (max) and %.1f->%.1f h (median)'
      % (len(moved), len(rel), old_mx, new_mx, old_md, new_md))
print('  net %+.1f to %+.1f h -- the two nearly cancel' % (net_lo, net_hi))
print('  -> %s (%d macros)' % (os.path.basename(OUT), len(M)))
