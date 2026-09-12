#!/usr/bin/env python3
"""v3.50 generator -> survey_numbers_round18.tex

Single-sources the four new quantitative blocks this round needs, so that
nothing below is hand-typed into the manuscript.

  (1) The Bonferroni/rank-floor ratio.  Two places in v3.49 said the
      survey-wide Bonferroni scale lies "two orders of magnitude" below the
      per-window rank floor 1/(N_ctrl+1).  1/513 = 1.95e-3 and the Bonferroni
      scale is 1.2e-4, so the ratio is 16, not 100.  Emitted as a macro so it
      cannot drift from BonferroniThresh and RankFloor again.

  (2) The held-out validation set (referee B4).  Every window of every
      execution block searched by the epoch-extension programme with the
      frozen pipeline, read from heldout_v350.json.  None of those blocks
      played any part in designing the statistic or the mask, so their
      star-rank distribution is a genuine out-of-sample check.  The four
      windows that carry beta Pic CO at the star are separated out: they are
      the astrophysical positive control, not a noise draw.

  (3) The Class A configuration-distance census (referees A6 and B3).  The
      completeness curve was measured on ONE configuration.  For each of the
      118 Class A windows we count how many of five configuration axes lie
      outside a factor of two (or, for the beam offset, outside 0.2 theta_PB)
      of that calibration window, so a reader can see which thresholds are
      supported and which are extrapolated.  Beam offset is inverted from the
      catalogue's own primary-beam factor, smin/(5 rms), through the
      pipeline's Gaussian G = exp(-4 ln2 (r/theta_PB)^2).

  (4) The four withheld epsilon Eri Band 6 windows (referee B, minor): the
      EIRP range they would have covered, from the frozen export, together
      with the primary-beam correction that is the reason they are withheld.

Inputs (all frozen, all in this directory):
  heldout_v350.json          the epoch-extension search products
  per_target_results_v3.52.csv  the released catalogue (431 windows)
  frozen_export_v3.31.json   carries the withheld rows the catalogue drops
  survey_numbers.tex, survey_numbers_round5.tex   for RankFloor/Bonferroni
"""
import csv
import json
import math
import os
import re
import statistics as st

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = []


def M(name, value):
    OUT.append(r'\newcommand{\%s}{%s}' % (name, value))


def texval(fn, macro):
    """Read a value back out of an already-generated macro file."""
    s = open(os.path.join(HERE, fn)).read()
    m = re.search(r'\\newcommand\{\\%s\}\{(.*?)\}\s*$' % macro, s, re.M)
    if not m:
        raise SystemExit('%s not found in %s' % (macro, fn))
    return m.group(1)


# ----------------------------------------------------------------- (1)
# The rank floor and the Bonferroni scale, both read from the macro files
# that the manuscript itself uses, so the ratio cannot go stale.
RANKFLOOR = float(texval('survey_numbers.tex', 'RankFloor'))
BONF_TEX = texval('survey_numbers_round5.tex', 'BonferroniThresh')
mb = re.match(r'([\d.]+)\\times10\^\{(-?\d+)\}', BONF_TEX)
BONF = float(mb.group(1)) * 10.0 ** int(mb.group(2))
ratio = (1.0 / RANKFLOOR) / BONF
M('BonfRankRatio', '%d' % round(ratio))
M('RankFloorVal', '%.2f\\times10^{-3}' % (1e3 / RANKFLOOR))

# ----------------------------------------------------------------- (2)
# The held-out validation set moved to v351_calc.py in v3.54, where it is
# recomputed at build time from the running epoch-extension campaign
# (heldout_v351.json).  Emitting it here as well would multiply-define every
# HO* macro, so this block is retired rather than duplicated.

# ----------------------------------------------------------------- (3)
ROWS = list(csv.DictReader(open(os.path.join(HERE,
                                             'per_target_results_v3.52.csv'))))
A = [r for r in ROWS if r['search_class'] == 'A']


def r_over_theta(r):
    g = float(r['smin_mJy']) / (5.0 * float(r['rms_mJy']))
    return math.sqrt(max(math.log(g), 0.0) / (4.0 * math.log(2.0)))


# The calibration configuration of Appendix app:inject: AU Mic, Band 6,
# 488.28125 kHz, the 49-trial drift grid.
CAL = [r for r in A if r['star_name'] == 'AU Mic' and r['band'] == '6'
       and abs(float(r['chanw_Hz']) - 488281.25) < 1.0]
assert len(CAL) == 1, 'calibration window not unique: %d' % len(CAL)
CAL = CAL[0]
CW, OS, ND = (float(CAL['chanw_Hz']), float(CAL['on_source_s']),
              float(CAL['n_drift_trials']))
M('CalBand', CAL['band'])
M('CalChanKHz', '%.0f' % (CW / 1e3))
M('CalOnSrcS', '%.0f' % OS)
M('CalNDrift', '%.0f' % ND)
M('CalNInt', CAL['n_int'])

OFFTOL = 0.2


def axes_out(r):
    n = 0
    if not 0.5 <= float(r['chanw_Hz']) / CW <= 2.0:
        n += 1
    if not 0.5 <= float(r['on_source_s']) / OS <= 2.0:
        n += 1
    if not 0.5 <= float(r['n_drift_trials']) / ND <= 2.0:
        n += 1
    if r_over_theta(r) >= OFFTOL:
        n += 1
    if r['band'] != CAL['band']:
        n += 1
    return n


hist = {k: sum(1 for r in A if axes_out(r) == k) for k in range(6)}
M('CfgNA', '%d' % len(A))
M('CfgAxesZero', '%d' % hist[0])
M('CfgAxesOne', '%d' % hist[1])
M('CfgAxesTwo', '%d' % hist[2])
M('CfgAxesThree', '%d' % sum(hist[k] for k in range(3, 6)))
M('CfgAxesZeroOne', '%d' % (hist[0] + hist[1]))
M('CfgAxesZeroOnePct', '%.0f' % (100.0 * (hist[0] + hist[1]) / len(A)))
M('CfgOffTol', '%.1f' % OFFTOL)


def inband(key, lo, hi, ref):
    return sum(1 for r in A if lo <= float(r[key]) / ref <= hi)


M('CfgChanIn', '%d' % inband('chanw_Hz', 0.5, 2.0, CW))
M('CfgOnSrcIn', '%d' % inband('on_source_s', 0.5, 2.0, OS))
M('CfgDriftIn', '%d' % inband('n_drift_trials', 0.5, 2.0, ND))
M('CfgOffIn', '%d' % sum(1 for r in A if r_over_theta(r) < OFFTOL))
M('CfgBandIn', '%d' % sum(1 for r in A if r['band'] == CAL['band']))
for nm, key, ref in (('Chan', 'chanw_Hz', CW), ('OnSrc', 'on_source_s', OS),
                     ('Drift', 'n_drift_trials', ND)):
    v = sorted(float(r[key]) / ref for r in A)
    M('Cfg%sLo' % nm, '%.2f' % v[0])
    M('Cfg%sHi' % nm, '%.1f' % v[-1])
ro = sorted(r_over_theta(r) for r in A)
M('CfgOffHi', '%.2f' % ro[-1])

# ----------------------------------------------------------------- (4)
EX = json.load(open(os.path.join(HERE, 'frozen_export_v3.31.json')))['rows']
EPS = [r for r in EX if r['star_name'] == 'eps Eri' and r['band'] == 6]
assert len(EPS) == 4, 'expected 4 withheld eps Eri windows, got %d' % len(EPS)
eirp = sorted(r['eirp'] for r in EPS)
pbf = sorted(r['smin'] * 1e3 / (5.0 * r['rms']) for r in EPS)


def sci(x):
    e = int(math.floor(math.log10(x)))
    return '%.1f\\times10^{%d}' % (x / 10.0 ** e, e)


M('EpsEriNWin', '%d' % len(EPS))
M('EpsEriEirpLo', sci(eirp[0]))
M('EpsEriEirpHi', sci(eirp[-1]))
M('EpsEriPbLo', '%.1f' % pbf[0])
M('EpsEriPbHi', '%.1f' % pbf[-1])
M('EpsEriDistPc', '%.2f' % EPS[0]['dist_pc'])
M('EpsEriNFine', '%d' % sum(1 for r in EPS if r['chanw'] < 1e6))

with open(os.path.join(HERE, 'survey_numbers_round18.tex'), 'w') as fh:
    fh.write('%% Generated by v350_calc.py -- do not edit by hand.\n')
    fh.write('\n'.join(OUT) + '\n')
print('survey_numbers_round18.tex: %d macros' % len(OUT))
for line in OUT:
    print('   ', line)
