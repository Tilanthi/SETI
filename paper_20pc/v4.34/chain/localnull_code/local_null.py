#!/usr/bin/env python3
"""
Second-stage LOCAL NULL for the four flagged windows of the ALMA
technosignature survey (referee A item 5).

METHOD -- "integration-scramble" (time-slide) null
-------------------------------------------------
The first-stage screen compares the star's search statistic T against the
maxima of 512 control positions, so its smallest resolvable p-value is
1/(1+512) = 1.95e-3.  To resolve deeper we need many more independent
realisations of the SAME statistic under the SAME local noise conditions.

For a control position q let R_q[t,c] be the baseline-subtracted residual
(integration t, channel c) and sigma[t,c] the pipeline's own all-probe
robust noise map (retained in *_search.npz).  Define the standardised
residual Z_q[t,c] = R_q[t,c]/sigma[t,c].

A null realisation is produced by giving every integration its own
independent random CIRCULAR shift in channel:

    Ztilde[t,c] = Z_q[t, (c + delta_t) mod nch],   delta_t ~ U{0..nch-1}
    Rtilde[t,c] = Ztilde[t,c] * sigma[t,c]

and then running the IDENTICAL de-drift search (same sigma, same weights,
same drift grid, same edge trim, same channel count) on Rtilde.

Why this is a valid local null:
  * Rtilde has exactly the same per-integration, per-channel noise scale as
    the real data (sigma is never scrambled, only the dimensionless
    fluctuation is), so atmospheric/bandpass/weight structure is preserved.
  * A rigid circular shift preserves each integration's spectral
    autocorrelation exactly, so residual baseline structure is preserved.
  * The shifts are independent across integrations, so NO feature that is
    coherent across integrations along any drift track can survive: the
    realisation is signal-free by construction.
  * The statistic is a maximum over the same nch channels x n_drift trials,
    so the trials factor / multiplicity is identical to the star's.
  * Unlike a null built by resampling the 512 control MAXIMA, this null is
    not bounded above by any already-observed value, so the tail is
    resolvable far beyond 1/513.

Cross-check null: disjoint spectral sub-bands of the real (unscrambled)
control positions, which samples genuinely independent spectral offsets
within the same window.

Nothing under /data/SETI/bin is modified; nothing is written into any
target products directory.
"""
import os, sys, json, time, math
for _v in ('OMP_NUM_THREADS','OPENBLAS_NUM_THREADS','MKL_NUM_THREADS',
           'NUMEXPR_NUM_THREADS','VECLIB_MAXIMUM_THREADS'):
    os.environ[_v] = '1'
import numpy as np
import multiprocessing as mp

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from validate_tstar import prepare, drift_search, WINDOWS

OUTDIR = '/data/SETI/work/localnull_v342'
_G = {}


# ----------------------------------------------------------------- workers
def _den_all(invvar, shifts):
    """Denominator sqrt(sum_t invvar) for every drift trial -- identical for
    every realisation, so compute once."""
    nd = shifts.shape[0]; nint, nch = invvar.shape
    den = np.zeros((nd, nch), dtype=np.float64)
    for k in range(nd):
        d = den[k]
        for t in range(nint):
            s = int(shifts[k, t])
            if s == 0:
                d += invvar[t]
            elif s > 0:
                if s >= nch: continue
                d[:nch - s] += invvar[t][s:]
            else:
                s = -s
                if s >= nch: continue
                d[s:] += invvar[t][:nch - s]
    return den


def _init(Z, u, shifts, den, nch, nint):
    _G.update(Z=Z, u=u, shifts=shifts, den=den, nch=nch, nint=nint)


def _chunk(args):
    """Run R scramble realisations as a batched 'position' axis."""
    seed, R = args
    Z = _G['Z']; u = _G['u']; shifts = _G['shifts']; den = _G['den']
    nch = _G['nch']; nint = _G['nint']
    nq = Z.shape[0]
    rng = np.random.default_rng(seed)
    q = rng.integers(0, nq, size=R)
    delta = rng.integers(0, nch, size=(R, nint))

    # X[t, j, c] = Z[q_j, t, (c+delta) mod nch] * u[t, c]
    X = np.empty((nint, R, nch), dtype=np.float32)
    for j in range(R):
        Zj = Z[q[j]]
        for t in range(nint):
            X[t, j] = np.roll(Zj[t], int(delta[j, t]))
    X *= u[:, None, :]

    best = np.full((R, nch), -np.inf, dtype=np.float32)
    num = np.empty((R, nch), dtype=np.float64)
    for k in range(shifts.shape[0]):
        num[:] = 0.0
        for t in range(nint):
            s = int(shifts[k, t])
            if s == 0:
                num += X[t]
            elif s > 0:
                if s >= nch: continue
                num[:, :nch - s] += X[t][:, s:]
            else:
                s = -s
                if s >= nch: continue
                num[:, s:] += X[t][:, :nch - s]
        with np.errstate(invalid='ignore', divide='ignore'):
            snr = np.nan_to_num(num / np.sqrt(den[k])[None, :]).astype(np.float32)
        np.maximum(best, snr, out=best)
    return best.max(axis=1).astype(np.float64)


# ------------------------------------------------------------------- stats
def gev_tail(null, T, n_cells=None):
    """Fit GEV and Gumbel to the null maxima.  These are PARAMETRIC
    EXTRAPOLATIONS far beyond the sampled range and are reported as
    illustrative only, never as the headline number."""
    out = {}
    try:
        from scipy.stats import genextreme, gumbel_r, kstest, norm
        c, loc, sc = genextreme.fit(null)
        ks = kstest(null, 'genextreme', args=(c, loc, sc))
        out.update(gev_shape_c=float(c), gev_loc=float(loc), gev_scale=float(sc),
                   gev_ks_stat=float(ks.statistic), gev_ks_p=float(ks.pvalue),
                   p_gev=float(genextreme.sf(T, c, loc=loc, scale=sc)))
        # scipy's c>0  <=>  EVT shape xi<0  <=>  tail BOUNDED at loc+scale/c.
        if c > 0:
            out['gev_upper_endpoint'] = float(loc + sc / c)
            out['gev_tail_bounded'] = True
            out['gev_note'] = ('GEV shape implies a BOUNDED upper tail; sf() '
                               'returns exactly 0 beyond the endpoint, which is '
                               'an artefact of the fit, not a measured p-value.')
        else:
            out['gev_tail_bounded'] = False
        g_loc, g_sc = gumbel_r.fit(null)
        ksg = kstest(null, 'gumbel_r', args=(g_loc, g_sc))
        out.update(gumbel_loc=float(g_loc), gumbel_scale=float(g_sc),
                   gumbel_ks_stat=float(ksg.statistic), gumbel_ks_p=float(ksg.pvalue),
                   p_gumbel=float(gumbel_r.sf(T, g_loc, g_sc)))
        # Gaussian-trials model: calibrate an effective independent trials
        # count N_eff from the null MEDIAN, then P(max>=T) = 1 - Phi(T)^N_eff.
        med = float(np.median(null))
        lp = norm.logcdf(med)
        n_eff = float(math.log(0.5) / lp) if lp < 0 else float('nan')
        out['n_eff_trials'] = n_eff
        out['n_cells_nominal'] = n_cells
        out['p_gauss_trials'] = float(-np.expm1(n_eff * norm.logcdf(T)))
    except Exception as e:
        out['error'] = f'{type(e).__name__}: {e}'
    return out


def p_against(null, val):
    """Conservative (+1) empirical p-value of `val` against the null sample."""
    B = null.size
    n = int((null >= val).sum())
    return dict(n_ge=n, p=(1 + n) / (1 + B), is_upper_bound=bool(n == 0),
                rule_of_three_95UCL=3.0 / B)


def subband_null(best_ctrl, ndrift, M=32):
    """Independent spectral offsets: max over each of M disjoint sub-bands,
    for each retained control position.  best_ctrl is (nctrl, nch) already
    maximised over drift."""
    nctrl, nch = best_ctrl.shape
    edges = np.linspace(0, nch, M + 1).astype(int)
    vals = [float(best_ctrl[p, edges[m]:edges[m + 1]].max())
            for p in range(nctrl) for m in range(M)]
    return vals


def run_window(idx, ndraw, nworkers, chunk):
    tdir, stem, fc, T_pub, ring_pub = WINDOWS[idx]
    t0 = time.time()
    d = prepare(tdir, stem)
    res = d['res']
    nint, nch = d['nint'], d['nch']
    sigma = d['sigma']; invvar = d['invvar']; shifts = d['shifts']

    # standardised residuals of the 8 retained control positions
    with np.errstate(invalid='ignore', divide='ignore'):
        Zc = np.nan_to_num(d['I_ctrl'] / sigma[:, None, :])      # (nint, nq, nch)
    Z = np.ascontiguousarray(np.transpose(Zc, (1, 0, 2)).astype(np.float32))  # (nq,nint,nch)
    u = np.nan_to_num(1.0 / sigma).astype(np.float32)

    # whiteness / scale diagnostics of the standardised residuals
    lag1 = float(np.nanmean([np.corrcoef(Z[q, t, :-1], Z[q, t, 1:])[0, 1]
                             for q in range(Z.shape[0])
                             for t in range(0, nint, max(1, nint // 20))]))
    zstd = float(np.nanstd(Z)); zkurt = float(np.nanmean(Z**4) / max(np.nanmean(Z**2), 1e-30)**2)

    # real (unscrambled) star + control search -> validation + sub-band null
    I = np.concatenate([d['I_star'][:, None, :], d['I_ctrl']], axis=1)
    best, _ = drift_search(I, invvar, shifts)
    T_star = float(best[0].max())
    T_ctrl8 = best[1:].max(axis=1).astype(float)
    sub = subband_null(best[1:], shifts.shape[0], M=32)

    den = _den_all(invvar, shifts)

    # ---- scramble null ----
    nchunk = int(math.ceil(ndraw / chunk))
    jobs = [(20260911000 + idx * 1000000 + i, chunk) for i in range(nchunk)]
    with mp.get_context('fork').Pool(nworkers, initializer=_init,
                                     initargs=(Z, u, shifts, den, nch, nint)) as pool:
        parts = []
        for n, r in enumerate(pool.imap_unordered(_chunk, jobs)):
            parts.append(r)
            if n % 20 == 0:
                print(f'[{tdir}] scramble chunk {n+1}/{nchunk} '
                      f'({time.time()-t0:.0f} s)', flush=True)
    null = np.concatenate(parts)[:ndraw]
    B = int(null.size)

    n_ge = int((null >= T_star).sum())
    p_emp = (1 + n_ge) / (1 + B)
    p_rule3 = 3.0 / B                         # 95% one-sided UCL when n_ge == 0
    q = np.percentile(null, [50, 90, 99, 99.9, 99.99, 100])

    # first-stage numbers for comparison
    cm = d['ctrl_max'].astype(float)
    p_stage1 = (1 + int((cm >= T_star).sum())) / (1 + cm.size)
    floor1 = 1.0 / (1 + cm.size)

    # ---- NULL SELF-VALIDATION ------------------------------------------
    # The scramble null must reproduce the distribution of the 512 REAL
    # control maxima measured by the first stage.  If it sits systematically
    # low the null is anti-conservative and must not be used.
    try:
        from scipy.stats import ks_2samp
        ks2 = ks_2samp(null, cm)
        ks2 = dict(stat=float(ks2.statistic), p=float(ks2.pvalue))
    except Exception as e:
        ks2 = dict(error=str(e))
    nullval = dict(
        null_median=float(np.median(null)), real512_median=float(np.median(cm)),
        null_p90=float(np.percentile(null, 90)), real512_p90=float(np.percentile(cm, 90)),
        null_p99=float(np.percentile(null, 99)), real512_p99=float(np.percentile(cm, 99)),
        null_max=float(null.max()), real512_max=float(cm.max()),
        median_offset=float(np.median(null) - np.median(cm)),
        ks_2samp_null_vs_real512=ks2,
        frac_real512_above_null_p99=float((cm > np.percentile(null, 99)).mean()),
    )

    # ---- DISCRIMINATION DIAGNOSTIC -------------------------------------
    # Score the CONTROL positions against the same local null.  If controls
    # are also "significant", the local null is measuring only thermal-like
    # noise and the binding test remains the first-stage star-vs-control
    # spatial comparison.
    ctrl_diag = dict(
        ring_max_vs_local_null=p_against(null, float(cm.max())),
        ctrl_p99_vs_local_null=p_against(null, float(np.percentile(cm, 99))),
        n_of_512_controls_with_p_local_below_bonferroni=int(
            (cm >= np.percentile(null, 100 * (1 - 1.2e-4))).sum())
        if B >= 10000 else None,
        n_of_512_controls_exceeding_null_max=int((cm > null.max()).sum()),
    )

    rec = dict(
        target=tdir, window=stem, band=res.get('alma_band_inferred'),
        centre_GHz=0.5 * (res['freq_lo_GHz'] + res['freq_hi_GHz']),
        srcspec_file=f'/data/SETI/targets/{tdir}/products/{stem}_srcspec.npz',
        search_file=f'/data/SETI/targets/{tdir}/products/{stem}_search.npz',
        n_int=nint, n_chan=nch, n_drift=int(shifts.shape[0]),
        n_control_retained=int(Z.shape[0]),
        T_star_published=float(res['star_peak_snr']), T_star_paper=T_pub,
        T_star_reproduced=T_star,
        reproduction_abs_diff=abs(T_star - float(res['star_peak_snr'])),
        ring_max_published=float(res['control_peak_snr']), ring_max_paper=ring_pub,
        stage1_n_control=int(cm.size), stage1_p=p_stage1, stage1_floor=floor1,
        z_lag1_autocorr=lag1, z_std=zstd, z_kurtosis=zkurt,
        T_controls_8_real=[float(v) for v in T_ctrl8],
        null_draws=B,
        null_median=float(q[0]), null_p90=float(q[1]), null_p99=float(q[2]),
        null_p999=float(q[3]), null_p9999=float(q[4]), null_max=float(q[5]),
        null_mean=float(null.mean()), null_std=float(null.std()),
        n_null_ge_Tstar=n_ge,
        p_local_empirical=p_emp,
        p_local_is_upper_bound=bool(n_ge == 0),
        p_local_rule_of_three_95UCL=p_rule3,
        gev=gev_tail(null, T_star, n_cells=int(nch) * int(shifts.shape[0])),
        null_self_validation=nullval,
        control_discrimination=ctrl_diag,
        subband_null_M=32, subband_n=len(sub),
        subband_median=float(np.median(sub)), subband_max=float(np.max(sub)),
        subband_n_ge_Tstar=int(np.sum(np.asarray(sub) >= T_star)),
        bonferroni_scale=1.2e-4,
        runtime_s=round(time.time() - t0, 1),
    )
    np.save(f'{OUTDIR}/null_{tdir}_{stem}.npy', null.astype(np.float32))
    json.dump(rec, open(f'{OUTDIR}/res_{idx}.json', 'w'), indent=1)
    print(json.dumps(rec, indent=1), flush=True)
    return rec


if __name__ == '__main__':
    idx      = int(sys.argv[1])
    ndraw    = int(sys.argv[2])
    nworkers = int(sys.argv[3]) if len(sys.argv) > 3 else 24
    chunk    = int(sys.argv[4]) if len(sys.argv) > 4 else 64
    run_window(idx, ndraw, nworkers, chunk)
