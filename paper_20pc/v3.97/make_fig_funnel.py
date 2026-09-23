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
# Referee: the right panel should be the experiment itself, step by step,
# with the survivor count at each step, and should match the summary
# subsection at the end of the methodology section line for line. Every
# count is read from the macros, so the two cannot drift.
STEPS = [
    ("Public execution blocks toward the target list", n("LedProgenitor"), "blocks"),
    ("Delivered with a usable calibration, processed uniformly", n("LedProcessed"), "blocks"),
    ("Retained after the pre-registered hold-out (%s withheld)" % n("LedHoldout"),
     n("LedCatalogue"), "blocks"),
    ("Spectral windows in the science sample", n("NWindows"), "windows"),
    ("Fine-channel, drift-resolving (Class A)", n("NWinA"), "windows"),
    (r"Threshold crossings at the stellar position, $T_\star\geq5$", n("NHits"), "crossings"),
    ("Rank-first against all %s spatial controls" % n("NCtrl"), n("NStageOneWin"), "windows"),
    ("Still rank-first under radius correction", n("LocAllFlagLocal"), "windows"),
    ("Localised at the star in the visibilities (stage 2)",
     n("NStageLocalised"), "windows"),
    ("Without an astrophysical attribution", n("NStageOneUnattrib"),
     "events"),
    ("Independently confirmed by recurrence or second epoch",
     n("NCandidates"), "confirmed"),
]

fig = plt.figure(figsize=(7.1, 2.75))
axL = fig.add_axes([0.030, 0.06, 0.300, 0.86])
axR = fig.add_axes([0.355, 0.06, 0.635, 0.86])
for ax in (axL, axR):
    ax.set_xlim(0, 1)
    ax.set_ylim(0, 1)
    ax.axis("off")

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

# right: the experiment as a ten-step ledger, survivors at every step
axR.text(0.5, 0.975, "The experiment, step by step", ha="center", va="center",
         fontsize=8, fontstyle="italic")
NS = len(STEPS)
rtop, rbot = 0.925, 0.03
rh = (rtop - rbot) / NS
# Shade the three regimes the steps fall into, so the eye can see where the
# experiment stops assembling data and starts testing it.
# The bands must follow the list, not a hard-coded length: adding the
# localisation stage left step 11 outside every band.
# R1-11 (v3.97): three fundamentally different operations, named as the
# referee asked, so that the figure itself shows the spatial rank
# selecting what is inspected rather than establishing anything.
REGIME = [(0, 5, "0.955", "data selection"),
          (5, 8, "0.90", "automated\ncandidate generation"),
          (8, NS, "0.975", "physical validation")]
for i0, i1, col, lab in REGIME:
    axR.add_patch(Rectangle((0.055, rtop - i1 * rh), 0.93, (i1 - i0) * rh,
                            facecolor=col, edgecolor="0.55", linewidth=0.5,
                            zorder=0))
    # Regime labels go in their own left margin, rotated: on the same line
    # as a step they collided with its text.
    axR.text(0.030, rtop - (i0 + i1) / 2.0 * rh, lab, ha="center",
             va="center", fontsize=5.8, fontstyle="italic", color="0.45",
             rotation=90, zorder=3)
for i, (lab, cnt, unit) in enumerate(STEPS):
    yc = rtop - (i + 0.5) * rh
    axR.text(0.115, yc, "%d." % (i + 1), ha="right", va="center", fontsize=6.4,
             color="0.45", zorder=4)
    axR.text(0.132, yc, lab, ha="left", va="center", fontsize=6.6, zorder=4)
    axR.text(0.880, yc, cnt, ha="right", va="center", fontsize=8,
             fontweight="bold", zorder=4)
    axR.text(0.890, yc, unit, ha="left", va="center", fontsize=5.6,
             color="0.40", zorder=4)
    if i < NS - 1:
        # heavier rules at the two operation boundaries (5 and 8), so the
        # eye sees three blocks rather than eleven equal steps
        heavy = (i + 1) in (5, 8)
        axR.plot([0.055, 0.985], [rtop - (i + 1) * rh] * 2,
                 color=("0.25" if heavy else "0.80"),
                 lw=(1.1 if heavy else 0.4), zorder=2)

fig.savefig(os.path.join(OUT, "selection_funnel.pdf"),
            bbox_inches="tight", pad_inches=0.01)
# The step count is drawn from the list, so the caption and the S5 summary
# must read it from here rather than spelling it out: the caption said
# "ten steps" against eleven drawn until v3.97.
WORDS = {9: 'nine', 10: 'ten', 11: 'eleven', 12: 'twelve',
         13: 'thirteen', 14: 'fourteen'}
with open(os.path.join(HERE, 'funnel_steps.tex'), 'w') as fh:
    fh.write('%% generated by make_fig_funnel.py -- do not edit\n')
    fh.write('\\newcommand{\\NFunnelSteps}{%d}\n' % NS)
    fh.write('\\newcommand{\\NFunnelStepsWord}{%s}\n'
             % WORDS.get(NS, str(NS)))

print("figures/selection_funnel.pdf written; %d steps -> funnel_steps.tex"
      % NS)
