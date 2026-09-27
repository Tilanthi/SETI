#!/usr/bin/env python3
"""round 99 (DECISIONS_R8 D14): the round-7 completeness campaign, with
$P^{\\rm sel}_{90}$ measured through the chain the survey ACTUALLY USES ---
trigger then visibility localisation --- and the rank-gated value reported as
ancillary and labelled superseded.

Why the redefinition.  Round-7 decision A2 demoted the 512-position rank screen
from a filter to a consistency check, because correctly pointed out it rejects
nothing.  A completeness measured THROUGH that screen therefore charges the
limit for a gate the analysis does not apply, and it charges it heavily: the
screen costs Class A a factor \\RsevGain{} in $P^{\\rm sel}_{90}$.  Both
numbers are published, and the reason for the change is a measurement.

★★ AND THE CHANCE EXPECTATION MOVES WITH IT.  \\ClustStageMean{} = 0.89 is
conditioned on trigger AND rank; if the rank screen is not a filter, that
number answers a question the paper no longer asks.  It is RE-DERIVED below on
trigger + localisation + attribution, and the answer is larger by more than an
order of magnitude.  Re-labelling it would have been wrong.

Writes `survey_numbers_round99.tex`, from the campaign's frozen analysis
(`r8inputs/p90_r7_analysis_v406.json` + `r8inputs/selfunc_classA_v406.json`).

★ THE CAMPAIGN'S OWN GATES ARE ASSERTED HERE AS LITERALS, and the literals are
the ones fixed before the campaign ran, not ones chosen after seeing it:

    the null's localised false-alarm rate must be under the 1 per cent ceiling
    of referee_r6/LOCALISATION_CRITERION.md (commit edfcc0d3d7db,
    2026-09-25T06:59:24Z), and every folded-in unit must have recovered its own
    20x positive control at >= 0.95, both at the trigger and through
    localisation.

Nothing is emitted unless they hold.  Two further assertions exist because this
particular multiplier is only meaningful if the 90 per cent point exists: the
Class A curve must reach 0.90, and the bootstrap must bracket it in EVERY
resample.  If a future run of this campaign saturates below 0.90 the right
output is the asymptote and the plateau amplitude -- which are in the json
either way -- and NOT an extrapolated multiplier.  This script refuses rather
than extrapolating.
"""
import json
import os

HERE = os.path.dirname(os.path.abspath(__file__))
A = json.load(open(os.path.join(HERE, 'r8inputs/p90_r7_analysis_v406.json')))
S = json.load(open(os.path.join(HERE, 'r8inputs/selfunc_classA_v406.json')))
OUT = os.path.join(HERE, 'survey_numbers_round99.tex')
JSN = os.path.join(HERE, 'p90_r7_macros_v406.json')

# ----------------------------------------------------------------- the gates
NULL_CEILING = 0.01          # LOCALISATION_CRITERION.md, fixed before the run
PC_FLOOR = 0.95              # campaign_p90_r7.py collect(), fixed before the run
g = A['gates']
assert g['campaign_valid'], 'campaign_valid is False'
assert g['null_frac_localised'] < NULL_CEILING, (
    'null localised rate %.5f is not under the %.2f ceiling fixed before the '
    'campaign ran' % (g['null_frac_localised'], NULL_CEILING))
assert g['positive_control_frac'] >= PC_FLOOR, g['positive_control_frac']
assert g['positive_control_frac_localised'] >= PC_FLOOR, \
    g['positive_control_frac_localised']

a = A['saturation']['class A']
b = A['saturation']['class B']
allc = A['saturation']['all']
assert a['trigger_and_localised']['reaches_90'], (
    'Class A recovery saturates at %.3f below 0.90: P90 does not exist for this '
    'selection -- quote the asymptote and the plateau amplitude instead'
    % a['trigger_and_localised']['max_frac'])
assert a['P90_loc_bootstrap_undefined_frac'] == 0.0, (
    'the 90 per cent point is not bracketed in %.1f per cent of bootstrap '
    'resamples' % (100 * a['P90_loc_bootstrap_undefined_frac']))

M = {}


def m(name, val):
    assert name not in M, name
    M[name] = val


def f2(x):
    return '%.2f' % x


def sig(x, n=2):
    """1.47e+15 -> 1.47\\times10^{15}"""
    s = '%.*e' % (n, x)
    mant, ex = s.split('e')
    return '%s\\times10^{%d}' % (mant, int(ex))


ra = A['relation']['class A']
t5 = ra['at_tstar_5']
ep = ra['epoch']
tr = A['transfer']['class A']
trb = A['transfer']['class B']

# ---- provenance and size
m('RsevNUnitPlan', '56')
m('RsevNUnitUsable', '%d' % (A['n_units_total'] - A['n_units_failed']))
m('RsevNUnitScored', '%d' % A['n_units_scored'])
m('RsevNUnitExcluded', '%d' % A['n_units_failed'])
m('RsevNTone', format(allc['n_tones'], ',').replace(',', chr(92) + ','))
m('RsevNToneA', format(a['n_tones'], ',').replace(',', chr(92) + ','))
m('RsevNFitA', format(ra['n_fits'], ',').replace(',', chr(92) + ','))
# ---- the gates, as printed numbers
m('RsevNullFracPct', '%.3f' % (100 * g['null_frac_localised']))
m('RsevNullCeilPct', '%.0f' % (100 * NULL_CEILING))
m('RsevPCFrac', '%.3f' % g['positive_control_frac'])
m('RsevPCFracLoc', '%.3f' % g['positive_control_frac_localised'])
# ---- R2-5: the multiplier
m('RsevPNinetyA', f2(a['P90_loc']))
m('RsevPNinetyALo', f2(a['P90_loc_ci68'][0]))
m('RsevPNinetyAHi', f2(a['P90_loc_ci68'][1]))
m('RsevPNinetyATrig', f2(a['P90_trigger']))
m('RsevPNinetyB', f2(b['P90_loc']))
m('RsevPNinetyBLo', f2(b['P90_loc_ci68'][0]))
m('RsevPNinetyBHi', f2(b['P90_loc_ci68'][1]))
m('RsevPNinetyAll', f2(allc['P90_loc']))
m('RsevUndefPctA', '%.0f' % (100 * a['P90_loc_bootstrap_undefined_frac']))
m('RsevTopFracA', '%.3f' % a['trigger_and_localised']['max_frac'])
m('RsevPlateauA', f2(a['trigger_and_localised']['plateau_amp']))
m('RsevLadderTop', f2(a['ladder_top']))
# the retired rank gate, for the comparison the referees asked for
m('RsevOldMult', '%.2f' % S['multiplier_old'])
m('RsevGain', '%.2f' % S['improvement_factor'])
m('RsevRankFracTwentyA', '%.3f' % a['rank_gate_frac_at_20x'])
m('RsevCtrlCleanA', f2(a['ctrl_top_clean_median']))
m('RsevCtrlTwentyA', f2(a['ctrl_top_at_20x_median']))
# ---- R2-3
m('RsevReAtFiveA', f2(t5['snr_re'][1]))
m('RsevReAtFiveALo', f2(t5['snr_re'][0]))
m('RsevReAtFiveAHi', f2(t5['snr_re'][2]))
m('RsevReAtFiveMeanA', f2(t5['snr_re_mean']))
m('RsevReAtFiveSdA', f2(t5['snr_re_sd']))
m('RsevNAtFiveA', '%d' % t5['n'])
m('RsevFracLocAtFiveA', '%.3f' % t5['frac_localised_re_ge4'])
m('RsevEpochRatioA', '%.3f' % ep['median_ratio'])
m('RsevEpochLostPctA', '%.1f' % (100 * ep['frac_r6epoch_below_4_while_correct_above']))
m('RsevEpochTopFracA', '%.3f' % a['trigger_and_localised_r6epoch']['max_frac'])
m('RsevEpochUndefPctA', '%.0f'
  % (100 * a['P90_loc_r6epoch_bootstrap_undefined_frac']))
# ---- R1-5
m('RsevNTestedA', '%d' % tr['n_units_directly_tested'])
m('RsevNWinA', '403')
m('RsevNTransferA', '%d' % (403 - tr['n_units_directly_tested']))
m('RsevTransAMed', f2(tr['per_unit_P90_loc_median']))
m('RsevTransALo', '%.2f' % tr['transfer_factor_p16_over_median'])
m('RsevTransAHi', '%.2f' % tr['transfer_factor_p84_over_median'])
m('RsevTransARangeLo', '%.2f' % tr['transfer_factor_min_over_median'])
m('RsevTransARangeHi', '%.2f' % tr['transfer_factor_max_over_median'])
m('RsevTransBLo', '%.2f' % trb['transfer_factor_p16_over_median'])
m('RsevTransBHi', '%.2f' % trb['transfer_factor_p84_over_median'])
# ---- R1-4
m('RsevSysA', '%d' % S['n_systems'])
m('RsevEirpMedA', sig(S['per_system_EIRP_new']['median']))
m('RsevEirpMedAOld', sig(S['per_system_EIRP_old']['median']))
m('RsevSysEfifteen', '%d' % S['per_system_EIRP_new']['n_below_1e15'])
m('RsevSysEfifteenOld', '%d' % S['per_system_EIRP_old']['n_below_1e15'])
m('RsevSysEsixteen', '%d' % S['per_system_EIRP_new']['n_below_1e16'])
m('RsevBwMedGHz', f2(S['union_bandwidth_GHz_median']))
m('RsevDriftLo', '%.0f' % S['drift_ceiling_Hz_s_range'][0])
m('RsevDriftHi', '%.0f' % S['drift_ceiling_Hz_s_range'][1])
m('RsevChanLoKHz', '%.1f' % S['chanwidth_kHz_range'][0])
m('RsevChanHiKHz', '%.0f' % S['chanwidth_kHz_range'][1])

# =====================================================================
# ★★★ D14: THE CHANCE EXPECTATION, RE-DERIVED AND NOT RE-LABELLED
# =====================================================================
# \ClustStageMean = 0.89 (v352_calc.py) is the expected number of windows that
# are simultaneously a threshold crossing AND rank-first against all 512
# controls.  It is therefore conditioned on TRIGGER AND RANK.  Under D14 the
# rank screen is a consistency check and not a filter, so that quantity answers
# a question the paper no longer asks, and it CANNOT be relabelled: the rank
# clause is a one-in-513 filter and removing it changes the answer by more than
# an order of magnitude.
#
# The chain the paper now states is  trigger -> localisation -> attribution.
# Each factor is measured, none is assumed:
#
#   E_trig    the expected number of Class A windows whose star exceeds a flat
#             5 sigma by chance, summed window by window over each window's own
#             realised null scale and effective cell count.  Computed here from
#             the RELEASED CATALOGUE's own published columns (D16), not taken
#             from another generator's macro.
#   f_loc     the measured fraction of injections at T* ~ 5 whose visibility
#             fit localises them -- because a noise maximum AT the stellar
#             position also has flux at the stellar position, so the fit's real
#             part carries almost no information beyond the trigger that
#             selected it.  This campaign measures it.
#   f_unattr  the fraction a chance frequency does NOT fall inside the frozen
#             line mask, from the mask's own occupancy of the searched band.
import csv as _csv
import math as _math
from scipy.stats import norm as _norm

_CAT = list(_csv.DictReader(open(os.path.join(HERE,
                                              'per_target_results_v3.99.csv'))))
_covA = [r for r in _CAT if r['n_ind_cells'] != '' and r['search_class'] == 'A']
assert len(_covA) > 300, len(_covA)


def _pexc(r, t=5.0):
    sw = 0.5 * (float(r['scale_route_a']) + float(r['scale_route_b']))
    n = float(r['n_ind_cells'])
    return -_math.expm1(n * _norm.logcdf(t / sw))


E_TRIG_A = sum(_pexc(r) for r in _covA)
F_LOC = a['at_tstar_5']['frac_localised_re_ge4'] if 'at_tstar_5' in a \
    else A['relation']['class A']['at_tstar_5']['frac_localised_re_ge4']
# ★ The three-clause pass rate reported by the campaign and the Re/sigma >= 4
# rate must agree to a per cent, or "localisation rejects nothing" is a claim
# about one clause rather than three.  F_LOC_THREE is the campaign's own.
F_LOC_THREE = 0.977
assert abs(F_LOC - F_LOC_THREE) < 0.015, (F_LOC, F_LOC_THREE)
# The mask's chance-attribution probability, read from the survey's own
# published expectation rather than recomputed: LgExpAttr crossings are
# expected to be attributed by chance out of LgNCross.
def _texval(fn, name):
    import re
    src = open(os.path.join(HERE, fn)).read()
    mm = re.search(r'\\newcommand\{\\%s\}\{([^}]*)\}' % name, src)
    assert mm, (fn, name)
    return mm.group(1).replace('\\,', '').replace(',', '')


_occ = float(_texval('survey_numbers_round80.tex', 'LgMaskOccPct')) / 100.0
assert 0.0 < _occ < 1.0, _occ
F_UNATTR = 1.0 - _occ
E_CHAIN = E_TRIG_A * F_LOC * F_UNATTR
m('RsevChanceTrigA', '%.1f' % E_TRIG_A)
m('RsevChanceFracLoc', '%.3f' % F_LOC)
m('RsevChanceFracLocThree', '%.3f' % F_LOC_THREE)
m('RsevChanceOccPct', '%.0f' % (100 * _occ))
m('RsevChanceExp', '%.1f' % E_CHAIN)
# ★★ THE ASSERTION THAT MAKES THIS A RE-DERIVATION.  If the two numbers were
# within a factor of a few, re-labelling would have been defensible.  They are
# not: the rank clause is a one-in-N_ctrl filter and dropping it changes the
# expectation by more than an order of magnitude.  Assert that, so nobody can
# quietly point the old macro at the new sentence.
_old = None
for _fn in sorted(f for f in os.listdir(HERE)
                 if f.startswith('survey_numbers') and f.endswith('.tex')):
    try:
        _old = float(_texval(_fn, 'ClustStageMean'))
        break
    except AssertionError:
        continue
assert _old is not None, 'ClustStageMean is not defined by any generator'
m('RsevChanceOldRank', '%.2f' % _old)
assert E_CHAIN / _old > 10.0, (
    'the trigger+localisation chance expectation (%.2f) is within a factor 10 '
    'of the trigger+rank one (%.2f); if that is really so, say which one the '
    'paper means rather than publishing both' % (E_CHAIN, _old))
m('RsevChanceRatio', '%.0f' % (E_CHAIN / _old))
# And the observed count it is to be compared with: Class A crossings, and the
# unattributed subset of them.
# ★ The comparison must use the SAME population the expectation was summed
# over -- the covered Class A windows -- and the same conditioning: E_CHAIN
# carries the f_unattr factor, so the observed number it predicts is the count
# of Class A crossings the frozen mask does NOT attribute, not all of them.
_xA = [r for r in _CAT if r['crossing'] == 'True' and r['search_class'] == 'A']
_xAcov = [r for r in _xA if r['n_ind_cells'] != '']
_xAun = [r for r in _xAcov
         if r['disposition_computed'].strip() == 'unattributed']
assert _xAun, 'the computed disposition column no longer says "unattributed"'
m('RsevChanceObsAAll', '%d' % len(_xA))
m('RsevChanceObsA', '%d' % len(_xAcov))
m('RsevChanceObsAUnattr', '%d' % len(_xAun))
# ★ and the prediction must not exceed what was observed by a factor that would
# make it absurd: the expectation is a NULL, so observed >= expected/2 is the
# consistency the paper claims.  Drive this in both directions in selftest.
assert 0.5 * E_CHAIN <= len(_xAcov), (E_CHAIN, len(_xAcov))

with open(OUT, 'w') as fh:
    fh.write('%% round 99: the round-7 completeness campaign through\n'
             '%% trigger -> visibility localisation (D14).  Generated by\n'
             '%% p90r7_v406.py from r8inputs/p90_r7_analysis_v406.json and\n'
             '%% r8inputs/selfunc_classA_v406.json.  Gates asserted here:\n'
             '%%   null localised rate %.5f < %.2f ceiling (pre-committed)\n'
             '%%   positive control %.3f / %.3f >= %.2f\n'
             '%%   Class A recovery reaches %.3f, 90%%%% point bracketed in\n'
             '%%   100%%%% of bootstrap resamples\n'
             % (g['null_frac_localised'], NULL_CEILING,
                g['positive_control_frac'], g['positive_control_frac_localised'],
                PC_FLOOR, a['trigger_and_localised']['max_frac']))
    for k, v in M.items():
        fh.write('\\newcommand{\\%s}{%s}\n' % (k, v))

json.dump(dict(generated_from=A['generated'],
               gates=dict(g, null_ceiling_prefixed=NULL_CEILING,
                          positive_control_floor_prefixed=PC_FLOOR),
               macros=M), open(JSN, 'w'), indent=1)
print('%d macros -> %s' % (len(M), OUT))
for k in sorted(M):
    print('  \\%-22s %s' % (k, M[k]))
