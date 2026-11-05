#!/usr/bin/env python3
r"""Fetcher, not a build generator: the two frozen inputs the LSR-frame
evaluation of the mask needs, so that the build makes no network call.

1.  LINES OF SIGHT AND SYSTEMIC VELOCITIES.  Every star that carries a
    threshold crossing, and every star of the primary (Class A) search, is
    resolved once at SIMBAD for its position and its heliocentric radial
    velocity.  The query string is `star_alias.designation()`, which is the
    project's own canonicalisation, so no hand table of query names exists
    to fall out of date.  The one target carried under an ALMA designation
    has no SIMBAD velocity and its Gaia position is already frozen in
    `r13inputs/almaid_r13.json`; it is READ from there.

2.  CARBON MONOXIDE ALONG EACH LINE OF SIGHT.  Spectra are cut from the
    moment-masked composite CO cube of Dame & Thaddeus (2022), which
    contains the Dame, Hartmann & Thaddeus (2001) survey, at the position
    of every star with a crossing.  Only the cut spectra are kept; the
    285 MB cube is read from its distribution zip and not unpacked.

    The cube is survey 5 of Table 3 of Dame & Thaddeus (2022): 146 velocity
    channels of 0.65 km/s covering +-47 km/s LSR, on a 0.25 deg rectilinear
    Galactic grid, main-beam brightness temperature, 8.4 arcmin beam,
    0.18 K rms per channel, moment-masked so that noise is set to zero.
    The all-sky Planck Commander CO(1-0) map (Planck Collaboration X 2016)
    is read at the same positions; it is smoothed to a 1 deg beam and
    carries no velocity information.

    python3 lsr_r15.py [--no-co] [--no-simbad]

-> r15inputs/losdir_r15.json, r15inputs/co_dht_r15.json,
   r15inputs/co_planck_r15.json
"""
from __future__ import annotations

import csv
import hashlib
import io
import json
import os
import sys
import time
import urllib.parse
import urllib.request
import zipfile

import numpy as np

import star_alias as sa

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, 'r15inputs')
CO_ZIP = os.path.join(HERE, '..', '..', 'referee_r15', 'co',
                      'DT22+DHT_masked.fits.zip')
CO_URL = ('https://lweb.cfa.harvard.edu/rtdc/CO/DameThaddeus22/'
          'DT22+DHT_masked.fits.zip')
PLANCK_URL = ('https://irsa.ipac.caltech.edu/data/Planck/release_2/'
              'all-sky-maps/maps/component-maps/foregrounds/'
              'COM_CompMap_CO-commander_0256_R2.00.fits')
SIMBAD = 'https://simbad.u-strasbg.fr/simbad/sim-script?script='


# ---------------------------------------------------------------- SIMBAD
def _simbad_raw(part):
    script = ('output console=off script=off\n'
              'format object f1 "%IDLIST(1)\t%COO(d;A)\t%COO(d;D)'
              '\t%OTYPE(S)\t%RV(V)\t%RV(R)\t%PLX(V)\t%PM(A)\t%PM(D)"\n'
              + ''.join('query id %s\n' % n for n in part))
    txt = urllib.request.urlopen(
        SIMBAD + urllib.parse.quote(script), timeout=120).read().decode()
    return [l for l in txt.splitlines() if l.count('\t') >= 4], txt


def _simbad_coo(ra, dec, radius='20s'):
    script = ('output console=off script=off\n'
              'format object f1 "%IDLIST(1)\t%COO(d;A)\t%COO(d;D)'
              '\t%OTYPE(S)\t%RV(V)\t%RV(R)\t%PLX(V)\t%PM(A)\t%PM(D)"\n'
              + 'query coo {:.6f} {:.6f} radius={} frame ICRS\n'.format(
                  ra, dec, radius))
    txt = urllib.request.urlopen(
        SIMBAD + urllib.parse.quote(script), timeout=120).read().decode()
    return [l for l in txt.splitlines() if l.count('\t') >= 4], txt


def simbad(names, chunk=20, hint=None):
    """Position, type and heliocentric radial velocity, one row per name.

    A batch whose row count does not match its query count is re-asked one
    name at a time, so that a name SIMBAD cannot resolve is NAMED rather
    than silently shifting every later row of the batch onto the wrong star.
    A name SIMBAD cannot parse at all is then re-asked BY POSITION, at the
    measured position of that star's own products, which is the key the rest
    of this project joins on; a planet row at the same position is skipped.
    """
    out, bad = {}, {}
    hint = hint or {}

    def take(n, line):
        f = [x.strip() for x in line.split('\t')]
        # SIMBAD prints "~" for a field it has no value for.
        g = lambda i: (float(f[i]) if i < len(f) and f[i]
                       and f[i] != '~' else None)
        out[n] = dict(query=n, simbad_id=f[0],
                      ra=g(1), dec=g(2), otype=f[3],
                      rv_kms=g(4),
                      rv_ref=(f[5] if len(f) > 5 and f[5] != '~' else None),
                      plx_mas=g(6), pmra_masyr=g(7), pmdec_masyr=g(8))

    for i in range(0, len(names), chunk):
        part = names[i:i + chunk]
        rows, txt = _simbad_raw(part)
        if len(rows) == len(part):
            for n, line in zip(part, rows):
                take(n, line)
        else:
            for n in part:
                r1, t1 = _simbad_raw([n])
                if len(r1) == 1:
                    take(n, r1[0])
                elif n in hint:
                    r2, t2 = _simbad_coo(*hint[n])
                    keep = [l for l in r2
                            if not l.split('\t')[3].strip().startswith(
                                'Planet')]
                    pick = ([l for l in keep
                             if l.split('\t')[4].strip() not in ('', '~')]
                            or keep)
                    if pick:
                        take(n, pick[0])
                        out[n]['query'] = '%s (resolved by position)' % n
                    else:
                        bad[n] = t2.strip().splitlines()[:3]
                else:
                    bad[n] = t1.strip().splitlines()[:3]
                time.sleep(0.3)
        time.sleep(1.0)
    return out, bad


def targets():
    """Every star this round must evaluate, as a canonical query string."""
    led = json.load(open(os.path.join(HERE, 'ledger.json'),
                         encoding='utf-8'))['rows']
    cat = list(csv.DictReader(open(
        os.path.join(HERE, 'per_target_results_v3.99.csv'), encoding='utf-8')))
    cross = {sa.designation(r['star'], tex=False) for r in led}
    classa = {sa.designation(r['star_name'], tex=False)
              for r in cat if r['search_class'] == 'A'}
    # The measured position of each star's own products, under the same
    # canonical designation, so that a name SIMBAD cannot parse can still
    # be resolved by where the telescope pointed.
    pb = json.load(open(os.path.join(HERE, 'pbcat_v408.json'),
                        encoding='utf-8'))
    hint = {}
    for k, v in pb.items():
        n = sa.designation(k.split('|')[0], tex=False)
        if v:
            hint.setdefault(n, (v[0]['star_ra'], v[0]['star_dec']))
    return cross, classa, hint


# ---------------------------------------------------------------- CO cube
def co_cube():
    """The masked composite cube, streamed from its zip; no unpacked copy."""
    if not os.path.exists(CO_ZIP):
        os.makedirs(os.path.dirname(CO_ZIP), exist_ok=True)
        with urllib.request.urlopen(CO_URL, timeout=900) as r, \
                open(CO_ZIP, 'wb') as fh:
            fh.write(r.read())
    md5 = hashlib.md5(open(CO_ZIP, 'rb').read()).hexdigest()
    z = zipfile.ZipFile(CO_ZIP)
    name = z.namelist()[0]
    fh = z.open(name)
    head = b''
    while b'END     ' not in head[-2880:] or len(head) == 0:
        b = fh.read(2880)
        assert b, 'header not terminated'
        head += b
        if b'END     ' in b:
            break
    hdr = {}
    s = head.decode('ascii')
    for i in range(0, len(s), 80):
        card = s[i:i + 80]
        if '=' in card[:10]:
            k = card[:8].strip()
            v = card[9:].split('/')[0].strip().strip("'").strip()
            hdr[k] = v
    return fh, hdr, md5, name


def co_extract(stars, box=1):
    """CO spectra at each direction, with a (2*box+1)^2 neighbourhood."""
    from astropy.coordinates import SkyCoord
    import astropy.units as u

    fh, hdr, md5, name = co_cube()
    nv, nl, nb = int(hdr['NAXIS1']), int(hdr['NAXIS2']), int(hdr['NAXIS3'])
    v0, dv, pv = (float(hdr['CRVAL1']), float(hdr['CDELT1']),
                  float(hdr['CRPIX1']))
    l0, dl, pl = (float(hdr['CRVAL2']), float(hdr['CDELT2']),
                  float(hdr['CRPIX2']))
    b0, db, pb = (float(hdr['CRVAL3']), float(hdr['CDELT3']),
                  float(hdr['CRPIX3']))
    scale, zero = float(hdr['BSCALE']), float(hdr['BZERO'])
    blank = int(float(hdr['BLANK']))
    vel = v0 + (np.arange(nv) + 1 - pv) * dv

    want = {}
    for k, (ra, dec) in stars.items():
        c = SkyCoord(ra * u.deg, dec * u.deg).galactic
        ll = c.l.deg
        ll = ll - 360.0 if ll > l0 + nl * dl else ll
        i = int(round((ll - l0) / dl + pl - 1))
        j = int(round((c.b.deg - b0) / db + pb - 1))
        want[k] = dict(l=ll, b=c.b.deg, il=i, ib=j, ra=ra, dec=dec)

    planes = {}
    for jb in sorted({w['ib'] + o for w in want.values()
                      for o in range(-box, box + 1)}):
        planes[jb] = None
    cur = -1
    raw = {}
    for jb in range(nb):
        buf = fh.read(nv * nl * 2)
        if jb in planes:
            raw[jb] = np.frombuffer(buf, dtype='>i2').reshape(nl, nv).copy()
    fh.close()

    out = {}
    for k, w in want.items():
        spec, grid = None, []
        for dj in range(-box, box + 1):
            for di in range(-box, box + 1):
                jb, il = w['ib'] + dj, w['il'] + di
                if jb not in raw or not (0 <= il < nl):
                    continue
                a = raw[jb][il].astype(float)
                m = raw[jb][il] == blank
                t = a * scale + zero
                t[m] = np.nan
                grid.append(t)
                if di == 0 and dj == 0:
                    spec = t
        assert spec is not None, k
        g = np.array(grid)
        cov = bool(np.isfinite(spec).any())
        rec = dict(w, covered=cov, vel_kms=[round(float(x), 4) for x in vel])
        if cov:
            t = np.nan_to_num(spec)
            tg = np.nan_to_num(np.nanmax(g, axis=0))
            rec.update(
                t_mb_K=[round(float(x), 4) for x in t],
                t_peak_K=float(t.max()),
                v_peak_kms=float(vel[int(np.argmax(t))]),
                w_co_K_kms=float(t.sum() * abs(dv)),
                t_peak_box_K=float(tg.max()),
                v_peak_box_kms=float(vel[int(np.argmax(tg))]),
                n_box=int(len(grid)))
        out[k] = rec
    return dict(
        _doc='CO(1-0) main-beam brightness temperature along each line of '
             'sight, cut from the moment-masked composite cube of Dame & '
             'Thaddeus (2022), which contains Dame, Hartmann & Thaddeus '
             '(2001).  Velocities are LSR.',
        source=dict(file=name, url=CO_URL, md5_zip=md5,
                    survey='Dame & Thaddeus (2022) Table 3 survey 5; '
                           'contains Dame, Hartmann & Thaddeus (2001)',
                    beam_arcmin=8.4, rms_K=0.18,
                    rms_src='Dame & Thaddeus (2022), Sec. 4',
                    moment_masked=True, grid_deg=abs(dl),
                    chan_kms=abs(dv), bunit=hdr.get('BUNIT'),
                    v_lo_kms=float(vel.min()), v_hi_kms=float(vel.max())),
        queried_utc=time.strftime('%Y-%m-%dT%H:%MZ', time.gmtime()),
        los=out)


def planck_extract(stars, radius_deg=0.25):
    """Velocity-integrated CO(1-0) from the Planck all-sky map.

    The CfA survey does not cover the whole sky, so the directions outside
    its footprint are also read from the Planck Commander CO(1-0) map
    (Planck Collaboration X 2016), which is all-sky but carries no
    velocity information.  Nside 256, 13.7 arcmin pixels, K_RJ km/s.
    Needs `astropy_healpix`, which only this fetcher imports.
    """
    from astropy.coordinates import SkyCoord
    from astropy.io import fits
    from astropy_healpix import HEALPix
    import astropy.units as u

    loc = os.path.join(os.path.dirname(CO_ZIP), os.path.basename(PLANCK_URL))
    if not os.path.exists(loc):
        with urllib.request.urlopen(PLANCK_URL, timeout=900) as r, \
                open(loc, 'wb') as fh:
            fh.write(r.read())
    md5 = hashlib.md5(open(loc, 'rb').read()).hexdigest()
    with fits.open(loc) as hd:
        h, dat = hd[1].header, hd[1].data
        col = [c for c in dat.columns.names if c.upper().startswith('I_')
               or c.upper() == 'INTENSITY'] or [dat.columns.names[0]]
        w = np.asarray(dat[col[0]], dtype=float).ravel()
        order = h.get('ORDERING', 'NESTED').strip().lower()
        nside = int(h['NSIDE'])
        unit = h.get('TUNIT1', '')
        fwhm = float(h.get('FWHM', 0.0))
    hp = HEALPix(nside=nside, order=order, frame='galactic')
    out = {}
    for k, (ra, dec) in stars.items():
        c = SkyCoord(ra * u.deg, dec * u.deg)
        i = int(hp.skycoord_to_healpix(c))
        near = hp.cone_search_skycoord(c, radius_deg * u.deg)
        out[k] = dict(ra=ra, dec=dec, pix=i, w_co=float(w[i]),
                      w_co_cone_max=float(np.max(w[np.asarray(near)]))
                      if len(near) else float(w[i]),
                      n_cone=int(len(near)))
    return dict(
        _doc='Velocity-integrated CO(1-0) from the Planck Commander '
             'component map, all-sky, no velocity information.',
        source=dict(file=os.path.basename(loc), url=PLANCK_URL, md5=md5,
                    column=col[0], nside=nside, ordering=order, unit=unit,
                    beam_arcmin=fwhm,
                    reference='Planck Collaboration X (2016), A&A 594, A10'),
        queried_utc=time.strftime('%Y-%m-%dT%H:%MZ', time.gmtime()),
        los=out)


def main(argv):
    os.makedirs(OUT, exist_ok=True)
    cross, classa, hint = targets()
    if '--no-simbad' not in argv:
        alma = json.load(open(os.path.join(HERE, 'r13inputs',
                                           'almaid_r13.json'),
                              encoding='utf-8'))
        ask = sorted(n for n in (cross | classa)
                     if n != alma['alma_designation'])
        d, bad = simbad(ask, hint=hint)
        assert not bad, bad
        d[alma['alma_designation']] = dict(
            query=alma['alma_designation'],
            simbad_id=alma['simbad_main_id'],
            ra=alma['gaia']['ra'], dec=alma['gaia']['dec'],
            otype=alma['otype'], rv_kms=None,
            pmra_masyr=alma['gaia']['pmra'],
            pmdec_masyr=alma['gaia']['pmdec'],
            rv_ref='none (no published radial velocity); '
                   'Gaia DR3 %d' % alma['gaia_dr3_source_id'],
            plx_mas=alma['gaia']['parallax'])
        json.dump(dict(
            _doc='Position and heliocentric radial velocity of every star '
                 'carrying a threshold crossing and every star of the '
                 'primary search, resolved at SIMBAD under '
                 'star_alias.designation().  Frozen so the build makes no '
                 'network call.',
            queried_utc=time.strftime('%Y-%m-%dT%H:%MZ', time.gmtime()),
            n_crossing_stars=len(cross), n_classa_stars=len(classa),
            unresolved=sorted(bad),
            crossing_stars=sorted(cross), classa_stars=sorted(classa),
            star=d), open(os.path.join(OUT, 'losdir_r15.json'), 'w'),
            indent=1, sort_keys=True)
        print('losdir_r15.json: %d stars' % len(d))
    if '--no-co' not in argv:
        d = json.load(open(os.path.join(OUT, 'losdir_r15.json'),
                           encoding='utf-8'))['star']
        pos = {k: (d[k]['ra'], d[k]['dec']) for k in sorted(cross)}
        json.dump(co_extract(pos),
                  open(os.path.join(OUT, 'co_dht_r15.json'), 'w'), indent=1)
        print('co_dht_r15.json: %d lines of sight' % len(pos))
        json.dump(planck_extract(pos),
                  open(os.path.join(OUT, 'co_planck_r15.json'), 'w'), indent=1)
        print('co_planck_r15.json: %d lines of sight' % len(pos))
    return 0


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
