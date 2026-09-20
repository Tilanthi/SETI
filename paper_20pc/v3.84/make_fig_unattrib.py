#!/usr/bin/env python3
r"""The four unattributed candidate events, on one panel each.

Referee 1: these four events are what most readers will want to inspect,
so give them a single compact figure with the visibility diagnostic and
the control comparison together.

Each panel shows, in units of the measurement uncertainty: the real part
of the phase-rotated visibility at the stellar position (a point source
there would be positive and significant), its imaginary part (which must
be consistent with zero for a source at the star), and the real parts
returned by eight control positions on the same annulus the image-plane
screen uses.

Writes figures/unattributed_vis.pdf.
"""
import json, os
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

os.chdir(os.path.dirname(os.path.abspath(__file__)))
plt.rcParams.update({'pdf.fonttype': 42, 'ps.fonttype': 42,
                     'font.family': 'serif', 'font.serif': ['DejaVu Serif'],
                     'mathtext.fontset': 'dejavuserif'})

VIS = json.load(open('vistest_v384.json'))
ok = [(k, v) for k, v in VIS.items() if v.get('status') == 'ok']
ok.sort(key=lambda kv: -kv[1]['event']['star_snr'])

fig, axes = plt.subplots(1, len(ok), figsize=(7.1, 1.95),
                         gridspec_kw=dict(wspace=0.33))
for ax, (k, v) in zip(axes, ok):
    st, ev = v['star'], v['event']
    cs = [c['snr_re'] for c in v['controls'] if c['snr_re'] is not None]
    ax.axhline(0, color='0.75', lw=0.6)
    ax.errorbar([0], [st['snr_re']], yerr=[1.0], fmt='o', ms=4.5,
                color='#3a6ea5', capsize=2, lw=1.0, label='star, Re')
    ax.errorbar([0.45], [st['snr_im']], yerr=[1.0], fmt='s', ms=4.0,
                color='#b03030', capsize=2, lw=1.0, label='star, Im')
    ax.scatter(np.full(len(cs), 1.1) + np.linspace(-.18, .18, len(cs)), cs,
               s=9, facecolor='none', edgecolor='0.45', linewidth=0.6,
               label='controls, Re')
    ax.set_xlim(-0.35, 1.5)
    ax.set_xticks([0, 0.45, 1.1])
    ax.set_xticklabels(['Re', 'Im', 'ctrl'], fontsize=6.4)
    ax.set_ylim(-4.2, 4.6)
    ax.tick_params(labelsize=6.2)
    # Strip the Gaia designation: it overran the panel.
    nm = k.split('  Gaia')[0].split(' Gaia')[0].replace('CP-72', 'CP$-$72')
    ax.set_title('%s\n$T_\\star=%.2f$, B%s' % (nm, ev['star_snr'], ev['band']),
                 fontsize=6.6, pad=3)
    for sp in ('top', 'right'):
        ax.spines[sp].set_visible(False)
    ax.grid(axis='y', color='0.93', lw=0.4)
axes[0].set_ylabel('visibility amplitude / $\\sigma$', fontsize=7.0)
axes[-1].legend(fontsize=5.4, frameon=False, loc='lower right',
                handletextpad=0.4, borderpad=0.2)
fig.savefig('figures/unattributed_vis.pdf', bbox_inches='tight',
            pad_inches=0.02)
print('unattributed_vis.pdf: %d panels' % len(ok))
