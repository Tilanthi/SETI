#!/usr/bin/env python3
"""Gate: no two generators may write the same survey_numbers_roundNN.tex,
and every such file the manuscript \\inputs must have exactly one writer.

Written after an occurrence-rate generator added in the v3.87 cycle
silently overwrote survey_numbers_round47.tex, which stageonenull_v387.py
owns. The build did not complain, because the macros it destroyed were
still in the .aux from the previous run. Nothing in gate.sh could see it.
The only defence is to check the writers, so this does.

Exit status 1 on any collision, missing writer, or orphan file.
"""
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
PAT = re.compile(r'survey_numbers_round(\d+)\.tex')

writers = {}
for fn in sorted(os.listdir(HERE)):
    if not fn.endswith('.py') or fn == os.path.basename(__file__):
        continue
    src = open(os.path.join(HERE, fn), errors='ignore').read()
    # A generator "writes" a round file if it names it in a write context.
    for mm in PAT.finditer(src):
        name = mm.group(0)
        ctx = src[max(0, mm.start() - 260):mm.end() + 60]
        if ("'w'" in ctx or '"w"' in ctx or '.write' in ctx
                or 'OUT =' in ctx or 'OUT=' in ctx):
            writers.setdefault(name, set()).add(fn)

# Rounds whose generator has been retired are shipped as frozen copies and
# restored by make_all.sh; those have a legitimate single "writer".
FROZEN = os.path.join(HERE, 'frozen_macros')
if os.path.isdir(FROZEN):
    for fn in sorted(os.listdir(FROZEN)):
        if PAT.fullmatch(fn):
            writers.setdefault(fn, set()).add('frozen_macros/ (retired)')

tex = [f for f in os.listdir(HERE)
       if f.startswith('technosignatures_') and f.endswith('.tex')]
inputs = set()
for f in tex:
    body = open(os.path.join(HERE, f), errors='ignore').read()
    for mm in re.finditer(r'\\input\{(survey_numbers_round\d+)\}', body):
        inputs.add(mm.group(1) + '.tex')

fail = 0
for name in sorted(writers, key=lambda n: int(PAT.match(n).group(1))):
    who = sorted(writers[name])
    if len(who) > 1:
        print('COLLISION %s written by %s' % (name, ', '.join(who)))
        fail += 1

for name in sorted(inputs, key=lambda n: int(PAT.match(n).group(1))):
    if name not in writers:
        print('NO WRITER %s is \\input by the manuscript but no generator '
              'writes it' % name)
        fail += 1
    if not os.path.exists(os.path.join(HERE, name)):
        print('MISSING   %s is \\input by the manuscript and does not exist'
              % name)
        fail += 1

for name in sorted(writers, key=lambda n: int(PAT.match(n).group(1))):
    if name not in inputs:
        print('ORPHAN    %s is generated but never \\input' % name)
        fail += 1

print('roundcollide: %d round files, %d inputs, %d problems'
      % (len(writers), len(inputs), fail))
sys.exit(1 if fail else 0)
