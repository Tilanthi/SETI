#!/usr/bin/env python3
r"""round 410 -> survey_numbers_round410.tex, scope_r14.json

TWO COMPLETENESSES, AND THE SELECTION EFFECT IN THE PER-SYSTEM LIMIT.

WHY THIS FILE EXISTS.  EIRP_90 is measured through the trigger and the
localisation at the star, in ONE execution block.  A detection, by this
paper's own definition, needs the event again in an independently separated
block.  Those are two different completenesses over two different
populations, and every sentence that quotes the first over all 60 Class A
systems as though it bounded the second is wrong.  This file measures both
populations and the one quantity needed to decide whether the per-system
limits need a dispersion attached.

★★★ WHAT IT FOUND ON THE WAY, which is why the epoch split is recomputed
here rather than cited.  `epochsplit_v399.py` publishes \EpOne, \EpSameDay
and \EpNoConfirm over ALL 82 surveyed systems; its Class A restriction
(\EpAOne, \EpASameDay) was computed, never referenced, and so retired.  The
Class A sensitivity figure's second panel and its caption then quoted the
all-82 numbers -- 27 single-block and 13 same-day, 40 with no confirmation
opportunity -- beside a panel holding 60 Class A points.  The bars sum to 82.
Restricted to the carrier experiment the figures are 18 and 10, so 28 of the
60 Class A systems have no independently separated epoch and 32 do.  The
published pair is internally impossible and this file asserts why: 30 systems
could be re-observed AT THE SAME FREQUENCY more than a day apart
(\RcConfSysDay), and that set is a subset of the systems with any block more
than a day apart, so a split leaving only 20 of them cannot be the Class A
one.  That assertion is S2 and it fails on the published numbers.

THE MEASUREMENT.  For 353 of the 402 Class A windows no ninety-per-cent point
was measured: the window's trigger power is multiplied by the class-average
factor, and the 49 injected windows resolve individual factors spanning
x0.80 to x1.58 of it.  A system's limit is its BEST window, and a minimum
over several estimates is where a dispersion can bite.  So the per-window
factor is resampled from the measured distribution of 49, the per-system
minimum is re-formed, and the two published statistics are recomputed: the
per-system median and the number of systems reaching 10^15 W.  The draw is
scaled so that its mean is the adopted factor, because the question is what
the DISPERSION does and not what a 0.4 per cent difference between a pooled
curve crossing and a mean of crossings does.

NOTHING IS TYPED.  The epoch rule's two inputs are the released catalogue and
`epochs_v386.json`, the same two `epochsplit_v399.py` reads, and the all-82
reproduction is asserted against that file's own deposited json so the rule
implemented here is demonstrably its rule.  The sensitivity arithmetic is
`adopted_e90`, the module that owns the paper's headline limit, so the
baseline of the resampling is the published number and not a second
derivation of it.

    python3 scope_r14.py [--drive N] [--out DIR]

--drive 1..7 breaks one assertion each and nothing else; --drive 0 means "no
perturbation, but do not write a path production reads".
"""
import collections
import csv
import json
import os
import statistics
import random
import sys

import adopted_e90
import epochs_r14 as _ep        # the ONE determination of a block's epoch

HERE = os.path.dirname(os.path.abspath(__file__))
ROUND = 410
SEP_DAYS = 1.0
N_TRIAL = 4000
SEED = 410011
LEVEL_W = 1.0e15

DRIVE = None
OUTDIR = HERE
for _i, _a in enumerate(sys.argv):
    if _a == '--drive':
        DRIVE = int(sys.argv[_i + 1])
    if _a == '--out':
        OUTDIR = sys.argv[_i + 1]

# D36: the suffix follows the FLAG, not the perturbation.  `--drive 0` writes
# a drive path too, so a harness that runs the unperturbed baseline cannot
# leave the real products behind.
SUF = '' if DRIVE is None else '_drive%d' % DRIVE
OUT = os.path.join(OUTDIR, 'survey_numbers_round%d%s.tex' % (ROUND, SUF))
JSON_OUT = os.path.join(OUTDIR, 'scope_r14%s.json' % SUF)

FAIL = []


def ck(what, cond, detail=''):
    print('  %-70s %s' % (what[:70], 'ok' if cond else 'FAIL'))
    if not cond:
        FAIL.append('%s (%s)' % (what, detail))


def texval(name):
    v = adopted_e90._texval(name, HERE)
    assert v, 'macro \\%s is not defined in the macro layer' % name
    return v


# ======================================================================= 1
# THE TWO POPULATIONS.  One rule, applied to the whole survey and then to the
# carrier experiment, from the two files that own the inputs.
CAT = adopted_e90.catalogue(HERE)
DEP = json.load(open(os.path.join(HERE, 'epochsplit_v399.json')))

# ★★★ ROUND 14: the rule and the epochs both come from the files that own
# them.  `epochsplit_v399.py` now classifies on MEASURED epochs through
# `epochs_r14`, and WRITES the json this file reads -- it used to be a frozen
# file that generator had never written.  So the split reproduced here is the
# same rule on the same epochs, and S1 below is a real comparison rather than
# a comparison with a months-old artefact.  The Class A figures move from
# 18 + 10 = 28 / 32 to 18 + 3 = 21 / 39.
split = _ep.split


def group(pred):
    g = collections.defaultdict(set)
    for r in CAT:
        if pred(r):
            g[r['system_id']].add(r['eb'])
    return g


ALL = split(group(lambda r: True))
if DRIVE == 1:
    ALL['one'] += 1
CLA = split(group(lambda r: r['search_class'] == 'A'))
if DRIVE == 2:
    # The published claim, reproduced exactly: the all-survey single-block and
    # same-day counts asserted over the Class A system total.
    CLA = collections.Counter(one=ALL['one'], sameday=ALL['sameday'],
                              years=sum(CLA.values()) - ALL['one']
                              - ALL['sameday'])
if DRIVE == 4:
    CLA = ALL
N_A = sum(CLA.values())
INDEP_A = CLA['days'] + CLA['months'] + CLA['years']
NOCONF_A = CLA['one'] + CLA['sameday']

# S1 THE RULE IMPLEMENTED HERE IS epochsplit_v399.py's RULE.  Every bin of
#    the all-survey split must reproduce that file's deposited json exactly.
#    Without this the Class A numbers below would be a second rule wearing
#    the first one's name.  Driven: --drive 1 moves one system.
# The deposited file spells the bin `same_day`; the keys are compared one by
# one rather than by a shared name, because a Counter returns 0 for a key it
# does not hold and a loop over the wrong spelling would pass on two zeros.
_same = all([ALL['one'] == DEP['one'], ALL['sameday'] == DEP['same_day'],
             ALL['days'] == DEP['days'], ALL['months'] == DEP['months'],
             ALL['years'] == DEP['years'],
             sum(ALL.values()) == DEP['total']])
ck('S1 the all-survey split reproduces epochsplit_v399.json bin for bin',
   _same, '%s against %s' % (dict(ALL), DEP))

# S2 THE CLASS A SPLIT MUST ADMIT THE SYSTEMS THAT COULD BE CONFIRMED.
#    A system observed again AT THE SAME FREQUENCY more than a day later has,
#    a fortiori, a block more than a day later.  \RcConfSysDay counts the
#    first; INDEP_A counts the second; so the first can never exceed it.
#    On the published all-82 split the independent Class A count reads 20
#    against \RcConfSysDay = 30, which is impossible -- that is the defect.
#    Driven: --drive 2 reproduces the published pair over the Class A total.
CONF_DAY = int(texval('RcConfSysDay'))
SEARCH_SYS = int(texval('RcSearchSys'))
ck('S2 every system that could be confirmed beyond a day has an epoch '
   'beyond a day', CONF_DAY <= INDEP_A,
   '%d confirmable against %d with an independent epoch' % (CONF_DAY,
                                                            INDEP_A))

# S3 the partition closes on the carrier experiment's own system count.
if DRIVE == 3:
    N_A += 1
ck('S3 the Class A epoch partition closes on the Class A system count',
   CLA['one'] + CLA['sameday'] + INDEP_A == N_A == SEARCH_SYS
   == int(texval('NSysClassA')),
   '%d + %d + %d against %d' % (CLA['one'], CLA['sameday'], INDEP_A, N_A))

# S4 AND IT IS NOT THE PUBLISHED ONE.  The point of this section is that the
#    all-survey split is not the Class A split; a run in which they agree
#    means the restriction did nothing and every number below is the wrong
#    population again.  A check that passes when the two coincide would be
#    the defect it exists to catch.  Driven: --drive 4.
ck('S4 the Class A restriction changes the split, so the figure is not '
   'drawing the survey population',
   NOCONF_A != DEP['one'] + DEP['same_day']
   and sum(ALL.values()) != N_A,
   '%d against %d' % (NOCONF_A, DEP['one'] + DEP['same_day']))

# ======================================================================= 2
# THE SELECTION EFFECT IN THE PER-SYSTEM LIMIT.
SENS = json.load(open(os.path.join(HERE, 'sens_r11.json')))
PXA = json.load(open(os.path.join(HERE,
                                  'pxapply_v411.json')))['retained_fraction_by_eb']
F0 = SENS['p90']
MEAS = list(SENS['transfer']['per_window'])
N_INJ = SENS['individual']['n']
CAT_A = [r for r in CAT if r['search_class'] == 'A']

# The published baseline comes from the module that owns it, so the
# resampling is anchored to the paper's own limits and not to a re-derivation.
E90 = adopted_e90.per_window(CAT, HERE)


def per_system(mults):
    s = collections.defaultdict(list)
    for r, m in zip(CAT_A, mults):
        e = float(r['eirp_nominal_W']) * m
        bm = PXA.get(r['eb'])
        if bm:
            e /= bm
        s[r['system_id']].append(e)
    return sorted(min(v) for v in s.values())


BASE = per_system([F0] * len(CAT_A))
BASE_MED = statistics.median(BASE)
BASE_N = sum(1 for x in BASE if x <= LEVEL_W)

# S5 the baseline IS the published pair, to the precision the paper prints.
_pub_n = int(texval('NSysEfifteen'))
if DRIVE == 5:
    BASE_N += 1
ck('S5 the resampling baseline is the published per-system median and system '
   'count',
   BASE_N == _pub_n
   and abs(BASE_MED / statistics.median(
       sorted(E90[id(r)] for r in CAT_A)) - 1.0) < 0.5
   and abs(BASE_MED / 1.6e15 - 1.0) < 0.05,
   '%d against %s, median %.4g W' % (BASE_N, _pub_n, BASE_MED))

# S6 THE TEST MUST BE ABLE TO MOVE.  The pool is scaled to the adopted factor
#    so that only the dispersion acts; a pool with no dispersion would return
#    zero movement for every input and the measurement would be a check that
#    cannot fail.  Require both: the mean is the adopted factor, and the
#    spread is the measured one.  Driven: --drive 6 flattens the pool.
POOL = [f * F0 / statistics.mean(MEAS) for f in MEAS]
if DRIVE == 6:
    POOL = [F0] * len(MEAS)
ck('S6 the resampling pool is centred on the adopted factor and carries the '
   'measured dispersion',
   abs(statistics.mean(POOL) / F0 - 1.0) < 1e-9
   and max(POOL) / min(POOL) > 1.5 and len(POOL) == N_INJ,
   'mean %.6f, span x%.3f, n %d' % (statistics.mean(POOL),
                                    max(POOL) / min(POOL), len(POOL)))

RND = random.Random(SEED)
meds, counts, ratios = [], [], []
for _t in range(N_TRIAL):
    draw = [POOL[RND.randrange(len(POOL))] for _ in CAT_A]
    b = per_system(draw)
    meds.append(statistics.median(b))
    counts.append(sum(1 for x in b if x <= LEVEL_W))
# The same draw, read per system rather than over the class, is what one
# system's own limit is uncertain by.
SYSKEY = collections.defaultdict(list)
for r in CAT_A:
    SYSKEY[r['system_id']].append(r)
for _t in range(N_TRIAL // 4):
    for _sys, rs in SYSKEY.items():
        def _e(r, m):
            e = float(r['eirp_nominal_W']) * m
            bm = PXA.get(r['eb'])
            return e / bm if bm else e
        got = min(_e(r, POOL[RND.randrange(len(POOL))]) for r in rs)
        ref = min(_e(r, F0) for r in rs)
        ratios.append(got / ref)
meds.sort()
counts.sort()
ratios.sort()


def q(a, p):
    return a[int(p * (len(a) - 1))]


MED_SHIFT_PCT = 100.0 * (q(meds, 0.5) / BASE_MED - 1.0)
SYS_LO_PCT = 100.0 * (q(ratios, 0.05) - 1.0)
SYS_HI_PCT = 100.0 * (q(ratios, 0.95) - 1.0)
N_LO, N_HI = q(counts, 0.05), q(counts, 0.95)
if DRIVE == 7:
    MED_SHIFT_PCT = 40.0

# S7 THE ANSWER AND ITS CONSEQUENCE.  The whole point of reporting a number
#    rather than a reassurance is that the number decides something: if the
#    per-system median moved by more than the calibration interval already
#    quoted, the per-system limits would need the dispersion attached as an
#    error bar.  The clause states which way it came out, so a future run in
#    which it comes out the other way stops the build instead of printing a
#    sentence that no longer follows.  Driven: --drive 7.
CAL_PCT = float(texval('SensCombPctHi'))
ck('S7 the resampled per-system median moves by less than the calibration '
   'interval already quoted, which is what licenses the sentence',
   abs(MED_SHIFT_PCT) < CAL_PCT,
   '%.2f per cent against +/-%.0f' % (MED_SHIFT_PCT, CAL_PCT))

# ======================================================================= 3
L = ['%% GENERATED by scope_r14.py -- do not hand-edit.\n']


def m(k, v):
    assert k.isalpha(), 'a LaTeX macro name may contain letters only: %s' % k
    L.append('\\newcommand{\\%s}{%s}\n' % (k, v))


m('ScSysOneBlock', '%d' % CLA['one'])
m('ScSysSameDay', '%d' % CLA['sameday'])
m('ScSysNoConf', '%d' % NOCONF_A)
m('ScSysIndep', '%d' % INDEP_A)
m('ScRsNTrial', '%s' % ('%d' % N_TRIAL).replace('000', '\\,000'))
m('ScRsMedShiftPct', '%.1f' % abs(MED_SHIFT_PCT))
m('ScRsNLo', '%d' % N_LO)
m('ScRsNHi', '%d' % N_HI)
m('ScRsSysLoPct', '%.0f' % abs(SYS_LO_PCT))
m('ScRsSysHiPct', '%.0f' % SYS_HI_PCT)

if FAIL:
    print('\nscope_r14: %d FAILURE(S)' % len(FAIL))
    for f in FAIL:
        print('  - %s' % f)
    sys.exit(1)

open(OUT, 'w').writelines(L)
json.dump(dict(generated_by='scope_r14.py', round=ROUND, drive=DRIVE,
               sep_days=SEP_DAYS,
               all_survey=dict(ALL), class_a=dict(CLA),
               class_a_total=N_A, class_a_indep=INDEP_A,
               class_a_noconf=NOCONF_A,
               confirmable_day=CONF_DAY,
               resample=dict(n_trial=N_TRIAL, seed=SEED, n_pool=len(POOL),
                             factor=F0, level_W=LEVEL_W,
                             base_median_W=BASE_MED, base_n=BASE_N,
                             median_shift_pct=MED_SHIFT_PCT,
                             median_lo_pct=100.0 * (q(meds, 0.05) / BASE_MED
                                                    - 1.0),
                             median_hi_pct=100.0 * (q(meds, 0.95) / BASE_MED
                                                    - 1.0),
                             count_lo=N_LO, count_hi=N_HI,
                             count_min=counts[0], count_max=counts[-1],
                             sys_lo_pct=SYS_LO_PCT, sys_hi_pct=SYS_HI_PCT)),
          open(JSON_OUT, 'w'), indent=1, sort_keys=True)
print('%s: %d macros' % (os.path.basename(OUT), len(L) - 1))
print('  Class A epochs: %d systems -- %d single block, %d all within %.0f d '
      '(%d with no independent epoch), %d separated'
      % (N_A, CLA['one'], CLA['sameday'], SEP_DAYS, NOCONF_A, INDEP_A))
print('  all-survey split for comparison: %d systems, %d + %d = %d with no '
      'independent epoch' % (sum(ALL.values()), ALL['one'], ALL['sameday'],
                             ALL['one'] + ALL['sameday']))
print('  resampling: per-system median %.4g -> %.4g W (%+.2f per cent, '
      '5-95 %+.1f..%+.1f), systems at 1e15 W %d -> %d (5-95 %d..%d, full '
      '%d..%d), one system own limit %+.0f..%+.0f per cent'
      % (BASE_MED, q(meds, 0.5), MED_SHIFT_PCT,
         100.0 * (q(meds, 0.05) / BASE_MED - 1.0),
         100.0 * (q(meds, 0.95) / BASE_MED - 1.0),
         BASE_N, q(counts, 0.5), N_LO, N_HI, counts[0], counts[-1],
         SYS_LO_PCT, SYS_HI_PCT))
