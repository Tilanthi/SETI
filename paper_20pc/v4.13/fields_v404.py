#!/usr/bin/env python3
"""Round 89 (v4.04, referee 2 items 4 and 15): two fields that need a
disposition of their own.

BD+05 1668 (= GJ 273, Luyten's Star).  The referee is right that four
threshold crossings with the highest statistics in the survey outside
beta Pictoris cannot be dismissed in one sentence.  The answer is mundane
and it is clean: all four are in ONE ACA execution block, and in that block
the whole field is above threshold -- every one of the 512 control positions
exceeds T = 5, with a median of about 11 against a survey median near 2.75.
The single-integration noise is exactly as predicted, but the residual does
not integrate down: the jackknife error on the channel mean is six times
thermal and a binned-mean test is flat.  A slow, smooth temporal drift
present at every position in every channel inflates the statistic roughly
uniformly, which turns an empty field into 512 detections.  Line emission, a
field source, a common mode and a signal at the star are each falsified
separately -- and decisively by the fact that the SAME SKY was observed 24
more times in the same project with the same array and setup and shows
nothing.

★ The quality criterion the survey lacked is the MEDIAN of the 512 controls,
not their maximum.  It is recomputed here from the released catalogue, and it
must be reported as DIAGNOSTIC and not as an exclusion: a cut strict enough
to remove this block would also remove the HD 48370 CO positive control.

alpha CMa B (Sirius B).  The referee asked whether Sirius A falls inside the
control annulus.  Answering it exposed a worse problem: the extraction
propagates Sirius B with the SYSTEM proper motion only and ignores the
50.13-year visual orbit, so the search ran several synthesised beams from
where Sirius B actually was.  ★ The published alpha CMa B limit is therefore
WITHDRAWN.  No threshold crossing depends on it.

-> survey_numbers_round89.tex
"""
import csv
import json
import os
import statistics as st

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, 'survey_numbers_round89.tex')
F = json.load(open(os.path.join(HERE, 'r8inputs', 'fields_v404.json')))
ROWS = list(csv.DictReader(open(os.path.join(HERE,
                                             'per_target_results_v3.99.csv'))))

M = {}


def m(k, v):
    M[k] = v


B = F['bd05']

# ---------------------------------------- recomputed from the catalogue
star_rows = [r for r in ROWS if r['star_name'].replace(' ', '').replace('+', '')
             .startswith('BD051668')]
assert star_rows, 'BD+05 1668 not found in the released catalogue'
blk_rows = [r for r in star_rows if r['eb'] == B['block']]
assert blk_rows, ('block %s not in the released catalogue' % B['block'])

m('BdStar', B['star'])
m('BdAlias', B['alias'])
m('BdBlock', B['block'].replace('_', r'\_'))
m('BdNWin', '%d' % len(star_rows))
m('BdNBlocks', '%d' % len({r['eb'] for r in star_rows}))
m('BdNBlockWin', '%d' % len(blk_rows))
m('BdNSibling', '%d' % (len({r['eb'] for r in star_rows}) - 1))

# The crossings, from the catalogue's own crossing flag.
cross = [r for r in star_rows if r['crossing'] in ('1', 'True', 'true')]
in_blk = [r for r in cross if r['eb'] == B['block']]
m('BdNCross', '%d' % len(cross))
m('BdNCrossBlock', '%d' % len(in_blk))
# ★ The whole disposition rests on the crossings being confined to one block.
# Assert it against the catalogue, not against the note it was measured in.
assert len(cross) == len(in_blk) and len(cross) > 0, (len(cross), len(in_blk))
m('BdTMax', '%.2f' % max(float(r['star_snr']) for r in in_blk))
_sib = max(float(r['star_snr']) for r in star_rows if r['eb'] != B['block'])
m('BdSibTMax', '%.2f' % _sib)
# ★ The argument is that 24 further executions of the same field show
# nothing.  That is only true if none of them reaches the trigger; assert it.
assert _sib < 5.0, _sib

# ★ The missing quality criterion: the MEDIAN control, survey-wide and here.
# The released catalogue carries the control MAXIMUM but not the control
# MEDIAN, which is precisely the diagnostic this field shows to be the useful
# one; the median comes from the frozen ensembles of the corrected export.
EXP = json.load(open(os.path.join(HERE, 'corrected_export_v399.json')))['rows']
med = sorted(float(x['ctrl_med']) for x in EXP if x.get('ctrl_med') is not None)
assert len(med) > 500, len(med)
m('BdSurvCtrlMed', '%.2f' % st.median(med))
m('BdSurvCtrlPNN', '%.2f' % med[int(0.99 * (len(med) - 1))])
m('BdSurvCtrlN', '%d' % len(med))

for k, v in (('BdCtrlMed', '%.1f' % B['ctrl_median']),
             ('BdCtrlMax', '%.1f' % B['ctrl_max']),
             ('BdNCtrlAbove', '%d' % B['n_ctrl_above_five']),
             ('BdNCtrl', '%d' % B['n_ctrl']),
             ('BdBlockCtrlMed', '%.2f' % B['block_ctrl_median']),
             ('BdSibCtrlLo', '%.2f' % B['sibling_ctrl_median_lo']),
             ('BdSibCtrlHi', '%.2f' % B['sibling_ctrl_median_hi']),
             ('BdRmsMeas', '%.4f' % B['rms_measured_Jy']),
             ('BdRmsPred', '%.4f' % B['rms_predicted_Jy']),
             ('BdThermal', '%.4f' % B['thermal_err_Jy']),
             ('BdJack', '%.3f' % B['jackknife_err_Jy']),
             ('BdJackRatio', '%.1f' % (B['jackknife_err_Jy']
                                       / B['thermal_err_Jy'])),
             ('BdScatter', '%.2f' % B['statistic_scatter']),
             ('BdChanCorr', '%.3f' % B['chan_corr_median']),
             ('BdOffFreqMax', '%.1f' % B['offfreq_ctrl_absmax']),
             ('BdEdgeChan', '%d' % B['edge_channels']),
             ('BdEdgeFrac', '%.3f' % B['edge_frac_in_window']),
             ('BdBasebandGHz', '%.3f' % B['baseband_sep_GHz'])):
    m(k, v)
assert B['n_ctrl_above_five'] == B['n_ctrl'], B
assert B['jackknife_err_Jy'] > 4 * B['thermal_err_Jy'], B
assert abs(B['rms_measured_Jy'] / B['rms_predicted_Jy'] - 1) < 0.02, B

# ------------------------------------------------------- alpha CMa B
S = F['sirius']
sir = [r for r in ROWS if 'CMa' in r['star_name']]
assert {r['star_name'] for r in sir} == {'alf CMa B'}, \
    {r['star_name'] for r in sir}
m('SirNWinCat', '%d' % len(sir))
m('SirNWin', '%d' % S['n_windows'])
m('SirNInAnn', '%d' % S['n_windows_A_in_annulus'])
m('SirPeriod', '%.2f' % S['orbit_period_yr'])
m('SirSemiMajor', '%.2f' % S['orbit_a_arcsec'])
m('SirSepLo', '%.1f' % S['sep_extracted_to_B_lo_arcsec'])
m('SirSepHi', '%.1f' % S['sep_extracted_to_B_hi_arcsec'])
m('SirBeamsLo', '%.0f' % S['sep_in_beams_lo'])
m('SirBeamsHi', '%.0f' % S['sep_in_beams_hi'])
m('SirASepLo', '%.2f' % S['sep_A_to_extracted_lo_arcsec'])
m('SirASepHi', '%.2f' % S['sep_A_to_extracted_hi_arcsec'])
m('SirBands', S['bands_with_A_in_annulus'])
# The withdrawal is only safe if no threshold crossing depends on this star.
sir_cross = [r for r in sir if r['crossing'] in ('1', 'True', 'true')]
m('SirNCross', '%d' % len(sir_cross))
assert len(sir_cross) == 0, ('alpha CMa B carries a threshold crossing; the '
                             'limit cannot simply be withdrawn')
assert S['n_windows_A_in_annulus'] < S['n_windows'], S
assert len(sir) > 0, 'alpha CMa B is not in the released catalogue'

with open(OUT, 'w') as fh:
    fh.write('%% GENERATED by fields_v404.py -- do not hand-edit.\n')
    for k in sorted(M):
        fh.write('\\newcommand{\\%s}{%s}\n' % (k, M[k]))

print('fields_v404: %s -- %d crossings, all %d in block %s of %d; sibling '
      'maximum T* = %s'
      % (B['star'], len(cross), len(in_blk), B['block'],
         len({r['eb'] for r in star_rows}), M['BdSibTMax']))
print('  alpha CMa B -- %d released windows, %d crossings; extraction ran '
      '%.1f-%.1f arcsec (%s-%s synthesised beams) from the star'
      % (len(sir), len(sir_cross), S['sep_extracted_to_B_lo_arcsec'],
         S['sep_extracted_to_B_hi_arcsec'], M['SirBeamsLo'], M['SirBeamsHi']))
print('  -> %s (%d macros)' % (os.path.basename(OUT), len(M)))
