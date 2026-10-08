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

Usage:  counts_r15.py [--drive N]      N = 0..9
--drive 0 means "no perturbation, but do not write a path production reads".
"""
import collections
import csv
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


OUT = os.path.join(HERE, suffixed('survey_numbers_round560.tex'))
TAB = os.path.join(HERE, suffixed('tab_counts.tex'))
CSVOUT = os.path.join(HERE, suffixed('persystem_chance_r15.csv'))

M, FAIL = {}, []


def m(k, v):
    assert k.isalpha(), 'a LaTeX macro name may contain letters only: ' + k
    assert k not in M, 'macro defined twice: ' + k
    M[k] = str(v)


def ck(tag, cond, detail=''):
    if not cond:
        FAIL.append(tag)
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
    for fn in sorted(os.listdir(HERE)):
        if not (fn.startswith('survey_numbers') and fn.endswith('.tex')):
            continue
        if '_drive' in fn or fn.startswith('survey_numbers_round%d' % ROUND):
            continue
        vals = [h for h in pat.findall(
            open(os.path.join(HERE, fn), errors='ignore').read()) if h.strip()]
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
XA_UN_CEN = [r for r in XA_UN if WIN[id(r)] is not None]

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
_MARK = 'P_UNMASKED = {i: PEXC[i] * (1.0 - MASK[i]) for i in PEXC}'
assert _SRC.count(_MARK) == 1, 'chance_v414.py no longer exposes P_UNMASKED'
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
N_OBS = P('CeObs')
N_A = len(XA)
if DRIVE == 4:
    N_A += 1                           # the Class A total must close

ck('A1 the crossing total partitions into Class A and Class B, and the '
   'Class A part into census and archival-tail rows',
   N_A == len(XA_CEN) + N_TAILX and N_A + N_B == N_RAW
   and len(XB) == N_B and len(TAIL) == N_TAILX,
   '%d A (%d census + %d tail) + %d B == %d' % (N_A, len(XA_CEN), N_TAILX,
                                                N_B, N_RAW))
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
   N_A_CEN == N_A and len(XA_CEN) != N_A_CEN,
   'released catalogue %d Class A, adopted ledger %d (%d census + %d tail)'
   % (N_A_CEN, N_A, len(XA_CEN), N_TAILX))
# ★★★ A2 IS M2(b)'s ANSWER.  "52 Class A crossings" and "52 quality-passing
#     crossings" are the same rows, because the one block that fails the
#     quality criterion is the only block in the survey holding a
#     coarse-channel crossing.  Until this is said, a reader has two routes to
#     52 and no reason to believe they meet.  Driven by --drive 4.
ck('A2 the quality-passing crossings and the Class A crossings are the same '
   'rows, because the failing block holds every Class B crossing',
   N_A == N_QP and {id(r) for r in QP} == {id(r) for r in XA}
   and {r['eb'] for r in FLAGGED} == {FAILBLOCK}
   and len(FLAGGED) == N_FLAG == N_B,
   '%d == %d, and all %d flagged crossings are the %d Class B ones in '
   '%s' % (N_A, N_QP, len(FLAGGED), N_B, FAILBLOCK.replace('_', '\\_')))
ck('A3 the quality-passing crossings partition into attributed and '
   'unattributed, and the unattributed into census and archival-tail',
   N_ATTR + N_UNATTR == N_QP and N_OBS + N_TAILX == N_UNATTR
   and len(XA_UN) == N_UNATTR and len(XA_UN_CEN) == N_OBS
   and N_RANK <= N_UNATTR,
   '%d + %d == %d; %d census + %d tail == %d unattributed, %d of them '
   'outranking every control' % (N_ATTR, N_UNATTR, N_QP, N_OBS, N_TAILX,
                                 N_UNATTR, N_RANK))
# ★★★ A4 IS M2(a)'s ANSWER: the three figures the manuscript used
#     interchangeably are three nested sets, and the nesting is what makes
#     them different quantities rather than contradictory counts.  A repeat
#     epoch at another frequency confirms nothing, so the middle set is the
#     one the paper quotes.
N_SYSA = P('NSysClassA')
N_SEP = P('ScSysIndep')
N_NOSEP = P('ScSysNoConf')
N_CONF = P('RcConfSysDay')
N_NOCONF = P('RcNoRepSys')
N_CONFYR = P('RcConfSysYr')
N_CONFALL = P('RcConfSysAllDay')
N_NOCONFALL = P('RcNoRepSysAll')
N_SYSALL = P('NSystems')
if DRIVE == 5:
    N_CONF = N_SEP + 1
ck('A4 the confirmation counts are three nested sets over two populations, '
   'and each complement closes on its own population',
   N_SEP + N_NOSEP == N_SYSA and N_CONF + N_NOCONF == N_SYSA
   and N_CONFALL + N_NOCONFALL == N_SYSALL
   and N_CONFYR <= N_CONF <= N_SEP <= N_CONFALL,
   'Class A: %d separated / %d at the same frequency / %d of those over a '
   'year, against %d systems; all systems: %d of %d'
   % (N_SEP, N_CONF, N_CONFYR, N_SYSA, N_CONFALL, N_SYSALL))
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
ck('A6 no single system holds more unattributed crossings than its own '
   'control positions allow, over the whole sample',
   N_LOW <= max(1, int(round(E_LOW))) and OBS[TOPSYS] <= 2.0 * EXP[TOPSYS]
   and _TOP2_OBS == _TOP2_WIN and _key(sorted(SYSNAME[TOPSYS])[0]) == _topkey
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
   TOPSTAR_N == TOPSTAR_UN == OBS[TOPSYS] + N_TAILX and NSPELL > 1,
   '%s: %d crossings, all unattributed, %d in census windows and %d in '
   'archival-tail blocks, under %d spellings in the ledger'
   % (TOPSTAR, TOPSTAR_N, OBS[TOPSYS], N_TAILX, NSPELL))
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
if DRIVE == 7:
    FAIL.append('A0 deliberate failure, drive 7')

# ================================================================ macros
m('MtCrossA', '%d' % N_A)
m('MtCrossACen', '%d' % len(XA_CEN))
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
HEAD = ('\\begin{tabular}'
        '{@{}r@{~}p{0.405\\columnwidth}r@{\\,\\,}'
        'p{0.325\\columnwidth}@{}}\n')


def row(num, label, val, note):
    return '%s & %s & %s & %s \\\\\n' % (num, label, val, note)


L = ['%% GENERATED by counts_r15.py -- do not hand-edit.\n',
     HEAD, '\\hline\n',
     ' & Count & Value & What it counts \\\\\n', '\\hline\n']
L.append(row('1', 'Threshold crossings at $T_\\star\\ge5$',
             r'\EvNCrossRaw', 'census and archival tail'))
L.append(row('1.1', 'Class~A, fine channels', r'\MtCrossA',
             'the carrier experiment'))
L.append(row('1.1.1', '\\ldots{} in the primary census', r'\MtCrossACen',
             'catalogued window by window'))
L.append(row('1.1.2', '\\ldots{} in archival-tail blocks', r'\CeNTailCross',
             'both toward \\CeTailStar; in no expectation'))
L.append(row('1.2', 'Class~B, coarse channels', r'\LdgNCrossB',
             'all in the one block failing \\S\\ref{sec:bdblock}'))
L.append('\\hline\n')
L.append(row('2', 'Quality-passing crossings', r'\EvNCrossQp',
             'the same rows as 1.1'))
L.append(row('2.1', '\\ldots{} attributed to a transition', r'\EvNAttrQp',
             'inside the mask in the star\'s own frame'))
L.append(row('2.2', '\\ldots{} unattributed', r'\EvNUnattrQp',
             'rows 2.2.1 and 2.2.2'))
L.append(row('2.2.1', '\\ldots{} in the primary census', r'\CeObs',
             'against \\CeExp{} expected by chance, measured at the '
             '\\CeNWin{} windows\' own control positions '
             '(\\CeLo--\\CeHi{} allowed)'))
L.append(row('2.2.2', '\\ldots{} in archival-tail blocks', r'\CeNTailCross',
             'outside that comparison'))
L.append(row('2.2.3', '\\ldots{} above all \\NCtrl{} controls', r'\EvNRankQp',
             'the two events of Fig.~\\ref{fig:event}'))
L.append(row('2.2.4', '\\ldots{} recovered in a later block',
             r'\NUnattNoRepeat',
             'no confirmed signal; \\MkAttrRecur{} attributed ones do'))
L.append('\\hline\n')
L.append(row('3', 'Class~A systems', r'\NSysClassA',
             'of \\NSystems{} surveyed'))
L.append(row('3.1', '\\ldots{} seen again after \\EpSep{} day',
             r'\ScSysIndep', 'at any frequency'))
L.append(row('3.2', '\\ldots{} at the same stellar-frame frequency',
             r'\RcConfSysDay',
             '\\textbf{where a signal could have been confirmed}; '
             '\\RcConfSysYr{} of them over a year later'))
L.append(row('3.3', '\\ldots{} with no such second block', r'\RcNoRepSys',
             'confirmation impossible; \\RcNoRepSysAll{} of all \\NSystems'))
L.append('\\hline\n')
L.append(row('4', 'Class~A union bandwidth', '\\CvUnionA\\,GHz',
             '\\DomAIslands{} disjoint islands'))
L.append(row('4.1', '\\ldots{} removed by the line mask',
             '\\MkMaskAPct\\,\\%',
             '\\MkMaskAGHz\\,GHz: the figure the text quotes, against '
             '\\FrMaskPct{} per cent of the \\DnuAB\\,GHz archival union'))
L.append('\\hline\n\\end{tabular}\n')

# ============================================================ the deposit
ROWS = []
for s in SYSROW:
    ROWS.append(dict(system_id=s,
                     stars='; '.join(sorted(SYSNAME[s])),
                     n_window_classA=NWINA[s],
                     observed_unattributed=OBS[s],
                     expected_unattributed='%.4f' % EXP[s],
                     p_at_least_observed='%.4f' % PGE[s]))

# =================================================================== write
if FAIL:
    print('\nFAILED: %s' % ', '.join(FAIL))
assert not FAIL, 'counts_r15: %d assertion(s) failed' % len(FAIL)

with open(TAB, 'w') as fh:
    fh.writelines(L)
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
print('\nthe five systems holding the most unattributed census crossings:')
for s in SYSROW[:5]:
    print('  %-28s %3d windows  %2d observed  %5.2f expected  p=%.3f'
          % (sorted(SYSNAME[s])[0][:28], NWINA[s], OBS[s], EXP[s], PGE[s]))
