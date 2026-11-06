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
import os, shutil, sys, json, time
for _v in ('OMP_NUM_THREADS','OPENBLAS_NUM_THREADS','MKL_NUM_THREADS',
           'NUMEXPR_NUM_THREADS','VECLIB_MAXIMUM_THREADS'):
    os.environ[_v] = '1'
import numpy as np

EB    = sys.argv[1]
NPROC = int(sys.argv[2]) if len(sys.argv) > 2 else 8
TARGET_DIR = os.environ['SETI_TARGET_DIR']
_IN_SFX  = os.environ.get('SETI_IN_SFX', os.environ.get('SETI_SFX', ''))
_OUT_SFX = os.environ.get('SETI_SFX', '')
NPZ   = f'{TARGET_DIR}/products/{EB}{_IN_SFX}_waterfall.npz'
OUT   = f'{TARGET_DIR}/products/{EB}{_OUT_SFX}_search.npz'
JSN   = f'{TARGET_DIR}/products/{EB}{_OUT_SFX}_result.json'

SNR_THRESH   = 5.0
MEDWIN       = 65          # channels, running-median baseline window
EDGE_FRAC    = 0.04        # drop this fraction at each spw edge
PC_M         = 3.0856775814913673e16
# Generic drift-rate bound: the reference paper's own fiducial assumption
# (+/-4 Hz/s at 1 GHz, scaled linearly with observing frequency -- Eq. 7 of
# Mason et al. 2024) times a x3 safety margin = 12.0 Hz/s per GHz.
#
# Updated 2026-08-30 (volume-limited 20pc survey, per Glenn's instruction to
# account for "possible orbital motions if any technosignatures come from
# planets orbiting the star"): this generalises the earlier TRAPPIST-1-only
# hardcoded override into a per-star mechanism driven by real NASA Exoplanet
# Archive data. seti_search_driver.py looks up each target's confirmed
# planets, computes the innermost (shortest-period) planet's own maximum
# line-of-sight orbital acceleration -> drift rate (Hz/s per GHz), and sets
# SETI_DRIFT_COEFF to whichever is larger: that planet-based value or this
# 12.0 Hz/s/GHz generic default. For targets with no confirmed planets (the
# large majority) or where the known planets' accelerations don't exceed
# the generic bound, SETI_DRIFT_COEFF is left at this same 12.0 default --
# identical behaviour to the original 100-star survey. Only TRAPPIST-1
# itself (planet b, P=1.51d) is actually widened by this mechanism (13.34
# vs 12.0 Hz/s/GHz); see /data/SETI/targets/drift_coeffs.json for the full
# per-star calculation across all checked confirmed-planet hosts.
DRIFT_COEFF_HZ_PER_GHZ = float(os.environ.get('SETI_DRIFT_COEFF', 12.0))
def _default_drift_max_hz_s(freq_hz):
    return DRIFT_COEFF_HZ_PER_GHZ * (freq_hz / 1e9)
# DRIFT_MAX: if SETI_DRIFT_MAX is set explicitly, use it; otherwise computed
# below (in main(), once the data's centre frequency is known) from
# _default_drift_max_hz_s(). None here is a sentinel for "compute from data".
DRIFT_MAX    = float(os.environ['SETI_DRIFT_MAX']) if os.environ.get('SETI_DRIFT_MAX') else None
DRIFT_STEP_DIV = float(os.environ.get('SETI_DRIFT_STEP_DIV', 2.0))  # trials
                           # per channel-crossing-over-full-span; default 2
                           # = half-channel steps, "deep" mode uses 4 = quarter

# Known mm/submm molecular rest frequencies (added 2026-08-30, per Glenn's
# instruction to state explicitly what is done about spectral-line
# contamination of the narrowband search). Previously this cross-check was
# done only once, by hand, for the single hit the pipeline has produced to
# date (beta Pictoris CO(1-0), see the paper's Results section) -- it is
# now automated here for every future candidate, using the same rest-
# frequency table already used by continuum_map_generic.py's line-exclusion
# step, so the check is applied uniformly and is no longer dependent on a
# human remembering to do it. A hit is flagged 'likely_line_contamination'
# if (a) its recovered frequency lies within one channel width of a known
# transition's rest frequency, when Doppler-shifted by the star's own
# system velocity (or, if unknown, checked at zero radial velocity too),
# AND (b) its best-fit drift rate is consistent with zero (|drift| less
# than one drift-search step), since a genuine spectral line is stationary
# in frequency over the observation whereas the search is explicitly
# looking for *drifting* signals.
KNOWN_LINES_GHZ = {
    'CO(1-0)': 115.271, 'CO(2-1)': 230.538, 'CO(3-2)': 345.796,
    'CO(4-3)': 461.041, 'CO(6-5)': 691.473, '13CO(2-1)': 220.399,
    'C18O(2-1)': 219.560, 'HCN(1-0)': 88.632, 'HCN(3-2)': 265.886,
    'HCO+(1-0)': 89.189, 'HCO+(3-2)': 267.558, 'CS(5-4)': 244.936,
    'CN(1-0)': 113.491, 'SiO(5-4)': 217.105, 'H2CO': 218.222,
}


def check_known_line(freq_ghz, drift_hz_s, chanw_hz, drift_step_hz_s, rv_kms=0.0):
    """Return (line_name, offset_MHz, is_likely_line) for the nearest known
    molecular rest frequency to freq_ghz (optionally Doppler-shifted by the
    star's own radial velocity rv_kms, positive = receding), and whether the
    candidate is close enough in frequency AND consistent with zero drift
    to be flagged as probable line contamination rather than a
    technosignature candidate."""
    shifted = {name: f0 * (1.0 - rv_kms / 299792.458) for name, f0 in KNOWN_LINES_GHZ.items()}
    name, f0 = min(shifted.items(), key=lambda kv: abs(kv[1] - freq_ghz))
    offset_mhz = (freq_ghz - f0) * 1e3
    tol_mhz = max(chanw_hz / 1e6, 1e-3)
    is_line = bool(abs(offset_mhz) < tol_mhz and abs(drift_hz_s) < max(drift_step_hz_s, 1e-9))
    return name, float(offset_mhz), is_line


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


def closure_phase_vetting(ms_path, peak_freq_hz, drift_hz_s,
                           t_ref, n_triangles=50, seed=20260830):
    """Added 2026-08-30, per Glenn's instruction: a model-independent
    RFI/near-field discriminant that is uniquely available to interferometric
    data and impossible for any single-dish SETI survey (Breakthrough Listen,
    FAST, ATA, LOFAR, etc. all lack it). The closure phase -- the phase sum
    arg(V_ij) + arg(V_jk) - arg(V_ik) around any closed triangle of baselines
    i-j-k -- is a standard interferometric identity that is THEORETICALLY
    EXACTLY ZERO for any unresolved point source at ANY sky position
    (a point source's visibility phase is a pure linear/planar function of
    (u,v), which cancels exactly around any closed baseline loop), and is
    immune to per-station calibration errors by construction. A genuinely
    non-zero closure phase at the candidate's own drifting frequency track
    is therefore evidence AGAINST the signal behaving like a real celestial
    point source (consistent instead with near-field/terrestrial
    interference or an instrumental artefact) -- this cannot be faked by
    ordinary calibration problems, which cancel out of closure phase.
    Validated against a synthetic (non-ALMA) point-source/non-point-source
    test before ever being pointed at real data -- see
    test_closure_phase.py in the repo alongside this file.
    NOTE: closure phase is, by construction, independent of the point
    source's actual sky position -- this test complements, but does not
    replace, the existing src_peak > ctrl_peak spatial-coincidence test
    (which does check position); this one instead asks "does this behave
    like ANY coherent point source at all", a question the spatial test
    alone cannot answer.
    Only ever called on an ACTUAL threshold-crossing candidate (rare), so
    the extra CASA table read this requires costs essentially nothing in
    the overwhelming common case of no candidate. Returns a dict summary,
    or a dict with an 'error' key if anything about this best-effort
    diagnostic fails -- this must never abort the main search."""
    try:
        from casatools import table
        tb = table()
        tb.open(ms_path)
        ant1 = tb.getcol('ANTENNA1')
        ant2 = tb.getcol('ANTENNA2')
        time_col = tb.getcol('TIME')
        data = tb.getcol('DATA')          # (npol, nchan, nrow)
        flag = tb.getcol('FLAG')          # (npol, nchan, nrow)
        tb.close()
        tb.open(ms_path + '/SPECTRAL_WINDOW')
        chan_freq = tb.getcol('CHAN_FREQ', startrow=0, nrow=1)[:, 0]
        tb.close()

        auto = (ant1 == ant2)
        ant1 = ant1[~auto]; ant2 = ant2[~auto]; time_col = time_col[~auto]
        data = data[:, :, ~auto]; flag = flag[:, :, ~auto]

        # Per row, the drifting candidate's instantaneous frequency, and the
        # nearest channel index in this MS's own (untrimmed) channel grid.
        dt = time_col - t_ref
        inst_freq = peak_freq_hz + drift_hz_s * dt
        chan_idx = np.array([int(np.argmin(np.abs(chan_freq - f))) for f in inst_freq])

        good = np.zeros(len(ant1), dtype=bool)
        vis_val = np.zeros(len(ant1), dtype=np.complex128)
        for r in range(len(ant1)):
            ci = chan_idx[r]
            pol_ok = ~flag[:, ci, r]
            if not pol_ok.any():
                continue
            vis_val[r] = np.mean(data[pol_ok, ci, r])
            good[r] = True
        ant1, ant2, vis_val = ant1[good], ant2[good], vis_val[good]

        # Coherently average (NOT just power-average) repeated visits to the
        # same baseline across the on-source time window, at each row's own
        # (already drift-tracked) channel -- this is what recovers SNR for a
        # real, coherent point-source signal the same way the main search's
        # de-drift stacking does.
        baseline_sum = {}
        for a, b, v in zip(ant1, ant2, vis_val):
            key = (int(a), int(b)) if a < b else (int(b), int(a))
            conj = 1.0 if a < b else -1.0
            vv = v if a < b else np.conj(v)
            if key not in baseline_sum:
                baseline_sum[key] = []
            baseline_sum[key].append(vv)
        baseline_vis = {k: np.mean(v) for k, v in baseline_sum.items() if len(v) > 0}

        ants = sorted(set(a for a, b in baseline_vis) | set(b for a, b in baseline_vis))
        rng = np.random.default_rng(seed)
        phases = []
        tried = set()
        attempts = 0
        while len(phases) < n_triangles and attempts < n_triangles * 40 and len(ants) >= 3:
            attempts += 1
            i, j, k = rng.choice(ants, 3, replace=False)
            i, j, k = sorted([int(i), int(j), int(k)])
            if (i, j, k) in tried:
                continue
            tried.add((i, j, k))
            try:
                v_ij = baseline_vis[(i, j)] if (i, j) in baseline_vis else np.conj(baseline_vis[(j, i)])
                v_jk = baseline_vis[(j, k)] if (j, k) in baseline_vis else np.conj(baseline_vis[(k, j)])
                v_ik = baseline_vis[(i, k)] if (i, k) in baseline_vis else np.conj(baseline_vis[(k, i)])
            except KeyError:
                continue
            phases.append(np.angle(v_ij * v_jk * np.conj(v_ik)))
        if len(phases) < 5:
            return dict(error=f'only {len(phases)} usable closure triangles, too few to test')
        phases = np.array(phases)
        mean_deg = float(np.degrees(np.mean(phases)))
        std_deg = float(np.degrees(np.std(phases)))
        sem_deg = std_deg / np.sqrt(len(phases))
        z = abs(mean_deg) / sem_deg if sem_deg > 0 else None
        return dict(n_triangles=len(phases), mean_closure_phase_deg=mean_deg,
                    std_closure_phase_deg=std_deg, z_score=z,
                    consistent_with_point_source=bool(z is not None and z < 5.0))
    except Exception as e:
        return dict(error=f'{type(e).__name__}: {e}')


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
    global DRIFT_MAX
    if DRIFT_MAX is None:
        DRIFT_MAX = _default_drift_max_hz_s(float(np.median(freqs)))
        print(f'[{EB}] drift max not overridden -- using frequency-scaled '
              f'default {DRIFT_MAX:.1f} Hz/s at {np.median(freqs)/1e9:.2f} GHz',
              flush=True)
    dt = (times - times[0]).astype(np.float64)         # seconds
    span = dt.max() - dt.min()
    ddrift = chanw / max(span, 1.0) / DRIFT_STEP_DIV
    drifts = np.arange(-DRIFT_MAX, DRIFT_MAX + ddrift, ddrift)
    print(f'[{EB}] time span {span:.0f} s -> {len(drifts)} drift trials at '
          f'{ddrift:.1f} Hz/s spacing', flush=True)

    invvar = (1.0 / sigma**2)
    invvar[~np.isfinite(invvar)] = 0.0
    X = np.nan_to_num(I) * invvar[:, None, :]          # (nint, npos, nch)

    # 'chanw' (from the extraction step) is an unsigned magnitude, but ALMA
    # spectral windows are frequently delivered with CHAN_FREQ *decreasing*
    # with increasing channel index (a standard USB/LSB tuning artifact,
    # confirmed present in some of this survey's data via injection-
    # recovery testing). A physically positive drift rate (frequency
    # increasing with time) must map to a *decreasing* channel index in
    # that case -- without this correction, every reported drift_Hz_s for
    # a descending-frequency spw comes out with the wrong sign (detection
    # SIGNIFICANCE/SNR and recovered frequency are unaffected, since the
    # +/-DRIFT_MAX trial grid is symmetric and still finds the right
    # |shift|; only the physical sign label was wrong).
    freq_sign = 1.0 if freqs[-1] >= freqs[0] else -1.0
    shifts = np.rint(freq_sign * np.outer(drifts, dt) / chanw).astype(np.int32)  # (nd,nint)

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

    # ---------------------------------------------------------------
    # FALSE-ALARM RATE over the control ensemble (added 2026-09-09 per
    # Glenn's instruction, replacing the bare `src_peak > ctrl_peak`
    # inequality that previously set the candidate flag).
    #
    # THE DEFECT THIS REPLACES -- measured, not asserted. `src_peak` is a
    # maximum over ALL n_src source-region positions (the star plus the
    # 1.1" ring: 135 positions in the real AU Mic B6 dataset) x channels
    # x drift trials, while EVERY entry of ctrl_max is a maximum over
    # exactly ONE position x channels x drifts. Comparing a max-of-n_src
    # statistic against a max-of-1 null is biased toward "detection":
    # under pure noise with exchangeable positions the overall maximum
    # falls inside the source region with probability
    # n_src/(n_src+n_control) -- 135/647 = 20.9% in that same real case,
    # i.e. the old flag fired on roughly one pure-noise search in five.
    # AU Mic B6 is the worked example: the STAR's own peak (5.221) is
    # exceeded by 10 of its 512 controls (p = 0.021, not significant),
    # yet the 135-position region max (5.973) cleared every control and
    # the old flag fired.
    #
    # THE REPLACEMENT is like-for-like: the primary test uses the STAR
    # position alone -- one position, exactly what each control is -- so
    # the star and the controls are exchangeable under the null. The
    # empirical p-value uses the standard conservative (+1) estimator
    # (Davison & Hinkley 1997; North et al. 2002), which cannot return
    # zero: with n_control controls the smallest RESOLVABLE p-value is
    # 1/(1+n_control), and we report that floor rather than implying more
    # resolution than the ensemble has.
    #
    # The region statistic is retained but scored against a MATCHED null:
    # resampled maxima over n_src drawn controls, so it is compared with
    # its own distribution instead of a max-of-one distribution.
    star_peak_val = float(star.max())
    _cm = np.asarray(ctrl_max, dtype=np.float64)
    _ncl = int(_cm.size)
    n_ctrl_ge_star = int((_cm >= star_peak_val).sum())
    p_star_empirical = float((1 + n_ctrl_ge_star) / (1 + _ncl)) if _ncl else float('nan')
    p_floor = float(1.0 / (1 + _ncl)) if _ncl else float('nan')

    # matched null for the region maximum (a max over n_src positions)
    p_region_matched = float('nan')
    n_region_null_ge = None
    if _ncl:
        _B = 20000
        _rng = np.random.default_rng(20260909)
        _k = int(min(n_src, _ncl))
        _idx = _rng.random((_B, _ncl)).argsort(axis=1)[:, :_k]
        _null = _cm[_idx].max(axis=1)
        n_region_null_ge = int((_null >= src_peak).sum())
        p_region_matched = float((1 + n_region_null_ge) / (1 + _B))
    # HONEST LIMITATION, caught by testing this block against real data before
    # trusting it (AU Mic B6): a null resampled from the control ensemble can
    # never exceed that ensemble's own maximum. So whenever src_peak is above
    # max(ctrl_max) -- which is precisely the condition the OLD flag tested --
    # every resample necessarily falls below it and p_region_matched saturates
    # at the 1/(B+1) floor BY CONSTRUCTION, carrying no information beyond the
    # old test. It is therefore recorded as a diagnostic only and is NOT used
    # to set any flag; the flag rests on the star-vs-controls test, which is
    # like-for-like and non-degenerate. `p_region_matched_saturated` marks the
    # degenerate case so no downstream reader mistakes the floor for evidence.
    p_region_saturated = bool(_ncl and src_peak > float(_cm.max()))

    _pct = ([float(v) for v in np.percentile(_cm, [50, 90, 99, 100])]
            if _ncl else None)
    print(f'[{EB}] FAR: star peak {star_peak_val:.3f}; '
          f'{n_ctrl_ge_star}/{_ncl} controls >= star -> p={p_star_empirical:.4g} '
          f'(floor {p_floor:.4g}); region max {src_peak:.3f} vs matched null '
          f'-> p={p_region_matched:.4g}', flush=True)

    # sensitivity of the fully de-drifted, EB-combined channel map
    sig_comb = float(np.nanmedian(1.0 / np.sqrt(np.nansum(invvar, axis=0))))
    S_min_measured = SNR_THRESH * sig_comb               # Jy, AS MEASURED at
                                                          # the star's exact
                                                          # (l,m) position
    plx = float(z['parallax']); plx_e = float(z['parallax_err'])
    d_pc = 1000.0 / plx
    d_m = d_pc * PC_M

    # Primary-beam correction (added 2026-08-30, per Glenn's instruction to
    # confirm this is done): the star's DFT-extracted flux is measured at
    # its own true (proper-motion-corrected) sky position, which is offset
    # by l_star,m_star from the MS's actual phase/pointing centre -- for a
    # crossmatch to genuinely cover the target this offset is normally tiny
    # (sub-arcsec to a few arcsec against a 17-70" beam), but is not zero,
    # and was previously not corrected for at all. The interferometer's
    # response to a source away from the pointing centre is attenuated by
    # the (two-dish-product) primary beam power pattern, approximated here
    # as a Gaussian with the same FWHM already used for the search-geometry
    # scaling (theta_PB = 1.22 lambda/D): A(theta) = exp(-4 ln2 (theta/FWHM)^2).
    # Since a real off-axis source of TRUE flux S_true is measured as
    # S_true * A(theta), the correctly PB-corrected minimum detectable
    # (or measured) flux AT THE STAR is S_min_measured / A(theta).
    l_star = float(z['l_star']); m_star = float(z['m_star'])
    pb_arcsec = float(z['pb_arcsec'])
    ARCSEC_ = np.pi / 180.0 / 3600.0
    pb_offset_arcsec = float(np.hypot(l_star, m_star) / ARCSEC_)
    pb_atten = float(np.exp(-4 * np.log(2) * (pb_offset_arcsec / pb_arcsec) ** 2))
    pb_correction = 1.0 / pb_atten
    S_min = S_min_measured * pb_correction               # Jy, PB-corrected
    eirp = 4 * np.pi * d_m**2 * (S_min * 1e-26) * chanw

    # Automated known-molecular-line contamination check (see KNOWN_LINES_GHZ
    # / check_known_line() above) -- applied at the star's own peak-SNR
    # channel, i.e. exactly the frequency/drift-rate pair that would set
    # 'credible_technosignature_candidate' below.
    star_peak_freq_ghz = float(freqs[np.argmax(star)] / 1e9)
    star_peak_drift = float(best_drift[0][np.argmax(star)])
    line_name, line_offset_mhz, likely_line = check_known_line(
        star_peak_freq_ghz, star_peak_drift, chanw, ddrift,
        rv_kms=float(os.environ.get('SETI_STAR_RV_KMS', 0.0)))

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
        S_min_measured_Jy=float(S_min_measured),
        primary_beam_offset_arcsec=pb_offset_arcsec,
        primary_beam_fwhm_arcsec=pb_arcsec,
        primary_beam_atten=pb_atten,
        primary_beam_corrected=True,
        distance_pc=d_pc, distance_pc_err=d_pc * plx_e / plx,
        EIRP_min_W=float(eirp),
        snr_threshold=SNR_THRESH,
        star_peak_snr=float(star.max()),
        star_peak_chan=int(np.argmax(star)),
        star_peak_freq_GHz=star_peak_freq_ghz,
        star_peak_drift_Hz_s=star_peak_drift,
        nearest_known_line=line_name,
        nearest_known_line_offset_MHz=line_offset_mhz,
        likely_line_contamination=likely_line,
        n_hits_above_threshold=int(hit.size),
        hit_freqs_GHz=[float(freqs[i] / 1e9) for i in hit[:50]],
        src_region_peak_snr=src_peak,
        control_peak_snr=ctrl_peak,
        # --- false-alarm-rate fields (2026-09-09) ---
        n_control_ge_star=n_ctrl_ge_star,
        p_star_empirical=p_star_empirical,
        p_value_floor=p_floor,
        p_region_matched_null=p_region_matched,
        p_region_matched_saturated=p_region_saturated,
        n_src_positions=int(n_src),
        control_snr_percentiles_50_90_99_100=_pct,
        n_control=int(len(probe)),
        n_control_dropped=int(ndropped),
        # NOTE: 'detection' is a NAIVE threshold-only flag (on-source peak
        # SNR > snr_threshold) -- it does NOT check whether the off-source
        # control positions show an equal or larger peak, which is the
        # actual test for whether a hit is source-localized vs. a
        # broadband systematic/RFI feature seen everywhere in the field.
        # Use 'credible_technosignature_candidate' for that rigorous test;
        # 'detection' is kept only for backward compatibility/debugging.
        # 2026-08-30: also require that the hit NOT already be automatically
        # identified as a known, non-drifting molecular line (previously
        # this cross-check was only ever done by hand, after the fact, for
        # the one hit the survey has produced so far -- beta Pictoris
        # CO(1-0); see check_known_line() above).
        detection=bool(star.max() > SNR_THRESH),
        # 2026-09-09: the candidate flag is now set by a FALSE-ALARM RATE over
        # the control ensemble, not by the old bare `src_peak > ctrl_peak`
        # inequality. Three changes, in order of importance:
        #   (1) the statistic is the STAR position alone, not the max over the
        #       whole n_src-position source region -- like-for-like against the
        #       single-position controls (see the derivation above);
        #   (2) it is expressed as an empirical p-value against the 512-control
        #       null, and required to sit at the ensemble's resolution FLOOR,
        #       i.e. NO control position reaches the star's peak;
        #   (3) the known-line veto is unchanged.
        # The old flag is preserved verbatim as `legacy_src_gt_ctrl_flag` so
        # that every previously published candidate count stays reproducible
        # and the reclassification is auditable rather than silent.
        credible_technosignature_candidate=bool(
            star.max() > SNR_THRESH
            and n_ctrl_ge_star == 0
            and not likely_line),
        legacy_src_gt_ctrl_flag=bool(
            star.max() > SNR_THRESH and src_peak > ctrl_peak and not likely_line),
        runtime_s=round(time.time() - t0, 1),
    )
    # Added 2026-08-26 per Glenn's request: make the search's actual
    # sensitivity/resolution immediately legible in every result, rather
    # than requiring the reader to interpret chanwidth_Hz/EIRP_min_W
    # unaided -- channel resolution varies by >100x across this survey's
    # targets purely based on what ALMA data happens to exist for each
    # star (122 kHz for PDS 70 vs 15,625 kHz for GJ 581, as one real
    # example), so an identical "no candidate" verdict can represent very
    # different search depths. 'resolution_class' gives an at-a-glance
    # read; alma_band_inferred cross-checks the data's actual frequency
    # against the nominal ALMA band (a useful sanity check in its own
    # right -- catches a wrong-band download before it's trusted).
    freq_mid_ghz = float(np.median(freqs)) / 1e9
    if chanw < 1e6:
        res_class = 'fine (<1 MHz)'
    elif chanw < 5e6:
        res_class = 'medium (1-5 MHz)'
    else:
        res_class = 'coarse (>5 MHz, continuum-mode -- weak technosignature constraint)'
    res['resolution_class'] = res_class
    _band_edges = [(3, 84, 116), (4, 125, 163), (5, 163, 211), (6, 211, 275),
                   (7, 275, 373), (8, 385, 500), (9, 602, 720), (10, 787, 950)]
    res['alma_band_inferred'] = next(
        (b for b, lo, hi in _band_edges if lo <= freq_mid_ghz <= hi), None)

    # Closure-phase vetting hook (added 2026-08-30, per Glenn's instruction):
    # only ever runs on an actual threshold-crossing candidate, so this costs
    # nothing in the overwhelming common (no-candidate) case. Uses the
    # calibrated search MS, which at this point in the pipeline has not yet
    # been cleaned up (that happens later, in continuum_map_generic.py's
    # consumers / process_one_target.sh's final cleanup).
    if res['credible_technosignature_candidate']:
        # Multi-spw update (2026-08-30): the search MS is no longer always
        # named "{EB}_search.ms" -- since the pipeline now searches every
        # distinct spw, each has its own SETI_MS override and SFX-tagged
        # filename (e.g. "{EB}_spw16_search.ms"). Reuse the exact same
        # override-then-fallback logic as seti_extract_generic.py so this
        # always points at the MS actually searched for this candidate.
        ms_path = os.environ.get('SETI_MS', f'{TARGET_DIR}/products/{EB}_search.ms')
        print(f'[{EB}] *** candidate hit -- running closure-phase point-source '
              f'vetting against {ms_path} ***', flush=True)
        cp_result = closure_phase_vetting(
            ms_path, peak_freq_hz=res['star_peak_freq_GHz'] * 1e9,
            drift_hz_s=res['star_peak_drift_Hz_s'], t_ref=float(times[0]))
        res['closure_phase_vetting'] = cp_result
        print(f'[{EB}] closure-phase vetting result: {cp_result}', flush=True)

    json.dump(res, open(JSN, 'w'), indent=1)
    np.savez_compressed(OUT, best_src=best_src, best_drift=best_drift,
                        ctrl_max=ctrl_max, freqs=freqs, sigma=sigma,
                        names=np.array(names[:n_src]))
    print(json.dumps(res, indent=1), flush=True)

    # The raw waterfall (hundreds of MB - few GB per target) was only ever
    # an intermediate input to this drift search; everything worth keeping
    # is now in the much smaller result JSON + search.npz above. Reclaim it
    # immediately rather than letting it accumulate across 100 targets
    # (disk-space discipline is the top priority for this survey).
    try:
        sz_gb = os.path.getsize(NPZ) / 1e9
        os.remove(NPZ)
        print(f'[{EB}] removed consumed waterfall {NPZ} ({sz_gb:.2f} GB reclaimed)', flush=True)
    except OSError as e:
        print(f'[{EB}] WARNING: could not remove waterfall {NPZ}: {e}', flush=True)

    # Same discipline for the per-spw split MS.  It is an intermediate: the
    # extract step consumed it into the waterfall and the closure-phase check
    # above is its last reader, so once the result JSON and search.npz are
    # written it is dead weight.  On wide-bandwidth Band 7 targets these run
    # ~30 GB per spw and had been accumulating until the disk governor
    # deadlocked the very target that created them (HD172555, 2026-09-10).
    # Only ever remove a pipeline-created split, never a user-supplied
    # SETI_MS override pointing at real archive data.
    _split = f'{TARGET_DIR}/products/{EB}{_IN_SFX}_search.ms'
    _ov = os.environ.get('SETI_MS')
    if os.path.isdir(_split) and (_ov is None or os.path.abspath(_ov) == os.path.abspath(_split)):
        try:
            _sz = sum(os.path.getsize(os.path.join(r, f))
                      for r, _, fs in os.walk(_split) for f in fs) / 1e9
            shutil.rmtree(_split)
            print(f'[{EB}] removed consumed split MS {_split} '
                  f'({_sz:.2f} GB reclaimed)', flush=True)
        except OSError as e:
            print(f'[{EB}] WARNING: could not remove split MS {_split}: {e}', flush=True)

    print(f'[{EB}] STEP3 COMPLETE in {time.time()-t0:.0f} s', flush=True)


if __name__ == '__main__':
    main()
