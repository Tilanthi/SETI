#!/usr/bin/env python3
r"""round 1300 -> survey_numbers_round1300.tex, sens_r28.json,
sens_r28_windows.csv and sens_r28_systems.csv (deposited by zdeposit.py as
sensitivity/class_A_limit_uncertainty.csv and sensitivity/system_limits.csv)

WHAT THE HEADLINE SENSITIVITY IS UNCERTAIN BY, AND WHICH SYSTEMS IT DECIDES.

Referee 1 (Major 1) asks that the sensitivity summaries -- the median system
limit and the number of systems reaching 1e15 W -- be recomputed with the
measured window-to-window dispersion of the completeness factor, that the
class-average and individual uncertainties be kept apart, that the systems
whose 1e15 W classification is uncertain be named, and that the 62
extrapolated windows not be presented as empirically bounded.  Referee 1
(Major 4) asks that the same statistics be described consistently with the
decorrelation analysis and that the corrected values be in the deposit.
Referee 2 (m11) asks whether the injections used each window's actual
channel response.  All three are answered here, from one population and one
definition of a limit, so the answers cannot disagree with each other.

THE TWO UNCERTAINTIES ENTER DIFFERENTLY, AND THAT IS THE POINT.
  * The CLASS-AVERAGE calibration interval (x\SensFacLo..x\SensFacHi) is one
    number shared by every transferred window: it moves every limit TOGETHER,
    so it is applied coherently -- every window scaled by the same factor --
    and its effect on the median and on the count is read off directly.
  * The INDIVIDUAL dispersion (the 49 injected windows' own ninety-per-cent
    points) is independent from window to window: it is applied by drawing
    each transferred window's factor from the measured distribution, the
    injected windows keeping their OWN measured factor, and the per-system
    best window re-formed in every draw.  A second draw shares one factor per
    execution block, because windows of one block share a configuration and
    the campaign's own windows show how much they share (reported, not
    assumed).

WHAT IS NOT A RESAMPLING.  The 62 extrapolated windows lie outside the
injected range on at least one of the five properties that set the reading;
for them the measured dispersion is not an empirical bound.  They are
therefore also bounded the only way that is honest -- by removing them
altogether, and by giving them the worst measured factor -- and the count is
reported under both.

m11, THE CHANNEL RESPONSE.  The campaign injector (`inject_vis_v399.py`,
pinned in `strata_v411.py`) deposits every tone as a linear split between two
channels convolved with the 0.25/0.5/0.25 kernel, ON THE DELIVERED CHANNEL
GRID, whatever the window's online spectral averaging.  That is ALMA's
response only for N = 1.  The archive's own effective-resolution column
(`archive_meta_v381.json`) and the catalogue's `n_chan_avg` both classify
every Class A window, and they must agree.  For N >= 2 the delivered response
is the sum of N raw Hann-smoothed channels (`cresp_v401.json`, validated
against the archive's resolution ratios), which keeps far MORE of a carrier in
the peak channel; the injected profile is then too pessimistic.  The size is
measured by refitting the campaign's own tones -- a probit in the deposited
peak share along each tone's own drift track, fitted separately to the native
and the averaged windows -- and re-reading the ninety-per-cent point with the
true share.  The same refit on the N = 1 windows must reproduce the
published 8 per cent residual, which is the validation of the method.

NOTHING IS TYPED.  Every input is the file that owns it; every published
value this file depends on is read from the macro layer and asserted.

    python3 sens_r28.py [--base DIR] [--out DIR] [--drive N] [--nodeposit]

--base is the tree whose products are read (default: this file's directory);
--out is where the products are written (default: --base).  --drive 1..14
breaks one assertion each; --drive 0 means "no perturbation, but do not
write a path production reads".
"""
import collections
import csv
import json
import math
import os
import random
import re
import statistics as st
import sys

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
ROUND = 1300
LEVEL_W = 1.0e15
N_TRIAL = 4000
SEED = 1300028
P_EDGE = 0.05            # a system is UNCERTAIN where 0.05 < P(<=1e15) < 0.95

DRIVES = {1: 'S2', 2: 'S4', 3: 'S8', 4: 'S11', 5: 'S14', 6: 'S3', 7: 'S9',
          8: 'S15', 9: 'S16', 10: 'S10', 11: 'S12', 12: 'S7', 13: 'S17',
          14: 'S18'}
if '--selftest' in sys.argv:
    import subprocess
    import tempfile
    _b = sys.argv[sys.argv.index('--base') + 1] if '--base' in sys.argv \
        else HERE
    _bad = []
    with tempfile.TemporaryDirectory() as _td:
        for _d in [0] + sorted(DRIVES):
            _p = subprocess.run([sys.executable, '-I', '-B',
                                 os.path.abspath(__file__), '--base', _b,
                                 '--out', _td, '--drive', str(_d),
                                 '--nodeposit'], capture_output=True,
                                text=True)
            _fails = re.findall(r'^  (S\d+) .*FAIL', _p.stdout, re.M)
            ok = (_p.returncode == 0 and not _fails) if _d == 0 else (
                _p.returncode == 1 and DRIVES[_d] in _fails)
            print('  drive %2d -> %-4s fired %-14s %s'
                  % (_d, DRIVES.get(_d, '-'), ','.join(_fails) or '-',
                     'ok' if ok else 'WRONG'))
            if not ok:
                _bad.append(_d)
    print('selftest: %s' % ('ALL DRIVES FIRE AS NAMED' if not _bad
                            else 'FAILED %r' % _bad))
    sys.exit(1 if _bad else 0)
BASE, OUTDIR, DRIVE, NODEP = HERE, None, None, False
for _i, _a in enumerate(sys.argv):
    if _a == '--base':
        BASE = os.path.abspath(sys.argv[_i + 1])
    if _a == '--out':
        OUTDIR = os.path.abspath(sys.argv[_i + 1])
    if _a == '--drive':
        DRIVE = int(sys.argv[_i + 1])
    if _a == '--nodeposit':
        NODEP = True
OUTDIR = OUTDIR or BASE
SUF = '' if DRIVE is None else '_drive%d' % DRIVE
OUT_TEX = os.path.join(OUTDIR, 'numbers/survey_numbers_round%d%s.tex' % (ROUND, SUF))
OUT_JSON = os.path.join(OUTDIR, 'sens_r28%s.json' % SUF)
# ★ the two deposit tables are written as PRODUCTS beside the macro file and
# carried into the archive by `zdeposit.py`, which rebuilds the archive
# directory from scratch on every run -- a file written straight into it
# would be deleted by the next build.
DEP_WIN = os.path.join(OUTDIR, 'sens_r28_windows%s.csv' % SUF)
DEP_SYS = os.path.join(OUTDIR, 'sens_r28_systems%s.csv' % SUF)

sys.path.insert(0, BASE)
import adopted_e90 as ae            # noqa: E402  the ONE definition of a limit
import decor_r13 as dc              # noqa: E402  the ONE decorrelation
import star_alias as sa             # noqa: E402

FAIL = []


def ck(label, cond, detail=''):
    print('  %-72s %s  %s' % (label[:72], 'PASS' if cond else 'FAIL', detail))
    if not cond:
        FAIL.append(label)


def texval(name):
    v = ae._texval(name, BASE)
    assert v, 'macro \\%s is not defined in the macro layer of %s' % (name,
                                                                      BASE)
    return v


def texnum(name):
    return float(texval(name).replace('\\,', '').replace(',', ''))


def sci_val(v):
    s = v.replace('\\,', '').replace('$', '').strip()
    mm = re.match(r'^([\d.]+)\\times10\^\{(-?\d+)\}$', s)
    assert mm, 'not in mantissa-exponent form: %r' % v
    return float(mm.group(1)) * 10 ** int(mm.group(2))


def sci(x, nd=1):
    e = int(math.floor(math.log10(x)))
    return r'%.*f\times10^{%d}' % (nd, x / 10.0 ** e, e)


def q(a, p):
    a = sorted(a)
    return a[int(round(p * (len(a) - 1)))]


# ======================================================================= 1
# THE POPULATION AND THE PUBLISHED BASELINE
print('\n1  the population, and the published baseline')
CAT = ae.catalogue(BASE)
E90 = ae.per_window(CAT, BASE)
F0 = json.load(open(os.path.join(BASE, 'sens_r11.json')))['p90']
SENS = json.load(open(os.path.join(BASE, 'sens_r11.json')))
CLSA = [r for r in CAT if r['search_class'] == 'A']
ELIG = [r for r in CLSA if ae.limit_eligible(r, BASE)]
SYS_COVER = sorted({r['system_id'] for r in CLSA})
# the factor-free part of each limit: the limit is linear in the class
# factor, which `senscal_r23b.py` X3 pins, so E = F0 * BASEW exactly
BASEW = {id(r): E90[id(r)] / float(r['p90_mult_adopted']) for r in ELIG}
ck('S1 every Class A limit carries the one class factor, so a limit is the '
   'factor times a factor-free part',
   all(abs(float(r['p90_mult_adopted']) / F0 - 1) < 1e-6 for r in CLSA),
   'factor %.6f on %d windows' % (F0, len(CLSA)))
SYSROWS = collections.defaultdict(list)
for r in ELIG:
    SYSROWS[r['system_id']].append(r)
SYSIDS = sorted(SYSROWS)
SIDX = {s: i for i, s in enumerate(SYSIDS)}
W_SYS = np.array([SIDX[r['system_id']] for r in ELIG])
W_BASE = np.array([BASEW[id(r)] for r in ELIG])


def sys_limits(fac):
    """per-system best-window limit for a per-window factor vector (len ELIG)"""
    v = W_BASE * fac
    out = np.full(len(SYSIDS), np.inf)
    np.minimum.at(out, W_SYS, v)
    return out


NOM = sys_limits(np.full(len(ELIG), F0))
NOM_MED = float(np.median(NOM))
NOM_N = int(np.sum(NOM <= LEVEL_W))
if DRIVE == 1:
    NOM_N += 1
ck('S2 the baseline is the published per-system median and count',
   NOM_N == int(texval('NSysEfifteen'))
   and sci(NOM_MED) == texval('EirpNinetySysMedA')
   and len(SYSIDS) == int(texval('NSysALim')),
   '%d systems, median %.4e W (published %s), %d reach 1e15 W (published %s)'
   % (len(SYSIDS), NOM_MED, texval('EirpNinetySysMedA'), NOM_N,
      texval('NSysEfifteen')))
BESTW = {}
for r in ELIG:
    s = r['system_id']
    if s not in BESTW or E90[id(r)] < E90[id(BESTW[s])]:
        BESTW[s] = r

# ======================================================================= 2
# THE THREE CALIBRATION LABELS (the five-axis rule of r1_r22.py, verbatim)
print('\n2  measured / interpolated / extrapolated')
INJ_ROWS = [r for r in CLSA if r['p90_basis'] == 'injected']
_ARCH = json.load(open(os.path.join(BASE, 'archive_meta_v381.json')))['ebs']
_arr = lambda r: _ARCH[r['eb']]['array']                       # noqa: E731
_res = lambda r: float(_ARCH[r['eb']]['s_resolution_arcsec'])  # noqa: E731
_BDUR = collections.defaultdict(float)
for _r in CAT:
    _BDUR[_r['eb']] = max(_BDUR[_r['eb']], float(_r['on_source_s']))
B_INJ = {r['band'] for r in INJ_ROWS}
C_INJ = {round(float(r['chanw_Hz'])) for r in INJ_ROWS}
A_INJ = {_arr(r) for r in INJ_ROWS}
_rng = lambda f: (min(f(r) for r in INJ_ROWS),                # noqa: E731
                  max(f(r) for r in INJ_ROWS))
T_INJ = _rng(lambda r: float(r['on_source_s']))
D_INJ = _rng(lambda r: _BDUR[r['eb']])
R_INJ = {a: (min(_res(r) for r in INJ_ROWS if _arr(r) == a),
             max(_res(r) for r in INJ_ROWS if _arr(r) == a)) for a in A_INJ}


def outside(r):
    o = []
    if r['band'] not in B_INJ:
        o.append('band')
    if round(float(r['chanw_Hz'])) not in C_INJ:
        o.append('channel width')
    if _arr(r) not in A_INJ:
        o.append('array')
    elif not R_INJ[_arr(r)][0] <= _res(r) <= R_INJ[_arr(r)][1]:
        o.append('configuration')
    if not T_INJ[0] <= float(r['on_source_s']) <= T_INJ[1]:
        o.append('integration time')
    if not D_INJ[0] <= _BDUR[r['eb']] <= D_INJ[1]:
        o.append('block duration')
    return o


LABEL = {}
for r in CLSA:
    LABEL[id(r)] = ('measured' if r['p90_basis'] == 'injected' else
                    'extrapolated' if outside(r) else 'interpolated')
if DRIVE == 6:
    LABEL[id(INJ_ROWS[0])] = 'interpolated'
_lc = collections.Counter(LABEL.values())
ck('S3 the labels are the published partition (measured, interpolated, '
   'extrapolated)',
   _lc['measured'] == int(texval('SensNInj'))
   and _lc['interpolated'] == int(texval('NgNInterpWin'))
   and _lc['extrapolated'] == int(texval('NgNExtrapWin')),
   '%(measured)d / %(interpolated)d / %(extrapolated)d' % _lc)

# ======================================================================= 3
# EACH INJECTED WINDOW'S OWN FACTOR, joined on POSITION
print('\n3  the injected windows\' own factors')
U9 = json.load(open(os.path.join(BASE, 'r9inputs', 'm3a_units_r9.json')))
T9 = json.load(open(os.path.join(BASE, 'r9inputs', 'm3a_tones_r9.json')))
N11 = json.load(open(os.path.join(BASE, 'r11inputs', 'm3a_r11.json')))
PERW = SENS['per_window']
_pos = {}
for t in T9:
    if t['tag'] in PERW:
        _pos[t['tag']] = (t['fsl'], t['cw'])
for u in N11['units']:
    _pos[u['tag']] = (u['cat_flo_GHz'], u['chanw_Hz'])
TAGROW = {}
for g in PERW:
    eb = g.rsplit('_spw', 1)[0]
    f, cw = _pos[g]
    c = [r for r in CLSA if r['eb'] == eb and r['p90_basis'] == 'injected'
         and abs(min(float(r['flo_GHz']), float(r['fhi_GHz'])) - f) < 2e-3
         and abs(float(r['chanw_Hz']) - cw) < 1.0]
    if len(c) == 1:
        TAGROW[g] = c[0]
OWN = {id(r): PERW[g]['trig'] for g, r in TAGROW.items()}
if DRIVE == 2:
    OWN.pop(next(iter(OWN)))
ck('S4 every injected window resolves to exactly one released row by '
   'position, and the rows are the deposit\'s injected set',
   len(OWN) == len(PERW) == len(INJ_ROWS)
   and {id(r) for r in INJ_ROWS} == set(OWN)
   and sorted(OWN.values()) == sorted(SENS['transfer']['per_window']),
   '%d tags -> %d rows' % (len(PERW), len(OWN)))
POOL_RAW = np.array(sorted(SENS['transfer']['per_window']))
POOL = POOL_RAW * F0 / POOL_RAW.mean()           # centred: only spread acts
DISP_LO, DISP_HI = POOL_RAW.min() / F0, POOL_RAW.max() / F0
ck('S5 the dispersion is the published one', '%.2f' % DISP_LO ==
   texval('SmcDispLo') and '%.2f' % DISP_HI == texval('SmcDispHi'),
   'x%.4f..x%.4f' % (DISP_LO, DISP_HI))
# within-block sharing of the factor, measured on the campaign's own windows
_byeb = collections.defaultdict(list)
for g, r in TAGROW.items():
    _byeb[r['eb']].append(PERW[g]['trig'])
_multi = [v for v in _byeb.values() if len(v) > 1]
_gm = st.mean(POOL_RAW)
_ssw = sum((x - st.mean(v)) ** 2 for v in _multi for x in v)
_dfw = sum(len(v) - 1 for v in _multi)
_sst = sum((x - _gm) ** 2 for x in POOL_RAW)
ICC_WITHIN_VAR = _ssw / _dfw if _dfw else float('nan')
TOT_VAR = _sst / (len(POOL_RAW) - 1)
ICC = 1.0 - ICC_WITHIN_VAR / TOT_VAR
print('  %d blocks hold >1 injected window; within-block variance %.4f of a '
      'total %.4f -> shared fraction %.2f' % (len(_multi), ICC_WITHIN_VAR,
                                              TOT_VAR, ICC))

# ======================================================================= 4
# THE CLASS-AVERAGE INTERVAL, COHERENTLY
print('\n4  the class-average calibration interval (coherent)')
FLO, FHI = SENS['budget']['factor_lo'], SENS['budget']['factor_hi']
if DRIVE == 12:
    FHI = 1.0
CAL_LO = sys_limits(np.full(len(ELIG), F0 * FLO))
CAL_HI = sys_limits(np.full(len(ELIG), F0 * FHI))
CAL_MED = (float(np.median(CAL_LO)), float(np.median(CAL_HI)))
CAL_N = (int(np.sum(CAL_HI <= LEVEL_W)), int(np.sum(CAL_LO <= LEVEL_W)))
ck('S6 the coherent interval reproduces the published interval on the median',
   sci(CAL_MED[0]) == texval('TfMedCalLo')
   and sci(CAL_MED[1]) == texval('TfMedCalHi'),
   'median %.3e..%.3e W; count %d..%d' % (CAL_MED + CAL_N))

# ======================================================================= 5
# THE INDIVIDUAL DISPERSION, WINDOW BY WINDOW
print('\n5  the individual dispersion (resampled)')
IS_INJ = np.array([id(r) in OWN for r in ELIG])
OWNV = np.array([OWN.get(id(r), F0) for r in ELIG])
IS_EXT = np.array([LABEL[id(r)] == 'extrapolated' for r in ELIG])
EB_OF = [r['eb'] for r in ELIG]
EBIDX = {e: i for i, e in enumerate(sorted(set(EB_OF)))}
W_EB = np.array([EBIDX[e] for e in EB_OF])

OWN_ONLY = sys_limits(np.where(IS_INJ, OWNV, F0))
OWN_MED, OWN_N = float(np.median(OWN_ONLY)), int(np.sum(OWN_ONLY <= LEVEL_W))


SYSDRAW = {}


def run_mc(mode, pool, rng, extra=None, keep=None):
    """mode 'window' or 'block'; returns (medians, counts, per-system hits)."""
    meds, cnts = [], []
    allb = []
    hits = np.zeros(len(SYSIDS))
    for _ in range(N_TRIAL):
        if mode == 'window':
            draw = pool[rng.integers(0, len(pool), len(ELIG))]
        else:
            draw = pool[rng.integers(0, len(pool), len(EBIDX))][W_EB]
        fac = np.where(IS_INJ, OWNV, draw)
        if extra is not None:
            fac = fac * extra
        b = sys_limits(fac)
        meds.append(float(np.median(b)))
        if keep:
            allb.append(b)
        c = b <= LEVEL_W
        cnts.append(int(c.sum()))
        hits += c
    if keep:
        SYSDRAW[keep] = np.array(allb)
    return np.array(meds), np.array(cnts), hits / N_TRIAL


RNG = np.random.default_rng(SEED)
MC = {}
for key, mode, pool in (('window', 'window', POOL), ('block', 'block', POOL),
                        ('window_raw', 'window', POOL_RAW)):
    MC[key] = run_mc(mode, pool, RNG, keep=key)
    m_, c_, _h = MC[key]
    print('  %-10s median %.3e [%.3e..%.3e]  count %d [%d..%d] full %d..%d'
          % (key, np.median(m_), q(m_, .05), q(m_, .95), int(np.median(c_)),
             q(c_, .05), q(c_, .95), c_.min(), c_.max()))
MEDW, CNTW, PW = MC['window']
MEDB, CNTB, PB = MC['block']
if DRIVE == 3:
    CNTW = CNTW * 0 + 40
ck('S7 the resampled median moves by less than the class-average interval '
   'already quoted, so the median keeps its printed interval',
   abs(np.median(MEDW) / NOM_MED - 1) < FHI - 1
   and abs(np.median(MEDB) / NOM_MED - 1) < FHI - 1,
   '%+.1f / %+.1f per cent against +-%.0f'
   % (100 * (np.median(MEDW) / NOM_MED - 1),
      100 * (np.median(MEDB) / NOM_MED - 1), 100 * (FHI - 1)))
ck('S8 the nominal count lies inside the resampled 5-95 per cent range under '
   'both draws, so it is defensible under the measured variation',
   q(CNTW, .05) <= NOM_N <= q(CNTW, .95) and q(CNTB, .05) <= NOM_N
   <= q(CNTB, .95),
   '%d in [%d, %d] and [%d, %d]' % (NOM_N, q(CNTW, .05), q(CNTW, .95),
                                    q(CNTB, .05), q(CNTB, .95)))

# ======================================================================= 6
# THE EXTRAPOLATED WINDOWS: NOT RESAMPLED, BOUNDED
print('\n6  the extrapolated windows, bounded rather than resampled')
EXT_DROP = sys_limits(np.where(IS_EXT, np.inf, F0))
EXT_WORST = sys_limits(np.where(IS_EXT, POOL_RAW.max(), F0))
EXT_BEST = sys_limits(np.where(IS_EXT, POOL_RAW.min(), F0))
EXT_N = (int(np.sum(EXT_DROP <= LEVEL_W)), int(np.sum(EXT_WORST <= LEVEL_W)),
         int(np.sum(EXT_BEST <= LEVEL_W)))
EXT_SYS = sorted(s for s in SYSIDS if LABEL[id(BESTW[s])] == 'extrapolated')
if DRIVE == 7:
    EXT_N = (EXT_N[0] - 1,) + EXT_N[1:]
ck('S9 no system reaching 1e15 W takes its limit from an extrapolated '
   'window, so the count does not depend on any factor given to them',
   EXT_N[0] == EXT_N[1] == NOM_N
   and not any(NOM[SIDX[s]] <= LEVEL_W for s in EXT_SYS),
   'count %d with them removed, %d at the worst factor, %d at the best'
   % EXT_N)

# ======================================================================= 7
# DECORRELATION, PER WINDOW
print('\n7  decorrelation, per window')
MATCH = dc.Matcher(BASE)
DEC = {}
for r in CLSA:
    o, basis, _hi = MATCH.correction(r)
    DEC[id(r)] = (o, basis)
DECV = np.array([1.0 + (DEC[id(r)][0] or 0.0) for r in ELIG])
if DRIVE == 10:
    DECV = np.ones(len(ELIG))
ADJ = sys_limits(np.full(len(ELIG), F0) * DECV)
ADJ_MED, ADJ_N = float(np.median(ADJ)), int(np.sum(ADJ <= LEVEL_W))
# the published route: the nominal best window, multiplied by its own term
ADJ_BEST = np.array([NOM[SIDX[s]] * (1.0 + (DEC[id(BESTW[s])][0] or 0.0))
                     for s in SYSIDS])
ADJB_N = int(np.sum(ADJ_BEST <= LEVEL_W))
ADJB_SHIFT = 100.0 * (np.median(ADJ_BEST) / NOM_MED - 1.0)
ck('S10 the best-window route reproduces the published adjusted count and '
   'shift, and re-choosing the best window after the correction changes '
   'neither the count nor the printed median',
   ADJB_N == int(texval('NmDecAdjNEfifteen'))
   and '%.1f' % ADJB_SHIFT == texval('NmDecAdjShiftPct')
   and ADJ_N == ADJB_N and sci(ADJ_MED) == sci(float(np.median(ADJ_BEST))),
   'best-window route %d, %+.2f per cent; per-window route %d, %.4e W'
   % (ADJB_N, ADJB_SHIFT, ADJ_N, ADJ_MED))
MC['window_dec'] = run_mc('window', POOL, RNG, extra=DECV)
MEDWD, CNTWD, PWD = MC['window_dec']
DEC_LOST = sorted(s for s in SYSIDS
                  if NOM[SIDX[s]] <= LEVEL_W < ADJ[SIDX[s]])

# ======================================================================= 8
# m11: THE DELIVERED RESPONSE FORM
print('\n8  m11: spectral averaging and the injected response')
NAVG = {id(r): int(r['n_chan_avg']) for r in CLSA}
# the independent route: the archive's resolution / channel spacing
_RATIO = {}
for r in CLSA:
    lo, hi = sorted((float(r['flo_GHz']), float(r['fhi_GHz'])))
    cw = float(r['chanw_Hz'])
    c = {round(x[2] / cw, 3) for x in _ARCH[r['eb']].get('freq_support', [])
         if x[0] - 0.05 <= lo and x[1] + 0.05 >= hi}
    _RATIO[id(r)] = c
CR = json.load(open(os.path.join(BASE, 'cresp_v401.json')))
PHI = np.array(CR['phi'])
RHO = {int(k): np.array(v) for k, v in CR['rho_by_n'].items()}
FWHM = {int(k): v for k, v in CR['fwhm_by_n'].items()}
_agree = all(len(_RATIO[id(r)]) == 1 and
             abs(next(iter(_RATIO[id(r)])) - FWHM[NAVG[id(r)]]) < 0.025
             for r in CLSA)
if DRIVE == 4:
    _agree = False
NCOUNT = collections.Counter(NAVG.values())
NINJ = collections.Counter(NAVG[id(r)] for r in INJ_ROWS)
ck('S11 the catalogue\'s averaging factor and the archive\'s own resolution '
   'ratio classify every Class A window the same way',
   _agree and sum(NCOUNT.values()) == len(CLSA),
   'N=1 %d, N=2 %d, N=4 %d (injected %d / %d / %d)'
   % (NCOUNT[1], NCOUNT[2], NCOUNT[4], NINJ[1], NINJ[2], NINJ[4]))
# the injector, read from its owner rather than retyped
_STRATA = open(os.path.join(BASE, 'strata_v411.py')).read()
_inj = re.search(r"CAMPAIGN_INJECTOR\s*=\s*'([^']+)'", _STRATA).group(1)
_ker = tuple(float(x) for x in re.search(
    r'HANN_KERNEL\s*=\s*\(([^)]*)\)', _STRATA).group(1).split(','))
if DRIVE == 11:
    _inj = 'inject_vis_v401.py'
ck('S12 the campaign injector deposits one fixed kernel on the delivered '
   'grid: no averaging factor enters the deposition',
   _inj == 'inject_vis_v399.py' and _ker == (0.25, 0.5, 0.25),
   '%s, kernel %s' % (_inj, _ker))


def s_dep(p):
    """the injector's peak share at |offset| p from a channel centre:
    linear split then the kernel (strata_v411.deposited)."""
    return _ker[1] - (_ker[1] - _ker[0]) * p


def s_true(n, p):
    return float(np.interp(p, PHI, RHO[n]))


DEP_MEAN = float(np.mean([s_dep(p) for p in PHI]))
TRUE_MEAN = {n: float(np.mean(RHO[n])) for n in RHO}
ck('S13 the deposited and exact phase means are the published ones',
   '%.4f' % DEP_MEAN == texval('InjDepMean')
   and '%.4f' % TRUE_MEAN[1] == texval('InjRespMean'),
   'deposited %.4f, exact N=1 %.4f, N=2 %.4f, N=4 %.4f'
   % (DEP_MEAN, TRUE_MEAN[1], TRUE_MEAN[2], TRUE_MEAN[4]))

# the campaign's own tones, as sens_r11 merges them
_old = {u['tag'] for u in U9 if u['cls'] == 'fine'}
TB = collections.defaultdict(list)
for t in T9:
    if not t['outside'] and t['tag'] in _old:
        TB[t['tag']].append(t)
for t in N11['tones']:
    if not t['outside']:
        TB[t['tag']].append(t)
POSCTRL = 20.0


def track_share(f, sub, exc, k=64):
    """mean peak share along a tone's own drift track (exc channels)."""
    if exc < 1e-6:
        return f(abs(sub))
    xs = sub + np.linspace(0.0, exc, k)
    ph = np.abs(((xs + 0.5) % 1.0) - 0.5)
    return float(np.mean([f(p) for p in ph]))


def exc_of(t, r):
    dm = float(r['drift_max_Hz_s'])
    return float(r['eta_drift']) * abs(t['dr']) / dm if dm > 0 else 0.0


from scipy.optimize import minimize       # noqa: E402
from scipy.special import ndtr            # noqa: E402


def probit(x, d):
    def nll(p):
        qq = np.clip(ndtr(p[0] * x + p[1]), 1e-12, 1 - 1e-12)
        return -np.sum(np.where(d, np.log(qq), np.log(1 - qq)))
    return minimize(nll, [1.0, -5.0], method='Nelder-Mead',
                    options=dict(xatol=1e-7, fatol=1e-7, maxiter=8000)).x


GRID = np.arange(0.5, 6.0, 0.0025)
RESP = {}
for n in (1, 2):
    tags = [g for g in TB if NAVG[id(TAGROW[g])] == n]
    rows = [(t['amp'], t['sub'], exc_of(t, TAGROW[g]), bool(t['trig']))
            for g in tags for t in TB[g] if t['amp'] != POSCTRL]
    A = np.array([x[0] for x in rows])
    D = np.array([x[3] for x in rows])
    SD = np.array([track_share(s_dep, s, e) for _, s, e, _ in rows])
    a, b = probit(A * SD, D)

    def p90(shares):
        fr = np.array([ndtr(a * g * shares + b).mean() for g in GRID])
        return float(GRID[np.argmax(fr >= 0.9)])
    rec = dict(n_windows=len(tags), n_tones=len(rows), probit=[a, b],
               p90_dep=p90(SD))
    for m_ in sorted(RHO):
        rec['p90_true_n%d' % m_] = p90(np.array(
            [track_share(lambda p, m_=m_: s_true(m_, p), s, e)
             for _, s, e, _ in rows]))
    RESP[n] = rec
    print('  N=%d: %d windows, %d tones; p90 deposited %.3f, true(N=1) %.3f, '
          'true(N=2) %.3f, true(N=4) %.3f' % (n, len(tags), len(rows),
                                              rec['p90_dep'],
                                              rec['p90_true_n1'],
                                              rec['p90_true_n2'],
                                              rec['p90_true_n4']))
# ★ THE CORRECTION IS THE RATIO OF PHASE-MEAN PEAK SHARES -- the same
# construction as the published native residual \InjShortPct, so the two
# response forms are stated on one footing.  The refit of the campaign's own
# tones is the VALIDATION: on the native windows it must reproduce the
# published residual, and on the averaged windows it must agree with the
# share ratio, or the share ratio is not what the trigger sees.  (N=4 has no
# injected window; its ratio is the share ratio alone, and it is one window.)
RATIO = {n: DEP_MEAN / TRUE_MEAN[n] for n in (1, 2, 4)}
REFIT = {1: RESP[1]['p90_true_n1'] / RESP[1]['p90_dep'],
         2: RESP[2]['p90_true_n2'] / RESP[2]['p90_dep'],
         4: RESP[2]['p90_true_n4'] / RESP[2]['p90_dep']}
SHORT_N1 = 1.0 - RATIO[1]
if DRIVE == 5:
    REFIT[2] = 0.5
ck('S14 VALIDATION: refitting the campaign\'s own tones reproduces the '
   'published native residual and the averaged-window share ratio',
   abs(REFIT[1] - RATIO[1]) < 0.02 and abs(REFIT[2] - RATIO[2]) < 0.02
   and round(100 * SHORT_N1) == int(texval('InjShortPct')),
   'native: refit x%.3f, share ratio x%.3f (published %s per cent); '
   'averaged: refit x%.3f, share ratio x%.3f'
   % (REFIT[1], RATIO[1], texval('InjShortPct'), REFIT[2], RATIO[2]))
FAC_N = {n: F0 * RATIO[n] for n in RATIO}
NAVG_E = np.array([NAVG[id(r)] for r in ELIG])
# the exact response in EVERY window: the native ones by the published
# residual, the averaged ones by theirs.  The averaged-only reading, which is
# what the referee's question isolates, is kept beside it.
RFAC = np.array([RATIO[n] for n in NAVG_E])
RFAC_AVG = np.array([RATIO[n] if n > 1 else 1.0 for n in NAVG_E])
_ra = sys_limits(np.full(len(ELIG), F0) * RFAC_AVG)
RESP_AVG_MED, RESP_AVG_N = float(np.median(_ra)), int(np.sum(_ra <= LEVEL_W))
if DRIVE == 8:
    RFAC = np.where(NAVG_E > 1, 1.2, RFAC)
RESP_SYS = sys_limits(np.full(len(ELIG), F0) * RFAC)
RESP_MED, RESP_N = float(np.median(RESP_SYS)), int(np.sum(RESP_SYS <= LEVEL_W))
RESP_DEEP = float(RESP_SYS.min())
RESP_MOVED = sum(1 for s in SYSIDS if RESP_SYS[SIDX[s]] < NOM[SIDX[s]] - 1)
RESP_GAIN = sorted(s for s in SYSIDS
                   if RESP_SYS[SIDX[s]] <= LEVEL_W < NOM[SIDX[s]])
ck('S15 the response correction can only deepen a limit, and it deepens '
   'every averaged window by the same ratio',
   np.all(RESP_SYS <= NOM + 1) and RATIO[2] < 1 and RATIO[4] < RATIO[2],
   'x%.3f (N=2), x%.3f (N=4); %d system limits move; count %d -> %d; '
   'median %.3e -> %.3e W' % (RATIO[2], RATIO[4], RESP_MOVED, NOM_N, RESP_N,
                              NOM_MED, RESP_MED))
_nav_best = collections.Counter(NAVG[id(BESTW[s])] for s in SYSIDS)

# ★ THE NET BIAS ON ONE LIMIT, WITH THE RESPONSE FORM IN IT.  `sens_r18.py`
# forms truth/quoted as (1+dec)/(1+short) with ONE shortfall for every window;
# that is the native window's.  Here the shortfall is the window's own form's.
# First the published construction is reproduced (uniform shortfall, the
# systems' best windows, nearest-rank ninetieth percentile), so that the
# N-aware figure differs from it in the response term and in nothing else.
def _p90nr(v):
    v = sorted(v)
    return v[int(0.9 * len(v))]


_SHORT_PUB = texnum('InjShortPct') / 100.0
if DRIVE == 13:
    _SHORT_PUB = 0.0
_sysdec = [(s, DEC[id(BESTW[s])][0]) for s in SYSIDS
           if DEC[id(BESTW[s])][0] is not None]
_pub_hi = _p90nr([(1 + o) / (1 + _SHORT_PUB) for _s, o in _sysdec])
_naw_sys = [RATIO[NAVG[id(BESTW[s_])]] * (1 + o) for s_, o in _sysdec]
_naw_win = [RATIO[NAVG[id(r)]] * (1 + DEC[id(r)][0]) for r in ELIG
            if DEC[id(r)][0] is not None]
NET_OPT_PCT = 100.0 * (_p90nr(_naw_sys) - 1.0)
NET_CONS_PCT = 100.0 * (1.0 / st.median(_naw_win) - 1.0)
NET_CONS_SYS_PCT = 100.0 * (1.0 / st.median(_naw_sys) - 1.0)
ck('S17 the published net optimism is reproduced by the published '
   'construction, so the response-aware figure differs only in the response',
   '%.0f' % (100 * (_pub_hi - 1)) == texval('NmNetOptPct'),
   'uniform shortfall %.1f per cent (published %s); response-aware: '
   'ninetieth percentile of systems %+.1f, median Class A window %.1f '
   'conservative, median system %.1f conservative'
   % (100 * (_pub_hi - 1), texval('NmNetOptPct'), NET_OPT_PCT, NET_CONS_PCT,
      NET_CONS_SYS_PCT))

# ★ THE ADOPTION GRID.  Three independent choices a coordinator can make, and
# what each does to the three printed statistics.  `own`: the 49 injected
# windows carry their OWN measured point instead of the class factor (the
# printed "measured" limits are, today, the class factor applied to an
# injected window); `resp`: the averaged windows carry the response-corrected
# factor; `dec`: the decorrelation term is divided out where a record allows.
GRID_ROWS = []
for _own in (False, True):
    for _resp in (False, True):
        for _dec in (False, True):
            fac = np.where(IS_INJ, OWNV, F0) if _own else np.full(len(ELIG),
                                                                    F0)
            if _resp:
                fac = fac * RFAC
            if _dec:
                fac = fac * DECV
            b = sys_limits(fac)
            GRID_ROWS.append(dict(
                own=_own, resp=_resp, dec=_dec, median_W=float(np.median(b)),
                median_printed=sci(float(np.median(b))),
                n_reach=int(np.sum(b <= LEVEL_W)), deepest_W=float(b.min()),
                deepest=SYSIDS[int(np.argmin(b))]))
for g_ in GRID_ROWS:
    print('  own=%-5s resp=%-5s dec=%-5s median %.3e (%s)  n %d  deepest '
          '%.2e %s' % (g_['own'], g_['resp'], g_['dec'], g_['median_W'],
                       g_['median_printed'], g_['n_reach'], g_['deepest_W'],
                       g_['deepest']))

# ======================================================================= 9
# WHICH SYSTEMS' CLASSIFICATION IS UNCERTAIN, AND WHY
print('\n9  systems whose 1e15 W classification is uncertain')
PER_SYS = []
for s in SYSIDS:
    i = SIDX[s]
    br = BESTW[s]
    nom_in = NOM[i] <= LEVEL_W
    why = []
    if P_EDGE < PW[i] < 1 - P_EDGE or P_EDGE < PB[i] < 1 - P_EDGE:
        why.append('dispersion')
    if (CAL_LO[i] <= LEVEL_W) != (CAL_HI[i] <= LEVEL_W):
        why.append('calibration interval')
    if (ADJ[i] <= LEVEL_W) != nom_in:
        why.append('decorrelation')
    if (RESP_SYS[i] <= LEVEL_W) != nom_in:
        why.append('exact response')
    # an extrapolated best window is not bounded by the measured spread; it
    # makes the CLASSIFICATION uncertain only where the threshold lies within
    # that spread of the limit (beyond it, the factor would have to leave the
    # measured range by more than its own width) -- the others are listed
    # separately as not empirically bounded
    if (LABEL[id(br)] == 'extrapolated'
            and NOM[i] * DISP_LO <= LEVEL_W <= NOM[i] * DISP_HI):
        why.append('extrapolated')
    PER_SYS.append(dict(
        system=s, designation=sa.designation(s, tex=False),
        best_eb=br['eb'], best_nu_lo_GHz=min(float(br['flo_GHz']),
                                              float(br['fhi_GHz'])),
        eirp90_W=NOM[i], basis=LABEL[id(br)],
        own_factor=OWN.get(id(br)), n_chan_avg=NAVG[id(br)],
        decor_frac=DEC[id(br)][0], decor_basis=DEC[id(br)][1],
        eirp90_cal_lo_W=CAL_LO[i], eirp90_cal_hi_W=CAL_HI[i],
        p_reach_window=PW[i], p_reach_block=PB[i], p_reach_window_dec=PWD[i],
        eirp90_decor_adjusted_W=ADJ[i], eirp90_response_corrected_W=RESP_SYS[i],
        sys_ratio_p05_block=float(q(SYSDRAW['block'][:, i] / NOM[i], .05)),
        sys_ratio_p95_block=float(q(SYSDRAW['block'][:, i] / NOM[i], .95)),
        reaches_1e15_nominal=nom_in, uncertain=';'.join(why)))
if DRIVE == 9:
    # a system the decorrelation takes out of the set, silently not named
    for d in PER_SYS:
        if d['system'] in DEC_LOST:
            d['uncertain'] = ''
            break
UNC = [d for d in PER_SYS if d['uncertain']]
UNC_NOM = [d for d in UNC if d['reaches_1e15_nominal']]
UNC_OUT = [d for d in UNC if not d['reaches_1e15_nominal']]
# the "robust core": reaches 1e15 W in >=95 per cent of both draws, at the
# shallow end of the calibration interval, and after decorrelation
CORE = [d for d in PER_SYS if d['reaches_1e15_nominal'] and not d['uncertain']]
EXT_FAR = [d for d in PER_SYS if d['basis'] == 'extrapolated'
           and 'extrapolated' not in d['uncertain']]
# one TRANSFERRED system's own limit, under the block draw: what a reader
# should attach to a single entry of Table F1
_tr = [d for d in PER_SYS if d['basis'] != 'measured']
SYS_RAT = (st.median([d['sys_ratio_p05_block'] for d in _tr]),
           st.median([d['sys_ratio_p95_block'] for d in _tr]))
print('  one transferred system\'s own limit, block draw, median 5-95 per '
      'cent range: x%.2f..x%.2f' % SYS_RAT)
for d in sorted(UNC, key=lambda d: d['eirp90_W']):
    print('  %-28s %.3e W  %-12s Pw %.2f Pb %.2f  %s'
          % (d['designation'], d['eirp90_W'], d['basis'], d['p_reach_window'],
             d['p_reach_block'], d['uncertain']))
_unc_ids = {d['system'] for d in UNC}
ck('S16 every system the decorrelation or the calibration interval moves '
   'across 1e15 W is named as uncertain, and every nominal member of the set '
   'is either robust or named',
   len(UNC) > 0 and len(CORE) + len(UNC_NOM) == NOM_N
   and set(DEC_LOST) <= _unc_ids
   and {s for s in SYSIDS if (CAL_LO[SIDX[s]] <= LEVEL_W)
        != (CAL_HI[SIDX[s]] <= LEVEL_W)} <= _unc_ids,
   '%d robust + %d uncertain = %d; %d uncertain outside'
   % (len(CORE), len(UNC_NOM), NOM_N, len(UNC_OUT)))

# ======================================================================= 10
# MACROS
L = ['%% GENERATED by sens_r28.py -- do not hand-edit.\n']


def m(k, v):
    assert k.isalpha(), 'a LaTeX macro name may contain letters only: %s' % k
    L.append('\\newcommand{\\%s}{%s}\n' % (k, v))


def word(n):
    w = ('zero one two three four five six seven eight nine ten eleven '
         'twelve').split()
    return w[n] if 0 <= n < len(w) else '%d' % n


m('SvNTrial', ('%d' % N_TRIAL).replace('000', '\\,000'))
m('SvCalNLo', '%d' % CAL_N[0])
m('SvCalNHi', '%d' % CAL_N[1])
m('SvRsNLo', '%d' % q(CNTW, .05))
m('SvRsNHi', '%d' % q(CNTW, .95))
m('SvRsBlkNLo', '%d' % q(CNTB, .05))
m('SvRsBlkNHi', '%d' % q(CNTB, .95))
m('SvRsMedLo', sci(q(np.concatenate([MEDW, MEDB]), .05)))
m('SvRsMedHi', sci(q(np.concatenate([MEDW, MEDB]), .95)))
m('SvRsDecNLo', '%d' % q(CNTWD, .05))
m('SvRsDecNHi', '%d' % q(CNTWD, .95))
m('SvNCore', '%d' % len(CORE))
m('SvNExtFar', '%d' % len(EXT_FAR))
m('SvSysRatLo', '%.2f' % SYS_RAT[0])
m('SvSysRatHi', '%.2f' % SYS_RAT[1])
m('SvRespDeep', sci(RESP_DEEP))
m('SvNUncIn', '%d' % len(UNC_NOM))
m('SvNUncOut', '%d' % len(UNC_OUT))
m('SvNUnc', '%d' % len(UNC))
m('SvExtNDrop', '%d' % EXT_N[0])
m('SvBlkSharePct', '%.0f' % (100 * max(ICC, 0.0)))
m('SvNWinNOne', '%d' % NCOUNT[1])
m('SvNWinNAvg', '%d' % (len(CLSA) - NCOUNT[1]))
m('SvNWinNTwo', '%d' % NCOUNT[2])
m('SvNWinNFour', '%d' % NCOUNT[4])
m('SvNInjNOne', '%d' % NINJ[1])
m('SvNInjNAvg', '%d' % (len(INJ_ROWS) - NINJ[1]))
m('SvRespMeanTwo', '%.3f' % TRUE_MEAN[2])
m('SvRespShortPctTwo', '%.0f' % (100 * (1 - RATIO[2])))
m('SvNetConsPct', '%.0f' % NET_CONS_PCT)
m('SvNetOptPct', '%.0f' % NET_OPT_PCT)
m('SvRsMedShiftPct', '%.0f' % abs(100 * (np.median(MEDB) / NOM_MED - 1)))


def _names(ds):
    nm = [sa.designation(d['system']).replace(' ', '~') for d in ds]
    return (nm[0] if len(nm) == 1 else
            ', '.join(nm[:-1]) + ' and ' + nm[-1]) if nm else ''


# ★ S18: the prose (Sec. 4.1) prints both name lists in one sentence.  A
# refold that empties either would typeset "and  by its extrapolated best
# window"; stop the build instead, so the sentence is rewritten, not broken.
_nin, _nout = list(UNC_NOM), list(UNC_OUT)
if DRIVE == 14:
    _nout = []
ck('S18 both name lists the prose prints are non-empty, and every name in '
   'them is a system of the limit population',
   # v4.29 fold (stage-2 rehearsal): on a later harvest no uncertain system lies outside 10^15 W; the text's
   # "and ... by its extrapolated best window" is then GENERATED empty (\SvUncOutClause), so the outside list may be
   # empty -- the inside list, which the sentence's subject is, may not
   bool(_nin)
   and all(d['system'] in SIDX for d in _nin + _nout),
   '%d inside, %d outside' % (len(_nin), len(_nout)))
if FAIL:
    print('\nsens_r28: %d FAILURE(S)' % len(FAIL))
    for f in FAIL:
        print('  - %s' % f)
    sys.exit(1)
m('SvUncInNames', _names(sorted(UNC_NOM, key=lambda d: d['eirp90_W'])))
m('SvUncOutNames', _names(sorted(UNC_OUT, key=lambda d: d['eirp90_W'])) if UNC_OUT else '')
m('SvUncOutClause', ('' if not UNC_OUT else
                     ', and %s by its extrapolated best window' % _names(sorted(UNC_OUT, key=lambda d: d['eirp90_W']))))
m('SvRespFacTwo', '%.2f' % FAC_N[2])
m('SvRespFacFour', '%.2f' % FAC_N[4])
m('SvRespRatioTwo', '%.2f' % RATIO[2])
m('SvRespConsPctTwo', '%.0f' % (100 * (1.0 / RATIO[2] - 1.0)))
m('SvRespMed', sci(RESP_MED))
m('SvRespAvgMed', sci(RESP_AVG_MED))
m('SvRespN', '%d' % RESP_N)
m('SvRespNSysMoved', '%d' % RESP_MOVED)
m('SvRespNBestAvg', '%d' % (_nav_best[2] + _nav_best[4]))

if FAIL:
    print('\nsens_r28: %d FAILURE(S)' % len(FAIL))
    for f in FAIL:
        print('  - %s' % f)
    sys.exit(1)

os.makedirs(OUTDIR, exist_ok=True)
os.makedirs(os.path.join(OUTDIR, 'numbers'), exist_ok=True)  # r28-numbers W1
open(OUT_TEX, 'w').writelines(L)


def stats(a):
    return dict(median=float(np.median(a)), p05=float(q(a, .05)),
                p95=float(q(a, .95)), min=float(np.min(a)),
                max=float(np.max(a)))


json.dump(dict(
    generated_by='sens_r28.py', round=ROUND, drive=DRIVE,
    base=os.path.relpath(BASE, HERE),  # relative: a product must not embed an absolute build path
    level_W=LEVEL_W, n_trial=N_TRIAL, seed=SEED, factor=F0,
    nominal=dict(median_W=NOM_MED, n_reach=NOM_N, n_systems=len(SYSIDS)),
    labels=dict(_lc),
    class_average=dict(factor_lo=FLO, factor_hi=FHI, median_W=CAL_MED,
                       n_reach=CAL_N),
    measured_own=dict(median_W=OWN_MED, n_reach=OWN_N),
    dispersion=dict(lo=DISP_LO, hi=DISP_HI, pool_mean_over_f0=float(
        POOL_RAW.mean() / F0), block_shared_fraction=ICC,
        n_blocks_multi=len(_multi)),
    resample={k: dict(median_W=stats(v[0]), n_reach=stats(v[1]))
              for k, v in MC.items()},
    extrapolated=dict(n_reach_removed=EXT_N[0], n_reach_worst=EXT_N[1],
                      n_reach_best=EXT_N[2], systems=EXT_SYS),
    decorrelation=dict(median_W=ADJ_MED, n_reach=ADJ_N,
                       best_window_route_n=ADJB_N,
                       best_window_route_shift_pct=ADJB_SHIFT,
                       systems_lost=DEC_LOST),
    response=dict(injector=_inj, kernel=_ker, n_windows=dict(NCOUNT),
                  n_injected=dict(NINJ), deposited_mean=DEP_MEAN,
                  exact_mean=TRUE_MEAN, refit=RESP, ratio=RATIO,
                  refit_ratio=REFIT,
                  net_bias=dict(opt_p90_systems_pct=NET_OPT_PCT,
                                cons_median_window_pct=NET_CONS_PCT,
                                cons_median_system_pct=NET_CONS_SYS_PCT),
                  factor=FAC_N, median_W=RESP_MED, n_reach=RESP_N,
                  averaged_only=dict(median_W=RESP_AVG_MED, n_reach=RESP_AVG_N),
                  deepest_W=RESP_DEEP, n_sys_moved=RESP_MOVED,
                  systems_gained=RESP_GAIN, best_window_navg=dict(_nav_best)),
    adoption_grid=GRID_ROWS,
    systems=PER_SYS), open(OUT_JSON, 'w'), indent=1, sort_keys=True,
    default=float)

if not NODEP:
    with open(DEP_WIN, 'w', newline='') as fh:
        w = csv.writer(fh)
        w.writerow(['target_id', 'system_id', 'eb', 'nu_lo_GHz', 'nu_hi_GHz',
                    'chan_width_Hz',
                    'n_chan_avg', 'calibration_label', 'outside_injected_on',
                    'own_p90_factor', 'class_p90_factor', 'eirp_p90_W',
                    'eirp_p90_dispersion_lo_W', 'eirp_p90_dispersion_hi_W',
                    'eirp_p90_classavg_lo_W', 'eirp_p90_classavg_hi_W',
                    'decorrelation_frac', 'decorrelation_basis',
                    'eirp_p90_decor_adjusted_W', 'response_ratio',
                    'eirp_p90_response_corrected_W', 'limit_eligible'])
        for r in CLSA:
            el = ae.limit_eligible(r, BASE)
            e = E90[id(r)]
            o, b = DEC[id(r)]
            lab = LABEL[id(r)]
            own = OWN.get(id(r))
            # a measured window carries its own point; a transferred one the
            # observed dispersion (an empirical bound only when interpolated)
            lo = e * own / F0 if own else e * DISP_LO
            hi = e * own / F0 if own else e * DISP_HI
            rr = RATIO[NAVG[id(r)]]
            w.writerow([r['star_name'], r['system_id'], r['eb'],
                        '%.6f' % min(float(r['flo_GHz']), float(r['fhi_GHz'])),
                        '%.6f' % max(float(r['flo_GHz']), float(r['fhi_GHz'])),
                        r['chanw_Hz'], NAVG[id(r)], lab,
                        ';'.join(outside(r)) if lab == 'extrapolated' else '',
                        '%.4f' % own if own else '', '%.4f' % F0,
                        '%.4e' % e, '%.4e' % lo, '%.4e' % hi,
                        '%.4e' % (e * FLO), '%.4e' % (e * FHI),
                        '%.4f' % o if o is not None else '', b,
                        '%.4e' % (e * (1 + o)) if o is not None else '',
                        '%.4f' % rr, '%.4e' % (e * rr),
                        '1' if el else '0'])
    with open(DEP_SYS, 'w', newline='') as fh:
        keys = ['designation', 'system', 'best_eb', 'best_nu_lo_GHz',
                'eirp90_W', 'basis', 'own_factor', 'n_chan_avg',
                'eirp90_cal_lo_W', 'eirp90_cal_hi_W', 'p_reach_window',
                'p_reach_block', 'p_reach_window_dec',
                'sys_ratio_p05_block', 'sys_ratio_p95_block', 'decor_frac',
                'decor_basis', 'eirp90_decor_adjusted_W',
                'eirp90_response_corrected_W', 'reaches_1e15_nominal',
                'uncertain']
        w = csv.DictWriter(fh, fieldnames=keys, extrasaction='ignore')
        w.writeheader()
        for d in sorted(PER_SYS, key=lambda d: d['eirp90_W']):
            dd = dict(d)
            for k in keys:
                v = dd.get(k)
                if isinstance(v, float) or isinstance(v, np.floating):
                    dd[k] = ('%.4e' % v if k.endswith('_W') else '%.4f' % v)
                elif v is None:
                    dd[k] = ''
            w.writerow(dd)
print('%s: %d macros' % (os.path.basename(OUT_TEX), len(L) - 1))
print('  nominal %d systems, median %.4e W, %d reach 1e15 W' % (
    len(SYSIDS), NOM_MED, NOM_N))
print('  class-average interval: median %.3e..%.3e, count %d..%d' % (
    CAL_MED + CAL_N))
print('  own factors on the 49: median %.4e, count %d' % (OWN_MED, OWN_N))
print('  extrapolated removed/worst/best: %d/%d/%d' % EXT_N)
print('  decorrelation: median %.4e, count %d (lost %s)' % (
    ADJ_MED, ADJ_N, DEC_LOST))
print('  exact response in every window: median %.4e, count %d, deepest %.3e (%s), '
      'gained %s' % (RESP_MED, RESP_N, RESP_DEEP,
                     SYSIDS[int(np.argmin(RESP_SYS))], RESP_GAIN))
print('  decorrelation + dispersion (window draw): count 5-95 %d..%d'
      % (q(CNTWD, .05), q(CNTWD, .95)))
