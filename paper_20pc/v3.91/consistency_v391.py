#!/usr/bin/env python3
"""Gate added for referee 2's point 1: the paper must not assert two
different primary statistics or two different headline counts.

v3.89 shipped with S4.2 saying the radius-corrected statistic was primary
while Appendix G said it was not, and with the conclusions printing the
frozen CO count (9) beside the corrected totals (10, 2), so that
9 + 2 = 11 did not equal 10. Nothing in gate.sh could see either. This
checks both.
"""
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
STEM = [f[:-4] for f in os.listdir(HERE)
        if f.startswith('technosignatures_') and f.endswith('.tex')][0]
tex = open(os.path.join(HERE, STEM + '.tex')).read()


def mac(name):
    for fn in sorted(os.listdir(HERE)):
        if fn.startswith('survey_numbers_round') and fn.endswith('.tex'):
            m = re.search(r'\\newcommand\{\\%s\}\{([^}]*)\}' % name,
                          open(os.path.join(HERE, fn)).read())
            if m:
                return m.group(1)
    return None

fail = 0

# 1. the two count identities must close
for trio, label in (((('NStageOneWin', 'NStageOneLine', 'NStageOneUnattrib')),
                     'frozen'),
                    ((('PriNStageOne', 'PriNAttrib', 'PriNUnattrib')),
                     'radius-corrected')):
    tot, a, b = (mac(x) for x in trio)
    if None in (tot, a, b):
        print('MISSING macro in the %s trio: %s' % (label, trio))
        fail += 1
        continue
    if int(a) + int(b) != int(tot):
        print('IDENTITY BROKEN (%s): %s + %s != %s' % (label, a, b, tot))
        fail += 1
    else:
        print('  %-17s %s = %s + %s  OK' % (label, tot, a, b))

# 2. the paper must not claim both statistics are primary
AFFIRM = re.compile(r'(?<!do not )(?<!not )adopt(?:ed)? '
                    r'the radius-corrected[^.]{0,90}as (?:the )?primary')
DENY = re.compile(r'do not adopt the radius-corrected')
# a historical statement about an earlier version is not a claim
HIST = re.compile(r'earlier version[^.]{0,120}adopted it as the primary')
claims_corrected = bool(AFFIRM.search(tex)) and not bool(
    HIST.search(tex) and AFFIRM.search(tex) and
    AFFIRM.search(tex).start() > HIST.search(tex).start() - 200)
denies_corrected = bool(DENY.search(tex))
if claims_corrected and denies_corrected:
    print('CONTRADICTION: the text both adopts and rejects the '
          'radius-corrected statistic as primary')
    fail += 1
else:
    print('  primary statistic   %s' % (
        'radius-corrected' if claims_corrected else
        'frozen screen (corrected rejected)' if denies_corrected else
        'no explicit claim found'))

# 3. the abstract's counts must come from the primary trio
i = tex.index('\\begin{abstract}')
j = tex.index('\\end{abstract}')
abstract = tex[i:j]
uses_pri = any(x in abstract for x in ('\\PriNStageOne', '\\PriNAttrib',
                                       '\\PriNUnattrib'))
uses_frz = any(x in abstract for x in ('\\NStageOneWin', '\\NStageOneLine',
                                       '\\NStageOneUnattrib'))
if uses_pri and uses_frz:
    print('MIXED: the abstract quotes counts from BOTH statistics')
    fail += 1
elif denies_corrected and uses_pri:
    print('MISMATCH: the appendix rejects the corrected statistic but the '
          'abstract quotes its counts')
    fail += 1
else:
    print('  abstract uses      %s' % ('radius-corrected' if uses_pri
                                       else 'frozen screen' if uses_frz
                                       else 'neither'))

print('consistency_v391: %d problem(s)' % fail)
sys.exit(1 if fail else 0)
