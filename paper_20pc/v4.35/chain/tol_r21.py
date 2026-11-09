#!/usr/bin/env python3
r"""tol_r21.py -- the recurrence reading taken over a WINDOW OF CHANNELS about
the predicted cell, instead of at the single cell, plus the de-drifted profile
over the same range.

This is the frozen reading path of `r10_recur_all.py` with ONE change: where
that script evaluates the de-drifted inverse-variance stack at one channel
`ch`, this one evaluates it at `ch + j` for every `j` in `-K..+K`, and records
the star and the control-ring maxima at each `j`.  Nothing else differs:
the same `Window`, the same baseline removal, the same weights, the same
barycentric correction, the same systemic velocities, the same stellar-frame
registration, the same per-block drift transport, the same accumulation ORDER
over integrations -- so `j = 0` must reproduce the frozen reading bit for bit,
and that is asserted per block against the published record rather than
checked by eye.

Why it exists (referee 2, major 3): the single-cell reading is registered only
as well as the stellar-frame frequency is known, and that is a VELOCITY-scale
error.  In a 15.3 kHz channel at 230 GHz, 0.1 km/s is six channels.  The paper
must therefore say what the registration error budget is, and re-derive the
exclusions at a tolerance matched to it -- as a maximum over +-k channels with
a trials correction, which is what this read-out supplies.

Usage: tol_r21.py <plan.json> <out.json.gz> [--kms 1.0] [--kmax 300]
                  [--only CID,CID] [--drive N]

Read-only on the archive.  Writes only <out.json.gz>.
"""
import gzip
import json
import math
import os
import sys
from collections import defaultdict

for _v in ('OMP_NUM_THREADS', 'OPENBLAS_NUM_THREADS', 'MKL_NUM_THREADS',
           'NUMEXPR_NUM_THREADS', 'VECLIB_MAXIMUM_THREADS'):
    os.environ[_v] = '2'
import numpy as np

sys.path.insert(0, '/data/SETI/r8')
from r8_window import Window, spectral_baseline, bary_kms, MEDWIN  # noqa

C = 299792.458
TRIG = 5.0
POS_TOL = 2.0
VSYS = json.load(open('/data/SETI/r8/starrv_v409.json'))

PLANP, OUTP = sys.argv[1], sys.argv[2]


def opt(name, default, cast):
    return cast(sys.argv[sys.argv.index(name) + 1]) if name in sys.argv \
        else default


KMS = opt('--kms', 1.0, float)
KMAX = opt('--kmax', 300, int)
ONLY = set(opt('--only', '', str).split(',')) - {''}
DRIVE = opt('--drive', 0, int)

fail = []


def ck(n, c, d=''):
    if not c:
        fail.append(n)
    print('  %-56s %s %s' % (n, 'PASS' if c else 'FAIL', d), flush=True)


def sep_arcsec(a, b):
    ra1, d1 = math.radians(a[0]), math.radians(a[1])
    ra2, d2 = math.radians(b[0]), math.radians(b[1])
    c = (math.sin(d1) * math.sin(d2)
         + math.cos(d1) * math.cos(d2) * math.cos(ra1 - ra2))
    return math.degrees(math.acos(max(-1.0, min(1.0, c)))) * 3600.0


class Prep:
    """One window, baselined once, with the inverse-variance weights.
    Verbatim from the frozen path."""

    def __init__(self, stem):
        self.w = w = Window(stem)
        I = np.nan_to_num(np.asarray(w.I, dtype=np.float32))
        self.I = I - spectral_baseline(I, MEDWIN)
        iv = 1.0 / np.asarray(w.sigma, dtype=np.float64) ** 2
        iv[~np.isfinite(iv)] = 0.0
        self.iv = iv
        self.dt = w.times - w.times[0]
        self.sign = 1.0 if w.freqs[-1] >= w.freqs[0] else -1.0
        z = np.load(stem + '_srcspec.npz', allow_pickle=True)
        self.ra = float(z['t1_ra'])
        self.dec = float(z['t1_dec'])
        self.prod_star = str(z['star_name'])
        self.v_corr = bary_kms(self.ra, self.dec, w.times)
        s = np.load(stem + '_search.npz', allow_pickle=True)
        self.best_drift = np.asarray(s['best_drift'])
        self.t_start = float(w.times.min())
        self.t_end = float(w.times.max())

    def at(self, ch, drift):
        """THE FROZEN SINGLE-CELL READING, unchanged, for the gate."""
        sh = np.rint(self.sign * drift * self.dt
                     / self.w.chanw).astype(np.int64)
        nch = self.I.shape[2]
        num = np.zeros(self.I.shape[1])
        den = 0.0
        nused = 0
        for t in range(self.I.shape[0]):
            j = ch + int(sh[t])
            if 0 <= j < nch:
                num += self.I[t, :, j] * self.iv[t, j]
                den += self.iv[t, j]
                nused += 1
        if den <= 0:
            return None
        a = num / den
        s = 1.0 / math.sqrt(den)
        return a, s, a / s, nused

    def over(self, ch, drift, K):
        """The same reading at ch+j for j in -K..+K.

        The accumulation runs over integrations in the same ascending order as
        `at()` and adds the same products, so the j = 0 column is the frozen
        value to the last bit.  Channels whose shifted index leaves the window
        for an integration simply do not receive that integration, exactly as
        the single-cell reading does.
        """
        sh = np.rint(self.sign * drift * self.dt
                     / self.w.chanw).astype(np.int64)
        nch = self.I.shape[2]
        npos = self.I.shape[1]
        n = 2 * K + 1
        num = np.zeros((npos, n))
        den = np.zeros(n)
        nused = np.zeros(n, dtype=np.int64)
        jj = np.arange(-K, K + 1)
        for t in range(self.I.shape[0]):
            idx = ch + int(sh[t]) + jj
            ok = (idx >= 0) & (idx < nch)
            if not ok.any():
                continue
            iok = idx[ok]
            num[:, ok] += self.I[t][:, iok] * self.iv[t][iok]
            den[ok] += self.iv[t][iok]
            nused[ok] += 1
        good = den > 0
        amp = np.full((npos, n), np.nan)
        sig = np.full(n, np.nan)
        amp[:, good] = num[:, good] / den[good]
        sig[good] = 1.0 / np.sqrt(den[good])
        T = amp / sig
        return amp, sig, T, nused, good


def main():
    P = json.load(open(PLANP))
    plan = [c for c in P['plan'] if not ONLY or c['cid'] in ONLY]
    groups = []
    for c in plan:
        if c['status'] != 'ok':
            continue
        pos = (c['discovery']['ra_deg'], c['discovery']['dec_deg'])
        for g in groups:
            if sep_arcsec(pos, g['pos']) <= POS_TOL:
                g['cross'].append(c)
                break
        else:
            groups.append(dict(pos=pos, cross=[c]))
    print('%d testable crossings in %d position groups'
          % (sum(len(g['cross']) for g in groups), len(groups)), flush=True)

    rows = []
    gate = []
    for g in groups:
        starname = g['cross'][0]['star']
        vs = VSYS.get(starname)
        if vs is None:
            vs = VSYS.get(starname.replace('HD ', 'HD'))
        if vs is None:
            vs = 0.0
        print('\n=== %s  (%d crossings, v_sys %+.3f km/s)'
              % (starname, len(g['cross']), vs), flush=True)
        disc = {}
        for c in g['cross']:
            st = c['discovery']['stem']
            if st not in disc:
                disc[st] = Prep(st)
            p = disc[st]
            f_ev = c['freq_GHz'] * 1e9
            ch1 = int(np.argmin(np.abs(p.w.freqs - f_ev)))
            dr = float(p.best_drift[0, ch1])
            a, sg, T, nu = p.at(ch1, dr)
            tpub = float(p.w.best_src_pub[0, ch1])
            c['_disc'] = dict(stem=st, chan=ch1, drift_Hz_s=dr,
                              v_corr_kms=p.v_corr,
                              amp_mJy=float(a[0]) * 1e3,
                              sig_mJy=float(sg) * 1e3,
                              T_matched=float(T[0]),
                              t_start_mjdsec=p.t_start, t_end_mjdsec=p.t_end,
                              chanw_Hz=p.w.chanw,
                              star_peak_freq_GHz=float(
                                  p.w.res['star_peak_freq_GHz']),
                              star_peak_snr=float(p.w.res['star_peak_snr']),
                              gate_rel=abs(T[0] - tpub)
                              / max(abs(tpub), 1e-12))
            print('  %-4s discovery %-24s ch %5d drift %+9.1f T %7.3f'
                  % (c['cid'], os.path.basename(st), ch1, dr, T[0]),
                  flush=True)
            del p
        want = defaultdict(list)
        allstems = set()
        for c in g['cross']:
            for r in c['repeats']:
                want[r['stem']].append(c)
                allstems.add((r['eb'], r['stem'],
                              r.get('in_released_catalogue')))
        for eb2, stem2, inrel in sorted(allstems):
            try:
                p = Prep(stem2)
            except Exception as exc:
                print('   LOAD FAILED %s (%r)' % (stem2, exc), flush=True)
                continue
            if sep_arcsec((p.ra, p.dec), g['pos']) > POS_TOL:
                print('   POSITION MISMATCH %s' % stem2, flush=True)
                continue
            for c in want.get(stem2, []):
                d = c['_disc']
                f_ev = c['freq_GHz'] * 1e9
                f_stel = f_ev / (1.0 - (vs - d['v_corr_kms']) / C)
                f_here = f_stel * (1.0 - (vs - p.v_corr) / C)
                lo, hi = p.w.freqs[0], p.w.freqs[-1]
                if not (min(lo, hi) - 0.5 * p.w.chanw <= f_here
                        <= max(lo, hi) + 0.5 * p.w.chanw):
                    continue
                ch = int(np.argmin(np.abs(p.w.freqs - f_here)))
                dr = d['drift_Hz_s'] * (f_here / f_ev)
                # the tolerance, in channels, matched to a velocity
                K = int(min(KMAX, max(2, round(KMS * 1e3 / C * f_here
                                               / p.w.chanw))))
                if DRIVE == 1:            # G1: a j=0 column that is not frozen
                    dr = dr * 1.05
                res = p.over(ch, dr, K)
                if res is None:
                    continue
                amp, sig, T, nused, good = res
                single = p.at(ch, dr)
                if single is None:
                    continue
                a1, s1, T1, nu1 = single
                rel = abs(T[0, K] - T1[0]) / max(abs(T1[0]), 1e-12)
                gate.append(rel)
                tstar = T[0, :]
                tctl = np.nanmax(T[1:, :], axis=0)
                rows.append(dict(
                    cid=c['cid'], star=c['star'], eb=eb2, stem=stem2,
                    spw=os.path.basename(stem2).split('_spw')[-1],
                    in_released_catalogue=inrel,
                    chanw_Hz=p.w.chanw, K=K,
                    n_int=int(len(p.w.times)),
                    t_start_mjdsec=p.t_start, t_end_mjdsec=p.t_end,
                    sep_from_discovery_h=(p.t_start - d['t_start_mjdsec'])
                    / 3600.0,
                    f_here_GHz=f_here / 1e9, chan=ch, drift_Hz_s=dr,
                    star_peak_freq_GHz=float(p.w.res['star_peak_freq_GHz']),
                    star_peak_snr=float(p.w.res['star_peak_snr']),
                    T_frozen_single=float(T1[0]),
                    gate_rel=rel,
                    amp_mJy=[None if not gk else float(x) * 1e3
                             for x, gk in zip(amp[0, :], good)],
                    sig_mJy=[None if not gk else float(x) * 1e3
                             for x, gk in zip(sig, good)],
                    T_star=[None if not gk else float(x)
                            for x, gk in zip(tstar, good)],
                    T_ctrl_max=[None if not gk else float(x)
                                for x, gk in zip(tctl, good)],
                    n_used=[int(x) for x in nused]))
                print('   %-4s %-22s K=%3d  T(0)=%7.3f  max|j|<=K %7.3f at '
                      'j=%+d  ctrlmax %7.3f  (gate %.1e)'
                      % (c['cid'], os.path.basename(stem2), K, T[0, K],
                         float(np.nanmax(tstar)),
                         int(np.nanargmax(tstar)) - K,
                         float(np.nanmax(tctl)), rel), flush=True)
            del p

    ck('G1 the j = 0 column reproduces the frozen single-cell reading',
       bool(gate) and max(gate) < 1e-12,
       '%d block readings, worst relative difference %.1e'
       % (len(gate), max(gate) if gate else -1))

    out = dict(generator=os.path.basename(__file__), kms=KMS, kmax=KMAX,
               drive=DRIVE, trigger=TRIG, n_rows=len(rows),
               gate_worst=max(gate) if gate else None,
               discovery={c['cid']: c['_disc'] for g in groups
                          for c in g['cross'] if '_disc' in c},
               rows=rows)
    with gzip.open(OUTP, 'wt') as fh:
        json.dump(out, fh, default=float)
    print('\nwrote %s (%d rows)' % (OUTP, len(rows)))
    if fail:
        print('FAILED: %s' % fail)
        sys.exit(1)


if __name__ == '__main__':
    main()
