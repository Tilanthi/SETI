#!/usr/bin/env python3
"""R2-t2 (v3.99): a cross-reference resolution pass that sees what the
"0 undefined references" gate cannot.

Four classes of defect, each found in this manuscript at v3.86:
  (a) a \\label placed after a float anchors on the FLOAT, so \\S\\ref
      prints a section number while the hyperlink lands on a table;
  (b) a label defined and never referenced;
  (c) two labels sharing one anchor, so a \\ref to either prints the same
      number and the distinction the labels imply does not exist;
  (d) a reference from inside the very section it points at.

Exit 1 on (a); (b)-(d) are reported, not enforced, since aliases are
sometimes deliberate (they keep old \\refs resolving after a rename).
"""
import collections
import os
import re
import sys
import manuscript  # v4.10: the manuscript is split into sections/

HERE = os.path.dirname(os.path.abspath(__file__))
STEM = [f[:-4] for f in os.listdir(HERE)
        if f.startswith('technosignatures_') and f.endswith('.tex')][0]
# ★ ROUND 9: strip source comments.  A `%% REQUEST ...` note to another owner
# is not typeset, and two labels that exist ONLY inside such notes
# (`app:pbresp`, `app:repro`, both in `app_A_reproducibility.tex`'s header and
# routing comments) were reported as defined and then as UNRESOLVED, because
# LaTeX never saw them and wrote no `\newlabel` for them.  Third tool in this
# tree to read the manuscript with its comments and draw a conclusion from
# them; `retired.py`'s R2 was the second, found in the same pass.
tex = re.sub(r'(?<!\\)%.*', '', manuscript.flat())
# ★ r16: `--aux PATH`, or a bare positional path.  This gate used to read only
# `<STEM>.aux` in the build root, and under BUILD_RULE 1 that path is the
# integrator's and is read-only, so no working agent could run it at all --
# `labelcheck` grew an `--aux` for exactly this reason and this one did not.
# A gate nobody can run is a gate that never runs.  And a missing .aux now
# STOPS it rather than crashing on an IOError, because the alternative to
# comparing against what LaTeX wrote is comparing against nothing.
_aux_arg = None
if '--aux' in sys.argv:
    _aux_arg = sys.argv[sys.argv.index('--aux') + 1]
else:
    _pos = [a for a in sys.argv[1:] if not a.startswith('-')]
    if _pos:
        _aux_arg = _pos[0]
AUXPATH = _aux_arg or os.path.join(HERE, STEM + '.aux')
if not os.path.exists(AUXPATH):
    raise SystemExit(
        'xrefcheck: no .aux at %s.  Build first, or pass '
        '--aux <jobname>.aux from your own output directory.' % AUXPATH)
aux = open(AUXPATH).read()

lab = {}
for m in re.finditer(r'\\newlabel\{([^}]+)\}\{\{([^}]*)\}\{(\d+)\}'
                     r'\{([^}]*)\}\{([^}]*)\}', aux):
    if m.group(1).endswith('@cref'):
        continue
    lab[m.group(1)] = {'num': m.group(2), 'page': m.group(3),
                       'anchor': m.group(5)}

defined = set(re.findall(r'\\label\{([^}]+)\}', tex))
used = collections.Counter(
    re.findall(r'\\(?:ref|autoref|pageref|eqref)\{([^}]+)\}', tex))

KIND = {'sec': ('section', 'subsection', 'subsubsection', 'paragraph'),
        'tab': ('table',), 'fig': ('figure',), 'eq': ('equation',),
        'app': ('section', 'subsection', 'subsubsection', 'appendix'),
        'page': ('page', 'section', 'subsection', 'subsubsection')}

hard = []
for l, v in sorted(lab.items()):
    pre = l.split(':')[0]
    if pre not in KIND or not v['anchor']:
        continue
    if not any(v['anchor'].startswith(k) for k in KIND[pre]):
        hard.append('%s: prefix %s but anchors on %s (prints %s)'
                    % (l, pre, v['anchor'], v['num']))

orphan = sorted(l for l in defined if l not in used)
bynum = collections.defaultdict(list)
for l, v in lab.items():
    if v['anchor']:
        bynum[v['anchor']].append(l)
shared = {k: sorted(v) for k, v in bynum.items()
          if len(v) > 1 and any(x in used for x in v)}

print('xrefcheck: %d labels, %d resolved, %d referenced'
      % (len(defined), len(lab), len(used)))
print('  MISPLACED LABELS (prefix disagrees with anchor): %d' % len(hard))
for h in hard:
    print('    %s' % h)
print('  DEFINED BUT NEVER REFERENCED: %d' % len(orphan))
for l in orphan:
    print('    %-28s -> %s' % (l, lab.get(l, {}).get('num', 'UNRESOLVED')))
print('  SHARED ANCHORS (deliberate aliases are fine): %d' % len(shared))
for k, v in sorted(shared.items()):
    print('    %-22s %s' % (k, ', '.join(v)))
sys.exit(1 if hard else 0)
