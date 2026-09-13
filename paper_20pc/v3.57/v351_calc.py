#!/usr/bin/env python3
"""v3.54 generator -> survey_numbers_round19.tex

Single-sources the quantitative blocks this round adds, so nothing below is
hand-typed into the manuscript.

  (1) The spectral-response-corrected threshold as the PRINCIPAL physical
      number (referees C3 and D2).  The nominal 5 sigma value stays the
      pipeline trigger P_trig; the effective unresolved-carrier threshold is
      P_eff = P_trig / f_peak, with f_peak the fraction of a sub-channel
      tone's power left in the peak channel by ALMA's online Hanning
      smoothing.  The median over uniform sub-channel placement is the
      principal factor (HanFacMed, 2.29); the 2.00-2.67 envelope is the
      spread over placement and is retained.  Every quantity a transmitter
      power is compared against is re-derived on P_eff here, including the
      Arecibo-class benchmark, where the correction changes the answer.

  (2) The held-out validation set, updated to the campaign as it stands at
      build time (referees C-major-4, D4 and D7, and the author's
      instruction).  Read from heldout_v351.json, which was read read-only
      from the processing host; the campaign is still running.

  (3) The star-versus-control residual variance R_sigma (referee D3), from
      rsigma_v351.json, measured on the retained per-integration products of
      the four stage-1 windows.  Eight controls per window is all the release
      keeps, so what these numbers can and cannot establish is emitted here
      as well: the star-side excess needed to retire the CP-72 2713 margin,
      against the bound the eight controls support.

  (4) The false-alarm arithmetic worked through (referee C2): the
      correlation-corrected effective trial count derived from the Hanning
      autocorrelation and the drift-grid oversampling rather than asserted,
      the decomposition of the residual cell excess, its Poisson consistency,
      and where the factor of 16 behind the survey-wide Bonferroni scale
      comes from, connected to N_eff.

  (5) The polarisation census (referee C5): what fraction of the 102 searched
      execution blocks the archive delivers with both parallel hands.

Inputs (all frozen, all in this directory):
  heldout_v351.json             the epoch-extension search products
  rsigma_v351.json              the D3 residual-variance measurement
  polstates_v351.json           ivoa.obscore pol_states per execution block
  per_target_results_v3.52.csv  the released catalogue (431 windows)
  survey_numbers*.tex           for values already single-sourced elsewhere
"""
import collections
import datetime
import csv
import json
import math
import os
import re
import statistics as st

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = []


def M(name, value):
    OUT.append(r'\newcommand{\%s}{%s}' % (name, value))


def texval(fn, macro):
    """Read a value back out of an already-generated macro file."""
    s = open(os.path.join(HERE, fn)).read()
    m = re.search(r'\\newcommand\{\\%s\}\{(.*?)\}\s*$' % macro, s, re.M)
    if not m:
        raise SystemExit('%s not found in %s' % (macro, fn))
    return m.group(1)


def sci(x, sf=2):
    e = int(math.floor(math.log10(abs(float(x)))))
    m = float(x) / 10 ** e
    return r'%.*f\times10^{%d}' % (sf - 1, m, e)


ROWS = list(csv.DictReader(open(os.path.join(HERE, 'per_target_results_v3.52.csv'))))
F = float

# =====================================================================
# (1) The spectral-response-corrected threshold as the principal number
# =====================================================================
# Hanning kernel (1/4, 1/2, 1/4) applied to a delta-function tone at
# sub-channel offset u.  Identical arithmetic to v342_calc.py section C; the
# factors are read back from its output so the two cannot drift apart.
HAN_MED = 1.0 / float(texval('survey_numbers_round12.tex', 'HanFacMed'))
HAN_FAC_MED = float(texval('survey_numbers_round12.tex', 'HanFacMed'))
HAN_FAC_BEST = float(texval('survey_numbers_round12.tex', 'HanFacBest'))
HAN_FAC_WORST = float(texval('survey_numbers_round12.tex', 'HanFacWorst'))

for tag, cls in (('A', 'fine'), ('B', 'coarse')):
    e = sorted(F(r['eirp_nominal_W']) for r in ROWS if r['resolution_class'] == cls)
    M('EirpEffMin' + tag, sci(e[0] * HAN_FAC_MED))
    M('EirpEffMed' + tag, sci(st.median(e) * HAN_FAC_MED))
    M('EirpEffMax' + tag, sci(e[-1] * HAN_FAC_MED))

_alle = sorted(F(r['eirp_nominal_W']) for r in ROWS)
M('EirpEffMedian', sci(st.median(_alle) * HAN_FAC_MED))
M('EirpEffDeepest', sci(_alle[0] * HAN_FAC_MED))

# Detectability cases, recomputed on P_eff.  The class restriction and the
# case powers are those of v342_calc.py section E, so only the threshold
# definition changes.
BYSYS = collections.defaultdict(list)
for r in ROWS:
    BYSYS[r['system_id']].append(r)
_deepc = {s: min([F(r['eirp_nominal_W']) for r in rs
                  if r['resolution_class'] == 'coarse'] or [float('inf')])
          for s, rs in BYSYS.items()}
_deepc_eff = {s: v * HAN_FAC_MED for s, v in _deepc.items()}
_CASEI = 1.62e13
# reproduce the nominal published values before quoting the corrected ones
assert sum(1 for v in _deepc.values() if v <= _CASEI) == 1
assert sum(1 for v in _deepc.values() if v <= 2 * _CASEI) == 2
AREC = 2.0e13                       # Arecibo-class total power, Sec. 4.3
M('CaseDetEffArec', '%d' % sum(1 for v in _deepc_eff.values() if v <= AREC))
M('CaseDetEffArecTwo', '%d' % sum(1 for v in _deepc_eff.values() if v <= 2 * AREC))
M('AreciboW', sci(AREC))
# the 12 m / 1 MW geometric benchmark of Sec. 4.3 against the effective median
BENCH = 8.0e14
_medA_eff = st.median([F(r['eirp_nominal_W']) for r in ROWS
                       if r['resolution_class'] == 'fine']) * HAN_FAC_MED
M('BenchEffRatio', '%.1f' % (_medA_eff / BENCH))

# =====================================================================
# (2) The held-out validation set, at build time
# =====================================================================
HO = json.load(open(os.path.join(HERE, 'heldout_v352.json')))
W = HO['windows']
CAMP = HO['campaign_status']
# Three dispositions, not two.  v3.51 split the campaign on the raw detection
# flag and described every detection as a beta Pictoris CO window, which was
# true of the 28 windows it then had.  The enlarged campaign holds detections
# that are neither CO nor spatial outliers, and one window that is a stage-1
# spatial outlier with no astrophysical attribution, so the classification is
# carried in the frozen record (refresh_campaign_v352.py) and read from it.
det = [w for w in W if w['line_attributed']]
odd = [w for w in W if w['unattributed_stage1']]
sub = [w for w in W if w['detection'] and not w['line_attributed']
       and not w['unattributed_stage1']]
nul = [w for w in W if not w['detection']]
assert len(det) + len(odd) + len(sub) + len(nul) == len(W)
M('HOWindows', '%d' % len(W))
M('HOBlocks', '%d' % CAMP['blocks_searched'])
M('HOStars', '%d' % CAMP['stars'])
M('HOCoWin', '%d' % len(det))
M('HOSubWin', '%d' % len(sub))
M('HONoiseWin', '%d' % len(nul))
M('HOFailCal', '%d' % CAMP['blocks_failed_calibration'])
M('HORunning', '%d' % CAMP['blocks_in_progress'])
# Derived, not typed.  v3.51 hard-set this count to a literal 2 with the two
# star names typed into the manuscript, so a refresh of the campaign printed
# the wrong pair over the new counts (referee F4).
M('HONewStars', '%d' % CAMP['new_star_blocks'])
M('HONewStarCount', '%d' % CAMP['new_star_count'])
_nsl = [s.replace(' ', '~') for s in CAMP['new_star_list']]
M('HONewStarList', ', '.join(_nsl[:-1]) + ' and ' + _nsl[-1])

# T_star of the CO detections, and the null rank distribution
M('HOCoTLo', '%.1f' % min(w['star_peak_snr'] for w in det))
M('HOCoTHi', '%.1f' % max(w['star_peak_snr'] for w in det))
M('HOSubCtrlHi', '%.0f' % max(w['control_peak_snr'] for w in sub))
pn = sorted(w['p_star_empirical'] for w in nul)
pa = sorted(w['p_star_empirical'] for w in W)
M('HONoiseMedP', '%.2f' % st.median(pn))


def ks_uniform(p):
    """Two-sided one-sample KS statistic against U(0,1), and its asymptotic
    p-value; scipy is used where available and the closed form otherwise."""
    n = len(p)
    x = sorted(p)
    d = max(max((i + 1) / n - v, v - i / n) for i, v in enumerate(x))
    try:
        from scipy import stats
        return d, float(stats.kstest(x, 'uniform').pvalue)
    except Exception:
        lam = (math.sqrt(n) + 0.12 + 0.11 / math.sqrt(n)) * d
        s = 2 * sum((-1) ** (k - 1) * math.exp(-2 * k * k * lam * lam)
                    for k in range(1, 100))
        return d, max(0.0, min(1.0, s))


d0, p0 = ks_uniform(pn)
d1, p1 = ks_uniform(pa)
M('HOKsD', '%.2f' % d0)
M('HOKsP', '%.2f' % p0)
M('HOKsDAll', '%.2f' % d1)
M('HOKsPAll', '%.2f' % p1)
M('HONoiseStageOne', '%d' % sum(1 for w in nul
                                if w['n_control_ge_star'] == 0))

# Windows inside one execution block share a calibration and blocks of one
# member observing unit set share a target, so the window-level figure treats
# as independent what is not.  The clustered version takes one median rank per
# star, the coarsest grouping the campaign supports.  Both are reported: the
# difference between them is the size of the dependence, and quoting only the
# first would overstate the evidence in the way this paper criticises
# elsewhere.
_bystar = collections.defaultdict(list)
for w in nul:
    _bystar[w['star']].append(w['p_star_empirical'])
_starp = sorted(st.median(v) for v in _bystar.values())
d2, p2 = ks_uniform(_starp)
M('HONullStars', '%d' % len(_starp))
M('HOKsDStar', '%.2f' % d2)
M('HOKsPStar', '%.2f' % p2)
M('HOMedPStar', '%.2f' % st.median(_starp))
M('HOFracLoPct', '%.0f' % (100.0 * sum(1 for x in pn if x < 0.1) / len(pn)))
M('HOFracHiPct', '%.0f' % (100.0 * sum(1 for x in pn if x > 0.9) / len(pn)))

_asof = datetime.datetime.strptime(CAMP['as_of_utc'], '%Y-%m-%dT%H:%M:%SZ')
M('HOAsOf', _asof.strftime('%Y %B %-d, %H:%M') + r'\,UTC')

# =====================================================================
# (3) Star-versus-control residual variance, referee D3
# =====================================================================
RS = json.load(open(os.path.join(HERE, 'rsigma_v351.json')))
BYW = {r['window']: r for r in RS['windows']}
NAMES = (('CP-72_2713_B7', 'RsigCP'), ('HD_48370_B6', 'RsigHD'),
         ('bet_Pic_B3', 'RsigBpThree'), ('bet_Pic_B6', 'RsigBpSix'))
vals = []
for key, macro in NAMES:
    r = BYW[key]
    M(macro, '%.3f' % r['R_sigma'])
    vals.append(r['R_sigma'])
M('RsigLo', '%.3f' % min(vals))
M('RsigHi', '%.3f' % max(vals))
M('RsigNCtrl', '%d' % len(BYW['CP-72_2713_B7']['sigma_ctrl']))
# the spread among the eight retained controls, as a percentage of their
# median, worst case over the four windows: this is what limits the test
M('RsigCtrlSpreadPct', '%.1f' % max(
    100.0 * (max(r['sigma_ctrl']) - min(r['sigma_ctrl'])) / r['sigma_ctrl_median']
    for r in RS['windows']))
# a two-sided 95 per cent bound on any star-side broadband excess, from the
# eight control scales alone (Student t on their scatter)
try:
    from scipy import stats as _sst
    tcrit = float(_sst.t.ppf(0.975, 7))
except Exception:
    tcrit = 2.365
bounds = []
for r in RS['windows']:
    s = r['sigma_ctrl']
    sem = st.stdev(s) / math.sqrt(len(s))
    bounds.append(100.0 * (abs(r['R_sigma'] - 1.0) + tcrit * sem / r['sigma_ctrl_median']))
M('RsigBoundPct', '%.1f' % max(bounds))
# what a star-side excess would have to be to erase the CP-72 2713 margin:
# T_star scales as 1/sigma_star, so T_star/R must fall below the ring maximum
# T_star and the ring maximum for CP-72 2713 come from the local-null
# reproduction, which reproduced the published values bit for bit before any
# null was drawn (localnull_code/res_0.json), so they are not hand-typed.
_ln = json.load(open(os.path.join(HERE, 'localnull_code', 'res_0.json')))
assert _ln['target'] == 'CP-72_2713_B7'
CP_T = float(_ln['T_star_reproduced'])
CP_RING = float(_ln['ring_max_published'])
M('RsigNeedCPPct', '%.1f' % (100.0 * (CP_T / CP_RING - 1.0)))

# =====================================================================
# (4) The false-alarm arithmetic, worked through (referee C2)
# =====================================================================
RHO1 = float(texval('survey_numbers_round16.tex', 'HanRhoOne'))
RHO2 = float(texval('survey_numbers_round16.tex', 'HanRhoTwo'))
FREQ_OVER = 1.0 + 2.0 * RHO1 + 2.0 * RHO2
DRIFT_OVER = 2.0                    # DRIFT_STEP_DIV in the extraction code:
#                                     two grid points per channel of traverse
M('FaFreqOver', '%.2f' % FREQ_OVER)
M('FaDriftOver', '%.0f' % DRIFT_OVER)
# v347_calc.py now derives the same product for the corrected trial count, so
# the two must agree to the printed precision or one of them is wrong.
assert abs(float(texval('survey_numbers_round16.tex', 'FaOverCount'))
           - round(FREQ_OVER * DRIFT_OVER, 1)) < 1e-9

# Poisson consistency of the residual window-level excess.  v344_calc.py
# already emits CrossWinPoisson from the same formula, so it is checked
# against that value here and not re-emitted.
MU = float(texval('survey_numbers_round14.tex', 'ExpCrossWin'))
NOBS = int(texval('survey_numbers_round13.tex', 'NHitWindowsRest'))
tail = 1.0 - sum(math.exp(-MU) * MU ** k / math.factorial(k) for k in range(NOBS))
_have = float(texval('survey_numbers_round14.tex', 'CrossWinPoisson'))
assert abs(_have - round(tail, 2)) < 1e-9, (_have, tail)

# where the factor of 16 comes from, and what N_eff does to it
ALPHA = 0.05
NWIN = len(ROWS)
BONF = ALPHA / NWIN
M('BonfAlpha', '%.2f' % ALPHA)
M('BonfNWin', '%d' % NWIN)
M('BonfScaleCalc', sci(BONF))
NEFF_LO, NEFF_HI = 30, 43
M('BonfGapEffLo', '%.0f' % ((1.0 / (NEFF_HI + 1)) / BONF))
M('BonfGapEffHi', '%.0f' % ((1.0 / (NEFF_LO + 1)) / BONF))
M('RankEffLo', '%.3f' % (1.0 / (NEFF_HI + 1)))
M('RankEffHi', '%.3f' % (1.0 / (NEFF_LO + 1)))

# =====================================================================
# (5) Polarisation census, referee C5
# =====================================================================
POL = json.load(open(os.path.join(HERE, 'polstates_v351.json')))
both = sum(1 for v in POL.values() if all('XX' in s and 'YY' in s for s in v))
M('NPolEB', '%d' % len(POL))
M('NPolBoth', '%d' % both)

# =====================================================================
# (6) Statistical units, referee D9
# =====================================================================
M('NEbSpwUnits', '%d' % len({(r['eb'], round(F(r['flo_GHz']), 4),
                              round(F(r['chanw_Hz']), 1)) for r in ROWS}))


# =====================================================================
# (7) Which configuration axis dominates the mismatch (referee C, minor)
# =====================================================================
_cfgN = int(texval('survey_numbers_round18.tex', 'CfgNA'))
for ax in ('Band', 'Chan', 'OnSrc', 'Drift', 'Off'):
    _in = int(texval('survey_numbers_round18.tex', 'Cfg%sIn' % ax))
    M('Cfg%sOut' % ax, '%d' % (_cfgN - _in))

open(os.path.join(HERE, 'survey_numbers_round19.tex'), 'w').write(
    '%% GENERATED by v351_calc.py -- do not hand-edit.\n' + '\n'.join(OUT) + '\n')
print('\n'.join(OUT))
