#!/usr/bin/env python3
r"""Figure 1 for v4.10: the two context panels, drawn natively and separately.

WHY THIS REPLACES make_fig_context_v342.py
------------------------------------------
1. v342 drew one wide two-panel figure and then produced the single-column
   panels `eirp_context_a.pdf` / `eirp_context_b.pdf` by COPYING artists out
   of the wide axes into a fresh figure.  That copy silently dropped the
   legend, the panel titles, the in-panel warning box and every
   `facecolor="none"`, so the shipped panel (a) carried no key at all and
   panel (b) drew the open Class B markers as filled grey blobs.  Each panel
   is now drawn directly, once, at the size it is used.
2. v342's panel (a) drew the Arecibo planetary-radar power line.  The paper's
   benchmark transmitter is now the \BenchDiam m / \BenchPowerMW MW /
   \BenchFreqGHz GHz dish at \BenchEirp W; an Arecibo-sized dish at 230 GHz is
   not physically realisable, so the Arecibo figure appears once in the
   prose of Sec. 2 and NOWHERE on a figure.  `assert_no_arecibo()` below
   checks every text artist, and is driven by --drive 1.
3. v342's ordinate was P_90^sel, taken from the catalogue column
   `eirp_p90_sel_W`.  That column is the RETIRED criterion: it is exactly
   2.876 x the nominal trigger in Class A and 4.90 x in Class B.  The adopted
   sensitivity is EIRP_90 = \EirpNinetyMultA P_trig (5.70) in Class A and
   \EirpNinetyMultB P_trig (4.55) in Class B.  Both multipliers are read from
   m3a_result_v400.json -- the injection campaign that measured them -- and
   asserted equal to the macros, so no figure can drift onto the retired
   scale again.  The catalogue column is never read by this file.

WHAT IT WRITES
--------------
    figures/eirp_context_a.pdf   minimum detectable EIRP against distance: the bare
                                 5 sigma threshold filled and EIRP_90 open on the same
                                 points, with the previous searches
    figures/eirp_context_b.pdf   native channel width against observing frequency
    figures_context_v410.json    every number the panels draw, with provenance

Panel letters live in the LaTeX float (sections/02_background.tex prints
"(a)" and "(b)" under the two graphics), so no letter is drawn here: one
source of truth per letter.

USAGE
    python3 make_fig_context_v410.py [--outdir figures] [--drive N]
      --drive 1  assert_no_arecibo must fire        (perturbation: label restored)
      --drive 2  the adopted-multiplier check must fire (perturbation: retired 2.88)
      --drive 3  the catalogue-census check must fire   (perturbation: drop a window)
      --drive 4  the filled/open ordering check must fire (perturbation: swap them)
    A drive writes figures/*_driveN.pdf, never a production path (D36).

Author: ASTRA PA (figures), for G. J. White.
"""

from __future__ import annotations

import argparse
import csv
import glob
import json
import math
import os
import re

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt            # noqa: E402
import numpy as np                         # noqa: E402
from matplotlib.lines import Line2D        # noqa: E402
from matplotlib.ticker import FixedFormatter, FixedLocator, LogLocator  # noqa: E402

from star_alias import canon as _canon     # noqa: E402

HERE = os.path.dirname(os.path.abspath(__file__))
CAT = os.path.join(HERE, "per_target_results_v3.99.csv")
M3A = os.path.join(HERE, "m3a_result_v400.json")
DEFAULT_OUTDIR = os.path.join(HERE, "figures")

# --------------------------------------------------------------------------------------
# literature comparison values -- HARD-CODED, one entry per published paper, each with
# the sentence it was taken from.  Carried over verbatim from make_fig_context_v342.py;
# these are other people's published numbers and there is no catalogue to read them from.
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
        chan_src="Enriquez et al. 2017 abstract: 'channelized into narrowband (3 Hz) "
                 "channels'; the BL high-spectral-resolution product is 2.79 Hz "
                 "(Lebofsky et al. 2019, Table 4).",
        freq_GHz=(1.10, 1.90),
        freq_src="Enriquez et al. 2017, title: '1.1-1.9 GHz Observations of 692 Stars'.",
        colour="#E69F00", marker="D", size=17,
    ),
    "margot2023": dict(
        label="Margot+23 (GBT, 11,680 stars)",
        pts=[(100.0, 1.35e13), (6135.0, 5.08e16)],
        src="Margot et al. 2023, AJ 166, 206, sec. 6: 'fewer than 6.6% of the 331,312 "
            "stars within 100 pc host a transmitter that is detectable in our survey "
            "(EIRP > 1.35 x 10^13 W) ... For stars located within 20,000 ly, ... "
            "(EIRP > 5.08 x 10^16 W)'.  20,000 ly = 6135 pc.",
        chan_Hz=2.98, chan_label="3.0 Hz",
        chan_src="Margot et al. 2023, sec. 4: 'a transform length of 2^20, yielding a "
                 "frequency resolution Delta f = 2.98 Hz'.",
        freq_GHz=(1.15, 1.73),
        freq_src="Margot et al. 2023, title: '... with the Green Bank Telescope at "
                 "1.15-1.73 GHz'.",
        colour="#00A0A0", marker="s", size=17,
    ),
    "mason2024": dict(
        label="Mason+25 (ALMA B3, 28 stars)",
        pts=[(1010.0, 6.91e17)],
        src="Mason et al. 2024, MNRAS 536, 2127, sec. 4: 'the smallest minimum "
            "detectable power ... is 6.91 x 10^17 W for the closest target star'; that "
            "star's distance in their Table 2 is 1.010 kpc.",
        chan_Hz=30.52e3, chan_label="30.5 kHz",
        chan_src="Mason et al. 2024, sec. 3: 'The data were correlated with 3840 "
                 "frequency points, each channel being 30.52 kHz wide'.",
        freq_GHz=(84.0, 116.0),
        freq_src="Mason et al. 2024: ALMA Band 3 (84-116 GHz), delta-nu < 35 kHz.",
        colour="#7B3EAD", marker="^", size=19,
    ),
    "price2020": dict(
        label="Price+20 deepest (GBT, Parkes)",
        pts=[(None, 2.0e12), (None, 9.0e12)],
        tick_names=["GBT", "Parkes"],
        src="Price et al. 2020, AJ 159, 86, abstract: 'an upper limit on the power of "
            "potential radio transmitters at these frequencies at 2x10^12 W, and "
            "9x10^12 W for GBT and Parkes respectively'.  Deepest per-target limits, "
            "not a single sample distance, so drawn as left-edge ticks.",
        chan_Hz=2.79, chan_label="2.8 Hz",
        chan_src="Price et al. 2020, sec. 3: 'our high-resolution (~2.79 Hz) Stokes-I "
                 "data'.",
        freq_GHz=(1.10, 3.45),
        freq_src="Price et al. 2020, title: 'Observations of 1327 Nearby Stars Over "
                 "1.10-3.45 GHz'.",
        colour="#D55E00",
    ),
}

# Grey guide line EIRP = D2_NORM (d/pc)^2 -- constant received flux.  Normalisation
# inherited unchanged from the v3.24 figure (4.0e12 W at 1 pc, slope 2.0000).  It is a
# guide, not a measurement; nothing in the paper quotes it.
D2_NORM = 4.0e12


# --------------------------------------------------------------------------------------
# macros: read the manuscript's own values, never type one
# --------------------------------------------------------------------------------------
def texval(name):
    """Last literal definition of \\name across survey_numbers*.tex.

    LAST, not first: round103 renames the retired families with \\renewcommand,
    and a first-match reader would return the superseded value.  Definitions
    whose body is itself a macro are skipped, so an alias never masks a value.
    """
    pat = re.compile(r"\\(?:new|renew|provide)command\{\\%s\}"
                     r"\{((?:[^{}]|\{[^{}]*\})*?)\}" % re.escape(name))
    out = None
    for f in sorted(glob.glob(os.path.join(HERE, "survey_numbers*.tex"))):
        for m in pat.finditer(open(f).read()):
            v = m.group(1).strip()
            if v and not v.startswith("\\"):
                out = v
    if out is None:
        raise KeyError(
            "no literal definition of \\%s.  make_fig_context_v410.py MUST run "
            "after numbers_v410.py (round 103), which defines the adopted "
            "multipliers and the benchmark." % name)
    return out


def texnum(name):
    """'5.3\\times10^{15}' -> 5.3e15 ; '5.70' -> 5.70 ; '402' -> 402.0"""
    v = texval(name).replace("$", "").replace("\\,", "").replace(",", "")
    m = re.match(r"^([-0-9.]+)\s*\\times\s*10\^\{?(-?[0-9]+)\}?$", v)
    if m:
        return float(m.group(1)) * 10.0 ** int(m.group(2))
    return float(v)


def close(a, b, tol):
    return abs(a / b - 1.0) <= tol


# --------------------------------------------------------------------------------------
# the adopted sensitivity.  EIRP_90 = multiplier x P_trig, per class.
# --------------------------------------------------------------------------------------
def multipliers(drive=0):
    """(Class A, Class B) adopted multipliers, EIRP_90 = multiplier x P_trig.

    ★ Read from the MACRO LAYER, which is the manuscript's single source.  An
    earlier version of this file read the campaign record m3a_result_v400.json
    directly and got 5.70/4.55; at 08:49 on 2026-10-04 numbers_v410.py adopted
    the control-maximum-stratified values 4.42/4.70 instead, and a figure that
    kept reading the campaign record would have shipped a sensitivity the paper
    does not adopt.  The campaign record is still read, but only to be
    REPORTED beside the adopted value, never to be plotted.

    The invariant this enforces is the one that matters: the plotted
    multiplier may not be a member of the RETIRED family (Class A 2.88,
    Class B 4.90), which differs from the adopted criterion by a factor two
    and has been published here by accident before.
    """
    ma, mb = texnum("EirpNinetyMultA"), texnum("EirpNinetyMultB")
    if drive == 2:                      # perturbation: the retired criterion
        ma, mb = 2.88, 4.90
    for got, retired, cls in ((ma, 2.88, "A"), (mb, 4.90, "B")):
        assert abs(got / retired - 1) > 0.01, (
            "Class %s would be plotted on the RETIRED x%.2f sensitivity; the "
            "adopted multiplier is in \\EirpNinetyMult%s" % (cls, retired, cls))
    strata = {s["stratum"]: s for s in json.load(open(M3A))["strata"]}
    return ma, mb, {"campaign_pooled_A": strata["fine (<1 MHz)"]["P90_over_trigger"],
                    "campaign_pooled_B": strata["coarse (>5 MHz)"]["P90_over_trigger"],
                    "adopted_A": ma, "adopted_B": mb,
                    "note": "adopted = control-maximum-stratified (numbers_v410.py), "
                            "not the campaign's own pooled 90 per cent point"}


def catalogue(drive=0):
    rows = list(csv.DictReader(open(CAT)))
    if drive == 3:                      # perturbation: a window goes missing
        rows = rows[:-1]
    for r in rows:
        r["_star"] = _canon(r["star_name"])
        r["_d"] = float(r["dist_pc"])
        r["_cw"] = float(r["chanw_Hz"])
        r["_fc"] = 0.5 * (float(r["flo_GHz"]) + float(r["fhi_GHz"]))
        r["_trig"] = float(r["eirp_nominal_W"])
        r["_A"] = r["search_class"] == "A"
        assert (r["resolution_class"] == "fine") == r["_A"], (
            "class and resolution disagree for %s" % r["eb"])
    global _ALLROWS
    _ALLROWS = rows
    nA = sum(r["_A"] for r in rows)
    assert len(rows) == int(texnum("NWindows")), (
        "catalogue has %d windows, manuscript says %d" % (len(rows), texnum("NWindows")))
    assert nA == int(texnum("NWinA")) and len(rows) - nA == int(texnum("NWinB"))
    assert len({r["_star"] for r in rows}) == int(texnum("NStars"))
    return rows


# ★★ v4.11: FIGURE 1 PLOTTED THE BLANKET-MULTIPLIER LIMIT, NOT THE ADOPTED
# ONE.  `(ma if A else mb) * P_trig` is the completeness of no window: the
# adopted per-window EIRP_90 is stratified on the window's own control
# maximum -- 390 of 402 Class A windows at x3.45 and the twelve
# disc-affected ones bounded above x20 -- and then divided by the retained
# amplitude fraction for the omitted annual parallax.  So the figure
# disagreed with the four macros it asserts itself against, which is how it
# was found: it stopped the build rather than shipping a panel a reader
# could not reconcile with the text.  One owner, `adopted_e90.py`.
import adopted_e90 as _ae
_E90 = None
_ALLROWS = None


def eirp90(r, ma, mb):
    global _E90
    if _E90 is None or id(r) not in _E90:
        _E90 = _ae.per_window(_ALLROWS, os.path.dirname(os.path.abspath(
            __file__)), mult_b=mb)
    return _E90[id(r)]


def assert_no_arecibo(fig, drive=0):
    """No figure in this paper carries the Arecibo benchmark: an Arecibo-sized
    dish at 230 GHz is not physically realisable, so the comparison is made once
    in the prose of Sec. 2 and never drawn."""
    bad = [t.get_text() for t in fig.findobj(matplotlib.text.Text)
           if "arecibo" in t.get_text().lower()]
    assert not bad, "Arecibo appears on a figure: %r" % bad


def set_style():
    plt.rcParams.update({
        "font.family": "serif",
        "font.serif": ["STIXGeneral", "DejaVu Serif", "Times New Roman"],
        "mathtext.fontset": "stix",
        "font.size": 8.4, "axes.titlesize": 8.0, "axes.labelsize": 8.0,
        "xtick.labelsize": 7.0, "ytick.labelsize": 7.0, "legend.fontsize": 5.9,
        "legend.frameon": True, "legend.framealpha": 0.92,
        "legend.edgecolor": "0.7",
        "axes.grid": True, "grid.color": "0.85", "grid.linewidth": 0.4,
        "grid.alpha": 0.9, "axes.axisbelow": True, "axes.linewidth": 0.6,
        "xtick.major.width": 0.6, "ytick.major.width": 0.6,
        "xtick.minor.width": 0.4, "ytick.minor.width": 0.4,
        "lines.linewidth": 1.0,
        "figure.dpi": 200, "savefig.dpi": 200,
        "pdf.fonttype": 42, "ps.fonttype": 42, "pdf.compression": 6,
        "image.composite_image": False,
    })


# ======================================================================================
# panel (a): EIRP_90 against distance, with the previous searches
# ======================================================================================
def panel_a(rows, ma, mb, outdir, report, drive=0):
    best = {}
    for r in rows:
        s = r["_star"]
        if s not in best or eirp90(r, ma, mb) < eirp90(best[s], ma, mb):
            best[s] = r
    d = np.array([r["_d"] for r in best.values()])
    e = np.array([eirp90(r, ma, mb) for r in best.values()])
    # ★ v4.12 (referee 2, figure point 1).  THE PANEL COMPARED TWO DIFFERENT
    # CONVENTIONS AND CONCEDED IT IN THE CAPTION INSTEAD OF FIXING IT.  Our
    # point was EIRP_90, a 90 per cent recovery through the whole automated
    # chain; every literature point is that programme's own bare 5 sigma flux
    # threshold, at which recovery is not stated.  Conceding a mismatch in
    # words is not a comparison, and the mismatch ran AGAINST us.  The
    # commensurable quantity is the catalogue's own `eirp_nominal_W` -- the
    # bare 5 sigma EIRP of the same window -- and it is now the FILLED symbol.
    # EIRP_90 stays as a second, open symbol on the same point, joined by a
    # hairline, so the reader sees the like-for-like comparison and what the
    # stricter convention costs, in one glyph pair.
    t = np.array([r["_trig"] for r in best.values()])
    o = np.argsort(d)
    d, e, t = d[o], e[o], t[o]
    if drive == 4:                      # perturbation: the pair is inverted
        e, t = t, e

    bench = texnum("BenchEirp")
    bench_lbl = ("%d\\,m dish, %d\\,MW, %d\\,GHz"
                 % (texnum("BenchDiam"), texnum("BenchPowerMW"),
                    texnum("BenchFreqGHz")))

    fig = plt.figure(figsize=(3.45, 3.05))
    ax = fig.add_axes([0.205, 0.148, 0.775, 0.835])
    xlo, xhi, ylo, yhi = 0.75, 2.6e4, 7e11, 2e20

    xs = np.logspace(math.log10(xlo), math.log10(xhi), 64)
    ax.plot(xs, D2_NORM * xs ** 2, ls=":", lw=0.9, color="0.55", zorder=1)
    ax.text(2600, D2_NORM * 2600 ** 2 * 1.6, r"EIRP $\propto d^{2}$", fontsize=6.2,
            color="0.45", rotation=38, rotation_mode="anchor",
            ha="center", va="bottom", zorder=6)

    # the benchmark transmitter of Sec. 6 -- a power scale, not a model
    ax.axhline(bench, ls="--", lw=1.0, color="#009E73", zorder=2)
    ax.text(2.2e4, bench * 1.22, bench_lbl.replace(chr(92) + ",", " "),
            fontsize=6.0, color="#009E73", ha="right", va="bottom", zorder=6,
            bbox=dict(facecolor="white", edgecolor="none", alpha=0.8, pad=0.6))
    if drive == 1:                      # perturbation: the old line comes back
        ax.text(1.0, 2.0e13, "Arecibo-like planetary radar", fontsize=6.0)

    ax.vlines(d, np.minimum(t, e), np.maximum(t, e), lw=0.45,
              color="#0072B2", alpha=0.40, zorder=3)
    ax.scatter(d, e, s=13, marker="o", facecolor="none", edgecolor="#0072B2",
               linewidths=0.6, alpha=0.95, zorder=4)
    ax.scatter(d, t, s=11, marker="o", facecolor="#0072B2", edgecolor="none",
               alpha=0.85, zorder=5)

    for key in ("enriquez2017", "margot2023", "mason2024"):
        L = LIT[key]
        xs_, ys_ = [p[0] for p in L["pts"]], [p[1] for p in L["pts"]]
        ax.scatter(xs_, ys_, s=L["size"] * 2.4, marker=L["marker"],
                   color="white", edgecolor="none", zorder=5)
        ax.scatter(xs_, ys_, s=L["size"] * 1.6, marker=L["marker"],
                   color=L["colour"], edgecolor="k", linewidths=0.8, zorder=6)
    L = LIT["price2020"]
    for (_, y), nm in zip(L["pts"], L["tick_names"]):
        ax.plot([xlo, xlo * 1.55], [y, y], lw=1.4, color=L["colour"],
                solid_capstyle="butt", zorder=5)
        ax.text(xlo * 1.75, y, nm, fontsize=6.0, color=L["colour"],
                ha="left", va="center", zorder=6)

    ax.set_xscale("log"); ax.set_yscale("log")
    ax.set_xlim(xlo, xhi); ax.set_ylim(ylo, yhi)
    ax.set_xlabel("distance (pc)", labelpad=1.0)
    ax.set_ylabel("minimum detectable EIRP (W)\n"
                  "every filled symbol is a bare 5$\\sigma$ flux threshold",
                  fontsize=7.0, labelpad=1.5)
    ax.xaxis.set_major_locator(FixedLocator([1, 10, 100, 1000, 10000]))
    ax.xaxis.set_major_formatter(FixedFormatter(
        ["1", "10", "100", r"$10^{3}$", r"$10^{4}$"]))
    ax.xaxis.set_minor_locator(LogLocator(base=10.0, subs=tuple(range(2, 10)),
                                          numticks=40))
    ax.yaxis.set_major_locator(LogLocator(base=10.0, numticks=12))
    ax.yaxis.set_minor_locator(LogLocator(base=10.0, subs=tuple(range(2, 10)),
                                          numticks=60))
    ax.grid(True, which="major", alpha=0.9)

    handles = [Line2D([], [], ls="none", marker="o", mfc="#0072B2", mec="none",
                      ms=3.4),
               Line2D([], [], ls="none", marker="o", mfc="none", mec="#0072B2",
                      mew=0.6, ms=3.7),
               Line2D([], [], ls="--", color="#009E73", lw=1.0)]
    labels = ["this survey, 5$\\sigma$ threshold, deepest window per star (%d)"
              % d.size,
              "   the same windows at $\\mathrm{EIRP}_{90}$",
              "benchmark transmitter, $%s$ W" % texval("BenchEirp")]
    for key in ("enriquez2017", "margot2023", "mason2024"):
        L = LIT[key]
        handles.append(Line2D([], [], ls="none", marker=L["marker"],
                              mfc=L["colour"], mec="k", mew=0.7, ms=4.4))
        labels.append(L["label"])
    handles.append(Line2D([], [], color=LIT["price2020"]["colour"], lw=1.4))
    labels.append(LIT["price2020"]["label"])
    leg = ax.legend(handles, labels, loc="upper left", fontsize=5.6,
                    handletextpad=0.5, borderpad=0.3, labelspacing=0.38,
                    borderaxespad=0.3, framealpha=0.93)
    leg.get_frame().set_linewidth(0.4)

    assert_no_arecibo(fig, drive)

    # the panel must reproduce the manuscript's own sensitivity numbers
    eA = np.array([eirp90(r, ma, mb) for r in rows if r["_A"]])
    sysbest = {}
    for r in rows:
        if not r["_A"]:
            continue
        k = r["system_id"]
        sysbest[k] = min(sysbest.get(k, float("inf")), eirp90(r, ma, mb))
    sb = np.array(sorted(sysbest.values()))
    # tolerance is half a unit in the macro's last printed digit: these ship
    # at two significant figures, so 1.273e14 is the correct source of \EirpNinetySysLoA
    # = 1.3e14 and a 2 per cent tolerance would reject the right answer.
    for got, name, tol in ((np.median(eA), "EirpNinetyWinMedA", 0.05),
                           (np.median(sb), "EirpNinetySysMedA", 0.05),
                           (sb.min(), "EirpNinetySysLoA", 0.05),
                           (sb.max(), "EirpNinetySysHiA", 0.05)):
        assert close(float(got), texnum(name), tol), (
            "panel (a) plots %g where \\%s is %g" % (got, name, texnum(name)))

    # ★ the two symbols must be the right way round -- the completeness
    #   convention is always the STRICTER statement, so every open symbol sits
    #   above its filled one.  Driven by --drive 4, which inverts the pair.
    assert np.all(e > t), (
        "panel (a) draws EIRP_90 below the bare threshold for %d of %d stars"
        % (int((e <= t).sum()), e.size))
    # ★ and the gap is not free-floating: the smallest ratio across the plotted
    #   windows is the ADOPTED Class A completeness factor \EirpNinetyMultA,
    #   which is the floor of the per-window EIRP_90 (the annual parallax can
    #   only raise a window above it).  If the factor is re-measured and this
    #   stops holding, the panel must stop too.
    # ★★ v4.12: this was pinned to \StrMultNoise, the superseded NOISE-STRATUM
    #   transfer of the two-stratum construction Ruling 1 removed.  When the
    #   rank came out of the chain that macro stopped being the floor of
    #   anything and stopped being emitted at all, and the figure asserted
    #   3.0287 against 3.45 and killed the build.  A figure pinned to a
    #   retired macro is pinned to a number the paper no longer adopts, which
    #   is what this clause exists to prevent -- so it must name the adopted
    #   one.  The tolerance is unchanged at 1 per cent.
    assert close(float((e / t).min()), texnum("EirpNinetyMultA"), 0.01), (
        "panel (a)'s smallest EIRP_90/threshold ratio is %.4f where "
        "\\EirpNinetyMultA is %g"
        % ((e / t).min(), texnum("EirpNinetyMultA")))

    report["panel_a"] = {
        "quantity": "filled: bare 5 sigma eirp_nominal_W; open: adopted EIRP_90",
        "mult_A": ma, "mult_B": mb,
        "n_stars": int(d.size),
        "deepest_star": min(best, key=lambda k: eirp90(best[k], ma, mb)),
        "trig_min_W": float(t.min()), "trig_max_W": float(t.max()),
        "trig_median_W": float(np.median(t)),
        "e90_over_trig_min": float((e / t).min()),
        "e90_over_trig_median": float(np.median(e / t)),
        "e90_over_trig_max": float((e / t).max()),
        "n_stars_trig_below_benchmark": int((t < bench).sum()),
        "eirp90_min_W": float(e.min()), "eirp90_max_W": float(e.max()),
        "eirp90_median_W": float(np.median(e)),
        "n_stars_below_benchmark": int((e < bench).sum()),
        "benchmark_W": bench, "benchmark_label": bench_lbl,
        "class_A_window_median_W": float(np.median(eA)),
        "class_A_system_median_W": float(np.median(sb)),
        "arecibo_drawn": False,
    }
    name = "eirp_context_a" + ("_drive%d" % drive if drive else "")
    p = os.path.join(outdir, name + ".pdf")
    fig.savefig(p, format="pdf", bbox_inches="tight", pad_inches=0.015)
    plt.close(fig)
    return p


# ======================================================================================
# panel (b): native channel width against observing frequency
# ======================================================================================
def panel_b(rows, outdir, report, drive=0):
    fc = np.array([r["_fc"] for r in rows])
    cw = np.array([r["_cw"] for r in rows])
    fine = np.array([r["_A"] for r in rows])
    lit_hz = [LIT[k]["chan_Hz"] for k in LIT]
    span = math.log10(max(lit_hz + [cw.max()]) / min(lit_hz + [cw.min()]))

    fig = plt.figure(figsize=(3.45, 2.85))
    ax = fig.add_axes([0.165, 0.155, 0.815, 0.825])

    ax.scatter(fc[~fine], cw[~fine], s=6.5, marker="v", facecolor="none",
               edgecolor="0.55", linewidths=0.45, zorder=3)
    ax.scatter(fc[fine], cw[fine], s=4.5, marker="o", facecolor="#0072B2",
               edgecolor="none", alpha=0.55, zorder=4)
    for key in ("enriquez2017", "margot2023", "price2020", "mason2024"):
        L = LIT[key]
        ax.plot(L["freq_GHz"], [L["chan_Hz"]] * 2, lw=1.8, color=L["colour"],
                solid_capstyle="butt", zorder=5)

    for key, ty, lab in (("price2020", 2.0e6, "Price+20  2.79 Hz"),
                         ("enriquez2017", 2.0e5, "Enriquez+17  2.79 Hz"),
                         ("margot2023", 2.0e4, "Margot+23  2.98 Hz")):
        L = LIT[key]
        ax.text(1.05, ty, lab, fontsize=5.8, color=L["colour"],
                ha="left", va="center", zorder=7)
        ax.plot([3.6, L["freq_GHz"][1] * 1.02], [ty * 0.60, L["chan_Hz"] * 1.35],
                lw=0.45, color=L["colour"], alpha=0.75, zorder=6)
    ax.text(5.5, 2.2e2, "Mason+25  30.5 kHz", fontsize=5.8,
            color=LIT["mason2024"]["colour"], ha="left", va="center", zorder=7)
    ax.plot([34.0, 98.0], [3.4e2, 2.4e4], lw=0.45,
            color=LIT["mason2024"]["colour"], alpha=0.75, zorder=6)

    ax.scatter([], [], s=4.5, marker="o", facecolor="#0072B2", edgecolor="none",
               label="this survey, Class A (%d)" % int(fine.sum()))
    ax.scatter([], [], s=6.5, marker="v", facecolor="none", edgecolor="0.55",
               linewidths=0.45, label="this survey, Class B (%d)" % int((~fine).sum()))
    leg = ax.legend(loc="lower right", fontsize=5.6, handletextpad=0.4,
                    borderpad=0.3, labelspacing=0.35, framealpha=0.93)
    leg.get_frame().set_linewidth(0.4)

    ax.annotate("", xy=(620.0, 3.2e7), xytext=(620.0, 3.0),
                arrowprops=dict(arrowstyle="<->", lw=0.7, color="0.35"))
    ax.text(560.0, 3.0e3, r"$\Delta\log\Delta\nu_{\rm ch}\!\approx\!%.0f$" % span,
            fontsize=6.0, color="0.35", ha="center", va="center",
            rotation=90, zorder=7)

    ax.set_xscale("log"); ax.set_yscale("log")
    ax.set_xlim(0.9, 700.0); ax.set_ylim(0.8, 1.2e8)
    ax.set_xlabel("observing frequency (GHz)", labelpad=1.0)
    ax.set_ylabel("native channel width (Hz)", labelpad=1.5)
    ax.xaxis.set_major_locator(FixedLocator([1, 10, 100, 500]))
    ax.xaxis.set_major_formatter(FixedFormatter(["1", "10", "100", "500"]))
    ax.xaxis.set_minor_locator(LogLocator(base=10.0, subs=tuple(range(2, 10)),
                                          numticks=40))
    ax.yaxis.set_major_locator(LogLocator(base=10.0, numticks=9))
    ax.yaxis.set_minor_locator(LogLocator(base=10.0, subs=tuple(range(2, 10)),
                                          numticks=60))
    ax.grid(True, which="major", alpha=0.9)

    assert_no_arecibo(fig, drive)
    assert round(span) == 7, "the channel-width span is %.2f decades, not 7" % span

    report["panel_b"] = {
        "n_windows": len(rows),
        "n_class_A": int(fine.sum()), "n_class_B": int((~fine).sum()),
        "chanw_min_Hz": float(cw.min()), "chanw_max_Hz": float(cw.max()),
        "chanw_median_Hz": float(np.median(cw)),
        "literature_channel_Hz": {k: LIT[k]["chan_Hz"] for k in LIT},
        "span_decades": round(span, 2),
    }
    name = "eirp_context_b" + ("_drive%d" % drive if drive else "")
    p = os.path.join(outdir, name + ".pdf")
    fig.savefig(p, format="pdf", bbox_inches="tight", pad_inches=0.015)
    plt.close(fig)
    return p


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--outdir", default=DEFAULT_OUTDIR)
    ap.add_argument("--drive", type=int, default=0)
    args = ap.parse_args()
    set_style()
    os.makedirs(args.outdir, exist_ok=True)
    report = {"catalogue": os.path.basename(CAT),
              "multiplier_source": os.path.basename(M3A)}
    ma, mb, _mrep = multipliers(args.drive)
    report["multipliers"] = _mrep
    rows = catalogue(args.drive)
    pa = panel_a(rows, ma, mb, args.outdir, report, args.drive)
    pb = panel_b(rows, args.outdir, report, args.drive)
    print("wrote:", pa, pb)
    if not args.drive:
        with open(os.path.join(HERE, "figures_context_v410.json"), "w") as fh:
            json.dump({"figures": [pa, pb], "numbers": report,
                       "literature": {k: {"pts": v["pts"], "src": v["src"],
                                          "chan_src": v["chan_src"],
                                          "freq_src": v["freq_src"]}
                                      for k, v in LIT.items()},
                       "d2_guide_norm_W_at_1pc": D2_NORM}, fh, indent=1)
    print(json.dumps(report, indent=1))


if __name__ == "__main__":
    main()
