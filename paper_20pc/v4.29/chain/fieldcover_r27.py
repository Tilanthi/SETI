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
THE SAME RULE OUTSIDE THE CENSUS (Ruling 34, v4.29).  The 1,008 windows of
the reserved hold-out, the beyond-40 pc control and the archival extension
(the three frozen exports) are held to it too, from `fieldcover_ext_r29.json`
(row 59's sweep of the supplying products' extraction logs, plus every
re-extraction's own field-selection record):
  E1  every exported window has a field record (block + sorted edges to
      1e-3 GHz + star);
  E2  a window whose block the tree does NOT fold from a re-extraction
      (holdfix/extfix `aca_blocks` + `fieldtrunc_blocks`) uses every in-beam
      row of its pointing, unless its block is DECLARED unrepaired;
  E3  a re-extraction the tree folds keeps every in-beam row it measured and
      discards <= 0.5 s in-beam;
  E4  a declaration names a block that is neither folded from a
      re-extraction nor free of the defect (it cannot outlive the defect);
  E5  a multi-field window of a folded block has a re-extraction field record
      (a fold the field table cannot vouch for fails).
  C2 counts as used an in-beam row that ALMA's own final flags (Pipeline_Final,
      restored in v4.29) flag WHOLLY, but only where the frozen field-loss
      evidence (`r29inputs/reflag/fieldloss_evidence_r29.json`, measured from
      ALMA's listobs + the flag template + the no-flags product) names it;
  C5  each field-loss evidence entry must be read by exactly one census window,
      must match that window's field-repair record (rows, integrations,
      on-source time) exactly, and must name only rows the record does not
      use -- so a flagged-out exemption cannot outlive its cause (v4.29,
      r28-fold29-x28a8: BD+05 1668 X28a8, scans 14~30 `bad_rawdata`).
C1 needs no MS: it fails when a block arrives without a sweep record.  C2/C3
read the field tables the sweep froze, so the build never touches the cluster.

Usage:  fieldcover_r27.py [--cat CSV] [--ffx JSON] [--cover JSON] [--drive N]
  --drive 1  delete the fieldfix records of ε Eri X2004   (C2 must fire)
  --drive 2  add a census window the sweep never saw      (C1 must fire)
  --drive 3  mark one field-repair record as discarding in-beam time (C3)
  --drive 4  declare a block that is already repaired            (C4 must fire)
  --drive 5  drop every declaration                              (C2 must fire
             wherever a declared block is still unrepaired)
  --drive 6  drop the outside-census declarations                  (E2 must fire)
  --drive 7  add an exported window the field table never saw     (E1 must fire)
  --drive 8  mark one folded re-extraction as discarding in-beam  (E3 must fire)
  --drive 9  declare a folded (repaired) block                    (E4 must fire)
  --drive 10 strip the field records of one folded truncated block (E5 must fire)
  --drive 11 drop the field-loss evidence                         (C2 must fire)
  --drive 12 alter one evidence entry's integration count         (C5 must fire)
  --drive 13 add evidence for a window that uses every in-beam row (C5 must fire)
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
ap.add_argument('--ext', default=os.path.join(HERE, 'r27inputs', 'fieldcover_ext_r29.json'))
ap.add_argument('--fieldloss', default=os.path.join(HERE, 'r29inputs', 'reflag', 'fieldloss_evidence_r29.json'))
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

FLOSS = json.load(open(A.fieldloss))['windows'] if os.path.exists(A.fieldloss) else []
if A.drive == 11:
    FLOSS = []
if A.drive == 12:
    FLOSS = [dict(e) for e in FLOSS]
    FLOSS[0] = dict(FLOSS[0], new=dict(FLOSS[0]['new'], n_int=FLOSS[0]['new']['n_int'] + 1))
if A.drive == 13:
    _x = next(r for r in FFX if r['eb'] == 'A002_Xe539c7_X12189' and r.get('flo') is not None)
    FLOSS = FLOSS + [dict(eb=_x['eb'], flo=_x['flo'], fhi=_x['fhi'], target_dir=_x['target_dir'],
                          pos_key=_x['pos_key'], flagged_out_fields=[99],
                          new={f: _x.get(f) for f in ('n_fields', 'kept_fields', 'n_int', 'onsrc')})]
FLK = {}
for e in FLOSS:
    FLK.setdefault(wk(e['eb'], e['flo'], e['fhi']), []).append(e)
FL_FIELDS = ('n_fields', 'kept_fields', 'n_int', 'onsrc')
FL_USED = []
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

c1, c2, c3, c4, c5 = [], [], [], [], []
n_decl = n_floss = 0
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
        for e in [e for e in FLK.get(k, []) if e['target_dir'] == ff[0].get('target_dir')
                  and e['pos_key'] == ff[0].get('pos_key')]:
            FL_USED.append(id(e))
            got = {f: ff[0].get(f) for f in FL_FIELDS}
            if got != e['new']:
                c5.append((r['eb'], k[1], k[2], r['star_name'], 'evidence %s != record %s' % (e['new'], got)))
            elif set(e['flagged_out_fields']) & used or not set(e['flagged_out_fields']) <= inbeam:
                c5.append((r['eb'], k[1], k[2], r['star_name'], 'flagged-out rows %s used or not in-beam %s'
                           % (e['flagged_out_fields'], sorted(inbeam))))
            else:
                used |= set(e['flagged_out_fields'])
                n_floss += 1
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
for e in FLOSS:
    if FL_USED.count(id(e)) != 1:
        c5.append((e['eb'], e['flo'], e['fhi'], e.get('target_dir'),
                   'field-loss evidence read by %d census window(s), not 1' % FL_USED.count(id(e))))
print('  in-beam rows wholly flagged by ALMA\'s final flags (field-loss evidence, counted as used): %d window(s)'
      % n_floss)
for lab, lst in (('C1 census window with no field record (census grew past the sweep)', c1),
                 ('C2 in-beam FIELD rows not used', c2),
                 ('C3 field-repair record discards in-beam time', c3),
                 ('C4 declaration that has outlived its defect', c4),
                 ('C5 field-loss evidence not matching its record / not read once', c5)):
    print('  %-70s: %d window(s) in %d block(s)' % (lab, len(lst), len({x[0] for x in lst})))
    for x in lst[:12]:
        print('      %s' % (x,))
print('  declared unrepaired (stated in the paper, exempt from C2): %d window(s) in %d block(s)'
      % (n_decl, len(DECL)))

# ---- Ruling 34: the hold-out, beyond-40 pc and extension windows -----------------------------
EXT = json.load(open(A.ext))
assert float(EXT['min_pb_resp']) == MINRESP, (EXT['min_pb_resp'], MINRESP)
_H = json.load(open(os.path.join(HERE, 'r27inputs', 'holdout', 'holdfix_r27.json')))
_E = json.load(open(os.path.join(HERE, 'r27inputs', 'extension', 'extfix_r27.json')))
FOLD = (set(_H['aca_blocks']['holdout']) | set(_H['aca_blocks']['oos'])
        | set(_H['fieldtrunc_blocks']['holdout']) | set(_H['fieldtrunc_blocks']['oos'])
        | set(_E['aca_blocks']) | set(_E['fieldtrunc_blocks']))
XW = []
for st, f in (('holdout', 'holdout_export_v381.json'), ('oos40', 'outofsample_v381.json'),
              ('extension', 'export_extension.json')):
    for r in json.load(open(os.path.join(HERE, f)))['rows']:
        XW.append((st, r['eb'], r['flo_GHz'] if 'flo_GHz' in r else r['flo'],
                   r['fhi_GHz'] if 'fhi_GHz' in r else r['fhi'], r['star_name']))
XROWS = [dict(r) for r in EXT['rows']]
XDECL = {d['eb']: d for d in EXT.get('declared_unrepaired', [])}
if A.drive == 6:
    XDECL = {}
if A.drive == 7:
    XW = XW + [('extension', 'A002_Xdeadbe_Xef01', 300.0, 301.8, 'drive star')]
if A.drive == 8:
    for r in XROWS:
        if r['eb'] in FOLD and r['repairs']:
            r['repairs'] = [dict(r['repairs'][0], disc_in=30.0)] + r['repairs'][1:]
            break
if A.drive == 9:
    XDECL['A002_Xb20b6d_Xc4c'] = dict(eb='A002_Xb20b6d_Xc4c', reason='drive 9')
if A.drive == 10:
    _b = next(r['eb'] for r in XROWS if r['eb'] in FOLD and r['orig'] == 'TRUNCATED')
    for r in XROWS:
        if r['eb'] == _b:
            r['repairs'] = []
XK = {}
for r in XROWS:
    XK.setdefault(wk(r['eb'], r['lo'], r['hi']), {})[r['star_name']] = r
e1, e2, e3, e4, e5 = [], [], [], [], []
n_xdecl = n_xfold_multi = n_xtrunc_rep = 0
for st, eb, lo, hi, star in XW:
    k = wk(eb, lo, hi)
    rec = XK.get(k, {}).get(star)
    if rec is None:
        e1.append((st, eb, k[1], k[2], star))
        continue
    inbeam = set(rec['inbeam'] or [])
    if eb in FOLD:
        if len(inbeam) > 1 or rec['orig'] == 'TRUNCATED':
            n_xfold_multi += 1
            if not rec['repairs']:
                e5.append((st, eb, k[1], k[2], star, 'folded multi-field window, no re-extraction field record'))
                continue
            if rec['orig'] == 'TRUNCATED':
                n_xtrunc_rep += 1
        for q in rec['repairs']:
            miss = sorted(set(q['inbeam']) - set(q['kept']))
            if miss or q['disc_in'] > 0.5:
                e3.append((st, eb, k[1], k[2], star, q['route'], 'misses %s, discards %.1f s in-beam'
                           % (miss, q['disc_in'])))
        if eb in XDECL:
            e4.append((st, eb, k[1], k[2], star, 'declared unrepaired but folded from a re-extraction'))
        continue
    miss = sorted(inbeam - set(rec['used'] or []))
    if eb in XDECL:
        if miss:
            n_xdecl += 1
        else:
            e4.append((st, eb, k[1], k[2], star, 'declared unrepaired but uses every in-beam row'))
        continue
    if miss:
        e2.append((st, eb, k[1], k[2], star, 'used %s of in-beam %s' % (rec['used'], sorted(inbeam))))
print('fieldcover_r27 (outside the census, Ruling 34): %d exported windows in %d blocks; %d blocks folded '
      'from a re-extraction; %d multi-field windows of folded blocks (%d of them truncated before repair)'
      % (len(XW), len({x[1] for x in XW}), len(FOLD & {x[1] for x in XW}), n_xfold_multi, n_xtrunc_rep))
for lab, lst in (('E1 exported window with no field record', e1),
                 ('E2 in-beam FIELD rows not used (unfolded, undeclared)', e2),
                 ('E3 folded re-extraction misses or discards in-beam rows', e3),
                 ('E4 declaration that has outlived its defect', e4),
                 ('E5 folded multi-field window without a field record', e5)):
    print('  %-70s: %d window(s) in %d block(s)' % (lab, len(lst), len({x[1] for x in lst})))
    for x in lst[:12]:
        print('      %s' % (x,))
print('  declared unrepaired outside the census (exempt from E2): %d window(s) in %d block(s)'
      % (n_xdecl, len(XDECL)))
bad = bool(c1 or c2 or c3 or c4 or c5 or e1 or e2 or e3 or e4 or e5)
print('fieldcover_r27: %s%s' % ('FAIL' if bad else 'PASS',
                                ' [drive %d]' % A.drive if A.drive else ''))
sys.exit(3 if bad else 0)
