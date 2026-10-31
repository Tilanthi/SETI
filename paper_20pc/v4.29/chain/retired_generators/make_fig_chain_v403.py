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
# ★ The chain reads the ADOPTED ledger.  It used to read the one keyed to
# the superseded statistic, which is why it printed the sky-frame
# attribution count under a stellar-frame heading: the figure was
# self-consistent with a table the paper no longer publishes.  The
# superseded summary is still read for the counts the adopted one does not
# carry (the fit coverage and the recurrence campaign), and those are
# asserted to be about the same number of crossings.
S = json.load(open(os.path.join(HERE, 'ledger.json')))['summary']
_OLD = json.load(open(os.path.join(HERE, 'ledger_v403.json')))['summary']
assert _OLD['n_crossings'] == S['n_crossings'], (
    'the fit-coverage and recurrence counts are taken from a ledger with a '
    'different number of crossings (%d against %d), so they cannot be '
    'printed on this chain' % (_OLD['n_crossings'], S['n_crossings']))
# ★★ (figures, v4.10) THE COUNT CHECK ABOVE PASSES ON A SET THAT DIFFERS.
# Both ledgers hold 56 crossings, but four fell and four were added, so only
# — measured here, not assumed — 47 of the 56 are the same crossing.  An
# assertion on the COUNT therefore cannot fail where it matters, which is the
# defect family this project has now found fifteen times.  The fit and
# recurrence bullets are measured on the released list; the box says so
# instead of letting a reader attach them to the adopted chain.
def _key(r):
    """(execution block, band, crossing frequency).  NOT the star name: the
    two ledgers spell one star differently ('HR 1010' against 'HR 1010 Gaia
    DR3 4722135642226902656'), and a name-keyed join is the defect family this
    project has found thirteen times."""
    f = r.get('freq')
    if f is None:
        f = r.get('freq_shown')
    return (r['eb'], str(r.get('band')),
            None if f is None else round(float(f), 4))


def _overlap(new_rows, old_rows):
    """How many of the two ledgers' crossings are the same crossing.

    Five released rows carry freq = null, so an exact key would call them
    different crossings and overstate the difference by five.  Those fall back
    to (block, band), which is accepted only where it is unique on both sides.
    """
    A = {_key(r): r for r in new_rows}
    B = {_key(r): r for r in old_rows}
    common = set(A) & set(B)
    rest_a = {k: v for k, v in A.items() if k not in common}
    rest_b = {k: v for k, v in B.items() if k not in common}
    n = len(common)
    for ka, _ in rest_a.items():
        cand = [kb for kb in rest_b if kb[:2] == ka[:2]]
        same_a = [k2 for k2 in rest_a if k2[:2] == ka[:2]]
        if len(cand) == 1 and len(same_a) == 1:
            n += 1
    return n


_NEWROWS = json.load(open(os.path.join(HERE, 'ledger.json')))['rows']
_OLDROWS = json.load(open(os.path.join(HERE, 'ledger_v403.json')))['rows']
N_COMMON = _overlap(_NEWROWS, _OLDROWS)
# ★ The real cross-check: the two ledgers must differ by exactly the declared
# delta.  Equality of COUNTS -- which is what the check above tests -- passes
# even though four crossings fell and four different ones were added, so it
# cannot fail where it matters.  This one can.
_D = S['delta']
assert (N_COMMON == S['n_crossings'] - _D['added']
        and N_COMMON == len(_OLDROWS) - _D['fell']), (
    'the two ledgers share %d crossings, which is not %d - %d added nor '
    '%d - %d fallen: the fit and recurrence counts cannot be printed on this '
    'chain' % (N_COMMON, S['n_crossings'], _D['added'], len(_OLDROWS),
               _D['fell']))
SETS_AGREE = N_COMMON == S['n_crossings']

S = dict(_OLD, **S)
S['n_unattr_screen'] = S['n_rank_flagged_unattributed']


def macro(name):
    """One generated macro, by name.  E[max of 12] is COMPUTED by
    epoch_v403.py and quoted in the prose; hard-coding it here made the
    figure disagree with the text in the second digit.  A figure that
    carries a number must read it from whoever owns it."""
    import re as _re
    # v4.10: LAST definition, across new/renew/providecommand, following
    # round 103's aliases.  The previous reader matched \\newcommand only and
    # took the FIRST file, so a macro that round 103 retires by aliasing it to
    # its replacement would have been read at its superseded value -- the same
    # defect that let make_fig_classa_sens.py draw a withdrawn band.
    pat = _re.compile(r'\\(?:new|renew|provide)command\{\\%s\}'
                      r'\{((?:[^{}]|\{[^{}]*\})*?)\}' % name)
    out = None
    for fn in sorted(glob.glob(os.path.join(HERE, 'survey_numbers*.tex'))):
        for m in pat.finditer(open(fn, encoding='utf-8').read()):
            if m.group(1).strip():
                out = m.group(1).strip()
    seen = set()
    while out and _re.fullmatch(r'\\[A-Za-z]+', out) and out not in seen:
        seen.add(out)
        out = macro(out[1:])
    if out is None:
        raise SystemExit('macro %s not found; make_fig_chain_v403.py must run '
                         'AFTER the generator that writes it' % name)
    return out

# v4.10 (figures): the mask half-width and the control count are drawn from
# the ledger json, while the caption and the prose quote \MaskVWidth and
# \NCtrl.  Nothing compared them.  They are compared here, and the panel now
# prints the macro values, so the figure cannot carry a criterion the text
# does not state.
MASK_KMS = float(macro('MaskVWidth'))
N_CTRL = int(macro('NCtrl'))
for _src, _got in (('the adopted ledger', S['mask_half_kms']),
                   ('the superseded ledger', S['criterion']['mask_kms'])):
    assert abs(_got - MASK_KMS) < 1e-9, (
        '%s was built with a +-%g km/s mask but the manuscript says +-%g '
        '(\\MaskVWidth)' % (_src, _got, MASK_KMS))

# ---- the chain: label, survivors, what leaves at this step
STEPS = [
    ('Threshold crossings at the stellar position, $T_\\star\\geq5$',
     S['n_crossings'], None),
    ('Stellar-frame line attribution, $\\pm%.0f$ km s$^{-1}$ mask'
     % MASK_KMS,
     S['n_unattributed'],
     '%d attributed to a catalogued transition' % S['n_attributed']),
    ('Rank against all %d spatial controls' % N_CTRL,
     S['n_unattr_screen'],
     '%d unattributed crossings below the screen'
     % (S['n_unattributed'] - S['n_unattr_screen'])),
    ('Recurrence and block-versus-position',
     S['n_confirmed'],
     'both evaluated, neither recurs; %d further crossings tested\n'
     'off-chain, %d repeat blocks in all, max $T_\\star$ %.2f'
     % (S['recurrence']['n_crossings_tested'] - S['n_unattr_screen']
        + S['n_recurrence_gap'],
        S['recurrence']['n_repeat_blocks'],
        S['recurrence']['max_T_over_repeats'])),
]

# ★ v4.10 (figures): SINGLE-COLUMN geometry.  Sec. 5 measured 6.0 pp with
# three full-width floats against 2.90 pp of prose -- the overage was float
# packing, not words -- and this float in a column saves exactly 1.0 pp.  The
# chain is a vertical sequence, so a column is the right shape for it; the
# visibility fit, which is not a step in the chain, moves from beside the
# chain to below it and keeps its dashed border and its connector.
fig = plt.figure(figsize=(3.4, 4.8))
ax = fig.add_axes([0.0, 0.0, 1.0, 1.0])
ax.set_xlim(0, 1)
ax.set_ylim(0, 1)
ax.axis('off')

LEFT, RIGHT = 0.025, 0.975          # the chain spans the column
top, bot = 0.945, 0.505
n = len(STEPS)
GAP = 0.024
h = (top - bot) / n - GAP
FILL = ['0.94', '0.90', '0.86', '0.80']

ax.text((LEFT + RIGHT) / 2, 0.985,
        'The chain that decides', ha='center', va='center', fontsize=7.6,
        fontstyle='italic')

for i, (lab, cnt, leaves) in enumerate(STEPS):
    y1 = top - i * (h + GAP)
    y0 = y1 - h
    ax.add_patch(Rectangle((LEFT, y0), RIGHT - LEFT, h, facecolor=FILL[i],
                           edgecolor='0.4', lw=0.6, zorder=2))
    ax.text(LEFT + 0.018, (y0 + y1) / 2 + (0.020 if leaves else 0.0), lab,
            ha='left', va='center', fontsize=6.0, zorder=4,
            wrap=False)
    ax.text(RIGHT - 0.018, (y0 + y1) / 2 + (0.020 if leaves else 0.0),
            '%d' % cnt, ha='right', va='center', fontsize=9.0,
            fontweight='bold', zorder=4)
    if leaves:
        ax.text(LEFT + 0.018, (y0 + y1) / 2 - 0.028, leaves, ha='left',
                va='center', fontsize=5.0, color='0.35', zorder=4)
    if i < n - 1:
        ax.add_patch(FancyArrowPatch((0.11, y0), (0.11, y0 - GAP),
                                     arrowstyle='-|>', mutation_scale=6,
                                     color='0.3', lw=0.8, zorder=3))

# the terminal statement, in counts rather than in a word
# ★ the terminal statement names its own gap: one of the two crossings
# entering the last step has no recurrence or second-epoch evidence yet, so
# "nothing survives" is not yet fully evidenced and the figure says so.
ax.text((LEFT + RIGHT) / 2, bot - 0.028,
        'no crossing tested survives the chain; %s (rank-flagged, '
        'unattributed) is still awaiting its recurrence test'
        % S['recurrence_gap'][0]['star'].replace('$', '')
        if S['n_recurrence_gap'] else
        'nothing survives the chain; no crossing is carried forward',
        ha='center', va='center', fontsize=5.3, color='0.25')

# ---- the consistency check, BELOW the chain and joined by a dashed line
SL, SR = 0.025, 0.975
sy1, sy0 = 0.405, 0.030
ax.add_patch(Rectangle((SL, sy0), SR - SL, sy1 - sy0, facecolor='none',
                       edgecolor='0.45', lw=0.7, ls=(0, (3, 2)), zorder=2))
ax.text((SL + SR) / 2, sy1 - 0.030,
        'Drift-following visibility fit', ha='center', va='center',
        fontsize=6.6, fontweight='bold')
ax.text((SL + SR) / 2, sy1 - 0.064,
        'a position-and-epoch consistency check, not a filter in the chain',
        ha='center', va='center', fontsize=5.3, fontstyle='italic',
        color='0.3')
BULLETS = ([] if SETS_AGREE else [
    'measured on the released crossing list, of which %d of the %d\nabove '
    'are the same crossing:' % (N_COMMON, S['n_crossings']),
]) + [
    '%d of %d crossings fitted, %d untested in %d blocks'
    % (S['n_fitted'], S['n_crossings'], S['n_untested'],
       len({u['eb'] for u in S['untested']})),
    # one epoch convention: the adopted one.  Naming the other is a record
    # of how the analysis changed, not a property of the analysis.
    'localised at the stellar position: %d'
    % S['n_localised_corrected'],
    # ★ the trailing clause here was a comparison with an earlier version of
    # this paper, printed INTO the figure, where no prose gate can see it.
    '%d of those are unattributed'
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
_SCOPE = 0 if SETS_AGREE else 1          # the scope line, if present
for j, b in enumerate(BULLETS):
    lead = '   ' if (j < _SCOPE or j >= _SCOPE + 5) else '\u2022 '
    ax.text(SL + 0.016, sy1 - 0.094 - j * 0.0365, lead + b, ha='left',
            va='center', fontsize=5.2,
            color='0.35' if j < _SCOPE else '0.15',
            fontstyle='italic' if j < _SCOPE else 'normal')

_cy0, _cy1 = sy1 + 0.004, bot - 0.062
ax.add_patch(FancyArrowPatch((0.30, _cy1), (0.30, _cy0),
                             arrowstyle='-', linestyle=(0, (2, 2)),
                             color='0.5', lw=0.8, zorder=3))
ax.text(0.325, 0.5 * (_cy0 + _cy1), 'reported alongside', ha='left',
        va='center', fontsize=5.0, color='0.45')

for ext in ('pdf', 'png'):
    fig.savefig(os.path.join(OUT, 'chain_v403.' + ext), bbox_inches='tight',
                pad_inches=0.015)
print('figures/chain_v403.pdf written: %d chain steps, terminal count %d'
      % (n, STEPS[-1][1]))
