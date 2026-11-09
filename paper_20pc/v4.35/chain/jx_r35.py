#!/usr/bin/env python3
r"""jx_r35.py -- round 3520: ALMA J153702653-33192492 and the CO rank (v4.35, Referee 2 M3, M4, m8).

Reads only products already in the tree, writes numbers/survey_numbers_round3520.tex, tab_jx_r35.tex and
jx_r35.json.

  Q1 (M3-4) THE PER-CROSSING VISIBILITY FIT AND WHERE ON THE SKY THE STATISTIC PEAKS.  The visibility fit
     (ledger_v403.csv, the adopted epoch) measures the mean real and imaginary part of the visibilities phased to
     the star and at eight control positions; it fixes the position and fits no offset.  The offset is read from
     the search's own source-region grid -- the statistic at the star and at 134 positions within 0.06 theta_PB
     of it, at the crossing's cell -- frozen from the census products by r35inputs/harvest_jx_r35.py
     (r35inputs/jx_srcgrid_r35.json).  Asserted: every frozen star statistic is the ledger's T* at the published
     cell, the grid is the extractor's (0.06 theta_PB, 135 positions), and the phase centre lies at the printed
     \TwPbJx.
  Q2 (M3-1/2) LEAKAGE FROM THE PHASE CENTRE.  The star is 5.75" from the phase centre, inside the main lobe of a
     7-8" synthesised beam.  Emission at the phase centre would make the statistic rise across the grid toward
     the phase centre: at the grid's edge on that side it would be B(d_pc - r_max)/B(d_pc) times the star's
     (3.2-3.9 for a Gaussian main lobe of the extractor's theta_syn, >= 1.3 for one twice as wide), against
     B(r_max) <= 0.67 for a source at the star.  Asserted per exceeding crossing; the verdict is printed.
  Q3 (M3-5) THE EXCESS COUNTED ONLY WITH THE EXCEEDANCES THE FIT PLACES AT THE STAR, against the same control-
     position expectation as \TwExpCtrlJx (twostars_r30.json, the control-rate look-elsewhere groups), exact
     Poisson-binomial tail; the look-elsewhere share over the same objects, simulated as twostars_r27 does it.
     Asserted: the full count's tail recomputed here is twostars' \TwProbCtrlJxRaw exactly.
  Q4 (M3-3) THE DENSE-GAS LINES OF THE REFEREE'S LIST IN THE TARGET'S LSR FRAME (masklsr_v520.json f_lsr; rest
     frequencies from the dated catalogue query r21inputs/r21_lines_full.json, the strongest component of each
     line), as velocities offset from the Lupus CO velocity \LsLupVco.  Asserted: every listed line is found once.
  Q5 (M4-1) THE CO MEMBERS OF THE SPATIAL STAGE (ledger_r34.json above_all_controls = \LrStageN rows): the beta
     Pic / HD 48370 split, and the beta Pic CO crossings by set (membership_r32.json: census / hold-out / tail).
  Q6 (M4-2) IS HD 48370's CO COMPACT AT THE STAR?  The fit's sigma is the scatter of the phased visibilities, so a
     source the array resolves inflates it: a point source of the search statistic T* would return Re/sigma ~
     T* x (\RsevReAtFiveMeanA / 5) (the injections at T = 5).  Also the grid's outer ring and the control ring.
  Q7 (m8) THE CENSUS CROSSINGS THE FIT DOES NOT PLACE AT THE STAR AND THOSE NEVER FITTED, joined exactly as
     counts_r15.py joins them (\CsNVisFit, \CsNVisLocal asserted), by attribution.

    python3 jx_r35.py [--drive N]      N = 1..11: each perturbs one input in memory, prints FAILED and exits 1
                                       without writing a production path
"""
import collections
import csv
import json
import math
import os
import re
import sys

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import star_alias                     # noqa: E402

ROUND = 3520
DRIVE = int(sys.argv[sys.argv.index('--drive') + 1]) if '--drive' in sys.argv else None
J = lambda p: json.load(open(os.path.join(HERE, p)))  # noqa: E731
OUT, FAIL = {}, []
WORD = ('no', 'one', 'two', 'three', 'four', 'five', 'six', 'seven', 'eight', 'nine', 'ten', 'eleven', 'twelve',
        'thirteen', 'fourteen', 'fifteen')
word = lambda k: WORD[k] if k < len(WORD) else '%d' % k  # noqa: E731
CKMS = 299792.458
JX, HD48 = 'ALMA J153702653-33192492', 'HD 48370'
NSIM = 200000


def m(k, v):
    assert k.isalpha() and k not in OUT, k
    OUT[k] = v


def ck(label, ok, detail=''):
    print('  %-78s %s  %s' % (label[:78], 'PASS' if ok else 'FAIL', detail))
    if not ok:
        FAIL.append(label.split()[0])


def tv(name):
    pat = re.compile(r'\\(?:new|renew|provide)command\{\\%s\}\{((?:[^{}]|\{[^{}]*\})*)\}' % name)
    vals = []
    for f in sorted(os.listdir(os.path.join(HERE, 'numbers'))):
        if f.startswith('survey_numbers') and f.endswith('.tex') and '_drive' not in f \
                and 'round%d' % ROUND not in f:
            vals += [v for v in pat.findall(open(os.path.join(HERE, 'numbers', f), errors='ignore').read()) if v]
    assert len(set(vals)) == 1, ('macro %s defined %d times: %s' % (name, len(vals), vals[:3]))
    return vals[0]


def tnum(name):
    s = tv(name).replace('\\ensuremath{-}', '-').replace('$', '').replace('{', '').replace('}', '')
    return float(s.replace('\\,', '').strip())


def gauss(x, fwhm):
    return math.exp(-4.0 * math.log(2.0) * (x / fwhm) ** 2)


# ================================================================== inputs
LED = J('ledger.json')['rows']
MEMB = J('membership_r32.json')['rows']
GRID = J('r35inputs/jx_srcgrid_r35.json')['rows']
TS27 = J('twostars_r27.json')
TS30 = J('twostars_r30.json')
LR34 = J('ledger_r34.json')
LSR = J('masklsr_v520.json')
CAT = J('r21inputs/r21_lines_full.json')
VF = list(csv.DictReader(open(os.path.join(HERE, 'ledger_v403.csv'))))
VFR = J('visfit_r7_result.json')['fits']

if DRIVE == 1:                      # Q1a: a frozen grid that is not the census product
    GRID[0]['grid'][0]['T'] += 0.01
if DRIVE == 2:                      # Q2: plant phase-centre emission on the first exceeding crossing's grid
    _g = GRID[0]
    _pc = (-_g['l_star_arcsec'], -_g['m_star_arcsec'])
    _d = math.hypot(*_pc)
    for q in _g['grid']:
        q['T'] = round(_g['tstar'] * gauss(math.hypot(q['dl'] - _pc[0], q['dm'] - _pc[1]), _g['syn_arcsec'])
                       / gauss(_d, _g['syn_arcsec']), 4)
if DRIVE == 3:                      # Q3: one control rate of J1537 changed -> no longer twostars' expectation
    for c in TS30['look_elsewhere']:
        if c['label'] == 'control rates':
            c['groups'][c['names'].index([n for n in c['names'] if n.startswith('ALMA J1537')][0])][0] += 0.05
if DRIVE == 4:                      # Q4: a listed line missing from the catalogue query
    CAT['lines'] = [x for x in CAT['lines'] if x[1] != 'DCN']
if DRIVE == 5:                      # Q5: an 11th-member that is neither beta Pic nor HD 48370 CO
    LR34['above_all_controls'][1]['star'] = 'HD 14055'
if DRIVE == 6:                      # Q1b: the phase centre read at the wrong offset
    for _g in GRID:
        _g['l_star_arcsec'] *= 1.05
if DRIVE == 7:                      # Q7: a census crossing loses its fit row
    VF = [v for v in VF if not (v['eb'] == 'A002_Xc66ce1_Xaa9')]
if DRIVE == 8:                      # Q4b: a crossing planted on DCO+ at the cloud velocity
    for r in LSR['rows']:
        if r['eb'] == 'A002_Xfe62c1_X398' and abs(r['freq'] - 216.1844318) < 1e-4:
            r['f_lsr'] = 216.1125822 * (1.0 - 4.9 / CKMS)
if DRIVE == 9:                      # Q6: HD 48370's fit made as compact as a point source of its T*
    for v in VF:
        if v['eb'] == 'A002_Xc26103_X155a':
            v['re_adopted'] = '35.0'

PBJX = tnum('TwPbJx')
VCLOUD = tnum('LsLupVco')
WCLOUD = tnum('LsLupWco')
VH = tnum('MaskHalfKms')
REINJ, REINJSD = tnum('RsevReAtFiveMeanA'), tnum('RsevReAtFiveSdA')
RE_MIN = 4.0                         # the committed criterion (ledger_v403.py RE_MIN), printed as Re/sigma >= 4


def lkey(eb, f):
    return (eb, round(float(f), 4))


LEDK = {lkey(r['eb'], r['freq']): r for r in LED}


def vfit(eb, f):
    """counts_r15.py's own join of a crossing to the fit ledger: block + topocentric frequency to 5e-4 GHz,
    block alone where each list holds one crossing in it."""
    c = [v for v in VF if v['eb'] == eb and v['f_cross_GHz'] and abs(float(v['f_cross_GHz']) - f) < 5e-4]
    if not c and _VFEB[eb] == 1 and _LDEB[eb] == 1:
        c = [v for v in VF if v['eb'] == eb]
    assert len(c) <= 1, ('two fit rows for one crossing', eb, f)
    return c[0] if c else None


# ★ the J1537 fits made along the other window's drift, corrected (r35inputs/visfit_fix_r35.json, J-recal): applied
# exactly as twostars_r27 applies them (its TV), so the two generators read one verdict per crossing
VFIX = J('r35inputs/visfit_fix_r35.json')['fits']
if DRIVE == 11:                     # Q1d: a corrected fit whose verdict the committed criterion does not give
    VFIX[0] = dict(VFIX[0], corrected=dict(VFIX[0]['corrected'], re=3.9))


def vfix(eb, f):
    fx = [x for x in VFIX if x['eb'] == eb and abs(x['f_cross_GHz'] - f) < 5e-4]
    return fx[0] if fx else None


_VFEB = collections.Counter(v['eb'] for v in VF)
_LDEB = collections.Counter(r['eb'] for r in LED)

# ===================================================== Q1 the per-crossing table
print('Q1 (M3-4) the fit and the grid, per crossing of %s' % JX)
JXC = sorted([r for r in LED if r['star'].startswith(JX)], key=lambda r: float(r['freq']))
GK = {lkey(g['eb'], g['freq']): g for g in GRID}
_exc_win = [w for w in TS27['windows'] if w['star'] == JX and w['exceeds']]
ROWS = []
for r in JXC:
    f = float(r['freq'])
    g = GK.get(lkey(r['eb'], f))
    v = vfit(r['eb'], f)
    xy = np.array([(q['dl'], q['dm']) for q in g['grid']])
    T = np.array([q['T'] for q in g['grid']])
    rr = np.hypot(xy[:, 0], xy[:, 1])
    rmax = float(rr.max())
    pc = -np.array([g['l_star_arcsec'], g['m_star_arcsec']])
    dpc = float(np.hypot(*pc))
    u = pc / dpc
    outer = rr > rmax - 1e-3
    kpc = int(np.flatnonzero(outer)[np.argmax(xy[outer] @ u)])
    kpk = int(np.argmax(T))
    th = g['syn_arcsec']
    d_edge = float(np.hypot(*(xy[kpc] - pc)))
    ROWS.append(dict(
        eb=r['eb'], f=f, tstar=float(r['tstar']), attributed=bool(r['attributed']),
        exceeds=any(w['eb'] == r['eb'] and w['lo'] <= f <= w['hi'] for w in _exc_win),
        re=float(v['re_adopted']), im=float(v['im_adopted']), cmax=float(v['ctrl_adopted']),
        localised=(v['localised_adopted'] == 'True'), fix=vfix(r['eb'], f),
        T_grid_star=float(T[0]), n_grid=len(T), rmax=rmax, pb=g['pb_arcsec'], syn=th, dpc=dpc,
        peak_r=float(rr[kpk]), peak_T=float(T[kpk]),
        peak_cos=(float(xy[kpk] @ u / rr[kpk]) if rr[kpk] > 0 else 0.0),
        edge_ratio=float(T[kpc] / T[0]), ring_ratio=float(T[outer].mean() / T[0]),
        pred_pc=gauss(d_edge, th) / gauss(dpc, th), pred_pc2=gauss(d_edge, 2 * th) / gauss(dpc, 2 * th),
        pred_star=gauss(rmax, th), product=g['product']))
_nflip = 0
_okfix = True
for x in ROWS:
    fx = x.pop('fix')
    if fx is None:
        continue
    a, k = fx['archived'], fx['corrected']
    _cm = max(k['ring_max'], k.get('freq_max', -1e9))
    _v = bool(k['re'] >= RE_MIN and abs(k['im']) < 3.0 and k['re'] > _cm)
    _okfix &= (abs(x['re'] - a['re']) < 6e-4 or abs(x['re'] - k['re']) < 6e-4) and _v == (k['status'] == 'localised')
    _nflip += int(_v != x['localised'])
    x.update(re=k['re'], im=k['im'], cmax=_cm, localised=_v, corrected=bool(fx['drift_wrong_in_archive']))
ck('Q1d the corrected fits replace the archived ones they name (the fit ledger holds that archived fit or the '
   'corrected one) and the committed criterion gives each record\'s verdict',
   _okfix and sum(1 for x in ROWS if 'corrected' in x) == len(VFIX),
   '%d corrected fits applied, %d verdicts change' % (sum(1 for x in ROWS if 'corrected' in x), _nflip))
m('JqNFixDrift', '%d' % sum(1 for x in ROWS if x.get('corrected')))
m('JqNFixDriftWord', word(sum(1 for x in ROWS if x.get('corrected'))))
ck('Q1a every frozen grid is the census product: its star statistic is the ledger\'s T* at the published cell, '
   'and every crossing of the object has one',
   len(ROWS) == len(JXC) == int(tnum('BkAlmaNCross'))
   and all(abs(x['T_grid_star'] - x['tstar']) < 1e-4 for x in ROWS),
   '; '.join('%.3f: %.4f vs %.4f' % (x['f'], x['T_grid_star'], x['tstar']) for x in ROWS))
ck('Q1b the grid is the extractor\'s (0.06 theta_PB, 135 positions) and the phase centre lies at the printed '
   'offset',
   all(x['n_grid'] == 135 and abs(x['rmax'] - 0.06 * x['pb']) < 0.01 and abs(x['dpc'] - PBJX) < 0.06
       for x in ROWS),
   '; '.join('%.3f: r_max %.3f (0.06 x %.2f), d_pc %.2f' % (x['f'], x['rmax'], x['pb'], x['dpc']) for x in ROWS))
EXC = [x for x in ROWS if x['exceeds']]
ck('Q1c the exceeding crossings are twostars\' (\\TwJxNCrossExc) and the localised ones \\TwJxNLocalExcWord',
   len(EXC) == int(tv('TwJxNCrossExc')) and word(sum(x['localised'] for x in EXC)) == tv('TwJxNLocalExcWord'),
   '%d exceeding, %d localised' % (len(EXC), sum(x['localised'] for x in EXC)))

# ===================================================== Q2 leakage from the phase centre
print('Q2 (M3-1/2) leakage from the phase centre')
for x in EXC:
    x['leak_excluded'] = bool(x['edge_ratio'] < 1.0 <= x['pred_pc2'] and x['peak_r'] < 0.5 * x['rmax'])
ck('Q2 for every exceeding crossing the statistic falls toward the phase centre where emission there would make '
   'it rise even through a main lobe twice the extractor\'s width, and the grid peak lies within half the grid '
   'radius of the star',
   all(x['leak_excluded'] for x in EXC),
   '; '.join('%.3f: edge/star %.2f (PC model %.2f, 2x beam %.2f; star model %.2f), peak %.2f"'
             % (x['f'], x['edge_ratio'], x['pred_pc'], x['pred_pc2'], x['pred_star'], x['peak_r']) for x in EXC))
m('JqLeakEdgeLo', '%.2f' % min(x['edge_ratio'] for x in EXC))
m('JqLeakEdgeHi', '%.2f' % max(x['edge_ratio'] for x in EXC))
m('JqLeakPcLo', '%.1f' % min(x['pred_pc'] for x in EXC))
m('JqLeakPcHi', '%.1f' % max(x['pred_pc'] for x in EXC))
m('JqLeakPcWide', '%.1f' % min(x['pred_pc2'] for x in EXC))
m('JqLeakStarLo', '%.2f' % min(x['pred_star'] for x in EXC))
m('JqLeakStarHi', '%.2f' % max(x['pred_star'] for x in EXC))
m('JqGridR', '%.1f' % float(np.median([x['rmax'] for x in EXC])))
m('JqPeakLo', '%.1f' % min(x['peak_r'] for x in EXC))
m('JqPeakHi', '%.1f' % max(x['peak_r'] for x in EXC))
m('JqSynLo', '%.1f' % min(x['syn'] for x in EXC))
m('JqSynHi', '%.1f' % max(x['syn'] for x in EXC))
m('JqPcBeams', '%.1f' % (PBJX / float(np.median([x['syn'] for x in EXC]))))
m('JqNLeakExcl', '%d' % sum(x['leak_excluded'] for x in EXC))
m('JqNLeakExclWord', word(sum(x['leak_excluded'] for x in EXC)))
_co = [x for x in ROWS if x['attributed']]
m('JqCoPeakR', '%.1f' % _co[0]['peak_r'] if _co else '?')
m('JqCoRingPct', '%.0f' % (100 * _co[0]['ring_ratio']) if _co else '?')

# ===================================================== Q3 the localised-only excess
print('Q3 (M3-5) the excess from the exceedances the fit places at the star')


def pb_pmf(ps):
    d = np.zeros(len(ps) + 1)
    d[0] = 1.0
    for i, p in enumerate(ps):
        d[1:i + 2] = d[1:i + 2] * (1.0 - p) + d[0:i + 1] * p
        d[0] *= (1.0 - p)
    return d


def tail(ps, k):
    return float(pb_pmf(ps)[k:].sum())


_le = [c for c in TS30['look_elsewhere'] if c['label'] == 'control rates']
assert len(_le) == 1
_le = _le[0]
_ij = [i for i, n in enumerate(_le['names']) if n == JX]
PSJ = _le['groups'][_ij[0]] if len(_ij) == 1 else []
ref = TS30['reference']
n_full = int(ref['n_exc_jx'])
n_loc = sum(1 for x in EXC if x['localised'])
p_full = tail(PSJ, n_full)
p_loc = tail(PSJ, n_loc)
ck('Q3 the expectation and the full count\'s tail recomputed from twostars\' own control-rate groups are '
   'twostars\' (\\TwExpCtrlJx, \\TwProbCtrlJxRaw), and the localised count is a part of the full one',
   len(_ij) == 1 and abs(sum(PSJ) - ref['exp_ctrl_jx']) < 1e-9 and abs(p_full - ref['p_ctrl_jx']) < 1e-12
   and '%.1f' % sum(PSJ) == tv('TwExpCtrlJx') and '%.3f' % p_full == tv('TwProbCtrlJxRaw')
   and n_full == int(tv('TwNExcJx')) and 0 <= n_loc <= n_full,
   'expected %.3f (twostars %.3f), %d exceedances P %.4f (twostars %.4f), %d localised P %.4f'
   % (sum(PSJ), ref['exp_ctrl_jx'], n_full, p_full, ref['p_ctrl_jx'], n_loc, p_loc))
rng = np.random.default_rng(ROUND)
mins = np.ones(NSIM)
for ps in _le['groups']:
    d = pb_pmf(ps)
    t = np.cumsum(d[::-1])[::-1]
    mins = np.minimum(mins, t[rng.choice(len(d), size=NSIM, p=d / d.sum())])
p_look_loc = float((mins <= p_loc + 1e-15).mean())
_se = math.sqrt(max(p_look_loc * (1 - p_look_loc), 1e-12) / NSIM)
_pct = lambda z: '%.0f' % round(100 * min(1.0, max(0.0, z)))  # noqa: E731
ck('Q3b the look-elsewhere share is at least the object\'s own tail and its printed digit is stable within two '
   'Monte Carlo standard errors',
   p_look_loc >= p_loc - 3 * _se and _pct(p_look_loc - 2 * _se) == _pct(p_look_loc) == _pct(p_look_loc + 2 * _se),
   '%.4f +- %.4f' % (p_look_loc, _se))
# the expectation is \TwExpCtrlJx itself (asserted in Q3); \JqLocExp is kept only because the r35 draft cites it --
# prefer \TwExpCtrlJx (one quantity, one name: valuetwin)
m('JqLocExp', tv('TwExpCtrlJx'))
m('JqLocObs', '%d' % n_loc)
m('JqLocObsWord', word(n_loc))
m('JqLocP', '%.2f' % p_loc)
m('JqLocLookPct', _pct(p_look_loc))

# ===================================================== Q4 the dense-gas lines in the LSR frame
print('Q4 (M3-3) the listed dense-gas lines at the Lupus CO velocity')
WANT = [('DCO+', 'DCO$^+$\\,$3$--$2$', 216.1126), ('DCN', 'DCN\\,$3$--$2$', 217.2385),
        ('c-HCCCH', 'c-C$_3$H$_2$', 217.8221), ('c-HCCCH', 'c-C$_3$H$_2$', 217.9400),
        ('c-HCCCH', 'c-C$_3$H$_2$', 218.1604), ('CH3OH', 'CH$_3$OH\\,$4_2$--$3_1$\\,E', 218.4401),
        ('HC3N', 'HC$_3$N\\,$24$--$23$', 218.3247)]
LINES = []
for mol, tex, f0 in WANT:
    c = [x for x in CAT['lines'] if x[1] == mol and abs(x[0] - f0) < 0.003]
    if c:
        best = max(c, key=lambda x: x[3])
        LINES.append(dict(mol=mol, tex=tex, f=best[0], comps=sorted(x[0] for x in c),
                          spread_kms=CKMS * (max(x[0] for x in c) - min(x[0] for x in c)) / f0, n=len(c)))
ck('Q4a every line of the referee\'s list is in the dated catalogue query (all its components within 3 MHz are '
   'kept, and the offset is taken to the nearest of them)',
   len(LINES) == len(WANT) and all(x['n'] >= 1 for x in LINES),
   '; '.join('%s %.6f (%d comp., %.2f km/s)' % (x['mol'], x['f'], x['n'], x['spread_kms']) for x in LINES))
LSRK = {lkey(r['eb'], r['freq']): r for r in LSR['rows']}
PAIRS = []
for x in EXC:
    q = LSRK[lkey(x['eb'], x['f'])]
    x['f_lsr'] = q['f_lsr']
    for ln in LINES:
        # the LSR velocity an emitter of this line would need, to the nearest of its components
        _v = [CKMS * (fc - q['f_lsr']) / fc for fc in ln['comps']]
        v_em = min(_v, key=lambda z: abs(z - VCLOUD))
        PAIRS.append(dict(f=x['f'], line=ln['mol'], f0=ln['f'], v_em=v_em, dv=v_em - VCLOUD))
_close = min(PAIRS, key=lambda p: abs(p['dv']))
ck('Q4b no listed line falls within the mask half-width of any exceeding crossing at the Lupus CO velocity',
   abs(_close['dv']) > VH,
   'closest: %.3f GHz vs %s %.4f, emitter at %+.1f km/s LSR, %+.1f from the cloud (v_h %.0f)'
   % (_close['f'], _close['line'], _close['f0'], _close['v_em'], _close['dv'], VH))
m('JqLineNList', '%d' % len(LINES))
m('JqLineMinDv', '%.0f' % abs(_close['dv']))
m('JqLineMinSpecies', [x['tex'] for x in LINES if x['mol'] == _close['line'] and x['f'] == _close['f0']][0])
m('JqLineMinFreq', '%.3f' % _close['f'])

# ===================================================== Q5 the CO members of the spatial stage
print('Q5 (M4-1) the CO members of the spatial stage')
STG = LR34['above_all_controls']
_isbp = lambda s: s.replace(' ', '').lower() in ('betapic', 'betpic')  # noqa: E731
n_bp = sum(1 for r in STG if _isbp(r['star']) and 'CO' in r['disposition'])
n_hd = sum(1 for r in STG if r['star'] == HD48 and 'CO' in r['disposition'])
BPCO = [r for r in MEMB if _isbp(r['star']) and r['attributed'] and r['transition'].startswith('CO(')]
_sets = collections.Counter(r['event'] for r in BPCO)
_bpcen = {(r['eb'], round(r['nu_topo_GHz'], 4)) for r in BPCO if r['event'] == 'census'}
_out = [r for r in LED if _isbp(r['star'].replace('bet', 'beta')) and r['attributed']
        and (r['eb'], round(float(r['freq']), 4)) in _bpcen
        and r['eb'] not in {s['eb'] for s in STG if _isbp(s['star'])}]
ck('Q5 the spatial stage is \\LrStageN rows, its CO members are \\LrStageNCo and all toward beta Pic or HD 48370, '
   'and every beta Pic CO crossing is a census crossing in its own block (\\CsBpCoBlocks)',
   len(STG) == int(tv('LrStageN')) and n_bp + n_hd == int(tv('LrStageNCo'))
   and n_bp + n_hd == sum(1 for r in STG if 'CO' in r['disposition'])
   and _sets['census'] == len(BPCO) == len({r['eb'] for r in BPCO}) == int(tv('CsBpCoBlocks'))
   and len(_out) == len(BPCO) - n_bp,
   '%d beta Pic + %d HD 48370 of %d CO; beta Pic CO by set %s; outranked %s'
   % (n_bp, n_hd, int(tv('LrStageNCo')), dict(_sets), [(r['eb'], r['tstar']) for r in _out]))
# the number of beta Pic CO crossings / blocks is \CsBpCoBlocks (asserted in Q5), not re-published here
m('JqNBpCo', '%d' % n_bp)
m('JqNBpCoWord', word(n_bp))
m('JqNHdCo', '%d' % n_hd)
m('JqNHdCoWord', word(n_hd))
m('JqNBpCoOther', '%d' % (len(BPCO) - _sets['census']))
m('JqNBpCoOtherWord', word(len(BPCO) - _sets['census']))
m('JqNBpCoOut', '%d' % len(_out))
m('JqNBpCoOutWord', word(len(_out)))

# ===================================================== Q6 is HD 48370's CO compact?
print('Q6 (M4-2) HD 48370\'s CO at the star')
_h = [r for r in LED if r['star'] == HD48 and r['attributed']]
assert len(_h) == 1
_h = _h[0]
_hv = vfit(_h['eb'], float(_h['freq']))
_hg = GK[lkey(_h['eb'], _h['freq'])]
_hT = np.array([q['T'] for q in _hg['grid']])
_hxy = np.array([(q['dl'], q['dm']) for q in _hg['grid']])
_hr = np.hypot(_hxy[:, 0], _hxy[:, 1])
_hout = _hr > _hr.max() - 1e-3
hd_re = float(_hv['re_adopted'])
hd_pt = float(_h['tstar']) * REINJ / 5.0                    # a point source of this T*, by the injections' scaling
hd_pt_lo = float(_h['tstar']) * (REINJ - REINJSD) / 5.0
hd_ring = float(_hT[_hout].mean() / _hT[0])
hd_ring_pt = gauss(float(_hr.max()), _hg['syn_arcsec'])
_stg = [r for r in STG if r['eb'] == _h['eb']][0]
hd_ctrl = float(_stg['T_ctrl_max']) / float(_stg['T_star'])
_hcomm = [v for k, v in VFR.items() if k.startswith('HD 48370|')][0]['star']['snr_re']
hd_compact = bool(hd_re >= hd_pt_lo and hd_ring <= hd_ring_pt + 0.1)
ck('Q6 HD 48370\'s CO is not compact at the star: the fit returns far less Re/sigma than a point source of its '
   'statistic would (at the adopted and the committed epoch), and the grid\'s outer ring stays above the point-'
   'source response',
   (not hd_compact) and hd_re < hd_pt_lo and _hcomm < hd_pt_lo and hd_ring > hd_ring_pt
   and abs(float(_hg['tstar']) - float(_h['tstar'])) < 1e-4,
   'Re/sigma %.1f adopted (%.1f committed) vs %.0f for a point source (%.0f at -1 sd); outer ring %.2f of the star vs '
   '%.2f; control maximum %.2f of the star' % (hd_re, _hcomm, hd_pt, hd_pt_lo, hd_ring, hd_ring_pt, hd_ctrl))
m('JqHdRe', '%.1f' % hd_re)
m('JqHdRePoint', '%.0f' % hd_pt)
m('JqHdRingPct', '%.0f' % (100 * hd_ring))
m('JqHdRingPointPct', '%.0f' % (100 * hd_ring_pt))
m('JqHdCtrlPct', '%.0f' % (100 * hd_ctrl))
m('JqHdCompact', 'compact' if hd_compact else 'extended')

# ===================================================== Q7 the census crossings not placed at the star
print('Q7 (m8) census crossings not localised and not fitted')
CEN = [r for r in MEMB if r['event'] == 'census']
VIS = collections.Counter()
NOTLOC, UNFIT = [], []
_flip_cen = 0
_CS_READS_FIX = 'visfit_fix_r35' in open(os.path.join(HERE, 'counts_r15.py')).read()
for r in CEN:
    v = vfit(r['eb'], r['nu_topo_GHz'])
    st = v['visibility_status'] if v else 'no fit'
    fx = vfix(r['eb'], r['nu_topo_GHz'])
    if fx is not None and v is not None:
        k = fx['corrected']
        _st = ('localised' if (k['re'] >= RE_MIN and abs(k['im']) < 3.0
                               and k['re'] > max(k['ring_max'], k.get('freq_max', -1e9))) else 'not localised')
        _flip_cen += int(_st != st)
        st = _st
    VIS[st] += 1
    if st == 'not localised':
        NOTLOC.append(r)
    elif st in ('untested', 'no fit'):
        UNFIT.append(dict(r, why=st))
n_fit = VIS['localised'] + VIS['not localised']
# why each was never fitted, from the campaign's own plan and outcome (r35inputs/jx_visplan_r35.json)
VPL = J('r35inputs/jx_visplan_r35.json')
if DRIVE == 10:                     # Q7b: a block outside the plan with an outcome recorded for it
    VPL['outcome'][[u['eb'] for u in UNFIT if u['eb'] not in VPL['plan_ebs']][0]] = dict(status='ok', cells=[])
_pl = set(VPL['plan_ebs'])
for u in UNFIT:
    o = VPL['outcome'].get(u['eb'], {})
    u['cause'] = ('late' if u['eb'] not in _pl else
                  'nocal' if o.get('status') == 'no_measurement_set' else 'other')
_cz = collections.Counter((u['cause'], bool(u['attributed'])) for u in UNFIT)
ck('Q7b every unfitted crossing has one cause: its block was not in the campaign\'s plan (it entered the census '
   'later), the campaign could not calibrate it, or it fitted the block at another cell or epoch',
   sum(_cz.values()) == len(UNFIT) and all(u['cause'] in ('late', 'nocal', 'other') for u in UNFIT)
   and all(u['cause'] != 'late' or u['eb'] not in VPL['outcome'] for u in UNFIT),
   str(sorted(_cz.items())))
ck('Q7 the census partition is counts_r15\'s (\\CsNVisFit fitted, \\CsNVisLocal localised, of \\CsNCross), and every '
   'unattributed crossing of the 6 + 13 is one of the \\CeObs compared',
   # r35: the corrected J1537 fits (visfit_fix_r35.json) flip _flip_cen verdicts of the fit ledger; counts_r15 must
   # print the corrected count if it reads that record, and the fit ledger's own count if it does not -- either way
   # exactly, and which one is decided by its source, not by agreement
   n_fit == int(tv('CsNVisFit'))
   and VIS['localised'] == int(tv('CsNVisLocal')) + (0 if _CS_READS_FIX else _flip_cen)
   and len(CEN) == int(tv('CsNCross'))
   and all(r['in_comparison'] for r in NOTLOC + UNFIT if not r['attributed'])
   and sum(1 for r in CEN if r['in_comparison']) == int(tv('CeObs')),
   '%s; not localised %d (%d unattributed), unfitted %d (%d unattributed)'
   % (dict(VIS), len(NOTLOC), sum(not r['attributed'] for r in NOTLOC), len(UNFIT),
      sum(not r['attributed'] for r in UNFIT)))
m('JqNVisLocal', '%d' % VIS['localised'])
m('JqNNotLoc', '%d' % len(NOTLOC))
m('JqNNotLocUn', '%d' % sum(not r['attributed'] for r in NOTLOC))
m('JqNNotLocUnWord', word(sum(not r['attributed'] for r in NOTLOC)))
m('JqNNotLocCo', '%d' % sum(r['attributed'] for r in NOTLOC))
m('JqNNotLocCoWord', word(sum(r['attributed'] for r in NOTLOC)))
m('JqNUnfit', '%d' % len(UNFIT))
m('JqNUnfitUn', '%d' % sum(not r['attributed'] for r in UNFIT))
m('JqNUnfitAttr', '%d' % sum(r['attributed'] for r in UNFIT))
# r35 (N5, fresh read): word forms of the three counts §4.4 prints, for the writers
m('JqNNotLocWord', word(len(NOTLOC)))
m('JqNUnfitWord', word(len(UNFIT)))
m('JqNUnfitUnWord', word(sum(not r['attributed'] for r in UNFIT)))
for _c in ('late', 'nocal', 'other'):
    _n = sum(1 for u in UNFIT if u['cause'] == _c)
    _nu = sum(1 for u in UNFIT if u['cause'] == _c and not u['attributed'])
    _cap = _c[0].upper() + _c[1:]
    m('JqNUnfit%s' % _cap, '%d' % _n)
    m('JqNUnfit%sWord' % _cap, word(_n))
    m('JqNUnfit%sUn' % _cap, '%d' % _nu)
    m('JqNUnfit%sUnWord' % _cap, word(_nu))

# ====================================================================== write
if FAIL:
    print('\nFAILED: %s' % ', '.join(FAIL))
    sys.exit(1)
if DRIVE is not None:
    print('jx_r35: drive %d passed every check -- it did NOT fire' % DRIVE)
    sys.exit(0)
with open(os.path.join(HERE, 'numbers/survey_numbers_round%d.tex' % ROUND), 'w') as fh:
    fh.write('%% GENERATED by jx_r35.py (round %d) -- do not hand-edit.\n' % ROUND)
    for k in sorted(OUT):
        fh.write('\\newcommand{\\%s}{%s}\n' % (k, OUT[k]))
# the float (caption, label, size) is the writer's, as for tab_recalrecon_r34: this is the tabular and its notes
_T = ['% GENERATED by jx_r35.py (round 3520) -- do not hand-edit.',
      '\\setlength{\\tabcolsep}{3pt}',
      '\\begin{tabular}{@{}rrrrrcr@{}}', '\\hline',
      '$\\nu$ & $T_\\star$ & Re/$\\sigma$ & Im/$\\sigma$ & ctrl & at star$^{a}$ & peak$^{b}$ \\\\',
      'GHz & & & & & & arcsec \\\\', '\\hline']


def _sg(v):                            # a signed one-decimal cell, with a typeset minus
    t = '%.1f' % v
    return '$-$' + t[1:] if t.startswith('-') else t


for x in ROWS:
    _T.append('%.3f%s & %.2f & %s%s & %s & %s & %s & %.1f \\\\'
              % (x['f'], '' if x['exceeds'] else '$^{d}$', x['tstar'], _sg(x['re']),
                 '$^{c}$' if x.get('corrected') else '', _sg(x['im']), _sg(x['cmax']),
                 'yes' if x['localised'] else 'no', x['peak_r']))
_T += ['\\hline', '\\end{tabular}',
       '\\par\\smallskip{\\footnotesize\\raggedright Re/$\\sigma$, Im/$\\sigma$: the mean real and imaginary parts of '
       'the visibilities phased to the star; ctrl: the largest Re/$\\sigma$ at the fit\\textquoteright s control '
       'positions and frequencies. $^{a}$Re/$\\sigma\\ge4$, $|$Im/$\\sigma|<3$ and above every control. '
       '$^{b}$Distance from the star of the largest statistic on the search\\textquoteright s source grid, which '
       'extends %s\\,arcsec from it. $^{c}$Fitted along the window\\textquoteright s own drift on the re-calibrated '
       'block; the archived fit had used the other window\\textquoteright s. $^{d}$The CO($2{\\to}1$) crossing, '
       'attributed.\\par}' % OUT['JqGridR']]
open(os.path.join(HERE, 'tab_jx_r35.tex'), 'w').write('\n'.join(_T) + '\n')
json.dump(dict(generated_by='jx_r35.py', round=ROUND, crossings=ROWS, lines=LINES, line_pairs=PAIRS,
               localised_only=dict(n_full=n_full, n_loc=n_loc, exp=sum(PSJ), p_full=p_full, p_loc=p_loc,
                                   p_look_loc=p_look_loc, n_sim=NSIM, seed=ROUND),
               hd48370=dict(eb=_h['eb'], tstar=float(_h['tstar']), re_adopted=hd_re, re_committed=_hcomm,
                            re_point=hd_pt, ring_ratio=hd_ring, ring_point=hd_ring_pt, ctrl_ratio=hd_ctrl),
               stage=dict(n_bp=n_bp, n_hd=n_hd, bp_sets=dict(_sets),
                          bp_outranked=[dict(eb=r['eb'], tstar=r['tstar']) for r in _out]),
               census_vis=dict(VIS), not_localised=[dict(star=star_alias.designation(r['star'], tex=False),
                                                         eb=r['eb'], nu=r['nu_topo_GHz'],
                                                         attributed=r['attributed']) for r in NOTLOC],
               unfitted=[dict(star=star_alias.designation(r['star'], tex=False), eb=r['eb'], nu=r['nu_topo_GHz'],
                              attributed=r['attributed'], why=r['why'], cause=r['cause']) for r in UNFIT]),
          open(os.path.join(HERE, 'jx_r35.json'), 'w'), indent=1, default=float)
print('jx_r35: %d macros, tab_jx_r35.tex, jx_r35.json' % len(OUT))
for k in sorted(OUT):
    print('  \\%-20s %s' % (k, OUT[k]))
