#!/usr/bin/env python3
r"""make_fig_chain_v411.py -- Fig. 7 redrawn as a flowchart.

What it replaces, and why.  The figure that ships is a stack of shaded
rectangles with a dashed box of bullet points beside it: a text box with a
caption, not a diagram.  Worse, its third stage was the control rank, drawn as
a GATE -- 37 unattributed crossings in, 1 out -- when the paper's own Appendix B
says the rank has no calibrated false-alarm probability and is not used as
evidence for detection.  A reader following the arrows would conclude that 36
crossings were disposed of on a statistic the paper declines to interpret.

So the chain now has three stages and the rank is not one of them:

    crossings  ->  stellar-frame line attribution  ->  stellar-frame
                                                       recurrence

and the rank hangs off the side as what it is, a prioritisation note saying
which crossing was looked at first.  The visibility-fit bullets move out of the
drawing into Table~\ref{tab:visfit}, where the three different control counts
(512 image-plane positions, 8 with a retained dynamic spectrum, 12 reachable in
the visibilities) can be set beside each other instead of one of them floating
unlabelled inside a figure.

Every count is read: the ledger for the attribution split, round 120 for the
recurrence test.  Usage: make_fig_chain_v411.py [outdir]
"""
import glob
import json
import os
import re
import sys

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt                            # noqa: E402
from matplotlib.patches import FancyArrowPatch, FancyBboxPatch  # noqa: E402

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
OUTDIR = sys.argv[1] if len(sys.argv) > 1 else os.path.join(HERE, 'figures')
os.makedirs(OUTDIR, exist_ok=True)


def macro(name):
    pat = re.compile(r'\\(?:new|renew|provide)command\{\\%s\}'
                     r'\{((?:[^{}]|\{[^{}]*\})*?)\}' % name)
    v = None
    for fn in sorted(glob.glob(os.path.join(HERE, 'survey_numbers*.tex'))):
        for mm in pat.finditer(open(fn, encoding='utf-8').read()):
            if mm.group(1).strip():
                v = mm.group(1).strip()
    if v is None:
        raise SystemExit('macro %s not found; run recur_v411.py first' % name)
    return v


S = json.load(open(os.path.join(HERE, 'ledger.json')))['summary']
N_CROSS = S['n_crossings']
N_ATTR = S['n_attributed']
N_UNATTR = S['n_unattributed']
N_SCREEN = S['n_rank_flagged_unattributed']
N_TESTED = int(macro('RcNTested'))
N_UNTESTED = int(macro('RcNUntested'))
N_REPEAT = int(macro('RcNRepeatMeas'))
T_MAX = macro('RcTMax')
N_CTRL = int(macro('NCtrl'))
EXMIN = macro('RcExclMin')

# ★ the figure must not be able to disagree with the ledger it draws
assert N_ATTR + N_UNATTR == N_CROSS, (N_ATTR, N_UNATTR, N_CROSS)
assert N_TESTED + N_UNTESTED == N_UNATTR, (N_TESTED, N_UNTESTED, N_UNATTR)

STAGES = [
    ('Threshold crossings at the stellar position',
     r'$T_\star \geq 5$ in a searched window', N_CROSS),
    ('Unattributed',
     'no catalogued transition within $\\pm$%s km s$^{-1}$\nin the '
     "star's own frame" % macro('MaskVWidth'), N_UNATTR),
    ('Tested for recurrence',
     'stellar-frame cell, matched drift,\n%d covering repeat blocks'
     % N_REPEAT, N_TESTED),
    ('Confirmed', 'present again at the predicted cell', 0),
]
LEAVES = [
    '%d attributed to a catalogued transition' % N_ATTR,
    '%d discovery dynamic spectrum not retained' % N_UNTESTED,
    'none reaches the trigger: largest $T_\\star$ %s at any drift,\n'
    'weakest exclusion %s$\\sigma$' % (T_MAX, EXMIN),
]

fig = plt.figure(figsize=(3.4, 3.35))
ax = fig.add_axes([0.0, 0.0, 1.0, 1.0])
ax.set_xlim(0, 1)
ax.set_ylim(0, 1)
ax.axis('off')

LEFT, RIGHT = 0.045, 0.70       # the chain; the right margin holds the counts
TOP, BOT = 0.985, 0.195
H = 0.138
GAP = (TOP - BOT - len(STAGES) * H) / (len(STAGES) - 1)

for i, (title, sub, cnt) in enumerate(STAGES):
    y1 = TOP - i * (H + GAP)
    y0 = y1 - H
    ax.add_patch(FancyBboxPatch(
        (LEFT, y0), RIGHT - LEFT, H,
        boxstyle='round,pad=0.004,rounding_size=0.012',
        facecolor='0.96' if i else '0.90', edgecolor='0.35', lw=0.7, zorder=2))
    ax.text(LEFT + 0.022, y1 - 0.040, title, ha='left', va='center',
            fontsize=6.6, fontweight='bold', zorder=4)
    ax.text(LEFT + 0.022, y0 + 0.042, sub, ha='left', va='center',
            fontsize=5.1, color='0.3', zorder=4, linespacing=1.25)
    ax.text(RIGHT + 0.055, (y0 + y1) / 2, '%d' % cnt, ha='left', va='center',
            fontsize=12.5, fontweight='bold', color='0.1', zorder=4)
    if i < len(STAGES) - 1:
        xm = 0.5 * (LEFT + RIGHT) - 0.16
        ax.add_patch(FancyArrowPatch((xm, y0), (xm, y0 - GAP),
                                     arrowstyle='-|>', mutation_scale=7,
                                     color='0.25', lw=0.9, zorder=3))
        # what leaves the chain at this step, with its own small arrow
        ax.add_patch(FancyArrowPatch((xm, y0 - 0.45 * GAP),
                                     (xm + 0.085, y0 - 0.45 * GAP),
                                     arrowstyle='-|>', mutation_scale=5,
                                     color='0.55', lw=0.6, zorder=3))
        ax.text(xm + 0.098, y0 - 0.45 * GAP, LEAVES[i], ha='left',
                va='center', fontsize=5.0, color='0.4', zorder=4,
                linespacing=1.25)

# ---- the rank, as an annotation on the chain and not a step in it
ax.add_patch(FancyBboxPatch(
    (LEFT, 0.012), 1.0 - 2 * LEFT, 0.125,
    boxstyle='round,pad=0.004,rounding_size=0.012', facecolor='none',
    edgecolor='0.6', lw=0.6, ls=(0, (3, 2)), zorder=2))
ax.text(LEFT + 0.022, 0.075, 'The rank is a prioritisation note, not a step',
        ha='left', va='center', fontsize=5.6, fontstyle='italic',
        color='0.25', zorder=4)
ax.text(LEFT + 0.022, 0.036,
        '%d of the %d unattributed crossings outranks all %d control '
        'positions and was examined first.' % (N_SCREEN, N_UNATTR, N_CTRL),
        ha='left', va='center', fontsize=5.1, color='0.35', zorder=4)
_y = TOP - (H + GAP) - 0.5 * H
ax.add_patch(FancyArrowPatch((LEFT - 0.022, _y), (LEFT - 0.022, 0.075),
                             arrowstyle='-', linestyle=(0, (2, 2)),
                             color='0.6', lw=0.6, zorder=3))
ax.add_patch(FancyArrowPatch((LEFT - 0.022, 0.075), (LEFT - 0.004, 0.075),
                             arrowstyle='-|>', mutation_scale=5,
                             color='0.6', lw=0.6, zorder=3))

for ext in ('pdf', 'png'):
    fig.savefig(os.path.join(OUTDIR, 'chain_v411.' + ext),
                bbox_inches='tight', pad_inches=0.015)
print('figures/chain_v411.pdf: %d stages, %d -> %d -> %d -> 0, '
      '%d repeat-block measurements, rank shown as an annotation'
      % (len(STAGES), N_CROSS, N_UNATTR, N_TESTED, N_REPEAT))
