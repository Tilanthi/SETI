#!/usr/bin/env python3
"""Rebuild the article's statistical and calibration summaries and compare.

    python3 reproduce.py [--data DIR] [--seed-offset K]

Runs chance_expectation.py, completeness.py, sensitivity_summary.py,
recurrence_expectation.py and response_ratio.py on the archive, then compares every rebuilt quantity with the value the article
prints, as listed in statistics/article_values.csv.  A quantity agrees when
the rebuilt value, written to the article's own number of digits, is the
article's value.  Exit status 0 when every listed quantity agrees, 1 otherwise.

--seed-offset K reruns chance_expectation.py with the deposited seed plus K,
so that the size of the Monte Carlo error can be seen;
the comparison is then reported but expected to differ in the last digit of a
few probabilities, never by more than about three of the Monte Carlo
standard errors printed beside them.

Needs Python 3, numpy and scipy, and nothing outside this archive.
"""
import argparse
import csv
import json
import os
import subprocess
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
AP = argparse.ArgumentParser(description=__doc__.split('\n')[0])
AP.add_argument('--data', default=os.path.join(HERE, '..'))
AP.add_argument('--seed-offset', type=int, default=0)
AP.add_argument('--keep', default=None, help='keep each program\'s JSON output in this directory')
PROGRAMS = ['chance_expectation.py', 'completeness.py', 'sensitivity_summary.py',
            'recurrence_expectation.py', 'response_ratio.py']


def main():
    a = AP.parse_args()
    data = os.path.abspath(a.data)
    got = {}
    with tempfile.TemporaryDirectory() as tmp:
        for prog in PROGRAMS:
            out = os.path.join(a.keep or tmp, prog + '.json')
            cmd = [sys.executable, '-I', '-B', os.path.join(HERE, prog), '--data', data,
                   '--json', out]
            if a.seed_offset and prog == 'chance_expectation.py':
                cmd += ['--seed', str(_seed(data) + a.seed_offset)]
            p = subprocess.run(cmd, capture_output=True, text=True)
            sys.stdout.write(p.stdout)
            if p.returncode:
                sys.stdout.write(p.stderr)
                print('FAILED: %s exited %d' % (prog, p.returncode))
                return 1
            with open(out) as fh:
                r = json.load(fh)
            if prog == 'chance_expectation.py':
                for reading, d in r.items():
                    if reading == 'two_readings':
                        got[(prog, 'both', 'smaller probability corrected for '
                             'the two readings')] = '%.2f' % d['corrected_p']
                        continue
                    for x in d['results']:
                        got[(prog, reading, x['quantity'])] = x['printed']
            else:
                for x in r['results']:
                    got[(prog, x.get('reading', ''), x['quantity'])] = x['printed']
    with open(os.path.join(data, 'statistics', 'article_values.csv'),
              newline='') as fh:
        want = list(csv.DictReader(fh))
    bad = 0
    print('\ncomparison with the values the article prints')
    for w in want:
        k = (w['program'], w['reading'], w['quantity'])
        g = got.get(k)
        ok = g == w['article_value']
        bad += not ok
        print('  %-4s %-22s %-13s %-52s article %-9s rebuilt %s'
              % ('ok' if ok else 'DIFF', w['program'], w['reading'] or '-',
                 w['quantity'], w['article_value'], g))
    print('\n%d of %d quantities agree with the article' % (len(want) - bad, len(want)))
    return 0 if bad == 0 else 1


def _seed(data):
    with open(os.path.join(data, 'statistics',
                           'chance_resampling_parameters.csv'), newline='') as fh:
        for r in csv.DictReader(fh):
            if r['parameter'] == 'seed':
                return int(r['value'])
    raise SystemExit('no seed in the parameters file')


if __name__ == '__main__':
    sys.exit(main())
