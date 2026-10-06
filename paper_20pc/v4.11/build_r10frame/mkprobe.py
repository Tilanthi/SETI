#!/usr/bin/env python3
r"""Build r10-frame's probe PDF without touching the shared job name.

★ WHY THE PROBE .tex LIVES HERE AND NOT IN THE BUILD DIRECTORY'S PARENT.
`retire_macros.py`'s consumer list is `glob.glob("*.tex")`, so ANY stray
`.tex` in the build root counts as a document that references macros -- and a
probe copy of the manuscript references every macro in the paper, including
the ones retirement is supposed to delete.  A probe left in the root
therefore turns the retirement gate into a check that cannot fail.  This
script writes the probe into its own directory, builds it there, and leaves
nothing behind in the root.

Usage (from the build root):  python3 build_r10frame/mkprobe.py
"""
import glob, os, re, subprocess, sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
MAIN = os.path.join(ROOT, 'technosignatures_40pc_v4.11.tex')
s = open(MAIN).read()
# every round file a generator writes that the manuscript does not yet
# \input -- round 10 leaves several, one per agent, until integration
orph = sorted(int(re.search(r'round(\d+)', f).group(1))
              for f in glob.glob(os.path.join(ROOT, 'survey_numbers_round*.tex'))
              if 'drive' not in f
              and '\\input{%s}' % os.path.basename(f)[:-4] not in s)
add = '\n'.join('\\input{survey_numbers_round%d}' % n for n in orph)
s = s.replace('\\input{survey_numbers_round105}',
              '\\input{survey_numbers_round105}\n' + add)
probe = os.path.join(HERE, 'r10frame_probe.tex')
open(probe, 'w').write(s)
print('orphan rounds added:', orph)
for _ in range(2):
    r = subprocess.run(['pdflatex', '-interaction=nonstopmode',
                        '-jobname=r10frame-probe', '-output-directory=' + HERE,
                        probe], cwd=ROOT, capture_output=True, text=True)
log = open(os.path.join(HERE, 'r10frame-probe.log'), errors='ignore').read()
errs = [l for l in log.splitlines() if l.startswith('! ')]
print('%d TeX error(s)' % len(errs))
for e in errs[:10]:
    print('  ' + e)
sys.exit(1 if errs else 0)
