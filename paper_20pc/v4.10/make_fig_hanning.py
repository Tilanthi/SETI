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

# v4.10 (figures): the panels now carry the MEASURED response, not a 3-tap
# linear-split toy.  The toy gave 50/44/38 per cent and a penalty running to
# 2.67, while the macros the caption prints -- \HanBest 0.50, \HanMed 0.48,
# \HanWorst 0.42, \HanFacMed 2.08 -- come from the Dirichlet response in
# cresp_v401.json.  The caption therefore said "\HanWorst on a boundary"
# directly above a panel that said 38 per cent.  Same source as v342_calc.py
# now, and asserted against the macros below.
import json as _json
_CR = _json.load(open('cresp_v401.json'))
PHI = np.array(_CR['phi'])            # sub-channel offset, 0 to 0.5
RHO = np.array(_CR['rho_n1'])         # fraction of the carrier in the peak channel


def rho_of(offset):
    """Measured peak-channel fraction at `offset` channels from a centre."""
    return float(np.interp(abs(offset), PHI, RHO))


def smoothed(offset, n=9):
    """Channel values for an unresolved carrier `offset` channels from the
    centre of channel n//2.  The peak channel holds the measured fraction and
    Hanning's two neighbours share the rest, which is exactly the three-tap
    structure the smoothing has; only the offset dependence of the peak is
    taken from the measurement rather than from a linear split."""
    y = np.zeros(n)
    i = n // 2
    r = rho_of(offset)
    y[i] = r
    y[i - 1] = y[i + 1] = 0.5 * (1.0 - r)
    return y


fig, axes = plt.subplots(1, 4, figsize=(7.1, 1.85),
                         gridspec_kw=dict(width_ratios=[1, 1, 1, 1.15],
                                          wspace=0.33))
cases = [(0.0, 'at channel centre', BEST),
         (0.25, 'quarter channel off', float(texval('HanMed'))),
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
    # the panel may not print a fraction the manuscript does not have
    assert frac is None or abs(peak - frac) < 0.005, (
        'panel "%s" draws %.3f where the caption prints %.2f' % (lab, peak, frac))
axes[0].set_ylabel('fraction of carrier\npower in channel', fontsize=6.0,
                   labelpad=1.5)

# the penalty as a function of offset
ax = axes[3]
offs = np.linspace(0, 0.5, 101)
pen = np.array([1.0 / rho_of(o) for o in offs])
# The curve's endpoints and median are \HanFacBest, \HanFacWorst and
# \HanFacMed.  Compared at the macros' own precision -- two decimals, so half
# a unit in the last digit -- not at a tolerance tighter than the number.
for _got, _name in ((pen[0], 'HanFacBest'), (pen[-1], 'HanFacWorst'),
                    (float(np.median(pen)), 'HanFacMed')):
    _want = float(texval(_name))
    assert abs(_got - _want) < 0.005, (
        'the penalty curve gives %.3f where \\%s is %.2f'
        % (_got, _name, _want))
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
