#!/usr/bin/env python3
"""Round 86 (v4.04, referee 2 item 8): the rank-first arithmetic of
Appendix J.3, recomputed -- and it does not say what the appendix said.

THE REFEREE FOUND A TYPOGRAPHICAL SYMPTOM OF A REAL ERROR.  The appendix read
"\\SbrN observed ... line emission accounts for \\SbrAstro of the \\SbrN,
which leaves \\SbrResid against \\ExpFlags expected -- far too many for
chance".  With the shipped values that is 14 observed, 3 astrophysical,
2 remaining, against 3.23 expected: the subtraction is wrong (14 - 3 = 11),
and the conclusion drawn from it is wrong in the opposite direction, because
2 is *fewer* than 3.23, not "far too many".  \\SbrAstro and \\SbrResid were
hand-typed literals in `make_numbers.py` dating from an extraction in which
the rank-first set was smaller.

RECOMPUTED FROM THE RELEASED CATALOGUE, THE CONCLUSION CHANGES.  Of the
rank-first windows, the great majority carry an identified line attribution
at the stellar position -- circumstellar CO in the beta Pictoris disc and
foreground CO toward HD 48370.  Removing them leaves a residual that is
entirely consistent with the exchangeable expectation.  So the rank-first
excess is explained by astrophysics, and **it is not, by itself, evidence
that the rank is non-exchangeable**.

That does not rescue the rank.  The evidence for non-exchangeability is
independent of the crossings and is out of sample: the stellar rank
distribution is displaced on windows the pipeline had never seen
(Appendix C).  The appendix now says so, and cites the evidence that
actually carries the claim rather than the one that does not.

★ The referee also suspected a copy error because the clustered and Poisson
tail probabilities are identical.  They are not a copy error: for this mean
the block-clustered convolution and the Poisson tail agree to three
significant figures, and `v352_calc.py` asserts that agreement.  The text now
states it rather than leaving it looking like a mistake.

-> survey_numbers_round86.tex
"""
import csv
import json
import math
import os

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, 'survey_numbers_round86.tex')
ROWS = list(csv.DictReader(open(os.path.join(HERE,
                                             'per_target_results_v3.99.csv'))))
K = json.load(open(os.path.join(HERE, 'catalogue_constants.json')))

M = {}


def m(k, v):
    M[k] = v


def fv(r, k):
    return float(r[k]) if r[k] not in ('', None) else None


NCTRL = int(K.get('n_ctrl', 512))
TRIG = 5.0

# Rank-first: the star's statistic exceeds EVERY control in its own window.
# This is the quantity Appendix J.3 counts, and it is NOT the stage-1 count,
# because a window can rank first without reaching the trigger.
first = [r for r in ROWS if r['n_ctrl_ge_star'] == '0']
trig = [r for r in first if (fv(r, 'star_snr') or 0) >= TRIG]
attr = [r for r in trig if 'CO' in r['disposition']]
resid = len(first) - len(attr)

m('FaNFirst', '%d' % len(first))
m('FaNFirstTrig', '%d' % len(trig))
m('FaNFirstBelow', '%d' % (len(first) - len(trig)))
m('FaNFirstAttr', '%d' % len(attr))
m('FaNFirstResid', '%d' % resid)

# The exchangeable expectation for rank-first windows: one designated
# position of NCTRL+1 ranks first with probability 1/(NCTRL+1), whatever the
# noise distribution.  Read the window count from the catalogue constants so
# the denominator cannot drift.
mu = K['n_windows'] / float(NCTRL + 1)
m('FaExpFirst', '%.2f' % mu)
# The paper's existing \ExpFlags must be that same quantity or the comparison
# is between two different things.  Read it back and assert, rather than
# publishing a second number that looks like it.
_ef = None
for line in open(os.path.join(HERE, 'survey_numbers.tex')):
    if '\\newcommand{\\ExpFlags}' in line:
        _ef = float(line.split('{')[-1].split('}')[0].strip())
assert _ef is not None, 'ExpFlags not found in survey_numbers.tex'
assert abs(_ef - mu) < 0.02, (_ef, mu)


def pois_tail(k, mu):
    t, s = math.exp(-mu), 0.0
    for i in range(0, 2000):
        if i >= k:
            s += t
        t *= mu / (i + 1)
    return s


m('FaPFirst', '%.1e' % pois_tail(len(first), mu))
m('FaPResid', '%.2f' % pois_tail(resid, mu))

# ★ The whole point of the rewrite: the residual must be CONSISTENT with
# chance for the new sentence to be true, and the raw count must NOT be.
# Both directions are asserted, so the paragraph cannot outlive its
# arithmetic in either direction.
assert pois_tail(len(first), mu) < 1e-3, pois_tail(len(first), mu)
assert pois_tail(resid, mu) > 0.05, pois_tail(resid, mu)
# ... and the subtraction that the appendix got wrong is now forced to close.
assert resid == len(first) - len(attr) and 0 <= resid <= len(first), resid

# Where the evidence for non-exchangeability actually comes from: the
# out-of-sample stellar rank displacement.  Name it by reading the macros
# that carry it, so the cross-reference cannot go stale.
_v = {}
for fn in os.listdir(HERE):
    if fn.startswith('survey_numbers') and fn.endswith('.tex'):
        for line in open(os.path.join(HERE, fn)):
            if line.startswith('\\newcommand{\\'):
                k = line.split('{\\', 1)[1].split('}', 1)[0]
                _v[k] = line.split('}{', 1)[1].rsplit('}', 1)[0]
assert 'HoRankMed' in _v, 'the out-of-sample rank median macro has moved'
m('FaOutRankMed', _v['HoRankMed'])

with open(OUT, 'w') as fh:
    fh.write('%% GENERATED by fa_v404.py -- do not hand-edit.\n')
    for k in sorted(M):
        fh.write('\\newcommand{\\%s}{%s}\n' % (k, M[k]))

print('fa_v404: %d rank-first windows (%d reaching the trigger) against '
      '%.2f expected, P(>=%d) = %.1e'
      % (len(first), len(trig), mu, len(first), pois_tail(len(first), mu)))
print('  %d carry an identified line attribution; residual %d against %.2f '
      'expected, P(>=%d) = %.2f -- CONSISTENT with chance'
      % (len(attr), resid, mu, resid, pois_tail(resid, mu)))
print('  -> %s (%d macros)' % (os.path.basename(OUT), len(M)))
