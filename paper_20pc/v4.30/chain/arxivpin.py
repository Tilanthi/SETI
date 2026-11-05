#!/usr/bin/env python3
r"""GATE: `ARXIV_UPLOAD.md` may not carry a hand-maintained measurement.

★★★ WHY THIS EXISTS.  The file whose only reader is the submitting author was
the one file nothing held.  At the close of the DEAI pass it stated, as the
things to verify at upload, a PDF md5, a main-text page count, an abstract
character count and an underfull-box count -- **all four belonging to the
build before the one in the tree**, because the revision landed at 00:47 and
the file was last written at 19:41.  Nothing about the paper was wrong; a
human following the file would have compared the tarball against the wrong
hash and concluded the package was corrupt.  Before that it had named a v3.62
manuscript under a v3.69 heading, 32 macro files where there were 145, a
29-page paper, and then two superseded item counts in succession.  Five
failures of one kind.

★★★ AND WHY IT IS NOT A HASH PIN.  The obvious repair -- have the gate hold
the four numbers the way `absmeta` holds the abstract's -- would make this the
SIXTH gate in this build to pin a form of words or a literal rather than a
fact (after `absreq` B5 and B7, `censusacct` A4, `prosegate_selfref`'s hash
pins and `LX-01c`).  A pinned number has to be updated by hand on every build,
which is the defect, not the cure.

So the gate holds a PROPERTY: **the file contains no measurement at all.**  It
tells the reader which command prints each number and what the verdict must
say, and it carries no md5, no page count, no word count, no item count and no
byte size of its own.  A measurement cannot go stale if it is not there.

Five clauses, each demonstrated firing by `--selftest`.
"""
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__)) or '.'
TARGET = 'ARXIV_UPLOAD.md'

# A number inside a fenced code block or a backticked span is a COMMAND or a
# filename, not a claim, and must not be swept: ``cat ${TMPDIR:-/tmp}/...``
# and ``\pdfsuppressptexinfo=-1`` both carry digits and neither is a
# measurement.  Prose is what is checked.
FENCE = re.compile(r'```.*?```', re.S)
CODE = re.compile(r'`[^`]*`')

CLAUSES = [
    ('P1 an md5 or any other long hex digest',
     re.compile(r'\b[0-9a-f]{8,}\b')),
    ('P2 a page count',
     re.compile(r'\b\d+(?:\.\d+)?\s*(?:pp|pages?)\b', re.I)),
    ('P3 an abstract length',
     re.compile(r'\b\d{3,4}\s*(?:characters|words)\b', re.I)),
    ('P4 an item or file count of the set',
     re.compile(r'\b\d+\s*items?\b', re.I)),
    ('P5 a size or box count of the build',
     re.compile(r'\b\d+(?:\.\d+)?\s*(?:kB|MB|underfull|overfull)\b', re.I)),
]


def strip(text):
    t = FENCE.sub(lambda m: '\n' * m.group(0).count('\n'), text)
    return CODE.sub(lambda m: ' ' * len(m.group(0)), t)


def check(text):
    """Return a list of (clause, line, matched text)."""
    t = strip(text)
    out = []
    for label, rx in CLAUSES:
        for m in rx.finditer(t):
            out.append((label, t[:m.start()].count('\n') + 1, m.group(0)))
    return out


def selftest():
    """Each clause has to be shown firing, on a string, or it is a claim."""
    base = ('Build it with `bash arxivset.sh --force` and read the A8 line.\n'
            'The numbers are printed by the run, never copied here.\n'
            '```\nmd5sum arxivset.tar.gz   # 41 pages, 1920 characters\n```\n')
    assert check(base) == [], check(base)
    drives = [
        ('P1', base + 'the md5 is 4dcb008f1938431749750bcc75bbc5cf\n'),
        ('P2', base + 'the main text comes down to 21.85 pp\n'),
        ('P3', base + 'the abstract is 1562 characters typeset\n'),
        ('P4', base + 'the set holds 240 items\n'),
        ('P5', base + 'the build leaves 30 underfull boxes\n'),
    ]
    bad = []
    for tag, txt in drives:
        hits = [h for h in check(txt) if h[0].startswith(tag)]
        print('  drive %s: %s' % (tag, 'FIRED %r' % hits[0][2] if hits
                                  else 'DID NOT FIRE -- the clause is vacuous'))
        if not hits:
            bad.append(tag)
    # ★ and the control: the same five numbers inside code spans and fences,
    # where they are commands and filenames, must NOT fire.
    quiet = (base + 'Run `md5sum 4dcb008f1938431749750bcc75bbc5cf.pdf`.\n'
             '```\npagesplit.py  -> 21.85 pp, 240 items, 30 underfull\n```\n')
    hits = check(quiet)
    print('  drive C (code spans and fences are not claims): %s'
          % ('CLEAN' if not hits else 'FIRED WRONGLY %s' % hits[:2]))
    if hits:
        bad.append('C')
    print('arxivpin --selftest: %d clause(s), %s'
          % (len(CLAUSES), 'all demonstrated' if not bad else 'BROKEN %s' % bad))
    return 1 if bad else 0


def main():
    if '--selftest' in sys.argv:
        return selftest()
    path = os.path.join(HERE, TARGET)
    if not os.path.isfile(path):
        print('arxivpin: FAIL %s does not exist -- nothing was measured, '
              'which is a failure and not a pass' % TARGET)
        return 1
    text = open(path, errors='ignore').read()
    hits = check(text)
    # the file must also still tell the reader how to get each number, or the
    # absence of measurements is silence rather than instruction.
    needs = ['arxivset.sh', 'A8', 'abswords.py', 'absmeta.py', 'pagesplit.py']
    absent = [n for n in needs if n not in text]
    print('arxivpin: %s, %d prose measurement(s), %d instruction(s) missing'
          % (TARGET, len(hits), len(absent)))
    for label, line, what in hits[:8]:
        print('  FAIL %s at line %d: %r -- take it from the run, not from '
              'this file' % (label, line, what))
    if absent:
        print('  FAIL P6 the file no longer says how to obtain: %s'
              % ', '.join(absent))
    if not hits and not absent:
        print('  OK no measurement is stated, and every number the author '
              'needs has a named command beside it')
    return 1 if (hits or absent) else 0


if __name__ == '__main__':
    sys.exit(main())
