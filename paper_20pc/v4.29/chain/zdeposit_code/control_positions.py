#!/usr/bin/env python3
"""Reference implementation of the control-position generator.

    python3 control_positions.py                         # known-answer tests
    python3 control_positions.py --check ../statistics/control_field_statistics.csv

THIS IS NOT THE SURVEY PIPELINE.  It is a short, self-contained
implementation of the published rule, written so that the rule can be read,
run and checked against the deposited tables.  What the pipeline does with
these positions -- extract a spectrum at each of them from calibrated
visibilities -- is not here, because neither the visibilities nor the
extraction are part of this archive.

THE RULE.  The control positions of a window lie, from a fixed seed, in an
annulus centred on the star and set by the primary beam of the dish that
observed it and by its synthesised beam:

    theta_pb = 1.22 lambda / D                (D = 12 m, or 7 m on the ACA)
    r_in  = max(0.14 theta_pb, f * theta_syn)   f = 2
    r_out = 0.78 theta_pb

with lambda at the window's centre and theta_syn = 1.22 lambda / B_max from
the window's longest projected baseline.  There are 512 positions, drawn
uniform in AREA and in azimuth:

    r     = sqrt( U(r_in^2, r_out^2) )        theta = U(0, 2 pi)

with numpy's default generator at seed 20260825, drawn in that order.

ONE DECLARED EXCEPTION.  The rows whose `geometry_provenance` is
`frozen-geometry` were extracted before the dish was read from the data: for
them D = 12 m whatever the array and there is no synthesised-beam floor.  On a
12 m array that is the same rule; on a 7 m array it is not, and those rows are
listed by name whenever --check runs.  The check does not pin how many there
are; it pins that every row follows the rule of the extraction that produced
its statistic, and that only a row declared `frozen-geometry` may differ from
its own array's dish.

Properties tested below:

  * UNIFORM IN AREA, not in radius.
  * SCALED TO THE WINDOW'S OWN DISH: the deposited beam must invert to the
    dish of the row's own array.  A beam that merely inverts to "a real ALMA
    dish" is not enough -- 12 m is a real ALMA dish, and quoting it on a 7 m
    observation is exactly the error this check exists to catch.
  * THE INNER EDGE CLEARS THE SYNTHESISED BEAM where one was applied.
"""
import argparse
import csv
import math
import os

import numpy as np

RING_SEED = 20260825
RING_IN, RING_OUT = 0.14, 0.78
PB_COEF = 1.22
C_M_S = 299792458.0
ARCSEC = 206264.806
N_CONTROL = 512
DISH_OF_ARRAY = {'12m': 12.0, '7m': 7.0}
FROZEN = 'frozen-geometry'
D_TOL = 0.005          # relative; the beam is printed to 0.001 arcsec of ~20-60
R_TOL = 2e-3           # arcsec; the radii are printed to 0.001


def theta_pb(nu_ghz, dish_m):
    """Primary-beam FWHM convention of the extractor, arcsec."""
    return PB_COEF * (C_M_S / (nu_ghz * 1e9)) / dish_m * ARCSEC


def dish_of_beam(nu_ghz, theta_arcsec):
    """Invert theta = 1.22 lambda / D for D, metres."""
    return PB_COEF * (C_M_S / (nu_ghz * 1e9)) / (theta_arcsec / ARCSEC)


def ring_radii(theta_pb_arcsec, syn_arcsec=None, factor=None):
    lo = RING_IN * theta_pb_arcsec
    if syn_arcsec and factor:
        lo = max(lo, factor * syn_arcsec)
    return lo, RING_OUT * theta_pb_arcsec


def control_offsets(theta_pb_arcsec, seed=RING_SEED, n=N_CONTROL,
                    syn_arcsec=None, factor=None):
    """The control positions of one window, as offsets from the star in
    arcseconds.  Returns (dx, dy) arrays of length n."""
    rng = np.random.default_rng(seed)
    lo, hi = ring_radii(theta_pb_arcsec, syn_arcsec, factor)
    r = np.sqrt(rng.uniform(lo ** 2, hi ** 2, n))
    th = rng.uniform(0.0, 2.0 * math.pi, n)
    return r * np.cos(th), r * np.sin(th)


def pb_response(r_arcsec, theta_pb_arcsec):
    """Gaussian primary-beam response at radius r for a given FWHM."""
    return math.exp(-4.0 * math.log(2.0)
                    * (r_arcsec / theta_pb_arcsec) ** 2)


# --------------------------------------------------------------- known answers
def _kat():
    pb = 28.066
    dx, dy = control_offsets(pb)
    r = np.hypot(dx, dy)
    lo, hi = ring_radii(pb)
    assert r.min() >= lo - 1e-9 and r.max() <= hi + 1e-9, (r.min(), r.max())
    assert r.size == N_CONTROL
    area_median = math.sqrt(0.5 * (lo ** 2 + hi ** 2))
    radius_median = 0.5 * (lo + hi)
    assert abs(float(np.median(r)) - area_median) < 0.4, float(np.median(r))
    assert abs(area_median - radius_median) > 0.4, (area_median, radius_median)
    assert np.allclose(control_offsets(pb)[0], dx)
    assert not np.allclose(control_offsets(pb, seed=RING_SEED + 1)[0], dx)
    assert abs(float(dx.mean())) < 0.1 * hi and abs(float(dy.mean())) < 0.1 * hi
    dx2, dy2 = control_offsets(2 * pb)
    assert np.allclose(np.hypot(dx2, dy2), 2 * r)
    # (7) the beam inverts to the dish it was made with, for both dishes
    for d in (7.0, 12.0):
        assert abs(dish_of_beam(230.0, theta_pb(230.0, d)) - d) < 1e-9
    # (8) the synthesised-beam floor binds when it is larger and only then
    assert ring_radii(pb, syn_arcsec=8.0, factor=2.0)[0] == 16.0
    assert ring_radii(pb, syn_arcsec=0.5, factor=2.0)[0] == RING_IN * pb
    # (9) the check itself can fail: a 7 m row described with a 12 m beam
    #     must be refused.  An undemonstrated check is not a check.
    good = dict(eb='X', nu_lo_GHz='229.6', nu_hi_GHz='231.4', array='7m',
                geometry_provenance='corrected-geometry', annulus_dish_m='7.0',
                ann_syn_factor='2.0', syn_arcsec='8.0', ring_seed=str(RING_SEED),
                n_ctrl=str(N_CONTROL))
    th7 = theta_pb(230.5, 7.0)
    lo7, hi7 = ring_radii(th7, 8.0, 2.0)
    good.update(theta_pb_arcsec='%.3f' % th7, ring_r_in_arcsec='%.3f' % lo7,
                ring_r_out_arcsec='%.3f' % hi7)
    assert not _faults([good])[0], _faults([good])
    th12 = theta_pb(230.5, 12.0)
    bad = dict(good, theta_pb_arcsec='%.3f' % th12,
               ring_r_in_arcsec='%.3f' % (RING_IN * th12),
               ring_r_out_arcsec='%.3f' % (RING_OUT * th12),
               annulus_dish_m='12.0', ann_syn_factor='', syn_arcsec='')
    assert any('not the 7 m' in m for m in _faults([bad])[0]), _faults([bad])
    print('control_positions: 9 known-answer tests pass, including that the '
          'check refuses a 7 m window described with a 12 m annulus')


def _faults(rows):
    """Every way a deposited row can disagree with the rule.  Returns
    (faults, declared) -- `declared` are the rows on a frozen pre-repair
    annulus whose array has a different dish, reported, never hidden."""
    faults, declared = [], []
    for row in rows:
        tag = '%s %s-%s GHz' % (row['eb'], row['nu_lo_GHz'], row['nu_hi_GHz'])
        nu = 0.5 * (float(row['nu_lo_GHz']) + float(row['nu_hi_GHz']))
        th = float(row['theta_pb_arcsec'])
        d_ann = float(row['annulus_dish_m'])
        d_arr = DISH_OF_ARRAY.get(row['array'])
        if d_arr is None:
            faults.append('%s: array %r is not one this rule knows' % (tag, row['array']))
            continue
        d_beam = dish_of_beam(nu, th)
        # C1: the beam is the one the stated annulus dish gives
        if abs(d_beam - d_ann) > D_TOL * d_ann:
            faults.append('%s: theta_pb %.3f" inverts to a %.2f m dish, not '
                          'the %.0f m the row says its annulus used' % (tag, th, d_beam, d_ann))
        # C2: the annulus dish is the observing dish, unless declared frozen
        if abs(d_ann - d_arr) > 1e-6:
            if row['geometry_provenance'] == FROZEN:
                declared.append(tag)
            else:
                faults.append('%s: annulus built for a %.0f m dish, not the '
                              '%.0f m dish of the row\'s own array %s'
                              % (tag, d_ann, d_arr, row['array']))
        # C3: the radii are the rule's, from the row's own beam and floor
        syn = float(row['syn_arcsec']) if row.get('syn_arcsec') else None
        fac = float(row['ann_syn_factor']) if row.get('ann_syn_factor') else None
        if row['geometry_provenance'] != FROZEN and d_arr == 7.0 and not (syn and fac):
            faults.append('%s: a repaired 7 m row carries no synthesised beam, '
                          'so its inner edge cannot be checked' % tag)
        lo, hi = ring_radii(th, syn, fac)
        if abs(lo - float(row['ring_r_in_arcsec'])) > R_TOL:
            faults.append('%s: r_in %s" is not the rule\'s %.3f"' % (tag, row['ring_r_in_arcsec'], lo))
        if abs(hi - float(row['ring_r_out_arcsec'])) > R_TOL:
            faults.append('%s: r_out %s" is not the rule\'s %.3f"' % (tag, row['ring_r_out_arcsec'], hi))
        if int(row['ring_seed']) != RING_SEED or int(row['n_ctrl']) != N_CONTROL:
            faults.append('%s: seed or ensemble size is not the rule\'s' % tag)
    return faults, declared


def _check(path):
    with open(path) as fh:
        rows = list(csv.DictReader(fh))
    need = ('array', 'geometry_provenance', 'annulus_dish_m', 'syn_arcsec',
            'ann_syn_factor', 'theta_pb_arcsec', 'ring_r_in_arcsec',
            'ring_r_out_arcsec')
    miss = [c for c in need if c not in (rows[0] if rows else {})]
    if miss:
        raise SystemExit('control_positions: %s carries no %s column(s), so '
                         'the dish that observed each window is not knowable '
                         'and the annulus cannot be checked against it'
                         % (os.path.basename(path), ', '.join(miss)))
    faults, declared = _faults(rows)
    for m in faults[:20]:
        print('  FAULT ' + m)
    print('control_positions: %d rows checked; %d fault(s); %d row(s) declared '
          'frozen-geometry on an annulus built for a different dish than their '
          'array%s' % (len(rows), len(faults), len(declared),
                       (':\n    ' + '\n    '.join(declared)) if declared else ''))
    if faults:
        raise SystemExit(1)


if __name__ == '__main__':
    ap = argparse.ArgumentParser()
    ap.add_argument('--check', metavar='CONTROL_FIELD_STATISTICS_CSV')
    a = ap.parse_args()
    _kat()
    if a.check:
        _check(os.path.abspath(a.check))
