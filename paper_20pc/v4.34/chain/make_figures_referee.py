#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
make_figures_referee.py -- the two figures added / rebuilt in the referee
revision of the 0-40 pc ALMA technosignature paper.

USAGE
-----
    python3 make_figures_referee.py [--outdir figures] [--data PATH]

    Defaults:  --outdir  ./figures
               --data    /workspace/SETI/figwork/v331_data.json

WHAT IT WRITES
--------------
    figures/eirp_context.pdf          REBUILT, now a SINGLE panel (see below)
    figures/completeness_surface.pdf  NEW

FIGURE 1 -- eirp_context.pdf : why it lost a panel
--------------------------------------------------
The two-panel version divided each survey's EIRP threshold by its native
channel width and plotted the result in W Hz^-1, calling that the primary
"like-for-like" comparison.  A referee showed this is wrong for the class of
transmitter being searched for.  EIRP / dnu_channel is a channel-AVERAGED
equivalent spectral luminosity, appropriate only to emission that FILLS the
channel.  An unresolved narrowband carrier does not fill an ALMA channel: a
1 Hz carrier that needs 1.6e13 W of total EIRP to be detected has an intrinsic
spectral power of order 1.6e13 W Hz^-1, not the ~1e6 W Hz^-1 that the division
returns.  The old panel (a) therefore flattered ALMA by ~6-7 orders of
magnitude.  It is deleted outright; no W Hz^-1 axis appears anywhere in this
figure.  What survives is the total-power comparison: the total EIRP an
unresolved narrowband transmitter must radiate to be detected at each
instrument's own native spectral resolution.  That is the physically
meaningful quantity, and it does not flatter us.

PROVENANCE OF EVERY POINT
-------------------------
THIS SURVEY  -- recomputed here from the frozen export, deepest window per
                star, under the selection rules of survey_stats.py (band
                reconstruction, de-duplication, the physical noise-defect cut,
                the withheld eps Eri Band 6 windows).  Nothing hard-coded.
LITERATURE   -- hard-coded, each with the sentence it comes from, in LIT below.
                All four were checked against the published papers while this
                script was written; where the superseded v3.24 figure differed
                from the paper, the paper wins (see the note on Margot 2023).

FIGURE 2 -- completeness_surface.pdf : what we may and may not draw
------------------------------------------------------------------
The trial-level records of the injection campaign were NOT retained.  What
survives is prose: 1200 trials over six window configurations; the
fine-channel configuration is AU Mic's 488 kHz window with a 49-trial drift
grid; amplitudes 4, 5, 6, 8, 10 sigma; f_drift = 0, 0.25, 0.5, 0.75, 1.0 of
the searched drift ceiling; carriers with f_drift <= 0.25 are entirely
absorbed by the per-channel time-median subtraction; for f_drift >= 0.5 the
recovery is 17, 42, 58, 75, 83 per cent at 4, 5, 6, 8, 10 sigma, POOLED over
grid phase and sub-channel placement.

We therefore have FIVE numbers for FIFTEEN drifting cells.  Drawing a smooth
interpolated surface would assert twenty-five independent measurements we do
not have, so the figure is drawn as a 5x5 grid of discrete cells in which the
three drifting rows of each amplitude column carry the SAME pooled value, are
hatched, and are bracketed and labelled as pooled.  Only the two absorbed rows
and the pooled drifting class are measurements.

DENOMINATOR.  n = 24 per amplitude for the pooled drifting class, reconstructed
as 1200 trials / 6 configurations / 5 amplitudes = 40 trials per amplitude in
this configuration, of which 3 of the 5 drift rows are drifting: 40 * 3/5 = 24.
This reconstruction is corroborated by the quoted percentages themselves, which
are exactly k/24 to rounding: 4/24 = 16.7 -> 17, 10/24 = 41.7 -> 42,
14/24 = 58.3 -> 58, 18/24 = 75.0 -> 75, 20/24 = 83.3 -> 83.  Wilson 68 per cent
(z = 1) intervals are computed from those integer k.  The absorbed rows have a
reconstructed n = 16 per amplitude by the same arithmetic; they are shown as
measured zeros and no interval is drawn on them.

Author: ASTRA PA, for G. J. White.  Re-runnable; no state outside --data.
"""

from __future__ import annotations

import argparse
import collections
import itertools          # noqa: F401  (used by the exec'd survey_stats.py prologue)
import json
import math
import os
import statistics as st   # noqa: F401  (ditto)

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt   # noqa: E402
import numpy as np                # noqa: E402
from matplotlib.lines import Line2D          # noqa: E402
from matplotlib.patches import Patch, Rectangle   # noqa: E402
from matplotlib.ticker import FixedFormatter, FixedLocator, LogLocator  # noqa: E402

HERE = os.path.dirname(os.path.abspath(__file__))
DEFAULT_DATA = "/workspace/SETI/figwork/v331_data.json"
DEFAULT_OUTDIR = os.path.join(HERE, "figures")

# --------------------------------------------------------------------------------------
# literature comparison values -- HARD-CODED, one entry per published paper.
# "value" is (distance/pc, EIRP/W).  "src" is the sentence it was taken from.
# --------------------------------------------------------------------------------------
LIT = {
    "enriquez2017": dict(
        label="Enriquez+17 (GBT, 692 stars)",
        pts=[(50.0, 1.0e13)],
        src="Enriquez et al. 2017, ApJ 849, 104, abstract: 'none of the observed "
            "systems host high-duty-cycle radio transmitters ... with an Equivalent "
            "Isotropic Radiated Power of ~10^13 W ... fewer than ~0.1% of the "
            "stellar systems within 50 pc'.",
        colour="#E69F00", marker="D", size=17,
    ),
    "margot2023": dict(
        label="Margot+23 (GBT, 11,680 stars)",
        pts=[(100.0, 1.35e13), (6135.0, 5.08e16)],
        src="Margot et al. 2023, AJ 166, 206, sec. 6: 'fewer than 6.6% of the "
            "331,312 stars within 100 pc host a transmitter that is detectable in "
            "our survey (EIRP > 1.35 x 10^13 W) ... For stars located within "
            "20,000 ly, ... (EIRP > 5.08 x 10^16 W)'.  20,000 ly = 6135 pc.  NOTE: "
            "the superseded v3.24 figure plotted the near point at 1.0e13 W; the "
            "published value is 1.35e13 W and is used here.",
        colour="#00A0A0", marker="s", size=17,
    ),
    "mason2024": dict(
        label="Mason+24 (ALMA B3, 28 stars)",
        pts=[(1010.0, 6.91e17)],
        src="Mason et al. 2024, MNRAS 536, 2127, sec. 4: 'the smallest minimum "
            "detectable power ... is 6.91 x 10^17 W for the closest target star "
            "(Gaia DR3 4154920820659128192)'; that star's distance in their "
            "Table 2 is 1.010 kpc.",
        colour="#7B3EAD", marker="^", size=19,
    ),
    "price2020": dict(
        label="Price+20 deepest (GBT, Parkes)",
        # plotted as left-edge ticks: distance is not the axis variable for these
        pts=[(None, 2.0e12), (None, 9.0e12)],
        tick_names=["GBT", "Parkes"],
        src="Price et al. 2020, AJ 159, 86, abstract: 'we can put an upper limit "
            "on the power of potential radio transmitters at these frequencies at "
            "2x10^12 W, and 9x10^12 W for GBT and Parkes respectively'.  These are "
            "deepest per-target limits, not a single sample distance, so they are "
            "drawn as left-edge ticks rather than as points in distance.",
        colour="#D55E00",
    ),
}

# Reference power, not a survey limit.
ARECIBO_W = 2.0e13          # Arecibo S-band planetary radar, ~1 MW into ~10^7 gain

# Grey guide line EIRP = D2_NORM * (d/pc)^2 -- constant received flux.  The
# normalisation is inherited unchanged from the v3.24 figure (4.0e12 W at 1 pc,
# recovered from that PDF's own vector geometry, slope 2.0000).
D2_NORM = 4.0e12

# --------------------------------------------------------------------------------------
# injection campaign -- TRANSCRIBED, not derived.  See module docstring.
# --------------------------------------------------------------------------------------
INJ_AMP = [4.0, 5.0, 6.0, 8.0, 10.0]           # injected amplitude, sigma
INJ_FDRIFT = [0.0, 0.25, 0.5, 0.75, 1.0]       # fraction of the searched drift ceiling
INJ_ABSORBED_MAX_F = 0.25                      # f_drift <= this is absorbed outright
INJ_POOLED_FRAC = [0.17, 0.42, 0.58, 0.75, 0.83]   # pooled over f_drift >= 0.5
INJ_N_POOLED = 24                              # reconstructed; see docstring
INJ_N_ABSORBED = 16                            # reconstructed; shown, no interval drawn
INJ_CONFIG = "AU Mic, 488 kHz window (49-trial drift grid)"


def set_style() -> None:
    """House style of make_figures_v328.py, verbatim."""
    plt.rcParams.update({
        "font.family": "serif",
        "font.serif": ["STIXGeneral", "DejaVu Serif", "Times New Roman"],
        "mathtext.fontset": "stix",
        "font.size": 8,
        "axes.titlesize": 8.5,
        "axes.labelsize": 8,
        "xtick.labelsize": 7,
        "ytick.labelsize": 7,
        "legend.fontsize": 6.5,
        "legend.frameon": True,
        "legend.framealpha": 0.9,
        "legend.edgecolor": "0.7",
        "axes.grid": True,
        "grid.color": "0.85",
        "grid.linewidth": 0.4,
        "grid.alpha": 0.9,
        "axes.axisbelow": True,
        "axes.linewidth": 0.6,
        "xtick.major.width": 0.6,
        "ytick.major.width": 0.6,
        "xtick.minor.width": 0.4,
        "ytick.minor.width": 0.4,
        "lines.linewidth": 1.1,
        "figure.dpi": 200,
        "savefig.dpi": 200,
        "pdf.fonttype": 42,
        "ps.fonttype": 42,
        "pdf.compression": 6,
        "image.composite_image": False,
    })


def save(fig, path):
    fig.savefig(path, format="pdf")     # NO bbox_inches='tight'
    plt.close(fig)
    return path


# --------------------------------------------------------------------------------------
# survey selection -- exec the prologue of survey_stats.py so the rules cannot drift
# --------------------------------------------------------------------------------------

def survey_rows(data_path):
    """Return the list `good` exactly as survey_stats.py builds it."""
    src = open(os.path.join(HERE, "survey_stats.py")).read()
    head = src.split("S=collections.OrderedDict()")[0]
    head = head.replace("SRC='/workspace/SETI/figwork/v331_data.json'",
                        "SRC=%r" % data_path)
    ns = {"__name__": "survey_stats_prologue"}
    exec(compile(head, "survey_stats.py[prologue]", "exec"), ns)
    return ns["good"]


def deepest_per_star(good):
    best = {}
    for r in good:
        s = r["star_name"]
        if s not in best or r["eirp"] < best[s]["eirp"]:
            best[s] = r
    return best


def wilson(k, n, z=1.0):
    """Wilson score interval.  z=1 -> 68.3 per cent."""
    p = k / n
    den = 1.0 + z * z / n
    centre = (p + z * z / (2 * n)) / den
    half = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / den
    return max(0.0, centre - half), min(1.0, centre + half)


# ======================================================================================
# FIGURE 1 -- eirp_context.pdf, single panel, total power only
# ======================================================================================

def fig_eirp_context(good, outdir, report):
    best = deepest_per_star(good)
    d = np.array([r["dist_pc"] for r in best.values()])
    e = np.array([r["eirp"] for r in best.values()])
    order = np.argsort(d)
    d, e = d[order], e[order]

    report["eirp_context"] = {
        "n_windows": len(good),
        "n_stars": int(d.size),
        "d_min_pc": float(d.min()), "d_max_pc": float(d.max()),
        "eirp_min_W": float(e.min()), "eirp_max_W": float(e.max()),
        "eirp_median_W": float(np.median(e)),
        "eirp_p16_W": float(np.percentile(e, 16)),
        "eirp_p84_W": float(np.percentile(e, 84)),
        "n_stars_below_arecibo": int((e < ARECIBO_W).sum()),
        "deepest_star": min(best, key=lambda k: best[k]["eirp"]),
        "nearest_star": min(best, key=lambda k: best[k]["dist_pc"]),
    }

    fig = plt.figure(figsize=(3.4, 3.0), layout="constrained")
    fig.get_layout_engine().set(w_pad=0.012, h_pad=0.012)
    ax = fig.add_subplot(111)

    xlo, xhi = 0.75, 2.6e4
    ylo, yhi = 7e11, 6e18

    # --- guide line: constant received flux, EIRP proportional to d^2 ------------------
    xs = np.logspace(math.log10(xlo), math.log10(xhi), 64)
    ax.plot(xs, D2_NORM * xs ** 2, ls=":", lw=0.9, color="0.55", zorder=1)
    ax.text(78, D2_NORM * 78 ** 2 * 1.5, r"EIRP $\propto d^{2}$", fontsize=5.8,
            color="0.45", rotation=39, rotation_mode="anchor",
            ha="center", va="bottom", zorder=6)

    # --- Arecibo-like planetary radar --------------------------------------------------
    ax.axhline(ARECIBO_W, ls="--", lw=0.9, color="#009E73", zorder=2)
    ax.text(1.0, ARECIBO_W / 1.3, "Arecibo-like planetary radar",
            fontsize=5.4, color="#009E73", ha="left", va="top", zorder=6,
            bbox=dict(facecolor="white", edgecolor="none", alpha=0.75, pad=0.6))

    # --- this survey -------------------------------------------------------------------
    ax.scatter(d, e, s=9, marker="o", facecolor="none", edgecolor="#0072B2",
               linewidths=0.7, zorder=4,
               label="this survey: deepest window\nper star (%d stars)" % d.size)

    # --- literature --------------------------------------------------------------------
    for key in ("enriquez2017", "margot2023", "mason2024"):
        L = LIT[key]
        xs_ = [p[0] for p in L["pts"]]
        ys_ = [p[1] for p in L["pts"]]
        ax.scatter(xs_, ys_, s=L["size"], marker=L["marker"], color=L["colour"],
                   edgecolor="white", linewidths=0.35, zorder=5, label=L["label"])

    L = LIT["price2020"]
    for (_, y), nm in zip(L["pts"], L["tick_names"]):
        ax.plot([xlo, xlo * 1.55], [y, y], lw=1.4, color=L["colour"],
                solid_capstyle="butt", zorder=5)
        ax.text(xlo * 1.75, y, nm, fontsize=5.2, color=L["colour"],
                ha="left", va="center", zorder=6)

    ax.set_xscale("log")
    ax.set_yscale("log")
    ax.set_xlim(xlo, xhi)
    ax.set_ylim(ylo, yhi)
    ax.set_xlabel("distance (pc)")
    ax.set_ylabel(r"total EIRP required for detection (W)")
    ax.xaxis.set_major_locator(FixedLocator([1, 10, 100, 1000, 10000]))
    ax.xaxis.set_major_formatter(FixedFormatter(
        ["1", "10", "100", r"$10^{3}$", r"$10^{4}$"]))
    ax.xaxis.set_minor_locator(LogLocator(base=10.0, subs=tuple(range(2, 10)),
                                          numticks=40))
    ax.yaxis.set_major_locator(LogLocator(base=10.0, numticks=12))
    ax.yaxis.set_minor_locator(LogLocator(base=10.0, subs=tuple(range(2, 10)),
                                          numticks=60))
    ax.grid(True, which="major", alpha=0.9)

    handles, labels = ax.get_legend_handles_labels()
    handles.append(Line2D([], [], color=LIT["price2020"]["colour"], lw=1.4))
    labels.append(LIT["price2020"]["label"])
    leg = ax.legend(handles, labels, loc="lower right", fontsize=5.3,
                    handletextpad=0.4, borderpad=0.35, labelspacing=0.45,
                    borderaxespad=0.3, framealpha=0.92, markerscale=1.0)
    leg.get_frame().set_linewidth(0.4)

    fig.text(0.5, 0.008,
             "Total power for an unresolved carrier at each survey's native "
             "resolution; not a spectral-power density.",
             ha="center", va="bottom", fontsize=5.2, color="0.35")
    fig.get_layout_engine().set(rect=(0.0, 0.035, 1.0, 0.965))

    return save(fig, os.path.join(outdir, "eirp_context.pdf"))


# ======================================================================================
# FIGURE 2 -- completeness_surface.pdf
# ======================================================================================

def fig_completeness_surface(outdir, report):
    """Pure-vector 5x5 cell grid.  No imshow / pcolormesh: every cell, and the
    colour key itself, is a filled Rectangle, so the PDF carries no raster."""
    na, nf = len(INJ_AMP), len(INJ_FDRIFT)
    drifting = [i for i, f in enumerate(INJ_FDRIFT) if f > INJ_ABSORBED_MAX_F]
    absorbed = [i for i, f in enumerate(INJ_FDRIFT) if f <= INJ_ABSORBED_MAX_F]

    # integer numerators behind the quoted percentages (see module docstring)
    kk = [int(round(p * INJ_N_POOLED)) for p in INJ_POOLED_FRAC]
    ci = [wilson(k, INJ_N_POOLED) for k in kk]
    frac = [k / INJ_N_POOLED for k in kk]

    report["completeness_surface"] = {
        "config": INJ_CONFIG,
        "amplitudes_sigma": INJ_AMP,
        "f_drift": INJ_FDRIFT,
        "absorbed_rows": [INJ_FDRIFT[i] for i in absorbed],
        "n_pooled_per_amplitude": INJ_N_POOLED,
        "n_absorbed_per_amplitude": INJ_N_ABSORBED,
        "pooled_k": kk,
        "pooled_fraction": [round(f, 4) for f in frac],
        "quoted_percent": [round(100 * p) for p in INJ_POOLED_FRAC],
        "wilson68_percent": [(round(100 * a, 1), round(100 * b, 1)) for a, b in ci],
    }

    cmap = plt.get_cmap("viridis")

    fig = plt.figure(figsize=(3.4, 2.8), layout="constrained")
    fig.get_layout_engine().set(w_pad=0.012, h_pad=0.012, wspace=0.02)
    # reserve the bottom strip for the honesty key before any axes are placed
    fig.get_layout_engine().set(rect=(0.0, 0.175, 1.0, 0.82))  # (l, b, w, h)
    gs = fig.add_gridspec(1, 2, width_ratios=[1.0, 0.052], wspace=0.03)
    ax = fig.add_subplot(gs[0, 0])
    cax = fig.add_subplot(gs[0, 1])
    ax.grid(False)
    ax.set_axisbelow(False)

    # ---- cells ------------------------------------------------------------------------
    for i in range(nf):
        pooled = i in drifting
        for j in range(na):
            v = frac[j] if pooled else 0.0
            ax.add_patch(Rectangle((j - 0.5, i - 0.5), 1, 1, facecolor=cmap(v),
                                   edgecolor="white", linewidth=0.6, zorder=2))
            if pooled:
                ax.add_patch(Rectangle((j - 0.5, i - 0.5), 1, 1, fill=False,
                                       hatch="/////", edgecolor="white",
                                       linewidth=0.0, alpha=0.40, zorder=3))
            col = "white" if v < 0.55 else "black"
            if pooled:
                ax.text(j, i + 0.13, "%d" % round(100 * v), ha="center",
                        va="center", fontsize=6.8, color=col, zorder=5)
                lo, hi = ci[j]
                ax.text(j, i - 0.20,
                        r"$^{+%.0f}_{-%.0f}$" % (100 * hi - 100 * v,
                                                 100 * v - 100 * lo),
                        ha="center", va="center", fontsize=5.2, color=col, zorder=5)
            else:
                ax.text(j, i, "0", ha="center", va="center", fontsize=6.8,
                        color=col, zorder=5)

    # ---- the two structural annotations ------------------------------------------------
    ax.plot([-0.5, na - 0.5], [max(absorbed) + 0.5] * 2, color="#D55E00",
            lw=1.2, zorder=6, clip_on=False)
    ax.text((na - 1) / 2.0, max(absorbed) - 0.5,
            "entirely absorbed by the per-channel time-median subtraction",
            ha="center", va="center", fontsize=5.0, color="white", zorder=7,
            bbox=dict(facecolor=cmap(0.0), edgecolor="none", pad=1.2, alpha=0.9))

    # bracket spanning the three pooled rows, outside the right-hand edge
    xb = na - 0.5
    y0, y1 = min(drifting) - 0.5, max(drifting) + 0.5
    ax.plot([xb + 0.06, xb + 0.16, xb + 0.16, xb + 0.06],
            [y0 + 0.03, y0 + 0.03, y1 - 0.03, y1 - 0.03],
            color="#D55E00", lw=0.7, zorder=6, clip_on=False)
    ax.text(xb + 0.30, 0.5 * (y0 + y1), "one pooled value\nper column",
            rotation=90, ha="center", va="center", fontsize=5.2,
            color="#D55E00", zorder=6, clip_on=False)

    ax.set_xlim(-0.5, na - 0.5)
    ax.set_ylim(-0.5, nf - 0.5)
    ax.set_xticks(range(na))
    ax.set_xticklabels(["%g" % a for a in INJ_AMP])
    ax.set_yticks(range(nf))
    ax.set_yticklabels(["%g" % f for f in INJ_FDRIFT])
    ax.tick_params(length=2, width=0.5)
    ax.set_xlabel(r"injected amplitude ($\sigma$)", labelpad=1.5)
    ax.set_ylabel(r"drift fraction $f_{\rm drift}$", labelpad=1.5)
    ax.set_title("recovery fraction (per cent), %s" % INJ_CONFIG,
                 fontsize=6.2, pad=3)
    for sp in ax.spines.values():
        sp.set_linewidth(0.6)

    # ---- vector colour key --------------------------------------------------------------
    nstep = 128
    for s_ in range(nstep):
        v0, v1 = s_ / nstep, (s_ + 1) / nstep
        cax.add_patch(Rectangle((0, v0), 1, v1 - v0, facecolor=cmap(0.5 * (v0 + v1)),
                                edgecolor="none", linewidth=0))
    cax.set_xlim(0, 1)
    cax.set_ylim(0, 1)
    cax.set_xticks([])
    cax.yaxis.tick_right()
    cax.yaxis.set_label_position("right")
    cax.set_yticks([0.0, 0.25, 0.5, 0.75, 1.0])
    cax.set_yticklabels(["0", "25", "50", "75", "100"])
    cax.tick_params(labelsize=5.4, length=2, width=0.5, pad=1.5)
    cax.set_ylabel("recovery (per cent)", fontsize=5.6, labelpad=1.5)
    cax.grid(False)
    for sp in cax.spines.values():
        sp.set_linewidth(0.5)

    # ---- honesty key, in the reserved bottom strip ---------------------------------------
    handles = [
        Patch(facecolor="0.62", edgecolor="white", hatch="/////",
              label=("hatched: ONE pooled measurement per amplitude ($n=%d$), "
                     "shared by\nthe three drifting rows -- NOT %d independent cell "
                     "measurements" % (INJ_N_POOLED, len(drifting) * na)),
              linewidth=0.4),
        Patch(facecolor=cmap(0.0), edgecolor="white",
              label=("unhatched: measured zero recovery "
                     "(reconstructed $n=%d$ per amplitude)" % INJ_N_ABSORBED),
              linewidth=0.4),
    ]
    leg = fig.legend(handles=handles, loc="lower left",
                     bbox_to_anchor=(0.012, 0.048), bbox_transform=fig.transFigure,
                     fontsize=5.2, handlelength=1.4, handleheight=1.0,
                     handletextpad=0.45, labelspacing=0.4, borderpad=0.32,
                     framealpha=1.0)
    leg.get_frame().set_linewidth(0.4)

    fig.text(0.012, 0.010,
             "Trial-level records were not retained; errors are binomial Wilson "
             "68 per cent intervals on the pooled class.",
             ha="left", va="bottom", fontsize=5.0, color="0.35")

    return save(fig, os.path.join(outdir, "completeness_surface.pdf"))


# ======================================================================================

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--data", default=DEFAULT_DATA)
    ap.add_argument("--outdir", default=DEFAULT_OUTDIR)
    args = ap.parse_args()

    set_style()
    os.makedirs(args.outdir, exist_ok=True)
    report = {}

    good = survey_rows(args.data)
    p1 = fig_eirp_context(good, args.outdir, report)
    p2 = fig_completeness_surface(args.outdir, report)

    print("wrote:", p1)
    print("wrote:", p2)
    print(json.dumps(report, indent=1))
    with open(os.path.join(HERE, "figures_referee_numbers.json"), "w") as fh:
        json.dump({"figures": [p1, p2], "numbers": report,
                   "literature": {k: {"pts": v["pts"], "src": v["src"]}
                                  for k, v in LIT.items()},
                   "arecibo_reference_W": ARECIBO_W,
                   "d2_guide_norm_W_at_1pc": D2_NORM}, fh, indent=1)


if __name__ == "__main__":
    main()
