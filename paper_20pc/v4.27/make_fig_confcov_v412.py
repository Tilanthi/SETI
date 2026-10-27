#!/usr/bin/env python3
r"""Searchable against confirmable: C_conf(nu).  Referee 1, point 4.

The survey's headline extent is a SEARCH extent.  A carrier seen once in one
window is not a detection, and whether it could ever have been tested again
depends on whether the archive happens to hold a second execution block
covering the SAME frequency toward the SAME system -- which it does not
decide window by window, because repeat visits re-tune.

This figure draws, against sky frequency and for the Class A experiment:

  * the number of systems a carrier could have been DETECTED ONCE toward
    (grey fill) -- the searchable extent, whose support is \CvUnionA GHz;
  * the number for which an independent repeat more than a DAY later also
    covers that frequency (blue), support \CvConfGHzDay GHz;
  * the same beyond a YEAR (dark), support \CvConfGHzYr GHz.

The abscissa is split by ALMA band with panel widths in proportion to the
frequency each band contributes, for the reason the completeness map is drawn
the same way: 47.7 GHz of union spread over 759 GHz renders every island as a
hairline on a single linear axis.

Reads the catalogue, the frozen epoch table and `cover_v412.json`, and
asserts the curves against the macros `cover_v412.py` published, so the
figure and its caption cannot disagree.  Writes figures/confcoverage.pdf.
No macros of its own.
"""
import csv
import glob
import json
import math
import os
import re

import sys

import numpy as np
import matplotlib
matplotlib.use('Agg')
import figfloor_r17 as ff        # the type floor, the scale and the float
ff.pin_epoch()                   # before any savefig, or the wall clock is stamped

# ★ THE TYPE FLOOR.  Every size set below is at or above it, and the assertion
#   at the foot of the file measures the file that was WRITTEN rather than the
#   sizes asked for here.  Drives 60-63 break one clause each; see there.
_DRIVE = int(sys.argv[sys.argv.index('--drive') + 1]) \
    if '--drive' in sys.argv else 0
# ★ FS_REQUIRED is what the figure is HELD to and is never perturbed; FS_FLOOR
#   is what it is DRAWN at.  They are separate because a drive that lowered
#   both would move the check and the thing it checks together and could never
#   fail -- this round has already found a gate that cross-checked the value
#   its own drive perturbed.
FS_REQUIRED = 6.5
FS_FLOOR = FS_REQUIRED if _DRIVE != 61 else 5.6   # 61: the sizes it shipped at
FS_TICK = FS_FLOOR
FS_TITLE = FS_FLOOR + 0.3
FS_LEGEND = FS_FLOOR
FS_AXLAB = 7.6

matplotlib.rcParams['pdf.fonttype'] = 42
matplotlib.rcParams['ps.fonttype'] = 42
matplotlib.rcParams.update({
    'font.family': 'serif',
    'font.serif': ['STIXGeneral', 'DejaVu Serif'],
    'mathtext.fontset': 'stix',
    'font.size': 8, 'axes.labelsize': FS_AXLAB,
    'xtick.labelsize': FS_TICK, 'ytick.labelsize': FS_TICK,
    'legend.fontsize': FS_LEGEND,
})
import matplotlib.pyplot as plt

HERE = os.path.dirname(os.path.abspath(__file__))
os.chdir(HERE)


def texval(name):
    pat = re.compile(r'\\(?:new|renew|provide)command\{\\%s\}'
                     r'\{((?:[^{}]|\{[^{}]*\})*?)\}' % name)
    v = None
    for fn in sorted([_mgp for _mgp in glob.glob('survey_numbers*.tex') if '_drive' not in _mgp]):
        for mm in pat.finditer(open(fn, encoding='utf-8').read()):
            if mm.group(1).strip():
                v = mm.group(1).strip()
    assert v is not None, name
    return v


CAT = [r for r in csv.DictReader(open('per_target_results_v3.99.csv'))
       if r['search_class'] == 'A']
import epochs_r14 as _ep    # the ONE determination of a block's epoch
MJD = _ep.EPOCHS
MEAS = json.load(open('cover_v412.json'))

SYS = sorted({r['system_id'] for r in CAT})
BYSYS = {}
for r in CAT:
    BYSYS.setdefault(r['system_id'], []).append(r)


def union(iv):
    out = []
    for a, b in sorted((min(x, y), max(x, y)) for x, y in iv):
        if out and a <= out[-1][1]:
            out[-1][1] = max(out[-1][1], b)
        else:
            out.append([a, b])
    return out


def confirmable(rows, sep):
    iv = [(min(float(r['flo_GHz']), float(r['fhi_GHz'])),
           max(float(r['flo_GHz']), float(r['fhi_GHz'])), r['eb'])
          for r in rows]
    pts = sorted({x for a, b, _ in iv for x in (a, b)})
    keep = []
    for i in range(len(pts) - 1):
        mid = 0.5 * (pts[i] + pts[i + 1])
        # ★★★ ROUND 14: measured separations, through epochs_r14 -- the same
        # substitution as in recur_v411.py and cover_v412.py.  This figure
        # draws the confirmation coverage, so drawing it from the broken OUS
        # join understated the very quantity it exists to show.
        if _ep.separated_confirming(
                [e for a, b, e in iv if a <= mid <= b], sep):
            keep.append([pts[i], pts[i + 1]])
    return union(keep)


PER = {'det': {}, 'day': {}, 'yr': {}}
for s, rows in BYSYS.items():
    PER['det'][s] = union([(float(r['flo_GHz']), float(r['fhi_GHz']))
                           for r in rows])
    PER['day'][s] = confirmable(rows, 1.0)
    PER['yr'][s] = confirmable(rows, 365.25)

# the exact step profile: breakpoints are interval boundaries, never a grid
PTS = sorted({x for d in PER.values() for iv in d.values()
              for a, b in iv for x in (a, b)})


def profile(key):
    xs, ys = [], []
    for i in range(len(PTS) - 1):
        mid = 0.5 * (PTS[i] + PTS[i + 1])
        n = sum(1 for iv in PER[key].values()
                if any(a <= mid <= b for a, b in iv))
        xs.append((PTS[i], PTS[i + 1]))
        ys.append(n)
    return xs, np.array(ys)


XS, Y = {}, {}
for k in PER:
    XS[k], Y[k] = profile(k)

# ---------------------------------------------------------------- checks
# (1) confirmable can never exceed searchable at any frequency
assert np.all(Y['day'] <= Y['det']) and np.all(Y['yr'] <= Y['day']), \
    'a system is confirmable at a frequency it was not searched at'
# (2) the supports reproduce the published union bandwidths
for key, nm in (('det', 'CvUnionA'), ('day', 'CvConfGHzDay'),
                ('yr', 'CvConfGHzYr')):
    sup = sum(b - a for (a, b), n in zip(XS[key], Y[key]) if n)
    assert abs(sup - float(texval(nm))) < 0.05, \
        ('the %s curve has support %.3f GHz where \\%s is %s'
         % (key, sup, nm, texval(nm)))
# (3) the peak of C_conf is where the macro says it is
_pk = int(Y['day'].max())
assert _pk == int(texval('CvConfNMaxDay')), (_pk, texval('CvConfNMaxDay'))
# (4) the system count is the published Class A one
assert len(SYS) == int(texval('NSysClassA')), (len(SYS),)

# ---------------------------------------------------------------- figure
BANDS = sorted({r['band'] for r in CAT}, key=int)
BSPAN = {}
for b in BANDS:
    f = [(min(float(r['flo_GHz']), float(r['fhi_GHz'])),
          max(float(r['flo_GHz']), float(r['fhi_GHz'])))
         for r in CAT if r['band'] == b]
    lo, hi = min(a for a, _ in f), max(c for _, c in f)
    pad = max(0.04 * (hi - lo), 0.05)
    BSPAN[b] = (lo - pad, hi + pad)
FLOOR = 5.0
WID = [max(BSPAN[b][1] - BSPAN[b][0], FLOOR) for b in BANDS]

# ★ The canvas IS the column: the saved width is the figsize, there is no tight
#   bbox here, so the float's scale is 1 by construction and the sizes above are
#   the sizes a reader sees.  The height grew with the type (118 -> 134 pt): the
#   panels keep their aspect and the legend keeps its single row.
W, H = ff.COL_PT, 128.0
if _DRIVE in (60, 62):           # 60: artwork too wide for the float it is given
    W = ff.TEXT_PT               # 62: and drawn as a two-column figure*
fig = plt.figure(figsize=(W / 72.0, H / 72.0))
gs = fig.add_gridspec(1, len(BANDS), width_ratios=WID, wspace=0.17 if _DRIVE != 65 else 0.03,
                      left=0.115, right=0.988, bottom=0.265, top=0.845)

STYLE = [('det', '#c9d4de', None, 'searched (detectable once)'),
         ('day', '#4878a8', '-', r'repeat at $>1$ d'),
         ('yr', '#16324a', '-', r'$>1$ yr')]


def steps(key):
    """x, y arrays that draw the exact step function, zero outside support."""
    x, y = [], []
    for (a, b), n in zip(XS[key], Y[key]):
        x += [a, b]
        y += [n, n]
    return np.array(x), np.array(y)


axes = []
for k, b in enumerate(BANDS):
    ax = fig.add_subplot(gs[0, k])
    lo, hi = BSPAN[b]
    for key, col, ls, _lab in STYLE:
        x, y = steps(key)
        if ls is None:
            ax.fill_between(x, 0, y, step='post', color=col, lw=0, zorder=1)
            ax.plot(x, y, drawstyle='steps-post', color='#8da4b8', lw=0.5,
                    zorder=2)
        else:
            ax.plot(x, y, drawstyle='steps-post', color=col, lw=1.0,
                    ls=ls, zorder=3)
    ax.set_xlim(lo, hi)
    ax.set_ylim(0, int(Y['det'].max()) + 2)
    ax.set_title('Band %s' % b, fontsize=FS_TITLE, pad=2.0)
    ax.tick_params(labelsize=FS_TICK, length=2, pad=1.5)
    if (hi - lo) > 12:
        ax.xaxis.set_major_locator(matplotlib.ticker.MaxNLocator(
            nbins=2, prune='both', integer=True, steps=[1, 2, 5, 10]))
    else:
        ax.set_xticks([round(0.5 * (lo + hi))])
    ax.xaxis.set_major_formatter(matplotlib.ticker.FormatStrFormatter('%d'))
    if k:
        ax.set_yticklabels([])
    else:
        ax.set_ylabel('systems', labelpad=1.5)
    for sp in ('top', 'right'):
        ax.spines[sp].set_visible(False)
    axes.append(ax)

fig.text(0.552, 0.028, 'sky frequency (GHz)', ha='center',
         fontsize=FS_AXLAB if _DRIVE != 64 else 24.0)
from matplotlib.lines import Line2D
from matplotlib.patches import Patch
fig.legend(handles=[Patch(facecolor='#c9d4de', edgecolor='#8da4b8',
                          lw=0.5, label=STYLE[0][3]),
                    Line2D([], [], color='#4878a8', lw=1.0, label=STYLE[1][3]),
                    Line2D([], [], color='#16324a', lw=1.0, label=STYLE[2][3])],
           loc='upper left', bbox_to_anchor=(0.112, 1.008), ncol=3,
           frameon=False, fontsize=FS_LEGEND, handlelength=1.2,
           columnspacing=0.7, handletextpad=0.35)

# ======================================================================================
# ★★ IS IT BIG ENOUGH TO READ?  Five clauses, each driven to fail on its own:
#   --drive 60  the canvas is drawn at the full text width while the float still
#               gives it one column -- the fault that halves every label without
#               a single warning anywhere in the build.  SCALE fires.
#   --drive 61  the sizes this figure shipped at are restored.  FLOOR fires, and
#               it fires on the PDF, not on the numbers above.
#   --drive 62  the drawing is emitted as a two-column figure* and declared as
#               one, while the manuscript places it in a figure.  FLOAT fires.
#   --drive 63  SOURCE_DATE_EPOCH is cleared before the save, which is how a
#               generator run by hand writes a file the build cannot reproduce.
#               EPOCH fires, on the stamp in the file.
#   --drive 64  the abscissa label is set at 24 pt, so it runs off a canvas that
#               does not grow to fit it.  FIT fires -- and neither an overlap
#               check nor a vertical-containment check could ever see it.
# ======================================================================================
# ★ TWO CLEARANCES, because they are two different questions.  Abscissa
#   labels in ADJACENT panels must stand apart -- 240 beside 320 reads
#   "240320" without ever intersecting -- while everything else need only not
#   collide.
#   --drive 65  the panels are pushed together until 240 and 320 touch across
#               the Band 6 / Band 7 boundary.  CLASH fires, on the clearance
#               clause: the two labels never intersect, they merely read as
#               one number, which is why bare non-intersection is not the test.
ff.no_overlap([t for a in axes for t in a.get_xticklabels()], fig, clear=2.5)
ff.no_overlap([t for a in axes for t in
               a.get_xticklabels() + a.get_yticklabels()]
              + [a.title for a in axes], fig, clear=0.0)

if _DRIVE == 63:
    os.environ.pop('SOURCE_DATE_EPOCH', None)
OUT = 'figures/confcoverage%s.pdf' % ('_drive%d' % _DRIVE if _DRIVE else '')
fig.savefig(OUT)
plt.close(fig)
ff.check(OUT, HERE, 'figures/confcoverage.pdf', floor=FS_REQUIRED,
         expect_env='figure*' if _DRIVE == 62 else 'figure')

# ★ D36, and a drive that silently passes is worse than no drive: every drive
#   number above is expected to have failed a clause by now, so reaching this
#   line with one set is itself a failure -- and it also guarantees a drive can
#   never write a path production reads.
assert not _DRIVE, ('--drive %d reached the end of the generator: the clause '
                    'it was written to break did not fire' % _DRIVE)

for key, nm in (('det', 'searched'), ('day', '>1 d'), ('yr', '>1 yr')):
    sup = sum(b - a for (a, b), n in zip(XS[key], Y[key]) if n)
    print('%-8s support %7.3f GHz, peak %2d systems'
          % (nm, sup, int(Y[key].max())))
print('confcoverage.pdf: %d Class A systems, %d bands' % (len(SYS), len(BANDS)))
