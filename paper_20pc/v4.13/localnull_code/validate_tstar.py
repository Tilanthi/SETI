#!/usr/bin/env python3
"""Faithful reimplementation of the seti_drift_search_generic.py statistic
T_star, from the RETAINED products only (srcspec.npz + search.npz), for the
four flagged windows.  Validation step: must reproduce the published
star_peak_snr (and, more stringently, the per-channel best_src[0] curve)
before any null is built on it.

Reads nothing but products; writes only into the scratch dir.
"""
import os, sys, json, time
for _v in ('OMP_NUM_THREADS','OPENBLAS_NUM_THREADS','MKL_NUM_THREADS',
           'NUMEXPR_NUM_THREADS','VECLIB_MAXIMUM_THREADS'):
    os.environ.setdefault(_v, '4')
import numpy as np

MEDWIN    = 65
EDGE_FRAC = 0.04
DRIFT_STEP_DIV = 2.0
DRIFT_COEFF_HZ_PER_GHZ = 12.0

WINDOWS = [
    # target dir, eb+spw stem, paper Table-7 centre freq GHz, paper T_star, paper ring max
    ('CP-72_2713_B7', 'A002_Xff0235_X4a6d_spw3',  345.1152,  5.81,  5.68),
    ('HD_48370_B6',   'A002_Xc26103_X155a_spw16', 230.7305, 27.10, 26.83),
    ('bet_Pic_B3',    'A002_Xf5d76d_X32f1_spw3',  115.2605, 14.65,  7.27),
    ('bet_Pic_B6',    'A002_Xd9668b_X3a90_spw5',  230.5164, 11.68,  9.12),
]
BASE = '/data/SETI/targets'


def spectral_baseline(a, win):
    """Verbatim port of the pipeline's block-median + linear-interp baseline."""
    lead = a.shape[:-1]; n = a.shape[-1]
    nb = max(2, n // win)
    edges = np.linspace(0, n, nb + 1).astype(int)
    cen = 0.5 * (edges[:-1] + edges[1:])
    flat = a.reshape(-1, n)
    med = np.empty((flat.shape[0], nb), dtype=np.float32)
    for k in range(nb):
        med[:, k] = np.median(flat[:, edges[k]:edges[k + 1]], axis=1)
    x = np.arange(n, dtype=np.float64)
    M = np.zeros((nb, n), dtype=np.float32)
    idx = np.clip(np.searchsorted(cen, x) - 1, 0, nb - 2)
    t = np.clip((x - cen[idx]) / (cen[idx + 1] - cen[idx]), 0.0, 1.0)
    M[idx, np.arange(n)] = (1.0 - t).astype(np.float32)
    M[idx + 1, np.arange(n)] += t.astype(np.float32)
    return (med @ M).reshape(*lead, n)


def prepare(tdir, stem, verbose=True):
    """Return everything needed to run the search for this window, using the
    pipeline's own preprocessing decisions."""
    p = f'{BASE}/{tdir}/products/{stem}'
    res = json.load(open(p + '_result.json'))
    zs  = np.load(p + '_srcspec.npz', allow_pickle=True)
    zr  = np.load(p + '_search.npz',  allow_pickle=True)

    I_star = np.asarray(zs['I_star'])                # (nint, nch_full)
    I_ctrl = np.asarray(zs['I_control_sample'])      # (nint, 8, nch_full)
    W      = np.asarray(zs['W'])                     # (nint, nch_full)
    times  = np.asarray(zs['times'])
    freqs  = np.asarray(zs['freqs'])
    chanw  = float(zs['chanw'])
    sigma_saved = np.asarray(zr['sigma'])            # (nint_kept, nch_trim) ALL-probe MAD
    best_src    = np.asarray(zr['best_src'])         # (135, nch_trim)
    ctrl_max    = np.asarray(zr['ctrl_max'])         # (512,)

    nint, nch = I_star.shape

    # --- edge trim, exactly as the pipeline ---
    e0 = int(EDGE_FRAC * nch)
    chan_ok = (W > 0).mean(axis=0) > 0.5
    lo = e0
    while lo < nch // 2 and not chan_ok[lo]:
        lo += 1
    hi = nch - e0
    while hi > nch // 2 and not chan_ok[hi - 1]:
        hi -= 1
    sl = slice(lo, hi)
    I_star = I_star[:, sl].astype(np.float32)
    I_ctrl = I_ctrl[:, :, sl].astype(np.float32)
    W      = W[:, sl].astype(np.float32)
    freqs  = freqs[sl]
    nch    = I_star.shape[1]

    # --- integration quality cut.  The pipeline's mask uses ALL n_src source
    # positions; we only retain the star (position 0).  We therefore derive
    # the kept-integration count from the saved sigma's first axis and check
    # consistency.
    good = np.isfinite(I_star).all(axis=1) & (W > 0).all(axis=1)
    if good.sum() != sigma_saved.shape[0]:
        # fall back: trust the pipeline's own count; only accept if the
        # star-only mask is a superset we can match by dropping the same number
        pass
    I_star = I_star[good]; I_ctrl = I_ctrl[good]; W = W[good]; t_keep = times[good]
    nint = I_star.shape[0]

    ok_shape = (sigma_saved.shape == (nint, nch))

    # --- baseline removal ---
    I_star = I_star - spectral_baseline(np.nan_to_num(I_star), MEDWIN)
    I_ctrl = I_ctrl - spectral_baseline(np.nan_to_num(I_ctrl), MEDWIN)

    # --- noise: use the pipeline's own saved all-probe sigma map ---
    sigma = sigma_saved.astype(np.float32).copy()
    sigma[sigma <= 0] = np.nan

    # --- drift grid, exactly as the pipeline ---
    drift_max = float(os.environ.get('SETI_DRIFT_MAX_OVERRIDE',
                      DRIFT_COEFF_HZ_PER_GHZ * (float(np.median(freqs)) / 1e9)))
    dt = (t_keep - t_keep[0]).astype(np.float64)
    span = dt.max() - dt.min()
    ddrift = chanw / max(span, 1.0) / DRIFT_STEP_DIV
    drifts = np.arange(-drift_max, drift_max + ddrift, ddrift)
    freq_sign = 1.0 if freqs[-1] >= freqs[0] else -1.0
    shifts = np.rint(freq_sign * np.outer(drifts, dt) / chanw).astype(np.int32)

    invvar = (1.0 / sigma ** 2)
    invvar[~np.isfinite(invvar)] = 0.0

    if verbose:
        print(f'[{tdir}/{stem}] trim [{lo}:{hi}] nch={nch} nint={nint} '
              f'(json n_int={res["n_int"]} n_chan={res["n_chan"]}) '
              f'sigma_shape_ok={ok_shape} ndrift={len(drifts)} '
              f'(json {res["n_drift_trials"]}) ddrift={ddrift:.4f} '
              f'(json {res["drift_step_Hz_s"]:.4f}) freq_sign={freq_sign:+.0f}',
              flush=True)
    return dict(res=res, I_star=I_star, I_ctrl=I_ctrl, invvar=invvar, sigma=sigma,
                shifts=shifts, drifts=drifts, freqs=freqs, chanw=chanw,
                nint=nint, nch=nch, best_src=best_src, ctrl_max=ctrl_max,
                lo=lo, hi=hi, ok_shape=ok_shape, dt=dt, tdir=tdir, stem=stem)


def drift_search(I, invvar, shifts, chunk_positions=None):
    """I: (nint, npos, nch) residuals.  Returns best-over-drift SNR (npos, nch)
    and the argmax drift index, reproducing one_drift()'s arithmetic."""
    nint, npos, nch = I.shape
    X = np.nan_to_num(I) * invvar[:, None, :]
    best = np.full((npos, nch), -np.inf, dtype=np.float32)
    bestk = np.zeros((npos, nch), dtype=np.int32)
    for k in range(shifts.shape[0]):
        num = np.zeros((npos, nch), dtype=np.float64)
        den = np.zeros(nch, dtype=np.float64)
        for t in range(nint):
            s = int(shifts[k, t])
            if s == 0:
                num += X[t]; den += invvar[t]
            elif s > 0:
                if s >= nch: continue
                num[:, :nch - s] += X[t][:, s:]
                den[:nch - s]    += invvar[t][s:]
            else:
                s = -s
                if s >= nch: continue
                num[:, s:] += X[t][:, :nch - s]
                den[s:]    += invvar[t][:nch - s]
        with np.errstate(invalid='ignore', divide='ignore'):
            snr = np.nan_to_num(num / np.sqrt(den)[None, :]).astype(np.float32)
        upd = snr > best
        best = np.where(upd, snr, best)
        bestk = np.where(upd, np.int32(k), bestk)
    return best, bestk


if __name__ == '__main__':
    out = []
    for tdir, stem, fc, T_pub, ring_pub in WINDOWS:
        t0 = time.time()
        d = prepare(tdir, stem)
        res = d['res']
        I = np.concatenate([d['I_star'][:, None, :], d['I_ctrl']], axis=1)
        best, bestk = drift_search(I, d['invvar'], d['shifts'])
        T_star_mine = float(best[0].max())
        pk = int(np.argmax(best[0]))
        ref = d['best_src'][0]
        # channel-wise comparison against the pipeline's own saved curve
        dev = np.abs(best[0] - ref)
        rec = dict(target=tdir, stem=stem, centre_GHz_paper=fc,
                   centre_GHz_data=0.5 * (res['freq_lo_GHz'] + res['freq_hi_GHz']),
                   T_star_published=res['star_peak_snr'], T_star_paper=T_pub,
                   T_star_reproduced=T_star_mine,
                   abs_diff=abs(T_star_mine - res['star_peak_snr']),
                   rel_diff=abs(T_star_mine - res['star_peak_snr']) / res['star_peak_snr'],
                   peak_chan_mine=pk, peak_chan_published=res['star_peak_chan'],
                   chanwise_max_abs_dev=float(dev.max()),
                   chanwise_median_abs_dev=float(np.median(dev)),
                   chanwise_corr=float(np.corrcoef(best[0], ref)[0, 1]),
                   n_int=d['nint'], n_chan=d['nch'], n_drift=int(d['shifts'].shape[0]),
                   sigma_shape_ok=d['ok_shape'],
                   T_controls_8=[float(v) for v in best[1:].max(axis=1)],
                   ctrl_max_512_max=float(d['ctrl_max'].max()),
                   ctrl_max_512_median=float(np.median(d['ctrl_max'])),
                   runtime_s=round(time.time() - t0, 1))
        print(json.dumps(rec, indent=1), flush=True)
        out.append(rec)
    json.dump(out, open('/data/SETI/work/localnull_v342/validation.json', 'w'), indent=1)
    print('WROTE validation.json', flush=True)
