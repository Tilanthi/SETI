#!/usr/bin/env python3
r"""Round 7: the drift-following visibility localisation fit, with the three
defects the phase-centre audit found in `visfit_r6.py` repaired.

THE ESTIMATOR IS STILL THE ROUND-6 ONE.  For each event, and for each
integration t: take the channel the carrier occupies at time t following the
recovered linear drift nu(t) = nu0 + nudot (t - t0); subtract a local
continuum estimated from reference channels outside a guard band in the same
integration; phase-rotate to the position being tested; average over
integrations and baselines.  Controls are the same fit at eight positions on
an annulus around the tested position and at four off-event frequencies in
the same window.  The localisation criterion is NOT applied here; this script
only measures.

THREE REPAIRS, each of which softened non-detections in the round-6 run
(`/workspace/SETI/referee_r7/OFFSET_AUDIT.md`):

  1. THE FIT POSITION.  `visfit_r6.py` fitted at (0, 0), the measurement
     set's phase centre, which is the star only when the star sits at the
     phase centre.  For 9 of the 44 round-6 fits it did not: the star lay
     0.85-1.6 synthesised beams away and a compact carrier at the star would
     have been attenuated to 0-13 per cent.  Here the stellar direction
     cosines are computed FROM THE MEASUREMENT SET, using `star_lm()`
     verbatim from `seti_extract_generic.py` (Gaia DR3 position at epoch
     2016, parallax and proper motion, `apply_space_motion()` to the median
     epoch of the rows actually fitted, against the selected field's
     `FIELD::PHASE_DIR`).  Nothing is reconstructed and no convention is
     invented.  `VF_POS=event` restores the round-6/round-7 behaviour of
     taking `l0_arcsec`/`m0_arcsec` from the event record.

  2. FIELD SELECTION.  `visfit_r6.load_slice` selected rows on
     `DATA_DESC_ID` alone.  In the legacy `scriptForCalibration` replay path
     `{EB}_target.ms` still carries the calibrators, and 8 of the 12
     surviving target measurement sets are multi-field with science-row
     fractions 0.31-1.00; a real source is then diluted by the target-row
     fraction f while the noise is estimated from every row, so Re/sigma is
     degraded by sqrt(f).  Here science rows are identified by
     `STATE::OBS_MODE` containing `OBSERVE_TARGET`, and among the science
     fields the one nearest the star is selected -- the same rule
     `seti_extract_generic._select_best_field_ms()` applies, so the fit sees
     the same pointing the image-plane screen searched.  For mosaics a
     secondary all-science-fields fit is also reported, each field
     phase-rotated to the star through its own phase centre; it is a
     diagnostic, not the criterion.

  4. THE REFERENCE EPOCH.  `visfit_r6.py` sets t0 = median(TIME) while the
     search that produced the crossing frequency de-drifts with
     `times - times[0]`, so the fit looks at a frequency displaced by
     nudot * T_span / 2.  In channels that is large for a fast drift, and an
     unresolved carrier occupies about 2.8 channels, so the committed
     convention could miss a carrier entirely while leaving a broad CO line
     -- which is what every positive control is -- unaffected.  This script
     evaluates EVERY fit under BOTH conventions and CHOOSES NEITHER, records
     the elapsed max(TIME)-min(TIME) of the rows actually fitted, and adds a
     scan of Re/sigma in whole channels about the committed convention wide
     enough to contain the other, so the profile itself shows where the
     signal is.  The top-level `star`/`pos_controls`/`freq_controls` keep the
     committed convention, so the schema and the ledger are unchanged; the
     alternative lives under `epoch`.

  3. THE CONTROL ANNULUS.  `visfit_r6.control_offsets()` placed the eight
     controls at 0.14-0.78 x `ev['theta_pb']` with no synthesised-beam
     floor, and every `theta_pb` in the event records is the pre-repair 12 m
     value -- so the innermost control of all 30 ACA fits sat 0.53-1.56
     synthesised beams from the star, inside its own main lobe.  That is the
     same defect the survey already found, fixed and wrote up in the image
     plane.  Here the survey's own repaired rule is applied: dish diameter
     from `ANTENNA::DISH_DIAMETER`, B_max from `UVW`, theta_PB = 1.22 lam/D,
     theta_syn = 1.22 lam/B_max, annulus from max(0.14 theta_PB,
     2.0 theta_syn) to 0.78 theta_PB, drawn with the extractor's own
     `sqrt(uniform(lo^2, hi^2))` / `uniform(0, 2pi)` in that order from
     `default_rng(20260825)`.

EQUIVALENCE.  With VF_LEGACY=1 this script takes the position from the event,
selects on DATA_DESC_ID alone and builds the annulus from `ev['theta_pb']`
with no floor, and then returns exactly what `visfit_r7.py` returns.  (The
radius draw is algebraically identical: `sqrt(U(a^2, b^2)) * theta` and
`sqrt(U((a theta)^2, (b theta)^2))` consume the same uniform deviate and give
the same number.)  `vf_equiv_r7x.py` checks that leaf by leaf.

Environment: VF_EVENTS, VF_DRIFT, VF_OUT; optional VF_LEGACY, VF_POS,
VF_VERBOSE.
"""
import glob
import json
import math
import os
import sys

import numpy as np

OUT = os.environ['VF_OUT']
EVENTS = json.load(open(os.environ['VF_EVENTS']))
DRIFT = json.load(open(os.environ['VF_DRIFT']))
VERBOSE = bool(os.environ.get('VF_VERBOSE'))
LEGACY = os.environ.get('VF_LEGACY') == '1'
POS_SRC = os.environ.get('VF_POS', 'event' if LEGACY else 'ms')

R_IN, R_OUT, NCTRL, SEED = 0.14, 0.78, 8, 20260825
NCTRLFREQ = 4
ANN_SYN_FACTOR = 2.0            # pre-specified 2026-09-23, from the extractor
ARCSEC = math.pi / 180.0 / 3600.0
C = 299792458.0


# --------------------------------------------------------------- geometry
def primary_beam_arcsec(freq_hz, dish_m):
    return math.degrees(1.22 * (C / freq_hz) / dish_m) * 3600.0


def synth_beam_arcsec(freq_hz, bmax_m):
    if not bmax_m:
        return 0.0
    return math.degrees(1.22 * (C / freq_hz) / bmax_m) * 3600.0


def control_offsets(ann_lo, ann_hi, n=NCTRL, seed=SEED, scale=None):
    """The extractor's annulus draw, in its own order: radii then angles.

    With `scale` the bounds are read as fractions of it, which is the
    round-6 spelling `sqrt(U(0.14^2, 0.78^2)) * theta_pb` bit for bit.  That
    is algebraically the same as drawing between the scaled radii -- the
    same uniform deviate is consumed -- but the two differ in the last two
    bits of the double, enough to fail an exact leaf-by-leaf check.
    """
    rng = np.random.default_rng(seed)
    if scale is not None:      # ann_lo/ann_hi are then FRACTIONS of scale
        rr = np.sqrt(rng.uniform(ann_lo ** 2, ann_hi ** 2, n)) * scale
    else:
        rr = np.sqrt(rng.uniform(ann_lo ** 2, ann_hi ** 2, n))
    th = rng.uniform(0, 2 * np.pi, n)
    return [(float(rr[i] * np.cos(th[i])), float(rr[i] * np.sin(th[i])))
            for i in range(n)]


def star_lm(phase_ra, phase_dec, mjd_sec, star):
    """Direction cosines of the star relative to a phase centre, propagated
    to the observation epoch.  Verbatim from seti_extract_generic.star_lm()."""
    from astropy.coordinates import SkyCoord, Distance
    from astropy.time import Time
    import astropy.units as u
    epoch_obs = Time(mjd_sec / 86400.0, format='mjd')
    c0 = SkyCoord(ra=star['ra_deg'] * u.deg, dec=star['dec_deg'] * u.deg,
                  pm_ra_cosdec=star['pmra'] * u.mas / u.yr,
                  pm_dec=star['pmdec'] * u.mas / u.yr,
                  distance=Distance(parallax=star['parallax'] * u.mas),
                  radial_velocity=star.get('rv_kms', 0.0) * u.km / u.s,
                  obstime=Time(star.get('epoch', 2016.0), format='jyear'))
    c = c0.apply_space_motion(epoch_obs)
    a, d = c.ra.rad, c.dec.rad
    a0, d0 = phase_ra, phase_dec
    l = np.cos(d) * np.sin(a - a0)
    m = np.sin(d) * np.cos(d0) - np.cos(d) * np.sin(d0) * np.cos(a - a0)
    return float(l), float(m)


def search_epoch(ms, eb, nu0):
    """The search's own reference epoch and span for the window holding nu0.

    `seti_drift_search_generic.py` de-drifts with `dt = times - times[0]`, so
    the crossing frequency it reports means 'the frequency at the search's
    first retained integration'.  Its `*_srcspec.npz` stores that `times`
    array and its `*_result.json` stores `time_span_s`.  Returns None when
    the products did not survive (round 6 deleted many of them)."""
    try:
        prod = os.path.join(os.path.dirname(ms))
        best = None
        for p in sorted(glob.glob(os.path.join(prod, eb + '_spw*_srcspec.npz'))):
            try:
                z = np.load(p, allow_pickle=True)
                fr = np.asarray(z['freqs'], float)
                if fr.size < 2 or not (fr.min() <= nu0 <= fr.max()):
                    continue
                tt = np.asarray(z['times'], float)
                if tt.size < 2:
                    continue
                cand = dict(file=os.path.basename(p), t0_s=float(tt.min()),
                            t_span_s=float(tt.max() - tt.min()),
                            n_int=int(tt.size))
                rj = p.replace('_srcspec.npz', '_result.json')
                if os.path.exists(rj):
                    try:
                        cand['result_time_span_s'] = float(
                            json.load(open(rj)).get('time_span_s'))
                    except Exception:
                        pass
                if best is None or cand['n_int'] > best['n_int']:
                    best = cand
            except Exception:
                continue
        return best
    except Exception:
        return None


# ------------------------------------------------------------- MS metadata
_META = {}


def ms_fields(ms):
    """Science fields of a measurement set and their phase centres.

    Science rows are those whose STATE carries an OBSERVE_TARGET intent,
    which is how ALMA marks them; if the STATE subtable is unusable every
    field is treated as science and the nearest-to-star rule alone decides.
    """
    if ms in _META:
        return _META[ms]
    from casatools import table
    tb = table()
    tb.open(ms + '/FIELD')
    pdir = tb.getcol('PHASE_DIR')[:, 0, :]       # (2, nfield)
    try:
        fname = list(tb.getcol('NAME'))
    except Exception:
        fname = ['?'] * pdir.shape[1]
    tb.close()
    sci_states = None
    try:
        tb.open(ms + '/STATE')
        if tb.nrows():
            modes = tb.getcol('OBS_MODE')
            sci_states = set(int(i) for i, s in enumerate(modes)
                             if 'OBSERVE_TARGET' in str(s))
        tb.close()
    except Exception:
        sci_states = None
    tb.open(ms + '/ANTENNA')
    diam = tb.getcol('DISH_DIAMETER')
    tb.close()
    dish = float(np.median(diam)) if diam.size else 12.0
    if not (3.0 < dish < 30.0):
        dish = 12.0
    _META[ms] = dict(pdir=pdir, fname=fname, sci_states=sci_states, dish=dish)
    return _META[ms]


_ROWS = {}


def row_index(ms, ddid):
    """FIELD_ID, STATE_ID, UVW and TIME of one spectral window, once per MS."""
    key = (ms, ddid)
    if key in _ROWS:
        return _ROWS[key]
    from casatools import table
    tb = table()
    tb.open(ms)
    sub = tb.query('DATA_DESC_ID==%d' % ddid)
    try:
        if sub.nrows() == 0:
            _ROWS[key] = None
        else:
            _ROWS[key] = dict(fid=np.asarray(sub.getcol('FIELD_ID')),
                              sid=np.asarray(sub.getcol('STATE_ID')),
                              uvw=sub.getcol('UVW'), tim=sub.getcol('TIME'),
                              nrow=int(sub.nrows()))
    finally:
        sub.close()
        tb.close()
    return _ROWS[key]


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


# -------------------------------------------------------------- data slice
def load_slice(ms, ddid, c0, c1, sel=None):
    """UVW, TIME and a channel slice [c0, c1) of one window's selected rows.

    getcol('DATA') would read every channel before any slicing, which for a
    3840-channel window and 4x10^5 rows is both slow and large; getcolslice
    reads only the block asked for.
    """
    from casatools import table
    idx = row_index(ms, ddid)
    if idx is None:
        return None
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
    uvw, tim = idx['uvw'], idx['tim']
    if sel is not None:
        uvw, tim, dat, ok = uvw[:, sel], tim[sel], dat[:, sel], ok[:, sel]
    return uvw, tim, dat, ok


def prep_track(uvw, tim, dat, ok, cf_slice, nu0, nudot, dnu, guard,
               t0=None, dch=0):
    """Continuum-subtracted visibilities on the drift track.

    `t0` is the epoch the drift is referenced to.  `visfit_r6.py` used
    median(TIME); `seti_drift_search_generic.py`, which produced the crossing
    frequency, de-drifts with `dt = times - times[0]`, so the two differ by
    nudot * T_span / 2.  Both are evaluated here and neither is chosen.
    `dch` shifts the track by an integer number of channels, which is how the
    scan across the two conventions is built.
    """
    nch, nrow = dat.shape
    if t0 is None:
        t0 = float(np.median(tim))
    idx = np.rint((nu0 + nudot * (tim - t0) - cf_slice[0]) / dnu).astype(int)
    if dch:
        idx = idx + int(dch)
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
    w_ = uvw[1, rows][keep]                     # uvw[1] is v; name is legacy
    if v.size < 50:
        return None
    return v, u_, w_, rows, keep, int(guard)


def evaluate(track, nu0, l_off, m_off):
    """Phase-rotate to (l, m) in arcsec and average.  Separated from
    prep_track so that the eight control positions, which share the same
    continuum-subtracted visibilities, cost a phase rotation each instead of
    a fresh 96-channel median."""
    v, u_, w_, rows, keep, guard = track
    lo = np.asarray(l_off, float)
    mo = np.asarray(m_off, float)
    if lo.ndim:
        lo = lo[rows][keep]
        mo = mo[rows][keep]
    lam = C / nu0
    phase = 2 * np.pi * ((u_ / lam) * lo * ARCSEC + (w_ / lam) * mo * ARCSEC)
    vr = v * np.exp(1j * phase)
    n = vr.size
    re, im = float(vr.real.mean()), float(vr.imag.mean())
    sre = float(vr.real.std(ddof=1) / math.sqrt(n))
    sim = float(vr.imag.std(ddof=1) / math.sqrt(n))
    return dict(n_vis=int(n), re=re, im=im, sig_re=sre, sig_im=sim,
                snr_re=re / sre if sre else None,
                snr_im=im / sim if sim else None, guard_chan=guard)


def fit_slice(uvw, tim, dat, ok, cf_slice, nu0, nudot, dnu, l_off, m_off,
              guard, t0=None, dch=0):
    tr = prep_track(uvw, tim, dat, ok, cf_slice, nu0, nudot, dnu, guard,
                    t0=t0, dch=dch)
    if tr is None:
        return None
    return evaluate(tr, nu0, l_off, m_off)


# ------------------------------------------------------------------ driver
def run_event(ev, nudot):
    ms = ev['ms']
    nu0 = ev['freq_GHz'] * 1e9
    ddid, cf = spw_for(ms, nu0)
    if ddid is None:
        return dict(status='frequency not in any window', event=ev)
    idx = row_index(ms, ddid)
    if idx is None:
        return dict(status='no rows', event=ev)
    dnu = float(np.median(np.diff(cf)))
    nch_all = cf.size
    fmed = float(np.median(cf))
    meta = ms_fields(ms)
    nrow_all = idx['nrow']

    # ---- (2) field selection -------------------------------------------
    star = ev.get('star')
    diag = dict(n_rows_window=nrow_all, legacy=LEGACY, pos_source=POS_SRC)
    if LEGACY:
        sel = None
        sel_fids = sorted(set(int(x) for x in np.unique(idx['fid'])))
        sci_fids = sel_fids
        diag.update(field_selection='legacy: none')
    else:
        fids_all = np.unique(idx['fid'])
        if meta['sci_states']:
            ssel = np.isin(idx['sid'], list(meta['sci_states']))
            sci_fids = sorted(set(int(x) for x in np.unique(idx['fid'][ssel])))
            n_sci = int(ssel.sum())
            intent = 'STATE::OBS_MODE OBSERVE_TARGET'
        else:
            ssel = np.ones(nrow_all, bool)
            sci_fids = sorted(int(x) for x in fids_all)
            n_sci = nrow_all
            intent = 'no usable STATE subtable; all fields treated as science'
        if not sci_fids:
            return dict(status='no science rows', event=ev)
        # among the science fields, the one nearest the star -- the rule
        # seti_extract_generic._select_best_field_ms() applies.
        offs = {}
        for fid in sci_fids:
            rsel = (idx['fid'] == fid) & ssel
            if not rsel.any():
                continue
            mjd = float(np.median(idx['tim'][rsel]))
            l, m = star_lm(float(meta['pdir'][0, fid]),
                           float(meta['pdir'][1, fid]), mjd, star)
            offs[fid] = (l / ARCSEC, m / ARCSEC,
                         math.hypot(l, m) / ARCSEC, int(rsel.sum()))
        if not offs:
            return dict(status='no science rows', event=ev)
        best = min(offs, key=lambda f: offs[f][2])
        sel = (idx['fid'] == best) & ssel
        sel_fids = [best]
        diag.update(field_selection=intent, n_fields_in_window=len(fids_all),
                    science_fields=sci_fids, n_rows_science=n_sci,
                    science_row_fraction=n_sci / float(nrow_all),
                    selected_field=best, n_rows_selected=int(sel.sum()),
                    selected_row_fraction=int(sel.sum()) / float(nrow_all),
                    field_offsets_arcsec={str(k): dict(
                        l=v[0], m=v[1], sep=v[2], nrow=v[3])
                        for k, v in offs.items()},
                    field_names=[meta['fname'][f] if f < len(meta['fname'])
                                 else '?' for f in sci_fids])

    # ---- (1) the fitted position ---------------------------------------
    if POS_SRC == 'event':
        l0 = float(ev.get('l0_arcsec', 0.0))
        m0 = float(ev.get('m0_arcsec', 0.0))
        diag.update(l0_arcsec=l0, m0_arcsec=m0, offset_arcsec=math.hypot(l0, m0),
                    offset_source='event record')
    else:
        fid = sel_fids[0]
        mjd = float(np.median(idx['tim'][sel]))
        l, m = star_lm(float(meta['pdir'][0, fid]),
                       float(meta['pdir'][1, fid]), mjd, star)
        l0, m0 = l / ARCSEC, m / ARCSEC
        diag.update(l0_arcsec=l0, m0_arcsec=m0,
                    offset_arcsec=math.hypot(l0, m0),
                    offset_source='measured: Gaia + FIELD::PHASE_DIR of the '
                                  'fitted field, this MS',
                    phase_centre_deg=[math.degrees(float(meta['pdir'][0, fid])) % 360.0,
                                      math.degrees(float(meta['pdir'][1, fid]))],
                    mjd_fit=mjd / 86400.0)

    # ---- (3) the control annulus ---------------------------------------
    if LEGACY:
        th_pb = float(ev['theta_pb'])
        ann_lo, ann_hi = R_IN * th_pb, R_OUT * th_pb
        ann_scale = th_pb
        diag.update(theta_pb_arcsec=th_pb, theta_syn_arcsec=None,
                    dish_m=None, bmax_m=None, ann_lo_arcsec=ann_lo,
                    ann_hi_arcsec=ann_hi, annulus_source='legacy: event theta_pb')
    else:
        uvw_sel = idx['uvw'][:, sel]
        bmax = float(np.max(np.hypot(uvw_sel[0], uvw_sel[1]))) if uvw_sel.size else 0.0
        dish = meta['dish']
        th_pb = primary_beam_arcsec(fmed, dish)
        th_syn = synth_beam_arcsec(fmed, bmax)
        ann_lo = max(R_IN * th_pb, ANN_SYN_FACTOR * th_syn)
        ann_hi = R_OUT * th_pb
        ann_scale = None
        diag.update(theta_pb_arcsec=th_pb, theta_syn_arcsec=th_syn,
                    dish_m=dish, bmax_m=bmax, ann_lo_arcsec=ann_lo,
                    ann_hi_arcsec=ann_hi, ann_syn_factor=ANN_SYN_FACTOR,
                    ann_lo_in_syn_beams=(ann_lo / th_syn) if th_syn else None,
                    theta_pb_legacy_arcsec=float(ev.get('theta_pb', 0.0)),
                    annulus_source='measured: ANTENNA::DISH_DIAMETER + UVW, '
                                   'max(0.14 th_PB, 2.0 th_syn)')
        if ann_lo >= 0.9 * ann_hi:
            diag['annulus_degenerate'] = True

    # ---- the fit --------------------------------------------------------
    def window_for(nu_c):
        centre = int(round((nu_c - cf[0]) / dnu))
        span = abs(nudot) * 3600.0 / abs(dnu)      # generous track allowance
        g = max(4, int(round(span)) + 2)
        half = int(min(nch_all // 2, g + 120))
        return max(0, centre - half), min(nch_all, centre + half + 1), g

    c0, c1, guard = window_for(nu0)
    got = load_slice(ms, ddid, c0, c1, sel)
    if got is None:
        return dict(status='no rows', event=ev)
    uvw, tim, dat, ok = got
    cfs = cf[c0:c1]
    ctrl_args = ((R_IN, R_OUT) if ann_scale is not None else (ann_lo, ann_hi))
    ctrl_off = control_offsets(*ctrl_args, scale=ann_scale)

    # ---- (4) the reference epoch ----------------------------------------
    # visfit_r6.py references the drift track to median(TIME).  The search
    # that produced the crossing frequency de-drifts with times - times[0],
    # and the codebase's own closure-phase vetting uses t_ref = times[0].
    # The two differ by nudot * T_span / 2, which for a fast drift is many
    # channels -- enough to miss an unresolved carrier entirely while leaving
    # a broad CO line unaffected.  BOTH are evaluated and NEITHER is chosen.
    t_med = float(np.median(tim))
    t_min = float(np.min(tim))
    t_span = float(np.max(tim) - t_min)
    dch_first = (nudot * (t_med - t_min)) / dnu     # median -> first, in chan
    # The fit does not necessarily load the rows the SEARCH loaded: different
    # flagging, and now a field selection the search did not have.  So the
    # fit's own times[0] need not be the search's times[0], and the search's
    # is the one the reported crossing frequency is referenced to.  Where the
    # search product survives it stores its own `times`, so the residual can
    # be measured rather than assumed.
    srch = search_epoch(ms, ev['eb'], nu0)

    def one_convention(t0):
        tr = prep_track(uvw, tim, dat, ok, cfs, nu0, nudot, dnu, guard, t0=t0)
        if tr is None:
            return None
        st = evaluate(tr, nu0, l0, m0)
        pc = []
        for dl, dm in ctrl_off:
            c = evaluate(tr, nu0, l0 + dl, m0 + dm)
            if c:
                pc.append(dict(c, dl_arcsec=dl, dm_arcsec=dm,
                               r_arcsec=math.hypot(dl, dm)))
        return st, pc

    got_med = one_convention(t_med)
    if got_med is None:
        return dict(status='fit failed', event=ev, diag=diag)
    starfit, pos = got_med
    got_first = None if LEGACY else one_convention(t_min)
    # The THIRD epoch, and the correct one: the search de-drifts to the first
    # integration it RETAINS after flagging, which is not the measurement
    # set's first row.  The P90 worker measured a residual of up to 6.46
    # channels from that alone.  Where the extraction product survives it
    # stores that instant as times[0]; use it exactly.  Where it does not,
    # min(TIME) is used and the residual is bounded rather than assumed zero.
    t_exact = (srch or {}).get('t0_s')
    resid_ch = ((nudot * (t_min - t_exact) / dnu)
                if (t_exact is not None) else None)
    got_exact, exact_same = None, False
    if (not LEGACY) and t_exact is not None:
        if abs(resid_ch) < 0.02:
            exact_same = True            # identical to the first convention
        else:
            got_exact = one_convention(t_exact)

    # a scan in whole channels about the committed convention, wide enough to
    # contain the other one, so the profile itself shows where the signal is
    nmax = int(round(abs(dch_first))) + 6
    step = max(1, int(math.ceil((2 * nmax + 1) / 41.0)))
    scan = []
    for d in ([] if LEGACY else range(-nmax, nmax + 1, step)):
        tr = prep_track(uvw, tim, dat, ok, cfs, nu0, nudot, dnu, guard,
                        t0=t_med, dch=d)
        if tr is None:
            continue
        e = evaluate(tr, nu0, l0, m0)
        scan.append(dict(dch=d, re=e['re'], sig_re=e['sig_re'],
                         snr_re=e['snr_re'], snr_im=e['snr_im'],
                         n_vis=e['n_vis']))

    frq, frq_first = [], []
    for k in range(1, NCTRLFREQ + 1):
        nu_c = cf.min() + (cf.max() - cf.min()) * k / (NCTRLFREQ + 1.0)
        if abs(nu_c - nu0) < 0.05 * (cf.max() - cf.min()):
            continue
        d0, d1, g2 = window_for(nu_c)
        g2d = load_slice(ms, ddid, d0, d1, sel)
        if not g2d:
            continue
        u2, t2, a2, o2 = g2d
        pairs = [(float(np.median(t2)), frq)]
        if not LEGACY:
            pairs.append((float(np.min(t2)), frq_first))
        for t0, sink in pairs:
            c = fit_slice(u2, t2, a2, o2, cf[d0:d1], nu_c, nudot, dnu,
                          l0, m0, g2, t0=t0)
            if c:
                sink.append(dict(freq_GHz=nu_c / 1e9, **c))
    res = dict(status='ok', event=ev, drift_Hz_s=nudot, star=starfit,
               pos_controls=pos, freq_controls=frq,
               ctrl_pos_max=max([c['snr_re'] for c in pos] or [None]),
               ctrl_freq_max=max([c['snr_re'] for c in frq] or [None]))
    if not LEGACY:
        res['diag'] = diag
        res['epoch'] = dict(
            t_span_s=t_span, t_median_minus_first_s=t_med - t_min,
            chan_width_Hz=dnu, drift_Hz_s=nudot,
            offset_channels_median_to_first=dch_first,
            t_min_s=t_min, t_max_s=float(np.max(tim)),
            n_rows_fitted=int(tim.size),
            committed_convention='median(TIME)',
            search_convention='min(TIME)',
            search_product=srch,
            t_ref_source=('extraction product times[0]'
                          if t_exact is not None else
                          'min(TIME) of the fitted rows; extraction product '
                          'was deleted, residual unknown'),
            residual_channels_fit_first_to_extraction_first=resid_ch,
            residual_bound_channels=(None if t_exact is not None
                                     else abs(2.0 * dch_first)),
            exact=(dict(same_as='first', residual_channels=resid_ch)
                   if exact_same else
                   (dict(star=got_exact[0], pos_controls=got_exact[1],
                         residual_channels=resid_ch,
                         ctrl_pos_max=max([c['snr_re']
                                           for c in got_exact[1]] or [None]))
                    if got_exact else None)),
            offset_channels_fit_first_to_search_first=(
                (nudot * (t_min - srch['t0_s']) / dnu)
                if srch and srch.get('t0_s') is not None else None),
            scan_about_median=scan,
            first=(dict(star=got_first[0], pos_controls=got_first[1],
                        freq_controls=frq_first,
                        ctrl_pos_max=max([c['snr_re']
                                          for c in got_first[1]] or [None]),
                        ctrl_freq_max=max([c['snr_re']
                                           for c in frq_first] or [None]))
                   if got_first else None))

    # ---- secondary diagnostic: all science fields jointly ---------------
    if (not LEGACY) and len(diag.get('science_fields', [])) > 1:
        try:
            ssel = np.isin(idx['sid'], list(meta['sci_states'])) \
                if meta['sci_states'] else np.ones(nrow_all, bool)
            jsel = ssel & np.isin(idx['fid'], diag['science_fields'])
            lrow = np.zeros(nrow_all)
            mrow = np.zeros(nrow_all)
            for fid in diag['science_fields']:
                o = diag['field_offsets_arcsec'].get(str(fid))
                if o is None:
                    continue
                lrow[idx['fid'] == fid] = o['l']
                mrow[idx['fid'] == fid] = o['m']
            gotj = load_slice(ms, ddid, c0, c1, jsel)
            if gotj:
                u3, t3, a3, o3 = gotj
                sj = fit_slice(u3, t3, a3, o3, cfs, nu0, nudot, dnu,
                               lrow[jsel], mrow[jsel], guard)
                pj = []
                for dl, dm in control_offsets(*ctrl_args, scale=ann_scale):
                    c = fit_slice(u3, t3, a3, o3, cfs, nu0, nudot, dnu,
                                  lrow[jsel] + dl, mrow[jsel] + dm, guard)
                    if c:
                        pj.append(c)
                res['joint_fields'] = dict(
                    n_fields=len(diag['science_fields']),
                    n_rows=int(jsel.sum()), star=sj, pos_controls=pj,
                    ctrl_pos_max=max([c['snr_re'] for c in pj] or [None]))
        except Exception as exc:          # a diagnostic must never kill a fit
            res['joint_fields'] = dict(error=repr(exc))
    return res


results = {}
for ev in EVENTS:
    # The window edges are part of the key.  `tag|eb` alone collides when a
    # block carries two crossings on the same star -- three blocks here do --
    # and the second silently overwrote the first, losing the window.
    key = '%s|%s|%.3f-%.3f' % (ev['tag'], ev['eb'],
                               min(ev['flo_GHz'], ev['fhi_GHz']),
                               max(ev['flo_GHz'], ev['fhi_GHz']))
    if not os.path.isdir(ev['ms']):
        results[key] = dict(status='no measurement set')
        continue
    nudot = DRIFT.get(ev['eb'])
    if nudot is None:
        results[key] = dict(status='no recovered drift rate', event=ev)
        continue
    if (not LEGACY) and POS_SRC != 'event' and not ev.get('star'):
        results[key] = dict(status='no star parameters', event=ev)
        continue
    try:
        results[key] = run_event(ev, nudot)
    except Exception as exc:
        import traceback
        results[key] = dict(status='exception', event=ev, error=repr(exc),
                            traceback=traceback.format_exc())
    if VERBOSE:
        r = results[key]
        s = r.get('star') or {}
        print('%-46s %-10s Re/sig=%+7.2f Im/sig=%+6.2f posctrl %6.2f '
              'freqctrl %6.2f n=%d off=%.3f"'
              % (key, r.get('status'), s.get('snr_re') or float('nan'),
                 s.get('snr_im') or float('nan'),
                 (r.get('ctrl_pos_max') if r.get('ctrl_pos_max') is not None
                  else float('nan')),
                 (r.get('ctrl_freq_max') if r.get('ctrl_freq_max') is not None
                  else float('nan')),
                 s.get('n_vis') or 0,
                 (r.get('diag') or {}).get('offset_arcsec', float('nan'))))
        sys.stdout.flush()

json.dump(results, open(OUT, 'w'), indent=1)
print('written %s (%d events)' % (OUT, len(results)))
