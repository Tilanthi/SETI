#!/usr/bin/env python3
r"""statunit_v426.py -- the unit of the widened recurrence comparison, the
rank's own expectation under exchangeability, and the broadband flare
prediction's channel count.

Round 991 (renumbered from 990 by r26-integrate: r26-limits had already claimed 990).  Writes `survey_numbers_round991.tex` and `statunit_v426.json`.

WHY THIS EXISTS.  Three statements in the paper are made in the wrong unit,
and each of them is load-bearing.

 1. THE WIDENED RECURRENCE COMPARISON IS QUOTED PER READING AND NOT PER
    WINDOW.  `recurnull_v413.py` builds the covering set crossing by
    crossing, so a window that covers two unattributed crossings enters the
    loop twice -- and `wread()` depends on the window alone, never on the
    crossing it was summoned for, so the second entry is the SAME
    measurement read a second time.  Both the count and the expectation are
    multiplied by that multiplicity, so the ratio survives, but the
    comparison is then written as though it had that many independent
    trials.  The distinct-window restatement is computed here, with its own
    Poisson-binomial tail, beside a block-resampled tail for the
    reading-level form, so the choice between the two units is measured and
    not asserted.

 2. THE RANK IS SAID TO DECIDE NOTHING WITHOUT THE NUMBER THAT WOULD SHOW
    IT.  Under exchangeability the chance that the star outranks all of its
    own control positions is 1/(n_ctrl+1) per crossing, so the expected
    number of crossings doing so across the unattributed population is a
    quantity of two inputs, and the tail at the observed count follows.  It
    is computed here, with the empirical rate in the two reserved sets.

 3. THE BROADBAND FLARE PREDICTION USES A CELL COUNT WHERE IT NEEDS A
    CHANNEL COUNT.  A flare raises every CHANNEL of a window alike, so the
    coherent gain is sqrt(N_chan); drift trials are re-reads of the same
    channels and add none.  The frozen input carries 49--4717, and
    5*sqrt(N)=4717 needs N = 890,004, which no ALMA window holds.  The
    channel count is recomputed here from the catalogue's own bandwidth and
    channel width.

Inputs, all of them the paper's own: `r10inputs/recur_v411.json`,
`ledger.json`, `per_target_results_v3.99.csv`, `repaired_v409.csv`, and the
frozen macro layer `survey_numbers*.tex` (read, never written).

Usage: statunit_v426.py [--drive N]

Drives, one per assertion, each the mistake the assertion exists to catch:
1 the readings not reduced to windows at all, so the window unit IS the
reading unit; 2 one covering window dropped from each crossing's set;
3 the window key reduced to the block, so two windows of one block collide;
4 the rank expectation taken over all crossings instead of the unattributed
ones; 5 the rank tail computed as P(>=1) instead of P(>=2); 6 the flare
prediction taken over searched cells instead of channels; 7 the readings'
tail resampled over windows instead of over the blocks they share.
"""
import csv
import glob
import json
import math
import os
import re
import sys

import numpy as np

# ★★★★ THE TREE IT READS AND THE DIRECTORY IT WRITES ARE TWO THINGS.  In the
# version directory, where `make_all.sh` runs it, they are the same and
# nothing changes.  Run from anywhere else, `STATUNIT_TREE` points the READS
# at a version tree -- and the WRITES stay beside this script, because the
# first version of this line set both and promptly wrote two new files into a
# tree declared read-only.  A test must never write a path production reads,
# and an input tree is such a path.
HERE = os.environ.get('STATUNIT_TREE') or os.path.dirname(
    os.path.abspath(__file__))
OUTDIR = os.path.dirname(os.path.abspath(__file__))
ROUND = 990
DRIVE = int(sys.argv[sys.argv.index('--drive') + 1]) if '--drive' in sys.argv \
    else 0
SFX = '' if DRIVE == 0 else '_drive%d' % DRIVE
OUT = os.path.join(OUTDIR, 'survey_numbers_round991%s.tex' % SFX)
OUTJ = os.path.join(OUTDIR, 'statunit_v426%s.json' % SFX)

TRIG = 5.0
CKMS = 299792.458
NBOOT = 20000
SEED = 990

M = []
FAIL = []


def _minus(v):
    """A leading hyphen is a minus sign."""
    s = str(v)
    return '\\ensuremath{-}' + s[1:] if s[:1] == '-' else s


def m(k, v):
    M.append((k, v))
    assert k.isalpha(), 'a LaTeX macro name may contain letters only: ' + k


def ck(name, cond, detail=''):
    if not cond:
        FAIL.append(name)
    print('  %-66s %s  %s' % (name, 'PASS' if cond else 'FAIL', detail))


_MPAT = re.compile(r'\\(?:new|renew|provide)command\{\\([A-Za-z]+)\}'
                   r'\{((?:[^{}]|\{[^{}]*\})*?)\}')
_FROZEN = {}
for _fn in sorted(glob.glob(os.path.join(HERE, 'survey_numbers*.tex'))):
    if '_drive' in _fn or 'round991' in _fn:
        continue
    for _mm in _MPAT.finditer(open(_fn, encoding='utf-8').read()):
        if _mm.group(2).strip():
            _FROZEN[_mm.group(1)] = _mm.group(2).strip()


def frozen(name):
    """One macro's value out of the frozen layer, by name."""
    if name not in _FROZEN:
        raise SystemExit('macro %s not found' % name)
    return _FROZEN[name]


def fnum(name):
    """The same, as a float, with the paper's own typography removed."""
    s = frozen(name)
    s = s.replace('\\ensuremath{-}', '-').replace('\\,', '')
    s = s.replace('$', '').replace('{', '').replace('}', '').strip()
    return float(s)


def gauss_sf(x):
    """One-sided Gaussian tail probability, from the error function."""
    return 0.5 * math.erfc(x / math.sqrt(2.0))


def pb_tail(ps, k):
    """P(K >= k) for independent Bernoulli trials of probabilities `ps`, by
    exact convolution of the Poisson-binomial distribution.  No Poisson or
    Gaussian approximation enters, because the per-window probabilities here
    are not small and not equal."""
    d = np.zeros(len(ps) + 1)
    d[0] = 1.0
    for i, p in enumerate(ps):
        d[1:i + 2] = d[1:i + 2] * (1.0 - p) + d[0:i + 1] * p
        d[0] *= (1.0 - p)
    return float(d[k:].sum()), d


# ------------------------------------------------------------------ inputs
R = json.load(open(os.path.join(HERE, 'r10inputs', 'recur_v411.json')))
LED = json.load(open(os.path.join(HERE, 'ledger.json')))
CAT = list(csv.DictReader(open(os.path.join(
    HERE, 'per_target_results_v3.99.csv'))))

REPAIR = {}
for _d in csv.DictReader(open(os.path.join(HERE, 'repaired_v409.csv'))):
    _lo, _hi = float(_d['flo_GHz']), float(_d['fhi_GHz'])
    REPAIR[(_d['eb'], round(min(_lo, _hi), 4),
            round(max(_lo, _hi), 4))] = float(_d['star_peak_snr_repaired'])

LEDEB = {}
for _l in LED['rows']:
    LEDEB.setdefault(_l['eb'], []).append(_l)

BYEB, BYSYS, BYNAME = {}, {}, {}
for _r in CAT:
    BYEB.setdefault(_r['eb'], []).append(_r)
    BYSYS.setdefault(_r['system_id'], []).append(_r)
    BYNAME.setdefault(_r['star_name'], []).append(_r)

CROSS = R['crossings']
UNATTR = [r for r in LED['rows'] if not r['attributed']]
CRK = {(c['eb'], round(float(c['freq_GHz']), 4)): c for c in CROSS.values()}


def blocks(c):
    return [b for b in c.get('blocks', []) if not b.get('bad_weight_product')]


def wread(q):
    """The adopted statistic of one window.  NOTE WHAT IS NOT IN THE
    SIGNATURE: the crossing.  This reading is a property of the window and of
    nothing else, which is the whole of finding 1."""
    lo, hi = float(q['flo_GHz']), float(q['fhi_GHz'])
    lo, hi = min(lo, hi), max(lo, hi)
    cat = (float(q['star_snr']),
           float(q['f_cross_GHz']) if q['f_cross_GHz'] else None)
    inside = [_l for _l in LEDEB.get(q['eb'], [])
              if lo <= float(_l['freq']) <= hi]
    if inside:
        best = max(inside, key=lambda _l: float(_l['tstar']))
        return float(best['tstar']), float(best['freq'])
    rep = REPAIR.get((q['eb'], round(lo, 4), round(hi, 4)))
    return (cat[0] if rep is None else rep), cat[1]


def wkey(q):
    """The identity of a window: its block and its own edges, in min/max
    order because a descending spectral window writes them reversed."""
    lo, hi = float(q['flo_GHz']), float(q['fhi_GHz'])
    if DRIVE == 3:
        return (q['eb'],)
    return (q['eb'], round(min(lo, hi), 4), round(max(lo, hi), 4))


def wexp(q):
    """The window's own chance of holding one cell above the trigger."""
    if not q['n_ind_cells']:
        return None
    N = float(q['n_ind_cells'])
    sw = 0.5 * (float(q['scale_route_a']) + float(q['scale_route_b']))
    return -math.expm1(N * math.log(1.0 - gauss_sf(TRIG / sw)))


# =====================================================================
# 1.  THE UNIT OF THE WIDENED RECURRENCE COMPARISON
# =====================================================================
# Rebuilt exactly as `recurnull_v413.py` builds it, and the rebuild is
# asserted against that generator's three published values before anything
# new is computed from it.  A restatement that cannot reproduce the statement
# it restates is worth nothing.
COVSET = {}
for r in UNATTR:
    f, eb = float(r['freq']), r['eb']
    dw = [q for q in BYEB.get(eb, [])
          if float(q['flo_GHz']) <= f <= float(q['fhi_GHz'])]
    sid = dw[0]['system_id'] if len(dw) == 1 else None
    if sid is None:
        c = CRK.get((eb, round(f, 4)))
        for b in blocks(c or {}) if c else []:
            q = [x for x in BYEB.get(b['eb'], [])
                 if float(x['flo_GHz']) <= b['f_here_GHz']
                 <= float(x['fhi_GHz'])]
            if q:
                sid = q[0]['system_id']
                break
    assert sid, 'no system identifier for %s %s' % (r['star'], eb)
    pool = BYSYS[sid]
    cov = [q for q in pool if q['eb'] != eb
           and float(q['flo_GHz']) <= f <= float(q['fhi_GHz'])]
    if DRIVE == 2 and cov:
        cov = cov[:-1]
    COVSET[(eb, round(f, 4))] = (sid, cov)

# --- the reading-level form, which is what the paper now quotes
read_rows = []           # (window key, statistic, expectation, catalogue row)
for k, (sid, cov) in COVSET.items():
    for q in cov:
        read_rows.append((wkey(q), wread(q)[0], wexp(q), q))
n_read = len(read_rows)
n_read_exc = sum(1 for _, s, _, _ in read_rows if s >= TRIG)
exp_read = sum(e for _, _, e, _ in read_rows if e is not None)

ck('U1 the rebuilt covering set reproduces the published reading-level '
   'comparison exactly, so the restatement below is of this paper and not '
   'of another one',
   n_read == int(fnum('WdNCov')) and n_read_exc == int(fnum('WdNExc'))
   and abs(exp_read - fnum('WdExpect')) < 0.05,
   '%d readings (published %s), %d above trigger (%s), expectation %.2f (%s)'
   % (n_read, frozen('WdNCov'), n_read_exc, frozen('WdNExc'), exp_read,
      frozen('WdExpect')))

# --- the window-level form
WIN, COLLIDE = {}, []
_SEQ = 0
for wk, s, e, q in read_rows:
    if DRIVE == 1:                # every reading kept as its own "window"
        _SEQ += 1
        wk = wk + (_SEQ,)
    if wk in WIN:
        # The same window read again.  It MUST return the same statistic and
        # the same expectation, because neither is a function of the crossing
        # -- and that identity is the evidence that the second reading is not
        # a second trial.  Recorded rather than asserted, so that a key which
        # collides two different windows fails a check instead of raising.
        if abs(WIN[wk][0] - s) > 1e-9 or (WIN[wk][1] is None) != (e is None) \
                or (e is not None and abs(WIN[wk][1] - e) > 1e-12):
            COLLIDE.append((wk, WIN[wk][0], s))
        WIN[wk] = (s, WIN[wk][1], WIN[wk][2] + 1, WIN[wk][3])
    else:
        WIN[wk] = (s, e, 1, q)

n_win = len(WIN)
n_win_exc = sum(1 for s, _, _, _ in WIN.values() if s >= TRIG)
exp_win = sum(e for _, e, _, _ in WIN.values() if e is not None)
mult = sorted((c for _, _, c, _ in WIN.values()), reverse=True)
n_multi = sum(1 for c in mult if c > 1)

ck('U2 every repeated reading of one window returns one statistic and one '
   'expectation, so a repeat is a re-read and not a trial, and the key does '
   'not collide two different windows',
   not COLLIDE and n_multi > 0,
   '%d readings over %d distinct windows, %d of them read more than once, '
   'the most %d times; %d collisions'
   % (n_read, n_win, n_multi, mult[0], len(COLLIDE)))
# ★★★★ THE MULTIPLICITY IS NOT UNIFORM, AND THAT IS THE WHOLE FINDING.  A
# window covering several crossings is a wide, finely channelised one with
# many cells, so weighting each window by the number of crossings it covers
# weights the EXPECTATION up far more than it weights the COUNT: the two
# units do not agree, and the reading unit is the more favourable of them.
# This is asserted in the direction that matters -- that the unit changes the
# answer -- so a future run cannot quietly return to the reading unit on the
# ground that it makes no difference.
ck('U3 the two units do not give the same answer, so the unit is a choice '
   'and not a presentation: weighting each window by the crossings it '
   'covers raises the expectation faster than the count',
   abs(n_read_exc / exp_read - n_win_exc / exp_win) > 0.2,
   'readings %d/%.2f = %.3f, windows %d/%.2f = %.3f'
   % (n_read_exc, exp_read, n_read_exc / exp_read, n_win_exc, exp_win,
      n_win_exc / exp_win))

# ★★★★ THE DISTINCT-WINDOW COUNT IS ALREADY IN THE PAPER.  Table D1, written
# by `pairacct_r23.py`, gives the above-trigger readings as `\PaNRepWin`
# windows of `\PaNRepBlock` blocks, and that is the same 17 counted here from
# a different generator on a different route.  The identity is asserted, so
# the two can never disagree, and it is why the restatement changes no
# measurement: the number was measured and printed, and the sentences quoting
# the comparison used the other one.
ck('U9 the distinct-window count agrees with the one the pair-accounting '
   'table already publishes, from a different generator and a different '
   'route, so the two statements of the same quantity cannot disagree',
   n_win_exc == int(fnum('PaNRepWin')),
   '%d here against %s in the table' % (n_win_exc, frozen('PaNRepWin')))

# --- the window-level tail, exactly
ps_win = [e for _, e, _, _ in WIN.values() if e is not None]
n_nocell = sum(1 for _, e, _, _ in WIN.values() if e is None)
p_win, dist_win = pb_tail(ps_win, n_win_exc)
ck('U4 the window-level tail is computed on the distribution of the count '
   'and not on a range about its mean, and the distribution is proper',
   abs(dist_win.sum() - 1.0) < 1e-9
   and abs(float((np.arange(len(dist_win)) * dist_win).sum()) - exp_win)
   < 1e-6,
   'sum %.12f, mean %.4f against the summed rate %.4f'
   % (dist_win.sum(), float((np.arange(len(dist_win)) * dist_win).sum()),
      exp_win))

# --- the reading-level tail with the correlation put back, by resampling the
#     execution blocks the windows belong to.  This is the other repair A5
#     allows: keep the readings and get the tail from blocks.
rng = np.random.default_rng(SEED)
BLK = {}
for wk, s, e, q in read_rows:
    BLK.setdefault(wk[0], []).append((s, e))
bkeys = sorted(BLK)
UNITS = {'block': [BLK[b] for b in bkeys],
         'window': [[(v[0], v[1])] * v[2] for v in WIN.values()]}


def resample(units):
    """The count's own distribution when the resampling unit is `units`."""
    out = np.empty(NBOOT)
    for i in range(NBOOT):
        pick = rng.integers(0, len(units), len(units))
        lam = 0.0
        for j in pick:
            for s, e in units[j]:
                if e is not None:
                    lam += e
        out[i] = rng.poisson(lam)
    return out


c_blk = resample(UNITS['block'])
c_win = resample(UNITS['window'])
_primary, _other = ((c_win, c_blk) if DRIVE == 7 else (c_blk, c_win))
p_read_boot = float((_primary >= n_read_exc).mean())
ck('U5 the readings are resampled over the BLOCKS they share and not over '
   'themselves, which is the only resampling that carries the correlation, '
   'and it gives the wider distribution',
   _primary.std() > _other.std(),
   'blocks give P = %.2f with s.d. %.2f over %d blocks, windows give '
   'P = %.2f with s.d. %.2f; the Poisson tail at the summed rate is %.2f'
   % (float((c_blk >= n_read_exc).mean()), c_blk.std(), len(bkeys),
      float((c_win >= n_read_exc).mean()), c_win.std(),
      1.0 - sum(math.exp(-exp_read) * exp_read ** k / math.factorial(k)
                for k in range(n_read_exc))))

m('WuNRead', '%d' % n_read)
m('WuNReadExc', '%d' % n_read_exc)
m('WuNWin', '%d' % n_win)
m('WuNWinExc', '%d' % n_win_exc)
m('WuExpWin', '%.1f' % exp_win)
m('WuProbWin', '%.2f' % p_win)
m('WuNMulti', '%d' % n_multi)
m('WuMultMax', '%d' % mult[0])
m('WuProbReadBoot', '%.2f' % p_read_boot)
m('WuNNoCell', '%d' % n_nocell)
m('WuNBlock', '%d' % len(bkeys))

# ---------------------------------------------------------------------
# 1b.  IS THE WINDOW-LEVEL EXCESS A PROPERTY OF THE NULL MODEL, OR OF THE
#      DATA?  Two independent nulls and one decomposition.
# ---------------------------------------------------------------------
# The expectation above is a Gaussian tail over each window's own
# independent cells, scaled by its own control positions.  The paper's
# PRIMARY null elsewhere is different and purely empirical: the fraction of
# a window's own control positions that reaches the trigger.  A comparison
# quoted to one digit must not depend on which of the two computed it, and
# quoting only the more favourable of two nulls is the practice R1 2.1 names.
import collections

EXPJ = json.load(open(os.path.join(HERE, 'corrected_export_v399.json')))['rows']
FFXJ = json.load(open(os.path.join(HERE, 'r8inputs', 'v409',
                                   'fieldfix_v409.json')))


def wkey3(eb, a, b):
    a, b = float(a), float(b)
    return (eb, round(min(a, b), 3), round(max(a, b), 3))


def skey(s):
    return re.sub(r'\s+', '', s or '').lower()


_BYWIN, _FFWIN = collections.defaultdict(list), collections.defaultdict(list)
for _r in EXPJ:
    _BYWIN[wkey3(_r['eb'], _r['flo'], _r['fhi'])].append(_r)
for _r in FFXJ:
    _FFWIN[wkey3(_r['eb'], _r['flo'], _r['fhi'])].append(_r)


def _pick(cands, row, namekey, maxkey):
    same = [x for x in cands if skey(x.get(namekey)) == skey(row['star_name'])]
    pool = same or cands
    if len(pool) == 1:
        return pool[0]
    return min(pool, key=lambda x: abs(float(x[maxkey])
                                       - float(row['ctrl_max_snr'] or 0)))


# Built exactly as `chance_v414.py` builds it: per catalogue ROW, because a
# window shared by two components of a multiple carries two rows and the
# control maximum is what distinguishes them.  Keyed afterwards by window.
PEXC, _NOVEC = {}, 0
for _i, _r in enumerate(CAT):
    _k = wkey3(_r['eb'], _r['flo_GHz'], _r['fhi_GHz'])
    _q = _pick(_FFWIN.get(_k, []), _r, 'star', 'ctrl_max') if _FFWIN.get(_k) \
        else None
    if _q is None or not _q.get('ctrl_all'):
        _q = _pick(_BYWIN.get(_k, []), _r, 'star_name', 'ctrl_max') \
            if _BYWIN.get(_k) else None
    if _q is not None and _q.get('ctrl_all'):
        PEXC[(_r['eb'], round(min(float(_r['flo_GHz']), float(_r['fhi_GHz'])),
                              4),
              round(max(float(_r['flo_GHz']), float(_r['fhi_GHz'])), 4),
              _r['star_name'])] = float(
                  (np.asarray(_q['ctrl_all'], float) >= TRIG).mean())
    else:
        _NOVEC += 1

ps_ctrl, n_noctrl = [], 0
for _wk, (_s, _e, _m, _c) in WIN.items():
    # ★ A DEGENERATE WINDOW KEY MUST NOT RAISE HERE.  Drive 3 reduces the key
    # to the block, and a drive has to end in a verdict, not a traceback: the
    # check it is aimed at (U2) has already recorded the collision.
    _kk = ((_wk[0], _wk[1], _wk[2], _c['star_name']) if len(_wk) >= 3
           else None)
    if _kk is not None and _kk in PEXC:
        ps_ctrl.append(PEXC[_kk])
    else:
        n_noctrl += 1
exp_ctrl = sum(ps_ctrl)
p_ctrl, _dc = pb_tail(ps_ctrl, n_win_exc)

ck('U6 the window-level comparison departs from chance on the empirical '
   'control-position null as well as on the Gaussian cell null, so the '
   'departure is a property of the data and not of one model, and the '
   'larger of the two probabilities is the one the paper quotes',
   n_noctrl <= 1 and p_ctrl < p_win and not COLLIDE,
   'control positions %d against %.2f at P = %.3f, cells %d against %.2f '
   'at P = %.3f (%d of %d windows retain no control vector)'
   % (n_win_exc, exp_ctrl, p_ctrl, n_win_exc, exp_win, p_win, n_noctrl,
      n_win))

# --- every window above the trigger holds a crossing the ledger lists, so
#     this comparison re-reads the survey's own trigger-level excess over its
#     control positions and is not independent of it.
n_led = 0
star_exc = collections.Counter()
for wk, (s, e, mm, c) in WIN.items():
    if s < TRIG:
        continue
    lo = wk[1] if len(wk) >= 3 else float(c['flo_GHz'])
    hi = wk[2] if len(wk) >= 3 else float(c['fhi_GHz'])
    rows = [l for l in LEDEB.get(wk[0], [])
            if min(lo, hi) <= float(l['freq']) <= max(lo, hi)]
    if rows:
        n_led += 1
    star_exc[c['star_name']] += 1
ck('U7 every covering window above the trigger holds a crossing the ledger '
   'already lists, so the window search re-reads the trigger-level excess '
   'of the census and adds no independent event to it',
   n_led == n_win_exc,
   '%d of %d, toward %s' % (n_led, n_win_exc,
                            ', '.join('%s (%d)' % kv
                                      for kv in star_exc.most_common())))

# --- and the departure is carried by two objects.  Their windows are removed
#     ENTIRELY -- above the trigger and below it alike -- because removing
#     only the ones above it would manufacture a deficit.
TOP2 = [k for k, _v in star_exc.most_common(2)]
rest_ps, rest_exc, rest_n = [], 0, 0
for wk, (s, e, mm, c) in WIN.items():
    if c['star_name'] in TOP2:
        continue
    rest_n += 1
    if e is not None:
        rest_ps.append(e)
    if s >= TRIG:
        rest_exc += 1
p_rest, _dr = pb_tail(rest_ps, rest_exc)
ck('U8 the nominal departure is concentrated on two objects, and over the '
   'other systems the comparison is consistent -- which is the statement '
   'the appendix must carry beside the pooled one',
   p_rest > 0.1 and rest_n < n_win,
   '%s carry %d of the %d; over the other %d windows it is %d against %.2f '
   'at P = %.2f' % (' and '.join(TOP2), sum(star_exc[k] for k in TOP2),
                    n_win_exc, rest_n, rest_exc, sum(rest_ps), p_rest))

m('WuExpWinCtrl', '%.1f' % exp_ctrl)
m('WuProbWinCtrl', '%.2f' % p_ctrl)
m('WuNWinLedger', '%d' % n_led)
m('WuNWinExcTwo', '%d' % sum(star_exc[k] for k in TOP2))
# ★ THE PAPER'S OWN SPELLING, NEVER THE CATALOGUE'S.  The catalogue carries
# `HD14055` where the page prints `HD 14055`, and a macro is typeset verbatim.
DISP = {}
for _l in LED['rows']:
    DISP[_l['star']] = _l.get('display') or _l['star']
_names = [DISP.get(k, k) for k in TOP2]
assert all(' ' in n or n.startswith('ALMA') for n in _names), _names
m('WuTwoStars', ' and '.join(_names))
m('WuNWinRestExc', '%d' % rest_exc)
m('WuNWinRest', '%d' % rest_n)
m('WuExpRest', '%.1f' % sum(rest_ps))
m('WuProbRest', '%.2f' % p_rest)

# =====================================================================
# 2.  THE RANK'S OWN EXPECTATION UNDER EXCHANGEABILITY
# =====================================================================
# Under exchangeability the star is one of n_ctrl+1 interchangeable
# positions, so the chance it leads them all is 1/(n_ctrl+1) -- a quantity
# with no free parameter.  The population is the unattributed crossings of
# the quality-passing data, which is the population the rank is read over.
NCTRL = int(fnum('NCtrl'))
nunattr = int(fnum('EvNCrossQp')) - int(fnum('EvNAttrQp'))
if DRIVE == 4:
    nunattr = int(fnum('EvNCrossQp'))
ck('R0 the unattributed population is the paper\'s own difference and is '
   'not retyped', nunattr == int(fnum('EvNUnattrQp')),
   '%d = %s - %s, published %s'
   % (nunattr, frozen('EvNCrossQp'), frozen('EvNAttrQp'),
      frozen('EvNUnattrQp')))

p1 = 1.0 / (NCTRL + 1)
exp_lead = nunattr * p1
k_tail = 1 if DRIVE == 5 else 2
p_lead, _d = pb_tail([p1] * nunattr, k_tail)
n_obs_lead = int(fnum('EvNRankQp'))

# the same tail two other ways, because a tail quoted to one digit must not
# depend on which of three equivalent routes computed it
p_pois = 1.0 - math.exp(-exp_lead) * (1.0 + exp_lead)
p_binom = 1.0 - (1 - p1) ** nunattr - nunattr * p1 * (1 - p1) ** (nunattr - 1)
ck('R1 the exchangeable tail at the observed count agrees to the digit '
   'printed by exact convolution, by the closed binomial form and by the '
   'Poisson limit',
   len({'%.3f' % p_lead, '%.3f' % p_binom, '%.3f' % p_pois}) == 1,
   'convolution %.5f, binomial %.5f, Poisson %.5f' % (p_lead, p_binom,
                                                      p_pois))
ck('R2 the observed count of leaders exceeds the exchangeable expectation, '
   'so the number is worth printing and the clause it supports is not '
   'vacuous', n_obs_lead > exp_lead,
   '%d observed against %.3f expected over %d crossings at 1/%d'
   % (n_obs_lead, exp_lead, nunattr, NCTRL + 1))

m('RkNUnattr', '%d' % nunattr)
m('RkCtrlDen', '%d' % (NCTRL + 1))
m('RkExpLead', '%.2f' % exp_lead)
m('RkProbTwo', '%.3f' % p_lead)
m('RkNObsLead', '%d' % n_obs_lead)

# --- the empirical rate in the two reserved sets, from the frozen layer:
#     every crossing of each set, and how many lead their own controls.
ho_n, ho_lead = int(fnum('HoNCross')), 0
oos_n, oos_lead = int(fnum('OosNCross')), 0
ck('R3 neither reserved set holds a crossing that leads its own control '
   'positions, and the margin is recorded rather than asserted',
   fnum('HoNCtrlMin') > 0 and fnum('OosNCtrlMin') > 0,
   'the fewest controls above the star is %s of %d in the reserved blocks '
   'and %s of %d beyond 40 pc' % (frozen('HoNCtrlMin'), NCTRL,
                                  frozen('OosNCtrlMin'), NCTRL))
m('RkHoN', '%d' % ho_n)
m('RkHoLead', '%d' % ho_lead)
m('RkOosN', '%d' % oos_n)
m('RkOosLead', '%d' % oos_lead)
exp_res = (ho_n + oos_n) * p1
m('RkExpRes', '%.2f' % exp_res)

# =====================================================================
# 3.  THE BROADBAND FLARE PREDICTION'S CHANNEL COUNT
# =====================================================================
# A flare raises every channel of a window by the same flux density, so the
# coherent gain over one channel is sqrt(N_chan).  Drift trials re-read the
# same channels and add nothing, so a CELL count is the wrong N.
XWIN = [q for q in CAT if q['crossing'] == 'True']
nch, ncell = [], []
for q in XWIN:
    n = float(q['bandwidth_Hz']) / float(q['chanw_Hz'])
    assert abs(n - round(n)) < 1e-3, (q['eb'], n)
    nch.append(int(round(n)))
    if q['n_search_cells']:
        ncell.append(float(q['n_search_cells']))
use = ncell if DRIVE == 6 else nch
zlo, zhi = TRIG * math.sqrt(min(use)), TRIG * math.sqrt(max(use))
zmed = TRIG * math.sqrt(float(np.median(use)))

# ★★★★ v4.27: F1 AND F2 WERE DIAGNOSTICS OF A DEFECT THAT HAS SINCE BEEN
# FIXED, AND THEY HAD BEGUN FAILING ON THE CORRECT ANSWER.  As written, F1
# asserted that the PUBLISHED high end is **unreachable** from any channel
# count in the survey -- which was exactly right while the paper printed
# 4,717 sigma (5 sqrt(N) = 4717 needs N = 890,004 and the largest window
# holds 3,769).  A14's recomputation re-pointed `flare_v404.py` at the
# catalogue's channel counts, so the published high end is now 307, it IS
# reachable by construction, and F1 failed the build for the paper carrying
# the corrected number.  F2 was in the same position and survived only on a
# rounding coincidence (the N 307 implies is 3,770 against a largest window
# of 3,769, so "outside the range of channel counts" was true by one).
# This is the round's second-commonest species -- a check that has begun
# failing on the correct answer -- and the repair is to assert the invariant
# the FIX establishes rather than the symptom the defect left:
#   F1  both published ends ARE reproduced by 5 sqrt(N) over the survey's own
#       channel counts, to the digit they are printed to;
#   F2  and the CELL axis does NOT reproduce them, which is what stops anyone
#       re-deriving the range from searched cells and arriving back at 4,717.
# Both can fail: F1 if a future edit re-publishes a number off this axis, F2
# if the two axes ever converge, in which case the distinction the paragraph
# rests on would no longer be measurable and the prose would have to say so.
_hi_ch = TRIG * math.sqrt(max(nch))
_lo_ch = TRIG * math.sqrt(min(nch))
_hi_cell = TRIG * math.sqrt(max(ncell))
if DRIVE == 7:
    _hi_ch *= 2.0
ck('F1 both ends of the published prediction are reproduced by 5 sqrt(N) '
   'over the survey own channel counts, to the digit they are printed to, '
   'so the range is derived from this axis and not from another',
   abs(_hi_ch - fnum('FlPredHi')) <= 1.0
   and abs(_lo_ch - fnum('FlPredLo')) <= 1.0,
   'published %s-%s against %.1f-%.1f from N = %d-%d channels over %d '
   'crossing windows'
   % (frozen('FlPredLo'), frozen('FlPredHi'), _lo_ch, _hi_ch,
      min(nch), max(nch), len(nch)))
_Nhi = (fnum('FlPredHi') / TRIG) ** 2
ck('F2 the SEARCHED CELL axis does not reproduce the published high end, so '
   'the two axes are still distinguishable and the historical 4717 remains '
   'identified as a unit error rather than an arithmetic one',
   abs(_hi_cell - fnum('FlPredHi')) > 10.0,
   'cells %.0f-%.0f give 5 sqrt(N) up to %.0f against the published %s; the '
   'published N is %.0f channels against a largest window of %d'
   % (min(ncell), max(ncell), _hi_cell, frozen('FlPredHi'), _Nhi, max(nch)))
ck('F3 both ends of the recomputed range correspond to a whole number of '
   'channels of a window in this survey, and the check is not vacuous at '
   'the high end as its predecessor was',
   min(use) in nch and max(use) in nch,
   'N = %d to %d channels over %d crossing windows'
   % (min(nch), max(nch), len(nch)))

# ★ NO MACRO IS EMITTED HERE.  The repaired prediction belongs to
# `flare_v404.py`, which owns the names the prose already cites; emitting a
# second pair under new names would leave the paper able to print either.
# What this section contributes is the measurement that generator must
# reproduce, and the checks above fail if it does not.
print('  -> the repaired prediction: N = %d to %d channels, '
      '5 sqrt(N) = %.0f to %.0f (median %.0f)'
      % (min(nch), max(nch), zlo, zhi, zmed))

# the worked example, recomputed on the catalogue's own channel count rather
# than on the frozen input's native one: the published contribution must not
# depend on which of the two is used.
WEG = [q for q in XWIN if q['eb'] == 'A002_Xa42f75_X319']
if WEG:
    negc = float(WEG[0]['bandwidth_Hz']) / float(WEG[0]['chanw_Hz'])
    ck('F4 the worked example\'s contribution is the same on the retained '
       'channel count as on the native one it was measured with, so the '
       'published 0.17 does not move with the repair',
       abs(fnum('FlEgContZ') / math.sqrt(negc) - fnum('FlEgContrib')) < 0.005,
       '%.3f on %d retained channels against the published %s'
       % (fnum('FlEgContZ') / math.sqrt(negc), round(negc),
          frozen('FlEgContrib')))
    pass

# =====================================================================
# EMIT
# =====================================================================
hdr = ['%%%% GENERATED by statunit_v426.py -- do not hand-edit.',
       '%%%% Round %d: the unit of the widened recurrence comparison, the '
       'rank\'s' % ROUND,
       '%% own expectation under exchangeability, and the channel count of the',
       '%% broadband flare prediction.']
lines = ['\n'.join(hdr)]
seen = set()
for k, v in M:
    assert k not in seen, 'duplicate macro ' + k
    seen.add(k)
    lines.append('\\newcommand{\\%s}{%s}' % (k, _minus(v)))
open(OUT, 'w', encoding='utf-8').write('\n'.join(lines) + '\n')
json.dump({k: v for k, v in M}, open(OUTJ, 'w'), indent=1, sort_keys=True)

print('\n%d macros -> %s' % (len(M), os.path.basename(OUT)))
if FAIL:
    print('FAILED: %s' % ', '.join(FAIL))
    raise SystemExit(1)
print('all checks pass')
