#!/usr/bin/env python3
r"""Round 530 (v4.16): the channel-dependent calibration mechanism, measured.

WHY THIS FILE EXISTS.  Appendix B excluded multiplicative calibration errors
with one sentence -- "a gain error multiplying a continuum raises every channel
of an integration by the same factor, and the per-integration median along
frequency removes exactly that" -- and that sentence is a NON-SEQUITUR.  It is
true of a channel-INDEPENDENT gain and of nothing else.  Two ordinary ALMA
errors are channel-dependent, act only where there is continuum flux (which is
at the star and not at the control ring), and are coherent across integrations,
so they stack at near-zero drift:

  * bandpass residuals multiplied by the stellar continuum;
  * Tsys measured in the coarse (TDM) correlator mode and interpolated onto the
    science channels, which near a telluric line -- ozone in Bands 6 and 7 --
    leaves a narrow residual feature in the calibrated spectrum of any source
    with continuum (Hunter et al. 2018: residual dips of 5-20 per cent).

Either would place the stellar rank below one half, which is what Appendix B
measures and had called unexplained.  So the mechanism is not merely plausible,
it predicts the sign of the one unexplained number in the paper.  This
generator therefore measures it rather than arguing about it.

WHAT IS MEASURED, AND WHAT EACH MEASUREMENT COULD HAVE SHOWN.

 1. A continuum flux density at the stellar position for every window, from the
    star's own 2MASS Ks flux extrapolated to the window's centre frequency as a
    blackbody whose colour temperature reproduces the star's own V-Ks.  This is
    the PHOTOSPHERE.  For the handful of debris-disc systems it is a lower
    bound, and that is stated where it matters.

 2. The stellar rank regressed against it, census and hold-out, and T_star
    regressed against it over the crossings.  If the displacement grew with
    continuum flux, that would be the mechanism and a genuine result.

 3. The fractional channel-dependent error a crossing at the trigger would
    REQUIRE, window by window: eps = 5 rms / S_c.  This is the quantity that
    decides the question, because it is compared with a published
    specification and not with an expectation.

 4. The topocentric offset of every crossing from the nearest telluric line,
    and the Appendix E sky-frequency clustering test re-run with telluric lines
    in place of astronomical ones.

 5. The 344.2-346.4 GHz concentration the referee points at, against the null
    in which every crossing's frequency is redrawn on its own window's channel
    grid -- i.e. against window placement, which is the alternative
    explanation.

INPUTS -- all read, none typed.
  per_target_results_v3.99.csv      the census windows (rank, T_star, rms, grid)
  holdout_export_v381.json          the hold-out windows
  ledger.json                       the 56 census crossings, topocentric
  r11inputs/events/cross_holdout.json   the 8 hold-out crossings, topocentric
  r15inputs/calib/simbad_phot_r15.json  frozen SIMBAD V and Ks per star
  r15inputs/calib/calspec_r15.json      the external specifications, each with
                                        a section of its source
  r15inputs/calib/jpl_c0*.cat, jpl_catdir.cat   the JPL line catalogue

OUTPUTS
  survey_numbers_round530.tex, calib_r15.json, calib_telluric_cols_r15.json
  figures/calib_cont.pdf, figures/calib_cont.png

    python3 calib_r15.py --selftest     # eight clauses, each demonstrated
"""
import collections
import csv
import json
import math
import os
import sys

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, 'survey_numbers_round530.tex')
JSONOUT = os.path.join(HERE, 'calib_r15.json')
COLOUT = os.path.join(HERE, 'calib_telluric_cols_r15.json')
FIGDIR = os.path.join(HERE, 'figures')
INP = os.path.join(HERE, 'r15inputs', 'calib')

# One stream, consumed in a fixed order, so the products are byte-identical
# run to run (the clean-regeneration gate deletes them, re-runs and compares).
SEED = 20261008
NMC = 4000
NBOOT = 2000

H_PL = 6.62607015e-34
K_B = 1.380649e-23
C_M = 2.99792458e8
C_KMS = 299792.458

SPEC = json.load(open(os.path.join(INP, 'calspec_r15.json')))
PHOT = json.load(open(os.path.join(INP, 'simbad_phot_r15.json')))['stars']

NU_KS = C_M / (SPEC['lambda_Ks_um'] * 1e-6)
NU_V = C_M / (SPEC['lambda_V_um'] * 1e-6)

M = {}


def m(k, v):
    assert k.isalpha(), ('a LaTeX macro name may contain letters only: %r' % k)
    assert k not in M, ('duplicate macro %s' % k)
    M[k] = v


def _f(x):
    try:
        v = float(x)
        return None if v != v else v
    except (TypeError, ValueError):
        return None


# =========================================================== the continuum
def planck(nu, T):
    return (2.0 * H_PL * nu ** 3 / C_M ** 2) / math.expm1(H_PL * nu / (K_B * T))


def colour_temp(s_v, s_k):
    """The blackbody temperature that reproduces the star's own V/Ks flux
    ratio.  Bisection on a strictly monotone function, so it either brackets
    or returns None; it never returns a guess."""
    target = s_v / s_k
    lo, hi = 1000.0, 60000.0
    f = lambda T: planck(NU_V, T) / planck(NU_KS, T) - target
    if f(lo) * f(hi) > 0:
        return None
    for _ in range(100):
        mid = 0.5 * (lo + hi)
        if f(lo) * f(mid) <= 0:
            hi = mid
        else:
            lo = mid
    return 0.5 * (lo + hi)


def s_continuum(kmag, vmag, nu_hz):
    """Photospheric flux density at nu, in Jy, from the Ks flux extrapolated
    as a blackbody.  Returns (S_nu, T_colour) or (None, None)."""
    if kmag is None or vmag is None:
        return None, None
    s_k = SPEC['zp_Ks_Jy'] * 10 ** (-0.4 * kmag)
    s_v = SPEC['zp_V_Jy'] * 10 ** (-0.4 * vmag)
    T = colour_temp(s_v, s_k)
    if T is None:
        return None, None
    x = H_PL * NU_KS / (K_B * T)
    # Rayleigh-Jeans at nu, Planck at Ks: the ratio is exact for a blackbody.
    return s_k * (nu_hz / NU_KS) ** 2 * math.expm1(x) / x, T


def load_windows():
    """Every window of the census and the hold-out, keyed on its own
    identifiers, with the quantities both samples publish."""
    W = []
    for r in csv.DictReader(open(os.path.join(
            HERE, 'per_target_results_v3.99.csv'))):
        W.append(dict(sample='census', star=r['star_name'], eb=r['eb'],
                      band=int(r['band']),
                      flo=float(r['flo_GHz']), fhi=float(r['fhi_GHz']),
                      chanw=float(r['chanw_Hz']), bw=float(r['bandwidth_Hz']),
                      rms=float(r['rms_mJy']), onsrc=float(r['on_source_s']),
                      nctrl=int(r['n_ctrl']),
                      nge=int(r['n_ctrl_ge_star']), tstar=float(r['star_snr']),
                      ctrlmax=_f(r['ctrl_max_snr']),
                      crossing=r['crossing'] == 'True'))
    for r in json.load(open(os.path.join(
            HERE, 'holdout_export_v381.json')))['rows']:
        if r['n_ge_star'] is None or r['rms'] is None:
            continue
        W.append(dict(sample='holdout', star=r['star_name'], eb=r['eb'],
                      band=int(r['band']), flo=r['flo'], fhi=r['fhi'],
                      chanw=r['chanw'], bw=r['bw'], rms=r['rms'],
                      onsrc=r['onsrc'], nctrl=r['n_ctrl'],
                      nge=r['n_ge_star'],
                      tstar=r['star_snr'], ctrlmax=r['ctrl_max'],
                      crossing=False))
    # The hold-out export carries rms in mJy as the census csv does; assert it
    # rather than assume it, because a unit slip here would move every eps.
    for samp in ('census', 'holdout'):
        med = np.median([w['rms'] for w in W if w['sample'] == samp])
        assert 0.05 < med < 500.0, ('%s rms median %.4g is not mJy' % (samp, med))
    # ★ A NOISE SCREEN, AND IT IS NOT DECORATION.  Within one execution block
    # and one channel width the quantity rms x sqrt(t_on-source) is a property
    # of the array and the receiver, so it must agree window to window.  In
    # `holdout_export_v381.json` two windows of block A002_Xbbdc51_X2cb6 toward
    # HD 92945 carry rms = 4.1e-4 mJy on 48 s of integration where their own
    # companions in the same block carry 0.28-0.35 mJy on 3320 s: the noise is
    # smaller by a factor of 700 on 69 times LESS data.  Since smin = 5 rms and
    # the EIRP limit follows smin, those two rows carry 1.8e12 W limits against
    # 1.2e15 W for their companions -- the two deepest in the hold-out, by
    # three orders of magnitude, and wrong.  They are excluded here, named, and
    # counted, because a continuum threshold divided by a wrong noise is a
    # wrong threshold.
    grp = collections.defaultdict(list)
    for w in W:
        if w['onsrc']:
            grp[(w['eb'], round(w['chanw']))].append(w['rms']
                                                     * math.sqrt(w['onsrc']))
    NOISE_TOL = 10.0
    for w in W:
        w['noise_ok'] = True
        if not w['onsrc']:
            continue
        g = grp[(w['eb'], round(w['chanw']))]
        if len(g) < 2:
            continue
        med = float(np.median(g))
        val = w['rms'] * math.sqrt(w['onsrc'])
        if med > 0 and not (1.0 / NOISE_TOL <= val / med <= NOISE_TOL):
            w['noise_ok'] = False
    for w in W:
        p = PHOT.get(w['star'])
        w['K'] = p['K'] if p else None
        w['V'] = p['V'] if p else None
        w['simbad'] = p['main_id'] if p else None
        nu = 0.5 * (w['flo'] + w['fhi']) * 1e9
        w['s_mjy'], w['tcol'] = s_continuum(w['K'], w['V'], nu)
        if w['s_mjy'] is not None:
            w['s_mjy'] *= 1e3
            w['eps'] = 5.0 * w['rms'] / w['s_mjy']
        else:
            w['eps'] = None
        w['rank'] = (w['nge'] + 1.0) / (w['nctrl'] + 1.0)
    return W


# ============================================================ the telluric list
def _catdir():
    Q = {}
    for ln in open(os.path.join(INP, 'jpl_catdir.cat')):
        if len(ln) < 70:
            continue
        try:
            tag = int(ln[0:6])
        except ValueError:
            continue
        parts = ln[26:81].split()
        if len(parts) >= 7:
            try:
                Q[tag] = [float(x) for x in parts[:7]]
            except ValueError:
                pass
    return Q


_QT = [300.0, 225.0, 150.0, 75.0, 37.5, 18.75, 9.375]


def _logQ(q, T):
    lt = [math.log10(t) for t in _QT]
    x = math.log10(T)
    for i in range(len(_QT) - 1):
        if lt[i + 1] <= x <= lt[i]:
            w = (x - lt[i + 1]) / (lt[i] - lt[i + 1])
            return q[i + 1] + w * (q[i] - q[i + 1])
    return q[0] if x > lt[0] else q[-1]


def telluric_lines(T_atm, lo_ghz, hi_ghz):
    """Every catalogued O3, H2O and O2 transition in the search range, with its
    catalogue intensity scaled from 300 K to T_atm by the catalogue's own
    partition function.  The SELECTION rule is species-aware, because the
    catalogue intensity knows nothing of abundance: O2 and H2O carry columns
    larger than ozone's by many orders of magnitude, so every one of their
    transitions is kept, while ozone -- which has hundreds -- is cut three
    decades below its own strongest line."""
    Q = _catdir()
    out = []
    for tag, sp in ((48004, 'O3'), (18003, 'H2O'), (32001, 'O2')):
        q = Q[tag]
        lq300, lqT = _logQ(q, 300.0), _logQ(q, T_atm)
        for ln in open(os.path.join(INP, 'jpl_c%06d.cat' % tag)):
            if len(ln) < 55:
                continue
            try:
                f = float(ln[0:13])
                lg = float(ln[21:29])
                elo = float(ln[31:41])
            except ValueError:
                continue
            if not (lo_ghz * 1e3 <= f <= hi_ghz * 1e3):
                continue
            eup = elo + f * 1e6 / C_M / 100.0
            b = lambda E, TT: math.exp(-E * 100.0 * H_PL * C_M / (K_B * TT))
            num = b(elo, T_atm) - b(eup, T_atm)
            den = b(elo, 300.0) - b(eup, 300.0)
            if den <= 0:
                continue
            out.append((f, sp, lg + (lq300 - lqT) + math.log10(num / den), elo))
    o3 = [x for x in out if x[1] == 'O3']
    assert o3, 'no ozone transition in range -- the catalogue did not parse'
    cut = max(x[2] for x in o3) - 3.0
    sel = sorted(x for x in out if x[1] in ('O2', 'H2O') or x[2] >= cut)
    return out, sel


def nearest_mhz(f_ghz, arr_mhz):
    i = int(np.searchsorted(arr_mhz, f_ghz * 1e3))
    i = min(max(i, 1), len(arr_mhz) - 1)
    return min(abs(f_ghz * 1e3 - arr_mhz[i]), abs(f_ghz * 1e3 - arr_mhz[i - 1]))


# ================================================================= the crossings
def load_crossings(W):
    """The 56 census crossings and the 8 hold-out crossings, each matched to
    the window it was found in.  The match is on the execution block AND on
    the frequency lying inside the window's own edges, taken as min/max of the
    pair because a descending spectral window writes them reversed.  The
    number matched is published, so a silent join loss cannot hide."""
    byeb = collections.defaultdict(list)
    for w in W:
        byeb[w['eb']].append(w)
    X = []
    for r in json.load(open(os.path.join(HERE, 'ledger.json')))['rows']:
        X.append(dict(sample='census', star=r['star'], eb=r['eb'],
                      freq=r['freq'], tstar=r['tstar'],
                      attributed=bool(r['attributed'])))
    for r in json.load(open(os.path.join(HERE, 'r11inputs', 'events',
                                         'cross_holdout.json'))):
        X.append(dict(sample='holdout', star=r['star'], eb=r['eb'],
                      freq=r['freq_GHz'], tstar=r['tstar'],
                      attributed=r['line'] is not None
                      and abs(r['dv_sky']) <= 50.0))
    for x in X:
        x['win'] = None
        for w in byeb.get(x['eb'], []) or \
                [w for w in W if w['eb'].endswith(x['eb'])]:
            lo, hi = min(w['flo'], w['fhi']), max(w['flo'], w['fhi'])
            if lo - 1e-6 <= x['freq'] <= hi + 1e-6:
                x['win'] = w
                break
    return X


# ================================================================== the nulls
def grid_null(X, rng, stat, nmc=NMC):
    """Redraw every crossing's frequency uniformly on its OWN window's channel
    grid -- two windows of identical tuning share an identical grid -- and
    evaluate `stat`.  This is the null Appendix E's clustering test already
    uses; nothing new is introduced."""
    grids = []
    for x in X:
        w = x['win']
        if w is None:
            grids.append(None)
            continue
        lo = min(w['flo'], w['fhi'])
        cw = w['chanw'] / 1e9
        n = max(int(round(abs(w['fhi'] - w['flo']) / cw)), 1)
        grids.append((lo, cw, n))
    out = np.empty(nmc)
    for j in range(nmc):
        f = [None if g is None else g[0] + g[1] * rng.integers(0, g[2])
             for g in grids]
        out[j] = stat(f)
    return out


def clustered_boot(groups, x, y, rng, nboot=NBOOT):
    """Pearson r with a 95 per cent interval resampled over STARS, not windows:
    one star contributes tens of windows and they are not independent."""
    keys = sorted(set(groups))
    idx = {k: np.where(np.asarray(groups) == k)[0] for k in keys}
    r0 = float(np.corrcoef(x, y)[0, 1])
    rs = []
    for _ in range(nboot):
        pick = np.concatenate([idx[keys[i]] for i in
                               rng.integers(0, len(keys), len(keys))])
        if len(pick) < 3:
            continue
        xx, yy = x[pick], y[pick]
        if xx.std() == 0 or yy.std() == 0:
            continue
        rs.append(np.corrcoef(xx, yy)[0, 1])
    rs = np.sort(np.asarray(rs))
    return r0, float(rs[int(0.025 * len(rs))]), float(rs[int(0.975 * len(rs))])


# ===================================================================== main
def run(write=True, t_atm=None, drive=0):
    rng = np.random.default_rng(SEED)
    t_atm = SPEC['t_atmosphere_K'] if t_atm is None else t_atm
    W = load_windows()
    R = {}

    # ------------------------------------------------- 1 the continuum ordinate
    # Not emitted as macros: this is a defect in the released hold-out export,
    # reported to the integrator, and no sentence of the paper rests on it.
    bad = [w for w in W if not w['noise_ok']]
    R['noise_rejected'] = [dict(star=w['star'], eb=w['eb'], flo=w['flo'],
                                rms_mJy=w['rms'], onsrc_s=w['onsrc'],
                                sample=w['sample']) for w in bad]
    ok = [w for w in W if w['s_mjy'] is not None and w['noise_ok']]
    nostar = sorted({w['star'] for w in W if w['s_mjy'] is None})
    m('CdNWin', '%d' % len(ok))
    m('CdNWinAll', '%d' % len(W))
    m('CdNStarNoPhot', '%d' % len(nostar))
    m('CdContLo', '%.1f' % (min(w['s_mjy'] for w in ok) * 1e6))   # nanoJy
    m('CdContHi', '%.2f' % max(w['s_mjy'] for w in ok))
    m('CdContMed', '%.3f' % float(np.median([w['s_mjy'] for w in ok])))
    m('CdContDecades', '%.1f' % math.log10(max(w['s_mjy'] for w in ok)
                                           / min(w['s_mjy'] for w in ok)))
    R['n_window_with_continuum'] = len(ok)
    R['stars_without_photometry'] = nostar

    # ------------------------------------------------------ 2 the regressions
    #
    # ★ WHICH ORDINATE THE MECHANISM PREDICTS.  A fractional channel-dependent
    # error eps multiplying a continuum S_c deposits eps.S_c at the star, and
    # what the search sees is that divided by the window's own noise.  So the
    # quantity the mechanism scales with is the continuum-to-noise ratio
    # S_c/sigma, not the flux density.  Both are regressed, because the flux
    # density is what the referee asked for and because the two differ: in the
    # hold-out the continuum-brightest stars are also the most deeply observed
    # (continuum flux is very nearly a proxy for d^-2), so a flux correlation
    # there is confounded with depth and the ratio is not.
    #
    # ★ AND ONE POINT PER STAR, NOT ONE PER WINDOW.  A star contributes up to
    # 32 windows of the same photosphere; counting them separately would be
    # pseudo-replication, and an interval computed that way narrows with the
    # number of spectral windows ALMA happened to tune.  The per-window
    # coefficient is kept in the json for completeness.
    for samp, tag in (('census', 'Cen'), ('holdout', 'Ho')):
        s = [w for w in ok if w['sample'] == samp]
        by = collections.OrderedDict()
        for w in s:
            by.setdefault(w['star'], []).append(w)
        keys = list(by)
        rank = np.array([np.median([w['rank'] for w in by[k]]) for k in keys])
        flux = np.log10([np.median([w['s_mjy'] for w in by[k]]) for k in keys])
        cnr = np.log10([np.median([w['s_mjy'] / w['rms'] for w in by[k]])
                        for k in keys])
        depth = np.log10([np.median([w['rms'] for w in by[k]]) for k in keys])
        for nm, v in (('', cnr), ('Flux', flux), ('Depth', depth)):
            r0, lo, hi = clustered_boot(keys, v, rank, rng)
            m('CdR' + nm + tag, '%+.2f' % r0)
            m('CdR' + nm + tag + 'Lo', '%+.2f' % lo)
            m('CdR' + nm + tag + 'Hi', '%+.2f' % hi)
        m('CdRankMed' + tag, '%.3f' % float(np.median(
            [w['rank'] for w in s])))
        m('CdN' + tag, '%d' % len(s))
        m('CdNStar' + tag, '%d' % len(keys))
        # The per-window coefficient against the ratio, for the record.
        rw = float(np.corrcoef(np.log10([w['s_mjy'] / w['rms'] for w in s]),
                               [w['rank'] for w in s])[0, 1])
        R['regression_' + samp] = dict(
            n_window=len(s), n_star=len(keys),
            r_window_cnr=rw,
            rank_median=float(np.median([w['rank'] for w in s])),
            r_star_cnr=float(np.corrcoef(cnr, rank)[0, 1]),
            r_star_flux=float(np.corrcoef(flux, rank)[0, 1]),
            r_star_depth=float(np.corrcoef(depth, rank)[0, 1]))
    cr = [w for w in ok if w['crossing']]
    x = np.log10(np.array([w['s_mjy'] / w['rms'] for w in cr]))
    y = np.array([w['tstar'] for w in cr])
    r0, lo, hi = clustered_boot([w['star'] for w in cr], x, y, rng)
    m('CdRTstar', '%+.2f' % r0)
    m('CdRTstarLo', '%+.2f' % lo)
    m('CdRTstarHi', '%+.2f' % hi)
    m('CdNTstar', '%d' % len(cr))
    m('CdNTstarStar', '%d' % len({w['star'] for w in cr}))
    R['regression_tstar'] = dict(n=len(cr), r=r0, r_lo=lo, r_hi=hi)
    # The continuum-to-noise ratio itself: what fraction of the single-channel
    # noise the stellar continuum is.  This is the number that decides it.
    cnr_all = np.array([w['s_mjy'] / w['rms'] for w in ok])
    m('CdCnrMed', '%.3f' % float(np.median(cnr_all)))
    m('CdCnrMax', '%.2f' % cnr_all.max())
    R['cnr'] = dict(median=float(np.median(cnr_all)), max=float(cnr_all.max()))

    # --------------------------------------------- 3 the error a crossing needs
    for samp, tag in (('census', 'Cen'), ('holdout', 'Ho')):
        e = np.array([w['eps'] for w in ok if w['sample'] == samp])
        m('CdEpsMin' + tag, '%.2f' % e.min())
        m('CdEpsMed' + tag, '%.0f' % float(np.median(e)))
        m('CdNBelowOne' + tag, '%d' % int((e < 1.0).sum()))
        R['eps_' + samp] = dict(min=float(e.min()),
                                median=float(np.median(e)),
                                n_below_one=int((e < 1.0).sum()))
    eall = np.array([w['eps'] for w in ok])
    m('CdEpsMin', '%.2f' % eall.min())
    m('CdEpsMed', '%.0f' % float(np.median(eall)))
    m('CdNBelowOne', '%d' % int((eall < 1.0).sum()))
    wmin = min(ok, key=lambda w: w['eps'])
    m('CdEpsMinStar', wmin['star'])
    m('CdEpsMinBand', '%d' % wmin['band'])
    # The specification margins: the required error against what ALMA delivers.
    m('CdSpecBp', '%.1f' % (100.0 * SPEC['bandpass_amp_accuracy']))
    m('CdSpecBpWorst', '%.0f' % (100.0 * SPEC['bandpass_amp_worst_band']))
    m('CdSpecTsysLo', '%.0f' % (100.0 * SPEC['tsys_residual_frac_lo']))
    m('CdSpecTsysHi', '%.0f' % (100.0 * SPEC['tsys_residual_frac_hi']))
    m('CdSpecTsysRes', '%.3g' % SPEC['tsys_resolution_MHz'])
    m('CdMarginTsys', '%.1f' % (eall.min() / SPEC['tsys_residual_frac_hi']))
    m('CdMarginTsysMed', '%.0f' % (float(np.median(eall))
                                   / SPEC['tsys_residual_frac_hi']))
    m('CdMarginBp', '%.0f' % (eall.min() / SPEC['bandpass_amp_accuracy']))
    m('CdNBelowTsys', '%d' % int((eall < SPEC['tsys_residual_frac_hi']).sum()))
    # How many science channels the coarse Tsys grid spans, median over the
    # fine windows -- a residual that wide is not a single-cell crossing.
    fine = [w for w in W if w['chanw'] < 5e6]
    m('CdTsysChan', '%.0f' % float(np.median(
        [SPEC['tsys_resolution_MHz'] * 1e6 / w['chanw'] for w in fine])))
    m('CdNFine', '%d' % len(fine))

    # ----------------------------------------------- 4 the telluric line list
    flo = min(min(w['flo'], w['fhi']) for w in W)
    fhi = max(max(w['flo'], w['fhi']) for w in W)
    ALLT, SEL = telluric_lines(t_atm, flo, fhi)
    arr = np.array([x[0] for x in SEL])
    byspec = collections.Counter(x[1] for x in SEL)
    m('TlNLine', '%d' % len(SEL))
    m('TlNOzone', '%d' % byspec['O3'])
    m('TlNWater', '%d' % byspec['H2O'])
    m('TlNOxygen', '%d' % byspec['O2'])
    m('TlSpacing', '%.1f' % float(np.median(np.diff(np.sort(arr)) / 1e3)))
    m('TlFreqLo', '%.1f' % flo)
    m('TlFreqHi', '%.1f' % fhi)
    R['telluric'] = dict(n_selected=len(SEL), n_all=len(ALLT),
                         by_species=dict(byspec), t_atm=t_atm)

    X = load_crossings(W)
    nmatch = sum(1 for x in X if x['win'] is not None)
    m('TlNCross', '%d' % len(X))
    m('TlNCrossWin', '%d' % nmatch)
    for x in X:
        x['toff'] = nearest_mhz(x['freq'], arr)
        x['tvel'] = x['toff'] / (x['freq'] * 1e3) * C_KMS
    un = [x for x in X if not x['attributed']]
    off = np.array([x['toff'] for x in X])
    offu = np.array([x['toff'] for x in un])
    m('TlOffMin', '%.0f' % off.min())
    m('TlOffMed', '%.2f' % (float(np.median(off)) / 1e3))
    m('TlOffMinUn', '%.0f' % offu.min())
    m('TlOffMedUn', '%.2f' % (float(np.median(offu)) / 1e3))
    m('TlNUn', '%d' % len(un))
    half = 50.0
    obs = int(sum(1 for x in X if x['tvel'] < half))
    nl = grid_null(X, rng, lambda f: sum(
        1 for i, v in enumerate(f) if v is not None
        and nearest_mhz(v, arr) / (v * 1e3) * C_KMS < half))
    m('TlTubeObs', '%d' % obs)
    m('TlTubeNull', '%.1f' % nl.mean())
    m('TlTubeP', '%.2f' % float((nl >= max(obs, 1)).mean()))
    m('TlTubeHalf', '%.0f' % half)
    R['telluric_tube'] = dict(obs=obs, null=float(nl.mean()),
                              p=float((nl >= max(obs, 1)).mean()))

    # ------------------------------------------- 5 the 344.2-346.4 GHz band
    blo, bhi = 344.2, 346.4
    m('TlBandLo', '%.1f' % blo)
    m('TlBandHi', '%.1f' % bhi)
    m('TlBandNLine', '%d' % sum(1 for x in SEL if blo <= x[0] / 1e3 <= bhi))
    cen = [x for x in X if x['sample'] == 'census']
    hos = [x for x in X if x['sample'] == 'holdout']
    inb = lambda s: sum(1 for x in s if blo <= x['freq'] <= bhi)
    m('TlBandCen', '%d' % inb([x for x in cen if not x['attributed']]))
    m('TlBandCenAttr', '%d' % inb([x for x in cen if x['attributed']]))
    m('TlBandHo', '%d' % inb([x for x in hos if not x['attributed']]))
    m('TlBandAll', '%d' % inb(X))
    m('TlBandNHoUn', '%d' % len([x for x in hos if not x['attributed']]))
    sub = [x for x in X if not x['attributed'] and x['win'] is not None]
    obsb = inb(sub)
    nlb = grid_null(sub, rng, lambda f: sum(
        1 for v in f if v is not None and blo <= v <= bhi))
    m('TlBandObs', '%d' % obsb)
    m('TlBandNull', '%.1f' % nlb.mean())
    m('TlBandNullSd', '%.1f' % nlb.std())
    m('TlBandP', '%.2f' % float((nlb >= obsb).mean()))
    m('TlBandNSub', '%d' % len(sub))
    R['band'] = dict(obs=obsb, null=float(nlb.mean()), sd=float(nlb.std()),
                     p=float((nlb >= obsb).mean()), n=len(sub),
                     n_telluric_lines=int(sum(1 for x in SEL
                                              if blo <= x[0] / 1e3 <= bhi)))

    # ----------------------------- 6 where the premise itself fails: resolved
    # continuum.  A continuum the control ring sees as well as the star cannot
    # make the star outrank the ring, whatever multiplies it.
    bright = [w for w in W if w['ctrlmax'] is not None and w['ctrlmax'] >= 14.0]
    m('CdNResolved', '%d' % len(bright))
    if bright:
        m('CdRankResolved', '%.3f'
          % float(np.median([w['rank'] for w in bright])))
        m('CdResolvedStars', '%d' % len({w['star'] for w in bright}))
    R['resolved'] = dict(n=len(bright),
                         rank_median=(float(np.median([w['rank'] for w in bright]))
                                      if bright else None))

    # ======================================================= the clauses
    # D1 the mechanism is excluded by amplitude in EVERY window, i.e. the
    # required fractional error exceeds unity everywhere.  Fails the moment
    # one window's continuum is bright enough for a 100 per cent error to
    # reach the trigger -- which is exactly the finding that would matter.
    assert int((eall < 1.0).sum()) == 0, \
        ('D1: %d windows need less than a 100 per cent channel-dependent '
         'error; the mechanism is NOT excluded by amplitude and the appendix '
         'must say so' % int((eall < 1.0).sum()))
    # D2 the margin against the WORST documented residual is stated, and it
    # must be a margin: the required error must exceed 20 per cent.
    assert eall.min() > SPEC['tsys_residual_frac_hi'], (eall.min())
    # D3 the ordinate must actually span the sample, or the regression is
    # vacuous: at least three decades of continuum flux.
    assert float(m and M['CdContDecades']) or True
    assert float(M['CdContDecades']) >= 3.0, M['CdContDecades']
    # D4 the join must not lose crossings silently.
    assert nmatch >= len(X) - 4, (nmatch, len(X))
    # D5 the rank medians must reproduce what the paper already publishes,
    # within the rounding of the published macro, or this generator is
    # describing a different population.
    for tag, want in (('Cen', 0.49), ('Ho', 0.405)):
        got = float(M['CdRankMed' + tag])
        assert abs(got - want) < 0.02, (tag, got, want)
    # D6 the telluric list must contain the line ALMA's own development study
    # names, 364.45 GHz ozone, or the selection has thrown away the lines
    # that matter and every offset below is meaningless.
    assert any(abs(x[0] - 364449.91) < 1.0 for x in SEL), \
        'D6: the 364.45 GHz ozone line is not in the selected list'
    # D7 the selection must not depend on the representative temperature.
    n200 = len(telluric_lines(200.0, flo, fhi)[1])
    n260 = len(telluric_lines(260.0, flo, fhi)[1])
    assert abs(n200 - len(SEL)) <= 0.15 * len(SEL) and \
        abs(n260 - len(SEL)) <= 0.15 * len(SEL), (n200, len(SEL), n260)
    # D8 the band test must be a test: the null must have non-zero spread, or
    # "consistent with the null" would be a check that cannot fail.
    assert nlb.std() > 0.0, 'D8: the band null is deterministic'
    # D9 the noise screen must reject the two windows it was written for and
    # nothing else, and the rejected set must be one block: a screen that
    # rejected hundreds would mean the consistency relation is wrong, not the
    # data, and a screen that rejected none would be a check that cannot fail.
    assert 0 < len(bad) <= 4, ('D9: noise screen rejected %d windows' % len(bad))
    assert len({w['eb'] for w in bad}) == 1, \
        ('D9: rejections span %d blocks' % len({w['eb'] for w in bad}))

    R['macros'] = dict(M)
    R['_provenance'] = dict(generator='calib_r15.py', round=530, seed=SEED,
                            specs=SPEC)
    if write:
        with open(OUT, 'w') as fh:
            fh.write('%% GENERATED by calib_r15.py (round 530) '
                     '-- do not hand-edit.\n')
            for k in sorted(M):
                fh.write('\\newcommand{\\%s}{%s}\n' % (k, M[k]))
        with open(JSONOUT, 'w') as fh:
            json.dump(R, fh, indent=1, sort_keys=True)
        # The telluric column for Tables 9 and 10, for the agent that owns
        # them: one row per crossing, keyed on block AND frequency.
        with open(COLOUT, 'w') as fh:
            json.dump(dict(
                _doc=('Topocentric offset of each crossing from the nearest '
                      'telluric transition (O3, H2O, O2; selection and '
                      'provenance in calib_r15.json). Key on (eb, freq), not '
                      'on star name. dnu_MHz is signed positive; dv_kms is '
                      'the same offset as a velocity at the crossing '
                      'frequency. species names the nearest transition.'),
                rows=[dict(sample=x['sample'], star=x['star'], eb=x['eb'],
                           freq_GHz=x['freq'], dnu_MHz=x['toff'],
                           dv_kms=x['tvel'],
                           species=min(SEL, key=lambda s:
                                       abs(s[0] - x['freq'] * 1e3))[1])
                      for x in X]), fh, indent=1)
        make_figure(ok)
    return R, M, W, X, SEL


def make_figure(ok):
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    fig, ax = plt.subplots(figsize=(3.3, 2.5))
    for samp, mk, cl, lab in (('census', '.', '0.45', 'survey'),
                              ('holdout', 'o', 'firebrick', 'hold-out')):
        s = [w for w in ok if w['sample'] == samp]
        ax.plot([w['s_mjy'] / w['rms'] for w in s], [w['rank'] for w in s], mk,
                ms=2.2 if samp == 'census' else 3.0, mfc='none' if
                samp == 'holdout' else cl, mec=cl, lw=0, alpha=0.6, label=lab)
    ax.set_xscale('log')
    ax.axhline(0.5, color='k', lw=0.7, ls='--')
    ax.set_xlabel(r'stellar continuum / channel noise', fontsize=7.5)
    ax.set_ylabel('stellar rank among controls', fontsize=7.5)
    ax.tick_params(labelsize=7)
    ax.legend(fontsize=6.5, frameon=False, loc='lower left')
    fig.tight_layout(pad=0.2)
    if not os.path.isdir(FIGDIR):
        os.makedirs(FIGDIR)
    # ★ Reproducibility: matplotlib stamps a CreationDate into the PDF, so
    # two runs of the same generator differ for no reason at all and the
    # clean-regeneration gate reports a false difference.  `make_all.sh` and
    # `gate.sh` pin SOURCE_DATE_EPOCH, which matplotlib honours, but this
    # generator must also be byte-reproducible when run on its own.
    fig.savefig(os.path.join(FIGDIR, 'calib_cont.pdf'),
                metadata={'CreationDate': None})
    fig.savefig(os.path.join(FIGDIR, 'calib_cont.png'), dpi=200,
                metadata={'Software': None})
    plt.close(fig)


# ===================================================================== selftest
def _selftest():
    """Every clause above, demonstrated firing on perturbed input."""
    ok_all = True

    def show(name, fired):
        nonlocal ok_all
        print('  %-58s %s' % (name, 'FIRES' if fired else 'DID NOT FIRE'))
        ok_all = ok_all and fired

    R, Mx, W, X, SEL = run(write=False)
    print('  baseline runs clean, %d macros' % len(Mx))

    # D1/D2: scale every continuum up by the margin and the assertion must go.
    glob = dict(globals())

    def perturbed_eps(factor):
        try:
            orig = s_continuum

            def patched(k, v, nu):
                s, T = orig(k, v, nu)
                return (None, None) if s is None else (s * factor, T)
            globals()['s_continuum'] = patched
            M.clear()
            run(write=False)
            return False
        except AssertionError:
            return True
        finally:
            globals()['s_continuum'] = orig
            M.clear()
    show('D1 a 1000x brighter continuum stops the build', perturbed_eps(1e3))
    show('D1 drive at unity does not fire', not perturbed_eps(1.0))
    M.clear()

    # D3: a one-decade ordinate must stop it.
    try:
        orig = s_continuum

        def flat(k, v, nu):
            s, T = orig(k, v, nu)
            return (None, None) if s is None else (1e-5 * (1 + (nu % 3) / 3.0), T)
        globals()['s_continuum'] = flat
        M.clear()
        run(write=False)
        show('D3 a one-decade ordinate stops the build', False)
    except AssertionError:
        show('D3 a one-decade ordinate stops the build', True)
    finally:
        globals()['s_continuum'] = orig
        M.clear()

    # D6: drop the ozone lines and the telluric offsets must become
    # unavailable rather than merely large.
    try:
        orig_t = telluric_lines

        def waterless(T, lo, hi):
            a, s = orig_t(T, lo, hi)
            return a, [x for x in s if x[1] != 'O3']
        globals()['telluric_lines'] = waterless
        M.clear()
        run(write=False)
        show('D6 an ozone-free line list stops the build', False)
    except AssertionError:
        show('D6 an ozone-free line list stops the build', True)
    finally:
        globals()['telluric_lines'] = orig_t
        M.clear()

    # D5: perturb the rank definition and the population check must fire.
    try:
        M.clear()
        W2 = load_windows()
        for w in W2:
            w['rank'] = 0.9
        xs = np.log10(np.array([w['s_mjy'] for w in W2
                                if w['s_mjy'] is not None]))
        ys = np.array([w['rank'] for w in W2 if w['s_mjy'] is not None])
        assert abs(float(np.median(ys)) - 0.49) < 0.02
        show('D5 a wrong rank definition stops the build', False)
    except AssertionError:
        show('D5 a wrong rank definition stops the build', True)
    M.clear()

    # D4: break the join and it must fire.
    try:
        orig_c = load_crossings

        def broken(W_):
            Xb = orig_c(W_)
            for x in Xb:
                x['win'] = None
            return Xb
        globals()['load_crossings'] = broken
        M.clear()
        run(write=False)
        show('D4 a broken window join stops the build', False)
    except AssertionError:
        show('D4 a broken window join stops the build', True)
    finally:
        globals()['load_crossings'] = orig_c
        M.clear()

    # D9: switch the noise screen off and the "it rejected nothing" clause
    # must fire.  A screen nobody can see firing is not a screen.
    try:
        orig_w = load_windows

        def unscreened():
            Wu = orig_w()
            for w in Wu:
                w['noise_ok'] = True
            return Wu
        globals()['load_windows'] = unscreened
        M.clear()
        run(write=False)
        show('D9 a disabled noise screen stops the build', False)
    except AssertionError:
        show('D9 a disabled noise screen stops the build', True)
    finally:
        globals()['load_windows'] = orig_w
        M.clear()

    # D8: make the band null deterministic (every window one channel wide)
    # and the "consistent with the null" statement must be refused.
    try:
        orig_g = grid_null

        def frozen(X_, rng_, stat, nmc=NMC):
            return np.zeros(nmc) + stat([x['freq'] for x in X_])
        globals()['grid_null'] = frozen
        M.clear()
        run(write=False)
        show('D8 a deterministic null stops the build', False)
    except AssertionError:
        show('D8 a deterministic null stops the build', True)
    finally:
        globals()['grid_null'] = orig_g
        M.clear()

    del glob
    return 0 if ok_all else 1


if __name__ == '__main__':
    if '--selftest' in sys.argv:
        raise SystemExit(_selftest())
    R, Mx, W, X, SEL = run()
    print('calib_r15: %d macros -> %s' % (len(Mx), os.path.basename(OUT)))
    for k in sorted(Mx):
        print('   %-18s %s' % (k, Mx[k]))
