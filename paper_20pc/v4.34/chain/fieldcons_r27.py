#!/usr/bin/env python3
"""fieldcons_r27.py -- the limits of the field-recombined windows describe the extraction the search read.

★ r29 (register row 1, R1-1 / R2 m8): RETIRED AS A FACTOR, KEPT AS A CHECK.  Until v4.29 the census search read the
field-recombined product of 44 blocks (`r8inputs/v409/fieldfix_v409.json`) while their limits stayed on the earlier,
narrower extraction (round-27 Ruling 23), and this file measured by how much those limits were conservative
(\\FcNSys, \\FcMedFactor, \\FcMaxFactor, the section marks of Table F1).  The referees asked for the limits to be
recomputed from the searched data, and since v4.30 they are: `recombfold_r30.py` (applied inside
corrected_export_v399.py) gives every such window the searched product's S_min, EIRP, rms and on-source time, v342
its integration count and primary-beam geometry, beam_r17 the mosaic's documented-beam retention and pxapply the
apparent-position product's parallax retention.  The factor is therefore one by construction, and what is left to
assert is that it IS one: that every limit of these windows is the searched product's, row for row.

For every catalogue row at a field-repair record's identity (block, sorted edges to 1e-3 GHz, distance to 1e-3 pc --
the harvest's fold-in key):
  F1 exactly one recombined record claims it (recombfold_r30.lookup);
  F2 its printed S_min, rms and on-source time are that record's (to the print rounding) -- THE LIMIT DESCRIBES THE
     SEARCHED EXTRACTION;
  F3 the record is the census's own field-repair record (S_min and T* equal fieldfix_v409's), so the extraction the
     limit describes is the one the search statistic came from;
  F4 every census system with a recombined Class A window is in the deposit table.
The pre-fold (narrow) limit columns of every row are in recombfold_r30_audit.json; no macro carries them.

Emits  survey_numbers_round994.tex   (\\FcNBlock, \\FcNWin)
       fieldcons_r27.csv             (per system: the deposit)
Usage: fieldcons_r27.py [--drive N]   (drives write *_driveN.*, never production)
  --drive 1  one recombined record duplicated                                  -> F1 must fail
  --drive 2  one recombined row's S_min put back to the narrow extraction's    -> F2 must fail
"""
import argparse
import csv
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import adopted_e90 as ae                                     # noqa: E402
import recombfold_r30 as rc                                  # noqa: E402

ap = argparse.ArgumentParser()
ap.add_argument('--drive', type=int, default=0)
A = ap.parse_args()
SUF = '_drive%d' % A.drive if A.drive else ''

ROWS = ae.catalogue()
ENT = rc.entries()
if A.drive == 1:
    ENT = ENT + [dict(ENT[0])]
AUD = json.load(open(os.path.join(HERE, 'recombfold_r30_audit.json')))
OLD = {}
for x in AUD['rows']:
    OLD.setdefault(rc._key(x['eb'], x['flo'], x['fhi']) + (round(float(x['dist_pc']), 3),), []).append(x['old'])
fails = []
joined = {}
for r in ROWS:
    try:
        e = rc.lookup_row(r, ENT if A.drive == 1 else None)
    except AssertionError as x:
        fails.append('F1 %s' % str(x)[:140])
        break
    if e is None:
        continue
    joined[id(r)] = e
smin_cat = {id(r): float(r['smin_mJy']) for r in ROWS}
if A.drive == 2:
    _r = next(r for r in ROWS if id(r) in joined)
    _o = OLD[rc._key(_r['eb'], _r['flo_GHz'], _r['fhi_GHz']) + (round(float(_r['dist_pc']), 3),)][0]
    smin_cat[id(_r)] = _o['smin'] * 1e3
for r in ROWS:
    e = joined.get(id(r))
    if e is None:
        continue
    for name, got, want, tol in (
            ('S_min', smin_cat[id(r)], e['smin_Jy'] * 1e3, 0.5e-5),
            ('rms', float(r['rms_mJy']), e['rms_mJy'], 0.5e-5),
            ('on-source time', float(r['on_source_s']), e['onsrc_s'], 0.005)):
        if abs(got - want) > tol + 1e-12:
            fails.append('F2 %s %s %.3f GHz: printed %s %r is not the searched product\'s %r'
                         % (r['star_name'], r['eb'], float(r['flo_GHz']), name, got, want))
FF = json.load(open(os.path.join(HERE, 'r8inputs', 'v409', 'fieldfix_v409.json')))
FFK = {}
for f in FF:
    FFK.setdefault((f['eb'], f['spw']), []).append(f)      # two stars of one block share (eb, spw): GJ 2006A/B
for e in {id(v): v for v in joined.values()}.values():
    if not any(f['smin'] == e['smin_Jy'] and f['star_snr'] == e['star_snr'] for f in FFK.get((e['eb'], e['spw']), ())):
        fails.append('F3 %s spw%s: the limit\'s product is not the census\'s field-repair record' % (e['eb'], e['spw']))

# the system table: each system holding a recombined Class A window, with its adopted limit and the window it is set by
E = ae.per_window(ROWS)
best, _ = ae.best_by_system(ROWS, E)
sysrows = []
for s in sorted(best):
    rA = [r for r in ROWS if r['system_id'] == s and r['search_class'] == 'A']
    nrep = sum(1 for r in rA if id(r) in joined)
    if not nrep:
        continue
    sysrows.append(dict(system_id=s, n_classA_windows=len(rA), n_classA_recombined=nrep,
                        adopted_limit_W='%.6e' % best[s][1],
                        set_by_recombined=str(id(best[s][0]) in joined),
                        adopted_from_eb=best[s][0]['eb'], adopted_from_lo_GHz=best[s][0]['flo_GHz']))
sys_with = {r['system_id'] for r in ROWS if r['search_class'] == 'A' and id(r) in joined and r['system_id'] in best}
if sys_with != {x['system_id'] for x in sysrows}:
    fails.append('F4 systems with a recombined window %d, rows in the table %d' % (len(sys_with), len(sysrows)))

blocks = sorted({e['eb'] for e in joined.values()})
m = {'FcNBlock': '%d' % len(blocks), 'FcNWin': '%d' % len(joined)}
for k in m:
    assert k.isalpha(), k
with open(os.path.join(HERE, 'numbers/survey_numbers_round994%s.tex' % SUF), 'w') as fh:
    fh.write('%% fieldcons_r27.py -- generated, do not edit\n')
    for k, v in sorted(m.items()):
        fh.write('\\newcommand{\\%s}{%s}\n' % (k, v))
with open(os.path.join(HERE, 'fieldcons_r27%s.csv' % SUF), 'w', newline='') as fh:
    w = csv.DictWriter(fh, fieldnames=list(sysrows[0]) if sysrows else ['system_id'])
    w.writeheader()
    for x in sysrows:
        w.writerow(x)
print('fieldcons_r27: %d recombined blocks, %d catalogue windows, %d systems hold a Class A one, %d set by one; '
      'every limit is the searched product\'s' % (len(blocks), len(joined), len(sysrows),
                                                  sum(x['set_by_recombined'] == 'True' for x in sysrows)))
for f in fails[:8]:
    print('FAIL', f)
print('fieldcons_r27: %s%s' % ('FAIL' if fails else 'PASS', ' [drive %d]' % A.drive if A.drive else ''))
sys.exit(3 if fails else 0)
