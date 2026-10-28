#!/usr/bin/env python3
"""fieldcover_r27.py -- every census window must be searched over EVERY FIELD
row of its target pointing (row 55, Ruling 21).

THE DEFECT THIS CATCHES.  An ALMA measurement set can write one pointing as
several FIELD rows (one per scan group), and a mosaic as several pointings
that all see the star.  The extractor used until 2026-09-26 kept one FIELD row
and discarded the rest.  The round-8 field-truncation ledger repaired 42
blocks, but it was a ONE-OFF list.  (i) It was taken against the census of
2026-09-26 (404 blocks) and never re-taken when the census grew: ε Eri
`A002_Xb9c01c_X2004` and `A002_Xe539c7_X12189` joined later and kept their
truncated products.  (ii) Five of its own 42 blocks were never re-extracted:
a guessed 8.5 GB size became a 13.5 GB download budget, and that budget
refused the real 26-31 GB ASDMs.  Nothing in the build compared the fields
each census window used with the fields its pointing has, so neither leak
could be seen.

THE CHECK.  For every census window (search class A or B) of the catalogue:
  C1  a field record exists for it in `fieldcover_r27.json` (block + sorted
      edges to 1e-3 GHz + star), i.e. the census has not grown past the
      sweep -- the exact failure mode of (i);
  C2  the FIELD rows the census statistic actually uses cover every in-beam
      FIELD row of the pointing (same pointing, or primary-beam response
      >= 0.05 at the star).  "Used" is the `kept_fields` of the
      `fieldfix_v409.json` record when the census reads one for that window
      (matched on block, edges and the star's distance, as the harvest's own
      fold-in is), and otherwise the field the supplying product's
      extraction selected;
  C3  a field-repair record the census reads discards no in-beam time
      (`discarded_in_beam_s` <= 0.5 s);
  C4  a block may be exempted from C2 only by being DECLARED in the field
      table (`declared_unrepaired`: block, reason, measured peak), which is
      how the paper states an infeasible repair -- and a declaration whose
      block has since been repaired fails, so an exemption can never outlive
      the defect it excuses.
C1 needs no MS: it fails when a block arrives without a sweep record.  C2/C3
read the field tables the sweep froze, so the build never touches the cluster.

Usage:  fieldcover_r27.py [--cat CSV] [--ffx JSON] [--cover JSON] [--drive N]
  --drive 1  delete the fieldfix records of ε Eri X2004   (C2 must fire)
  --drive 2  add a census window the sweep never saw      (C1 must fire)
  --drive 3  mark one field-repair record as discarding in-beam time (C3)
  --drive 4  declare a block that is already repaired            (C4 must fire)
  --drive 5  drop every declaration                              (C2 must fire
             wherever a declared block is still unrepaired)
Drives perturb in memory only and write nothing.  Exit 0 = pass, 3 = fail.
"""
import argparse
import csv
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ap = argparse.ArgumentParser()
ap.add_argument('--cat', default=os.path.join(HERE, 'per_target_results_v3.99.csv'))
ap.add_argument('--ffx', default=os.path.join(HERE, 'r8inputs', 'v409', 'fieldfix_v409.json'))
ap.add_argument('--cover', default=os.path.join(HERE, 'r27inputs', 'fieldcover_r27.json'))
ap.add_argument('--drive', type=int, default=0)
A = ap.parse_args()

CAT = [r for r in csv.DictReader(open(A.cat)) if r.get('search_class') in ('A', 'B')]
FFX = json.load(open(A.ffx))
COV = json.load(open(A.cover))
MINRESP = float(COV['min_pb_resp'])


def wk(eb, a, b):
    a, b = float(a), float(b)
    return (eb, round(min(a, b), 3), round(max(a, b), 3))


if A.drive == 1:
    FFX = [r for r in FFX if r['eb'] != 'A002_Xb9c01c_X2004']
if A.drive == 2:
    CAT = CAT + [dict(CAT[0], eb='A002_Xdeadbe_Xef00', star_name='drive star')]
if A.drive == 3:
    FFX = [dict(r) for r in FFX]
    FFX[0]['discarded_in_beam_s'] = 30.0

DECL = {d['eb']: d for d in COV.get('declared_unrepaired', [])}
if A.drive == 4:
    DECL['A002_Xb9c01c_X2004'] = dict(eb='A002_Xb9c01c_X2004', reason='drive 4')
if A.drive == 5:
    DECL = {}

COVK = {}
for r in COV['rows']:
    COVK.setdefault(wk(r['eb'], r['lo'], r['hi']), {})[r['star_name']] = r
FFK = {}
for r in FFX:
    if r.get('flo') is None:
        continue
    FFK.setdefault(wk(r['eb'], r['flo'], r['fhi']), []).append(r)

c1, c2, c3, c4 = [], [], [], []
n_decl = 0
n_multi = n_ffx = 0
for r in CAT:
    k = wk(r['eb'], r['flo_GHz'], r['fhi_GHz'])
    rec = COVK.get(k, {}).get(r['star_name'])
    if rec is None:
        c1.append((r['eb'], k[1], k[2], r['star_name']))
        continue
    inbeam = set(rec.get('inbeam') or [])
    used = set(x for x in (rec.get('used') or []) if x is not None)
    ff = [f for f in FFK.get(k, [])
          if f.get('dist_pc') is None or abs(float(f['dist_pc']) - float(r['dist_pc'])) <= 1e-3]
    if len(ff) > 1:
        c2.append((r['eb'], k[1], k[2], r['star_name'], 'ambiguous fieldfix records: %d' % len(ff)))
        continue
    if ff:
        n_ffx += 1
        used = set(ff[0].get('kept_fields') or [])
        if (ff[0].get('discarded_in_beam_s') or 0) > 0.5:
            c3.append((r['eb'], k[1], k[2], r['star_name'], ff[0]['discarded_in_beam_s']))
    if len(inbeam) > 1:
        n_multi += 1
    miss = sorted(inbeam - used)
    if r['eb'] in DECL:
        if not miss:
            c4.append((r['eb'], k[1], k[2], r['star_name'],
                       'declared unrepaired but uses every in-beam row'))
        else:
            n_decl += 1
        continue
    if miss:
        c2.append((r['eb'], k[1], k[2], r['star_name'],
                   'used %s of in-beam %s' % (sorted(used), sorted(inbeam))))

print('fieldcover_r27: %d census windows in %d blocks; %d with >1 in-beam FIELD row; '
      '%d read a field-repair record'
      % (len(CAT), len({r['eb'] for r in CAT}), n_multi, n_ffx))
for lab, lst in (('C1 census window with no field record (census grew past the sweep)', c1),
                 ('C2 in-beam FIELD rows not used', c2),
                 ('C3 field-repair record discards in-beam time', c3),
                 ('C4 declaration that has outlived its defect', c4)):
    print('  %-70s: %d window(s) in %d block(s)' % (lab, len(lst), len({x[0] for x in lst})))
    for x in lst[:12]:
        print('      %s' % (x,))
print('  declared unrepaired (stated in the paper, exempt from C2): %d window(s) in %d block(s)'
      % (n_decl, len(DECL)))
bad = bool(c1 or c2 or c3 or c4)
print('fieldcover_r27: %s%s' % ('FAIL' if bad else 'PASS',
                                ' [drive %d]' % A.drive if A.drive else ''))
sys.exit(3 if bad else 0)
