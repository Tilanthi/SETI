#!/usr/bin/env python3
"""Page-count gate, and what it would take to meet the limit.

The Open Journal of Astrophysics sets no page limit of any kind -- it is an
arXiv overlay journal, so the published article is the arXiv PDF and there is
no typesetting, no copy-editing and no Supporting Information to move anything
into.  The limit here is therefore the author's: ONE document, no more than
LIMIT pages, appendices included.  That is why this gate counts the whole PDF
and not the main text: there is nowhere else for a page to go.

It also prints the shortfall in the unit the work is actually done in.  A page
of this class is two columns of 693.8 pt, so 1388 pt of column is one page;
quoting a cut as "two pages" and quoting it as "2775 pt of column" are the same
instruction, but only the second can be checked against a section's measured
extent in secbudget.py.

Two independent readers must agree on the count -- pymupdf and poppler's
pdfinfo -- because a single reader cannot catch itself, and the gate fails if
the file is missing, unreadable, empty, or ends in a page with nothing on it.
A page count that is wrong in the direction of a pass is the whole failure mode.

★★ THE TARGET IS ADVISORY AS OF 2026-10-10 AND THE MEASUREMENT IS NOT.
Glenn relaxed the page count for this round -- nothing is to be deleted to
meet it -- so being over the target is printed loudly and exits ZERO, while
a count that cannot be made (missing file, no pages, the two readers
disagreeing, a blank trailing page) still fails.  `--strict` turns the target
back into a verdict for the trimming pass.

  python3 pagegate.py [pdf] [--limit N] [--drive N] [--strict]

Drives:
  1  limit lowered below the measured count    -> the shortfall is REPORTED
     (exit 0 by design; the drive checks the report, not the status)
  2  the second reader is made to disagree      -> the cross-check fires
  3  a PDF path that does not exist             -> the missing-file clause fires
  4  the last-page-has-text check is applied to a blank page appended in
     memory                                     -> the trailing-blank clause
"""
import os
import re
import subprocess
import sys

import pymupdf

import manuscript

LIMIT = 25                      # pages, one document, appendices included
STRICT = '--strict' in sys.argv  # make the target a verdict again
COLPT = 693.8                   # one column of this class, points
PAGEPT = 2 * COLPT              # one page of column measure


def arg(flag, default):
    for i, a in enumerate(sys.argv[1:], 1):
        if a.startswith(flag):
            return int(a.split('=')[1]) if '=' in a else int(sys.argv[i + 1])
    return default


def poppler_pages(pdf, d=0):
    """The count according to a different program entirely."""
    out = subprocess.run(['pdfinfo', pdf], capture_output=True, text=True)
    if out.returncode != 0:
        raise RuntimeError('pdfinfo could not read %s: %s'
                           % (pdf, out.stderr.strip()[:200]))
    m = re.search(r'^Pages:\s+(\d+)', out.stdout, re.M)
    if not m:
        raise RuntimeError('pdfinfo printed no Pages field for %s -- the '
                           'cross-check cannot be made, so it has not been '
                           'made' % pdf)
    return int(m.group(1)) + (1 if d == 2 else 0)


def main():
    d = arg('--drive', 0)
    limit = arg('--limit', LIMIT)
    pdf = next((a for a in sys.argv[1:] if a.endswith('.pdf')),
               manuscript.main_file()[:-4] + '.pdf')
    if d == 3:
        pdf = pdf + '.no-such-file.pdf'
    if not os.path.exists(pdf):
        print('pagegate: FAIL %s does not exist -- nothing was measured, '
              'which is a failure and not a pass' % pdf)
        return 1
    try:
        doc = pymupdf.open(pdf)
        n = doc.page_count
        other = poppler_pages(pdf, d)
    except Exception as e:
        print('pagegate: FAIL could not read %s: %s' % (pdf, e))
        return 1
    bad = []
    if n == 0:
        bad.append('the PDF has no pages at all')
    if n != other:
        bad.append('pymupdf counts %d pages and pdfinfo counts %d -- one of '
                   'the two readers is wrong and the count cannot be trusted'
                   % (n, other))
    last = doc[n - 1].get_text().strip() if n else ''
    if d == 4:
        last = ''
    if n and not last:
        bad.append('the last page carries no text: either a stray \\clearpage '
                   'has added a blank page, or the extraction is broken')
    if d == 1:
        limit = n - 1
    over = n - limit
    print('pagegate: %d pages in %s (limit %d, %s)'
          % (n, os.path.basename(pdf), limit,
             'under by %d' % -over if over < 0 else
             'exactly at the limit' if over == 0 else 'OVER BY %d' % over))
    # ★★★★ THE LIMIT IS A REPORT, NOT A VERDICT -- GLENN, 2026-10-10.
    # "you can relax the page count - and focus instead on getting the text
    # correct ... I can then separately look at trimming the length at a
    # later stage."  So the page count may not fail the build: nothing is to
    # be deleted to meet it this round, and a gate that is red for a reason
    # the author has already ruled on is a gate that gets switched off.
    # ★ But the DISTINCTION matters and is the whole of the design here: the
    # page count is advisory, the MEASUREMENT is not.  A missing file, zero
    # pages, two readers disagreeing or a blank trailing page all still fail,
    # because a page count that is wrong in the direction of a pass is this
    # gate's only real failure mode and relaxing the target must not relax
    # that.  `bad` carries the measurement failures and nothing else.
    # ★ `--strict` restores the hard verdict in one word, for the trimming
    # pass; the shortfall is printed identically either way so the two modes
    # cannot drift apart in what they report.
    shortfall = ''
    if over > 0:
        shortfall = ('%d pages against a target of %d: %d page(s) are to come '
                     'out, which is %.0f pt of column measure (1 page = '
                     '%.0f pt, 1 column = %.1f pt)'
                     % (n, limit, over, over * PAGEPT, PAGEPT, COLPT))
    if bad:
        for b in bad:
            print('  FAIL ' + b)
        return 1
    # anti-vacuity: the gate must have measured something, in both readers,
    # and must have produced the column arithmetic whenever it is over.
    if not n or n != other or (over > 0 and not shortfall):
        print('  FAIL the measurement did not complete, so this run is not '
              'evidence of anything (pages=%r other=%r over=%r)'
              % (n, other, over))
        return 1
    if shortfall:
        print('  ' + '=' * 68)
        print('  ***  PAGE TARGET NOT MET  ***')
        print('  *** ' + shortfall)
        print('  *** Relaxed by the author on 2026-10-10 for this round: the')
        print('  *** text is to be made correct first and trimmed afterwards.')
        print('  *** This is a REPORT, not a verdict -- run with --strict to')
        print('  *** make it a verdict again when the trimming pass begins.')
        print('  ' + '=' * 68)
        if STRICT:
            print('  FAIL --strict: ' + shortfall)
            return 1
    if d:
        # For the advisory clause a drive proves the REPORT is produced; for
        # the measurement clauses it proves the build fails.  Drive 1 is the
        # advisory one and is checked by its own text, not by the exit code,
        # because the exit code is deliberately zero now.
        if d == 1 and shortfall:
            print('  DRIVE 1 fired: the shortfall was measured and reported '
                  'and the exit status is deliberately 0')
            return 0
        print('  DRIVE %d DID NOT FAIL -- the clause it exercises is vacuous'
              % d)
        return 2
    print('  OK %d pages, both readers agree, last page is not blank' % n)
    return 0


if __name__ == '__main__':
    sys.exit(main())
