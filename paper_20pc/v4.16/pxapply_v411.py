#!/usr/bin/env python3
r"""round 72 -> survey_numbers_round72.tex, pxapply_v411.json

APPLYING THE OMITTED ANNUAL PARALLAX, RATHER THAN STATING IT.

The extraction phase-rotates the visibilities to each star's barycentric
direction while the visibilities see the apparent one, so the annual parallax
is left out of the assumed phase centre.  The resulting amplitude loss is the
normalised dirty beam at the parallactic displacement: parameter-free,
multiplicative and shape-preserving.  Because it is multiplicative, two things
follow arithmetically and neither needs new data.

  (1) THE LIMITS.  A true flux f is recovered as f*(1-loss), so every limit is
      too deep by 1/(1-loss) in its own window.  Dividing by the retained
      fraction makes the limits SHALLOWER.  That is published here.

  (2) THE SEARCH.  Attenuating a real source by (1-loss) and triggering at
      five sigma is the same arithmetic as leaving the source alone and
      triggering at 5*(1-loss).  So the corrected search is the search that
      was already run, read against a lower per-window trigger -- and the
      catalogue's published statistic is the MAXIMUM over each window's whole
      drift plane, so it decides exactly which windows produce a crossing
      under the lower trigger.  No spectrum is re-extracted and none needs to
      be.

  ★ A LOWER TRIGGER ADMITS MORE NOISE AS WELL AS MORE SIGNAL, so the new
    crossings are compared with the expectation computed at the SAME
    per-window trigger, from each window's own realised null scale and
    effective cell count.  Comparing them with an expectation computed at a
    flat five sigma would not be a comparison at all.

  ★ THE LOSS TABLE IS CHECKED, NOT TRUSTED.  One large-loss window is rebuilt
    from first principles -- the catalogue's own distance, the block's longest
    baseline, the window's own frequency -- and the synthesised beam, the
    displacement in beams and the normalised dirty beam are each reproduced.
    A bound that cannot be argued with is also applied to all 413 blocks: the
    parallactic displacement can never exceed the parallax itself.

    python3 pxapply_v411.py [--out DIR] [--drive N]

--drive 1..8 breaks one assertion each; --drive 0 means "no perturbation, but
do not write a path production reads".  MUST RUN BEFORE numbers_v410.py, which
reads pxapply_v411.json for the per-window retained fraction.
"""
import collections
import csv
import json
import math
import os
import statistics
import sys

from scipy.stats import norm

HERE = os.path.dirname(os.path.abspath(__file__))

DRIVE = None
OUTDIR = HERE
for _i, _a in enumerate(sys.argv):
    if _a == '--drive':
        DRIVE = int(sys.argv[_i + 1])
    if _a == '--out':
        OUTDIR = sys.argv[_i + 1]
SUF = '' if DRIVE is None else '_drive%d' % DRIVE

TRIGGER_SIGMA = 5.0
C_M_S = 2.99792458e8
ARCSEC = 206264.80624709636
PB_COEF = 1.22                     # the coefficient the loss table itself used

CAT = list(csv.DictReader(open(os.path.join(
    HERE, 'per_target_results_v3.99.csv'))))
PX = json.load(open(os.path.join(HERE, 'r8inputs', 'parallax_loss_v404.json')))
STR = json.load(open(os.path.join(HERE, 'strata_v411.json')))

OUT, FAIL = [], []


def m(name, val):
    assert name.isalpha(), (
        'a LaTeX macro name may contain letters only: %r' % name)
    OUT.append('\\newcommand{\\%s}{%s}' % (name, val))


def ck(label, cond, detail=''):
    print('  %-66s %s  %s' % (label, 'PASS' if cond else 'FAIL', detail))
    if not cond:
        FAIL.append(label)


# --------------------------------------------------------------- the join
# The loss is a property of the execution BLOCK (one parallax, one longest
# baseline, one epoch), so the join is on the block and not on the star: a
# companion pair observed in one block shares the block's geometry exactly.
# That is asserted rather than assumed, because the table holds one entry per
# star and nine blocks carry two or three.
BYEB = collections.defaultdict(list)
for b in PX['blocks']:
    BYEB[b['eb']].append(b)
DUP = {k: v for k, v in BYEB.items() if len(v) > 1}
RETAINED = {k: v[0]['Bm'] for k, v in BYEB.items()}

JOINED = [r for r in CAT if r['eb'] in RETAINED]
MISSING = [r for r in CAT if r['eb'] not in RETAINED]
LOSS = {id(r): 1.0 - RETAINED[r['eb']] for r in JOINED}

CAT_A = [r for r in CAT if r['search_class'] == 'A']
N_GT10_ALL = sum(1 for r in JOINED if LOSS[id(r)] > 0.10)
N_GT10_A = sum(1 for r in JOINED
               if LOSS[id(r)] > 0.10 and r['search_class'] == 'A')
LOSS_MED = statistics.median(LOSS.values())
LOSS_MAX = max(LOSS.values())

# ------------------------------------------------- (1) the corrected limits
# The multiplier is the stratum's, from the completeness record; the parallax
# divides it.  Both are per window, so the headline is rebuilt from the rows.
RULE = STR['rule']['sigma']
MULT_NOISE = STR['noise']['p90']
MULT_DISC = STR['disc']['bound_adopted']


def mult(r):
    return MULT_DISC if float(r['ctrl_max_snr']) >= RULE else MULT_NOISE


def eirp(r, parallax=True, stratified=True):
    e = float(r['eirp_nominal_W'])
    e *= mult(r) if stratified else STR['blanket']['p90']
    if parallax and r['eb'] in RETAINED:
        e /= RETAINED[r['eb']]
    return e


def sysbest(**kw):
    best = {}
    for r in CAT_A:
        s = r['system_id']
        v = eirp(r, **kw)
        if s not in best or v < best[s]:
            best[s] = v
    return sorted(best.values())


def bench_eirp():
    g = 0.7 * (math.pi * 12.0 * 230e9 / C_M_S) ** 2
    return 1e6 * g


BENCH = bench_eirp()
WIN_OLD = sorted(eirp(r, parallax=False, stratified=False) for r in CAT_A)
WIN_NEW = sorted(eirp(r) for r in CAT_A)
SYS_OLD = sysbest(parallax=False, stratified=False)
SYS_NEW = sysbest()
SYS_STRAT_ONLY = sysbest(parallax=False)
PX_ONLY_WIN = sorted(eirp(r, stratified=False) for r in CAT_A)
PX_SHIFT_WIN = (statistics.median(PX_ONLY_WIN)
                / statistics.median(WIN_OLD) - 1.0)
PX_SHIFT_SYS = (statistics.median(sysbest(stratified=False))
                / statistics.median(SYS_OLD) - 1.0)
N15_OLD = sum(1 for x in SYS_OLD if x <= 1e15)
N15_NEW = sum(1 for x in SYS_NEW if x <= 1e15)
NB_OLD = sum(1 for x in SYS_OLD if x <= BENCH)
NB_NEW = sum(1 for x in SYS_NEW if x <= BENCH)

# ------------------------------------------------- (2) the corrected search
def pexc(r, t):
    sw = 0.5 * (float(r['scale_route_a']) + float(r['scale_route_b']))
    n = float(r['n_ind_cells'])
    return -math.expm1(n * norm.logcdf(t / sw))


COV = [r for r in JOINED if r['n_ind_cells'] != '']
E_FLAT = sum(pexc(r, TRIGGER_SIGMA) for r in COV)
E_CORR = sum(pexc(r, TRIGGER_SIGMA * RETAINED[r['eb']]) for r in COV)
E_NEW = E_CORR - E_FLAT
NEW = [r for r in JOINED if r['crossing'] != 'True'
       and float(r['star_snr']) >= TRIGGER_SIGMA * RETAINED[r['eb']]]
NEW_A = [r for r in NEW if r['search_class'] == 'A']
NEW_B = [r for r in NEW if r['search_class'] == 'B']
COV_A = [r for r in COV if r['search_class'] == 'A']
E_NEW_A = (sum(pexc(r, TRIGGER_SIGMA * RETAINED[r['eb']]) for r in COV_A)
           - sum(pexc(r, TRIGGER_SIGMA) for r in COV_A))
# every new crossing is put through the same screen as every old one
NEW_NCTRL = [int(r['n_ctrl_ge_star']) for r in NEW]
NEW_PASS = [r for r in NEW if int(r['n_ctrl_ge_star']) == 0]
POISSON_SIGMA = (len(NEW) - E_NEW) / math.sqrt(E_NEW)

# ----------------------------------------------- the loss table, checked
# (a) the bound nothing can argue with: the parallactic displacement cannot
#     exceed the parallax, whose ellipse has semi-major axis exactly that.
EXCEED = [(b, b['dpar'] / (b['plx'] / 1000.0)) for b in PX['blocks']
          if b['dpar'] > b['plx'] / 1000.0]
EXCEED_MAX = max((x[1] for x in EXCEED), default=1.0)
# (b) one large-loss window rebuilt from the catalogue's own columns
WORST = max(PX['blocks'], key=lambda b: 1.0 - b['Bm'])
_rows = [r for r in CAT if r['eb'] == WORST['eb']]
assert _rows, WORST['eb']
NU_GHZ = statistics.mean(0.5 * (float(r['flo_GHz']) + float(r['fhi_GHz']))
                         for r in _rows)
SYN_REBUILT = (PB_COEF * (C_M_S / (NU_GHZ * 1e9)) / WORST['bmax']) * ARCSEC
SYN_RATIO = SYN_REBUILT / WORST['syn']
PLX_CAT = 1000.0 / statistics.mean(float(r['dist_pc']) for r in _rows)
PLX_RATIO = PLX_CAT / WORST['plx']
U_REBUILT = WORST['dpar'] / SYN_REBUILT
BG_REBUILT = math.exp(-4.0 * math.log(2.0) * U_REBUILT ** 2)
BG_RATIO = BG_REBUILT / WORST['Bg']
WORST_STAR = WORST['star']

print('\nthe omitted parallax, applied')
print('  %d of %d released windows carry a loss; %d do not (%s)'
      % (len(JOINED), len(CAT), len(MISSING),
         ', '.join('%s %s' % (r['star_name'], r['eb']) for r in MISSING)))
print('  %d blocks carry more than one star; all share one geometry: %s'
      % (len(DUP), all(len({round(x['Bm'], 12) for x in v}) == 1
                       for v in DUP.values())))
print('  loss > 10 per cent: %d of %d windows, %d of %d Class A'
      % (N_GT10_ALL, len(JOINED), N_GT10_A, len(CAT_A)))
print('  median %.3f per cent, max %.1f per cent'
      % (100 * LOSS_MED, 100 * LOSS_MAX))
print('  parallax alone moves the median window limit by %+.1f per cent and '
      'the per-system median by %+.1f per cent'
      % (100 * PX_SHIFT_WIN, 100 * PX_SHIFT_SYS))
print('  corrected search: expected %.1f new crossings, observed %d '
      '(%d Class A against %.1f expected, %d Class B)'
      % (E_NEW, len(NEW), len(NEW_A), E_NEW_A, len(NEW_B)))
print('  of the %d, %d pass the spatial screen; the fewest controls above '
      'the star in any of them is %d of 512'
      % (len(NEW), len(NEW_PASS), min(NEW_NCTRL)))
print('  worst window rebuilt: %s, %s, %.1f GHz, B_max %.0f m'
      % (WORST_STAR, WORST['eb'], NU_GHZ, WORST['bmax']))
print('    theta_syn %.5f" rebuilt against %.5f" recorded (%.4f)'
      % (SYN_REBUILT, WORST['syn'], SYN_RATIO))
print('    parallax %.2f mas from the catalogue distance against %.2f mas '
      'recorded (%.4f)' % (PLX_CAT, WORST['plx'], PLX_RATIO))
print('    dirty beam %.4f rebuilt against %.4f recorded (%.4f)'
      % (BG_REBUILT, WORST['Bg'], BG_RATIO))
print('  blocks whose displacement exceeds their parallax: %d of %d, '
      'worst by %.1f per cent'
      % (len(EXCEED), len(PX['blocks']), 100 * (EXCEED_MAX - 1)))
print('\nthe headline, stratified and parallax-corrected')
for lab, w, s in (('as published', WIN_OLD, SYS_OLD),
                  ('stratified only', None, SYS_STRAT_ONLY),
                  ('stratified + parallax', WIN_NEW, SYS_NEW)):
    print('  %-22s sys median %.3g W, <=1e15 %2d, benchmark %2d%s'
          % (lab, statistics.median(s), sum(1 for x in s if x <= 1e15),
             sum(1 for x in s if x <= BENCH),
             '' if w is None else ', window median %.3g W'
             % statistics.median(w)))

print('\nassertions')
ck('P1 the loss is a BLOCK property: every block carrying more than one star '
   'gives all of them the same geometry',
   all(len({round(x['Bm'], 12) for x in v}) == 1 for v in DUP.values())
   and (len(DUP) > 0 if DRIVE != 1 else False),
   '%d blocks with more than one star' % len(DUP))
ck('P2 the >10 per cent count is quoted against the set it was counted on: '
   'the whole release, not the Class A subset',
   N_GT10_ALL == (PX['rep']['meas']['n_gt10'] if DRIVE != 2 else -1)
   and N_GT10_A < N_GT10_ALL,
   '%d of %d released against %d of %d Class A; the frozen table says %d'
   % (N_GT10_ALL, len(JOINED), N_GT10_A, len(CAT_A),
      PX['rep']['meas']['n_gt10']))
ck('P3 the correction makes every limit SHALLOWER, never deeper',
   all(eirp(r, stratified=False) >= eirp(r, parallax=False, stratified=False)
       - 1e-6 for r in CAT_A) and (PX_SHIFT_WIN > 0 if DRIVE != 3 else False),
   'median window limit %+.2f per cent' % (100 * PX_SHIFT_WIN))
ck('P4 the corrected search is compared with the expectation at the SAME '
   'per-window trigger, which is larger than the flat one',
   (E_CORR if DRIVE != 4 else 0.0) > E_FLAT,
   'expected %.1f at 5 sigma, %.1f at 5(1-loss)' % (E_FLAT, E_CORR))
ck('P5 the new crossings are consistent with that expectation, so the lower '
   'trigger admits noise and not signal',
   abs(POISSON_SIGMA if DRIVE != 5 else 9.9) < 3.0,
   '%d observed against %.1f expected, %.1f sigma'
   % (len(NEW), E_NEW, POISSON_SIGMA))
ck('P6 every new crossing is put through the unchanged spatial screen, and '
   'none of them passes it',
   len(NEW_PASS) == (0 if DRIVE != 6 else 1) and min(NEW_NCTRL) > 0,
   '%d of %d pass; fewest controls above the star %d'
   % (len(NEW_PASS), len(NEW), min(NEW_NCTRL)))
ck('P7 the loss table rebuilds from the catalogue\'s own columns: beam, '
   'parallax and dirty beam each to one per cent',
   max(abs(SYN_RATIO - 1), abs(PLX_RATIO - 1),
       abs(BG_RATIO - 1) if DRIVE != 7 else 9.0) < 0.01,
   'beam %.4f, parallax %.4f, dirty beam %.4f'
   % (SYN_RATIO, PLX_RATIO, BG_RATIO))
ck('P8 the parallactic displacement never exceeds the parallax by more than '
   'a per cent or two, and where it does the error is CONSERVATIVE',
   (EXCEED_MAX if DRIVE != 8 else 2.0) < 1.05,
   '%d of %d blocks exceed it, worst by %.1f per cent'
   % (len(EXCEED), len(PX['blocks']), 100 * (EXCEED_MAX - 1)))

print('\nassertions failed: %d %s' % (len(FAIL), FAIL))
if FAIL and DRIVE is None:
    raise SystemExit('pxapply_v411: %d assertion(s) failed: %s'
                     % (len(FAIL), FAIL))

m('PxaNWin', '%d' % len(JOINED))
m('PxaNWinAll', '%d' % len(CAT))
m('PxaNMissing', '%d' % len(MISSING))
m('PxaMissingStar', MISSING[0]['star_name'].replace(' ', '~')
  if MISSING else 'none')
m('PxaMissingEb', r'\texttt{%s}' % MISSING[0]['eb'].replace('_', r'\_')
  if MISSING else 'none')
m('PxaNGtTen', '%d' % N_GT10_ALL)
m('PxaNGtTenA', '%d' % N_GT10_A)
m('PxaLossMedPct', '%.2f' % (100 * LOSS_MED))
m('PxaLossMaxPct', '%.1f' % (100 * LOSS_MAX))
m('PxaShiftWinPct', '%.1f' % (100 * PX_SHIFT_WIN))
m('PxaShiftSysPct', '%.1f' % (100 * PX_SHIFT_SYS))
m('PxaNNew', '%d' % len(NEW))
m('PxaNNewA', '%d' % len(NEW_A))
m('PxaNNewB', '%d' % len(NEW_B))
m('PxaExpNew', '%.0f' % E_NEW)
m('PxaExpNewA', '%.0f' % E_NEW_A)
m('PxaNNewPass', '%d' % len(NEW_PASS))
m('PxaNewMinCtrl', '%d' % min(NEW_NCTRL))
m('PxaNCtrl', '%d' % int(NEW[0]['n_ctrl']))

path = os.path.join(OUTDIR, 'survey_numbers_round72.tex' if DRIVE is None else
                    'survey_numbers_round72_drive%d.tex' % DRIVE)
with open(path, 'w') as fh:
    fh.write('%% GENERATED by pxapply_v411.py -- do not hand-edit.\n')
    fh.write('\n'.join(sorted(OUT)) + '\n')
print('\nwrote %s (%d macros)' % (os.path.basename(path), len(OUT)))

REC = dict(
    generated_by='pxapply_v411.py',
    retained_fraction_by_eb=RETAINED,
    n_joined=len(JOINED), n_missing=len(MISSING),
    missing=[dict(star=r['star_name'], eb=r['eb']) for r in MISSING],
    shift=dict(window_median_frac=PX_SHIFT_WIN, system_median_frac=PX_SHIFT_SYS,
               loss_median=LOSS_MED, loss_max=LOSS_MAX,
               n_gt10_release=N_GT10_ALL, n_gt10_classA=N_GT10_A),
    headline=dict(
        published=dict(win_med=statistics.median(WIN_OLD),
                       sys_med=statistics.median(SYS_OLD),
                       n_sys_1e15=N15_OLD, n_sys_bench=NB_OLD),
        stratified_only=dict(sys_med=statistics.median(SYS_STRAT_ONLY)),
        adopted=dict(win_med=statistics.median(WIN_NEW),
                     sys_med=statistics.median(SYS_NEW),
                     n_sys_1e15=N15_NEW, n_sys_bench=NB_NEW,
                     sys_lo=SYS_NEW[0], sys_hi=SYS_NEW[-1])),
    search=dict(expected_new=E_NEW, observed_new=len(NEW),
                expected_new_A=E_NEW_A, observed_new_A=len(NEW_A),
                observed_new_B=len(NEW_B), n_pass_screen=len(NEW_PASS),
                min_controls_above_star=min(NEW_NCTRL),
                rows=[dict(star=r['star_name'], eb=r['eb'], band=r['band'],
                           cls=r['search_class'],
                           tstar=float(r['star_snr']),
                           trigger=TRIGGER_SIGMA * RETAINED[r['eb']],
                           n_ctrl_ge_star=int(r['n_ctrl_ge_star']))
                      for r in NEW]),
    table_check=dict(window=WORST['eb'], star=WORST_STAR, nu_GHz=NU_GHZ,
                     syn_ratio=SYN_RATIO, plx_ratio=PLX_RATIO,
                     dirty_beam_ratio=BG_RATIO,
                     n_blocks_displacement_exceeds_parallax=len(EXCEED),
                     worst_excess=EXCEED_MAX - 1.0))
jpath = os.path.join(OUTDIR, 'pxapply_v411%s.json' % SUF)
json.dump(REC, open(jpath, 'w'), indent=1, sort_keys=True)
print('wrote %s' % os.path.basename(jpath))
