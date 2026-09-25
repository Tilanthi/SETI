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


TRIG, SEL, SEL_CI = {}, {}, {}
for _c, _k in _KEY.items():
    _s = _S[_k]
    TRIG[_c] = _cross(_s['ladder'], 'frac_trig_only')
    SEL[_c] = _s['P90_over_trigger']
    SEL_CI[_c] = tuple(_s['P90_ci68'])
    assert SEL[_c] is not None and TRIG[_c] is not None, (
        'the campaign does not resolve a 90 per cent point for %s' % _k)
    assert SEL[_c] > TRIG[_c], (
        'the control gate cannot make a carrier easier to find: %s trigger '
        '%.2f, through the gate %.2f' % (_k, TRIG[_c], SEL[_c]))

#: the campaign passed its own controls, or none of this may be quoted
assert _S['all']['null_recovered'] == 0
assert all(_S[k]['positive_control_frac'] >= 0.95 for k in _KEY.values())

#: rows in the catalogue carry `resolution_class`; map it to a stratum
def cls_of(row):
    return 'fine' if row.get('resolution_class') == 'fine' else 'coarse'


if __name__ == '__main__':
    for c in ('all', 'fine', 'coarse'):
        print('%-7s trigger P90 = %.2f x P_trig, selection P90 = %.2f '
              '(68%% CI %.2f-%.2f), gate costs x%.2f'
              % (c, TRIG[c], SEL[c], SEL_CI[c][0], SEL_CI[c][1],
                 SEL[c] / TRIG[c]))
