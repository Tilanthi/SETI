#!/usr/bin/env python3
"""Referee: the search statistic uses one robust noise scale per window, global in
frequency.  Recompute a LOCAL robust scale around each flagged feature, excluding the
feature itself, and report both.  Uses the retained per-integration source spectra."""
import numpy as np, json, glob, os, sys
TARGETS = [('CP-72_2713_B7','A002_Xff0235_X4a6d',345.1152),
           ('HD_48370_B6','A002_Xc26103_X155a',230.7305),
           ('bet_Pic_B3','A002_Xf5d76d_X32f1',115.2605),
           ('bet_Pic_B6','A002_Xd9668b_X3a90',230.5164)]
out=[]
for tdir,eb,fc in TARGETS:
    base='/data/SETI/targets/%s/products'%tdir
    best=None
    for res in sorted(glob.glob(os.path.join(base,'%s_spw*_result.json'%eb))):
        r=json.load(open(res))
        lo,hi=sorted((r['freq_lo_GHz'],r['freq_hi_GHz']))
        if lo-0.05<=fc<=hi+0.05:
            if best is None or abs(r.get('star_peak_snr',0))>abs(best[1].get('star_peak_snr',0)):
                best=(res,r)
    if best is None:
        out.append(dict(target=tdir,error='no window covering %.4f GHz'%fc)); continue
    res,r=best
    spec=res.replace('_result.json','_srcspec.npz')
    if not os.path.exists(spec):
        out.append(dict(target=tdir,error='no srcspec')); continue
    z=np.load(spec,allow_pickle=True)
    I=np.asarray(z['I_star'],dtype=float)               # (n_int, n_chan)
    resid=I-np.median(I,axis=0,keepdims=True)           # per-channel time-median subtraction
    coadd=np.nanmean(resid,axis=0)                      # zero-drift coadd, the fiducial spectrum
    n=coadd.size
    pk=int(r.get('star_peak_chan',int(np.nanargmax(np.abs(coadd)))))
    pk=min(max(pk,0),n-1)
    mad=lambda x: 1.4826*np.nanmedian(np.abs(x-np.nanmedian(x)))
    g=mad(coadd)
    # local: a band around the peak, excluding +-3 channels of the feature itself
    half=max(12,n//8)
    lo,hi=max(0,pk-half),min(n,pk+half+1)
    idx=np.array([i for i in range(lo,hi) if abs(i-pk)>3])
    l=mad(coadd[idx]) if idx.size>8 else float('nan')
    out.append(dict(target=tdir, spw=os.path.basename(res), n_chan=n, peak_chan=pk,
                    star_peak_snr=r.get('star_peak_snr'),
                    sigma_global=float(g), sigma_local=float(l),
                    ratio=float(l/g) if g>0 else float('nan'),
                    T_global=float(abs(coadd[pk])/g) if g>0 else float('nan'),
                    T_local=float(abs(coadd[pk])/l) if l>0 else float('nan'),
                    n_local_chan=int(idx.size)))
print(json.dumps(out,indent=1))
