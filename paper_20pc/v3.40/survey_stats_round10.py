#!/usr/bin/env python3
"""Authoritative survey statistics for the 0-40 pc release.  Every number
quoted in the paper is produced here, from one frozen export, so text,
tables and figures cannot drift apart.   Writes survey_stats.json.
"""
import json, math, collections, statistics as st, itertools

SRC='frozen_export_v3.31.json'
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
       ('LP 476-207 384128','LP 476-207 783296'),('V star TX PsA','V star WW PsA')]
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

# ---- measured detection completeness, from the 3888-trial injection campaign -
# Each trial injects a tone of amplitude amp_sigma (in units of the
# per-integration rms) present for a fraction f_dwell of the track.  The
# pipeline stacks by an inverse-variance-weighted SUM over ALL integrations, so
# the signal accumulates as amp * f_dwell * sqrt(N_int) while the noise
# accumulates as sqrt(N_int): the equivalent amplitude in units of the window's
# own quoted 5-sigma threshold is therefore
#     a = amp_sigma * f_dwell * sqrt(N_int).
# Binning the trials in a unifies the dwell and amplitude axes and yields a
# completeness curve measured across 12 window configurations in 3 ALMA bands,
# replacing the single-configuration curve transferred in earlier releases.
import csv as _csv
_TR=list(_csv.DictReader(open('dwell_campaign_trials_v3.32.csv')))
for _r in _TR:
    _r['a']=float(_r['amp_sigma'])*float(_r['dwell'])*math.sqrt(int(_r['n_int']))
    _r['det']=_r['detected'].lower()=='true'
_EFF=st.median([float(_r['recovered_snr'])/_r['a'] for _r in _TR if _r['a']>3 and _r['det']])
S['inj_trials']=len(_TR); S['inj_win']=len({_r['window'] for _r in _TR})
S['inj_tgt']=len({_r['target'] for _r in _TR}); S['inj_bands']=sorted({int(_r['band']) for _r in _TR})
S['inj_eff']=_EFF
_EDG=[0,3,4,5,6,7,8,10,1e9]
_CURVE={}
for _c in ('coarse','fine'):
    pts=[]
    for lo,hi in zip(_EDG,_EDG[1:]):
        sel=[r for r in _TR if r['klass']==_c and lo<=r['a']<hi]
        if len(sel)<12: continue
        pts.append((0.5*(lo+min(hi,25.0)), sum(r['det'] for r in sel)/len(sel), sum(r['det'] for r in sel), len(sel)))
    _CURVE[_c]=pts
S['completeness_curve']={k:[(round(a,2),round(p,3),k1,n) for a,p,k1,n in v] for k,v in _CURVE.items()}
def _cmp(cls,a):
    """Measured detection completeness of class `cls` at amplitude `a`, in units
    of that window's own quoted 5-sigma threshold."""
    pts=_CURVE[cls]
    if a<=pts[0][0]: return 0.0
    if a>=pts[-1][0]: return pts[-1][1]
    for i in range(len(pts)-1):
        if pts[i][0]<=a<pts[i+1][0]:
            u=(a-pts[i][0])/(pts[i+1][0]-pts[i][0]); return pts[i][1]+u*(pts[i+1][1]-pts[i][1])
    return pts[-1][1]
S['C_at_5_coarse']=_cmp('coarse',5.0); S['C_at_5_fine']=_cmp('fine',5.0)
S['C_at_8_coarse']=_cmp('coarse',8.0); S['C_at_8_fine']=_cmp('fine',8.0)

# ---- drift excursion over the track, which is what makes the coarse class
# ---- differ from the fine one: sub-channel drift means no smearing loss, and
# ---- equally no drift discrimination.
for _c in ('coarse','fine'):
    v=sorted(r['drift_max']*r['onsrc']/r['chanw'] for r in good if r['res_x']==_c)
    S['drchan_med_'+_c]=st.median(v); S['drchan_max_'+_c]=v[-1]
    S['drchan_sub_'+_c]=sum(1 for x in v if x<1.0); S['drchan_n_'+_c]=len(v)
S['drchan_sub_pct_coarse']=100.0*S['drchan_sub_coarse']/S['drchan_n_coarse']

# ---- effective search bandwidth after the molecular-line exclusion mask ------
LINES_GHZ={'CO(1-0)':115.271,'CO(2-1)':230.538,'CO(3-2)':345.796,'CO(4-3)':461.041,
  'CO(6-5)':691.473,'13CO(2-1)':220.399,'C18O(2-1)':219.560,'HCN(1-0)':88.632,
  'HCN(3-2)':265.886,'HCO+(1-0)':89.189,'HCO+(3-2)':267.558,'CS(5-4)':244.936,
  'CN(1-0)':113.491,'SiO(5-4)':217.105,'H2CO':218.222}
S['n_lines']=len(LINES_GHZ)
_VMASK=50.0; _C=299792.458
_masked=[]
for f0 in LINES_GHZ.values():
    h=f0*_VMASK/_C; _masked.append((f0-h,f0+h))
def _sub(iv,cut):
    out=[]
    for lo,hi in iv:
        seg=[(lo,hi)]
        for a,b in cut:
            nxt=[]
            for x,y in seg:
                if b<=x or a>=y: nxt.append((x,y)); continue
                if a>x: nxt.append((x,min(a,y)))
                if b<y: nxt.append((max(b,x),y))
            seg=nxt
        out+=seg
    return [(a,b) for a,b in out if b>a]
S['eff_band_GHz']=sum(b-a for a,b in _sub([(a,b) for a,b in mg],_masked))
S['mask_loss_GHz']=S['union_GHz']-S['eff_band_GHz']

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
C5=0.42   # legacy single-configuration recovery, retained for comparison only
for P in (1e15,1e16,1e17):
    unit=[];uni=[];fine=[];allw=[];unit5=[];fine5=[];all5=[];all1=[]
    nsys=nfin=nall=0
    for s_,rs in bysys.items():
        ba=min(r['eirp'] for r in rs)
        a=1.0 if ba<=P else 0.0
        fw=[r for r in rs if r['res_x']=='fine']
        den=sum(abs(r['fhi']-r['flo']) for r in fw)
        f2=(sum(abs(r['fhi']-r['flo'])*_rec(5.0*P/r['eirp']) for r in fw)/den) if den>0 else 0.0
        # Coarse-inclusive: every searched window contributes its own class's
        # measured completeness FOR ITS OWN SEARCHED MORPHOLOGY.
        #   fine (Class A): the searched class is the DRIFTING carrier, whose
        #     curve is _rec() -- still the single v3.28 calibration
        #     configuration.  The dwell campaign injects NON-drifting carriers
        #     and cannot stand in for it.
        #   coarse (Class B): drift is sub-channel over the track, so the
        #     searched class IS the persistent/partial-dwell unresolved
        #     carrier -- exactly what the dwell campaign injects, measured
        #     across six coarse configurations.
        # Mixing the two curves is the point: each class gets the completeness
        # that was actually measured for what it actually searches.
        dena=sum(abs(r['fhi']-r['flo']) for r in rs)
        _cw=lambda r: _rec(5.0*P/r['eirp']) if r['res_x']=='fine' else _cmp('coarse',5.0*P/r['eirp'])
        fa=(sum(abs(r['fhi']-r['flo'])*_cw(r) for r in rs)/dena) if dena>0 else 0.0
        # Duty cycle uses the paper's CORRECTED Bernoulli form (round-5 fix,
        # R1's #1): a system observed in n_i independent execution blocks is
        # sampled n_i times, so D_i = 1-(1-D)^n_i, NOT D_i = D.  n_i is the
        # number of distinct EBs contributing windows to that system.
        ni=len({r['eb'] for r in rs}) or 1
        d5=1.0-(1.0-0.5)**ni; d1=1.0-(1.0-0.1)**ni
        nsys+=int(a>0); nfin+=int(f2>0); nall+=int(fa>0)
        unit.append(a); uni.append(C5*a); fine.append(f2); allw.append(fa)
        unit5.append(d5*a); fine5.append(d5*f2); all5.append(d5*fa); all1.append(d1*fa)
    S['occurrence']['%.0e'%P]={'n_sys':nsys,'n_sys_fine':nfin,'n_sys_all':nall,
        'unit':limit(unit),'uniform':limit(uni),'measured':limit(fine),
        'all':limit(allw),'all_D05':limit(all5),'all_D01':limit(all1),
        'unit_D05':limit(unit5),'measured_D05':limit(fine5)}
json.dump(S,open('survey_stats_round10.json','w'),indent=1,default=str)
for k,v in S.items():
    if k in ('flagged','old_only','occurrence'): continue
    print('%-22s %s'%(k,('%.6g'%v if isinstance(v,float) else v)))
print('\nFLAGGED:');  [print('  ',f) for f in S['flagged']]
print('\nOLD-ONLY (removed by the symmetric criterion):'); [print('  ',f) for f in S['old_only']]
print('\nOCCURRENCE:'); [print('  ',k,v) for k,v in S['occurrence'].items()]
