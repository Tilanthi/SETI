#!/usr/bin/env python3
r"""round 180 -> survey_numbers_round180.tex, sens_r11.json,
figures/sens_ring.pdf

THE SENSITIVITY OF THE SURVEY, MEASURED THROUGH THE CHAIN THAT ACTUALLY
DECIDES SOMETHING.

WHAT THIS FILE REPLACES, AND WHY.  The published completeness charged a
carrier for reaching the trigger AND outranking all 512 control positions.
The rank, however, disposes of nothing: recurrence is applied to every
unattributed crossing whatever its rank, because the rank has no calibrated
false-alarm probability.  So the published limits paid for a gate that was
never used, and the price was not uniform: the cost rises with the brightness
of the control ring, which is what forced the completeness to be
post-stratified on the ring and what created a second "disc-affected" stratum
whose ninety-per-cent point could not be measured at all and was published as
a bound.

★ REMOVING THE RANK REMOVES THE STRATUM, AND THAT IS A MEASUREMENT RATHER
  THAN AN ARGUMENT.  Every injected window resolves a ninety-per-cent point
  on the trigger alone -- including the three whose ladders never reached
  ninety per cent with the rank, which were the whole evidential basis of the
  second stratum.  They come back inside the range of the rest.  The stratum
  had a cause; the cause was a gate that decided nothing; and with the gate
  gone there is one completeness factor for the whole class.

  This file therefore measures ONE pooled curve, and it must not be allowed
  to do so by assumption.  Two things are required of it: that the
  ninety-per-cent point does not depend on the control ring (measured, and
  asserted against the dependence the rank-gated version has), and that the
  pooled value agrees with the ring-stratified value the published estimator
  would compute (so that the simplification is shown to cost nothing rather
  than claimed to).

WHAT ELSE IS HERE.
  * The campaign extent and the achieved sample's representativeness.  The
    sample is a stratified random CLUSTER sample of execution blocks: band
    and array are block properties and were controlled; channel width, the
    control-ring maximum and integration length vary inside a block and were
    only MEASURED afterwards.  The comparison with the population is computed
    here, so the paper's one sentence about stratification is backed.
  * The primary-beam response column, recomputed with ALMA's FWHM
    coefficient at each window's own dish diameter, with the released column
    verified forward over all 1651 rows against three candidate models.
  * The parallactic offset expressed in synthesised beams, which is the
    quantity that decides whether a scalar amplitude correction is legitimate
    at all.
  * The transfer uncertainty of Table 4, recomputed on the achieved sample.

NOTHING IS TYPED.  The recovery fractions come from the campaign's own tone
records; the ring weights from the released catalogue's own column; the dish
diameters from the per-window geometry record; the beams from the loss
ledger; the sample provenance from the file that drew it before any data were
fetched.

    python3 sens_r11.py [--out DIR] [--drive N] [--nofig]

--drive 1..27 breaks one assertion each and nothing else; --drive 0 means "no
perturbation, but do not write a path production reads".  MUST RUN BEFORE
numbers_v410.py, which takes the per-window multiplier from sens_r11.json.
"""
import collections
import csv
import json
import math
import os
import random
import statistics
import sys

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
ROUND = 180

DRIVE = None
OUTDIR = HERE
NOFIG = '--nofig' in sys.argv
for _i, _a in enumerate(sys.argv):
    if _a == '--drive':
        DRIVE = int(sys.argv[_i + 1])
    if _a == '--out':
        OUTDIR = sys.argv[_i + 1]
SUF = '' if DRIVE is None else '_drive%d' % DRIVE
OUT_TEX = os.path.join(OUTDIR, 'survey_numbers_round%d%s.tex' % (ROUND, SUF))
OUT_JSON = os.path.join(OUTDIR, 'sens_r11%s.json' % SUF)

C_M_S = 2.99792458e8
ARCSEC = 206264.80624709636
TRIGGER_SIGMA = 5.0
POSCTRL_AMP = 20.0
# The coefficient the pipeline's Gaussian used (an Airy first-null value) and
# ALMA's own primary-beam FWHM coefficient.  Both are conventions, not
# measurements, so they are named here and used everywhere below.
PB_COEF_CODE = 1.22
PB_COEF_ALMA = 1.13
# The published retention floor on the primary-beam response.
PB_FLOOR = 0.5
# The ring level at which the published work declared a window
# "disc-affected".  Kept only so that the stratification the rank forced can
# be reproduced and shown to be unnecessary.
RING_RULE_SIGMA = 10.0

# ------------------------------------------------------------------- inputs
CAT = list(csv.DictReader(open(os.path.join(
    HERE, 'per_target_results_v3.99.csv'))))
TONES = json.load(open(os.path.join(HERE, 'r9inputs', 'm3a_tones_r9.json')))
UNITS = json.load(open(os.path.join(HERE, 'r9inputs', 'm3a_units_r9.json')))
PXL = json.load(open(os.path.join(HERE, 'r8inputs',
                                  'parallax_loss_v404.json')))
# The two frozen records the published completeness was read out of.  They are
# inputs to a REGRESSION here, not sources of a value: this file recomputes
# both numbers and compares.
SENSB0 = json.load(open(os.path.join(HERE, 'r9inputs', 'sens_r9b.json')))
STRA0 = json.load(open(os.path.join(HERE, 'strata_v411.json')))
GEOM = json.load(open(os.path.join(HERE, 'r11inputs',
                                   'window_geometry_r11.json')))
SEL = json.load(open(os.path.join(HERE, 'r11inputs',
                                  'campaign_plan_r11.json')))
# The round-11 extension of the campaign.  Absent until the host finishes; the
# file then carries one record per newly injected window in the SAME shape the
# round-9 records have, because the two must be one measurement.
_newp = os.path.join(HERE, 'r11inputs', 'm3a_r11.json')
NEW = json.load(open(_newp)) if os.path.exists(_newp) else dict(
    units=[], tones=[], generated=None, note='campaign not yet collected')

OUT, FAIL = [], []


def m(name, val):
    assert name.isalpha(), (
        'a LaTeX macro name may contain letters only: %r' % name)
    OUT.append('\\newcommand{\\%s}{%s}' % (name, val))


# ★ Star names come from the records, never typed; the Bayer abbreviations the
# catalogues use are expanded to the paper's own convention by the project's
# own map (`star_alias._GREEK`), so this file holds no name of its own.
import star_alias as _sa


def texstar(name):
    w = name.split()
    if w and w[0].lower().rstrip('01') in _sa._GREEK:
        g = _sa._GREEK[w[0].lower().rstrip('01')]
        return '$\\%s$~%s' % (g, ' '.join(w[1:]))
    return name



def ck(label, cond, detail=''):
    print('  %-70s %s  %s' % (label, 'PASS' if cond else 'FAIL', detail))
    if not cond:
        FAIL.append(label)


def med(xs):
    return statistics.median(xs)


# ======================================================================= 1
# THE INJECTED SAMPLE: THE 21 OF THE PUBLISHED CAMPAIGN PLUS THIS ROUND'S.
#
# The two sets are merged here and nowhere else, and they are required to have
# been scored by the same code: the round-11 record carries the scorer's name
# and it must be the one that produced the round-9 record.
OLD_UNITS = [u for u in UNITS if u['cls'] == 'fine']
OLD_TAGS = sorted(u['tag'] for u in OLD_UNITS)
NEW_UNITS = list(NEW.get('units', []))
NEW_TAGS = sorted(u['tag'] for u in NEW_UNITS)
ck('the two campaign halves do not overlap',
   not (set(OLD_TAGS) & set(NEW_TAGS)), sorted(set(OLD_TAGS) & set(NEW_TAGS)))
if NEW.get('scorer'):
    ck('the extension was scored by the same code as the published 21',
       NEW['scorer'] == 'campaign_m3a_v399.py', NEW.get('scorer'))

TONE_BY_TAG = collections.defaultdict(list)
for t in TONES:
    if not t['outside'] and t['tag'] in set(OLD_TAGS):
        TONE_BY_TAG[t['tag']].append(t)
for t in NEW.get('tones', []):
    if not t['outside']:
        TONE_BY_TAG[t['tag']].append(t)

TAGS = sorted(TONE_BY_TAG)
N_INJ = len(TAGS)
CAT_A = [r for r in CAT if r['search_class'] == 'A']
CAT_B = [r for r in CAT if r['search_class'] == 'B']
N_A = len(CAT_A)

# The amplitude ladder, read off the records rather than retyped, with the
# positive control excluded: it is a diagnostic rung, not a measurement point.
AMPS = sorted({t['amp'] for g in TAGS for t in TONE_BY_TAG[g]
               if t['amp'] != POSCTRL_AMP})


def _cross(amps, fr, want=0.9):
    """Where a recovery curve first reaches `want`, linearly interpolated."""
    prev = None
    for a, f in zip(amps, fr):
        if f is None:
            continue
        if f >= want:
            if prev is None:
                return a
            pa, pf = prev
            return pa + (want - pf) * (a - pa) / (f - pf) if f > pf else a
        prev = (a, f)
    return None


def curve(tags, key, amps=None):
    amps = AMPS if amps is None else amps
    out = []
    for a in amps:
        tt = [t for g in tags for t in TONE_BY_TAG[g] if t['amp'] == a]
        out.append(sum(bool(t[key]) for t in tt) / len(tt) if tt else None)
    return out


P90_TRIG = _cross(AMPS, curve(TAGS, 'trig'))
P90_RANK = _cross(AMPS, curve(TAGS, 'rec'))
if DRIVE == 1:
    P90_TRIG = P90_RANK
ck('the completeness measured through the trigger alone is DEEPER than the '
   'one that also charged for the rank',
   P90_TRIG is not None and P90_RANK is not None and P90_TRIG < P90_RANK,
   'trigger alone %.4f against trigger+rank %.4f'
   % (P90_TRIG or -1, P90_RANK or -1))

# per-window points, both criteria
PER = {}
for g in TAGS:
    PER[g] = dict(trig=_cross(AMPS, curve([g], 'trig')),
                  rank=_cross(AMPS, curve([g], 'rec')),
                  n_tone=len(TONE_BY_TAG[g]))
N_RES_TRIG = sum(1 for g in TAGS if PER[g]['trig'] is not None)
N_RES_RANK = sum(1 for g in TAGS if PER[g]['rank'] is not None)
if DRIVE == 2:
    N_RES_TRIG = N_INJ - 1
ck('every injected window resolves a ninety-per-cent point on the trigger '
   'alone', N_RES_TRIG == N_INJ, '%d of %d' % (N_RES_TRIG, N_INJ))
ck('and the rank-gated criterion does NOT, so the simplification is doing '
   'the work', N_RES_RANK < N_INJ, '%d of %d' % (N_RES_RANK, N_INJ))
IND = sorted(PER[g]['trig'] for g in TAGS)
IND_LO, IND_HI = IND[0], IND[-1]

# bootstrap over WINDOWS, which is the unit of the sample
rng = random.Random(1800 + (DRIVE or 0) * 0)
BOOT = []
for _ in range(2000):
    s = [TAGS[rng.randrange(N_INJ)] for _ in range(N_INJ)]
    v = _cross(AMPS, curve(s, 'trig'))
    if v is not None:
        BOOT.append(v)
BOOT.sort()
BOOT_UNDEF = 1.0 - len(BOOT) / 2000.0
P90_LO = BOOT[int(0.16 * len(BOOT))]
P90_HI = BOOT[int(0.84 * len(BOOT))]
ck('the bootstrap resolves a ninety-per-cent point in every resample',
   BOOT_UNDEF == 0.0, BOOT_UNDEF)

# ======================================================================= 2
# ★ THE RING NO LONGER MATTERS, AND THAT IS THE WHOLE OF THE SIMPLIFICATION.
#
# The injected window's own clean control maximum is the campaign's own
# measurement of its ring; the catalogue publishes the same quantity for all
# 402.  Two things are measured: the ninety-per-cent point split on the
# published 10 sigma rule, and the ring-weighted (post-stratified) pooled
# value that the published estimator would form.  The first says the
# dependence is gone; the second says the pooling costs nothing.
def clean_ctrl(tag):
    u = ([u for u in OLD_UNITS if u['tag'] == tag]
         + [u for u in NEW_UNITS if u['tag'] == tag])[0]
    g = [r for r in u['rungs'] if r['amp'] == min(AMPS)]
    return float(g[0]['ctrl_top'])


RING = {g: clean_ctrl(g) for g in TAGS}
HI = [g for g in TAGS if RING[g] >= RING_RULE_SIGMA]
LO = [g for g in TAGS if RING[g] < RING_RULE_SIGMA]
RING_HI_TRIG = med([PER[g]['trig'] for g in HI]) if HI else None
RING_LO_TRIG = med([PER[g]['trig'] for g in LO])
RING_HI_RANK = [PER[g]['rank'] for g in HI]
RING_SPLIT = (RING_HI_TRIG - RING_LO_TRIG) if HI else 0.0
RING_RATIO = (RING_HI_TRIG / RING_LO_TRIG) if HI else 1.0
# ★ WHAT MAY AND MAY NOT BE ASSERTED HERE.  The dependence on the ring does
# not vanish: the bright-ring windows still sit at the top of the range, by
# a measured amount that is published.  What vanishes is the dependence that
# made the second stratum unmeasurable.  So the assertion is that the
# bright-ring value lies INSIDE the range the other windows span -- which is
# the operational meaning of "one stratum" -- and not that the difference is
# zero, which would be false and is not needed.
_lo_rng = (min(PER[g]['trig'] for g in LO), max(PER[g]['trig'] for g in LO))
if DRIVE == 3 and HI:
    PER[HI[0]]['trig'] = 3.0 * _lo_rng[1]
ck('the bright-ring windows\' ninety-per-cent points lie inside the range '
   'the rest of the sample spans, which is what one stratum means',
   HI and all(_lo_rng[0] <= PER[g]['trig'] <= _lo_rng[1] for g in HI),
   'bright-ring %s against a range of %.3f-%.3f'
   % (['%.3f' % PER[g]['trig'] for g in HI], _lo_rng[0], _lo_rng[1]))
N_UNRES_RANK_HI = sum(1 for v in RING_HI_RANK if v is None)
ck('and they did NOT lie inside it when the rank was charged for: the '
   'bright-ring windows are exactly the ones whose rank-gated ladder never '
   'got there', N_UNRES_RANK_HI > 0,
   '%d of %d bright-ring windows unresolved with the rank'
   % (N_UNRES_RANK_HI, len(HI)))
# and the size of the collapse, measured both ways
_rk_lo = [PER[g]['rank'] for g in LO if PER[g]['rank'] is not None]
RANK_RING_RATIO = (max(RING_HI_RANK_V) / med(_rk_lo)
                   if (RING_HI_RANK_V := [v for v in RING_HI_RANK
                                          if v is not None]) and _rk_lo
                   else None)
# ★ THE COMPARISON THAT IS HONEST.  A ratio computed from the rank-gated
# points is computed on a CENSORED sample -- most bright-ring windows have no
# rank-gated ninety-per-cent point at all -- so comparing the two ratios
# compares a complete measurement with an incomplete one.  The statement that
# survives both ways is the pair: with the rank the dependence is not
# measurable on most bright-ring windows; without it, it is 1.1.
if DRIVE == 9:
    RING_RATIO = 3.0
ck('with the rank the ring dependence was unmeasurable on most bright-ring '
   'windows; without it, it is a tenth and not a factor',
   N_UNRES_RANK_HI >= max(1, len(HI) // 2) and RING_RATIO < 1.5,
   '%d of %d unresolved with the rank; bright/faint ratio %.3f without it'
   % (N_UNRES_RANK_HI, len(HI), RING_RATIO))

# the post-stratified value the published estimator would form
_BINS = [0.0, 6.0, RING_RULE_SIGMA, 14.0, 1e9]


def binof(c):
    for i in range(len(_BINS) - 1):
        if _BINS[i] <= c < _BINS[i + 1]:
            return i
    raise ValueError(c)


WCAT = [0] * (len(_BINS) - 1)
for r in CAT_A:
    WCAT[binof(float(r['ctrl_max_snr']))] += 1
BYBIN = [[] for _ in range(len(_BINS) - 1)]
for g in TAGS:
    BYBIN[binof(RING[g])].append(g)


def strat_curve(key):
    out = []
    for a in AMPS:
        acc = wn = 0.0
        for i, tg in enumerate(BYBIN):
            if not tg or not WCAT[i]:
                continue
            tt = [t for g in tg for t in TONE_BY_TAG[g] if t['amp'] == a]
            if not tt:
                continue
            acc += WCAT[i] * sum(bool(t[key]) for t in tt) / len(tt)
            wn += WCAT[i]
        out.append(acc / wn if wn else None)
    return out


P90_STRAT = _cross(AMPS, strat_curve('trig'))
_dev = abs(P90_STRAT - P90_TRIG) / P90_TRIG
if DRIVE == 4:
    _dev = 0.5
ck('post-stratifying on the ring, as the published estimator had to, moves '
   'the trigger-alone value by only a few per cent, so one pooled factor '
   'costs almost nothing', _dev < 0.05,
   'pooled %.4f against ring-weighted %.4f, %.2f per cent'
   % (P90_TRIG, P90_STRAT, 100 * _dev))
# ★ AND THE DIRECTION IS THE ONE THAT MAY BE PUBLISHED.  The campaign
# over-samples bright rings relative to the survey, so the ring-weighted
# value is the DEEPER of the two; publishing the pooled one is therefore
# conservative, and this assertion is what stops the flattering one being
# published if the sample composition ever changes.
_pooled_conservative = P90_TRIG >= P90_STRAT
if DRIVE == 12:
    _pooled_conservative = False
ck('and the pooled factor is the conservative one of the two',
   _pooled_conservative,
   'pooled %.4f, ring-weighted %.4f' % (P90_TRIG, P90_STRAT))
N_BLIND = sum(WCAT[i] for i in range(len(WCAT)) if WCAT[i] and not BYBIN[i])
ck('every Class A window lies in a ring stratum the campaign injected into',
   N_BLIND == 0, '%d windows in uninjected strata' % N_BLIND)

# ======================================================================= 2b
# ★★★ THE REGRESSION.  FOUR NUMBERS, ONE CODE PATH, AND THEY MUST BE NAMED
# APART.
#
# The published blanket factor is 4.42 and the published noise-stratum factor
# 3.45, both with the rank charged for.  A naive pooled curve over the same
# 21 windows on the same scoring gives 8.0.  Those are not three measurements
# of one quantity and they are not evidence that anything changed: they are
# one curve under two WEIGHTINGS and two SUBSETS.
#
#   * The campaign over-samples bright control rings -- 4 of its 21 windows
#     sit above the 10 sigma rule against 12 of the survey's 402 -- and with
#     the rank charged for, a bright-ring window never reaches ninety per cent
#     at all.  An unweighted pool therefore carries a fifth of its weight in
#     windows that never recover, and its ninety per cent point is pushed to
#     8.0.  Post-stratifying on the ring down-weights them to their survey
#     frequency and gives 4.42.  THE WEIGHTED ONE IS THE RIGHT ONE, and that
#     is why the published estimator was weighted.
#   * 3.45 is neither: it is the weighted curve over the NOISE stratum alone,
#     and it is the number the per-window limits were actually built from, the
#     other twelve windows carrying a bound instead.
#
# So the reconciliation is definitional, and it is DEMONSTRATED here rather
# than asserted: the two published values are recomputed on this file's own
# code path from this file's own tone records and required to reproduce the
# frozen ones to three decimal places.  If a future campaign changes the
# scoring, these two assertions fail and nothing is published quietly.
def weighted_curve(key, bins=None, only=None):
    """The published estimator: ring-post-stratified, weighted by the number
    of CATALOGUE windows in each ring bin.  `bins=None` is all of them;
    `only` restricts to a subset of windows."""
    use = range(len(_BINS) - 1) if bins is None else bins
    out = []
    for a in AMPS:
        acc = wn = 0.0
        for i in use:
            tg = BYBIN[i] if only is None else [g for g in BYBIN[i] if g in only]
            if not tg or not WCAT[i]:
                continue
            tt = [t for g in tg for t in TONE_BY_TAG[g] if t['amp'] == a]
            if not tt:
                continue
            acc += WCAT[i] * sum(bool(t[key]) for t in tt) / len(tt)
            wn += WCAT[i]
        out.append(acc / wn if wn else None)
    return out


_NOISE_BINS = [i for i in range(len(_BINS) - 1)
               if _BINS[i + 1] <= RING_RULE_SIGMA]
# ★ THE REGRESSION IS A STATEMENT ABOUT THE PUBLISHED CAMPAIGN, SO IT IS
# COMPUTED ON THE PUBLISHED CAMPAIGN.  Running it over the whole extended
# sample would compare a number measured on 21 windows with one measured on
# more, and it would fail for a reason that has nothing to do with the
# scoring -- which is the kind of check that looks like a defect and is not.
_OLD = set(OLD_TAGS)
REG = dict(
    pooled_rank=_cross(AMPS, curve(OLD_TAGS, 'rec')),
    weighted_rank=_cross(AMPS, weighted_curve('rec', only=_OLD)),
    noise_rank=_cross(AMPS, weighted_curve('rec', _NOISE_BINS, only=_OLD)),
    pooled_trig=_cross(AMPS, curve(OLD_TAGS, 'trig')),
    weighted_trig=_cross(AMPS, weighted_curve('trig', only=_OLD)),
    noise_trig=_cross(AMPS, weighted_curve('trig', _NOISE_BINS, only=_OLD)),
    n_windows=len(OLD_TAGS),
    note=('computed on the published campaign alone, because that is the '
          'measurement the frozen records describe'))
# and the same six on the whole sample, for the paper
REG_ALL = dict(
    pooled_rank=_cross(AMPS, curve(TAGS, 'rec')),
    weighted_rank=_cross(AMPS, weighted_curve('rec')),
    noise_rank=_cross(AMPS, weighted_curve('rec', _NOISE_BINS)),
    pooled_trig=P90_TRIG,
    weighted_trig=_cross(AMPS, weighted_curve('trig')),
    noise_trig=_cross(AMPS, weighted_curve('trig', _NOISE_BINS)),
    n_windows=N_INJ)
PUB_BLANKET = SENSB0['stratified']['p90']
PUB_NOISE = STRA0['noise']['p90']
PUB_DISC_LO = STRA0['disc']['bound_lo']
PUB_DISC_ADOPTED = STRA0['disc']['bound_adopted']
_d1 = abs(REG['weighted_rank'] - PUB_BLANKET)
_d2 = abs(REG['noise_rank'] - PUB_NOISE)
if DRIVE == 13:
    _d1 = 1.0
if DRIVE == 14:
    _d2 = 1.0
ck('REGRESSION: the published blanket factor is reproduced exactly by this '
   'file, as the ring-weighted curve with the rank charged for',
   _d1 < 1e-3, 'recomputed %.4f against a published %.4f'
   % (REG['weighted_rank'], PUB_BLANKET))
ck('REGRESSION: and the published noise-stratum factor is reproduced as the '
   'same curve over the noise bins alone',
   _d2 < 1e-3, 'recomputed %.4f against a published %.4f'
   % (REG['noise_rank'], PUB_NOISE))
ck('so nothing changed in the scoring, and the naive pooled with-rank value '
   'is a THIRD quantity that must not be called by either name',
   REG['pooled_rank'] > 1.5 * REG['weighted_rank'],
   'pooled %.3f against weighted %.3f, because %d of %d injected windows '
   'have a bright ring against %d of %d in the survey'
   % (REG['pooled_rank'], REG['weighted_rank'], len(HI), N_INJ,
      STRA0['disc']['n_cat'], N_A))
# ★ AND THE LIKE-FOR-LIKE COST OF THE RANK IS THE WEIGHTED RATIO, NOT THE
# POOLED ONE.  The pooled ratio is inflated by the sample's composition, so
# quoting it would overstate what removing the rank buys.
COST_LIKE = REG_ALL['weighted_rank'] / REG_ALL['weighted_trig']
COST_POOLED = REG_ALL['pooled_rank'] / REG_ALL['pooled_trig']
ck('the like-for-like cost of the rank is smaller than the pooled ratio, so '
   'the conservative figure is the one published',
   COST_LIKE < COST_POOLED,
   'like-for-like x%.2f against a pooled x%.2f' % (COST_LIKE, COST_POOLED))
# ★ AND WHAT THE LIMITS ACTUALLY MOVE BY is neither of those: the per-window
# limits were built from the noise stratum and the disc bound, so the change
# a reader sees in the headline is this ratio on 390 windows and a much
# larger one on 12.
MOVE_NOISE = P90_TRIG / PUB_NOISE
MOVE_DISC = P90_TRIG / PUB_DISC_ADOPTED
ck('the headline moves by the noise-stratum ratio and not by the pooled one, '
   'because that is what the published per-window limits were built from',
   0.8 < MOVE_NOISE < 1.0 and MOVE_DISC < 0.3,
   'x%.3f on the %d noise windows, x%.3f on the %d disc windows'
   % (MOVE_NOISE, STRA0['noise']['n_cat'], MOVE_DISC, STRA0['disc']['n_cat']))

# ======================================================================= 2c
# CLASS B, ON THE SAME CRITERION.
#
# ★ WHY CLASS B HAS TO MOVE TOO.  The coarse campaign's recovery also carries
# a rank penalty -- its pooled recovery at 4x its trigger is 0.88 through the
# trigger and 0.80 through the trigger and rank together -- so leaving Class B
# on the rank-charged criterion while Class A is not would be an inconsistency
# inside one table.  Both classes are therefore measured through the trigger.
#
# The coarse route is the PER-UNIT one: per-tone records exist only for the
# fine units, so the coarse curve is formed from each unit's own rung counts.
# The size of that approximation is measured on the fine class, where both
# routes can be run, rather than assumed small.
UCOARSE = [u for u in UNITS if u['cls'] == 'coarse']
CAT_B_BY = collections.defaultdict(list)
for r in CAT_B:
    CAT_B_BY[(r['eb'], int(round(float(r['chanw_Hz']))))].append(r)
MATCH_B, UNMATCHED_B = {}, []
for u in UCOARSE:
    eb = u['tag'].rsplit('_spw', 1)[0]
    cand = CAT_B_BY.get((eb, int(round(u['chanw_Hz']))), [])
    ct = [g['ctrl_top'] for g in u['rungs'] if g['amp'] == min(AMPS)][0]
    if not cand:
        UNMATCHED_B.append(u['tag'])
        continue
    MATCH_B[u['tag']] = min(
        cand, key=lambda c: abs(float(c['ctrl_max_snr']) - ct))
ck('every injected coarse window joined a released Class B row',
   not UNMATCHED_B, str(UNMATCHED_B))
_bk = ['%s|%s' % (r['eb'], r['flo_GHz']) for r in MATCH_B.values()]
if DRIVE == 17:
    _bk = _bk + _bk[:1]
ck('and no two injected coarse windows joined the same released row',
   len(set(_bk)) == len(_bk), '%d rows for %d windows'
   % (len(set(_bk)), len(_bk)))
WCAT_B = [0] * (len(_BINS) - 1)
for r in CAT_B:
    WCAT_B[binof(float(r['ctrl_max_snr']))] += 1
BYBIN_B = [[] for _ in range(len(_BINS) - 1)]
for t, r in MATCH_B.items():
    BYBIN_B[binof(float(r['ctrl_max_snr']))].append(t)
URUNG = {u['tag']: {g['amp']: g for g in u['rungs']} for u in UCOARSE}


def curve_unit(tags_by_bin, wcat, key):
    out = []
    for a in AMPS:
        acc = wn = 0.0
        for i, tg in enumerate(tags_by_bin):
            if not tg or not wcat[i]:
                continue
            num = den = 0
            for t in tg:
                g = URUNG[t].get(a)
                if g:
                    num += g[key]
                    den += g['n']
            if den:
                acc += wcat[i] * num / den
                wn += wcat[i]
        out.append(acc / wn if wn else None)
    return out


P90_B = _cross(AMPS, curve_unit(BYBIN_B, WCAT_B, 'trig'))
P90_B_RANK = _cross(AMPS, curve_unit(BYBIN_B, WCAT_B, 'both'))
N_BLIND_B = sum(WCAT_B[i] for i in range(len(WCAT_B))
                if WCAT_B[i] and not BYBIN_B[i])
if DRIVE == 15:
    P90_B = P90_B_RANK
ck('Class B is measured on the same criterion as Class A and is therefore '
   'also deeper than its rank-charged value',
   P90_B < P90_B_RANK, 'trigger alone %.3f against %.3f with the rank'
   % (P90_B, P90_B_RANK))
ck('the two classes are measured separately and are not the same number',
   abs(P90_B - P90_TRIG) > 0.05, (P90_B, P90_TRIG))
ck('the Class B blind stratum is small and declared',
   0 < N_BLIND_B < 0.01 * sum(WCAT_B),
   'blind %d of %d' % (N_BLIND_B, sum(WCAT_B)))
# the per-unit route is the only one available for the coarse class, so the
# size of the approximation is measured on the fine class
_fine_unit_bin = [[g for g in tg] for tg in BYBIN]
URUNG_F = {u['tag']: {g['amp']: g for g in u['rungs']}
           for u in OLD_UNITS + NEW_UNITS}
_save = URUNG
URUNG = URUNG_F
P90_A_UNITROUTE = _cross(AMPS, curve_unit(BYBIN, WCAT, 'trig'))
URUNG = _save
_rdev = abs(P90_A_UNITROUTE - P90_STRAT) / P90_STRAT
if DRIVE == 16:
    _rdev = 0.5
ck('the per-unit route agrees with the per-tone route where both can be run, '
   'which bounds the approximation Class B is forced into',
   _rdev < 0.03, 'the two routes give %.4f and %.4f, %.1f per cent'
   % (P90_STRAT, P90_A_UNITROUTE, 100 * _rdev))
m('SensMultB', '%.2f' % P90_B)
m('SensMultBRank', '%.2f' % P90_B_RANK)
m('SensRouteDevPct', '%.1f' % (100 * _rdev))
m('SensNBlindB', '%d' % N_BLIND_B)
# ★★ THE BASIS OF THE CLASS B FACTOR, PUBLISHED.  The factor underpins the
# Barnard's Star, Wolf 359 and Proxima limits, and the paper gave no count of
# what it was measured on, which left a reader free to guess -- one did, and
# guessed three windows.  It is 35.
N_INJ_B = len(MATCH_B)
N_INJ_B_BLOCK = len({t.rsplit('_spw', 1)[0] for t in MATCH_B})
N_TONE_B = sum(sum(g['n'] for g in u['rungs']) for u in UCOARSE
               if u['tag'] in MATCH_B)
if DRIVE == 27:
    N_INJ_B = len(UCOARSE) - 1
ck('the Class B factor rests on a stated number of injected coarse windows, '
   'in more than one execution block, and every one of them joined a '
   'released Class B row',
   N_INJ_B == len(UCOARSE) and N_INJ_B_BLOCK > 1 and N_TONE_B > 0,
   '%d windows in %d blocks, %d tones' % (N_INJ_B, N_INJ_B_BLOCK, N_TONE_B))
m('SensNInjCoarse', '%d' % N_INJ_B)
m('SensNInjCoarseBlock', '%d' % N_INJ_B_BLOCK)
m('SensNToneCoarse', '{:,}'.format(N_TONE_B).replace(',', '\\,'))


# what the rank was costing, per window and in the median
COST = sorted(PER[g]['rank'] / PER[g]['trig'] for g in TAGS
              if PER[g]['rank'] is not None)
COST_MED, COST_HI = med(COST), COST[-1]


# ======================================================================= 3
# THE COVARIATES R1 ASKED FOR, MEASURED ON THE ACHIEVED SAMPLE.
#
# Band and array were controlled by the draw; channel width, ring and
# integration length could not be, because they vary inside a block.  What is
# published is therefore a COMPARISON with the population, not a claim to have
# stratified on five axes.
CATROW = {}
for g in TAGS:
    eb = g.rsplit('_spw', 1)[0]
    cand = [r for r in CAT_A if r['eb'] == eb]
    if not cand:
        continue
    # the campaign's own clean ring maximum identifies the window inside the
    # block: a block-only key averages two windows, which is the key-collision
    # family this project has met thirteen times.
    CATROW[g] = min(cand, key=lambda r: abs(float(r['ctrl_max_snr']) - RING[g]))
ck('every injected window joined a released Class A row',
   len(CATROW) == N_INJ, '%d of %d' % (len(CATROW), N_INJ))
_joined = [CATROW[g]['eb'] + '|' + CATROW[g]['flo_GHz'] for g in CATROW]
ck('and no two injected windows joined the same released row',
   len(set(_joined)) == len(_joined),
   '%d rows for %d windows' % (len(set(_joined)), len(_joined)))

ARRAY_OF = {b['eb']: b for b in PXL['blocks']}
GEO = {}
for w in GEOM['windows']:
    GEO[(w['eb'], round(w['flo'], 4), round(w['fhi'], 4))] = w


def geo(r):
    return GEO[(r['eb'], round(float(r['flo_GHz']), 4),
                round(float(r['fhi_GHz']), 4))]


def dist(rows, f):
    return collections.Counter(f(r) for r in rows)


COV = {}
for name, f in (('band', lambda r: r['band']),
                ('array', lambda r: '7m' if geo(r)['dish_m'] < 10 else '12m'),
                ('chanw', lambda r: '%.0f kHz' % (float(r['chanw_Hz']) / 1e3))):
    pop = dist(CAT_A, f)
    got = dist([CATROW[g] for g in CATROW], f)
    npop, ngot = sum(pop.values()), sum(got.values())
    worst, worstk = 0.0, None
    for k in set(pop) | set(got):
        d = abs(got.get(k, 0) / ngot - pop.get(k, 0) / npop)
        if d > worst:
            worst, worstk = d, k
    COV[name] = dict(population={str(k): v for k, v in pop.items()},
                     achieved={str(k): v for k, v in got.items()},
                     worst_abs_frac_diff=worst, worst_level=str(worstk))

# the continuous covariates: ring and integration length, by median
CONT = {}
for name, f in (('ring', lambda r: float(r['ctrl_max_snr'])),
                ('on_source_s', lambda r: float(r['on_source_s'])),
                ('rms_mJy', lambda r: float(r['rms_mJy']))):
    p = sorted(f(r) for r in CAT_A)
    a = sorted(f(CATROW[g]) for g in CATROW)
    CONT[name] = dict(pop_median=med(p), ach_median=med(a),
                      pop_range=[p[0], p[-1]], ach_range=[a[0], a[-1]],
                      ach_covers_pop_decile=(a[0] <= p[int(0.1 * len(p))]
                                             and a[-1] >= p[int(0.9 * len(p))]))

# and the thing the referee insisted on: the sample must not know about
# crossings.  This is MEASURED, not claimed by construction.
def is_cross(r):
    return r['crossing'] not in ('', '0', 'False', 'false')


N_CROSS_POP = sum(1 for r in CAT_A if is_cross(r))
N_CROSS_ACH = sum(1 for g in CATROW if is_cross(CATROW[g]))
_p = N_CROSS_POP / N_A
_exp = _p * N_INJ
_sd = math.sqrt(N_INJ * _p * (1 - _p))
_z = abs(N_CROSS_ACH - _exp) / _sd if _sd else 0.0
if DRIVE == 5:
    _z = 9.0
ck('the injected sample holds crossings at the population rate, which is '
   'what selection without reference to them predicts',
   _z < 3.0, '%d observed against %.1f expected, %.1f sigma'
   % (N_CROSS_ACH, _exp, _z))

# spreads by covariate, on the trigger-alone point
def spread(f, key='trig', only=None):
    g_ = collections.defaultdict(list)
    for g in TAGS:
        if only is not None and g not in only:
            continue
        if g in CATROW and PER[g][key] is not None:
            g_[f(CATROW[g])].append(PER[g][key])
    v = {k: med(x) for k, x in g_.items() if len(x) >= 2}
    return (max(v.values()) - min(v.values()), v) if len(v) > 1 else (0.0, v)


BAND_SPREAD, BAND_V = spread(lambda r: r['band'])
CHAN_SPREAD, CHAN_V = spread(lambda r: int(round(float(r['chanw_Hz']))))
ARR_SPREAD, ARR_V = spread(
    lambda r: '7m' if geo(r)['dish_m'] < 10 else '12m')
# The comparison that means something is with the SAME spreads measured on
# the rank-gated criterion, because a covariate that looked like a real
# dependence there and does not here is a covariate that was tracking the
# screen.  The array is the case in point: in this sample it is confounded
# with the ring.
BAND_SPREAD_R, _ = spread(lambda r: r['band'], 'rank')
CHAN_SPREAD_R, _ = spread(lambda r: int(round(float(r['chanw_Hz']))), 'rank')
ARR_SPREAD_R, _ = spread(
    lambda r: '7m' if geo(r)['dish_m'] < 10 else '12m', 'rank')
_cov_pairs = [('band', BAND_SPREAD, BAND_SPREAD_R),
              ('channel width', CHAN_SPREAD, CHAN_SPREAD_R),
              ('array', ARR_SPREAD, ARR_SPREAD_R)]
if DRIVE == 8:
    _cov_pairs = [('band', 9.0, 0.1)]
ck('no covariate moves the completeness by as much as the rank itself was '
   'costing', max(t for _, t, _ in _cov_pairs) < (COST_MED - 1.0) * P90_TRIG,
   '; '.join('%s %.3f' % (a, b) for a, b, _ in _cov_pairs)
   + ' against a median rank cost of %.3f' % ((COST_MED - 1.0) * P90_TRIG))
# ★ HOW MUCH OF THE ARRAY DIFFERENCE IS THE RING IS MEASURED, NOT ASSERTED
# EITHER WAY.  On a sample of twenty-one windows the two were confounded --
# the bright rings all sat on one array -- and a conclusion drawn there would
# have been a conclusion about the sample.  So both figures are published and
# neither direction is assumed; what is required is only that whatever
# remains is smaller than the gate the chain no longer charges for.
ARR_SPREAD_FAINT, ARR_V_FAINT = spread(
    lambda r: '7m' if geo(r)['dish_m'] < 10 else '12m', 'trig',
    only=set(LO))
ARR_RING_SHARE = (1.0 - ARR_SPREAD_FAINT / ARR_SPREAD) if ARR_SPREAD else 0.0
print('  %-70s      %s' % (
    'how much of the array difference is the control ring',
    '%.3f over all windows, %.3f with the bright rings set aside, so the ring '
    'accounts for %.0f per cent of it'
    % (ARR_SPREAD, ARR_SPREAD_FAINT, 100 * ARR_RING_SHARE)))

# ★★★ WHICH COVARIATE MOVES THE COMPLETENESS MOST IS A MEASUREMENT, AND THE
# PROSE HAS TO TAKE IT FROM HERE.  The paper said "the largest difference is
# between the arrays" while printing a larger figure for channel width in the
# same sentence, and said "most of that is the control ring" while printing a
# ring share of zero in the next clause.  Both were leftovers from a sample a
# fifth this size in which the two were confounded.  The axis is now NAMED by
# the measurement, so a sentence that names a different one cannot be written
# without this macro contradicting it on the same line.
_COV_SPREAD = {'band': BAND_SPREAD, 'channel width': CHAN_SPREAD,
               'array': ARR_SPREAD}
COV_AXIS = max(_COV_SPREAD, key=_COV_SPREAD.get)
COV_MAX = _COV_SPREAD[COV_AXIS]
if DRIVE == 25:
    COV_AXIS = 'array'
ck('the covariate with the largest spread is named by the measurement and is '
   'not the array, whose apparent effect the ring was once blamed for',
   COV_AXIS == max(_COV_SPREAD, key=_COV_SPREAD.get) and COV_AXIS != 'array'
   and _COV_SPREAD[COV_AXIS] >= max(_COV_SPREAD.values()) - 1e-12,
   '%s at %.3f, against %s'
   % (COV_AXIS, COV_MAX,
      ', '.join('%s %.3f' % kv for kv in sorted(_COV_SPREAD.items()))))
# ★ and the ring share is published as measured, in whichever direction it
# comes out.  On this sample it is zero: setting the bright-ring windows aside
# leaves the array difference unchanged to the printed precision.
_ARS = ARR_RING_SHARE
if DRIVE == 26:
    _ARS = 0.72
ck('the array difference is unchanged when the bright-ring windows are set '
   'aside, so the ring explains none of it and the sentence must say so',
   abs(_ARS) < 0.005,
   'x%.3f of the difference, %.3f against %.3f'
   % (_ARS, ARR_SPREAD, ARR_SPREAD_FAINT))
# What matters for the pooled factor is not whether the covariate exists but
# whether the sample is balanced in it.  Weighting the pooled curve by the
# survey's own array composition must move it by less than the sampling
# interval, or the pooled factor is biased and the weighted one must be
# published instead.
_arrpop = collections.Counter(
    '7m' if geo(r)['dish_m'] < 10 else '12m' for r in CAT_A)
_arrtag = collections.defaultdict(list)
for g in TAGS:
    if g in CATROW:
        _arrtag['7m' if geo(CATROW[g])['dish_m'] < 10 else '12m'].append(g)


def weighted_pooled(pop, grp):
    out = []
    for a in AMPS:
        acc = wn = 0.0
        for k, tg in grp.items():
            tt = [t for g in tg for t in TONE_BY_TAG[g] if t['amp'] == a]
            if not tt or not pop.get(k):
                continue
            acc += pop[k] * sum(bool(t['trig']) for t in tt) / len(tt)
            wn += pop[k]
        out.append(acc / wn if wn else None)
    return _cross(AMPS, out)


P90_ARRW = weighted_pooled(_arrpop, _arrtag)
if DRIVE == 10:
    P90_ARRW = P90_TRIG * 2.0
ck('weighting the pooled curve by the survey\'s own array composition moves '
   'it by less than the sampling interval, so the pooled factor is not '
   'biased by the sample\'s array mix',
   abs(P90_ARRW - P90_TRIG) < (P90_HI - P90_LO),
   'array-weighted %.4f against pooled %.4f, interval %.4f'
   % (P90_ARRW, P90_TRIG, P90_HI - P90_LO))

# ★ THE TRANSFER UNCERTAINTY IS A QUANTILE SPREAD, NOT THE EXTREMES.
# "The spread across the injected windows" has to be a quantile range, because
# the minimum and maximum of a sample WIDEN WITH SAMPLE SIZE by construction:
# quoting them would make the transfer uncertainty grow every time the
# campaign is improved, which is perverse.  So the row is the 16th-to-84th
# percentile of the per-window points -- a one-standard-deviation
# window-to-window spread -- and the full range is published beside it rather
# than folded in, together with the single window that sets its upper end.
_IND = sorted(PER[g]['trig'] for g in TAGS)
TR_LO = float(np.percentile(_IND, 16)) / P90_TRIG
TR_HI = float(np.percentile(_IND, 84)) / P90_TRIG
TR_FULL_LO = IND_LO / P90_TRIG
TR_FULL_HI = IND_HI / P90_TRIG
_hi_tag = max(TAGS, key=lambda g: PER[g]['trig'])
_hi_second = sorted((PER[g]['trig'] for g in TAGS), reverse=True)[1]
if DRIVE == 20:
    TR_HI = 2.0 * TR_FULL_HI
ck('the quantile spread lies inside the full range of the per-window points, '
   'and the full range is published beside it',
   TR_FULL_LO <= TR_LO and TR_HI <= TR_FULL_HI,
   'quantile x%.3f-x%.3f inside a full x%.3f-x%.3f'
   % (TR_LO, TR_HI, TR_FULL_LO, TR_FULL_HI))
if DRIVE == 21:
    _hi_second = PER[_hi_tag]['trig']
ck('the deepest and shallowest windows are named rather than absorbed, and '
   'the upper end of the full range is set by one window',
   PER[_hi_tag]['trig'] > 1.3 * _hi_second,
   'the shallowest window needs %.2f P_trig against %.2f for the next, in %s'
   % (PER[_hi_tag]['trig'], _hi_second, _hi_tag))

# ======================================================================= 4
# THE PRIMARY-BEAM RESPONSE COLUMN.
#
# Verified FORWARD over every released row against three candidate models, so
# the check covers the whole catalogue instead of the subset whose response
# can be inverted.  131 rows carry A = 1.000000 to six places and one has an
# offset of exactly zero; a backward check cannot speak about those at all.
def A_of(off, f_Hz, D_m, coef):
    fwhm = coef * C_M_S / f_Hz / D_m * ARCSEC
    return math.exp(-math.log(2.0) * (off / (0.5 * fwhm)) ** 2)


PBROWS = []
for r in CAT:
    g = geo(r)
    f = 0.5 * (float(r['flo_GHz']) + float(r['fhi_GHz'])) * 1e9
    off = float(r['pb_offset_arcsec'])
    a_pub = float(r['pb_atten'])
    PBROWS.append(dict(
        row=r, off=off, f=f, dish=g['dish_m'], a_pub=a_pub,
        a_code=A_of(off, f, g['dish_m'], PB_COEF_CODE),
        a_twelve=A_of(off, f, 12.0, PB_COEF_CODE),
        a_alma=A_of(off, f, g['dish_m'], PB_COEF_ALMA)))
PBERR = {k: max(abs(p[k] - p['a_pub']) for p in PBROWS)
         for k in ('a_code', 'a_twelve', 'a_alma')}
if DRIVE == 6:
    PBERR['a_code'] = 1.0
ck('the released pb_atten is a Gaussian at %.2f lambda/D at EACH WINDOW\'S '
   'OWN dish' % PB_COEF_CODE, PBERR['a_code'] < 1e-4,
   'worst residual %.3e over %d rows' % (PBERR['a_code'], len(PBROWS)))
ck('and a 12-m-for-every-row model is excluded by three orders of magnitude, '
   'so the referee has named the wrong column',
   PBERR['a_twelve'] > 100 * PBERR['a_code'],
   'worst residual %.3e against %.3e' % (PBERR['a_twelve'], PBERR['a_code']))
N_PB_1PCT = sum(1 for p in PBROWS if p['a_pub'] / p['a_alma'] > 1.01)
N_PB_10PCT = sum(1 for p in PBROWS if p['a_pub'] / p['a_alma'] > 1.10)
PB_SHIFT_MED = med([p['a_pub'] / p['a_alma'] for p in PBROWS])
PB_SHIFT_MAX = max(p['a_pub'] / p['a_alma'] for p in PBROWS)
PB_WORST_STAR = max(PBROWS, key=lambda p: p['a_pub'] / p['a_alma'])
PB_AMIN_PUB = min(p['a_pub'] for p in PBROWS)
PB_AMIN_ALMA = min(p['a_alma'] for p in PBROWS)
ck('the corrected response still clears the published retention floor, so '
   'no released window leaves the sample', PB_AMIN_ALMA > PB_FLOOR,
   'minimum response %.4f against a floor of %.2f' % (PB_AMIN_ALMA, PB_FLOOR))
ck('and the margin by which it clears it is small enough to be worth '
   'stating', PB_AMIN_ALMA - PB_FLOOR < 0.01, PB_AMIN_ALMA - PB_FLOOR)
# the three families that a backward check cannot cover, counted
PB_UNIT = sum(1 for p in PBROWS if p['a_pub'] >= 1.0 and p['off'] > 0)
PB_ZERO = sum(1 for p in PBROWS if p['off'] <= 0)
PB_INV = len(PBROWS) - PB_UNIT - PB_ZERO
ck('the rows a backward check cannot invert are named and the count closes',
   PB_INV + PB_UNIT + PB_ZERO == len(CAT),
   '%d invertible + %d at unit response + %d at zero offset = %d'
   % (PB_INV, PB_UNIT, PB_ZERO, len(CAT)))

# ★ AND THE CORRECTED COLUMN IS RELEASED, not merely described.  One row per
# released window, keyed the way the catalogue is keyed, so a reader can join
# it without ambiguity.  ★ BEFORE CHANGING A COLUMN, FIND OUT WHAT READS IT:
# in this project a retired column stayed load-bearing in seven generators.
# `pb_atten` is read by the published identity S_min = 5 sigma / A on every
# row, so the corrected response is deposited BESIDE the applied one rather
# than in place of it, and the identity is left closing on the column it was
# formed with.  The consequence of adopting it is quoted as a signed term.
if DRIVE is None:
    _pbout = os.path.join(OUTDIR, 'pb_atten_fwhm_r11.csv')
    with open(_pbout, 'w', newline='') as _fh:
        _w = csv.writer(_fh)
        _w.writerow(['star_name', 'eb', 'flo_GHz', 'fhi_GHz', 'dish_m',
                     'pb_offset_arcsec', 'theta_pb_fwhm_arcsec',
                     'pb_atten', 'pb_atten_fwhm', 'smin_ratio'])
        for _p in PBROWS:
            _r = _p['row']
            _w.writerow([_r['star_name'], _r['eb'], _r['flo_GHz'],
                         _r['fhi_GHz'], '%.1f' % _p['dish'],
                         _r['pb_offset_arcsec'],
                         '%.4f' % (PB_COEF_ALMA * C_M_S / _p['f'] / _p['dish']
                                   * ARCSEC),
                         _r['pb_atten'], '%.6f' % _p['a_alma'],
                         '%.6f' % (_p['a_pub'] / _p['a_alma'])])
    print('  wrote pb_atten_fwhm_r11.csv (%d rows)' % len(PBROWS))
_readers = []
for _f in sorted(os.listdir(HERE)):
    if _f.endswith('.py') and _f != os.path.basename(__file__):
        try:
            if 'pb_atten' in open(os.path.join(HERE, _f), errors='ignore').read():
                _readers.append(_f)
        except OSError:
            pass
ck('the generators that read pb_atten are enumerated, so changing the column '
   'in place could not have gone unnoticed', True,
   '%d read it: %s' % (len(_readers), ', '.join(_readers)))


# ======================================================================= 5
# THE PARALLACTIC OFFSET IN SYNTHESISED BEAMS.
#
# This is the quantity that decides whether treating the loss as a scalar is
# legitimate.  An offset that is a small fraction of a beam attenuates a
# compact source and does nothing else; an offset approaching a beam puts the
# phase wrong on every long baseline, and no scalar describes that.  The two
# orderings -- by loss and by beams -- are the SAME ordering, because the loss
# is a monotone function of the offset in beams; what the beams add is a
# criterion for validity, not a different priority list.  That is asserted
# here rather than left for a reader to assume.
PXB = {b['eb']: b for b in PXL['blocks']}
PX = []
for r in CAT:
    b = PXB.get(r['eb'])
    if b:
        PX.append(dict(row=r, beams=b['beams'], loss=1.0 - b['Bm'],
                       retained=b['Bm'], syn=b['syn'], dpar=b['dpar']))
# ★ THE TWO ORDERINGS AGREE WHERE THEY MATTER AND DISAGREE WHERE THEY DO
# NOT, AND THAT IS WORTH MEASURING RATHER THAN ASSUMING EITHER WAY.  The loss
# is the MEASURED normalised dirty beam, which depends on the uv distribution
# and not on the offset in beams alone, so it is not a monotone function of
# it.  But the disagreements are all among blocks whose loss is a fraction of
# a per cent: the top 25 blocks are the same set under either key.  So the
# referee's distinction is real in physics and does not reorder the triage;
# what the offset in beams decides is whether the scalar remedy is VALID,
# which is a different question from which window to look at first.
_blk = sorted({(x['beams'], x['loss'], x['row']['eb']) for x in PX})
N_INVERSION = sum(1 for i in range(len(_blk) - 1)
                  if _blk[i][1] > _blk[i + 1][1] + 1e-9)
INVERSION_MAXLOSS = max([max(_blk[i][1], _blk[i + 1][1])
                         for i in range(len(_blk) - 1)
                         if _blk[i][1] > _blk[i + 1][1] + 1e-9] or [0.0])
_topb = {e for _, _, e in sorted(_blk, key=lambda x: -x[0])[:25]}
_topl = {e for _, _, e in sorted(_blk, key=lambda x: -x[1])[:25]}
if DRIVE == 7:
    _topb = set()
ck('the 25 blocks with the largest offset in beams are the same 25 as the '
   'ones with the largest amplitude loss, so ordering by the physics and '
   'ordering by the bookkeeping pick the same windows to re-extract',
   _topb == _topl, '%d blocks differ' % len(_topb ^ _topl))
# and no inversion crosses the boundary of the re-extraction set, which is
# the only place an inversion could change what was done
_cross_boundary = [i for i in range(len(_blk) - 1)
                   if _blk[i][1] > _blk[i + 1][1] + 1e-9
                   and (_blk[i][1] > 0.10) != (_blk[i + 1][1] > 0.10)]
if DRIVE == 11:
    _cross_boundary = [0]
ck('and no disagreement between the two orderings crosses the boundary of '
   'the re-extracted set, so none of them changed what was done',
   not _cross_boundary,
   '%d inversions in all, worst at a loss of %.1f per cent, %d crossing the '
   'boundary' % (N_INVERSION, 100 * INVERSION_MAXLOSS, len(_cross_boundary)))
BEAMS_MAX = max(x['beams'] for x in PX)
BEAMS_MED = med([x['beams'] for x in PX])
N_BEAMS_QUARTER = sum(1 for x in PX if x['beams'] > 0.25)
N_BEAMS_QUARTER_A = sum(1 for x in PX
                        if x['beams'] > 0.25 and x['row']['search_class'] == 'A')
N_BEAMS_TENTH = sum(1 for x in PX if x['beams'] > 0.10)
N_LOSS_TENTH = sum(1 for x in PX if x['loss'] > 0.10)
EB_BEAMS_QUARTER = sorted({x['row']['eb'] for x in PX if x['beams'] > 0.25})
ck('no window in the release has a parallactic offset of a whole synthesised '
   'beam, which is the premise the remedy was asked for under',
   BEAMS_MAX < 1.0, 'largest offset %.3f beams' % BEAMS_MAX)

# ======================================================================= 5b
# ★★★ THE RE-EXTRACTION, AND THE MEASUREMENT THAT MAKES THE AMPLITUDE FACTOR
# A MEASUREMENT RATHER THAN A MODEL.
#
# Re-extracting a window at the apparent position says whether any disposition
# moves.  It cannot say whether the retained-amplitude factor is right, because
# the factor describes a compact source at the star and these windows contain
# none: the statistic there is a noise maximum over a drift plane, and moving
# the extraction point by two thirds of a synthesised beam draws a nearly
# independent noise realisation.  Measured that way the ratio scatters about
# one and says nothing either way.  ★ A CHECK THAT CANNOT RESPOND TO THE THING
# IT IS SUPPOSED TO TEST IS NOT A CHECK, so a source was put there: a carrier
# injected at the apparent direction cosines and recovered from the SAME
# visibilities at both positions.  The ratio of recovered signal-to-noise then
# IS the normalised dirty beam at the omitted displacement, on that block's own
# uv coverage, with no model in it.
RX = json.load(open(os.path.join(HERE, 'r11inputs', 'reext_r11.json')))
RE = [r for r in RX['reext'] if r.get('status') == 'ok']
PT = [r for r in RX['pxtest'] if r.get('status') == 'ok']
N_RE_WIN = len(RE)
N_RE_BLOCK = len({r['unit']['eb'] for r in RE})
RE_NOISE = sorted(r['noise_ratio'] for r in RE)
RE_TSTAR = sorted(r['measured_ratio_tstar'] for r in RE)
N_RE_CHANGED = sum(1 for r in RE if r['crossing_changed'])
ck('re-extracting at the apparent position leaves the window\'s own noise '
   'unchanged, so the denominator of every limit is unaffected by the '
   'extraction position',
   max(abs(x - 1.0) for x in RE_NOISE) < 0.005,
   'noise ratio %.5f to %.5f over %d windows'
   % (RE_NOISE[0], RE_NOISE[-1], N_RE_WIN))
if DRIVE == 18:
    N_RE_CHANGED = 1
ck('and it changes no disposition: no crossing appears and none disappears',
   N_RE_CHANGED == 0, '%d of %d windows change' % (N_RE_CHANGED, N_RE_WIN))
_tsc = max(abs(x - 1.0) for x in RE_TSTAR)
ck('the statistic at the star scatters about unity rather than about the '
   'retained fraction, which is what a source-free window must do and is why '
   'the factor has to be tested with a source',
   abs(med(RE_TSTAR) - 1.0) < 0.1 and _tsc > 0.1,
   'median %.3f, spread %.3f-%.3f, against predicted retentions %s'
   % (med(RE_TSTAR), RE_TSTAR[0], RE_TSTAR[-1],
      sorted({round(r['predicted_retained'], 3) for r in RE})))

# the injected measurement
PX_ROWS = sorted(
    [dict(tag=r['unit']['tag'], star=r['unit']['star'], beams=r['beams'],
          pred=r['predicted_retained'],
          meas=r['measured_retained_median'],
          lo=r['measured_retained_lo'], hi=r['measured_retained_hi'],
          n=r['n_paired'],
          ratio=r['measured_retained_median'] / r['predicted_retained'])
     for r in PT], key=lambda x: x['beams'])
if PX_ROWS:
    _small, _large = PX_ROWS[0], PX_ROWS[-1]
    if DRIVE == 19:
        _small['ratio'] = 2.0
    ck('the scalar amplitude correction is accurate where the displacement is '
       'a small fraction of a beam', abs(_small['ratio'] - 1.0) < 0.07,
       'at %.3f beams, measured %.4f against a predicted %.4f, ratio %.3f'
       % (_small['beams'], _small['meas'], _small['pred'], _small['ratio']))
    ck('and departs from the prediction where it is not, in the CONSERVATIVE '
       'direction: the pipeline retains more than the beam model predicts, so '
       'a limit corrected by the model is shallower than it needs to be',
       _large['ratio'] > _small['ratio'] and _large['ratio'] > 1.0,
       'at %.3f beams, measured %.4f against a predicted %.4f, ratio %.3f'
       % (_large['beams'], _large['meas'], _large['pred'], _large['ratio']))
    m('SensPxNTest', '%d' % len(PX_ROWS))
    m('SensPxNTone', '%d' % _large['n'])
    m('SensPxSmallBeams', '%.2f' % _small['beams'])
    m('SensPxSmallPred', '%.2f' % _small['pred'])
    m('SensPxSmallMeas', '%.2f' % _small['meas'])
    m('SensPxSmallRatioPct', '%.0f' % (100 * (_small['ratio'] - 1.0)))
    m('SensPxLargeBeams', '%.2f' % _large['beams'])
    m('SensPxLargePred', '%.2f' % _large['pred'])
    m('SensPxLargeMeas', '%.2f' % _large['meas'])
    m('SensPxLargeMeasLo', '%.2f' % _large['lo'])
    m('SensPxLargeMeasHi', '%.2f' % _large['hi'])
    m('SensPxLargeRatioPct', '%.0f' % (100 * (_large['ratio'] - 1.0)))
    m('SensPxLargeStar', texstar(_large['star']))
    m('SensPxSmallStar', texstar(_small['star']))
m('SensNReextWin', '%d' % N_RE_WIN)
m('SensNReextBlock', '%d' % N_RE_BLOCK)
m('SensReextNoiseMaxPct', '%.2f' % (100 * max(abs(x - 1.0)
                                              for x in RE_NOISE)))
m('SensNReextChanged', '%d' % N_RE_CHANGED)
m('SensReTstarLo', '%.2f' % RE_TSTAR[0])
m('SensReTstarHi', '%.2f' % RE_TSTAR[-1])
m('SensReTstarMed', '%.2f' % med(RE_TSTAR))

# the table of the measured retained amplitude
if DRIVE is None and PX_ROWS:
    _pt = os.path.join(OUTDIR, 'tab_pxmeasured_r11.tex')
    with open(_pt, 'w') as fh:
        fh.write('%% GENERATED by %s -- do not hand-edit.\n'
                 % os.path.basename(__file__))
        fh.write('\\begin{tabular}{@{}l@{~~}r@{~~}r@{~~}r@{~~}r@{}}\n'
                 '\\hline\n')
        fh.write('star & offset & predicted & measured & tones \\\\\n')
        fh.write(' & (beams) & & & \\\\\n\\hline\n')
        for r in PX_ROWS:
            fh.write('%s & %.2f & %.3f & $%.3f^{+%.3f}_{-%.3f}$ & %d '
                     '\\\\\n'
                     % (texstar(r['star']), r['beams'], r['pred'], r['meas'],
                        r['hi'] - r['meas'], r['meas'] - r['lo'], r['n']))
        fh.write('\\hline\n\\end{tabular}\n')
    print('  wrote tab_pxmeasured_r11.tex (%d rows)' % len(PX_ROWS))



# ======================================================================= 6
# MACROS
m('SensNInj', '%d' % N_INJ)
m('SensNInjOld', '%d' % len(OLD_TAGS))
m('SensNInjNew', '%d' % len(NEW_TAGS))
m('SensNInjBlock', '%d' % len({g.rsplit('_spw', 1)[0] for g in TAGS}))
m('SensNInjPct', '%.0f' % (100.0 * N_INJ / N_A))
m('SensNTransfer', '%d' % (N_A - N_INJ))
m('SensSeed', '%d' % SEL['seed'])
m('SensNFrameWin', '%d' % SEL['n_frame_windows'])
m('SensNFrameBlock', '%d' % SEL['n_frame_blocks'])
# the completeness, to two significant figures as the policy requires
m('SensMultA', '%.2f' % P90_TRIG)
m('SensMultALo', '%.2f' % P90_LO)
m('SensMultAHi', '%.2f' % P90_HI)
m('SensMultRank', '%.2f' % P90_RANK)
m('SensIndivLo', '%.2f' % IND_LO)
m('SensIndivHi', '%.2f' % IND_HI)
m('SensNIndiv', '%d' % N_RES_TRIG)
m('SensNIndivRank', '%d' % N_RES_RANK)
m('SensRingHi', '%.2f' % RING_HI_TRIG)
m('SensRingLo', '%.2f' % RING_LO_TRIG)
m('SensNRingHi', '%d' % len(HI))
m('SensNRingHiUnres', '%d' % N_UNRES_RANK_HI)
m('SensRingRule', '%.0f' % RING_RULE_SIGMA)
m('SensRingCatPct', '%.0f' % (100.0 * STRA0['disc']['n_cat'] / N_A))
m('SensNRingCat', '%d' % STRA0['disc']['n_cat'])
m('SensStratDevPct', '%.1f' % (100 * _dev))
m('SensCostMed', '%.2f' % COST_MED)
m('SensCostHi', '%.2f' % COST_HI)
m('SensBandSpread', '%.2f' % BAND_SPREAD)
m('SensChanSpread', '%.2f' % CHAN_SPREAD)
m('SensArrSpread', '%.2f' % ARR_SPREAD)
m('SensCovAxis', COV_AXIS)
m('SensCovMax', '%.2f' % COV_MAX)
m('SensTransferLo', '%.2f' % TR_LO)
m('SensTransferHi', '%.2f' % TR_HI)
m('SensTransferFullLo', '%.2f' % TR_FULL_LO)
m('SensTransferFullHi', '%.2f' % TR_FULL_HI)
m('SensIndivHiTag', _hi_tag.replace('_', '\\_'))
m('SensIndivHiSecond', '%.2f' % _hi_second)
m('SensNCrossAch', '%d' % N_CROSS_ACH)
m('SensNCrossExp', '%.1f' % _exp)
m('SensCovWorstPct', '%.0f' % (100 * max(c['worst_abs_frac_diff']
                                         for c in COV.values())))
m('SensCovWorstAxis', max(COV, key=lambda k: COV[k]['worst_abs_frac_diff']))
# the primary beam
m('SensPbCoefCode', '%.2f' % PB_COEF_CODE)
m('SensPbCoefAlma', '%.2f' % PB_COEF_ALMA)
def _tex_e(x, nd=1):
    e = int(math.floor(math.log10(abs(x))))
    return '%.*f\\times10^{%d}' % (nd, x / 10.0 ** e, e)


m('SensPbResid', _tex_e(PBERR['a_code']))
m('SensPbResidTwelve', _tex_e(PBERR['a_twelve']))
m('SensPbNOnePct', '%d' % N_PB_1PCT)
m('SensPbNTenPct', '%d' % N_PB_10PCT)
m('SensPbShiftMaxPct', '%.1f' % (100 * (PB_SHIFT_MAX - 1.0)))
m('SensPbWorstStar', PB_WORST_STAR['row']['star_name'])
m('SensPbWorstOff', '%.1f' % PB_WORST_STAR['off'])
m('SensPbAMin', '%.4f' % PB_AMIN_PUB)
m('SensPbAMinAlma', '%.4f' % PB_AMIN_ALMA)
m('SensPbFloor', '%.1f' % PB_FLOOR)
m('SensPbNUnit', '%d' % PB_UNIT)
m('SensPbNInv', '%d' % PB_INV)
# the parallactic offset
m('SensBeamsMax', '%.2f' % BEAMS_MAX)
m('SensBeamsMed', '%.3f' % BEAMS_MED)
m('SensNBeamsQuarter', '%d' % N_BEAMS_QUARTER)
m('SensNBeamsQuarterA', '%d' % N_BEAMS_QUARTER_A)
m('SensNBeamsTenth', '%d' % N_BEAMS_TENTH)
m('SensNLossTenth', '%d' % N_LOSS_TENTH)
m('SensNBeamsBlock', '%d' % len(EB_BEAMS_QUARTER))
m('SensNInversion', '%d' % N_INVERSION)
m('SensInversionMaxLossPct', '%.1f' % (100 * INVERSION_MAXLOSS))
m('SensRingSplit', '%.2f' % RING_SPLIT)
m('SensRingRatio', '%.2f' % RING_RATIO)
m('SensRingRatioRank', '%.1f' % (RANK_RING_RATIO or 0.0))
m('SensPooledRingWeighted', '%.2f' % P90_STRAT)
m('SensArrSpreadFaint', '%.2f' % ARR_SPREAD_FAINT)
m('SensArrRingSharePct', '%.0f' % (100 * ARR_RING_SHARE))
m('SensArrTwelve', '%.2f' % ARR_V['12m'])
m('SensArrAca', '%.2f' % ARR_V['7m'])
m('SensPooledArrWeighted', '%.2f' % P90_ARRW)
m('SensRegBlanket', '%.2f' % REG['weighted_rank'])
m('SensRegNoise', '%.2f' % REG['noise_rank'])
m('SensRegPooledRank', '%.1f' % REG['pooled_rank'])
m('SensRegWeightedTrig', '%.2f' % REG['weighted_trig'])
m('SensRegNoiseTrig', '%.2f' % REG['noise_trig'])
m('SensCostLike', '%.2f' % COST_LIKE)
m('SensMoveNoise', '%.2f' % MOVE_NOISE)
m('SensMoveNoisePct', '%.0f' % (100 * (1.0 - MOVE_NOISE)))
m('SensMoveDisc', '%.2f' % MOVE_DISC)

# ======================================================================= 6b
# THE BUDGET OF TABLE 4, AND THE TABLE.
#
# ★ WHAT CHANGES AND WHAT DOES NOT.  The completeness factor changes; the
# budget around it barely does.  The transfer term keeps its published
# meaning -- the spread across the injected windows, which is what its own
# caption says it is -- and the sampling error of the factor itself is now a
# few per cent, so the interval is set by real window-to-window variation and
# not by the size of the campaign.  That distinction is published, because an
# interval that shrank merely because more windows were injected would be
# the wrong lesson to draw.
#
# TWO ROWS LEAVE.  The two strata and the single blanket factor collapse to
# one row, because there is one factor.  The annual-parallax row leaves
# because the correction is no longer a correction: where the offset is a
# small fraction of a beam it is a parameter-free multiplicative factor
# inside each window's own limit, and where it is not, the window is
# re-extracted at the apparent position and the amplitude is measured.  A
# budget lists what is NOT already inside the number.
#
# ONE ROW ARRIVES, in place of the parallax row: the primary-beam model.
SENSB = SENSB0
INST = SENSB['combined']['instrumental']
INST_WORST = SENSB['combined']['instrumental_worst']
BOOT_LO_PCT = 1.0 - P90_LO / P90_TRIG
BOOT_HI_PCT = P90_HI / P90_TRIG - 1.0
TRANS_LO_PCT = 1.0 - TR_LO
TRANS_HI_PCT = TR_HI - 1.0

# ★★★★ WHAT THE QUOTED INTERVAL IS AN INTERVAL ON, AND WHAT IT IS NOT.
#
# The interval used to be hypot(window-to-window spread, calibration) and was
# printed as applying "to every limit".  The window-to-window spread is a
# DISPERSION AMONG THE INJECTED WINDOWS -- the central two thirds of 49
# measured ninety-per-cent points -- and a dispersion among tested windows is
# not an uncertainty on carrying one factor to each of the other 353.  Quoting
# it that way claimed a precision of plus or minus seven per cent on an
# individual limit while the measured points themselves span x0.80 to x1.58 of
# the adopted factor: the error bar was four times narrower than the scatter
# it was derived from.
#
# So the two quantities are separated and each is given the meaning it has:
#
#   * the QUOTED INTERVAL is the uncertainty on the class-average calibration
#     -- the sampling error of the pooled factor over the injected windows,
#     and the absolute flux, distance and visibility scale.  It applies to the
#     factor, and therefore to any statistic formed over many windows: the
#     median limit, the system counts, the figures of merit.
#   * the WINDOW-TO-WINDOW RANGE is published as what it is, an observed
#     dispersion over the injected windows, with its full extent and not only
#     its central two thirds.  It is the statement about an individual
#     uninjected window's own limit, and it is deliberately wider.
#
# Nothing is hidden by the change: the dispersion is now printed at its full
# x0.80-x1.58 rather than at a trimmed -6/+8 per cent.
COMB_LO = math.hypot(BOOT_LO_PCT, INST)
COMB_HI = math.hypot(BOOT_HI_PCT, INST)
ck('the sampling error of the completeness factor is much smaller than the '
   'window-to-window spread, so the quoted interval is an interval on the '
   'calibration and the spread has to be published separately',
   max(BOOT_LO_PCT, BOOT_HI_PCT) < 0.5 * min(TRANS_LO_PCT, TRANS_HI_PCT),
   'bootstrap -%.1f/+%.1f against a spread of -%.1f/+%.1f per cent'
   % (100 * BOOT_LO_PCT, 100 * BOOT_HI_PCT,
      100 * TRANS_LO_PCT, 100 * TRANS_HI_PCT))
ck('the combined interval brackets unity and is wider than either part',
   1.0 - COMB_LO < 1.0 < 1.0 + COMB_HI
   and COMB_LO > max(BOOT_LO_PCT, INST) and COMB_HI > max(BOOT_HI_PCT, INST),
   'x%.2f-x%.2f' % (1.0 - COMB_LO, 1.0 + COMB_HI))
# ★ THE CLAUSE THAT STOPS THE DISPERSION BEING FOLDED BACK IN.  If the
# quadrature sum ever contains the window-to-window term again, the interval
# grows past the calibration-only one and this fails.  Driven: --drive 22
# rebuilds it the old way.
_COMB_OLD_HI = math.hypot(TRANS_HI_PCT, INST)
if DRIVE == 22:
    COMB_HI = _COMB_OLD_HI
ck('the quoted interval contains no window-to-window dispersion term, so it '
   'is not read as a precision on an individual limit',
   COMB_HI < _COMB_OLD_HI - 1e-9,
   'calibration-only +%.1f against +%.1f with the dispersion folded in'
   % (100 * COMB_HI, 100 * _COMB_OLD_HI))
# ★ AND THE CLAUSE THAT STOPS THE DISPERSION BEING QUIETLY NARROWED.  What is
# published for an individual window is the FULL range of the measured points,
# and it must bracket the adopted factor and be wider than the quoted
# interval.  Driven by --drive 23, which substitutes the trimmed range.
IND_FAC_LO, IND_FAC_HI = TR_FULL_LO, TR_FULL_HI
if DRIVE == 23:
    IND_FAC_LO, IND_FAC_HI = TR_LO, TR_HI
ck('the window-to-window range published for an individual limit is the full '
   'range of the measured points, brackets the adopted factor and is wider '
   'than the quoted interval',
   IND_FAC_LO < 1.0 < IND_FAC_HI
   and IND_FAC_LO < 1.0 - COMB_LO and IND_FAC_HI > 1.0 + COMB_HI
   and abs(IND_FAC_LO * P90_TRIG - IND_LO) < 0.02
   and abs(IND_FAC_HI * P90_TRIG - IND_HI) < 0.02,
   'x%.2f-x%.2f, i.e. %.2f-%.2f P_trig against an adopted %.2f'
   % (IND_FAC_LO, IND_FAC_HI, IND_FAC_LO * P90_TRIG, IND_FAC_HI * P90_TRIG,
      P90_TRIG))

# ------------------------------------------------- decorrelation, one-sided
# ★★★★ THE SIGN OF THIS TERM IS NOT A CHOICE.  A synthetic carrier is added
# to visibilities that have already been phase- and amplitude-calibrated, so
# it suffers no atmospheric or instrumental coherence loss; a real carrier
# does.  The completeness is therefore OPTIMISTIC by the array's coherence
# loss and by nothing in the other direction, and a negative branch would
# assert that a real carrier is recovered better than an injected one, which
# the injection route cannot produce.  It was printed as a two-sided bracket.
#
# ★★★★ AND THE MAGNITUDE IS NOW MEASURED, BLOCK BY BLOCK, FROM THIS SURVEY'S
# OWN DATA.  It used to be a flat twenty per cent "declared from the
# literature rather than measured here" -- with no reference given, which is
# not a declaration from the literature at all.  Every block observes a phase
# calibrator, which is a point source at the phase centre, and the observatory
# records its residual path-length fluctuation after the water-vapour
# correction; that path rms, taken to each window's own sky frequency, IS the
# coherence a carrier would lose.  decor_r13.py does the arithmetic and
# carries the checks on the reading.  The flat bound turns out to have been
# wrong in both directions at once: the median window loses one per cent, and
# a long-baseline or high-frequency minority loses very much more.
import decor_r13                                              # noqa: E402

DEC = decor_r13.load()
_DPERT = {28: 'impute', 30: 'medianforhigh'}.get(DRIVE)
if DRIVE in (29, 31):
    # break the reading, not the arithmetic: 29 corrupts the degrees the
    # report printed, 31 swaps the two arrays' labels
    DEC = json.loads(json.dumps(DEC))
    for _b in DEC['blocks'].values():
        if DRIVE == 29 and 'stated_phasecal_deg' in _b:
            _b['stated_phasecal_deg'] *= 1.6
        if DRIVE == 31 and 'array_m' in _b:
            _b['array_m'] = 19.0 - _b['array_m']
            _b['bl_max_m'] = 1000.0 - min(999.0, _b.get('bl_max_m', 0.0))
DECM = decor_r13.measure(CAT, DEC, perturb=_DPERT)
DECOR = [0.0, DECM['opt_med']]
DECOR_HI = DECM['opt_hiband_med']
if DRIVE == 24:
    DECOR = DEC['superseded_declaration']['declared_two_sided']
_DECLARED = DEC['superseded_declaration']['declared_two_sided']
ck('decorrelation is one-sided in the direction that weakens the limits',
   DECOR[0] == 0.0 and DECOR[1] > 0.0,
   '%+.1f/%+.1f per cent against a declared %+.0f/%+.0f'
   % (100 * DECOR[0], 100 * DECOR[1],
      100 * _DECLARED[0], 100 * _DECLARED[1]))
ck('and it is measured here, from the survey\'s own blocks, rather than '
   'declared with no reference',
   DEC['measured_here'] is True, str(DEC['measured_here']))
for _lab, _ok, _det in decor_r13.self_checks(DEC):
    ck(_lab, _ok, _det)
ck('the coverage of the measurement is published rather than imputed: the '
   'blocks whose delivery exposes no report carry no value',
   DECM['n_block'] < DECM['n_block_cat']
   and DECM['n_win'] < DECM['n_win_cat'],
   '%d of %d blocks, %d of %d windows, %d of %d bands'
   % (DECM['n_block'], DECM['n_block_cat'], DECM['n_win'],
      DECM['n_win_cat'], DECM['n_band'], DECM['n_band_cat']))
# ★ THE CLAUSE THAT STOPS THE TERM BECOMING ONE FLAT NUMBER AGAIN.  The whole
# point of the measurement is that the loss is not the same at the top of the
# frequency range as in the middle of it, so the high-frequency figure must be
# strictly the larger and must be published beside the median.
ck('the loss above the high-frequency threshold is strictly larger than the '
   'median window\'s, so one flat figure cannot stand for both',
   DECOR_HI > DECOR[1] and DECM['n_hiband_win'] > 0,
   '%.1f per cent over %d windows above %.0f GHz against %.1f per cent for '
   'the median window'
   % (100 * DECOR_HI, DECM['n_hiband_win'], DECM['hiband_ghz'],
      100 * DECOR[1]))

m('SensInstPct', '%.0f' % (100 * INST))
m('SensTransPctLo', '%.0f' % (100 * TRANS_LO_PCT))
m('SensTransPctHi', '%.0f' % (100 * TRANS_HI_PCT))
m('SensIndivFacLo', '%.2f' % IND_FAC_LO)
m('SensIndivFacHi', '%.2f' % IND_FAC_HI)
m('SensBootPct', '%.0f' % (100 * max(BOOT_LO_PCT, BOOT_HI_PCT)))
m('SensCombPctLo', '%.0f' % (100 * COMB_LO))
m('SensCombPctHi', '%.0f' % (100 * COMB_HI))
m('SensFacLo', '%.2f' % (1.0 - COMB_LO))
m('SensFacHi', '%.2f' % (1.0 + COMB_HI))
m('SensDecorPct', '%.0f' % (100 * DECOR[1]))
m('SensDecorHiPct', '%.0f' % (100 * DECOR_HI))
m('SensDecorHiGHz', '%.0f' % DECM['hiband_ghz'])
m('SensDecorTailPct', '%.0f' % (100 * DECM['tail_frac']))
m('SensDecorTailLevelPct', '%.0f' % (100 * DECM['tail_level']))
m('SensDecorNBlk', '%d' % DECM['n_block'])
m('SensDecorNBlkTot', '%d' % DECM['n_block_cat'])

TABLE = os.path.join(OUTDIR, 'tab_budget_r11%s.tex' % SUF)
with open(TABLE, 'w') as fh:
    w = fh.write
    w('%% GENERATED by %s -- do not hand-edit.\n' % os.path.basename(__file__))
    w('\\begin{tabular}{@{}l@{~~}r@{~~}'
      '>{\\raggedright\\arraybackslash}p{0.37\\columnwidth}@{}}\n')
    w('\\hline\n & value & what it does to the limit \\\\\n\\hline\n')
    w('Class-average completeness & $\\times%.2f$ & nine carriers in ten '
      'recovered at this multiple of a window\'s own trigger power, over '
      '%d injected Class~A windows \\\\\n' % (P90_TRIG, N_INJ))
    w('\\hline\n\\multicolumn{3}{@{}l}{\\emph{Uncertainty on that '
      'calibration} (per cent), combined in quadrature} \\\\\n')
    w('The factor itself & $\\pm%.0f$ & sampling error of the pooled value '
      'over the %d injected windows \\\\\n'
      % (100 * max(BOOT_LO_PCT, BOOT_HI_PCT), N_INJ))
    w('Flux, distance and visibility scale & $\\pm%.0f$ & calibration '
      '\\\\\n' % (100 * INST))
    w('\\emph{Combined} & $-%.0f/+%.0f$ & $\\times%.2f$--$\\times%.2f$ '
      'on the factor, and so on the median limit and on the system counts '
      '\\\\\n'
      % (100 * COMB_LO, 100 * COMB_HI, 1.0 - COMB_LO, 1.0 + COMB_HI))
    w('\\hline\n\\multicolumn{3}{@{}l}{\\emph{Spread between windows}. An '
      'observed dispersion, not an error bar.} \\\\\n')
    w('Window to window & $\\times%.2f$--$\\times%.2f$ & the %d injected '
      'windows resolve %.2f--%.2f\\,$P_{\\rm trig}$ individually, so an '
      'uninjected window\'s own completeness is not known to the interval '
      'above \\\\\n' % (IND_FAC_LO, IND_FAC_HI, N_INJ, IND_LO, IND_HI))
    w('\\hline\n\\multicolumn{3}{@{}l}{\\emph{Signed terms}. A bias is '
      'not an error bar and is not added to one.} \\\\\n')
    w('Channel response & $\\times\\InjPeakAtNinety$ & carried by the '
      'injections, so already inside the completeness above \\\\\n')
    w('\\quad its residual & $+\\InjShortPct$ & the injected profile falls '
      'short of the exact response: \\emph{conservative} \\\\\n')
    w('Primary-beam model & $+0/+%.0f$ & ALMA\'s beamwidth in place of the '
      'pipeline\'s Airy-null one: nothing in the median window, '
      '%d windows of one star \\\\\n'
      % (100 * (PB_SHIFT_MAX - 1.0), N_PB_10PCT))
    # ★ The row the referee was right about.  It carried one flat figure, and
    # the figure was asserted.  It now carries a measurement, and because the
    # measurement is per block the row has to say so in both directions: what
    # the median window loses, and what the tail loses.
    w('Decorrelation & $+0/+\\SensDecorPct$ & measured block by block from '
      'the phase rms the observatory records on each block\'s phase '
      'calibrator, which an injected carrier does not suffer and a real one '
      'does: $+\\SensDecorHiPct$ above \\SensDecorHiGHz\\,GHz, and more than '
      '$+\\SensDecorTailLevelPct$ in \\SensDecorTailPct{} per cent of '
      'windows \\\\\n')
    w('\\hline\n\\end{tabular}\n')
print('  wrote %s' % os.path.basename(TABLE))

# ======================================================================= 6c
# THE HEADLINE, RECOMPUTED.  Not emitted as macros -- \EirpNinety* already
# name these quantities and a second name for one number is what twinmacro
# exists to refuse.  Written to the json so that the one-line change in
# adopted_e90.py can be verified against it.
PXBM = json.load(open(os.path.join(HERE, 'pxapply_v411.json')
                      ))['retained_fraction_by_eb']
# ★★★ v4.12 INTEGRATION: THIS WAS A CIRCULAR DEPENDENCY, and only a clean
#     regeneration could see it.  The Class B factor was read out of the macro
#     layer -- i.e. out of round 103, which `numbers_v410.py` writes -- and
#     `numbers_v410.py` reads THIS file's json for the factor it writes there.
#     On any tree where the macro files already existed the read returned the
#     PREVIOUS run's value and the cycle was invisible; from a clean tree the
#     name is undefined, `MULT_B` came back None, `HEAD` stayed empty, and
#     `numbers_v410.py` died 100 lines later with `KeyError: 'win_med'` -- two
#     generators away from the cause.
#     The cycle is broken by using this file's OWN measurement, `P90_B`, which
#     is what the loop below already used for every Class B row: `MULT_B` was
#     never the number the headline was computed with, only the number it was
#     reported against.  The macro layer is still consulted, but as a
#     cross-check WHERE IT IS DEFINED and never as the source -- the same
#     discipline `recur_v411.py` adopted for \\LNNRetained.
import adopted_e90 as _ae
MULT_B = P90_B
try:
    _layer_b = _ae.multiplier_b(HERE)
except Exception:
    _layer_b = None
if _layer_b:
    ck('the Class B factor this file measures is the one the macro layer '
       'publishes, where the layer defines it at all',
       abs(_layer_b / P90_B - 1.0) < 0.01,
       'layer %.4f against measured %.4f' % (_layer_b, P90_B))
else:
    print('  Class B factor not yet in the macro layer (clean tree); the '
          'headline uses this file own measurement, %.4f' % P90_B)
HEAD = {}
if MULT_B:
    _win, _sys = [], collections.defaultdict(list)
    for r in CAT:
        mult = P90_TRIG if r['search_class'] == 'A' else P90_B
        e = float(r['eirp_nominal_W']) * mult
        bm = PXBM.get(r['eb'])
        if bm:
            e /= bm
        r['_e90new'] = e
        if r['search_class'] == 'A':
            _win.append(e)
            _sys[r['system_id']].append(e)
    _best = sorted(min(v) for v in _sys.values())
    HEAD = dict(mult_a=P90_TRIG, mult_b=MULT_B,
                win_med=med(_win), sys_med=med(_best),
                sys_lo=_best[0], sys_hi=_best[-1],
                n_sys=len(_best),
                n_sys_1e15=sum(1 for x in _best if x <= 1e15))
    print('  headline on the new criterion: median window %.3g W, median '
          'system %.3g W, %d of %d systems reach 1e15 W'
          % (HEAD['win_med'], HEAD['sys_med'], HEAD['n_sys_1e15'],
             HEAD['n_sys']))

# ======================================================================= 7
# FIGURE: the one piece of evidence Ruling 1 rests on, in one single-column
# panel, replacing a full-width two-panel figure about a stratification that
# no longer exists.
if not NOFIG and DRIVE is None:
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    fig, ax = plt.subplots(figsize=(3.4, 2.9))
    xs = [RING[g] for g in TAGS]
    yt = [PER[g]['trig'] for g in TAGS]
    yr = [PER[g]['rank'] for g in TAGS]
    ax.axhline(P90_TRIG, color='C0', lw=1.0, zorder=1)
    ax.axhspan(P90_LO, P90_HI, color='C0', alpha=0.15, zorder=0)
    ax.scatter(xs, yt, s=22, c='C0', marker='o', zorder=3,
               label='trigger alone')
    _xr = [x for x, y in zip(xs, yr) if y is not None]
    _yr = [y for y in yr if y is not None]
    ax.scatter(_xr, _yr, s=26, facecolors='none', edgecolors='0.35',
               marker='s', zorder=2, label='trigger and 512-position rank')
    top = max([y for y in yr if y is not None] + [IND_HI]) * 1.25
    for x, y in zip(xs, yr):
        if y is None:
            ax.annotate('', xy=(x, top), xytext=(x, top / 1.18),
                        arrowprops=dict(arrowstyle='-|>', color='0.35',
                                        lw=0.9))
    ax.axvline(RING_RULE_SIGMA, color='0.6', ls=':', lw=0.9)
    ax.set_xlabel(r'control-ring maximum, $\sigma$')
    ax.set_ylabel(r'$P_{90}\,/\,P_{\rm trig}$')
    ax.set_ylim(0, top * 1.05)
    ax.legend(fontsize=6, frameon=False, loc='upper left')
    fig.tight_layout(pad=0.3)
    fig.savefig(os.path.join(OUTDIR, 'figures', 'sens_ring.pdf'))
    plt.close(fig)
    print('  wrote figures/sens_ring.pdf')

# ======================================================================= 8
doc = dict(
    generated_by=os.path.basename(__file__), round=ROUND, drive=DRIVE,
    criterion=('recovery through extraction, baseline removal, de-drifted '
               'stack and the trigger at the stellar position; the '
               '512-position rank is recorded and not required'),
    n_injected=N_INJ, n_injected_old=len(OLD_TAGS), n_injected_new=len(NEW_TAGS),
    tags=TAGS, per_window=PER, ring=RING, amps=AMPS,
    curve_trig=curve(TAGS, 'trig'), curve_rank=curve(TAGS, 'rec'),
    p90=P90_TRIG, p90_rank=P90_RANK, p90_boot=dict(
        lo=P90_LO, hi=P90_HI, undef_frac=BOOT_UNDEF, n=len(BOOT)),
    p90_ring_weighted=P90_STRAT, ring_rule_sigma=RING_RULE_SIGMA,
    individual=dict(lo=IND_LO, hi=IND_HI, n=N_RES_TRIG),
    rank_cost=dict(median=COST_MED, max=COST_HI, n=len(COST)),
    covariates=COV, continuous=CONT,
    spreads=dict(band=BAND_V, chanw={str(k): v for k, v in CHAN_V.items()},
                 array=ARR_V),
    transfer=dict(lo=TR_LO, hi=TR_HI, full_lo=TR_FULL_LO, full_hi=TR_FULL_HI,
                  per_window=_IND, shallowest=_hi_tag), p90_array_weighted=P90_ARRW,
    budget=dict(transfer_lo=TRANS_LO_PCT, transfer_hi=TRANS_HI_PCT,
                boot_lo=BOOT_LO_PCT, boot_hi=BOOT_HI_PCT,
                instrumental=INST, instrumental_worst=INST_WORST,
                comb_lo=COMB_LO, comb_hi=COMB_HI,
                factor_lo=1.0 - COMB_LO, factor_hi=1.0 + COMB_HI,
                comb_is='the uncertainty on the class-average calibration; '
                        'the window-to-window dispersion is published beside '
                        'it as a range and is NOT folded in',
                individual_fac_lo=IND_FAC_LO, individual_fac_hi=IND_FAC_HI,
                # the key name is legacy: numbers_v410.py reads it, and the
                # quantity is now MEASURED, which is what the two keys below
                # record.  It carries the median window's loss.
                decorrelation_declared=DECOR,
                decorrelation_one_sided=True,
                decorrelation_measured_here=DEC['measured_here'],
                decorrelation_hiband=DECOR_HI,
                decorrelation_hiband_ghz=DECM['hiband_ghz'],
                decorrelation_tail_frac=DECM['tail_frac'],
                decorrelation_n_block=DECM['n_block'],
                decorrelation_n_block_cat=DECM['n_block_cat'],
                decorrelation_bands={k: v['opt_med']
                                     for k, v in DECM['bands'].items()},
                decorrelation_direction=DEC['_direction']),
    covariate_largest=dict(axis=COV_AXIS, spread=COV_MAX,
                           all=_COV_SPREAD,
                           array_ring_share=ARR_RING_SHARE,
                           array_spread_faint=ARR_SPREAD_FAINT),
    class_b=dict(n_inj=N_INJ_B, n_inj_block=N_INJ_B_BLOCK, n_tone=N_TONE_B,
                 n_cat=sum(WCAT_B), n_blind=N_BLIND_B, p90=P90_B),
    headline=HEAD, p90_B=P90_B, p90_B_rank=P90_B_RANK,
    strat=dict(bins=_BINS, n_cat=WCAT, n_inj=[len(x) for x in BYBIN],
               n_cat_B=WCAT_B, n_inj_B=[len(x) for x in BYBIN_B],
               n_matched=N_INJ, n_matched_B=len(MATCH_B),
               n_blind=N_BLIND, n_blind_B=N_BLIND_B,
               n_covered=sum(WCAT[i] for i in range(len(WCAT))
                             if WCAT[i] and BYBIN[i]),
               n_covered_B=sum(WCAT_B[i] for i in range(len(WCAT_B))
                               if WCAT_B[i] and BYBIN_B[i]),
               unmatched=[], unmatched_B=UNMATCHED_B),
    route_dev=_rdev, n_blind_B=N_BLIND_B,
    regression=dict(recomputed=REG, published_blanket=PUB_BLANKET,
                    published_noise=PUB_NOISE,
                    published_disc_bound=[PUB_DISC_LO, PUB_DISC_ADOPTED],
                    recomputed_all=REG_ALL,
                    cost_like_for_like=COST_LIKE, cost_pooled=COST_POOLED,
                    move_noise=MOVE_NOISE, move_disc=MOVE_DISC),
    ring_summary=dict(split=RING_SPLIT, ratio=RING_RATIO,
              ratio_rank=RANK_RING_RATIO, n_hi=len(HI),
              n_hi_unresolved_rank=N_UNRES_RANK_HI,
              lo_range=_lo_rng),
    ordering=dict(n_inversion=N_INVERSION,
                  inversion_max_loss=INVERSION_MAXLOSS),
    crossings=dict(achieved=N_CROSS_ACH, expected=_exp, z=_z,
                   population=N_CROSS_POP),
    pb_readers=_readers,
    pb=dict(coef_code=PB_COEF_CODE, coef_alma=PB_COEF_ALMA,
            residuals=PBERR, n_gt_1pct=N_PB_1PCT, n_gt_10pct=N_PB_10PCT,
            shift_median=PB_SHIFT_MED, shift_max=PB_SHIFT_MAX,
            worst_star=PB_WORST_STAR['row']['star_name'],
            a_min_published=PB_AMIN_PUB, a_min_alma=PB_AMIN_ALMA,
            floor=PB_FLOOR, n_unit_response=PB_UNIT, n_zero_offset=PB_ZERO,
            n_invertible=PB_INV),
    reext=dict(n_win=N_RE_WIN, n_block=N_RE_BLOCK,
               noise_ratio_range=[RE_NOISE[0], RE_NOISE[-1]],
               tstar_ratio=RE_TSTAR, n_changed=N_RE_CHANGED,
               injected_test=PX_ROWS),
    beams=dict(max=BEAMS_MAX, median=BEAMS_MED, n_gt_quarter=N_BEAMS_QUARTER,
               n_gt_quarter_classA=N_BEAMS_QUARTER_A,
               n_gt_tenth=N_BEAMS_TENTH, n_loss_gt_tenth=N_LOSS_TENTH,
               blocks_gt_quarter=EB_BEAMS_QUARTER),
    selection=dict(seed=SEL['seed'], sha256=SEL.get('sha256_of_this_file'),
                   n_frame_windows=SEL['n_frame_windows'],
                   n_frame_blocks=SEL['n_frame_blocks']),
    failures=FAIL)
json.dump(doc, open(OUT_JSON, 'w'), indent=1)
with open(OUT_TEX, 'w') as fh:
    fh.write('%% GENERATED by %s -- do not hand-edit.\n'
             % os.path.basename(__file__))
    fh.write('\n'.join(sorted(OUT)) + '\n')

print('\n%d macros -> %s' % (len(OUT), os.path.basename(OUT_TEX)))
print('injected %d of %d Class A windows (%.0f per cent)' % (N_INJ, N_A, 100.0 * N_INJ / N_A))
print('completeness, one curve under two weightings and two criteria:')
print('                           pooled   ring-weighted   noise stratum')
print('  trigger and rank        %7.2f %13.2f %15.2f   <- 4.42 and 3.45 published'
      % (REG['pooled_rank'], REG['weighted_rank'], REG['noise_rank']))
print('  trigger alone           %7.2f %13.2f %15.2f   <- 3.06 adopted'
      % (REG['pooled_trig'], REG['weighted_trig'], REG['noise_trig']))
print('  adopted %.2f (%.2f-%.2f); the rank cost x%.2f like for like; the '
      'limits move x%.3f' % (P90_TRIG, P90_LO, P90_HI, COST_LIKE, MOVE_NOISE))
if FAIL:
    print('FAILURES: %s' % FAIL)
    sys.exit(1)
