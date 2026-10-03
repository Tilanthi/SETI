#!/usr/bin/env python3
r"""The archival selection, drawn rather than tabulated.

Referee 1: the statement that 21 of 5908 classified M dwarfs are searched
is scientifically important and should not be buried in prose. This plots
the spectral-type composition of the searched sample against the 40-pc
reference census, side by side, so the bias is visible at a glance.

Both columns are read out of the generated selection-function table, so
the figure and the table cannot disagree.

Writes figures/selection_bias.pdf.
"""
import os, re

import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

os.chdir(os.path.dirname(os.path.abspath(__file__)))
plt.rcParams.update({'pdf.fonttype': 42, 'ps.fonttype': 42,
                     'font.family': 'serif', 'font.serif': ['DejaVu Serif'],
                     'mathtext.fontset': 'dejavuserif'})

TEX = open('tab_selection.tex').read()

# Rows of the temperature panel look like:
#   \quad M ($<3900$\,K) & 5908 (68.7\%) & 21 (36.8\%) & 0.5 \\
ROW = re.compile(r'\\quad\s+([OBAFGKM])\s*\([^)]*\)\s*&\s*'
                 r'([\d\s,]+)\s*\(([\d.]+)\\%\)\s*&\s*'
                 r'([\d\s,]+)\s*\(([\d.]+)\\%\)')
rows = []
for m in ROW.finditer(TEX):
    rows.append((m.group(1),
                 int(m.group(2).replace(' ', '').replace(',', '')),
                 float(m.group(3)),
                 int(m.group(4).replace(' ', '').replace(',', '')),
                 float(m.group(5))))
assert rows, 'no spectral-type rows found in tab_selection.tex'
order = [c for c in 'OBAFGKM' if any(r[0] == c for r in rows)]
rows = sorted(rows, key=lambda r: order.index(r[0]))

lab = [r[0] for r in rows]
cen = np.array([r[2] for r in rows])
sea = np.array([r[4] for r in rows])
ncen = np.array([r[1] for r in rows])
nsea = np.array([r[3] for r in rows])

fig, ax = plt.subplots(figsize=(3.4, 2.15))
x = np.arange(len(lab))
ax.bar(x - 0.19, cen, width=0.36, color='0.72', edgecolor='0.35',
       linewidth=0.4, label='within 40 pc (%d classified)' % ncen.sum())
ax.bar(x + 0.19, sea, width=0.36, color='#3a6ea5', edgecolor='0.25',
       linewidth=0.4, label='searched here (%d classified)' % nsea.sum())
for i in range(len(lab)):
    ax.text(x[i] - 0.19, cen[i] + 1.4, str(ncen[i]), ha='center', fontsize=5.4,
            color='0.35')
    ax.text(x[i] + 0.19, sea[i] + 1.4, str(nsea[i]), ha='center', fontsize=5.4,
            color='#22456b')
ax.set_xticks(x)
ax.set_xticklabels(lab, fontsize=7.2)
ax.set_xlabel('spectral class',
              fontsize=7.2)
ax.set_ylabel('per cent of classified objects', fontsize=7.2)
ax.tick_params(labelsize=6.6)
ax.legend(fontsize=5.9, frameon=False, borderpad=0.25, handlelength=1.2,
          handletextpad=0.5, loc='upper left')
ax.set_ylim(0, max(cen.max(), sea.max()) * 1.30)
for sp in ('top', 'right'):
    ax.spines[sp].set_visible(False)
ax.grid(axis='y', color='0.92', lw=0.4)
fig.savefig('figures/selection_bias.pdf', bbox_inches='tight', pad_inches=0.02)
print('selection_bias.pdf: ' + ', '.join(
    '%s %d/%d (%.0f%% vs %.0f%%)' % (l, ns, nc, sv, cv)
    for l, nc, cv, ns, sv in rows))
