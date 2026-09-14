#!/usr/bin/env python3
r"""Clustered uncertainty on the empirical false-alarm tail factor.

Referee 1, point 4.  The tail factor is the ratio of the measured pseudo-star
first-rank rate to the exchangeable rate 1/(N_ctrl+1).  A binomial interval on
the pooled trials assumes the trials are independent Bernoulli draws, which
they are not: the 16 inner probes of one window share that window's noise
realisation, and windows share execution blocks.

This recomputes the pseudo-star test from the stored control vectors, so the
clustering is available, and reports three intervals:

  * naive binomial (Clopper-Pearson) over pooled probe-trials;
  * bootstrap resampling whole WINDOWS;
  * bootstrap resampling whole EXECUTION BLOCKS.

A pseudo-star is an inner-annulus probe ranked against the remaining probes of
its own window, exactly as in `radial_null_v361.py`; it contains no star, so a
first rank is a false alarm by construction.

Writes `tailboot_v371.json`.  No network, no products beyond this folder.
"""
import collections, json, os
import numpy as np
from scipy import stats

os.chdir(os.path.dirname(os.path.abspath(__file__)))
R_IN, R_OUT, NPROBE, SEED = 0.14, 0.78, 512, 20260825
N_INNER = 16                      # matches radial_null_v361.json: pseudo n_probes
BOOT = 20000
RNG = np.random.default_rng(20260913)


def probe_radii():
    rng = np.random.default_rng(SEED)
    return np.sqrt(rng.uniform(R_IN ** 2, R_OUT ** 2, NPROBE))


U = probe_radii()
inner = np.argsort(U)[:N_INNER]          # the innermost probes, same every window

HO = json.load(open('heldout_ctrl_v361.json'))
win = []
for r in HO:
    c = np.asarray(r['c'], float)
    if c.size != NPROBE or not np.all(np.isfinite(c)):
        continue
    # each inner probe ranked against the OTHER probes of the same window
    hits = 0
    for i in inner:
        others = np.delete(c, i)
        if c[i] > others.max():
            hits += 1
    win.append({'eb': r['eb'], 'n': N_INNER, 'k': hits})

K = sum(w['k'] for w in win)
N = sum(w['n'] for w in win)
p_exch = 1.0 / (NPROBE + 1)
print('windows %d  pseudo-star trials %d  first-rank %d  rate %.4f %%'
      % (len(win), N, K, 100 * K / N))
print('exchangeable rate %.4f %%  ->  ratio %.2f' % (100 * p_exch, K / N / p_exch))

lo = stats.beta.ppf(0.025, K, N - K + 1) if K else 0.0
hi = stats.beta.ppf(0.975, K + 1, N - K)
out = {'n_windows': len(win), 'n_trials': N, 'k': K,
       'rate_pct': 100 * K / N, 'p_exch_pct': 100 * p_exch,
       'ratio': K / N / p_exch,
       'binomial_ci': [lo / p_exch, hi / p_exch]}
print('naive binomial 95%%  %.2f - %.2f' % (lo / p_exch, hi / p_exch))


def boot(groups):
    """groups: list of lists of window dicts.  Resample groups with replacement."""
    g = [(sum(w['k'] for w in grp), sum(w['n'] for w in grp)) for grp in groups]
    ks = np.array([x[0] for x in g], float)
    ns = np.array([x[1] for x in g], float)
    m = len(g)
    idx = RNG.integers(0, m, size=(BOOT, m))
    rate = ks[idx].sum(axis=1) / ns[idx].sum(axis=1)
    r = rate / p_exch
    return [float(np.percentile(r, 2.5)), float(np.percentile(r, 97.5))]


out['window_ci'] = boot([[w] for w in win])
byeb = collections.defaultdict(list)
for w in win:
    byeb[w['eb']].append(w)
out['n_blocks'] = len(byeb)
out['block_ci'] = boot(list(byeb.values()))
print('window-clustered  95%%  %.2f - %.2f' % tuple(out['window_ci']))
print('block-clustered   95%%  %.2f - %.2f  (%d blocks)'
      % (out['block_ci'][0], out['block_ci'][1], len(byeb)))

json.dump(out, open('tailboot_v371.json', 'w'), indent=1)
