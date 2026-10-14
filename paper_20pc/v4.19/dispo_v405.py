#!/usr/bin/env python3
"""Round 90 (v4.05, DECISIONS_R8 D4): the computed dispositions, and every
place they disagree with the hand-assigned ones.

The survey's published dispositions are a hand-written five-entry literal.
They were never computed from the line mask, in any frame, and earlier
versions of this paper implied that they were.  v4.05 computes a disposition
for all \\NCrossings{} threshold crossings from the frozen 15-transition mask
evaluated topocentrically -- the list and the frame the search actually ran --
and keeps the hand judgement in its own labelled column.  `v342_calc.py` owns
the computation and the columns; this generator owns the REPORT, because a
disagreement between the two is a result and must be printed crossing by
crossing rather than reconciled.

Two disagreements exist and both are in the release:

  (1) six crossings the frozen mask attributes ship with a BLANK disposition,
      because the survey only ever dispositioned the windows the rank screen
      let through.  It is a coverage gap, not an error of attribution: every
      one of the six is correctly attributed by the computed rule, and three
      of them are the HD 285968 CO(2-1) events the round-6 campaign localised
      in three independent blocks.

  (2) the old (star, band) key is not a key.  beta Pic band 6 holds seven
      crossings in two basebands; applied to all of them -- which is what a
      (star, band) literal asserts -- the map labels two crossings 3,793 and
      3,898 km/s from CS(5-4) "circumstellar CO".

Where both a computed and a hand label exist they AGREE in content for every
crossing; the hand string carries extra information (the second-epoch test)
that the mask cannot know, which is exactly the material D4 says to keep.

-> survey_numbers_round90.tex, tab_dispo_v405.tex
"""
import csv
import os

from star_alias import designation

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, 'survey_numbers_round90.tex')
TAB = os.path.join(HERE, 'tab_dispo_v405.tex')
ROWS = [r for r in csv.DictReader(open(os.path.join(
    HERE, 'per_target_results_v3.99.csv'))) if r['crossing'] == 'True']

C_KMS = 299792.458

# The frozen list the SEARCH ran, parsed out of the generator that owns it so
# the two cannot drift apart.  Parsing beats importing: importing v342_calc
# would rebuild the catalogue this script reads.
_src = open(os.path.join(HERE, 'v342_calc.py')).read()
_i = _src.index('CAT_OLD = {')
CAT_OLD = eval(_src[_i + len('CAT_OLD = '):_src.index('}', _i) + 1])  # noqa: S307
assert len(CAT_OLD) == 15, len(CAT_OLD)
# The hand map, both keyings, from the same place.
_j = _src.index('DISPOSITION_HAND_OLDKEY = {')
HAND_OLD = eval(_src[_j + len('DISPOSITION_HAND_OLDKEY = '):
                     _src.index('\n}', _j) + 2])                      # noqa: S307
_k = _src.index('\nDISPOSITION_HAND = {')
HAND = eval(_src[_k + len('\nDISPOSITION_HAND = '):
                 _src.index('\n}', _k) + 2])                          # noqa: S307
assert len(HAND_OLD) == 5 and len(HAND) == 12, (len(HAND_OLD), len(HAND))

M = {}


def m(k, v):
    M[k] = v


def tex_name(s):
    return designation(s)


# ------------------------------------------------------------ the two sets --
attr = [r for r in ROWS if r['disposition_computed'].startswith('attributed')]
rankd = [r for r in ROWS if float(r['star_snr']) >= 5.0
         and float(r['star_snr']) > float(r['ctrl_max_snr'])]
blank_attr = [r for r in attr if not r['disposition']]
shipped = [r for r in ROWS if r['disposition']]
# The rank-flagged crossings the mask does NOT attribute: the two the paper
# carries as unattributed.  Their computed and hand labels agree in content.
rank_unattr = [r for r in rankd
               if not r['disposition_computed'].startswith('attributed')]

# ★ These are the numbers the prose quotes.  If the catalogue moves, the
# assertion fires rather than the sentence going quietly stale.
assert len(ROWS) == 56, len(ROWS)
assert len(attr) == 16, len(attr)
assert len(blank_attr) == 6, [(r['star_name'], r['eb']) for r in blank_attr]
assert len(shipped) == 12, len(shipped)
assert len(rank_unattr) == 2, [(r['star_name'], r['eb']) for r in rank_unattr]
# ★ The claim the paper makes about the two columns: wherever BOTH exist they
# agree.  A computed "unattributed" against a hand string naming a molecule,
# or the reverse, would be a substantive disagreement and would have to be
# written up as one, so it must fail the build instead of being averaged away.
_conflict = [(r['star_name'], r['eb'], r['disposition'],
              r['disposition_computed'])
             for r in shipped
             if ('CO' in r['disposition'])
             != r['disposition_computed'].startswith('attributed')]
assert not _conflict, _conflict
# ★ And the computed column must be populated for every crossing, or the
# "all 56" in the prose is false.
assert all(r['disposition_computed'] for r in ROWS)

m('DispoNCross', '%d' % len(ROWS))
m('DispoNAttr', '%d' % len(attr))
m('DispoNUnattr', '%d' % (len(ROWS) - len(attr)))
m('DispoNAttrRank', '%d' % len([r for r in attr if r in rankd]))
m('DispoNBlankAttr', '%d' % len(blank_attr))
m('DispoNRankUnattr', '%d' % len(rank_unattr))
m('DispoNStars', '%d' % len({r['star_name'] for r in blank_attr}))

# --------------------------------------------------------- the disagreement --
# One row per disagreement, in the order the catalogue carries them.
L = ['%% GENERATED by dispo_v405.py -- do not hand-edit.\n',
     '%% Every crossing where the computed disposition and the hand-assigned\n'
     '%% one do not say the same thing about the same object.\n',
     '\\begin{tabular}{@{}l@{~}l@{~}c@{~}r@{~}l@{~}r@{~~}l@{}}\n',
     '\\hline\n',
     'Star & block & B & $T_\\star$ & mask & $\\Delta v$ & shipped '
     'disposition \\\\\n',
     '\\hline\n']


def _short_eb(eb):
    return eb.replace('A002_', '').replace('_', '\\_')


def _line_tex(k):
    """Isotopologue prefixes are numerals in the catalogue and superscripts
    in print; nothing else in the frozen mask needs marking up."""
    for iso in ('13', '18'):
        if k.startswith(iso):
            return '$^{%s}$%s' % (iso, k[len(iso):])
        if k.startswith('C' + iso):                      # C18O
            return 'C$^{%s}$%s' % (iso, k[1 + len(iso):])
    return k


def _dv(r):
    k = r['nearest_line']
    if k not in CAT_OLD:
        c = [x for x in CAT_OLD if x.split('(')[0] == k]
        k = c[0] if len(c) == 1 else k
    return float(r['line_offset_kms']), k


rows_tab = []
for r in sorted(blank_attr, key=lambda r: (r['star_name'], r['eb'])):
    dv, k = _dv(r)
    rows_tab.append((tex_name(r['star_name']), _short_eb(r['eb']), r['band'],
                     '%.2f' % float(r['star_snr']), _line_tex(k), '%+.1f' % dv,
                     '\\emph{(blank)}'))
for r in sorted(rank_unattr, key=lambda r: (r['star_name'], r['eb'])):
    dv, k = _dv(r)
    rows_tab.append((tex_name(r['star_name']), _short_eb(r['eb']), r['band'],
                     '%.2f' % float(r['star_snr']), _line_tex(k), '%+.1f' % dv,
                     r['disposition']))
for t in rows_tab:
    L.append(' & '.join(t) + ' \\\\\n')
L.append('\\hline\n\\end{tabular}\n')
# ★ A table that prints no rows would let the prose claim a disagreement list
# that does not exist.
assert len(rows_tab) == len(blank_attr) + len(rank_unattr) == 8, len(rows_tab)
m('DispoNTabRows', '%d' % len(rows_tab))
open(TAB, 'w').writelines(L)

# --------------------------------------- what the old key would have labelled --
# Re-run the old map ungated: every crossing of every (star, band) pair it
# names.  This is the measurement behind "the key is not a key".
old_reach = [r for r in ROWS
             if (r['star_name'], int(r['band'])) in HAND_OLD
             and (r['star_name'], r['eb'],
                  round(float(r['flo_GHz']), 6)) not in HAND]
mislabel = [r for r in old_reach
            if 'CO' in HAND_OLD[(r['star_name'], int(r['band']))]
            and not r['disposition_computed'].startswith('attributed')]
assert len(mislabel) == 2, [(r['star_name'], r['eb']) for r in mislabel]
m('DispoOldReach', '%d' % len(old_reach))
m('DispoOldMislabel', '%d' % len(mislabel))
_mm = sorted(abs(float(r['line_offset_kms'])) for r in mislabel)
m('DispoMislabelLo', '{:,}'.format(int(round(_mm[0]))))
m('DispoMislabelHi', '{:,}'.format(int(round(_mm[-1]))))
m('DispoMislabelLine', mislabel[0]['nearest_line'].replace('(', '($')
  .replace('-', '{\\to}').replace(')', '$)'))
m('DispoBetPicBSix', '%d' % len([r for r in ROWS
                                 if r['star_name'] == 'bet Pic'
                                 and r['band'] == '6']))
m('DispoBetPicBSixCO', '%d' % len([r for r in ROWS
                                   if r['star_name'] == 'bet Pic'
                                   and r['band'] == '6'
                                   and r['nearest_line'] == 'CO(2-1)']))
# ★ The sentence says the two basebands are about 11 GHz apart.  Measure it.
_bp = sorted({round(float(r['flo_GHz'])) for r in ROWS
              if r['star_name'] == 'bet Pic' and r['band'] == '6'})
m('DispoBetPicSplitGHz', '%d' % (max(_bp) - min(_bp)))
assert max(_bp) - min(_bp) > 5, _bp

with open(OUT, 'w') as fh:
    fh.write('%% GENERATED by dispo_v405.py -- do not hand-edit.\n')
    for k in sorted(M):
        fh.write('\\newcommand{\\%s}{%s}\n' % (k, M[k]))

print('dispo_v405 (round 90): %d crossings, %d attributed by the frozen '
      '%d-line mask topocentrically at +-50 km/s, %d of those rank-screened'
      % (len(ROWS), len(attr), len(CAT_OLD), len([r for r in attr if r in rankd])))
print('  the shipped column carries %d strings from %d hand judgements and '
      'leaves %d mask-attributed crossings blank, on %d stars'
      % (len(shipped), len(HAND_OLD), len(blank_attr),
         len({r['star_name'] for r in blank_attr})))
print('  the (star, band) key reaches %d crossings it was not written about, '
      'and would mislabel %d of them by %s-%s km/s'
      % (len(old_reach), len(mislabel), M['DispoMislabelLo'],
         M['DispoMislabelHi']))
print('  -> %s (%d macros), %s (%d rows)'
      % (os.path.basename(OUT), len(M), os.path.basename(TAB), len(rows_tab)))
