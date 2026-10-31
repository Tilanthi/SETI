#!/usr/bin/env python3
r"""Round 560: THE MASTER COUNT TABLE -- the second panel of the block and
window ledger, and the one place every headline count in this paper is read
from.

WHY THIS EXISTS
---------------
Referee 2 tabulated eight pairs of figures in this manuscript that contradict
one another, and the request was not "pick one" but "print them all in one
table, say what each counts, and read every use site out of it".  Almost none
of them was wrong arithmetic.  Four were DIFFERENT SETS GIVEN THE SAME NAME in
running prose:

  * 39 against 37 against 36 "systems where confirmation was possible".  39 is
    the Class A systems with a second block more than a day from the first,
    37 is the subset whose second block covers the same stellar-frame
    frequency, and 36 is the complement of the same quantity over ALL 82
    surveyed systems rather than the 60 of the carrier experiment.  The
    quantity that bears on confirmation is the middle one, because a repeat
    epoch at another frequency confirms nothing; the paper now uses it
    everywhere and this table prints the other two beside it so the
    difference is visible rather than apparent.
  * 52 against "50 census plus 2 archival-tail" Class A crossings.  These are
    the same 52.  The one execution block that fails the quality criterion is
    also the only block in the survey with a coarse-channel crossing, so
    "quality-passing" and "Class A" select the same 52 rows -- a coincidence
    of sets that no sentence in the paper stated, and the reason a reader
    could not reconcile the two routes.  A2 asserts it.
  * 4.3 against 6.4 per cent for the cost of the line mask: the same masked
    bandwidth over the archival union and over the Class A union.  Both rows
    are printed with their denominators and the main text quotes the Class A
    figure only.

NOTHING HERE IS A NEW NUMBER
----------------------------
Every value this table prints is read out of the macro layer, so the table
cannot become a thirteenth set of counts; what the generator contributes is
the ARITHMETIC BETWEEN them, which is what a reader was being asked to do in
their head across eleven pages.  Two quantities are measured here rather than
read, because no generator published them:

  * `\MtCrossA`, the Class A crossing total, asserted equal both to the census
    and archival-tail rows that make it up and to the quality-passing total;
  * the per-system chance expectation, which answers the referee's minor 8.
    HD 14055 alone holds 8 of the 56 crossings, so a reader needs to see that
    no single star is anomalous.  The expectation for a system is the sum over
    its own windows of each window's own control-position exceedance rate,
    reduced by the share of that window's channels the line mask covers --
    which is the identical quantity `chance_v414.py` sums over the whole
    census.  A5 requires the per-system sums to reproduce the published total,
    so this is a decomposition of the paper's own expectation and not a second
    derivation of it.

Usage:  counts_r15.py [--drive N]      N = 0..9, 11 (and later drives up to 23)
        11 drives A4's new clause -- that the census block set is contained
        in the set the recurrence test reads -- on its own.
--drive 0 means "no perturbation, but do not write a path production reads".
"""
import collections
import csv
import glob
import json
import math
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROUND = 560

DRIVE = int(sys.argv[sys.argv.index('--drive') + 1]) if '--drive' in sys.argv \
    else None
SUF = '' if DRIVE is None else '_drive%d' % DRIVE


def suffixed(name):
    stem, ext = os.path.splitext(name)
    return stem + SUF + ext


OUT = os.path.join(HERE, suffixed('numbers/survey_numbers_round560.tex'))
TAB = os.path.join(HERE, suffixed('tab_counts.tex'))
CSVOUT = os.path.join(HERE, suffixed('persystem_chance_r15.csv'))

M, FAIL = {}, []
# A failure in a file this generator does not own must still stop the build,
# but it must not stop the TABLE from being written: the table is the fix, and
# withholding it would leave the manuscript with the stale one.  Such a check
# goes in OUTSIDE, which writes the products and then exits non-zero.
OUTSIDE = []


def m(k, v):
    assert k.isalpha(), 'a LaTeX macro name may contain letters only: ' + k
    assert k not in M, 'macro defined twice: ' + k
    M[k] = str(v)


def ck(tag, cond, detail='', outside=False):
    if not cond:
        (OUTSIDE if outside else FAIL).append(tag)
    print('  %-68s %s  %s' % (tag, 'PASS' if cond else 'FAIL', detail))


# --------------------------------------------------------- the macro layer
def published(macro):
    """The value of \\macro wherever the macro layer defines it.

    Takes the last non-empty definition in each file, because
    `\\providecommand{\\X}{}\\renewcommand{\\X}{1651}` is the house idiom for
    a macro a later round overrides and the first match is the empty
    placeholder -- which would make every comparison against that macro a
    comparison against the empty string, i.e. a check that cannot fail.
    Never reads this round's own file.
    """
    pat = re.compile(r'\\(?:new|renew|provide)command\*?\{\\%s\}\{([^}]*)\}'
                     % re.escape(macro))
    hits = []
    for fn in sorted(os.listdir(os.path.join(HERE, 'numbers'))):
        if not (fn.startswith('survey_numbers') and fn.endswith('.tex')):
            continue
        if '_drive' in fn or fn.startswith('survey_numbers_round%d' % ROUND):
            continue
        vals = [h for h in pat.findall(
            open(os.path.join(HERE, 'numbers', fn), errors='ignore').read()) if h.strip()]
        if vals:
            hits.append((fn, vals[-1].strip()))
    assert hits, 'macro %s is not defined by any round file' % macro
    seen = {v for _, v in hits}
    assert len(seen) == 1, ('%s has %d published values: %s'
                            % (macro, len(seen), hits))
    return hits[0][1]


def P(macro):
    return int(str(published(macro)).replace('\\,', '').replace(',', ''))


def PF(macro):
    return float(published(macro).replace('\\,', ''))


# ------------------------------------------------------------- the inputs
CAT = list(csv.DictReader(open(os.path.join(
    HERE, 'per_target_results_v3.99.csv'))))
LED = json.load(open(os.path.join(HERE, 'ledger.json')))['rows']

# every crossing's window, by position in frequency inside its own block and
# never by a name; a crossing whose block is not in the released catalogue is
# an archival-tail crossing, which is how the two sets are told apart
WINSPAN = collections.defaultdict(list)
for _i, _r in enumerate(CAT):
    _lo, _hi = float(_r['flo_GHz']), float(_r['fhi_GHz'])
    WINSPAN[_r['eb']].append((min(_lo, _hi), max(_lo, _hi), _i))


def window_of(row):
    f = (row.get('frame') or {}).get('f_topo', row['freq'])
    hit = [i for lo, hi, i in WINSPAN.get(row['eb'], ())
           if lo - 1e-6 <= f <= hi + 1e-6]
    return hit[0] if hit else None


WIN = {id(r): window_of(r) for r in LED}
if DRIVE == 1:
    # the archival tail must be identified by the catalogue's own window
    # spans, not assumed: fold the tail rows back in and the partition breaks
    WIN = {k: (0 if v is None else v) for k, v in WIN.items()}
CLS = {id(r): (CAT[WIN[id(r)]]['search_class'] if WIN[id(r)] is not None
               else 'A') for r in LED}
TAIL = [r for r in LED if WIN[id(r)] is None]
XA = [r for r in LED if CLS[id(r)] == 'A']
XB = [r for r in LED if CLS[id(r)] == 'B']
XA_CEN = [r for r in XA if WIN[id(r)] is not None]
XA_UN = [r for r in XA if not r['attributed']]
#: ★ XA_UN_CEN is completed after the chance generator's head is executed
#: below: a crossing the atmosphere accounts for leaves the counted set, and
#: the predicate that decides it is THAT generator's, read out of its own
#: namespace rather than written a second time from the same description.

FAILBLOCK = published('BqFailBlock').replace('\\_', '_')
FLAGGED = [r for r in LED if r['eb'] == FAILBLOCK]
QP = [r for r in LED if r['eb'] != FAILBLOCK]

# ================================================== the per-system chance
# The expectation is `chance_v414.py`'s own, decomposed by system.  Its head
# is executed rather than reimplemented, so the control ensembles, the window
# join, the mask list and the frame are the published ones by construction and
# cannot drift from them.  The head stops before any assertion and before any
# file is written.
_SRC = open(os.path.join(HERE, 'chance_v414.py')).read()
# ★★★ v4.18: THE MARKER IS STRUCTURAL, NOT THE EXACT SOURCE LINE.  It used to
# be the verbatim text
#     'P_UNMASKED = {i: PEXC[i] * (1.0 - MASK[i]) for i in PEXC}'
# and round 17 rewrote that statement -- the attribution share is now measured
# on the channels the control maxima land on (R2-3), so the comprehension
# carries `A_MEAS` and spans two lines.  The pin then failed with
# "chance_v414.py no longer exposes P_UNMASKED", which was false: it exposes
# it, differently spelled.
# ★ A diagnostic pinned on exact source text fails on a reformat and says
# something untrue when it does.  What this code needs is the END OFFSET of
# that statement, so it is found by locating the assignment and balancing the
# braces of the comprehension -- which is a property of the statement rather
# than of its wording.  The name is still required to appear exactly once, so
# a rename still stops the build, and the extracted text is asserted to parse
# and to assign the name.
_HEAD = 'P_UNMASKED = {'
assert _SRC.count(_HEAD) == 1, (
    'chance_v414.py no longer assigns P_UNMASKED exactly once (%d occurrences '
    'of %r)' % (_SRC.count(_HEAD), _HEAD))
_i = _SRC.index(_HEAD)
_j, _d = _SRC.index('{', _i), 0
while True:
    if _SRC[_j] == '{':
        _d += 1
    elif _SRC[_j] == '}':
        _d -= 1
        if _d == 0:
            break
    _j += 1
_j = _SRC.index('\n', _j)
_MARK = _SRC[_i:_j]
import ast as _ast
_chk = _ast.parse(_MARK)
assert (len(_chk.body) == 1 and isinstance(_chk.body[0], _ast.Assign)
        and getattr(_chk.body[0].targets[0], 'id', None) == 'P_UNMASKED'), (
    'the extracted statement is not a single assignment to P_UNMASKED: %r'
    % _MARK[:120])
_ARGV, _CWD = sys.argv, os.getcwd()
sys.argv = ['chance_v414.py']          # its own --drive must not see ours
os.chdir(HERE)
_G = {'__name__': 'chance_head',
      '__file__': os.path.join(HERE, 'chance_v414.py')}
exec(compile(_SRC.split(_MARK)[0] + _MARK, 'chance_v414.py', 'exec'), _G)
sys.argv, _ = _ARGV, os.chdir(_CWD)
assert [r['eb'] for r in _G['CAT']] == [r['eb'] for r in CAT], \
    'chance_v414 and this generator read different catalogues'
PU, IA = _G['P_UNMASKED'], _G['IA']
#: the atmospheric screen, applied here by the generator that owns it
_TLHIT = [r for r in XA_UN if _G['telluric'](r)]
_TLID = {id(r) for r in _TLHIT}
XA_UN_OPEN = [r for r in XA_UN if id(r) not in _TLID]
XA_UN_CEN = [r for r in XA_UN_OPEN if WIN[id(r)] is not None]
if DRIVE == 2:
    PU = {k: v * 0.5 for k, v in PU.items()}    # the decomposition must sum
                                                # to the published total

EXP = collections.defaultdict(float)
NWINA = collections.Counter()
SYSNAME = collections.defaultdict(set)
for i in IA:
    sid = CAT[i]['system_id']
    NWINA[sid] += 1
    SYSNAME[sid].add(CAT[i]['star_name'])
    if i in PU:
        EXP[sid] += PU[i]
OBS = collections.Counter()
for r in XA_UN_CEN:
    OBS[CAT[WIN[id(r)]]['system_id']] += 1

E_TOT = sum(EXP[s] for s in NWINA)
SYSROW = sorted(NWINA, key=lambda s: (-OBS[s], -EXP[s]))


def poisson_ge(k, lam):
    """P(at least k) for a Poisson mean lam."""
    if k <= 0:
        return 1.0
    acc, term = 0.0, math.exp(-lam)
    for j in range(k):
        acc += term
        term *= lam / (j + 1)
    return max(0.0, 1.0 - acc)


PGE = {s: poisson_ge(OBS[s], EXP[s]) for s in NWINA}
N_LOW = sum(1 for s in NWINA if PGE[s] < 0.05)
E_LOW = 0.05 * len(NWINA)
TOPSYS = max(NWINA, key=lambda s: (OBS[s], EXP[s]))
_TOP2_OBS = frozenset(sorted(NWINA, key=lambda s: -OBS[s])[:2])
_TOP2_WIN = frozenset(sorted(NWINA, key=lambda s: -NWINA[s])[:2])
if DRIVE == 3:
    PGE = dict(PGE, **{s: 1e-6 for s in NWINA})   # no single system may be
    N_LOW = len(NWINA)                            # anomalous

# ★ The star the referee names is found by counting, not by name.  The
#   display column spells one star two ways -- with and without a non-breaking
#   space -- because the archival-tail rows were added by a different
#   generator, so the key strips punctuation and case.  That spelling split is
#   itself why "8 of the 56" is not visible in the ledger as printed.
def _key(disp):
    return re.sub(r'[^a-z0-9]', '', disp.replace('~', ' ').lower())


UN_BY_STAR = collections.Counter(_key(r['display'])
                                 for r in LED if not r['attributed'])
ALL_BY_STAR = collections.Counter(_key(r['display']) for r in LED)
_topkey = max(UN_BY_STAR, key=UN_BY_STAR.get)
TOPSTAR_N = ALL_BY_STAR[_topkey]
TOPSTAR_UN = UN_BY_STAR[_topkey]
TOPSTAR = sorted({r['display'].replace('~', ' ') for r in LED
                  if _key(r['display']) == _topkey})[0]
NSPELL = len({r['display'] for r in LED if _key(r['display']) == _topkey})

# ============================================================= assertions
print('counts_r15: the master count table'
      + ('  [drive %d]' % DRIVE if DRIVE is not None else ''))
print('\nassertions')

N_RAW = P('EvNCrossRaw')
N_FLAG = P('EvNCrossFlag')
N_QP = P('EvNCrossQp')
N_ATTR = P('EvNAttrQp')
N_UNATTR = P('EvNUnattrQp')
N_RANK = P('EvNRankQp')
N_A_CEN = P('LdgNCrossA')
N_B = P('LdgNCrossB')
N_TAILX = P('CeNTailCross')
N_TLX = P('CeTlObsCut')
N_OBS = P('CeObs')
N_A = len(XA)
if DRIVE == 4:
    N_A += 1                           # the Class A total must close
# ★ GEN (v4.29 fold, E2 = (a)): \LdgNCrossA / \LdgNCrossB are the RELEASED CATALOGUE's class counts (ledger_v403,
#   54 = 50 A + 4 B); LED is the CENSUS ledger (51, all Class A: ALMA's flags take BD+05 1668's four Class B
#   crossings below the trigger).  Before the fold the class-B counts coincided (4 = 4) and several clauses below
#   used the catalogue's number for the census's.  The two now close through the field-repair delta
#   (v409_delta_r29.json, the record blockq B7 / statchain N8 / quality Q8 use), by class.
_D29 = json.load(open(os.path.join(HERE, 'v409_delta_r29.json')))
_D_FELL = {c: sum(1 for d in _D29['fell_detail'] if d['cls'] == c) for c in 'AB'}
_D_ROSE = {c: sum(1 for d in _D29['risen_attributed'] if d['cls'] == c) for c in 'AB'}
_D_ADD_A = len(_D29['restored_cls']) + len(_D29['tail_cls'])
assert set(_D29['restored_cls']) | set(_D29['tail_cls']) <= {'A'}, _D29['restored_cls'] + _D29['tail_cls']
N_B_CEN = len(XB)
if DRIVE == 22:
    _D_FELL = dict(_D_FELL, B=_D_FELL['B'] - 1)   # GEN: a delta that lost a fallen Class B row

ck('A1 the crossing total partitions into Class A and Class B, and the '
   'Class A part into census and archival-tail rows',
   N_A == len(XA_CEN) + N_TAILX and N_A + N_B_CEN == N_RAW
   and N_B - _D_FELL['B'] + _D_ROSE['B'] == N_B_CEN and len(TAIL) == N_TAILX,
   '%d A (%d census + %d tail) + %d B == %d; the catalogue\'s %d Class B less %d fallen plus %d risen'
   % (N_A, len(XA_CEN), N_TAILX, N_B_CEN, N_RAW, N_B, _D_FELL['B'], _D_ROSE['B']))
# ★★★ A1b: THE THIRD ROUTE TO 52, AND THE REASON THE REFEREE COULD NOT
#     RECONCILE THEM.  The released catalogue's own Class A crossing count is
#     also 52, over a DIFFERENT set of rows: the repair that produced the
#     adopted ledger took four released crossings below the trigger and
#     brought four others above it, two of them in archival-tail blocks.  So
#     three counts of 52 sit in this paper over three different sets, and
#     nothing said so.  The coincidence is asserted, and the caption states
#     it.
ck('A1b the released catalogue reaches the same Class A total over a '
   'different set of rows, and the difference is the repair',
   # GEN (v4.29 fold): "N_A_CEN == N_A" asserted the COINCIDENCE of the day (52 = 52); after the fold the two
   # totals differ (50 against 51) and the invariant is the stated reason: the difference IS the repair.
   N_A_CEN - _D_FELL['A'] + _D_ROSE['A'] + _D_ADD_A == N_A and len(XA_CEN) != N_A_CEN,
   'released catalogue %d Class A, less %d fallen, plus %d risen and %d restored or tail, is the adopted '
   'ledger %d (%d census + %d tail)'
   % (N_A_CEN, _D_FELL['A'], _D_ROSE['A'], _D_ADD_A, N_A, len(XA_CEN), N_TAILX))
# ★★★ A2 IS M2(b)'s ANSWER.  "52 Class A crossings" and "52 quality-passing
#     crossings" are the same rows, because the one block that fails the
#     quality criterion is the only block in the survey holding a
#     coarse-channel crossing.  Until this is said, a reader has two routes to
#     52 and no reason to believe they meet.  Driven by --drive 4.
ck('A2 the quality-passing crossings and the Class A crossings are the same '
   'rows, because the failing block holds every Class B crossing',
   N_A == N_QP and {id(r) for r in QP} == {id(r) for r in XA}
   # GEN (v4.29 fold): census Class B (0 after the fold), and the failing block may now hold none
   and {r['eb'] for r in FLAGGED} <= {FAILBLOCK}
   and len(FLAGGED) == N_FLAG == N_B_CEN,
   '%d == %d, and all %d flagged crossings are the %d Class B ones in '
   '%s' % (N_A, N_QP, len(FLAGGED), N_B_CEN, FAILBLOCK.replace('_', '\\_')))
ck('A3 the quality-passing crossings partition into attributed and '
   'unattributed, and the unattributed into census and archival-tail',
   N_ATTR + N_UNATTR == N_QP
   and N_OBS + N_TAILX + N_TLX == N_UNATTR
   and len(XA_UN) == N_UNATTR and len(_TLHIT) == N_TLX
   and len(XA_UN_CEN) == N_OBS
   and N_RANK <= N_UNATTR,
   '%d + %d == %d; %d census + %d tail + %d atmospheric == %d unattributed, '
   '%d of them outranking every control'
   % (N_ATTR, N_UNATTR, N_QP, N_OBS, N_TAILX, N_TLX, N_UNATTR, N_RANK))
# ★★★ r28 (R2-M6, R2-m1; Ruling R4): THE COUNTS OVER THE PRIMARY CENSUS.
# The abstract, Sec. 2, Sec. 4.3 and the Conclusions quote crossing counts
# over the census -- the set every expectation and every limit is formed
# over -- and report the archival tail once, apart.  A census crossing is
# one a catalogued window of its own block contains (`window_of`, the
# position-equivalent key A1 separates the tail with).  A15 closes the
# census counts on the published ones; drive 19 counts a tail crossing in.
CS_X = [r for r in LED if WIN[id(r)] is not None]
if DRIVE == 19:
    CS_X = CS_X + TAIL[:1]
CS_QP = [r for r in CS_X if r['eb'] != FAILBLOCK]
CS_ATTR = [r for r in CS_QP if r['attributed']]
CS_UN = [r for r in CS_QP if not r['attributed']]
ck('A15 the census crossings are the ledger less the archival tail; their '
   'quality-passing part is the census Class A rows, and its unattributed '
   'part is the chance comparison\'s count plus the atmospheric one',
   len(CS_X) + len(TAIL) == N_RAW and len(CS_X) == len(XA_CEN) + N_B_CEN
   and {id(r) for r in CS_QP} == {id(r) for r in XA_CEN}
   and len(CS_ATTR) + len(CS_UN) == len(CS_QP)
   and len(CS_UN) == N_OBS + N_TLX,
   '%d census + %d tail == %d; %d quality-passing = %d attributed + %d '
   'unattributed (%d compared + %d atmospheric)'
   % (len(CS_X), len(TAIL), N_RAW, len(CS_QP), len(CS_ATTR), len(CS_UN),
      N_OBS, N_TLX))
# ★★ r28: THE VISIBILITY-FIT COUNTS OF Sec. 4.5 WERE OVER ANOTHER SET.
# `ledger_v403.csv` -- the fit ledger behind \LgNFit and \LgNLocalCor --
# is the RELEASED crossing list: four of its rows fell below the trigger
# in the repair and four current crossings (two of them the tail's) are
# not in it, so "51 of the 56" counted fits of crossings this paper no
# longer reports.  Joined to the adopted ledger on block + topocentric
# frequency (block alone where each list holds one crossing in it) and
# counted over the census.  A16 proves the old pair is the fit ledger's
# own count, so the two can be told apart.
VF = list(csv.DictReader(open(os.path.join(HERE, 'ledger_v403.csv'))))
_VFEB = collections.Counter(v['eb'] for v in VF)
_LDEB = collections.Counter(r['eb'] for r in LED)


def _vfit(r):
    f = (r.get('frame') or {}).get('f_topo', r['freq'])
    c = [v for v in VF if v['eb'] == r['eb'] and v['f_cross_GHz']
         and abs(float(v['f_cross_GHz']) - f) < 5e-4]
    if not c and _VFEB[r['eb']] == 1 and _LDEB[r['eb']] == 1:
        c = [v for v in VF if v['eb'] == r['eb']]
    assert len(c) <= 1, ('two fit rows for one crossing', r['eb'], f)
    return c[0]['visibility_status'] if c else 'no fit'


CS_VIS = collections.Counter(_vfit(r) for r in CS_X)
CS_VFIT = CS_VIS['localised'] + CS_VIS['not localised']
_VF_ALL = collections.Counter(v['visibility_status'] for v in VF)
ck('A16 the fit counts the paper printed are the released list\'s, and the '
   'census ones partition the census crossings',
   _VF_ALL['localised'] + _VF_ALL['not localised'] == P('LgNFit')
   and _VF_ALL['localised'] == P('LgNLocalCor')
   and sum(CS_VIS.values()) == len(CS_X)
   and set(CS_VIS) <= {'localised', 'not localised', 'untested', 'no fit'},
   'released list %d fitted / %d localised; census %d fitted / %d '
   'localised / %d untested / %d never fitted, of %d'
   % (_VF_ALL['localised'] + _VF_ALL['not localised'],
      _VF_ALL['localised'], CS_VFIT, CS_VIS['localised'],
      CS_VIS['untested'], CS_VIS['no fit'], len(CS_X)))
# ★ r28 (R2-m13): the crossing dynamic spectra deposited, keyed on block
# + topocentric frequency to 1 kHz; every ledger crossing must have one.
SPX = list(csv.DictReader(open(os.path.join(
    HERE, 'r28inputs', 'crossing_spectra_index_r28.csv'))))
_SPK = {(s['eb'], round(float(s['f_topo_GHz']), 6)) for s in SPX
        if s['file']}
SP_MISS = [r for r in LED if (r['eb'], round((r.get('frame') or {})
           .get('f_topo', r['freq']), 6)) not in _SPK]
if DRIVE == 20:
    SP_MISS = SP_MISS + LED[:1]
ck('A17 every crossing of the ledger has its deposited dynamic spectra',
   not SP_MISS, '%d of %d; missing %s' % (len(LED) - len(SP_MISS), len(LED),
                                          [r['eb'] for r in SP_MISS]))
# ★ v4.29 (push29): A17 keys on block + frequency only, so a spectrum cut from
#   a PRE-re-flag product passed it: CD-57 1054 X5aa4's deposited row carried
#   T* 5.1083 while the census reads 5.6924.  The deposit must be cut from the
#   product the census reads, so each row's T* must be its crossing's.
_LEDK = {(r['eb'], round((r.get('frame') or {}).get('f_topo', r['freq']), 6)): r
         for r in LED}
SP_STALE = [s['eb'] for s in SPX if s['file'] and (s['eb'], round(float(
    s['f_topo_GHz']), 6)) in _LEDK and abs(float(s['tstar']) - float(_LEDK[(
        s['eb'], round(float(s['f_topo_GHz']), 6))]['tstar'])) > 5e-4]
if DRIVE == 23:
    SP_STALE = SP_STALE + [SPX[0]['eb']]
ck('A17c every deposited crossing spectrum is cut from the product the census '
   'reads (its T* is the ledger crossing\'s, to 5e-4)', not SP_STALE,
   '%d rows; stale %s' % (len([s for s in SPX if s['file']]), SP_STALE))
# ★★★ A4 IS M2(a)'s ANSWER: the three figures the manuscript used
#     interchangeably are three nested sets, and the nesting is what makes
#     them different quantities rather than contradictory counts.  A repeat
#     epoch at another frequency confirms nothing, so the middle set is the
#     one the paper quotes.
N_SYSA = P('NSysClassA')
N_SEP = P('ScSysIndep')
N_NOSEP = P('ScSysNoConf')
N_CONF = P('ZcConfSysDay')
N_NOCONF = P('ZcNoRepSys')
N_CONFYR = P('ZcConfSysYr')
#: the census-only pair, kept so that its own closure is still proved and the
#: two block sets can be seen to be nested rather than merely different
N_CENCONF = P('RcConfSysDay')
N_CENNOCONF = P('ZcCenNoRepSys')
N_CONFALL = P('RcConfSysAllDay')
N_NOCONFALL = P('RcNoRepSysAll')
N_SYSALL = P('NSystems')
if DRIVE == 5:
    N_CONF = N_SEP + 1
if DRIVE == 11:
    N_CENCONF = N_CONF + 1          # census must not exceed the enlarged set
ck('A4 the confirmation counts are three nested sets over two populations, '
   'each complement closes on its own population, and the census block set '
   'is contained in the set the recurrence test reads',
   N_SEP + N_NOSEP == N_SYSA and N_CONF + N_NOCONF == N_SYSA
   and N_CENCONF + N_CENNOCONF == N_SYSA
   and N_CONFALL + N_NOCONFALL == N_SYSALL
   and N_CONFYR <= N_CONF <= N_SEP <= N_CONFALL
   and N_CENCONF <= N_CONF,
   'Class A: %d separated / %d at the same frequency over the recurrence '
   'test block set (%d over the census alone) / %d of those over a '
   'year, against %d systems; all systems: %d of %d'
   % (N_SEP, N_CONF, N_CENCONF, N_CONFYR, N_SYSA, N_CONFALL, N_SYSALL))
# ★★ A5 is what makes the per-system column a decomposition of the paper's
#    own expectation rather than a second one.  Driven by --drive 2.
ck('A5 the per-system expectations sum to the published chance expectation',
   abs(E_TOT - PF('CeExp')) < 0.05 and sum(OBS.values()) == N_OBS
   and len(NWINA) == N_SYSA,
   '%.2f against the published %s over %d systems; %d observed'
   % (E_TOT, published('CeExp'), len(NWINA), sum(OBS.values())))
# ★★★★ A6 IS MINOR 8.  One star holds 8 of the 56 crossings, and the
#      question is whether that is a property of the star or of its coverage.
#      It is the latter: it holds the most Class A windows in the survey, and
#      no system in the sample departs from its own control positions by more
#      than chance allows over 60 trials.  If one ever does, the build stops.
#      Driven by --drive 3.
# ★ GEN (v4.29 fold, E3): A6 also required the system with the most CENSUS Class A unattributed crossings to be
#   the star with the most LEDGER crossings (HD 14055 both, before).  With HD 14055 X29ae / X2c3bb gone the census
#   leader is ALMA J1537 (5, p=0.14) and the ledger leader HD 14055 (4 census + the 2 archival-tail) -- a population
#   fact, not the claim.  The claim is that NO system departs from its controls; both leaders are now checked
#   against the same allowance, and A6b reads the top STAR's own system (TSYS) instead of assuming it is TOPSYS.
TSYS = sorted({CAT[WIN[id(r)]]['system_id'] for r in LED
               if _key(r['display']) == _topkey and WIN[id(r)] is not None})
assert len(TSYS) == 1, ('the top star\'s census crossings lie in %d systems' % len(TSYS), TSYS)
TSYS = TSYS[0]
ck('A6 no single system holds more unattributed crossings than its own '
   'control positions allow, over the whole sample',
   N_LOW <= max(1, int(round(E_LOW))) and OBS[TOPSYS] <= 2.0 * EXP[TOPSYS]
   and _TOP2_OBS == _TOP2_WIN and OBS[TSYS] <= 2.0 * EXP[TSYS]
   and TOPSTAR_N == TOPSTAR_UN,
   '%d of %d systems reach p<0.05 against %.1f expected; the system holding '
   'the most crossings is %s, %d observed against %.2f expected over its '
   '%d Class A windows (p=%.2f), and the two systems holding the most '
   'crossings are the two carrying the most windows (%s)'
   % (N_LOW, len(NWINA), E_LOW,
      sorted(SYSNAME[TOPSYS])[0], OBS[TOPSYS], EXP[TOPSYS],
      NWINA[TOPSYS], PGE[TOPSYS],
      ', '.join(sorted(SYSNAME[s])[0] for s in _TOP2_WIN)))
# ★ A6b: the star-keyed and the system-keyed views of the same ledger must
#   agree, and the reason "8 of the 56" is invisible in the printed ledger is
#   that one star is spelled two ways in it.  Naming that keeps a later reader
#   from re-deriving the discrepancy.
ck('A6b the star holding the most crossings carries all of them '
   'unattributed, and the ledger spells it more than one way',
   TOPSTAR_N == TOPSTAR_UN == OBS[TSYS] + N_TAILX and NSPELL > 1,
   '%s: %d crossings, all unattributed, %d in census windows and %d in '
   'archival-tail blocks, under %d spellings in the ledger'
   % (TOPSTAR, TOPSTAR_N, OBS[TSYS], N_TAILX, NSPELL))
# ★★ A7: THE MASK COST IS ONE BANDWIDTH OVER TWO DENOMINATORS, and neither
#    figure may be printed without saying which.  The Class A figure must be
#    the larger, because the mask is evaluated on the fine-channel windows
#    and the archival union is wider than the Class A one.
MASK_A = PF('MkMaskAPct')
MASK_ALL = PF('FrMaskPct')
MASK_GHZ = PF('MkMaskAGHz')
UNION_A = PF('CvUnionA')
UNION_ALL = PF('DnuAB')
if DRIVE == 6:
    MASK_ALL = MASK_A + 1.0
ck('A7 the two mask percentages are one masked bandwidth over two unions, '
   'and the Class A figure is the larger',
   MASK_A > MASK_ALL and UNION_A < UNION_ALL
   and abs(100.0 * MASK_GHZ / UNION_A - MASK_A) < 0.2,
   '%.2f GHz over %.1f GHz is %.1f per cent and over %.1f GHz is %.1f per '
   'cent' % (MASK_GHZ, UNION_A, MASK_A, UNION_ALL, MASK_ALL))
# ★ A8: every count the table prints must already be a published macro, or
#   the master table becomes the thirteenth set of numbers it exists to
#   prevent.  The two exceptions are declared and both are asserted above.
# ★★★★ A9 IS WHAT KEEPS A SENTENCE FROM QUOTING THE WRONG MEMBER OF A NESTED
#      PAIR.  Rows 3.1 and 3.1.1 are both true, and only the inner one is a
#      confirmation figure, because a later block at a frequency the first did
#      not cover confirms nothing.  The any-frequency pair -- \ScSysIndep and
#      its complement \ScSysNoConf -- is therefore a ledger count and nothing
#      else, and a sentence about confirmation must use \ZcConfSysDay or
#      \ZcNoRepSys -- the confirmability of the block set the recurrence test
#      actually reads, which is what confset_r18.py publishes.  A4 already proves the two pairs are nested; nesting is
#      exactly why no gate could see that the running text had taken the
#      outer one, so the USE SITES are checked here and not only the values.
LEDGER_ONLY = {'ScSysIndep': 'ZcConfSysDay', 'ScSysNoConf': 'ZcNoRepSys'}
PROSE = sorted(glob.glob(os.path.join(HERE, 'sections', '*.tex'))
               + glob.glob(os.path.join(HERE, 'technosignatures_40pc_v*.tex')))
assert PROSE, 'A9 scanned no manuscript file, so it could not have failed'
_bad = []
for _fn in PROSE:
    for _ln, _line in enumerate(open(_fn, errors='ignore'), 1):
        _line = re.sub(r'(?<!\\)%.*$', '', _line)
        for _mac, _use in sorted(LEDGER_ONLY.items()):
            if re.search(r'\\%s(?![A-Za-z])' % _mac, _line):
                _bad.append('%s:%d \\%s should be \\%s'
                            % (os.path.basename(_fn), _ln, _mac, _use))
if DRIVE == 8:
    _bad.append('(drive 8) sections/none.tex:0 \\ScSysIndep')
ck('A9 the any-frequency pair is a ledger count only, so no sentence quotes '
   'it as a confirmation figure',
   not _bad,
   'clean over %d manuscript files' % len(PROSE) if not _bad
   else '%d use site(s), each a one-token swap: %s' % (len(_bad),
                                                       '; '.join(_bad)),
   outside=True)
if DRIVE == 7:
    FAIL.append('A0 deliberate failure, drive 7')

# ★★★★ A10 AND A11 ARE PROSE CHECKS, AND THEY EXIST BECAUSE THE DEFECTS THEY
#      CATCH WERE IN A SHIPPED PDF WITH EVERY VALUE GATE GREEN.  Both are
#      CORRECT MACROS INSIDE FALSE SENTENCES, which is a class A9 is the only
#      other instrument for, and A9 asks which macro was cited rather than
#      what the sentence around it says.
#
#  A10  TAIL vs EXTENSION.  Sec. 3 defines two disjoint block sets -- the
#       archival TAIL (searched after the census sweep closed, toward census
#       stars, in no expectation) and the archival EXTENSION (searched after
#       the statistic and the mask were fixed, in no census statistic).
#       Conclusion 4 placed the two tail crossings "in the archival
#       extension", in the one sentence referee 2 quoted back at us, while
#       Sec. 5.6.2 measures the extension at ZERO unattributed crossings.  So:
#       no sentence citing a tail macro may contain the word "extension", and
#       no sentence citing an extension macro may contain the word "tail".
#       The two words are the only thing that tells the sets apart in print.
#
#  A11  COINCIDENCE vs ATTRIBUTION.  21 crossings fall inside the mask; 18 of
#       them are attributed, the other 3 being the sulphur monoxide
#       coincidences that Appendix C reports rather than acts on.  Sec. 5.4
#       printed the ATTRIBUTION count with the COINCIDENCE verb ("18 of all 56
#       crossings land on a catalogued transition"), which is referee 1's own
#       item 5 -- attribution is not identification -- made in our voice.  So
#       an attribution macro may not stand in a sentence that uses a
#       coincidence verb unless the coincidence count is in the same sentence,
#       and the coincidence count may not stand in a sentence that says
#       "attributed" unless an attribution macro is in it too.
#
# Sentences, not lines: both defects spanned a line break.  The scan is over
# the SOURCE, because that is where the fix has to live; the typeset stream is
# `prosegate_selfref`'s instrument and shares nothing with this one.
_TAILMAC = ('CeNTailCross', 'CeNTailCrossWord', 'CeNWinTail', 'CeTailStar',
            'LdgExtTail', 'LdgExtTailWin')
_EXTMAC = ('LdgExtEB', 'LdgExtWin', 'LdgExtStars', 'LdgExtScope',
           'LdgExtSearched', 'LdgExtWithheldWin', 'ExtNCross', 'ExtCrossPct',
           'ExtNStageOne', 'ExtNRankOneNonBp')
_ATTRMAC = ('EvNAttrQp', 'CsNAttrQp', 'MkAttr', 'NAttributed')
_COINCMAC = ('MkNCoinc',)
# The VERBS of coincidence, as word-bounded patterns.  "coincidence" is
# deliberately NOT one of them: "rest on the coincidence alone" is a statement
# about the evidence an attribution has, not a count of coincidences, and it is
# the sentence referee 1's item 5 asked for.  A bare substring test made this
# clause fire on exactly that sentence in two files -- a check that fails on
# good text gets whitelisted, which is a way of having no check.
_COINCVERB = (r'\bcoincides?\b', r'\blands? on\b', r'\bfalls? within\b',
              r'inside the mask', r'within that distance')


def _sentences(path):
    """(first line number, text) for each sentence of a manuscript file."""
    txt, lineno = [], []
    for _n, _l in enumerate(open(path, errors='ignore'), 1):
        _l = re.sub(r'(?<!\\)%.*$', '', _l)
        txt.append(_l)
        lineno.append(_n)
    flat = ''.join(txt)
    # map character offset -> line number
    at, off = [], 0
    for _n, _l in zip(lineno, txt):
        at.append((off, _n))
        off += len(_l)

    def line_of(pos):
        ln = at[0][1]
        for o, n in at:
            if o > pos:
                break
            ln = n
        return ln
    out, start = [], 0
    for mm in re.finditer(r'(?<![A-Z])\.(?=[\s~]|$)|\\par\b|\n\s*\n', flat):
        out.append((line_of(start), flat[start:mm.end()]))
        start = mm.end()
    out.append((line_of(start), flat[start:]))
    return [(n, s) for n, s in out if s.strip()]


def _cites(sentence, macros):
    return [mc for mc in macros
            if re.search(r'\\%s(?![A-Za-z])' % mc, sentence)]


_mix = []
for _fn in PROSE:
    for _ln, _s in _sentences(_fn):
        _flatS = ' '.join(_s.split())
        _low = _flatS.lower()
        if _cites(_s, _TAILMAC) and 'extension' in _low:
            _mix.append('%s:%d a tail count in a sentence saying "extension"'
                        % (os.path.basename(_fn), _ln))
        if _cites(_s, _EXTMAC) and 'tail' in _low:
            _mix.append('%s:%d an extension count in a sentence saying "tail"'
                        % (os.path.basename(_fn), _ln))
if DRIVE == 12:
    # the defect this clause was written for, restored verbatim
    _mix += ['(drive 12) 07_conclusions.tex:32 \\CeNTailCrossWord{} Class~A '
             'in the archival extension']
if DRIVE == 13:
    _mix += ['(drive 13) 05_results.tex:777 \\ExtNCross{} crossings in the '
             'archival tail']
ck('A10 no sentence puts an archival-tail count in the archival extension, '
   'or an extension count in the tail',
   not _mix,
   'clean over %d manuscript files' % len(PROSE) if not _mix
   else '%d sentence(s): %s' % (len(_mix), '; '.join(_mix)),
   outside=True)

_verb = []
_nattr = _ncoinc = 0
for _fn in PROSE:
    for _ln, _s in _sentences(_fn):
        _flatS = ' '.join(_s.split())
        _low = _flatS.lower()
        _a, _c = _cites(_s, _ATTRMAC), _cites(_s, _COINCMAC)
        _nattr += len(_a)
        _ncoinc += len(_c)
        _hit = [mm.group(0) for mm in
                (re.search(v, _low) for v in _COINCVERB) if mm]
        if _a and _hit and not _c:
            _verb.append('%s:%d \\%s with "%s" and no coincidence count'
                         % (os.path.basename(_fn), _ln, _a[0], _hit[0]))
        # ★★★ v4.27: `'attribut' in _low` ALSO MATCHES **"unattributed"**, which
        # is the OPPOSITE of what this clause is about -- and it fired on a
        # correct sentence the moment a length cut joined two sentences with a
        # semicolon: *"the mask places \MkNCoinc of the \EvNCrossQp within
        # that distance of a catalogued transition; a further \SoNCrossWord
        # fall on transitions of a species no debris disc has been shown to
        # carry ... and stay UNattributed"*.  A11's purpose -- never print the
        # coincidence count as a count of attributions -- was not violated;
        # the substring was.  This is the same defect as `chance_v414`'s A18
        # floor, where `'\CeAddLim' in s` matches `\CeAddLimNear`, and it is
        # the third substring-match defect of round 26.  A gate must not fail
        # on a correct sentence.  Drive 15 still demonstrates the clause.
        if _c and re.search(r'(?<!un)(?<!non-)attribut', _low) and not _a:
            _verb.append('%s:%d \\%s in a sentence saying "attributed"'
                         % (os.path.basename(_fn), _ln, _c[0]))
if DRIVE == 14:
    _verb += ['(drive 14) 05_results.tex:443 \\NAttributed{} of all '
              '\\NCross{} crossings land on a catalogued transition']
if DRIVE == 15:
    _verb += ['(drive 15) app_I_linemask.tex:134 \\MkNCoinc{} attributed']
ck('A11 the attributed count is never printed as a count of coincidences, '
   'nor the coincidence count as a count of attributions',
   not _verb and _nattr and _ncoinc,
   'clean: %d attribution and %d coincidence use sites over %d files'
   % (_nattr, _ncoinc, len(PROSE)) if not _verb
   else '%d sentence(s): %s' % (len(_verb), '; '.join(_verb)),
   outside=True)

# ================================================================ macros
m('MtCrossA', '%d' % N_A)
m('MtCrossACen', '%d' % len(XA_CEN))
m('CsNCross', '%d' % len(CS_X))
m('CsNCrossQp', '%d' % len(CS_QP))
m('CsNAttrQp', '%d' % len(CS_ATTR))
m('CsNUnattrQp', '%d' % len(CS_UN))
m('CsNVisFit', '%d' % CS_VFIT)
m('CsNVisLocal', '%d' % CS_VIS['localised'])
m('DaNSpecCross', '%d' % (len(LED) - len(SP_MISS)))
#: ★ r28 (integrate, note 15): the spectra file's size, so Data Availability
#: can state it without a typed number.  The sum of the deposited files' own
#: byte counts, as the index records them (the zip stores the .npz files,
#: already compressed, so the archive is this size to <0.1 per cent: 217.2 MB
#: measured on the built zip).  Every ledger crossing's file must carry a
#: positive size, or the sum understates it.
_SPB = [int(s['bytes'] or 0) for s in SPX if s['file']]
ck('A17b every deposited crossing spectrum carries its byte count',
   bool(_SPB) and all(b > 0 for b in _SPB),
   '%d files, %.1f MB' % (len(_SPB), sum(_SPB) / 1e6))
m('DaSpecFileMB', '%.0f' % (sum(_SPB) / 1e6))
m('MtNSysChance', '%d' % len(NWINA))
m('MtTopStar', TOPSTAR.replace(' ', '~'))
m('MtTopStarNCross', '%d' % TOPSTAR_N)
m('MtTopStarNUnattr', '%d' % TOPSTAR_UN)
m('MtTopSysNWin', '%d' % NWINA[TOPSYS])
m('MtTopSysObs', '%d' % OBS[TOPSYS])
m('MtTopSysExp', '%.1f' % EXP[TOPSYS])
m('MtNSysLowP', '%d' % N_LOW)
m('MtNSysLowPExp', '%.0f' % E_LOW)

# ================================================================== table
# ★★★★ r20-final: THE ARTICLE PRINTS THE ACCOUNTING ROWS AND THE FILE CARRIES
# THE ITEMISATION.  Glenn approved taking this table and the crossing ledger
# out of the typeset article; measured, the two are worth one page between
# them, and an in-paper remnant of each is free.  So the ROWS ARE DECLARED
# ONCE, each with a flag saying whether the article prints it, and the two
# outputs -- the LaTeX fragment and the machine-readable ancillary file -- are
# both written from that one list.  A second list, or a hand-trimmed table,
# is how an accounting table and its own data file come to disagree.
# ★★★ What stays in the article is what the text's sums close on: the
# crossing total and its two classes, the quality-passing total and its
# attribution split, the census comparison against chance, the system count
# with the confirmable set and the set for which confirmation is impossible,
# and the union bandwidth with the mask's share of it.  What moves is the
# itemisation: the census/archival-tail decomposition of row 1.1, the
# rank-leading and recovered counts of row 2.2 (both of which the text and
# Table~5 carry), the any-frequency epoch pair of row 3.1/3.2 -- which A9
# forbids any sentence from quoting in any case -- and the census-blocks-only
# variant of row 3.3.
# ★★ AND THREE CHECKS THAT EXIST BECAUSE TRIMMING A NESTED TABLE BREAKS IT
# SILENTLY: a printed row whose label begins with the continuation mark must
# have its parent printed (A12); no printed note may point at a row the
# article does not print (A13, and row 2.2's note does point at two); and
# every row of the table must be in the file, with the same value, resolved
# to plain text with nothing of LaTeX left in it (A14).
#: ★ r27: Table A2 grew by nine set-definition rows this round and no
#: longer fits one column; it is a table* now, and the widths are fractions
#: of \linewidth, which is the full text width inside a table* (\columnwidth
#: is not reset there in this class).
HEAD = ('\\begin{tabular}'
        '{@{}r@{~}p{0.405\\linewidth}r@{\\,\\,}'
        'p{0.325\\linewidth}@{}}\n')


def _close(name, lhs, rhs):
    """One identity among the unattributed sets, closed on the macro layer.

    ★ Each of these was reconstructible only by a reader willing to subtract
    guesses.  Closed here, a set cannot change size without the build saying
    which other set it no longer agrees with.  A3g fails as written on the
    shipped numbers, and that is this function's first result rather than a
    reason to weaken it: \\TlBandNSub counts the hold-out on the sky-frame
    offset where the paper's rule is the star's own frame.
    """
    lv = P(lhs)
    rv = sum(P(t) for t in rhs)
    ck('A%s the unattributed set register closes: %s == %s'
       % (name, lhs, ' + '.join(rhs)), lv == rv,
       '%d against %d' % (lv, rv))


_close('3a', 'MkUnattr', ['EvNUnattrQp', 'EvNUnattrFlag'])
# GEN (v4.29 fold): 3a2 closed the released catalogue's Class B count on the census's flagged unattributed count
# (4 = 4 before the fold).  ALMA's flags take all four below the trigger, so it closes through the delta.
ck('A3a2 the unattributed set register closes: LdgNCrossB less the fallen Class B rows == EvNUnattrFlag',
   P('LdgNCrossB') - _D_FELL['B'] + _D_ROSE['B'] == P('EvNUnattrFlag'),
   '%d - %d + %d against %d' % (P('LdgNCrossB'), _D_FELL['B'], _D_ROSE['B'], P('EvNUnattrFlag')))
_close('3b', 'MkUnattr', ['RcNExclPoss', 'RcNUnread'])
_close('3c', 'RcNExclPoss', ['RcNExcl', 'RcNWithheld'])
_close('3d', 'MkUnattr', ['PaNCovWinCross', 'WdNNoCov'])
_close('3e', 'MkUnattr', ['ImNScreen', 'CeNTailCross'])
_close('3f', 'EvNUnattrQp', ['CeObs', 'CeNTailCross', 'CeTlObsCut'])
_close('3g', 'TlBandNSub', ['ImNScreen', 'HoNUnattr'])
#: r28 (m6): rows 3.1 + 3.2 and rows 3.3 + 3.4 each partition row 3 -- the
#: printed note of row 3 says so, so the build asserts it.
for _nm, _parts in (('3h', ('ZcConfSysDay', 'ZcNoRepSys')),
                   ('3i', ('ScSysIndep', 'ScSysNoConf'))):
    ck('A%s the system partition closes: NSysClassA == %s'
       % (_nm, ' + '.join(_parts)),
       P('NSysClassA') == sum(P(_t) for _t in _parts)
       + (1 if DRIVE == 21 and _nm == '3h' else 0),
       '%d against %d' % (P('NSysClassA'), sum(P(_t) for _t in _parts)))

CONT = '\\ldots{}'                   # the continuation mark of a child row

# (row number, label, value, note, printed in the article)
SPEC = [
    #: ★★ r28 (R2-M6, Ruling R4): ROW 1 IS SPLIT INTO THE CENSUS AND THE
    #: ARCHIVAL TAIL, and every count below row 1.1 is over the census.
    ('1', 'Threshold crossings at $T_\\star\\ge5$',
     r'\EvNCrossRaw', 'rows 1.1 and 1.2', True),
    ('1.1', CONT + ' in the primary census', r'\CsNCross',
     'rows 1.1.1 and 1.1.2', True),
    ('1.1.1', 'Class~A, fine channels', r'\MtCrossACen',
     'the carrier experiment', True),
    #: GEN (v4.29 fold): the census's Class B count (row 1.1 is the census), not the released catalogue's
    #: \LdgNCrossB; ALMA's flags take the failing block's four below the trigger, and the section the note
    #: pointed to (sec:bdblock) is gone from the text.
    ('1.1.2', 'Class~B, coarse channels', r'\EvNCrossFlag',
     'the released catalogue\'s \\LdgNCrossB, all in the one block that fails the quality criterion, '
     'fall below the trigger on recalibration', True),
    ('1.2', CONT + ' in the archival tail', r'\CeNTailCross',
     'both unattributed, toward \\CeTailStar, in windows no '
     'expectation covers (Table~\\ref{tab:blockledger})', True),
    ('2', 'Quality-passing crossings of the census', r'\CsNCrossQp',
     'the same rows as 1.1.1', True),
    ('2.1', CONT + ' attributed to a transition', r'\CsNAttrQp',
     'of \\MkNCoinc{} coincidences inside the mask in the star\'s '
     'own frame; rows 2.1.1 and 2.1.2', True),
    ('2.1.1', CONT + ' with evidence beyond the coincidence',
     r'\LnAttrSupp',
     'recurrence at the predicted cell, a second transition of the same '
     'species, or catalogued gas on the sightline', True),
    ('2.1.2', CONT + ' on the frequency coincidence alone', r'\LnAttrCoinc',
     '\\LnCoincStars{}: consistent with molecular emission, not '
     'identified as it', True),
    ('2.2', CONT + ' unattributed', r'\CsNUnattrQp',
     'rows 2.2.1 and 2.2.2', True),
    #: ★★★★ ONE EXPECTATION IN THIS ROW, AND IT IS THE ADOPTED ONE.  The row
    #: used to end "and \CeExpX with the sub-trigger on-star excess carried
    #: into it", which gave the table two expectations for one comparison and
    #: left a reader to guess which the paper's own added-population bound was
    #: computed against.  The adopted expectation is the control-position sum
    #: \CeExp; the stepped sum is a sensitivity test, it is named as one in
    #: Sec. 5.3.1 and in Appendix D.1, and a counting table is not the place
    #: to repeat it.
    ('2.2.1', CONT + ' in the primary census', r'\CeObs',
     'against \\CeExp{} expected by chance at the \\CeNWin{} '
     'windows\' own control positions -- a count chance delivers '
     'with probability \\CeProbNull', True),
    ('2.2.2', CONT + ' coincident with an atmospheric transition',
     r'\CeTlObsCut',
     'within \\ScRadMHz\\,MHz of one in the topocentric frame '
     '(Appendix~\\ref{app:rfi}), and counted as atmospheric on both '
     'sides of that comparison', True),
    # ★ NOT "the two events of Fig. 7".  Figure 7 draws ONE of them, 61 Vir,
    # in four panels; the panels for the second were cut and the figure's own
    # caption, Table 6's caption and Sec. 5.5 all say "the first of them".
    # This note was the only place left promising two, which is the shape of
    # defect that outlives a figure change: the float moved, the pointer to it
    # did not.
    ('2.2.3', CONT + ' recovered in a later block', r'\NUnattNoRepeat',
     'no confirmed signal; \\MkAttrRecur{} attributed ones do', True),
    ('2.2.4', CONT + ' above all \\NCtrl{} controls', r'\EvNRankQp',
     'the two events of Table~\\ref{tab:cand}', False),
    #: Eight counts in this paper select on the word "unattributed" and the
    #: eight sets are not the same.  Each row below is one of them, with the
    #: filter that selects it; the member list is in the machine-readable
    #: itemisation beside this table.  A3 closes every one of them on
    #: another, so a set cannot drift without failing the build.
    ('2.3', 'All unattributed crossings, both quality classes',
     r'\MkUnattr',
     'rows 2.2, 1.1.2 and 1.2 together, every crossing of the failing block '
     'being unattributed: the population the recurrence test and the '
     'interference screens of Appendix~\\ref{app:rfi} are formed over',
     False),
    ('2.3.1', CONT + ' whose predicted cell was read', r'\RcNExclPoss',
     'the remaining \\RcNUnread{} was not read at its repeat epochs, '
     'so no amplitude could be carried to a repeat epoch for it', False),
    ('2.3.2', CONT + ' carrying an amplitude bound', r'\RcNExcl',
     'row 2.3.1 less the \\RcNWithheld{} of row 1.1.2, whose discovery '
     'amplitude comes from the block that fails the quality criterion',
     False),
    ('2.3.3', CONT + ' a catalogued window of a later block covers',
     r'\PaNCovWinCross',
     'the set the drift-pair accounting of the data archive is formed '
     'over; \\WdNNoCov{} is '
     'covered by no catalogued window at all', False),
    ('2.3.4', CONT + ' in a block the per-window catalogue describes',
     r'\ImNScreen',
     'the image-sideband population of Table~\\ref{tab:rfitests}; the '
     '\\CeNTailCross{} of row 1.2 lie outside it', False),
    ('2.3.5', CONT + ' with both an amplitude bound and a catalogued '
     'covering window', r'\WdNOrbTot',
     'rows 2.3.2 and 2.3.3 together, the set \\S\\ref{sec:etacrv} sets '
     'against the orbital excursion', False),
    ('2.4', 'Unattributed crossings of the census and the reserved '
     'hold-out in a searched window', r'\TlBandNSub',
     'row 2.3.4 with the \\HoNUnattr{} of \\S\\ref{sec:holdoutsearch}: '
     'the population of the sky-frequency occupancy test of '
     'Appendix~\\ref{app:rfi}', False),
    ('3', 'Class~A systems', r'\NSysClassA',
     'of \\NSystems{} surveyed; rows 3.1 and 3.2', True),
    # ★ ROW 3.1 IS IN THE FILE AND NOT IN THE ARTICLE, and the reason is not
    # its own value: 3.1.1 is the confirmable set, it is the only
    # confirmation count the paper quotes, and it is written as a
    # continuation of 3.1.  A continuation mark whose parent is absent reads
    # as a continuation of whatever row precedes it -- here the system total,
    # a different population -- so taking 3.1 out would cost either this
    # row's meaning or a rewritten label.  A12 enforces the pair; 3.1's own
    # note says in the table what A9 enforces everywhere else, that the
    # any-frequency count is not a confirmation count.
    #: ★ r28 (m6): THE PRINTED ROWS OF GROUP 3 ARE NUMBERED CONTIGUOUSLY WITH
    #: THEIR PARENT PRESENT.  The confirmable set was 3.1.1 under an unprinted
    #: any-frequency parent 3.1; it is now 3.1, a direct child of the system
    #: total, and with 3.2 it partitions row 3 (A3h).  The any-frequency pair,
    #: which A9 keeps out of every sentence, is a second partition of row 3 in
    #: the file only (3.3 and 3.4, A3i).  The row 3.1 note used to end in a
    #: sentence fragment ("Over the census together with the repeat blocks the
    #: recurrence test reads"), shipped in v4.28; it is now a clause.
    ('3.1', CONT + ' with same-frequency coverage in a separated session',
     r'\textbf{\ZcConfSysDay}',
     '\\textbf{the only confirmation count quoted}: a later block in another '
     'session, among the census and the repeat blocks the recurrence test '
     'reads, covering a frequency the first covered; \\ZcConfSysYr{} of them '
     'over a year later. For an accelerating carrier, confirmation further '
     'requires the repeat to fall at a matching orbital phase', True),
    ('3.2', CONT + ' with no separated second block at a covered frequency',
     r'\ZcNoRepSys',
     'confirmation impossible over the \\ZcNRecEB{} blocks the '
     'recurrence test reads; \\RcNoRepSysAll{} of all \\NSystems', True),
    ('3.2.1', CONT + ' counting census blocks alone', r'\ZcCenNoRepSys',
     'the \\ZcNMovedWord{} systems the archive retests outside the '
     'census are the difference', False),
    ('3.3', CONT + ' observed again more than \\EpSep{} day later',
     r'\ScSysIndep', 'over the census blocks, at any frequency and '
     'whatever the session, so not a confirmation count; rows 3.3 and 3.4 '
     'split row 3 a second way', False),
    ('3.4', CONT + ' observed once, or all within one day',
     r'\ScSysNoConf',
     'over the census blocks: \\ScSysOneBlock{} in a single block, '
     '\\ScSysSameDay{} within a day', False),
    ('4', 'Class~A union bandwidth', '\\CvUnionA\\,GHz',
     '\\DomAIslands{} disjoint islands', True),
    ('4.1', CONT + ' removed by the line mask', '\\MkMaskAPct\\,\\%',
     '\\MkMaskAGHz\\,GHz: the figure the text quotes, against '
     '\\FrMaskPct{} per cent of the \\DnuAB\\,GHz archival union', True),
]

PRINTED = [r for r in SPEC if r[4]]
# ★ The caption says how many rows the ledger has and how many of them the
# article does not print, and both are `len()` of the list above rather than a
# number anybody maintains: this table has gained and lost rows in four
# rounds, and a caption carrying a remembered count is how it comes to promise
# a row that is not in the file.
m('MtCountRows', '%d' % len(SPEC))
m('MtCountRowsOut', '%d' % (len(SPEC) - len(PRINTED)))


def row(num, label, val, note):
    return '%s & %s & %s & %s \\\\\n' % (num, label, val, note)


L = ['%% GENERATED by counts_r15.py -- do not hand-edit.\n',
     '%% The accounting rows of the master count table; the itemisation is in\n'
     '%% the machine-readable file this generator writes beside it.\n',
     HEAD, '\\hline\n',
     ' & Count & Value & What it counts \\\\\n', '\\hline\n']
_grp = None
for _num, _lab, _val, _note, _ in PRINTED:
    if _grp is not None and _num.split('.')[0] != _grp:
        L.append('\\hline\n')
    _grp = _num.split('.')[0]
    L.append(row(_num, _lab, _val, _note))
L.append('\\hline\n\\end{tabular}\n')

# ------------------------------------------------- the plain-text resolution
# ★★ The file carries VALUES, not macro names: a machine-readable table whose
# value column reads `\EvNCrossRaw` is not machine-readable.  Every macro is
# resolved out of the macro layer -- this generator's own first, the published
# layer second -- and every piece of LaTeX markup the table uses is removed by
# a rule written for it.  The assertion at the end is the check: if anything
# of LaTeX survives, a macro or a construct has been added to a row and
# nobody has said what it means in plain text, and the build stops rather
# than shipping a data file with a backslash in it.
_TEXT_FIRST = [
    #: GEN (v4.29 fold): a Greek-letter star name ($\eta$~Crv) now reaches a cell through \LnCoincStars (eta Crv
    #: X1430 entered the census attributed on the coincidence alone); spelled out, as the deposit spells it.
    (r'\$\\(alpha|beta|gamma|delta|epsilon|zeta|eta|theta|iota|kappa|lambda|mu|nu|xi|pi|rho|sigma|tau|'
     r'upsilon|phi|chi|psi|omega)\$', r'\1'),
    (r'\\S\\ref\{sec:bdblock\}', 'Sec. 5.3.2'),
    (r'\\S\\ref\{[^}]*\}', 'the section cited in the paper'),
    (r'\\ref\{tab:cand\}', '5'),
    #: ★ r27 merge: Table A2's new set rows (sets P1) cite two tables, and a
    #: bare `\\ref{tab:...}` rule left "Table the table cited" -- the v4.26
    #: defect below, for tables.  The introducing word goes WITH the label.
    (r'Table~?\\ref\{tab:[a-z]+\}', 'the table cited in the paper'),
    (r'\\ref\{tab:[a-z]+\}', 'the table cited in the paper'),
    #: ★★★★ v4.26.  THIS RULE SHIPPED A MACRO ARTEFACT IN AN ARXIV ANCILLARY
    #: FILE.  `(Appendix~\\ref{app:rfi})` met the `~` rule and then this one
    #: and came out as "(Appendix the appendix cited in the paper)", which is
    #: what `si_counts.txt` has been serving to readers.  The defect is that
    #: a generic substitution cannot keep the word that introduces the
    #: reference, so the sentence is left half-dereferenced.  Each appendix
    #: label is now replaced TOGETHER with its introducing word, by name, and
    #: the assertion below refuses any label this list does not cover -- so a
    #: new appendix reference stops the build instead of printing nonsense.
    (r'Appendix~?\\ref\{app:rfi\}', 'the atmospheric screen'),
    (r'Appendix~?\\ref\{app:[a-z]+\}', 'the appendix cited in the paper'),
    (r'\\ref\{app:[a-z]+\}', 'the appendix cited in the paper'),
    (r'\\textbf\{([^{}]*)\}', r'\1'),
    (r'\\emph\{([^{}]*)\}', r'\1'),
    (r'\\ldots\{\}', '...'),
    (r'\\ldots', '...'),
    (r'\$T_\\star\\ge5\$', 'T* >= 5'),
    (r'\\,', ' '),
    (r'\\%', '%'),
    (r'\\&', 'and'),
    (r'~', ' '),
]


def _resolve(s, depth=0):
    """One table cell as plain text, with every macro replaced by its value."""
    t = s
    for pat, sub in _TEXT_FIRST:
        t = re.sub(pat, sub, t)

    def _mv(mo):
        nm = mo.group(1)
        return _resolve(M[nm] if nm in M else published(nm), depth + 1)
    t = re.sub(r'\\([A-Za-z]+)(?:\{\})?', _mv, t)
    t = t.replace('$', '').replace('{', '').replace('}', '')
    t = re.sub(r'\s+', ' ', t).strip()
    if depth == 0:
        assert '\\' not in t, (
            'the plain-text form of a count-table cell still carries LaTeX, '
            'so a construct in it has no plain-text rule: %r -> %r' % (s, t))
        #: ★★★★ v4.26.  AND NO HALF-DEREFERENCED CROSS-REFERENCE EITHER.  The
        #: LaTeX check above passed for two versions on a cell reading
        #: "(Appendix the appendix cited in the paper)", because a generic
        #: `\ref{app:...}` rule leaves the introducing word behind and
        #: nothing is left to carry a backslash.  A cell may say "the
        #: appendix/section/table cited in the paper", but never with
        #: "Appendix", "Sec." or "Table" standing in front of it.
        _ART = re.search(r'(?:Appendix|Sec\.|Section|Table|Figure|Fig\.)\s+'
                         r'the (?:appendix|section|table|figure) cited', t)
        assert not _ART, (
            'a cross-reference in a count-table cell is only half '
            'dereferenced, so the plain-text file would ship a macro '
            'artefact: %r -> %r' % (s, t))
    return t


# ============================================================ the deposit

ROWS = []
for s in SYSROW:
    ROWS.append(dict(system_id=s,
                     stars='; '.join(sorted(SYSNAME[s])),
                     n_window_classA=NWINA[s],
                     observed_unattributed=OBS[s],
                     expected_unattributed='%.4f' % EXP[s],
                     p_at_least_observed='%.4f' % PGE[s]))

# ------------------------------- the master counts as an ancillary file ----
# ★★★ The machine-readable form of this table, to accompany the arXiv
# submission as an ANCILLARY FILE (`anc/`), exactly as the crossing ledger and
# the per-window catalogue already do.  An ancillary file is not refereed and
# is not part of the article, so it carries no claim of its own: it is this
# table's own rows, resolved to values, with a column saying which of them the
# article prints.  It is written by the generator that writes the table, from
# the same list, because the alternative is a data file that drifts from the
# table it is the data of.
MRCOLS = [
    ('row', 'the row number, as in the master count table of the article'),
    ('count', 'what is counted'),
    ('value', 'the published value'),
    ('what_it_counts', 'the note the table carries, in plain text'),
    ('in_article', '1 where the article prints this row, 0 where the row is '
                   'in this file only'),
]
MRROWS = []
for _num, _lab, _val, _note, _inpaper in SPEC:
    MRROWS.append(dict(row=_num, count=_resolve(_lab).lstrip('. '),
                       value=_resolve(_val),
                       what_it_counts=_resolve(_note),
                       in_article='1' if _inpaper else '0'))

# ★★ A12: a child row the article prints must have its parent printed.  The
# continuation mark means "of the row above"; with the parent moved out of the
# article it reads as a continuation of whatever row happens to precede it,
# which in this table would be a different population altogether.  Row 3.1.1
# is the case: it is printed, its parent 3.1 is not, and its label is
# therefore written out in full.
_orphan = [r[0] for r in PRINTED
           if r[1].startswith(CONT)
           and r[0].rsplit('.', 1)[0] not in [q[0] for q in PRINTED]]
if DRIVE == 16:
    _orphan.append('(drive 16) 9.9.9')
ck('A12 every printed row that continues its parent has its parent printed',
   not _orphan,
   '%d printed rows, %d of them continuations'
   % (len(PRINTED), sum(1 for r in PRINTED if r[1].startswith(CONT)))
   if not _orphan else 'orphaned continuation row(s): %s' % _orphan)

# ★★ A13: and no printed note may point at a row the article does not print.
# Row 2.2's note is "rows 2.2.1 and 2.2.2", so this is not vacuous; it is the
# check that would have fired had the itemisation been taken out wholesale.
_dangling = []
for _num, _lab, _val, _note, _ in PRINTED:
    for _ref in re.findall(r'\b(\d+(?:\.\d+)+)\b', _note):
        if _ref not in [q[0] for q in PRINTED]:
            _dangling.append('%s -> %s' % (_num, _ref))
if DRIVE == 17:
    _dangling.append('(drive 17) 2.2 -> 2.2.9')
ck('A13 no printed note points at a row the article does not print',
   not _dangling,
   '%d cross-references in the printed notes'
   % sum(len(re.findall(r'\b\d+(?:\.\d+)+\b', r[3])) for r in PRINTED)
   if not _dangling else 'dangling: %s' % '; '.join(_dangling))

# ★★ A14: the file is this table, whole.  Every row of the declared list is in
# it, the values the article prints are the values the file carries, and
# nothing of LaTeX survives in any field (the resolution itself asserts that
# cell by cell, so this is the count and the agreement).
_vals_agree = all(
    _resolve(r[2]) == MRROWS[_i]['value'] for _i, r in enumerate(SPEC))
_nart = sum(1 for r in MRROWS if r['in_article'] == '1')
if DRIVE == 18:
    MRROWS = MRROWS[:-1]
ck('A14 the ancillary file carries every row of the table, with the values '
   'the article prints',
   len(MRROWS) == len(SPEC) and _vals_agree and _nart == len(PRINTED)
   and all(set(r) == {c for c, _ in MRCOLS} for r in MRROWS),
   '%d rows, %d of them printed in the article, %d columns described'
   % (len(MRROWS), _nart, len(MRCOLS)))

# =================================================================== write
if FAIL:
    print('\nFAILED: %s' % ', '.join(FAIL))
assert not FAIL, 'counts_r15: %d assertion(s) failed' % len(FAIL)

with open(TAB, 'w') as fh:
    fh.writelines(L)
with open(os.path.join(HERE, suffixed('si_counts.txt')), 'w') as fh:
    fh.write('# The master count table of the ALMA 40 pc technosignature '
             'search: one row per published count.\n')
    fh.write('# Accompanies the arXiv submission as an ancillary file '
             '(anc/).  Tab-separated; the rows are the table\'s own.\n')
    fh.write('# The article prints the %d accounting rows; this file carries '
             'all %d, itemisation included.\n' % (_nart, len(MRROWS)))
    fh.write('#\n# Columns:\n')
    for _i, (_c, _d) in enumerate(MRCOLS, 1):
        fh.write('#  %2d  %-16s %s\n' % (_i, _c, _d))
    fh.write('#\n')
    fh.write('\t'.join(c for c, _ in MRCOLS) + '\n')
    for _r in MRROWS:
        _line = [_r[c] for c, _ in MRCOLS]
        assert not any('\t' in x for x in _line), _r
        fh.write('\t'.join(_line) + '\n')
with open(CSVOUT, 'w', newline='') as fh:
    w = csv.DictWriter(fh, fieldnames=list(ROWS[0].keys()))
    w.writeheader()
    w.writerows(ROWS)
with open(OUT, 'w') as fh:
    fh.write('%% round 560: the master count table.  Generated by\n'
             '%% counts_r15.py.  Every value the table prints is read out of\n'
             '%% the macro layer; what this generator contributes is the\n'
             '%% arithmetic between them and the per-system decomposition of\n'
             '%% the chance expectation (persystem_chance_r15.csv).\n')
    for k, v in M.items():
        fh.write('\\newcommand{\\%s}{%s}\n' % (k, v))

print('\n%s: %d macros' % (os.path.basename(OUT), len(M)))
print('%s: %d rows' % (os.path.basename(TAB),
                       sum(1 for x in L if x.endswith('\\\\\n'))))
print('%s: %d systems' % (os.path.basename(CSVOUT), len(ROWS)))
print('%s: %d rows, %d printed in the article'
      % (os.path.basename(suffixed('si_counts.txt')), len(MRROWS), _nart))
print('\nthe five systems holding the most unattributed census crossings:')
for s in SYSROW[:5]:
    print('  %-28s %3d windows  %2d observed  %5.2f expected  p=%.3f'
          % (sorted(SYSNAME[s])[0][:28], NWINA[s], OBS[s], EXP[s], PGE[s]))

if OUTSIDE:
    # The products above are written and correct; what failed is a use site in
    # a file this generator does not own.  Non-zero so the build stops.
    print('\nFAILED OUTSIDE THIS GENERATOR: %s' % ', '.join(OUTSIDE))
    sys.exit(1)
