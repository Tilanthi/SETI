#!/usr/bin/env python3
r"""pairacct_r23.py -- the accounting that takes the widened recurrence
window's exceedances to the pairs the trajectory test is asked of, and the
count of systems with three or more separated covering epochs.

Round 981.  Writes `survey_numbers_round981.tex`, `tab_pairacct_r23.tex` and
`pairacct_r23.json`.

WHY THIS EXISTS.  Two numbers sit side by side in the recurrence section --
the exceedances the widened window holds, and the pairs at least one of whose
members is unattributed -- and nothing connects them.  They are not two views
of one set: the first is a count of WINDOW READINGS, one per (crossing,
covering window) combination, and the second is a count of CROSSING PAIRS.
Three distinct effects separate them, and each is measured here:

 1. A pair whose two members are both unattributed discovery crossings is
    read TWICE, once from each member, because each member's own covering
    windows include the other's block.  Those readings are not independent
    trials and must not be counted as two pairs.

 2. The covering window is wider than the interval the pair test admits.
    The window a repeat could be found in has a median half-width of
    \WdHalfKms km/s, and the pair test uses that half-width as its interval,
    so an exceedance in a window WIDER than the median can fall outside it.

 3. A pair can be formed from the crossing ledger that no covering window
    delivers, because the statistic recorded for that window at the star and
    the statistic the ledger carries for the crossing inside it are read over
    different fields.  THE NUMBER IN THAT ROW IS THEREFORE A MEASURE OF HOW
    FAR THE TWO READINGS DISAGREE, and on a single extraction it is zero.

AND THE THREE-EPOCH QUESTION.  A criterion that can ACCEPT a drifting carrier
cannot be read at one predicted cell: with two epochs a circular orbit has as
many free parameters as the pair has measurements, so the orbit is determined
rather than tested.  Three separated epochs covering one frequency would
over-determine it.  Whether that is reachable here is a property of the
archive and is measured: for every system the largest set of blocks covering
ONE common frequency that are PAIRWISE separated in the sense of the
confirmation criterion -- a different observing session and more than a day
apart.  The predicate is `epochs_r14.confirms` and not a second
implementation of it, and the >=2 and ==1 columns of the resulting histogram
are asserted against the published confirmability counts, so this is the
paper's own criterion counted one level deeper.

NO NUMBER HERE IS TYPED.  Every row of the table and every macro is computed
from `ledger.json`, `per_target_results_v3.99.csv` and
`r10inputs/recur_v411.json`, the same three inputs the two sides of the
accounting already use, and the chain is asserted to close.

Usage: pairacct_r23.py [--drive N]
"""
import collections
import csv
import glob
import itertools
import json
import math
import os
import re
import sys

import epochs_r14 as ep

HERE = os.path.dirname(os.path.abspath(__file__))
ROUND = 981
DRIVE = int(sys.argv[sys.argv.index('--drive') + 1]) if '--drive' in sys.argv \
    else 0
SFX = '' if DRIVE == 0 else '_drive%d' % DRIVE
OUT = os.path.join(HERE, 'numbers/survey_numbers_round981%s.tex' % SFX)
OUTT = os.path.join(HERE, 'tab_pairacct_r23%s.tex' % SFX)
OUTJ = os.path.join(HERE, 'pairacct_r23%s.json' % SFX)

CKMS = 299792.458
TRIG = 5.0

M, FAIL = [], []


def m(k, v):
    assert k.isalpha(), 'a LaTeX macro name may contain letters only: ' + k
    assert k not in dict(M), 'macro defined twice: ' + k
    M.append((k, str(v)))


def ck(name, cond, detail=''):
    if not cond:
        FAIL.append(name)
    print('  %-70s %s  %s' % (name, 'PASS' if cond else 'FAIL', detail))


def macro(name):
    """One macro's value out of the frozen layer, by name."""
    pat = re.compile(r'\\(?:new|renew|provide)command\{\\%s\}'
                     r'\{((?:[^{}]|\{[^{}]*\})*?)\}' % name)
    v = None
    for fn in sorted(glob.glob(os.path.join(HERE, 'numbers/survey_numbers*.tex'))):
        if '_drive' in fn:
            continue
        for mm in pat.finditer(open(fn, encoding='utf-8').read()):
            if mm.group(1).strip():
                v = mm.group(1).strip()
    if v is None:
        raise SystemExit('macro %s not found' % name)
    return v


# ------------------------------------------------------------------ inputs
CAT = list(csv.DictReader(open(os.path.join(
    HERE, 'per_target_results_v3.99.csv'), encoding='utf-8')))
LED = json.load(open(os.path.join(HERE, 'ledger.json'), encoding='utf-8'))
REC = json.load(open(os.path.join(HERE, 'r10inputs', 'recur_v411.json'),
                     encoding='utf-8'))
CROSS = REC['crossings']
ROWS = LED['rows']

#: the pair test's interval, read from the frozen layer rather than chosen
#: here: it is the median covering window's half-width and the two sides of
#: this accounting must use one value of it.
HALF_KMS = float(macro('WdHalfKms'))

#: WHAT A WINDOW IS READ ON.  The per-window catalogue carries the released
#: maximum of each window; the crossing ledger carries the adopted statistic
#: and frequency of every cell above the trigger, and the re-extraction
#: deposit the whole-beam statistic of every window extracted with its own
#: observation's antenna geometry.  This accounting reads the adopted record
#: wherever one exists, which is the same rule the covering-window scan uses,
#: so a reading and a ledger crossing are the same object seen twice.  The
#: window key puts the edges in min/max order: a descending spectral window
#: writes them reversed.
REPAIR = {}
for _d in csv.DictReader(open(os.path.join(HERE, 'repaired_v409.csv'),
                              encoding='utf-8')):
    _lo, _hi = float(_d['flo_GHz']), float(_d['fhi_GHz'])
    REPAIR[(_d['eb'], round(min(_lo, _hi), 4),
            round(max(_lo, _hi), 4))] = float(_d['star_peak_snr_repaired'])
LEDEB = {}
for _l in ROWS:
    LEDEB.setdefault(_l['eb'], []).append(_l)


def wread(q):
    """The adopted statistic of one window, and the frequency it is read at."""
    lo, hi = float(q['flo_GHz']), float(q['fhi_GHz'])
    lo, hi = min(lo, hi), max(lo, hi)
    cat = (float(q['star_snr']),
           float(q['f_cross_GHz']) if q['f_cross_GHz'] else None)
    if DRIVE == 7:                # the released record where an adopted one exists
        return cat
    inside = [_l for _l in LEDEB.get(q['eb'], [])
              if lo <= float(_l['freq']) <= hi]
    if inside:
        best = max(inside, key=lambda _l: float(_l['tstar']))
        return float(best['tstar']), float(best['freq'])
    rep = REPAIR.get((q['eb'], round(lo, 4), round(hi, 4)))
    return (cat[0] if rep is None else rep), cat[1]

BYEB, BYSYS = collections.defaultdict(list), collections.defaultdict(list)
for _r in CAT:
    BYEB[_r['eb']].append(_r)
    BYSYS[_r['system_id']].append(_r)


def blocks(c):
    """The covering repeat blocks of one crossing, with the paper's own
    weight-pathology list applied."""
    return [b for b in c.get('blocks', []) if not b.get('bad_weight_product')]


CRK = {(c['eb'], round(float(c['freq_GHz']), 4)): c for c in CROSS.values()}
UNATTR = [r for r in ROWS if not r['attributed']]

# =====================================================================
# 1.  THE COVERING WINDOWS, AND WHAT THEY HOLD
# =====================================================================
# Reproduced from the same three inputs rather than read from the recurrence
# record, so that the two sides of the accounting cannot be one side twice.
COVSET = {}
for r in UNATTR:
    f, eb = float(r['freq']), r['eb']
    dw = [q for q in BYEB.get(eb, [])
          if float(q['flo_GHz']) <= f <= float(q['fhi_GHz'])]
    sid = dw[0]['system_id'] if len(dw) == 1 else None
    if sid is None:
        c = CRK.get((eb, round(f, 4)))
        for b in blocks(c or {}) if c else []:
            q = [x for x in BYEB.get(b['eb'], [])
                 if float(x['flo_GHz']) <= b['f_here_GHz']
                 <= float(x['fhi_GHz'])]
            if q:
                sid = q[0]['system_id']
                break
    assert sid, 'no system identifier for %s %s' % (r['star'], eb)
    cov = [q for q in BYSYS[sid] if q['eb'] != eb
           and float(q['flo_GHz']) <= f <= float(q['fhi_GHz'])]
    COVSET[(eb, round(f, 4))] = (sid, cov)

NCOV = sum(len(v[1]) for v in COVSET.values())
if DRIVE == 6:                    # a covering window counted twice
    NCOV += 1
NCROSSCOV = sum(1 for v in COVSET.values() if v[1])
READ = []
for k, (sid, cov) in COVSET.items():
    for q in cov:
        _st, _fr = wread(q)
        if _st >= TRIG:
            READ.append(dict(disc=k, rep_eb=q['eb'],
                             rep_f=round(_fr, 4) if _fr else None,
                             win=(q['eb'], q['flo_GHz'], q['fhi_GHz'])))
if DRIVE == 1:                    # a reading that lands on no crossing
    READ.append(dict(disc=list(COVSET)[0], rep_eb='A002_X0_X0',
                     rep_f=0.0, win=('A002_X0_X0', '0', '1')))
NEXC = len(READ)
m('PaNCovWinCross', '%d' % NCROSSCOV)
ck('A1 the covering windows and the exceedances among them reproduce the '
   'published pair of counts from the catalogue and the ledger alone',
   NCOV == int(macro('WdNCov')) and NEXC == int(macro('WdNExc')),
   '%d windows and %d above the trigger against %s and %s published'
   % (NCOV, NEXC, macro('WdNCov'), macro('WdNExc')))

# =====================================================================
# 2.  FROM READINGS TO CROSSING PAIRS
# =====================================================================
BYK = {(r['eb'], round(float(r['freq']), 4)): r for r in ROWS}
PAIRED = collections.defaultdict(list)
nocross = 0
for d in READ:
    rk = (d['rep_eb'], d['rep_f'])
    if rk not in BYK:
        nocross += 1
        continue
    PAIRED[tuple(sorted([d['disc'], rk]))].append(d)
ck('A2 every reading above the trigger lands on a crossing the ledger lists, '
   'so a reading and a pair are the same objects counted two ways',
   nocross == 0, '%d readings with no ledger crossing' % nocross)

NFROM = len(PAIRED)
NDOUBLE = NEXC - NFROM
NREPWIN = len({d['win'] for d in READ})
NREPEB = len({d['rep_eb'] for d in READ})


def dvs(a, b):
    fa = float(BYK[a]['frame']['f_stellar'])
    fb = float(BYK[b]['frame']['f_stellar'])
    return CKMS * (fb - fa) / (0.5 * (fa + fb))


BEYOND = [k for k in PAIRED if abs(dvs(*k)) > HALF_KMS]
INSIDE = [k for k in PAIRED if abs(dvs(*k)) <= HALF_KMS]
if DRIVE == 4:                    # a pair outside the interval, lost
    BEYOND = BEYOND[:-1]
m('PaNRepWin', '%d' % NREPWIN)
m('PaNRepBlock', '%d' % NREPEB)
m('PaNPairRead', '%d' % NFROM)
m('PaNPairTwice', '%d' % NDOUBLE)
m('PaNPairBeyond', '%d' % len(BEYOND))
m('PaNPairInside', '%d' % len(INSIDE))
m('PaDvBeyondMax', '%.0f' % max(abs(dvs(*k)) for k in BEYOND))

# =====================================================================
# 3.  THE PAIRS THE LEDGER FORMS, ON THE PAIR TEST'S OWN ENUMERATION
# =====================================================================
# Keyed on the system the catalogue gives each crossing's own window, and on
# the canonical star only for the archival-tail crossings the released
# catalogue carries no window for -- the same order of authority the pair
# test uses, and never a name where a position is available.


def _norm(s):
    return ''.join(ch for ch in s.split(' Gaia')[0].lower() if ch.isalnum())


SYS_BY_STAR = {}
for _r in CAT:
    SYS_BY_STAR.setdefault(_norm(_r['star_name']), _r['system_id'])
KEY = {}
for r in ROWS:
    k = (r['eb'], round(float(r['freq']), 4))
    w = [q for q in BYEB.get(r['eb'], [])
         if float(q['flo_GHz']) <= float(r['freq']) <= float(q['fhi_GHz'])]
    KEY[k] = w[0]['system_id'] if w else SYS_BY_STAR.get(_norm(r['star']),
                                                         'x' + _norm(r['star']))
CAND = []
for a, b in itertools.combinations(sorted(BYK), 2):
    if a[0] == b[0] or KEY[a] != KEY[b]:
        continue
    if abs(dvs(a, b)) > HALF_KMS:
        continue
    CAND.append((a, b))
CU = [p for p in CAND if not (BYK[p[0]]['attributed']
                              and BYK[p[1]]['attributed'])]
if DRIVE == 3:                    # a pair the ledger forms, dropped
    CU = CU[:-1]
LEDONLY = [p for p in CU if tuple(sorted(p)) not in PAIRED]
ck('A3 the pairs with an unattributed member reproduce the published count, '
   'and the ones the covering windows deliver are a subset of them',
   len(CU) == int(macro('TjNCandPair'))
   and all(tuple(sorted(k)) in {tuple(sorted(p)) for p in CU}
           for k in INSIDE),
   '%d pairs, %d of them delivered by a covering window and %d only by the '
   'ledger' % (len(CU), len(CU) - len(LEDONLY), len(LEDONLY)))
ck('A4 the chain closes: the readings less the ones counted twice, less the '
   'ones outside the interval, plus the ones only the ledger forms, are the '
   'pairs with an unattributed member',
   NEXC - NDOUBLE - len(BEYOND) + len(LEDONLY) == len(CU),
   '%d - %d - %d + %d = %d' % (NEXC, NDOUBLE, len(BEYOND), len(LEDONLY),
                               len(CU)))
ck('A7 and no pair the ledger forms is missing from the covering windows, so '
   'the two sides of this accounting are read off one record',
   not LEDONLY,
   '%d pair(s) the covering windows do not deliver%s'
   % (len(LEDONLY), '' if not LEDONLY else ': ' + repr(sorted(LEDONLY)[:2])))

# =====================================================================
# 4.  THREE OR MORE SEPARATED EPOCHS AT ONE FREQUENCY
# =====================================================================
# The interval lists are the ones the confirmability census is scored on: the
# Class A census windows, plus the cell each recurrence reading was taken at.
CLA = [r for r in CAT if r['search_class'] == 'A']


def edges(r):
    a, b = float(r['flo_GHz']), float(r['fhi_GHz'])
    return min(a, b), max(a, b)


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


SYSOF = {}
for cid, c in CROSS.items():
    i = window_of(c['eb'], c['freq_GHz'])
    SYSOF[cid] = CAT[i]['system_id'] if i is not None \
        else SYS_BY_STAR.get(_norm(c['star']))
EXTRA = collections.defaultdict(list)
for cid, c in CROSS.items():
    sid = SYSOF.get(cid)
    if sid is None:
        continue
    for b in blocks(c):
        half = 0.5 * float(b['chanw_Hz']) / 1e9
        f = float(b['f_here_GHz'])
        EXTRA[sid].append((f - half, f + half, b['eb']))
    d = c.get('discovery')
    if d:
        half = 0.5 * float(d['chanw_Hz']) / 1e9
        EXTRA[sid].append((float(c['freq_GHz']) - half,
                           float(c['freq_GHz']) + half, c['eb']))

_CONF = {}


def confirms(a, b):
    """The confirmation criterion, from the module that owns it."""
    if (a, b) not in _CONF:
        _CONF[(a, b)] = _CONF[(b, a)] = ep.confirms(a, b)
    return _CONF[(a, b)]


def clique(ebs):
    """The largest set of these blocks that is PAIRWISE separated."""
    ebs = sorted(set(ebs))
    if not ebs:
        return 0
    adj = {a: {b for b in ebs if b != a and confirms(a, b)} for a in ebs}
    best = [1]

    def grow(size, cands):
        if size > best[0]:
            best[0] = size
        cl = sorted(cands)
        for i, v in enumerate(cl):
            if size + len(cl) - i <= best[0]:
                break
            grow(size + 1, {w for w in cl[i + 1:] if w in adj[v]})

    grow(0, set(ebs))
    return best[0]


def maxepochs(iv):
    """The deepest pairwise-separated coverage of any one frequency, and the
    frequency it is reached at.  Evaluated between interval boundaries, so no
    island can be lost to a grid."""
    pts = sorted({x for a, b, _ in iv for x in (a, b)})
    best, bf = 0, None
    for i in range(len(pts) - 1):
        mid = 0.5 * (pts[i] + pts[i + 1])
        k = clique([e for a, b, e in iv if a <= mid <= b])
        if k > best:
            best, bf = k, mid
    return best, bf


SYSTEMS = sorted(CENSUS)
DEPTH = {}
for sid in SYSTEMS:
    DEPTH[sid] = maxepochs(CENSUS[sid] + EXTRA.get(sid, []))
if DRIVE == 2:                    # a system credited with an epoch it lacks
    _s = sorted(SYSTEMS)[0]
    DEPTH[_s] = (DEPTH[_s][0] + 1, DEPTH[_s][1])
HIST = collections.Counter(v[0] for v in DEPTH.values())
if DRIVE == 5:                    # a sample with no third epoch anywhere
    HIST = collections.Counter({1: HIST.get(1, 0),
                                2: len(DEPTH) - HIST.get(1, 0)})
NTWO = sum(n for k, n in HIST.items() if k >= 2)
NTHREE = sum(n for k, n in HIST.items() if k >= 3)
NFOUR = sum(n for k, n in HIST.items() if k >= 4)
NONE_ = HIST.get(1, 0)
DEEP = max(DEPTH.items(), key=lambda z: z[1][0])
m('PaNSysThree', '%d' % NTHREE)
ck('A5 the one- and two-epoch columns of this histogram ARE the published '
   'confirmability counts, so the three-epoch column is the paper\'s own '
   'criterion counted one level deeper and not a second rule',
   NTWO == int(macro('ZcConfSysDay')) and NONE_ == int(macro('ZcNoRepSys'))
   and len(SYSTEMS) == int(macro('NSysClassA')),
   '%d systems: %d with one epoch (published %s), %d with two or more '
   '(published %s), %d with three or more'
   % (len(SYSTEMS), NONE_, macro('ZcNoRepSys'), NTWO,
      macro('ZcConfSysDay'), NTHREE))
ck('A6 and a three-epoch criterion is not limited by the epochs: more than '
   'a third of the sample has them',
   NTHREE > 0.33 * len(SYSTEMS),
   '%d of %d systems, deepest %d at %.4f GHz'
   % (NTHREE, len(SYSTEMS), DEEP[1][0], DEEP[1][1]))

# =====================================================================
# 5.  THE TABLE
# =====================================================================
TROWS = [
    (r'Covering windows read, over the \PaNCovWinCross{} unattributed '
     r'crossings a later block covers', r'\WdNCov'),
    (r'\ldots{} holding a statistic above the trigger, in \PaNRepWin{} '
     r'windows of \PaNRepBlock{} blocks', r'\WdNExc'),
    (r'Distinct crossing pairs those readings represent', r'\PaNPairRead'),
    (r'\ldots{} readings that are the second reading of such a pair',
     r'\PaNPairTwice'),
    (r'Pairs separated by more than $\pm\WdHalfKms$\,km\,s$^{-1}$ in the '
     r"star's frame, to \PaDvBeyondMax\,km\,s$^{-1}$", r'\PaNPairBeyond'),
    (r'Pairs inside that interval', r'\PaNPairInside'),
    (r'Pairs with at least one unattributed member', r'\TjNCandPair'),
    (r'\ldots{} with a fitted drift and a block epoch for both members',
     r'\TjNPair'),
    (r'\ldots{} separated by the bounded-trajectory criterion',
     r'\TjNExcl'),
    (r'\ldots{} open', r'\TjNOpen'),
]
with open(OUTT, 'w', encoding='utf-8') as fh:
    fh.write('%% GENERATED by pairacct_r23.py -- do not hand-edit.\n')
    fh.write(r'\begin{tabular}{@{}p{0.76\columnwidth}r@{}}' + '\n')
    fh.write('\\hline\n')
    for i, (lab, val) in enumerate(TROWS):
        fh.write('%s & %s \\\\\n' % (lab, val))
        if i in (1, 5, 7):
            fh.write('\\hline\n')
    fh.write('\\hline\n')
    fh.write(r'\end{tabular}' + '\n')

# =====================================================================
with open(OUT, 'w', encoding='utf-8') as fh:
    fh.write('%% GENERATED by pairacct_r23.py (round %d) -- do not '
             'hand-edit.\n' % ROUND)
    for k, v in M:
        fh.write('\\newcommand{\\%s}{%s}\n' % (k, v))
json.dump(dict(macros=dict(M), hist=dict(HIST),
               depth={k: list(v) for k, v in DEPTH.items()},
               beyond=[[list(x) for x in k] for k in BEYOND],
               ledger_only=[[list(x) for x in p] for p in LEDONLY],
               n_cov=NCOV, n_exc=NEXC, half_kms=HALF_KMS),
          open(OUTJ, 'w'), indent=1, default=str)
print('  %d macros, %d table rows' % (len(M), len(TROWS)))
if FAIL:
    raise SystemExit('FAILED: ' + ', '.join(FAIL))
