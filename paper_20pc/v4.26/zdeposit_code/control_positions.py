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
annulus centred on the star and set by that window's own primary beam:

    r_in  = 0.14 * theta_pb      r_out = 0.78 * theta_pb

where theta_pb is the recorded primary-beam FWHM of the window.  There are
512 of them, drawn uniform in AREA and in azimuth:

    r     = sqrt( U(r_in^2, r_out^2) )        theta = U(0, 2 pi)

with numpy's default generator at seed 20260825, drawn in that order.  Three
properties of the rule matter and are tested below:

  * UNIFORM IN AREA, not in radius.  Drawing r uniform in radius would
    concentrate the ensemble toward the inner edge, where the primary-beam
    response is highest, and so would bias the control side high.
  * SCALED TO THE WINDOW'S OWN BEAM.  theta_pb spans a factor of nearly ten
    across the survey, so a fixed angular annulus would sit outside the beam
    in some windows and on the star in others.  The outer radius lies past
    the half-power point of the beam and the inner radius well inside it.
  * NO CONTROL ON THE STAR.  The inner radius is large compared with the
    synthesised beam in every window, so the star does not contribute to any
    control position.

The seed is fixed and is deposited with every window, so the ensemble is
reproducible position by position.
"""
import argparse
import csv
import math
import os

import numpy as np

RING_SEED = 20260825
RING_IN, RING_OUT = 0.14, 0.78
N_CONTROL = 512


def control_offsets(theta_pb_arcsec, seed=RING_SEED, n=N_CONTROL):
    """The control positions of one window, as offsets from the star in
    arcseconds.  Returns (dx, dy) arrays of length n."""
    rng = np.random.default_rng(seed)
    lo = RING_IN * theta_pb_arcsec
    hi = RING_OUT * theta_pb_arcsec
    r = np.sqrt(rng.uniform(lo ** 2, hi ** 2, n))
    th = rng.uniform(0.0, 2.0 * math.pi, n)
    return r * np.cos(th), r * np.sin(th)


def pb_response(r_arcsec, theta_pb_arcsec):
    """Gaussian primary-beam response at radius r for a given FWHM."""
    return math.exp(-4.0 * math.log(2.0)
                    * (r_arcsec / theta_pb_arcsec) ** 2)


def ring_radii(theta_pb_arcsec):
    return RING_IN * theta_pb_arcsec, RING_OUT * theta_pb_arcsec


# --------------------------------------------------------------- known answers
def _kat():
    pb = 28.066
    dx, dy = control_offsets(pb)
    r = np.hypot(dx, dy)
    lo, hi = ring_radii(pb)

    # (1) every position is inside the annulus
    assert r.min() >= lo - 1e-9 and r.max() <= hi + 1e-9, (r.min(), r.max())
    assert r.size == N_CONTROL

    # (2) uniform in AREA: the median radius is the area-median, not the
    # midpoint of the radii.  This is the test that fails if the draw is
    # uniform in radius, and it is the bias that would matter.
    area_median = math.sqrt(0.5 * (lo ** 2 + hi ** 2))
    radius_median = 0.5 * (lo + hi)
    assert abs(float(np.median(r)) - area_median) < 0.4, float(np.median(r))
    assert abs(area_median - radius_median) > 0.4, (area_median, radius_median)

    # (3) reproducible from the seed, and different for a different seed
    assert np.allclose(control_offsets(pb)[0], dx)
    assert not np.allclose(control_offsets(pb, seed=RING_SEED + 1)[0], dx)

    # (4) azimuthally uniform: the mean offset is small against the annulus
    assert abs(float(dx.mean())) < 0.1 * hi and abs(float(dy.mean())) < 0.1 * hi

    # (5) the annulus straddles the half-power point of the beam: the inner
    # radius is well inside it and the outer radius past it
    assert pb_response(lo, pb) > 0.9, pb_response(lo, pb)
    assert pb_response(hi, pb) < 0.25, pb_response(hi, pb)

    # (6) scaling: double the beam and every radius doubles
    dx2, dy2 = control_offsets(2 * pb)
    assert np.allclose(np.hypot(dx2, dy2), 2 * r)
    print('control_positions: 6 known-answer tests pass')


def _check(path):
    """The deposited radii are what this rule gives, row by row."""
    n = worst_in = worst_out = 0
    with open(path) as fh:
        for row in csv.DictReader(fh):
            pb = float(row['theta_pb_arcsec'])
            lo, hi = ring_radii(pb)
            worst_in = max(worst_in, abs(lo - float(row['ring_r_in_arcsec'])))
            worst_out = max(worst_out, abs(hi - float(row['ring_r_out_arcsec'])))
            assert int(row['ring_seed']) == RING_SEED
            assert int(row['n_ctrl']) == N_CONTROL
            n += 1
    print('control_positions: %d deposited rows reproduce from the rule; '
          'largest disagreement %.5f arcsec inner, %.5f arcsec outer, '
          'against the 0.001 arcsec the radii and the beam are printed to'
          % (n, worst_in, worst_out))
    assert worst_in < 2e-3 and worst_out < 2e-3


if __name__ == '__main__':
    ap = argparse.ArgumentParser()
    ap.add_argument('--check', metavar='CONTROL_FIELD_STATISTICS_CSV')
    a = ap.parse_args()
    _kat()
    if a.check:
        _check(os.path.abspath(a.check))
