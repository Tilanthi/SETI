"""Apparent (topocentric) stellar direction cosines for ALMA visibility work.

WHY THIS MODULE EXISTS
----------------------
`seti_extract_generic.star_lm()` -- and its verbatim copies in `visfit_r7x.py`,
`visfit_r7y.py`, `step2_extract.py` and `continuum_map_generic.py` -- propagate
the Gaia catalogue position to the observation epoch with

    SkyCoord(...).apply_space_motion(epoch_obs)

and then take `c.ra`, `c.dec` as the direction to phase-rotate to.  That is the
star's **barycentric** direction at that date: `apply_space_motion()` moves the
star along its space-motion track in the BCRS, it does not place an observer
anywhere.  The visibilities, however, record the direction of the wavefront as
seen **from the observatory**, which differs from the barycentric direction by
the annual (plus diurnal) parallax -- up to the full parallax of the star.  It
is precisely the term VLBI astrometry uses to measure parallaxes.

Consequence: the extractor phase-rotates to a position displaced from the star's
true apparent position, and a compact source measured off-position loses
amplitude by the value of the normalised dirty beam at that offset, while
leaking signal into the imaginary part.  Diagnosed and quantified in
`/workspace/SETI/referee_r8/ROSS154_AND_SCALE.md`; decided in
`/workspace/SETI/referee_r8/DECISIONS_R8.md` D6.

The term does *not* cancel against the phase centre.  Aberration and light
deflection do cancel to well below a milliarcsecond, because they are common to
every direction within an arcsecond-scale field; parallax does not, because it
depends on the source distance and the phase centre is a catalogue direction at
infinity.  Aberration is therefore deliberately **excluded** here.

WHAT THIS MODULE PROVIDES
-------------------------
    star_lm_apparent(phase_ra, phase_dec, mjd_sec, star, ...) -> (l, m, c_bary)
        Drop-in replacement for the four `star_lm()` copies.  Same argument
        order, same radian units, same return arity.  `c_bary` is still the
        BARYCENTRIC SkyCoord at epoch, deliberately unchanged, so that the
        `t1_ra` / `t1_dec` columns written into `*_srcspec.npz` keep the
        meaning every downstream consumer already assumes.

    make_star_lm(star, ...) -> callable(phase_ra, phase_dec, mjd_sec)
        Closure for the two call sites whose `star_lm()` reads a module global
        (`seti_extract_generic.STAR`, `step2_extract.T1`) instead of taking a
        star dict.

    parallax_offset(star, mjd_sec, ...) -> (dl, dm) in RADIANS
        The omitted displacement itself (apparent minus barycentric), for
        recording alongside the position and for the per-window loss ledger.

    star_lm_report(...) -> dict
        Everything at once, in arcseconds, for logging / provenance.

No free parameter enters anywhere: the displacement follows from the stored
Gaia astrometry, the observation timestamp and the site.

VALIDATION: `test_star_lm_apparent.py` in this directory.  Every check is run
against BOTH this implementation and a verbatim copy of the shipped one, and
the test fails unless the shipped one *fails* the checks this one passes.
"""

import numpy as np

ARCSEC = np.pi / 180.0 / 3600.0
AU_M = 1.49597870700e11

# ALMA array reference position.  Geodetic values as used elsewhere in this
# project (`/data/SETI/mmvar/par1.py`); agrees with CASA's observatory table
# for ALMA to a few metres, i.e. to ~1e-4 mas of diurnal parallax for the
# nearest star in the sample.  `site=None` selects this.
ALMA_GEODETIC = dict(lon_deg=-67.7538, lat_deg=-23.0292, height_m=5070.0)

_CACHE = {}


# ----------------------------------------------------------------- internals
def _alma_location():
    if 'alma' not in _CACHE:
        from astropy.coordinates import EarthLocation
        import astropy.units as u
        _CACHE['alma'] = EarthLocation.from_geodetic(
            ALMA_GEODETIC['lon_deg'] * u.deg,
            ALMA_GEODETIC['lat_deg'] * u.deg,
            ALMA_GEODETIC['height_m'] * u.m)
    return _CACHE['alma']


def _star_field(star, *names, default=None):
    """Tolerate the several spellings the four call sites use."""
    for n in names:
        if n in star and star[n] is not None:
            return star[n]
    if default is None:
        raise KeyError('star dict lacks any of %r' % (names,))
    return default


def observer_bcrs_au(mjd_sec, site=None, topocentric=True):
    """Barycentric position of the observer, in au, as a (3,) array.

    `topocentric=True` adds the observatory's geocentric vector (diurnal
    parallax).  That term is 4.3e-5 au, i.e. 0.033 mas even for Proxima, so it
    is included only because it is free, never because it matters.
    """
    from astropy.coordinates import get_body_barycentric
    from astropy.time import Time
    import astropy.units as u
    t = Time(np.asarray(mjd_sec, dtype=float) / 86400.0, format='mjd')
    r = get_body_barycentric('earth', t).xyz.to(u.au).value
    if topocentric:
        loc = _alma_location() if site is None else site
        r = r + loc.get_itrs(obstime=t).cartesian.xyz.to(u.au).value
    return np.asarray(r, dtype=float)


def barycentric_at_epoch(star, mjd_sec):
    """The SkyCoord the legacy code used: Gaia position space-motion-propagated
    to the observation epoch, in the BCRS.  Distance is carried, so
    `.cartesian` is the full BCRS position vector."""
    from astropy.coordinates import SkyCoord, Distance
    from astropy.time import Time
    import astropy.units as u
    plx = float(_star_field(star, 'parallax', 'plx', 'plx_mas'))
    if not np.isfinite(plx) or plx <= 0.0:
        plx = 1e-3                      # matches continuum_map_generic's guard
    c0 = SkyCoord(
        ra=float(_star_field(star, 'ra_deg', 'ra')) * u.deg,
        dec=float(_star_field(star, 'dec_deg', 'dec')) * u.deg,
        pm_ra_cosdec=float(_star_field(star, 'pmra', 'pm_ra_cosdec',
                                       default=0.0)) * u.mas / u.yr,
        pm_dec=float(_star_field(star, 'pmdec', 'pm_dec',
                                 default=0.0)) * u.mas / u.yr,
        distance=Distance(parallax=plx * u.mas),
        radial_velocity=float(_star_field(star, 'rv_kms', 'rv',
                                          default=0.0)) * u.km / u.s,
        obstime=Time(float(_star_field(star, 'epoch', default=2016.0)),
                     format='jyear'))
    return c0.apply_space_motion(
        Time(float(mjd_sec) / 86400.0, format='mjd'))


def _lm(a, d, a0, d0):
    """Direction cosines, IDENTICAL algebra to the shipped `star_lm()`."""
    l = np.cos(d) * np.sin(a - a0)
    m = np.sin(d) * np.cos(d0) - np.cos(d) * np.sin(d0) * np.cos(a - a0)
    return l, m


# -------------------------------------------------------------------- public
def apparent_radec(star, mjd_sec, site=None, topocentric=True, c_bary=None):
    """(ra, dec) in RADIANS of the star's APPARENT direction as seen from the
    observatory: the unit vector from the observer to the star.  Parallax only;
    aberration and light deflection are excluded (they cancel against the phase
    centre to <<1 mas over an arcsecond-scale field)."""
    import astropy.units as u
    c = barycentric_at_epoch(star, mjd_sec) if c_bary is None else c_bary
    r_star = c.cartesian.xyz.to(u.au).value           # BCRS, au
    r_obs = observer_bcrs_au(mjd_sec, site=site, topocentric=topocentric)
    v = np.asarray(r_star, dtype=float) - r_obs
    v = v / np.linalg.norm(v)
    return float(np.arctan2(v[1], v[0])), float(np.arcsin(v[2]))


def parallax_offset(star, mjd_sec, site=None, topocentric=True, c_bary=None):
    """Omitted displacement (apparent minus barycentric) in RADIANS, as
    (dl, dm) in the tangent plane at the star's own barycentric direction:
    dl eastward, dm northward.  This is exactly what `star_lm()` leaves out."""
    c = barycentric_at_epoch(star, mjd_sec) if c_bary is None else c_bary
    a0, d0 = float(c.ra.rad), float(c.dec.rad)
    a, d = apparent_radec(star, mjd_sec, site=site,
                          topocentric=topocentric, c_bary=c)
    return _lm(a, d, a0, d0)


def star_lm_apparent(phase_ra, phase_dec, mjd_sec, star, site=None,
                     topocentric=True, include_parallax=True):
    """Direction cosines of the star's APPARENT position relative to the MS
    phase centre.  Drop-in replacement for `star_lm()`.

    Parameters are the shipped ones: `phase_ra`, `phase_dec` in RADIANS (as
    read from `FIELD::PHASE_DIR`), `mjd_sec` the observation epoch in seconds.
    `star` is the dict the call site already holds.

    Returns `(l, m, c_bary)`.  `c_bary` is the **barycentric** SkyCoord at
    epoch -- unchanged from the shipped behaviour on purpose, so that the
    `t1_ra` / `t1_dec` provenance columns keep their existing meaning.  Use
    `parallax_offset()` or `star_lm_report()` to record the correction itself.

    `include_parallax=False` reproduces the shipped (defective) behaviour
    exactly, for A/B work only.
    """
    c = barycentric_at_epoch(star, mjd_sec)
    if not include_parallax:
        a, d = float(c.ra.rad), float(c.dec.rad)
    else:
        a, d = apparent_radec(star, mjd_sec, site=site,
                              topocentric=topocentric, c_bary=c)
    l, m = _lm(a, d, float(phase_ra), float(phase_dec))
    return l, m, c


def make_star_lm(star, site=None, topocentric=True, include_parallax=True):
    """Return a `star_lm(phase_ra, phase_dec, mjd_sec)` closure, for the call
    sites whose shipped version reads a module-level star record."""
    def star_lm(phase_ra, phase_dec, mjd_sec):
        return star_lm_apparent(phase_ra, phase_dec, mjd_sec, star, site=site,
                                topocentric=topocentric,
                                include_parallax=include_parallax)
    star_lm.__doc__ = star_lm_apparent.__doc__
    return star_lm


def star_lm_report(phase_ra, phase_dec, mjd_sec, star, site=None,
                   topocentric=True, syn_arcsec=None):
    """Everything, in arcseconds, for logging and for the per-window ledger.

    If `syn_arcsec` is given, also returns the displacement in synthesised
    beams and the Gaussian-dirty-beam amplitude retained at that offset.  The
    Gaussian rule is OPTIMISTIC -- the measured main lobe is 0.72-0.92 of
    1.22 lambda/B_max, so the true loss is larger; see
    `ROSS154_AND_SCALE.md` Sec. 1.4 and `loss_gaussian()` below.
    """
    c = barycentric_at_epoch(star, mjd_sec)
    lb, mb = _lm(float(c.ra.rad), float(c.dec.rad),
                 float(phase_ra), float(phase_dec))
    dl, dm = parallax_offset(star, mjd_sec, site=site,
                             topocentric=topocentric, c_bary=c)
    out = dict(
        l_bary_arcsec=lb / ARCSEC, m_bary_arcsec=mb / ARCSEC,
        l_app_arcsec=(lb + dl) / ARCSEC, m_app_arcsec=(mb + dm) / ARCSEC,
        plx_dl_arcsec=dl / ARCSEC, plx_dm_arcsec=dm / ARCSEC,
        plx_offset_arcsec=float(np.hypot(dl, dm)) / ARCSEC,
        bary_ra_deg=float(c.ra.deg), bary_dec_deg=float(c.dec.deg),
        mjd_sec=float(mjd_sec), topocentric=bool(topocentric))
    if syn_arcsec:
        r = out['plx_offset_arcsec'] / float(syn_arcsec)
        out['plx_offset_beams'] = r
        out['loss_gaussian'] = loss_gaussian(r)
    return out


def loss_gaussian(offset_beams):
    """Normalised Gaussian beam at an offset expressed in FWHM units:
    exp(-4 ln2 x^2).  The amplitude RETAINED, not the fraction lost."""
    x = np.asarray(offset_beams, dtype=float)
    return np.exp(-4.0 * np.log(2.0) * x * x)


# ------------------------------------------------------------ classical form
def parallax_offset_classical(star, mjd_sec, site=None, topocentric=True):
    """The textbook first-order parallax ellipse, kept as an INDEPENDENT
    derivation for the test:

        d(alpha) cos(dec) =  pi (X sin a - Y cos a)
        d(dec)            =  pi (X cos a sin d + Y sin a sin d - Z cos d)

    with (X, Y, Z) the observer's barycentric position in au and pi the
    parallax in radians (e.g. Green, *Spherical Astronomy*, Sec. 9.2).  It is
    derived from the geometry, not from `apparent_radec()`, so agreement
    between the two fixes the SIGN as well as the size.
    """
    c = barycentric_at_epoch(star, mjd_sec)
    a, d = float(c.ra.rad), float(c.dec.rad)
    import astropy.units as u
    plx_rad = 1.0 / float(c.distance.to(u.au).value)   # small-angle: 1 au / D
    X, Y, Z = observer_bcrs_au(mjd_sec, site=site, topocentric=topocentric)
    dl = plx_rad * (X * np.sin(a) - Y * np.cos(a))
    dm = plx_rad * (X * np.cos(a) * np.sin(d) + Y * np.sin(a) * np.sin(d)
                    - Z * np.cos(d))
    return float(dl), float(dm)
