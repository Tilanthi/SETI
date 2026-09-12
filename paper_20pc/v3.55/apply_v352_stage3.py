#!/usr/bin/env python3
"""v3.54 stage 3: pay for the two new results out of float geometry.

Stage 2 added about 3,500 characters of measured result to the main text and
took the paper to 30 pages.  Prose is the expensive way to buy a page back and
the cheap way is float geometry, which the v3.50 cycle measured: nine thousand
characters of prose cuts left the page count where it was, and shrinking three
floats closed it in one step.

Two moves here, neither of which deletes a measurement:

  * `tab:configdist` goes back to Appendix~B, beside the injection campaign it
    qualifies.  v3.50 moved it the other way to fill 0.22 pp of main-text
    slack; there is no slack now, and the paragraph in Appendix~B that
    introduces the 0.5--2x transfer bracket is where a reader meets the
    question it answers.  Five \\ref calls elsewhere are unaffected.
  * two figures that are not in the protected set lose about a tenth of their
    width.  `fig:waterfall` is deliberately NOT among them: two referees have
    asked for it to be enlarged, and shrinking a figure a referee called
    illegible is the one economy that costs more than it saves.
"""
import re
import sys

PATH = sys.argv[1] if len(sys.argv) > 1 else 'technosignatures_20pc_v3.55.tex'
tex = open(PATH).read()
orig = tex

# ------------------------------------------------------- move tab:configdist
i = tex.index(r'\label{tab:configdist}')
b = tex.rindex(r'\begin{table}', 0, i)
e = tex.index(r'\end{table}', i) + len(r'\end{table}')
float_src = tex[b:e]
tex = tex[:b] + tex[e:].lstrip('\n')
tex = re.sub(r'\n{3,}', '\n\n', tex, count=0)

dest = r"""\textbf{This
is a demonstration that the pipeline recovers a carrier in a representative
configuration. It is not a survey completeness function.}"""
if tex.count(dest) != 1:
    raise SystemExit('destination anchor occurs %d times' % tex.count(dest))
tex = tex.replace(dest, float_src + '\n\n' + dest, 1)

# --------------------------------------------------------- float geometry
for old, new, what in (
        (r'\includegraphics[width=0.78\columnwidth]{figures/control_diagnostics.pdf}',
         r'\includegraphics[width=0.68\columnwidth]{figures/control_diagnostics.pdf}',
         'fig:ctrldiag'),
        (r'\includegraphics[width=0.86\textwidth]{figures/selection_funnel.pdf}',
         r'\includegraphics[width=0.78\textwidth]{figures/selection_funnel.pdf}',
         'fig:funnel')):
    if tex.count(old) != 1:
        raise SystemExit('%s: width anchor occurs %d times' % (what, tex.count(old)))
    tex = tex.replace(old, new, 1)
    print('  %-14s width reduced' % what)

print('stage 3: tab:configdist moved to Appendix B, 2 figures shrunk, NET %+d characters'
      % (len(tex) - len(orig)))
open(PATH, 'w').write(tex)
print('written', PATH)
