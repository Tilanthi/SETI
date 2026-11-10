#!/usr/bin/env python3
r"""nofn_r35.py -- round 3560 (v4.35, N4, register A3): no "N of N" and no typed "both"/"five"/"sixth".

The prose printed "In 12 of 12 subsets", "in 9 of the 9 pairs", "on five of the 6 properties ... on the sixth"
and "whose 2 windows both lie inside it" -- each a pair of counts with a word between them that only one value
of the pair makes true.  This reads the two counts each clause is made of (as printed, from the numbers layer)
and writes the clause, so the words follow the counts:

  \BgConfInOf       "all 12" | "11 of the 12"            (\BgNConfIn of \BgNConf, bkg_r28)
  \TjUneqDriftOf    "all 9"  | "8 of the 9"              (\TjNUneqDrift of \TjNPair, pairs_v415)
  \RpCovOtherOf     "five of the six"                     (\RpNAxis - 1 of \RpNAxis, resp_r16)
  \RpCovWorstOrd    "sixth"                               (the remaining one, the ordinal of \RpNAxis)
  \UmALostWinClause "two windows both lie" | "one window lies" | "three windows all lie"
                                                          (\UmNWinALostWin, unmask_r26: every window of the one
                                                           system the mask leaves nothing of)

Reads only numbers/survey_numbers_round*.tex (never its own round); writes numbers/survey_numbers_round3560.tex.

  N1  every source count is a non-negative integer, k <= N, and N >= 1
  N2  each "of" clause says "all" exactly when k == N, and otherwise names both k and N
  N3  resp_r16 compares on RpNAxis properties and the worst is ONE of them: the matched count is RpNAxis - 1 and
      both are in the word table (a sixth property needs "sixth", not a typed one)
  N4  the lost system's window clause agrees in number with its count and uses "both" only for two

    python3 nofn_r35.py [--drive N]     N = 1..4: each perturbs one input in memory, prints FAILED and exits 1
                                        without writing a production path
"""
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROUND = 3560
DRIVE = int(sys.argv[sys.argv.index('--drive') + 1]) if '--drive' in sys.argv else None
OUT, FAIL = {}, []
WORD = ('no', 'one', 'two', 'three', 'four', 'five', 'six', 'seven', 'eight', 'nine', 'ten', 'eleven', 'twelve')
ORD = ('zeroth', 'first', 'second', 'third', 'fourth', 'fifth', 'sixth', 'seventh', 'eighth', 'ninth', 'tenth',
       'eleventh', 'twelfth')


def m(k, v):
    assert k.isalpha() and k not in OUT, k
    OUT[k] = v


def ck(label, ok, detail=''):
    print('  %-78s %s  %s' % (label[:78], 'PASS' if ok else 'FAIL', detail))
    if not ok:
        FAIL.append(label.split()[0])


def tv(name):
    """The printed value of \\name: its last non-empty definition, the same in every file that defines it."""
    pat = re.compile(r'\\(?:new|renew|provide)command\{\\%s\}\{(.*)\}\s*$' % name, re.M)
    vals = []
    for f in sorted(os.listdir(os.path.join(HERE, 'numbers'))):
        if f.startswith('survey_numbers') and f.endswith('.tex') and '_drive' not in f \
                and 'round%d' % ROUND not in f:
            vals += [v for v in pat.findall(open(os.path.join(HERE, 'numbers', f), errors='ignore').read()) if v]
    assert len(set(vals)) == 1, ('macro %s defined %d times: %s' % (name, len(vals), vals[:3]))
    return vals[0]


def ti(name):
    v = tv(name).replace('\\,', '')
    assert re.fullmatch(r'\d+', v), (name, v)
    return int(v)


def of_clause(k, n):
    return ('all %d' % n) if k == n else ('%d of the %d' % (k, n))


print('nofn_r35: round %d%s' % (ROUND, '' if DRIVE is None else '  (drive %d)' % DRIVE))

PAIRS = [('BgConfInOf', 'BgNConfIn', 'BgNConf'), ('TjUneqDriftOf', 'TjNUneqDrift', 'TjNPair')]
VAL = {n: ti(n) for _, a, b in PAIRS for n in (a, b)}
for n in ('RpNAxis', 'UmNWinALostWin'):
    VAL[n] = ti(n)
if DRIVE == 1:
    VAL['TjNUneqDrift'] = VAL['TjNPair'] + 1          # k > N
ck('N1 every source count is a non-negative integer, k <= N, N >= 1',
   all(v >= 0 for v in VAL.values()) and all(VAL[a] <= VAL[b] and VAL[b] >= 1 for _, a, b in PAIRS)
   and VAL['RpNAxis'] >= 2 and VAL['UmNWinALostWin'] >= 1,
   ', '.join('%s %d' % kv for kv in sorted(VAL.items())))

CL = {name: of_clause(VAL[a], VAL[b]) for name, a, b in PAIRS}
if DRIVE == 2:
    CL['BgConfInOf'] = '%d of the %d' % (VAL['BgNConf'], VAL['BgNConf'])    # an "N of N" again
ok2 = True
for name, a, b in PAIRS:
    k, n, c = VAL[a], VAL[b], CL[name]
    ok2 &= (c == 'all %d' % n) if k == n else (c == '%d of the %d' % (k, n))
    ok2 &= not re.fullmatch(r'(\d+) of the \1', c)
ck('N2 each "of" clause says "all" exactly when k == N, and otherwise names k and N',
   ok2, '; '.join('%s = "%s"' % (n_, CL[n_]) for n_, _, _ in PAIRS))
for name in CL:
    m(name, CL[name])

NAX = VAL['RpNAxis']
if DRIVE == 3:
    NAX = len(WORD)                                    # beyond the word table
ck('N3 the covariate comparison is on RpNAxis properties, one of them the worst: matched = RpNAxis - 1, '
   'both in the word and ordinal tables',
   2 <= NAX < len(WORD) and NAX < len(ORD), 'RpNAxis %d -> "%s of the %s", the %s'
   % (NAX, WORD[NAX - 1] if NAX - 1 < len(WORD) else '?', WORD[NAX] if NAX < len(WORD) else '?',
      ORD[NAX] if NAX < len(ORD) else '?'))
if 2 <= NAX < len(WORD):
    m('RpCovOtherOf', '%s of the %s' % (WORD[NAX - 1], WORD[NAX]))
    m('RpCovWorstOrd', ORD[NAX])

NW = VAL['UmNWinALostWin']
UCL = ('one window lies' if NW == 1 else 'two windows both lie' if NW == 2
       else '%s windows all lie' % (WORD[NW] if NW < len(WORD) else '%d' % NW))
if DRIVE == 4:
    UCL = 'three windows both lie'
ck('N4 the lost system\'s window clause agrees with its count: "both" only for two, singular only for one',
   (('both' in UCL) == (NW == 2)) and (UCL.startswith('one window ') == (NW == 1))
   and UCL.split()[0] == (WORD[NW] if NW < len(WORD) else '%d' % NW),
   '%d -> "%s"' % (NW, UCL))
m('UmALostWinClause', UCL)

if FAIL:
    print('\nFAILED: %s' % ', '.join(FAIL))
    sys.exit(1)
if DRIVE is not None:
    print('nofn_r35: drive %d passed every check -- it did NOT fire' % DRIVE)
    sys.exit(0)
with open(os.path.join(HERE, 'numbers/survey_numbers_round%d.tex' % ROUND), 'w') as fh:
    fh.write('%% GENERATED by nofn_r35.py (round %d) -- do not hand-edit.\n' % ROUND)
    for k in sorted(OUT):
        fh.write('\\newcommand{\\%s}{%s}\n' % (k, OUT[k]))
print('nofn_r35: %d macros written (round %d)' % (len(OUT), ROUND))
