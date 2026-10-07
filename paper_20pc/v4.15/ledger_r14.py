#!/usr/bin/env python3
r"""Round 450: the sample ledger's three undocumented items, and the
intra-integration smearing term for the WHOLE census rather than a third of it.

1. INTRA-INTEGRATION SMEARING, MEASURED OR BOUNDED FOR EVERY WINDOW.
   The release carries `n_int` for 451 of the 1651 census windows, and the
   appendix said of the other 1200 that "the quantity cannot be formed at all
   and the thresholds are unverified on this point".  That is not true.  The
   campaign's own exposure scan (`r8inputs/d3_scan_v404.json`) applied both
   on-source estimators to the `times` array of every surviving extraction
   product -- 3007 (block, spectral window) records -- and it carries `nint`
   and the integration-summed span.  Joined to the catalogue on the block and
   the window's own published on-source time, it recovers the integration
   length for 595 further windows; where the release and the scan both carry
   it they agree on all 242, exactly, which is what makes the join an
   identifier and not a guess.

   For the 605 windows that remain, the term is BOUNDED rather than left
   open, and the bound is conclusive: at the longest integration delivered
   anywhere in the campaign none of them falls below eta_smear = 0.997.  So
   the census splits 1046 measured / 605 bounded / 0 neither, and no window's
   threshold is unverified on this point.

   13 windows -- all fine-channel -- fall below 0.99 at the top of their own
   drift range, against 9 in the released subset.  Folded into their limits
   the per-system median is unchanged at the two significant figures the paper
   prints, and one system's best Class A limit crosses 10^15 W.

2. THE TWO CUTS THE SAMPLE SECTION DID NOT DOCUMENT.
   (a) There is no on-source-time threshold at all: the shortest retained
       window is 21 s, and the sentence that read "or for short integration"
       implied a cut that does not exist.
   (b) The window quality cut is the noise-handling defect test: a window
       whose sigma*sqrt(t_on*dnu_ch) is more than a hundred times below the
       sample median cannot be a real measurement.  It removes 13 windows in
       11 blocks toward 8 stars, and it is insensitive to where the line was
       drawn -- the 13 are 4.7e3 to 3.0e4 times below the median and the
       nearest retained window 24 times, so any threshold between them
       removes the same 13.

3. THE LEDGER ROW LABELLED "NO WINDOW SURVIVED THE QUALITY CUT" IS NOT A
   QUALITY CUT.  Its three blocks are the three epsilon Eridani Band 6 blocks,
   and its 12 windows are the 12 the withholding rule sets aside.  Eight of
   them, in two blocks, have a primary-beam response of 0.28-0.35 and so fail
   the 0.5 floor.  The other four, in one block, place the star at the
   pointing centre at a response of 1.00: the floor cannot be what removed
   them, and their limits are reported.

4. TWO SAMPLE COUNTS THAT MATCH NO LEDGER ROW, NAMED.
   3027 windows toward 133 stars is every window the pipeline extracted: the
   census and the rows its audit removed, the reserved hold-out, the archival
   extension, the out-of-sample control, and 64 windows in 16 blocks that
   entered none of them.  And the 149 blocks of the rank comparison are the
   epoch-extension campaign, which is disjoint from the archival extension
   and is not the reserved hold-out.

Usage:  ledger_r14.py [--drive N]      N in 1..12, each breaks one assertion
"""
import collections
import csv
import json
import math
import os
import re
import sys

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
ROUND = 450
DRIVE = int(sys.argv[sys.argv.index('--drive') + 1]) if '--drive' in sys.argv \
    else 0
SUF = '' if DRIVE == 0 else '_drive%d' % DRIVE
OUT = 'survey_numbers_round450%s.tex' % SUF
OUT_PATH = os.path.join(HERE, OUT)

CAT_NAME = 'per_target_results_v3.99.csv'
DEFECT_CUT = 100.0          # the published noise-handling defect threshold
LOW = 0.99                  # the appendix's own "fold it in below this"

M, FAIL = [], []


def m(k, v):
    assert k.isalpha(), 'a LaTeX macro name may contain letters only: %s' % k
    M.append('\\newcommand{\\%s}{%s}' % (k, v))


def ck(name, cond, detail=''):
    print('  %-72s %s' % (name[:72], 'OK' if cond else 'FAIL ' + str(detail)))
    if not cond:
        FAIL.append(name.split()[0])


def texval(macro):
    pat = re.compile(r'(?:new|renew|provide)command\{\\%s\}\{([^}]*)\}'
                     % macro)
    for fn in sorted(os.listdir(HERE)):
        if not fn.startswith('survey_numbers') or not fn.endswith('.tex'):
            continue
        if '_drive' in fn:
            continue
        # round 103 declares with \providecommand{\X}{} and then sets the
        # value with \renewcommand, so an empty first match is a declaration
        # and not the value.
        for mm in pat.finditer(open(os.path.join(HERE, fn)).read()):
            if mm.group(1).strip():
                return mm.group(1)
    raise KeyError(macro)


def texnum(macro):
    return float(texval(macro).replace('\\,', '').replace(',', ''))


def sinc(x):
    return 1.0 if x == 0.0 else math.sin(x) / x


def sci(x, sf=2):
    e = int(math.floor(math.log10(abs(x))))
    return r'%.*f\times10^{%d}' % (sf - 1, x / 10.0 ** e, e)


CAT = list(csv.DictReader(open(os.path.join(HERE, CAT_NAME))))
SCAN = json.load(open(os.path.join(HERE, 'r8inputs',
                                   'd3_scan_v404.json')))['rows']
EXPORT = json.load(open(os.path.join(HERE,
                                     'corrected_export_v399.json')))['rows']
META = json.load(open(os.path.join(HERE, 'archive_meta_v381.json')))
HOLD = json.load(open(os.path.join(HERE, 'holdout_export_v381.json')))['rows']
OOS = json.load(open(os.path.join(HERE, 'outofsample_v381.json')))['rows']
EXTR = json.load(open(os.path.join(HERE, 'export_extension.json')))['rows']
OCC = list(csv.DictReader(open(os.path.join(HERE, 'occupancy_windows.csv'))))
EPOCHX = json.load(open(os.path.join(HERE, 'heldout_v352.json')))

import star_alias as sa                                      # noqa: E402

print('ledger_r14 round %d%s' % (ROUND, '' if not DRIVE
                                 else ' (drive %d)' % DRIVE))


def tex_star(name):
    return sa.designation(name).replace(' ', '~')


# =====================================================================
# 1. THE INTEGRATION LENGTH OF EVERY CENSUS WINDOW
# =====================================================================
# The scan is keyed on (block, spectral window); the catalogue has no
# spectral-window column, so the join key is the block together with the
# window's own published on-source time, which the scan records as `pub`.
# `old` is the catalogue's own estimator -- n_int x median(dt) -- so where
# both sources carry a window they must agree exactly, and that equality is
# the test of the join below.
SCAN_IX = collections.defaultdict(list)
for _s in SCAN:
    if _s['pub'] is not None and _s['nint']:
        SCAN_IX[(_s['eb'], round(_s['pub'], 3))].append(_s)

MEAS, BOUND, NONE, AGREE = [], [], [], []
for r in CAT:
    key = (r['eb'], round(float(r['on_source_s']), 3))
    hit = SCAN_IX.get(key)
    if r['n_int'] not in ('', 'None'):
        r['_dt'], r['_src'] = (float(r['on_source_s'])
                               / float(r['n_int']), 'release')
        if hit:
            AGREE.append(abs(hit[0]['old'] / hit[0]['nint'] / r['_dt'] - 1.0))
    elif hit:
        r['_dt'], r['_src'] = hit[0]['old'] / hit[0]['nint'], 'scan'
    else:
        r['_dt'], r['_src'] = None, 'bound'

# ★ THE CEILING IS THE LONGEST INTEGRATION THE CAMPAIGN DELIVERED ANYWHERE,
# from either source.  Taking it from the exposure scan alone made L3 fail on
# the first run, and it was right to: the release's own records hold a longer
# integration (11.58 s) than any product the scan reached (10.08 s), so a
# scan-only ceiling would not have bounded anything.
DT_CEIL = max([s['old'] / s['nint'] for s in SCAN if s['nint']]
              + [r['_dt'] for r in CAT if r['_dt'] is not None])
if DRIVE == 3:
    DT_CEIL = 0.5                      # the bound must stop being a bound

# ★ "NEITHER" MUST BE A CATEGORY THAT CAN BE OCCUPIED, or counting it is a
# check that cannot fail.  A window is in it when eta_smear cannot be formed
# even from the ceiling -- that is, when its own drift ceiling or channel
# width is missing -- which is the only way the bound can fail to apply.
for r in CAT:
    if DRIVE == 12 and r is CAT[0]:
        r['drift_max_Hz_s'] = ''       # "neither" must be reachable
    if r['drift_max_Hz_s'] in ('', 'None') or r['chanw_Hz'] in ('', 'None'):
        r['_src'] = 'none'
        NONE.append(r)
        continue
    if r['_dt'] is None:
        r['_dt'] = DT_CEIL
    r['_delta'] = float(r['drift_max_Hz_s']) * r['_dt'] / float(r['chanw_Hz'])
    r['_eta'] = sinc(math.pi * r['_delta'] / 2.0)
    (MEAS if r['_src'] in ('release', 'scan') else BOUND).append(r)

if DRIVE == 1:
    MEAS = MEAS[:-1]                   # the three groups must partition

N_FROM_SCAN = sum(1 for r in MEAS if r['_src'] == 'scan')
N_FROM_CAT = sum(1 for r in MEAS if r['_src'] == 'release')
LOWS = sorted((r for r in MEAS if r['_eta'] < LOW), key=lambda r: r['_eta'])
BOUND_ETA = min(r['_eta'] for r in BOUND)

print('\n1. the smearing coverage of the census')
print('   measured %d (%d in the release, %d recovered from the exposure '
      'scan), bounded %d, neither %d'
      % (len(MEAS), N_FROM_CAT, N_FROM_SCAN, len(BOUND), len(NONE)))
print('   the release and the scan both carry %d windows and agree to %.2g'
      % (len(AGREE), max(AGREE) if AGREE else 0.0))
print('   longest integration delivered anywhere %.2f s; at that ceiling the '
      'bounded windows reach eta >= %.4f' % (DT_CEIL, BOUND_ETA))
print('   %d measured windows fall below %.2f:' % (len(LOWS), LOW))
for r in LOWS:
    print('     %-14s %-22s B%-2s %7.1f kHz  Delta=%.2f  eta=%.3f (x%.2f)'
          % (r['star_name'][:14], r['eb'], r['band'],
             float(r['chanw_Hz']) / 1e3, r['_delta'], r['_eta'],
             1.0 / r['_eta']))

_n = len(MEAS) + len(BOUND) + len(NONE)
ck('L1 every census window is measured or bounded, with nothing left in '
   'between, the three groups partition the census, and the measured group '
   'contains the subset the release itself carries',
   _n == int(texnum('NWindows')) and len(NONE) == 0
   and N_FROM_CAT == int(texnum('CsNDumpWin')) and N_FROM_SCAN > 0,
   '%d + %d + %d = %d against %s; release subset %d against %s'
   % (len(MEAS), len(BOUND), len(NONE), _n, texval('NWindows'),
      N_FROM_CAT, texval('CsNDumpWin')))

_worst = max(AGREE) if AGREE else 1.0
if DRIVE == 2:
    _worst = 0.5                       # the join must be exact where testable
ck('L2 the join is an identifier and not a guess: where the release and the '
   'exposure scan both carry a window they agree exactly, and the overlap '
   'is large enough for that to mean something',
   len(AGREE) > 100 and _worst < 1e-5,
   '%d windows overlap, worst relative disagreement %.3g' % (len(AGREE),
                                                             _worst))

ck('L3 the bound is conclusive: at the longest integration delivered '
   'anywhere, which is at least as long as the longest measured one, no '
   'bounded window loses one per cent',
   DT_CEIL >= max(r['_dt'] for r in MEAS) - 1e-9 and BOUND_ETA >= LOW,
   'ceiling %.3f s against the longest measured %.3f s; worst bounded eta '
   '%.4f' % (DT_CEIL, max(r['_dt'] for r in MEAS), BOUND_ETA))

# ★ This used to compare against the published \NSmearLo, which this pass
# retires: a generator that reads a macro it is causing to be deleted breaks
# on the next build.  The comparison is made against the recomputed
# release-only subset instead, which is self-contained.
N_LOW_REL = sum(1 for r in LOWS if r['_src'] == 'release')
_nlow = len(LOWS) if DRIVE != 4 else N_LOW_REL
ck('L4 the term bites only on the fine-channel experiment, and the recovered '
   'integration lengths find more affected windows than the released '
   'integration counts alone could',
   all(r['resolution_class'] == 'fine' for r in LOWS)
   and _nlow > N_LOW_REL > 0,
   '%d below %.2f, %d of them fine; %d are in the release\'s own subset'
   % (_nlow, LOW, sum(1 for r in LOWS if r['resolution_class'] == 'fine'),
      N_LOW_REL))

# The stars the term reaches, named in plain English rather than as a string
# of bracketed numbers: the factors themselves are a range and are printed as
# one.
_stars = []
for r in LOWS:
    s = tex_star(r['star_name'])
    if s not in _stars:
        _stars.append(s)
SMSTARS = ', '.join(_stars[:-1]) + ' and ' + _stars[-1]

# the same factor averaged over the drift grid the search actually ran, so
# that the ceiling value is not mistaken for the typical one
_grid = []
for r in LOWS:
    g = np.linspace(-r['_delta'], r['_delta'], 4001)
    _grid.append(float(np.mean([sinc(math.pi * abs(x) / 2.0) for x in g])))
GRID_WORST = 1.0 / min(_grid)

m('SmNMeas', '%d' % len(MEAS))
m('SmNBound', '%d' % len(BOUND))
m('SmNNone', '%d' % len(NONE))
m('SmNRecov', '%d' % N_FROM_SCAN)
m('SmDtCeil', '%.1f' % DT_CEIL)
m('SmBoundEta', '%.3f' % BOUND_ETA)
m('SmDeltaMax', '%.2f' % max(r['_delta'] for r in MEAS))
m('SmNLow', '%d' % len(LOWS))
m('SmNLowStar', '%d' % len(_stars))
m('SmLowStars', SMSTARS)
m('SmEtaMin', '%.3f' % LOWS[0]['_eta'])
m('SmFacLo', '%.2f' % (1.0 / LOWS[-1]['_eta']))
m('SmFacWorst', '%.2f' % (1.0 / LOWS[0]['_eta']))
m('SmFacGrid', '%.2f' % GRID_WORST)
m('SmCompound', '%.1f' % (texnum('HanFacWorst') / LOWS[0]['_eta']))

# ------------------------------------------------- what folding it in costs
import adopted_e90 as _ae                                    # noqa: E402

_E90 = _ae.per_window(CAT, HERE)


def _sysbest(fold):
    best = {}
    for r in CAT:
        if r['resolution_class'] != 'fine':
            continue
        v = _E90[id(r)]
        if v is None:
            continue
        if fold and r['_eta'] < LOW:
            v = v / r['_eta']
        s = r['system_id']
        if s not in best or v < best[s]:
            best[s] = v
    return np.array(sorted(best.values()))


_A0, _A1 = _sysbest(False), _sysbest(True)
MED0, MED1 = float(np.median(_A0)), float(np.median(_A1))
NE0, NE1 = int((_A0 <= 1e15).sum()), int((_A1 <= 1e15).sum())
print('   per-system median %.4e -> %.4e W (printed %s -> %s); systems '
      'reaching 1e15 W %d -> %d'
      % (MED0, MED1, sci(MED0), sci(MED1), NE0, NE1))

_lost = NE0 - NE1 if DRIVE != 11 else 0
ck('L11 folding the term in leaves the printed per-system median where it is '
   'and moves the count of systems reaching 1e15 W, so the one number that '
   'changes is identified rather than absorbed',
   sci(MED0) == sci(MED1) and _lost > 0 and NE0 == int(texnum('NSysEfifteen')),
   'median %s against %s; %d systems against %s, %d after folding'
   % (sci(MED0), sci(MED1), NE0, texval('NSysEfifteen'), NE1))

m('SmNSysLost', '%d' % (NE0 - NE1))
m('SmSysEfifteen', '%d' % NE1)
# generated English, not a figure: a sentence must not read "move 1 system",
# and "0 windows are unaccounted for" is not a sentence either.
_WORDS = ['no', 'one', 'two', 'three', 'four', 'five', 'six', 'seven',
          'eight', 'nine']


def _word(n):
    return _WORDS[n] if n < len(_WORDS) else '%d' % n


m('SmSysLostWord', _word(NE0 - NE1))
m('SmSysLostPlural', '' if NE0 - NE1 == 1 else 's')
m('SmNoneClause', 'no window is left unaccounted for' if not NONE
  else '%s windows are left unaccounted for' % _word(len(NONE)))

# =====================================================================
# 2. THE CATALOGUE AUDIT, AND THE TWO CUTS THE SAMPLE SECTION DID NOT NAME
# =====================================================================
for r in EXPORT:
    r['_qa'] = r['rms'] * math.sqrt(r['onsrc'] * r['chanw'])


def _wkey(r):
    return (r['star_name'], r['eb'], round(min(r['flo'], r['fhi']), 6),
            round(max(r['flo'], r['fhi']), 6), r['chanw'])


_best = {}
for r in EXPORT:
    k = _wkey(r)
    if k not in _best or (_best[k]['line'] is None and r['line'] is not None):
        _best[k] = r
UNIQ = list(_best.values())
QA_MED = float(np.median([r['_qa'] for r in UNIQ]))
DEFECT = [r for r in UNIQ if r['_qa'] < QA_MED / DEFECT_CUT]
KEPT = [r for r in UNIQ if r['_qa'] >= QA_MED / DEFECT_CUT]


def _is_eps(r):
    return r['star_name'] == 'eps Eri' and (r['band'] or 0) == 6


WITHHELD = [r for r in KEPT if _is_eps(r)]
GOOD = [r for r in KEPT if not _is_eps(r)]

DEF_FACS = sorted(QA_MED / r['_qa'] for r in DEFECT)
KEPT_FAC = max(QA_MED / r['_qa'] for r in KEPT)
ONSRC = sorted(r['onsrc'] for r in GOOD)
N_AT_MIN = sum(1 for x in ONSRC if x < ONSRC[0] * 1.01)

print('\n2. the catalogue audit and the two unnamed cuts')
print('   export %d - duplicates %d - defect %d - withheld %d = %d'
      % (len(EXPORT), len(EXPORT) - len(UNIQ), len(DEFECT), len(WITHHELD),
         len(GOOD)))
print('   the defect cut is at %.0fx below the median; the removed windows '
      'are %.2g-%.2gx below it and the nearest retained %.0fx'
      % (DEFECT_CUT, DEF_FACS[0], DEF_FACS[-1], KEPT_FAC))
print('   defect: %d windows, %d blocks, %d stars'
      % (len(DEFECT), len({r['eb'] for r in DEFECT}),
         len({r['star_name'] for r in DEFECT})))
print('   shortest retained on-source time %.2f s (%d windows), next %.2f s'
      % (ONSRC[0], N_AT_MIN, ONSRC[N_AT_MIN]))

_ndup = len(EXPORT) - len(UNIQ) if DRIVE != 5 else len(EXPORT) - len(UNIQ) + 1
ck('L5 the catalogue audit closes on the published census, and the defect '
   'cut sits inside a gap, so any threshold between the nearest retained '
   'window and the nearest removed one removes the same windows',
   len(EXPORT) - _ndup - len(DEFECT) - len(WITHHELD)
   == int(texnum('NWindows'))
   and _ndup == int(texnum('NDup'))
   and len(DEFECT) == int(texnum('NDefect'))
   and len(WITHHELD) == int(texnum('NWithheld'))
   and KEPT_FAC < DEFECT_CUT < DEF_FACS[0],
   '%d - %d - %d - %d = %d against %s; gap %.0fx .. %.2gx around %.0fx'
   % (len(EXPORT), _ndup, len(DEFECT), len(WITHHELD),
      len(EXPORT) - _ndup - len(DEFECT) - len(WITHHELD), texval('NWindows'),
      KEPT_FAC, DEF_FACS[0], DEFECT_CUT))

_omin = ONSRC[0] if DRIVE != 6 else 600.0
ck('L6 no on-source-time threshold was applied: the shortest retained window '
   'is far below any plausible one, and the windows holding it were searched '
   'like the rest',
   _omin < 30.0
   and all(r['star_snr'] is not None for r in GOOD if r['onsrc'] == ONSRC[0]),
   'shortest retained %.2f s on %d windows' % (_omin, N_AT_MIN))

m('LqNExport', '%d' % len(EXPORT))
m('LqDefectCut', '%d' % int(DEFECT_CUT))
m('LqDefectFacLo', sci(DEF_FACS[0]))
m('LqDefectFacHi', sci(DEF_FACS[-1]))
m('LqKeptFac', '%.0f' % KEPT_FAC)
m('LqDefectNEb', '%d' % len({r['eb'] for r in DEFECT}))
m('LqDefectNStar', '%d' % len({r['star_name'] for r in DEFECT}))
m('LqOnsrcMin', '%.0f' % ONSRC[0])
m('LqNOnsrcMin', '%d' % N_AT_MIN)

# =====================================================================
# 3. THE LEDGER ROW THAT IS NOT A QUALITY CUT
# =====================================================================
NOWINDOW = set(META['ebs']) - {r['eb'] for r in CAT} - {r['eb'] for r in HOLD}
EPS_EB = {r['eb'] for r in WITHHELD}


def _resp(r):
    return 5.0 * r['rms'] / (r['smin'] * 1e3)


ON = [r for r in WITHHELD if _resp(r) > 0.9]
OFF = [r for r in WITHHELD if _resp(r) <= 0.9]
FLOOR = texnum('PbFloorResp')

print('\n3. the three blocks with no census window')
print('   %s' % ', '.join(sorted(NOWINDOW)))
print('   they are the %d epsilon Eri Band 6 blocks and hold all %d '
      'withheld windows: %d at response %.2f-%.2f in %d blocks, %d at '
      '%.2f in %d block'
      % (len(EPS_EB), len(WITHHELD), len(OFF), min(_resp(r) for r in OFF),
         max(_resp(r) for r in OFF), len({r['eb'] for r in OFF}), len(ON),
         min(_resp(r) for r in ON), len({r['eb'] for r in ON})))

_eb = EPS_EB if DRIVE != 7 else set(sorted(EPS_EB)[:-1])
ck('L7 the ledger row labelled a quality cut is the withholding rule: its '
   'blocks are exactly the withheld star-band blocks and its windows exactly '
   'the withheld windows',
   _eb == NOWINDOW and len(WITHHELD) == int(texnum('EpsEriNWin'))
   and len(OFF) + len(ON) == len(WITHHELD),
   '%d blocks against %d with no census window; %d windows against %s'
   % (len(_eb), len(NOWINDOW), len(WITHHELD), texval('EpsEriNWin')))

_on_resp = min(_resp(r) for r in ON) if DRIVE != 8 else 0.1
ck('L8 the response floor cannot be the rule that removed the on-axis '
   'windows: they sit at the pointing centre, above it, while the others '
   'are below it',
   max(_resp(r) for r in OFF) < FLOOR < _on_resp
   and len(ON) == int(texnum('EpsEriNOnAxis'))
   and len(OFF) == int(texnum('EpsEriNOffAxis')),
   'off axis up to %.3f, floor %s, on axis from %.3f; %d and %d against %s '
   'and %s' % (max(_resp(r) for r in OFF), texval('PbFloorResp'), _on_resp,
               len(OFF), len(ON), texval('EpsEriNOffAxis'),
               texval('EpsEriNOnAxis')))

m('LqEpsRespLo', '%.2f' % min(_resp(r) for r in OFF))
m('LqEpsRespHi', '%.2f' % max(_resp(r) for r in OFF))
m('LqEpsRespOn', '%.2f' % min(_resp(r) for r in ON))
m('LqEpsOffEb', '%d' % len({r['eb'] for r in OFF}))
m('LqEpsOnEb', '%d' % len({r['eb'] for r in ON}))

# =====================================================================
# 4. THE TWO SAMPLE COUNTS THAT MATCH NO LEDGER ROW
# =====================================================================
SETS = {'census': {r['eb'] for r in CAT},
        'holdout': {r['eb'] for r in HOLD},
        'extension': {r['eb'] for r in EXTR},
        'outofsample': {r['eb'] for r in OOS}}
_named = set().union(*SETS.values())
OTHER_EB = {r['eb'] for r in OCC} - _named
OTHER_WIN = [r for r in OCC if r['eb'] in OTHER_EB]
PARTS = collections.Counter()
for r in OCC:
    PARTS[next((k for k, v in SETS.items() if r['eb'] in v), 'other')] += 1

print('\n4. the extraction, and the epoch-extension campaign')
print('   %d extracted windows in %d blocks: %s'
      % (len(OCC), len({r['eb'] for r in OCC}), dict(PARTS)))

_tot = sum(PARTS.values()) if DRIVE != 9 else sum(PARTS.values()) + 1
ck('L9 the extracted-window count is the five block sets together and '
   'nothing else, and the residual blocks are in none of the four named '
   'sets',
   _tot == int(texnum('RfiOccNWin')) and len(OTHER_WIN) == PARTS['other']
   and not (OTHER_EB & _named),
   '%d against %s; %d residual windows in %d residual blocks'
   % (_tot, texval('RfiOccNWin'), len(OTHER_WIN), len(OTHER_EB)))

XWIN = [w for w in EPOCHX['windows']
        if not w.get('detection') and not w.get('stage1')]
XEB = {w['eb'] for w in XWIN}
_xeb = XEB if DRIVE != 10 else XEB | {sorted(SETS['extension'])[0]}
ck('L10 the 149-block rank comparison is the epoch-extension campaign: it is '
   'disjoint from the archival extension, it is not the reserved hold-out, '
   'and its block count is the published one',
   len(XEB) == int(texnum('HOBlockN'))
   and not (_xeb & SETS['extension'])
   and XEB != SETS['holdout'] and len(XEB & SETS['census']) > 0,
   '%d blocks against %s; %d in the archival extension; %d census and %d '
   'hold-out blocks among them'
   % (len(XEB), texval('HOBlockN'), len(_xeb & SETS['extension']),
      len(XEB & SETS['census']), len(XEB & SETS['holdout'])))

m('OqOtherWin', '%d' % len(OTHER_WIN))
m('OqOtherEb', '%d' % len(OTHER_EB))
m('OqCampNEb', '%d' % len(XEB))
m('OqCampNStar', '%d' % len({w['star'] for w in XWIN}))
m('OqCampNCensusEb', '%d' % len(XEB & SETS['census']))

# =====================================================================
print('\nassertions failed: %d %s' % (len(FAIL), FAIL))
if FAIL and DRIVE == 0:
    raise SystemExit('ledger_r14: %d assertion(s) failed: %s'
                     % (len(FAIL), FAIL))

HDR = ['%% GENERATED by ledger_r14.py -- do not hand-edit.',
       '%% round 450: intra-integration smearing measured or bounded for '
       'every census',
       '%% window, the catalogue audit and its two unnamed cuts, the '
       'withholding rule',
       '%% that the ledger called a quality cut, and the two sample counts '
       'that match',
       '%% no ledger row.']
with open(OUT_PATH, 'w') as fh:
    fh.write('\n'.join(HDR + sorted(M)) + '\n')
print('wrote %s: %d macros' % (OUT, len(M)))
