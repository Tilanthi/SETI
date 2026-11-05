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


#: Inner control radius must clear this many synthesised-beam FWHM of the
#: star. PRE-SPECIFIED 2026-09-23, before any corrected extraction was run.
ANN_SYN_FACTOR = 2.0

#: SETI_PX=0 reproduces the pre-2026-09-26 barycentric behaviour bit-for-bit
#: (max difference 0.0 rad over 42 star-epochs). Kept as the A/B switch the
#: integration note asks for; the default is the repair. What was actually
#: applied is written into the product as `pos_convention`, so a product can
#: never claim a convention it did not use.
PX_ON = os.environ.get('SETI_PX', '1') != '0'
PX_CONV = ('apparent_topocentric_2026-09-26' if PX_ON
           else 'barycentric_legacy_SETI_PX=0')


def array_geometry():
    """True dish diameter and maximum projected baseline, read from the MS.

    Referee 2 (M3): the control annulus was previously built from a
    hard-coded 12 m primary beam for EVERY window. For ACA 7 m data that
    placed the annulus at 7/12 = 58 per cent of the correct radius, putting
    the inner controls inside the synthesised main lobe, where they collect
    the star's own flux and are not independent of it. Both quantities now
    come from the data itself rather than from a constant.
    """
    from casatools import table
    tb = table()
    tb.open(MS + '/ANTENNA')
    diam = tb.getcol('DISH_DIAMETER')
    tb.close()
    dish = float(np.median(diam)) if diam.size else ALMA_DISH_M
    if not (3.0 < dish < 30.0):
        dish = ALMA_DISH_M
    tb.open(MS)
    uvw = tb.getcol('UVW')
    tb.close()
    bmax = float(np.max(np.hypot(uvw[0], uvw[1]))) if uvw.size else 0.0
    return dish, bmax


def primary_beam_arcsec(freq_hz, dish_m=None):
    """FWHM of a single ALMA dish's primary beam at freq_hz,
    theta_PB = 1.22 lambda / D, for the dish that actually observed."""
    wavelength_m = C_M_S / freq_hz
    return np.degrees(1.22 * wavelength_m /
                      (ALMA_DISH_M if dish_m is None else dish_m)) * 3600.0


def synth_beam_arcsec(freq_hz, bmax_m):
    """Approximate synthesised-beam FWHM from the longest projected
    baseline, theta_syn = 1.22 lambda / B_max."""
    if not bmax_m:
        return 0.0
    return np.degrees(1.22 * (C_M_S / freq_hz) / bmax_m) * 3600.0


def probe_positions(pb_arcsec, seed=20260825, syn_arcsec=0.0):
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
    # Inner edge: 0.14 theta_PB as before, but never inside
    # ANN_SYN_FACTOR synthesised beams of the star, so no control position
    # sits on the star's own main lobe (referee 2, M3).
    ann_lo = 0.14 * pb_arcsec
    if syn_arcsec:
        ann_lo = max(ann_lo, ANN_SYN_FACTOR * syn_arcsec)
    ann_hi = 0.78 * pb_arcsec                             # stays inside the PB
    if ann_lo >= 0.9 * ann_hi:
        raise SystemExit(
            f'[{EB}] FATAL: synthesised beam {syn_arcsec:.2f}" leaves no '
            f'usable control annulus inside the primary beam '
            f'({ann_lo:.2f}"-{ann_hi:.2f}"); this window cannot carry a '
            f'spatial control screen')
    n_probe = 512
    rr = np.sqrt(rng.uniform(ann_lo**2, ann_hi**2, n_probe))
    th = rng.uniform(0, 2 * np.pi, n_probe)
    for k in range(n_probe):
        names.append(f'probe_{k}')
        dl.append(rr[k] * np.cos(th[k])); dm.append(rr[k] * np.sin(th[k]))
    return names, np.array(dl), np.array(dm), n_src


def star_lm(phase_ra, phase_dec, mjd_sec):
    """Direction cosines of the target star's APPARENT (topocentric) position
    relative to the MS phase centre: Gaia proper motion to the observation
    epoch PLUS the annual parallax, which the pre-2026-09-26 version omitted
    (DECISIONS_R8 D6.1; referee_r8/ROSS154_AND_SCALE.md Sec. 1,
    referee_r8/parallax/INTEGRATE_ME.md).

    `SkyCoord.apply_space_motion()` returns a BARYCENTRIC direction; the
    visibilities see the apparent one. The difference is up to the star's full
    parallax, and a compact source phase-rotated to the wrong position loses
    amplitude by the normalised dirty beam at that offset and leaks into the
    imaginary part -- 1.0000 against 0.8385 for AU Mic in the reference
    experiment, which reproduces its observed 16 per cent deficit from
    geometry alone.

    The third return value stays the BARYCENTRIC SkyCoord on purpose: it is
    written into the products as `t1_ra`/`t1_dec` and two analysis scripts read
    those keys as the barycentric position. The correction is recorded as
    separate `plx_*` keys plus a `pos_convention` flag instead (see main()).
    Aberration and light deflection are deliberately excluded -- they are
    common to the whole arcsecond field and cancel against the phase centre.
    """
    from star_lm_apparent import star_lm_apparent
    # SETI_PX=0 reproduces the pre-repair barycentric behaviour bit-for-bit
    # (verified, max difference 0.0 rad over 42 star-epochs). Kept as the A/B
    # switch the integration note asks for; the default is the repair.
    return star_lm_apparent(phase_ra, phase_dec, mjd_sec, STAR,
                            include_parallax=PX_ON)


# ------------------------------------------------------- on-source time (D3)
def on_source_time(times, expos=None):
    """On-source integration time of a set of integration timestamps.

    THE ONE COMPUTATION, used by the extractor and by the search's
    `result.json` writer (round 8, D3). The previous estimator was
    ``n_int * median(diff(times))``, which assumes every integration has
    the same length. Four released blocks (HD 10647 / HD 139664 B6) violate
    that: 18 of their 86 integrations are 0.576 s sub-scan-boundary partial
    dumps against a 6.048 s median, so the estimator returned 520.1 s for a
    block whose timestamps span 418.0 s -- an overstatement of 23 per cent.

    * With `expos` (the MS's own EXPOSURE column, per integration) the
      answer is exact: the sum of the integrations' own durations.
    * Without it -- for products already written -- each gap is capped at
      the modal integration length, which cannot exceed the true duration
      and reduces EXACTLY to the old formula when sampling is uniform
      (sum(min(d, dn)) + dn == n_int * dn), so no uniformly sampled block's
      published number moves.

    Deliberately NOT clipped to the wall-clock span: a span is not an
    integration time and clipping would hide the cause rather than fix it.
    """
    if expos is not None:
        expos = np.asarray(expos, dtype=float)
        if expos.size and np.all(np.isfinite(expos)) and np.all(expos > 0):
            return float(expos.sum())
    times = np.asarray(times, dtype=float)
    if times.size < 2:
        return 0.0
    d = np.diff(times)
    dn = float(np.median(d))
    return float(np.minimum(d, dn).sum() + dn)


# --------------------------------------------------------------- MS metadata
#: A field whose phase centre is within this fraction of the primary-beam
#: FWHM of the reference field's is the SAME POINTING, recorded as several
#: FIELD rows (which ALMA does routinely, one row per scan group or per
#: ephemeris update). 34 of the 42 blocks damaged by the old single-field
#: selection are of this kind: there is no mosaic to choose a pointing from.
FIELD_SAME_POS_FRAC = 0.1
#: A genuinely offset pointing is still worth combining while the primary
#: beam delivers at least this fraction of its peak response at the star.
#: Below it the field is a different patch of sky (or a calibrator, which
#: sits degrees away and scores ~0).
FIELD_MIN_PB_RESP = 0.05
_FIELD_SPLIT_DONE = False


def _pb_response(off_arcsec, pb_arcsec):
    """Gaussian primary-beam power response at an offset from the pointing."""
    if pb_arcsec <= 0:
        return 0.0
    return float(np.exp(-4.0 * np.log(2.0) * (off_arcsec / pb_arcsec) ** 2))


def _select_in_beam_fields_ms(ms_path, field_ids, times, freqs):
    """Split out EVERY field that actually sees the star, not just one.

    Replaces `_select_best_field_ms` (2026-08-28 -- 2026-09-26). That
    function kept the single field whose phase centre was nearest the star
    and discarded the rest, on the premise that a >1-FIELD_ID MS is a
    mosaic whose best pointing must be chosen. **The premise is wrong for
    81 per cent of the blocks it fired on**: they are one pointing written
    as several FIELD rows, so it kept one scan group and threw the others
    away. Measured cost (referee_r8/FIELD_TRUNCATION_LEDGER.md): 42 released
    blocks, 171 of 1,655 windows, 19.1-19.6 h of ~30 h of available in-beam
    on-source time, a median 1.73x flux penalty in those windows. It was
    invisible because nothing logged it -- the affected blocks' duty cycle
    (0.857) looks like everyone else's (0.823).

    What this does instead:

    1. Measures each field's offset from the star, its primary-beam
       response at the star, and **its own on-source time** (the old
       selector was blind to integration time, which is how five Proxima
       blocks and one HR 1010 block came to retain a 60.5 s field while a
       ~2,900 s sibling field in the same block was discarded).
    2. Picks the REFERENCE field by largest effective weight A^2 t -- the
       quantity that actually sets a point source's S/N -- not by position
       alone. The reference fixes the flux convention, so a block whose
       reference is the field the old code chose keeps its published flux
       scale exactly.
    3. Keeps every field that is the same pointing as the reference
       (<= FIELD_SAME_POS_FRAC of the beam away) AND every genuinely offset
       pointing still delivering >= FIELD_MIN_PB_RESP at the star. The
       offset ones are primary-beam weighted downstream, not counted equal.
    4. **Logs, and writes to JSON, the retained against the discarded
       on-source time.** A selection that discards data must say how much.

    Where only one field sees the star -- 192 of the 294 blocks that reach
    here, every other field being a calibrator degrees away -- the returned
    MS is identical to what the old code produced, so those blocks carry no
    regression risk.
    """
    from casatools import table
    from casatasks import mstransform
    import shutil
    tb = table()
    tb.open(ms_path + '/FIELD')
    all_pc = tb.getcol('PHASE_DIR')[:, 0, :]
    try:
        all_nm = list(tb.getcol('NAME'))
    except Exception:
        all_nm = []
    tb.close()
    tb.open(ms_path)
    frow = tb.getcol('FIELD_ID')
    trow = tb.getcol('TIME')
    try:
        erow = tb.getcol('EXPOSURE')
    except Exception:
        erow = None
    tb.close()

    dish_m, _ = array_geometry()
    pb_arcsec = primary_beam_arcsec(float(np.median(freqs)), dish_m)
    mjd_sec = float(np.median(times))

    info = {}
    for fid in field_ids:
        fid = int(fid)
        pra, pdec = float(all_pc[0, fid]), float(all_pc[1, fid])
        l, m, _ = star_lm(pra, pdec, mjd_sec)
        off = float(np.hypot(l, m) / ARCSEC)
        sel = (frow == fid)
        tu, first = np.unique(trow[sel], return_index=True)
        if erow is not None:
            t_on = on_source_time(tu, erow[sel][first])
        else:
            t_on = on_source_time(tu)
        info[fid] = dict(
            field_id=fid, name=(all_nm[fid] if fid < len(all_nm) else ''),
            ra_rad=pra, dec_rad=pdec, offset_arcsec=off,
            pb_resp=_pb_response(off, pb_arcsec),
            n_int=int(len(tu)), on_source_s=float(t_on),
            span_s=float(tu[-1] - tu[0]) if len(tu) > 1 else 0.0)
        info[fid]['eff_weight'] = info[fid]['pb_resp'] ** 2 * t_on

    # ---- reference field: largest A^2 t among the fields that see the star
    cand = [f for f, d in info.items() if d['pb_resp'] >= FIELD_MIN_PB_RESP]
    if not cand:          # nothing in the beam: fall back to nearest, as before
        cand = [min(info, key=lambda f: info[f]['offset_arcsec'])]
    ref = max(cand, key=lambda f: (info[f]['eff_weight'],
                                   -info[f]['offset_arcsec']))
    rra, rdec = info[ref]['ra_rad'], info[ref]['dec_rad']

    keep = []
    for fid, d in sorted(info.items()):
        dra = (d['ra_rad'] - rra) * np.cos(rdec)
        sep = float(np.hypot(dra, d['dec_rad'] - rdec) / ARCSEC)
        d['sep_from_ref_arcsec'] = sep
        if fid == ref:
            d['verdict'] = 'reference'
        elif sep <= FIELD_SAME_POS_FRAC * pb_arcsec:
            d['verdict'] = 'kept_same_pointing'
        elif d['pb_resp'] >= FIELD_MIN_PB_RESP:
            d['verdict'] = 'kept_offset_pointing'
        elif d['pb_resp'] > 1e-6:
            d['verdict'] = 'discarded_beam_edge'
        else:
            d['verdict'] = 'discarded_off_source'
        if d['verdict'] == 'reference' or d['verdict'].startswith('kept'):
            keep.append(fid)

    kept_s = sum(info[f]['on_source_s'] for f in keep)
    disc_s = sum(d['on_source_s'] for f, d in info.items() if f not in keep)
    disc_in = sum(d['on_source_s'] for f, d in info.items()
                  if f not in keep and d['pb_resp'] >= 0.5)
    aref = info[ref]['pb_resp'] or 1.0
    eff_s = sum(info[f]['on_source_s'] * (info[f]['pb_resp'] / aref) ** 2
                for f in keep)

    for fid, d in sorted(info.items()):
        print(f'[{EB}] field {fid:>3d} {str(d["name"])[:18]:<18} '
              f'off {d["offset_arcsec"]:9.2f}" A {d["pb_resp"]:.3f} '
              f'{d["n_int"]:5d} int {d["on_source_s"]:8.1f} s  {d["verdict"]}',
              flush=True)
    print(f'[{EB}] FIELDSEL pb {pb_arcsec:.2f}" ref field {ref}: '
          f'keeping {len(keep)} of {len(info)} fields, '
          f'RETAINED {kept_s:.1f} s on-source '
          f'(effective {eff_s:.1f} s at the reference response), '
          f'DISCARDED {disc_s:.1f} s of which {disc_in:.1f} s was inside the '
          f'half-power point', flush=True)
    if disc_in > 0.5:
        print(f'[{EB}] FIELDSEL WARNING: {disc_in:.1f} s of in-beam on-source '
              f'time is being discarded -- this is the round-8 defect and '
              f'should be zero', flush=True)

    os.makedirs(f'{TARGET_DIR}/products', exist_ok=True)
    try:
        with open(f'{TARGET_DIR}/products/{EB}{_SFX}_fieldsel.json', 'w') as fh:
            json.dump(dict(eb=EB, sfx=_SFX, star=STAR_NAME,
                           pb_arcsec=pb_arcsec, dish_m=dish_m,
                           ref_field=ref, kept_fields=keep,
                           retained_on_source_s=kept_s,
                           retained_effective_s=eff_s,
                           discarded_on_source_s=disc_s,
                           discarded_in_beam_s=disc_in,
                           fields=[info[f] for f in sorted(info)]), fh, indent=1)
    except Exception as exc:                       # never fail a run on a log
        print(f'[{EB}] FIELDSEL could not write json: {exc}', flush=True)

    tag = '_'.join(str(f) for f in keep)
    if len(tag) > 40:
        tag = f'{ref}_plus{len(keep) - 1}'
    out_ms = f'{TARGET_DIR}/work/{EB}{_SFX}_field{tag}.ms'
    os.makedirs(f'{TARGET_DIR}/work', exist_ok=True)
    shutil.rmtree(out_ms, ignore_errors=True)
    mstransform(vis=ms_path, outputvis=out_ms,
                field=','.join(str(f) for f in keep),
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
    fieldrow = tb.getcol('FIELD_ID')
    try:
        exprow = tb.getcol('EXPOSURE')
    except Exception:
        exprow = None
    field_ids = np.unique(fieldrow)
    tb.close()
    global _FIELD_SPLIT_DONE
    if len(field_ids) != 1 and not _FIELD_SPLIT_DONE:
        MS = _select_in_beam_fields_ms(MS, field_ids, times, freqs)
        _FIELD_SPLIT_DONE = True
        return ms_meta()
    # Every field still present now belongs in the search. Read each one's
    # own phase centre: the direction cosines of the star -- and therefore
    # the DFT phase and the probe grid -- are field-dependent, which is the
    # reason the old code could only handle one field at a time.
    tb.open(MS + '/FIELD')
    all_pc = tb.getcol('PHASE_DIR')[:, 0, :]
    tb.close()
    pc_by_field = {int(f): all_pc[:, int(f)].copy() for f in field_ids}
    return freqs, chanw, pc_by_field, times, nrow, fieldrow, exprow


def integration_blocks(times, fields=None, expos=None):
    """Contiguous row ranges sharing one timestamp -- and one FIELD_ID.

    A block must not straddle two fields: each field has its own phase
    centre, so the DFT kernel differs. ALMA never points two ways at once,
    so (TIME, FIELD_ID) groups are contiguous in a time-ordered MS; that is
    asserted rather than assumed.
    """
    d = np.diff(times)
    if np.any(d < -1e-6):
        raise RuntimeError('MS is not time-ordered')
    chg = np.abs(d) > 1e-6
    if fields is not None:
        chg = chg | (np.diff(np.asarray(fields, dtype=np.int64)) != 0)
    edges = np.flatnonzero(chg) + 1
    starts = np.concatenate(([0], edges))
    stops = np.concatenate((edges, [len(times)]))
    if fields is not None:
        fields = np.asarray(fields, dtype=np.int64)
        fld = fields[starts]
        # contiguity check: one block per distinct (time, field) pair
        key = np.unique(np.stack([times, fields.astype(float)]), axis=1)
        if key.shape[1] != len(starts):
            raise RuntimeError(
                f'(TIME, FIELD_ID) groups are not contiguous: '
                f'{key.shape[1]} distinct pairs but {len(starts)} row blocks '
                f'-- the MS needs sorting before extraction')
    else:
        fld = np.zeros(len(starts), dtype=np.int64)
    if expos is not None:
        expos = np.asarray(expos, dtype=float)
        ex = np.array([float(np.median(expos[a:b])) for a, b in zip(starts, stops)])
    else:
        ex = None
    return starts, stops, times[starts], fld, ex


# ------------------------------------------------------------------- worker
_G = {}


def _init(freqs, lm, msname, star_lm_, inject, has_wspec, arel=None):
    _G['freqs'] = freqs
    _G['lm'] = lm                 # {field_id: (l_array, m_array)}
    _G['ms'] = msname
    _G['star_lm'] = star_lm_      # {field_id: (l_star, m_star)}
    _G['inject'] = inject
    _G['has_wspec'] = has_wspec
    _G['arel'] = arel or {}       # {field_id: A_field / A_reference}


def _do_block(args):
    from casatools import table
    i0, i1, idx, tsec, fid = args
    freqs = _G['freqs']; l, m = _G['lm'][fid]
    arel = float(_G['arel'].get(fid, 1.0))
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
            ls, ms_ = _G['star_lm'][fid]
            ph = (-2j * np.pi * freqs[ich] / C_M_S) * (uvw[0] * ls + uvw[1] * ms_)
            # Attenuate the injected carrier by THIS pointing's primary-beam
            # response relative to the reference field, so an injected tone
            # behaves like a real source at the star and is recovered at the
            # same flux from every pointing. A no-op (arel == 1) for
            # single-pointing blocks, i.e. for every injection campaign run
            # before 2026-09-26.
            dat[:, ich, :] += (amp * arel *
                               np.exp(ph)).astype(np.complex64)[None, :]

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
    # Put every pointing on the REFERENCE field's flux scale and give it the
    # weight it deserves. A pointing offset from the star sees it attenuated
    # by A_field, so I_field measures A_field * S: dividing by A_rel =
    # A_field/A_ref makes every field measure A_ref * S (the published
    # convention, unchanged for the reference field), and scaling the weight
    # by A_rel^2 makes the downstream inverse-variance combination the
    # optimal linear mosaic estimator. Both of the search's noise estimates
    # follow automatically: sigma_theory = 1/sqrt(W) scales as 1/A_rel, and
    # the empirical MAD over control probes scales the same way because the
    # controls live in the same scaled map.
    if arel != 1.0:
        out /= arel
        wsum = wsum * (arel ** 2)
    return idx, out, wsum.astype(np.float32)


def main():
    t_start = time.time()
    freqs, chanw, pc_by_field, times, nrow, fieldrow, exprow = ms_meta()
    starts, stops, tstamps, fldblk, expblk = integration_blocks(
        times, fieldrow, exprow)
    nint = len(starts)
    dish_m, bmax_m = array_geometry()
    fmed = float(np.median(freqs))
    pb_arcsec = primary_beam_arcsec(fmed, dish_m)
    syn_arcsec = synth_beam_arcsec(fmed, bmax_m)
    print(f'[{EB}] {nrow} rows, {nint} integrations, {len(freqs)} channels, '
          f'chanwidth {chanw/1e3:.2f} kHz, {freqs[0]/1e9:.4f}-{freqs[-1]/1e9:.4f} GHz, '
          f'primary beam FWHM {pb_arcsec:.2f}"', flush=True)
    print(f'[{EB}] array: {dish_m:.0f} m dish, B_max {bmax_m:.0f} m, '
          f'synthesised beam {syn_arcsec:.2f}", inner control radius '
          f'{max(0.14*pb_arcsec, ANN_SYN_FACTOR*syn_arcsec):.2f}"', flush=True)

    # Per-field geometry. One pointing is the REFERENCE: it carries the flux
    # convention and A_rel = 1, so a single-pointing block behaves exactly as
    # before. The reference is the field with the largest effective weight
    # A^2 t among those actually present, matching the choice made at split
    # time (and recomputed here so that the two cannot silently disagree).
    tmid = float(np.mean(tstamps))
    geom = {}
    for fid, p in sorted(pc_by_field.items()):
        l_f, m_f, csky = star_lm(float(p[0]), float(p[1]), tmid)
        off_f = float(np.hypot(l_f, m_f) / ARCSEC)
        t_f = on_source_time(tstamps[fldblk == fid],
                            None if expblk is None else expblk[fldblk == fid])
        geom[fid] = dict(pc=p, l=l_f, m=m_f, off=off_f,
                         A=_pb_response(off_f, pb_arcsec), t_on=t_f)
        geom[fid]['eff'] = geom[fid]['A'] ** 2 * t_f
    ref = max(geom, key=lambda f: (geom[f]['eff'], -geom[f]['off']))
    a_ref = geom[ref]['A'] or 1.0
    arel = {f: (g['A'] / a_ref) for f, g in geom.items()}
    pc = geom[ref]['pc']
    l_star, m_star = geom[ref]['l'], geom[ref]['m']
    _, _, csky = star_lm(float(pc[0]), float(pc[1]), tmid)
    on_source_s = on_source_time(tstamps, expblk)
    # D6.1: record the annual-parallax term the pre-repair extractor omitted.
    # The reason it survived seven referee rounds is that nothing recorded the
    # quantity -- the same failure mode as the field truncation. `t1_ra`/
    # `t1_dec` keep their barycentric meaning; these are new keys.
    from star_lm_apparent import star_lm_report
    rep = star_lm_report(float(pc[0]), float(pc[1]), tmid, STAR,
                         syn_arcsec=syn_arcsec)
    if not PX_ON:      # the switch is off: report zero, and say so
        for _k in ('plx_dl_arcsec', 'plx_dm_arcsec', 'plx_offset_arcsec',
                   'plx_offset_beams'):
            if _k in rep:
                rep[_k] = 0.0
        rep['loss_gaussian'] = 1.0
        rep['l_app_arcsec'] = rep['l_bary_arcsec']
        rep['m_app_arcsec'] = rep['m_bary_arcsec']
    print(f'[{EB}] parallax term dl={rep["plx_dl_arcsec"]:+.4f}" '
          f'dm={rep["plx_dm_arcsec"]:+.4f}" '
          f'|d|={rep["plx_offset_arcsec"]:.4f}" = '
          f'{rep.get("plx_offset_beams", float("nan")):.3f} synthesised beams '
          f'(Gaussian amplitude retained '
          f'{rep.get("loss_gaussian", float("nan")):.4f}) -- APPLIED, '
          f'pos_convention={PX_CONV}', flush=True)

    print(f'[{EB}] phase centre  RA={np.degrees(pc[0])%360:.6f} '
          f'Dec={np.degrees(pc[1]):.6f}', flush=True)
    print(f'[{EB}] {STAR_NAME} at RA={csky.ra.deg:.6f} Dec={csky.dec.deg:.6f} '
          f'-> offset l={l_star/ARCSEC:+.3f}" m={m_star/ARCSEC:+.3f}"', flush=True)
    if len(geom) > 1:
        for fid, g in sorted(geom.items()):
            print(f'[{EB}] searching field {fid:>3d} off {g["off"]:7.2f}" '
                  f'A {g["A"]:.3f} A_rel {arel[fid]:.3f} '
                  f'{int((fldblk == fid).sum()):5d} int {g["t_on"]:8.1f} s'
                  f'{"   <- reference" if fid == ref else ""}', flush=True)
        eff_tot = sum(g['t_on'] * arel[f] ** 2 for f, g in geom.items())
        print(f'[{EB}] MULTI-FIELD SEARCH: {len(geom)} pointings, '
              f'{on_source_s:.1f} s on-source, {eff_tot:.1f} s effective at '
              f'the reference response, expected S/N gain over the reference '
              f'field alone x{np.sqrt(eff_tot / max(geom[ref]["t_on"], 1e-9)):.2f}',
              flush=True)
    print(f'[{EB}] on-source {on_source_s:.2f} s over a span of '
          f'{float(tstamps[-1] - tstamps[0]):.2f} s '
          f'({"EXPOSURE" if expblk is not None else "timestamps"})', flush=True)

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

    names, dl, dm, n_src = probe_positions(pb_arcsec, syn_arcsec=syn_arcsec)
    lam = l_star + dl * ARCSEC
    mam = m_star + dm * ARCSEC
    # The probe grid is defined as offsets from the STAR, so the same physical
    # sky positions are evaluated in every pointing -- each field simply needs
    # its own direction cosines for them.
    lm_by_field = {f: (g['l'] + dl * ARCSEC, g['m'] + dm * ARCSEC)
                   for f, g in geom.items()}
    starlm_by_field = {f: (g['l'], g['m']) for f, g in geom.items()}

    from casatools import table as _tbl
    _t = _tbl(); _t.open(MS, nomodify=True)
    has_wspec = 'WEIGHT_SPECTRUM' in _t.colnames(); _t.close()
    print(f'[{EB}] WEIGHT_SPECTRUM present: {has_wspec}', flush=True)

    import multiprocessing as mp
    ctx = mp.get_context('fork')
    t0ref = float(tstamps[0])
    tasks = [(int(starts[i]), int(stops[i]), i, float(tstamps[i]) - t0ref,
              int(fldblk[i])) for i in range(nint)]
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
                  initargs=(freqs, lm_by_field, MS,
                            starlm_by_field, inject, has_wspec, arel)) as pool:
        done = 0
        for idx, blk, wsum in pool.imap_unordered(_do_block, tasks, chunksize=1):
            I[idx] = blk; W[idx] = wsum
            done += 1
            if done % 50 == 0:
                print(f'[{EB}]   {done}/{nint} integrations '
                      f'({time.time()-t_start:.0f} s)', flush=True)

    # Round-8 additions, written into BOTH products: the per-integration
    # exposure (so on-source time is the sum of the integrations' own
    # durations, not a count times a median -- D3), and the field each
    # integration came from with its relative primary-beam weight (so the
    # multi-pointing combination is auditable after the fact -- D2).
    extra = dict(
        expos=(np.zeros(0) if expblk is None else expblk.astype(np.float64)),
        field_id=fldblk.astype(np.int32),
        pb_resp_rel=np.array([arel[int(f)] for f in fldblk], dtype=np.float64),
        on_source_s=float(on_source_s),
        ref_field=int(ref), n_fields=int(len(geom)),
        field_ids=np.array(sorted(geom), dtype=np.int32),
        field_on_source_s=np.array([geom[f]['t_on'] for f in sorted(geom)]),
        field_offset_arcsec=np.array([geom[f]['off'] for f in sorted(geom)]),
        field_pb_resp=np.array([geom[f]['A'] for f in sorted(geom)]),
        extract_version='r8-multifield-parallax-20260926',
        # D6.1, recorded not merely applied. `pos_convention` is the flag that
        # lets a later consumer tell a repaired product from a legacy one with
        # no re-derivation; absence of the key means 'barycentric_legacy'.
        pos_convention=PX_CONV,
        plx_dl_arcsec=rep['plx_dl_arcsec'],
        plx_dm_arcsec=rep['plx_dm_arcsec'],
        plx_offset_arcsec=rep['plx_offset_arcsec'],
        plx_offset_beams=rep.get('plx_offset_beams', np.nan),
        plx_loss_gaussian=rep.get('loss_gaussian', np.nan),
        l_bary_arcsec=rep['l_bary_arcsec'], m_bary_arcsec=rep['m_bary_arcsec'],
        l_app_arcsec=rep['l_app_arcsec'], m_app_arcsec=rep['m_app_arcsec'])

    np.savez_compressed(
        OUT, I=I, W=W, times=tstamps, freqs=freqs, chanw=chanw,
        names=np.array(names), dl=dl, dm=dm, n_src=n_src,
        phase_ra=pc[0], phase_dec=pc[1], l_star=l_star, m_star=m_star,
        pb_arcsec=pb_arcsec, dish_m=dish_m, bmax_m=bmax_m,
        syn_arcsec=syn_arcsec, ann_syn_factor=ANN_SYN_FACTOR,
        star_name=STAR_NAME,
        t1_ra=csky.ra.deg, t1_dec=csky.dec.deg,
        parallax=STAR['parallax'], parallax_err=STAR['parallax_err'], **extra)
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
        pb_arcsec=pb_arcsec, dish_m=dish_m, bmax_m=bmax_m,
        syn_arcsec=syn_arcsec, ann_syn_factor=ANN_SYN_FACTOR,
        star_name=STAR_NAME,
        t1_ra=csky.ra.deg, t1_dec=csky.dec.deg,
        parallax=STAR['parallax'], parallax_err=STAR['parallax_err'], **extra)
    print(f'[{EB}] retained star-only raw spectrum for future ML/anomaly-'
          f'detection follow-up -> {SRC_OUT} '
          f'({os.path.getsize(SRC_OUT)/1e6:.1f} MB, vs '
          f'{os.path.getsize(OUT)/1e6:.0f} MB for the full multi-control '
          f'waterfall that will shortly be deleted)', flush=True)


if __name__ == '__main__':
    main()
