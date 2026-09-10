#!/usr/bin/env python3
"""EIRP threshold versus distance, single column.  Replaces the two-panel
EIRP+continuum figure of earlier versions: the continuum lane is deferred to
a companion paper, so its panel no longer belongs in this one."""
import json, math, collections, statistics as st
import matplotlib; matplotlib.use('Agg')
matplotlib.rcParams.update({'pdf.fonttype':42,'ps.fonttype':42,'font.size':7.5,
                            'axes.linewidth':0.6,'xtick.labelsize':7,'ytick.labelsize':7})
import matplotlib.pyplot as plt
exec(open('survey_stats.py').read().split("S=collections.OrderedDict()")[0])
best={}
for r in good:
    k=(r['star_name'],r['band_x'])
    if k not in best or r['eirp']<best[k]['eirp']: best[k]=r
rows=list(best.values())
fig=plt.figure(figsize=(3.4,2.9),constrained_layout=True)
ax=fig.add_subplot(111)
col={3:'#1f77b4',4:'#8c564b',5:'#9467bd',6:'#2ca02c',7:'#d62728',8:'#ff7f0e'}
for b in sorted({r['band_x'] for r in rows}):
    sub=[r for r in rows if r['band_x']==b]
    ax.scatter([r['dist_pc'] for r in sub],[r['eirp'] for r in sub],s=11,marker='v',
               facecolor='none',edgecolor=col[b],linewidths=0.7,label='B%d'%b)
flag={'bet Pic','CP-72 2713','HD 48370'}
sub=[r for r in rows if r['star_name'] in flag]
ax.scatter([r['dist_pc'] for r in sub],[r['eirp'] for r in sub],s=34,marker='*',
           color='k',zorder=5,label='flagged window')
ax.axhline(2e13,ls='--',lw=0.8,color='0.35')
ax.set_xscale('log'); ax.set_yscale('log')
ax.set_ylim(1.1e13,2.2e17)
ax.text(1.35,1.35e13,'Arecibo-like planetary radar',fontsize=5.8,color='0.35',va='bottom')
ax.set_xlabel('distance (pc)'); ax.set_ylabel(r'nominal EIRP$_{5\sigma}$ threshold (W)')
from matplotlib.ticker import FixedLocator, FixedFormatter
ax.xaxis.set_major_locator(FixedLocator([2,3,5,10,20,40]))
ax.xaxis.set_major_formatter(FixedFormatter(['2','3','5','10','20','40']))
ax.xaxis.set_minor_locator(FixedLocator([]))
ax.legend(fontsize=5.9,frameon=False,ncol=3,loc='upper left',handletextpad=0.25,
          columnspacing=0.7,borderpad=0.15)
ax.grid(alpha=0.25,lw=0.4)
fig.savefig('figures/eirp_vs_distance.pdf')
print('rows plotted',len(rows),'stars',len({r['star_name'] for r in rows}),
      'EIRP %.2g - %.2g'%(min(r['eirp'] for r in rows),max(r['eirp'] for r in rows)))
