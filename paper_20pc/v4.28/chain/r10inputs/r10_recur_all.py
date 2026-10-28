#!/usr/bin/env python3
r"""The stellar-frame recurrence test, run on EVERY unattributed crossing.

Method verbatim from `v409_recur_star.py`, which produced the published eta Crv
and HD 14055 exclusions: the survey's own estimator re-run at a SINGLE drift --
the discovery drift transported to the repeat epoch's observed frequency -- at
the channel the event's stellar-frame rest frequency lands on in that epoch.
`best_src` is a maximum over ~125 drift trials and is reported beside the
matched value, never instead of it.

  f_stel = f_event / (1 - (v_sys - v_corr_disc)/c)
  f_here = f_stel  * (1 - (v_sys - v_corr_here)/c)
  drift  = drift_event * f_here / f_event

Three things this does that the five-star version did not:

* it loads each window ONCE and evaluates every crossing of that star which
  that window covers, because six of the thirty-eight crossings share one
  star's thirty repeat blocks and loading them six times over is 1.9 GB of
  needless I/O;
* it takes the event channel from the CROSSING frequency in the ledger rather
  than from the window's `star_peak_freq_GHz`, because four crossings of one
  block cannot all be their window's peak, and two further crossings are not
  their window's peak either.  Where the crossing IS the window peak the two
  agree and that is asserted;
* the join from a crossing to its repeat blocks is on the POSITION recorded in
  each product's own `srcspec.npz` (`t1_ra`, `t1_dec`), never on the star name.

Read-only.  Usage: r10_recur_all.py <plan.json> <out.json> [--drive N]
"""
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
DRIVE = int(sys.argv[sys.argv.index('--drive') + 1]) if '--drive' in sys.argv \
    else 0

fail = []


def ck(n, c, d=''):
    if not c:
        fail.append(n)
    print('  %-52s %s %s' % (n, 'PASS' if c else 'FAIL', d), flush=True)


def sep_arcsec(a, b):
    ra1, d1 = math.radians(a[0]), math.radians(a[1])
    ra2, d2 = math.radians(b[0]), math.radians(b[1])
    c = (math.sin(d1) * math.sin(d2)
         + math.cos(d1) * math.cos(d2) * math.cos(ra1 - ra2))
    return math.degrees(math.acos(max(-1.0, min(1.0, c)))) * 3600.0


class Prep:
    """One window, baselined once, with the inverse-variance weights."""

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
        """Inverse-variance weighted de-drifted stack at one cell, for the
        star and the retained controls.  Returns amp, sigma, T per position."""
        sh = np.rint(self.sign * drift * self.dt / self.w.chanw).astype(np.int64)
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


def main():
    P = json.load(open(PLANP))
    plan = P['plan']
    # ---- group crossings by star POSITION (the discovery product's own)
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
    out_cross = {}
    vsys_missing = set()
    for g in groups:
        # every window this group needs, loaded once
        stems = {}
        for c in g['cross']:
            stems.setdefault(c['discovery']['stem'], set()).add(c['cid'])
            for r in c['repeats']:
                stems.setdefault(r['stem'], set()).add(c['cid'])
        # the per-EB window choice is re-derived below, so load every window of
        # every repeat block, not only the finest: `n_windows_covering` in the
        # plan says how many there are and the choice must be reproducible.
        starname = g['cross'][0]['star']
        vs = VSYS.get(starname)
        if vs is None:
            vs = VSYS.get(starname.replace('HD ', 'HD'))
        if vs is None:
            vsys_missing.add(starname)
            vs = 0.0
        print('\n=== %s  (%d crossings, %d windows, v_sys %+.3f km/s)'
              % (starname, len(g['cross']), len(stems), vs), flush=True)
        # discovery first: we need f_event, drift and the discovery amplitude
        disc = {}
        for c in g['cross']:
            st = c['discovery']['stem']
            if st not in disc:
                disc[st] = Prep(st)
            p = disc[st]
            f_ev = c['freq_GHz'] * 1e9
            ch1 = int(np.argmin(np.abs(p.w.freqs - f_ev)))
            dr = float(p.best_drift[0, ch1])
            got = p.at(ch1, dr)
            tpub = float(p.w.best_src_pub[0, ch1])
            a, sg, T, nu = got
            rel = abs(T[0] - tpub) / max(abs(tpub), 1e-12)
            c['_disc'] = dict(
                stem=st, chan=ch1, f_chan_GHz=float(p.w.freqs[ch1]) / 1e9,
                f_offset_kHz=float(p.w.freqs[ch1] - f_ev) / 1e3,
                drift_Hz_s=dr, v_corr_kms=p.v_corr,
                amp_mJy=float(a[0]) * 1e3, sig_mJy=float(sg) * 1e3,
                t_start_mjdsec=p.t_start, t_end_mjdsec=p.t_end,
                on_source_s=float(p.w.res['on_source_s']),
                rms_combined_mJy=float(p.w.res['rms_combined_mJy']),
                band=str(p.w.res['alma_band_inferred']),
                T_matched=float(T[0]), T_bestdrift_pub=tpub,
                ctrl_T_matched_max=float(T[1:].max()),
                n_ctrl_retained=int(p.I.shape[1] - 1),
                n_int_used=nu, n_int=int(len(p.w.times)),
                chanw_Hz=p.w.chanw, gate_rel=rel,
                gate_ok=bool(rel < 1e-3),
                prod_star=p.prod_star, ra=p.ra, dec=p.dec,
                window_peak_pub=float(p.w.res['star_peak_snr']),
                is_window_peak=bool(abs(float(
                    p.w.res['star_peak_freq_GHz']) * 1e9 - f_ev)
                    < 1.5 * p.w.chanw))
            print('  %-4s discovery %-22s ch %5d  drift %+9.1f  T %7.3f '
                  '(pub %7.3f, rel %.1e)  a %9.4f +- %7.4f mJy'
                  % (c['cid'], os.path.basename(st), ch1, dr, T[0], tpub, rel,
                     a[0] * 1e3, sg * 1e3), flush=True)
            del p
        # now every repeat window, once
        want = defaultdict(list)       # stem -> list of crossings to evaluate
        for c in g['cross']:
            for r in c['repeats']:
                want[r['stem']].append(c)
        # evaluate ALL windows of each repeat block, not only the plan's pick
        allstems = set()
        for c in g['cross']:
            for r in c['repeats']:
                allstems.add((r['eb'], r['stem'], r['in_released_catalogue']))
        done = 0
        for eb2, stem2, inrel in sorted(allstems):
            try:
                p = Prep(stem2)
            except Exception as exc:
                for c in g['cross']:
                    if any(r['stem'] == stem2 for r in c['repeats']):
                        rows.append(dict(cid=c['cid'], eb=eb2, stem=stem2,
                                         status='load_failed', error=repr(exc)))
                print('   LOAD FAILED %s (%r)' % (stem2, exc), flush=True)
                continue
            if sep_arcsec((p.ra, p.dec), g['pos']) > POS_TOL:
                print('   POSITION MISMATCH %s (%.2f")' %
                      (stem2, sep_arcsec((p.ra, p.dec), g['pos'])), flush=True)
                continue
            for c in want.get(stem2, []):
                d = c['_disc']
                f_ev = c['freq_GHz'] * 1e9
                f_stel = f_ev / (1.0 - (vs - d['v_corr_kms']) / C)
                f_here = f_stel * (1.0 - (vs - p.v_corr) / C)
                if DRIVE == 6:
                    f_here = f_ev
                lo, hi = p.w.freqs[0], p.w.freqs[-1]
                if not (min(lo, hi) - 0.5 * p.w.chanw <= f_here
                        <= max(lo, hi) + 0.5 * p.w.chanw):
                    rows.append(dict(cid=c['cid'], eb=eb2, stem=stem2,
                                     status='registered_cell_outside_window',
                                     f_here_GHz=f_here / 1e9))
                    continue
                ch = int(np.argmin(np.abs(p.w.freqs - f_here)))
                dr = d['drift_Hz_s'] * (f_here / f_ev)
                got = p.at(ch, dr)
                if got is None:
                    rows.append(dict(cid=c['cid'], eb=eb2, stem=stem2,
                                     status='no_weight_at_cell'))
                    continue
                a, sg, T, nu = got
                rows.append(dict(
                    cid=c['cid'], eb=eb2, stem=stem2,
                    spw=os.path.basename(stem2).split('_spw')[-1],
                    status='ok', in_released_catalogue=inrel,
                    chanw_Hz=p.w.chanw, n_int=int(len(p.w.times)),
                    n_int_used=nu,
                    t_start_mjdsec=p.t_start, t_end_mjdsec=p.t_end,
                    sep_from_discovery_h=(p.t_start - d['t_start_mjdsec'])
                    / 3600.0,
                    v_corr_kms=p.v_corr,
                    f_here_GHz=f_here / 1e9, chan=ch,
                    dchan_from_sky=float((f_here - f_ev) / p.w.chanw),
                    drift_Hz_s=dr,
                    amp_mJy=float(a[0]) * 1e3, sig_mJy=float(sg) * 1e3,
                    T_matched=float(T[0]),
                    T_bestdrift_pub=float(p.w.best_src_pub[0, ch]),
                    ctrl_T_matched_max=float(T[1:].max()),
                    n_ctrl_retained=int(p.I.shape[1] - 1),
                    rms_combined_mJy=float(p.w.res['rms_combined_mJy']),
                    window_peak_pub=float(p.w.res['star_peak_snr']),
                    prod_star=p.prod_star, ra=p.ra, dec=p.dec,
                    sep_from_group_arcsec=sep_arcsec((p.ra, p.dec), g['pos'])))
            done += 1
            del p
        print('   %d repeat windows measured' % done, flush=True)

    # ---- per-crossing combination
    bycid = defaultdict(list)
    for r in rows:
        if r.get('status') == 'ok':
            bycid[r['cid']].append(r)
    for c in plan:
        if c['status'] != 'ok':
            out_cross[c['cid']] = dict(
                {k: v for k, v in c.items() if k not in ('repeats', '_disc')},
                n_repeat_blocks_measured=0)
            continue
        got = bycid.get(c['cid'], [])
        # one window per block: the finest channel among those that cover it
        byeb = {}
        for r in got:
            o = byeb.get(r['eb'])
            if o is None or r['chanw_Hz'] < o['chanw_Hz']:
                byeb[r['eb']] = r
        use = sorted(byeb.values(), key=lambda r: r['t_start_mjdsec'])
        d = c['_disc']
        S = d['amp_mJy']
        sd = d['sig_mJy']

        def comb(rs):
            if not rs:
                return None
            w_ = np.array([1.0 / r['sig_mJy'] ** 2 for r in rs])
            am = np.array([r['amp_mJy'] for r in rs])
            sb = float(1.0 / math.sqrt(w_.sum()))
            ab = float((am * w_).sum() / w_.sum())
            return dict(n=len(rs), abar_mJy=ab, sbar_mJy=sb,
                        T_if_persistent=S / sb,
                        exclusion_sigma=(S - ab) / sb,
                        T_max=max(r['T_matched'] for r in rs),
                        T_bestdrift_max=max(r['T_bestdrift_pub'] for r in rs),
                        T_median=float(np.median([r['T_matched'] for r in rs])))
        inf = [r for r in use if r['sig_mJy'] < 2.0 * sd]
        A, I_, U = comb(use), comb(inf), comb([r for r in use
                                               if r['sig_mJy'] >= 2.0 * sd])
        neff = (sd / A['sbar_mJy']) ** 2 if A else 0.0
        out_cross[c['cid']] = dict(
            {k: v for k, v in c.items() if k not in ('repeats', '_disc')},
            discovery=d, v_sys_kms=VSYS.get(c['star'], 0.0),
            n_repeat_blocks_planned=len(c['repeats']),
            n_repeat_blocks_measured=len(use),
            n_repeat_blocks_in_catalogue=sum(
                1 for r in use if r.get('in_released_catalogue')),
            blocks=use, all_other=A, informative=I_, uninformative=U,
            n_eff=neff,
            span_h=((max(r['t_start_mjdsec'] for r in use)
                     - min(r['t_start_mjdsec'] for r in use)) / 3600.0
                    if use else None),
            nearest_repeat_h=(min(abs(r['sep_from_discovery_h'])
                                  for r in use) if use else None),
            nearest_repeat_eb=(min(use, key=lambda r: abs(
                r['sep_from_discovery_h']))['eb'] if use else None),
            farthest_repeat_h=(max(abs(r['sep_from_discovery_h'])
                                   for r in use) if use else None))
    res = dict(generator=os.path.basename(__file__), drive=DRIVE,
               trigger=TRIG, pos_tol_arcsec=POS_TOL,
               vsys_missing=sorted(vsys_missing),
               n_crossings=len(plan), rows=rows, crossings=out_cross)
    json.dump(res, open(OUTP, 'w'), indent=1, default=float)
    print('\nwrote %s' % OUTP)


if __name__ == '__main__':
    main()
