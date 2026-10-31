#!/usr/bin/env python3
r"""confirm_r19.py -- round 806.  ONE definition of a confirmed signal, and
the baselines over which the recurrence stage's positive controls were
actually recovered.

WHY THIS EXISTS.  Two statements of ours about confirmation were incompatible,
and a third was false.

 1. THE CRITERION APPLIED TO EVENTS WAS WEAKER THAN THE CRITERION USED TO
    COUNT WHAT IS CONFIRMABLE.  Sec. 4.2(iii) accepted a recovery in "any
    other execution block", explicitly including one hours later in the same
    scheduling session, while the confirmability census counts only blocks
    more than a day apart.  A same-session block shares the calibrators, the
    atmosphere, the correlator setup and the local interference environment,
    and the survey's own data-quality failure is a residual that persists
    from one integration to the next -- so the weaker rule admits exactly the
    failure mode the paper documents.  It is not hypothetical: for
    `QcNHazard` of the tested unattributed crossings the nearest covering
    block is in the same session and less than a day away, the two
    rank-leading events among them at 2.0 and 2.1 h.
    ONE definition is adopted here, in one place: a recovery confirms where
    the recovering block belongs to a different observing session AND is more
    than a day from the discovery block.  A recovery in any block of the
    discovery's own session is a WITHIN-SESSION REPEAT, whatever the
    interval: necessary, not sufficient.

 2. THE POSITIVE CONTROL'S BASELINES WERE REPORTED FROM THE WRONG BLOCK.  The
    recurrence record keeps, for each recovered crossing, the STRONGEST
    recovering block.  For four of the thirteen controls that block is a
    sibling of the discovery block's own observing unit, whose separation the
    archive does not record -- so the section reported those four as testing
    "the reading rather than the baseline".  Measured over EVERY block that
    satisfies the criterion rather than over the strongest one, all thirteen
    are recovered in a block that is both more than a day away and in a
    different session, the four CO(1-0) crossings across `QcBpCoOneSepD` d.
    The baseline exists; the record simply named a nearer block.

 3. A SEPARATION THE ARCHIVE DOES NOT RECORD WAS PRINTED AS 0.0.  Where a
    block's own epoch is not indexed it inherits the earliest stamp of its
    member observing unit, so two blocks of one unit come back with the same
    number and the interval between them is zero by construction.  Zero is a
    measurement; this is not one.  The table written here prints n/r, and the
    patch to `ledger_v410.py` filed with it does the same in Table D1.

WHAT IS NOT DONE HERE.  The confirmability counts are recomputed on the
adopted definition in `confirm_r20.py`, which also measures what the second
conjunct costs: 31 pairs of census blocks are rejected by it over 15 systems,
and no published count moves, because every one of those systems is
confirmable through a pair in two sessions as well.  The criterion is now the
conjunction -- a different observing session AND more than a day -- and the
disjunction this generator adopted is withdrawn: it admitted exactly the
same-session pairs its own rationale excludes.

THE ASSERTIONS, AND WHY EACH CAN FAIL.
  A1  the control list is the one the manuscript counts (`\MkAttrRecur`),
      every row carries a recovering block, and every recovering statistic
      reaches the trigger.  A control the paper counts and this table cannot
      name would be a count with no evidence under it.
  A2  every control is recovered in a block both more than a day away and in
      a different session -- the fact that corrects the section.  Driven with
      the strongest-block choice, which reproduces the published 9/4 split and
      fails.
  A3  no separation is printed as a zero, and no separation the archive does
      not record is printed as a number at all.
  A4  no unattributed crossing is recovered in any block, so the definition
      moves no disposition.  This is what makes the change safe to adopt; if
      it ever fails, a disposition has moved and must be reported.
  A5  the confirmability predicate, run on the census blocks on the ADOPTED
      conjunction, reproduces `\RcConfSysDay` and `\RcNoRepSys` exactly,
      and the day branch alone is reported beside it.  Without this the
      published count could sit on a rule the criterion no longer is.
  A6  the hazard set is non-empty, every member is same-session and inside a
      day, and the two rank-leading events are in it with the separations
      Table 6 prints -- read from the typeset fragment, not from the record
      the fragment was built from.
  A7  the block that carries the CO(1-0) baseline is in a different session,
      more than a day away, and holds the line itself at the statistic the
      corrected sentence quotes.

    python3 confirm_r19.py                 # measure and write
    python3 confirm_r19.py --drive N       # N = 1..9, one assertion each
    python3 confirm_r19.py --selftest      # drive every assertion to fail
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
V = HERE                      # in the tree the generator and the paper are one
ROUND = 806
DRIVE = int(sys.argv[sys.argv.index('--drive') + 1]) if '--drive' in sys.argv \
    else 0
SFX = '' if DRIVE == 0 else '_drive%d' % DRIVE
OUT = os.path.join(HERE, 'numbers/survey_numbers_round%d%s.tex' % (ROUND, SFX))
OUTJ = os.path.join(HERE, 'confirm_r19%s.json' % SFX)
OUTT = os.path.join(HERE, 'tab_confirm_r19%s.tex' % SFX)

sys.path.insert(0, V)
DAY = 1.0                     # the paper's own separation, days

M, FAIL = [], []


def m(k, v):
    assert k.isalpha(), 'a LaTeX macro name may contain letters only: ' + k
    assert k not in dict(M), 'macro defined twice: ' + k
    M.append((k, str(v)))


def ck(name, cond, detail=''):
    if not cond:
        FAIL.append(name)
    print('  %-66s %s  %s' % (name, 'PASS' if cond else 'FAIL', detail))


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


def tname(s):
    s = s.split(' Gaia')[0].strip()
    s = re.sub(r'^HD(\d)', r'HD \1', s)
    s = s.replace('bet Pic', r'$\beta$~Pic').replace('eta Crv', r'$\eta$~Crv')
    s = s.replace('CP-72', 'CP$-$72').replace('CD-57', 'CD$-$57')
    s = s.replace('BD05', 'BD+05')
    return s.replace(' ', '~')


def short(eb):
    """`A002_Xf4df6f_Xc7` -> `Xf4df6f_Xc7`: the session is the first field of
    what is printed, so no separate session column is needed."""
    return '_'.join(eb.split('_')[1:])


def session(eb):
    """The observing session an execution block belongs to.  ALMA's block
    identifier carries the session above the block, so several executions of
    one session share this field; `consist_v412.py` reads it the same way.
    None where the identifier does not have that shape, which is the "where
    sessions are known" of the criterion."""
    parts = eb.split('_')
    return parts[1] if len(parts) == 3 and parts[0] == 'A002' else None


def utdate(mjd):
    """MJD -> UT calendar date.  Civil-date arithmetic only; no epoch here is
    quoted finer than the day, because the stamp of a block the archive does
    not index is its observing unit's."""
    jd = int(mjd + 2400001.0)                 # integer JD at the day start
    a = jd + 32044
    b = (4 * a + 3) // 146097
    c = a - 146097 * b // 4
    d = (4 * c + 3) // 1461
    e = c - 1461 * d // 4
    mth = (5 * e + 2) // 153
    day = e - (153 * mth + 2) // 5 + 1
    month = mth + 3 - 12 * (mth // 10)
    year = 100 * b + d - 4800 + mth // 10
    return '%04d-%02d-%02d' % (year, month, day)


# ------------------------------------------------------------------ inputs
# The recovery record is the manuscript's own: `maskso_v414.attributed_
# recurrence` applies the criterion and this generator asks it for every
# block that satisfies it, rather than reapplying the criterion here.  A
# second implementation of the criterion is how two numbers for one quantity
# get into a paper.
import maskso_v414 as MS                                        # noqa: E402
EP = __import__('epochs_r14')

LED = json.load(open(os.path.join(V, 'ledger.json')))['rows']
RCOL = json.load(open(os.path.join(V, 'recurcols_v411.json')))
CROSS = json.load(open(os.path.join(V, 'r10inputs',
                                   'recur_v411.json')))['crossings']
ALLREC = {}
EXTRA = MS.attributed_recurrence(LED, RCOL, here=V, collect=ALLREC)
TRIG = float(macro('StageNullTrig'))


def record(r):
    k = MS.key_of(r)
    q = RCOL.get(k) if (RCOL.get(k) or {}).get('T_pers') is not None \
        else EXTRA.get(k)
    return k, (q or {})


def reliable(eb):
    """True where the block's own epoch is known: a surviving measurement set,
    or a stamp the archive indexes on the block's own identifier.  A stamp
    resolved through the member observing unit is the earliest block of that
    unit and is not this block's epoch."""
    return eb in EP.MS or EP.SRC.get(eb) == 'block'


# ================================== 1. THE POSITIVE CONTROLS AND THEIR BASELINES
ROWS = []
for r in LED:
    k, q = record(r)
    if q.get('verdict') != 'recovered':
        continue
    eb0 = r['eb']
    cands = []
    for eb1, trec in ALLREC.get(k, []):
        if DRIVE == 8 and session(eb0) != session(eb1) \
                and 'f5d76d' in (eb0 + eb1):
            continue        # A7: the CO(1-0) baseline removed
        if DRIVE == 2:
            # the published choice: the STRONGEST recovering block, whatever
            # its session and whatever its separation
            if (eb1, trec) != ALLREC[k][0]:
                continue
        t0, t1 = EP.EPOCHS.get(eb0), EP.EPOCHS.get(eb1)
        sep = (t1 - t0) if (t0 is not None and t1 is not None) else None
        unrec = (sep is not None and abs(sep) < 1e-9
                 and not (reliable(eb0) and reliable(eb1)))
        if sep is None:
            unrec = True
        apart = bool(EP.apart(eb0, eb1)) or bool(
            reliable(eb0) and reliable(eb1) and sep is not None
            and abs(sep) > DAY)
        diff = (session(eb0) is not None and session(eb1) is not None
                and session(eb0) != session(eb1))
        cands.append(dict(eb=eb1, t=trec, sep=sep, unrec=unrec,
                          apart=apart, diff_sess=diff,
                          both=bool(apart and diff),
                          approx=not (reliable(eb0) and reliable(eb1))))
    indep = [c for c in cands if c['both']]
    # the criterion names the strongest recovering block; restricted to the
    # blocks the adopted definition admits, that is the strongest independent
    # one.  `cands` is already strongest-first.
    best = indep[0] if indep else None
    ROWS.append(dict(
        star=r['display'], line=(r.get('line') or '--'), eb=eb0,
        freq=float(r['freq']), fstar=float(r['frame']['f_stellar']),
        tstar=float(r['tstar']), n_cand=len(cands),
        n_indep=len(indep), n_unrec=sum(1 for c in cands if c['unrec']),
        n_apart=sum(1 for c in cands if c['apart']),
        n_diff=sum(1 for c in cands if c['diff_sess']),
        named=q.get('recovered_eb'), named_t=q.get('T_recov'),
        best=best))
ROWS.sort(key=lambda z: (z['star'], z['fstar']))
if DRIVE == 1:
    ROWS = ROWS[:-1]

NCTL = int(macro('MkAttrRecur'))
ck('A1 every crossing the manuscript counts as a positive control is listed '
   'with a recovering block that reaches the trigger',
   len(ROWS) == NCTL
   and all(z['named'] and z['named_t'] is not None
           and z['named_t'] >= TRIG for z in ROWS),
   '%d listed against %s counted; weakest recovering statistic %.2f'
   % (len(ROWS), macro('MkAttrRecur'),
      min(z['named_t'] for z in ROWS if z['named_t'] is not None)))

INDEP = [z for z in ROWS if z['best']]
ck('A2 every positive control is recovered in a block both more than a day '
   'from its own and in a different observing session',
   len(INDEP) == len(ROWS) and len(ROWS) > 0,
   '%d of %d; separations %.0f to %.0f d; %d of them also hold a '
   'within-session repeat whose separation the archive does not record'
   % (len(INDEP), len(ROWS),
      min(abs(z['best']['sep']) for z in INDEP) if INDEP else -1,
      max(abs(z['best']['sep']) for z in INDEP) if INDEP else -1,
      sum(1 for z in ROWS if z['n_unrec'])))

# ---------------------------------------------- the printed separations
def sepstr(z):
    c = z['best']
    if c is None or c['unrec'] or c['sep'] is None:
        return 'n/r'
    s = abs(c['sep'])
    out = ('%.2f' % s) if s < 10 else '%.0f' % s
    if DRIVE == 3:
        out = '0.0'
    return out + ('$^\\ddagger$' if c['approx'] else '')


PRINTED = [sepstr(z) for z in ROWS]
ck('A3 no separation is printed as a zero, and a separation the archive does '
   'not record is not printed as a number',
   all(not re.match(r'^0(\.0+)?(\$|$)', p) for p in PRINTED)
   and all((p == 'n/r') == (z['best'] is None or z['best']['unrec'])
           for p, z in zip(PRINTED, ROWS)),
   'printed: %s' % ', '.join(sorted(set(PRINTED))))

# ================================ 2. DOES THE DEFINITION MOVE A DISPOSITION?
UNATTR_REC, HAZARD = [], []
for r in LED:
    k, q = record(r)
    att = (r.get('line_coincident')
           and q.get('verdict') == 'recovered') or False
    if q.get('verdict') == 'recovered' and not r.get('line_coincident'):
        UNATTR_REC.append(k)
if DRIVE == 4:
    UNATTR_REC = [MS.key_of(LED[0])]
# every crossing the recurrence campaign tested, and the session and
# separation of its NEAREST covering block.  This is the set the old rule
# exposed: a recovery in that block would have been published as a
# confirmation on data sharing one session with the discovery.
for cid, c in CROSS.items():
    seps = [(b['sep_from_discovery_h'], b['eb']) for b in (c.get('blocks') or [])
            if b.get('sep_from_discovery_h') is not None]
    if not seps:
        continue
    h, eb1 = min(seps, key=lambda z: abs(z[0]))
    if abs(h) <= 24.0 * DAY and session(c['eb']) == session(eb1):
        HAZARD.append(dict(cid=cid, star=c['star'], eb=c['eb'], near=eb1,
                           sep_h=h, freq=c['freq_GHz']))
HAZARD.sort(key=lambda z: abs(z['sep_h']))
if DRIVE == 5:
    HAZARD = [dict(h, sep_h=99.0) for h in HAZARD]

ck('A4 no unattributed crossing is recovered in any block, so the adopted '
   'definition moves no disposition and no count of crossings',
   not UNATTR_REC,
   '%d unattributed crossings recovered anywhere; %d dispositions move'
   % (len(UNATTR_REC), len(UNATTR_REC)))

# the two rank-leading events, read from the typeset fragment rather than
# from the record it was built from
TAB6 = open(os.path.join(V, 'tab_recurcand_v411.tex')).read()
_mm = re.search(r'Nearest covering epoch, separation \(h\) &\s*'
                r'\$([-+\\]*[\d.]+)\$ &\s*\$?([-+\\]*[\d.]+)\$?', TAB6)
T6 = tuple(abs(float(x.replace('$', '').replace('\\', '')))
           for x in _mm.groups()) if _mm else (None, None)
_byeb = {h['eb']: h for h in HAZARD}
EV = [('61 Vir', 'A002_Xc079b5_X82f'), ('CP-72 2713', 'A002_Xff0235_X4a6d')]
_evsep = tuple(abs(_byeb[e]['sep_h']) if e in _byeb else None
               for _, e in EV)
if DRIVE == 6:
    T6 = (T6[0] + 1.0, T6[1])
ck('A5 the hazard the old rule left open is measured, every member of it is '
   'same-session and inside a day, and the two rank-leading events are in it '
   'with the separations the event table prints',
   bool(HAZARD)
   and all(abs(h['sep_h']) <= 24.0 and session(h['eb']) == session(h['near'])
           for h in HAZARD)
   and all(a is not None and b is not None and abs(a - b) < 0.011
           for a, b in zip(_evsep, T6)),
   '%d of %s tested crossings; nearest %.2f h; events %s against %s printed'
   % (len(HAZARD), macro('RcNTested'), min(abs(h['sep_h']) for h in HAZARD),
      _evsep, T6))

# ============================ 3. THE CONFIRMABILITY BRANCHES, CENSUS BLOCKS
CAT = [r for r in csv.DictReader(open(os.path.join(
    V, 'per_target_results_v3.99.csv'), encoding='utf-8'))
    if r['search_class'] == 'A']
BYSYS = collections.defaultdict(list)
for r in CAT:
    BYSYS[r['system_id']].append(r)


def overlap(a, b):
    la, ha = sorted((float(a['flo_GHz']), float(a['fhi_GHz'])))
    lb, hb = sorted((float(b['flo_GHz']), float(b['fhi_GHz'])))
    return min(ha, hb) - max(la, lb) > 0


def confirmable(rows, rule):
    """True where two blocks of this system cover a common frequency and
    satisfy `rule`.  Equivalent to the interval construction of
    `cover_v412.py` for a system count: a frequency covered by two blocks is
    covered at the midpoint of their overlap."""
    for a, b in itertools.combinations(rows, 2):
        if a['eb'] != b['eb'] and overlap(a, b) \
                and rule(a['eb'], b['eb']):
            return True
    return False


def rule_day(a, b):
    return EP.apart(a, b)


def rule_adopted(a, b):
    """THE ADOPTED CRITERION, as `epochs_r14.confirms` implements it: a
    different observing session AND more than a day.  It was a disjunction,
    which admitted the same-session pairs its own rationale excludes."""
    return EP.confirms(a, b)


CD = sum(1 for rows in BYSYS.values() if confirmable(rows, rule_day))
CO = sum(1 for rows in BYSYS.values() if confirmable(rows, rule_adopted))
if DRIVE == 7:
    CO = CO + 1
MOVED_SYS = [sid for sid, rows in BYSYS.items()
             if confirmable(rows, rule_day)
             and not confirmable(rows, rule_adopted)]
# ★★★ RESTATED v4.21.  This clause used to assert the published count against
# the DAY BRANCH and report what the session branch "adds" -- which was the
# right test of the old disjunction and is the wrong test of the adopted
# conjunction: it would pass unchanged while the manuscript printed a count
# computed on a rule the criterion no longer is.  The invariant is which rule
# the published number is on, not what the answer happens to be: the
# conjunction, counted on the census blocks, must BE \RcConfSysDay and
# \RcNoRepSys, and the day branch is reported beside it so that the cost of
# the second conjunct is visible rather than assumed to be nil.  It can fail
# in either direction -- a system that the tightening moves, or a published
# macro left on the looser rule.
ck('A6 THE PUBLISHED CENSUS CONFIRMABILITY IS THE COUNT ON THE ADOPTED '
   'CRITERION: the conjunction -- a different observing session and more '
   'than a day -- counted over the census blocks reproduces '
   '\\RcConfSysDay and \\RcNoRepSys, and the day branch alone is '
   'reported beside it',
   '%d' % CO == macro('RcConfSysDay')
   and '%d' % (len(BYSYS) - CO) == macro('RcNoRepSys')
   and CO <= CD,
   '%d confirmable on the adopted conjunction against %s published, %d not '
   'against %s; the day branch alone gives %d, so the session conjunct '
   'moves %d system(s): %s (the pair-level count is confirm_r20.py\'s '
   '\\QfNPairDrop)'
   % (CO, macro('RcConfSysDay'), len(BYSYS) - CO, macro('RcNoRepSys'),
      CD, len(MOVED_SYS), MOVED_SYS or 'none'))

# ======================= 4. THE CO(1-0) BASELINE THE SECTION DENIES EXISTS
BPCO = [z for z in ROWS if 'Pic' in z['star'] and '1' in z['line']
        and z['line'].startswith('CO(1')]
BPB = collections.Counter(z['best']['eb'] for z in BPCO if z['best'])
BPEB, _n = BPB.most_common(1)[0] if BPB else (None, 0)
BPT = max((z['best']['t'] for z in BPCO if z['best'] and z['best']['eb'] == BPEB),
          default=None)
BPSEP = max((abs(z['best']['sep']) for z in BPCO
             if z['best'] and z['best']['eb'] == BPEB), default=None)
BPUNREC = sum(z['n_unrec'] for z in BPCO)
_bpok = (BPEB is not None and BPSEP is not None and BPSEP > DAY
         and BPUNREC > 0
         and all(z['best'] and z['best']['diff_sess'] for z in BPCO))
ck('A7 the CO(1-0) crossings reported as having no baseline are recovered in '
   'a block of another session more than a day away, which holds the line '
   'itself, and they also hold the within-session repeats that were quoted '
   'instead',
   _bpok,
   '%d crossings recovered in %s at T* %.2f, %.2f d away; %d within-session '
   'repeats with no recorded separation'
   % (len(BPCO), short(BPEB or '--'), BPT or -1, BPSEP or -1, BPUNREC))

# ★ WHERE A SEPARATION IS MEASURED FROM AN OBSERVING UNIT'S STAMP RATHER THAN
# A BLOCK'S OWN, THE UNIT'S OWN SPAN IS THE ERROR ON IT.  That span is not in
# the archive either, but it is bounded by the one witness every block carries:
# the barycentric velocity term moves by about 60 km/s over a year and by a
# fraction of a km/s within a day, and `epochs_r14` calibrates the largest
# spread seen among blocks genuinely taken within one day.  A unit whose blocks
# lie inside that spread spans less than a day, so a separation of tens of days
# measured from its stamp is good to the day it is quoted to.
UNITS = {}
for z in ROWS:
    for eb in (z['eb'], z['best']['eb'] if z['best'] else None):
        if eb and not reliable(eb):
            UNITS.setdefault(session(eb), set())
for u in list(UNITS):
    UNITS[u] = {e for e in set(EP.MJD) | set(EP.MS) if session(e) == u}
VBSPREAD = {u: (max(EP.VB[e] for e in ebs if e in EP.VB)
                - min(EP.VB[e] for e in ebs if e in EP.VB))
            for u, ebs in UNITS.items() if any(e in EP.VB for e in ebs)}
WMAX = EP.WITHIN_MAX
if DRIVE == 9:
    WMAX = 0.01
ck('A8 every observing unit a quoted separation is measured from spans less '
   'than a day on the barycentric witness, so the separations the table '
   'daggers are good to the day they are printed to',
   bool(VBSPREAD) and all(v <= WMAX for v in VBSPREAD.values()),
   '%d unit(s); largest spread %.3f km/s against %.3f seen within one day'
   % (len(VBSPREAD), max(VBSPREAD.values()), WMAX))

# the within-session pair of one session, which is why "between sessions"
# does not mean "between days": one session here spans more than a day.
SAMESESS = []
for r in LED:
    k, q = record(r)
    if q.get('verdict') != 'recovered':
        continue
    for eb1, _t in ALLREC.get(k, []):
        if session(eb1) == session(r['eb']):
            t0, t1 = EP.EPOCHS.get(r['eb']), EP.EPOCHS.get(eb1)
            if t0 is not None and t1 is not None and abs(t1 - t0) > DAY:
                SAMESESS.append((r['eb'], eb1, abs(t1 - t0)))
SS_MAX = max((s for _, _, s in SAMESESS), default=None)

# ======================================================= macros
m('QcNCtl', '%d' % len(ROWS))
m('QcNStar', '%d' % len({z['star'] for z in ROWS}))
m('QcNIndep', '%d' % len(INDEP))
m('QcNIndepWord', ['no', 'one', 'two', 'three', 'four', 'five', 'six',
                   'seven', 'eight', 'nine', 'ten', 'eleven', 'twelve',
                   'thirteen'][len(INDEP)] if len(INDEP) <= 13
  else '%d' % len(INDEP))
_nunrec = sum(1 for z in ROWS if z['n_unrec'])
m('QcNUnrec', '%d' % _nunrec)
# ★ the same count as a word, because both places that cite it begin a
# sentence with it and a sentence does not begin with a numeral.
m('QcNUnrecWord', ['No', 'One', 'Two', 'Three', 'Four', 'Five', 'Six',
                   'Seven', 'Eight', 'Nine', 'Ten', 'Eleven', 'Twelve',
                   'Thirteen'][_nunrec] if _nunrec <= 13 else '%d' % _nunrec)
m('QcSepMinD', '%.0f' % min(abs(z['best']['sep']) for z in INDEP))
m('QcSepMaxD', '%.0f' % max(abs(z['best']['sep']) for z in INDEP))
m('QcNHazard', '%d' % len(HAZARD))
m('QcHazardMinH', '%.2f' % min(abs(h['sep_h']) for h in HAZARD))
m('QcEvSepOneH', '%.2f' % _evsep[0])
m('QcEvSepTwoH', '%.2f' % _evsep[1])
m('QcConfSysCen', '%d' % CD)
# ★ `QcConfAddCen`/`QcConfAddCenWord` RETIRED v4.21: on the adopted
# conjunction the "systems the session branch adds" is zero by construction,
# and a macro that can only be zero is not a measurement.  What the second
# conjunct costs is measured in `confirm_r20.py` (\QfNPairDrop pairs over
# \QfNSysPairDrop systems, \QfNSysMoved systems moved) and the sentence
# that quoted these two reads those instead.
m('QcNDispMoved', '%d' % len(UNATTR_REC))
m('QcBpCoOneSepD', '%.0f' % BPSEP)
m('QcBpCoOneT', '%.1f' % BPT)
m('QcBpCoOneBlock', '\\texttt{%s}' % short(BPEB).replace('_', '\\_'))
m('QcBpCoOneN', '%d' % len(BPCO))
m('QcUnitVbSpread', '%.2f' % max(VBSPREAD.values()))
m('QcVbWithinMax', '%.2f' % EP.WITHIN_MAX)
m('QcSameSessMaxD', '%.2f' % SS_MAX)

# =============================================================== the table
# ★ R2-3: the positive control named each repeat block's own window-maximum
# crossing, which is not the quantity the exclusions are built from.  The two
# columns added here are: the SINGLE-CELL reading of that same block at the
# cell the discovery predicts, through the same frame correction, anchor and
# carried drift; and that cell's distance in channels from where the block's
# own search puts the line.  Both come from `linerecur_r20.py` (round 910),
# which runs the frozen reading code on these crossings, and are read here
# rather than recomputed, because a second implementation of a reading is how
# two numbers for one quantity get into a paper.
_LRJ = json.load(open(os.path.join(V, 'linerecur_r20.json')))
LR = _LRJ['table_d2']
LRB = _LRJ['per_block']
# the one window whose surviving product disagrees with the published
# statistic, named by the read-out that read it and not by a literal here
_supp = sorted({x['eb'] for v in LRB.values() for x in v if x.get('supplied')})
# ★ r28 (RR-lines): at most once -- in the re-flag fold the window's product
# reproduces the catalogue and nothing is supplied, so no row is exempt below.
assert len(_supp) <= 1, 'the supplied window is declared more than once: %r' \
    % _supp
SUPPLIED_EB = _supp[0] if _supp else None
if DRIVE == 11:              # A10: a control whose predicted-cell reading is
    LR = {}                  #      silently absent from the table
_lrmiss = [MS.key_of(dict(eb=z['eb'], freq=z['freq'])) for z in ROWS
           if MS.key_of(dict(eb=z['eb'], freq=z['freq'])) not in LR]
ck('A10 every positive control carries the single-cell reading at its own '
   'predicted cell, measured by the frozen reading code, and every one of '
   'them reaches the trigger somewhere in its covering blocks',
   not _lrmiss
   and all(LR[MS.key_of(dict(eb=z['eb'], freq=z['freq']))]['n_block_trig']
           >= 1 for z in ROWS),
   '%d rows, %d without a reading %s' % (len(ROWS), len(_lrmiss),
                                         _lrmiss[:2] or ''))

# ★★★★ ONE ROW, ONE BLOCK.  The table prints, on one line, a block identifier,
# that block's own crossing statistic $T$, and a single-cell reading
# $T_{\rm rep}$ at the cell the discovery predicts.  Those three must all be
# the SAME block, and until this was measured two of them were not: the
# recovering block and $T$ came from the strongest block the ADOPTED
# CRITERION admits, while $T_{\rm rep}$ and $\Delta c$ were read out of
# `linerecur_r20.json`'s `table_d2`, which keeps the reading in the strongest
# recovering block of any kind -- for the four CO(1-0) rows a block of the
# discovery's own observing session, which the criterion excludes.  Six of
# the thirteen rows mixed two blocks and four of them then printed a single
# cell LARGER THAN ITS OWN WINDOW MAXIMUM (30.76, 30.76, 27.68 and 28.42
# against a window maximum of 17.91), which is arithmetically impossible and
# is what a referee found in the typeset table.  Neither column was wrong on
# its own; the row was.  The reading is therefore taken from the per-block
# read-out, in the block this row names, and the three clauses below are what
# make that structural rather than incidental.
READ = []
for z in ROWS:
    c = z['best']
    k = MS.key_of(dict(eb=z['eb'], freq=z['freq']))
    q = LR.get(k, {})
    rd = None
    if c is not None and q.get('cid'):
        _hit = [x for x in LRB.get(q['cid'], []) if x['eb'] == c['eb']]
        rd = dict(_hit[0]) if _hit else None
        if DRIVE == 12:
            # A11: the reading the table used to print -- the strongest
            # recovering block's, whatever session it belongs to
            rd = dict(eb=q['recovering_eb'], T=q['T_rep'], dch=q['dchan'],
                      supplied=bool(q['recovering_eb'] == SUPPLIED_EB))
        if DRIVE == 14 and rd is not None and not rd.get('supplied') \
                and not any(x is not None and x.get('_driven') for x in READ):
            # A12: one cell reading larger than its own window maximum, in a
            # row that does not declare a second product
            rd = dict(rd, T=z['best']['t'] + 1.0, _driven=True)
    READ.append(rd)

_rdwrong = [(short(z['eb']), short(r['eb']) if r else None,
             short(z['best']['eb']) if z['best'] else None)
            for z, r in zip(ROWS, READ)
            if r is None or z['best'] is None or r['eb'] != z['best']['eb']]
ck('A11 the single-cell reading and the registration printed on each row are '
   'read in the block that row names -- the one the criterion admits and the '
   'one $T$ is taken from -- and not in some other recovering block',
   not _rdwrong,
   '%d of %d rows read in a block they do not name %s'
   % (len(_rdwrong), len(ROWS), _rdwrong[:2] or ''))

# ★★★★ THE INVARIANT, AND IT IS AN INVARIANT AND NOT THIS ROUND'S ANSWER: a
# reading of ONE CELL cannot exceed the maximum over every channel and drift
# of the window it sits in.  It is asserted on the two numbers AS PRINTED,
# because that is the comparison a reader makes, and rounding cannot be
# argued with it.  The one admitted exception is provenance and not
# arithmetic: for the single window whose surviving product disagrees with
# the published statistic, $T$ comes from the ledger and $T_{\rm rep}$ from
# that product, so the two are measurements of different products and their
# order carries no information.  The exception set is the set of rows whose
# reading is taken in that window -- declared by the read-out, never inferred
# from the comparison itself, which would make this clause unfalsifiable.
_pr = [dict(eb=short(z['eb']), tmax=float('%.2f' % z['best']['t']),
            tcell=float('%.2f' % r['T']), supplied=bool(r.get('supplied')))
       for z, r in zip(ROWS, READ) if z['best'] is not None and r is not None]
_over = [x for x in _pr if x['tcell'] > x['tmax']]
_overbad = [x for x in _over if not x['supplied']]
ck('A12 no row prints a single-cell reading larger than the maximum over the '
   'whole window it was read in, except where that reading comes from the '
   'one product that disagrees with the published statistic, which the row '
   'declares',
   not _overbad and len(_pr) == len(ROWS),
   '%d of %d rows print T_rep > T, %d of them from the declared product; '
   'largest excess %.3f over %s'
   % (len(_over), len(_pr), len(_over) - len(_overbad),
      max([x['tcell'] - x['tmax'] for x in _pr], default=0.0),
      [(x['eb'], x['tmax'], x['tcell']) for x in _over] or 'none'))

# ★★ THE COMBINED READING IS A DIFFERENT QUANTITY FROM THE SINGLE-BLOCK ONE
# AND NOW HAS ITS OWN COLUMN.  Sec. 5.6 quotes the combined value and the
# conclusions quote the single-block count; with only one column printed, a
# reader checking either against the table found the other.  The clause pins
# the provenance -- the column is the read-out's own combination over every
# covering block, not a re-combination here -- and that both are present on
# every row.
_combmiss = [short(z['eb']) for z, r in zip(ROWS, READ)
             if LR.get(MS.key_of(dict(eb=z['eb'], freq=z['freq'])), {})
             .get('T_rep_combined') is None]
if DRIVE == 13:
    _combmiss.append('driven')
ck('A13 every row carries both readings -- the single block it names and the '
   'crossing\'s covering blocks combined, which is the quantity the section '
   'quotes -- taken from the frozen read-out and not recombined here',
   not _combmiss,
   '%d of %d rows without a combined reading %s'
   % (len(_combmiss), len(ROWS), _combmiss[:2] or ''))

with open(OUTT, 'w') as fh:
    fh.write('%% GENERATED by confirm_r19.py -- do not hand-edit.\n')
    fh.write('%% The recurrence stage\'s positive controls and the baseline '
             'each was recovered over.\n')
    fh.write('\\begin{tabular}{@{}llrllrrrrrr@{}}\n\\hline\n')
    fh.write('Star & transition & $\\nu_\\star$ (GHz) & discovery block & '
             'recovering block & epoch & $\\Delta t$ (d) & $T$ & '
             # ★★ v4.23: `$T_{\\rm rep}^{\\rm comb}$` WAS A TYPE-FLOOR
             # FAILURE AND NOT A STYLE CHOICE.  A subscript carrying a
             # superscript isolates the subscript as its own line of type
             # at 5.98 pt in this column's \small, against
             # `tabfloor_r17.py`'s 6.50 pt floor -- running type a reader
             # has to read, which no LaTeX warning mentions.  A plain
             # subscript sets at the same size as `$T_{\\rm rep}$`, which
             # this table has carried for two versions, so the combined
             # reading takes a subscript of its own.
             '$T_{\\rm rep}$ & $T_{\\rm comb}$ & '
             '$\\Delta c$ \\\\\n')
    fh.write('\\hline\n')
    for z, p, r in zip(ROWS, PRINTED, READ):
        c = z['best']
        ep = EP.EPOCHS.get(c['eb']) if c else None
        q = LR.get(MS.key_of(dict(eb=z['eb'], freq=z['freq'])), {})
        mark = '$^\\dagger$' if ((r and r.get('supplied'))
                                 or q.get('supplied_disc')) else ''
        trep = ('%.2f%s' % (r['T'], mark)) if r else 'n/r'
        comb = ('%.2f' % q['T_rep_combined']) \
            if q.get('T_rep_combined') is not None else 'n/r'
        # ★ `minuscheck`: a signed number in a table is set in maths mode,
        # or the hyphen typesets as a hyphen and not as a minus.
        dch = 'n/r'
        if r and r.get('dch') is not None:
            dch = ('$0.00$' if abs(r['dch']) < 0.005
                   else '$%+.2f$' % r['dch'])
        fh.write('%s & %s & %.4f & \\texttt{%s} & \\texttt{%s} & %s & %s & '
                 '%.2f & %s & %s & %s \\\\\n'
                 % (tname(z['star']),
                    z['line'].replace('-', '--'),
                    z['fstar'],
                    short(z['eb']).replace('_', '\\_'),
                    short(c['eb']).replace('_', '\\_') if c else '--',
                    utdate(ep) if ep is not None else 'n/r',
                    p, c['t'] if c else float('nan'), trep, comb, dch))
    fh.write('\\hline\n\\end{tabular}\n')

json.dump(dict(round=ROUND, drive=DRIVE,
               definition=('a confirmed signal requires recovery at the '
                           'predicted stellar-frame cell in a block of a '
                           'different observing session AND more than %g d '
                           'from the discovery block; a recovery in any '
                           'block of the discovery\'s own session is a '
                           'within-session repeat, whatever the interval'
                           % DAY),
               controls=ROWS, printed=PRINTED, hazard=HAZARD,
               # ★ the rows AS PRINTED: the block each row names, the window
               # maximum there, the single-cell reading taken in that same
               # block, and the combined reading.  `tolrecur_r21.py` counts
               # the published single-block and combined counts off this,
               # so the count in the text and the column in the table are
               # one quantity and cannot drift apart.
               table=[dict(
                   star=z['star'], line=z['line'], eb=z['eb'],
                   freq=z['freq'], fstar=z['fstar'],
                   recovering_eb=(z['best']['eb'] if z['best'] else None),
                   t_window_max=(z['best']['t'] if z['best'] else None),
                   t_rep=(r['T'] if r else None),
                   dchan=(r['dch'] if r else None),
                   dkms=(r.get('dkms') if r else None),
                   chanw_Hz=(r.get('chanw') if r else None),
                   supplied_reading=bool(r.get('supplied')) if r else None,
                   t_rep_combined=LR.get(
                       MS.key_of(dict(eb=z['eb'], freq=z['freq'])),
                       {}).get('T_rep_combined'))
                   for z, r in zip(ROWS, READ)],
               conf_census_day=CD, conf_census_adopted=CO,
               unattributed_recovered=UNATTR_REC,
               same_session_over_a_day=SAMESESS),
          open(OUTJ, 'w'), indent=1, default=str)

with open(OUT, 'w') as fh:
    fh.write('%% GENERATED by confirm_r19.py (round %d) -- do not hand-edit.\n'
             % ROUND)
    fh.write('%% One definition of a confirmed signal, and the positive '
             'controls\' baselines.\n')
    for k, v in M:
        fh.write('\\newcommand{\\%s}{%s}\n' % (k, v))

print('\n%d macros -> %s' % (len(M), os.path.basename(OUT)))
for z, p in zip(ROWS, PRINTED):
    c = z['best']
    print('  %-12s %-8s %10.4f  T*%6.2f  rec %-16s %-9s dt %8s  T %5.2f  '
          '(%d cand, %d indep, %d unrecorded)'
          % (z['star'][:12], z['line'], z['fstar'], z['tstar'],
             short(c['eb']) if c else '--',
             session(c['eb']) if c else '--', p, c['t'] if c else -1,
             z['n_cand'], z['n_indep'], z['n_unrec']))
print('  hazard: %d crossings whose nearest covering block is same-session '
      'and inside a day' % len(HAZARD))
for h in HAZARD[:4]:
    print('      %-10s %-20s %+6.2f h  %s' % (h['star'][:10], short(h['eb']),
                                              h['sep_h'], short(h['near'])))
if FAIL:
    print('FAILED: %s' % ', '.join(FAIL))
    if DRIVE == 0:
        raise SystemExit(1)

if '--selftest' in sys.argv:
    print('\nselftest: every assertion driven to fail')
    want = {1: 'A1', 2: 'A2', 3: 'A3', 4: 'A4', 5: 'A5', 6: 'A5',
            7: 'A6', 8: 'A7', 9: 'A8', 11: 'A10', 12: 'A11', 14: 'A12',
            13: 'A13'}
    bad = []
    for d, nm in sorted(want.items()):
        p = subprocess.run([sys.executable, __file__, '--drive', str(d)],
                           capture_output=True, text=True)
        fired = [l for l in p.stdout.splitlines()
                 if l.strip().startswith(nm) and 'FAIL' in l]
        print('  drive %d -> %s %s' % (d, nm,
                                       'FIRED' if fired else 'DID NOT FIRE'))
        if not fired:
            bad.append((d, nm))
    for f in sorted(([_e for _e in os.listdir(HERE) if _e != 'numbers'] + [os.path.join('numbers', _e) for _e in (os.listdir(os.path.join(HERE, 'numbers')) if os.path.isdir(os.path.join(HERE, 'numbers')) else [])]), key=os.path.basename):
        if '_drive' in f:
            os.remove(os.path.join(HERE, f))
    print('  selftest %s' % ('PASS' if not bad else 'FAIL %s' % bad))
    raise SystemExit(1 if bad else 0)
