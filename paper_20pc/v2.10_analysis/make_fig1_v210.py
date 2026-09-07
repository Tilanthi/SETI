import json
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np

rows = json.load(open('/workspace/SETI/paper_20pc/paper_v210_rows.json'))

# main sample: deepest EIRP per target/band group -> actually deepest per unique target (across bands)
best_eirp = {}  # name -> (dist, eirp)
for r in rows:
    if not r['techno']:
        continue
    best = min(t['EIRP_min_W'] for t in r['techno'])
    key = r['name']
    if key not in best_eirp or best < best_eirp[key][1]:
        best_eirp[key] = (r['dist'], best, r['disp'])

cand_names = {'AU Mic', 'bet Pic'}

eirp_dist = np.array([v[0] for v in best_eirp.values()])
eirp_val = np.array([v[1] for v in best_eirp.values()])
eirp_iscand = np.array([k in cand_names for k in best_eirp.keys()])

# continuum
cont_dist_det, cont_val_det = [], []
cont_dist_nondet, cont_val_nondet = [], []
for r in rows:
    c = r['cont']
    if not c or 'continuum_source_detected' not in c:
        continue
    if c['continuum_source_detected']:
        cont_dist_det.append(r['dist']); cont_val_det.append(c['image_peak_mJy'])
    else:
        cont_dist_nondet.append(r['dist']); cont_val_nondet.append(c['image_rms_mJy']*5)

# 20-30pc extension data
ext = [
    ("HD 45184", 21.89, 3.034137161817094e15, 0.5974, False),   # (name, dist, eirp, contval, det)
    ("HD 107146", 27.47, 4.857157314205755e15, 0.02573, False),
    ("HD 31392", 25.76, 4.845615129302079e15, 0.7051, False),
    ("L 836-122", 28.70, 7.10466712834169e14, 63.069, True),
    ("HD 92945", 21.51, 3.0611037720268585e15, 2.2008, True),
]
ext_cont_only = [
    ("CD-57 1054", 26.87, 25.371, True),
    ("LP 476-207", 23.79, 22.055, True),
]

fig, axes = plt.subplots(1, 2, figsize=(11, 4.3))

ax = axes[0]
ax.scatter(eirp_dist[~eirp_iscand], eirp_val[~eirp_iscand], c='steelblue', s=28, label='EIRP$_{min}$ (deepest window per target)', zorder=3)
ax.scatter(eirp_dist[eirp_iscand], eirp_val[eirp_iscand], c='steelblue', s=140, marker='*', edgecolor='k', label='automated candidate flag (not credible, see text)', zorder=4)
ext_x = [e[1] for e in ext]; ext_y = [e[2] for e in ext]
ax.scatter(ext_x, ext_y, facecolor='none', edgecolor='darkorange', marker='D', s=55, linewidth=1.5, label='20--30 pc extension (preliminary, Appendix B)', zorder=3)
ax.axhline(2e13, color='green', ls='--', lw=1, label='Arecibo-like planetary radar ($2\\times10^{13}$ W)')
ax.set_yscale('log')
ax.set_xlabel('Distance (pc)')
ax.set_ylabel('EIRP$_{min}$ (W)')
ax.set_title('Technosignature EIRP limits')
ax.legend(fontsize=6.3, loc='lower right')
ax.set_xlim(0, 30)

ax2 = axes[1]
ax2.scatter(cont_dist_nondet, cont_val_nondet, marker='v', c='indianred', s=26, label='non-detection ($5\\sigma$ UL)', zorder=3)
ax2.scatter(cont_dist_det, cont_val_det, marker='o', c='indianred', s=30, label='detection', zorder=3)
ext_cont_x = [e[1] for e in ext]; ext_cont_y = [e[3] for e in ext]
ext_cont_det = [e[4] for e in ext]
ext2_x = [e[1] for e in ext_cont_only]; ext2_y = [e[2] for e in ext_cont_only]
ax2.scatter(ext_cont_x, ext_cont_y, facecolor='none', edgecolor='darkorange', marker='D', s=55, linewidth=1.5, label='20--30 pc extension (preliminary, Appendix B)', zorder=3)
ax2.scatter(ext2_x, ext2_y, facecolor='none', edgecolor='darkorange', marker='D', s=55, linewidth=1.5, zorder=3)
ax2.set_yscale('log')
ax2.set_xlabel('Distance (pc)')
ax2.set_ylabel('Continuum flux density (mJy)')
ax2.set_title('Continuum measurements')
ax2.legend(fontsize=6.3, loc='upper left')
ax2.set_xlim(0, 30)

plt.tight_layout()
plt.savefig('/workspace/SETI/paper_20pc/v2.10/figures/eirp_continuum_vs_distance.pdf')
plt.savefig('/workspace/SETI/paper_20pc/v2.10/figures/eirp_continuum_vs_distance.png', dpi=150)
print("done", len(best_eirp), "unique targets w/ EIRP")
