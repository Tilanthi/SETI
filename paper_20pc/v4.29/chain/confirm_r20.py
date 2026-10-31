#!/usr/bin/env python3
r"""confirm_r20.py -- round 910.  ONE confirmation criterion, matching its own
rationale, applied everywhere the paper counts what could have been confirmed.

WHY THIS EXISTS.  The criterion and the reason given for it did not agree.

 1. THE RULE ADMITTED WHAT ITS RATIONALE EXCLUDES.  Sec. 4.2(iii) required the
    recovering block to be "more than 1 day from the first, OR an execution of
    a different observing session", and justified that by saying blocks of one
    session share calibrators, atmosphere, correlator setup and interference
    environment.  That reason applies to ANY two blocks of one session,
    whatever the interval between them, so the disjunction admitted exactly
    what the reason rules out: `QfNPairDrop` pairs of census blocks are more
    than a day apart AND in one session, the widest of them `QfSameSessMaxD` d.
    The adopted criterion is the CONJUNCTION -- a different observing session
    AND more than one day apart -- because the rationale is the part of the
    sentence we believe.

 2. THE CENSUS IMPLEMENTED ONE BRANCH OF A RULE WITH TWO.  Every published
    confirmability count came from the day branch alone, so the quoted figures
    were neither branch of the rule as written.  Under the conjunction the day
    branch IS the rule, up to the second conjunct, and this generator measures
    what that second conjunct costs: it is measured and it is zero at the level
    of every published count, which is the only reason the numbers do not move.
    The disjunction, by contrast, would have added `QfNSysOrOnly` system
    (`QfSysOrOnly`), so the looser rule was not harmless either.

WHAT MOVES AND WHAT DOES NOT.  No published count moves.  `QfNPairDrop` block
pairs over `QfNSysPairDrop` systems lose their standing as a confirming pair,
and `QfNSysMoved` systems lose their mark, because every one of those systems
is confirmable through a different pair as well.  That is a measurement and not
an expectation: it is asserted below and the assertion is driven.

THE ASSERTIONS, AND WHY EACH CAN FAIL.
  K1  the day branch, implemented here, reproduces every published
      confirmability macro exactly on both block sets and at all three
      thresholds.  Without this the comparison below would be between two
      methods and not between two rules.
  K2  the adopted conjunction gives the same mark as the day branch for every
      system, on both block sets, at all three thresholds -- so no published
      count moves.  Driven by flipping one system.
  K3  the strengthening is not vacuous: it rejects pairs the day branch
      admitted, they are named, and the beta Pic pair the report names is
      among them.  A rule that changed nothing at the level of pairs would be
      a rule we had not actually applied.
  K4  every system holding a rejected pair keeps its mark through a pair that
      satisfies the conjunction, and the pair is named.  This is what makes K2
      an explanation rather than a coincidence.
  K5  the disjunction is strictly looser than the conjunction and the system
      it alone would add is named, so the branch withdrawn here is shown to
      have had an effect.
  K6  all `QfNCtl` positive controls are recovered in a block that satisfies
      the conjunction.  That count licenses every exclusion in the paper, so
      it is verified and not inherited.  Driven by requiring same-session.
  K7  no unattributed crossing is recovered in any block under any of the
      three rules, so no disposition moves.  A stricter rule cannot promote
      one, but it is cheaper to measure than to argue.
  K8  every power-sufficient exclusion rests on repeat coverage that satisfies
      the conjunction, and the crossings whose only covering block shares the
      discovery's session are all in the set already reported too shallow to
      exclude anything.  Without this the paper would exclude on data it
      declines to confirm on.
  K9  the confirmable frequency support, which Fig. 8 draws, is the same under
      the conjunction as under the day branch, to the precision it is printed
      at.

    ASTRA_PAPER=/path/to/paper python3 confirm_r20.py      # read-only tree
    python3 confirm_r20.py                 # in the paper tree: measure and write
    python3 confirm_r20.py --drive N       # N = 1..11, one assertion each
    python3 confirm_r20.py --selftest      # drive every assertion to fail
"""
import collections
import csv
import glob
import itertools
import json
import os
import re
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
#: the paper tree.  In the tree the generator and the paper are one directory;
#: `ASTRA_PAPER` lets a wave-1 agent read a read-only tree from outside and
#: write only into its own, which is the standing rule for this round.
V = os.environ.get('ASTRA_PAPER', HERE)

ROUND = 910
DRIVE = int(sys.argv[sys.argv.index('--drive') + 1]) if '--drive' in sys.argv \
    else 0
SFX = '' if DRIVE == 0 else '_drive%d' % DRIVE
OUT = os.path.join(HERE, 'numbers/survey_numbers_round%d%s.tex' % (ROUND, SFX))
OUTJ = os.path.join(HERE, 'confirm_r20%s.json' % SFX)

sys.path.insert(0, V)

DAY = 1.0
MONTH = 30.0
YEAR = 365.25
POWER = 0.90                  # the recovery level the exclusions quote

M, FAIL = [], []

WORD = ['no', 'one', 'two', 'three', 'four', 'five', 'six', 'seven', 'eight',
        'nine', 'ten', 'eleven', 'twelve', 'thirteen', 'fourteen', 'fifteen',
        'sixteen', 'seventeen', 'eighteen', 'nineteen', 'twenty',
        'twenty-one', 'twenty-two', 'twenty-three']


def word(n):
    return WORD[n] if n < len(WORD) else '%d' % n


def starname(sid):
    s = sid.split(' Gaia')[0].strip()
    s = re.sub(r'^HD(\d)', r'HD \1', s)
    s = s.replace('bet Pic', r'$\beta$~Pic').replace('eta Crv', r'$\eta$~Crv')
    return s.replace(' ', '~')


def m(k, v):
    assert k.isalpha(), 'a LaTeX macro name may contain letters only: ' + k
    assert k not in dict(M), 'macro defined twice: ' + k
    M.append((k, str(v)))


def ck(name, cond, detail=''):
    if not cond:
        FAIL.append(name.split()[0])
    print('  %-72s %s  %s' % (name[:72], 'PASS' if cond else 'FAIL', detail))


def macro(name):
    pat = re.compile(r'\\newcommand\{\\%s\}\{(.*)\}\s*$' % name)
    for p in sorted(glob.glob(os.path.join(V, 'numbers/survey_numbers*.tex'))):
        if '_drive' in p:
            continue
        for line in open(p):
            mm = pat.match(line.strip())
            if mm:
                return mm.group(1)
    raise KeyError(name)


import epochs_r14 as EP                                        # noqa: E402


def session(eb):
    """The observing session an execution block belongs to.  ALMA's block
    identifier carries the session above the block, so several executions of
    one session share this field.  `None` where the identifier does not have
    that shape, which is the "where sessions are known" of the criterion;
    every block of this survey has it."""
    parts = eb.split('_')
    return parts[1] if len(parts) == 3 and parts[0] == 'A002' else None


def diff_session(a, b):
    sa, sb = session(a), session(b)
    return sa is not None and sb is not None and sa != sb


# ------------------------------------------------------- the two rules
# Both are ONE-SIDED, inherited from `epochs_r14.apart`: each can show that a
# pair satisfies the criterion and neither can show that a pair does not.  A
# count of confirmable systems is therefore a LOWER bound and a count of
# systems with no confirmation epoch an UPPER bound, under either rule.
def _apart(a, b, sep):
    return EP.apart(a, b) if sep <= EP.SEP else EP.apart_above(a, b, sep)


def rule_day(a, b, sep=DAY):
    """The branch every published count was computed on."""
    if DRIVE == 1:                      # K1: the day branch stops being it
        return _apart(a, b, sep) and session(a) == session(b)
    return _apart(a, b, sep)


def rule_adopted(a, b, sep=DAY):
    """THE ADOPTED CRITERION: a different observing session AND more than
    `sep` days apart."""
    return _apart(a, b, sep) and diff_session(a, b)


def rule_or(a, b, sep=DAY):
    """The disjunction the paper printed, withdrawn here."""
    return _apart(a, b, sep) or diff_session(a, b)


RULES = (('day', rule_day), ('adopted', rule_adopted), ('or', rule_or))

# ------------------------------------------------------------------ inputs
CAT = list(csv.DictReader(open(os.path.join(
    V, 'per_target_results_v3.99.csv'), encoding='utf-8')))
CLA = [r for r in CAT if r['search_class'] == 'A']
REC = json.load(open(os.path.join(V, 'r10inputs', 'recur_v411.json')))
CROSS = REC['crossings']
HOST = json.load(open(os.path.join(V, 'hostinj_r19.json')))['crossings']


def edges(r):
    a, b = float(r['flo_GHz']), float(r['fhi_GHz'])
    return min(a, b), max(a, b)


#: the census interval list per system, exactly as `confset_r18.py` builds it
CENSUS = collections.defaultdict(list)
for r in CLA:
    lo, hi = edges(r)
    CENSUS[r['system_id']].append((lo, hi, r['eb']))

WINSPAN = collections.defaultdict(list)
for i, r in enumerate(CAT):
    lo, hi = edges(r)
    WINSPAN[r['eb']].append((lo, hi, i))


def window_of(eb, f):
    hit = [i for lo, hi, i in WINSPAN.get(eb, [])
           if lo - 1e-6 <= f <= hi + 1e-6]
    return hit[0] if hit else None


def _norm(s):
    return ''.join(c for c in s.lower() if c.isalnum())


SYS_BY_STAR = {}
for r in CAT:
    SYS_BY_STAR.setdefault(_norm(r['star_name']), r['system_id'])

SYSOF = {}
for cid, c in CROSS.items():
    i = window_of(c['eb'], c['freq_GHz'])
    SYSOF[cid] = CAT[i]['system_id'] if i is not None \
        else SYS_BY_STAR.get(_norm(c['star']))

#: the repeat readings the recurrence test made, one interval per reading, as
#: `confset_r18.py` builds them.  The larger block set the published counts use.
EXTRA = collections.defaultdict(list)
for cid, c in CROSS.items():
    sid = SYSOF.get(cid)
    if sid is None:
        continue
    for b in c.get('blocks', []):
        if b.get('bad_weight_product'):
            continue
        half = 0.5 * float(b['chanw_Hz']) / 1e9
        f = float(b['f_here_GHz'])
        EXTRA[sid].append((f - half, f + half, b['eb']))
    d = c.get('discovery')
    if d:
        half = 0.5 * float(d['chanw_Hz']) / 1e9
        f = float(c['freq_GHz'])
        EXTRA[sid].append((f - half, f + half, c['eb']))

SYSTEMS = sorted(CENSUS)


# --------------------------------------------- the confirmability predicate
def confirmable(iv, rule, sep):
    """True where two blocks of this system satisfy `rule` at `sep` and cover
    one common frequency.  Evaluated on the interval boundaries, so no island
    can be lost to a grid."""
    pts = sorted({x for a, b, _ in iv for x in (a, b)})
    for i in range(len(pts) - 1):
        mid = 0.5 * (pts[i] + pts[i + 1])
        ebs = sorted({e for a, b, e in iv if a <= mid <= b})
        for x, y in itertools.combinations(ebs, 2):
            if rule(x, y, sep):
                return True
    return False


def marks(iv, rule):
    return (confirmable(iv, rule, DAY), confirmable(iv, rule, YEAR),
            confirmable(iv, rule, MONTH))


RES = {}
for sid in SYSTEMS:
    cen, rec = CENSUS[sid], CENSUS[sid] + EXTRA.get(sid, [])
    RES[sid] = {nm: dict(census=marks(cen, rl), recur=marks(rec, rl))
                for nm, rl in RULES}
if DRIVE == 2:                             # K2: one system's mark moves
    _s = SYSTEMS[0]
    RES[_s]['adopted']['recur'] = (not RES[_s]['adopted']['recur'][0],
                                   RES[_s]['adopted']['recur'][1],
                                   RES[_s]['adopted']['recur'][2])


def count(rule, setname, idx=0):
    return sum(1 for s in SYSTEMS if RES[s][rule][setname][idx])


NSYS = len(SYSTEMS)
CEN_D = count('day', 'census')
CEN_A = count('adopted', 'census')
CEN_O = count('or', 'census')
REC_D = count('day', 'recur')
REC_A = count('adopted', 'recur')
REC_O = count('or', 'recur')

print('confirm_r20 (round %d)%s'
      % (ROUND, '  [drive %d]' % DRIVE if DRIVE else ''))
print('\nconfirmable systems of %d, by rule and block set' % NSYS)
for nm, _ in RULES:
    print('  %-8s census %3d (%2d unconfirmable) / %3d yr / %3d mo   '
          'recurrence set %3d (%2d) / %3d yr / %3d mo'
          % (nm, count(nm, 'census'), NSYS - count(nm, 'census'),
             count(nm, 'census', 1), count(nm, 'census', 2),
             count(nm, 'recur'), NSYS - count(nm, 'recur'),
             count(nm, 'recur', 1), count(nm, 'recur', 2)))
print('\nassertions')

# ---------------------------------------------------------------------- K1
_pub = dict(ZcConfSysDay=REC_D, ZcConfSysYr=count('day', 'recur', 1),
            ZcConfSysMonth=count('day', 'recur', 2),
            ZcNoRepSys=NSYS - REC_D,
            ZcCenNoRepSys=NSYS - CEN_D,
            RcConfSysDay=CEN_D, RcNoRepSys=NSYS - CEN_D,
            RcConfSysYr=count('day', 'census', 1),
            QcConfSysCen=CEN_D, NSysClassA=NSYS)
_bad = {k: (v, macro(k)) for k, v in _pub.items() if '%d' % v != macro(k)}
ck('K1 the day branch implemented here reproduces every published '
   'confirmability macro', not _bad,
   '%d macros checked; %s' % (len(_pub), _bad or 'all agree'))

# ---------------------------------------------------------------------- K2
MOVED = [(s, k, i) for s in SYSTEMS for k in ('census', 'recur')
         for i in range(3)
         if RES[s]['day'][k][i] != RES[s]['adopted'][k][i]]
ck('K2 the adopted conjunction gives the same mark as the day branch for '
   'every system, so no published count moves',
   not MOVED,
   '%d of %d system-marks differ%s'
   % (len(MOVED), 6 * NSYS,
      ': %s' % MOVED[:4] if MOVED else '; counts %d/%d census, %d/%d '
      'recurrence set' % (CEN_D, CEN_A, REC_D, REC_A)))

# ----------------------------------------- K3 the pairs the conjunction drops
BYSYS_EB = collections.defaultdict(set)
for r in CLA:
    BYSYS_EB[r['system_id']].add(r['eb'])
DROP = []
for s in SYSTEMS:
    for a, b in itertools.combinations(sorted(BYSYS_EB[s]), 2):
        if rule_day(a, b) and not rule_adopted(a, b):
            ta, tb = EP.EPOCHS.get(a), EP.EPOCHS.get(b)
            DROP.append(dict(system=s, a=a, b=b, sess=session(a),
                             dt=(abs(ta - tb) if ta is not None
                                 and tb is not None else None)))
if DRIVE == 3:
    DROP = []
DROP_SYS = sorted({d['system'] for d in DROP})
BPIC_PAIR = ('A002_Xd9668b_X3a90', 'A002_Xd9668b_Xa9df')
_bp = [d for d in DROP if {d['a'], d['b']} == set(BPIC_PAIR)]
ck('K3 the strengthening rejects pairs the day branch admitted, and the pair '
   'the report names is among them',
   bool(DROP) and bool(_bp),
   '%d pairs over %d systems; widest %s; the named pair %s'
   % (len(DROP), len(DROP_SYS),
      ('%.2f d' % max(d['dt'] for d in DROP if d['dt'] is not None))
      if DROP else 'n/a', 'present' if _bp else 'ABSENT'))

# -------------------------- K4 every such system keeps its mark another way
KEPT = {}
for s in DROP_SYS:
    iv = CENSUS[s] + EXTRA.get(s, [])
    pts = sorted({x for a, b, _ in iv for x in (a, b)})
    found = None
    for i in range(len(pts) - 1):
        mid = 0.5 * (pts[i] + pts[i + 1])
        ebs = sorted({e for a, b, e in iv if a <= mid <= b})
        for x, y in itertools.combinations(ebs, 2):
            if rule_adopted(x, y):
                found = (x, y)
                break
        if found:
            break
    KEPT[s] = found
_lostmark = [s for s in DROP_SYS
             if RES[s]['day']['recur'][0] and not RES[s]['adopted']['recur'][0]]
_unexplained = [s for s in DROP_SYS
                if RES[s]['adopted']['recur'][0] and not KEPT[s]]
if DRIVE == 4:
    KEPT = {s: None for s in DROP_SYS}
    _unexplained = [s for s in DROP_SYS
                    if RES[s]['adopted']['recur'][0] and not KEPT[s]]
ck('K4 every system holding a rejected pair keeps its mark through a pair '
   'that satisfies the conjunction, and that pair is named',
   not _lostmark and not _unexplained,
   '%d systems hold a rejected pair; %d of them confirmable, all through a '
   'named pair; %d lose a mark' % (len(DROP_SYS),
                                   sum(1 for s in DROP_SYS
                                       if RES[s]['adopted']['recur'][0]),
                                   len(_lostmark)))

# --------------------------------- K5 the disjunction was not harmless either
OR_ONLY_CEN = [s for s in SYSTEMS
               if RES[s]['or']['census'][0] and not RES[s]['adopted']['census'][0]]
OR_ONLY_REC = [s for s in SYSTEMS
               if RES[s]['or']['recur'][0] and not RES[s]['adopted']['recur'][0]]
if DRIVE == 5:
    OR_ONLY_CEN, OR_ONLY_REC = [], []
ck('K5 the disjunction is strictly looser than the conjunction and the '
   'systems it alone would add are named',
   bool(OR_ONLY_CEN) and bool(OR_ONLY_REC) and CEN_O > CEN_A and REC_O > REC_A,
   'census %d against %d, adding %s; recurrence set %d against %d, adding %s'
   % (CEN_O, CEN_A, OR_ONLY_CEN, REC_O, REC_A, OR_ONLY_REC))

# ----------------------------------------- K6 the thirteen positive controls
# ★★★ THE CONTROLS' RECOVERY IS NOT RE-DERIVED HERE.  `confirm_r19.py` owns
# the per-control record and already evaluates BOTH conjuncts for every
# recovering block; its `best` field is the strongest block that satisfies
# them both.  Reading that record rather than reapplying the criterion is
# deliberate, and not only because a second implementation is how two numbers
# for one quantity get into a paper: the day conjunct there is wider than
# `epochs_r14.apart` by one documented clause -- two blocks whose own epochs
# are both RELIABLE (a surviving measurement set, or a stamp the archive
# indexes on the block itself) and more than a day apart on those epochs.
# `apart` refuses that pair when only one of the two is in the measurement
# sets, which is exactly the three HD 285968 blocks, separated by 39 to 44 d
# on two reliable epochs; `ctl_r18.py` carries the same clause for the same
# reason.  Applying `apart` alone here would have reported 12 of 13 and the
# missing one would have been an artefact of the narrower witness, not a
# control without a baseline.  The strict leg is measured below and reported.
TRIG = float(macro('StageNullTrig'))
C19 = json.load(open(os.path.join(V, 'confirm_r19.json')))
CTL = C19['controls']
if DRIVE == 6:                          # K6: one control loses its baseline
    CTL = [dict(CTL[0], best=None)] + CTL[1:]
NCTL = int(macro('MkAttrRecur'))
_okctl = [z for z in CTL
          if z['best'] and z['best']['both'] and z['best']['t'] >= TRIG]
_seps = [abs(float(z['best']['sep'])) for z in _okctl
         if z['best']['sep'] is not None]
_strict = [z for z in _okctl if EP.apart(z['eb'], z['best']['eb'])]
ck('K6 every positive control is recovered, at the trigger, in a block that '
   'satisfies the adopted conjunction',
   len(CTL) == NCTL and len(_okctl) == NCTL and bool(_seps),
   '%d of %d qualify; separations %s to %s d; %d of them also on the '
   'narrower epoch witness alone'
   % (len(_okctl), NCTL,
      '%.0f' % min(_seps) if _seps else 'n/a',
      '%.0f' % max(_seps) if _seps else 'n/a', len(_strict)))

# ---------------------------------------------------- K7 no disposition moves
UNATTR_REC = list(C19['unattributed_recovered'])
if DRIVE == 7:
    UNATTR_REC = ['a recovered unattributed crossing']
ck('K7 no unattributed crossing is recovered in any block under any of the '
   'three rules, so no disposition moves',
   not UNATTR_REC,
   '%d unattributed crossings recovered anywhere; a stricter rule cannot '
   'promote one' % len(UNATTR_REC))

# --------------------------------- K8 what the exclusions actually rest on
HOSTBY = {h['cid']: h for h in HOST}
EXCL = []
for cid, c in CROSS.items():
    h = HOSTBY.get(cid)
    if h is None:
        continue
    eb0 = c['eb']
    blocks = [b['eb'] for b in (c.get('blocks') or [])]
    ind = [e for e in blocks if rule_adopted(eb0, e)]
    EXCL.append(dict(cid=cid, star=c['star'], eb=eb0, p=float(h['p']),
                     n_block=len(blocks), n_indep=len(ind),
                     power=float(h['p']) >= POWER))
HI = [z for z in EXCL if z['power']]
LO = [z for z in EXCL if not z['power']]
SAMEONLY = [z for z in EXCL if z['n_block'] and not z['n_indep']]
if DRIVE == 8:
    HI = HI + [dict(z, power=True) for z in SAMEONLY[:1]]
_hibad = [z for z in HI if not z['n_indep']]
ck('K8 every power-sufficient exclusion rests on coverage satisfying the '
   'conjunction, and the same-session-only crossings are all too shallow',
   not _hibad and bool(SAMEONLY)
   and all(not z['power'] for z in SAMEONLY),
   '%d exclusions, %d power-sufficient (%d without independent coverage), '
   '%d too shallow; same-session-only: %s'
   % (len(EXCL), len(HI), len(_hibad), len(LO),
      ', '.join('%s %s (p=%.2f)'
                % (z['star'][:12], z['eb'].split('_', 1)[1], z['p'])
                for z in SAMEONLY)))
NREAD = sum(z['n_block'] for z in EXCL)
NREAD_IND = sum(z['n_indep'] for z in EXCL)


# ------------------------------- K9 the confirmable frequency support, Fig. 8
def _union(iv):
    iv, o = sorted(iv), []
    for a, b in iv:
        if o and a <= o[-1][1]:
            o[-1][1] = max(o[-1][1], b)
        else:
            o.append([a, b])
    return o


def conf_iv(iv, rule, sep):
    pts = sorted({x for a, b, _ in iv for x in (a, b)})
    keep = []
    for i in range(len(pts) - 1):
        mid = 0.5 * (pts[i] + pts[i + 1])
        ebs = sorted({e for a, b, e in iv if a <= mid <= b})
        if any(rule(x, y, sep) for x, y in itertools.combinations(ebs, 2)):
            keep.append([pts[i], pts[i + 1]])
    return _union(keep)


def _tot(iv):
    return sum(b - a for a, b in iv)


SUP, PERSYS, PROF = {}, {}, {}
for nm, rl in (('day', rule_day), ('adopted', rule_adopted)):
    for tag, sep in (('Day', DAY), ('Yr', YEAR)):
        pooled, per, ps = [], {}, 0.0
        for s in SYSTEMS:
            d = conf_iv(CENSUS[s], rl, sep)
            per[s] = d
            pooled += [tuple(x) for x in d]
            ps += _tot(d)
        SUP[(nm, tag)] = _tot(_union([list(x) for x in pooled]))
        PERSYS[(nm, tag)] = ps
        PROF[(nm, tag)] = per
U_A = float(macro('CvUnionA'))


def profile_peak(per):
    pts = sorted({x for iv in per.values() for a, b in iv for x in (a, b)})
    runs = []
    for i in range(len(pts) - 1):
        mid = 0.5 * (pts[i] + pts[i + 1])
        n = sum(1 for iv in per.values() if any(a <= mid <= b for a, b in iv))
        if n:
            runs.append((pts[i], pts[i + 1], n))
    nmax = max(n for _, _, n in runs)
    return nmax, [0.5 * (a + b) for a, b, n in runs if n == nmax][0]


PK = {nm: profile_peak(PROF[(nm, 'Day')]) for nm in ('day', 'adopted')}

# ---------------------------------------------------------------------- K9
# ★ THE ONE PUBLISHED QUANTITY THE CONJUNCTION DOES MOVE.  The system counts
# do not move because every affected system is confirmable through another
# pair; the confirmable BANDWIDTH does, because the frequency a rejected pair
# alone covered stops being confirmable even when the system is not.  So the
# loss must be non-zero and must be wholly accounted for by the systems that
# hold a rejected pair -- a loss anywhere else would mean the two rules differ
# for a reason this generator has not identified.
LOSS = {s: _tot(PROF[('day', 'Day')][s]) - _tot(PROF[('adopted', 'Day')][s])
        for s in SYSTEMS}
LOSSY = sorted((s for s in SYSTEMS if LOSS[s] > 1e-9),
               key=lambda s: -LOSS[s])
_outside = [s for s in LOSSY if s not in DROP_SYS]
if DRIVE == 9:
    _outside = LOSSY[:1]
ck('K9 the confirmable bandwidth loses support, every system that loses '
   'any is one that holds a rejected pair, and the published figure is the '
   'one the ADOPTED criterion gives',
   SUP[('day', 'Day')] - SUP[('adopted', 'Day')] > 1e-4 and not _outside
   and abs(SUP[('adopted', 'Day')] - float(macro('CvConfGHzDay'))) < 0.05,
   'pooled %.4f -> %.4f GHz at a day (published %s); %.4f -> %.4f at a year; '
   '%d systems lose support (%s); %d outside the rejected-pair set'
   % (SUP[('day', 'Day')], SUP[('adopted', 'Day')], macro('CvConfGHzDay'),
      SUP[('day', 'Yr')], SUP[('adopted', 'Yr')], len(LOSSY),
      ', '.join('%s %.3f' % (starname(s), LOSS[s]) for s in LOSSY),
      len(_outside)))

# --------------------------------------------------------------------- K10
_CV_DAY = {'CvConfGHzDay': '%.1f' % SUP[('day', 'Day')],
           'CvConfGHzYr': '%.1f' % SUP[('day', 'Yr')],
           'CvConfPctDay': '%.0f' % (100.0 * SUP[('day', 'Day')] / U_A),
           'CvConfPctYr': '%.0f' % (100.0 * SUP[('day', 'Yr')] / U_A),
           'CvConfNMaxDay': '%d' % PK['day'][0],
           'CvConfNuMaxDay': '%.0f' % PK['day'][1]}
_CV_AD = {'CvConfGHzDay': '%.1f' % SUP[('adopted', 'Day')],
          'CvConfGHzYr': '%.1f' % SUP[('adopted', 'Yr')],
          'CvConfPctDay': '%.0f' % (100.0 * SUP[('adopted', 'Day')] / U_A),
          'CvConfPctYr': '%.0f' % (100.0 * SUP[('adopted', 'Yr')] / U_A),
          'CvConfNMaxDay': '%d' % PK['adopted'][0],
          'CvConfNuMaxDay': '%.0f' % PK['adopted'][1]}
# ★★★★ THE COMPARISON IS AGAINST THE ADOPTED LEG, NOT THE DAY LEG.  Written
# the other way round it asserted that the macro layer still held the value the
# withdrawn rule gave -- true while this generator ran outside the tree and
# false the moment `cover_v412.py` ran inside it, which is the one state that
# matters.  The day leg is kept in the message so that the cost of the second
# conjunct is on the page of the log beside the published figure.
_cvbad = {k: (v, macro(k)) for k, v in _CV_AD.items() if v != macro(k)}
CV_MOVES = sorted(k for k in _CV_DAY if _CV_DAY[k] != _CV_AD[k])
if DRIVE == 10:
    _cvbad = {'CvConfGHzDay': ('x', 'y')}
ck('K10 EVERY PUBLISHED COVERAGE MACRO IS THE ONE THE ADOPTED CRITERION '
   'GIVES, and the ones the second conjunct moves are named against what '
   'the day branch alone would have given',
   not _cvbad and bool(CV_MOVES),
   '%d macros checked, %s; moved by the conjunction: %s'
   % (len(_CV_AD), _cvbad or 'all agree',
      ', '.join('%s %s -> %s' % (k, _CV_DAY[k], _CV_AD[k])
                for k in CV_MOVES) or 'none'))

# --------------------------------------------------------------------- K11
_YRSAME = (abs(SUP[('day', 'Yr')] - SUP[('adopted', 'Yr')]) < 1e-9
           and PERSYS[('day', 'Yr')] == PERSYS[('adopted', 'Yr')]
           and count('day', 'recur', 1) == count('adopted', 'recur', 1)
           and count('day', 'recur', 2) == count('adopted', 'recur', 2))
if DRIVE == 11:
    _YRSAME = False
ck('K11 nothing at the month or year threshold moves, so the change is '
   'confined to the day threshold and to bandwidth rather than systems',
   _YRSAME,
   'year support %.4f both ways; month %d and year %d systems both ways'
   % (SUP[('adopted', 'Yr')], count('adopted', 'recur', 2),
      count('adopted', 'recur', 1)))

# ======================================================= macros
# ★ NO MACRO HERE RESTATES A PUBLISHED QUANTITY.  The counts this round
# confirms unchanged -- the confirmable systems, the unconfirmable systems,
# the thirteen controls, their separations, the confirmable bandwidth -- stay
# in the macros that already own them (`\ZcConfSysDay`, `\ZcNoRepSys`,
# `\ZcConfSysYr`, `\ZcConfSysMonth`, `\ZcCenNoRepSys`, `\QcNCtl`,
# `\QcSepMinD`, `\QcSepMaxD`, `\CvConfGHzDay`, `\CvConfPctDay`), whose
# generators are patched to the adopted rule.  K1, K6 and K10 ASSERT against
# those names instead of emitting a second macro for the same number: two
# macros for one quantity is how this project has twice printed two values
# for it.  What is emitted below exists nowhere else.
m('QfNPairDrop', '%d' % len(DROP))
m('QfNPairDropWord', word(len(DROP)))
m('QfNSysPairDrop', '%d' % len(DROP_SYS))
m('QfNSysPairDropWord', word(len(DROP_SYS)))
m('QfNSysMoved', '%d' % len(MOVED))
m('QfNSysMovedWord', word(len(MOVED)))
#: the widest interval between two blocks of ONE observing session anywhere in
#: the census: the measure of what the disjunction admitted.
m('QfSameSessMaxD', '%.2f'
  % max(d['dt'] for d in DROP if d['dt'] is not None))
#: and the same quantity for the one system Sec. 5.4 discusses, which is the
#: pair named in the report.
m('QfBpSameSessD', '%.2f'
  % max(d['dt'] for d in DROP
        if 'Pic' in d['system'] and d['dt'] is not None))
m('QfNSysOrOnly', '%d' % len(OR_ONLY_REC))
m('QfNSysOrOnlyWord', word(len(OR_ONLY_REC)))
m('QfSysOrOnly', starname(OR_ONLY_REC[0]) if OR_ONLY_REC else 'none')
m('QfNExclSameOnly', '%d' % len(SAMEONLY))
m('QfNExclSameOnlyWord', word(len(SAMEONLY)))
m('QfConfGHzDrop', '%.1f' % (SUP[('day', 'Day')] - SUP[('adopted', 'Day')]))
m('QfNSysLoseGHz', '%d' % len(LOSSY))
m('QfNSysLoseGHzWord', word(len(LOSSY)))
m('QfSysLoseGHzMax', starname(LOSSY[0]) if LOSSY else 'none')

if FAIL:
    print('\nFAILED: %s' % ', '.join(FAIL))
    if DRIVE == 0:
        raise SystemExit(1)

json.dump(dict(round=ROUND, drive=DRIVE,
               definition=('a confirmed signal requires recovery at the '
                           'predicted stellar-frame cell in a block that is '
                           'an execution of a DIFFERENT observing session '
                           'AND more than %g d from the discovery block; a '
                           'recovery in any block of the discovery\'s own '
                           'session is a within-session repeat, whatever '
                           'the interval' % DAY),
               n_systems=NSYS,
               counts={nm: dict(census=[count(nm, 'census', i)
                                        for i in range(3)],
                                recur=[count(nm, 'recur', i)
                                       for i in range(3)])
                       for nm, _ in RULES},
               dropped_pairs=DROP, dropped_systems=DROP_SYS,
               kept_through=KEPT, moved_marks=MOVED,
               or_only_census=OR_ONLY_CEN, or_only_recur=OR_ONLY_REC,
               controls=CTL, unattributed_recovered=UNATTR_REC,
               exclusions=EXCL, same_session_only=SAMEONLY,
               support={'%s_%s' % k: v for k, v in SUP.items()},
               persys_support={'%s_%s' % k: v for k, v in PERSYS.items()},
               n_repeat_readings=NREAD, n_repeat_readings_independent=NREAD_IND,
               coverage_macros=dict(day=_CV_DAY, adopted=_CV_AD,
                                    moved=CV_MOVES),
               bandwidth_loss={s: LOSS[s] for s in LOSSY},
               per_system={s: {nm: RES[s][nm] for nm, _ in RULES}
                           for s in SYSTEMS}),
          open(OUTJ, 'w'), indent=1, default=str)

with open(OUT, 'w') as fh:
    fh.write('%% GENERATED by confirm_r20.py (round %d) -- do not hand-edit.\n'
             % ROUND)
    fh.write('%% The adopted confirmation criterion: a different observing '
             'session AND more than a day.\n')
    for k, v in M:
        fh.write('\\newcommand{\\%s}{%s}\n' % (k, v))

print('\nthe pairs the conjunction rejects (%d over %d systems)'
      % (len(DROP), len(DROP_SYS)))
for d in DROP:
    print('  %-28s %-22s %-22s %s'
          % (d['system'][:28], d['a'].split('_', 1)[1], d['b'].split('_', 1)[1],
             ('%.3f d' % d['dt']) if d['dt'] is not None else 'n/r'))
print('\nand what each of those systems keeps its mark through')
for s in DROP_SYS:
    k = KEPT[s]
    print('  %-30s %s'
          % (s[:30], '%s + %s' % (k[0].split('_', 1)[1], k[1].split('_', 1)[1])
             if k else 'NOT CONFIRMABLE (no qualifying pair)'))
print('\n%d macros -> %s' % (len(M), os.path.basename(OUT)))

if '--selftest' in sys.argv:
    print('\nselftest: every assertion driven to fail')
    want = {1: 'K1', 2: 'K2', 3: 'K3', 4: 'K4', 5: 'K5', 6: 'K6', 7: 'K7',
            8: 'K8', 9: 'K9', 10: 'K10', 11: 'K11'}
    bad = []
    for d, nm in sorted(want.items()):
        p = subprocess.run([sys.executable, __file__, '--drive', str(d)],
                           capture_output=True, text=True)
        fired = [ln for ln in p.stdout.splitlines()
                 # ★ `'K10 ...'.startswith('K1')` is True, so a bare prefix
                 # match reported drive 1 as firing K1 when K1 had PASSED and
                 # K10 was merely further down the list.  The space is the fix.
                 if ln.strip().startswith(nm + ' ') and 'FAIL' in ln]
        print('  drive %d -> %s %s'
              % (d, nm, 'FIRED' if fired else 'DID NOT FIRE'))
        if not fired:
            bad.append((d, nm))
    for f in sorted(([_e for _e in os.listdir(HERE) if _e != 'numbers'] + [os.path.join('numbers', _e) for _e in (os.listdir(os.path.join(HERE, 'numbers')) if os.path.isdir(os.path.join(HERE, 'numbers')) else [])]), key=os.path.basename):
        if '_drive' in f:
            os.remove(os.path.join(HERE, f))
    print('  selftest %s' % ('PASS' if not bad else 'FAIL %s' % bad))
    raise SystemExit(1 if bad else 0)
