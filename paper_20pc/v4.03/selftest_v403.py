#!/usr/bin/env python3
"""Demonstrate that every check in `ledger_v403.py` can actually fail.

`ledger_v401.py` shipped a line-attribution test written as `if not r['line']`.
Every one of the 56 crossings has a nearest catalogued transition -- one of
them 20,255 km/s away -- so the test was false for all of them and the count
of unattributed localised crossings was zero BY CONSTRUCTION.  It passed every
build.  A check that cannot fail is not a check, and the only way to know the
difference is to make it fail on purpose.

This driver runs the generator once per perturbation, each of which corrupts
an INPUT (never a threshold), into a throwaway output directory, and requires
that the named check -- and no other -- be the one that fires.

    python3 selftest_v403.py           # run them all
    python3 selftest_v403.py NAME ...  # run some

Exit status is non-zero if any perturbation passes silently, or fires the
wrong check.
"""
import os
import re
import subprocess
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
GEN = os.path.join(HERE, 'ledger_v403.py')

# perturbation -> the check it must make fail
CASES = [
    ('drop-crossing', 'n-crossings'),
    ('orphan-fit', 'no-orphan-fit'),
    ('attr-by-presence', 'mask-not-presence'),
    ('mask-all-inside', 'mask-not-presence'),
    ('mask-all-outside', 'mask-discriminates'),
    ('mask-null-far', 'mask-far-example'),
    ('untracked-untested', 'untested-accounted'),
    ('strip-bound', 'provisional-rows-bounded'),
    ('strip-first', 'adopted-verdict-present'),
    ('criterion-mismatch', 'criterion-unmoved'),
    ('fa-inflate', 'false-alarm-ceiling'),
    ('kill-localisations', 'localisations-not-false-alarms'),
    ('flip-small-D', 'epoch-change-is-displacement'),
    ('drop-mask-macro', 'mask-occupancy-available'),
    ('attr-thin', 'attribution-informative'),
    ('recurrence-name', 'recurrence-join-names-agree'),
    ('recurrence-unjoined', 'recurrence-fully-joined'),
    ('candidate-word', 'no-candidate-word'),
    ('etacrv-screened', 'etacrv-facts'),
    ('recurrence-drop', 'recurrence-gap-known'),
    ('scorer-mismatch', 'agrees-with-scorer'),
]

# Checks with no perturbation here, and why.  They are structural invariants
# of the join: no INPUT can violate them without the code changing too, so
# there is nothing to drive.  They are listed so the gap is visible rather
# than implicit.
STRUCTURAL = {
    'partition-fitted': 'every row is fitted or untested by construction',
    'untested-carry-no-verdict': 'the untested branch assigns None',
    'criterion-is-conjunction': 'both sides come from verdict()',
    'clause3-never-rejects-alone': 'a property of the data, not of the join; '
                                   'it fires if a future refit produces one',
    'vis-status-vocabulary': 'the three states are assigned in one place',
    'etacrv-present': 'fires if the block leaves the catalogue',
}


def run(perturb, outdir):
    env = dict(os.environ, LEDGER_V403_PERTURB=perturb)
    return subprocess.run([sys.executable, GEN, '--outdir', outdir],
                          env=env, capture_output=True, text=True)


def main():
    want = set(sys.argv[1:])
    cases = [c for c in CASES if not want or c[0] in want]
    with tempfile.TemporaryDirectory() as td:
        base = run('', os.path.join(td, 'base'))
        if base.returncode != 0:
            print('UNPERTURBED RUN FAILED:\n' + base.stderr)
            return 1
        names = set(re.findall(r'"name": "([^"]+)"',
                               open(os.path.join(td, 'base',
                                                 'ledger_v403.json')).read()))
        bad = 0
        for perturb, expect in cases:
            r = run(perturb, os.path.join(td, perturb))
            # ★ match the raised MESSAGE, not the source line the traceback
            # echoes -- the `raise` statement itself contains the literal
            # text "CHECK FAILED [%s]", so a loose regex reported every
            # perturbation as firing a check named "%s" and would have passed
            # a driver that never checked anything.
            m = re.search(r'^AssertionError: CHECK FAILED \[([^\]]+)\]',
                          r.stderr, re.M)
            if r.returncode == 0:
                print('SILENT  %-20s -> expected [%s], generator succeeded'
                      % (perturb, expect))
                bad += 1
            elif not m:
                print('CRASHED %-20s -> %s' % (perturb,
                                               r.stderr.strip().splitlines()[-1]))
                bad += 1
            elif m.group(1) != expect:
                print('WRONG   %-20s -> fired [%s], expected [%s]'
                      % (perturb, m.group(1), expect))
                bad += 1
            else:
                print('ok      %-20s -> [%s]' % (perturb, expect))
        covered = {e for _, e in CASES}
        missing = names - covered - set(STRUCTURAL)
        for n in sorted(missing):
            print('UNDEMONSTRATED check with no perturbation: %s' % n)
            bad += 1
        print('\n%d checks in the generator; %d demonstrated failing, '
              '%d structural, %d undemonstrated'
              % (len(names), len(covered & names), len(set(STRUCTURAL) & names),
                 len(missing)))
        return 1 if bad else 0


if __name__ == '__main__':
    sys.exit(main())
