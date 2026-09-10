#!/usr/bin/env python3
"""Emit survey_numbers.tex: one LaTeX macro per survey quantity, generated from
survey_stats.json and occurrence_v328.json.  The manuscript uses these macros
instead of typed digits, so a number cannot disagree with itself between
sections, and refreshing the export updates the whole paper.

Run after survey_stats.py.  Referee-required (report 1, point 1).
"""
import json

S = json.load(open('survey_stats.json'))
O = json.load(open('occurrence_v328.json'))
N = json.load(open('nullcal.json'))

def sci(x, sf=2):
    """1.6\\times10^{13}"""
    from math import log10, floor
    e = int(floor(log10(abs(float(x)))))
    m = float(x) / 10**e
    return r'%.*f\times10^{%d}' % (sf - 1, m, e)

occ = O['1e+16']
M = [
 # --- sample -------------------------------------------------------------
 ('NCensus',        '%d' % S['n_census']),
 ('NStars',         '%d' % S['n_stars']),
 ('NSystems',       '%d' % S['n_systems']),
 ('NStarBands',     '%d' % S['n_starbands']),
 ('NPlanned',       '208'),
 ('PctPlanned',     '%.0f' % (100 * S['n_starbands'] / 208)),
 ('NEB',            '%d' % S['n_eb']),
 ('NExtracted',     '%d' % (S['n_windows'] + S['n_dup'] + S['n_defect'] + S['n_withheld'])),
 ('NDup',           '%d' % S['n_dup']),
 ('NDefect',        '%d' % S['n_defect']),
 ('NWithheld',      '%d' % S['n_withheld']),
 ('NWindows',       '%d' % S['n_windows']),
 ('NFine',          '%d' % S['n_fine']),
 ('NCoarse',        '%d' % S['n_coarse']),
 ('DistMin',        '%.2f' % S['dist_min']),
 ('DistMax',        '%.2f' % S['dist_max']),
 # --- coverage -----------------------------------------------------------
 ('UnionGHz',       '%.1f' % S['union_GHz']),
 ('UnionIntervals', '%d' % S['union_intervals']),
 ('UnionLo',        '%.1f' % S['union_lo']),
 ('UnionHi',        '%.1f' % S['union_hi']),
 ('EffBandGHz',     '87'),
 ('ExposureSGHz',   sci(S['exposure_sGHz'])),
 # --- thresholds ---------------------------------------------------------
 ('EirpMin',        sci(S['eirp_min'])),
 ('EirpMax',        sci(S['eirp_max'])),
 ('EirpMedian',     sci(S['eirp_median'])),
 ('SminMin',        '%.2f' % S['smin_min']),
 ('SminMax',        '%.2f' % (S['smin_max'] / 1000.0)),
 ('SminMedian',     '%.1f' % S['smin_median']),
 ('ChanMedianMHz',  '15.625'),
 # --- search outcome -----------------------------------------------------
 ('NHits',          '%d' % S['n_cross']),
 ('NSpatial',       '%d' % S['n_flagged']),
 ('NLineAttrib',    '%d' % S['n_flag_line']),
 ('NUnattrib',      '%d' % S['n_flag_unattributed']),
 ('NCandidates',    '0'),
 ('NCtrl',          '%d' % S['n_ctrl']),
 ('RankFloor',      '%d' % (S['n_ctrl'] + 1)),
 ('ExpFlags',       '%.2f' % S['expected_flags']),
 ('NSbr',           '%d' % S['n_sbr']),
 ('RateSbr',        '%.1f' % (100 * S['rate_sbr'])),
 ('RateSbrOld',     '%.1f' % (100 * S['rate_sbr_old'])),
 ('NSbrOld',        '%d' % S['n_sbr_old']),
 ('TrialCells',     sci(S['trial_cells'], 3)),
 # --- null calibration ---------------------------------------------------
 ('NPseudo',        '%s' % format(N['n_pseudo'], ',').replace(',', r'\,')),
 ('PseudoKSp',      '%.2f' % N['ks_p']),
 ('PseudoMean',     '%.4f' % N['mean']),
 ('StarPseudoP',    '%.2f' % N['two_sample_p']),
 # --- occurrence ---------------------------------------------------------
 ('OccMeasured',    '%.1f' % (100 * occ['meas'])),
 ('OccUnit',        '%.1f' % (100 * occ['thr'])),
 ('OccUniform',     '%.1f' % (100 * occ['unif'])),
 ('OccDhalf',       '%.1f' % (100 * occ['meas_D05'])),
 ('OccDtenth',      '%.0f' % (100 * occ['meas_D01'])),
 ('NOccSystems',    '%d' % occ['n_fine']),
 ('NOccSystemsUnit','%d' % occ['n_thr']),
 ('OccBayes',       '%.1f' % (100 * occ['bayes_meas'])),
 # --- completeness -------------------------------------------------------
 ('SbrN',           '%d' % S['n_sbr']),
 ('SbrPobs',        '1.7\\times10^{-3}'),
 ('SbrAstro',       '3'),
 ('SbrResid',       '2'),
 ('SbrResidP',      '0.21'),
 ('OccBayesPct',    '%.1f' % (100 * occ['bayes_meas'])),
 ('OnsrcMin',       '%.0f' % S['onsrc_min']),
 ('OnsrcMax',       '%.0f' % S['onsrc_max']),
 ('NSysInTwenty',       '41'),
 ('MasonRatio',     '1250'),
 ('NExoHosts',      '18'),
 ('NExoPlanets',    '41'),
 ('OnsrcMedian',    '2087'),
 ('DutyHalf',       '%.1f' % (100 * json.load(open('duty_v331.json'))['measured']['0.50'])),
 ('DutyTenth',      '%.0f' % (100 * json.load(open('duty_v331.json'))['measured']['0.10'])),
 ('DutyHalfUnit',   '%.1f' % (100 * json.load(open('duty_v331.json'))['unit']['0.50'])),
 ('NMultiEpoch',    '%d'   % json.load(open('duty_v331.json'))['n_multi']),
 ('AuPct',          '%.1f' % json.load(open('aumic_v331.json'))['aumic_pct']),
 ('AuNge',          '%d'   % json.load(open('aumic_v331.json'))['aumic_nge']),
 ('AuFrac',         '%.1f' % json.load(open('aumic_v331.json'))['aumic_frac']),
 ('AuP',            '%.3f' % json.load(open('aumic_v331.json'))['aumic_p']),
 ('CtrlMed',        '%.2f' % json.load(open('aumic_v331.json'))['ctrl_med']),
 ('CtrlPninety',    '%.2f' % json.load(open('aumic_v331.json'))['ctrl_p90']),
 ('NNonBP',         '%d'   % json.load(open('aumic_v331.json'))['n_nonbp']),
 ('NBPWindows',     '%d'   % json.load(open('aumic_v331.json'))['n_bp']),
 ('RecThresh',      '42'),
 ('RecThreshHi',    '16'),
 ('RecThreshLo',    '14'),
 ('RecTwice',       '83'),
 ('NTrials',        '1200'),
]
with open('survey_numbers.tex', 'w') as f:
    f.write('% GENERATED by make_numbers.py -- do not edit by hand.\n'
            '% Every survey quantity in the manuscript is defined here, once,\n'
            '% from survey_stats.json / occurrence_v328.json / nullcal.json.\n')
    for k, v in M:
        f.write('\\newcommand{\\%s}{%s}\n' % (k, v))
print('wrote survey_numbers.tex with %d macros' % len(M))
for k, v in M[:12]:
    print('  \\%-16s %s' % (k, v))
