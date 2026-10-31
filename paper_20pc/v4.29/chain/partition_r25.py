#!/usr/bin/env python3
r"""partition_r25.py -- GATE: the published counts partition each other.

WHY THIS FILE EXISTS (round 25, Ruling 9)

    Referee 2 sent fourteen internal inconsistencies.  Six of them -- B1, B2,
    B3, B4, B10 and B12 -- were the same shape: a count published by one
    generator that is supposed to be the sum of counts published by others,
    with nothing anywhere comparing the two.  Each generator asserted its own
    arithmetic and every one of those assertions passed; what nothing checked
    was the arithmetic BETWEEN them.  That is why fourteen inconsistencies
    survived five rounds of referees and were found by a reader instead.

    So this gate owns exactly one thing: cross-generator partitions.  It
    reads the macro layer -- the values that are actually typeset -- and
    requires each identity to close exactly in integers.  It computes
    nothing; a generator that cannot produce its own number is not this
    gate's problem.

HOW TO READ A FAILURE

    A failure here names two sentences of the paper that cannot both be true.
    It does NOT say which is wrong.  Resolve it at the generator that owns
    the smaller side, never by editing the sum.

PROVENANCE OF THE LIST

    `r25-consist` built a 25-identity audit, found 24 clean and the 25th
    failing (that was B2), and recommended promoting it into `gate.sh`.  Its
    working tree was deleted before integration, so the identities below are
    rebuilt from the six it named in its queue's C1 section plus the
    partitions this build's own generators assert internally.  Rebuilt, not
    copied -- which is why each carries its source.

    ★ Every identity is checked for VACUITY as well as for truth: an identity
    whose terms are all zero, or which names a macro the layer does not
    carry, is a FAIL and not a skip.  A partition check that silently passes
    on a missing macro is the defect it exists to catch, one level up.

DRIVE (`--drive N`): perturbs identity N's left-hand side by one and requires
    the gate to fail on exactly that identity.

Usage:  partition_r25.py [--drive N] [--list]
"""
import glob
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))

#: (id, source of the identity, left macro, [right macros])
#: Every one is "the left count IS the sum of the right counts", in integers.
IDENT = [
    ('B2', 'D.4 walks the subtraction: the unattributed crossings that enter '
           'the chance comparison are the census less the attributed, the '
           'quality-flagged, the archival tail and the atmospheric one',
     'MkUnattr', ['CeObs', 'EvNCrossFlag', 'CeNTailCross', 'CeTlObsCut']),
    ('B2b', 'and the crossing census itself splits into attributed and '
            'unattributed',
     'NCross', ['MkAttr', 'MkUnattr']),
    ('B3', 'the recurrence test partitions the whole unattributed set: the '
           'ones it excludes, the ones too shallow to test, the ones '
           'withheld on data quality, and the one not read',
     'RcNTested', ['HjNPowerHi', 'HjNPowerLo', 'RcNWithheld', 'RcNUnread']),
    ('B3b', 'and the crossings that carry a repeat reading are that set less '
            'the one that carries none',
     'RcNTested', ['RcNExclPoss', 'RcNUnread']),
    ('B4', 'the unresolved pairs are the open ones and the edge-limited '
           'ones, which the table prints as disjoint',
     'TjNOpen', ['TjNOpenPlain', 'TjNPairEdge']),
    ('B4b', 'and the testable pairs are those the grid separates and those '
            'it leaves unresolved',
     'TjNPair', ['TjNExcl', 'TjNOpen']),
    #: ★ the repeat-block term is `\RcNRepeatBlock`, `recur_v411.py`'s, and
    #: NOT a `\ZcNRecEBRep` of `confset_r18.py`'s own: that generator
    #: deliberately declines to publish a second name for a quantity another
    #: generator already owns, and asserts the two equal instead.  My first
    #: version of this list named the macro that would have existed if it
    #: had, and the vacuity clause below reported it as absent from the layer
    #: rather than skipping it -- which is the behaviour this gate was
    #: written for, working on the gate itself.
    # ★ r28 (Ruling R3): the repeat blocks the test READS include those of
    # the three sulphur-monoxide crossings the mask now attributes, so they
    # are no longer round 120's \RcNRepeatBlock (the unattributed crossings'
    # own).  The partition is over what is read; confset_r18's Z12 asserts
    # that round 120's set is the unattributed part of it.
    ('B10', 'the recurrence test reads the repeat blocks together with the '
            'discovery blocks that supply the other end of a comparison',
     'ZcNRecEB', ['ZcNRecEBRep', 'ZcNRecEBDisc']),
    ('B12', 'the searched Class A windows the deposit does not tabulate are '
            'the archival tail plus the companion resolved after the census '
            'closed',
     None, None),           # handled below: a difference, not a sum
    ('B14', 'under A3 option (a) the mask holds no species whose '
            'coincidences are withheld, so every coincidence IS an '
            'attribution and the two counts are one count -- the identity '
            'the abstract\'s "coincide with" sentence depends on',
     'MkNCoinc', ['MkAttr', 'ZzZero']),
    ('W1', 'the window census splits on channel width',
     'NWindows', ['NWinA', 'NWinB']),
    ('Q1', 'the crossings split on the block-quality criterion',
     'EvNCrossRaw', ['EvNCrossQp', 'EvNCrossFlag']),
    ('Q2', 'and the quality-passing crossings split on attribution',
     'EvNCrossQp', ['EvNAttrQp', 'EvNUnattrQp']),
]


def _num(x):
    x = x.replace('\\,', '').replace(',', '').strip()
    return int(x)


def layer(drive=None):
    """Every `\\newcommand` of the generated macro layer, as the page has it.
    The *_driveN.tex artefacts are excluded by name: they are a drive's own
    output and are not typeset."""
    out = {}
    for fn in sorted(glob.glob(os.path.join(HERE, 'numbers/survey_numbers*.tex'))):
        if re.search(r'_drive\d+\.tex$', fn):
            continue
        #: ★ `\providecommand{\X}{}\renewcommand{\X}{v}` is how a dozen of
        #: this build's generators emit a macro, so a pattern that reads only
        #: `\newcommand` sees neither `\NCross` nor `\NHits` and a gate built
        #: on it would report half this paper's headline counts as "absent
        #: from the layer" -- which is a skip wearing a failure's clothes.
        for m in re.finditer(
                r'\\(?:new|renew|provide)command\{\\([A-Za-z]+)\}\{([^}]*)\}',
                open(fn, encoding='utf-8').read()):
            if not m.group(2).strip():
                continue
            out[m.group(1)] = m.group(2)
    return out


#: a generated zero, so that a two-term identity whose second term is
#: structurally empty is still written as a partition rather than as an
#: equality -- and so that the vacuity clause below can still see it.
ZZ = {'ZzZero': '0'}


def main():
    drive = None
    a = sys.argv[1:]
    if '--drive' in a:
        drive = a[a.index('--drive') + 1]
    if '--list' in a:
        for i, w, lhs, rhs in IDENT:
            print('%-5s %s' % (i, w))
        return 0
    M = layer()
    M.update({k: v for k, v in ZZ.items() if k not in M})
    print('partition_r25: %d macros in the layer, %d identities'
          % (len(M), len(IDENT)))
    fail = []
    for ident, why, lhs, rhs in IDENT:
        if ident == 'B12':
            need = ['VnWinA', 'NWinA', 'VnTailNWinA', 'VnCompNWinA']
            miss = [k for k in need if k not in M]
            if miss:
                fail.append(ident)
                print('  %-5s FAIL  macro(s) absent from the layer: %s'
                      % (ident, ', '.join(miss)))
                continue
            left = _num(M['VnWinA']) - _num(M['NWinA'])
            terms = [_num(M['VnTailNWinA']), _num(M['VnCompNWinA'])]
            if drive == ident:
                left += 1
        else:
            need = [lhs] + rhs
            miss = [k for k in need if k not in M]
            if miss:
                fail.append(ident)
                print('  %-5s FAIL  macro(s) absent from the layer: %s'
                      % (ident, ', '.join(miss)))
                continue
            try:
                left = _num(M[lhs])
                terms = [_num(M[k]) for k in rhs]
            except ValueError as e:
                fail.append(ident)
                print('  %-5s FAIL  a term is not an integer: %s' % (ident, e))
                continue
            if drive == ident:
                left += 1
        #: ★ NON-VACUITY.  An identity in which the right-hand side is a
        #: single term, or in which every term is zero, is arithmetic about
        #: nothing.  It is reported as a failure, because a partition gate
        #: that passes on a degenerate identity is the defect it exists to
        #: catch, one level up.
        vacuous = len(terms) < 2 or sum(abs(t) for t in terms) == 0
        ok = (left == sum(terms)) and not vacuous
        if not ok:
            fail.append(ident)
        print('  %-5s %-4s  %d = %s = %d%s'
              % (ident, 'PASS' if ok else 'FAIL', left,
                 ' + '.join(str(t) for t in terms), sum(terms),
                 '   [VACUOUS]' if vacuous else ''))
        if not ok:
            print('        %s' % why)
    print('partition_r25: %d identities, %d FAIL' % (len(IDENT), len(fail)))
    if fail:
        print('partition_r25: a failure here names two sentences of the paper '
              'that cannot both be true.  Resolve it at the generator that '
              'owns the smaller side, never by editing the sum.')
    return 1 if fail else 0


if __name__ == '__main__':
    sys.exit(main())
