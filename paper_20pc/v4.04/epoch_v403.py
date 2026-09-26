#!/usr/bin/env python3
r"""v4.03: the reference-epoch defect, what a threshold crossing is worth, and
the one crossing that makes "zero unattributed localised crossings" false.

Three measurements the manuscript needs and which no other generator owns.

1. THE REFERENCE EPOCH.  The drift-following visibility fit evaluates the
   carrier's channel at a reference time t0.  The round-6 implementation used
   t0 = median(TIME) of the rows it loaded; the search de-drifts to its own
   first retained integration.  Which is right is not a matter of convention:
   the injection campaign fitted every triggered tone BOTH ways, so the answer
   is a read of data already taken.  `epoch_inject_v403.json` is that campaign
   record, one row per tone, fetched verbatim from the host
   (/data/SETI/p90_r7/epoch/part_b_epoch_vs_D.json).  Beyond a displacement of
   a few channels one convention finds the carrier and the other finds zero.

   The bins here are computed from the raw rows, not copied from a report, and
   the generator ASSERTS the qualitative result rather than printing whatever
   the file says: above the displacement threshold the adopted convention must
   recover a positive fraction and localise a majority, and the committed one
   must do neither.  If a future campaign overturns that, the build stops.

2. WHAT T* >= 5 IS WORTH.  `ctrlrate_v403.json` is the per-control-position
   rate of reaching the survey's SMALLEST crossing statistic, measured on the
   released catalogue's own windows (matched on eb and window edges, so no
   epoch-extension block leaks in) from the retained 512-element control
   vectors.  In a fine-channel window a single control position reaches it
   about one time in eleven.  The trigger therefore carries no evidential
   weight on its own -- which is why there is a rank screen, and why the
   paper's chain does not stop at a crossing.

3. ETA CRV A002_X122b6ff_X1041e.  The crossing that localises under BOTH
   reference epochs and is unattributed under the frozen mask, so the
   sentence "zero unattributed localised crossings" is false.  Every number
   about it is read from the ledger, the catalogue and the frozen protocol
   products; DECISIONS_R7 A5 requires its T* and its FAILED rank screen to
   travel with it in every sentence, and `etacrv-facts` in ledger_v403.py is
   the gate on that.  The wide-line-list coincidence is reported here too,
   with the calibration that makes it worthless: at these frequencies a
   RANDOM frequency lands within the mask half-width of some harvested
   transition most of the time.

Writes survey_numbers_round81.tex.  MUST follow ledger_v403.py (reads
ledger_v403.json) and make_numbers/v342_calc (reads the catalogue).
"""
import csv
import json
import math
import os
import statistics

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, 'survey_numbers_round81.tex')

M = {}


def m(k, v):
    M[k] = v


def jload(name):
    return json.load(open(os.path.join(HERE, name)))


# ---------------------------------------------------------------- 1. epoch
INJ = jload('epoch_inject_v403.json')
# The displacement below which the two conventions are the same experiment.
# A LITERAL, and the same one ledger_v403.py uses: it is set by the campaign's
# own resolution, not fitted to these fits.
D_LO = 2.8

units = {r['unit'] for r in INJ}
above = [r for r in INJ if r['D'] > D_LO]
below = [r for r in INJ if r['D'] <= 0.25]


def frac(rows, key):
    return statistics.median(r[key] for r in rows)


def locrate(rows, key):
    return sum(1 for r in rows if r[key]) / float(len(rows))


f_cor, f_com = frac(above, 'first'), frac(above, 'median')
l_cor, l_com = locrate(above, 'loc'), locrate(above, 'loc_r6')

# The result the paper states, asserted rather than transcribed.  If a future
# campaign reverses it the build stops here instead of printing a number that
# contradicts the sentence around it.
assert f_cor > 0.1 > f_com, (
    'the injection campaign no longer shows the adopted epoch recovering flux '
    'above %.1f channels of displacement where the committed one does not '
    '(%.3f vs %.3f)' % (D_LO, f_cor, f_com))
assert l_cor > 0.5 and l_com < 0.05, (
    'the injection campaign no longer shows the adopted epoch localising a '
    'majority above %.1f channels where the committed one localises almost '
    'nothing (%.3f vs %.3f)' % (D_LO, l_cor, l_com))
# and below a quarter of a channel the two must be indistinguishable, which is
# why a pilot on a short-span window could not have found this.
assert abs(frac(below, 'first') - frac(below, 'median')) < 0.02, (
    'the two conventions no longer agree below 0.25 channels; the claim that '
    'the defect is invisible at small displacement rests on this')

m('EpNTone', '%d' % len(INJ))
m('EpNUnit', '%d' % len(units))
m('EpDLo', '%.1f' % D_LO)
m('EpNAbove', '%d' % len(above))
m('EpFracCor', '%.3f' % f_cor)
m('EpFracCom', '%.3f' % f_com)
m('EpLocPctCor', '%.1f' % (100.0 * l_cor))
m('EpNLocCom', '%d' % sum(1 for r in above if r['loc_r6']))

# ------------------------------------------------- 2. what a crossing is worth
CR = jload('ctrlrate_v403.json')
T_MIN = CR['T']
A = [w for w in CR['windows'] if w['cls'] == 'A']
B = [w for w in CR['windows'] if w['cls'] == 'B']
assert A and B, 'the control-rate measurement carries no windows of one class'
rate_a = sum(w['rate'] for w in A) / len(A)
rate_b = sum(w['rate'] for w in B) / len(B)
assert rate_a > 10 * rate_b, (
    'the fine-channel control rate is no longer far above the coarse one; the '
    'sentence this supports is about Class A windows specifically')
exp_a = sum(w['rate'] for w in A)
obs_a = sum(1 for w in A if w['star'] >= T_MIN)

# Read the Class A window count from the catalogue rather than a macro file,
# so this cannot disagree with \NWinA: macrosyn checks the two agree.
CAT = list(csv.DictReader(open(os.path.join(HERE,
                                            'per_target_results_v3.99.csv'))))
N_WIN_A = sum(1 for r in CAT if r['search_class'] == 'A')

m('EpTmin', '%.4f' % T_MIN)
m('EpCtrlNA', '%d' % len(A))
m('EpCtrlNB', '%d' % len(B))
m('EpCtrlNWinA', '%d' % N_WIN_A)
m('EpCtrlRateA', '%.1f' % (100.0 * rate_a))
m('EpCtrlRateAMed', '%.1f' % (100.0 * statistics.median(w['rate'] for w in A)))
m('EpCtrlRateB', '%.2f' % (100.0 * rate_b))
m('EpCtrlExpA', '%.0f' % exp_a)
m('EpCtrlObsA', '%d' % obs_a)
m('EpCtrlExpFullA', '%.0f' % (rate_a * N_WIN_A))

# The visibility fit's own control ensemble is twelve positions and
# frequencies, not 512.  What a maximum over twelve standard normals is worth
# is arithmetic, and it is the measurement behind DECISIONS_R7 A2: the third
# clause of the localisation criterion is passed by anything above about 2
# sigma.  Computed here, by the same quadrature for both sizes, so the
# comparison cannot be a transcription error.
def emax(n, lo=-8.0, hi=12.0, steps=400000):
    """E[max of n iid standard normals], by numerical integration of
    1 - Phi(x)^n over x.  Simpson's rule on a grid wide enough that the tails
    contribute below the printed precision."""
    def Phi(x):
        return 0.5 * (1.0 + math.erf(x / math.sqrt(2.0)))
    h = (hi - lo) / steps
    tot = 0.0
    for i in range(steps + 1):
        x = lo + i * h
        f = (1.0 - Phi(x) ** n) if x >= 0 else -(Phi(x) ** n)
        w = 1 if i in (0, steps) else (4 if i % 2 else 2)
        tot += w * f
    return tot * h / 3.0


N_VIS_CTRL = 8 + 4                # eight annulus positions, four off-frequencies
E12, E512 = emax(N_VIS_CTRL), emax(512)
assert 1.5 < E12 < 1.8 and 2.9 < E512 < 3.2, \
    'the expected maxima moved; the integration grid is wrong'
m('EpNVisCtrl', '%d' % N_VIS_CTRL)
m('EpEmaxVis', '%.2f' % E12)
m('EpEmaxRank', '%.2f' % E512)
m('EpVisRankRes', '1/%d' % (N_VIS_CTRL + 1))

# --------------------------------------------------------------- 3. eta Crv
LED = jload('ledger_v403.json')
EB = 'A002_X122b6ff_X1041e'
ROW = [r for r in LED['rows'] if r['eb'] == EB]
assert len(ROW) == 1, 'eta Crv %s is not a single row of the ledger' % EB
R = ROW[0]
# The four facts DECISIONS_R7 A5 requires to travel together.  ledger_v403.py
# gates them too (`etacrv-facts`); asserted again here because this generator
# is what writes them into the prose.
assert R['committed']['localised'] and R['adopted']['localised'], \
    'eta Crv no longer localises under both conventions'
assert not R['attributed'] and not R['screen'], \
    'eta Crv is no longer both unattributed and below the rank screen'

CATROW = [r for r in CAT if r['eb'] == EB and r['crossing'].strip().lower()
          in ('true', '1')]
assert len(CATROW) == 1, 'the catalogue does not carry exactly one eta Crv crossing'
C = CATROW[0]
n_ge = int(C['n_ctrl_ge_star'])
n_ctrl = int(C['n_ctrl'])
assert n_ge > 0, ('eta Crv would pass the rank screen; the sentence in the '
                  'paper says it fails it')

FRAME = jload('etacrv_frame_v403.json')['cross'][EB]
CALIB = jload('etacrv_frame_v403.json')['calibration'][EB]
VER = jload('etacrv_verify.json')['eta Crv 357GHz']
RFI = jload('etacrv_rfi_v403.json')[EB]
REP = [b for b in VER['blocks'] if b['status'] == 'ok']
assert len(REP) == 1, 'the eta Crv recurrence test no longer rests on one repeat'
P = REP[0]

# The wide-list coincidence and why it is worth nothing.  This is the general
# finding, not a fact about eta Crv: at these frequencies the harvested line
# list is dense enough that a hit is the DEFAULT outcome.
assert FRAME['wide_in_mask'] and not FRAME['frozen_in_mask'], (
    'the wide-list hit or the frozen-mask miss has moved; the paragraph '
    'contrasting the two lists depends on both')
assert CALIB['frac_in_mask'] > 0.5, (
    'a random frequency in this window no longer lands inside the mask of '
    'some harvested transition more often than not -- the point of the '
    'calibration is that the wide-list test cannot fail')

m('EpEtaEb', '\\texttt{%s}' % EB.replace('_', '\\_'))
m('EpEtaFreq', '%.6f' % FRAME['fx'])
m('EpEtaT', '%.4f' % R['tstar'])
m('EpEtaNGe', '%d' % n_ge)
m('EpEtaNCtrl', '%d' % n_ctrl)
m('EpEtaPRank', '%.3f' % ((n_ge + 1.0) / (n_ctrl + 1.0)))
m('EpEtaReCom', '%.2f' % R['committed']['re'])
m('EpEtaReCor', '%.2f' % R['adopted']['re'])
m('EpEtaImCor', '%.2f' % R['adopted']['im'])
m('EpEtaCtrlCom', '%.2f' % R['committed']['cmax'])
m('EpEtaCtrlCor', '%.2f' % R['adopted']['cmax'])
m('EpEtaD', '%.2f' % R['dch'])
m('EpEtaDvFrozen', '%d' % round(FRAME['frozen_dv_stellar']))
m('EpEtaLineFrozen', FRAME['frozen_nearest'].replace('(', '($').replace('-', '{\\to}')
  .replace(')', '$)'))
m('EpEtaWideSpecies', 'SO$_2$')
m('EpEtaWideDv', '%+.1f' % FRAME['wide_dv_stellar'])
m('EpWideFrac', '%.1f' % (100.0 * CALIB['frac_in_mask']))
m('EpWideNu', '%d' % round(FRAME['fx']))
m('EpWideLinesGHz', '%.0f' % CALIB['lines_per_GHz'])
m('EpWideNInMask', '%.1f' % CALIB['expected_lines_in_pm50'])
m('EpEtaSepD', '%.1f' % abs(P['sep_start_to_start_d']))
m('EpEtaRepRms', '%.2f' % P['rms_combined_mJy'])
m('EpEtaDiscRms', '%.2f' % VER['discovery']['rms_combined_mJy'])
m('EpEtaRepDepth', '%.1f' % (VER['discovery']['rms_combined_mJy']
                             / P['rms_combined_mJy']))
m('EpEtaRepT', '%.2f' % P['T_matched_chan_best_drift'])
m('EpEtaExclSig', '%.1f' % P['exclusion_sigma'])
m('EpEtaDiscFlux', '%.1f' % VER['discovery']['flux_mJy'])
m('EpEtaRepFlux', '%.2f' % P['flux_mJy'])
m('EpEtaRepFluxErr', '%.2f' % P['flux_err_mJy'])
m('EpEtaRfiBlocks', '%d' % RFI['n_other_blocks'])
m('EpEtaRfiStars', '%d' % RFI['n_other_stars'])
m('EpEtaRfiCross', '%d' % RFI['n_other_crossings'])
m('EpEtaEdgeChan', '%d' % round(RFI['edge_channels']))

# The two crossings that are BOTH unattributed and rank-flagged: the end of
# the chain.  Taken from the ledger rather than named here, so that if the
# set ever changes the macros follow it and the surrounding prose is forced
# to be rewritten with them.
# ★ Until 2026-09-26 one of them (61 Vir) had no recurrence test at all and
# this generator asserted the gap was exactly one crossing.  Both are now
# measured; the assertion below is the mirror of the old one and fails if a
# gap reopens.
END = [r for r in LED['rows'] if not r['attributed'] and r['screen']]
assert len(END) == 2, ('the number of unattributed rank-flagged crossings '
                       'has changed from two; S5.2.3 names them individually')
assert not LED['summary']['recurrence_gap'], (
    'a rank-flagged unattributed crossing has lost its recurrence test again;'
    ' S5.2.3 asserts that both have one')
# the one whose verdict the epoch correction moves, and the one still
# awaiting a fit, identified by what the ledger says rather than by name
G = [r for r in END if r['fitted']]
U = [r for r in END if not r['fitted']]
assert len(G) == 1 and len(U) == 1, (
    'exactly one of the two rank-flagged unattributed crossings is expected '
    'to be fitted and one outstanding; that is what S5.2.3 says')
G, U = G[0], U[0]
assert G['recurrence'] and U['recurrence'], 'both must carry recurrence now'
m('EpGapStar', G['display'])
m('EpGapEb', '\\texttt{%s}' % G['eb'].replace('_', '\\_'))
m('EpGapT', '%.2f' % G['tstar'])
m('EpGapReCom', '%.2f' % G['committed']['re'])
m('EpGapReCor', '%.2f' % G['adopted']['re'])
m('EpGapD', '%.1f' % G['dch'])
m('EpGapNRep', '%d' % G['recurrence']['n_repeats'])
m('EpGapRepTMax', '%.2f' % G['recurrence']['t_max'])
m('EpOutStar', U['display'])
m('EpOutEb', '\\texttt{%s}' % U['eb'].replace('_', '\\_'))
m('EpOutT', '%.2f' % U['tstar'])
m('EpOutNRep', '%d' % U['recurrence']['n_repeats'])
m('EpOutRepTMax', '%.2f' % U['recurrence']['t_max'])

with open(OUT, 'w') as fh:
    fh.write('%% GENERATED by epoch_v403.py -- do not hand-edit.\n')
    for k in sorted(M):
        fh.write('\\newcommand{\\%s}{%s}\n' % (k, M[k]))

print('epoch_v403: %d tones in %d configurations; above %.1f ch recovered '
      '%.3f vs %.3f, localised %.0f%% vs %d of %d'
      % (len(INJ), len(units), D_LO, f_cor, f_com, 100 * l_cor,
         sum(1 for r in above if r['loc_r6']), len(above)))
print('  Class A control positions reach T>=%.4f %.1f%% of the time '
      '(%d windows); expected %.0f, observed %d'
      % (T_MIN, 100 * rate_a, len(A), exp_a, obs_a))
print('  eta Crv: T* %.4f, rank %d/%d, Re/sigma %.2f -> %.2f, D %.2f ch'
      % (R['tstar'], n_ge, n_ctrl, R['committed']['re'], R['adopted']['re'],
         R['dch']))
print('  -> %s (%d macros)' % (os.path.basename(OUT), len(M)))
