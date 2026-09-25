#!/usr/bin/env python3
"""Build the CORRECTED survey export from the repaired ACA extraction.

`v342_calc.py` builds the released per-window catalogue from a single
frozen export, and every other generator reads the catalogue. So the one
correct place to fold in the repaired extraction is the export itself: do
it here and the whole downstream chain follows, with all of its existing
cross-assertions still guarding the result.

Patching the catalogue CSV after the fact does NOT work -- `v342_calc.py`
rewrites it from the export on every build, so the patch is silently
discarded. That was tried first and is recorded here so it is not tried
again.

What is replaced, per matched window: the stellar statistic, the full
512-element control vector and the summaries derived from it, the noise and
sensitivity columns, the nearest-line association, and the peak frequency
and drift rate (which the original extraction did not retain and referee 2
required, M1).

What is NOT replaced: anything the re-extraction did not measure. Windows
outside the 278 re-extracted blocks are copied through untouched.

Writes corrected_export_v399.json and corrected_export_v399_audit.json.
"""
import json
import os

HERE = os.path.dirname(os.path.abspath(__file__))
FROZEN = os.path.join(HERE, 'frozen_export_v3.81_survey.json')
OUT = os.path.join(HERE, 'corrected_export_v399.json')

D = json.load(open(FROZEN))
ROWS = D['rows']
NEW = json.load(open(os.path.join(HERE, 'acafull_v399.json')))
GEOM = json.load(open(os.path.join(HERE, 'acageom_v399.json')))


def key(eb, a, b):
    """Match on sorted frequency bounds: the products store flo/fhi in
    tuning order, which is descending for half the windows."""
    lo, hi = (a, b) if a <= b else (b, a)
    return (eb, round(lo, 3), round(hi, 3))


prod = {}
for w in NEW:
    if w.get('flo') is None or w.get('star_snr') is None:
        continue
    prod.setdefault(key(w['eb'], w['flo'], w['fhi']), []).append(w)

n_upd = n_amb = 0
moved = []
for r in ROWS:
    k = key(r['eb'], float(r['flo']), float(r['fhi']))
    cand = prod.get(k)
    if not cand:
        continue
    if len(cand) > 1:
        n_amb += 1
        continue
    w = cand[0]
    ca = w['ctrl_all']
    assert len(ca) == len(r['ctrl_all']), (
        'control vector length changed for %s (%d -> %d); the downstream '
        'rank statistics assume a fixed ensemble size'
        % (w['eb'], len(r['ctrl_all']), len(ca)))
    old_star = r.get('star_snr')

    r['star_snr'] = w['star_snr']
    r['ctrl_all'] = ca
    s = sorted(ca)
    r['ctrl_max'] = max(ca)
    r['ctrl_med'] = s[len(s) // 2]
    r['ctrl_p90'] = s[int(0.9 * (len(s) - 1))]
    r['n_ge_star'] = int(w['n_ge'])
    r['n_ctrl'] = int(w['n_ctrl'])
    if w.get('src') is not None:
        r['src_snr'] = w['src']
    for a, b in (('eirp', 'eirp'), ('smin', 'smin'), ('rms', 'rms')):
        if w.get(b) is not None:
            r[a] = w[b]
    if w.get('line') is not None:
        r['line'] = w['line'] or None
    if w.get('line_off') is not None:
        r['line_off'] = w['line_off']
    # referee 2, M1: the cell the statistic peaked in, now retained
    if w.get('pkf'):
        r['f_cross'] = w['pkf']
    if w.get('pkd') is not None:
        r['drift_peak'] = w['pkd']
    g = GEOM.get('%s|%d' % (w['eb'], w['spw']))
    if g:
        r['dish_m'] = g['dish']
        r['syn_arcsec'] = g['syn']
        r['r_in_arcsec'] = g['rin']
    if w.get('pb'):
        r['pb_arcsec'] = w['pb']
        r['r_out_arcsec'] = 0.78 * w['pb']
    r['provenance'] = 'corrected-geometry'
    n_upd += 1
    if old_star:
        moved.append(w['star_snr'] / old_star)

for r in ROWS:
    r.setdefault('provenance', 'frozen-geometry')

assert n_upd, 'no rows were updated; the match key is probably wrong'
D['rows'] = ROWS
D['corrected'] = dict(n_updated=n_upd, n_ambiguous=n_amb,
                      source='ACA re-extraction 2026-09-23/24')
json.dump(D, open(OUT, 'w'))

moved.sort()
audit = dict(rows=len(ROWS), updated=n_upd, ambiguous=n_amb,
             tstar_ratio_median=moved[len(moved) // 2] if moved else None,
             tstar_ratio_p10=moved[len(moved) // 10] if moved else None,
             tstar_ratio_p90=moved[9 * len(moved) // 10] if moved else None)
json.dump(audit, open(os.path.join(HERE, 'corrected_export_v399_audit.json'),
                      'w'), indent=1)
print('corrected export: %d rows, %d updated, %d ambiguous' % (len(ROWS), n_upd,
                                                               n_amb))
print('  T* new/old: median %.4f (10th %.3f, 90th %.3f)'
      % (audit['tstar_ratio_median'], audit['tstar_ratio_p10'],
         audit['tstar_ratio_p90']))
