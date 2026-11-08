#!/usr/bin/env python3
"""
Step 2 of the ALMA-SETI / TRAPPIST-1 pipeline.

Reads the calibrated, TRAPPIST-1-only measurement set and evaluates the
*dirty* channel-map intensity at a set of sky positions, for every
correlator integration and every frequency channel, by direct Fourier
transform of the visibilities:

     I(l,m) = Re[ SUM_k w_k V_k exp(2 pi i (u_k l + v_k m) nu / c) ] / SUM_k w_k

This is mathematically identical to reading the pixel value out of a
naturally-weighted dirty image (as the reference paper does with CASA
tclean+imstat) but costs ~10^4 times less, because we only ever evaluate
the few hundred pixels we actually care about.

Positions evaluated
  - "src"  : TRAPPIST-1 (Gaia DR3 astrometry propagated to the epoch of
             observation) plus a ring of offsets out to 1.1 arcsec,
             matching the reference paper's adjacent-pixel search.
  - "ctrl" : control positions, on which the identical search is run to
             measure the empirical false-alarm rate.
  - "noise": probe positions used to measure the r.m.s. of each channel
             map (the analogue of CASA imstat).

Output: /data/SETI/products/<EB>_waterfall.npz

Usage: step2_extract.py <EBID> [nproc]
"""
import os, sys, json, time
for _v in ('OMP_NUM_THREADS','OPENBLAS_NUM_THREADS','MKL_NUM_THREADS',
           'NUMEXPR_NUM_THREADS','VECLIB_MAXIMUM_THREADS'):
    os.environ[_v] = '1'
import numpy as np

EB    = sys.argv[1]
NPROC = int(sys.argv[2]) if len(sys.argv) > 2 else 48
ROOT  = '/data/SETI'
_MSOVERRIDE = os.environ.get('SETI_MS')
MS    = _MSOVERRIDE or f'{ROOT}/products/{EB}_trappist1_fdm.ms'
_SFX  = os.environ.get('SETI_SFX', '') or ('_inj' if os.environ.get('SETI_INJECT') else '')
OUT   = f'{ROOT}/products/{EB}{_SFX}_waterfall.npz'
# For calibrator fields the "source" IS the phase centre by construction
# (calibrator scans are pointed directly at the calibrator), so there is no
# Gaia proper-motion lookup to do -- just search at l=m=0.
PHASECENTER_MODE = bool(os.environ.get('SETI_PHASECENTER_MODE'))
os.environ.setdefault('CASASITECONFIG', '/home/fetch-agi/.casa/config.py')

C_M_S = 299792458.0
ARCSEC = np.pi / 180.0 / 3600.0

# ---- TRAPPIST-1, Gaia DR3 2635476908753563008 (epoch 2016.0) --------------
T1 = dict(ra_deg=346.62652162764437, dec_deg=-5.043528319429532,
          pmra=930.7875225817781, pmdec=-479.0375409528857,   # mas/yr
          parallax=80.21231612635748, parallax_err=0.07160574,  # mas
          epoch=2016.0, rv_kms=-51.0)


def probe_positions(seed=20260822):
    """Return (name, l_arcsec, m_arcsec) arrays, offsets from the STAR."""
    rng = np.random.default_rng(seed)
    names, dl, dm = [], [], []
    names.append('star'); dl.append(0.0); dm.append(0.0)
    # ring sampling out to 1.1" (reference paper searches adjacent pixels
    # over a 1.1" diameter; we go to 1.1" radius, i.e. more conservative)
    for r in (0.15, 0.30, 0.55, 0.80, 1.10):
        n = max(6, int(round(2 * np.pi * r / 0.15)))
        n = min(n, 24)
        for k in range(n):
            th = 2 * np.pi * k / n
            names.append(f'src_r{r:.2f}_{k}')
            dl.append(r * np.cos(th)); dm.append(r * np.sin(th))
    n_src = len(names)
    # control + noise probes: annulus 2.5" - 14" (inside the 18" primary beam)
    n_probe = 512
    rr = np.sqrt(rng.uniform(2.5**2, 14.0**2, n_probe))
    th = rng.uniform(0, 2 * np.pi, n_probe)
    for k in range(n_probe):
        names.append(f'probe_{k}')
        dl.append(rr[k] * np.cos(th[k])); dm.append(rr[k] * np.sin(th[k]))
    return names, np.array(dl), np.array(dm), n_src


def star_lm(phase_ra, phase_dec, mjd_sec):
    """Direction cosines of TRAPPIST-1 relative to the MS phase centre."""
    from astropy.coordinates import SkyCoord, Distance
    from astropy.time import Time
    import astropy.units as u
    epoch_obs = Time(mjd_sec / 86400.0, format='mjd')
    c0 = SkyCoord(ra=T1['ra_deg'] * u.deg, dec=T1['dec_deg'] * u.deg,
                  pm_ra_cosdec=T1['pmra'] * u.mas / u.yr,
                  pm_dec=T1['pmdec'] * u.mas / u.yr,
                  distance=Distance(parallax=T1['parallax'] * u.mas),
                  radial_velocity=T1['rv_kms'] * u.km / u.s,
                  obstime=Time(T1['epoch'], format='jyear'))
    c = c0.apply_space_motion(epoch_obs)
    a, d = c.ra.rad, c.dec.rad
    a0, d0 = phase_ra, phase_dec
    l = np.cos(d) * np.sin(a - a0)
    m = np.sin(d) * np.cos(d0) - np.cos(d) * np.sin(d0) * np.cos(a - a0)
    return l, m, c


# --------------------------------------------------------------- MS metadata
def ms_meta():
    from casatools import table
    tb = table()
    tb.open(MS + '/SPECTRAL_WINDOW'); freqs = tb.getcol('CHAN_FREQ')[:, 0].copy()
    chanw = float(abs(tb.getcol('CHAN_WIDTH')[0, 0])); tb.close()
    tb.open(MS + '/FIELD'); pc = tb.getcol('PHASE_DIR')[:, 0, 0].copy(); tb.close()
    tb.open(MS)
    times = tb.getcol('TIME')
    nrow = tb.nrows()
    tb.close()
    return freqs, chanw, pc, times, nrow


def integration_blocks(times):
    """Contiguous row ranges sharing one TIME stamp."""
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
    """DFT one integration to all probe positions -> (npos, nchan) float32."""
    from casatools import table
    i0, i1, idx, tsec = args
    freqs = _G['freqs']; l, m = _G['lm']
    nch = len(freqs); npos = len(l)
    tb = table()
    tb.open(_G['ms'], nomodify=True)
    uvw = tb.getcol('UVW', i0, i1 - i0)                # (3, nrow)
    dat = tb.getcol('DATA', i0, i1 - i0)               # (npol, nch, nrow)
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
    # Autocorrelations must never enter the interferometric sum: they carry
    # total power (~13 Jy here) at u=v=0, so they add a position-independent
    # pedestal, and ALMA gives them WEIGHT ~8e6, i.e. ~4e5 times the
    # cross-correlation weights -- they would dominate SUM(w) and dilute any
    # real point-source signal into invisibility.
    auto = (a1 == a2)
    if auto.any():
        wsp[:, :, auto] = 0.0
    dat = np.nan_to_num(dat).astype(np.complex64)

    # ---- optional end-to-end validation: inject a synthetic narrowband,
    # ---- linearly drifting point source at the position of TRAPPIST-1.
    inj = _G.get('inject')
    if inj is not None:
        amp, drift, f0 = inj                     # Jy, Hz/s, Hz
        fsig = f0 + drift * tsec
        ich = int(round((fsig - freqs[0]) / (freqs[1] - freqs[0])))
        if 0 <= ich < len(freqs):
            ls, ms_ = _G['star_lm']
            ph = (-2j * np.pi * freqs[ich] / C_M_S) * (uvw[0] * ls + uvw[1] * ms_)
            dat[:, ich, :] += (amp * np.exp(ph)).astype(np.complex64)[None, :]
    # Stokes I from XX,YY  (weighted mean of the parallel hands)
    wv = (dat * wsp).sum(axis=0)                       # (nch, nrow)
    ww = wsp.sum(axis=0)                               # (nch, nrow)

    u, v = uvw[0], uvw[1]
    out = np.zeros((npos, nch), dtype=np.float32)
    wsum = ww.sum(axis=1)
    wsum[wsum == 0] = np.nan

    # Channel blocks: within a block the (u,v) scaling with frequency is
    # frozen at the block centre. 64 channels = 62 MHz out of 346 GHz,
    # a 1.8e-4 fractional change -> < 0.01 rad phase error at 14".
    BLK = 64
    for b0 in range(0, nch, BLK):
        b1 = min(b0 + BLK, nch)
        nu = freqs[(b0 + b1) // 2]
        ph = (2j * np.pi * nu / C_M_S) * (np.outer(u, l) + np.outer(v, m))
        P = np.exp(ph).astype(np.complex64)            # (nrow, npos)
        out[:, b0:b1] = np.real(wv[b0:b1] @ P).T.astype(np.float32)
    out /= wsum[None, :]
    return idx, out, wsum.astype(np.float32)


def main():
    t_start = time.time()
    freqs, chanw, pc, times, nrow = ms_meta()
    starts, stops, tstamps = integration_blocks(times)
    nint = len(starts)
    print(f'[{EB}] {nrow} rows, {nint} integrations, {len(freqs)} channels, '
          f'chanwidth {chanw/1e3:.2f} kHz, {freqs[0]/1e9:.4f}-{freqs[-1]/1e9:.4f} GHz',
          flush=True)

    if PHASECENTER_MODE:
        l_star, m_star = 0.0, 0.0
        print(f'[{EB}] phase centre  RA={np.degrees(pc[0])%360:.6f} '
              f'Dec={np.degrees(pc[1]):.6f}  (calibrator field: searching '
              f'AT the phase centre, l=m=0)', flush=True)
    else:
        l_star, m_star, csky = star_lm(pc[0], pc[1], float(np.mean(tstamps)))
        print(f'[{EB}] phase centre  RA={np.degrees(pc[0])%360:.6f} '
              f'Dec={np.degrees(pc[1]):.6f}', flush=True)
        print(f'[{EB}] TRAPPIST-1 at RA={csky.ra.deg:.6f} Dec={csky.dec.deg:.6f} '
              f'-> offset l={l_star/ARCSEC:+.3f}" m={m_star/ARCSEC:+.3f}"', flush=True)

    names, dl, dm, n_src = probe_positions()
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
        if fo < 1e6:                       # given as a channel index
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

    if PHASECENTER_MODE:
        # calibrator field: no real distance/EIRP interpretation intended,
        # this is a pure systematics/false-alarm check, not a new limit.
        t1_ra, t1_dec = np.degrees(pc[0]) % 360, np.degrees(pc[1])
        plx, plx_e = 1000.0 / 1.0, 0.0   # placeholder d=1000pc, EIRP not meaningful
    else:
        t1_ra, t1_dec = csky.ra.deg, csky.dec.deg
        plx, plx_e = T1['parallax'], T1['parallax_err']

    np.savez_compressed(
        OUT, I=I, W=W, times=tstamps, freqs=freqs, chanw=chanw,
        names=np.array(names), dl=dl, dm=dm, n_src=n_src,
        phase_ra=pc[0], phase_dec=pc[1], l_star=l_star, m_star=m_star,
        t1_ra=t1_ra, t1_dec=t1_dec,
        parallax=plx, parallax_err=plx_e)
    print(f'[{EB}] STEP2 COMPLETE in {time.time()-t_start:.0f} s -> {OUT} '
          f'({os.path.getsize(OUT)/1e6:.0f} MB)', flush=True)


if __name__ == '__main__':
    main()
