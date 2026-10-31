#!/usr/bin/env python3
r"""The delivered channel response, and the amplitude a carrier keeps when it
sweeps across it inside one integration.  ONE implementation, imported.

Like `decor_r13.py` this module writes no file and claims no macro round: it
is the physics, and the generators that publish numbers from it
(`smear_r15.py`, which applies it, and `sens_r18.py`, which compares it with
the transform-limited form) import it.  Before this file the integration lived
in `sens_r18.py` and the applied retention in `smear_r15.py` as
`sinc(pi*Delta/2)`, so the paper applied one form and reported another.

WHY THE SINC FORM IS NOT THE RIGHT ONE HERE.  `sinc(pi*Delta/2)` is the
amplitude a swept carrier leaves when the spectral resolution is set by the
integration itself, so that the sweep destroys coherence inside the transform.
These channels are some 1e5 times wider than the reciprocal of an integration,
so nothing decoheres inside the transform: the sweep moves the carrier's dwell
time across the delivered channel response, and the amplitude the correlator
accumulates in a channel is the mean of that response over the sweep.  That is
arithmetic on a response this build already computes and validates against
five documented ALMA numbers (`cresp_v401.py`), and it is smaller than the
sinc form at every displacement.

THE RESPONSE IS THE VALIDATED ONE, AND THAT IS ASSERTED HERE AND NOT ASSUMED.
`validate()` rebuilds `cresp_v401.json`'s own published table at every
sub-channel phase and every averaging factor and requires agreement to 1e-6,
and reproduces the two spectral resolutions the observatory documents (1.2
channels unsmoothed, 2.0 with the default Hanning).  Every caller runs it.

    import respint_r20 as ri
    ri.validate(catdir)            # refuses unless this is cresp's response
    ri.eta(delta, navg)            # retained peak-channel amplitude
    ri.eta_sinc(delta)             # the transform-limited form, for comparison

★ THE GRID, AND WHY IT IS FIXED.  The release holds 1663 windows on three
drift conventions, and the exact integration costs some fifty milliseconds,
so `eta` is a cubic spline through an exact table in `delta`.  The table's
range and step are CONSTANTS and do not depend on what a caller asks for:
a grid that grew to fit the largest request would give two generators
slightly different values for one window, and the deposited retention is
compared with a recomputation of itself elsewhere in this build.  The spline
error is asserted against exact evaluations at points the table does not
hold, and the same clause requires linear interpolation on the same grid to
MISS that tolerance, so the order of the interpolation is doing work rather
than being asserted to.  ★ The floor is the exact integration's own
quadrature, about 1e-8: a finer grid does not improve the agreement, which is
why the tolerance is 1e-7 and not smaller.

Self-test:  python3 respint_r20.py --selftest
"""
import json
import math
import os
import sys

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))

#: lag samples; the answer is insensitive to this (cresp_v401.py uses 1024)
NLAG = 1024
#: the response is tabulated on this grid of delivered-channel offsets
GRID_STEP = 0.0005
GRID_HALF = 40.0
#: sub-channel phases averaged over, sweep samples, and delivered channels
#: searched for the peak.  The same numbers the integration was written with.
NPHI, NS, DMAX = 201, 401, 8
#: the exact-table step and range in `delta`, both CONSTANTS, and the error
#: the spline through it is required to hold to.  The range covers every
#: convention the release reaches (the worst window sweeps 0.97 of a channel
#: at the ninetieth percentile of its drift draw and 1.10 at the ceiling).
#: ★ THE TABLE IS FOR THE UNAVERAGED RESPONSE ONLY.  Online channel averaging
#: gives a different response shape, and this release holds 147 averaged
#: windows against 1516 unaveraged ones, so the averaged ones are integrated
#: EXACTLY rather than tabulated: few enough for the exact route to be
#: affordable, and no interpolation statement to make about them at all.
ETA_STEP = 0.01
ETA_DMAX = 2.0
ETA_TOL = 1e-7

_TAU = np.arange(NLAG) - NLAG / 2.0
_WINDOW = {'hann': 0.5 * (1.0 + np.cos(2.0 * math.pi * _TAU / NLAG)),
           'unif': np.ones(NLAG)}
_GRID = np.arange(-GRID_HALF, GRID_HALF + 1e-9, GRID_STEP)
_PHI = np.linspace(-0.5, 0.5, NPHI)
_D = np.arange(-DMAX, DMAX + 1)
_TAB = {}
_ETACACHE = {}
_ETATAB = {}
_VALIDATED = set()


def _table(kind):
    """|transform of the lag window| on the delivered-channel offset grid."""
    if kind not in _TAB:
        win = _WINDOW[kind]
        out = np.empty(_GRID.size)
        for i in range(0, _GRID.size, 2000):
            x = _GRID[i:i + 2000][:, None]
            ph = np.exp(2j * math.pi * x * _TAU[None, :] / NLAG)
            out[i:i + 2000] = np.abs((ph * win[None, :]).sum(1)) / NLAG
        _TAB[kind] = out
    return _TAB[kind]


def response(kind, navg, u):
    """One delivered channel's response at offset `u` delivered channels.

    Online channel averaging sums `navg` raw channels into one delivered
    channel `navg` times wider; at navg = 1 this is the raw response.
    """
    tab = _table(kind)
    u = np.asarray(u, float)
    tot = np.zeros(u.shape)
    for j in range(navg):
        tot = tot + np.interp((j - (navg - 1) / 2.0) - u * navg, _GRID, tab)
    return tot


def fwhm(kind, navg=1):
    """Full width at half maximum of the delivered response, in channels."""
    xs = np.linspace(0.0, 4.0, 801)
    r = response(kind, navg, xs)
    r = r / r[0]
    i = int(np.argmax(r < 0.5))
    assert i > 0
    return 2.0 * (xs[i - 1] + (r[i - 1] - 0.5) / (r[i - 1] - r[i])
                  * (xs[i] - xs[i - 1]))


def eta_exact(delta, navg=1, kind='hann'):
    """Retained peak-channel amplitude of a carrier sweeping `delta`
    delivered channels within one integration, relative to one that does not
    sweep, averaged over sub-channel phase.  Exact; no interpolation."""
    k = (round(float(delta), 9), int(navg), kind)
    if k in _ETACACHE:
        return _ETACACHE[k]
    d = abs(float(delta))
    s = np.linspace(-0.5, 0.5, NS) * d if d > 0 else np.zeros(1)
    u = _PHI[:, None, None] + s[None, :, None] - _D[None, None, :]
    sw = response(kind, navg, u).mean(1).max(1).mean()
    pl = response(kind, navg, _PHI[:, None] - _D[None, :]).max(1).mean()
    _ETACACHE[k] = sw / pl
    return _ETACACHE[k]


def _etatable(navg, kind):
    """A cubic spline through exact `eta` on the FIXED `delta` grid.

    The spline's error is asserted against exact evaluations at points the
    grid does not hold, and linear interpolation on the same grid is required
    to miss that tolerance -- so the clause tests the interpolation rather
    than merely declaring it.
    """
    from scipy.interpolate import CubicSpline
    key = (int(navg), kind)
    if key in _ETATAB:
        return _ETATAB[key]
    xs = np.arange(0.0, ETA_DMAX + ETA_STEP, ETA_STEP)
    ys = np.array([eta_exact(x, navg, kind) for x in xs])
    cs = CubicSpline(xs, ys)
    probes = [0.5 * ETA_STEP] + list(np.linspace(ETA_STEP, ETA_DMAX
                                                 - ETA_STEP, 7))
    worst = max(abs(float(cs(p)) - eta_exact(p, navg, kind)) for p in probes)
    crude = max(abs(float(np.interp(p, xs, ys)) - eta_exact(p, navg, kind))
                for p in probes)
    assert worst < ETA_TOL <= crude, (
        'the spline through a %.3f-channel grid holds eta to %.2g against a '
        'tolerance of %.0e, and linear interpolation on the same grid holds '
        'it to %.2g: either the grid is too coarse or the tolerance is so '
        'loose that the interpolation order is doing nothing'
        % (ETA_STEP, worst, ETA_TOL, crude))
    _ETATAB[key] = (cs, worst, crude)
    return _ETATAB[key]


def eta(delta, navg=1, kind='hann'):
    """The retained amplitude: exact for an averaged window, and for an
    unaveraged one a cubic spline through the fixed exact table."""
    d = abs(float(delta))
    if int(navg) != 1:
        return eta_exact(d, navg, kind)
    assert d <= ETA_DMAX, (
        'a sweep of %.3f channels is outside the tabulated range: raise '
        'ETA_DMAX rather than extrapolating' % d)
    cs, _w, _c = _etatable(navg, kind)
    return float(cs(d))


def eta_sinc(delta):
    """The transform-limited form, which applies when the spectral resolution
    is set by the integration itself.  Kept here so that the comparison the
    paper draws is between two expressions in one file."""
    x = math.pi * abs(float(delta)) / 2.0
    return 1.0 if x == 0.0 else math.sin(x) / x


def validate(catdir=HERE, cresp=None):
    """Refuse unless this is the response `cresp_v401.py` validated.

    Returns (worst departure, unsmoothed FWHM, Hanning FWHM).  Cached per
    directory, because every caller runs it and the table build is the
    expensive part.
    """
    if catdir in _VALIDATED and cresp is None:
        return _VALIDATED and _CHECKED[catdir]
    rec = cresp or json.load(open(os.path.join(catdir, 'cresp_v401.json')))
    phi = rec['phi']
    worst = 0.0
    n = 0
    for navg_s, pub in sorted(rec['rho_by_n'].items()):
        for p, q in zip(phi, pub):
            got = response('hann', int(navg_s), np.array([p]))[0]
            worst = max(worst, abs(got - q))
            n += 1
    assert n > 0, 'cresp_v401.json carries no response table to check against'
    assert worst < 1e-6, (
        'the channel response rebuilt here is not the one cresp_v401.py '
        'validated: worst departure %.3g over %d phase/averaging pairs'
        % (worst, n))
    fw_u, fw_h = fwhm('unif', 1), fwhm('hann', 1)
    _CHECKED[catdir] = (worst, fw_u, fw_h, n)
    _VALIDATED.add(catdir)
    return _CHECKED[catdir]


_CHECKED = {}


def _selftest():
    """Drive each of this module's own claims to fail."""
    global ETA_STEP, ETA_TOL
    fails = []

    def chk(name, cond, detail=''):
        print('  %-70s %s  %s' % (name[:70], 'OK' if cond else 'FAIL',
                                  detail))
        if not cond:
            fails.append(name)

    w, fu, fh, n = validate(HERE)
    chk('R1 the response is cresp_v401 own, at every phase and factor',
        w < 1e-6 and n > 100, 'worst %.2g over %d pairs' % (w, n))
    chk('R2 and it reproduces the two documented spectral resolutions',
        abs(fu - 1.2) < 0.02 and abs(fh - 2.0) < 0.01,
        'unsmoothed %.4f, Hanning %.4f' % (fu, fh))
    # R3 the retention is a retention: unity at no sweep, falling, bounded.
    v = [eta(d) for d in (0.0, 0.2, 0.5, 0.97, 1.5)]
    chk('R3 the retention is unity at no sweep and falls monotonically',
        abs(v[0] - 1.0) < 1e-12 and all(v[i] > v[i + 1]
                                        for i in range(len(v) - 1))
        and v[-1] > 0.0, ', '.join('%.6f' % x for x in v))
    # R4 THE DIRECTION THE PAPER RESTS ON: the transform-limited form is more
    #    severe at every displacement the release reaches, so adopting the
    #    integrated response can only make a limit deeper, never shallower.
    ds = [0.01 * i for i in range(1, 121)]
    bad = [d for d in ds if eta_sinc(d) > eta(d) + 1e-12]
    chk('R4 the transform-limited form is more severe at every displacement '
        'out to 1.2 channels', not bad,
        'worst ratio %.4f at delta 1.2'
        % (eta(1.2) / eta_sinc(1.2)))
    # R5 the interpolation is not where the answer comes from: exact and
    #    interpolated agree at points the table does not hold, and an
    #    averaged window never goes near the table at all.
    worst = max(abs(eta(d) - eta_exact(d)) for d in
                (0.0013, 0.137, 0.3331, 0.6667, 0.9733))
    avg = max(abs(eta(d, 2) - eta_exact(d, 2)) for d in (0.0086, 0.137))
    chk('R5 the interpolated retention equals the exact one, and an averaged '
        'window is integrated exactly', worst < ETA_TOL and avg == 0.0,
        'worst %.2g against a tolerance of %.0e; averaged route %.1g'
        % (worst, ETA_TOL, avg))
    # R6 THE GRID GUARD, DRIVEN BOTH WAYS.  Coarsen the step until the spline
    #    must miss the tolerance, and loosen the tolerance until linear
    #    interpolation would do: both are refusals, and the second is the one
    #    that stops the clause being decorative.
    keep_s, keep_t = ETA_STEP, ETA_TOL
    for lab, s, t, want in (('too coarse a grid', 0.5, keep_t, 'too coarse'),
                            ('a tolerance linear interpolation would meet',
                             keep_s, 1e-3, 'doing nothing')):
        try:
            ETA_STEP, ETA_TOL = s, t
            _ETATAB.clear()
            fired = False
            try:
                eta(0.97)
            except AssertionError as exc:
                fired = want in str(exc)
            chk('R6 %s is refused' % lab, fired, '')
        finally:
            ETA_STEP, ETA_TOL = keep_s, keep_t
            _ETATAB.clear()
    # R7 THE VALIDATION GUARD, DRIVEN.  Hand it a perturbed cresp table and
    #    require a refusal: a validation that cannot fail is not one.
    rec = json.load(open(os.path.join(HERE, 'cresp_v401.json')))
    rec['rho_by_n'] = {k: [x * 1.01 for x in v]
                       for k, v in rec['rho_by_n'].items()}
    _VALIDATED.discard(HERE)
    fired = False
    try:
        validate(HERE, cresp=rec)
    except AssertionError as exc:
        fired = 'not the one cresp_v401.py validated' in str(exc)
    _VALIDATED.discard(HERE)
    validate(HERE)
    chk('R7 a response that is not cresp_v401 own is refused', fired, '')
    print('respint_r20 selftest: %d failure(s)' % len(fails))
    return 1 if fails else 0


if __name__ == '__main__':
    if '--selftest' in sys.argv:
        sys.exit(_selftest())
    validate(HERE)
    for d in (0.2029, 0.3650, 0.5195, 0.9305, 0.9733):
        print('delta %.4f  eta %.6f (x%.4f)   sinc %.6f (x%.4f)'
              % (d, eta(d), 1 / eta(d), eta_sinc(d), 1 / eta_sinc(d)))
