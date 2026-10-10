#!/usr/bin/env python3
r"""round 65 -> survey_numbers_round65.tex, strata_v411.json, figures/sens_strata.pdf

WHAT THIS IS FOR.  Two things in the paper rested on one number that is the
completeness of no window in the survey.

  (1) WHAT THE INJECTIONS DEPOSIT.  The appendix claimed the injected
      carriers were deltas in one channel, so that the spectral response was
      outside the measurement and had to be applied to it afterwards.  That is
      false: the campaign deposits the tone split between the channels it
      straddles and then convolved with the correlator's three-point channel
      response.  This file measures what that deposition delivers, against the
      exact transform of the lag window, and shows the response is ALREADY
      inside the measured factor -- so applying it again would count it twice.
      It also measures the recovered signal-to-noise against injected
      sub-channel phase, which is flat, and the reason it is flat: a typical
      injected carrier drifts across about eleven channels during one
      observation and therefore samples the whole channel response.

  (2) WHERE THE COMPLETENESS IS TRANSFERRED TO.  A single factor was measured
      over 21 injected windows and transferred to all 402.  Stratified on the
      one variable the screen is a function of -- whether the control ring
      carries emission, the rule being fixed at 10 sigma before the curves
      were looked at -- the two strata do not share a value: the 390
      noise-dominated windows reach ninety per cent recovery at 3.4 times
      their own trigger power, and in the 12 windows whose ring carries
      resolved disc emission the ladder does not reach ninety per cent at all
      below eight times it.  The blanket factor lies above the first stratum's
      own interval and far below the second's bound.  Publishing it for every
      window is wrong in both directions, which is what both referees said.

  (3) AND THE DIAGNOSTIC THAT JUSTIFIES THAT CHOICE OF STRATUM.  Among the
      windows that resolve a ninety per cent point there is no dependence on
      band and none on channel width.  There is an apparent dependence on
      array, and it is NOT the array: it is the four windows whose target has
      bright resolved emission near the ring, and it disappears when the
      star's own contribution to the controls is removed.  The subtraction is
      implemented here as a MEASUREMENT rather than a model -- the entire rise
      of a window's control maximum with injected amplitude is the star's leak
      into the ring, so freezing each window's own uninjected control maximum
      removes exactly that and nothing else.  It is shown, it is not adopted:
      it changes the noise stratum by two per cent, changes the disc stratum
      not at all, and would make the screen depend on a model of the source
      being tested for.

NOTHING HERE IS TYPED.  The response is transformed from the lag window; the
deposition is recomputed from the injector's own kernel; the strata are
weighted by the released catalogue's own control-maximum column; the array of
each block comes from the archive metadata.  The blanket factor is read back
out of the frozen record so that this file cannot disagree with it silently.

    python3 strata_v411.py [--out DIR] [--drive N] [--nofig]

--drive 1..10 breaks one assertion each and nothing else; --drive 0 means "no
perturbation, but do not write a path production reads" (the suffix follows the
FLAG, not the perturbation).  MUST RUN BEFORE numbers_v410.py, which reads
strata_v411.json for the per-window multiplier.
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

DRIVE = None
OUTDIR = HERE
NOFIG = '--nofig' in sys.argv
for _i, _a in enumerate(sys.argv):
    if _a == '--drive':
        DRIVE = int(sys.argv[_i + 1])
    if _a == '--out':
        OUTDIR = sys.argv[_i + 1]
SUF = '' if DRIVE is None else '_drive%d' % DRIVE

# ---------------------------------------------------------------- the rule
# Fixed before any curve in this file was evaluated, and stated in the paper:
# a window is DISC-AFFECTED if its control ring carries emission at or above
# this level, and NOISE-DOMINATED otherwise.  The catalogue publishes the
# column, so every one of the 402 windows is assigned by measurement.
RULE_SIGMA = 10.0
TRIGGER_SIGMA = 5.0

# The injector's kernel, taken from the injection script rather than retyped:
# the tone is split between the two channels it straddles and the split is
# convolved with this.
HANN_KERNEL = (0.25, 0.5, 0.25)
# The exact channel response is the transform of the Hann lag window sampled
# on the channel grid.  The lag count only sets the sampling of a continuous
# function, so it is a numerical detail, not a physical one.
NLAG = 1024

# ---------------------------------------------------------------- inputs
CAT = list(csv.DictReader(open(os.path.join(
    HERE, 'per_target_results_v3.99.csv'))))
TONES = json.load(open(os.path.join(HERE, 'r9inputs', 'm3a_tones_r9.json')))
UNITS = json.load(open(os.path.join(HERE, 'r9inputs', 'm3a_units_r9.json')))
SENSB = json.load(open(os.path.join(HERE, 'r9inputs', 'sens_r9b.json')))
CAMP = json.load(open(os.path.join(HERE, 'm3a_result_v400.json')))

# ★ THE CAMPAIGN RECORD DOES NOT SAY WHICH INJECTOR MADE IT.  A later campaign
# record in this tree does (`p90_r7_result.json` carries an `injector` block),
# and the absence here is how a validation belonging to a DIFFERENT injector
# came to be offered as evidence for this completeness.  Until the field
# exists, the record is pinned by the one identifier it does carry, so a
# substituted or re-run record cannot pass unnoticed.
CAMPAIGN_INJECTOR = 'inject_vis_v399.py'
CAMPAIGN_STAMP = '2026-09-24T14:34:19Z'
META = json.load(open(os.path.join(HERE, 'archive_meta_v381.json')))['ebs']

OUT, FAIL = [], []


def m(name, val):
    assert name.isalpha(), (
        'a LaTeX macro name may contain letters only: %r' % name)
    OUT.append('\\newcommand{\\%s}{%s}' % (name, val))


def ck(label, cond, detail=''):
    print('  %-66s %s  %s' % (label, 'PASS' if cond else 'FAIL', detail))
    if not cond:
        FAIL.append(label)


# ======================================================================= 1
# WHAT THE INJECTIONS DEPOSIT, AND WHY THE RESPONSE CANNOT BE APPLIED TWICE.
_tau = np.arange(NLAG) - NLAG / 2.0
_W = 0.5 * (1.0 + np.cos(2.0 * math.pi * _tau / NLAG))


def resp(x):
    """Exact delivered amplitude, relative to an unsmoothed channel-centred
    tone of the same flux, in the channel x channels from the carrier."""
    return float((np.sum(_W * np.exp(2j * math.pi * float(x) * _tau / NLAG))
                  / NLAG).real)


def deposited(frac):
    """The injector's own deposition: a linear split between the two
    straddled channels, convolved with the three-point kernel."""
    out = {}
    for k in (-1, 0, 1, 2):
        w = 0.0
        for j, hk in zip((-1, 0, 1), HANN_KERNEL):
            if k - j == 0:
                w += hk * (1.0 - frac)
            elif k - j == 1:
                w += hk * frac
        out[k] = w
    return out


_PH = np.linspace(0.0, 1.0, 2001)[:-1]
_dep_peak = np.array([max(deposited(f).values()) for f in _PH])
_exact_peak = np.array([max(resp(k - f) for k in (-1, 0, 1, 2)) for f in _PH])
DEP_CENTRE = max(deposited(0.0).values())
DEP_EDGE = max(deposited(0.5).values())
EXACT_CENTRE = max(resp(k) for k in (-1, 0, 1, 2))
EXACT_EDGE = max(resp(k - 0.5) for k in (-1, 0, 1, 2))
DEP_MEAN = float(_dep_peak.mean())
EXACT_MEAN = float(_exact_peak.mean())
SHORT_MEAN = 1.0 - DEP_MEAN / EXACT_MEAN          # phase-averaged shortfall
SHORT_EDGE = 1.0 - DEP_EDGE / EXACT_EDGE          # worst, at a boundary

# the phase flatness, measured on the campaign's own tones
_byur = collections.defaultdict(list)
for _t in TONES:
    if not _t['outside'] and _t['snr'] and _t['amp']:
        _byur[(_t['tag'], _t['amp'])].append(_t)
_rel = []
for _k, _v in _byur.items():
    _ref = [t['snr'] / t['amp'] for t in _v if abs(t['sub']) < 0.10]
    if len(_ref) < 2:
        continue
    _r0 = statistics.median(_ref)
    for t in _v:
        _rel.append((abs(t['sub']), (t['snr'] / t['amp']) / _r0))
_rel = [x for x in _rel if x[1] > 0]
PHASE_BINS = [(0.0, 0.1), (0.1, 0.2), (0.2, 0.3), (0.3, 0.4), (0.4, 0.5)]
PHASE_MED = [statistics.median([r for s, r in _rel if lo <= s < hi])
             for lo, hi in PHASE_BINS]
PHASE_FLAT = max(abs(x - 1.0) for x in PHASE_MED)
N_PHASE_TONE = len(_rel)
# and the physical reason it is flat
_exc = [abs(t['dr']) * t['tspan'] / t['cw']
        for t in TONES if not t['outside'] and t['snr'] and t['amp']]
DRIFT_CHAN = statistics.median(_exc)

# ======================================================================= 2
# THE STRATA.  The catalogue's own control-maximum column assigns every
# window; the campaign's own clean control maximum assigns every injected one.
CAT_A = [r for r in CAT if r['search_class'] == 'A']
CAT_B = [r for r in CAT if r['search_class'] == 'B']
UFINE = [u for u in UNITS if u['cls'] == 'fine']
UCOARSE = [u for u in UNITS if u['cls'] == 'coarse']
CLEAN_CTRL = {u['tag']: [g['ctrl_top'] for g in u['rungs']
                         if g['amp'] == 0.75][0] for u in UFINE}
MATCH = SENSB['match']['rows']
assert set(MATCH) == set(CLEAN_CTRL), 'the frozen join and the units disagree'

# the published bin edges nest inside the rule, which is why the rule can be
# applied to the frozen stratification without re-deriving it
BINS = [0.0, 6.0, RULE_SIGMA, 14.0, 1e9]
assert RULE_SIGMA in BINS, RULE_SIGMA
NOISE_BINS = [i for i in range(len(BINS) - 1) if BINS[i + 1] <= RULE_SIGMA]
DISC_BINS = [i for i in range(len(BINS) - 1) if BINS[i] >= RULE_SIGMA]


def binof(c):
    for i in range(len(BINS) - 1):
        if BINS[i] <= c < BINS[i + 1]:
            return i
    raise ValueError(c)


WCAT = [0] * (len(BINS) - 1)
for r in CAT_A:
    WCAT[binof(float(r['ctrl_max_snr']))] += 1
INJ = [[] for _ in range(len(BINS) - 1)]
for tag, v in MATCH.items():
    INJ[binof(v['ctrl_cat'])].append(tag)

BYTAG = collections.defaultdict(list)
for t in TONES:
    if not t['outside']:
        BYTAG[t['tag']].append(t)
AMPS = sorted({t['amp'] for t in TONES if t['amp'] != 20.0})
POSCTRL = max({t['amp'] for t in TONES})


def frac(tags, a, subtract):
    tt = [t for g in tags for t in BYTAG[g] if t['amp'] == a]
    if not tt:
        return None
    if subtract:
        # the star's own leak removed by using the window's own UNINJECTED
        # control maximum: the whole rise with amplitude is that leak
        return sum(1 for t in tt
                   if t['snr'] >= TRIGGER_SIGMA
                   and t['snr'] > CLEAN_CTRL[t['tag']]) / len(tt)
    return sum(t['rec'] for t in tt) / len(tt)


def curve(sel, subtract=False, amps=None):
    amps = AMPS if amps is None else amps
    out = []
    for a in amps:
        acc = wn = 0.0
        for i, tags in enumerate(sel):
            if not tags or not WCAT[i]:
                continue
            f = frac(tags, a, subtract)
            if f is None:
                continue
            acc += WCAT[i] * f
            wn += WCAT[i]
        out.append(acc / wn if wn else 0.0)
    return out


def cross(xs, ys, level=0.9):
    for j in range(1, len(xs)):
        if ys[j - 1] < level <= ys[j]:
            w = (level - ys[j - 1]) / (ys[j] - ys[j - 1])
            return xs[j - 1] + w * (xs[j] - xs[j - 1])
    return None


def p90(bins, subtract=False):
    sel = [tags if i in bins else [] for i, tags in enumerate(INJ)]
    return cross(AMPS, curve(sel, subtract))


def boot(bins, subtract=False, n=1200, seed=23):
    rng = random.Random(seed)
    vals, und = [], 0
    for _ in range(n):
        sel = [[tags[rng.randrange(len(tags))] for _ in tags]
               if (i in bins and tags) else []
               for i, tags in enumerate(INJ)]
        c = cross(AMPS, curve(sel, subtract))
        if c is None:
            und += 1
        else:
            vals.append(c)
    vals.sort()
    return ((vals[int(0.16 * len(vals))] if vals else None),
            (vals[int(0.84 * len(vals))] if vals else None),
            und / float(n))


ALL_BINS = list(range(len(BINS) - 1))
P_BLANKET = p90(ALL_BINS)
P_NOISE = p90(NOISE_BINS)
P_NOISE_SUB = p90(NOISE_BINS, True)
P_DISC = p90(DISC_BINS)
P_DISC_SUB = p90(DISC_BINS, True)
NOISE_LO, NOISE_HI, _ = boot(NOISE_BINS)
_, _, DISC_UNDEF = boot(DISC_BINS)
N_NOISE_WIN = sum(WCAT[i] for i in NOISE_BINS)
N_DISC_WIN = sum(WCAT[i] for i in DISC_BINS)
N_NOISE_INJ = sum(len(INJ[i]) for i in NOISE_BINS)
N_DISC_INJ = sum(len(INJ[i]) for i in DISC_BINS)
_dc = curve([tags if i in DISC_BINS else [] for i, tags in enumerate(INJ)],
            False, AMPS + [POSCTRL])
DISC_TOP_FRAC = _dc[-2]                 # at the top ordinary rung
DISC_POSCTRL_FRAC = _dc[-1]             # at the positive control
_nc = curve([tags if i in NOISE_BINS else [] for i, tags in enumerate(INJ)],
            False, AMPS + [POSCTRL])
NOISE_POSCTRL_FRAC = _nc[-1]
TOP_RUNG = AMPS[-1]
DISC_STARS = []
for r in CAT_A:
    if float(r['ctrl_max_snr']) >= RULE_SIGMA:
        s = {'bet Pic': r'$\beta$~Pictoris',
             'ALMA J153702653-33192492': 'ALMA~J1537$-$3319'}.get(
                 r['star_name'], r['star_name'].replace(' ', '~'))
        if s not in DISC_STARS:
            DISC_STARS.append(s)

# ======================================================================= 3
# THE 21 INDIVIDUAL WINDOWS, AND WHAT THEY DEPEND ON.
BYKEY = collections.defaultdict(list)
for r in CAT_A:
    BYKEY[(r['eb'], int(round(float(r['chanw_Hz']))))].append(r)
INDIV = []
for u in UFINE:
    tag = u['tag']
    eb = tag.rsplit('_spw', 1)[0]
    cand = BYKEY.get((eb, int(round(u['chanw_Hz']))), [])
    assert cand, 'no catalogue row for injected unit %s' % tag
    # the same block and channel width can hold two windows, so the join
    # closes on the control maximum the campaign measured for itself
    r = min(cand, key=lambda c: abs(float(c['ctrl_max_snr'])
                                    - CLEAN_CTRL[tag]))
    sel = [[tag] if tag in tags else [] for tags in INJ]
    INDIV.append(dict(
        tag=tag, star=r['star_name'], band=int(r['band']),
        array=META.get(eb, {}).get('array', '?'),
        chanw_kHz=float(r['chanw_Hz']) / 1e3,
        ctrl=float(r['ctrl_max_snr']),
        p90=cross(AMPS, [frac([tag], a, False) for a in AMPS]),
        p90sub=cross(AMPS, [frac([tag], a, True) for a in AMPS]),
        top=frac([tag], POSCTRL, False)))
RES = [d for d in INDIV if d['p90'] is not None]
IND_LO = min(d['p90'] for d in RES)
IND_HI = max(d['p90'] for d in RES)
IND_MED = statistics.median([d['p90'] for d in RES])


def med_by(key, keyfn, sub=False):
    g = collections.defaultdict(list)
    for d in RES:
        v = d['p90sub'] if sub else d['p90']
        if v is not None:
            g[keyfn(d)].append(v)
    return {k: statistics.median(v) for k, v in g.items()}, \
           {k: len(v) for k, v in g.items()}


BAND_MED, BAND_N = med_by('band', lambda d: d['band'])
ARR_MED, ARR_N = med_by('array', lambda d: d['array'])
ARR_MED_SUB, _ = med_by('array', lambda d: d['array'], sub=True)
CHAN_MED, CHAN_N = med_by('chan', lambda d: ('fine' if d['chanw_kHz'] < 200.0
                                             else 'coarse'))
BAND_SPREAD = max(BAND_MED.values()) - min(BAND_MED.values())
CHAN_SPREAD = abs(CHAN_MED['fine'] - CHAN_MED['coarse'])
ARR_SPREAD = abs(ARR_MED['12m'] - ARR_MED['7m'])
ARR_SPREAD_SUB = abs(ARR_MED_SUB['12m'] - ARR_MED_SUB['7m'])
# the windows carrying the apparent array difference: ACA windows whose
# individual p90 exceeds the stratum value, i.e. the bright-ring ones
ARR_DRIVERS = sorted((d for d in RES
                      if d['array'] == '7m' and d['p90'] > P_NOISE * 1.25),
                     key=lambda d: -d['p90'])
# M7(d): the ACA share of the injected set against its share of Class A
ACA_CAT = sum(1 for r in CAT_A if META.get(r['eb'], {}).get('array') == '7m')
ACA_INJ = sum(1 for d in INDIV if d['array'] == '7m')

# Class B: can the rule be applied at all?
NB_BRIGHT = sum(1 for r in CAT_B if float(r['ctrl_max_snr']) >= RULE_SIGMA)
NB_INJ_BRIGHT = sum(1 for u in UCOARSE
                    if [g['ctrl_top'] for g in u['rungs']
                        if g['amp'] == 0.75][0] >= RULE_SIGMA)

# ---------------------------------------------------------------- report
print('\ndeposition against the exact channel response')
print('  centre  deposited %.4f  exact %.4f' % (DEP_CENTRE, EXACT_CENTRE))
print('  edge    deposited %.4f  exact %.4f  (%.1f per cent short)'
      % (DEP_EDGE, EXACT_EDGE, 100 * SHORT_EDGE))
print('  phase-averaged peak %.4f against %.4f, %.1f per cent short'
      % (DEP_MEAN, EXACT_MEAN, 100 * SHORT_MEAN))
print('  recovered SNR against |sub-channel phase|: %s (%d tones)'
      % (' '.join('%.3f' % x for x in PHASE_MED), N_PHASE_TONE))
print('  median drift excursion %.1f channels per observation' % DRIFT_CHAN)
print('  blanket factor %.4f x deposited peak %.4f = %.3f x nominal trigger'
      % (P_BLANKET, DEP_MEAN, P_BLANKET * DEP_MEAN))
print('\nstrata at %.0f sigma' % RULE_SIGMA)
print('  noise-dominated %d windows, %d injected: P90 = %.3f (68%% %.2f-%.2f)'
      % (N_NOISE_WIN, N_NOISE_INJ, P_NOISE, NOISE_LO, NOISE_HI))
print('  disc-affected   %d windows, %d injected: no 90%% point below %.0fx '
      '(%.3f at %.0fx, %.3f at %.0fx); undefined in %.0f%% of resamples'
      % (N_DISC_WIN, N_DISC_INJ, TOP_RUNG, DISC_TOP_FRAC, TOP_RUNG,
         DISC_POSCTRL_FRAC, POSCTRL, 100 * DISC_UNDEF))
print('  blanket %.3f ; subtracted: noise %.3f, disc %s'
      % (P_BLANKET, P_NOISE_SUB, P_DISC_SUB))
print('  individual: %d of %d resolve, %.2f-%.2f, median %.2f'
      % (len(RES), len(INDIV), IND_LO, IND_HI, IND_MED))
print('  band medians %s ; channel %s ; array %s -> subtracted %s'
      % ({k: round(v, 2) for k, v in sorted(BAND_MED.items())},
         {k: round(v, 2) for k, v in CHAN_MED.items()},
         {k: round(v, 2) for k, v in ARR_MED.items()},
         {k: round(v, 2) for k, v in ARR_MED_SUB.items()}))

# ---------------------------------------------------------------- asserts
print('\nassertions')
ck('T1 the deposition is NOT a delta in one channel: it puts a quarter of '
   'the flux in each neighbour at a channel centre',
   abs(deposited(0.0)[-1] - (0.25 if DRIVE != 1 else 0.0)) < 1e-9
   and abs(deposited(0.0)[1] - 0.25) < 1e-9,
   'neighbours %.3f / %.3f' % (deposited(0.0)[-1], deposited(0.0)[1]))
ck('T2 the deposition UNDER-delivers against the exact response, so the '
   'residual bias is conservative and not optimistic',
   (DEP_MEAN if DRIVE != 2 else EXACT_MEAN * 1.01) < EXACT_MEAN,
   'phase-averaged %.4f against %.4f' % (DEP_MEAN, EXACT_MEAN))
ck('T3 the response is already inside the measured factor: the recovered '
   'peak-channel amplitude at the 90 per cent point is near the trigger',
   1.0 < (P_BLANKET * DEP_MEAN if DRIVE != 3 else 9.0) < 3.0,
   '%.3f x nominal trigger' % (P_BLANKET * DEP_MEAN))
ck('T4 recovered signal-to-noise is flat in sub-channel phase, which is why '
   'the deposition detail cannot matter much',
   (PHASE_FLAT if DRIVE != 4 else 0.5) < 0.02,
   'worst bin departs by %.3f over %d tones' % (PHASE_FLAT, N_PHASE_TONE))
ck('T5 the blanket factor read here is the one the frozen record carries, '
   'so this file cannot disagree with the adopted sensitivity',
   abs(P_BLANKET - (SENSB['stratified']['p90'] if DRIVE != 5
                    else 0.0)) < 5e-4,
   'recomputed %.4f against frozen %.4f'
   % (P_BLANKET, SENSB['stratified']['p90']))
ck('T6 the strata partition the Class A sample, counted two ways',
   N_NOISE_WIN + N_DISC_WIN == len(CAT_A)
   and N_NOISE_INJ + N_DISC_INJ == (len(INDIV) if DRIVE != 6 else 0),
   '%d + %d = %d windows; %d + %d = %d injected'
   % (N_NOISE_WIN, N_DISC_WIN, len(CAT_A), N_NOISE_INJ, N_DISC_INJ,
      len(INDIV)))
ck('T7 the blanket factor is the completeness of NEITHER stratum: it lies '
   'above the noise stratum\'s own interval and below the disc bound',
   (P_BLANKET if DRIVE != 7 else P_NOISE) > NOISE_HI
   and P_DISC is None,
   'blanket %.2f against noise 68%% %.2f-%.2f and a disc bound > %.0f'
   % (P_BLANKET, NOISE_LO, NOISE_HI, TOP_RUNG))
ck('T8 completeness is MEASURED monotonic where it is not already unity: '
   'every stratum recovers everything at the positive control',
   min(NOISE_POSCTRL_FRAC,
       DISC_POSCTRL_FRAC if DRIVE != 8 else 0.0) >= 0.999,
   'noise %.3f, disc %.3f at %.0fx'
   % (NOISE_POSCTRL_FRAC, DISC_POSCTRL_FRAC, POSCTRL))
ck('T9 the apparent array dependence is the bright-ring windows and not the '
   'array: removing the star\'s own leak removes it',
   (ARR_SPREAD if DRIVE != 9 else 0.0) > 3.0 * ARR_SPREAD_SUB,
   '12 m against ACA %.2f before, %.2f after' % (ARR_SPREAD, ARR_SPREAD_SUB))

ck('T10 the campaign record is the one this file describes: it either names '
   'its injector or is pinned by the identifier it does carry',
   (CAMP['injector']['script'] if 'injector' in CAMP else
    CAMP['generated'] if DRIVE != 10 else 'substituted')
   in (CAMPAIGN_INJECTOR, CAMPAIGN_STAMP),
   'named %s, stamped %s'
   % (CAMP.get('injector', {}).get('script', 'nothing'), CAMP['generated']))

print('\nassertions failed: %d %s' % (len(FAIL), FAIL))
if FAIL and DRIVE is None:
    raise SystemExit('strata_v411: %d assertion(s) failed: %s'
                     % (len(FAIL), FAIL))

# ---------------------------------------------------------------- macros
m('InjDepCentre', '%.3f' % DEP_CENTRE)
m('InjDepEdge', '%.3f' % DEP_EDGE)
m('InjDepMean', '%.4f' % DEP_MEAN)
m('InjRespEdge', '%.4f' % EXACT_EDGE)
m('InjRespMean', '%.4f' % EXACT_MEAN)
m('InjShortPct', '%.0f' % (100 * SHORT_MEAN))
m('InjShortEdgePct', '%.0f' % (100 * SHORT_EDGE))
## ★★★ r16, R2b-8: `\InjPeakAtNinety` IS RETIRED, NOT RENAMED, AND THE REASON
## MATTERS.  Its value was `P_BLANKET * DEP_MEAN` = 4.4152 x 0.4375 = 1.93,
## and `P_BLANKET` is the **retired** rank-gated, ring-stratified
## completeness.  Table 4 printed that 1.93 as the "channel response" of the
## **adopted** EIRP_90 factor, where the same quantity is 1.33 -- so a reader
## could take the adopted 3.0287 to be carrying a correction still owing,
## which is exactly the double-counting R2b-8 asked about.  Both halves of the
## adopted factorisation now come from round 620 (`\RpRespFac` 2.29 for the
## response, `\RpMarginNinety` 1.33 for the margin a peak channel needs over
## five sigma), and nothing cites this name.  Emitting it under any name
## invites the same misreading, so it is not emitted; the quantity itself is
## unchanged and recoverable from `P_BLANKET` and `DEP_MEAN`, which are both
## still published.
m('InjPhaseFlatPct', '%.0f' % max(1.0, 100 * PHASE_FLAT))
m('InjNPhaseTone', '%d' % N_PHASE_TONE)
m('InjDriftChan', '%.0f' % DRIFT_CHAN)

m('StrRuleSig', '%.0f' % RULE_SIGMA)
m('StrNNoiseWin', '%d' % N_NOISE_WIN)
m('StrNDiscWin', '%d' % N_DISC_WIN)
m('StrNNoiseInj', '%d' % N_NOISE_INJ)
m('StrNDiscInj', '%d' % N_DISC_INJ)
m('StrMultNoise', '%.2f' % P_NOISE)
m('StrMultNoiseLo', '%.2f' % NOISE_LO)
m('StrMultNoiseHi', '%.2f' % NOISE_HI)
# ★ The blanket factor is NOT emitted under a second name here: it is
# \EirpNinetyMultA and nothing else, because a quantity with two names is how
# this paper has twice ended up printing two values for one thing.
m('StrTopRung', '%.0f' % TOP_RUNG)
m('StrPosCtrl', '%.0f' % POSCTRL)
m('StrDiscTopPct', '%.0f' % (100 * DISC_TOP_FRAC))
m('StrDiscStars', ', '.join(DISC_STARS[:-1]) + ' and ' + DISC_STARS[-1])
m('StrMultNoiseSub', '%.2f' % P_NOISE_SUB)
m('StrNIndiv', '%d' % len(RES))
m('StrNInjWin', '%d' % len(INDIV))
m('StrIndivLo', '%.1f' % IND_LO)
m('StrIndivHi', '%.1f' % IND_HI)
m('StrBandSpread', '%.1f' % BAND_SPREAD)
m('StrChanSpread', '%.1f' % CHAN_SPREAD)
m('StrArrTwelve', '%.1f' % ARR_MED['12m'])
m('StrArrAca', '%.1f' % ARR_MED['7m'])
m('StrArrTwelveSub', '%.1f' % ARR_MED_SUB['12m'])
m('StrArrAcaSub', '%.1f' % ARR_MED_SUB['7m'])
m('StrNArrDriver', '%d' % len(ARR_DRIVERS))
m('StrAcaCatPct', '%.0f' % (100.0 * ACA_CAT / len(CAT_A)))
m('StrAcaInjPct', '%.0f' % (100.0 * ACA_INJ / len(INDIV)))
m('StrNBrightB', '%d' % NB_BRIGHT)
m('StrNInjBrightB', '%d' % NB_INJ_BRIGHT)
m('StrNWinB', '%d' % len(CAT_B))

path = os.path.join(OUTDIR, 'survey_numbers_round65.tex' if DRIVE is None else
                    'survey_numbers_round65_drive%d.tex' % DRIVE)
with open(path, 'w') as fh:
    fh.write('%% GENERATED by strata_v411.py -- do not hand-edit.\n')
    fh.write('\n'.join(sorted(OUT)) + '\n')
print('\nwrote %s (%d macros)' % (os.path.basename(path), len(OUT)))

# ------------------------------------------------- the frozen record others read
REC = dict(
    generated_by='strata_v411.py',
    rule=dict(column='ctrl_max_snr', sigma=RULE_SIGMA,
              disc='>= sigma', noise='< sigma'),
    noise=dict(n_cat=N_NOISE_WIN, n_inj=N_NOISE_INJ, p90=P_NOISE,
               p90_lo=NOISE_LO, p90_hi=NOISE_HI, p90_subtracted=P_NOISE_SUB),
    disc=dict(n_cat=N_DISC_WIN, n_inj=N_DISC_INJ, p90=None,
              bound_lo=TOP_RUNG, bound_adopted=POSCTRL,
              frac_at_top_rung=DISC_TOP_FRAC,
              frac_at_positive_control=DISC_POSCTRL_FRAC,
              stars=DISC_STARS),
    blanket=dict(p90=P_BLANKET, note='the completeness of no window; '
                 'reported beside the strata and named as a blend'),
    response=dict(deposited_centre=DEP_CENTRE, deposited_edge=DEP_EDGE,
                  exact_centre=EXACT_CENTRE, exact_edge=EXACT_EDGE,
                  deposited_phase_mean=DEP_MEAN, exact_phase_mean=EXACT_MEAN,
                  shortfall_phase_mean=SHORT_MEAN, shortfall_edge=SHORT_EDGE,
                  peak_at_ninety=P_BLANKET * DEP_MEAN,
                  phase_flatness=PHASE_FLAT, n_phase_tone=N_PHASE_TONE,
                  drift_channels_median=DRIFT_CHAN),
    class_b=dict(n_bright=NB_BRIGHT, n_injected_bright=NB_INJ_BRIGHT,
                 note='no injected coarse unit has a bright control ring, so '
                      'the rule cannot be applied; the Class B factor stays a '
                      'blend and is declared as one'),
    individual=[{k: d[k] for k in ('tag', 'star', 'band', 'array',
                                   'chanw_kHz', 'ctrl', 'p90', 'p90sub',
                                   'top')} for d in INDIV],
    # ★ the provenance field the campaign record does not carry.  The adopted
    # completeness came from the injector named here; a later reader must not
    # have to reconstruct that from file dates and a driver script.
    provenance=dict(
        campaign='campaign_m3a_v399.py',
        injector='inject_vis_v399.py',
        deposition='linear split between the two straddled channels, '
                   'convolved with the 0.25/0.5/0.25 channel kernel',
        result='m3a_result_v400.json (generated 2026-09-24T14:34:19Z)',
        note='the result predates inject_vis_v401.py and carries no injector '
             'field of its own; this record supplies it.  Any generator '
             'quoting the exact lag-window validation of a LATER injector '
             'alongside this completeness is mis-attributing it.'))
jpath = os.path.join(OUTDIR, 'strata_v411%s.json' % SUF)
json.dump(REC, open(jpath, 'w'), indent=1, sort_keys=True)
print('wrote %s' % os.path.basename(jpath))

# ---------------------------------------------------------------- the figure
if NOFIG:
    raise SystemExit(0)
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
plt.rcParams.update({'pdf.fonttype': 42, 'ps.fonttype': 42,
                     'font.family': 'serif', 'font.serif': ['DejaVu Serif'],
                     'mathtext.fontset': 'dejavuserif'})

fig, (axL, axR) = plt.subplots(1, 2, figsize=(7.3, 3.05))

# (a) the individual windows
MK = {6: 'o', 7: 's', 8: '^', 9: 'D', 10: 'v'}
for d in INDIV:
    x = d['ctrl']
    y = d['p90'] if d['p90'] is not None else TOP_RUNG * 1.14
    fc = 'none' if d['array'] == '7m' else '0.25'
    axL.plot([x], [y], marker=MK.get(d['band'], 'o'), ms=6.5,
             mfc=fc, mec='0.15', mew=1.1, ls='none', zorder=3, alpha=0.85,
             clip_on=False)
    if d['chanw_kHz'] < 200.0:
        axL.plot([x], [y], marker='+', ms=5.0, color='0.0', mew=0.9,
                 ls='none', zorder=4, clip_on=False)
    if d['p90'] is None:
        axL.annotate('', xy=(x, TOP_RUNG * 1.30), xytext=(x, TOP_RUNG * 1.14),
                     arrowprops=dict(arrowstyle='-|>', color='0.15', lw=1.0))
axL.axhline(P_NOISE, color='0.1', lw=1.1)
axL.axhspan(NOISE_LO, NOISE_HI, color='0.1', alpha=0.10, lw=0)
axL.axhline(P_BLANKET, color='0.35', lw=1.0, ls=':')
axL.axvline(RULE_SIGMA, color='0.45', lw=0.9, ls='--')
axL.set_yscale('log')
axL.set_ylim(2.4, TOP_RUNG * 1.5)
axL.set_xscale('log')
axL.set_xlim(4.4, 24.0)
axL.set_xticks([5, 6, 8, 10, 14, 20])
axL.set_xticklabels(['5', '6', '8', '10', '14', '20'])
axL.set_yticks([2.5, 3, 4, 5, 6, 8, 10])
axL.set_yticklabels(['2.5', '3', '4', '5', '6', '8', '10'])
axL.set_xlabel(r'control-ring maximum ($\sigma$)')
axL.set_ylabel(r'$\mathrm{EIRP}_{90}\,/\,P_{\rm trig}$')
axL.text(RULE_SIGMA * 1.06, 2.55, 'disc-affected', fontsize=7.4,
         color='0.35')
axL.text(RULE_SIGMA * 0.95, 2.55, 'noise-dominated', fontsize=7.4,
         color='0.35', ha='right')
axL.text(22.5, P_NOISE * 1.05, r'$%.1f\,P_{\rm trig}$' % P_NOISE,
         fontsize=7.4, ha='right')
axL.text(22.5, P_BLANKET * 1.05, 'single factor', fontsize=7.4,
         color='0.35', ha='right')
_h = [plt.Line2D([], [], ls='none', marker=MK[b], mfc='0.25', mec='0.15',
                 ms=6.0, label='Band %d' % b) for b in sorted(BAND_MED)]
_h += [plt.Line2D([], [], ls='none', marker='o', mfc='none', mec='0.15',
                  ms=6.0, label='ACA 7 m'),
       plt.Line2D([], [], ls='none', marker='+', color='0.0', ms=6.0,
                  label='< 200 kHz')]
axL.legend(handles=_h, fontsize=6.6, loc='upper left', frameon=False,
           handletextpad=0.3, borderpad=0.1, labelspacing=0.25)
axL.set_title('(a) the 21 injected windows', fontsize=8.5, loc='left')

# (b) the recovery curves, with and without the subtraction
xs = AMPS + [POSCTRL]
for bins, lab, col in ((NOISE_BINS, 'noise-dominated', '0.1'),
                       (DISC_BINS, 'disc-affected', '0.55')):
    sel = [tags if i in bins else [] for i, tags in enumerate(INJ)]
    axR.plot(xs, curve(sel, False, xs), '-', color=col, lw=1.6, label=lab)
    axR.plot(xs, curve(sel, True, xs), '--', color=col, lw=1.1)
axR.axhline(0.9, color='0.45', lw=0.8, ls=':')
axR.set_xscale('log')
axR.set_xlim(0.7, POSCTRL * 1.15)
axR.set_ylim(0.0, 1.045)
axR.set_xticks([1, 2, 3, 5, 8, 20])
axR.set_xticklabels(['1', '2', '3', '5', '8', '20'])
axR.set_xlabel(r'injected power $/\,P_{\rm trig}$')
axR.set_ylabel('fraction recovered')
axR.legend(fontsize=7.0, loc='upper left', frameon=False,
           handletextpad=0.5, borderpad=0.1, labelspacing=0.25)
axR.text(POSCTRL * 0.98, 0.915, 'ninety per cent', fontsize=7.0,
         color='0.45', ha='right')
axR.set_title('(b) recovery curves', fontsize=8.5, loc='left')
for ax in (axL, axR):
    for s in ('top', 'right'):
        ax.spines[s].set_visible(False)
    ax.tick_params(labelsize=7.6)
fig.tight_layout(pad=0.4)
# ★★ v4.12 / RULING 1: THE FIGURE IS NO LONGER WRITTEN.  The spatial rank
#    gates no disposition, so it is not charged against the completeness, so
#    there are no strata to draw and `fig:strata` has left the paper.  A
#    figure that is built, deposited and included nowhere is a product nobody
#    can check, and `figorphan` fails on it -- correctly.  The record this
#    generator writes is still read by `pxapply_v411.py` and by `sens_r11.py`
#    (whose regression reproduces the frozen rank-charged x4.4152 out of it),
#    so the generator stays and only the artwork goes.  Set
#    STRATA_FIG=1 to draw it for inspection; it then lands on a name the
#    manuscript cannot include.
if os.environ.get('STRATA_FIG') == '1':
    fpath = os.path.join(OUTDIR, 'figures',
                         'sens_strata_inspect%s.pdf' % SUF)
    fig.savefig(fpath)
    print('wrote figures/%s (inspection only)' % os.path.basename(fpath))
else:
    print('figures/sens_strata.pdf NOT written: fig:strata left the paper '
          'with the strata (Ruling 1)')
