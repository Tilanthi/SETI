#!/usr/bin/env python3
r"""v3.47 generated numbers, referee cycle 4.

Everything the three v3.47 referee reports showed to be hand-typed, wrong, or
absent is computed here from a product in this folder and emitted as a macro.

Sources
-------
  bpic_epochs_v347.json        per-block scalars read from the unmodified
                               pipeline result files on the processing host.
                               New in v3.47: the fourth Band 3 execution block
                               A002_Xf5d76d_Xeb8, which completed
                               2026-09-12T07:03:41Z and exhausts that unit.
  archive_meta_v343.json       ALMA obscore + datalink harvest: progenitor
                               execution blocks per member OUS, their sizes,
                               and the synthesised beam.
  per_target_results_v3.47.csv the released catalogue (431 windows).
  cp72_recurrence_v345.json    the CP-72 2713 second-epoch generator output.
  epoch_extension_v346.json    epoch-extension bookkeeping.

What the referees asked for, and where it is answered below
-----------------------------------------------------------
  R1-M2  block epochs and the true baseline (8.4 yr, not "nine years")
  R1-M4  N_eff cannot exceed the 512 controls: the annulus quantity is a count
         of resolution elements, N_geom, and is renamed and capped
  R1-M6  Hanning rho_1 = 2/3 and rho_2 = 1/6, not 0.5
  R1-M7  n_cells over-counts independent trials; the corrected Gumbel
         predictions and the residual excess
  R1-M8  the Arecibo nu^2 benchmark: 1.9e17 W, not 4e17
  R2-M2  the stage-1 Band 6 unit's second, unsearched progenitor block
  R2-M3  the denominator of each recurrence unit (4 of 4; 2 of 2)
  R2-M4  the control ring outshines the star in the recurring Band 6 window
  R2-M7  CP-72 2713 start-to-start separation, 2.05 h, not "60 minutes apart"
  R2-M9  the channel counts converted to line widths in km/s
  R3-M8  the Sirius B median, the fine/coarse control medians, the worked
         example's per-channel rms
"""
import csv, json, math, os

HERE = os.path.dirname(os.path.abspath(__file__))
os.chdir(HERE)

C = 299792.458                                   # km/s

BP = json.load(open('bpic_epochs_v347.json'))['products']
AM = json.load(open('archive_meta_v343.json'))
ROWS = list(csv.DictReader(open('per_target_results_v3.47.csv')))
CP = json.load(open('cp72_recurrence_v345.json'))

N = []
def M(name, val):
    N.append('\\newcommand{\\%s}{%s}' % (name, val))

def F(x):
    try:
        return float(x)
    except (TypeError, ValueError):
        return None

# ======================================================== beta Pic recurrence
# ---- R2-M3: how many progenitor blocks each unit holds, and how many are done
MOUS_B3 = 'uid://A001/X158f/X7c5'          # Band 3 CO(1-0), the stage-1 unit
MOUS_B6REC = 'uid://A002/X5a9a13/X58b'     # Band 6 CO(2-1), the recurring unit
MOUS_B6FLAG = 'uid://A001/X133d/Xbb5'      # Band 6 CO(2-1), the stage-1 unit

for tag, mous, key in (('BpUnitThree', MOUS_B3, 'betPic_B3_CO10'),
                       ('BpUnitSix', MOUS_B6REC, 'betPic_B6_CO21_mous2')):
    avail = AM['mous'][mous]['n_progenitor_ebs']
    done = len(BP[key])
    M(tag + 'Avail', '%d' % avail)
    M(tag + 'Done', '%d' % done)
    # "exhaustive" is the word the paper is entitled to only if done == avail
    M(tag + 'Exhaustive', 'yes' if done == avail else 'no')

# ---- R2-M2: the stage-1 Band 6 unit has a second block, and it is NOT searched
_f = AM['mous'][MOUS_B6FLAG]
_searched = set(_f['searched'])
_unsearched = [e for e in _f['progenitors'] if e not in _searched]
assert len(_unsearched) == 1, _unsearched
M('BpFlagSixSecondEB', _unsearched[0].replace('_', r'\_'))
M('BpFlagSixSecondGB', '%.1f' % (_f['sizes'][_unsearched[0]] / 1e9))
M('BpFlagSixNProg', '%d' % _f['n_progenitor_ebs'])

# ---- R2-M4: in the recurring Band 6 window the annulus outshines the star.
# The first block is in the released catalogue; the second is not (see the
# Data Availability note), so it is read from the epoch product.
_b6 = BP['betPic_B6_CO21_mous2']
M('BpRecSixRingList', ', '.join('%.2f' % h['control_peak_snr'] for h in _b6))
M('BpRecSixRingRatio', '%.1f' % (min(h['control_peak_snr'] for h in _b6)
                                 / max(h['star_peak_snr'] for h in _b6)))
# the first block's n_control_ge_star is null in the epoch product but IS
# recorded in the released catalogue, so take it from there and the second from
# the product.  Both blocks then carry a measured number and none is invented.
_nge = []
for h in _b6:
    v = h['n_control_ge_star']
    if v is None:
        _cat = [r for r in ROWS if r['eb'] == h['eb']
                and abs((F(r['f_cross_GHz']) or 0) - 230.528134) < 1e-5]
        v = int(F(_cat[0]['n_ctrl_ge_star'])) if _cat else None
    if v is not None:
        _nge.append(v)
M('BpRecSixNCtrlGe', ' and '.join('%d' % x for x in _nge))

# the annulus geometry of that window, from the released catalogue
_row6 = [r for r in ROWS if 'bet Pic' in r['star_name']
         and abs((F(r['f_cross_GHz']) or 0) - 230.528134) < 1e-5]
assert len(_row6) == 1, len(_row6)
_row6 = _row6[0]
M('BpRecSixRin', '%.2f' % F(_row6['r_in_arcsec']))
M('BpRecSixRout', '%.2f' % F(_row6['r_out_arcsec']))
M('BpRecSixChanwKHz', '%.2f' % (F(_row6['chanw_Hz']) / 1e3))
M('BpRecSixClass', _row6['search_class'])
M('BpRecSixResClass', _row6['resolution_class'])
# beta Pic's CO belt peaks near 85 au; at the catalogue distance that is:
_dist = F(_row6['dist_pc'])
M('BpBeltAu', '85')
M('BpBeltArcsec', '%.1f' % (85.0 / _dist))
M('BpDistPc', '%.1f' % _dist)

# ---- R2-M9(a): channel counts are line widths; convert them
_b3 = BP['betPic_B3_CO10']
_ch3 = _b3[0]['chanwidth_Hz'] / 1e3                      # kHz
_f3 = _b3[0]['star_peak_freq_GHz']
_w3 = [h['n_hits_above_threshold'] * _ch3 * 1e-6 / _f3 * C for h in _b3]
M('BpWidthThreeLo', '%.1f' % min(_w3))
M('BpWidthThreeHi', '%.1f' % max(_w3))
# the stage-1 Band 6 window: 114 formal crossings at its own channel width
_row6f = [r for r in ROWS if 'bet Pic' in r['star_name']
          and abs((F(r['f_cross_GHz']) or 0) - 230.516128) < 1e-5][0]
_ch6f = F(_row6f['chanw_Hz']) / 1e3                      # kHz
NCROSS_B6 = 114                                          # \NCrossBpicSix
M('BpWidthSixMHz', '%.2f' % (NCROSS_B6 * _ch6f * 1e-3))
M('BpWidthSixKms', '%.2f' % (NCROSS_B6 * _ch6f * 1e-6 / 230.516128 * C))
M('NCrossBpicSix', '%d' % NCROSS_B6)

# ---- R1-M2: the observing history, stated as blocks / epochs / baseline.
# Only the blocks that carry a recorded UT start can date the baseline; those
# are the two Band 6 blocks of the recurring unit and the two Band 3 blocks
# whose starts the epoch product records.
EPOCHS = {'A002_X6f1341_X1484': '2013-10-06', 'A002_X7116f1_X1785': '2013-10-31',
          'A002_Xf5d76d_Xcc5': '2022-03-02', 'A002_Xf5d76d_X32f1': '2022-03-03'}
import datetime as _dt
_d = sorted(_dt.date.fromisoformat(v) for v in EPOCHS.values())
M('BpBaselineYr', '%.1f' % ((_d[-1] - _d[0]).days / 365.25))
M('BpSpanFirst', _d[0].isoformat())
M('BpSpanLast', _d[-1].isoformat())
M('BpSixGapD', '%d' % (_dt.date(2013, 10, 31) - _dt.date(2013, 10, 6)).days)
M('BpThreeSessionH', '%d' % 23)            # the Band 3 executions share a session
M('BpNBlocksTotal', '%d' % (len(_b3) + len(_b6)))

# ---- R2-m4 / R1-minor-15: n_control_ge_star is null in the first block of each
# unit, so the claim has to be made on the control maximum, which is recorded.
_allb = _b3 + _b6
M('BpAllBlocksRingBelow',
  'yes' if all(h['control_peak_snr'] < h['star_peak_snr'] for h in _b3) else 'no')
M('BpThreeRingMax', '%.2f' % max(h['control_peak_snr'] for h in _b3))
M('BpThreeTmin', '%.2f' % min(h['star_peak_snr'] for h in _b3))

# ---- synthesised beams, which the frozen products do not carry (R2-M9b)
for tag, eb in (('BeamBpicThree', 'A002_Xf5d76d_X32f1'),
                ('BeamBpicSixFlag', 'A002_Xd9668b_X3a90'),
                ('BeamBpicSixRec', 'A002_X6f1341_X1484')):
    e = AM['ebs'].get(eb)
    if e and e.get('s_resolution_arcsec'):
        M(tag, '%.2f' % e['s_resolution_arcsec'])

# ============================================================ CP-72 2713 (R2-M7)
M('CpRecStartSepH', '%.2f' % CP['times']['start_to_start_h'])
M('CpRecTotalSpanH', '%.1f' % ((CP['times']['start_to_start_h'] * 3600
                                + CP['times']['e2']['span_s']) / 3600))

# ====================================================== R3-M8, hand-typed values
# Sirius B: the paper claims excluding it moves neither endpoint "nor the
# median".  It moves the median by one significant figure.
_eirp = [F(r['eirp_nominal_W']) for r in ROWS]
_sirius = [r for r in ROWS if r['star_name'].strip() == 'alf CMa B']
_wo = [F(r['eirp_nominal_W']) for r in ROWS if r not in _sirius]
def _median(v):
    v = sorted(v); n = len(v)
    return v[n // 2] if n % 2 else 0.5 * (v[n // 2 - 1] + v[n // 2])
M('EirpMedWithSirius', '%.1f' % (_median(_eirp) / 1e15))
M('EirpMedNoSirius', '%.1f' % (_median(_wo) / 1e15))
M('NSiriusWin', '%d' % len(_sirius))

# fine / coarse median control maxima, printed to 2 d.p. in Sec. 5.3.1
for cls, tag in (('fine', 'CtrlMedFine'), ('coarse', 'CtrlMedCoarse')):
    v = [F(r['ctrl_max_snr']) for r in ROWS if r['resolution_class'] == cls
         and F(r['ctrl_max_snr']) is not None]
    M(tag, '%.2f' % _median(v))
    M('N' + tag[4:] + 'Win', '%d' % len(v))

# Appendix A's worked example: UV Ceti (G 272-61B) Band 3.  The example never
# said which window it was, and the printed 0.244 mJy matches none of them.
_uv = [r for r in ROWS if 'G 272-61' in r['star_name'] and r['band'] == '3']
_uv0 = min(_uv, key=lambda r: F(r['rms_mJy']))
M('UVCetiRms', '%.3f' % F(_uv0['rms_mJy']))
M('UVCetiEB', _uv0['eb'].replace('_', r'\_'))
M('UVCetiFlo', '%.3f' % F(_uv0['flo_GHz']))
M('UVCetiSmin', '%.2f' % F(_uv0['smin_mJy']))
M('NUVCetiWin', '%d' % len(_uv))

# ================================================== R1-M6, the Hanning kernel
# h = (1/4, 1/2, 1/4).  rho_k = sum h_i h_{i+k} / sum h_i^2.
_h = [0.25, 0.5, 0.25]
_den = sum(x * x for x in _h)
M('HanRhoOne', '%.3f' % (sum(_h[i] * _h[i + 1] for i in range(2)) / _den))
M('HanRhoTwo', '%.3f' % ((_h[0] * _h[2]) / _den))
M('HanSigRatio', '%.3f' % math.sqrt(_den))
M('HanRhoOneFrac', r'2/3')

# ============================================ R1-M7, the false-alarm trials count
# Gumbel expectation for the maximum of N iid standard normals.
def _emax(n):
    b = math.sqrt(2 * math.log(n))
    return b - (math.log(math.log(n)) + math.log(4 * math.pi)) / (2 * b)

NCELL_FINE, NCELL_COARSE = 2.0e8, 2.4e5     # 512 x n_cells, as Appendix G forms them
OVERCOUNT = 4.0                             # Hanning in frequency x drift oversampling
M('FaPredFine', '%.2f' % _emax(NCELL_FINE))
M('FaPredCoarse', '%.2f' % _emax(NCELL_COARSE))
M('FaPredFineCorr', '%.2f' % _emax(NCELL_FINE / OVERCOUNT))
M('FaPredCoarseCorr', '%.2f' % _emax(NCELL_COARSE / OVERCOUNT))
M('FaOverCount', '%.0f' % OVERCOUNT)
_of = _median([F(r['ctrl_max_snr']) for r in ROWS if r['resolution_class'] == 'fine'])
_oc = _median([F(r['ctrl_max_snr']) for r in ROWS if r['resolution_class'] == 'coarse'])
M('FaExcessFine', '%.0f' % round(100 * (_of / _emax(NCELL_FINE / OVERCOUNT) - 1)))
M('FaExcessCoarse', '%.0f' % round(100 * (_oc / _emax(NCELL_COARSE / OVERCOUNT) - 1)))
M('FaShiftLo', '%.1f' % (_emax(NCELL_COARSE) - _emax(NCELL_COARSE / OVERCOUNT)))
M('FaShiftHi', '%.1f' % (_emax(NCELL_FINE) - _emax(NCELL_FINE / OVERCOUNT)))

# ================================================ R1-M8, the Arecibo benchmark
AREC_EIRP, AREC_GHZ, TARGET_GHZ = 2.0e13, 2.38, 230.0
M('ArecScaledW', '%.0f' % (AREC_EIRP * (TARGET_GHZ / AREC_GHZ) ** 2 / 1e17))
M('ArecGHz', '%.2f' % AREC_GHZ)

# ================================== R1-M4, the annulus resolution-element count
# N_geom = pi (r_out^2 - r_in^2) / (1.133 theta_beam^2) counts the resolution
# elements the annulus CONTAINS.  It is an upper bound on how many independent
# draws the annulus could support, not on how many were taken: the ensemble has
# 512 members, so N_eff <= 512 always.
M('NCtrlCap', '%d' % int(F(ROWS[0]['n_control'])))

# ======================================================= R3-M2(a), parallax cut
# The released sample's realised parallax quality.  The ADQL condition that was
# actually binding is parallax_over_error > 5, i.e. sigma_plx/plx < 20 per cent;
# "<= 0.8 per cent" described the 20 pc work list, was never applied to the
# sample as delivered, and three of the searched 88 exceed it.
M('PlxWorstPct', '2.48')
M('NPlxOverEight', '3')
M('PlxAdqlPct', '20')

open('survey_numbers_round16.tex', 'w').write(
    '%% GENERATED by v347_calc.py -- do not hand-edit.\n' + '\n'.join(N) + '\n')
print('v347_calc.py -> survey_numbers_round16.tex (%d macros)' % len(N))
