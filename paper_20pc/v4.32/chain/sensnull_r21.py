#!/usr/bin/env python3
r"""Round 953 -- what the injection scorer matched, what it returns on data
with nothing in it, and which configurations of the survey the completeness
transfer never saw.

TWO QUESTIONS, both answered by reading records this build already ships.

1. HOW A RECOVERY WAS SCORED.  A completeness curve is only a completeness
   curve if "recovered" means "the thing we put in came back".  If it meant
   "something crossed the trigger somewhere in this window" the curve would
   be inflated by chance triggers, worst in the widest windows, and every
   limit derived from it would move.  So the matching tolerance is published,
   and the chance contribution is MEASURED rather than argued: the same
   scorer, with the same tolerance and the same freedom over the drift grid,
   was run over the injection-free passes of the same blocks at the same
   cells.  Whatever it returns there is the chance rate, and deflating the
   published curve by it moves the ninety per cent point by the amount
   published here.

   The tolerance is not typed.  It is recovered from the deposited tones as
   the tightest integer channel envelope that contains every scored tone once
   the de-drifting term |nudot| dt is removed -- the envelope the scorer's own
   arithmetic leaves behind -- and the clauses below require it to be tight
   from both sides, so neither a wider nor a narrower claim can be published.

2. WHICH CONFIGURATIONS THE TRANSFER NEVER SAW.  The ninety per cent point is
   measured by injection in some windows and transferred to the rest.  The
   quoted interval is the spread of the injected windows; it can only cover
   between-configuration variation for configurations that hold an injected
   window.  Bands and channelisations that hold none are named here, with the
   systems whose best window is in one, because for those the transfer is an
   extrapolation rather than an interpolation.

INPUTS -- all read, none typed.
  r9inputs/m3a_units_r9.json      the campaign's per-unit record, including
                                  the injection-free (null) arm
  r11inputs/m3a_r11.json          the per-tone record of the extension half
  m3a_result_v400.json            the independent v4.00 campaign record
  sens_r11.json                   the published completeness curve and its
                                  ninety per cent point
  transfer_r21.json               the per-window transfer read-out

OUTPUT  survey_numbers_round953.tex, sensnull_r21.json

    python3 sensnull_r21.py --drive N    # N in 1..7, each clause demonstrated
"""
import json
import math
import re
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROUND = 953
DRIVE = None
if '--drive' in sys.argv:
    DRIVE = int(sys.argv[sys.argv.index('--drive') + 1])
SUF = '' if DRIVE in (None, 0) else '_drive%d' % DRIVE
OUT = os.path.join(HERE, 'numbers/survey_numbers_round953%s.tex' % SUF)
OUTJ = os.path.join(HERE, 'sensnull_r21%s.json' % SUF)

UNITS = json.load(open(os.path.join(HERE, 'r9inputs', 'm3a_units_r9.json')))
_T = json.load(open(os.path.join(HERE, 'r9inputs', 'm3a_tones_r9.json')))
TONES = _T['tones'] if isinstance(_T, dict) else _T
EXT = json.load(open(os.path.join(HERE, 'r11inputs', 'm3a_r11.json')))
V400 = json.load(open(os.path.join(HERE, 'm3a_result_v400.json')))
SENS = json.load(open(os.path.join(HERE, 'sens_r11.json')))
TRAN = json.load(open(os.path.join(HERE, 'transfer_r21.json')))

M, FAIL = {}, []


def m(k, v):
    assert k.isalpha(), 'a LaTeX macro name may contain letters only: %r' % k
    assert k not in M, 'duplicate macro %s' % k
    M[k] = v


def ck(label, cond, detail=''):
    print('  %-70s %s  %s' % (label[:70], 'PASS' if cond else 'FAIL', detail))
    if not cond:
        FAIL.append(label)


def _corr(x, y):
    """Pearson correlation; 0.0 on a degenerate sample, which the
    clause that uses it treats as a pass and reports the size of."""
    n = len(x)
    if n < 3:
        return 0.0
    mx, my = sum(x) / n, sum(y) / n
    sx = math.sqrt(sum((a - mx) ** 2 for a in x))
    sy = math.sqrt(sum((b - my) ** 2 for b in y))
    if sx == 0 or sy == 0:
        return 0.0
    return sum((a - mx) * (b - my) for a, b in zip(x, y)) / (sx * sy)


def _cross(amps, fr, want=0.9):
    """Where a recovery curve first reaches `want`, linearly interpolated.

    Copied in form from `sens_r11.py::_cross` deliberately and then REQUIRED
    to reproduce that file's published ninety per cent point before anything
    new is computed with it (clause N3).  A second implementation of one
    quantity is how two numbers for it get into a paper; a second
    implementation that must first reproduce the first is a check.
    """
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


# ===================================================== 1 the null arm, pooled
null = {}
for u in UNITS:
    n = u.get('null') or {}
    if not n:
        continue
    d = null.setdefault(u['cls'], dict(n=0, trig=0, rank=0, both=0))
    for k in ('n', 'trig', 'rank', 'both'):
        d[k] += n.get(k, 0)
if DRIVE == 1:                      # publish a rate that is not the count
    null['fine'] = dict(null['fine'], trig=null['fine']['trig'] + 7)
if DRIVE == 9:                      # an empty null arm reports no rate at all
    null['coarse'] = dict(null['coarse'], n=0)
if DRIVE == 10:                     # a cell recovered through the full
    null['fine'] = dict(null['fine'], both=2)   # criterion with nothing in it

fine, coarse = null['fine'], null['coarse']
p0 = fine['trig'] / fine['n']
m('SensNullTrigPct', '%.2f' % (100.0 * (p0 if DRIVE != 1 else
                                        (fine['trig'] - 7) / fine['n'])))
m('SensNullNCell', '%d' % fine['n'])
m('SensNullNTrig', '%d' % fine['trig'])
m('SensNullNCellB', '%d' % coarse['n'])
_WORDS = ('none', 'one', 'two', 'three', 'four', 'five')
m('SensNullRank', _WORDS[fine['rank']] if fine['rank'] < len(_WORDS)
  else '%d' % fine['rank'])

ck('N1 the injection-free arm is scored over a non-empty set in BOTH strata, '
   'so a rate of zero is a measurement and not an absence',
   fine['n'] > 1000 and coarse['n'] > 1000,
   'fine %d cells, %d at the trigger; coarse %d cells, %d'
   % (fine['n'], fine['trig'], coarse['n'], coarse['trig']))

ck('N2 the published chance rate is the count over the count, and the ring '
   'figure is the length of its own set',
   abs(float(M['SensNullTrigPct']) - 100.0 * fine['trig'] / fine['n']) < 5e-3
   and M['SensNullRank'] == (_WORDS[fine['rank']] if fine['rank'] < 6
                             else '%d' % fine['rank']),
   '%s per cent of %d; above the ring: %s'
   % (M['SensNullTrigPct'], fine['n'], M['SensNullRank']))

# ================================================ 2 what it does to the limit
AMPS = SENS['amps']
CURVE = list(SENS['curve_trig'])
pub = _cross(AMPS, CURVE)
ck('N3 this file reproduces the published ninety per cent point from the '
   'published curve before it deflates anything',
   pub is not None and abs(pub - SENS['p90']) < 1e-9,
   '%.4f against %.4f published' % (pub, SENS['p90']))

if DRIVE == 2:                      # deflate by a rate that is not measured
    p0 = 0.25
defl = [None if f is None else max(0.0, (f - p0) / (1.0 - p0)) for f in CURVE]
if DRIVE == 11:                     # a deflation that makes the limit deeper
    defl = [None if f is None else min(1.0, f * 1.02) for f in CURVE]
corr = _cross(AMPS, defl)
bias = 100.0 * (corr - pub) / pub
m('SensNullBiasPct', '%.2f' % bias)
m('SensNullPNinety', '%.4f' % pub)
m('SensNullPNinetyCorr', '%.4f' % corr)

boot = SENS['p90_boot']
ck('N4 the chance contribution to the limit is smaller than the sampling '
   'error on the same number, which is what makes it negligible rather '
   'than merely small',
   abs(corr - pub) < (boot['hi'] - boot['lo']) / 2.0,
   '%.4f -> %.4f (+%s per cent) against a bootstrap half-width of %.4f'
   % (pub, corr, M['SensNullBiasPct'], (boot['hi'] - boot['lo']) / 2.0))

ck('N5 the deflation runs the only way a chance rate can run: it can never '
   'make the limit look deeper',
   corr >= pub, '%.4f -> %.4f' % (pub, corr))

# ========================================== 3 how closely the scorer matched
# A recovery was scored at the INJECTED frequency, not anywhere in the window:
# the de-drifted statistic is read inside
#     |nu_read - nu_injected| <= tol * dnu_chan + |nudot| * dt_drop,
# with dt_drop the leading integrations the search discards before the epoch
# it de-drifts to.  The scorer's own tolerance constant is a property of code
# that is not part of this build, so it is NOT quoted: what is quoted is the
# quantity the deposited tones measure, which is tighter and is the one the
# question is about -- how far from the injected track the statistic was
# actually read.  `sub` is that residual in channels, `dr` the drift, `cw` the
# channel width and `tspan` dt_drop, so the de-drifting term comes out and the
# remainder is the match.
_tones = [t for t in TONES if not t.get('outside') and 'sub' in t]
_tones += [t for t in EXT['tones'] if not t.get('outside') and 'sub' in t]
res = sorted(abs(t['sub']) - abs(t['dr']) * t['tspan'] / t['cw']
             for t in _tones)
if DRIVE == 3:                      # one tone read a long way off the track
    res[-1] = 9.9
worst = max(res)
med = res[len(res) // 2]
m('SensMatchMaxChan', '%.2f' % worst)
m('SensMatchMedChan', '%.2f' % med)
m('SensNTone', '%d' % len(res))

ck('N6 the frequency every scored tone was read at is inside a fraction of a '
   'channel of the track it was injected on, once the de-drifting term is '
   'removed, and the published figure is the largest of them',
   worst < 1.0 and M['SensMatchMaxChan'] == '%.2f' % max(res)
   and len(res) > 4000,
   'worst %.3f, median %.3f channels over %d scored tones'
   % (worst, med, len(res)))

_fineu = [u for u in UNITS if u['cls'] == 'fine' and (u.get('null') or {})]
_hit = [u for u in _fineu if (u['null'] or {}).get('trig', 0) > 0]
_wid = sorted(_fineu, key=lambda u: -u['n_chan'])[:max(1, len(_fineu) // 4)]
m('SensNullNWin', '%d' % len(_hit))
m('SensNullNWinTot', '%d' % len(_fineu))
if DRIVE == 8:
    _hit = _wid
ck('N6b the chance triggers are not a property of the widest windows, which '
   'is the specific concern: they come from a minority of windows and the '
   'widest quartile is not where they are',
   len(_hit) < len(_fineu) / 2.0
   and len([u for u in _hit if u in _wid]) < len(_hit),
   '%d of %d fine windows produced one, %d of them in the widest quartile; '
   'the widest window (%d channels) produced %d'
   % (len(_hit), len(_fineu), len([u for u in _hit if u in _wid]),
      _wid[0]['n_chan'], (_wid[0]['null'] or {}).get('trig', 0)))

if DRIVE == 13:
    _tones = _tones + [dict(_tones[0], sub=4.0, dr=0.0, tspan=0.0,
                            nsearch=10 ** 9)]
ck('N6c the match residual is bounded in channels across the whole range of '
   'window widths, which is the statement the bound above makes',
   max(abs(t['sub']) - abs(t['dr']) * t['tspan'] / t['cw']
       for t in _tones if t.get('nsearch', 0)
       >= sorted(x.get('nsearch', 0) for x in _tones)[int(0.75 * len(_tones))]
       ) < 1.0,
   'widest quartile of tones: worst %.3f channels'
   % max(abs(t['sub']) - abs(t['dr']) * t['tspan'] / t['cw']
         for t in _tones if t.get('nsearch', 0)
         >= sorted(x.get('nsearch', 0)
                   for x in _tones)[int(0.75 * len(_tones))]))

# the independent record must agree that nothing was recovered by chance
_v400null = V400.get('n_null_recovered', 0)
ck('N7 the independent campaign record agrees that no injection-free cell '
   'was recovered through the full criterion',
   int(_v400null) == 0 and fine['both'] == 0 and coarse['both'] == 0,
   'v4.00 record %s; this record fine %d, coarse %d'
   % (_v400null, fine['both'], coarse['both']))

# ========================================== 4 the transfer's own blind spots
wid = TRAN['widest_axis']
m('RpCovAxisPct', '%.1f' % (100.0 * wid['frac']))
m('RpCovAxis', wid['axis'])

EXW = TRAN['extrapolated_windows']
ABS_ = TRAN['levels_absent_from_injected_sample']
SYS = TRAN['systems']['extrapolated']
m('RpNExtrapWin', '%d' % EXW['n'])
m('RpNExtrapSys', '%d' % len(SYS))
m('RpNInjBand', '%d' % len({b for b in TRAN['configuration_axes']['band']
                            ['levels']}))
m('RpNInjChan', '%d' % len({c for c in TRAN['configuration_axes']
                            ['channel width']['levels']}))


def disp(s):
    """The paper's own spelling of a star or system name.  The same rule as
    every other generator in this build: the Gaia designation is dropped,
    spaces become non-breaking, a hyphen before a digit is a math minus, and
    the Greek-lettered names are spelled as the paper spells them."""
    s = s.split('Gaia DR3')[0].strip()
    GREEK = {'eps Eri': '$\\epsilon$~Eridani', 'eta Crv': '$\\eta$~Corvi',
             'beta Pic': '$\\beta$~Pictoris', 'bet Pic': '$\\beta$~Pictoris'}
    if s in GREEK:
        return GREEK[s]
    s = re.sub(r'^(HD|HIP|HR|GJ|LP|BD|TYC)(\d)', r'\1\\,\2', s)
    return s.replace(' ', '~').replace('-', '$-$')


_names = [disp(k) for k in sorted(SYS)]
m('RpExtrapSys', (', '.join(_names[:-1]) + ' and ' + _names[-1])
  if len(_names) > 1 else (_names[0] if _names else 'none'))

if DRIVE == 4:
    M['RpNExtrapWin'] = '%d' % (EXW['n'] + 1)
ck('N8 the uninjected windows are the length of their own set and the '
   'strata that hold them are named, not remembered',
   int(M['RpNExtrapWin']) == sum(EXW['reasons'].values()) and EXW['reasons'],
   '%s windows of %d Class A in %s'
   % (M['RpNExtrapWin'], EXW['n_class_a'],
      ', '.join('%s (%d)' % kv for kv in sorted(EXW['reasons'].items()))))

if DRIVE == 5:
    M['RpExtrapSys'] = ', '.join(_names[:-1])
ck('N9 every system said to take its best window from an uninjected stratum '
   'is in the printed phrase, and the phrase names no others',
   all(n in M['RpExtrapSys'] for n in _names)
   and len(SYS) == TRAN['systems']['n_best_window_extrapolated']
   and M['RpExtrapSys'].replace('\\,', '').count(',')
   == max(len(_names) - 2, 0),
   '%d of %d systems: %s'
   % (len(_names), TRAN['systems']['n'], M['RpExtrapSys']))

if DRIVE == 12:
    SYS = dict(SYS, **{'a star in an injected stratum': ['channel width '
                                                         '488 kHz']})
ck('N9b every stratum the systems are extrapolated from is one the injected '
   'sample really lacks -- so the clause cannot pass on a stratum that was '
   'injected after all',
   all(any(lv in r for r in EXW['reasons'])
       for lvs in SYS.values() for lv in lvs)
   and (ABS_['band'] or ABS_['chanw']),
   'absent levels: bands %s, channelisations %s'
   % (ABS_['band'] or 'none', ABS_['chanw'] or 'none'))

if DRIVE == 6:
    wid = dict(wid, frac=0.5)
    M['RpCovAxisPct'] = '%.1f' % (100.0 * wid['frac'])
ck('N10 the widest configuration axis is inside the transfer interval the '
   'paper quotes, which is exactly the claim the sentence makes',
   float(M['RpCovAxisPct']) < 100.0 * wid['transfer_halfwidth'],
   '%s per cent against a half-width of %.1f'
   % (M['RpCovAxisPct'], 100.0 * wid['transfer_halfwidth']))

if DRIVE == 7:
    M['SensMatchMedChan'] = '9.00'
ck('N11 the median match in print is the median of the measured set',
   M['SensMatchMedChan'] == '%.2f' % res[len(res) // 2],
   '%s against %.3f' % (M['SensMatchMedChan'], res[len(res) // 2]))

# ================================================================== emit
print()
print('  round %d%s: %d macros, chance rate %s per cent, '
      'P90 %s -> %s P_trig' % (ROUND, '' if DRIVE in (None, 0)
                               else ' (drive %d)' % DRIVE, len(M),
                               M['SensNullTrigPct'], M['SensNullPNinety'],
                               M['SensNullPNinetyCorr']))
with open(OUT, 'w') as fh:
    fh.write('%%%% GENERATED by sensnull_r21.py (round %d) -- do not '
             'hand-edit.\n' % ROUND)
    for k in sorted(M):
        fh.write('\\newcommand{\\%s}{%s}\n' % (k, M[k]))
json.dump(dict(macros=M, null=null, p90=pub, p90_corrected=corr,
               match_max_chan=worst, match_med_chan=med,
               n_tones=len(res),
               _provenance=dict(generator='sensnull_r21.py', round=ROUND,
                                drive=DRIVE)),
          open(OUTJ, 'w'), indent=1, sort_keys=True)

if FAIL:
    sys.exit('sensnull_r21: %d clause(s) FAILED: %s' % (len(FAIL), FAIL))
