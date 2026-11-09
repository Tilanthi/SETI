#!/usr/bin/env python3
"""Sanity check: does the re-implemented statistic reproduce the pipeline's own
recorded star_peak_snr on UNINJECTED windows?  If it does not, the injection
result cannot be trusted."""
import numpy as np, json, glob, os, ast, random
SRC=open('/data/SETI/bin/seti_drift_search_generic.py').read()
ns={'np':np}
for node in ast.parse(SRC).body:
    if isinstance(node,ast.FunctionDef) and node.name=='spectral_baseline':
        exec(compile(ast.Module([node],[]),'<p>','exec'),ns)
    elif isinstance(node,ast.Assign) and getattr(node.targets[0],'id','')=='MEDWIN':
        exec(compile(ast.Module([node],[]),'<p>','exec'),ns)
sb,MEDWIN=ns['spectral_baseline'],ns['MEDWIN']
def stat(I,C):
    med=np.nanmedian(C,axis=1); mad=np.nanmedian(np.abs(C-med[:,None,:]),axis=1)
    sigma=1.4826*mad
    resid=I-sb(np.nan_to_num(I)[None,:,:],MEDWIN)[0]
    w=1.0/np.nanmean(sigma,axis=1)**2
    st=np.nansum(resid*w[:,None],axis=0)/np.nansum(w)
    nz=1.4826*np.nanmedian(np.abs(st-np.nanmedian(st)))
    return float(np.nanmax((st-np.nanmedian(st))/nz))
cands=[]
for res in glob.glob('/data/SETI/targets/*/products/*_result.json'):
    sp=res.replace('_result.json','_srcspec.npz')
    if not os.path.exists(sp): continue
    try: r=json.load(open(res))
    except Exception: continue
    if r.get('star_peak_snr') is None: continue
    cands.append((res,r,sp))
random.Random(3).shuffle(cands)
print('%-46s %8s %8s %7s'%('window','pipeline','mine(0-drift)','ratio'))
rat=[]
for res,r,sp in cands[:12]:
    try:
        z=np.load(sp,allow_pickle=True)
        I=np.asarray(z['I_star'],float); C=np.asarray(z['I_control_sample'],float)
        if I.shape[0]<20: continue
        m=stat(I,C); p=r['star_peak_snr']
        rat.append(m/p)
        print('%-46s %8.2f %8.2f %7.2f'%(os.path.basename(res)[:44],p,m,m/p))
    except Exception as e: print('skip',e)
import statistics as st
if rat: print('\nmedian ratio mine/pipeline = %.2f  (n=%d)'%(st.median(rat),len(rat)))
print('NOTE: mine is zero-drift only; the pipeline maximises over the drift grid,')
print('so mine should be <= pipeline, and close on coarse windows where the grid degenerates.')
