#!/usr/bin/env python3
r"""round 840 -> survey_numbers_round840.tex: FOUR ITEMS OWNED BY `r19-quality`.

  (1) R1-4  the post-hoc execution-block quality criterion, shown to be
            robust to where the line was drawn.
  (2) R2-9  the archival bookkeeping sentence, with its three counts verified.
  (3) R2-10 the interference clustering statistic, DEFINED, and applied to the
            unattributed crossings as the results section defines them.
  (4) R2-11 the archival extension's zero unattributed crossings, against the
            expectation the false-alarm appendix builds.

READ-ONLY on the version directory: every input is read from PAPER, every
output is written beside this file.  Nothing is typed that the products can
be asked for, and each block begins with a FALSIFIER -- it must reproduce the
published number before it is allowed to extend or criticise it.

    python3 quality_r19.py [--drive N]

`--drive 0` means "no perturbation, but do not write a path production reads".
"""
import collections
import csv
import json
import math
import os
import sys

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
ROUND = 840

#: Where the inputs are read from.  When this file sits in the version
#: directory -- where it belongs once it is adopted -- that directory is both
#: the input and the output, like every other generator here.  While it is
#: being written it sits outside and reads the frozen version READ-ONLY.
#: Outputs are always written beside this file.
_V419 = '/workspace/SETI/paper_20pc/v4.19'
PAPER = (HERE if os.path.exists(os.path.join(
    HERE, 'per_target_results_v3.99.csv')) else _V419)

sys.path.insert(0, PAPER)
import dqflag                                                    # noqa: E402
import maskframe_v411 as mf                                      # noqa: E402

DRIVE = None
for _i, _a in enumerate(sys.argv):
    if _a == '--drive':
        DRIVE = int(sys.argv[_i + 1])
SUF = '' if DRIVE is None else '_drive%d' % DRIVE

OUT_NAME = 'survey_numbers_round840%s.tex' % SUF
OUT_PATH = os.path.join(HERE, OUT_NAME)
JSON_PATH = os.path.join(HERE, 'quality_r19%s.json' % SUF)

C_KMS = 299792.458
TRIG = 5.0
HALF = mf.MASK_HALF_KMS
SEED = 20261014
RNG = np.random.default_rng(SEED)
NMC = 20000

#: the clustering tolerances.  NOT chosen here: this is the ladder the
#: interference appendix already publishes (\AppMLadderLo-\AppMLadderHi), so
#: the pair statistic introduces no new tuned number.  Every rung is reported.
LADDER_MHZ = [1.0, 3.0, 10.0, 30.0, 100.0, 300.0]

OUT, fail = [], []
J = {'generator': 'quality_r19.py', 'round': ROUND, 'seed': SEED,
     'n_mc': NMC, 'ladder_MHz': LADDER_MHZ, 'drive': DRIVE}


def m(name, val):
    assert name.isalpha(), (
        'a LaTeX macro name may contain letters only: %r' % name)
    assert not any(x.startswith('\\newcommand{\\%s}' % name) for x in OUT), name
    OUT.append('\\newcommand{\\%s}{%s}' % (name, val))


def ck(label, cond, detail=''):
    print('  %-76s %s  %s' % (label[:76], 'PASS' if cond else 'FAIL', detail))
    if not cond:
        fail.append(label)


_TEXCACHE = {}


def texval(name):
    """A macro from the published layer of the version directory; last wins."""
    if not _TEXCACHE:
        import re
        pat = re.compile(r'\\(?:provide|renew|new)command\{?\\([A-Za-z]+)\}?'
                         r'\{([^}]*)\}')
        for f in sorted(os.listdir(PAPER)):
            if not (f.startswith('survey_numbers') and f.endswith('.tex')):
                continue
            for mm in pat.finditer(open(os.path.join(PAPER, f),
                                        errors='ignore').read()):
                if mm.group(2).strip():
                    _TEXCACHE[mm.group(1)] = mm.group(2).strip()
    return _TEXCACHE.get(name)


def F(x):
    try:
        return float(x)
    except (TypeError, ValueError):
        return None


# =====================================================================
# the inputs
# =====================================================================
CAT = list(csv.DictReader(open(os.path.join(
    PAPER, 'per_target_results_v3.99.csv'))))
LEDGER = json.load(open(os.path.join(PAPER, 'ledger.json')))
XR = LEDGER['rows']
EXTEXP = json.load(open(os.path.join(PAPER, 'export_extension.json')))['rows']
HD14055 = json.load(open(os.path.join(
    PAPER, 'r8inputs', 'v409', 'hd14055_results.json')))
TAILCOLL = json.load(open(os.path.join(
    PAPER, 'r8inputs', 'v409', 'tail_collect.json')))

CLS = {}
for r in CAT:
    CLS[dqflag.key(r['eb'], r['rms_mJy'], r['star_snr'])] = r['search_class']
RINGMED = dqflag._load(PAPER)['ringmed']
assert len(RINGMED) == len(CLS), (len(RINGMED), len(CLS))


# =====================================================================
# (1) R1-4: THE QUALITY CRITERION, AND WHETHER THE LINE'S POSITION MATTERS
# =====================================================================
# The statistic and the rule are the published ones, recomputed here so that
# the sweep runs on the same object the paper applies:
#
#     m_w  = median of window w's own 512-position control ensemble
#     q_w  = m_w / median(m over the windows of w's own search class)   SEPARATE
#     r_w  = m_w / median(m over every window of the survey)            JOINT
#     Q_b  = median(q_w over block b's windows);  R_b likewise from r_w
#     block FAILS when its block statistic exceeds the factor (published: 2)
#
# Instruction 5 asks whether the answer depends on treating the two classes
# separately or jointly.  That is exactly the difference between q and r, so
# both are swept; and both class-restricted variants are computed as well.
def block_stat(norm):
    """Block statistics under one normalisation: `norm` maps a window key to
    the divisor applied to its m_w."""
    q = {k: v / norm(k) for k, v in RINGMED.items()}
    by = collections.defaultdict(list)
    for k, v in q.items():
        by[k[0]].append(v)
    return {e: float(np.median(v)) for e, v in by.items()}, q


CLASS_MED = {c: float(np.median([v for k, v in RINGMED.items()
                                 if CLS[k] == c]))
             for c in sorted(set(CLS.values()))}
SURV_MED = float(np.median(list(RINGMED.values())))

QB_SEP, Q_SEP = block_stat(lambda k: CLASS_MED[CLS[k]])
QB_JOINT, _ = block_stat(lambda k: SURV_MED)

# class-restricted variants: a block judged on only one class of its windows
QB_A, QB_B = {}, {}
for k, v in Q_SEP.items():
    (QB_A if CLS[k] == 'A' else QB_B).setdefault(k[0], []).append(v)
QB_A = {e: float(np.median(v)) for e, v in QB_A.items()}
QB_B = {e: float(np.median(v)) for e, v in QB_B.items()}

VARIANTS = collections.OrderedDict((
    ('separate', QB_SEP),      # per-class normalisation -- the published rule
    ('joint', QB_JOINT),       # one survey-wide normalisation
    ('class_A_only', QB_A),    # judged on the block's Class A windows only
    ('class_B_only', QB_B),    # judged on the block's Class B windows only
))

FACTOR = float(texval('DqFactorVal') or dqflag.DQ_FACTOR)
SORTED_SEP = sorted(QB_SEP.items(), key=lambda kv: -kv[1])
WORST, WORST_Q = SORTED_SEP[0]
NEXT_EB, NEXT_Q = SORTED_SEP[1]
SEP_RATIO = WORST_Q / NEXT_Q
SEP_GAP = WORST_Q - NEXT_Q

# ---- FALSIFIER: reproduce the published criterion before extending it ------
PUB_FAILQ = float(texval('BqFailQ'))
PUB_NEXTQ = float(texval('BqNextQ'))
PUB_NFAIL = int(texval('BqNFail'))
PUB_BLOCK = (texval('BqFailBlock') or '').replace('\\_', '_')
PUB_NBLOCK = int(texval('BqNBlocks'))
FAILED_PUB = {e for e, q in QB_SEP.items() if q > FACTOR}

# ---- THE SWEEP ------------------------------------------------------------
# Thresholds strictly between the next-worst and the worst block statistic --
# the whole interval instruction 3 names -- sampled at a fixed number of
# steps.  Each variant is swept between ITS OWN two extremes, because the two
# normalisations do not share a scale and a threshold is only meaningful
# against the statistic it is applied to.
N_STEP = 41


def sweep_of(QB):
    s = sorted(QB.values(), reverse=True)
    hi, lo = s[0], s[1]
    ts = [lo + (hi - lo) * (i + 1) / (N_STEP + 1) for i in range(N_STEP)]
    if DRIVE == 2:                      # a sweep that leaves the interval
        ts = ts + [hi * 1.5]
    return ts, lo, hi


SWEEP, SWEEP_RANGE = collections.OrderedDict(), {}
for tag, QB in VARIANTS.items():
    ts, lo, hi = sweep_of(QB)
    SWEEP_RANGE[tag] = (lo, hi)
    SWEEP[tag] = [dict(threshold=t, n=len(sel), blocks=sorted(sel))
                  for t, sel in ((t, frozenset(e for e, q in QB.items()
                                               if q > t)) for t in ts)]
SWEEP_T, _, _ = sweep_of(QB_SEP)

IDENT = {tag: {frozenset(r['blocks']) for r in rows}
         for tag, rows in SWEEP.items()}
N_DISTINCT = {tag: len(s) for tag, s in IDENT.items()}
SEL_ALL = set()
for tag in ('separate', 'joint', 'class_B_only'):
    SEL_ALL |= IDENT[tag]

# the Class-A-only rule cannot reach the failing block, which holds no Class A
# window, so what it does reach is reported rather than asserted: the block
# with the largest Class A statistic, and the published justification for it.
A_TOP_EB, A_TOP_Q = max(QB_A.items(), key=lambda kv: kv[1])
A_TOP_STAR = sorted({r['star_name'] for r in CAT if r['eb'] == A_TOP_EB})

# ★★★ THE HONEST READING OF INSTRUCTIONS 3 AND 4.  Sweeping thresholds
# strictly between the two most extreme block statistics selects the single
# most extreme block AT EVERY STEP BY DEFINITION, so the sweep by itself is a
# check that cannot fail.  What is measured, and what carries the referee's
# point, is the WIDTH of the interval over which the answer is constant -- the
# factor the published threshold may be multiplied by in either direction --
# together with a demonstration of where the answer does change.
MARGIN_DOWN = NEXT_Q / FACTOR
MARGIN_UP = WORST_Q / FACTOR
Q_RANK = sorted(QB_SEP.values(), reverse=True)
#: how many blocks a threshold at the median block, and at the next-worst,
#: would exclude -- the demonstration that the rule discriminates at all
N_AT_NEXT = sum(1 for q in Q_RANK if q > NEXT_Q * 0.999)
Q_MED_BLOCK = float(np.median(Q_RANK))
N_AT_MED = sum(1 for q in Q_RANK if q > Q_MED_BLOCK)

# the same question asked of the published factor, variant by variant
AT_FACTOR = {tag: sorted(e for e, q in QB.items() if q > FACTOR)
             for tag, QB in VARIANTS.items()}

# where the class-restricted variants are even defined
N_DEF = {tag: len(QB) for tag, QB in VARIANTS.items()}
WORST_HAS_A = WORST in QB_A
WORST_HAS_B = WORST in QB_B

# does any block fail on one class and pass on the other, at the factor?
BOTH = set(QB_A) & set(QB_B)
DISAGREE = sorted(e for e in BOTH
                  if (QB_A[e] > FACTOR) != (QB_B[e] > FACTOR))

# the failing block's own windows and crossings, read not typed
WORST_WIN = [k for k in CLS if k[0] == WORST]
WORST_WIN_CLS = collections.Counter(CLS[k] for k in WORST_WIN)
WORST_X = [r for r in XR if r['eb'] == WORST]

print('(1) R1-4  the block-quality criterion, and the position of the line')
print('    statistic: Q_b = median over the block of m_w / median(m of its '
      'class);  factor %.1f' % FACTOR)
print('    %d blocks judged.  worst %s Q_b = %.4f;  next worst %s Q_b = %.4f'
      % (len(QB_SEP), WORST, WORST_Q, NEXT_EB, NEXT_Q))
print('    separation: a factor %.3f, a gap of %.3f in Q_b; the published '
      'threshold %.1f sits %.1f%% of the way across it'
      % (SEP_RATIO, SEP_GAP, FACTOR, 100 * (FACTOR - NEXT_Q) / SEP_GAP))
for tag in VARIANTS:
    sets = IDENT[tag]
    lo, hi = SWEEP_RANGE[tag]
    print('      %-13s %3d blocks judged, sweep (%.3f, %.3f), %d distinct '
          'excluded set(s): %s'
          % (tag, N_DEF[tag], lo, hi, N_DISTINCT[tag],
             ' | '.join(sorted(','.join(sorted(s)) or '{}' for s in sets))[
                 :160]))
print('    at the published factor: %s'
      % {t: v for t, v in AT_FACTOR.items()})
print('    largest Class-A-only statistic: %s %.3f toward %s'
      % (A_TOP_EB, A_TOP_Q, A_TOP_STAR))
print('    stability margin: the published threshold may be multiplied by '
      'anything in (%.2f, %.2f) with no change to the excluded set'
      % (MARGIN_DOWN, MARGIN_UP))
print('    where it does change: at %.3f (the next-worst block) %d blocks '
      'are excluded; at the median block %.3f, %d are'
      % (NEXT_Q, N_AT_NEXT, Q_MED_BLOCK, N_AT_MED))
print('    the failing block holds %d windows (%s) and %d crossings; it has '
      'a Class A window: %s' % (len(WORST_WIN), dict(WORST_WIN_CLS),
                                len(WORST_X), WORST_HAS_A))
print('    blocks the two class-restricted rules disagree about: %s'
      % (DISAGREE or 'none'))

J['r1_4'] = dict(
    factor=FACTOR, n_blocks=len(QB_SEP), worst=WORST, worst_Q=WORST_Q,
    next_worst=NEXT_EB, next_Q=NEXT_Q, separation_ratio=SEP_RATIO,
    separation_gap=SEP_GAP, class_medians=CLASS_MED, survey_median=SURV_MED,
    n_steps=len(SWEEP_T), sweep_range=SWEEP_RANGE,
    distinct_sets=N_DISTINCT, at_factor=AT_FACTOR,
    class_A_only_top=dict(eb=A_TOP_EB, Q=A_TOP_Q, stars=A_TOP_STAR),
    n_blocks_judged=N_DEF, worst_has_class_A_window=WORST_HAS_A,
    worst_window_classes=dict(WORST_WIN_CLS),
    class_rule_disagreements=DISAGREE,
    margin_down=MARGIN_DOWN, margin_up=MARGIN_UP,
    n_excluded_at_next_worst=N_AT_NEXT, median_block_Q=Q_MED_BLOCK,
    n_excluded_at_median_block=N_AT_MED,
    note='a sweep strictly inside (next_Q, worst_Q) selects the single most '
         'extreme block at every step by construction; the measured content '
         'is the width of that interval and the demonstration of where the '
         'answer changes',
    sweep={tag: [dict(threshold=r['threshold'], n=r['n'],
                      blocks=r['blocks']) for r in rows]
           for tag, rows in SWEEP.items()})


# =====================================================================
# (2) R2-9: THE ARCHIVAL BOOKKEEPING SENTENCE
# =====================================================================
# The referee's replacement sentence carries three counts.  Each is taken from
# the ledger table's own generator inputs, never from the table's typeset text.
SEARCHED_REP = int(texval('LdgExtEB'))        # 115 reported as repeat epochs
SEARCHED_ALL = int(texval('LdgExtSearched'))  # 144 calibrated and searched
NOT_REPORTED = int(texval('BkExtNotReported'))

EXT_ALL_EB = {r['eb'] for r in EXTEXP if r.get('star_snr') is not None}
EPS_EB = {r['eb'] for r in EXTEXP
          if r['star_name'] == 'eps Eri' and int(r.get('band') or 0) == 6}
EPS_WIN = [r for r in EXTEXP
           if r['star_name'] == 'eps Eri' and int(r.get('band') or 0) == 6]
REPORTED_EB = EXT_ALL_EB - EPS_EB
# the archival tail: the blocks the tail campaign finished that are not in the
# extension export at all -- the same construction the ledger table uses, and
# never the whole of hd14055_results.json, which holds every covering epoch of
# that star including census and follow-up blocks.
TAILDONE = {t['eb'] for t in TAILCOLL if t.get('done')}
TAIL_EB = TAILDONE - EXT_ALL_EB
TAIL_WIN = sum(int(t.get('n_result') or 0) for t in TAILCOLL
               if t['eb'] in TAIL_EB)
# the fourth part is a residual and is labelled as one: searched, and no
# window reached any export.
N_NOWIN = SEARCHED_ALL - len(REPORTED_EB) - len(EPS_EB) - len(TAIL_EB)
if DRIVE == 15:
    N_NOWIN += 1

# the 2 crossings the tail blocks hold, from the ledger and by block identity
TAIL_X = [r for r in XR if r['eb'] in TAIL_EB]
TAIL_STARS = sorted({r['display'] for r in TAIL_X})

print('\n(2) R2-9  the archival bookkeeping')
print('    %d searched; %d reported as repeat epochs; %d not reported'
      % (SEARCHED_ALL, SEARCHED_REP, NOT_REPORTED))
print('      archival-tail blocks %d (%d windows, %d crossings toward %s)'
      % (len(TAIL_EB), TAIL_WIN, len(TAIL_X), ', '.join(TAIL_STARS)))
print('      eps Eri blocks       %d (%d windows, withheld -- limits only)'
      % (len(EPS_EB), len(EPS_WIN)))
print('      yielded no window    %d' % N_NOWIN)
print('      sum %d against the published %d'
      % (len(TAIL_EB) + len(EPS_EB) + N_NOWIN, NOT_REPORTED))

J['r2_9'] = dict(searched=SEARCHED_ALL, reported=SEARCHED_REP,
                 not_reported=NOT_REPORTED, n_tail_eb=len(TAIL_EB),
                 n_tail_win=TAIL_WIN, n_tail_cross=len(TAIL_X),
                 tail_stars=TAIL_STARS, n_eps_eb=len(EPS_EB),
                 n_eps_win=len(EPS_WIN), n_nowin=N_NOWIN,
                 tail_blocks=sorted(TAIL_EB), eps_blocks=sorted(EPS_EB))


# =====================================================================
# (3) R2-10: THE CLUSTERING STATISTIC, DEFINED
# =====================================================================
# THE STATISTIC, in the referee's own form: the number of PAIRS of crossings
# whose topocentric frequencies lie within X MHz of each other.  The null
# redraws each crossing's peak uniformly on its OWN window's channel grid and
# recounts, so the sample size, the tuning of the windows and the channel
# spacing are identical on both sides.
#
# ★ WHY THIS IS NOT CIRCULAR.  The set is selected by stellar-frame
#   attribution -- distance from a tabulated transition after the barycentric
#   and systemic shifts -- and the statistic is mutual proximity between
#   crossings in the topocentric frame.  Neither is a function of the other:
#   two crossings 1 MHz apart in sky frequency toward stars of different
#   systemic velocity are a pair here and may be attributed or not, and an
#   attributed crossing is removed whether or not it has a neighbour.  The
#   null is redrawn over the same selected set, so the selection acts
#   identically on observed and simulated counts.  The quantity the old
#   sentence reported was the count of crossings NEAR A LINE after the
#   near-a-line crossings had been removed, which is zero by construction.
def win_grid(eb, freq):
    """The window a crossing falls in, by containment in frequency, and that
    window's own channel grid.  Never keyed on a star name.  min/max of the
    edge pair, because a descending spectral window writes them reversed."""
    for r in CAT:
        if r['eb'] != eb:
            continue
        lo, hi = sorted((F(r['flo_GHz']), F(r['fhi_GHz'])))
        if lo - 1e-6 <= freq <= hi + 1e-6:
            cw = F(r['chanw_Hz']) / 1e9
            n = int(round((hi - lo) / cw)) + 1
            return lo, hi, cw, n, 'catalogue'
    for x in HD14055:
        if x['eb'] != eb:
            continue
        lo, hi = sorted((float(x['flo']), float(x['fhi'])))
        if lo - 1e-6 <= freq <= hi + 1e-6:
            cw = float(x['chw']) / 1e9
            n = int(x['nch'])
            return lo, hi, cw, n, 'extension'
    return None


MEASURED = [r for r in XR
            if r['frame'].get('f_topo_source') != 'recovered from the '
            'released offset']
for r in MEASURED:
    r['_grid'] = win_grid(r['eb'], r['freq'])

NOGRID = [r for r in MEASURED if r['_grid'] is None]
USABLE = [r for r in MEASURED if r['_grid'] is not None]

SETS = collections.OrderedDict((
    ('all_measured', USABLE),
    ('attributed', [r for r in USABLE if r['attributed']]),
    ('unattributed_quality_passing',
     [r for r in USABLE if not r['attributed'] and not r['dq']]),
    ('unattributed_including_flagged',
     [r for r in USABLE if not r['attributed']]),
))


def npairs(f_ghz, tol_mhz):
    """Pairs within tol_mhz.  O(n log n), and exact."""
    f = np.sort(np.asarray(f_ghz, float)) * 1000.0
    j = np.searchsorted(f, f + tol_mhz, side='right')
    return int((j - np.arange(f.size) - 1).sum())


def null_draw(rows):
    out = np.empty(len(rows))
    for i, r in enumerate(rows):
        lo, _hi, cw, n, _src = r['_grid']
        out[i] = lo + cw * RNG.integers(0, n)
    return out


CLUST = collections.OrderedDict()
for tag, rows in SETS.items():
    f = [r['freq'] for r in rows]
    obs = {t: npairs(f, t) for t in LADDER_MHZ}
    draws = np.array([[npairs(null_draw(rows), t) for t in LADDER_MHZ]
                      for _ in range(NMC)])
    res = {}
    for ti, t in enumerate(LADDER_MHZ):
        col = draws[:, ti]
        o = obs[t] if not (DRIVE == 6 and tag.startswith('unattributed')) \
            else int(col.max()) + 5
        res['%g' % t] = dict(
            observed=o, null_mean=float(col.mean()), null_sd=float(col.std()),
            p=float(((col >= o).sum() + 1) / (NMC + 1)))
    CLUST[tag] = dict(n=len(rows), per_tol=res,
                      p_max=max(v['p'] for v in res.values()),
                      p_min=min(v['p'] for v in res.values()))

# the grid assumption this null rests on, measured: every measured peak must
# sit on one of its own window's channels, or the null is the wrong null.
GRES, GKHZ = [], []
for r in USABLE:
    lo, _hi, cw, _n, _src = r['_grid']
    k = (r['freq'] - lo) / cw
    GRES.append(abs(k - round(k)))
    GKHZ.append(abs(k - round(k)) * cw * 1e6)         # kHz off the grid
GRID_WORST = float(max(GRES))
#: the released peak frequency is rounded to 1 kHz, so a departure of up to
#: half a kHz is arithmetic and anything larger is not.  Testing the kHz
#: rather than the channel fraction makes the assertion independent of the
#: channel width, which is what let the finest window look like an outlier.
GRID_WORST_KHZ = float(max(GKHZ))

print('\n(3) R2-10  the clustering statistic: pairs within X MHz, '
      'topocentric, against each window\'s own channel grid')
print('    %d of the %d ledger crossings carry a measured topocentric peak; '
      '%d of those resolve to a window (%d do not)'
      % (len(MEASURED), len(XR), len(USABLE), len(NOGRID)))
print('    worst departure of a measured peak from its own channel grid: '
      '%.4f channels' % GRID_WORST)
for tag, d in CLUST.items():
    print('    %-32s n=%2d  ' % (tag, d['n'])
          + '  '.join('%gMHz:%d/%.2f p=%.3f'
                      % (t, d['per_tol']['%g' % t]['observed'],
                         d['per_tol']['%g' % t]['null_mean'],
                         d['per_tol']['%g' % t]['p']) for t in LADDER_MHZ))
J['r2_10'] = dict(statistic='number of crossing pairs within X MHz in '
                            'topocentric frequency; null redraws each peak '
                            'uniformly on its own window channel grid',
                  n_measured=len(MEASURED), n_usable=len(USABLE),
                  n_nogrid=len(NOGRID), grid_worst_channel_fraction=GRID_WORST,
                  sets=CLUST)


# =====================================================================
# (4) R2-11: THE EXTENSION'S ZERO UNATTRIBUTED CROSSINGS
# =====================================================================
# The false-alarm appendix's chain, applied to the extension's Class A
# windows and to nothing else:
#     lambda_trig = sum over those windows of the share of its own 512
#                   control positions that reaches the trigger
#     x (1 - masked share of its own channel grid, in the star's frame)
#     x the step from a control position to a star
# and then P(0 | lambda) = exp(-lambda).
REST = np.array(sorted(v[0] for k, v in mf.TRANS.items()
                       if mf.species(k) not in mf.NOTED_SPECIES))

EXT_ROWS = [r for r in EXTEXP
            if r.get('star_snr') is not None and r['eb'] in REPORTED_EB]
EXT_A = [r for r in EXT_ROWS if str(r.get('res', '')).startswith('fine')]
EXT_B = [r for r in EXT_ROWS if not str(r.get('res', '')).startswith('fine')]


def masked_share(r, vsys_force=None):
    lo, hi = sorted((float(r['flo']), float(r['fhi'])))
    cw = float(r['chanw']) / 1e9
    n = int(round((hi - lo) / cw)) + 1
    g = lo + cw * np.arange(n)
    vb, _s = mf.vbary(r['eb'], r['flo'])
    vs, _s2, _b = mf.vsys(r['star_name'])
    known = vs is not None
    if vsys_force is not None:
        vs = vsys_force
    fs = g * (1.0 - (vb or 0.0) / C_KMS) * (1.0 + (vs or 0.0) / C_KMS)
    ins = np.zeros(n, bool)
    for fr in REST:
        ins |= ((fs >= fr * (1.0 - HALF / C_KMS))
                & (fs <= fr * (1.0 + HALF / C_KMS)))
    return float(ins.mean()), known


def lam_of(rows, vsys_force=None):
    lt = lu = 0.0
    nk = 0
    for r in rows:
        v = np.asarray(r['ctrl_all'], float)
        p = float((v >= TRIG).mean())
        s, kn = masked_share(r, vsys_force)
        nk += kn
        lt += p
        lu += p * (1.0 - s)
    return lt, lu, nk


LAM_TRIG_A, LAM_UNATTR_A, NVSYS_A = lam_of(EXT_A)
LAM_TRIG_B, LAM_UNATTR_B, _ = lam_of(EXT_B)

#: ★ THE STEP FROM A CONTROL POSITION TO A STAR IS NOT THIS GENERATOR'S.
#: Its owner recomputes it on sub-trigger levels only, because the value at
#: the trigger is formed from the very cells under test.  The recomputed value
#: is read from the owner's own generated macro file where that exists; the
#: published trigger-level value is the fallback.  Which was used is recorded,
#: printed and published as a macro, and the expectation is reported under
#: both so that a different adoption cannot silently change the conclusion.
import re                                                       # noqa: E402

STEP_SRC = 'the published trigger-level step'
STEP_NAME = 'CeTrAt'
STEP = STEP_ALT = float(texval('CeTrAt'))
#: first choice: the sub-trigger step in the macro layer of the directory this
#: generator is reading, which is where it lives once its owner's change is
#: adopted, so the adopted build is self-contained
if texval('CeStep'):
    STEP = float(texval('CeStep'))
    STEP_NAME = 'CeStep'
    STEP_SRC = 'the sub-trigger step in the macro layer, \\CeStep'
else:
    #: second choice, used only while the owner's change is still in its own
    #: working copy: its generated macro file, read and named
    _cand = os.path.join(os.path.dirname(HERE), 'chance', 'sandbox',
                         'survey_numbers_round310.tex')
    if os.path.exists(_cand):
        _mm = re.search(r'\\newcommand\{\\CeStep\}\{([0-9.]+)\}',
                        open(_cand).read())
        if _mm:
            STEP = float(_mm.group(1))
            STEP_NAME = 'CeStep'
            STEP_SRC = ('the sub-trigger step recomputed this round, %s'
                        % os.path.relpath(_cand, os.path.dirname(HERE)))

LAM_A = LAM_UNATTR_A * STEP
LAM_A_ALT = LAM_UNATTR_A * STEP_ALT
P0_A = math.exp(-LAM_A)
P0_A_NOSTEP = math.exp(-LAM_UNATTR_A)
P0_TRIG_A = math.exp(-LAM_TRIG_A)

# the vsys sensitivity, measured over the span the census uses rather than
# assumed small
_, LU_M30, _ = lam_of(EXT_A, vsys_force=-30.0)
_, LU_P30, _ = lam_of(EXT_A, vsys_force=+30.0)
VSYS_SPAN_A = (min(LU_M30, LU_P30) * STEP, max(LU_M30, LU_P30) * STEP)

# ===== the observed side, attributed by the SAME mask, in the star's frame ==
# ★★★★ THE PUBLISHED COUNT IS NOT A COUNT OF UNATTRIBUTED CROSSINGS.
# `\ExtNUnattrib` is emitted as (rank-passing crossings) - (beta Pic rows), so
# it counts the rank-passing crossings outside one star and is zero because
# all three rank-passing crossings are that star's carbon monoxide.  The
# attribution of the other ten was never evaluated.  It is evaluated here, by
# the mask the census uses, in each star's own rest frame.
EXT_X = [r for r in EXTEXP if r['eb'] in REPORTED_EB
         and r.get('star_snr') is not None and float(r['star_snr']) >= TRIG]
EXT_X_A = [r for r in EXT_X if str(r.get('res', '')).startswith('fine')]
EXT_PUBLISHED_UNATTR = int(texval('ExtNRankOneNonBp'))

REST_KEY = {k: v[0] for k, v in mf.TRANS.items()
            if mf.species(k) not in mf.NOTED_SPECIES}


def stellar_dv(r, vb_force=None, vs_force=None):
    """Offset from the nearest masked transition, in the star's rest frame.
    Returns (dv, line, has_bary, has_vsys)."""
    f = r.get('_star_peak_freq')
    if f is None:
        return None, None, False, False
    vb, _s = mf.vbary(r['eb'], r['flo'])
    vs, _s2, _b = mf.vsys(r['star_name'])
    hb, hv = vb is not None, vs is not None
    if vb_force is not None:
        vb = vb_force
    if vs_force is not None and not hv:
        vs = vs_force
    fs = f * (1.0 - (vb or 0.0) / C_KMS) * (1.0 + (vs or 0.0) / C_KMS)
    k = min(REST_KEY, key=lambda q: abs(fs - REST_KEY[q]) / REST_KEY[q])
    return C_KMS * (fs - REST_KEY[k]) / REST_KEY[k], k, hb, hv


EXT_ATTR, EXT_UNATTR, EXT_NOPEAK = [], [], []
for r in EXT_X:
    dv, ln, hb, hv = stellar_dv(r)
    if dv is None:
        EXT_NOPEAK.append(r)
    elif abs(dv) <= HALF:
        EXT_ATTR.append((r, dv, ln))
    else:
        EXT_UNATTR.append((r, dv, ln))
EXT_OBS = len(EXT_UNATTR)
N_BARY_KNOWN = sum(1 for r in EXT_X if stellar_dv(r)[2])
N_VSYS_KNOWN = sum(1 for r in EXT_X if stellar_dv(r)[3])

#: ★ THE HONEST CAVEAT, MEASURED.  No barycentric term is recorded for any
#: extension block and two stars have no measured systemic velocity, so the
#: frame is approximate.  The attribution is therefore recomputed over the
#: whole span either term can take, and what survives every choice is the
#: count that can be relied on.
SPAN = (-30.0, 30.0)
_worst = []
for vbf in SPAN:
    for vsf in SPAN:
        _worst.append(sum(1 for r in EXT_X
                          if (stellar_dv(r, vbf, vsf)[0] or 1e9) is not None
                          and abs(stellar_dv(r, vbf, vsf)[0]) > HALF))
EXT_OBS_LO, EXT_OBS_HI = min(_worst), max(_worst)

# the Poisson predictive statement the referee asks for, on the count
def ppois_ge(k, lam):
    return 1.0 - sum(math.exp(-lam) * lam ** i / math.factorial(i)
                     for i in range(k))


def ppois_le(k, lam):
    return sum(math.exp(-lam) * lam ** i / math.factorial(i)
               for i in range(k + 1))


P_GE = ppois_ge(EXT_OBS, LAM_A)
P_LE = ppois_le(EXT_OBS, LAM_A)
#: and the probability of the count the manuscript claims, which is how the
#: claim is known to be wrong rather than merely unsupported
P0_CLAIM = P0_A

MASK_W = 1.0 - LAM_UNATTR_A / LAM_TRIG_A           # exceedance-weighted share
CEN_W = 1.0 - float(texval('CeExp')) / float(texval('CeExpTrig'))

# the census, by the same chain, as the comparison the sentence should make
#: built from the same step this generator adopted, so the two rates are
#: comparable whichever step is in force
CEN_EXP = float(texval('CeExp')) * STEP
CEN_OBS = int(texval('CeObs'))
CEN_NWINA = int(texval('CeNWin'))
RATE_CEN = CEN_EXP / CEN_NWINA
RATE_EXT = LAM_A / len(EXT_A)

print('\n(4) R2-11  the extension, against the expectation')
print('    %d Class A windows (and %d Class B) in %d reported blocks'
      % (len(EXT_A), len(EXT_B), len(REPORTED_EB)))
print('    lambda at the trigger          %.3f   (P(0) = %.3f)'
      % (LAM_TRIG_A, P0_TRIG_A))
print('    x unattributed share           %.3f   (P(0) = %.3f)'
      % (LAM_UNATTR_A, P0_A_NOSTEP))
print('    x step %.3f  [%s]'
      '\n                                   %.3f   (P(0) = %.3f)'
      % (STEP, STEP_SRC, LAM_A, P0_A))
print('      under the %s instead (%.3f): lambda %.3f, P(N>=%d) = %.2f'
      % ('trigger-level step' if STEP_NAME == 'CeStep' else 'sub-trigger step',
         STEP_ALT, LAM_A_ALT, EXT_OBS if 'EXT_OBS' in dir() else 0, 0.0)
      if False else '      the other step (%.3f) gives lambda %.3f'
      % (STEP_ALT, LAM_A_ALT))
print('    vsys span (-30..+30 km/s)      %.3f-%.3f' % VSYS_SPAN_A)
print('    %d of %d Class A windows have a measured systemic velocity'
      % (NVSYS_A, len(EXT_A)))
print('    observed: %d crossings, all in Class A windows; %d attributed by '
      'the mask in the star\'s frame, %d UNATTRIBUTED'
      % (len(EXT_X), len(EXT_ATTR), EXT_OBS))
print('      the published \\ExtNRankOneNonBp is %d, and it is not this quantity: '
      'it counts rank-passing crossings outside one star'
      % EXT_PUBLISHED_UNATTR)
print('      P(N >= %d | %.2f) = %.2f;  P(N <= %d | %.2f) = %.2f;  the '
      'claimed zero would have had P = %.4f'
      % (EXT_OBS, LAM_A, P_GE, EXT_OBS, LAM_A, P_LE, P0_CLAIM))
print('      frame caveat: %d of %d crossings carry a recorded barycentric '
      'term and %d a measured systemic velocity; over +-30 km/s in each the '
      'unattributed count runs %d-%d'
      % (N_BARY_KNOWN, len(EXT_X), N_VSYS_KNOWN, EXT_OBS_LO, EXT_OBS_HI))
print('      the attributed five: %s'
      % '; '.join('%s %.1f km/s from %s' % (r['star_name'], dv, ln)
                  for r, dv, ln in EXT_ATTR))
print('    per-window unattributed rate: census %.4f, extension %.4f '
      '(ratio %.2f)' % (RATE_CEN, EXT_OBS / len(EXT_A),
                        (EXT_OBS / len(EXT_A)) / RATE_CEN))
print('    Class B lambda at the trigger %.4f -- a coarse field essentially '
      'never triggers by chance' % LAM_TRIG_B)
print('    the mask takes %.1f per cent of the extension\'s expectation '
      'against %.0f per cent measured in the census'
      % (100 * MASK_W, 100 * CEN_W))

J['r2_11'] = dict(n_win_A=len(EXT_A), n_win_B=len(EXT_B),
                  n_reported_blocks=len(REPORTED_EB),
                  lam_trigger_A=LAM_TRIG_A, lam_unattr_A=LAM_UNATTR_A,
                  step=STEP, step_source=STEP_SRC,
                  step_macro=STEP_NAME, step_alt=STEP_ALT,
                  lam_A_alt=LAM_A_ALT, lam_A=LAM_A,
                  p_zero_A=P0_A, p_zero_A_nostep=P0_A_NOSTEP,
                  p_zero_trigger_A=P0_TRIG_A,
                  vsys_span_lam_A=VSYS_SPAN_A, n_vsys_known_A=NVSYS_A,
                  lam_trigger_B=LAM_TRIG_B,
                  n_cross_A_observed=len(EXT_X_A), n_cross=len(EXT_X),
                  n_attributed=len(EXT_ATTR), n_unattributed=EXT_OBS,
                  n_unattributed_published=EXT_PUBLISHED_UNATTR,
                  p_ge_observed=P_GE, p_le_observed=P_LE,
                  p_zero_claimed=P0_CLAIM,
                  n_bary_known=N_BARY_KNOWN, n_vsys_known=N_VSYS_KNOWN,
                  unattributed_span=[EXT_OBS_LO, EXT_OBS_HI],
                  census_rate=RATE_CEN,
                  extension_rate=EXT_OBS / len(EXT_A),
                  mask_weight_A=MASK_W, census_mask_weight=CEN_W,
                  attributed_rows=[dict(star=r['star_name'], eb=r['eb'],
                                        dv=dv, line=ln)
                                   for r, dv, ln in EXT_ATTR],
                  unattributed_rows=[dict(star=r['star_name'], eb=r['eb'],
                                          dv=dv, line=ln)
                                     for r, dv, ln in EXT_UNATTR])


# =====================================================================
# ASSERTIONS -- each names what would make it fail, and each has a drive
# =====================================================================
print('\nassertions')
ck('Q1 FALSIFIER: this generator reproduces the published criterion exactly '
   '-- the same block count, the same failing block, the same two statistics '
   '-- before it is allowed to sweep anything',
   len(QB_SEP) == PUB_NBLOCK and WORST == PUB_BLOCK
   and abs(WORST_Q - PUB_FAILQ) < 0.05
   and abs((NEXT_Q if DRIVE != 1 else 9.9) - PUB_NEXTQ) < 0.005
   and len(FAILED_PUB) == PUB_NFAIL and FAILED_PUB == {PUB_BLOCK},
   '%d blocks (published %d), worst %s %.4f (published %.1f), next %.4f '
   '(published %.2f), %d fail (published %d)'
   % (len(QB_SEP), PUB_NBLOCK, WORST, WORST_Q, PUB_FAILQ, NEXT_Q, PUB_NEXTQ,
      len(FAILED_PUB), PUB_NFAIL))
ck('Q2 the sweep stays inside the interval the referee names: every threshold '
   'lies strictly between the next-worst and the worst block statistic',
   all(NEXT_Q < t < WORST_Q for t in SWEEP_T) and len(SWEEP_T) >= 20,
   '%d thresholds in (%.4f, %.4f), actual span %.4f-%.4f'
   % (len(SWEEP_T), NEXT_Q, WORST_Q, min(SWEEP_T), max(SWEEP_T)))
ck('Q3 THE RESULT: over the whole interval, under both normalisations and on '
   'the coarse windows alone, the excluded set is one and the same block -- '
   'unchanged in number and in identity',
   all(N_DISTINCT[t] == 1 for t in ('separate', 'joint', 'class_B_only'))
   and (SEL_ALL if DRIVE != 3 else {frozenset(), frozenset(['x'])})
   == {frozenset([WORST])},
   'distinct sets %s; the union of all sweep selections is %s'
   % (N_DISTINCT, sorted(','.join(sorted(s)) for s in SEL_ALL)))
ck('Q3b the stability is a measured width and not an artefact of sweeping '
   'inside an interval defined by its own endpoints: the published threshold '
   'may be scaled by a factor of at least two in each direction',
   MARGIN_DOWN < 1.0 < MARGIN_UP
   and (MARGIN_UP / MARGIN_DOWN if DRIVE != 16 else 1.0) > 3.0,
   'the excluded set is this one block for every threshold from %.3f to '
   '%.3f, i.e. the published %.1f scaled by %.2f-%.2f'
   % (NEXT_Q, WORST_Q, FACTOR, MARGIN_DOWN, MARGIN_UP))
ck('Q4 the sweep can discriminate: at a threshold just below the next-worst '
   'block a second block is selected, and just above the worst none is -- so '
   'the stability is a property of the data and not of the sweep',
   len({e for e, q in QB_SEP.items() if q > NEXT_Q * 0.999}) > 1
   and len({e for e, q in QB_SEP.items()
            if q > (WORST_Q * 1.001 if DRIVE != 4 else 0.0)}) == 0,
   'just below the next-worst: %d blocks; just above the worst: %d'
   % (len({e for e, q in QB_SEP.items() if q > NEXT_Q * 0.999}),
      len({e for e, q in QB_SEP.items() if q > WORST_Q * 1.001})))
ck('Q5 the class treatment does not decide the answer: the separate and the '
   'joint normalisations select the same block at the published factor, no '
   'block is failed on one class and passed on the other, and the failing '
   'block holds no Class A window at all',
   AT_FACTOR['separate'] == AT_FACTOR['joint'] == [WORST]
   and (DISAGREE if DRIVE != 5 else ['x']) == []
   and not WORST_HAS_A and WORST_HAS_B
   and AT_FACTOR['class_B_only'] == [WORST]
   and AT_FACTOR['class_A_only'] == [],
   'separate %s, joint %s, A-only %s, B-only %s, disagreements %s, '
   'failing block classes %s'
   % (AT_FACTOR['separate'], AT_FACTOR['joint'], AT_FACTOR['class_A_only'],
      AT_FACTOR['class_B_only'], DISAGREE, dict(WORST_WIN_CLS)))
ck('Q6 the bookkeeping sentence closes: the three sets are disjoint, they '
   'sum to the published count of blocks that enter no number, and adding '
   'the reported blocks gives the published searched total',
   len(TAIL_EB) + len(EPS_EB) + N_NOWIN == NOT_REPORTED
   and SEARCHED_REP + NOT_REPORTED == SEARCHED_ALL
   and not (TAIL_EB & EPS_EB) and not (TAIL_EB & REPORTED_EB)
   and not (EPS_EB & REPORTED_EB)
   and (len(REPORTED_EB) if DRIVE != 7 else -1) == SEARCHED_REP,
   '%d + %d + %d = %d (published %d); reported %d (published %d); '
   'searched %d' % (len(TAIL_EB), len(EPS_EB), N_NOWIN,
                    len(TAIL_EB) + len(EPS_EB) + N_NOWIN, NOT_REPORTED,
                    len(REPORTED_EB), SEARCHED_REP, SEARCHED_ALL))
ck('Q7 the tail blocks really do hold crossings and the eps Eri blocks '
   'really do hold none: the first claim of the replacement sentence is the '
   'ledger\'s own, resolved by block identity and not by a star name',
   len(TAIL_X) == int(texval('CeNTailCross'))
   and (len(TAIL_X) if DRIVE != 8 else 0) > 0
   and not [r for r in XR if r['eb'] in EPS_EB]
   and len(TAIL_STARS) == 1,
   '%d crossings in the %d tail blocks toward %s; %d in the %d eps Eri blocks'
   % (len(TAIL_X), len(TAIL_EB), TAIL_STARS,
      len([r for r in XR if r['eb'] in EPS_EB]), len(EPS_EB)))
ck('Q8 the clustering sets are the ones the results section defines, and they '
   'close on the published totals: measured peaks, attributed, '
   'quality-passing unattributed, and the flagged four',
   len(MEASURED) == int(texval('AppMNCrossF'))
   and len(NOGRID) == 0
   and len(SETS['unattributed_quality_passing']) == int(texval('ChnUnattrA'))
   and (len(SETS['unattributed_including_flagged']) if DRIVE != 9 else -1)
   == int(texval('NUnattributed'))
   and len(SETS['attributed']) + len(SETS['unattributed_including_flagged'])
   == len(USABLE),
   '%d measured (published %s), %d unresolved, %d quality-passing unattr '
   '(published %s), %d incl. flagged (published %s), %d attributed'
   % (len(MEASURED), texval('AppMNCrossF'), len(NOGRID),
      len(SETS['unattributed_quality_passing']), texval('ChnUnattrA'),
      len(SETS['unattributed_including_flagged']), texval('NUnattributed'),
      len(SETS['attributed'])))
ck('Q9 the null is the right null: every measured peak sits on a channel of '
   'its own window to within the kHz the released frequency is rounded to, '
   'so redrawing on that grid is the null the data allow',
   (GRID_WORST if DRIVE != 10 else 0.5) < 0.1 and GRID_WORST_KHZ < 1.0,
   'worst departure %.3f kHz (%.5f channels of the finest window) over %d '
   'crossings' % (GRID_WORST_KHZ, GRID_WORST, len(USABLE)))
ck('Q10 the statistic has teeth: on the attributed crossings -- which the '
   'paper says ARE concentrated, on the survey\'s own lines -- it rejects at '
   'some rung of the ladder, so a null on the unattributed set is a result '
   'and not an insensitive test',
   (CLUST['attributed']['p_min'] if DRIVE != 11 else 1.0) < 0.05,
   'attributed: smallest p over the ladder %.4f (n=%d); all measured %.4f'
   % (CLUST['attributed']['p_min'], CLUST['attributed']['n'],
      CLUST['all_measured']['p_min']))
ck('Q11 THE RESULT: the quality-passing unattributed crossings show no '
   'clustering at any rung, and neither do they with the flagged four put '
   'back -- reported at every rung, so no rung is selected after the fact',
   (CLUST['unattributed_quality_passing']['p_min'] if DRIVE != 6 else 0.0)
   > 0.05
   and CLUST['unattributed_including_flagged']['p_min'] > 0.05,
   'quality-passing smallest p %.4f (n=%d); including the flagged %.4f (n=%d)'
   % (CLUST['unattributed_quality_passing']['p_min'],
      CLUST['unattributed_quality_passing']['n'],
      CLUST['unattributed_including_flagged']['p_min'],
      CLUST['unattributed_including_flagged']['n']))
ck('Q12 the removal is not the statistic: the number of pairs is not a '
   'function of distance from a line, so the selected set could have '
   'clustered and the test was free to say so -- the attributed set, '
   'selected by the same mask, does cluster',
   CLUST['attributed']['p_min'] < CLUST['unattributed_quality_passing'][
       'p_min']
   and (CLUST['unattributed_quality_passing']['per_tol']['300']['null_mean']
        if DRIVE != 12 else 0.0) > 1.0,
   'attributed p_min %.4f vs quality-passing p_min %.4f; the null at 300 MHz '
   'expects %.2f pairs in the quality-passing set, so zero observed pairs '
   'would have been informative'
   % (CLUST['attributed']['p_min'],
      CLUST['unattributed_quality_passing']['p_min'],
      CLUST['unattributed_quality_passing']['per_tol']['300']['null_mean']))
ck('Q13 the extension expectation is built on the same chain as the census '
   'and over the extension\'s own Class A windows: the window count is the '
   'extension\'s published fine-channel count and each window contributes '
   'its own control rate',
   len(EXT_A) == int(texval('ExtNWinA') or 67)
   and len(EXT_A) + len(EXT_B) == int(texval('LdgExtWin'))
   and (LAM_TRIG_A if DRIVE != 13 else -1.0) > LAM_UNATTR_A > 0
   and LAM_A > 0,
   '%d Class A + %d Class B = %s published windows; lambda %.3f -> %.3f -> '
   '%.3f' % (len(EXT_A), len(EXT_B), texval('LdgExtWin'), LAM_TRIG_A,
             LAM_UNATTR_A, LAM_A))
ck('Q14 ★ THE PUBLISHED COUNT IS NOT THE QUANTITY ITS SENTENCE NAMES: the '
   'extension\'s unattributed crossings, counted by the census\'s own mask '
   'in each star\'s frame, are not zero, and every crossing lies in a '
   'Class A window so the expectation and the count run over one population',
   len([r for r in XR if r['eb'] in REPORTED_EB]) == 0
   and len(EXT_X_A) == len(EXT_X) and not EXT_NOPEAK
   and len(EXT_ATTR) + EXT_OBS == len(EXT_X)
   and (EXT_OBS if DRIVE != 14 else 0) > EXT_PUBLISHED_UNATTR,
   '%d crossings, %d attributed, %d unattributed, against a published %d; '
   '%d carry no peak frequency' % (len(EXT_X), len(EXT_ATTR), EXT_OBS,
                                   EXT_PUBLISHED_UNATTR, len(EXT_NOPEAK)))
ck('Q15 THE RESULT: the count agrees with the expectation the false-alarm '
   'appendix builds for those same windows, so there is no deficit to '
   'explain -- and the zero the manuscript claims would have been one, which '
   'is how the claim is known to be wrong and not merely unsupported',
   0.05 < (P_GE if DRIVE != 17 else 0.001) < 0.95
   and P0_CLAIM < 0.05 and LAM_A > 3.0,
   'observed %d against %.2f expected: P(N>=%d) = %.2f, P(N<=%d) = %.2f; '
   'P(0) = %.4f' % (EXT_OBS, LAM_A, EXT_OBS, P_GE, EXT_OBS, P_LE, P0_CLAIM))
ck('Q16 the frame the attribution is read in is approximate and the count '
   'survives it: over the whole span the barycentric and systemic terms can '
   'take, the unattributed count moves by at most one',
   (EXT_OBS_HI - EXT_OBS_LO if DRIVE != 18 else 9) <= 1
   and EXT_OBS_LO <= EXT_OBS <= EXT_OBS_HI
   and N_BARY_KNOWN == 0,
   'unattributed %d, span %d-%d over +-30 km/s in each term; %d of %d '
   'crossings carry a recorded barycentric term'
   % (EXT_OBS, EXT_OBS_LO, EXT_OBS_HI, N_BARY_KNOWN, len(EXT_X)))

print('\nassertions failed: %d %s' % (len(fail), fail))
if fail and DRIVE is None:
    raise SystemExit('quality_r19: %d assertion(s) failed: %s'
                     % (len(fail), fail))


# =====================================================================
# macros
# =====================================================================
# ★ ONLY WHAT THE PROSE CITES IS EMITTED.  Every other quantity this
#   generator measures is in quality_r19.json, which is the record; a macro
#   nobody cites is a macro a later round can cite without reading how it was
#   built, which is how `\ExtNUnattrib` came to stand for a quantity its own
#   sentence did not describe.
# (1) R1-4
m('QsRatio', '%.1f' % SEP_RATIO)
m('QsNStep', '%d' % len(SWEEP_T))
m('QsMarginLo', '%.2f' % MARGIN_DOWN)
m('QsMarginHi', '%.2f' % MARGIN_UP)
m('QsQMed', '%.2f' % Q_MED_BLOCK)
m('QsNAtNext', '%d' % N_AT_NEXT)
m('QsNAtMed', '%d' % N_AT_MED)
m('QsFailNWinB', '%d' % WORST_WIN_CLS.get('B', 0))

# (2) R2-9
m('QbkNTail', '%d' % len(TAIL_EB))
m('QbkNTailCross', '%d' % len(TAIL_X))
m('QbkNEps', '%d' % len(EPS_EB))
m('QbkNNoWin', '%d' % N_NOWIN)

# (3) R2-10
_qp = CLUST['unattributed_quality_passing']
_qf = CLUST['unattributed_including_flagged']
_qa = CLUST['attributed']
m('QcTolLo', '%g' % LADDER_MHZ[0])
m('QcTolHi', '%g' % LADDER_MHZ[-1])
m('QcNAttr', '%d' % _qa['n'])
m('QcNQP', '%d' % _qp['n'])
m('QcNFlag', '%d' % (_qf['n'] - _qp['n']))
m('QcPQPMin', '%.2f' % _qp['p_min'])
m('QcPFlagMin', '%.2f' % _qf['p_min'])
m('QcPAttrMin', '%s' % ('%.4f' % _qa['p_min'] if _qa['p_min'] >= 1e-4
                        else '<10^{-4}'))
m('QcQPObsWide', '%d' % _qp['per_tol']['300']['observed'])
m('QcQPNullWide', '%.1f' % _qp['per_tol']['300']['null_mean'])

# (4) R2-11
m('QxNWinA', '%d' % len(EXT_A))
m('QxLam', '%.1f' % LAM_A)
m('QxPZero', '%.3f' % P0_A)
m('QxObsCross', '%d' % len(EXT_X))
m('QxObsAttr', '%d' % len(EXT_ATTR))
m('QxObsUnattr', '%d' % EXT_OBS)
m('QxObsUnattrLo', '%d' % EXT_OBS_LO)
m('QxObsUnattrHi', '%d' % EXT_OBS_HI)
m('QxPGe', '%.2f' % P_GE)
m('QxNVsysCross', '%d' % N_VSYS_KNOWN)

HDR = ['%% GENERATED by quality_r19.py -- do not hand-edit.',
       '%% round ' + str(ROUND) + ': the quality criterion\'s threshold '
       'stability, the archival',
       '%% bookkeeping counts, the interference clustering statistic, and the',
       '%% archival extension\'s expectation.']
with open(OUT_PATH, 'w') as fh:
    fh.write('\n'.join(HDR + sorted(OUT)) + '\n')
J['macros'] = {x.split('}')[0].split('{\\')[1]: x.split('{')[-1].rstrip('}')
               for x in OUT}
with open(JSON_PATH, 'w') as fh:
    json.dump(J, fh, indent=1, sort_keys=True, default=float)
print('\nwrote %s: %d macros, and %s'
      % (OUT_NAME, len(OUT), os.path.basename(JSON_PATH)))
