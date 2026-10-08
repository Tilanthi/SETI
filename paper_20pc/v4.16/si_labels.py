#!/usr/bin/env python3
r"""si_labels.py SOURCE.aux TARGET.aux -- the labels of one document, without
its bibliography, for the other document to import through `xr`.

★★ WHY.  The split build is two documents from one source: the printed paper
(`\SIPAPER`) and the Supporting Information (`\SIAPPX`).  Each cites the
other's labels -- the paper says "Appendix~\ref{app:linemask}", an appendix
says "\S\ref{sec:technosearch}" -- so each imports the other's `.aux` through
`xr`.  But both documents print the SAME reference list, so importing a raw
`.aux` re-declares all of its `\bibcite` entries and pdflatex reports
"Citation `X' multiply defined" once per entry: 53 warnings in each log, on a
build where nothing is wrong.  This project treats the LaTeX log as a gate,
and a log with 53 warnings in it is a log nobody reads.

So the imported file is the source `.aux` with its `\bibcite` and `\citation`
lines removed and NOTHING ELSE CHANGED.  In particular `\newlabel` entries are
passed through verbatim, including the ones pdflatex wraps across two lines --
which is why this filters by line prefix and does not try to parse.

A missing source is not an error: on the first round of the fixed point the
other document has not been built yet, so an empty label file is written and
the references resolve on the next round.  `make_si.sh` checks that the two
page counts stop moving, which is what proves the fixed point was reached.
"""
import os
import re
import sys

src, dst = sys.argv[1], sys.argv[2]
try:
    txt = open(src, errors='ignore').read()
except OSError:
    txt = '\\relax\n'
keep = [ln for ln in txt.split('\n')
        if not ln.startswith('\\bibcite') and not ln.startswith('\\citation')]
body = '\n'.join(keep).rstrip('\n') + '\n'
# idempotent: do not touch the file if the content is unchanged, so a
# converged round does not restamp an mtime other gates compare against
if not (os.path.exists(dst) and open(dst, errors='ignore').read() == body):
    open(dst, 'w').write(body)
print('%s -> %s: %d line(s), %d newlabel, %d bibcite dropped'
      % (os.path.basename(src), os.path.basename(dst), len(keep),
         len(re.findall(r'\\newlabel', body)),
         len(re.findall(r'^\\bibcite', txt, re.M))))
