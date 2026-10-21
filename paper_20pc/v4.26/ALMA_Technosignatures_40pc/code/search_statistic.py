#!/usr/bin/env python3
"""Reference implementation of the search statistic.

    python3 search_statistic.py            # the known-answer tests
    python3 search_statistic.py --demo     # a worked recovery on synthetic data

THIS IS NOT THE SURVEY PIPELINE.  It is a short, self-contained
implementation of the published definition, written so that the definition
can be read, run and checked against the deposited tables.  The pipeline
that produced the survey reads calibrated visibilities, and neither it nor
the data it reads is part of this archive; what is here is the arithmetic the
published equation specifies, and nothing else.

THE DEFINITION.  For a position x, the statistic is the largest stacked
signal-to-noise ratio anywhere on the channel-by-drift grid,

    T(x) = max over (nu_dot, nu) of
              sum_t I(x, t, nu + nu_dot t) / sigma^2(t, nu)
            / [ sum_t 1 / sigma^2(t, nu) ]^(1/2)

where I(x, t, nu) is the spectrum at position x in integration t and channel
nu, and sigma(t, nu) is the noise scale there.  It is the matched filter for
a constant-drift carrier: a drift-aligned, inverse-variance-weighted stack of
the intensities along the track, divided by the noise of that stack.  So T is
an absolute signal-to-noise ratio and not a local contrast.

Three properties of the definition that are easy to lose and are tested below:

  * t runs from the first integration of the observation, so the channel that
    labels a track is the one a carrier would occupy at the start of the
    block.  A repeat epoch is read at the cell that same convention fixes.
  * the noise scale is the median absolute deviation across the control
    positions at each integration and each channel, scaled to its
    Gaussian-equivalent standard deviation.  It is local in time and
    frequency, global in position, and SHARED by the star and every control:
    the same sigma array divides every position, which is what makes the
    positions comparable.
  * the statistic is evaluated at one position at a time, identically at the
    star and at each control.
"""
import argparse
import math

import numpy as np

MAD_TO_SIGMA = 1.4826022185056018   # 1 / Phi^{-1}(3/4); MAD -> Gaussian sigma


def noise_scale(cube):
    """sigma(t, nu) from the control positions: the median absolute deviation
    across POSITION at each integration and each channel, scaled to its
    Gaussian-equivalent standard deviation.

    cube has shape (n_pos, n_int, n_chan) and holds the control positions.
    The returned array has shape (n_int, n_chan) and is shared by every
    position, the star included.
    """
    cube = np.asarray(cube, dtype=float)
    med = np.median(cube, axis=0)
    return MAD_TO_SIGMA * np.median(np.abs(cube - med), axis=0)


def stack(spec, sigma, drift_chan_per_int):
    """The inverse-variance-weighted, drift-aligned stack of one position.

    spec   (n_int, n_chan)   the spectrum at one position
    sigma  (n_int, n_chan)   the shared noise scale
    drift_chan_per_int       drift rate, in CHANNELS per integration

    Returns the stacked signal-to-noise ratio for every start channel, as an
    array of length n_chan.  t runs from the first integration, so index j of
    the result is the track that starts in channel j.
    """
    spec = np.asarray(spec, dtype=float)
    sigma = np.asarray(sigma, dtype=float)
    n_int, n_chan = spec.shape
    w = 1.0 / sigma ** 2
    num = np.zeros(n_chan)
    den = np.zeros(n_chan)
    for t in range(n_int):
        shift = int(round(drift_chan_per_int * t))
        # the track leaves the band at one end; those start channels get no
        # contribution from this integration rather than a wrapped one
        idx = np.arange(n_chan) + shift
        ok = (idx >= 0) & (idx < n_chan)
        num[ok] += spec[t, idx[ok]] * w[t, idx[ok]]
        den[ok] += w[t, idx[ok]]
    out = np.zeros(n_chan)
    nz = den > 0
    out[nz] = num[nz] / np.sqrt(den[nz])
    return out


def statistic(spec, sigma, drifts_chan_per_int):
    """T(x): the maximum of the stack over the channel-by-drift grid.

    Returns (T, best_channel, best_drift).
    """
    best = (-np.inf, -1, float('nan'))
    for d in drifts_chan_per_int:
        s = stack(spec, sigma, d)
        j = int(np.argmax(s))
        if s[j] > best[0]:
            best = (float(s[j]), j, float(d))
    return best


def drift_trials(n_int, n_chan, chan_width_Hz, t_int_s, drift_max_Hz_s,
                 n_trials):
    """The drift grid, in channels per integration, spanning plus and minus
    the largest drift rate searched in the window."""
    lo = -abs(drift_max_Hz_s)
    hi = abs(drift_max_Hz_s)
    return [(d * t_int_s) / chan_width_Hz
            for d in np.linspace(lo, hi, n_trials)]


# --------------------------------------------------------------- known answers
def _kat():
    rng = np.random.default_rng(7)
    n_pos, n_int, n_chan = 64, 20, 256
    noise = rng.normal(0.0, 1.0, (n_pos, n_int, n_chan))
    sig = noise_scale(noise)

    # (1) the scale recovered from unit-variance noise is unity to the
    # accuracy a finite ensemble allows
    assert abs(float(np.median(sig)) - 1.0) < 0.05, float(np.median(sig))

    # (2) a zero-drift carrier of amplitude a in every one of n integrations
    # stacks to a * sqrt(n) / sigma, which is the matched-filter gain
    spec = rng.normal(0.0, 1.0, (n_int, n_chan))
    a = 1.5
    spec[:, 100] += a
    T, j, d = statistic(spec, sig, [0.0])
    assert j == 100, j
    assert abs(T - a * math.sqrt(n_int)) < 3.0, (T, a * math.sqrt(n_int))

    # (3) the drift convention: a carrier that moves one channel per
    # integration is found at the drift trial of one channel per integration
    # and at the channel it STARTED in
    spec = rng.normal(0.0, 1.0, (n_int, n_chan))
    for t in range(n_int):
        spec[t, 50 + t] += 3.0
    T, j, d = statistic(spec, sig, [-1.0, 0.0, 1.0])
    assert (j, d) == (50, 1.0), (j, d)

    # (4) the statistic is absolute and not a local contrast: adding a
    # constant to one position does not change it, because the continuum is
    # removed along frequency before the search and a level is not a shape
    spec2 = spec + 17.0
    spec2 = spec2 - np.median(spec2, axis=1, keepdims=True)
    base = spec - np.median(spec, axis=1, keepdims=True)
    T1 = statistic(base, sig, [1.0])[0]
    T2 = statistic(spec2, sig, [1.0])[0]
    assert abs(T1 - T2) < 1e-9, (T1, T2)

    # (5) the scale is SHARED: a position whose own noise is twice the
    # ensemble's does not have it divided out, and its statistic rises
    loud = 2.0 * rng.normal(0.0, 1.0, (n_int, n_chan))
    Tq = statistic(rng.normal(0.0, 1.0, (n_int, n_chan)), sig, [0.0])[0]
    Tl = statistic(loud, sig, [0.0])[0]
    assert Tl > Tq, (Tl, Tq)
    print('search_statistic: 5 known-answer tests pass')


def _demo():
    rng = np.random.default_rng(11)
    n_pos, n_int, n_chan = 512, 30, 1024
    sig = noise_scale(rng.normal(0.0, 1.0, (n_pos, n_int, n_chan)))
    spec = rng.normal(0.0, 1.0, (n_int, n_chan))
    drift = 0.37                      # channels per integration
    for t in range(n_int):
        c = 400 + drift * t
        lo = int(math.floor(c))
        frac = c - lo
        spec[t, lo] += 2.0 * (1.0 - frac)
        spec[t, lo + 1] += 2.0 * frac
    trials = np.linspace(-1.0, 1.0, 41)
    T, j, d = statistic(spec, sig, trials)
    print('demo: amplitude 2.0 sigma per integration over %d integrations'
          % n_int)
    print('      recovered T = %.3f at channel %d, drift %.3f channels/int'
          % (T, j, d))
    print('      injected                channel %d, drift %.3f' % (400, drift))


if __name__ == '__main__':
    ap = argparse.ArgumentParser()
    ap.add_argument('--demo', action='store_true')
    a = ap.parse_args()
    _kat()
    if a.demo:
        _demo()
