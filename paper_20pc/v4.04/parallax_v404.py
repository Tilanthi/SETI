#!/usr/bin/env python3
"""Round 84 (v4.04, decisions D6 and D7): the omitted annual parallax.

THE DEFECT.  The extraction phase-rotates the visibilities to the star's
BARYCENTRIC direction -- `apply_space_motion()` returns a barycentric
position -- while the visibilities themselves see the APPARENT one.  The
annual parallax is therefore omitted from the phase centre, and the
amplitude recovered at the assumed position is the normalised dirty beam
evaluated at (parallax displacement)/(synthesised beam).  It is
parameter-free, multiplicative and shape-preserving.

WHY IT IS STATED AND NOT APPLIED (D6.3).  The loss is below 1 per cent in
the median released window; a full re-extraction of the survey would be
~4 TB for a correction that changes no disposition.  It is therefore quoted
as a measured per-window systematic, in the same way as the <=13 per cent
tone-deposition bias at v4.01.

★ THE DIRECTION MATTERS AND IS THE POINT.  The injected tones of the
completeness campaign are deposited at the same assumed position the
estimator evaluates at, so the campaign is BLIND to this term.  The quoted
limits are therefore OPTIMISTIC by 1/(1-loss), window by window.  That is
the third instance in this project of *a validation must be sensitive to the
error it exists to catch*.

WHY THE HEADLINE BARELY MOVES.  A large loss needs a large parallax AND a
long baseline, and a long-baseline block is never a system's most sensitive
window, so the per-system median moves by well under a per cent while
individual windows move by tens of per cent.  Both are reported; quoting
only the first would hide the systematic and only the second would
exaggerate it.

D7, THE ABSOLUTE-SCALE CHECK.  The same term is what reconciles our
extractor with two independent published reductions of the same archival
blocks: agreement to 1-2 per cent on ACA (where the displacement is 0.04-0.05
of a beam) and an 18-19 per cent deficit on a 1.3 km 12 m configuration
(0.245 of a beam).  ★ The honest qualification, which an earlier note could
not make because its lower bound came from a 39.5 m ACA configuration: over
the 17 REAL 12 m configurations for which the dirty beam was measured the
prediction is 0.89 (0.86-0.93) against 0.81-0.82 observed, so the parallax
term accounts for about 60 per cent of the deficit and the residual bounds
any second systematic in the absolute scale at roughly the 10 per cent
level -- NOT at zero.

Input: `r8inputs/parallax_loss_v404.json`, the frozen product of the
measurement campaign (per-window displacement and dirty-beam loss for every
retained window that carries the astrometric keys; a 19-configuration beam
library; and the headline recomputed with and without the correction).

-> survey_numbers_round84.tex
"""
import json
import os

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, 'survey_numbers_round84.tex')
P = json.load(open(os.path.join(HERE, 'r8inputs', 'parallax_loss_v404.json')))

M = {}


def m(k, v):
    M[k] = v


# ------------------------------------------------- the per-window systematic
# Two beam models are carried.  `meas` is the measured dirty beam of the real
# configurations; `gauss` is the Gaussian rule.  The measured beam is the
# one quoted, because the true main lobe is NARROWER than 1.22 lambda/B_max
# and the Gaussian rule therefore understates the loss -- so using it would
# be the flattering choice.
R = P['rep']['meas']
G = P['rep']['gauss']
assert R['n'] == G['n'], (R['n'], G['n'])
m('PxNWin', '%d' % R['n'])
m('PxLossMedPct', '%.2f' % (100.0 * R['median']))
m('PxLossNinetyPct', '%.2f' % (100.0 * R['p90']))
m('PxLossNNPct', '%.1f' % (100.0 * R['p99']))
m('PxLossMaxPct', '%.1f' % (100.0 * R['max']))
m('PxNGtTen', '%d' % R['n_gt10'])
m('PxNGtFive', '%d' % R['n_gt5'])
m('PxNGtOne', '%d' % R['n_gt1'])
m('PxRetMedPct', '%.2f' % (100.0 * R['p50_ret']))
m('PxNBlocks', '%d' % len(P['blocks']))
# The Gaussian rule is the optimistic one; say by how much, so that the
# choice of beam model is visible rather than silent.
m('PxGaussMaxPct', '%.1f' % (100.0 * G['max']))
assert G['max'] > R['max'], (G['max'], R['max'])

# ------------------------------------------------------------- the headline
B, C = P['headline']['base'], P['headline']['meas']
m('PxSysMedBase', '%.2f' % (B['sys_med_sel'] / 1e15))
m('PxSysMedCorr', '%.2f' % (C['sys_med_sel'] / 1e15))
m('PxWinMedBase', '%.2f' % (B['win_med_sel'] / 1e15))
m('PxWinMedCorr', '%.2f' % (C['win_med_sel'] / 1e15))
m('PxSysMedShiftPct', '%.2f' % (100.0 * (C['sys_med_sel'] / B['sys_med_sel'] - 1)))
m('PxNSysBase', '%d' % B['n_sys_le_1e15'])
m('PxNSysCorr', '%d' % C['n_sys_le_1e15'])
# The claim in the prose is that the count of systems reaching 10^15 W does
# not move.  Assert it rather than assert nothing, so the sentence cannot
# outlive the measurement.
assert B['n_sys_le_1e15'] == C['n_sys_le_1e15'], (B, C)
assert C['sys_med_sel'] > B['sys_med_sel'], 'correction must raise the limit'

# ----------------------------------------------------- the crossings' fits
# D6.4: the imaginary-part rejections stand.  The omitted parallax leaks a
# little of Re into Im; quantify the largest leak over the fitted crossings
# so the reader can check it against the rejections themselves.
led = P['ledger']
m('PxNLedger', '%d' % len(led))
worst = max(led, key=lambda r: r['beams'])
m('PxWorstStar', worst['star'].replace('bet Pic', r'$\beta$~Pic')
  .replace('eta Crv', r'$\eta$~Crv'))
m('PxWorstBeams', '%.3f' % worst['beams'])
m('PxWorstRetain', '%.3f' % worst['Bm'])
m('PxImLeakMax', '%.3f' % max(r['imk'] for r in led))
m('PxImLeakMaxX', '%.3f' % max(r['imkx'] for r in led))

# ------------------------------------------ D7: the absolute-scale check
F = P['family']['12m']
m('PxNTwelveConfig', '%d' % F['n'])
# The AU Mic block sits at 0.245 beams.  Read the prediction off the measured
# library at that abscissa rather than retyping it.
X = 0.245
i = min(range(len(F['x'])), key=lambda j: abs(F['x'][j] - X))
assert abs(F['x'][i] - X) < 1e-9, F['x']
m('PxAuMicBeams', '%.3f' % X)
m('PxAuMicPred', '%.2f' % F['med'][i])
m('PxAuMicPredLo', '%.2f' % F['lo'][i])
m('PxAuMicPredHi', '%.2f' % F['hi'][i])
m('PxAuMicLossPct', '%.0f' % (100.0 * (1 - F['med'][i])))
m('PxAuMicLossLoPct', '%.0f' % (100.0 * (1 - F['hi'][i])))
m('PxAuMicLossHiPct', '%.0f' % (100.0 * (1 - F['lo'][i])))

# The two published comparisons.  These are other groups' numbers and our
# own measured amplitudes; they are constants of the comparison, recorded
# here with their sources so that no use site retypes them.
AUMIC_OBS_LO, AUMIC_OBS_HI = 0.81, 0.82       # USB / LSB vs MacGregor+2020
ROSS_OBS_LO, ROSS_OBS_HI = 0.98, 0.99         # two flares vs Burton (2024)
m('PxAuMicObsLo', '%.2f' % AUMIC_OBS_LO)
m('PxAuMicObsHi', '%.2f' % AUMIC_OBS_HI)
m('PxRossObsLo', '%.2f' % ROSS_OBS_LO)
m('PxRossObsHi', '%.2f' % ROSS_OBS_HI)
A = P['family']['aca']
j = min(range(len(A['x'])), key=lambda k: abs(A['x'][k] - 0.05))
m('PxRossBeamsLo', '0.04')
m('PxRossBeamsHi', '0.05')
m('PxRossPredLossPct', '%.1f' % (100.0 * (1 - A['med'][j])))

# What fraction of the AU Mic deficit the parallax term explains, on the
# measured beam.  This is the number that turns "no room for a second term"
# into "no room for a second term larger than about 10 per cent", and it is
# computed, not asserted.
obs = 0.5 * (AUMIC_OBS_LO + AUMIC_OBS_HI)
frac = (1 - F['med'][i]) / (1 - obs)
resid = F['med'][i] - obs
m('PxAuMicExplainedPct', '%.0f' % (100.0 * frac))
m('PxAuMicResidLoPct', '%.0f' % (100.0 * (F['med'][i] - AUMIC_OBS_HI)))
m('PxAuMicResidHiPct', '%.0f' % (100.0 * (F['med'][i] - AUMIC_OBS_LO)))
m('PxScaleBoundPct', '10')
# ★ A check that cannot fail is not a check.  The claim the manuscript makes
# is specifically that the parallax term does NOT close the whole gap, i.e.
# the residual is positive and smaller than the bound quoted beside it.  Both
# halves are asserted, so that a future beam library which either closed the
# gap or blew past the bound would stop the build.
assert 0.0 < resid < 0.10, resid
assert 0.4 < frac < 0.9, frac

with open(OUT, 'w') as fh:
    fh.write('%% GENERATED by parallax_v404.py -- do not hand-edit.\n')
    for k in sorted(M):
        fh.write('\\newcommand{\\%s}{%s}\n' % (k, M[k]))

print('parallax_v404: per-window loss median %.2f%%, p90 %.2f%%, p99 %.1f%%, '
      'max %.1f%%; %d of %d windows above 10%%'
      % (100 * R['median'], 100 * R['p90'], 100 * R['p99'], 100 * R['max'],
         R['n_gt10'], R['n']))
print('  headline per-system P90 %.2f -> %.2f e15 W (%+.2f%%), systems at '
      '1e15 W %d -> %d'
      % (B['sys_med_sel'] / 1e15, C['sys_med_sel'] / 1e15,
         100 * (C['sys_med_sel'] / B['sys_med_sel'] - 1),
         B['n_sys_le_1e15'], C['n_sys_le_1e15']))
print('  D7: %d real 12 m configurations predict %.2f (%.2f-%.2f) at %.3f '
      'beams against %.2f-%.2f observed -> %.0f%% of the deficit, residual '
      '%.0f-%.0f%%'
      % (F['n'], F['med'][i], F['lo'][i], F['hi'][i], X,
         AUMIC_OBS_LO, AUMIC_OBS_HI, 100 * frac,
         100 * (F['med'][i] - AUMIC_OBS_HI), 100 * (F['med'][i] - AUMIC_OBS_LO)))
print('  -> %s (%d macros)' % (os.path.basename(OUT), len(M)))
