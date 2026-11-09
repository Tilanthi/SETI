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

(R2-5)  a_w per window, shrunk to the pooled share with the beta-binomial
prior strength of maximum marginal likelihood, is (since r35, the author's
decision A1) the PRIMARY estimator: the production run and every field / mask
run carry it, each measured on that reading's own exceedances, so every cell
of the grid uses its own per-window shares.  The pooled share is the check
(--ashare pooled; the production run also prints it on its own draws, and S1
asserts the two agree bit for bit); --ashare strat (above / at or below the
median grid share of masked channels) stays as a sensitivity.  S3 was the
register's rule (pooled stays primary unless the stratified share moves the
expectation by more than one event); it is RESTATED to the author's decision:
the production estimator is the per-window one and the pooled check is the
pooled run.  S4 (homogeneous-share simulation) still says whether the
per-window move is larger than the estimator's own noise.

(r35, A1, the hold-out)  The hold-out has no retained control profiles, so
it carries ONE share from the census: since r35 the per-window estimator's
EFFECTIVE share (the trigger-rate weighted mean of the per-window shares over
the census windows with profiles, chance_v414's a_effective; it is the pooled
share exactly when the shares are pooled), with the pooled share beside it as
the check, on the same block resamplings.

Inputs: chance_v414.json (production), chance_v414_fieldnarrow.json
(fieldread_r23.py), chance_v414_masknoso.json (maskpost_r31.py),
chance_resample_r30.json, holdout_export_v381.json and the macro layer.  Runs
chance_v414.py three times (in parallel, ~2 min): --field narrow --mask noso,
--ashare strat, --ashare pooled.  Under --drive those runs are NOT repeated
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
        'asharepooled': ['--ashare', 'pooled']}
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
JS, JP = load('_asharestrat'), load('_asharepooled')
JK = J[('W', 'S')]                           # r35 (A1): the production run IS the per-window estimator
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
    # r35: "to the printed digit" is read at the digits the publishing generator prints (fieldread_r23 prints a
    # P below 0.1 to three places when its error allows); the value at those places must be the macro's
    _tp = texval(mp)
    _dp = len(_tp.split('.')[1]) if '.' in _tp else 0
    _g1.append((mo is None or str(c['obs']) == texval(mo))
               and '%.1f' % c['exp'] == texval(me)
               and (c['pr'] == _tp or (_dp > len(c['pr'].split('.')[-1]) and '%.*f' % (_dp, c['p']) == _tp
                                       and c['se'] < 0.25 * 10.0 ** (-_dp))))
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
# r35: below 0.1 the corrected P prints to three places where its error allows (as the smallest P does); at
# 0.0544 +- 0.0001 the third place sits on the 0.0545 rounding edge, so the edge rule prints two (0.05)
PR_BONF = edge_fmt(P_BONF, SE_BONF, 3 if P_BONF < 0.1 else 2)
ALPHA = float(texval('CeAlphaPct')) / 100.0
if DRIVE == 7:
    P_BONF = 2 * CMIN['p']                   # the field-only correction comes back
# G4 the printed corrected value is NTRIAL times the printed precision's minimum, above the level
# r35: RESTATED (was: unrounded AND printed value above the level).  The corrected value can now print AS the level
# (0.0544 -> 0.05); the invariant -- it lies above the level, beyond its Monte Carlo error -- is asserted on the
# unrounded value with four of its standard errors, the printed one may not fall below the level, and the verdict
# clause has a branch of its own for this case (below).
ck('G4 the corrected smallest P is x%d the smallest of the four untransferred cells, printed by the '
   'chance generator\'s rule, and lies above the one-sided level the text states (unrounded, by more than four '
   'Monte Carlo errors; printed, not below it)' % NTRIAL,
   P_BONF > ALPHA + 4 * SE_BONF and float(PR_BONF) >= ALPHA and float(PR_BONF) >= float(CMIN['pr'])
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
A_EFF = RS['a_effective']                    # r35 (A1): what the hold-out carries
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
HO_EXP = HO_EXP_TRIG * (1.0 - A_EFF) * TL
HO_EXP_POOL = HO_EXP_TRIG * (1.0 - A_POOL) * TL
if DRIVE == 4:
    HO_UN = HO_UN + 1                        # an unattributed crossing appears from nowhere
_rng = np.random.default_rng(SEED)
_pk = _rng.integers(0, len(_heb), size=(200000, len(_heb)))
_lam0 = (_hr[_pk].sum(axis=1) / _hn[_pk].sum(axis=1)) * len(HOF)
_lam = _lam0 * (1.0 - A_EFF) * TL
_pv = gammainc(HO_UN, _lam)
HO_P = float(_pv.mean())
HO_SE = float(np.array([_pv[k::20].mean() for k in range(20)]).std(ddof=1) / math.sqrt(20))
HO_PR = edge_fmt(HO_P, HO_SE)
#: the pooled-share check, on the same block resamplings
_pvp = gammainc(HO_UN, _lam0 * (1.0 - A_POOL) * TL)
HO_P_POOL = float(_pvp.mean())
HO_SE_POOL = float(np.array([_pvp[k::20].mean() for k in range(20)]).std(ddof=1) / math.sqrt(20))
HO_PR_POOL = edge_fmt(HO_P_POOL, HO_SE_POOL)
if DRIVE == 15:
    A_EFF = A_POOL                           # the hold-out carries the pooled share as if it were the primary's
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
# H4 (r35, A1) the share the hold-out carries is the production estimator's effective share, recomputed here from the
#    per-window shares and control rates the production run deposits, and it is not the pooled one (unless they agree)
_rw = [w for w in RS['windows'] if w['attribution'] == 'measured']
_aeff = (sum(w['n_ctrl_trig'] / float(w['n_ctrl']) * w['a_share'] for w in _rw)
         / sum(w['n_ctrl_trig'] / float(w['n_ctrl']) for w in _rw))
ck('H4 the hold-out carries the census per-window estimator\'s effective share (trigger-rate weighted), recomputed '
   'from the deposited per-window shares, with the pooled share beside it as the check',
   RS['a_estimator'] == 'shrink' and abs(_aeff - A_EFF) < 1e-12 and abs(A_EFF - JK['ashare']['a_effective']) < 1e-12
   and (abs(A_EFF - A_POOL) > 1e-9 or RS['a_estimator'] == 'pooled'),
   'estimator %s; effective %.5f (recomputed %.5f), pooled %.5f; hold-out %.3f / pooled %.3f'
   % (RS['a_estimator'], A_EFF, _aeff, A_POOL, HO_EXP, HO_EXP_POOL))

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
N_PRIM = nbar(lambda w: w['a_share'])        # r35: the production record's own per-window shares
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
# S1 this file's own arithmetic reproduces the production (per-window) expectation and both a_w runs, and the
#    pooled check the production run prints on its own draws IS the pooled run (r35: restated, production = per window)
_pc = JK['ashare']['pooled_check']
_s1 = (abs(N_SHR - JK['e_chance']) < 1e-9 and abs(N_PRIM - JK['e_chance']) < 1e-9
       and all(abs(_ash[w['cat_index']] - w['a_share']) < 1e-12 for w in _meas)
       and abs(N_POOL - JP['e_chance']) < 1e-9 and abs(N_STRAT - JS['e_chance']) < 1e-9
       and abs(_med - _ast['strat_median_grid_share']) < 1e-12
       and all(abs(_st[s] - _ast['strata'][s]['a']) < 1e-12 for s in _st)
       and abs(K_SH - _ask['shrink_prior_strength']) < 1e-12
       and sum(v['n_exc'] for v in _ast['strata'].values()) == RS['n_exc_recorded']
       and _pc['e_chance'] == JP['e_chance']
       and _pc['p_at_least_observed'] == JP['p_at_least_observed_control_only']
       and _pc['added_population_limit_exact'] == JP['added_population_limit_exact'])
ck('S1 the per-window arithmetic reproduces the adopted (per-window) expectation and the pooled and stratified '
   'runs, and the pooled check printed by the production run is the pooled run bit for bit',
   _s1, 'per-window %.4f/%.4f (record shares %.4f) pooled %.4f/%.4f strat %.4f/%.4f K %.3f; check P %.6f vs run %.6f'
   % (N_SHR, JK['e_chance'], N_PRIM, N_POOL, JP['e_chance'], N_STRAT, JS['e_chance'], K_SH,
      _pc['p_at_least_observed'], JP['p_at_least_observed_control_only']))
D_STRAT = JS['e_chance'] - JP['e_chance']   # the stratified share against the pooled one it splits
D_SHR = JK['e_chance'] - JP['e_chance']     # the per-window (primary) against the pooled check
PRIMARY = JK['ashare']['variant']
if DRIVE == 5:
    PRIMARY = 'pooled'                       # the production run is not the estimator the author adopted
# S2 the strata differ (the stratification is not vacuous) in the direction the masked fraction says
ck('S2 the share is larger in the windows with the larger masked fraction', _st['hi'] > _st['lo'],
   'a_hi %.3f (%d exc) a_lo %.3f (%d exc), median grid share %.4f'
   % (_st['hi'], _ast['strata']['hi']['n_exc'], _st['lo'], _ast['strata']['lo']['n_exc'], _med))
# S3 (restated r35: was the register's rule "pooled stays primary unless the stratified a_w moves N by > 1"; the
#    author decided, register A1, 2026-11-09, that the per-window estimator is primary) THE PRODUCTION ESTIMATOR IS THE
#    ONE THE AUTHOR ADOPTED and every grid reading carries it; the pooled check is the pooled run.
ADOPT_STRAT = False
_prim_all = all(d.get('ashare', {}).get('variant') == 'shrink' for d in J.values())
ck('S3 the author\'s decision (A1): the production chance estimator is the per-window shrunk share, in every '
   'reading of the grid, and the pooled share is the check',
   PRIMARY == 'shrink' and _prim_all and JP['ashare']['variant'] == 'pooled',
   'production %s, grid readings %s, check %s; per-window vs pooled %+.3f, stratified vs pooled %+.3f'
   % (PRIMARY, [d.get('ashare', {}).get('variant') for d in J.values()], JP['ashare']['variant'], D_SHR, D_STRAT))
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
# r35: RESTATED (was: the product of the printed minimum and the trial count, rounded, IS the printed corrected P).
# At three places the minimum's own rounding (half a unit, x NTRIAL) can exceed the corrected value's last unit
# (0.014 x 4 = 0.056 against 0.0544 -> 0.054), and four places are not stable; the invariant -- the arithmetic a
# reader does closes within the rounding of the number he multiplies -- is asserted instead, and the exact
# closure is still required whenever the printed minimum carries enough places for it.
_dpm = len(MINPR.split('.')[1]) if '.' in MINPR else 0
_half = 0.5 * 10.0 ** (-_dpm)
_g6 = ('%.*f' % (_dpb, min(1.0, NTRIAL * float(MINPR))) == PR_BONF
       or (NTRIAL * (float(MINPR) - _half) <= float(PR_BONF) + 0.5 * 10.0 ** (-_dpb)
           and float(PR_BONF) - 0.5 * 10.0 ** (-_dpb) <= NTRIAL * (float(MINPR) + _half)
           # only when both numbers already carry every place their errors allow
           and MINPR == edge_fmt(CMIN['p'], CMIN['se'], 4)
           and PR_BONF == edge_fmt(P_BONF, SE_BONF, 4)))
ck('G6 the printed smallest P times the trial count gives the printed corrected P within the rounding of the '
   'printed smallest P (the arithmetic a reader does closes)', _g6,
   '%s x %d = %.4f (range %.4f-%.4f) -> %s' % (MINPR, NTRIAL, NTRIAL * float(MINPR), NTRIAL * (float(MINPR) - _half),
                                               NTRIAL * (float(MINPR) + _half), PR_BONF))
m('CgMinProb', MINPR)
m('CgMinCell', {('W', 'S'): 'the adopted reading', ('N', 'S'): 'the nearest field with the mask',
                ('W', 'O'): 'the whole beam without SO',
                ('N', 'O'): 'the nearest field without SO'}[KMIN])
m('CgBonfProb', PR_BONF)
m('CgHoObs', '%d' % HO_UN)
m('CgHoExp', '%.1f' % HO_EXP)
m('CgHoProb', HO_PR)
m('CgHoExpPool', '%.1f' % HO_EXP_POOL)
m('CgHoProbPool', HO_PR_POOL)
m('CgHoNWin', '%d' % len(HOF))
m('CgHoMinDv', '%.0f' % HO_MINDV)
# r35 (integrator): the corrected minimum as a PHRASE and a short verdict.  When the edge rule prints the corrected
# value AS the level (0.0544 -> 0.05) the number alone would read as "at the level"; the phrase says "slightly above"
# it, which G7 allows only when the unrounded value lies above the level by more than four Monte Carlo errors.
_AT_LEVEL = float(PR_BONF) == ALPHA
_PHRASE = ('slightly above %s' % PR_BONF) if (_AT_LEVEL and P_BONF > ALPHA) else PR_BONF
if DRIVE == 16:
    _PHRASE = 'slightly above %s' % PR_BONF   # the phrase without the margin it needs
    P_BONF_G7 = ALPHA + SE_BONF
else:
    P_BONF_G7 = P_BONF
ck('G7 the corrected minimum is called "slightly above" the level only when it prints as the level and its '
   'unrounded value exceeds the level by more than four Monte Carlo errors',
   (not _PHRASE.startswith('slightly above')) or (_AT_LEVEL and P_BONF_G7 > ALPHA + 4 * SE_BONF),
   'phrase %r, printed %s, unrounded %.4f +- %.4f, level %.2f' % (_PHRASE, PR_BONF, P_BONF_G7, SE_BONF, ALPHA))
m('CgBonfPhrase', _PHRASE)
m('CgVerdictClause', ('so no combination departs from chance at the \\CeAlphaPct{} per cent level'
                      if P_BONF >= 2 * ALPHA else
                      'so no combination departs from chance at the \\CeAlphaPct{} per cent level, although the '
                      'least favourable comes close' if P_BONF > ALPHA else
                      'so the least favourable combination departs from chance at the \\CeAlphaPct{} per cent level'))
m('CgAwHi', '%.2f' % _st['hi'])
m('CgAwLo', '%.2f' % _st['lo'])
m('CgAwNExcHi', '%d' % _ast['strata']['hi']['n_exc'])
m('CgAwNExcLo', '%d' % _ast['strata']['lo']['n_exc'])
m('CgAwStratExp', '%.1f' % JS['e_chance'])
m('CgAwStratProb', JS['mc_report']['CeProbNull']['printed'])
m('CgAwStratMove', '%.2f' % abs(D_STRAT))
m('CgAwShrMove', '%.1f' % abs(D_SHR))
m('CgAwShrSimP', '%.3f' % SH_P if SH_P >= 0.001 else '<0.001')
m('CgAwPrimary', 'per window')
# r35: generated, so the clause cannot outlive the numbers it describes
m('CgAwStratClause', ('close to the pooled value, so the split by masked fraction does not explain the per-window move'
                      if abs(D_STRAT) < 0.5 * abs(D_SHR) else
                      'which accounts for much of the per-window move'))

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
# ★ r35 (N5, fresh read B10): Table D1 printed the smallest P at its cell's two places (0.01) while D.2 prints
# \CgMinProb (0.014, the places the edge rule allows for the minimum).  The minimum cell now prints \CgMinProb, so the
# table and the text carry one value at one precision; G8 asserts it, drive 17 restores the cell's own macro.
if DRIVE != 17:
    _ce[(KMIN[0], KMIN[1], 1)] = _ce[(KMIN[0], KMIN[1], 1)][:2] + ('\\CgMinProb',)
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
_minrow = [ln for ln in T if ln.startswith(_fl[KMIN[0]] + ' & ' + _ml[KMIN[1]])]
ck('G8 (r35) the table prints the smallest P through \\CgMinProb, the value and precision the text quotes',
   len(_minrow) == 1 and _minrow[0].split(' & ')[4] == '\\CgMinProb{}' and _tt.count('\\CgMinProb{}') == 1,
   'min cell %s: %s' % (''.join(KMIN), _minrow[0].split(' & ')[4] if len(_minrow) == 1 else _minrow))

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
                            exp_unattr=HO_EXP, a_carried=A_EFF, a_carried_basis='census per-window effective share',
                            tl_carried=TL, p=HO_P, se=HO_SE, printed=HO_PR, n_blocks=len(_heb),
                            pooled_check=dict(a=A_POOL, exp_unattr=HO_EXP_POOL, p=HO_P_POOL, se=HO_SE_POOL,
                                              printed=HO_PR_POOL)),
               ashare=dict(pooled=dict(a=A_POOL, exp=N_POOL, p=JP['mc_report']['CeProbNull']),
                           strat=dict(median=_med, a=_st, exp=JS['e_chance'], move=D_STRAT,
                                      p=JS['mc_report']['CeProbNull']),
                           shrink=dict(K=K_SH, exp=JK['e_chance'], move=D_SHR,
                                       p=JK['mc_report']['CeProbNull'], sim_sd=SH_SD,
                                       sim_mean=float(_ds.mean()), sim_p=SH_P, nsim=NSIM),
                           primary=PRIMARY)),
          open(OUT_JSON, 'w'), indent=1, sort_keys=True)
print('chancegrid_r34: min P %s (%s%s) x%d -> %s; hold-out %d vs %.2f P %s; a_w strat %+.2f, '
      'shrink %+.2f (sim sd %.2f, p %.4f) -> %s'
      % (CMIN['pr'], KMIN[0], KMIN[1], NTRIAL, PR_BONF, HO_UN, HO_EXP, HO_PR, D_STRAT, D_SHR,
         SH_SD, SH_P, os.path.basename(OUT_TEX)))
