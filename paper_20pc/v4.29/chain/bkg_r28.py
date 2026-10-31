#!/usr/bin/env python3
r"""Round 2820 (renumbered by the merger: 2810 is rankpairs_r28.py) -> survey_numbers_round2820.tex, bkg_r28.json (deposit).

THE CHANCE EXPECTATION, TAKEN APART: WHERE IT COMES FROM, WHETHER IT HOLDS IN
EVERY KIND OF FIELD, AND WHETHER THE STAR-TO-CONTROL EXCESS BELOW THE TRIGGER
LIVES AT THE PHASE CENTRE.

Nothing here is a new statistic.  Every number is a SUBSET of the comparison
`chance_v414.py` already makes -- its own per-window factors
(`chance_perwin_v422.json`), its own observed set, its own sub-trigger band --
read on a partition of the same windows.  The generator first reproduces the
whole-census values from those inputs (A1-A4) and only then splits them.

  1. CONCENTRATION.  The expectation is a sum of window rates.  How much of it
     the top N windows carry, and what the comparison gives with them removed
     from BOTH sides (a window removed from the expectation takes its own
     crossing, if it has one, out of the count).
  2. CONFIGURATION.  The same comparison inside each band, array, channel-width
     class and field type: observed against expected, and the probability of a
     count at least / at most as extreme under the same block-resampled
     predictive distribution the paper uses.
  3. BLOCK DEPENDENCE.  (a) the expectation's scatter when execution blocks are
     resampled against when windows are; (b) the COUNT's own dispersion under a
     pseudo-star drawn from the control positions, one position index per
     block (the 512 positions are drawn from one seed and sit at the same
     angle and nearly the same radius in every window of a block, so index k
     is one sky position across a block's windows, as the star is) against one
     index per window.  If windows of one block were correlated beyond what
     their rates carry, the first would be over-dispersed.
  4. THE PHASE-CENTRE SPLIT (referee M5).  Windows whose star lies within one
     synthesised beam of the phase centre (catalogue `pb_offset_arcsec`
     against the archive's own synthesised beam for the block, the convention
     `ctrlsep_v400.py` uses) and windows beyond it: the stellar-to-control
     ratio in \CeNearBandLo <= T < \CeNearBandHi with its block-resampled
     interval, and unattributed crossings against expectation, for each.

    python3 -I -B bkg_r28.py [--drive N]

--drive N breaks one assertion and writes only *_driveN.* (never a production
path); --drive 0 perturbs nothing but also writes only *_drive0.*.
  1: the per-window factors are read one row out of step     -> A1, A2b
  2: one observed crossing is dropped                        -> A3, A6
  3: the band is read from the wrong ladder edge             -> A4
  4: one window is lost from the phase-centre partition      -> A5, A8
  5: the coherent pseudo-star draws one index per WINDOW     -> A7
  6: the off-centre stars lose their sub-trigger events      -> A9 (and A4)
  7: the two arrays' labels are exchanged                    -> A10
  8: one window is given fifty times its rate                -> A11
A9-A11 are the PREMISES of the sentences the paper prints from these macros
(the excess is not confined to on-centre windows; it is carried by the 7 m
array and absent on the 12 m array; the expectation is not carried by a few
fields).  When a regeneration -- the v4.29 re-flag fold -- turns a premise
false the build stops, and the sentence is rewritten, not the check.
"""
import collections
import csv
import json
import math
import os
import sys

import numpy as np
from scipy.special import gammainc

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import posjoin_r27 as PJ                                         # noqa: E402
import star_alias as sa                                          # noqa: E402

ROUND = 2820
TRIG = 5.0
SEED = 2810
NBOOT = 40000
NPSEUDO = 40000
COV_LOQ, COV_HIQ = 2.5, 97.5
TOPN = (1, 5, 10, 20)
DROP = (5, 10)

DRIVE = None
for _i, _a in enumerate(sys.argv):
    if _a == '--drive':
        DRIVE = int(sys.argv[_i + 1])
SUFFIX = '' if DRIVE is None else '_drive%d' % DRIVE
OUT_TEX = os.path.join(HERE, 'numbers/survey_numbers_round2820.tex' if not SUFFIX
                       else 'numbers/survey_numbers_round2820%s.tex' % SUFFIX)
OUT_JSON = os.path.join(HERE, 'bkg_r28%s.json' % SUFFIX)

OUT, fail = [], []


def m(name, val):
    assert name.isalpha(), 'a macro name may contain letters only: %r' % name
    assert not any(x.startswith('\\newcommand{\\%s}' % name) for x in OUT), name
    OUT.append('\\newcommand{\\%s}{%s}' % (name, val))


def ck(label, cond, detail=''):
    print('  %-70s %s  %s' % (label[:70], 'PASS' if cond else 'FAIL', detail))
    if not cond:
        fail.append(label)


def p_ge(k, lam):
    lam = np.asarray(lam, float)
    return np.ones_like(lam) if k <= 0 else gammainc(k, lam)


def p_le(k, lam):
    return 1.0 - p_ge(k + 1, lam)


# =====================================================================
# inputs: the catalogue and chance_v414's own outputs
# =====================================================================
CAT = list(csv.DictReader(open(os.path.join(HERE, 'per_target_results_v3.99.csv'))))
META = json.load(open(os.path.join(HERE, 'archive_meta_v381.json')))['ebs']
CH = json.load(open(os.path.join(HERE, 'chance_v414.json')))
PW = json.load(open(os.path.join(HERE, 'chance_perwin_v422.json')))
LROWS = json.load(open(os.path.join(HERE, 'ledger.json')))['rows']
CELLS = json.load(open(os.path.join(
    HERE, 'r15inputs/cells/cells_extract_result.json')))['windows']
EXP = json.load(open(os.path.join(HERE, 'corrected_export_v399.json')))['rows']
FFX = json.load(open(os.path.join(HERE, 'r8inputs/v409/fieldfix_v409.json')))
COVER = json.load(open(os.path.join(HERE, 'r27inputs/fieldcover_r27.json')))


def macro_from(fn, name):
    pre = '\\newcommand{\\%s}{' % name
    for ln in open(os.path.join(HERE, 'numbers', fn), errors='ignore'):
        if ln.startswith(pre):
            return ln.strip()[len(pre):-1]
    raise AssertionError('%s does not publish \\%s' % (fn, name))

IA = [i for i, r in enumerate(CAT) if r['search_class'] == 'A']


def beam(i):
    """The block's synthesised beam as the archive records it (the
    convention ctrlsep_v400.py uses)."""
    return float(META[CAT[i]['eb']]['s_resolution_arcsec'])


def off(i):
    """The star's offset from the phase centre, as the catalogue gives it."""
    return float(CAT[i]['pb_offset_arcsec'])


ON = [i for i in IA if off(i) <= beam(i)]
OFF = [i for i in IA if off(i) > beam(i)]
_OFFSET = set(OFF)
ARR = {i: META[CAT[i]['eb']]['array'] for i in IA}
if DRIVE == 7:
    ARR = {i: ('7m' if a == '12m' else '12m') for i, a in ARR.items()}
ROWS = PW['rows']
if DRIVE == 1:
    ROWS = ROWS[1:] + ROWS[:1]
# A1: chance_v414 writes its per-window factors in catalogue Class A order;
# the row's own (block, rms, statistic) must match the catalogue row it is
# read against, or the factors belong to another window.
_al = [(CAT[i]['eb'], round(float(CAT[i]['rms_mJy']), 5),
        round(float(CAT[i]['star_snr']), 4)) == (w['eb'], w['rms_mJy'], w['star_snr'])
       for i, w in zip(IA, ROWS)]
ck('A1 per-window factors align with the catalogue rows, one for one',
   len(ROWS) == len(IA) and all(_al), '%d of %d aligned' % (sum(_al), len(IA)))
E = {}
NC = {}
RET = {}          # the window's own retained exceedances: (all, in the mask)
for i, w in zip(IA, ROWS):
    if w['n_ctrl_trig'] is None:
        continue
    NC[i] = (w['n_ctrl'], w['n_ctrl_trig'], w['mask_attr_share'],
             w['telluric_factor'])
    if w.get('n_ret_exc') is not None:
        RET[i] = (w['n_ret_exc'], w['n_ret_exc_attr'])
    E[i] = (w['n_ctrl_trig'] / float(w['n_ctrl'])
            * (1.0 - w['mask_attr_share']) * w['telluric_factor'])
E_ALL = sum(E.values())
ck('A2 the per-window expectations sum to the published one',
   abs(E_ALL - CH['e_chance']) < 1e-9, '%.6f against %.6f' % (E_ALL, CH['e_chance']))
A_CEN = (sum(a for _, a in RET.values()) / float(sum(n for n, _ in RET.values())))
ck('A2c the retained exceedances reproduce the census attributed share',
   len(RET) > 0 and all(abs(NC[i][2] - A_CEN) < 1e-12 for i in RET)
   and CH['telluric']['ctrl_exceedances'] == sum(n for n, _ in RET.values())
   and CH['telluric']['ctrl_in_mask'] == sum(a for _, a in RET.values()),
   '%d windows, share %.5f' % (len(RET), A_CEN))


# --------------------------------------------------- the whole-beam vectors
# the same positional join chance_v414 makes, so that the pseudo-star in (3)
# reads the very ensembles the expectation is built from; validated window by
# window against the deposited exceedance counts.
def wkey(eb, a, b):
    a, b = float(a), float(b)
    return (eb, round(min(a, b), 3), round(max(a, b), 3))


BYWIN, FFWIN = collections.defaultdict(list), collections.defaultdict(list)
for r in EXP:
    BYWIN[wkey(r['eb'], r['flo'], r['fhi'])].append(r)
for r in FFX:
    FFWIN[wkey(r['eb'], r['flo'], r['fhi'])].append(r)
VEC = {}
for i in IA:
    r = CAT[i]
    k = wkey(r['eb'], r['flo_GHz'], r['fhi_GHz'])
    q = PJ.pick_rep(FFWIN[k], r, HERE) if FFWIN.get(k) else None
    if q is not None and q.get('ctrl_all'):
        VEC[i], src = np.asarray(q['ctrl_all'], float), 'rep'
        continue
    p = PJ.pick_exp(BYWIN[k], r) if BYWIN.get(k) else None
    if p is not None and p.get('ctrl_all'):
        VEC[i] = np.asarray(p['ctrl_all'], float)
REPAIRED = {i for i in IA if FFWIN.get(wkey(CAT[i]['eb'], CAT[i]['flo_GHz'],
                                             CAT[i]['fhi_GHz']))
            and i in VEC}
_vbad = [i for i in E if i not in VEC or VEC[i].size != NC[i][0]
         or int((VEC[i] >= TRIG).sum()) != NC[i][1]]
ck('A2b every whole-beam control vector reproduces its deposited exceedance count',
   not _vbad and set(VEC) >= set(E), '%d mismatches over %d windows' % (len(_vbad), len(E)))

# --------------------------------------------------- the observed side
# chance_v414's own set: unattributed (the ledger's adopted disposition), not
# atmospheric (its published list of the ones the screen removed), in a
# released Class A window.  A3 requires its count.
WINSPAN = collections.defaultdict(list)
for i, r in enumerate(CAT):
    lo, hi = float(r['flo_GHz']), float(r['fhi_GHz'])
    WINSPAN[r['eb']].append((min(lo, hi), max(lo, hi), i))


def window_of(eb, f):
    hit = [i for lo, hi, i in WINSPAN.get(eb, []) if lo - 1e-6 <= f <= hi + 1e-6]
    return hit[0] if hit else None


_tl = {(x['eb'], round(x['f_topo'], 6)) for x in CH['telluric']['observed_removed']}
OBSWIN = collections.Counter()
for r in LROWS:
    if r['attributed'] or (r['eb'], round(r['freq'], 6)) in _tl:
        continue
    i = window_of(r['eb'], r['freq'])
    if i is not None and CAT[i]['search_class'] == 'A':
        OBSWIN[i] += 1
if DRIVE == 2:
    OBSWIN[next(iter(OBSWIN))] -= 1
N_OBS = sum(OBSWIN.values())
ck('A3 the observed set is chance_v414\'s: same count, every window in the expectation',
   N_OBS == CH['observed'] and all(i in E for i in OBSWIN if OBSWIN[i]),
   '%d against %d' % (N_OBS, CH['observed']))

# --------------------------------------------------- the sub-trigger ladder
# joined to the catalogue as chance_v414 joins it (block and edges, then the
# canonical star name, then the row whose statistic the profile reproduces)
CATKEY = collections.defaultdict(list)
for i in IA:
    CATKEY[wkey(CAT[i]['eb'], CAT[i]['flo_GHz'], CAT[i]['fhi_GHz'])].append(i)
LAD = {}
_LADCAT = {}     # id(cell window) -> catalogue row, for drive 6
for w in CELLS:
    if w['cls'] != 'A' or w['stratum'] == 'archival_tail':
        continue
    idx = CATKEY.get(wkey(w['eb'], w['lo'], w['hi']), [])
    same = [j for j in idx if sa.canon(CAT[j]['star_name']) == sa.canon(w['star'])]
    cand = same or idx
    if len(cand) > 1:
        cand = [min(cand, key=lambda j: abs(float(CAT[j]['star_snr']) - w['adopted']))]
    assert len(cand) == 1, w['key']
    LAD[cand[0]] = w
    _LADCAT[id(w)] = cand[0]
NLO, NHI = '%.2f' % CH['near_band'][0], '%.2f' % CH['near_band'][1]
if DRIVE == 3:
    NLO = '3.50'


def nband(w, side):
    k = '%s_out' % side
    if DRIVE == 6 and side == 'star' and _LADCAT.get(id(w)) in _OFFSET:
        return 0
    return w['ladder'][NLO][k] - w['ladder'][NHI][k]


rng = np.random.default_rng(SEED)


def near(ix):
    """(ratio, lo, hi, n_star_events, n_windows) over windows ix, the ratio
    chance_v414 publishes, with execution blocks resampled."""
    ws = [LAD[i] for i in ix if i in LAD]
    if not ws:
        return None
    s = sum(nband(w, 'star') for w in ws)
    c = sum(nband(w, 'ctrl') for w in ws)
    nc = sum(w['n_ctrl'] for w in ws)
    if not c:
        return None
    by = collections.defaultdict(list)
    for w in ws:
        by[w['eb']].append(w)
    ks = sorted(by)
    a = np.array([[sum(nband(w, 'star') for w in by[k]),
                   sum(nband(w, 'ctrl') for w in by[k]),
                   len(by[k]), sum(w['n_ctrl'] for w in by[k])] for k in ks], float)
    pk = rng.integers(0, len(ks), size=(NBOOT, len(ks)))
    sb = a[:, 0][pk].sum(1)
    cb = a[:, 1][pk].sum(1)
    with np.errstate(divide='ignore', invalid='ignore'):
        bt = (sb / a[:, 2][pk].sum(1)) / (cb / a[:, 3][pk].sum(1))
    bt = bt[np.isfinite(bt)]
    return ((s / float(len(ws))) / (c / float(nc)),
            float(np.percentile(bt, COV_LOQ)), float(np.percentile(bt, COV_HIQ)),
            int(s), len(ws), len(ks))


NEAR_ALL = near(IA)
ck('A4 the sub-trigger ratio over the whole census is the published one',
   abs(NEAR_ALL[0] - CH['near_ratio']) < 1e-12 and NEAR_ALL[4] == CH['near_n_windows']
   and abs(NEAR_ALL[1] - CH['near_interval'][0]) < 0.01
   and abs(NEAR_ALL[2] - CH['near_interval'][1]) < 0.01,
   '%.4f (%.3f-%.3f) against %.4f (%.3f-%.3f)'
   % (NEAR_ALL[0], NEAR_ALL[1], NEAR_ALL[2], CH['near_ratio'],
      CH['near_interval'][0], CH['near_interval'][1]))


# =====================================================================
# the comparison on any subset of windows: chance_v414's construction
# =====================================================================
def compare(ix):
    """Observed against expected over windows ix, with the predictive
    distribution chance_v414 uses: execution blocks resampled, each window's
    control fraction redrawn as a binomial on its own ensemble, the count
    Poisson about the resampled rate.

    ★ THE ATTRIBUTED SHARE IS MEASURED ON THE SUBSET IT IS APPLIED TO.  The
    census applies one pooled share (88 of 302) to every window with a
    retained profile.  Pooled over the census the sum is right, but the share
    is not uniform -- in a CO-bright field nearly every control maximum lands
    on the line -- so a subset carrying the census share is mis-allocated:
    the noisiest windows would keep 71 per cent of a rate that is almost all
    attributed.  Each subset therefore carries the share its own retained
    exceedances give, resampled with the same blocks as its rates.  Over the
    whole census this is the published construction (A6)."""
    ix = [i for i in ix if i in E]
    by = collections.defaultdict(list)
    for i in ix:
        by[CAT[i]['eb']].append(i)
    ks = sorted(by)
    nw = np.array([len(by[k]) for k in ks], float)
    _n = sum(RET[i][0] for i in ix if i in RET)
    a_sub = (sum(RET[i][1] for i in ix if i in RET) / float(_n)) if _n else A_CEN
    bj = np.zeros((len(ks), 64))     # windows with a retained profile, before the share
    bf = np.zeros((len(ks), 64))     # the rest, at their own grid share
    ra = np.array([[sum(RET[i][1] for i in by[k] if i in RET),
                    sum(RET[i][0] for i in by[k] if i in RET)] for k in ks], float)
    e = 0.0
    for j, k in enumerate(ks):
        for i in by[k]:
            n, t, s, tl = NC[i]
            d = rng.binomial(n, t / float(n), 64) / float(n) * tl
            if i in RET:
                bj[j] += d
                e += t / float(n) * (1 - a_sub) * tl
            else:
                bf[j] += d * (1 - s)
                e += E[i]
    pk = rng.integers(0, len(ks), size=(NBOOT, len(ks)))
    rl = rng.integers(0, 64, size=(NBOOT, len(ks)))
    den = ra[:, 1][pk].sum(1)
    with np.errstate(divide='ignore', invalid='ignore'):
        ab = np.where(den > 0, ra[:, 0][pk].sum(1) / den, a_sub)
    lam = ((bj[pk, rl].sum(1) * (1 - ab) + bf[pk, rl].sum(1))
           / nw[pk].sum(1) * len(ix))
    o = sum(OBSWIN[i] for i in ix)
    return dict(n_win=len(ix), n_blk=len(ks), exp=e, obs=o, share=a_sub,
                n_ret_exc=_n, exp_census_share=sum(E[i] for i in ix),
                p_ge=float(p_ge(o, lam).mean()), p_le=float(p_le(o, lam).mean()),
                lam_sd=float(lam.std()))


ALL = compare(IA)
ck('A6 the subset machinery reproduces the published whole-census expectation and probability',
   abs(ALL['exp'] - E_ALL) < 1e-9
   and abs(ALL['p_ge'] - CH['p_at_least_observed_control_only']) < 0.02,
   '%.4f against %.4f' % (ALL['p_ge'], CH['p_at_least_observed_control_only']))

# =====================================================================
# 1. concentration
# =====================================================================
# ranked by how often the window's control positions trigger -- the "noisy
# field" of the referee's question -- and not by the census-share product,
# which would rank by an allocation this generator shows is not uniform
RATE = {i: NC[i][1] / float(NC[i][0]) for i in E}
ORDER = sorted(E, key=lambda i: (-RATE[i], i))
_EW = dict(E)
if DRIVE == 8:
    _EW[ORDER[0]] *= 50.0
    ORDER = sorted(_EW, key=lambda i: -_EW[i])
CUM = np.cumsum([_EW[i] for i in ORDER]) / sum(_EW.values())
SHARE = {n: float(CUM[n - 1]) for n in TOPN}
N_HALF = int(np.searchsorted(CUM, 0.5) + 1)
TOP = [dict(star=CAT[i]['star_name'], eb=CAT[i]['eb'], band=CAT[i]['band'],
            f_lo=CAT[i]['flo_GHz'], e=E[i], obs=OBSWIN[i],
            ctrl_trig=NC[i][1], n_ctrl=NC[i][0]) for i in ORDER[:20]]
DROPPED = {n: compare([i for i in IA if i not in set(ORDER[:n])]) for n in DROP}
# and by execution block, since a structured field is a block property
BLKE = collections.Counter()
for i in E:
    BLKE[CAT[i]['eb']] += E[i]
BORDER = [b for b, _ in BLKE.most_common()]
BSHARE5 = sum(BLKE[b] for b in BORDER[:5]) / E_ALL
DROPBLK5 = compare([i for i in IA if CAT[i]['eb'] not in set(BORDER[:5])])

# =====================================================================
# 2. configurations
# =====================================================================
def chanclass(i):
    cw = float(CAT[i]['chanw_Hz'])
    return ('<=244 kHz' if cw < 3e5 else '488 kHz' if cw < 6e5 else '>=977 kHz')


SPLITS = collections.OrderedDict()
SPLITS['band'] = lambda i: ('Band %s' % CAT[i]['band']
                            if CAT[i]['band'] in ('6', '7') else 'Bands 3/8/10')
SPLITS['array'] = lambda i: ARR[i]
SPLITS['channel width'] = chanclass
SPLITS['field'] = lambda i: ('recombined multi-field' if i in REPAIRED
                             else 'single field')
SPLITS['line content'] = lambda i: ('overlaps the line mask'
                                    if float(CAT[i]['unmasked_fraction']) < 1.0
                                    else 'line-free')
CONF = collections.OrderedDict()
for name, f in SPLITS.items():
    g = collections.defaultdict(list)
    for i in IA:
        g[f(i)].append(i)
    CONF[name] = collections.OrderedDict(
        (k, dict(compare(v), near=near(v))) for k, v in sorted(g.items()))
_cells = [c for d in CONF.values() for c in d.values()]
N_CONF = len(_cells)
N_CONF_IN = sum(1 for c in _cells if c['p_ge'] > COV_LOQ / 100.0
                and c['p_le'] > (100.0 - COV_HIQ) / 100.0)
_pmin = min(min(c['p_ge'], c['p_le']) for c in _cells)

# =====================================================================
# 3. block dependence
# =====================================================================
_by = collections.defaultdict(list)
for i in E:
    _by[CAT[i]['eb']].append(i)
_ks = sorted(_by)
_be = np.array([sum(E[i] for i in _by[k]) for k in _ks])
_bn = np.array([len(_by[k]) for k in _ks], float)
_pk = rng.integers(0, len(_ks), size=(NBOOT, len(_ks)))
SD_BLOCK = float((_be[_pk].sum(1) / _bn[_pk].sum(1) * len(E)).std())
_we = np.array([E[i] for i in E])
_pw = rng.integers(0, len(_we), size=(NBOOT, len(_we)))
SD_WIN = float((_we[_pw].sum(1)).std())

# (b) the count's own dispersion: a pseudo-star at one control position
_ix = sorted(E)
_keep = np.array([(1 - NC[i][2]) * NC[i][3] for i in _ix])
_blk = np.array([_ks.index(CAT[i]['eb']) for i in _ix])
_n = np.array([VEC[i].size for i in _ix])
_nmin = int(_n.min())


def pseudo(coherent):
    tot = np.zeros(NPSEUDO)
    if coherent and DRIVE != 5:
        kb = rng.integers(0, _nmin, size=(NPSEUDO, len(_ks)))
        kidx = kb[:, _blk]
    else:
        kidx = rng.integers(0, _nmin, size=(NPSEUDO, len(_ix)))
    for j, i in enumerate(_ix):
        hit = VEC[i][kidx[:, j]] >= TRIG
        tot += hit & (rng.random(NPSEUDO) < _keep[j])
    return tot, kidx


(PS_COH, _KCOH), (PS_IND, _) = pseudo(True), pseudo(False)
DISP = float(PS_COH.var() / PS_IND.var())
P_PSEUDO = float((PS_COH >= N_OBS).mean())
# the drive must make the two draws the same construction, so A7 is a check
# that the coherent draw really is coherent: on the real data the windows of
# one block share a position index, and their exceedances are compared.
_same = [(a, b) for k in _ks for a in _by[k] for b in _by[k] if a < b]
_kk = rng.integers(0, _nmin, 4000)
_co = np.mean([np.mean((VEC[a][_kk] >= TRIG) & (VEC[b][_kk] >= TRIG))
               for a, b in _same]) if _same else 0.0
_multi = [(a, b) for a in range(len(_ix)) for b in range(a + 1, len(_ix))
          if _blk[a] == _blk[b]]
ck('A7 the coherent pseudo-star is coherent: every window of a block reads the '
   'same control position in every draw',
   _multi and all(np.array_equal(_KCOH[:, a], _KCOH[:, b]) for a, b in _multi),
   '%d same-block window pairs, %d blocks, %d windows'
   % (len(_multi), len(_ks), len(_ix)))

# =====================================================================
# 4. the phase-centre split (M5)
# =====================================================================
if DRIVE == 4:
    OFF = OFF[1:]
ck('A5 the phase-centre split is a partition of the census',
   len(ON) + len(OFF) == len(IA) and not set(ON) & set(OFF),
   '%d + %d against %d' % (len(ON), len(OFF), len(IA)))
SPLIT = collections.OrderedDict()
for nm, ix in (('on', ON), ('off', OFF)):
    c = compare(ix)
    c['near'] = near(ix)
    c['stars'] = sorted({CAT[i]['star_name'] for i in ix})
    c['n_stars'] = len(c['stars'])
    c['offset_beams_median'] = float(np.median([off(i) / beam(i) for i in ix]))
    SPLIT[nm] = c
# the off-centre side without its dominant star, as a description of what the
# subset is (not a further test): which star carries it
_offstar = collections.Counter(CAT[i]['star_name'] for i in OFF)
OFF_TOPSTAR, OFF_TOPN = _offstar.most_common(1)[0]
# the beam convention: the archive's largest beam for the block instead
ON_MAX = [i for i in IA if off(i) <= float(
    META[CAT[i]['eb']].get('s_resolution_max_arcsec')
    or META[CAT[i]['eb']]['s_resolution_arcsec'])]
SPLIT_MAXBEAM = dict(on=dict(compare(ON_MAX), near=near(ON_MAX)),
                     off=dict(compare([i for i in IA if i not in set(ON_MAX)]),
                              near=near([i for i in IA if i not in set(ON_MAX)])))
_on, _off = SPLIT['on']['near'], SPLIT['off']['near']
# the verdict, stated from the intervals: the excess is confined to on-centre
# windows only if the off-centre ratio is consistent with 1 AND below the
# on-centre one beyond the on-centre interval.
CONFINED = (_off[1] <= 1.0 and _off[0] < _on[1] and _on[1] > 1.0
            and _off[0] < 1.0)
_alma = macro_from('survey_numbers_round340.tex', 'BkAlmaName').replace('$', '')
ck('A9 PREMISE of "not confined to on-centre windows": the off-centre ratio is '
   'not below the on-centre interval, and the dominant off-centre star is the '
   'one the text names',
   not CONFINED and _off[2] >= _on[1] and sa.canon(OFF_TOPSTAR) == sa.canon(_alma),
   'on %.3f (%.3f-%.3f), off %.3f (%.3f-%.3f); %s'
   % (_on[0], _on[1], _on[2], _off[0], _off[1], _off[2], OFF_TOPSTAR))
_a12, _a7 = CONF['array']['12m']['near'], CONF['array']['7m']['near']
ck('A10 PREMISE of "carried by the 7 m array": its interval excludes 1 and the '
   '12 m interval contains 1',
   _a7[1] > 1.0 and _a12[1] <= 1.0 <= _a12[2],
   '7 m %.3f (%.3f-%.3f), 12 m %.3f (%.3f-%.3f)' % (_a7[:3] + _a12[:3]))
ck('A11 PREMISE of "not carried by a few fields": the ten largest windows carry '
   'under a third of it, and without them the count stays inside its central '
   'interval',
   SHARE[10] < 1.0 / 3 and DROPPED[10]['p_ge'] > COV_LOQ / 100.0
   and DROPPED[10]['p_le'] > (100.0 - COV_HIQ) / 100.0,
   'share %.3f, P>= %.3f' % (SHARE[10], DROPPED[10]['p_ge']))
# the stellar transfer calibrated per array instead of census-wide
E_ARRCAL = sum(CONF['array'][a]['exp_census_share'] * CONF['array'][a]['near'][0]
               for a in CONF['array'])

# =====================================================================
# macros (only those the text cites) and the deposit record
# =====================================================================
fmt = lambda x: '%.1f' % x
m('BgTopNWord', {10: 'ten'}[DROP[1]])
m('BgDropTenNWin', '%d' % DROPPED[10]['n_win'])
m('BgDropTenExp', fmt(DROPPED[10]['exp']))
m('BgDropTenObs', '%d' % DROPPED[10]['obs'])
m('BgDropTenP', '%.2f' % DROPPED[10]['p_ge'])
m('BgNConf', '%d' % N_CONF)
m('BgNConfIn', '%d' % N_CONF_IN)
m('BgBlockSdRatio', '%.2f' % (SD_BLOCK / SD_WIN))
m('BgDisp', '%.2f' % DISP)
m('BgPseudoP', '%.2f' % P_PSEUDO)
for nm, tag in (('on', 'On'), ('off', 'Off')):
    c = SPLIT[nm]
    m('BgPc%sNWin' % tag, '%d' % c['n_win'])
    m('BgPc%sNStar' % tag, '%d' % c['n_stars'])
    m('BgPc%sRatio' % tag, '%.2f' % c['near'][0])
    m('BgPc%sRatioLo' % tag, '%.2f' % c['near'][1])
    m('BgPc%sRatioHi' % tag, '%.2f' % c['near'][2])
    m('BgPc%sObs' % tag, '%d' % c['obs'])
    m('BgPc%sExp' % tag, fmt(c['exp']))
    m('BgPc%sP' % tag, '%.2f' % c['p_ge'])
m('BgPcOffTopN', '%d' % OFF_TOPN)
m('BgPcOffMedBeams', '%.1f' % SPLIT['off']['offset_beams_median'])
for a, tag in (('7m', 'Seven'), ('12m', 'Twelve')):
    _c = CONF['array'][a]
    m('BgArr%sRatio' % tag, '%.2f' % _c['near'][0])
    m('BgArr%sRatioLo' % tag, '%.2f' % _c['near'][1])
    m('BgArr%sRatioHi' % tag, '%.2f' % _c['near'][2])
    m('BgArr%sObs' % tag, '%d' % _c['obs'])
    m('BgArr%sExp' % tag, fmt(_c['exp']))
m('BgFieldMinResp', '%g' % float(COVER['min_pb_resp']))

ck('A8 the subsets close: on + off windows and counts equal the census, and at '
   'the census share so do their expectations',
   abs(SPLIT['on']['exp_census_share'] + SPLIT['off']['exp_census_share'] - E_ALL) < 1e-9
   and SPLIT['on']['obs'] + SPLIT['off']['obs'] == N_OBS
   and SPLIT['on']['n_win'] + SPLIT['off']['n_win'] == len(E)
   and all(abs(sum(c['exp_census_share'] for c in d.values()) - E_ALL) < 1e-9
           and sum(c['obs'] for c in d.values()) == N_OBS
           for d in CONF.values()), '')
# the census-wide expectation with every window carrying its OWN measured
# share (where it has retained exceedances) -- a check on the pooling itself
E_OWN = sum((NC[i][1] / float(NC[i][0]) * (1 - (RET[i][1] / float(RET[i][0])
                                                 if i in RET and RET[i][0] else NC[i][2]))
             * NC[i][3]) for i in E)
print('census expectation with each window at its own retained share: %.2f '
      '(pooled %.2f)' % (E_OWN, E_ALL))

print('\nconcentration: top-N shares %s, half in %d windows; top-5 blocks %.3f'
      % ({k: round(v, 3) for k, v in SHARE.items()}, N_HALF, BSHARE5))
for n, c in DROPPED.items():
    print('  drop top %d windows: %d obs vs %.2f exp [census share %.2f], share %.3f, P(>=)=%.3f'
          % (n, c['obs'], c['exp'], c['exp_census_share'], c['share'], c['p_ge']))
print('  drop top 5 blocks: %d obs vs %.2f exp, P(>=)=%.3f' % (DROPBLK5['obs'], DROPBLK5['exp'], DROPBLK5['p_ge']))
print('configurations (%d of %d inside the central %g%%; smallest tail %.3f):'
      % (N_CONF_IN, N_CONF, COV_HIQ - COV_LOQ, _pmin))
for name, d in CONF.items():
    for k, c in d.items():
        nr = c['near']
        print('  %-14s %-24s win %3d blk %3d  obs %2d exp %5.2f [%5.2f] share %.2f/%3d  P>= %.3f P<= %.3f  near %s'
              % (name, k, c['n_win'], c['n_blk'], c['obs'], c['exp'], c['exp_census_share'], c['share'], c['n_ret_exc'], c['p_ge'], c['p_le'],
                 'n/a' if nr is None else '%.3f (%.3f-%.3f) n*=%d' % nr[:4]))
print('block dependence: sd(block) %.3f sd(window) %.3f ratio %.2f; count dispersion '
      'coherent/independent %.3f (var %.2f / %.2f, mean %.2f); P_pseudo(>=%d) %.3f; '
      'P published %.3f; P point-Poisson %.3f; same-block joint exceedance %.4f'
      % (SD_BLOCK, SD_WIN, SD_BLOCK / SD_WIN, DISP, PS_COH.var(), PS_IND.var(),
         PS_COH.mean(), N_OBS, P_PSEUDO, CH['p_at_least_observed_control_only'],
         CH['p_at_least_observed_control_only_point'], _co))
for nm, c in SPLIT.items():
    print('phase centre %-3s: win %d blk %d stars %d  near %.3f (%.3f-%.3f) n*=%d  obs %d exp %.2f '
          'P>= %.3f P<= %.3f  median offset %.2f beams'
          % (nm, c['n_win'], c['n_blk'], c['n_stars'], c['near'][0], c['near'][1],
             c['near'][2], c['near'][3], c['obs'], c['exp'], c['p_ge'], c['p_le'],
             c['offset_beams_median']))
print('  off-centre dominated by %s (%d of %d windows); confined to on-centre: %s'
      % (OFF_TOPSTAR, OFF_TOPN, len(OFF), CONFINED))
print('transfer calibrated per array: %.2f (census-wide %s)' % (E_ARRCAL, CH['near_expectation']))
for nm, c in SPLIT_MAXBEAM.items():
    print('  [largest archive beam] %-3s win %d obs %d exp %.2f near %s'
          % (nm, c['n_win'], c['obs'], c['exp'],
             'n/a' if c['near'] is None else '%.3f (%.3f-%.3f)' % c['near'][:3]))

if fail:
    print('\nFAILED: %s' % '; '.join(fail))
    if DRIVE is None:
        raise SystemExit(1)

with open(OUT_TEX, 'w') as fh:
    fh.write('\n'.join(['%% GENERATED by bkg_r28.py (round %d) -- do not hand-edit.' % ROUND,
                        '%% The chance expectation taken apart: concentration, configuration,',
                        '%% block dependence, and the phase-centre split.'] + sorted(OUT)) + '\n')
json.dump(dict(round=ROUND, drive=DRIVE, seed=SEED, n_boot=NBOOT, n_pseudo=NPSEUDO,
               e_chance=E_ALL, observed=N_OBS, whole=ALL,
               top_share=SHARE, n_half=N_HALF, top20=TOP,
               drop_top_windows={str(k): v for k, v in DROPPED.items()},
               top5_block_share=BSHARE5, drop_top5_blocks=DROPBLK5,
               configurations=CONF, n_conf=N_CONF, n_conf_inside=N_CONF_IN,
               smallest_tail=_pmin,
               block_sd=SD_BLOCK, window_sd=SD_WIN,
               count_dispersion_coherent_over_independent=DISP,
               pseudo_star_p_at_least=P_PSEUDO,
               same_block_joint_exceedance=float(_co),
               near_whole=NEAR_ALL,
               e_chance_own_window_share=E_OWN,
               e_chance_transfer_per_array=E_ARRCAL,
               field_min_pb_resp=COVER['min_pb_resp'],
               phase_centre=dict(beam='archive s_resolution_arcsec of the block',
                                 offset='catalogue pb_offset_arcsec', split=SPLIT,
                                 largest_beam=SPLIT_MAXBEAM,
                                 off_dominant_star=[OFF_TOPSTAR, OFF_TOPN],
                                 excess_confined_on_centre=CONFINED)),
          open(OUT_JSON, 'w'), indent=1, sort_keys=True, default=float)
print('\nwrote %s (%d macros) and %s' % (os.path.basename(OUT_TEX), len(OUT),
                                         os.path.basename(OUT_JSON)))
