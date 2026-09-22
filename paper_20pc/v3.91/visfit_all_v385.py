#!/usr/bin/env python3
r"""Drift-following, continuum-subtracted point-source fit at the stellar
position, for every stage-1 event.

Round-2 self-review, condition of acceptance M1. The uniform test of
Table 9 averages ONE channel with the continuum left in, which makes the
thirteen events comparable but loses a drifting carrier by roughly the
square root of the number of channels its track sweeps. One event,
CP-72 2713, had already been measured the better way and came out at
5.5 sigma against the uniform test's 2.3. Leaving the other twelve
measured only the weak way is not defensible, so this script applies the
better estimator to all of them.

THE ESTIMATOR
-------------
For each event, and for each integration t:

  * take the channel the carrier occupies at time t, following the
    recovered linear drift  nu(t) = nu0 + nudot (t - t0);
  * subtract a local continuum estimated from channels well away from the
    track in the same integration, so the star's own continuum is not read
    as a narrowband excess;
  * phase-rotate the visibilities to the stellar position.

Averaging over integrations and baselines then gives the amplitude of a
source AT the star: a real part that measures it, and an imaginary part
that a source at the phase centre must leave at zero.

Controls: the same fit at four off-event frequencies in the same window,
and at eight positions on the annulus the image-plane screen uses.

Runs on the processing host inside CASA's python. Writes one JSON.
"""
import json, math, os, sys

import numpy as np

OUT = '/data/SETI/vistest/visfit_all_v385.json'
EVENTS = json.load(open('/tmp/vistest_events_v385.json'))
DRIFT = json.load(open('/tmp/vistest_drift_v385.json'))

R_IN, R_OUT, NCTRL, SEED = 0.14, 0.78, 8, 20260825
NCTRLFREQ = 4
ARCSEC = math.pi / 180.0 / 3600.0
C = 299792458.0


def control_offsets(theta_pb, n=NCTRL, seed=SEED):
    rng = np.random.default_rng(seed)
    u = np.sqrt(rng.uniform(R_IN ** 2, R_OUT ** 2, n))
    ph = rng.uniform(0, 2 * np.pi, n)
    r = u * theta_pb
    return [(float(r[i] * np.cos(ph[i])), float(r[i] * np.sin(ph[i])))
            for i in range(n)]


def spw_for(ms, freq_hz):
    """(data_desc_id, channel frequencies) for the window holding freq."""
    from casatools import table
    tb = table()
    tb.open(ms + '/DATA_DESCRIPTION')
    dd2spw = tb.getcol('SPECTRAL_WINDOW_ID')
    tb.close()
    tb.open(ms + '/SPECTRAL_WINDOW')
    best = None
    for i in range(tb.nrows()):
        cf = np.asarray(tb.getcell('CHAN_FREQ', i), float)
        if cf.size < 8:
            continue
        if cf.min() <= freq_hz <= cf.max():
            if best is None or cf.size > best[1].size:
                best = (i, cf)
    tb.close()
    if best is None:
        return None, None
    spw, cf = best
    ddid = int(np.where(dd2spw == spw)[0][0]) if (dd2spw == spw).any() else spw
    return ddid, cf


def load_slice(ms, ddid, c0, c1):
    """UVW, TIME and a channel slice [c0, c1) of one spectral window.

    getcol('DATA') would read every channel before any slicing, which for a
    3840-channel window and 4x10^5 rows is both slow and large; getcolslice
    reads only the block asked for.
    """
    from casatools import table
    tb = table()
    tb.open(ms)
    sub = tb.query('DATA_DESC_ID==%d' % ddid)
    try:
        if sub.nrows() == 0:
            return None
        uvw = sub.getcol('UVW')
        tim = sub.getcol('TIME')
        dat = sub.getcolslice('DATA', [0, c0], [-1, c1 - 1], [1, 1])
        flg = sub.getcolslice('FLAG', [0, c0], [-1, c1 - 1], [1, 1])
    finally:
        sub.close()
        tb.close()
    dat = np.nanmean(np.where(flg, np.nan, dat), axis=0)   # (nch, nrow)
    ok = ~np.all(flg, axis=0)
    return uvw, tim, dat, ok


def fit_slice(uvw, tim, dat, ok, cf_slice, c0, nu0, nudot, dnu, l_off, m_off,
              guard):
    """Amplitude at (l, m) on the drift track, local continuum removed."""
    nch, nrow = dat.shape
    t0 = float(np.median(tim))
    idx = np.rint((nu0 + nudot * (tim - t0) - cf_slice[0]) / dnu).astype(int)
    good = (idx >= 0) & (idx < nch)
    if good.sum() < 50:
        return None
    rows = np.where(good)[0]
    ch = idx[rows]
    vals = dat[ch, rows]
    # Continuum: the per-row median of a FIXED set of reference channels at
    # offsets outside the guard band. Taking every channel in the slice
    # built an 11.9 GB array for the 15.3 kHz windows; a median needs a
    # sample, and 2 x NREF offsets either side is one.
    NREF = 48
    offs = np.concatenate([-(guard + 1 + np.arange(NREF)),
                           +(guard + 1 + np.arange(NREF))])
    ref = ch[None, :] + offs[:, None]                 # (2*NREF, nrows)
    valid = (ref >= 0) & (ref < nch)
    ref = np.clip(ref, 0, nch - 1)
    blk = dat[ref, rows[None, :]]
    blk = np.where(valid, blk, np.nan)
    cont = (np.nanmedian(blk.real, axis=0)
            + 1j * np.nanmedian(blk.imag, axis=0))
    v = vals - cont
    keep = np.isfinite(v) & ok[ch, rows]
    v = v[keep]
    u_ = uvw[0, rows][keep]
    w_ = uvw[1, rows][keep]
    if v.size < 50:
        return None
    lam = C / nu0
    phase = 2 * np.pi * ((u_ / lam) * l_off * ARCSEC + (w_ / lam) * m_off * ARCSEC)
    vr = v * np.exp(1j * phase)
    n = vr.size
    re, im = float(vr.real.mean()), float(vr.imag.mean())
    sre = float(vr.real.std(ddof=1) / math.sqrt(n))
    sim = float(vr.imag.std(ddof=1) / math.sqrt(n))
    return dict(n_vis=int(n), re=re, im=im, sig_re=sre, sig_im=sim,
                snr_re=re / sre if sre else None,
                snr_im=im / sim if sim else None, guard_chan=int(guard))


results = {}
for ev in EVENTS:
    key = '%s|%s' % (ev['tag'], ev['eb'])
    ms = ev['ms']
    nudot = DRIFT.get(ev['eb'])
    if not os.path.isdir(ms):
        results[key] = dict(status='no measurement set')
        continue
    if nudot is None:
        results[key] = dict(status='no recovered drift rate', event=ev)
        continue
    nu0 = ev['freq_GHz'] * 1e9
    ddid, cf = spw_for(ms, nu0)
    if ddid is None:
        results[key] = dict(status='frequency not in any window', event=ev)
        continue
    dnu = float(np.median(np.diff(cf)))
    nch_all = cf.size
    ic = int(round((nu0 - cf[0]) / dnu))

    def window_for(nu_c):
        """Channel slice holding the whole track plus continuum reference."""
        centre = int(round((nu_c - cf[0]) / dnu))
        span = abs(nudot) * 3600.0 / abs(dnu)      # generous track allowance
        g = max(4, int(round(span)) + 2)
        half = int(min(nch_all // 2, g + 120))
        return max(0, centre - half), min(nch_all, centre + half + 1), g

    c0, c1, guard = window_for(nu0)
    got = load_slice(ms, ddid, c0, c1)
    if got is None:
        results[key] = dict(status='no rows', event=ev)
        continue
    uvw, tim, dat, ok = got
    cfs = cf[c0:c1]
    star = fit_slice(uvw, tim, dat, ok, cfs, c0, nu0, nudot, dnu, 0.0, 0.0, guard)
    if star is None:
        results[key] = dict(status='fit failed', event=ev)
        continue
    pos = []
    for l, m_ in control_offsets(ev['theta_pb']):
        c = fit_slice(uvw, tim, dat, ok, cfs, c0, nu0, nudot, dnu, l, m_, guard)
        if c:
            pos.append(c)
    frq = []
    for k in range(1, NCTRLFREQ + 1):
        nu_c = cf.min() + (cf.max() - cf.min()) * k / (NCTRLFREQ + 1.0)
        if abs(nu_c - nu0) < 0.05 * (cf.max() - cf.min()):
            continue
        d0, d1, g2 = window_for(nu_c)
        g2d = load_slice(ms, ddid, d0, d1)
        if not g2d:
            continue
        u2, t2, a2, o2 = g2d
        c = fit_slice(u2, t2, a2, o2, cf[d0:d1], d0, nu_c, nudot, dnu,
                      0.0, 0.0, g2)
        if c:
            frq.append(dict(freq_GHz=nu_c / 1e9, **c))
    results[key] = dict(status='ok', event=ev, drift_Hz_s=nudot, star=star,
                        pos_controls=pos, freq_controls=frq,
                        ctrl_pos_max=max([c['snr_re'] for c in pos] or [None]),
                        ctrl_freq_max=max([c['snr_re'] for c in frq] or [None]))
    print('%-46s Re=%+.4g+-%.2g  Re/sig=%+7.2f  Im/sig=%+6.2f  '
          'posctrl %.2f  freqctrl %.2f  n=%d'
          % (key, star['re'], star['sig_re'], star['snr_re'] or 0,
             star['snr_im'] or 0,
             results[key]['ctrl_pos_max'] if results[key]['ctrl_pos_max'] is not None else float('nan'),
             results[key]['ctrl_freq_max'] if results[key]['ctrl_freq_max'] is not None else float('nan'),
             star['n_vis']))
    sys.stdout.flush()

json.dump(results, open(OUT, 'w'), indent=1)
print('written', OUT)
