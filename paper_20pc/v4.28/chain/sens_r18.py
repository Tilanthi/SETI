#!/usr/bin/env python3
r"""Round 740.  FOUR THINGS ABOUT THE SENSITIVITY THAT WERE STATED MORE
STRONGLY THAN THEY WERE MEASURED.

Owner: r18-sens.  Writes `survey_numbers_round740.tex` and `sens_r18.json`
and nothing else.  Every value here is a reduction of files already in the
build; no new campaign, no new statistic, no new model.

-------------------------------------------------------------------------
1.  MEASURED SENSITIVITY AND TRANSFERRED SENSITIVITY ARE DIFFERENT CLAIMS.

A window that was injected into has a measured recovery completeness; one
that was not carries the class average, and the right statement of ITS
uncertainty is the observed spread BETWEEN injected windows.  The deposit
already names each window's basis.  What was missing is three things a
reader needs and could not get:

  * which of the SIX systems whose headline window was injected is which
    (the table marks them now; this file emits the count and the names it is
    checked against);
  * what those six windows' OWN measured factors are, since the published
    limit uses the pooled factor even there -- so the reader can see that
    using the window's own value would move them by at most a tenth;
  * the SHAPE of the x0.80-x1.58 spread, which is a full range over 49
    windows whose upper end rests on ONE window: 41 of the 49 lie within a
    tenth of the pooled value and the second largest is x1.11.  A range
    quoted without that reads as a typical uncertainty and is not one.

-------------------------------------------------------------------------
2.  ATMOSPHERIC DECORRELATION: THE MEDIAN IS NOT THE STATEMENT.

The published figures are a median -- 1 per cent over the census, 8 above
400 GHz -- and a baseline-matched median for the blocks with no phase
record.  A median describes no individual limit, and the distribution has a
long tail: the ninetieth percentile is an order of magnitude above the
median in both groups, and on the limits that matter -- each system's own
headline window -- the correction reaches a third.  This file measures the
ninetieth percentile of both groups and of the per-system headline windows,
and NAMES the systems whose headline limit carries more than a tenth, so
that a reader can apply the correction to the exclusions it touches instead
of being told it is small on average.

Nothing is folded into any limit: the limits stay nominal, and the word is
now in the paper.

-------------------------------------------------------------------------
3.  THE SMEARING CORRECTION IS NOT THE RIGHT FUNCTIONAL FORM, AND IT ERRS
    THE SAFE WAY.

Every limit is divided by eta = sinc(pi*Delta/2), the retained amplitude of
a carrier sweeping Delta channels within one integration.  That form belongs
to a search whose spectral resolution is set by the integration itself, so
that a sweep destroys coherence inside the transform.  ALMA's channels are
some 10^5 times wider than 1/tau, so the sweep does not decohere anything:
it redistributes the carrier's dwell time across the delivered channel
response, and the retained amplitude is the dwell-time average of that
response.  That is arithmetic on a response this build already computes and
validates against five documented ALMA numbers (`cresp_v401.py`).

Measured that way the loss is far smaller than the applied one -- a factor
1.05 against 1.53 in the worst window -- so the thirteen limits concerned
are conservative, not optimistic, and nothing has to move.  The response
model is re-derived here from the lag window and ASSERTED against
`cresp_v401.json` row for row, so this is the same validated response and
not a second one.  Online channel averaging is carried for completeness:
it makes the response broader and the loss smaller still, and none of the
thirteen windows is an averaged one.

-------------------------------------------------------------------------
4.  THE OFF-AXIS BEAM COSTS A FACTOR, NOT A PERCENTAGE.

The primary-beam response A at the star's offset divides into every limit,
so its cost is 1/A -- a factor of 4.3 in the worst window.  The paper
reports "23.2 per cent" in that sentence, which is a different quantity
altogether (the cost of adopting the observatory's documented beamwidth in
place of the pipeline's), and the two numbers 0.2308 and 23.2 are a
coincidence of digits that has already misled a reader.

-------------------------------------------------------------------------
    python3 sens_r18.py              # macros + json
    python3 sens_r18.py --drive N    # perturbation N (see DRIVES)
    python3 sens_r18.py --selftest   # run every drive, require a refusal

DRIVES (each breaks one thing and must make exactly one check FAIL):
  1  the deposited smearing column is perturbed            -> X1
  2  the injected-window join is made many-to-one          -> X2
  3  the response table is built from the wrong taper      -> X3, X4
  4  the measured-group decorrelation median is shifted    -> X6
  5  the two decorrelation groups are swapped              -> X7
  6  a system is named as strongly corrected when it is not-> X8
  7  a system's basis is flipped to injected               -> X9, X2
  8  the dispersion is narrowed inside the calibration     -> X10
  9  the beam factor is taken at the median response       -> X11
 10  the swept average is replaced by the sinc form        -> X5
"""
import collections
import csv
import glob
import json
import math
import os
import re
import statistics as st
import subprocess
import sys

import numpy as np

ROUND = 740
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

DRIVE = 0
if '--drive' in sys.argv:
    DRIVE = int(sys.argv[sys.argv.index('--drive') + 1])
# D36: the suffix follows the FLAG, not the perturbation, so a driven run can
# never write a path production reads.
SUF = '' if '--drive' not in sys.argv else '_drive%d' % DRIVE
OUT = os.path.join(HERE, 'survey_numbers_round740%s.tex' % SUF)
OUTJSON = os.path.join(HERE, 'sens_r18%s.json' % SUF)

#: drive -> the check it must break.  A drive that breaks nothing, or breaks
#: a different check, is a drive that proves nothing.
DRIVES = {1: 'X1', 2: 'X2', 3: 'X3', 4: 'X6', 5: 'X7', 6: 'X8',
          7: 'X9', 8: 'X10', 9: 'X11', 10: 'X5', 11: 'X7', 12: 'X12',
          13: 'X1', 14: 'X13', 15: 'X14'}

if '--selftest' in sys.argv:
    bad = []
    for d, want in sorted(DRIVES.items()):
        r = subprocess.run([sys.executable, os.path.abspath(__file__),
                            '--drive', str(d)], cwd=HERE,
                           capture_output=True, text=True)
        got = [ln.split()[0] for ln in (r.stdout + r.stderr).splitlines()
               if ' FAIL ' in ln]
        ok = r.returncode != 0 and want in got
        print('drive %-3d must break %-4s -> %s%s'
              % (d, want, 'FIRES' if ok else 'DID NOT FIRE',
                 '' if ok else ' (broke %s, rc=%d)' % (got or 'nothing',
                                                       r.returncode)))
        if not ok:
            bad.append(d)
    for f in os.listdir(HERE):
        if f.startswith(('survey_numbers_round740_drive', 'sens_r18_drive')):
            os.remove(os.path.join(HERE, f))
    print('sens_r18 selftest: %d drive(s) failed to fire' % len(bad))
    sys.exit(1 if bad else 0)

FAIL = []


def ck(name, cond, detail=''):
    print('  %-76s %s  %s' % (name[:76], 'PASS' if cond else 'FAIL', detail))
    if not cond:
        FAIL.append(name)


LINES = ['%% GENERATED by sens_r18.py (round %d) -- do not hand-edit.\n'
         % ROUND]


def m(name, val):
    # a LaTeX macro name may contain letters only
    assert name.isalpha(), 'macro names carry letters only: %r' % name
    LINES.append('\\newcommand{\\%s}{%s}\n' % (name, val))


import adopted_e90 as ae                                      # noqa: E402
import decor_r13 as dc                                        # noqa: E402
import respint_r20 as ri                                      # noqa: E402
import star_alias as sa                                       # noqa: E402


def texval(name):
    v = ae._texval(name, HERE)
    assert v is not None, 'macro \\%s is not generated anywhere' % name
    return v


def texnum(name):
    return float(texval(name).replace('\\,', '').replace(',', ''))


def pct90(v):
    """The ninetieth percentile of a sample, by the nearest-rank rule.

    Deliberately the same rule `smear_r15.py` uses on the drift draw --
    sorted[int(0.9*n)] -- so that two percentiles in one paper are the same
    construction.  n is never small here (the smallest group is 61).
    """
    s = sorted(v)
    return s[min(len(s) - 1, int(0.90 * len(s)))]


def sinc(x):
    return math.sin(x) / x if x else 1.0


def sci_int(x):
    """A round order of magnitude, as LaTeX: 9.2e4 -> 9\\times10^{4}."""
    e = int(math.floor(math.log10(abs(x))))
    return r'%.0f\times10^{%d}' % (x / 10.0 ** e, e)


print('sens_r18 round %d%s' % (ROUND, '' if not DRIVE else ' (drive %d)'
                               % DRIVE))

# ======================================================================
# INPUTS
# ======================================================================
CAT = list(csv.DictReader(open(os.path.join(
    HERE, 'per_target_results_v3.99.csv'))))
SENS = json.load(open(os.path.join(HERE, 'sens_r11.json')))
SM = json.load(open(os.path.join(HERE, 'smear_r15.json')))
CRESP = json.load(open(os.path.join(HERE, 'cresp_v401.json')))
TONES = json.load(open(os.path.join(HERE, 'r9inputs', 'm3a_tones_r9.json')))
UNITS = json.load(open(os.path.join(HERE, 'r9inputs', 'm3a_units_r9.json')))
NEW = json.load(open(os.path.join(HERE, 'r11inputs', 'm3a_r11.json')))
GEOM = json.load(open(os.path.join(
    HERE, 'r11inputs', 'window_geometry_r11.json')))['windows']
PBF = list(csv.DictReader(open(os.path.join(HERE, 'pb_atten_fwhm_r11.csv'))))

P90 = SENS['p90']
E90 = ae.per_window(CAT, HERE)

# ★ The best window is the best ELIGIBLE window: one wholly inside the
# attribution mask constrains nothing (Sec. \ref{sec:lines}).  One rule, in
# `adopted_e90`, for every generator that forms a per-system limit.
BEST = {}
for r in CAT:
    if r['search_class'] != 'A' or not ae.limit_eligible(r, HERE):
        continue
    s, v = r['system_id'], E90[id(r)]
    if s not in BEST or v < BEST[s][0]:
        BEST[s] = (v, r)
NSYS = len(BEST)
print('  %d census windows, %d Class A systems, pooled factor %.4f'
      % (len(CAT), NSYS, P90))

# ======================================================================
# 1  THE SWEEP PER WINDOW, RECOMPUTED FROM THE CATALOGUE
# ======================================================================
# Delta is the number of channels a carrier at the ninetieth percentile of
# the window's own drift draw crosses during one integration.  It is
# recomputed here from the catalogue's own drift ceiling and channel width
# and the integration length the smearing record carries, and the sinc of it
# is required to reproduce the DEPOSITED factor on every row -- so the
# response-matched comparison below is against the factor the paper applies
# and not against a re-derivation of it that might have drifted.
Q90 = SM['q90']
BYKEY = {ae.smear_key(r): r for r in CAT}
assert len(BYKEY) == len(CAT), 'the window key is not unique'
WIN = []
_worst = 0.0
for k, v in SM['eta'].items():
    r = BYKEY[k]
    cw = float(r['chanw_Hz'])
    delta = Q90 * float(r['drift_max_Hz_s']) * v['dt'] / cw
    dep = float(r['eta_smear_adopted'])
    if DRIVE == 1 and not WIN:
        dep *= 1.05
    if DRIVE == 13:
        # the deposit carrying the transform-limited form: the retention
        # applied to the limits and the one reported would then part company
        dep = sinc(math.pi * delta / 2.0)
    # the deposited column carries ten significant figures, so that is the
    # precision the identity can be asserted at and no tighter
    _worst = max(_worst, abs(ri.eta(delta, int(r['n_chan_avg'])) / dep
                             - 1.0))
    WIN.append(dict(key=k, row=r, delta=delta, eta=dep,
                    navg=int(r['n_chan_avg']), cls=r['search_class'],
                    basis=r['eta_smear_basis'], inj=v['injected'],
                    dt=v['dt']))
ck('X1 the sweep recomputed from the catalogue, integrated through the '
   'delivered channel response, reproduces the smearing factor the deposit '
   'carries on every window -- so the factor applied to the limits is this '
   'form and not the transform-limited one',
   _worst < 1e-9, 'worst disagreement %.2g over %d windows'
   % (_worst, len(WIN)))

# ★★★ THE COMPARISON SET IS DEFINED BY THE DISPLACEMENT AND NOT BY THE
# APPLIED FACTOR.  It used to be "the windows whose applied factor exceeds
# 1.01", which selected the 13 windows the sinc form penalised by more than a
# per cent.  With the integrated response applied, that rule would select the
# 9 windows the RESPONSE penalises by more than a per cent and then compare
# the response factor with itself: a check that cannot fail.  So the set is
# the windows where the two forms differ by more than a per cent -- the same
# 13 -- which is a statement about the sweep and not about the choice.
AFF = sorted([w for w in WIN
              if 1.0 / sinc(math.pi * w['delta'] / 2.0) > 1.01],
             key=lambda w: -w['delta'])
N_AFF = len(AFF)
N_APP = sum(1 for w in WIN if 1.0 / w['eta'] > 1.01)

# ======================================================================
# 2  THE INJECTED SET, JOINED INDEPENDENTLY OF THE DEPOSIT
# ======================================================================
# The campaign record names each injected window by a tag; the deposit
# carries a `p90_basis` column that says `injected`.  Those are two routes
# to the same set, so they are required to agree exactly -- one-to-one, 49
# rows -- which is the only evidence that the per-window factors read below
# belong to the windows they are attributed to.  The join is on POSITION
# (block, lower edge, channel width) and never on a star name.
_TW = collections.defaultdict(set)
for t in TONES:
    _TW[t['tag']].add((round(min(t['fsl'], t['fsh']), 6), round(t['cw'], 1)))
CIX = collections.defaultdict(list)
for r in CAT:
    CIX[(r['eb'], round(min(float(r['flo_GHz']), float(r['fhi_GHz'])), 6),
         round(float(r['chanw_Hz']), 1))].append(r)
INJ = {}
_unres = []
for u in [x for x in UNITS if x['cls'] == 'fine']:
    g = _TW.get(u['tag'], set())
    if len(g) != 1:
        _unres.append((u['tag'], 'ambiguous tone window'))
        continue
    lo, cw = next(iter(g))
    c = CIX.get((u['eb'], lo, cw), [])
    if len(c) == 1:
        INJ[u['tag']] = c[0]
    else:
        _unres.append((u['tag'], 'catalogue candidates %d' % len(c)))
for u in NEW['units']:
    c = CIX.get((u['eb'], round(u['cat_flo_GHz'], 6),
                 round(u['chanw_Hz'], 1)), [])
    if len(c) == 1:
        INJ[u['tag']] = c[0]
    else:
        _unres.append((u['tag'], 'catalogue candidates %d' % len(c)))
if DRIVE == 2:
    INJ[list(INJ)[0]] = INJ[list(INJ)[1]]


_dep_inj = [r for r in CAT if r['p90_basis'] == 'injected']
_ids = [id(v) for v in INJ.values()]
ck('X2 the campaign record and the deposit name the same injected windows, '
   'one tag to one row, with nothing unresolved',
   not _unres and len(set(_ids)) == len(INJ) == len(_dep_inj)
   == SENS['n_injected']
   and {id(r) for r in _dep_inj} == set(_ids),
   '%d tags, %d distinct rows, %d flagged in the deposit, record says %d; '
   'unresolved %s' % (len(INJ), len(set(_ids)), len(_dep_inj),
                      SENS['n_injected'], _unres))

# each injected window's OWN ninety per cent point, as a ratio to the pooled
FAC = {t: SENS['per_window'][t]['trig'] / P90 for t in INJ}
RAT = sorted(FAC.values())
DISP_LO, DISP_HI = RAT[0], RAT[-1]
if DRIVE == 8:
    DISP_LO, DISP_HI = 0.95, 1.05
N_TENTH = sum(1 for x in RAT if 0.9 <= x <= 1.1)
CAL_LO, CAL_HI = SENS['budget']['factor_lo'], SENS['budget']['factor_hi']
ck('X10 the window-to-window dispersion reproduces the published range and '
   'is wider than the calibration interval, so the two are not '
   'interchangeable',
   abs(DISP_LO - texnum('SmcDispLo')) < 0.005
   and abs(DISP_HI - texnum('SmcDispHi')) < 0.005
   and DISP_LO < CAL_LO and DISP_HI > CAL_HI,
   'x%.3f-x%.3f against the published x%.2f-x%.2f and the calibration '
   'x%.3f-x%.3f' % (DISP_LO, DISP_HI, texnum('SmcDispLo'),
                    texnum('SmcDispHi'), CAL_LO, CAL_HI))

# ---- the systems whose headline window was injected
TAG_OF = {id(r): t for t, r in INJ.items()}
MEAS_SYS, EST_SYS = [], []
for s, (v, r) in BEST.items():
    (MEAS_SYS if r['p90_basis'] == 'injected' else EST_SYS).append(s)
if DRIVE == 7:
    # the count of measured systems parts from the deposit's own flags
    MEAS_SYS.pop()
OWN = sorted((FAC[TAG_OF[id(BEST[s][1])]], s) for s in MEAS_SYS)
OWN_LO, OWN_HI = (OWN[0][0], OWN[-1][0]) if OWN else (1.0, 1.0)
OWN_DEV = max(abs(x - 1.0) for x, _ in OWN) if OWN else 0.0
ck('X9 the systems whose headline limit is measured are exactly the systems '
   'whose best window the deposit flags as injected, and the count is the '
   'published one',
   len(MEAS_SYS) == int(texnum('SmcNMeasSys'))
   and len(EST_SYS) == int(texnum('SmcNEstSys'))
   and len(MEAS_SYS) + len(EST_SYS) == NSYS
   and all(id(BEST[s][1]) in TAG_OF for s in MEAS_SYS),
   '%d measured + %d estimated = %d systems, published %s + %s'
   % (len(MEAS_SYS), len(EST_SYS), NSYS, texval('SmcNMeasSys'),
      texval('SmcNEstSys')))
print('     measured systems: %s'
      % ', '.join('%s (x%.3f)' % (sa.designation(s), f) for f, s in OWN))

# ---- X15: AND THE DENOMINATOR THE PROSE PUTS THEM OVER
# ★★★★ B1 (round 26).  X9 ABOVE PINS THE RIGHT FACT AND THE PAPER WAS STILL
# WRONG ON THE PAGE.  It asserts \SmcNMeasSys + \SmcNEstSys == NSYS, with
# NSYS the systems that CARRY A LIMIT -- 6 + 54 == 60, true -- and it passed
# while three prose sites, one of them in the Conclusions two sentences from a
# correct "24 of the 60", divided those same two numerators by \NSysClassA =
# 61, the count of systems the search COVERS.  A reader subtracts 6 from 61
# and the paper is wrong.  Nothing in the build pinned WHICH DENOMINATOR the
# prose puts them over, so the one check that knew the population was 60 could
# not see the sentence that said 61.  This clause reads every file the
# manuscript typesets and requires that wherever either numerator is printed
# over a denominator, that denominator's own value equals their sum.  It pins
# the relation, not the macro name and not today's 60: rename the population
# or change it and the clause still holds.
_NUM = ('SmcNMeasSys', 'SmcNEstSys')
_PROSE = sorted(glob.glob(os.path.join(HERE, 'sections', '*.tex'))
                + glob.glob(os.path.join(HERE, 'tab_*.tex')))
_DEN = re.compile(r'\\(?:%s)\{\}(?:[^\\]{0,40}?)\\([A-Za-z]+)\{\}'
                  % '|'.join(_NUM))
_densite, _denbad = [], []
for _f in _PROSE:
    _t = ' '.join(open(_f, errors='ignore').read().split())
    for _mm in _DEN.finditer(_t):
        _nm = _mm.group(1)
        _v = ae._texval(_nm, HERE)
        _densite.append((os.path.basename(_f), _nm, _v))
if DRIVE == 16:
    # the denominator of the population the search covers, which is what the
    # three shipped sites used
    _densite.append(('05_results.tex', 'NSysClassA',
                     ae._texval('NSysClassA', HERE)))
for _f, _nm, _v in _densite:
    try:
        _iv = int(str(_v).replace(',', ''))
    except (TypeError, ValueError):
        _denbad.append((_f, _nm, _v, 'not an integer'))
        continue
    if _iv != len(MEAS_SYS) + len(EST_SYS):
        _denbad.append((_f, _nm, _iv, 'is not %d'
                        % (len(MEAS_SYS) + len(EST_SYS))))
ck('X15 wherever the measured and transferred system counts are printed '
   'over a denominator, that denominator is the population they sum to and '
   'not the population the search covers',
   not _denbad,
   '%d site(s) checked: %s; %s'
   % (len(_densite),
      ', '.join('%s/\\%s=%s' % x for x in _densite) or 'none',
      'all over %d' % (len(MEAS_SYS) + len(EST_SYS)) if not _denbad
      else 'WRONG: %r' % (_denbad,)))

# ======================================================================
# 3  DECORRELATION: BOTH GROUPS, MEDIAN AND NINETIETH PERCENTILE
# ======================================================================
# ★★★ THE MATCHING RULE AND THE PER-WINDOW CORRECTION NOW LIVE IN
# `decor_r13.py`, which already owned the physics.  They moved there because
# Table F1 carries each system's own decorrelation factor as a column, so two
# generators need the value; a second copy of the rule in the table generator
# is how one quantity acquires two values.
MATCH = dc.Matcher(HERE)
BLK = MATCH.blocks


def bmax(eb):
    return MATCH.bmax(eb)


def correction(row):
    return MATCH.correction(row)


BL_MATCH = dc.BL_MATCH

D_MEAS, D_UNM, D_UNM_HI, D_NONE = [], [], [], []
for r in CAT:
    o, basis, hi = correction(r)
    if basis == 'measured':
        D_MEAS.append(o)
    elif basis == 'matched':
        D_UNM.append(o)
        D_UNM_HI.append(hi)
    else:
        D_NONE.append(r)
if DRIVE == 5:
    D_MEAS, D_UNM = D_UNM, D_MEAS
if DRIVE == 4:
    D_MEAS = [x * 4.0 for x in D_MEAS]
if DRIVE == 11:
    D_MEAS = [st.median(D_MEAS)] * len(D_MEAS)

DEC_MED, DEC_HI = st.median(D_MEAS), pct90(D_MEAS)
UNM_MED, UNM_COND = st.median(D_UNM), st.median(D_UNM_HI)
ck('X6 the measured-group median, the baseline-matched median and the '
   'matched ninetieth-percentile coherence all reproduce the figures the '
   'paper publishes, so this is the published measurement and not a second '
   'one',
   abs(100 * DEC_MED - texnum('SensDecorPct')) < 0.5
   and abs(100 * UNM_MED - texnum('RpDecMatchMed')) < 0.1
   and abs(100 * UNM_COND - texnum('RpDecMatchHi')) < 0.5,
   'measured median %.2f per cent against the published %s; matched median '
   '%.2f against %s; matched ninetieth-percentile coherence %.1f against %s'
   % (100 * DEC_MED, texval('SensDecorPct'), 100 * UNM_MED,
      texval('RpDecMatchMed'), 100 * UNM_COND, texval('RpDecMatchHi')))
# ★ THE TWO GROUPS' SPREADS ARE NOT THE SAME CONSTRUCTION, AND A SINGLE
# "ninetieth percentile" FOR BOTH WOULD BE A FICTION.  Where the record
# exists the ninetieth percentile is of the measured corrections.  Where it
# does not, every window is given the MEDIAN coherence of its matched peers,
# so that estimate has no tail of its own: the ninetieth percentile of it
# (9 per cent) is smaller than the measured group's (11) while its median is
# larger, which is an artefact of the estimator and not a statement about
# those blocks.  What can honestly be said for them is the conditional
# figure above.  So: a tail in the measured group, a higher median in the
# unmeasured one, and the estimator's own narrowness asserted rather than
# papered over.
ck('X7 the measured correction has a long tail, the blocks with no record '
   'have the higher median as their baselines imply, and the matched '
   'estimate is narrower than the measured spread because it is a median '
   'over peers',
   DEC_HI > 5 * DEC_MED and UNM_MED > DEC_MED
   and pct90(D_UNM) < DEC_HI and UNM_COND > DEC_HI,
   'with a record: median %.2f, ninetieth %.1f per cent (%d windows); '
   'without: median %.2f, ninetieth %.1f of a median-coherence estimate, '
   '%.1f conditional (%d windows)'
   % (100 * DEC_MED, 100 * DEC_HI, len(D_MEAS), 100 * UNM_MED,
      100 * pct90(D_UNM), 100 * UNM_COND, len(D_UNM)))

# ---- the limits a reader actually uses: one headline window per system
SYSD, NOREC = [], []
for s, (v, r) in BEST.items():
    o, basis, _hi = correction(r)
    if o is None:
        NOREC.append(s)
    else:
        SYSD.append((o, basis, s, v))
SYSD.sort()
SYS_MED = st.median([o for o, _, _, _ in SYSD])
SYS_HI = pct90([o for o, _, _, _ in SYSD])
BIG_PCT = 0.10
BIG = sorted([(o, s, v) for o, _, s, v in SYSD if o > BIG_PCT],
             key=lambda x: x[2])
if DRIVE == 6:
    BIG = BIG + [(0.01, SYSD[0][2], SYSD[0][3])]
_names = [sa.designation(s).replace(' ', '~') for _, s, _ in BIG]
ck('X8 every system named as carrying more than a tenth does carry more '
   'than a tenth, and no system that does is left unnamed',
   all(o > BIG_PCT for o, _, _ in BIG)
   and len(BIG) == sum(1 for o, _, _, _ in SYSD if o > BIG_PCT),
   '%d named of %d systems with a correction at all (%d have no baseline '
   'record to match on)' % (len(BIG), len(SYSD), len(NOREC)))
# ★ THE DEEPEST LIMITS ARE THE ONES THE PAPER LEANS ON, so the correction on
# them is reported separately rather than hidden inside a median -- and the
# ten are the ten deepest OF ALL, not the ten deepest that happen to carry an
# estimate.  Taking them from `SYSD` would silently drop the one system that
# has no estimate at all, which is itself one of the ten, and the sentence
# "of the ten deepest" would then be true of nine.
_byval = sorted(BEST.items(), key=lambda kv: kv[1][0])[:10]
_corr = {s: o for o, _b, s, _v in SYSD}
DEEP = [(_corr[s], 'measured' if r['eb'] in BLK else 'matched', s, v)
        for s, (v, r) in _byval if s in _corr]
DEEP_NOREC = [s for s, _ in _byval if s not in _corr]
if DRIVE == 12:
    # the ten deepest taken over the systems that carry an estimate, which
    # is how the set loses the one system that has none
    DEEP = sorted(SYSD, key=lambda x: x[3])[:10]
    DEEP_NOREC = []
DEEP_BIG = [x for x in DEEP if x[0] > 0.05]
print('     per-system headline correction: median %.1f per cent, '
      'ninetieth %.1f, largest %.1f (%s)'
      % (100 * SYS_MED, 100 * SYS_HI, 100 * SYSD[-1][0],
         sa.designation(SYSD[-1][2])))
print('     of the ten deepest systems, %d carry more than five per cent: %s'
      '; %d carry no estimate at all (%s)'
      % (len(DEEP_BIG), ', '.join('%s %.0f per cent'
                                  % (sa.designation(x[2]), 100 * x[0])
                                  for x in DEEP_BIG) or 'none',
         len(DEEP_NOREC),
         ', '.join(sa.designation(s) for s in DEEP_NOREC) or 'none'))
ck('X12 every system named as among the ten deepest and strongly corrected '
   'is one of the ten deepest limits in the survey, and the systems with no '
   'estimate at all are counted there rather than dropped out of the set',
   len(DEEP) + len(DEEP_NOREC) == 10
   and all(x[3] <= sorted(v for v, _ in BEST.values())[9] for x in DEEP)
   and set(DEEP_NOREC) <= set(NOREC),
   '%d of the ten deepest carry an estimate, %d do not' % (len(DEEP),
                                                           len(DEEP_NOREC)))

# ======================================================================
# 4  THE SWEPT TONE THROUGH THE ACTUAL CHANNEL RESPONSE
# ======================================================================
# ★★★ THE INTEGRATION HAS MOVED TO `respint_r20.py`, which is the one
# implementation of it in this build and the one `smear_r15.py` applies to
# every limit.  It used to live here while the limits were divided by
# sinc(pi*Delta/2), so the paper reported one form and applied another.  What
# is left here is the COMPARISON: the response is still asserted against
# `cresp_v401.json` row for row, the two documented spectral resolutions are
# still reproduced, and the transform-limited form is still required to be
# the more severe of the two in every window where they differ.
if DRIVE == 3:
    # the response table built from the wrong taper
    ri._WINDOW['hann'] = ri._WINDOW['unif']
    ri._TAB.clear()
    ri._ETACACHE.clear()
    ri._ETATAB.clear()
    ri._VALIDATED.discard(HERE)
try:
    _rho_dev, FW_U, FW_H, _npair = ri.validate(HERE)
except AssertionError as _exc:
    _rho_dev, FW_U, FW_H, _npair = 1.0, float('nan'), float('nan'), 0
ck('X3 the channel response the applied retention is integrated through is '
   'the response cresp_v401.py validated, at every sub-channel phase and '
   'every averaging factor',
   _rho_dev < 1e-6 and _npair > 100,
   'worst departure %.2g over %d phase/averaging pairs' % (_rho_dev, _npair))
ck('X4 and it reproduces the two spectral resolutions the observatory '
   'documents: 1.2 channels unsmoothed, 2.0 with the default Hanning',
   abs(FW_U - texnum('CrFwhmUnif')) < 0.02
   and abs(FW_H - texnum('CrFwhmHann')) < 0.01,
   'unsmoothed %.3f against %s, Hanning %.3f against %s'
   % (FW_U, texval('CrFwhmUnif'), FW_H, texval('CrFwhmHann')))


def eta_resp(delta, navg=1):
    """The applied retention, and the plain response for the record."""
    if DRIVE == 10:
        # the comparison made optimistic: a form MORE severe than the applied
        # one, so the direction X5 asserts is genuinely reversed
        return 0.9 * sinc(math.pi * delta / 2.0), 1.0
    return ri.eta(delta, navg), 1.0


# ---- the comparison, window by window, over the windows the two forms part
RESP = []
for w in AFF:
    e_r, _ = eta_resp(w['delta'], w['navg'])
    e_s = sinc(math.pi * w['delta'] / 2.0)
    RESP.append(dict(key=w['key'], star=w['row']['star_name'],
                     sid=w['row']['system_id'], delta=w['delta'],
                     navg=w['navg'], eta_sinc=e_s, eta_resp=e_r,
                     eta_applied=w['eta'],
                     fac_sinc=1.0 / e_s, fac_resp=1.0 / e_r))
RESP.sort(key=lambda d: -d['fac_sinc'])
_opt = [d for d in RESP if d['eta_resp'] < d['eta_sinc'] - 1e-9]
# ★ AND THE APPLIED RETENTION IS THE INTEGRATED ONE, which is what makes the
# direction a statement about this paper rather than about two formulae.  X1
# already ties the deposit to `respint_r20.eta`; this clause ties the window
# the comparison is quoted from to the deposit as well, so the sentence
# "the factor applied is the integrated response" cannot be printed beside a
# deposit that carries the other form.
_dep = [d for d in RESP if abs(d['eta_applied'] / d['eta_resp'] - 1.0) > 1e-9]
ck('X5 the retention applied to every limit is the integrated response, and '
   'the transform-limited sinc form is the more severe of the two in every '
   'window where they part -- so the correction that is applied is the '
   'smaller one and is not an upper bound on the loss',
   not _opt and not _dep and N_AFF > 0,
   '%d windows compared, the sinc form more severe in %d, worst applied '
   'factor %.3f against a transform-limited %.3f; %d windows whose deposit '
   'does not carry the applied form'
   % (N_AFF, N_AFF - len(_opt), RESP[0]['fac_resp'], RESP[0]['fac_sinc'],
      len(_dep)))
OVER_PCT = 100.0 * (RESP[0]['fac_sinc'] / RESP[0]['fac_resp'] - 1.0)
# ★ WHY THE SINC FORM DOES NOT APPLY HERE, AS A NUMBER RATHER THAN AN
# ARGUMENT: a sweep decoheres a transform only when the spectral resolution
# is the reciprocal of the integration.  The least favourable of the
# affected windows has a channel this many times wider than 1/tau, so the
# carrier is monochromatic over any one transform and the sweep can only
# move its dwell time between channels.
CHAN_TAU = min(float(d_['row']['chanw_Hz']) * d_['dt']
               for d_ in AFF)
N_AVG_A = sum(1 for w in WIN if w['cls'] == 'A' and w['navg'] > 1)
N_AVG_AFF = sum(1 for d in RESP if d['navg'] > 1)
print('     worst window: Delta %.3f channels, applied x%.3f, '
      'transform-limited x%.3f (%.0f per cent more)'
      % (RESP[0]['delta'], RESP[0]['fac_resp'], RESP[0]['fac_sinc'],
         OVER_PCT))
print('     online channel averaging: %d Class A windows, %d of the %d '
      'affected' % (N_AVG_A, N_AVG_AFF, N_AFF))

# ---- WHAT THE TRANSFORM-LIMITED FORM WOULD HAVE COST, for the record.
# The integrated response is what the build applies, so this is now the
# counterfactual and not the proposal: it is kept because it is the size of
# the choice, and because Sec. 5.1 says the net bias on a limit runs both
# ways and this is the term that runs against the decorrelation one.
ETA_S = {}
for w in WIN:
    if 1.0 / sinc(math.pi * w['delta'] / 2.0) > 1.01 and DRIVE != 14:
        ETA_S[w['key']] = sinc(math.pi * w['delta'] / 2.0)
    else:
        # drive 14: the alternative form made identical to the applied one,
        # so the comparison would be a formality
        ETA_S[w['key']] = w['eta']
E_S = ae.per_window(CAT, HERE, smear=ETA_S)
_b_now = sorted(v for v, _ in BEST.values())
_best_s = {}
for r in CAT:
    if r['search_class'] != 'A':
        continue
    s_, v = r['system_id'], E_S[id(r)]
    if s_ not in _best_s or v < _best_s[s_]:
        _best_s[s_] = v
_b_sinc = sorted(_best_s.values())
IF_SINC = dict(
    n_1e15_applied=sum(1 for v in _b_now if v <= 1e15),
    n_1e15_sinc=sum(1 for v in _b_sinc if v <= 1e15),
    sys_med_applied=st.median(_b_now), sys_med_sinc=st.median(_b_sinc),
    win_lo_applied=min(E90[id(r)] for r in CAT if r['search_class'] == 'A'),
    win_lo_sinc=min(E_S[id(r)] for r in CAT if r['search_class'] == 'A'),
    moved=[dict(sid=s_, applied=v, sinc=_best_s[s_])
           for s_, (v, _) in BEST.items()
           if abs(_best_s[s_] / v - 1.0) > 1e-9])
# ★ AND THE CHOICE IS MATERIAL, which is asserted rather than asserted of:
# a comparison between two forms that moved nothing would not be worth a
# sentence in the paper, and the one number the referee's point turns on is
# the count of systems reaching 1e15 W.
ck('X13 the choice of retention is material: the transform-limited form '
   'would give a different count of systems reaching 1e15 W and a '
   'shallower deepest window, so the comparison is not a formality',
   IF_SINC['n_1e15_sinc'] != IF_SINC['n_1e15_applied']
   and IF_SINC['win_lo_sinc'] > IF_SINC['win_lo_applied'] * 1.01,
   'applied: %d systems at 1e15 W, deepest window %.3e W; transform-limited: '
   '%d and %.3e W; %d system limits differ'
   % (IF_SINC['n_1e15_applied'], IF_SINC['win_lo_applied'],
      IF_SINC['n_1e15_sinc'], IF_SINC['win_lo_sinc'],
      len(IF_SINC['moved'])))
print('     the transform-limited form would give %d systems at 1e15 W '
      'against %d, median system %.3e against %.3e, %d system limits differ'
      % (IF_SINC['n_1e15_sinc'], IF_SINC['n_1e15_applied'],
         IF_SINC['sys_med_sinc'], IF_SINC['sys_med_applied'],
         len(IF_SINC['moved'])))
for d in sorted(IF_SINC['moved'], key=lambda d: d['applied']):
    print('        %-18s %.3e applied -> %.3e  (x%.3f)'
          % (sa.designation(d['sid']), d['applied'], d['sinc'],
             d['sinc'] / d['applied']))

# ======================================================================
# 4b  THE NET BIAS ON ONE WINDOW'S LIMIT, WHICH IS OF EITHER SIGN
# ======================================================================
# ★★★★ "THESE LIMITS ARE OPTIMISTIC" IS NOT ESTABLISHED, and saying it while
# the paper also reports a conservative term of the same size is the defect
# R2-1d names.  Two one-sided terms act on a window's own limit in opposite
# directions and neither is folded into it:
#   * the atmospheric decorrelation leaves it OPTIMISTIC by the fraction
#     measured above -- a median under one per cent, a long tail;
#   * the injected profile falls \InjShortPct per cent short of the exact
#     channel response, so the measured completeness is too large and every
#     limit is CONSERVATIVE by that much (Table 4's own signed row).
# A limit is therefore quoted (1 + short) / (1 + dec) times the truth, and
# the sign of that changes across the population.  Both ends are emitted, and
# the clause requires the sign to change -- a net bias that ran one way would
# be a different sentence, and the paper would have to say so.
SHORT = texnum('InjShortPct') / 100.0
if DRIVE == 15:
    SHORT = 0.0


def _net(dec):
    """How many times the truth a quoted limit is: >1 conservative."""
    return (1.0 + SHORT) / (1.0 + dec)


NET_MED = _net(DEC_MED)
NET_SYS_MED = _net(SYS_MED)
NET_SYS_HI = _net(SYS_HI)
NET_SYS_WORST = _net(SYSD[-1][0])
ck('X14 the net bias on one window own limit is of either sign across the '
   'population -- conservative in the median window, where the injected '
   'profile shortfall exceeds the decorrelation, and optimistic in the tail '
   'where the decorrelation exceeds it -- so neither direction may be '
   'stated as the direction',
   NET_MED > 1.0 and NET_SYS_HI < 1.0 and SHORT > 0,
   'median window x%.3f of the truth, median system x%.3f, ninetieth '
   'percentile of systems x%.3f, worst system x%.3f (%s)'
   % (NET_MED, NET_SYS_MED, NET_SYS_HI, NET_SYS_WORST,
      sa.designation(SYSD[-1][2])))
print('     net bias: median window %+.0f per cent, median system %+.0f, '
      'ninetieth percentile %+.0f, worst %+.0f (per cent, + conservative)'
      % (100 * (NET_MED - 1), 100 * (NET_SYS_MED - 1),
         100 * (NET_SYS_HI - 1), 100 * (NET_SYS_WORST - 1)))

# ======================================================================
# 5  THE OFF-AXIS BEAM, AS A FACTOR
# ======================================================================
A_DOC = [float(p['pb_atten_fwhm']) for p in PBF]
A_MIN = min(A_DOC)
if DRIVE == 9:
    A_MIN = st.median(A_DOC)
BEAM_FAC = 1.0 / A_MIN
N_BEAM_TWO = sum(1 for a in A_DOC if 1.0 / a > 2.0)
ck('X11 the beam cost is the reciprocal of the response the paper already '
   'publishes as its minimum, so the factor and the response cannot part',
   abs(A_MIN - texnum('BmRespMin')) < 5e-5 and len(A_DOC) == len(CAT),
   'worst response %.4f against the published %s, factor x%.2f over %d '
   'windows' % (A_MIN, texval('BmRespMin'), BEAM_FAC, len(A_DOC)))

# ======================================================================
# 6  MACROS
# ======================================================================
# R1-1: the shape of the transferred-sensitivity uncertainty.  The range
# itself is already published (\SmcDispLo, \SmcDispHi) and is NOT
# republished here.
m('NmDispSecond', '%.2f' % RAT[-2])
m('NmDispNTenth', '%d' % N_TENTH)
m('NmOwnFacLo', '%.2f' % OWN_LO)
m('NmOwnFacHi', '%.2f' % OWN_HI)
m('NmOwnDevPct', '%.0f' % math.ceil(100 * OWN_DEV))
m('NmMeasSysNames', ', '.join(
    sa.designation(s).replace(' ', '~') for _, s in OWN[:-1])
  + ' and ' + sa.designation(OWN[-1][1]).replace(' ', '~'))
# R1-2: the tail of the decorrelation correction, both groups, and the
# systems whose own headline limit it touches.
m('NmDecHiPct', '%.0f' % (100 * DEC_HI))
m('NmDecSysMedPct', '%.0f' % (100 * SYS_MED))
m('NmDecSysHiPct', '%.0f' % (100 * SYS_HI))
m('NmDecNBigSys', '%d' % len(BIG))
# ★ the threshold is a CHOICE and not a measurement, so the prose says "a
# tenth" in words and no macro carries it: a macro would invite a reader to
# treat 10 per cent as a measured quantity, and it would join a group of
# four unrelated ten per cents that `valuetwin` would then have to declare.
m('NmDecBigSys', ', '.join(_names[:-1]) + ' and ' + _names[-1])
m('NmDecNDeepBig', '%d' % len(DEEP_BIG))
m('NmDecDeepBigSys', ', '.join(
    sa.designation(x[2]).replace(' ', '~') for x in DEEP_BIG) or 'none')
# ★ THE SET CAN NOW BE EMPTY, and an empty maximum is not a zero.  The ten
# deepest systems changed when windows wholly inside the attribution mask
# stopped supplying limits, and none of the new ten carries more than five
# per cent.  The count and the percentage are emitted as one statement so
# that a reader cannot take "0 per cent" for a measurement: where the count
# is zero the percentage is a dash.
assert (len(DEEP_BIG) == 0) == (not DEEP_BIG)
m('NmDecDeepBigPct',
  '--' if not DEEP_BIG else '%.0f' % (100 * max(x[0] for x in DEEP_BIG)))
m('NmDecNNoRec', '%d' % len(NOREC))
m('NmDecNoRecSys', ', '.join(sa.designation(s).replace(' ', '~')
                             for s in NOREC) or 'none')
# R2-4: the retention that is applied is the integrated response, so what
# this file publishes is the size of the alternative.
# ★ `\NmRespFacWorst` IS RETIRED.  It carried the response-matched factor,
# which is now the APPLIED factor and is published by the generator that
# applies it as `\SmcFacWorst`; emitting it here as well would put one
# quantity in the layer under two names, which is what `twinmacro` exists
# to refuse.
m('NmSincFacWorst', '%.2f' % RESP[0]['fac_sinc'])
# R2-1d/R2-4: the net bias, both ends.  Printed as positive numbers with the
# direction in the words beside them, because a signed per cent in prose
# reads as an error bar.
m('NmNetConsPct', '%.0f' % (100 * (NET_MED - 1.0)))
m('NmNetOptPct', '%.0f' % (100 * (1.0 / NET_SYS_HI - 1.0)))
m('NmNetOptMaxPct', '%.0f' % (100 * (1.0 / NET_SYS_WORST - 1.0)))
# ★★★ R1-1.4/R2-A6: THE GROSS FIGURE BESIDE EVERY NET ONE, AND THE SYSTEM
# NAMED.  Both published optimism figures are NET of the channel-response
# shortfall -- (1+dec)/(1+short) -- and the paper said so nowhere, so a
# reader comparing Sec. 4.1's 178 with Table F1's own 200 for the same system
# found two numbers for one quantity.  The gross ninetieth percentile is
# already published as \NmDecSysHiPct; the worst system's gross correction and
# its name were not, and Table F1 prints the gross value in its dec. column.
m('NmDecSysWorstPct', '%.0f' % (100 * SYSD[-1][0]))
m('NmDecSysWorstName', sa.designation(SYSD[-1][2]).replace(' ', '~'))
# ★★★ AND THE ATMOSPHERE-ADJUSTED COUNTERPART OF THE HEADLINE (R1-1.4).  The
# limits stay nominal; this is what they would be if the measured loss were
# divided out, which is what the referee asks to see beside them.  Applied to
# the systems that carry a value and NOT to the one that carries none, whose
# limit stays nominal -- dropping it would shorten the sample and make the
# "same systems" comparison false, which is what X16's first clause pins.
# The adjusted median itself is deliberately NOT emitted: at the two
# significant figures this paper quotes EIRP to it equals
# \EirpNinetySysMedA, and two generators publishing one value with one unit
# is what `valuetwin` exists to refuse.  The SHIFT is the statement.
_nom_sys = sorted(v for v, _r in BEST.values())
_adj_sys = sorted([v * (1.0 + o) for o, _b, _s, v in SYSD]
                  + [BEST[s][0] for s in NOREC])
if DRIVE == 17:
    # (r27 merge: renumbered from 16, which line ~414 already claims --
    # roundcollide's DRIVE clause: one number, two perturbations)
    # the system with no estimate silently dropped out of the adjusted
    # median, so the two medians are taken over different samples
    _adj_sys = sorted(v * (1.0 + o) for o, _b, _s, v in SYSD)
_NOM_MED, _ADJ_MED = st.median(_nom_sys), st.median(_adj_sys)
_ADJ_N15 = sum(1 for v in _adj_sys if v <= 1e15)
ck('X16 the atmosphere-adjusted median is taken over the same systems as the '
   'nominal one, is the shallower of the two because the correction is '
   'one-sided, and cannot raise the count of systems reaching 1e15 W',
   len(_adj_sys) == len(_nom_sys) == len(BEST) and _ADJ_MED > _NOM_MED
   and _ADJ_N15 <= texnum('NSysEfifteen'),
   '%d systems: %.4e W nominal -> %.4e W adjusted (%+.2f per cent); %d reach '
   '1e15 W against the published %s'
   % (len(_adj_sys), _NOM_MED, _ADJ_MED, 100 * (_ADJ_MED / _NOM_MED - 1.0),
      _ADJ_N15, texval('NSysEfifteen')))
m('NmDecAdjShiftPct', '%.1f' % (100 * (_ADJ_MED / _NOM_MED - 1.0)))
m('NmDecAdjNEfifteen', '%d' % _ADJ_N15)
m('NmRespDeltaWorst', '%.2f' % RESP[0]['delta'])
m('NmRespOverPct', '%.0f' % OVER_PCT)
m('NmRespNPart', '%d' % N_AFF)
m('NmRespNApplied', '%d' % N_APP)
m('NmRespNAvgA', '%d' % N_AVG_A)
m('NmRespChanTau', sci_int(CHAN_TAU))
# Minor 9: the off-axis beam as a factor.
m('NmBeamFacWorst', '%.1f' % BEAM_FAC)
m('NmBeamNFacTwo', '%d' % N_BEAM_TWO)

# ======================================================================
json.dump(dict(
    generated_by='sens_r18.py', round=ROUND, drive=DRIVE,
    n_windows=len(CAT), n_systems=NSYS, pooled_factor=P90,
    dispersion=dict(lo=DISP_LO, hi=DISP_HI, second_hi=RAT[-2],
                    n_within_tenth=N_TENTH, n=len(RAT),
                    calibration=[CAL_LO, CAL_HI]),
    measured_systems=[dict(sid=s, own_factor_ratio=f,
                           eirp_p90_W=BEST[s][0]) for f, s in OWN],
    estimated_systems=len(EST_SYS),
    decorrelation=dict(
        measured=dict(n=len(D_MEAS), median=DEC_MED, p90=DEC_HI),
        unmatched=dict(n=len(D_UNM), median=UNM_MED,
                       p90_of_median_estimate=pct90(D_UNM),
                       conditional_p90_coherence=UNM_COND),
        per_system=dict(median=SYS_MED, p90=SYS_HI,
                        worst=dict(sid=SYSD[-1][2], frac=SYSD[-1][0])),
        big=[dict(sid=s, frac=o, eirp_p90_W=v) for o, s, v in BIG],
        deepest_ten=[dict(sid=s, frac=o, eirp_p90_W=v, basis=b)
                     for o, b, s, v in DEEP]
        + [dict(sid=s, frac=None, eirp_p90_W=BEST[s][0], basis='none')
           for s in DEEP_NOREC],
        no_record=[dict(sid=s) for s in NOREC],
        threshold=BIG_PCT),
    response=dict(fwhm_unsmoothed=FW_U, fwhm_hanning=FW_H,
                  n_forms_part=N_AFF, n_applied_above_one_pct=N_APP,
                  n_avg_classa=N_AVG_A,
                  n_avg_affected=N_AVG_AFF, windows=RESP,
                  over_pct_worst=OVER_PCT,
                  if_transform_limited=IF_SINC),
    beam=dict(a_min=A_MIN, factor=BEAM_FAC, n_factor_above_two=N_BEAM_TWO),
    net_bias=dict(short=SHORT, median_window=NET_MED,
                  median_system=NET_SYS_MED, p90_system=NET_SYS_HI,
                  worst_system=NET_SYS_WORST, worst_sid=SYSD[-1][2]),
    failures=FAIL), open(OUTJSON, 'w'), indent=1)

if FAIL:
    print('\nsens_r18: %d FAILURE(S)' % len(FAIL))
    for f in FAIL:
        print('  - %s' % f)
    sys.exit(1)
open(OUT, 'w').writelines(LINES)
print('\nsens_r18: %d macros -> %s' % (len(LINES) - 1, os.path.basename(OUT)))
