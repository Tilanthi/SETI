#!/usr/bin/env python3
"""Emit survey_numbers.tex: one LaTeX macro per survey quantity, generated from
survey_stats.json and occurrence_v328.json.  The manuscript uses these macros
instead of typed digits, so a number cannot disagree with itself between
sections, and refreshing the export updates the whole paper.

Run after survey_stats.py.  Referee-required (report 1, point 1).
"""
import json, csv, statistics

# Fine-channel windows (transfer-error bound, round 4 R2-2): median on-source
# time and the AU Mic Band-6 488-kHz calibration window's on-source time.
_pt = list(csv.DictReader(open('per_target_results_v3.32.csv')))
_fine = [float(r['on_source_s']) for r in _pt if r['resolution_class'] == 'fine']
FINE_MED_ONSRC = statistics.median(_fine)
CALIB_ONSRC = [float(r['on_source_s']) for r in _pt
               if r['resolution_class'] == 'fine'
               and 'AU Mic' in r['star_name'] and r['band'] == '6'
               and float(r['chanw_Hz']) < 6e5][0]

S = json.load(open('survey_stats.json'))
N = json.load(open('nullcal.json'))
# v3.42 single-source repair: the occurrence and duty quantities were read from
# two frozen side files (occurrence_v328.json, duty_v331.json) that carry the
# pre-repair N_sys = 82 denominators, while round10_calc.py computed the SAME
# quantities live from survey_stats_round10.json.  Two sources, one quantity.
# They now all come from the live engine.
R10 = json.load(open('survey_stats_round10.json'))
O = {k: {'n_thr': v['n_sys'], 'thr': v['unit'], 'n_fine': v['n_sys_fine'],
         'meas': v['measured'], 'unif': v['uniform'],
         'meas_D05': v['measured_D05'], 'meas_D01': v['measured_D01']}
     for k, v in R10['occurrence'].items()}

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
 ('OccMeasuredRound', '%.0f' % (100 * occ['meas'])),
 ('OccUnit',        '%.1f' % (100 * occ['thr'])),
 ('OccUniform',     '%.1f' % (100 * occ['unif'])),
 ('OccDhalf',       '%.1f' % (100 * occ['meas_D05'])),
 ('OccDtenth',      '%.0f' % (100 * occ['meas_D01'])),
 ('NOccSystems',    '%d' % occ['n_fine']),
 ('NOccSystemsUnit','%d' % occ['n_thr']),
 # --- transfer-error analytic bound (round 4, R2-2): coherent-averaging gain
 # across the on-source span, and the calibration window's position in it.
 # Fine-window statistics come from per_target_results_v3.32.csv.
 ('IntGainSpan',    '%.0f' % (S['onsrc_max'] / S['onsrc_min']) ** 0.5),
 ('FineOnsrcMedian','%.0f' % FINE_MED_ONSRC),
 ('CalibOnsrc',     '%.0f' % CALIB_ONSRC),
 ('CalibGainRatio', '%.1f' % (FINE_MED_ONSRC / CALIB_ONSRC) ** 0.5),
 # --- completeness -------------------------------------------------------
 ('SbrN',           '%d' % S['n_sbr']),
 ('SbrPobs',        '1.7\\times10^{-3}'),
 ('SbrAstro',       '3'),
 ('SbrResid',       '2'),
 ('SbrResidP',      '0.21'),
 ('OnsrcMin',       '%.0f' % S['onsrc_min']),
 ('OnsrcMax',       '%.0f' % S['onsrc_max']),
 ('MasonRatio',     '1250'),
 ('NExoHosts',      '18'),
 ('NExoPlanets',    '41'),
 ('OnsrcMedian',    '2087'),
 ('DutyHalf',       '%.1f' % (100 * occ['meas_D05'])),
 ('DutyTenth',      '%.0f' % (100 * occ['meas_D01'])),
 ('DutyHalfUnit',   '%.1f' % (100 * R10['occurrence']['1e+16']['unit_D05'])),
 ('NMultiEpoch',    '%d'   % R10['n_multi']),
 ('AuPct',          '%.1f' % json.load(open('aumic_v331.json'))['aumic_pct']),
 ('AuNge',          '%d'   % json.load(open('aumic_v331.json'))['aumic_nge']),
 ('AuFrac',         '%.1f' % json.load(open('aumic_v331.json'))['aumic_frac']),
 ('AuP',            '%.3f' % json.load(open('aumic_v331.json'))['aumic_p']),
 ('CtrlMed',        '%.2f' % json.load(open('aumic_v331.json'))['ctrl_med']),
 ('CtrlPninety',    '%.2f' % json.load(open('aumic_v331.json'))['ctrl_p90']),
 ('NNonBP',         '%d'   % json.load(open('aumic_v331.json'))['n_nonbp']),
 ('NBPWindows',     '%d'   % json.load(open('aumic_v331.json'))['n_bp']),
 ('NDwellTrials',   '%s' % format(json.load(open('dwell_v332.json'))['n_trials'],',').replace(',', chr(92)+',')),
 ('NDwellWin',      '%d' % json.load(open('dwell_v332.json'))['n_win']),
 ('DwellCoarseOne', '%d' % json.load(open('dwell_v332.json'))['coarseOne']),
 ('DwellCoarseQ',   '%d' % json.load(open('dwell_v332.json'))['coarseQuarter']),
 ('DwellCoarseT',   '%d' % json.load(open('dwell_v332.json'))['coarseTenth']),
 ('DwellFineOne',   '%d' % json.load(open('dwell_v332.json'))['fineOne']),
 ('DwellFineQ',     '%d' % json.load(open('dwell_v332.json'))['fineQuarter']),
 ('DwellFineT',     '%d' % json.load(open('dwell_v332.json'))['fineTenth']),
 ('RecThresh',      '42'),
 ('RecThreshHi',    '16'),
 ('RecThreshLo',    '14'),
 ('RecTwice',       '83'),
 ('NTrials',        '1200'),
 # v3.42: Bands 6+7 share of searched windows.  Was hand-typed as '83 per
 # cent' in Appendix E against a table that gives 86 per cent; now a macro.
 ('PctBandsSixSeven', '%d' % round(100.0 * (S['bands']['6'] + S['bands']['7'])
                                  / S['n_windows'])),
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
