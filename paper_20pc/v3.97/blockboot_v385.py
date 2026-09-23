#!/usr/bin/env python3
r"""The survey-level null for stage-1 outliers, by block-level resampling.

Referee 1's fifth required change. A Poisson calculation on 1655/513
treats the windows as independent trials, which the paper itself says
they are not: windows share execution blocks, correlator setups, weather
and targets. The dependence structure is knowable, so use it.

Resample whole EXECUTION BLOCKS with replacement, preserving every
within-block correlation, and count how many stage-1 outliers a survey of
this structure produces under the null. The null is supplied by the data
themselves: for each window we already have 512 control values from
positions containing no star, so ranking a randomly chosen control against
the others gives a draw from the no-signal distribution of the statistic.

Writes blockboot_v385.json and survey_numbers_round35.tex.
"""
import collections, csv, json

import numpy as np

NPROBE, NBOOT = 512, 20000
RNG = np.random.default_rng(20260920)
FLOOR = 1.0 / (NPROBE + 1)

EXP = json.load(open('frozen_export_v3.81_survey.json'))['rows']
CAT = {}
for r in csv.DictReader(open('per_target_results_v3.97.csv')):
    CAT[(r['eb'], round(min(float(r['flo_GHz']), float(r['fhi_GHz'])), 4))] = r

# Reference sets. All 1655 searched windows were screened, so every one of
# them was eligible a priori; but all NStageOne stage-1 flags are Class A,
# and a coarse channel dilutes a narrow feature, so the Class A set is the
# narrower and arguably the honest reference class. We report both and let
# the reader see that the answer depends on the choice.
byblock = collections.defaultdict(list)
byblockA = collections.defaultdict(list)
seen = set()
for r in EXP:
    c = np.asarray(r.get('ctrl_all') or [], float)
    # Q14: (eb, flo) alone is degenerate where one execution block holds
    # two targets in the same tuning.
    key = (r['eb'], round(min(r['flo'], r['fhi']), 4))
    if c.size != NPROBE or key in seen or key not in CAT:
        continue
    seen.add(key)
    byblock[r['eb']].append(1)
    if CAT[key]['search_class'] == 'A':
        byblockA[r['eb']].append(1)

# The per-window null rate. Under exchangeability it is 1/(NPROBE+1); the
# calibration sample measures the true rate for a no-signal position to be
# TAIL times that, and that factor is the one thing here that is measured
# rather than assumed. The rate is NOT measured per window -- only the
# clustering of windows within blocks is resampled.
# The tail factor is measured twice: 1.4 on the processing-order set and
# 1.22 on the pre-registered hold-out, whose block-clustered 95 per cent
# interval is 0.61-1.87. Propagating a single value would hide that the
# factor does not replicate tightly, so the null is run across the
# hold-out interval as well as at the in-sample value.
TAIL = 1.4
TAIL_HO, TAIL_LO, TAIL_HI = 1.22, 0.61, 1.87
P_EXCH = 1.0 / (NPROBE + 1.0)


def resample(bb, rate):
    blocks_ = list(bb)
    out = np.empty(NBOOT, dtype=int)
    for b in range(NBOOT):
        pick = RNG.integers(0, len(blocks_), len(blocks_))
        tot = 0
        for i in pick:
            k = len(bb[blocks_[i]])
            if k:
                tot += int((RNG.random(k) < rate).sum())
        out[b] = tot
    return out


blocks = list(byblock)
nwin = sum(len(v) for v in byblock.values())
nwinA = sum(len(v) for v in byblockA.values())
counts = resample(byblock, P_EXCH * TAIL)
countsA = resample(byblockA, P_EXCH * TAIL)
sens = {}
for lab, t in (('ho', TAIL_HO), ('lo', TAIL_LO), ('hi', TAIL_HI)):
    sens[lab] = resample(byblockA, P_EXCH * t)

# v3.85: this was hard-coded to 2, the count under the RADIUS-CORRECTED
# statistic, while every headline number in the paper uses the frozen
# statistic, which gives 4. Read it from the released catalogue so the
# comparison is against the number the paper actually reports.
import csv as _csv
_cat = list(_csv.DictReader(open('per_target_results_v3.97.csv')))
obs = sum(1 for r in _cat if r['stage1_flag'] == 'True'
          and not r['nearest_line'])
if obs == 0:                      # no line column: fall back to disposition
    obs = sum(1 for r in _cat if r['stage1_flag'] == 'True'
              and 'CO' not in str(r['disposition']))
assert obs > 0, 'observed unattributed count is zero'
OUT_OBS = obs
q = [float(np.percentile(counts, p)) for p in (2.5, 50, 97.5)]
pge = float((counts >= obs).mean())
qA = [float(np.percentile(countsA, p)) for p in (2.5, 50, 97.5)]
pgeA = float((countsA >= obs).mean())
res = dict(n_blocks=len(blocks), n_windows=nwin, n_boot=NBOOT,
           mean=float(counts.mean()), median=q[1], lo=q[0], hi=q[2],
           p_ge_observed=pge, observed=obs,
           poisson_naive=nwin / float(NPROBE + 1))
json.dump(res, open('blockboot_v385.json', 'w'), indent=1)

M = ['\\newcommand{\\BootBlocks}{%d}' % len(blocks),
     '\\newcommand{\\BootWin}{%d}' % nwin,
     '\\newcommand{\\BootMean}{%.1f}' % counts.mean(),
     '\\newcommand{\\BootLo}{%.0f}' % q[0],
     '\\newcommand{\\BootHi}{%.0f}' % q[2],
     '\\newcommand{\\BootP}{%.2f}' % pge,
     '\\newcommand{\\BootPoisson}{%.1f}' % (nwin / (NPROBE + 1.0)),
     '\\newcommand{\\BootObs}{%d}' % obs,
     '\\newcommand{\\BootTail}{%.1f}' % TAIL,
     '\\newcommand{\\BootWinA}{%d}' % nwinA,
     '\\newcommand{\\BootMeanA}{%.1f}' % countsA.mean(),
     '\\newcommand{\\BootLoA}{%.0f}' % qA[0],
     '\\newcommand{\\BootHiA}{%.0f}' % qA[2],
     '\\newcommand{\\BootPA}{%.3f}' % pgeA,
     '\\newcommand{\\BootTailHo}{%.2f}' % TAIL_HO,
     '\\newcommand{\\BootTailLo}{%.2f}' % TAIL_LO,
     '\\newcommand{\\BootTailHi}{%.2f}' % TAIL_HI,
     '\\newcommand{\\BootPAHo}{%.3f}' % float((sens['ho'] >= obs).mean()),
     '\\newcommand{\\BootPALo}{%.3f}' % float((sens['lo'] >= obs).mean()),
     '\\newcommand{\\BootPAHi}{%.3f}' % float((sens['hi'] >= obs).mean()),
     '\\newcommand{\\BootWinShort}{%d}' % (len(_cat) - nwin),
     # R1-2: the expectation's own uncertainty, from the tail factor, so
     # the abstract can quote 1.1 with a bracket rather than leave the
     # reader to reconstruct it.
     '\\newcommand{\\BootMeanALo}{%.1f}' % sens['lo'].mean(),
     '\\newcommand{\\BootMeanAHi}{%.1f}' % sens['hi'].mean(),
     '\\newcommand{\\BootMeanAHo}{%.1f}' % sens['ho'].mean()]
open('survey_numbers_round35.tex', 'w').write(
    '% generated by blockboot_v385.py -- do not edit\n' + '\n'.join(M) + '\n')
print('block-resampled null over %d blocks, %d windows, %d draws'
      % (len(blocks), nwin, NBOOT))
print('  expected stage-1 outliers: mean %.1f, 95 per cent %.0f-%.0f'
      % (counts.mean(), q[0], q[2]))
print('  naive Poisson expectation : %.1f' % (nwin / (NPROBE + 1.0)))
print('  P(>= %d observed)         : %.2f' % (obs, pge))
print('  CLASS A reference set only: %d windows, mean %.1f, 95 per cent %.0f-%.0f,'
      % (nwinA, countsA.mean(), qA[0], qA[2]))
print('    P(>= %d observed)       : %.3f' % (obs, pgeA))
print('  per-window rate = %.1f x 1/(%d+1); only the block clustering is'
      ' resampled, not the rate' % (TAIL, NPROBE))
print('  sensitivity to the tail factor, Class A reference set:')
for lab, t in (('hold-out 1.22', TAIL_HO), ('CI low 0.61', TAIL_LO),
               ('CI high 1.87', TAIL_HI)):
    print('    tail %-14s P(>= %d) = %.3f'
          % (lab, obs, float((sens[{'hold-out 1.22': 'ho', 'CI low 0.61': 'lo',
                                    'CI high 1.87': 'hi'}[lab]] >= obs).mean())))
