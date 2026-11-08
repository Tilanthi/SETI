#!/usr/bin/env python3
"""
Generic version of the ALMA-SETI direct-DFT extraction step, generalised
from the TRAPPIST-1 pipeline for the 100-star survey: takes the target
star's astrometry via environment variables instead of a hardcoded T1
dict, and scales the search-ring/control-annulus geometry to the actual
ALMA primary beam at the observing frequency in use (TRAPPIST-1's fixed
2.5"-14" control annulus was tuned for Band 7's ~18" beam and would be
wrong -- either too cramped, or entirely outside the beam -- for other
bands, which this 100-star survey deliberately spans).

Evaluates the *dirty* channel-map intensity at a set of sky positions, for
every correlator integration and every frequency channel, by direct
Fourier transform of the visibilities:

     I(l,m) = Re[ SUM_k w_k V_k exp(2 pi i (u_k l + v_k m) nu / c) ] / SUM_k w_k

mathematically identical to reading the pixel value out of a
naturally-weighted dirty image but ~10^4 times cheaper, since only a
handful of pixels are ever evaluated.

Required environment variables:
  SETI_TARGET_DIR      e.g. /data/SETI/targets/tau_Cet
  SETI_STAR_NAME, SETI_STAR_RA, SETI_STAR_DEC (deg),
  SETI_STAR_PMRA, SETI_STAR_PMDEC (mas/yr), SETI_STAR_PARALLAX (mas)
Optional: SETI_STAR_PARALLAX_ERR, SETI_STAR_RV_KMS, SETI_MS, SETI_SFX

Usage: seti_extract_generic.py <EBID> [nproc]
"""
import os, sys, json, time
for _v in ('OMP_NUM_THREADS', 'OPENBLAS_NUM_THREADS', 'MKL_NUM_THREADS',
           'NUMEXPR_NUM_THREADS', 'VECLIB_MAXIMUM_THREADS'):
    os.environ[_v] = '1'
import numpy as np

EB = sys.argv[1]
NPROC = int(sys.argv[2]) if len(sys.argv) > 2 else 8
TARGET_DIR = os.environ['SETI_TARGET_DIR']
_MSOVERRIDE = os.environ.get('SETI_MS')
MS = _MSOVERRIDE or f'{TARGET_DIR}/products/{EB}_search.ms'
_SFX = os.environ.get('SETI_SFX', '') or ('_inj' if os.environ.get('SETI_INJECT') else '')
OUT = f'{TARGET_DIR}/products/{EB}{_SFX}_waterfall.npz'
os.environ.setdefault('CASASITECONFIG', '/home/fetch-agi/.casa/config.py')

C_M_S = 299792458.0
ARCSEC = np.pi / 180.0 / 3600.0
ALMA_DISH_M = 12.0

STAR_NAME = os.environ.get('SETI_STAR_NAME', 'target')
STAR = dict(
    ra_deg=float(os.environ['SETI_STAR_RA']),
    dec_deg=float(os.environ['SETI_STAR_DEC']),
    pmra=float(os.environ['SETI_STAR_PMRA']),
    pmdec=float(os.environ['SETI_STAR_PMDEC']),
    parallax=float(os.environ['SETI_STAR_PARALLAX']),
    parallax_err=float(os.environ.get('SETI_STAR_PARALLAX_ERR', 0.0)) or 1e-3,
    epoch=2016.0, rv_kms=float(os.environ.get('SETI_STAR_RV_KMS', 0.0)),
)


def primary_beam_arcsec(freq_hz):
    """FWHM of a single 12 m ALMA dish's primary beam at freq_hz (Eq. 1 of
    the reference paper: theta_PB = 1.22 lambda / D)."""
    wavelength_m = C_M_S / freq_hz
    return np.degrees(1.22 * wavelength_m / ALMA_DISH_M) * 3600.0


def probe_positions(pb_arcsec, seed=20260825):
    """Return (names, l_arcsec, m_arcsec, n_src). Ring radii and the
    control annulus are scaled to the actual primary beam FWHM rather than
    the Band-7-specific fixed values used for TRAPPIST-1, so this remains
    sensible across all ALMA bands."""
    rng = np.random.default_rng(seed)
    names, dl, dm = [], [], []
    names.append('star'); dl.append(0.0); dm.append(0.0)
    ring_max = 0.06 * pb_arcsec       # ~1.1" at Band 7 (pb~18"), scales elsewhere
    ring_step = ring_max / 7.0
    for r in np.arange(ring_step, ring_max + 1e-9, ring_step):
        n = max(6, min(24, int(round(2 * np.pi * r / ring_step))))
        for k in range(n):
            th = 2 * np.pi * k / n
            names.append(f'src_r{r:.3f}_{k}')
            dl.append(r * np.cos(th)); dm.append(r * np.sin(th))
    n_src = len(names)
    ann_lo, ann_hi = 0.14 * pb_arcsec, 0.78 * pb_arcsec   # stays inside the PB
    n_probe = 512
    rr = np.sqrt(rng.uniform(ann_lo**2, ann_hi**2, n_probe))
    th = rng.uniform(0, 2 * np.pi, n_probe)
    for k in range(n_probe):
        names.append(f'probe_{k}')
        dl.append(rr[k] * np.cos(th[k])); dm.append(rr[k] * np.sin(th[k]))
    return names, np.array(dl), np.array(dm), n_src


def star_lm(phase_ra, phase_dec, mjd_sec):
    """Direction cosines of the target star relative to the MS phase centre,
    propagated to the observation epoch via its Gaia proper motion."""
    from astropy.coordinates import SkyCoord, Distance
    from astropy.time import Time
    import astropy.units as u
    epoch_obs = Time(mjd_sec / 86400.0, format='mjd')
    c0 = SkyCoord(ra=STAR['ra_deg'] * u.deg, dec=STAR['dec_deg'] * u.deg,
                  pm_ra_cosdec=STAR['pmra'] * u.mas / u.yr,
                  pm_dec=STAR['pmdec'] * u.mas / u.yr,
                  distance=Distance(parallax=STAR['parallax'] * u.mas),
                  radial_velocity=STAR['rv_kms'] * u.km / u.s,
                  obstime=Time(STAR['epoch'], format='jyear'))
    c = c0.apply_space_motion(epoch_obs)
    a, d = c.ra.rad, c.dec.rad
    a0, d0 = phase_ra, phase_dec
    l = np.cos(d) * np.sin(a - a0)
    m = np.sin(d) * np.cos(d0) - np.cos(d) * np.sin(d0) * np.cos(a - a0)
    return l, m, c


# --------------------------------------------------------------- MS metadata
def _select_best_field_ms(ms_path, field_ids, times):
    """Handle genuine multi-field/mosaic data (added 2026-08-28): rather
    than refusing to search a MS with >1 FIELD_ID in its data rows (the
    previous behaviour, which silently cost 14 targets their entire
    technosignature search -- LP 876-10, TW Hya [B6/B7], HIP 36948,
    NAME AT Mic AB, HD 48370, and others), find whichever of the mosaic's
    pointings the star's own catalog position actually falls closest to,
    and split that one field out into its own single-pointing MS to search
    exactly as normal. This is a coarse (single-epoch) nearest-pointing
    choice, not a joint-mosaic search -- adequate for identifying which
    single pointing to search, since primary-beam-scale mosaic offsets
    change positions by far less than a day's worth of proper motion could
    ever matter for this purpose."""
    from casatools import table
    from casatasks import mstransform
    import shutil
    tb = table()
    tb.open(ms_path + '/FIELD')
    all_pc = tb.getcol('PHASE_DIR')[:, 0, :]
    tb.close()
    mjd_sec = float(np.median(times))
    best_id, best_off = None, np.inf
    for fid in field_ids:
        fid = int(fid)
        pra, pdec = float(all_pc[0, fid]), float(all_pc[1, fid])
        l, m, _ = star_lm(pra, pdec, mjd_sec)
        off = float(np.hypot(l, m) / ARCSEC)
        print(f'[{EB}] multi-field MS: field {fid} phase centre offset '
              f'from star = {off:.2f}"', flush=True)
        if off < best_off:
            best_off, best_id = off, fid
    print(f'[{EB}] multi-field MS: selecting field {best_id} '
          f'(closest to star, {best_off:.2f}")', flush=True)
    out_ms = f'{TARGET_DIR}/work/{EB}_field{best_id}.ms'
    os.makedirs(f'{TARGET_DIR}/work', exist_ok=True)
    shutil.rmtree(out_ms, ignore_errors=True)
    mstransform(vis=ms_path, outputvis=out_ms, field=str(best_id),
                datacolumn='data', reindex=True, keepflags=True)
    return out_ms


def ms_meta():
    from casatools import table
    global MS
    tb = table()
    tb.open(MS + '/SPECTRAL_WINDOW')
    freqs = tb.getcol('CHAN_FREQ')[:, 0].copy()
    chanw = float(abs(tb.getcol('CHAN_WIDTH')[0, 0]))
    tb.close()
    tb.open(MS)
    times = tb.getcol('TIME')
    nrow = tb.nrows()
    # Which FIELD_ID the actual DATA rows use -- NOT necessarily 0. The
    # calibration step's mstransform runs with reindex=False (needed
    # elsewhere in the pipeline), which means the FIELD subtable keeps ALL
    # of the *original* MS's rows (including calibrator fields), even
    # though only the target field's rows survive in the main table. Row 0
    # of that unreindexed FIELD table is only the target by coincidence --
    # found this the hard way: 3+ already-completed targets (PDS 70,
    # HR 8799, HD 107146) had their phase-centre read from a CALIBRATOR's
    # field entry instead, producing bogus multi-degree "offsets" in the
    # log even though the actual data and continuum maps were correctly
    # pointed at the star all along.
    field_ids = np.unique(tb.getcol('FIELD_ID'))
    tb.close()
    if len(field_ids) != 1:
        MS = _select_best_field_ms(MS, field_ids, times)
        return ms_meta()
    target_field_id = int(field_ids[0])
    tb.open(MS + '/FIELD')
    pc = tb.getcol('PHASE_DIR')[:, 0, target_field_id].copy()
    tb.close()
    return freqs, chanw, pc, times, nrow


def integration_blocks(times):
    d = np.diff(times)
    if np.any(d < -1e-6):
        raise RuntimeError('MS is not time-ordered')
    edges = np.flatnonzero(np.abs(d) > 1e-6) + 1
    starts = np.concatenate(([0], edges))
    stops = np.concatenate((edges, [len(times)]))
    return starts, stops, times[starts]


# ------------------------------------------------------------------- worker
_G = {}


def _init(freqs, lm, msname, star_lm_, inject, has_wspec):
    _G['freqs'] = freqs
    _G['lm'] = lm
    _G['ms'] = msname
    _G['star_lm'] = star_lm_
    _G['inject'] = inject
    _G['has_wspec'] = has_wspec


def _do_block(args):
    from casatools import table
    i0, i1, idx, tsec = args
    freqs = _G['freqs']; l, m = _G['lm']
    nch = len(freqs); npos = len(l)
    tb = table()
    tb.open(_G['ms'], nomodify=True)
    uvw = tb.getcol('UVW', i0, i1 - i0)
    dat = tb.getcol('DATA', i0, i1 - i0)
    flg = tb.getcol('FLAG', i0, i1 - i0)
    a1 = tb.getcol('ANTENNA1', i0, i1 - i0)
    a2 = tb.getcol('ANTENNA2', i0, i1 - i0)
    if _G['has_wspec']:
        wsp = tb.getcol('WEIGHT_SPECTRUM', i0, i1 - i0)
    else:
        w = tb.getcol('WEIGHT', i0, i1 - i0)
        wsp = np.repeat(w[:, None, :], nch, axis=1)
    tb.close()

    wsp = np.where(flg, 0.0, wsp).astype(np.float32)
    auto = (a1 == a2)
    if auto.any():
        wsp[:, :, auto] = 0.0
    dat = np.nan_to_num(dat).astype(np.complex64)

    inj = _G.get('inject')
    if inj is not None:
        amp, drift, f0 = inj
        fsig = f0 + drift * tsec
        ich = int(round((fsig - freqs[0]) / (freqs[1] - freqs[0])))
        if 0 <= ich < len(freqs):
            ls, ms_ = _G['star_lm']
            ph = (-2j * np.pi * freqs[ich] / C_M_S) * (uvw[0] * ls + uvw[1] * ms_)
            dat[:, ich, :] += (amp * np.exp(ph)).astype(np.complex64)[None, :]

    wv = (dat * wsp).sum(axis=0)
    ww = wsp.sum(axis=0)

    u, v = uvw[0], uvw[1]
    out = np.zeros((npos, nch), dtype=np.float32)
    wsum = ww.sum(axis=1)
    wsum[wsum == 0] = np.nan

    BLK = 64
    for b0 in range(0, nch, BLK):
        b1 = min(b0 + BLK, nch)
        nu = freqs[(b0 + b1) // 2]
        ph = (2j * np.pi * nu / C_M_S) * (np.outer(u, l) + np.outer(v, m))
        P = np.exp(ph).astype(np.complex64)
        out[:, b0:b1] = np.real(wv[b0:b1] @ P).T.astype(np.float32)
    out /= wsum[None, :]
    return idx, out, wsum.astype(np.float32)


def main():
    t_start = time.time()
    freqs, chanw, pc, times, nrow = ms_meta()
    starts, stops, tstamps = integration_blocks(times)
    nint = len(starts)
    pb_arcsec = primary_beam_arcsec(float(np.median(freqs)))
    print(f'[{EB}] {nrow} rows, {nint} integrations, {len(freqs)} channels, '
          f'chanwidth {chanw/1e3:.2f} kHz, {freqs[0]/1e9:.4f}-{freqs[-1]/1e9:.4f} GHz, '
          f'primary beam FWHM {pb_arcsec:.2f}"', flush=True)

    l_star, m_star, csky = star_lm(pc[0], pc[1], float(np.mean(tstamps)))
    print(f'[{EB}] phase centre  RA={np.degrees(pc[0])%360:.6f} '
          f'Dec={np.degrees(pc[1]):.6f}', flush=True)
    print(f'[{EB}] {STAR_NAME} at RA={csky.ra.deg:.6f} Dec={csky.dec.deg:.6f} '
          f'-> offset l={l_star/ARCSEC:+.3f}" m={m_star/ARCSEC:+.3f}"', flush=True)

    # Hard sanity check (added 2026-08-26 after finding LP 876-10's assigned
    # MOUS pointed ~2-3 DEGREES away from the star's own catalog position --
    # not a proper-motion issue, a crossmatch/target-assignment error
    # upstream in the ranking pipeline). Searching a field the star isn't
    # even in produces a harmless-looking "no candidate" result that is
    # actually meaningless (background sky, not the target) -- fail loudly
    # and specifically instead of silently banking a bogus null result.
    offset_arcsec = float(np.hypot(l_star, m_star) / ARCSEC)
    if offset_arcsec > 2 * pb_arcsec:
        print(f'[{EB}] FATAL: {STAR_NAME} is {offset_arcsec:.1f}" from the '
              f'ALMA phase centre, >2x the primary beam FWHM ({pb_arcsec:.1f}") '
              f'-- this MOUS almost certainly does not actually cover this '
              f'target (likely a crossmatch error upstream), aborting rather '
              f'than searching the wrong patch of sky', flush=True)
        sys.exit(1)

    names, dl, dm, n_src = probe_positions(pb_arcsec)
    lam = l_star + dl * ARCSEC
    mam = m_star + dm * ARCSEC

    from casatools import table as _tbl
    _t = _tbl(); _t.open(MS, nomodify=True)
    has_wspec = 'WEIGHT_SPECTRUM' in _t.colnames(); _t.close()
    print(f'[{EB}] WEIGHT_SPECTRUM present: {has_wspec}', flush=True)

    import multiprocessing as mp
    ctx = mp.get_context('fork')
    t0ref = float(tstamps[0])
    tasks = [(int(starts[i]), int(stops[i]), i, float(tstamps[i]) - t0ref)
             for i in range(nint)]
    npos = len(lam); nch = len(freqs)
    I = np.zeros((nint, npos, nch), dtype=np.float32)
    W = np.zeros((nint, nch), dtype=np.float32)

    inject = None
    if os.environ.get('SETI_INJECT'):
        a, dr, fo = [float(x) for x in os.environ['SETI_INJECT'].split(',')]
        if fo < 1e6:
            fo = freqs[int(fo)]
        inject = (a, dr, fo)
        print(f'[{EB}] *** INJECTION TEST: {a} Jy at {fo/1e9:.6f} GHz '
              f'drifting {dr} Hz/s ***', flush=True)

    with ctx.Pool(NPROC, initializer=_init,
                  initargs=(freqs, (lam, mam), MS,
                            (l_star, m_star), inject, has_wspec)) as pool:
        done = 0
        for idx, blk, wsum in pool.imap_unordered(_do_block, tasks, chunksize=1):
            I[idx] = blk; W[idx] = wsum
            done += 1
            if done % 50 == 0:
                print(f'[{EB}]   {done}/{nint} integrations '
                      f'({time.time()-t_start:.0f} s)', flush=True)

    np.savez_compressed(
        OUT, I=I, W=W, times=tstamps, freqs=freqs, chanw=chanw,
        names=np.array(names), dl=dl, dm=dm, n_src=n_src,
        phase_ra=pc[0], phase_dec=pc[1], l_star=l_star, m_star=m_star,
        pb_arcsec=pb_arcsec, star_name=STAR_NAME,
        t1_ra=csky.ra.deg, t1_dec=csky.dec.deg,
        parallax=STAR['parallax'], parallax_err=STAR['parallax_err'])
    print(f'[{EB}] EXTRACT COMPLETE in {time.time()-t_start:.0f} s -> {OUT} '
          f'({os.path.getsize(OUT)/1e6:.0f} MB)', flush=True)

    # ------------------------------------------------------------------
    # Retain a small, permanent copy of the STAR'S OWN raw dynamic
    # spectrum (added 2026-08-30, per Glenn's instruction). The full
    # waterfall above (I, all npos~=n_src+512 positions) is deleted by
    # process_one_target.sh right after the classical drift search runs,
    # since keeping it for every target/band would cost tens-hundreds of
    # GB (observed sizes: 46 MB-3.2 GB per EB, dominated by the 512
    # control positions, which exist only for this EB's own false-alarm
    # calibration and have no future re-analysis value). But the
    # classical linear-drift/narrowband search used here is, by design,
    # blind to non-linearly-drifting or broadband signals (see Paper I,
    # Sec 2.4) -- a complementary anomaly-detection/ML pass over the same
    # archival data is explicitly future work (Paper I, Sec 5), and
    # cannot be done later without this raw material, which cannot be
    # cheaply regenerated once the calibrated MS is cleaned up downstream.
    # Keep ONLY the star's own spectrum (index 0 of the position axis --
    # NOT the ring-of-nearby-source-checks or the 512 controls) plus a
    # small, fixed-size sample of control positions for future local-RFI
    # context, at a cost of order (1+N_CONTROL_SAMPLE)/npos of the full
    # file, i.e. a few MB rather than hundreds/thousands.
    N_CONTROL_SAMPLE = 8
    control_start = n_src  # index 0..n_src-1 are 'star' + its check-ring
    n_control_total = I.shape[1] - control_start
    sample_idx = np.linspace(0, n_control_total - 1,
                              min(N_CONTROL_SAMPLE, n_control_total)).astype(int)
    sample_idx = control_start + sample_idx
    SRC_OUT = f'{TARGET_DIR}/products/{EB}{_SFX}_srcspec.npz'
    np.savez_compressed(
        SRC_OUT,
        I_star=I[:, 0, :],                       # (nint, nch) -- the star itself
        I_control_sample=I[:, sample_idx, :],    # (nint, N_CONTROL_SAMPLE, nch)
        control_sample_names=np.array(names)[sample_idx],
        W=W, times=tstamps, freqs=freqs, chanw=chanw,
        phase_ra=pc[0], phase_dec=pc[1], l_star=l_star, m_star=m_star,
        pb_arcsec=pb_arcsec, star_name=STAR_NAME,
        t1_ra=csky.ra.deg, t1_dec=csky.dec.deg,
        parallax=STAR['parallax'], parallax_err=STAR['parallax_err'])
    print(f'[{EB}] retained star-only raw spectrum for future ML/anomaly-'
          f'detection follow-up -> {SRC_OUT} '
          f'({os.path.getsize(SRC_OUT)/1e6:.1f} MB, vs '
          f'{os.path.getsize(OUT)/1e6:.0f} MB for the full multi-control '
          f'waterfall that will shortly be deleted)', flush=True)


if __name__ == '__main__':
    main()
