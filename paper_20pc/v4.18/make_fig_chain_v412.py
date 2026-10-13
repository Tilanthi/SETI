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
# ★★★ r16: THIS WAS `RcNPowerLo` = 4, THE COUNT AT THE DISCOVERY AMPLITUDE,
# while Sec. 5.6 and Conclusion 5 now quote the count at the TRIGGER
# amplitude, `RcNPowerLoTrig` = 7 (Ruling 4 / R2b-4: our own appendix says the
# discovery amplitude is biased high, so the honest power is
# Phi(5 T_pers/T_star - 5)).  The figure would have labelled 4 untested
# crossings beside a text that says 7.  ★ Nothing could have caught it:
# `retire_macros.py` PROTECTS a macro a generator reads by name, so dropping
# the last prose citation of `\RcNPowerLo` kept the macro alive here instead
# of reporting that it had been superseded.  Protection hides an
# inconsistency rather than finding it, which is why the clause below asserts
# the partition rather than trusting the name.
N_POWLO = int(macro('RcNPowerLoTrig'))
# the figure's count is the published partition of the exclusions, not a
# third number: low-power + high-power == exclusions tested.
assert N_POWLO + int(macro('RqNPowerHi')) == int(macro('RcNExcl')), (
    'the chain figure would print %d low-power crossings against %s '
    'exclusions and %s above the level'
    % (N_POWLO, macro('RcNExcl'), macro('RqNPowerHi')))
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
#   implying one.  The population is the unattributed crossings; the count the
#   box may call TESTED is the smaller one that carries a repeat reading, and
#   the two must not be printed as one.
RECUR_POP = N_TESTED
assert RECUR_POP in (N_UNATTR, N_CROSS), (N_TESTED, N_UNATTR, N_CROSS)
assert N_EXCL + N_WITHHELD + N_NOSPEC == N_TESTED, (
    N_EXCL, N_WITHHELD, N_NOSPEC, N_TESTED)
# ★★★★ AND THE TESTED COUNT IS NOT THE POPULATION.  The box said "38 of the 38
#   unattributed crossings tested against 444 repeat-block readings", and the
#   444 are summed over the 37 that carry one: the crossing whose discovery
#   spectrum was not retained has no repeat record anywhere, which is why the
#   ledger prints em-dashes for it.  A figure may not report a test for a row
#   that carries no result.  `RcNExclPoss` is the count that does, and the
#   partition is asserted here rather than remembered.
N_WITHREAD = int(macro('RcNExclPoss'))
assert N_WITHREAD + N_NOSPEC == N_TESTED and N_EXCL + N_WITHHELD == N_WITHREAD, (
    'the chain figure would print %d crossings carrying a reading against '
    '%d exclusions + %d withheld, out of %d with %d retaining no spectrum'
    % (N_WITHREAD, N_EXCL, N_WITHHELD, N_TESTED, N_NOSPEC))
RECUR_WORD = ('unattributed crossings' if RECUR_POP == N_UNATTR
              else 'crossings, attributed or not')

LEVELS = [
    ('Trigger $\\to$ crossings',
     '$T_\\star \\geq 5$ at the stellar position, in a\n'
     'searched channel $\\times$ drift cell',
     N_CROSS, '%d Class A, %d Class B' % (N_XA, N_XB)),
    ('Attribution $\\to$ unattributed crossings',
     # ★ "from every CATALOGUED transition" is the claim Fig. B1's caption
     #   carried and lost: a crossing 3800 km/s from the mask is 0.1 km/s
     #   from a catalogued line of some carrier, and these boxes must state
     #   the criterion that is applied, which is the twelve-species mask.
     'more than %s km s$^{-1}$ in the star\'s own frame\n'
     'from every transition of the line mask' % MASKV,
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
    '%d of the %d %s tested against %d repeat-block readings: %d exclusions '
    'and %d withheld\n'
    'on data quality; %d retains no flux to transport.  The repeat '
    'coverage rules out a\n'
    'carrier above a median %s of the discovery amplitude, individually '
    '%s–%s; on %d of them\n'
    'the criterion has under %s per cent power.'
    % (N_WITHREAD, RECUR_POP, RECUR_WORD, N_REPEAT, N_EXCL, N_WITHHELD,
       N_NOSPEC, FRAC_MED, '%.2f' % float(FRAC_MIN), FRAC_MAX, N_POWLO,
       POW_LEVEL))
if '--drive' in sys.argv and sys.argv[sys.argv.index('--drive') + 1] == '20':
    RECUR_NOTE = ('carriers above %s of the discovery amplitude excluded'
                  % FRAC_MED)
if '--drive' in sys.argv and sys.argv[sys.argv.index('--drive') + 1] == '26':
    # the defect, restored: the whole population reported as tested
    RECUR_NOTE = RECUR_NOTE.replace('%d of the %d' % (N_WITHREAD, RECUR_POP),
                                    '%d of the %d' % (RECUR_POP, RECUR_POP), 1)
assert 'median' in RECUR_NOTE and FRAC_MAX in RECUR_NOTE, (
    'the recurrence note must print the limit as a median with its range, '
    'not a median dressed as a bound: %r' % RECUR_NOTE)
assert 'power' in RECUR_NOTE, (
    'the recurrence note must say how many crossings the criterion cannot '
    'test at the declared power: %r' % RECUR_NOTE)
# ★★★ and it must not claim a test for the crossing that has no reading: the
#     string the figure draws has to open on the count that carries one.
assert RECUR_NOTE.startswith('%d of the %d ' % (N_WITHREAD, RECUR_POP)) \
    and N_WITHREAD < RECUR_POP, (
    'the recurrence note must report the tested count as %d of %d, not %r'
    % (N_WITHREAD, RECUR_POP, RECUR_NOTE[:60]))

# the hold-out branch's own sentence, lifted out of the drawing code so that
# it can be wrapped to the measured width like every other passage.
# r16, minor 26(b): "reserved before the search" is not what happened.  The
# census search was already under way; what was fixed beforehand is the RULE,
# committed three days before the first held-out block was searched.  The
# backmatter and Appendix B.1 both state it that way, and this label was the
# loosest of the four places the claim is made.
HOLDOUT_NOTE = (
    '%d blocks held out by a rule fixed before any of them was searched, '
    '%d windows: %d crossings, %s outranking all %d controls, %s confirmed.'
    % (HO_EB, HO_WIN, HO_X, HO_FIRST or 'none', N_CTRL, 'none'))

# ======================================================================================
# LAYOUT.  ★★ minor 4: THE RECURRENCE BOX'S OWN TEXT RAN OUT OF ITS BOX.
#
# Every level box was drawn at one constant height, H = 0.142 of the figure, and the
# text inside it was centred on a fixed offset from the box floor.  That works while
# every box holds two lines of description.  The recurrence box holds FIVE, because
# the criterion it states was made explicit in an earlier revision, and five lines of
# 5.1 pt on 1.3 spacing are 0.127 of the figure against an 0.142 box with a bold title
# already occupying the top of it.  The description therefore overflowed the box at
# BOTH ends: upwards through its own heading, and downwards through the note beneath
# it.  Nothing in a LaTeX log can see that, and no assertion in this file looked.
#
# The layout is now computed from the text.  Each block's height is the height of what
# it contains -- title, description, note -- in points, and the blocks are stacked in
# points from the top; the figure's own height is the total.  Add a line to any box and
# the box grows.  THEN the drawing is measured with the renderer and every pair of text
# artists is checked for overlap, and every description is checked to be inside the box
# it describes.  Both clauses are driven (--drive 22, --drive 23).
# ======================================================================================
_DRIVE = (int(sys.argv[sys.argv.index('--drive') + 1])
          if '--drive' in sys.argv else 0)
# ======================================================================================
# ★★★★ TYPE SIZE.  The canvas is drawn at the width of the column it is placed in, so
# the size the drawing asks for IS the size the reader gets.  That identity only holds
# while the two agree, and it did not: the drawing was emitted at one width and the
# float gives it another, and every label is then scaled by the ratio without anything
# in the build noticing.  Two defences, both below.  (1) COL_PT is the class's own
# \columnwidth, so the scale is 1 by construction.  (2) GEOMETRY, further down, reads
# the manuscript and refuses to draw if the float does not place this file at
# \columnwidth in a one-column figure.
#
# ★★ And the sizes themselves.  Nothing measured them before, so they had drifted to
# 4.6 pt for the longest passage in the drawing -- half the size of the caption
# immediately beneath it, and with mathtext subscripts landing near 3 pt.  Every size
# here is now at or above FS_FLOOR, the smallest type a reader should be asked to read
# at print size, and CLAUSE 3 measures the rendered glyphs rather than trusting this
# block.  Raising them makes the lines longer than their boxes, so the text is no
# longer wrapped by hand: `wrap()` measures each candidate line with the renderer and
# breaks it at the box it has to live in.  Change a font size and the drawing reflows.
# ======================================================================================
COL_PT = 245.27                         # \columnwidth of openjournal, twocolumn
PAD_IN = 0.015                          # savefig's border, inches
# the canvas is the column LESS the border savefig will add, so that the file
# on disk is one column wide and \includegraphics scales it by exactly 1.
PTS_W = COL_PT - 2 * PAD_IN * 72.0
FS_FLOOR = 6.5                          # no text in this drawing may be smaller
FS_HEAD, FS_HEAD2 = 8.0, 6.8            # census header, two lines
FS_TITLE, FS_SUB = 8.0, 6.8             # level heading, level description
FS_NOTE = FS_FLOOR                      # the note that sits between two levels
FS_RECUR = FS_FLOOR                     # the note under the recurrence box
FS_HO, FS_HO2 = 7.2, FS_FLOOR           # the hold-out branch
FS_MARGIN = FS_FLOOR                    # the note beside a level's count
FS_COUNT = 15.0                         # the count itself
LS = 1.3                                # line spacing, as passed to ax.text
PADI = 4.2                              # inner padding of a box, points
TITLE_GAP = 2.4                         # heading to description
if _DRIVE == 25:
    FS_RECUR = 4.6                      # the size this passage used to carry

# ---- a scratch canvas used only to measure strings before the real one exists
_MF = plt.figure(figsize=(1.0, 1.0), dpi=100)
_MF.canvas.draw()
_MR = _MF.canvas.get_renderer()


def text_w(s, fs):
    """width of one line, in points, as the renderer will actually set it."""
    t = _MF.text(0.0, 0.0, s, fontsize=fs)
    bb = t.get_window_extent(renderer=_MR)
    t.remove()
    return bb.width / _MF.dpi * 72.0


def _tokens(s):
    """Whitespace tokens, but a `$...$` group is ATOMIC: these strings carry
    inline mathtext with spaces in it ("$T_\\star \\geq 5$"), and breaking a
    line inside the dollars gives matplotlib two unterminated expressions and
    a drawing full of literal backslashes."""
    toks, buf, inmath = [], '', False
    for c in s:
        if c == '$':
            inmath = not inmath
            buf += c
        elif c.isspace() and not inmath:
            if buf:
                toks.append(buf)
                buf = ''
        else:
            buf += c
    if buf:
        toks.append(buf)
    assert not inmath, 'unbalanced $ in %r' % s
    return toks


def wrap(s, fs, maxpt):
    """Greedy word wrap at a MEASURED width.  Any newline already in `s` is
    discarded first: a hand-placed break is a break for one font size, and the
    whole point here is that the sizes are no longer fixed."""
    line, out = '', []
    for tok in _tokens(' '.join(s.split())):
        cand = tok if not line else line + ' ' + tok
        if line and text_w(cand, fs) > maxpt:
            out.append(line)
            line = tok
        else:
            line = cand
    out.append(line)
    return '\n'.join(out)


def nlines(s):
    return s.count('\n') + 1


def text_h(s, fs, ls=LS):
    return nlines(s) * fs * ls


# ---- the geometry of the drawing, in axes fractions of a COL_PT-wide canvas.
# ★ RIGHT was 0.655.  The counts and their margin notes live to the right of it,
#   and at FS_MARGIN the note "52 Class A, 4 Class B" no longer fits in what was
#   left, so the chain boxes give the margin the width it needs.
LEFT, RIGHT = 0.035, 0.595          # chain boxes; the margin holds the counts
XM = 0.17                           # the trunk arrow
XB = XM + 0.066                     # the notes between the levels
XR = RIGHT + 0.052                  # the margin column
W_BOX = (RIGHT - (LEFT + 0.022)) * PTS_W        # inside a level box
W_FULL = ((1.0 - LEFT) - (LEFT + 0.022)) * PTS_W   # a full-width passage
W_BETW = ((1.0 - LEFT) - XB) * PTS_W            # a note between two levels
W_MARG = ((1.0 - LEFT) - XR) * PTS_W            # beside a count
W_HEAD = (1.0 - 2 * LEFT) * PTS_W - 2 * PADI    # the centred header

# ---- measure every block, top to bottom, before anything is drawn
_WSUB = W_BOX * (1.8 if _DRIVE == 24 else 1.0)  # drive 24: wrap too wide
LEVELS = [(t, wrap(s, FS_SUB, _WSUB), c, wrap(n, FS_MARGIN, W_MARG))
          for t, s, c, n in LEVELS]
HEAD1 = wrap('Primary census: %d execution blocks, %d windows'
             % (N_EB, N_WIN), FS_HEAD, W_HEAD)
HEAD2 = wrap('%d Class A (fine channel, the carrier search)  +  '
             '%d Class B (coarse channel)' % (N_WINA, N_WINB),
             FS_HEAD2, W_HEAD)
head_h = (PADI + text_h(HEAD1, FS_HEAD) + text_h(HEAD2, FS_HEAD2) + PADI)
lvl_h = [PADI + FS_TITLE * LS + TITLE_GAP + text_h(sub, FS_SUB) + PADI
         for _t, sub, _c, _n in LEVELS]
if _DRIVE == 22:
    # the defect, restored: one constant box height for every level, which is
    # what the figure did before and what overflowed the recurrence box.
    lvl_h = [lvl_h[0]] * len(lvl_h)
BETWEEN = [wrap(s, FS_NOTE, W_BETW) for s in [
    'The line flag is a FLAG, not a disposal: %d of the %d crossings '
    'coincide with a masked transition, and all %d go on.'
    % (N_ATTR, N_CROSS, N_CROSS),
    'Diagnostics, deciding nothing: %d of the %d %s all %d control '
    'positions; the visibility fit localises but cannot discriminate '
    'at the trigger.'
    % (N_SCREEN, N_UNATTR, 'outranks' if N_SCREEN == 1 else 'outrank', N_CTRL),
]]
RECUR_NOTE = wrap(RECUR_NOTE, FS_RECUR, W_FULL)
HOLDOUT_NOTE = wrap(HOLDOUT_NOTE, FS_HO2, W_FULL)
gap_h = [max(text_h(s, FS_NOTE) + 7.0, 17.0) for s in BETWEEN]
recur_h = text_h(RECUR_NOTE, FS_RECUR, 1.32) + 6.0
ho_h = (PADI + FS_HO * LS + TITLE_GAP + text_h(HOLDOUT_NOTE, FS_HO2) + PADI)
GAP_HEAD, GAP_HO = 7.0, 10.0
TOTAL = (head_h + GAP_HEAD + sum(lvl_h) + sum(gap_h) + recur_h + GAP_HO + ho_h
         + 2 * PADI)

fig = plt.figure(figsize=(PTS_W / 72.0, TOTAL / 72.0))
ax = fig.add_axes([0.0, 0.0, 1.0, 1.0])
ax.set_xlim(0, 1)
ax.set_ylim(0, 1)
ax.axis('off')


def Y(pt_from_top):
    """points measured down from the top of the figure -> axes fraction."""
    return 1.0 - pt_from_top / TOTAL


def box(y0, h, x0=LEFT, x1=RIGHT, fc='0.96', ec='0.35', lw=0.7, ls='-'):
    ax.add_patch(FancyBboxPatch(
        (x0, y0), x1 - x0, h,
        boxstyle='round,pad=0.004,rounding_size=0.012',
        facecolor=fc, edgecolor=ec, lw=lw, linestyle=ls, zorder=2))


TEXTS = []                          # (artist, 'role', box index or None)


def put(x, y_top_pt, s, fs, role, inbox=None, **kw):
    """Place text by its TOP edge, which is the only anchor that makes a
    measured layout reproduce what was measured."""
    t = ax.text(x, Y(y_top_pt), s, ha=kw.pop('ha', 'left'), va='top',
                fontsize=fs, zorder=4, linespacing=kw.pop('linespacing', LS),
                **kw)
    TEXTS.append((t, role, inbox))
    return t


cur = PADI
# ---- the census header: the scale of the experiment, in one line
box(Y(cur + head_h), head_h / TOTAL, x1=1.0 - LEFT, fc='0.90')
put(0.5, cur + PADI, HEAD1, FS_HEAD, 'head', ha='center', fontweight='bold')
put(0.5, cur + PADI + text_h(HEAD1, FS_HEAD), HEAD2, FS_HEAD2, 'head',
    ha='center', color='0.3')
cur += head_h + GAP_HEAD

BOXES = []
for i, (title, sub, cnt, note) in enumerate(LEVELS):
    top, h = cur, lvl_h[i]
    BOXES.append((Y(top), Y(top + h)))
    box(Y(top + h), h / TOTAL, fc='0.955' if i else '0.90')
    put(LEFT + 0.022, top + PADI, title, FS_TITLE, 'title', i,
        fontweight='bold')
    put(LEFT + 0.022, top + PADI + FS_TITLE * LS + TITLE_GAP, sub, FS_SUB,
        'sub', i, color='0.3')
    ax.text(XR + 0.003, Y(top + h / 2.0), '%d' % cnt, ha='left',
            va='center', fontsize=FS_COUNT, fontweight='bold', color='0.1',
            zorder=4)
    if note:
        put(XR, top + h - PADI - text_h(note, FS_MARGIN), note, FS_MARGIN,
            'margin', i, color='0.42')
    cur += h
    if i < len(LEVELS) - 1:
        g = gap_h[i]
        ax.add_patch(FancyArrowPatch((XM, Y(cur)), (XM, Y(cur + g)),
                                     arrowstyle='-|>', mutation_scale=7,
                                     color='0.25', lw=1.0, zorder=3))
        # what sits BETWEEN the steps: a flag, and then two diagnostics.
        # Neither is a leaf arrow out of the chain, because neither removes a
        # crossing from it.
        s = BETWEEN[i]
        ymid = cur + g / 2.0
        ax.add_patch(FancyArrowPatch((XM, Y(ymid)), (XM + 0.055, Y(ymid)),
                                     arrowstyle='-', color='0.6', lw=0.6,
                                     zorder=3))
        put(XB, ymid - text_h(s, FS_NOTE) / 2.0, s, FS_NOTE, 'between',
            color='0.3')
        cur += g

# the recurrence box needs its own population, and what the test does and does
# not establish, stated under it.  ★ "covering repeat windows" counted BLOCK
# READINGS, not windows, and the section's other count -- the catalogue's
# covering windows -- is a different number of a different thing; each is now
# named for what it counts.
put(LEFT + 0.022, cur + 3.0, RECUR_NOTE, FS_RECUR, 'recurnote', color='0.35',
    linespacing=1.32)
cur += recur_h + GAP_HO

# ---- the reserved hold-out, as a branch of its own
box(Y(cur + ho_h), ho_h / TOTAL, x1=1.0 - LEFT, fc='none', ec='0.55', lw=0.6,
    ls=(0, (3, 2)))
put(LEFT + 0.022, cur + PADI,
    'Reserved hold-out, searched with the frozen pipeline', FS_HO, 'holdout',
    fontstyle='italic', color='0.2')
put(LEFT + 0.022, cur + PADI + FS_HO * LS + TITLE_GAP, HOLDOUT_NOTE, FS_HO2,
    'holdout', color='0.35')
# ★ NO connector.  The hold-out is not a further step of the chain and not
#   part of the primary census: it is the same pipeline run on blocks
#   reserved before the search, and an arrow from the recurrence box would
#   say the opposite.

# ======================================================================================
# ★★ THE MEASURED CHECK.  Everything above is arithmetic about font metrics; this is
# what the renderer actually produced.  Five clauses, each driven:
#   --drive 22  every level box is forced back to one constant height, which is
#               exactly the defect the referee found: CLAUSE 1 must fire.
#   --drive 23  the note beneath the last box is moved up into it.  That note is
#               inside no box, so only CLAUSE 2 can see it, and it must fire.
#   --drive 24  the hand wrapping is restored on one description, so its longest
#               line runs out of the side of its box: CLAUSE 1 again, horizontally.
#               Vertical containment and overlap both pass on it, which is why the
#               horizontal half had to be written: the drawing that shipped for four
#               versions would have passed clauses 1 and 2 at any font size at all.
#   --drive 25  one passage is set at the size it used to carry: CLAUSE 4 must fire.
#   --drive 26  the canvas is widened to full text width while the float still gives
#               it one column -- the original fault, where the artwork and the
#               geometry disagree and every label is silently halved: CLAUSE 3.
#   --drive 27  the manuscript is read as if the float were a full-width figure*:
#               CLAUSE 5 must fire.
# ======================================================================================
if _DRIVE == 23:
    # the note beneath the last box is moved up into it.  That note belongs to no
    # box, so the containment clause cannot see it and only the overlap clause
    # can -- which is why both clauses are here.
    _t = [t for t, role, _b in TEXTS if role == 'recurnote'][0]
    _t.set_y(_t.get_position()[1] + 0.055)

fig.canvas.draw()
_rend = fig.canvas.get_renderer()


def _bb(t):
    b = t.get_window_extent(renderer=_rend)
    return (b.x0, b.y0, b.x1, b.y1)


def _overlap(a, b, slack=0.5):
    return (a[0] < b[2] - slack and b[0] < a[2] - slack
            and a[1] < b[3] - slack and b[1] < a[3] - slack)


# CLAUSE 1: a description must be inside the box it describes.  Checked first,
# because it is the narrower statement and the one a reader of the figure would
# make; overlap alone does not catch a box's own text escaping into white space.
_dpi = fig.dpi
_H = fig.get_figheight() * _dpi
_W = fig.get_figwidth() * _dpi
_out = []
for t, role, ib in TEXTS:
    if ib is None:
        continue
    y1f, y0f = BOXES[ib]
    bb = _bb(t)
    if bb[1] < y0f * _H - 0.5 or bb[3] > y1f * _H + 0.5:
        _out.append(('vertical', role, t.get_text()[:34]))
    # ★ AND HORIZONTALLY.  A box's own text running out of its SIDE is the
    #   failure a hand-wrapped string gives the moment anyone changes a font
    #   size, and neither the vertical clause nor the overlap clause can see
    #   it: there is nothing to the right of these boxes to collide with.
    #   The margin column is the exception -- it is beside the boxes by
    #   design -- so it is bounded by the canvas instead.
    x0f, x1f = ((XR, 1.0 - LEFT) if role == 'margin' else (LEFT, RIGHT))
    if bb[0] < x0f * _W - 0.5 or bb[2] > x1f * _W + 0.5:
        _out.append(('horizontal', role, t.get_text()[:34]))
assert not _out, (
    'text drawn outside the box it belongs to: %r' % _out)

# CLAUSE 2: and no text may land on any other text, anywhere in the drawing.
_bad = []
for ia in range(len(TEXTS)):
    for ib in range(ia + 1, len(TEXTS)):
        ta, ra, _ = TEXTS[ia]
        tb, rb, _ = TEXTS[ib]
        if _overlap(_bb(ta), _bb(tb)):
            _bad.append((ra, rb, ta.get_text()[:34], tb.get_text()[:34]))
assert not _bad, (
    'text overlaps text in the rendered figure -- this is referee 2, minor 4, '
    'and it is only visible in the drawing: %r' % _bad[:4])

# ======================================================================================
# CLAUSES 3-5: IS IT BIG ENOUGH TO READ, AT THE SIZE IT IS PRINTED?
#
# Nothing in this build had ever asked.  A drawing is emitted at some width and then
# scaled by \includegraphics to whatever the float gives it, so the type a reader sees
# is the type asked for TIMES that ratio -- and the ratio is invisible from either end:
# the generator cannot see the float, the float cannot see the artwork, and pdflatex
# reports neither.  The three clauses close the loop: the saved width (clause 4) fixes
# the ratio, the manuscript (clause 5) fixes the float, and clause 4 multiplies them.
# ======================================================================================
_tb = fig.get_tightbbox(_rend)
W_SAVED = (_tb.width + 2 * PAD_IN) * 72.0        # what savefig will write, in points
SCALE = COL_PT / W_SAVED
if _DRIVE == 26:
    SCALE = COL_PT / (2.0 * COL_PT)             # emitted for the full text width

# CLAUSE 3: the artwork must be drawn at the width it is placed at.  Checked
# before the size clause, because a wrong scale makes every size wrong and the
# diagnosis a reader needs is the scale, not the symptom.
assert abs(SCALE - 1.0) < 0.03, (
    'this drawing is %.1f pt wide and the column is %.1f pt, so every label '
    'in it is set at %.0f per cent of the size it was drawn at'
    % (W_SAVED, COL_PT, 100 * SCALE))

# CLAUSE 4: no glyph may be set below the floor once the float has scaled it.
_small = sorted({round(t.get_fontsize() * SCALE, 2) for t, _r, _b in TEXTS})
assert _small[0] >= FS_FLOOR - 1e-9, (
    'the smallest type in this drawing prints at %.2f pt against a floor of '
    '%.2f pt (scale %.3f).  A reader cannot read it, and no LaTeX warning '
    'says so: %r' % (_small[0], FS_FLOOR, SCALE, _small[:3]))

# CLAUSE 5: and the float must agree with both.  Read from the manuscript, which
# is a different file from the one being checked, so the check is not circular.
_MAIN = [f for f in sorted(os.listdir(HERE))
         if f.startswith('technosignatures') and f.endswith('.tex')]
assert len(_MAIN) == 1, _MAIN
_SRC = ''
for _d in (HERE, os.path.join(HERE, 'sections')):
    for _f in sorted(os.listdir(_d)):
        if _f.endswith('.tex'):
            _SRC += open(os.path.join(_d, _f), encoding='utf-8',
                         errors='replace').read()
_SRC = re.sub(r'(?m)^\s*%.*$', '', _SRC)        # a commented float is not a float
if _DRIVE == 27:
    _SRC = (r'\begin{figure*}\includegraphics[width=0.98\textwidth]'
            r'{figures/chain_v412.pdf}\end{figure*}')
_HIT = [m for m in re.finditer(
    r'\\includegraphics\[([^\]]*)\]\{figures/chain_v412\.pdf\}', _SRC)]
assert len(_HIT) == 1, (
    'figures/chain_v412.pdf is included %d times in the manuscript; this '
    'check, and the type size it protects, assume exactly one' % len(_HIT))
_OPT = _HIT[0].group(1)
_ENV = _SRC[:_HIT[0].start()].rfind(r'\begin{figure*}') > \
    _SRC[:_HIT[0].start()].rfind(r'\begin{figure}')
assert not _ENV and re.search(r'width\s*=\s*\\columnwidth', _OPT), (
    'the chain is drawn for one column (%.1f pt) but the manuscript places '
    'it in a %s at [%s].  The caption, the placement and the artwork must '
    'all three agree; this is the defect that left its labels at half size.'
    % (COL_PT, 'figure*' if _ENV else 'figure', _OPT))

# D36: a drive never writes a production path.
_STEM = 'chain_v412' + ('_drive%d' % _DRIVE if _DRIVE else '')
for ext in ('pdf', 'png'):
    fig.savefig(os.path.join(OUTDIR, _STEM + '.' + ext),
                bbox_inches='tight', pad_inches=PAD_IN)
print('figures/chain_v412.pdf: 3 levels %d -> %d -> 0; census %d blocks / '
      '%d windows (%d A + %d B); flag %d line-coincident; rank %d of %d; '
      'recurrence %d of %d %s against %d repeat-block readings '
      '(%d retaining no spectrum); '
      'hold-out %d blocks '
      '/ %d windows / %d crossings / %d star-first'
      % (N_CROSS, N_UNATTR, N_EB, N_WIN, N_WINA, N_WINB, N_ATTR, N_SCREEN,
         N_UNATTR, N_WITHREAD, RECUR_POP, RECUR_WORD, N_REPEAT, N_NOSPEC,
         HO_EB, HO_WIN, HO_X, HO_FIRST))
