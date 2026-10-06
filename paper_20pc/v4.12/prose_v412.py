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

WHAT IT GATES

The four files of the front matter -- abstract, introduction, conclusions,
backmatter -- are the only ones a referee and most readers see in full, and
every existing gate in this build compares strings or numbers.  None reads
English.  So:

    P4  the abstract must carry Referee 1's exact confirmation formulation,
        and must NOT promote the spatial rank: \NUnattrRankFlagged gates no
        disposition, so advertising it in the abstract advertises a quantity
        the paper says carries no evidential weight (R2-M3.4);
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

# ------------------------------------------------------------- the four files
TEXT = {f: prose(f) for f in MINE}
if DRIVE == 4:
    TEXT['abstract.tex'] += (
        r' Only \NUnattrRankFlagged{} unattributed crossing is brighter at '
        r'its star than at any control.')
if DRIVE == 5:
    TEXT['01_intro.tex'] += ' We now report the revised search.'
if DRIVE == 6:
    NUMOK = set()                           # P6: the allow-list is the check
if DRIVE == 7:
    TEXT['abstract.tex'] = TEXT['abstract.tex'].replace(
        'union bandwidth', 'sky frequency')

ABS = TEXT['abstract.tex']

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

_rankwords = ('NUnattrRankFlagged', 'brighter at its star',
              'outranks', 'control positions of their own field')
ck('P4 the abstract carries R1\'s confirmation wording and not the rank',
   'pre-defined independent-recurrence confirmation criterion' in ABS
   and not any(w in ABS for w in _rankwords),
   'rank words present: %s'
   % ([w for w in _rankwords if w in ABS] or 'none'))

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
   and RANK_W is not None and FLAG_W is not None,
   '%s=%r %s=%r' % (RANK_N, RANK_W, FLAG_N, FLAG_W))

# -------------------------------------------------------------------- output
m('PrSysClassB', '%d' % SYS_B)
#: SYS_B_BYNAME is deliberately NOT published.  It is the wrong answer, it
#: exists to drive P2, and an emitted macro that no sentence references is
#: exactly what `retire_macros.py` deletes -- which is how a typed 403 once
#: survived in this build with no gate able to see it.
m('PrConfFactor', WORD or 'UNRESOLVED')
m('PrRankWord', RANK_W or 'UNRESOLVED')
m('PrFlagXrossWord', FLAG_W or 'UNRESOLVED')

HDR = ['%% GENERATED by prose_v412.py -- do not hand-edit.',
       '%% round ' + str(ROUND) + ': the Class B system count, and the word '
       'the abstract',
       '%% uses for the ratio of the searched union to the confirmable one.']
with open(OUT_PATH, 'w') as fh:
    fh.write('\n'.join(HDR + sorted(OUT)) + '\n')
print('\nwrote %s: %d macros' % (OUT_NAME, len(OUT)))
if fail:
    print('FAILED: %s' % '; '.join(fail))
    raise SystemExit(1)
