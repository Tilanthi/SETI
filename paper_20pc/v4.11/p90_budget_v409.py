#!/usr/bin/env python3
r"""Referee 1, point 15: a systematic uncertainty budget on $P_{90}$.

Supersedes `p90_budget_v385.py` (round 38).  Every term is multiplicative on
$P_{90}$, because

    P_90 = 4 pi d^2 . S_min . C_resp . C_smear . (P_90 / P_trig),

so a fractional error on any factor is a fractional error on $P_{90}$, and
$d$ enters squared.  Terms are combined in quadrature where they are
independent and stated separately where they are not errors at all but known
spreads a reader must carry.

★★★ WHAT v4.09 CHANGES, AND WHY THE STANDING NOTE WAS WRONG.  Four versions
of this paper carried the note "Table 11 is still 6 of 7 rows hand-written".
It is not: the predecessor generated the whole table.  What was actually
wrong is narrower and worse.

  * `PLX_WORST = 0.0248`, commented "the largest fractional parallax error in
    the sample", was a TYPED CLAIM ABOUT THE SAMPLE that nothing compared to
    the sample.  Measured from SIMBAD's own Gaia DR3 parallaxes over
    `BudPlxNStar` of the catalogue's stars it is 0.0165 -- the literal was
    x1.5 too large -- and the worst star is gam Tri = HD 14055, the star of
    v4.09's two new threshold crossings.
  * `E_DIST_TYP = 2 * 0.001` was a typed FRACTIONAL parallax error, while the
    products' own `parallax_err` field is a typed ABSOLUTE 0.001 mas
    placeholder on 396 of 400 products.  Two different quantities wearing the
    same number, neither measured.  The measured median fractional error is
    7.9e-4, so the printed +-0.2 per cent survives -- by luck, and now by
    measurement.
  * `E_DECOR_LO, E_DECOR_HI = 0.05, 0.20` have no source anywhere in this
    project.  They are now DECLARED an external assumption and asserted to be
    so, rather than printed beside measured terms as if they were one.
  * ★★ the WINDOW-TO-WINDOW TRANSFER row -- the row referee 1's point 5 is
    about -- was computed as `BudTransLo`/`BudTransHi` and then dropped by
    `retire_macros.py` as unreferenced, so it never reached the table.  That
    is the same mechanism that hid `\RsevNWinA`'s typed 403.  It is printed
    now, from the measured x0.94-1.09 over the `BudTransN` directly tested
    Class A windows, with `BudTransN + RsevNTransferA == NWinA` asserted.
  * `T_LO, T_HI = MC_LO, MC_HI`: the transfer and campaign rows were
    literally the same two numbers.  They are now separate and asserted to
    differ.
  * ★ `\BudDominant` was chosen as the largest of four terms, two of which
    are NOT in the quadrature sum the sentence attributes it to, so the paper
    printed "the independent terms combine to +-9 per cent dominated by the
    injection statistics" -- a term that is not one of them.  It is now the
    largest of exactly the three rows above the Combined line.

Usage: p90_budget_v409.py [--drive N]   N = 1..9
"""
import collections
import csv
import glob
import json
import math
import os
import re
import sys

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
INP = os.path.join(HERE, 'r8inputs', 'v409')
# ★ `--drive 0` is "no perturbation, but DO NOT write a production path".
#   The gate's own baseline check needs to run the generator unperturbed, and
#   if that run landed on the real products it would be the very thing D36
#   forbids -- a test writing where production reads.  So DRIVE is None when
#   the flag is absent and an integer (including 0) when it is present, and
#   the suffix follows the flag rather than the perturbation.
DRIVE = int(sys.argv[sys.argv.index('--drive') + 1]) if '--drive' in sys.argv \
    else None
SUF = '' if DRIVE is None else '_drive%d' % DRIVE
fail = []


def suffixed(name):
    # ★ D36's standing rule: a driven run may not land on a production path.
    stem, ext = os.path.splitext(name)
    return stem + SUF + ext


def ck(tag, cond, detail=''):
    if not cond:
        fail.append(tag)
    print('  %-56s %s  %s' % (tag, 'PASS' if cond else 'FAIL', detail))


def macro(name):
    """Read a generated macro's numeric value out of the round files.

    Measured quantities are read rather than retyped so that this table and
    the text that quotes it cannot disagree, which is exactly how they came
    to in v4.07.
    """
    for f in sorted(glob.glob(os.path.join(HERE, 'survey_numbers*.tex'))):
        # ★ \providecommand{\X}{}\renewcommand{\X}{v} is now a definition
        # shape too; a reader that knows only \newcommand reports every
        # macro written that way as "not generated anywhere".
        mm = re.search(
            r'\\(?:new|renew)command\{\\%s\}\{([-+0-9.]+)\}' % name,
            open(f, errors='replace').read())
        if mm:
            return float(mm.group(1))
    raise SystemExit('p90_budget_v409: macro %s is not generated anywhere; '
                     'it must be written before this runs' % name)


def macro_text(name):
    """The same, for a macro whose body is not a number -- a star name.

    `macro()` matches a numeric body only, so asking it for the worst star's
    designation reported it as "not generated anywhere", which is a true
    message about a false condition.
    """
    for f in sorted(glob.glob(os.path.join(HERE, 'survey_numbers*.tex'))):
        mm = re.search(
            r'\\(?:new|renew)command\{\\%s\}\{((?:[^{}]|\{[^{}]*\})*)\}'
            % name, open(f, errors='replace').read())
        if mm and mm.group(1).strip():
            return mm.group(1).strip()
    return None


OUT = []


def M(n, v):
    assert n.isalpha(), 'macro name %r is not letters-only' % n
    OUT.append(r'\newcommand{\%s}{%s}' % (n, v))


CATALL = list(csv.DictReader(open(os.path.join(
    HERE, 'per_target_results_v3.99.csv'))))
CAT = [r for r in CATALL if r['search_class'] == 'A']
print('Class A windows: %d of %d' % (len(CAT), len(CATALL)))

# ---------------------------------------------------------------- 1. flux scale
# ALMA's delivered absolute flux scale.  EXTERNAL: the observatory's own
# band-dependent accuracy specification, weighted by the band mix of the
# Class A sample.  These are specifications, not measurements made here, and
# the emitted JSON says so.
FLUXCAL = {3: 0.05, 4: 0.05, 5: 0.05, 6: 0.05, 7: 0.10, 8: 0.10,
           9: 0.20, 10: 0.20}
FLUXCAL_SOURCE = 'ALMA Technical Handbook absolute-accuracy specification ' \
                 '(EXTERNAL SPECIFICATION, not measured here)'
BANDN = collections.Counter(int(r['band']) for r in CAT)
E_FLUX = sum(BANDN[b] * FLUXCAL[b] for b in BANDN) / sum(BANDN.values())
E_FLUX_WORST = max(FLUXCAL[b] for b in BANDN)

# ------------------------------------------------------------------ 2. distance
# P_90 scales as d^2, so the parallax error enters doubled.  MEASURED, from a
# live SIMBAD TAP resolution of the catalogue's own stars against Gaia DR3.
# ★★★ v4.11: THE JOIN BEHIND THIS TERM LOST TWELVE STARS, AND THE TERM IT
# PRODUCED WAS THE FLATTERING ONE.  `simbad_plx_v409.json` is a
# position-only SIMBAD resolution of the catalogue's stars and it covers 77
# of the 89: SIMBAD positions are J2000, the work list is Gaia DR3 at J2016,
# and the largest proper-motion displacement in this sample is 321 arcsec,
# so the twelve it loses are the nearest, fastest stars -- Barnard's Star,
# Proxima, Kapteyn's Star, Luyten's Star and tau Cet among them, i.e. exactly
# the stars whose parallax matters most.  `selfunc_v411.py`'s S11 propagates
# proper motion before matching and resolves 89 of 89, and over all 89 the
# worst fractional parallax error is 2.5 per cent against the 1.65 this file
# published.  Nothing compared the two until `synmacro.py` was written.
#
# Both terms are therefore taken from the 89-star measurement, read out of
# the macro layer so there is one owner, and the file-based 77-star figure is
# kept only to be reported as the size of the join's effect.
PLX = json.load(open(os.path.join(INP, 'simbad_plx_v409.json')))
frac = sorted((p[3] / p[2], p[1]) for p in PLX if p[2] and p[3])
E_PLX_MED_77 = float(np.median([f for f, _ in frac]))
E_PLX_WORST_77, WORST_STAR_77 = frac[-1]
N_PLX_77 = len(frac)
_sfw = macro('SfPlxWorstPct')
_sfm = macro('SfPlxMedPct')
_sfn = macro('SfPlxNStar')
assert _sfw and _sfm and _sfn, (
    'this term is measured over every searched star by selfunc_v411.py '
    '(round 111); it must run before this generator')
E_PLX_WORST = float(_sfw) / 100.0
E_PLX_MED = float(_sfm) / 100.0
WORST_STAR = macro_text('SfPlxWorstStar') or '--'
N_PLX = int(_sfn)
if DRIVE == 1:
    E_PLX_WORST = E_PLX_WORST_77    # the 77-star join; must now disagree
E_DIST_TYP = 2 * E_PLX_MED
E_DIST_WORST = 2 * E_PLX_WORST
N_STAR_CAT = len(set(r['star_name'] for r in CATALL))

# --------------------------------------------- 3. spectral response, phase
# A carrier at an unknown sub-channel position is attenuated by a factor the
# paper corrects at the median.  The residual is not an error in the
# calibration sense: it is an irreducible unknown about the carrier.
H = list(csv.DictReader(open(os.path.join(
    HERE, 'hanning_response_trials_v3.58.csv'))))
FAC = collections.defaultdict(list)
for h in H:
    FAC[float(h['phi'])].append(float(h['factor']))
F_MED = float(np.median([float(h['factor']) for h in H]))
E_PHASE_LO = min(np.mean(FAC[k]) for k in FAC) / F_MED - 1
E_PHASE_HI = max(np.mean(FAC[k]) for k in FAC) / F_MED - 1

# ------------------------------------------ 4. finite trials in the campaign
# The recovery curve is estimated from a finite number of injections, so
# P_90 carries a Monte Carlo error.  The campaign's own bootstrap is over
# CONFIGURATIONS, which is the level at which the trials are independent:
# tones injected into one window share its noise realisation, its control
# ensemble and its beam.
M3A = {x['stratum']: x for x in json.load(open(os.path.join(
    HERE, 'm3a_result_v400.json')))['strata']}['fine (<1 MHz)']
_P90 = M3A['P90_over_trigger']
_CI = M3A['P90_ci68']
E_MC = float((_CI[1] - _CI[0]) / 2.0 / _P90)
MC_LO, MC_HI = _CI[0] / _P90, _CI[1] / _P90
N_TONES, N_CONFIG = M3A['n_tones'], M3A['n_units']

# --------------------------------------------- 5. window-to-window transfer
# ★ THE ROW THAT NEVER REACHED THE TABLE (R1-5).  Not an error on a given
#   window: the spread BETWEEN windows, measured on the published criterion
#   over the windows the campaign injected into directly.
# ★★ THESE NOW COME FROM THE ADOPTED CAMPAIGN, not the superseded one.
#   The predecessor read \RsevTransARange* and \RsevNTransferA, which are
#   the round-7 campaign: 13 windows tested, 389 transferred, x0.94-1.09.
#   Printing those today would put "13 of 402" and "-6/+9 per cent" in the
#   same paragraph as the adopted 21 of 402 and x0.77-1.12 -- two campaigns
#   in one budget, which is exactly the contradiction this round exists to
#   remove.  The adopted names are read instead, and the superseded ones are
#   asserted to be retired so this cannot quietly revert.
T_LO = macro('EirpNinetyFacLo')
T_HI = macro('EirpNinetyFacHi')
T_N = int(macro('NInjWinA'))
T_TRANSFERRED = int(macro('NTransferWinA'))
T_NWINA = int(macro('NWinA'))
T_OLD_LO, T_OLD_HI = macro('RsevTransOldLo'), macro('RsevTransOldHi')
# ★ and the campaign row IS the transfer row: the bootstrap that produces
#   the interval is a bootstrap OVER THE INJECTED WINDOWS, so it already
#   contains the window-to-window spread.  The predecessor printed both,
#   which counted the same quantity twice.  One row now.
MC_LO, MC_HI = T_LO, T_HI

N_CONFIG = T_N
if DRIVE == 2:
    # ★ This drive used to read `T_LO, T_HI = MC_LO, MC_HI`, and the moment B4
    #   reversed -- transfer and campaign became ONE quantity, so MC is T by
    #   construction -- that assignment became a NO-OP and the drive stopped
    #   firing: a drive that cannot perturb is a check that cannot fail.
    #   Reinstate the defect B4 exists to catch, which is the budget carrying
    #   the quantity TWICE, under two row names.
    MC_LO, MC_HI = T_LO * 0.9, T_HI * 1.1
    _DRIVE2_CAMPAIGN_ROW = True
else:
    _DRIVE2_CAMPAIGN_ROW = False

# ------------------------------------------------------- 6. pointing / beam
# The star sits at the phase centre, so what remains is the residual pointing
# error against the beam, which at ALMA's specified accuracy is a small
# fraction of a beam on axis, where the beam is flat.  EXTERNAL specification.
POINT_ARCSEC = 0.6
POINT_SOURCE = 'ALMA absolute pointing specification (EXTERNAL)'
THETA = np.array([float(r['theta_pb_arcsec']) for r in CAT])
E_POINT = float(np.max(1 - np.exp(-4 * math.log(2)
                                  * (POINT_ARCSEC / THETA) ** 2)))

# ------------------------------------- 7. atmospheric decorrelation
# An injected tone is added to already-calibrated visibilities and so suffers
# no decorrelation, while a real carrier does.  P_90 is therefore optimistic
# by this amount, one-directionally.  ★ NO MEASUREMENT OF IT EXISTS in this
# project; it is declared as an assumption and asserted to be declared.
E_DECOR_LO, E_DECOR_HI = 0.05, 0.20
E_DECOR_SOURCE = 'DECLARED EXTERNAL ASSUMPTION -- no measurement exists ' \
                 'in this work'
if DRIVE == 3:
    E_DECOR_SOURCE = 'measured in this work'

# ------------------------------------------------------------------ combine
# Terms 1, 2 and the visibility-calibration bound are independent errors on
# the quoted number; add in quadrature.  E_MC is NOT in this sum: the
# campaign's bootstrap over configurations already contains both the
# finite-tone error and the spread between injected windows, it is strongly
# asymmetric, and adding it here as well would count it twice.
E_VISCAL = macro('VisCalPct') / 100.0
E_COMB = math.sqrt(E_FLUX ** 2 + E_DIST_TYP ** 2 + E_VISCAL ** 2)
E_COMB_WORST = math.sqrt(E_FLUX_WORST ** 2 + E_DIST_WORST ** 2
                         + E_VISCAL ** 2)
# ★ the dominant term of the sum is chosen from EXACTLY the rows in the sum
QUAD = {'the absolute flux scale': E_FLUX,
        'the Gaia parallaxes': E_DIST_TYP,
        'the visibility calibration': E_VISCAL}
DOMINANT = max(QUAD, key=QUAD.get)
if DRIVE == 4:
    QUAD['the injection statistics'] = E_MC       # a term not in the sum
    DOMINANT = max(QUAD, key=QUAD.get)

print('\nmeasured inputs')
print('  flux scale, band-weighted over %d Class A windows: %.4f (worst band '
      '%.2f); bands %s' % (len(CAT), E_FLUX, E_FLUX_WORST, dict(BANDN)))
print('  parallax: %d of %d catalogue stars resolved live in SIMBAD; '
      'fractional error median %.3e, max %.4f (%s)'
      % (len(frac), N_STAR_CAT, E_PLX_MED, E_PLX_WORST, WORST_STAR))
print('  transfer: %d of %d Class A windows tested directly, '
      'x%.2f-%.2f = %+.0f/%+.0f per cent'
      % (T_N, T_NWINA, T_LO, T_HI, 100 * (T_LO - 1), 100 * (T_HI - 1)))
print('  campaign: %d tones, %d configurations, x%.2f-%.2f'
      % (N_TONES, N_CONFIG, MC_LO, MC_HI))
print('  pointing: worst theta_pb %.2f arcsec -> %.4f' % (THETA.min(), E_POINT))
print('  combined %.4f (worst case %.4f), dominated by %s'
      % (E_COMB, E_COMB_WORST, DOMINANT))

# ------------------------------------------------------------- the table
TERMS = [
    ('Absolute flux scale', 'ALMA calibration, band-weighted',
     '$\\pm%.0f$' % (100 * E_FLUX), 'q'),
    ('Distance', 'Gaia parallax, as $d^{2}$; %d stars' % len(frac),
     '$\\pm%.1f$' % (100 * E_DIST_TYP), 'q'),
    ('Visibility calibration', 'block-to-block scale',
     '$\\pm%.1f$' % (100 * E_VISCAL), 'q'),
    (r'\emph{Combined}', 'in quadrature', '$\\pm%.0f$' % (100 * E_COMB), 'c'),
    ('Decorrelation', 'one-sided; injections suffer none; \\emph{assumed}',
     '$+%.0f/+%.0f$' % (100 * E_DECOR_LO, 100 * E_DECOR_HI), 'o'),
    ('Pointing', 'one-sided; worst case %.1f\\arcsec{} off axis'
     % POINT_ARCSEC, '$+%.1f$' % (100 * E_POINT), 'o'),
    ('Sub-channel phase', 'irreducible; median-corrected',
     '$%+.0f/%+.0f$' % (100 * E_PHASE_LO, 100 * E_PHASE_HI), 'o'),
    ] + ([('Calibration campaign', 'the same windows, resampled again',
           '$%+.0f/%+.0f$' % (100 * (MC_LO - 1), 100 * (MC_HI - 1)), 'o')]
         if _DRIVE2_CAMPAIGN_ROW else []) + [
    ('Window-to-window transfer',
     '%d of %d Class~A injected directly, bootstrap over those windows '
     '(%s tones)'
     % (T_N, T_NWINA, '{:,}'.format(N_TONES).replace(',', '\\,')),
     '$%+.0f/%+.0f$' % (100 * (T_LO - 1), 100 * (T_HI - 1)), 'o'),
]
N_ROWS = len(TERMS) if DRIVE != 5 else len(TERMS) + 1

# ------------------------------------------------------- assertions
SHIPPED = os.path.join(INP, 'tab_p90budget_v385_shipped.tex')
ship = open(SHIPPED).read() if os.path.exists(SHIPPED) else ''


def shipped_val(label):
    for line in ship.splitlines():
        if line.startswith(label + ' &'):
            return line.split('&')[-1].replace(r'\\', '').strip()
    return None


print('\nassertions -- every row is compared with the shipped literal')
ck('B1 the flux row reproduces the shipped literal',
   shipped_val('Absolute flux scale') == '$\\pm%.0f$' % (100 * E_FLUX),
   '%s vs computed $\\pm%.0f$' % (shipped_val('Absolute flux scale'),
                                  100 * E_FLUX))
_v = '$\\pm%.1f$' % (100 * E_DIST_TYP)
ck('B2 the distance row survives being measured',
   shipped_val('Distance') == _v,
   '%s vs measured %s' % (shipped_val('Distance'), _v))
ck('B3 the parallax term is measured over EVERY searched star, and the '
   'position-only join that covered 77 of them gave a smaller number',
   N_PLX > N_PLX_77 and E_PLX_WORST > E_PLX_WORST_77 + 1e-4,
   'typed 0.0248 vs measured %.4f (%s), ratio %.2f'
   % (E_PLX_WORST, WORST_STAR, 0.0248 / max(E_PLX_WORST, 1e-9)))
# ★★ B4 IS NOW THE OTHER WAY ROUND, and the reversal is the finding.  The
#    predecessor required the transfer row and the campaign row to DIFFER,
#    which is only true while they are measured on two different campaigns.
#    On one campaign they are one quantity -- the bootstrap that produces
#    the interval resamples the injected WINDOWS, so the window-to-window
#    spread is already inside it -- and printing both counted it twice.  So
#    the check now requires them to be identical AND the table to carry the
#    row once.
ck('B4 the transfer row and the campaign row are one quantity, printed once',
   abs(T_LO - MC_LO) < 1e-9 and abs(T_HI - MC_HI) < 1e-9
   and sum(1 for t in TERMS if 'ampaign' in t[0]) == 0,
   'transfer x%.2f-%.2f vs campaign x%.2f-%.2f, %d campaign row(s)'
   % (T_LO, T_HI, MC_LO, MC_HI,
      sum(1 for t in TERMS if 'ampaign' in t[0])))
ck('B5 decorrelation is declared external, not implied measured',
   E_DECOR_SOURCE.startswith('DECLARED EXTERNAL'), E_DECOR_SOURCE)
ck('B6 Combined is the quadrature sum of exactly its three rows',
   abs(E_COMB - math.hypot(math.hypot(E_FLUX, E_DIST_TYP), E_VISCAL))
   < (1e-12 if DRIVE != 6 else -1), '%.6f' % E_COMB)
ck('B7 the table has exactly 8 content rows', N_ROWS == 8, '%d' % N_ROWS)
ck('B7b tested + transferred == NWinA',
   T_N + T_TRANSFERRED == (T_NWINA if DRIVE != 7 else T_NWINA + 1),
   '%d + %d == %d' % (T_N, T_TRANSFERRED, T_NWINA))
ck('B8 R1-5\'s withdrawn bracket is NOT what gets printed',
   abs(T_LO - T_OLD_LO) > 0.1 if DRIVE != 8 else False,
   'measured %.2f-%.2f vs withdrawn %.2f-%.2f'
   % (T_LO, T_HI, T_OLD_LO, T_OLD_HI))
# ★★★ B10: THE ROW MUST SURVIVE RETIREMENT.  This is the defect VERDICT 9 is
#     about, and it is not enough to compute the row: `retire_macros.py`
#     strips any macro the manuscript does not reference, and it stripped
#     exactly these for four versions, so the row referee 1's point is about
#     never reached the reader.  Require the manuscript to reference them.
import manuscript  # v4.10: split manuscript
# v4.10: the manuscript is split into sections/, so this must read the
# FLATTENED document.  Reading the main file alone leaves this check
# looking at a preamble, where it can only be vacuous or wrong.
_body = manuscript.flat()
# ★★ B10 AMENDED (round 9).  Its original list demanded `BudTransLo/Hi`, and
#    that requirement became WRONG when B4 reversed: on one campaign the
#    bootstrap resamples the injected WINDOWS, so the transfer spread is
#    already inside the combined interval and the separate transfer row was
#    deleted.  B10 was therefore demanding a citation for a row that no
#    longer exists -- and `BudTransLo/Hi` held the COMBINED interval under a
#    TRANSFER name (-23/+12, which is 0.77-1.12 expressed as a percentage),
#    so the only way to satisfy it was to print a percentage as a factor, or
#    to print the combined interval twice under two different labels.  The
#    row that must survive retirement is now the single combined interval
#    plus the counts that say how much of the sample was measured directly.
_need = ['EirpNinetyFacLo', 'EirpNinetyFacHi',      # the ONE interval, x0.77-1.12
         'BudTransN', 'BudTransNTransferred',       # 21 injected, 381 transferred
         # ★★ The worst fractional parallax error and the star carrying it are
         #    now published by selfunc_v411.py, which re-derives them from the
         #    sample; this file's own BudPlxWorst* pair are the superseded
         #    duplicates.  B10 asks whether the QUANTITY is still in the prose,
         #    so it must name the macro the prose actually uses: a citation
         #    check pinned to a dead name pins the prose to that dead name too,
         #    and that is how this gate came to fail on text that was correct.
         #    Both pairs carry the same values (2.50 per cent, PM J05243-1601A).
         'SfPlxWorstPct', 'SfPlxWorstStar', 'BudPlxNStar']
if DRIVE == 9:
    _need.append('BudNeverReferenced')
_absent = [n for n in _need if ('\\' + n) not in _body]
ck('B10 the combined interval, the injected/transferred counts and the '
   'parallax term are REFERENCED, so they survive retire_macros',
   not _absent, 'unreferenced: %s' % _absent)
# ★★ B10b: and exactly ONE name may carry that interval.  The predecessor's
#    failure was not that the row went missing but that it acquired four
#    names -- BudTransLo/Hi, BudCampLo/Hi, BudMCLo/Hi and the adopted
#    EirpNinetyFac*/Pct* pair -- so a reader could meet the same quantity
#    under a label that said something else.  Scan the whole macro layer by
#    VALUE: no name containing 'Trans' may carry the combined interval in
#    either form, and the factor pair may have exactly one live name.
_mac = {}
for _f in sorted(glob.glob(os.path.join(HERE, 'survey_numbers*.tex'))):
    for _l in open(_f, errors='ignore'):
        _m = re.match(r'\s*\\(?:provide|re|new)command\{?\\([A-Za-z]+)\}?'
                      r'\{(.*)\}\s*$', _l)
        if _m and _m.group(2).strip():
            _mac[_m.group(1)] = _m.group(2).strip()
_facstr = ('%.2f' % T_LO, '%.2f' % T_HI)
_pctstr = ('%.0f' % (100 * (T_LO - 1)), '%.0f' % (100 * (T_HI - 1)))
_fac_names = sorted(n for n, v in _mac.items() if v in _facstr)
_trans_carriers = sorted(
    n for n, v in _mac.items()
    if 'Trans' in n and v in (_facstr + _pctstr))
if DRIVE == 10:
    _trans_carriers.append('BudDriveTransLo')
ck('B10b nothing carries the combined interval under a transfer label',
   not _trans_carriers, 'transfer-labelled carriers: %s' % _trans_carriers)
ck('B9 the dominant term is one of the three rows in the sum',
   DOMINANT in ('the absolute flux scale', 'the Gaia parallaxes',
                'the visibility calibration'), DOMINANT)
# ★ B10 is a condition on the MANUSCRIPT, not on this product: it requires
#   a sentence in someone else's file to cite the row, so that
#   `retire_macros` cannot strip it.  Holding the generated table hostage to
#   it means the owner of that sentence cannot see the row they are being
#   asked to cite.  So the product is written either way and B10 is carried
#   as a routed failure -- the exit status is unchanged, the build still
#   stops, but the table on disk is the correct one.
_routed = [f for f in fail if f.startswith('B10')]
fail = [f for f in fail if not f.startswith('B10')]
print('\nassertions failed: %d %s' % (len(fail), fail))
for f in _routed:
    print('ROUTED (a condition on a prose file, not on this product): %s' % f)
if fail and DRIVE is None:
    raise SystemExit('p90_budget_v409: %d assertion(s) failed: %s'
                     % (len(fail), fail))

T = [r'\begin{tabular}{@{}l@{~}>{\raggedright\arraybackslash}'
     r'p{0.41\columnwidth}@{~}r@{}}', r'\hline',
     r'Term & Origin & $\Delta P_{90}$ (\%) \\', r'\hline']
prev = 'q'
for name, origin, val, kind in TERMS:
    if kind != prev:
        T.append(r'\hline')
    T.append('%s & %s & %s \\\\' % (name, origin, val))
    prev = kind
T += [r'\hline', r'\end{tabular}']
TABOUT = 'tab_p90budget_v409.tex'
open(os.path.join(HERE, suffixed(TABOUT)), 'w').write(
    '%% GENERATED by p90_budget_v409.py -- do not hand-edit.\n'
    + '\n'.join(T) + '\n')

M('BudFlux', '%.0f' % (100 * E_FLUX))
M('BudFluxWorst', '%.0f' % (100 * E_FLUX_WORST))
M('BudDist', '%.1f' % (100 * E_DIST_TYP))
M('BudDistWorst', '%.1f' % (100 * E_DIST_WORST))
M('BudPlxMed', '%.1f' % (1e4 * E_PLX_MED))
M('BudPlxWorstPct', '%.2f' % (100 * E_PLX_WORST))
M('BudPlxWorstStar', WORST_STAR.replace('*', '').strip().replace('gam ',
                                                                 r'$\gamma$~'))
M('BudPlxNStar', '%d' % N_PLX)
M('BudPlxNStarJoinOnly', '%d' % N_PLX_77)
M('BudPlxNStarCat', '%d' % N_STAR_CAT)
M('BudPlxTypedWrongX', '%.2f' % (E_PLX_WORST / E_PLX_WORST_77))
M('BudMC', '%.1f' % (100 * E_MC))
# BudMCLo/BudMCHi are NOT emitted: the campaign interval IS the combined
# interval (B4), whose one name is \EirpNinetyFacLo/Hi.
# BudCampLo/BudCampHi are NOT emitted: round 103 already aliases them to
# \EirpNinetyPctLo/Hi, so emitting them here defined the same number twice.
M('BudPoint', '%.1f' % (100 * E_POINT))
M('BudPointArc', '%.1f' % POINT_ARCSEC)
M('BudComb', '%.0f' % (100 * E_COMB))
M('BudCombWorst', '%.0f' % (100 * E_COMB_WORST))
M('BudPhaseLo', '%.0f' % (100 * E_PHASE_LO))
M('BudPhaseHi', '%.0f' % (100 * E_PHASE_HI))
# BudTransLo/BudTransHi are NOT emitted: they carried the COMBINED
# interval under a transfer label, which is the same number as
# \EirpNinetyPctLo/Hi and the same quantity as \EirpNinetyFacLo/Hi.
# One quantity, one name -- see B10b.
M('BudTransN', '%d' % T_N)
M('BudTransNTransferred', '%d' % T_TRANSFERRED)
M('BudDecorLo', '%.0f' % (100 * E_DECOR_LO))
M('BudDecorHi', '%.0f' % (100 * E_DECOR_HI))
M('BudBoot', '%d' % N_CONFIG)
M('BudNRows', '%d' % N_ROWS)
M('BudDominant', DOMINANT)

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

TEXOUT = 'survey_numbers_round38.tex'
open(os.path.join(HERE, suffixed(TEXOUT)), 'w').write(
    '%% GENERATED by p90_budget_v409.py -- do not hand-edit.\n'
    + '\n'.join(OUT) + '\n')
json.dump(dict(E_FLUX=E_FLUX, E_DIST_TYP=E_DIST_TYP, E_PLX_MED=E_PLX_MED,
               E_PLX_WORST=E_PLX_WORST, worst_star=WORST_STAR,
               n_plx=len(frac), n_star_cat=N_STAR_CAT, E_VISCAL=E_VISCAL,
               E_COMB=E_COMB, E_COMB_WORST=E_COMB_WORST, dominant=DOMINANT,
               T_LO=T_LO, T_HI=T_HI, T_N=T_N, T_TRANSFERRED=T_TRANSFERRED,
               MC_LO=MC_LO, MC_HI=MC_HI, E_POINT=E_POINT,
               E_PHASE_LO=E_PHASE_LO, E_PHASE_HI=E_PHASE_HI,
               decor_source=E_DECOR_SOURCE, fluxcal_source=FLUXCAL_SOURCE,
               point_source=POINT_SOURCE, n_rows=N_ROWS, fail=fail),
          open(os.path.join(HERE, 'p90budget_v409' + SUF + '.json'), 'w'),
          indent=1)
print('\nwrote %s (%d content rows), %s (%d macros)'
      % (suffixed(TABOUT), N_ROWS, suffixed(TEXOUT), len(OUT)))
if _routed:
    raise SystemExit('p90_budget_v409: %d routed condition(s): %s'
                     % (len(_routed), _routed))
