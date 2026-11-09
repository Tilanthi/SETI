#!/usr/bin/env python3
"""Rebuild the channel-response ratios and the completeness factor of every class and averaging mode.

    python3 response_ratio.py [--data DIR] [--json FILE]

Reads sensitivity/response_injection_trials.csv, sensitivity/response_parameters.csv,
sensitivity/injection_trials.csv and sensitivity/completeness_parameters.csv, and prints:

  the response ratio      for each search class and online-averaging mode N, the
                          amplitude at which nine pooled trials in ten reach the
                          trigger with the window's own channel response, divided
                          by the same point with the deposited 0.25/0.5/0.25
                          profile, on identical carriers in the same windows
  the factor              the class level (Class A: the pooled ninety-per-cent
                          point of injection_trials.csv, as completeness.py forms
                          it; Class B: the deposited parameter) times that ratio,
                          the multiple of each window's trigger power that sets
                          its EIRP_90

A recovery curve is the fraction of trials reaching the trigger at each rung of
the amplitude ladder; its ninety-per-cent point is where it first reaches 0.9,
linearly interpolated between rungs.  The positive-control rung is excluded.
Needs Python 3 only.
"""
import argparse
import csv
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
AP = argparse.ArgumentParser(description=__doc__.split('\n')[0])
AP.add_argument('--data', default=os.path.join(HERE, '..'))
AP.add_argument('--json', default=None)
WORD = {1: 'one', 2: 'two', 4: 'four'}


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


def p90(trials, amps, want):
    fr = []
    for amp in amps:
        tt = [hit for x, hit in trials if x == amp]
        fr.append(sum(tt) / len(tt) if tt else None)
    return cross(amps, fr, want)


def main():
    a = AP.parse_args()
    sd = os.path.join(a.data, 'sensitivity')
    par = {r['parameter']: r['value'] for r in read(os.path.join(sd, 'response_parameters.csv'))}
    want = float(par['completeness_level'])
    posctrl = float(par['positive_control_amp'])
    level_b = float(par['class_level_B'])
    amps = sorted(float(x) for x in par['amplitude_ladder'].split(';'))
    # the Class A level, exactly as completeness.py forms it
    cpar = {r['parameter']: r['value'] for r in read(os.path.join(sd, 'completeness_parameters.csv'))}
    cposctrl = float(cpar['positive_control_amp'])
    cw = {}
    for r in read(os.path.join(sd, 'injection_trials.csv')):
        cw.setdefault(r['window_tag'], []).append((float(r['amp_over_trigger']), r['reached_trigger'] == '1'))
    camps = sorted({x for k in cw for x, _ in cw[k] if x != cposctrl})
    level_a = p90([t for k in sorted(cw) for t in cw[k]], camps, float(cpar['completeness_level']))
    # the paired campaign, pooled per class and averaging mode
    pool = {}
    for r in read(os.path.join(sd, 'response_injection_trials.csv')):
        amp = float(r['amp_over_trigger'])
        if amp == posctrl:
            continue
        k = (r['search_class'], int(r['n_chan_avg']))
        pool.setdefault(k, {}).setdefault(r['model'], {}).setdefault(r['window_tag'], []).append(
            (amp, r['reached_trigger'] == '1'))
    R, out = [], []
    for (cls, n) in sorted(pool):
        m = pool[(cls, n)]
        tags = sorted(m['deposited_profile'])
        h = p90([t for g in tags for t in m['deposited_profile'][g]], amps, want)
        e = p90([t for g in tags for t in m['own_response_paired'][g]], amps, want)
        rho = e / h
        lvl = level_a if cls == 'A' else level_b
        R.append(('response ratio, class %s, N = %d' % (cls, n), rho, '%.2f', len(tags)))
        R.append(('factor, class %s, N = %d (x P_trig)' % (cls, n), lvl * rho, '%.2f', len(tags)))
    print('channel response from %d modes; class levels A %.4f, B %.4f' % (len(pool), level_a, level_b))
    for name, v, fmt, nw in R:
        print('  %-44s %s   (%d windows)' % (name, fmt % v, nw))
        out.append(dict(quantity=name, value=v, printed=fmt % v, n_windows=nw))
    if a.json:
        with open(a.json, 'w') as fh:
            json.dump(dict(results=out, class_level_A=level_a, class_level_B=level_b), fh, indent=1)
    return 0


if __name__ == '__main__':
    sys.exit(main())
