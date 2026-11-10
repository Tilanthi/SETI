#!/usr/bin/env python3
"""
Continuum map for one SETI-search target, using the full available ALMA
bandwidth EXCLUDING any spectral window/channels found to carry strong
molecular line emission (e.g. CO), per Glenn's instruction. Produces a
FITS image, a PNG rendering, and a notes.txt documenting which channels
(if any) were blanked and why.

Design choices driven by the "minimise cluster impact" directive for this
run: line identification uses a single-position direct-DFT spectrum (cheap:
one visibility pass per EB, not a full per-channel image cube), and the
final map is a naturally-weighted DIRTY image (niter=0, no deconvolution
iterations) rather than a cleaned one -- this is the same "no cleaning"
convention already used for the SETI search itself (matching Mason et al.
2024's method) and keeps tclean's compute cost to a single wideband FFT/
gridding pass instead of many CLEAN major/minor cycles.

Usage: continuum_map_generic.py <target_dir> <star_name> <ra_deg> <dec_deg>
                                  <pmra_masyr> <pmdec_masyr> <parallax_mas>
                                  [ncores]
"""
import os, re, sys, json, glob, shutil, time
os.environ.setdefault('CASASITECONFIG', '/home/fetch-agi/.casa/config.py')
for _v in ('OMP_NUM_THREADS', 'OPENBLAS_NUM_THREADS', 'MKL_NUM_THREADS'):
    os.environ[_v] = os.environ.get(_v, '2')
import numpy as np

TARGET_DIR, STAR_NAME = sys.argv[1], sys.argv[2]
RA, DEC, PMRA, PMDEC, PLX = (float(x) for x in sys.argv[3:8])
NCORES = int(sys.argv[8]) if len(sys.argv) > 8 else 4

PROD = f'{TARGET_DIR}/products'
LOGD = f'{TARGET_DIR}/logs'
WORK = f'{TARGET_DIR}/work'
os.makedirs(WORK, exist_ok=True)

C_M_S = 299792458.0
ALMA_DISH_M = 12.0
ARCSEC = np.pi / 180.0 / 3600.0


def primary_beam_arcsec(freq_hz):
    """FWHM of a single 12 m ALMA dish's primary beam at freq_hz (same
    theta_PB = 1.22 lambda / D convention as seti_extract_generic.py, so
    the two scripts' primary-beam accounting stays consistent)."""
    wavelength_m = C_M_S / freq_hz
    return np.degrees(1.22 * wavelength_m / ALMA_DISH_M) * 3600.0


def safe_filename(name):
    """Some targets have no resolvable common name and fall back to a
    Gaia DR3 identifier string like 'HR 1010 (Gaia DR3 4722...)' -- naive
    space-replacement leaves the parentheses in place, which CASA's
    exportfits/CFITSIO chokes on ('Cannot open file for writing'), losing
    the continuum map entirely for every such target. Strip to a safe
    [A-Za-z0-9_-] filename stem, same convention as the per-target
    directory name in process_one_target.sh."""
    s = re.sub(r"[ /()]", "_", name)
    s = re.sub(r"[^A-Za-z0-9_-]", "", s)
    return re.sub(r"_+", "_", s).strip("_")

# Common bright millimetre molecular transitions to name-check identified
# line channels against in the notes (not required for the blanking logic
# itself, which is purely a data-driven outlier search -- this is just to
# make the human-readable note more informative).
KNOWN_LINES_GHZ = {
    'CO(1-0)': 115.271, 'CO(2-1)': 230.538, 'CO(3-2)': 345.796,
    'CO(4-3)': 461.041, 'CO(6-5)': 691.473, '13CO(2-1)': 220.399,
    'C18O(2-1)': 219.560, 'HCN(1-0)': 88.632, 'HCN(3-2)': 265.886,
    'HCO+(1-0)': 89.189, 'HCO+(3-2)': 267.558, 'CS(5-4)': 244.936,
    'CN(1-0)': 113.491, 'SiO(5-4)': 217.105, 'H2CO': 218.222,
}


def nearest_known_line(freq_ghz):
    best, bestdf = None, 1e9
    for name, f0 in KNOWN_LINES_GHZ.items():
        df = abs(freq_ghz - f0)
        if df < bestdf:
            best, bestdf = name, df
    return best, bestdf


def find_target_ms_list():
    status_path = f'{LOGD}/calibrate_status.json'
    if not os.path.exists(status_path):
        return []
    status = json.load(open(status_path))
    return [v['ms'] for v in status['ebs'].values() if v.get('ok')]


def resolve_single_field_ms(ms):
    """Fixed 2026-08-30: this target/band's calibrated MS may cover a genuine
    multi-object ALMA mosaic (a single MOUS observing dozens of named fields
    at once, e.g. a whole star-forming-region disk survey) rather than one
    field per our star. Before this fix, any MS with >1 real FIELD_ID fell
    back to an arbitrary 'field 0' for both the line-search phase centre AND
    the final tclean image (which was run with field='', i.e. ALL fields
    blended together) -- meaning the reported continuum flux/detection was
    NOT specific to our star at all. Caught because two of our own catalogue
    targets sharing one such mosaic (e.g. CT Cha / CHXR 73; HT Lup / TYC
    7851-810-1) produced bit-identical 'detections'. A scan across the whole
    sample found 66/136 processed targets (~49%) are on a multi-field MOUS.
    Fix: pick the one FIELD_ID whose own phase centre is closest to our
    star's true (proper-motion-corrected) position, and physically split
    the MS down to just that field -- exactly the same approach already
    used for the narrowband search path in seti_extract_generic.py's
    ms_meta()/_select_best_field_ms() since 2026-08-28, which this brings
    the continuum path into line with."""
    from casatools import table
    tb = table()
    tb.open(ms)
    field_ids = np.unique(tb.getcol('FIELD_ID'))
    tstamp = float(np.median(tb.getcol('TIME')))
    tb.close()
    if len(field_ids) == 1:
        return ms
    tb.open(ms + '/FIELD')
    pcs = tb.getcol('PHASE_DIR')[:, 0, :].copy()   # shape (2, nfield)
    tb.close()
    best_id, best_sep = None, None
    for fid in field_ids:
        pc_ra, pc_dec = pcs[0, fid], pcs[1, fid]
        l, m = star_lm(pc_ra, pc_dec, tstamp)
        sep = float(np.hypot(l, m))
        if best_sep is None or sep < best_sep:
            best_id, best_sep = int(fid), sep
    print(f'[continuum_map] {os.path.basename(ms)} has {len(field_ids)} distinct '
          f'FIELD_IDs; star is closest to field {best_id} '
          f'({np.degrees(best_sep)*3600:.2f} arcsec away) -- splitting to that '
          f'field only before imaging', flush=True)
    from casatasks import mstransform
    out = f'{WORK}/{os.path.basename(ms).replace(".ms","")}_field{best_id}.ms'
    shutil.rmtree(out, ignore_errors=True)
    mstransform(vis=ms, outputvis=out, field=str(best_id), datacolumn='data',
                reindex=True, keepflags=True)
    return out


def star_lm(phase_ra, phase_dec, mjd_sec):
    from astropy.coordinates import SkyCoord, Distance
    from astropy.time import Time
    import astropy.units as u
    epoch_obs = Time(mjd_sec / 86400.0, format='mjd')
    plx = PLX if PLX and PLX > 0 else 1e-3
    c0 = SkyCoord(ra=RA * u.deg, dec=DEC * u.deg,
                  pm_ra_cosdec=PMRA * u.mas / u.yr, pm_dec=PMDEC * u.mas / u.yr,
                  distance=Distance(parallax=plx * u.mas),
                  radial_velocity=0 * u.km / u.s, obstime=Time(2016.0, format='jyear'))
    c = c0.apply_space_motion(epoch_obs)
    a, d = c.ra.rad, c.dec.rad
    a0, d0 = phase_ra, phase_dec
    l = np.cos(d) * np.sin(a - a0)
    m = np.sin(d) * np.cos(d0) - np.cos(d) * np.sin(d0) * np.cos(a - a0)
    return l, m


def quick_spectrum(ms, spw_id, l, m):
    """Cheap single-position DFT spectrum, summed over all rows, for line
    identification only -- not used for the final map."""
    from casatools import table
    tb = table()
    tb.open(f'{ms}/SPECTRAL_WINDOW')
    freqs = tb.getcol('CHAN_FREQ', startrow=spw_id, nrow=1)[:, 0].copy()
    tb.close()
    tb.open(ms)
    try:
        sub = tb.query(f'DATA_DESC_ID=={spw_id}')
    except Exception:
        sub = tb
    uvw = sub.getcol('UVW')
    dat = sub.getcol('DATA')
    flg = sub.getcol('FLAG')
    a1 = sub.getcol('ANTENNA1'); a2 = sub.getcol('ANTENNA2')
    w = sub.getcol('WEIGHT')
    if sub is not tb:
        sub.close()
    tb.close()
    nch = len(freqs)
    # Defensive shape handling: some ALMA calibration/channel-averaged
    # windows (e.g. single-polarization-product spws) deliver DATA/FLAG/
    # WEIGHT with a squeezed polarization axis, which otherwise crashes the
    # indexing below -- normalise everything to (npol, nch, nrow) /
    # (npol, nrow) before combining, rather than silently dropping the spw.
    if dat.ndim == 2:      # (nch, nrow) -> (1, nch, nrow)
        dat = dat[None, :, :]
    if flg.ndim == 2:
        flg = flg[None, :, :]
    if w.ndim == 1:        # (nrow,) -> (1, nrow)
        w = w[None, :]
    npol_dat = dat.shape[0]
    if w.shape[0] != npol_dat:
        if w.shape[0] == 1:
            w = np.repeat(w, npol_dat, axis=0)
        elif npol_dat == 1:
            w = w.mean(axis=0, keepdims=True)
        else:
            w = w[:npol_dat]
    wsp = np.repeat(w[:, None, :], nch, axis=1).astype(np.float32)
    wsp = np.where(flg, 0.0, wsp)
    auto = (a1 == a2)
    if auto.any():
        wsp[:, :, auto] = 0.0
    dat = np.nan_to_num(dat).astype(np.complex64)
    ph = (2j * np.pi * freqs[:, None] / C_M_S) * (uvw[0] * l + uvw[1] * m)
    P = np.exp(ph).astype(np.complex64)          # (nch, nrow)
    wv = (dat * wsp).sum(axis=0)                  # (nch, nrow)
    ww = wsp.sum(axis=0)                           # (nch, nrow)
    num = np.real(np.sum(wv * P, axis=1))
    den = np.sum(ww, axis=1)
    spec = np.divide(num, den, out=np.full(nch, np.nan), where=den > 0)
    return freqs, spec


def find_line_channels(freqs, spec, nsigma=5.0):
    """Robust outlier search: any channel whose flux exceeds the local
    (median-filtered) baseline by more than nsigma x MAD is flagged as
    line-contaminated. A wide median window (~5% of the band) approximates
    the true (smooth) continuum level so real, typically much narrower
    line features stand out clearly."""
    from scipy.ndimage import median_filter
    n = len(spec)
    win = max(9, (n // 20) | 1)
    finite = np.isfinite(spec)
    filled = np.where(finite, spec, np.nanmedian(spec))
    baseline = median_filter(filled, size=win, mode='nearest')
    resid = filled - baseline
    mad = 1.4826 * np.median(np.abs(resid[finite] - np.median(resid[finite])))
    if mad <= 0 or not np.isfinite(mad):
        return np.zeros(n, dtype=bool), baseline
    is_line = finite & (np.abs(resid) > nsigma * mad)
    return is_line, baseline


def main():
    t0 = time.time()
    ms_list_raw = find_target_ms_list()
    if not ms_list_raw:
        print('[continuum_map] no calibrated target MS found, aborting', flush=True)
        sys.exit(1)
    ms_list = [resolve_single_field_ms(ms) for ms in ms_list_raw]

    notes = [f'Continuum map notes for {STAR_NAME}', f'Generated {time.time()}',
              f'Input MS(es) (raw): {ms_list_raw}',
              f'Input MS(es) (after per-star field resolution): {ms_list}', '']
    spw_windows = []   # (ms, spw_id, freqs, line_mask, spec)
    eb_tstamp = {}      # ms -> median MJD time (seconds), for the variability check below
    ms_pb_info = {}     # ms -> (offset_arcsec, pb_arcsec), for the primary-beam
                         # correction applied to the final image below
    from casatools import table
    tb = table()
    for ms in ms_list:
        tb.open(ms)
        tstamp = float(np.median(tb.getcol('TIME')))
        eb_tstamp[ms] = tstamp
        # Same fix as seti_extract_generic.py's ms_meta() (2026-08-26): use
        # the FIELD_ID actually referenced by the data rows, not row 0 of
        # the FIELD subtable, which can be a leftover calibrator entry
        # (mstransform runs with reindex=False elsewhere in the pipeline,
        # so unused fields -- including calibrators -- remain in the table).
        field_ids = np.unique(tb.getcol('FIELD_ID'))
        tb.close()
        if len(field_ids) != 1:
            print(f'[continuum_map] WARNING: {os.path.basename(ms)} has '
                  f'{len(field_ids)} distinct FIELD_IDs in its data rows '
                  f'(expected 1) -- falling back to field 0 for the line-'
                  f'search phase centre, which may be imprecise', flush=True)
        target_field_id = int(field_ids[0]) if len(field_ids) == 1 else 0
        tb.open(ms + '/FIELD')
        pc = tb.getcol('PHASE_DIR')[:, 0, target_field_id].copy()
        tb.close()
        l, m = star_lm(pc[0], pc[1], tstamp)
        tb.open(ms + '/SPECTRAL_WINDOW')
        nspw = tb.nrows()
        spw0_freqs = tb.getcol('CHAN_FREQ', startrow=0, nrow=1)[:, 0].copy()
        tb.close()

        # Crossmatch sanity check (added 2026-08-30, mirroring the same
        # check already in seti_extract_generic.py, after finding it was
        # MISSING here: a MOUS wrongly cross-matched to a star -- its actual
        # pointing many primary-beam-widths away -- was silently imaged and
        # could produce a spurious "detection" of whatever unrelated bright
        # source happens to sit at that MOUS's real phase centre (caught
        # live for 3 targets in this survey, one showing an 8 Jy "peak"
        # utterly inconsistent with any of our other continuum measurements,
        # all sub-10 mJy). Abort this target's continuum step rather than
        # bank a result attributable to the wrong patch of sky.
        offset_arcsec = float(np.hypot(l, m) / ARCSEC)
        pb_arcsec = primary_beam_arcsec(float(np.median(spw0_freqs)))
        if offset_arcsec > 2 * pb_arcsec:
            print(f'[continuum_map] FATAL: {STAR_NAME} is {offset_arcsec:.1f}" '
                  f'from the ALMA phase centre of {os.path.basename(ms)}, '
                  f'>2x the primary beam FWHM ({pb_arcsec:.1f}") -- this MOUS '
                  f'almost certainly does not actually cover this target '
                  f'(likely a crossmatch error upstream), aborting rather '
                  f'than imaging the wrong patch of sky', flush=True)
            sys.exit(1)
        ms_pb_info[ms] = (offset_arcsec, pb_arcsec)
        for spw_id in range(nspw):
            tb.open(ms + '/SPECTRAL_WINDOW')
            nch = tb.getcol('NUM_CHAN', startrow=spw_id, nrow=1)[0]
            tb.close()
            if nch < 4:
                continue
            try:
                freqs, spec = quick_spectrum(ms, spw_id, l, m)
            except Exception as e:
                notes.append(f'spw {spw_id} in {os.path.basename(ms)}: '
                             f'spectrum extraction failed ({e}), skipped for line search')
                continue
            is_line, baseline = find_line_channels(freqs, spec)
            frac_line = is_line.mean()
            spw_windows.append((ms, spw_id, freqs, is_line, spec))
            if is_line.any():
                # summarise contiguous line-flagged channel groups
                idx = np.flatnonzero(is_line)
                groups = np.split(idx, np.flatnonzero(np.diff(idx) > 1) + 1)
                for g in groups:
                    flo, fhi = freqs[g[0]] / 1e9, freqs[g[-1]] / 1e9
                    fmid = 0.5 * (flo + fhi)
                    name, df = nearest_known_line(fmid)
                    tag = f' (near {name}, {df*1e3:.0f} MHz away)' if df < 0.3 else ''
                    notes.append(f'  BLANKED: spw {spw_id} [{os.path.basename(ms)}] '
                                 f'{flo:.4f}-{fhi:.4f} GHz ({len(g)} channels){tag}')
            print(f'[continuum_map] {os.path.basename(ms)} spw {spw_id}: '
                  f'{is_line.sum()}/{nch} channels ({frac_line*100:.1f}%) flagged as line',
                  flush=True)

    if not spw_windows:
        print('[continuum_map] no usable spectral windows found', flush=True)
        sys.exit(1)

    # ------------------------------------------- per-epoch variability check
    # Added 2026-08-28 per Glenn's request: up to now, when a target has
    # multiple execution blocks (potentially different dates -- ALMA often
    # splits a program's on-source time across separate scheduling blocks),
    # they were combined into one averaged continuum image with no check
    # that the source's flux was actually consistent between them first. A
    # genuine flare/fade between epochs would have been silently smeared
    # into the combined map rather than reported. This reuses the
    # already-computed per-channel, line-free spectra (spw_windows) --
    # essentially free, no extra visibility pass -- to get one continuum
    # flux density per EB, and tests whether those EB-level fluxes are
    # consistent with a single constant source. (Comparing FLUX ACROSS
    # BANDS is a separate question -- different bands are different
    # frequencies with their own expected spectral index, so a raw flux
    # difference there is not by itself evidence of variability; that
    # would require a spectral-index model and is not attempted here.)
    per_eb = {}
    for ms, spw_id, freqs, is_line, spec in spw_windows:
        good = ~is_line & np.isfinite(spec)
        if not good.any():
            continue
        per_eb.setdefault(ms, []).append(spec[good])
    eb_flux = []   # (eb_label, tstamp, flux_mJy, err_mJy, n_chan)
    for ms, chunks in per_eb.items():
        vals = np.concatenate(chunks)
        if len(vals) < 3:
            continue
        flux = float(np.median(vals)) * 1e3
        mad = 1.4826 * float(np.median(np.abs(vals - np.median(vals))))
        # np.sqrt() on a plain int returns numpy.float64, not a native
        # Python float -- explicit cast (bit us once before with float32
        # in this same file; being careful about it consistently now).
        err = float((mad * 1e3) / np.sqrt(len(vals))) if mad > 0 else float('nan')
        eb_flux.append((os.path.basename(ms), eb_tstamp[ms], flux, err, len(vals)))
    eb_flux.sort(key=lambda x: x[1])

    variability = dict(n_epochs=len(eb_flux), epochs=[])
    for label, tstamp, flux, err, n in eb_flux:
        variability['epochs'].append(dict(eb=label, mjd=tstamp / 86400.0,
                                           flux_mJy=flux, err_mJy=err, n_chan=int(n)))
    if len(eb_flux) >= 2:
        fluxes = np.array([e[2] for e in eb_flux])
        errs = np.array([e[3] for e in eb_flux])
        errs = np.where((errs > 0) & np.isfinite(errs), errs, np.nanmedian(errs[errs > 0]))
        w = 1.0 / errs**2
        wmean = float(np.sum(fluxes * w) / np.sum(w))
        chi2 = float(np.sum((fluxes - wmean)**2 * w))
        dof = len(fluxes) - 1
        chi2_red = chi2 / dof if dof > 0 else np.nan
        span_days = (eb_flux[-1][1] - eb_flux[0][1]) / 86400.0
        variability.update(weighted_mean_flux_mJy=wmean, chi2=chi2, dof=dof,
                            chi2_reduced=chi2_red, time_span_days=span_days,
                            flagged_variable=bool(chi2_red > 3.0))
        notes.append('')
        notes.append(f'Per-epoch continuum flux check ({len(eb_flux)} EBs spanning '
                     f'{span_days:.2f} days):')
        for label, tstamp, flux, err, n in eb_flux:
            notes.append(f'  {label}: {flux:.3f} +/- {err:.3f} mJy ({n} channels)')
        notes.append(f'  weighted mean = {wmean:.3f} mJy, '
                     f'chi2/dof = {chi2:.2f}/{dof} = {chi2_red:.2f}')
        if variability['flagged_variable']:
            notes.append('  ** FLAGGED: epoch-to-epoch flux inconsistent with a constant '
                         'source (chi2_reduced > 3) -- possible genuine variability, '
                         'review before treating the combined map as a single-epoch flux **')
        else:
            notes.append('  epoch fluxes consistent with a constant source at this '
                         'sensitivity (no variability flagged)')
        print(f'[continuum_map] variability check: {len(eb_flux)} epochs, '
              f'chi2_reduced={chi2_red:.2f}, flagged={variability["flagged_variable"]}',
              flush=True)
    elif len(eb_flux) == 1:
        notes.append('')
        notes.append(f'Only 1 usable EB for this target/band -- no epoch-to-epoch '
                     f'variability check possible (flux = {eb_flux[0][2]:.3f} '
                     f'+/- {eb_flux[0][3]:.3f} mJy).')

    # ---------------------------------------------------- build tclean spw string
    # For each spw, express the line-free channel ranges as a CASA spw
    # selection string "spwid:ch0~ch1;ch2~ch3;...".
    spw_sel_parts = []
    total_line_frac = []
    for ms, spw_id, freqs, is_line, _spec in spw_windows:
        good = ~is_line
        total_line_frac.append(is_line.mean())
        if not good.any():
            continue
        idx = np.flatnonzero(good)
        groups = np.split(idx, np.flatnonzero(np.diff(idx) > 1) + 1)
        ranges = ';'.join(f'{g[0]}~{g[-1]}' for g in groups if len(g) > 0)
        spw_sel_parts.append((ms, f'{spw_id}:{ranges}'))

    if not spw_sel_parts:
        notes.append('ALL channels in ALL spws were flagged as line-contaminated -- '
                     'no line-free continuum could be formed for this target.')
        open(f'{PROD}/continuum_notes.txt', 'w').write('\n'.join(notes))
        print('[continuum_map] no line-free channels available, aborting imaging', flush=True)
        sys.exit(0)

    # tclean needs one MS + one spw-selection string per vis; group by MS
    from collections import defaultdict
    by_ms = defaultdict(list)
    for ms, sel in spw_sel_parts:
        by_ms[ms].append(sel)
    vis_list = list(by_ms.keys())
    spw_list = [','.join(v) for v in by_ms.values()]

    notes.append('')
    notes.append(f'Line-flagged fraction of bandwidth (mean over spws): '
                 f'{np.mean(total_line_frac)*100:.1f}%')
    notes.append(f'Imaging {len(vis_list)} MS(es), spw selections: {spw_list}')

    # ---------------------------------------------------------- image (dirty)
    from casatasks import tclean, exportfits
    imname = f'{WORK}/{safe_filename(STAR_NAME)}_cont'
    IMSIZE = 256
    CELL_ARCSEC = 0.5
    for ext in ('.image', '.psf', '.pb', '.residual', '.model', '.sumwt', '.mask'):
        shutil.rmtree(imname + ext, ignore_errors=True)
    try:
        tclean(vis=vis_list, spw=spw_list, field='', imagename=imname,
               specmode='mfs', deconvolver='hogbom', niter=0,
               imsize=IMSIZE, cell=f'{CELL_ARCSEC}arcsec', weighting='natural',
               pbcor=False, interactive=False, parallel=False)
        # (thread count is capped via OMP_NUM_THREADS/taskset above and in
        # governor.run_throttled, not via a tclean kwarg -- this CASA build's
        # tclean doesn't accept a 'threads=' argument)
    except Exception as e:
        notes.append(f'tclean failed: {e}')
        open(f'{PROD}/continuum_notes.txt', 'w').write('\n'.join(notes))
        print(f'[continuum_map] tclean failed: {e}', flush=True)
        sys.exit(1)

    fits_out = f'{PROD}/{safe_filename(STAR_NAME)}_continuum.fits'
    exportfits(imagename=imname + '.image', fitsimage=fits_out, overwrite=True)

    # ---------------------------------------------------------------- PNG
    from astropy.io import fits
    from astropy.wcs import WCS
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    with fits.open(fits_out) as hdul:
        data = np.squeeze(hdul[0].data)
        hdr = hdul[0].header
    rms = 1.4826 * np.nanmedian(np.abs(data - np.nanmedian(data)))
    peak = np.nanmax(data)

    # Primary-beam correction (added 2026-08-30, per Glenn's instruction to
    # confirm this is done -- previously this map was formed with
    # pbcor=False and never corrected afterwards either). Since tclean was
    # run with pbcor=False, both the image rms and peak are the RAW,
    # PB-attenuated values at the star's true (small but nonzero) offset
    # from the field phase centre. Correct both by the same factor (so the
    # reported SNR is unchanged but the absolute mJy values become the
    # true, PB-corrected flux/noise AT THE STAR), applied before both the
    # PNG title and the JSON summary are written, using the worst-case
    # (largest) correction across the epochs/MSes actually imaged -- in
    # every case checked so far in this survey the epochs share an almost
    # identical pointing (sub-arcsec to a few arcsec apart), so this is a
    # safe, conservative simplification rather than a per-pixel mosaic
    # correction.
    pb_correction = max(
        (1.0 / np.exp(-4 * np.log(2) * (off / pb) ** 2) for off, pb in ms_pb_info.values()),
        default=1.0)
    rms = rms * pb_correction
    peak = peak * pb_correction

    # Added 2026-08-30: the continuum image's effective centre frequency
    # (CASA/exportfits writes this to CRVAL3 for an MFS image) was
    # previously not carried into continuum_summary.json at all -- a real
    # gap flagged when Glenn asked for a frequency-range table for the
    # eventual write-up. Needed now, additionally, by the new population-
    # level anomaly check (population_anomaly_check.py), which needs the
    # actual observing frequency to compute the star's expected
    # photospheric flux via the Planck function.
    freq_center_hz = float(hdr.get('CRVAL3')) if hdr.get('CRVAL3') else None
    # Real RA/Dec sky-coordinate axes (WCSAxes, from the FITS header CASA's
    # exportfits already writes), not just a pixel/arcsec-offset grid --
    # the standard, publication-appropriate way to label a map. Field size
    # in arcsec is still noted in the title for a quick-look sense of scale.
    wcs = WCS(hdr).celestial
    fig = plt.figure(figsize=(7.5, 6.2))
    ax = fig.add_subplot(111, projection=wcs)
    im = ax.imshow(data * 1e3, origin='lower', cmap='inferno',
                   vmin=-3 * rms * 1e3, vmax=max(5 * rms * 1e3, peak * 1e3 * 0.9))
    plt.colorbar(im, ax=ax, label='mJy/beam')
    ny, nx = data.shape
    fov_arcsec = nx * CELL_ARCSEC
    ax.set_title(f'{STAR_NAME} continuum (line-excluded)\n'
                 f'rms={rms*1e3:.3f} mJy/beam, peak={peak*1e3:.3f} mJy/beam, '
                 f'FOV={fov_arcsec:.0f}″', fontsize=10)
    ax.coords[0].set_axislabel('Right Ascension (J2000)')
    ax.coords[1].set_axislabel('Declination (J2000)')
    ax.coords[0].set_major_formatter('hh:mm:ss.s')
    ax.coords[1].set_major_formatter('dd:mm:ss')
    ax.coords.grid(color='white', alpha=0.25, linestyle='dotted')
    plt.tight_layout()
    png_out = f'{PROD}/{safe_filename(STAR_NAME)}_continuum.png'
    plt.savefig(png_out, dpi=130)
    plt.close(fig)

    # ------------------------------------------- continuum-source detection
    # A "detection" requires BOTH statistical significance (peak >
    # CONT_SIG_THRESH x rms) AND spatial coincidence with the star's own
    # (proper-motion-corrected) phase-centre position -- a >5sigma peak
    # anywhere else in a ~256x256-pixel dirty image is not unusual by
    # chance alone (many independent beam areas per image) and is NOT
    # evidence of a real source at the target.
    CONT_SIG_THRESH = 5.0
    POS_TOL_ARCSEC = 3.0   # conservative; dirty image has no fitted clean
                           # beam to compare against (niter=0, no restore)
    iy, ix = np.unravel_index(np.nanargmax(data), data.shape)
    peak_offset_arcsec = float(np.hypot(ix - nx / 2.0, iy - ny / 2.0) * CELL_ARCSEC)
    peak_snr = float(peak / rms) if rms > 0 else float('nan')
    continuum_source_detected = bool(peak_snr > CONT_SIG_THRESH and
                                      peak_offset_arcsec < POS_TOL_ARCSEC)

    notes.append('')
    notes.append(f'Primary-beam correction applied: x{pb_correction:.4f} '
                 f'(worst-case star offset/FWHM among imaged epochs: '
                 f'{ {os.path.basename(k): v for k, v in ms_pb_info.items()} })')
    notes.append(f'Image rms: {rms*1e3:.4f} mJy/beam')
    notes.append(f'Image peak: {peak*1e3:.4f} mJy/beam (SNR={peak_snr:.2f})')
    notes.append(f'Peak position offset from phase centre: {peak_offset_arcsec:.2f} arcsec')
    notes.append(f'CONTINUUM SOURCE DETECTED: {continuum_source_detected} '
                 f'(requires peak SNR > {CONT_SIG_THRESH} AND offset < '
                 f'{POS_TOL_ARCSEC} arcsec of phase centre)')
    notes.append(f'FITS: {fits_out}')
    notes.append(f'PNG: {png_out}')
    notes.append(f'Runtime: {time.time()-t0:.0f} s')
    open(f'{PROD}/continuum_notes.txt', 'w').write('\n'.join(notes))
    # NOTE: rms/peak are numpy.float32 (from the FITS data array); numpy's
    # value-based scalar promotion can leave float32*python-float still as
    # float32, which json.dump cannot serialize -- cast everything to
    # native Python float/bool explicitly (bit us once already in a
    # one-off backfill script; fixing it here for real this time).
    json.dump(dict(star_name=STAR_NAME, image_rms_mJy=float(rms) * 1e3,
                    image_peak_mJy=float(peak) * 1e3, peak_snr=float(peak_snr),
                    peak_offset_arcsec=float(peak_offset_arcsec),
                    primary_beam_correction=float(pb_correction),
                    primary_beam_corrected=True,
                    continuum_source_detected=bool(continuum_source_detected),
                    sig_threshold=float(CONT_SIG_THRESH),
                    pos_tol_arcsec=float(POS_TOL_ARCSEC),
                    freq_center_Hz=freq_center_hz,
                    variability=variability),
              open(f'{PROD}/continuum_summary.json', 'w'), indent=1)

    # Population-level, spectral-type-normalised anomaly check (added
    # 2026-08-30, approach #2 alongside the closure-phase hit-vetting hook
    # in seti_drift_search_generic.py): run immediately, incrementally,
    # after every target's continuum measurement -- needs no additional
    # raw-data retention, just this target's own just-written
    # continuum_summary.json plus the running population state file.
    try:
        import subprocess
        subprocess.run(['python3', f'{os.path.dirname(os.path.abspath(__file__))}/population_anomaly_check.py',
                         TARGET_DIR, STAR_NAME], check=False)
    except Exception as e:
        print(f'[continuum_map] population_anomaly_check failed (non-fatal): {e}', flush=True)

    for ext in ('.image', '.psf', '.pb', '.residual', '.model', '.sumwt', '.mask'):
        shutil.rmtree(imname + ext, ignore_errors=True)

    print(f'[continuum_map] COMPLETE in {time.time()-t0:.0f}s -> {png_out}', flush=True)


if __name__ == '__main__':
    main()
