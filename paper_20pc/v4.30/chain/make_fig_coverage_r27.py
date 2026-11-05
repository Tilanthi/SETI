#!/usr/bin/env python3
r"""Where the survey searched, and where a repeat could test it.  R2-D10.

REPLACES TWO FIGURES WITH ONE.  Fig. 2 (`coverage_waterfall.pdf`, the number of
independent systems covering each sky frequency, Class A and Class B) and
Fig. 7 (`confcoverage.pdf`, the Class A systems detectable once, and those with
a separated repeat beyond a day and beyond a year) drew the same abscissa and,
for Class A, the same top curve.  Referee 2 (D10) asked for one two-row figure.

  row (a)  independent systems covering each sky frequency, Class B grey fill,
           Class A blue fill -- Fig. 2's content;
  row (b)  Class A only: detectable once (grey), with a SEPARATED repeat
           covering the frequency (blue), beyond a year (dark) -- Fig. 7's
           content, computed exactly as `make_fig_confcov_v412.py` computes it.

ONE ABSCISSA FOR BOTH ROWS.  Fig. 2 drew a continuous 84--950 GHz axis on which
47.7 GHz of Class A union is a row of hairlines; Fig. 7 split the axis by ALMA
band, panel widths in proportion to the frequency each band contributes.  The
merged figure uses Fig. 7's split for BOTH rows, over every band either class
populates, so a frequency sits at the same x in (a) and (b) and the two can be
read against each other -- which is the point of merging them.

Writes figures/coverage_r27.pdf.  No macros of its own.  Every curve is
asserted against the macros its caption and the text quote, on VALUES, and each
assertion has a drive that perturbs one input and must make it fire (B6: a
guard that tests set membership where the claim is about values cannot fail).
    --drive 1  one Class B window dropped          -> NWindows / DnuAB fire
    --drive 2  the separated-repeat rule moved to 30 d -> CvConfGHzDay fires
    --drive 3  one Class A system dropped          -> NSysClassA fires
A drive writes `figures/coverage_r27_driveN.pdf` and must not reach the end.
"""
import csv
import glob
import os
import re
import sys

import numpy as np
import matplotlib
matplotlib.use('Agg')

HERE = os.path.dirname(os.path.abspath(__file__))
os.chdir(HERE)
sys.path.insert(0, HERE)
import figfloor_r17 as ff        # the type floor, the scale and the float
ff.pin_epoch()

_DRIVE = int(sys.argv[sys.argv.index('--drive') + 1]) \
    if '--drive' in sys.argv else 0
FS_REQUIRED = 6.5
FS_FLOOR = FS_REQUIRED
FS_AXLAB = 7.6
matplotlib.rcParams['pdf.fonttype'] = 42
matplotlib.rcParams['ps.fonttype'] = 42
matplotlib.rcParams.update({
    'font.family': 'serif',
    'font.serif': ['STIXGeneral', 'DejaVu Serif'],
    'mathtext.fontset': 'stix',
    'font.size': 8, 'axes.labelsize': FS_AXLAB,
    'xtick.labelsize': FS_FLOOR, 'ytick.labelsize': FS_FLOOR,
    'legend.fontsize': FS_FLOOR,
})
import matplotlib.pyplot as plt
import epochs_r14 as _ep          # the ONE determination of a block's epoch


def texval(name):
    pat = re.compile(r'\\(?:new|renew|provide)command\{\\%s\}'
                     r'\{((?:[^{}]|\{[^{}]*\})*?)\}' % name)
    v = None
    for fn in sorted(f for f in glob.glob('numbers/survey_numbers*.tex')
                     if '_drive' not in f):
        for mm in pat.finditer(open(fn, encoding='utf-8').read()):
            if mm.group(1).strip():
                v = mm.group(1).strip()
    assert v is not None, name
    return v


ALL = list(csv.DictReader(open('per_target_results_v3.99.csv')))
if _DRIVE == 1:
    ALL = [r for r in ALL if r is not next(x for x in ALL
                                           if x['search_class'] == 'B')]
CAT = [r for r in ALL if r['search_class'] == 'A']
if _DRIVE == 3:
    _drop = sorted({r['system_id'] for r in CAT})[0]
    CAT = [r for r in CAT if r['system_id'] != _drop]


def iv_of(r):
    a, b = float(r['flo_GHz']), float(r['fhi_GHz'])
    return (min(a, b), max(a, b))


def union(iv):
    out = []
    for a, b in sorted(iv):
        if out and a <= out[-1][1]:
            out[-1][1] = max(out[-1][1], b)
        else:
            out.append([a, b])
    return out


def confirmable(rows, sep):
    """make_fig_confcov_v412.confirmable, verbatim in effect."""
    iv = [iv_of(r) + (r['eb'],) for r in rows]
    pts = sorted({x for a, b, _ in iv for x in (a, b)})
    keep = []
    for i in range(len(pts) - 1):
        mid = 0.5 * (pts[i] + pts[i + 1])
        if _ep.separated_confirming(
                [e for a, b, e in iv if a <= mid <= b], sep):
            keep.append([pts[i], pts[i + 1]])
    return union(keep)


def per_system(rows):
    by = {}
    for r in rows:
        by.setdefault(r['system_id'], []).append(r)
    return by


BYA = per_system(CAT)
BYB = per_system([r for r in ALL if r['search_class'] == 'B'])
PER = {'A': {s: union([iv_of(r) for r in v]) for s, v in BYA.items()},
       'B': {s: union([iv_of(r) for r in v]) for s, v in BYB.items()},
       'det': {}, 'day': {}, 'yr': {}}
_SEP_DAY = 1.0 if _DRIVE != 2 else 30.0
for s, rows in BYA.items():
    PER['det'][s] = PER['A'][s]
    PER['day'][s] = confirmable(rows, _SEP_DAY)
    PER['yr'][s] = confirmable(rows, 365.25)
PTS = sorted({x for d in PER.values() for iv in d.values()
              for a, b in iv for x in (a, b)})


def profile(key):
    xs, ys = [], []
    for i in range(len(PTS) - 1):
        mid = 0.5 * (PTS[i] + PTS[i + 1])
        xs.append((PTS[i], PTS[i + 1]))
        ys.append(sum(1 for iv in PER[key].values()
                      if any(a <= mid <= b for a, b in iv)))
    return xs, np.array(ys)


XS, Y = {}, {}
for k in PER:
    XS[k], Y[k] = profile(k)


def support(key):
    return sum(b - a for (a, b), n in zip(XS[key], Y[key]) if n)


# ---------------------------------------------------------------- checks
# Every clause compares a VALUE with the published macro, so each can fail.
assert np.all(Y['day'] <= Y['det']) and np.all(Y['yr'] <= Y['day']), \
    'a system is confirmable at a frequency it was not searched at'
_allU = union([iv_of(r) for r in ALL])
for got, nm, tol in ((len(ALL), 'NWindows', 0.5),
                     (len(set(BYA) | set(BYB)), 'NSystems', 0.5),
                     (sum(b - a for a, b in _allU), 'DnuAB', 0.05),
                     (len(_allU), 'UnionIntervals', 0.5),
                     (sum(r_b - r_a for r_a, r_b in (iv_of(r) for r in ALL))
                      / sum(b - a for a, b in _allU), 'GrossOverUnion', 0.05),
                     (len(BYA), 'NSysClassA', 0.5),
                     (support('det'), 'CvUnionA', 0.05),
                     (support('day'), 'CvConfGHzDay', 0.05),
                     (support('yr'), 'CvConfGHzYr', 0.05),
                     (int(Y['day'].max()), 'CvConfNMaxDay', 0.5)):
    want = float(texval(nm))
    assert abs(got - want) < tol, (
        'coverage_r27 draws %s where \\%s is %s' % (got, nm, want))

# ---------------------------------------------------------------- figure
BANDS = sorted({r['band'] for r in ALL}, key=int)
BSPAN = {}
for b in BANDS:
    f = [iv_of(r) for r in ALL if r['band'] == b]
    lo, hi = min(a for a, _ in f), max(c for _, c in f)
    pad = max(0.04 * (hi - lo), 0.05)
    BSPAN[b] = (lo - pad, hi + pad)
FLOOR = 9.0
WID = [max(BSPAN[b][1] - BSPAN[b][0], FLOOR) for b in BANDS]

W, H = ff.TEXT_PT, 176.0
fig = plt.figure(figsize=(W / 72.0, H / 72.0))
gs = fig.add_gridspec(2, len(BANDS), width_ratios=WID, wspace=0.16,
                      hspace=0.55, left=0.055, right=0.995, bottom=0.13,
                      top=0.90)


def steps(key):
    x, y = [], []
    for (a, b), n in zip(XS[key], Y[key]):
        x += [a, b]
        y += [n, n]
    return np.array(x), np.array(y)


ROWS = [
    ('(a) all windows', [('B', '#c8c8c8', 'fill', 'Class B: spectral excess'),
                         ('A', '#3a6ea5', 'fill', 'Class A: carrier search')]),
    ('(b) Class A', [('det', '#c9d4de', 'fill', 'detectable once'),
                     ('day', '#4878a8', '-', r'separated repeat, $>1$ d'),
                     ('yr', '#16324a', '-', r'$>1$ yr')]),
]
axes = []
for row, (tag, styles) in enumerate(ROWS):
    ymax = max(int(Y[k].max()) for k, *_ in styles) + 2
    for k, b in enumerate(BANDS):
        ax = fig.add_subplot(gs[row, k])
        lo, hi = BSPAN[b]
        for key, col, how, _lab in styles:
            x, y = steps(key)
            if how == 'fill':
                ax.fill_between(x, 0, y, step='post', color=col, lw=0,
                                zorder=1 if key in ('B', 'det') else 2)
            else:
                ax.plot(x, y, drawstyle='steps-post', color=col, lw=1.0,
                        zorder=3)
        ax.set_xlim(lo, hi)
        ax.set_ylim(0, ymax)
        ax.yaxis.set_major_locator(matplotlib.ticker.MaxNLocator(
            nbins=3, integer=True))
        if row == 0:
            ax.set_title('Band %s' % b, fontsize=FS_FLOOR + 0.3, pad=2.0)
        ax.tick_params(labelsize=FS_FLOOR, length=2, pad=1.5)
        if (hi - lo) > 12 and WID[k] / sum(WID) > 0.12:
            ax.xaxis.set_major_locator(matplotlib.ticker.MaxNLocator(
                nbins=2, prune='both', integer=True, steps=[1, 2, 5, 10]))
        else:
            ax.set_xticks([round(0.5 * (lo + hi))])
        ax.xaxis.set_major_formatter(
            matplotlib.ticker.FormatStrFormatter('%d'))
        if k:
            ax.set_yticklabels([])
        else:
            ax.set_ylabel('systems', labelpad=1.5)
        for sp in ('top', 'right'):
            ax.spines[sp].set_visible(False)
        axes.append(ax)
    from matplotlib.lines import Line2D
    from matplotlib.patches import Patch
    hand = [Patch(facecolor=c, lw=0, label=l) if h == 'fill'
            else Line2D([], [], color=c, lw=1.0, label=l)
            for _k, c, h, l in styles]
    y_leg = 0.995 if row == 0 else 0.505
    fig.text(0.057, y_leg, tag, ha='left', va='top', fontsize=FS_AXLAB,
             weight='bold')
    fig.legend(handles=hand, loc='upper left',
               bbox_to_anchor=(0.20, y_leg + 0.012), ncol=len(hand),
               frameon=False, fontsize=FS_FLOOR, handlelength=1.2,
               columnspacing=0.9, handletextpad=0.35)
fig.text(0.525, 0.012, 'sky frequency (GHz)', ha='center', fontsize=FS_AXLAB)

ff.no_overlap([t for a in axes for t in a.get_xticklabels()], fig, clear=2.5)
ff.no_overlap([t for a in axes for t in a.get_xticklabels()
               + a.get_yticklabels()] + [a.title for a in axes], fig,
              clear=0.0)

OUT = 'figures/coverage_r27%s.pdf' % ('_drive%d' % _DRIVE if _DRIVE else '')
fig.savefig(OUT)
plt.close(fig)
ff.check(OUT, HERE, 'figures/coverage_r27.pdf', floor=FS_REQUIRED,
         expect_env='figure*')
assert not _DRIVE, ('--drive %d reached the end of the generator: the clause '
                    'it was written to break did not fire' % _DRIVE)
for key in ('A', 'B', 'det', 'day', 'yr'):
    print('%-4s support %7.3f GHz, peak %2d systems'
          % (key, support(key), int(Y[key].max())))
print('coverage_r27.pdf: %d windows, %d bands' % (len(ALL), len(BANDS)))
