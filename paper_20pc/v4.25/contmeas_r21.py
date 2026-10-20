#!/usr/bin/env python3
r"""R2-10 stage A (runs on the campaign host): the continuum at the extraction
position, measured for EVERY window whose retained spectra survive.

Appendix B's vulnerability census -- the windows in which a channel-dependent
calibration residual could reach the trigger -- was computed only on the 28
windows of 6 stars for which a continuum IMAGE exists, plus AU Mic by hand.
The quantity it needs, however, is recorded in every window's own retained
spectra: `I_star` in `*_srcspec.npz` is the phase-rotated amplitude at the
stellar position, in apparent flux, per integration and per channel -- which
IS the dirty-map amplitude at that pixel, including whatever dust lies inside
the synthesised beam.  Averaged over time and frequency it is the continuum
the residual would multiply, measured by the survey's own extractor in the
window's own execution block.

So the census can be made COMPLETE rather than extended by hand, and the
route is validated where both exist: the six stars with continuum images.

Writes one row per product.  No selection, no cuts: every file found.
"""
import glob
import json
import os
import sys

import numpy as np

OUT = sys.argv[1] if len(sys.argv) > 1 else '/data/SETI/r21calib/contmeas_r21.json'
ROOT = '/data/SETI/targets'
CO21 = 230.538000e9          # the one bright line in the B6 windows of interest
CO32 = 345.795990e9
MASK_KMS = 50.0              # the survey's own mask half-width
C_KMS = 299792.458


def one(path):
    z = np.load(path, allow_pickle=True)
    if 'I_star' not in z.files:
        return None
    I = np.asarray(z['I_star'], dtype=np.float64)        # (n_int, n_chan) Jy
    W = np.asarray(z['W'], dtype=np.float64)
    f = np.asarray(z['freqs'], dtype=np.float64)
    if I.size == 0 or f.size == 0:
        return None
    good = np.isfinite(I) & np.isfinite(W) & (W > 0)
    if not good.any():
        return None
    Iw = np.where(good, I, 0.0)
    Ww = np.where(good, W, 0.0)
    # the weighted mean over time, channel by channel, then over channels:
    num = (Iw * Ww).sum(axis=0)
    den = Ww.sum(axis=0)
    spec = np.where(den > 0, num / np.maximum(den, 1e-30), np.nan)
    # a line mask, so a bright transition inside the window cannot be read as
    # continuum.  Both CO lines are tried; only one can fall in a window.
    msk = np.ones(f.size, dtype=bool)
    for f0 in (CO21, CO32):
        msk &= np.abs(f - f0) > (MASK_KMS / C_KMS) * f0
    # the per-channel scatter of the time-mean gives the error on the mean
    # continuum without assuming anything about the noise model.
    def stats(sel):
        v = spec[sel]
        v = v[np.isfinite(v)]
        if v.size < 8:
            return None
        return dict(n_chan=int(v.size), mean=float(v.mean()),
                    median=float(np.median(v)),
                    err=float(v.std(ddof=1) / np.sqrt(v.size)),
                    p10=float(np.percentile(v, 10)),
                    p90=float(np.percentile(v, 90)))
    allch = stats(np.ones(f.size, dtype=bool))
    masked = stats(msk)
    # the control ring, same reduction, as a check that the star is the source
    ring = None
    if 'I_control_sample' in z.files:
        Ic = np.asarray(z['I_control_sample'], dtype=np.float64)
        if Ic.ndim == 3 and Ic.shape[0] == I.shape[0]:
            cw = np.repeat(Ww[:, None, :], Ic.shape[1], axis=1)
            cg = np.isfinite(Ic) & (cw > 0)
            n2 = (np.where(cg, Ic, 0.0) * np.where(cg, cw, 0.0)).sum(axis=0)
            d2 = np.where(cg, cw, 0.0).sum(axis=0)
            cs = np.where(d2 > 0, n2 / np.maximum(d2, 1e-30), np.nan)
            cm = np.nanmedian(cs[:, msk], axis=1) if msk.any() else None
            if cm is not None and np.isfinite(cm).any():
                ring = dict(median_of_probes=float(np.nanmedian(cm)),
                            max_of_probes=float(np.nanmax(cm)),
                            n_probe=int(cm.size))
    return dict(file=os.path.relpath(path, ROOT),
                star=str(z['star_name']) if 'star_name' in z.files else None,
                n_int=int(I.shape[0]), n_chan=int(I.shape[1]),
                chanw_Hz=float(z['chanw']) if 'chanw' in z.files else None,
                flo_GHz=float(f.min()) / 1e9, fhi_GHz=float(f.max()) / 1e9,
                all_channels=allch, line_masked=masked, ring=ring)


def main():
    files = sorted(glob.glob(os.path.join(ROOT, '*', 'products',
                                          '*_srcspec.npz')))
    rows, bad = [], []
    for i, p in enumerate(files):
        try:
            r = one(p)
        except Exception as e:                      # noqa: BLE001
            bad.append([os.path.basename(p), repr(e)])
            continue
        if r is None:
            bad.append([os.path.basename(p), 'no usable I_star'])
            continue
        base = os.path.basename(p)
        stem = base[:-len('_srcspec.npz')]
        # ★ four products of the 3,051 carry no `_spwN` in the name at all;
        # they are kept with spw = None rather than dropped, and the join
        # downstream closes on (eb, frequency, channel width) in any case.
        if '_spw' in stem:
            r['eb'] = stem.rsplit('_spw', 1)[0]
            r['spw'] = int(stem.rsplit('_spw', 1)[1])
        else:
            r['eb'] = stem
            r['spw'] = None
        r['targetdir'] = p.split('/')[-3]
        rows.append(r)
        if i % 200 == 0:
            print('%d / %d' % (i, len(files)), flush=True)
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    json.dump(dict(n_file=len(files), n_row=len(rows), bad=bad, rows=rows),
              open(OUT, 'w'), indent=1)
    print('wrote %s: %d rows of %d files, %d unusable'
          % (OUT, len(rows), len(files), len(bad)))


if __name__ == '__main__':
    main()
