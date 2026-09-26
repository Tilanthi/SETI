#!/usr/bin/env python3
"""Figure (replaces Fig. 5): the visibility-domain consistency check on every
threshold crossing, under BOTH epoch conventions.

The figure v4.01 ships shows one convention and therefore shows a test that
appears to reject almost everything.  It does not: with the drift referenced
to `median(TIME)` instead of the search's `times[0]`, the estimator evaluates
a channel displaced by nudot*(t_med - t_min)/dnu, and for an unresolved
carrier -- 2-3 channels wide -- that is a channel where nothing is.  The
displacement is the x-axis of the right panel, and the collapse is visible
along it.

Left panel: Re/sigma against Im/sigma, both conventions, joined by a line so
the movement of each crossing is legible; the committed criterion drawn as
the rectangle it is; the event-free control samples as the grey cloud.

Right panel: Re/sigma against |D|, the channel displacement between the two
conventions, which is what drives the change.  Below ~0.25 channels the two
conventions are the same experiment and the pairs sit on top of each other.

Reads ledger_v403.json only, so the figure cannot drift from the table.
Usage: python3 make_fig_ledger_v403.py [outdir]
"""
import json
import os
import sys

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt          # noqa: E402
import numpy as np                       # noqa: E402

# Type-3 fonts fail the manuscript's build gate: embed TrueType.
plt.rcParams.update({
    'font.family': 'serif',
    'font.serif': ['STIXGeneral', 'DejaVu Serif', 'Times New Roman'],
    'mathtext.fontset': 'stix',
    'font.size': 7.2,
    'axes.linewidth': 0.6,
    'pdf.fonttype': 42, 'ps.fonttype': 42,
    'figure.dpi': 200,
})

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = sys.argv[1] if len(sys.argv) > 1 else os.path.join(HERE, 'figures')
os.makedirs(OUT, exist_ok=True)

LED = json.load(open(os.path.join(HERE, 'ledger_v403.json')))
SUM, ROWS = LED['summary'], LED['rows']
RE_MIN = SUM['criterion']['re_min']
IM_MAX = SUM['criterion']['im_max']
D_SAME = SUM['criterion']['d_same_ch']

FIT = [r for r in ROWS if r['fitted'] and r['committed'] and r['adopted']]
UNT = [r for r in ROWS if not r['fitted']]

# the control samples, recomputed here would be a second source of truth, so
# they are read from the same fit files the ledger read
CTRL = []
for fn in SUM['fit_files']:
    for d in (HERE, os.path.join(HERE, 'inputs')):
        p = os.path.join(d, fn)
        if not os.path.exists(p):
            continue
        j = json.load(open(p))
        for rec in (j['fits'] if 'fits' in j else j).values():
            if rec.get('status') != 'ok':
                continue
            src = (rec.get('epoch') or {}).get('first') or rec
            for key in ('pos_controls', 'freq_controls'):
                for c in src.get(key) or []:
                    if c.get('snr_re') is not None and c.get('snr_im') is not None:
                        CTRL.append((float(c['snr_re']), float(c['snr_im'])))
        break
CTRL = np.array(CTRL) if CTRL else np.zeros((0, 2))

C_ATTR = '#1f6fb4'      # inside the +-50 km/s stellar-frame mask
C_UN = '#c0392b'        # outside it
fig, (axL, axR) = plt.subplots(1, 2, figsize=(7.1, 3.15))

# ------------------------------------------------------------------ left
if len(CTRL):
    axL.plot(CTRL[:, 0], CTRL[:, 1], '.', ms=1.6, color='0.78', zorder=1,
             label='event-free controls (%d)' % len(CTRL))
axL.add_patch(plt.Rectangle((RE_MIN, -IM_MAX), 60, 2 * IM_MAX,
                            facecolor='0.93', edgecolor='0.55', lw=0.6,
                            zorder=0))
axL.text(RE_MIN + 0.25, -IM_MAX + 0.25,
         r'criterion: Re/$\sigma\geq%.0f$, $|$Im/$\sigma|<%.0f$, '
         r'above all 12 controls' % (RE_MIN, IM_MAX),
         fontsize=5.4, color='0.35', zorder=6)

for r in FIT:
    col = C_ATTR if r['attributed'] else C_UN
    x0, y0 = r['committed']['re'], r['committed']['im']
    x1, y1 = r['adopted']['re'], r['adopted']['im']
    axL.annotate('', xy=(x1, y1), xytext=(x0, y0), zorder=2,
                 arrowprops=dict(arrowstyle='-|>', color=col, lw=0.45,
                                 alpha=0.55, shrinkA=1.2, shrinkB=1.2,
                                 mutation_scale=5))
    axL.plot([x0], [y0], 'o', ms=2.6, mfc='none', mec=col, mew=0.6, zorder=3)
    axL.plot([x1], [y1], 'o', ms=2.9, mfc=col, mec=col, mew=0.0, zorder=4,
             alpha=0.9)

axL.plot([], [], 'o', ms=3, mfc='none', mec='0.3', mew=0.6,
         label=r'committed $t_0=\mathrm{median}(T)$')
axL.plot([], [], 'o', ms=3, color='0.3', label=r'adopted $t_0=T_0$')
axL.plot([], [], 's', ms=3, color=C_ATTR, label='line-attributed')
axL.plot([], [], 's', ms=3, color=C_UN, label='unattributed')
axL.set_xlim(-4, 14)
axL.set_ylim(-5.5, 5.5)
axL.axhline(0, color='0.8', lw=0.4, zorder=0)
axL.axvline(0, color='0.8', lw=0.4, zorder=0)
axL.set_xlabel(r'Re/$\sigma$ at the stellar position')
axL.set_ylabel(r'Im/$\sigma$')
axL.legend(loc='upper left', fontsize=5.3, frameon=False, handlelength=1.2)
# BD+05 1668 sits at Re/sigma ~ 50 with Im/sigma ~ 30 under both conventions;
# it is off-scale by design, and is annotated rather than allowed to set the
# axis limits and flatten everything else into a dot.
_off = [r for r in FIT if r['adopted']['re'] > 14 or abs(r['adopted']['im']) > 5.5]
if _off:
    axL.text(0.985, 0.03,
             '%d crossings off-scale (%s: Re/$\\sigma$ to %.0f, '
             '$|$Im/$\\sigma|$ to %.0f)'
             % (len(_off), _off[0]['display'],
                max(r['adopted']['re'] for r in _off),
                max(abs(r['adopted']['im']) for r in _off)),
             transform=axL.transAxes, ha='right', va='bottom', fontsize=5.0,
             color='0.35')
axL.set_title('(a) the same fit, two reference epochs', fontsize=7.4)

# ----------------------------------------------------------------- right
for r in FIT:
    col = C_ATTR if r['attributed'] else C_UN
    d = abs(r['dch'] if r['dch'] is not None else 0.0)
    d = max(d, 0.02)
    axR.plot([d, d], [r['committed']['re'], r['adopted']['re']], '-',
             color=col, lw=0.45, alpha=0.5, zorder=2)
    axR.plot([d], [r['committed']['re']], 'o', ms=2.6, mfc='none', mec=col,
             mew=0.6, zorder=3)
    axR.plot([d], [r['adopted']['re']], 'o', ms=2.9, color=col, zorder=4,
             alpha=0.9)
axR.axhline(RE_MIN, color='0.3', lw=0.7, ls='--', zorder=1)
axR.text(0.022, RE_MIN + 0.18, r'Re/$\sigma=%.0f$' % RE_MIN, fontsize=5.4,
         color='0.3')
axR.axvline(D_SAME, color='0.55', lw=0.6, ls=':', zorder=1)
axR.text(D_SAME * 1.12, -3.4,
         'below %.2f channels the two\nconventions are the same fit'
         % D_SAME, fontsize=5.2, color='0.4')
axR.set_xscale('log')
axR.set_xlim(0.018, 60)
axR.set_ylim(-4, 14)
axR.set_xlabel(r'$|D|$, channel displacement between the two epochs')
axR.set_ylabel(r'Re/$\sigma$ at the stellar position')
axR.set_title('(b) the change is displacement-driven', fontsize=7.4)

fig.text(0.005, 0.012,
         '%d of %d crossings fitted; %d untested (fit outstanding, shown in '
         'the table, absent here). Localised: %d committed, %d adopted '
         '(%d with the epoch residual verified).'
         % (SUM['n_fitted'], SUM['n_crossings'], SUM['n_untested'],
            SUM['n_localised_committed'], SUM['n_localised_corrected'],
            SUM['n_localised_corrected_verified']),
         fontsize=5.2, color='0.3')
fig.tight_layout(rect=(0, 0.035, 1, 1))
for ext in ('pdf', 'png'):
    fig.savefig(os.path.join(OUT, 'ledger_vis_v403.' + ext),
                bbox_inches='tight', pad_inches=0.01)
print('figures/ledger_vis_v403.pdf written (%d fitted, %d untested, %d controls)'
      % (len(FIT), len(UNT), len(CTRL)))
