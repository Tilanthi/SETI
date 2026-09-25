#!/usr/bin/env python3
"""Referee 1, point 3: the injection campaign resolved by drift rate.

The campaign already injects only DRIFTING carriers -- not a single trial is
at zero drift -- but the paper reported it as one pooled recovery curve, so a
reader cannot tell whether the quoted completeness holds at the top of the
drift grid as well as near its centre.  This generator takes the frozen trial
record apart along every stratification axis the campaign varied
(observing frequency, channel width, integration count, array, drift rate)
and emits the recovery curve for each level, plus the carrier sub-channel
phase from the companion response campaign.

Nothing is simulated here; the trials are the frozen 2026 campaign.
"""
import csv, os, collections
import numpy as np
from inject_curve import curve, pX, AMPS

HERE = os.path.dirname(os.path.abspath(__file__))
R = list(csv.DictReader(open(os.path.join(HERE, 'stratified_inject_trials_v3.58.csv'))))
H = list(csv.DictReader(open(os.path.join(HERE, 'hanning_response_trials_v3.58.csv'))))
OUT = []
def M(n, v): OUT.append(r'\newcommand{\%s}{%s}' % (n, v))

# ---------------------------------------------------- the drift dimension
# The grid is symmetric about zero and its half-width is the ceiling, so the
# largest rate the campaign injected in a window IS that window's ceiling to
# within one grid step.  Express every trial as a fraction of it.
CEIL = {}
for r in R:
    w = r['window']
    CEIL[w] = max(CEIL.get(w, 0.0), abs(float(r['inj_drift_Hz_s'])))
for r in R:
    r['_f'] = abs(float(r['inj_drift_Hz_s'])) / CEIL[r['window']]
    r['_a'] = float(r['amp_sigma'])

NZERO = sum(1 for r in R if float(r['inj_drift_Hz_s']) == 0.0)
assert NZERO == 0, 'a zero-drift trial has appeared in the campaign'
M('DriftStratTrials', '%d' % len(R))
M('DriftStratZero', '%d' % NZERO)
M('DriftStratRateLo', '%.0f' % min(abs(float(r['inj_drift_Hz_s'])) for r in R))
M('DriftStratRateHi', '%.0f' % max(abs(float(r['inj_drift_Hz_s'])) for r in R))

BINS = [('low', 0.0, 1 / 3.), ('mid', 1 / 3., 2 / 3.), ('high', 2 / 3., 1.001)]
NAME = {'low': 'Low', 'mid': 'Mid', 'high': 'High'}
ROWS = []
for key, lo, hi in BINS:
    sel = [r for r in R if lo <= r['_f'] < hi]
    c = curve(sel)
    p50, p90 = pX(c, 0.5), pX(c, 0.9)
    M('DriftStrat%sN' % NAME[key], '%d' % len(sel))
    M('DriftStrat%sPFifty' % NAME[key], '%.1f' % p50)
    M('DriftStrat%sPNinety' % NAME[key], '%.1f' % p90)
    ROWS.append((key, lo, hi, len(sel), p50, p90))

_p90s = [r[5] for r in ROWS]
M('DriftStratSpread', '%.0f' % (100 * (max(_p90s) / min(_p90s) - 1)))

# Is the residual drift dependence real, or amplitude sampling?  Compare
# recovery at a fixed, well-sampled amplitude.
FIX = 6.0
for key, lo, hi in BINS:
    sel = [r for r in R if lo <= r['_f'] < hi and r['_a'] == FIX]
    M('DriftStrat%sRecSix' % NAME[key],
      '%.0f' % (100 * np.mean([s['detected'] == 'True' for s in sel])) if sel else '--')
M('DriftStratFixAmp', '%.0f' % FIX)

# Does the search recover the RATE as well as the frequency?  The campaign
# records the matched drift trial, so this is a measurement, not an argument.
_d = [r for r in R if r['detected'] == 'True' and r['_a'] >= FIX]
M('DriftStratMatchPct',
  '%.0f' % (100 * np.mean([r['drift_matched'] == 'True' for r in _d])))
_err = np.array([abs(float(r['rec_drift_Hz_s']) - float(r['inj_drift_Hz_s']))
                 / (float(r['chanw_Hz']) / float(r['span_s'])) for r in _d])
M('DriftStratErrMed', '%.2f' % np.median(_err))
M('DriftStratErrNine', '%.1f' % np.percentile(_err, 90))

# --------------------------------------------- the other stratification axes
def axis(rows, keyfn, label, fmt='%s'):
    lv = collections.defaultdict(list)
    for r in rows:
        lv[keyfn(r)].append(r)
    out = []
    for k in sorted(lv):
        c = curve(lv[k])
        out.append((fmt % k, len(lv[k]), pX(c, 0.5), pX(c, 0.9)))
    return label, out


AXES = [
    axis(R, lambda r: int(r['band']), 'ALMA band', 'B%d'),
    axis(R, lambda r: float(r['chanw_Hz']) / 1e3, 'Channel width (kHz)', '%.1f'),
    axis(R, lambda r: '12\\,m' if r['array'] == '12m' else 'ACA', 'Array'),
    axis(R, lambda r: ('$<$1/3', '1/3--2/3', '$>$2/3')[
        0 if r['_f'] < 1 / 3. else 1 if r['_f'] < 2 / 3. else 2],
         'Drift rate / ceiling'),
    axis(R, lambda r: ('$<$150', '150--350', '$>$350')[
        0 if int(r['n_int']) < 150 else 1 if int(r['n_int']) <= 350 else 2],
         'Integrations'),
]
# carrier sub-channel phase, from the companion response campaign
for h in H:
    h['_a'] = None
PH = collections.defaultdict(list)
for h in H:
    PH[float(h['phi'])].append(float(h['factor']))
AXES.append(('Sub-channel phase',
             [('%.3f' % k, len(PH[k]), float(np.mean(PH[k])), float('nan'))
              for k in sorted(PH)]))
M('PhaseStratTrials', '%d' % len(H))
M('PhaseStratLevels', '%d' % len(PH))
M('PhaseStratWorst', '%.2f' % min(np.mean(PH[k]) for k in PH))
M('PhaseStratBest', '%.2f' % max(np.mean(PH[k]) for k in PH))

# ----------------------------------------------------------------- outputs
T = [r'\begin{tabular}{llrrr}', r'\hline',
     r'Axis & Level & Trials & $P_{50}$ & $P_{90}$ \\',
     r' & & & ($\sigma$) & ($\sigma$) \\', r'\hline']
for label, rows in AXES:
    for i, (lv, n, p50, p90) in enumerate(rows):
        T.append('%s & %s & %d & %s & %s \\\\'
                 % (label if i == 0 else '', lv, n,
                    '%.1f' % p50 if p50 == p50 else '--',
                    '%.1f' % p90 if p90 == p90 else '--'))
    T.append(r'\hline')
T.append(r'\end{tabular}')
open(os.path.join(HERE, 'tab_driftstrata_v385.tex'), 'w').write('\n'.join(T) + '\n')

open(os.path.join(HERE, 'survey_numbers_round36.tex'), 'w').write(
    '%% GENERATED by drift_strata_v385.py -- do not hand-edit.\n' + '\n'.join(OUT) + '\n')

print('trials %d, zero-drift trials %d, rates %.0f-%.0f Hz/s'
      % (len(R), NZERO, min(abs(float(r['inj_drift_Hz_s'])) for r in R),
         max(abs(float(r['inj_drift_Hz_s'])) for r in R)))
for key, lo, hi, n, p50, p90 in ROWS:
    print('  drift %-5s (%.2f-%.2f ceiling) n=%4d  P50 %.2f  P90 %.2f'
          % (key, lo, hi, n, p50, p90))
print('  P90 spread across drift terciles: %.0f per cent'
      % (100 * (max(_p90s) / min(_p90s) - 1)))
print('  rate recovered to within %.2f grid steps (median), %.1f at 90 per cent; '
      'matched trial %d per cent'
      % (np.median(_err), np.percentile(_err, 90),
         round(100 * np.mean([r['drift_matched'] == 'True' for r in _d]))))
print('  sub-channel phase: %d trials, %d levels, response %.2f-%.2f'
      % (len(H), len(PH), min(np.mean(PH[k]) for k in PH),
         max(np.mean(PH[k]) for k in PH)))
print('table -> tab_driftstrata_v385.tex; macros -> survey_numbers_round36.tex (%d)'
      % len(OUT))
