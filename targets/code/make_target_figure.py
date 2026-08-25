import json, numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

top100 = json.load(open('ranked_top100.json'))
sizes = json.load(open('mous_sizes.json'))

fig, ax = plt.subplots(2, 2, figsize=(12, 9))

# (a) sky distribution
ra = np.array([s['ra'] for s in top100])
dec = np.array([s['dec'] for s in top100])
mdw = np.array([s['is_mdwarf'] for s in top100])
sun = np.array([s['is_sunlike'] for s in top100])
other = ~mdw & ~sun
sc = ax[0,0].scatter(ra[other], dec[other], c='gray', s=25, label='other', alpha=0.7)
ax[0,0].scatter(ra[mdw], dec[mdw], c='C3', s=30, label='M dwarf', alpha=0.8)
ax[0,0].scatter(ra[sun], dec[sun], c='C0', s=30, label='Sun-like (G)', alpha=0.8)
ax[0,0].set_xlabel('RA (deg)'); ax[0,0].set_ylabel('Dec (deg)')
ax[0,0].set_title('(a) Sky distribution of top-100 targets')
ax[0,0].legend(fontsize=8)

# (b) distance histogram
dist = np.array([s['dist_pc'] for s in top100])
ax[0,1].hist(dist, bins=20, color='C0', edgecolor='k')
ax[0,1].set_xlabel('Distance (pc)'); ax[0,1].set_ylabel('N targets')
ax[0,1].set_title(f'(b) Distance distribution (median {np.median(dist):.1f} pc)')

# (c) score component stack for top 20
top20 = top100[:20]
names = [s['name'][:16] for s in top20]
comps = ['score_dist','score_bright','score_startype','score_disk','score_exo','score_pmq','score_dataq']
W = dict(score_dist=0.30, score_bright=0.10, score_startype=0.20, score_disk=0.15,
         score_exo=0.15, score_pmq=0.05, score_dataq=0.05)
bottom = np.zeros(len(top20))
colors = plt.cm.tab10(np.linspace(0,1,len(comps)))
for comp, col in zip(comps, colors):
    vals = np.array([s[comp]*W[comp] for s in top20])
    ax[1,0].bar(names, vals, bottom=bottom, label=comp.replace('score_',''), color=col)
    bottom += vals
ax[1,0].set_ylabel('Weighted score contribution')
ax[1,0].set_title('(c) Score composition, top 20 targets')
ax[1,0].tick_params(axis='x', rotation=80, labelsize=7)
ax[1,0].legend(fontsize=6, ncol=2)

# (d) data volume distribution
vals = np.array([v for v in sizes.values() if v]) / 1e9
ax[1,1].hist(np.log10(vals), bins=20, color='C2', edgecolor='k')
ax[1,1].set_xlabel(r'$\log_{10}$(raw data volume / GB)')
ax[1,1].set_ylabel('N targets')
ax[1,1].set_title(f'(d) Best-MOUS raw data volume (total {vals.sum():.0f} GB)')

plt.tight_layout()
plt.savefig('target_list_summary.png', dpi=140)
print('saved target_list_summary.png')
