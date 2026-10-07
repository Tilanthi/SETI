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
        only inside the denial.  The spatial rank may now be named -- only
        one unattributed crossing leads its own control field and the
        sentence that names it is the sentence saying it did not return --
        but ONLY as an appositive of the non-recurrence statement, never as
        a result of its own, because the rank still gates no disposition;
    P9  the crossing total may never appear in the front matter without the
        subset arising in the block that fails the quality criterion, and
        the pooled \NCross must not appear in these four files at all: that
        pooling is the defect, and a gate that only checked the abstract
        would let the conclusions pool them instead;
    P10 the chance comparison must carry the size of population it could
        not have registered.  "No more numerous than chance predicts" over
        an expectation whose own scatter is several events is a true
        statement that reads as a stronger one;
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
RANK_W = WORDS.get(RANK_N)
FLAG_W = WORDS.get(FLAG_N)
if DRIVE == 8:
    RANK_W = WORDS[RANK_N + 1]              # P8: the word stops matching

#: ...and the clause, grammar and all.  See docstring (3).  The number is
#: never set in type here either: the singular branch says "the one", so
#: the clause reads as English for a set of one, of two or of none, and
#: `\NCtrl` is the macro the rest of the paper uses for the ring size.
RANK_SINGULAR = (r'the one ahead of all \NCtrl{} control positions of '
                 r'its own field')
RANK_PLURAL = (r'the \PrRankWord{} ahead of all \NCtrl{} control '
               r'positions of their own fields')
RANK_NONE = (r'no crossing that leads all \NCtrl{} control positions of '
             r'its own field')
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
if DRIVE == 4:
    #: P4: the operational clause goes and the generic claim replaces it,
    #: which is the sentence both referees objected to.
    TEXT['abstract.tex'] = TEXT['abstract.tex'].replace(
        'That excludes a carrier holding its frequency inside the window '
        'searched and radiating through both observations, not a persistent '
        'transmitter of any kind.',
        'That excludes a persistent transmitter.')
if DRIVE == 5:
    TEXT['01_intro.tex'] += ' We now report the revised search.'
if DRIVE == 6:
    NUMOK = set()                           # P6: the allow-list is the check
if DRIVE == 7:
    TEXT['abstract.tex'] = TEXT['abstract.tex'].replace(
        'union bandwidth', 'sky frequency')
if DRIVE == 10:
    #: P4c: the rank is promoted to a result of its own, detached from the
    #: statement that it did not return.
    TEXT['abstract.tex'] = TEXT['abstract.tex'].replace(
        r'none returned, including \PrRankClause.',
        r'none returned. \PrRankClause{} leads its own control field.')
if DRIVE == 11:
    #: P9: the crossing total pooled, which is R1-5's objection exactly.
    TEXT['abstract.tex'] = TEXT['abstract.tex'].replace(
        r'Of \EvNCrossRaw{} threshold crossings, \PrFlagXrossWord{} arise '
        r'in one execution block that fails a quality criterion fixed in '
        r'advance; of the rest,',
        r'Of \NCross{} threshold crossings,')
if DRIVE == 12:
    #: P10: the chance comparison stated without what it could not see.
    #: Written as a pattern and not as a literal, because the first version
    #: of this drive quoted the sentence verbatim and stopped firing the
    #: moment the sentence was reworded -- a drive that silently stops
    #: driving leaves a gate that is never known to work.
    TEXT['abstract.tex'], _n12 = re.subn(
        r', a comparison[^.]*?\\StFloor\{\}[^.]*', '',
        TEXT['abstract.tex'])
    assert _n12 == 1, ('drive 12 removed %d chance-comparison qualifications, '
                       'so it is not driving P10' % _n12)
if DRIVE == 13:
    #: P11: the proposal-code list back in the Acknowledgements.
    TEXT['08_backmatter.tex'] = TEXT['08_backmatter.tex'].replace(
        'are recorded block by block in the data release',
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
   and RANK_W is not None and FLAG_W is not None
   and FLAG_N == int(texval('EvNCrossFlag')),
   '%s=%r %s=%r (EvNCrossFlag %s)'
   % (RANK_N, RANK_W, FLAG_N, FLAG_W, texval('EvNCrossFlag')))

ck('P8b \\PrRankClause is written for the size of the set it describes',
   (RANK_CLAUSE is RANK_SINGULAR) == (RANK_N == 1)
   and (RANK_CLAUSE is RANK_NONE) == (RANK_N == 0)
   and ('their own fields' in RANK_CLAUSE) == (RANK_N > 1),
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

ck('P10 the chance comparison carries the population it could not have '
   'registered',
   'chance predicts' in ABS and r'\StFloor' in ABS,
   'StFloor %s' % ('cited' if r'\StFloor' in ABS else 'MISSING'))

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
