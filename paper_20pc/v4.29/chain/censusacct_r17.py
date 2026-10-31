#!/usr/bin/env python3
r"""Gate on the crossing accounting of the front matter.  Publishes nothing.

Referee 1's first point was that the paper reported one crossing total over
two different populations: the primary census and the archival tail.
The conclusions set the accounting out in full --- the census's Class A
crossings, the Class B crossings of the one block that fails the quality
criterion, and the archival tail's Class A crossings --- and that statement is an
ARITHMETIC IDENTITY between four macros emitted by three unrelated
generators:

    \CkNCrossCenA   50  cells_v416.py  (round 510), asserted by its own C9
    \EvNCrossFlag    4  events_r12.py  (round 230)
    \CeNTailCross    2  chance_v414.py (round 310)
    \EvNCrossRaw    56  events_r12.py  (round 230)
    \EvNCrossQp     52  events_r12.py  (round 230)

Nothing in the build checked that the identity closes.  Prose arithmetic that
no gate evaluates is this project's commonest defect, and the accounting the
referee complained about is exactly the kind that drifts: three of the five
numbers moved in the round before this one.  So the identity is evaluated
here, from the macro layer, and the prose is required to keep citing the
terms --- an identity typeset in one place and checked in another is only
worth something if deleting the sentence fails the build too.

This file reads the macro layer and the section sources.  It shares no code
with any generator that writes them, and the three generators behind the five
macros are independent of one another, so no clause can be satisfied by the
thing it is checking.

CHECKS (rule 9: every one is driven to fail on purpose)

    A1  census Class A + flagged Class B + extension Class A == the reported
        total.  50 + 4 + 2 == 56;
    A2  census Class A + extension Class A == the quality-passing total, and
        the flagged crossings are the whole difference.  50 + 2 == 52, and
        52 + 4 == 56.  This is Referee 1's third point: the quality-passing
        data hold \EvNCrossQp{} crossings and they are all Class A;
    A3  the attributed and unattributed quality-passing crossings partition
        that same total.  18 + 34 == 52.  \S6.1 now quotes all three, where
        it used to quote the pooled 56;
    A4  the conclusions carry every term of A1 and A2, so the accounting
        cannot be deleted from the text while the macros still agree.  The
        four Class B crossings must be DESCRIBED there as the whole of the
        Class B crossing population and as coming from the failing block,
        which is what Referee 1 asked for and what a count alone does not
        say;
    A5  \S6.1 attributes the crossings on the quality-passing population and
        never on the pooled total: \NCross is banned from that subsection.
        The pooled macro is what produced the inconsistency in the first
        place.

Usage: `python3 censusacct_r17.py [--drive N]`, N in 1..8.  Nothing is
written, including under a drive: every drive perturbs an in-memory copy, so
no run of this file can leave a path production reads.

★ Drives 1 and 2 each fire TWO clauses, and that is stated rather than
hidden: A1 and A2 are two routes through the same five counts, so no single
term belongs to one of them alone, and drive 2's perturbation of the
quality-passing total is read by A3 as well.  Drives 3, 4 and 5 fire exactly
one clause each.  All five have been made to fail on purpose.
"""
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
SEC = os.path.join(HERE, 'sections')

DRIVE = 0
if '--drive' in sys.argv:
    DRIVE = int(sys.argv[sys.argv.index('--drive') + 1])

FAIL = []


def ck(label, ok, detail=''):
    print('%-5s %s%s' % ('PASS' if ok else 'FAIL', label,
                         '  [%s]' % detail if detail else ''))
    if not ok:
        FAIL.append(label)


def texval(name):
    """A macro's value as the macro layer defines it, last definition
    winning, which is the order TeX reads the round files in."""
    pat = re.compile(r'\\(?:new|renew|provide)command\{\\%s\}\{([^}]*)\}'
                     % name)
    hit = None
    for fn in sorted(os.listdir(os.path.join(HERE, 'numbers'))):
        if not re.match(r'survey_numbers_round\d+\.tex$', fn):
            continue
        for line in open(os.path.join(HERE, 'numbers', fn)):
            m = pat.search(line)
            if m and m.group(1).strip():
                hit = m.group(1)
    if hit is None:
        sys.exit('censusacct: \\%s is not defined anywhere in the macro '
                 'layer -- that is a failure, not a pass' % name)
    return hit


def num(name):
    v = texval(name)
    if not re.fullmatch(r'\d+', v):
        sys.exit('censusacct: \\%s is %r and not a plain integer; this gate '
                 'cannot be allowed to compare something it cannot read'
                 % (name, v))
    return int(v)


def text(fn):
    return ' '.join(open(os.path.join(SEC, fn)).read().split())


CEN_A = num('CkNCrossCenA')
FLAG = num('EvNCrossFlag')
TAIL = num('CeNTailCross')
RAW = num('EvNCrossRaw')
QP = num('EvNCrossQp')
ATTR_QP = num('EvNAttrQp')
UNATTR_QP = num('EvNUnattrQp')

CONC = text('07_conclusions.tex')
DISC = text('06_discussion.tex')

#: the drives.  Each perturbs one input of one clause, in memory only.
if DRIVE == 1:
    TAIL += 1
if DRIVE == 2:
    QP += FLAG
if DRIVE == 3:
    UNATTR_QP -= 1
#: drive 4 now perturbs the whole-paper text A4 reads (r27, Ruling 16), below
if DRIVE == 5:
    DISC = DISC.replace(r'for \EvNAttrQp{} of the \EvNCrossQp{} crossings '
                        r'in quality-passing data',
                        r'for \NAttributed{} of the \NCross{} threshold '
                        r'crossings')
    DISC = DISC.replace(r'for \CsNAttrQp{} of the \CsNCrossQp{} crossings '
                        r"in the census's quality-passing data",
                        r'for \NAttributed{} of the \NCross{} threshold '
                        r'crossings')

ck('A1 the census, the failing block and the archival tail sum to the '
   'reported crossing total',
   CEN_A + FLAG + TAIL == RAW,
   '%d census Class A + %d flagged Class B + %d archival-tail Class A = %d '
   'against \\EvNCrossRaw %d'
   % (CEN_A, FLAG, TAIL, CEN_A + FLAG + TAIL, RAW))

ck('A2 the quality-passing crossings are the census and archival-tail '
   'Class A sets, and the flagged block is the whole of the difference',
   CEN_A + TAIL == QP and QP + FLAG == RAW,
   '%d + %d = %d against \\EvNCrossQp %d; %d + %d = %d against %d'
   % (CEN_A, TAIL, CEN_A + TAIL, QP, QP, FLAG, QP + FLAG, RAW))

ck('A3 the attributed and unattributed quality-passing crossings partition '
   'that total',
   ATTR_QP + UNATTR_QP == QP and min(ATTR_QP, UNATTR_QP) > 0,
   '%d attributed + %d unattributed = %d against %d'
   % (ATTR_QP, UNATTR_QP, ATTR_QP + UNATTR_QP, QP))

#: ★ r27 (Ruling 16): A4 requires the accounting IN THE PAPER, not in the
#: conclusions.  The author's complaint was this bookkeeping in the
#: conclusions; the invariant A4 protects is that the paper states every
#: term and describes the flagged set where it counts it, and placement in
#: one section is not that invariant.  Each term may be given by any of the
#: macros that carry its value.
PAPERTXT = ' '.join(text(_f) for _f in sorted(os.listdir(SEC))
                    if _f.endswith('.tex') and _f != 'abstract.tex')
if DRIVE == 4:
    PAPERTXT = re.sub(r'\\CeNTailCross(?:Word)?\{\}', 'a few more', PAPERTXT)
#: ★ r28 (integrate): the census Class A count is also printed as the census
#: QUALITY-PASSING count \CsNCrossQp (the failing block holds no Class A
#: window, events_r12 E1), and after the text pass that is the only macro the
#: paper gives it by.  It counts as this term only while the two are EQUAL,
#: which A4 asserts below -- the fact is pinned, not the macro name.
CS_QP = num('CsNCrossQp')
_terms = [(r'\CkNCrossCenA', r'\MtCrossACen')
          + ((r'\CsNCrossQp',) if CS_QP == CEN_A else ()),
          (r'\PrFlagXrossWord', r'\EvNCrossFlag', r'\LdgNCrossB'),
          (r'\CeNTailCrossWord', r'\CeNTailCross{}'),
          (r'\EvNCrossRaw',), (r'\EvNCrossQp', r'\CsNCross')]
# ★ GEN (v4.29 fold, E3): with ALMA's final flags the failing block holds NO crossing (\EvNCrossFlag 0), and the
#   text owner rewrote every sentence that counted it (guarded by G2/G3 below).  The flagged term and its
#   description are required while the flagged set is non-empty; drive 8 forces it non-empty, so A4 still fires.
_FLAG_LIVE = num('EvNCrossFlag') > 0 or DRIVE == 8
if not _FLAG_LIVE:
    _terms = [t for t in _terms if r'\EvNCrossFlag' not in t]
_missing = [t[0] for t in _terms if not any(x in PAPERTXT for x in t)]
#: ★★★★ v4.25: A4 PINNED THE WORDS AND NOT THE FACT, AND THE WORDS IT PINNED
#: WERE A TAUTOLOGY.  It required the conclusions to contain "Class B
#: crossings are the whole of that search's crossing population" -- a clause
#: that is true by construction, because \PrFlagXrossWord IS the count of that
#: search's crossings, so it carries no information and a length pass was
#: right to delete it.  The check then failed on prose that was strictly
#: better.  What A4 exists to require is that the flagged set is DESCRIBED
#: rather than merely counted: a reader meeting the number must learn, in the
#: same sentence, that those crossings all come from the one execution block
#: that fails the data-quality criterion.  That is what is pinned now, as a
#: property of the sentence carrying the count and not as a form of words.
#: ►► The standing rule it follows: a gate may pin that a fact is stated; it
#: may not pin the words that state it.
_flagsent = [_s for _s in re.split(r'(?<=[.!?])\s+', PAPERTXT)
             if any(m in _s for m in (r'\PrFlagXrossWord', r'\LdgNCrossB'))
             and (r'\EvNCrossRaw' in _s or r'\CkNCrossCenA' in _s
                  or r'\CsNCross' in _s
                  or r'\MtCrossACen' in _s)]
if DRIVE == 8:                     # the count is printed with no description
    _flagsent = ['All \\PrFlagXrossWord{} Class~B crossings are set aside.']
_described = any(
    re.search(r'fails the data-quality criterion', _s)
    and re.search(r'single execution block|one execution block', _s)
    for _s in _flagsent)
ck('A4 the paper carries every term of the accounting and describes the '
   'flagged set in the sentence that counts it',
   not _missing and (_described or not _FLAG_LIVE),
   'missing %s; %d sentence(s) carry the flagged count; flagged set %s; '
   'census Class A %d, census quality-passing %d'
   % (_missing or 'nothing', len(_flagsent),
      'described in the sentence that counts it' if _described
      else 'COUNTED BUT NOT DESCRIBED', CEN_A, CS_QP))

_pooled = re.search(r'\\NCross\b', DISC) is not None
ck('A5 the attribution in the discussion is made on the quality-passing '
   'population and not on the pooled total',
   not _pooled
   and any(m in DISC for m in (r'\EvNAttrQp', r'\CsNAttrQp'))
   and any(m in DISC for m in (r'\EvNCrossQp', r'\CsNCrossQp'))
   and any(m in DISC for m in (r'\EvNUnattrQp', r'\CsNUnattrQp')),
   'pooled \\NCross %s; quality-passing terms %s'
   % ('PRESENT' if _pooled else 'absent',
      'present' if r'\EvNAttrQp' in DISC else 'MISSING'))

#: ★★★ A6, v4.24: THE ABSTRACT NOW ASKS THE READER TO DO A FOUR-TERM
#: SUBTRACTION, AND NOTHING PINNED IT.  The paragraph reads "Of the \MkUnattr
#: unattributed -- \PrFlagXrossWord failing a quality criterion,
#: \CeNTailCrossWord outside the control sample, \CeTlObsCutWord atmospheric
#: -- \CeObs are consistent with chance", and those four terms come from four
#: different generators (`counts_r15`, the quality ledger, `chance_v414`
#: twice).  A1-A3 pin the census splits; the chain a reader actually performs
#: in their head was unpinned, so any one term moving alone would print a
#: paragraph whose arithmetic does not close.  The second identity is the one
#: the recurrence sentence rests on: exactly one unattributed crossing has no
#: repeat reading, published as two counts in two sentences and nowhere
#: compared.
#: ★ It lives in a GATE and not in a generator because the terms are owned by
#: generators on both sides of `chance_v414.py` in `make_all.sh`: inside the
#: build the chain is not yet closable, and a check that has to be deferred is
#: a check that can be deferred into vacuity.  A gate runs when the whole
#: layer is published.  (Tried in `census_r12.py` first; it failed the build
#: at line 473, which is the cycle telling the truth.)
#: ★ Identities, never values: every term may move and the clause still holds
#: iff the paragraph stays arithmetically readable.
UNATTR = num('MkUnattr')
TLCUT = num('CeTlObsCut')
CEOBS = num('CeObs')
NREP = num('RcNExclPoss')
_chain = UNATTR - FLAG - TAIL - TLCUT
_norep = UNATTR - NREP
if DRIVE == 6:
    _chain += 1                    # the deductions stop closing on \CeObs
if DRIVE == 7:
    _norep += 1                    # two crossings with no repeat, not one
ck('A6 the deductions the abstract prints close on the count it prints, and '
   'exactly one unattributed crossing has no repeat reading, so the '
   'arithmetic a reader does in that paragraph is the arithmetic the '
   'generators did',
   # GEN (v4.29 fold, E3): "_norep == 1" was HD 14055 U25 X29ae, the one unattributed crossing with no repeat
   # reading; it fell with ALMA's flags.  The count the paper publishes for that set is \RcNUnread (now 0).
   _chain == CEOBS and _norep == num('RcNUnread'),
   r'\MkUnattr %d - \EvNCrossFlag %d - \CeNTailCross %d - \CeTlObsCut %d '
   r'= %d against \CeObs %d; \MkUnattr - \RcNExclPoss %d = %d against \RcNUnread %d'
   % (UNATTR, FLAG, TAIL, TLCUT, _chain, CEOBS, NREP, _norep, num('RcNUnread')))

# =====================================================================
# ★ GEN (v4.29 fold, coordinator D9/D10): DIRECTION GUARDS for the sentences the fold made true by REWRITING
# them (ALMA's flags emptied the failing block, the atmospheric screen catches no crossing, nothing is unread).
# Each guard is bound to its sentence: while the sentence is on the page its condition must hold, so a stage-2
# fold that puts a crossing back stops the build and the sentence must change with it.  No sentence, no pin.
# Drives 11-16 break one condition each.
# =====================================================================
def _flat(fn):
    t = re.sub(r'(?<!\\)%.*', '', open(os.path.join(SEC, fn), errors='ignore').read())
    return re.sub(r'\s+', ' ', t)


_CONC, _SAMP, _METH, _RES = (_flat('07_conclusions.tex'), _flat('03_sample.tex'), _flat('04_method.tex'),
                             _flat('05_results.tex'))
_GV = dict((k, num(k)) for k in ('CeTlObsCut', 'CeObs', 'CsNUnattrQp', 'EvNCrossFlag', 'CsNCross',
                                 'CsNCrossQp', 'BqFailNCross', 'RcNUnread', 'WuNWinExc', 'WuNWinExcTwo'))
_PHD, _ALPHA = float(texval('TwProbHD')), float(texval('CeAlphaPct')) / 100.0
for _d, _k, _v in ((11, 'CeTlObsCut', 1), (12, 'CsNCrossQp', _GV['CsNCross'] - 1), (13, 'BqFailNCross', 1),
                   (14, 'RcNUnread', 1), (16, 'WuNWinExcTwo', 0)):
    if DRIVE == _d:
        _GV[_k] = _v
if DRIVE == 15:
    _PHD = 0.5 * _ALPHA
# G1 (D9): conclusions "The other \CsNUnattrQp{} are consistent with chance" -- no atmospheric crossing set aside
if r'The other \CsNUnattrQp{} are consistent with chance' in _CONC:
    ck('G1 "the other N are consistent with chance": none is atmospheric and they are the compared count',
       _GV['CeTlObsCut'] == 0 and _GV['CeObs'] == _GV['CsNUnattrQp'],
       r'\CeTlObsCut %d, \CeObs %d, \CsNUnattrQp %d' % (_GV['CeTlObsCut'], _GV['CeObs'], _GV['CsNUnattrQp']))
# G2 (D10): Sec. 2 "It holds \CsNCross{} of the \EvNCrossRaw{} ... crossings this paper reports, all in quality-passing data"
if 'all in quality-passing data' in _SAMP:
    ck('G2 Sec. 2 "all in quality-passing data": the failing block holds none and the census is its quality-passing part',
       _GV['EvNCrossFlag'] == 0 and _GV['CsNCross'] == _GV['CsNCrossQp'],
       r'\EvNCrossFlag %d, \CsNCross %d, \CsNCrossQp %d' % (_GV['EvNCrossFlag'], _GV['CsNCross'], _GV['CsNCrossQp']))
# G3 (D10): Sec. 3.x "With ALMA's final flags restored it holds no crossing"
if 'final flags restored it holds no crossing' in _METH:
    ck('G3 Sec. 3 "the failing block holds no crossing"', _GV['BqFailNCross'] == 0 and _GV['EvNCrossFlag'] == 0,
       r'\BqFailNCross %d, \EvNCrossFlag %d' % (_GV['BqFailNCross'], _GV['EvNCrossFlag']))
# G4 (D10): Sec. 4.6 reads the predicted cell "on the \RcNExclPoss{} unattributed crossings" with no unread remainder
if r'On the \RcNExclPoss{} unattributed crossings' in _RES:
    ck('G4 Sec. 4.6 names no unread crossing, so none may exist', _GV['RcNUnread'] == 0,
       r'\RcNUnread %d' % _GV['RcNUnread'])
# G5 (D10, INTEGRATE 7.2 #1): "its concentration is its exposure" / "HD 14055's share is explained by its exposure"
if 'its concentration is its exposure' in _RES or "share is explained by its exposure" in _CONC:
    ck('G5 HD 14055 "explained by its exposure": its own probability is above the level', _PHD > _ALPHA,
       r'\TwProbHD %.3f against %.3f' % (_PHD, _ALPHA))
# G6 (D10, INTEGRATE 7.2 #2): "\TwNWinExcTwoWord{} of them toward two objects" read as a concentration -- at least half
if r'\TwNWinExcTwoWord{} of them toward two objects' in _CONC:
    ck('G6 "N of them toward two objects" is a concentration: at least half of the repeat windows above the trigger',
       2 * _GV['WuNWinExcTwo'] >= _GV['WuNWinExc'],
       r'\WuNWinExcTwo %d of \WuNWinExc %d' % (_GV['WuNWinExcTwo'], _GV['WuNWinExc']))
# G7 (coordinator, after D15): App. E.2's table cell "none inside the \ScRadMHz MHz screening radius" and the
# deposit excerpt's "No crossing lies inside the atmospheric screen's radius" -- no crossing may lie inside it.
_RFI = _flat('app_N_rfi.tex')
_EXC_E = re.sub(r'\s+', ' ', open(os.path.join(HERE, 'r28inputs', 'docapx', 'appendix_E_rfi.excerpt'),
                                  errors='ignore').read())
_INRAD = num('ScNInRad') if DRIVE != 17 else 1
if (r'none inside the \ScRadMHz' in _RFI
        or "No crossing lies inside the atmospheric screen's radius" in _EXC_E):
    ck('G7 App. E.2 / deposit excerpt "no crossing inside the screening radius"', _INRAD == 0,
       r'\ScNInRad %d' % _INRAD)
# (D10 #4, eps Eri "no window reaches the trigger": the sentence is not in the v4.29 sections or deposit excerpts --
#  checked 2026-10-29 -- so there is nothing to bind; re-add a guard with the sentence if it returns.)

print('censusacct_r17: %d check(s), %d FAILED' % (6, len(FAIL)))
if FAIL:
    sys.exit('censusacct_r17: FAILED %s' % FAIL)
if DRIVE:
    sys.exit('censusacct_r17: DRIVE %d DID NOT FAIL -- the clause it '
             'exercises is vacuous' % DRIVE)
