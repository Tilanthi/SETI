#!/usr/bin/env python3
r"""Round 982.  THE COMPLETENESS FACTOR AND THE SMEARING RETENTION, PINNED AS
INVARIANTS: one factor per class is transferred and nothing instrumental is;
the retention enters every published limit with exponent exactly one; and the
interval quoted on the class-average calibration is wider than the last figure
the survey-wide median is printed to, so the precision statement that goes
with it can never be dropped as unnecessary.

★★★ WHAT THE EXISTING GATES CANNOT SEE.
Four generators form the adopted per-window limit independently --
`adopted_e90.py` (the owner), `numbers_v410.py` (C2d), `sens_r11.py` (the
headline) and `scope_r14.py` (S5) -- and each divides by the window's own
intra-integration smearing retention.  The build already checks

  * that the retention is the INTEGRATED delivered channel response and not
    the transform-limited sinc, recomputed from the catalogue on every window
    (`sens_r18.py` X1, driven with the sinc put back);
  * that no released window is left uncorrected (`numbers_v410.py` C2e);
  * that the four routes AGREE row for row (C2d, C9, S5).

None of those can see a correction applied TWICE.  Agreement between routes is
preserved if every route doubles it, and C2e counts rows rather than
applications.  The quantity those clauses leave unpinned is the EXPONENT, so
that is what X1 pins: for every released row,

    EIRP_90 = eirp_nominal_W x p90_mult_adopted
              / (eta_px_retained . eta_smear_adopted . eta_beam_retained)

is required to hold with the smearing retention appearing to the first power
and no other -- measured as

    n = ln(EIRP_90 / base) / ln(1 / eta_smear_adopted),    n == 1

on the rows whose ten stored digits resolve n.  A double application gives
n = 2, an omission n = 0, and a correction applied in the optimistic direction
n = -1.  The clause pins the INVARIANT and not today's retentions: it holds
for any retention the campaign ever measures.

★★ THE TWO ROUTES THAT DO NOT PASS THROUGH THE OWNER, each checked on its own
population rather than on the owner's.  `beam_r17.py` forms the limits of the
one far-off-axis star-band from the nominal power, the class multiplier and
the beam response alone, over a population that includes windows outside the
released catalogue; the stacked limits are measured by injection into the
stack and carry no smearing term at all.  Neither is a defect so long as what
they omit is below the precision they are printed at, and X4 and X5 measure
that instead of assuming it.

★★ AND THE AXIS OF THE CALIBRATION'S COVERAGE THAT NO GENERATOR TESTS.
`resp_r16.py` compares the injected windows with the population on six
properties, none of which is the delivered response FORM.  Online channel
averaging gives a different response shape -- `respint_r20.py` integrates the
averaged windows exactly rather than through its spline for that reason -- so
whether the class-average completeness transfers across that boundary is a
question about the calibration and not about the response integral.  X6
measures it from the campaign's own per-window ninety per cent points.

Output: survey_numbers_round982.tex, senscal_r23b.json.

    python3 senscal_r23b.py
    python3 senscal_r23b.py --drive N      # see DRIVES
    python3 senscal_r23b.py --selftest     # every drive must fire

DRIVES (each must break a NAMED clause, and each has been shown to):
    1  the retention is applied a second time                     -> X1
    2  the retention is not applied at all                        -> X1
    3  the retention is applied in the optimistic direction        -> X1
    4  the resolved set is emptied, so X1 could not fail           -> X2
    5  a window whose correction exceeds the printed precision is
       dropped from the resolved set                               -> X2
    6  the owner and the deposit part company on the stored factor  -> X3
    7  the owner's no-smearing route stops being the deposit
       divided by exactly one retention                            -> X3
    8  a Class A row is given the display-precision multiplier      -> X3
    9  the off-axis route omits a term large enough to show         -> X4
   10  a coarse window carries a smearing term large enough to
       matter at the precision a stacked limit is printed to        -> X5
   11  the injected set loses its channel-averaged windows          -> X6
   12  the native and averaged factors are divorced                 -> X6
   13  the printed median stops being the computed one              -> X7
   14  the calibration interval shrinks inside the last printed
       figure, so the precision clause would be decorative          -> X7
   15  the smearing term moves the printed median                   -> X8
"""
import collections
import csv
import json
import math
import os
import statistics as st
import subprocess
import sys

ROUND = 982
HERE = os.path.dirname(os.path.abspath(__file__))
# The tree this reads.  A copy of the release, never the release itself.
CATDIR = HERE
sys.path.insert(0, CATDIR)

DRIVE = 0
if '--drive' in sys.argv:
    DRIVE = int(sys.argv[sys.argv.index('--drive') + 1])
# The suffix follows the FLAG and not the perturbation, so a driven run can
# never write a path production reads.
SUF = '' if '--drive' not in sys.argv else '_drive%d' % DRIVE
OUT = os.path.join(HERE, 'survey_numbers_round982%s.tex' % SUF)
OUTJSON = os.path.join(HERE, 'senscal_r23b%s.json' % SUF)

DRIVES = {1: 'X1', 2: 'X1', 3: 'X1', 4: 'X2', 5: 'X2', 6: 'X3', 7: 'X3',
          8: 'X3', 9: 'X4', 10: 'X5', 11: 'X6', 12: 'X6', 13: 'X7', 14: 'X7',
          15: 'X8'}

if '--selftest' in sys.argv:
    bad = []
    for d, want in sorted(DRIVES.items()):
        r = subprocess.run([sys.executable, os.path.abspath(__file__),
                            '--drive', str(d)], cwd=HERE,
                           capture_output=True, text=True)
        got = [ln.split()[0] for ln in (r.stdout + r.stderr).splitlines()
               if ' FAIL ' in ln]
        ok = r.returncode != 0 and want in got
        print('drive %-3d must break %-4s -> %s%s'
              % (d, want, 'FIRES' if ok else 'DID NOT FIRE',
                 '' if ok else ' (broke %s, rc=%d)' % (got or 'nothing',
                                                       r.returncode)))
        if not ok:
            bad.append(d)
    for f in os.listdir(HERE):
        if f.startswith(('survey_numbers_round982_drive',
                         'senscal_r23b_drive')):
            os.remove(os.path.join(HERE, f))
    print('senscal_r23b selftest: %d drive(s) failed to fire' % len(bad))
    sys.exit(1 if bad else 0)

FAIL = []


def ck(name, cond, detail=''):
    print('  %-76s %s  %s' % (name[:76], 'PASS' if cond else 'FAIL', detail))
    if not cond:
        FAIL.append(name)


LINES = ['%% GENERATED by senscal_r23b.py (round %d) -- do not hand-edit.\n'
         % ROUND]


def m(name, val):
    # a LaTeX macro name may contain letters only
    assert name.isalpha(), 'macro names carry letters only: %r' % name
    LINES.append('\\newcommand{\\%s}{%s}\n' % (name, val))


import adopted_e90 as ae                                      # noqa: E402
import census_rule                                            # noqa: E402
import respint_r20 as ri                                      # noqa: E402


def F(x):
    return float(x)


def texval(name):
    v = ae._texval(name, CATDIR)
    assert v is not None, 'macro \\%s is not generated anywhere' % name
    return v


def texnum(name):
    return float(texval(name).replace('\\,', '').replace(',', ''))


CAT = list(csv.DictReader(open(os.path.join(
    CATDIR, 'per_target_results_v3.99.csv'))))
SENS = json.load(open(os.path.join(CATDIR, 'sens_r11.json')))
SMEAR = json.load(open(os.path.join(CATDIR, 'smear_r15.json')))
assert CAT and SENS['tags']

# The precision the deposit itself resolves.  `eirp_p90_adopted_W` is written
# to ten significant figures, so an exponent read off a retention that departs
# from unity by less than about 1e-6 is read off the rounding and not off the
# arithmetic.  The cut is a property of the FILE FORMAT and is not tuned to
# any retention.
ETA_RESOLVED = 1e-6
EXPO_TOL = 1e-3
# Two significant figures is what every EIRP in the paper is printed to, so
# half of the last of them -- half a per cent -- is the precision at which an
# omitted term becomes visible on the page.
PRINT_PREC = 0.005

# ======================================================================= 1
print('\n1  the exponent the smearing retention enters a published limit at')


def base_of(r):
    """The limit with the parallax and beam retentions applied and NO smearing
    term: nominal power times the class multiplier, divided by the two other
    retentions exactly as `adopted_e90.per_window` divides by them."""
    e = F(r['eirp_nominal_W']) * F(r['p90_mult_adopted'])
    return e / min(F(r['eta_px_retained']), 1.0) \
             / min(F(r['eta_beam_retained']), 1.0)


EXPO, BIG = [], []
for r in CAT:
    eta = F(r['eta_smear_adopted'])
    e = F(r['eirp_p90_adopted_W'])
    if DRIVE == 1:
        e = e / eta                       # applied twice
    elif DRIVE == 2:
        e = e * eta                       # not applied at all
    elif DRIVE == 3:
        e = e * eta * eta                 # applied the optimistic way
    if 1.0 - eta <= ETA_RESOLVED:
        continue
    n = math.log(e / base_of(r)) / math.log(1.0 / eta)
    row = dict(key=ae.smear_key(r), eta=eta, n=n, cls=r['search_class'],
               star=r['star_name'], penalty=1.0 / eta)
    EXPO.append(row)
    if 1.0 / eta - 1.0 > PRINT_PREC:
        BIG.append(row)
if DRIVE == 4:
    EXPO = []
if DRIVE == 5:
    BIG = BIG + [dict(key='a window that is not in the resolved set',
                      eta=0.5, n=1.0, cls='A', star='-', penalty=2.0)]

_worst = max((abs(x['n'] - 1.0) for x in EXPO), default=None)
ck('X1 the intra-integration smearing retention enters the adopted limit of '
   'every released window with exponent exactly one, so it is neither '
   'applied twice nor left out',
   _worst is not None and _worst < EXPO_TOL,
   ('worst |n-1| = %.2g over %d windows, n in %.6f-%.6f'
    % (_worst, len(EXPO), min(x['n'] for x in EXPO),
       max(x['n'] for x in EXPO))) if EXPO else 'the resolved set is EMPTY')

_missing = [x['key'] for x in BIG if x['key'] not in {y['key'] for y in EXPO}]
ck('X2 and the exponent is read on a set that is not empty and contains every '
   'window whose correction is large enough to show at the precision the '
   'limits are printed to',
   len(EXPO) > 100 and not _missing,
   '%d windows resolved, %d of them corrected by more than %.1f per cent; '
   'unresolved and large: %d' % (len(EXPO), len(BIG), 100 * PRINT_PREC,
                                 len(_missing)))

# ======================================================================= 2
# X3.  THE OWNER'S OWN ROUTE, AND THE ONE PLACE IT READS A DISPLAY STRING.
# `adopted_e90.multiplier_b` takes the Class B factor from the macro layer,
# where it is stored to the two decimals the paper prints; the deposit carries
# the same factor unrounded.  So the owner reproduces the deposit EXACTLY when
# it is handed the deposit's own factor, and departs from it by the rounding of
# that string -- on Class B rows and on no others -- when it is not.  Both
# halves are asserted, so a genuine arithmetic difference cannot hide inside
# the rounding and the rounding cannot grow unnoticed.
print('\n2  the one owner of the arithmetic, against the deposit')
_MULTS = {c: sorted({r['p90_mult_adopted'] for r in CAT
                     if r['search_class'] == c}) for c in ('A', 'B')}
assert all(len(v) == 1 for v in _MULTS.values()), _MULTS
_MB_DEPOSIT = float(_MULTS['B'][0])
_MB_MACRO = ae.multiplier_b(CATDIR)
E_EXACT = ae.per_window(CAT, CATDIR, mult_b=_MB_DEPOSIT)
E_ON = ae.per_window(CAT, CATDIR)
E_OFF = ae.per_window(CAT, CATDIR, mult_b=_MB_DEPOSIT, _smear=False)
_d_dep = max(abs(E_EXACT[id(r)] / F(r['eirp_p90_adopted_W']) - 1.0)
             for r in CAT)
_d_one = max(abs(E_OFF[id(r)] * (1.0 / F(r['eta_smear_adopted']))
                 / E_EXACT[id(r)] - 1.0) for r in CAT)
_round = _MB_MACRO / _MB_DEPOSIT - 1.0
_moved = {r['search_class'] for r in CAT
          if abs(E_ON[id(r)] / E_EXACT[id(r)] - 1.0) > 1e-12}
if DRIVE == 6:
    _d_dep = 0.5
if DRIVE == 7:
    _d_one = 0.5
if DRIVE == 8:
    _moved = {'A', 'B'}
ck('X3 the module every other generator reads reproduces the deposited limit '
   'from the deposited factor, its uncorrected route is that limit with '
   'exactly one retention removed, and the one factor it takes at display '
   'precision moves no other class',
   _d_dep < 2e-6 and _d_one < 1e-9 and _moved == {'B'}
   and abs(_round) < PRINT_PREC,
   'deposit %.2g, one-retention identity %.2g over %d windows; the stored '
   'Class B factor is %+.4f per cent from the deposited one and moves %s'
   % (_d_dep, _d_one, len(CAT), 100 * _round, ','.join(sorted(_moved))))

# ======================================================================= 3
# X4.  THE PUBLISHED LIMITS FORMED OUTSIDE THE OWNER.
# ★ THE POPULATION IS THE ROUTE'S OWN.  `beam_r17.py` reports on one star-band
# over the census windows AND the archival extension's, and only the census
# half is in the released catalogue -- so comparing its printed extrema with
# the catalogue's extrema compares two different populations and says nothing.
# What can be asserted, and is what matters, is that the terms this route does
# not carry -- the parallax retention, the smearing retention, and the display
# rounding of the class factor -- are together below the precision those limits
# are printed at.  The smearing term is computed for every window of the route,
# including the ones with no deposited retention, on the conservative
# integration ceiling the smearing record itself uses where the length is not
# recorded.
print('\n3  the published limits formed outside the owner')
ri.validate(CATDIR)
_EXPORT = json.load(open(os.path.join(
    CATDIR, 'corrected_export_v399.json')))['rows']
_EXTEND = json.load(open(os.path.join(
    CATDIR, 'export_extension.json')))['rows']
OFFAX = [dict(r, _scope='census') for r in _EXPORT
         if census_rule.is_star_band(r)] \
    + [dict(r, _scope='extension') for r in _EXTEND
       if census_rule.is_star_band(r)]
_DTC = SMEAR['dt_ceiling_s']
_Q90 = SMEAR['q90']
_NAVG = sorted({int(r['n_chan_avg']) for r in CAT})
_pen = []
for r in OFFAX:
    d = _Q90 * F(r['drift_max']) * _DTC / F(r['chanw'])
    # the response form is not recorded for the extension rows, so take the
    # worst over every averaging factor the release holds
    _pen.append(max(1.0 / ri.eta(d, n) for n in _NAVG))
# the parallax retention: this star-band carries no annual-parallax record, so
# the term the route omits is unity -- read from the deposit, not assumed
_PX = [F(r['eta_px_retained']) for r in CAT if census_rule.is_star_band(r)]
_omit = max(_pen) - 1.0 + (1.0 - min(_PX)) + abs(_round)
if DRIVE == 9:
    _omit = 0.02
ck('X4 the terms the one printed route outside the owner does not carry are '
   'together below the precision its limits are printed at, over its own '
   'population and not the owner\'s',
   bool(OFFAX) and _omit < PRINT_PREC and len(_PX) > 0,
   'worst omitted term %.4f per cent over %d windows (%d outside the '
   'released catalogue) against a printed precision of %.1f per cent'
   % (100 * _omit, len(OFFAX),
      sum(1 for r in OFFAX if r['_scope'] == 'extension'), 100 * PRINT_PREC))

# ======================================================================= 4
# X5.  THE STACKED LIMITS, which are measured by injection into the stack and
# carry no smearing term.  Every stacked limit the paper prints as a power is a
# coarse-channel one, where a carrier at the searched drift ceiling sweeps a
# negligible part of a channel in one integration.
print('\n4  the stacked limits, which carry no smearing term')
_pen_b = max(1.0 / F(r['eta_smear_adopted'])
             for r in CAT if r['search_class'] == 'B')
_pen_a = max(1.0 / F(r['eta_smear_adopted'])
             for r in CAT if r['search_class'] == 'A')
if DRIVE == 10:
    _pen_b = 1.02
ck('X5 the term omitted from the stacked limits is below the precision they '
   'are printed to on every window that can enter one',
   _pen_b - 1.0 < PRINT_PREC,
   'worst coarse-window penalty x%.7f against a printed precision of %.1f '
   'per cent; worst fine-window penalty x%.4f'
   % (_pen_b, 100 * PRINT_PREC, _pen_a))

# ======================================================================= 5
# X6.  THE RESPONSE FORM, AS A COVERAGE AXIS OF THE CALIBRATION.
print('\n5  the delivered response form, native against channel-averaged')
CAT_A = [r for r in CAT if r['search_class'] == 'A']
_by = collections.defaultdict(list)
for r in CAT_A:
    _by[r['eb']].append(r)
# The campaign's own clean ring maximum identifies the window inside the block,
# exactly as `resp_r16.py` resolves it; a block-only key averages two windows.
# The join is on POSITION and a measured quantity, never on a name, and it is
# required to be one-to-one.
ROW = {}
for g, v in SENS['ring'].items():
    cand = _by.get(g.rsplit('_spw', 1)[0], [])
    if cand:
        ROW[g] = min(cand, key=lambda r: abs(F(r['ctrl_max_snr']) - v))
assert len(ROW) == len(SENS['ring']) and len(
    {(r['eb'], r['flo_GHz'], r['fhi_GHz']) for r in ROW.values()}) == len(ROW)
PERW = SENS['per_window']
_nat = [PERW[g]['trig'] for g in ROW if int(ROW[g]['n_chan_avg']) == 1]
_avg = [PERW[g]['trig'] for g in ROW if int(ROW[g]['n_chan_avg']) > 1]
if DRIVE == 11:
    _avg = []
_pop_nat = sum(1 for r in CAT_A if int(r['n_chan_avg']) == 1)
_pop_avg = len(CAT_A) - _pop_nat
_shift = (abs(st.median(_avg) - st.median(_nat)) if _nat and _avg else None)
if DRIVE == 12:
    _shift = 9.9
# The shift is held to the largest shift any of the six properties
# `resp_r16.py` compares produces, which is a published number and not a
# threshold chosen here: a seventh axis that moved the factor by more than the
# worst of the six would be a transfer the calibration does not support.
_ceil = texnum('RpFacShiftMax')
ck('X6 the injected calibration covers both delivered response forms, and the '
   'factor it measures does not depend on which, by more than the largest '
   'departure the properties already compared produce',
   bool(_nat) and bool(_avg) and _shift is not None and _shift <= _ceil,
   'native %d injected of %d, averaged %d of %d; median factor %.3f against '
   '%.3f, shift %.3f against a ceiling of %.2f'
   % (len(_nat), _pop_nat, len(_avg), _pop_avg,
      st.median(_nat) if _nat else float('nan'),
      st.median(_avg) if _avg else float('nan'),
      _shift if _shift is not None else float('nan'), _ceil))

# ======================================================================= 6
# X7.  THE SURVEY-WIDE MEDIAN AND THE INTERVAL ON IT.
# ★ THE INVARIANT, AND WHY IT IS NOT TODAY'S NUMBER.  The median is printed to
# the two significant figures the paper quotes every EIRP to, and the interval
# that applies to a statistic formed over many windows is the uncertainty on
# the class-average calibration.  The clause requires (a) that the printed
# macro is the rounding of the computed median, and (b) that the interval is
# WIDER than half the last printed figure -- which is what makes a statement
# of the interval necessary beside the number.  If the calibration ever became
# precise enough that the printed digit were safe, (b) would fail and the
# sentence could go; while the calibration stands where it does, the number
# cannot be printed bare.
print('\n6  the survey-wide median, and the precision the calibration '
      'supports')
E_SYS = ae.per_window(CAT, CATDIR, mult_b=_MB_DEPOSIT)
_best = {}
for r in CAT:
    # ★ the limit population: a window wholly inside the attribution mask
    # constrains nothing (Sec. \ref{sec:lines}) and is not a best window
    if r['search_class'] != 'A' or not ae.limit_eligible(r, CATDIR):
        continue
    k = r['system_id']
    _best[k] = min(_best.get(k, float('inf')), E_SYS[id(r)])
_med = st.median(sorted(_best.values()))
_BUD = SENS['budget']
_flo, _fhi = _BUD['factor_lo'], _BUD['factor_hi']


def sci(x, nd=1):
    e = int(math.floor(math.log10(x)))
    return r'%.*f\times10^{%d}' % (nd, x / 10.0 ** e, e)


_printed = sci(_med)
if DRIVE == 13:
    _printed = sci(_med * 1.3)
# half the last printed figure, as a fraction of the value
_halfdigit = 0.5 * 10.0 ** (int(math.floor(math.log10(_med))) - 1) / _med
_width = min(1.0 - _flo, _fhi - 1.0)
if DRIVE == 14:
    _width = 0.5 * _halfdigit
ck('X7 the survey-wide median is the computed one at the precision the paper '
   'quotes, and the interval on the class-average calibration is wider than '
   'half its last printed figure, so the number cannot stand without it',
   _printed == texval('EirpNinetySysMedA') and _width > _halfdigit
   # ★ the median is over the systems that carry a limit (\NSysALim), not
   #   over every system the search covers (\NSysClassA); the two differ by
   #   the systems the attribution mask leaves nothing of
   and len(_best) == int(texnum('NSysALim')),
   'median %.4e over %d systems, printed %s against %s; interval x%.4f-x%.4f '
   'is +-%.1f per cent against a half-figure of %.1f per cent'
   % (_med, len(_best), _printed, texval('EirpNinetySysMedA'), _flo, _fhi,
      100 * _width, 100 * _halfdigit))

# ======================================================================= 7
# X8.  AND THE SMEARING TERM DOES NOT REACH THE SURVEY-WIDE MEDIAN.
# The windows the correction moves are few and deep; the statistic the paper
# leads with is a median over systems, and the clause pins that the term is
# below the precision that median is printed to -- the same invariant as X5
# and X4, applied to the headline.  If the campaign ever searched a
# configuration where it mattered, this fails and the paper has to say so.
print('\n7  and what the smearing term does to the printed median')
E_NOSM = ae.per_window(CAT, CATDIR, mult_b=_MB_DEPOSIT, _smear=False)
_best_nosm = {}
for r in CAT:
    # ★ the limit population: a window wholly inside the attribution mask
    # constrains nothing (Sec. \ref{sec:lines}) and is not a best window
    if r['search_class'] != 'A' or not ae.limit_eligible(r, CATDIR):
        continue
    k = r['system_id']
    _best_nosm[k] = min(_best_nosm.get(k, float('inf')), E_NOSM[id(r)])
_med_nosm = st.median(sorted(_best_nosm.values()))
_medmove = _med / _med_nosm - 1.0
if DRIVE == 15:
    _medmove = 0.02
_bestids = set()
for k, v in _best.items():
    for r in CAT:
        if r['search_class'] == 'A' and ae.limit_eligible(r, CATDIR) \
                and r['system_id'] == k and E_SYS[id(r)] == v:
            _bestids.add(id(r))
_bigbest = sorted({x['star'] for x in BIG
                   if any(ae.smear_key(r) == x['key'] and id(r) in _bestids
                          for r in CAT)})
ck('X8 the smearing term moves the printed survey-wide median by less than '
   'the precision it is printed to, so the windows it does move are '
   'individual limits and not the headline',
   abs(_medmove) < PRINT_PREC and _medmove >= 0.0,
   'median moves x%.6f; %d windows are corrected by more than %.1f per cent '
   'and %d of them is a system\'s best window (%s)'
   % (1.0 + _medmove, len(BIG), 100 * PRINT_PREC,
      len(_bigbest), ', '.join(_bigbest) or 'none'))

# ======================================================================= 8
# MACROS.
m('TfInjNat', '%d' % len(_nat))
m('TfInjAvg', '%d' % len(_avg))
m('TfPopNat', '%d' % _pop_nat)
m('TfPopAvg', '%d' % _pop_avg)
m('TfFacNat', '%.2f' % st.median(_nat))
m('TfFacAvg', '%.2f' % st.median(_avg))
m('TfFacShift', '%.2f' % _shift)
m('TfExpoNWin', '%d' % len(EXPO))
m('TfMedCalLo', sci(_med * _flo))
m('TfMedCalHi', sci(_med * _fhi))

json.dump(dict(generated_by='senscal_r23b.py', round=ROUND, drive=DRIVE,
               exponent=dict(n_resolved=len(EXPO), n_large=len(BIG),
                             eta_resolved=ETA_RESOLVED, tol=EXPO_TOL,
                             worst_abs_dev=_worst, windows=EXPO),
               routes=dict(deposit_worst=_d_dep, one_retention_worst=_d_one,
                           mult_b_deposit=_MB_DEPOSIT,
                           mult_b_macro=_MB_MACRO, rounding=_round,
                           classes_moved=sorted(_moved)),
               offaxis=dict(n_window=len(OFFAX),
                            n_extension=sum(1 for r in OFFAX
                                            if r['_scope'] == 'extension'),
                            worst_smear_penalty=max(_pen),
                            worst_omitted=_omit,
                            dt_ceiling_s=_DTC),
               stacked=dict(worst_coarse_penalty=_pen_b,
                            worst_fine_penalty=_pen_a,
                            printed_precision=PRINT_PREC),
               response_form=dict(n_inj_native=len(_nat),
                                  n_inj_averaged=len(_avg),
                                  n_pop_native=_pop_nat,
                                  n_pop_averaged=_pop_avg,
                                  factor_native=st.median(_nat) if _nat
                                  else None,
                                  factor_averaged=st.median(_avg) if _avg
                                  else None,
                                  shift=_shift, ceiling=_ceil),
               median=dict(value_W=_med, n_system=len(_best),
                           printed=_printed, factor_lo=_flo, factor_hi=_fhi,
                           interval_W=[_med * _flo, _med * _fhi],
                           half_last_figure=_halfdigit,
                           interval_half_width=_width,
                           move_from_smearing=_medmove,
                           best_windows_corrected=_bigbest),
               failures=FAIL), open(OUTJSON, 'w'), indent=1)

if FAIL:
    print('\nsenscal_r23b: %d FAILURE(S)' % len(FAIL))
    for f in FAIL:
        print('  - %s' % f)
    sys.exit(1)
open(OUT, 'w').writelines(LINES)
print('\nsenscal_r23b: %d macros -> %s' % (len(LINES) - 1,
                                           os.path.basename(OUT)))
