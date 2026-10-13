#!/usr/bin/env python3
r"""Gate on the crossing accounting of the front matter.  Publishes nothing.

Referee 1's first point was that the paper reported one crossing total over
two different populations: the primary census and the archival extension.
The conclusions now set the accounting out in full --- the census's Class A
crossings, the Class B crossings of the one block that fails the quality
criterion, and the extension's Class A crossings --- and that statement is an
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

Usage: `python3 censusacct_r17.py [--drive N]`, N in 1..5.  Nothing is
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
    for fn in sorted(os.listdir(HERE)):
        if not re.match(r'survey_numbers_round\d+\.tex$', fn):
            continue
        for line in open(os.path.join(HERE, fn)):
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
if DRIVE == 4:
    CONC = CONC.replace(r'\CeNTailCrossWord{} Class~A', 'a few more')
if DRIVE == 5:
    DISC = DISC.replace(r'for \EvNAttrQp{} of the \EvNCrossQp{} crossings '
                        r'in quality-passing data',
                        r'for \NAttributed{} of the \NCross{} threshold '
                        r'crossings')

ck('A1 the census, the failing block and the archival extension sum to the '
   'reported crossing total',
   CEN_A + FLAG + TAIL == RAW,
   '%d census Class A + %d flagged Class B + %d extension Class A = %d '
   'against \\EvNCrossRaw %d'
   % (CEN_A, FLAG, TAIL, CEN_A + FLAG + TAIL, RAW))

ck('A2 the quality-passing crossings are the census and extension Class A '
   'sets, and the flagged block is the whole of the difference',
   CEN_A + TAIL == QP and QP + FLAG == RAW,
   '%d + %d = %d against \\EvNCrossQp %d; %d + %d = %d against %d'
   % (CEN_A, TAIL, CEN_A + TAIL, QP, QP, FLAG, QP + FLAG, RAW))

ck('A3 the attributed and unattributed quality-passing crossings partition '
   'that total',
   ATTR_QP + UNATTR_QP == QP and min(ATTR_QP, UNATTR_QP) > 0,
   '%d attributed + %d unattributed = %d against %d'
   % (ATTR_QP, UNATTR_QP, ATTR_QP + UNATTR_QP, QP))

_terms = [r'\CkNCrossCenA', r'\PrFlagXrossWord', r'\CeNTailCrossWord{} Class~A',
          r'\EvNCrossRaw', r'\EvNCrossQp']
_missing = [t for t in _terms if t not in CONC]
_described = (re.search(r'Class~B crossings are the whole of that\s*'
                        r'search\'s crossing population', CONC) is not None
              and re.search(r'fails the data-quality criterion', CONC)
              is not None)
ck('A4 the conclusions carry every term of the accounting and describe the '
   'flagged set rather than merely counting it',
   not _missing and _described,
   'missing %s; flagged set %s'
   % (_missing or 'nothing',
      'described' if _described else 'COUNTED BUT NOT DESCRIBED'))

_pooled = re.search(r'\\NCross\b', DISC) is not None
ck('A5 the attribution in the discussion is made on the quality-passing '
   'population and not on the pooled total',
   not _pooled and r'\EvNAttrQp' in DISC and r'\EvNCrossQp' in DISC
   and r'\EvNUnattrQp' in DISC,
   'pooled \\NCross %s; quality-passing terms %s'
   % ('PRESENT' if _pooled else 'absent',
      'present' if r'\EvNAttrQp' in DISC else 'MISSING'))

print('censusacct_r17: %d check(s), %d FAILED' % (5, len(FAIL)))
if FAIL:
    sys.exit('censusacct_r17: FAILED %s' % FAIL)
if DRIVE:
    sys.exit('censusacct_r17: DRIVE %d DID NOT FAIL -- the clause it '
             'exercises is vacuous' % DRIVE)
