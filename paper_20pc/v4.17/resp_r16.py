#!/usr/bin/env python3
r"""round 620 -> survey_numbers_round620.tex, resp_r16.json

WHERE THE CHANNEL RESPONSE IS APPLIED, AND THREE THINGS THAT WERE DESCRIBED
RATHER THAN MEASURED.

★★★★ 1.  THE CHANNEL RESPONSE IS APPLIED EXACTLY ONCE, AND THE PLACEMENT IS
AN IDENTITY RATHER THAN AN ARGUMENT.

  * `campaign_m3a_v399.py` takes each window's own `S_min_measured_Jy`, which
    is the bare 5 sigma of that window's combined spectrum, and walks an
    amplitude ladder in units of it.  So P_trig is NOMINAL: no response
    correction is in it, and `pbaudit_v408.py` asserts the matching identity
    on the released rows, S_min = 5 sigma / A.
  * `inject_vis_v399.py` deposits a tone of TOTAL flux f x S_min by splitting
    it linearly between the two straddled channels and convolving with the
    0.25/0.5/0.25 channel kernel.  The peak channel therefore receives
    `deposited_phase_mean` = 0.4375 of the tone, averaged over sub-channel
    phase, and the pipeline triggers on that peak channel.
  * The measured ninety-per-cent point is a TOTAL flux: 3.03 P_trig.  Hence

        3.03  =  (1 / 0.4375)  x  (3.03 x 0.4375)
              =    2.29        x     1.33
                response       margin above 5 sigma

    identically.  The response factor 2.29 lies inside the +/-2.00-2.36
    placement envelope the appendix derives from the kernel, and the residual
    1.33 is what the peak channel must hold above the nominal trigger for nine
    carriers in ten to come back.  EIRP_90 = 3.03 P_trig therefore carries the
    response ONCE, inside the measured completeness; P_trig, S_min and the
    bare 5 sigma symbols of the context figure carry it NOT AT ALL.

  ★ THE STALE NUMBER THIS REPLACES.  `strata_v411.py` emits
    `\InjPeakAtNinety` as `blanket p90 x deposited mean` = 4.4152 x 0.4375 =
    1.93, and 4.4152 is the RETIRED rank-gated, ring-stratified completeness.
    On the adopted trigger-alone factor the same quantity is 1.33.  The table
    row that quoted 1.93 was describing a criterion the paper no longer uses.

2.  R2a-1: whether the 49 injected windows sample the conditions of all 402.
    Six properties are compared between the injected set and the population:
    channel width, on-source integration time, noise, control-ring maximum,
    de-drifting burden (eta_drift = |nudot| tau / dnu_ch) and the smearing
    retention.  Five agree in the median to six per cent; the noise does not,
    the injected windows being 1.7 times noisier, which is a consequence of
    the draw being on BLOCKS.  The ladder is in units of each window's own
    threshold, so absolute depth is not a covariate of the factor by
    construction -- and that is measured here rather than asserted, by
    splitting the injected set at the median of each property in turn.

3.  R2a-2: whether the 125 blocks with no phase-stability record could be
    systematically worse than the 279 that have one.  They could, and the
    proxy says they are: their median maximum baseline is 279 m against 46 m.
    Each unmeasured window is therefore given the measured blocks within a
    factor of two of its own baseline -- no fit, no imputation into the
    published limits -- and the median and ninetieth percentile of that
    matched set are reported as what the correction would be.

4.  Minor 21: adopting ALMA's 1.13 lambda/D beamwidth in place of the
    pipeline's 1.22 Airy-null one, with the consequence for every published
    statistic measured from `pb_atten_fwhm_r11.csv`, which `sens_r11.py`
    already writes for all 1651 rows.

5.  Minor 20: the two parallax figures are different statistics, and the
    reason the median limit moves ten times more than the median window is
    counted rather than explained.

NOTHING IS TYPED.  Inputs are the released catalogue, `sens_r11.json`,
`strata_v411.json`, `r13inputs/decor_r13.json`, `r11inputs/window_geometry_
r11.json`, `pb_atten_fwhm_r11.csv` and `pxapply_v411.json`.

    python3 resp_r16.py [--out DIR] [--drive N]

--drive 1..9 breaks one assertion each and nothing else; --drive 0 means "no
perturbation, but do not write a path production reads".
"""
import collections
import csv
import json
import math
import os
import statistics as st
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROUND = 620

DRIVE = None
OUTDIR = HERE
for _i, _a in enumerate(sys.argv):
    if _a == '--drive':
        DRIVE = int(sys.argv[_i + 1])
    if _a == '--out':
        OUTDIR = sys.argv[_i + 1]
SUF = '' if DRIVE is None else '_drive%d' % DRIVE
OUT = os.path.join(OUTDIR, 'survey_numbers_round%d%s.tex' % (ROUND, SUF))
OUT_JSON = os.path.join(OUTDIR, 'resp_r16%s.json' % SUF)

C_UM_GHZ = 299792.458          # micron * GHz
BL_MATCH = 2.0                 # the factor in baseline length a proxy match allows
PB_LOW = 0.9                   # the response level the appendix counts windows below

MACROS, FAIL = [], []


def m(name, val):
    assert name.isalpha(), 'a LaTeX macro name may contain letters only: %r' % name
    assert not any(x.startswith('\\newcommand{\\%s}' % name) for x in MACROS), name
    MACROS.append('\\newcommand{\\%s}{%s}' % (name, val))


def ck(label, ok, detail=''):
    if not ok:
        FAIL.append(label)
    print('  %-74s %s  %s' % (label[:74], 'PASS' if ok else 'FAIL', detail))


def med(x):
    return st.median(x)


# ------------------------------------------------------------------- inputs
CAT = list(csv.DictReader(open(os.path.join(
    HERE, 'per_target_results_v3.99.csv'))))
SENS = json.load(open(os.path.join(HERE, 'sens_r11.json')))
STRA = json.load(open(os.path.join(HERE, 'strata_v411.json')))
DECOR = json.load(open(os.path.join(HERE, 'r13inputs', 'decor_r13.json')))
GEOM = json.load(open(os.path.join(HERE, 'r11inputs',
                                   'window_geometry_r11.json')))['windows']
PBF = list(csv.DictReader(open(os.path.join(HERE, 'pb_atten_fwhm_r11.csv'))))
PXA = json.load(open(os.path.join(HERE, 'pxapply_v411.json')))

CAT_A = [r for r in CAT if r['search_class'] == 'A']
P90 = float(SENS['headline']['mult_a'])
DEP = float(STRA['response']['deposited_phase_mean'])

# ===================================================================== 1
# THE PLACEMENT OF THE CHANNEL RESPONSE, AS A FACTORISATION OF THE MEASURED
# COMPLETENESS.
print('\n1  where the channel response is applied')
RESP_FAC = 1.0 / DEP
MARGIN = P90 * DEP
if DRIVE == 1:
    MARGIN = P90                      # as if the peak channel took the lot
ck('the measured completeness factorises exactly into the channel response '
   'the injections carry and the margin above the nominal trigger',
   abs(RESP_FAC * MARGIN - P90) < 1e-9,
   '%.4f x %.4f = %.4f against an adopted %.4f'
   % (RESP_FAC, MARGIN, RESP_FAC * MARGIN, P90))
# The envelope the appendix quotes comes from the kernel's peak-channel
# fraction at a channel centre and on a boundary.  The factor the injections
# actually carry must lie inside it, or the deposition is not the response.
ENV_LO = 1.0 / float(STRA['response']['exact_centre'])
ENV_HI = 1.0 / float(STRA['response']['exact_edge'])
_rf = RESP_FAC if DRIVE != 2 else 9.9
ck('and the factor the injections carry lies inside the placement envelope '
   'the kernel itself gives', ENV_LO <= _rf <= ENV_HI,
   'x%.2f inside x%.2f-x%.2f' % (_rf, ENV_LO, ENV_HI))
# The nominal trigger must be free of it: S_min = 5 sigma / A on every row,
# with no response term anywhere in the identity.
_worst = max(abs(5 * float(r['rms_mJy']) / float(r['pb_atten'])
                 - float(r['smin_mJy'])) / float(r['smin_mJy']) for r in CAT)
if DRIVE == 3:
    _worst = 0.5
ck('the quoted threshold is the bare five sigma over the beam response, with '
   'no response correction in it, on every released row', _worst < 1e-3,
   'worst residual %.1e over %d rows' % (_worst, len(CAT)))
m('RpRespFac', '%.2f' % RESP_FAC)
# ★ THREE DECIMALS, DELIBERATELY.  The appendix prints this factorisation as
# an identity -- "3.03 P_trig is x2.29 for the channel response and x<this>
# for the margin" -- and at two decimals the PRINTED numbers do not satisfy
# it: 2.29 x 1.33 = 3.05, not 3.03.  A reader who multiplies the one
# arithmetic identity the paper volunteers must get the published product, so
# the factor that carries the rounding carries the extra digit.  The check
# below is on the printed strings and not on the floats, which is the whole
# point: the float identity is already asserted above and passed while the
# typeset one failed.
m('RpMarginNinety', '%.3f' % MARGIN)
_pv = {x.split('{')[1].strip('}\\'): float(x.split('{')[-1].rstrip('}'))
       for x in MACROS if 'RpRespFac' in x or 'RpMarginNinety' in x}
_prod = _pv['RpRespFac'] * _pv['RpMarginNinety']
if DRIVE == 10:
    _prod = 9.99
ck('and the identity holds between the numbers as PRINTED, not only between '
   'the floats behind them, because the appendix asks the reader to multiply '
   'them', abs(round(_prod, 2) - round(P90, 2)) < 1e-9,
   '%s x %s = %.4f against a published %.2f'
   % (_pv['RpRespFac'], _pv['RpMarginNinety'], _prod, P90))

# ===================================================================== 2
# R2a-1.  REPRESENTATIVENESS OF THE INJECTED SET, SIX PROPERTIES.
print('\n2  do the %d injected windows sample the conditions of the %d'
      % (len(SENS['ring']), len(CAT_A)))
RING = SENS['ring']
PERW = SENS['per_window']
_by = collections.defaultdict(list)
for r in CAT_A:
    _by[r['eb']].append(r)
ROW = {}
for g, v in RING.items():
    # the campaign's own clean ring maximum identifies the window inside the
    # block; a block-only key averages two windows
    cand = _by.get(g.rsplit('_spw', 1)[0], [])
    if cand:
        ROW[g] = min(cand, key=lambda r: abs(float(r['ctrl_max_snr']) - v))
_dist = {(r['eb'], r['flo_GHz'], r['fhi_GHz']) for r in ROW.values()}
ck('every injected window joins one released Class A row and no two join the '
   'same one', len(ROW) == len(RING) and len(_dist) == len(ROW),
   '%d windows, %d rows, %d distinct' % (len(RING), len(ROW), len(_dist)))

AXES = (('the channel width', lambda r: float(r['chanw_Hz'])),
        ('the integration time', lambda r: float(r['on_source_s'])),
        ('the noise level', lambda r: float(r['rms_mJy'])),
        ('the control-ring maximum', lambda r: float(r['ctrl_max_snr'])),
        ('the de-drifting burden', lambda r: float(r['eta_drift'])),
        ('the smearing retention', lambda r: float(r['eta_smear_adopted'])))
INJ = [ROW[g] for g in sorted(ROW)]
COV, SPLIT = {}, {}
for name, f in AXES:
    p = sorted(f(r) for r in CAT_A)
    a = sorted(f(r) for r in INJ)
    COV[name] = dict(pop_med=med(p), inj_med=med(a),
                     ratio=med(a) / med(p),
                     pop_range=[p[0], p[-1]], inj_range=[a[0], a[-1]],
                     covers_central=(a[0] <= p[int(0.1 * len(p))]
                                     and a[-1] >= p[int(0.9 * len(p))]))
    # and what the property does to the factor, measured by splitting the
    # injected set at its own median
    pr = sorted((f(ROW[g]), PERW[g]['trig']) for g in ROW)
    h = len(pr) // 2
    SPLIT[name] = dict(lower=med([x[1] for x in pr[:h]]),
                       upper=med([x[1] for x in pr[h:]]))
    SPLIT[name]['shift'] = abs(SPLIT[name]['upper'] - SPLIT[name]['lower'])
    print('  %-26s pop %10.4g  inj %10.4g  x%.3f  central %s  '
          'factor shift %.3f'
          % (name, COV[name]['pop_med'], COV[name]['inj_med'],
             COV[name]['ratio'], COV[name]['covers_central'],
             SPLIT[name]['shift']))

N_COVER = sum(1 for v in COV.values() if v['covers_central'])
if DRIVE == 4:
    N_COVER -= 1
ck('every one of the %d properties spans the central eight-tenths of the '
   'population' % len(AXES), N_COVER == len(AXES),
   '%d of %d' % (N_COVER, len(AXES)))
WORST = max(COV, key=lambda k: abs(math.log(COV[k]['ratio'])))
OTHER = max(abs(COV[k]['ratio'] - 1.0) for k in COV if k != WORST)
ck('exactly one property is unrepresented in the median, so it can be named '
   'rather than a blanket shortfall quoted',
   abs(COV[WORST]['ratio'] - 1.0) > 2.0 * OTHER,
   '%s at x%.2f against %.1f per cent on every other'
   % (WORST, COV[WORST]['ratio'], 100 * OTHER))
SHIFT_AXIS = max(SPLIT, key=lambda k: SPLIT[k]['shift'])
SHIFT_MAX = SPLIT[SHIFT_AXIS]['shift']
IND_LO, IND_HI = SENS['individual']['lo'], SENS['individual']['hi']
_sm = SHIFT_MAX if DRIVE != 5 else 9.0
ck('splitting the injected set on any of the six properties moves the median '
   'factor by less than the dispersion between individual windows',
   _sm < (IND_HI - IND_LO) / 2.0,
   'largest shift %.2f P_trig on %s, against a half-spread of %.2f'
   % (_sm, SHIFT_AXIS, (IND_HI - IND_LO) / 2.0))
m('RpNAxis', '%d' % len(AXES))
m('RpCovWorstAxis', WORST)
m('RpCovWorstRatio', '%.1f' % COV[WORST]['ratio'])
m('RpCovOtherPct', '%.1f' % (100 * OTHER))
m('RpFacShiftMax', '%.2f' % SHIFT_MAX)

# ===================================================================== 3
# R2a-2.  COULD THE UNMEASURED BLOCKS BE WORSE?  PROXY: BASELINE LENGTH.
print('\n3  the %d blocks with no phase-stability record'
      % (len({r['eb'] for r in CAT}) - len(DECOR['blocks'])))
GB = collections.defaultdict(list)
for w in GEOM:
    GB[w['eb']].append(w)


def bmax(eb):
    v = [w['bmax'] for w in GB.get(eb, []) if w.get('bmax')]
    return max(v) if v else None


def opt(um, f_ghz):
    """How much a limit must be raised, as a fraction, at this frequency."""
    phi = math.radians(360.0 * um / (C_UM_GHZ / f_ghz))
    return 1.0 / math.exp(-phi * phi / 2.0) - 1.0


BLK = DECOR['blocks']
EBS = sorted({r['eb'] for r in CAT})
MEAS = [e for e in EBS if e in BLK]
UNM = [e for e in EBS if e not in BLK]
BL_M = sorted(bmax(e) for e in MEAS if bmax(e))
BL_U = sorted(bmax(e) for e in UNM if bmax(e))
_blu = med(BL_U) if DRIVE != 6 else med(BL_M)
ck('the unmeasured blocks are NOT a random subset: their baselines are '
   'systematically longer, which is the direction that loses coherence',
   _blu > 2.0 * med(BL_M),
   'median %.0f m over %d unmeasured against %.0f m over %d measured'
   % (_blu, len(BL_U), med(BL_M), len(BL_M)))

REF = [(bmax(e), BLK[e]['path_rms_um']) for e in MEAS if bmax(e)]


def matched(b):
    v = [p for bb, p in REF if BL_M[0] and b / BL_MATCH <= bb <= b * BL_MATCH]
    if len(v) < 5:
        v = [p for bb, p in REF if b / BL_MATCH ** 2 <= bb <= b * BL_MATCH ** 2]
    return sorted(v)


_cache, O_M, O_U = {}, [], []
for r in CAT:
    f = 0.5 * (float(r['flo_GHz']) + float(r['fhi_GHz']))
    if r['eb'] in BLK:
        O_M.append(opt(BLK[r['eb']]['path_rms_um'], f))
        continue
    b = bmax(r['eb'])
    if not b:
        continue
    if b not in _cache:
        _cache[b] = matched(b)
    v = _cache[b]
    O_U.append((opt(med(v), f), opt(v[int(0.9 * len(v))], f)))
U_MED = med([a for a, _ in O_U])
U_HI = med([b for _, b in O_U])
print('  measured %d windows median %.1f per cent; unmeasured %d windows '
      'matched median %.1f per cent, matched ninetieth %.1f per cent'
      % (len(O_M), 100 * med(O_M), len(O_U), 100 * U_MED, 100 * U_HI))
_um = U_MED if DRIVE != 7 else 0.0
ck('and the matched proxy says their correction is larger than the measured '
   'median, so the limits for them must be stated as conditional',
   _um > med(O_M), 'matched %.3f against measured %.3f' % (_um, med(O_M)))
m('RpDecNUn', '%d' % len(UNM))
m('RpDecBlMeas', '%.0f' % med(BL_M))
m('RpDecBlUn', '%.0f' % med(BL_U))
m('RpDecMatchMed', '%.1f' % (100 * U_MED))
m('RpDecMatchHi', '%.0f' % (100 * U_HI))

# ===================================================================== 4
# MINOR 21.  ADOPTING 1.13 lambda/D.
print('\n4  adopting ALMA\'s beamwidth')
# ★ THE JOIN IS POSITIONAL, AND THAT IS NOT AN ASSUMPTION.  `sens_r11.py`
# writes one row of `pb_atten_fwhm_r11.csv` per catalogue row in catalogue
# order, and (eb, flo, fhi) is NOT a unique key -- four rows of one block
# share it and differ only in their pointing offset, so a dictionary join on
# it silently collapses them and undercounts the low-response windows.  The
# pairing is therefore by position and the applied response is required to
# agree on every row, which is what would detect a reordering.
assert len(PBF) == len(CAT), (len(PBF), len(CAT))
_bad = [i for i, (p, r) in enumerate(zip(PBF, CAT))
        if p['pb_atten'] != r['pb_atten'] or p['eb'] != r['eb']]
ck('the corrected response column pairs row for row with the catalogue, on '
   'the applied response and the block of every row', not _bad,
   '%d rows disagree' % len(_bad))
import adopted_e90 as _ae
E90 = _ae.per_window(CAT, HERE)
ROWS = []
for p, r in zip(PBF, CAT):
    ROWS.append((r, E90[id(r)], E90[id(r)] * float(p['smin_ratio']),
                 float(p['pb_atten_fwhm'])))
A_ROWS = [x for x in ROWS if x[0]['search_class'] == 'A']
W_OLD, W_NEW = med([x[1] for x in A_ROWS]), med([x[2] for x in A_ROWS])
S_OLD, S_NEW = {}, {}
for r, e0, e1, _a in A_ROWS:
    S_OLD[r['system_id']] = min(S_OLD.get(r['system_id'], 1e99), e0)
    S_NEW[r['system_id']] = min(S_NEW.get(r['system_id'], 1e99), e1)
N15_OLD = sum(1 for v in S_OLD.values() if v <= 1e15)
N15_NEW = sum(1 for v in S_NEW.values() if v <= 1e15)
_n15 = N15_NEW if DRIVE != 8 else N15_NEW + 1
ck('adopting the narrower beamwidth changes no published count: the systems '
   'reaching ten to the fifteen watts are the same set',
   _n15 == N15_OLD and set(S_NEW) == set(S_OLD),
   '%d against %d of %d systems' % (_n15, N15_OLD, len(S_OLD)))
A_NEW = sorted(x[3] for x in ROWS)
ck('and no window leaves the sample, because the lowest corrected response '
   'still clears the retention floor', A_NEW[0] > 0.5,
   'minimum %.4f against a floor of 0.50' % A_NEW[0])
print('  median Class A window %+.4f per cent, median system %+.3f per cent, '
      'windows below %.1f: %d'
      % (100 * (W_NEW / W_OLD - 1), 100 * (med(list(S_NEW.values()))
                                           / med(list(S_OLD.values())) - 1),
         PB_LOW, sum(1 for a in A_NEW if a < PB_LOW)))
m('RpPbWinShiftPct', '%.3f' % (100 * (W_NEW / W_OLD - 1)))
m('RpPbSysShiftPct', '%.2f' % (100 * (med(list(S_NEW.values()))
                                      / med(list(S_OLD.values())) - 1)))
A_OLD = sorted(float(r['pb_atten']) for r in CAT)
_nn = (sum(1 for a in A_NEW if a < 0.99), sum(1 for a in A_OLD if a < 0.99))
if DRIVE == 9:
    _nn = (_nn[0] + 1, _nn[1])
ck('the count of windows whose response falls below a hundredth is the same '
   'under either beamwidth, so the published figure holds under both',
   _nn[0] == _nn[1], '%d against %d' % _nn)
m('RpPbNLowAlma', '%d' % sum(1 for a in A_NEW if a < PB_LOW))
m('RpPbAMed', '%.6f' % med(A_NEW))

# ★★★★ AND THE SAME TWO STATISTICS FOR THE RESPONSE THAT WAS ACTUALLY
# APPLIED, because the appendix needs both and had only one.  `pb_atten` --
# the column the published identity S_min = 5 sigma / A closes on, on all
# 1651 rows -- is the 1.22 lambda/D Airy-null Gaussian, NOT ALMA's 1.13
# documented FWHM.  Minor 21 asked us to adopt 1.13 "or justify keeping it";
# the measurement above is the justification, but for one round the APPENDIX
# said 1.13 was the width applied while every limit in the paper stood on
# 1.22, and printed the 1.13 response distribution (median 0.999982, minimum
# 0.5005, below 0.9 on 38) as though it described the applied column (median
# 0.999984, minimum 0.552206, below 0.9 on 34).  Two paragraphs of one
# appendix then described two different beams with nothing saying so, the
# off-axis paragraph's A = 0.552 contradicted the 0.5005 above it, and
# "no window lies near the floor" was printed beside a minimum 0.1 per cent
# above it.
m('RpPbNLowApplied', '%d' % sum(1 for a in A_OLD if a < PB_LOW))
m('RpPbAMedApplied', '%.6f' % med(A_OLD))
m('RpPbAMinApplied', '%.6f' % A_OLD[0])
# ★ the four exceptions are the rows whose products are not retained and
# whose A is back-solved from 5 sigma / S_min against a catalogued sigma that
# is 0.9-1.3 per cent higher than the surviving product's (Appendix A.2 says
# so); the back-solved value therefore sits 2.4e-5 below the model one, which
# is a provenance gap and not a reversal of the inequality.
_RATIO_TOL = 1e-4
_rev = [p for p in PBF if float(p['smin_ratio']) < 1.0 - _RATIO_TOL]
if DRIVE == 12:
    _rev = [PBF[0]]
ck('the applied response is the WIDER of the two, so every limit here is '
   'optimistic by the shift above and never pessimistic',
   A_OLD[0] > A_NEW[0] and med(A_OLD) >= med(A_NEW) and not _rev,
   'applied minimum %.6f against %.6f at ALMA\'s width; %d row(s) reversed '
   'beyond %g, %d within it'
   % (A_OLD[0], A_NEW[0], len(_rev), _RATIO_TOL,
      sum(1 for p in PBF if float(p['smin_ratio']) < 1.0)))

# ★★★★ AND THE CHECK THAT WOULD HAVE CAUGHT THE DEFECT: THE MANUSCRIPT MUST
# NAME THE APPLIED COEFFICIENT AS THE APPLIED ONE.  `sens_r11.py` has
# asserted since round 11 that `pb_atten` reproduces a Gaussian at
# \RingPbCoefCode = 1.22 lambda/D, and it passed every build.  What no gate
# read was the SENTENCE, and the two macros differ by one word in the name.
# So: the clause of Appendix A.2 that says which response was applied must
# cite \RingPbCoefCode, and must not cite \RingPbCoef in the same clause.
_app = os.path.join(HERE, 'sections', 'app_A_reproducibility.tex')
_txt = open(_app, errors='ignore').read() if os.path.exists(_app) else ''
_sent = [s for s in _txt.replace('\n', ' ').split('.') if 'response applied' in s]
if DRIVE == 11:
    _sent = ['The response applied is a Gaussian of \\RingPbCoef\\,\\lambda/D']
ck('the manuscript names the coefficient that was applied, and it is the one '
   'the released response column reproduces',
   len(_sent) == 1 and '\\RingPbCoefCode' in _sent[0]
   and '\\RingPbCoef{' not in _sent[0]
   and '\\RingPbCoef\\' not in _sent[0],
   '%d clause(s); %s' % (len(_sent), (_sent[0][:110] if _sent else '-')))

# ===================================================================== 5
# MINOR 20.  TWO PARALLAX FIGURES, TWO DIFFERENT STATISTICS.
print('\n5  the two parallax figures')
PXL = [1.0 / float(r['eta_px_retained']) - 1.0
       for r in CAT_A if r['eta_px_retained']]
N_NONE = sum(1 for x in PXL if x < 1e-4)
N_BIG = sum(1 for x in PXL if x > 0.10)
W_SHIFT = float(PXA['shift']['window_median_frac'])
L_MED = float(PXA['shift']['loss_median'])
ck('the median window needs no correction while the median limit moves, so '
   'the two figures are different statistics and not a contradiction',
   med(PXL) < 1e-6 < L_MED < W_SHIFT,
   'median Class A loss %.2e, median released loss %.4f, median limit shift '
   '%.4f' % (med(PXL), L_MED, W_SHIFT))
m('RpPxNNone', '%d' % N_NONE)
m('RpPxNBig', '%d' % N_BIG)

# ------------------------------------------------------------------- output
print('\nassertions failed: %d %s' % (len(FAIL), FAIL))
if FAIL and DRIVE is None:
    raise SystemExit('resp_r16: %d assertion(s) failed: %s' % (len(FAIL), FAIL))

with open(OUT, 'w') as fh:
    fh.write('%% GENERATED by %s -- do not hand-edit.\n'
             % os.path.basename(__file__))
    # ★ r16-integrate: declare the supersession here, in the round file of the
    # generator that publishes the REPLACEMENT, which is what `retired.py`
    # reads.  `\InjPeakAtNinety` (round 65) was `retired completeness x
    # deposited phase mean` = 1.93 and Table 4 printed it as the channel
    # response of the ADOPTED factor, where the quantity is \RpMarginNinety =
    # 1.33.  `strata_v411.py` no longer emits it; this line is what stops the
    # NAME coming back into the manuscript, and `retired.py` fails if the
    # replacement is not defined, so the declaration cannot go stale.
    fh.write('%% SUPERSEDES: InjPeakAtNinety=RpMarginNinety\n')
    fh.write('\n'.join(sorted(MACROS)) + '\n')
json.dump(dict(generated_by=os.path.basename(__file__), round=ROUND,
               drive=DRIVE,
               response=dict(p90=P90, deposited_phase_mean=DEP,
                             response_factor=RESP_FAC, margin=MARGIN,
                             envelope=[ENV_LO, ENV_HI]),
               representativeness=dict(axes=COV, split=SPLIT,
                                       worst=WORST, n_cover=N_COVER),
               decorrelation=dict(n_measured=len(MEAS), n_unmeasured=len(UNM),
                                  bl_med_measured=med(BL_M),
                                  bl_med_unmeasured=med(BL_U),
                                  opt_med_measured=med(O_M),
                                  opt_med_matched=U_MED,
                                  opt_hi_matched=U_HI),
               beamwidth=dict(win_shift=W_NEW / W_OLD - 1,
                              sys_shift=med(list(S_NEW.values()))
                              / med(list(S_OLD.values())) - 1,
                              n_sys_1e15=[N15_OLD, N15_NEW],
                              a_min=A_NEW[0]),
               parallax=dict(n_none=N_NONE, n_big=N_BIG,
                             median_loss_classA=med(PXL),
                             median_loss_released=L_MED,
                             median_limit_shift=W_SHIFT),
               failures=FAIL),
          open(OUT_JSON, 'w'), indent=1, sort_keys=True)
print('\n%d macros -> %s' % (len(MACROS), os.path.basename(OUT)))
