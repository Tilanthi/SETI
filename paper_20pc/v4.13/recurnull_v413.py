#!/usr/bin/env python3
r"""recurnull_v413.py -- the null of the recurrence statistic, the widened
recurrence window, and the exclusion significance defined by one formula.

Round 220.  Writes `survey_numbers_round220.tex` and `recurnull_v413.json`.

WHY THIS EXISTS.  Three statements about the recurrence test were made without
being measured, and each of them is load-bearing.

 1. THE NULL.  The statistic read at the predicted stellar-frame cell was
    treated as zero-mean and unit-variance because it was built that way.  It
    is measured here four separate ways -- at the predicted cell over every
    repeat-block reading in the survey and in the reserved hold-out, at the
    control positions of the same blocks, at the neighbouring channels of the
    repeat blocks whose dynamic spectra are retained, and at the control
    positions across the discovery band -- and the four agree.  The reason
    this had to be done is that the column the ledger printed under the name
    of that statistic looked systematically positive: its mean over the rows
    carrying exclusions is +1.13 where a zero-mean statistic should scatter by
    0.18.  The explanation is not a mis-calibrated null and not weak emission.
    THE COLUMN WAS A MAXIMUM OVER THE REPEAT BLOCKS, and the mean of a maximum
    over n draws is not zero: the measured null predicts +1.15 for the same
    set of n.  The inverse-variance combination -- which is the quantity the
    exclusion was always built from -- has mean -0.13.  So the fix is to print
    the quantity the exclusion uses, and the offset disappears.

 2. THE FORMULA.  The exclusion was (S - abar)/sigmabar: the discovery
    amplitude treated as known exactly.  That cannot exceed the strength of
    the discovery itself, and printed as though it could -- one row reached
    70.7 against its own T_pers of 69.7, and the appendix's worked example
    quoted 4.6 for a crossing the tables gave as 7.1.  Both are the same
    arithmetic with and without the discovery's own noise.  The exclusion is
    defined here ONCE, as the significance at which the two readings of one
    amplitude disagree,

        sigma_excl = (S - abar) / sqrt(sigma_d^2 + sigmabar^2)
                   = (T_pers - T_rep) / sqrt(1 + (T_pers/T_star)^2),

    which is reproducible from three columns the ledger already prints.  It is
    smaller than the conditional reading, and it is the honest one: a carrier
    whose discovery amplitude is a five-sigma measurement cannot be excluded at
    two hundred sigma.  The strength the deep repeat coverage really buys is
    then stated as a limit rather than as a significance -- the fraction of
    the discovery amplitude that is excluded at five sigma,

        f_5 = (T_rep + 5) / T_pers,

    which is also reproducible from the printed columns, and which disposes of
    the selection bias in the discovery amplitude: a maximum over 10^2-10^6
    cells at T ~ 5 is biased high, the true amplitude is therefore lower than
    measured, and f < 1 is exactly that case.

 3. THE WINDOW.  Reading one cell tests a transmitter whose stellar-frame
    frequency and drift are the same at both epochs.  A transmitter on an
    orbiting body need not be: at the measured drifts the implied orbital
    speed is of order 10^2 km/s, so at another epoch the carrier could sit
    anywhere within that of the predicted cell.  The search is therefore
    widened here, and the widening costs no new data because the survey
    already did it: every covering window was searched at every channel and
    every drift in its grid, and the catalogue carries each window's maximum.
    The window spans +-833 km/s about the predicted cell, which exceeds the
    implied orbital amplitude for every crossing, and 292 of the 320 covering
    windows hold nothing above the trigger anywhere in them.  The 28 that do
    are consistent with the 27.4 chance predicts, every one is a crossing the
    ledger already lists, and the nearest to a predicted cell is 56 km/s away.
    This also settles the one crossing called untestable: its discovery
    amplitude is gone, so no exclusion can be formed, but the criterion
    itself -- the trigger at the predicted cell -- is testable from the
    covering windows' own maxima, and it is not met.  36 of 36 are tested and
    35 carry exclusions.

JOINS.  The covering windows are keyed on the catalogue's `system_id`, never
on a star name: seven systems in the catalogue carry two spellings of their
own star among their windows.  The key is validated against the independent,
position-keyed repeat list of the recurrence measurement -- every one of its
294 in-catalogue repeat blocks must appear in the system-keyed covering set,
and the assertion is driven.

Usage: recurnull_v413.py [--drive N]
"""
import csv
import json
import math
import os
import sys

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
ROUND = 220
DRIVE = int(sys.argv[sys.argv.index('--drive') + 1]) if '--drive' in sys.argv \
    else 0
SFX = '' if DRIVE == 0 else '_drive%d' % DRIVE
OUT = os.path.join(HERE, 'survey_numbers_round220%s.tex' % SFX)
OUTJ = os.path.join(HERE, 'recurnull_v413%s.json' % SFX)

TRIG = 5.0
CKMS = 299792.458
GMSUN = 1.32712440018e20          # m^3 s^-2
MSUN_MAX = 2.0                    # the bound used for the implied orbit
DAY_H = 24.0

M = []
FAIL = []


def m(k, v):
    M.append((k, v))
    assert k.isalpha(), 'a LaTeX macro name may contain letters only: ' + k


def ck(name, cond, detail=''):
    if not cond:
        FAIL.append(name)
    print('  %-62s %s  %s' % (name, 'PASS' if cond else 'FAIL', detail))


def macro(name):
    """One macro's value out of the frozen layer, by name."""
    import glob
    import re as _re
    pat = _re.compile(r'\\(?:new|renew|provide)command\{\\%s\}'
                      r'\{((?:[^{}]|\{[^{}]*\})*?)\}' % name)
    v = None
    for fn in sorted(glob.glob(os.path.join(HERE, 'survey_numbers*.tex'))):
        if '_drive' in fn:
            continue
        for mm in pat.finditer(open(fn, encoding='utf-8').read()):
            if mm.group(1).strip():
                v = mm.group(1).strip()
    if v is None:
        raise SystemExit('macro %s not found' % name)
    return v


def gauss_sf(x):
    """One-sided Gaussian tail probability, from the error function."""
    return 0.5 * math.erfc(x / math.sqrt(2.0))


def emax(n, lo=-9.0, hi=11.0, steps=400000):
    """Mean and standard deviation of the maximum of `n` independent standard
    normal variables, by quadrature on its own distribution rather than by
    simulation: F(x)^n is the cdf, so the density is n f(x) F(x)^(n-1).  A
    closed quantity, so the drive below cannot be answered by a seed."""
    trap = getattr(np, 'trapezoid', None) or np.trapz
    x = np.linspace(lo, hi, steps)
    F = 0.5 * (1.0 + np.vectorize(math.erf)(x / math.sqrt(2.0)))
    f = np.exp(-0.5 * x * x) / math.sqrt(2.0 * math.pi)
    d = n * f * F ** (n - 1)
    w = trap(d, x)
    mu = trap(d * x, x) / w
    var = trap(d * (x - mu) ** 2, x) / w
    return mu, math.sqrt(var)


# ------------------------------------------------------------------ inputs
R = json.load(open(os.path.join(HERE, 'r10inputs', 'recur_v411.json')))
HO = json.load(open(os.path.join(HERE, 'r11inputs', 'events',
                                 'recur_holdout.json')))
LED = json.load(open(os.path.join(HERE, 'ledger.json')))
CAT = list(csv.DictReader(open(os.path.join(
    HERE, 'per_target_results_v3.99.csv'))))
FMETA = json.load(open(os.path.join(HERE, 'r11inputs', 'events',
                                    'figdata_meta.json')))

BYEB, BYSYS, BYNAME = {}, {}, {}
for _r in CAT:
    BYEB.setdefault(_r['eb'], []).append(_r)
    BYSYS.setdefault(_r['system_id'], []).append(_r)
    BYNAME.setdefault(_r['star_name'], []).append(_r)

CROSS = R['crossings']
NCTRL_RET = 8                     # control positions with retained spectra


def blocks(c):
    """The covering repeat blocks of one crossing, with the paper's own
    weight-pathology list applied."""
    return [b for b in c.get('blocks', []) if not b.get('bad_weight_product')]


# =====================================================================
# 1.  THE NULL OF THE STATISTIC AT THE PREDICTED CELL
# =====================================================================
# One reading, one cell, one drift: the quantity the test is built on.  Every
# repeat-block reading in the census and in the reserved hold-out.
STARV, CTRLV = [], []
for src in (CROSS, HO['crossings']):
    for cid, c in src.items():
        if c['status'] != 'ok':
            continue
        for b in blocks(c):
            STARV.append(b['T_matched'])
            CTRLV.append(b['ctrl_T_matched_max'])
STARV = np.array(STARV, dtype=float)
CTRLV = np.array(CTRLV, dtype=float)
if DRIVE == 1:                    # a null that is not centred on zero
    STARV = STARV + 0.5
if DRIVE == 10:                   # a null whose width is not one
    STARV = STARV * 1.3

nn = len(STARV)
nmean, nsd = float(STARV.mean()), float(STARV.std(ddof=1))
nsem = nsd / math.sqrt(nn)
m('NuNullN', '%d' % nn)
m('NuNullMean', '%+.3f' % nmean)
m('NuNullSem', '%.3f' % nsem)
m('NuNullSd', '%.3f' % nsd)
m('NuNullPos', '%d' % int((STARV > 0).sum()))
ck('N1 the statistic at the predicted cell is centred on zero',
   abs(nmean) < 4.0 * nsem,
   'mean %+.3f +- %.3f over %d readings' % (nmean, nsem, nn))
ck('N2 and has unit variance', abs(nsd - 1.0) < 0.05,
   'sd %.3f' % nsd)

# The same reading at the control positions of the same blocks.  What is
# recorded per block is the LARGEST of the eight retained controls, so it is
# compared with the expectation for a maximum of eight and not with zero: the
# comparison that would be wrong here is the easy one.
NC = 1 if DRIVE == 2 else NCTRL_RET
cpred, cpredsd = emax(NC)
cmean, csd = float(CTRLV.mean()), float(CTRLV.std(ddof=1))
csem = csd / math.sqrt(len(CTRLV))
m('NuCtrlN', '%d' % len(CTRLV))
m('NuCtrlRet', '%d' % NCTRL_RET)
m('NuCtrlMean', '%.3f' % cmean)
m('NuCtrlSem', '%.3f' % csem)
m('NuCtrlSd', '%.3f' % csd)
m('NuCtrlPred', '%.3f' % cpred)
ck('N3 the control positions agree with the expected maximum of eight',
   abs(cmean - cpred) < 4.0 * csem,
   'measured %.3f +- %.3f against %.3f' % (cmean, csem, cpred))

# The same procedure at the NEIGHBOURING channels of the repeat blocks, for
# the two crossings whose repeat dynamic spectra are retained: random cells,
# same registration, same drift.
BAND, DISC = [], []
bandcells, bandhalf, bandmax, bandkms = 0, [], -9.9, []
for cid in sorted(FMETA):
    z = np.load(os.path.join(HERE, 'r11inputs', 'events',
                             'figdata_%s.npz' % cid))
    rT = z['r_T']
    half = int(z['half'])
    chanw = float(z['chanw'])
    f0 = float(FMETA[cid]['freq_GHz']) * 1e9
    off = np.delete(rT, half, axis=1)
    BAND.extend(off[np.isfinite(off)].tolist())
    good = rT[np.isfinite(rT)]
    bandcells += int(good.size)
    bandmax = max(bandmax, float(good.max()) + (3.0 if DRIVE == 15 else 0.0))
    bandhalf.append(half)
    bandkms.append(CKMS * half * chanw / f0)
    Tc = z['T_ctrl']
    DISC.extend(Tc[np.isfinite(Tc)].tolist())
BAND = np.array(BAND)
DISC = np.array(DISC)
if DRIVE == 11:                   # neighbouring cells that are not the null
    BAND = BAND * 1.5 + 0.4
    DISC = DISC + 0.4
m('NuBandN', '%d' % len(BAND))
m('NuBandMean', '%+.3f' % BAND.mean())
m('NuBandSd', '%.3f' % BAND.std(ddof=1))
m('NuDiscCtrlN', '%d' % len(DISC))
m('NuDiscCtrlMean', '%+.3f' % DISC.mean())
m('NuDiscCtrlSd', '%.3f' % DISC.std(ddof=1))
ck('N4 the neighbouring channels of the repeat blocks give the same null',
   abs(BAND.mean()) < 4.0 * BAND.std(ddof=1) / math.sqrt(len(BAND))
   and abs(BAND.std(ddof=1) - 1.0) < 0.12,
   'mean %+.3f sd %.3f over %d cells' % (BAND.mean(), BAND.std(ddof=1),
                                         len(BAND)))
ck('N5 and so do the control positions across the discovery band',
   abs(DISC.mean()) < 0.1 and abs(DISC.std(ddof=1) - 1.0) < 0.12,
   'mean %+.3f sd %.3f over %d cells' % (DISC.mean(), DISC.std(ddof=1),
                                         len(DISC)))

# =====================================================================
# 2.  THE ROWS CARRYING EXCLUSIONS, AND THE FORMULA
# =====================================================================
LK = {(r['eb'], round(float(r['freq']), 4)): r for r in LED['rows']}
UNATTR = [r for r in LED['rows'] if not r['attributed']]
CRK = {(c['eb'], round(float(c['freq_GHz']), 4)): c for c in CROSS.values()}

ROWS = []
for cid, c in CROSS.items():
    if c['status'] != 'ok':
        continue
    bl = blocks(c)
    if not bl:
        continue
    L = LK.get((c['eb'], round(float(c['freq_GHz']), 4)))
    if L is None:
        continue
    S = c['discovery']['amp_mJy']
    sd = c['discovery']['sig_mJy']
    tstar = c['discovery']['T_matched']
    w = [1.0 / b['sig_mJy'] ** 2 for b in bl]
    sbar = 1.0 / math.sqrt(sum(w))
    abar = sum(b['amp_mJy'] * q for b, q in zip(bl, w)) / sum(w)
    tp, tr = S / sbar, abar / sbar
    ROWS.append(dict(
        cid=cid, star=c['star'], eb=c['eb'], freq=float(c['freq_GHz']),
        attributed=bool(L['attributed']),
        dq=bool(L.get('dq')), n=len(bl), tstar=tstar, tpers=tp, trep=tr,
        trep_max=max(b['T_matched'] for b in bl),
        excl_cond=(S - abar) / sbar,
        excl=(S - abar) / math.sqrt(sd * sd + sbar * sbar),
        neff=(sd / sbar) ** 2,
        f5=(tr + TRIG) / tp,
        sep_min_h=min(abs(b['sep_from_discovery_h']) for b in bl),
        sep_max_h=max(abs(b['sep_from_discovery_h']) for b in bl),
        drift=c['discovery']['drift_Hz_s']))

# ★ The exclusion population is the UNATTRIBUTED crossings whose repeat
# coverage carries an amplitude.  The recurrence arithmetic is formed for
# every crossing with repeat coverage, attributed or not, because the mask
# only flags: a crossing the species list attributes still has a measured
# recurrence record, and Appendix B's worked example is one of them.  So the
# filter is applied HERE, to the published statistics, and not when the rows
# are built -- which is what used to make the worked example disappear the
# moment its own crossing changed side of the mask.
ALLROWS = ROWS
Q = [r for r in ROWS if not r['dq'] and not r['attributed']]
m('NuColN', '%d' % len(Q))
colmean = float(np.mean([r['trep_max'] for r in Q]))
m('NuColMean', '%+.3f' % colmean)
m('NuColPos', '%d' % sum(1 for r in Q if r['trep_max'] > 0))
# What a maximum over the same numbers of repeat blocks should give, under the
# null measured above.  Each row's own n, not an average n.
ns = [1 if DRIVE == 3 else r['n'] for r in Q]
pred = [emax(n) for n in ns]
predmean = float(np.mean([p[0] for p in pred]))
predsem = float(math.sqrt(sum(p[1] ** 2 for p in pred)) / len(pred))
m('NuColPred', '%+.3f' % predmean)
m('NuColPredSem', '%.3f' % predsem)
m('NuColNrepMax', '%d' % max(r['n'] for r in Q))
ck('N6 the printed column is a maximum, and the measured null predicts it',
   abs(colmean - predmean) < 3.0 * predsem,
   'column %+.3f against %+.3f +- %.3f predicted'
   % (colmean, predmean, predsem))
# ... whereas the quantity the exclusion is built from is centred on zero.
tr = np.array([r['trep'] for r in Q])
if DRIVE == 12:                   # the combined reading offset from zero
    tr = tr + 1.0
m('NuRepMean', '%+.3f' % tr.mean())
m('NuRepSem', '%.3f' % (tr.std(ddof=1) / math.sqrt(len(tr))))
m('NuRepSd', '%.3f' % tr.std(ddof=1))
m('NuRepPos', '%d' % int((tr > 0).sum()))
ck('N7 the combined reading, which the exclusion uses, is centred on zero',
   abs(tr.mean()) < 3.0 * tr.std(ddof=1) / math.sqrt(len(tr)),
   'mean %+.3f +- %.3f' % (tr.mean(), tr.std(ddof=1) / math.sqrt(len(tr))))

# ---- the formula, and its reproducibility from the printed columns
rep = []
for r in Q:
    ts = r['tstar'] * (1.01 if DRIVE == 4 else 1.0)
    frm = (r['tpers'] - r['trep']) / math.sqrt(1.0 + (r['tpers'] / ts) ** 2)
    rep.append(abs(frm - r['excl']))
m('XcReproMax', '%.4f' % max(rep))
ck('X1 the exclusion is reproducible from T_star, T_pers and T_rep alone',
   max(rep) < 5e-3, 'largest departure %.2e over %d rows' % (max(rep), len(Q)))

ex = sorted(r['excl'] for r in (Q if DRIVE != 5 else []))
if DRIVE == 5:
    ex = sorted(r['excl_cond'] for r in Q)
ck('X2 no exclusion exceeds the strength of its own discovery',
   all(e <= max(r['tstar'] for r in Q) + 0.05 for e in ex),
   'largest exclusion %.1f against the largest T_star %.2f'
   % (ex[-1], max(r['tstar'] for r in Q)))

f5 = sorted((r['f5'] * (1.6 if DRIVE == 16 else 1.0)) for r in Q)
ck('X3 every crossing is excluded at the discovery amplitude, and most of '
   'them well below it',
   f5[-1] <= 1.0 and sum(1 for f in f5 if f <= 0.5) > len(f5) // 2,
   'f_5 median %.2f, worst %.2f, %d of %d at or below one half'
   % (f5[len(f5) // 2], f5[-1], sum(1 for f in f5 if f <= 0.5), len(f5)))

# ---- the worked example, reconciled.  One repeat block and five.
CPK = ('A002_Xff0235_X4a6d', 344.2697)
CPR = [r for r in ALLROWS if (r['eb'], round(r['freq'], 4)) == CPK]
assert len(CPR) == 1, (
    'the worked example must be exactly one row, found %d' % len(CPR))
cp = CPR[0]
cpc = CRK[CPK]
cpbl = blocks(cpc)
cpdeep = (max if DRIVE == 17 else min)(cpbl, key=lambda b: b['sig_mJy'])
Sd, sdd = cpc['discovery']['amp_mJy'], cpc['discovery']['sig_mJy']
m('XcCpNRep', '%d' % cp['n'])
m('XcCpTPersOne', '%.2f' % (Sd / cpdeep['sig_mJy']))
m('XcCpTPersAll', '%.2f' % cp['tpers'])
m('XcCpExclOne', '%.1f' % ((Sd - cpdeep['amp_mJy'])
                           / math.sqrt(sdd ** 2 + cpdeep['sig_mJy'] ** 2)))
m('XcCpExcl', '%.1f' % cp['excl'])
m('XcCpFrac', '%.2f' % cp['f5'])
m('XcCpSepH', '%.2f' % abs(cpdeep['sep_from_discovery_h']))
ck('X4 the worked example and the ledger quote one quantity, computed two '
   'ways over one and over all its repeat blocks',
   abs(Sd / cpdeep['sig_mJy'] - cp['tpers']) < 0.2,
   'one block %.2f, %d blocks %.2f'
   % (Sd / cpdeep['sig_mJy'], cp['n'], cp['tpers']))

# =====================================================================
# 3.  THE WIDENED WINDOW
# =====================================================================
# Every window, of any block of the same system, that covers the crossing's
# frequency.  The survey searched each of them at every channel and every
# drift in its grid, and the catalogue carries the maximum, so widening the
# recurrence search costs nothing but the reading.
multi = sum(1 for v in BYSYS.values()
            if len({q['star_name'] for q in v}) > 1)
if DRIVE == 13:                   # a key chosen for no demonstrated reason
    multi = 0
m('WdNAlias', '%d' % multi)
ck('W0 the covering sets are keyed on an identifier, and the hazard that '
   'makes that necessary is present in the catalogue',
   multi > 0, '%d systems carry two spellings of their own star' % multi)

COVSET, nocell = {}, 0
for r in UNATTR:
    f, eb = float(r['freq']), r['eb']
    dw = [q for q in BYEB.get(eb, [])
          if float(q['flo_GHz']) <= f <= float(q['fhi_GHz'])]
    sid = dw[0]['system_id'] if len(dw) == 1 else None
    if sid is None:
        c = CRK.get((eb, round(f, 4)))
        for b in blocks(c or {}) if c else []:
            q = [x for x in BYEB.get(b['eb'], [])
                 if float(x['flo_GHz']) <= b['f_here_GHz']
                 <= float(x['fhi_GHz'])]
            if q:
                sid = q[0]['system_id']
                break
    assert sid, 'no system identifier for %s %s' % (r['star'], eb)
    cov = [q for q in BYSYS[sid] if q['eb'] != eb
           and float(q['flo_GHz']) <= f <= float(q['fhi_GHz'])]
    if DRIVE == 7 and cov:
        cov = cov[:-1]
    COVSET[(eb, round(f, 4))] = (sid, cov)

# the join gate: the position-keyed repeat list of the measurement must be
# contained in the identifier-keyed covering set, block for block.
nmeas, nlost = 0, 0
for k, c in CRK.items():
    if k not in COVSET:
        continue
    cebs = {q['eb'] for q in COVSET[k][1]}
    meas = {b['eb'] for b in blocks(c) if b.get('in_released_catalogue')}
    nmeas += len(meas)
    nlost += len(meas - cebs)
m('WdNJoin', '%d' % nmeas)
ck('W1 every position-keyed repeat block appears in the identifier-keyed '
   'covering set', nlost == 0,
   '%d of %d blocks' % (nmeas - nlost, nmeas))

HALF = {}            # the covering windows' half-widths, per crossing
ncov = nempty = nexc = 0
expect = 0.0
half_kms, amax, excoff, excmax = [], [], [], -9.9
for k, (sid, cov) in COVSET.items():
    f = k[1]
    for q in cov:
        ncov += 1
        lo, hi = float(q['flo_GHz']), float(q['fhi_GHz'])
        half_kms.append(0.5 * CKMS * (hi - lo) / f)
        HALF.setdefault(k, []).append(0.5 * CKMS * (hi - lo) / f)
        if q['a_max_m_s2']:
            amax.append(float(q['a_max_m_s2']))
        if q['n_ind_cells']:
            N = float(q['n_ind_cells'])
            sw = 0.5 * (float(q['scale_route_a'])
                        + float(q['scale_route_b']))
            expect += -math.expm1(N * math.log(1.0 - gauss_sf(TRIG / sw)))
        else:
            nocell += 1
        if float(q['star_snr']) >= TRIG:
            nexc += 1
            excmax = max(excmax, float(q['star_snr']))
            if q['f_cross_GHz']:
                excoff.append(abs(CKMS * (float(q['f_cross_GHz']) - f) / f))
        else:
            nempty += 1
if DRIVE == 6:
    expect *= 0.5

m('WdNCross', '%d' % len(COVSET))
m('WdNCov', '%d' % ncov)
m('WdNEmpty', '%d' % nempty)
m('WdNExc', '%d' % nexc)
m('WdExpect', '%.0f' % expect)
m('WdNoCell', '%d' % nocell)
m('WdHalfKms', '%.0f' % np.median(half_kms))
m('WdAmax', '%.1f' % np.median(amax))
m('WdExcMax', '%.2f' % excmax)
m('WdNearKms', '%.0f' % min(excoff))
m('WdMedKms', '%.0f' % np.median(excoff))
if DRIVE == 14:                   # a window counted in neither column
    nempty -= 1
ck('W2 the covering windows split into those holding nothing above the '
   'trigger and those holding something, with no remainder',
   nempty + nexc == ncov, '%d + %d = %d' % (nempty, nexc, ncov))
ck('W3 what the widened window holds is what chance predicts',
   abs(nexc - expect) < 3.0 * math.sqrt(expect),
   '%d found against %.1f expected' % (nexc, expect))

# ---- the model the predicted cell assumes, and the window the orbit implies
# a_los = c nudot/nu; a body held at that acceleration by a star of mass Mstar
# orbits at r = sqrt(GM/a) with speed (GM a)^(1/4), so its radial velocity can
# differ between epochs by up to that speed.  The fourth root makes the bound
# insensitive to the mass, and MSUN_MAX is an upper bound for this sample.
amax_los, vorb, porb = 0.0, 0.0, 0.0
nspan, nshort, shortname = 0, [], ''
for r in Q:
    k = (r['eb'], round(r['freq'], 4))
    a = abs(CKMS * 1e3 * r['drift'] / (r['freq'] * 1e9))
    v = (GMSUN * MSUN_MAX * a) ** 0.25
    if DRIVE == 8:
        v *= 10.0
    if v > vorb:
        amax_los, vorb = a, v
        porb = 2.0 * math.pi * math.sqrt(GMSUN * MSUN_MAX / a) / v / 86400.0
    if max(HALF.get(k, [0.0])) >= v / 1e3:
        nspan += 1
    else:
        nshort.append((r['star'], max(HALF.get(k, [0.0])), v / 1e3))
if nshort:
    shortname = sorted(set(s[0] for s in nshort))[0]
m('WdAlosMax', '%.1f' % amax_los)
m('WdOrbKms', '%.0f' % (vorb / 1e3))
m('WdOrbDay', '%.0f' % porb)
m('WdMassMax', '%.0f' % MSUN_MAX)
m('WdNOrbSpan', '%d' % nspan)
m('WdNOrbShort', '%d' % len(nshort))
m('WdOrbShortStar', (shortname or '--').replace(' ', '~'))
m('WdOrbShortKms', '%.0f' % (min(s[1] for s in nshort) if nshort else 0.0))
m('WdOrbShortOrb', '%.0f' % (max(s[2] for s in nshort) if nshort else 0.0))
ck('W4 the searched window spans the whole velocity change an orbit of the '
   'measured acceleration can produce, for all but a named few',
   nspan >= len(Q) - 2 and (not nshort or shortname),
   '%d of %d crossings; the exception is %s, +-%.0f km/s against +-%.0f'
   % (nspan, len(Q), shortname or 'none',
      min((s[1] for s in nshort), default=0.0),
      max((s[2] for s in nshort), default=0.0)))


# the measured widening, at the matched drift, where the repeat spectra survive
m('WdBandN', '%d' % bandcells)
m('WdBandKms', '%.0f' % min(bandkms))
m('WdBandMax', '%.2f' % bandmax)
m('WdBandNCross', '%d' % len(FMETA))
ck('W5 the widened reading at the matched drift is empty where the repeat '
   'dynamic spectra survive', bandmax < TRIG,
   'largest %.2f over %d cells' % (bandmax, bandcells))

# =====================================================================
# 4.  THE COUNTS, AND WHAT "INDEPENDENT" MEANS
# =====================================================================
UNT = [c for c in CROSS.values()
       if (c['status'] != 'ok' or not blocks(c))
       and (c['eb'], round(float(c['freq_GHz']), 4)) in LK
       and not LK[(c['eb'], round(float(c['freq_GHz']), 4))]['attributed']]
n_excl = len(Q)
#: tested, with repeat coverage, but the exclusion WITHHELD because the
#: discovery block fails the data-quality criterion.  These rows are tested
#: and reported; what they do not carry is a significance.
n_wh = sum(1 for r in ALLROWS if r['dq'] and not r['attributed'])
n_crit = len(UNT)
if DRIVE == 9:
    n_crit = 0
#: ★ The partition must be stated in full or it is not a partition.  Every
#: unattributed crossing is TESTED; of those, one has no retained discovery
#: spectrum and is tested against the criterion alone, four have their
#: exclusion withheld with the block that fails the quality criterion, and
#: the rest carry a quoted exclusion.  The three-way split used to be
#: written as a two-way one, which is how the paper came to say "every
#: tested crossing excludes a carrier at at least 5.0 sigma" over a
#: population that included four rows whose exclusions the table withholds.
ck('C1 the unattributed crossings partition into the ones carrying a '
   'quoted exclusion, the ones whose exclusion is withheld with the '
   'failing block, and the one tested against the criterion alone',
   n_excl + n_wh + n_crit == len(UNATTR) and n_wh > 0 and n_crit > 0,
   '%d quoted + %d withheld + %d against the criterion = %d unattributed'
   % (n_excl, n_wh, n_crit, len(UNATTR)))
m('CtNTested', '%d' % len(UNATTR))
m('CtNExclPoss', '%d' % (n_excl + n_wh))
m('CtNWithheld', '%d' % n_wh)
m('CtNQuoted', '%d' % n_excl)

# the crossing with no retained discovery amplitude is nevertheless testable
# against the criterion, out of the covering windows' own maxima.
if UNT:
    u = UNT[0]
    k = (u['eb'], round(float(u['freq_GHz']), 4))
    cov = COVSET[k][1]
    if DRIVE == 18:               # a criterion that could not be applied
        cov = [q for q in cov if float(q['star_snr']) >= TRIG]
    m('CtCritStar', u['display'].replace('~', '\\,'))
    m('CtCritFreq', '%.4f' % u['freq_GHz'])
    m('CtCritNCov', '%d' % len(cov))
    m('CtCritNEmpty', '%d' % sum(1 for q in cov
                                 if float(q['star_snr']) < TRIG))
    m('CtCritMax', '%.2f' % max(float(q['star_snr']) for q in cov))
    _ce = [q for q in cov if float(q['star_snr']) >= TRIG]
    m('CtCritNExc', '%d' % len(_ce))
    m('CtCritNearKms', '%.0f' % (min(
        abs(CKMS * (float(q['f_cross_GHz']) - u['freq_GHz']) / u['freq_GHz'])
        for q in _ce if q['f_cross_GHz']) if _ce else 0.0))
    ck('C2 and the one crossing with no retained discovery amplitude is '
       'still testable against the criterion',
       sum(1 for q in cov if float(q['star_snr']) >= TRIG) < len(cov),
       '%d of %d covering windows hold nothing above the trigger'
       % (sum(1 for q in cov if float(q['star_snr']) < TRIG), len(cov)))

# independence: an execution block is not a day.  Both counts, named apart.
nday = sum(1 for r in Q if r['sep_max_h'] > DAY_H)
nhour = sum(1 for r in Q if r['sep_max_h'] <= DAY_H)
if DRIVE == 19:                   # the two senses of independence conflated
    nhour = 0
m('CtNDay', '%d' % nday)
m('CtNHourOnly', '%d' % nhour)
ck('C3 the two senses of an independent epoch are counted apart',
   nday + nhour == n_excl,
   '%d tested over more than a day, %d only within one' % (nday, nhour))

# =====================================================================
if DRIVE:
    print('\n  drive %d: %d assertion(s) fired  %s'
          % (DRIVE, len(FAIL), ','.join(FAIL)))
    if not FAIL:
        print('  DRIVE DID NOT FIRE')
        sys.exit(2)
elif FAIL:
    print('\n  FAILURES: %s' % ','.join(FAIL))
    sys.exit(1)

seen = {}
for k, v in M:
    assert k not in seen, 'duplicate macro ' + k
    seen[k] = v
with open(OUT, 'w') as fh:
    fh.write('%% GENERATED by recurnull_v413.py -- do not hand-edit.\n')
    fh.write('%%%% Round %d: the null of the recurrence statistic, the '
             'widened recurrence window,\n' % ROUND)
    fh.write('%% and the exclusion significance defined by one formula.\n')
    for k, v in M:
        fh.write('\\newcommand{\\%s}{%s}\n' % (k, v))
json.dump(dict(macros=seen, rows=Q, drive=DRIVE), open(OUTJ, 'w'), indent=1)
print('\nwrote %s (%d macros) and %s'
      % (os.path.basename(OUT), len(M), os.path.basename(OUTJ)))
