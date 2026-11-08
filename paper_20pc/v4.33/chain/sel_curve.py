#!/usr/bin/env python3
"""The measured recovery curve, shared so that no two generators can drift.

This is the v4.00 replacement for inject_curve.py as the source of the
survey's completeness numbers. inject_curve.py described a campaign that
injected into retained per-integration spectra AFTER the baseline step and
never passed through the 512-control rank; the numbers here come from
carriers injected into calibrated VISIBILITIES and recovered through the
unmodified pipeline, trigger and rank included.

Two ratios are published, both as multiples of a window's own nominal
trigger power:

    TRIG[cls]  the 90 per cent point of the TRIGGER-only curve, which is
               what P_90 has always meant in this paper;
    SEL[cls]   the 90 per cent point of the curve scored on the full
               criterion, trigger AND star above all 512 controls, which
               is P_90^sel.

They are given per resolution class because the two classes behave
differently: a coarse channel needs almost no de-drifting, and its control
ensemble is correspondingly less contaminated by the injected source, so
the gate costs it far less.

BOTH MULTIPLY THE NOMINAL TRIGGER AND NOTHING ELSE. An end-to-end measured
ratio already contains the instrumental spectral response and the drift
smear, so applying it to a response-corrected power would count those
twice. Every consumer of this module is written that way and asserts it.
"""
import json
import os

HERE = os.path.dirname(os.path.abspath(__file__))
_D = json.load(open(os.path.join(HERE, 'm3a_result_v400.json')))
_S = {x['stratum']: x for x in _D['strata']}

_KEY = {'fine': 'fine (<1 MHz)', 'coarse': 'coarse (>5 MHz)', 'all': 'all'}


def _cross(ladder, key, level=0.9):
    xs = [r['amp_over_trig'] for r in ladder]
    ys = [r[key] for r in ladder]
    for j in range(1, len(xs)):
        if ys[j - 1] < level <= ys[j]:
            w = (level - ys[j - 1]) / (ys[j] - ys[j - 1])
            return xs[j - 1] + w * (xs[j] - xs[j - 1])
    return None


# ---------------------------------------------------------------------------
# v4.06 (DECISIONS_R8 D14).  THE HEADLINE COMPLETENESS IS NOW MEASURED THROUGH
# THE CHAIN THE SURVEY ACTUALLY USES: trigger -> visibility localisation.
#
# Round-7 decision A2 demoted the 512-position rank screen from a filter to a
# consistency check, because correctly pointed out it rejects nothing.  A
# completeness measured THROUGH that screen therefore charges the published
# limit for a gate the analysis does not apply -- and charges it a factor of
# about two in Class A.  Both are published; the rank-gated value is retained
# below as SEL_RANK and is labelled superseded wherever it is quoted.
#
# ★ The two numbers come from DIFFERENT CAMPAIGNS (M3a for the rank gate, the
# round-7 campaign for localisation), so the trigger-only reference must come
# from the SAME campaign as the selection value it is compared with.  Mixing
# M3a's trigger-only 2.99 with round 7's localisation 2.88 would manufacture a
# gain out of two unrelated measurements; TRIG and SEL are therefore both taken
# from the round-7 analysis, and the M3a pair is kept together as _M3A.
_R7 = json.load(open(os.path.join(HERE,
                                  'r8inputs/p90_r7_analysis_v406.json')))
_RS = {'fine': 'class A', 'coarse': 'class B', 'all': 'all'}
assert _R7['gates']['campaign_valid'], 'the round-7 campaign did not validate'
assert _R7['gates']['null_frac_localised'] < _R7['gates'][
    'null_ceiling_prefixed'], _R7['gates']
assert _R7['gates']['positive_control_frac'] >= 0.95, _R7['gates']

TRIG, SEL, SEL_CI = {}, {}, {}
TRIG_M3A, SEL_RANK, SEL_RANK_CI = {}, {}, {}
for _c, _k in _KEY.items():
    _s = _S[_k]
    TRIG_M3A[_c] = _cross(_s['ladder'], 'frac_trig_only')
    SEL_RANK[_c] = _s['P90_over_trigger']
    SEL_RANK_CI[_c] = tuple(_s['P90_ci68'])
    assert SEL_RANK[_c] is not None and TRIG_M3A[_c] is not None, (
        'the campaign does not resolve a 90 per cent point for %s' % _k)
    assert SEL_RANK[_c] > TRIG_M3A[_c], (
        'the control gate cannot make a carrier easier to find: %s trigger '
        '%.2f, through the gate %.2f' % (_k, TRIG_M3A[_c], SEL_RANK[_c]))
    _r = _R7['saturation'][_RS[_c]]
    TRIG[_c] = float(_r['P90_trigger'])
    SEL[_c] = float(_r['P90_loc'])
    SEL_CI[_c] = tuple(float(x) for x in _r['P90_loc_ci68'])
    # Localisation is a further requirement, so it cannot make a carrier
    # easier to find either.  In Class A it costs 0.2 per cent, which IS the
    # finding: the visibility clauses reject essentially nothing at T* ~ 5.
    assert SEL[_c] >= TRIG[_c] - 1e-9, (_c, TRIG[_c], SEL[_c])
    assert _r['trigger_and_localised']['reaches_90'], _c

#: the campaign passed its own controls, or none of this may be quoted
assert _S['all']['null_recovered'] == 0
assert all(_S[k]['positive_control_frac'] >= 0.95 for k in _KEY.values())

#: ★ the redefinition must MOVE the Class A limit by about the factor D14
#: states, or the change is not the one the paper describes.  Driven in both
#: directions by selftest_v406.py.
GAIN = {c: SEL_RANK[c] / SEL[c] for c in _KEY}
assert 1.5 < GAIN['fine'] < 2.5, GAIN
#: ... and the rank gate's cost must be the reason, i.e. the trigger-only
#: points of the two campaigns must agree to well within that factor, or the
#: difference is between campaigns and not between criteria.
assert abs(TRIG['fine'] / TRIG_M3A['fine'] - 1.0) < 0.10, (TRIG['fine'],
                                                           TRIG_M3A['fine'])

#: rows in the catalogue carry `resolution_class`; map it to a stratum
def cls_of(row):
    return 'fine' if row.get('resolution_class') == 'fine' else 'coarse'


if __name__ == '__main__':
    for c in ('all', 'fine', 'coarse'):
        print('%-7s trigger P90 = %.2f x P_trig, PUBLISHED (trigger+localised) '
              'P90 = %.2f (68%% CI %.2f-%.2f); superseded rank-gated %.2f, '
              'i.e. the rank screen cost x%.2f'
              % (c, TRIG[c], SEL[c], SEL_CI[c][0], SEL_CI[c][1],
                 SEL_RANK[c], GAIN[c]))
