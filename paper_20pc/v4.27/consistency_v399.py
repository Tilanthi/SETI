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
import manuscript  # v4.10: the manuscript is split into sections/
tex = manuscript.flat()


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
# The frozen trio is always in the text. The corrected trio may be partly
# retired once the prose stops quoting all three, so read it from the
# generator's own JSON, which always carries it.
import json as _json
_pj = os.path.join(HERE, 'primary_v399.json')
_pri = _json.load(open(_pj)) if os.path.exists(_pj) else {}
TRIOS = [(('NStageOneWin', 'NStageOneLine', 'NStageOneUnattrib'), 'frozen',
          None),
         (None, 'radius-corrected',
          (_pri.get('n_corrected'), _pri.get('n_corrected')
           and _pri['n_corrected'] - _pri['n_corrected_unattrib'],
           _pri.get('n_corrected_unattrib')))]
for trio, label, direct in TRIOS:
    if direct is not None:
        tot, a, b = direct
    else:
        tot, a, b = (mac(x) for x in trio)
    if None in (tot, a, b):
        print('MISSING values for the %s trio' % label)
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

# 4. an attribution is never scoped to the star's velocity alone.
# The mask is a +-\MaskHalfKms km/s interval ABOUT the star's velocity, and 6
# of the 21 coincidences are interstellar gas at its own LSR velocity, so a
# sentence saying a crossing is attributed to a transition AT the star's
# velocity drops the width and the interstellar half at once.  What is pinned
# is the invariant and not a wording: wherever ONE sentence carries both an
# attribution and the star's velocity, that sentence must also carry the mask
# half-width macro or the word interstellar.  4b is what keeps 4a from going
# vacuous -- a tree that deleted the mask's own definition would otherwise
# satisfy 4a by having nothing left to measure it against.
_DRV = int((sys.argv[sys.argv.index('--drive') + 1:] or ['0'])[0]
           if '--drive' in sys.argv else 0)
ATTRV = re.compile(r"attribut[a-z]*[^.]{0,200}?star's(?: own)? velocity"
                   r"|star's(?: own)? velocity[^.]{0,200}?attribut[a-z]*")
SCOPED = re.compile(r'\\MaskHalfKms|interstellar')
prose = re.sub(r'(?m)(?<!\\)%.*$', '', tex)
if _DRV == 1:                      # 4a: the defect itself
    prose = ("\\EvNAttrQp{} of those are attributed to a catalogued "
             "molecular transition at the star's own velocity. " + prose)
if _DRV == 2:                      # 4b: the mask's definition removed
    prose = prose.replace('\\MaskHalfKms', 'MASKWIDTH')
_sents = re.split(r'(?<=[.!?])\s+', prose)
_loose = [' '.join(s.split())[:80] for s in _sents
          if ATTRV.search(s) and not SCOPED.search(s)]
_defines = sum(1 for s in _sents
               if '\\MaskHalfKms' in s and 'star' in s)
for _s in _loose:
    print("ATTRIBUTION SCOPED TO THE STAR'S VELOCITY ALONE: %s" % _s)
fail += len(_loose)
if not _defines:
    print('NO SENTENCE GIVES THE MASK HALF-WIDTH ABOUT THE STAR, so the '
          'clause above has nothing to be measured against')
    fail += 1
else:
    print('  attribution scope   %d sentence(s) give the mask half-width '
          'about the star; %d attribute at its velocity alone'
          % (_defines, len(_loose)))

print('consistency_v399: %d problem(s)' % fail)
sys.exit(1 if fail else 0)
