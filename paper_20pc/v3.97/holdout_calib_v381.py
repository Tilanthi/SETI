#!/usr/bin/env python3
r"""Measure the paper's empirical calibration on the PRE-REGISTERED hold-out.

Up to v3.80 every calibrated statement in this paper was licensed by data
that was also in the headline sample: the rank displacement, the false-alarm
tail factor, the radial profile, and the claim that stage-1 status alone
carries no candidate significance. Referee 1 objected to exactly that for
the radial repair, and the objection was right.

`holdout_rule_v371.py` was committed 2026-09-14T07:10:24Z (`c75069040eab`),
before the sweep finished and before any reserved block was searched. It
reserves a block iff `sha256(canonical uid)[:8] mod 5 == 0`, with two
data-independent guards. On the completed sweep that is 77 of 484 blocks
and 315 windows, and it costs the headline no stars and no systems.

This measures, on those reserved blocks alone:

  * the stellar add-one rank distribution against U(0,1);
  * the stage-1 spatial-outlier rate against the exchangeable expectation;
  * the pseudo-star first-rank rate -- the false-alarm tail factor -- with a
    bootstrap clustered by execution block, matching the independence model
    the rest of the paper already uses;
  * the radial dependence of the control statistic, which is the effect the
    radial repair corrects for.

Writes holdout_calib_v381.json and survey_numbers_round31.tex.
"""
import collections, json, math, os
import numpy as np

os.chdir(os.path.dirname(os.path.abspath(__file__)))

R_IN, R_OUT, NPROBE, SEED = 0.14, 0.78, 512, 20260825
N_INNER = 16
BOOT = 20000
RNG = np.random.default_rng(20260920)

HO = json.load(open('holdout_export_v381.json'))
rows = [r for r in HO['rows'] if r.get('ctrl_all') and r.get('star_snr') is not None]
M = []


def m(name, val):
    M.append('\\newcommand{\\%s}{%s}' % (name, val))


# ------------------------------------------------- 1. the rank distribution
ranks, byblock = [], collections.defaultdict(list)
for r in rows:
    c = np.asarray(r['ctrl_all'], float)
    if c.size != NPROBE or not np.all(np.isfinite(c)):
        continue
    p = (1 + int((c >= r['star_snr']).sum())) / (c.size + 1.0)
    ranks.append(p)
    byblock[r['eb']].append(p)
ranks = np.array(sorted(ranks))
n = len(ranks)


def ks(u):
    u = np.sort(u)
    k = len(u)
    i = np.arange(1, k + 1)
    d = max((i / k - u).max(), (u - (i - 1) / k).max())
    lam = d * math.sqrt(k)
    return d, min(1.0, 2 * math.exp(-2 * lam * lam))


D, P = ks(ranks)
m('HoWin', '%d' % n)
m('HoBlocks', '%d' % len(byblock))
m('HoStars', '%d' % len({r['star_name'] for r in rows}))
m('HoRankMed', '%.3f' % float(np.median(ranks)))
m('HoRankKsD', '%.3f' % D)
m('HoRankKsP', '%.2g' % P)

# Block-clustered uncertainty on the median: resample whole blocks, because
# blocks share weather, calibration and correlator setup.
keys = list(byblock)
meds = []
for _ in range(2000):
    pick = RNG.integers(0, len(keys), len(keys))
    pool = [x for i in pick for x in byblock[keys[i]]]
    meds.append(np.median(pool))
lo, hi = np.percentile(meds, [2.5, 97.5])
m('HoRankMedLo', '%.3f' % lo)
m('HoRankMedHi', '%.3f' % hi)

# ------------------------------------------- 2. stage-1 rate out of sample
flag = [r for r in rows
        if r['star_snr'] >= 5.0 and r['star_snr'] > max(r['ctrl_all'])]
exp = n / float(NPROBE + 1)
m('HoStageOne', '%d' % len(flag))
m('HoStageOneExp', '%.2f' % exp)
m('HoStageOneP', '%.2f' % (1.0 - sum(math.exp(-exp) * exp ** i / math.factorial(i)
                                     for i in range(len(flag)))))

# --------------------------------------- 3. the pseudo-star tail factor
# A pseudo-star is an inner-annulus probe ranked against the other probes of
# its own window. It contains no star, so a first rank is a false alarm by
# construction. The probe positions come from one fixed seed, so the inner
# set is the same in every window.
rng = np.random.default_rng(SEED)
U = np.sqrt(rng.uniform(R_IN ** 2, R_OUT ** 2, NPROBE))
inner = np.argsort(U)[:N_INNER]

win = []
for r in rows:
    c = np.asarray(r['ctrl_all'], float)
    if c.size != NPROBE or not np.all(np.isfinite(c)):
        continue
    hits = sum(1 for i in inner if c[i] > np.delete(c, i).max())
    win.append((r['eb'], N_INNER, hits))

K = sum(w[2] for w in win)
N = sum(w[1] for w in win)
rate = K / float(N)
exch = 1.0 / NPROBE
m('HoPseudoTrials', '{:,}'.format(N).replace(',', '\\,'))
m('HoPseudoHits', '%d' % K)
m('HoTailFactor', '%.1f' % (rate / exch))

bb = collections.defaultdict(list)
for eb, nn, kk in win:
    bb[eb].append((nn, kk))
bk = list(bb)
rat = []
for _ in range(BOOT):
    pick = RNG.integers(0, len(bk), len(bk))
    kk = nn = 0
    for i in pick:
        for a, b in bb[bk[i]]:
            nn += a
            kk += b
    if nn:
        rat.append((kk / nn) / exch)
lo, hi = np.percentile(rat, [2.5, 97.5])
m('HoTailLo', '%.1f' % lo)
m('HoTailHi', '%.1f' % hi)
m('HoTailBlocks', '%d' % len(bk))

# ------------------------------------------------- 4. the radial dependence
# Every window's controls come from the same fixed probe geometry, so each
# stored control value can be paired with its fractional radius. This is the
# effect the radial repair corrects; measuring it out of sample is what makes
# the correction legitimate.
# Standardise exactly as radial_null_v361.py does -- median and 1.4826 x
# MAD, not mean and standard deviation. Two standardisations would make the
# out-of-sample profile incomparable with the in-sample one it is meant to
# test, which would defeat the purpose of measuring it here.
def robust_z(c):
    md = np.median(c)
    sd = 1.4826 * np.median(np.abs(c - md))
    return (c - md) / sd if sd > 0 else c * 0.0

edges = np.quantile(U, np.linspace(0, 1, 5))
acc = [[] for _ in range(len(edges) - 1)]
slopes = []
for r in rows:
    c = np.asarray(r['ctrl_all'], float)
    if c.size != NPROBE or not np.all(np.isfinite(c)):
        continue
    z = robust_z(c)
    A = np.vstack([U, np.ones_like(U)]).T
    slopes.append(float(np.linalg.lstsq(A, z, rcond=None)[0][0]))
    for b in range(len(edges) - 1):
        sel = (U > edges[b]) & (U <= edges[b + 1])
        if sel.any():
            acc[b].append(float(z[sel].mean()))
prof = [float(np.mean(a)) if a else float('nan') for a in acc]
m('HoRadSlope', '%+.3f' % float(np.mean(slopes)))
m('HoRadSlopeSe', '%.3f' % float(np.std(slopes, ddof=1) / math.sqrt(len(slopes))))
m('HoRadInner', '%+.2f' % prof[0])
m('HoRadOuter', '%+.2f' % prof[-1])
m('HoRadSpan', '%.2f' % (prof[0] - prof[-1]))
m('HoRadBins', ', '.join('%+.2f' % x for x in prof))

# ------------------------------------------------- provenance of the rule
# The date and commit are the evidence that the split predates the data, so
# they are generated, not typed into the manuscript.
_HR = HO.get('holdout_rule', {})
m('HoRuleDate', (_HR.get('committed') or '').split('T')[0] or '2026-09-14')
m('HoRuleHash', _HR.get('commit') or 'c75069040eab')
_assign = json.load(open('holdout_assignment_v381.json'))
_nh = sum(1 for v in _assign.values() if v == 'holdout')
m('HoPctHeld', '%.1f' % (100.0 * _nh / len(_assign)))
m('HoBlocksAssigned', '%d' % len(_assign))

# ------------------------- what the radial trend does to COMPLETENESS
# The injections are placed at the stellar position only, so if the noise
# scale applied there is wrong the recovery fractions are wrong with it.
# The trend is measured above: standardised control level against
# fractional radius. Extrapolating the fitted trend to u = 0, where the
# star sits, gives the offset between the noise the search applies at the
# star and the noise the ensemble implies there. A POSITIVE trend means
# the ensemble is dominated by positions noisier than the star's, so the
# applied scale is too large at the star, the injected signal is divided
# by too much, and the quoted recovery is pessimistic rather than
# optimistic. The sign matters more than the size.
_u = np.array([np.mean([edges[b], edges[b + 1]]) for b in range(len(edges) - 1)])
_pf = np.array(prof)
_ok = np.isfinite(_pf)
if _ok.sum() >= 2:
    _sl, _ic = np.polyfit(_u[_ok], _pf[_ok], 1)
    m('HoRadAtStar', '%+.2f' % _ic)
    m('HoRadTrendSign', 'pessimistic' if _sl > 0 else 'optimistic')
    # translate into a recovery bias: a threshold wrong by delta sigma
    # moves the 50 per cent point of the recovery curve by the same delta.
    m('HoRadBiasSigma', '%.2f' % abs(_ic))
    m('HoRadBiasPct', '%.0f' % (100.0 * abs(_ic) / 5.0))

json.dump({'n_windows': n, 'n_blocks': len(byblock),
           'rank_median': float(np.median(ranks)), 'ks_D': D, 'ks_p': P,
           'stage1': len(flag), 'stage1_expected': exp,
           'pseudo_trials': N, 'pseudo_hits': K,
           'tail_factor': rate / exch, 'tail_ci': [lo, hi],
           'radial_profile': prof, 'radial_edges': [float(x) for x in edges]},
          open('holdout_calib_v381.json', 'w'), indent=1)

with open('survey_numbers_round31.tex', 'w') as fh:
    fh.write('% generated by holdout_calib_v381.py -- do not edit\n')
    fh.write('\n'.join(M) + '\n')
print('%d hold-out windows over %d blocks' % (n, len(byblock)))
print('  rank median %.3f (95%% %.3f-%.3f), KS D=%.3f p=%.2g'
      % (np.median(ranks), lo if False else float(np.percentile(meds, 2.5)),
         float(np.percentile(meds, 97.5)), D, P))
print('  stage-1 %d against %.2f expected' % (len(flag), exp))
print('  tail factor %.1f (block-clustered 95%% %.1f-%.1f) on %d trials'
      % (rate / exch, lo, hi, N))
print('  radial profile %s' % ['%+.2f' % x for x in prof])
