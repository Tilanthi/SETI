#!/usr/bin/env python3
"""The selection funnel (referees A3, A15, B2): from the Gaia reference
census to the systems actually searched, so the three denominators readers
confuse (17,566 catalogued, ~115 genuinely covered, 88 searched) are
visibly different objects.  Every number is read from the generated macro
files, so the figure cannot drift from the text.

v4.03: the right-hand panel is GONE.  It drew the experiment as one nested
funnel ending in "of those, localised at the star in the visibilities" ->
"independently confirmed", which asserts that the drift-following
visibility fit filters candidates.  DECISIONS_R7 A2 withdraws that: under
the corrected reference epoch the fit rejects nothing except one grossly
displaced source, and its twelve controls resolve a rank of about 1/13.
The panel also ran the rank screen BEFORE line attribution, where the chain
that decides runs attribution first.  Both are now drawn by
make_fig_chain_v403.py, from the ledger's own counts, with the fit outside
the column; drawing a second, differently ordered chain here would be two
figures contradicting each other.  `funnel_steps.tex` went with it -- a
macro reporting how many steps are drawn is meaningless once none are.

Usage: python3 make_fig_funnel.py [outdir]
"""
import glob
import os
import re
import sys

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import Polygon

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = sys.argv[1] if len(sys.argv) > 1 else os.path.join(HERE, "figures")

plt.rcParams.update({
    "font.family": "serif",
    "font.serif": ["STIXGeneral", "DejaVu Serif", "Times New Roman"],
    "mathtext.fontset": "stix",
    "font.size": 7.2,
    "axes.linewidth": 0.6,
    "pdf.fonttype": 42, "ps.fonttype": 42,      # never Type 3
    "figure.dpi": 200,
})


def macros():
    d = {}
    for fn in glob.glob(os.path.join(HERE, "survey_numbers*.tex")):
        for m in re.finditer(r"\\newcommand\{\\([A-Za-z]+)\}\{(.*)\}",
                             open(fn, encoding="utf-8").read()):
            d[m.group(1)] = m.group(2)
    return d


M = macros()


def n(name):
    """Macro value as plain text: LaTeX thin spaces become real ones."""
    return M[name].replace("\\,", " ")


# ---------------------------------------------------------------- panel 1
FUNNEL = [
    (n("NGaiaCensus"), "Gaia DR3 stars within 40 pc"),
    (n("NCensus"), "on the ALMA-covered work list"),
    (n("NGenuinelyCovered"), "genuinely inside a public field"),
    (n("NStars"), "searched (%s systems)" % n("NSystems")),
]
fig = plt.figure(figsize=(2.35, 2.75))
axL = fig.add_axes([0.02, 0.02, 0.96, 0.96])
axL.set_xlim(0, 1)
axL.set_ylim(0, 1)
axL.axis("off")

# left: a real funnel, width proportional to log count
FILL = ["0.90", "0.82", "0.72", "0.60"]
top, bot, gap = 0.90, 0.10, 0.022
h = (top - bot - 3 * gap) / 4.0
half = [0.46, 0.34, 0.24, 0.17]
for i, ((cnt, lab), f) in enumerate(zip(FUNNEL, FILL)):
    y1 = top - i * (h + gap)
    y0 = y1 - h
    w0, w1 = half[i], half[min(i + 1, 3)] if i < 3 else half[3] * 0.92
    poly = Polygon([(0.5 - w0, y1), (0.5 + w0, y1),
                    (0.5 + w1, y0), (0.5 - w1, y0)],
                   closed=True, facecolor=f, edgecolor="0.35", linewidth=0.6)
    axL.add_patch(poly)
    axL.text(0.5, (y0 + y1) / 2 + 0.028, cnt, ha="center", va="center",
             fontsize=8.5, fontweight="bold")
    axL.text(0.5, (y0 + y1) / 2 - 0.050, lab, ha="center", va="center",
             fontsize=5.6)
axL.text(0.5, 0.975, "Selection", ha="center", va="center", fontsize=8,
         fontstyle="italic")
axL.annotate("", xy=(0.5, 0.045), xytext=(0.5, 0.06),
             arrowprops=dict(arrowstyle="-|>", color="0.35", lw=0.7))

fig.savefig(os.path.join(OUT, "selection_funnel.pdf"),
            bbox_inches="tight", pad_inches=0.01)
print("figures/selection_funnel.pdf written (selection funnel only)")
