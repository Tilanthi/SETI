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
import math
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

# ===================================================================== v4.08
# ★★★ D30.  THE LOSS MODEL HAS NOW BEEN MEASURED ON SKY, AND IT IS
# PESSIMISTIC BY 7 PER CENT -- so the fraction of the AU Mic deficit that
# geometry explains goes DOWN and the residual absolute-scale term goes UP.
#
# Project 2024.1.01095.S writes the star's APPARENT position into
# FIELD::PHASE_DIR: the pipeline's barycentric offset and the independently
# computed annual-parallax displacement cancel to 0.1-0.2 mas at all ten
# retained executions, through a 3.8x change in magnitude and a ~170 degree
# rotation between January and late May -- proper motion, being monotonic at
# 0.456"/yr, cannot imitate that.  So an independent reduction of those
# visibilities by a phase-centre estimator carries no positional error, and
# running OUR extractor on the SAME visibilities at the SAME timestamps
# isolates OUR loss.  In May, at 0.42 of a synthesised beam, the model
# predicts 0.717 retained and we measure 0.78 +- 0.03: it over-predicts the
# LOSS by a factor 0.22/0.283.  Scale the predicted loss at AU Mic's 0.245
# beams by that same factor and the retained amplitude rises, so geometry
# explains LESS of the 2015 Band 6 deficit than v4.07 claimed.
AU = json.load(open(os.path.join(HERE, 'r8inputs', 'aumic_scale_v408.json')))
_may, _jan = AU['may'], AU['january']
m('PxOnSkyBeams', '%.2f' % (_may['delta_arcsec'] / _may['theta_syn_arcsec']))
m('PxOnSkyPred', '%.3f' % _may['predicted_retained'])
m('PxOnSkyMeas', '%.2f' % _may['ratio'])
m('PxOnSkyMeasErr', '%.2f' % _may['ratio_err'])
PESS = (1 - _may['ratio']) / (1 - _may['predicted_retained'])
# Two framings, both emitted, because they differ by a factor of three and a
# reader must not have to guess which one a bare "pessimistic by X per cent"
# means: the shortfall in AMPLITUDE (6 points of retained flux) and the
# fraction by which the LOSS itself is over-predicted (22 per cent of it).
m('PxPessAmpPct', '%.0f' % (100 * (_may['ratio'] - _may['predicted_retained'])))
m('PxPessLossPct', '%.0f' % (100 * (1 - PESS)))
# ★ The model must be pessimistic, not optimistic.  A model that UNDER-predicted
# the loss would mean the survey-wide table above is anti-conservative, and the
# whole of this appendix would have to be re-derived rather than annotated.
assert 0.5 < PESS < 1.0, (
    'the on-sky measurement says the loss model is OPTIMISTIC (loss ratio '
    '%.3f): the survey-wide loss table is then anti-conservative and must be '
    'recomputed, not annotated' % PESS)
pred_corr = 1 - PESS * (1 - F['med'][i])
m('PxAuMicPredCorr', '%.2f' % pred_corr)

# What fraction of the AU Mic deficit the parallax term explains, on the
# measured beam CORRECTED BY THE ON-SKY CALIBRATION of that beam.  This is the
# number that turns "no room for a second term" into "no room for a second
# term larger than about 10 per cent", and it is computed, not asserted.
obs = 0.5 * (AUMIC_OBS_LO + AUMIC_OBS_HI)
frac = (1 - pred_corr) / (1 - obs)
resid = pred_corr - obs
frac_raw = (1 - F['med'][i]) / (1 - obs)
m('PxAuMicExplainedPct', '%.0f' % (100.0 * frac))
m('PxAuMicExplainedRawPct', '%.0f' % (100.0 * frac_raw))
m('PxAuMicResidLoPct', '%.0f' % (100.0 * (pred_corr - AUMIC_OBS_HI)))
m('PxAuMicResidHiPct', '%.0f' % (100.0 * (pred_corr - AUMIC_OBS_LO)))
# ★★ v4.08: THE BOUND WAS THE TYPED LITERAL '10' AND IT IS NOW TOO SMALL.
# Correcting the loss model by its own on-sky calibration moves the residual
# from 8 to 11 per cent, so a typed 10 would have been quietly wrong in the
# unsafe direction.  Computed here, from the largest residual, rounded up.
_resid_hi = pred_corr - AUMIC_OBS_LO
m('PxScaleBoundPct', '%d' % math.ceil(100.0 * _resid_hi))
# ★ A check that cannot fail is not a check.  The claim the manuscript makes
# is specifically that the parallax term does NOT close the whole gap, i.e.
# the residual is positive and no larger than the bound quoted beside it.
# Both halves are asserted, so that a future beam library which either closed
# the gap or blew past the bound would stop the build.
assert 0.0 < resid < 0.15, resid
assert 0.3 < frac < 0.9, frac
assert 0.01 * float(M['PxScaleBoundPct']) >= _resid_hi, (
    'the quoted absolute-scale bound %s per cent is smaller than the measured '
    'residual %.1f per cent' % (M['PxScaleBoundPct'], 100 * _resid_hi))
# ★★ and the correction must move the answer in the stated DIRECTION: a
# pessimistic model means geometry explains LESS, not more.  Asserted, so that
# applying the calibration the wrong way round stops the build.
assert frac < frac_raw, ('the on-sky calibration was applied in the wrong '
                         'direction: it must REDUCE the fraction geometry '
                         'explains (%.3f vs %.3f)' % (frac, frac_raw))

# ★★ THE STRONGER CHECK, available for the first time.  The January
# configuration is geometry-free (delta/theta = 0.023, predicted loss 0.2 per
# cent), so the same comparison there measures our EXTRACTOR SCALE with no
# geometry in it -- which the AU Mic / Ross 154 pair above conflates.
m('PxJanBeams', '%.3f' % (_jan['delta_arcsec'] / _jan['theta_syn_arcsec']))
m('PxJanRatio', '%.3f' % _jan['ratio'])
m('PxJanRatioErr', '%.3f' % _jan['ratio_err'])
m('PxJanFluxMJy', '%.1f' % _jan['published_mJy'])
m('PxJanScalePct', '%.0f' % (100 * max(abs(1 - _jan['ratio']), _jan['ratio_err'])))
m('PxJanThetaSyn', '%.2f' % _jan['theta_syn_arcsec'])
m('PxJanDelta', '%.4f' % _jan['delta_arcsec'])
m('PxBandGHz', '%.0f' % AU['band_GHz'])
# ★ It is only a scale check if the geometry really is negligible there: the
# predicted loss must be smaller than the measurement error, or the two terms
# are not separated and the sentence must not be written.
assert (1 - _jan['predicted_retained']) < _jan['ratio_err'], (
    'the January configuration is not geometry-free: predicted loss %.4f '
    'against a measurement error of %.4f'
    % (1 - _jan['predicted_retained'], _jan['ratio_err']))
# ★ And the primary beam is NOT the term on either epoch -- stated because that
# was the hypothesis D29 had to kill.
assert 1 - AU['primary_beam']['atten_at_may_offset'] < 1e-4, AU['primary_beam']
m('PxAuMicPbPpm', '%.1f' % (1e6 * (1 - AU['primary_beam']['atten_at_may_offset'])))
m('PxAuMicPbFwhm', '%.1f' % AU['primary_beam']['fwhm_arcsec'])

# =====================================================================
# ★ v4.08 (D33): THE SECOND INDEPENDENT EXTERNAL TEST OF THE FLUX SCALE
# =====================================================================
# The tau Ceti Letter that commissioned this measurement is CANCELLED (D33);
# this one check is the only part of it that enters the paper.  epsilon Eridani
# has published millimetre photometry from execution blocks this survey also
# searched.  Their three flares are all in the 2015 January 12 m block, where
# the star sits 17.99 arcsec off axis near 0.7 of the primary-beam FWHM -- the
# stratum this paper WITHHOLDS under its own rule -- so that block plays no part
# here.  The 2016 ACA executions put the star at the pointing centre, where no
# beam correction enters at all, and there the comparison is clean.
#
# ★ The ratio and its error are RECOMPUTED from the four measurements; nothing
# is transcribed, so a mistyped ratio cannot survive.
EPS = json.load(open(os.path.join(HERE, 'r8inputs', 'epseri_scale_v408.json')))
_eps_pub = EPS['published_uJy'] / 1e3
_eps_pub_err = EPS['published_err_uJy'] / 1e3
_eps_ratio = EPS['ours_mJy'] / _eps_pub
_eps_ratio_err = _eps_ratio * math.hypot(EPS['ours_err_mJy'] / EPS['ours_mJy'],
                                         _eps_pub_err / _eps_pub)
m('PxEpsN', '%d' % EPS['n_blocks'])
m('PxEpsHours', '%.2f' % EPS['on_source_h'])
m('PxEpsOurs', '%.3f' % EPS['ours_mJy'])
m('PxEpsOursErr', '%.3f' % EPS['ours_err_mJy'])
m('PxEpsPubUJy', '%.0f' % EPS['published_uJy'])
m('PxEpsPubErrUJy', '%.0f' % EPS['published_err_uJy'])
m('PxEpsRatio', '%.2f' % _eps_ratio)
m('PxEpsRatioErr', '%.2f' % _eps_ratio_err)
m('PxEpsOffTwelve', '%.2f' % EPS['twelve_m_offset_arcsec'])
m('PxEpsBand', EPS['band'])
# ★ "do not oversell it" (D33), as two assertions rather than as an adjective.
# It must be CONSISTENT with unity -- otherwise it is not a validation and the
# sentence changes -- and it must be LESS precise than the January check, or the
# paper would be quoting the weaker bound as though it were the stronger.
assert abs(1.0 - _eps_ratio) < _eps_ratio_err, (
    'the epsilon Eridani scale check is not consistent with unity: %.2f +- %.2f'
    % (_eps_ratio, _eps_ratio_err))
assert _eps_ratio_err > _jan['ratio_err'], (
    'the epsilon Eridani check (+-%.2f) is tighter than the January one '
    '(+-%.3f); the paper quotes January as the bound and must be re-worded'
    % (_eps_ratio_err, _jan['ratio_err']))
# ★ and the two checks are only INDEPENDENT tests of the scale if they share
# neither band nor array.  Asserted, because that is the claim being made.
assert EPS['band'] != '3' and '7 m' in EPS['array'], (EPS['band'], EPS['array'])
assert abs(AU['band_GHz'] - 106.0) < 1.0, AU['band_GHz']

# ★★ v4.08: macro count pinned with ==, as for the stack and round 99.
NMACRO = int(os.environ.get('PARALLAX_NMACRO', '71'))
assert len(M) == NMACRO, (
    'parallax_v404 emitted %d macros, not the pinned %d: a macro has been '
    'ADDED or SILENTLY DROPPED' % (len(M), NMACRO))

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
      'beams against %.2f-%.2f observed'
      % (F['n'], F['med'][i], F['lo'][i], F['hi'][i], X,
         AUMIC_OBS_LO, AUMIC_OBS_HI))
print('  D30: the model is %.0f points pessimistic in amplitude on sky (%.2f measured vs %.3f '
      'predicted at %.2f beams), so the prediction becomes %.2f and geometry '
      'explains %.0f%% not %.0f%%, residual %.0f-%.0f%% (bound %s%%)'
      % (100 * (_may['ratio'] - _may['predicted_retained']), _may['ratio'], _may['predicted_retained'],
         _may['delta_arcsec'] / _may['theta_syn_arcsec'], pred_corr,
         100 * frac, 100 * frac_raw, 100 * (pred_corr - AUMIC_OBS_HI),
         100 * _resid_hi, M['PxScaleBoundPct']))
print('  D30: the GEOMETRY-FREE check -- January, %.3f beams: our extractor '
      'reproduces an independent reduction of the SAME visibilities to '
      '%.3f +- %.3f on a %.1f mJy Band 3 point source (extractor scale ~%s%%)'
      % (_jan['delta_arcsec'] / _jan['theta_syn_arcsec'], _jan['ratio'],
         _jan['ratio_err'], _jan['published_mJy'], M['PxJanScalePct']))
print('  -> %s (%d macros)' % (os.path.basename(OUT), len(M)))
