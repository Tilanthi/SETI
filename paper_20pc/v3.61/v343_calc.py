#!/usr/bin/env python3
"""Round-13 (v3.46) generated numbers.

Every quantity the three v3.46 referee reports showed to be hand-typed,
stale or contradicted by the shipped catalogue is recomputed here from
`per_target_results_v3.61.csv` (the released catalogue), the frozen export
and `pipeline_peakfreq_v342.json`, and emitted as macros in
`survey_numbers_round13.tex`.  Run after `v342_calc.py`, which writes the CSV.

Nothing in this file is hand-typed except the two pipeline code constants
MEDWIN = 65 and the block rule nb = max(2, n // MEDWIN), both quoted from
`seti_drift_search_generic.py:98-124` and recorded in BUILD_NOTES.md.
"""
import csv, json, math
import statistics as st

HERE = __file__.rsplit('/', 1)[0]
CSV = HERE + '/per_target_results_v3.61.csv'
PK = HERE + '/pipeline_peakfreq_v342.json'
OUT = HERE + '/survey_numbers_round13.tex'

ROWS = list(csv.DictReader(open(CSV)))
N = len(ROWS)
assert N == 443, N   # 431 released + 12 Band 9/10 restored in v3.60

macros = []

# Retired in the v3.46 cycle after the unused-macro sweep: AcaBeamRatio,
# CellsObsMedian, EdgeStarMin, NEbTwelveM, NWinBeamKnown, NeffMedSevenM,
# PbMaxPct and the seven SmearEta/SmearPen spares, none of which the
# manuscript referenced (the smearing census travels as \SmearList).


def M(name, val):
    macros.append('\\newcommand{\\%s}{%s}' % (name, val))


def f(r, k):
    v = r[k]
    if v == '':
        raise KeyError(k)          # absent, e.g. no crossing in this window
    return float(v)


# ---------------------------------------------------------------- R1-M6
# Intra-integration smearing census.  The manuscript said three windows;
# the catalogue carries nine.
SM = sorted((r for r in ROWS if f(r, 'eta_smear') < 0.99),
            key=lambda r: f(r, 'eta_smear'))
M('NSmearLo', '%d' % len(SM))
WORST = [r for r in SM if f(r, 'eta_smear') < 0.7]
M('NSmearWorst', '%d' % len(WORST))
M('SmearWorstPenLo', '%.2f' % (1.0 / max(f(r, 'eta_smear') for r in WORST)))
M('SmearWorstPenHi', '%.2f' % (1.0 / min(f(r, 'eta_smear') for r in WORST)))
M('SmearWorstChanKHz', '%.1f' % (f(WORST[0], 'chanw_Hz') / 1e3))
M('NSmearFlagged', '%d' % sum(1 for r in SM if r['stage1_flag'] == 'True'))
M('NSmearOk', '%d' % (N - len(SM)))


def tidy(name):
    return {'bet Pic': r'$\beta$~Pic', 'eta Crv': r'$\eta$~Crv',
            'HIP10679': 'HIP~10679', 'HD172555': 'HD~172555',
            'HD 48370': 'HD~48370',
            'CP-72 2713': 'CP$-$72~2713'}.get(name, name.replace(' ', '~'))


# generated inline list, worst first, grouped by eta
cells = []
for r in SM:
    cells.append('%s Band~%s (%.3f, $\\times$%.2f)'
                 % (tidy(r['star_name']), r['band'], f(r, 'eta_smear'),
                    1.0 / f(r, 'eta_smear')))
M('SmearList', ', '.join(cells[:-1]) + ' and ' + cells[-1])

# ---------------------------------------------------------------- R1-M7
# Primary-beam correction factor = smin / (5 rms), the ratio the catalogue
# carries.  r/theta_PB inverted from the pipeline's own Gaussian,
# G = exp(-4 ln2 (r/theta_PB)^2), theta_PB = PB_COEF_CODE lambda / DISH_CODE.
# Referee E2: that is an Airy first-null coefficient at a single hard-wired
# dish diameter.  The same constants as v342_calc.py, which sets the geometry.
PB_COEF_CODE = 1.22
PB_COEF_FWHM = 1.13
DISH_CODE = 12.0
DISH_ACA = 7.0


def pbf(r):
    return f(r, 'smin_mJy') / (5.0 * f(r, 'rms_mJy'))


def r_over_theta(g):
    return math.sqrt(math.log(g) / (4.0 * math.log(2.0)))


PB = sorted(pbf(r) for r in ROWS)
M('PbMedian', '%.5f' % st.median(PB))
M('PbPninety', '%.3f' % PB[int(0.9 * N)])
M('NPbAboveTwoPct', '%d' % sum(1 for x in PB if x > 1.02))
M('NPbAboveTenPct', '%d' % sum(1 for x in PB if x > 1.10))
TOP = max(ROWS, key=pbf)
M('PbMaxStar', tidy(TOP['star_name']))
M('PbMaxBand', TOP['band'])
M('PbMax', '%.2f' % pbf(TOP))
M('PbMaxRoverTheta', '%.2f' % r_over_theta(pbf(TOP)))
M('PbMaxRoverFwhm', '%.2f' % (r_over_theta(pbf(TOP)) * 1.22 / 1.13))
SIR = [r for r in ROWS if r['star_name'].startswith('alf CMa')
       or 'Sirius' in r['star_name']]
M('NSirWin', '%d' % len(SIR))
M('PbSirLoPct', '%.1f' % (100 * (min(pbf(r) for r in SIR) - 1)))
M('PbSirHiPct', '%.1f' % (100 * (max(pbf(r) for r in SIR) - 1)))
M('PbSirRoverThetaLo', '%.2f' % r_over_theta(min(pbf(r) for r in SIR)))
M('PbSirRoverThetaHi', '%.2f' % r_over_theta(max(pbf(r) for r in SIR)))
# the next tier down, named in the report
TIER = {}
for r in ROWS:
    if pbf(r) > 1.10:
        TIER.setdefault((tidy(r['star_name']), r['band']), []).append(pbf(r))
M('NPbTierStars', '%d' % len({k[0] for k in TIER}))

# ---------------------------------------------------------------- R1-M8
# beta Pic empirical significance against the 431 control maxima, on the
# operative symmetric statistic.
CMAX = sorted((f(r, 'ctrl_max_snr') for r in ROWS), reverse=True)
M('CtrlMaxSurveyMax', '%.1f' % CMAX[0])
M('CtrlMaxSurveySecond', '%.1f' % CMAX[1])
BP = [r for r in ROWS if r['star_name'] == 'bet Pic' and r['stage1_flag'] == 'True']
for r in BP:
    b = r['band']
    tag = {'3': 'Three', '6': 'Six'}[b]
    T = f(r, 'star_snr')
    nge = sum(1 for q in ROWS if f(q, 'ctrl_max_snr') >= T)
    M('BpicB%sTsym' % tag, '%.2f' % T)
    M('NCtrlGeBpicB%s' % tag, '%d' % nge)
    M('BpicB%sAddOne' % tag, '%.3f' % ((nge + 1) / (N + 1)))
M('BpicAddOneDen', '%d' % (N + 1))
# the CO-filled beta Pic Band 6 window whose ring reaches 15.2
COFILL = max((r for r in ROWS if r['star_name'] == 'bet Pic'
              and r['stage1_flag'] == 'False'), key=lambda r: f(r, 'ctrl_max_snr'))
M('BpicCoRingMax', '%.1f' % f(COFILL, 'ctrl_max_snr'))
M('BpicCoRingRank', '%d' % (1 + sum(1 for q in ROWS
                                    if f(q, 'ctrl_max_snr') > f(COFILL, 'ctrl_max_snr'))))

# ---------------------------------------------------------------- R3-4
# Band 4-8 union: the complement of the Band 3 union within the survey union.
def union(intervals):
    iv = sorted((min(a, b), max(a, b)) for a, b in intervals)
    tot, lo, hi = 0.0, None, None
    for a, b in iv:
        if lo is None:
            lo, hi = a, b
        elif a <= hi:
            hi = max(hi, b)
        else:
            tot += hi - lo
            lo, hi = a, b
    if lo is not None:
        tot += hi - lo
    return tot


ALL = union([(f(r, 'flo_GHz'), f(r, 'fhi_GHz')) for r in ROWS])
B3 = union([(f(r, 'flo_GHz'), f(r, 'fhi_GHz')) for r in ROWS if r['band'] == '3'])
HI = union([(f(r, 'flo_GHz'), f(r, 'fhi_GHz')) for r in ROWS if r['band'] != '3'])
M('UnionBandThree', '%.1f' % B3)
M('UnionBandsFourEight', '%.1f' % HI)
M('UnionHiLoGHz', '%d' % round(min(min(f(r, 'flo_GHz'), f(r, 'fhi_GHz'))
                                   for r in ROWS if r['band'] != '3')))
M('UnionHiHiGHz', '%d' % round(max(max(f(r, 'flo_GHz'), f(r, 'fhi_GHz'))
                                   for r in ROWS if r['band'] != '3')))
GROSS = sum(abs(f(r, 'fhi_GHz') - f(r, 'flo_GHz')) for r in ROWS)
M('GrossOverUnion', '%.1f' % (GROSS / ALL))

# ---------------------------------------------------------------- R1-M5 / R3-7
# Baseline filter: contiguous block median with linear interpolation between
# block centres, nb = max(2, n // MEDWIN) blocks, so the effective width is
# W = n / nb channels.  `pipeline_peakfreq_v342.json` carries the trimmed
# channel count n per window; matched to the catalogue on (EB, window edges).
MEDWIN = 65
PKROWS = json.load(open(PK))
PKIDX = {}
for r in PKROWS:
    PKIDX[(r['eb'], round(min(r['flo'], r['fhi']), 4),
           round(max(r['flo'], r['fhi']), 4))] = r
for r in ROWS:
    k = (r['eb'], round(min(f(r, 'flo_GHz'), f(r, 'fhi_GHz')), 4),
         round(max(f(r, 'flo_GHz'), f(r, 'fhi_GHz')), 4))
    # the Band 9/10 windows restored in v3.60 are outside the peak-frequency
    # file; they carry no crossing, so nothing downstream needs their peak
    r['_pk'] = PKIDX.get(k)
    n_ = r['_pk']['nch'] if r['_pk'] else None
    r['_W'] = (n_ / max(2, n_ // MEDWIN)) if n_ else None

FINE = [r for r in ROWS if r['resolution_class'].startswith('fine')]
COARSE = [r for r in ROWS if not r['resolution_class'].startswith('fine')]
M('MedWin', '%d' % MEDWIN)
M('MedWinSplit', '%d' % (2 * MEDWIN))
M('MedWinFineLo', '%.0f' % min(r['_W'] for r in FINE if r['_W'] is not None))
M('MedWinFineHi', '%.0f' % max(r['_W'] for r in FINE if r['_W'] is not None))
M('MedWinCoarseLo', '%.0f' % min(r['_W'] for r in COARSE if r['_W'] is not None))
M('MedWinCoarseHi', '%.0f' % max(r['_W'] for r in COARSE if r['_W'] is not None))
M('NWinFullWidth', '%d' % sum(1 for r in ROWS if r['_pk'] and r['_pk']['nch'] > 2 * MEDWIN))
# the baseline ceiling W x channel width, per resolution class
ceilF = sorted(r['_W'] * f(r, 'chanw_Hz') for r in FINE if r['_W'] is not None)
ceilC = sorted(r['_W'] * f(r, 'chanw_Hz') for r in COARSE if r['_W'] is not None)
M('MedWinCeilFineMHz', '%.0f' % (st.median(ceilF) / 1e6))
M('MedWinCeilCoarseGHz', '%.1f' % (st.median(ceilC) / 1e9))
M('ChanFineKHz', '%.0f' % (st.median(f(r, 'chanw_Hz') for r in FINE if r['_W'] is not None) / 1e3))
M('ChanCoarseMHz', '%.2f' % (st.median(f(r, 'chanw_Hz') for r in COARSE if r['_W'] is not None) / 1e6))

# ---------------------------------------------------------------- R1-M9
# Trials accounting, stated once and in one set of units.
def ncell(r):
    nch = int(abs(f(r, 'fhi_GHz') - f(r, 'flo_GHz')) * 1e9 / f(r, 'chanw_Hz'))
    return nch * int(f(r, 'n_drift_trials'))


CELLS = sorted(ncell(r) for r in ROWS)
TOT = sum(CELLS)


def sci(x, nd=1):
    e = int(math.floor(math.log10(x)))
    return '$%.*f\\times10^{%d}$' % (nd, x / 10 ** e, e)


M('CellsTotal', sci(TOT, 2))
M('CellsWinMed', format(int(st.median(CELLS)), ',').replace(',', '\\,'))
M('CellsWinMax', format(CELLS[-1], ',').replace(',', '\\,'))
M('CellsWinMin', format(CELLS[0], ',').replace(',', '\\,'))
GAUSS5 = 2.8665e-7
M('CellExpect', '%.1f' % (TOT * GAUSS5))
# Observed exceedances in the same units, from the pipeline's own per-window
# count of >=5 sigma on-star channel x drift cells (`nhit`).  Counted over the
# windows the catalogue records as carrying an on-star crossing, so the two
# HD 139084B component rows that share one window are not double-counted.
CRS = [r for r in ROWS if r['crossing'] == 'True']
NHIT = sum(r['_pk']['nhit'] for r in CRS)
FLG = [r for r in CRS if r['stage1_flag'] == 'True']
NHITFLG = sum(r['_pk']['nhit'] for r in FLG)
M('CellsObserved', '%d' % NHIT)
M('CellsObsFlagged', '%d' % NHITFLG)
M('CellsObsRest', '%d' % (NHIT - NHITFLG))
M('NHitWindows', '%d' % len(CRS))
M('NHitWindowsRest', '%d' % (len(CRS) - len(FLG)))
M('CellsRestOverExpect', '%.1f' % ((NHIT - NHITFLG) / (TOT * GAUSS5)))

# ---------------------------------------------------------------- R2-M4
# Edge proximity of the 20 on-star crossings.
def chan_index(r):
    lo = min(f(r, 'flo_GHz'), f(r, 'fhi_GHz'))
    hi = max(f(r, 'flo_GHz'), f(r, 'fhi_GHz'))
    nch = int(round((hi - lo) * 1e9 / f(r, 'chanw_Hz')))
    i = int(round((f(r, 'f_cross_GHz') - lo) * 1e9 / f(r, 'chanw_Hz')))
    return i, nch


CROSS = [r for r in ROWS if r['crossing'] == 'True']
M('NCrossWin', '%d' % len(CROSS))
EDGE = []
for r in CROSS:
    i, nch = chan_index(r)
    frac = min(i, nch - i) / nch
    EDGE.append((frac, r, i, nch))
EDGE.sort()
M('EdgeFracMin', '%.3f' % EDGE[0][0])
M('EdgeChanMin', '%d' % EDGE[0][2])
M('EdgeFracSecond', '%.3f' % EDGE[1][0])
M('EdgeStarSecond', tidy(EDGE[1][1]['star_name']))
M('EdgeChanSecond', '%d' % EDGE[1][2])
NFLAG = sum(1 for r in CROSS if r['stage1_flag'] == 'True')
M('EdgeTwoFlagPct', '%.1f' % (100.0 * NFLAG * (NFLAG - 1)
                              / (len(CROSS) * (len(CROSS) - 1))))
BPF = [e for e in EDGE if e[1]['star_name'] == 'bet Pic'
       and e[1]['stage1_flag'] == 'True']
M('EdgeFracBpicLo', '%.2f' % min(e[0] for e in BPF))
M('EdgeFracBpicHi', '%.2f' % max(e[0] for e in BPF))
# across all windows, how often does the recorded peak channel fall in the
# outer 3 per cent?
NOUT = 0
for r in PKROWS:
    if r['nch'] and r['ch'] is not None:
        if min(r['ch'], r['nch'] - r['ch']) / r['nch'] < 0.03:
            NOUT += 1
M('NPeakOuterThree', '%d' % NOUT)
M('NPeakRows', '%d' % len(PKROWS))

# ---------------------------------------------------------------- R2 ACA
# theta_PB is 1.22 lambda / 12 m throughout; the ACA 7 m windows are not
# rescaled.  Recorded as a stated limitation (see BUILD_NOTES).
M('AcaDiamRatio', '%.2f' % (12.0 / 7.0))

with open(OUT, 'w') as fh:
    fh.write('% Generated by v343_calc.py -- do not edit by hand.\n')
    fh.write('\n'.join(macros) + '\n')
print('%d macros -> %s' % (len(macros), OUT))

# ================================================================= v3.46 II
# Quantities settled from metadata and catalogue products shipped in this
# release folder: `archive_meta_v343.json` (ALMA obscore + datalink harvest)
# and `linecat_v343.json` (Splatalogue query at the corrected CP-72 2713
# crossing frequency and at all 20 crossings).

# ---- generated smearing table fragment (R1-M6) ---------------------------
with open(HERE + '/tab_smear.tex', 'w') as fh:
    fh.write('%% GENERATED by v343_calc.py -- do not hand-edit.\n')
    fh.write('\\begin{tabular}{@{}llrrr@{}}\n\\toprule\n')
    fh.write('Star & Band & $\\Delta\\nu_{\\rm ch}$ (kHz) & '
             '$\\eta_{\\rm smear}$ & penalty \\\\\n\\midrule\n')
    for r in SM:
        fh.write('%s & %s & %.1f & %.3f & $\\times%.2f$ \\\\\n'
                 % (tidy(r['star_name']), r['band'], f(r, 'chanw_Hz') / 1e3,
                    f(r, 'eta_smear'), 1.0 / f(r, 'eta_smear')))
    fh.write('\\bottomrule\n\\end{tabular}\n')

META = json.load(open(HERE + '/archive_meta_v343.json'))
EBS, MOUS = META['ebs'], META['mous']

# ---- R2-M6: array configuration and synthesised beam ---------------------
n7 = sum(1 for v in EBS.values() if v.get('array') == '7m')
M('NEbSevenM', '%d' % n7)
w7 = [r for r in ROWS if EBS.get(r['eb'], {}).get('array') == '7m']
M('NWinSevenM', '%d' % len(w7))
M('PctWinSevenM', '%d' % round(100.0 * len(w7) / N))
# how many windows have an inner annulus radius below the synthesised beam
nb_ = 0
res_ok = 0
for r in ROWS:
    sr = EBS.get(r['eb'], {}).get('s_resolution_arcsec')
    if sr:
        res_ok += 1
        if f(r, 'r_in_arcsec') < sr:
            nb_ += 1
M('NWinRinBelowBeam', '%d' % nb_)
BEAM = sorted(EBS[r['eb']]['s_resolution_arcsec'] for r in ROWS
              if EBS.get(r['eb'], {}).get('s_resolution_arcsec'))
M('BeamMinArcsec', '%.2f' % BEAM[0])
M('BeamMaxArcsec', '%.1f' % BEAM[-1])
M('BeamMedArcsec', '%.2f' % st.median(BEAM))
# effective independent spatial trials across the annulus,
# N_eff = pi (r_out^2 - r_in^2) / (1.133 theta_beam^2)
NEFF = []
for r in ROWS:
    sr = EBS.get(r['eb'], {}).get('s_resolution_arcsec')
    if sr:
        NEFF.append(math.pi * (f(r, 'r_out_arcsec') ** 2 - f(r, 'r_in_arcsec') ** 2)
                    / (1.133 * sr ** 2))
NEFF.sort()
M('NeffMed', '%d' % round(st.median(NEFF)))
M('NeffLo', '%d' % round(NEFF[0]))
M('NeffHi', sci(NEFF[-1], 1))
NEFF7 = sorted(math.pi * (f(r, 'r_out_arcsec') ** 2 - f(r, 'r_in_arcsec') ** 2)
               / (1.133 * EBS[r['eb']]['s_resolution_arcsec'] ** 2) for r in w7
               if EBS.get(r['eb'], {}).get('s_resolution_arcsec'))

# ---- R1-M11: online smoothing state, from frequency_support --------------
# The archive reports the effective spectral resolution per spectral window;
# its ratio to the measurement set's own channel separation is 2.00 where
# ALMA's default online Hanning smoothing was applied.
def fs_ratio(r):
    fs = EBS.get(r['eb'], {}).get('freq_support') or []
    lo = min(f(r, 'flo_GHz'), f(r, 'fhi_GHz'))
    hi = max(f(r, 'flo_GHz'), f(r, 'fhi_GHz'))
    best = None
    for a, b, res in fs:
        ov = min(hi, max(a, b)) - max(lo, min(a, b))
        if ov > 0 and (best is None or ov > best[0]):
            best = (ov, res)
    return None if best is None else best[1] / f(r, 'chanw_Hz')


RAT = [(r, fs_ratio(r)) for r in ROWS]
KNOWN = [(r, x) for r, x in RAT if x]
HAN = [(r, x) for r, x in KNOWN if abs(x - 2.0) < 0.05]
M('NHanKnown', '%d' % len(KNOWN))
M('NHanTwo', '%d' % len(HAN))
M('NHanTwoCoarse', '%d' % sum(1 for r, x in HAN
                              if not r['resolution_class'].startswith('fine')))
M('NCoarseHanKnown', '%d' % sum(1 for r, x in KNOWN
                                if not r['resolution_class'].startswith('fine')))
M('NHanOther', '%d' % (len(KNOWN) - len(HAN)))

# ---- R2-M2: unsearched execution blocks in the same member OUS -----------
NPROG = sum(v['n_progenitor_ebs'] for v in MOUS.values())
M('NProgenitorEB', '%d' % NPROG)
M('NMousMulti', '%d' % sum(1 for v in MOUS.values() if v['n_progenitor_ebs'] > 1))
M('NMous', '%d' % len(MOUS))
multi = {k for k, v in MOUS.items() if v['n_progenitor_ebs'] > 1}
wm = [r for r in ROWS if any(k in multi for k in
                             (EBS.get(r['eb'], {}).get('member_ous') or []))]
M('NWinMultiEB', '%d' % len(wm))
M('PctWinMultiEB', '%d' % round(100.0 * len(wm) / N))
M('NStarMultiEB', '%d' % len({r['star_name'] for r in wm}))

# ---- R2-M1: line catalogue at the corrected CP-72 2713 frequency ---------
LC = json.load(open(HERE + '/linecat_v343.json'))
TUBE = [e for e in LC['cp72']['at_corrected'] if e['in_tube']]
M('CpCatFreq', '%.6f' % LC['cp72']['corrected_crossing_GHz'])
M('NCpTube', '%d' % len(TUBE))


def _lab(e):
    nm = e['name'].split(' v')[0].replace('3Sigma', '').strip()
    sub = {'34SO2': r'$^{34}$SO$_{2}$', 'SO': 'SO', 'HC15N': r'HC$^{15}$N',
           'Unidentified Transition': 'the unidentified Lovas entry'}
    return sub.get(nm, nm)


TUBE = sorted(TUBE, key=lambda e: abs(e['v_star']))
def _num(v):
    return ('$%.0f$' % v).replace('-', '−') if False else ('$%s%.0f$' % ('-' if v < 0 else '', abs(v)))


M('CpTubeList', ', '.join(
    ('%s at %s (%s) km\\,s$^{-1}$' % (_lab(e), _num(e['v_star']), _num(e['v_lsr'])))
    if 'nidentified' in e['name'] else
    ('%s %s at %s (%s) km\\,s$^{-1}$'
     % (_lab(e), e['qn'].replace(' ', ''), _num(e['v_star']), _num(e['v_lsr'])))
    for e in TUBE))
SO = [e for e in TUBE if e['name'].startswith('SO ')][0]
M('CpSoFreq', '%.6f' % SO['freq'])
M('CpSoVstar', '%.1f' % SO['v_star'])
M('CpSoEu', '%.0f' % SO['eu'])
SO2 = [e for e in TUBE if '34SO2' in e['name']][0]
M('CpSotwoEu', '%.0f' % SO2['eu'])
CR = LC['crossings']
M('NCrossWithCat', '%d' % sum(1 for c in CR if c['n_within_60kms_topo'] > 0))
M('NCrossQueried', '%d' % len(CR))
M('CrossCatMedian', '%d' % round(st.median([c['n_within_60kms_topo'] for c in CR])))

with open(OUT, 'w') as fh:
    fh.write('% Generated by v343_calc.py -- do not edit by hand.\n')
    fh.write('\n'.join(macros) + '\n')
print('%d macros (total) -> %s' % (len(macros), OUT))

# ---- R1-M10: family sensitivity of the GEV confirmation, and the ring -----
LN = json.load(open(HERE + '/v342_local_null.json'))
CPW = [w for w in LN['windows'] if w['band'] == 7][0]
try:
    from scipy.stats import gumbel_r
    CM = json.load(open(HERE + '/localnull_code/ctrlmax.json'))['CP-72_2713_B7']
    g = gumbel_r.fit(CM)
    pg = float(gumbel_r.sf(CPW['reproduction']['T_star_published'], *g))
    M('LNpCPgum', sci(pg, 1))
    M('LNGumRatio', '%.1f' % (pg / CPW['null_B_real_controls_gev']['p']))
except Exception as exc:                    # pragma: no cover
    print('gumbel skipped:', exc)
pr = CPW['control_discrimination']['ring_max_p_against_local_null']
M('LNpCPRing', sci(pr, 1))
M('LNCPRingRatio', '%.1f' % (pr / CPW['null_A']['p_local']))

# ---- R1-M12: the edge trim that actually ran -----------------------------
CPROW = [r for r in ROWS if r['star_name'] == 'CP-72 2713' and r['band'] == '7'
         and r['crossing'] == 'True'][0]
BASEBAND = 1.875                              # GHz, the ALMA baseband width
kept = abs(f(CPROW, 'fhi_GHz') - f(CPROW, 'flo_GHz'))
M('CpTrimPct', '%.0f' % (100 * (BASEBAND - kept) / BASEBAND / 2))
M('CpEdgeInsideMHz', '%.0f' % (1e3 * ((BASEBAND - kept) / 2)
                               + 1e-6 * 35 * f(CPROW, 'chanw_Hz')))

with open(OUT, 'w') as fh:
    fh.write('% Generated by v343_calc.py -- do not edit by hand.\n')
    fh.write('\n'.join(macros) + '\n')
print('%d macros (final) -> %s' % (len(macros), OUT))

# ---- R1-m4: the searched drift ceiling is not uniform --------------------
AM = sorted(f(r, 'a_max_m_s2') for r in ROWS)
DR = sorted(f(r, 'drift_max_Hz_s') / (0.5 * (f(r, 'flo_GHz') + f(r, 'fhi_GHz')))
            for r in ROWS)
M('AccelCeilLo', '%.2f' % AM[0])
M('AccelCeilHi', '%.2f' % AM[-1])
M('DriftCeilLo', '%.1f' % DR[0])
M('DriftCeilHi', '%.1f' % DR[-1])
M('NAccelPlanet', '%d' % sum(1 for x in AM if x > AM[0] + 0.01))

with open(OUT, 'w') as fh:
    fh.write('% Generated by v343_calc.py -- do not edit by hand.\n')
    fh.write('\n'.join(macros) + '\n')
print('%d macros -> %s' % (len(macros), OUT))
