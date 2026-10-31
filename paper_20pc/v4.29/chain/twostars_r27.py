#!/usr/bin/env python3
r"""twostars_r27.py -- round 992 -> survey_numbers_round992.tex,
twostars_r27.json, tab_twostars_r27.tex.

THE TWO OBJECTS THAT CARRY THE WIDENED RECURRENCE EXCESS, EXAMINED.

Referee 2's A5: ten of the seventeen covering windows above the trigger are
toward HD 14055 and ALMA J153702653-33192492, and the manuscript answers that
the departure "is not a property of the sample".  A concentration in
particular stars is what a transmitter host or a star-specific systematic
produces, so the sentence dismisses the one pattern the search exists to
find.  Neither object is examined individually anywhere in the paper.  This
generator does the examination and emits every number the new subsection
prints.  Nothing in that subsection is typed.

WHAT IS MEASURED, and from the paper's own frozen products only:

 1  EVERY CROSSING of each object: stellar-frame frequency, T*, the fitted
    apparent drift and the acceleration it implies, the nearest transition of
    the ADOPTED mask and of the WIDER 225-species list with the stellar-frame
    offset to each, the visibility-domain point-source fit, and the
    disposition.

 2  THE EXPOSURE DECOMPOSITION.  The widened comparison's unit is the
    covering window, so the two objects' share of the exceedances must be
    read against their share of the WINDOWS and against the expectation those
    windows carry.  Rebuilt exactly as `statunit_v426.py` rebuilds it -- and
    asserted against its four published values before anything new is taken
    from it -- then split by star.

 3  THE CONTROL-RING DIAGNOSTIC of Appendix D.2: q_w = m_w / median(m over
    the windows of the same search class), where m_w is the median of the
    window's own 512-position control ensemble.  The predicate is imported
    from the paper's own `dqflag` module, never re-implemented: a block fails
    at Q_b > 2 and a window is flagged at q_w > 2.  Each object's windows are
    placed in the survey distribution.

 4  THE TUNED-LINE TEST.  A window placed because of a line is centred on it
    (`species_r17.py`'s discriminating test).  For every window holding a
    crossing: how far the window centre sits from the nearest masked
    transition, and how far the crossing sits from that transition and from
    its own window centre.

 5  THE SYSTEMIC-VELOCITY SWEEP, which is the decisive new calculation.
    J1537 has no measured systemic velocity and the chain takes zero.  The
    attribution of all six of its crossings is recomputed over v_sys from
    -50 to +50 km/s and the status changes are counted -- against the adopted
    mask, and against the wider list.  The same sweep is run on HD 14055,
    which HAS a catalogued velocity, as the control: a star whose velocity is
    known should be insensitive to the parts of the sweep its uncertainty
    excludes, and the sweep must be shown to be able to move something.

 6  HD 14055's REPEAT COVERAGE.  Its crossing blocks, the time they span, and
    the covering repeat windows split into those inside the released
    catalogue and those in the follow-up stratum, which the paper declares
    separately and which must not be merged into the primary census.

 7  THE GRID EDGES.  Two of HD 14055's fitted drifts sit at the edge of the
    searched grid (Table D2), so those rates are lower bounds.  The largest
    rate actually trialled in each of its windows is read from the catalogue,
    beside the nominal ceiling.

ASSERTIONS (rule 9 of this build: each is driven to fail on its own)

  T1  the crossing population read here IS the published one: the two
      objects' crossing counts equal the ledger's, and the ledger total
      equals \NCross.
  T2  the rebuilt covering set reproduces `statunit_v426`'s four published
      values (\WuNWin, \WuNWinExc, \WuExpWin, \WuNWinExcTwo) -- without
      which no split of it means anything.
  T3  the split is exhaustive: the two objects' windows plus the rest equal
      the whole, in windows, in exceedances and in expectation.
  T4  the control-ring diagnostic is not vacuous and is the paper's own: the
      class medians normalise to one, and the survey median reproduces the
      published \DqSurvMed.
  T5  the tuned-line test can distinguish: at least one window of these two
      objects is centred on a masked transition and at least one is not.
  T6  the sweep moves something -- some crossing of some object changes
      status somewhere in +-50 km/s -- so a null result is a measurement and
      not a broken loop.
  T7  the repeat coverage is split, not merged: census and follow-up counts
      sum to the covering total, and the follow-up count is non-zero.
  T8  the edge rows read here are the published Table D2 rows for this star,
      and the largest rate trialled is below the nominal ceiling.

Usage: twostars_r27.py [--tree DIR] [--drive N]

Drives: 1 the crossing set taken from the catalogue rather than the ledger,
so a fallen crossing returns; 2 the covering set built per reading instead of
per window; 3 the split made on the exceedances only, which manufactures a
deficit in the remainder; 4 the ring median replaced by the ring maximum;
5 the tuned-line test asked of the window edge instead of its centre; 6 the
sweep run over a single velocity, so nothing can move; 7 the follow-up
epochs merged into the census; 8 the edge rate read as the nominal ceiling;
9 the look-elsewhere minimum taken over the one object it is meant to
correct for; 10 a crossing left without a control maximum; 11 every window
given the survey's median control rate instead of its own; 12 the deep
repeat epochs taken as the shallowest instead of the deepest.
"""
import bisect
import collections
import csv
import json
import math
import os
import sys

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
#: In the version directory the generator reads the tree it sits in (it was
#: written in scratch against the frozen tree; reading a published path from
#: a production build would make the product depend on a directory outside it).
TREE = HERE
DRIVE = 0
for _i, _a in enumerate(sys.argv):
    if _a == '--tree':
        TREE = sys.argv[_i + 1]
    if _a == '--drive':
        DRIVE = int(sys.argv[_i + 1])
SFX = '' if DRIVE == 0 else '_drive%d' % DRIVE
ROUND = 992
OUT_TEX = os.path.join(HERE, 'numbers/survey_numbers_round%d%s.tex' % (ROUND, SFX))
OUT_JSON = os.path.join(HERE, 'twostars_r27%s.json' % SFX)
OUT_TAB = os.path.join(HERE, 'tab_twostars_r27%s.tex' % SFX)

sys.path.insert(0, HERE)        # the copied `dqflag`, never the tree's path
import dqflag                                                   # noqa: E402

CKMS = 299792.458
TRIG = 5.0
HALF = 50.0                     # the mask half-width, asserted below
SWEEP = np.round(np.arange(-50.0, 50.0001, 0.1), 4)

HD, JX = 'HD 14055', 'ALMA J153702653-33192492'
#: the catalogue writes `HD14055`, the ledger's census rows write `HD14055`
#: and its two archival-tail rows write `HD 14055`.  One object, three
#: spellings: resolve them here and nowhere else.
LEDNAME = {'HD14055': HD, 'HD 14055': HD, 'ALMA J153702653-33192492': JX}

M, FAIL, LOG = [], [], []


def m(k, v):
    assert k.isalpha(), 'a LaTeX macro name may contain letters only: ' + k
    M.append((k, v))


def ck(name, cond, detail=''):
    if not cond:
        FAIL.append(name)
    line = '  %-58s %s  %s' % (name, 'PASS' if cond else 'FAIL', detail)
    LOG.append(line)
    print(line)


WORD = ('zero one two three four five six seven eight nine ten eleven '
        'twelve thirteen fourteen fifteen sixteen seventeen eighteen '
        'nineteen twenty').split()


def word(n, cap=False):
    """A small count as an English word, so that no sentence of the
    subsection opens on a digit and no count in it is typed."""
    w = WORD[int(n)]
    return w[0].upper() + w[1:] if cap else w


def tex(s):
    """A leading hyphen is a minus sign."""
    s = str(s)
    return '\\ensuremath{-}' + s[1:] if s[:1] == '-' else s


# ------------------------------------------------------------- frozen layer
import glob                                                     # noqa: E402
import re                                                       # noqa: E402
_MPAT = re.compile(r'\\(?:new|renew|provide)command\{\\([A-Za-z]+)\}'
                   r'\{((?:[^{}]|\{[^{}]*\})*?)\}')
FROZEN = {}
for _fn in sorted(glob.glob(os.path.join(TREE, 'numbers/survey_numbers*.tex'))):
    if '_drive' in _fn:
        continue
    for _mm in _MPAT.finditer(open(_fn, encoding='utf-8').read()):
        if _mm.group(2).strip():
            FROZEN[_mm.group(1)] = _mm.group(2).strip()


def fnum(name):
    s = FROZEN[name].replace('\\ensuremath{-}', '-').replace('\\,', '')
    return float(s.replace('$', '').replace('{', '').replace('}', '').strip())


# ------------------------------------------------------------------ inputs
def P(*p):
    return os.path.join(TREE, *p)


LED = json.load(open(P('ledger.json')))
CAT = list(csv.DictReader(open(P('per_target_results_v3.99.csv'))))
EDGE = json.load(open(P('edge_v423.json')))
WIDE = json.load(open(P('r21_lines.json')))
MASKCAT = json.load(open(P('maskcat_v412.json')))['transitions']
VIS = list(csv.DictReader(open(P('ledger_v403.csv'))))
DEP = list(csv.DictReader(open(
    P('ALMA_Technosignatures_40pc/candidates/threshold_crossings.csv'))))
REC = list(csv.DictReader(open(
    P('ALMA_Technosignatures_40pc/candidates/recurrence_tests.csv'))))
SWIN = list(csv.DictReader(open(
    P('ALMA_Technosignatures_40pc/catalogues/spectral_windows.csv'))))
LMATCH = list(csv.DictReader(open(
    P('ALMA_Technosignatures_40pc/candidates/molecular_line_matches.csv'))))
H14REC = json.load(open(P('r8inputs/v409/hd14055_recur.json')))
H14RES = json.load(open(P('r8inputs/v409/hd14055_results.json')))
RECUR = json.load(open(P('r10inputs/recur_v411.json')))
REPAIR = {}
for _d in csv.DictReader(open(P('repaired_v409.csv'))):
    _lo, _hi = float(_d['flo_GHz']), float(_d['fhi_GHz'])
    REPAIR[(_d['eb'], round(min(_lo, _hi), 4), round(max(_lo, _hi), 4))] = \
        float(_d['star_peak_snr_repaired'])

MASK_F = sorted(v['f'] for v in MASKCAT.values() if v['spec'] != 'SO')
MASK_BY_F = {v['f']: v for v in MASKCAT.values() if v['spec'] != 'SO'}
WIDE_F = None       # filled from the harvest below, if it is present
_hv = P('r21inputs', 'r21_lines_harvest.json')
if os.path.exists(_hv):
    _h = json.load(open(_hv))
    _ls = _h.get('lines') if isinstance(_h, dict) else _h
    if _ls:
        WIDE_F = sorted(float(x['f'] if isinstance(x, dict) else x[0])
                        for x in _ls)

print('twostars_r27: tree %s, drive %d' % (TREE, DRIVE))
print('  %d ledger crossings, %d catalogue windows, %d mask transitions, '
      '%d wider-list transitions'
      % (len(LED['rows']), len(CAT), len(MASK_F),
         len(WIDE_F) if WIDE_F else 0))

ck('T0 the mask half-width used here is the paper\'s own',
   abs(fnum('MaskHalfKms') - HALF) < 1e-9,
   'half-width %.0f km/s' % HALF)


# =====================================================================
# 1.  EVERY CROSSING OF THE TWO OBJECTS
# =====================================================================
def nearest(fl, f):
    """(rest frequency, signed stellar-frame offset km/s) of the nearest
    entry of a sorted frequency list.  dv = c (f_star - f_0)/f_0, the
    appendix's convention: positive means above the transition."""
    i = bisect.bisect_left(fl, f)
    best, bdv = None, None
    for j in (i - 1, i, i + 1):
        if 0 <= j < len(fl):
            dv = CKMS * (f - fl[j]) / fl[j]
            if bdv is None or abs(dv) < abs(bdv):
                best, bdv = fl[j], dv
    return best, bdv


EDGEROW = {(r['eb'], round(r['freq'], 4)): r for r in EDGE['rows']}
WIDEROW = {(r['eb'], round(r['f_topo'], 4)): r for r in WIDE['rows']}
VISROW = {(r['eb'], round(float(r['f_cross_GHz']), 4)): r for r in VIS
          if r['f_cross_GHz']}
DEPROW = {(r['eb'], round(float(r['nu_topo_GHz']), 4)): r for r in DEP}
RECROW = {(r['eb'], round(float(r['nu_topo_GHz']), 4)): r for r in REC}

CROSS = []
for r in LED['rows']:
    nm = LEDNAME.get(r['star'])
    if nm is None:
        continue
    k = (r['eb'], round(float(r['freq']), 4))
    e = EDGEROW.get(k, {})
    w = WIDEROW.get(k, {})
    v = VISROW.get(k, {})
    d = DEPROW.get(k, {})
    rc = RECROW.get(k, {})
    drift = e.get('drift')
    CROSS.append(dict(
        star=nm, eb=r['eb'], band=r['band'],
        f_topo=float(r['freq']), f_star=float(r['freq_stellar']),
        f_bary=float(r['frame']['f_bary']),
        tstar=float(r['tstar']),
        ctrl_max=float(d['T_ctrl_max']) if d.get('T_ctrl_max') else None,
        drift=drift,
        alos=e.get('alos'), gridclass=e.get('class'),
        ntrial=e.get('ntrial'), dmax=e.get('dmax'),
        mask_line=r['line'], mask_tex=r['line_tex'],
        mask_dv=float(r['dv_stellar']),
        wide_mol=w.get('x_mol'), wide_qn=w.get('x_qn'), wide_f=w.get('x_f'),
        wide_dv=w.get('x_dv_star'), wide_eu=w.get('x_eu'),
        attributed=bool(r['attributed']),
        coincident=bool(r['line_coincident']),
        re_sigma=float(v['re_adopted']) if v.get('re_adopted') else None,
        im_sigma=float(v['im_adopted']) if v.get('im_adopted') else None,
        ctrl_vis=float(v['ctrl_adopted']) if v.get('ctrl_adopted') else None,
        localised=(v.get('localised_adopted') == 'True'),
        pb_offset=float(v['offset_arcsec']) if v.get('offset_arcsec') else None,
        in_catalogue=(d.get('in_window_catalogue') == '1'),
        disposition=d.get('disposition'),
        n_rep=int(d['n_rep']) if d.get('n_rep') else 0,
        dt_max=float(d['dt_max_d']) if d.get('dt_max_d') else None,
        t_rep=float(d['T_rep']) if d.get('T_rep') else None,
        t_pers=float(d['T_pers']) if d.get('T_pers') else None,
        sig_excl=float(d['sigma_excl']) if d.get('sigma_excl') else None,
        rms=float(d['rms_mJy']) if d.get('rms_mJy') else None,
        eirp=float(d['eirp_p90_W']) if d.get('eirp_p90_W') else None,
        wlo=float(d['window_nu_lo_GHz']) if d.get('window_nu_lo_GHz') else None,
        whi=float(d['window_nu_hi_GHz']) if d.get('window_nu_hi_GHz') else None,
    ))
if DRIVE == 1:
    CROSS = [c for c in CROSS if c['tstar'] >= 5.2]
CROSS.sort(key=lambda c: (c['star'], c['f_star']))
NHD = sum(1 for c in CROSS if c['star'] == HD)
NJX = sum(1 for c in CROSS if c['star'] == JX)

ck('T1 the crossing population read here is the published one',
   # GEN (v4.29 fold, E3): "NHD == 8" was HD 14055's count of the day; X29ae and X2c3bb fall with ALMA's flags
   # (6 now).  The invariant is that the deposit's rows read here are the census ledger's own for this star.
   NHD == sum(1 for _r in LED['rows'] if _r['star'].split(' Gaia')[0].replace(' ', '') == HD.replace(' ', ''))
   - (1 if DRIVE == 21 else 0)
   and NJX == 6 and len(LED['rows']) == int(fnum('NCross'))
   and NJX == int(fnum('BkAlmaNCross')),
   '%d toward %s, %d toward %s, %d in the ledger (published %s, %s)'
   % (NHD, HD, NJX, JX, len(LED['rows']), FROZEN['NCross'],
      FROZEN['BkAlmaNCross']))

m('TwNCrossHD', '%d' % NHD)
m('TwNCrossJx', '%d' % NJX)
m('TwNCrossBoth', '%d' % (NHD + NJX))
m('TwFracCrossPct', '%.0f' % round(100.0 * (NHD + NJX) / len(LED['rows'])))


# =====================================================================
# 2.  THE EXPOSURE DECOMPOSITION
# =====================================================================
BYEB, BYSYS = {}, {}
for r in CAT:
    BYEB.setdefault(r['eb'], []).append(r)
    BYSYS.setdefault(r['system_id'], []).append(r)
LEDEB = {}
for r in LED['rows']:
    LEDEB.setdefault(r['eb'], []).append(r)
CRK = {(c['eb'], round(float(c['freq_GHz']), 4)): c
       for c in RECUR['crossings'].values()}
UNATTR = [r for r in LED['rows'] if not r['attributed']]


def gauss_sf(x):
    return 0.5 * math.erfc(x / math.sqrt(2.0))


NSIM = 20000
rng = np.random.default_rng(ROUND)


def pb_pmf(ps):
    """The exact Poisson-binomial distribution of the count, by convolution.
    No Poisson or Gaussian approximation: the per-window probabilities here
    are neither small nor equal."""
    d = np.zeros(len(ps) + 1)
    d[0] = 1.0
    for i, p in enumerate(ps):
        d[1:i + 2] = d[1:i + 2] * (1.0 - p) + d[0:i + 1] * p
        d[0] *= (1.0 - p)
    return d


def pb_tail(ps, k):
    return float(pb_pmf(ps)[k:].sum())


def look_elsewhere(groups, p_obs):
    """How often chance makes SOME group's own tail as small as `p_obs`,
    with every group drawn from its own distribution."""
    mins = np.ones(NSIM)
    for ps in groups:
        d = pb_pmf(ps)
        t = np.cumsum(d[::-1])[::-1]
        mins = np.minimum(mins, t[rng.choice(len(d), size=NSIM,
                                             p=d / d.sum())])
    return float((mins <= p_obs).mean())


def wread(q):
    lo, hi = sorted((float(q['flo_GHz']), float(q['fhi_GHz'])))
    inside = [l for l in LEDEB.get(q['eb'], [])
              if lo <= float(l['freq']) <= hi]
    if inside:
        return max(float(l['tstar']) for l in inside)
    rep = REPAIR.get((q['eb'], round(lo, 4), round(hi, 4)))
    return float(q['star_snr']) if rep is None else rep


def wkey(q):
    lo, hi = sorted((float(q['flo_GHz']), float(q['fhi_GHz'])))
    return (q['eb'], round(lo, 4), round(hi, 4))


def wexp(q):
    if not q['n_ind_cells']:
        return None
    N = float(q['n_ind_cells'])
    sw = 0.5 * (float(q['scale_route_a']) + float(q['scale_route_b']))
    return -math.expm1(N * math.log(1.0 - gauss_sf(TRIG / sw)))


read_rows = []
for r in UNATTR:
    f, eb = float(r['freq']), r['eb']
    dw = [q for q in BYEB.get(eb, [])
          if float(q['flo_GHz']) <= f <= float(q['fhi_GHz'])]
    sid = dw[0]['system_id'] if len(dw) == 1 else None
    if sid is None:
        c = CRK.get((eb, round(f, 4)))
        for b in (c.get('blocks', []) if c else []):
            if b.get('bad_weight_product'):
                continue
            q = [x for x in BYEB.get(b['eb'], [])
                 if float(x['flo_GHz']) <= b['f_here_GHz']
                 <= float(x['fhi_GHz'])]
            if q:
                sid = q[0]['system_id']
                break
    assert sid, 'no system identifier for %s %s' % (r['star'], eb)
    for q in BYSYS[sid]:
        if q['eb'] != eb and float(q['flo_GHz']) <= f <= float(q['fhi_GHz']):
            read_rows.append((wkey(q), wread(q), wexp(q), q))

WIN = {}
_seq = 0
for wk, s, e, q in read_rows:
    if DRIVE == 2:
        _seq += 1
        wk = wk + (_seq,)
    WIN.setdefault(wk, (s, e, q))
n_win = len(WIN)
n_win_exc = sum(1 for s, _, _ in WIN.values() if s >= TRIG)
exp_win = sum(e for _, e, _ in WIN.values() if e is not None)

star_win = collections.Counter()
star_exc = collections.Counter()
star_exp = collections.Counter()
for wk, (s, e, q) in WIN.items():
    nm = LEDNAME.get(q['star_name'], q['star_name'])
    star_win[nm] += 1
    star_exp[nm] += e or 0.0
    if s >= TRIG:
        star_exc[nm] += 1
TOP2 = [HD, JX]
two_win = sum(star_win[k] for k in TOP2)
two_exc = sum(star_exc[k] for k in TOP2)
two_exp = sum(star_exp[k] for k in TOP2)
two_ps = [e for wk, (s, e, q) in WIN.items()
          if LEDNAME.get(q['star_name'], q['star_name']) in TOP2
          and e is not None]
rest_ps, rest_exc, rest_n = [], 0, 0
for wk, (s, e, q) in WIN.items():
    nm = LEDNAME.get(q['star_name'], q['star_name'])
    if nm in TOP2:
        continue
    if DRIVE == 3 and s < TRIG:
        continue
    rest_n += 1
    if e is not None:
        rest_ps.append(e)
    if s >= TRIG:
        rest_exc += 1
p_two = pb_tail(two_ps, two_exc)
p_rest = pb_tail(rest_ps, rest_exc)
p_all = pb_tail([e for _, e, _ in WIN.values() if e is not None], n_win_exc)

ck('T2 the rebuilt covering set reproduces the published comparison',
   n_win == int(fnum('WuNWin')) and n_win_exc == int(fnum('WuNWinExc'))
   and abs(exp_win - fnum('WuExpWin')) < 0.05
   and two_exc == int(fnum('WuNWinExcTwo')),
   '%d windows (%s), %d above trigger (%s), expectation %.2f (%s), '
   'two objects %d (%s)'
   % (n_win, FROZEN['WuNWin'], n_win_exc, FROZEN['WuNWinExc'], exp_win,
      FROZEN['WuExpWin'], two_exc, FROZEN['WuNWinExcTwo']))

ck('T3 the split is exhaustive in windows, exceedances and expectation',
   two_win + rest_n == n_win and two_exc + rest_exc == n_win_exc
   and abs(two_exp + sum(rest_ps) - exp_win) < 1e-6,
   'two objects %d windows / %d exc / %.2f expected; rest %d / %d / %.2f; '
   'whole %d / %d / %.2f'
   % (two_win, two_exc, two_exp, rest_n, rest_exc, sum(rest_ps),
      n_win, n_win_exc, exp_win))

m('TwNWinTwo', '%d' % two_win)
m('TwNWinExcTwo', '%d' % two_exc)
m('TwExpTwo', '%.1f' % two_exp)
m('TwProbTwo', '%.2f' % p_two)
m('TwWinSharePct', '%.0f' % round(100.0 * two_win / n_win))
m('TwExcSharePct', '%.0f' % round(100.0 * two_exc / n_win_exc))
m('TwExpSharePct', '%.0f' % round(100.0 * two_exp / exp_win))
m('TwNWinHD', '%d' % star_win[HD])
m('TwNWinJx', '%d' % star_win[JX])
m('TwNExcHD', '%d' % star_exc[HD])
m('TwNExcJx', '%d' % star_exc[JX])
m('TwNExcJxWord', word(star_exc[JX]))
m('TwExpHD', '%.1f' % star_exp[HD])
m('TwExpJx', '%.1f' % star_exp[JX])
m('TwProbHD', '%.2f' % pb_tail(
    [e for wk, (s, e, q) in WIN.items()
     if LEDNAME.get(q['star_name'], q['star_name']) == HD and e is not None],
    star_exc[HD]))
m('TwProbJx', '%.2f' % pb_tail(
    [e for wk, (s, e, q) in WIN.items()
     if LEDNAME.get(q['star_name'], q['star_name']) == JX and e is not None],
    star_exc[JX]))

# the Class A window census of each object, as a share of the survey's
CLASSA = [r for r in CAT if r['search_class'] == 'A']
na_hd = sum(1 for r in CLASSA if LEDNAME.get(r['star_name']) == HD)
na_jx = sum(1 for r in CLASSA if LEDNAME.get(r['star_name']) == JX)
m('TwNWinAHD', '%d' % na_hd)
m('TwNWinAJx', '%d' % na_jx)
m('TwWinASharePct', '%.0f' % round(100.0 * (na_hd + na_jx) / len(CLASSA)))
_rank = sorted(collections.Counter(
    LEDNAME.get(r['star_name'], r['star_name']) for r in CLASSA).items(),
    key=lambda kv: -kv[1])
m('TwRankAHD', '%d' % (1 + [k for k, _ in _rank].index(HD)))
m('TwRankAJx', '%d' % (1 + [k for k, _ in _rank].index(JX)))
m('TwNStarA', '%d' % len(_rank))


# --- the same split on the paper's OTHER null, the empirical one: the
# fraction of a window's own 512 control positions that reaches the trigger.
# A comparison quoted to one digit must not depend on which of the two
# computed it, and quoting only the more favourable is the practice R1 2.1
# names.  The rates are the deposited per-window ones.
CFS = {}
for r in csv.DictReader(open(P(
        'ALMA_Technosignatures_40pc/statistics/control_field_statistics.csv'))):
    if r['p_trig_ctrl']:
        CFS[(r['eb'], round(float(r['nu_lo_GHz']), 4),
             round(float(r['nu_hi_GHz']), 4))] = float(r['p_trig_ctrl'])
ctrl_ps = collections.defaultdict(list)
n_nocf = 0
for wk, (s_, e_, q_) in WIN.items():
    nm = LEDNAME.get(q_['star_name'], q_['star_name'])
    k = (wk[0], wk[1], wk[2])
    if DRIVE == 11:
        ctrl_ps[nm].append(float(np.median(list(CFS.values()))))
    elif k in CFS:
        ctrl_ps[nm].append(CFS[k])
    elif q_['search_class'] == 'A':
        # the deposited rates cover the Class A population; a coarse Class B
        # window has no deposited rate and carries ~0 expectation anyway
        n_nocf += 1
exp_ctrl_hd = sum(ctrl_ps[HD])
exp_ctrl_jx = sum(ctrl_ps[JX])
exp_ctrl_all = sum(sum(v) for v in ctrl_ps.values())
p_ctrl_jx = pb_tail(ctrl_ps[JX], star_exc[JX])
p_ctrl_hd = pb_tail(ctrl_ps[HD], star_exc[HD])
ck('TB the two-object split is made on BOTH of the paper\'s nulls, and the '
   'empirical one reproduces the published total for the whole comparison',
   abs(exp_ctrl_all - fnum('WuExpWinCtrl')) < 0.6 and n_nocf == 0,
   'empirical control null: whole %.2f (published %s), HD 14055 %.2f '
   'against %d at P = %.2f, J1537 %.2f against %d at P = %.3f; %d Class A windows '
   'carry no deposited rate'
   % (exp_ctrl_all, FROZEN['WuExpWinCtrl'], exp_ctrl_hd, star_exc[HD],
      p_ctrl_hd, exp_ctrl_jx, star_exc[JX], p_ctrl_jx, n_nocf))
m('TwExpCtrlHD', '%.1f' % exp_ctrl_hd)
m('TwExpCtrlJx', '%.1f' % exp_ctrl_jx)
m('TwProbCtrlHD', '%.2f' % p_ctrl_hd)
m('TwProbCtrlJx', '%.2f' % p_ctrl_jx)
m('TwCtrlRateHD', '%.0f' % round(100 * float(np.median(ctrl_ps[HD]))))
m('TwCtrlRateJx', '%.0f' % round(100 * float(np.median(ctrl_ps[JX]))))
m('TwCtrlRateSurv', '%.0f' % round(100 * float(np.median(list(CFS.values())))))


# =====================================================================
# 3.  THE CONTROL-RING DIAGNOSTIC (Appendix D.2)
# =====================================================================
ST = dqflag._load(TREE)
RINGMED = dict(ST['ringmed'])
if DRIVE == 4:
    EXPJ = json.load(open(P('corrected_export_v399.json')))['rows']
    for _r in EXPJ:
        c, s = _r.get('ctrl_all'), _r.get('star_snr')
        if not c or s is None:
            continue
        k = dqflag.key(_r['eb'], _r['rms'], s)
        if k in RINGMED:
            RINGMED[k] = float(np.max(np.asarray(c, float)))
CLS, ROWOF = {}, {}
for r in CAT:
    k = dqflag.key(r['eb'], r['rms_mJy'], r['star_snr'])
    CLS[k] = r['search_class']
    ROWOF[k] = r
CLASS_MED = {}
#: sorted: iterating a set made the record's key order (and so its bytes)
#: depend on hash seeding -- cleanregen's one differing product (r27 merge)
for c in sorted(set(CLS.get(k) for k in RINGMED) - {None, ''}):
    if c:
        CLASS_MED[c] = float(np.median([v for k, v in RINGMED.items()
                                        if CLS.get(k) == c]))
Q = {k: v / CLASS_MED[CLS[k]] for k, v in RINGMED.items() if CLS.get(k)}
SURVMED = float(np.median(list(RINGMED.values())))

ck('T4 the control-ring diagnostic is the paper\'s own and normalises',
   all(abs(float(np.median([v for k, v in Q.items() if CLS[k] == c])) - 1.0)
       < 1e-9 for c in CLASS_MED)
   and abs(SURVMED - fnum('DqSurvMed')) < 0.005,
   'class medians %s, survey median %.3f (published %s)'
   % ({c: round(v, 3) for c, v in CLASS_MED.items()}, SURVMED,
      FROZEN['DqSurvMed']))

STARQ = collections.defaultdict(list)
for k, q in Q.items():
    STARQ[LEDNAME.get(ROWOF[k]['star_name'], ROWOF[k]['star_name'])].append(q)
STARQMED = {s: float(np.median(v)) for s, v in STARQ.items() if len(v) >= 4}
_ordq = sorted(STARQMED.items(), key=lambda kv: kv[1])
_names_q = [k for k, _ in _ordq]
q_hd, q_jx = STARQMED[HD], STARQMED[JX]
q_surv = float(np.median(list(Q.values())))
# the crossing windows alone
CROSSWIN_Q = collections.defaultdict(list)
for c in CROSS:
    for k, r in ROWOF.items():
        if r['eb'] == c['eb'] and min(float(r['flo_GHz']),
                                      float(r['fhi_GHz'])) <= c['f_topo'] \
                <= max(float(r['flo_GHz']), float(r['fhi_GHz'])):
            if k in Q:
                CROSSWIN_Q[c['star']].append(Q[k])
# the block statistic of Appendix D.2
BYBLK = collections.defaultdict(list)
for k, q in Q.items():
    BYBLK[k[0]].append(q)
QB = {b: float(np.median(v)) for b, v in BYBLK.items()}
blk_hd = sorted({c['eb'] for c in CROSS if c['star'] == HD} & set(QB))
blk_jx = sorted({c['eb'] for c in CROSS if c['star'] == JX} & set(QB))
qb_hd = [QB[b] for b in blk_hd]
qb_jx = [QB[b] for b in blk_jx]
qb_all = sorted(QB.values())
qb_fail = [b for b, v in QB.items() if v > dqflag.DQ_FACTOR]

m('TwRingQHD', '%.2f' % q_hd)
m('TwRingQJx', '%.2f' % q_jx)
m('TwRingQSurv', '%.2f' % q_surv)
m('TwRingPctHD', '%.0f' % round(100.0 * (_names_q.index(HD) + 0.5)
                                / len(_names_q)))
m('TwRingPctJx', '%.0f' % round(100.0 * (_names_q.index(JX) + 0.5)
                                / len(_names_q)))
m('TwRingNStar', '%d' % len(STARQMED))
m('TwRingQCrossHD', '%.2f' % float(np.median(CROSSWIN_Q[HD])))
m('TwRingQCrossJx', '%.2f' % float(np.median(CROSSWIN_Q[JX])))
m('TwBlockQHDLo', '%.2f' % min(qb_hd))
m('TwBlockQHDHi', '%.2f' % max(qb_hd))
m('TwBlockQJxLo', '%.2f' % min(qb_jx))
m('TwBlockQJxHi', '%.2f' % max(qb_jx))
m('TwBlockQMax', '%.1f' % max(qb_all))
m('TwBlockNFail', '%d' % len(qb_fail))
#: the extreme of the distribution as a VALUE, never as a catalogue name:
#: the catalogue splits one star across two keys and a macro is typeset
#: verbatim.
m('TwRingQWorst', '%.2f' % _ordq[-1][1])
m('TwRingQBest', '%.2f' % _ordq[0][1])
m('TwRingQSpreadPct', '%.0f' % round(100 * (_ordq[-1][1] - _ordq[0][1])))


# =====================================================================
# 4.  THE TUNED-LINE TEST
# =====================================================================
TUNED = []
for c in CROSS:
    row = None
    for k, r in ROWOF.items():
        if r['eb'] == c['eb'] and min(float(r['flo_GHz']),
                                      float(r['fhi_GHz'])) <= c['f_topo'] \
                <= max(float(r['flo_GHz']), float(r['fhi_GHz'])):
            row = r
            break
    if row is None:
        TUNED.append(dict(star=c['star'], f=c['f_topo'], centred=None))
        continue
    lo, hi = sorted((float(row['flo_GHz']), float(row['fhi_GHz'])))
    fc = lo + (hi - lo) * (1.0 if DRIVE == 5 else 0.5)
    fline, dv_c = nearest(MASK_F, fc)
    _, dv_x = nearest(MASK_F, c['f_topo'])
    TUNED.append(dict(star=c['star'], f=c['f_topo'], wlo=lo, whi=hi,
                      width_GHz=hi - lo, f_centre=fc,
                      tuned_line=MASK_BY_F[fline]['spec'],
                      tuned_qn=MASK_BY_F[fline]['qn'],
                      tuned_f=fline, centre_dv=dv_c,
                      centred=abs(dv_c) < HALF,
                      cross_dv_sky=dv_x,
                      cross_from_centre_kms=CKMS * (c['f_topo'] - fc) / fc))
n_cen = sum(1 for t in TUNED if t.get('centred'))
ck('T5 the tuned-line test distinguishes: some of these windows are '
   'centred on a masked transition and some are not',
   0 < n_cen < len([t for t in TUNED if t.get('centred') is not None]),
   '%d of %d crossing windows centred within %.0f km/s of a masked '
   'transition' % (n_cen, len(TUNED), HALF))
m('TwNTunedWin', '%d' % n_cen)
m('TwNCrossWin', '%d' % len([t for t in TUNED
                             if t.get('centred') is not None]))
_cj = [t for t in TUNED if t['star'] == JX and t.get('centred')]
_ch = [t for t in TUNED if t['star'] == HD and t.get('centred')]
m('TwNTunedJx', '%d' % len(_cj))
m('TwNTunedHD', '%d' % len(_ch))
m('TwTunedCenKms', '%.0f' % abs(_cj[0]['centre_dv']) if _cj else '0')
m('TwTunedLineJx', _cj[0]['tuned_line'] if _cj else 'none')
_hdoff = sorted(abs(t['centre_dv']) for t in TUNED
            if t['star'] == HD and 'centre_dv' in t)
m('TwHDCenMinKms', '%.0f' % _hdoff[0])
m('TwHDWinWidthGHz', '%.2f' % float(np.median(
    [t['width_GHz'] for t in TUNED if t['star'] == HD and 'width_GHz' in t])))


# =====================================================================
# 5.  THE SYSTEMIC-VELOCITY SWEEP
# =====================================================================
def attr_at(f_bary, v, lines):
    """(nearest rest frequency, signed offset, inside the mask) for one
    crossing carried into a rest frame moving at v km/s."""
    f = f_bary * (1.0 + v / CKMS)
    f0, dv = nearest(lines, f)
    return f0, dv, abs(dv) <= HALF


def sweep(crossings, lines, vs):
    out = []
    for c in crossings:
        base = attr_at(c['f_bary'], 0.0, lines)[2]
        flips, inside = [], []
        for v in vs:
            f0, dv, ins = attr_at(c['f_bary'], float(v), lines)
            inside.append(ins)
            if ins != base:
                flips.append((float(v), f0, dv))
        out.append(dict(star=c['star'], f_star=c['f_star'],
                        f_topo=c['f_topo'], base=base,
                        n_in=int(sum(inside)), n_v=len(vs),
                        frac_in=float(sum(inside)) / len(vs),
                        changes=bool(flips),
                        v_lo=min(v for v, _, _ in flips) if flips else None,
                        v_hi=max(v for v, _, _ in flips) if flips else None))
    return out


VS = SWEEP if DRIVE != 6 else np.array([0.0])
JXC = [c for c in CROSS if c['star'] == JX]
HDC = [c for c in CROSS if c['star'] == HD]
SW_JX = sweep(JXC, MASK_F, VS)
SW_HD = sweep(HDC, MASK_F, VS)
SW_JX_WIDE = sweep(JXC, WIDE_F, VS) if WIDE_F else []
n_ch_jx = sum(1 for r in SW_JX if r['changes'])
n_ch_hd = sum(1 for r in SW_HD if r['changes'])
n_ch_jx_wide = sum(1 for r in SW_JX_WIDE if r['changes'])
# the velocity at which the single attributed crossing leaves the mask
_att = [r for r in SW_JX if r['base']]
_vcrit = None
if _att:
    r0 = _att[0]
    bad = [float(v) for v in VS
           if not attr_at(
               [c for c in JXC if abs(c['f_star'] - r0['f_star']) < 1e-9
                ][0]['f_bary'], float(v), MASK_F)[2]]
    _vcrit = min(bad, key=abs) if bad else None

ck('T6 the sweep is able to move something, so a null result is a '
   'measurement and not a broken loop',
   (n_ch_jx + n_ch_hd + n_ch_jx_wide) > 0,
   'over +-%.0f km/s: %d of %d J1537 crossings change status against the '
   'mask, %d of %d against the wider list, %d of %d HD 14055 crossings'
   % (max(abs(VS)), n_ch_jx, len(SW_JX), n_ch_jx_wide, len(SW_JX_WIDE),
      n_ch_hd, len(SW_HD)))

m('TwSweepHalfKms', '%.0f' % max(abs(VS)))
m('TwSweepNChangeJx', '%d' % n_ch_jx)
m('TwSweepNChangeJxWordCap', word(n_ch_jx, cap=True))
m('TwSweepNChangeJxWide', '%d' % n_ch_jx_wide)
m('TwSweepNChangeHD', '%d' % n_ch_hd)
m('TwSweepNJx', '%d' % len(SW_JX))
m('TwSweepVCrit', tex('%+.0f' % _vcrit) if _vcrit is not None else 'none')
# how close the nearest unattributed crossing ever comes to the mask
_closest = min(min(abs(attr_at(c['f_bary'], float(v), MASK_F)[1])
                   for v in VS) for c in JXC
               if not attr_at(c['f_bary'], 0.0, MASK_F)[2])
m('TwSweepClosestKms', '%.0f' % _closest)
# the sample's own systemic velocities, for scale
VSYS = sorted(abs(r['frame']['v_sys']) for r in LED['rows']
              if r['frame'].get('v_sys') is not None
              and not r['frame'].get('bound_only'))
_byst = {}
for r in LED['rows']:
    if r['frame'].get('v_sys') is not None and not r['frame'].get(
            'bound_only'):
        _byst[r['star']] = abs(r['frame']['v_sys'])
_vv = sorted(_byst.values())
m('TwVsysMedKms', '%.0f' % _vv[len(_vv) // 2])
m('TwVsysMaxKms', '%.0f' % _vv[-1])
m('TwVsysNStar', '%d' % len(_vv))
m('TwVsysOverPct', '%.0f' % round(100.0 * sum(1 for v in _vv if v > HALF)
                                  / len(_vv)))


# =====================================================================
# 6.  HD 14055's REPEAT COVERAGE
# =====================================================================
CATEB = {r['eb'] for r in CAT}
hd_blocks = sorted({c['eb'] for c in CROSS if c['star'] == HD})
hd_dates = {}
for r in SWIN:
    if r['star'] == HD:
        hd_dates[r['eb']] = r['date_utc']
hd_cross_dates = sorted(set(hd_dates[b] for b in hd_blocks if b in hd_dates))
hd_nblk_cat = len([b for b in hd_blocks if b in CATEB])
hd_nblk_tail = len([b for b in hd_blocks if b not in CATEB])
# the covering repeat epochs of the two archival-tail events
ev_rows = collections.defaultdict(list)
for r in H14REC['rows']:
    ev_rows[r['event']].append(r)
cov_cat, cov_tail = {}, {}
for ev, rs in ev_rows.items():
    o = [r for r in rs if not r['is_discovery']]
    if DRIVE == 7:
        cov_cat[ev], cov_tail[ev] = len(o), 0
    else:
        cov_cat[ev] = sum(1 for r in o if r['eb'] in CATEB)
        cov_tail[ev] = sum(1 for r in o if r['eb'] not in CATEB)
ck('T7 the repeat coverage is split and not merged, and the follow-up '
   'stratum is non-empty',
   all(cov_cat[e] + cov_tail[e] == len(
       [r for r in ev_rows[e] if not r['is_discovery']]) for e in ev_rows)
   and min(cov_tail.values()) > 0,
   '; '.join('event %s: %d covering epochs, %d in the released catalogue, '
             '%d in the follow-up stratum'
             % (e, cov_cat[e] + cov_tail[e], cov_cat[e], cov_tail[e])
             for e in sorted(ev_rows)))

EV = {e['tag']: e for e in H14REC['events']}
m('TwHDNBlockCross', '%d' % len(hd_blocks))
m('TwHDNBlockCensus', '%d' % hd_nblk_cat)
m('TwHDNBlockCensusWord', word(hd_nblk_cat))
m('TwHDNBlockTail', '%d' % hd_nblk_tail)
m('TwHDNNightCross', '%d' % len(hd_cross_dates))
m('TwHDNBlockCat', '%d' % len({r['eb'] for r in SWIN if r['star'] == HD}))
m('TwHDNWinCat', '%d' % len([r for r in SWIN if r['star'] == HD]))
m('TwHDCovEpoch', '%d' % (cov_cat['A'] + cov_tail['A']))
m('TwHDCovCensus', '%d' % cov_cat['A'])
m('TwHDCovTail', '%d' % cov_tail['A'])
m('TwHDNDeep', '%d' % EV['A']['deep']['n'])
m('TwHDExclA', '%.1f' % EV['A']['deep']['exclusion_sigma'])
m('TwHDExclB', '%.1f' % EV['B']['deep']['exclusion_sigma'])
m('TwHDNeffA', '%.1f' % EV['A']['n_eff_epochs'])
m('TwHDNeffB', '%.1f' % EV['B']['n_eff_epochs'])
_sig = sorted(c['sig_excl'] for c in CROSS
              if c['star'] == HD and c['sig_excl'] is not None)
m('TwHDSigLo', '%.1f' % _sig[0])
m('TwHDSigHi', '%.1f' % _sig[-1])
_tr = [abs(c['t_rep']) for c in CROSS
       if c['star'] == HD and c['t_rep'] is not None]
m('TwHDTRepMax', '%.1f' % max(_tr))
m('TwHDNRep', '%d' % max(c['n_rep'] for c in CROSS if c['star'] == HD))
m('TwHDSpanD', '%.0f' % max(c['dt_max'] for c in CROSS
                            if c['star'] == HD and c['dt_max']))
_jr = [abs(c['t_rep']) for c in CROSS
       if c['star'] == JX and c['t_rep'] is not None]
m('TwJxTRepMax', '%.1f' % max(_jr))
m('TwJxNRepMax', '%d' % max(c['n_rep'] for c in CROSS if c['star'] == JX))
m('TwJxSigHi', '%.1f' % max(c['sig_excl'] for c in CROSS
                            if c['star'] == JX and c['sig_excl']))


# =====================================================================
# 7.  THE GRID EDGES
# =====================================================================
#: `cid` is NOT unique in this record -- every attributed row carries the
#: label `L` -- so the edge predicate is the grid class the generator
#: computed, never the identifier.
EDGESET = [r for r in EDGE['rows']
           if str(r.get('class', '')).startswith('edge')]
hd_edge = [r for r in EDGESET if LEDNAME.get(r['star'], r['star']) == HD]
# the largest rate actually trialled, reconstructed by `edge_v423.py` from
# the window's own trial count and channel width: the grid's last trial is
# the first at or beyond the nominal ceiling, so it OVERSHOOTS by under one
# step.  Read from that generator's record, never recomputed here.
hd_grid = [r for r in EDGE['rows']
           if LEDNAME.get(r['star'], r['star']) == HD
           and r.get('top') is not None]
_nom = max(r['dmax'] for r in hd_grid)
_top = max(r['top'] for r in hd_grid)
_step = max(r['dd'] for r in hd_grid)
if DRIVE == 8:
    _top = _nom
ck('T8 the edge rows read here are the published Table D2 rows for this '
   'star, and the grid overshoots its nominal ceiling by under one step',
   # GEN (v4.29 fold, E3): "len(hd_edge) == 2" -- HD 14055's two edge-limited drifts were X29ae and X2c3bb, which
   # both fell; the star now holds none.  Asserted: the edge set read here is the published Table D1 set, and the
   # grid construction (overshoot under one step) on this star's windows.  \TwHDEdge* are emitted only while
   # the star holds an edge row (the sentence that cites them is the text owner's to remove).
   len(EDGESET) == int(fnum('EgNEdge'))
   and _nom < _top < _nom + _step,
   '%s; largest rate trialled %.0f Hz/s against a nominal ceiling of '
   '%.0f Hz/s, a step of %.0f Hz/s'
   % (', '.join('%s %.3f GHz %+.0f Hz/s (trial %d of %d)'
                % (r['eb'].split('_')[-1], r['freq'], r['drift'],
                   r['k'], r['ntrial'] - 1) for r in hd_edge),
      _top, _nom, _step))
m('TwHDNEdge', '%d' % len(hd_edge))
m('TwHDNEdgeWordCap', word(len(hd_edge), cap=True))
if hd_edge:
    m('TwHDEdgeALos', '%.2f' % min(abs(r['alos']) for r in hd_edge))
    m('TwHDEdgeALosHi', '%.2f' % max(abs(r['alos']) for r in hd_edge))
m('TwHDRateTop', '%.0f' % _top)
m('TwHDRateNom', '%.0f' % _nom)
m('TwHDRateStep', '%.0f' % _step)
# the two edges are not the same kind of number, and `r27-minor` (B2) says
# so from the same record: one is the FIRST trial, exactly at the negative
# ceiling with no overshoot; the other is the LAST, past its own ceiling by
# a fraction of one step.
if hd_edge:
    _hi = max(hd_edge, key=lambda r: r['drift'])
    _lo = min(hd_edge, key=lambda r: r['drift'])
    m('TwHDEdgeOverHz', '%.0f' % (_hi['drift'] - _hi['dmax']))
    m('TwHDEdgeOverPct', '%.1f' % (100.0 * (_hi['drift'] - _hi['dmax'])
                                   / _hi['dmax']))
    m('TwHDEdgeLoOverHz', '%.0f' % abs(_lo['drift'] + _lo['dmax']))
m('TwAccelCeilMed', FROZEN['AccelCeilMed'])

# ★ how surprising is an edge landing?  Under exchangeability over its own
# trials a window's maximum lands on one of the two outermost with
# probability 2/n.  Summed over every crossing that carries a reconstructed
# grid, that is the expected number of edge-limited fits in the survey -- and
# the same sum over this one star's crossings is what makes two of them
# notable.  The assumption is stated: a drifting carrier is NOT uniform over
# trials, so this is a statement about the noise hypothesis only.
#: a grid is RECONSTRUCTED, not merely recorded: `edge_v423.py` solves
#: for the step and the trial index, and one row has a trial count it
#: cannot place on a grid at all.
_grid = [r for r in EDGE['rows']
         if r.get('ntrial') and r.get('k') is not None]
_pe = [2.0 / r['ntrial'] for r in _grid]
_hdg = [r for r in _grid if LEDNAME.get(r['star'], r['star']) == HD]
_pehd = [2.0 / r['ntrial'] for r in _hdg]
_obs_hd = sum(1 for r in _hdg if str(r['class']).startswith('edge'))
ck('TD the edge-landing comparison is over the same population in both '
   'halves, and the grid-carrying crossing count is the published one',
   len(_grid) == int(fnum('EgNGrid')) and len(EDGESET) == int(fnum('EgNEdge'))
   and _obs_hd == len(hd_edge),
   '%d of %d grid-carrying crossings land on an outermost trial against '
   '%.2f expected if the maximum were uniform over trials; toward %s it is '
   '%d of %d against %.3f (P = %.4f)'
   % (len(EDGESET), len(_grid), sum(_pe), HD, _obs_hd, len(_hdg),
      sum(_pehd), pb_tail(_pehd, _obs_hd)))
m('TwEdgeObsAll', '%d' % len(EDGESET))
m('TwEdgeNGrid', '%d' % len(_grid))
m('TwEdgeExpAll', '%.1f' % sum(_pe))
m('TwEdgeObsHD', '%d' % _obs_hd)
m('TwEdgeNGridHD', '%d' % len(_hdg))
m('TwEdgeExpHD', '%.3f' % sum(_pehd))
m('TwEdgeProbHD', '%.4f' % pb_tail(_pehd, _obs_hd))
# and the same look-elsewhere correction, because HD 14055 was chosen after
# the fact here too
_bystar = collections.defaultdict(list)
for r in _grid:
    _bystar[LEDNAME.get(r['star'], r['star'])].append(2.0 / r['ntrial'])
m('TwEdgeLookProb', '%.2f'
  % look_elsewhere(list(_bystar.values()), pb_tail(_pehd, _obs_hd)))
m('TwEdgeLookNStar', '%d' % len(_bystar))
# ★ and the split that says where the effect lives: the expectation over the
# whole is dominated by four three-trial coarse grids, where an edge landing
# is nearly even money.  Over the FINE grids the carrier search actually
# uses, the pile-up is real and HD 14055 holds half of it.
_fine = [r for r in _grid if r['ntrial'] >= 20]
m('TwEdgeNFine', '%d' % len(_fine))
m('TwEdgeObsFine', '%d' % sum(1 for r in _fine
                              if str(r['class']).startswith('edge')))
m('TwEdgeExpFine', '%.1f' % sum(2.0 / r['ntrial'] for r in _fine))
m('TwEdgeProbFine', '%.2f' % pb_tail([2.0 / r['ntrial'] for r in _fine],
                                     sum(1 for r in _fine
                                         if str(r['class']).startswith(
                                             'edge'))))
m('TwNEdgeSurvey', '%d' % len(EDGESET))
# how far each fitted rate sits from the zero a transition at rest demands,
# in steps of its own grid: the one number that separates a line from a
# carrier without appealing to anything outside the window
_steps = {}
for c in CROSS:
    e = EDGEROW.get((c['eb'], round(c['f_topo'], 4)), {})
    if e.get('dd'):
        _steps[(c['star'], round(c['f_star'], 3))] = abs(e['drift']) / e['dd']
_sv = sorted(_steps.values())
m('TwStepMin', '%.1f' % _sv[0])
m('TwStepNext', '%.0f' % _sv[1])
m('TwStepMax', '%.0f' % _sv[-1])
m('TwNStepGrid', '%d' % len(_sv))
if hd_edge:
    m('TwHDEdgeFreqLo', '%.3f' % min(r['freq'] for r in hd_edge))
    m('TwHDEdgeFreqHi', '%.3f' % max(r['freq'] for r in hd_edge))
m('TwAGrid', FROZEN['WdAGrid'])


# =====================================================================
# 7b.  HOW OFTEN CHANCE MAKES SOME OBJECT LOOK THIS CONCENTRATED
# =====================================================================
# J1537 is the most discrepant object of the many the comparison covers, and
# it was chosen BECAUSE it is.  Its own tail is therefore not the probability
# that anything unusual happened; the probability that SOME object in the
# comparison reaches a tail that small is.  Measured, not asserted: each
# window keeps its own exceedance probability, every star's count is drawn
# from its own Poisson-binomial distribution, and the smallest per-star tail
# of the realisation is recorded.
STARPS = collections.defaultdict(list)
for wk, (s_, e_, q_) in WIN.items():
    if e_ is not None:
        STARPS[LEDNAME.get(q_['star_name'], q_['star_name'])].append(e_)


if DRIVE == 9:
    STARPS = {JX: STARPS[JX]}
PMF = {st_: pb_pmf(ps) for st_, ps in STARPS.items()}
p_obs_jx = float(np.cumsum(PMF[JX][::-1])[::-1][star_exc[JX]])
p_look = look_elsewhere(list(STARPS.values()), p_obs_jx)
ck('T9 the look-elsewhere correction is computed and not waved at: the '
   'most discrepant of many objects is drawn from the same windows and '
   'the same per-window rates',
   len(PMF) > 10 and 0.0 < p_obs_jx < 1.0 and p_look >= p_obs_jx,
   '%s alone gives P = %.3f over %d objects; some object reaches a tail '
   'that small in %.2f of %d chance realisations'
   % (JX, p_obs_jx, len(PMF), p_look, NSIM))
m('TwLookNStar', '%d' % len(PMF))
m('TwLookProb', '%.2f' % p_look)
m('TwLookPct', '%.0f' % round(100 * p_look))
m('TwProbJxRaw', '%.3f' % p_obs_jx)


# =====================================================================
# 7c.  WHAT THE STAR'S OWN FIELD SAYS: THE RANK AND THE VISIBILITY FIT
# =====================================================================
n_out = sum(1 for c in CROSS
            if c['ctrl_max'] is not None and c['ctrl_max'] > c['tstar'])
n_meas = sum(1 for c in CROSS if c['ctrl_max'] is not None)
if DRIVE == 10:
    n_meas -= 1
surv_out = sum(1 for r in DEP
               if r['T_ctrl_max'] and float(r['T_ctrl_max']) > float(
                   r['T_star']))
n_loc = sum(1 for c in CROSS if c['localised'])
n_fit = sum(1 for c in CROSS if c['re_sigma'] is not None)
ck('TA the rank is read over the same population in both places: every '
   'crossing of these two objects carries a control maximum, and the '
   'survey-wide count is read from the same column',
   n_meas == len(CROSS) and 0 < surv_out <= len(DEP),
   '%d of %d crossings of the two objects are outranked by their own '
   'control ring, against %d of %d in the survey; %d of %d visibility '
   'fits localise' % (n_out, n_meas, surv_out, len(DEP), n_loc, n_fit))
m('TwNOutranked', '%d' % n_out)
m('TwNOutrankedSurv', '%d' % surv_out)
m('TwNCrossSurv', '%d' % len(DEP))
m('TwNLocalised', '%d' % n_loc)
m('TwNFit', '%d' % n_fit)
m('TwNLocalHD', '%d' % sum(1 for c in CROSS
                           if c['star'] == HD and c['localised']))
m('TwNLocalJx', '%d' % sum(1 for c in CROSS
                           if c['star'] == JX and c['localised']))
m('TwReLo', '%.1f' % min(c['re_sigma'] for c in CROSS
                         if c['re_sigma'] is not None))
m('TwReHi', '%.1f' % max(c['re_sigma'] for c in CROSS
                         if c['re_sigma'] is not None))
m('TwPbHD', '%.2f' % float(np.median([c['pb_offset'] for c in CROSS
                                      if c['star'] == HD and c['pb_offset']])))
m('TwPbJx', '%.2f' % float(np.median([c['pb_offset'] for c in CROSS
                                      if c['star'] == JX and c['pb_offset']])))
m('TwReInjMean', FROZEN['RsevReAtFiveMeanA'])
m('TwReInjSd', FROZEN['RsevReAtFiveSdA'])
m('TwCtrlMaxJx', '%.1f' % max(c['ctrl_max'] for c in CROSS
                              if c['star'] == JX))
m('TwTStarCtrlJx', '%.1f' % [c['tstar'] for c in CROSS
                             if c['star'] == JX
                             and c['ctrl_max'] == max(
                                 x['ctrl_max'] for x in CROSS
                                 if x['star'] == JX)][0])
m('TwOnSrcJx', '%.0f' % float(np.median(
    [float(r['on_source_s']) for r in CAT
     if LEDNAME.get(r['star_name']) == JX])))
m('TwOnSrcHD', '%.0f' % float(np.median(
    [float(r['on_source_s']) for r in CAT
     if LEDNAME.get(r['star_name']) == HD])))
_hm = sorted(abs(c['mask_dv']) for c in CROSS if c['star'] == HD)
m('TwHDMaskLo', '%.0f' % _hm[0])
m('TwHDMaskHi', '%.0f' % _hm[-1])
_jm = sorted(abs(c['mask_dv']) for c in CROSS
             if c['star'] == JX and not c['attributed'])
m('TwJxMaskLo', '%.0f' % _jm[0])
m('TwJxMaskHi', '%.0f' % _jm[-1])
# where J1537's exceedances sit: which blocks, and over what band
_jwin = [w for w in [dict(star=LEDNAME.get(q_['star_name'], q_['star_name']),
                          eb=wk[0], lo=wk[1], hi=wk[2], exc=(s_ >= TRIG))
                     for wk, (s_, e_, q_) in WIN.items()]
         if w['star'] == JX]
_jexc = [w for w in _jwin if w['exc']]
m('TwJxNBlock', '%d' % len({w['eb'] for w in _jwin}))
m('TwJxNBlockWord', word(len({w['eb'] for w in _jwin})))
m('TwJxNBlockExc', '%d' % len({w['eb'] for w in _jexc}))
m('TwJxNBlockExcWord', word(len({w['eb'] for w in _jexc})))
m('TwJxExcBandLo', '%.0f' % min(w['lo'] for w in _jexc))
m('TwJxExcBandHi', '%.0f' % max(w['hi'] for w in _jexc))
m('TwJxNWinInExcBlock', '%d' % len([w for w in _jwin
                                    if w['eb'] in {x['eb'] for x in _jexc}]))
# the crossings those exceeding windows hold, and how many of them the
# visibility fit places at the star
_jxc = [c for c in CROSS if c['star'] == JX
        and any(w['eb'] == c['eb'] and w['lo'] <= c['f_topo'] <= w['hi']
                for w in _jexc)]
m('TwJxNCrossExcWord', word(len(_jxc)))
m('TwJxNCrossExc', '%d' % len(_jxc))
m('TwJxNLocalExcWord', word(sum(1 for c in _jxc if c['localised'])))
m('TwJxNNotLocalExcWord', word(sum(1 for c in _jxc if not c['localised'])))
m('TwSweepNJxWord', word(len(SW_JX)))
m('TwSweepNUnchJxWord', word(len(SW_JX) - n_ch_jx))
m('TwNWinExcTwoWord', word(two_exc))

# the two objects' covering windows, written out so the report can be read
# against them
WINDUMP = []
for wk, (s_, e_, q_) in sorted(WIN.items()):
    nm = LEDNAME.get(q_['star_name'], q_['star_name'])
    if nm in TOP2:
        WINDUMP.append(dict(star=nm, eb=wk[0], lo=wk[1], hi=wk[2],
                            cls=q_['search_class'],
                            chanw=float(q_['chanw_Hz']),
                            stat=s_, exp=e_, exceeds=bool(s_ >= TRIG)))


# =====================================================================
# 7d.  WHAT THE PAIR TABLE IS MADE OF, AND WHEN THE BLOCKS WERE TAKEN
# =====================================================================
PAIRS = json.load(open(P('pairs_v415.json')))['pairs']
hd_pairs = [q for q in PAIRS if LEDNAME.get(q['star'], q['star']) == HD]
jx_pairs = [q for q in PAIRS if LEDNAME.get(q['star'], q['star']) == JX]
TAILEB = {c['eb'] for c in CROSS if not c['in_catalogue']}
hd_census_pairs = [q for q in hd_pairs
                   if q['eblo'] not in TAILEB and q['ebhi'] not in TAILEB]
m('TwNPairAll', FROZEN['TjNPair'])
m('TwNPairHD', '%d' % len(hd_pairs))
m('TwNPairJx', '%d' % len(jx_pairs))
#: pairs with an EDGE-LIMITED MEMBER, which is not Table 5's `edge`
#: verdict: one of the three is excluded outright and the table records the
#: stronger verdict.  Both counts are emitted so neither can be read as the
#: other.
m('TwNPairEdgeMemHD', '%d' % sum(1 for q in hd_pairs
                                 if str(q['edgelo']).startswith('edge')
                                 or str(q['edgehi']).startswith('edge')))
m('TwNPairEdgeHD', FROZEN['TjNPairEdge'])
m('TwNPairEdgeHDWord', word(int(fnum('TjNPairEdge'))))
# GEN (v4.29 fold, E3): with X29ae / X2c3bb gone, HD 14055's census crossings form no cross-block pair of Table 5;
# the span is emitted only while one exists (the sentence citing it is the text owner's).
if hd_census_pairs:
    m('TwPairCensusSpanD', '%.1f' % (max(q['dt'] for q in hd_census_pairs)
                                     / 86400.0))
m('TwPairSpanD', '%.0f' % (max(q['dt'] for q in hd_pairs) / 86400.0))
m('TwGridFactor', FROZEN['EcGridFactor'])
# the nine informative repeat epochs, and how much deeper they are
_deep = {}
for ev, rs in ev_rows.items():
    o = sorted([r for r in rs if not r['is_discovery']],
               key=lambda r: r['rms_combined_mJy'],
               reverse=(DRIVE == 12))
    nd = EV[ev]['deep']['n']
    _deep[ev] = dict(n=nd,
                     in_cat=sum(1 for r in o[:nd] if r['eb'] in CATEB),
                     rms_deep_hi=max(r['rms_combined_mJy'] for r in o[:nd]),
                     rms_rest_lo=min(r['rms_combined_mJy'] for r in o[nd:]))
ck('TC the informative repeat epochs are named for what they are: the '
   'deep ones are the follow-up blocks and not the released catalogue, '
   'and they are deeper by a clear margin',
   all(v['in_cat'] == 0 and v['rms_deep_hi'] < v['rms_rest_lo']
       for v in _deep.values()),
   '; '.join('event %s: %d deep epochs, %d of them in the released '
             'catalogue, rms <= %.1f mJy against >= %.1f for the rest'
             % (e, v['n'], v['in_cat'], v['rms_deep_hi'], v['rms_rest_lo'])
             for e, v in sorted(_deep.items())))
m('TwHDNDeepCat', '%d' % _deep['A']['in_cat'])
m('TwHDRmsDeep', '%.1f' % _deep['A']['rms_deep_hi'])
m('TwHDRmsRest', '%.1f' % _deep['A']['rms_rest_lo'])


# =====================================================================
# 8.  OUTPUT
# =====================================================================
ISOTOPE = {'13', '15', '17', '18', '29', '30', '33', '34', '36', '37'}


def mol(t):
    """A Splatalogue species string as the page should set it.  A digit run
    is a mass-number SUPERSCRIPT where it opens the formula or follows a
    hyphen, and otherwise a SUBSCRIPT -- except that a run ending in a
    two-digit mass number and followed by a letter splits, which is what
    `CH3CH213CN` is: ethyl cyanide with a 13-C."""
    out, i = [], 0
    while i < len(t):
        if not t[i].isdigit():
            out.append({'-': '$-$'}.get(t[i], t[i]))
            i += 1
            continue
        j = i
        while j < len(t) and t[j].isdigit():
            j += 1
        run, prev = t[i:j], (t[i - 1] if i else '')
        nxt = t[j] if j < len(t) else ''
        if i == 0 or prev in '-\u2013':
            out.append('$^{%s}$' % run)
        elif prev.isalpha() and len(run) > 2 and run[-2:] in ISOTOPE \
                and nxt.isalpha():
            out.append('$_{%s}$$^{%s}$' % (run[:-2], run[-2:]))
        elif prev.isalpha() and len(run) == 2 and run in ISOTOPE \
                and nxt.isalpha():
            out.append('$^{%s}$' % run)
        else:
            out.append('$_{%s}$' % run)
        i = j
    return ''.join(out)


#: the star is a SPANNING ROW and not a column: a column wide enough for
#: the object's name does not fit an OJA column, measured.
STARTEX = {HD: 'HD~14055', JX: '\\BkAlmaName'}
rows_tex = []
for s_ in (HD, JX):
    first = True
    rows_tex.append('\\multicolumn{6}{@{}l}{\\emph{%s}} \\\\'
                    % STARTEX[s_])
    for c in [x for x in CROSS if x['star'] == s_]:
        if c['drift'] is None:
            drift = '--'
        elif c['gridclass'] == 'edge-high':
            drift = '$\\ge\\!+%d$' % round(c['drift'])
        elif c['gridclass'] == 'edge-low':
            drift = '$\\le\\!-%d$' % abs(round(c['drift']))
        else:
            drift = '$%+d$' % round(c['drift'])
        rows_tex.append(
            '%.3f & %.2f & %s & %s & %s & %s \\\\'
            % (c['f_star'], c['tstar'], drift,
               c['mask_tex'], '$%+d$' % round(c['mask_dv']),
               ('$%+.1f$' % c['re_sigma'])
               if c['re_sigma'] is not None else '--'))
        first = False
    if s_ == HD:
        rows_tex.append('\\hline')
m('TwWideMolList', ', '.join(sorted(
    {mol(c['wide_mol']) for c in CROSS if c['wide_mol']})))
m('TwWideDvMax', '%.0f' % max(abs(c['wide_dv']) for c in CROSS
                              if c['wide_dv'] is not None))
m('TwWideNTrans', FROZEN['XlNTrans'])
m('TwWideNSpecies', FROZEN['XlNSpecies'])
TAB = ('%% GENERATED by twostars_r27.py -- do not hand-edit.\n'
       '\\begin{tabular}{@{}r@{~}r@{~}r@{~}l@{~}r@{~}r@{}}\n'
       '\\hline\n'
       '$\\nu_\\star$ & $T_\\star$ & $\\dot\\nu_{\\rm obs}$ & '
       'nearest masked & $\\Delta v_\\star$ & '
       '${\\rm Re}/\\sigma$ \\\\\n'
       '(GHz) & & (Hz\\,s$^{-1}$) & transition & (km\\,s$^{-1}$) & '
       '\\\\\n'
       '\\hline\n' + '\n'.join(rows_tex) + '\n\\hline\n\\end{tabular}\n')
open(OUT_TAB, 'w').write(TAB)

with open(OUT_TEX, 'w') as fh:
    fh.write('%% GENERATED by twostars_r27.py (round %d) -- do not '
             'hand-edit.\n' % ROUND)
    for k, v in M:
        fh.write('\\newcommand{\\%s}{%s}\n' % (k, v))

json.dump(dict(generator='twostars_r27.py', round=ROUND, drive=DRIVE,
               #: relative: an absolute build path made this record differ after
               #: the tree moved (cleanregen, r27 merge pass 3)
               tree=os.path.relpath(TREE, HERE), crossings=CROSS, tuned=TUNED,
               window_split=dict(
                   n_win=n_win, n_exc=n_win_exc, exp=exp_win, p=p_all,
                   two_win=two_win, two_exc=two_exc, two_exp=two_exp,
                   p_two=p_two, rest_n=rest_n, rest_exc=rest_exc,
                   rest_exp=sum(rest_ps), p_rest=p_rest,
                   by_star={k: dict(win=star_win[k], exc=star_exc[k],
                                    exp=star_exp[k]) for k in star_win}),
               ring=dict(class_median=CLASS_MED, survey_median=SURVMED,
                         star_median=STARQMED, block=QB,
                         cross_windows=dict(CROSSWIN_Q)),
               sweep=dict(mask_jx=SW_JX, mask_hd=SW_HD, wide_jx=SW_JX_WIDE,
                          v_crit=_vcrit, closest=_closest),
               hd_recurrence=dict(blocks=hd_blocks, dates=hd_cross_dates,
                                  cov_census=cov_cat, cov_tail=cov_tail,
                                  events=H14REC['events']),
               edges=hd_grid, windows=WINDUMP, macros=dict(M), checks=LOG, fails=FAIL),
          open(OUT_JSON, 'w'), indent=1, default=float)

print('\n%d macros -> %s' % (len(M), os.path.basename(OUT_TEX)))
for k, v in M:
    print('  \\%-22s %s' % (k, v))
print('\n%s: %d checks, %d FAIL %s'
      % ('twostars_r27', len(LOG), len(FAIL), FAIL))
sys.exit(1 if (FAIL and DRIVE == 0) else 0)
