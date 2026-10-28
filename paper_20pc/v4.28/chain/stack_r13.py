#!/usr/bin/env python3
r"""Round 350 -> survey_numbers_round350.tex: WHAT THE STELLAR-FRAME STACK CAN
AND CANNOT TEST, AND HOW MUCH OF THIS EXPERIMENT FALLS INSIDE THE CONVENTIONAL
SEARCH HAYSTACK.

Three sentences of the manuscript were wrong in three different ways and all
three had the same cause: a quantity was remembered instead of read.

1. THE STACK WAS CALLED AN INDEPENDENT TEST OF THE THRESHOLD CROSSINGS, OVER A
   HARD-CODED LIST OF NINE STARS.  `stack_v408.py` carries

       PERSIST = ['taucet', '61vir', 'cp-722713', 'etacrv', 'hd31392',
                  'hd285968', 'gj849', 'lhs1140', 'hd207129']

   which is a list of the stars the crossing chain reached several rounds
   earlier.  It is not the set of hosts of the unattributed crossings: two of
   the nine (tau Cet, HD 285968) carry none, and the crossings are spread over
   stars the list never had.  Counted from the ledger itself the hosts number
   \SttNHostStar.  The only safe form of this number is `len(set)` over the
   ledger's own rows, so that is what this generator publishes.

2. IT WAS NOT INDEPENDENT.  For \SttNIncDisc of the unattributed crossings the
   stacked group covering that crossing's own stellar-frame frequency contains
   the crossing's own discovery execution block.  A test that contains the
   datum it is testing is not an independent test of it, and A6 asserts the
   overlap rather than leaving the word to be noticed by a reader.

3. AND IT COULD NOT HAVE TESTED THEM ANYWAY.  A stack holds a carrier inside
   one \StkRefChanKHz kHz channel across its epochs only if the carrier drifts
   by less than one channel over the span: \StkDriftTolHzS Hz/s over the median
   span.  The slowest drift measured among the unattributed crossings is
   \SttDriftMinHzS Hz/s -- four thousand times that, and enough to carry a
   carrier out of one channel in \SttDriftMinMin minutes.  Coverage is not the
   obstacle (A5: every crossing lies inside the stellar-frame coverage of a
   stacked group of its own star); the drift is.  So the stack tests a carrier
   that does not drift, and the honest statement is that and no more.

4. A FOURTH, in the discussion: "20.6 GHz of the union here lies inside the
   10 MHz-115 GHz interval".  \UnionBandThree is the union of the ALMA Band 3
   windows, 0.75 GHz of which lies ABOVE 115 GHz (A7), so it is the
   wrong quantity for that sentence by construction.  Clipped at the haystack
   ceiling the total union contributes \SttHayGHz GHz, of which only
   \SttHayFineGHz GHz is fine-channel carrier search -- the Class A union
   begins at \SurvFreqLoA GHz.  A7 ties the three together so the Band 3 union can
   never again be printed as the sub-115 GHz one.

5. AND A FIFTH, in the same subsection: "58 of the surveyed stars, lying in 58
   separate systems, hold more than one searched execution block".  \EpMulti of
   the \NSystems surveyed systems hold more than one searched block;
   \SxStkStarCensus is the number of census stars the stack combines, which is
   a different set and larger because the stack also draws on the archival
   extension and the reserved hold-out -- \SttNStkOneEb of those stars hold
   only one census block.  A8 recomputes \EpMulti from the catalogue and
   requires the two macros to differ, so neither can be printed as the other.

Emits (all referenced in the manuscript):

    \SttNHostStar     stars carrying the unattributed crossings of the
                      recurrence section, len(set) over the ledger
    \SttDriftMinHzS   slowest measured discovery drift among those crossings
    \SttDriftMinMin   minutes for that drift to cross one \StkRefChanKHz kHz
                      channel
    \SttNIncDisc      crossings whose covering stack contains their own
                      discovery block
    \SttNStkOneEb     stacked census stars holding only one census block
    \SttHayLoMHz      the search-haystack frequency axis, low edge
    \SttHayHiGHz      ... and high edge, as adopted by Wright et al.
    \SttHayGHz        total union bandwidth inside that interval
    \SttHayFineGHz    the fine-channel carrier part of it

Eight assertions, eight drives.  --drive N breaks assertion N and nothing
else; --drive 0 means "no perturbation, but do not write a path production
reads".

    python3 stack_r13.py [--drive N]

Run after stack_v408.py, ledger_v410.py, epochsplit_v399.py, cover_v412.py and
v343_calc.py: every one of those is read back out of the macro layer or out of
its own product here, so a disagreement is reported against the file that
published it.
"""
import collections
import csv
import glob
import json
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
DATA = os.path.join(HERE, 'stack_v408')
sys.path.insert(0, DATA)
import starkey                                            # noqa: E402

DRIVE = None
for _i, _a in enumerate(sys.argv):
    if _a == '--drive':
        DRIVE = int(sys.argv[_i + 1])
SUF = '' if DRIVE is None else '_drive%d' % DRIVE

HAY_LO_MHZ = 10.0          # Wright et al. (2018), the search-haystack axis
HAY_HI_GHZ = 115.0

MACROS, fail = [], []


def m(name, val):
    # A LaTeX macro name may contain letters only: \FooV409 defines \FooV and
    # asks TeX to typeset "409", which in the preamble is no PDF at all.
    assert name.isalpha(), (
        'a LaTeX macro name may contain letters only: %r' % name)
    MACROS.append('\\newcommand{\\%s}{%s}' % (name, val))


def ck(label, cond, detail=''):
    print('  %-70s %s  %s' % (label, 'PASS' if cond else 'FAIL', detail))
    if not cond:
        fail.append(label)


def texval(name):
    """One macro's value out of the frozen layer, by name.  LAST definition
    wins: the retirement rounds alias superseded names, so a first-match
    reader returns the stale value."""
    pat = re.compile(r'\\(?:new|renew|provide)command\{\\%s\}'
                     r'\{((?:[^{}]|\{[^{}]*\})*?)\}' % name)
    v = None
    for fn in sorted(glob.glob(os.path.join(HERE, 'survey_numbers*.tex'))):
        for mm in pat.finditer(open(fn, encoding='utf-8').read()):
            if mm.group(1).strip():
                v = mm.group(1).strip()
    if v is None:
        raise SystemExit('stack_r13: macro %s not found' % name)
    return v


def texnum(name):
    """...as a float, stripping the maths a scientific-notation macro carries.
    `$1.3 \times 10^{-1}$` is a number, and comparing it as a string is how a
    recomputation check goes vacuous."""
    s = texval(name)
    mm = re.match(r'^\$?\s*([-+]?[\d.]+)\s*(?:\\times\s*10\^\{?([-+]?\d+)\}?)?'
                  r'\s*\$?$', s)
    if not mm:
        raise SystemExit('stack_r13: %s = %r is not a number' % (name, s))
    return float(mm.group(1)) * (10.0 ** int(mm.group(2) or 0))


# ------------------------------------------------------------------- inputs
LED = json.load(open(os.path.join(HERE, 'ledger.json')))
REC = json.load(open(os.path.join(HERE, 'r10inputs', 'recur_v411.json')))
STK = [json.loads(l) for l in
       open(os.path.join(DATA, 'stack6_result.jsonl')) if 'err' not in l]
GRP = json.load(open(os.path.join(DATA, 'groups3.json')))
CAT = list(csv.DictReader(open(os.path.join(
    HERE, 'per_target_results_v3.99.csv'))))
MJD = json.load(open(os.path.join(HERE, 'epochs_v386.json')))['mjd']
IDMAP, _ = starkey.build(json.load(open(os.path.join(DATA, 'windows.json'))))

EBPAT = re.compile(r'(A002_X[0-9a-f]+_X[0-9a-f]+)_spw')


def nk(s):
    return re.sub(r'[^a-z0-9+-]', '', s.lower())


def canon(s):
    """The star's catalogued identity, never the spelling.  The ledger spells
    one star both `HD 14055` and `HD~14055`, and a set of raw names counts it
    twice."""
    return IDMAP.get(nk(s), s)


# ============================================ 1. the crossings and their hosts
UNATTR = [r for r in LED['rows'] if not r['attributed']]
HOSTS = sorted({canon(r['star']) for r in UNATTR})
RAW = {r['star'] for r in UNATTR}
N_HOST = len(HOSTS)

# the discovery drift of each, from the measurement the recurrence test used,
# joined on the execution block and the crossing frequency -- never on a name
RECBY = {(c['eb'], round(c['freq_GHz'], 6)): c
         for c in REC['crossings'].values()}
DRIFT, NOJOIN = {}, []
for r in UNATTR:
    k = (r['eb'], round(r['freq'], 6))
    if k not in RECBY:
        NOJOIN.append((r['display'], r['freq']))
        continue
    DRIFT[k] = (RECBY[k].get('discovery') or {}).get('drift_Hz_s')
MEAS = [abs(v) for v in DRIFT.values() if v is not None]
N_NODRIFT = sum(1 for v in DRIFT.values() if v is None)
DRIFT_MIN = min(MEAS) if MEAS else 0.0

# ============================================ 2. the stack's own tolerance
# Recomputed exactly as stack_v408.py does: the MODE of the sub-MHz stacked
# channel widths over the MEDIAN inter-epoch span of the stacked groups.
_fine = [r['chanw'] for r in STK if r['chanw'] < 1e6]
CHANW_REF = float(max(set(_fine), key=_fine.count))
_spans = sorted(r['span_d'] for r in STK if r['span_d'] > 0)
SPAN_MED = _spans[len(_spans) // 2] if len(_spans) % 2 \
    else 0.5 * (_spans[len(_spans) // 2 - 1] + _spans[len(_spans) // 2])
DRIFT_TOL = CHANW_REF / (SPAN_MED * 86400.0)
N_IN_TOL = sum(1 for v in MEAS if v <= DRIFT_TOL)
# how long the slowest of them stays inside one reference channel
DRIFT_MIN_S = CHANW_REF / DRIFT_MIN if DRIFT_MIN else 0.0

# ====================== 3. coverage, and whether the stack holds the discovery
for g in GRP:
    g['_ebs'] = {mm.group(1) for p in g['paths']
                 for mm in [EBPAT.search(p)] if mm}
    g['_lo'] = min(g['sf_common_lo'], g['sf_common_hi'])
    g['_hi'] = max(g['sf_common_lo'], g['sf_common_hi'])
N_COV, N_INC = 0, 0
for r in UNATTR:
    fs, sk = r['freq_stellar'] * 1e9, canon(r['star'])
    gs = [g for g in GRP if g['skey'] == sk and g['_lo'] <= fs <= g['_hi']]
    if not gs:
        continue
    N_COV += 1
    if any(r['eb'] in g['_ebs'] for g in gs):
        N_INC += 1

# ============================== 4. the two multi-block counts, kept apart
BYSYS = collections.defaultdict(set)
BYSTAR = collections.defaultdict(set)
for r in CAT:
    BYSYS[r['system_id']].add(r['eb'])
    BYSTAR[nk(r['star_name'])].add(r['eb'])
EP_MULTI = sum(1 for v in BYSYS.values()
               if len({e for e in v if e in MJD}) > 1)
SYSOF = {nk(r['star_name']): r['system_id'] for r in CAT}
STK_CENSUS = [s for s in sorted({r['skey'] for r in STK}) if nk(s) in SYSOF]
N_STK_ONE_EB = sum(1 for s in STK_CENSUS if len(BYSTAR[nk(s)]) < 2)

# ===================================== 5. the haystack axis of the discussion
def union(iv):
    """Merged disjoint intervals.  min/max on the pair, because a descending
    spectral window writes its edges reversed."""
    out = []
    for a, b in sorted((min(x, y), max(x, y)) for x, y in iv):
        if out and a <= out[-1][1]:
            out[-1][1] = max(out[-1][1], b)
        else:
            out.append([a, b])
    return out


def total(iv):
    return sum(b - a for a, b in iv)


def clip_lo(iv, hi):
    return [(a, min(b, hi)) for a, b in iv if a < hi]


def edges(rows):
    return [(float(r['flo_GHz']), float(r['fhi_GHz'])) for r in rows]


FINE = [r for r in CAT if r['resolution_class'].startswith('fine')]
BTHREE = [r for r in CAT if r['band'] == '3']
U_ALL, U_A, U_B3 = (union(edges(s)) for s in (CAT, FINE, BTHREE))
HAY = total(clip_lo(U_ALL, HAY_HI_GHZ))
HAY_A = total(clip_lo(U_A, HAY_HI_GHZ))
B3_ABOVE = total(U_B3) - total(clip_lo(U_B3, HAY_HI_GHZ))
FREQ_LO_A = U_A[0][0]

# ------------------------------------------------------------------- checks
print('assertions')
ck('A1 the unattributed crossings are the ledger\'s own and the attribution '
   'split closes on the published crossing total',
   len(UNATTR) == (LED['summary']['n_unattributed'] if DRIVE != 1
                   else len(UNATTR) + 1)
   and len(UNATTR) + LED['summary']['n_attributed'] == int(texval('NCross')),
   '%d unattributed + %d attributed against \\NCross %s'
   % (len(UNATTR), LED['summary']['n_attributed'], texval('NCross')))

ck('A2 the hosts are len(set) over catalogued identities, the identity map is '
   'not vacuous, and every host is a star the stack combines',
   N_HOST == len({canon(r['star']) for r in UNATTR})
   and (len(RAW) > N_HOST if DRIVE != 2 else len(RAW) < N_HOST)
   and not set(HOSTS) - {r['skey'] for r in STK},
   '%d hosts from %d spellings; %d not stacked'
   % (N_HOST, len(RAW), len(set(HOSTS) - {r['skey'] for r in STK})))

ck('A3 the published stack drift tolerance reproduces from the stacked '
   'groups\' own median span and reference channel',
   abs(DRIFT_TOL / (texnum('StkDriftTolHzS') * (2.0 if DRIVE == 3 else 1.0))
       - 1.0) < 0.05
   and abs(SPAN_MED - float(texval('StkSpanMedD'))) < 1.0
   and abs(CHANW_REF / 1e3 - float(texval('StkRefChanKHz'))) < 1.0,
   'tol %.4f vs %.4f Hz/s, span %.1f d, channel %.1f kHz'
   % (DRIFT_TOL, texnum('StkDriftTolHzS'), SPAN_MED, CHANW_REF / 1e3))

ck('A4 every crossing joins to exactly one drift measurement, and not one '
   'measured drift is inside the stack tolerance',
   not NOJOIN and len(DRIFT) == len(UNATTR) and MEAS
   and (N_IN_TOL == 0 if DRIVE != 4 else N_IN_TOL > 0)
   and DRIFT_MIN > 100.0 * DRIFT_TOL,
   '%d joined, %d without a measured drift, slowest %.1f Hz/s = %.0fx the '
   'tolerance' % (len(DRIFT), N_NODRIFT, DRIFT_MIN, DRIFT_MIN / DRIFT_TOL))

ck('A5 coverage is not the obstacle: every crossing lies inside the '
   'stellar-frame coverage of a stacked group of its own star',
   N_COV == (len(UNATTR) if DRIVE != 5 else len(UNATTR) - 1),
   '%d of %d covered' % (N_COV, len(UNATTR)))

ck('A6 the stack is not independent of them: the covering group contains the '
   'crossing\'s own discovery block',
   (N_INC > 0 if DRIVE != 6 else N_INC == 0) and N_INC <= N_COV,
   '%d of %d covering stacks contain the discovery block' % (N_INC, N_COV))

ck('A7 the sub-haystack union is not the Band 3 union, and the Class A part '
   'is smaller still',
   abs((total(U_B3) - B3_ABOVE) - HAY) < 0.05
   and B3_ABOVE > (0.1 if DRIVE != 7 else 1e9)
   and HAY_A < HAY
   and round(FREQ_LO_A) == int(texval('SurvFreqLoA'))
   and FREQ_LO_A > HAY_HI_GHZ - 1.0,
   'union<%.0f GHz %.3f, Band 3 union %.3f of which %.3f above, Class A '
   '%.3f from %.3f GHz'
   % (HAY_HI_GHZ, HAY, total(U_B3), B3_ABOVE, HAY_A, FREQ_LO_A))

ck('A8 the multi-block systems and the stacked census stars are different '
   'sets and may not be printed as one',
   EP_MULTI == int(texval('EpMulti'))
   and len(STK_CENSUS) == int(texval('SxStkStarCensus'))
   and (EP_MULTI != len(STK_CENSUS) if DRIVE != 8
        else EP_MULTI == len(STK_CENSUS))
   and N_STK_ONE_EB > 0,
   '%d systems with >1 block, %d stacked census stars, %d of them with one '
   'census block' % (EP_MULTI, len(STK_CENSUS), N_STK_ONE_EB))

# ★★ Reported, not asserted, because the macro layer is written by another
#    generator and is legitimately mid-flight while the line mask is rebuilt:
#    \NUnattributed must agree with the ledger this generator reads.  A1
#    asserts the split against \NCross, which the mask cannot move, so a stale
#    \NUnattributed cannot pass unnoticed into the host count.
if texval('NUnattributed') != '%d' % len(UNATTR):
    print('\n  STALE MACRO LAYER  \\NUnattributed=%s against the ledger\'s '
          '%d.\n        Re-run the ledger macro generator, then this one.  '
          'The host count published\n        here is the LEDGER\'s.'
          % (texval('NUnattributed'), len(UNATTR)))

print('\nassertions failed: %d %s' % (len(fail), fail))
if fail and DRIVE is None:
    raise SystemExit('stack_r13: %d assertion(s) failed: %s'
                     % (len(fail), fail))

# ------------------------------------------------------------------- macros
m('SttNHostStar', '%d' % N_HOST)
m('SttDriftMinHzS', '%.0f' % DRIFT_MIN)
m('SttDriftMinMin', '%.0f' % (DRIFT_MIN_S / 60.0))
m('SttNIncDisc', '%d' % N_INC)
m('SttNStkOneEb', '%d' % N_STK_ONE_EB)
m('SttHayLoMHz', '%.0f' % HAY_LO_MHZ)
m('SttHayHiGHz', '%.0f' % HAY_HI_GHZ)
m('SttHayGHz', '%.1f' % HAY)
m('SttHayFineGHz', '%.1f' % HAY_A)

path = os.path.join(HERE, 'survey_numbers_round350%s.tex' % SUF)
with open(path, 'w') as fh:
    fh.write('%% GENERATED by stack_r13.py -- do not hand-edit.\n')
    fh.write('\n'.join(sorted(MACROS)) + '\n')
print('\nwrote %s (%d macros)' % (os.path.basename(path), len(MACROS)))
print('  hosts of the %d unattributed crossings: %d stars -- %s'
      % (len(UNATTR), N_HOST, ', '.join(HOSTS)))
print('  drift: slowest %.1f Hz/s, tolerance %.4f Hz/s, inside it %d; one '
      'channel in %.1f min' % (DRIFT_MIN, DRIFT_TOL, N_IN_TOL,
                               DRIFT_MIN_S / 60.0))
