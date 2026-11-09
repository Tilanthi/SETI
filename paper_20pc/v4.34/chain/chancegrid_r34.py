#!/usr/bin/env python3
r"""Round 3420: THE POST HOC CHOICES OF THE CHANCE COMPARISON CORRECTED ONE AT
A TIME AND TOGETHER, THE RESERVED HOLD-OUT SET BESIDE THEM, AND THE ATTRIBUTED
SHARE a_w NOT POOLED.

(R2-2)  Two choices were made after the crossings had been seen: the field the
statistic is read over (the whole primary beam, adopted, or the one field entry
whose phase centre lies nearest the star) and whether sulphur monoxide is in the
line mask.  A third quantity, the factor \CeNear by which a star reaches the
level just below the trigger more often than its own controls, is a measured
transfer applied as a sensitivity check.  This generator lays out all eight
cells {field} x {mask} x {transfer applied or not} from the SAME chance
generator (chance_v414.py, the production run and its --field / --mask runs,
plus the one combination no other generator runs, --field narrow --mask noso),
prints the observed count, the expectation and P(N >= observed) for each, and
corrects the smallest P for the number of choices.

WHY x4 AND NOT x8.  The transfer is one measured number, identical in every
reading (it is read from the census ladder, which neither the field nor the
mask changes: G2), and it is >= 1.  A Poisson tail P(N >= k | lambda) rises
with lambda, so applying a factor >= 1 can only RAISE the probability: in every
one of the four (field, mask) readings the transferred cell has the larger P
(G2 asserts it, cell by cell, on the unrounded values).  The event "the
smallest of the eight P is below alpha" is therefore the same event as "the
smallest of the four untransferred P is below alpha", and the Bonferroni union
bound over it needs four terms, not eight.  The factor is a bound on how far a
star can exceed its controls, not a choice that could have been made to
lower P.

(R2-2, the hold-out)  The reserved hold-out (77 blocks set aside by the
identifier rule committed 2026-09-14) is compared separately: its unattributed
crossings in the fine-resolution windows against the expectation built from
those windows' own control positions, with the census's measured attributed
share and atmospheric share carried over (the hold-out has no retained control
profiles of its own) and the same block resampling.  H3: no hold-out
disposition rests on SO (the one attribution is CO; every unattributed one lies
farther than the mask half-width from any listed transition), so the later
decision on SO moves none of them.  When the hold-out crossings were first
examined relative to the mask is a matter of record, not of code: see
referee_r34/N2_chance.md.

(R2-5)  The adopted a_w is ONE share pooled over every retained control
exceedance.  chance_v414.py --ashare strat measures it separately above and at
or below the median grid share of masked channels; --ashare shrink per window,
shrunk to the pooled share with the beta-binomial prior strength of maximum
marginal likelihood.  The register's rule: adopt a variant as primary ONLY if
it moves the expectation by more than one event.  S3 is that rule, evaluated
on the stratified estimator the rule names; the per-window estimate is
reported beside it, with the homogeneous-share simulation (S4) that says
whether its move is larger than its own estimation noise.

Inputs: chance_v414.json (production), chance_v414_fieldnarrow.json
(fieldread_r23.py), chance_v414_masknoso.json (maskpost_r31.py),
chance_resample_r30.json, holdout_export_v381.json and the macro layer.  Runs
chance_v414.py three times (in parallel, ~2 min): --field narrow --mask noso,
--ashare strat, --ashare shrink.  Under --drive those runs are NOT repeated
(their JSONs from the last production run are read) and nothing production
reads is written.

    python3 chancegrid_r34.py [--drive N]
"""
import collections
import glob
import json
import math
import os
import re
import subprocess
import sys

import numpy as np
from scipy.special import betaln, gammainc

HERE = os.path.dirname(os.path.abspath(__file__))
ROUND = 3420
GEN = 'chance_v414.py'
SEED = 3420
NSIM = 1000

DRIVE = None
for _i, _a in enumerate(sys.argv):
    if _a == '--drive':
        DRIVE = int(sys.argv[_i + 1])

OUT_TEX = os.path.join(HERE, 'numbers/survey_numbers_round3420.tex' if DRIVE is None
                       else 'numbers/survey_numbers_round3420_drive%d.tex' % DRIVE)
OUT_TAB = os.path.join(HERE, 'tab_chancegrid_r34.tex' if DRIVE is None
                       else 'tab_chancegrid_r34_drive%d.tex' % DRIVE)
OUT_JSON = os.path.join(HERE, 'chancegrid_r34.json' if DRIVE is None
                        else 'chancegrid_r34_drive%d.json' % DRIVE)
OUT = []
fail = []


def m(name, val):
    assert name.isalpha(), name
    assert not any(x.startswith('\\newcommand{\\%s}' % name) for x in OUT), name
    OUT.append('\\newcommand{\\%s}{%s}' % (name, val))


def ck(label, cond, detail=''):
    print('  %-70s %s  %s' % (label[:70], 'PASS' if cond else 'FAIL', detail))
    if not cond:
        fail.append(label)


def texval(name):
    """The value the macro layer publishes, in \\input order (later wins)."""
    main = glob.glob(os.path.join(HERE, 'technosignatures_*.tex'))
    order = []
    if len(main) == 1:
        for ln in open(main[0], errors='ignore'):
            mm = re.match(r'\s*\\input\{(?:numbers/)?(survey_numbers[A-Za-z0-9_]*)\}', ln)
            if mm:
                order.append(mm.group(1) + '.tex')
    val = None
    for fn in order:
        p = os.path.join(HERE, 'numbers', fn)
        if not os.path.exists(p):
            continue
        for ln in open(p, errors='ignore'):
            for nm, vv in re.findall(r'\\(?:providecommand|renewcommand|newcommand)'
                                     r'\{?\\([A-Za-z]+)\}?\{([^{}]*)\}', ln):
                if nm == name and vv.strip():
                    val = vv.strip()
    assert val is not None, 'no generator publishes \\%s' % name
    return val


def edge_fmt(p, se, dp=2):
    """The chance generator's printing rule (Ruling 30 + R13(b)): drop a place
    until the Monte Carlo error is below a quarter of the last unit AND the
    value +- 2 se rounds to the same digits."""
    while dp > 0 and not (se < 0.25 * 10.0 ** (-dp)
                          and ('%.*f' % (dp, p - 2 * se) == '%.*f' % (dp, p)
                               == '%.*f' % (dp, p + 2 * se))):
        dp -= 1
    assert se < 0.25 * 10.0 ** (-dp), (p, se)
    return '%.*f' % (dp, p)


# =====================================================================
# the three runs no other generator makes
# =====================================================================
RUNS = {'fieldnarrow_masknoso': ['--field', 'narrow', '--mask', 'noso'],
        'asharestrat': ['--ashare', 'strat'],
        'ashareshrink': ['--ashare', 'shrink']}
if DRIVE is None:
    procs = {}
    for k, a in RUNS.items():
        t = os.path.join(HERE, 'chance_v414_%s.json' % k)
        if os.path.exists(t):
            os.remove(t)
        procs[k] = subprocess.Popen([sys.executable, os.path.join(HERE, GEN)] + a, cwd=HERE,
                                    stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    for k, p in procs.items():
        out = p.communicate()[0].decode(errors='replace')
        assert os.path.exists(os.path.join(HERE, 'chance_v414_%s.json' % k)), (
            '%s %s wrote nothing (rc %d)\n%s' % (GEN, ' '.join(RUNS[k]), p.returncode, out[-2000:]))


def load(sfx):
    return json.load(open(os.path.join(HERE, 'chance_v414%s.json' % sfx)))


J = {('W', 'S'): load(''), ('N', 'S'): load('_fieldnarrow'),
     ('W', 'O'): load('_masknoso'), ('N', 'O'): load('_fieldnarrow_masknoso')}
JS, JK = load('_asharestrat'), load('_ashareshrink')
RS = json.load(open(os.path.join(HERE, 'chance_resample_r30.json')))

# =====================================================================
# (R2-2) the eight cells
# =====================================================================
CELL = {}
for (f, k), d in J.items():
    mc = d['mc_report']
    CELL[(f, k, 1)] = dict(obs=d['observed'], exp=d['e_chance'],
                           p=mc['CeProbNull']['p'], se=mc['CeProbNull']['se'],
                           pr=mc['CeProbNull']['printed'])
    CELL[(f, k, 'st')] = dict(obs=d['observed'], exp=d['near_expectation'],
                              p=mc['CeProbNear']['p'], se=mc['CeProbNear']['se'],
                              pr=mc['CeProbNear']['printed'])
NEARS = {fk: d['near_ratio'] for fk, d in J.items()}
NEAR = NEARS[('W', 'S')]
if DRIVE is not None and DRIVE != 11:
    NSIM = 100                               # a drive aimed at another clause needs no full S4 run
if DRIVE == 1:
    CELL[('N', 'O', 1)]['exp'] += 0.5        # the combined cell stops reproducing its own record
if DRIVE == 2:
    CELL[('N', 'O', 'st')]['p'] = CELL[('N', 'O', 1)]['p'] - 0.01   # the transfer LOWERS a P
if DRIVE == 3:
    NEARS[('N', 'O')] = 0.98                 # a reading with its own, sub-unity transfer
if DRIVE == 6:
    J[('N', 'O')] = dict(J[('N', 'O')], observed=J[('N', 'S')]['observed'] - 1)   # SO removal un-attributes less

# G1 every cell already in print is reproduced from its own record, printed digits included
_pub = [(('W', 'S', 1), 'CeObs', 'CeExp', 'CeProbNull'),
        (('W', 'S', 'st'), None, 'CeExpNear', 'CeProbNear'),
        (('N', 'S', 1), 'FrNarrowObs', 'FrNarrowExp', 'FrNarrowProb'),
        (('W', 'O', 1), 'MkNoSOObs', 'MkNoSOExp', 'MkNoSOProb')]
_g1 = []
for key, mo, me, mp in _pub:
    c = CELL[key]
    _g1.append((mo is None or str(c['obs']) == texval(mo))
               and '%.1f' % c['exp'] == texval(me) and c['pr'] == texval(mp))
_jn = J[('N', 'O')]
_g1b = (abs(_jn['e_chance'] - CELL[('N', 'O', 1)]['exp']) < 1e-12
        and abs(_jn['near_expectation'] - CELL[('N', 'O', 'st')]['exp']) < 1e-12)
ck('G1 the four cells in print reproduce their published values to the printed digit, and the '
   'combined reading is its own record', all(_g1) and _g1b,
   '%s; combined %.4f/%.4f' % (_g1, CELL[('N', 'O', 1)]['exp'], _jn['e_chance']))

# G2 the transfer is one measured number >= 1 in every reading and raises every P
_g2 = (len({round(v, 12) for v in NEARS.values()}) == 1 and NEAR >= 1.0
       and all(CELL[(f, k, 'st')]['p'] >= CELL[(f, k, 1)]['p']
               and CELL[(f, k, 'st')]['exp'] >= CELL[(f, k, 1)]['exp']
               for f in 'WN' for k in 'SO'))
ck('G2 the stellar transfer is one number >= 1, the same in all four readings, and in each reading '
   'it raises the expectation and P -- so the minimum lies among the four untransferred cells '
   'and the correction is x4', _g2,
   'transfer %s; P %s' % (sorted({'%.4f' % v for v in NEARS.values()}),
                          ['%s%s %.4f/%.4f' % (f, k, CELL[(f, k, 1)]['p'], CELL[(f, k, 'st')]['p'])
                           for f in 'WN' for k in 'SO']))

# G3 the mask only removes and the narrower field is the other reading of the same windows
_g3 = all(J[(f, 'O')]['observed'] >= J[(f, 'S')]['observed']
          and J[(f, 'O')]['e_chance'] > J[(f, 'S')]['e_chance'] for f in 'WN') and all(
    d['n_win_A_reference'] == J[('W', 'S')]['n_win_A_reference'] for d in J.values())
ck('G3 without SO each field reading expects more and attributes no more, over one window set', _g3,
   '; '.join('%s: %d->%d, %.2f->%.2f' % (f, J[(f, 'S')]['observed'], J[(f, 'O')]['observed'],
                                         J[(f, 'S')]['e_chance'], J[(f, 'O')]['e_chance'])
             for f in 'WN'))

NTRIAL = 4
KMIN = min(((f, k) for f in 'WN' for k in 'SO'), key=lambda x: CELL[(x[0], x[1], 1)]['p'])
CMIN = CELL[(KMIN[0], KMIN[1], 1)]
P_BONF = min(1.0, NTRIAL * CMIN['p'])
SE_BONF = NTRIAL * CMIN['se']
PR_BONF = edge_fmt(P_BONF, SE_BONF)
ALPHA = float(texval('CeAlphaPct')) / 100.0
if DRIVE == 7:
    P_BONF = 2 * CMIN['p']                   # the field-only correction comes back
# G4 the printed corrected value is NTRIAL times the printed precision's minimum, above the level
ck('G4 the corrected smallest P is x%d the smallest of the four untransferred cells, printed by the '
   'chance generator\'s rule, and lies above the one-sided level the text states' % NTRIAL,
   P_BONF > ALPHA and float(PR_BONF) > ALPHA and float(PR_BONF) >= float(CMIN['pr'])
   and abs(P_BONF - NTRIAL * CMIN['p']) < 1e-12,
   'min %s%s P %.4f (+-%.4f, printed %s) -> x%d %.4f printed %s, level %.2f'
   % (KMIN[0], KMIN[1], CMIN['p'], CMIN['se'], CMIN['pr'], NTRIAL, P_BONF, PR_BONF, ALPHA))

# =====================================================================
# (R2-2) the reserved hold-out, compared on its own
# =====================================================================
HOL = json.load(open(os.path.join(HERE, 'holdout_export_v381.json')))
HOF = [r for r in HOL['rows'] if r['res'].startswith('fine')]
HO_TRIG = sum(1 for r in HOF if r.get('star_snr') not in (None, '')
              and float(r['star_snr']) >= 5.0)
HO_NX = int(texval('HoNCross'))
HO_UN = int(texval('HoNUnattr'))
HO_AT = int(texval('HoNAttr'))
HO_SC = int(texval('HoNScreen'))
A_POOL = RS['a_measured']
TL = RS['telluric_factor']


def _ctrl(r):
    v = r['ctrl_all']
    return np.asarray(json.loads(v) if isinstance(v, str) else v, float)


_hblk = collections.defaultdict(list)
for r in HOF:
    _hblk[r['eb']].append(_ctrl(r))
_heb = sorted(_hblk)
_hr = np.array([sum(float((v >= 5.0).mean()) for v in _hblk[e]) for e in _heb])
_hn = np.array([len(_hblk[e]) for e in _heb], float)
HO_EXP_TRIG = float(_hr.sum())
if DRIVE == 12:
    HO_EXP_TRIG *= 1.1                       # the hold-out read on other controls
HO_EXP = HO_EXP_TRIG * (1.0 - A_POOL) * TL
if DRIVE == 4:
    HO_UN = HO_UN + 1                        # an unattributed crossing appears from nowhere
_rng = np.random.default_rng(SEED)
_pk = _rng.integers(0, len(_heb), size=(200000, len(_heb)))
_lam = (_hr[_pk].sum(axis=1) / _hn[_pk].sum(axis=1)) * len(HOF) * (1.0 - A_POOL) * TL
_pv = gammainc(HO_UN, _lam)
HO_P = float(_pv.mean())
HO_SE = float(np.array([_pv[k::20].mean() for k in range(20)]).std(ddof=1) / math.sqrt(20))
HO_PR = edge_fmt(HO_P, HO_SE)
# H1 the observed side is the hold-out's own crossings and dispositions, and they are the fine triggers
ck('H1 the hold-out crossings are its fine-window triggers and partition into attributed, '
   'screened and unattributed', HO_NX == HO_TRIG == J[('W', 'S')]['transfer_obs']
   and HO_AT + HO_SC + HO_UN == HO_NX,
   '%d crossings, %d fine triggers (%s in chance_v414), %d attr + %d screen + %d unattr'
   % (HO_NX, HO_TRIG, J[('W', 'S')]['transfer_obs'], HO_AT, HO_SC, HO_UN))
# H2 the trigger expectation is the one the chance generator compares the reserved blocks on
ck('H2 the hold-out trigger expectation is the chance generator\'s own reserved-block figure',
   abs(HO_EXP_TRIG - J[('W', 'S')]['transfer_exp']) < 1e-9 and '%.1f' % HO_EXP_TRIG == texval('StHoExpFine'),
   '%.4f vs %.4f (\\StHoExpFine %s)' % (HO_EXP_TRIG, J[('W', 'S')]['transfer_exp'], texval('StHoExpFine')))

# H3 no hold-out disposition rests on SO: the attributed one is not an SO line, and every unattributed one lies
#    farther than the mask half-width from ANY listed transition, so adding or dropping SO moves none of them
_HT = [ln for ln in open(os.path.join(HERE, 'tab_holdout_v412.tex'), errors='ignore')
       if ln.count(' & ') >= 9 and ('attributed' in ln)]
_HR = [[c.strip() for c in ln.rstrip().rstrip('\\').split(' & ')] for ln in _HT]
_hdv = lambda c: float(c.replace('\\ensuremath{-}', '-').replace('$-$', '-'))
_hat = [r for r in _HR if r[-1].startswith('attributed')]
_hun = [r for r in _HR if r[-1].startswith('unattributed')]
if DRIVE == 13:
    _hat = [r[:4] + ['SO($8_{8}$--$7_{7}$)'] + r[5:] for r in _hat]     # the one attribution becomes an SO line
VH = float(texval('MaskHalfKms'))
HO_MINDV = min(abs(_hdv(r[5])) for r in _hun) if _hun else float('inf')
ck('H3 no hold-out disposition depends on SO: the attributed crossing is not an SO line and every unattributed '
   'one is farther than the half-width from any listed transition', len(_HR) == HO_NX
   and len(_hat) == HO_AT and len(_hun) == HO_UN + HO_SC
   and not any(r[4].startswith('SO') for r in _hat) and HO_MINDV > VH,
   '%d rows; attributed %s; nearest transition to an unattributed one %.1f km/s against %.0f'
   % (len(_HR), [r[4] for r in _hat], HO_MINDV, VH))

# =====================================================================
# (R2-5) the attributed share, stratified and per window
# =====================================================================
W = RS['windows']
_meas = [w for w in W if w['attribution'] == 'measured']


def nbar(a_of):
    return RS['scale'] * TL * sum(w['n_ctrl_trig'] / float(w['n_ctrl'])
                                  * (1.0 - (a_of(w) if w['attribution'] == 'measured'
                                            else w['grid_mask_share'])) for w in W)


N_POOL = nbar(lambda w: A_POOL)
_med = float(np.median([w['grid_mask_share'] for w in _meas]))
_st = {}
for s in ('lo', 'hi'):
    ws = [w for w in _meas if (w['grid_mask_share'] > _med) == (s == 'hi')]
    _st[s] = sum(w['n_exc_in_mask'] for w in ws) / float(sum(w['n_exc_recorded'] for w in ws))
N_STRAT = nbar(lambda w: _st['hi' if w['grid_mask_share'] > _med else 'lo'])
if DRIVE == 9:
    N_STRAT += 0.01                          # the arithmetic stops reproducing the generator's run
if DRIVE == 10:
    _st = {'hi': _st['lo'], 'lo': _st['hi']}  # the strata swapped
_n = np.array([w['n_exc_recorded'] for w in _meas], float)
_k = np.array([w['n_exc_in_mask'] for w in _meas], float)
_KG = np.logspace(-2, 4, 601)


def kfit(k, n):
    K = _KG[:, None]
    ll = (betaln(k[None, :] + K * A_POOL, (n - k)[None, :] + K * (1 - A_POOL))
          - betaln(K * A_POOL, K * (1 - A_POOL))).sum(axis=1)
    return float(_KG[int(np.argmax(ll))])


K_SH = kfit(_k, _n)
_ash = dict(zip([w['cat_index'] for w in _meas], (_k + K_SH * A_POOL) / (_n + K_SH)))
N_SHR = nbar(lambda w: _ash[w['cat_index']])
_ast = JS['ashare']
_ask = JK['ashare']
# S1 this file's own arithmetic reproduces the production expectation and both variant runs
ck('S1 the per-window arithmetic reproduces the adopted expectation and the two a_w runs of the '
   'chance generator (strata, shares, prior strength, expectation)',
   abs(N_POOL - J[('W', 'S')]['e_chance']) < 1e-9 and abs(N_STRAT - JS['e_chance']) < 1e-9
   and abs(N_SHR - JK['e_chance']) < 1e-9 and abs(_med - _ast['strat_median_grid_share']) < 1e-12
   and all(abs(_st[s] - _ast['strata'][s]['a']) < 1e-12 for s in _st)
   and abs(K_SH - _ask['shrink_prior_strength']) < 1e-12
   and sum(v['n_exc'] for v in _ast['strata'].values()) == RS['n_exc_recorded'],
   'pooled %.4f/%.4f strat %.4f/%.4f shrink %.4f/%.4f K %.3f'
   % (N_POOL, J[('W', 'S')]['e_chance'], N_STRAT, JS['e_chance'], N_SHR, JK['e_chance'], K_SH))
D_STRAT = JS['e_chance'] - J[('W', 'S')]['e_chance']
D_SHR = JK['e_chance'] - J[('W', 'S')]['e_chance']
if DRIVE == 5:
    D_STRAT = 1.5                            # the stratified share moves the expectation by > 1
# S2 the strata differ (the stratification is not vacuous) in the direction the masked fraction says
ck('S2 the share is larger in the windows with the larger masked fraction', _st['hi'] > _st['lo'],
   'a_hi %.3f (%d exc) a_lo %.3f (%d exc), median grid share %.4f'
   % (_st['hi'], _ast['strata']['hi']['n_exc'], _st['lo'], _ast['strata']['lo']['n_exc'], _med))
# S3 THE REGISTER'S RULE: the pooled share stays primary unless the stratified one moves N by > 1
ADOPT_STRAT = abs(D_STRAT) > 1.0
ck('S3 the register\'s rule: the stratified a_w moves the expectation by no more than one event, so '
   'the pooled share stays primary (if this fails the primary comparison must be re-based)',
   not ADOPT_STRAT, 'stratified %+.3f, per-window shrunk %+.3f' % (D_STRAT, D_SHR))
# S4 the per-window move against its own noise: the same estimator on shares drawn homogeneous
_g = np.random.default_rng(SEED + 1)
_ds = np.empty(NSIM)
_r = np.array([w['n_ctrl_trig'] / float(w['n_ctrl']) for w in _meas]) * RS['scale'] * TL
for j in range(NSIM):
    ks = _g.binomial(_n.astype(int), A_POOL)
    a_pool_s = ks.sum() / _n.sum()
    Ks = kfit(ks, _n)
    a_w = (ks + Ks * A_POOL) / (_n + Ks)
    _ds[j] = float(np.sum(_r * (a_pool_s - a_w))) + (1.0 if DRIVE == 11 else 0.0)
SH_P = float(np.mean(np.abs(_ds) >= abs(D_SHR)))
SH_SD = float(_ds.std())
ck('S4 the homogeneous-share simulation is centred on no move (the per-window estimator is not '
   'biased by construction)', abs(float(_ds.mean())) < 0.25,
   'mean %+.3f sd %.3f; observed %+.3f, |move| reached in %.4f of %d' % (
       float(_ds.mean()), SH_SD, D_SHR, SH_P, NSIM))

# =====================================================================
# macros and the table
# =====================================================================
_code = {('N', 'S', 'st'): 'NSSt', ('W', 'O', 'st'): 'WOSt', ('N', 'O', 1): 'NO',
         ('N', 'O', 'st'): 'NOSt'}
for key, c in _code.items():
    m('CgExp' + c, '%.1f' % CELL[key]['exp'])
    m('CgProb' + c, CELL[key]['pr'])
m('CgObsNO', '%d' % CELL[('N', 'O', 1)]['obs'])
m('CgNCell', '%d' % len(CELL))
m('CgNCellWord', 'eight')
m('CgNTrial', '%d' % NTRIAL)
m('CgNTrialWord', 'four')
# r34 (fresh read B4): the smallest P printed to the places at which ITS Monte Carlo error is stable (three, when the rule
# allows), so that "x4" closes on the page: 0.04 x 4 = 0.17 did not.  G6: the printed minimum times the trial count
# rounds to the printed corrected value.  Drive 14 prints the minimum at the cell's two places (the old form).
MINPR = edge_fmt(CMIN['p'], CMIN['se'], 3) if CMIN['p'] < 0.1 else CMIN['pr']
if DRIVE == 14:
    MINPR = CMIN['pr']
_dpb = len(PR_BONF.split('.')[1]) if '.' in PR_BONF else 0
ck('G6 the printed smallest P times the trial count rounds to the printed corrected P (the arithmetic a reader does '
   'closes)', '%.*f' % (_dpb, min(1.0, NTRIAL * float(MINPR))) == PR_BONF,
   '%s x %d = %.4f -> %s' % (MINPR, NTRIAL, NTRIAL * float(MINPR), PR_BONF))
m('CgMinProb', MINPR)
m('CgMinCell', {('W', 'S'): 'the adopted reading', ('N', 'S'): 'the nearest field with the mask',
                ('W', 'O'): 'the whole beam without SO',
                ('N', 'O'): 'the nearest field without SO'}[KMIN])
m('CgBonfProb', PR_BONF)
m('CgHoObs', '%d' % HO_UN)
m('CgHoExp', '%.1f' % HO_EXP)
m('CgHoProb', HO_PR)
m('CgHoNWin', '%d' % len(HOF))
m('CgHoMinDv', '%.0f' % HO_MINDV)
m('CgVerdictClause', ('so no combination departs from chance at the \\CeAlphaPct{} per cent level'
                      if P_BONF > ALPHA else 'below the \\CeAlphaPct{} per cent level'))
m('CgAwHi', '%.2f' % _st['hi'])
m('CgAwLo', '%.2f' % _st['lo'])
m('CgAwNExcHi', '%d' % _ast['strata']['hi']['n_exc'])
m('CgAwNExcLo', '%d' % _ast['strata']['lo']['n_exc'])
m('CgAwStratExp', '%.1f' % JS['e_chance'])
m('CgAwStratProb', JS['mc_report']['CeProbNull']['printed'])
m('CgAwShrExp', '%.1f' % JK['e_chance'])
m('CgAwShrProb', JK['mc_report']['CeProbNull']['printed'])
m('CgAwStratMove', '%.2f' % abs(D_STRAT))
m('CgAwShrMove', '%.1f' % abs(D_SHR))
m('CgAwShrSimP', '%.3f' % SH_P if SH_P >= 0.001 else '<0.001')
m('CgAwPrimary', 'pooled' if not ADOPT_STRAT else 'stratified')
m('CgAwStratClause', 'so the pooled share is kept' if not ADOPT_STRAT
  else 'a move of more than one crossing, so the two shares replace the pooled one')

_ce = {('W', 'S', 1): ('\\CeObs', '\\CeExp', '\\CeProbNull'),
       ('W', 'S', 'st'): ('\\CeObs', '\\CeExpNear', '\\CeProbNear'),
       ('N', 'S', 1): ('\\FrNarrowObs', '\\FrNarrowExp', '\\FrNarrowProb'),
       ('N', 'S', 'st'): ('\\FrNarrowObs', '\\CgExpNSSt', '\\CgProbNSSt'),
       ('W', 'O', 1): ('\\MkNoSOObs', '\\MkNoSOExp', '\\MkNoSOProb'),
       ('W', 'O', 'st'): ('\\MkNoSOObs', '\\CgExpWOSt', '\\CgProbWOSt'),
       ('N', 'O', 1): ('\\CgObsNO', '\\CgExpNO', '\\CgProbNO'),
       ('N', 'O', 'st'): ('\\CgObsNO', '\\CgExpNOSt', '\\CgProbNOSt')}
_fl = {'W': 'whole beam', 'N': 'nearest field'}
_ml = {'S': 'with SO', 'O': 'without SO'}
_ad = {('W', 'S'): ' (adopted)'}
T = ['%% GENERATED by chancegrid_r34.py (round %d) -- do not hand-edit.' % ROUND,
     r'\begin{tabular}{@{}llrrrrr@{}}', r'\hline',
     r'field & mask & $N_{\rm obs}$ & $\bar N$ & $P$ & $\bar N\times\CeNear$ & $P$ \\', r'\hline']
for f in 'WN':
    for k in 'SO':
        a, b = _ce[(f, k, 1)], _ce[(f, k, 'st')]
        T.append('%s & %s & %s & %s & %s & %s & %s \\\\'
                 % (_fl[f], _ml[k] + _ad.get((f, k), ''), a[0] + '{}', a[1] + '{}', a[2] + '{}', b[1] + '{}', b[2] + '{}'))
T += [r'\hline', r'\end{tabular}']
if DRIVE == 8:
    T.insert(-2, r'all & & 26 & & & & \\')   # a typed number in the table
# G5 the table prints every cell through the macro that carries its value, none typed
_tt = '\n'.join(T)
ck('G5 the table carries no typed number: every cell is a macro of this or an upstream generator',
   not re.search(r'(?<![\\A-Za-z{])\d', re.sub(r'\$[^$]*\$|%[^\n]*', '', _tt)) and len(
       re.findall(r'\\(?:Ce|Fr|Mk|Cg)[A-Za-z]+\{\}', _tt)) == 4 * 5,
   '%d macro cells' % len(re.findall(r'\\(?:Ce|Fr|Mk|Cg)[A-Za-z]+\{\}', _tt)))

if fail:
    print('\nFAILED: %s' % '; '.join(fail))
    raise SystemExit(1)

hdr = ['%% GENERATED by chancegrid_r34.py (round %d) -- do not hand-edit.' % ROUND,
       '% The chance comparison under the 2 x 2 post hoc choices (field, SO) with and',
       '% without the stellar transfer; the x4 correction; the hold-out on its own; a_w unpooled.']
open(OUT_TEX, 'w').write('\n'.join(hdr + sorted(OUT)) + '\n')
open(OUT_TAB, 'w').write(_tt + '\n')
json.dump(dict(round=ROUND, drive=DRIVE,
               cells={'%s%s_%s' % k: v for k, v in CELL.items()}, near=NEAR,
               min_cell=''.join(KMIN), n_trial=NTRIAL, p_bonf=P_BONF, p_bonf_se=SE_BONF,
               p_bonf_printed=PR_BONF,
               holdout=dict(n_fine=len(HOF), n_cross=HO_NX, n_unattr=HO_UN, exp_trig=HO_EXP_TRIG,
                            exp_unattr=HO_EXP, a_carried=A_POOL, tl_carried=TL, p=HO_P, se=HO_SE,
                            printed=HO_PR, n_blocks=len(_heb)),
               ashare=dict(pooled=dict(a=A_POOL, exp=N_POOL, p=J[('W', 'S')]['mc_report']['CeProbNull']),
                           strat=dict(median=_med, a=_st, exp=JS['e_chance'], move=D_STRAT,
                                      p=JS['mc_report']['CeProbNull']),
                           shrink=dict(K=K_SH, exp=JK['e_chance'], move=D_SHR,
                                       p=JK['mc_report']['CeProbNull'], sim_sd=SH_SD,
                                       sim_mean=float(_ds.mean()), sim_p=SH_P, nsim=NSIM),
                           primary='pooled' if not ADOPT_STRAT else 'stratified')),
          open(OUT_JSON, 'w'), indent=1, sort_keys=True)
print('chancegrid_r34: min P %s (%s%s) x%d -> %s; hold-out %d vs %.2f P %s; a_w strat %+.2f, '
      'shrink %+.2f (sim sd %.2f, p %.4f) -> %s'
      % (CMIN['pr'], KMIN[0], KMIN[1], NTRIAL, PR_BONF, HO_UN, HO_EXP, HO_PR, D_STRAT, D_SHR,
         SH_SD, SH_P, os.path.basename(OUT_TEX)))
