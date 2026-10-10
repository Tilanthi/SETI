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

# ---------------------------------------------------------------------------
# v4.07.  THE MATCH KEY CARRIES NO STAR, AND acafull_v399.json CARRIES NO
# TARGET FIELD, so a product cannot be attributed to a star even in principle.
# 35 physical windows of this survey contain more than one catalogued star (two
# stars inside one primary beam is legitimate and happens in nine fields), and
# for such a window ONE star's re-extraction is written onto BOTH rows.  The
# n_amb guard cannot see it: that fires only when the harvest holds TWO
# products for a window.
#
# This is not hypothetical.  It happened at v3.99 to the HD 139084 field and it
# silently DELETED A COUNTED CROSSING: `per_target_results_v3.81/84.csv` ship
# HD 139084B ...805632 at 345.1449 GHz with T* = 5.6634 and crossing = True,
# and after this stage both rows carry the ...921024 values.  The same release
# moved the crossing count for a dozen other reasons, so nothing reported it.
#
# Until the harvest records which target directory each product came from, the
# only defensible behaviour is to REFUSE to spread one product over two stars
# unless the case is declared here, naming the star the product belongs to and
# what becomes of the others.  `fieldfix_v404.py` carries the same guard,
# because the queued 42-block re-extraction runs through it.
MULTISTAR_DECLARED = {
    # (eb, star whose extraction this is): what happens to the other rows
    ('A002_Xcd8029_Xb6b0', 'HD 139084B 921024'):
        'HD 139084 (= V343 Nor A, the misnamed primary) is the extraction '
        'these products are; the HD 139084B rows they also overwrote are '
        'dropped by censusfix_v407.py and the companion is disclosed as '
        'covered, extracted and not represented in this release',
}
_bystar = {}
for r in ROWS:
    k = key(r['eb'], float(r['flo']), float(r['fhi']))
    if k in prod and len(prod[k]) == 1:
        _bystar.setdefault(k, set()).add(r['star_name'])
_spread = sorted((k, sorted(v)) for k, v in _bystar.items() if len(v) > 1)
_undeclared = [(k, v) for k, v in _spread
               if not any((k[0], s) in MULTISTAR_DECLARED for s in v)]
assert not _undeclared, (
    'one re-extraction product would be applied to rows of %d different stars '
    'in %d window(s): %s.  The harvest carries no target, so the product '
    'cannot be attributed; declare the case in MULTISTAR_DECLARED or give the '
    'harvest a star field.  Applied blind, this overwrites one star with '
    'another and has already destroyed a counted crossing once (v3.99, '
    'HD 139084B at 345.1449 GHz, T* = 5.6634).'
    % (max(len(v) for _, v in _undeclared), len(_undeclared),
       [(k[0], round(k[1], 4), v) for k, v in _undeclared[:4]]))

n_upd = n_amb = n_spread_rows = 0
moved = []
for r in ROWS:
    k = key(r['eb'], float(r['flo']), float(r['fhi']))
    cand = prod.get(k)
    if not cand:
        continue
    if len(cand) > 1:
        n_amb += 1
        continue
    if k in _bystar and len(_bystar[k]) > 1:
        n_spread_rows += 1
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
                      n_multistar_rows=n_spread_rows,
                      n_multistar_windows=len(_spread),
                      source='ACA re-extraction 2026-09-23/24')
# ---- round 8: the field-selection repair, applied inside this stage so that
# not one of the seventeen generators that read the export has to change.
# A no-op until the re-extraction harvest (fieldfix_r8.json) exists.
import fieldfix_v404
n_field = fieldfix_v404.apply(ROWS)
if n_field:                     # absent, not zero, so a pre-campaign build of
    D['field_repaired'] = n_field   # the export stays byte-identical

# ---- v4.07: the census name-collision repair, applied in the same stage and
# for the same reason.  It MUST come after the two re-extraction repairs: it
# identifies which star a row's EIRP was computed for, and both repairs above
# rewrite `eirp`.  Running it earlier would test the identity on values that
# are about to be replaced.
import censusfix_v407
n_ren, n_drop = censusfix_v407.apply(ROWS)
D['rows'] = ROWS
D['census_repaired'] = dict(renamed=n_ren, dropped=n_drop)
n_cen = censusfix_v407.repair_census_list(D.get('census'))
assert n_cen == len(censusfix_v407.RENAME), (
    'the export embeds a census of %d entries and only %d of %d declared '
    'renames landed in it' % (len(D.get('census') or []), n_cen,
                             len(censusfix_v407.RENAME)))

json.dump(D, open(OUT, 'w'))

moved.sort()
audit = dict(rows=len(ROWS), updated=n_upd, ambiguous=n_amb,
             tstar_ratio_median=moved[len(moved) // 2] if moved else None,
             tstar_ratio_p10=moved[len(moved) // 10] if moved else None,
             tstar_ratio_p90=moved[9 * len(moved) // 10] if moved else None)
json.dump(audit, open(os.path.join(HERE, 'corrected_export_v399_audit.json'),
                      'w'), indent=1)
print('corrected export: %d rows, %d updated, %d ambiguous, %d rows in %d '
      'declared multi-star window(s)' % (len(ROWS), n_upd, n_amb,
                                         n_spread_rows, len(_spread)))
print('  T* new/old: median %.4f (10th %.3f, 90th %.3f)'
      % (audit['tstar_ratio_median'], audit['tstar_ratio_p10'],
         audit['tstar_ratio_p90']))
