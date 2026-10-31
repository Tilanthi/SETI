#!/usr/bin/env python3
r"""extfix_r27.py -- the archival extension's compact-array blocks, re-read from
their RE-EXTRACTION on the repaired control annulus (round 1280).

WHY THIS EXISTS.  The census's compact-array windows were re-extracted on
2026-09-23/24 with the control annulus scaled to the dish that observed them
(7 m, with the synthesised-beam floor).  The archival extension never was:
`export_extension.json` is a snapshot (2026-09-22) of products made on
2026-09-21/22 by the archive-mining lanes, BEFORE that repair.  85 of its 123
blocks (340 of its 495 windows) are compact-array (7 m) blocks, so they were
searched on a 12 m annulus inside a 7 m beam, and the paper's sentence that
every set was "searched with the same pipeline" was false for them -- the same
defect `holdfix_r27.py` repairs for the hold-out (referee round 27, row 53).

Referee round 27, row 58 (Rulings 22 and 25): every one of those 85 blocks was
re-extracted on the cluster with the DEPOSITED extractor and search
(`seti_extract_generic.py` sha256 dd1300e0..., the code deposit's copy) through
the same per-block driver the census's compact-array campaign used, and each
product was read into an export row by the SAME mapping that wrote the
original rows (`mine2026/export_ext.py`; the harvest's self-test reproduced all
495 original rows from their original products, 30 fields each, before it
touched a new one).  The array of every block is the ALMA archive's (obscore
antenna list by member OUS), not inferred from a product.  That harvest is the
frozen input `r27inputs/extension/extfix_r27.json`.

WHAT THIS DOES.  Runs before the first reader of the extension export.
  * reads the ORIGINAL snapshot `export_extension_prerepair.json` (a frozen
    input, byte-identical to the v4.27 `export_extension.json`), so a second
    run writes the same bytes and the before/after comparison is generated;
  * replaces, in every row the harvest covers, exactly the fields the export
    mapping reads from a product (MEAS below) and nothing else -- the row's
    target, star name, naming route and member OUS are untouched, because
    re-extraction changes the code, not the sample;
  * records the geometry each folded row was searched on and sets
    `provenance` to `r27-reextracted`;
  * writes `export_extension.json`, which every downstream reader opens.

Usage: extfix_r27.py [--drive N]   (--drive 0: no perturbation, no production path)
"""
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROUND = 1280
DRIVE = None
if '--drive' in sys.argv:
    DRIVE = int(sys.argv[sys.argv.index('--drive') + 1])
SFX = '' if DRIVE is None else '_drive%d' % DRIVE


def P(name):
    return os.path.join(HERE, name)


def out(name):
    b, e = os.path.splitext(name)
    return P(b + SFX + e)


HARVEST = P('r27inputs/extension/extfix_r27.json')
PRE = P('export_extension_prerepair.json')        # frozen input (the v4.27 snapshot)

#: every field `mine2026/export_ext.py` reads from a product, less the window
#: identity (IDENT), which must be EQUAL after the fold, not replaced
MEAS = ('ctrl_all', 'ctrl_max', 'ctrl_med', 'ctrl_p90', 'dist_pc', 'drift_max',
        'eirp', 'likely', 'line', 'line_off', 'n_ctrl', 'n_ge_star', 'n_src',
        'ndrift', 'old_flag', 'onsrc', 'res', 'rms', 'smin', 'src_snr',
        'star_snr', '_n_hits', '_star_peak_freq')
IDENT = ('eb', 'band', 'flo', 'fhi', 'chanw', 'bw', '_spw')
GEOM = ('array', 'dish_m', 'syn_arcsec', 'ann_syn_factor', 'pb_arcsec',
        'ring_r_in_arcsec', 'ring_r_out_arcsec', 'n_fields', 'field_retained_s',
        'extract_version', 'pos_convention', 'pbgeom')
C_M_S, ARCSEC, PB_COEF = 299792458.0, 206264.806, 1.22
RING_IN, RING_OUT = 0.14, 0.78
TRIG = 5.0

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
EXT = json.load(open(PRE))
assert EXT['rows'] and not any(r.get('provenance') == 'r27-reextracted'
                               for r in EXT['rows']), (
    'export_extension_prerepair.json is already folded -- it must be the '
    'original 2026-09-22 snapshot')
pre = json.loads(json.dumps(EXT['rows']))

idx = {}
for w in H['rows']:
    idx.setdefault(key(w['eb'], w['flo'], w['fhi'], w['chanw']), []).append(w)
amb = [k for k, v in idx.items() if len(v) > 1]
assert not amb, 'two harvest rows for one window: %s' % amb[:3]
used, moved = set(), []
for r in EXT['rows']:
    k = key(r['eb'], r['flo'], r['fhi'], r['chanw'])
    w = idx.get(k)
    if not w:
        continue
    w = w[0]
    for f in IDENT:
        assert w[f] == r[f], ('%s: identity column %s differs (%r vs %r) -- a '
                              'different window, not a re-measurement'
                              % (k, f, w[f], r[f]))
    assert len(w['ctrl_all']) == len(r['ctrl_all']), (
        '%s: control ensemble %d -> %d' % (k, len(r['ctrl_all']),
                                          len(w['ctrl_all'])))
    old_t = r['star_snr']
    for f in MEAS:
        r[f] = w[f]
    for f in GEOM:
        r[f] = w.get(f)
    r['provenance'] = 'r27-reextracted'
    r['star_snr_prerepair'] = old_t
    used.add(k)
    moved.append((r['eb'], r['flo'], old_t, r['star_snr'], r['star_name']))
unused = sorted(set(idx) - used)
# every row carries the ARCHIVE's array (obscore antenna list by member OUS), so
# a reader never has to infer the dish from a stored beam width -- the very
# inference the 12 m annulus defect made.  The 12 m rows are otherwise untouched.
for r in EXT['rows']:
    if r['eb'] in H['twelve_m_blocks']:
        r['array'] = '12m'
# v4.29 (round 27 Rulings 29/31): 12 m extension blocks re-calibrated with ALMA's final flags and re-searched
# with the deposited extractor have no r27 row (they were never on the defective annulus); their measured
# columns come from the new product (r29inputs/reflag/reflag_ext12m_r29.json, built by the re-flag fold).
# Only MEAS moves (E4 holds); provenance is not changed, so E2's fold set is still the r27 one.
_R29 = P('r29inputs/reflag/reflag_ext12m_r29.json')
N_R29 = 0
if os.path.exists(_R29):
    for _w in json.load(open(_R29))['rows']:
        _i = _w['ident']
        _m = [r for r in EXT['rows'] if key(r['eb'], r['flo'], r['fhi'], r['chanw'])
              == key(_i['eb'], _i['flo'], _i['fhi'], _i['chanw'])]
        assert len(_m) == 1, ('r29 12 m row matches %d export rows' % len(_m), _i)
        _r = _m[0]
        assert _r['eb'] in H['twelve_m_blocks'] and _r.get('provenance') is None, (
            'r29 12 m pass may touch only untouched 12 m rows', _i)
        for f in ('eb', 'flo', 'fhi', 'chanw'):
            assert _r[f] == _i[f], ('r29 12 m identity', f, _r[f], _i[f])
        assert len(_w['meas']['ctrl_all']) == len(_r['ctrl_all']), ('r29 12 m control ensemble', _i)
        for f in MEAS:
            _r[f] = _w['meas'][f]
        N_R29 += 1

if DRIVE == 1:      # a harvest row that matches nothing must be caught
    unused = unused + [('A002_Xdrive_X1', 1.0, 2.0, 1.0)]
#: r27 row 59: the 12 m blocks re-extracted because their FIELD rows were
#: truncated (FIELDTRUNC.md Row 59) -- the only 12 m blocks the fold may touch.
FT = set(H.get('fieldtrunc_blocks', []))
if DRIVE == 2:      # a 12 m row touched by the fold must be caught
    _r = [r for r in EXT['rows'] if r['eb'] in H['twelve_m_blocks']
          and r['eb'] not in FT][0]
    _r['provenance'] = 'r27-reextracted'
    _r['array'] = '12m'
if DRIVE == 3:      # a folded row whose annulus is not its own dish's
    _r = [r for r in EXT['rows'] if r.get('provenance') == 'r27-reextracted'][0]
    _r['pb_arcsec'] = _r['pb_arcsec'] * 7.0 / 12.0
if DRIVE == 4:      # a non-measured column changed by the fold
    _r = [r for r in EXT['rows'] if r.get('provenance') == 'r27-reextracted'][0]
    _r['star_name'] = _r['star_name'] + ' x'
if DRIVE == 5:      # a compact-array block left on the old annulus
    _r = [r for r in EXT['rows'] if r.get('provenance') == 'r27-reextracted']
    _eb = _r[0]['eb']
    for r in EXT['rows']:
        if r['eb'] == _eb:
            r['provenance'] = None
            r['array'] = None

print('assertions (round %d)' % ROUND)
ck('E1 every harvest row lands on exactly one exported window', not unused,
   'unused: %s' % (unused[:3],))

# E2: the fold is exactly the compact-array blocks, by the ARCHIVE's array
aca = set(H['aca_blocks'])
folded = {r['eb'] for r in EXT['rows'] if r.get('provenance') == 'r27-reextracted'}
notseven = [r for r in EXT['rows'] if r.get('provenance') == 'r27-reextracted'
            and r.get('array') != '7m' and r['eb'] not in FT]
ftbad = [r['eb'] for r in EXT['rows'] if r['eb'] in FT
         and (r.get('provenance') != 'r27-reextracted' or r.get('array') != '12m')]
ck('E2 the re-extracted blocks are exactly the compact-array blocks plus the '
   'declared field-truncated 12 m blocks (row 59), every ACA one 7 m and every '
   'field-repaired one 12 m',
   folded == aca | FT and not notseven and not ftbad
   and FT <= set(H['twelve_m_blocks']),
   '%d ACA blocks (archive), %d field-repaired 12 m, %d folded, %d folded rows '
   'not 7 m outside the declared set, %d declared rows not folded on 12 m'
   % (len(aca), len(FT), len(folded), len(notseven), len(ftbad)))
part = [eb for eb in folded
        if any(r.get('provenance') != 'r27-reextracted'
               for r in EXT['rows'] if r['eb'] == eb)]
ck('E2b no block is half re-extracted', not part, str(part[:3]))
ck('E2c the archive partitions the snapshot into 7 m and 12 m blocks',
   aca | set(H['twelve_m_blocks']) == set(EXT['blocks'])
   and not aca & set(H['twelve_m_blocks']),
   '%d + %d = %d blocks' % (len(aca), len(H['twelve_m_blocks']),
                            len(EXT['blocks'])))

# E3: the annulus each folded row was searched on is the rule of its OWN dish
bad = []
for r in EXT['rows']:
    if r.get('provenance') != 'r27-reextracted':
        continue
    dish = 12.0 if r['eb'] in FT else 7.0
    if any(r.get(f) is None for f in ('dish_m', 'pb_arcsec', 'syn_arcsec',
                                       'ann_syn_factor', 'ring_r_in_arcsec',
                                       'ring_r_out_arcsec')):
        bad.append((r['eb'], round(r['flo'], 3)))      # no geometry recorded
        continue
    nu = 0.5 * (r['flo'] + r['fhi'])
    th = PB_COEF * C_M_S / (nu * 1e9) / float(r['dish_m']) * ARCSEC
    lo = max(RING_IN * th, float(r['ann_syn_factor']) * float(r['syn_arcsec']))
    if (abs(float(r['pb_arcsec']) - th) > 5e-3 * th
            or abs(float(r['ring_r_in_arcsec']) - lo) > 2e-3
            or abs(float(r['ring_r_out_arcsec']) - RING_OUT * th) > 2e-3
            or float(r['dish_m']) != dish):
        bad.append((r['eb'], round(r['flo'], 3)))
ck('E3 every re-extracted window was searched on the annulus of its own dish '
   '(7 m, or 12 m for a declared field-repaired block), with the '
   'synthesised-beam floor', not bad, '%d bad %s' % (len(bad), bad[:3]))

# E4: nothing but the measured columns moved
chg = []
for a, b in zip(pre, EXT['rows']):
    for f in set(a) | set(b):
        if f in MEAS or f in GEOM or f in ('provenance', 'star_snr_prerepair'):
            continue
        if a.get(f) != b.get(f):
            chg.append((b['eb'], f))
ck('E4 the fold changes only the measured columns (and adds geometry and '
   'provenance)', not chg, str(chg[:4]))
ck('E5 the drive set is not empty (the check is about something)',
   len(moved) > 0, '%d rows folded' % len(moved))

# ---------------------------------------------------------------- outputs
if DRIVE is None:
    json.dump(EXT, open(out('export_extension.json'), 'w'))
in85 = [x for x in moved]
pre_x = sum(1 for x in in85 if x[2] >= TRIG)
post_x = sum(1 for x in in85 if x[3] >= TRIG)
all_pre_x = sum(1 for r in pre if r.get('star_snr') is not None
                and r['star_snr'] >= TRIG)
all_post_x = sum(1 for r in EXT['rows'] if r.get('star_snr') is not None
                 and r['star_snr'] >= TRIG)
m('ExRepNWin', '%d' % len(moved))
m('ExRepNBlock', '%d' % len(folded))
m('ExRepNKept', '%d' % sum(1 for x in in85 if x[2] >= TRIG and x[3] >= TRIG))
m('ExRepNFell', '%d' % sum(1 for x in in85 if x[2] >= TRIG > x[3]))
m('ExRepNRose', '%d' % sum(1 for x in in85 if x[3] >= TRIG > x[2]))
m('ExRepPreNCross', '%d' % pre_x)
m('ExRepPostNCross', '%d' % post_x)
_d = sorted(x[3] - x[2] for x in in85)
m('ExRepMedDT', '%+.2f' % _d[len(_d) // 2])
_on = [(a, b) for a, b in zip(pre, EXT['rows'])
       if b.get('provenance') == 'r27-reextracted'
       and abs(float(b['onsrc']) - float(a['onsrc'])) > 1e-3 * float(a['onsrc'])]
m('ExRepNOnsrcWin', '%d' % len(_on))
m('ExRepNOnsrcBlock', '%d' % len({b['eb'] for a, b in _on}))
_tex = ['%% GENERATED by extfix_r27.py (round %d) -- do not hand-edit.' % ROUND]
_tex += ['\\newcommand{\\%s}{%s}' % kv for kv in M]
open(out('numbers/survey_numbers_round%d.tex' % ROUND), 'w').write('\n'.join(_tex) + '\n')
audit = dict(round=ROUND, folded=len(moved), folded_blocks=len(folded),
             crossings_in_folded=[pre_x, post_x],
             crossings_all=[all_pre_x, all_post_x],
             moved=moved,
             harvest=os.path.relpath(HARVEST, HERE),
             harvest_meta={k: v for k, v in H.items() if k != 'rows'})
json.dump(audit, open(out('extfix_r27_audit.json'), 'w'), indent=1)
print('extfix_r27: %d extension windows in %d blocks re-read from the repaired '
      'extraction; crossings in them %d -> %d (whole extension %d -> %d)'
      % (len(moved), len(folded), pre_x, post_x, all_pre_x, all_post_x))
if fail:
    print('FAILED: %s' % fail)
    sys.exit(1 if DRIVE is None else 3)
