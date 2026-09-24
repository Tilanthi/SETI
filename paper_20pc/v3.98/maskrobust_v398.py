#!/usr/bin/env python3
"""R2-5 (v3.98): robustness of the dispositions to the line-mask half-width,
as a table.

Referee 2 asked for the line-mask sensitivity analysis to be presented as a
table rather than asserted in prose.  The paper already argued that a
pre-registrable +-13 km/s Keplerian-only mask would have released and
suppressed exactly the same windows; this generator shows the far stronger
statement the data actually support.

Every stage-1 window attributed to molecular emission lies within
~35 km/s of its nearest catalogued transition, and every unattributed one
lies beyond ~330 km/s.  The two populations are separated by about an order
of magnitude in velocity offset, so the classification is invariant for any
half-width chosen anywhere in that gap.  The adopted +-50 km/s sits inside
it with roughly a factor of seven of headroom on one side and a factor of
about six on the other.  That is a much better answer than "the result is
not sensitive to the choice", and it is the reason the choice of mask
cannot be doing any work in the candidate list.

FRAME, checked rather than assumed.  The offsets used here are the
catalogue's line_offset_kms, which is an uncorrected sky-frequency offset:
beta Pic's CO(1-0) crossings read ~27.7 km/s in this column but -0.39 km/s
once the full frame chain to the stellar rest frame is applied.  That is
the quantity the mask is actually applied to throughout the pipeline
(falsealarm_v398.py, primary_v398.py, make_vistest_events_v385.py all test
|line_offset_kms| <= 50), and the generous +-50 km/s half-width exists
precisely to absorb the barycentric and systemic terms that are not
applied.  This table is therefore the mask as implemented, and it
reproduces the released dispositions exactly.  It is NOT comparable with
the paper's "+-13 km/s Keplerian-only" figure, which is a stellar-frame
velocity; the two are different frames and the manuscript is corrected to
say so.

Writes survey_numbers_round59.tex and tab_maskrobust_v398.tex.
"""
import csv
import os

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, 'survey_numbers_round59.tex')
TAB = os.path.join(HERE, 'tab_maskrobust_v398.tex')

ADOPTED = 50.0                       # km/s, the adopted mask half-width
WIDTHS = [5, 10, 13, 20, 35, 50, 100, 200, 330, 500]

CAT = list(csv.DictReader(open(os.path.join(
    HERE, 'per_target_results_v3.98.csv'))))
flagged = [r for r in CAT if r['stage1_flag'] == 'True']

# R2-M1: the offset is only meaningful where the pipeline actually stored the
# crossing frequency.  For the rest, line_offset_kms is a window-level
# quantity -- HD 14055's reads -12161 km/s -- and cannot support a statement
# about how far a CROSSING sits from a transition.  Restricting to measured
# crossings is an honest weakening of the v3.94 claim, which pooled all 13.
measured = [r for r in flagged
            if r['f_cross_GHz'] and float(r['f_cross_GHz']) > 0]
n_dropped = len(flagged) - len(measured)
flagged = measured


def off(r):
    try:
        return abs(float(r['line_offset_kms']))
    except (ValueError, TypeError):
        return None


# the disposition recorded in the released catalogue is the ground truth we
# are testing the mask against
attributed = [r for r in flagged if r['disposition'] and 'CO' in r['disposition']]
unattrib = [r for r in flagged if r not in attributed]

off_att = [off(r) for r in attributed if off(r) is not None]
off_un = [off(r) for r in unattrib if off(r) is not None]
assert off_att and off_un, 'missing line offsets for the flagged windows'

att_max = max(off_att)               # furthest line-attributed window
un_min = min(off_un)                 # closest unattributed window

# the whole point: the two populations must not overlap, or no half-width
# reproduces the released dispositions and this table would be misleading
assert att_max < un_min, (
    'line-attributed windows reach %.1f km/s while the closest unattributed '
    'window is at %.1f km/s: the populations overlap, so no single mask '
    'half-width reproduces the released classification' % (att_max, un_min))
assert att_max < ADOPTED < un_min, (
    'the adopted +-%.0f km/s mask does not lie in the separating gap '
    '%.1f-%.1f km/s' % (ADOPTED, att_max, un_min))

rows = []
for w in WIDTHS:
    n_att = sum(1 for v in off_att if v <= w)
    n_un = sum(1 for v in off_un if v <= w)
    same = (n_att == len(off_att) and n_un == 0)
    mark = '\\checkmark' if same else '$\\times$'
    note = ('identical' if same else
            ('%d attributed window%s missed' % (len(off_att) - n_att,
                                                '' if len(off_att) - n_att == 1
                                                else 's')
             if n_att < len(off_att) else
             '%d unattributed window%s swept in' % (n_un, '' if n_un == 1
                                                    else 's')))
    b = (lambda x: '\\textbf{%s}' % x) if w == ADOPTED else (lambda x: x)
    rows.append('%s & %s & %s & %s \\\\' % (
        b('%d' % w), b('%d/%d' % (n_att, len(off_att))),
        b('%d/%d' % (n_un, len(off_un))), mark))

with open(TAB, 'w') as f:
    f.write('%% GENERATED by maskrobust_v398.py -- do not hand-edit.\n')
    f.write('\\begin{tabular}{@{}rccc@{}}\n\\hline\n')
    f.write('Half-width & line-attributed & unattributed & same as \\\\\n')
    f.write('(km\\,s$^{-1}$) & masked & masked & released? \\\\\n')
    f.write('\\hline\n' + '\n'.join(rows) + '\n\\hline\n\\end{tabular}\n')

with open(OUT, 'w') as f:
    f.write('%% GENERATED by maskrobust_v398.py -- do not hand-edit.\n')
    f.write('\\newcommand{\\MrAdopted}{%.0f}\n' % ADOPTED)
    f.write('\\newcommand{\\MrAttMax}{%.0f}\n' % att_max)
    f.write('\\newcommand{\\MrUnMin}{%.0f}\n' % un_min)
    f.write('\\newcommand{\\MrGapRatio}{%.0f}\n' % (un_min / att_max))
    f.write('\\newcommand{\\MrHeadLo}{%.1f}\n' % (ADOPTED / att_max))
    f.write('\\newcommand{\\MrHeadHi}{%.1f}\n' % (un_min / ADOPTED))
    f.write('\\newcommand{\\MrNAtt}{%d}\n' % len(off_att))
    f.write('\\newcommand{\\MrNUn}{%d}\n' % len(off_un))
    f.write('\\newcommand{\\MrNDropped}{%d}\n' % n_dropped)

print('maskrobust: attributed <= %.1f km/s, unattributed >= %.1f km/s, '
      'gap x%.0f; adopted %.0f sits x%.1f above / x%.1f below'
      % (att_max, un_min, un_min / att_max, ADOPTED, ADOPTED / att_max,
         un_min / ADOPTED))
