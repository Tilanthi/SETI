#!/usr/bin/env python3
r"""Gate on the seven statements the abstract must carry.  Publishes nothing.

The abstract is the one paragraph every reader and every referee reads in
full, and it is also the only part of the paper under a hard external limit:
arXiv refuses an abstract over 1920 characters.  Those two facts pull in
opposite directions, and what gets sacrificed to a character budget is never
a number -- it is a qualification, because a qualification is the part of a
sentence that can be removed without the sentence becoming ungrammatical or
obviously false.  Every clause here is one of those.

WHY THIS FILE EXISTS.  Five clauses already protect this paragraph:
`prose_v412.py` P4 (the class of transmitter non-recurrence excludes, with
the width of the interval the test permits), P7 (a bandwidth is labelled a
union bandwidth), P9 (the crossing total never appears without the flagged
subset), P10 (the chance comparison is stated as a consistency), and
`prosegate_r15.py` S6 (the sensitivity is conditional on the carrier being
narrower than the channel, and carries the drift fraction).  Four more
statements were required of the abstract and gated by nothing:

    the count of crossings whose repeats are too shallow to test them;
    that the quoted limits exclude atmospheric decorrelation;
    that the chance comparison does not exclude a smaller added population;
    that a calibration residual is admissible in some windows and is
      measured to act in none.

All four are qualifications that weaken a claim.  All four could have been
deleted to buy characters without any gate noticing, and one of them -- the
first -- had already been reduced from a count to a single case in an earlier
draft, which is the conflation the correction exists to prevent.

HOW IT AVOIDS THE TWO FAILURE MODES THIS PROJECT KEEPS HITTING.

(a) A gate that cannot fail.  Every clause is driven to fail on purpose
    (`--drive 1..7`), and the module refuses to run at all if the extracted
    paragraph is implausibly short, so it can never report success on an
    abstract it did not read.

(b) A prose gate pinned to a sentence a measurement later falsifies -- which
    is how P4 came to forbid the exact wording Referee 2 required.  So each
    clause keys on the MACRO that carries the statement, which cannot be
    paraphrased away and moves with the measurement, plus the smallest
    semantic token that distinguishes the qualification from its absence.
    Where a token has a hyphen, both renderings are searched: a hyphenated
    phrase hides from a de-hyphenated search and has done so here before.

It reads `sections/abstract.tex` with comments stripped -- a requirement
satisfied by a comment is not satisfied -- and the macro layer for the values
it reports.  It shares no code with any generator.

CHECKS

    B1  the number of crossings whose repeats cannot test them is given as a
        COUNT (\RcNPowerLoTrig), with "too shallow" and the amplitude the
        power is evaluated at.  "None recurred" and "persistence excluded"
        are different statements and the paragraph must hold both;
    B2  no confirmed carrier is claimed either way: the plain negative
        result is stated, and the trajectory family the test does not
        constrain is not reintroduced -- "1 au", "frequency-stable" and
        "frequency stable" are banned, the orbit having been the premise
        Referee 2 showed the fitted drifts contradict;
    B3  the chance comparison is stated as a CONSISTENCY, against the
        control positions of the same fields, and says in the same sentence
        what it does not exclude -- a smaller added population (R1-4, R1-6).
        ★ This clause used to require the sentence to name the \StHoObs
        reserved events the step rested on.  That qualification has not been
        dropped: the step is now measured on the census's own cell ladder at
        every level up to the trigger, the reserved events are the
        out-of-sample check rather than the measurement, and the sentence
        naming them would be false of this build.  The gate moved with the
        measurement;
    B4  the calibration residual carries BOTH halves: admissible in
        \CxNAdmit{} windows, and measured to act in none.  Either half alone
        is a different and wrong statement;
    B5  the limits are said to exclude atmospheric decorrelation and to be
        optimistic by it, in one sentence;
    B6  the headline depth and the scale are present: \EirpNinetySysMedA,
        \NWinA, \NSysClassA and \NWinB;
    B7  what limits the search is coverage and not depth, with the systems
        that cannot be confirmed (\ZcNoRepSys, R2-1), and line emission named as
        the astrophysical false positive.

Usage: `python3 absreq_r17.py [--drive N]`, N in 1..7.  Nothing is written,
under a drive or otherwise: every drive perturbs an in-memory copy, so no run
of this file can leave a path production reads.
"""
import glob
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
SEC = os.path.join(HERE, 'sections')
ABSFILE = os.path.join(SEC, 'abstract.tex')
#: below this the extraction has clipped and no verdict here is trustworthy
FLOOR = 900

DRIVE = None
if '--drive' in sys.argv:
    DRIVE = int(sys.argv[sys.argv.index('--drive') + 1])

FAIL = []


def ck(label, ok, detail=''):
    print('%-5s %s%s' % ('PASS' if ok else 'FAIL', label,
                         '  [%s]' % detail if detail else ''))
    if not ok:
        FAIL.append(label.split()[0])


def macros():
    """The macro layer, read the way every other tool here reads it."""
    out = {}
    for fn in glob.glob(os.path.join(HERE, 'survey_numbers*.tex')):
        if '_drive' in os.path.basename(fn):
            continue
        for name, val in re.findall(
                r'^\\(?:newcommand|renewcommand)\{\\([A-Za-z]+)\}\{(.*)\}\s*$',
                open(fn).read(), re.M):
            out[name] = val
    return out


def body():
    """The abstract paragraph, comments stripped, whitespace collapsed."""
    raw = open(ABSFILE).read()
    m = re.search(r'\\begin\{abstract\}(.*?)\\end\{abstract\}', raw, re.S)
    if not m:
        sys.exit('absreq_r17: no abstract environment in %s -- the gate '
                 'cannot check what it cannot find, so this is a FAILURE, '
                 'not a pass' % ABSFILE)
    t = m.group(1)
    t = re.sub(r'(?m)^\s*%.*$', '', t)
    t = re.sub(r'(?<!\\)%.*$', '', t, flags=re.M)
    return ' '.join(t.split())


def has(t, *alts):
    """True if any rendering is present.  A hyphen is a rendering: `\\,` and
    `-` both wrap, so a phrase written with one hides from a search for the
    other, and that has cost this project a round."""
    for a in alts:
        for v in {a, a.replace('-', ' '), a.replace(' ', '-')}:
            if re.search(v, t, re.I):
                return True
    return False


def sentences(t):
    return [s for s in re.split(r'(?<=[.!?])\s+', t) if s.strip()]


ABS = body()
MAC = macros()

#: the drives.  Each is the smallest perturbation that removes exactly one
#: qualification, written the way a character-budget edit would make it.
if DRIVE == 1:
    #: the conflation the correction exists to prevent: the count becomes the
    #: single event, which is how it was written before.
    ABS = re.sub(r'For \\RcNPowerLoTrig\{\}[^.]*\.',
                 'One of them is untested.', ABS)
if DRIVE == 2:
    ABS = ABS.replace('No confirmed carrier is found.',
                      'A transmitter in a circular orbit at 1 au is excluded.')
if DRIVE == 3:
    ABS = re.sub(r', on a step from the control positions[^.]*', '', ABS)
if DRIVE == 4:
    ABS = ABS.replace('and is measured to act in none', '')
if DRIVE == 5:
    ABS = re.sub(r'The injections carry no atmospheric[^.]*\.', '', ABS)
if DRIVE == 6:
    ABS = ABS.replace(r'$\EirpNinetySysMedA$\,W', 'a measured power')
if DRIVE == 7:
    ABS = re.sub(r'What limits the search[^.]*\.', '', ABS)

if len(ABS) < FLOOR:
    #: and this is not reachable by a drive: every drive above removes tens of
    #: characters from a paragraph of eighteen hundred.
    sys.exit('absreq_r17: the extracted paragraph is %d characters, below the '
             '%d floor -- the extraction has clipped and every verdict below '
             'would be meaningless' % (len(ABS), FLOOR))

# ------------------------------------------------------------------- B1 .. B7
ck('B1 the crossings whose repeats cannot test them are given as a count, '
   'with the amplitude the power is evaluated at (R1-2)',
   r'\RcNPowerLoTrig' in ABS and has(ABS, 'too shallow')
   and has(ABS, 'trigger amplitude'),
   'count %s; shallow %s; amplitude %s'
   % (MAC.get('RcNPowerLoTrig', 'MISSING'),
      has(ABS, 'too shallow'), has(ABS, 'trigger amplitude')))

_BANNED = ('1 au', 'frequency-stable', 'au orbit')
_back = [b for b in _BANNED if has(ABS, b)]
ck('B2 the plain negative result is stated and the trajectory family the '
   'test does not constrain is not reintroduced (R2-1)',
   has(ABS, 'no confirmed carrier') and not _back,
   'negative %s; reintroduced %s'
   % (has(ABS, 'no confirmed carrier'), _back or 'nothing'))

_chance = [s for s in sentences(ABS) if has(s, 'consistent with chance')]
ck('B3 the chance comparison is stated as a consistency and says what it does '
   'not exclude, in the sentence that states it (R1-4, R1-6)',
   len(_chance) == 1 and has(_chance[0], 'control positions')
   and has(_chance[0], 'does not exclude'),
   '%d chance sentence(s); qualification %s'
   % (len(_chance), has(_chance[0], 'does not exclude') if _chance else 'n/a'))

ck('B4 the calibration residual is admissible in a counted set of windows '
   'AND measured to act in none (R2-4.4, round 16)',
   r'\CxNAdmit' in ABS and has(ABS, 'could mimic')
   and has(ABS, r'measured to act in none|acts in none'),
   'admissible in %s window(s); not acting %s'
   % (MAC.get('CxNAdmit', 'MISSING'),
      has(ABS, r'measured to act in none|acts in none')))

_dec = [s for s in sentences(ABS) if has(s, 'decorrelation')]
ck('B5 the limits are said to exclude atmospheric decorrelation and to be '
   'optimistic by it (R2-8.4)',
   len(_dec) == 1 and has(_dec[0], 'optimistic'),
   '%d decorrelation sentence(s); optimistic %s'
   % (len(_dec), bool(_dec) and has(_dec[0], 'optimistic')))

_scale = [m for m in ('EirpNinetySysMedA', 'NWinA', 'NSysClassA', 'NWinB')
          if '\\%s' % m not in ABS]
ck('B6 the headline depth and the scale of both searches are set in type',
   not _scale, 'missing %s' % (_scale or 'nothing'))

ck('B7 what limits the search is coverage and not depth, with the systems '
   'that cannot be confirmed and line emission named (R2-5)',
   r'\ZcNoRepSys' in ABS and has(ABS, 'what limits the search')
   and has(ABS, 'not depth|rather than depth')
   and has(ABS, 'line emission'),
   'systems %s; coverage clause %s'
   % (MAC.get('ZcNoRepSys', 'MISSING'), has(ABS, 'what limits the search')))

print('absreq_r17: %d check(s), %d FAILED' % (7, len(FAIL)))
if FAIL:
    sys.exit('absreq_r17: FAILED %s' % FAIL)
if DRIVE:
    sys.exit('absreq_r17: DRIVE %d DID NOT FAIL -- the clause it exercises '
             'is vacuous' % DRIVE)
