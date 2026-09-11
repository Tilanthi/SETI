#!/usr/bin/env python3
"""Authoritative survey statistics for the 0-40 pc release.  Every number
quoted in the paper is produced here, from one frozen export, so text,
tables and figures cannot drift apart.   Writes survey_stats.json.
"""
import json, math, collections, statistics as st, itertools

SRC='frozen_export_v3.31.json'   # v3.42: was an absolute path outside the
                                 # release folder; byte-identical file, now local
C=299792.458
d=json.load(open(SRC)); rows=d['rows']

def band_of(r):
    if r['band'] is not None: return r['band']
    f=0.5*(r['flo']+r['fhi'])
    for lo,hi,b in [(84,116,3),(125,163,4),(163,211,5),(211,275,6),(275,373,7),(385,500,8)]:
        if lo<=f<hi: return b
for r in rows:
    r['band_x']=band_of(r)
    r['res_x']='fine' if r['chanw']<5e6 else 'coarse'
    r['qa']=r['rms']*math.sqrt(r['onsrc']*r['chanw'])
    r['ctrl_max_all']=max(r['ctrl_all']) if r['ctrl_all'] else r['ctrl_max']

# 1. de-duplicate repeated window rows (catalogue audit); keep the annotated row
key=lambda r:(r['star_name'],r['eb'],round(min(r['flo'],r['fhi']),6),
              round(max(r['flo'],r['fhi']),6),r['chanw'])
best={}
for r in rows:
    k=key(r)
    if k not in best or (best[k]['line'] is None and r['line'] is not None): best[k]=r
uniq=list(best.values()); n_dup=len(rows)-len(uniq)

# 2. noise-handling defect: physical test.  sigma*sqrt(t_on*dnu_ch) is fixed by
#    Tsys and collecting area, so it varies by factors of a few across an
#    archive; >100x below the sample median cannot be a real measurement.
qa_med=st.median(r['qa'] for r in uniq)
defect=[r for r in uniq if r['qa']<qa_med/100.0]
kept=[r for r in uniq if r['qa']>=qa_med/100.0]

# 3. withheld: eps Eri Band 6 sits at ~0.7 primary-beam FWHM, where the
#    Gaussian beam form used for the correction (2.9-3.4x) is not valid.
withheld=[r for r in kept if r['star_name']=='eps Eri' and r['band_x']==6]
good=[r for r in kept if r not in withheld]

# 4. independent systems: components of one bound system count once
PAIRS=[('2MASS J05241914-1601153 551040','2MASS J05241914-1601153 717696'),
       ('NAME AT Mic AB  Gaia DR3 6792436799475128960','V AT Mic B'),
       ('G 272-61A','G 272-61B'),('GJ 2006A','GJ 2006B'),
       ('LP 476-207 384128','LP 476-207 783296'),('V star TX PsA','V star WW PsA'),
       # v3.42 (referee A1): HD 139084B appears under two catalogue entries with
       # identical EB, spectral windows and on-source times but different
       # system ids and distances (39.31 / 38.72 pc).  It is one system.
       ('HD 139084B 805632','HD 139084B 921024')]
sysof={}
for a,b in PAIRS: sysof[a]=a; sysof[b]=a
sysn=lambda n: sysof.get(n,n)

for r in good:
    r['sbr']=r['star_snr']>r['ctrl_max_all']
    r['sbr_old']=r['src_snr']>r['ctrl_max']
    r['cross']=r['star_snr']>=5.0
    r['p_emp']=(1+sum(1 for c in r['ctrl_all'] if c>=r['star_snr']))/(len(r['ctrl_all'])+1)
    r['vel_off']=(r['line_off']*1e-3/(0.5*(r['flo']+r['fhi']))*C) if r['line_off'] is not None else None

def wilson(k,n,z=1.96):
    p=k/n; den=1+z*z/n; c=(p+z*z/(2*n))/den
    h=z*math.sqrt(p*(1-p)/n+z*z/(4*n*n))/den; return (c-h,c+h)

S=collections.OrderedDict()
S['n_census']=len(d['census'])
S['n_dup']=n_dup; S['n_defect']=len(defect); S['n_withheld']=len(withheld)
S['n_windows']=len(good)
S['defect_stars']=sorted({r['star_name'] for r in defect})
S['defect_gap']=round(min(r['qa'] for r in good)/max(r['qa'] for r in defect),0)
S['defect_eirp_lo']=min(r['eirp'] for r in defect); S['defect_eirp_hi']=max(r['eirp'] for r in defect)
stars=sorted({r['star_name'] for r in good}); systems=sorted({sysn(s) for s in stars})
S['n_stars']=len(stars); S['n_systems']=len(systems)
S['n_starbands']=len({(r['star_name'],r['band_x']) for r in good})
S['n_eb']=len({r['eb'] for r in good})
S['dist_min']=min(r['dist_pc'] for r in good); S['dist_max']=max(r['dist_pc'] for r in good)
S['bands']=dict(sorted(collections.Counter(r['band_x'] for r in good).items()))
S['n_fine']=sum(1 for r in good if r['res_x']=='fine')
S['n_coarse']=sum(1 for r in good if r['res_x']=='coarse')
e=[r['eirp'] for r in good]
S['eirp_min']=min(e); S['eirp_max']=max(e); S['eirp_median']=st.median(e)
byst={}
for r in good: byst[r['star_name']]=min(byst.get(r['star_name'],9e99),r['eirp'])
S['star_deepest']=min(byst,key=byst.get); S['n_star_below_arecibo']=sum(1 for v in byst.values() if v<2e13)
S['smin_min']=min(r['smin'] for r in good)*1e3; S['smin_max']=max(r['smin'] for r in good)*1e3
S['smin_median']=st.median(r['smin'] for r in good)*1e3
S['chanw_min']=min(r['chanw'] for r in good); S['chanw_max']=max(r['chanw'] for r in good)
S['chanw_median']=st.median(r['chanw'] for r in good)
S['drift_min']=min(r['drift_max'] for r in good); S['drift_max']=max(r['drift_max'] for r in good)
S['ndrift_min']=min(r['ndrift'] for r in good); S['ndrift_max']=max(r['ndrift'] for r in good)
S['ndrift_median']=st.median(r['ndrift'] for r in good)
S['onsrc_min']=min(r['onsrc'] for r in good); S['onsrc_max']=max(r['onsrc'] for r in good)
S['onsrc_median']=st.median(r['onsrc'] for r in good)
iv=sorted((min(r['flo'],r['fhi']),max(r['flo'],r['fhi'])) for r in good); mg=[]
for lo,hi in iv:
    if mg and lo<=mg[-1][1]: mg[-1][1]=max(mg[-1][1],hi)
    else: mg.append([lo,hi])
S['union_GHz']=sum(b-a for a,b in mg); S['union_intervals']=len(mg)
S['union_lo']=mg[0][0]; S['union_hi']=mg[-1][1]
S['gross_bw_GHz']=sum(abs(r['fhi']-r['flo']) for r in good)
S['exposure_sGHz']=sum(r['onsrc']*abs(r['fhi']-r['flo']) for r in good)
S['n_sbr']=sum(1 for r in good if r['sbr']); S['rate_sbr']=S['n_sbr']/len(good)
S['wilson_sbr']=wilson(S['n_sbr'],len(good))
S['n_sbr_old']=sum(1 for r in good if r['sbr_old']); S['rate_sbr_old']=S['n_sbr_old']/len(good)
S['wilson_sbr_old']=wilson(S['n_sbr_old'],len(good))
S['n_cross']=sum(1 for r in good if r['cross'])
S['n_src']=int(st.median(r['n_src'] for r in good)); S['n_ctrl']=int(st.median(r['n_ctrl'] for r in good))
S['exch']=1.0/(S['n_ctrl']+1); S['expected_flags']=len(good)*S['exch']
S['asym_expect']=S['n_src']/(S['n_src']+S['n_ctrl'])
S['trial_cells']=sum(int(abs(r['fhi']-r['flo'])*1e9/r['chanw'])*r['ndrift'] for r in good)
fl=[r for r in good if r['cross'] and r['sbr']]
flold=[r for r in good if r['cross'] and r['sbr_old']]
S['n_flagged']=len(fl); S['n_flagged_old']=len(flold)
S['old_only']=[{'star':r['star_name'],'band':r['band_x'],'src_snr':round(r['src_snr'],2),
                'star_snr':round(r['star_snr'],2),'ctrl_max':round(r['ctrl_max_all'],2)}
               for r in flold if not r['sbr']]
S['sym_subset_of_old']=all(r['sbr_old'] for r in fl)
S['flagged']=[{'star':r['star_name'],'band':r['band_x'],'f_GHz':round(0.5*(r['flo']+r['fhi']),4),
  'chanw_kHz':round(r['chanw']/1e3,2),'star_snr':round(r['star_snr'],2),
  'ctrl_max':round(r['ctrl_max_all'],2),'p':round(r['p_emp'],5),'eirp':r['eirp'],
  'dist_pc':round(r['dist_pc'],2),'line':r['line'],
  'line_off_MHz':(round(r['line_off'],2) if r['line_off'] is not None else None),
  'vel_kms':(round(r['vel_off'],1) if r['vel_off'] is not None else None),
  'eb':r['eb'],'onsrc':round(r['onsrc'],1)} for r in fl]
S['n_flag_line']=sum(1 for f in S['flagged'] if f['vel_kms'] is not None and abs(f['vel_kms'])<=50)
S['n_flag_unattributed']=S['n_flagged']-S['n_flag_line']

# ---- occurrence limits ----------------------------------------------------
bysys=collections.defaultdict(list)
for r in good: bysys[sysn(r['star_name'])].append(r)
_A=[4.0,5.0,6.0,8.0,10.0]; _R=[0.17,0.42,0.58,0.75,0.83]
def _rec(a):
    """Measured injection recovery of the searched class vs amplitude in sigma."""
    if a<_A[0]: return 0.0
    if a>=_A[-1]: return _R[-1]
    for i in range(len(_A)-1):
        if _A[i]<=a<_A[i+1]:
            u=(a-_A[i])/(_A[i+1]-_A[i]); return _R[i]+u*(_R[i+1]-_R[i])
    return 0.0

def limit(Cs):
    Cs=[c for c in Cs if c>0]
    if not Cs: return None
    f=lambda x: sum(math.log(max(1e-300,1-x*c)) for c in Cs)-math.log(0.05)
    if f(1.0)>0: return None
    lo,hi=1e-9,1.0
    for _ in range(200):
        m=0.5*(lo+hi)
        if f(m)>0: lo=m
        else: hi=m
    return 0.5*(lo+hi)
# Occurrence limits use the bandwidth-integrated measured recovery, which is
# what the paper quotes; see occurrence_v328.py for the standalone derivation.
S['occurrence']={}
C5=0.42   # measured recovery of the searched class at the nominal threshold
for P in (1e15,1e16,1e17):
    unit=[];uni=[];fine=[];unit5=[];fine5=[]
    nsys=nfin=0
    for s,rs in bysys.items():
        ba=min(r['eirp'] for r in rs)
        bf=min((r['eirp'] for r in rs if r['res_x']=='fine'),default=None)
        a=1.0 if ba<=P else 0.0
        fw=[r for r in rs if r['res_x']=='fine']
        den=sum(abs(r['fhi']-r['flo']) for r in fw)
        f2=(sum(abs(r['fhi']-r['flo'])*_rec(5.0*P/r['eirp']) for r in fw)/den) if den>0 else 0.0
        nsys+=int(a>0); nfin+=int(f2>0)
        unit.append(a); uni.append(C5*a); fine.append(f2)
        unit5.append(0.5*a); fine5.append(0.5*f2)
    S['occurrence']['%.0e'%P]={'n_sys':nsys,'n_sys_fine':nfin,
        'unit':limit(unit),'uniform':limit(uni),'measured':limit(fine),
        'unit_D05':limit(unit5),'measured_D05':limit(fine5)}
json.dump(S,open('survey_stats.json','w'),indent=1,default=str)
for k,v in S.items():
    if k in ('flagged','old_only','occurrence'): continue
    print('%-22s %s'%(k,('%.6g'%v if isinstance(v,float) else v)))
print('\nFLAGGED:');  [print('  ',f) for f in S['flagged']]
print('\nOLD-ONLY (removed by the symmetric criterion):'); [print('  ',f) for f in S['old_only']]
print('\nOCCURRENCE:'); [print('  ',k,v) for k,v in S['occurrence'].items()]
