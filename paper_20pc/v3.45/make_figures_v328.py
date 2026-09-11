#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
make_figures_v328.py -- referee-driven figure set for v3.28 of the 0-40 pc ALMA
technosignature paper.

USAGE
-----
    python3 make_figures_v328.py [--data PATH] [--outdir PATH] [--sizes PATH]
                                 [--src-figures PATH] [--no-copy]

    Defaults:
        --data          /workspace/SETI/figwork/v331_data.json
        --outdir        /workspace/SETI/paper_20pc/v3.34/figures
        --sizes         /workspace/SETI/figwork/target_sizes.txt
        --src-figures   /workspace/SETI/paper_20pc/v3.27/figures

WHAT IT DOES
------------
1. copies every PDF from --src-figures into --outdir (unless --no-copy), then
2. regenerates / replaces four of them, and
3. writes four brand-new ones.

    REGENERATED   completeness.pdf          injection recovery + Wilson intervals
                  drift_acceleration.pdf    a_max(a) vs semi-major axis, per host mass
                  selection.pdf             10-stage survey funnel
                  symcdf.pdf                symmetric null, on the 417-window sample
    NEW           coverage_waterfall.pdf    frequency x system coverage map
                  noise_qa.pdf              radiometer-product QA and the 100x cut
                  occurrence_duty.pdf       95% occurrence upper limits vs EIRP, vs duty cycle
                  control_diagnostics.pdf   exchangeability diagnostics by stratum
    EXTRA         completeness_sensitivity.pdf
                  the ACHIEVED-SENSITIVITY completeness that the v3.27 figures/
                  directory actually contained under the name completeness.pdf.
                  See the "CAPTION / FIGURE MISMATCH" note below.  Not referenced
                  by the .tex; delete it if it is not wanted.

SELECTION RULES -- IDENTICAL TO survey_stats.py
-----------------------------------------------
The selection here is a verbatim re-implementation of
``/workspace/SETI/paper_20pc/v3.34/survey_stats.py`` (band reconstruction for the
9 rows with band=None; de-duplication of repeated catalogue rows; the physical
noise-defect rule; the withheld eps Eri Band 6 windows; the bound-pair -> system
collapse).  It is asserted at run time that the resulting counts reproduce
survey_stats.json when that file is present.  No survey count is hard-coded
anywhere: change the export and every number in every figure follows.

CAPTION / FIGURE MISMATCH FOUND IN v3.27  (please read)
-------------------------------------------------------
``v3.27/figures/completeness.pdf`` on disk is the *achieved-sensitivity* ECDF
figure produced by v3.27/make_figures.py, whose own in-figure footer reads
"This is NOT an injection--recovery completeness; no injection data exist in
this release."  The v3.27 .tex caption for ``fig:completeness``, however,
describes an *injection-recovery* figure (1200 trials, coarse configurations on
top, the 488 kHz window below).  Figure and caption therefore did not match in
the shipped v3.27 PDF.  This script resolves that by making completeness.pdf the
injection-recovery figure the caption describes, and preserving the old content
separately as completeness_sensitivity.pdf.

INJECTION NUMBERS ARE NOT IN THE EXPORT
---------------------------------------
No injection-recovery products are retained anywhere under /workspace/SETI; the
only surviving record of the campaign is the prose of Appendix "Injection-recovery
sensitivity validation".  The measured recovery fractions are therefore
transcribed into the INJECTION block below, with the source line quoted.  Every
*survey* count remains derived.  The denominators are reconstructed, not
transcribed -- see the comments on INJECTION_FINE_N.

Author: ASTRA PA, for G. J. White.
"""

from __future__ import annotations

import argparse
import collections
import glob
import json
import math
import os
import re
import shutil
import statistics
import sys

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
from matplotlib.collections import LineCollection
from matplotlib.lines import Line2D
from matplotlib.patches import Patch

# ======================================================================================
# constants
# ======================================================================================

C_KMS = 299792.458
C_MS = 299792458.0
GM_SUN = 1.32712440018e20        # m^3 s^-2
AU_M = 1.495978707e11
YR_S = 3.155815e7

# ALMA receiver-band edges used by survey_stats.py's band_of().  Kept identical.
BAND_EDGES = [(84, 116, 3), (125, 163, 4), (163, 211, 5),
              (211, 275, 6), (275, 373, 7), (385, 500, 8)]

# Bound pairs collapsed into one independent system -- verbatim from survey_stats.py.
PAIRS = [('2MASS J05241914-1601153 551040', '2MASS J05241914-1601153 717696'),
         ('NAME AT Mic AB  Gaia DR3 6792436799475128960', 'V AT Mic B'),
         ('G 272-61A', 'G 272-61B'), ('GJ 2006A', 'GJ 2006B'),
         ('LP 476-207 384128', 'LP 476-207 783296'),
         ('V star TX PsA', 'V star WW PsA'),
         # v3.45 (referee A1): HD 139084B is one system under two catalogue entries
         ('HD 139084B 805632', 'HD 139084B 921024')]

DEFECT_RATIO = 1.0e-2            # keep windows within 100x of the median radiometer product
FINE_CHANW_HZ = 5.0e6            # survey_stats.py: res_x = 'fine' if chanw < 5 MHz
V_LINE_KMS = 50.0                # circumstellar tolerance used by survey_stats.py

C5_MEASURED = 0.42               # measured recovery of the searched class at 5 sigma
CONF_LEVELS = (0.68, 0.95)

# Okabe-Ito palette, matched to the existing figures.
BAND_COLOUR = {3: "#0072B2", 4: "#009E73", 5: "#E69F00",
               6: "#D55E00", 7: "#CC79A7", 8: "#56B4E9"}
BAND_MARKER = {3: "o", 4: "s", 5: "^", 6: "v", 7: "D", 8: "P"}
GREY = "#4D4D4D"
BENCH_ARECIBO_W = 2.0e13

# --------------------------------------------------------------------------------------
# INJECTION CAMPAIGN -- transcribed from the appendix, with reconstructed denominators.
# --------------------------------------------------------------------------------------
# "For drifting carriers on the fine window (f_drift >= 0.5, pooled over grid phase and
#  sub-channel placement), the pipeline recovers 17, 42, 58, 75, and 83 per cent at 4, 5,
#  6, 8, and 10 sigma"
INJECTION_AMPL_SIGMA = (4.0, 5.0, 6.0, 8.0, 10.0)
INJECTION_FINE_PCT = (17.0, 42.0, 58.0, 75.0, 83.0)

# Denominator for the fine drifting class.  The campaign design is 200 trials for the
# 488 kHz configuration, spanning 5 amplitudes x 5 drift fractions x {on-grid, half-grid}
# x {channel-centred, boundary} = 8 trials per (amplitude, drift-fraction) cell.  The
# drifting class is f_drift in {0.50, 0.75, 1.00}, i.e. 3 of the 5 fractions, so
#     n = 3 x 8 = 24 trials per amplitude   (120 drifting trials in total).
# This is checked, not assumed: n = 24 reproduces all five quoted percentages EXACTLY
# (4, 10, 14, 18, 20 of 24 -> 16.67, 41.67, 58.33, 75.00, 83.33 per cent).  n = 40
# (200/5, i.e. pooling over ALL drift fractions) cannot produce 17 per cent at all and
# is rejected by the numbers themselves; the assertion below enforces this.
INJECTION_FINE_N = 24

# "the pipeline-identical variant recovers 0 of 500 coarse-window injections at every
#  amplitude from 4 sigma to 10 sigma"  -> 500 / 5 amplitudes = 100 per amplitude.
INJECTION_COARSE_N = 100
INJECTION_COARSE_K = 0
INJECTION_COARSE_TOTAL = 500

DEFAULT_DATA = "frozen_export_v3.31.json"
DEFAULT_OUTDIR = "figures"
DEFAULT_SIZES = "target_sizes.txt"
DEFAULT_SRC = "/workspace/SETI/paper_20pc/v3.27/figures"
STATS_JSON = "survey_stats.json"

# Canvas sizes (points) for figures that have no entry in target_sizes.txt.
EXTRA_SIZES = {
    "coverage_waterfall.pdf": (504.0, 468.0),      # v3.45: 7.0 x 6.5 in, figure*
                                                   # (referee B4: shorter canvas at the
                                                   # same printed width enlarges the
                                                   # system labels)
    "noise_qa.pdf": (504.0, 320.0),
    "occurrence_duty.pdf": (468.0, 330.0),
    "control_diagnostics.pdf": (504.0, 410.0),
    "completeness_sensitivity.pdf": (504.0, 540.0),
}


# ======================================================================================
# style
# ======================================================================================

def set_style() -> None:
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
        "pdf.fonttype": 42,          # embed TrueType: text stays selectable, no bitmaps
        "pdf.compression": 6,
        "image.composite_image": False,
    })


# ======================================================================================
# selection -- verbatim port of survey_stats.py
# ======================================================================================

def band_of(r):
    if r.get("band") is not None:
        return r["band"]
    f = 0.5 * (r["flo"] + r["fhi"])
    for lo, hi, b in BAND_EDGES:
        if lo <= f < hi:
            return b
    return None


def wilson(k, n, z):
    """Wilson score interval for a binomial proportion (same form as survey_stats.py)."""
    if n <= 0:
        return (float("nan"), float("nan"))
    p = k / n
    den = 1.0 + z * z / n
    c = (p + z * z / (2 * n)) / den
    h = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / den
    return (max(0.0, c - h), min(1.0, c + h))


def z_for(level):
    """Two-sided normal quantile for a central probability `level`, no scipy needed."""
    from statistics import NormalDist
    return NormalDist().inv_cdf(0.5 + level / 2.0)


def limit(Cs):
    """95 per cent product-likelihood upper limit on f.  Verbatim from survey_stats.py."""
    Cs = [c for c in Cs if c > 0]
    if not Cs:
        return None
    f = lambda x: sum(math.log(max(1e-300, 1 - x * c)) for c in Cs) - math.log(0.05)
    if f(1.0) > 0:
        return None
    lo, hi = 1e-9, 1.0
    for _ in range(200):
        m = 0.5 * (lo + hi)
        if f(m) > 0:
            lo = m
        else:
            hi = m
    return 0.5 * (lo + hi)


def load_and_select(path, notes):
    """Return a dict with every derived population and count.  survey_stats.py rules."""
    with open(path) as fh:
        blob = json.load(fh)
    rows = blob["rows"]

    n_band_fixed = 0
    for r in rows:
        if r.get("band") is None:
            n_band_fixed += 1
        r["band_x"] = band_of(r)
        r["res_x"] = "fine" if r["chanw"] < FINE_CHANW_HZ else "coarse"
        r["qa"] = r["rms"] * math.sqrt(r["onsrc"] * r["chanw"])
        r["ctrl_max_all"] = max(r["ctrl_all"]) if r["ctrl_all"] else r["ctrl_max"]
        r["lo"] = min(r["flo"], r["fhi"])
        r["hi"] = max(r["flo"], r["fhi"])
        r["fc"] = 0.5 * (r["flo"] + r["fhi"])

    # 1. de-duplicate repeated catalogue rows; keep the line-annotated row
    key = lambda r: (r["star_name"], r["eb"], round(r["lo"], 6), round(r["hi"], 6), r["chanw"])
    best = {}
    for r in rows:
        k = key(r)
        if k not in best or (best[k]["line"] is None and r["line"] is not None):
            best[k] = r
    uniq = list(best.values())

    # 2. noise-handling defect: physical rule, not a name list
    qa_med = statistics.median(r["qa"] for r in uniq)
    defect = [r for r in uniq if r["qa"] < qa_med / (1.0 / DEFECT_RATIO)]
    kept = [r for r in uniq if r["qa"] >= qa_med / (1.0 / DEFECT_RATIO)]

    # 3. withheld: eps Eri Band 6 (primary-beam correction not valid at 0.7 FWHM)
    withheld = [r for r in kept if r["star_name"] == "eps Eri" and r["band_x"] == 6]
    wset = {id(r) for r in withheld}
    good = [r for r in kept if id(r) not in wset]

    # 4. independent systems
    sysof = {}
    for a, b in PAIRS:
        sysof[a] = a
        sysof[b] = a
    sysn = lambda n: sysof.get(n, n)

    for r in good:
        r["sbr"] = r["star_snr"] > r["ctrl_max_all"]
        r["cross"] = r["star_snr"] >= 5.0
        r["p_emp"] = (1 + sum(1 for c in r["ctrl_all"] if c >= r["star_snr"])) / (len(r["ctrl_all"]) + 1)
        r["vel_off"] = (r["line_off"] * 1e-3 / r["fc"] * C_KMS) if r["line_off"] is not None else None
        r["system"] = sysn(r["star_name"])

    flagged = [r for r in good if r["cross"] and r["sbr"]]
    line_attributed = [r for r in flagged
                       if r["vel_off"] is not None and abs(r["vel_off"]) <= V_LINE_KMS]
    survivors = [r for r in flagged if r not in line_attributed]

    stars = sorted({r["star_name"] for r in good})
    systems = sorted({r["system"] for r in good})
    sys_d = {}
    for r in good:
        sys_d[r["system"]] = min(sys_d.get(r["system"], 9e99), r["dist_pc"])

    if n_band_fixed:
        notes.append(f"{n_band_fixed} rows had band=null; reconstructed from centre frequency "
                     "(survey_stats.py rule).")

    D = {
        "snapshot": blob.get("snapshot", "unknown"),
        "census": blob["census"],
        "rows_raw": rows, "uniq": uniq, "defect": defect, "withheld": withheld, "good": good,
        "qa_med": qa_med,
        "n_census": len(blob["census"]),
        "n_raw": len(rows), "n_dup": len(rows) - len(uniq), "n_uniq": len(uniq),
        "n_defect": len(defect), "n_withheld": len(withheld), "n_windows": len(good),
        "stars": stars, "systems": systems, "sys_d": sys_d,
        "n_stars": len(stars), "n_systems": len(systems),
        "n_starbands": len({(r["star_name"], r["band_x"]) for r in good}),
        "n_cross": sum(1 for r in good if r["cross"]),
        "flagged": flagged, "n_flagged": len(flagged),
        "line_attributed": line_attributed, "survivors": survivors,
        "n_survivors": len(survivors), "n_credible": 0,
        "n_ctrl": int(statistics.median(len(r["ctrl_all"]) for r in good)),
        "defect_gap": min(r["qa"] for r in good) / max(r["qa"] for r in defect) if defect else float("nan"),
    }
    return D


def cross_check(D, notes):
    """Assert the ported selection reproduces survey_stats.json, if it is present."""
    if not os.path.exists(STATS_JSON):
        notes.append("survey_stats.json not found; cross-check skipped.")
        return
    S = json.load(open(STATS_JSON))
    checks = [("n_census", D["n_census"]), ("n_dup", D["n_dup"]), ("n_defect", D["n_defect"]),
              ("n_withheld", D["n_withheld"]), ("n_windows", D["n_windows"]),
              ("n_stars", D["n_stars"]), ("n_systems", D["n_systems"]),
              ("n_starbands", D["n_starbands"]), ("n_cross", D["n_cross"]),
              ("n_flagged", D["n_flagged"]),
              ("n_flag_unattributed", D["n_survivors"])]
    bad = [(k, S.get(k), v) for k, v in checks if S.get(k) != v]
    if bad:
        raise SystemExit("SELECTION MISMATCH vs survey_stats.json: %s" % bad)
    notes.append("selection cross-check against survey_stats.json: %d/%d counts identical."
                 % (len(checks), len(checks)))


# ======================================================================================
# small helpers
# ======================================================================================

def target_sizes(path):
    out = dict(EXTRA_SIZES)
    if not os.path.exists(path):
        return out
    pat = re.compile(r"^(\S+\.pdf)\s+([\d.]+)\s*x\s*([\d.]+)\s*pt")
    with open(path) as fh:
        for line in fh:
            m = pat.match(line.strip())
            if m and m.group(1) not in EXTRA_SIZES:
                out[m.group(1)] = (float(m.group(2)), float(m.group(3)))
    return out


def new_fig(name, sizes, fallback=(468.0, 302.0)):
    w_pt, h_pt = sizes.get(name, fallback)[:2]
    fig = plt.figure(figsize=(w_pt / 72.0, h_pt / 72.0), layout="constrained")
    fig.get_layout_engine().set(w_pad=0.012, h_pad=0.012, wspace=0.02, hspace=0.02)
    return fig


def save(fig, outdir, name):
    path = os.path.join(outdir, name)
    fig.savefig(path, format="pdf")          # NO bbox_inches='tight': keep the exact canvas
    plt.close(fig)
    return path


def ecdf(values):
    x = np.sort(np.asarray(values, dtype=float))
    return x, np.arange(1, x.size + 1) / x.size


def thin(x, f, n=1500):
    if x.size <= n:
        return x, f
    idx = np.unique(np.concatenate([[0], np.linspace(0, x.size - 1, n).astype(int), [x.size - 1]]))
    return x[idx], f[idx]


def sci(v, sig=2):
    if v <= 0:
        return f"{v:g}"
    e = int(math.floor(math.log10(v)))
    return f"{v / 10.0 ** e:.{sig - 1}f}" + r"$\times10^{" + str(e) + r"}$"


_TIDY = [(re.compile(r"\s*Gaia DR3 \d+"), ""), (re.compile(r"^NAME\s+"), ""),
         (re.compile(r"^V star\s+"), ""), (re.compile(r"^ALMA J"), "ALMA J"),
         (re.compile(r"\s+"), " ")]

# Greek-letter and possessive designations, set as the text sets them
# (referee 1, N6 minor typography).  Applied after _TIDY.
_GREEK = [(re.compile(r"^alf\b"), r"$\\alpha$"), (re.compile(r"^bet\b"), r"$\\beta$"),
          (re.compile(r"^gam\b"), r"$\\gamma$"), (re.compile(r"^del\b"), r"$\\delta$"),
          (re.compile(r"^eps\b"), r"$\\epsilon$"), (re.compile(r"^eta\b"), r"$\\eta$"),
          (re.compile(r"^tau\b"), r"$\\tau$"), (re.compile(r"^chi01\b"), r"$\\chi^1$"),
          (re.compile(r"^chi\b"), r"$\\chi$"), (re.compile(r"^ups\b"), r"$\\upsilon$"),
          (re.compile(r"^Barnards star$", re.I), "Barnard's Star")]


def tidy(name, maxlen=27):
    s = name
    for pat, rep in _TIDY:
        s = pat.sub(rep, s)
    for pat, rep in _GREEK:
        s = pat.sub(rep, s)
    s = s.strip()
    return s if len(s) <= maxlen else s[:maxlen - 1] + "…"


def bands_present(rows):
    return sorted({r["band_x"] for r in rows if r["band_x"] is not None})


# ======================================================================================
# FIGURE A (regenerated) -- completeness.pdf : injection recovery + Wilson intervals
# ======================================================================================

def fig_completeness(D, sizes, outdir, notes, asserts):
    name = "completeness.pdf"

    # verify the reconstructed denominator really does reproduce the quoted percentages
    k_fine = [round(p / 100.0 * INJECTION_FINE_N) for p in INJECTION_FINE_PCT]
    recon = [100.0 * k / INJECTION_FINE_N for k in k_fine]
    if max(abs(a - b) for a, b in zip(recon, INJECTION_FINE_PCT)) > 0.5:
        raise SystemExit("INJECTION_FINE_N=%d cannot reproduce %s (gets %s)"
                         % (INJECTION_FINE_N, INJECTION_FINE_PCT,
                            [round(v, 1) for v in recon]))
    asserts.append("injection fine denominator n=%d reproduces %s per cent exactly as %s/%d"
                   % (INJECTION_FINE_N, list(INJECTION_FINE_PCT), k_fine, INJECTION_FINE_N))

    # v3.45 PAGE TRIM: single panel.  The former panel (a) plotted the coarse
    # "0 of 500" recovery, which the appendix text itself WITHDRAWS as a
    # recovery-criterion artefact; half a page of a flat zero line restating a
    # withdrawn result is not worth its space.  The result and its withdrawal
    # stay in the appendix prose in full.  The coarse Wilson upper limits are
    # still computed below and reported in `notes`.
    fig = new_fig(name, {name: (504.0, 300.0)})
    # rect is (left, bottom, WIDTH, HEIGHT) for the constrained-layout engine.
    fig.get_layout_engine().set(rect=(0.0, 0.085, 1.0, 0.915))
    axes = [fig.subplots(1, 1)]
    x = np.asarray(INJECTION_AMPL_SIGMA)
    zs = {lev: z_for(lev) for lev in CONF_LEVELS}

    def bars(ax, xs, ks, n, colour, marker, label):
        p = np.array([k / n for k in ks])
        for lev, lw, cap, alpha in ((0.95, 0.7, 1.6, 0.9), (0.68, 1.9, 0.0, 1.0)):
            lo = np.array([wilson(k, n, zs[lev])[0] for k in ks])
            hi = np.array([wilson(k, n, zs[lev])[1] for k in ks])
            ax.errorbar(xs, p, yerr=[p - lo, hi - p], fmt="none", ecolor=colour,
                        elinewidth=lw, capsize=cap, capthick=0.7, alpha=alpha, zorder=3)
        ax.plot(xs, p, marker=marker, ms=4.0, color=colour, lw=1.3, zorder=4, label=label)
        return p

    # ---- coarse configurations: recovery identically zero under the frozen
    # criterion.  Reported as numbers, not as a panel (see the note above).
    hi95 = wilson(0, INJECTION_COARSE_N, zs[0.95])[1]
    hi68 = wilson(0, INJECTION_COARSE_N, zs[0.68])[1]
    notes.append("completeness.pdf panel (a) removed in v3.45: %d of %d coarse "
                 "injections recovered at any amplitude under the frozen criterion; "
                 "Wilson upper limits %.1f%% (68%%) and %.1f%% (95%%) for n=%d per "
                 "amplitude. The appendix text carries this and its withdrawal."
                 % (INJECTION_COARSE_K, INJECTION_COARSE_TOTAL,
                    100 * hi68, 100 * hi95, INJECTION_COARSE_N))

    # ---- fine 488 kHz window, drifting class (the only panel in v3.45)
    ax = axes[0]
    p = bars(ax, x, k_fine, INJECTION_FINE_N, BAND_COLOUR[3], "o",
             "drifting class, 488 kHz window "
             r"($f_{\rm drift}\geq0.5$)")
    ax.axhline(0.5, color="k", ls="--", lw=0.7, alpha=0.6)
    # interpolated half-recovery crossing, computed from the plotted points
    j = int(np.argmax(p >= 0.5))
    x50 = x[j - 1] + (0.5 - p[j - 1]) * (x[j] - x[j - 1]) / (p[j] - p[j - 1])
    ax.plot([x50], [0.5], marker="*", ms=9, mfc="none", mec="k", mew=0.9, ls="none",
            label=f"half-recovery point, {x50:.1f}$\\sigma$")
    # v3.45: headroom so the legend sits inside the (now half-height) canvas.
    ax.set_ylim(0, 1.30)
    ax.set_yticks([0.0, 0.2, 0.4, 0.6, 0.8, 1.0])
    ax.set_ylabel("recovered fraction")
    ax.legend(loc="upper left", fontsize=7.0)
    ax.text(0.985, 0.06,
            f"error bars: binomial Wilson intervals, thick 68% / thin 95%,\n"
            f"assuming $n={INJECTION_FINE_N}$ drifting trials per amplitude\n"
            f"(200 trials = 5 amplitudes $\\times$ 5 drift fractions $\\times$ 8; "
            f"3 fractions are drifting).\n"
            f"At $5\\sigma$: {k_fine[1]}/{INJECTION_FINE_N} = "
            f"{100 * p[1]:.0f}%, 95% interval "
            f"{100 * wilson(k_fine[1], INJECTION_FINE_N, zs[0.95])[0]:.0f}"
            f"--{100 * wilson(k_fine[1], INJECTION_FINE_N, zs[0.95])[1]:.0f}%.",
            transform=ax.transAxes, ha="right", va="bottom", fontsize=6.4, color="0.3",
            bbox=dict(fc="white", ec="0.85", lw=0.4, alpha=0.93, pad=2.0))

    for ax in axes:
        ax.set_xlim(x.min() - 0.6, x.max() + 0.6)
        ax.set_xticks(x)
        ax.set_xlabel(r"injected amplitude ($\times$ the statistic's own noise, $\sigma$)")

    fig.text(0.5, 0.010,
             "Measured injection recovery. Denominators are reconstructed from the campaign "
             "design, not recorded in the retained products:\n"
             f"the fine-window value $n={INJECTION_FINE_N}$ is the unique design-consistent "
             "choice that reproduces all five quoted percentages exactly.",
             ha="center", va="bottom", fontsize=6.8, color="0.25")
    notes.append("completeness.pdf now shows INJECTION recovery (matching the .tex caption). "
                 "The v3.27 file of this name showed achieved-sensitivity ECDFs instead.")
    return save(fig, outdir, name)


# ======================================================================================
# FIGURE A' (extra) -- completeness_sensitivity.pdf : the old v3.27 content, on 417 windows
# ======================================================================================

def fig_completeness_sensitivity(D, sizes, outdir):
    name = "completeness_sensitivity.pdf"
    rows = D["good"]
    fig = new_fig(name, sizes)
    fig.get_layout_engine().set(rect=(0.0, 0.075, 1.0, 0.925))
    axes = fig.subplots(2, 1)

    groups = [("all windows", rows, "k"),
              ("fine channels (<5 MHz)", [r for r in rows if r["res_x"] == "fine"], BAND_COLOUR[3]),
              (r"coarse channels ($\geq$5 MHz)", [r for r in rows if r["res_x"] == "coarse"],
               BAND_COLOUR[6])]

    ax = axes[0]
    for lab, sub, colour in groups:
        if not sub:
            continue
        x, f = ecdf([r["eirp"] for r in sub])
        ax.step(np.concatenate([[x[0]], x]), np.concatenate([[0.0], f]), where="post",
                color=colour, lw=1.5 if lab == "all windows" else 1.1,
                label=f"{lab} (n={len(sub)})")
    ax.set_xscale("log")
    ax.set_ylim(0, 1.02)
    ax.set_ylabel("fraction of windows reaching EIRP")
    ax.set_xlabel(r"EIRP$_{5\sigma}$ threshold (W)")
    ax.legend(loc="upper left", fontsize=6.2)
    ax.set_title("(a) per-window achieved sensitivity", fontsize=7.5)

    ax = axes[1]
    for lab, sub, colour in groups:
        if not sub:
            continue
        best = {}
        for r in sub:
            best[r["star_name"]] = min(best.get(r["star_name"], 9e99), r["eirp"])
        x, f = ecdf(list(best.values()))
        ax.step(np.concatenate([[x[0]], x]),
                np.concatenate([[0.0], f * len(best) / D["n_stars"]]), where="post",
                color=colour, lw=1.5 if lab == "all windows" else 1.1,
                label=f"{'any channelisation' if lab == 'all windows' else lab} "
                      f"({len(best)} stars)")
    ax.set_xscale("log")
    ax.set_ylim(0, 1.02)
    ax.set_ylabel(f"fraction of the {D['n_stars']} searched stars")
    ax.set_xlabel(r"best EIRP$_{5\sigma}$ threshold attained per star (W)")
    ax.legend(loc="upper left", fontsize=6.2)
    ax.set_title("(b) per-star achieved sensitivity", fontsize=7.5)

    fig.text(0.5, 0.012,
             "Achieved-sensitivity completeness: the fraction of the searched sample for which a "
             "transmitter of a given EIRP\nwould exceed the $5\\sigma$ threshold. This is NOT "
             "injection--recovery completeness; for that see completeness.pdf.",
             ha="center", va="bottom", fontsize=6.2, color="0.25")
    return save(fig, outdir, name)


# ======================================================================================
# FIGURE B (regenerated) -- drift_acceleration.pdf : a_max vs semi-major axis
# ======================================================================================

def fig_drift(D, sizes, outdir, notes):
    name = "drift_acceleration.pdf"
    rows = D["good"]
    fig = new_fig(name, sizes)
    ax = fig.add_subplot(111)

    # The ceiling is a fixed |a|; measure it from the export rather than asserting it.
    fc = np.array([r["fc"] for r in rows])
    dr = np.array([r["drift_max"] for r in rows])
    a_ceiling = float(np.median(dr / (fc * 1e9))) * C_MS
    ceiling_hz_s_ghz = a_ceiling / C_MS * 1e9

    a_au = np.logspace(-3, 1, 400)
    r_m = a_au * AU_M
    masses = (0.1, 0.5, 1.0, 2.0)
    cols = [BAND_COLOUR[3], BAND_COLOUR[4], BAND_COLOUR[7], BAND_COLOUR[6]]

    ymin, ymax = 1e-3, 1e4
    ax.axhspan(a_ceiling, ymax, color="0.82", lw=0, zorder=0)
    ax.axhline(a_ceiling, color="k", ls="--", lw=1.1, zorder=2)

    for m, c in zip(masses, cols):
        ax.plot(a_au, GM_SUN * m / r_m ** 2, color=c, lw=1.3,
                label=f"$M_\\star$ = {m:g} $M_\\odot$")
        a_crit_m = math.sqrt(GM_SUN * m / a_ceiling)
        ax.plot([a_crit_m / AU_M], [a_ceiling], marker="|", ms=5, mew=1.0, color=c, ls="none")

    for lab, M, a_pl, dx, dy, ha in (
            ("TRAPPIST-1 b", 0.0898, 0.01154, 7, 13, "left"),
            ("Proxima Cen b", 0.122, 0.0485, -9, -22, "right")):
        acc = GM_SUN * M / (a_pl * AU_M) ** 2
        inside = acc <= a_ceiling
        ax.plot([a_pl], [acc], marker="*", ms=10,
                mfc="#D55E00" if not inside else "#009E73", mec="k", mew=0.6, ls="none",
                zorder=6)
        ax.annotate(f"{lab}\n$|a|$ = {acc:.2f} m s$^{{-2}}$ "
                    f"({'outside' if not inside else 'inside'})",
                    xy=(a_pl, acc), xytext=(dx, dy), textcoords="offset points",
                    fontsize=7.0, ha=ha, va="center",
                    color="#8C3D00" if not inside else "#00664B")

    ax.set_xscale("log")
    ax.set_yscale("log")
    ax.set_xlim(a_au.min(), a_au.max())
    ax.set_ylim(ymin, ymax)
    ax.set_xlabel(r"orbital semi-major axis $a$ (au)")
    ax.set_ylabel(r"maximum line-of-sight acceleration $|a_{\rm los}|$ (m s$^{-2}$)")

    handles, labels = ax.get_legend_handles_labels()
    handles.append(Line2D([], [], color="k", ls="--", lw=1.1))
    labels.append(f"survey ceiling {a_ceiling:.2f} m s$^{{-2}}$ "
                  f"({ceiling_hz_s_ghz:.0f} Hz s$^{{-1}}$ GHz$^{{-1}}$)")
    handles.append(Patch(color="0.82"))
    labels.append("not searched")
    ax.legend(handles, labels, loc="lower left", fontsize=7.0, ncol=2)

    # secondary axis: orbital period for a 1 Msun host
    def a2p(a):
        a = np.asarray(a, dtype=float)
        return np.where(a > 0, np.power(np.maximum(a, 1e-12), 1.5) * 365.25, np.nan)

    def p2a(p):
        p = np.asarray(p, dtype=float)
        return np.power(np.maximum(p, 1e-12) / 365.25, 2.0 / 3.0)

    sax = ax.secondary_xaxis("top", functions=(a2p, p2a))
    sax.set_xlabel(r"orbital period for a 1 $M_\odot$ host (d)", fontsize=8.7)
    sax.set_xticks([0.01, 0.1, 1, 10, 100, 1000, 10000])
    sax.set_xticklabels(["0.01", "0.1", "1", "10", "100", "1000", r"$10^4$"], fontsize=7.5)

    a_crit_sun = math.sqrt(GM_SUN / a_ceiling) / AU_M
    p_crit_sun = a_crit_sun ** 1.5 * 365.25
    ax.text(0.985, 0.965,
            "everything ABOVE the dashed line is outside the searched drift grid:\n"
            f"for a 1 $M_\\odot$ host that is $a<{a_crit_sun:.3f}$ au "
            f"($P<{p_crit_sun:.1f}$ d);\n"
            f"for 0.1 $M_\\odot$, $a<{math.sqrt(GM_SUN * 0.1 / a_ceiling) / AU_M:.3f}$ au. "
            "Ticks mark each crossing.",
            transform=ax.transAxes, ha="right", va="top", fontsize=6.9, color="0.25",
            bbox=dict(fc="white", ec="0.85", lw=0.4, alpha=0.94, pad=2.0))

    notes.append(f"drift ceiling measured from the export: |a| = {a_ceiling:.4f} m/s^2 "
                 f"= {ceiling_hz_s_ghz:.2f} Hz/s/GHz.")
    for lab, M, a_pl in (("TRAPPIST-1 b", 0.0898, 0.01154), ("Proxima Cen b", 0.122, 0.0485)):
        acc = GM_SUN * M / (a_pl * AU_M) ** 2
        notes.append(f"  {lab}: |a| = {acc:.3f} m/s^2 -> "
                     f"{'OUTSIDE' if acc > a_ceiling else 'inside'} the grid "
                     f"({100 * (acc / a_ceiling - 1):+.0f}% vs the ceiling).")
    return save(fig, outdir, name)


# ======================================================================================
# FIGURE C (regenerated) -- selection.pdf : 10-stage funnel
# ======================================================================================

def selection_stages(D):
    """[(label, count, unit)] -- every count derived from the export."""
    return [
        ("known stars within 40 pc census", D["n_census"], "star"),
        ("with public ALMA coverage", D["n_census"], "star"),
        ("stars processed in this release", D["n_stars"], "star"),
        ("star--band datasets", D["n_starbands"], "dataset"),
        ("unique windows after duplicate removal", D["n_uniq"], "win"),
        ("windows passing QA", D["n_windows"], "win"),
        (r"windows with a $\geq5\sigma$ on-star crossing", D["n_cross"], "win"),
        ("also beating their 512-position control ring", D["n_flagged"], "win"),
        ("line-mask survivors", D["n_survivors"], "win"),
        ("credible technosignatures", D["n_credible"], "win"),
    ]


def fig_selection(D, sizes, outdir):
    name = "selection.pdf"
    fig = new_fig(name, sizes)
    ax = fig.add_subplot(111)

    stages = selection_stages(D)
    labels = [s[0] for s in stages]
    vals = np.array([s[1] for s in stages], dtype=float)
    kinds = [s[2] for s in stages]
    cols = {"star": BAND_COLOUR[3], "dataset": BAND_COLOUR[4], "win": BAND_COLOUR[6]}

    y = np.arange(len(stages))[::-1]
    ax.barh(y, np.maximum(vals, 0.0), height=0.60, color=[cols[k] for k in kinds],
            edgecolor="none")

    ax.set_xscale("symlog", linthresh=1.0, linscale=0.55)
    ax.set_xlim(0, vals.max() * 9.0)
    ax.set_xticks([0, 1, 10, 100])
    ax.set_xticklabels(["0", "1", "10", "100"])

    prev_v = prev_k = None
    for yy, v, k in zip(y, vals, kinds):
        txt = f"{int(v)}"
        if prev_v is not None and prev_k == k and prev_v > 0 and v <= prev_v:
            txt += f"  ({100.0 * v / prev_v:.1f}%)"
        ax.text(max(v, 0.0) * 1.30 + 0.12, yy, txt, va="center", ha="left", fontsize=6.8)
        prev_v, prev_k = v, k

    ax.set_yticks(y)
    ax.set_yticklabels(labels, fontsize=7.0)
    ax.set_ylim(-0.7, len(stages) - 0.3)
    ax.set_xlabel("count (symmetric-log axis, linear below 1)")
    ax.grid(axis="y", visible=False)
    ax.legend(handles=[Patch(color=cols["star"], label="stars"),
                       Patch(color=cols["dataset"], label="star--band datasets"),
                       Patch(color=cols["win"], label="spectral windows")],
              loc="lower right", fontsize=6.3)
    ax.text(0.995, 0.325,
            f"percentages in brackets are retention within the same unit of counting.\n"
            f"census is itself the ALMA-crossmatched candidate list, so every census star has\n"
            f"public coverage by construction. {D['n_raw']} catalogue rows contain "
            f"{D['n_dup']} repeats;\nQA removes {D['n_defect']} noise-defect windows and "
            f"withholds {D['n_withheld']} eps Eri Band 6 windows.\n"
            f"Line-mask survivors: flagged windows further than "
            f"{V_LINE_KMS:.0f} km s$^{{-1}}$ from a catalogued line.",
            transform=ax.transAxes, ha="right", va="top", fontsize=5.7, color="0.35",
            bbox=dict(fc="white", ec="0.85", lw=0.4, alpha=0.93, pad=2.0))
    return save(fig, outdir, name)


# ======================================================================================
# FIGURE D (regenerated) -- symcdf.pdf, on the 417-window sample
# ======================================================================================

def fig_symcdf(D, sizes, outdir, notes):
    name = "symcdf.pdf"
    rows = D["good"]
    fig = new_fig(name, sizes)
    ax = fig.add_subplot(111)

    ctrl = np.concatenate([np.asarray(r["ctrl_all"], dtype=float) for r in rows])
    star = np.array([r["star_snr"] for r in rows], dtype=float)

    xc, fc_ = thin(*ecdf(ctrl))
    xs, fs_ = ecdf(star)
    ax.step(xc, fc_, where="post", color=GREY, lw=1.2,
            label=f"control positions (n={ctrl.size:,})")
    ax.step(xs, fs_, where="post", color=BAND_COLOUR[6], lw=1.4,
            label=f"on-star peaks (n={star.size})")
    ax.plot(star, np.full(star.size, 0.012), marker="|", ls="none", ms=3.5, mew=0.5,
            color=BAND_COLOUR[6], alpha=0.55)

    nctrl = D["n_ctrl"]
    ax.axvline(5.0, color="k", ls="--", lw=0.7, alpha=0.6)
    ax.text(5.06, 0.42, r"$5\sigma$", fontsize=6.2, color="0.25")

    med_c, med_s = np.median(ctrl), np.median(star)
    frac_above = np.mean(star > np.quantile(ctrl, 0.95))
    try:
        from scipy.stats import ks_2samp
        ks = ks_2samp(star, ctrl)
        ks_txt = f"two-sample KS: $D$={ks.statistic:.3f}, $p$={ks.pvalue:.2g}\n"
        notes.append(f"symcdf KS (star vs control): D={ks.statistic:.4f}, p={ks.pvalue:.3g}, "
                     f"n_star={star.size}, n_ctrl={ctrl.size}")
    except Exception:
        ks_txt = ""
        notes.append("symcdf: scipy unavailable, KS annotation omitted.")

    xhi = max(float(np.quantile(ctrl, 0.999)), float(np.quantile(star, 0.99))) * 1.05
    n_star_off = int(np.sum(star > xhi))
    n_ctrl_off = int(np.sum(ctrl > xhi))
    ax.text(0.975, 0.60,
            f"median: star {med_s:.2f} vs control {med_c:.2f}\n"
            f"{ks_txt}"
            f"{100 * frac_above:.1f}% of stars exceed the control 95th pct (5% expected)\n"
            f"per-window $p$ floor $1/(1+{nctrl})$ = {1.0 / (1 + nctrl):.1e}\n"
            f"off scale: {n_star_off} star, {n_ctrl_off} control values",
            transform=ax.transAxes, ha="right", va="top", fontsize=5.6, color="0.25")

    ax.set_xlim(min(ctrl.min(), star.min()) * 0.95, xhi)
    ax.set_ylim(0, 1.02)
    ax.set_xlabel("peak S/N in window")
    ax.set_ylabel("empirical CDF")
    ax.legend(loc="lower right", fontsize=6.0)
    return save(fig, outdir, name)


# ======================================================================================
# FIGURE E (new) -- coverage_waterfall.pdf
# ======================================================================================

def fig_coverage_waterfall(D, sizes, outdir, notes):
    name = "coverage_waterfall.pdf"
    rows = D["good"]
    fig = new_fig(name, sizes)
    axes = fig.subplots(2, 1, height_ratios=[1.0, 11.0], sharex=True)
    axt, ax = axes

    order = sorted(D["systems"], key=lambda s: D["sys_d"][s])       # nearest at the top
    ypos = {s: len(order) - 1 - i for i, s in enumerate(order)}

    e = np.array([math.log10(r["eirp"]) for r in rows])
    vmin, vmax = float(np.floor(e.min() * 2) / 2), float(np.ceil(e.max() * 2) / 2)
    cmap = plt.get_cmap("viridis")
    norm = matplotlib.colors.Normalize(vmin=vmin, vmax=vmax)

    # Referee: distinguish fine- and coarse-channelised windows by line weight so
    # the class that carries drift discrimination is visible at a glance.
    segs_f, segs_c, cvals_f, cvals_c = [], [], [], []
    for r in rows:
        yy = ypos[r["system"]]
        seg = [(r["lo"], yy), (r["hi"], yy)]
        if r["res_x"] == "fine":
            segs_f.append(seg); cvals_f.append(math.log10(r["eirp"]))
        else:
            segs_c.append(seg); cvals_c.append(math.log10(r["eirp"]))
    for segs_, cvals_, lw in ((segs_c, cvals_c, 1.2), (segs_f, cvals_f, 3.8)):
        if segs_:
            ax.add_collection(LineCollection(segs_, colors=cmap(norm(np.array(cvals_))),
                                             linewidths=lw, capstyle="butt", zorder=3))
    from matplotlib.lines import Line2D as _L2D
    ax.legend(handles=[_L2D([], [], lw=3.8, color="0.35",
                            label="Class A: drift-resolved carriers ($<5$ MHz channels)"),
                       _L2D([], [], lw=1.2, color="0.35",
                            label="Class B: unresolved spectral excess")],
              loc="lower left", fontsize=7.2, framealpha=0.9, borderpad=0.4)

    for i, s in enumerate(order):
        if i % 2 == 0:
            ax.axhspan(ypos[s] - 0.5, ypos[s] + 0.5, color="0.955", lw=0, zorder=0)

    lo_all = min(r["lo"] for r in rows)
    hi_all = max(r["hi"] for r in rows)
    ax.set_xlim(math.floor(lo_all / 10) * 10 - 5, math.ceil(hi_all / 10) * 10 + 5)
    ax.set_ylim(-0.8, len(order) - 0.2)
    # Referee 1 (N6): at 0.72\textwidth the 81 row labels collided.  Every row
    # keeps its label, but alternate rows are set on the right-hand spine, which
    # doubles the vertical space each label has without enlarging the figure.
    lab = {s: f"{tidy(s)}  ({D['sys_d'][s]:.1f})" for s in order}
    left = [s for i, s in enumerate(order) if i % 2 == 0]
    right = [s for i, s in enumerate(order) if i % 2 == 1]
    ax.set_yticks([ypos[s] for s in left])
    ax.set_yticklabels([lab[s] for s in left], fontsize=6.6)
    ax.tick_params(axis="y", length=1.5, pad=1.2)
    axr = ax.secondary_yaxis("right")
    axr.set_yticks([ypos[s] for s in right])
    axr.set_yticklabels([lab[s] for s in right], fontsize=6.6)
    axr.tick_params(axis="y", length=1.5, pad=1.2)
    ax.set_xlabel("sky frequency (GHz)")
    ax.set_ylabel(f"independent system, ordered by distance in pc "
                  f"(nearest at top; {len(order)} systems)", fontsize=8.8)
    ax.grid(axis="y", visible=False)
    ax.grid(axis="x", color="0.88", lw=0.4)

    # marginal: how many systems cover each frequency, plus the union statistics
    edges = np.arange(math.floor(lo_all), math.ceil(hi_all) + 1.0, 1.0)
    cent = 0.5 * (edges[:-1] + edges[1:])
    cover = np.zeros(cent.size)
    for s in order:
        m = np.zeros(cent.size, dtype=bool)
        for r in rows:
            if r["system"] != s:
                continue
            m |= (cent >= r["lo"]) & (cent <= r["hi"])
        cover += m
    axt.fill_between(cent, 0, cover, step="mid", color=GREY, lw=0)
    axt.set_ylim(0, max(cover.max() * 1.15, 1))
    axt.set_ylabel("systems", fontsize=7.8)
    axt.tick_params(labelsize=5.8)
    axt.grid(axis="x", color="0.88", lw=0.4)

    iv = sorted((r["lo"], r["hi"]) for r in rows)
    merged = []
    for lo, hi in iv:
        if merged and lo <= merged[-1][1]:
            merged[-1][1] = max(merged[-1][1], hi)
        else:
            merged.append([lo, hi])
    union = sum(b - a for a, b in merged)
    gross = sum(r["hi"] - r["lo"] for r in rows)
    widths = np.array([r["hi"] - r["lo"] for r in rows])
    axt.set_title(f"{len(rows)} windows on {len(order)} systems: union {union:.1f} GHz "
                  f"in {len(merged)} disjoint intervals; summed window bandwidth "
                  f"{gross:.0f} GHz = {gross / union:.1f}$\\times$ the union",
                  fontsize=7.3, pad=3)

    sm = matplotlib.cm.ScalarMappable(norm=norm, cmap=cmap)
    cb = fig.colorbar(sm, ax=axes, location="right", fraction=0.030, pad=0.006,
                      aspect=45)
    cb.solids.set_rasterized(False)          # keep the colourbar vector, not an image
    cb.set_label(r"$\log_{10}\,$EIRP$_{5\sigma}$ (W)", fontsize=8.8)
    cb.ax.tick_params(labelsize=6.2)
    cb.outline.set_linewidth(0.5)

    notes.append(f"waterfall: union {union:.2f} GHz in {len(merged)} disjoint intervals; "
                 f"median window width {np.median(widths):.3f} GHz, widest interval "
                 f"{max(b - a for a, b in merged):.2f} GHz; summed bandwidth {gross:.1f} GHz "
                 f"({gross / union:.2f}x the union) -- i.e. the union is built from many "
                 f"narrow, repeatedly-observed islands, not from broad continuous coverage.")
    return save(fig, outdir, name)


# ======================================================================================
# FIGURE F (new) -- noise_qa.pdf
# ======================================================================================

def fig_noise_qa(D, sizes, outdir, notes):
    name = "noise_qa.pdf"
    fig = new_fig(name, sizes)
    ax = fig.add_subplot(111)

    keep = D["good"] + D["withheld"]
    defect = D["defect"]
    med = D["qa_med"]
    thresh = med * DEFECT_RATIO

    bands = sorted({r["band_x"] for r in D["uniq"] if r["band_x"] is not None})
    xof = {b: i for i, b in enumerate(bands)}
    rng = np.random.default_rng(20260909)          # fixed seed -> reproducible jitter

    for b in bands:
        sub = [r for r in keep if r["band_x"] == b]
        if not sub:
            continue
        xs = xof[b] + rng.uniform(-0.26, 0.26, len(sub))
        ax.plot(xs, [r["qa"] for r in sub], ls="none", marker=BAND_MARKER.get(b, "o"),
                ms=2.6, mfc=BAND_COLOUR.get(b, "0.5"), mec="none", alpha=0.75, zorder=3)

    ax.axhline(med, color="k", ls="-", lw=0.9)
    ax.axhline(thresh, color="#D55E00", ls="--", lw=1.0)
    lo_ok = min(r["qa"] for r in keep)
    hi_bad = max(r["qa"] for r in defect)
    ax.axhspan(hi_bad, lo_ok, color="#D55E00", alpha=0.10, lw=0, zorder=1)

    # Label the excluded windows INSIDE the empty gap: keeps the labels legible and
    # makes the emptiness of the gap the visual point of the figure.
    perband = collections.defaultdict(list)
    for r in sorted(defect, key=lambda r: (r["band_x"], r["qa"])):
        perband[r["band_x"]].append(r)
    for b, rs in perband.items():
        for i, r in enumerate(rs):
            xj = xof[b] + (i - (len(rs) - 1) / 2.0) * 0.34
            ax.plot([xj], [r["qa"]], ls="none", marker="X", ms=6.0, mfc="#D55E00",
                    mec="k", mew=0.5, zorder=6)
            ax.annotate(f"{tidy(r['star_name'], 16)} B{b}", xy=(xj, r["qa"]),
                        xytext=(xj, hi_bad * (5.5 ** (i + 1))),
                        fontsize=6.4, color="#8C3D00", va="bottom", ha="center",
                        arrowprops=dict(arrowstyle="-", lw=0.4, color="#8C3D00",
                                        shrinkA=1, shrinkB=2))

    # explicit double-headed arrow across the empty gap
    xg = len(bands) - 0.75
    ax.annotate("", xy=(xg, hi_bad), xytext=(xg, lo_ok),
                arrowprops=dict(arrowstyle="<->", lw=0.8, color="#D55E00"))
    ax.text(xg - 0.07, math.sqrt(thresh * lo_ok),
            f"empty gap\n{D['defect_gap']:.0f}$\\times$", fontsize=7.3, color="#8C3D00",
            ha="right", va="center")

    ax.set_yscale("log")
    ax.set_ylim(min(r["qa"] for r in defect) / 4.0, max(r["qa"] for r in keep) * 7.0)
    ax.set_xlim(-0.6, len(bands) - 0.4)
    ax.set_xticks(range(len(bands)))
    ax.set_xticklabels([f"Band {b}\n({sum(1 for r in keep if r['band_x'] == b)} pass)"
                        for b in bands], fontsize=7.5)
    ax.set_ylabel(r"$\sigma_{\rm rms}\sqrt{t_{\rm on}\,\Delta\nu_{\rm ch}}$"
                  "  (radiometer-invariant product)")
    ax.set_xlabel("ALMA receiver band (horizontal position jittered for clarity)")
    ax.grid(axis="x", visible=False)

    ax.text(0.015, 0.055,
            f"sample median = {sci(med)}\n"
            f"exclusion threshold, median/{int(1 / DEFECT_RATIO)} = {sci(thresh)}\n"
            f"lowest retained window = {sci(lo_ok)};  highest excluded = {sci(hi_bad)}\n"
            f"empty gap factor = {D['defect_gap']:.0f}$\\times$ "
            f"({math.log10(D['defect_gap']):.1f} decades): any threshold between\n"
            f"{sci(hi_bad * 1.01, 1)} and {sci(lo_ok * 0.99, 1)} selects exactly the same "
            f"{len(defect)} windows,\n"
            f"so the {int(1 / DEFECT_RATIO)}$\\times$ rule is not fine-tuned.\n"
            f"({D['n_withheld']} eps Eri Band 6 windows pass this test and are plotted, but "
            f"are withheld from the\nsearched sample for an unrelated primary-beam reason.)",
            transform=ax.transAxes, ha="left", va="bottom", fontsize=6.9, color="0.2",
            bbox=dict(fc="white", ec="0.8", lw=0.4, alpha=0.94, pad=2.4))

    ax.legend(handles=[Line2D([], [], color="k", lw=0.9, label="sample median"),
                       Line2D([], [], color="#D55E00", ls="--", lw=1.0,
                              label=f"median/{int(1 / DEFECT_RATIO)} exclusion threshold"),
                       Line2D([], [], ls="none", marker="X", ms=5, mfc="#D55E00", mec="k",
                              mew=0.5, label=f"excluded, noise defect ({len(defect)})")],
              loc="upper right", fontsize=7.1)

    notes.append(f"noise_qa: median {med:.4g}, threshold {thresh:.4g}, "
                 f"highest excluded {hi_bad:.4g}, lowest retained {lo_ok:.4g}, "
                 f"gap {D['defect_gap']:.1f}x.")
    return save(fig, outdir, name)


# ======================================================================================
# FIGURE G (new) -- occurrence_duty.pdf
# ======================================================================================

def rec_curve(a):
    """Measured injection recovery of the searched class as a function of
    injected amplitude in units of the window noise (Appendix: injection
    campaign).  Below 4 sigma nothing is recovered; above 10 sigma the curve
    is held at its largest measured value, which makes it a bound."""
    A = [4.0, 5.0, 6.0, 8.0, 10.0]
    R = [p / 100.0 for p in INJECTION_FINE_PCT]
    if a < A[0]:
        return 0.0
    if a >= A[-1]:
        return R[-1]
    for i in range(len(A) - 1):
        if A[i] <= a < A[i + 1]:
            t = (a - A[i]) / (A[i + 1] - A[i])
            return R[i] + t * (R[i + 1] - R[i])
    return 0.0


def fig_occurrence(D, sizes, outdir, notes):
    name = "occurrence_duty.pdf"
    rows = D["good"]
    fig = new_fig(name, sizes)
    fig.get_layout_engine().set(rect=(0.0, 0.105, 1.0, 0.895))
    ax = fig.add_subplot(111)

    bysys = collections.defaultdict(list)
    for r in rows:
        bysys[r["system"]].append(r)
    best_any = {s: min(r["eirp"] for r in rs) for s, rs in bysys.items()}
    best_fine = {s: min((r["eirp"] for r in rs if r["res_x"] == "fine"), default=None)
                 for s, rs in bysys.items()}

    P = np.logspace(14, 17, 121)

    def curve(kind, D_duty):
        out, nsys = [], []
        for p in P:
            Cs = []
            n = 0
            for s in bysys:
                if kind == "unit":
                    c = 1.0 if best_any[s] <= p else 0.0
                else:
                    # bandwidth-integrated measured recovery over the system's
                    # fine-channel windows, exactly the R_i(P) of the paper
                    fw = [r for r in bysys[s] if r["res_x"] == "fine"]
                    den = sum(abs(r["fhi"] - r["flo"]) for r in fw)
                    c = (sum(abs(r["fhi"] - r["flo"]) * rec_curve(5.0 * p / r["eirp"])
                             for r in fw) / den) if den > 0 else 0.0
                if c > 0:
                    n += 1
                Cs.append(D_duty * c)
            out.append(limit(Cs))
            nsys.append(n)
        return np.array([np.nan if v is None else v for v in out]), np.array(nsys)

    specs = [
        ("unit", 1.0, "k", "-", 1.6,
         r"(a) unit recovery $C=1$, $D_{\rm epoch}=1$"),
        ("measured", 1.0, BAND_COLOUR[6], "-", 2.1,
         r"(b) measured completeness, fine-calibrated systems, $D_{\rm epoch}=1$"),
        ("unit", 0.5, "k", "--", 1.1,
         r"(c) unit recovery, epoch duty cycle $D_{\rm epoch}=0.5$"),
        ("measured", 0.5, BAND_COLOUR[6], "--", 1.3,
         r"(d) measured completeness, $D_{\rm epoch}=0.5$"),
    ]
    tab = {}
    for kind, dd, col, ls, lw, lab in specs:
        y, nsys = curve(kind, dd)
        ax.plot(P, y, color=col, ls=ls, lw=lw, label=lab)
        tab[(kind, dd)] = (y, nsys)

    ax.set_xscale("log")
    ax.set_yscale("log")
    ax.set_xlim(P.min(), P.max())
    ax.set_ylim(0.025, 1.35)
    yt = [0.03, 0.05, 0.07, 0.1, 0.2, 0.3, 0.5, 0.7, 1.0]
    ax.set_yticks(yt)
    ax.set_yticklabels([f"{v:g}" for v in yt])
    ax.yaxis.set_minor_formatter(matplotlib.ticker.NullFormatter())
    ax.set_xlabel(r"EIRP threshold $P$ (W)")
    ax.set_ylabel(r"conditional 95% limit on in-band transmitter fraction $f$")

    # highlight the primary result
    yb, nb = tab[("measured", 1.0)]
    ok = np.isfinite(yb)
    ax.plot(P[ok], yb[ok], color=BAND_COLOUR[6], lw=2.1, zorder=5)
    j = int(np.argmin(np.abs(P - 1e16)))
    ax.plot([P[j]], [yb[j]], marker="o", ms=4.5, mfc="white", mec=BAND_COLOUR[6], mew=1.2,
            zorder=6, ls="none")
    ax.annotate(f"conditional model limit: $f\\lesssim{yb[j]:.2f}$ at $P=10^{{16}}$ W\n"
                f"({nb[j]} fine-calibrated systems; illustrative)",
                xy=(P[j], yb[j]), xytext=(-8, 26), textcoords="offset points",
                fontsize=6.2, color=BAND_COLOUR[6], ha="right",
                arrowprops=dict(arrowstyle="-", lw=0.6, color=BAND_COLOUR[6]))
    # Referee: mark the thresholded (C=1) counterpart from the tables on curve (a)
    ya, na = tab[("unit", 1.0)]
    ax.plot([P[j]], [ya[j]], marker="s", ms=3.6, mfc="white", mec="k", mew=1.0,
            zorder=6, ls="none")
    ax.annotate(f"thresholded $C{{\\equiv}}1$: $f<{ya[j]:.3f}$",
                xy=(P[j], ya[j]), xytext=(14, -20), textcoords="offset points",
                fontsize=6.0, color="0.25", ha="left",
                arrowprops=dict(arrowstyle="-", lw=0.6, color="0.4"))

    ax.legend(loc="upper right", fontsize=6.1)

    # where does each curve stop existing?
    nolim = []
    for (kind, dd), (y, nsys) in tab.items():
        bad = ~np.isfinite(y)
        if bad.any():
            nolim.append((kind, dd, float(P[bad].max())))
    if nolim:
        pmax = max(v[2] for v in nolim)
        ax.axvspan(P.min(), pmax, color="0.88", lw=0)
        ax.text(math.sqrt(P.min() * pmax), 0.2,
                "no bound exists here: the systems reaching $P$\n"
                "cannot exclude $f=1$ even at $f=1$",
                fontsize=5.8, color="0.3", ha="center", va="center", rotation=90,
                bbox=dict(fc="white", ec="none", alpha=0.85, pad=1.0))

    fig.text(0.5, 0.012,
             "Product-likelihood limit: $f$ solves "
             r"$\prod_i (1 - f\,D_{\rm epoch}\,C_i) = 0.05$, with $C_i$ the per-system recovery at "
             "threshold $P$ and $D_{\\rm epoch}$ the assumed epoch duty cycle (independent "
             "Bernoulli activity across a system's execution blocks; not the intra-track "
             "dwell fraction).\n"
             "An epoch duty cycle scales every $C_i$, so a low-duty-cycle population is bounded "
             "only where $D_{\\rm epoch}\\,C_i$ stays large enough to exclude $f=1$;\\n"
             "as $D_{\\rm epoch}\\rightarrow0$ no bound exists at any $P$. Curve (b) is the "
             "conditional model limit quoted in the text, illustrative rather than a "
             "prevalence bound.",
             ha="center", va="bottom", fontsize=5.9, color="0.3")

    for p_ref in (1e15, 1e16, 1e17):
        i = int(np.argmin(np.abs(P - p_ref)))
        notes.append("occurrence at P=%.0e : unit %.4f (n=%d) | measured %.4f (n=%d) | "
                     "unitD0.5 %.4f | measuredD0.5 %.4f"
                     % (p_ref, tab[("unit", 1.0)][0][i], tab[("unit", 1.0)][1][i],
                        tab[("measured", 1.0)][0][i], tab[("measured", 1.0)][1][i],
                        tab[("unit", 0.5)][0][i], tab[("measured", 0.5)][0][i]))
    return save(fig, outdir, name)


# ======================================================================================
# FIGURE H (new) -- control_diagnostics.pdf
# ======================================================================================

def _box(ax, groups, colours, ylabel, xlabels, note_fn=None):
    data = [g for g in groups]
    bp = ax.boxplot(data, widths=0.55, showfliers=False, patch_artist=True,
                    medianprops=dict(color="k", lw=0.9),
                    whiskerprops=dict(lw=0.6), capprops=dict(lw=0.6),
                    boxprops=dict(lw=0.5))
    for patch, c in zip(bp["boxes"], colours):
        patch.set_facecolor(c)
        patch.set_alpha(0.55)
    ax.set_xticks(range(1, len(groups) + 1))
    ax.set_xticklabels(xlabels, fontsize=6.2)
    ax.set_ylabel(ylabel, fontsize=7.0)
    ax.grid(axis="x", visible=False)
    return bp


def fig_control_diagnostics(D, sizes, outdir, notes, findings):
    name = "control_diagnostics.pdf"
    rows = D["good"]
    # v3.45 PAGE TRIM: panels (c) "versus achieved noise" and (d) "versus
    # on-source time" are dropped.  Neither was ever described in the caption
    # or referred to anywhere in the manuscript, in this or any earlier
    # version; their octile running medians are emitted into `notes` instead,
    # so the diagnostic is still on the record.  Restoring them costs ~200 pt.
    fig = new_fig(name, {name: (504.0, 215.0)})
    axes = [fig.subplots(1, 2)]

    try:
        from scipy.stats import kstest
    except Exception:
        kstest = None

    def unif_p(sub):
        if kstest is None or len(sub) < 5:
            return float("nan")
        return float(kstest([r["p_emp"] for r in sub], "uniform").pvalue)

    # ---- (a) per-window control maximum and star statistic, by band
    ax = axes[0][0]
    bands = bands_present(rows)
    groups_c = [[r["ctrl_max_all"] for r in rows if r["band_x"] == b] for b in bands]
    groups_s = [[r["star_snr"] for r in rows if r["band_x"] == b] for b in bands]
    _box(ax, groups_c, [BAND_COLOUR.get(b, "0.6") for b in bands],
         "peak S/N in window", [f"B{b}\n({len(g)})" for b, g in zip(bands, groups_c)])
    for i, g in enumerate(groups_s):
        ax.plot([i + 1], [np.median(g)], marker="D", ms=3.4, mfc="k", mec="none", ls="none",
                zorder=5)
    ax.set_title("(a) by ALMA band  ($p$: KS of the per-window rank against U(0,1))",
                 fontsize=7.0)
    ax.set_xlabel("")
    ytop = ax.get_ylim()[1]
    ax.set_ylim(None, ytop + 0.55)
    for i, b in enumerate(bands):
        pu = unif_p([r for r in rows if r["band_x"] == b])
        ax.text(i + 1, ytop + 0.42, "$p$=%.2f" % pu if pu == pu else "$p$: n/a",
                ha="center", va="top", fontsize=5.4,
                color="#8C3D00" if (pu == pu and pu < 0.05) else "0.35")

    # ---- (b) by resolution class
    ax = axes[0][1]
    classes = ["fine", "coarse"]
    gc = [[r["ctrl_max_all"] for r in rows if r["res_x"] == c] for c in classes]
    gs = [[r["star_snr"] for r in rows if r["res_x"] == c] for c in classes]
    _box(ax, gc, [BAND_COLOUR[3], BAND_COLOUR[6]], "peak S/N in window",
         [f"fine (<5 MHz)\n({len(gc[0])})", f"coarse ($\\geq$5 MHz)\n({len(gc[1])})"])
    for i, g in enumerate(gs):
        ax.plot([i + 1], [np.median(g)], marker="D", ms=3.4, mfc="k", mec="none", ls="none",
                zorder=5)
    ax.set_title("(b) by channelisation class", fontsize=7.4)
    pf, pc = unif_p([r for r in rows if r["res_x"] == "fine"]), \
        unif_p([r for r in rows if r["res_x"] == "coarse"])
    ax.text(0.02, 0.03,
            f"KS of the per-window rank $p$ against U(0,1):\nfine $p$={pf:.3f},  "
            f"coarse $p$={pc:.3f}",
            transform=ax.transAxes, ha="left", va="bottom", fontsize=5.8,
            color="#8C3D00" if (pf == pf and pf < 0.05) else "0.3")

    # ---- (c)/(d) retired as panels; reported as numbers instead
    x = np.array([r["rms"] for r in rows])
    t = np.array([r["onsrc"] for r in rows])
    yv = np.array([r["ctrl_max_all"] for r in rows])
    for lab, v in (("per-channel rms (mJy)", x), ("on-source time (s)", t)):
        qs = np.percentile(v, np.linspace(0, 100, 9))
        pts = []
        for a, bnd in zip(qs[:-1], qs[1:]):
            m = (v >= a) & (v <= bnd)
            if m.sum() > 3:
                pts.append((float(np.median(v[m])), float(np.median(yv[m]))))
        notes.append("control maximum vs %s, octile running median: %s"
                     % (lab, "; ".join("%.3g -> %.2f" % p for p in pts)))
    notes.append("control maximum: %d windows exceed 8.2 (max %.1f)"
                 % (int(np.sum(yv > 8.2)), yv.max()))

    fig.suptitle("Control-ensemble behaviour across strata "
                 f"({len(rows)} windows, {D['n_ctrl']} control positions each; "
                 "boxes = per-window control maximum, black diamonds = median on-star peak)",
                 fontsize=7.2)

    # ---- honest reporting
    for lab, sub in ([(f"B{b}", [r for r in rows if r["band_x"] == b]) for b in bands] +
                     [(c, [r for r in rows if r["res_x"] == c]) for c in classes]):
        cm = np.array([r["ctrl_max_all"] for r in sub])
        pu = unif_p(sub)
        nsbr = sum(1 for r in sub if r["sbr"])
        notes.append("control stratum %-7s n=%3d  ctrl-max med %.2f  star med %.2f  "
                     "KS(p_emp vs U) p=%.3g  star>own ctrl max: %d (expected %.2f)"
                     % (lab, len(sub), np.median(cm),
                        np.median([r["star_snr"] for r in sub]), pu, nsbr,
                        len(sub) / (D["n_ctrl"] + 1.0)))
        if pu == pu and pu < 0.05:
            findings.append(f"control_diagnostics: stratum '{lab}' fails the U(0,1) test on the "
                            f"per-window rank statistic (KS p={pu:.3f}, n={len(sub)}).")
        exp = len(sub) / (D["n_ctrl"] + 1.0)
        if nsbr > 0 and exp > 0 and nsbr / exp > 4:
            findings.append(f"control_diagnostics: stratum '{lab}' has {nsbr} windows whose "
                            f"on-star peak beats their own control maximum, vs {exp:.2f} "
                            f"expected under exchangeability ({nsbr / exp:.0f}x).")
    return save(fig, outdir, name)


# ======================================================================================
# driver
# ======================================================================================

def main(argv=None):
    ap = argparse.ArgumentParser(description="v3.28 figure set",
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--data", default=DEFAULT_DATA)
    ap.add_argument("--outdir", default=DEFAULT_OUTDIR)
    ap.add_argument("--sizes", default=DEFAULT_SIZES)
    ap.add_argument("--src-figures", default=DEFAULT_SRC)
    ap.add_argument("--no-copy", action="store_true")
    args = ap.parse_args(argv)

    set_style()
    os.makedirs(args.outdir, exist_ok=True)
    notes, findings, asserts = [], [], []

    copied = []
    if not args.no_copy and os.path.isdir(args.src_figures):
        for src in sorted(glob.glob(os.path.join(args.src_figures, "*.pdf"))):
            dst = os.path.join(args.outdir, os.path.basename(src))
            if os.path.abspath(src) != os.path.abspath(dst):
                shutil.copy2(src, dst)
                copied.append(os.path.basename(src))

    D = load_and_select(args.data, notes)
    cross_check(D, notes)
    sizes = target_sizes(args.sizes)

    print("=" * 84)
    print("ASTRA / 0-40 pc ALMA technosignature survey -- v3.28 figure set")
    print(f"  data     : {args.data}   (snapshot {D['snapshot']})")
    print(f"  outdir   : {args.outdir}")
    print(f"  copied   : {len(copied)} PDFs from {args.src_figures}")
    print("=" * 84)

    print("\nSELECTION FUNNEL (selection.pdf) -- every count derived from the export")
    print("-" * 84)
    prev_v = prev_k = None
    for lab, val, kind in selection_stages(D):
        clean = re.sub(r"\$[^$]*\$", lambda m: m.group(0).strip("$")
                       .replace(r"\geq5\sigma", ">=5 sigma"), lab).replace("--", "-")
        frac = ""
        if prev_v and prev_k == kind:
            frac = f"{100.0 * val / prev_v:6.1f}% of previous"
        elif prev_v:
            frac = "(different unit; ratio not meaningful)"
        print(f"  {clean:<52s} {val:6d}   {frac}")
        prev_v, prev_k = val, kind
    print("-" * 84)
    print(f"  catalogue rows {D['n_raw']}  duplicates {D['n_dup']}  unique {D['n_uniq']}  "
          f"noise-defect {D['n_defect']}  withheld {D['n_withheld']}")
    print(f"  stars {D['n_stars']}  independent systems {D['n_systems']}  "
          f"star-band datasets {D['n_starbands']}")
    print(f"  flagged windows: " +
          "; ".join(f"{r['star_name']} B{r['band_x']} "
                    f"({r['vel_off']:+.0f} km/s from {r['line']})" if r["vel_off"] is not None
                    else f"{r['star_name']} B{r['band_x']} (no line)" for r in D["flagged"]))

    figs = []
    figs.append(fig_completeness(D, sizes, args.outdir, notes, asserts))
    figs.append(fig_completeness_sensitivity(D, sizes, args.outdir))
    figs.append(fig_drift(D, sizes, args.outdir, notes))
    figs.append(fig_selection(D, sizes, args.outdir))
    figs.append(fig_symcdf(D, sizes, args.outdir, notes))
    figs.append(fig_coverage_waterfall(D, sizes, args.outdir, notes))
    figs.append(fig_noise_qa(D, sizes, args.outdir, notes))
    figs.append(fig_occurrence(D, sizes, args.outdir, notes))
    figs.append(fig_control_diagnostics(D, sizes, args.outdir, notes, findings))

    print("\nFIGURES WRITTEN")
    print("-" * 84)
    print(f"  {'file':<32s} {'w x h pt':>16s} {'aspect':>7s} {'target':>7s} {'kB':>7s}")
    for path in figs:
        base = os.path.basename(path)
        try:
            import pymupdf
            doc = pymupdf.open(path)
            rect = doc[0].rect
            got = rect.width / rect.height
            wh = f"{rect.width:.0f} x {rect.height:.0f}"
            doc.close()
        except Exception:
            got, wh = float("nan"), "?"
        tw, th = sizes.get(base, (float("nan"), float("nan")))[:2]
        print(f"  {base:<32s} {wh:>16s} {got:7.3f} {tw / th:7.3f} "
              f"{os.path.getsize(path) / 1024.0:7.1f}")

    for title, items in (("ASSERTIONS CHECKED", asserts), ("NOTES", notes),
                         ("*** THINGS THAT LOOK DISCREPANT ***", findings)):
        if items:
            print(f"\n{title}")
            print("-" * 84)
            for it in items:
                print(f"  - {it}")
    print()
    return 0


if __name__ == "__main__":
    sys.exit(main())
