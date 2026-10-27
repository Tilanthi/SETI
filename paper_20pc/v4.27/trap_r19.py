#!/usr/bin/env python3
r"""round 902 -> survey_numbers_round902.tex, trapphase_r19.json.

HOW MUCH OF TRAPPIST-1 b's ORBITAL PHASE LIES ABOVE THE DRIFT CEILING, WITH
THE UNCERTAINTIES ON ITS HOST'S MASS AND ITS ORBIT PROPAGATED.

Referee 2's thirteenth point.  The fraction of phase above a ceiling $c$, for
an edge-on orbit of maximum line-of-sight acceleration $a_{\max}$, is
$(2/\pi)\arccos(c/a_{\max})$, and that function is vertical at
$c = a_{\max}$.  The widened drift ceiling used on this star's own windows and
this planet's nominal acceleration agree to about one part in ten thousand,
while the host's mass and the planet's orbit are known to a few per cent, so a
fraction of one per cent is a reading of the fourth decimal place of the
inputs.

TWO ROUTES TO $a_{\max}$ FROM ONE ARCHIVE ROW, AND THEY STRADDLE THE CEILING.
$a_{\max} = GM_\star/a^2$ and $a_{\max} = (GM_\star)^{1/3}(2\pi/P)^{4/3}$ are
the same quantity under Kepler's third law, and the archive's own mass, orbit
and period do not satisfy that law exactly.  Taken through the period -- which
is the route the figure uses -- the planet is a hair ABOVE the widened
ceiling; taken through the semi-major axis, which is the route the referee's
instruction names, it is a hair BELOW it, and the fraction is then exactly
zero.  The published figure is therefore not robust in sign, let alone in
value, and that is measured here rather than argued.

What survives propagation is the statement about the DEFAULT ceiling, which is
ten per cent below the planet's acceleration rather than a part in ten
thousand: that fraction moves by a few points over the same range and the
single figure the paper prints for it stands.

Inputs: `trappist_r19.json` (the archive's own default-parameter row with its
uncertainties, the same table and parameter set `host_masses_v385.json` took
the mass from), the released catalogue's own per-window drift ceilings, and
the macro layer for every published figure this file checks itself against.

    python3 trap_r19.py [--paper DIR] [--out DIR] [--drive N]

--drive 1..6 breaks one assertion each; --drive 0 means "no perturbation, but
do not write a path production reads".
"""
import json
import math
import os
import statistics as st
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROUND = 902

DRIVE = None
OUTDIR = HERE
PAPER = HERE
for _i, _a in enumerate(sys.argv):
    if _a == '--drive':
        DRIVE = int(sys.argv[_i + 1])
    if _a == '--out':
        OUTDIR = sys.argv[_i + 1]
    if _a == '--paper':
        PAPER = sys.argv[_i + 1]
SUF = '' if DRIVE is None else '_drive%d' % DRIVE
OUT = os.path.join(OUTDIR, 'survey_numbers_round%d%s.tex' % (ROUND, SUF))
OUT_JSON = os.path.join(OUTDIR, 'trapphase_r19%s.json' % SUF)

GM_SUN = 1.32712440018e20            # IAU 2015 nominal solar mass parameter
AU = 1.495978707e11                  # IAU 2012 astronomical unit
# The bound the text states in words.  It is a round bound on a quantity the
# data do not determine, so it belongs in words and not in a macro, and T4 is
# what keeps it true.
PHASE_BOUND = 1.0 / 6.0

MACROS, FAIL = [], []


def m(name, val):
    assert name.isalpha(), 'a LaTeX macro name may contain letters only: %r' % name
    assert not any(x.startswith('\\newcommand{\\%s}' % name) for x in MACROS), name
    MACROS.append('\\newcommand{\\%s}{%s}' % (name, val))


def ck(label, ok, detail=''):
    if not ok:
        FAIL.append(label.split()[0])
    print('  %-70s %s  %s' % (label[:70], 'PASS' if ok else 'FAIL', detail))


sys.path.insert(0, PAPER)
import adopted_e90 as ae                                      # noqa: E402

CAT = ae.catalogue(PAPER)
PL = json.load(open(os.path.join(HERE, 'trappist_r19.json')))
MASS = json.load(open(os.path.join(PAPER, 'host_masses_v385.json')))


def tex(name):
    return ae._texval(name, PAPER)


print('trap_r19 round %d%s' % (ROUND, '' if DRIVE is None
                               else ' (drive %d)' % DRIVE))

# =====================================================================
# 0  THE INPUTS ARE THE ONES THE PAPER ALREADY USES
# =====================================================================
M_STAR, dM = PL['st_mass'], PL['st_masserr1']
P_D, dP = PL['pl_orbper'], PL['pl_orbpererr1']
A_AU, dA = PL['pl_orbsmax'], PL['pl_orbsmaxerr1']
_same = abs(MASS[PL['hostname']] - M_STAR) < 1e-12
if DRIVE == 1:
    _same = False
ck('T1 the stellar mass whose uncertainty is propagated here is the mass the '
   'drift figure already uses, so this is the same quantity with an error bar '
   'and not a second determination of it',
   _same, '%.4f against %.4f in the figure\'s own input'
   % (M_STAR, MASS[PL['hostname']]))

# =====================================================================
# 1  THE CEILINGS, FROM THE WINDOWS THEMSELVES
# =====================================================================
ACC = [float(r['a_max_m_s2']) for r in CAT if r['search_class'] == 'A']
C_DEF, C_WIDE = st.median(ACC), max(ACC)
_pub = (float(tex('AccelCeilMed')), float(tex('AccelCeilMax')))
_ok = abs(C_DEF - _pub[0]) < 0.005 and abs(C_WIDE - _pub[1]) < 0.005
if DRIVE == 2:
    _ok = False
ck('T2 the default and widened ceilings are counted from the windows and are '
   'the published pair',
   _ok, '%.4f and %.4f against %s and %s published'
   % (C_DEF, C_WIDE, _pub[0], _pub[1]))


def a_max_period(m_star, period_d):
    return (GM_SUN * m_star) ** (1 / 3.) * (2 * math.pi
                                            / (period_d * 86400.0)) ** (4 / 3.)


def a_max_smax(m_star, a_au):
    return GM_SUN * m_star / (a_au * AU) ** 2


def phase(c, a_max):
    """The fraction of an edge-on orbit's phase above a ceiling c."""
    return 0.0 if c >= a_max else (2 / math.pi) * math.acos(c / a_max)


A_P = a_max_period(M_STAR, P_D)
A_A = a_max_smax(M_STAR, A_AU)
S_P = math.hypot(dM / M_STAR / 3.0, 4 / 3. * dP / P_D)
S_A = math.hypot(dM / M_STAR, 2 * dA / A_AU)
print('  a_max through the period      %.4f +- %.4f m s^-2 (%.2f per cent)'
      % (A_P, A_P * S_P, 100 * S_P))
print('  a_max through the semi-major axis %.4f +- %.4f m s^-2 (%.2f per cent)'
      % (A_A, A_A * S_A, 100 * S_A))

# =====================================================================
# 2  THE QUOTED ONE PER CENT IS A READING OF THE FOURTH DECIMAL PLACE
# =====================================================================
RATIO = A_P / C_WIDE
_frac_pub = float(tex('TrapPhaseLo')) / 100.0
_need = abs(RATIO - 1.0)
if DRIVE == 3:
    _need = 0.5
ck('T3 the published fraction above the widened ceiling rests on the planet\'s '
   'acceleration and that ceiling agreeing to a part in ten thousand, which '
   'is three orders of magnitude finer than the inputs are known to',
   _need < 1e-3 and _need < 0.05 * S_A,
   'a_max/c = %.5f, i.e. %.1e, against an input uncertainty of %.1e'
   % (RATIO, _need, S_A))

# the two routes straddle the ceiling: one gives a per cent, the other zero
F_P = phase(C_WIDE, A_P)
F_A = phase(C_WIDE, A_A)
_straddle = (A_P > C_WIDE) != (A_A > C_WIDE)
if DRIVE == 4:
    _straddle = False
ck('T4 the two routes to the same acceleration from the same archive row fall '
   'on opposite sides of the widened ceiling, so the published fraction is '
   'not robust in sign',
   _straddle and abs(F_P - _frac_pub) < 0.005,
   'through the period %.2f per cent, through the semi-major axis %.2f per '
   'cent, published %.0f per cent'
   % (100 * F_P, 100 * F_A, 100 * _frac_pub))

# =====================================================================
# 3  THE PROPAGATED RANGE, AND THE BOUND THE TEXT STATES
# =====================================================================
RANGE = {}
for nm, am, s in (('period', A_P, S_P), ('smax', A_A, S_A)):
    for cn, c in (('default', C_DEF), ('widened', C_WIDE)):
        RANGE['%s/%s' % (nm, cn)] = [
            phase(c, am * (1 - k * s)) for k in (1, 0, -1)]
        print('  %-6s %-8s %-7s nominal %5.2f per cent, one sigma %5.2f-%5.2f'
              % (nm, cn, '', 100 * RANGE['%s/%s' % (nm, cn)][1],
                 100 * RANGE['%s/%s' % (nm, cn)][0],
                 100 * RANGE['%s/%s' % (nm, cn)][2]))
WIDE_HI = max(RANGE['period/widened'][2], RANGE['smax/widened'][2])
WIDE_LO = min(RANGE['period/widened'][0], RANGE['smax/widened'][0])
_bound = PHASE_BOUND if DRIVE != 5 else 0.01
ck('T5 the fraction above the widened ceiling, over one standard deviation of '
   'the mass and the orbit by either route, runs from nothing up to the bound '
   'the text states in words and no further',
   WIDE_LO <= 1e-12 and WIDE_HI < _bound,
   'from %.2f to %.2f per cent against a stated bound of %.1f per cent'
   % (100 * WIDE_LO, 100 * WIDE_HI, 100 * _bound))

DEF_HI = max(RANGE['period/default'][2], RANGE['smax/default'][2])
DEF_LO = min(RANGE['period/default'][0], RANGE['smax/default'][0])
_defpub = float(tex('TrapPhaseHi'))
_spread = 100 * (DEF_HI - DEF_LO)
if DRIVE == 6:
    _spread = 50.0
ck('T6 the fraction above the DEFAULT ceiling survives the same propagation '
   'within a few points and brackets the published figure, so one figure may '
   'be printed for it where the widened ceiling admits none',
   DEF_LO * 100 <= _defpub <= DEF_HI * 100 and _spread < 10.0,
   'from %.1f to %.1f per cent around a published %.0f, a spread of %.1f '
   'points' % (100 * DEF_LO, 100 * DEF_HI, _defpub, _spread))

# =====================================================================
# 4  THE MACROS
# =====================================================================
# ★ One macro.  The range on the widened-ceiling fraction is stated in the
# text as "between nothing and a sixth", in words, because it is a round bound
# on a quantity the data do not determine and T5 is the gate that keeps it
# true; a macro would invite a reader to treat it as a measurement.  What is
# worth a number is the accuracy to which the planet's acceleration is known
# at all, which is what the figure's caption now says.
m('TrpAmaxPct', '%.1f' % (100 * S_A))

json.dump(dict(
    inputs=dict(m_star=M_STAR, m_star_err=dM, period_d=P_D, period_err=dP,
                a_au=A_AU, a_err=dA, reference=PL['reference']),
    ceilings=dict(default=C_DEF, widened=C_WIDE),
    a_max=dict(period=A_P, period_sigma=A_P * S_P, smax=A_A,
               smax_sigma=A_A * S_A, rel_sigma_period=S_P,
               rel_sigma_smax=S_A),
    phase_fraction={k: v for k, v in RANGE.items()},
    widened_range=[WIDE_LO, WIDE_HI], default_range=[DEF_LO, DEF_HI],
    stated_bound=PHASE_BOUND, fails=FAIL),
    open(OUT_JSON, 'w'), indent=1, sort_keys=True)
with open(OUT, 'w') as fh:
    fh.write('%% GENERATED by %s -- do not hand-edit.\n'
             % os.path.basename(__file__))
    fh.write('\n'.join(sorted(MACROS)) + '\n')
print('\n  wrote %s and %s' % (os.path.basename(OUT),
                               os.path.basename(OUT_JSON)))
if FAIL:
    print('  FAILURES: %s' % ', '.join(sorted(set(FAIL))))
    raise SystemExit(1)
print('  all clauses pass')
