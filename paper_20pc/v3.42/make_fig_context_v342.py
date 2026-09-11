#!/usr/bin/env python3
# v3.42 page-trim variant: Figure 1 panels side by side, fonts rescaled for 1:1
# placement at full text width.  Science content identical to v3.31.
# -*- coding: utf-8 -*-
"""
make_figures_referee_v331.py -- a MODIFIED COPY of make_figures_referee.py for
the SECOND referee round of the 0-40 pc ALMA technosignature paper.

WHAT CHANGED FROM make_figures_referee.py
-----------------------------------------
Only fig_eirp_context().  Referee 2: a plot of EIRP against distance still
invites a sensitivity comparison that hides the enormous difference in native
channel width between an Hz-resolution single-dish backend and an ALMA
correlator, and asks that channel width be exposed graphically.  Every survey
in the figure now carries its native channel width twice over: as a direct
annotation beside its own points, and in its legend entry.  The span is about
seven decades, 2.79 Hz to 31.25 MHz, and the figure now says so.

Nothing else moves: same 3.4 x 3.0 in single-column geometry, same literature
points, same EIRP proportional to d^2 guide, same Arecibo reference line, and
still no W/Hz axis anywhere.  fig_completeness_surface() is carried over
unchanged (and unused by the referee-2 driver) so this file stays a faithful
copy of its parent.

USAGE
-----
    python3 make_figures_referee_v331.py [--outdir figures] [--data PATH]

    Defaults:  --outdir  ./figures
               --data    /workspace/SETI/figwork/v331_data.json

WHAT IT WRITES
--------------
    figures/eirp_context.pdf          REBUILT, now a SINGLE panel (see below)
    figures/completeness_surface.pdf  NEW

FIGURE 1 -- eirp_context.pdf : why it lost a panel
--------------------------------------------------
ROUND-9 REDESIGN (referee R3-7, Option A adopted): the figure is now TWO
panels.  (a) total-power threshold vs distance, as before but WITHOUT the
symbol-size channel-width encoding -- its in-panel width labels ("2.8 Hz",
"3.0 Hz", "30.5 kHz") collided with the legend at final size (referee
R4-B), and panel (b) now carries that information on a real axis.  (b)
native channel width vs observing frequency: every searched window of this
survey plus the four literature programmes as horizontal segments, so the
~10^7 resolution span between Hz-resolution radio surveys and ALMA
correlator channels is the panel's subject rather than a symbol-size
convention.  Literature observing bands are hard-coded in LIT with their
sources (freq_src), checked against the papers' own titles/sections.
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
import decimal
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
DEFAULT_DATA = os.path.join(HERE, "frozen_export_v3.31.json")  # v3.42: local copy;
# byte-identical to /workspace/SETI/figwork/v331_data.json, so the generator chain
# runs from this folder alone.
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
        chan_Hz=2.79, chan_label="2.8 Hz",
        chan_src="Enriquez et al. 2017 abstract: data 'channelized into narrowband "
                 "(3 Hz) channels'; the Breakthrough Listen high-spectral-resolution "
                 "product they search is 2.79 Hz (Lebofsky et al. 2019, Table 4).",
        freq_GHz=(1.10, 1.90),
        freq_src="Enriquez et al. 2017, title: '1.1-1.9 GHz Observations of 692 Stars'.",
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
        chan_Hz=2.98, chan_label="3.0 Hz",
        chan_src="Margot et al. 2023, sec. 4: 'we computed power spectra with the "
                 "FFTW library ... and a transform length of 2^20, yielding a "
                 "frequency resolution Delta f = 2.98 Hz'.  Their detectability "
                 "statement assumes a transmitter bandwidth < 3 Hz.",
        freq_GHz=(1.15, 1.73),
        freq_src="Margot et al. 2023, title: '... with the Green Bank Telescope at 1.15-1.73 GHz'.",
        colour="#00A0A0", marker="s", size=17,
    ),
    "mason2024": dict(
        label="Mason+24 (ALMA B3, 28 stars)",
        pts=[(1010.0, 6.91e17)],
        src="Mason et al. 2024, MNRAS 536, 2127, sec. 4: 'the smallest minimum "
            "detectable power ... is 6.91 x 10^17 W for the closest target star "
            "(Gaia DR3 4154920820659128192)'; that star's distance in their "
            "Table 2 is 1.010 kpc.",
        chan_Hz=30.52e3, chan_label="30.5 kHz",
        chan_src="Mason et al. 2024, sec. 3: 'The data were correlated with 3840 "
                 "frequency points, each channel being 30.52 kHz wide'; that same "
                 "delta-nu enters their EIRP_min = 4 pi d^2 S_min delta-nu.  Their "
                 "archive selection required delta-nu < 35 kHz.",
        freq_GHz=(84.0, 116.0),
        freq_src="Mason et al. 2024: ALMA Band 3 (84-116 GHz) archive selection, delta-nu < 35 kHz.",
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
        chan_Hz=2.79, chan_label="2.8 Hz",
        chan_src="Price et al. 2020, sec. 3: 'we use the turboSETI incoherent "
                 "dedoppler code ... to search our high-resolution (~2.79 Hz) "
                 "Stokes-I data'.  The Parkes recorder produces the same 2.79 Hz "
                 "resolution (Price et al. 2018, PASA 35, e041).",
        freq_GHz=(1.10, 3.45),
        freq_src="Price et al. 2020, title: 'Observations of 1327 Nearby Stars Over 1.10-3.45 GHz' (GBT L+S 1.1-2.8 GHz; Parkes 1.23-1.53 GHz).",
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
        "font.size": 10.56,
        "axes.titlesize": 11.22,
        "axes.labelsize": 10.56,
        "xtick.labelsize": 9.24,
        "ytick.labelsize": 9.24,
        "legend.fontsize": 8.58,
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
    # v3.42: tight bbox for the side-by-side Fig. 1 so no label is clipped.
    fig.savefig(path, format="pdf", bbox_inches="tight", pad_inches=0.012)
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

def _chan_label(hz, sig=4):
    """15625000.0 -> '15.63 MHz';  15258.789 -> '15.26 kHz';  2.79 -> '2.79 Hz'.
    Rounds half away from zero, so 15.625 MHz prints 15.63 as elsewhere in the
    paper, not the 15.62 that IEEE round-half-even would give."""
    for scale, unit in ((1e6, "MHz"), (1e3, "kHz"), (1.0, "Hz")):
        if hz >= scale:
            v = decimal.Decimal(repr(hz / scale))
            q = v.scaleb(-(v.adjusted() - (sig - 1))).quantize(
                decimal.Decimal(1), rounding=decimal.ROUND_HALF_UP)
            v = q.scaleb(v.adjusted() - (sig - 1)).normalize()
            return "%s %s" % (v if v == v.to_integral() and v.adjusted() < sig
                              else v, unit)
    return "%.3g Hz" % hz


def _chan_sym_diam(hz):
    """Symbol DIAMETER (points) scaling with log10 of the native channel width,
    so the ~7-decade resolution gap between Hz-resolution programmes and ALMA's
    correlator is carried by the symbol size itself, not only by annotations.
    2.8 Hz -> 2.9 pt; 30 kHz -> 7.7 pt; 15.6 MHz -> 10.8 pt."""
    return 1.8 + 1.15 * max(0.0, math.log10(hz) + 0.5)


def fig_eirp_context(good, outdir, report):
    """Two panels (round-9 redesign, referee R3-7 Option A).
    (a) total-power trigger threshold vs distance.
    (b) native channel width vs observing frequency, every searched window,
        plus the literature programmes as horizontal segments."""
    best = deepest_per_star(good)
    d = np.array([r["dist_pc"] for r in best.values()])
    e = np.array([r["eirp"] for r in best.values()])
    fine_star = np.array([best[k]["res_x"] == "fine" for k in best])
    order = np.argsort(d)
    d, e, fine_star = d[order], e[order], fine_star[order]

    # ---- native channel width of THIS survey: derived, never typed --------------------
    cw = np.array([r["chanw"] for r in good])
    cw_med, cw_lo, cw_hi = float(np.median(cw)), float(cw.min()), float(cw.max())
    lit_hz = [LIT[k]["chan_Hz"] for k in LIT]
    span_dex = math.log10(max(lit_hz + [cw_hi]) / min(lit_hz + [cw_lo]))

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
        "chanw_median_Hz": cw_med, "chanw_min_Hz": cw_lo, "chanw_max_Hz": cw_hi,
        "chanw_median_label": _chan_label(cw_med),
        "chanw_range_label": "%s--%s" % (_chan_label(cw_lo), _chan_label(cw_hi)),
        "literature_channel_Hz": {k: LIT[k]["chan_Hz"] for k in LIT},
        "literature_freq_GHz": {k: LIT[k]["freq_GHz"] for k in LIT},
        "channel_width_span_dex": round(span_dex, 2),
    }

    fig = plt.figure(figsize=(7.05, 2.95), layout="constrained")
    fig.get_layout_engine().set(w_pad=0.012, h_pad=0.012)
    gs = fig.add_gridspec(1, 2, width_ratios=[1.08, 1.0], wspace=0.02)
    ax = fig.add_subplot(gs[0, 0])
    axb = fig.add_subplot(gs[0, 1])

    xlo, xhi = 0.75, 2.6e4
    ylo, yhi = 7e11, 6e18

    # --- panel (a) guide line: constant received flux, EIRP proportional to d^2 --------
    xs = np.logspace(math.log10(xlo), math.log10(xhi), 64)
    ax.plot(xs, D2_NORM * xs ** 2, ls=":", lw=0.9, color="0.55", zorder=1)
    ax.text(78, D2_NORM * 78 ** 2 * 1.5, r"EIRP $\propto d^{2}$", fontsize=7.66,
            color="0.45", rotation=39, rotation_mode="anchor",
            ha="center", va="bottom", zorder=6)

    # --- Arecibo-like planetary radar: a power scale, not a model ----------------------
    ax.axhline(ARECIBO_W, ls="--", lw=0.9, color="#009E73", zorder=2)
    # single line, offset right of the Price tick labels (which end near
    # x = 3 pc) so the two never collide at final size
    ax.text(1.0, ARECIBO_W * 1.18, "Arecibo-like planetary radar",
            fontsize=6.86, color="#009E73", ha="left", va="bottom", zorder=6,
            bbox=dict(facecolor="white", edgecolor="none", alpha=0.75, pad=0.6))

    # --- this survey: deepest window per star, by channelisation class ------------------
    ax.scatter(d[~fine_star], e[~fine_star], s=12, marker="v",
               facecolor="none", edgecolor="#56B4E9", linewidths=0.7, zorder=4,
               label="this survey: deepest window Class B (%d)" % int((~fine_star).sum()))
    ax.scatter(d[fine_star], e[fine_star], s=14, marker="o",
               facecolor="#0072B2", edgecolor="none", alpha=0.85, zorder=4,
               label="this survey: deepest window Class A (%d)" % int(fine_star.sum()))
    flag = {"bet Pic", "CP-72 2713", "HD 48370"}
    sub = [best[k] for k in best if k in flag]
    ax.scatter([r["dist_pc"] for r in sub], [r["eirp"] for r in sub],
               s=30, marker="*", color="k", zorder=5, label="flagged window")

    # --- literature thresholds, uniform symbol size (widths live in panel b) -----------
    for key in ("enriquez2017", "margot2023", "mason2024"):
        L = LIT[key]
        ax.scatter([p[0] for p in L["pts"]], [p[1] for p in L["pts"]],
                   s=L["size"], marker=L["marker"], color=L["colour"],
                   edgecolor="white", linewidths=0.35, zorder=5, label=L["label"])
    L = LIT["price2020"]
    for (_, y), nm in zip(L["pts"], L["tick_names"]):
        ax.plot([xlo, xlo * 1.55], [y, y], lw=1.4, color=L["colour"],
                solid_capstyle="butt", zorder=5)
        ax.text(xlo * 1.75, y, nm, fontsize=6.86, color=L["colour"],
                ha="left", va="center", zorder=6)

    ax.set_xscale("log")
    ax.set_yscale("log")
    ax.set_xlim(xlo, xhi)
    ax.set_ylim(ylo, yhi)
    ax.set_xlabel("distance (pc)", labelpad=1.0)
    ax.set_ylabel("total EIRP required for detection (W)\n(nominal, not completeness-corrected)", labelpad=1.5)
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
    leg = ax.legend(handles, labels, loc="lower right", fontsize=6.86,
                    handletextpad=0.4, borderpad=0.35, labelspacing=0.45,
                    borderaxespad=0.3, framealpha=0.92, markerscale=1.0)
    leg.get_frame().set_linewidth(0.4)

    # ================= panel (b): native channel width vs frequency ====================
    fc = np.array([0.5 * (r["flo"] + r["fhi"]) for r in good])
    cww = np.array([r["chanw"] for r in good])
    fm = np.array([r["res_x"] == "fine" for r in good])
    axb.scatter(fc[fm], cww[fm], s=4.2, marker="o", facecolor="#0072B2",
                edgecolor="none", alpha=0.5, zorder=4)
    axb.scatter(fc[~fm], cww[~fm], s=7, marker="v", facecolor="none",
                edgecolor="0.55", linewidths=0.45, zorder=3)
    for key in ("enriquez2017", "margot2023", "price2020", "mason2024"):
        L = LIT[key]
        axb.plot(L["freq_GHz"], [L["chan_Hz"]] * 2, lw=1.8, color=L["colour"],
                 solid_capstyle="butt", zorder=5)

    # in-panel tags.  The three Hz-resolution programmes pile into the lower
    # left corner (x = 1.1-3.45 GHz, y ~ 3 Hz); their tags stack in the empty
    # region below the survey's 84 GHz edge, with thin leaders to segments.
    for key, ty, lab in (("price2020", 1.0e6, "Price+20  2.79 Hz"),
                         ("enriquez2017", 1.0e5, "Enriquez+17  2.79 Hz"),
                         ("margot2023", 1.0e4, "Margot+23  2.98 Hz")):
        L = LIT[key]
        axb.text(1.05, ty, lab, fontsize=6.86, color=L["colour"],
                 ha="left", va="center", zorder=7)
        axb.plot([4.5, L["freq_GHz"][1] * 1.02], [ty * 0.72, L["chan_Hz"] * 1.18],
                 lw=0.45, color=L["colour"], alpha=0.75, zorder=6)
    axb.text(6.5, 3.2e2, "Mason+24  30.5 kHz", fontsize=6.86,
             color=LIT["mason2024"]["colour"], ha="left", va="center", zorder=7)
    axb.plot([34.0, 105.0], [5.0e2, 2.5e4], lw=0.45,
             color=LIT["mason2024"]["colour"], alpha=0.75, zorder=6)

    # this-survey key, in the empty band between the fine and coarse channels
    axb.text(1.05, 8.0e6,
             "this survey, all %d windows:  filled Class A, open Class B"
             % len(good),
             fontsize=6.86, color="0.25", ha="left", va="center", zorder=7)

    # resolution-span bracket, far right, in the empty x > 500 GHz margin
    axb.annotate("", xy=(672.0, 3.2e7), xytext=(672.0, 3.0),
                 arrowprops=dict(arrowstyle="<->", lw=0.7, color="0.35"))
    axb.text(628.0, 3.0e3, r"$\Delta\log\Delta\nu_{\rm ch}\!\approx\!7$",
             fontsize=6.86, color="0.35", ha="center", va="center",
             rotation=90, zorder=7)

    axb.set_xscale("log")
    axb.set_yscale("log")
    axb.set_xlim(0.9, 700.0)
    axb.set_ylim(0.8, 1.2e8)
    axb.set_xlabel("observing frequency (GHz)", labelpad=1.0)
    axb.set_ylabel("native channel width (Hz)")
    axb.xaxis.set_major_locator(FixedLocator([1, 10, 100, 500]))
    axb.xaxis.set_major_formatter(FixedFormatter(["1", "10", "100", "500"]))
    axb.xaxis.set_minor_locator(LogLocator(base=10.0, subs=tuple(range(2, 10)),
                                           numticks=40))
    axb.yaxis.set_major_locator(LogLocator(base=10.0, numticks=9))
    axb.yaxis.set_minor_locator(LogLocator(base=10.0, subs=tuple(range(2, 10)),
                                           numticks=60))
    axb.grid(True, which="major", alpha=0.9)

    fig.text(0.5, 0.008,
             "Total power for an unresolved carrier at each survey's native "
             "resolution; not a spectral-power density.\nNative resolutions "
             "span %.0f decades across the surveys plotted -- the subject of "
             "panel (b)." % span_dex,
             ha="center", va="bottom", fontsize=6.86, color="0.35",
             linespacing=1.35)
    fig.get_layout_engine().set(rect=(0.0, 0.085, 1.0, 0.915))

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
                        ha="center", va="center", fontsize=6.86, color=col, zorder=5)
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
            rotation=90, ha="center", va="center", fontsize=6.86,
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
                     fontsize=6.86, handlelength=1.4, handleheight=1.0,
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
    p2 = p1  # completeness_surface is not used in v3.42

    print("wrote:", p1)
    
    print(json.dumps(report, indent=1))
    with open(os.path.join(HERE, "figures_referee_numbers.json"), "w") as fh:
        json.dump({"figures": [p1, p2], "numbers": report,
                   "literature": {k: {"pts": v["pts"], "src": v["src"]}
                                  for k, v in LIT.items()},
                   "arecibo_reference_W": ARECIBO_W,
                   "d2_guide_norm_W_at_1pc": D2_NORM}, fh, indent=1)


if __name__ == "__main__":
    main()
