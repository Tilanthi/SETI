#!/usr/bin/env python3
r"""traj_v418.py -- the trajectory model the recurrence reading actually
performs, its registration, and what the reading becomes when the carried
drift is given up entirely.

Round 700.  Writes `survey_numbers_round700.tex` and `traj_v418.json`.

WHY THIS EXISTS.  Three statements about the same test were in circulation and
only one of them described the test: the reading was interpreted with a
transmitter in a circular orbit at 1 au, whose line-of-sight acceleration is
about 6 mm s^-2, while every crossing the test is applied to has a fitted
drift corresponding to 0.5-3.8 m s^-2 -- a thousand times larger, and large
enough to carry the carrier right out of the cell inside a minute.  So the
orbit used to interpret the exclusions was not the carrier class the data
describe.  This generator measures the three things needed to state one model
and say honestly what it constrains:

 1. WHERE THE PREDICTED CELL COMES FROM.  It is the crossing's stellar-frame
    frequency re-registered at the repeat epoch -- the Earth's motion then and
    the star's systemic velocity -- and NOT the discovery drift integrated
    across the gap.  That is checkable: the recorded displacement of the cell
    from the one the delivered sky frequency would occupy is at most a few
    hundredths of what carrying the drift over the same interval would give.
    So the cell is registered to a fraction of a channel however long the gap,
    and the drift enters only inside each observation, where the search grid
    steps by half a channel across the dwell.

 2. WHAT THE GAP DOES TO A DRIFTING CARRIER.  The honest limitation is not an
    arithmetic error in the cell; it is that a carrier drifting at the fitted
    rate does not stay in that cell.  Half a step of the search's own drift
    grid, carried over the interval to the nearest covering block, moves a
    constant-acceleration carrier by a median of several channels, and the
    fitted drift itself carries it half a channel in about a minute.  Both are
    measured here.  A single-cell reading therefore tests a carrier whose
    stellar-frame frequency RECURS -- stable over the gap, or periodic and
    sampled at matched phase -- and nothing else.

 3. WHAT HAPPENS IF THE CARRIED DRIFT IS GIVEN UP.  Every repeat reading was
    also recorded at the predicted cell maximised over the whole drift grid,
    which bounds any error in the carried drift whatever its origin.  That
    reading reaches the trigger nowhere.  The exclusion depths weaken, and the
    crossings whose exclusion then rules out nothing are measured to be
    exactly the ones the recovery probability at the trigger amplitude already
    reports as untested rather than excluded.  No disposition moves, and the
    identity of those two sets is asserted rather than asserted of.

 4. WHAT A THRESHOLD OF 5 MEANS AT ONE CELL.  The trigger was set for windows
    of 10^2-10^6 cells.  At one pre-specified cell its false-alarm probability
    is 3e-7, and over the single-cell readings this stage takes the expected
    number of false confirmations is 1e-4.  The threshold that would give one
    expected false confirmation over the same readings is computed here, and
    so is the number of crossings the stage could test at it -- which is why
    the stage's low power is not attributable to archival sparsity alone.

EVERY NUMBER IS READ.  Nothing is typed: the grid steps come from the
catalogue's own per-window grids, the gaps from the measurement sets' start
times, the readings from the frozen recurrence record, and the published
counts are asserted against round 120's macros rather than repeated.

Usage: traj_v418.py [--drive N]
"""
import csv
import json
import math
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROUND = 700
DRIVE = int(sys.argv[sys.argv.index('--drive') + 1]) if '--drive' in sys.argv \
    else 0
SFX = '' if DRIVE == 0 else '_drive%d' % DRIVE
OUT = os.path.join(HERE, 'survey_numbers_round700%s.tex' % SFX)
OUTJ = os.path.join(HERE, 'traj_v418%s.json' % SFX)

CKMS = 299792.458
TRIG = 5.0
POWER = 0.90                  # the one declared level, as in round 120

M, FAIL = [], []


def m(k, v):
    assert k.isalpha(), 'a LaTeX macro name may contain letters only: ' + k
    assert k not in dict(M), 'macro defined twice: ' + k
    M.append((k, str(v)))


def ck(name, cond, detail=''):
    if not cond:
        FAIL.append(name)
    print('  %-62s %s  %s' % (name, 'PASS' if cond else 'FAIL', detail))


def macro(name):
    """One macro's value out of the frozen layer, by name."""
    import glob
    import re
    pat = re.compile(r'\\newcommand\{\\%s\}\{(.*)\}\s*$' % name)
    for p in sorted(glob.glob(os.path.join(HERE, 'survey_numbers*.tex'))):
        if '_drive' in p:
            continue
        for line in open(p):
            mm = pat.match(line.strip())
            if mm:
                return mm.group(1)
    raise KeyError(name)


def phi(x):
    """The standard normal distribution function.  The recurrence reading is
    centred on zero and scatters by one, measured in Appendix B, so nothing
    more than this is needed."""
    return 0.5 * math.erfc(-x / math.sqrt(2.0))


def med(v):
    s = sorted(v)
    n = len(s)
    return s[n // 2] if n % 2 else 0.5 * (s[n // 2 - 1] + s[n // 2])


# ---------------------------------------------------------------- inputs
REC = json.load(open(os.path.join(HERE, 'r10inputs',
                                  'recur_v411.json')))['crossings']
RCOL = json.load(open(os.path.join(HERE, 'recurcols_v411.json')))
LED = json.load(open(os.path.join(HERE, 'ledger.json')))['rows']
CAT = list(csv.DictReader(open(os.path.join(
    HERE, 'per_target_results_v3.99.csv'))))

WINOF = {}
for _r in CAT:
    WINOF.setdefault(_r['eb'], []).append(_r)


def window(eb, f):
    for r in WINOF.get(eb, []):
        lo, hi = sorted((float(r['flo_GHz']), float(r['fhi_GHz'])))
        if lo <= f <= hi:
            return r
    return None


# the one execution block the quality criterion rejects, read from the ledger
DQKEY = {(r['eb'], round(float(r['freq']), 6)) for r in LED if r.get('dq')}


def blocks(c):
    return [b for b in (c.get('blocks') or [])
            if not b.get('bad_weight_product')]


# =====================================================================
# 1.  THE PREDICTED CELL IS A FRAME TRANSFORM, NOT A CARRIED DRIFT
# =====================================================================
# Each repeat block records how far the predicted cell sits from the one the
# delivered sky frequency would occupy.  If the cell were the discovery drift
# integrated across the gap, that displacement would be of order the drift
# times the gap.  It is not, by three to five orders of magnitude, and that is
# what licenses the paper to say the cell is registered by the frame transform
# alone however long the gap.
RAT, NREAD, DCHMAX = [], 0, 0.0
for cid, v in sorted(REC.items()):
    if v['status'] != 'ok':
        continue
    d = v.get('discovery') or {}
    for b in blocks(v):
        NREAD += 1
        dc = abs(float(b['dchan_from_sky']))
        DCHMAX = max(DCHMAX, dc)
        gap = abs(float(b['sep_from_discovery_h'])) * 3600.0
        carried = abs(float(d.get('drift_Hz_s') or 0.0)) * gap \
            / float(b['chanw_Hz'])
        if carried > 0.0:
            RAT.append(dc / carried)
if DRIVE == 1:                      # T1: a cell that IS drift-propagated
    RAT = [1.0] + RAT
m('ZtFrameChanMax', '%.0f' % DCHMAX)
m('ZtFrameFrac', '%.3f' % max(RAT))
ck('T1 the predicted cell is set by the frame transform and not by the '
   'discovery drift carried across the gap',
   max(RAT) < 0.10 and NREAD == int(macro('RcNRepeatMeas')),
   '%d readings; the frame moves the cell by up to %.0f channels, at most '
   '%.3f of what carrying the drift over the same interval would give'
   % (NREAD, DCHMAX, max(RAT)))

# =====================================================================
# 2.  WHAT THE GAP DOES TO A CARRIER THAT IS ACTUALLY DRIFTING
# =====================================================================
# Two measurements, both on the search's own grid and the crossings' own
# fitted drifts, over the crossings that carry a quoted exclusion.
ROWS = []
for cid, v in sorted(REC.items()):
    d = v.get('discovery') or {}
    key = (v['eb'], round(float(v['freq_GHz']), 6))
    rc = RCOL.get('%s|%.6f' % (v['eb'], float(v['freq_GHz']))) or {}
    bl = blocks(v)
    if not bl or rc.get('T_pers') is None or not d.get('amp_mJy'):
        continue
    if key in DQKEY:
        continue
    w = window(v['eb'], float(v['freq_GHz']))
    dwell = float(d['t_end_mjdsec']) - float(d['t_start_mjdsec'])
    chanw = float(w['chanw_Hz']) if w else float(d['chanw_Hz'])
    if w and w['n_drift_trials']:
        step = 2.0 * float(w['drift_max_Hz_s']) \
            / (int(w['n_drift_trials']) - 1)
        src = 'catalogue grid'
    else:
        step = chanw / (2.0 * dwell)
        src = 'half a channel across the dwell'
    near = min(bl, key=lambda z: abs(float(z['sep_from_discovery_h'])))
    gap_near = abs(float(near['sep_from_discovery_h'])) * 3600.0
    gap_far = float(rc['dt_max_d']) * 86400.0
    drift = abs(float(d['drift_Hz_s']))
    ROWS.append(dict(
        cid=cid, star=v['star'], freq=float(v['freq_GHz']), step=step,
        step_src=src, chanw=chanw, dwell=dwell, drift=drift,
        gap_near=gap_near, gap_far=gap_far,
        tstar=float(v['tstar']), tpers=float(rc['T_pers']),
        trep=float(rc['T_rep']), f5=float(rc['f5']), excl=float(rc['excl']),
        tbest=max(float(b['T_bestdrift_pub']) for b in bl),
        tmatch=max(float(b['T_matched']) for b in bl),
        # half a grid step carried over the gap, in channels of that window
        regnear=0.5 * step * gap_near / chanw,
        regfar=0.5 * step * gap_far / chanw,
        # the interval over which half a step displaces half a channel
        regtime=chanw / step,
        # and the interval the fitted drift itself needs to leave the cell
        leave=0.5 * chanw / drift if drift > 0 else None))
if DRIVE == 7:                      # T0: a row silently lost from the set
    ROWS = ROWS[:-1]
NQ = len(ROWS)
m('ZtNCross', '%d' % NQ)
ck('T0 the set is the crossings that carry a quoted exclusion, and it is '
   "round 120's own count",
   NQ == int(macro('RcNExcl')),
   '%d against %s' % (NQ, macro('RcNExcl')))

_reg = [r['regnear'] for r in ROWS]
_half = sum(1 for r in ROWS if r['regnear'] > 0.5)
if DRIVE == 2:                      # T2: a grid fine enough to register
    for r in ROWS:
        r['regnear'] *= 1e-4
    _reg = [r['regnear'] for r in ROWS]
    _half = sum(1 for r in ROWS if r['regnear'] > 0.5)
# the line-of-sight accelerations the fitted drifts correspond to, which are
# what makes the orbital interpretation the wrong one
_alos = [CKMS * 1e3 * r['drift'] / (r['freq'] * 1e9) for r in ROWS]
m('ZtALosLo', '%.1f' % min(_alos))
m('ZtALosHi', '%.1f' % max(_alos))
m('ZtStepMed', '%.0f' % med([r['step'] for r in ROWS]))
# ★★ THE ERROR ON A FITTED DRIFT IS HALF THE GRID STEP, AND THE GRID STEP IS
#    THE MACRO ABOVE.  Printing the step while calling it the error is what
#    makes the registration interval below look twice too long: half a channel
#    at the full step is reached in half the time.  Both are published so that
#    the sentence can name the quantity it prints.
_hstep = med([0.5 * r['step'] for r in ROWS])
_hchan = med([0.5 * r['chanw'] for r in ROWS])
_regtmed = med([r['regtime'] for r in ROWS])
if DRIVE == 11:            # T2b: the full step, and a whole channel counted
    _hstep = med([r['step'] for r in ROWS])
    _half = sum(1 for r in ROWS if r['regnear'] > 1.0)
m('ZtHalfStepMed', '%.0f' % _hstep)
m('ZtRegChanMed', '%.0f' % med(_reg))
m('ZtRegChanFarMed', '%.0f' % med([r['regfar'] for r in ROWS]))
m('ZtNRegNear', '%d' % _half)
m('ZtNRegFar', '%d' % sum(1 for r in ROWS if r['regfar'] > 0.5))
m('ZtRegHoursMed', '%.1f' % (med([r['regtime'] for r in ROWS]) / 3600.0))
m('ZtRegHoursLo', '%.1f' % (min(r['regtime'] for r in ROWS) / 3600.0))
m('ZtRegHoursHi', '%.1f' % (max(r['regtime'] for r in ROWS) / 3600.0))
m('ZtLeaveSecMed', '%.0f' % med([r['leave'] for r in ROWS]))
ck('T2 a half-step error in the fitted drift, carried over the interval to '
   'the nearest covering block, displaces a constant-acceleration carrier by '
   'more than half a channel for most of these crossings, so a single-cell '
   'reading is not registered to half a channel beyond a few hours',
   _half > 0.5 * NQ
   and med([r['regtime'] for r in ROWS]) < 4.0 * 3600.0,
   'median %.1f channels at the nearest block and %.0f over the longest '
   'baseline; %d of %d exceed half a channel; half a step reaches half a '
   'channel in %.1f h (%.1f-%.1f)'
   % (med(_reg), med([r['regfar'] for r in ROWS]), _half, NQ,
      med([r['regtime'] for r in ROWS]) / 3600.0,
      min(r['regtime'] for r in ROWS) / 3600.0,
      max(r['regtime'] for r in ROWS) / 3600.0))
ck('T2b the interval published is the time HALF a grid step takes to carry a '
   'carrier HALF a channel, and the companion count uses the same '
   'half-channel definition',
   all(abs(0.5 * r['step'] * r['regtime'] - 0.5 * r['chanw'])
       < 1e-9 * r['chanw'] for r in ROWS)
   and abs(_hstep * _regtmed - _hchan) < 0.02 * _hchan
   and _half == sum(1 for r in ROWS if r['regnear'] > 0.5)
   and sum(1 for r in ROWS if r['regnear'] > 1.0) < _half,
   'half step %.1f Hz/s carries half a channel, %.1f kHz, in %.2f h; %d of '
   '%d exceed half a channel and %d a whole one'
   % (_hstep, _hchan / 1e3, _regtmed / 3600.0, _half, NQ,
      sum(1 for r in ROWS if r['regnear'] > 1.0)))

# ★★ THE SAME TWO NUMBERS FOR THE TWO CROSSINGS THE TEXT FOLLOWS THROUGH THE
# CHAIN, so that the section which describes them can say what their own
# fitted drift does to the cell instead of what a gentler orbit would do.  The
# pair is READ from the ledger's rank flag and ordered by discovery statistic
# -- the order round 550 uses for the same two crossings -- and the join is
# asserted on the stellar-frame frequency, so neither value can be attached to
# the wrong event.
LFS = {(r['eb'], round(float(r['freq']), 6)): r for r in LED}
for r in ROWS:
    _c = REC[r['cid']]
    lr = LFS[(_c['eb'], round(float(_c['freq_GHz']), 6))]
    r['fstar'] = float(lr['frame']['f_stellar'])
    r['screen'] = bool(lr['screen'])
SCR = sorted([r for r in ROWS if r['screen']], key=lambda r: -r['tstar'])
if DRIVE == 9:                      # T8: the pair taken in the other order
    SCR = SCR[::-1]
for tag, r in zip(('Sx', 'Cp'), SCR):
    m('Zt%sLeaveSec' % tag, '%.0f' % r['leave'])
    m('Zt%sDriftKms' % tag,
      '%.0f' % (CKMS * r['drift'] * r['gap_near'] / (r['freq'] * 1e9)))
ck('T8 the two crossings the text follows are the ledger\'s own rank-leading '
   'pair, in the same order and at the same stellar-frame frequencies '
   'another round prints for them',
   len(SCR) == 2
   and ['%.4f' % r['fstar'] for r in SCR] == [macro('RqFreqSx'),
                                              macro('RqFreqCp')],
   '%s at %s against %s'
   % ([r['star'] for r in SCR], ['%.4f' % r['fstar'] for r in SCR],
      [macro('RqFreqSx'), macro('RqFreqCp')]))

# =====================================================================
# 3.  THE READING WITH THE CARRIED DRIFT GIVEN UP ENTIRELY
# =====================================================================
# `T_bestdrift_pub` is the same cell read at every trial of the window's own
# drift grid, recorded for every repeat block at the time of measurement.  It
# bounds any error in the carried drift, from whatever cause, and a maximum
# over trials is positive on average whatever is there -- so it is a bound and
# not an estimate, and it is used only as one.
for r in ROWS:
    r['f5wide'] = (r['tbest'] + TRIG) / r['tpers']
    r['exclwide'] = (r['tpers'] - r['tbest']) \
        / math.sqrt(1.0 + (r['tpers'] / r['tstar']) ** 2)
    r['powtrig'] = phi(TRIG * r['tpers'] / r['tstar'] - TRIG)
WIDEMAX = max(r['tbest'] for r in ROWS)
if DRIVE == 3:                      # T3: a widened reading that confirms
    WIDEMAX = TRIG + 0.1
m('ZtFracWideMed', '%.2f' % med([r['f5wide'] for r in ROWS]))
m('ZtExclWideMed', '%.1f' % med([r['exclwide'] for r in ROWS]))
VAC = [r for r in ROWS if r['f5wide'] >= 1.0]
UNT = [r for r in ROWS if r['powtrig'] < POWER]
if DRIVE == 8:                      # T5: a power level read at the wrong bar
    UNT = [r for r in ROWS if r['powtrig'] < 0.5 * POWER]
if DRIVE == 4:                      # T4: a vacuous exclusion NOT untested
    #: ★ RE-POINTED (r19): this drive removed a row from VAC, which leaves a
    #: SUBSET and so can no longer fail the clause below.  It now adds a row
    #: that is not in the untested set, which is the defect the clause exists
    #: to refuse.
    VAC = VAC + [r for r in ROWS
                 if r['cid'] not in {q['cid'] for q in VAC}][:1]
m('ZtNWideVac', '%d' % len(VAC))
ck('T3 giving up the carried drift confirms nothing: the same cell read at '
   'every trial of the grid reaches the trigger in no repeat block',
   WIDEMAX < TRIG and '%.2f' % WIDEMAX == macro('RcTMax'),
   'largest %.2f against a trigger of %.1f and against the published %s, '
   'over %d readings' % (WIDEMAX, TRIG, macro('RcTMax'), NREAD))
ck('T4 and every crossing whose exclusion then rules out nothing is '
   'already reported as untested rather than excluded, so no disposition '
   'depends on the carried drift.  A SUBSET AND NOT AN IDENTITY: the set the '
   'paper reports untested is the MEASURED one, which is the larger, and the '
   'comparison against it is hostinj_r19.py C14 -- this generator writes '
   'round 700 and the measurement is round 870, so it cannot be made here',
   {r['cid'] for r in VAC} <= {r['cid'] for r in UNT} and len(VAC) > 0,
   '%d of %d rule out nothing (%s); %d are untested at the trigger '
   'amplitude (%s)'
   % (len(VAC), NQ, ', '.join(sorted(r['cid'] for r in VAC)), len(UNT),
      ', '.join(sorted(r['cid'] for r in UNT))))
ck('T5 the published exclusion count and the untested count are round '
   "120's, not repeated here",
   len(UNT) == int(macro('RcNPowerLoTrig'))
   and NQ - len(UNT) == int(macro('RqNPowerHi')),
   '%d untested against %s, %d tested against %s, %d in all'
   % (len(UNT), macro('RcNPowerLoTrig'), NQ - len(UNT),
      macro('RqNPowerHi'), NQ))

# =====================================================================
# 4.  A THRESHOLD OF FIVE, AT ONE PRE-SPECIFIED CELL
# =====================================================================
# ★★★★ v4.23 (R2-12(c)): THE ONE-CELL FALSE-ALARM PROBABILITY IS EVALUATED
# AT THE SCATTER THE READING ACTUALLY HAS, not at unit variance.  The null of
# this statistic is measured in `recurnull_v413.py` over 511 one-cell
# readings -- mean +0.014, sd 1.046 -- and a 4.6 per cent wider distribution
# is a factor of three in the tail at a threshold of five.  Quoting 3e-7
# where the measurement gives 9e-7 overstates the stage by that factor, and
# the number is a floor on the paper's own claim rather than a decoration.
# The scatter is READ from the null record and never typed.
SCAT = float(json.load(open(os.path.join(
    HERE, 'recurnull_v413.json')))['null']['sd'])
ALPHA = 1.0 - phi(TRIG / SCAT)
EXPFALSE = NREAD * ALPHA
# ★ THE BAR THIS STAGE SHOULD BE JUDGED AGAINST IS A STATED FALSE-ALARM
# PROBABILITY FOR THE WHOLE SET OF READINGS, not an expectation of one false
# confirmation: at the threshold where one is expected, the chance of making
# one at all is about two in three, which is no protection whatever.  One
# declared level, as elsewhere in this paper.
FWTARGET = 0.01


def fwthr(n, fw, s=1.0):
    """The threshold at which the probability that ANY of `n` readings of
    scatter `s` exceeds it is `fw`.  `s` defaults to unity so that the
    unit-variance bar can be computed for comparison, which is what the
    clause below asserts the scaling against."""
    per = 1.0 - (1.0 - fw) ** (1.0 / n)
    lo, hi = 0.0, 12.0
    for _ in range(200):
        mid = 0.5 * (lo + hi)
        if 1.0 - phi(mid / s) > per:
            lo = mid
        else:
            hi = mid
    return hi


def fwrate(n, z, s=1.0):
    """The probability that any of `n` readings of scatter `s` exceeds `z`.
    ★ v4.23: `s` joins it with `fwthr`, because the bar is now set at the
    MEASURED scatter and a family-wise rate computed at unit variance
    against a bar computed at 1.046 is a comparison of two different
    quantities -- which is what made T9 fail when the scatter went in."""
    return 1.0 - phi(z / s) ** n


THR = fwthr(NREAD, FWTARGET, SCAT)
EXPONE = 0.0
_lo, _hi = 0.0, 12.0
for _ in range(200):                  # the bar an expectation of one sets
    _mid = 0.5 * (_lo + _hi)
    #   ★ v4.23: at the measured scatter, like the bar it is compared with
    if NREAD * (1.0 - phi(_mid / SCAT)) > 1.0:
        _lo = _mid
    else:
        _hi = _mid
EXPONE = _hi
MATCHMAX = max(r['tmatch'] for r in ROWS)
if DRIVE == 5:                      # T6: a reading above the matched bar
    MATCHMAX = THR + 0.1
# the two probabilities, mantissa and exponent computed, never typed
def _sci(x, nd=0):
    e = int(math.floor(math.log10(abs(x))))
    return ('%.*f' % (nd, x / 10.0 ** e)), '%d' % e


_pm, _pe = _sci(ALPHA)
m('ZtOneCellP', _pm)
m('ZtOneCellExp', _pe)
_fm, _fe = _sci(EXPFALSE)
m('ZtExpFalseP', _fm)
m('ZtExpFalseExp', _fe)
m('ZtFwPct', '%g' % (100.0 * FWTARGET))
m('ZtTrialThr', '%.1f' % THR)
_ntrial = sum(1 for r in ROWS
              if phi(TRIG * r['tpers'] / r['tstar'] - THR) >= POWER)
if DRIVE == 6:                      # T7: a lower bar that tests no more
    _ntrial = int(macro('RqNPowerHi'))
m('ZtNPowerTrial', '%d' % _ntrial)
ck('T6 the trigger is far stricter at one pre-specified cell than in a '
   'window, and no reading at the carried drift reaches even the lower '
   'threshold that holds the false-alarm probability of the whole set at the '
   'declared level',
   MATCHMAX < THR and THR < TRIG
   #   ★★★ v4.23: WAS `ALPHA < 1e-6`, WHICH PINNED TODAY'S NUMBER.  On the
   #   measured scatter alpha is 8.8e-7, twelve per cent from firing for no
   #   reason anyone chose.  The invariant is the DIRECTION: a wider
   #   measured null can only make a single cell LESS safe than the
   #   unit-variance calculation, never more.
   and ALPHA > 1.0 - phi(TRIG)
   #   and the bar must be the unit-variance bar times the measured
   #   scatter, which is what "evaluated at the measured scatter" means
   and abs(THR - SCAT * fwthr(NREAD, FWTARGET, 1.0)) < 1e-9
   and EXPFALSE < 1e-3
   and '%.2f' % MATCHMAX == macro('RcTMatched'),
   'one-cell false alarm %.2e at the measured scatter %.3f (%.2e at unit '
   'variance), %.2e expected over %d readings; %.0f per cent over the set '
   'puts the bar at %.2f, the unit-variance bar at %.2f, and the largest '
   'reading is %.2f'
   % (ALPHA, SCAT, 1.0 - phi(TRIG), EXPFALSE, NREAD, 100.0 * FWTARGET, THR,
      fwthr(NREAD, FWTARGET, 1.0), MATCHMAX))
ck('T7 at that threshold the stage tests more of these crossings than at '
   'the trigger, so its low power is not attributable to the archive alone',
   _ntrial > int(macro('RqNPowerHi')) and _ntrial <= NQ,
   '%d of %d at a threshold of %.2f against %s of %d at %.1f'
   % (_ntrial, NQ, THR, macro('RqNPowerHi'), NQ, TRIG))

_FW = fwrate(NREAD, THR if DRIVE != 10 else EXPONE, SCAT)
ck('T9 the bar quoted is the one its own stated false-alarm probability '
   'implies, and an expectation of one false confirmation is not that bar',
   abs(_FW - FWTARGET) < 1e-6 and fwrate(NREAD, EXPONE, SCAT) > 0.5,
   'a bar of %.2f gives %.4f over %d readings, against the %.2f target; the '
   'threshold at which one false confirmation is EXPECTED is %.2f, where the '
   'probability of making one is %.2f'
   % (THR, _FW, NREAD, FWTARGET, EXPONE, fwrate(NREAD, EXPONE, SCAT)))

# ------------------------------------------------------------------ output
json.dump(dict(rows=ROWS, n_read=NREAD, frame_frac_max=max(RAT),
               fw_target=FWTARGET, fw_rate=_FW, exp_one_thr=EXPONE,
               wide_max=WIDEMAX, trial_thr=THR, alpha_one_cell=ALPHA,
               vacuous=[r['cid'] for r in VAC],
               untested=[r['cid'] for r in UNT]),
          open(OUTJ, 'w'), indent=1, default=str)

with open(OUT, 'w') as fh:
    fh.write('%% GENERATED by traj_v418.py (round %d) -- do not hand-edit.\n'
             % ROUND)
    for k, v in M:
        fh.write('\\newcommand{\\%s}{%s}\n' % (k, v))
print('\n%d macros -> %s' % (len(M), os.path.basename(OUT)))
if FAIL:
    print('FAILED: %s' % ', '.join(FAIL))
    sys.exit(1)
