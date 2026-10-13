#!/usr/bin/env python3
"""round 95 (DECISIONS_R8 D16): A FLAT 5 SIGMA IS NOT A UNIFORM CRITERION.

This is the reframing, not a gain.  The survey triggers when a window's stellar
position reaches T = 5.  That is a threshold on a statistic, not a false-alarm
rate, and the two are not interchangeable here because the number of searched
(channel, drift) cells per window runs over four and a half orders of
magnitude.  A window with 112 cells is protected at 5 sigma far better than one
with 6.87e6 cells, and the paper's crossing population is the direct
consequence.

Three quantities are computed:

  1. Per window, the realised scale of its own null, s_w, by two INDEPENDENT
     routes, and the fitted number of independent cells N_ind.  Published in
     the catalogue (v342_calc.py, D16) and summarised here.
  2. The statistic each window would have to reach for a fixed false-alarm
     probability, T_w = s_w Phi^-1((1-alpha)^(1/N_ind)), at a per-window
     alpha = 1 per cent and at the per-window alpha that delivers 1 per cent
     over the whole catalogue.
  3. The number of crossings EXPECTED at a flat 5 sigma, which is the number
     that changes what the paper claims.

★ THE POINT, and why this strengthens the null result rather than weakening it:
27 to 37 of the 51 measured crossings are expected by chance at a flat 5 sigma
(three independent routes bracket Class A at 33-41 against 50 observed), so the
crossing population needs no artefact hypothesis at all -- and the smallest
crossing in the survey, eta Crv's T* = 5.006, is BELOW what its own window
requires under either target.  The rank screen and the recurrence test are
relative to the same window and are unaffected by any of this.

This generator also carries the measured NULLS of D16, stated as nulls, and the
one measured-but-unapplied gain, because a referee is entitled to know which
recommended upgrades were tried and found to be worth nothing:

  * morphology-for-threshold: x1.16 in P90^sel, i.e. 16 per cent WORSE;
  * drift-grid quantisation recovery: x1.00, because the measured P90^sel
    already contains the loss -- so nobody may correct for it twice;
  * the top-hit deduplication artefact: absent, and of the opposite sign;
  * a 3-channel matched filter: x1.08 fixed / x1.17 offset-matched, measured
    against the real channel covariance, NOT APPLIED here because it changes
    the search statistic and therefore the frozen crossing list.

Inputs (all frozen, all in the version folder):
  r8inputs/scale_v406.jsonl   the per-window scale measurement (3005 products)
  r8inputs/sens_v406.json     the Item 1/2/3/7 summary numbers, each one an
                              output of a measurement recorded in
                              referee_r8/SENSITIVITY_UPGRADES.md
  per_target_results_v3.99.csv  MUST FOLLOW v342_calc.py
"""
import csv
import json
import os

import numpy as np
from scipy.stats import norm

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, 'survey_numbers_round95.tex')
M = {}


def m(k, v):
    assert k not in M, k
    M[k] = v


def sci(x, nd=2):
    e = int(np.floor(np.log10(abs(x))))
    return r'%.*f \times 10^{%d}' % (nd, x / 10.0 ** e, e)


CAT = list(csv.DictReader(open(os.path.join(HERE,
                                           'per_target_results_v3.99.csv'))))
SENS = json.load(open(os.path.join(HERE, 'r8inputs/sens_v406.json')))

# The catalogue carries the measurement, so this generator reads the SHIPPED
# columns rather than re-deriving the join.  That is deliberate: if the columns
# and the prose ever disagreed, there would be no way to tell which was right.
COV = [r for r in CAT if r['n_ind_cells'] != '']
A = [r for r in COV if r['search_class'] == 'A']
B = [r for r in COV if r['search_class'] == 'B']
assert len(A) + len(B) == len(COV), (len(A), len(B), len(COV))
m('TuNCov', '%d' % len(COV))
m('TuNCovA', '%d' % len(A))
m('TuNCovB', '%d' % len(B))
m('TuNWinAll', '%d' % len(CAT))

XR = [r for r in CAT if r['crossing'] == 'True']
XC = [r for r in XR if r['n_ind_cells'] != '']
m('TuNCrossAll', '%d' % len(XR))
m('TuNCross', '%d' % len(XC))
m('TuNCrossA', '%d' % sum(1 for r in XC if r['search_class'] == 'A'))
m('TuNCrossB', '%d' % sum(1 for r in XC if r['search_class'] == 'B'))
m('TuNCrossUncov', '%d' % (len(XR) - len(XC)))

CELLS = np.array([float(r['n_search_cells']) for r in COV])
NIND = np.array([float(r['n_ind_cells']) for r in COV])
SW = np.array([0.5 * (float(r['scale_route_a']) + float(r['scale_route_b']))
               for r in COV])
SA = np.array([float(r['scale_route_a']) for r in COV])
SB = np.array([float(r['scale_route_b']) for r in COV])
TW = np.array([float(r['trigger_1pct_window']) for r in COV])
TS = np.array([float(r['trigger_1pct_survey']) for r in COV])
ISA = np.array([r['search_class'] == 'A' for r in COV])

# ★ The spread of the cell count is the whole reason a flat threshold is not a
# criterion.  Assert it spans more than three decades, because if it did not,
# this section would be making a fuss about nothing.
m('TuCellsLo', '%d' % round(CELLS.min()))
m('TuCellsHi', sci(CELLS.max()))
m('TuCellsMed', '%d' % round(np.median(CELLS)))
m('TuCellsDecades', '%.1f' % np.log10(CELLS.max() / CELLS.min()))
assert CELLS.max() / CELLS.min() > 1e3, (CELLS.min(), CELLS.max())
m('TuNindFrac', '%.3f' % np.median(NIND / CELLS))

# -------------------------------------------------- 1. the realised null scale
for tag, v in (('A', SA), ('B', SB), ('W', SW)):
    m('TuScale' + tag + 'Med', '%.3f' % np.median(v))
    m('TuScale' + tag + 'PSixteen', '%.3f' % np.percentile(v, 16))
    m('TuScale' + tag + 'PEightFour', '%.3f' % np.percentile(v, 84))
    m('TuScale' + tag + 'PNineNine', '%.3f' % np.percentile(v, 99))
    m('TuScale' + tag + 'Max', '%.3f' % v.max())
m('TuScaleAgree', '%.3f' % np.median(SA / SB))
# The band a reader should quote: the p1-p99 deviation of s_w from unity.  Not
# "+-5 per cent", which is the level at which the two routes' MEDIANS sit.
m('TuScaleBandPct', '%.0f' % (100 * max(abs(np.percentile(SW, 99) - 1),
                                        abs(np.percentile(SW, 1) - 1))))
# The one broken window, found by requiring BOTH routes to exceed a threshold
# fixed before the numbers were tabulated.  Counted at four cuts, because the
# claim is that the count does not depend on where the cut is put.
FLAGTH = (1.1, 1.15, 1.2, 1.5)
both = {t: [r for r, a, b in zip(COV, SA, SB) if a > t and b > t]
        for t in FLAGTH}
either = {t: [r for r, a, b in zip(COV, SA, SB) if a > t or b > t]
          for t in FLAGTH}
m('TuFlagTh', '%.1f' % 1.2)
m('TuNFlagBoth', '%d' % len(both[1.2]))
m('TuNFlagEither', '%d' % len(either[1.2]))
m('TuFlagBothLadder', ' / '.join('%d' % len(both[t]) for t in FLAGTH))
m('TuFlagEitherLadder', ' / '.join('%d' % len(either[t]) for t in FLAGTH))
m('TuFlagThLadder', ' / '.join('%.2f' % t for t in FLAGTH))
# ★ The count must be the SAME at every cut; if it is not, the "exactly one
# broken window" claim is a cut-dependent statement and must not be made.
assert len({len(both[t]) for t in FLAGTH}) == 1, {t: len(both[t])
                                                  for t in FLAGTH}
assert len(both[1.2]) == 1, [r['star_name'] for r in both[1.2]]
_bw = both[1.2][0]
m('TuFlagStar', _bw['star_name'])
m('TuFlagEb', _bw['eb'].replace('_', r'\_'))
m('TuFlagSa', '%.2f' % float(_bw['scale_route_a']))
m('TuFlagSb', '%.2f' % float(_bw['scale_route_b']))
m('TuFlagTstar', '%.2f' % float(_bw['star_snr']))
m('TuFlagIsCross', 'yes' if _bw['crossing'] == 'True' else 'no')
m('TuNFlagCross', '%d' % sum(1 for r in both[1.2] if r['crossing'] == 'True'))
m('TuNFlagCrossEither',
  '%d' % sum(1 for r in either[1.2] if r['crossing'] == 'True'))
# By BLOCK attribution: the same execution block holds three further windows
# whose retained products can no longer be re-reduced, so they cannot be
# measured -- but they are the same defective block, and the paper must count
# them.  This is the honest total and it is larger than the measured one.
_blkcross = [r for r in XR if r['eb'] == _bw['eb']]
m('TuNFlagCrossBlock', '%d' % len(_blkcross))
assert len(_blkcross) >= len(both[1.2]), (len(_blkcross), len(both[1.2]))

# ------------------------------------- 2. the threshold for a uniform criterion
ALPHA_WIN = SENS['alpha_window']
m('TuAlphaWinPct', '%g' % (100 * ALPHA_WIN))
_alpha_s = 1.0 - (1.0 - ALPHA_WIN) ** (1.0 / len(CAT))
m('TuAlphaSurvey', sci(_alpha_s))
for tag, v in (('Win', TW), ('Surv', TS)):
    m('TuT' + tag + 'Med', '%.2f' % np.median(v))
    m('TuT' + tag + 'PSixteen', '%.2f' % np.percentile(v, 16))
    m('TuT' + tag + 'PEightFour', '%.2f' % np.percentile(v, 84))
    m('TuT' + tag + 'Lo', '%.2f' % v.min())
    m('TuT' + tag + 'Hi', '%.2f' % v.max())
    m('TuT' + tag + 'A', '%.2f' % np.median(v[ISA]))
    m('TuT' + tag + 'B', '%.2f' % np.median(v[~ISA]))
# The flat 5 sigma is wrong in BOTH directions, which is the sentence that
# stops a reader concluding the survey was simply too lax.
m('TuNOver', '%d' % int((TW < 5).sum()))
m('TuOverMed', '%.2f' % np.median(5 - TW[TW < 5]))
m('TuNUnder', '%d' % int((TW > 5).sum()))
m('TuNUnderSurv', '%d' % int((TS > 5).sum()))
assert (TW < 5).sum() > 0 and (TW > 5).sum() > 0, 'not wrong in both directions'
# The realised false-alarm probability of the flat threshold, per window.
PFA = -np.expm1(NIND * norm.logcdf(5.0 / SW))
m('TuPfaMed', sci(float(np.median(PFA))))
m('TuPfaPEightFour', '%.3f' % np.percentile(PFA, 84))
m('TuPfaPNineNine', '%.3f' % np.percentile(PFA, 99))
m('TuPfaMax', '%.3f' % PFA.max())

# ---------------------------------------------- 3. how many crossings are free
PFA_IDEAL = -np.expm1(NIND * norm.logcdf(5.0 / 1.0))
for tag, p in (('Ideal', PFA_IDEAL), ('Real', PFA)):
    m('TuExp' + tag, '%.1f' % p.sum())
    m('TuExp' + tag + 'A', '%.1f' % p[ISA].sum())
    m('TuExp' + tag + 'B', '%.1f' % p[~ISA].sum())
m('TuExpRealPct', '%.0f' % (100 * (PFA.sum() / PFA_IDEAL.sum() - 1)))
# The three independent routes, of which this is one.  The other two live in
# the sens study and in epoch_v403.py; carrying all three is the point, because
# no single estimator is being asked to bear the claim.
m('TuRouteEmp', '%.1f' % SENS['route_empirical_512'])
m('TuRouteMc', '%.1f' % PFA[ISA].sum())
m('TuRouteLoose', '%.1f' % SENS['route_loose_join'])
_routes = [SENS['route_empirical_512'], float(PFA[ISA].sum()),
           SENS['route_loose_join']]
m('TuRouteLo', '%d' % int(np.floor(min(_routes))))
m('TuRouteHi', '%d' % int(np.floor(max(_routes))))
m('TuBracketLo', '%d' % int(np.floor(PFA_IDEAL.sum())))
m('TuBracketHi', '%d' % int(np.floor(max(_routes))))
# ★ The routes must AGREE, and "agree" has to be a number: no route may differ
# from another by more than a factor 1.5, or the bracket is meaningless.
assert max(_routes) / min(_routes) < 1.5, _routes
m('TuRouteSpread', '%.2f' % (max(_routes) / min(_routes)))
m('TuObsA', '%d' % sum(1 for r in XC if r['search_class'] == 'A'))
# ... and the whole claim reduces to this comparison, so state the ratio.
m('TuExpObsFrac', '%.0f' % (100 * PFA[ISA].sum()
                            / max(1, sum(1 for r in XC
                                         if r['search_class'] == 'A'))))

# How many individual crossings fail their own window's requirement
def _below(col):
    return sum(1 for r in XC if float(r['star_snr']) < float(r[col]))


m('TuNBelowWin', '%d' % _below('trigger_1pct_window'))
m('TuNBelowSurv', '%d' % _below('trigger_1pct_survey'))
assert _below('trigger_1pct_survey') >= _below('trigger_1pct_window'), (
    'the survey-wide requirement is the stricter one, so it cannot leave '
    'fewer crossings below it')

# eta Crv, the smallest crossing in the survey and the one the paper singles out
_eta = min(XC, key=lambda r: float(r['star_snr']))
m('TuEtaStar', _eta['star_name'].replace('eta Crv', r'$\eta$~Crv'))
m('TuEtaEb', _eta['eb'].replace('_', r'\_'))
m('TuEtaTstar', '%.4f' % float(_eta['star_snr']))
m('TuEtaCells', sci(float(_eta['n_search_cells'])))
m('TuEtaNind', sci(float(_eta['n_ind_cells'])))
m('TuEtaSw', '%.3f' % (0.5 * (float(_eta['scale_route_a'])
                              + float(_eta['scale_route_b']))))
m('TuEtaTwin', '%.3f' % float(_eta['trigger_1pct_window']))
m('TuEtaTsurv', '%.3f' % float(_eta['trigger_1pct_survey']))
# ★ The claim about eta Crv is that it is below BOTH.  Assert it; if a future
# catalogue moves it above one of them, the sentence must not survive.
assert float(_eta['star_snr']) < float(_eta['trigger_1pct_window']), _eta
assert float(_eta['star_snr']) < float(_eta['trigger_1pct_survey']), _eta
m('TuEtaScaleClean', 'yes' if abs(0.5 * (float(_eta['scale_route_a'])
                                         + float(_eta['scale_route_b'])) - 1)
  < 0.05 else 'no')

# ------------------------------------------------------ 4. the measured nulls
N = SENS['nulls']
m('TuMorphFactor', '%.2f' % N['morph']['p90_factor'])
m('TuMorphFactorLo', '%.2f' % N['morph']['p90_lo'])
m('TuMorphFactorHi', '%.2f' % N['morph']['p90_hi'])
m('TuMorphPctWorse', '%.0f' % (100 * (N['morph']['p90_factor'] - 1)))
m('TuMorphSlope', '%.2f' % abs(N['morph']['far_log_slope_per_sigma']))
m('TuMorphNeedFive', '%.0f' % (100 * N['morph']['need_frac_for_5pct']))
m('TuMorphNeedTen', '%.0f' % (100 * N['morph']['need_frac_for_10pct']))
m('TuMorphNeedTwenty', '%.0f' % (100 * N['morph']['need_frac_for_20pct']))
m('TuMorphGot', '%.1f' % (100 * N['morph']['got_frac']))
m('TuMorphThreshOld', '%.2f' % N['morph']['thresh_old'])
m('TuMorphThreshNew', '%.2f' % N['morph']['thresh_new'])
m('TuMorphFluxGain', '%.3f' % N['morph']['flux_gain'])
m('TuMorphRho', '%.3f' % N['morph']['hanning_rho1'])
m('TuMorphAuc', '%.3f' % N['morph']['auc_best'])
m('TuMorphAucStat', N['morph']['auc_best_stat'])
m('TuMorphCostLo', '%.0f' % (100 * N['morph']['completeness_cost_lo']))
m('TuMorphCostHi', '%.0f' % (100 * N['morph']['completeness_cost_hi']))
m('TuMorphTauOld', '%.2f' % N['morph']['tau90_old'])
m('TuMorphTauNew', '%.2f' % N['morph']['tau90_new'])
# ★ The falsifier.  A cut that rejects nothing may simply be broken, so the
# same cuts were run on signals they SHOULD reject.  Without this the null is
# not a measurement.
m('TuMorphLineRej', '%d' % N['morph']['reject_resolved_line'])
m('TuMorphLineN', '%d' % N['morph']['reject_resolved_line_n'])
m('TuMorphTransRej', '%d' % N['morph']['reject_transient'])
m('TuMorphTransN', '%d' % N['morph']['reject_transient_n'])
m('TuMorphKeepCarrier', '%.0f' % (100 * N['morph']['keep_carrier']))
assert N['morph']['reject_resolved_line'] == N['morph']['reject_resolved_line_n']
assert N['morph']['p90_factor'] > 1.0, 'this item is reported as a null'
# The arithmetic, recomputed here from the slope rather than copied: a veto must
# remove 1 - exp(-slope * df) of the false alarms to buy a flux fraction df.
_sl = abs(N['morph']['far_log_slope_per_sigma'])
for pct, key in ((5, 'need_frac_for_5pct'), (10, 'need_frac_for_10pct'),
                 (20, 'need_frac_for_20pct')):
    _pred = 1.0 - np.exp(-_sl * N['morph']['thresh_old'] * pct / 100.0)
    assert abs(_pred - N[ 'morph'][key]) < 0.02, (pct, _pred, N['morph'][key])
m('TuMorphNeedCheck', 'reproduced')

Q = N['quant']
# Quoted to three digits, because "1.00 +- 0.01" hides that the measured net is
# BELOW one on both sides: 0.997 against the trigger threshold and 0.992
# against the rank screen, the latter worse because a maximum over ~1e5-1e6
# cells sits on a sharper local peak than an injected carrier does.
m('TuQuantNet', '%.3f' % Q['net'])
m('TuQuantNetErr', '%.3f' % Q['net_err'])
m('TuQuantNetRank', '%.3f' % Q['net_rank'])
assert Q['net'] <= 1.0 and Q['net_rank'] <= 1.0, Q
m('TuQuantGross', '%.4f' % Q['gross_signal'])
m('TuQuantNoiseLo', '%.3f' % Q['noise_infl_lo'])
m('TuQuantNoiseHi', '%.3f' % Q['noise_infl_hi'])
m('TuQuantAlignPct', '%.1f' % (100 * Q['total_align_loss']))
m('TuQuantCeilPct', '%.1f' % (100 * Q['integer_shift_ceiling_loss']))
m('TuQuantResidPct', '%.2f' % (100 * (Q['total_align_loss']
                                      - Q['integer_shift_ceiling_loss'])))
assert abs(Q['net'] - 1.0) <= Q['net_err'] + 1e-9, Q
# ★ THE SENTENCE THAT STOPS A DOUBLE CORRECTION.  The injection campaigns draw
# drift and sub-channel offset continuously, so the quantisation loss is inside
# the measured P90^sel already.  Assert the provenance flag rather than trust
# the prose, because this is the kind of claim that decays.
assert Q['injection_draws_continuous'] is True, Q
m('TuQuantInside', 'already contained in')

D = N['dedup']
m('TuDedupWindows', '%d' % D['dedup_windows_in_our_code'])
assert D['dedup_windows_in_our_code'] == 0, D
m('TuDedupYieldUp', '%.0f' % (100 * D['yield_ratio_double'] - 100))
m('TuDedupYieldDown', '%.0f' % (100 - 100 * D['yield_ratio_quarter']))
m('TuDedupPeakPct', '%.1f' % (100 * D['peak_move_max']))
m('TuDedupRange', '%d' % D['ceiling_range_factor'])
m('TuDedupMonoN', '%d' % D['n_monotone'])
m('TuDedupN', '%d' % D['n_windows'])
m('TuDedupTruncN', '%d' % D['n_truncated_hitlists'])
m('TuDedupTruncCap', '%d' % D['hitlist_cap'])
assert D['yield_ratio_double'] >= 1.0, 'the sign is the opposite of TurboSETI'

# ---------------------------------- 5. the one measured, unapplied improvement
F = SENS['matched_filter']
m('TuMfFixed', '%.2f' % F['gain_fixed_mean_offset'])
m('TuMfMatched', '%.2f' % F['gain_matched_mean_offset'])
m('TuMfCentre', '%.3f' % F['gain_at_centre'])
m('TuMfEdgeFixed', '%.3f' % F['gain_fixed_at_boundary'])
m('TuMfNaive', '%.4f' % F['naive_lag1_only'])
m('TuMfLagOne', '%.3f' % F['measured_lag1'])
m('TuMfLagTwo', '%.3f' % F['measured_lag2'])
m('TuMfPredOne', '%.3f' % F['predicted_lag1'])
m('TuMfPredTwo', '%.3f' % F['predicted_lag2'])
m('TuMfNWin', '%d' % F['n_windows'])
m('TuMfNWithin', '%d' % F['n_within_008'])
# ★ D18's correction to D16's own wording, carried here because this is where
# the gain is quoted: the verified covariance is the n = 1 population's, so the
# gain is an n = 1 gain.  The averaged windows have nearly uncorrelated
# channels and a whitening filter buys them much less.
m('TuMfScope', r'the $n=1$ (Hanning-only) population')
# ★ The relations among these five numbers, each of which can fail:
#  - at the channel centre the two filters ARE the same filter, so equal gain;
#  - the offset-matched bank cannot be worse than the one fixed filter anywhere;
#  - the mean-over-offset gain must lie between the centre and boundary values;
#  - the naive lag-1-only figure is exactly sqrt(3/2), which is why quoting it
#    is a statement about a covariance nobody measured.
assert abs(F['gain_at_centre'] - F['gain_fixed_at_centre']) < 1e-9, F
assert F['gain_matched_mean_offset'] >= F['gain_fixed_mean_offset'], F
assert F['gain_matched_at_boundary'] >= F['gain_fixed_at_boundary'], F
assert (min(F['gain_at_centre'], F['gain_fixed_at_boundary'])
        <= F['gain_fixed_mean_offset']
        <= max(F['gain_at_centre'], F['gain_fixed_at_boundary'])), F
assert abs(F['naive_lag1_only'] - np.sqrt(1.5)) < 1e-9, F
m('TuMfNaiveExact', r'\sqrt{3/2}')
assert F['gain_fixed_at_boundary'] < 1.0, (
    'the fixed filter is a LOSS at a channel boundary and the paper must say '
    'so, because that is what makes the offset-matched bank a trials problem')
m('TuMfApplied', 'not applied')

with open(OUT, 'w') as fh:
    fh.write('%% GENERATED by trigunif_v406.py -- do not hand-edit.\n')
    for k in sorted(M):
        fh.write('\\newcommand{\\%s}{%s}\n' % (k, M[k]))

print('trigunif_v406 (round 95): %d of %d catalogue windows carry a measured '
      'null scale (%d A, %d B), holding %d of the %d crossings'
      % (len(COV), len(CAT), len(A), len(B), len(XC), len(XR)))
print('  cells per window %d to %.3g (median %d), N_ind/cells %.3f -- %.1f '
      'decades, which is why a flat threshold is not a criterion'
      % (CELLS.min(), CELLS.max(), np.median(CELLS), np.median(NIND / CELLS),
         np.log10(CELLS.max() / CELLS.min())))
print('  threshold for a uniform false alarm: per-window %.0f%% needs %.2f '
      '(%.2f-%.2f; A %.2f, B %.2f); survey-wide %.0f%% needs %.2f (%.2f-%.2f)'
      % (100 * ALPHA_WIN, np.median(TW), TW.min(), TW.max(),
         np.median(TW[ISA]), np.median(TW[~ISA]), 100 * ALPHA_WIN,
         np.median(TS), TS.min(), TS.max()))
print('  the flat 5 sigma OVER-protects %d windows (median by %.2f sigma) and '
      'UNDER-protects %d; survey-wide it under-protects %d of %d'
      % ((TW < 5).sum(), np.median(5 - TW[TW < 5]), (TW > 5).sum(),
         (TS > 5).sum(), len(TS)))
print('  EXPECTED crossings at a flat 5 sigma: %.1f with an ideal unit null, '
      '%.1f with the realised scale, against %d observed'
      % (PFA_IDEAL.sum(), PFA.sum(), len(XC)))
print('    Class A, three independent routes: %.1f (empirical 512-position) / '
      '%.1f (Monte-Carlo null max) / %.1f (looser join) against %d observed'
      % (SENS['route_empirical_512'], PFA[ISA].sum(),
         SENS['route_loose_join'], sum(1 for r in XC
                                       if r['search_class'] == 'A')))
print('    %d of the %d measured crossings are below their own window\'s '
      'per-window %.0f%% threshold, %d below the survey-wide one'
      % (_below('trigger_1pct_window'), len(XC), 100 * ALPHA_WIN,
         _below('trigger_1pct_survey')))
print('  %s %s: T* = %.4f, %.3g cells, s_w = %.3f -> needs %.3f / %.3f: below '
      'both' % (_eta['star_name'], _eta['eb'], float(_eta['star_snr']),
                float(_eta['n_search_cells']),
                0.5 * (float(_eta['scale_route_a'])
                       + float(_eta['scale_route_b'])),
                float(_eta['trigger_1pct_window']),
                float(_eta['trigger_1pct_survey'])))
print('  the null is unit variance (s_w p1-p99 within %.0f%% of unity; route A '
      'median %.3f, route B %.3f); '
      'exactly %d window of %d fails at every cut in %.2f-%.2f: %s %s'
      % (100 * max(abs(np.percentile(SW, 99) - 1), abs(np.percentile(SW, 1) - 1)),
         np.median(SA), np.median(SB), len(both[1.2]), len(COV),
         min(FLAGTH), max(FLAGTH), _bw['star_name'], _bw['eb']))
print('  NULLS, measured: morphology-for-threshold x%.2f (worse); grid '
      'quantisation x%.3f+-%.3f (already inside P90^sel); dedup artefact '
      'absent, yield monotone non-decreasing'
      % (N['morph']['p90_factor'], Q['net'], Q['net_err']))
print('  UNAPPLIED gain: 3-channel matched filter x%.2f fixed / x%.2f '
      'offset-matched, %s' % (F['gain_fixed_mean_offset'],
                              F['gain_matched_mean_offset'], M['TuMfScope']))
print('  -> %s (%d macros)' % (os.path.basename(OUT), len(M)))
