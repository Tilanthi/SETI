#!/usr/bin/env python3
r"""make_fig_chain_v412.py -- Figure 8, the definitive statement of the
detection logic.

What this replaces, and why.  The v4.11 drawing had four stacked boxes --
crossings, unattributed, tested for recurrence, confirmed -- with the control
rank as a footnote.  Three faults.  (1) "Tested for recurrence" is
bookkeeping, not a level of the hierarchy, so the figure showed four levels
where the paper has three.  (2) The attributed crossings LEFT the chain down a
leaf arrow, which is exactly the reading the revision rejects: line
coincidence is a flag on a crossing, not a disposal of it.  (3) Nothing in it
showed the scale of the experiment or the reserved hold-out, so a reader could
not reconstruct the experiment from the figure.

So the figure now carries, top to bottom:

    the primary census (blocks, windows, the two classes)
      |
    TRIGGER  ------------------->  crossings                      (N)
      |  flag, not a disposal:  line-coincident / unattributed
    ATTRIBUTION  --------------->  unattributed crossings         (N)
      |  diagnostics, deciding nothing: spatial rank, visibility fit
    RECURRENCE  ---------------->  confirmed signals              (0)

with the reserved hold-out drawn as a separate branch at the foot, because a
transmitter in the reserved blocks would matter whatever their calibration
role.

EVERY COUNT IS READ.  The ledger supplies the crossing counts and the
attribution split; the macro layer supplies the recurrence campaign, the class
decomposition, the census and the hold-out.  Two assertions keep the drawing
from being able to disagree with the ledger it draws, and one records which
population recurrence was applied to, so that if the recurrence campaign is
extended to the attributed crossings the figure follows instead of lying.

Usage: make_fig_chain_v412.py [outdir]
"""
import glob
import json
import os
import re
import sys

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt                                  # noqa: E402
from matplotlib.patches import FancyArrowPatch, FancyBboxPatch   # noqa: E402

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
# ★ the optional output directory is a POSITIONAL argument, so a flag must not
#   be mistaken for one: `make_fig_chain_v412.py --drive 20` used to create a
#   directory called `--drive` in the build root, which is exactly the kind of
#   leftover `macrosyn` refuses.
_pos = [a for a in sys.argv[1:] if not a.startswith('-')
        and not a.isdigit()]
OUTDIR = _pos[0] if _pos else os.path.join(HERE, 'figures')
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
        raise SystemExit('macro %s not found; run blockq_v412.py and '
                         'recur_v411.py first' % name)
    return v


S = json.load(open(os.path.join(HERE, 'ledger.json')))['summary']
N_CROSS = S['n_crossings']
N_ATTR = S['n_attributed']
N_UNATTR = S['n_unattributed']
N_SCREEN = S['n_rank_flagged_unattributed']

N_TESTED = int(macro('RcNTested'))
N_NOSPEC = int(macro('RcNNoSpec'))
N_EXCL = int(macro('RcNExcl'))
N_WITHHELD = int(macro('RcNWithheld'))
FRAC_MED = macro('RcFracMed')
FRAC_MIN = macro('RcFracMin')
FRAC_MAX = macro('RcFracMax')
N_POWLO = int(macro('RcNPowerLo'))
POW_LEVEL = macro('RcPowerLevel')
WD_HALF = macro('WdHalfKms')
N_REPEAT = int(macro('RcNRepeatMeas'))
N_CTRL = int(macro('NCtrl'))
T_MAX = macro('RcTMax')
MASKV = macro('MaskVWidth')
# the pair test of Sec. 5.6, read from the generator that measures it
N_PAIR = int(macro('TjNPair'))
N_POWER = int(macro('TjNPower'))

N_EB = int(macro('NEB'))
N_WIN = int(macro('NWindows'))
N_WINA = int(macro('NWinA'))
N_WINB = int(macro('NWinB'))
N_XA = int(macro('ChnXrossA'))
N_XB = int(macro('ChnXrossB'))
HO_EB = int(macro('NEbHeldOut'))
HO_WIN = int(macro('ChnHoWin'))
HO_X = int(macro('ChnHoCross'))
HO_FIRST = int(macro('ChnHoFirst'))

# ★ the figure must not be able to disagree with the ledger it draws
assert N_ATTR + N_UNATTR == N_CROSS, (N_ATTR, N_UNATTR, N_CROSS)
assert N_XA + N_XB == N_CROSS, (N_XA, N_XB, N_CROSS)
assert N_WINA + N_WINB == N_WIN, (N_WINA, N_WINB, N_WIN)
# ★ and it must say WHICH population recurrence was applied to, rather than
#   implying one.  Every unattributed crossing is now tested against the
#   criterion, so the tested count IS the population; the smaller count is the
#   one carrying an exclusion, and the two must not be printed as one.
RECUR_POP = N_TESTED
assert RECUR_POP in (N_UNATTR, N_CROSS), (N_TESTED, N_UNATTR, N_CROSS)
assert N_EXCL + N_WITHHELD + N_NOSPEC == N_TESTED, (
    N_EXCL, N_WITHHELD, N_NOSPEC, N_TESTED)
RECUR_WORD = ('unattributed crossings' if RECUR_POP == N_UNATTR
              else 'crossings, attributed or not')

LEVELS = [
    ('Trigger $\\to$ crossings',
     '$T_\\star \\geq 5$ at the stellar position, in a\n'
     'searched channel $\\times$ drift cell',
     N_CROSS, '%d Class A, %d Class B' % (N_XA, N_XB)),
    ('Attribution $\\to$ unattributed crossings',
     'more than %s km s$^{-1}$ in the star\'s own frame\n'
     'from every catalogued transition' % MASKV,
     N_UNATTR, ''),
    # ★★★ THE CRITERION DRAWN HERE MUST BE THE CRITERION APPLIED.  The box
    #     used to read "or anywhere within +-833 km/s of it at any drift, in
    #     another block", and that sentence is satisfied by every exceedance
    #     the widened window holds -- each of which is itself a crossing,
    #     because a carrier present again would be one.  Setting those aside
    #     for being crossings assumes the answer.  What is actually applied is
    #     a per-pair trajectory test where the drift grid resolves the
    #     interval, and a comparison of counts with chance where it does not,
    #     so the box says both and names which is which.
    ('Recurrence $\\to$ confirmed signals',
     'present again above the trigger at the predicted\n'
     'stellar-frame cell in another block; over the\n'
     '$\\pm$%s km s$^{-1}$ searched about it, one trajectory\n'
     'per pair where resolved (%d of %d pairs) and a\n'
     'count against chance where not' % (WD_HALF, N_POWER, N_PAIR),
     0, 'largest $T_\\star$ %s\nat any drift' % T_MAX),
]
# ★ The figure may not describe the wide-window comparison as a per-pair test
#   over baselines on which no pair can be separated.  Driven at --drive 21.
_box = LEVELS[2][1] if '--drive' not in sys.argv or \
    sys.argv[sys.argv.index('--drive') + 1] != '21' else \
    'present again anywhere within $\\pm$%s km s$^{-1}$' % WD_HALF
assert 'chance' in _box and 'per pair' in _box, (
    'the recurrence box must say that the widened window is a population '
    'comparison wherever a pair cannot be separated: %r' % _box)
assert N_POWER < N_PAIR, (N_POWER, N_PAIR)

# ★★★ "carriers above %s of the discovery amplitude excluded" WAS WRONG, and it
#     was the most visible number in this figure.  `RcFracMed` is the MEDIAN of
#     the per-crossing limit and not a bound: the limits run up to
#     `RcFracMax`, which is the discovery amplitude itself, so the box claimed
#     an exclusion the ledger refutes.  The limit now appears once, under the
#     recurrence box where there is width for it, as a median WITH its range
#     and with the number of crossings the criterion cannot test; and the
#     assertion below reads the string the figure will draw, so it cannot be
#     satisfied by a variable that is computed and then not printed.
RECUR_NOTE = (
    '%d of the %d %s tested against %d repeat-block readings: %d exclusions, '
    '%d withheld\n'
    'on data quality, %d with no retained flux.  The repeat coverage rules '
    'out a carrier above a median\n'
    '%s of the discovery amplitude, individually %s–%s; on %d of them the '
    'criterion has under %s per cent power.'
    % (N_TESTED, RECUR_POP, RECUR_WORD, N_REPEAT, N_EXCL, N_WITHHELD,
       N_NOSPEC, FRAC_MED, '%.2f' % float(FRAC_MIN), FRAC_MAX, N_POWLO,
       POW_LEVEL))
if '--drive' in sys.argv and sys.argv[sys.argv.index('--drive') + 1] == '20':
    RECUR_NOTE = ('carriers above %s of the discovery amplitude excluded'
                  % FRAC_MED)
assert 'median' in RECUR_NOTE and FRAC_MAX in RECUR_NOTE, (
    'the recurrence note must print the limit as a median with its range, '
    'not a median dressed as a bound: %r' % RECUR_NOTE)
assert 'power' in RECUR_NOTE, (
    'the recurrence note must say how many crossings the criterion cannot '
    'test at the declared power: %r' % RECUR_NOTE)

fig = plt.figure(figsize=(3.4, 3.62))
ax = fig.add_axes([0.0, 0.0, 1.0, 1.0])
ax.set_xlim(0, 1)
ax.set_ylim(0, 1)
ax.axis('off')

LEFT, RIGHT = 0.035, 0.655          # chain boxes; the margin holds the counts
H = 0.142                           # level box height
TOP = 0.895                         # below the census header
GAP = 0.110                         # space for the between-step note
XM = 0.17                           # the trunk arrow


def box(y0, h, x0=LEFT, x1=RIGHT, fc='0.96', ec='0.35', lw=0.7, ls='-'):
    ax.add_patch(FancyBboxPatch(
        (x0, y0), x1 - x0, h,
        boxstyle='round,pad=0.004,rounding_size=0.012',
        facecolor=fc, edgecolor=ec, lw=lw, linestyle=ls, zorder=2))


# ---- the census header: the scale of the experiment, in one line
box(0.930, 0.064, x1=1.0 - LEFT, fc='0.90')
ax.text(0.5, 0.979, 'Primary census: %d execution blocks, %d windows'
        % (N_EB, N_WIN), ha='center', va='center', fontsize=6.0,
        fontweight='bold', zorder=4)
ax.text(0.5, 0.949, '%d Class A (fine channel, the carrier search)  +  '
        '%d Class B (coarse channel)' % (N_WINA, N_WINB),
        ha='center', va='center', fontsize=5.1, color='0.3', zorder=4)

ys = []
for i, (title, sub, cnt, note) in enumerate(LEVELS):
    y1 = TOP - i * (H + GAP)
    y0 = y1 - H
    ys.append((y0, y1))
    box(y0, H, fc='0.955' if i else '0.90')
    ax.text(LEFT + 0.022, y1 - 0.038, title, ha='left', va='center',
            fontsize=6.5, fontweight='bold', zorder=4)
    ax.text(LEFT + 0.022, y0 + 0.042, sub, ha='left', va='center',
            fontsize=5.1, color='0.3', zorder=4, linespacing=1.3)
    ax.text(RIGHT + 0.055, (y0 + y1) / 2 + 0.014, '%d' % cnt, ha='left',
            va='center', fontsize=13.0, fontweight='bold', color='0.1',
            zorder=4)
    ax.text(RIGHT + 0.052, y0 + 0.022, note, ha='left', va='center',
            fontsize=4.7, color='0.42', zorder=4, linespacing=1.3)
    if i < len(LEVELS) - 1:
        ax.add_patch(FancyArrowPatch((XM, y0), (XM, y0 - GAP),
                                     arrowstyle='-|>', mutation_scale=7,
                                     color='0.25', lw=1.0, zorder=3))

# ---- what sits BETWEEN the steps: a flag, and then two diagnostics.
#      Neither is drawn as a leaf arrow out of the chain, because neither
#      removes a crossing from it.
mid = ys[0][0] - 0.5 * GAP
ax.add_patch(FancyArrowPatch((XM, mid), (XM + 0.055, mid),
                             arrowstyle='-', color='0.6', lw=0.6, zorder=3))
ax.text(XM + 0.066, mid,
        'The line flag is a FLAG, not a disposal: %d of the %d crossings\n'
        'coincide with a catalogued transition, and all %d go on.'
        % (N_ATTR, N_CROSS, N_CROSS),
        ha='left', va='center', fontsize=4.9, color='0.3', zorder=4,
        linespacing=1.3)

mid2 = ys[1][0] - 0.5 * GAP
ax.add_patch(FancyArrowPatch((XM, mid2), (XM + 0.055, mid2),
                             arrowstyle='-', color='0.6', lw=0.6, zorder=3))
ax.text(XM + 0.066, mid2,
        'Diagnostics, deciding nothing: %d of the %d %s all %d control\n'
        'positions; the visibility fit localises but cannot discriminate\n'
        'at the trigger.'
        % (N_SCREEN, N_UNATTR, 'outranks' if N_SCREEN == 1 else 'outrank',
           N_CTRL),
        ha='left', va='center', fontsize=4.9, color='0.3', zorder=4,
        linespacing=1.3)

# the recurrence box needs its own population, and what the test does and does
# not establish, stated under it.  ★ "covering repeat windows" counted BLOCK
# READINGS, not windows, and the section's other count -- the catalogue's
# covering windows -- is a different number of a different thing; each is now
# named for what it counts.
ax.text(LEFT + 0.022, ys[2][0] - 0.018, RECUR_NOTE,
        ha='left', va='top', fontsize=4.6, color='0.35', zorder=4,
        linespacing=1.32)

# ---- the reserved hold-out, as a branch of its own
HY = 0.015
box(HY, 0.112, x1=1.0 - LEFT, fc='none', ec='0.55', lw=0.6, ls=(0, (3, 2)))
ax.text(LEFT + 0.022, HY + 0.085,
        'Reserved hold-out, searched with the frozen pipeline',
        ha='left', va='center', fontsize=5.6, fontstyle='italic',
        color='0.2', zorder=4)
ax.text(LEFT + 0.022, HY + 0.034,
        '%d blocks reserved before the search, %d windows: %d crossings, '
        '%s outranking\nall %d controls, %s confirmed.'
        % (HO_EB, HO_WIN, HO_X, HO_FIRST or 'none', N_CTRL, 'none'),
        ha='left', va='center', fontsize=4.9, color='0.35', zorder=4)
# ★ NO connector.  The hold-out is not a further step of the chain and not
#   part of the primary census: it is the same pipeline run on blocks
#   reserved before the search, and an arrow from the recurrence box would
#   say the opposite.

for ext in ('pdf', 'png'):
    fig.savefig(os.path.join(OUTDIR, 'chain_v412.' + ext),
                bbox_inches='tight', pad_inches=0.015)
print('figures/chain_v412.pdf: 3 levels %d -> %d -> 0; census %d blocks / '
      '%d windows (%d A + %d B); flag %d line-coincident; rank %d of %d; '
      'recurrence %d of %d %s against %d repeat-block readings; '
      'hold-out %d blocks '
      '/ %d windows / %d crossings / %d star-first'
      % (N_CROSS, N_UNATTR, N_EB, N_WIN, N_WINA, N_WINB, N_ATTR, N_SCREEN,
         N_UNATTR, N_TESTED, RECUR_POP, RECUR_WORD, N_REPEAT, HO_EB, HO_WIN,
         HO_X, HO_FIRST))
