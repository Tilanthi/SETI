#!/usr/bin/env python3
"""arXiv abstract CHARACTER gate, measured on the typeset page.

arXiv: "Keep it short -- abstracts longer than 1920 characters will not be
accepted; abridge your abstract if necessary" (info.arxiv.org/help/prep.html).
The limit applies to the plain-ASCII abstract pasted into the submission
metadata field -- as SUBMITTED, not as rendered -- and the field is where a
submission is actually refused.  The typeset paragraph with its line breaks
collapsed is the closest measurable proxy and an upper bound on it, since the
form drops the TeX spacing commands that the page sets as space.

This file used to MEASURE and print and then exit zero whatever it found.  A
length check that cannot fail is not a check: the companion word count has
refused to pass without finding the abstract since v4.11, and this one would
have announced 2682 characters and returned success.  It now fails above the
limit, and -- the property that matters more -- it fails if it cannot find the
abstract at all, or finds implausibly little of it, rather than reporting
success for a paper whose abstract it never read.

Two numbers are deliberately kept, here and in abstract_limit.py: this one
reads the PDF, that one expands the macros in the source.  Neither can check
the other if they share code, so they share none.

  python3 abschars.py [pdf] [--text] [--drive N]

Drives (each must FAIL; the suffix follows the flag, not the perturbation, so
no drive can leave a file production reads -- this gate writes nothing):
  1  limit lowered below the measured length   -> the comparison fires
  2  the ABSTRACT heading is looked for under a name that is not on the page
                                               -> "cannot find" fires
  3  the extraction is truncated to a few words -> the clipped-extraction
                                                  floor fires
  4  the closing heading is removed from the list -> refuses to count to the
                                                    foot of the page
"""
import os
import re
import sys

import pymupdf

import manuscript

LIMIT = 1920                      # arXiv, characters, hard refusal
FLOOR = 600                       # below this the extraction has clipped
# The abstract ends at whichever of these the class typesets next.  A single
# hard-coded ender is one of this project's two "blind on a literal" gates.
ENDERS = ('Subject headings', 'Key words', 'Keywords', 'Unified Astronomy',
          '1. INTRODUCTION', '1.  INTRODUCTION', 'INTRODUCTION')


def drive():
    for i, a in enumerate(sys.argv[1:], 1):
        if a.startswith('--drive'):
            return int(a.split('=')[1]) if '=' in a else int(sys.argv[i + 1])
    return 0


def abstract(pdf, d=0):
    """The typeset abstract, whitespace collapsed.  Raises if not found."""
    txt = pymupdf.open(pdf)[0].get_text()
    head = 'ABSTRAKT' if d == 2 else 'ABSTRACT'
    i = txt.find(head)
    if i < 0:
        raise LookupError('no %s heading on page 1 of %s -- the gate cannot '
                          'measure what it cannot find, so this is a FAILURE, '
                          'not a pass' % (head, pdf))
    body = txt[i + len(head):]
    enders = () if d == 4 else ENDERS
    for e in enders:
        j = body.find(e)
        if j > 0:
            body = body[:j]
            break
    else:
        raise LookupError('found the ABSTRACT heading but none of the headings '
                          'that follow it (%s); refusing to count to the foot '
                          'of the page' % ', '.join(ENDERS))
    s = re.sub(r'\s+', ' ', body.replace('-\n', '')).strip()
    return ' '.join(s.split()[:6]) if d == 3 else s


def main():
    d = drive()
    pdf = next((a for a in sys.argv[1:] if a.endswith('.pdf')),
               manuscript.main_file()[:-4] + '.pdf')
    limit = LIMIT
    bad = []
    if not os.path.exists(pdf):
        print('abschars: FAIL %s does not exist -- nothing was measured, '
              'which is a failure and not a pass' % pdf)
        return 1
    try:
        s = abstract(pdf, d)
    except LookupError as e:
        print('abschars: FAIL %s' % e)
        return 1
    n = len(s)
    if d == 1:
        limit = n - 1
    nw = len([w for w in s.split() if re.search(r'[0-9A-Za-z]', w)])
    print('abschars: %d characters, %d words in the typeset abstract of %s '
          '(arXiv limit %d, headroom %d)' % (n, nw, pdf, limit, limit - n))
    if n > limit:
        bad.append('abstract is %d characters, %d over the arXiv limit of %d; '
                   'arXiv will refuse the submission' % (n, n - limit, limit))
    if n < FLOOR:
        bad.append('abstract measured as only %d characters, below the %d '
                   'floor -- the extraction has clipped and the measurement '
                   'is not trustworthy' % (n, FLOOR))
    # arXiv's metadata fields are ASCII only ("Bad character(s) in field..."),
    # so whatever is reported here must be hand-converted when the abstract is
    # pasted into the form.  The PDF is allowed these characters and this is
    # therefore a notice, not a failure -- said plainly so that nobody later
    # reads the silence as "there are none".
    na = sorted(set(c for c in s if ord(c) > 127))
    if na:
        print('  NOTE %d non-ASCII character(s) in the typeset abstract, which '
              'the arXiv metadata field will reject and which must be entered '
              'as TeX or as words: %s'
              % (len(na), ' '.join('%s (U+%04X)' % (c, ord(c)) for c in na)))
    else:
        print('  NOTE no non-ASCII characters; the abstract can be pasted into '
              'the arXiv form as it stands')
    if '--text' in sys.argv:
        print(s)
    if bad:
        for b in bad:
            print('  FAIL ' + b)
        return 1
    if d:
        print('  DRIVE %d DID NOT FAIL -- the clause it exercises is vacuous'
              % d)
        return 2
    print('  OK within the arXiv character limit, measured on the page')
    return 0


if __name__ == '__main__':
    sys.exit(main())
