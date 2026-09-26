#!/usr/bin/env python3
"""Figure: the visibility-domain localisation of every threshold crossing.

Replaces the thirteen bar panels of the old unattributed-events figure, which
showed only the windows the rank screen had selected and was built from a
frozen pre-repair fit file. Referee 2 asks for one scatter of Re/sigma against
Im/sigma for all crossings, coloured by disposition, with the control values as
small grey points; Referee 1 asks for the same information as a ledger. This is
that figure, and it reads the same join the ledger table does.

The committed criterion is drawn on the plot, so a reader can see which region
of the plane counts as localised without consulting the text.
"""
import json
import os

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt  # noqa: E402

# Type-3 fonts fail the build gate: the manuscript must embed TrueType.
plt.rcParams.update({'pdf.fonttype': 42, 'ps.fonttype': 42})
import numpy as np  # noqa: E402

import importlib.util  # noqa: E402

HERE = os.path.dirname(os.path.abspath(__file__))
_spec = importlib.util.spec_from_file_location(
    'ledger_v401', os.path.join(HERE, 'ledger_v401.py'))
_lg = importlib.util.module_from_spec(_spec)
import io  # noqa: E402
import contextlib  # noqa: E402
with contextlib.redirect_stdout(io.StringIO()):
    _spec.loader.exec_module(_lg)

RE_MIN, IM_MAX = _lg.RE_MIN, _lg.IM_MAX
ROWS = [r for r in _lg.ROWS if r['fitted']]

# control points, from both fit files, as the null cloud
CTRL = []
for src in ('visfit_all_v385.json', 'visfit_r6_result.json'):
    d = json.load(open(os.path.join(HERE, src)))
    recs = d['fits'] if 'fits' in d else d
    for rec in recs.values():
        if rec.get('status') != 'ok':
            continue
        for key in ('pos_controls', 'freq_controls'):
            for c in rec.get(key) or []:
                if c.get('snr_re') is not None and c.get('snr_im') is not None:
                    CTRL.append((float(c['snr_re']), float(c['snr_im'])))
CTRL = np.array(CTRL) if CTRL else np.zeros((0, 2))

fig, ax = plt.subplots(figsize=(7.0, 4.6))

if len(CTRL):
    ax.plot(CTRL[:, 0], CTRL[:, 1], '.', ms=2.0, color='0.72', zorder=1,
            label='control positions and frequencies (%d)' % len(CTRL))

# the localisation region is the RECTANGLE, not the half-plane: a crossing
# with a large real part and a large imaginary part is a displaced source and
# must not appear to be inside the criterion
ax.add_patch(plt.Rectangle((RE_MIN, -IM_MAX), 1e3, 2 * IM_MAX,
                           facecolor='#cfe6cf', edgecolor='none', zorder=0))

groups = [
    ([r for r in ROWS if r['localised'] and r['line']],
     'o', '#1a7f1a', 'localised, line-attributed'),
    ([r for r in ROWS if r['localised'] and not r['line']],
     'D', '#c1121f', 'localised, unattributed'),
    ([r for r in ROWS if not r['localised'] and r['screen']],
     's', '#1f4e9c', 'not localised, rank screen passed'),
    ([r for r in ROWS if not r['localised'] and not r['screen']],
     'x', '0.25', 'not localised'),
]
for rows, mk, col, lab in groups:
    if not rows:
        continue
    ax.plot([r['re'] for r in rows], [r['im'] for r in rows], mk, ms=5.5,
            mfc='none' if mk in 'oDs' else col, mec=col, color=col, mew=1.3,
            ls='none', zorder=3, label='%s (%d)' % (lab, len(rows)))

# the two extremes earn a label: the largest real part in the survey, thrown
# out by its imaginary part, and the strongest positive control
_ext = max(ROWS, key=lambda r: r['re'])
ax.plot([_ext['re']], [_ext['im']], 'x', ms=8, mew=2.0, color='#c1121f',
        zorder=5)
from star_alias import designation as _dg  # noqa: E402
ax.annotate('%s\nRe/$\\sigma$=%.1f, Im/$\\sigma$=%.1f\nrejected: displaced'
            % (_dg(_ext['star'], tex=False), _ext['re'], _ext['im']),
            xy=(_ext['re'], _ext['im']), xytext=(-104, -30),
            textcoords='offset points', fontsize=6.5, ha='left',
            arrowprops=dict(arrowstyle='-', lw=0.6, color='0.4'))

ax.axvline(RE_MIN, color='#1a7f1a', lw=0.8, ls='--')
ax.axhline(IM_MAX, color='#1a7f1a', lw=0.8, ls='--')
ax.axhline(-IM_MAX, color='#1a7f1a', lw=0.8, ls='--')
ax.axhline(0, color='0.6', lw=0.5)
ax.set_xscale('symlog', linthresh=5)
ax.set_xlabel(r'Re/$\sigma$ at the stellar position')
ax.set_ylabel(r'Im/$\sigma$')
ax.set_ylim(-11, 44)
ax.set_xlim(-6, 90)
ax.text(RE_MIN * 1.06, 43.0, 'localisation region (criterion committed '
        'before the fits)', fontsize=6.3, color='#146114', va='top')
ax.legend(fontsize=6.3, loc='lower right', framealpha=0.95)
fig.tight_layout()
fig.savefig(os.path.join(HERE, 'figures', 'ledger_vis.pdf'))
print('figure -> figures/ledger_vis.pdf  (%d crossings, %d controls)'
      % (len(ROWS), len(CTRL)))
