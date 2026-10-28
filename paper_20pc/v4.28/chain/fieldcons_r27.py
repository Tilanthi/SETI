#!/usr/bin/env python3
"""fieldcons_r27.py -- by how much the quoted limits are conservative where a
block's FIELD rows were recombined after the limits were computed (Ruling 23).

The field-truncation repair (round 8, extended in round 27 by row 55) re-ran
the extraction over every in-beam FIELD row of a block.  The census SEARCH
statistic reads the repaired product (`fieldfix_v409.json`, eight generators),
but the LIMITS stay on the extraction the injection completeness was
calibrated on (Ruling 23): the catalogue's `eirp_p90_adopted_W` comes from the
first, narrower extraction.  A limit from the narrower extraction is valid and
conservative, because the search itself ran on the more sensitive product.
This generator measures how conservative.

For every Class A census window that reads a field-repair record (joined on
block, sorted edges to 1e-3 GHz and the star's distance to 1e-3 pc, which is
the harvest's own fold-in key), the adopted limit is rescaled by the ratio of
the two extractions' point-source sensitivities, S_min(repaired) /
S_min(catalogue).  Each system's best eligible window is then re-selected
with `adopted_e90.best_by_system`, the same function that picks the printed
limits.  The factor for a system is its adopted limit / its limit if folded.
Nothing else in the chain (completeness factor, parallax, smearing, mask) is
re-derived: this factor is a ratio of sensitivities, not a new limit.

Emits  survey_numbers_round994.tex   (macros \\FcNBlock \\FcNSys \\FcMedFactor
                            \\FcMaxFactor -- exactly the four the clause cites)
       fieldcons_r27.csv   (per system: the deposit)
Usage: fieldcons_r27.py [--drive N]   (drives write *_driveN.*, never production)
  --drive 1  one field-repair record duplicated              -> F1 must fail
  --drive 2  the S_min ratio of a repaired window that SETS its system's
             adopted limit forced to 1.25                      -> F4 must fail
"""
import argparse
import csv
import json
import os
import statistics
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import adopted_e90 as ae                                     # noqa: E402

ap = argparse.ArgumentParser()
ap.add_argument('--drive', type=int, default=0)
A = ap.parse_args()
SUF = '_drive%d' % A.drive if A.drive else ''

ROWS = ae.catalogue()
FFX = json.load(open(os.path.join(HERE, 'r8inputs', 'v409', 'fieldfix_v409.json')))
if A.drive == 1:
    FFX = FFX + [dict(FFX[0])]


def wk(eb, a, b):
    a, b = float(a), float(b)
    return (eb, round(min(a, b), 3), round(max(a, b), 3))


FK = {}
for f in FFX:
    if f.get('flo') is None or f.get('smin') is None:
        continue
    FK.setdefault(wk(f['eb'], f['flo'], f['fhi']), []).append(f)

E = ae.per_window(ROWS)
EF = dict(E)
best, lost = ae.best_by_system(ROWS, E)
BEST_IDS = {id(v[0]) for v in best.values()}
fails = []
joined, ratio = {}, {}
for r in ROWS:
    k = wk(r['eb'], r['flo_GHz'], r['fhi_GHz'])
    cand = [f for f in FK.get(k, [])
            if f.get('dist_pc') is None
            or abs(float(f['dist_pc']) - float(r['dist_pc'])) <= 1e-3]
    if not cand:
        continue
    if len(cand) > 1:
        fails.append('F1 window %s %.3f-%.3f (%s) joins %d field-repair records'
                     % (k[0], k[1], k[2], r['star_name'], len(cand)))
        continue
    f = cand[0]
    q = float(f['smin']) * 1e3 / float(r['smin_mJy'])        # Jy -> mJy
    if A.drive == 2 and id(r) in BEST_IDS and not any(x > 1 for x in ratio.values()):
        q = 1.25          # a window that SETS its system's limit, made less sensitive
    joined[id(r)] = f
    ratio[id(r)] = q
    EF[id(r)] = E[id(r)] * q

bestf, lostf = ae.best_by_system(ROWS, EF)
if lost != lostf:
    fails.append('F2 the systems the mask removes differ when folded: %s vs %s'
                 % (lost, lostf))

sysrows = []
for s in sorted(best):
    rA = [r for r in ROWS if r['system_id'] == s and r['search_class'] == 'A']
    nrep = sum(1 for r in rA if id(r) in joined)
    if not nrep:
        continue
    l0, lf = best[s][1], bestf[s][1]
    sysrows.append(dict(system_id=s, n_classA_windows=len(rA),
                        n_classA_recombined=nrep,
                        adopted_limit_W='%.6e' % l0,
                        limit_if_recombined_W='%.6e' % lf,
                        factor='%.4f' % (l0 / lf),
                        adopted_from_eb=best[s][0]['eb'],
                        adopted_from_lo_GHz=best[s][0]['flo_GHz'],
                        folded_from_eb=bestf[s][0]['eb'],
                        folded_from_lo_GHz=bestf[s][0]['flo_GHz']))

# F3 every repaired Class A window's ratio is a real number and the system
#    table holds every system that has one
repA = [r for r in ROWS if r['search_class'] == 'A' and id(r) in joined]
sys_with = {r['system_id'] for r in repA if r['system_id'] in best}
if sys_with != {x['system_id'] for x in sysrows}:
    fails.append('F3 systems with a recombined window %d, rows in the table %d'
                 % (len(sys_with), len(sysrows)))
# F4 THE WORD "CONSERVATIVE" MUST BE TRUE: no system's limit may get WORSE
#    when folded.  A system whose factor is below one is not conservatively
#    stated, it is optimistically stated, and the clause would be false for it.
below = [x for x in sysrows if float(x['factor']) < 1 - 1e-9]
if below:
    fails.append('F4 %d system(s) whose limit would be SHALLOWER if folded: %s'
                 % (len(below), [(x['system_id'], x['factor']) for x in below]))

moved = [float(x['factor']) for x in sysrows if float(x['factor']) > 1 + 1e-9]
blocks = sorted({joined[id(r)]['eb'] for r in ROWS if id(r) in joined})
m = {
    'FcNBlock': '%d' % len(blocks),
    'FcNSys': '%d' % len(moved),
    'FcMedFactor': '%.1f' % statistics.median(moved) if moved else '1.0',
    'FcMaxFactor': '%.1f' % max(moved) if moved else '1.0',
}
MINF = '%.2f' % min(float(x['factor']) for x in sysrows) if sysrows else '1.00'
for k in m:
    assert k.isalpha(), k
with open(os.path.join(HERE, 'survey_numbers_round994%s.tex' % SUF), 'w') as fh:
    fh.write('%% fieldcons_r27.py -- generated, do not edit\n')
    for k, v in sorted(m.items()):
        fh.write('\\newcommand{\\%s}{%s}\n' % (k, v))
with open(os.path.join(HERE, 'fieldcons_r27%s.csv' % SUF), 'w', newline='') as fh:
    w = csv.DictWriter(fh, fieldnames=list(sysrows[0]) if sysrows else ['system_id'])
    w.writeheader()
    for x in sysrows:
        w.writerow(x)

print('fieldcons_r27: %d recombined blocks, %d Class A windows, %d systems hold one; '
      '%d systems\' adopted limit is conservative, median x%s, max x%s (min factor %s)'
      % (len(blocks), len(repA), len(sysrows), len(moved), m['FcMedFactor'],
         m['FcMaxFactor'], MINF))
for x in sorted(sysrows, key=lambda x: -float(x['factor']))[:12]:
    print('   %-28s %s -> %s  x%s' % (x['system_id'], x['adopted_limit_W'],
                                    x['limit_if_recombined_W'], x['factor']))
for f in fails:
    print('FAIL', f)
print('fieldcons_r27: %s%s' % ('FAIL' if fails else 'PASS',
                               ' [drive %d]' % A.drive if A.drive else ''))
sys.exit(3 if fails else 0)
