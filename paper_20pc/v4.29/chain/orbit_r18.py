#!/usr/bin/env python3
r"""orbit_r18.py -- the orbital-reversal bound behind the pair verdicts,
re-derived with each host's own mass, with eccentric orbits, and over
orientation.  Round 803.  Writes `survey_numbers_round803.tex` and
`orbit_r18.json`.

WHY THIS EXISTS.  The pair test disposes of a pair of crossings in one of
three ways, and two of the three "no" verdicts rest on a reversal timescale:
the line-of-sight acceleration a single carrier would need to swing across
the searched range faster than orbital motion about the host star can swing
it.  The bound published for that is the quarter period of the tightest
circular orbit about a star of AT MOST two solar masses, at the drift grid's
own acceleration ceiling.  Three things are wrong with it, and they do not
all point the same way.

 1. THE HOST MASS RUNS THE WRONG WAY.  At fixed peak acceleration the
    circular period is P = 2 pi (GM)^(1/4) a^(-3/4), so it GROWS with mass:
    a lower-mass host permits a FASTER reversal.  An upper bound on the mass
    therefore selects the SLOWEST admissible reversal, which is the most
    generous possible comparison to our own exclusion and not the tightest.
    The quantity needed is the host's own mass.  For beta Pic that lowers
    the bound; for HD 14055, an A1 V star heavier than the two solar masses
    assumed, it raises it.

 2. ECCENTRICITY IS IGNORED.  An orbit whose periastron sits at the same
    acceleration ceiling sweeps the acceleration vector faster there, by
    sqrt(1+e) in the angular rate, so the fastest admissible reversal is
    shorter than the circular one by that factor -- up to sqrt(2) for a
    bound orbit.  The factor is derived below and checked against an exact
    Kepler sweep, which is slower than the bound: sqrt(1+e) is generous, as
    a bound used against our own exclusion should be.

 3. AND THE CEILING DOES NOT BOUND THE REVERSAL AT ALL.  This is not a
    correction but a withdrawal, and it is measured here rather than
    argued.  What the search bounds is the LINE-OF-SIGHT component of the
    acceleration, because that is what the drift grid covers.  Tilt the
    orbit: at inclination sin i = s the same ceiling admits an orbit s^(1/2)
    times smaller, whose angular rate is s^(-3/4) times higher, so the
    line-of-sight acceleration reverses s^(-3/4) times faster while never
    leaving the ceiling.  As s falls the admissible reversal time falls
    without limit.  The VELOCITY excursion is not like this -- it is bounded
    by (GM a)^(1/4) over all inclinations, which is why the widened window
    of S5.6 survives the same scrutiny and is rechecked below -- but the
    reversal time has no bound, and the two reversal verdicts cannot stand.

WHAT THIS GENERATOR THEREFORE PUBLISHES.  The corrected margins at each
host's own mass (which is what a reader who checks the arithmetic will
compute), the eccentricity at which each one fails, the explicit tilted
orbit that defeats each one at the same ceiling, and the counts of the new
partition: one pair separated, the rest open.  It also rechecks the one
place the same ceiling IS used correctly -- the velocity excursion the
widened recurrence window has to span -- at the sample's own masses and
over orientation, so that the sentence quoting it can keep its claim.

THE CONVENTION IS NOT CHANGED.  `pairs_v415.py` compares the time
tau = 2a_ceil / (c nuddot / nu) -- the time a constant rate would take to
cross the whole searched range -- with the quarter period.  That comparison
is 4/pi stricter than comparing the required rate with the orbit's own
maximum rate, i.e. it is conservative, and this generator leaves it exactly
as it is: one input is changed at a time, and the reproduction of every
published number at two solar masses is the first assertion.

Usage: orbit_r18.py [--drive N]
"""
import csv
import glob
import json
import math
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
V = os.path.dirname(os.path.abspath(__file__))   # the tree this lives in
ROUND = 803
DRIVE = int(sys.argv[sys.argv.index('--drive') + 1]) if '--drive' in sys.argv \
    else 0
SFX = '' if DRIVE == 0 else '_drive%d' % DRIVE
# ★ DERIVED FROM `ROUND`, NEVER TYPED AGAIN.  This literal used to
# carry the round number a second time, and when the round was moved
# off `r18-census`'s claim the constant changed and this did not --
# so this generator silently overwrote another generator's published
# round file.  That is the defect `roundcollide` exists for, and it
# resolves a format-built name, so it would have caught the next one.
OUT = os.path.join(HERE, 'numbers/survey_numbers_round%d%s.tex' % (ROUND, SFX))
OUTJ = os.path.join(HERE, 'orbit_r18%s.json' % SFX)

CKMS = 299792.458
C = CKMS * 1e3
GMSUN = 1.32712440018e20
AU = 1.495978707e11
MSUN_PUB = 2.0            # the bound the published verdicts were built on

M, FAIL = [], []


def m(k, v):
    assert k.isalpha(), 'a LaTeX macro name may contain letters only: ' + k
    assert k not in dict(M), 'macro defined twice: ' + k
    M.append((k, str(v)))


def ck(name, cond, detail=''):
    if not cond:
        FAIL.append(name)
    print('  %-70s %s  %s' % (name, 'PASS' if cond else 'FAIL', detail))


def macro(name):
    """One macro's value out of the frozen layer of the manuscript."""
    pat = re.compile(r'\\newcommand\{\\%s\}\{(.*)\}\s*$' % name)
    for p in sorted(glob.glob(os.path.join(V, 'numbers/survey_numbers*.tex'))):
        if '_drive' in p:
            continue
        for line in open(p):
            mm = pat.match(line.strip())
            if mm:
                return mm.group(1)
    raise KeyError(name)


def tname(s):
    s = s.split(' Gaia')[0].strip()
    s = re.sub(r'^HD(\d)', r'HD \1', s)
    s = s.replace('HD14055', 'HD 14055').replace('bet Pic', r'$\beta$~Pic')
    s = s.replace('eta Crv', r'$\eta$~Crv').replace('BD05', 'BD+05')
    return s.replace(' ', '~').replace('-', '$-$')


# ---------------------------------------------------------------- inputs
PAIRS = json.load(open(os.path.join(V, 'pairs_v415.json')))
#: ★★★ THE PRE-WITHDRAWAL MARGINS, FROZEN.  O1 below exists to prove this
#: generator is the manuscript's own arithmetic with one input changed, and the
#: per-pair `ratio` it reproduced is DELETED from `pairs_v415.py` by the
#: withdrawal this generator motivates.  Reading it out of the live record
#: after the patch would leave O1 comparing nothing -- a check that cannot
#: fail.  So the quantities as the build published them before the withdrawal
#: are frozen in `r18inputs/pairs_published_r18.json` and O1 reproduces those,
#: while the ARITHMETIC anchors that survive in the macro layer
#: (\TjTauOrbH, \TjVorbKms, \TjROrbAu) are still asserted against the live
#: build.  Both halves are needed: the frozen file alone could drift from the
#: tree, and the macros alone do not reach the per-pair margins.
PUB = json.load(open(os.path.join(V, 'r18inputs',
                                  'pairs_published_r18.json')))
CAT = list(csv.DictReader(open(os.path.join(
    V, 'per_target_results_v3.99.csv'))))
LED = json.load(open(os.path.join(V, 'ledger.json')))['rows']
CROSS = json.load(open(os.path.join(V, 'r10inputs',
                                    'recur_v411.json')))['crossings']
MASS = json.load(open(os.path.join(HERE, 'masses_r18.json')))
SPT = json.load(open(os.path.join(HERE, 'hosts_sptype_r18.json')))['hosts']

# the acceleration ceiling, read from the catalogue exactly as the pair test
# and the widened-window generator read it: one number for the whole survey.
AG = sorted({round(float(r['a_max_m_s2']), 3) for r in CAT
             if r['a_max_m_s2']})[0]


def canon(s):
    """The ledger's star string reduced to the mass table's key."""
    s = s.split(' Gaia')[0].strip()
    return MASS['alias'].get(s, s)


def mass_of(star):
    k = canon(star)
    rec = MASS['stars'].get(k)
    return (float(rec['mass_msun']), rec) if rec else (None, None)


# ===================================================== the orbital relations
def tau_circ(msun, a=None):
    """Quarter period of the circular orbit whose acceleration is the
    ceiling: (pi/2) (GM)^(1/4) a^(-3/4).  Identical to PORB/4 as
    `pairs_v415.py` forms it, which O1 asserts."""
    a = AG if a is None else a
    gm = GMSUN * msun
    if DRIVE == 1:                    # O2: the mass exponent inverted
        return 0.5 * math.pi * gm ** -0.25 * a ** -0.75 * (GMSUN ** 0.5)
    return 0.5 * math.pi * gm ** 0.25 * a ** -0.75


def v_circ(msun, a=None):
    """Line-of-sight velocity amplitude of that orbit, (GM a)^(1/4)."""
    a = AG if a is None else a
    return (GMSUN * msun * (AG if a is None else a)) ** 0.25


def r_circ(msun, a=None):
    a = AG if a is None else a
    return math.sqrt(GMSUN * msun / a)


def adot_circ(msun, a=None):
    """The largest rate of change of the line-of-sight acceleration that
    orbit reaches: a times its angular rate."""
    a = AG if a is None else a
    return a * 0.5 * math.pi / tau_circ(msun, a)


# the rate the pair test's own convention demands of a carrier
def adot_req(tau):
    return 2.0 * AG / tau


# =============================================== 1. REPRODUCE THE PUBLISHED
# Nothing below is trustworthy unless this generator is the same arithmetic
# as the one in the manuscript with one input changed, so the published
# bound and every published margin are reproduced first, to the printed
# digit, at two solar masses and zero eccentricity.
TAU_PUB = PUB['tau_orb_s']
P_PUB = PUB['porb_s']
# ★ GEN (v4.29 fold): the survey's acceleration ceiling is the MINIMUM a_max over the catalogue rows, and the
#   fold's re-run export rows for alpha CMa B X579 (two descending Band 4 windows) carry the deposited extractor's
#   drift_max, which puts their a_max at 3.597 against 3.598 everywhere else (a code-version rounding; \WdAGrid
#   still prints 3.6).  The frozen pre-withdrawal record was computed at the PRE-FOLD ceiling, so it is reproduced
#   at that ceiling, taken INDEPENDENTLY of the record as the minimum a_max over the catalogue rows the fold did
#   NOT re-run (1,605 rows; unchanged by the fold), and O1 then tests the arithmetic exactly as before.  The live
#   ceiling may lie below it only by catalogue rounding (<= 0.001) and only through rows the fold re-ran; the live
#   pair test is checked against the live ceiling.  Before the fold A_PUB == AG and this is the old assertion.
import refoldpop_r29                                            # noqa: E402
_RR29 = refoldpop_r29.rerun_keys()
A_PUB = min(round(float(r['a_max_m_s2']), 3) for r in CAT if r['a_max_m_s2']
            and refoldpop_r29.wkey(r['eb'], r['flo_GHz'], r['fhi_GHz']) not in _RR29)
_below = [r for r in CAT if r['a_max_m_s2'] and round(float(r['a_max_m_s2']), 3) < A_PUB]
assert (AG <= A_PUB <= AG + 0.001 + 1e-9
        and all(refoldpop_r29.wkey(r['eb'], r['flo_GHz'], r['fhi_GHz']) in _RR29 for r in _below)), (
    'the ceiling of the rows the fold did not re-run (%.3f) and the live ceiling (%.3f) differ by more than '
    'catalogue rounding, or through a row the fold did not re-run: %s'
    % (A_PUB, AG, [(r['eb'], r['flo_GHz']) for r in _below][:5]))
TAU_MINE = tau_circ(MSUN_PUB, A_PUB)
assert (len([p for p in PUB['pairs'] if p['verdict'] == 'excluded'])
        == PUB['n_excluded']
        and len([p for p in PUB['pairs'] if p['verdict'] == 'not separable'])
        == PUB['n_open']), (
    'the frozen pre-withdrawal record does not hold the partition it '
    'declares: %d excluded / %d open against %d / %d'
    % (len([p for p in PUB['pairs'] if p['verdict'] == 'excluded']),
       len([p for p in PUB['pairs'] if p['verdict'] == 'not separable']),
       PUB['n_excluded'], PUB['n_open']))
assert abs(PAIRS['tau_orb_s'] - tau_circ(MSUN_PUB, AG)) < 1e-9 * TAU_PUB, (
    'the live pair test and this generator disagree about the '
    'quarter period the ceiling implies at %s Msun: %r against %r'
    % (PUB['msun_max'], tau_circ(MSUN_PUB, AG), PAIRS['tau_orb_s']))
_tau = [p for p in PUB['pairs'] if p['tau'] is not None]
for p in _tau:
    p['tau'] = float(p['tau'])
    p['ratio_pub'] = float(p['ratio'])
    p['ratio_mine'] = TAU_MINE / p['tau']
_etau = [p for p in _tau if p['verdict'] == 'excluded']
_egrid = [p for p in PUB['pairs']
          if p['verdict'] == 'needs a drift outside the searched range']
_open = [p for p in PUB['pairs'] if p['verdict'] == 'not separable']
_ctl = [p for p in PUB['pairs'] if p['verdict'] == 'one trajectory']
BP = [p for p in _etau if 'bet Pic' in p['star']]
if DRIVE == 2:                        # O1: a bound that is not the published
    TAU_MINE *= 1.05
ck('O1 the published reversal bound and every published margin are '
   'reproduced at two solar masses and zero eccentricity, so what follows '
   'differs from the manuscript by the inputs and not by the arithmetic',
   abs(TAU_MINE - TAU_PUB) < 1e-6 * TAU_PUB
   and abs(4.0 * TAU_PUB - P_PUB) < 1e-9 * P_PUB
   and '%.0f' % (tau_circ(MSUN_PUB, AG) / 3600.0) == macro('TjTauOrbH')
   and '%.0f' % (v_circ(MSUN_PUB) / 1e3) == macro('TjVorbKms')
   and '%.3f' % (r_circ(MSUN_PUB) / AU) == macro('TjROrbAu')
   and all(abs(p['ratio_mine'] - p['ratio_pub']) < 2e-9 for p in _tau)
   and len(BP) == 1
   and '%.1f' % BP[0]['ratio_mine'] == PUB['bp_ratio_printed'],
   'bound %.1f h against %s h published; %d margins reproduced; beta Pic '
   '%.4f against %s printed' % (TAU_MINE / 3600.0, macro('TjTauOrbH'),
                                len(_tau),
                                BP[0]['ratio_mine'] if BP else -1,
                                PUB['bp_ratio_printed']))

# =============================================== 2. THE MASS RUNS ONE WAY
_m1, _m2 = 0.5, 2.0
ck('O2 the quarter period grows as the fourth root of the host mass, so a '
   'LOWER mass permits a faster reversal and an upper bound on the mass is '
   'the most generous comparison available rather than the tightest',
   abs(tau_circ(_m2) / tau_circ(_m1) - (_m2 / _m1) ** 0.25) < 1e-12
   and tau_circ(_m1) < tau_circ(_m2)
   and all(tau_circ(x) < tau_circ(y) for x, y in
           zip([0.1, 0.3, 1.0, 1.75, 2.33], [0.3, 1.0, 1.75, 2.33, 3.0])),
   '%.1f h at %.2f Msun against %.1f h at %.2f; ratio %.6f against the '
   'fourth root %.6f' % (tau_circ(_m1) / 3600.0, _m1,
                         tau_circ(_m2) / 3600.0, _m2,
                         tau_circ(_m2) / tau_circ(_m1),
                         (_m2 / _m1) ** 0.25))

# ======================================== 3. THE ECCENTRIC SWEEP, EXACTLY
# An orbit with periastron at the ceiling has angular rate sqrt(1+e) times
# the circular rate THERE, so the time to turn the acceleration vector
# through a right angle is at most the circular quarter period divided by
# sqrt(1+e).  That is a bound and not a value: away from periastron the rate
# falls, so the exact Kepler sweep takes longer.  Both are computed, and the
# assertion is that the bound is the generous one -- a bound used against our
# own exclusion must err that way.
def sweep_exact(e, n=200001):
    """Time for the true anomaly to run from -45 to +45 degrees, in units of
    the circular quarter period at periastron: integrate dt = r^2 dtheta / h
    with r = r_p (1+e)/(1+e cos theta), h = sqrt(GM r_p (1+e))."""
    rp, gm = 1.0, 1.0
    h = math.sqrt(gm * rp * (1.0 + e))
    th = [(-0.25 + 0.5 * i / (n - 1)) * math.pi for i in range(n)]
    tot = 0.0
    for i in range(n - 1):
        for t in (th[i], th[i + 1]):
            r = rp * (1.0 + e) / (1.0 + e * math.cos(t))
            tot += 0.5 * (th[i + 1] - th[i]) * r * r / h
    # the circular quarter period at the same radius r_p is (pi/2) sqrt(rp^3/gm)
    return tot / (0.5 * math.pi * math.sqrt(rp ** 3 / gm))


ECC_GRID = [0.0, 0.2, 0.4, 0.55, 0.7, 0.9, 0.99, 0.999]
SWEEP = {e: sweep_exact(e) for e in ECC_GRID}
_bound = {e: 1.0 / math.sqrt(1.0 + e) for e in ECC_GRID}
if DRIVE == 3:
    #: O3: a speed-up claimed LARGER than the exact sweep, which is the
    #: direction that would matter -- it would let an eccentric orbit
    #: reverse faster than Kepler allows and withdraw an exclusion that
    #: stands.  The first version of this drive made the bound smaller,
    #: which the assertion is satisfied by, and it fired nothing.
    _bound = {e: 1.0 / (1.0 + e) ** 0.25 for e in ECC_GRID}
ck('O3 the periastron speed-up sqrt(1+e) is an UPPER bound on how much '
   'faster an eccentric orbit turns the acceleration vector: the exact '
   'Kepler sweep through a right angle about periastron is slower than it '
   'at every eccentricity, and equals it at zero',
   abs(SWEEP[0.0] - 1.0) < 1e-6
   and all(SWEEP[e] >= _bound[e] - 1e-9 for e in ECC_GRID)
   and SWEEP[0.99] < 1.0,
   'exact/circular %s against the bound %s'
   % (['%.3f' % SWEEP[e] for e in ECC_GRID],
      ['%.3f' % _bound[e] for e in ECC_GRID]))

# ============================= 4. ORIENTATION, MEASURED ON KEPLER ORBITS
# The family: a planar Kepler orbit of eccentricity e, periastron r_p, seen
# along a direction whose in-plane projection has length s = sin i and makes
# an angle phi with periastron.  Only those two orientation numbers enter,
# because r and v are in the orbital plane.  r_p is then rescaled so that the
# LARGEST line-of-sight acceleration anywhere on the orbit is exactly the
# ceiling -- which is the only thing the search constrains -- and what is
# recorded is the largest line-of-sight velocity and the largest rate of
# change of the line-of-sight acceleration that the orbit then reaches, both
# in units of the circular edge-on orbit at the same ceiling.
def family(e, s, phi, n=4001):
    """(max|a_los|, max|v_los|, max|adot_los|) for r_p = GM = 1."""
    rp, gm = 1.0, 1.0
    h = math.sqrt(gm * rp * (1.0 + e))
    amax = vmax = dmax = 0.0
    prev = None
    for i in range(n):
        th = 2.0 * math.pi * i / (n - 1) - math.pi
        r = rp * (1.0 + e) / (1.0 + e * math.cos(th))
        thdot = h / (r * r)
        rdot = rp * (1.0 + e) * e * math.sin(th) * thdot \
            / (1.0 + e * math.cos(th)) ** 2
        # unit vectors; the line of sight projects onto the plane as
        # (cos phi, sin phi) with length s
        cr, sr = math.cos(th), math.sin(th)
        rhat = (cr, sr)
        that = (-sr, cr)
        nn = (s * math.cos(phi), s * math.sin(phi))
        vx = rdot * rhat[0] + r * thdot * that[0]
        vy = rdot * rhat[1] + r * thdot * that[1]
        a_los = -(gm / (r * r)) * (rhat[0] * nn[0] + rhat[1] * nn[1])
        v_los = vx * nn[0] + vy * nn[1]
        amax = max(amax, abs(a_los))
        vmax = max(vmax, abs(v_los))
        if prev is not None:
            dt = (th - prev[0]) / (0.5 * (thdot + prev[2]))
            dmax = max(dmax, abs(a_los - prev[1]) / dt)
        prev = (th, a_los, thdot)
    return amax, vmax, dmax


def scaled(e, s, phi):
    """The same orbit with r_p rescaled so max|a_los| is the ceiling, in
    units of the circular edge-on orbit at that ceiling.  a scales as
    lambda^-2, v as lambda^-1/2 and adot as lambda^-7/2."""
    amax, vmax, dmax = family(e, s, phi)
    lam = math.sqrt(amax)             # max|a_los| -> 1 in GM = r_p = 1 units
    return vmax / math.sqrt(lam), dmax / lam ** 3.5


PHI = [0.5 * math.pi * k / 12.0 for k in range(13)]
SIN = [1.0, 0.7, 0.5, 0.35, 0.25, 0.18, 0.12, 0.08, 0.05, 0.03]
#: the whole family, once: (e, sin i, phi, max|v_los|, max|adot_los|), each in
#: units of the circular edge-on orbit whose line-of-sight acceleration sits
#: at the ceiling.  Every statement below is read out of this list.
FAM = [(e, s, phi) + scaled(e, s, phi)
       for e in ECC_GRID for s in SIN for phi in PHI]
EDGE = [z for z in FAM if z[1] == 1.0]
VSUP = max(z[3] for z in EDGE)
VSUP_CIRC = max(z[3] for z in EDGE if z[0] == 0.0)
#: the fastest reversal the family reaches WITHOUT tilting the orbit at all,
#: which is the factor the paper quotes: a deep periastron directed across the
#: sky keeps the line-of-sight component inside the ceiling throughout while
#: turning it over far faster than a circular orbit at the ceiling can.
RATE_EDGE = max(z[4] for z in EDGE)
_rwo = max(EDGE, key=lambda z: z[4])
TILT = [0.5, 0.2, 0.1, 0.05]
TSEQ = [(s,) + scaled(0.0, s, 0.0) for s in TILT]
_circ_edge = scaled(0.0, 1.0, 0.0)
if DRIVE == 4:                        # O4: an orientation sweep that is flat
    TSEQ = [(s, _circ_edge[0], _circ_edge[1]) for s in TILT]
ck('O4 tilting the orbit leaves the line-of-sight VELOCITY bounded but '
   'makes the reversal arbitrarily fast at the same ceiling: the measured '
   'rate grows as sin(i)^(-3/4) with no bound, while the velocity never '
   'exceeds the edge-on circular amplitude',
   abs(_circ_edge[0] - 1.0) < 2e-3 and abs(_circ_edge[1] - 1.0) < 5e-3
   and all(abs(z[2] / s ** -0.75 - 1.0) < 0.02 for s, z in
           zip(TILT, [(0, a, b) for _, a, b in TSEQ]))
   and all(z[1] <= 1.0 + 1e-6 for z in TSEQ)
   and TSEQ[-1][2] > 5.0,
   'circular edge-on reproduces (%.4f, %.4f); tilted rates %s against '
   'sin(i)^-3/4 %s; velocities %s'
   % (_circ_edge[0], _circ_edge[1],
      ['%.2f' % z[2] for z in TSEQ], ['%.2f' % (s ** -0.75) for s in TILT],
      ['%.3f' % z[1] for z in TSEQ]))

# the worst orientation for the VELOCITY excursion, which is the one place
# the ceiling is used correctly and has to keep its claim
_vwo = max(EDGE, key=lambda z: z[3])
# the sup converges as e -> 1, so the bound the paper quotes is a declared
# round factor above the measured one rather than the grid's own maximum.
VFAC = 1.7
_byecc = [max(z[3] for z in EDGE if z[0] == e) for e in ECC_GRID]
if DRIVE == 7:                        # O5b: a bound under the measured sup
    VFAC = 1.5
ck('O5 the velocity excursion is bounded over the whole family and '
   'converges as the orbit becomes radial, is larger than the circular '
   'amplitude, and the factor the paper quotes is above the measured '
   'maximum -- so the widened window may be compared with it',
   VSUP > VSUP_CIRC + 0.1 and VSUP < VFAC
   and abs(VSUP_CIRC - 1.0) < 2e-3
   and all(_byecc[i] <= _byecc[i + 1] + 1e-6
           for i in range(len(_byecc) - 1))
   and _byecc[-1] - _byecc[-2] < 0.01
   and all(z[3] <= VSUP + 1e-9 for z in FAM),
   'measured sup %.4f of the circular amplitude at e = %.3f, phi = %.0f '
   'deg, against the quoted %.2f; by eccentricity %s'
   % (VSUP, _vwo[0], math.degrees(_vwo[2]), VFAC,
      ['%.3f' % x for x in _byecc]))

# ★★★★ AND THE RATE IS NOT BOUNDED EVEN WITHOUT TILTING.  The eccentric
# speed-up sqrt(1+e) of O3 is the factor for an orbit whose PERIASTRON
# acceleration is the ceiling.  The search does not constrain that: it
# constrains the line-of-sight component, and an orbit whose periastron is
# much deeper than the ceiling but directed across the plane of the sky has a
# small line-of-sight component exactly where it is moving fastest.  Measured
# edge-on, with no tilt at all, the family reaches RATE_EDGE times the
# circular rate -- and O4's tilt sequence then removes any bound whatever.
ck('O6a the fastest reversal the family reaches with no tilt at all is '
   'already several times the circular one, and it is reached by an '
   "eccentric orbit whose periastron points across the sky, so sqrt(1+e) "
   'is not the whole of the eccentric freedom either',
   RATE_EDGE > 3.0 and _rwo[0] > 0.9
   and abs(math.degrees(_rwo[2]) - 90.0) < 1e-6
   and RATE_EDGE > math.sqrt(1.0 + _rwo[0]) if DRIVE != 10 else False,
   'rate %.2f times circular at e = %.3f, phi = %.0f deg, against the '
   'periastron-at-the-ceiling factor %.2f'
   % (RATE_EDGE, _rwo[0], math.degrees(_rwo[2]),
      math.sqrt(1.0 + _rwo[0])))

# =================================== 5. THE VERDICTS, RE-DERIVED PAIR BY PAIR
ROWS = []
for p in sorted(_tau + _egrid, key=lambda z: float(z['dt'])):
    msun, rec = mass_of(p['star'])
    tau = p['tau']
    row = dict(star=canon(p['star']), display=tname(p['star']),
               eblo=p['eblo'], ebhi=p['ebhi'],
               dt_d=float(p['dt']) / 86400.0, dv=float(p['dv']),
               nsig=float(p['nsig']), power=bool(p['power']),
               verdict_pub=p['verdict'], mass=msun,
               mass_src=(rec or {}).get('source'),
               tau_h=(tau / 3600.0) if tau else None)
    if tau is None:                   # the grid clause: no orbit enters it
        row.update(margin_pub=None, margin_mass=None, ecc_crit=None,
                   margin_ecc=None, verdict=('needs a drift outside the '
                                             'searched range'),
                   mean_req=float(p['meanreq']), dmax=float(p['dmax']),
                   grid_factor=abs(float(p['meanreq'])) / float(p['dmax']))
        ROWS.append(row)
        continue
    mg_pub = p['ratio_mine']
    mg_mass = tau_circ(msun) / tau if msun else None
    row.update(margin_pub=mg_pub, margin_mass=mg_mass,
               ecc_crit=((mg_mass ** 2 - 1.0) if mg_mass and mg_mass > 1.0
                         else 0.0),
               margin_ecc=(mg_mass / math.sqrt(2.0)) if mg_mass else None)
    # ★★★★ THE TWO THINGS ONE CARRIER HAS TO DO AT ONCE, in units of the
    # circular edge-on orbit at the ceiling about THIS host: turn the
    # line-of-sight acceleration over at the rate the pair demands, and carry
    # enough line-of-sight velocity to produce the offset the pair shows.  A
    # sinusoid of amplitude A spans 2A, so the second demand is |dv|/2.  An
    # orbit that meets one and not the other is no counterexample, and the
    # first version of this generator offered exactly that for one pair.
    if msun:
        ra = adot_req(tau) / adot_circ(msun)
        rv = 0.5 * abs(float(p['dv'])) * 1e3 / v_circ(msun)
        feas = [z for z in FAM if z[4] >= ra and z[3] >= rv]
        # the least extreme witness: lowest eccentricity, then most edge-on
        wit = min(feas, key=lambda z: (z[0], 1.0 - z[1])) if feas else None
        row.update(req_rate=ra, req_vamp=rv, n_feasible=len(feas))
        if wit:
            vn, dn = wit[3], wit[4]
            # ★ THE PHYSICAL PERIASTRON.  In the normalised run (r_p = GM = 1)
            # the largest line-of-sight acceleration is `amax_norm`, and
            # a_los scales as GM/r^2, so putting it AT the ceiling gives
            # r_p = sqrt(amax_norm) x sqrt(GM/a_ceil): a tilted or
            # sky-directed orbit has to be TIGHTER than the circular one at
            # the ceiling, not wider.  (Written the other way up first, which
            # put the witness orbit outside the circular radius -- impossible,
            # and the reason the radius is now checked against it below.)
            amax_norm = family(wit[0], wit[1], wit[2])[0]
            rp = math.sqrt(GMSUN * msun / AG) * math.sqrt(amax_norm)
            sma = rp / (1.0 - wit[0]) if wit[0] < 1.0 else float('inf')
            per = (2.0 * math.pi * math.sqrt(sma ** 3 / (GMSUN * msun))
                   if sma < float('inf') else None)
            row.update(wit_ecc=wit[0], wit_sini=wit[1],
                       wit_inc_deg=math.degrees(math.asin(wit[1])),
                       wit_phi_deg=math.degrees(wit[2]),
                       wit_rate=dn, wit_vamp=vn,
                       wit_rp_au=rp / AU, wit_sma_au=sma / AU,
                       wit_rp_frac=math.sqrt(amax_norm),
                       wit_span_kms=2.0 * vn * v_circ(msun) / 1e3,
                       wit_p_d=(per / 86400.0) if per else None)
    row['verdict'] = 'not separable'
    ROWS.append(row)

NO = [r for r in ROWS if r['verdict'] != 'not separable']
REOPEN = [r for r in ROWS if r['verdict'] == 'not separable'
          and r['verdict_pub'] == 'excluded']
NOPEN = len(_open) + len(REOPEN)
_bp = [r for r in ROWS if 'bet Pic' in r['star']]
_hd = [r for r in REOPEN if 'bet Pic' not in r['star']]
ck('O6 both reversal verdicts are re-derived at the host mass and both are '
   'withdrawn, the one pair separated by the searched drift range is not '
   'touched by the orbit at all, and the partition still closes on the '
   'number of pairs the test formed',
   len(REOPEN) == len(_etau) and len(NO) == len(_egrid) == 1
   and len(NO) + NOPEN + len(_ctl) == len(PUB['pairs'])
   and all(r['mass'] is not None for r in REOPEN)
   and all(r.get('wit_ecc') is not None for r in REOPEN),
   '%d withdrawn, %d separated, %d open, %d control = %d pairs'
   % (len(REOPEN), len(NO), NOPEN, len(_ctl), len(PUB['pairs'])))

# ★★ EACH WITHDRAWAL IS WITHDRAWN AGAINST A NAMED ORBIT THAT DOES BOTH JOBS.
_wit_ok = all(r.get('wit_ecc') is not None
              and r['wit_rate'] >= r['req_rate']
              and r['wit_vamp'] >= r['req_vamp'] for r in REOPEN)
if DRIVE == 5:
    _wit_ok = False
ck('O7 each withdrawn verdict is withdrawn against a named orbit and not '
   'against a general argument: for every one of them the family holds an '
   'orbit that both turns the line-of-sight acceleration over at the rate '
   'the pair demands AND carries the velocity its offset needs, at the same '
   'ceiling',
   _wit_ok and bool(REOPEN)
   and all(r['wit_rp_frac'] <= 1.0 + 1e-9
           and r['wit_span_kms'] >= abs(r['dv']) for r in REOPEN),
   '; '.join('%s needs rate %.2f and amplitude %.2f, met by e = %.3f, '
             'sin i = %.2f, phi = %.0f deg (%.2f, %.2f), %d of %d orbits'
             % (r['star'], r['req_rate'], r['req_vamp'], r['wit_ecc'],
                r['wit_sini'], r['wit_phi_deg'], r['wit_rate'],
                r['wit_vamp'], r['n_feasible'], len(FAM)) for r in REOPEN))

# ============== 6. THE ONE PLACE THE CEILING IS USED CORRECTLY, RECHECKED
# S5.6 justifies the widened recurrence window by comparing its half-width
# with the velocity excursion an orbit at the ceiling can produce.  That use
# is sound -- the excursion IS bounded over orientation (O4) -- but the
# number is evaluated at two solar masses and zero eccentricity, and the
# sample holds A stars heavier than that.  The covering sets of
# `recurnull_v413.py` are rebuilt here and the count is gated against the
# published one at the published bound before being recomputed at the
# corrected one.
BYEB, BYSYS = {}, {}
for r in CAT:
    BYEB.setdefault(r['eb'], []).append(r)
    BYSYS.setdefault(r['system_id'], []).append(r)
CRK = {(c['eb'], round(float(c['freq_GHz']), 4)): c for c in CROSS.values()}
LDQ = {(r['eb'], round(float(r['freq']), 4)) for r in LED if r.get('dq')}
UNATTR = [r for r in LED if not r['attributed']]


def blocks(c):
    return [b for b in c.get('blocks', []) if not b.get('bad_weight_product')]


HALF, QSTAR = {}, {}
for r in UNATTR:
    f, eb = float(r['freq']), r['eb']
    k = (eb, round(f, 4))
    if k in LDQ:
        continue
    c = CRK.get(k)
    if c is None or not blocks(c):
        continue
    dw = [q for q in BYEB.get(eb, []) if float(q['flo_GHz']) <= f
          <= float(q['fhi_GHz'])]
    sid = dw[0]['system_id'] if len(dw) == 1 else None
    if sid is None:
        for b in blocks(c):
            q = [x for x in BYEB.get(b['eb'], [])
                 if float(x['flo_GHz']) <= b['f_here_GHz']
                 <= float(x['fhi_GHz'])]
            if q:
                sid = q[0]['system_id']
                break
    assert sid, 'no system identifier for %s %s' % (r['star'], eb)
    cov = [q for q in BYSYS[sid] if q['eb'] != eb
           and float(q['flo_GHz']) <= f <= float(q['fhi_GHz'])]
    QSTAR[k] = r['star']
    for q in cov:
        lo, hi = float(q['flo_GHz']), float(q['fhi_GHz'])
        HALF.setdefault(k, []).append(0.5 * CKMS * (hi - lo) / f)


def span_count(vmax_kms, per_host=False):
    nspan, nshort, nocov = 0, [], []
    for k in QSTAR:
        lim = vmax_kms
        if per_host:
            msun, _ = mass_of(QSTAR[k])
            lim = vmax_kms * ((msun / MASS['ceiling_msun']) ** 0.25
                              if msun else 1.0)
        if not HALF.get(k):
            nocov.append(QSTAR[k])
        elif max(HALF[k]) >= lim:
            nspan += 1
        else:
            nshort.append((QSTAR[k], max(HALF[k]), lim))
    return nspan, nshort, nocov


NSPAN_PUB, NSHORT_PUB, NOCOV = span_count(v_circ(MSUN_PUB) / 1e3)
ck('O8 the covering sets are rebuilt from the catalogue and reproduce the '
   'published widened-window counts at the published bound, so the recount '
   'below changes the bound and nothing else',
   len(QSTAR) - len(NOCOV) == int(macro('WdNOrbTot'))
   and len(NOCOV) == int(macro('WdNNoCov'))
   and NSPAN_PUB == int(macro('WdNOrbSpan'))
   and len(NSHORT_PUB) == int(macro('WdNOrbShort')),
   '%d crossings with coverage (%s), %d without (%s): %d span (%s), %d short '
   '(%s)' % (len(QSTAR) - len(NOCOV), macro('WdNOrbTot'), len(NOCOV),
             macro('WdNNoCov'), NSPAN_PUB, macro('WdNOrbSpan'),
             len(NSHORT_PUB), macro('WdNOrbShort')))

VCEIL = VFAC * v_circ(MASS['ceiling_msun']) / 1e3
NSPAN, NSHORT, _ = span_count(VCEIL)
_mpub = max(float(v['mass_msun']) for v in MASS['stars'].values())
_nomass = sorted(k for k in {canon(QSTAR[q]) for q in QSTAR}
                 if k not in MASS['stars'])
_late = [k for k in _nomass
         if (SPT.get(MASS['simbad'].get(k, k), {}).get('sp_type') or '~')[:1]
         in 'FGKM']
if DRIVE == 6:                        # O9: a ceiling under the sample
    MASS['ceiling_msun'] = 1.0
ck('O9 the mass ceiling the excursion is evaluated at is above every host '
   'mass published for this sample, and every host with no published mass '
   'is of a later type than the ones that have one, with the single '
   'serendipitous field star named as the exception',
   MASS['ceiling_msun'] >= 1.05 * _mpub
   and len(_late) == len(_nomass) - 1
   and len(_nomass) - len(_late) == 1,
   'ceiling %.2f Msun against the largest published %.2f; %d hosts without '
   'a published mass, %d of them F or later, exception %s'
   % (MASS['ceiling_msun'], _mpub, len(_nomass), len(_late),
      [k for k in _nomass if k not in _late]))

# ======================================================= macros
m('EcMassBp', '%.2f' % mass_of('bet Pic')[0])
m('EcMassHd', '%.2f' % mass_of('HD14055')[0])
m('EcTauBpH', '%.1f' % (tau_circ(mass_of('bet Pic')[0]) / 3600.0))
m('EcMarginBp', '%.2f' % _bp[0]['margin_mass'])
m('EcEccBp', '%.2f' % _bp[0]['ecc_crit'])
m('EcReqRateBp', '%.1f' % _bp[0]['req_rate'])
m('EcReqVampBp', '%.2f' % _bp[0]['req_vamp'])
m('EcWitEccBp', '%.1f' % _bp[0]['wit_ecc'])
m('EcWitSinBp', '%.2f' % _bp[0]['wit_sini'])
m('EcWitAuBp', '%.3f' % _bp[0]['wit_rp_au'])
m('EcWitIncBp', '%.0f' % _bp[0]['wit_inc_deg'])
m('EcWitDayBp', '%.1f' % _bp[0]['wit_p_d'])
m('EcWitSpanBp', '%.0f' % _bp[0]['wit_span_kms'])
m('EcRateSupFac', '%.1f' % RATE_EDGE)
m('EcRateSupEcc', '%.3f' % _rwo[0])
m('EcMarginHd', '%.2f' % _hd[0]['margin_mass'])
m('EcEccHd', '%.2f' % _hd[0]['ecc_crit'])
m('EcReqRateHd', '%.1f' % _hd[0]['req_rate'])
m('EcReqVampHd', '%.2f' % _hd[0]['req_vamp'])
m('EcWitEccHd', '%.3f' % _hd[0]['wit_ecc'])
m('EcStarHd', _hd[0]['display'])
m('EcNWithdrawn', '%d' % len(REOPEN))
m('EcNNo', '%d' % len(NO))
m('EcNOpen', '%d' % NOPEN)
m('EcGridStar', NO[0]['display'])
m('EcGridFactor', '%.0f' % NO[0]['grid_factor'])
m('EcGridDvKms', '%.0f' % abs(NO[0]['dv']))
m('EcGridDtH', '%.1f' % (NO[0]['dt_d'] * 24.0))
m('EcEccFac', '%.2f' % math.sqrt(2.0))
m('EcTiltExp', '3/4')
m('EcVsupFac', '%.1f' % VFAC)
m('EcVsupMeas', '%.2f' % VSUP)
m('EcCeilMass', '%.1f' % MASS['ceiling_msun'])
m('EcVexcKms', '%.0f' % VCEIL)
m('EcVcircKms', '%.0f' % (v_circ(MASS['ceiling_msun']) / 1e3))
m('EcNSpan', '%d' % NSPAN)
m('EcNSpanTot', '%d' % (len(QSTAR) - len(NOCOV)))
m('EcNShort', '%d' % len(NSHORT))
m('EcShortStar', tname(sorted({s[0] for s in NSHORT})[0]) if NSHORT else '--')
_ss = sorted({tname(s[0]) for s in NSHORT})
m('EcNShortStar', '%d' % len(_ss))
m('EcShortStarList', (', '.join(_ss[:-1]) + ' and ' + _ss[-1]) if len(_ss) > 1
  else (_ss[0] if _ss else '--'))
m('EcShortKms', '%.0f' % min([s[1] for s in NSHORT] or [0.0]))
m('EcHalfKms', macro('WdHalfKms'))
#: ★ r28 (integrate, note 7): App. C's physical justification of the mask
#: half-width -- the Keplerian speed of gas beyond KEP_R_AU -- was two typed
#: numbers ("13 km/s beyond 10 au").  It is now computed at this sample's mass
#: ceiling (the ceiling the excursion bound above uses, above every published
#: host mass), rounded UP because the sentence states an upper bound, and K1
#: asserts it bounds every published host and lies inside the adopted
#: half-width it justifies.  (Numbers_v410 writes \MaskHalfKms in the
#: \providecommand/\renewcommand form, which macro() does not read.)
KEP_R_AU = 10
_mh = None
for _p in sorted(glob.glob(os.path.join(V, 'numbers/survey_numbers*.tex'))):
    if '_drive' in _p:
        continue
    for _l in open(_p):
        _mm = re.search(r'\\renewcommand\{\\MaskHalfKms\}\{([0-9.]+)\}', _l)
        if _mm:
            _mh = float(_mm.group(1))
assert _mh, 'MaskHalfKms not found in the macro layer'
_vkep = math.sqrt(GMSUN * MASS['ceiling_msun'] / (KEP_R_AU * AU)) / 1e3
_vkep_pub = math.sqrt(GMSUN * _mpub / (KEP_R_AU * AU)) / 1e3
if DRIVE == 8:                       # K1: a half-width below the Keplerian speed
    _mh = 0.5 * _vkep
ck('K1 Keplerian speed beyond %d au: ceiling %.2f >= hosts %.2f, < mask %g km/s'
   % (KEP_R_AU, _vkep, _vkep_pub, _mh),
   _vkep_pub <= _vkep < _mh)
m('EcKepRAu', '%d' % KEP_R_AU)
m('EcKepVKms', '%d' % math.ceil(_vkep))

json.dump(dict(a_ceiling=AG, tau_pub_s=TAU_PUB, rows=ROWS,
               family=FAM, tilt_sequence=TSEQ, sweep=SWEEP,
               rate_sup_edge=RATE_EDGE,
               v_sup_factor=VSUP, v_sup_quoted=VFAC, v_excursion_kms=VCEIL,
               n_span=NSPAN, n_short=[list(s) for s in NSHORT],
               n_open=NOPEN, masses=MASS['stars']),
          open(OUTJ, 'w'), indent=1, default=str)

with open(OUT, 'w') as fh:
    fh.write('%% GENERATED by orbit_r18.py (round %d) -- do not hand-edit.\n'
             % ROUND)
    for k, v in M:
        fh.write('\\newcommand{\\%s}{%s}\n' % (k, v))
print('\n%d macros -> %s' % (len(M), os.path.basename(OUT)))
# ★ A NOTE AND NOT AN ASSERTION, deliberately.  After `pairs_v415.py` is
# patched its own counts must equal these; before the patch they cannot, and an
# assertion that fails until an edit lands elsewhere is a gate that cries wolf.
print('NOTE  this round: %d separated, %d open.  pairs_v415.py currently '
      'publishes TjNExcl = %s, TjNOpen = %s -- they must AGREE once the '
      'verdict rule is patched (QUEUE_recur entry 13).'
      % (len(NO), NOPEN, macro('TjNExcl'), macro('TjNOpen')))
for r in ROWS:
    print('  %-12s %-10s/%-10s dt %8.3f d  dv %+8.1f  margin %s -> %s  %s'
          % (r['star'][:12], r['eblo'].split('_')[-1], r['ebhi'].split('_')[-1],
             r['dt_d'], r['dv'],
             ('%.2f' % r['margin_pub']) if r['margin_pub'] else '  --  ',
             ('%.2f' % r['margin_mass']) if r['margin_mass'] else '  --  ',
             r['verdict']))
if FAIL:
    print('FAILED: %s' % ', '.join(FAIL))
    sys.exit(1)
