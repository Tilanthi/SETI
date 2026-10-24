#!/usr/bin/env python3
"""D3 (referee D): star-versus-control residual variance for the four stage-1
windows, from the RETAINED products only.  Reads nothing else, writes nothing.

R_sigma = sigma_star,residual / median(sigma_controls,residual), where the
residual is the pipeline's own baseline-subtracted spectrum standardised by
the pipeline's own all-probe noise map sigma(t,nu), and sigma_x is a robust
(1.4826 x MAD) scale over the (integration, channel) plane with the crossing
region excluded.
"""
import os, sys, json
for _v in ('OMP_NUM_THREADS','OPENBLAS_NUM_THREADS','MKL_NUM_THREADS'):
    os.environ[_v] = '1'
sys.path.insert(0, '/data/SETI/work/localnull_v342')
import numpy as np
from validate_tstar import prepare, WINDOWS

def rstd(a):
    a = a[np.isfinite(a)]
    return float(1.4826 * np.median(np.abs(a - np.median(a))))

out = []
for tdir, stem, fghz, tpaper, ringpaper in WINDOWS:
    d = prepare(tdir, stem, verbose=False)
    I_star, I_ctrl, sigma = d['I_star'], d['I_ctrl'], d['sigma']
    nint, nch = I_star.shape
    z_star = np.nan_to_num(I_star / sigma)
    z_ctrl = np.nan_to_num(I_ctrl / sigma[:, None, :])
    # exclude the 64 channels around the window's own strongest on-star
    # channel (the feature) from every position alike
    prof = np.nanmean(np.abs(z_star), axis=0)
    c0 = int(np.nanargmax(prof))
    keep = np.ones(nch, bool); keep[max(0, c0-32):c0+33] = False
    s_star = rstd(z_star[:, keep])
    s_ctrl = [rstd(z_ctrl[:, q, keep]) for q in range(z_ctrl.shape[1])]
    # per-integration scales, to see whether the ratio is time-stable
    ps = np.array([rstd(z_star[t, keep]) for t in range(nint)])
    pc = np.array([[rstd(z_ctrl[t, q, keep]) for t in range(nint)]
                   for q in range(z_ctrl.shape[1])])
    r = s_star / float(np.median(s_ctrl))
    out.append(dict(window=tdir, stem=stem, nint=nint, nch=nch, nkeep=int(keep.sum()),
                    sigma_star=s_star, sigma_ctrl=s_ctrl,
                    sigma_ctrl_median=float(np.median(s_ctrl)),
                    sigma_ctrl_min=float(np.min(s_ctrl)), sigma_ctrl_max=float(np.max(s_ctrl)),
                    R_sigma=r,
                    R_sigma_vs_each=[s_star/x for x in s_ctrl],
                    n_ctrl_above_star=int(sum(1 for x in s_ctrl if x >= s_star)),
                    per_int_R_median=float(np.median(ps / np.median(pc, axis=0))),
                    per_int_R_lo=float(np.percentile(ps / np.median(pc, axis=0), 5)),
                    per_int_R_hi=float(np.percentile(ps / np.median(pc, axis=0), 95)),
                    T_star_paper=tpaper))
    print(json.dumps(out[-1]), flush=True)
print('===JSON===')
print(json.dumps(out))
