#!/usr/bin/env python3
r"""round 200 -> survey_numbers_round200.tex: the two quantities the abstract
and the conclusions need and no other generator publishes, plus the gates
that keep the front matter honest.

WHAT IT PUBLISHES

(1) \PrSysClassB -- the number of stellar systems carrying at least one
    Class B window.  R1-7 requires that wherever a headline sample size
    appears, the Class A experiment be given first and the supplementary
    Class B search second, each with its own counts.  The paper publishes
    \NWinA, \NWinB and \NSysClassA, and has never published the Class B
    system count, so conclusion 2 could not obey R1-7 without typing it.
    Measured here from the released catalogue on `system_id`, which is the
    key \NSysClassA is measured on; `star_name` gives 88, and the difference
    is the multiple systems -- this project's commonest defect wearing its
    usual clothes, so both are computed and the wrong one is used only to
    drive the check.

(2) \PrConfFactor -- the ENGLISH WORD for the ratio of the searched union
    bandwidth to the union over which an independent repeat exists, so that
    the abstract's "about twice the extent over which a persistent carrier
    could have been confirmed" is generated and not asserted.  \CvUnionA
    and \CvConfGHzDay are owned by round 185; if either moves, the word
    follows or P3 fails.  A sentence whose adverb is typed is a sentence
    that goes quietly wrong.

(3) \PrRankClause -- the whole sub-clause the abstract uses for the
    crossings that lead their own control fields, grammar included.  The
    count has been both one and two in the course of this analysis, so a
    typed "the two ... their own fields" goes wrong as soon as one of them
    turns out to sit near a catalogued transition after all, while a bare
    macro in its place typesets "1 unattributed crossing".  The clause is
    therefore emitted where the size of the set is known, the way
    \ProjCodeUnresClause and \HostActiveClause already are.

WHAT IT GATES

The four files of the front matter -- abstract, introduction, conclusions,
backmatter -- are the only ones a referee and most readers see in full, and
every existing gate in this build compares strings or numbers.  None reads
English.  So:

    P4  the abstract must say what class of transmitter non-recurrence
        excludes, and must not claim a generic one.  A single cell at a
        predicted stellar-frame frequency tests a carrier that holds that
        frequency and radiates at both epochs; a transmitter on an
        accelerating platform need not, which is the whole reason the
        search allows drift in the first place.  So the abstract must carry
        the operational clause, and the word "persistent" may appear in it
        only inside the denial.  The spatial rank may be named -- the
        crossings that lead their own control fields are named in the
        sentence saying they did not return -- but ONLY as an appositive of
        the non-recurrence statement, never as a result of its own, because
        the rank still gates no disposition;
    P9  the crossing total may never appear in the front matter without the
        subset arising in the block that fails the quality criterion, and
        the pooled \NCross must not appear in these four files at all: that
        pooling is the defect, and a gate that only checked the abstract
        would let the conclusions pool them instead;
    P10 the chance comparison must be stated as a CONSISTENCY and must not
        carry a floor.  The expectation is measured from the control
        positions, not from a Poisson model, so its honest interval is set
        by how well those positions stand in for the star; a floor derived
        from a Poisson scatter is the flattering figure and is withdrawn,
        and this check now refuses it rather than requiring it;
    P8c no macro whose value is English may be the FIRST TOKEN of a
        sentence in these four files.  A generated word is lower case by
        construction, so a sentence that opens on one typesets a
        misspelling that every other gate here passes: the value is right,
        the macro is right, and only the capital is missing.  It happened
        twice in one round -- `\MkNSODecideWord` in conclusion 4 and
        `\PrFlagXrossWord` in the abstract -- and the second was found by
        this check rather than by reading;
    P11 the Acknowledgements must not list the proposal codes, and the
        sentence that replaces the list must point at the release.  ALMA's
        data-use policy needs the codes traceable; it does not need
        \NProjCodes of them set in type;
    P5  no reference to versions, revisions, referees or earlier text, and
        no "candidate" except inside Referee 1's own required phrase
        "candidate classification", which is about classifying events and
        not a level of the chain (R2-M10.3);
    P6  no typed number in the abstract or the introduction.  Scope is
        deliberately those two files: the backmatter legitimately carries
        dates, commit hashes and software versions, and a gate that had to
        whitelist all of those would whitelist anything.  The allow-list is
        the two definitional constants of the survey, 40 pc and 30 GHz,
        both of which appear in the title or in the sample definition;
    P7  the abstract must label its headline bandwidth "union bandwidth"
        (R2-M6), because the defect there was the label and not the macro.

Rule 9: every check is driven to fail on purpose; `--drive N` writes
survey_numbers_round200_driveN.tex and never a production path, including
`--drive 0`, which perturbs nothing.
"""
import csv
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROUND = 200

DRIVE = None
for _i, _a in enumerate(sys.argv):
    if _a == '--drive':
        DRIVE = int(sys.argv[_i + 1])
SUF = '' if DRIVE is None else '_drive%d' % DRIVE

#: written as a literal so that `roundcollide` and `macrosyn` can both see
#: which round this generator claims.  A template-built name is invisible to
#: the second of those.
OUT_NAME = 'survey_numbers_round200%s.tex' % SUF
OUT_PATH = os.path.join(HERE, OUT_NAME)

MINE = ('abstract.tex', '01_intro.tex', '07_conclusions.tex',
        '08_backmatter.tex')
#: P6's scope and its allow-list.  See the module docstring.
NUMSCOPE = ('abstract.tex', '01_intro.tex')
NUMOK = {'40', '30'}

#: P5.  Tokens that cannot be innocent in a paper presented as new work.
#: "version" alone is not here: the Software section properly records exact
#: software versions, and a gate that forbade the word would be wrong.
BADVOICE = ('referee', 'revision', 'revised', 'we now', 'as corrected',
            'it should be noted', 'previously', 'earlier version',
            'this version', 'in the previous', 'updated version')
#: the one permitted occurrence of the word the chain no longer uses.
CANDOK = 'candidate classification'

OUT, fail = [], []


def m(name, val):
    assert name.isalpha(), (
        'a LaTeX macro name may contain letters only: %r' % name)
    assert not any(x.startswith('\\newcommand{\\%s}' % name) for x in OUT), name
    OUT.append('\\newcommand{\\%s}{%s}' % (name, val))


def ck(label, cond, detail=''):
    print('  %-70s %s  %s' % (label, 'PASS' if cond else 'FAIL', detail))
    if not cond:
        fail.append(label)


def texval(name):
    """Read a macro out of the published macro layer; last definition wins."""
    pat = re.compile(r'\\(?:provide|renew|new)command\{?\\%s\}?\{([^}]*)\}'
                     % name)
    got = None
    for f in sorted(os.listdir(HERE)):
        if not (f.startswith('survey_numbers') and f.endswith('.tex')):
            continue
        if f.endswith('_drive%s.tex' % (DRIVE,)) if DRIVE is not None else False:
            continue
        if re.search(r'_drive\d+\.tex$', f):
            continue             # never read a driven product, ours or anyone's
        if f == 'survey_numbers_round%d.tex' % ROUND:
            continue             # never read our own previous output
        for mm in pat.finditer(open(os.path.join(HERE, f),
                                    errors='ignore').read()):
            if mm.group(1).strip():
                got = mm.group(1).strip()
    return got


def prose(fname):
    """One of my section files as the typeset paragraph roughly sees it:
    comments gone, and the bodies of the commands that carry identifiers
    rather than prose gone with them."""
    t = open(os.path.join(HERE, 'sections', fname), errors='ignore').read()
    t = re.sub(r'(?m)^\s*%.*$', '', t)
    t = re.sub(r'(?<!\\)%.*$', '', t, flags=re.M)
    #: ONE SPACE.  Every string test below is a test on the typeset
    #: paragraph, and the source wraps: "the pre-defined\nindependent-"
    #: and "For candidate\nclassification" both read as two words on the
    #: page and as something with a newline in it in the file.  A gate that
    #: searched the raw source would pass P4 and P5 by accident, which is
    #: exactly the class of silent pass this generator exists to prevent.
    return ' '.join(t.split())


def stripped(t):
    """`prose` with citations, labels, refs, identifiers and maths removed,
    which is what P6 may legitimately look for digits in."""
    t = re.sub(r'\\(?:cite[a-zA-Z]*|ref|label|input|texttt|url)\s*'
               r'(?:\[[^\]]*\])*\{[^}]*\}', ' ', t)
    t = re.sub(r'\$[^$]*\$', ' ', t)
    #: an ALMA band number is a name, not a measurement: "Band~3" is no
    #: more a typed quantity than "CO(3-2)" is.  Nothing else in these two
    #: files may carry a digit.
    t = re.sub(r'Band~?\d+', ' ', t)
    return t


# ------------------------------------------------------------- the catalogue
CAT = list(csv.DictReader(open(os.path.join(
    HERE, 'per_target_results_v3.99.csv'))))
A = [r for r in CAT if r['search_class'] == 'A']
B = [r for r in CAT if r['search_class'] == 'B']
if DRIVE == 1:
    #: P1 only.  Dropping ALL of class B would also break P2, and a drive
    #: that fires two checks does not demonstrate either of them: one row
    #: is enough to stop the partition closing and leaves every system in
    #: place.
    B = B[1:]


def syst(rows):
    return len({r['system_id'] for r in rows})


SYS_B = syst(B)
SYS_B_BYNAME = len({r['star_name'] for r in B})
if DRIVE == 2:
    SYS_B = SYS_B_BYNAME                    # P2: the star-blind key again

# -------------------------------------------------------- the two bandwidths
UNION_A = float(texval('CvUnionA'))
CONF_A = float(texval('CvConfGHzDay'))
if DRIVE == 3:
    UNION_A = UNION_A * 3.0                 # P3: the word stops being true
RATIO = UNION_A / CONF_A
WORD = {2: 'twice', 3: 'three times', 4: 'four times'}.get(int(round(RATIO)))

# ------------------------------------------------- small counts, as words
#: A sentence that begins "2 of the 36 are brighter..." is a sentence no
#: astronomer would write, and the only reason this paper wrote it is that
#: the quantity is a macro and the macro holds a numeral.  So the WORD is
#: generated from the number, the way round 175 generates \BqFactor, and
#: P8 holds the two together.  Typing "two" beside a macro that says 2
#: would be the same defect as typing the 2.
WORDS = {0: 'no', 1: 'one', 2: 'two', 3: 'three', 4: 'four', 5: 'five',
         6: 'six', 7: 'seven', 8: 'eight', 9: 'nine', 10: 'ten'}
RANK_N = int(texval('NUnattrRankFlagged'))
FLAG_N = int(texval('BqFailNCross'))
#: the coincidences the paper reports and does not act on.  Conclusion 4
#: opens a clause on this count and needs the word, not the numeral -- and
#: round 330 ALREADY EMITS IT as \MkNSODecideWord.  A second name for it
#: here would be this project's commonest defect wearing a new coat, so it
#: is read back and checked rather than re-derived.
SO_N = int(texval('MkNSODecide'))
RANK_W = WORDS.get(RANK_N)
FLAG_W = WORDS.get(FLAG_N)
SO_W = texval('MkNSODecideWord')
if DRIVE == 8:
    RANK_W = WORDS[RANK_N + 1]              # P8: the word stops matching
if DRIVE == 14:
    SO_W = WORDS[SO_N + 1]                  # P8: round 330's word disagrees

#: ...and the clause, grammar and all.  See docstring (3).  The number is
#: never set in type here either: the singular branch says "the one", so
#: the clause reads as English for a set of one, of two or of none.
#: The size of the control ring was named inside this clause until the
#: abstract was cut to six quantities.  It is a property of the method, it
#: is stated in S4.1 beside the statistic it belongs to and again in S5.4,
#: and the clause reads as English without it; the wording here is now the
#: one S5.4's own heading uses, so the abstract and that section name one
#: thing one way.
RANK_SINGULAR = r'the one that leads its own control field'
RANK_PLURAL = r'the \PrRankWord{} that lead their own control fields'
RANK_NONE = r'no crossing that leads its own control field'
BRANCH = {0: RANK_NONE}.get(RANK_N,
                            RANK_SINGULAR if RANK_N == 1 else RANK_PLURAL)
if DRIVE == 9:
    #: P8b: emit the clause written for the OTHER set size, which is how
    #: "2 unattributed crossing" and "the one ... their own fields" both
    #: reached a page in this project.
    BRANCH = RANK_PLURAL if BRANCH is RANK_SINGULAR else RANK_SINGULAR
RANK_CLAUSE = BRANCH

# ------------------------------------------------------------- the four files
TEXT = {f: prose(f) for f in MINE}


def perturb(fname, pattern, repl, want=1):
    r"""Apply a drive's perturbation to one of my files AND REQUIRE IT TO
    LAND.  Every one of the prose drives below rewrites a quoted phrase, and
    a quoted phrase is a hostage to the next edit of the sentence: drive 12
    was already rewritten once for exactly this reason, and the other four
    were still literal `str.replace` calls, which return the string
    unchanged and raise nothing when the sentence has moved on.  A drive
    that silently stops perturbing leaves a gate that is never known to
    work, and this generator exists to stop that class of failure in the
    prose rather than create it in its own harness.  `pattern` is a regex;
    the substitution count must be exactly `want`."""
    new, n = re.subn(pattern, repl.replace('\\', '\\\\'), TEXT[fname])
    assert n == want, (
        'drive %s made %d of %d substitutions in %s, so it is not driving '
        'its check any more -- the sentence it quotes has been reworded'
        % (DRIVE, n, want, fname))
    TEXT[fname] = new


if DRIVE == 4:
    #: P4: the operational clause goes and the generic claim replaces it,
    #: which is the sentence both referees objected to.
    perturb('abstract.tex',
            r'That excludes a carrier holding its frequency inside the '
            r'window searched and radiating through both observations, not '
            r'a persistent transmitter of any kind;',
            'That excludes a persistent transmitter;')
if DRIVE == 5:
    TEXT['01_intro.tex'] += ' We now report the revised search.'
if DRIVE == 6:
    NUMOK = set()                           # P6: the allow-list is the check
if DRIVE == 7:
    perturb('abstract.tex', r'union bandwidth', 'sky frequency')
if DRIVE == 10:
    #: P4c: the rank is promoted to a result of its own, detached from the
    #: statement that it did not return.
    #: the clause stays mid-sentence, so this drive fires P4 and P4 alone;
    #: a perturbation that also puts a lower-case word at a sentence start
    #: would fire P8c with it and demonstrate neither cleanly.
    perturb('abstract.tex',
            r'none returned, including \\PrRankClause\.',
            r'none returned. Two crossings stand out, \PrRankClause{} '
            r'among them.')
if DRIVE == 11:
    #: P9: the crossing total pooled, which is R1-5's objection exactly.
    perturb('abstract.tex',
            r'Of the \\EvNCrossRaw\{\} threshold crossings, '
            r'\\PrFlagXrossWord\{\} arise in one execution block that fails '
            r'a quality criterion fixed in advance, and',
            r'Of the \NCross{} threshold crossings, and')
if DRIVE == 12:
    #: P10: the withdrawn population floor put back, which is the sentence
    #: both referees objected to and the one Ruling 1 deleted.  Written as a
    #: pattern because the first version of this drive quoted a sentence
    #: verbatim and stopped firing the moment the sentence was reworded.
    perturb('abstract.tex',
            r'the remainder is consistent with chance, to the accuracy '
            r'with which control positions stand in for the star',
            r'the remainder is no more numerous than chance predicts, a '
            r'comparison that could not see a population below about '
            r'\StFloor{} events')
if DRIVE == 13:
    #: P11: the proposal-code list back in the Acknowledgements.
    perturb('08_backmatter.tex',
            r'are recorded block by block in the data release',
            r'are: \input{tab_projcodes_v400}')

ABS = TEXT['abstract.tex']
ACK = TEXT['08_backmatter.tex']

# ------------------------------------------------------------------ P1 .. P7
ck('P1 the two search classes partition the released catalogue',
   len(A) + len(B) == len(CAT) == int(texval('NWindows'))
   and len(A) == int(texval('NWinA')) and len(B) == int(texval('NWinB')),
   '%d A + %d B = %d' % (len(A), len(B), len(CAT)))

ck('P2 the system counts are keyed on system_id and nest in \\NSystems',
   syst(A) == int(texval('NSysClassA'))
   and SYS_B == syst(B)
   and syst(CAT) == int(texval('NSystems'))
   and int(texval('NSysClassA')) < SYS_B < syst(CAT),
   'A %d, B %d (by name %d), all %d'
   % (syst(A), SYS_B, SYS_B_BYNAME, syst(CAT)))

ck('P3 \\PrConfFactor is the word for \\CvUnionA/\\CvConfGHzDay',
   WORD is not None and 1.5 <= RATIO < 2.5 and WORD == 'twice',
   '%.3f/%.3f = %.2f -> %r' % (UNION_A, CONF_A, RATIO, WORD))

#: P4.  Three clauses, and the third is the one that keeps the rank in its
#: place: `\PrRankClause` may appear only inside the sentence that says
#: nothing returned, never as a finding of its own.
_P4OP = ('holding its frequency inside the window searched', 'both observations')
#: the SENTENCE the rank clause sits in, not a window of characters around
#: it: a window ending at the clause happily spans a full stop, so the first
#: version of this check passed its own drive.
_P4sent = [s for s in ABS.split('. ') if r'\PrRankClause' in s]
_P4sub = bool(_P4sent) and any(w in _P4sent[0]
                               for w in ('returned', 'recur', 'present again'))
ck('P4 the abstract says what non-recurrence excludes, claims no generic '
   'transmitter, and keeps the rank subordinate to it',
   all(w in ABS for w in _P4OP)
   and 'not a persistent transmitter of any kind' in ABS
   and ABS.count('persistent') == 1
   and len(_P4sent) == 1 and _P4sub,
   'operational %s; persistent x%d; rank clause %s'
   % ([w for w in _P4OP if w not in ABS] or 'present',
      ABS.count('persistent'),
      'subordinate' if _P4sub else 'LOOSE'))

_voice = sorted({(f, b) for f in MINE for b in BADVOICE
                 if b in TEXT[f].lower()})
_cand = sorted({(f, TEXT[f].lower().count('candidate'))
                for f in MINE
                if TEXT[f].lower().count('candidate')
                != TEXT[f].lower().count(CANDOK)})
ck('P5 no version, revision, referee or stray "candidate" in the front matter',
   not _voice and not _cand, '%s %s' % (_voice or '-', _cand or '-'))

_digits = []
for f in NUMSCOPE:
    for d in re.findall(r'\d+(?:\.\d+)?', stripped(TEXT[f])):
        if d not in NUMOK:
            _digits.append((f, d))
ck('P6 no typed number in the abstract or the introduction',
   not _digits, '%s (allowed %s)'
   % (sorted(set(_digits)) or 'none', sorted(NUMOK) or 'nothing'))

ck('P7 the abstract labels its headline bandwidth "union bandwidth"',
   'union bandwidth' in ABS)

ck('P8 the spelled-out counts are the English of the macros they stand for',
   RANK_W == WORDS.get(RANK_N) and FLAG_W == WORDS.get(FLAG_N)
   and SO_W == WORDS.get(SO_N)
   and None not in (RANK_W, FLAG_W, SO_W)
   and not any(x.startswith('\\newcommand{\\PrSOWord}') for x in OUT)
   and FLAG_N == int(texval('EvNCrossFlag')),
   '%s=%r %s=%r %s=%r (EvNCrossFlag %s)'
   % (RANK_N, RANK_W, FLAG_N, FLAG_W, SO_N, SO_W, texval('EvNCrossFlag')))

#: P8c.  THE DEFECT THIS CLAUSE EXISTS FOR REACHED A PAGE IN THIS ROUND,
#: TWICE, AND THE CHECK FOUND THE SECOND ONE.  Conclusion 4 opened a
#: sentence with \MkNSODecideWord and the page read "... and 34 do not.
#: three of the unattributed coincide with sulphur monoxide"; the abstract
#: then did the same with \PrFlagXrossWord.  No gate here could see either:
#: the value is right, the macro is right, the sentence parses, and only the
#: capital is missing.  A macro whose value is English is lower case by
#: construction -- it is written to sit mid-sentence -- so the rule is that
#: it may never be the first token of one.  The check is made over EVERY
#: macro these four files cite, with its value read out of the macro layer,
#: so it covers the word macros other generators own as well as mine and
#: covers a new one the moment a sentence cites it.
#: `texval` deliberately never reads this generator's own round file, so
#: the four macros it emits are invisible to it -- and three of them ARE the
#: lower-case words this check is about.  The first version of the check
#: looked only at those four; the second looked only at the macro layer and
#: so covered \MkNSODecideWord and lost all four of mine.  Both halves are
#: needed, and the in-memory value is the authority for anything emitted in
#: this run.
_OWNVALS = {'PrConfFactor': WORD, 'PrRankWord': RANK_W,
            'PrFlagXrossWord': FLAG_W, 'PrRankClause': RANK_CLAUSE,
            'PrSysClassB': '%d' % SYS_B}
_CITED = sorted({mm for f in MINE
                 for mm in re.findall(r'\\([A-Za-z]+)', TEXT[f])})
_LOWER = []
for _nm in _CITED:
    _v = _OWNVALS.get(_nm) or texval(_nm)
    if _v and _v[:1].isalpha() and _v[:1].islower():
        _LOWER.append(_nm)
#: and the coverage is asserted, because losing it is silent: every macro of
#: mine that IS a lower-case word and IS cited in these files must be in the
#: list the check searches for.  A macro a drive has deliberately made
#: unresolvable is exempt -- P3 and P8 are the checks for that -- and
#: \PrSysClassB is a count, not a word.
_OWNWORDS = {k for k, v in _OWNVALS.items()
             if v and v[:1].isalpha() and v[:1].islower()}
assert (_OWNWORDS & set(_CITED)) <= set(_LOWER), (
    'P8c lost sight of this generator\'s own word macros: %s'
    % sorted((_OWNWORDS & set(_CITED)) - set(_LOWER)))
_SENTSTART = re.compile(
    r'(?:(?<=[.!?])\s+|\A)\\(?:%s)\b' % '|'.join(_LOWER or ['never']))


def _sentence_initial():
    return sorted({(f, _SENTSTART.search(TEXT[f]).group(0).strip())
                   for f in MINE if _SENTSTART.search(TEXT[f])})


_opens = _sentence_initial()
if DRIVE == 15:
    #: the exact sentence that reached the page, put back.  A plain string
    #: swap, not a regex: `\MkNSODecideWord` begins `\M`, and `re` reads a
    #: backslash-letter it does not know as a bad escape and raises instead
    #: of driving -- which is how the first version of this drive failed.
    _bad = r'do not. Of the unattributed, \MkNSODecideWord{} coincide'
    assert _bad in TEXT['07_conclusions.tex'], 'drive 15 is not driving'
    TEXT['07_conclusions.tex'] = TEXT['07_conclusions.tex'].replace(
        _bad, r'do not. \MkNSODecideWord{} of the unattributed coincide')
    _opens = _sentence_initial()
ck('P8c no generated English word opens a sentence, where its lower case '
   'would be typeset as a misspelling',
   not _opens,
   '%d of the %d macros cited here expand to lower-case English; '
   'sentence-initial %s' % (len(_LOWER), len(_CITED), _opens or 'none'))

ck('P8b \\PrRankClause is written for the size of the set it describes',
   (RANK_CLAUSE is RANK_SINGULAR) == (RANK_N == 1)
   and (RANK_CLAUSE is RANK_NONE) == (RANK_N == 0)
   and ('their own control fields' in RANK_CLAUSE) == (RANK_N > 1),
   '%d -> %s' % (RANK_N, 'singular' if RANK_CLAUSE is RANK_SINGULAR
                 else 'none' if RANK_CLAUSE is RANK_NONE else 'plural'))

#: P9.  The pooled total is the defect R1-5 names, so it is banned from all
#: four files and not only from the abstract: the conclusions pooled it too.
_pooled = sorted(f for f in MINE if r'\NCross' in TEXT[f])
ck('P9 the crossing total always carries the flagged subset, and the pooled '
   'macro appears nowhere in the front matter',
   not _pooled
   and r'\EvNCrossRaw' in ABS
   and (r'\PrFlagXrossWord' in ABS or r'\EvNCrossFlag' in ABS)
   and 'fails a quality criterion' in ABS,
   'pooled in %s' % (_pooled or 'nothing'))

#: P10.  THIS CHECK HAS BEEN REVERSED, and the reason is worth recording.
#: It used to REQUIRE the abstract to name the size of population the chance
#: comparison could not have registered, on the ground that "no more
#: numerous than chance predicts" reads as a stronger statement than it is.
#: The qualification it required was `about \StFloor{} events`, derived from
#: the Poisson scatter of the expectation -- and the expectation is not a
#: Poisson one.  It is measured from the control positions, whose standing
#: in for the star is established to a few tens of per cent, so the honest
#: interval is several times the Poisson width and the floor was the
#: flattering figure.  The expectation is now measured with that interval
#: and the floor is withdrawn, so the abstract must state the comparison as
#: a CONSISTENCY, with the accuracy of the control positions as its limit,
#: and must not reintroduce a floor, a Poisson scatter or any second
#: construction of the same comparison.  The macros of the withdrawn
#: derivation are named here so that citing one of them again fails here
#: rather than on the page.
_WITHDRAWN = (r'\StFloor', r'\StPois', r'\StExpChance')
_revived = [x for x in _WITHDRAWN if x in ABS]
ck('P10 the chance comparison is stated as a consistency, bounded by the '
   'accuracy of the control positions, with no population floor',
   'consistent with chance' in ABS
   and 'control positions' in ABS
   and not _revived
   and not re.search(r'could not (?:see|have seen|register)', ABS)
   and 'Poisson' not in ABS,
   'withdrawn macros %s' % (_revived or 'absent'))

#: P11.  The list is gone; what must survive is the pointer, because the
#: policy is about traceability and not about typography.
ck('P11 the Acknowledgements point at the release for the proposal codes '
   'instead of listing them',
   'tab_projcodes' not in ACK
   and r'\NProjCodes' in ACK
   and 'data release' in ACK,
   'list %s; pointer %s'
   % ('present' if 'tab_projcodes' in ACK else 'gone',
      'present' if 'data release' in ACK else 'MISSING'))

# -------------------------------------------------------------------- output
m('PrSysClassB', '%d' % SYS_B)
#: SYS_B_BYNAME is deliberately NOT published.  It is the wrong answer, it
#: exists to drive P2, and an emitted macro that no sentence references is
#: exactly what `retire_macros.py` deletes -- which is how a typed 403 once
#: survived in this build with no gate able to see it.
m('PrConfFactor', WORD or 'UNRESOLVED')
m('PrRankWord', RANK_W or 'UNRESOLVED')
m('PrFlagXrossWord', FLAG_W or 'UNRESOLVED')
m('PrRankClause', RANK_CLAUSE)

HDR = ['%% GENERATED by prose_v412.py -- do not hand-edit.',
       '%% round ' + str(ROUND) + ': the Class B system count, the word '
       'the abstract uses',
       '%% for the ratio of the searched union to the confirmable one, and '
       'the clause',
       '%% it uses for the crossings that lead their own control fields.']
with open(OUT_PATH, 'w') as fh:
    fh.write('\n'.join(HDR + sorted(OUT)) + '\n')
print('\nwrote %s: %d macros' % (OUT_NAME, len(OUT)))
if fail:
    print('FAILED: %s' % '; '.join(fail))
    raise SystemExit(1)
