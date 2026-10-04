#!/usr/bin/env python3
r"""Self-test for numbers.py: every assertion driven in both directions.

Unperturbed, all of them must stay silent.  Under --drive N exactly one must
fire, and it must be the one that drive was written to break -- an assertion
that fires under somebody else's perturbation is not testing what its name
says it is.  Nothing here writes a path the production run writes: the driven
runs put their output in a temporary directory and the suffix follows the
flag, so --drive 0 is as barred from a production path as --drive 7.
"""
import os
import re
import shutil
import subprocess
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
GEN = os.path.join(HERE, 'numbers_v410.py')
# drive -> the assertions that must fire, and ONLY those.  Three
# perturbations legitimately cascade: breaking the multiplier must also trip
# the checks that the headline powers and the system counts reproduce the
# frozen result, and breaking one term of the crossing delta must also trip
# the closure and the reproduction.  The cascade is DECLARED rather than
# allowed, so a drive that starts tripping something new still fails here.
EXPECT = {0: None, 1: 'A3', 2: 'B1', 3: ('C1', 'C9', 'C10'), 4: 'C3',
          5: 'D3', 6: 'F1', 7: 'E1', 8: 'A6', 9: 'E2', 10: 'D4', 11: 'G4',
          12: 'H1', 13: 'G5', 15: 'C6', 16: 'B2',
          17: ('B5', 'B6', 'B7'), 18: ('B6', 'B7'), 19: 'D5'}


def run(cat, picks, out, drive):
    cmd = [sys.executable, GEN, '--cat', cat, '--out', out]
    for p in picks:
        cmd += ['--pick', p]
    if drive is not None:
        cmd += ['--drive', str(drive)]
    p = subprocess.run(cmd, capture_output=True, text=True)
    return p.returncode, p.stdout + p.stderr


def main():
    cat = sys.argv[1]
    picks = sys.argv[2:]
    out = tempfile.mkdtemp(prefix='numbers_selftest_')
    npass = nfail = 0
    try:
        prod_out = tempfile.mkdtemp(prefix='numbers_selftest_prod_')
        rc, o = run(cat, picks, prod_out, None)
        ok = (rc == 0 and 'FIRED' not in o)
        print('  %-5s production run: %d assertions fired'
              % ('PASS' if ok else 'FAIL',
                 len(re.findall(r'ASSERTION FIRED', o))))
        if not ok:
            print(o[-900:])
        npass += ok
        nfail += not ok
        for d in sorted(EXPECT):
            rc, o = run(cat, picks, out, d)
            fired = re.findall(r'ASSERTION FIRED\s+(\w+)', o)
            want = EXPECT[d]
            if want is None:
                ok = (rc == 0 and not fired)
                what = 'no perturbation, nothing fires'
            else:
                exp = list(want) if isinstance(want, tuple) else [want]
                ok = (rc == 1 and sorted(fired) == sorted(exp))
                what = ('%s fires, and only %s'
                        % (','.join(exp), 'it' if len(exp) == 1
                           else 'those'))
            print('  %-5s drive %d  %-32s %s'
                  % ('PASS' if ok else 'FAIL', d, what,
                     '' if ok else 'got %s' % fired))
            npass += ok
            nfail += not ok
        prod = [f for f in os.listdir(out) if '_drive' not in f]
        ok = not prod
        print('  %-5s no driven run wrote a production path %s'
              % ('PASS' if ok else 'FAIL', sorted(prod)))
        shutil.rmtree(prod_out, ignore_errors=True)
        npass += ok
        nfail += not ok
        print('numbers_selftest: %d/%d' % (npass, npass + nfail))
        return 1 if nfail else 0
    finally:
        shutil.rmtree(out, ignore_errors=True)


if __name__ == '__main__':
    sys.exit(main())
