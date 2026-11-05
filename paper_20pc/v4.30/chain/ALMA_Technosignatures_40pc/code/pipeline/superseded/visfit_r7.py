#!/usr/bin/env python3
r"""Round 7: the round-6 drift-following visibility fit, applied to INJECTED
carriers instead of to real threshold crossings.

THE ESTIMATOR IS THE ROUND-6 ONE, UNCHANGED.  For each event, and for each
integration t: take the channel the carrier occupies at time t following the
recovered linear drift nu(t) = nu0 + nudot (t - t0); subtract a local
continuum estimated from reference channels outside a guard band in the same
integration; phase-rotate to the position being tested; average over
integrations and baselines.  Controls are the same fit at eight positions on
the annulus the image-plane screen uses and at four off-event frequencies in
the same window.

FOUR DIFFERENCES FROM visfit_r6.py, every one a no-op unless the new field or
environment variable is supplied, so that the default behaviour is byte-for-byte
the round-6 estimator:

  1. The position tested is (l0_arcsec, m0_arcsec) from the event, defaulting
     to (0, 0).  visfit_r6.py hard-codes the phase centre, which is right for
     a survey crossing only when the star sits at the phase centre.  It does
     not always: of the blocks used here the stellar offset runs from 0.011"
     to 4.98", and 4.98" is several synthesised beams for a 12 m array at
     230 GHz, so a fit at the phase centre would return nothing for a source
     at the star.  The injector deposits the tone at the star, so the fit must
     be evaluated there.  The eight annulus controls are placed around that
     same position, as the image-plane screen places them around the star.

  2. VF_TREF selects the epoch the drift track is referenced to.  'median',
     the default, is what visfit_r6.py does: nu(t) = nu0 + nudot (t - median(t)).
     ★ THAT IS WRONG, and the error is not small.
     seti_drift_search_generic.py de-drifts with `dt = times - times[0]`, so the
     frequency it reports is the frequency at the FIRST retained integration,
     not at the middle of the observation.  The two differ by
     nudot x T_span / 2.  The codebase's own closure-phase vetting already gets
     this right -- it is called with `t_ref=float(times[0])`.  Measured on a
     Band 8 ACA window of 2048 x 0.488 MHz channels and 2118 s span, at an
     amplitude where every tone triggers at SNR 37-40, the recovered flux falls
     from 0.473 of the injected value at an offset of 0.06 channels to zero
     beyond 2.8 channels, monotonically.  VF_TREF='first' uses min(TIME).
     Both are computed for every pass of the round-7 campaign so that the
     completeness of the estimator AS COMMITTED and of the corrected estimator
     are both reported, and so that it is stated which one dispositioned the
     candidate list.

  3. Optional `avoid_GHz` / `avoid_tol_GHz` on the event move an off-event
     control frequency off any carrier.  In the survey a window holds at most
     one carrier, so the four control frequencies at fixed fractions of the
     window are event-free by construction.  In an injection pass carrying
     twelve to twenty-four tones they are not: they land on other tones and
     return Re/sigma of 30-52 where they should return zero, so the star fails
     criterion 3 for a reason that cannot occur in the data.  With the field
     present, a contaminated control frequency is moved to the nearest clean
     one inside the same window, preserving both the count and the intent; if
     none exists it is dropped rather than used.

  4. Events may be many per measurement set (one per injected tone), so UVW
     and TIME are read once per (ms, ddid) rather than once per event, and the
     per-event console line is suppressed unless VF_VERBOSE is set.  Neither
     changes a fitted number.

With VF_TREF unset, no l0_arcsec/m0_arcsec and no avoid_GHz, this script
returns exactly what visfit_r6.py returns; that equivalence is checked by
vf_equiv_check.py.

Environment: VF_EVENTS, VF_DRIFT, VF_OUT, optional VF_TREF, VF_VERBOSE.
"""
import json
import math
import os
import sys

import numpy as np

OUT = os.environ['VF_OUT']
EVENTS = json.load(open(os.environ['VF_EVENTS']))
DRIFT = json.load(open(os.environ['VF_DRIFT']))
VERBOSE = bool(os.environ.get('VF_VERBOSE'))
TREF = os.environ.get('VF_TREF', 'median')
if TREF not in ('median', 'first', 'explicit'):
    raise SystemExit('VF_TREF must be median, first or explicit, not %r' % TREF)

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


_GEOM = {}


def geometry(ms, ddid):
    """UVW and TIME of one window, read once per measurement set."""
    key = (ms, ddid)
    if key not in _GEOM:
        from casatools import table
        tb = table()
        tb.open(ms)
        sub = tb.query('DATA_DESC_ID==%d' % ddid)
        try:
            if sub.nrows() == 0:
                _GEOM[key] = None
            else:
                _GEOM[key] = (sub.getcol('UVW'), sub.getcol('TIME'))
        finally:
            sub.close()
            tb.close()
    return _GEOM[key]


def load_slice(ms, ddid, c0, c1):
    """UVW, TIME and a channel slice [c0, c1) of one spectral window.

    getcol('DATA') would read every channel before any slicing, which for a
    3840-channel window and 4x10^5 rows is both slow and large; getcolslice
    reads only the block asked for.
    """
    from casatools import table
    geo = geometry(ms, ddid)
    if geo is None:
        return None
    uvw, tim = geo
    tb = table()
    tb.open(ms)
    sub = tb.query('DATA_DESC_ID==%d' % ddid)
    try:
        if sub.nrows() == 0:
            return None
        dat = sub.getcolslice('DATA', [0, c0], [-1, c1 - 1], [1, 1])
        flg = sub.getcolslice('FLAG', [0, c0], [-1, c1 - 1], [1, 1])
    finally:
        sub.close()
        tb.close()
    dat = np.nanmean(np.where(flg, np.nan, dat), axis=0)   # (nch, nrow)
    ok = ~np.all(flg, axis=0)
    return uvw, tim, dat, ok


def fit_slice(uvw, tim, dat, ok, cf_slice, c0, nu0, nudot, dnu, l_off, m_off,
              guard, t_ref=None):
    """Amplitude at (l, m) on the drift track, local continuum removed."""
    nch, nrow = dat.shape
    # The epoch nu0 is referenced to. See VF_TREF in the module docstring.
    # 'median' is what visfit_r6.py does and is off by nudot x T_span / 2.
    # 'first' is min(TIME) of the rows loaded here -- still not exactly right,
    # because the search de-drifts to the first integration it RETAINS after
    # flagging, and the fit loads rows the extraction discarded; that residual
    # reaches 6.5 channels on one block in four (EPOCH_DECIDED.md).
    # 'explicit' takes the extraction's own first retained integration, which
    # is the epoch the search's reported frequency actually refers to.
    if TREF == 'median':
        t0 = float(np.median(tim))
    elif TREF == 'explicit' and t_ref is not None:
        t0 = float(t_ref)
    else:
        t0 = float(np.min(tim))
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
    l0 = float(ev.get('l0_arcsec', 0.0))
    m0 = float(ev.get('m0_arcsec', 0.0))
    nu0 = ev['freq_GHz'] * 1e9
    ddid, cf = spw_for(ms, nu0)
    if ddid is None:
        results[key] = dict(status='frequency not in any window', event=ev)
        continue
    dnu = float(np.median(np.diff(cf)))
    nch_all = cf.size
    ic = int(round((nu0 - cf[0]) / dnu))

    def window_for(nu_c, nudot=nudot, cf=cf, nch_all=nch_all, dnu=dnu):
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
    t_ref = ev.get('t_ref_mjds')
    star = fit_slice(uvw, tim, dat, ok, cfs, c0, nu0, nudot, dnu, l0, m0,
                     guard, t_ref)
    if star is None:
        results[key] = dict(status='fit failed', event=ev)
        continue
    pos = []
    for dl, dm in control_offsets(ev['theta_pb']):
        c = fit_slice(uvw, tim, dat, ok, cfs, c0, nu0, nudot, dnu,
                      l0 + dl, m0 + dm, guard, t_ref)
        if c:
            pos.append(c)
    # Off-event control frequencies. `avoid` holds every frequency in this
    # window known to carry a signal; in the survey that is just the event, in
    # an injection pass it is every tone of the pass. A control frequency is
    # only a control if nothing is there.
    avoid = [float(x) * 1e9 for x in (ev.get('avoid_GHz') or [])]
    avoid_tol = float(ev.get('avoid_tol_GHz', 0.0)) * 1e9
    span_hz = float(cf.max() - cf.min())

    def clean(nu_c):
        if abs(nu_c - nu0) < 0.05 * span_hz:
            return False
        return not any(abs(nu_c - a) < avoid_tol for a in avoid)

    def relocate(nu_c):
        """The nearest frequency inside this window carrying nothing. Stepping
        by the avoidance tolerance keeps the search finite and keeps the
        relocated control as close as possible to the nominal fraction of the
        window, so the control set stays four strong and stays where the
        round-6 estimator put it."""
        if clean(nu_c):
            return nu_c
        if avoid_tol <= 0:
            return None
        lo, hi = cf.min() + 0.02 * span_hz, cf.max() - 0.02 * span_hz
        for j in range(1, int(span_hz / avoid_tol) + 2):
            for cand in (nu_c + j * avoid_tol, nu_c - j * avoid_tol):
                if lo <= cand <= hi and clean(cand):
                    return cand
        return None

    frq = []
    for k in range(1, NCTRLFREQ + 1):
        nu_c = cf.min() + span_hz * k / (NCTRLFREQ + 1.0)
        nu_c = relocate(nu_c)
        if nu_c is None:
            continue
        d0, d1, g2 = window_for(nu_c)
        g2d = load_slice(ms, ddid, d0, d1)
        if not g2d:
            continue
        u2, t2, a2, o2 = g2d
        c = fit_slice(u2, t2, a2, o2, cf[d0:d1], d0, nu_c, nudot, dnu,
                      l0, m0, g2, t_ref)
        if c:
            frq.append(dict(freq_GHz=nu_c / 1e9, **c))
    results[key] = dict(status='ok', event=ev, drift_Hz_s=nudot,
                        t_ref_used=('median' if TREF == 'median' else
                                    'explicit' if (TREF == 'explicit'
                                                   and t_ref is not None)
                                    else 'first'), star=star,
                        pos_controls=pos, freq_controls=frq,
                        ctrl_pos_max=max([c['snr_re'] for c in pos] or [None]),
                        ctrl_freq_max=max([c['snr_re'] for c in frq] or [None]))
    if VERBOSE:
        print('%-46s Re=%+.4g+-%.2g  Re/sig=%+7.2f  Im/sig=%+6.2f  '
              'posctrl %.2f  freqctrl %.2f  n=%d'
              % (key, star['re'], star['sig_re'], star['snr_re'] or 0,
                 star['snr_im'] or 0,
                 results[key]['ctrl_pos_max'] if results[key]['ctrl_pos_max']
                 is not None else float('nan'),
                 results[key]['ctrl_freq_max'] if results[key]['ctrl_freq_max']
                 is not None else float('nan'),
                 star['n_vis']))
        sys.stdout.flush()

json.dump(results, open(OUT, 'w'), indent=1)
print('written %s (%d events)' % (OUT, len(results)))
