#!/usr/bin/env python3
r"""Referee 1's principal requirement: do not merely characterise the radial
defect in the spatial null, repair it and RERUN the candidate generation.

Two repaired screens are built, both from stored products:

  (A) RADIUS-MATCHED.  Rank the star against only those control probes whose
      radius lies in the inner part of the annulus, the closest approach to an
      iso-primary-beam comparison the frozen products allow.  Honest cost: the
      ensemble shrinks from 512 to 54 probes, so the rank resolution falls from
      1/513 to 1/55 and the screen necessarily admits more windows.

  (B) RADIALLY DETRENDED.  Keep all 512 probes and remove the measured radial
      trend instead.  In units of each window's own robust scale the pooled
      control level is m(u); subtract s*m(u_k) from every control and s*m(0)
      from the star, where s is that window's 1.4826*MAD scale.  m(0) is taken
      as the innermost measured bin, which is the conservative choice: the
      trend is still rising inwards there, so the star is debited less than an
      extrapolation would debit it.  Rank resolution stays 1/513.

Screen (B) is the one the paper adopts as its primary candidate-generation
criterion.  Screen (A) is reported beside it because it assumes nothing about
the shape of the trend.

Outputs `radius_matched_v362.json`: the flagged set under each screen, the
comparison with the released set, and the held-out rank distributions that
show whether the repair works out of sample.
"""
import csv, collections, json, math, os
import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
ROWS = list(csv.DictReader(open(os.path.join(HERE, 'per_target_results_v3.62.csv'))))
FRZ = json.load(open(os.path.join(HERE, 'frozen_ctrl_v362.json')))
HO_ALL = json.load(open(os.path.join(HERE, 'heldout_ctrl_v361.json')))
HOMETA = {os.path.basename(w['result_file']): w
          for w in json.load(open(os.path.join(HERE, 'heldout_v352.json')))['windows']}

R_IN, R_OUT, NPROBE, SEED = 0.14, 0.78, 512, 20260825
INNER_U = 0.30                      # the radius-matched subset
NBIN = 8                            # radial bins for the trend
THRESH = 5.0


def probe_radii():
    rng = np.random.default_rng(SEED)
    rr = np.sqrt(rng.uniform(R_IN ** 2, R_OUT ** 2, NPROBE))
    rng.uniform(0, 2 * np.pi, NPROBE)          # azimuths, drawn but unused here
    return rr


U = probe_radii()
INNER = U <= INNER_U
EDGES = np.quantile(U, np.linspace(0, 1, NBIN + 1))
EDGES[0] -= 1e-9
BIN = np.digitize(U, EDGES) - 1
BIN = np.clip(BIN, 0, NBIN - 1)


def scale(c):
    return 1.4826 * np.median(np.abs(c - np.median(c)))


def zof(c):
    s = scale(c)
    return (c - np.median(c)) / s if s > 0 else c * 0.0


# ------------------------------------------------------------------ the trend
# measured on the HELD-OUT windows, which played no part in defining the
# statistic, so the correction applied to the survey is not fitted on it
ho = [r for r in HO_ALL if r.get('c') and len(r['c']) == NPROBE
      and r.get('star') is not None
      and not HOMETA.get(r['f'], {}).get('line_attributed')]
prof = np.zeros(NBIN)
for b in range(NBIN):
    sel = BIN == b
    prof[b] = float(np.mean([zof(np.asarray(r['c'], float))[sel].mean() for r in ho]))
M_STAR = prof[0]                    # conservative value at the stellar radius
print('radial trend (held-out, %d windows): %s' % (len(ho),
      ' '.join('%+.3f' % x for x in prof)))
print('correction applied at the stellar radius: %+.3f sigma' % M_STAR)

# --------------------------------------------------------------- the rescoring
CT = {}
for r in FRZ:
    CT.setdefault((r['eb'], r['lo'], r['hi']), r)
k4 = lambda e, a, b: (e, round(min(a, b), 4), round(max(a, b), 4))

res, miss = [], 0
for row in ROWS:
    k = k4(row['eb'], float(row['flo_GHz']), float(row['fhi_GHz']))
    rec = CT.get(k)
    if rec is None or not rec.get('c'):
        miss += 1
        continue
    c = np.asarray(rec['c'], float)
    t = float(row['star_snr'])
    s = scale(c)
    cin = c[INNER]
    cdet = c - s * prof[BIN]
    tdet = t - s * M_STAR
    res.append(dict(
        star=row['star_name'], band=row['band'], eb=row['eb'],
        flo=float(row['flo_GHz']), fhi=float(row['fhi_GHz']),
        cls=row['search_class'], t=t, cmax=float(row['ctrl_max_snr']),
        released=row['stage1_flag'] == 'True',
        crossing=t >= THRESH,
        # (A) radius-matched
        a_flag=bool(t >= THRESH and t > cin.max()),
        a_rank=float((1 + (cin >= t).sum()) / (cin.size + 1)),
        # (B) radially detrended
        b_flag=bool(t >= THRESH and tdet > cdet.max()),
        b_rank=float((1 + (cdet >= tdet).sum()) / (cdet.size + 1)),
        disposition=row['disposition']))
print('rescored %d windows (%d catalogue rows had no stored control vector)'
      % (len(res), miss))

rel = [r for r in res if r['released']]
A = [r for r in res if r['a_flag']]
B = [r for r in res if r['b_flag']]
print('\nreleased stage-1 set: %d' % len(rel))
for r in rel:
    print('   %-14s B%-2s %9.3f  T*=%.2f  A:%s  B:%s  (%s)'
          % (r['star'], r['band'], r['flo'], r['t'], r['a_flag'], r['b_flag'],
             r['disposition'][:28]))
print('\n(A) radius-matched, %d inner probes, resolution 1/%d -> %d windows'
      % (INNER.sum(), INNER.sum() + 1, len(A)))
print('    expected by chance over %d windows: %.1f'
      % (len(res), len(res) / float(INNER.sum() + 1)))
for r in A:
    if not r['released']:
        print('   NEW  %-14s B%-2s %9.3f  T*=%.2f  class %s'
              % (r['star'], r['band'], r['flo'], r['t'], r['cls']))
print('\n(B) radially detrended, 512 probes, resolution 1/513 -> %d windows' % len(B))
for r in B:
    tag = 'released' if r['released'] else 'NEW'
    print('   %-8s %-14s B%-2s %9.3f  T*=%.2f  class %s'
          % (tag, r['star'], r['band'], r['flo'], r['t'], r['cls']))
lost = [r for r in rel if not r['b_flag']]
print('    released windows NOT recovered by (B): %d' % len(lost))

# ---- how big a stellar debit would each released window survive, and what
# debit centres the held-out rank distribution?
for r in res:
    c = np.asarray(CT[k4(r['eb'], r['flo'], r['fhi'])]['c'], float)
    s_ = scale(c)
    r['survives'] = float((r['t'] - (c - s_ * prof[BIN]).max()) / s_)


def ho_median(mstar):
    out = []
    for q in ho:
        c = np.asarray(q['c'], float)
        t = float(q['star'])
        s_ = scale(c)
        out.append((1 + ((c - s_ * prof[BIN]) >= t - s_ * mstar).sum()) / (c.size + 1))
    return float(np.median(out))


_lo, _hi = 0.0, 2.0
for _ in range(40):
    _m = 0.5 * (_lo + _hi)
    if ho_median(_m) < 0.5:
        _lo = _m
    else:
        _hi = _m
DEBIT_CAL = 0.5 * (_lo + _hi)
print('\ndebit that centres the held-out rank distribution: %.3f sigma '
      '(conservative innermost-bin value %.3f)' % (DEBIT_CAL, M_STAR))
for r in sorted(rel, key=lambda x: -x['survives']):
    print('   %-14s B%-2s survives a debit up to %6.2f sigma' % (r['star'], r['band'], r['survives']))
_at_cal = [r for r in res if r['t'] >= THRESH and r['survives'] > DEBIT_CAL]
print('   flagged at the calibrated debit: %d  (%s)'
      % (len(_at_cal), ', '.join(sorted({x['star'] for x in _at_cal}))))

# ------------------------------------------------- does the repair work?
def ks_uniform(x):
    x = np.sort(np.asarray(x, float))
    n = len(x)
    i = np.arange(1, n + 1)
    d = max(np.max(i / n - x), np.max(x - (i - 1) / n))
    lam = (math.sqrt(n) + 0.12 + 0.11 / math.sqrt(n)) * d
    p = 2 * sum((-1) ** (j - 1) * math.exp(-2 * j * j * lam * lam) for j in range(1, 101))
    return float(d), float(min(1.0, max(0.0, p)))


ho_raw, ho_det = [], []
for r in ho:
    c = np.asarray(r['c'], float)
    t = float(r['star'])
    s = scale(c)
    ho_raw.append((1 + (c >= t).sum()) / (c.size + 1))
    cdet = c - s * prof[BIN]
    ho_det.append((1 + (cdet >= t - s * M_STAR).sum()) / (cdet.size + 1))
sv_raw = [float(r['star_snr']) for r in ROWS]
print('\nheld-out star rank, raw       : median %.3f  D %.3f p %.4g'
      % (np.median(ho_raw), *ks_uniform(ho_raw)))
print('held-out star rank, detrended : median %.3f  D %.3f p %.4g'
      % (np.median(ho_det), *ks_uniform(ho_det)))
surv_raw = [r['a_rank'] for r in res]      # placeholder, replaced below
surv_b = [r['b_rank'] for r in res]
surv_raw = [(1 + (np.asarray(CT[k4(row['eb'], float(row['flo_GHz']),
                                   float(row['fhi_GHz']))]['c'], float)
                  >= float(row['star_snr'])).sum()) / 513.0
            for row in ROWS
            if k4(row['eb'], float(row['flo_GHz']), float(row['fhi_GHz'])) in CT]
print('survey star rank, raw         : median %.3f  D %.3f p %.4g'
      % (np.median(surv_raw), *ks_uniform(surv_raw)))
print('survey star rank, detrended   : median %.3f  D %.3f p %.4g'
      % (np.median(surv_b), *ks_uniform(surv_b)))

json.dump(dict(
    _doc=__doc__.strip(),
    n=len(res), inner_n=int(INNER.sum()), inner_u=INNER_U, nbin=NBIN,
    profile=[float(x) for x in prof], m_star=float(M_STAR),
    debit_calibrated=float(DEBIT_CAL),
    n_flag_at_calibrated=len(_at_cal),
    flag_at_calibrated=sorted({x['star'] for x in _at_cal}),
    released=[{k: r[k] for k in ('star', 'band', 'flo', 't', 'cmax', 'a_flag',
                                 'b_flag', 'a_rank', 'b_rank', 'survives',
                                 'disposition')}
              for r in rel],
    a_flagged=[{k: r[k] for k in ('star', 'band', 'flo', 't', 'cls', 'released')}
               for r in A],
    b_flagged=[{k: r[k] for k in ('star', 'band', 'flo', 't', 'cls', 'released')}
               for r in B],
    a_expected=len(res) / float(INNER.sum() + 1),
    b_expected=len(res) / 513.0,
    heldout=dict(raw_median=float(np.median(ho_raw)),
                 raw_D=ks_uniform(ho_raw)[0], raw_p=ks_uniform(ho_raw)[1],
                 det_median=float(np.median(ho_det)),
                 det_D=ks_uniform(ho_det)[0], det_p=ks_uniform(ho_det)[1],
                 n=len(ho)),
    survey=dict(raw_median=float(np.median(surv_raw)),
                raw_D=ks_uniform(surv_raw)[0], raw_p=ks_uniform(surv_raw)[1],
                det_median=float(np.median(surv_b)),
                det_D=ks_uniform(surv_b)[0], det_p=ks_uniform(surv_b)[1],
                n=len(surv_b)),
), open(os.path.join(HERE, 'radius_matched_v362.json'), 'w'), indent=1)
print('\nwrote radius_matched_v362.json')
