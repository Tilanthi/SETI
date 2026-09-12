#!/usr/bin/env python3
"""The combined selection-funnel and pipeline-flow figure (referees A3,
A15, B2).

One figure, two panels.  Left: the selection funnel, from the Gaia
reference census to the systems actually searched, so the three
denominators readers confuse (17,566 catalogued, ~115 genuinely covered,
88 searched) are visibly different objects.  Right: the decision flow that
turns a window into a disposition, which is the sequence the text describes
in twelve steps.

Every number on the left panel is read from the generated macro files, so
the figure cannot drift from the text.  The right panel is structural and
carries only the two counts that label its branches.

Usage: python3 make_fig_funnel.py [outdir]
"""
import glob
import os
import re
import sys

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import FancyArrowPatch, Polygon, Rectangle

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
PIPE = [
    ("%s windows" % n("NWindows"), "%s drift-resolved, %s spectral-excess"
     % (n("NWinA"), n("NWinB"))),
    ("%s crossings" % n("NHits"), r"$T_\star \geq 5$ at the stellar position"),
    ("%s stage-1 flags" % n("NSpatial"), "star exceeds all %s controls"
     % n("NCtrl")),
    ("%s candidates" % n("NCandidates"), "after line, recurrence and null checks"),
]

fig = plt.figure(figsize=(7.1, 1.78))
axL = fig.add_axes([0.035, 0.06, 0.435, 0.86])
axR = fig.add_axes([0.545, 0.06, 0.435, 0.86])
for ax in (axL, axR):
    ax.set_xlim(0, 1)
    ax.set_ylim(0, 1)
    ax.axis("off")

# left: a real funnel, width proportional to log count
FILL = ["0.90", "0.82", "0.72", "0.60"]
top, bot, gap = 0.90, 0.06, 0.022
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
    axL.text(0.5, (y0 + y1) / 2 + 0.030, cnt, ha="center", va="center",
             fontsize=9, fontweight="bold")
    axL.text(0.5, (y0 + y1) / 2 - 0.048, lab, ha="center", va="center",
             fontsize=6.6)
axL.text(0.5, 0.975, "Selection", ha="center", va="center", fontsize=8,
         fontstyle="italic")
axL.annotate("", xy=(0.5, 0.045), xytext=(0.5, 0.06),
             arrowprops=dict(arrowstyle="-|>", color="0.35", lw=0.7))

# right: the decision flow
axR.text(0.5, 0.975, "Decision flow", ha="center", va="center", fontsize=8,
         fontstyle="italic")
bh = 0.135
bgap = (0.90 - 0.06 - 4 * bh) / 3.0
for i, (head, sub) in enumerate(PIPE):
    y1 = 0.90 - i * (bh + bgap)
    axR.add_patch(Rectangle((0.06, y1 - bh), 0.88, bh, facecolor="0.94",
                            edgecolor="0.35", linewidth=0.6))
    axR.text(0.5, y1 - bh * 0.36, head, ha="center", va="center",
             fontsize=8, fontweight="bold")
    axR.text(0.5, y1 - bh * 0.76, sub, ha="center", va="center", fontsize=6.4)
    if i < 3:
        axR.add_patch(FancyArrowPatch((0.5, y1 - bh), (0.5, y1 - bh - bgap),
                                      arrowstyle="-|>", mutation_scale=7,
                                      color="0.35", lw=0.7))
GATES = ["spatial screen", "excluded frequency regions",
         "vetting, recurrence, local null"]
for i, g in enumerate(GATES):
    y = 0.90 - (i + 1) * bh - (i + 0.5) * bgap
    axR.text(0.535, y, g, ha="left", va="center", fontsize=6.2,
             fontstyle="italic", color="0.25")

fig.savefig(os.path.join(OUT, "selection_funnel.pdf"),
            bbox_inches="tight", pad_inches=0.01)
print("figures/selection_funnel.pdf written")
