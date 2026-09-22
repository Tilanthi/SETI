#!/usr/bin/env python3
"""Independent re-derivation of the CP-72 2713 two-epoch comparison.

Runs on the processing host, read-only, against the retained search products.
It reimplements the release pipeline's statistic (edge trim, 65-channel
frequency-median baseline, inverse-variance weighted de-drifted stack) from
`*_srcspec.npz` (the star's own raw spectrum) plus the per-channel noise
`sigma` retained in `*_search.npz`, and checks it against the published
first-epoch value before using it on the second epoch.

Nothing is written outside the caller's own directory.
"""
import json
import sys

import numpy as np

B7 = '/data/SETI/targets/CP-72_2713_B7/products/A002_Xff0235_X4a6d_spw3'
EB2 = '/data/SETI/targets/CP-72_2713_EB2/products/A002_Xff0235_X502d_spw3'
MEDWIN = 65
EDGE_FRAC = 0.04


def spectral_baseline(a, win):
    """Verbatim from seti_drift_search_generic.py."""
    lead = a.shape[:-1]
    n = a.shape[-1]
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


class Epoch:
    def __init__(self, stem):
        self.stem = stem
        self.res = json.load(open(stem + '_result.json'))
        s = np.load(stem + '_search.npz', allow_pickle=True)
        z = np.load(stem + '_srcspec.npz', allow_pickle=True)
        self.sigma = s['sigma']                 # (nint, nch) after edge trim
        self.freqs = s['freqs']
        self.ctrl_max = s['ctrl_max']
        self.best_src = s['best_src']
        self.best_drift = s['best_drift']
        I = z['I_star']
        W = z['W']
        self.times = z['times']
        chanw = float(z['chanw'])
        self.chanw = chanw
        nch0 = I.shape[1]
        e0 = int(EDGE_FRAC * nch0)
        chan_ok = (W > 0).mean(axis=0) > 0.5
        lo = e0
        while lo < nch0 // 2 and not chan_ok[lo]:
            lo += 1
        hi = nch0 - e0
        while hi > nch0 // 2 and not chan_ok[hi - 1]:
            hi -= 1
        assert hi - lo == self.sigma.shape[1], (lo, hi, self.sigma.shape)
        fr = z['freqs'][lo:hi]
        assert np.allclose(fr, self.freqs)
        I = I[:, lo:hi].astype(np.float32)
        I = I - spectral_baseline(np.nan_to_num(I), MEDWIN)
        invvar = 1.0 / self.sigma.astype(np.float64) ** 2
        invvar[~np.isfinite(invvar)] = 0.0
        self.I = np.nan_to_num(I).astype(np.float64)
        self.invvar = invvar
        self.X = self.I * invvar
        self.dt = (self.times - self.times[0]).astype(np.float64)
        self.freq_sign = 1.0 if self.freqs[-1] >= self.freqs[0] else -1.0
        step = self.res['drift_step_Hz_s']
        dmax = self.res['drift_max_Hz_s']
        self.drifts = np.arange(-dmax, dmax + step, step)
        assert len(self.drifts) == self.res['n_drift_trials']

    def at(self, chan, drift):
        """Weighted flux, its error, and S/N at one channel and one drift."""
        s = np.rint(self.freq_sign * drift * self.dt / self.chanw).astype(int)
        nch = self.I.shape[1]
        num = 0.0
        den = 0.0
        for t in range(len(self.dt)):
            c = chan + s[t]
            if 0 <= c < nch:
                num += self.X[t, c]
                den += self.invvar[t, c]
        if den <= 0:
            return np.nan, np.nan, np.nan
        return num / den, 1.0 / np.sqrt(den), num / np.sqrt(den)

    def maxdrift(self, chan):
        best = (-np.inf, None)
        for d in self.drifts:
            snr = self.at(chan, d)[2]
            if snr > best[0]:
                best = (snr, d)
        return best


def main():
    out = {}
    e1 = Epoch(B7)
    e2 = Epoch(EB2)

    # --- gate: reproduce the published first-epoch value -------------------
    ch1 = e1.res['star_peak_chan']
    d1 = e1.res['star_peak_drift_Hz_s']
    f1, ef1, t1 = e1.at(ch1, d1)
    pub = e1.res['star_peak_snr']
    out['gate'] = dict(published_T=pub, reimplemented_T=t1,
                       rel_err=abs(t1 - pub) / pub,
                       flux_mJy=f1 * 1e3, flux_err_mJy=ef1 * 1e3,
                       chan=ch1, drift=d1)
    mx1 = e1.maxdrift(ch1)
    out['gate']['max_over_own_grid'] = dict(T=mx1[0], drift=float(mx1[1]))

    # --- frequency axes ----------------------------------------------------
    out['freq'] = dict(
        f1_ch35_Hz=float(e1.freqs[ch1]), f2_ch35_Hz=float(e2.freqs[ch1]),
        offset_kHz=(float(e2.freqs[ch1]) - float(e1.freqs[ch1])) / 1e3,
        offset_chan=(float(e2.freqs[ch1]) - float(e1.freqs[ch1])) / e1.chanw,
        chanw_Hz=e1.chanw)

    # --- epoch 2 at the matched channel and the matched drift --------------
    f2, ef2, t2 = e2.at(ch1, d1)
    out['matched'] = dict(flux_mJy=f2 * 1e3, flux_err_mJy=ef2 * 1e3, T=t2)
    # nearest node of epoch 2's own grid to epoch 1's fitted drift
    j = int(np.argmin(np.abs(e2.drifts - d1)))
    out['matched']['nearest_node_Hz_s'] = float(e2.drifts[j])
    out['matched']['node_offset_Hz_s'] = float(e2.drifts[j] - d1)
    fn, efn, tn = e2.at(ch1, float(e2.drifts[j]))
    out['matched']['at_nearest_node'] = dict(flux_mJy=fn * 1e3, T=tn)

    # --- zero drift, both epochs ------------------------------------------
    for nm, e in (('e1', e1), ('e2', e2)):
        f, ef, t = e.at(ch1, 0.0)
        out.setdefault('zero_drift', {})[nm] = dict(
            flux_mJy=f * 1e3, flux_err_mJy=ef * 1e3, T=t)

    # --- epoch 2 maximised over its own drift grid at channel 35 ----------
    mx2 = e2.maxdrift(ch1)
    out['e2_drift_max_at_ch35'] = dict(T=mx2[0], drift=float(mx2[1]),
                                       pipeline_best_src=float(e2.best_src[0, ch1]),
                                       pipeline_best_drift=float(e2.best_drift[0, ch1]))

    # --- the ten neighbouring channels in epoch 2 -------------------------
    nb = [c for c in range(ch1 - 5, ch1 + 6) if c != ch1]
    vals = [float(e2.best_src[0, c]) for c in nb]
    out['neighbours_e2'] = dict(chans=nb, vals=vals,
                                mean=float(np.mean(vals)), sd=float(np.std(vals, ddof=1)),
                                z_of_star=(float(e2.best_src[0, ch1]) - np.mean(vals)) / np.std(vals, ddof=1))

    # --- window maximum rank against the control maxima -------------------
    for nm, e in (('e1', e1), ('e2', e2)):
        wm = float(e.best_src[0].max())
        cm = np.asarray(e.ctrl_max, dtype=float)
        ge = int((cm >= wm).sum())
        out.setdefault('windowmax', {})[nm] = dict(
            star_window_max=wm, n_ctrl_ge=ge, n_ctrl=int(cm.size),
            rank=ge + 1, of=int(cm.size) + 1,
            add_one_p=(1 + ge) / (1 + cm.size),
            ctrl_max=float(cm.max()), ctrl_med=float(np.median(cm)))

    # --- depth ------------------------------------------------------------
    r1 = e1.res['rms_combined_mJy']
    r2 = e2.res['rms_combined_mJy']
    out['depth'] = dict(rms1_mJy=r1, rms2_mJy=r2, ratio=r1 / r2,
                        pct_lower_rms=100 * (1 - r2 / r1),
                        S_min1_mJy=1e3 * e1.res['S_min_Jy'],
                        S_min2_mJy=1e3 * e2.res['S_min_Jy'],
                        err1_at_feature_mJy=ef1 * 1e3,
                        err2_at_feature_mJy=ef2 * 1e3,
                        pct_lower_err_at_feature=100 * (1 - ef2 / ef1),
                        # a persistent emitter at the first epoch's fitted flux
                        # would appear in the second epoch at
                        expected_T2_if_persistent=f1 / ef2)

    # --- how strongly is a persistent constant-flux emitter disfavoured? ---
    d_two_sample = (f1 - f2) / np.hypot(ef1, ef2)
    out['exclusion'] = dict(
        # epoch 2 alone, conditioning on epoch 1's fitted amplitude as exact
        conditional_sigma=(f1 - f2) / ef2,
        # both epochs as measurements of one amplitude (no conditioning)
        two_sample_sigma=d_two_sample,
        # the drift-maximised comparison the earlier text rested on
        drift_max_sigma=(e1.res['star_peak_snr'] - e2.best_src[0, ch1]) / np.sqrt(2.0),
        flux1_mJy=f1 * 1e3, flux1_err_mJy=ef1 * 1e3,
        flux2_mJy=f2 * 1e3, flux2_err_mJy=ef2 * 1e3)

    # --- epoch times ------------------------------------------------------
    from datetime import datetime, timedelta
    ep = datetime(1858, 11, 17)

    def utc(mjdsec):
        return (ep + timedelta(seconds=float(mjdsec))).strftime('%Y-%m-%dT%H:%M:%S')
    for nm, e in (('e1', e1), ('e2', e2)):
        out.setdefault('times', {})[nm] = dict(
            start=utc(e.times.min()), end=utc(e.times.max()),
            span_s=float(e.times.max() - e.times.min()))
    gap = (e2.times.min() - e1.times.max())
    out['times']['gap_min'] = float(gap) / 60.0
    out['times']['start_to_start_h'] = float(e2.times.min() - e1.times.min()) / 3600.0

    # --- drift track sweep ------------------------------------------------
    out['sweep'] = dict(drift_Hz_s=d1, span_s=e1.res['time_span_s'],
                        sweep_MHz=abs(d1) * e1.res['time_span_s'] / 1e6,
                        sweep_chan=abs(d1) * e1.res['time_span_s'] / e1.chanw,
                        accel_m_s2=2.99792458e8 * abs(d1) / e1.freqs[ch1])

    # --- other three windows of epoch 2 -----------------------------------
    oth = []
    for spw in (0, 1, 2):
        r = json.load(open(EB2.replace('spw3', 'spw%d' % spw) + '_result.json'))
        oth.append(dict(spw=spw, star_peak=r['star_peak_snr'],
                        ctrl_max=r['control_peak_snr'],
                        hits=r['n_hits_above_threshold'],
                        detection=r['detection'],
                        lo=r['freq_lo_GHz'], hi=r['freq_hi_GHz']))
    out['other_windows_e2'] = oth

    json.dump(out, open('cp72_verify_out.json', 'w'), indent=1)
    print(json.dumps(out, indent=1))


if __name__ == '__main__':
    sys.exit(main())
