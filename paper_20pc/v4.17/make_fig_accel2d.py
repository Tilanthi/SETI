#!/usr/bin/env python3
"""Referee 1, point 9: the searched and unsearched drift domain, expressed
as line-of-sight acceleration against observing frequency.

The old version of this figure plotted acceleration against orbital
semi-major axis and drew the survey ceiling as a single horizontal line
taken from the median window.  That hides the question the referee asks:
a drift-rate grid in Hz s^-1 does NOT correspond to a fixed acceleration,
because nu-dot/nu = a/c, so the same grid is a different physical limit at
90 GHz and at 870 GHz.

Here the boundary is drawn from the catalogue itself, window by window,
against observing frequency, with reference accelerations overlaid:
Earth's rotation and orbit (which a terrestrial transmitter carries whether
or not anyone intends it), the most demanding short-period terrestrial
planet among the targets, and a wide-orbit giant for scale.

Upper panel: acceleration.  Lower panel: the same boundary in the units the
search actually works in, Hz s^-1, where it is NOT flat.  Showing both is
the point -- a reader who thinks in drift rate and a reader who thinks in
orbital dynamics see the same experiment.
"""
import csv, json, math, os, sys
import numpy as np
import matplotlib
matplotlib.use('Agg')
matplotlib.rcParams['pdf.fonttype'] = 42
matplotlib.rcParams.update({
    'font.family': 'serif',
    'font.serif': ['STIXGeneral', 'DejaVu Serif'],
    'mathtext.fontset': 'stix',
    'font.size': 8, 'axes.labelsize': 7.6,
    'xtick.labelsize': 6.8, 'ytick.labelsize': 6.8, 'legend.fontsize': 5.8,
})
import matplotlib.pyplot as plt

HERE = os.path.dirname(os.path.abspath(__file__))
C_MS = 299792458.0
GM_SUN = 1.32712440018e20
OUT = []
def M(n, v): OUT.append(r'\newcommand{\%s}{%s}' % (n, v))

# --------------------------------------------------------------------------------
# R2-M9.  THE LITERATURE STATES DRIFT REACH AS A FRACTIONAL RATE, IN nHz, AND THIS
# FIGURE STATED IT ONLY AS AN ACCELERATION.  The two are the same quantity --
# nu-dot/nu = a/c, which is Eq. (accel) and the reason this panel is flat -- so the
# nHz reading is a second axis on the one already drawn and not a second
# measurement.  It is worth drawing because the comparison a reader wants is with
# published guidance and with published searches, and both are quoted in nHz.
#
# Three literature values, each with the sentence it was read from.  Nothing here
# is derived from our data; nothing in our data is derived from it.
NHZ_LIT = {
    'sheikh_guideline': dict(
        nHz=200.0,
        src="Sheikh et al. 2019, ApJ 884, 14, abstract: 'We determine that a "
            "normalized drift rate of 200 nHz (eg. 200 Hz/s at 1 GHz) is a "
            "generous, physically motivated guideline for the maximum drift rate "
            "that should be applied to future narrowband SETI projects.'"),
    # Jupiter's equatorial rotation, computed rather than quoted, because the
    # ordinate of this figure is an acceleration and the conversion must be the
    # same one every other line on the panel uses.  Sheikh et al. (2019),
    # sec. 4.1, publish 7.2 nHz for the same quantity; they normalise by the
    # volumetric mean radius (69,911 km) and this uses the equatorial radius,
    # where a transmitter on the equator actually sits, so the two differ by
    # 2 per cent.  Both say the same thing: a transmitter on a giant planet
    # spends most of its drift budget on the planet's own spin.
    'jupiter_rotation': dict(
        R_eq_m=7.1492e7, P_rot_s=35729.711,
        src="IAU/NASA planetary fact sheet: Jupiter equatorial radius "
            "71,492 km, sidereal rotation period (System III) 9h 55m 29.711s.  "
            "a = omega^2 R_eq, and nu-dot/nu = a/c.  Compare Sheikh et al. "
            "2019, sec. 4.1: 'Jupiter's rotational motion would impart a "
            "maximum drift rate of 7.2 nHz' (volumetric mean radius)."),
    'earth_total': dict(
        nHz=0.11,
        src="Sheikh et al. 2019, sec. 4.1: 'the Earth's fractional drift rate "
            "from both rotation and orbital motion is 0.11 nHz.'"),
    'margot_reach': dict(
        nHz=6.24,
        src="Margot et al. 2023, AJ 166, 206, sec. 3.2: 'Our selection of a range "
            "of trial drift rates with maximum value f_r,max = +-8.86 Hz s-1 "
            "corresponds to a fractional drift rate of +-6.24 nHz at ft = 1.42 "
            "GHz (maximum accelerations vdot_max of 1.87 ms-2).'"),
}


def texnum(name):
    """The last literal value of \\name across survey_numbers*.tex.

    Only used to CHECK against, never to plot: this file computes the ceiling
    from the catalogue and the macro layer publishes it, and the two must
    agree."""
    import glob as _g, re as _re
    pat = _re.compile(r'\\(?:new|renew|provide)command\{\\%s\}'
                      r'\{((?:[^{}]|\{[^{}]*\})*?)\}' % _re.escape(name))
    out = None
    for fn in sorted(_g.glob(os.path.join(HERE, 'survey_numbers*.tex'))):
        for mm in pat.finditer(open(fn, encoding='utf-8').read()):
            v = mm.group(1).strip()
            if v and not v.startswith('\\'):
                out = v
    if out is None:
        raise KeyError('no literal definition of \\%s' % name)
    return float(out)


def _jup_rot_accel():
    J = NHZ_LIT['jupiter_rotation']
    om = 2.0 * math.pi / J['P_rot_s']
    return om * om * J['R_eq_m']


def nhz(a_ms2):
    """Line-of-sight acceleration (m s^-2) as a fractional drift rate in nHz."""
    return 1e9 * a_ms2 / C_MS


def a_of_nhz(v_nHz):
    """...and back, which is what the secondary axis needs."""
    return v_nHz * C_MS / 1e9

ROWS = [r for r in csv.DictReader(open(os.path.join(HERE, 'per_target_results_v3.99.csv')))
        if r['search_class'] == 'A']
FREQ = np.array([(float(r['flo_GHz']) + float(r['fhi_GHz'])) / 2 for r in ROWS])
ACC = np.array([float(r['a_max_m_s2']) for r in ROWS])
DRIFT = np.array([float(r['drift_max_Hz_s']) for r in ROWS])
# The catalogue's own consistency: a_max = c nu-dot_max / nu.
assert np.allclose(ACC, C_MS * DRIFT / (FREQ * 1e9), rtol=0.02), 'a_max is not c.nudot/nu'

# ------------------------------------------------ the reference accelerations
OMEGA_E = 7.292115e-5            # rad/s, Earth sidereal rotation
R_E = 6.378137e6                 # m, equatorial radius
A_ROT = OMEGA_E ** 2 * R_E       # equatorial centripetal, the diurnal maximum
A_ORB = GM_SUN / (1.495978707e11) ** 2

PL = json.load(open(os.path.join(HERE, 'planet_periods_v361.json')))
MASS = json.load(open(os.path.join(HERE, 'host_masses_v385.json')))


def accel(period_d, m_star):
    """Maximum line-of-sight acceleration of a circular orbit, edge-on."""
    return (GM_SUN * m_star) ** (1 / 3.) * (2 * math.pi / (period_d * 86400.0)) ** (4 / 3.)


PACC = sorted(((accel(r['pl_orbper'], MASS[r['hostname']]), r['pl_name'],
                r['pl_orbper']) for r in PL), reverse=True)
A_WORST, N_WORST, P_WORST = PACC[0]
A_SECOND, N_SECOND, P_SECOND = PACC[1]

CEIL_MED = float(np.median(ACC))
CEIL_MAX = float(ACC.max())
CEIL_MIN = float(ACC.min())
N_ABOVE = sum(1 for a, _, _ in PACC if a > CEIL_MAX)
N_BELOW_MED = sum(1 for a, _, _ in PACC if a <= CEIL_MED)
# The grid takes exactly two ceiling values: the survey default, and a wider
# one used only for TRAPPIST-1's own windows. The widened grid still falls
# fractionally short of planet b at maximum line-of-sight acceleration, so
# the honest statement is a margin, not a category.
CEILS = sorted(set(np.round(ACC, 4)))
N_WIDE = int((ACC > CEIL_MED * 1.001).sum())
# R1-9 / R2 Fig. 3.  There are TWO margins and the caption quoted one of them
# under the other's name: \AccelShortPct was A_WORST/CEIL_MAX - 1 = 0.01 per
# cent, the shortfall against the WIDENED grid used on TRAPPIST-1's own
# windows, while the sentence said "exceeds the MEDIAN boundary by".  Against
# the median (= default) ceiling the excess is 11 per cent.  Both are
# published, each named for the ceiling it is measured against.
SHORT_PCT_MAX = 100.0 * (A_WORST / CEIL_MAX - 1.0)
SHORT_PCT_MED = 100.0 * (A_WORST / CEIL_MED - 1.0)
WIDE_STARS = sorted({r['star_name'] for r in ROWS
                     if float(r['a_max_m_s2']) > CEIL_MED * 1.001})

# The two TRAPPIST-1 planets the text names, from the same orbital model as
# the figure.  These were \OrbAccTrapb and \OrbAccTrapc in the ungenerated
# frozen round-6 file; b is also the survey's most demanding known planet, so
# it must agree with A_WORST by construction and that is asserted, not hoped.
TRAP = {n.split()[-1]: a for a, n, _ in PACC if n.startswith('TRAPPIST-1 ')}
assert abs(TRAP['b'] - A_WORST) < 1e-9, 'TRAPPIST-1 b is not the worst case'

# ------------------------------------------------------------------- figure
# v4.01 (R2 Fig. 3): the lower panel, which redrew the same boundary in
# Hz s^-1, is deleted at the referee's request -- the acceleration panel
# carries the result and the conversion is Eq. (4).
#
# THE ORDINATE RANGE.  It was 1e-3 to 3e2 m s^-2, five and a half decades,
# while every one of the 402 plotted ceilings lies between 3.598 and 3.999 --
# 0.05 of a decade, under one per cent of the axis.  The points were a single
# unresolved smear and the two populations of ceiling could not be told apart.
# ★★ GLENN, 2026-10-06: "Figure 3 should be changed so that the y-axis goes
# from 2 to 5".  (He wrote m s^-1; the ordinate is a line-of-sight
# ACCELERATION, so m s^-2.)  The range brackets the measured ceilings, which
# span 3.598-3.999, with room either side, and it also contains both drawn
# planet lines -- TRAPPIST-1 b at 3.999 and GJ 581 e at 2.271.
# ★ NOTHING PLOTTED IS CLIPPED BY IT, and that is asserted rather than
# assumed: the fault being corrected is an axis that hid the data, and it
# must not be corrected by hiding different data.  Both assertions below
# cover every drawn datum -- the 402 window ceilings AND the reference
# lines -- so a future re-extraction that widened a drift grid, or a new
# planet with a shorter period, stops the build instead of being cropped.
# What the range costs is stated and not hidden: Earth's rotation and orbit
# (0.034 and 0.0059 m s^-2) fall far below the foot of the axis and are
# given in the caption as numbers, where they already were, and the number
# of the sample's own planets below the foot is counted here and quoted
# there.
YLO, YHI = 2.0, 5.0
N_CLIPPED = int(((ACC < YLO) | (ACC > YHI)).sum())
assert N_CLIPPED == 0, (
    '%d of %d Class A window ceilings fall outside the plotted range '
    '%g-%g m s^-2: widen the axis rather than hide them'
    % (N_CLIPPED, ACC.size, YLO, YHI))
# The two reference accelerations the axis no longer reaches must be quoted in
# the caption, so the generator has to know that it dropped them.
N_REF_BELOW = sum(1 for a in (A_ROT, A_ORB) if a < YLO)
assert N_REF_BELOW == 2, 'the caption text assumes both Earth lines are off-axis'
# ...and how many of the sample's own planets the axis no longer reaches, which
# the caption also states.
N_PL_BELOW = sum(1 for a, _, _ in PACC if a < YLO)

W, H = 245.0, 150.0
fig = plt.figure(figsize=(W / 72.0, H / 72.0))
# the right-hand margin is the nHz axis of R2-M9, so the plot box gives it room
ax = fig.add_axes([0.175, 0.170, 0.705, 0.800])

FLO, FHI = 80.0, 950.0
ax.fill_between([FLO, FHI], [CEIL_MAX, CEIL_MAX], [YHI, YHI],
                color='0.86', lw=0, zorder=0)
ax.fill_between([FLO, FHI], [CEIL_MIN, CEIL_MIN], [CEIL_MAX, CEIL_MAX],
                color='0.93', lw=0, zorder=0)
ax.scatter(FREQ, ACC, s=5, marker='o', facecolor='#0072B2', edgecolor='none',
           alpha=0.55, zorder=4, label='searched window (ceiling)')
ax.axhline(CEIL_MED, color='k', ls='--', lw=1.0, zorder=5)

# With one decade of ordinate the two ceiling populations separate, so say how
# many windows sit in each.  Counted here, never typed.
N_DEFAULT = int(ACC.size - N_WIDE)
# moved up out of the foot of the panel: the Jupiter rotation line of R2-M9 and
# the GJ 581 e line both land there, and three annotations in one corner is how
# the figure 7 overlap happened.
ax.text(0.035, 0.42,
        '%d window ceilings:\n%d at %.2f, %d at %.2f m s$^{-2}$'
        % (ACC.size, N_DEFAULT, CEIL_MED, N_WIDE, CEIL_MAX),
        transform=ax.transAxes, ha='left', va='bottom', fontsize=6.0,
        color='#0072B2', linespacing=1.4)

# A planet's line-of-sight acceleration does not depend on the observing
# frequency, so it belongs here as a horizontal line.
# v4.10 (figures): label the two planets with their ACCELERATION, which is
# what the ordinate is and what the caption quotes (\AccelWorstVal,
# \AccelSecondVal).  They carried orbital periods, so the caption named one
# quantity and the figure printed another; both come from this file, so no
# number was wrong, but a reader could not match them up.
# v4.11: Earth's rotation and orbit are no longer DRAWN.  At 0.034 and 0.0059
# m s^-2 they are two and three decades below everything else in the figure,
# and drawing them is what forced the ordinate that hid the data.  They are
# quoted in the caption instead.
REFS = [(A_WORST, '%s (%.2f m s$^{-2}$)'
         % (N_WORST.replace('-', '–'), A_WORST), '#D55E00', '-',
         (0.965, 1.055, 'right', 'bottom')),
        (A_SECOND, '%s (%.2f m s$^{-2}$)' % (N_SECOND, A_SECOND), '#CC79A7',
         # ★ ABOVE its own line, not below it: the Jupiter-rotation line added
         #   for R2-M9 lies at 2.16 m s^-2 and this label was being printed at
         #   2.14, straight through it.
         '-.', (0.965, 1.014, 'right', 'bottom'))]
# ★ The reference lines are DRAWN data: a line outside the limits is as
# hidden as a point outside them, and this is the clause that stops the
# ordinate being narrowed until something falls off it.
_REF_OUT = [lab for y, lab, _c, _l, _p in REFS if not YLO <= y <= YHI]
assert not _REF_OUT, (
    'the reference line(s) %s fall outside the plotted range %g-%g m s^-2: '
    'widen the axis rather than hide them' % (_REF_OUT, YLO, YHI))
for y, lab, col, ls, (fx, fy, ha, va) in REFS:
    ax.axhline(y, color=col, ls=ls, lw=1.1, zorder=3)
    ax.text(FHI * fx, y * fy, lab, ha=ha, va=va, fontsize=6.0, color=col)

ax.set_xscale('log'); ax.set_yscale('log')
ax.set_xlim(FLO, FHI); ax.set_ylim(YLO, YHI)
ax.set_ylabel(r'max. line-of-sight acceleration (m s$^{-2}$)')
ax.set_xticks([100, 200, 300, 500, 700, 900])
ax.set_xticklabels(['100', '200', '300', '500', '700', '900'])
ax.set_yticks([2, 2.5, 3, 3.5, 4, 4.5, 5])
ax.set_yticklabels(['2', '2.5', '3', '3.5', '4', '4.5', '5'])
ax.minorticks_off()
ax.set_xlabel('observing frequency (GHz)')
ax.text(0.985, 0.955, 'not searched', transform=ax.transAxes, ha='right',
        va='top', fontsize=6.6, color='0.30')

# ---- R2-M9: the same ordinate as a fractional drift rate, which is the unit the
#      literature quotes.  A secondary axis, not a second plot: the transform is
#      exactly Eq. (accel), so the two scales cannot disagree.
sax = ax.secondary_yaxis('right', functions=(nhz, a_of_nhz))
sax.set_ylabel(r'$|\dot\nu/\nu|$ (nHz)', fontsize=7.6, labelpad=2.0)
sax.set_yticks([7, 8, 9, 10, 12, 14, 16])
sax.set_yticklabels(['7', '8', '9', '10', '12', '14', '16'], fontsize=6.8)
sax.minorticks_off()
# Jupiter's own rotation, drawn on the axis it is published on.  It is below the
# ceiling, so a reader can see at once that a Jupiter-like spin alone consumes
# most of the budget and leaves little for the orbit.
A_JUP_ROT = _jup_rot_accel()
assert YLO <= A_JUP_ROT <= YHI, A_JUP_ROT
ax.axhline(A_JUP_ROT, color='0.35', ls=':', lw=1.0, zorder=3)
ax.text(FLO * 1.06, A_JUP_ROT / 1.014,
        "a Jupiter's equatorial rotation (%.1f m s$^{-2}$)" % A_JUP_ROT,
        ha='left', va='top', fontsize=6.0, color='0.35')
# ★ no legend.  Its single entry, "searched window (ceiling)", said nothing the
# blue annotation above does not say with its counts, and it occupied the corner
# the new reference line needs.

os.makedirs(os.path.join(HERE, 'figures'), exist_ok=True)
fig.savefig(os.path.join(HERE, 'figures', 'drift_acceleration.pdf'))
plt.close(fig)

# ------------------------------------------------------------------- macros
M('AccelCeilMed', '%.2f' % CEIL_MED)
M('AccelCeilMin', '%.2f' % CEIL_MIN)
M('AccelCeilMax', '%.2f' % CEIL_MAX)
M('AccelDriftLo', '%.1f' % (CEIL_MED / C_MS * FREQ.min() * 1e9 / 1e3))
M('AccelDriftHi', '%.1f' % (CEIL_MED / C_MS * FREQ.max() * 1e9 / 1e3))
M('AccelFreqLo', '%.0f' % FREQ.min())
M('AccelFreqHi', '%.0f' % FREQ.max())
M('AccelEarthRot', '%.3f' % A_ROT)
M('AccelEarthOrb', '%.4f' % A_ORB)
M('AccelRotMargin', '%.0f' % (CEIL_MED / A_ROT))
M('AccelOrbMargin', '%.0f' % (CEIL_MED / A_ORB))
# v4.11: the ordinate is 1--10 m s^-2 and the caption must account for what
# that range does not reach.  Both counts are measured in the figure block.
M('AccelNDefault', '%d' % N_DEFAULT)
M('AccelNPlBelowAxis', '%d' % N_PL_BELOW)
M('AccelWorstName', N_WORST.replace('-', '--'))
M('AccelWorstVal', '%.2f' % A_WORST)
M('AccelWorstP', '%.2f' % P_WORST)
M('AccelSecondName', N_SECOND.replace('-', '--'))
M('AccelSecondVal', '%.2f' % A_SECOND)
M('AccelNAbove', '%d' % N_ABOVE)
M('AccelNBelowMed', '%d' % N_BELOW_MED)
M('AccelNPlanets', '%d' % len(PACC))
M('AccelNCeil', '%d' % len(CEILS))
M('AccelNWide', '%d' % N_WIDE)
M('AccelWideStar', (WIDE_STARS[0] if WIDE_STARS else '--').replace('-', '--'))
M('AccelShortPctMax', '%.2f' % SHORT_PCT_MAX)
M('AccelShortPctMed', '%.0f' % SHORT_PCT_MED)
for _p in ('b', 'c', 'd'):
    if _p in TRAP:
        M('OrbAccTrap' + _p, '%.2f' % TRAP[_p])
# R1-9: the orbital-phase fraction above the ceiling, moved here from
# v363_calc.py, which hard-coded both a_max and the two ceilings as literals.
# For a circular orbit |a_los| = a_max |cos theta| at the measured
# (transiting, effectively edge-on) inclination, so the fraction of phase
# above a ceiling a_c is (2/pi) arccos(a_c/a_max).  \TrapPhaseHi is measured
# against the DEFAULT (median) ceiling, \TrapPhaseLo against the WIDENED one
# used on TRAPPIST-1's own windows; the text must say which is which.
_phase = lambda ac: (0.0 if A_WORST <= ac else
                     (2 / math.pi) * math.acos(min(1.0, ac / A_WORST)))
M('TrapPhaseHi', '%.0f' % (100 * _phase(CEIL_MED)))
M('TrapPhaseLo', '%.0f' % (100 * _phase(CEIL_MAX)))

# ---------------------------------------------------------------- R2-M9, in nHz
# The ceiling, the published guideline, and the fraction of it this search
# reaches.  All three are needed in the abstract and in Conclusion 8, so they are
# macros and not a sentence anyone retypes.
NHZ_MED, NHZ_MAX = nhz(CEIL_MED), nhz(CEIL_MAX)
NHZ_SHEIKH = NHZ_LIT['sheikh_guideline']['nHz']
NHZ_JUP = nhz(_jup_rot_accel())
# ★ A CHECK THAT CAN FAIL, AND THE ONE WORTH HAVING: the referee's two arithmetic
#   claims.  The ceiling must be the quoted 12 nHz to the digit printed, and the
#   Jupiter line must take more than half the budget -- which is what makes
#   "transmitters on rapidly rotating bodies are not constrained" a statement
#   about this experiment rather than a disclaimer.  If a re-extraction widens
#   the drift grid these stop holding and the caption must be rewritten, which is
#   the point.
assert abs(NHZ_MED - 12.0) < 0.5, (
    'the drift ceiling is %.2f nHz, not the 12 nHz the text states' % NHZ_MED)
assert 0.5 < NHZ_JUP / NHZ_MED < 1.0, (
    'a Jupiter-like rotation is %.0f per cent of the ceiling; the caption claims '
    'it consumes most of the budget but leaves some'
    % (100 * NHZ_JUP / NHZ_MED))
# ★ NO NEW MACRO FOR THE CEILING IN nHz.  The manuscript has published it in
#   these units since round 13 without saying so: \DriftCeilLo is quoted as
#   Hz s^-1 GHz^-1, and one Hz per second per gigahertz IS one nanohertz.  A
#   second name for it is the twin-macro defect, so this file asserts the
#   identity instead of republishing the number, and the caption uses
#   \DriftCeilLo.  Both ends of the grid are checked.
for _nm, _got in (('DriftCeilLo', NHZ_MED), ('DriftCeilHi', NHZ_MAX)):
    assert abs(texnum(_nm) - _got) < 0.05, (
        'the catalogue gives %.3f nHz where \\%s is %.3f; one Hz per second '
        'per GHz is one nanohertz, so these are the same number'
        % (_got, _nm, texnum(_nm)))
M('AccelSheikhNHz', '%.0f' % NHZ_SHEIKH)
M('AccelSheikhPct', '%.0f' % (100 * NHZ_MED / NHZ_SHEIKH))
M('AccelJupRotNHz', '%.1f' % NHZ_JUP)
M('AccelJupRot', '%.1f' % _jup_rot_accel())
M('AccelJupPct', '%.0f' % (100 * NHZ_JUP / NHZ_MED))
# ★★★★ A CROSS-GENERATOR TWIN CHECK, BECAUSE `twinmacro` CANNOT SEE THIS ONE
#    -- AND IT IS INVERTED, BECAUSE THE FAMILY IT COMPARED AGAINST IS GONE.
#    The prose generator's round 590 published the same four quantities under a
#    \Ps... family fourteen minutes after this file published them under
#    \Accel..., and `twinmacro` strips neither "Ps" nor "Accel" as a prefix, so
#    two values for Jupiter's rotational acceleration -- 2.2 against 2.16 --
#    would have shipped with no gate able to say so.  The first form of this
#    check compared the two families and SKIPPED, printing that it had, when a
#    name was not yet published.
#      Round 590 is now RETIRED: generator, round file and \input all deleted.
#    So every name in the \Ps... family raises KeyError on every future run,
#    the old loop would have printed "SKIPPED" three times and asserted
#    nothing, and this project's commonest defect -- a check that cannot fail
#    -- would have been sitting inside the comment that documents it.
#      The question is therefore no longer "do the two agree" but "is there
#    only one", and that is what is asserted: no \Ps... name may be back in
#    the macro layer.  The independent recomputation of the four values has
#    not been lost -- `prosegate_r15.py` S2-S4 read \AccelSheikhNHz,
#    \AccelSheikhPct, \AccelJupRot and \AccelJupPct back out of the layer and
#    check them against a frozen record of the published Sheikh et al.
#    sentence and against omega^2 R for Jupiter recomputed from its radius and
#    rotation period -- and the general case is now a gate of its own,
#    `valuetwin.py`, which groups every cited macro by printed value and by
#    the unit beside it at the use site and fails on a cross-generator group
#    that nobody has declared.
#    `--drive 1` puts one of the retired names back and the clause must fire.
_TWINS = ('PsSheikhNHz', 'PsDriftPctSheikh', 'PsJupAccel', 'PsAccelRotRatio')
_DRV1 = ('--drive' in sys.argv
         and sys.argv[sys.argv.index('--drive') + 1] == '1')


def _has_macro(_n):
    try:
        texnum(_n)
    except KeyError:
        return False
    return True


_dup = [_n for _n in _TWINS if _has_macro(_n)]
if _DRV1:
    _dup = _dup + ['PsJupAccel']
assert not _dup, (
    'two names for one quantity are back in the macro layer: %s against this '
    'file\'s \\Accel... family.  Round 590 was retired at round 15 precisely '
    'because it published these four numbers a second time; one of the two '
    'families must go, and it is not this one -- the ownership table gives '
    'M9 here.' % ', '.join('\\' + _n for _n in _dup))
print('  twin check: none of the %d retired \\Ps... names is in the macro '
      'layer' % len(_TWINS))
M('AccelEarthNHz', '%.2f' % NHZ_LIT['earth_total']['nHz'])
M('AccelMargotNHz', '%.2f' % NHZ_LIT['margot_reach']['nHz'])
open(os.path.join(HERE, 'survey_numbers_round37.tex'), 'w').write(
    '%% GENERATED by make_fig_accel2d.py -- do not hand-edit.\n' + '\n'.join(OUT) + '\n')

print('drift_acceleration.pdf: %d Class A windows, %.0f-%.0f GHz'
      % (len(ROWS), FREQ.min(), FREQ.max()))
print('  ceiling: %.3f m/s2 (median), %.3f-%.3f across windows'
      % (CEIL_MED, CEIL_MIN, CEIL_MAX))
print('  = %.1f kHz/s at %.0f GHz and %.1f kHz/s at %.0f GHz'
      % (CEIL_MED / C_MS * FREQ.min() * 1e9 / 1e3, FREQ.min(),
         CEIL_MED / C_MS * FREQ.max() * 1e9 / 1e3, FREQ.max()))
print("  Earth rotation %.4f, Earth orbit %.5f m/s2 -> margin x%.0f, x%.0f"
      % (A_ROT, A_ORB, CEIL_MED / A_ROT, CEIL_MED / A_ORB))
print('  most demanding known planet: %s, %.3f m/s2 (P=%.3f d); %d of %d above the ceiling'
      % (N_WORST, A_WORST, P_WORST, N_ABOVE, len(PACC)))
print('  the grid takes %d ceiling values; %d windows (all %s) use the wider one,'
      % (len(CEILS), N_WIDE, ', '.join(WIDE_STARS)))
print('  and that wider ceiling still falls %.2f per cent short of %s'
      % (SHORT_PCT_MAX, N_WORST))
print('macros -> survey_numbers_round37.tex (%d)' % len(OUT))
