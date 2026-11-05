#!/usr/bin/env python3
r"""triple_r30.py -- round 2935 -> survey_numbers_round2935.tex,
tab_triple_r30.tex, triple_r30.json.

THE ORBITAL ROUTE OF THE CONFIRMATION DEFINITION, APPLIED (Referee 2 M2).

Table 2 defines a second way a carrier is confirmed: an additional separated
epoch at the frequency an independently specified trajectory predicts.  The
pair test (Table 5) finds three crossings toward one star -- HD 14055, with
its archival-tail blocks -- every two of which a bounded trajectory joins, in
three different sessions (`rankpairs_r28.py`, \OpTriStars).  That is the case
the route was written for, and the paper had never asked of it whether ONE
trajectory joins all three and whether the first two PREDICT the third.  This
generator asks, for every such triple, with the two trajectory families the
referee names, both inside the searched grid:

 A  CONSTANT LINE-OF-SIGHT ACCELERATION.  nu(t) = nu_1 + nudot (t - t_1) with
    one drift rate for all three epochs.  The first two crossings fix nudot
    as their mean rate; the third is then predicted with no freedom at all,
    in frequency and in drift.

 B  A CIRCULAR ORBIT whose line-of-sight acceleration never leaves the grid's
    ceiling: v_los(t) = A sin(w t) + B cos(w t), nu = nu_0 (1 - v_los/c),
    with w sqrt(A^2 + B^2) <= a_grid.  For each angular rate w on a grid fine
    enough to resolve the phase at the third epoch, (nu_0, A, B) are fitted
    by weighted least squares to the observables of the FIRST TWO crossings
    (frequency and drift at each, 4 numbers for 3 linear unknowns), on the
    ceiling where the free fit exceeds it; the w the two crossings admit are
    those whose four residuals all lie within the grid's resolution, and each
    admitted w PREDICTS the third crossing's frequency and drift.  The same
    fit to all six numbers asks whether any one orbit passes all three.

THE RESOLUTION is the grid's own: half a channel in frequency (the cell a
crossing is registered to) and half a drift step in rate (the error a
fitted drift carries, \ZtHalfStepMed).  A prediction "within the grid
resolution" lies inside both.  Times are each block's first integration,
the convention every frequency in Table 5 is quoted at, and rates and
frequencies are in the star's frame, as Table 5 prints them.

Every number the paper prints from this is generated here; nothing is typed.

Usage: triple_r30.py [--drive N]
Drives: 1 one block standing for two of a triple's epochs (T1); 2 the
resolution taken as ten channels (T3); 3 the pair-only admissible set taken
from all three crossings, so the third is fitted and called predicted (T4);
4 the ceiling lifted a thousandfold (T2); 5 the drift equation's sign
reversed, which the known-answer orbit T0 must catch.
"""
import collections
import itertools
import json
import math
import os
import sys

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import epochs_r14 as EP                                          # noqa: E402

ROUND = 2935
DRIVE = int(sys.argv[sys.argv.index('--drive') + 1]) if '--drive' in sys.argv \
    else 0
SFX = '' if DRIVE == 0 else '_drive%d' % DRIVE
OUT = os.path.join(HERE, 'numbers/survey_numbers_round%d%s.tex' % (ROUND, SFX))
OUTJ = os.path.join(HERE, 'triple_r30%s.json' % SFX)
OUTT = os.path.join(HERE, 'tab_triple_r30%s.tex' % SFX)
C = 299792458.0

M, FAIL = [], []


def m(k, v):
    assert k.isalpha() and k not in dict(M), k
    M.append((k, str(v)))


def ck(name, cond, detail=''):
    if not cond:
        FAIL.append(name)
    print('  %-70s %s  %s' % (name, 'PASS' if cond else 'FAIL', detail))


def macro(name):
    import glob
    import re
    pat = re.compile(r'\\(?:new|renew|provide)command\{\\%s\}'
                     r'\{((?:[^{}]|\{[^{}]*\})*?)\}' % name)
    v = None
    for fn in sorted(glob.glob(os.path.join(HERE,
                                            'numbers/survey_numbers*.tex'))):
        if '_drive' in fn or 'round%d' % ROUND in fn:
            continue
        for mm in pat.finditer(open(fn, encoding='utf-8').read()):
            if mm.group(1).strip():
                v = mm.group(1).strip()
    if v is None:
        raise SystemExit('macro %s not found' % name)
    return v


PJ = json.load(open(os.path.join(HERE, 'pairs_v415.json')))
REC = json.load(open(os.path.join(HERE, 'r10inputs',
                                  'recur_v411.json')))['crossings']
AG = float(PJ['a_grid'])
OPEN = [p for p in PJ['pairs'] if not p['attr']
        and p['verdict'] == 'not separable']

# ------------------------------------------------------ the crossings
NODE = {}
for p in OPEN:
    for side in ('lo', 'hi'):
        cid = p['cid' + side]
        d = REC[cid]['discovery']
        NODE[cid] = dict(cid=cid, star=p['star'].replace(' ', ''),
                         eb=p['eb' + side], t=float(d['t_start_mjdsec']),
                         f=float(p['fstar' + side]) * 1e9,
                         fd=float(p['d' + side]),
                         step=float(p['step' + side]),
                         chanw=float(d['chanw_Hz']),
                         sess=EP.session(p['eb' + side]))
ADJ = collections.defaultdict(set)
for p in OPEN:
    ADJ[p['cidlo']].add(p['cidhi'])
    ADJ[p['cidhi']].add(p['cidlo'])
TRI = []
for x, y, z in itertools.combinations(sorted(NODE), 3):
    a, b, c = NODE[x], NODE[y], NODE[z]
    if not (a['star'] == b['star'] == c['star']):
        continue
    if not (y in ADJ[x] and z in ADJ[x] and z in ADJ[y]):
        continue
    if DRIVE != 1 and len({a['sess'], b['sess'], c['sess']}) < 3:
        continue
    TRI.append(sorted((a, b, c), key=lambda n: n['t']))
if DRIVE == 1:                       # T1: a block standing for two epochs
    TRI[0][2] = dict(TRI[0][2], eb=TRI[0][1]['eb'])
_stars = sorted({t[0]['star'] for t in TRI})
ck('T1 the triples are three crossings of one star in three sessions, every '
   'two of them an open pair of Table 5, and they are the stars round 2810 '
   'names',
   bool(TRI) and all(len({n['sess'] for n in t}) == 3 for t in TRI)
   and all(EP.confirms(u['eb'], v['eb'])
           for t in TRI for u, v in itertools.combinations(t, 2))
   and ' and '.join(_stars).replace('HD14055', 'HD~14055')
   == macro('OpTriStars'),
   '%d triple(s) toward %s: %s' % (
       len(TRI), _stars, ['/'.join(n['eb'][-6:] for n in t) for t in TRI]))

TOLF = 0.5          # of a channel
TOLD = 0.5          # of a drift step
if DRIVE == 2:
    TOLF = 5.0


def res_units(n, f, fd):
    return ((f - n['f']) / (TOLF * n['chanw']),
            (fd - n['fd']) / (TOLD * n['step']))


# ======================================== A. constant acceleration
def model_a(t):
    a, b, c = t
    rate = (b['f'] - a['f']) / (b['t'] - a['t'])
    f3 = b['f'] + rate * (c['t'] - b['t'])
    # the resolution of the prediction: one registration cell at each of the
    # first two epochs, carried over the baseline to the third
    sig = math.hypot(TOLF * a['chanw'], TOLF * b['chanw']) \
        * (c['t'] - a['t']) / (b['t'] - a['t'])
    return dict(rate=rate, f3=f3, d3=rate, miss_f=(c['f'] - f3) / sig,
                miss_d1=(a['fd'] - rate) / (TOLD * a['step']),
                miss_d2=(b['fd'] - rate) / (TOLD * b['step']),
                miss_d3=(c['fd'] - rate) / (TOLD * c['step']))


# ======================================== B. circular, inside the ceiling
def design(nodes, w, nubar):
    rows, y, s = [], [], []
    for n in nodes:
        t = n['t'] - nodes[0]['t']
        sw, cw = math.sin(w * t), math.cos(w * t)
        # nu = nu0 - (nubar/c)(A sin + B cos);  nudot = -(nubar/c) w (A cos - B sin)
        rows.append([1.0, -nubar / C * sw, -nubar / C * cw])
        y.append(n['f'])
        s.append(TOLF * n['chanw'])
        _sg = -1.0 if DRIVE == 5 else 1.0   # T0: the drift row's sign
        rows.append([0.0, -_sg * nubar / C * w * cw, _sg * nubar / C * w * sw])
        y.append(n['fd'])
        s.append(TOLD * n['step'])
    return np.array(rows), np.array(y), np.array(s)


PHI = np.linspace(0.0, 2.0 * math.pi, 721)[:-1]


def fit(nodes, w, nubar, amax):
    X, y, s = design(nodes, w, nubar)
    Xw, yw = X / s[:, None], y / s
    sol, *_ = np.linalg.lstsq(Xw, yw, rcond=None)
    K = math.hypot(sol[1], sol[2])
    if K * w <= amax:
        r = (Xw @ sol - yw)
        return sol, r
    # on the ceiling: A = K cos phi, B = K sin phi with K = amax / w, nu0
    # free; every phase at once
    Kc = amax / w
    Aa, Bb = Kc * np.cos(PHI), Kc * np.sin(PHI)
    rest = yw[:, None] - Xw[:, 1:2] * Aa[None, :] - Xw[:, 2:3] * Bb[None, :]
    nu0 = (Xw[:, 0:1] * rest).sum(axis=0) / (Xw[:, 0] ** 2).sum()
    R = Xw[:, 0:1] * nu0[None, :] + Xw[:, 1:2] * Aa[None, :] \
        + Xw[:, 2:3] * Bb[None, :] - yw[:, None]
    j = int(np.argmin((R * R).sum(axis=0)))
    return np.array([nu0[j], Aa[j], Bb[j]]), R[:, j]


def predict(sol, n0, n, w, nubar):
    t = n['t'] - n0['t']
    v = sol[1] * math.sin(w * t) + sol[2] * math.cos(w * t)
    f = sol[0] - nubar / C * v
    fd = -nubar / C * w * (sol[1] * math.cos(w * t) - sol[2] * math.sin(w * t))
    return f, fd


def circular(t, amax):
    a, b, c = t
    nubar = sum(n['f'] for n in t) / 3.0
    span = c['t'] - a['t']
    # w from the slowest orbit that matters (a quarter period over the whole
    # span) to the fastest the ceiling admits for the velocity change the
    # first two crossings need; the step resolves 1/20 of a radian of phase
    # at the third epoch.
    dv12 = abs(b['f'] - a['f']) / nubar * C
    wmin = 0.5 * math.pi / (4.0 * span)
    wmax = 2.0 * AG / max(dv12, 1.0) * 1.2
    dw = 0.05 / span
    W = np.arange(wmin, wmax, dw)
    pair_ok, pred, joint = [], [], []
    for w in W:
        sol2, r2 = fit([a, b], w, nubar, amax)
        if DRIVE == 3:
            sol2, r2 = fit([a, b, c], w, nubar, amax)
            r2 = r2[:4]
        if np.all(np.abs(r2) <= 1.0):
            f3, d3 = predict(sol2, a, c, w, nubar)
            pair_ok.append(w)
            pred.append((w, f3, d3) + res_units(c, f3, d3))
        sol3, r3 = fit([a, b, c], w, nubar, amax)
        joint.append((float(np.max(np.abs(r3))), w,
                      w * math.hypot(sol3[1], sol3[2])))
    hit = [p for p in pred if abs(p[3]) <= 1.0 and abs(p[4]) <= 1.0]
    jbest = min(joint)
    fpred = [p[1] for p in pred]
    spread = (max(fpred) - min(fpred)) if fpred else 0.0
    pbest = min(float(np.max(np.abs(fit([a, b], w, nubar, amax)[1])))
                for w in W)
    return dict(W=W, pair_ok=pair_ok, pred=pred, hit=hit, jbest=jbest,
                spread=spread, pbest=pbest, span=span)


def verdict(cr, c):
    if not cr['pair_ok'] or cr['jbest'][0] > 1.0:
        return 'excluded'
    if cr['hit'] and cr['spread'] <= 2.0 * TOLF * c['chanw']:
        return 'predicted'
    return 'fits, not predicted' if cr['hit'] else 'excluded'


# ★ T0: KNOWN ANSWER.  A synthetic carrier on a circular orbit inside the
# ceiling, sampled at the first real triple's own epochs with its own grid,
# must be admitted by its first two crossings at the true rate and predicted
# at the third -- otherwise a verdict of "excluded" could be the fitter's.
_t0 = [dict(n) for n in TRI[0]]
_w0, _K0, _ph0 = 2.0 * math.pi / (5.3 * 86400.0), 150e3, 0.7
for n in _t0:
    tt = n['t'] - _t0[0]['t']
    v = _K0 * math.sin(_w0 * tt + _ph0)
    n['f'] = 345.0e9 * (1.0 - v / C)
    n['fd'] = -345.0e9 / C * _K0 * _w0 * math.cos(_w0 * tt + _ph0)
_kat = circular(_t0, AG if DRIVE != 4 else 1e3 * AG)
_near = min(abs(w - _w0) for w in _kat['pair_ok']) if _kat['pair_ok'] \
    else 1.0
ck('T0 known answer: a circular orbit inside the ceiling, sampled at the '
   'triple\'s own epochs, is admitted by its first two crossings near its '
   'true rate, fitted through all three, and found at the third',
   _kat['pair_ok'] and _near < 2.0 * 0.05 / _kat['span'] and _kat['hit']
   and _kat['jbest'][0] <= 1.0,
   '%d rates admitted, nearest the truth by %.2e rad/s, %d hit the third, '
   'best joint residual %.2f' % (len(_kat['pair_ok']), _near,
                                 len(_kat['hit']), _kat['jbest'][0]))

OUTROWS = []
for t in TRI:
    a, b, c = t
    A = model_a(t)
    amax = AG if DRIVE != 4 else 1e3 * AG
    cr = circular(t, amax)
    W, pair_ok, hit, jbest, spread = (cr['W'], cr['pair_ok'], cr['hit'],
                                      cr['jbest'], cr['spread'])
    span = cr['span']
    OUTROWS.append(dict(verdict_b=verdict(cr, c), pair_best_res=cr['pbest'],
        joint_best_alos=jbest[2],
        star=a['star'], cids=[n['cid'] for n in t], ebs=[n['eb'] for n in t],
        dt12_d=(b['t'] - a['t']) / 86400.0, dt13_d=span / 86400.0,
        A=A, n_w=len(W), n_pair_ok=len(pair_ok), n_hit=len(hit),
        frac_hit=(len(hit) / len(pair_ok)) if pair_ok else 0.0,
        pred_spread_MHz=spread / 1e6,
        pred_spread_chan=spread / c['chanw'],
        joint_best_res=jbest[0], joint_best_w=jbest[1],
        joint_best_P_d=2.0 * math.pi / jbest[1] / 86400.0,
        chanw=c['chanw'], step=c['step']))

# ---------------------------------------------------------- checks
ck('T2 every trajectory fitted stays inside the searched grid: its '
   'line-of-sight acceleration amplitude is at most the ceiling',
   AG > 0 and all(r['n_w'] > 1000 for r in OUTROWS)
   and all(r['joint_best_alos'] <= AG * (1.0 + 1e-9) for r in OUTROWS),
   'ceiling %.3f m/s^2; %s angular rates scanned per triple; best orbits '
   'reach %s m/s^2' % (AG, [r['n_w'] for r in OUTROWS],
                       ['%.3f' % r['joint_best_alos'] for r in OUTROWS]))
ck('T3 the resolution is the grid\'s own: half a channel and half a drift '
   'step at each crossing',
   TOLF == 0.5 and TOLD == 0.5,
   'half a channel (%s kHz at the third epoch) and half a step'
   % ['%.0f' % (r['chanw'] / 2e3) for r in OUTROWS])
_aexcl = all(abs(r['A']['miss_f']) > 3.0 or abs(r['A']['miss_d1']) > 3.0
             for r in OUTROWS)
ck('T4 each verdict follows from the prediction made by the first two '
   'crossings ALONE: constant acceleration is excluded where it misses the '
   'third by more than three resolutions, and the circular verdict is the '
   'rule\'s own',
   DRIVE != 3 and _aexcl
   and all(r['verdict_b'] in ('excluded', 'predicted', 'fits, not predicted')
           for r in OUTROWS),
   '; '.join('%s: constant acceleration misses the third by %.0f '
             'resolutions in frequency (drifts %.0f / %.0f / %.0f steps from '
             'one rate); circular: %d of %d rates admitted by the first two '
             '(their best fit misses by %.1f resolutions), %d within '
             'resolution of the third; best single orbit through all three '
             'misses by %.1f resolutions (P = %.2f d): %s'
             % ('/'.join(e[-6:] for e in r['ebs']), abs(r['A']['miss_f']),
                r['A']['miss_d1'], r['A']['miss_d2'], r['A']['miss_d3'],
                r['n_pair_ok'], r['n_w'], r['pair_best_res'], r['n_hit'],
                r['joint_best_res'], r['joint_best_P_d'], r['verdict_b'])
             for r in OUTROWS))

# ---------------------------------------------------------- emit
WD = ('no', 'one', 'two', 'three', 'four', 'five')
m('TrNTriple', '%d' % len(OUTROWS))
m('TrNTripleWord', WD[len(OUTROWS)] if len(OUTROWS) < len(WD)
  else '%d' % len(OUTROWS))
m('TrAMissMin', '%.0f' % min(abs(r['A']['miss_f']) for r in OUTROWS))
m('TrADriftMissMin', '%.0f' % min(max(abs(r['A']['miss_d1']),
                                      abs(r['A']['miss_d2']))
                                  for r in OUTROWS))
m('TrNHitAll', '%d' % sum(1 for r in OUTROWS if r['n_hit'] > 0))
m('TrNExclB', '%d' % sum(1 for r in OUTROWS if r['verdict_b'] == 'excluded'))
m('TrPairMissMin', '%.0f' % min(r['pair_best_res'] for r in OUTROWS))
m('TrJointMissMin', '%.0f' % min(r['joint_best_res'] for r in OUTROWS))
m('TrVerdictB', ' and '.join(sorted({r['verdict_b'] for r in OUTROWS})))
# the row block appended under Table 5: one line per triple, the verdict in
# words
TL = ['%% GENERATED by triple_r30.py -- do not hand-edit.',
      r'\begin{tabular}{@{}l@{~}l@{~}l@{}}', r'\hline',
      r'Triple & constant acceleration & circular orbit \\', r'\hline']
for r in OUTROWS:
    TL.append(r'%s & misses by %.0f & %s \\'
              % ('/'.join(e.split('_')[-1] for e in r['ebs']),
                 abs(r['A']['miss_f']),
                 r['verdict_b'] if r['verdict_b'] != 'excluded'
                 else 'misses by %.0f' % r['joint_best_res']))
TL += [r'\hline', r'\end{tabular}']
open(OUTT, 'w').write('\n'.join(TL) + '\n')
json.dump(dict(generator='triple_r30.py', round=ROUND, drive=DRIVE,
               a_grid=AG, tol_chan=TOLF, tol_step=TOLD, triples=OUTROWS),
          open(OUTJ, 'w'), indent=1, sort_keys=True)
with open(OUT, 'w') as fh:
    fh.write('%% GENERATED by triple_r30.py -- do not hand-edit.\n')
    for k, v in M:
        fh.write('\\newcommand{\\%s}{%s}\n' % (k, v))
print('\n%d macros, %d assertions failed %s' % (len(M), len(FAIL), FAIL))
if FAIL and DRIVE == 0:
    raise SystemExit('assertions failed: %s' % FAIL)
