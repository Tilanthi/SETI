#!/usr/bin/env python3
"""r29-recur M11: the fitted-drift uncertainty of the J1537 crossings, in grid steps,
measured by injection into each crossing's own retained spectrum (star position, other
channels), with the release statistic re-implemented exactly as cp72_verify.py does it
(gate: reproduce the published T at the published cell).  Read-only on the products.
usage: jx_drift.py OUT.json STEM:CHAN:DRIFT:LABEL ..."""
import json, sys, math
import numpy as np
MEDWIN = 65
EDGE_FRAC = 0.04
NINJ = 400
RNG = np.random.default_rng(2929)


def spectral_baseline(a, win):
    lead = a.shape[:-1]; n = a.shape[-1]; nb = max(2, n // win)
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
        self.res = json.load(open(stem + '_result.json'))
        s = np.load(stem + '_search.npz', allow_pickle=True)
        z = np.load(stem + '_srcspec.npz', allow_pickle=True)
        self.sigma = s['sigma']; self.freqs = s['freqs']
        I = z['I_star']; W = z['W']; self.times = z['times']
        self.chanw = float(z['chanw']); nch0 = I.shape[1]
        e0 = int(EDGE_FRAC * nch0)
        chan_ok = (W > 0).mean(axis=0) > 0.5
        lo = e0
        while lo < nch0 // 2 and not chan_ok[lo]:
            lo += 1
        hi = nch0 - e0
        while hi > nch0 // 2 and not chan_ok[hi - 1]:
            hi -= 1
        assert hi - lo == self.sigma.shape[1]
        assert np.allclose(z['freqs'][lo:hi], self.freqs)
        I = I[:, lo:hi].astype(np.float32)
        I = I - spectral_baseline(np.nan_to_num(I), MEDWIN)
        iv = 1.0 / self.sigma.astype(np.float64) ** 2
        iv[~np.isfinite(iv)] = 0.0
        self.I = np.nan_to_num(I).astype(np.float64); self.iv = iv
        self.dt = (self.times - self.times[0]).astype(np.float64)
        self.sgn = 1.0 if self.freqs[-1] >= self.freqs[0] else -1.0
        self.step = self.res['drift_step_Hz_s']; dmax = self.res['drift_max_Hz_s']
        self.dmax = dmax
        self.drifts = np.arange(-dmax, dmax + self.step, self.step)
        assert len(self.drifts) == self.res['n_drift_trials']
        self.span = float(self.dt[-1]); self.nch = self.I.shape[1]

    def shifts(self, d):
        return np.rint(self.sgn * d * self.dt / self.chanw).astype(int)

    def at(self, I, c, d):
        s = self.shifts(d); num = den = 0.0
        for t in range(len(self.dt)):
            cc = c + s[t]
            if 0 <= cc < self.nch:
                num += I[t, cc] * self.iv[t, cc]; den += self.iv[t, cc]
        return (num / den, 1 / math.sqrt(den), num / math.sqrt(den)) if den > 0 else (np.nan,) * 3

    def local_max(self, I, c0, K):
        best = (-np.inf, None, None)
        for d in self.drifts:
            s = self.shifts(d)
            cs = np.arange(c0 - K, c0 + K + 1)
            num = np.zeros(len(cs)); den = np.zeros(len(cs))
            for t in range(len(self.dt)):
                cc = cs + s[t]; ok = (cc >= 0) & (cc < self.nch)
                num[ok] += I[t, cc[ok]] * self.iv[t, cc[ok]]; den[ok] += self.iv[t, cc[ok]]
            T = np.where(den > 0, num / np.sqrt(np.maximum(den, 1e-300)), -np.inf)
            j = int(np.argmax(T))
            if T[j] > best[0]:
                best = (float(T[j]), int(cs[j]), float(d))
        return best


out = {'_doc': __doc__, 'ninj': NINJ, 'rows': []}
for spec in sys.argv[2:]:
    stem, chan, drift, label = spec.split(':')
    chan = int(chan); drift = float(drift)
    e = Epoch(stem)
    f, ef, T = e.at(e.I, chan, drift)
    pub = e.res['star_peak_snr'] if e.res['star_peak_chan'] == chan else None
    K = int(math.ceil(e.dmax * e.span / e.chanw)) + 2
    gl = e.local_max(e.I, chan, K)
    # profile over drift (max over start channels within +-K)
    prof = []
    for d in e.drifts:
        s = e.shifts(d); best = -np.inf
        for c in range(chan - K, chan + K + 1):
            best = max(best, e.at(e.I, c, d)[2])
        prof.append(best)
    prof = np.array(prof); Tm = prof.max()
    ok1 = e.drifts[prof >= Tm - 1.0]
    def family(dc):
        rec = []
        tries = 0
        while len(rec) < NINJ and tries < 20 * NINJ:
            tries += 1
            c0 = int(RNG.integers(K + 3, e.nch - K - 3))
            if abs(c0 - chan) < 3 * K:
                continue
            dinj = dc + (RNG.random() - 0.5) * e.step
            _, err, _ = e.at(e.I, c0, dinj)
            if not np.isfinite(err):
                continue
            A = T * err
            I2 = e.I.copy(); s = e.shifts(dinj)
            for t in range(len(e.dt)):
                cc = c0 + s[t]
                if 0 <= cc < e.nch:
                    I2[t, cc] += A
            Tr, cr, dr = e.local_max(I2, c0, K)
            rec.append((Tr, dr - dinj, dr))
        return np.array(rec)
    rec = family(drift)
    rz = family(0.0)
    dz = rz[rz[:, 0] >= 5.0]
    det = rec[rec[:, 0] >= 5.0]
    dd = det[:, 1] / e.step
    row = dict(label=label, stem=stem, chan=chan, drift=drift, T=T, T_pub=pub,
               gate_rel=(abs(T - pub) / pub if pub else None), flux_mJy=f * 1e3, err_mJy=ef * 1e3,
               local_max=gl, step=e.step, dmax=e.dmax, span_s=e.span, on_source_s=e.res['on_source_s'],
               chanw=e.chanw, n_int=len(e.dt), ntrial=len(e.drifts),
               eta_onsource=e.dmax * e.res['on_source_s'] / e.chanw, eta_span=e.dmax * e.span / e.chanw,
               drift_steps=drift / e.step,
               prof_dT1_lo=float(ok1.min()), prof_dT1_hi=float(ok1.max()),
               n_inj=len(rec), n_det=len(det), det_frac=len(det) / len(rec),
               sd_steps=float(np.std(dd)), q16=float(np.percentile(dd, 16)), q84=float(np.percentile(dd, 84)),
               q025=float(np.percentile(dd, 2.5)), q975=float(np.percentile(dd, 97.5)),
               mad_steps=float(1.4826 * np.median(np.abs(dd - np.median(dd)))),
               bias_steps=float(np.median(dd)),
               sd_steps_all=float(np.std(rec[:, 1] / e.step)),
               frac_rec_within_zero_of_true=float(np.mean(np.abs(det[:, 2]) <= abs(drift) - 3 * e.step)) if abs(drift) > 3 * e.step else None)
    row['zero_n_det'] = len(dz)
    row['zero_sd_steps'] = float(np.std(dz[:, 2] / e.step))
    row['zero_q975_abs_steps'] = float(np.percentile(np.abs(dz[:, 2] / e.step), 97.5))
    row['zero_frac_ge_obs'] = float(np.mean(np.abs(dz[:, 2]) >= abs(drift) - 1e-9))
    row['zero_frac_le_obs'] = float(np.mean(np.abs(dz[:, 2]) <= abs(drift) + 1e-9))
    row['z_from_zero'] = abs(drift) / (e.step * row['sd_steps']) if row['sd_steps'] > 0 else None
    out['rows'].append(row)
    print(json.dumps({k: (round(v, 4) if isinstance(v, float) else v) for k, v in row.items() if k not in ('stem',)}))
json.dump(out, open(sys.argv[1], 'w'), indent=1)
