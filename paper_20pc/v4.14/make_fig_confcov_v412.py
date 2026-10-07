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

import numpy as np
import matplotlib
matplotlib.use('Agg')
matplotlib.rcParams['pdf.fonttype'] = 42
matplotlib.rcParams['ps.fonttype'] = 42
matplotlib.rcParams.update({
    'font.family': 'serif',
    'font.serif': ['STIXGeneral', 'DejaVu Serif'],
    'mathtext.fontset': 'stix',
    'font.size': 8, 'axes.labelsize': 7.6,
    'xtick.labelsize': 6.8, 'ytick.labelsize': 6.8, 'legend.fontsize': 6.0,
})
import matplotlib.pyplot as plt

HERE = os.path.dirname(os.path.abspath(__file__))
os.chdir(HERE)


def texval(name):
    pat = re.compile(r'\\(?:new|renew|provide)command\{\\%s\}'
                     r'\{((?:[^{}]|\{[^{}]*\})*?)\}' % name)
    v = None
    for fn in sorted(glob.glob('survey_numbers*.tex')):
        for mm in pat.finditer(open(fn, encoding='utf-8').read()):
            if mm.group(1).strip():
                v = mm.group(1).strip()
    assert v is not None, name
    return v


CAT = [r for r in csv.DictReader(open('per_target_results_v3.99.csv'))
       if r['search_class'] == 'A']
MJD = json.load(open('epochs_v386.json'))['mjd']
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
        ts = sorted(MJD[e] for a, b, e in iv if a <= mid <= b and e in MJD)
        if any(ts[k] - ts[j] > sep
               for j in range(len(ts)) for k in range(j + 1, len(ts))):
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

W, H = 245.0, 118.0
fig = plt.figure(figsize=(W / 72.0, H / 72.0))
gs = fig.add_gridspec(1, len(BANDS), width_ratios=WID, wspace=0.14,
                      left=0.105, right=0.985, bottom=0.215, top=0.845)

STYLE = [('det', '#c9d4de', None, 'searched (detectable once)'),
         ('day', '#4878a8', '-', r'confirmable at $>1$ d'),
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
    ax.set_title('Band %s' % b, fontsize=6.6, pad=2.0)
    ax.tick_params(labelsize=6.0, length=2, pad=1.5)
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

fig.text(0.545, 0.012, 'sky frequency (GHz)', ha='center', fontsize=7.6)
from matplotlib.lines import Line2D
from matplotlib.patches import Patch
fig.legend(handles=[Patch(facecolor='#c9d4de', edgecolor='#8da4b8',
                          lw=0.5, label=STYLE[0][3]),
                    Line2D([], [], color='#4878a8', lw=1.0, label=STYLE[1][3]),
                    Line2D([], [], color='#16324a', lw=1.0, label=STYLE[2][3])],
           loc='upper left', bbox_to_anchor=(0.105, 1.005), ncol=3,
           frameon=False, fontsize=5.6, handlelength=1.3,
           columnspacing=0.8, handletextpad=0.4)

fig.savefig('figures/confcoverage.pdf')
plt.close(fig)

for key, nm in (('det', 'searched'), ('day', '>1 d'), ('yr', '>1 yr')):
    sup = sum(b - a for (a, b), n in zip(XS[key], Y[key]) if n)
    print('%-8s support %7.3f GHz, peak %2d systems'
          % (nm, sup, int(Y[key].max())))
print('confcoverage.pdf: %d Class A systems, %d bands' % (len(SYS), len(BANDS)))
