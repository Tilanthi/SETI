#!/usr/bin/env python3
"""The measured Class-A recovery curve, in one place.

Both the catalogue writer (`v342_calc.py`, which runs early) and the
injection-campaign generator (`v358_inject.py`, which runs late) need the
same numbers from the stratified campaign.  Having the early generator read
a macro written by the late one is a forward dependency, and forward
dependencies in this build have twice been caught only by the clean
regeneration test.  So the arithmetic lives here and both import it.

Everything is derived from one frozen input, `stratified_inject_trials_v3.58.csv`.
"""
import csv, os
import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
TRIALS = os.path.join(HERE, 'stratified_inject_trials_v3.58.csv')

ROWS = list(csv.DictReader(open(TRIALS)))
AMPS = sorted({float(r['amp_sigma']) for r in ROWS})


def curve(rows):
    """Recovery fraction against injected amplitude, in units of sigma."""
    return {a: float(np.mean([r['detected'] == 'True' for r in rows
                              if float(r['amp_sigma']) == a])) for a in AMPS}


def pX(c, x):
    """The amplitude, in sigma, at which the recovery curve first reaches x."""
    xs = sorted(c); ys = [c[a] for a in xs]
    for i in range(1, len(xs)):
        if ys[i - 1] < x <= ys[i]:
            f = (x - ys[i - 1]) / (ys[i] - ys[i - 1]) if ys[i] != ys[i - 1] else 0.0
            return xs[i - 1] + f * (xs[i] - xs[i - 1])
    return float('nan') if ys[-1] < x else xs[0]


WINDOWS = sorted(set(r['window'] for r in ROWS))
_p50 = np.array([pX(curve([r for r in ROWS if r['window'] == w]), 0.5) for w in WINDOWS])
_p90 = np.array([pX(curve([r for r in ROWS if r['window'] == w]), 0.9) for w in WINDOWS])
P50_WIN = _p50[np.isfinite(_p50)]
P90_WIN = _p90[np.isfinite(_p90)]

#: amplitude in sigma at which a pooled trial is recovered half / nine times in ten
P50_POOL = pX(curve(ROWS), 0.5)
P90_POOL = pX(curve(ROWS), 0.9)

#: P_90 expressed as a multiple of the nominal 5-sigma trigger power
P90_OVER_TRIG = P90_POOL / 5.0

#: window-to-window spread of the recovery curve, as a multiplier on the
#: median window.  This is what a single quoted threshold should be read with.
TRANSFER_P50 = (float((P50_WIN / np.median(P50_WIN)).min()),
                float((P50_WIN / np.median(P50_WIN)).max()))
TRANSFER_P90 = (float((P90_WIN / np.median(P90_WIN)).min()),
                float((P90_WIN / np.median(P90_WIN)).max()))

if __name__ == '__main__':
    print('windows %d, trials %d' % (len(WINDOWS), len(ROWS)))
    print('P50 pooled %.2f sigma, P90 pooled %.2f sigma, P90/trigger %.2f'
          % (P50_POOL, P90_POOL, P90_OVER_TRIG))
    print('transfer P50 x%.2f-x%.2f, P90 x%.2f-x%.2f'
          % (TRANSFER_P50 + TRANSFER_P90))
