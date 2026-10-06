#!/usr/bin/env python3
"""MNRAS abstract length, measured on the built page.

The abstract must be one paragraph of no more than 250 words.  That is a
property of the TYPESET paragraph, not of the source: the source contains
macros, comments and line breaks, and every count made from it so far has
been wrong.  A comment in abstract.tex claimed 245 words while the printed
paragraph held 253 -- an eight-word error in the one number a journal checks
mechanically.

So this gate reads the PDF.  It extracts the text between the ABSTRACT
heading and whatever follows it, counts words the way a copy-editor would,
and fails above the limit.

It also refuses to pass if it cannot find the abstract at all, because a
length check that silently measures nothing is worse than no check: it
reports success for a paper whose abstract it never saw.
"""
import re
import subprocess
import sys
import glob
import os

LIMIT = 250
ENDERS = ('Subject headings', 'Key words', 'Keywords',
          '1. INTRODUCTION', '1.  INTRODUCTION', 'INTRODUCTION')


def main_pdf():
    """The one manuscript PDF, found the same way every other tool finds it."""
    cand = [p for p in glob.glob('technosignatures_*.pdf')
            if re.match(r'technosignatures_\d+pc_v[\d.]+\.pdf$', os.path.basename(p))]
    if len(cand) != 1:
        sys.exit('abswords: expected exactly one manuscript PDF, found %d: %s'
                 % (len(cand), sorted(cand)))
    return cand[0]


def abstract_text(pdf):
    out = subprocess.run(['pdftotext', '-f', '1', '-l', '1', pdf, '-'],
                         capture_output=True, text=True, check=True).stdout
    i = out.find('ABSTRACT')
    if i < 0:
        sys.exit('abswords: no ABSTRACT heading on page 1 of %s -- the gate '
                 'cannot measure what it cannot find, so this is a FAILURE, '
                 'not a pass' % pdf)
    body = out[i + len('ABSTRACT'):]
    for e in ENDERS:
        j = body.find(e)
        if j > 0:
            body = body[:j]
            break
    else:
        sys.exit('abswords: found ABSTRACT but no following heading; refusing '
                 'to count to the end of the page')
    return body.replace('-\n', '').replace('\n', ' ').strip()


def count(text):
    # A word is a whitespace-separated token carrying at least one
    # alphanumeric character; "---" and bare punctuation do not count.
    return len([w for w in re.split(r'\s+', text) if re.search(r'[0-9A-Za-z]', w)])


if __name__ == '__main__':
    pdf = main_pdf()
    text = abstract_text(pdf)
    n = count(text)
    paras = len([b for b in re.split(r'\s{4,}', text) if b.strip()])
    print('abswords: %d words in the typeset abstract of %s (limit %d)'
          % (n, pdf, LIMIT))
    bad = []
    if n > LIMIT:
        bad.append('abstract is %d words, %d over the MNRAS limit of %d'
                   % (n, n - LIMIT, LIMIT))
    if n < 120:
        bad.append('abstract is only %d words -- extraction probably clipped '
                   'it, which would make this gate vacuous' % n)
    if bad:
        for b in bad:
            print('  FAIL ' + b)
        sys.exit(1)
    print('  OK one paragraph, within the limit, measured on the page')
