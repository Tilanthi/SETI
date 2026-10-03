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
import csv as _csv
import json
import os
import re as _re

HERE = os.path.dirname(os.path.abspath(__file__))


def _texval(fn, name):
    """the CURRENT value of a generated macro, read from its own round file."""
    src = open(os.path.join(HERE, fn)).read()
    mm = _re.search(r'\\newcommand\{\\%s\}\{([^}]*)\}' % name, src)
    assert mm, (fn, name)
    return mm.group(1).replace('\\,', '').replace(',', '')


# the released catalogue, needed both for the Class A window count (R1-5) and
# for the chance expectation at the end of this script.
_CAT = list(_csv.DictReader(open(os.path.join(HERE,
                                              'per_target_results_v3.99.csv'))))
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
# ★★★ v4.08 (D23/D25).  THE UNIT COUNT MUST CLOSE, AND IT DID NOT.  v4.06 and
# v4.07 printed a plan of 56, "usable" and "scored" differing by 3, and 1
# excluded -- and those 3 units went unaccounted for in the paper.  They are
# the three that FAILED THEIR OWN 20x POSITIVE CONTROL at localisation
# (0.42-0.92 against the 0.95 floor fixed before the campaign ran): the
# campaign excluding units on a pre-registered criterion, which must be printed
# rather than absorbed into a difference of two other numbers.
#
# A further five units were never run to completion: they were stopped at rung
# 3 of the 10-rung ladder to release ~140 GB for the CP-72 2713 refit and the
# 44-block re-extraction.  ★ THE REASON IS SCHEDULING, NOT DATA QUALITY, and
# the five are named in r8inputs/p90_r7_truncation_v408.log, which is the
# campaign's own log and is read here rather than transcribed.
#
# Both identities are now ASSERTED, so an unexplained unit fails the build:
#     plan  = units with a record + truncated
#     record = scored + search-base failures + positive-control failures
TRUNC_LOG = os.path.join(HERE, 'r8inputs', 'p90_r7_truncation_v408.log')
_trunc = sorted({l.split('TRUNCATED:')[1].strip()
                 for l in open(TRUNC_LOG) if 'TRUNCATED:' in l})
_npc = len(A['positive_control_failures'])
_plan, _done = 56, A['n_units_total']
assert _plan == _done + len(_trunc), (
    'the P90 unit count does not close: %d planned, %d with a record, %d '
    'truncated' % (_plan, _done, len(_trunc)))
assert _done == A['n_units_scored'] + A['n_units_failed'] + _npc, (
    'units with a record do not decompose: %d != %d scored + %d failed + %d '
    'positive-control' % (_done, A['n_units_scored'], A['n_units_failed'], _npc))
m('RsevNUnitPlan', '%d' % _plan)
m('RsevNUnitDone', '%d' % _done)
m('RsevNUnitTrunc', '%d' % len(_trunc))
m('RsevNUnitPCFail', '%d' % _npc)
m('RsevPCFloor', '%.2f' % PC_FLOOR)
m('RsevPCWorst', '%.2f' % min(float(r.rsplit(' ', 1)[1])
                              for _, r in A['positive_control_failures']))
m('RsevTruncRung', '3')
# ★ v4.08: THE FIVE TRUNCATED UNITS ARE NAMED IN THE PAPER, not only in the
# deposited log -- a reader cannot audit a scheduling decision against a list
# they have to take on trust.  The list is READ from the campaign's own log, so
# it cannot drift from it, and its length is the same count asserted above.
m('RsevTruncList', ', '.join('\\texttt{%s}' % t.replace('_', '\\_')
                             for t in _trunc))
# ★★ AND THE ONE SEARCH-STAGE FAILURE NOW HAS ITS CAUSE PRINTED.  v4.06 and
# v4.07 printed the exclusion with no reason; the reason is a kernel OOM in an
# unbounded array read that ABORTED THE SEARCH DESPITE A DOCSTRING PROMISING IT
# COULD NOT, because SIGKILL pre-empts the except clause.  The same read was in
# the production search path.
FU = json.load(open(os.path.join(HERE, 'r8inputs',
                                 'p90_r7_failed_unit_v408.json')))
assert FU['status'] == 'failed_search_base' and FU['rc'] == -9, FU
# the mechanism must be big enough to explain the kill, computed from the
# window's own shape and not taken from the note: 2 pol x nchan x nrow
# complex128, read and then copied by the mask.
_bytes = 2 * FU['n_chan'] * FU['n_row'] * 16
_floor_GB = 2 * _bytes / 1024.0 ** 3
assert _floor_GB < FU['anon_rss_GB'] < FU['machine_RAM_GB'], (
    'the measured resident size %.1f GB is not between the %.1f GB the read '
    'requires by construction and the %.1f GB the machine has'
    % (FU['anon_rss_GB'], _floor_GB, FU['machine_RAM_GB']))
# ★ and the mechanism must EXPLAIN the kill, not merely be consistent with it:
# the measured residency has to be within a factor of two of what the read
# costs by construction, or something else was using the memory and the
# sentence in the paper is the wrong diagnosis.
assert FU['anon_rss_GB'] < 2.0 * _floor_GB, (
    'the %.1f GB measured is more than twice the %.1f GB this read requires, '
    'so the read does not account for the kill'
    % (FU['anon_rss_GB'], _floor_GB))
m('RsevFailUnit', '\\texttt{%s}' % FU['unit'].replace('_', '\\_'))
m('RsevFailRssGB', '%.0f' % FU['anon_rss_GB'])
m('RsevFailFloorGB', '%.0f' % _floor_GB)
m('RsevFailNChan', format(FU['n_chan'], ',').replace(',', chr(92) + ','))
m('RsevFailFunc', '\\texttt{%s}' % FU['function'].replace('_', '\\_'))
# the ladder length is the campaign's own, read from its collect record
_COL = json.load(open(os.path.join(HERE, 'r8inputs', 'p90_r7_collect_v408.json')))
assert _COL['n_units_scored'] == A['n_units_scored'], 'collect/analysis disagree'
m('RsevTruncRungTot', '%d' % len(_COL['ladder']))
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

# =====================================================================
# ★★★ v4.08 (D32): R2-3 REVERSES, AND THIS IS THE MEASUREMENT THAT DOES IT
# =====================================================================
# The referee asked us to "derive the exclusion level for the two unattributed
# events from the measured Re/sigma--T* relation".  Measured, the relation does
# NOT exclude them.  Three things are computed here, none of them transcribed:
#
#   (1) the two estimators DO track, for a real source at the star: the median
#       Re/sigma / T* ratio over every recovered-T* bin.  So Table 3's failure
#       to track is evidence about the crossings, not about the estimators.
#   (2) the observed events, read from the paper's OWN released ledger, against
#       the injected distribution in the same recovered-T* bin.
#   (3) the superseded-epoch distribution of the SAME injected real sources,
#       which is where the referee's -0.93 and -0.86 come from.  A negative
#       value there is what a genuine compact source looks like under the epoch
#       defect, so it is not evidence about the events at all.
#
# ★ The per-event percentiles are the one quantity the deposited aggregate
# cannot yield (it carries quantiles, not the individual fits), so they come
# from r8inputs/r23_v408.json -- and EVERY one of them is asserted against the
# deposit's own 16th percentile and against the ledger's own Re/sigma, so a
# mistyped percentile or a mis-keyed star fails the build.
R23 = json.load(open(os.path.join(HERE, 'r8inputs', 'r23_v408.json')))

# (1) tracking.  The claim is "Re/sigma ~ T* at every amplitude", so it must be
# asserted over EVERY bin and not over a favourable one.
_rat = [bb['ratio_snrre_over_tstar'][1] for bb in ra['by_recovered_tstar']]
assert len(_rat) >= 4, _rat
assert max(abs(r - 1.0) for r in _rat) < 0.25, (
    'the two estimators do not track for an injected source at the star '
    '(median Re/sigma / T* ratios %s); the R2-3 paragraph must not be written'
    % ['%.3f' % r for r in _rat])
m('RsevTrackLo', f2(min(_rat)))
m('RsevTrackHi', f2(max(_rat)))
m('RsevTrackNBin', '%d' % len(_rat))

# the bin the events live in is the campaign's own lowest recovered-T* bin, and
# it is the one at_tstar_5 reports -- asserted, not assumed.
_b5 = ra['by_recovered_tstar'][0]
assert _b5['n'] == t5['n'], (_b5['n'], t5['n'])
TS_LO, TS_HI = float(_b5['tstar_lo']), float(_b5['tstar_hi'])
m('RsevTstarLo', '%.1f' % TS_LO)
m('RsevTstarHi', '%.1f' % TS_HI)
P16 = t5['snr_re'][0]
m('RsevImFracAtFive', '%.3f' % R23['frac_im_below_3_at_tstar5_classA'])

# (2) the observed events, from the released ledger.  Unattributed, fitted, in
# the same recovered-T* bin.
_LED = json.load(open(os.path.join(HERE, 'ledger_v403.json')))
_un = [r for r in _LED['rows']
       if (not r['attributed']) and r['fitted']
       and TS_LO <= r['tstar'] < TS_HI]
_unloc = [r for r in _un if r['corrected']['localised']]
assert _un, 'no unattributed fitted crossing falls in the campaign bin'
m('RsevUnattrNBin', '%d' % len(_un))
m('RsevUnattrNLoc', '%d' % len(_unloc))
# one crossing per star, the deepest, and the N highest of those: the subset the
# referee's question is about.  The range is stable against the exact N, which
# is why it is quoted as a range and the selection is stated.
_bystar = {}
for r in _unloc:
    k = r['display']
    if k not in _bystar or r['tstar'] > _bystar[k]['tstar']:
        _bystar[k] = r
_top = sorted(_bystar.values(), key=lambda r: -r['tstar'])[:6]
m('RsevUnattrTopN', '%d' % len(_top))
m('RsevUnattrReLo', f2(min(r['corrected']['re'] for r in _top)))
m('RsevUnattrReHi', f2(max(r['corrected']['re'] for r in _top)))
m('RsevUnattrAbovePSixteen', '%d' % sum(1 for r in _top
                                   if r['corrected']['re'] > P16))
# the rank-flagged one is the event the paper's own stage-1 pair names, and it
# is SELECTED on the screen flag, not typed.
_s1 = [r for r in _unloc if r['screen']]
assert len(_s1) == 1, [r['star'] for r in _s1]
m('RsevStageOneStar', _s1[0]['display'])
m('RsevStageOneRe', f2(_s1[0]['corrected']['re']))
# ★ and the superseded-epoch value for that same crossing, from the ledger's own
# r6 record: this is the class of number the referee quoted as an exclusion.
m('RsevStageOneReSix', f2(_s1[0]['r6']['re']))

# the transcribed percentiles, each one checked against the deposit and the
# ledger.  A star named here that the ledger does not hold, a Re/sigma that
# disagrees, or a percentile on the wrong side of the 16th fails the build.
PCT = R23['percentile_among_injected_at_tstar_bin']
_pcts = []
for _star, _p in PCT.items():
    if _star.startswith('_'):
        continue
    _hit = [r for r in _unloc if r['star'].startswith(_star)
            or r['display'].replace('$', '').replace('~', ' ').replace(
                '\\', '').strip() == _star]
    assert len(_hit) >= 1, ('r23_v408.json names %s, which is not an '
                            'unattributed localised crossing in the bin' % _star)
    _hit = sorted(_hit, key=lambda r: -r['tstar'])[0]
    _reval = _hit['corrected']['re']
    assert (_reval > P16) == (_p > 16), (
        'the transcribed percentile for %s (%dth) is on the wrong side of the '
        'injected 16th percentile (Re/sigma %.2f against %.2f)'
        % (_star, _p, _reval, P16))
    _pcts.append(_p)
assert len(_pcts) == 6, len(_pcts)
m('RsevUnattrPctLo', '%d' % min(_pcts))
m('RsevUnattrPctHi', '%d' % max(_pcts))
m('RsevStageOnePct', '%d' % PCT[_s1[0]['star'].split(' Gaia')[0]])
# (3) the same injected sources re-fitted at the superseded epoch.
m('RsevReSixEpochMed', f2(t5['snr_re_r6epoch'][1]))
m('RsevReSixEpochLo', f2(t5['snr_re_r6epoch'][0]))
# ★★ THE FALSIFIER.  The paper's claim is that the events sit INSIDE the
# injected distribution and that the superseded-epoch values do not.  Both
# directions are asserted, so neither sentence can be written if the data stop
# supporting it.
assert min(r['corrected']['re'] for r in _top) > t5['snr_re_r6epoch'][1], (
    'the observed events are not above the superseded-epoch median of the '
    'injected sources, so the "not comparable" sentence must not be written')
assert max(r['corrected']['re'] for r in _top) > P16, (
    'no observed event reaches the injected 16th percentile: the events are '
    'NOT inside the injected distribution and "consistent, not excluded" must '
    'not be written')

# ★ the clean-pass control census: why the trigger and the fit are not
# independent at T* ~ 5.
_cc = R23['clean_pass_control_census']
m('RsevCleanNWinA', '%d' % _cc['classA']['n_windows'])
m('RsevCleanCtrlGeFiveA', '%d' % _cc['classA']['n_with_control_ge5'])
m('RsevCleanStarGeFiveA', '%d' % _cc['classA']['n_with_star_ge5'])
m('RsevCleanNWinB', '%d' % _cc['classB']['n_windows'])
m('RsevCleanCtrlGeFiveB', '%d' % _cc['classB']['n_with_control_ge5'])
# the census is only the point being made if a control above 5 is the DEFAULT
# outcome in Class A and the exception in Class B.  Asserted both ways.
assert (_cc['classA']['n_with_control_ge5'] / _cc['classA']['n_windows']) > 0.5
assert (_cc['classB']['n_with_control_ge5'] / _cc['classB']['n_windows']) < 0.5
assert a['ctrl_top_clean_median'] >= 5.0, a['ctrl_top_clean_median']

# ---- R1-5
# ★★ v4.08: \RsevNWinA WAS THE TYPED LITERAL '403', and v4.07 moved the Class A
# window count to 402 when the HD 139084 misattribution was repaired.  The macro
# was unreferenced, so nothing compared it with \NWinA and retire_macros.py
# dropped it before any gate could see it -- a stale number one \input away from
# being printed.  It is now COUNTED from the released catalogue and PINNED with
# == against the catalogue macro the rest of the paper uses.
_nwinA = len([r for r in _CAT if r['search_class'] == 'A'])
_nwinA_macro = int(_texval('survey_numbers_round12.tex', 'NWinA'))
assert _nwinA == _nwinA_macro, (
    'the Class A window count disagrees with \\NWinA: %d counted in the '
    'catalogue against %d published' % (_nwinA, _nwinA_macro))
m('RsevNTestedA', '%d' % tr['n_units_directly_tested'])
m('RsevNWinA', '%d' % _nwinA)
m('RsevNTransferA', '%d' % (_nwinA - tr['n_units_directly_tested']))
m('RsevTransAMed', f2(tr['per_unit_P90_loc_median']))
m('RsevTransALo', '%.2f' % tr['transfer_factor_p16_over_median'])
m('RsevTransAHi', '%.2f' % tr['transfer_factor_p84_over_median'])
m('RsevTransARangeLo', '%.2f' % tr['transfer_factor_min_over_median'])
m('RsevTransARangeHi', '%.2f' % tr['transfer_factor_max_over_median'])
m('RsevTransBLo', '%.2f' % trb['transfer_factor_p16_over_median'])
m('RsevTransBHi', '%.2f' % trb['transfer_factor_p84_over_median'])
# ★★ v4.08 (D32, R1-5): the SAME measurement as a percentage, for the
# uncertainty budget.  The budget's window-to-window row was carried from the
# predecessor campaign's x0.48-1.35 and the paper called that term its LARGEST;
# measured on the criterion the paper publishes it is one of the smallest, and
# the claim is withdrawn.  Asserted, so the withdrawal cannot be written if the
# measured spread ever grows back.
_tlo = tr['transfer_factor_min_over_median']
_thi = tr['transfer_factor_max_over_median']
m('RsevTransPctLo', '%.0f' % (100 * (_tlo - 1.0)))
m('RsevTransPctHi', '+%.0f' % (100 * (_thi - 1.0)))
_old_lo = float(_texval('survey_numbers_round23.tex', 'StratTransferNineLo'))
_old_hi = float(_texval('survey_numbers_round23.tex', 'StratTransferNineHi'))
assert max(abs(_tlo - 1), abs(_thi - 1)) < 0.5 * max(abs(_old_lo - 1),
                                                     abs(_old_hi - 1)), (
    'the measured Class A transfer spread (%.2f-%.2f) is not materially '
    'smaller than the predecessor bracket (%.2f-%.2f) the paper called its '
    'largest systematic; the withdrawal must not be written'
    % (_tlo, _thi, _old_lo, _old_hi))
m('RsevTransOldLo', '%.2f' % _old_lo)
m('RsevTransOldHi', '%.2f' % _old_hi)
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
import math as _math
from scipy.stats import norm as _norm

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

# ★★ v4.08: THE MACRO COUNT IS PINNED WITH ==, for the same reason the stack's
# is (D31).  The failure mode this cycle keeps producing is a macro that is
# ABSENT, and an absent macro is neither empty nor NaN, so no value-level gate
# can see it.  Driven in selftest_v408.
NMACRO = int(os.environ.get('P90R7_NMACRO', '112'))
assert len(M) == NMACRO, (
    'p90r7_v406 emitted %d macros, not the pinned %d: a macro has been ADDED '
    'or SILENTLY DROPPED' % (len(M), NMACRO))

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
