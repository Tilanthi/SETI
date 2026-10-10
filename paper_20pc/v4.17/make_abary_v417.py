#!/usr/bin/env python3
r"""make_abary_v417.py -- freeze the observer's line-of-sight ACCELERATION
toward each crossing's own position at each block's mid-time.

Writes `r16inputs/abary_v417.json`.  Run once; the product is an input.

WHY THIS EXISTS.  The search ran topocentrically, so every fitted drift is
d(nu_topo)/dt.  The pair-consistency test compares a STELLAR-FRAME frequency
offset with an extrapolation of those drifts, and the two are not in the same
frame: the topocentric drift carries the observatory's own line-of-sight
acceleration, which is dominated by the Earth's rotation and therefore
oscillates with a period of a day instead of accumulating.  Extrapolating it
linearly over days adds a term that is not there.  Converting is one line,

    nu_star = nu_topo (1 + v_sys/c)(1 - v_bary/c)
    => nudot_star = nudot_topo (1 + v_sys/c)(1 - v_bary/c)
                    - nu_topo (1 + v_sys/c) a_bary / c,

so the quantity the frozen catalogue lacks is a_bary = d(v_bary)/dt.  It is
computed here from each block's own pointing and mid-time, by central
difference of the same barycentric projection the survey used.

THE CHECK THAT MAKES THIS SAFE.  The parent quantity, v_bary itself, is
already frozen for every block and window in `r8inputs/bary_v405.json`, and
was measured on the host during a different campaign with different code.
This script reproduces it from the position and the time, and refuses to
write unless it agrees.  A derivative computed by machinery that cannot
reproduce the function is worth nothing.

★ The agreement is demanded in TWO parts, because one tolerance would have
had to be loosened to the worst case and would then have passed anything.
The median deviation over the 125 blocks the frozen file covers is 7e-6 km/s,
and the tolerance on it is MED_TOL.  Ten blocks deviate by up to 4e-2 km/s,
every one of them in the same direction, and the amount is what evaluating
v_bary at a different instant WITHIN THE SAME BLOCK would give: so the second
clause requires each deviation to be smaller than |a_bary| times that block's
own duration, which is the largest excursion the block itself can produce.
A deviation larger than that could not come from the choice of instant and
would mean a different site, ephemeris or pointing.

Requires astropy.  Nothing in the build does: the product is json.
"""
import json
import math
import os
import sys

import astropy.units as u
from astropy.coordinates import EarthLocation, SkyCoord
from astropy.time import Time

HERE = os.path.dirname(os.path.abspath(__file__))
OUTDIR = os.path.join(HERE, 'r16inputs')
OUT = os.path.join(OUTDIR, 'abary_v417.json')
MED_TOL = 1.0e-4                 # median agreement against the frozen v_bary
STEP_S = 60.0                    # central-difference half-step

# The array centre.  ALMA's geodetic position is an instrument constant, not a
# measurement of this survey; the reproduction check below is what proves the
# value used here is the one the frozen v_bary was computed at.
ALMA = EarthLocation.from_geodetic(lon=-67.7549 * u.deg,
                                   lat=-23.0229 * u.deg,
                                   height=5070.0 * u.m)

REC = json.load(open(os.path.join(HERE, 'r10inputs', 'recur_v411.json')))
# ★ The holdout campaign's records are read as well, because the attributed
# crossings that serve as the pair test's positive control were never covered
# by the census recurrence campaign and their blocks appear only there.  A
# generator that needs a block's pointing must read every file that carries
# one, or the block silently falls out of the correction.
HOLD = json.load(open(os.path.join(
    HERE, 'r11inputs', 'events', 'recur_holdout.json')))
BARY = json.load(open(os.path.join(
    HERE, 'r8inputs', 'bary_v405.json')))['v_bary_kms']

# One position and one mid-time per execution block, taken from the block's
# own record.  Keyed on the block, never on a star name.
POS, TMID, DUR = {}, {}, {}
for src in (REC, HOLD):
    for c in list(src['crossings'].values()) + list(src.get('rows', [])):
        for d in (c.get('discovery') or c, ) + tuple(c.get('blocks') or ()):
            eb = d.get('eb') or c['eb']
            if d.get('t_start_mjdsec') and d.get('ra') is not None:
                POS.setdefault(eb, (d['ra'], d['dec']))
                TMID.setdefault(eb, 0.5 * (d['t_start_mjdsec']
                                           + d['t_end_mjdsec']) / 86400.0)
                DUR.setdefault(eb, d['t_end_mjdsec'] - d['t_start_mjdsec'])

OUTJ, worst = {}, (0.0, None)
for eb in sorted(POS):
    ra, dec = POS[eb]
    sky = SkyCoord(ra=ra * u.deg, dec=dec * u.deg)
    t0 = TMID[eb]

    def vb(mjd):
        return sky.radial_velocity_correction(
            kind='barycentric', obstime=Time(mjd, format='mjd', scale='utc'),
            location=ALMA).to(u.km / u.s).value

    h = STEP_S / 86400.0
    v0 = vb(t0)
    a = (vb(t0 + h) - vb(t0 - h)) / (2.0 * STEP_S) * 1000.0   # m s^-2
    ref = [BARY[k] for k in BARY if k.startswith(eb + '|')]
    dev = max(abs(v0 - q) for q in ref) if ref else None
    if dev is not None and dev > worst[0]:
        worst = (dev, eb)
    OUTJ[eb] = dict(v_bary_kms=v0, a_bary_m_s2=a, mjd_mid=t0,
                    dur_s=DUR[eb], ra=ra, dec=dec, n_frozen=len(ref),
                    dev_from_frozen_kms=dev,
                    dev_budget_kms=abs(a) * DUR[eb] / 1000.0)

_dev = sorted(v['dev_from_frozen_kms'] for v in OUTJ.values()
              if v['n_frozen'])
_over = [k for k, v in OUTJ.items()
         if v['n_frozen'] and v['dev_from_frozen_kms'] > v['dev_budget_kms']]
_med = _dev[len(_dev) // 2] if len(_dev) % 2 else \
    0.5 * (_dev[len(_dev) // 2 - 1] + _dev[len(_dev) // 2])
if not _dev or _med > MED_TOL or _over:
    sys.exit('REFUSING TO WRITE: v_bary reproduced for %d of %d blocks, '
             'median deviation %.2e km/s against %.0e, worst %.2e on %s; '
             '%d block(s) deviate by more than their own duration allows: %s'
             % (len(_dev), len(OUTJ), _med, MED_TOL, worst[0], worst[1],
                len(_over), sorted(_over)[:5]))
os.makedirs(OUTDIR, exist_ok=True)
json.dump(dict(
    _provenance='Observer line-of-sight velocity and ACCELERATION toward '
                'each execution block\'s own pointing at that block\'s '
                'mid-time, for converting a topocentric fitted drift into '
                'the stellar frame.  Central difference of the barycentric '
                'projection over +/-%.0f s, astropy builtin ephemeris, ALMA '
                'array centre.  Validated against r8inputs/bary_v405.json: '
                'median deviation %.2e km/s over %d blocks, worst %.2e on '
                '%s, and every deviation smaller than that block\'s own '
                '|a_bary| x duration.  Generated by make_abary_v417.py.'
                % (STEP_S, _med, len(_dev), worst[0], worst[1]),
    blocks=OUTJ), open(OUT, 'w'), indent=1, sort_keys=True)
print('%d blocks written, v_bary reproduced for %d of them, median deviation '
      '%.2e km/s, worst %.2e on %s'
      % (len(OUTJ), len(_dev), _med, worst[0], worst[1]))
print('a_bary spans %.4f to %.4f m/s2'
      % (min(v['a_bary_m_s2'] for v in OUTJ.values()),
         max(v['a_bary_m_s2'] for v in OUTJ.values())))
