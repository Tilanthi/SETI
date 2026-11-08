#!/usr/bin/env python3
"""
Second-pass re-analysis of the retained per-star dynamic spectra
(srcspec.npz), extending the primary linear-drift/threshold search with
two complementary signal classes it is blind to by design (Glenn's Tier-1
"advanced analysis" request, 2026-08-30):

  (a) a CHIRPED (quadratic-drift) narrowband search, for a transmitter
      whose drift rate itself changes over the observation (e.g. very
      short-period/high-eccentricity orbital motion, faster than the
      linear approximation the primary search assumes captures);
  (b) a time-domain PERIODICITY/PULSE search, for a modulated or pulsed
      (rather than continuous) narrowband signal -- a pure drift-rate
      search cannot distinguish a pulsed carrier from continuous noise
      averaged over the same integration.

Both reuse ONLY the already-retained srcspec.npz (star's own spectrum +
8 sampled control positions) -- no re-download, no re-extraction, no
CASA needed; this is exactly what that retention was for. Coarser trial
grids than the primary search are used deliberately (this is an
exploratory second pass over already-searched data, not a replacement
for the primary pipeline), and this is stated explicitly wherever these
results are reported.

Usage: reanalyze_srcspec.py <srcspec.npz>
Writes: <same path>_reanalysis.json
"""
import sys, os, json, time
import numpy as np
from scipy.ndimage import median_filter

SNR_THRESH = 5.0
MEDWIN = 65
EDGE_FRAC = 0.04
DRIFT_COEFF_HZ_PER_GHZ = 12.0
N_DRIFT_TRIALS = 21
N_CHIRP_TRIALS = 5


def main(path):
    t0 = time.time()
    z = np.load(path, allow_pickle=True)
    I_star = z['I_star']              # (nint, nch)
    I_ctrl = z['I_control_sample']    # (nint, n_ctrl, nch)
    W = z['W']                        # (nint, nch)
    times = z['times']; freqs = z['freqs']; chanw = float(z['chanw'])
    star_name = str(z['star_name'])
    nint, nch = I_star.shape
    n_ctrl = I_ctrl.shape[1]

    if nint < 8 or nch < 16:
        json.dump(dict(error='too small', nint=int(nint), nch=int(nch)),
                   open(path.replace('.npz', '_reanalysis.json'), 'w'))
        return

    # combine star (position 0) + controls (positions 1..n_ctrl) into one
    # array so both searches below treat them uniformly
    I_all = np.concatenate([I_star[:, None, :], I_ctrl], axis=1)  # (nint, 1+n_ctrl, nch)
    npos = I_all.shape[1]

    # ---- shared baseline removal (per-integration running-median across
    # frequency, same convention as the primary search) ----
    win = max(9, min(MEDWIN, (nch // 2) | 1))
    baseline = median_filter(I_all, size=(1, 1, win), mode='nearest')
    resid = I_all - baseline

    e0 = int(EDGE_FRAC * nch)
    good_ch = np.ones(nch, dtype=bool)
    good_ch[:e0] = False
    good_ch[nch - e0:] = False

    # empirical per-channel noise from the CONTROL ensemble only (avoids
    # biasing the noise estimate by a possible real signal in the star)
    ctrl_resid = resid[:, 1:, :]
    sigma = 1.4826 * np.nanmedian(
        np.abs(ctrl_resid - np.nanmedian(ctrl_resid, axis=(0, 1), keepdims=True)),
        axis=(0, 1))
    sigma[sigma <= 0] = np.nanmedian(sigma[sigma > 0]) if np.any(sigma > 0) else 1.0
    invvar = np.where(good_ch, 1.0 / sigma**2, 0.0)

    out = dict(star_name=star_name, path=path, nint=int(nint), nch=int(nch),
               n_ctrl=int(n_ctrl))

    # ================================================= (a) CHIRP SEARCH
    try:
        dt = (times - times[0]).astype(np.float64)
        span = max(dt.max() - dt.min(), 1.0)
        freq_mid = float(np.median(freqs))
        drift_max = DRIFT_COEFF_HZ_PER_GHZ * (freq_mid / 1e9)
        drifts = np.linspace(-drift_max, drift_max, N_DRIFT_TRIALS)
        chirp_max = 2.0 * drift_max / span   # Hz/s^2: lets drift sweep its
                                              # own full dynamic range once
        chirps = np.linspace(-chirp_max, chirp_max, N_CHIRP_TRIALS)
        freq_sign = 1.0 if freqs[-1] >= freqs[0] else -1.0

        X = np.nan_to_num(resid) * invvar[None, None, :]
        best = np.full((npos, nch), -np.inf, dtype=np.float64)
        for c in chirps:
            for d in drifts:
                shift = np.rint(freq_sign * (d * dt + 0.5 * c * dt**2) / chanw).astype(np.int64)
                num = np.zeros((npos, nch)); den = np.zeros(nch)
                for t in range(nint):
                    s = int(shift[t])
                    if s == 0:
                        num += X[t]; den += invvar
                    elif 0 < s < nch:
                        num[:, :nch - s] += X[t][:, s:]; den[:nch - s] += invvar[s:]
                    elif -nch < s < 0:
                        sneg = -s
                        num[:, sneg:] += X[t][:, :nch - sneg]; den[sneg:] += invvar[:nch - sneg]
                snr = np.divide(num, np.sqrt(np.maximum(den, 1e-30)),
                                 out=np.zeros_like(num), where=den > 0)
                best = np.maximum(best, snr)
        star_best = best[0]
        ctrl_best = best[1:]
        star_peak_snr = float(np.nanmax(star_best))
        star_peak_ch = int(np.nanargmax(star_best))
        ctrl_peak_snr = float(np.nanmax(ctrl_best))
        out['chirp_search'] = dict(
            n_drift_trials=N_DRIFT_TRIALS, n_chirp_trials=N_CHIRP_TRIALS,
            drift_max_Hz_s=drift_max, chirp_max_Hz_s2=chirp_max,
            star_peak_snr=star_peak_snr, star_peak_chan=star_peak_ch,
            star_peak_freq_GHz=float(freqs[star_peak_ch] / 1e9),
            control_peak_snr=ctrl_peak_snr,
            credible=bool(star_peak_snr > SNR_THRESH and star_peak_snr > ctrl_peak_snr))
    except Exception as e:
        out['chirp_search'] = dict(error=str(e))

    # ============================================ (b) PERIODICITY SEARCH
    try:
        # weighted time-mean subtraction per (position, channel), then FFT
        # along the time axis; use only the good (non-edge) channels
        wsum = np.sum(W, axis=0)  # (nch,)
        tmean = np.divide(np.sum(I_all * W[:, None, :], axis=0), wsum[None, :],
                           out=np.zeros((npos, nch)), where=wsum[None, :] > 0)
        centered = I_all - tmean[None, :, :]
        centered = np.nan_to_num(centered)
        spec = np.fft.rfft(centered, axis=0)          # (nfreq, npos, nch)
        power = np.abs(spec)**2
        power = power[1:]                              # drop DC bin
        med = np.nanmedian(power, axis=0, keepdims=True)
        mad = 1.4826 * np.nanmedian(np.abs(power - med), axis=0, keepdims=True)
        mad[mad <= 0] = np.nanmedian(mad[mad > 0]) if np.any(mad > 0) else 1.0
        zscore = (power - med) / mad                   # (nfreq, npos, nch)
        peak_z = np.nanmax(zscore, axis=0)              # (npos, nch)
        peak_bin = np.nanargmax(zscore, axis=0)         # (npos, nch)
        peak_z_masked = np.where(good_ch[None, :], peak_z, -np.inf)
        star_z = peak_z_masked[0]
        ctrl_z = peak_z_masked[1:]
        star_best_ch = int(np.nanargmax(star_z))
        star_best_z = float(star_z[star_best_ch])
        ctrl_best_z = float(np.nanmax(ctrl_z))
        n_time_bins = power.shape[0] + 1
        best_period_bin = int(peak_bin[0, star_best_ch]) + 1
        period_s = float(span / best_period_bin) if best_period_bin > 0 else None
        out['periodicity_search'] = dict(
            n_freq_bins_tested=int(power.shape[0]),
            star_peak_z=star_best_z, star_peak_chan=star_best_ch,
            star_peak_freq_GHz=float(freqs[star_best_ch] / 1e9),
            candidate_period_s=period_s,
            control_peak_z=ctrl_best_z,
            credible=bool(star_best_z > SNR_THRESH and star_best_z > ctrl_best_z))
    except Exception as e:
        out['periodicity_search'] = dict(error=str(e))

    out['runtime_s'] = round(time.time() - t0, 1)
    json.dump(out, open(path.replace('.npz', '_reanalysis.json'), 'w'), indent=1)
    print(f"{star_name}: chirp_peak={out.get('chirp_search',{}).get('star_peak_snr','?')} "
          f"periodicity_peak_z={out.get('periodicity_search',{}).get('star_peak_z','?')} "
          f"({out['runtime_s']}s)", flush=True)


if __name__ == '__main__':
    main(sys.argv[1])
