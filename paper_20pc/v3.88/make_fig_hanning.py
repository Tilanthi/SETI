#!/usr/bin/env python3
r"""Schematic of why the nominal channel threshold is not the transmitter threshold.

ALMA applies online Hanning smoothing by default. An intrinsically
unresolved carrier is therefore never wholly contained in one channel, and
how much of it survives into the peak channel depends on where between two
channel centres it happens to fall. The search threshold is expressed in
units of the channel noise, so the power a transmitter must radiate to
trigger it is larger than the nominal figure by the reciprocal of that
fraction -- best case at a channel centre, worst on a boundary.

The correction is the single most consequential methodological number in
the paper and it is hard to believe from a sentence. This draws it: the
same carrier at three offsets, with the smoothed channel values it
produces, and the resulting power penalty.

Reads survey_numbers*.tex for the three generated values so the figure
cannot disagree with the text. Writes figures/hanning_response.pdf.
"""
import glob, os, re
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

# Embed TrueType, as every other figure generator here does: the default
# Type 3 fonts are bitmapped, unselectable, and fail the build's font gate.
plt.rcParams.update({'pdf.fonttype': 42, 'ps.fonttype': 42,
                     'font.family': 'serif',
                     'font.serif': ['DejaVu Serif'],
                     'mathtext.fontset': 'dejavuserif'})

os.chdir(os.path.dirname(os.path.abspath(__file__)))


def texval(name):
    for f in sorted(glob.glob('survey_numbers*.tex')):
        m = re.search(r'\\newcommand\{\\%s\}\{([^}]*)\}' % name, open(f).read())
        if m:
            return m.group(1)
    return None


BEST = float(texval('HanBest') or 0.500)
WORST = float(texval('HanWorst') or 0.375)
# Use the paper's own median correction rather than the reciprocal of a
# rounded fraction: 1/0.44 is 2.27 where the per-window median is 2.29, and
# a figure that disagrees with the text by two in the second decimal is
# worse than no figure.
MEDFAC = float(texval('HanFacMed') or 2.29)

# Hanning weights over three raw channels, the response ALMA applies.
W = np.array([0.25, 0.50, 0.25])


def smoothed(offset, n=9):
    """Channel values for an unresolved line at `offset` channels from the
    centre of channel n//2, after Hanning smoothing. Unit total power."""
    raw = np.zeros(n)
    i = n // 2
    f = offset - np.floor(offset)
    raw[i + int(np.floor(offset))] += 1.0 - f
    if f > 0:
        raw[i + int(np.floor(offset)) + 1] += f
    return np.convolve(raw, W, mode='same')


fig, axes = plt.subplots(1, 4, figsize=(7.1, 1.85),
                         gridspec_kw=dict(width_ratios=[1, 1, 1, 1.15],
                                          wspace=0.33))
cases = [(0.0, 'at channel centre', BEST),
         (0.25, 'quarter channel off', None),
         (0.5, 'on channel boundary', WORST)]
x = np.arange(-4, 5)
for ax, (off, lab, frac) in zip(axes[:3], cases):
    y = smoothed(off)
    ax.bar(x, y, width=0.9, color='0.78', edgecolor='0.35', linewidth=0.4)
    peak = y.max()
    ax.bar(x[np.argmax(y)], peak, width=0.9, color='#4878a8',
           edgecolor='0.2', linewidth=0.5)
    ax.axvline(off, color='#b03030', lw=1.0, ls='--')
    ax.set_xlim(-3.2, 3.2)
    ax.set_ylim(0, 0.58)
    ax.set_title(lab, fontsize=6.0, pad=3)
    ax.tick_params(labelsize=5.4, length=2, pad=1.2)
    ax.set_xlabel('channel', fontsize=6.0, labelpad=1.0)
    ax.text(0.03, 0.93, 'peak channel holds\n%.0f per cent' % (100 * peak),
            transform=ax.transAxes, fontsize=5.6, va='top')
axes[0].set_ylabel('fraction of carrier\npower in channel', fontsize=6.0,
                   labelpad=1.5)

# the penalty as a function of offset
ax = axes[3]
offs = np.linspace(0, 0.5, 101)
pen = np.array([1.0 / smoothed(o).max() for o in offs])
ax.plot(offs, pen, color='#4878a8', lw=1.2)
ax.axhline(MEDFAC, color='#b03030', lw=0.9, ls=':')
ax.text(0.015, MEDFAC, ' survey median $\\times%.2f$' % MEDFAC,
        fontsize=5.6, va='bottom', color='#b03030')
ax.set_xlim(0, 0.5)
ax.set_xlabel('offset from channel centre', fontsize=6.0, labelpad=1.0)
ax.set_ylabel('power penalty $P_{\\rm eff}/P_{\\rm trig}$', fontsize=6.0,
              labelpad=1.5)
ax.tick_params(labelsize=5.4, length=2, pad=1.2)
ax.set_title('the resulting correction', fontsize=6.0, pad=3)

for a in axes:
    for sp in ('top', 'right'):
        a.spines[sp].set_visible(False)
fig.savefig('figures/hanning_response.pdf', bbox_inches='tight',
            pad_inches=0.03)
print('figures/hanning_response.pdf: penalty %.2f (centre) to %.2f (boundary),'
      ' median %.2f' % (pen[0], pen[-1], MEDFAC))
