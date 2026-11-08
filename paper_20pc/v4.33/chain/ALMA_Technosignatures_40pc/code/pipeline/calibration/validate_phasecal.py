#!/usr/bin/env python3
"""
End-to-end validation of the ALMA-SETI chain using the phase calibrator.

J2301-0158 is a bright, essentially unresolved quasar sitting exactly at the
phase centre of its own scans.  Running the *identical* direct-Fourier-
transform estimator that the search uses must therefore return its known
Band-7 flux density.  This simultaneously validates

    (i)   that the restored ALMA pipeline calibration was applied correctly,
    (ii)  that the DFT / weighting normalisation of step2 is right (i.e. that
          a 1 Jy point source really reads back as 1 Jy), and
    (iii) that the measured per-channel r.m.s. is the true noise.

Usage: validate_phasecal.py <EBID>
"""
import os, sys, json
for _v in ('OMP_NUM_THREADS', 'OPENBLAS_NUM_THREADS', 'MKL_NUM_THREADS'):
    os.environ[_v] = '1'
import numpy as np

EB   = sys.argv[1]
ROOT = '/data/SETI'
MS   = f'{ROOT}/products/{EB}_trappist1_phasecal.ms'
OUT  = f'{ROOT}/products/{EB}_phasecal_validation.json'
os.environ.setdefault('CASASITECONFIG', '/home/fetch-agi/.casa/config.py')

from casatools import table

tb = table()
tb.open(MS + '/SPECTRAL_WINDOW')
freqs = tb.getcol('CHAN_FREQ')[:, 0].copy()
chanw = float(abs(tb.getcol('CHAN_WIDTH')[0, 0]))
tb.close()

tb.open(MS, nomodify=True)
nrow = tb.nrows()
times = tb.getcol('TIME')
has_ws = 'WEIGHT_SPECTRUM' in tb.colnames()
_a1all = tb.getcol('ANTENNA1'); _a2all = tb.getcol('ANTENNA2')
_autofrac = float((_a1all == _a2all).mean())
if _autofrac > 0:
    print(f'[{EB}] WARNING: {_autofrac*100:.2f}% autocorrelation rows in {MS}; excluding')

# process in row chunks; the calibrator is AT the phase centre so the
# estimator collapses to the weighted mean of Re(V) -- no phase term needed.
num = np.zeros(len(freqs), dtype=np.float64)
den = np.zeros(len(freqs), dtype=np.float64)
sq  = np.zeros(len(freqs), dtype=np.float64)
nvis = 0
CH = 20000
for i0 in range(0, nrow, CH):
    n = min(CH, nrow - i0)
    d = tb.getcol('DATA', i0, n)
    f = tb.getcol('FLAG', i0, n)
    if has_ws:
        w = tb.getcol('WEIGHT_SPECTRUM', i0, n)
    else:
        w = np.repeat(tb.getcol('WEIGHT', i0, n)[:, None, :], len(freqs), axis=1)
    a1c = tb.getcol('ANTENNA1', i0, n); a2c = tb.getcol('ANTENNA2', i0, n)
    auto = (a1c == a2c)
    w = np.where(f, 0.0, w)
    if auto.any():
        w[:, :, auto] = 0.0
    d = np.nan_to_num(d)
    num += (w * d.real).sum(axis=(0, 2))
    den += w.sum(axis=(0, 2))
    sq  += (w * d.real**2).sum(axis=(0, 2))
    nvis += int((w > 0).sum())
tb.close()

spec = num / den                       # Jy per channel, time+baseline averaged
sigma_vis = np.sqrt(np.maximum(sq / den - spec**2, 0))   # scatter per visibility
sigma_chan = 1.0 / np.sqrt(den)        # weight-predicted rms of the mean

flux = float(np.nanmedian(spec))
scatter = float(np.nanstd(spec))
res = dict(
    eb=EB, ms=MS, nrow=int(nrow), n_unflagged_vis=nvis,
    n_chan=len(freqs), chanwidth_Hz=chanw,
    freq_lo_GHz=float(freqs[0] / 1e9), freq_hi_GHz=float(freqs[-1] / 1e9),
    integration_time_s=float(np.ptp(times)),
    phasecal_flux_Jy=flux,
    phasecal_spectrum_scatter_Jy=scatter,
    predicted_rms_per_chan_Jy=float(np.nanmedian(sigma_chan)),
    per_visibility_scatter_Jy=float(np.nanmedian(sigma_vis)),
    weight_consistency=float(np.nanstd(spec) /
                             np.nanmedian(sigma_chan)),
)
print(json.dumps(res, indent=1))
print(f'\nJ2301-0158 recovered flux = {flux*1e3:.1f} mJy '
      f'(channel-to-channel scatter {scatter*1e3:.1f} mJy, '
      f'weight-predicted {np.nanmedian(sigma_chan)*1e3:.1f} mJy)')
print(f'weight consistency (measured scatter / predicted) = '
      f'{res["weight_consistency"]:.2f}   [1.0 = weights are correct]')
json.dump(res, open(OUT, 'w'), indent=1)
