#!/usr/bin/env python3
r"""Round 260: ONE POPULATION FOR THE CHANCE COMPARISON, MEASURED EXCHANGE-
ABILITY, AND THE TWO KINDS OF HOUR.

Four things, all of them asked for, none of them a new statistical device.

(1) ONE POPULATION, ONE OBSERVED COUNT (R1-6, R2-9).  The paper compared an
    expectation summed over the Class A windows that carry a fitted cell count
    with an observed number taken from a different set, and then printed three
    counts -- the released catalogue's column, its cell-counted subset, and the
    adopted ledger -- and left the reader to reconcile them.  Here the two
    sides are defined over ONE set of windows, the \NWinA{} Class A windows of
    the primary census, with ONE condition on both sides: a cell at the stellar
    position reaching the trigger that the line mask does not attribute.

      expected   the empirical exceedance rate of the window's own control
                 positions, summed window by window.  No cell count, no
                 Gaussian tail, no grid-correlation factor: each window
                 contributes the fraction of its own control ensemble that
                 reaches the trigger, which is the probability a position in
                 that field does so.  Times the fraction of the searched band
                 the mask does not occupy.

      observed   the adopted ledger's unattributed Class A crossings whose
                 frequency falls inside one of those same windows, as a SET.
                 Asserted against the two arithmetic routes to it, so a
                 remembered integer cannot stand in for the set.

    ★ The repair comes off both sides.  Where the adopted statistic comes from
    the re-extraction, the expectation uses that extraction's own control
    vector; the same windows, the same positions, the same threshold.  The
    crossings the repair takes below the trigger leave the observed side
    because they are not crossings, not because they were removed by hand.

(2) EXCHANGEABILITY, MEASURED IN THE QUANTITY THAT IS USED (R2-8).  The
    expectation assumes a star behaves like a control position in its own
    field.  That was previously corrected by a factor measured as a rate of
    RANKING FIRST among controls, which is a different quantity from a rate of
    exceeding the trigger.  It is measured here directly: in the reserved
    blocks -- disjoint from the census, asserted -- the stars reach the trigger
    in \StHoObs{} of \StHoNFine{} fine-channel windows where their own control
    positions predict \StHoExp.  The ratio is \StHoRatio.  No departure, to the
    accuracy eight events allow, so none is applied.

(3) THE CELL BUDGET IS A CROSS-CHECK AND NOT THE BASIS (R2-16).  Two
    incompatible over-counts were in print: a window's fitted independent-cell
    count, \StNindFrac{} of its searched cells, and an analytic smoothing-plus-
    drift factor leaving only \StGridFrac{} of them.  The control ensembles
    settle it -- the maxima agree with the raw searched count treated as
    independent and Gaussian -- and nothing depends on the answer, because the
    expectation of (1) is summed from the control rates themselves.  The
    cell-count route is published as what it is: a cross-check, agreeing to
    \StModelAgreePct{} per cent.

(4) THE TWO KINDS OF HOUR (R2-26).  The block ledger's hours are summed over
    WINDOWS, so a block delivering four spectral windows at once contributes
    its on-source time four times.  That is why the two class rows sum exactly
    to the census total while most blocks carry both classes.  The telescope
    on-source time is a different and smaller number, \StTelHours{} h, and the
    per-class telescope hours overlap rather than add.  Both are published and
    named for what they are.

Inputs, all read and none remembered: `per_target_results_v3.99.csv`,
`corrected_export_v399.json`, `r8inputs/v409/fieldfix_v409.json`,
`holdout_export_v381.json`, `ledger.json`, `repaired_v409.csv`, and the macro
layer for the counts other generators publish.

Seven assertions, seven drives.  `--drive 0` means "no perturbation, but do not
write a path production reads".

    python3 stats_v413.py [--drive N]
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
from scipy.stats import norm, chi2

HERE = os.path.dirname(os.path.abspath(__file__))
ROUND = 260
TRIG = 5.0

DRIVE = None
if '--drive' in sys.argv:
    DRIVE = int(sys.argv[sys.argv.index('--drive') + 1])

# ★ The production name is a literal and only the drive branch is built by
#   format, so `roundcollide` can resolve the claim on round 260.
OUT_TEX = os.path.join(HERE, 'survey_numbers_round260.tex' if DRIVE is None
                       else 'survey_numbers_round260_drive%d.tex' % DRIVE)
OUT_JSON = os.path.join(HERE, 'stats_v413%s.json'
                        % ('' if DRIVE is None else '_drive%d' % DRIVE))

OUT = []
fail = []

#: counts small enough to read as words do, at the head of a sentence.
_WORDS = ['no', 'one', 'two', 'three', 'four', 'five', 'six', 'seven',
          'eight', 'nine', 'ten']


def m(name, val):
    assert name.isalpha(), 'a macro name may contain letters only: %r' % name
    assert not any(x.startswith('\\newcommand{\\%s}' % name) for x in OUT), name
    OUT.append('\\newcommand{\\%s}{%s}' % (name, val))


def ck(label, cond, detail=''):
    print('  %-74s %s  %s' % (label[:74], 'PASS' if cond else 'FAIL', detail))
    if not cond:
        fail.append(label)


def texval(name):
    """The value the macro layer publishes, in \\input order so a later
    \\renewcommand wins."""
    main = glob.glob(os.path.join(HERE, 'technosignatures_*.tex'))
    order = []
    if len(main) == 1:
        for ln in open(main[0], errors='ignore'):
            mm = re.match(r'\s*\\input\{(survey_numbers[A-Za-z0-9_]*)\}', ln)
            if mm:
                order.append(mm.group(1) + '.tex')
    val = None
    for fn in order:
        p = os.path.join(HERE, fn)
        if not os.path.exists(p):
            continue
        for ln in open(p, errors='ignore'):
            for nm, vv in re.findall(
                    r'\\(?:providecommand|renewcommand|newcommand)'
                    r'\{?\\([A-Za-z]+)\}?\{([^{}]*)\}', ln):
                if nm == name and vv.strip():
                    val = vv.strip()
    assert val is not None, 'no generator publishes \\%s' % name
    return val


# =====================================================================
# inputs
# =====================================================================
CAT = list(csv.DictReader(open(os.path.join(
    HERE, 'per_target_results_v3.99.csv'))))
EXP = json.load(open(os.path.join(HERE, 'corrected_export_v399.json')))['rows']
FFX = json.load(open(os.path.join(HERE, 'r8inputs/v409/fieldfix_v409.json')))
HOL = json.load(open(os.path.join(HERE, 'holdout_export_v381.json')))['rows']
LED = json.load(open(os.path.join(HERE, 'ledger.json')))
REPAIR = list(csv.DictReader(open(os.path.join(HERE, 'repaired_v409.csv'))))
LROWS, LSUM = LED['rows'], LED['summary']


# --------------------------------------------------------------- the join
# ★ A window is identified by its block and its two edges, and the edges are
#   taken as min/max of the pair: a descending spectral window is written
#   with flo above fhi in one product and below it in another, and keying on
#   the stored order loses half the survey silently (it lost 1240 of 1651 the
#   first time this join was written).  The join is then VALIDATED, not
#   trusted: every matched row's control maximum must equal the catalogue's
#   own published one.
def wkey(eb, a, b):
    a, b = float(a), float(b)
    if DRIVE == 1:
        return (eb, round(a, 3), round(b, 3))      # the stored order
    return (eb, round(min(a, b), 3), round(max(a, b), 3))


def skey(s):
    return re.sub(r'\s+', '', s or '').lower()


BYWIN = collections.defaultdict(list)
for r in EXP:
    BYWIN[wkey(r['eb'], r['flo'], r['fhi'])].append(r)

FFWIN = collections.defaultdict(list)
for r in FFX:
    FFWIN[wkey(r['eb'], r['flo'], r['fhi'])].append(r)


def _pick(cands, row, namekey, maxkey):
    """One (star, window) search unit out of the window's rows.  Several
    components of one multiple share a window; they are distinguished by name
    where the names agree between products and by the published control
    maximum where they do not."""
    same = [x for x in cands if skey(x.get(namekey)) == skey(row['star_name'])]
    pool = same or cands
    if len(pool) == 1:
        return pool[0]
    return min(pool, key=lambda x: abs(float(x[maxkey])
                                       - float(row['ctrl_max_snr'] or 0)))


JOIN, NOVEC, HOWJOIN = {}, [], collections.Counter()
for i, r in enumerate(CAT):
    cands = BYWIN.get(wkey(r['eb'], r['flo_GHz'], r['fhi_GHz']), [])
    if not cands:
        NOVEC.append(r)
        HOWJOIN['no control vector'] += 1
        continue
    p = _pick(cands, r, 'star_name', 'ctrl_max')
    if not (p.get('ctrl_all') or []):
        NOVEC.append(r)
        HOWJOIN['no control vector'] += 1
        continue
    JOIN[i] = p
    HOWJOIN['matched'] += 1

MISMATCH = [i for i, p in JOIN.items()
            if CAT[i]['ctrl_max_snr']
            and abs(float(p['ctrl_max']) - float(CAT[i]['ctrl_max_snr'])) > 1e-3]

# ------------------------------------------- the repaired control vectors
# Where the adopted statistic comes from the re-extraction, the expectation
# must use that extraction's own controls.  Same window, same ring, same
# threshold -- otherwise the repair has been applied to one side only, which
# is the defect this round exists to remove.
REPJOIN = {}
for i, r in enumerate(CAT):
    cands = FFWIN.get(wkey(r['eb'], r['flo_GHz'], r['fhi_GHz']), [])
    if not cands:
        continue
    q = _pick(cands, r, 'star', 'ctrl_max')
    if q.get('ctrl_all'):
        REPJOIN[i] = q

if DRIVE == 6:
    # the repair applied to one side only: drop the re-extracted controls of a
    # window whose own adopted statistic comes from that re-extraction.
    for _r in LROWS:
        if _r.get('tstar_source') != 'repaired':
            continue
        for _i, _c in enumerate(CAT):
            _lo, _hi = float(_c['flo_GHz']), float(_c['fhi_GHz'])
            if (_c['eb'] == _r['eb']
                    and min(_lo, _hi) - 1e-6 <= _r['freq'] <= max(_lo, _hi) + 1e-6
                    and _i in REPJOIN):
                REPJOIN.pop(_i)
                break
        else:
            continue
        break


def pexc_emp(i, repaired=True):
    """The fraction of a window's own control positions that reach the
    trigger: the probability a position in that field does so."""
    src = REPJOIN.get(i) if (repaired and i in REPJOIN) else JOIN.get(i)
    if src is None:
        return None
    v = src['ctrl_all']
    return sum(1 for x in v if x >= TRIG) / float(len(v))


IA = [i for i, r in enumerate(CAT) if r['search_class'] == 'A']
IB = [i for i, r in enumerate(CAT) if r['search_class'] == 'B']
ICOV = [i for i in IA if CAT[i]['n_ind_cells'] != '']

E_TRIG_A = sum(p for p in (pexc_emp(i) for i in IA) if p is not None)
E_TRIG_A_REL = sum(p for p in (pexc_emp(i, False) for i in IA)
                   if p is not None)
E_TRIG_B = sum(p for p in (pexc_emp(i) for i in IB) if p is not None)

#: The fraction of the trigger-level exceedances that the line mask would
#: attribute.  ★ This is the PER-WINDOW occupancy of the attribution windows
#: (round 300), not the mask's share of the searched band.  The windows are
#: line-tuned: a crossing lands on the channel grid of a window chosen to
#: contain a transition, so it falls inside an attribution window about twice
#: as often as a band-average would predict.  Using the per-window figure
#: LOWERS the expectation -- it is the direction that runs against the null,
#: and `census_r12.py` C5 asserts that direction so the band average cannot
#: come back as the flattering choice.  The band average is kept beside it in
#: the record, because the difference between the two is the referee's point.
OCC = float(texval('CxOccPerWinPct')) / 100.0
OCC_BAND = float(texval('LgMaskOccPct')) / 100.0
if DRIVE == 7:                      # the flattering factor comes back
    OCC = OCC_BAND
assert 0.0 < OCC < 1.0, OCC
assert OCC >= OCC_BAND, (OCC, OCC_BAND)
E_CHANCE = E_TRIG_A * (1.0 - OCC)
E_CHANCE_BAND = E_TRIG_A * (1.0 - OCC_BAND)

# ------------------------------------- the cell-count route, as a cross-check
def pexc_cells(i, nkey='n_ind_cells'):
    r = CAT[i]
    if r[nkey] == '':
        return None
    sw = 0.5 * (float(r['scale_route_a']) + float(r['scale_route_b']))
    return -math.expm1(float(r[nkey]) * norm.logcdf(TRIG / sw))


E_MODEL = sum(p for p in (pexc_cells(i) for i in ICOV) if p is not None)
E_EMP_COV = sum(p for p in (pexc_emp(i) for i in ICOV) if p is not None)
if DRIVE == 4:
    E_MODEL *= 1.4                             # the routes stop agreeing
AGREE_PCT = 100.0 * abs(E_MODEL - E_EMP_COV) / E_EMP_COV

NS = np.array([float(CAT[i]['n_search_cells']) for i in ICOV])
NI = np.array([float(CAT[i]['n_ind_cells']) for i in ICOV])
NIND_FRAC = float(np.median(NI / NS))
GRID_FRAC = 1.0 / float(texval('FaOverCount'))

# =====================================================================
# the observed side, over the same windows and under the same condition
# =====================================================================
WINSPAN = collections.defaultdict(list)
for i, r in enumerate(CAT):
    lo, hi = float(r['flo_GHz']), float(r['fhi_GHz'])
    WINSPAN[r['eb']].append((min(lo, hi), max(lo, hi), r['search_class'], i))


def window_of(eb, freq):
    """The released window a crossing falls in, by position in frequency and
    never by a name.  Returns the catalogue row index or None when the block
    is not in the released catalogue at all."""
    hit = [i for lo, hi, _c, i in WINSPAN.get(eb, [])
           if lo - 1e-6 <= freq <= hi + 1e-6]
    return hit[0] if hit else None


UN_LED = [r for r in LROWS if not r['attributed']]
INSIDE, OUTSIDE = [], []
for r in UN_LED:
    i = window_of(r['eb'], r['freq'])
    if i is None:
        OUTSIDE.append(r)
    elif CAT[i]['search_class'] == 'A':
        INSIDE.append(r)

if DRIVE == 2:
    INSIDE = INSIDE[:-1]                       # the two routes stop agreeing

N_OBS = len(INSIDE)
OUT_STARS = sorted({r['display'].replace('~', ' ') for r in OUTSIDE})

# the two arithmetic routes to the same count, from the released column
RELA = [r for r in CAT if r['crossing'] == 'True' and r['search_class'] == 'A']
REL_UN = [r for r in RELA
          if r['disposition_computed'].strip() == 'unattributed']
LKEY = {(r['eb'], round(r['freq'], 4)) for r in LROWS}
LATTR = {(r['eb'], round(r['freq'], 4)) for r in LROWS if r['attributed']}
FELL = [r for r in REL_UN
        if (r['eb'], round(float(r['f_cross_GHz']), 4)) not in LKEY]
NOWATTR = [r for r in REL_UN
           if (r['eb'], round(float(r['f_cross_GHz']), 4)) in LATTR]
ROUTE_REL = len(REL_UN) - len(FELL) - len(NOWATTR)
ROUTE_LED = int(texval('ChnUnattrA')) - len(OUTSIDE)

# --------------------------------------------------------------- the repair
DT = [float(r['star_peak_snr_repaired']) - float(r['star_peak_snr_released'])
      for r in REPAIR]
ONS = [float(r['on_source_s_repaired']) / float(r['on_source_s_released'])
       for r in REPAIR if float(r['on_source_s_released']) > 0]
N_REP_ADOPTED = sum(1 for r in LROWS if r.get('tstar_source') == 'repaired')

# =====================================================================
# exchangeability, measured on the reserved blocks
# =====================================================================
HO_EB = {r['eb'] for r in HOL}
CAT_EB = {r['eb'] for r in CAT}
if DRIVE == 3:
    HO_EB = HO_EB | {sorted(CAT_EB)[0]}        # the calibration goes circular

HO_FINE = [r for r in HOL if r['res'].startswith('fine')]
HO_COARSE = [r for r in HOL if not r['res'].startswith('fine')]


def ho_rate(rows):
    obs = [r for r in rows if r.get('star_snr') is not None
           and float(r['star_snr']) >= TRIG]
    exp = sum(sum(1 for x in r['ctrl_all'] if x >= TRIG) / float(len(r['ctrl_all']))
              for r in rows if r.get('ctrl_all'))
    return len(obs), exp, obs


HO_OBS, HO_EXP, HO_HITS = ho_rate(HO_FINE)
HO_OBS_C, HO_EXP_C, _ = ho_rate(HO_COARSE)
HO_RATIO = HO_OBS / HO_EXP

# The interval is Poisson on the events the calibration rests on, clustered
# over the reserved blocks: the resampling and the Poisson form agree here
# because the exceedances fall in distinct blocks, which is reported.
_rng = np.random.default_rng(260)
_ebs = sorted({r['eb'] for r in HO_FINE})
_by = collections.defaultdict(list)
for r in HO_FINE:
    _by[r['eb']].append(r)
_bo = np.array([sum(1 for r in _by[e] if float(r['star_snr']) >= TRIG)
                for e in _ebs], float)
_be = np.array([ho_rate(_by[e])[1] for e in _ebs], float)
_pk = _rng.integers(0, len(_ebs), size=(20000, len(_ebs)))
_so, _se = _bo[_pk].sum(axis=1), _be[_pk].sum(axis=1)
_boot = list(_so[_se > 0] / _se[_se > 0])
HO_LO, HO_HI = (float(np.percentile(_boot, 2.5)),
                float(np.percentile(_boot, 97.5)))
HO_ACC_PCT = 100.0 / math.sqrt(HO_OBS)
HO_NBLOCK_HIT = len({r['eb'] for r in HO_HITS})
_pl = chi2.ppf(0.025, 2 * HO_OBS) / 2.0
_ph = chi2.ppf(0.975, 2 * (HO_OBS + 1)) / 2.0

# =====================================================================
# the two kinds of hour
# =====================================================================
def win_hours(rows):
    return sum(float(r['on_source_s'] or 0) for r in rows) / 3600.0


def tel_hours(rows):
    by = collections.defaultdict(float)
    for r in rows:
        by[r['eb']] = max(by[r['eb']], float(r['on_source_s'] or 0))
    return sum(by.values()) / 3600.0


ROWS_A = [CAT[i] for i in IA]
ROWS_B = [CAT[i] for i in IB]
H_WIN, H_WIN_A, H_WIN_B = win_hours(CAT), win_hours(ROWS_A), win_hours(ROWS_B)
H_TEL, H_TEL_A, H_TEL_B = tel_hours(CAT), tel_hours(ROWS_A), tel_hours(ROWS_B)
if DRIVE == 5:
    H_TEL = H_WIN                              # the two kinds stop differing

# ★ The quality-passing survey, both classes: the comparison the whole
#   crossing population supports, and the reason the Class A statement is
#   also the survey statement.  The coarse class contributes almost nothing
#   because almost no coarse window has a control above the trigger.
E_SURV = (E_TRIG_A + sum(p for p in (pexc_emp(i) for i in IB
                                     if CAT[i]['eb'] != texval('BqFailBlock')
                                     .replace('\\_', '_'))
                         if p is not None)) * (1.0 - OCC)

# the flagged block, reported separately rather than pooled
FLAG_EB = texval('BqFailBlock').replace('\\_', '_')
IFLAG = [i for i, r in enumerate(CAT) if r['eb'] == FLAG_EB]
E_FLAG = sum(p for p in (pexc_emp(i) for i in IFLAG) if p is not None)
IBC = [i for i in IB if CAT[i]['eb'] != FLAG_EB]
E_B_CLEAN = sum(p for p in (pexc_emp(i) for i in IBC) if p is not None)
OBS_B_CLEAN = sum(1 for i in IBC if CAT[i]['crossing'] == 'True')

# what the comparison can and cannot register: a Poisson scatter on the
# expectation, and the added population that would clear two of them.
POIS = math.sqrt(E_CHANCE)
FLOOR = 2.0 * POIS

# =====================================================================
# what was found
# =====================================================================
print('stats_v413: round %d%s' % (ROUND, '' if DRIVE is None
                                  else '  (drive %d)' % DRIVE))
print('  join: %s; %d control-max mismatches; no vector: %s'
      % (dict(HOWJOIN), len(MISMATCH),
         ', '.join('%s %s' % (r['star_name'], r['eb']) for r in NOVEC)))
print('  ONE POPULATION: %d Class A windows' % len(IA))
print('    expected  %.2f trigger by chance (control rates; %.2f on the '
      'released extraction alone) x (1 - %.3f per-window attribution '
      'occupancy) = %.2f   [band-average occupancy %.3f would have given '
      '%.2f]'
      % (E_TRIG_A, E_TRIG_A_REL, OCC, E_CHANCE, OCC_BAND, E_CHANCE_BAND))
print('    observed  %d unattributed Class A crossings inside those windows; '
      'arithmetic routes %d (released column) and %d (ledger)'
      % (N_OBS, ROUTE_REL, ROUTE_LED))
print('    outside   %d, all %s' % (len(OUTSIDE), ' / '.join(OUT_STARS)))
print('    ledger    %d unattributed Class A in all' % len(UN_LED))
print('  cross-check: cell-count route %.2f against %.2f empirical over the '
      'same %d windows, %.1f per cent' % (E_MODEL, E_EMP_COV, len(ICOV),
                                          AGREE_PCT))
print('    fitted independent cells %.3f of the searched count; the grid '
      'correlation estimate %.3f' % (NIND_FRAC, GRID_FRAC))
print('  exchangeability on the reserved blocks (%d, census overlap %d):'
      % (len(HO_EB), len(HO_EB & CAT_EB)))
print('    fine   %d of %d windows against %.2f predicted -> %.3f '
      '(%.2f-%.2f resampled, Poisson %.2f-%.2f), hits in %d distinct blocks'
      % (HO_OBS, len(HO_FINE), HO_EXP, HO_RATIO, HO_LO, HO_HI,
         _pl / HO_EXP, _ph / HO_EXP, HO_NBLOCK_HIT))
print('    coarse %d of %d windows against %.2f predicted'
      % (HO_OBS_C, len(HO_COARSE), HO_EXP_C))
print('  the repair: %d windows re-extracted, on-source x%.2f median, '
      'dT median %+.3f signed / %.3f absolute; adopted on %d ledger rows, '
      '%d crossings fell, %d attributed by the rebuilt mask'
      % (len(REPAIR), float(np.median(ONS)), float(np.median(DT)),
         float(np.median(np.abs(DT))), N_REP_ADOPTED, len(FELL),
         len(NOWATTR)))
print('  hours: window-hours %.1f (A %.1f + B %.1f); telescope on-source '
      '%.1f h (A %.1f, B %.1f, which overlap)'
      % (H_WIN, H_WIN_A, H_WIN_B, H_TEL, H_TEL_A, H_TEL_B))
print('  flagged block %s: %d windows, %.2f expected, %d crossings; the other '
      '%d Class B windows expect %.2f and hold %d'
      % (FLAG_EB, len(IFLAG), E_FLAG,
         sum(1 for i in IFLAG if CAT[i]['crossing'] == 'True'),
         len(IBC), E_B_CLEAN, OBS_B_CLEAN))
print('  discriminating power: Poisson scatter %.1f on the expectation, so an '
      'added population below about %.0f cannot register' % (POIS, FLOOR))

# =====================================================================
# assertions
# =====================================================================
print('\nassertions')
ck('S1 THE JOIN IS VALIDATED AND NOT TRUSTED: every catalogue row but the '
   'named one carries a control vector, and every matched row reproduces the '
   "catalogue's own published control maximum",
   len(JOIN) == len(CAT) - len(NOVEC) and len(NOVEC) <= 1
   and not MISMATCH,
   '%d joined, %d without a vector, %d control maxima disagree'
   % (len(JOIN), len(NOVEC), len(MISMATCH)))

ck('S2 ONE POPULATION: the observed count is a SET -- the ledger\'s '
   'unattributed Class A crossings inside the released Class A windows -- '
   'and the two arithmetic routes to it agree with the set',
   N_OBS == ROUTE_REL == ROUTE_LED
   and N_OBS + len(OUTSIDE) == int(texval('ChnUnattrA'))
   and len(IA) == int(texval('NWinA')),
   'set %d, released route %d, published-ledger route %d; %d inside + %d '
   'outside against the published %s, over %d windows against the published '
   '%s' % (N_OBS, ROUTE_REL, ROUTE_LED, N_OBS, len(OUTSIDE),
           texval('ChnUnattrA'), len(IA), texval('NWinA')))

ck('S2b THE MASK FACTOR IS THE PER-WINDOW OCCUPANCY AND IT RUNS AGAINST THE '
   'NULL: the attribution windows take a larger share of a line-tuned '
   "window's own grid than of the searched band, so the expectation FALLS",
   OCC > OCC_BAND and E_CHANCE < E_CHANCE_BAND
   and E_CHANCE > float(N_OBS),
   'per window %.3f against band average %.3f; expectation %.2f against '
   '%.2f, observed %d' % (OCC, OCC_BAND, E_CHANCE, E_CHANCE_BAND, N_OBS))

ck('S3 THE CALIBRATION IS NOT CIRCULAR: no reserved block appears in the '
   'primary census, so the measured exchangeability is out of sample',
   not (HO_EB & CAT_EB) and len(HO_EB) > 50,
   '%d reserved blocks, %d of them in the census' % (len(HO_EB),
                                                     len(HO_EB & CAT_EB)))

ck('S4 THREE ROUTES TO ONE EXPECTATION AGREE: the control rates, the fitted '
   'cell count, and the raw searched count under a Gaussian tail',
   AGREE_PCT < 10.0
   and abs(float(texval('CtrlMaxRatioMed')) - 1.0) < 0.05,
   'cell-count route differs by %.1f per cent; control maxima sit at %s of '
   'the raw-count prediction' % (AGREE_PCT, texval('CtrlMaxRatioMed')))

ck('S5 THE TWO KINDS OF HOUR ARE DISTINCT AND EACH BEHAVES AS ITS DEFINITION '
   'REQUIRES: window-hours partition the census, telescope hours overlap it '
   'and are smaller',
   abs(H_WIN_A + H_WIN_B - H_WIN) < 1e-6 and H_TEL < H_WIN
   and H_TEL_A + H_TEL_B > H_TEL,
   '%.1f + %.1f == %.1f window-hours; telescope %.1f h with %.1f + %.1f per '
   'class' % (H_WIN_A, H_WIN_B, H_WIN, H_TEL, H_TEL_A, H_TEL_B))

REPWIN = [window_of(r['eb'], r['freq']) for r in LROWS
          if r.get('tstar_source') == 'repaired']
REPWIN = [i for i in REPWIN if i is not None]
ck('S6 THE REPAIR COMES OFF BOTH SIDES: every window whose adopted statistic '
   'is the re-extracted one contributes its re-extracted control vector to '
   'the expectation, and the expectation demonstrably changes because of it',
   all(i in REPJOIN for i in REPWIN) and len(REPWIN) >= 1
   and abs(E_TRIG_A - E_TRIG_A_REL) > 0.01,
   '%d of %d such windows joined; the expectation moves %.2f -> %.2f when '
   'the re-extracted controls are used'
   % (sum(1 for i in REPWIN if i in REPJOIN), len(REPWIN),
      E_TRIG_A_REL, E_TRIG_A))

# =====================================================================
# macros
# =====================================================================
m('StExpTrig', '%.1f' % E_TRIG_A)
m('StExpChance', '%.1f' % E_CHANCE)
m('StNOutsideWord', _WORDS[len(OUTSIDE)])
m('StObs', '%d' % N_OBS)
m('StNOutside', '%d' % len(OUTSIDE))
m('StOutsideStar', ' / '.join(s.replace(' ', '~') for s in OUT_STARS))
m('StPois', '%.0f' % POIS)
m('StFloor', '%.0f' % FLOOR)

m('StExpModel', '%.1f' % E_MODEL)
m('StModelAgreePct', '%.0f' % AGREE_PCT)
m('StNindFrac', '%.2f' % NIND_FRAC)
m('StGridFrac', '%.2f' % GRID_FRAC)

m('StHoNFine', '%d' % len(HO_FINE))
m('StHoObs', '%d' % HO_OBS)
m('StHoExpFine', '%.1f' % HO_EXP)
m('StHoRatio', '%.2f' % HO_RATIO)
m('StHoLo', '%.2f' % HO_LO)
m('StHoHi', '%.2f' % HO_HI)
m('StHoAccPct', '%.0f' % HO_ACC_PCT)
m('StHoNCoarse', '%d' % len(HO_COARSE))
m('StHoExpCoarse', '%.2f' % HO_EXP_C)

m('StNRep', '%d' % len(REPAIR))
m('StRepOnsrc', '%.1f' % float(np.median(ONS)))
m('StRepDT', '%.2f' % float(np.median(DT)))
m('StRepDTAbs', '%.2f' % float(np.median(np.abs(DT))))
m('StRepAdopted', '%d' % N_REP_ADOPTED)
m('StRepFell', '%d' % len(FELL))
m('StRepAttr', '%d' % len(NOWATTR))

m('StTelHours', '%.0f' % H_TEL)
m('StTelHoursFine', '%.0f' % H_TEL_A)
m('StTelHoursCoarse', '%.0f' % H_TEL_B)

m('StExpSurv', '%.1f' % E_SURV)
m('StFlagExp', '%.1f' % E_FLAG)
m('StBCleanExp', '%.2f' % E_B_CLEAN)
m('StBCleanObs', '%d' % OBS_B_CLEAN)

# =====================================================================
# write
# =====================================================================
if fail:
    print('\nFAILED: %s' % '; '.join(fail))
    if DRIVE is None:
        raise SystemExit(1)

hdr = ['%% GENERATED by stats_v413.py (round %d) -- do not hand-edit.' % ROUND,
       '%% One population for the chance comparison, exchangeability measured',
       '%% on the reserved blocks, the cell budget as a cross-check, and the',
       '%% two kinds of on-source hour.']
with open(OUT_TEX, 'w') as fh:
    fh.write('\n'.join(hdr + sorted(OUT)) + '\n')
json.dump(dict(round=ROUND,
               n_win_A=len(IA),
               e_trig_A=E_TRIG_A,
               e_trig_A_released_extraction=E_TRIG_A_REL,
               mask_occupancy=OCC,
               e_chance=E_CHANCE,
               observed=N_OBS,
               observed_routes=[ROUTE_REL, ROUTE_LED],
               outside=[(r['display'], r['eb'], r['freq']) for r in OUTSIDE],
               ledger_unattributed_A=len(UN_LED),
               e_model=E_MODEL, e_emp_same_windows=E_EMP_COV,
               agree_pct=AGREE_PCT,
               nind_frac=NIND_FRAC, grid_frac=GRID_FRAC,
               holdout=dict(fine_windows=len(HO_FINE), observed=HO_OBS,
                            expected=HO_EXP, ratio=HO_RATIO,
                            interval=[HO_LO, HO_HI],
                            blocks_hit=HO_NBLOCK_HIT,
                            coarse_windows=len(HO_COARSE),
                            coarse_observed=HO_OBS_C,
                            coarse_expected=HO_EXP_C),
               repair=dict(n_windows=len(REPAIR),
                           onsource_ratio=float(np.median(ONS)),
                           dt_signed=float(np.median(DT)),
                           dt_abs=float(np.median(np.abs(DT))),
                           adopted_rows=N_REP_ADOPTED,
                           fell=len(FELL), attributed=len(NOWATTR)),
               hours=dict(window=H_WIN, window_A=H_WIN_A, window_B=H_WIN_B,
                          telescope=H_TEL, telescope_A=H_TEL_A,
                          telescope_B=H_TEL_B),
               flagged=dict(block=FLAG_EB, windows=len(IFLAG), expected=E_FLAG,
                            b_clean_expected=E_B_CLEAN,
                            b_clean_observed=OBS_B_CLEAN),
               drive=DRIVE),
          open(OUT_JSON, 'w'), indent=1, sort_keys=True)
print('\nwrote %s (%d macros) and %s'
      % (os.path.basename(OUT_TEX), len(OUT), os.path.basename(OUT_JSON)))
