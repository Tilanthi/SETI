#!/usr/bin/env python3
"""Rebuild the per-system sensitivity summaries from the deposited tables.

    python3 sensitivity_summary.py [--data DIR] [--json FILE]

Reads three files of sensitivity/ and nothing else:

  sensitivity_resampling_windows.csv     every Class A window that constrains
                                         bandwidth, in order, with the part of
                                         its EIRP_90 limit that does not depend
                                         on the completeness factor
  sensitivity_resampling_pool.csv        the injected windows' own factors
  sensitivity_resampling_parameters.csv  the class factor, its calibration
                                         interval, the level, the seed, the
                                         trial count

A window's limit is its factor-free part times a completeness factor, and a
system's limit is the smallest over its windows.  Every median and count over
systems is over the systems whose positional loss is bounded
(position_bounded = 1), as in the article; the others' windows are still
drawn, so the draws are those of the computation the article reports.  The
program prints:

  the median, over systems, of each system's best-window limit, and the number
  of systems at or below the level (1e15 W), with every window at the class
  factor;
  the same with the class factor at both ends of its calibration interval,
  which moves every window together;
  four resamplings of the window-to-window dispersion: each non-injected
  window's factor drawn from the pool independently (`window`) or one draw per
  execution block (`block`), from the pool centred on the class factor or as
  measured (`window_raw`), and the window draw with each window's
  decorrelation factor applied (`window_dec`); an injected window keeps its own
  measured factor.  For each: the median of the system medians and its 5-95
  per cent range, and the 5-95 per cent range of the count.

The draws are NumPy's default generator from the deposited seed, in that
order, so with the NumPy release the parameters file names they are those of
the computation the article reports.  Needs Python 3 and numpy.
"""
import argparse
import csv
import json
import os
import sys

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
AP = argparse.ArgumentParser(description=__doc__.split('\n')[0])
AP.add_argument('--data', default=os.path.join(HERE, '..'))
AP.add_argument('--json', default=None)


def read(path):
    with open(path, newline='') as fh:
        return list(csv.DictReader(fh))


def q(a, p):
    a = sorted(a)
    return a[int(round(p * (len(a) - 1)))]


def sci(x):
    e = int(np.floor(np.log10(x)))
    return '%.1fe%d' % (x / 10.0 ** e, e)


def main():
    a = AP.parse_args()
    sd = os.path.join(a.data, 'sensitivity')
    par = {r['parameter']: r['value'] for r in
           read(os.path.join(sd, 'sensitivity_resampling_parameters.csv'))}
    win = read(os.path.join(sd, 'sensitivity_resampling_windows.csv'))
    win.sort(key=lambda r: int(r['window_order']))
    pool_raw = np.array([float(r['own_factor']) for r in sorted(
        read(os.path.join(sd, 'sensitivity_resampling_pool.csv')),
        key=lambda r: int(r['pool_order']))])
    f0, flo, fhi = (float(par['class_factor']), float(par['factor_lo']),
                    float(par['factor_hi']))
    level = float(par['level_W'])
    seed, ntrial = int(par['seed']), int(par['n_trial'])
    systems = sorted({r['system_id'] for r in win})
    sidx = {s: i for i, s in enumerate(systems)}
    blocks = sorted({r['eb'] for r in win})
    bidx = {e: i for i, e in enumerate(blocks)}
    w_sys = np.array([sidx[r['system_id']] for r in win])
    w_eb = np.array([bidx[r['eb']] for r in win])
    w_base = np.array([float(r['factor_free_limit_W']) for r in win])
    is_inj = np.array([r['injected'] == '1' for r in win])
    ownv = np.array([float(r['own_factor']) if r['injected'] == '1' else f0
                     for r in win])
    decv = np.array([float(r['decorrelation_factor']) for r in win])
    pool = pool_raw * f0 / pool_raw.mean()

    def sys_limits(fac):
        out = np.full(len(systems), np.inf)
        np.minimum.at(out, w_sys, w_base * fac)
        return out

    nom = sys_limits(np.full(len(win), f0))
    cal_lo, cal_hi = (sys_limits(np.full(len(win), f0 * flo)),
                      sys_limits(np.full(len(win), f0 * fhi)))
    # the median, the extremes and the counts the article prints -- and the resampled medians and counts -- leave
    # out the systems whose positional loss is unbounded (position_bounded = 0)
    pb = {}
    for r in win:
        pb[r['system_id']] = r.get('position_bounded', '1') == '1'
    bnd = np.array([pb[s] for s in systems])
    rng = np.random.default_rng(seed)

    def run_mc(mode, pl, extra=None):
        meds, cnts = [], []
        for _ in range(ntrial):
            if mode == 'window':
                draw = pl[rng.integers(0, len(pl), len(win))]
            else:
                draw = pl[rng.integers(0, len(pl), len(blocks))][w_eb]
            fac = np.where(is_inj, ownv, draw)
            if extra is not None:
                fac = fac * extra
            b = sys_limits(fac)
            meds.append(float(np.median(b[bnd])))
            cnts.append(int((b[bnd] <= level).sum()))
        return np.array(meds), np.array(cnts)

    mc = {}
    for key, mode, pl, ex in (('window', 'window', pool, None),
                              ('block', 'block', pool, None),
                              ('window_raw', 'window', pool_raw, None),
                              ('window_dec', 'window', pool, decv)):
        mc[key] = run_mc(mode, pl, ex)
    nom_med = float(np.median(nom[bnd]))
    R = [('systems', len(systems), '%d'),
         ('systems with a bounded position', int(bnd.sum()), '%d'),
         ('median best-window EIRP_90 (W)', float(np.median(nom[bnd])), None),
         ('deepest system (W)', float(nom[bnd].min()), None),
         ('shallowest system (W)', float(nom[bnd].max()), None),
         ('systems at or below the level', int((nom[bnd] <= level).sum()), '%d'),
         ('median at the calibration interval low end (W)', float(np.median(cal_lo[bnd])), None),
         ('median at the calibration interval high end (W)', float(np.median(cal_hi[bnd])), None),
         ('count at the calibration interval high end', int((cal_hi[bnd] <= level).sum()), '%d'),
         ('count at the calibration interval low end', int((cal_lo[bnd] <= level).sum()), '%d')]
    for k, (m_, c_) in mc.items():
        R += [('%s draw: median of system medians (W)' % k, float(np.median(m_)), None),
              ('%s draw: median 5 per cent (W)' % k, float(q(m_, .05)), None),
              ('%s draw: median 95 per cent (W)' % k, float(q(m_, .95)), None),
              ('%s draw: count 5 per cent' % k, int(q(c_, .05)), '%d'),
              ('%s draw: count 95 per cent' % k, int(q(c_, .95)), '%d'),
              ('%s draw: median shift (per cent)' % k,
               abs(100.0 * (float(np.median(m_)) / nom_med - 1.0)), '%.0f')]
    print('sensitivity summaries over %d systems, %d windows, %d trials per draw'
          % (len(systems), len(win), ntrial))
    out = []
    for name, v, fmt in R:
        shown = sci(v) if fmt is None else fmt % v
        print('  %-52s %s' % (name, shown))
        out.append(dict(quantity=name, value=v, printed=shown))
    if a.json:
        with open(a.json, 'w') as fh:
            json.dump(dict(results=out,
                           med_sums={k: float(np.sum(v[0])) for k, v in mc.items()}),
                      fh, indent=1)
    return 0


if __name__ == '__main__':
    sys.exit(main())
