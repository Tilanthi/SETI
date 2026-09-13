#!/usr/bin/env python3
r"""Referee 1 major point 2, and the diagnosis behind referee 1 point 1 and
referee 2 point M2: is the stellar/control rank displacement a PROPERTY OF THE
STELLAR POSITION, or a property of RADIUS from the pointing centre?

The control probes are not random from run to run.  `probe_positions()` in
`/data/SETI/bin/seti_extract_generic.py` draws them from
`numpy.random.default_rng(20260825)`, the same seed for every window, as

    r_k = sqrt(U(r_in^2, r_out^2)),   theta_k = U(0, 2 pi),
    r_in = 0.14 theta_PB,  r_out = 0.78 theta_PB,

so the FRACTIONAL radii u_k = r_k / theta_PB are identical in every window of
the survey and are reproduced exactly here.  Each window's stored control
vector `ctrl_all` is in probe order, so every control statistic can be paired
with the radius at which it was measured without re-running anything.

Three tests, all from the released products:

  (1) RADIAL TREND.  Regress the standardised control statistic on u.  If the
      stellar excess is a radial effect -- primary-beam response, deconvolution
      residual of the field's own bright target, position-dependent
      calibration error -- the controls must already show it, because they span
      0.14-0.78 theta_PB while the star sits at ~0.

  (2) MATCHED-RADIUS RANK.  Rank the star against the INNERMOST controls only,
      the closest approach to referee 1's iso-primary-beam annulus that stored
      products allow, and compare with its rank against all 512.

  (3) PSEUDO-STARS.  Treat each of the innermost probes as a pseudo-star and
      rank it against the other 511.  These positions carry no star, so any
      departure from uniformity is instrumental by construction.

Writes `radial_null_v361.json`.  Reads only this folder.
"""
import csv, json, math, os
import numpy as np
from statistics import NormalDist

HERE = os.path.dirname(os.path.abspath(__file__))
ROWS = list(csv.DictReader(open(os.path.join(HERE, 'per_target_results_v3.62.csv'))))
EXP = json.load(open(os.path.join(HERE, 'frozen_export_v3.60.json')))['rows']

R_IN, R_OUT, NPROBE, SEED = 0.14, 0.78, 512, 20260825


def probe_radii():
    """Fractional radii u_k = r_k/theta_PB, in probe order, exactly as the
    pipeline draws them (the seed is fixed, so this is every window's ring)."""
    rng = np.random.default_rng(SEED)
    rr = np.sqrt(rng.uniform(R_IN ** 2, R_OUT ** 2, NPROBE))
    th = rng.uniform(0, 2 * np.pi, NPROBE)          # drawn, not used here
    return rr, th


U, TH = probe_radii()
assert abs(U.min() - R_IN) < 0.02 and abs(U.max() - R_OUT) < 0.01, (U.min(), U.max())

# pair each export row with its catalogue row (same key the catalogue uses)
key = lambda s, e, lo, hi: (s, e, round(min(lo, hi), 6), round(max(lo, hi), 6))
CAT = {key(r['star_name'], r['eb'], float(r['flo_GHz']), float(r['fhi_GHz'])): r
       for r in ROWS}

W = []
for r in EXP:
    k = key(r['star_name'], r['eb'], r['flo'], r['fhi'])
    if k not in CAT or not r.get('ctrl_all') or len(r['ctrl_all']) != NPROBE:
        continue
    c = np.asarray(r['ctrl_all'], float)
    if not np.all(np.isfinite(c)):
        continue
    W.append((CAT[k], r, c))
print('windows with a full 512-probe vector: %d of %d' % (len(W), len(ROWS)))


def robust_z(c):
    m = np.median(c)
    s = 1.4826 * np.median(np.abs(c - m))
    return (c - m) / s if s > 0 else c * 0.0


# ---------------------------------------------------------------- (1) trend
slopes, rs = [], []
zpool, upool = [], []
for cat, r, c in W:
    z = robust_z(c)
    zpool.append(z)
    upool.append(U)
    A = np.vstack([U, np.ones_like(U)]).T
    b = np.linalg.lstsq(A, z, rcond=None)[0]
    slopes.append(b[0])
    rs.append(np.corrcoef(U, z)[0, 1])
zpool = np.concatenate(zpool)
upool = np.concatenate(upool)
A = np.vstack([upool, np.ones_like(upool)]).T
gb, ga = np.linalg.lstsq(A, zpool, rcond=None)[0]
# standard error of the pooled slope, with windows as the independent unit
sl = np.array(slopes)
se = sl.std(ddof=1) / math.sqrt(len(sl))
print('pooled slope %.4f sigma per theta_PB; per-window mean %.4f +- %.4f (t=%.2f)'
      % (gb, sl.mean(), se, sl.mean() / se))

# what that trend predicts AT the stellar radius, extrapolated to u = 0
pred_star = ga + gb * 0.0
pred_mid = ga + gb * np.median(U)
print('extrapolated control level at u=0: %+.4f sigma; at the median probe '
      'radius %+.4f sigma; difference %+.4f' % (pred_star, pred_mid, pred_star - pred_mid))

# ---------------------------------------------- (2) matched-radius sub-rank
INNER = U <= 0.30            # the innermost quartile-ish of the annulus
print('inner subset: %d probes, u in %.3f-%.3f' % (INNER.sum(), U[INNER].min(), U[INNER].max()))


def addone(star, ctrl):
    return (1.0 + np.sum(np.asarray(ctrl) >= star)) / (1.0 + len(ctrl))


rank_all, rank_in = [], []
for cat, r, c in W:
    s = float(cat['star_snr'])
    rank_all.append(addone(s, c))
    rank_in.append(addone(s, c[INNER]))
rank_all = np.array(rank_all)
rank_in = np.array(rank_in)


def ks_uniform(x):
    x = np.sort(np.asarray(x, float))
    n = len(x)
    i = np.arange(1, n + 1)
    d = max(np.max(i / n - x), np.max(x - (i - 1) / n))
    # asymptotic two-sided KS p-value
    lam = (math.sqrt(n) + 0.12 + 0.11 / math.sqrt(n)) * d
    p = 2 * sum((-1) ** (j - 1) * math.exp(-2 * j * j * lam * lam)
                for j in range(1, 101))
    return d, min(1.0, max(0.0, p))


for name, x in (('all 512', rank_all), ('inner subset', rank_in)):
    d, p = ks_uniform(x)
    print('star rank vs %-13s median %.3f  frac<0.1 %.3f  frac>0.9 %.3f  '
          'D %.3f p %.3g' % (name, np.median(x), np.mean(x < 0.1),
                             np.mean(x > 0.9), d, p))

# ------------------------------------------------------------ (3) pseudo-stars
NPS = 16                                  # the 16 innermost probes
order = np.argsort(U)[:NPS]
ps_rank = []
for cat, r, c in W:
    for q in order:
        others = np.delete(c, q)
        ps_rank.append(addone(c[q], others))
ps_rank = np.array(ps_rank)
d_ps, p_ps = ks_uniform(ps_rank)
print('pseudo-stars (%d innermost probes, u %.3f-%.3f): n %d median %.3f '
      'frac<0.1 %.3f D %.3f p %.3g'
      % (NPS, U[order].min(), U[order].max(), len(ps_rank), np.median(ps_rank),
         np.mean(ps_rank < 0.1), d_ps, p_ps))
# one pseudo-star per window, so the window is the independent unit
ps_one = ps_rank.reshape(len(W), NPS)[:, 0]
d1, p1 = ks_uniform(ps_one)
print('  one pseudo-star per window: median %.3f D %.3f p %.3g'
      % (np.median(ps_one), d1, p1))

# how often does a pseudo-star beat all 511 others (the stage-1 analogue)?
ps_first = float(np.mean(ps_rank <= 1.0 / 512.0))
print('  pseudo-star ranks first in %.4f of trials (exchangeable 1/512 = %.4f)'
      % (ps_first, 1.0 / 512))

# =====================================================================
# The same three tests on the HELD-OUT sample, which played no part in
# defining the statistic.  `heldout_ctrl_v361.json` is the control vector of
# every held-out window, read from the pipeline's own stored `*_search.npz`
# on the host (read-only; only the derived numbers were transferred).
# =====================================================================
HO_ALL = json.load(open(os.path.join(HERE, 'heldout_ctrl_v361.json')))
HOMETA = {os.path.basename(w['result_file']): w
          for w in json.load(open(os.path.join(HERE, 'heldout_v352.json')))['windows']}
HO = [r for r in HO_ALL
      if r.get('c') and len(r['c']) == NPROBE and r.get('star') is not None
      and not HOMETA.get(r['f'], {}).get('line_attributed')]
print('\nheld-out null windows with a full probe vector: %d of %d'
      % (len(HO), len(HO_ALL)))

offs = [r['pboff'] / r['pbfwhm'] for r in HO_ALL
        if r.get('pboff') is not None and r.get('pbfwhm')]
print('star offset from the phase centre: median %.4f theta_PB, max %.4f; '
      'the annulus starts at %.2f, so the star is never inside it'
      % (np.median(offs), max(offs), R_IN))

ho_slopes, ho_all, ho_in, ho_ps = [], [], [], []
for r in HO:
    c = np.asarray(r['c'], float)
    if not np.all(np.isfinite(c)):
        continue
    z = robust_z(c)
    A = np.vstack([U, np.ones_like(U)]).T
    ho_slopes.append(np.linalg.lstsq(A, z, rcond=None)[0][0])
    s = float(r['star'])
    ho_all.append(addone(s, c))
    ho_in.append(addone(s, c[INNER]))
    for q in order:
        ho_ps.append(addone(c[q], np.delete(c, q)))
ho_all = np.array(ho_all); ho_in = np.array(ho_in); ho_ps = np.array(ho_ps)
ho_ps_one = ho_ps.reshape(-1, NPS)[:, 0]
d_h1, p_h1 = ks_uniform(ho_ps_one)
print('held-out one pseudo-star per window: median %.3f D %.3f p %.3g'
      % (np.median(ho_ps_one), d_h1, p_h1))


def radial_profile(vectors, nbin=8):
    """Mean standardised control level in radial bins, pooled over windows."""
    edges = np.quantile(U, np.linspace(0, 1, nbin + 1))
    edges[0] -= 1e-9
    idx = [np.where((U > edges[i]) & (U <= edges[i + 1]))[0] for i in range(nbin)]
    prof, uc = [], []
    for i in range(nbin):
        vals = [robust_z(v)[idx[i]].mean() for v in vectors]
        prof.append(float(np.mean(vals)))
        prof_se = float(np.std(vals, ddof=1) / math.sqrt(len(vals)))
        uc.append(float(U[idx[i]].mean()))
        print('   u %.3f  n_probe %3d  mean z %+.4f +- %.4f'
              % (uc[-1], len(idx[i]), prof[-1], prof_se))
    return uc, prof


# ---- the natural experiment: windows in which the star is ITSELF inside the
# annulus.  `pboffsets_v361.json` carries u_star = offset/theta_PB for every
# searched window, read from the pipeline's own result records.
POFF = {(e, round(min(a, b), 4), round(max(a, b), 4)): o
        for e, a, b, o in json.load(open(os.path.join(HERE, 'pboffsets_v361.json')))}
ustar, urank = [], []
for cat, r, c in W:
    k = (cat['eb'], round(min(r['flo'], r['fhi']), 4), round(max(r['flo'], r['fhi']), 4))
    if k in POFF:
        ustar.append(POFF[k])
        urank.append(addone(float(cat['star_snr']), np.asarray(c, float)))
ustar = np.array(ustar); urank = np.array(urank)
inside = ustar >= R_IN
print('')
print('stars inside the control annulus (u_star >= %.2f): %d of %d'
      % (R_IN, inside.sum(), len(ustar)))
INSIDE_STATS = {}
for name, sel in (('outside', ~inside), ('inside', inside)):
    x = urank[sel]
    d, p = ks_uniform(x)
    INSIDE_STATS[name] = dict(n=int(len(x)), median=float(np.median(x)),
                              lo=float(np.mean(x < 0.1)), D=float(d), p=float(p))
    print('  u_star %-8s n %3d median %.3f frac<0.1 %.3f D %.3f p %.3g'
          % (name, len(x), np.median(x), np.mean(x < 0.1), d, p))
INSIDE_STATS['u_median'] = float(np.median(ustar))
INSIDE_STATS['u_p90'] = float(np.percentile(ustar, 90))
INSIDE_STATS['u_max'] = float(ustar.max())

print(' frozen radial profile:')
uc_f, pf_f = radial_profile([np.asarray(c, float) for _, _, c in W])
print(' held-out radial profile:')
uc_h, pf_h = radial_profile([np.asarray(r['c'], float) for r in HO])
hsl = np.array(ho_slopes)
hse = hsl.std(ddof=1) / math.sqrt(len(hsl))
print('held-out pooled slope %.4f +- %.4f sigma per theta_PB (t=%.2f)'
      % (hsl.mean(), hse, hsl.mean() / hse))
for name, x in (('all 512', ho_all), ('inner subset', ho_in),
                ('pseudo-stars', ho_ps)):
    d, p = ks_uniform(x)
    print('held-out rank vs %-13s median %.3f  frac<0.1 %.3f  D %.3f p %.3g'
          % (name, np.median(x), np.mean(x < 0.1), d, p))
ho_first = float(np.mean(ho_ps <= 1.0 / 512.0))
print('held-out pseudo-star ranks first in %.4f (exchangeable %.4f)'
      % (ho_first, 1.0 / 512))

out = dict(
    _doc=__doc__.strip(),
    heldout=dict(
        n=len(ho_all), n_all=len(HO_ALL),
        off_median=float(np.median(offs)), off_max=float(max(offs)),
        slope=float(hsl.mean()), slope_se=float(hse),
        slope_t=float(hsl.mean() / hse),
        rank_all=dict(median=float(np.median(ho_all)),
                      lo=float(np.mean(ho_all < 0.1)),
                      hi=float(np.mean(ho_all > 0.9)),
                      D=ks_uniform(ho_all)[0], p=ks_uniform(ho_all)[1]),
        rank_inner=dict(median=float(np.median(ho_in)),
                        lo=float(np.mean(ho_in < 0.1)),
                        D=ks_uniform(ho_in)[0], p=ks_uniform(ho_in)[1]),
        pseudo=dict(n=len(ho_ps), median=float(np.median(ho_ps)),
                    lo=float(np.mean(ho_ps < 0.1)),
                    D=ks_uniform(ho_ps)[0], p=ks_uniform(ho_ps)[1],
                    first_frac=ho_first,
                    median_one=float(np.median(ho_ps_one)),
                    D_one=float(d_h1), p_one=float(p_h1)),
        profile=dict(u=uc_h, z=pf_h)),
    profile=dict(u=uc_f, z=pf_f),
    arrays=dict(star_frozen=[round(float(x), 5) for x in rank_all],
                star_heldout=[round(float(x), 5) for x in ho_all],
                pseudo_heldout=[round(float(x), 5) for x in ho_ps_one],
                pseudo_frozen=[round(float(x), 5) for x in ps_one],
                star_inner_frozen=[round(float(x), 5) for x in rank_in],
                star_inner_heldout=[round(float(x), 5) for x in ho_in]),
    ustar=INSIDE_STATS,
    n_windows=len(W), seed=SEED, r_in=R_IN, r_out=R_OUT, n_probe=NPROBE,
    u_min=float(U.min()), u_max=float(U.max()), u_median=float(np.median(U)),
    slope_pooled=float(gb), slope_mean=float(sl.mean()), slope_se=float(se),
    slope_t=float(sl.mean() / se), intercept=float(ga),
    pred_at_star=float(pred_star), pred_at_median=float(pred_mid),
    r_pearson_median=float(np.median(rs)),
    inner_n=int(INNER.sum()), inner_u_max=float(U[INNER].max()),
    rank_all=dict(median=float(np.median(rank_all)),
                  lo=float(np.mean(rank_all < 0.1)),
                  hi=float(np.mean(rank_all > 0.9)),
                  D=ks_uniform(rank_all)[0], p=ks_uniform(rank_all)[1]),
    rank_inner=dict(median=float(np.median(rank_in)),
                    lo=float(np.mean(rank_in < 0.1)),
                    hi=float(np.mean(rank_in > 0.9)),
                    D=ks_uniform(rank_in)[0], p=ks_uniform(rank_in)[1]),
    pseudo=dict(n=len(ps_rank), n_probes=NPS,
                u_lo=float(U[order].min()), u_hi=float(U[order].max()),
                median=float(np.median(ps_rank)),
                lo=float(np.mean(ps_rank < 0.1)),
                D=float(d_ps), p=float(p_ps),
                median_one=float(np.median(ps_one)), D_one=float(d1),
                p_one=float(p1), first_frac=ps_first))
json.dump(out, open(os.path.join(HERE, 'radial_null_v361.json'), 'w'), indent=1)
print('wrote radial_null_v361.json')
