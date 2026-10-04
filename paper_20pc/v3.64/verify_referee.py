#!/usr/bin/env python3
"""Independent verification of referee numerical claims against the frozen export."""
import json, math, statistics as st, collections
C=299792.458
d=json.load(open('frozen_export_v3.31.json')); rows=d['rows']
def band_of(r):
    if r['band'] is not None: return r['band']
    f=0.5*(r['flo']+r['fhi'])
    for lo,hi,b in [(84,116,3),(125,163,4),(163,211,5),(211,275,6),(275,373,7),(385,500,8)]:
        if lo<=f<hi: return b
for r in rows:
    r['band_x']=band_of(r); r['res_x']='fine' if r['chanw']<5e6 else 'coarse'
    r['qa']=r['rms']*math.sqrt(r['onsrc']*r['chanw'])
    r['ctrl_max_all']=max(r['ctrl_all']) if r['ctrl_all'] else r['ctrl_max']
key=lambda r:(r['star_name'],r['eb'],round(min(r['flo'],r['fhi']),6),round(max(r['flo'],r['fhi']),6),r['chanw'])
best={}
for r in rows:
    k=key(r)
    if k not in best or (best[k]['line'] is None and r['line'] is not None): best[k]=r
uniq=list(best.values())
qa_med=st.median(r['qa'] for r in uniq)
kept=[r for r in uniq if r['qa']>=qa_med/100.0]
withheld=[r for r in kept if r['star_name']=='eps Eri' and r['band_x']==6]
good=[r for r in kept if r not in withheld]
print('N windows (good):',len(good))
print()
print('=== R1-M8 / A3: gross bandwidth ===')
gross=sum(abs(r['fhi']-r['flo']) for r in good)
print('  gross_bw_GHz =',round(gross,4),' printed in paper: 700.8 ; referee says 716.65')
print()
print('=== R1-M8: Gaussian-expected chance crossings ===')
cells=sum(int(abs(r['fhi']-r['flo'])*1e9/r['chanw'])*r['ndrift'] for r in good)
from math import erfc,sqrt
p5=0.5*erfc(5/sqrt(2))
print('  trial cells =',f'{cells:.3e}','  one-sided p(5sig) =',f'{p5:.3e}','  product =',round(cells*p5,2))
print('  two-sided p =',f'{2*p5:.3e}','  product =',round(cells*2*p5,2))
print()
print('=== R1-M8: Poisson P(>=4|0.84) ===')
mu=0.84
import math as m
pk=[m.exp(-mu)*mu**k/m.factorial(k) for k in range(6)]
print('  P(exactly 4)=',round(pk[4]*100,3),'%   P(>=4)=',round((1-sum(pk[:4]))*100,3),'%')
print()
print('=== R1-M8 / A2: non-beta-Pic windows and expectation ===')
nbp=[r for r in good if 'bet Pic' not in r['star_name'] and 'beta Pic' not in r['star_name']]
bp=[r for r in good if r not in nbp]
print('  bet-Pic-like star names:',sorted({r['star_name'] for r in bp}))
print('  N non-bPic windows =',len(nbp),' (paper macro NNonBP=416; text says 402)')
for n in (402,416,len(nbp)):
    e=n/513.0
    print(f'   n={n}: expected={e:.3f}  P(>=1)={1-m.exp(-e):.4f}')
print()
print('=== R2-M1: peak flux densities (star_snr * rms) ===')

flag=[r for r in good if r['star_snr']>=5.0 and r['star_snr']>r['ctrl_max_all']]
for r in flag:
    print(f"  {r['star_name']:40s} B{r['band_x']} f={0.5*(r['flo']+r['fhi']):.5f} GHz chanw={r['chanw']/1e3:.1f} kHz "
          f"star_snr={r['star_snr']:.2f} rms={r['rms']*1e3:.3f} mJy -> peak={r['star_snr']*r['rms']*1e3:.1f} mJy  line={r['line']} off={r['line_off']}")
print()
print('=== A4/R1-M11/R2-M2: beta Pic B3 line offset ===')
for r in good:
    if 'bet Pic' in r['star_name'] or 'beta Pic' in r['star_name']:
        if r['star_snr']>=5.0:
            fc=0.5*(r['flo']+r['fhi'])
            print(f"  band {r['band_x']} fcen={fc:.6f} chanw={r['chanw']:.0f} line={r['line']} line_off={r['line_off']} kHz?")
            print(f"    line_off interpreted as MHz -> dv = {r['line_off']*1e-3/fc*C:.4f} km/s")
print()
print('=== R2-M10: radiometric q range ===')
q=[r['qa'] for r in good]; qm=st.median(q)
print('  min/med =',round(min(q)/qm,3),' max/med =',round(max(q)/qm,2))
byband=collections.defaultdict(list)
for r in good: byband[r['band_x']].append(r['qa']/qm)
for b in sorted(byband): print(f'   band {b}: n={len(byband[b])} median={st.median(byband[b]):.2f} range {min(byband[b]):.2f}-{max(byband[b]):.2f}')
print()
print('=== R2-M6: Band 8 windows ===')
b8=[r for r in good if r['band_x']==8]
print('  n=',len(b8),' stars=',sorted({r['star_name'] for r in b8}))
for r in b8: print(f"   {r['star_name']:20s} {r['flo']:.4f}-{r['fhi']:.4f} chanw={r['chanw']/1e3:.1f}kHz line={r['line']} star_snr={r['star_snr']:.2f} ctrlmax={r['ctrl_max_all']:.2f}")
print()
print('=== R1-M5: number of windows with on-star crossing (>=5 sigma) ===')
cross=[r for r in good if r['star_snr']>=5.0]
print('  n_cross windows =',len(cross))
print()
print('=== R2-m9: HD 139084B duplication ===')
for r in uniq:
    if '139084' in r['star_name']: print('  ',r['star_name'], round(r['dist_pc'],2), r['band_x'], r['eb'])
print()
print('=== R1-M12: stars vs systems ===')
stars=sorted({r['star_name'] for r in good}); print('  n_stars',len(stars))
