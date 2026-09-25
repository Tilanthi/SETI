#!/usr/bin/env python3
"""R2-M6 gate: catch survey counts written as literal words or digits in the
PROSE, where they cannot track the generated macros.

Referee 2: "The authors state that every count is generated from macros. The
prose clearly is not... the regeneration script should be extended to check
numbers in the prose as well as the tables."

That is exactly how this paper came to say it had "one" unattributed event
in three places while the catalogue said four: the count grew, the macros
followed, and three hand-written sentences did not.

This gate is deliberately narrow.  A general number checker would drown in
false positives, so it looks only for a small set of survey quantities whose
value is fixed by a macro, written near a number word or digit in the prose.
Each hit is reported with the macro's current value so a human can judge.
Exit status 1 on a hit whose literal disagrees with the macro.
"""
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
TEX = os.path.join(HERE, 'technosignatures_40pc_v4.01.tex')

WORD = {'no': 0, 'zero': 0, 'one': 1, 'two': 2, 'three': 3, 'four': 4,
        'five': 5, 'six': 6, 'seven': 7, 'eight': 8, 'nine': 9, 'ten': 10}

# phrase fragment -> macro whose value the phrase must agree with
CHECKS = [
    (r'(\w+)\s+unattributed(?:\s+stage-1)?\s+(?:event|window|crossing)s?',
     'NStageOneUnattrib'),
    (r'(\w+)\s+stage-1\s+flagged\s+windows?\b', 'NStageOneWin'),
    (r'and\s+has\s+(\w+)\b', 'NStageOneUnattrib'),
]

macros = {}
for fn in sorted(os.listdir(HERE)):
    if fn.startswith('survey_numbers') and fn.endswith('.tex'):
        for line in open(os.path.join(HERE, fn)):
            m = re.match(r'\\newcommand\{\\(\w+)\}\{([^}]*)\}', line.strip())
            if m:
                macros[m.group(1)] = m.group(2)

tex = open(TEX, errors='ignore').read()
# strip comments and the generated inputs; only prose is in scope
tex = re.sub(r'(?<!\\)%.*', '', tex)

bad = 0
for pat, mac in CHECKS:
    val = macros.get(mac)
    if val is None or not val.isdigit():
        continue
    want = int(val)
    for m in re.finditer(pat, tex):
        tok = m.group(1).lower().strip('\\{}')
        if tok in WORD:
            got = WORD[tok]
        elif tok.isdigit():
            got = int(tok)
        else:
            continue          # a macro or an adjective, which is fine
        # "adds no unattributed event" is a statement about what a NEW
        # sample contributes, not about the survey total
        pre = tex[max(0, m.start() - 24):m.start()].lower()
        if re.search(r'\b(adds|added|contribut\w*|introduc\w*)\s*$', pre):
            continue
        if got != want:
            ctx = ' '.join(tex[max(0, m.start() - 70):m.end() + 20].split())
            print('  LITERAL %r where \\%s = %s' % (tok, mac, val))
            print('     ...%s...' % ctx)
            bad += 1

print('prosenum: %d literal(s) disagreeing with a macro' % bad)
sys.exit(1 if bad else 0)
