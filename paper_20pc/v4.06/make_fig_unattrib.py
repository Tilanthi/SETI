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

VIS = json.load(open('vistest_v385.json' if os.path.exists('vistest_v385.json')
                     else 'vistest_v384.json'))
ok = [(k, v) for k, v in VIS.items() if v.get('status') == 'ok']
ok.sort(key=lambda kv: -kv[1]['event']['star_snr'])


def attributed(v):
    return 'CO' in str(v['event'].get('disposition', ''))


UN = [kv for kv in ok if not attributed(kv[1])]
AT = [kv for kv in ok if attributed(kv[1])]
NCOL = max(len(UN), 5)
NROW = 1 + (len(AT) + NCOL - 1) // NCOL

fig, axes = plt.subplots(NROW, NCOL, figsize=(7.1, 1.55 * NROW + 0.5),
                         gridspec_kw=dict(wspace=0.36, hspace=0.95))
axes = np.atleast_2d(axes)


def panel(ax, k, v, big):
    st = v['star']
    ev = v['event']
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
    # The attributed panels reach +59 sigma, so they cannot share the
    # unattributed panels' scale; each attributed panel is autoscaled and
    # says so, while the four unattributed share one fixed scale.
    if big:
        hi = max(6.0, 1.25 * max([st['snr_re']] + cs + [abs(st['snr_im'])]))
        ax.set_ylim(-0.12 * hi, hi)
    else:
        ax.set_ylim(-4.2, 4.6)
    ax.tick_params(labelsize=6.2)
    nm = k.split('|')[0].split('  Gaia')[0].split(' Gaia')[0]
    nm = nm.replace('CP-72', 'CP$-$72').replace('bet Pic', r'$\beta$ Pic')
    ax.set_title('%s\n$T_\\star=%.2f$, B%s' % (nm, ev['star_snr'], ev['band']),
                 fontsize=6.6, pad=3)
    for sp in ('top', 'right'):
        ax.spines[sp].set_visible(False)
    ax.grid(axis='y', color='0.93', lw=0.4)


for j in range(NCOL):
    ax = axes[0, j]
    if j < len(UN):
        panel(ax, UN[j][0], UN[j][1], False)
    else:
        ax.axis('off')
for n, (k, v) in enumerate(AT):
    r, c = 1 + n // NCOL, n % NCOL
    panel(axes[r, c], k, v, True)
for n in range(len(AT), (NROW - 1) * NCOL):
    axes[1 + n // NCOL, n % NCOL].axis('off')

axes[0, 0].set_ylabel('visibility / $\\sigma$', fontsize=7.0)
axes[1, 0].set_ylabel('visibility / $\\sigma$', fontsize=7.0)
axes[0, 0].text(-0.35, 1.52, 'unattributed events (shared scale)',
                transform=axes[0, 0].transAxes, fontsize=7.0,
                fontstyle='italic', ha='left')
axes[1, 0].text(-0.35, 1.52, 'events attributed to CO: the test\'s controls '
                '(panels autoscaled)', transform=axes[1, 0].transAxes,
                fontsize=7.0, fontstyle='italic', ha='left')
# The legend sat on HD 23484's control points; the first empty panel of
# the top row is free space.
_legax = axes[0, len(UN)] if len(UN) < NCOL else axes[0, len(UN) - 1]
_h, _l = axes[0, 0].get_legend_handles_labels()
_legax.legend(_h, _l, fontsize=6.0, frameon=False, loc='center',
              handletextpad=0.4, borderpad=0.2)
fig.savefig('figures/unattributed_vis.pdf', bbox_inches='tight',
            pad_inches=0.02)
print('unattributed_vis.pdf: %d unattributed + %d attributed panels'
      % (len(UN), len(AT)))
