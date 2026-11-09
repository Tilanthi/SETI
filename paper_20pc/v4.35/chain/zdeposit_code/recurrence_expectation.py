#!/usr/bin/env python3
"""Rebuild the widened-window recurrence comparison from the deposited inputs.

    python3 recurrence_expectation.py [--data DIR] [--json FILE]

Reads statistics/recurrence_windows.csv, statistics/look_elsewhere_groups.csv,
statistics/recurrence_parameters.csv and statistics/control_field_statistics.csv
and nothing else, and prints:

  the whole comparison    the distinct covering windows (each window of a
                          block of another session, more than a day from the
                          discovery, that covers an unattributed crossing's
                          frequency), how many hold a statistic at or above
                          the trigger, the number the windows' own control
                          positions predict (the sum of each window's control
                          trigger rate) and the exact Poisson-binomial
                          probability of a count at least that large
  the two objects         the share of that expectation and of the count
                          toward the two objects the article names, and the
                          same comparison over the remaining windows
  each of the two         its count, its expectation from the per-window rates
                          of control_field_statistics.csv, and its own tail
  the look-elsewhere      how often chance makes some object's own tail as
                          small as the more discrepant object's: every
                          object's count drawn from its own Poisson-binomial
                          distribution, replayed draw for draw from the
                          deposited seed, simulations in the deposited order

The Poisson-binomial distribution is computed exactly, by convolution.  Needs
Python 3 and numpy.
"""
import argparse
import collections
import csv
import json
import os
import sys

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
AP = argparse.ArgumentParser(description=__doc__.split('\n')[0])
AP.add_argument('--data', default=os.path.join(HERE, '..'))
AP.add_argument('--json', default=None)


def read(path):
    with open(path, newline='') as fh:
        return list(csv.DictReader(fh))


def pb_pmf(ps):
    d = np.zeros(len(ps) + 1)
    d[0] = 1.0
    for i, p in enumerate(ps):
        d[1:i + 2] = d[1:i + 2] * (1.0 - p) + d[0:i + 1] * p
        d[0] *= (1.0 - p)
    return d


def pb_tail(ps, k):
    return float(pb_pmf(ps)[k:].sum())


def look_elsewhere(rng, n_sim, groups, p_obs):
    mins = np.ones(n_sim)
    for ps in groups:
        d = pb_pmf(ps)
        t = np.cumsum(d[::-1])[::-1]
        mins = np.minimum(mins, t[rng.choice(len(d), size=n_sim, p=d / d.sum())])
    return float((mins <= p_obs).mean())


def main():
    a = AP.parse_args()
    st = os.path.join(os.path.abspath(a.data), 'statistics')
    par = {r['parameter']: r['value'] for r in read(os.path.join(st, 'recurrence_parameters.csv'))}
    win = sorted(read(os.path.join(st, 'recurrence_windows.csv')),
                 key=lambda r: int(r['window_order']))
    seed, n_sim = int(par['seed']), int(par['n_sim'])
    hd, jx = par['first_object'], par['second_object']
    two = [par['first_star'], par['second_star']]
    print('numpy %s; data %s' % (np.__version__, os.path.abspath(a.data)))

    # ---------------------------------------------------- the whole comparison
    above = [r['above_trigger'] == '1' for r in win]
    n_win, n_exc = len(win), sum(above)
    ps = [float(r['p_trig_ctrl']) for r in win if r['p_trig_ctrl'] != '']
    exp_all, p_all = sum(ps), pb_tail(ps, n_exc)
    exc_star = collections.Counter(r['star'] for r, ab in zip(win, above) if ab)
    if min(exc_star[s] for s in two) < max([0] + [v for s, v in exc_star.items() if s not in two]):
        raise SystemExit('the two named objects do not hold the most exceedances')
    rest = [(r, ab) for r, ab in zip(win, above) if r['star'] not in two]
    rest_ps = [float(r['p_trig_ctrl']) for r, _ab in rest if r['p_trig_ctrl'] != '']
    rest_exc = sum(1 for _r, ab in rest if ab)
    exp_rest = sum(rest_ps)

    # ------------------------------------- each of the two, on deposited rates
    cfs = {}
    for r in read(os.path.join(st, 'control_field_statistics.csv')):
        if r['p_trig_ctrl']:
            cfs[(r['eb'], round(float(r['nu_lo_GHz']), 4),
                 round(float(r['nu_hi_GHz']), 4))] = float(r['p_trig_ctrl'])
    ctrl = collections.OrderedDict()
    exc_obj = collections.Counter()
    missing = 0
    for r, ab in zip(win, above):
        k = (r['eb'], round(float(r['nu_lo_GHz']), 4), round(float(r['nu_hi_GHz']), 4))
        if k in cfs:
            ctrl.setdefault(r['object'], []).append(cfs[k])
        elif r['search_class'] == 'A':
            missing += 1
        if ab:
            exc_obj[r['object']] += 1
    if missing:
        raise SystemExit('%d Class A covering windows have no deposited control rate' % missing)
    e_hd, e_jx = sum(ctrl.get(hd, [])), sum(ctrl.get(jx, []))
    p_hd = pb_tail(ctrl.get(hd, []), exc_obj[hd])
    p_jx = pb_tail(ctrl.get(jx, []), exc_obj[jx])

    # ------------------------------------------------------ the look-elsewhere
    calls = collections.OrderedDict()
    for r in sorted(read(os.path.join(st, 'look_elsewhere_groups.csv')),
                    key=lambda r: (int(r['call']), int(r['group']), int(r['member']))):
        c = calls.setdefault(int(r['call']), dict(purpose=r['purpose'], groups=collections.OrderedDict()))
        c['groups'].setdefault((int(r['group']), r['object']), []).append(float(r['p']))
    rng = np.random.default_rng(seed)
    look = {}
    for n, c in calls.items():
        groups = list(c['groups'].values())
        if c['purpose'] == 'control rates':
            mine = list(ctrl.values())
            if groups != mine or [o for (_g, o) in c['groups']] != list(ctrl):
                raise SystemExit('the deposited control-rate groups are not the ones the '
                                 'windows and control_field_statistics.csv form')
            p_obs = p_jx
        else:
            p_obs = float(par['p_obs_call_%d' % n])
        look[c['purpose']] = (look_elsewhere(rng, n_sim, groups, p_obs), len(groups))
    p_look, n_look = look['control rates']

    R = [
        ('', 'distinct covering windows', n_win, '%d'),
        ('', 'windows at or above the trigger', n_exc, '%d'),
        ('', 'expected from the control positions', exp_all, '%.1f'),
        ('', 'P(count >= observed)', p_all, '%.2f'),
        ('', 'the two objects\' share of the expectation', exp_all - exp_rest, '%.1f'),
        ('', 'windows toward the two objects at or above the trigger',
         n_exc - rest_exc, '%d'),
        ('', 'other windows', len(rest), '%d'),
        ('', 'other windows at or above the trigger', rest_exc, '%d'),
        ('', 'other windows expected', exp_rest, '%.1f'),
        ('', 'other windows P(count >= observed)', pb_tail(rest_ps, rest_exc), '%.2f'),
        (hd, 'at or above the trigger', exc_obj[hd], '%d'),
        (hd, 'expected from deposited control rates', e_hd, '%.1f'),
        (hd, 'P(count >= observed)', p_hd, '%.2f'),
        (jx, 'at or above the trigger', exc_obj[jx], '%d'),
        (jx, 'expected from deposited control rates', e_jx, '%.1f'),
        (jx, 'P(count >= observed)', p_jx, '%.3f'),
        ('both', 'the two objects\' expectation on deposited control rates', e_hd + e_jx, '%.1f'),
        ('both', 'objects in the look-elsewhere simulation', n_look, '%d'),
        ('both', 'look-elsewhere chance (per cent)', 100.0 * p_look, '%.0f'),
    ]
    rows = []
    print('\nthe widened-window recurrence comparison (seed %d, %d simulations)' % (seed, n_sim))
    for obj, name, v, fmt in R:
        shown = fmt % (round(v) if fmt == '%.0f' else v)
        print('  %-26s %-56s %s' % (obj or '-', name, shown))
        rows.append(dict(reading=obj, quantity=name, value=v, printed=shown))
    out = dict(results=rows, look_elsewhere={k: v[0] for k, v in look.items()})
    if a.json:
        with open(a.json, 'w') as fh:
            json.dump(out, fh, indent=1)
    return 0


if __name__ == '__main__':
    sys.exit(main())
