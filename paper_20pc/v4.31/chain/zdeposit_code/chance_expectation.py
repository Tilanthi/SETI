#!/usr/bin/env python3
"""Rebuild the chance comparison from the deposited tables alone.

    python3 chance_expectation.py [--data DIR] [--field whole_beam|narrow_field|both]
                                  [--seed N] [--json FILE]

Reads three files of statistics/ and nothing else:

  chance_resampling_windows.csv     one row per Class A window with a control
                                    ensemble, in the order the resampling
                                    consumes them (blocks, then windows)
  chance_resampling_blocks.csv      the control exceedances whose landing channel
                                    is recorded, summed per execution block, in
                                    the order the attributed share is resampled
  chance_resampling_parameters.csv  the seed, the draw sizes, the observed count
                                    and the scalar inputs

and prints, for each field reading, the quantities the article quotes:

  expected at the trigger         sum over windows of n_ctrl_trig / n_ctrl
  chance expectation              the same, each window reduced by its
                                  attributed share and by the atmospheric factor
  P(count >= observed)            mean over the block resamplings of the Poisson
                                  upper tail at each resampled expectation
  added-population bound          the largest number of further crossings that
                                  still leaves the observed count credible at
                                  the stated level, and the probabilities at it
                                  and one above it
  interval on the expectation     central percentiles of the resampled
                                  expectation, without and with the transfer band
  the stellar-calibrated reading  the expectation scaled by the star-to-control
                                  ratio measured in the band below the trigger,
                                  its probability and its bound

THE RESAMPLING.  Execution blocks are resampled with replacement, because the
windows of one block share calibration and noise.  Inside every realisation
each window's control rate is redrawn as a binomial on its own n_ctrl
positions; the attributed share of the windows marked `measured` is one value
per realisation, the share of recorded exceedances landing inside the mask
over a block resampling of chance_resampling_blocks.csv; a window marked
`grid` keeps the share of its channel grid the mask covers; the atmospheric
share is a binomial on the exceedances the mask leaves.  The realisations are
split into n_batches disjoint batches and resampling b reads only batch
(b mod n_batches), so the scatter of the batch means is the Monte Carlo error
quoted beside every probability.

With the deposited seed and the NumPy release the parameters file names the
draws are those of the computation the article reports, so every value below
is reproduced exactly; with another seed, or another NumPy release whose
generator streams differ, the Monte Carlo quantities agree within the quoted
Monte Carlo error and the deterministic sums are unchanged.  Needs Python 3,
numpy and scipy.
"""
import argparse
import csv
import json
import math
import os
import sys

import numpy as np
from scipy.special import gammainc, gammaincc

HERE = os.path.dirname(os.path.abspath(__file__))
AP = argparse.ArgumentParser(description=__doc__.split('\n')[0])
AP.add_argument('--data', default=os.path.join(HERE, '..'),
                help='the unzipped archive (the directory holding statistics/)')
AP.add_argument('--field', default='both',
                choices=['whole_beam', 'narrow_field', 'both'])
AP.add_argument('--seed', type=int, default=None,
                help='override the deposited seed (shows the Monte Carlo error)')
AP.add_argument('--json', default=None, help='also write the results here')


def read(path):
    with open(path, newline='') as fh:
        return list(csv.DictReader(fh))


def p_at_least(k, lam):
    """P(N >= k) for a Poisson count of mean lam, vectorised over lam."""
    return gammainc(k, np.asarray(lam, float))


def p_at_most(k, lam):
    return gammaincc(k + 1.0, np.asarray(lam, float))


class Reading:
    """One field reading: its inputs, and the resampling run on them."""

    def __init__(self, data, field, seed=None):
        st = os.path.join(data, 'statistics')
        self.field = field
        win = [r for r in read(os.path.join(st, 'chance_resampling_windows.csv'))
               if r['field_reading'] == field]
        blk = [r for r in read(os.path.join(st, 'chance_resampling_blocks.csv'))
               if r['field_reading'] == field]
        par = {r['parameter']: r['value'] for r in
               read(os.path.join(st, 'chance_resampling_parameters.csv'))
               if r['field_reading'] == field}
        if not win:
            raise SystemExit('no windows for field reading %r' % field)
        self.P = par
        g = lambda k: float(par[k])                      # noqa: E731
        gi = lambda k: int(par[k])                       # noqa: E731
        self.seed = gi('seed') if seed is None else seed
        self.NREAL, self.NBATCH, self.NBOOT = (gi('n_realisations'),
                                               gi('n_batches'), gi('n_boot'))
        self.N_OBS = gi('n_observed')
        self.N_REF = gi('n_reference_windows')
        self.SCALE = g('scale')
        self.ALPHA = g('alpha')
        self.COV = g('coverage_pct')
        self.N_EXC = gi('n_exc_recorded')
        self.A_MEAS = gi('n_exc_in_mask') / float(self.N_EXC)
        self.SURV = gi('n_exc_survive_mask')
        self.TL_FAC = ((self.SURV - gi('n_exc_telluric_only')) / float(self.SURV)
                       if self.SURV else 1.0)
        self.N_HOL = gi('n_holdout_blocks')
        self.TR = (g('transfer_band_lo'), g('transfer_band_hi'))
        self.NEAR = ((gi('near_n_star_events') / float(gi('near_n_windows')))
                     / (gi('near_n_control_events')
                        / float(gi('near_n_control_positions'))))
        self.MAX_EXT = gi('max_ext_chunks')
        # the blocks, in order, each with its windows in order
        win.sort(key=lambda r: (int(r['block_order']), int(r['window_order'])))
        self.blocks = []
        for r in win:
            j = int(r['block_order'])
            while len(self.blocks) <= j:
                self.blocks.append([])
            self.blocks[j].append(dict(
                n=int(r['n_ctrl']), nt=int(r['n_ctrl_trig']),
                measured=(r['attribution'] == 'measured'),
                grid=float(r['grid_mask_share'])))
        assert all(self.blocks), 'a block with no window'
        self.NB = len(self.blocks)
        self.NW = np.array([len(b) for b in self.blocks], float)
        blk.sort(key=lambda r: int(r['attr_order']))
        self.AA = np.array([float(r['n_exc_in_mask']) for r in blk])
        self.AB = np.array([float(r['n_exc_recorded']) for r in blk])
        assert int(self.AA.sum()) == gi('n_exc_in_mask'), 'block sums'
        assert int(self.AB.sum()) == self.N_EXC, 'block sums'
        self.BATCH = np.arange(self.NBOOT) % self.NBATCH

    # ------------------------------------------------------------ point sums
    def point(self):
        e_trig = e_cen = 0.0
        for b in self.blocks:
            for w in b:
                p = w['nt'] / float(w['n'])
                att = self.A_MEAS if w['measured'] else w['grid']
                e_trig += p
                e_cen += p * (1.0 - att) * self.TL_FAC
        return e_trig * self.SCALE, e_cen * self.SCALE

    # ------------------------------------------------------- the realisations
    def _bv(self, g, real_batched):
        nak = len(self.AA)
        pk = g.integers(0, nak, size=(self.NREAL, nak))
        a_draw = self.AA[pk].sum(axis=1) / self.AB[pk].sum(axis=1)
        if real_batched:
            # the binomial counterpart of the share is drawn and not used: it
            # is kept so that the stream matches the computation reported
            g.binomial(self.N_EXC, self.A_MEAS, self.NREAL)
        tl = (1.0 - g.binomial(self.SURV, 1.0 - self.TL_FAC, self.NREAL)
              / float(self.SURV) if self.SURV else np.ones(self.NREAL))
        bv = np.empty((self.NB, self.NREAL))
        for j, b in enumerate(self.blocks):
            acc = np.zeros(self.NREAL)
            for w in b:
                n, p = w['n'], w['nt'] / float(w['n'])
                att = a_draw if w['measured'] else np.full(self.NREAL, w['grid'])
                acc += g.binomial(n, p, self.NREAL) / float(n) * (1.0 - att)
            bv[j] = acc * tl
        pick = g.integers(0, self.NB, size=(self.NBOOT, self.NB))
        if real_batched:
            rpb = self.NREAL // self.NBATCH
            real = (self.BATCH[:, None] * rpb
                    + g.integers(0, rpb, size=(self.NBOOT, self.NB)))
        else:
            real = g.integers(0, self.NREAL, size=(self.NBOOT, self.NB))
        return (bv[pick, real].sum(axis=1) / self.NW[pick].sum(axis=1)) * self.N_REF

    def run(self):
        rng = np.random.default_rng(self.seed)
        self.boot = self._bv(rng, True)
        # the stream then passes through the hold-out block resampling, which
        # the reported computation draws next; its size is all that matters
        rng.integers(0, self.N_HOL, size=(self.NBOOT, self.N_HOL))
        self.boot_tr = (self.boot[rng.integers(0, self.boot.size, self.NBOOT)]
                        * rng.uniform(self.TR[0], self.TR[1], self.NBOOT))
        return self

    # --------------------------------------------------------- Monte Carlo
    def se(self, a):
        bm = np.array([a[self.BATCH == k].mean() for k in range(self.NBATCH)])
        return float(bm.std(ddof=1) / math.sqrt(self.NBATCH))

    def lim(self, lam):
        lam = np.asarray(lam, float)

        def p_low(add):
            return float(p_at_most(self.N_OBS, lam + add).mean())
        lo, hi = 0.0, 1.0
        while p_low(hi) > self.ALPHA and hi < 1.0e4:
            hi *= 2.0
        for _ in range(60):
            mid = 0.5 * (lo + hi)
            if p_low(mid) > self.ALPHA:
                lo = mid
            else:
                hi = mid
        return 0.5 * (lo + hi)

    def lim_stable(self, factor):
        """The integer bound, with its Monte Carlo error from the batches;
        where the integer is not stable within two errors, independent
        replicates of the whole resampling are added (seeds seed*1000 + k)
        until it is, exactly as in the computation reported."""
        lam = self.boot * factor
        x = self.lim(lam)
        bx = np.array([self.lim(lam[self.BATCH == k]) for k in range(self.NBATCH)])
        se = float(bx.std(ddof=1) / math.sqrt(self.NBATCH))
        n = int(math.floor(x))
        if se < 0.25 and math.floor(x - 2 * se) == n == math.floor(x + 2 * se):
            return n, x, se, 1
        lams, ests = [lam], [x]
        while True:
            k = len(lams)
            lk = self._bv(np.random.default_rng(self.seed * 1000 + k), False) * factor
            lams.append(lk)
            ests.append(self.lim(lk))
            if (k + 1 >= 8 and (k + 1) % 8 == 0) or k + 1 >= self.MAX_EXT:
                allv = np.concatenate(lams)
                x = self.lim(allv)
                se = float(np.std(ests, ddof=1) / math.sqrt(len(ests)))
                n = int(math.floor(x))
                stable = math.floor(x - 2 * se) == n == math.floor(x + 2 * se)
                if (se < 0.25 and stable) or se < 0.001 or k + 1 >= self.MAX_EXT:
                    return n, x, se, len(ests)

    def results(self):
        e_trig, e_cen = self.point()
        lo_q, hi_q = (100.0 - self.COV) / 2.0, 100.0 - (100.0 - self.COV) / 2.0
        pt = p_at_least(self.N_OBS, self.boot)
        n_lim, x_lim, se_lim, nrep = self.lim_stable(1.0)
        p_at = p_at_most(self.N_OBS, self.boot + n_lim)
        p_ab = p_at_most(self.N_OBS, self.boot + n_lim + 1)
        pn = p_at_least(self.N_OBS, self.boot * self.NEAR)
        n_near, x_near, se_near, nrep_near = self.lim_stable(self.NEAR)
        R = [
            ('observed unattributed Class A crossings', self.N_OBS, None, None),
            ('expected to reach the trigger', e_trig, None, '%.1f'),
            ('chance expectation', e_cen, None, '%.1f'),
            ('P(count >= observed)', float(pt.mean()), self.se(pt), '%.2f'),
            ('added-population bound', n_lim, se_lim, '%d'),
            ('added-population bound, continuous', x_lim, se_lim, '%.3f'),
            ('P(count <= observed) at the bound', float(p_at.mean()), self.se(p_at), '%.3f'),
            ('P(count <= observed) one above it', float(p_ab.mean()), self.se(p_ab), '%.3f'),
            ('expectation interval low', float(np.percentile(self.boot, lo_q)), None, '%.0f'),
            ('expectation interval high', float(np.percentile(self.boot, hi_q)), None, '%.0f'),
            ('expectation interval with transfer, low', float(np.percentile(self.boot_tr, lo_q)), None, '%.0f'),
            ('expectation interval with transfer, high', float(np.percentile(self.boot_tr, hi_q)), None, '%.0f'),
            ('star-to-control ratio below the trigger', self.NEAR, None, '%.3f'),
            ('stellar-calibrated expectation', e_cen * self.NEAR, None, '%.1f'),
            ('stellar-calibrated P(count >= observed)', float(pn.mean()), self.se(pn), '%.2f'),
            ('stellar-calibrated added-population bound', n_near, se_near, '%d'),
        ]
        self.extra = dict(boot_mean=float(self.boot.mean()),
                          boot_sum=float(self.boot.sum()),
                          replicates_bound=nrep, replicates_near_bound=nrep_near)
        return R


def mc_digits(v, se, dp):
    """The digits a Monte Carlo probability is printed to: the requested
    number of places, less one while the Monte Carlo error is not below a
    quarter of the last place, or while the value lies within two standard
    errors of a rounding boundary at that place (so that another seed could
    not change the printed digits)."""
    def stable(d):
        return ('%.*f' % (d, v - 2.0 * se) == '%.*f' % (d, v)
                == '%.*f' % (d, v + 2.0 * se))
    while dp > 0 and not (se < 0.25 * 10.0 ** (-dp) and stable(dp)):
        dp -= 1
    return '%.*f' % (dp, v)


def two_reading_correction(p):
    """Bonferroni over the field readings: the smaller probability times the
    number of readings, capped at one."""
    return min(1.0, len(p) * min(p))


def main():
    a = AP.parse_args()
    fields = (['whole_beam', 'narrow_field'] if a.field == 'both' else [a.field])
    out, ps = {}, []
    print('numpy %s; data %s' % (np.__version__, os.path.abspath(a.data)))
    for f in fields:
        r = Reading(a.data, f, a.seed).run()
        res = r.results()
        print('\n%s reading (seed %d, %d realisations, %d block resamplings '
              'of %d blocks)' % (f.replace('_', ' '), r.seed, r.NREAL, r.NBOOT, r.NB))
        rows = []
        for name, v, se, fmt in res:
            shown = ('%d' % v) if fmt is None else (fmt % v)
            if se is not None and name.startswith(('P(', 'stellar-calibrated P(')):
                shown = mc_digits(v, se, int(fmt[2]))
            print('  %-46s %-10s %s' % (name, shown,
                                        '' if se is None else '(MC se %.2g)' % se))
            rows.append(dict(quantity=name, value=v, printed=shown, mc_se=se))
        out[f] = dict(results=rows, extra=r.extra, seed=r.seed)
        ps.append(next(x['value'] for x in rows if x['quantity'] == 'P(count >= observed)'))
    if len(ps) == 2:
        c = two_reading_correction(ps)
        print('\nsmaller probability corrected for the two readings  %.2f' % c)
        out['two_readings'] = dict(corrected_p=c)
    if a.json:
        with open(a.json, 'w') as fh:
            json.dump(out, fh, indent=1)
    return 0


if __name__ == '__main__':
    sys.exit(main())
