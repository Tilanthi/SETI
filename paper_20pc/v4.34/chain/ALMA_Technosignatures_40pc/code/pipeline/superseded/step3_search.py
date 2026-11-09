#!/usr/bin/env python3
"""
Step 3 of the ALMA-SETI / TRAPPIST-1 pipeline: the technosignature search.

For each execution block:
  1. Remove a running-median spectral baseline from every (integration,
     position) spectrum.  This is the image-plane equivalent of the
     reference paper's CASA `uvsub` continuum subtraction, and additionally
     flattens any residual bandpass structure.
  2. Estimate the r.m.s. of every channel map empirically from the
     off-source probe positions (the analogue of CASA `imstat`), and
     independently from the visibility weights as a cross-check.
  3. Run a Doppler de-drift search: for each trial drift rate the spectrum
     of every integration is shifted by the appropriate number of channels
     and the integrations are combined with inverse-variance weights.

     This EXTENDS the reference paper, which mitigated drift only by
     chopping the data into short blocks and never recovered the lost
     sensitivity.  De-drifting restores the full coherent sensitivity of
     the whole execution block.

  4. Threshold at SNR > 5 (as the reference paper) and convert the
     non-detection into an EIRP limit,  EIRP_min = 4 pi d^2 S_min dnu.

The identical search is run on the control positions to measure the
empirical false-alarm distribution, rather than assuming Gaussianity.

Usage: step3_search.py <EBID> [nproc]
"""
import os, sys, json, time
for _v in ('OMP_NUM_THREADS','OPENBLAS_NUM_THREADS','MKL_NUM_THREADS',
           'NUMEXPR_NUM_THREADS','VECLIB_MAXIMUM_THREADS'):
    os.environ[_v] = '1'
import numpy as np

EB    = sys.argv[1]
NPROC = int(sys.argv[2]) if len(sys.argv) > 2 else 64
ROOT  = '/data/SETI'
_IN_SFX  = os.environ.get('SETI_IN_SFX', os.environ.get('SETI_SFX', ''))
_OUT_SFX = os.environ.get('SETI_SFX', '')
NPZ   = f'{ROOT}/products/{EB}{_IN_SFX}_waterfall.npz'
OUT   = f'{ROOT}/products/{EB}{_OUT_SFX}_search.npz'
JSN   = f'{ROOT}/products/{EB}{_OUT_SFX}_result.json'

SNR_THRESH   = 5.0
MEDWIN       = 65          # channels, running-median baseline window
EDGE_FRAC    = 0.04        # drop this fraction at each spw edge
PC_M         = 3.0856775814913673e16
# DRIFT_MAX default 6000 Hz/s covers all seven TRAPPIST-1 planets' own
# orbital acceleration (max 4621 Hz/s, planet b) at 346.5 GHz. The widened
# "deep" search (SETI_DRIFT_MAX=12000, see run_widened_search.sh) covers, in
# addition, a worst-case low-orbit artificial satellite around planet b
# (+2317 Hz/s) stacked on planet b's own orbital motion (combined 6938 Hz/s),
# with ~1.7x headroom on top of that combined worst case.
DRIFT_MAX    = float(os.environ.get('SETI_DRIFT_MAX', 6000.0))
DRIFT_STEP_DIV = float(os.environ.get('SETI_DRIFT_STEP_DIV', 2.0))  # trials
                           # per channel-crossing-over-full-span; default 2
                           # = half-channel steps, "deep" mode uses 4 = quarter


_S = {}


def one_drift(k):
    """Inverse-variance-weighted, de-drifted stack for drift trial k."""
    X = _S['X']; invvar = _S['invvar']; shifts = _S['shifts']
    npos = _S['npos']; nch = _S['nch']; nint = _S['nint']
    num = np.zeros((npos, nch), dtype=np.float64)
    den = np.zeros(nch, dtype=np.float64)
    for t in range(nint):
        s = int(shifts[k, t])
        if s == 0:
            num += X[t]; den += invvar[t]
        elif s > 0:
            if s >= nch:
                continue
            num[:, :nch - s] += X[t][:, s:]
            den[:nch - s] += invvar[t][s:]
        else:
            s = -s
            if s >= nch:
                continue
            num[:, s:] += X[t][:, :nch - s]
            den[s:] += invvar[t][:nch - s]
    with np.errstate(invalid='ignore', divide='ignore'):
        snr = num / np.sqrt(den)[None, :]
    return np.nan_to_num(snr).astype(np.float32)


def spectral_baseline(a, win):
    """
    Smooth spectral baseline along the last axis.

    A true running median over ~1e9 samples with a 65-channel window is
    prohibitively slow, so we take the median in contiguous blocks of `win`
    channels and linearly interpolate between block centres.  For removing
    continuum plus residual bandpass curvature this is equivalent, and it is
    ~100x faster because the interpolation collapses to a single BLAS call.
    Narrowband (1-3 channel) signals are unaffected either way: they cannot
    shift a median taken over `win` channels.
    """
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


def main():
    t0 = time.time()
    z = np.load(NPZ, allow_pickle=True)
    I = z['I']                       # (nint, npos, nch)
    W = z['W']                       # (nint, nch)  sum of weights
    times = z['times']; freqs = z['freqs']; chanw = float(z['chanw'])
    names = list(z['names']); n_src = int(z['n_src'])
    nint, npos, nch = I.shape
    print(f'[{EB}] waterfall {I.shape}, {chanw/1e3:.2f} kHz channels', flush=True)

    # ------------------------------------------------ 1. baseline removal
    # First trim a fixed minimum edge fraction, THEN adaptively extend the
    # trim on either side until reaching a channel with >50% weighted
    # integrations. ALMA correlators commonly flag a band of edge channels
    # entirely (observed here: exactly the outer 8/128 channels on each
    # side, 12.5% total -- wider than the fixed 4% EDGE_FRAC default tuned
    # on the Band-7 FDM data). A fixed fraction is a guess; detecting the
    # true dead band from the data themselves is robust across bands/setups.
    e0 = int(EDGE_FRAC * nch)
    chan_ok = (W > 0).mean(axis=0) > 0.5
    lo = e0
    while lo < nch // 2 and not chan_ok[lo]:
        lo += 1
    hi = nch - e0
    while hi > nch // 2 and not chan_ok[hi - 1]:
        hi -= 1
    if hi - lo != nch - 2 * e0:
        print(f'[{EB}] adaptive edge trim extended to [{lo}:{hi}] '
              f'(fixed guess was [{e0}:{nch-e0}])', flush=True)
    sl = slice(lo, hi)
    I = I[:, :, sl].astype(np.float32)
    W = W[:, sl].astype(np.float32)
    freqs = freqs[sl]
    nch = I.shape[2]

    # Integrations are kept/dropped based only on the SOURCE positions
    # (0:n_src) and the weights -- those are what we are actually trying to
    # measure. A handful of CONTROL probe positions can carry zero total
    # weight (and hence NaN, from the 0/0 DFT normalisation) at some times
    # without that being a real problem, e.g. in smaller/more compact array
    # configurations where a probe near the annulus edge occasionally has
    # no valid baselines; requiring EVERY one of the ~600 probe positions to
    # be finite at every integration is needlessly strict and (as found on
    # the Band-3 dataset) can wipe out 100% of integrations even though the
    # actual source measurement is fine. Chronically-bad probe COLUMNS are
    # dropped separately below instead.
    good = np.isfinite(I[:, :n_src, :]).all(axis=(1, 2)) & (W > 0).all(axis=1)
    I = I[good]; W = W[good]; times = times[good]
    nint = I.shape[0]
    if nint == 0:
        raise RuntimeError('0 usable integrations after quality cuts -- '
                            'check source-position data for this EB')

    # Drop any probe position that is non-finite more than 10% of the time;
    # keep the rest even if they have occasional NaNs (handled with
    # nan-aware statistics below).
    probe_all = np.arange(n_src, npos)
    bad_rate = 1.0 - np.isfinite(I[:, probe_all, :]).all(axis=2).mean(axis=0)
    probe = probe_all[bad_rate < 0.10]
    ndropped = len(probe_all) - len(probe)
    if ndropped:
        print(f'[{EB}] dropped {ndropped}/{len(probe_all)} chronically-bad '
              f'control probe positions', flush=True)
    print(f'[{EB}] {nint} usable integrations, {nch} channels after edge trim, '
          f'{len(probe)} usable control probes', flush=True)

    I -= spectral_baseline(np.nan_to_num(I), MEDWIN)

    # ------------------------------------------------ 2. noise per channel map
    med = np.nanmedian(I[:, probe, :], axis=1)
    mad = np.nanmedian(np.abs(I[:, probe, :] - med[:, None, :]), axis=1)
    sigma = (1.4826 * mad).astype(np.float32)          # (nint, nch) empirical
    sigma[sigma <= 0] = np.nan
    sigma_theory = 1.0 / np.sqrt(W)                    # from visibility weights
    print(f'[{EB}] median empirical rms  = {np.nanmedian(sigma)*1e3:.3f} mJy/beam '
          f'per {chanw/1e3:.1f} kHz channel per integration', flush=True)
    print(f'[{EB}] median theoretical rms= {np.nanmedian(sigma_theory)*1e3:.3f} mJy/beam',
          flush=True)

    # ------------------------------------------------ 3. de-drift search
    dt = (times - times[0]).astype(np.float64)         # seconds
    span = dt.max() - dt.min()
    ddrift = chanw / max(span, 1.0) / DRIFT_STEP_DIV
    drifts = np.arange(-DRIFT_MAX, DRIFT_MAX + ddrift, ddrift)
    print(f'[{EB}] time span {span:.0f} s -> {len(drifts)} drift trials at '
          f'{ddrift:.1f} Hz/s spacing', flush=True)

    invvar = (1.0 / sigma**2)
    invvar[~np.isfinite(invvar)] = 0.0
    X = np.nan_to_num(I) * invvar[:, None, :]          # (nint, npos, nch)

    shifts = np.rint(np.outer(drifts, dt) / chanw).astype(np.int32)  # (nd,nint)

    # published into module globals so forked workers inherit them cheaply
    _S.update(X=X, invvar=invvar, shifts=shifts,
              npos=npos, nch=nch, nint=nint)

    import multiprocessing as mp
    best_src = np.full((n_src, nch), -np.inf, dtype=np.float32)
    best_drift = np.zeros((n_src, nch), dtype=np.float32)
    ctrl_max = []
    with mp.get_context('fork').Pool(min(NPROC, len(drifts))) as pool:
        for k, snr in enumerate(pool.imap(one_drift, range(len(drifts)),
                                          chunksize=1)):
            s = snr[:n_src]
            upd = s > best_src
            best_src = np.where(upd, s, best_src)
            best_drift = np.where(upd, np.float32(drifts[k]), best_drift)
            ctrl_max.append(snr[probe].max(axis=1))    # per usable control position
            if k % 25 == 0:
                print(f'[{EB}]   drift {k+1}/{len(drifts)} '
                      f'({time.time()-t0:.0f} s)', flush=True)
    ctrl_max = np.max(np.array(ctrl_max), axis=0)       # (nprobe,)

    # ------------------------------------------------ 4. results & EIRP
    star = best_src[0]
    hit = np.flatnonzero(star > SNR_THRESH)
    src_peak = float(best_src.max())
    ctrl_peak = float(ctrl_max.max())

    # sensitivity of the fully de-drifted, EB-combined channel map
    sig_comb = float(np.nanmedian(1.0 / np.sqrt(np.nansum(invvar, axis=0))))
    S_min = SNR_THRESH * sig_comb                       # Jy
    plx = float(z['parallax']); plx_e = float(z['parallax_err'])
    d_pc = 1000.0 / plx
    d_m = d_pc * PC_M
    eirp = 4 * np.pi * d_m**2 * (S_min * 1e-26) * chanw

    res = dict(
        eb=EB, n_int=int(nint), n_chan=int(nch), chanwidth_Hz=chanw,
        freq_lo_GHz=float(freqs[0] / 1e9), freq_hi_GHz=float(freqs[-1] / 1e9),
        bandwidth_Hz=float(nch * chanw),
        time_span_s=float(span), on_source_s=float(nint * np.median(np.diff(times))),
        n_drift_trials=int(len(drifts)), drift_step_Hz_s=float(ddrift),
        drift_max_Hz_s=float(DRIFT_MAX),
        rms_per_int_mJy=float(np.nanmedian(sigma) * 1e3),
        rms_theory_per_int_mJy=float(np.nanmedian(sigma_theory) * 1e3),
        rms_combined_mJy=float(sig_comb * 1e3),
        S_min_Jy=float(S_min),
        distance_pc=d_pc, distance_pc_err=d_pc * plx_e / plx,
        EIRP_min_W=float(eirp),
        snr_threshold=SNR_THRESH,
        star_peak_snr=float(star.max()),
        star_peak_chan=int(np.argmax(star)),
        star_peak_freq_GHz=float(freqs[np.argmax(star)] / 1e9),
        star_peak_drift_Hz_s=float(best_drift[0][np.argmax(star)]),
        n_hits_above_threshold=int(hit.size),
        hit_freqs_GHz=[float(freqs[i] / 1e9) for i in hit[:50]],
        src_region_peak_snr=src_peak,
        control_peak_snr=ctrl_peak,
        n_control=int(len(probe)),
        n_control_dropped=int(ndropped),
        detection=bool(star.max() > SNR_THRESH),
        runtime_s=round(time.time() - t0, 1),
    )
    json.dump(res, open(JSN, 'w'), indent=1)
    np.savez_compressed(OUT, best_src=best_src, best_drift=best_drift,
                        ctrl_max=ctrl_max, freqs=freqs, sigma=sigma,
                        names=np.array(names[:n_src]))
    print(json.dumps(res, indent=1), flush=True)
    print(f'[{EB}] STEP3 COMPLETE in {time.time()-t0:.0f} s', flush=True)


if __name__ == '__main__':
    main()
