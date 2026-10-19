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
        COUNT (\HjNPowerLo, the MEASURED count since v4.20), with "too
        shallow" and the amplitude the power is evaluated at, IN THE
        PARAGRAPH THAT QUANTIFIES THE EXCLUSION -- Sec. 5.5.  "None
        recurred" and "persistence excluded" are different statements and
        that paragraph must hold both.  The abstract half is now an
        implication: it may not quote the excluded count without the
        untestable one, which is the failure the clause exists to stop and
        the only part of it the abstract can still get wrong;
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
    B5  (v4.21, R2-1d; rewritten v4.24) the limits are said to exclude
        atmospheric decorrelation in ONE sentence, that sentence gives the
        DIRECTION of the omission, and it NAMES the comparable
        channel-response term that offsets it -- so the net bias is left
        unresolved by construction rather than by a missing word.  It used to
        require the word "optimistic", which R2-4's integrated-response
        measurement withdraws: the two signed terms run opposite ways, 7 per
        cent conservative in the median window against 21 per cent optimistic
        at the ninetieth percentile of the systems' own best windows.  A gate
        may not require a sentence the paper has retracted.  v4.21 then
        replaced that requirement with a BAN on "optimistic|conservative",
        which is a word list standing in for a proposition: R2-1(a) requires
        a direction for the omission and the abstract gives one in a third
        word the ban could not see, so the clause passed for the wrong
        reason, and it would have FAILED the identical meaning written in the
        banned vocabulary.  Keyed on what the sentence must contain.
    B5-old  the limits are said to exclude atmospheric decorrelation and to be
        optimistic by it, in one sentence;
    B6  the headline depth and the scale are present: \EirpNinetySysMedA,
        \NWinA, \NSysClassA and \NWinB;
    B7  what limits the search is coverage and not depth, with the systems
        that cannot be confirmed (\ZcNoRepSys, R2-1), and line emission named as
        the astrophysical false positive.

Usage: `python3 absreq_r17.py [--drive N]`, N in 1..9.  Nothing is written,
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


def section(fn):
    """A prose section, comments stripped, whitespace collapsed per paragraph.

    Returns the list of paragraphs, because a clause that requires two things
    to be said together needs a unit larger than a sentence and smaller than
    a file: `. ` splits a mechanism away from the number that disposes of it
    whenever the two are written as a statement and its measurement, which is
    how a careful author writes them.
    """
    t = open(os.path.join(SEC, fn)).read()
    t = re.sub(r'(?m)^\s*%.*$', '', t)
    t = re.sub(r'(?<!\\)%.*$', '', t, flags=re.M)
    return [' '.join(p.split()) for p in re.split(r'\n\s*\n', t)
            if p.strip()]


#: ★★★★ EVERY DRIVE BELOW MUST LAND, AND THREE OF THEM HAD STOPPED LANDING.
#: `re.sub` and `str.replace` return the string unchanged when they match
#: nothing, so a drive whose quoted wording the paragraph has moved past
#: perturbs NOTHING, the clause passes, and the harness reports the clause
#: VACUOUS when in fact the drive was.  Round 22's abstract rewrite expired
#: drives 1, 3 and 4 at a stroke -- "for \HjNPowerLo" became "while
#: \HjNPowerLo", "and does not exclude" became "which does not exclude", and
#: \CyEpsMinPct left the paragraph altogether.  Each of those would have been
#: a silent loss of a demonstration, which is the same species as the gates
#: this build keeps finding that cannot fail.  `cut()` makes a drive that
#: does not perturb an ERROR rather than a pass.
def cut(text, pattern, repl=''):
    out, n = re.subn(pattern, repl, text)
    if not n:
        sys.exit('absreq_r17: DRIVE %s did not perturb anything -- the '
                 'pattern %r matches nothing in the text it was written '
                 'against, so the clause it exercises would have been '
                 'reported vacuous when the DRIVE is what expired. '
                 'Re-point the drive in the same edit that moves the '
                 'sentence.' % (DRIVE, pattern))
    return out


ABS = body()
MAC = macros()
RESPARA = section('05_results.tex')
#: the paragraph of Sec. 5.3 that disposes of the calibration mechanism.
CALPARA = [p for p in RESPARA if r'\CyEpsMinPct' in p]
#: the paragraphs of Sec. 5.5 that quantify the recurrence exclusion -- where
#: B1's count moved to when the abstract stopped quoting it.
SHALLOW = [p for p in RESPARA
           if r'\HjNPowerLo' in p or 'too shallow' in p
           or 'trigger amplitude' in p]

#: the drives.  Each is the smallest perturbation that removes exactly one
#: qualification, written the way a character-budget edit would make it.
if DRIVE == 1:
    #: the conflation the correction exists to prevent: the count becomes the
    #: single event, which is how it was written before.
    #: ★ RE-POINTED (r22-main): the clause reads "while \HjNPowerLo repeats
    #: are too shallow..." now, so the old "for \HjNPowerLo" pattern matched
    #: nothing and this drive had expired.  Keyed on the macro B1 itself
    #: names, which cannot drift without the check drifting with it.
    #: ★★★★ RE-POINTED.  B1's content is no longer in the abstract: the
    #: quantified exclusion left the paragraph when its model turned out to be
    #: misdescribed there, and the count now lives where the exclusion is
    #: measured.  So drive 1 perturbs SEC. 5.5, which is what B1 reads, and
    #: drive 8 below perturbs the abstract half.
    SHALLOW = [cut(q, r'\\HjNPowerLo', 'some')
               if r'\HjNPowerLo' in q else q for q in SHALLOW]
if DRIVE == 2:
    ABS = ABS.replace('No confirmed carrier is found.',
                      'A transmitter in a circular orbit at 1 au is excluded.')
if DRIVE == 3:
    #: ★ RE-POINTED, v4.20: this drive quoted ", on a step from the control
    #: positions ...", and that clause was rewritten when the chance
    #: comparison became a probability rather than a step, so the drive
    #: stopped perturbing anything and B3 went undemonstrated.  It now removes
    #: the qualification B3 exists to protect.
    #: ★ RE-POINTED (r19): the qualification is now named against the
    #: measured limit ("up to 17 added events"), so a literal match on the
    #: old wording would stop perturbing anything.  Keyed on the clause this
    #: check requires rather than on the words it happens to use.
    #: ★ RE-POINTED AGAIN (r22-main): "and does not exclude" became "which
    #: does not exclude" in the shortened paragraph, so the conjunction was
    #: doing the matching and the drive expired.  Keyed on the three words
    #: B3 itself requires and on nothing else.
    ABS = cut(ABS, r'(,\s*)?(?:which|and) does not exclude[^.]*', '')
if DRIVE == 4:
    #: ★ RE-POINTED WITH B4 A SECOND TIME, AND THE TARGET MOVED FILE.  The
    #: clause left the abstract on Referee 1's instruction 13 (remove
    #: "secondary calibration diagnostics"), so B4 now reads Sec. 5.3, where
    #: the disposition is made in full, and the drive removes the quantity
    #: there.  Keyed on the macro the check itself names.
    CALPARA = [cut(p, r'\\CyEpsMinPct', 'a large fraction') for p in CALPARA]
if DRIVE == 5:
    #: ★ RE-POINTED TWICE, and the second time says something.  v4.20 keyed it
    #: on "carry no atmospheric" because the sentence had been reworded once;
    #: v4.21 rewords it again, to "These limits exclude atmospheric
    #: decorrelation and the net bias is of either sign by window" (R2-1d), and
    #: the v4.20 pattern matched nothing, so the drive passed and reported its
    #: own clause vacuous.  ★ A DRIVE KEYED ON A FORM OF WORDS IS A DRIVE THAT
    #: EXPIRES.  Keyed now on the one word B5 itself requires, which cannot
    #: drift without the check drifting with it.
    ABS = re.sub(r'[^.]*decorrelation[^.]*\.', '', ABS)
if DRIVE == 6:
    ABS = ABS.replace(r'$\EirpNinetySysMedA$\,W', 'a measured power')
if DRIVE == 7:
    ABS = re.sub(r'What limits the search[^.]*\.', '', ABS)
if DRIVE == 8:
    #: the abstract quotes the excluded count and not the untestable one,
    #: which is the half of B1 that still belongs to the abstract.
    ABS = ABS.replace('not a persistent transmitter of any kind',
                      r'not a persistent transmitter of any kind, for '
                      r'\HjNPowerHi{} of them')
if DRIVE == 9:
    #: ★ v4.24, for the HALF OF B5 THAT IS NEW: keep the decorrelation
    #: sentence and its direction, and delete only the offsetting term -- the
    #: edit a length pass makes, and the one that turns a two-sided
    #: disclosure into a one-signed claim.  Keyed on the term B5 requires, so
    #: it cannot expire without the check expiring with it.
    ABS = cut(ABS, r',?\s*offset by a comparable channel.{0,3}response term')

if len(ABS) < FLOOR:
    #: and this is not reachable by a drive: every drive above removes tens of
    #: characters from a paragraph of eighteen hundred.
    sys.exit('absreq_r17: the extracted paragraph is %d characters, below the '
             '%d floor -- the extraction has clipped and every verdict below '
             'would be meaningless' % (len(ABS), FLOOR))

# ------------------------------------------------------------------- B1 .. B7
#: *** B1 USED TO READ THE ABSTRACT, AND IT WAS PINNING A SENTENCE THE PAPER
#: HAS SINCE WITHDRAWN FROM THERE.  The clause exists because "none recurred"
#: and "persistence excluded" are different statements, so a quantified
#: exclusion may never be printed without the count whose repeats are too
#: shallow to support one.  That is an invariant about the paragraph which
#: QUANTIFIES the exclusion, and that paragraph is now Sec. 5.5 and not the
#: abstract: 25 of 33 could not be reconciled there with the other counts in
#: the same paragraph, and the abstract keeps the non-recurrence result with
#: its model and without its arithmetic.
#: So B1 is in two halves.  The first reads Sec. 5.5, where the numbers are.
#: The second is the only part that still concerns the abstract, and is the
#: part that would actually go wrong: if the excluded count is ever put back
#: there, the untestable count must come back with it.  It is an implication
#: and not a presence test, so it holds while neither is present and fails
#: the moment one returns alone -- which is what drive 8 does.
_b1sec = (any(r'\HjNPowerLo' in q for q in SHALLOW)
          and any(has(q, 'too shallow') for q in SHALLOW)
          and any(has(q, 'trigger amplitude') for q in SHALLOW))
_b1abs = (r'\HjNPowerLo' in ABS) or (r'\HjNPowerHi' not in ABS)
ck('B1 the crossings whose repeats cannot test them are given as a count '
   'where the exclusion is quantified, with the amplitude the power is '
   'evaluated at, and the abstract never quotes the excluded count without '
   'it (R1-2)',
   _b1sec and _b1abs,
   'count %s; in Sec. 5.5 %s (%d paragraph(s)); abstract implication %s'
   % (MAC.get('HjNPowerLo', 'MISSING'), _b1sec, len(SHALLOW), _b1abs))

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

#: ★★★★ B4 USED TO PIN AN OUTCOME AND A FORM OF WORDS AT ONCE.  It required
#: the abstract to contain `\CxNAdmit` together with "could mimic" and
#: "measured to act in none" -- that is, it required the abstract to SAY that
#: the mechanism is admissible in a counted set of windows.  A gate framed
#: that way cannot survive the measurement falling the other way: where no
#: window admits, the only abstract that passes is one that misreports the
#: census, and the gate has become a defence of the statement it was written
#: to protect.
#: What the abstract owes a reader is not a verdict but a QUANTIFIED
#: disposition: the mechanism named, and the size a residual would have to
#: reach set in type from the macro that carries it.  That requirement is the
#: same whichever way the number falls, so it is the invariant and the
#: verdict is not.  ★ Keyed on the macro AND on the mechanism being named in
#: the same sentence as the number, so neither half can be dropped quietly.
#: ★★★★ AND v4.23 MOVES IT OUT OF THE ABSTRACT, WHICH IS THE THIRD TIME THIS
#: CLAUSE HAS HAD TO FOLLOW THE PAPER RATHER THAN HOLD IT STILL.  Referee 1's
#: instruction 13 asks for "detailed velocity tolerances, individual
#: recurrence statistics and secondary calibration diagnostics" to leave the
#: abstract, and this is exactly a secondary calibration diagnostic; Referee
#: 2 separately showed the old wording overstated what the appendix supports.
#: So the statement moved to Sec. 5.3, beside the chance comparison it
#: qualifies, where it is made in full.
#: ►► THE REQUIREMENT MOVED WITH IT AND WAS NOT RETIRED.  That is the whole
#: point: a qualification deleted under a budget is what this file exists to
#: prevent, and a qualification RELOCATED is a different act only if the
#: check follows it.  What is lost is the abstract-specific protection, and
#: that loss is deliberate, instructed and recorded in MAIN_REPORT_R22.md --
#: not silent, which is the only form of it that matters.
#: ★ The unit is the PARAGRAPH and not the sentence.  Sec. 5.3 names the
#: mechanism in one sentence ("a calibration error that varied with
#: frequency would raise the star and not them") and disposes of it with the
#: number in the next, which is how the statement should be written; a
#: sentence-scoped check would have forced the prose to be worse to satisfy
#: the gate.
_calok = bool(CALPARA) and all((r'\CyEpsMinPct' in p) for p in CALPARA[:1])
_calnamed = bool(CALPARA) and has(CALPARA[0], 'calibration')
_caldisp = bool(CALPARA) and has(CALPARA[0],
                                 'could reach the trigger|would need|needs')
ck('B4 the calibration residual is disposed of quantitatively where the '
   'chance comparison is made: in Sec. 5.3 the mechanism is named and the '
   'residual a window would have to carry is in type from its own macro, in '
   'the same paragraph (R2-4.4 round 16; R2-10 round 21; relocated out of '
   'the abstract on R1-13, round 22)',
   _calok and _calnamed and _caldisp,
   'least demanding window needs %s per cent; %d paragraph(s) of '
   '05_results.tex carry the macro; mechanism named %s; disposed %s'
   % (MAC.get('CyEpsMinPct', 'MISSING'), len(CALPARA), _calnamed, _caldisp))

_dec = [s for s in sentences(ABS) if has(s, 'decorrelation')]
#: ★★★ v4.24: B5 IS KEYED ON WHAT THE SENTENCE MUST CONTAIN, NOT ON TWO
#: BANNED WORDS.  It used to pass iff the abstract nowhere said "optimistic"
#: or "conservative", which is a word list standing in for a proposition, and
#: it was passing for the wrong reason: R2-1(a) REQUIRES a direction for the
#: omission ("making them underestimates"), and the sentence makes that claim
#: with a third word the ban could not see.  Worse, the clause would have
#: FAILED a correct sentence that said "optimistic by it, offset by a
#: comparable channel-response term" -- the identical meaning in the banned
#: vocabulary.  The proposition R2-1(a) and R2-4 together require is: the
#: omission is one-signed, AND a term of comparable size runs the other way,
#: so the NET is left unresolved.  That is now checked by requiring the
#: offsetting term to be NAMED in the same sentence.  A ban on a word is not a
#: check on a claim -- the same mistake as B5-old's requirement that the word
#: "optimistic" APPEAR, with the sign reversed.
_decoffset = bool(_dec) and has(_dec[0], 'channel.{0,3}response')
_decdir = bool(_dec) and has(_dec[0],
                             'underestimate|optimistic|lower bound')
ck('B5 the limits are said to exclude atmospheric decorrelation, in one '
   'sentence, which gives the direction of that omission and names the '
   'comparable channel-response term offsetting it, so no NET direction is '
   'claimed (R2-8.4, restated at R2-1d, with R2-1a and R2-4)',
   len(_dec) == 1 and _decoffset and _decdir,
   '%d decorrelation sentence(s); direction of the omission given: %s; '
   'offsetting channel-response term named in the same sentence: %s'
   % (len(_dec), _decdir, _decoffset))

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
