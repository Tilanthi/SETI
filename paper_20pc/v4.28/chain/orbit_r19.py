#!/usr/bin/env python3
r"""orbit_r19.py -- the orbit behind the beta Pictoris pair, SOLVED rather
than offered.  Round 860.  Writes `survey_numbers_round860.tex` and
`orbit_r19.json`.

WHY THIS EXISTS.  The pair of 241.8 GHz crossings toward beta Pic is the
closest case in the pair table: the two blocks are 1.017 d apart, a single
carrier at constant line-of-sight acceleration misses the measured frequency
offset by 132 standard deviations, and the question is whether an ACCELERATING
carrier -- a transmitter in orbit about the host -- could have produced both.
The text answers it with a named circular orbit, 30 degrees of inclination,
0.038 au, 2.0 d.  That orbit cannot have produced this pair, and the arithmetic
is a line long:

  * The interval is 1.017 d = 0.497 of the quoted period, so the phase advances
    by 179 degrees and the line-of-sight acceleration very nearly REVERSES
    between the epochs.
  * Both fitted drifts are negative, so both accelerations have the SAME sign,
    with ratio a2/a1 = 0.421.
  * A sinusoid can take the same sign, in that ratio, half a period apart only
    within a few degrees of a node, i.e. with an amplitude at the epochs far
    below the amplitude of the orbit.  For the quoted orbit the largest first
    acceleration compatible with the measured ratio is 0.043 m/s2, and the
    measurement is 1.998 m/s2.

So the witness is wrong by a factor of ~47 and has to be replaced -- but the
question it was answering is still open, and it is a well-posed inverse
problem rather than a search for an illustration.  THE PAIR SUPPLIES EXACTLY
THREE NUMBERS and a circular orbit has exactly three free parameters, so the
orbit is DETERMINED, not merely permitted:

    a_los(t1), a_los(t2)        from the two fitted drifts, a = -c nudot / nu
    Delta nu = +85.456 MHz      the stellar-frame offset over Delta t = 1.017 d
    (A, omega, phase)           amplitude, rate and phase of a_los(t)

with the host's own mass fixing the Kepler link between A, omega and the
inclination, and with ONE inequality to satisfy: the line-of-sight
acceleration may never leave the searched drift grid, |a_los| <= 3.598 m/s2,
or the carrier would not have been found by the search that found it.

WHAT IS SOLVED, AND HOW COMPLETELY.  For a circular orbit the three equations
reduce to two in (omega, phase) once the amplitude is eliminated, and the
inequality bounds the search box from above without any approximation:
|Delta v| <= 2A/omega <= 2 a_ceil / omega gives omega <= 2 a_ceil / |Delta v|,
i.e. P >= 1.071 d.  Inside that box the two residual surfaces are enumerated
on a grid and every sign-change cell is refined, so the enumeration is
complete and not a sample: it returns ONE solution.  The same system is also
solved a second way, by the analytic reduction in the appendix of this
docstring (the mean of a sinusoid over the interval is fixed by the pair, which
collapses the system to a single equation in sin(phase)), and the two agree.
For an eccentric orbit there are five parameters and three equations, so the
solutions form a two-parameter family; it is enumerated the same way on a grid
of (e, argument of periastron), and the ceiling -- not the data -- is what
limits it: beyond e ~ 0.2 the periastron acceleration leaves the grid.

THE DRIFT IS A FIT OVER A DWELL, NOT AN INSTANT.  Each drift is the slope of a
straight line fitted to a carrier's track across its own 2680 s dwell, so the
model here fits the SLOPE OVER THE DWELL and not the instantaneous derivative
at the block start.  For a sinusoid the least-squares slope over [t0, t0+T] is
exactly a_los(t_mid) * 3(sin x - x cos x)/x^3 with x = omega T / 2, so the
difference is a known half-dwell shift of the phase; it moves the inclination
by 0.23 degrees and the period by 0.004 d, which is larger than the half-grid-
step errors and is therefore not optional.  The crossing FREQUENCIES are read
at the block start (the de-drift convention), so the offset equation uses the
start epochs and the drift equations the mid-dwell epochs.

Usage: orbit_r19.py [--drive N]        N = 1..8, each breaks one assertion.
"""
import glob
import json
import math
import os
import re
import sys

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
# ★★★★ THIS WAS PINNED AT `/workspace/SETI/paper_20pc/v4.19`, THE TREE THE
# FILE WAS WRITTEN IN, and it was never repointed when the file was adopted
# into the version directory.  So this generator read its inputs and the macro
# layer out of the PREVIOUS version for a whole round -- and when that
# directory was removed, `make_all.sh` stopped here with a
# FileNotFoundError on `pairs_v415.json`.  The pattern the rest of the build
# uses is `quality_r19.py`'s: read this tree when the file sits in it, and the
# frozen previous one only while the file is being written outside it.
V = (HERE if os.path.exists(os.path.join(HERE, 'pairs_v415.json'))
     else '/workspace/SETI/paper_20pc/v4.19')
ROUND = 860
DRIVE = int(sys.argv[sys.argv.index('--drive') + 1]) if '--drive' in sys.argv \
    else 0
SFX = '' if DRIVE == 0 else '_drive%d' % DRIVE
OUT = os.path.join(HERE, 'survey_numbers_round860%s.tex' % SFX)
OUTJ = os.path.join(HERE, 'orbit_r19%s.json' % SFX)

C = 299792458.0
CKMS = C / 1e3
GMSUN = 1.32712440018e20
AU = 1.495978707e11

M, FAIL = [], []


def m(k, v):
    assert k.isalpha(), 'a LaTeX macro name may contain letters only: ' + k
    assert k not in dict(M), 'macro defined twice: ' + k
    M.append((k, str(v)))


def ck(name, cond, detail=''):
    if not cond:
        FAIL.append(name)
    print('  %-66s %s  %s' % (name, 'PASS' if cond else 'FAIL', detail))


def macro(name):
    """One macro's value out of the frozen layer of the manuscript."""
    pat = re.compile(r'\\newcommand\{\\%s\}\{(.*)\}\s*$' % name)
    for p in sorted(glob.glob(os.path.join(V, 'survey_numbers*.tex'))):
        if '_drive' in p:
            continue
        for line in open(p):
            mm = pat.match(line.strip())
            if mm:
                return mm.group(1)
    raise KeyError(name)


# --------------------------------------------------------------- the inputs
PAIRS = json.load(open(os.path.join(V, 'pairs_v415.json')))
REC = json.load(open(os.path.join(V, 'r10inputs',
                                  'recur_v411.json')))['crossings']
PAIR = [q for q in PAIRS['pairs']
        if q['star'] == 'bet Pic' and q['power'] and abs(q['dt']) < 2 * 86400]
assert len(PAIR) == 1, 'the pair this generator is about is not unique'
PAIR = PAIR[0]

# ★ THE ORBIT BEING REPLACED IS READ FROM A FROZEN RECORD, not from the live
# macro layer, because replacing it removes the macros it was written in: a
# generator that read them would stop running the moment its own result was
# adopted.  Where the macro still exists the two are required to agree, so the
# frozen copy cannot drift away from what the manuscript said.
PUB = json.load(open(os.path.join(HERE, 'r19inputs',
                                  'orbit_published_r19.json')))
PUBLIVE = {}
for _k, _mk in (('inc_deg', 'EcWitIncBp'), ('r_au', 'EcWitAuBp'),
                ('p_d', 'EcWitDayBp'), ('span_kms', 'EcWitSpanBp'),
                ('mass_msun', 'EcMassBp')):
    try:
        PUBLIVE[_k] = float(macro(_mk))
    except KeyError:
        pass
MASS = PUBLIVE.get('mass_msun', PUB['mass_msun'])   # host mass, solar units
GM = MASS * GMSUN
ACEIL = float(PAIRS['a_grid'])               # the drift grid's own ceiling
DT = PAIR['dt']                              # block starts, seconds apart
NUR = PAIR['fstarlo'] * 1e9                  # rest-frequency scale
DNU = (PAIR['fstarhi'] - PAIR['fstarlo']) * 1e9
D1, D2 = PAIR['dlo'], PAIR['dhi']            # stellar-frame fitted drifts
if DRIVE == 1:                               # O1: the topocentric drifts
    D1, D2 = PAIR['dlotopo'], PAIR['dhitopo']
DW = []
for cid in (PAIR['cidlo'], PAIR['cidhi']):
    d = REC[cid]['discovery']
    DW.append(dict(cid=cid, dwell=d['t_end_mjdsec'] - d['t_start_mjdsec'],
                   chanw=float(d['chanw_Hz']), t0=d['t_start_mjdsec']))
T1, T2 = DW[0]['dwell'], DW[1]['dwell']
if DRIVE == 5:                               # O4: an impossibly long dwell
    T1, T2 = 10 * T1, 10 * T2
CHANW = DW[0]['chanw']
assert DW[0]['chanw'] == DW[1]['chanw']
assert abs((DW[1]['t0'] - DW[0]['t0']) - DT) < 1e-3, 'epoch key disagreement'

# accelerations from the drifts: nu = nu_rest (1 - v/c) so a = -c nudot / nu
A1 = -C * D1 / NUR
A2 = -C * D2 / NUR
DV = -C * DNU / NUR                          # the offset as a velocity change
ABAR = DV / DT                               # the mean acceleration demanded
# the errors the referee asks for: half a grid step on each drift, and half a
# channel on each crossing frequency.
E1 = 0.5 * PAIR['steplo'] * C / NUR
E2 = 0.5 * PAIR['stephi'] * C / NUR
EDV = C * 0.5 * CHANW * math.sqrt(2.0) / NUR
if DRIVE == 6:                               # O5: errors inflated 100-fold
    E1, E2, EDV = 100 * E1, 100 * E2, 100 * EDV


# -------------------------------------------------- the forward model, exact
def gfac(x):
    """The least-squares slope of a sinusoid over a dwell, relative to its
    derivative at the dwell midpoint: 3(sin x - x cos x)/x^3, x = omega T/2."""
    x = np.asarray(x, dtype=float)
    small = np.abs(x) < 1e-6
    xs = np.where(small, 1.0, x)
    return np.where(small, 1.0, 3.0 * (np.sin(xs) - xs * np.cos(xs)) / xs ** 3)


def circ_resid(w, th, a1=None, a2=None, dv=None):
    """Residuals of the two equations that remain once the amplitude is
    eliminated.  `th` is the phase of a_los at block 1's DWELL MIDPOINT."""
    a1 = A1 if a1 is None else a1
    a2 = A2 if a2 is None else a2
    dv = DV if dv is None else dv
    g1, g2 = gfac(w * T1 / 2.0), gfac(w * T2 / 2.0)
    with np.errstate(divide='ignore', invalid='ignore'):
        amp = a1 / (g1 * np.sin(th))
        th2 = th + w * (DT + (T2 - T1) / 2.0)
        r1 = amp * g2 * np.sin(th2) - a2
        # the offset is read at the block STARTS, half a dwell earlier
        r2 = (amp / w) * (np.cos(th - w * T1 / 2.0)
                          - np.cos(th2 - w * T2 / 2.0)) - dv
    return r1, r2, amp


def circ_solutions(a1=None, a2=None, dv=None, aceil=None, nw=4001, nt=4001,
                   wtop=None):
    """EVERY circular orbit that reproduces the three observables and keeps
    |a_los| inside the ceiling.  Complete by construction: the ceiling bounds
    omega from above, because |dv| <= 2A/omega <= 2 a_ceil/omega, and inside
    that box every sign-change cell of both residual surfaces is refined."""
    a1 = A1 if a1 is None else a1
    a2 = A2 if a2 is None else a2
    dv = DV if dv is None else dv
    aceil = ACEIL if aceil is None else aceil
    wmax = (2.0 * aceil / abs(dv)) if wtop is None else wtop
    ws = np.linspace(1e-6, wmax * 1.02, nw)
    ths = np.linspace(1e-6, math.pi - 1e-6, nt)
    W, TH = np.meshgrid(ws, ths, indexing='ij')
    r1, r2, _ = circ_resid(W, TH, a1, a2, dv)
    fin = np.isfinite(r1) & np.isfinite(r2)
    s1 = np.where(fin, np.sign(r1), 0.0)
    s2 = np.where(fin, np.sign(r2), 0.0)

    def cells(s):
        return ((s[:-1, :-1] != s[1:, :-1]) | (s[:-1, :-1] != s[:-1, 1:])
                | (s[:-1, :-1] != s[1:, 1:]))

    out = []
    for i, j in np.argwhere(cells(s1) & cells(s2)):
        x = np.array([ws[i], ths[j]])
        for _ in range(300):
            q1, q2, _ = circ_resid(x[0], x[1], a1, a2, dv)
            f0 = np.array([float(q1), float(q2)])
            J = np.zeros((2, 2))
            for k, h in enumerate((1e-11, 1e-8)):
                xp = x.copy()
                xp[k] += h
                b1, b2, _ = circ_resid(xp[0], xp[1], a1, a2, dv)
                J[:, k] = (np.array([float(b1), float(b2)]) - f0) / h
            try:
                d = np.linalg.solve(J, -f0)
            except np.linalg.LinAlgError:
                break
            lim = np.array([0.2 * abs(x[0]), 0.3])
            sc = min([1.0] + [lim[k] / abs(d[k]) for k in range(2) if d[k]])
            x = x + d * sc
            if x[0] <= 0 or not 0 < x[1] < math.pi:
                break
            q1, q2, _ = circ_resid(x[0], x[1], a1, a2, dv)
            if abs(float(q1)) < 1e-12 and abs(float(q2)) < 1e-9:
                break
        q1, q2, amp = circ_resid(x[0], x[1], a1, a2, dv)
        if not (abs(float(q1)) < 1e-8 and abs(float(q2)) < 1e-4):
            continue
        w, th, amp = float(x[0]), float(x[1]), float(amp)
        if amp <= 0 or amp > aceil or w <= 0:
            continue
        rad = (GM / w ** 2) ** (1.0 / 3.0)
        sini = amp / (GM / rad ** 2)
        if not 0 < sini <= 1.0:
            continue
        P = 2 * math.pi / w
        if any(abs(o['P'] - P) < 1e-3 for o in out):
            continue
        out.append(dict(P=P, Pd=P / 86400.0, w=w, A=amp, th=math.degrees(th),
                        r_au=rad / AU, sini=sini,
                        inc=math.degrees(math.asin(sini)),
                        K=amp / w, span=2 * amp / w / 1e3,
                        r1=float(q1), r2=float(q2)))
    return sorted(out, key=lambda o: o['P'])


def circ_analytic(a1=None, a2=None, dv=None, aceil=None, n=400001):
    """The same system solved independently, with the drifts read at the
    block START instead of the dwell midpoint, by the reduction that makes
    the enumeration provably complete.  The mean of a_los over the interval
    is (dv/dt), so sin(phase) obeys one scalar equation and the branches of
    the two arcsines are exhaustive."""
    a1 = A1 if a1 is None else a1
    a2 = A2 if a2 is None else a2
    dv = DV if dv is None else dv
    aceil = ACEIL if aceil is None else aceil
    rat, q = a2 / a1, dv / (DT * a1)
    smin = abs(a1) / aceil
    out = []
    for b1 in (0, 1):
        for b2 in (0, 1):
            def F(s):
                th1 = math.asin(s) if b1 == 0 else math.pi - math.asin(s)
                sb = rat * s
                if abs(sb) > 1:
                    return None
                be = math.asin(sb) if b2 == 0 else math.pi - math.asin(sb)
                u = 2 * math.pi + be - th1
                if u <= 0:
                    return None
                return (math.cos(th1) - math.cos(be)) / u - q * s

            prev = None
            for s in np.linspace(smin, 1.0, n):
                v = F(s)
                if v is None:
                    prev = None
                    continue
                if prev is not None and prev[0] * v < 0:
                    lo, hi = prev[1], s
                    for _ in range(100):
                        mid = 0.5 * (lo + hi)
                        if F(mid) * F(lo) <= 0:
                            hi = mid
                        else:
                            lo = mid
                    s0 = 0.5 * (lo + hi)
                    th1 = math.asin(s0) if b1 == 0 else math.pi - math.asin(s0)
                    be = (math.asin(rat * s0) if b2 == 0
                          else math.pi - math.asin(rat * s0))
                    u = 2 * math.pi + be - th1
                    amp, w = a1 / s0, u / DT
                    rad = (GM / w ** 2) ** (1.0 / 3.0)
                    out.append(dict(Pd=2 * math.pi / w / 86400.0, A=amp,
                                    r_au=rad / AU,
                                    sini=amp / (GM / rad ** 2),
                                    th=math.degrees(th1)))
                prev = (v, s)
    return out


# ----------------------------------------------------- Kepler, for e > 0
def kepler(Ma, e, nit=16):
    Ma = np.mod(Ma, 2 * np.pi)
    E = Ma + e * np.sin(Ma)
    for _ in range(nit):
        E = E - (E - e * np.sin(E) - Ma) / (1 - e * np.cos(E))
    return E


def ecc_state(e, om, P, Ma):
    """Unit-sin(i) line-of-sight acceleration and velocity at mean anomaly
    Ma, for a Kepler orbit of period P, eccentricity e and argument of
    periastron om about this host."""
    a = (GM * P ** 2 / (4 * np.pi ** 2)) ** (1.0 / 3.0)
    s = math.sqrt(1 - e ** 2)
    E = kepler(Ma, e)
    nu = np.arctan2(s * np.sin(E), np.cos(E) - e)
    r = a * (1 - e * np.cos(E))
    al = -(GM / r ** 2) * np.sin(nu + om)
    K = 2 * np.pi * a / (P * s)
    return al, K * (np.cos(nu + om) + e * np.cos(om)), a


def ecc_resid(e, om, P, Ma1):
    """Ma1 = mean anomaly at block 1's START.  Drifts at the dwell midpoints,
    offset between the block starts, amplitude eliminated by sin i."""
    n = 2 * np.pi / P
    am1, _, _ = ecc_state(e, om, P, Ma1 + n * T1 / 2.0)
    am2, _, _ = ecc_state(e, om, P, Ma1 + n * (DT + T2 / 2.0))
    _, v1, _ = ecc_state(e, om, P, Ma1)
    _, v2, a = ecc_state(e, om, P, Ma1 + n * DT)
    with np.errstate(divide='ignore', invalid='ignore'):
        return am2 / am1 - A2 / A1, (v2 - v1) / am1 - DV / A1, A1 / am1, a


def ecc_peak(e, om, P, sini, n=4096):
    al, _, _ = ecc_state(e, om, P, np.linspace(0, 2 * np.pi, n))
    return sini * float(np.max(np.abs(al)))


def ecc_solutions(e, om, plo=0.3 * 86400, phi=6.0 * 86400, npd=260, nm=520,
                  aceil=None):
    """Every (P, mean anomaly, inclination) that fits the three observables at
    this (e, om), with the ceiling applied to the peak |a_los| of the WHOLE
    orbit and not only to the two epochs."""
    aceil = ACEIL if aceil is None else aceil
    Ps = np.exp(np.linspace(math.log(plo), math.log(phi), npd))
    Ms = np.linspace(0, 2 * np.pi, nm, endpoint=False)
    P, Ma = np.meshgrid(Ps, Ms, indexing='ij')
    r1, r2, _, _ = ecc_resid(e, om, P, Ma)
    fin = np.isfinite(r1) & np.isfinite(r2)
    s1 = np.where(fin, np.sign(r1), 0.0)
    s2 = np.where(fin, np.sign(r2), 0.0)

    def cells(s):
        return ((s[:-1, :-1] != s[1:, :-1]) | (s[:-1, :-1] != s[:-1, 1:])
                | (s[:-1, :-1] != s[1:, 1:]))

    ij = np.argwhere(cells(s1) & cells(s2))
    if not len(ij):
        return []
    x0 = np.log(Ps[ij[:, 0]])
    x1 = Ms[ij[:, 1]].astype(float)
    for _ in range(250):
        q1, q2, _, _ = ecc_resid(e, om, np.exp(x0), x1)
        h = 1e-7
        a1g, a2g, _, _ = ecc_resid(e, om, np.exp(x0 + h), x1)
        b1g, b2g, _, _ = ecc_resid(e, om, np.exp(x0), x1 + h)
        J11, J12 = (a1g - q1) / h, (b1g - q1) / h
        J21, J22 = (a2g - q2) / h, (b2g - q2) / h
        det = J11 * J22 - J12 * J21
        with np.errstate(divide='ignore', invalid='ignore'):
            d0 = (-q1 * J22 + q2 * J12) / det
            d1 = (-q2 * J11 + q1 * J21) / det
        d0 = np.where(np.isfinite(d0), d0, 0.0)
        d1 = np.where(np.isfinite(d1), d1, 0.0)
        nn = np.maximum(np.abs(d0), np.abs(d1))
        sc = np.where(nn > 0.3, 0.3 / np.maximum(nn, 1e-30), 1.0)
        x0 = np.clip(x0 + d0 * sc, math.log(0.05 * 86400),
                     math.log(200 * 86400))
        x1 = x1 + d1 * sc
    q1, q2, sini, _ = ecc_resid(e, om, np.exp(x0), x1)
    good = ((np.abs(q1) < 1e-11) & (np.abs(q2) < 1e-8)
            & (sini > 0) & (sini <= 1.0))
    out, seen = [], []
    for k in np.where(good)[0]:
        Pd = float(np.exp(x0[k]) / 86400.0)
        if any(abs(s - Pd) < 1e-5 for s in seen):
            continue
        seen.append(Pd)
        pk = ecc_peak(e, om, float(np.exp(x0[k])), float(sini[k]))
        _, _, _, a = ecc_resid(e, om, float(np.exp(x0[k])), float(x1[k]))
        out.append(dict(e=e, om=math.degrees(om) % 360.0, Pd=Pd,
                        Ma1=math.degrees(x1[k]) % 360.0, sini=float(sini[k]),
                        inc=math.degrees(math.asin(float(sini[k]))),
                        apk=pk, ok=bool(pk <= aceil), a_au=float(a) / AU))
    return out


# =========================================================================
print('\n%s  round %d  drive %d' % (os.path.basename(__file__), ROUND, DRIVE))
print('pair %s/%s  dt %.1f s  drifts %.2f, %.2f Hz/s  dnu %+.4f MHz'
      % (PAIR['cidlo'], PAIR['cidhi'], DT, D1, D2, DNU / 1e6))
print('a_los %.5f, %.5f m/s2 (+-%.5f, %.5f)  mean %.5f  ceiling %.3f'
      % (A1, A2, E1, E2, ABAR, ACEIL))

# ---- O1  the pair's own published numbers, from the frozen inputs
mass_r18 = json.load(open(os.path.join(V, 'masses_r18.json')))
_mm = [v for k, v in (mass_r18.get('stars') or mass_r18).items()
       if 'Pic' in k] if isinstance(mass_r18, dict) else []
_mv = None
for _e in _mm:
    _mv = (_e.get('mass_msun') if isinstance(_e, dict) else _e)
_pubspan = (2.0 * (GM / (PUB['r_au'] * AU) ** 2 * math.sin(
    math.radians(PUB['inc_deg'])))
    / math.sqrt(GM / (PUB['r_au'] * AU) ** 3) / 1e3)
ck('O1 the three observables and the orbit being replaced are reproduced from '
   'the frozen inputs, the host mass is the one the manuscript and the mass '
   'table carry, and the frozen record of that orbit still agrees with the '
   'macro layer it was taken from',
   abs(abs(DV) / 1e3 - float(macro('TjBpDvKms'))) < 0.5
   and abs(abs(ABAR) - float(macro('TjBpAccelReq'))) < 5e-3
   and abs(MASS - 1.75) < 1e-9
   and (_mv is None or abs(float(_mv) - MASS) < 0.02)
   and abs(float(macro('TjBpDriftLo')) - D1) < 1.0
   and abs(float(macro('TjBpDriftHi')) - D2) < 1.0
   and abs(float(macro('WdAGrid')) - ACEIL) < 0.005
   and abs(_pubspan - PUB['span_kms']) < 1.5
   and all(abs(PUBLIVE[k] - PUB[k]) < 1e-9 for k in PUBLIVE),
   'dv %.2f vs %s km/s; mean a %.4f vs %s; mass %.2f (table %s); ceiling '
   '%.3f vs %s; the named orbit spans %.1f vs %s km/s published; %d of 5 '
   'frozen values still live and agreeing'
   % (abs(DV) / 1e3, macro('TjBpDvKms'), abs(ABAR), macro('TjBpAccelReq'),
      MASS, _mv, ACEIL, macro('WdAGrid'), _pubspan, PUB['span_kms'],
      len(PUBLIVE)))

# ---- O2  the orbit the text names cannot have produced this pair
PUB_INC = math.radians(PUB['inc_deg'])
PUB_AU = PUB['r_au']
PUB_PD = PUB['p_d']
pub_r = PUB_AU * AU
pub_w_kep = math.sqrt(GM / pub_r ** 3)          # Kepler rate at that radius
pub_A = GM / pub_r ** 2 * math.sin(PUB_INC)
if DRIVE == 2:
    # O2: a pair the quoted orbit COULD have produced -- its own accelerations
    # at one phase, substituted for the measured ones BEFORE the test reads
    # them, so that every clause of the check sees a consistent pair.
    _u = pub_w_kep * DT
    A1 = pub_A * math.sin(0.7)
    A2 = pub_A * math.sin(0.7 + _u)
pub = []
for tag, w in (('kepler', pub_w_kep), ('asquoted', 2 * math.pi / (PUB_PD * 86400))):
    u = w * DT
    # the phase at which the quoted orbit matches the measured RATIO, and the
    # largest |a_los(t1)| it can then deliver
    th = math.atan2(math.sin(u), (A2 / A1) - math.cos(u))
    amax = abs(pub_A * math.sin(th))
    # and the best it can do on the two accelerations jointly
    g = np.linspace(0, 2 * math.pi, 2000001)
    chi2 = ((pub_A * np.sin(g) - A1) / E1) ** 2 \
        + ((pub_A * np.sin(g + u) - A2) / E2) ** 2
    k = int(np.argmin(chi2))
    pub.append(dict(tag=tag, Pd=2 * math.pi / w / 86400.0,
                    advance=math.degrees(u) % 360.0, A=pub_A,
                    span=2 * pub_A / w / 1e3, amax_ratio=amax,
                    factor=abs(A1) / amax, chi2=float(chi2[k]),
                    best_a1=float(pub_A * np.sin(g[k])),
                    best_a2=float(pub_A * np.sin(g[k] + u))))
ck('O2 the orbit the text names cannot produce this pair: at the measured '
   'ratio of the two accelerations it delivers at most a tenth of the first '
   'one, and no phase fits the pair',
   all(p['factor'] > 10.0 and p['chi2'] > 100.0 for p in pub)
   and abs(A1) > 10 * pub[0]['amax_ratio'],
   '; '.join('%s P %.4f d, advance %.2f deg, max|a1| %.4f vs %.4f (x%.1f), '
             'best chi2 %.3g' % (p['tag'], p['Pd'], p['advance'],
                                 p['amax_ratio'], abs(A1), p['factor'],
                                 p['chi2']) for p in pub))

# ---- O3  the circular solution, enumerated completely
WMAX = 2.0 * ACEIL / abs(DV)
ACE_USE = ACEIL
if DRIVE == 3:            # O3: a ceiling below the solution's own amplitude
    ACE_USE = 2.0
SOL = circ_solutions(aceil=ACE_USE)
WIDE = circ_solutions(aceil=ACE_USE, wtop=3.0 * WMAX, nw=6001, nt=4001)
ANA = circ_analytic(aceil=ACE_USE)
COARSE = circ_solutions(aceil=ACE_USE, nw=1201, nt=1201)
if DRIVE == 4:
    # O3, from the other side: twice the ceiling admits a second solution, at
    # 0.647 d with an amplitude of 6.3 m/s2, so the count is no longer one.
    SOL = circ_solutions(aceil=2.0 * ACEIL)
for s in SOL:
    print('   circular: P %.5f d  i %.3f deg  r %.5f au  A %.4f  span %.1f '
          'km/s  phase %.2f deg' % (s['Pd'], s['inc'], s['r_au'], s['A'],
                                    s['span'], s['th']))
W = SOL[0] if SOL else None
ck('O3 exactly one circular orbit reproduces both drifts and the offset '
   'inside the ceiling; the enumeration is complete (the ceiling bounds the '
   'period from below), survives a wider box and a coarser grid, and a '
   'second, analytic solution of the same system agrees',
   len(SOL) == 1 and len(WIDE) == 1 and len(COARSE) == 1
   and len([a for a in ANA if abs(a['A']) <= ACE_USE]) == 1
   and abs(SOL[0]['Pd'] - WIDE[0]['Pd']) < 1e-6
   and abs(SOL[0]['Pd'] - COARSE[0]['Pd']) < 1e-6
   and abs(SOL[0]['Pd']
           - [a for a in ANA if abs(a['A']) <= ACE_USE][0]['Pd']) < 0.01,
   '%d in the box (P >= %.4f d), %d in a 3x box, %d on a coarse grid, %d '
   'analytic; P %.5f vs %.5f d analytic' % (
       len(SOL), 2 * math.pi / (WMAX * 1.02) / 86400.0, len(WIDE),
       len(COARSE), len([a for a in ANA if abs(a['A']) <= ACE_USE]),
       SOL[0]['Pd'] if SOL else float('nan'),
       ([a for a in ANA if abs(a['A']) <= ACE_USE] or [dict(Pd=float('nan'))])
       [0]['Pd']))

# ---- O4  the solution is consistent with the search that measured it
LIN = []
if W:
    for k, (T, meas) in enumerate(((T1, D1), (T2, D2))):
        t = np.linspace(0, T, 1025) + (0.0 if k == 0 else DT)
        ph = W['w'] * t + math.radians(W['th']) - W['w'] * (T1 / 2.0)
        nu = NUR * (1.0 + (W['A'] / W['w']) * np.cos(ph) / C)
        tb = t - t.mean()
        slope = float(np.dot(tb, nu - nu.mean()) / np.dot(tb, tb))
        resid = nu - (nu.mean() + slope * tb)
        # ★ what the comparison has to be against.  One step of the drift grid
        # the window was searched on displaces the track by step*T across the
        # dwell -- half a channel, by construction of the grid -- so curvature
        # smaller than that is below the resolution at which the drift the
        # model is fitting was measured in the first place.
        step = PAIR['steplo'] if k == 0 else PAIR['stephi']
        LIN.append(dict(slope=slope, meas=meas,
                        dev_hz=float(np.max(np.abs(resid))),
                        dev_chan=float(np.max(np.abs(resid)) / CHANW),
                        rms_chan=float(np.std(resid) / CHANW),
                        step_chan=step * T / CHANW))
        print('   block %d: fitted slope %.3f Hz/s vs measured %.3f; '
              'curvature displaces the track by %.1f kHz = %.3f channel peak, '
              '%.3f rms, against %.3f channel for one drift-grid step'
              % (k + 1, slope, meas, LIN[-1]['dev_hz'] / 1e3,
                 LIN[-1]['dev_chan'], LIN[-1]['rms_chan'],
                 LIN[-1]['step_chan']))
ck('O4 the solution is consistent with the linear-drift search that measured '
   'it: over each dwell its track departs from the fitted straight line by '
   'less than a channel, and by no more than one step of the drift grid the '
   'window was searched on, so the slope it would have fitted is the measured '
   'drift',
   bool(LIN) and all(x['dev_chan'] < 1.0 and x['rms_chan'] < 0.5
                     and x['dev_chan'] < 1.2 * x['step_chan'] for x in LIN)
   and all(abs(x['slope'] - x['meas']) < 0.5 for x in LIN),
   'departures %s channel peak, %s rms, grid step %s channel; slope '
   'residuals %s Hz/s'
   % (', '.join('%.3f' % x['dev_chan'] for x in LIN),
      ', '.join('%.3f' % x['rms_chan'] for x in LIN),
      ', '.join('%.3f' % x['step_chan'] for x in LIN),
      ', '.join('%+.3f' % (x['slope'] - x['meas']) for x in LIN)))

# ---- O5  the family the measurement errors allow
BOX = []
for i in (-1, 0, 1):
    for j in (-1, 0, 1):
        for k in (-1, 0, 1):
            ss = circ_solutions(a1=A1 + i * E1, a2=A2 + j * E2,
                                dv=DV + k * EDV, aceil=ACE_USE, nw=2001,
                                nt=2001)
            BOX.append((i, j, k, ss))
HIT = [s for _, _, _, ss in BOX for s in ss]
rng = {q: (min(s[q] for s in HIT), max(s[q] for s in HIT))
       for q in ('Pd', 'inc', 'r_au', 'A', 'span')} if HIT else {}
ck('O5 every corner of the error box the referee asks for -- half a grid step '
   'on each drift, half a channel on each frequency -- still admits exactly '
   'one orbit, and the solution moves by less than its own rounding',
   all(len(ss) == 1 for _, _, _, ss in BOX)
   and rng and rng['Pd'][1] - rng['Pd'][0] < 0.02
   and rng['inc'][1] - rng['inc'][0] < 0.2,
   '27 corners, %d with one solution; P %.4f-%.4f d, i %.3f-%.3f deg, '
   'r %.5f-%.5f au, A %.4f-%.4f'
   % (sum(1 for _, _, _, ss in BOX if len(ss) == 1),
      rng['Pd'][0], rng['Pd'][1], rng['inc'][0], rng['inc'][1],
      rng['r_au'][0], rng['r_au'][1], rng['A'][0], rng['A'][1])
   if rng else 'no solution at some corner')

# ---- O6  the eccentric family, and what limits it
ECC, EGRID = [], [0.0, 0.05, 0.1, 0.15, 0.2, 0.25, 0.3, 0.4, 0.5, 0.7]
OMS = np.linspace(0, 2 * np.pi, 24, endpoint=False)
for e in EGRID:
    sub = []
    for om in OMS:
        sub += ecc_solutions(e, float(om),
                             aceil=1e3 if DRIVE == 7 else ACE_USE)
    ECC += sub
    ok = [s for s in sub if s['ok']]
    print('   e = %.2f: %3d solutions, %3d inside the ceiling%s'
          % (e, len(sub), len(ok),
             '' if not ok else '  P %.4f-%.4f d, i %.2f-%.2f deg'
             % (min(s['Pd'] for s in ok), max(s['Pd'] for s in ok),
                min(s['inc'] for s in ok), max(s['inc'] for s in ok))))
EOK = [s for s in ECC if s['ok']]
EMAX = max([s['e'] for s in EOK], default=0.0)
ENONE = min([e for e in EGRID if e > EMAX
             and not [s for s in EOK if s['e'] == e]], default=None)
E0 = [s for s in EOK if s['e'] == 0.0]
ck('O6 the eccentric family exists, is limited by the ceiling and not by the '
   'data, and reduces to the circular solution at e = 0',
   bool(EOK) and EMAX > 0.0 and EMAX < 0.5
   and bool(E0) and W is not None
   and all(abs(s['Pd'] - W['Pd']) < 1e-3 and abs(s['inc'] - W['inc']) < 0.05
           for s in E0)
   and all(s['apk'] > ACE_USE for s in ECC if s['e'] > EMAX + 1e-9),
   'eccentric solutions inside the ceiling up to e = %.2f (none at e = %s); '
   'e=0 recovers P %.5f d, i %.3f deg against %.5f, %.3f'
   % (EMAX, ENONE, E0[0]['Pd'] if E0 else float('nan'),
      E0[0]['inc'] if E0 else float('nan'),
      W['Pd'] if W else float('nan'), W['inc'] if W else float('nan')))

# the eccentricity boundary, refined between the grid points that bracket it
EHI = EMAX
if EOK and ENONE is not None:
    lo, hi = EMAX, ENONE
    for _ in range(6):
        mid = 0.5 * (lo + hi)
        hit = any(s['ok'] for om in OMS
                  for s in ecc_solutions(mid, float(om), aceil=ACE_USE))
        if hit:
            lo = mid
        else:
            hi = mid
    EHI = lo
print('   eccentricity boundary refined to e = %.3f' % EHI)

# ---- O7  the verdict, and the counts that would have moved
if DRIVE == 8:            # O7: the verdict this generator is defending
    PAIR['verdict'] = 'needs a drift outside the searched range'
OPEN = [q for q in PAIRS['pairs'] if q['verdict'] == 'not separable']
EXCL = [q for q in PAIRS['pairs']
        if q['verdict'] == 'needs a drift outside the searched range']
ck('O7 the verdict stands on an orbit that fits, so no count moves: the pair '
   'is open, and the open and separated counts are the ones the manuscript '
   'prints',
   PAIR['verdict'] == 'not separable' and W is not None
   and len(OPEN) == int(macro('TjNOpen'))
   and len(EXCL) == int(macro('TjNExcl')),
   '%s; %d open vs %s printed, %d separated vs %s printed'
   % (PAIR['verdict'], len(OPEN), macro('TjNOpen'), len(EXCL),
      macro('TjNExcl')))

# ------------------------------------------------------------- the macros
if W:
    m('ObDayBp', '%.2f' % W['Pd'])
    m('ObIncBp', '%.1f' % W['inc'])
    m('ObAuBp', '%.4f' % W['r_au'])
    m('ObSpanBp', '%.0f' % W['span'])
    m('ObPeakBp', '%.2f' % W['A'])
    m('ObEccMaxBp', '%.2f' % EHI)
    m('ObPubFacBp', '%.0f' % pub[0]['factor'])
    m('ObNCircBp', '%d' % len(SOL))
    m('ObDayLoBp', '%.2f' % rng['Pd'][0])
    m('ObDayHiBp', '%.2f' % rng['Pd'][1])
    m('ObIncLoBp', '%.1f' % rng['inc'][0])
    m('ObIncHiBp', '%.1f' % rng['inc'][1])

print('')
for k, v in M:
    print('  \\%-16s %s' % (k, v))
with open(OUT, 'w') as fh:
    fh.write('%% generated by orbit_r19.py (round %d) -- do not edit\n'
             % ROUND)
    for k, v in M:
        fh.write('\\newcommand{\\%s}{%s}\n' % (k, v))
json.dump(dict(pair=PAIR, a_los=[A1, A2], err=[E1, E2, EDV], dv=DV,
               mean_accel=ABAR, ceiling=ACEIL, mass_msun=MASS,
               published=pub, circular=SOL, circular_wide=WIDE,
               circular_analytic=ANA, box=[dict(i=i, j=j, k=k, n=len(ss),
                                                sol=ss)
                                           for i, j, k, ss in BOX],
               box_range=rng, linearity=LIN, eccentric=ECC, ecc_max=EHI,
               verdict=PAIR['verdict'], n_open=len(OPEN), n_excl=len(EXCL),
               drive=DRIVE, fail=FAIL),
          open(OUTJ, 'w'), indent=1, default=float)
print('\n%s  %s' % (OUT, 'FAIL: ' + ','.join(FAIL) if FAIL else 'all PASS'))
sys.exit(1 if FAIL else 0)
