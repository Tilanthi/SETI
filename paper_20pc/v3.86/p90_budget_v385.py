#!/usr/bin/env python3
"""Referee 1, point 15: a systematic uncertainty budget on P_90.

The paper quotes P_90 to two significant figures and lists its ingredients
in several different places, but never says how well the number is known.
This generator assembles the budget, term by term, and combines it.

Every term is multiplicative on P_90, because

    P_90 = 4 pi d^2 . S_min . C_resp . C_smear . (P_90 / P_trig),

so a fractional error on any factor is a fractional error on P_90, and d
enters squared.  Terms are combined in quadrature where they are
independent and stated separately where they are not errors at all but
known spreads a reader must carry.
"""
import csv, json, math, os
import collections
import numpy as np
from inject_curve import ROWS as TRIALS, curve, pX, P90_POOL, TRANSFER_P90

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = []
def M(n, v): OUT.append(r'\newcommand{\%s}{%s}' % (n, v))

CAT = [r for r in csv.DictReader(open(os.path.join(HERE, 'per_target_results_v3.86.csv')))
       if r['search_class'] == 'A']

# ---------------------------------------------------------------- 1. flux scale
# ALMA's delivered absolute flux scale. The observatory's own accuracy
# statement is band-dependent and the archive spans 2013-2025, so take the
# conservative per-band figure and weight it by the band mix of the Class A
# sample. These are specifications, not measurements made here.
FLUXCAL = {3: 0.05, 4: 0.05, 5: 0.05, 6: 0.05, 7: 0.10, 8: 0.10, 9: 0.20, 10: 0.20}
BANDN = collections.Counter(int(r['band']) for r in CAT)
E_FLUX = sum(BANDN[b] * FLUXCAL[b] for b in BANDN) / sum(BANDN.values())
E_FLUX_WORST = max(FLUXCAL[b] for b in BANDN)

# ------------------------------------------------------------------ 2. distance
# P_90 scales as d^2, so the parallax error enters doubled.
PLX_WORST = 0.0248        # the largest fractional parallax error in the sample
E_DIST_WORST = 2 * PLX_WORST
# Gaia DR3 fractional parallax errors for stars this close are ~1e-4-1e-3;
# the 2.5 per cent case is a close binary. Quote the worst as the bound.
E_DIST_TYP = 2 * 0.001

# --------------------------------------------- 3. spectral response, phase
# A carrier at an unknown sub-channel position is attenuated by a factor the
# paper corrects at the median. The residual is not an error in the
# calibration sense: it is an irreducible unknown about the carrier.
H = list(csv.DictReader(open(os.path.join(HERE, 'hanning_response_trials_v3.58.csv'))))
FAC = collections.defaultdict(list)
for h in H:
    FAC[float(h['phi'])].append(float(h['factor']))
F_MED = float(np.median([float(h['factor']) for h in H]))
F_LO = min(np.mean(FAC[k]) for k in FAC)
F_HI = max(np.mean(FAC[k]) for k in FAC)
E_PHASE_LO = F_LO / F_MED - 1
E_PHASE_HI = F_HI / F_MED - 1

# ------------------------------------------ 4. finite trials in the campaign
# The recovery curve is estimated from a finite number of injections, so
# P_90 carries a Monte Carlo error. Bootstrap the trials.
RNG = np.random.default_rng(20260920)
idx = np.arange(len(TRIALS))
boot = []
for _ in range(400):
    sel = [TRIALS[i] for i in RNG.integers(0, len(TRIALS), len(TRIALS))]
    v = pX(curve(sel), 0.9)
    if v == v:
        boot.append(v)
boot = np.array(boot)
E_MC = float(np.std(boot) / P90_POOL)
MC_LO, MC_HI = np.percentile(boot, [2.5, 97.5]) / P90_POOL

# --------------------------------------------------- 5. window-to-window transfer
# Not an error on a given window; the spread between windows. It dominates
# any survey-wide statement and is reported separately for that reason.
T_LO, T_HI = TRANSFER_P90

# ------------------------------------------------------- 6. pointing / beam
# The star sits at the phase centre, so the primary-beam correction that
# matters for the control annulus does not apply to it; what remains is the
# residual pointing error against the beam, which at ALMA's specified
# accuracy is a small fraction of a beam on axis, where the beam is flat.
POINT_ARCSEC = 0.6                 # ALMA absolute pointing, offset observing
THETA = np.array([float(r['theta_pb_arcsec']) for r in CAT])
# Gaussian primary beam: loss = 1 - exp(-4 ln2 (dp/theta)^2)
E_POINT = float(np.max(1 - np.exp(-4 * math.log(2) * (POINT_ARCSEC / THETA) ** 2)))

# ------------------------------------- 7. atmospheric decorrelation
# Declared in the methodology as multiplying S_min and omitted from this
# budget until the round-2 self-review. It is not symmetric: an injected
# tone is added to already-calibrated visibilities and so suffers no
# decorrelation, while a real carrier does. P_90 is therefore optimistic by
# this amount, one-directionally, and it belongs in the budget as a
# one-sided term rather than in quadrature.
E_DECOR_LO, E_DECOR_HI = 0.05, 0.20

# ------------------------------------------------------------------ combine
# Terms 1, 2, 4 and 6 are independent errors on the quoted number; add in
# quadrature. Terms 3 and 5 are known spreads, not errors, and are carried
# separately so that a reader does not double-count them.
# Q27: pointing is a one-sided loss and E_POINT is its MAXIMUM over the
# sample, so it belongs with the other one-sided terms and not in a
# symmetric quadrature sum. The combined figure is now the two genuinely
# two-sided errors plus the Monte Carlo term; the typical and worst cases
# use consistent choices for every term.
E_COMB = math.sqrt(E_FLUX ** 2 + E_DIST_TYP ** 2 + E_MC ** 2)
E_COMB_WORST = math.sqrt(E_FLUX_WORST ** 2 + E_DIST_WORST ** 2 + E_MC ** 2)

TERMS = [
    ('Absolute flux scale', 'ALMA calibration, band-weighted',
     '$\\pm%.0f$' % (100 * E_FLUX), 'quadrature'),
    ('Distance', 'Gaia parallax, as $d^{2}$',
     '$\\pm%.1f$' % (100 * E_DIST_TYP), 'quadrature'),
    ('Injection statistics', '%d trials, bootstrap' % len(TRIALS),
     '$\\pm%.1f$' % (100 * E_MC), 'quadrature'),

    (r'\emph{Combined}', 'in quadrature', '$\\pm%.0f$' % (100 * E_COMB), ''),
    ('Decorrelation', 'one-sided; injections suffer none',
     '$+%.0f/+%.0f$' % (100 * E_DECOR_LO, 100 * E_DECOR_HI), 'carried'),
    ('Pointing', 'one-sided; worst case, %.1f\\arcsec{} off axis' % POINT_ARCSEC,
     '$+%.1f$' % (100 * E_POINT), 'carried'),
    ('Sub-channel phase', 'irreducible; median-corrected',
     '$%+.0f/%+.0f$' % (100 * E_PHASE_LO, 100 * E_PHASE_HI), 'carried'),
    ('Window-to-window', 'transfer uncertainty off-grid',
     '$%+.0f/%+.0f$' % (100 * (T_LO - 1), 100 * (T_HI - 1)), 'carried'),
]
T = [r'\begin{tabular}{@{}l@{~}l@{~}r@{}}', r'\hline',
     r'Term & Origin & $\Delta P_{90}$ (\%) \\', r'\hline']
for name, origin, val, kind in TERMS:
    if name.startswith(r'\emph{Combined'):
        T.append(r'\hline')
    if kind == 'carried' and TERMS[TERMS.index(
            (name, origin, val, kind)) - 1][3] != 'carried':
        T.append(r'\hline')
    T.append('%s & %s & %s \\\\' % (name, origin, val))
T += [r'\hline', r'\end{tabular}']
open(os.path.join(HERE, 'tab_p90budget_v385.tex'), 'w').write('\n'.join(T) + '\n')

M('BudFlux', '%.0f' % (100 * E_FLUX))
M('BudFluxWorst', '%.0f' % (100 * E_FLUX_WORST))
M('BudDist', '%.1f' % (100 * E_DIST_TYP))
M('BudDistWorst', '%.1f' % (100 * E_DIST_WORST))
M('BudMC', '%.1f' % (100 * E_MC))
M('BudMCLo', '%.2f' % MC_LO)
M('BudMCHi', '%.2f' % MC_HI)
M('BudPoint', '%.1f' % (100 * E_POINT))
M('BudPointArc', '%.1f' % POINT_ARCSEC)
M('BudComb', '%.0f' % (100 * E_COMB))
M('BudCombWorst', '%.0f' % (100 * E_COMB_WORST))
M('BudPhaseLo', '%.0f' % (100 * E_PHASE_LO))
M('BudPhaseHi', '%.0f' % (100 * E_PHASE_HI))
M('BudTransLo', '%.0f' % (100 * (T_LO - 1)))
M('BudTransHi', '%.0f' % (100 * (T_HI - 1)))
M('BudDecorLo', '%.0f' % (100 * E_DECOR_LO))
M('BudDecorHi', '%.0f' % (100 * E_DECOR_HI))
M('BudBoot', '%d' % len(boot))
M('BudDominant', 'the absolute flux scale' if E_FLUX == max(E_FLUX, E_DIST_TYP, E_MC, E_POINT)
  else 'the injection statistics')

# R2-m4: a worked example for one representative window, so that how the
# one-sided terms were kept out of the quadrature sum is explicit.
_cand = sorted((float(r['eirp_p90_W']), r['star_name'], r['band'])
               for r in CAT if r.get('eirp_p90_W'))
_p, _wstar, _wband = _cand[len(_cand) // 2]
M('WorkedStar', _wstar.split('  Gaia')[0].replace('-', '--'))
M('WorkedBand', _wband)
M('WorkedPNinety', '%.2f' % (_p / 1e15))
M('WorkedTwoSided', '%.0f' % (100 * E_COMB))
M('WorkedLoW', '%.2f' % (_p * (1 - E_COMB) / 1e15))
M('WorkedHiW', '%.2f' % (_p * (1 + E_COMB) / 1e15))
M('WorkedBiasW', '%.2f' % (_p * (1 + E_COMB) * (1 + E_DECOR_HI) / 1e15))
M('WorkedTransLoW', '%.2f' % (_p * T_LO / 1e15))
M('WorkedTransHiW', '%.2f' % (_p * T_HI / 1e15))

open(os.path.join(HERE, 'survey_numbers_round38.tex'), 'w').write(
    '%% GENERATED by p90_budget_v385.py -- do not hand-edit.\n' + '\n'.join(OUT) + '\n')

print('P90 systematic budget (per cent of P_90):')
print('  worked example, %s B%s: P90 = %.2fe15 W, two-sided +-%.0f%% gives'
      ' %.2f-%.2fe15, the one-sided bias takes the upper end to %.2fe15,'
      ' and the transfer bracket spans %.2f-%.2fe15'
      % (_wstar[:12], _wband, _p / 1e15, 100 * E_COMB,
         _p * (1 - E_COMB) / 1e15, _p * (1 + E_COMB) / 1e15,
         _p * (1 + E_COMB) * (1 + E_DECOR_HI) / 1e15,
         _p * T_LO / 1e15, _p * T_HI / 1e15))
print('  absolute flux scale  %5.1f  (band-weighted; worst band %.0f)'
      % (100 * E_FLUX, 100 * E_FLUX_WORST))
print('  distance (d^2)       %5.1f  (worst case %.1f)'
      % (100 * E_DIST_TYP, 100 * E_DIST_WORST))
print('  injection statistics %5.1f  (%d bootstraps, 95%% %.2f-%.2f x P90)'
      % (100 * E_MC, len(boot), MC_LO, MC_HI))
print('  pointing             %5.1f  (%.1f arcsec, worst theta_PB %.1f)'
      % (100 * E_POINT, POINT_ARCSEC, THETA.min()))
print('  COMBINED             %5.1f  (worst case %.1f)'
      % (100 * E_COMB, 100 * E_COMB_WORST))
print('  carried separately: sub-channel phase %+.0f/%+.0f, '
      'window-to-window %+.0f/%+.0f'
      % (100 * E_PHASE_LO, 100 * E_PHASE_HI, 100 * (T_LO - 1), 100 * (T_HI - 1)))
print('table -> tab_p90budget_v385.tex; macros -> survey_numbers_round38.tex (%d)'
      % len(OUT))
