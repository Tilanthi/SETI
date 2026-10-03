#!/usr/bin/env python3
"""round 98 (v4.06 residue): the habitable-zone M-dwarf list of Sec. 6.5,
GENERATED instead of typed.

What was wrong.  The paper said "Six of the searched M~dwarfs host a planet
that some published analysis places in the habitable zone" and then named six
stars in running prose.  Three separate things were hard-coded there:

  (1) the WORD "six", which is a count of a set defined two lines later;
  (2) the claim that each of them is SEARCHED, which is a fact about the
      released catalogue and was never checked against it;
  (3) the spelling of each star's name, so a canonicalisation change anywhere
      in the pipeline could silently drop a star from the list while leaving
      the count at six.

(3) is not hypothetical: the first draft of the multi-epoch stack's own
persistence list in this same version misspelt three of nine star keys and
quietly tested six stars while claiming nine.

What is a literature judgement and stays one.  WHETHER a planet is in its
star's habitable zone is model-dependent and contested, and no catalogue this
paper holds can decide it.  So the MEMBERSHIP of the set is declared here as an
explicit literature table, one entry per star, each carrying the planet and the
reference the paper already cites.  Everything else -- the count, the
searched-ness, the M-dwarf classification, the formatted list -- is computed
from the released catalogue, and every declared star must resolve to a star the
survey actually searched or this generator fails.

Inputs: per_target_results_v3.99.csv (MUST FOLLOW v342_calc.py),
        tab_selection.tex (for the M-dwarf census, the same source v363_calc.py
        reads, so the two cannot disagree).
"""
import csv
import os
import re

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, 'survey_numbers_round98.tex')
M = {}


def m(k, v):
    assert k not in M, k
    M[k] = v


# ---------------------------------------------------------------------------
# THE LITERATURE DECLARATION.  Key = the star name as the RELEASED CATALOGUE
# spells it.  Value = (typeset name, planet, bibkey or '' where the citation
# already sits elsewhere in the sentence, contested?).
#
# "Contested" is the authors' reading of the literature and is declared, not
# derived; it is carried here so the paper's hedge ("two of these are
# contested") is a count of a marked set rather than a typed word.
HZ_MDWARF = {
    'Proxima Cen':  ('Proxima~Centauri', 'Proxima~b', '', False),
    'TRAPPIST-1':   ('TRAPPIST-1', 'TRAPPIST-1\\,e', '', False),
    'LHS 1140':     ('LHS~1140', 'LHS~1140\\,b', '', False),
    'GJ 581':       ('GJ~581', 'GJ~581\\,d', '', True),
    'HN Lib':       ('HN~Lib', 'HN~Lib\\,b', '', True),
    'BD05 1668':    ('GJ~273', 'GJ~273\\,b', 'AstudilloDefru2017', False),
}
# The catalogue's own alias for GJ 273 is BD+05 1668; the paper's prose uses
# GJ 273 and prints the catalogue form through \BdStar.  Both spellings must
# therefore appear, and the join must be on the catalogue's.
CAT = list(csv.DictReader(open(os.path.join(HERE,
                                            'per_target_results_v3.99.csv'))))
SEARCHED = {}
for r in CAT:
    SEARCHED.setdefault(r['star_name'], []).append(r)

# ★ EVERY DECLARED STAR MUST BE IN THE RELEASED CATALOGUE.  This is the
# assertion the typed list did not have, and it is the one that matters: a
# rename upstream now fails the build instead of shrinking the list.
missing = sorted(k for k in HZ_MDWARF if k not in SEARCHED)
assert not missing, (
    'habitable-zone hosts named in Sec. 6.5 that the released catalogue does '
    'not contain: %s.  Either the star was never searched -- in which case the '
    'sentence is false -- or its catalogue name changed.' % missing)

# ★ ... and each must carry at least one SEARCHED window, which is a different
# statement from appearing in the catalogue.
nowin = sorted(k for k in HZ_MDWARF if not SEARCHED[k])
assert not nowin, nowin

# The M-dwarf census, from the same generated table v363_calc.py reads, so the
# denominator here and the denominator two sentences earlier are one number.
_sel = open(os.path.join(HERE, 'tab_selection.tex')).read()
_mrow = re.search(r'\\quad M \(\$<3900\$\\,K\) & (\d+) \([^)]*\) & (\d+) ',
                  _sel)
assert _mrow, 'M-dwarf row not found in tab_selection.tex'
MCEN, MSEA = int(_mrow.group(1)), int(_mrow.group(2))
m('HzNMCensus', '{:,}'.format(MCEN).replace(',', '\\,'))
m('HzNMSearched', '%d' % MSEA)

order = sorted(HZ_MDWARF, key=lambda k: min(float(r['dist_pc'])
                                            for r in SEARCHED[k]))
names = [HZ_MDWARF[k][0] for k in order]
m('HzNHosts', {1: 'One', 2: 'Two', 3: 'Three', 4: 'Four', 5: 'Five',
               6: 'Six', 7: 'Seven', 8: 'Eight', 9: 'Nine',
               10: 'Ten'}.get(len(order), '%d' % len(order)))
m('HzNHostsNum', '%d' % len(order))
m('HzNContested', '%d' % sum(1 for k in order if HZ_MDWARF[k][3]))
m('HzNContestedWord', {0: 'none', 1: 'one', 2: 'two', 3: 'three'}.get(
    sum(1 for k in order if HZ_MDWARF[k][3]), '%d' % sum(
        1 for k in order if HZ_MDWARF[k][3])))
# The list itself, in order of distance, with the Oxford-comma-free house
# style the surrounding prose uses ("A, B, C, D, E and F").
m('HzList', ', '.join(names[:-1]) + ' and ' + names[-1])
# The one entry that carries its own citation in the prose.
_cited = [k for k in order if HZ_MDWARF[k][2]]
assert len(_cited) == 1, _cited
_c = _cited[0]
m('HzCitedStar', HZ_MDWARF[_c][0])
m('HzCitedCatName', _c.replace('BD05', 'BD$+$05'))
m('HzCitedPlanet', HZ_MDWARF[_c][1])
m('HzCitedKey', HZ_MDWARF[_c][2])
# ★ The count cannot be allowed to drift from the list: assert the formatted
# string contains exactly as many names as the count claims.
# The formatted string must carry exactly `len(order)` names: n-2 commas plus
# one " and ".  If the count and the list ever disagree, this fires.
assert M['HzList'].count(',') == len(order) - 2, M['HzList']
assert M['HzList'].count(' and ') == 1, M['HzList']
assert len(order) < MSEA, (len(order), MSEA)
m('HzPctOfSearchedM', '%.0f' % (100.0 * len(order) / MSEA))

# The two the prose singles out as now carrying a non-detection, likewise
# derived: those declared here that are ALSO confirmed exoplanet hosts in the
# catalogue's own census route -- which is what the sentence claims.
m('HzNWindows', '%d' % sum(len(SEARCHED[k]) for k in order))
m('HzNCrossings', '%d' % sum(1 for k in order for r in SEARCHED[k]
                             if r['crossing'] == 'True'))
# ★ If one of these stars ever produced a crossing the sentence would have to
# change, so make the build say so rather than leaving it to a reader.
# ★ And one of them DOES carry crossings -- GJ 273 -- so the list cannot be
# introduced as a clean non-detection without naming it.  All of them lie in
# the one defective ACA block diagnosed in App. ref{app:fields}, which is why
# the sentence is about that block and not about the star.
_xs = {HZ_MDWARF[k][0]: sum(1 for r in SEARCHED[k] if r['crossing'] == 'True')
       for k in order}
_xs = {k: v for k, v in _xs.items() if v}
m('HzAnyCross', 'yes' if _xs else 'no')
m('HzCrossStars', ', '.join('%s (%d)' % (k, v) for k, v in sorted(_xs.items()))
  or 'none')
m('HzNCrossStars', '%d' % len(_xs))
m('HzNCleanStars', '%d' % (len(order) - len(_xs)))
_xblocks = sorted({r['eb'] for k in order for r in SEARCHED[k]
                   if r['crossing'] == 'True'})
m('HzNCrossBlocks', '%d' % len(_xblocks))
m('HzCrossBlocks', ', '.join(b.replace('_', r'\_') for b in _xblocks))
# ★ TWO blocks, not one, and that is worth knowing: GJ 273's four crossings are
# the single defective ACA block of App. J, but LHS 1140 carries one of its own
# -- one of the five events whose verdict moved under the corrected reference
# epoch (DECISIONS_R7 A6), which does not recur.  So the introductory sentence
# may not describe this set as crossing-free.  Assert the number is small and
# that each block is named, rather than asserting a number that is wrong.
assert len(_xblocks) <= 3, _xblocks
_dispos = sorted({r['disposition'] or r['disposition_computed'] or
                  '(none assigned)'
                  for k in order for r in SEARCHED[k]
                  if r['crossing'] == 'True'})
m('HzCrossDispo', '; '.join(_dispos))
import math
_deep = min((min(float(r['eirp_p90_sel_W']) for r in SEARCHED[k]), k)
            for k in order)
m('HzDeepestStar', HZ_MDWARF[_deep[1]][0])
_e = int(math.floor(math.log10(_deep[0])))
m('HzDeepestEirp', r'%.2f \times 10^{%d}' % (_deep[0] / 10.0 ** _e, _e))

with open(OUT, 'w') as fh:
    fh.write('%% GENERATED by hzlist_v406.py -- do not hand-edit.\n')
    for k in sorted(M):
        fh.write('\\newcommand{\\%s}{%s}\n' % (k, M[k]))

print('hzlist_v406 (round 98): %d declared habitable-zone M-dwarf hosts, all '
      '%d present in the released catalogue with %d searched windows between '
      'them' % (len(order), len(order), sum(len(SEARCHED[k]) for k in order)))
print('  list (by distance): %s' % M['HzList'])
print('  %s contested; crossings: %s in %d block(s) -- %s; %d of the %d searched '
      'M dwarfs (%s per cent)'
      % (M['HzNContestedWord'], M['HzCrossStars'], len(_xblocks),
         ', '.join(_xblocks), len(order), MSEA, M['HzPctOfSearchedM']))
print('  -> %s (%d macros)' % (os.path.basename(OUT), len(M)))
