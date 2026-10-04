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
import csv, json, math, os
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
W, H = 245.0, 168.0
fig = plt.figure(figsize=(W / 72.0, H / 72.0))
ax = fig.add_axes([0.175, 0.155, 0.80, 0.815])

FLO, FHI = 80.0, 950.0
ax.fill_between([FLO, FHI], [CEIL_MAX, CEIL_MAX], [1e3, 1e3],
                color='0.86', lw=0, zorder=0)
ax.fill_between([FLO, FHI], [CEIL_MIN, CEIL_MIN], [CEIL_MAX, CEIL_MAX],
                color='0.93', lw=0, zorder=0)
ax.scatter(FREQ, ACC, s=5, marker='o', facecolor='#0072B2', edgecolor='none',
           alpha=0.55, zorder=4, label='searched window (ceiling)')
ax.axhline(CEIL_MED, color='k', ls='--', lw=1.0, zorder=5)

# A planet's line-of-sight acceleration does not depend on the observing
# frequency, so it belongs here as a horizontal line, exactly like Earth's.
REFS = [(A_WORST, '%s (%.2f d)' % (N_WORST.replace('-', '\u2013'), P_WORST), '#D55E00', '-'),
        (A_SECOND, '%s (%.2f d)' % (N_SECOND, P_SECOND), '#CC79A7', '-.'),
        (A_ROT, "Earth's rotation", '#009E73', ':'),
        (A_ORB, "Earth's orbit", '#56B4E9', ':')]
# Stagger the two planet labels: the accelerations differ by less than a
# factor of two, so right-aligning both puts them on top of each other.
for (y, lab, col, ls), (fx, fy, ha, va) in zip(
        REFS, [(0.965, 1.22, 'right', 'bottom'), (0.115, 0.82, 'left', 'top'),
               (0.965, 1.22, 'right', 'bottom'), (0.965, 1.22, 'right', 'bottom')]):
    ax.axhline(y, color=col, ls=ls, lw=1.1, zorder=3)
    ax.text(FHI ** fx * FLO ** (1 - fx) if fx < 0.5 else FHI * fx, y * fy, lab,
            ha=ha, va=va, fontsize=6.0, color=col)

ax.set_xscale('log'); ax.set_yscale('log')
ax.set_xlim(FLO, FHI); ax.set_ylim(1e-3, 3e2)
ax.set_ylabel(r'max. line-of-sight acceleration (m s$^{-2}$)')
ax.set_xticks([100, 200, 300, 500, 700, 900])
ax.set_xticklabels(['100', '200', '300', '500', '700', '900'])
ax.set_xlabel('observing frequency (GHz)')
ax.text(0.985, 0.955, 'not searched', transform=ax.transAxes, ha='right',
        va='top', fontsize=6.6, color='0.30')
ax.legend(loc='lower left', frameon=False, borderpad=0.2, handletextpad=0.4,
          markerscale=1.6)

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
