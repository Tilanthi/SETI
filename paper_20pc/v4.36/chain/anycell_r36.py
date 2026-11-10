#!/usr/bin/env python3
r"""Round 3640 (v4.36, N3): FOUR CHECKS THE ROUND-36 REFEREES ASKED FOR, EACH FROM EXISTING PRODUCTS.

(R2-3) THE COUNTING RULE, AND THE COMPARISON UNDER THE OTHER ONE.  A crossing is a window whose
LARGEST cell at the stellar position reaches the trigger and is neither attributed by the line mask nor
taken by the atmospheric screen; the control side is the same rule (chance_v414: n_w control positions
whose window MAXIMUM reaches the trigger, a_w the share of those maxima in the mask, tau the share the
screen leaves; code/chance_expectation.py reads exactly those columns).  The OTHER rule reads every
above-trigger cell.  The retained per-channel profiles (the cells extract's; star and the retained
control positions of every Class A census window) hold every cell, so the other rule is computed on
both sides alike, with the production mask module and the production screen
(r36inputs/anycell_r36.json, frozen by r36inputs/anycell_extract_r36.py; an event is a maximal run of
adjacent above-trigger channels at its largest channel, the cells extract's adopted rule):
  (B) a window counts once if ANY of its above-trigger cells is unattributed and unscreened;
  (A) every unattributed, unscreened above-trigger cell counts.
Expected: the production per-window expectation (deposited resampling, rebuilt draw for draw by
zdeposit_code/chance_expectation.py from chance_resample_r30.json) plus the control positions' extra
per exceedance (pooled over the retained exceedances, redrawn binomially in every resampling) times the
trigger-rate sum.  Secondary cells exist only where the maximum reaches the trigger (X3), so the extra
is conditional on an exceedance exactly.
(R1-1) beta Pic: CO crossings in all, those above every control, those placed at the star.
(R1-2) the Bonferroni product printed with the digits that make it close, and the "about" form.
(R1-3) the injected carriers drift linearly in each block (the deposited injectors), and the span over
which the track must stay straight: first to last integration searched, per Class A window.

ASSERTIONS (each driven, `--drive N`; a drive writes nothing):
  X1  the primary rule rebuilt from the profiles is the production one: control exceedances / in mask /
      screened only = the resampling export's; the star's counted maxima = chance_v414's observed rows;
      the rebuilt P = chance_v414's \CeProbNull value bit for bit (drive 1: the mask lost on the control
      side; drive 2: one counted star maximum lost)
  X2  decomposition: (B) = primary + windows whose maximum is not counted but a secondary is; (A) =
      primary + every counted secondary; the star's secondaries are cells_v416's (\CkNSecondary,
      \CkNSecUnattr) (drive 3)
  X3  no secondary in a window whose maximum is below the trigger, on either side, and every star
      extra lies in a census window of the comparison (not the flagged block, not uncatalogued)
      (drive 4)
  X4  the verdict word: "below"/"above" the level only if the UNROUNDED x2 P lies beyond it by more than
      four Monte Carlo errors ("at" otherwise), "slightly" only where it prints as the level (drive 5)
  B1  beta Pic: CO crossings = \CsBpCoBlocks, above every control = \JqNBpCo, the rest = \JqNBpCoOut;
      localised + not localised + not fitted = all; every attributed census crossing not localised is
      beta Pic CO (the premise of Sec. 4.4's sentence); both transitions localised (drive 6)
  P1  digits: printed fine minimum x trials, at its places, IS the printed fine product, and each
      lies within half its last unit plus two Monte Carlo errors of its unrounded value (drive 7)
  P2  "about" only if both the unrounded product and trials x the printed minimum lie within a
      quarter of the level of it (drive 8)
  L1  every deposited injector (pipeline.tar: inject_vis_v401.py, which the campaign that sets P90 runs, and
      superseded/inject_vis_v399.py) draws ONE constant drift per tone and moves the tone as
      nu0 + drift * dt, dt from the window's first time (drive 9)
  L2  the span of every Class A window reproduces its catalogued drift-trial count where an exact span
      is on record, and lies in the grid's bracket where it is not (drive 10)

    python3 anycell_r36.py [--drive N]
"""
import collections
import csv
import io
import json
import math
import os
import re
import sys
import tarfile

import numpy as np
from scipy.special import gammainc

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import maskframe_v411 as mf                                      # noqa: E402
import calib_r15 as c15                                          # noqa: E402

ROUND = 3640
DRIVE = int(sys.argv[sys.argv.index('--drive') + 1]) if '--drive' in sys.argv else None
J = lambda p: json.load(open(os.path.join(HERE, p)))  # noqa: E731
OUT, FAIL, REC = {}, [], {}
WORD = ('no', 'one', 'two', 'three', 'four', 'five', 'six', 'seven', 'eight', 'nine', 'ten', 'eleven', 'twelve')
word = lambda k: WORD[k] if k < len(WORD) else '%d' % k  # noqa: E731
TRIG = 5.0
C, HALF = mf.C_KMS, mf.MASK_HALF_KMS


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


def edge_fmt(p, se, dp=2):
    """chancegrid_r34's (= the chance generator's) printing rule."""
    while dp > 0 and not (se < 0.25 * 10.0 ** (-dp)
                          and ('%.*f' % (dp, p - 2 * se) == '%.*f' % (dp, p) == '%.*f' % (dp, p + 2 * se))):
        dp -= 1
    assert se < 0.25 * 10.0 ** (-dp), (p, se)
    return '%.*f' % (dp, p)


# ============================================================ (R2-3) the counting rule
print('X (R2-3) the primary-cell rule and the any-cell rule, on both sides')
AC = J('r36inputs/anycell_r36.json')
RS = J('chance_resample_r30.json')
CV = J('chance_v414.json')
CELLS = {w['key']: w for w in J('r15inputs/cells/cells_extract_result.json')['windows']}
REST = np.array(sorted(v[0] for v in mf.TRANS.values()))
if DRIVE == 1:
    REST = REST[:0]                               # X1: the control side loses the mask
TLSPEC = J('r15inputs/calib/calspec_r15.json')
TL_RAD = 2 * float(TLSPEC['tsys_resolution_MHz'])          # chance_v414's radius (N_TSYS_CHAN = 2)
assert abs(TL_RAD - float(CV['telluric']['radius_MHz'])) < 1e-9
_lo = min(min(w['lo'], w['hi']) for w in AC['windows']) - 1.0
_hi = max(max(w['lo'], w['hi']) for w in AC['windows']) + 1.0
TL_ARR = np.array(sorted(x[0] for x in c15.telluric_lines(float(TLSPEC['t_atmosphere_K']), _lo, _hi)[1]))


def screened(f_topo):
    return bool(np.min(np.abs(TL_ARR - f_topo * 1e3)) <= TL_RAD)


def fstar(w, f_topo):
    return f_topo * (1.0 - w['v_bary'] / C) * (1.0 + w['v_sys'] / C)


def ctrl_masked(w, f_topo):
    fs = fstar(w, f_topo)
    return bool(np.any((fs >= REST * (1.0 - HALF / C)) & (fs <= REST * (1.0 + HALF / C))))


def star_masked(w, f_topo):
    """chance_v414's adopted_attributed: inside the searched mask and not a noted coincidence."""
    nm, _f0, dv = mf.nearest(fstar(w, f_topo))
    return bool(abs(dv) <= HALF and not mf.note_reason(nm, dv))


FLAG_EB = tv('BqFailBlock').replace('\\_', '_')
UNCAT = set(CV['uncatalogued']['stars'])
C_EXC = C_ATTR = C_TL = C_SECN = C_BX = 0
C_BELOW_SEC = 0
S_PRIM, S_SEC, S_SECN, S_BX, S_BELOW = [], [], [], [], 0
for w in AC['windows']:
    cw = CELLS[w['key']]
    assert cw['n_ctrl'] == len(w['ctrl']) and abs(cw['star_peak'] - w['star_peak']) < 1e-5, w['key']
    for c, cc in zip(w['ctrl'], cw['ctrl']):
        assert c['max_chan'] == cc['max_chan'] and abs(c['win_max'] - cc['win_max']) < 1e-5, w['key']
        if c['win_max'] < TRIG:
            C_BELOW_SEC += len(c['events'])
            continue
        assert len(c['events']) == cc['n_merge_adj'], w['key']
        ev = {e[0]: e for e in c['events']}
        mx = ev[c['max_chan']]
        att = ctrl_masked(w, mx[2])
        tl = (not att) and screened(mx[2])
        C_EXC += 1
        C_ATTR += att
        C_TL += tl
        cnt_sec = [e for k_, e in ev.items() if k_ != c['max_chan']
                   and not ctrl_masked(w, e[2]) and not screened(e[2])]
        C_SECN += len(cnt_sec)
        C_BX += int((att or tl) and len(cnt_sec) > 0)
    if w['star_peak'] < TRIG:
        S_BELOW += len(w['star_events'])
        continue
    assert len(w['star_events']) == cw['n_events'], w['key']
    if w['eb'] == FLAG_EB or w['star'] in UNCAT:
        continue
    pk = [e for e in w['star_events'] if e[0] == w['star_peak_chan']][0]
    p_cnt = (not star_masked(w, pk[2])) and not screened(pk[2])
    if DRIVE == 2 and p_cnt and not S_PRIM:
        p_cnt = False                             # X1: one counted maximum lost from the star side
    if p_cnt:
        S_PRIM.append((w, pk))
    sec = [e for e in w['star_events'] if e[0] != w['star_peak_chan']]
    S_SEC += [(w, e) for e in sec]
    secn = [(w, e) for e in sec if not star_masked(w, e[2]) and not screened(e[2])]
    S_SECN += secn
    if (not p_cnt) and secn:
        S_BX.append(w)
if DRIVE == 4:
    C_BELOW_SEC += 1                              # X3: a secondary where the maximum is below the trigger
_obs = {(r['eb'], round(float(r['freq']), 3)) for r in CV['observed_rows']}
_prim = {(w['eb'], round(e[2], 3)) for w, e in S_PRIM}
ck('X1 the primary rule rebuilt from the retained profiles is the production one: control exceedances, '
   'in mask, screened only, and the star\'s counted maxima are chance_v414\'s',
   (C_EXC, C_ATTR, C_TL) == (RS['n_exc_recorded'], RS['n_exc_in_mask'], RS['n_exc_telluric_only'])
   and _prim == _obs and len(S_PRIM) == CV['observed'] == int(tv('CeObs')),
   'ctrl %d/%d/%d vs %d/%d/%d; star %d vs %d observed (%d unmatched)'
   % (C_EXC, C_ATTR, C_TL, RS['n_exc_recorded'], RS['n_exc_in_mask'], RS['n_exc_telluric_only'],
      len(S_PRIM), CV['observed'], len(_prim ^ _obs)))

# the production resampling, rebuilt draw for draw from the current build's export
sys.path.insert(0, os.path.join(HERE, 'zdeposit_code'))
import chance_expectation as CE                                  # noqa: E402

_s = lambda v: '' if v is None else v  # noqa: E731
_TAB = {
    'chance_resampling_windows.csv': [dict(field_reading='whole_beam', block_order=w['block_order'],
                                           window_order=w['window_order'], n_ctrl=w['n_ctrl'],
                                           n_ctrl_trig=w['n_ctrl_trig'], attribution=w['attribution'],
                                           grid_mask_share=w['grid_mask_share'],
                                           n_exc_recorded=_s(w['n_exc_recorded']),
                                           n_exc_in_mask=_s(w['n_exc_in_mask'])) for w in RS['windows']],
    'chance_resampling_blocks.csv': [dict(field_reading='whole_beam', **b) for b in RS['attr_blocks']],
    'chance_resampling_parameters.csv': [dict(field_reading='whole_beam', parameter=k, value=v) for k, v in [
        ('seed', RS['seed']), ('n_realisations', RS['n_realisations']), ('n_batches', RS['n_batches']),
        ('n_boot', RS['n_boot']), ('n_observed', RS['n_observed']), ('n_reference_windows', RS['n_reference_windows']),
        ('scale', RS['scale']), ('alpha', RS['alpha']), ('coverage_pct', RS['coverage_pct']),
        ('n_exc_recorded', RS['n_exc_recorded']), ('n_exc_in_mask', RS['n_exc_in_mask']),
        ('n_exc_survive_mask', RS['n_exc_survive_mask']), ('n_exc_telluric_only', RS['n_exc_telluric_only']),
        ('n_holdout_blocks', RS['n_holdout_blocks']), ('transfer_band_lo', RS['transfer_band'][0]),
        ('transfer_band_hi', RS['transfer_band'][1]), ('near_n_star_events', RS['near_n_star_events']),
        ('near_n_windows', RS['near_n_windows']), ('near_n_control_events', RS['near_n_control_events']),
        ('near_n_control_positions', RS['near_n_control_positions']), ('max_ext_chunks', RS['max_ext_chunks']),
        ('a_share_estimator', RS['a_estimator']), ('shrink_prior_strength', RS['shrink_prior_strength'])]]}
CE.read = lambda path: _TAB[os.path.basename(path)]
RD = CE.Reading('-', 'whole_beam').run()
E_TRIG, E_CEN = RD.point()
LAM = RD.boot
P_PRIM = float(gammainc(RS['n_observed'], LAM).mean())
ck('X1b the deposited resampling, rebuilt here, gives chance_v414\'s expectation and P bit for bit',
   P_PRIM == float(RS['reference']['p_at_least_observed']) and abs(E_CEN - CV['e_chance']) < 1e-9
   and abs(E_TRIG - RS['reference']['expectation_trigger']) < 1e-9,
   'P %.10f vs %.10f; N %.4f vs %.4f' % (P_PRIM, RS['reference']['p_at_least_observed'], E_CEN, CV['e_chance']))

N_SEC_STAR = len(S_SEC)
if DRIVE == 3:
    N_SEC_STAR -= 1                               # X2: the star's secondaries stop being cells_v416's
OBS_B = len(S_PRIM) + len(S_BX)
OBS_A = len(S_PRIM) + len(S_SECN)
ck('X2 the other rule decomposes: (B) = primary + windows with an uncounted maximum and a counted '
   'secondary, (A) = primary + every counted secondary; the star\'s secondaries are cells_v416\'s',
   OBS_B == len(S_PRIM) + len({id(w) for w in S_BX}) and OBS_A >= OBS_B >= len(S_PRIM)
   and N_SEC_STAR == int(tv('CkNSecondary')) and len(S_SECN) == int(tv('CkNSecUnattr'))
   and C_BX <= C_SECN,
   'star: %d sec, %d counted, %d window extras; ctrl: %d counted sec, %d window extras of %d exceedances'
   % (N_SEC_STAR, len(S_SECN), len(S_BX), C_SECN, C_BX, C_EXC))
ck('X3 no secondary cell where the window maximum is below the trigger (star and controls), and every '
   'star extra is in a census window of the comparison',
   C_BELOW_SEC == 0 and S_BELOW == 0
   and all(w['eb'] != FLAG_EB and w['star'] not in UNCAT for w, _e in S_SECN),
   'below-trigger secondaries: ctrl %d, star %d' % (C_BELOW_SEC, S_BELOW))

rng = np.random.default_rng(ROUND)
NB = RD.NBATCH
RES = {}
for nm, nobs, nx in (('win', OBS_B, C_BX), ('cell', OBS_A, C_SECN)):
    xs = rng.binomial(C_EXC, nx / float(C_EXC), LAM.size) / float(C_EXC)
    lam = LAM + E_TRIG * xs
    pt = gammainc(nobs, lam)
    bm = np.array([pt[RD.BATCH == k].mean() for k in range(NB)])
    se = float(bm.std(ddof=1) / math.sqrt(NB))
    p = float(pt.mean())
    ptn = gammainc(nobs, lam * RD.NEAR)
    RES[nm] = dict(obs=nobs, extra_ctrl=nx, exp=float(E_CEN + E_TRIG * nx / float(C_EXC)), p=p, se=se,
                   pr=edge_fmt(p, se, 3 if p < 0.1 else 2), p_near=float(ptn.mean()),
                   p_two=min(1.0, 2.0 * p))
    RES[nm]['pr_near'] = edge_fmt(RES[nm]['p_near'], float(np.array([ptn[RD.BATCH == k].mean() for k in range(NB)])
                                                           .std(ddof=1) / math.sqrt(NB)), 2)
    RES[nm]['pr_two'] = edge_fmt(RES[nm]['p_two'], 2 * se, 3 if RES[nm]['p_two'] < 0.1 else 2)
# the secondaries on their own: found at the star against the controls' expectation, same draws
_xs = rng.binomial(C_EXC, C_SECN / float(C_EXC), LAM.size) / float(C_EXC)
_ps = gammainc(len(S_SECN), E_TRIG * _xs) if S_SECN else np.ones(LAM.size)
P_SEC = float(_ps.mean())
SE_SEC = float(np.array([_ps[RD.BATCH == k].mean() for k in range(NB)]).std(ddof=1) / math.sqrt(NB))
ALPHA = float(RS['alpha'])
_clause = {}
for nm in ('win', 'cell'):
    # on the UNROUNDED x2 value with four Monte Carlo errors (as chancegrid G7): the printed value can sit AT the
    # level (0.046 -> 0.05) and must not decide the word
    p2, se2 = RES[nm]['p_two'], 2 * RES[nm]['se']
    _clause[nm] = 'below' if p2 + 4 * se2 < ALPHA else ('above' if p2 - 4 * se2 > ALPHA else 'at')
    if DRIVE == 5 and nm == 'win':
        _clause[nm] = 'below'                     # X4: "below" for a value above the level
    pr2 = RES[nm]['pr_two']
    RES[nm]['phrase_two'] = ('slightly %s %s' % (_clause[nm], pr2) if float(pr2) == ALPHA and _clause[nm] != 'at'
                             else pr2)
ck('X4 each rule\'s verdict word (x2 for the choice of rule) follows its unrounded P against the level by more '
   'than four Monte Carlo errors, and "slightly" is used only where the value prints as the level',
   all((_clause[nm] == 'below') == (RES[nm]['p_two'] + 8 * RES[nm]['se'] < ALPHA)
       and (_clause[nm] == 'above') == (RES[nm]['p_two'] - 8 * RES[nm]['se'] > ALPHA) for nm in RES)
   and all(('slightly' in RES[nm]['phrase_two']) == (float(RES[nm]['pr_two']) == ALPHA and _clause[nm] != 'at')
           for nm in RES),
   '; '.join('%s %d vs %.2f P %s (x2 %.4f+-%.4f %r)' % (k, v['obs'], v['exp'], v['pr'], v['p_two'], 2 * v['se'],
                                                        v['phrase_two']) for k, v in RES.items()))
m('AcRulePrimary', 'the largest cell of each window')
m('AcCtrlExc', '%d' % C_EXC)
m('AcStarSecN', '%d' % len(S_SECN))
m('AcStarSecNWord', word(len(S_SECN)))
m('AcCtrlSecN', '%d' % C_SECN)
m('AcCtrlSecNWord', word(C_SECN))
m('AcSecExp', '%.1f' % (E_TRIG * C_SECN / float(C_EXC)))
m('AcProbSec', edge_fmt(P_SEC, SE_SEC, 4))
m('AcStarWinX', '%d' % len(S_BX))
m('AcStarWinXWord', word(len(S_BX)))
m('AcCtrlWinX', '%d' % C_BX)
m('AcObsWin', '%d' % RES['win']['obs'])
m('AcExpWin', '%.1f' % RES['win']['exp'])
m('AcProbWin', RES['win']['pr'])
m('AcProbWinTwo', RES['win']['pr_two'])
m('AcProbWinNear', RES['win']['pr_near'])
m('AcExpWinNear', '%.1f' % (RES['win']['exp'] * RD.NEAR))
m('AcObsCell', '%d' % RES['cell']['obs'])
m('AcExpCell', '%.1f' % RES['cell']['exp'])
m('AcProbCell', RES['cell']['pr'])
m('AcProbCellTwo', RES['cell']['pr_two'])
m('AcProbCellNear', RES['cell']['pr_near'])
m('AcExpCellNear', '%.1f' % (RES['cell']['exp'] * RD.NEAR))
m('AcCellVerdict', _clause['cell'])
m('AcWinVerdict', _clause['win'])
m('AcProbCellTwoPhrase', RES['cell']['phrase_two'])
# ★ r36 integrator (fresh read A2): three counting rules are shown on the page, so the allowance is stated both ways --
#   doubled for the choice between the largest cell and every cell, and trebled for all three rules compared (the
#   analogue of chancegrid's x4 over every combination examined).  X5: the x3 value is three times the unrounded
#   P (capped at 1), printed under the edge rule, and never below the x2 value; drive 11 prints the x2 value as x3.
_p3 = min(1.0, 3.0 * RES['cell']['p'])
_pr3 = edge_fmt(_p3, 3 * RES['cell']['se'], 3 if _p3 < 0.1 else 2)
if DRIVE == 11:
    _pr3 = RES['cell']['pr_two']
ck('X5 the every-cell P trebled for the three rules compared is three times the unrounded P, printed at its own '
   'precision, and it is not below the doubled value',
   abs(float(_pr3) - _p3) <= 0.5 * 10 ** -(len(_pr3.split('.')[1]) if '.' in _pr3 else 0) + 3 * RES['cell']['se'] + 1e-12
   and float(_pr3) >= float(RES['cell']['pr_two']) and _pr3 != RES['cell']['pr_two'],
   'x3 %.4f printed %s; x2 printed %s' % (_p3, _pr3, RES['cell']['pr_two']))
m('AcProbCellThree', _pr3)
m('AcProbWinTwoPhrase', RES['win']['phrase_two'])
REC['anycell'] = dict(res=RES, ctrl=dict(exc=C_EXC, attr=C_ATTR, tl_only=C_TL, sec_counted=C_SECN, win_extra=C_BX),
                      star=dict(primary=len(S_PRIM), sec=N_SEC_STAR, sec_counted=[(w['star'], w['eb'], e[2], e[1])
                                                                               for w, e in S_SECN],
                                win_extra=[(w['star'], w['eb']) for w in S_BX]),
                      e_trig=E_TRIG, e_cen=E_CEN, p_primary=P_PRIM, p_sec=P_SEC, p_sec_se=SE_SEC, near=RD.NEAR)

# ============================================================ (R1-1) beta Pic
print('B (R1-1) beta Pic: in all, above every control, placed at the star')
JX = J('jx_r35.json')
LED = J('ledger.json')['rows']
_isbp = lambda s: s.replace(' ', '').lower() in ('betapic', 'betpic', 'betapictoris')  # noqa: E731
BP = [r for r in LED if _isbp(r['star']) and r['attributed']]
_nl = [x for x in JX['not_localised'] if x['attributed']]
if DRIVE == 6:
    _nl = _nl + [dict(star='HD 48370', eb='X', nu=230.5, attributed=True)]
_key = lambda eb, f: (eb, round(float(f), 3))  # noqa: E731
_nlk = {_key(x['eb'], x['nu']) for x in _nl if _isbp(x['star'])}
_ufk = {_key(x['eb'], x['nu']) for x in JX['unfitted'] if x['attributed'] and _isbp(x['star'])}
_loc = [r for r in BP if _key(r['eb'], r['freq']) not in _nlk | _ufk]
_tr = lambda f: 'CO(1-0)' if float(f) < 150 else 'CO(2-1)'  # noqa: E731
ck('B1 beta Pic: CO crossings = \\CsBpCoBlocks, above every control = \\JqNBpCo, the rest = \\JqNBpCoOut; '
   'localised + not localised + not fitted = all; every attributed census crossing not localised is beta Pic '
   'CO; both transitions are localised',
   len(BP) == int(tv('CsBpCoBlocks')) == JX['stage']['n_bp'] + len(JX['stage']['bp_outranked'])
   and JX['stage']['n_bp'] == int(tv('JqNBpCo')) and len(JX['stage']['bp_outranked']) == int(tv('JqNBpCoOut'))
   and len(_loc) + len(_nlk) + len(_ufk) == len(BP) and all(_isbp(x['star']) for x in _nl)
   and len(_nl) == int(tv('JqNNotLocCo')) and len({_tr(r['freq']) for r in _loc}) == 2,
   '%d CO, %d above, %d localised (%s), %d not, %d not fitted'
   % (len(BP), JX['stage']['n_bp'], len(_loc), sorted(collections.Counter(_tr(r['freq']) for r in _loc).items()),
      len(_nlk), len(_ufk)))
m('AcBpNCoWord', word(len(BP)))
m('AcBpNLocal', '%d' % len(_loc))
m('AcBpNLocalWord', word(len(_loc)))
m('AcBpNNotLocWord', word(len(_nlk)))
m('AcBpNUnfitWord', word(len(_ufk)))

# ============================================================ (R1-2) the Bonferroni digits
print('P (R1-2) the corrected grid minimum, printed so that it closes')
CG = J('chancegrid_r34.json')
_c = CG['cells'][CG['min_cell'] + '_1']
NT = int(CG['n_trial'])
P_MIN, SE_MIN, P_B, SE_B = float(_c['p']), float(_c['se']), float(CG['p_bonf']), float(CG['p_bonf_se'])
assert abs(P_B - NT * P_MIN) < 1e-12 and int(tv('CgNTrial')) == NT
MINF = '%.4f' % P_MIN                     # three significant figures of the minimum
BONF = '%.3f' % (NT * float(MINF))        # the reader's product, at the places it carries
if DRIVE == 7:
    BONF = '%.3f' % (NT * float(tv('CgMinProb')))
_okf = lambda pr, p, se: abs(float(pr) - p) <= 0.5 * 10.0 ** (-len(pr.split('.')[1])) + 2 * se  # noqa: E731
ck('P1 the fine minimum x %d at its places is the printed fine product, and each lies within half its last unit '
   'plus two Monte Carlo errors of its unrounded value' % NT,
   BONF == '%.3f' % (NT * float(MINF)) and _okf(MINF, P_MIN, SE_MIN) and _okf(BONF, P_B, SE_B),
   '%s x %d = %s (unrounded %.5f +- %.5f, %.5f +- %.5f)' % (MINF, NT, BONF, P_MIN, SE_MIN, P_B, SE_B))
_prod_printed = NT * float(tv('CgMinProb'))
_about = abs(P_B - ALPHA) < 0.25 * ALPHA and abs(_prod_printed - ALPHA) < 0.25 * ALPHA and P_B > ALPHA
ABOUT = 'about %s' % ('%.2f' % ALPHA) if (_about or DRIVE == 8) else '%s' % tv('CgBonfProb')
if DRIVE == 8:
    P_B_CHECK = 2 * ALPHA
else:
    P_B_CHECK = P_B
ck('P2 "about" the level only if the unrounded product and %d x the printed minimum both lie within a quarter '
   'of the level of it' % NT,
   (not ABOUT.startswith('about')) or (abs(P_B_CHECK - ALPHA) < 0.25 * ALPHA
                                       and abs(_prod_printed - ALPHA) < 0.25 * ALPHA),
   '%r: %.4f and %.3f against %.2f' % (ABOUT, P_B_CHECK, _prod_printed, ALPHA))
m('AcMinProbFine', MINF)
m('AcBonfProbFine', BONF)
m('AcBonfAbout', ABOUT)

# ============================================================ (R1-3) the straight track
print('L (R1-3) the injected carriers drift linearly; the span the track must stay straight over')
TAR = tarfile.open(os.path.join(HERE, 'r30inputs/20261104/pipeline.tar'))
_inj = [n for n in TAR.getnames() if re.search(r'(^|/)inject_vis_v\d+\.py$', n)]
_law = {}
for n in _inj:
    s = TAR.extractfile(n).read().decode()
    if DRIVE == 9 and n == _inj[0]:
        s = s.replace('nu_row = nu0 + drift * dt', 'nu_row = nu0 + drift * dt + 0.5 * ddot * dt ** 2')
    _law[n] = (len(re.findall(r'^\s*nu_row\s*=\s*nu0\s*\+\s*drift\s*\*\s*dt\s*(#.*)?$', s, re.M)),
               len(re.findall(r'nu_row\s*=', s)), bool(re.search(r'dt\s*=\s*times\s*-\s*times\.min\(\)', s)),
               len(re.findall(r'drift\s*=\s*float\(rng\.uniform\(-drift_max,\s*drift_max\)\)', s)))
ck('L1 every deposited injector moves each tone as nu0 + drift * dt (one law, dt from the window\'s first time) '
   'with ONE drift drawn per tone',
   len(_inj) >= 2 and all(v == (1, 1, True, 1) for v in _law.values()), str(_law))
SW = list(csv.DictReader(open(os.path.join(HERE, 'per_target_results_v3.99.csv'))))
SWA = [r for r in SW if r.get('search_class') == 'A']
INV = collections.defaultdict(list)
for x in J('pbaudit_v408/inv_products.json')['recs']:
    INV[(x['eb'], round(min(x['freq_lo_GHz'], x['freq_hi_GHz']), 3))].append(x['time_span_s'])
DIV = float(re.search(r'^DRIFT_STEP_DIV\s*=\s*([0-9.]+)', open(os.path.join(HERE, 'localnull_code/validate_tstar.py'))
                      .read(), re.M).group(1))
SPAN, NEX, BAD = [], 0, []
for r in SWA:
    n, dm, cw = int(float(r['n_drift_trials'])), float(r['drift_max_Hz_s']), float(r['chanw_Hz'])
    lo, hi = cw * (n - 2) / (2 * dm * DIV), cw * (n - 1) / (2 * dm * DIV)
    ex = None
    for sp in INV.get((r['eb'], round(min(float(r['flo_GHz']), float(r['fhi_GHz'])), 3)), []):
        dd = cw / max(sp, 1.0) / DIV
        if len(np.arange(-dm, dm + dd, dd)) == n:
            ex = sp
    if DRIVE == 10 and ex is not None and not BAD and NEX == 0:
        ex = hi * 1.5
    if ex is not None:
        NEX += 1
        if not (lo - 1e-6 <= ex <= hi + 1e-6):
            BAD.append((r['eb'], ex, lo, hi))
        SPAN.append((ex, ex))
    else:
        SPAN.append((lo, hi))
_smin = min(SPAN, key=lambda t: t[1])
_smax = max(SPAN, key=lambda t: t[0])
_med = (float(np.median([t[0] for t in SPAN])), float(np.median([t[1] for t in SPAN])))
TRLO = '%.0f' % _smin[1]                                   # seconds
TRHI = '%.1f' % (_smax[0] / 3600.0)                        # hours
TRMED = '%.0f' % (_med[0] / 60.0)                          # minutes
ck('L2 every Class A window\'s span reproduces its drift-trial count where an exact span is on record and lies in '
   'its grid bracket where not; the printed extremes and median are the same at both ends of every bracket',
   not BAD and NEX > 0.8 * len(SPAN) and TRLO == '%.0f' % _smin[0] and TRHI == '%.1f' % (_smax[1] / 3600.0)
   and TRMED == '%.0f' % (_med[1] / 60.0) and len(SPAN) == int(tv('CeNWin')),
   '%d windows, %d exact, span %s s to %s h, median %s min; bad %s' % (len(SPAN), NEX, TRLO, TRHI, TRMED, BAD[:2]))
m('AcTrackLoS', TRLO)
m('AcTrackHiH', TRHI)
m('AcTrackMedMin', TRMED)
REC['track'] = dict(n=len(SPAN), n_exact=NEX, lo=_smin, hi=_smax, median=_med, injectors=_law)

# ====================================================================== write
if FAIL:
    print('\nFAILED: %s' % ', '.join(FAIL))
    sys.exit(1)
if DRIVE is not None:
    print('anycell_r36: drive %d passed every check -- it did NOT fire' % DRIVE)
    sys.exit(0)
with open(os.path.join(HERE, 'numbers/survey_numbers_round3640.tex'), 'w') as fh:
    fh.write('%% GENERATED by anycell_r36.py (round %d) -- do not hand-edit.\n' % ROUND)
    for k in sorted(OUT):
        fh.write('\\newcommand{\\%s}{%s}\n' % (k, OUT[k]))
json.dump(dict(generated_by='anycell_r36.py', round=ROUND, **REC), open(os.path.join(HERE, 'anycell_r36.json'), 'w'),
          indent=1, default=float)
print('anycell_r36: %d macros -> numbers/survey_numbers_round3640.tex' % len(OUT))
