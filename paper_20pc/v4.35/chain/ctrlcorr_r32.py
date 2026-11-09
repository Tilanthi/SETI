#!/usr/bin/env python3
r"""Round 3220 (r32, R1-4): ARE THE CONTROL POSITIONS OF A WINDOW INDEPENDENT? MEASURED, AND THE CHANCE
COMPARISON RE-RESAMPLED WITH THE CORRELATION KEPT.

The referee: the 512 control positions of a window are not independent draws -- neighbours inside one
synthesised beam see the same noise, and in a line-bright field the exceedances cluster on the emission --
so redrawing a window's control rate as a binomial on 512 trials understates its uncertainty, and with it
the spread of the expectation \CeExp and the probability \CeProbNull.

Everything here is read from products the build already holds; nothing is re-extracted.
  * The positions.  The extractor (`seti_extract_generic.probe_positions`) draws the 512 controls uniform in
    area over the annulus r_in..r_out from a FRESH default_rng(20260825) -- radii first, then angles -- and
    nothing else consumes that stream, so with the searched annulus of every window (`ringgeom_r27.json`) the
    positions are reconstructed exactly, in the order of the window's `ctrl_all` vector (all 405 vectors are
    complete, 512 entries, so no probe was dropped and the order is the probe index).  C1 PROVES the
    reconstruction from the data: neighbouring positions (< 0.1 beam) are strongly correlated and the same
    pairs shuffled are not.
  * The vectors are joined to the catalogue exactly as `chance_v414.py` joins them (repair record where one
    exists, else the export row, both by position, `posjoin_r27`), and C0 requires every window's trigger
    count to equal the resampling export's.
  * The beam.  theta_syn = 1.22 lambda / B_max is recorded for the windows whose geometry was re-derived
    (`ringgeom_r27` routes product/block); the frozen-geometry windows carry none.  For them it is FITTED
    from the window's own correlogram against the pooled template of the recorded windows (a one-parameter
    scale fit); on the recorded windows the same fit returns \CcBeamFitMed times the recorded beam
    (inter-quartile \CcBeamFitLo--\CcBeamFitHi), which is what licenses it.
  * The correlation.  The control statistic is rank-normalised inside its window and the products of pairs
    are pooled in bins of separation / theta_syn (`correlogram`), together with the exceedance indicator's
    own pair correlation.  The statistic decorrelates within a fraction of theta_syn (it is a maximum over
    thousands of channels and drift tracks), so the noise term is small; structure on larger scales -- real
    emission over arcs of the annulus -- is what the arc blocks below are for.
  * N_eff.  For each window the variance of its control rate is estimated with the positions grouped into
    blocks -- square cells of 0.5, 1, 2 and 4 theta_syn, and 32, 16 and 8 contiguous arcs of the annulus --
    as the between-block (cluster) variance; N_eff = p(1-p)/var.  Reported for the windows that carry half
    of the expectation.
  * The resampling.  `chance_v414`'s construction is repeated draw for draw (C2 reproduces its P and its
    resampled sum bit for bit on the binomial), then repeated with each window's binomial replaced by a
    block bootstrap of its own positions under each blocking (all the other terms unchanged: block
    resampling of execution blocks, the attributed share, the atmospheric share).  The probability, the
    interval and the added-population bound are compared with the published ones.

Macros (round 3220):
  \CcNWin, \CcNWinBeamRec, \CcNWinBeamFit     windows; with a recorded beam; with a fitted beam
  \CcNWinNoPos   windows whose positions cannot be placed (vector not 512 long, or no annulus): binomial kept
  \CcNWinGeoOk   windows whose geometry is verified one by one (>= 20 pairs < 0.1 beam, correlation > 0.2)
  \CcBeamFitMed, \CcBeamFitLo, \CcBeamFitHi   fitted / recorded beam on the recorded windows (median, IQR)
  \CcRhoNear     rank correlation of the control statistic between positions < 0.1 theta_syn apart
  \CcHalfBeam    separation (theta_syn) at which it has fallen to one half
  \CcRhoHalfBeamOut  largest |correlation| of the statistic beyond 0.5 theta_syn (binned)
  \CcRhoIndNear  pair correlation of the exceedance indicator < 0.1 theta_syn
  \CcNLead, \CcLeadPct   windows carrying half of the expectation, and that share in per cent
  \CcNeffLeadMed, \CcNeffLeadMin   their N_eff under the most pessimistic blocking (median, minimum)
  \CcSdBinom, \CcSdCorr  s.d. of the expectation from the window rates alone, binomial and worst blocking
  \CcSdTotal     s.d. of the full resampled expectation (published construction)
  \CcProbRange   P(N >= N_obs) over the blockings, "min--max" or one value when both ends print alike
  \CcAddLimRange the added-population bound over the blockings, the same way
  \CcIntLo, \CcIntHi     the widest null interval over the blockings (2.5--97.5 per cent)
  \CcMaxShift    largest |P_blocked - P_binomial| (three decimals)

Assertions (each driven: `--drive N` prints FAILED and exits 1, writes nothing):
  C0 the join reproduces every window's trigger count                       (drive 5)
  C1 the reconstructed positions are the searched ones                      (drive 1: wrong seed)
  C2 the binomial run IS chance_v414's resampling (P and sum bit for bit)   (drive 2: one draw size off)
  C3 every blocked resampling keeps the mean of the expectation             (drive 3: empty blocks dropped)
  C4 the printed range is the min/max over the blockings, and the binomial value lies inside the
     blockings' span or below the widest                                    (drive 4: binomial printed as Hi)
  C5 keeping the correlation does not move \CeProbNull as printed; if it ever does the build stops and the
     blocked resampling must be adopted                                      (drive 6: a 0.02 shift)

    python3 ctrlcorr_r32.py [--drive N] [--quick]
"""
import collections
import csv
import time
import json
import math
import os
import sys

import numpy as np
from scipy.special import gammainc, gammaincc
from scipy.stats import norm, rankdata

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
os.chdir(HERE)
import posjoin_r27 as PJ  # noqa: E402

ROUND = 3220
DRIVE = None
for _i, _a in enumerate(sys.argv):
    if _a == '--drive':
        DRIVE = int(sys.argv[_i + 1])
QUICK = '--quick' in sys.argv or DRIVE in (3, 4, 6)     # the C3/C4 drives need no full draw count
OUT_TEX = os.path.join(HERE, 'numbers/survey_numbers_round3220.tex' if DRIVE is None
                       else 'numbers/survey_numbers_round3220_drive%d.tex' % DRIVE)
OUT_JSON = os.path.join(HERE, 'ctrlcorr_r32.json' if DRIVE is None else 'ctrlcorr_r32_drive%d.json' % DRIVE)
SEED_PROBE = 20260825 if DRIVE != 1 else 20260826
N_PROBE = 512
OUT, fail = [], []


def m(name, val):
    assert name.isalpha(), name
    assert not any(x.startswith('\\newcommand{\\%s}' % name) for x in OUT), name
    OUT.append('\\newcommand{\\%s}{%s}' % (name, val))


def ck(label, cond, detail=''):
    print('  %-74s %s  %s' % (label[:74], 'PASS' if cond else 'FAIL', detail))
    if not cond:
        fail.append(label.split()[0])


def wkey(eb, a, b):
    a, b = float(a), float(b)
    return (eb, round(min(a, b), 3), round(max(a, b), 3))


# =====================================================================  inputs
RS = json.load(open(os.path.join(HERE, 'chance_resample_r30.json')))
CAT = list(csv.DictReader(open(os.path.join(HERE, 'per_target_results_v3.99.csv'))))
EXP = json.load(open(os.path.join(HERE, 'corrected_export_v399.json')))['rows']
FFX = json.load(open(os.path.join(HERE, 'r8inputs/v409/fieldfix_v409.json')))
GEO = {wkey(g['eb'], g['lo'], g['hi']): g for g in json.load(open(os.path.join(HERE, 'ringgeom_r27.json')))['rows']}
BYWIN, FFWIN = collections.defaultdict(list), collections.defaultdict(list)
for r in EXP:
    BYWIN[wkey(r['eb'], r['flo'], r['fhi'])].append(r)
for r in FFX:
    FFWIN[wkey(r['eb'], r['flo'], r['fhi'])].append(r)


def vector(i):
    """chance_v414.ctrl_vector on the adopted (whole-beam) reading: the repair record where one is at the
    row's position, else the export row (posjoin_r27, by position, never by name)."""
    r = CAT[i]
    c = FFWIN.get(wkey(r['eb'], r['flo_GHz'], r['fhi_GHz']), [])
    q = PJ.pick_rep(c, r, HERE) if c else None
    if q is not None and q.get('ctrl_all'):
        src = q
    else:
        c = BYWIN.get(wkey(r['eb'], r['flo_GHz'], r['fhi_GHz']), [])
        src = PJ.pick_exp(c, r) if c else None
    v = src['ctrl_all']
    return np.asarray(json.loads(v) if isinstance(v, str) else v, float)


def probe_lm(r_in, r_out):
    """seti_extract_generic.probe_positions, the control annulus only."""
    g = np.random.default_rng(SEED_PROBE)
    rr = np.sqrt(g.uniform(r_in ** 2, r_out ** 2, N_PROBE))
    th = g.uniform(0, 2 * np.pi, N_PROBE)
    return rr * np.cos(th), rr * np.sin(th)


TRIG = float(RS['trigger'])
WIN = []
for w in RS['windows']:
    v = vector(w['cat_index'])
    if DRIVE == 5 and not WIN:
        v = v[::-1].copy()
        v[:3] = TRIG + 1.0
    g = GEO.get(wkey(w['eb'], w['flo_GHz'], w['fhi_GHz']))
    #: a window whose vector is not the full 512 (probes dropped: the order is no longer the probe index) or
    #: whose searched annulus is not recorded cannot be placed; it keeps the binomial draw and is counted
    pos = g is not None and v.size == N_PROBE
    l, mm = probe_lm(g['r_in_arcsec'], g['r_out_arcsec']) if pos else (None, None)
    WIN.append(dict(w=w, v=v, l=l, m=mm, geo=g or {}, pos=pos, I=(v >= TRIG).astype(float)))
_bad0 = [x['w']['cat_index'] for x in WIN if x['v'].size != x['w']['n_ctrl']
         or int(x['I'].sum()) != x['w']['n_ctrl_trig']]
ck('C0 the control vectors are chance_v414\'s: every window\'s trigger count is the resampling export\'s',
   not _bad0, '%d windows, %d differ %s; %d cannot be placed (kept binomial)'
   % (len(WIN), len(_bad0), _bad0[:5], sum(1 for x in WIN if not x['pos'])))
ALL = WIN
WIN = [x for x in ALL if x['pos']]
NOPOS = [x for x in ALL if not x['pos']]

# =====================================================================  the correlogram
IU = np.triu_indices(N_PROBE, 1)
XB = np.round(np.arange(0.0, 1.55, 0.05), 2)            # separation / theta_syn, template bins
for x in WIN:
    d = np.hypot(x['l'][:, None] - x['l'][None, :], x['m'][:, None] - x['m'][None, :])[IU]
    z = norm.ppf((rankdata(x['v']) - 0.5) / x['v'].size)
    x['d'], x['P'] = d, (z[:, None] * z[None, :])[IU]
    x['z'] = z
REC = [x for x in WIN if x['geo'].get('syn_arcsec')]
_num, _den = np.zeros(len(XB) - 1), np.zeros(len(XB) - 1)
for x in REC:
    t = x['d'] / x['geo']['syn_arcsec']
    s = t < XB[-1]
    j = np.digitize(t[s], XB) - 1
    _num += np.bincount(j, weights=x['P'][s], minlength=len(_num))
    _den += np.bincount(j, minlength=len(_den))
TEMPLATE = _num / np.maximum(_den, 1)


def tmpl(t):
    j = np.minimum((t / 0.05).astype(int), len(TEMPLATE) - 1)
    out = TEMPLATE[j]
    out[t >= XB[-1]] = 0.0
    return out


TH_GRID = np.exp(np.linspace(np.log(0.03), np.log(30.0), 240 if not QUICK else 60))


def fit_beam(x):
    s = x['d'] < 25.0
    d, P = x['d'][s], x['P'][s]
    best = None
    for t in TH_GRID:
        near = d < XB[-1] * t
        r = ((P[near] - tmpl(d[near] / t)) ** 2).sum() + (P[~near] ** 2).sum()
        if best is None or r < best[0]:
            best = (r, t)
    return float(best[1])


NPROC = max(1, min(int(os.environ.get('NPROC', os.cpu_count() or 1)), 24))
_MP = __import__('multiprocessing').get_context('fork')


def _fit_i(i):
    return fit_beam(WIN[i])


with _MP.Pool(NPROC) as _pool:
    _fits = _pool.map(_fit_i, range(len(WIN)), chunksize=4)
for x, _t in zip(WIN, _fits):
    x['th_fit'] = _t
    x['th'] = float(x['geo']['syn_arcsec']) if x['geo'].get('syn_arcsec') else x['th_fit']
    x['th_src'] = 'recorded' if x['geo'].get('syn_arcsec') else 'fitted'
_fr = np.array([x['th_fit'] / x['geo']['syn_arcsec'] for x in REC])
FIT_MED, FIT_LO, FIT_HI = (float(np.median(_fr)), float(np.percentile(_fr, 25)), float(np.percentile(_fr, 75)))

# correlogram over ALL windows in units of their adopted theta, statistic and indicator
CB = [0.0, 0.05, 0.1, 0.2, 0.3, 0.5, 0.75, 1.0, 1.5, 2.0, 3.0, 5.0, 8.0, 1e9]
CORR = []
_rs = np.random.default_rng(3220)
_acc = np.zeros((len(CB) - 1, 6))
for x in WIN:
    t = x['d'] / x['th']
    j = np.digitize(t, CB) - 1
    p = x['I'].mean()
    Ii = x['I'] - p
    PI = (Ii[:, None] * Ii[None, :])[IU]
    zs = x['z'][_rs.permutation(N_PROBE)]
    Ps = (zs[:, None] * zs[None, :])[IU]
    _acc[:, 0] += np.bincount(j, minlength=len(CB) - 1)
    _acc[:, 1] += np.bincount(j, weights=x['P'], minlength=len(CB) - 1)
    _acc[:, 2] += np.bincount(j, weights=Ps, minlength=len(CB) - 1)
    _acc[:, 3] += np.bincount(j, weights=PI, minlength=len(CB) - 1)
    _acc[:, 4] += np.bincount(j, minlength=len(CB) - 1) * p * (1 - p)
    _acc[:, 5] += np.bincount(j, weights=x['I'][IU[0]] * x['I'][IU[1]], minlength=len(CB) - 1)
for k in range(len(CB) - 1):
    n = _acc[k, 0]
    CORR.append(dict(sep_lo_beam=CB[k], sep_hi_beam=(CB[k + 1] if CB[k + 1] < 1e8 else None), n_pairs=int(n),
                     rho_statistic=float(_acc[k, 1] / max(n, 1)), rho_statistic_shuffled=float(_acc[k, 2] / max(n, 1)),
                     rho_indicator=float(_acc[k, 3] / max(_acc[k, 4], 1e-300)),
                     n_pairs_both_exceed=int(round(_acc[k, 5]))))
RHO_NEAR = (_acc[0, 1] + _acc[1, 1]) / max(_acc[0, 0] + _acc[1, 0], 1)
#: and window by window: where a window has at least 20 pairs closer than 0.1 beam, their correlation must be
#: clearly positive -- a window whose annulus the record has wrong (e.g. re-extracted under another ring rule)
#: shows none, which is how a stale geometry row would be caught one window at a time
GEO_BAD = []
for x in WIN:
    s_ = x['d'] / x['th'] < 0.1
    x['n_close'] = int(s_.sum())
    x['rho_close'] = float(x['P'][s_].mean()) if s_.any() else None
    x['geo_check'] = ('verified' if x['n_close'] >= 20 and x['rho_close'] > 0.2 else
                      ('failed' if x['n_close'] >= 20 else 'too few close pairs'))
    if x['geo_check'] == 'failed':
        GEO_BAD.append('%s %s' % (x['w']['eb'], x['w']['flo_GHz']))
N_GEO_OK = sum(1 for x in WIN if x['geo_check'] == 'verified')
RHO_NEAR_SH = (_acc[0, 2] + _acc[1, 2]) / max(_acc[0, 0] + _acc[1, 0], 1)
RHOI_NEAR = (_acc[0, 3] + _acc[1, 3]) / max(_acc[0, 4] + _acc[1, 4], 1e-300)
_mid = 0.5 * (XB[:-1] + XB[1:])
_k = int(np.argmax(TEMPLATE < 0.5 * TEMPLATE[0]))
HALF_BEAM = float(_mid[_k - 1] + (0.5 * TEMPLATE[0] - TEMPLATE[_k - 1]) * (_mid[_k] - _mid[_k - 1])
                  / (TEMPLATE[_k] - TEMPLATE[_k - 1]))
RHO_OUT = max(abs(c['rho_statistic']) for c in CORR if c['sep_lo_beam'] >= 0.5)
ck('C1 the reconstructed positions are the searched ones: positions < 0.1 beam apart are correlated, the same '
   'pairs shuffled are not, and the fitted beam reproduces the recorded one',
   RHO_NEAR > 0.5 and abs(RHO_NEAR_SH) < 0.05 and 0.8 <= FIT_MED <= 1.25 and not GEO_BAD,
   'rho(<0.1 beam) %.3f (shuffled %+.3f), fitted/recorded beam %.3f (IQR %.3f-%.3f) over %d windows; '
   'window by window %d verified, %d failed %s'
   % (RHO_NEAR, RHO_NEAR_SH, FIT_MED, FIT_LO, FIT_HI, len(REC), N_GEO_OK, len(GEO_BAD), GEO_BAD[:4]))



def early_exit():
    """A drive stops as soon as its own assertion has fired (the gate runs five of them)."""
    if fail and DRIVE is not None:
        print('\nFAILED: %s' % '; '.join(fail))
        raise SystemExit(1)


early_exit()

# =====================================================================  blockings and N_eff
SCHEMES = [('cell', 0.5), ('cell', 1.0), ('cell', 2.0), ('cell', 4.0), ('arc', 32), ('arc', 16), ('arc', 8)]


def labels(x, kind, par):
    if kind == 'cell':
        s = par * x['th']
        return np.floor(x['l'] / s).astype(np.int64) * 1000003 + np.floor(x['m'] / s).astype(np.int64)
    phi = np.arctan2(x['m'], x['l']) + np.pi
    return np.minimum(np.floor(phi / (2 * np.pi / par)).astype(np.int64), par - 1)


def sname(kind, par):
    return '%s%g' % (kind, par)


A_MEAS = RS['n_exc_in_mask'] / float(RS['n_exc_recorded'])
TL_FAC = ((RS['n_exc_survive_mask'] - RS['n_exc_telluric_only']) / float(RS['n_exc_survive_mask'])
          if RS['n_exc_survive_mask'] else 1.0)
for x in ALL:
    w = x['w']
    p = x['I'].mean()
    # r35 (A1): a measured window carries its own (per-window, shrunk) share, as chance_v414 now does
    att = ((w['a_share'] if RS.get('a_estimator') == 'shrink' else A_MEAS) if w['attribution'] == 'measured'
           else float(w['grid_mask_share']))
    x['p'], x['wt'] = p, (1.0 - att) * TL_FAC
    x['contrib'] = p * x['wt']
    x['var_binom'] = p * (1 - p) / x['v'].size
    x['blocks'], x['neff'], x['neff_min'] = {}, {}, None
for x in WIN:
    p = x['p']
    for kind, par in SCHEMES:
        lab = labels(x, kind, par)
        u, inv = np.unique(lab, return_inverse=True)
        t = np.bincount(inv, weights=x['I'])
        mj = np.bincount(inv).astype(float)
        K = len(u)
        var = K / (K - 1.0) * ((t - p * mj) ** 2).sum() / N_PROBE ** 2 if K > 1 else 0.0
        if DRIVE == 3:
            keep = t > 0                         # empty blocks dropped: the rate is biased up
            t, mj, K = t[keep], mj[keep], int(keep.sum())
        x['blocks'][sname(kind, par)] = dict(t=t, mj=mj, K=K, var=var)
    x['neff'] = {k: (p * (1 - p) / v['var'] if v['var'] > 0 else float(N_PROBE))
                 for k, v in x['blocks'].items()}
    x['neff_min'] = min(min(x['neff'].values()), float(N_PROBE)) if 0 < p < 1 else float(N_PROBE)

E_POINT = sum(x['contrib'] for x in ALL) * RS['scale']
_ord = sorted(ALL, key=lambda x: -x['contrib'])
_cs = np.cumsum([x['contrib'] for x in _ord]) * RS['scale']
N_LEAD = int(np.searchsorted(_cs, 0.5 * E_POINT) + 1)
LEAD = _ord[:N_LEAD]
LEAD_PCT = 100.0 * _cs[N_LEAD - 1] / E_POINT
NEFF_LEAD = np.array([x['neff_min'] for x in LEAD if x['pos']])
SD_BINOM = math.sqrt(sum(x['wt'] ** 2 * x['var_binom'] for x in ALL)) * RS['scale']
SD_SCHEME = {sname(k, p_): math.sqrt(sum(x['wt'] ** 2 * (x['blocks'][sname(k, p_)]['var'] if x['pos']
                                                         else x['var_binom']) for x in ALL)) * RS['scale']
             for k, p_ in SCHEMES}

# =====================================================================  the resampling, chance_v414's construction
NREAL, NBATCH, NBOOT = RS['n_realisations'], RS['n_batches'], RS['n_boot']
if QUICK:
    NREAL, NBOOT = NREAL // 4, NBOOT // 4
NOBS, NREF = int(RS['n_observed']), int(RS['n_reference_windows'])
ALPHA = float(RS['alpha'])
BLK = collections.defaultdict(list)
for x in ALL:
    BLK[x['w']['block_order']].append(x)
NB = len(BLK)
BLOCKS = [sorted(BLK[j], key=lambda x: x['w']['window_order']) for j in range(NB)]
NW = np.array([len(b) for b in BLOCKS], float)
_AB = sorted(RS['attr_blocks'], key=lambda b: b['attr_order'])
AA = np.array([b['n_exc_in_mask'] for b in _AB], float)
AB = np.array([b['n_exc_recorded'] for b in _AB], float)
BATCH = np.arange(NBOOT) % NBATCH


def resample(scheme):
    """chance_v414 lines (1)-(e) and BOOT_NULL, with the window-rate draw by `scheme` (None = binomial)."""
    g = np.random.default_rng(int(RS['seed']))
    pk = g.integers(0, len(AA), size=(NREAL, len(AA)))
    a_draw = AA[pk].sum(axis=1) / AB[pk].sum(axis=1)
    g.binomial(int(RS['n_exc_recorded']), A_MEAS, NREAL)          # drawn and not used, as in chance_v414
    # r35 (A1): each measured window's share drawn from its posterior on its own stream (seed + 3500), in the
    # record's window order -- chance_v414's construction, so the binomial run stays its resampling bit for bit
    sh = {}
    if RS.get('a_estimator') == 'shrink':
        gs = np.random.default_rng(int(RS['seed']) + 3500)
        a_ = np.clip(a_draw, 1e-12, 1.0 - 1e-12)
        K = float(RS['shrink_prior_strength'])
        for b in BLOCKS:
            for x in b:
                w = x['w']
                if w['attribution'] == 'measured':
                    sh[id(x)] = gs.beta(w['n_exc_in_mask'] + K * a_,
                                        w['n_exc_recorded'] - w['n_exc_in_mask'] + K * (1.0 - a_))
    surv = int(RS['n_exc_survive_mask'])
    tl = (1.0 - g.binomial(surv, 1.0 - TL_FAC, NREAL) / float(surv)) if surv else np.ones(NREAL)
    bv = np.empty((NB, NREAL))
    for j, b in enumerate(BLOCKS):
        acc = np.zeros(NREAL)
        for x in b:
            n, w = x['v'].size, x['w']
            att = a_draw if w['attribution'] == 'measured' else np.full(NREAL, float(w['grid_mask_share']))
            att = sh.get(id(x), att)
            if scheme is None or not x['pos']:
                r = g.binomial(n, x['p'] if DRIVE != 2 else x['p'] * 0.999, NREAL) / float(n)
            else:
                bl = x['blocks'][scheme]
                if x['p'] in (0.0, 1.0) or bl['K'] < 2:
                    r = np.full(NREAL, x['p'])
                else:
                    c = g.multinomial(bl['K'], np.full(bl['K'], 1.0 / bl['K']), size=NREAL)
                    r = (c @ bl['t']) / (c @ bl['mj'])
            acc += r * (1.0 - att)
        bv[j] = acc * tl
    pick = g.integers(0, NB, size=(NBOOT, NB))
    rpb = NREAL // NBATCH
    real = BATCH[:, None] * rpb + g.integers(0, rpb, size=(NBOOT, NB))
    return (bv[pick, real].sum(axis=1) / NW[pick].sum(axis=1)) * NREF


def p_at_least(k, lam):
    return gammainc(k, np.asarray(lam, float))


def p_at_most(k, lam):
    return gammaincc(k + 1.0, np.asarray(lam, float))


def lim(lam):
    def p_low(add):
        return float(p_at_most(NOBS, lam + add).mean())
    lo, hi = 0.0, 1.0
    while p_low(hi) > ALPHA and hi < 1e4:
        hi *= 2.0
    for _ in range(60):
        mid = 0.5 * (lo + hi)
        if p_low(mid) > ALPHA:
            lo = mid
        else:
            hi = mid
    return 0.5 * (lo + hi)


def mcse(a):
    bm = np.array([a[BATCH == k].mean() for k in range(NBATCH)])
    return float(bm.std(ddof=1) / math.sqrt(NBATCH))


def summary(boot):
    pt = p_at_least(NOBS, boot)
    x = lim(boot)
    return dict(p=float(pt.mean()), p_se=mcse(pt), mean=float(boot.mean()), mean_se=mcse(boot),
                sd=float(boot.std()),
                int_lo=float(np.percentile(boot, 2.5)), int_hi=float(np.percentile(boot, 97.5)),
                bound_exact=x, bound=int(math.floor(x)),
                p_le_at_bound=float(p_at_most(NOBS, boot + math.floor(x)).mean()), boot_sum=float(boot.sum()))


RES = {}
_b0 = resample(None)
RES['binomial'] = summary(_b0)
_ref = RS['reference']
ck('C2 the binomial run IS chance_v414\'s resampling: its P and resampled sum, bit for bit',
   QUICK or (RES['binomial']['p'] == _ref['p_at_least_observed']
             and RES['binomial']['boot_sum'] == _ref['boot_null_sum']),
   'P %.6f vs %.6f, sum %.6f vs %.6f%s' % (RES['binomial']['p'], _ref['p_at_least_observed'],
                                          RES['binomial']['boot_sum'], _ref['boot_null_sum'],
                                          ' (quick: not asserted)' if QUICK else ''))
early_exit()


def _res_s(s):
    return s, summary(resample(s))


with _MP.Pool(min(NPROC, len(SCHEMES))) as _pool:
    for s, r in _pool.map(_res_s, [sname(k, p_) for k, p_ in SCHEMES]):
        RES[s] = r
for kind, par in SCHEMES:
    s = sname(kind, par)
    print('  %-8s P %.4f (se %.4f)  mean %.3f sd %.3f  interval %.2f-%.2f  bound %d (%.3f)'
          % (s, RES[s]['p'], RES[s]['p_se'], RES[s]['mean'], RES[s]['sd'], RES[s]['int_lo'], RES[s]['int_hi'],
             RES[s]['bound'], RES[s]['bound_exact']))
print('  %-8s P %.4f (se %.4f)  mean %.3f sd %.3f  interval %.2f-%.2f  bound %d (%.3f)'
      % ('binomial', RES['binomial']['p'], RES['binomial']['p_se'], RES['binomial']['mean'], RES['binomial']['sd'],
         RES['binomial']['int_lo'], RES['binomial']['int_hi'], RES['binomial']['bound'],
         RES['binomial']['bound_exact']))
_bl = [sname(k, p_) for k, p_ in SCHEMES]
_mse = max(RES[s]['p_se'] for s in _bl + ['binomial'])
ck('C3 every blocked resampling keeps the mean of the expectation (to 5 Monte Carlo errors)',
   all(abs(RES[s]['mean'] - RES['binomial']['mean'])
       < 5 * math.hypot(RES[s]['mean_se'], RES['binomial']['mean_se']) for s in _bl),
   ', '.join('%s %.3f' % (s, RES[s]['mean']) for s in _bl) + '; binomial %.3f' % RES['binomial']['mean'])

P_LO = min(RES[s]['p'] for s in _bl)
P_HI = max(RES[s]['p'] for s in _bl)
if DRIVE == 4:
    P_HI = RES['binomial']['p']
_shift = max(abs(RES[s]['p'] - RES['binomial']['p']) for s in _bl)
# ★ v4.33 (Ruling R13(b), as chance_v414 applies it to \CeProbNull): the ends print at the places at which they are
# stable over two Monte Carlo errors -- two, or one when two straddles a rounding edge (P 0.383-0.385 sat on 0.385)
def _stab(dp):
    return all('%.*f' % (dp, RES[s]['p'] - 2 * RES[s]['p_se']) == '%.*f' % (dp, RES[s]['p'])
               == '%.*f' % (dp, RES[s]['p'] + 2 * RES[s]['p_se']) for s in _bl if RES[s]['p'] in (P_LO, P_HI))


P_DP = 2 if _stab(2) else 1
_stable = _stab(P_DP)
ck('C4 the printed range is the min and max over the blockings, its printed ends are stable within two Monte '
   'Carlo errors, and the largest shift from the binomial is the largest |difference|',
   P_LO == min(RES[s]['p'] for s in _bl) and P_HI == max(RES[s]['p'] for s in _bl) and (_stable or QUICK)
   and abs(_shift - max(abs(P_HI - RES['binomial']['p']), abs(P_LO - RES['binomial']['p']))) < 1e-12,
   'P %.4f-%.4f over %d blockings, binomial %.4f, largest shift %.4f (MC se <= %.4f)'
   % (P_LO, P_HI, len(_bl), RES['binomial']['p'], _shift, _mse))

#: C5 -- "adopt it only if material": if keeping the correlation would change the probability AS PRINTED,
#: the build stops, because the page would then be quoting the binomial construction where it matters.
import adopted_e90 as _ae  # noqa: E402
_pub = _ae._texval('CeProbNull')
# v4.33: "as printed" = at the digits \CeProbNull is printed to (R13(b) can print it to one place: 0.4)
_dpp = len(_pub.split('.')[-1]) if _pub and '.' in _pub else 2
_ends = ({'%.*f' % (_dpp, P_LO), '%.*f' % (_dpp, P_HI)} if DRIVE != 6
         else {'%.*f' % (_dpp, P_LO + 2 * 10.0 ** -_dpp)})
ck('C5 keeping the correlation does not change the probability as printed (else adopt the blocked resampling)',
   _pub is not None and _ends == {_pub},
   'blocked %s against \\CeProbNull %s' % ('/'.join(sorted(_ends)), _pub))

if fail:
    print('\nFAILED: %s' % '; '.join(fail))
    raise SystemExit(1)
if DRIVE is not None:
    print('drive %d did not fire' % DRIVE)
    raise SystemExit(0)


# =====================================================================  macros and record
def f2(x):
    return '%.2f' % x


def rng_txt(a, b):
    """'a' when the two print alike, else 'a--b' (never the degenerate 'a--a')."""
    return a if a == b else '%s--%s' % (a, b)


m('CcNWin', '%d' % len(ALL))
m('CcNWinNoPos', '%d' % len(NOPOS))
m('CcNWinGeoOk', '%d' % N_GEO_OK)
m('CcNWinBeamRec', '%d' % len(REC))
m('CcNWinBeamFit', '%d' % (len(WIN) - len(REC)))
m('CcBeamFitMed', f2(FIT_MED))
m('CcBeamFitLo', f2(FIT_LO))
m('CcBeamFitHi', f2(FIT_HI))
m('CcRhoNear', f2(RHO_NEAR))
m('CcHalfBeam', f2(HALF_BEAM))
m('CcRhoHalfBeamOut', f2(RHO_OUT))
m('CcRhoIndNear', f2(RHOI_NEAR))
m('CcNLead', '%d' % N_LEAD)
m('CcLeadPct', '%.0f' % LEAD_PCT)
m('CcNeffLeadMed', '%d' % int(round(float(np.median(NEFF_LEAD)))))
m('CcNeffLeadMin', '%d' % int(round(float(NEFF_LEAD.min()))))
m('CcSdBinom', f2(SD_BINOM))
m('CcSdCorr', f2(max(SD_SCHEME.values())))
m('CcSdTotal', '%.1f' % RES['binomial']['sd'])
m('CcProbRange', rng_txt('%.*f' % (P_DP, P_LO), '%.*f' % (P_DP, P_HI)))
m('CcMaxShift', '%.3f' % _shift)
m('CcAddLimRange', rng_txt('%d' % min(RES[s]['bound'] for s in _bl), '%d' % max(RES[s]['bound'] for s in _bl)))
m('CcIntLo', '%.0f' % min(RES[s]['int_lo'] for s in _bl))
m('CcIntHi', '%.0f' % max(RES[s]['int_hi'] for s in _bl))

PERWIN = []
for x in ALL:
    w = x['w']
    if not x['pos']:
        PERWIN.append(dict(block_order=w['block_order'], window_order=w['window_order'], eb=w['eb'],
                           star_name=w['star_name'], flo_GHz=w['flo_GHz'], fhi_GHz=w['fhi_GHz'],
                           array=x['geo'].get('array'), ring_source=x['geo'].get('ring_source'),
                           r_in_arcsec=x['geo'].get('r_in_arcsec'), r_out_arcsec=x['geo'].get('r_out_arcsec'),
                           theta_syn_arcsec=None, theta_syn_source='unplaced', theta_fit_arcsec=None,
                           nn_sep_median_beam=None, n_close=None, rho_close=None, geometry_check='unplaced',
                           n_ctrl=int(x['v'].size), n_ctrl_trig=int(x['I'].sum()),
                           contribution=x['contrib'] * RS['scale'], lead=bool(any(x is y for y in LEAD)),
                           neff={}, neff_min=None, n_blocks={}))
        continue
    PERWIN.append(dict(block_order=w['block_order'], window_order=w['window_order'], eb=w['eb'],
                       star_name=w['star_name'], flo_GHz=w['flo_GHz'], fhi_GHz=w['fhi_GHz'],
                       array=x['geo']['array'], ring_source=x['geo']['ring_source'],
                       r_in_arcsec=x['geo']['r_in_arcsec'], r_out_arcsec=x['geo']['r_out_arcsec'],
                       theta_syn_arcsec=x['th'], theta_syn_source=x['th_src'], theta_fit_arcsec=x['th_fit'],
                       nn_sep_median_beam=float(np.median(np.sort(
                           np.hypot(x['l'][:, None] - x['l'][None, :], x['m'][:, None] - x['m'][None, :])
                           + np.eye(N_PROBE) * 1e9, axis=1)[:, 0]) / x['th']),
                       n_close=x['n_close'], rho_close=x['rho_close'], geometry_check=x['geo_check'],
                       n_ctrl=N_PROBE, n_ctrl_trig=int(x['I'].sum()), contribution=x['contrib'] * RS['scale'],
                       lead=bool(any(x is y for y in LEAD)),
                       neff={k: float(v) for k, v in x['neff'].items()}, neff_min=x['neff_min'],
                       n_blocks={k: int(v['K']) for k, v in x['blocks'].items()}))
json.dump(dict(produced_by='ctrlcorr_r32.py', round=ROUND, probe_seed=SEED_PROBE, n_probe=N_PROBE,
               template_bins_beam=XB.tolist(), template_rho=TEMPLATE.tolist(), correlogram=CORR,
               beam_fit=dict(median=FIT_MED, q25=FIT_LO, q75=FIT_HI, n_recorded=len(REC)),
               half_correlation_beam=HALF_BEAM, rho_near=RHO_NEAR, rho_near_shuffled=RHO_NEAR_SH,
               rho_indicator_near=RHOI_NEAR, n_lead=N_LEAD, lead_pct=LEAD_PCT,
               sd_window_term=dict(binomial=SD_BINOM, **SD_SCHEME), resampling=RES,
               schemes=[sname(k, p_) for k, p_ in SCHEMES], windows=PERWIN, quick=QUICK),
          open(OUT_JSON, 'w'), indent=1, sort_keys=True)
hdr = ['%% GENERATED by ctrlcorr_r32.py (round %d) -- do not hand-edit.' % ROUND,
       '% The spatial correlation of the control positions and the chance comparison re-resampled with it kept.']
open(OUT_TEX, 'w').write('\n'.join(hdr + sorted(OUT)) + '\n')
print('ctrlcorr_r32: %d windows (%d placed), %d macros -> %s' % (len(ALL), len(WIN), len(OUT), os.path.basename(OUT_TEX)))
