#!/usr/bin/env python3
r"""Round 77: the quantities that used to live in the ungenerated frozen
macro files `survey_numbers_round{5,6,7}.tex`.

Referee 2's M2 headline is that the manuscript "mixes results from at least
two extractions".  It mixed three.  `make_all.sh` restored rounds 5, 6 and 7
verbatim from `frozen_macros/` because their generators were never shipped,
so nothing in the build could recompute them; their own headers say they came
from `frozen_export_v3.31.json` / `per_target_results_v3.32.csv`, two
revisions before the ACA control-annulus repair.  Twelve of their macros were
still typeset.

This file, together with three additions made in the generators that already
own the relevant machinery (`v361_calc.py` for the line-mask geometry,
`v343_calc.py` for the drift grid, `make_fig_accel2d.py` for the planetary
accelerations), recomputes every one of them from the released catalogue, and
the three frozen files are deleted.

What moves here:

  \HdCorrectedT, \HdCorrectedRing   the HD 48370 statistic and its control
                                    ring after the local noise rescaling of
                                    the bandpass-ripple bound.  The frozen
                                    pair (21.0, 20.8) is 27.10/1.29 and
                                    26.83/1.29 -- the PRE-repair T* over the
                                    PRE-repair ring maximum.  The catalogue
                                    now gives T* = 26.83 against a ring
                                    maximum of 18.36, so the rescaled pair
                                    moves to 20.8 against 14.2 and the window
                                    is flagged by a wider margin, not a
                                    narrower one.

  \NonExcRingGe, \NonExcRingMed,    the tail of the Appendix J crossing
  \NonExcHitMed, \NonExcTMed,       ledger.  The frozen \NonExcRingGe = 16 is
  \NonExcTQLo, \NonExcTQHi          why that ledger did not close: 56 - 12 - 6
                                    = 38, not 16.

  \HaystackFrac                     Wright, Kanodia & Lubar (2018) haystack
                                    fraction.  A literature constant, but it
                                    is quoted in the first paragraph of the
                                    paper, so it is declared here with its
                                    source rather than inherited from a file
                                    no generator writes.

and the named examples the Appendix I mask ledger used to hard-code, whose
literals had all drifted (AU Mic "+379" is +373.5, LHS 1140 "+115" is +126.7,
and HD 285968's "maximum 10.9 against a star peak of 6.5" matches none of its
three in-mask crossings).
"""
import csv
import os
import re
import statistics as st

os.chdir(os.path.dirname(os.path.abspath(__file__)))

import star_alias                                          # noqa: E402

OUT = []


def M(name, val):
    OUT.append(r'\newcommand{\%s}{%s}' % (name, val))


def texval(macro):
    import glob
    for fn in sorted(glob.glob('survey_numbers*.tex')):
        m = re.search(r'\\newcommand\{\\%s\}\{(.*?)\}\s*$' % macro,
                      open(fn).read(), re.M)
        if m:
            return m.group(1)
    raise SystemExit('%s not found' % macro)


ROWS = list(csv.DictReader(open('per_target_results_v3.99.csv')))
CROSS = [r for r in ROWS if r['crossing'] == 'True']
HALF = float(texval('MaskVWidth'))          # the adopted mask half-width


def star(r):
    return r['star_name'].split('  Gaia')[0].strip()


def inmask(r):
    v = r['line_offset_kms']
    return v not in ('', 'None') and abs(float(v)) <= HALF


# =====================================================================
# (1) HD 48370 after the local noise rescaling  (was \HdCorrected*)
# =====================================================================
# The ratio is the local-to-global noise scale measured in a band around the
# feature and excluding the feature itself; it is a property of the field,
# not of the control-annulus geometry, so the ACA repair does not touch it.
# It is quoted in the same sentence of the manuscript and is asserted here so
# the two cannot drift apart.
HD_LOCAL_RATIO = 1.29
_hd = [r for r in CROSS if star(r) == 'HD 48370' and r['band'] == '6']
assert len(_hd) == 1, _hd
_hd = _hd[0]
HD_T = float(_hd['star_snr'])
HD_RING = float(_hd['ctrl_max_snr'])
assert HD_T > HD_RING, 'HD 48370 no longer beats its ring'
M('HdCorrectedT', '%.1f' % (HD_T / HD_LOCAL_RATIO))
M('HdCorrectedRing', '%.1f' % (HD_RING / HD_LOCAL_RATIO))
M('HdLocalRatio', '%.2f' % HD_LOCAL_RATIO)

# =====================================================================
# (2) the crossing ledger of Appendix J  (was \NonExc*)
# =====================================================================
# Every threshold crossing falls in exactly one of three bins, and the three
# must sum to the crossing count.  The frozen \NonExcRingGe = 16 came from an
# extraction in which the other two bins were different sizes, so the ledger
# in the text could not be made to close.
FLAG = [r for r in CROSS if r['stage1_flag'] == 'True']
INMASK_NOFLAG = [r for r in CROSS if r['stage1_flag'] != 'True' and inmask(r)]
REST = [r for r in CROSS
        if r['stage1_flag'] != 'True' and not inmask(r)]
assert len(FLAG) + len(INMASK_NOFLAG) + len(REST) == len(CROSS), 'ledger open'
# By construction a crossing that did not reach stage 1 has a control ring
# reaching or exceeding it; assert it rather than assert it in prose.
assert all(float(r['ctrl_max_snr']) >= float(r['star_snr']) for r in REST)
M('NonExcRingGe', '%d' % len(REST))
M('NonExcRingMed', '%.2f' % st.median(float(r['ctrl_max_snr']) for r in REST))
M('NonExcHitMed', '%.2f' % st.median(float(r['star_snr']) for r in REST))
_t = sorted(float(r['star_snr']) for r in REST)
M('NonExcTQLo', '%.1f' % _t[len(_t) // 4])
M('NonExcTQHi', '%.1f' % _t[(3 * len(_t)) // 4])
M('NonExcTMax', '%.1f' % _t[-1])
M('MaskCrossInNoFlagN', '%d' % len(INMASK_NOFLAG))
M('MaskCrossInStageOneN', '%d' % sum(1 for r in FLAG if inmask(r)))
M('MaskCrossOutStageOne', '%d' % sum(1 for r in FLAG if not inmask(r)))

# ---- the named examples the Appendix I ledger used to hard-code ----------
# The old text asserted that the remainder "lie far outside any circumstellar
# tolerance" and gave two examples, both of whose velocities had drifted
# (AU Mic "+379" is +373.5; LHS 1140 "+115" is +126.7).  An example is weaker
# than the bound, so publish the bound: the SMALLEST separation in the whole
# bin, which is what "all of them lie far outside" actually asserts.
_off = [abs(float(r['line_offset_kms'])) for r in REST
        if r['line_offset_kms'] not in ('', 'None')]
_nearest = min(_off)
_nr = [r for r in REST if r['line_offset_kms'] not in ('', 'None')
       and abs(float(r['line_offset_kms'])) == _nearest][0]
M('MaskNearestKms', '%.0f' % _nearest)
M('MaskNearestStar', star_alias.designation(_nr['star_name']))
M('MaskNearestMult', '%.1f' % (_nearest / HALF))
M('MaskNoLineN', '%d' % (len(REST) - len(_off)))
# The most-repeated in-mask crossing that did NOT beat its ring: the example
# the text gives of the mask catching something the ring had already rejected.
_byst = {}
for r in INMASK_NOFLAG:
    _byst.setdefault(star(r), []).append(r)
_rep = max(_byst.items(), key=lambda kv: (len(kv[1]), kv[0]))
M('MaskRepStar', star_alias.designation(_rep[1][0]['star_name']))
M('MaskRepN', '%d' % len(_rep[1]))
M('MaskRepTLo', '%.2f' % min(float(r['star_snr']) for r in _rep[1]))
M('MaskRepTHi', '%.2f' % max(float(r['star_snr']) for r in _rep[1]))
M('MaskRepRingLo', '%.2f' % min(float(r['ctrl_max_snr']) for r in _rep[1]))
M('MaskRepRingHi', '%.2f' % max(float(r['ctrl_max_snr']) for r in _rep[1]))
M('MaskRepVLo', '%+.1f' % min(float(r['line_offset_kms']) for r in _rep[1]))
M('MaskRepVHi', '%+.1f' % max(float(r['line_offset_kms']) for r in _rep[1]))

# =====================================================================
# (3) the haystack fraction  (was \HaystackFrac)
# =====================================================================
# Wright, Kanodia & Lubar (2018), "How Much SETI Has Been Done?", AJ 156, 260.
# Their eight-dimensional haystack figure of merit for the union of all radio
# searches published to that date.  A literature constant: declared here, with
# its source, so that no macro the manuscript typesets comes from a file the
# build cannot write.
HAYSTACK_FRAC_EXP = -18
HAYSTACK_FRAC_MANT = 6
M('HaystackFrac', r'$%d\times10^{%d}$' % (HAYSTACK_FRAC_MANT,
                                          HAYSTACK_FRAC_EXP))

# =====================================================================
# (4) Table 23, which was hand-typed  (tab:bothstats)
# =====================================================================
# Forty hand-typed numerals, no generator, and four of its seven rows stale:
# HD 48370 was printed as T* = 27.10 against a control maximum of 26.83, the
# PRE-repair pair, and one row was HD 14055, a window the repair removed from
# the stage-1 set.  It also carried the region-max control maximum and the
# symmetric ring maximum as two columns, which were identical in all seven
# rows because they are the same quantity.
#
# Generated here from the catalogue, over the star-band pairs the SYMMETRIC
# statistic promotes -- the released stage-1 set.  The region-max-only pairs
# are a count, not rows: there are too many to table and the text already
# quotes \NRegionMaxFlag and \NRegionMaxPairs.
_pair = {}
for r in ROWS:
    if r['stage1_flag'] != 'True' and r['stage1_flag_regionmax'] != 'True':
        continue
    k = (star_alias.designation(r['star_name']), int(r['band']))
    cur = _pair.get(k)
    if cur is None or float(r['star_snr_regionmax'] or 0) > \
            float(cur['star_snr_regionmax'] or 0):
        _pair[k] = r
SYMPAIR = {k: r for k, r in _pair.items() if any(
    x['stage1_flag'] == 'True' for x in ROWS
    if star_alias.designation(x['star_name']) == k[0]
    and int(x['band']) == k[1])}
assert SYMPAIR, 'no stage-1 star-band pair'
_L = ['%% GENERATED by exfrozen_v401.py -- do not hand-edit.',
      r'\begin{tabular}{@{}llrrrr@{}}', r'\toprule',
      r'Star & Band & $\nu$ (GHz) & $S_{\rm reg}$ & $T_\star$ & '
      r'ctrl.\ max \\', r'\midrule']
for k in sorted(SYMPAIR, key=lambda k: -float(SYMPAIR[k]['star_snr_regionmax'])):
    r = SYMPAIR[k]
    assert r['stage1_flag'] == 'True', k
    _L.append('%s & %d & %.4f & %.2f & %.2f & %.2f \\\\'
              % (k[0], k[1],
                 0.5 * (float(r['flo_GHz']) + float(r['fhi_GHz'])),
                 float(r['star_snr_regionmax']), float(r['star_snr']),
                 float(r['ctrl_max_snr'])))
_L += [r'\bottomrule', r'\end{tabular}']
open('tab_bothstats_v401.tex', 'w').write('\n'.join(_L) + '\n')
M('BothStatsRows', '%d' % len(SYMPAIR))
M('RegOnlyPairs', '%d' % (len(_pair) - len(SYMPAIR)))
M('SymOnlyPairs', '%d' % sum(1 for k, r in SYMPAIR.items()
                             if r['stage1_flag_regionmax'] != 'True'))

with open('survey_numbers_round77.tex', 'w') as fh:
    fh.write('% GENERATED by exfrozen_v401.py -- do not edit by hand.\n'
             '% The ex-frozen quantities, recomputed from the released '
             'catalogue.\n')
    fh.write('\n'.join(OUT) + '\n')

print('exfrozen_v401: %d crossings = %d stage-1 + %d in-mask unflagged + %d other'
      % (len(CROSS), len(FLAG), len(INMASK_NOFLAG), len(REST)))
print('  HD 48370 rescaled by %.2f: T* %.2f -> %.1f, ring %.2f -> %.1f'
      % (HD_LOCAL_RATIO, HD_T, HD_T / HD_LOCAL_RATIO,
         HD_RING, HD_RING / HD_LOCAL_RATIO))
print('  other crossings: ring median %.2f against a crossing median %.2f'
      % (st.median(float(r['ctrl_max_snr']) for r in REST),
         st.median(float(r['star_snr']) for r in REST)))
print('  nearest miss outside the mask: %s at %.1f km/s (%.1f x the half-width);'
      ' %d have no catalogued transition of a masked species in the window'
      % (star(_nr), _nearest, _nearest / HALF, len(REST) - len(_off)))
print('  most repeated in-mask unflagged: %s x%d' % (_rep[0], len(_rep[1])))
print('%d macros -> survey_numbers_round77.tex' % len(OUT))
