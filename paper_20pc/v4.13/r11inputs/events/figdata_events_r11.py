#!/usr/bin/env python3
r"""figdata_events_r11.py -- HOST-SIDE extraction for the two-event figure.

Read-only.  Produces one compact npz per crossing holding exactly what the
figure draws, so the figure generator in the manuscript tree needs no access
to the 29 MB product files:

  dyn        (nint, 2W+1)  baselined star dynamic spectrum, mJy, about the
                           event channel, NOT de-drifted
  dyn_dd     (nint, 2W+1)  the same rows shifted by the integer channel
                           displacement of the best-fitting drift
  sig_t      (nint,)       per-integration noise at the event channel, mJy
  dt         (nint,)       seconds from the first integration
  T_star     (2W+1,)       inverse-variance de-drifted stack at the event
                           drift, in units of its own noise, per channel
  T_ctrl     (nctrl, 2W+1) the same for each retained control position
  ctrl_max   (512,)        the published image-plane rank statistics
  freqs      (2W+1,)       sky frequency, Hz

and for every repeat block of the same crossing, registered on the channel
the event's stellar-frame frequency lands on in that epoch:

  r_T        (nrep, 2W+1)  matched-drift stack in units of its own noise
  r_amp      (nrep, 2W+1)  the same as an amplitude, mJy
  r_sig      (nrep, 2W+1)  its noise, mJy

The stacking is `Prep.at` from r10_recur_all.py, which is the same code path
that produced the published exclusions; the gate below requires the
reconstructed discovery statistic to reproduce the published one.

Usage: figdata_events_r11.py <plan.json> <outdir>
"""
import json
import math
import os
import sys

for _v in ('OMP_NUM_THREADS', 'OPENBLAS_NUM_THREADS', 'MKL_NUM_THREADS',
           'NUMEXPR_NUM_THREADS', 'VECLIB_MAXIMUM_THREADS'):
    os.environ[_v] = '2'
import numpy as np

sys.path.insert(0, '/data/SETI/r8')
from r8_window import Window, spectral_baseline, MEDWIN      # noqa

PLANP, OUTDIR = sys.argv[1], sys.argv[2]
HALF = 48


class Prep:
    def __init__(self, stem):
        self.w = w = Window(stem)
        I = np.nan_to_num(np.asarray(w.I, dtype=np.float32))
        self.I = I - spectral_baseline(I, MEDWIN)
        iv = 1.0 / np.asarray(w.sigma, dtype=np.float64) ** 2
        iv[~np.isfinite(iv)] = 0.0
        self.iv = iv
        self.dt = w.times - w.times[0]
        self.sign = 1.0 if w.freqs[-1] >= w.freqs[0] else -1.0

    def shifts(self, drift):
        return np.rint(self.sign * drift * self.dt
                       / self.w.chanw).astype(np.int64)

    def at(self, ch, drift):
        sh = self.shifts(drift)
        nch = self.I.shape[2]
        num = np.zeros(self.I.shape[1])
        den = 0.0
        for t in range(self.I.shape[0]):
            j = ch + int(sh[t])
            if 0 <= j < nch:
                num += self.I[t, :, j] * self.iv[t, j]
                den += self.iv[t, j]
        if den <= 0:
            return None
        a = num / den
        s = 1.0 / math.sqrt(den)
        return a, s

    def band(self, ch, drift, half):
        """T, amp and sigma per channel over +-half channels of `ch`, all at
        the one drift."""
        lo = max(0, ch - half)
        hi = min(self.I.shape[2], ch + half + 1)
        T = np.full((self.I.shape[1], 2 * half + 1), np.nan)
        A = np.full((self.I.shape[1], 2 * half + 1), np.nan)
        S = np.full(2 * half + 1, np.nan)
        for c in range(lo, hi):
            got = self.at(c, drift)
            if got is None:
                continue
            a, s = got
            T[:, c - ch + half] = a / s
            A[:, c - ch + half] = a * 1e3
            S[c - ch + half] = s * 1e3
        return T, A, S

    def dyn(self, ch, drift, half):
        """The star's rows about `ch`, raw and shifted by the drift."""
        nch = self.I.shape[2]
        sh = self.shifts(drift)
        n = self.I.shape[0]
        raw = np.full((n, 2 * half + 1), np.nan, dtype=np.float32)
        dd = np.full((n, 2 * half + 1), np.nan, dtype=np.float32)
        st = np.full(n, np.nan)
        for t in range(n):
            for k in range(-half, half + 1):
                j = ch + k
                if 0 <= j < nch:
                    raw[t, k + half] = self.I[t, 0, j] * 1e3
                j2 = ch + k + int(sh[t])
                if 0 <= j2 < nch:
                    dd[t, k + half] = self.I[t, 0, j2] * 1e3
            j = ch + int(sh[t])
            if 0 <= j < nch and self.iv[t, j] > 0:
                st[t] = 1e3 / math.sqrt(self.iv[t, j])
        return raw, dd, st


def main():
    P = json.load(open(PLANP))
    os.makedirs(OUTDIR, exist_ok=True)
    meta = {}
    for cid, c in P.items():
        print('=== %s %s %.6f GHz' % (cid, c['star'], c['freq_GHz']),
              flush=True)
        d = c['disc']
        p = Prep(d['stem'])
        f_ev = c['freq_GHz'] * 1e9
        ch = int(np.argmin(np.abs(p.w.freqs - f_ev)))
        assert ch == d['chan'], (ch, d['chan'])
        drift = float(p.w.best_src_pub.shape and
                      np.load(d['stem'] + '_search.npz')['best_drift'][0, ch])
        half = min(HALF, ch, p.I.shape[2] - 1 - ch)
        T, A, S = p.band(ch, drift, half)
        tpub = float(p.w.best_src_pub[0, ch])
        rel = abs(T[0, half] - tpub) / max(abs(tpub), 1e-12)
        print('   gate  T recon %.6f  published %.6f  rel %.2e'
              % (T[0, half], tpub, rel), flush=True)
        assert rel < 1e-6, rel
        raw, dd, st = p.dyn(ch, drift, half)
        lo, hi = ch - half, ch + half + 1
        o = dict(dyn=raw, dyn_dd=dd, sig_t=st, dt=p.dt,
                 T_star=T[0], T_ctrl=T[1:], amp_star=A[0], sig_ch=S,
                 ctrl_max=np.asarray(p.w.ctrl_max_pub),
                 freqs=p.w.freqs[lo:hi], chanw=p.w.chanw,
                 shifts=p.shifts(drift), half=half)
        mt = dict(cid=cid, star=c['star'], display=c['display'],
                  freq_GHz=c['freq_GHz'], chan=ch, half=half, drift=drift,
                  chanw_Hz=p.w.chanw,
                  T_disc=float(T[0, half]), T_pub=tpub,
                  n_int=int(len(p.dt)),
                  t_start_mjd=float(p.w.times.min()) / 86400.0,
                  t_end_mjd=float(p.w.times.max()) / 86400.0,
                  on_source_s=float(p.w.res['on_source_s']),
                  eirp_trig_W=float(p.w.res['EIRP_min_W']),
                  dist_pc=float(p.w.res['distance_pc']),
                  n_ctrl=int(p.w.res['n_control']),
                  ctrl_max_max=float(np.asarray(p.w.ctrl_max_pub).max()),
                  n_ctrl_ge_star=int(p.w.res['n_control_ge_star']),
                  repeats=[])
        del p
        rT, rA, rS, rmeta = [], [], [], []
        for r in c['repeats']:
            q = Prep(r['stem'])
            chr_ = int(np.argmin(np.abs(q.w.freqs - r['f_here_GHz'] * 1e9)))
            hh = min(half, chr_, q.I.shape[2] - 1 - chr_)
            T2, A2, S2 = q.band(chr_, r['drift'], hh)
            pad = half - hh

            def _p(a, nd=1):
                if pad == 0:
                    return a
                if nd == 1:
                    return np.concatenate([np.full(pad, np.nan), a,
                                           np.full(pad, np.nan)])
                return np.concatenate(
                    [np.full((a.shape[0], pad), np.nan), a,
                     np.full((a.shape[0], pad), np.nan)], axis=1)
            rT.append(_p(T2[0]))
            rA.append(_p(A2[0]))
            rS.append(_p(S2))
            rmeta.append(dict(eb=r['eb'], sep_h=r['sep_h'],
                              chan=chr_, in_cat=r['in_cat'],
                              f_here_GHz=r['f_here_GHz'],
                              sig_mJy=r['sig_mJy'],
                              t_start_mjd=float(q.w.times.min()) / 86400.0,
                              T_at_cell=float(T2[0, hh])))
            print('   repeat %-22s sep %+8.2f h  T at cell %+7.3f'
                  % (r['eb'], r['sep_h'], T2[0, hh]), flush=True)
            del q
        o['r_T'] = np.array(rT)
        o['r_amp'] = np.array(rA)
        o['r_sig'] = np.array(rS)
        mt['repeats'] = rmeta
        np.savez_compressed(os.path.join(OUTDIR, 'figdata_%s.npz' % cid), **o)
        meta[cid] = mt
    json.dump(meta, open(os.path.join(OUTDIR, 'figdata_meta.json'), 'w'),
              indent=1)
    print('\nwrote %s' % OUTDIR)


main()
