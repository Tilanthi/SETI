#!/usr/bin/env python3
"""Cumulative N(<d) for the 40 pc Gaia reference census, the 168-star
ALMA-covered census, and the stars searched in this release.  Replaces a
figure that still carried 20 pc-era labels and an n=86 searched count."""
import csv, math, json, collections
import matplotlib; matplotlib.use('Agg')
matplotlib.rcParams.update({'pdf.fonttype':42,'font.size':7.5,'axes.linewidth':0.6,
                            'xtick.labelsize':7,'ytick.labelsize':7})
import matplotlib.pyplot as plt, numpy as np
exec(open('survey_stats.py').read().split("S=collections.OrderedDict()")[0])

# Gaia reference census within 40 pc, same cut as tab:selfunc
gaia=[]
with open('/workspace/SETI/gaia_nearby50pc.ecsv') as f:
    hdr=None
    for line in f:
        if line.startswith('#'): continue
        p=line.split()
        if hdr is None: hdr=p; continue
        try:
            plx=float(p[hdr.index('parallax')]); e=float(p[hdr.index('parallax_error')])
        except Exception: continue
        if plx>0 and e/plx<=0.10:
            d=1000.0/plx
            if d<=40.0: gaia.append(d)
census=[float(r['dist_pc']) for r in csv.DictReader(open('/workspace/SETI/ranked_master40pc.csv'))]
searched={}
for r in good: searched[r['star_name']]=r['dist_pc']
srch=sorted(searched.values())
def cum(x):
    x=np.sort(np.asarray(x)); return x, np.arange(1,x.size+1)
fig=plt.figure(figsize=(3.4,2.6),constrained_layout=True); ax=fig.add_subplot(111)
for data,col,lab in ((gaia,'0.55','Gaia DR3 reference census (n=%d)'%len(gaia)),
                     (census,'#1f77b4','ALMA-covered census (n=%d)'%len(census)),
                     (srch,'#d62728','searched in this release (n=%d)'%len(srch))):
    x,y=cum(data); ax.step(x,y,where='post',color=col,lw=1.3,label=lab)
ax.set_yscale('log'); ax.set_xlim(0,40)
ax.set_xlabel('distance $d$ (pc)'); ax.set_ylabel('$N(<d)$')
ax.legend(fontsize=5.9,frameon=False,loc='lower right',handletextpad=0.5,borderpad=0.2)
ax.grid(alpha=0.25,lw=0.4)
ax.text(0.03,0.95,'ALMA-covered fraction of the reference census: %.1f%%'%(100*len(census)/len(gaia)),
        transform=ax.transAxes,fontsize=5.9,va='top')
fig.savefig('figures/sample_distance_distribution.pdf')
print('gaia %d  census %d  searched %d  fraction %.2f%%'%(len(gaia),len(census),len(srch),
      100*len(census)/len(gaia)))
