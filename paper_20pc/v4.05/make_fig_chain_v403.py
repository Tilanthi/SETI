#!/usr/bin/env python3
"""Draft replacement for the right-hand panel of Fig. 2 (the chain diagram).

DECISIONS_R7 A3 fixes the chain as

    crossing -> stellar-frame line attribution -> rank screen
             -> recurrence / block-versus-position

with the drift-following visibility fit reported ALONGSIDE as a position and
epoch consistency check, not as a step.  The panel v4.01 ships puts
"localised at the star in the visibilities" inside the funnel, between
attribution and confirmation, which asserts exactly what A2 withdraws: that
the fit filters.  It does not.  Under the adopted epoch every crossing
reaching Re/sigma >= 4 also clears the imaginary-part and control clauses
except one bright displaced source, and twelve controls resolve a rank of
about 1/13, so the third clause is passed by anything above ~2 sigma.

So the fit moves out of the column and into a box beside it, joined by a
dashed connector.  Nothing in the chain depends on it.

Every count is read from ledger_v403.json.  Usage:
    python3 make_fig_chain_v403.py [outdir]
"""
import glob
import json
import os
import sys

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt                         # noqa: E402
from matplotlib.patches import FancyArrowPatch, Rectangle   # noqa: E402

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
S = json.load(open(os.path.join(HERE, 'ledger_v403.json')))['summary']


def macro(name):
    """One generated macro, by name.  E[max of 12] is COMPUTED by
    epoch_v403.py and quoted in the prose; hard-coding it here made the
    figure disagree with the text in the second digit.  A figure that
    carries a number must read it from whoever owns it."""
    import re as _re
    for fn in sorted(glob.glob(os.path.join(HERE, 'survey_numbers*.tex'))):
        m = _re.search(r'\\newcommand\{\\%s\}\{(.*?)\}' % name,
                       open(fn, encoding='utf-8').read())
        if m:
            return m.group(1)
    raise SystemExit('macro %s not found; make_fig_chain_v403.py must run '
                     'AFTER the generator that writes it' % name)

# ---- the chain: label, survivors, what leaves at this step
STEPS = [
    ('Threshold crossings at the stellar position, $T_\\star\\geq5$',
     S['n_crossings'], None),
    ('Stellar-frame line attribution, $\\pm%.0f$ km s$^{-1}$ mask'
     % S['criterion']['mask_kms'],
     S['n_unattributed'],
     '%d attributed to a catalogued transition' % S['n_attributed']),
    ('Rank against all 512 spatial controls',
     S['n_unattr_screen'],
     '%d unattributed crossings below the screen'
     % (S['n_unattributed'] - S['n_unattr_screen'])),
    ('Recurrence and block-versus-position',
     S['n_confirmed'],
     'both evaluated, neither recurs; %d further crossings tested off-chain, '
     '%d repeat blocks in all, max $T_\\star$ %.2f against a trigger of 5'
     % (S['recurrence']['n_crossings_tested'] - S['n_unattr_screen']
        + S['n_recurrence_gap'],
        S['recurrence']['n_repeat_blocks'],
        S['recurrence']['max_T_over_repeats'])),
]

fig = plt.figure(figsize=(7.1, 2.55))
ax = fig.add_axes([0.0, 0.0, 1.0, 1.0])
ax.set_xlim(0, 1)
ax.set_ylim(0, 1)
ax.axis('off')

LEFT, RIGHT = 0.035, 0.605          # the chain column
top, bot = 0.90, 0.075
n = len(STEPS)
h = (top - bot) / n - 0.035
FILL = ['0.94', '0.90', '0.86', '0.80']

ax.text((LEFT + RIGHT) / 2, 0.965,
        'The chain that decides', ha='center', va='center', fontsize=7.6,
        fontstyle='italic')

for i, (lab, cnt, leaves) in enumerate(STEPS):
    y1 = top - i * (h + 0.035)
    y0 = y1 - h
    ax.add_patch(Rectangle((LEFT, y0), RIGHT - LEFT, h, facecolor=FILL[i],
                           edgecolor='0.4', lw=0.6, zorder=2))
    ax.text(LEFT + 0.012, (y0 + y1) / 2 + 0.035, lab, ha='left', va='center',
            fontsize=6.5, zorder=4)
    ax.text(RIGHT - 0.012, (y0 + y1) / 2 + 0.035, '%d' % cnt, ha='right',
            va='center', fontsize=9.5, fontweight='bold', zorder=4)
    if leaves:
        ax.text(LEFT + 0.012, (y0 + y1) / 2 - 0.045, leaves, ha='left',
                va='center', fontsize=5.5, color='0.35', zorder=4)
    if i < n - 1:
        ax.add_patch(FancyArrowPatch((0.16, y0), (0.16, y0 - 0.035),
                                     arrowstyle='-|>', mutation_scale=7,
                                     color='0.3', lw=0.8, zorder=3))

# the terminal statement, in counts rather than in a word
# ★ the terminal statement names its own gap: one of the two crossings
# entering the last step has no recurrence or second-epoch evidence yet, so
# "nothing survives" is not yet fully evidenced and the figure says so.
ax.text((LEFT + RIGHT) / 2, bot - 0.048,
        'no crossing tested survives the chain; %s (rank-flagged, '
        'unattributed) is still awaiting its recurrence test'
        % S['recurrence_gap'][0]['star'].replace('$', '')
        if S['n_recurrence_gap'] else
        'nothing survives the chain; no crossing is carried forward',
        ha='center', va='center', fontsize=5.8, color='0.25')

# ---- the consistency check, beside the chain and joined by a dashed line
SL, SR = 0.655, 0.985
sy1, sy0 = 0.900, 0.105
ax.add_patch(Rectangle((SL, sy0), SR - SL, sy1 - sy0, facecolor='none',
                       edgecolor='0.45', lw=0.7, ls=(0, (3, 2)), zorder=2))
ax.text((SL + SR) / 2, sy1 - 0.055,
        'Drift-following visibility fit', ha='center', va='center',
        fontsize=7.0, fontweight='bold')
ax.text((SL + SR) / 2, sy1 - 0.135,
        'a position-and-epoch consistency check,\nnot a filter in the chain',
        ha='center', va='center', fontsize=5.9, fontstyle='italic',
        color='0.3')
BULLETS = [
    '%d of %d crossings fitted, %d untested in %d blocks'
    % (S['n_fitted'], S['n_crossings'], S['n_untested'],
       len({u['eb'] for u in S['untested']})),
    'localised: %d under the committed epoch, %d under the adopted one'
    % (S['n_localised_committed'], S['n_localised_corrected']),
    '%d of those are unattributed, where v4.02 reported none'
    % S['n_localised_unattributed_corrected'],
    'clauses 2 and 3 reject %d of the %d reaching Re/$\\sigma\\geq$%.0f'
    % (S['clause_power']['corrected_rejected_by_clauses_2_3'],
       S['clause_power']['corrected_re_ge_4'], S['criterion']['re_min']),
    '%s controls resolve a rank of $\\sim$%s; E[max of %s] = %s'
    % (macro('EpNVisCtrl'), macro('EpVisRankRes'), macro('EpNVisCtrl'),
       macro('EpEmaxVis')),
    'a crossing is DEFINED by excess at this position and cell, so the',
    'fit confirms the search rather than testing it independently',
]
for j, b in enumerate(BULLETS):
    lead = '\u2022 ' if j < 5 else '   '
    ax.text(SL + 0.012, sy1 - 0.250 - j * 0.079, lead + b, ha='left',
            va='center', fontsize=5.5, color='0.15')

ax.add_patch(FancyArrowPatch((RIGHT + 0.004, 0.52), (SL - 0.004, 0.52),
                             arrowstyle='-', linestyle=(0, (2, 2)),
                             color='0.5', lw=0.8, zorder=3))
ax.text((RIGHT + SL) / 2, 0.555, 'reported\nalongside', ha='center',
        va='bottom', fontsize=5.2, color='0.45')

for ext in ('pdf', 'png'):
    fig.savefig(os.path.join(OUT, 'chain_v403.' + ext), bbox_inches='tight',
                pad_inches=0.015)
print('figures/chain_v403.pdf written: %d chain steps, terminal count %d'
      % (n, STEPS[-1][1]))
