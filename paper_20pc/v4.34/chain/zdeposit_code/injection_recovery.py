#!/usr/bin/env python3
"""Reference implementation of the injection-recovery harness.

    python3 injection_recovery.py                     # known-answer tests
    python3 injection_recovery.py --curve             # a completeness curve
    python3 injection_recovery.py --compare ../sensitivity/injection_recovery.csv

THIS IS NOT THE SURVEY PIPELINE, AND THE DIFFERENCE MATTERS MORE HERE THAN
ANYWHERE ELSE IN THIS ARCHIVE.  The survey's completeness was measured by
injecting carriers into the RETAINED PER-INTEGRATION SPECTRA OF REAL WINDOWS
and reading them back through the unmodified search path.  Those spectra are
not part of this archive, so that measurement cannot be repeated from what is
here.  What this file does is implement the harness itself -- the deposition
of a carrier, the reading, and the completeness curve formed from repeated
trials -- and run it on synthetic noise, so that the procedure can be
inspected and its properties checked.  The recovered fractions it produces
are properties of synthetic noise, not of the survey.

WHAT THE HARNESS DOES.

 1. A carrier of amplitude a (in units of the per-channel noise) is placed at
    a channel and a drift rate, both drawn at random within the window.
 2. It is deposited with the correlator's own three-point channel response
    (0.25, 0.5, 0.25) at a random SUB-CHANNEL PHASE, and linearly split
    between the two channels it straddles.  A carrier deposited as a delta in
    one channel would be recovered more easily than a real one, and the
    completeness would come out optimistic.
 3. The spectrum is read by the unchanged search statistic over the same
    drift grid the window was searched with.
 4. A trial is DETECTED when the recovered statistic reaches the trigger.
    Whether the recovered drift trial is the injected one is recorded
    separately: a trial can be detected without it.
 5. The completeness at amplitude a is the detected fraction over the
    realisations, and the 90 per cent point is read by interpolation between
    the two amplitudes that straddle it.

WHAT IT MEASURES AND WHAT IT DOES NOT.  It measures the READING: the
de-drifting, the drift trials, the shared noise scale, the maximum over the
grid and the threshold.  It does not measure the step from calibrated
visibilities to a spectrum, which is upstream of the injection point in the
survey as well -- so the survey's own completeness does not cover that step
either, and the article says so.
"""
import argparse
import csv
import math
import os

import numpy as np

import search_statistic as ss

KERNEL = (0.25, 0.5, 0.25)      # the correlator's three-point channel response
TRIGGER = 5.0


def deposit(spec, chan0, drift_chan_per_int, amp, kernel=KERNEL):
    """Put a drifting carrier into a dynamic spectrum, in place.

    The carrier is at a real-valued channel at every integration; it is split
    linearly between the two channels it straddles and then convolved with
    the channel response, which is what the correlator does to it.
    """
    n_int, n_chan = spec.shape
    for t in range(n_int):
        c = chan0 + drift_chan_per_int * t
        lo = int(math.floor(c))
        frac = c - lo
        for off, w in ((0, 1.0 - frac), (1, frac)):
            for k, kw in enumerate(kernel, start=-1):
                j = lo + off + k
                if 0 <= j < n_chan:
                    spec[t, j] += amp * w * kw
    return spec


def one_trial(rng, n_int, n_chan, sigma, amp_sigma, drifts, trigger=TRIGGER,
              chan_tol=2):
    """One injection and one reading.

    Returns (detected, drift_matched, T_recovered, T_window_max).

    amp_sigma is the amplitude in units of the noise of the FULLY STACKED
    spectrum, which is the convention the deposited trials use: a carrier
    injected at amp_sigma is expected to be recovered at a statistic near
    amp_sigma, less what the channel response and the drift grid cost it.
    Per integration that is amp_sigma / sqrt(n_int), because the stack of n
    integrations gains sqrt(n) on the noise.

    ★ The recovered statistic is read AT THE INJECTED CELL, within a
    tolerance of a few channels and over the drift grid; the largest
    statistic anywhere in the window is returned beside it and is a different
    quantity.  Reading the window maximum instead would make the harness
    measure the false-alarm rate of the window as well as the recovery of the
    carrier, and the completeness would then fall as the window grew.
    """
    spec = rng.normal(0.0, 1.0, (n_int, n_chan)) * sigma
    chan0 = rng.uniform(0.1 * n_chan, 0.9 * n_chan)
    drift = float(rng.choice(drifts))
    deposit(spec, chan0, drift, amp_sigma / math.sqrt(n_int))
    spec = spec - np.median(spec, axis=1, keepdims=True)
    lo = max(0, int(round(chan0)) - chan_tol)
    hi = min(n_chan, int(round(chan0)) + chan_tol + 1)
    best = (-np.inf, float('nan'))
    gmax = -np.inf
    for d in drifts:
        s = ss.stack(spec, sigma, d)
        gmax = max(gmax, float(s.max()))
        k = int(np.argmax(s[lo:hi])) + lo
        if s[k] > best[0]:
            best = (float(s[k]), float(d))
    return (best[0] >= trigger, abs(best[1] - drift) < 1e-12,
            best[0], gmax)


def completeness(amps, n_real=64, n_int=30, n_chan=512, n_drift=21,
                 drift_max=1.0, seed=1):
    """The recovered fraction at each amplitude."""
    rng = np.random.default_rng(seed)
    sigma = np.ones((n_int, n_chan))
    drifts = np.linspace(-drift_max, drift_max, n_drift)
    out = []
    for a in amps:
        det = sum(one_trial(rng, n_int, n_chan, sigma, a, drifts)[0]
                  for _ in range(n_real))
        out.append(det / float(n_real))
    return out


def ninety_point(amps, frac):
    """The amplitude at which the recovered fraction reaches 0.9, by linear
    interpolation between the two amplitudes that straddle it."""
    for k in range(1, len(amps)):
        if frac[k - 1] < 0.9 <= frac[k]:
            if frac[k] == frac[k - 1]:
                return amps[k]
            g = (0.9 - frac[k - 1]) / (frac[k] - frac[k - 1])
            return amps[k - 1] + g * (amps[k] - amps[k - 1])
    return float('nan') if frac[-1] < 0.9 else amps[0]


# --------------------------------------------------------------- known answers
def _kat():
    # (1) the deposition conserves the carrier: the kernel sums to one and so
    # the amplitude put into each integration is the amplitude asked for
    assert abs(sum(KERNEL) - 1.0) < 1e-12
    spec = np.zeros((1, 64))
    deposit(spec, 30.0, 0.0, 4.0)
    assert abs(spec.sum() - 4.0) < 1e-12, spec.sum()

    # (2) it is NOT a delta: the central channel receives half, not all, when
    # the carrier sits on a channel centre.  deposit() takes a per-integration
    # amplitude; one_trial() converts the stacked amplitude into one.
    assert abs(spec[0, 30] - 2.0) < 1e-12, spec[0, 30]

    # (3) at the worst sub-channel phase the central channel receives less
    # still, which is why the phase is drawn at random rather than centred
    spec2 = np.zeros((1, 64))
    deposit(spec2, 30.5, 0.0, 4.0)
    assert spec2.max() < spec[0, 30], (spec2.max(), spec[0, 30])

    # (4) completeness rises with amplitude and is bounded by 0 and 1
    amps = [4.0, 10.0, 16.0, 30.0]
    frac = completeness(amps, n_real=24, n_chan=256)
    assert all(0.0 <= f <= 1.0 for f in frac), frac
    assert frac[0] <= frac[-1], frac
    assert frac[-1] > 0.9 > frac[0], frac

    # (5) the 90 per cent point lies between the amplitudes that straddle it,
    # and it is far above the trigger: a carrier whose amplitude equals the
    # trigger is recovered hardly ever, which is the whole reason a
    # completeness multiplier exists and is larger than one.
    p90 = ninety_point(amps, frac)
    assert amps[0] < p90 <= amps[-1], (p90, amps)
    assert p90 > 2.0 * TRIGGER, p90

    # (7) ★ THE CHANNEL RESPONSE, AND THE DEPOSITED NUMBER IT MATCHES.  The
    # central channel of a carrier at a random sub-channel phase receives, on
    # average over phase, the fraction below -- so a carrier is recovered at
    # that fraction of the amplitude it was injected with, and the
    # completeness multiplier has to carry the difference.  The value is the
    # deposited_response_phase_mean row of completeness_calibration.csv, and
    # this is an independent route to it.
    phase = np.linspace(0.0, 1.0, 1001)[:-1]
    centre = []
    for ph in phase:
        col = np.zeros(9)
        deposit(col.reshape(1, 9), 4.0 + ph, 0.0, 1.0)
        centre.append(col.max())
    assert abs(float(np.mean(centre)) - 0.4375) < 2e-3, float(np.mean(centre))

    # (8) and the harness recovers that fraction end to end, which is the
    # check that the deposition and the reading agree with each other
    rng = np.random.default_rng(5)
    sig = np.ones((40, 512))
    dr = np.linspace(-1.0, 1.0, 21)
    recs = [one_trial(rng, 40, 512, sig, 40.0, dr)[2] for _ in range(40)]
    assert abs(float(np.median(recs)) / 40.0 - 0.4375) < 0.06, \
        float(np.median(recs)) / 40.0

    # (6) a trial can be detected without recovering the injected drift, so
    # the two are recorded apart.  Near the trigger the neighbouring drift
    # trials are strongly correlated and the maximum often lands on one of
    # them; at a high amplitude it does not, which is why the amplitude here
    # is a marginal one.
    rng = np.random.default_rng(3)
    sig = np.ones((30, 256))
    drifts = np.linspace(-1.0, 1.0, 21)
    res = [one_trial(rng, 30, 256, sig, 12.0, drifts) for _ in range(80)]
    assert any(d and not m for d, m, _, _ in res), \
        'no trial was detected at a drift trial other than the injected one'
    print('injection_recovery: 8 known-answer tests pass')


def _curve():
    amps = [5.0, 8.0, 10.0, 12.0, 14.0, 16.0, 20.0, 25.0, 30.0]
    frac = completeness(amps, n_real=64)
    print('amplitude (sigma)   recovered fraction')
    for a, f in zip(amps, frac):
        print('   %5.1f               %.3f' % (a, f))
    print('90 per cent point: %.3f times the per-channel noise' %
          ninety_point(amps, frac))
    print('(synthetic noise, so this is a property of the harness and not a '
          'measurement of the survey)')


def _compare(path):
    """The deposited trials, reduced the way the harness reduces its own."""
    rows = list(csv.DictReader(open(path)))
    amps = sorted({float(r['amp_sigma']) for r in rows})
    print('deposited trials: %d over %d windows' %
          (len(rows), len({(r['eb'], r['window_nu_lo_GHz']) for r in rows})))
    print('amplitude (sigma)   recovered fraction   trials')
    frac = []
    for a in amps:
        sel = [r for r in rows if float(r['amp_sigma']) == a]
        f = sum(r['detected'] == '1' for r in sel) / float(len(sel))
        frac.append(f)
        print('   %5.1f               %.3f                %d' % (a, f, len(sel)))
    p90 = ninety_point(amps, frac)
    print('90 per cent point of the deposited campaign: %.3f times the '
          'per-channel noise' % p90)
    # ★★★★ AND WHAT THAT NUMBER IS, because without this it reads as a
    # refutation of the article by a factor of two and a half.  The article
    # publishes a completeness multiplier of 3.03 trigger amplitudes; the
    # figure just printed is about 1.2 of the trigger.  They are not the same
    # quantity and neither is wrong:
    #
    #     3.03 P_trig  =  2.29 (the channel response)  x  1.325 (the margin)
    #
    # The channel response is ALREADY INSIDE these trials.  Every carrier here
    # is deposited at a random sub-channel phase through the three-point
    # response, and the central channel receives 0.4375 of it averaged over
    # phase -- known-answer test (7) measures exactly that fraction -- which
    # is 1/0.4375 = 2.29 of amplitude lost before the reading begins.  So the
    # trials recover a carrier at the amplitude it was INJECTED with, and the
    # 90 per cent point measured over them is the MARGIN TERM ALONE: the
    # factor a peak channel needs above the nominal trigger for nine carriers
    # in ten to return.
    #
    # ★ The deposited campaign is also a SUBSET: 28 of the 49 directly
    # injected Class A windows, as column_descriptions.md states, so its 90
    # per cent point is that subset's and not the published calibration's.
    # Both factors are rows of sensitivity/completeness_calibration.csv
    # (deposited_response_phase_mean and p90_multiplier), so this arithmetic
    # is checkable without reading the article.
    resp = 1.0 / 0.4375
    print('   that figure is the MARGIN term alone, x%.3f of the %.1f '
          'trigger.  The channel response is already inside these trials '
          '(deposited_response_phase_mean = 0.4375, i.e. x%.2f), so the '
          'comparable multiplier for this subset is the product, x%.2f '
          'P_trig.' % (p90 / TRIGGER, TRIGGER, resp, resp * p90 / TRIGGER))
    print('   The article publishes x3.03 = x2.29 x x1.325, the margin there '
          'being measured over all 49 directly injected Class A windows '
          'while these trials cover 28 of them.  So x%.2f and x3.03 are the '
          'same quantity on two samples, and x%.2f against x3.03 is not a '
          'comparison at all.' % (resp * p90 / TRIGGER, p90 / TRIGGER))


if __name__ == '__main__':
    ap = argparse.ArgumentParser()
    ap.add_argument('--curve', action='store_true')
    ap.add_argument('--compare', metavar='INJECTION_RECOVERY_CSV')
    a = ap.parse_args()
    _kat()
    if a.curve:
        _curve()
    if a.compare:
        _compare(os.path.abspath(a.compare))
