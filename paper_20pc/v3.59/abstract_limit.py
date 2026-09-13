#!/usr/bin/env python3
"""arXiv abstract length gate.

arXiv rejects abstracts longer than 1920 characters as rendered. This paper's
abstract was 2682 characters at v3.44 and would have been refused at
submission; nobody caught it for nine versions. Run this in gate.sh on every
build from now on.

v3.49 DEFECT FOUND AND FIXED.  Until now this gate stripped every control
sequence to a space, so the VALUES of the generated macros -- which are what a
reader and arXiv actually see -- were not counted at all.  The abstract cites
twenty of them, and the gate therefore under-reported by about 70 characters.
At v3.48 it printed 1907 while the typeset abstract (`abschars.py`, which reads
the PDF) was 1975: the paper was over the limit and three referees, all quoting
this tool, could not see it.  Macros are now expanded from the generated
`survey_numbers*.tex` files before counting, and gate.sh runs `abschars.py`
alongside this script so the source-side and PDF-side numbers are checked
against each other on every build.
"""
import re, sys, glob

tex = sorted(glob.glob('technosignatures_20pc_v*.tex'))[-1]
s = open(tex).read()
m = re.search(r'\\begin\{abstract\}(.*?)\\end\{abstract\}', s, re.S)
if not m:
    sys.exit('abstract not found in ' + tex)
a = m.group(1)

# 1. expand generated macros to their values (\NWindows -> 431, and so on)
macros = {}
for fn in glob.glob('survey_numbers*.tex'):
    for name, val in re.findall(r'^\\newcommand\{\\([A-Za-z]+)\}\{(.*)\}\s*$',
                                open(fn).read(), re.M):
        macros[name] = val
for _ in range(3):                      # macros may contain macros
    a = re.sub(r'\\([A-Za-z]+)(\{\})?',
               lambda mm: macros.get(mm.group(1), '\\' + mm.group(1)
                                     + (mm.group(2) or '')), a)

# 2. symbols that occupy one character when typeset
for cmd, ch in (('\\times', 'x'), ('\\approx', '~'), ('\\pm', '+'),
                ('\\beta', 'b'), ('\\S', 'S'), ('\\ldots', '.'),
                ('\\gtrsim', '>'), ('\\lesssim', '<'), ('\\sim', '~'),
                ('\\geq', '>'), ('\\leq', '<'), ('\\,', ' '), ('\\%', '%')):
    a = a.replace(cmd, ch)
a = re.sub(r'\\ref\{[^}]*\}', '0', a)           # a section number
a = re.sub(r'\\(?:textbf|emph|texttt|mbox)\b', '', a)

# 3. strip what remains of the LaTeX, then collapse whitespace
p = re.sub(r'\\[a-zA-Z]+\*?(\[[^\]]*\])?', ' ', a)
p = re.sub(r'[{}$~\\^_]', '', p)
p = ' '.join(p.split())

LIMIT = 1920
print('abstract: %d rendered characters (arXiv limit %d) -- %s'
      % (len(p), LIMIT, 'OK' if len(p) <= LIMIT else 'OVER BY %d' % (len(p) - LIMIT)))
if '--text' in sys.argv:
    print(p)
sys.exit(0 if len(p) <= LIMIT else 1)
