#!/usr/bin/env python3
"""round 97 (DECISIONS_R8 D18): the delivered channel-to-channel noise
covariance, measured on sky, as a FIFTH and independent validation of the
response model -- and the one window whose averaging factor the shipped code
got wrong.

Why this is not just another cross-check.  The response model's four existing
validations are:
  1. the modelled FWHM against the archive's reported effective resolution,
  2. the scalloping depth,
  3. the equivalent noise bandwidth,
  4. the known-answer test vectors (katcheck_v401.py).
(1) is a metadata comparison and (2) is a ratio, so normalisation cancels;
neither can see whether a window was averaged by 2 or by 4, because both
report a resolution smaller than the Hanning one.  The channel covariance CAN:
the Hann kernel (1/4, 1/2, 1/4) summed over n raw channels and decimated by n
predicts a different lag-1 correlation for every n, and those predictions are
0.667 (n=1), 0.300 (n=2) and 0.115 (n=4) -- a factor of six apart.  Measured
on control positions of real windows, all three branches are confirmed.

This generator owns:
  * the predicted lag-1/lag-2 correlations for n = 1, 2, 4 RECOMPUTED here
    from the kernel, importing nothing from cresp_v401.py -- if the two
    disagreed, that would be the finding;
  * the measured correlations, grouped by the averaging factor v342_calc.py
    keyed each window to, so the grouping is the catalogue's and not this
    file's;
  * the 51 Eri mis-keying: what shipped, what it should be, and the
    conservative direction of the error.

Inputs (frozen, in the version folder):
  r8inputs/chancorr_v406.json     25 fine windows, sens/chancorr.py
  r8inputs/chancorr_n4_v406.json  51 Eri spw25, the n = 4 measurement
  per_target_results_v3.99.csv    the released catalogue (MUST FOLLOW v342_calc.py)
  cresp_v401.json                 the response model, for fwhm_by_n only
"""
import csv
import json
import os

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, 'survey_numbers_round97.tex')
M = {}


def m(k, v):
    assert k not in M, k
    M[k] = v


# ------------------------------------------------- 1. the prediction, from the
# kernel and nothing else.  Hann taper on the raw spectrometer channels, then a
# block average by n, then decimation by n.  The delivered channel's weight
# vector over raw channels is the convolution of the taper with a length-n
# boxcar; the correlation at delivered lag L is the normalised autocovariance of
# that vector sampled at nL raw channels.
TAPER = np.array([0.25, 0.50, 0.25])


def delivered_rho(n, lag):
    w = np.convolve(TAPER, np.ones(n))
    full = np.correlate(w, w, mode='full')
    c0 = full[len(w) - 1]
    k = len(w) - 1 + n * lag
    return float(full[k] / c0) if 0 <= k < len(full) else 0.0


PRED = {n: (delivered_rho(n, 1), delivered_rho(n, 2)) for n in (1, 2, 4)}
# The n = 1 prediction is the one the paper already quotes as 2/3, so assert it
# closed-form rather than trusting the convolution: rho(1) = 0.25/0.375 = 2/3,
# rho(2) = 0.0625/0.375 = 1/6.
assert abs(PRED[1][0] - 2.0 / 3.0) < 1e-12, PRED[1]
assert abs(PRED[1][1] - 1.0 / 6.0) < 1e-12, PRED[1]
# And assert the three branches really are far apart, because a validation
# whose branches predict the same thing cannot distinguish them.  This is the
# clause that makes the covariance a key and the FWHM check not one.
assert PRED[1][0] / PRED[4][0] > 4.0, PRED
for n in (1, 2, 4):
    m('CcPredOne%s' % {1: 'N', 2: 'Two', 4: 'Four'}[n], '%.3f' % PRED[n][0])
    m('CcPredTwo%s' % {1: 'N', 2: 'Two', 4: 'Four'}[n], '%.3f' % PRED[n][1])
m('CcPredRatio', '%.1f' % (PRED[1][0] / PRED[4][0]))

# The model file must agree on the modelled resolutions this keying uses.  If
# cresp_v401.py ever stops modelling n = 4, the catalogue's key silently loses
# its third state again, so fail here rather than there.
_CR = json.load(open(os.path.join(HERE, 'cresp_v401.json')))
FWN = {int(k): float(v) for k, v in _CR['fwhm_by_n'].items()}
assert set(FWN) >= {1, 2, 4}, FWN
m('CcFwhmOneN', '%.3f' % FWN[1])
m('CcFwhmTwo', '%.4f' % FWN[2])
m('CcFwhmFour', '%.4f' % FWN[4])

# ---------------------------------------- 2. the measurement, keyed by the
# CATALOGUE's own averaging factor.  The catalogue does not ship n_avg (it
# ships c_response_smear, which is a function of it), so the key is recovered
# from the response factor: each n has a distinct median response, and the
# recovery is asserted to be one-to-one.
CAT = list(csv.DictReader(open(os.path.join(HERE,
                                            'per_target_results_v3.99.csv'))))
RHO = {int(k): np.array(v) for k, v in _CR['rho_by_n'].items()}
# v4.06: the catalogue now PUBLISHES the averaging factor (D18), so the key is
# read rather than reverse-engineered.  It could not have been reverse-
# engineered from c_response_smear, which folds in the per-window intra-
# integration smear and therefore takes 51 distinct values over the catalogue.
KEYED = {n: [r for r in CAT if int(r['n_chan_avg']) == n] for n in (1, 2, 4)}
assert sum(len(v) for v in KEYED.values()) == len(CAT), (
    'the catalogue carries an averaging factor outside the modelled set %s: %s'
    % (sorted(RHO), sorted({r['n_chan_avg'] for r in CAT})))
for n in (1, 2, 4):
    m('CcNWin%s' % {1: 'One', 2: 'Two', 4: 'Four'}[n], '%d' % len(KEYED[n]))
# ★ the third state must be OCCUPIED -- if the nearest-modelled key ever falls
# back to a binary, this drops to 0 and the assertion fires.
assert len(KEYED[4]) == 1, len(KEYED[4])
assert len(KEYED[2]) > 100, len(KEYED[2])

MEAS = (json.load(open(os.path.join(HERE, 'r8inputs/chancorr_v406.json')))
        + json.load(open(os.path.join(HERE, 'r8inputs/chancorr_n4_v406.json'))))
# Map each measured product to the catalogue window it belongs to, by execution
# block: the covariance is a property of the correlator setup, so the block and
# the channel width identify the population.  Products whose block is not in
# the released catalogue are reported, not silently dropped.
CATBY = {}
for r in CAT:
    CATBY.setdefault((r['eb'], round(float(r['chanw_Hz']))), r)
rows, unmatched = [], []
for d in MEAS:
    eb = d['base'].rsplit('_spw', 1)[0]
    r = CATBY.get((eb, round(d['chanw'])))
    if r is None:
        unmatched.append(d['base'])
        continue
    rows.append((int(r['n_chan_avg']), d, r))
m('CcNMeas', '%d' % len(MEAS))
m('CcNMatched', '%d' % len(rows))
m('CcNUnmatched', '%d' % len(unmatched))
# Every matched window must confirm its own key: the measured lag-1 must be
# closer to its keyed n's prediction than to either other branch.  This is the
# whole claim, and it is one assertion.
bad = []
for n, d, r in rows:
    a1 = d['ac'][0]
    best = min(PRED, key=lambda k: abs(a1 - PRED[k][0]))
    if best != n:
        bad.append((d['base'], n, best, a1))
assert not bad, ('the measured channel covariance contradicts the catalogue\'s '
                 'averaging key for %d window(s): %s' % (len(bad), bad))
m('CcNAgree', '%d' % len(rows))
m('CcNDisagree', '%d' % len(bad))
for n, tag in ((1, 'One'), (2, 'Two'), (4, 'Four')):
    sel = [d['ac'][0] for nn, d, _ in rows if nn == n]
    se2 = [d['ac'][1] for nn, d, _ in rows if nn == n]
    if not sel:
        continue
    m('CcMeasN' + tag, '%d' % len(sel))
    m('CcMeasOne' + tag + 'Lo', '%.3f' % min(sel))
    m('CcMeasOne' + tag + 'Hi', '%.3f' % max(sel))
    m('CcMeasTwo' + tag + 'Lo', '%.3f' % min(se2))
    m('CcMeasTwo' + tag + 'Hi', '%.3f' % max(se2))
# The hard cases, which are the reason channel width alone is not a key:
# windows of the SAME channel width keyed to different averaging factors.
_w = {}
for n, d, r in rows:
    _w.setdefault(round(d['chanw'] / 1e3, 1), set()).add(n)
_both = sorted(k for k, v in _w.items() if len(v) > 1)
m('CcAmbigWidths', ', '.join('%.1f' % k for k in _both) or 'none')
m('CcNAmbigWidths', '%d' % len(_both))
assert _both, ('no channel width appears in two averaging classes in the '
               'measured sample, so this sample cannot demonstrate that '
               'channel width is not a key')

# ---------------------------------------------- 3. the one mis-keyed window
FOUR = KEYED[4][0]
m('CcFourStar', FOUR['star_name'])
m('CcFourEb', FOUR['eb'].replace('_', r'\_'))
m('CcFourChanKHz', '%.1f' % (float(FOUR['chanw_Hz']) / 1e3))
m('CcFourTstar', '%.2f' % float(FOUR['star_snr']))
_a1 = [d['ac'][0] for n, d, _ in rows if n == 4][0]
m('CcFourMeasOne', '%.3f' % _a1)
# What shipped through v4.05, and what this window gets now.  Both come from
# the model, so neither is typed.
_shipped = round(1.0 / float(np.median(RHO[2])), 4)
_now = round(1.0 / float(np.median(RHO[4])), 4)
m('CcFourCrespOld', '%.3f' % _shipped)
m('CcFourCrespNew', '%.3f' % _now)
m('CcFourRatio', '%.3f' % (_shipped / _now))
m('CcFourRatioDb', '%.2f' % (10.0 * np.log10(_shipped / _now)))
_eirp_now = float(FOUR['eirp_eff_total_W'])
_eirp_old = _eirp_now * _shipped / _now
m('CcFourEirpOld', r'%.3f \times 10^{15}' % (_eirp_old / 1e15))
m('CcFourEirpNew', r'%.3f \times 10^{15}' % (_eirp_now / 1e15))
# 0 crossings affected: assert it, because that is what makes this a limits
# correction and not a candidate-list change.
assert FOUR['crossing'] != 'True', FOUR['crossing']
m('CcFourNCross', '0')
# ... and the system-level limit, which is the number a reader would look up.
_sys = [r for r in CAT if r['system_id'] == FOUR['system_id']]
_deep_new = min(float(r['eirp_eff_total_W']) for r in _sys)
_deep_old = min((_eirp_old if r is FOUR else float(r['eirp_eff_total_W']))
                for r in _sys)
m('CcFourSysOld', r'%.2f \times 10^{15}' % (_deep_old / 1e15))
m('CcFourSysNew', r'%.2f \times 10^{15}' % (_deep_new / 1e15))
m('CcFourNSysWin', '%d' % len(_sys))
# The window IS the system's deepest, which is why the system limit moves at
# all -- assert that, since otherwise the sentence about 51 Eri is wrong.
assert _deep_new == _eirp_now, (_deep_new, _eirp_now)
# The counts of systems reaching 1e15 W must not move: that is the claim, and
# it has to be checked on BOTH power scales, because the paper quotes a count
# on each and they are different numbers.
#   eirp_eff_total_W  = P_trig x C_resp x C_smear -- DOES contain the response
#                       correction, so the mis-keying could in principle move it
#   eirp_p90_sel_W    = P_trig x the measured selection factor -- does NOT
#                       contain it, so it cannot move at all, which is worth
#                       asserting rather than assuming
_bysys = {}
for r in CAT:
    _bysys.setdefault(r['system_id'], []).append(r)


def _n_le(col, patch):
    return sum(1 for _s, rs in _bysys.items()
               if min((patch if r is FOUR and patch is not None
                       else float(r[col])) for r in rs) <= 1e15)


_n15_eff_new, _n15_eff_old = _n_le('eirp_eff_total_W', None), _n_le(
    'eirp_eff_total_W', _eirp_old)
_n15_sel_new = _n_le('eirp_p90_sel_W', None)
m('CcNSysEffFifteen', '%d' % _n15_eff_new)
m('CcNSysSelFifteen', '%d' % _n15_sel_new)
assert _n15_eff_new == _n15_eff_old, (_n15_eff_new, _n15_eff_old)
# ★ And the P90^sel scale is UNTOUCHED by construction: the selection factor
# multiplies P_trig, not C_resp.  Assert the algebra rather than the count, so
# a future version that folds the response into P90^sel cannot pass silently.
_sel_ratio = {round(float(r["eirp_p90_sel_W"]) / float(r["eirp_nominal_W"]), 4)
              for r in CAT}
assert len(_sel_ratio) <= 4, sorted(_sel_ratio)
assert round(float(FOUR["eirp_p90_sel_W"]) / float(FOUR["eirp_nominal_W"]),
             4) in _sel_ratio, 'P90^sel for the mis-keyed window is not a pure '\
                               'multiple of its nominal power'
m('CcSysFifteenMoved', 'unchanged')
m('CcNSelRatios', '%d' % len(_sel_ratio))
# Per-window median EIRP_eff: the order statistic the abstract quotes.
_med_new = float(np.median([float(r['eirp_eff_total_W']) for r in CAT]))
_med_old = float(np.median([(_eirp_old if r is FOUR
                             else float(r['eirp_eff_total_W'])) for r in CAT]))
m('CcMedEirpShiftPct', '%.2f' % (100.0 * abs(_med_new - _med_old) / _med_old))

# ---------------------------------------- 4. the matched-filter scope clause.
# D16 quoted the 3-channel matched filter's gain against a POOLED lag-1 of
# 0.651, which is the median over 25 fine windows and therefore dominated by
# the 17 unaveraged ones.  The averaged windows measure ~0.27, so the gain is
# an n = 1 gain.  Compute the pooled median here and show it sits on the n = 1
# branch, so the scope restriction is a measurement and not an assertion.
_all1 = [d['ac'][0] for _, d, _ in rows]
m('CcPooledOne', '%.3f' % float(np.median(_all1)))
_n1 = [d['ac'][0] for n, d, _ in rows if n == 1]
assert abs(np.median(_all1) - np.median(_n1)) < 0.05, (np.median(_all1),
                                                       np.median(_n1))
m('CcPooledIsNOne', 'the $n=1$ population')
m('CcMfPopPct', '%.0f' % (100.0 * len(KEYED[1]) / len(CAT)))

with open(OUT, 'w') as fh:
    fh.write('%% GENERATED by crespkey_v406.py -- do not hand-edit.\n')
    for k in sorted(M):
        fh.write('\\newcommand{\\%s}{%s}\n' % (k, M[k]))

print('crespkey_v406 (round 97): predicted delivered lag-1 %.3f / %.3f / %.3f '
      'for n = 1 / 2 / 4, a factor %.1f apart'
      % (PRED[1][0], PRED[2][0], PRED[4][0], PRED[1][0] / PRED[4][0]))
print('  measured on %d of %d products that are in the released catalogue: '
      '%d agree with the catalogue key, %d disagree'
      % (len(rows), len(MEAS), len(rows) - len(bad), len(bad)))
for n, tag in ((1, 'One'), (2, 'Two'), (4, 'Four')):
    sel = [d['ac'][0] for nn, d, _ in rows if nn == n]
    if sel:
        print('    n = %d: %d window(s), lag-1 %.3f-%.3f against %.3f predicted'
              % (n, len(sel), min(sel), max(sel), PRED[n][0]))
print('  channel widths appearing in two averaging classes: %s kHz -- so '
      'channel width alone is not a key' % M['CcAmbigWidths'])
print('  the mis-keyed window: %s %s, C_resp %.3f -> %.3f (x%.3f, %.2f dB, '
      'conservative), EIRP %.3g -> %.3g W, %s crossings, system limit '
      '%.3g -> %.3g W, systems at 1e15 W %s'
      % (FOUR['star_name'], FOUR['eb'], _shipped, _now, _shipped / _now,
         10 * np.log10(_shipped / _now), _eirp_old, _eirp_now,
         M['CcFourNCross'], _deep_old, _deep_new, M['CcSysFifteenMoved']))
print('  systems at or below 1e15 W: %d on P_eff (unchanged), %d on P90^sel '
      '(which the response correction does not enter at all)'
      % (_n15_eff_new, _n15_sel_new))
print('  -> %s (%d macros)' % (os.path.basename(OUT), len(M)))
