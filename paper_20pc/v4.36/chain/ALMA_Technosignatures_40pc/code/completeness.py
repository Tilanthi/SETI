#!/usr/bin/env python3
"""Rebuild the Class A completeness factor from the deposited injection trials.

    python3 completeness.py [--data DIR] [--json FILE]

Reads sensitivity/injection_trials.csv and
sensitivity/completeness_parameters.csv and nothing else, and prints:

  the class factor        the amplitude, in units of each window's own trigger
                          power, at which nine pooled trials in ten reach the
                          trigger -- the factor EIRP_90 = factor x P_trig uses
  its bootstrap interval  the same point over resamplings of the injected
                          windows with replacement (the window is the unit of
                          the sample), at the deposited quantiles
  the calibration interval  that sampling error combined in quadrature with
                          the instrumental term, as fractions of the factor
  the per-window points   each injected window's own ninety-per-cent point,
                          their full range and their central spread, as
                          multiples of the class factor

A recovery curve is the fraction of trials reaching the trigger at each rung of
the amplitude ladder; its ninety-per-cent point is where it first reaches 0.9,
linearly interpolated between rungs.  The positive-control rung is a diagnostic
and is excluded.  The bootstrap draws window indices with Python's own
generator (random.Random) from the deposited seed, so the interval is
reproduced exactly.  Needs Python 3 and numpy.
"""
import argparse
import csv
import json
import math
import os
import random
import sys

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
AP = argparse.ArgumentParser(description=__doc__.split('\n')[0])
AP.add_argument('--data', default=os.path.join(HERE, '..'))
AP.add_argument('--json', default=None)


def read(path):
    with open(path, newline='') as fh:
        return list(csv.DictReader(fh))


def cross(amps, fr, want):
    """Where a recovery curve first reaches `want`, linearly interpolated."""
    prev = None
    for a, f in zip(amps, fr):
        if f is None:
            continue
        if f >= want:
            if prev is None:
                return a
            pa, pf = prev
            return pa + (want - pf) * (a - pa) / (f - pf) if f > pf else a
        prev = (a, f)
    return None


def main():
    a = AP.parse_args()
    sd = os.path.join(a.data, 'sensitivity')
    par = {r['parameter']: r['value']
           for r in read(os.path.join(sd, 'completeness_parameters.csv'))}
    want = float(par['completeness_level'])
    posctrl = float(par['positive_control_amp'])
    seed, nboot = int(par['bootstrap_seed']), int(par['bootstrap_n'])
    qlo, qhi = float(par['bootstrap_q_lo']), float(par['bootstrap_q_hi'])
    plo, phi = float(par['spread_pct_lo']), float(par['spread_pct_hi'])
    inst = float(par['instrumental_fraction'])
    rows = read(os.path.join(sd, 'injection_trials.csv'))
    by = {}
    order = []
    for r in rows:
        k = r['window_tag']
        if k not in by:
            by[k] = []
            order.append(k)
        by[k].append((float(r['amp_over_trigger']), r['reached_trigger'] == '1'))
    tags = sorted(by)
    amps = sorted({x for k in tags for x, _ in by[k] if x != posctrl})

    def curve(sel):
        out = []
        for amp in amps:
            tt = [hit for k in sel for x, hit in by[k] if x == amp]
            out.append(sum(tt) / len(tt) if tt else None)
        return out

    p90 = cross(amps, curve(tags), want)
    per = {k: cross(amps, curve([k]), want) for k in tags}
    n = len(tags)
    rng = random.Random(seed)
    boot = []
    for _ in range(nboot):
        s = [tags[rng.randrange(n)] for _ in range(n)]
        v = cross(amps, curve(s), want)
        if v is not None:
            boot.append(v)
    boot.sort()
    lo, hi = boot[int(qlo * len(boot))], boot[int(qhi * len(boot))]
    comb_lo = math.hypot(1.0 - lo / p90, inst)
    comb_hi = math.hypot(hi / p90 - 1.0, inst)
    ind = sorted(per.values())
    R = [
        ('injected windows', n, '%d'),
        ('trials', len(rows), '%d'),
        ('class factor (x P_trig)', p90, '%.2f'),
        ('bootstrap interval low', lo, '%.2f'),
        ('bootstrap interval high', hi, '%.2f'),
        ('calibration interval low (x factor)', 1.0 - comb_lo, '%.2f'),
        ('calibration interval high (x factor)', 1.0 + comb_hi, '%.2f'),
        ('per-window point, lowest (x factor)', ind[0] / p90, '%.2f'),
        ('per-window point, highest (x factor)', ind[-1] / p90, '%.2f'),
        ('per-window spread low (x factor)', float(np.percentile(ind, plo)) / p90, '%.3f'),
        ('per-window spread high (x factor)', float(np.percentile(ind, phi)) / p90, '%.3f'),
        ('windows within a tenth of the factor',
         sum(1 for v in ind if 0.9 <= v / p90 <= 1.1), '%d'),
    ]
    print('completeness from %d trials in %d windows' % (len(rows), n))
    out = []
    for name, v, fmt in R:
        print('  %-44s %s' % (name, fmt % v))
        out.append(dict(quantity=name, value=v, printed=fmt % v))
    if a.json:
        with open(a.json, 'w') as fh:
            json.dump(dict(results=out, per_window=per), fh, indent=1)
    return 0


if __name__ == '__main__':
    sys.exit(main())
