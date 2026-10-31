#!/usr/bin/env python3
"""The arXiv METADATA abstract: the plain-ASCII text that is actually pasted.

    python3 absmeta.py [--drive N] [--text]

arXiv refuses an abstract longer than 1920 characters, and it refuses unicode
in the metadata fields outright ("Bad character(s) in field Abstract").  The
text that meets those two rules is NOT the typeset paragraph: the page carries
`+/-`, `x`, `-` and a closing quote as real unicode, and two superscripts that
the PDF extractor flattens.  So the submission carries a transliteration of
the abstract, and it is written down in `OJA_SUBMISSION.md` for the author to
paste.

A number written down in a markdown file is not a measured number -- that is
this project's oldest defect -- and a transliteration written down beside a
paragraph that moves every build is worse: the typeset abstract is 64
characters short of the limit, so one macro gaining a digit changes both the
text and its length.  This gate therefore measures the block that is actually
in that file, on every build:

  M1  the block is pure ASCII, since arXiv's field rejects everything else;
  M2  it is within the 1920-character limit;
  M3  it IS the current typeset abstract, transliterated -- not an older one.
      Equality, character for character, so a value that moved in the paper
      and not in the block fails the build rather than being submitted;
  M4  the two counts the file quotes beside it are the measured ones.

M3 deliberately shares the extractor with `abschars.py`: the question here is
not "how long is the abstract" (that gate asks it on the page, and
`abstract_limit.py` asks it again from the source with no shared code) but
"is the text in the submission file the one the paper now prints", which can
only be asked against the same extraction.  The transliteration table is
duplicated from `../../referee_r17/absascii_r17.py`, which GENERATES the
block; a generator and a gate that agree by construction would be one check,
and this file is here to disagree when the block goes stale.

Drives (each must FAIL on its own; nothing is written by any of them):
  1  the limit is lowered below the measured length  -> M2 fires
  2  a non-ASCII character is put back into the block -> M1 fires
  3  one character of the block is changed            -> M3 fires
  4  the block is looked for under a heading that is not in the file
                                                      -> "cannot find" fires
  5  the quoted character count is moved by one       -> M4 fires
  6  the quoted page count is moved by one            -> M5 fires
  7  one character of the metadata title is changed   -> M5 fires

  M5  (r28-abstract, v4.29) the arXiv metadata block in the same file --
      `Title:` and `Comments: N pages, M figures` -- states the title the
      PDF prints (page 1, above the author line, transliterated) and the
      PDF's page count and figure count (figure captions in the .aux).
      Referee 2 asks that both be checked; a typed count in a markdown
      file is checked here or it goes stale.
"""
import os
import re
import sys

import abschars
import manuscript

LIMIT = 1920
FLOOR = 600
SUBMISSION = 'OJA_SUBMISSION.md'
HEADING = re.compile(r'^##\s.*plain ASCII', re.M)

# The character map and the two extractor repairs, exactly as the generator
# applies them.  Written out rather than imported: the generator lives outside
# the paper tree on purpose, and a gate that imports the thing it checks is
# circular.
MAP = {'±': '+/-', '×': 'x', '−': '-', '–': '-',
       '—': '--', '’': "'", '‘': "'", '“': '"',
       '”': '"', ' ': ' ', ' ': ' '}
# ★ 2026-10-14: the first repair used to open with `\b`, which assumed the PDF
# extractor put a space in front of the mantissa.  On this build it does not --
# the abstract extracts as `1.5x1015 W`, where `x` and `1` are both word
# characters, so there is no boundary and the repair matched nothing.  The gate
# then refused a correct abstract.  The pattern now keys on what is actually
# invariant: the mantissa is preceded either by the transliterated multiplication
# sign or by whitespace, and is followed by the unit.  Spacing in the extracted
# text is not a property of the paper and no gate may depend on it.
# ★★★★ THE THIRD REPAIR IS NOT A SUPERSCRIPT -- IT IS A HYPHEN THE PAGE
# PRINTS AND THE EXTRACTOR EATS.  `abschars.py` joins a line broken by TeX by
# deleting `-\n`, which is right for a word TeX hyphenated ("instru-mental")
# and WRONG for a compound whose hyphen is the author's and happens to fall
# at the break: "a single-epoch trigger completeness" extracts as
# "singleepoch".  The page is correct, the paper is correct, and the only
# thing wrong is the string we would paste into the arXiv metadata field --
# which is exactly what this gate exists to protect.  It is triggered by
# where the line happens to break, so it comes and goes with any edit
# anywhere above it; that is why it is a REPAIR (reported when its artefact
# is absent) and not an assertion.
# ►► IF ANOTHER AUTHORED COMPOUND EVER MEETS A LINE BREAK HERE, ADD IT -- in
# BOTH this tuple and the generator's, which is the pair of places that must
# agree.  There is no general rule available: the extractor cannot tell the
# two kinds of hyphen apart, and only the source knows which it was.
# ►► THE LIST IS THE ABSTRACT'S OWN AUTHORED COMPOUNDS, NOT THE ONE THAT
# BREAKS TODAY.  Which compound meets the line break moves with every edit
# above it, so a tuple carrying only today's casualty has to be re-found
# every round -- and was: `singleepoch` is not in this abstract at all now,
# while `channelresponse` and the flattened `m s-2` both were, and neither
# had an entry.  An entry whose artefact is absent is reported and costs
# nothing, so every authored hyphen in the paragraph gets one.
# ★★★★ 2026-10-18 (integration): THE POWER-OF-TEN RULE WAS WRITTEN FOR THE
# ONE POWER THAT HAPPENED TO BE FOLLOWED BY "W".  The per-system span puts a
# second one before the word "to", the extractor flattened it there
# ("7.1 x 1013"), and the rule could not see it -- the same defect as the
# hyphen list, one namespace along: a repair pinned to where today's
# artefact fell rather than to what the artefact IS.  A flattened exponent
# is "x 10" followed immediately by digits, wherever it falls, and the
# invariant below is that none survives the repairs.
REPAIR = ((r'(?:(?<=x)|(?<=\s))10(\d{2})\b', r'10^\1'),
          (r'\bkm s-1\b', 'km s^-1'),
          (r'\bm s-2\b', 'm s^-2'),
          (r'\bsingleepoch\b', 'single-epoch'),
          (r'\bfinechannel\b', 'fine-channel'),
          (r'\bdedrifted\b', 'de-drifted'),
          (r'\bchannelresponse\b', 'channel-response'),
          (r'\bstellarframe\b', 'stellar-frame'),
          (r'\bqualitypassing\b', 'quality-passing'),
          (r'\b([Dd])riftcorrected\b', r'\1rift-corrected'),
          (r'\bnondetection\b', 'non-detection'))


def drive():
    for i, a in enumerate(sys.argv[1:], 1):
        if a.startswith('--drive'):
            return int(a.split('=')[1]) if '=' in a else int(sys.argv[i + 1])
    return 0


def block(path, d=0):
    """The one fenced block under the plain-ASCII heading, and the counts
    quoted in the sentence above it."""
    txt = open(path, encoding='utf-8').read()
    head = re.compile(r'^##\s.*plain ASCII in the arXiv form', re.M) \
        if d == 4 else HEADING
    m = head.search(txt)
    if not m:
        raise LookupError('no "plain ASCII" section heading in %s -- the gate '
                          'cannot check a block it cannot find, so this is a '
                          'FAILURE and not a pass' % path)
    rest = txt[m.end():]
    nxt = re.search(r'^##\s', rest, re.M)
    sect = rest[:nxt.start()] if nxt else rest
    fences = re.findall(r'^```\n(.*?)^```', sect, re.M | re.S)
    if len(fences) != 1:
        raise LookupError('expected exactly one fenced block under the '
                          'plain-ASCII heading of %s, found %d'
                          % (path, len(fences)))
    lines = [l for l in fences[0].splitlines() if l.strip()]
    if len(lines) != 1:
        raise LookupError('the pasted abstract must be one paragraph on one '
                          'line; found %d non-empty line(s)' % len(lines))
    quoted = re.search(r'\*\*(\d+) characters, (\d+) words\.\*\*', sect)
    if not quoted:
        raise LookupError('the plain-ASCII section does not state the '
                          'character and word counts of its own block')
    return lines[0], int(quoted.group(1)), int(quoted.group(2))


def transliterate(s):
    for k, v in MAP.items():
        s = s.replace(k, v)
    # ★★★ A REPAIR IS FOR AN ARTEFACT THAT MAY NOT BE THERE.  Each entry
    # undoes one way the PDF extractor flattens a superscript, and the
    # abstract is rewritten every round: an abstract that no longer quotes a
    # velocity simply has no `km s-1` to repair, and raising on that made the
    # build fail on a correct abstract.  What must never happen silently is
    # a repair going stale while its artefact IS present -- and the
    # justification that used to stand here for leaving that to M1/M3 was
    # WRONG, which is worth recording because it is why a `1.5x1015` could
    # ship.  It said an unrepaired superscript "leaves the block disagreeing
    # with the generated one (M3) or carrying a character the metadata field
    # refuses (M1)".  It does NEITHER: the pasted block is produced by this
    # same code, so a stale repair agrees with itself perfectly, and
    # `1.5x1015` is pure ASCII.  The only protection is the net below -- which
    # is why it must not require the space the `\times` glue is free to shrink
    # away.  So a repair that matches nothing is REPORTED, and the NET fails.
    for pat, rep in REPAIR:
        s, n = re.subn(pat, rep, s)
        if not n:
            print('    note: the repair %r matched nothing in this '
                  'abstract, so the artefact it undoes is not present'
                  % pat)
    # ★★ v4.24: THE NET MUST NOT REQUIRE THE SPACE EITHER.  `x 10\d` does not
    # match `x1015`, which is precisely the form the shrunken \times glue
    # produces, so the net was blind to the one case the repair above had
    # stopped catching.  `x ?10\d` matches `x 1015` and `x1015` and neither
    # `x 10^15` nor `x10^15`, because `^` is not a digit.
    assert not re.search(r'x ?10\d', s), (
        'a flattened power of ten survives the repairs: %r -- the extractor '
        'has changed and the transliteration must be checked by eye'
        % re.search(r'.{0,25}x ?10\d.{0,15}', s).group(0))
    return s


META = re.compile(r'^##\s.*Title and comments.*?\n```\n(.*?)\n```', re.M | re.S)


def metadata(path, pdf, d=0):
    """M5: (problems, report) for the Title/Comments block."""
    import pymupdf
    txt = open(path, encoding='utf-8').read()
    m = META.search(txt)
    if not m:
        return (['M5 no "## ... Title and comments" section with a fenced '
                 'Title/Comments block in %s' % SUBMISSION], '')
    f = dict(l.split(':', 1) for l in m.group(1).splitlines() if ':' in l)
    title = f.get('Title', '').strip()
    com = f.get('Comments', '').strip()
    doc = pymupdf.open(pdf)
    p1 = doc[0].get_text()
    j = p1.find('ABSTRACT')
    head = p1[:j] if j > 0 else p1
    # the title is everything above the author line (the first line that
    # carries an affiliation mark); whitespace collapsed, transliterated.
    lines = head.splitlines()
    k = next((i for i, l in enumerate(lines) if re.search(r'\band\b.*\d', l)
              or re.search(r'[a-z]\d(,\d)*$', l.strip())), len(lines))
    page_title = ' '.join(' '.join(lines[:k]).split())
    for a, b in MAP.items():
        page_title = page_title.replace(a, b)
    if d == 7:
        title = title[:-1] + ('x' if title[-1:] != 'x' else 'y')
    aux = os.path.splitext(pdf)[0] + '.aux'
    nfig = (len(re.findall(r'\\contentsline \{figure\}', open(aux).read()))
            if os.path.exists(aux) else -1)
    npg = doc.page_count
    mc = re.fullmatch(r'(\d+) pages, (\d+) figures(?:,.*)?', com)
    qp, qf = (int(mc.group(1)), int(mc.group(2))) if mc else (None, None)
    if d == 6 and qp is not None:
        qp += 1
    bad = []
    if title != page_title:
        bad.append('M5 the metadata title %r is not the title the PDF prints '
                   '%r' % (title, page_title))
    if (qp, qf) != (npg, nfig):
        bad.append('M5 the comments field says %s pages and %s figures; the '
                   'PDF has %d pages and %d figures' % (qp, qf, npg, nfig))
    return bad, ('title as printed; %d pages, %d figures' % (npg, nfig))


def main():
    d = drive()
    here = os.path.dirname(os.path.abspath(__file__)) or '.'
    pdf = next((a for a in sys.argv[1:] if a.endswith('.pdf')),
               os.path.join(here, manuscript.main_file()[:-4] + '.pdf'))
    path = os.path.join(here, SUBMISSION)
    limit = LIMIT
    bad = []
    if not os.path.exists(pdf):
        print('absmeta: FAIL %s does not exist -- nothing was measured, '
              'which is a failure and not a pass' % pdf)
        return 1
    try:
        txt, q_chars, q_words = block(path, d)
        want = transliterate(abschars.abstract(pdf))
    except LookupError as e:
        print('absmeta: FAIL %s' % e)
        return 1
    if d == 2:
        #: ★★★★ RE-POINTED (v4.26): THIS DRIVE HAD GONE VACUOUS AND SAID
        #: NOTHING ABOUT IT, WHICH IS THE FAILURE MODE THIS WHOLE FILE IS
        #: WRITTEN AGAINST.  It put back a `±` by undoing the one
        #: transliteration `+/-`, and the abstract has carried no plus-minus
        #: sign for two revisions -- so `str.replace` returned the string
        #: unchanged, M1 was never exercised, and the harness reported the
        #: CLAUSE vacuous when the DRIVE was.  M1 is the clause with a real
        #: refusal behind it: arXiv's metadata field rejects the character.
        #: Keyed now on the page's own non-ASCII set rather than on one
        #: character the paragraph happens to use, so it cannot expire while
        #: the page carries anything to transliterate, and it RAISES rather
        #: than passing if the page carries nothing at all.
        _na = sorted({c for c in abschars.abstract(pdf) if ord(c) > 126})
        if not _na:
            raise LookupError(
                'drive 2 cannot drive: the typeset abstract carries no '
                'non-ASCII character, so M1 is unfalsifiable on this build '
                'and the clause must not be reported as demonstrated')
        _c = _na[0]
        _ascii = MAP.get(_c)
        if _ascii and _ascii in txt:
            txt = txt.replace(_ascii, _c, 1)
        else:
            txt = txt + _c
    if d == 3:
        txt = txt[:-1] + ('.' if txt[-1] != '.' else ',')
    if d == 5:
        q_chars += 1
    n = len(txt)
    nw = len([w for w in txt.split() if re.search(r'[0-9A-Za-z]', w)])
    if d == 1:                       # the limit brought below what is there,
        limit = n - 1                # which is how abschars.py drives its own
    print('absmeta: the pasted abstract in %s is %d characters, %d words '
          '(arXiv limit %d, headroom %d)'
          % (SUBMISSION, n, nw, limit, limit - n))
    na = sorted(set(c for c in txt if ord(c) > 126))
    if na:
        bad.append('M1 %d character(s) arXiv\'s metadata field rejects: %s'
                   % (len(na), ' '.join('%r (U+%04X)' % (c, ord(c))
                                        for c in na)))
    if n > limit:
        bad.append('M2 the pasted abstract is %d characters, %d over the '
                   'arXiv limit of %d; arXiv will refuse the submission'
                   % (n, n - limit, limit))
    if n < FLOOR:
        bad.append('M2 the pasted abstract is only %d characters, below the '
                   '%d floor -- it is not the abstract' % (n, FLOOR))
    if txt != want:
        i = next((k for k in range(min(len(txt), len(want)))
                  if txt[k] != want[k]), min(len(txt), len(want)))
        bad.append('M3 the pasted abstract is not the typeset one '
                   'transliterated: they first differ at character %d, '
                   '...%r in the file against ...%r on the page (%d against '
                   '%d characters)'
                   % (i + 1, txt[max(0, i - 25):i + 15],
                      want[max(0, i - 25):i + 15], len(txt), len(want)))
    else:
        print('  OK the pasted text is the typeset abstract, transliterated, '
              'character for character')
    if (q_chars, q_words) != (n, nw):
        bad.append('M4 the section states %d characters and %d words; the '
                   'block holds %d and %d' % (q_chars, q_words, n, nw))
    _mbad, _mrep = metadata(path, pdf, d)
    bad += _mbad
    if not _mbad:
        print('  OK the metadata block states the ' + _mrep)
    if '--text' in sys.argv:
        print(txt)
    if bad:
        for b in bad:
            print('  FAIL ' + b)
        return 1
    if d:
        print('  DRIVE %d DID NOT FAIL -- the clause it exercises is vacuous'
              % d)
        return 2
    print('  OK pure ASCII, within the arXiv character limit, and the counts '
          'the file quotes are the measured ones')
    return 0


if __name__ == '__main__':
    sys.exit(main())
