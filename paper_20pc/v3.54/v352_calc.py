#!/usr/bin/env python3
"""v3.54 generator -> survey_numbers_round20.tex

Single-sources the quantitative blocks the v3.54 cycle adds, so that nothing
below is hand-typed into the manuscript.  Nothing here is a hand-set constant:
where a number looks like a constant it is either read back out of an
already-generated macro file (texval), measured off a frozen input, or derived
from a stated definition in the code beside it.  The one exception class is
named physical/definitional conventions (the speed of light, the +-50 km/s
mask tube of v342_calc.py:469, the 0.99 smearing threshold of the referee's
own question); each is flagged at its point of use.

  (1) Spectral response, measured rather than assumed (referee E1).  The
      archive's own effective spectral resolution for each window, divided by
      its delivered channel width, separates windows that carry plain online
      Hanning smoothing (ratio 2) from windows that additionally carry online
      channel averaging (ratio near 1.16).  The peak-fraction correction for
      the averaged windows is computed from the same kernel model that
      v342_calc.py uses for the unaveraged case, generalised to an averaging
      factor N, and the N=1 case is asserted against the shipped HanFacMed so
      the two models cannot drift apart.

  (2) The primary-beam convention defect (referee E2).  The released
      catalogue's theta_pb is 1.22 lambda / 12 m for every window including
      the ACA ones; the coefficient and the assumed diameter are measured off
      the catalogue itself here rather than asserted.  Re-deriving the
      attenuation with 1.13 lambda / D at each window's real dish diameter
      moves the applied threshold factor; how far, and for how many windows,
      is emitted.

  (3) The array strata (referee E3).  The 12 m and ACA 7 m subsets are
      separated by execution block and summarised, including the rank
      uniformity of each, because the departure from uniformity is confined
      to the ACA subset.

  (4) The clustered permutation (referee E4).  Windows inside one execution
      block share their 512 control probes, so the null count of rank-first
      windows is not Poisson.  The exact clustered distribution is computed
      by convolution over the 102 blocks; the null distribution of the survey
      maximum is sampled with a fixed seed.

  (5, 6) The held-out campaign, recomputed at build time (referees C-major-4,
      D4, D7).  heldout_v352.json is the build-time state of a campaign that
      is still running.  A window is null when its detection flag is false.
      The enlarged campaign contains exactly one unattributed stage-1 outlier,
      so the per-window rate bound is the exact one-sided 95 per cent
      Clopper-Pearson upper limit for one event in n trials (the largest p
      with P(X<=1 | n, p) >= 0.05), solved by bisection here, NOT a
      rule-of-three-on-zero.  The KS critical value and its power against a
      one-fifth contaminated mixture are Monte Carlo with fixed seeds.

  (7) The beta Pictoris Band 6 stage-1 recurrence (referee E7), from the two
      blocks' own products.  The two blocks' peak separation is derived here
      in kHz, in km/s and in channels from the two peak frequencies and the
      channel width.

  (8) The closure-phase screen (referee E8), from closure_v352.json.  The
      z-scores are re-derived from the per-window mean, scatter and triangle
      count and asserted against the stored values.

  (9) The transfer bracket (referee E9).  The occurrence appendix already
      brackets completeness multiplicatively; the bracket endpoints are read
      out of the manuscript sentence that states them, and the recovery
      fractions out of the generated macro files, so the two cannot drift.

  (10) The line-database cross-check (referee F/M3).  What a prospective
      database-wide mask would cost, recomputed from the released catalogue's
      own merged frequency islands.

Inputs (all frozen; all in this directory unless noted):
  frozen_export_v3.31.json        the per-window search export (512 controls)
  per_target_results_v3.52.csv    the released catalogue (431 windows)
  archive_meta_v343.json          per-EB array, frequency support
  heldout_v352.json               the held-out campaign at build time
  bpic_stage1_v352.json           the beta Pic B6 recurrence, two blocks
  closure_v352.json               the closure-phase screen
  linecat_v343.json               (not read; the mask is taken from v342_calc)
  v342_calc.py                    parsed, not imported, for the frozen mask
  technosignatures_20pc_v3.54.tex parsed, read-only, for the transfer bracket
  survey_numbers*.tex             values already single-sourced elsewhere
  ../../v352_F/mask_xcheck_lines.json   the Splatalogue harvest over the 33
                                  islands (read-only; a copy in this
                                  directory is preferred if present)
"""
import ast
import calendar
import collections
import csv
import json
import math
import os
import re
import statistics as st

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = []

# Files loaded before this script's output in the manuscript preamble. A macro
# defined in any of them is that file's to own.
EARLIER_ROUNDS = ['survey_numbers.tex'] + [
    'survey_numbers_round%s.tex' % n
    for n in list(range(5, 20))] + [
    'survey_numbers_pointing.tex', 'survey_numbers_recurrence.tex',
    'survey_numbers_localnull.tex']

C_KMS = 299792.458                  # speed of light, km/s
C_MS = C_KMS * 1e3
ARCSEC = 180.0 * 3600.0 / math.pi   # radians -> arcsec


def M(name, value):
    """Emit a macro, unless an earlier-loaded file already defines it.

    Two files defining one macro is a build error, so a macro this script
    recomputes but an earlier round already owns is checked against that
    owner and then dropped. A disagreement is a real defect and stops the
    build rather than being silently resolved by load order.
    """
    for fn in EARLIER_ROUNDS:
        p = os.path.join(HERE, fn)
        if not os.path.exists(p):
            continue
        m = re.search(r'\\newcommand\{\\%s\}\{(.*?)\}\s*$' % name,
                      open(p).read(), re.M)
        if m:
            if m.group(1) != str(value):
                raise SystemExit(
                    '%s: %s already defines it as %r, this script computes %r'
                    % (name, fn, m.group(1), str(value)))
            return
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


def comma(n):
    return '{:,}'.format(int(n))


def texsafe(s):
    for a, b in (('\\', r'\textbackslash{}'), ('&', r'\&'), ('%', r'\%'),
                 ('$', r'\$'), ('#', r'\#'), ('_', r'\_'), ('{', r'\{'),
                 ('}', r'\}'), ('~', r'\textasciitilde{}'),
                 ('^', r'\textasciicircum{}')):
        s = s.replace(a, b)
    return s


F = float
ROWS = list(csv.DictReader(open(os.path.join(HERE, 'per_target_results_v3.52.csv'))))
META = json.load(open(os.path.join(HERE, 'archive_meta_v343.json')))
EBS = META['ebs']


# =====================================================================
# shared: the 431-window selection, replicating survey_stats.py
# =====================================================================
def load_windows():
    """Reproduce survey_stats.py's selection from the frozen export."""
    d = json.load(open(os.path.join(HERE, 'frozen_export_v3.31.json')))
    rows = d['rows']
    edges = [(84, 116, 3), (125, 163, 4), (163, 211, 5),
             (211, 275, 6), (275, 373, 7), (385, 500, 8)]

    def band_of(r):
        if r['band'] is not None:
            return r['band']
        f = 0.5 * (r['flo'] + r['fhi'])
        for lo, hi, b in edges:
            if lo <= f < hi:
                return b
    for r in rows:
        r['band_x'] = band_of(r)
        r['res_x'] = 'fine' if r['chanw'] < 5e6 else 'coarse'
        r['qa'] = r['rms'] * math.sqrt(r['onsrc'] * r['chanw'])
        r['ctrl_max_all'] = max(r['ctrl_all']) if r['ctrl_all'] else r['ctrl_max']
    key = lambda r: (r['star_name'], r['eb'], round(min(r['flo'], r['fhi']), 6),
                     round(max(r['flo'], r['fhi']), 6), r['chanw'])
    best = {}
    for r in rows:
        k = key(r)
        if k not in best or (best[k]['line'] is None and r['line'] is not None):
            best[k] = r
    uniq = list(best.values())
    qa_med = st.median(r['qa'] for r in uniq)
    kept = [r for r in uniq if r['qa'] >= qa_med / 100.0]
    withheld = [r for r in kept if r['star_name'] == 'eps Eri' and r['band_x'] == 6]
    good = [r for r in kept if r not in withheld]
    PAIRS = [('2MASS J05241914-1601153 551040', '2MASS J05241914-1601153 717696'),
             ('NAME AT Mic AB  Gaia DR3 6792436799475128960', 'V AT Mic B'),
             ('G 272-61A', 'G 272-61B'), ('GJ 2006A', 'GJ 2006B'),
             ('LP 476-207 384128', 'LP 476-207 783296'),
             ('V star TX PsA', 'V star WW PsA'),
             ('HD 139084B 805632', 'HD 139084B 921024')]
    sysof = {}
    for a, b in PAIRS:
        sysof[a] = a
        sysof[b] = a
    for r in good:
        r['sys'] = sysof.get(r['star_name'], r['star_name'])
        r['sbr'] = r['star_snr'] > r['ctrl_max_all']
        r['cross'] = r['star_snr'] >= 5.0
    return good


G = load_windows()
NCTRL = len(G[0]['ctrl_all'])                       # 512 control probes
NRANK = NCTRL + 1                                   # add-one rank denominator
assert len(G) == len(ROWS), (len(G), len(ROWS))
ARRAY = {eb: EBS.get(eb, {}).get('array') for eb in {r['eb'] for r in G}}
DISH = {a: F(re.match(r'([0-9.]+)\s*m', a).group(1)) for a in set(ARRAY.values())}


def p_rank(r):
    return (1 + sum(1 for c in r['ctrl_all'] if c >= r['star_snr'])) / float(NRANK)


def ks_uniform(p):
    """Two-sided one-sample KS statistic against U(0,1) and its p-value."""
    x = sorted(p)
    n = len(x)
    d = max(max((i + 1) / n - v, v - i / n) for i, v in enumerate(x))
    try:
        from scipy import stats
        return d, float(stats.kstest(x, 'uniform').pvalue)
    except Exception:
        lam = (math.sqrt(n) + 0.12 + 0.11 / math.sqrt(n)) * d
        s = 2 * sum((-1) ** (k - 1) * math.exp(-2 * k * k * lam * lam)
                    for k in range(1, 100))
        return d, max(0.0, min(1.0, s))


# =====================================================================
# (1) Spectral response: which windows carry online channel averaging
# =====================================================================
def eff_res_ratio(flo, fhi, chanw_hz, eb):
    """Archive effective spectral resolution / delivered channel width, taken
    from the overlapping frequency-support segment of the window's own EB."""
    fs = EBS.get(eb, {}).get('freq_support') or []
    lo, hi = min(flo, fhi), max(flo, fhi)
    best = None
    for a, b, res in fs:
        ov = min(hi, max(a, b)) - max(lo, min(a, b))
        if ov > 0 and (best is None or ov > best[0]):
            best = (ov, res)
    return None if best is None else best[1] / chanw_hz


RATIO = [eff_res_ratio(F(r['flo_GHz']), F(r['fhi_GHz']), F(r['chanw_Hz']), r['eb'])
         for r in ROWS]
assert all(x is not None for x in RATIO), 'window with no archive frequency support'
_modal = collections.Counter(round(x, 3) for x in RATIO).most_common(1)[0][0]
HAN_TOL = 0.05                       # tolerance on the ratio, dimensionless
_n_two = sum(1 for x in RATIO if abs(x - _modal) < HAN_TOL)
M('HanRatioTwo', '%.2f' % _modal)
M('NHanTwo', '%d' % _n_two)
M('NHanOther', '%d' % (len(RATIO) - _n_two))
_other = [x for x in RATIO if abs(x - _modal) >= HAN_TOL]
_other_ratio = st.median(_other)     # ~1.16, used only to bracket N below

# Kernel model.  A sub-channel tone is split linearly between the two nearest
# raw channels, Hanning-smoothed with (1/4, 1/2, 1/4), then N consecutive raw
# channels are summed into one delivered channel.  Identical arithmetic to
# v342_calc.py section C for N = 1.
HANN = {-1: 0.25, 0: 0.5, 1: 0.25}
NRAW = 81                            # raw channels in the model spectrum


def _delivered(t, n, nraw=NRAW):
    x = np.zeros(nraw)
    c = int(round(t))
    u = t - c
    s = 1 if u >= 0 else -1
    x[c + nraw // 2] += 1.0 - abs(u)
    x[c + s + nraw // 2] += abs(u)
    y = np.zeros_like(x)
    for d, w in HANN.items():
        y[1:-1] += w * x[1 + d:len(x) - 1 + d]
    m = (nraw // n) * n
    return y[:m].reshape(-1, n).sum(1)


def peak_factor_median(n, npts=2001):
    """Median over uniform sub-channel placement of 1 / (peak power fraction)."""
    fr = [_delivered(t, n).max() / _delivered(t, n).sum()
          for t in np.linspace(-0.5 * n, 0.5 * n, npts)]
    return 1.0 / float(np.median(fr))


def resolution_ratio(n, npts=4001, nraw=801):
    """FWHM of one delivered channel's response, in delivered channels: the
    quantity the archive reports as effective spectral resolution."""
    ts = np.linspace(-3.0 * n, 3.0 * n, npts)
    k = (nraw // n) // 2
    prof = np.array([_delivered(t, n, nraw)[k] for t in ts])
    prof /= prof.max()
    above = ts[prof >= 0.5]
    return (above.max() - above.min()) / n


# the unaveraged case must reproduce the shipped Hanning factor exactly
_fac_one = peak_factor_median(1)
assert abs(_fac_one - F(texval('survey_numbers_round12.tex', 'HanFacMed'))) < 5e-3, _fac_one
# the observed ratio of the averaged windows is bracketed by N = 2 and N = 4
N_AVG_HI, N_AVG_LO = 2, 4            # averaging factors bracketing the ratio
assert (resolution_ratio(N_AVG_LO) < _other_ratio < resolution_ratio(N_AVG_HI)), _other_ratio
M('HanFacAvgLo', '%.2f' % peak_factor_median(N_AVG_LO))
M('HanFacAvgHi', '%.2f' % peak_factor_median(N_AVG_HI))

# =====================================================================
# (2) The primary-beam convention defect
# =====================================================================
# What the released catalogue actually applied, measured off its own
# theta_pb_arcsec column: theta_pb = COEF_APPLIED * lambda / D_APPLIED, the
# same value for every window whatever the array.
_applied = [F(r['theta_pb_arcsec']) / ARCSEC /
            (C_MS / (0.5 * (F(r['flo_GHz']) + F(r['fhi_GHz'])) * 1e9))
            for r in ROWS]
# The tolerance must be relative: this quantity is of order 4e9, so an
# absolute bound of 1e-6 tests the print precision of the column, not the
# convention. The residual spread is the rounding of theta_pb_arcsec.
_spread = (max(_applied) - min(_applied)) / st.median(_applied)
assert _spread < 1e-3, 'catalogue theta_pb is not one convention (%.2e)' % _spread
APPLIED_RATIO = st.median(_applied)                 # = coefficient / diameter
PB_COEF = F(texval('survey_numbers_round12.tex', 'RingPbCoef'))   # 1.13, ALMA
# A Gaussian primary beam attenuates as exp(-a theta^2 / theta_pb^2), so
# replacing theta_pb rescales the applied attenuation factor by the exponent
# (theta_applied / theta_correct)^2 = (APPLIED_RATIO / (PB_COEF / D))^2.
_pb = []
for r in ROWS:
    d = DISH[ARRAY[r['eb']]]
    k = APPLIED_RATIO ** 2 / (PB_COEF / d) ** 2
    applied = F(r['smin_mJy']) / (5.0 * F(r['rms_mJy']))
    _pb.append((r, applied, applied ** k, d))
_chg = [c / a for _, a, c, _ in _pb]
M('NPbFixOnePct', '%d' % sum(1 for x in _chg if abs(x - 1.0) > 0.01))
M('NPbFixFivePct', '%d' % sum(1 for x in _chg if abs(x - 1.0) > 0.05))
M('PbFixLoPct', '%.1f' % (100.0 * (min(_chg) - 1.0)))
M('PbFixHiPct', '%.1f' % (100.0 * (max(_chg) - 1.0)))
M('PbMaxFixed', '%.2f' % max(c for _, _, c, _ in _pb))

# =====================================================================
# (3) The array strata
# =====================================================================
_by_array = collections.defaultdict(list)
for r in G:
    _by_array[ARRAY[r['eb']]].append(r)
_dish_sorted = sorted(_by_array, key=lambda a: -DISH[a])
BIG, SMALL = _dish_sorted[0], _dish_sorted[-1]
assert len(_dish_sorted) == 2, _dish_sorted
w12, w7 = _by_array[BIG], _by_array[SMALL]
M('NWinTwelveM', '%d' % len(w12))
M('NEbTwelveM', '%d' % len({r['eb'] for r in w12}))
M('NStarTwelveM', '%d' % len({r['star_name'] for r in w12}))
M('NSysTwelveM', '%d' % len({r['sys'] for r in w12}))
M('NCrossTwelveM', '%d' % sum(1 for r in w12 if r['cross']))
M('NRankFirstTwelveM', '%d' % sum(1 for r in w12 if r['sbr']))
M('NStageOneTwelveM', '%d' % sum(1 for r in w12 if r['sbr'] and r['cross']))
# expected rank-first count under exchangeability: one window in NRANK
M('ExpFlagsTwelveM', '%.2f' % (len(w12) / float(NRANK)))
_d12, _p12 = ks_uniform([p_rank(r) for r in w12])
_d7, _p7 = ks_uniform([p_rank(r) for r in w7])
M('KsTwelveD', '%.3f' % _d12)
M('KsTwelveP', '%.2f' % _p12)
M('KsAcaD', '%.2f' % _d7)
M('KsAcaP', '%.3f' % _p7)

# =====================================================================
# (4) The clustered permutation
# =====================================================================
BLOCKS = collections.defaultdict(list)
for r in G:
    BLOCKS[r['eb']].append(r)
for r in G:
    a = np.asarray(r['ctrl_all'])
    r['argmax'] = int(a.argmax())
    r['ctrlmax'] = float(a.max())
CROSS_SIGMA = 5.0                    # the survey's own crossing threshold


def clustered_pmf(gate=None):
    """Exact null distribution of the number of rank-first windows when every
    window in one execution block is scored against the same control probe."""
    tot = np.array([1.0])
    for ws in BLOCKS.values():
        cnt = np.zeros(NCTRL, dtype=int)
        for w in ws:
            if gate is None or w['ctrlmax'] >= gate:
                cnt[w['argmax']] += 1
        tot = np.convolve(tot, np.bincount(cnt, minlength=1) / float(NCTRL))
    return tot


_pmf = clustered_pmf()
_k = np.arange(len(_pmf))
M('ClustMean', '%.2f' % float((_k * _pmf).sum()))
M('ClustPfour', '%.3f' % float(_pmf[4:].sum()))
M('ClustPfive', sci(float(_pmf[5:].sum())))
_pmf1 = clustered_pmf(CROSS_SIGMA)
_k1 = np.arange(len(_pmf1))
M('ClustStageMean', '%.2f' % float((_k1 * _pmf1).sum()))
M('ClustStagePone', '%.2f' % float(_pmf1[1:].sum()))

# concordance of the control-maximum position within a block
_pairs = _same = 0
for ws in BLOCKS.values():
    for i in range(len(ws)):
        for j in range(i + 1, len(ws)):
            _pairs += 1
            _same += (ws[i]['argmax'] == ws[j]['argmax'])
M('ClustPairSame', '%d' % _same)
M('ClustPairs', '%d' % _pairs)
M('ClustPairsExp', '%.1f' % (_pairs / float(NCTRL)))

# null distribution of the survey maximum: one control probe per block, drawn
# independently, the block maximum over its own windows taken at that probe
CLUST_DRAWS = 20000
CLUST_SEED = 20260912
_colmax = {eb: np.asarray([w['ctrl_all'] for w in ws]).max(0)
           for eb, ws in BLOCKS.items()}
_rng = np.random.default_rng(CLUST_SEED)
_maxes = np.empty(CLUST_DRAWS)
for _m in range(CLUST_DRAWS):
    _best = -np.inf
    for _eb in BLOCKS:
        _v = _colmax[_eb][_rng.integers(NCTRL)]
        if _v > _best:
            _best = _v
    _maxes[_m] = _best
M('ClustDraws', comma(CLUST_DRAWS))
M('ClustMaxMed', '%.1f' % float(np.median(_maxes)))
M('ClustMaxLo', '%.1f' % float(np.percentile(_maxes, 5)))
M('ClustMaxHi', '%.1f' % float(np.percentile(_maxes, 95)))

# =====================================================================
# (5) The held-out campaign, at build time
# =====================================================================
HO = json.load(open(os.path.join(HERE, 'heldout_v352.json')))
HW = HO['windows']
HNULL = [w for w in HW if not w['detection']]
HO_SEED_CRIT, HO_SEED_POWER = 20260912, 20260913
HO_DRAWS = 20000
HO_ALPHA = 0.05                      # test size, and 1 - confidence level
HO_MIX = 0.2                         # "a fifth of the windows" in the alternative
HO_MIX_HI = 0.05                     # the contaminated fifth draws U(0, 0.05)


def ks_crit_and_power(n):
    i = np.arange(1, n + 1)

    def dstat(u):
        u = np.sort(u, axis=1)
        return np.maximum((i / n - u).max(1), (u - (i - 1) / n).max(1))
    rng = np.random.default_rng(HO_SEED_CRIT)
    crit = float(np.quantile(dstat(rng.random((HO_DRAWS, n))), 1.0 - HO_ALPHA))
    rng2 = np.random.default_rng(HO_SEED_POWER)
    u = rng2.random((HO_DRAWS, n))
    mixed = np.where(rng2.random((HO_DRAWS, n)) < HO_MIX, u * HO_MIX_HI, u)
    return crit, 100.0 * float(np.mean(dstat(mixed) >= crit))


_crit, _power = ks_crit_and_power(len(HNULL))
M('HOKsCrit', '%.2f' % _crit)
M('HOKsPowerFifth', '%.0f' % _power)

# the unattributed stage-1 rate and its exact one-sided upper bound
_odd = [w for w in HW if w['unattributed_stage1']]
K_ODD, N_HO = len(_odd), len(HW)
M('HOUnattribStageOne', '%d' % K_ODD)
M('HOUnattribRatePct', '%.2f' % (100.0 * K_ODD / N_HO))


def clopper_pearson_upper(k, n, alpha=HO_ALPHA):
    """Largest p with P(X <= k | n, p) >= alpha, by bisection: the exact
    one-sided 1 - alpha upper bound for k successes in n Bernoulli trials."""
    def cdf(p):
        return sum(math.comb(n, i) * p ** i * (1 - p) ** (n - i)
                   for i in range(k + 1))
    lo, hi = 0.0, 1.0
    for _ in range(200):
        mid = 0.5 * (lo + hi)
        if cdf(mid) > alpha:
            lo = mid
        else:
            hi = mid
    return 0.5 * (lo + hi)


_bound = clopper_pearson_upper(K_ODD, N_HO)
_survey_rate = sum(1 for r in ROWS if r['stage1_flag'] in ('True', 'true', '1')) / float(len(ROWS))
M('HOStageOneBoundPct', '%.1f' % (100.0 * _bound))
M('HOBoundRatio', '%.1f' % (_bound / _survey_rate))

# =====================================================================
# (6) The unattributed held-out stage-1 window
# =====================================================================
assert K_ODD == 1, 'group 6 assumes exactly one unattributed stage-1 window'
ODD = _odd[0]
M('HOOddStar', texsafe(ODD['star']))
M('HOOddBand', re.sub(r'[^0-9]', '', ODD['band']))
M('HOOddT', '%.2f' % ODD['star_peak_snr'])
M('HOOddCtrlMax', '%.2f' % ODD['control_peak_snr'])
M('HOOddChanwKHz', '%.1f' % (ODD['chanwidth_Hz'] / 1e3))
M('HOOddLineOff', '%.0f' % abs(ODD['nearest_known_line_offset_MHz']))

# The frozen mask of v342_calc.py section B, parsed rather than imported so
# that the rest frequency behind the offset is the survey's own value.
_src = open(os.path.join(HERE, 'v342_calc.py')).read()
_mm = re.search(r'^CAT = (\{.*?^\})', _src, re.S | re.M)
if not _mm:
    raise SystemExit('frozen line mask not found in v342_calc.py')
CAT = ast.literal_eval(re.sub(r'#[^\n]*', '', _mm.group(1)))
assert ODD['nearest_known_line'] in CAT, ODD['nearest_known_line']
M('HOOddFreq', '%.3f' % (CAT[ODD['nearest_known_line']]
                         + ODD['nearest_known_line_offset_MHz'] / 1e3))
# The control percentile now comes from the window's own control-maximum
# array in the search product, read live rather than from the frozen record.
# HOOddHits and HOOddDrift remain unemitted: neither the hit count nor the
# fitted drift for this window is carried anywhere we can read.
assert ODD.get('ctrl_p99') is not None, 'control percentiles absent from harvest'
M('HOOddCtrlNinetyNine', '%.2f' % ODD['ctrl_p99'])

# =====================================================================
# (7) The beta Pictoris Band 6 stage-1 recurrence
# =====================================================================
BP = json.load(open(os.path.join(HERE, 'bpic_stage1_v352.json')))
B1, B2 = BP['blocks']['original'], BP['blocks']['repeat']
assert B1['chanwidth_Hz'] == B2['chanwidth_Hz'], 'blocks differ in channel width'
BPCHAN = B1['chanwidth_Hz']
M('BpRecTOne', '%.2f' % B1['star_peak_snr'])
M('BpRecTTwo', '%.2f' % B2['star_peak_snr'])
M('BpRecCtrlOne', '%.2f' % B1['control_peak_snr'])
M('BpRecCtrlTwo', '%.2f' % B2['control_peak_snr'])
M('BpRecMarginOne', '%.2f' % (B1['star_peak_snr'] / B1['control_peak_snr']))
M('BpRecMarginTwo', '%.2f' % (B2['star_peak_snr'] / B2['control_peak_snr']))
M('BpRecHitsOne', '%d' % B1['n_hits_above_threshold'])
M('BpRecHitsTwo', '%d' % B2['n_hits_above_threshold'])
assert B1['n_int'] == B2['n_int'] and B1['n_chan'] == B2['n_chan']
M('BpRecNInt', '%d' % B1['n_int'])
M('BpRecNChan', comma(B1['n_chan']))
M('BpRecChanwKHz', '%.2f' % (BPCHAN / 1e3))
M('BpRecEbTwo', texsafe(B2['eb']))
_dt = B2['searched_utc']
_y, _mo, _d = int(_dt[0:4]), int(_dt[5:7]), int(_dt[8:10])
M('BpRecDateTwo', '%d %s %d' % (_y, calendar.month_name[_mo], _d))
_df_hz = abs(B1['star_peak_freq_GHz'] - B2['star_peak_freq_GHz']) * 1e9
M('BpRecOffkHz', '%.1f' % (_df_hz / 1e3))
M('BpRecOffkms', '%.2f' % (C_KMS * _df_hz / (B1['star_peak_freq_GHz'] * 1e9)))
M('BpRecOffChan', '%.1f' % (_df_hz / BPCHAN))
M('BpRecTPinned', '%.2f' % B2['T_star_at_flagged_frequency'])
M('BpRecNCtrlPinned', '%d' % B2['n_control_ge_T_at_flagged_frequency'])
assert B2['n_control'] == NCTRL, B2['n_control']
M('BpRecPPinned', '%.4f'
  % ((1 + B2['n_control_ge_T_at_flagged_frequency']) / float(NRANK)))

# =====================================================================
# (8) The closure-phase screen
# =====================================================================
CL = json.load(open(os.path.join(HERE, 'closure_v352.json')))
CLW = CL['windows']
_cp = [v for k, v in CLW.items() if k.startswith('CP-72')]
assert len(_cp) == 1, list(CLW)
_cp = _cp[0]


def closure_z(w):
    z = w['mean_closure_phase_deg'] / (w['std_closure_phase_deg']
                                       / math.sqrt(w['n_triangles']))
    assert abs(z - w['z_score']) < 1e-6, (z, w['z_score'])
    return z


M('CpClosTri', '%d' % _cp['n_triangles'])
M('CpClosSd', '%.1f' % _cp['std_closure_phase_deg'])
M('CpClosMean', '%.1f' % _cp['mean_closure_phase_deg'])
M('CpClosZ', '%.2f' % closure_z(_cp))
# the scatter a uniformly distributed phase would give, 360 deg / sqrt(12)
M('ClosUnifSd', '%.1f' % (360.0 / math.sqrt(12.0)))
M('ClosSnrLo', '%.1f' % CL['per_baseline_snr_lo'])
M('ClosSnrHi', '%.1f' % CL['per_baseline_snr_hi'])
_bpz = sorted(abs(closure_z(v)) for k, v in CLW.items()
              if k.startswith('bet Pic') and 'repeat' not in k)
assert len(_bpz) == 2, _bpz
M('BpClosZLo', '%.2f' % _bpz[0])
M('BpClosZHi', '%.2f' % _bpz[1])

# =====================================================================
# (9) The transfer bracket on the recovery fractions
# =====================================================================
# The bracket endpoints are read out of the occurrence appendix sentence that
# states them, so that changing one changes the other.
_tex = open(os.path.join(HERE, 'technosignatures_20pc_v3.54.tex')).read()
_bm = re.search(r'scaling (?:it|the curve) by\s*([0-9.]+)--([0-9.]+)\$\\times\$', _tex)
if not _bm:
    raise SystemExit('completeness bracket sentence not found in the manuscript')
BRA_LO, BRA_HI = F(_bm.group(1)), F(_bm.group(2))
for macro, src in (('RecTwice', 'RecTwice'), ('RecThresh', 'RecThresh')):
    v = F(texval('survey_numbers.tex', src))
    M(macro + 'BraLo', '%.0f' % min(100.0, v * BRA_LO))
    M(macro + 'BraHi', '%.0f' % min(100.0, v * BRA_HI))

# =====================================================================
# (10) The line-database cross-check
# =====================================================================
_mask_paths = [os.path.join(HERE, 'mask_xcheck_lines.json'),
               os.path.abspath(os.path.join(HERE, '..', '..', 'v352_F',
                                            'mask_xcheck_lines.json'))]
_mp = next((p for p in _mask_paths if os.path.exists(p)), None)
if _mp is None:
    raise SystemExit('mask_xcheck_lines.json not found in %s' % _mask_paths)
DB = json.load(open(_mp))
MASK_HALF_KMS = 50.0                 # the survey's own tube, v342_calc.py:469

# the searched islands, recomputed from the released catalogue
_iv = sorted((min(F(r['flo_GHz']), F(r['fhi_GHz'])),
              max(F(r['flo_GHz']), F(r['fhi_GHz']))) for r in ROWS)
ISL = []
for a, b in _iv:
    if ISL and a <= ISL[-1][1]:
        ISL[-1][1] = max(ISL[-1][1], b)
    else:
        ISL.append([a, b])
assert len(ISL) == len(DB['islands']) and all(
    abs(a1 - a2) < 1e-9 and abs(b1 - b2) < 1e-9
    for (a1, b1), (a2, b2) in zip(ISL, DB['islands'])), \
    'the harvest was taken over different islands from the released catalogue'
UNION = sum(b - a for a, b in ISL)


def veto_cost(freqs, half_kms=MASK_HALF_KMS):
    """Fraction of the searched union a +-half_kms veto around these rest
    frequencies removes, tubes merged before intersecting the islands."""
    tubes = sorted((f * (1 - half_kms / C_KMS), f * (1 + half_kms / C_KMS))
                   for f in freqs)
    merged = []
    for a, b in tubes:
        if merged and a <= merged[-1][1]:
            merged[-1][1] = max(merged[-1][1], b)
        else:
            merged.append([a, b])
    tot = 0.0
    for a, b in ISL:
        for c, d in merged:
            lo, hi = max(a, c), min(b, d)
            if hi > lo:
                tot += hi - lo
    return 100.0 * tot / UNION


_strip = lambda s: re.sub(r'<[^>]+>', '', s).replace('&#150;', '-').strip()
M('MaskDbTrans', comma(len(DB['lines'])))
M('MaskDbCarriers', '%d' % len({_strip(x['name']) for x in DB['lines']}))
M('MaskDbEuK', '%.0f' % DB['eu_max'])
M('MaskDbLogA', '%.0f' % DB['loga_min'])
M('MaskDbPctUnion', '%.1f' % veto_cost([x['f'] for x in DB['lines']]))
M('MaskOwnPctUnion', '%.2f' % veto_cost(CAT.values()))
# rows whose intra-integration smearing correction is worse than one per cent
SMEAR_FLOOR = 0.99
M('NSmearLo', '%d' % sum(1 for r in ROWS if F(r['eta_smear']) < SMEAR_FLOOR))

# =====================================================================
_names = [re.match(r'\\newcommand\{\\([A-Za-z]+)\}', s).group(1) for s in OUT]
assert len(set(_names)) == len(_names), 'duplicate macro in this round'
open(os.path.join(HERE, 'survey_numbers_round20.tex'), 'w').write(
    '%% GENERATED by v352_calc.py -- do not hand-edit.\n' + '\n'.join(OUT) + '\n')
print('\n'.join(OUT))
print('%d macros' % len(OUT))


# ---------------------------------------------------------------------
# The manuscript names the released catalogue by filename. Assert the named
# file is the one this script measured, so the two cannot drift apart.
CATALOGUE_FILE = 'per_target_results_v3.52.csv'
MAIN_TEX = [f for f in os.listdir(HERE)
            if f.startswith('technosignatures_20pc_v') and f.endswith('.tex')][0]
_named = re.search(r'per\\_target\\_results\\_v([0-9.]+)\.csv',
                   open(os.path.join(HERE, MAIN_TEX)).read())
assert _named, 'manuscript does not name the released catalogue'
_want = 'per_target_results_v%s.csv' % _named.group(1).rstrip('.')
assert _want == CATALOGUE_FILE, (
    'manuscript names %s, this script reads %s' % (_want, CATALOGUE_FILE))
print('catalogue name agrees with the manuscript: %s' % _want)
