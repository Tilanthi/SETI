#!/usr/bin/env python3
r"""holdfix_r27.py -- the reserved hold-out and the beyond-40 pc control, re-read
from their RE-EXTRACTION on the repaired control annulus (round 1270).

WHY THIS EXISTS.  The census's compact-array windows were re-extracted on
2026-09-23/24 with the control annulus scaled to the dish that observed them
(7 m, with the synthesised-beam floor) and folded into the census export by
`corrected_export_v399.py`.  The hold-out never was: `apply_holdout_v381.py`
splits it out of `frozen_export_v3.81.json`, written 2026-09-20, BEFORE the
repair, and nothing downstream folded the repair into it.  So 229 of its 315
windows (57 of its 77 blocks, every one of them an ACA block) were searched on
a 12 m annulus inside a 7 m beam, and the paper's sentence that the reserved
sets were "searched with the same pipeline" was false for them.  The same was
true of 29 of the 198 windows (7 of the 47 blocks) of the control beyond 40 pc,
whose export `outofsample_v381.json` is a frozen input of the same vintage.

Referee round 27, row 53 (Ruling 17): every one of those 64 blocks was
re-extracted on the cluster with the DEPOSITED extractor and search
(`seti_extract_generic.py` sha256 dd1300e0..., the code deposit's copy) through
the same per-block driver the census's compact-array campaign used, and each
product was read into an export row by the SAME mapping that wrote the
original rows (`hostsrc/export_figdata.py`; reproduced by the harvest, whose
self-test reproduced all 315 + 198 original rows from their original products
field for field before it touched a new one).  That harvest is the frozen input
`r27inputs/holdout/holdfix_r27.json`.

WHAT THIS DOES.  Runs immediately after `apply_holdout_v381.py`.
  * keeps the pre-repair hold-out export as `holdout_export_v381_prerepair.json`
    (so the before/after comparison is generated, never typed);
  * replaces, in every hold-out row the harvest covers, exactly the measured
    columns the export carries (the list MEAS below) and nothing else -- the
    row's target, star name, naming route and the pre-registered assignment are
    untouched, because re-extraction changes the code, not the split;
  * builds `outofsample_v381.json` the same way from the frozen pre-repair
    copy `outofsample_v381_prerepair.json`;
  * records the geometry each folded row was searched on (`array`, `dish_m`,
    `syn_arcsec`, `ann_syn_factor`, `pb_arcsec`, ring radii) and its field
    provenance, and sets `provenance` to `r27-reextracted`.

Idempotent: it always starts from the pre-repair files, so a second run
writes the same bytes.

Usage: holdfix_r27.py [--drive N]   (--drive 0: no perturbation, no production path)
"""
import json
import math
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROUND = 1270
DRIVE = None
if '--drive' in sys.argv:
    DRIVE = int(sys.argv[sys.argv.index('--drive') + 1])
SFX = '' if DRIVE is None else '_drive%d' % DRIVE


def P(name):
    return os.path.join(HERE, name)


def out(name):
    b, e = os.path.splitext(name)
    return P(b + SFX + e)


HARVEST = P('r27inputs/holdout/holdfix_r27.json')
HO_IN = P('holdout_export_v381.json')            # written by apply_holdout_v381.py
HO_PRE = 'holdout_export_v381_prerepair.json'
OOS_PRE = P('outofsample_v381_prerepair.json')    # frozen input (the original file)

#: the measured columns of an export row -- exactly the fields
#: `hostsrc/export_figdata.py` reads from a product.  Nothing else is replaced.
MEAS = ('star_snr', 'src_snr', 'ctrl_max', 'ctrl_med', 'ctrl_p90', 'n_ge_star',
        'n_ctrl', 'n_src', 'dist_pc', 'eirp', 'drift_max', 'ndrift', 'onsrc',
        'rms', 'smin', 'res', 'line', 'line_off', 'likely', 'old_flag',
        'ctrl_all')
#: the window identity: must be equal, not merely matched, after the fold
IDENT = ('eb', 'band', 'flo', 'fhi', 'chanw', 'bw')
GEOM = ('array', 'dish_m', 'syn_arcsec', 'ann_syn_factor', 'pb_arcsec',
        'ring_r_in_arcsec', 'ring_r_out_arcsec', 'n_fields', 'field_retained_s',
        'extract_version', 'pos_convention')
C_M_S, ARCSEC, PB_COEF = 299792458.0, 206264.806, 1.22
RING_IN, RING_OUT = 0.14, 0.78

M, fail = [], []


def m(k, v):
    assert k.isalpha(), 'a macro name may contain letters only: %r' % k
    assert k not in [x[0] for x in M], k
    M.append((k, v))


def ck(name, cond, detail=''):
    if not cond:
        fail.append(name)
    print('  %-60s %s  %s' % (name, 'PASS' if cond else 'FAIL', detail))


def key(eb, a, b, cw):
    lo, hi = (a, b) if a <= b else (b, a)
    return (eb, round(lo, 3), round(hi, 3), round(float(cw), 1))


H = json.load(open(HARVEST))
HROWS = {s: H['rows'][s] for s in ('holdout', 'oos')}
DECL = H.get('declared_unmatched', {})


def fold(rows, hrows, tag):
    """Fold the harvest into `rows` in place.  Returns (n_folded, report)."""
    idx = {}
    for w in hrows:
        idx.setdefault(key(w['eb'], w['flo'], w['fhi'], w['chanw']), []).append(w)
    amb = [k for k, v in idx.items() if len(v) > 1]
    assert not amb, '%s: two harvest rows for one window: %s' % (tag, amb[:3])
    used, n, moved = set(), 0, []
    for r in rows:
        k = key(r['eb'], r['flo'], r['fhi'], r['chanw'])
        w = idx.get(k)
        if not w:
            continue
        w = w[0]
        for f in IDENT:
            assert w[f] == r[f], ('%s %s: identity column %s differs (%r vs %r) '
                                  '-- a different window, not a re-measurement'
                                  % (tag, k, f, w[f], r[f]))
        assert len(w['ctrl_all']) == len(r['ctrl_all']), (
            '%s %s: control ensemble %d -> %d' % (tag, k, len(r['ctrl_all']),
                                                 len(w['ctrl_all'])))
        old_t = r['star_snr']
        for f in MEAS:
            r[f] = w[f]
        for f in GEOM:
            r[f] = w.get(f)
        r['provenance'] = 'r27-reextracted'
        r['star_snr_prerepair'] = old_t
        used.add(k)
        n += 1
        moved.append((r['eb'], r['flo'], old_t, r['star_snr']))
    unused = sorted(set(idx) - used)
    return n, unused, moved


# ---------------------------------------------------------------- hold-out
# A drive may run after the build, when the hold-out export is already folded:
# it then reads the pre-repair copy this generator kept, never a production path.
_src = HO_IN
if DRIVE is not None and os.path.exists(P(HO_PRE)):
    _src = P(HO_PRE)
HO = json.load(open(_src))
assert HO['rows'] and not any(r.get('provenance') == 'r27-reextracted'
                              for r in HO['rows']), (
    'holdout_export_v381.json is already folded: run apply_holdout_v381.py '
    'first, which rewrites it from the frozen sweep')
json.dump(HO, open(out(HO_PRE), 'w'))
pre_ho = json.loads(json.dumps(HO['rows']))
n_ho, unused_ho, moved_ho = fold(HO['rows'], HROWS['holdout'], 'hold-out')

OOS = json.load(open(OOS_PRE))
pre_oos = json.loads(json.dumps(OOS['rows']))
n_oos, unused_oos, moved_oos = fold(OOS['rows'], HROWS['oos'], 'beyond-40 pc')

if DRIVE == 1:      # a harvest row that matches nothing must be caught
    unused_ho = unused_ho + [('A002_Xdrive_X1', 1.0, 2.0, 1.0)]
if DRIVE == 2:      # a 12 m row touched by the fold must be caught
    HO['rows'][0]['provenance'] = 'r27-reextracted'
    HO['rows'][0]['array'] = '12m'
if DRIVE == 3:      # a folded row whose annulus is not its own dish's
    _r = [r for r in HO['rows'] if r.get('provenance') == 'r27-reextracted'][0]
    _r['pb_arcsec'] = _r['pb_arcsec'] * 7.0 / 12.0
if DRIVE == 4:      # a non-measured column changed by the fold
    _r = [r for r in HO['rows'] if r.get('provenance') == 'r27-reextracted'][0]
    _r['star_name'] = _r['star_name'] + ' x'
if DRIVE == 5:      # a compact-array block left on the old annulus
    _r = [r for r in HO['rows'] if r.get('provenance') == 'r27-reextracted']
    _eb = _r[0]['eb']
    for r in HO['rows']:
        if r['eb'] == _eb:
            r['provenance'] = None
            r['array'] = None

print('assertions (round %d)' % ROUND)
ck('F1 every harvest row lands on exactly one exported window, in both sets',
   not unused_ho and not unused_oos,
   'unused: hold-out %s, beyond-40 pc %s' % (unused_ho[:3], unused_oos[:3]))

# F2: the fold is exactly the compact-array blocks.  The array of every block
# is the harvest's own (read from the data by the extractor), and the set of
# blocks the harvest declares ACA from the archive (obscore antenna list) must
# equal the set it re-extracted: no ACA block left behind, no 12 m block touched.
for tag, rows, sel in (('hold-out', HO['rows'], 'holdout'),
                       ('beyond-40 pc', OOS['rows'], 'oos')):
    aca = set(H['aca_blocks'][sel])
    folded = {r['eb'] for r in rows if r.get('provenance') == 'r27-reextracted'}
    twelve = [r for r in rows if r.get('provenance') == 'r27-reextracted'
              and r.get('array') != '7m']
    declared = set(DECL.get(sel, {}))
    ck('F2 %s: the re-extracted blocks are exactly its compact-array blocks, '
       'and every one is 7 m' % tag,
       folded == aca - declared and not twelve,
       '%d ACA blocks (archive), %d folded, %d declared unfoldable %s, '
       '%d folded rows not 7 m' % (len(aca), len(folded), len(declared),
                                    sorted(declared), len(twelve)))
    # every window of a folded block is folded, except windows declared by name
    part = []
    for eb in folded:
        ws = [r for r in rows if r['eb'] == eb]
        nf = [r for r in ws if r.get('provenance') != 'r27-reextracted']
        dw = DECL.get(sel + '_windows', {})
        nf = [r for r in nf if '%s|%.3f' % (eb, min(r['flo'], r['fhi'])) not in dw]
        if nf:
            part.append(eb)
    ck('F2b %s: no block is half re-extracted' % tag, not part, str(part[:3]))

# F3: the annulus each folded row was searched on is the rule of its OWN dish
bad = []
for rows in (HO['rows'], OOS['rows']):
    for r in rows:
        if r.get('provenance') != 'r27-reextracted':
            continue
        nu = 0.5 * (r['flo'] + r['fhi'])
        th = PB_COEF * C_M_S / (nu * 1e9) / float(r['dish_m']) * ARCSEC
        lo = max(RING_IN * th, float(r['ann_syn_factor']) * float(r['syn_arcsec']))
        if (abs(float(r['pb_arcsec']) - th) > 5e-3 * th
                or abs(float(r['ring_r_in_arcsec']) - lo) > 2e-3
                or abs(float(r['ring_r_out_arcsec']) - RING_OUT * th) > 2e-3
                or float(r['dish_m']) != 7.0):
            bad.append((r['eb'], round(r['flo'], 3)))
ck('F3 every re-extracted window was searched on the annulus of a 7 m dish, '
   'with the synthesised-beam floor', not bad, '%d bad %s' % (len(bad), bad[:3]))

# F4: nothing but the measured columns moved
chg = []
for pre, rows in ((pre_ho, HO['rows']), (pre_oos, OOS['rows'])):
    for a, b in zip(pre, rows):
        extra = set(b) - set(a)
        for f in set(a) | set(b):
            if f in MEAS or f in GEOM or f in ('provenance', 'star_snr_prerepair'):
                continue
            if a.get(f) != b.get(f):
                chg.append((b['eb'], f))
ck('F4 the fold changes only the measured columns (and adds geometry and '
   'provenance)', not chg, str(chg[:4]))
ck('F5 the drive set is not empty (the check is about something)',
   n_ho > 0 and n_oos > 0, '%d hold-out + %d beyond-40 pc rows folded'
   % (n_ho, n_oos))

# ---------------------------------------------------------------- outputs
if DRIVE is None:
    json.dump(HO, open(out('holdout_export_v381.json'), 'w'))
    json.dump(OOS, open(out('outofsample_v381.json'), 'w'))
TRIG = 5.0
ho_pre_x = sum(1 for r in pre_ho if r['star_snr'] >= TRIG)
ho_post_x = sum(1 for r in HO['rows'] if r['star_snr'] >= TRIG)
oos_pre_x = sum(1 for r in pre_oos if r['star_snr'] >= TRIG)
oos_post_x = sum(1 for r in OOS['rows'] if r['star_snr'] >= TRIG)
m('HoRepNWin', '%d' % n_ho)
m('HoRepNBlock', '%d' % len({r['eb'] for r in HO['rows']
                              if r.get('provenance') == 'r27-reextracted'}))
m('OosRepNWin', '%d' % n_oos)
m('OosRepNBlock', '%d' % len({r['eb'] for r in OOS['rows']
                               if r.get('provenance') == 'r27-reextracted'}))
m('HoPreNCross', '%d' % ho_pre_x)
m('OosPreNCross', '%d' % oos_pre_x)
_sv = [(a, b) for (_e, _f, a, b) in moved_ho if a >= TRIG or b >= TRIG]
m('HoRepNKept', '%d' % sum(1 for a, b in _sv if a >= TRIG and b >= TRIG))
m('HoRepNFell', '%d' % sum(1 for a, b in _sv if a >= TRIG > b))
m('HoRepNRose', '%d' % sum(1 for a, b in _sv if b >= TRIG > a))
_d = sorted(b - a for (_e, _f, a, b) in moved_ho)
m('HoRepMedDT', '%+.2f' % _d[len(_d) // 2])
_tex = ['%% GENERATED by holdfix_r27.py (round %d) -- do not hand-edit.' % ROUND]
_tex += ['\\newcommand{\\%s}{%s}' % kv for kv in M]
open(out('survey_numbers_round%d.tex' % ROUND), 'w').write('\n'.join(_tex) + '\n')
audit = dict(round=ROUND, folded_holdout=n_ho, folded_oos=n_oos,
             crossings_holdout=[ho_pre_x, ho_post_x],
             crossings_oos=[oos_pre_x, oos_post_x],
             moved_holdout=moved_ho, moved_oos=moved_oos,
             harvest=os.path.relpath(HARVEST, HERE),
             harvest_meta={k: v for k, v in H.items() if k != 'rows'})
json.dump(audit, open(out('holdfix_r27_audit.json'), 'w'), indent=1)
print('holdfix_r27: %d hold-out + %d beyond-40 pc windows re-read from the '
      'repaired extraction; crossings %d -> %d and %d -> %d'
      % (n_ho, n_oos, ho_pre_x, ho_post_x, oos_pre_x, oos_post_x))
if fail:
    print('FAILED: %s' % fail)
    sys.exit(1 if DRIVE is None else 3)
