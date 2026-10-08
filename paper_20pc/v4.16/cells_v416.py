#!/usr/bin/env python3
r"""Round 510: EVERY ABOVE-TRIGGER CELL, NOT ONLY THE WINDOW MAXIMUM, AND A
CHANCE EXPECTATION AT THE SAME GRAIN.

WHAT THIS CLOSES
    The search records one number per window -- the largest value its
    per-channel, drift-maximised statistic reaches at the stellar position --
    so a carrier is unrecordable whenever anything else in the same window is
    larger.  A molecular line can do that, and so can a noise excursion, and
    windows hold up to 6.9e6 channel x drift cells.  The published crossing
    counts therefore measure WINDOWS, not EVENTS, and the chance expectation
    they are compared with counts windows too.

    The retained per-channel profile of every window has been re-read, every
    above-trigger cell extracted at the stellar position AND at each retained
    control position, every cell carried through the same attribution and the
    same recurrence test, and the expectation recomputed at the cell level
    from the same control ensembles.  Both sides now count cells.

THE RULE, AND WHY IT IS NOT THE ONE THAT LOOKS NATURAL
    An event is a maximal run of channels whose statistic reaches the trigger,
    represented by the run's largest cell.  Channel adjacency, and nothing
    else.

    The obvious refinement -- merge two neighbouring channels only if the
    drifts that attained them agree to within one step of the window's own
    drift grid -- is WRONG here, and measurably so.  The retained statistic is
    already maximised over drift, so the trial that wins in the channel BESIDE
    an excursion carries no information about the excursion: little power lands
    there and the winning trial wanders.  Imposing the drift clause splits one
    excursion into two for 11 of the 14 unattributed cells it then produces,
    and splits the resolved beta Pictoris CO line into of order a hundred.
    Both rules are measured here and both are published, because the count is
    the thing a reader will want to know the sensitivity of.

WHY THE NEW POPULATION CAN ONLY LIVE WHERE A CROSSING ALREADY IS
    The recorded statistic is the window's largest cell, so a window whose
    recorded statistic is below the trigger holds no above-trigger cell at
    all.  Every secondary cell is therefore in a window that already produced
    a crossing.  C2 asserts it, and it is why the new search is bounded.

THE FREE REGRESSION TEST
    Run on the window maxima the rule must return exactly the published
    crossings.  It does: 50 of the 56, at the published frequency to 0.002 of
    a channel, with nothing else above the trigger anywhere in the survey
    except the two windows searched on a profile that does not reproduce their
    own adopted statistic -- which are named.  The six it does not reach are
    named too: four are the quality-failing block's, whose adopted statistic
    is the field-repaired one and whose repaired profile was not retained, and
    two have no retained profile at all.

ASSERTIONS (each driven; `--drive N`)
    C1  the window maxima reproduce the published crossings, by frequency and
        by value, and the recovered set holds nothing else
    C2  no window below the trigger holds an above-trigger cell, and every
        secondary cell lies in a window that holds a crossing
    C3  the counts decompose: primary + secondary = all cells, and
        attributed + unattributed = all cells, on both sides
    C4  the control side is counted at the same grain as the star side, over
        the same windows, and is not empty
    C5  the cell-level expectation exceeds nothing by construction: the
        observed count, the expectation and the measured star-to-control
        ratio are consistent, and the ratio is quoted below the trigger as
        well as at it
    C6  every unattributed secondary cell was carried to the recurrence test,
        under both the position join and the position-or-name join, and the
        number recurring is the same under each
    C7  the de-duplication rule is not vacuous: both rules are evaluated, they
        disagree, and the disagreement is published
    C8  the reference set is the released Class A windows, the windows not
        covered are named, and covered + named == the published count

Inputs, all read: `r15inputs/cells/cells_extract_result.json`,
`cells_recur_result.json`, `cells_recur_union.json`, `cells_jobs.json`,
`ledger.json`, and the macro layer for the counts other generators own.

    python3 cells_v416.py [--drive N]
"""
import collections
import glob
import json
import math
import os
import re
import sys

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

ROUND = 510
TRIG = 5.0
NBOOT = 20000
SEED = 510

DRIVE = None
for _i, _a in enumerate(sys.argv):
    if _a == '--drive':
        DRIVE = int(sys.argv[_i + 1])

# The production name is a literal; only the drive branch is built by format,
# so `roundcollide` resolves the claim on round 510.
OUT_TEX = os.path.join(HERE, 'survey_numbers_round510.tex' if DRIVE is None
                       else 'survey_numbers_round510_drive%d.tex' % DRIVE)
OUT_JSON = os.path.join(HERE, 'cells_v416%s.json'
                        % ('' if DRIVE is None else '_drive%d' % DRIVE))

OUT = []
fail = []


def m(name, val):
    assert name.isalpha(), 'a macro name may contain letters only: %r' % name
    assert not any(x.startswith('\\newcommand{\\%s}' % name) for x in OUT), name
    OUT.append('\\newcommand{\\%s}{%s}' % (name, val))


def ck(label, cond, detail=''):
    print('  %-66s %s  %s' % (label[:66], 'PASS' if cond else 'FAIL', detail))
    if not cond:
        fail.append(label)


def texval(name):
    main = glob.glob(os.path.join(HERE, 'technosignatures_*.tex'))
    order = []
    if len(main) == 1:
        for ln in open(main[0], errors='ignore'):
            mm = re.match(r'\s*\\input\{(survey_numbers[A-Za-z0-9_]*)\}', ln)
            if mm:
                order.append(mm.group(1) + '.tex')
    val = None
    for fn in order:
        p = os.path.join(HERE, fn)
        if not os.path.exists(p):
            continue
        for ln in open(p, errors='ignore'):
            for nm, vv in re.findall(
                    r'\\(?:providecommand|renewcommand|newcommand)'
                    r'\{?\\([A-Za-z]+)\}?\{([^{}]*)\}', ln):
                if nm == name and vv.strip():
                    val = vv.strip()
    assert val is not None, 'no generator publishes \\%s' % name
    return val


D = os.path.join(HERE, 'r15inputs', 'cells')
EXT = json.load(open(os.path.join(D, 'cells_extract_result.json')))
JOB = json.load(open(os.path.join(D, 'cells_jobs.json')))
RECP = json.load(open(os.path.join(D, 'cells_recur_result.json')))
RECU = json.load(open(os.path.join(D, 'cells_recur_union.json')))
LED = json.load(open(os.path.join(HERE, 'ledger.json')))['rows']

WIN = EXT['windows']


def attributed(e):
    """The disposition the paper reports: inside the mask of a transition the
    attribution acts on.  A coincidence with a species reported rather than
    acted on is counted UNATTRIBUTED, which is the adopted rule."""
    return bool(e['in_mask'] and e['in_mask_null'])


A_REL = [w for w in WIN if w['cls'] == 'A' and w['stratum'] != 'archival_tail']
A_TAIL = [w for w in WIN if w['cls'] == 'A' and w['stratum'] == 'archival_tail']
B_ALL = [w for w in WIN if w['cls'] == 'B']


def cells(S, primary=None, unattr=None):
    out = []
    for w in S:
        for e in w['events']:
            if primary is not None and e['is_window_max'] != primary:
                continue
            if unattr is not None and attributed(e) == unattr:
                continue
            out.append((w, e))
    return out


N_WIN = len(A_REL)
N_CTRL_POS = sum(w['n_ctrl'] for w in A_REL)
PRI = cells(A_REL, primary=True)
SEC = cells(A_REL, primary=False)
PRI_U = cells(A_REL, primary=True, unattr=True)
SEC_U = cells(A_REL, primary=False, unattr=True)
SEC_A = cells(A_REL, primary=False, unattr=False)
if DRIVE == 3:
    SEC_A = SEC_A[:-1]              # the decomposition stops closing

# the control side, counted the same way over the same windows
C_PRI = sum(1 for w in A_REL for c in w['ctrl'] if c['win_max'] >= TRIG)
C_SEC = sum(c['n_sec'] for w in A_REL for c in w['ctrl'])
C_PRI_U = sum(1 for w in A_REL for c in w['ctrl']
              if c['win_max'] >= TRIG and not c['max_in_mask'])
C_SEC_U = sum(c['n_sec_out'] for w in A_REL for c in w['ctrl'])
if DRIVE == 4:
    C_SEC_U = 0                     # the control side is not counted at all

# the expectation: one position's worth, summed window by window, which is
# what "window by window" means on this side of the comparison
E_PRI = sum(sum(1 for c in w['ctrl']
                if c['win_max'] >= TRIG and not c['max_in_mask'])
            / w['n_ctrl'] for w in A_REL)
E_SEC = sum(sum(c['n_sec_out'] for c in w['ctrl']) / w['n_ctrl']
            for w in A_REL)
E_ALL = E_PRI + E_SEC
N_OBS = len(PRI_U) + len(SEC_U)

# the threshold ladder: the same count at the star and at a control position,
# outside the mask, as a function of the level
LAD = []
for thr in sorted(float(k) for k in A_REL[0]['ladder']):
    k = '%.2f' % thr
    s = sum(w['ladder'][k]['star_out'] for w in A_REL)
    c = sum(w['ladder'][k]['ctrl_out'] for w in A_REL)
    LAD.append((thr, s, c, (s / N_WIN) / (c / N_CTRL_POS) if c else None))
if DRIVE == 5:
    LAD = [r for r in LAD if r[0] >= TRIG]      # the ladder loses its shank
LAD_R = [r for r in LAD if r[3] is not None and r[0] <= TRIG]
RAT_LO, RAT_HI = min(r[3] for r in LAD_R), max(r[3] for r in LAD_R)
RAT_AT = [r[3] for r in LAD if r[0] == TRIG][0]

# the interval: execution blocks resampled, as the window-level comparison does
rng = np.random.default_rng(SEED)
BLK = collections.defaultdict(list)
for w in A_REL:
    BLK[w['eb']].append(w)
EBS = sorted(BLK)
PERBLK = np.array([sum(sum(1 for c in w['ctrl']
                           if c['win_max'] >= TRIG and not c['max_in_mask'])
                       / w['n_ctrl']
                       + sum(c['n_sec_out'] for c in w['ctrl']) / w['n_ctrl']
                       for w in BLK[e]) for e in EBS])
NWB = np.array([len(BLK[e]) for e in EBS], float)
pick = rng.integers(0, len(EBS), size=(NBOOT, len(EBS)))
BOOT = PERBLK[pick].sum(axis=1) / NWB[pick].sum(axis=1) * N_WIN
HO = float(texval('StHoRatio'))
HOLO, HOHI = float(texval('StHoLo')), float(texval('StHoHi'))
BOOT = BOOT * rng.uniform(HOLO / HO, HOHI / HO, NBOOT)
E_LO, E_HI = float(np.percentile(BOOT, 2.5)), float(np.percentile(BOOT, 97.5))

# recurrence
REC = RECP['rows']
RECUN = RECU['rows']
N_REC = sum(1 for r in REC if r['n_recurring'] > 0)
N_RECU = sum(1 for r in RECUN if r['n_recurring'] > 0)
if DRIVE == 6:
    N_RECU = 1                      # the two joins stop agreeing
N_NOCOVER = sum(1 for r in REC if r['n_read'] == 0)
COVLO = min(r['n_read'] for r in REC)
COVHI = max(r['n_read'] for r in REC)
TREPHI = max(r['T_rep_max'] for r in REC)

# the rule, and what it costs
if DRIVE == 7:                 # the two rules are made to agree
    for w in A_REL + A_TAIL:
        w['variants']['driftstep'] = dict(w['variants']['adopted'])
V = {nm: dict(n=sum(w['variants'][nm]['n'] for w in A_REL + A_TAIL),
              sec=sum(w['variants'][nm]['n_sec'] for w in A_REL + A_TAIL),
              secu=sum(w['variants'][nm]['n_sec_unattr']
                       for w in A_REL + A_TAIL))
     for nm in A_REL[0]['variants']}
N_SPLIT = sum(1 for w in A_REL + A_TAIL
              if w['variants']['driftstep']['n_sec_unattr']
              > w['variants']['adopted']['n_sec_unattr'])
SPLIT_CELLS = (V['driftstep']['secu'] - V['adopted']['secu'])

# ---------------------------------------------------------------- regression
BYEB = collections.defaultdict(list)
for w in WIN:
    BYEB[w['eb']].append(w)
hit, missed = [], []
for r in LED:
    cand = [w for w in BYEB.get(r['eb'], [])
            if min(w['lo'], w['hi']) - 1e-6 <= r['freq'] <= max(w['lo'],
                                                               w['hi']) + 1e-6
            and abs(w['star_peak'] - r['tstar']) / r['tstar'] <= 1e-3]
    if not cand:
        missed.append(r)
        continue
    w = cand[0]
    e = [x for x in w['events'] if x['is_window_max']][0]
    hit.append((r, w, abs(e['f_topo'] - r['freq']) * 1e9 / w['chanw']))
REG_N = len(hit)
REG_DEV = max(h[2] for h in hit)
if DRIVE == 1:
    REG_DEV = 1.0                   # the recovered peak is a channel away
REG_ALLTRIG = all(h[1]['star_peak'] >= TRIG for h in hit)
PUBKEY = {h[1]['key'] for h in hit}
EXTRA = [w for w in WIN if w['star_peak'] >= TRIG and w['key'] not in PUBKEY]
EXTRA_OK = all(w['stratum'] in ('released_prerepair', 'released_other')
               for w in EXTRA)
MISS_DQ = sum(1 for r in missed if r['dq'])

# C2: a window below the trigger cannot hold an above-trigger cell
BAD2 = [w for w in WIN if w['star_peak'] < TRIG and w['n_events'] > 0]
SEC_IN_CROSS = all(w['star_peak'] >= TRIG for w in WIN if w['n_events'] > 1)
if DRIVE == 2:
    BAD2 = BAD2 + [WIN[0]]          # a sub-trigger window holds a cell

# C8: the reference set
N_A_REL_PUB = int(texval('NWinA'))
NOT_COVERED = sorted({(u['eb'], u['star']) for u in EXT['meta']['unresolved']
                      if u['cls'] == 'A'}
                     | {(r['eb'], r['display']) for r in missed if not r['dq']})
N_NOT_COVERED = N_A_REL_PUB - N_WIN
if DRIVE == 8:
    N_WIN_CHK = N_A_REL_PUB         # the gap is papered over
else:
    N_WIN_CHK = N_WIN

print('cells_v416: round %d%s' % (ROUND, '' if DRIVE is None
                                  else '  (drive %d)' % DRIVE))
print('  %d windows searched; released Class A %d of %d; archival-tail Class A '
      '%d; Class B %d' % (len(WIN), N_WIN, N_A_REL_PUB, len(A_TAIL),
                          len(B_ALL)))
print('  star: %d primary, %d secondary; unattributed %d + %d = %d'
      % (len(PRI), len(SEC), len(PRI_U), len(SEC_U), N_OBS))
print('  control: %d primary, %d secondary over %d positions; unattributed '
      '%d + %d' % (C_PRI, C_SEC, N_CTRL_POS, C_PRI_U, C_SEC_U))
print('  expected at one position, summed window by window: %.2f + %.2f = '
      '%.2f (%.0f-%.0f)' % (E_PRI, E_SEC, E_ALL, E_LO, E_HI))
print('  out-of-mask cells per position, star/control: %.2f at the trigger, '
      '%.2f-%.2f over %g-%g' % (RAT_AT, RAT_LO, RAT_HI, LAD_R[0][0], TRIG))
print('  recurrence: %d of %d secondary cells recur (position join), %d '
      '(position-or-name join); coverage %d-%d blocks; deepest repeat %.3f'
      % (N_REC, len(REC), N_RECU, COVLO, COVHI, TREPHI))

ck('C1 THE WINDOW MAXIMA ARE THE PUBLISHED CROSSINGS: %d of %d reproduced, '
   'worst %.4f channels, every one at the trigger, and the recovered set '
   'holds nothing else' % (REG_N, len(LED), REG_DEV),
   REG_N == 50 and REG_DEV < 0.01 and REG_ALLTRIG and EXTRA_OK
   and len(missed) == len(LED) - REG_N,
   '%d not reached, %d of them the quality-failing block\'s; %d extra, all on '
   'a non-reproducing profile' % (len(missed), MISS_DQ, len(EXTRA)))

ck('C2 A WINDOW BELOW THE TRIGGER HOLDS NO ABOVE-TRIGGER CELL, so every '
   'secondary cell lies in a window that already holds a crossing',
   not BAD2 and SEC_IN_CROSS,
   '%d violations' % len(BAD2))

ck('C3 THE COUNTS DECOMPOSE on both sides',
   len(PRI) + len(SEC) == len(cells(A_REL))
   and len(SEC_U) + len(SEC_A) == len(SEC)
   and len(PRI_U) + len(SEC_U) == N_OBS,
   '%d+%d=%d cells; %d+%d=%d secondary'
   % (len(PRI), len(SEC), len(cells(A_REL)), len(SEC_U), len(SEC_A), len(SEC)))

ck('C4 THE CONTROL SIDE IS COUNTED AT THE SAME GRAIN over the same windows '
   'and is not empty',
   C_SEC_U > 0 and C_PRI_U > 0 and N_CTRL_POS == 8 * N_WIN
   and E_SEC > 0 and E_PRI > 0,
   '%d control positions, %d secondary cells outside the mask'
   % (N_CTRL_POS, C_SEC_U))

ck('C5 THE CELL-LEVEL COMPARISON IS CONSISTENT and the ratio is quoted below '
   'the trigger as well as at it',
   E_LO <= N_OBS <= E_HI and len(LAD_R) >= 4
   and abs(RAT_AT - HO) < 0.5 * HO,
   'observed %d, expected %.2f (%.0f-%.0f), ratio at the trigger %.2f against '
   'the reserved blocks\' %.2f' % (N_OBS, E_ALL, E_LO, E_HI, RAT_AT, HO))

ck('C6 EVERY UNATTRIBUTED SECONDARY CELL WENT TO RECURRENCE under both joins '
   'and the two agree',
   len(REC) == len(SEC_U) + len(cells(A_TAIL, primary=False, unattr=True))
   and len(RECUN) == len(REC) and N_REC == N_RECU and N_NOCOVER == 0,
   '%d tested, %d recur under the position join and %d under the '
   'position-or-name join' % (len(REC), N_REC, N_RECU))

ck('C7 THE DE-DUPLICATION RULE IS MEASURED, NOT ASSERTED: two rules, they '
   'disagree, and the disagreement is published',
   V['adopted']['secu'] != V['driftstep']['secu'] and SPLIT_CELLS > 0
   and N_SPLIT > 0,
   'adopted %d secondary cells / %d unattributed against %d / %d with the '
   'drift clause, %d of them one excursion counted twice in %d windows'
   % (V['adopted']['sec'], V['adopted']['secu'], V['driftstep']['sec'],
      V['driftstep']['secu'], SPLIT_CELLS, N_SPLIT))

ck('C8 THE REFERENCE SET IS THE RELEASED CLASS A WINDOWS and the ones not '
   'covered are named',
   N_WIN_CHK + N_NOT_COVERED == N_A_REL_PUB and len(NOT_COVERED) > 0,
   '%d searched + %d not covered = %d; not covered: %s'
   % (N_WIN, N_NOT_COVERED, N_A_REL_PUB,
      ', '.join('%s (%s)' % (b, s) for b, s in NOT_COVERED)))

# ===================================================================== macros
m('CkNWin', N_WIN)
m('CkNWinNotCov', N_NOT_COVERED)
m('CkNCtrlPos', format(N_CTRL_POS, ',').replace(',', '\\,'))
m('CkNPrimary', len(PRI))
m('CkNSecondary', len(SEC))
m('CkNSecondaryWord', {0: 'no', 1: 'one', 2: 'two', 3: 'three',
                       21: 'twenty-one'}.get(len(SEC), str(len(SEC))))
m('CkNSecWin', sum(1 for w in A_REL if w['n_events'] > 1))
m('CkNSecMax', max(w['n_events'] - 1 for w in A_REL))
m('CkNSecAttr', len(SEC_A))
m('CkNSecUnattr', len(SEC_U))
m('CkNSecUnattrWord', {0: 'none', 1: 'one', 2: 'two', 3: 'three',
                       4: 'four'}.get(len(SEC_U), str(len(SEC_U))))
m('CkNObs', N_OBS)
m('CkExp', '%.1f' % E_ALL)
m('CkExpSec', '%.1f' % E_SEC)
m('CkLo', '%.0f' % E_LO)
m('CkHi', '%.0f' % E_HI)
m('CkRatioLo', '%.2f' % RAT_LO)
m('CkRatioHi', '%.2f' % RAT_HI)
m('CkLadderLo', '%g' % LAD_R[0][0])
m('CkNRecurWord', {0: 'none', 1: 'one', 2: 'two'}.get(N_REC, str(N_REC)))
m('CkCovLo', COVLO)
m('CkCovHi', COVHI)
m('CkTrepHi', '%.1f' % TREPHI)
m('CkRegN', REG_N)
m('CkRegDev', '%.3f' % REG_DEV)
m('CkRegMiss', len(missed))
m('CkRuleSec', V['driftstep']['sec'])
m('CkRuleSecUnattr', V['driftstep']['secu'])
m('CkRuleSplit', SPLIT_CELLS)
# The three stars, named from the ledger's own typeset display names so the
# paper cannot carry a raw product string, and read from the ledger rather
# than written down here.
DISP = {}
for r in LED:
    DISP[r['eb']] = r['display']
_names = []
for r in REC:
    nm = DISP.get(r['eb'])
    if nm is None:
        nm = next((DISP[k] for k in DISP
                   if any(x['eb'] == k and x['star'] == r['star']
                          for x in WIN)), r['star'])
    if nm not in _names:
        _names.append(nm)
assert all(' ' in n or '~' in n for n in _names), _names
assert not any('Gaia' in n for n in _names), _names
_names = [n.replace(' ', '~') for n in _names]
m('CkSecStars', ', '.join(_names[:-1]) + ' and ' + _names[-1]
  if len(_names) > 1 else _names[0])

OUT.insert(0, '%%%% survey_numbers_round%d.tex -- generated by cells_v416.py.'
           % ROUND)
OUT.insert(1, '%% Every above-trigger cell of every window, the chance')
OUT.insert(2, '%% expectation at the same grain, and the recurrence test run')
OUT.insert(3, '%% on every cell the attribution leaves unattributed.')
with open(OUT_TEX, 'w') as fh:
    fh.write('\n'.join(OUT) + '\n')

json.dump(dict(round=ROUND, drive=DRIVE,
               n_window=len(WIN), n_win_relA=N_WIN, n_win_tailA=len(A_TAIL),
               n_primary=len(PRI), n_secondary=len(SEC),
               n_sec_attr=len(SEC_A), n_sec_unattr=len(SEC_U),
               n_pri_unattr=len(PRI_U), n_obs=N_OBS,
               e_pri=E_PRI, e_sec=E_SEC, e_all=E_ALL, e_lo=E_LO, e_hi=E_HI,
               ctrl_pri=C_PRI, ctrl_sec=C_SEC, ctrl_sec_unattr=C_SEC_U,
               ladder=[dict(thr=t, star=s, ctrl=c, ratio=r)
                       for t, s, c, r in LAD],
               n_recur=N_REC, n_recur_union=N_RECU, n_tested=len(REC),
               variants=V, rule_split=SPLIT_CELLS, n_split_windows=N_SPLIT,
               regression=dict(n=REG_N, worst_channel_dev=REG_DEV,
                               missed=[dict(star=r['display'], eb=r['eb'],
                                            dq=r['dq']) for r in missed],
                               extra=[dict(key=w['key'], stratum=w['stratum'],
                                           peak=w['star_peak'])
                                      for w in EXTRA]),
               not_covered=NOT_COVERED,
               secondary=[dict(star=w['star'], eb=w['eb'], T=e['T'],
                               f_topo=e['f_topo'], f_star=e['f_star'],
                               drift=e['drift'], line=e['line'], dv=e['dv'],
                               in_mask=e['in_mask'],
                               window_max=w['star_peak'])
                          for w, e in SEC_U],
               n_boot=NBOOT, seed=SEED), open(OUT_JSON, 'w'), indent=1)

print('  %d macros -> %s' % (len(OUT) - 4, os.path.basename(OUT_TEX)))
if fail:
    print('FAILED: %s' % '; '.join(fail))
sys.exit(1 if fail else 0)
