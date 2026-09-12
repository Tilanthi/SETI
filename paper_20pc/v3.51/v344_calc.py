#!/usr/bin/env python3
"""Round-14 (v3.46, referee cycle 2) generated numbers.

Everything the three cycle-2 referee reports showed to be missing, wrong or
hand-typed is recomputed here from products shipped in this folder:

  per_target_results_v3.51.csv   the released catalogue (431 windows)
  archive_meta_v343.json         ALMA obscore + datalink harvest
  linecat_v343.json              Splatalogue query at the crossing frequencies
  pipeline_peakfreq_v342.json    per-window peak channel and >=5 sigma cell count

Output: survey_numbers_round14.tex.  Run after v343_calc.py.

Hand-typed constants, all quoted from a named source:
  MEDWIN = 65 and nb = max(2, n // MEDWIN)   seti_drift_search_generic.py:98-124
  belt peak radius 140 au                    Moor et al. (2020), AJ 159, 288
  CO molecular data (A_ul, g_u, E_u, B)      CDMS/JPL, as cited in the text
  assumed belt linewidth dV = 4 km/s         stated in the text as an assumption
"""
import csv, json, math
import statistics as st
from statistics import NormalDist

HERE = __file__.rsplit('/', 1)[0]
ROWS = list(csv.DictReader(open(HERE + '/per_target_results_v3.51.csv')))
META = json.load(open(HERE + '/archive_meta_v343.json'))
LC = json.load(open(HERE + '/linecat_v343.json'))
PK = json.load(open(HERE + '/pipeline_peakfreq_v342.json'))
OUT = HERE + '/survey_numbers_round14.tex'

N = len(ROWS)
assert N == 431, N
MOUS, EBS = META['mous'], META['ebs']
ND = NormalDist()
macros = []


def M(name, val):
    macros.append('\\newcommand{\\%s}{%s}' % (name, val))


def f(r, k):
    return float(r[k])


def ncell(r):
    nch = int(abs(f(r, 'fhi_GHz') - f(r, 'flo_GHz')) * 1e9 / f(r, 'chanw_Hz'))
    return nch * int(f(r, 'n_drift_trials'))


GAUSS5 = 2.8665e-7

# ================================================================= R1-N3
# The 5 sigma cell excess, decomposed into its two independent factors and
# then calibrated empirically on the control ensembles.  Correlation between
# adjacent cells cannot change E[number of cells above 5 sigma] = N p; it
# changes the clumping.  The window-level and cell-level factors are separate.
pw = {'fine': 0.0, 'coarse': 0.0}
cells = {'fine': 0, 'coarse': 0}
for r in ROWS:
    nc = ncell(r)
    cells[r['resolution_class']] += nc
    pw[r['resolution_class']] += 1.0 - (1.0 - GAUSS5) ** nc
TOT = cells['fine'] + cells['coarse']
EXPWIN = pw['fine'] + pw['coarse']
M('ExpCrossWin', '%.1f' % EXPWIN)
M('ExpCrossWinFine', '%.1f' % pw['fine'])
M('ExpCrossWinCoarse', '%.2f' % pw['coarse'])
M('CellsFineSci', '$%.2f\\times10^{%d}$' % (cells['fine'] / 1e7, 7))

CROSS = [r for r in ROWS if r['crossing'] == 'True']
FLAG = [r for r in CROSS if r['stage1_flag'] == 'True']
NREST = len(CROSS) - len(FLAG)
M('CrossWinRatio', '%.1f' % (NREST / EXPWIN))
# one-sided Poisson tail for the non-flag crossing count against expectation
tail = 1.0 - sum(math.exp(-EXPWIN) * EXPWIN ** k / math.factorial(k)
                 for k in range(NREST))
M('CrossWinPoisson', '%.2f' % tail)
NHITREST = sum(r['_nhit'] for r in CROSS if r['stage1_flag'] != 'True') \
    if '_nhit' in (CROSS[0] if CROSS else {}) else None
# cells per crossing window: iid expectation against observed
PKIDX = {}
for p in PK:
    PKIDX.setdefault((p['eb'], round(min(p['flo'], p['fhi']), 4)), p)


def nhit(r):
    key = (r['eb'], round(min(f(r, 'flo_GHz'), f(r, 'fhi_GHz')), 4))
    return PKIDX[key]['nhit']


obs_rest = sum(nhit(r) for r in CROSS if r['stage1_flag'] != 'True')
M('CellsPerCrossExp', '%.1f' % (TOT * GAUSS5 / EXPWIN))
M('CellsPerCrossObs', '%.1f' % (obs_rest / NREST))
M('CellsPerCrossRatio', '%.1f' % ((obs_rest / NREST) / (TOT * GAUSS5 / EXPWIN)))

# Empirical calibration on the controls: no Gaussian assumption survives it.
nobs = 0
eexp = 0.0
ratios, fo, fp, co, cp = [], [], [], [], []
for r in ROWS:
    nc = ncell(r)
    nctrl = int(f(r, 'n_control'))
    eexp += 1.0 - (1.0 - GAUSS5) ** (nc * nctrl)
    cm = f(r, 'ctrl_max_snr')
    if cm > 5.0:
        nobs += 1
    # median of the maximum of nc*nctrl iid standard normals
    pred = ND.inv_cdf(0.5 ** (1.0 / (nc * nctrl)))
    ratios.append(cm / pred)
    (fo if r['resolution_class'] == 'fine' else co).append(cm)
    (fp if r['resolution_class'] == 'fine' else cp).append(pred)
ratios.sort()
M('NCtrlWinObs', '%d' % nobs)
M('NCtrlWinExp', '%.0f' % eexp)
M('CtrlWinRatio', '%.2f' % (nobs / eexp))
M('CtrlWinAgreePct', '%.0f' % (100 * abs(nobs - eexp) / eexp))
M('CtrlMaxRatioMed', '%.3f' % st.median(ratios))
M('CtrlMaxRatioLo', '%.2f' % ratios[int(0.05 * len(ratios))])
M('CtrlMaxRatioHi', '%.2f' % ratios[int(0.95 * len(ratios))])
M('CtrlMaxFineObs', '%.2f' % st.median(fo))
M('CtrlMaxFinePred', '%.2f' % st.median(fp))
M('CtrlMaxCoarseObs', '%.2f' % st.median(co))
M('CtrlMaxCoarsePred', '%.2f' % st.median(cp))

# ================================================================= R1-N4
# The block-median baseline's first interpolation node is a block CENTRE.
MEDWIN = 65
CPB7 = [r for r in ROWS if r['star_name'].startswith('CP-72')
        and r['stage1_flag'] == 'True'][0]
# channel count and crossing channel index come from the pipeline's own
# per-window record, not from re-deriving them out of the frequency edges
_cpk = PKIDX[(CPB7['eb'], round(min(f(CPB7, 'flo_GHz'),
                                    f(CPB7, 'fhi_GHz')), 4))]
nch, ich = _cpk['nch'], _cpk['ch']
nb = max(2, nch // MEDWIN)
W = nch / nb
node1 = 0.5 * W
M('BaseNodeFirst', '%.1f' % node1)
M('CpNChan', '%d' % nch)
M('BaseBlockWidth', '%.1f' % W)
M('CpNodeDistChan', '%.1f' % (ich - node1))

# ================================================================= R1-N1, R3-A
# Epoch completeness: archive-complete in targets and tunings, not in epochs.
NPROG = sum(v['n_progenitor_ebs'] for v in MOUS.values())
NSRCH = sum(len(v['searched']) for v in MOUS.values())
M('NUnsearchedEB', '%d' % (NPROG - NSRCH))
M('PctEbSearched', '%.1f' % (100.0 * NSRCH / NPROG))
star_av, star_se = {}, {}
sys_av, sys_se = {}, {}
for r in ROWS:
    for k in (EBS.get(r['eb'], {}).get('member_ous') or []):
        star_av.setdefault(r['star_name'], set()).update(MOUS[k]['progenitors'])
        sys_av.setdefault(r['system_id'], set()).update(MOUS[k]['progenitors'])
    star_se.setdefault(r['star_name'], set()).add(r['eb'])
    sys_se.setdefault(r['system_id'], set()).add(r['eb'])
M('NStarMoreEB', '%d' % sum(1 for s in star_av
                            if len(star_av[s]) > len(star_se[s])))
M('MaxProgEBStar', '%d' % max(len(v) for v in star_av.values()))
M('MaxSearchedEBStar', '%d' % max(len(v) for v in star_se.values()))
M('NSysSingleEB', '%d' % sum(1 for s in sys_av if len(sys_av[s]) == 1))
M('NSysMultiEB', '%d' % sum(1 for s in sys_av if len(sys_av[s]) > 1))

# ---- R1-N2 / R2-N3 / R3-A(iii): the second public block on CP-72 2713's MOUS
CPM = 'uid://A001/X2d20/X2e25'
cpm = MOUS[CPM]
assert cpm['n_progenitor_ebs'] == 2 and len(cpm['searched']) == 1
unse = [p for p in cpm['progenitors'] if p not in cpm['searched']][0]
M('CpMous', CPM.replace('_', '\\_'))
M('CpEbSearched', cpm['searched'][0].replace('_', '\\_'))
M('CpEbUnsearched', unse.replace('_', '\\_'))
M('CpEbSearchedGB', '%.1f' % (cpm['sizes'][cpm['searched'][0]] / 1e9))
M('CpEbUnsearchedGB', '%.1f' % (cpm['sizes'][unse] / 1e9))

# ================================================================= R2-N2
# The CP-72 2713 debris belt: geometry, and CO limits from the shipped rms.
C = 2.99792458e8
H = 6.62607015e-34
KB = 1.380649e-23
PCM = 3.0856775814913673e16
MCO = (12.0 + 15.9949146) * 1.66053906660e-27
BROT = 57.6360e9                                    # CO rotational constant
DPC = float(CPB7['dist_pc'])
BELT_AU = 140.0                                     # Moor et al. (2020)
DV = 4.0e3                                          # assumed belt linewidth
M('BeltRadiusAu', '%d' % int(BELT_AU))
M('BeltRadiusArcsec', '%.1f' % (BELT_AU / DPC))
M('CoAssumedDVkms', '%d' % int(DV / 1e3))
M('CpRinAu', '%d' % round(f(CPB7, 'r_in_arcsec') * DPC))
M('CpRoutAu', '%d' % round(f(CPB7, 'r_out_arcsec') * DPC))

EB7 = EBS[CPB7['eb']]
M('CpBeamSeven', '%.2f' % EB7['s_resolution_arcsec'])
M('CpNantSeven', '%d' % EB7['n_ant'])
# the ACA Band 6 window covering CO(2-1)
CPB6 = [r for r in ROWS if r['star_name'].startswith('CP-72')
        and r['nearest_line'] == 'CO(2-1)'
        and r['resolution_class'] == 'fine'][0]
EB6 = EBS[CPB6['eb']]
M('CpBeamSix', '%.2f' % EB6['s_resolution_arcsec'])
M('CpBeamSixAu', '%d' % round(EB6['s_resolution_arcsec'] * DPC))
M('CpNantSix', '%d' % EB6['n_ant'])
M('CpArraySix', EB6['array'].replace('m', '\\,m'))


def int_limit(rms_mJy, chanw_Hz, nu):
    """3 sigma matched-width integrated flux limit, in Jy m/s."""
    dv = C * chanw_Hz / nu
    nchan = DV / dv
    return 3.0 * rms_mJy * 1e-3 * dv * math.sqrt(nchan), dv


def co_mass(int_Jy_ms, nu, aul, gu, eu, T):
    """Optically thin LTE CO mass, in kg."""
    Q = KB * T / (H * BROT) + 1.0 / 3.0
    xu = gu * math.exp(-eu / T) / Q
    flux = int_Jy_ms * 1e-26 * nu / C                 # W m^-2
    nph = 4.0 * math.pi * (DPC * PCM) ** 2 * flux / (H * nu)
    return nph / aul / xu * MCO


NU21, NU32 = 230.5380000e9, 345.7959899e9
I21, DV21 = int_limit(f(CPB6, 'rms_mJy'), f(CPB6, 'chanw_Hz'), NU21)
I32, DV32 = int_limit(f(CPB7, 'rms_mJy'), f(CPB7, 'chanw_Hz'), NU32)
# 1 Jy m/s = 1 mJy km/s, so the limits pass through unscaled
M('CoTwoOneLimMJy', '%.0f' % I21)
M('CoThreeTwoLimMJy', '%.1f' % I32)
m21lo = co_mass(I21, NU21, 6.910e-7, 5, 16.60, 20.0)
m21hi = co_mass(I21, NU21, 6.910e-7, 5, 16.60, 50.0)
M('CoMassLo', '%.1f' % (m21lo / 1e19))
M('CoMassHi', '%.1f' % (m21hi / 1e19))
M('CoMassEarthLo', '%.1f' % (m21lo / 5.9722e24 * 1e6))
M('CoMassEarthHi', '%.1f' % (m21hi / 5.9722e24 * 1e6))
M('CoTempLo', '20')
M('CoTempHi', '50')
# the baseline filter passband at the flagged window, in km/s
M('CpFilterKms', '%.0f' % (MEDWIN * f(CPB7, 'chanw_Hz') / NU32 * C / 1e3))
M('CpFilterMHz', '%.0f' % (MEDWIN * f(CPB7, 'chanw_Hz') / 1e6))

# ================================================================= R2-N1
# The excitation argument disposes of the two identified entries only.
TUBE = [e for e in LC['cp72']['at_corrected'] if e['in_tube']]
UNID = [e for e in TUBE if e['chem'] == 'UNIDENTIFIED']
IDENT = [e for e in TUBE if e['chem'] != 'UNIDENTIFIED']
assert len(TUBE) == 3 and len(UNID) == 1
M('NCpTubeIdent', '%d' % len(IDENT))
M('NCpTubeUnid', '%d' % len(UNID))
M('CpUnidQn', UNID[0]['qn'].replace('-', '$-$'))
M('CpUnidVstar', '%+.1f' % UNID[0]['v_star'])
M('CpUnidList', UNID[0]['linelist'])

# ================================================================= R1-M2/N5, R2-M3/N4
# Measurements on the retained dynamic spectrum.  Frozen input: the *.npz
# products are on the processing host, not in this folder (see the file's
# own _doc field and BUILD_NOTES.md).
CK = json.load(open(HERE + '/cp72_checks_v344.json'))
M('CpVarRatio', '%.3f' % CK['var_ratio_star_over_control_median'])
M('LNpCPstar', '$%.1f\\times10^{-3}$'
  % (CK['local_null_p_star_own_residual'] * 1e3))
M('CpSplitLo', '%.2f' % CK['split_half_T_first'])
M('CpSplitHi', '%.2f' % CK['split_half_T_second'])
M('CpSplitExp', '%.2f' % CK['split_half_T_expected'])
M('CpSplitSigma', '%.1f' % CK['split_half_sigma_difference'])
M('CpNInt', '%d' % CK['n_int'])
M('CpContMjy', '%.2f' % CK['continuum_per_int_mJy'])
M('CpContErrMjy', '%.2f' % CK['continuum_per_int_err_mJy'])
M('CpContThreeSig', '%.2f' % CK['continuum_three_sigma_mJy'])
M('AuMicFlareLo', '%.1f' % CK['aumic_flare_mJy'][0])
M('AuMicFlareHi', '%.1f' % CK['aumic_flare_mJy'][1])
M('CpBandpassEps', '%d' % CK['bandpass_epsilon_required'])

# ================================================================= R1-N7
# ACA geometry: two consequences the disclosure paragraph did not carry.
import numpy as np


def mean_gain(a, b):
    rr = np.linspace(a, b, 600)
    return float((np.exp(-4 * np.log(2) * rr * rr) * rr).sum() / rr.sum())


DR = 12.0 / 7.0
gac, g12 = [], []
for r in ROWS:
    arr = EBS[r['eb']]['array']
    sc = DR if arr == '7m' else 1.0
    g = mean_gain(f(r, 'r_in_arcsec') / (f(r, 'theta_pb_arcsec') * sc),
                  f(r, 'r_out_arcsec') / (f(r, 'theta_pb_arcsec') * sc))
    (gac if arr == '7m' else g12).append(g)
M('AcaAnnGain', '%.2f' % st.median(gac))
M('AcaAnnFracLo', '%.2f' % min(f(r, 'r_in_arcsec') / (f(r, 'theta_pb_arcsec') * DR)
                               for r in ROWS if EBS[r['eb']]['array'] == '7m'))
M('AcaAnnFracHi', '%.2f' % max(f(r, 'r_out_arcsec') / (f(r, 'theta_pb_arcsec') * DR)
                               for r in ROWS if EBS[r['eb']]['array'] == '7m'))
HI = [r for r in ROWS if f(r, 'smin_mJy') / (5 * f(r, 'rms_mJy')) > 1.02]
M('NPbHiTwelve', '%d' % sum(1 for r in HI if EBS[r['eb']]['array'] == '12m'))
M('NPbHiSeven', '%d' % sum(1 for r in HI if EBS[r['eb']]['array'] == '7m'))
M('AcaCorrShown', '1.05')
M('AcaCorrTrue', '%.3f' % 1.05 ** (1.0 / DR ** 2))

# R2-M6 residual: the HD 48370 13CO ring offsets, in beams.
HD = [r for r in ROWS if r['star_name'].startswith('HD 48370')
      and r['stage1_flag'] == 'True'][0]
HDBEAM = EBS[HD['eb']]['s_resolution_arcsec']
M('HdBeamArcsec', '%.2f' % HDBEAM)


def _m(name):
    for line in open(HERE + '/survey_numbers_round12.tex'):
        if '\\%s}' % name in line:
            return float(line.split('{')[-1].split('}')[0])
    for fn in ('survey_numbers.tex', 'survey_numbers_round8.tex',
               'survey_numbers_round9.tex', 'survey_numbers_round13.tex'):
        for line in open(HERE + '/' + fn):
            if '\\%s}' % name in line:
                return float(line.split('{')[-1].split('}')[0])
    raise KeyError(name)


M('HdCoOffsetBeams', '%.1f' % (_m('HdThirteenOffset') / HDBEAM))
M('HdCoTopBeamsLo', '%.1f' % (_m('HdThirteenTopLo') / HDBEAM))
M('HdCoTopBeamsHi', '%.1f' % (_m('HdThirteenTopHi') / HDBEAM))

# R1-m3: the 431 rows reduce to this many distinct (EB, spectral window) datasets.
M('NDistinctDatasets', '%d' % len({(r['eb'], r['flo_GHz'], r['fhi_GHz'])
                                   for r in ROWS}))

# R1-m4: the compounded worst-case threshold multiplier.
WORST = max((1.0 / f(r, 'eta_smear')) for r in ROWS)
M('CompoundWorst', '%.1f' % (WORST * 2.6667))

# ================================================================= misc
# R3-E: the Band 3 fraction of the Wright et al. haystack frequency axis.
HAYSTACK_GHZ = 115.0
# \UnionBandThree is generated in round 13; recompute the fraction from it
u3 = None
for line in open(HERE + '/survey_numbers_round13.tex'):
    if '\\UnionBandThree}' in line:
        u3 = float(line.split('{')[-1].split('}')[0])
assert u3 is not None
M('UnionBandThreeFrac', '%.2f' % (u3 / HAYSTACK_GHZ))

# R2 minor 1: the searched sample as a fraction of the reference census.
NSTARS = len({r['star_name'] for r in ROWS})
M('PctSampleOfCensus', '%.2f' % (100.0 * NSTARS / 17566))

with open(OUT, 'w') as fh:
    fh.write('% Generated by v344_calc.py -- do not edit by hand.\n')
    fh.write('\n'.join(macros) + '\n')
print('%d macros -> %s' % (len(macros), OUT))
