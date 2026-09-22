#!/usr/bin/env python3
"""Gate: no stray or mangled LaTeX macros in the source or the rendered PDF.

A referee found '\\textbf{We' rendered as literal 'extbfWe' in the compiled
PDF. The cause was a text-processing script that wrote its replacement
through a path interpreting backslash escapes, turning '\\t' into a TAB.
Nothing in gate.sh could see it: LaTeX compiled without error because
'extbf' is just a word.

Checks, on the source and on the extracted PDF text:
  1. control characters immediately followed by letters (mangled macros);
  2. bare 'extbf'/'extit'/'mph'/'ection' fragments not preceded by a
     backslash, which are what a lost backslash leaves behind;
  3. common macro names appearing in the rendered text, which should never
     survive typesetting.
"""
import os
import re
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
STEM = [f[:-4] for f in os.listdir(HERE)
        if f.startswith('technosignatures_') and f.endswith('.tex')][0]
src = open(os.path.join(HERE, STEM + '.tex')).read()
fail = 0

ctl = [(src[:m.start()].count('\n') + 1, m.group(1))
       for m in re.finditer(r'[\t\x08\x0b\x0c]([A-Za-z]+)', src)]
if ctl:
    fail += len(ctl)
    for ln, w in ctl:
        print('MANGLED  source line %d: control character + %r' % (ln, w))

FRAGS = ('extbf', 'extit', 'mph{', 'ection{', 'aption{', 'abel{')
for f in FRAGS:
    for m in re.finditer(r'(?<![\\A-Za-z])' + re.escape(f), src):
        ln = src[:m.start()].count('\n') + 1
        print('STRAY    source line %d: %r without a backslash' % (ln, f))
        fail += 1

pdf = os.path.join(HERE, STEM + '.pdf')
if os.path.exists(pdf):
    txt = subprocess.run(['pdftotext', pdf, '-'], capture_output=True,
                         text=True).stdout
    for f in ('extbf', 'extit', 'textbf', 'emph{', 'ref{'):
        n = txt.count(f)
        if n:
            print('RENDERED %r appears %d time(s) in the PDF text' % (f, n))
            fail += n

print('macroleak: %d problem(s)' % fail)
sys.exit(1 if fail else 0)
