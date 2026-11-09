#!/usr/bin/env python3
r"""rankpairs_r28.py -- round 2810.  Two chance rates the paper printed in the
wrong form or not at all, both computed from the census's own control
ensembles over the windows and with the weights of Appendix D.1.

Writes `survey_numbers_round2810.tex` and `rankpairs_r28.json`.

1. THE RANK'S CHANCE RATE, CONDITIONAL ON THE TRIGGER (Referee 2, M1).  The
   unattributed crossings the rank is read over were SELECTED on T* >= 5, so
   the unconditional 1/(n_ctrl+1) that the star leads its field is not their
   chance rate: what is needed is P(star leads | T* >= 5), which is large
   wherever few controls reach the trigger.  It is estimated, window by window,
   exactly as the referee specifies: of the controls reaching the trigger, the
   fraction exceeding every other position of the window (the star included);
   that fraction weights the window's own unattributed chance expectation --
   the term Appendix D.1 sums to \CeExp -- and the sum is the number of
   rank-leading crossings chance predicts.  The unconditional figure is not
   computed here or anywhere: it is the wrong quantity.

2. HOW MANY OPEN PAIRS CHANCE PREDICTS (Referee 2, M2(c)).  Table 5's pairs
   are pairs of crossings toward one star, in two blocks, within the
   +-\WdHalfKms km/s window, and a pair is `open' when one bounded trajectory
   inside the drift grid joins the two -- which, for a pair whose interval is
   long enough, is whenever |dnu| <= dnu_max * dt.  So the chance expectation
   of open pairs is a sum over pairs of census windows toward one star in two
   blocks of (rate in one) x (rate in the other) x P(two random above-trigger
   cells, one per window, are joinable), each rate the window's own D.1 term
   and each cell uniform over its window's stellar-frame band.  The joining
   probability is exact for uniform cells (the difference of two uniforms has
   a trapezoidal law).  Where both blocks carry only a SHARED stored stamp
   (`epochs_r14`: the member-OUS artefact) the interval is unknown; such pairs
   are counted as never joinable for the lower end and as always joinable for
   the upper end, and both ends are published.  The comparison is over the
   census only (Ruling R4): pairs with a member in an archival-tail window
   enter neither side.

Inputs: chance_perwin_v422.json and chance_v414.json (chance_v414.py),
pairs_v415.json (pairs_v415.py), per_target_results_v3.99.csv,
pbaudit_v408/pbgeom.json, epochs_r14 and maskframe_v411 and star_alias as
modules, and the macro layer for \WdHalfKms and \EvNRankQp.

Drives (each writes *_driveN.* only and must make its own assertion fail):
1 the unconditional 1/(n+1) comes back (K2); 2 the tail read at P(>=1) when
two are observed (K3); 3 the sign of the uniform-difference law reversed
(K4); 4 the tail pairs counted as census pairs (K5); 5 a colliding name key
(the catalogue prefix alone) merging different stars into one group (K6); 6 the deposit joined to the catalogue off by one row
(K1); 7 the census and with-tail populations of the orbital route swapped
(K7); 8 a tail crossing counted into the observed side (K2b, Ruling R18).

    python3 -I -B rankpairs_r28.py [--drive N]
"""
import collections
import csv
import glob
import itertools
import json
import math
import os
import re
import sys

import numpy as np
from scipy.special import gammainc

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import epochs_r14 as EP                                          # noqa: E402
import maskframe_v411 as mf                                      # noqa: E402
import star_alias as sa                                          # noqa: E402

ROUND = 2810
DRIVE = int(sys.argv[sys.argv.index('--drive') + 1]) if '--drive' in sys.argv \
    else 0
SFX = '' if DRIVE == 0 else '_drive%d' % DRIVE
OUT = os.path.join(HERE, 'numbers/survey_numbers_round2810%s.tex' % SFX)
OUTJ = os.path.join(HERE, 'rankpairs_r28%s.json' % SFX)
CKMS = 299792.458
POS_TOL = 2.0                      # arcsec, as pairs_v415.py

M, FAIL = [], []


def m(k, v):
    assert k.isalpha(), 'a LaTeX macro name may contain letters only: ' + k
    assert k not in dict(M), 'macro defined twice: ' + k
    M.append((k, str(v)))


def ck(name, cond, detail=''):
    if not cond:
        FAIL.append(name)
    print('  %-70s %s  %s' % (name[:70], 'PASS' if cond else 'FAIL', detail))


def macro(name):
    """One macro's value from the frozen layer (never this round's output)."""
    pat = re.compile(r'\\newcommand\{\\%s\}\{(.*)\}\s*$' % name)
    got = None
    for p in sorted(glob.glob(os.path.join(HERE, 'numbers/survey_numbers*.tex'))):
        if '_drive' in p or '_field' in p or 'round2810' in p:
            continue
        for line in open(p, errors='ignore'):
            mm = pat.match(line.strip())
            if mm:
                got = mm.group(1)
    if got is None:
        raise KeyError(name)
    return got


def word(n):
    return ['no', 'one', 'two', 'three', 'four', 'five', 'six', 'seven',
            'eight', 'nine', 'ten'][n] if 0 <= n <= 10 else '%d' % n


def p_ge(k, lam):
    """Poisson P(N >= k)."""
    return 1.0 if k <= 0 else float(gammainc(k, lam))


# ------------------------------------------------------------------ inputs
CAT = list(csv.DictReader(open(os.path.join(HERE,
                                            'per_target_results_v3.99.csv'))))
IA = [i for i, r in enumerate(CAT) if r['search_class'] == 'A']
PW = json.load(open(os.path.join(HERE, 'chance_perwin_v422.json')))
CH = json.load(open(os.path.join(HERE, 'chance_v414.json')))
PAIRS = json.load(open(os.path.join(HERE, 'pairs_v415.json')))['pairs']
GEO = json.load(open(os.path.join(HERE, 'pbaudit_v408', 'pbgeom.json')))
HALF = float(macro('WdHalfKms'))

# K1 -- the per-window deposit is in the catalogue's own Class A order (that is
# how chance_v414.py writes it); the join is by that order and is VALIDATED row
# by row on three fields, never assumed.
ROWS = PW['rows']
_off = 1 if DRIVE == 6 else 0
JOINBAD = []
WIN = []
for k, i in enumerate(IA):
    w = ROWS[(k + _off) % len(ROWS)]
    r = CAT[i]
    if (w['eb'] != r['eb'] or abs(w['rms_mJy'] - float(r['rms_mJy'])) > 1e-4
            or abs(w['star_snr'] - float(r['star_snr'])) > 1e-3):
        JOINBAD.append(i)
    if w['n_ctrl_trig'] is None:
        continue
    fac = (1.0 - w['mask_attr_share']) * w['telluric_factor']
    WIN.append(dict(i=i, eb=r['eb'], star=r['star_name'],
                    sysid=r['system_id'], n=w['n_ctrl'], n5=w['n_ctrl_trig'],
                    lead=w['ctrl_lead_trig'], fac=fac,
                    lam=w['n_ctrl_trig'] / float(w['n_ctrl']) * fac,
                    flo=float(r['flo_GHz']), fhi=float(r['fhi_GHz']),
                    dmax=float(r['drift_max_Hz_s'])))
E_CEN = sum(w['lam'] for w in WIN)
ck('K1 the per-window deposit joins the catalogue row for row (block, rms, '
   'star statistic) and its weights sum to the published chance expectation',
   not JOINBAD and len(ROWS) == len(IA)
   and abs(E_CEN - CH['e_chance']) < 1e-9
   and abs(E_CEN - float(macro('CeExp'))) < 0.05,
   '%d of %d rows disagree; sum %.4f against chance_v414 %.4f and the printed '
   '%s' % (len(JOINBAD), len(IA), E_CEN, CH['e_chance'], macro('CeExp')))

# =========================================================== 1.  THE RANK
# Route (a): the referee's construction, window rate x conditional fraction.
RK_Q = {}
for w in WIN:
    q = (w['lead'] / float(w['n5'])) if w['n5'] else 0.0
    if DRIVE == 1:                       # the unconditional rate comes back
        q = 1.0 / (w['n'] + 1.0)
    RK_Q[w['i']] = q
RK_EXP = sum(w['lam'] * RK_Q[w['i']] for w in WIN)
# Route (b): straight off the deposited columns, lead / n_ctrl x factor.
RK_EXP_B = sum(w['lead'] / float(w['n']) * w['fac'] for w in WIN)
OBS = CH['observed_rows']
RK_OBS = [r for r in OBS if r['rank_ctrl'] is not None
          and r['tstar'] is not None and r['tstar'] > r['rank_ctrl']]
N_LEAD_WIN = sum(w['lead'] for w in WIN)
ck('K2 the rank expectation is the CONDITIONAL one: two routes through the '
   'deposit agree, every conditional fraction is a probability, the '
   'expectation cannot exceed the chance expectation it is a share of, and '
   'the observed leaders are a subset of the ledger\'s own',
   abs(RK_EXP - RK_EXP_B) < 1e-9
   and all(0.0 <= q <= 1.0 for q in RK_Q.values())
   and RK_EXP <= E_CEN
   and len(RK_OBS) <= int(macro('EvNRankQp'))
   and len(OBS) == CH['observed'],
   '%.4f by the conditional fraction, %.4f off the columns; %d of %d windows '
   'have a leading above-trigger control; observed %d of %d (ledger %s)'
   % (RK_EXP, RK_EXP_B, N_LEAD_WIN, len(WIN), len(RK_OBS), len(OBS),
      macro('EvNRankQp')))
K_OBS = len(RK_OBS)
K_TAIL = 1 if DRIVE == 2 else K_OBS
RK_P = p_ge(K_TAIL, RK_EXP)
_pmf = sum(math.exp(-RK_EXP) * RK_EXP ** j / math.factorial(j)
           for j in range(K_OBS))
ck('K3 the tail is read at the OBSERVED count, by the regularised gamma '
   'function and by the summed Poisson terms alike',
   abs(RK_P - (1.0 - _pmf)) < 1e-12,
   'P(N >= %d | %.4f) = %.5f, summed terms %.5f'
   % (K_OBS, RK_EXP, RK_P, 1.0 - _pmf))
# ★ round-28 Ruling R18 (merger): the comparison is over the CENSUS's unattributed crossings -- the ledger
# less the archival tail, quality-passing -- never the 52/56 that include the tail.  The observed side is
# chance_v414's own comparison rows (the census Class A unattributed crossings it compares with chance); they
# must lie inside that census set, keyed on (block, frequency), and every rank leader of the census set must be
# among them, so no leader of the census can be left out and none from the tail counted in.
_TAILEB = {r['eb'] for r in json.load(open(os.path.join(HERE, 'r28inputs', 'tail_windows_r28.json')))['rows']}
_LEDC = [r for r in json.load(open(os.path.join(HERE, 'ledger.json')))['rows']
         if r['eb'] not in _TAILEB and not r['attributed'] and not r['dq']]
_CK = {(r['eb'], round(float(r['freq']), 4)) for r in _LEDC}
_CLEAD = {(r['eb'], round(float(r['freq']), 4)) for r in _LEDC
          if r['rank_ctrl'] is not None and r['tstar'] > r['rank_ctrl']}
_OK = {(r['eb'], round(float(r['freq']), 4)) for r in RK_OBS}
_OBSK = {(r['eb'], round(float(r['freq']), 4)) for r in OBS}
if DRIVE == 8:                       # a tail crossing counted into the observed side
    _OBSK = _OBSK | {('A002_Xtail_X0', 1.0)}
ck('K2b (R18) the rank comparison is over the census\'s unattributed crossings: every observed row is one of '
   'them, and the leaders counted are exactly the census set\'s own leaders',
   _OBSK <= _CK and _OK == _CLEAD,
   '%d observed rows in the census set of %d unattributed quality-passing crossings; leaders %d counted, %d in '
   'the census set' % (len(_OBSK & _CK), len(_CK), len(_OK), len(_CLEAD)))
m('RkCondNSet', '%d' % len(_CK))
m('RkCondExp', '%.2f' % RK_EXP)
m('RkCondProb', '%.2g' % RK_P if RK_P < 0.1 else '%.2f' % RK_P)
m('RkCondNObs', '%d' % K_OBS)
m('RkCondNObsWord', word(K_OBS))
m('RkCondNWin', '%d' % N_LEAD_WIN)

# ===================================================== 2.  THE OPEN PAIRS
def _R(u, L):
    u = np.asarray(u, float)
    return np.where(u <= 0, 0.0,
                    np.where(u <= L, 0.5 * u * u, 0.5 * L * L + L * (u - L)))


def cdf_diff(d, a1, b1, a2, b2):
    """P(X - Y <= d) for X ~ U[a1, b1] and Y ~ U[a2, b2], exactly."""
    L1, L2 = b1 - a1, b2 - a2
    if DRIVE == 3:                        # the sign of the law reversed
        return float((_R(b1 - d - a2, L2) - _R(a1 - d - a2, L2)) / (L1 * L2))
    return float((_R(b2 + d - a1, L2) - _R(b2 + d - b1, L2)) / (L1 * L2))


def p_within(h, w1, w2):
    return (cdf_diff(h, w1['slo'], w1['shi'], w2['slo'], w2['shi'])
            - cdf_diff(-h, w1['slo'], w1['shi'], w2['slo'], w2['shi']))


# K4 -- the law is validated against direct sampling on three window pairs of
# different overlap before it is used.
_rng = np.random.default_rng(2810)
_tests = [((0.0, 1.0), (0.0, 1.0), 0.5), ((2.0, 5.0), (3.0, 3.5), 0.7),
          ((0.0, 1.0), (1.5, 2.0), 0.8)]
_worst = 0.0
for (a1, b1), (a2, b2), h in _tests:
    x = _rng.uniform(a1, b1, 400000)
    y = _rng.uniform(a2, b2, 400000)
    mc = float(np.mean(np.abs(x - y) <= h))
    ex = (cdf_diff(h, a1, b1, a2, b2) - cdf_diff(-h, a1, b1, a2, b2))
    _worst = max(_worst, abs(mc - ex))

# the stellar-frame band of every window, through the paper's own frame chain
NOVB = 0
for w in WIN:
    vb, _src = mf.vbary(w['eb'], CAT[w['i']]['flo_GHz'])
    vs, _s2, _b = mf.vsys(w['star'])
    NOVB += vb is None
    k = (1.0 - (vb or 0.0) / CKMS) * (1.0 + (vs or 0.0) / CKMS)
    lo, hi = sorted((w['flo'], w['fhi']))
    w['slo'], w['shi'] = lo * k * 1e9, hi * k * 1e9
    w['t'] = EP.epoch(w['eb'])

# K6 -- windows are grouped by star.  The catalogue carries no position, so the
# key is the system identifier with the project's canonical star name, and it
# is VALIDATED on position: every window whose block the primary-beam audit
# holds at one unambiguous position must agree with the rest of its group to
# POS_TOL.  (A block observing two stars cannot be placed this way and is
# reported, not guessed.)
GBY = collections.defaultdict(list)
for g in GEO:
    GBY[g['_stem'].rsplit('_spw', 1)[0]].append(g)
GROUP = collections.defaultdict(list)
for w in WIN:
    key = (w['sysid'], sa.canon(w['star']))
    if DRIVE == 5:                        # a name key that collides
        key = (sa.canon(w['star']).split()[0],)
    GROUP[key].append(w)
    lo, hi = sorted((w['flo'], w['fhi']))
    c = [g for g in GBY.get(w['eb'], [])
         if lo - 1e-3 <= g['freqmed'] / 1e9 <= hi + 1e-3]
    pos = {(round(g['t1_ra'], 5), round(g['t1_dec'], 5)) for g in c}
    w['pos'] = next(iter(pos)) if len(pos) == 1 else None
SPLIT, NPLACED, PMMAX = [], 0, 0.0
#: ★ the audit's positions are at each block's own epoch (proper motion
#: propagated), so two epochs of one high-proper-motion star are several
#: arcsec apart.  The tolerance is POS_TOL plus the largest proper motion any
#: star within 40 pc has (Barnard's star, 10.4 arcsec/yr) times the interval;
#: a merged pair of DIFFERENT stars at one epoch still fails at POS_TOL.
PM_MAX = 10.4
for key, ws in GROUP.items():
    pw = [w for w in ws if w['pos'] is not None]
    NPLACED += len(pw)
    for a, b in itertools.combinations(pw, 2):
        pa, pb = a['pos'], b['pos']
        sep = 3600.0 * math.hypot((pa[0] - pb[0]) * math.cos(math.radians(pa[1])),
                                  pa[1] - pb[1])
        dty = (abs(a['t'] - b['t']) / 365.25 if a['t'] is not None
               and b['t'] is not None else 0.0)
        if sep > POS_TOL and dty > 0:
            PMMAX = max(PMMAX, (sep - POS_TOL) / dty)
        if sep > POS_TOL + PM_MAX * dty:
            SPLIT.append((key, round(sep, 1), round(dty, 2)))
            break
ck('K6 the star groups are confirmed on position: no group holds two placed '
   'windows further apart than %.0f arcsec plus the largest proper motion '
   'in the volume over their interval' % POS_TOL,
   not SPLIT,
   '%d groups, %d of %d windows placed by the primary-beam audit, %d groups '
   'too wide %s; largest implied motion %.2f arcsec/yr'
   % (len(GROUP), NPLACED, len(WIN), len(SPLIT), SPLIT[:2], PMMAX))

E = collections.Counter()
NUNK = 0
for key, ws in GROUP.items():
    for a, b in itertools.combinations(ws, 2):
        if a['eb'] == b['eb'] or a['lam'] == 0.0 or b['lam'] == 0.0:
            continue
        nu = 0.25 * (a['slo'] + a['shi'] + b['slo'] + b['shi'])
        hh = HALF / CKMS * nu
        ll = a['lam'] * b['lam']
        p_pair = p_within(hh, a, b)
        if p_pair <= 0.0:
            continue
        shared = (a['eb'] not in EP.MS and b['eb'] not in EP.MS
                  and EP.MJD.get(a['eb']) == EP.MJD.get(b['eb']))
        if a['t'] is None or b['t'] is None or shared:
            NUNK += 1
            pj_lo, pj_hi = 0.0, p_pair
        else:
            dt = abs(a['t'] - b['t']) * 86400.0
            pj_lo = pj_hi = p_within(min(hh, min(a['dmax'], b['dmax']) * dt),
                                     a, b)
        sep = EP.different_session(a['eb'], b['eb']) and EP.apart(a['eb'],
                                                                  b['eb'])
        E['pair'] += ll * p_pair
        E['join_lo'] += ll * pj_lo
        E['join_hi'] += ll * pj_hi
        if sep:
            E['sep_lo'] += ll * pj_lo
            E['sep_hi'] += ll * pj_hi
ck('K4 the joining probability is the exact law of a difference of two '
   'uniform cells (validated against direct sampling), and the expectations '
   'nest: separated-and-joinable <= joinable <= pairs',
   _worst < 3e-3 and E['sep_lo'] <= E['sep_hi'] <= E['join_hi'] + 1e-12
   and E['join_lo'] <= E['join_hi'] <= E['pair'] + 1e-12 and E['pair'] > 0,
   'largest departure from sampling %.4f; pairs %.3f, joinable %.3f-%.3f, '
   'separated %.3f-%.3f; %d window pairs with no interval, %d windows with no '
   'barycentric term' % (_worst, E['pair'], E['join_lo'], E['join_hi'],
                         E['sep_lo'], E['sep_hi'], NUNK, NOVB))

# the observed side: Table 5's own pairs, over the census windows only
def _released_A(eb, f):
    for r in CAT:
        if r['eb'] == eb:
            lo, hi = sorted((float(r['flo_GHz']), float(r['fhi_GHz'])))
            if lo - 1e-6 <= f <= hi + 1e-6:
                return r['search_class'] == 'A'
    return False


UN = [p for p in PAIRS if not p['attr']]
CEN = [p for p in UN if (_released_A(p['eblo'], p['ftopolo'])
                         and _released_A(p['ebhi'], p['ftopohi']))
       or DRIVE == 4]
TAILP = [p for p in UN if p not in CEN]
_open = [p for p in CEN if p['verdict'] == 'not separable']
_sep = [p for p in _open if EP.different_session(p['eblo'], p['ebhi'])
        and EP.apart(p['eblo'], p['ebhi'])]
ck('K5 the observed pairs are Table 5\'s own, split into census and archival '
   'tail with nothing lost, and the tail pairs enter neither side',
   len(CEN) + len(TAILP) == int(macro('TjNPair')) and len(TAILP) > 0
   if DRIVE != 4 else False,
   '%d census + %d tail = %d against the printed %s; census: %d open of which '
   '%d in separated sessions' % (len(CEN), len(TAILP), len(CEN) + len(TAILP),
                                 macro('TjNPair'), len(_open), len(_sep)))
# ★ the orbital route of the confirmation definition needs three crossings of
# one star in three different sessions, every two of them joined by a bounded
# trajectory (an open pair).  Counted over the census alone and with the
# archival tail, from Table 5's own pairs.
def _triples(pairs):
    adj = collections.defaultdict(set)
    node_sess = {}
    for p in pairs:
        a = (p['eblo'], round(float(p['ftopolo']), 6))
        b = (p['ebhi'], round(float(p['ftopohi']), 6))
        st = sa.canon(p['star'])
        adj[(st, a)].add((st, b))
        adj[(st, b)].add((st, a))
        node_sess[(st, a)] = EP.session(p['eblo'])
        node_sess[(st, b)] = EP.session(p['ebhi'])
    stars = set()
    for x, y, z in itertools.combinations(sorted(adj), 3):
        if (x[0] == y[0] == z[0] and y in adj[x] and z in adj[x]
                and z in adj[y]
                and len({node_sess[x], node_sess[y], node_sess[z]}) == 3):
            stars.add(x[0])
    return sorted(stars)


TRI_CEN = _triples(_open)
TRI_ALL = _triples([p for p in UN if p['verdict'] == 'not separable'])
if DRIVE == 7:                            # the two populations swapped
    TRI_CEN, TRI_ALL = TRI_ALL, TRI_CEN
ck('K7 the stars offering the orbital route are counted from Table 5\'s own '
   'open pairs, and the census count cannot exceed the count with the tail',
   set(TRI_CEN) <= set(TRI_ALL),
   'census: %s; with the archival tail: %s' % (TRI_CEN or 'none', TRI_ALL))
m('OpNTriCen', '%d' % len(TRI_CEN))
m('OpNTriAll', '%d' % len(TRI_ALL))
m('OpNTriAllWord', word(len(TRI_ALL)))
m('OpNTriCenWord', 'none' if not TRI_CEN else word(len(TRI_CEN)))
# the paper's own spelling of each star, from the ledger's display field,
# reached through a crossing of the star (never through the name itself)
_LED = json.load(open(os.path.join(HERE, 'ledger.json')))['rows']
_DISP = {}
for p in UN:
    for eb, f in ((p['eblo'], p['ftopolo']), (p['ebhi'], p['ftopohi'])):
        for r in _LED:
            if r['eb'] == eb and abs(float(r['freq']) - float(f)) < 1e-6:
                _DISP[sa.canon(p['star'])] = r['display']
m('OpTriStars', ' and '.join(_DISP.get(k, k) for k in TRI_ALL) or 'none')
m('OpExpPair', '%.1f' % E['pair'])
m('OpExpSepLo', '%.1f' % E['sep_lo'])
m('OpExpSepHi', '%.1f' % E['sep_hi'])
# ★ v4.29 (push29): after the fold both ends printed 3.8 and the page read
#   "3.8--3.8".  One figure when the two ends print alike, a range when they
#   do not -- rfi_v399's idiom for a range that can collapse onto itself.
_slo, _shi = '%.1f' % E['sep_lo'], '%.1f' % E['sep_hi']
m('OpExpSepRange', _slo if _slo == _shi else '%s--%s' % (_slo, _shi))
_den = E['pair'] if E['pair'] > 0 else float('nan')    # K4 has already failed
m('OpJoinPctLo', '%.0f' % (100.0 * E['join_lo'] / _den))
m('OpJoinPctHi', '%.0f' % (100.0 * E['join_hi'] / _den))
m('OpObsPair', '%d' % len(CEN))
m('OpObsOpen', '%d' % len(_open))
m('OpObsSep', '%d' % len(_sep))
m('OpNTailPair', '%d' % len(TAILP))

# ------------------------------------------------------------------ write
with open(OUT, 'w') as fh:
    fh.write('%% GENERATED by rankpairs_r28.py (round 2810) -- do not '
             'hand-edit.\n%% The rank\'s chance rate conditional on the '
             'trigger, and the chance\n%% expectation of open pairs, both '
             'over the census with the D.1 weights.\n')
    for k, v in M:
        fh.write('\\newcommand{\\%s}{%s}\n' % (k, v))
json.dump(dict(round=ROUND, drive=DRIVE,
               rank=dict(expectation=RK_EXP, p_tail=RK_P, observed=K_OBS,
                         observed_rows=RK_OBS, windows_with_leader=N_LEAD_WIN,
                         n_windows=len(WIN)),
               pairs=dict(expected=dict(E), window_pairs_no_interval=NUNK,
                          census_pairs=[(p['eblo'], p['ebhi'], p['verdict'])
                                        for p in CEN],
                          tail_pairs=[(p['eblo'], p['ebhi']) for p in TAILP],
                          observed_open=len(_open),
                          observed_open_separated=len(_sep),
                          orbit_route_stars_census=TRI_CEN,
                          orbit_route_stars_all=TRI_ALL)),
          open(OUTJ, 'w'), indent=1, default=str)
print('%d macros -> %s' % (len(M), os.path.basename(OUT)))
if FAIL:
    print('FAILED: %s' % ', '.join(FAIL))
    if DRIVE == 0:
        raise SystemExit(1)
else:
    print('all checks pass')
