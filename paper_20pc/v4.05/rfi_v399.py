#!/usr/bin/env python3
"""R2-3 (v3.99): the RFI vetting statement for the unattributed events,
by measurement rather than by assertion.

Referee 2 observed that the paper never states what was done to exclude
radio-frequency interference for the four unattributed stage-1 events.
It is a fair criticism: the manuscript relied on the reader knowing that
millimetre interferometry is a hostile environment for RFI, and never
said so or tested it.

Four tests are computed here, all from the frozen catalogue:

 (1) SKY-FREQUENCY RECURRENCE ACROSS UNRELATED TARGETS. Interference is a
     property of the observatory, not of the star. A carrier of
     terrestrial origin at a fixed sky frequency should appear in every
     window that covers that frequency, whatever it is pointing at. For
     each event we count the other windows in the survey that cover its
     frequency (or its window), how many stars and blocks they represent,
     and how many of them carry a threshold crossing.

 (2) CROSSING CLUSTERING IN SKY FREQUENCY. If interference dominated the
     crossing population, crossings would pile up at particular sky
     frequencies. We bin all released crossing frequencies at 1 MHz and
     report the largest multiplicity, and the same statistic for the
     shuffled-within-window null.

 (3) FRACTIONAL POSITION IN THE SPECTRAL WINDOW. An artefact of the
     signal chain sits at a fixed intermediate frequency, so it appears
     at the same fractional position in every window rather than at the
     same sky frequency. We report where the crossings with a released
     frequency fall.

 (4) WINDOW-EDGE PROXIMITY. Band-edge and baseband-edge roll-off is the
     one instrumental defect known to generate excess power, so we report
     each event's distance from its window edges in channels.

The physical argument, which the tests support but do not establish, goes
in the manuscript: the searched bands lie at 89-873 GHz, above every
allocated terrestrial service; the array is at 5000 m; and a signal that
is not in the far field at the phase centre does not fringe-track, so it
is suppressed rather than imaged.
"""
import csv
import json
import os
import collections

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
CAT = os.path.join(HERE, 'per_target_results_v3.99.csv')
OUT = os.path.join(HERE, 'survey_numbers_round49.tex')
RNG = np.random.default_rng(20260921)


def F(x):
    try:
        return float(x)
    except (TypeError, ValueError):
        return None


ROWS = list(csv.DictReader(open(CAT)))
# The attribution rule is v381_calc.py's and is reproduced, not guessed:
# a stage-1 event is attributed iff its crossing lies within +-50 km/s of a
# catalogued transition in the stellar frame.
TUBE_KMS = 50.0
UNATT = [r for r in ROWS if r['stage1_flag'] == 'True'
         and abs(F(r['line_offset_kms']) or 9e9) > TUBE_KMS]
# v3.99: the count is DERIVED, not asserted against a literal. The ACA
# control-geometry repair changed it from 4 to 2 (HD 23484 and HD 14055 were
# artefacts of contaminated controls), and a hard-coded 4 would have silently
# blocked the corrected result rather than reporting it.
assert UNATT, 'no unattributed stage-1 events found; the attribution rule or '\
              'the catalogue is wrong'


def lohi(r):
    return (min(F(r['flo_GHz']), F(r['fhi_GHz'])),
            max(F(r['flo_GHz']), F(r['fhi_GHz'])))


# ---- (1) sky-frequency recurrence across unrelated targets --------------
per = {}
for r in UNATT:
    lo, hi = lohi(r)
    fc = F(r['f_cross_GHz'])
    others, ostars, oblocks, ocross = [], set(), set(), 0
    for q in ROWS:
        if q['eb'] == r['eb'] and lohi(q) == (lo, hi):
            continue
        qlo, qhi = lohi(q)
        if fc is not None:
            hit = qlo <= fc <= qhi
        else:
            hit = qlo < hi and qhi > lo        # any overlap
        if not hit:
            continue
        others.append(q)
        if q['star_name'] != r['star_name']:
            ostars.add(q['star_name'])
            oblocks.add(q['eb'])
            if q['crossing'] == 'True':
                ocross += 1
    # The sharp test, where a released crossing frequency allows it: does
    # any OTHER star carry a crossing at the same sky frequency, within one
    # channel? Window overlap is 2 GHz wide and proves nothing; a
    # same-channel coincidence across unrelated targets would be decisive.
    samechan = []
    if fc is not None:
        cw = (F(r['chanw_Hz']) or 0.0) / 1e9
        for q in ROWS:
            qf = F(q['f_cross_GHz'])
            if (qf is not None and q['star_name'] != r['star_name']
                    and abs(qf - fc) <= max(cw, 1e-6)):
                samechan.append((q['star_name'], q['eb'], qf))
    per[r['eb']] = {
        'n_same_channel_other_stars': len(samechan),
        'same_channel': samechan,
        'star': r['star_name'], 'band': r['band'],
        'f_cross_GHz': fc, 'flo': lo, 'fhi': hi,
        'n_overlap_windows': len(others),
        'n_other_stars': len(ostars),
        'n_other_blocks': len(oblocks),
        'n_other_crossings': ocross,
    }

tot_same_chan = sum(v['n_same_channel_other_stars'] for v in per.values())
n_testable = sum(1 for v in per.values() if v['f_cross_GHz'] is not None)
tot_other_stars = sum(v['n_other_stars'] for v in per.values())
tot_other_cross = sum(v['n_other_crossings'] for v in per.values())

# ---- (2) clustering of crossing frequencies in sky frequency -----------
fc_all = [F(r['f_cross_GHz']) for r in ROWS if F(r['f_cross_GHz'])]
BIN_MHZ = 1.0
bins = collections.Counter(int(round(f * 1000.0 / BIN_MHZ)) for f in fc_all)
maxmult = max(bins.values())
nbins = len(bins)
# the null: keep each crossing in its own window but randomise where in it
win = [(lohi(r), F(r['f_cross_GHz'])) for r in ROWS if F(r['f_cross_GHz'])]
nullmax = []
for _ in range(2000):
    b = collections.Counter()
    for (lo, hi), _f in win:
        b[int(round(RNG.uniform(lo, hi) * 1000.0 / BIN_MHZ))] += 1
    nullmax.append(max(b.values()))
nullmax = np.asarray(nullmax)

# ---- (3) fractional position within the spectral window ---------------
frac = [(F(r['f_cross_GHz']) - lohi(r)[0]) / (lohi(r)[1] - lohi(r)[0])
        for r in ROWS if F(r['f_cross_GHz']) and lohi(r)[1] > lohi(r)[0]]
frac = np.asarray(frac)
# KS against uniform, computed here rather than imported
fs = np.sort(frac)
n = fs.size
d = max(np.max(np.arange(1, n + 1) / n - fs),
        np.max(fs - np.arange(0, n) / n))
ks_lam = (np.sqrt(n) + 0.12 + 0.11 / np.sqrt(n)) * d
ks_p = 2.0 * sum((-1) ** (k - 1) * np.exp(-2.0 * k * k * ks_lam ** 2)
                 for k in range(1, 100))
ks_p = float(min(1.0, max(0.0, ks_p)))

# ---- (4) window-edge proximity, in channels ---------------------------
edges = {}
for r in UNATT:
    lo, hi = lohi(r)
    cw = F(r['chanw_Hz'])
    fc = F(r['f_cross_GHz'])
    if fc is None or not cw:
        edges[r['eb']] = None
        continue
    edges[r['eb']] = min(fc - lo, hi - fc) * 1e9 / cw

res = {
    'per_event': per,
    'total_other_stars': tot_other_stars,
    'total_other_crossings': tot_other_cross,
    'n_crossings_with_freq': len(fc_all),
    'bin_MHz': BIN_MHZ,
    'n_occupied_bins': nbins,
    'max_multiplicity': maxmult,
    'null_max_mean': float(nullmax.mean()),
    'null_max_p95': float(np.percentile(nullmax, 95)),
    'p_maxmult': float((nullmax >= maxmult).mean()),
    'frac_ks_D': float(d), 'frac_ks_p': ks_p, 'n_frac': int(n),
    'frac_median': float(np.median(frac)),
    'edge_channels': edges,
}
json.dump(res, open(os.path.join(HERE, 'rfi_v399.json'), 'w'),
          indent=1, sort_keys=True, default=str)

L = ['%% GENERATED by rfi_v399.py -- do not hand-edit.\n']


def m(k, v):
    L.append('\\newcommand{\\%s}{%s}\n' % (k, v))


m('RfiSameChan', '%d' % tot_same_chan)
m('RfiNTestable', '%d' % n_testable)
m('RfiNNotTestable', '%d' % (len(UNATT) - n_testable))
# Macro-generated grammar: the prose read "2 has a released crossing
# frequency" and then "For the other 0 the pipeline stored no peak
# frequency", a sentence about an empty set. Emit the verb and the whole
# trailing clause here, where the counts are known.
_nn = len(UNATT) - n_testable
m('RfiTestableVerb', 'has' if n_testable == 1 else 'have')
m('RfiNotTestableClause',
  ('' if _nn == 0 else
   ' For the %s the pipeline stored no peak frequency, so this test cannot '
   'be run on %s and we do not claim it was.'
   % ('other one' if _nn == 1 else 'other %d' % _nn,
      'it' if _nn == 1 else 'them')))
m('RfiOtherStars', '%d' % tot_other_stars)
m('RfiOtherCross', '%d' % tot_other_cross)
m('RfiOtherStarsMin', '%d' % min(v['n_other_stars'] for v in per.values()))
m('RfiOtherStarsMax', '%d' % max(v['n_other_stars'] for v in per.values()))
m('RfiOtherBlocks', '%d' % sum(v['n_other_blocks'] for v in per.values()))
m('RfiNCross', '%d' % len(fc_all))
m('RfiBinMHz', '%.0f' % BIN_MHZ)
m('RfiMaxMult', '%d' % maxmult)
m('RfiNullMaxMean', '%.1f' % nullmax.mean())
m('RfiNullMaxP', '%.2f' % res['p_maxmult'])
m('RfiFracMed', '%.2f' % res['frac_median'])
m('RfiFracKsD', '%.3f' % d)
m('RfiFracKsP', '%.2f' % ks_p)
m('RfiNFrac', '%d' % n)
_ed = [v for v in edges.values() if v is not None]
if _ed:
    m('RfiEdgeChanMin', '%.0f' % min(_ed))
m('RfiFreqLo', '%.0f' % min(lohi(r)[0] for r in ROWS))
m('RfiFreqHi', '%.0f' % max(lohi(r)[1] for r in ROWS))
open(OUT, 'w').writelines(L)

print('%s: %d macros' % (os.path.basename(OUT), len(L) - 1))
print('RFI vetting of the %d unattributed events' % len(UNATT))
for eb, v in per.items():
    print('  %-14s B%s  %s  overlapping windows %4d  other stars %3d  '
          'blocks %3d  crossings there %d'
          % (v['star'][:14], v['band'],
             ('%.4f GHz' % v['f_cross_GHz']) if v['f_cross_GHz']
             else '%.2f-%.2f GHz' % (v['flo'], v['fhi']),
             v['n_overlap_windows'], v['n_other_stars'],
             v['n_other_blocks'], v['n_other_crossings']))
print('  totals: %d other-star windows cover these frequencies in %d '
      'blocks, and %d of them carry a crossing'
      % (tot_other_stars, res['total_other_stars'] and
         sum(v['n_other_blocks'] for v in per.values()), tot_other_cross))
print('  same-channel coincidence with an unrelated star: %d, over the %d '
      'of %d events with a released crossing frequency'
      % (tot_same_chan, n_testable, len(UNATT)))
print('clustering of %d released crossing frequencies at %.0f MHz: '
      'max multiplicity %d, null %.1f (95%% %.0f), p = %.3f'
      % (len(fc_all), BIN_MHZ, maxmult, nullmax.mean(),
         res['null_max_p95'], res['p_maxmult']))
print('fractional position in window: median %.2f, KS D = %.3f p = %.2f '
      'over %d crossings' % (res['frac_median'], d, ks_p, n))
print('edge proximity of the events with a released frequency: %s channels'
      % ', '.join('%.0f' % v for v in _ed))
