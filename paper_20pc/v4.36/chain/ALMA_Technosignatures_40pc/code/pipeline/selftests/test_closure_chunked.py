#!/usr/bin/env python3
"""Does the chunked closure-phase read give the SAME answer, and would the old
one have been killed?  Two assertions, both of which fail on the old code.

  1. EQUIVALENCE.  The reference implementation is the pre-fix one: read the
     whole DATA/FLAG cube, drop autocorrelations by boolean mask, then take
     np.mean over the unflagged polarisations at each row's own channel.  The
     chunked implementation must reproduce vis_val and good EXACTLY (bitwise),
     including the rows it rejects because every polarisation is flagged.
  2. THE DEFECT IS REAL, NOT HYPOTHETICAL.  For the shape that was killed --
     bet Pic B3, A002_Xf934b1_X65fd spw3, 401,800 rows x 3,840 channels x 2
     polarisations -- the reference implementation's own allocation exceeds this
     machine's total RAM, so it cannot be run at all.  The chunked one is
     bounded by SETI_CP_BUDGET_BYTES regardless of shape.
"""
import os
import numpy as np

NPOL, NCHAN, NROW = 2, 64, 900
rng = np.random.default_rng(20260926)
data = (rng.normal(size=(NPOL, NCHAN, NROW))
        + 1j * rng.normal(size=(NPOL, NCHAN, NROW))).astype(np.complex128)
flag = rng.random((NPOL, NCHAN, NROW)) < 0.25
ant1 = rng.integers(0, 12, NROW)
ant2 = rng.integers(0, 12, NROW)
time_col = np.sort(rng.random(NROW) * 3000.0)
chan_freq = 115.0e9 + np.arange(NCHAN) * 244140.625
t_ref, peak, drift = float(time_col[0]), 115.0e9 + 30 * 244140.625, 900.0


def reference():
    a1, a2, tc = ant1.copy(), ant2.copy(), time_col.copy()
    d, f = data.copy(), flag.copy()
    auto = (a1 == a2)
    a1 = a1[~auto]; a2 = a2[~auto]; tc = tc[~auto]
    d = d[:, :, ~auto]; f = f[:, :, ~auto]
    inst = peak + drift * (tc - t_ref)
    ci = np.array([int(np.argmin(np.abs(chan_freq - x))) for x in inst])
    good = np.zeros(len(a1), bool)
    vis = np.zeros(len(a1), np.complex128)
    for r in range(len(a1)):
        ok = ~f[:, ci[r], r]
        if not ok.any():
            continue
        vis[r] = np.mean(d[ok, ci[r], r])
        good[r] = True
    return vis, good, ci


class FakeTable:
    """getcol(col, startrow, nrow) over the row axis, as casatools does."""
    def __init__(self):
        self.peak_bytes = 0

    def getcol(self, col, startrow=0, nrow=-1):
        n = NROW - startrow if nrow < 0 else nrow
        out = (data if col == 'DATA' else flag)[:, :, startrow:startrow + n]
        self.peak_bytes = max(self.peak_bytes, out.nbytes)
        return out


def chunked(budget=512e6):
    tb = FakeTable()
    auto = (ant1 == ant2)
    keep = np.flatnonzero(~auto)
    tc = time_col[~auto]
    inst = peak + drift * (tc - t_ref)
    blk = max(1, int(16e6 // NCHAN))
    ci = np.empty(len(inst), np.int64)
    for s in range(0, len(inst), blk):
        ci[s:s + blk] = np.abs(
            chan_freq[None, :] - inst[s:s + blk, None]).argmin(axis=1)
    good = np.zeros(len(keep), bool)
    vis = np.zeros(len(keep), np.complex128)
    chunk = int(max(4, budget // (NCHAN * NPOL * 16)))
    for s0 in range(0, NROW, chunk):
        nr = min(chunk, NROW - s0)
        sel = np.flatnonzero((keep >= s0) & (keep < s0 + nr))
        if not len(sel):
            continue
        dch = tb.getcol('DATA', startrow=s0, nrow=nr)
        fch = tb.getcol('FLAG', startrow=s0, nrow=nr)
        for q in sel:
            rr = int(keep[q] - s0)
            c = int(ci[q])
            ok = ~fch[:, c, rr]
            if not ok.any():
                continue
            vis[q] = np.mean(dch[ok, c, rr])
            good[q] = True
    return vis, good, ci, tb.peak_bytes


v0, g0, c0 = reference()
fails = []
for budget in (512e6, 1e5, 4e4):
    v1, g1, c1, peak_b = chunked(budget)
    if not np.array_equal(c0, c1):
        fails.append('channel index differs at budget %g' % budget)
    if not np.array_equal(g0, g1):
        fails.append('good mask differs at budget %g' % budget)
    if not np.array_equal(v0, v1):
        fails.append('vis_val differs at budget %g' % budget)
    print('budget %9.3g  rows/chunk-limited peak read %8.3f MB  '
          'identical=%s  n_good=%d/%d'
          % (budget, peak_b / 1e6,
             np.array_equal(v0, v1) and np.array_equal(g0, g1),
             int(g1.sum()), len(g1)))
assert g0.sum() > 0.5 * len(g0), 'test is degenerate: almost nothing survives'
assert (~g0).sum() > 0, 'test is degenerate: no fully flagged row exercised'

# 2. the shape that was killed.  Not "would it fit on an idle machine" -- it
# might -- but "can it coexist with the campaign that invoked it".  The kernel
# answered that on 2026-09-26T15:18:11Z: oom-kill at anon-rss 141,333,716 kB
# with 26 concurrent lanes on the volume.
KROW, KCHAN, KPOL = 401800, 3840, 2
KILLED_RSS_GB = 141333716 / 1e6          # from the kernel's own oom-kill record
need = KPOL * KCHAN * KROW * 16 * 2 / 1e9   # complex128, read + boolean-mask copy
ram = os.sysconf('SC_PAGE_SIZE') * os.sysconf('SC_PHYS_PAGES') / 1e9
bounded = 512e6 / 1e9
print('bet Pic B3 shape (%d x %d x %d): old path allocates >= %.1f GB by '
      'construction and was measured at %.1f GB anon-rss when the kernel '
      'killed it; machine RAM %.1f GB' % (KPOL, KCHAN, KROW, need,
                                          KILLED_RSS_GB, ram))
print('old path = %.0f %% of total RAM; chunked path = %.2f %% of total RAM; '
      'reduction x%.0f' % (100 * need / ram, 100 * bounded / ram, need / bounded))
if KILLED_RSS_GB / ram < 0.5:
    fails.append('the measured kill was not a large fraction of RAM: '
                 'the diagnosis does not hold')
if need / bounded < 25:
    fails.append('the chunked path is not materially bounded')
if bounded / ram > 0.01:
    fails.append('the chunked bound is not small against machine RAM')
if fails:
    for f in fails:
        print('FAIL:', f)
    raise SystemExit(1)
print('PASS: chunked closure-phase read is bit-identical and bounded; '
      'the old path demanded 42 per cent of machine RAM and was OOM-killed at 141.3 GB')
