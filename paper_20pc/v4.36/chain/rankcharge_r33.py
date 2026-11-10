#!/usr/bin/env python3
r"""rankcharge_r33.py -- round 3340.  ROUND 32, R1-3 AND R1-5: THE LIMITS WITH
THE SPATIAL RANK CHARGED, WINDOW BY WINDOW, AND THE SUMMARIES OVER THE
SYSTEMS WHOSE LIMIT IS NOT EXTRAPOLATED.

R1-3.  The limits are trigger completeness: nine carriers in ten make a
crossing at the star.  The spatial rank (the star's statistic above all of
its window's control positions) is a PRIORITISATION SCREEN, not an acceptance
criterion: crossings that fail it stay in the census, are counted against the
chance expectation and go to the recurrence test like every other
(sens_r11.py docstring; Sec. 3 "From a crossing to a confirmed signal" names
three steps and the rank is not one of them; ledger `screen` is False on most
census rows).  What charging it WOULD cost is printed beside the median
(\SensCostLike, \EirpNinetySysMedARank).  The referee asks whether that x1.27
is uniform.  It is not, and this file says by how much, from the EXISTING
injection trials only (`inject_trials_r30.json`, which sens_r11.py writes and
the deposit carries):
  * the per-window cost (rank-gated over trigger-only ninety-per-cent point,
    each injected window on its own ladder): range, median, the windows that
    never reach ninety per cent with the rank at any injected power (named);
  * the cost per control-ring stratum (sens_r11's own bins), pooled over the
    injected windows in the stratum -- this is the like-for-like factor taken
    apart, and it is what a transferred window can be charged, because the
    ring is the property the rank cost depends on and the catalogue carries
    it for every window;
  * the median over systems and the count at 10^15 W with every window
    charged at its own stratum's cost.  A stratum whose pooled ladder never
    reaches ninety per cent with the rank gives its windows no rank-charged
    limit; a system whose best window is one of them is treated two ways and
    both are printed: it takes its next-best window, or it is unbounded.
R1-5.  The \NgNExtrapSys systems whose best window lies outside the injected
configurations (extrap_r33, the rule of r1_r22): the median and the count at
10^15 W over the other systems, and the counts that say to which limits the
window-to-window dispersion applies.

Every set is derived from the data; nothing names a star or pins a value.
Reads: inject_trials_r30.json, sens_r11.json (ring per injected window, ring
bins, like-for-like cost, per-window points), the catalogue through
adopted_e90, posflag_r31, extrap_r33, refoldpop_r29 (pre-fold ring for the
injected-window join), and the macro layer.  MUST FOLLOW sens_r11.py (pass 2),
numbers_v410.py, smear_r15.py --deposit and r1_r22.py; MUST PRECEDE
retire_macros.py.

  python3 rankcharge_r33.py              # -> numbers/survey_numbers_round3340.tex, rankcharge_r33.json
  python3 rankcharge_r33.py --drive N    # N = 1..15, each must print FAILED: <id> and exit 1
"""
import json
import math
import os
import re
import statistics as st
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import adopted_e90 as ae          # noqa: E402
import posflag_r31 as pf          # noqa: E402
import extrap_r33                 # noqa: E402
import refoldpop_r29              # noqa: E402
import star_alias                 # noqa: E402

ROUND = 3340
DRIVE = None
if '--drive' in sys.argv:
    DRIVE = int(sys.argv[sys.argv.index('--drive') + 1])
SFX = '' if DRIVE is None else '_drive%d' % DRIVE
OUT, FAIL = [], []


def m(k, v):
    assert k.isalpha() and k not in {x.split('}')[0][13:] for x in OUT}, k
    OUT.append('\\newcommand{\\%s}{%s}' % (k, v))


def ck(label, ok, detail=''):
    print('  %-74s %s  %s' % (label[:74], 'PASS' if ok else 'FAIL', detail))
    if not ok:
        FAIL.append(label.split()[0])


def tv(name):
    v = ae._texval(name, HERE)
    assert v is not None, 'macro \\%s is not in the layer' % name
    return v


def tnum(name):
    v = tv(name)
    mm = re.match(r'\s*([0-9.]+)\s*(?:\\times\s*10\^\{?(-?\d+)\}?)?\s*$', v)
    assert mm, (name, v)
    return float(mm.group(1)) * (10.0 ** int(mm.group(2)) if mm.group(2) else 1.0)


def sci(x, nd=1):
    e = int(math.floor(math.log10(x)))
    mant = round(x / 10.0 ** e, nd)
    if mant >= 10.0:
        mant, e = mant / 10.0, e + 1
    return r'%.*f\times10^{%d}' % (nd, mant, e)


def median_inf(vals):
    """median with None read as +infinity (an unbounded system)"""
    xs = sorted(float('inf') if v is None else v for v in vals)
    return st.median(xs)


def name_of(row):
    return star_alias.designation(re.sub(r'^(?:NAME|V\s*star|V\*|\*\*|\*)\s+',
                                         '', row['star_name'])).replace(' ', '~')


def and_list(xs):
    xs = list(xs)
    if not xs:
        return 'none'
    return xs[0] if len(xs) == 1 else ', '.join(xs[:-1]) + ' and ' + xs[-1]


# ====================================================================== inputs
TR = json.load(open(os.path.join(HERE, 'inject_trials_r30.json')))
SENS = json.load(open(os.path.join(HERE, 'sens_r11.json')))
AMPS = [a for a in TR['amps'] if a != TR['positive_control_amp']]
TONES = {w['tag']: w['trials'] for w in TR['windows']}
TAGS = sorted(TONES)
RING = SENS['ring']
BINS = SENS['strat']['bins']
WCAT = SENS['strat']['n_cat']
RULE = float(SENS['ring_rule_sigma'])
COST_LIKE = float(SENS['regression']['cost_like_for_like'])
if DRIVE == 1:            # RC1: one window's trials around its ninety-per-cent point lost
    for _t in TONES[TAGS[0]]:
        if 2.0 < _t['amp'] < 5.0:
            _t['rec'] = _t['trig'] = False


def _cross(amps, fr, want=0.9):
    """sens_r11._cross, verbatim: where a recovery curve first reaches want"""
    prev = None
    for a, f in zip(amps, fr):
        if f is None:
            continue
        if f >= want:
            if prev is None:
                return a
            pa, pf_ = prev
            return pa + (want - pf_) * (a - pa) / (f - pf_) if f > pf_ else a
        prev = (a, f)
    return None


def curve(tags, key):
    out = []
    for a in AMPS:
        tt = [t for g in tags for t in TONES[g] if t['amp'] == a]
        out.append(sum(bool(t[key]) for t in tt) / len(tt) if tt else None)
    return out


def binof(c):
    for i in range(len(BINS) - 1):
        if BINS[i] <= c < BINS[i + 1]:
            return i
    raise ValueError(c)


print('rankcharge_r33: round %d%s' % (ROUND, '' if DRIVE is None
                                      else '  (drive %d)' % DRIVE))
# ============================================================ 1 per window
print('\n1  the rank cost window by window, from the deposited trials')
PER = {g: dict(trig=_cross(AMPS, curve([g], 'trig')),
               rank=_cross(AMPS, curve([g], 'rec'))) for g in TAGS}
_bad = [g for g in TAGS
        if g not in SENS['per_window']
        or abs(PER[g]['trig'] - SENS['per_window'][g]['trig']) > 1e-12
        or (PER[g]['rank'] is None) != (SENS['per_window'][g]['rank'] is None)
        or (PER[g]['rank'] is not None
            and abs(PER[g]['rank'] - SENS['per_window'][g]['rank']) > 1e-12)]
ck('RC1 the deposited trials reproduce sens_r11\'s per-window points, both '
   'criteria, on every injected window',
   not _bad and len(TAGS) == SENS['n_injected'],
   '%d windows, %d differ: %s' % (len(TAGS), len(_bad), _bad[:3]))
# rec = trigger AND rank, so it can only cost
_sub = [g for g in TAGS for t in TONES[g] if t['rec'] and not t['trig']]
COST = {g: (PER[g]['rank'] / PER[g]['trig'] if PER[g]['rank'] is not None
            else None) for g in TAGS}
if DRIVE == 2:
    COST[TAGS[0]] = 0.9
ck('RC2 the rank-charged criterion is a subset of the trigger on every trial, '
   'so no window\'s cost is below one',
   not _sub and all(c >= 1.0 for c in COST.values() if c is not None),
   '%d trials recovered without the trigger; smallest cost %.4f'
   % (len(_sub), min(c for c in COST.values() if c is not None)))
RES = sorted(c for c in COST.values() if c is not None)
UNRES = sorted(g for g in TAGS if COST[g] is None)
if DRIVE == 3:
    UNRES = UNRES + [min((g for g in TAGS if g not in UNRES),
                         key=lambda g: RING[g])]
N_UNRES_PUB = int(tv('SensNRingHiUnres'))
ck('RC3 the windows that never meet the rank are exactly the bright-ring ones '
   'the text counts (\\SensNRingHiUnres), every one above the ring rule',
   len(UNRES) == N_UNRES_PUB and all(RING[g] >= RULE for g in UNRES),
   '%d unresolved (published %d), rings %s against the %.0f rule'
   % (len(UNRES), N_UNRES_PUB, ['%.1f' % RING[g] for g in UNRES], RULE))


def q(xs, p):
    """linear-interpolated quantile, p in [0, 1]"""
    xs = sorted(xs)
    k = p * (len(xs) - 1)
    f = int(math.floor(k))
    return xs[f] if f + 1 >= len(xs) else xs[f] + (k - f) * (xs[f + 1] - xs[f])


Q = {p: q(RES, p) for p in (0.0, 0.1, 0.25, 0.5, 0.75, 0.9, 1.0)}
_lo, _hi = Q[0.0], Q[1.0]
if DRIVE == 4:
    _hi = COST_LIKE * 0.99
ck('RC4 the like-for-like factor lies inside the per-window range, so it is '
   'an average over a spread and not a property of every window',
   _lo <= COST_LIKE <= _hi,
   'x%.3f within x%.3f-x%.3f (median x%.3f, %d resolved)'
   % (COST_LIKE, _lo, _hi, Q[0.5], len(RES)))

# the join of each injected window to its released row ON FREQUENCY AND
# CHANNEL WIDTH (smear_r15's rule, which writes the deposit's p90_basis): the
# round-9 tone records carry the window edges, the round-11 units the
# catalogue's own lower edge.  ★ NOT sens_r11's CATROW rule (block, then the
# nearest pre-fold control maximum to the campaign's ring): two windows of
# one block can carry rings 0.01 apart, and on HD 14055 A002_Xfff3d8_Xd46
# spw3 that rule takes the 330.39 GHz window (5.988, which holds a crossing)
# for the injected 344.22 GHz one (6.000; the campaign measured 5.986).
ROWS = ae.catalogue(HERE)
E = ae.per_window(ROWS, HERE)
CLSA = [r for r in ROWS if r['search_class'] == 'A']
_IX = {}
for r in CLSA:
    _IX.setdefault((r['eb'], round(min(float(r['flo_GHz']), float(r['fhi_GHz'])), 6),
                    round(float(r['chanw_Hz']), 1)), []).append(r)
_EDGE = {}
for t in json.load(open(os.path.join(HERE, 'r9inputs', 'm3a_tones_r9.json'))):
    _EDGE.setdefault(t['tag'], set()).add((round(min(t['fsl'], t['fsh']), 6),
                                           round(t['cw'], 1)))
for u in json.load(open(os.path.join(HERE, 'r11inputs', 'm3a_r11.json')))['units']:
    _EDGE.setdefault(u['tag'], set()).add((round(u['cat_flo_GHz'], 6),
                                           round(u['chanw_Hz'], 1)))
CATROW, _amb = {}, []
for g in TAGS:
    eb = g.rsplit('_spw', 1)[0]
    ed = _EDGE.get(g, set())
    c = _IX.get((eb,) + next(iter(ed)), []) if len(ed) == 1 else []
    if len(c) == 1:
        CATROW[g] = c[0]
    else:
        _amb.append((g, len(ed), len(c)))
_inj_ids = {id(r) for r in CLSA if r['p90_basis'] == 'injected'}
_got = [id(r) for r in CATROW.values()]
if DRIVE == 5:
    _got = _got[1:] + _got[:1]
    _got[0] = _got[1]
ck('RC5 every injected window joins one released row on frequency and channel '
   'width, and the joined rows are exactly the deposit\'s injected rows',
   not _amb and len(CATROW) == len(TAGS) and len(set(_got)) == len(_got)
   and set(_got) == _inj_ids,
   '%d joined, %d distinct, deposit flags %d; unresolved %s'
   % (len(CATROW), len(set(_got)), len(_inj_ids), _amb[:3]))
# reported, not asserted: where sens_r11's ring-nearest join differs
RINGJOIN_DIFF = []
for g, r in CATROW.items():
    cand = [x for x in CLSA if x['eb'] == r['eb']]
    rj = min(cand, key=lambda x: abs(refoldpop_r29.ctrl_max_prefold(x) - RING[g]))
    if rj is not r:
        RINGJOIN_DIFF.append(dict(tag=g, injected_flo=r['flo_GHz'],
                                  ring_join_flo=rj['flo_GHz']))
print('   sens_r11 ring-nearest join differs on %d window(s): %s'
      % (len(RINGJOIN_DIFF), RINGJOIN_DIFF))
UNRES_DESC = []
for g in sorted(UNRES, key=lambda g: (name_of(CATROW[g]), g)):
    r = CATROW[g]
    nu = 0.5 * (float(r['flo_GHz']) + float(r['fhi_GHz']))
    UNRES_DESC.append(dict(tag=g, eb=r['eb'], spw=g.rsplit('_spw', 1)[1],
                           star=r['star_name'], system=r['system_id'],
                           name=name_of(r), nu_GHz=nu, ring=RING[g],
                           ring_cat=float(r['ctrl_max_snr'])))
    print('   never meets the rank: %-34s %s spw%s %.2f GHz ring %.1f'
          % (r['star_name'], r['eb'], g.rsplit('_spw', 1)[1], nu, RING[g]))

# ============================================================ 2 per stratum
print('\n2  the rank cost per control-ring stratum (sens_r11 bins)')
BYBIN = [[] for _ in range(len(BINS) - 1)]
for g in TAGS:
    BYBIN[binof(RING[g])].append(g)
STRATA = []
for i, tg in enumerate(BYBIN):
    t90 = _cross(AMPS, curve(tg, 'trig')) if tg else None
    r90 = _cross(AMPS, curve(tg, 'rec')) if tg else None
    STRATA.append(dict(lo=BINS[i], hi=BINS[i + 1], n_inj=len(tg),
                       n_cat=WCAT[i], trig90=t90, rank90=r90,
                       cost=(r90 / t90 if (r90 and t90) else None),
                       unres=[g for g in tg if COST[g] is None]))
    print('   ring %5.1f-%-6s  %2d injected, %3d catalogue  trig %s rank %s '
          'cost %s' % (BINS[i], ('%.1f' % BINS[i + 1]) if BINS[i + 1] < 1e8
                       else 'up', len(tg), WCAT[i],
                       '%.3f' % t90 if t90 else '-', '%.3f' % r90 if r90
                       else '-', '%.3f' % STRATA[-1]['cost']
                       if STRATA[-1]['cost'] else 'none'))


# the like-for-like factor IS these strata, weighted by the catalogue: rebuilt
def wcurve(key):
    out = []
    for a in AMPS:
        acc = wn = 0.0
        for i, tg in enumerate(BYBIN):
            if not tg or not WCAT[i]:
                continue
            tt = [t for g in tg for t in TONES[g] if t['amp'] == a]
            if tt:
                acc += WCAT[i] * sum(bool(t[key]) for t in tt) / len(tt)
                wn += WCAT[i]
        out.append(acc / wn if wn else None)
    return out


_like = _cross(AMPS, wcurve('rec')) / _cross(AMPS, wcurve('trig'))
if DRIVE == 6:
    _like *= 1.01
ck('RC6 the like-for-like factor is rebuilt from the same trials and strata '
   'this file charges with (one estimator, two uses)',
   abs(_like / COST_LIKE - 1.0) < 1e-9,
   'rebuilt x%.6f against sens_r11 x%.6f' % (_like, COST_LIKE))
_nblind = sum(WCAT[i] for i, s in enumerate(STRATA) if WCAT[i] and not s['n_inj'])
_nores = [s for s in STRATA if s['n_inj'] and s['cost'] is None]
if DRIVE == 7:
    _nores = [s for s in STRATA if s['n_inj']]
ck('RC7 every Class A window lies in a stratum the campaign injected into, and '
   'a stratum without a rank-charged point holds only windows that never met '
   'the rank on their own ladders',
   _nblind == 0 and all(len(s['unres']) == s['n_inj'] for s in _nores),
   '%d windows in uninjected strata; strata without a point: %s'
   % (_nblind, ['%.0f+ (%d/%d unresolved)' % (s['lo'], len(s['unres']),
                                              s['n_inj']) for s in _nores]))

# ============================================================ 3 over systems
print('\n3  the summaries over systems, uncharged and charged')
EL = [r for r in CLSA if ae.limit_eligible(r, HERE)]
BEST = {}
for r in EL:
    s = r['system_id']
    if s not in BEST or E[id(r)] < E[id(BEST[s])]:
        BEST[s] = r
SUM = sorted(s for s in BEST if not pf.is_cond(s))   # the summary set (C14)
N_SUM = int(tv('NSysALimSum'))
LIM = {s: E[id(BEST[s])] for s in SUM}
_med0 = st.median(LIM.values())
_n0 = sum(1 for v in LIM.values() if v <= 1e15)
if DRIVE == 8:
    _n0 += 1
ck('RC8 the uncharged summaries formed here are the published ones (set size, '
   'median at its printed figures, count at 10^15 W)',
   len(SUM) == N_SUM and _n0 == int(tv('NSysEfifteen'))
   and sci(_med0) == tv('EirpNinetySysMedA').replace(' ', ''),
   '%d systems (\\NSysALimSum %d), median %s (\\EirpNinetySysMedA %s), '
   '%d at 1e15 (\\NSysEfifteen %s)'
   % (len(SUM), N_SUM, sci(_med0), tv('EirpNinetySysMedA'), _n0,
      tv('NSysEfifteen')))
# (a) pooled: one factor on every window -- the printed \EirpNinetySysMedARank
POOL = {s: v * COST_LIKE for s, v in LIM.items()}
_medP = st.median(POOL.values())
_nP = sum(1 for v in POOL.values() if v <= 1e15)
_pub = tv('EirpNinetySysMedARank').replace(' ', '')
if DRIVE == 9:
    _medP *= 1.2
ck('RC9 the pooled charge reproduces the printed rank-charged median '
   '(numbers_v410 C2k), so the two charges below are compared with it',
   sci(_medP) == _pub, '%s against \\EirpNinetySysMedARank %s' % (sci(_medP), _pub))


# (b) per stratum: each window at its own ring stratum's cost
def charged(r):
    c = STRATA[binof(float(r['ctrl_max_snr']))]['cost']
    return None if c is None else E[id(r)] * c


CH = {id(r): charged(r) for r in EL}
NEXT, UNB, NOMEET = {}, {}, []
for s in SUM:
    fin = [CH[id(r)] for r in EL if r['system_id'] == s and CH[id(r)] is not None]
    NEXT[s] = min(fin) if fin else None
    if CH[id(BEST[s])] is None:
        NOMEET.append(s)
        UNB[s] = None
    else:
        UNB[s] = NEXT[s]
_medN, _medU = median_inf(NEXT.values()), median_inf(UNB.values())
_nN = sum(1 for v in NEXT.values() if v is not None and v <= 1e15)
_nU = sum(1 for v in UNB.values() if v is not None and v <= 1e15)
_nNinf = sum(1 for v in NEXT.values() if v is None)
_ok10 = (_med0 <= _medN <= _medU and _nU <= _nN <= _n0
         and all(NEXT[s] is None or NEXT[s] >= LIM[s] * (1 - 1e-12) for s in SUM)
         and math.isfinite(_medU))
if DRIVE == 10:
    _ok10 = _ok10 and _medU < _med0
ck('RC10 charging can only raise a limit: uncharged <= next-best <= unbounded '
   'for the median, the reverse for the count, and both medians are finite',
   _ok10,
   'median %.3e <= %.3e <= %.3e; count %d >= %d >= %d'
   % (_med0, _medN, _medU, _n0, _nN, _nU))
NOMEET_DESC = []
for s in NOMEET:
    r = BEST[s]
    NOMEET_DESC.append(dict(system=s, name=name_of(r), eb=r['eb'],
                            nu_GHz=0.5 * (float(r['flo_GHz']) + float(r['fhi_GHz'])),
                            ring=float(r['ctrl_max_snr']), limit=LIM[s],
                            next_best=NEXT[s],
                            injected=r['p90_basis'] == 'injected'))
    print('   best window cannot meet the rank: %-22s %s %.2f GHz ring %.1f; '
          'limit %.2e, next best charged %s'
          % (s, r['eb'], NOMEET_DESC[-1]['nu_GHz'], NOMEET_DESC[-1]['ring'],
             LIM[s], '%.2e' % NEXT[s] if NEXT[s] else 'none'))
print('   uncharged    median %.3e  %d at 1e15' % (_med0, _n0))
print('   pooled x%.3f median %.3e  %d at 1e15' % (COST_LIKE, _medP, _nP))
print('   per stratum, next-best   median %.3e  %d at 1e15 (%d unbounded)'
      % (_medN, _nN, _nNinf))
print('   per stratum, unbounded   median %.3e  %d at 1e15 (%d unbounded)'
      % (_medU, _nU, len(NOMEET)))
# own-window variant, reported only (an injected window charged at its own
# measured cost, every other at its stratum's): the per-window spread
OWN = {}
for s in SUM:
    vals = []
    for r in EL:
        if r['system_id'] != s:
            continue
        g = next((g for g, rr in CATROW.items() if rr is r), None)
        if g is not None:
            vals.append(None if COST[g] is None else E[id(r)] * COST[g])
        else:
            vals.append(CH[id(r)])
    fin = [v for v in vals if v is not None]
    OWN[s] = min(fin) if fin else None
_medO = median_inf(OWN.values())
_nO = sum(1 for v in OWN.values() if v is not None and v <= 1e15)
print('   own-window variant (not printed) median %.3e  %d at 1e15' % (_medO, _nO))

# ============================================================ 4 R1-5
print('\n4  R1-5: the systems whose best window is extrapolated')
CL = extrap_r33.classify(HERE, ROWS, E)
EX = set(CL['ex_sys'])
if DRIVE == 11:
    EX = set()
_npub = int(tv('NgNExtrapSys'))
ck('NG1 the extrapolated systems are r1_r22\'s (count) and each takes its best '
   'window from a transferred row outside the injected range',
   len(EX) == _npub and all(BEST[s]['p90_basis'] != 'injected'
                            and CL['outside'][id(BEST[s])] for s in EX),
   '%d systems against \\NgNExtrapSys %d: %s'
   % (len(EX), _npub, sorted(EX)))
EXB = sorted(s for s in SUM if s in EX)
INT = sorted(s for s in SUM if s not in EX)
_medI = st.median([LIM[s] for s in INT])
_nI = sum(1 for s in INT if LIM[s] <= 1e15)
_nXe = sum(1 for s in EXB if LIM[s] <= 1e15)
_nmeas = sum(1 for s in SUM if BEST[s]['p90_basis'] == 'injected')
_nest = int(tv('SmcNEstSysBnd'))
_ninterp_est = len(INT) - _nmeas
_ok = (len(INT) + len(EXB) == len(SUM) and _nI + _nXe == _n0
       and _nmeas == int(tv('SmcNMeasSysBnd'))
       and _ninterp_est + len(EXB) == _nest and len(INT) > len(SUM) // 2)
if DRIVE == 12:
    _ok = _ok and _nI + _nXe == _n0 + 1
ck('NG2 the interpolated-only sample is the summary set less the extrapolated '
   'systems; measured + interpolated-transferred + extrapolated close on '
   '\\NSysALimSum and the counts at 10^15 W add',
   _ok,
   '%d = %d + %d systems; %d = %d + %d at 1e15; %d measured + %d interpolated '
   '+ %d extrapolated (\\SmcNEstSysBnd %d)'
   % (len(SUM), len(INT), len(EXB), _n0, _nI, _nXe, _nmeas, _ninterp_est,
      len(EXB), _nest))
# the prose claim in Sec. 4.1 ("none of them is among the \NSysEfifteen
# reaching 10^15 W") is true only while the count is zero
_r = ' '.join(open(os.path.join(HERE, 'sections', '05_results.tex')).read().split())
_claim = bool(re.search(r'none of them is among the \\NSysEfifteen', _r))
if DRIVE == 13:
    _nXe, _claim = 1, True
ck('NG3 the sentence saying no extrapolated system reaches 10^15 W is there '
   'only while none does',
   not _claim or _nXe == 0,
   'claim in 05_results: %s; extrapolated systems at 1e15: %d' % (_claim, _nXe))
# the dispersion is attached to the interpolated transfers only: no sentence
# or Table 3 row that quotes it may count \SmcNEstSysBnd as the systems it
# applies to (that count includes the extrapolated ones)
_sites = []
for f in ('sections/app_P_persys.tex', 'tab_budget_r11.tex'):
    p = os.path.join(HERE, f)
    if not os.path.exists(p):
        continue
    t = ' '.join(re.sub(r'(?m)%.*$', '', open(p).read()).split())
    if DRIVE == 14 and f.endswith('app_P_persys.tex'):
        t += (r' The other \SmcNEstSysBnd{} limits carry the dispersion '
              r'$\times\SmcDispLo$ to $\times\SmcDispHi$.')
    # a table row is one unit (its cells are several sentences); prose splits
    # into sentences
    units = (re.split(r'\\\\', t) if f.startswith('tab_')
             else re.split(r'(?<=[.])\s+(?=[A-Z\\])', t))
    for u in units:
        if ('SmcDispLo' in u or 'Window to window' in u) and 'SmcNEstSysBnd' in u:
            _sites.append((f, u[:90]))
ck('NG4 the window-to-window dispersion is never attached to a count that '
   'includes the extrapolated systems',
   not _sites, '%d site(s): %s' % (len(_sites), _sites[:2]))

# ============================================================ macros
m('RcWinCostLo', '%.2f' % Q[0.0])
m('RcWinCostMed', '%.2f' % Q[0.5])
m('RcWinCostHi', '%.2f' % Q[1.0])
m('RcWinCostPten', '%.2f' % Q[0.1])
m('RcWinCostPninety', '%.2f' % Q[0.9])
m('RcNWinCost', '%d' % len(RES))
_WORD = {1: 'one', 2: 'two', 3: 'three', 4: 'four', 5: 'five', 6: 'six'}
_grp = {}
for d in UNRES_DESC:
    _grp[d['name']] = _grp.get(d['name'], 0) + 1
m('RcNoRankWins', and_list('%s toward %s' % (_WORD.get(n, str(n)), nm)
                           for nm, n in sorted(_grp.items(), key=lambda x: (-x[1], x[0]))))
m('RcNoRankFreqLo', '%.1f' % min(d['nu_GHz'] for d in UNRES_DESC))
m('RcNoRankFreqHi', '%.1f' % max(d['nu_GHz'] for d in UNRES_DESC))
_sc = [s['cost'] for s in STRATA if s['cost'] is not None]
m('RcStratCostLo', '%.2f' % min(_sc))
m('RcStratCostHi', '%.2f' % max(_sc))
_nr = [s for s in STRATA if s['n_inj'] and s['cost'] is None]
m('RcNoRankRing', '%.0f' % min(s['lo'] for s in _nr) if _nr else '--')
m('RcNWinNoRankCat', '%d' % sum(s['n_cat'] for s in _nr))
m('RcSysMedStrat', sci(_medN))
m('RcNSysEfifteenStrat', '%d' % _nN)
m('RcSysMedStratUnb', sci(_medU))
m('RcNSysEfifteenStratUnb', '%d' % _nU)
m('RcNSysEfifteenPool', '%d' % _nP)
m('RcNSysNoRank', '%d' % len(NOMEET))
m('RcNoRankSys', and_list(d['name'] for d in NOMEET_DESC))
# ★ the clause about the systems whose best window cannot meet the rank is
#   GENERATED for any count and for either outcome of the two treatments, so
#   the sentence cannot say "either way unchanged" when it is not
_same = sci(_medN) == sci(_medU) and _nN == _nU
_nn = len(NOMEET)
if _nn == 0:
    _cl = 'No system takes its limit from such a window'
else:
    # ★ r34 (Referee 2, item 11): the clause read as if HD 139084 were one of
    # the windows that never met the rank.  It is not: its best window was not
    # injected, and is uncharged because its ring falls in the stratum whose
    # injected windows never met the rank.  Say which best window was injected
    # and which was not, and which system has no chargeable window at all.
    _inj = [d['name'] for d in NOMEET_DESC if d['injected']]
    _ninj = [d['name'] for d in NOMEET_DESC if not d['injected']]
    _nonext = [d['name'] for d in NOMEET_DESC if d['next_best'] is None]
    _UN_EB = {d['eb'] for d in UNRES_DESC}
    _nmd = NOMEET_DESC
    if DRIVE == 15:                # a best window's injection status misread
        _nmd = [dict(d, injected=not d['injected']) if i == 0 else d
                for i, d in enumerate(NOMEET_DESC)]
    ck('RC11 a best window that cannot be charged is one of the injected '
       'windows that never met the rank exactly when it was injected, and '
       'otherwise lies in their ring stratum',
       all((d['eb'] in _UN_EB) == d['injected'] for d in _nmd)
       and all(STRATA[binof(d['ring'])]['cost'] is None for d in _nmd),
       '; '.join('%s %s ring %.1f %s' % (d['name'], d['eb'], d['ring'],
                                          'injected' if d['injected'] else 'not injected')
                 for d in _nmd))
    # r34 phase 3 (readability): two plain sentences instead of one with two parentheticals and a semicolon; the
    # clause now OPENS a sentence (the prose ends the previous one before it).
    _bits = []
    if _inj:
        _bits.append('%s %s one of those %s windows' % (
            ' and '.join(n + '\\textquoteright s' for n in _inj),
            'is' if len(_inj) == 1 else 'are', _WORD.get(len(UNRES_DESC), str(len(UNRES_DESC)))))
    if _ninj:
        _bits.append('%s %s not injected' % (
            ' and '.join(n + '\\textquoteright s' for n in _ninj),
            'was' if len(_ninj) == 1 else 'were'))
    _cl = ('The best window%s of \\RcNoRankSys{} ha%s a ring as bright, so the rank cannot be charged on %s. '
           '%s. Counting %s at %s next-best window that can be charged, or as having no limit%s, '
           % ('' if _nn == 1 else 's', 's' if _nn == 1 else 've',
              'it' if _nn == 1 else 'either' if _nn == 2 else 'any',
              (', while '.join(_bits))[0].upper() + (', while '.join(_bits))[1:],
              'it' if _nn == 1 else 'each', 'its',
              (' where it has none (%s)' % ' and '.join(_nonext)) if _nonext else ''))
    _cl += ('leaves the median and the count just given unchanged' if _same else
            'gives a median of $\\RcSysMedStrat$ or $\\RcSysMedStratUnb$\\,W, with '
            '\\RcNSysEfifteenStrat{} or \\RcNSysEfifteenStratUnb{} systems at $10^{15}$\\,W')
m('RcNoRankSysClause', _cl)
m('NgSysMedInterp', sci(_medI))
m('NgNSysEfifteenInterp', '%d' % _nI)
m('NgNSysInterpSum', '%d' % len(INT))
m('NgNExtrapSysBnd', '%d' % len(EXB))
m('NgNInterpEstSysBnd', '%d' % _ninterp_est)
m('NgNExtrapSysEfifteen', '%d' % _nXe)

doc = dict(generated_by=os.path.basename(__file__), round=ROUND, drive=DRIVE,
           per_window_cost={g: COST[g] for g in TAGS},
           per_window_quantiles={str(k): v for k, v in Q.items()},
           n_resolved=len(RES), never_meets_rank=UNRES_DESC,
           cost_like_for_like=COST_LIKE, strata=STRATA,
           summaries=dict(n=len(SUM), uncharged=dict(median=_med0, n_1e15=_n0),
                          pooled=dict(median=_medP, n_1e15=_nP),
                          stratified_next_best=dict(median=_medN, n_1e15=_nN,
                                                    n_unbounded=_nNinf),
                          stratified_unbounded=dict(median=_medU, n_1e15=_nU,
                                                    n_unbounded=len(NOMEET)),
                          own_window_variant=dict(median=_medO, n_1e15=_nO)),
           best_cannot_meet_rank=NOMEET_DESC,
           r1_5=dict(extrap_systems=[dict(system=s, name=name_of(BEST[s]),
                                          eb=BEST[s]['eb'],
                                          nu_GHz=0.5 * (float(BEST[s]['flo_GHz'])
                                                        + float(BEST[s]['fhi_GHz'])),
                                          chanw_kHz=float(BEST[s]['chanw_Hz']) / 1e3,
                                          limit_W=E[id(BEST[s])],
                                          outside=CL['outside'][id(BEST[s])],
                                          in_summaries=s in SUM)
                                     for s in sorted(EX)],
                     interp_only=dict(n=len(INT), median=_medI, n_1e15=_nI),
                     n_measured=_nmeas, n_interp_transferred=_ninterp_est),
           macros={x.split('}')[0][13:]: x.split('}{', 1)[1][:-1] for x in OUT},
           ringjoin_diff=RINGJOIN_DIFF, failures=FAIL)
json.dump(doc, open(os.path.join(HERE, 'rankcharge_r33%s.json' % SFX), 'w'),
          indent=1, sort_keys=True, default=str)
if DRIVE is None and not FAIL:
    with open(os.path.join(HERE, 'numbers/survey_numbers_round%d.tex' % ROUND),
              'w') as fh:
        fh.write('%% GENERATED by rankcharge_r33.py (round %d) -- do not '
                 'hand-edit.\n' % ROUND)
        fh.write('\n'.join(sorted(OUT)) + '\n')
print('\n%d macros%s' % (len(OUT), '' if DRIVE is None or FAIL else ' (drive: not written)'))
if FAIL:
    print('FAILED: %s' % ' '.join(FAIL))
    sys.exit(1)
