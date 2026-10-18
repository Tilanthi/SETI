#!/usr/bin/env python3
r"""Macros for the CP-72 2713 second-epoch (recurrence) test.

Input: `cp72_recurrence.json`, written by `cp72_verify.py` run read-only
on the processing host against the retained search products of both epochs,
`/data/SETI/targets/CP-72_2713_{B7,EB2}/products/*_{search,srcspec}.npz`.

The second execution block of MOUS uid://A001/X2d20/X2e25, A002_Xff0235_X502d,
was declined by the per-target download budget during the survey and was
calibrated and searched afterwards with the unmodified release pipeline in an
isolated target directory.  Its four windows are a targeted follow-up and are
not part of the survey: they do not enter the 431-window trials budget, the
102 searched blocks or the Bonferroni denominator.

`cp72_verify.py` reimplements the release statistic (4 per cent adaptive edge
trim, 65-channel frequency-median baseline, inverse-variance weighted
de-drifted stack).  It is gated on reproducing the published first-epoch
value, and does so to a relative error of 2e-8, which is why the matched-drift
fluxes below can be quoted as pipeline quantities.

`\CpRecEb` and `\CpRecGB` are deliberately absent: the manuscript uses
`\CpEbUnsearched` and `\CpEbUnsearchedGB` from round 14 for the same two
quantities, and a second definition of a value already carried by a macro is
the double-definition trap closed in v3.42.
"""
import json

R = json.load(open('cp72_recurrence.json'))

G, FQ, MT, ZD, NB = R['gate'], R['freq'], R['matched'], R['zero_drift'], R['neighbours_e2']
WM, DP, EX, TM, SW = R['windowmax'], R['depth'], R['exclusion'], R['times'], R['sweep']

# The comparison is only clean because the configuration matches.  These are
# the assertions that would have caught a mismatched pair of products.
assert G['chan'] == 35 and abs(G['rel_err']) < 1e-6, 'first-epoch gate failed'
assert abs(FQ['chanw_Hz'] - 488281.25) < 1e-6, 'channel width mismatch'
assert abs(FQ['offset_chan']) < 0.25, 'the feature does not fall in one channel'

# Both epoch labels are the same UT date, which is why the text says so.
assert TM['e1']['start'][:10] == TM['e2']['start'][:10], 'not the same night'


def hm(iso):
    return iso[11:16]


M = [
    # configuration match
    ('CpRecNInt',      '495'),
    ('CpRecChanwkHz',  '488.28'),
    ('CpRecChan',      '%d' % G['chan']),
    ('CpRecOffkHz',    '%.1f' % abs(FQ['offset_kHz'])),
    ('CpRecOffChan',   '%.2f' % abs(FQ['offset_chan'])),
    # epochs
    ('CpRecDate',      '2022 October 2'),
    ('CpRecUTone',     hm(TM['e1']['start'])),
    ('CpRecUTtwo',     hm(TM['e2']['start'])),
    ('CpRecGapMin',    '%d' % round(TM['gap_min'])),
    ('CpRecStartSep',  '%.1f' % TM['start_to_start_h']),
    # depth
    ('CpRecRmsOne',    '%.3f' % DP['rms1_mJy']),
    ('CpRecRmsTwo',    '%.3f' % DP['rms2_mJy']),
    ('CpRecDeeperPct', '%.1f' % DP['pct_lower_rms']),
    ('CpRecSminTwo',   '%.2f' % DP['S_min2_mJy']),
    ('CpRecExpT',      '%.2f' % DP['expected_T2_if_persistent']),
    # the drift-maximised statistic (what the pipeline reports)
    ('CpRecT',         '%.2f' % R['e2_drift_max_at_ch35']['T']),
    ('CpRecCtrlMed',   '%.2f' % WM['e2']['ctrl_med']),
    ('CpRecCtrlMax',   '%.2f' % WM['e2']['ctrl_max']),
    ('CpRecWinPeak',   '%.2f' % WM['e2']['star_window_max']),
    ('CpRecWinPeakGHz', '%.4f' % 344.7648),
    ('CpRecHits',      '0'),
    ('CpRecCtrlMedOne', '%.2f' % WM['e1']['ctrl_med']),
    ('CpRecCtrlMaxOne', '%.2f' % WM['e1']['ctrl_max']),
    ('CpRecHitsOne',   '2'),
    ('CpRecRank',      '%d' % WM['e2']['rank']),
    ('CpRecRankOf',    '%d' % WM['e2']['of']),
    ('CpRecRankP',     '%.2f' % WM['e2']['add_one_p']),
    # like-for-like at a single channel
    ('CpRecNbrMean',   '%.2f' % NB['mean']),
    ('CpRecNbrSd',     '%.2f' % NB['sd']),
    ('CpRecNbrSig',    '%.1f' % NB['z_of_star']),
    # the matched-drift measurement
    ('CpRecDriftkHzs', '%.2f' % (SW['drift_Hz_s'] / 1e3)),
    ('CpRecSweepMHz',  '%.2f' % SW['sweep_MHz']),
    ('CpRecSweepChan', '%.1f' % SW['sweep_chan']),
    ('CpRecAccel',     '%.2f' % SW['accel_m_s2']),
    ('CpRecFluxOne',   '%.1f' % EX['flux1_mJy']),
    ('CpRecErrOne',    '%.1f' % EX['flux1_err_mJy']),
    ('CpRecFluxTwo',   '%.1f' % EX['flux2_mJy']),
    ('CpRecErrTwo',    '%.1f' % EX['flux2_err_mJy']),
    ('CpRecSigTwo',    '%.1f' % MT['T']),
    ('CpRecExclCond',  '%.1f' % EX['conditional_sigma']),
    ('CpRecExclPair',  '%.1f' % EX['two_sample_sigma']),
    ('CpRecExclDmax',  '%.1f' % EX['drift_max_sigma']),
    ('CpRecNodeChan',  '%.2f' % abs(MT['node_offset_Hz_s'] * 3716.35 / 488281.25)),
    # epoch 1 at zero drift: no stationary line can make this feature
    ('CpRecZeroSig',   '%.2f' % ZD['e1']['T']),
    # the block's other three windows
    ('CpRecOthA',      '%.2f' % R['other_windows_e2'][0]['star_peak']),
    ('CpRecOthB',      '%.2f' % R['other_windows_e2'][1]['star_peak']),
    ('CpRecOthC',      '%.2f' % R['other_windows_e2'][2]['star_peak']),
]

with open('survey_numbers_recurrence.tex', 'w') as f:
    f.write('%% GENERATED by recurrence_calc.py -- do not hand-edit.\n')
    for k, v in M:
        f.write('\\newcommand{\\%s}{%s}\n' % (k, v))

print('first-epoch gate: reimplemented %.9f vs published %.9f (rel %.1e)'
      % (G['reimplemented_T'], G['published_T'], G['rel_err']))
print('matched channel %d and drift %.1f Hz/s: epoch 2 gives %+.2f +/- %.2f mJy '
      '(%.2f sigma) against %+.2f +/- %.2f mJy in epoch 1'
      % (G['chan'], SW['drift_Hz_s'], EX['flux2_mJy'], EX['flux2_err_mJy'],
         MT['T'], EX['flux1_mJy'], EX['flux1_err_mJy']))
print('  persistent constant-flux emitter disfavoured at %.1f sigma (pair) / '
      '%.1f sigma (conditioned on epoch 1); drift-maximised only %.1f sigma'
      % (EX['two_sample_sigma'], EX['conditional_sigma'], EX['drift_max_sigma']))
print('  epoch 2 is %.1f per cent deeper; a repeat would have given T* = %.2f'
      % (DP['pct_lower_rms'], DP['expected_T2_if_persistent']))
print('  control maximum %.2f exceeds the %.2f that raised the flag'
      % (WM['e2']['ctrl_max'], WM['e1']['star_window_max']))
print('macros -> survey_numbers_recurrence.tex')
