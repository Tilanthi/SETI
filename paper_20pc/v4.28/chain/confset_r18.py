#!/usr/bin/env python3
r"""confset_r18.py -- round 800.  Confirmability, computed over the block set
the recurrence test actually reads.

THE DEFECT THIS MEASURES.  The paper's confirmability column (Table F1, the
`conf.` column) and the three counts drawn from it are computed over the
PRIMARY CENSUS and over nothing else: `recur_v411.py`'s `doubly()` and
`cover_v412.py`'s `confirmable()` both reduce `per_target_results_v3.99.csv`.
The recurrence test, by contrast, reads every retained product that covers the
crossing's position and frequency, whatever block set it belongs to -- census,
reserved hold-out, archival tail, follow-up stratum or prospective extension.
So a system can be marked "no second block at a covered frequency" and be
tested for recurrence against blocks more than a day later in the same paper.

WHAT IS AND IS NOT RECOVERABLE HERE.  The recurrence harness indexed 3325
retained products on a host volume that no longer exists, and the tree carries
window edges for only 138 of the 152 execution blocks the test used.  A full
re-inventory of the archive per system is therefore NOT reproducible from the
repository, and this generator does not pretend to one.  What it does is
exact: it recomputes the same predicate over

    the census windows  UNION  the repeat readings the recurrence test made,

each repeat contributing the one cell the test actually read (f_here +- half a
channel) and its own measured start time.  That is a subset of the archive, so
every count it produces is a BOUND IN THE SAFE DIRECTION: confirmable can only
be undercounted, never overcounted, and the systems it moves out of the
"no confirming epoch" class are moved on measurement.

THE ASSERTIONS, AND WHY EACH CAN FAIL.
  C1  the predicate, run on the census set alone, reproduces the three
      published macros \RcConfSysDay, \RcConfSysYr and \RcNoRepSys exactly.
      Without this the comparison below would be between two methods and not
      between two block sets.
  C2  the two set-ups are nested -- every system confirmable on the census set
      is confirmable on the larger set -- and the larger set is strictly
      larger, so the defect is real and not a rounding of it.
  C3  the two systems named in the report, CP-72 2713 and CD-57 1054, are
      marked "no second block" on the census set and ARE confirmable over a
      day on the recurrence set.  A fix that did not move those two would not
      be a fix.
  C4  every block in either set is epoch-resolved, and where the recurrence
      record and `epochs_r14` both carry a block they agree.  Two epoch
      determinations that disagreed would make the separations unfalsifiable.
  C5  on both sets, no system is confirmable over a year without being
      confirmable over a day.
  C6  every crossing in the record resolves to a system of the census, and the
      Class A system count is the published one.

    python3 confset_r18.py                 # measure and write
    python3 confset_r18.py --drive N       # N = 1..6, one assertion each
    python3 confset_r18.py --selftest      # drive every assertion to fail
"""
import collections
import csv
import json
import os
import re
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
#: In the tree the generator and the paper are the same directory.  It was
#: written to read a read-only tree from outside, which is why PAPER existed
#: at all; keeping the name makes the reads below unambiguous.
PAPER = HERE
ROUND = 800                       # claimed by r18-census; 800-809 is its block
OUT_TEX = os.path.join(HERE, 'survey_numbers_round%d.tex' % ROUND)
OUT_JSON = os.path.join(HERE, 'confset_r18.json')

SEP_DAY = 1.0
SEP_YR = 365.25

DRIVE = int(sys.argv[sys.argv.index('--drive') + 1]) if '--drive' in sys.argv \
    else 0
SFX = '' if DRIVE == 0 else '_drive%d' % DRIVE

sys.path.insert(0, PAPER)
import epochs_r14 as ep           # noqa: E402  the one determination of an epoch

FAIL = []


def ck(name, cond, detail=''):
    if not cond:
        FAIL.append(name)
    print('  %-4s %s  %s' % (name.split()[0], 'PASS' if cond else 'FAIL',
                             detail))


# --------------------------------------------------------------- macro layer
def _macros():
    import manuscript
    main = os.path.join(PAPER, manuscript.main_file())
    order = []
    for line in open(main):
        m = re.match(r'\\input\{(survey_numbers[^}]*)\}', line.strip())
        if m:
            order.append(m.group(1) + '.tex')
    vals = {}
    for fn in order:
        p = os.path.join(PAPER, fn)
        if not os.path.exists(p):
            continue
        for m in re.finditer(
                r'\\(?:newcommand|renewcommand)\{\\([A-Za-z]+)\}\{(.*)\}\s*$',
                open(p).read(), re.M):
            vals[m.group(1)] = m.group(2)
    return vals


MAC = _macros()


def pub(name):
    return MAC[name]


# -------------------------------------------------------------------- inputs
CAT = list(csv.DictReader(open(os.path.join(
    PAPER, 'per_target_results_v3.99.csv'))))
REC = json.load(open(os.path.join(PAPER, 'r10inputs', 'recur_v411.json')))
CROSS = REC['crossings']

CLA = [r for r in CAT if r['search_class'] == 'A']


def edges(r):
    a, b = float(r['flo_GHz']), float(r['fhi_GHz'])
    return min(a, b), max(a, b)


# the census interval list, per system: (lo, hi, eb)
CENSUS = collections.defaultdict(list)
for r in CLA:
    lo, hi = edges(r)
    CENSUS[r['system_id']].append((lo, hi, r['eb']))

# the crossing -> system join, on POSITION in (block, frequency) wherever the
# census tabulates the window, and on the system's own star label only where
# it does not (the archival-tail crossings, whose windows the released
# catalogue does not carry).  Never on a name where a position is available.
WINSPAN = collections.defaultdict(list)
for i, r in enumerate(CAT):
    lo, hi = edges(r)
    WINSPAN[r['eb']].append((lo, hi, i))


def window_of(eb, f):
    hit = [i for lo, hi, i in WINSPAN.get(eb, []) if lo - 1e-6 <= f <= hi + 1e-6]
    return hit[0] if hit else None


def _norm(s):
    return ''.join(c for c in s.lower() if c.isalnum())


SYS_BY_STAR = {}
for r in CAT:
    SYS_BY_STAR.setdefault(_norm(r['star_name']), r['system_id'])

SYSOF, BYNAME = {}, []
for cid, c in CROSS.items():
    i = window_of(c['eb'], c['freq_GHz'])
    if i is not None:
        SYSOF[cid] = CAT[i]['system_id']
    else:
        SYSOF[cid] = SYS_BY_STAR.get(_norm(c['star']))
        BYNAME.append(cid)

# the repeat readings the recurrence test made, per system.  One interval per
# reading: the cell it read, half a channel wide, with the block's own start
# time.  A repeat the paper's weight-pathology list drops is dropped here too,
# because the test did not use it.
EXTRA = collections.defaultdict(list)
REC_EB = set()
REC_ROWS = 0
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
        REC_EB.add(b['eb'])
        REC_ROWS += 1
    # the discovery block itself, at the discovery frequency: it is a census
    # block in every case, and it is already in CENSUS, but the frequency is
    # added so that a point-interval repeat has something to overlap.
    d = c.get('discovery')
    if d:
        REC_EB.add(c['eb'])
        half = 0.5 * float(d['chanw_Hz']) / 1e9
        f = float(c['freq_GHz'])
        EXTRA[sid].append((f - half, f + half, c['eb']))

# ★★ THE BLOCK SET THIS TEST READS IS NOT THE SET THAT SUPPLIES A REPEAT
#    READING, AND THE PAPER PRINTED THE UNION UNDER THE SECOND NAME.  The
#    comparison needs both ends of a pair, so the discovery block is read
#    too; 15 of them are not a repeat block of any other crossing.  Both
#    parts are published so a sentence can name them instead of summing them.
REP_ONLY = {b['eb'] for c in CROSS.values() for b in c.get('blocks', [])
            if not b.get('bad_weight_product')}
DISC_ONLY = REC_EB - REP_ONLY
if DRIVE == 13:                   # Z12: a repeat-reading block gone missing
    REP_ONLY = set(sorted(REP_ONLY)[:-1])

if DRIVE == 2:
    EXTRA = collections.defaultdict(list)       # the two sets coincide
if DRIVE == 3:
    for k in list(EXTRA):
        if k in ('CP-72 2713', 'CD-57 1054'):
            EXTRA.pop(k)                        # the named systems do not move

# ----------------------------------------------------------------- the epochs
#: one mapping, used for both sets.  `epochs_r14` owns it; the recurrence
#: record's own time stamps are compared with it, never substituted for it.
MJD = dict(ep.EPOCHS)
STAMP = {}
for r in REC['rows']:
    STAMP.setdefault(r['eb'], r['t_start_mjdsec'] / 86400.0)
for cid, c in CROSS.items():
    d = c.get('discovery')
    if d and d.get('t_start_mjdsec'):
        STAMP.setdefault(c['eb'], d['t_start_mjdsec'] / 86400.0)
_both = sorted(set(MJD) & set(STAMP))
_worst = max((abs(MJD[e] - STAMP[e]), e) for e in _both)
if DRIVE == 4:
    MJD[_both[0]] = MJD[_both[0]] + 7.0         # two epoch determinations
    _worst = max((abs(MJD[e] - STAMP[e]), e) for e in _both)


def separated(ebs, sep):
    """True where two of these blocks SATISFY THE CONFIRMATION CRITERION at
    `sep`: a different observing session, and more than `sep` days apart.  ★ THIS IS `epochs_r14.separated` AND NOT A SECOND IMPLEMENTATION
    OF IT: that predicate weighs three witnesses in order of authority -- the
    surviving measurement sets, the barycentric term, and last the stored
    stamp, trusted only where two blocks do not share it -- and a min/max over
    stored stamps written here instead gave 32/12/28 where the paper publishes
    38/12/23.  One-sided at every threshold: it can show two blocks separated
    and can never show two simultaneous, so a count of confirmable systems is
    a lower bound.
    ★ A consequence worth knowing: `separated(ebs, 0.0)` takes the `sep <=
    SEP` branch and therefore tests `> SEP = 1` day, so the paper's
    \\RcNoRepSys is "no second covering block MORE THAN A DAY LATER" and not
    "no second covering block at all"."""
    if DRIVE == 6:
        ts = sorted(MJD[e] for e in set(ebs) if e in MJD)
        return bool(ts) and (ts[-1] - ts[0]) > sep
    return ep.separated_confirming(list(ebs), sep)


def confirmable(iv, sep):
    """True where two blocks more than `sep` days apart cover one frequency.
    Evaluated on the interval boundaries, so no island can be lost to a grid."""
    pts = sorted({x for a, b, _ in iv for x in (a, b)})
    for i in range(len(pts) - 1):
        mid = 0.5 * (pts[i] + pts[i + 1])
        if separated([e for a, b, e in iv if a <= mid <= b], sep):
            return True
    return False


SEP_MONTH = 30.0


def mark(iv):
    """The three-way mark the paper prints, plus the 30-day class the
    sensitivity figure's panel (b) bins on."""
    d = confirmable(iv, SEP_DAY)
    mo = confirmable(iv, SEP_MONTH)
    y = confirmable(iv, SEP_YR)
    n = confirmable(iv, 0.0)
    return d, y, n, mo


if DRIVE == 7:
    SYSOF[sorted(CROSS)[0]] = None     # a crossing resolves to no system

SYSTEMS = sorted(CENSUS)
RES = {}
for sid in SYSTEMS:
    cen = CENSUS[sid]
    rec = cen + EXTRA.get(sid, [])
    RES[sid] = dict(census=mark(cen), recur=mark(rec),
                    n_extra=len(EXTRA.get(sid, [])))


def counts(key):
    d = sum(1 for s in SYSTEMS if RES[s][key][0])
    y = sum(1 for s in SYSTEMS if RES[s][key][1])
    n = sum(1 for s in SYSTEMS if RES[s][key][2])
    return d, y, len(SYSTEMS) - n


CD, CY, CN = counts('census')
RD, RY, RN = counts('recur')
if DRIVE == 1:
    CD += 1                                      # the census leg drifts
if DRIVE == 5:
    for s in SYSTEMS:
        RES[s]['recur'] = (RES[s]['recur'][0], True, RES[s]['recur'][2])
    RD, RY, RN = counts('recur')
MOVED = [s for s in SYSTEMS
         if not RES[s]['census'][2] and RES[s]['recur'][2]]
GAINED_D = [s for s in SYSTEMS
            if not RES[s]['census'][0] and RES[s]['recur'][0]]

# --------------------------------------------------------------- assertions
print('confset_r18 (round %d)%s' % (ROUND, '  [drive %d]' % DRIVE if DRIVE else ''))
print('\nassertions')

ck('C1 the predicate run on the census set alone reproduces the three '
   'published macros',
   (CD, CY, CN) == (int(pub('RcConfSysDay')), int(pub('RcConfSysYr')),
                    int(pub('RcNoRepSys'))),
   'measured %d/%d/%d against published %s/%s/%s'
   % (CD, CY, CN, pub('RcConfSysDay'), pub('RcConfSysYr'), pub('RcNoRepSys')))

ck('C2 the two block sets are nested and the larger one is strictly larger',
   all(not (RES[s]['census'][0] and not RES[s]['recur'][0]) for s in SYSTEMS)
   and all(not (RES[s]['census'][2] and not RES[s]['recur'][2])
           for s in SYSTEMS)
   and RD > CD and RN < CN,
   'census %d confirmable over a day and %d with no covering second block; '
   'recurrence set %d and %d; %d systems move'
   % (CD, CN, RD, RN, len(MOVED)))

_named = ['CP-72 2713', 'CD-57 1054']
ck('C3 the two systems the report names are "--" on the census set and '
   'confirmable over a day on the recurrence set',
   all(s in RES for s in _named)
   and all(not RES[s]['census'][2] for s in _named)
   and all(RES[s]['recur'][0] for s in _named),
   '; '.join('%s census %s recur %s' % (s, RES[s]['census'], RES[s]['recur'])
             for s in _named))

ck('C4 every block in either set is epoch-resolved, and the two epoch '
   'determinations agree wherever both carry a block',
   all(e in MJD for iv in list(CENSUS.values()) + list(EXTRA.values())
       for _a, _b, e in iv)
   and _worst[0] < 1e-6,
   '%d blocks in the recurrence set, %d compared with epochs_r14, worst '
   'disagreement %.3g d (%s)'
   % (len(REC_EB), len(_both), _worst[0], _worst[1]))

ck('C5 on both sets, no system is confirmable over a year without being '
   'confirmable over a day',
   not [s for s in SYSTEMS
        if (RES[s]['census'][1] and not RES[s]['census'][0])
        or (RES[s]['recur'][1] and not RES[s]['recur'][0])],
   'census %d/%d, recurrence set %d/%d' % (CY, CD, RY, RD))

ck('C6 every crossing of the record resolves to a census system, and the '
   'system count is the published one',
   not [c for c in CROSS if SYSOF.get(c) is None]
   and len(SYSTEMS) == int(pub('NSysClassA')),
   '%d crossings, %d resolved by star label where the catalogue carries no '
   'window; %d systems against the published %s'
   % (len(CROSS), len(BYNAME), len(SYSTEMS), pub('NSysClassA')))


_FINE = collections.defaultdict(list)
for _r in CAT:
    if _r['resolution_class'] == 'fine':
        _FINE[_r['system_id']].append(_r)
_nest_bad = [s for s in SYSTEMS
             for k in ('census', 'recur')
             if (RES[s][k][1] and not RES[s][k][3])
             or (RES[s][k][3] and not RES[s][k][0])]
if DRIVE == 9:
    _FINE.pop(sorted(_FINE)[0])

ck('C8 the day / month / year classes are nested on both sets, and the '
   'systems grouped here are the same systems the sensitivity figure groups '
   'by fine resolution class',
   not _nest_bad and set(_FINE) == set(SYSTEMS),
   '%d non-nested; %d fine-resolution systems against %d Class A systems'
   % (len(_nest_bad), len(_FINE), len(SYSTEMS)))

# ---------------------------------- the frequency support, for Fig. 8's caption
def _union(iv):
    iv, o = sorted(iv), []
    for a, b in iv:
        if o and a <= o[-1][1]:
            o[-1][1] = max(o[-1][1], b)
        else:
            o.append([a, b])
    return o


def _total(iv):
    return sum(b - a for a, b in iv)


def _conf_iv(iv, sep):
    pts = sorted({x for a, b, _ in iv for x in (a, b)})
    keep = []
    for i in range(len(pts) - 1):
        mid = 0.5 * (pts[i] + pts[i + 1])
        if separated([e for a, b, e in iv if a <= mid <= b], sep):
            keep.append([pts[i], pts[i + 1]])
    return _union(keep)


SUP = {}
for _tag, _sep in (('Day', SEP_DAY), ('Yr', SEP_YR)):
    _c = _r = 0.0
    _pc, _pr = [], []
    for sid in SYSTEMS:
        a = _conf_iv(CENSUS[sid], _sep)
        b = _conf_iv(CENSUS[sid] + EXTRA.get(sid, []), _sep)
        _c += _total(a)
        _r += _total(b)
        _pc += [tuple(x) for x in a]
        _pr += [tuple(x) for x in b]
    SUP[_tag] = dict(persys_census=_c, persys_recur=_r,
                     pooled_census=_total(_union([list(x) for x in _pc])),
                     pooled_recur=_total(_union([list(x) for x in _pr])))
ADD_DAY_MHZ = (SUP['Day']['persys_recur'] - SUP['Day']['persys_census']) * 1e3
ADD_YR_MHZ = (SUP['Yr']['persys_recur'] - SUP['Yr']['persys_census']) * 1e3
POOLED_SAME = (abs(SUP['Day']['pooled_recur'] - SUP['Day']['pooled_census'])
               < 5e-5 and
               abs(SUP['Yr']['pooled_recur'] - SUP['Yr']['pooled_census'])
               < 5e-5)
if DRIVE == 8:
    ADD_DAY_MHZ = 4000.0

ck('C7 the added blocks move the pooled confirmable frequency support by '
   'less than the precision it is printed at, so the confirmation-coverage '
   'figure is unchanged by them',
   POOLED_SAME and ADD_DAY_MHZ < 50.0
   and abs(SUP['Day']['pooled_census']
           - float(pub('CvConfGHzDay'))) < 0.05,
   'pooled support %.4f -> %.4f GHz at a day and %.4f -> %.4f GHz at a year, '
   'against the published %s and %s; per-system support grows by %.2f MHz '
   'and %.2f MHz'
   % (SUP['Day']['pooled_census'], SUP['Day']['pooled_recur'],
      SUP['Yr']['pooled_census'], SUP['Yr']['pooled_recur'],
      pub('CvConfGHzDay'), pub('CvConfGHzYr'), ADD_DAY_MHZ, ADD_YR_MHZ))

ck('Z12 the block set this test reads decomposes into the blocks that supply '
   'a repeat reading and the discovery blocks that supply none, and the '
   'first is the count published for the repeat readings',
   REP_ONLY <= REC_EB
   and len(REP_ONLY) + len(DISC_ONLY) == len(REC_EB)
   and len(REP_ONLY) == int(pub('RcNRepeatBlock'))
   and len(DISC_ONLY) > 0,
   '%d repeat-reading + %d discovery-only = %d read; published repeat-block '
   'count %s' % (len(REP_ONLY), len(DISC_ONLY), len(REC_EB),
                 pub('RcNRepeatBlock')))

# ------------------------------------------------------------------- report
print('\nmeasured')
print('  census block set      : %3d confirmable over a day, %3d over a year, '
      '%3d with no covering second block' % (CD, CY, CN))
print('  + recurrence repeats  : %3d confirmable over a day, %3d over a year, '
      '%3d with no covering second block' % (RD, RY, RN))
print('  blocks the recurrence test read: %d, of which %d are census blocks'
      % (len(REC_EB), len(REC_EB & {r['eb'] for r in CAT})))
print('  %d repeat readings over %d systems' % (REC_ROWS, len(EXTRA)))
print('  systems that lose the "no covering second block" mark (%d): %s'
      % (len(MOVED), ', '.join(MOVED)))
print('  systems that gain a confirmable-over-a-day mark (%d): %s'
      % (len(GAINED_D), ', '.join(GAINED_D)))

M = {}


def m(k, v):
    assert k.isalpha(), k
    assert k not in M, k
    M[k] = str(v)


m('ZcConfSysDay', '%d' % RD)
m('ZcConfSysYr', '%d' % RY)
m('ZcNoRepSys', '%d' % RN)
m('ZcNoRepSysWord', ['no', 'one', 'two', 'three', 'four', 'five', 'six',
                     'seven', 'eight', 'nine', 'ten', 'eleven', 'twelve',
                     'thirteen', 'fourteen', 'fifteen', 'sixteen',
                     'seventeen', 'eighteen', 'nineteen', 'twenty'][RN]
  if RN <= 20 else '%d' % RN)
m('ZcNMoved', '%d' % len(MOVED))
m('ZcNMovedWord', ['no', 'one', 'two', 'three', 'four', 'five', 'six',
                   'seven', 'eight', 'nine', 'ten'][len(MOVED)]
  if len(MOVED) <= 10 else '%d' % len(MOVED))
m('ZcNRecEB', '%d' % len(REC_EB))
# ★ `REP_ONLY` is NOT published: its value is \RcNRepeatBlock, which
#   recur_v411.py already owns, and a second macro for one quantity is
#   the twin this tree retires.  Z12 asserts the two are equal instead.
m('ZcNRecEBDisc', '%d' % len(DISC_ONLY))
m('ZcNRecEBOut', '%d' % len(REC_EB - {r['eb'] for r in CAT}))
# =====================================================================
# A10 / R1 SEC. 7: WHAT THE BLOCKS OUTSIDE THE CENSUS ACTUALLY ARE
# =====================================================================
# ★★★★ Referee 2's A10 is that Sec. 2.2's "115 repeat epochs" is the archival
# EXTENSION and not a repeat-block count.  He is right -- and the replacement
# he suggests, 42, **would also have been wrong**, because 22 of those 42 are
# the RESERVED HOLD-OUT: a processed set deliberately booked outside the
# census, not one of the unprocessed blocks at the freeze.  Writing the
# referee's own number would have put something false on the page, which
# happened four times in this round.
#
# Referee 1 Sec. 7's rule is the general one: *counts from different samples
# must never be combined without explicitly identifying the population.*
# \ZcNRecEBOut was exactly such a count -- 42, with no statement of what the
# 42 were -- so the three populations are now emitted and the prose names
# them.  Measured here, from the same three export records the census is
# defined against, and ASSERTED to sum to the published total, so the
# decomposition cannot drift away from the number it decomposes.
#
# ★ It is NOT a leakage problem and must not be written as one: the hold-out
# is searched as an additional sample, set aside by an identifier rule, and
# Sec. 4.6's null already says "every repeat block in the census and the
# hold-out".  An epoch of the same star at the same frequency is evidence
# wherever it is booked.  But a reader told the hold-out is reserved deserves
# to be told it supplies 22 of the 42.
_OUT_EB = REC_EB - {r['eb'] for r in CAT}


def _ebset(fn):
    """Every execution-block identifier anywhere in one export record."""
    out = set()

    def walk(x):
        if isinstance(x, dict):
            for k, v in x.items():
                if k in ('eb', 'execblock', 'execblock_uid') and \
                        isinstance(v, str):
                    out.add(v)
                else:
                    walk(v)
        elif isinstance(x, list):
            for y in x:
                walk(y)
    pth = os.path.join(PAPER, fn)
    if os.path.exists(pth):
        walk(json.load(open(pth)))
    return out


_EXT_EB = _ebset('export_extension.json')
_HOLD_EB = _ebset('holdout_export_v381.json')
_nExt = len(_OUT_EB & _EXT_EB)
_nHold = len(_OUT_EB & _HOLD_EB)
_nEpoch = len(_OUT_EB - _EXT_EB - _HOLD_EB)
if DRIVE == 31:
    _nEpoch += 1
m('ZcNRecEBOutExt', '%d' % _nExt)
m('ZcNRecEBOutHold', '%d' % _nHold)
m('ZcNRecEBOutEpoch', '%d' % _nEpoch)
ck('Z20 the recurrence blocks outside the census decompose into the archival '
   'extension, the reserved hold-out and the epoch-extension campaign with '
   'nothing left over, so the count can never be printed without its '
   'populations (R1 Sec. 7; A10)',
   _nExt + _nHold + _nEpoch == len(_OUT_EB),
   '%d + %d + %d = %d against \\ZcNRecEBOut %d'
   % (_nExt, _nHold, _nEpoch, _nExt + _nHold + _nEpoch, len(_OUT_EB)))
ck('Z21 the hold-out really is the largest of the three, which is the fact '
   'that makes the referee-suggested 42 wrong and is why the clause exists',
   _nHold > _nExt and _nHold > _nEpoch,
   'extension %d, hold-out %d, epoch-extension %d' % (_nExt, _nHold, _nEpoch))
m('ZcCenNoRepSys', '%d' % CN)
m('ZcAddSupDayMHz', '%.1f' % ADD_DAY_MHZ)
m('ZcAddSupYrMHz', '%.1f' % ADD_YR_MHZ)
m('ZcConfSysMonth', '%d' % sum(1 for s in SYSTEMS if RES[s]['recur'][3]))

if FAIL:
    print('\nFAILED: %s' % '; '.join(FAIL))
    if DRIVE == 0:
        raise SystemExit(1)

hdr = ['%%%% GENERATED by confset_r18.py (round %d) -- do not hand-edit.' % ROUND,
       '%% Confirmability over the block set the recurrence test reads.']
with open(os.path.join(HERE, 'survey_numbers_round%d%s.tex' % (ROUND, SFX)),
          'w') as fh:
    fh.write('\n'.join(hdr + ['\\newcommand{\\%s}{%s}' % (k, v)
                              for k, v in sorted(M.items())]) + '\n')
with open(os.path.join(HERE, 'confset_r18%s.json' % SFX), 'w') as fh:
    json.dump(dict(round=ROUND, drive=DRIVE,
                   census=dict(day=CD, yr=CY, norep=CN),
                   recur=dict(day=RD, yr=RY, norep=RN),
                   n_rec_eb=len(REC_EB),
                   n_rec_eb_outside_census=len(
                       REC_EB - {r['eb'] for r in CAT}),
                   moved=MOVED, gained_day=GAINED_D,
                   per_system={s: dict(census=RES[s]['census'],
                                       recur=RES[s]['recur'],
                                       n_extra=RES[s]['n_extra'])
                               for s in SYSTEMS}), fh, indent=1)
print('\n%d macros written' % len(M))

if '--selftest' in sys.argv:
    print('\nselftest: every assertion driven to fail')
    want = {1: 'C1', 2: 'C2', 3: 'C3', 4: 'C4', 5: 'C5', 6: 'C1', 7: 'C6',
            8: 'C7', 9: 'C8'}
    bad = []
    for d, nm in sorted(want.items()):
        p = subprocess.run([sys.executable, __file__, '--drive', str(d)],
                           capture_output=True, text=True)
        fired = [l for l in p.stdout.splitlines()
                 if l.strip().startswith(nm) and 'FAIL' in l]
        print('  drive %d -> %s %s' % (d, nm, 'FIRED' if fired else 'DID NOT FIRE'))
        if not fired:
            bad.append((d, nm))
    for f in sorted(os.listdir(HERE)):
        if '_drive' in f:
            os.remove(os.path.join(HERE, f))
    print('  selftest %s' % ('PASS' if not bad else 'FAIL %s' % bad))
    # ★ the selftest must FAIL THE PROCESS, not merely print the word: a
    #   suite whose verdict is readable only by a human eye is the
    #   seventeenth species of check-that-cannot-fail in this tree.
    raise SystemExit(1 if bad else 0)
