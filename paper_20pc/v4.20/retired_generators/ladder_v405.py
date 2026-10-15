#!/usr/bin/env python3
"""Round 93 (v4.05, referee 1 item 7): the mask-width ladder as a generated
table, in BOTH frames.

R1-7 asks for a sensitivity table over the line-mask half-width, and states as
its premise that a wider tolerance costs no yield.  That premise is false in
the frame the search actually ran in and very nearly true in the one the paper
used to describe, so both columns are printed.

The stronger answer to the post-hoc-tuning charge is not the table but one
fact inside it, machine-checked here rather than asserted in prose: at
+-50 and +-100 km/s the rank-flagged unattributed crossings are not merely
equal in NUMBER but the IDENTICAL SET, in both frames.  A half-width chosen to
bury a candidate would show one reappearing when the tube is widened; here the
tube can be doubled, in either frame, and the same two events survive.

Frames.  The sky (topocentric) column is the frame the search ran -- proved by
maskframe_v404.py, which re-derives every released offset from the observed
sky frequency and from nothing else.  The stellar column is
dv_sky - v_bary + v_sys, with v_bary per (block, window) from the frozen
measurement in r8inputs/bary_v405.json and v_sys from SIMBAD via
starrv_v399.json.  It is evaluable for 44 of the 56 crossings; the other 12
lack one term or the other, and the denominator is a macro so the caption
cannot drift from the table.

FALSIFIER F3, fixed before running: the sky column must reproduce R1-7's
published 11/10/3/2/2 on the population R1-7 quoted (the crossings with a
released line_offset_kms as the catalogue stood at v4.03, i.e. before the
H2CO key fix), or the join is wrong and nothing here stands.

-> survey_numbers_round93.tex, tab_maskladder_v405.tex
"""
import csv
import json
import os

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, 'survey_numbers_round93.tex')
TAB = os.path.join(HERE, 'tab_maskladder_v405.tex')

C_KMS = 299792.458
LADDER = [13.0, 20.0, 30.0, 50.0, 100.0]
# R1-7, as printed in the report, and EDGE_AND_MASKFRAME Sec. 6.4.
PUBLISHED_SKY_RANKFLAGGED = [11, 10, 3, 2, 2]
PUBLISHED_STELLAR_RANKFLAGGED = [3, 2, 2, 2, 2]
PUBLISHED_STELLAR_ATTRIBUTED = [13, 14, 14, 14, 14]
# The three crossings whose km/s offset was blank before the v4.04 H2CO key
# fix.  R1-7's ladder was quoted over the 53 rows that had one; the fix adds
# these at -677, +617 and +894 km/s, which change no cell.  Naming them keeps
# the two denominators honest instead of quietly re-basing the published
# numbers on a different population.
H2CO_REPAIRED = 'H2CO'

_src = open(os.path.join(HERE, 'v342_calc.py')).read()
_i = _src.index('CAT_OLD = {')
CAT_OLD = eval(_src[_i + len('CAT_OLD = '):_src.index('}', _i) + 1])  # noqa: S307
assert len(CAT_OLD) == 15, len(CAT_OLD)

ROWS = [r for r in csv.DictReader(open(os.path.join(
    HERE, 'per_target_results_v3.99.csv'))) if r['crossing'] == 'True']
VSYS = json.load(open(os.path.join(HERE, 'starrv_v399.json')))
BARY = json.load(open(os.path.join(HERE, 'r8inputs',
                                   'bary_v405.json')))['v_bary_kms']

M = {}


def m(k, v):
    M[k] = v


recs = []
for r in ROWS:
    dv = float(r['line_offset_kms'])
    vc = BARY.get('%s|%.6f' % (r['eb'], float(r['flo_GHz'])))
    vs = VSYS.get(r['star_name']) or VSYS.get(r['star_name'].split(' Gaia')[0])
    recs.append(dict(
        star=r['star_name'], eb=r['eb'],
        dv_sky=dv,
        dv_stel=((dv - vc + vs) if (vc is not None and vs is not None)
                 else None),
        # the population R1-7 quoted: everything except the three rows the
        # H2CO key bug left blank
        in_published=(r['nearest_line'] != H2CO_REPAIRED),
        rank=(float(r['star_snr']) >= 5.0
              and float(r['star_snr']) > float(r['ctrl_max_snr'])),
        T=float(r['star_snr'])))

sky56 = recs
sky53 = [r for r in recs if r['in_published']]
stel = [r for r in recs if r['dv_stel'] is not None]
assert len(sky56) == 56 and len(sky53) == 53, (len(sky56), len(sky53))
assert len(stel) == 44, len(stel)


def ladder(sub, key):
    out = {}
    for w in LADDER:
        rf = [r for r in sub if abs(r[key]) > w and r['rank']]
        out[w] = dict(attributed=sum(1 for r in sub if abs(r[key]) <= w),
                      unattributed=sum(1 for r in sub if abs(r[key]) > w),
                      rf=len(rf),
                      names={(r['star'], r['eb']) for r in rf})
    return out


L56 = ladder(sky56, 'dv_sky')
L53 = ladder(sky53, 'dv_sky')
LST = ladder(stel, 'dv_stel')

got53 = [L53[w]['rf'] for w in LADDER]
got56 = [L56[w]['rf'] for w in LADDER]
gotst = [LST[w]['rf'] for w in LADDER]
gotst_a = [LST[w]['attributed'] for w in LADDER]
# ★ F3.  If the sky column stops reproducing R1-7's published ladder, the join
# between the catalogue and the published numbers is wrong and every count
# below is untrustworthy.
assert got53 == PUBLISHED_SKY_RANKFLAGGED, (got53, PUBLISHED_SKY_RANKFLAGGED)
# ★ The H2CO repair must not move a cell.  If it does, the two denominators
# are not interchangeable and the paper may not quote the ladder over all 56.
assert got56 == got53, (got56, got53)
assert gotst == PUBLISHED_STELLAR_RANKFLAGGED, gotst
assert gotst_a == PUBLISHED_STELLAR_ATTRIBUTED, gotst_a

# ★ The fact that answers the post-hoc charge: not "the counts agree" but
# "the sets are equal".  A tuned half-width would fail this.
same_sky = L56[50.0]['names'] == L56[100.0]['names']
same_stel = LST[50.0]['names'] == LST[100.0]['names']
assert same_sky and same_stel, (same_sky, same_stel)
pair_sky = sorted(L56[50.0]['names'])
pair_stel = sorted(LST[50.0]['names'])
# ★ ...and it is the same pair in both frames, which is why the frame
# documentation defect changes no result.
assert {p[0] for p in pair_sky} == {p[0] for p in pair_stel}, \
    (pair_sky, pair_stel)
# ★ A set identity over an EMPTY set would pass vacuously.  Require content.
assert len(pair_sky) == 2, pair_sky

# ★ R1-7's premise, tested rather than repeated: does widening the tube cost
# yield?  In the sky frame it does -- 9 of the 11 go between +-13 and +-50.
_lost_sky = got53[0] - got53[LADDER.index(50.0)]
_lost_stel = gotst[0] - gotst[LADDER.index(50.0)]
assert _lost_sky > _lost_stel, (_lost_sky, _lost_stel)

m('MaskFrameUsed', 'topocentric')
m('MaskLadderNSky', '%d' % len(sky56))
m('MaskLadderNSkyReleased', '%d' % len(sky53))
m('MaskLadderNStellar', '%d' % len(stel))
m('MaskLadderNUneval', '%d' % (len(sky56) - len(stel)))
m('MaskLadderFiftyEqHundred', 'identical')
m('MaskLadderPairN', '%d' % len(pair_sky))
m('MaskLadderLostSky', '%d' % _lost_sky)
m('MaskLadderLostStel', '%d' % _lost_stel)
# LaTeX control sequences cannot contain digits, so the half-width goes into
# the macro name as a word.
WORD = {13.0: 'Thirteen', 20.0: 'Twenty', 30.0: 'Thirty', 50.0: 'Fifty',
        100.0: 'Hundred'}
for w in LADDER:
    tag = 'W' + WORD[w]
    m('MaskLadderSky' + tag, '%d' % L53[w]['rf'])
    m('MaskLadderSkyFixed' + tag, '%d' % L56[w]['rf'])
    m('MaskLadderSkyAttr' + tag, '%d' % L53[w]['attributed'])
    m('MaskLadderStel' + tag, '%d' % LST[w]['rf'])
    m('MaskLadderStelAttr' + tag, '%d' % LST[w]['attributed'])

lines = ['%% GENERATED by ladder_v405.py -- do not hand-edit.\n',
         '\\begin{tabular}{@{}l@{~~}rrc@{~~}rrc@{}}\n', '\\hline\n',
         '& \\multicolumn{3}{c}{sky (topocentric)} '
         '& \\multicolumn{3}{c}{stellar} \\\\\n',
         'half-width & attr. & unattr. & rank-fl. & attr. & unattr. '
         '& rank-fl. \\\\\n', '\\hline\n']
for w in LADDER:
    s, t = L53[w], LST[w]
    b = (lambda x: '\\textbf{%s}' % x) if w == 50.0 else (lambda x: x)
    lines.append('%s & %d & %d & %s & %d & %d & %s \\\\\n' % (
        b('$\\pm%g$' % w), s['attributed'], s['unattributed'],
        b('%d' % s['rf']), t['attributed'], t['unattributed'], b('%d' % t['rf'])))
lines.append('\\hline\n\\end{tabular}\n')
open(TAB, 'w').writelines(lines)

with open(OUT, 'w') as fh:
    fh.write('%% GENERATED by ladder_v405.py -- do not hand-edit.\n')
    for k in sorted(M):
        fh.write('\\newcommand{\\%s}{%s}\n' % (k, M[k]))

print('ladder_v405 (round 93): F3 PASS -- sky(%d) rank-flagged unattributed '
      '%s reproduces R1-7; with the H2CO repair over all %d it is %s '
      '(unchanged)' % (len(sky53), got53, len(sky56), got56))
print('  stellar(%d): rank-flagged %s, attributed %s' % (len(stel), gotst, gotst_a))
print('  +-50 and +-100 select the IDENTICAL SET in both frames: %s'
      % ', '.join('%s %s' % p for p in pair_sky))
print('  widening +-13 -> +-50 costs %d of %d in the sky frame and %d of %d '
      'in the stellar frame' % (_lost_sky, got53[0], _lost_stel, gotst[0]))
print('  -> %s (%d macros), %s' % (os.path.basename(OUT), len(M),
                                   os.path.basename(TAB)))
