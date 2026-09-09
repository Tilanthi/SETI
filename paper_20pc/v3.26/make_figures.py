#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
make_figures.py -- regenerate all data figures for the 40 pc ALMA technosignature
paper (v3.26) directly from the frozen survey export.

USAGE
-----
    python3 make_figures.py [--data PATH] [--outdir PATH] [--sizes PATH]

    Defaults:
        --data    /workspace/SETI/figwork/v326_data.json
        --outdir  /workspace/SETI/paper_20pc/v3.26/figures
        --sizes   /workspace/SETI/figwork/target_sizes.txt

The script is written to be re-run unchanged as the survey grows: every count,
limit, axis range and legend label is derived from the data at run time.  There
are no hard-coded sample sizes.  Re-export ``v326_data.json`` with more rows and
re-run; the figures follow.

INPUT FORMAT
------------
JSON with keys ``snapshot`` (ISO time string), ``rows`` (one record per searched
spectral window) and ``census`` (one record per star in the 40 pc ALMA-crossmatched
candidate list).  See ``describe_data()`` below for the fields used.

FIGURES PRODUCED (13)
---------------------
    sample_distance_distribution.pdf  cumulative N(<d): searched vs census, to 40 pc
    star_coverage.pdf                 searched bandwidth per star, stacked by ALMA band
    eirp_continuum_vs_distance.pdf    EIRP_5sigma and continuum rms vs distance
    eirp_vs_frequency.pdf             EIRP_5sigma vs window centre frequency
    freq_coverage.pdf                 sky-frequency coverage of the release
    eirp_vs_linewidth.pdf             EIRP threshold vs assumed transmitter linewidth
    drift_acceleration.pdf            drift-rate ceiling as a selection function
    symcdf.pdf                        symmetric star-vs-control null (ECDFs)
    aumic_control_maxima.pdf          per-window control maxima, AU Mic marked
    selection.pdf                     selection funnel (counts printed to console)
    eirp_context.pdf                  EIRP distribution vs benchmark powers
    completeness.pdf                  achieved-sensitivity completeness (NOT injection)
    bpic_velocity_space.pdf           stellar-frame velocity offsets of flagged windows

``pipeline_schematic.pdf`` is a hand-drawn schematic with no underlying data and is
deliberately NOT regenerated here; the existing file is left untouched.

DESIGN NOTES / DECISIONS (please read before editing)
----------------------------------------------------
* Aspect ratios are read from ``target_sizes.txt`` and reproduced exactly.  Figures
  are saved with a *constrained* layout and WITHOUT ``bbox_inches='tight'`` so the
  saved canvas is exactly the requested width x height in points; LaTeX then sets the
  width and the paper length does not change.
* ``flo``/``fhi`` are stored in sideband order and are swapped for 231/448 rows in
  the v3.26 export (lower-sideband windows).  Everything here uses
  ``lo = min(flo, fhi)``, ``hi = max(flo, fhi)``; the centre ``0.5*(flo+fhi)`` is
  unaffected by the swap.
* ``band`` is null for 9 rows and ``res`` is null for the same 9.  Both are
  reconstructed from the data itself (band from the window centre frequency using
  the standard ALMA receiver-band edges; resolution class from ``chanw`` with the
  same <1 MHz / 1-5 MHz / >=5 MHz cuts used in the export).  Reconstruction was
  verified against all 439 rows where the fields *are* populated: 0 disagreements.
* ``census[*]['d']`` is 0.0 for every star in the v3.26 export -- the distances were
  not written out.  The script therefore falls back to the ranked candidate list
  (``ranked_master40pc.csv``), joining on ``rank`` and verifying that the star names
  agree exactly before using it.  A loud warning is printed whenever the fallback is
  used.  Once the exporter is fixed, the JSON values are used automatically and the
  fallback silently stops mattering.
* star_coverage: all searched stars are plotted individually (86 in this release) with
  ~4 pt tick labels, which is legible at the printed column width.  If the sample
  grows past ~110 stars the labels will start to collide; the code prints a warning
  and thins the labels to every Nth star in that case, keeping every bar.
* completeness: THERE IS NO INJECTION-RECOVERY DATA IN THE EXPORT.  This figure is
  therefore an *achieved-sensitivity* completeness curve (cumulative fraction of
  windows/stars reaching a given EIRP threshold), explicitly labelled as such.  The
  console output says so on every run.

Author: ASTRA PA, for G. J. White.
"""

from __future__ import annotations

import statistics
import argparse
import csv
import json
import math
import os
import re
import sys
from collections import Counter, defaultdict

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
from matplotlib.lines import Line2D
from matplotlib.patches import Patch

# --------------------------------------------------------------------------------------
# constants
# --------------------------------------------------------------------------------------

C_KMS = 299792.458          # speed of light, km/s
C_MS = 299792458.0          # speed of light, m/s
GM_SUN = 1.32712440018e20   # m^3 s^-2
AU_M = 1.495978707e11
DAY_S = 86400.0

# ALMA receiver band edges (GHz), used only to reconstruct the 9 rows with band=null.
ALMA_BANDS = {
    3: (84.0, 116.0),
    4: (125.0, 163.0),
    5: (163.0, 211.0),
    6: (211.0, 275.0),
    7: (275.0, 373.0),
    8: (385.0, 500.0),
    9: (602.0, 720.0),
    10: (787.0, 950.0),
}

# Okabe-Ito colourblind-safe palette, one colour + one marker per ALMA band.
BAND_COLOUR = {
    3: "#0072B2",   # blue
    4: "#009E73",   # bluish green
    5: "#E69F00",   # orange
    6: "#D55E00",   # vermillion
    7: "#CC79A7",   # reddish purple
    8: "#56B4E9",   # sky blue
    9: "#666666",
    10: "#000000",
}
BAND_MARKER = {3: "o", 4: "s", 5: "^", 6: "v", 7: "D", 8: "P", 9: "X", 10: "*"}
GREY = "#4D4D4D"

# Literature benchmark powers used in eirp_context.pdf.  ONLY these two, both are
# textbook reference numbers rather than survey results, and both are labelled as
# power comparisons rather than as competing limits.
BENCH_ARECIBO_W = 2.0e13      # Arecibo S-band planetary radar, ~1 MW into 10^7 gain
BENCH_KARDASHEV_I_W = 1.0e17  # 10^-... fraction-of-a-type-I reference power

# Fallback locations for the census distances (see module docstring).
CENSUS_DISTANCE_FALLBACKS = [
    "/workspace/SETI/ranked_master40pc.csv",
    "/workspace/SETI/figwork/ranked_master40pc.csv",
]

DEFAULT_DATA = "/workspace/SETI/figwork/v326_data.json"
DEFAULT_OUTDIR = "/workspace/SETI/paper_20pc/v3.26/figures"
DEFAULT_SIZES = "/workspace/SETI/figwork/target_sizes.txt"


# --------------------------------------------------------------------------------------
# style
# --------------------------------------------------------------------------------------

def set_style() -> None:
    """Serif, modest sizes, light grid -- matched to the journal body text."""
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
        "pdf.compression": 6,
    })


# --------------------------------------------------------------------------------------
# data loading / normalisation
# --------------------------------------------------------------------------------------

def describe_data() -> str:
    return __doc__


def band_from_freq(f_ghz: float):
    for b, (lo, hi) in ALMA_BANDS.items():
        if lo <= f_ghz <= hi:
            return b
    return None


def res_class(chanw_hz: float) -> str:
    """Channelisation class.  Same cuts as the survey export's `res` string."""
    if chanw_hz < 1.0e6:
        return "fine"
    if chanw_hz < 5.0e6:
        return "medium"
    return "coarse"


def load_census_distances(census, warnings):
    """Return {rank: distance_pc}, from the JSON if populated, else from the ranked CSV."""
    have = {c["rank"]: c.get("d") for c in census}
    if any((v or 0) > 0 for v in have.values()):
        missing = [r for r, v in have.items() if not v or v <= 0]
        if missing:
            warnings.append(
                f"census: {len(missing)} of {len(have)} stars have non-positive distance; "
                "they are dropped from the cumulative-distance figure."
            )
        return {r: v for r, v in have.items() if v and v > 0}

    warnings.append(
        "census distances are ALL ZERO in the export ('d' field never populated). "
        "Falling back to the ranked candidate list for distances -- FIX THE EXPORTER."
    )
    by_name = {c["rank"]: c["name"] for c in census}
    for path in CENSUS_DISTANCE_FALLBACKS:
        if not os.path.exists(path):
            continue
        out, mismatch = {}, 0
        with open(path) as fh:
            for row in csv.DictReader(fh):
                try:
                    rank = int(row["rank"])
                    dist = float(row["dist_pc"])
                except (KeyError, TypeError, ValueError):
                    continue
                if rank in by_name and row.get("name", "") != by_name[rank]:
                    mismatch += 1
                    continue
                if dist > 0:
                    out[rank] = dist
        if mismatch:
            warnings.append(f"census fallback {path}: {mismatch} rank/name mismatches skipped.")
        if len(out) >= 0.5 * len(census):
            warnings.append(
                f"census distances recovered for {len(out)}/{len(census)} stars from {path}."
            )
            return out
    warnings.append("NO census distances available from any source; census curve omitted.")
    return {}


DEFECT_RATIO = 1.0e-2   # keep windows within 100x of the median radiometer product


def radiometer_product(r):
    """rms * sqrt(t_onsource * dnu_chan).

    For a correctly weighted interferometric measurement this is set by the
    system temperature and collecting area, so it is roughly constant across a
    heterogeneous archive -- varying by a factor of a few, not orders of
    magnitude.  It is therefore a physical consistency check on the noise, and
    it is independent of distance, band and integration time by construction.
    """
    if not (r.get("rms") and r.get("onsrc") and r.get("chanw")):
        return None
    return r["rms"] * math.sqrt(r["onsrc"] * r["chanw"])


def flag_noise_defect(rows, warnings):
    """Mark windows whose noise is physically implausible.

    This is the generalisation of the named exclusion carried through v3.25
    (one window each in HD 10647 and HD 139664).  That exclusion was a list of
    two names; as the sample grew past 20 pc the same correlator-setup defect
    recurred in further windows, which a name list cannot catch.  The rule here
    is the physical one: a window is excluded if its radiometer product falls
    more than 1/DEFECT_RATIO below the sample median.  On the current export the
    excluded population is separated from the rest by a factor of ~1500, so the
    threshold is not fine-tuned -- any cut between ~1e-3 and ~0.1 selects the
    same windows.
    """
    prods = [p for p in (radiometer_product(r) for r in rows) if p]
    if not prods:
        return rows, []
    med = statistics.median(prods)
    excluded = []
    for r in rows:
        p = radiometer_product(r)
        r["radiometer_product"] = p
        r["noise_defect"] = bool(p is not None and p < med * DEFECT_RATIO)
        if r["noise_defect"]:
            excluded.append(r)
    if excluded:
        warnings.append(
            "noise-defect filter: excluded %d of %d windows whose radiometer "
            "product lies >%.0fx below the median (%s); best EIRP among them "
            "%.3g W, which would otherwise set the survey's headline depth"
            % (len(excluded), len(rows), 1.0 / DEFECT_RATIO,
               ", ".join(sorted({e["target"] for e in excluded})),
               min(e["eirp"] for e in excluded if e.get("eirp"))))
    return [r for r in rows if not r["noise_defect"]], excluded


def load_data(path):
    """Read the export and normalise it.  Returns (rows, census, meta, warnings)."""
    warnings = []
    with open(path) as fh:
        blob = json.load(fh)

    rows = blob["rows"]
    census = blob["census"]

    n_band_fixed = n_res_fixed = n_swapped = 0
    band_check_bad = res_check_bad = 0

    for r in rows:
        flo, fhi = r["flo"], r["fhi"]
        r["lo"] = min(flo, fhi)
        r["hi"] = max(flo, fhi)
        r["fc"] = 0.5 * (flo + fhi)                # GHz, unaffected by sideband order
        if flo > fhi:
            n_swapped += 1

        derived_band = band_from_freq(r["fc"])
        if r.get("band") is None:
            r["band"] = derived_band
            r["band_derived"] = True
            n_band_fixed += 1
        else:
            r["band_derived"] = False
            if derived_band is not None and derived_band != r["band"]:
                band_check_bad += 1

        derived_res = res_class(r["chanw"])
        if r.get("res") is None:
            r["res_class"] = derived_res
            n_res_fixed += 1
        else:
            r["res_class"] = derived_res
            if not str(r["res"]).startswith(derived_res):
                res_check_bad += 1

        # symmetric-test p with add-one correction: (1 + #controls >= star) / (1 + n_ctrl)
        nctrl = r.get("n_ctrl") or (len(r["ctrl_all"]) if r.get("ctrl_all") else 0)
        r["n_ctrl_eff"] = nctrl
        r["p_sym"] = (1.0 + r["n_ge_star"]) / (1.0 + nctrl) if nctrl else float("nan")

        # stellar-frame velocity offset from the nearest catalogued line, km/s
        if r.get("line") and r.get("line_off") is not None and r["fc"] > 0:
            r["v_off"] = C_KMS * (r["line_off"] * 1.0e6) / (r["fc"] * 1.0e9)
        else:
            r["v_off"] = None

    if n_swapped:
        warnings.append(f"{n_swapped}/{len(rows)} rows have flo > fhi (lower sideband); "
                        "min/max used throughout.")
    if n_band_fixed:
        warnings.append(f"{n_band_fixed} rows had band=null; reconstructed from centre frequency.")
    if n_res_fixed:
        warnings.append(f"{n_res_fixed} rows had res=null; reconstructed from chanw.")
    if band_check_bad:
        warnings.append(f"WARNING: {band_check_bad} rows disagree with the frequency->band map.")
    if res_check_bad:
        warnings.append(f"WARNING: {res_check_bad} rows disagree with the chanw->resolution map.")

    census_d = load_census_distances(census, warnings)
    meta = {
        "snapshot": blob.get("snapshot", "unknown"),
        "census_d": census_d,
        "n_census": len(census),
    }
    rows, defect_rows = flag_noise_defect(rows, warnings)
    meta["n_defect_excluded"] = len(defect_rows)
    meta["defect_targets"] = sorted({d["target"] for d in defect_rows})

    return rows, census, meta, warnings


# --------------------------------------------------------------------------------------
# small helpers
# --------------------------------------------------------------------------------------

def target_sizes(path):
    """Parse target_sizes.txt -> {filename: (width_pt, height_pt, aspect)}."""
    out = {}
    if not os.path.exists(path):
        return out
    pat = re.compile(r"^(\S+\.pdf)\s+([\d.]+)\s*x\s*([\d.]+)\s*pt\s+aspect\s+([\d.]+)")
    with open(path) as fh:
        for line in fh:
            m = pat.match(line.strip())
            if m:
                out[m.group(1)] = (float(m.group(2)), float(m.group(3)), float(m.group(4)))
    return out


def new_fig(name, sizes, fallback=(468.0, 302.0)):
    """Figure sized exactly to the target box (points -> inches), constrained layout."""
    w_pt, h_pt = sizes.get(name, (fallback[0], fallback[1], 0))[:2] if name in sizes else fallback
    fig = plt.figure(figsize=(w_pt / 72.0, h_pt / 72.0), layout="constrained")
    fig.get_layout_engine().set(w_pad=0.012, h_pad=0.012, wspace=0.02, hspace=0.02)
    return fig


def save(fig, outdir, name):
    """Save WITHOUT bbox_inches='tight' so the canvas keeps the exact target aspect."""
    path = os.path.join(outdir, name)
    fig.savefig(path, format="pdf")
    plt.close(fig)
    return path


def band_label(b, n=None):
    txt = f"Band {b}" if b is not None else "band unknown"
    return f"{txt} ({n})" if n is not None else txt


def bands_present(rows):
    return sorted({r["band"] for r in rows if r["band"] is not None})


def ecdf(values):
    """Return (x, F) of the empirical CDF, x sorted ascending."""
    x = np.sort(np.asarray(values, dtype=float))
    f = np.arange(1, x.size + 1) / x.size
    return x, f


def thin(x, f, n=1500):
    """Thin a big ECDF to ~n points for a light vector file (keeps the ends)."""
    if x.size <= n:
        return x, f
    idx = np.unique(np.concatenate([[0], np.linspace(0, x.size - 1, n).astype(int), [x.size - 1]]))
    return x[idx], f[idx]


def sci(v, sig=2):
    """LaTeX-ish scientific notation, e.g. 1.0e15 -> '1.0$\\times10^{15}$'."""
    if v <= 0:
        return f"{v:g}"
    exp = int(math.floor(math.log10(v)))
    mant = v / 10.0 ** exp
    return f"{mant:.{sig - 1}f}" + r"$\times10^{" + str(exp) + r"}$"


def unique_span_ghz(intervals):
    """Total union length (GHz) of a list of (lo, hi) intervals."""
    if not intervals:
        return 0.0
    merged = []
    for lo, hi in sorted(intervals):
        if merged and lo <= merged[-1][1]:
            merged[-1][1] = max(merged[-1][1], hi)
        else:
            merged.append([lo, hi])
    return sum(hi - lo for lo, hi in merged)


# --------------------------------------------------------------------------------------
# derived survey quantities (single source of truth for every count in the paper)
# --------------------------------------------------------------------------------------

def survey_stats(rows, census, meta):
    stars = sorted({r["star_name"] for r in rows})
    star_d = {}
    for r in rows:
        star_d.setdefault(r["star_name"], r["dist_pc"])

    hits = [r for r in rows if r["star_snr"] > 5.0]
    passed = [r for r in hits if r["n_ge_star"] == 0]
    vetted = [r for r in passed if not r.get("likely")]

    return {
        "n_census": len(census),
        "n_census_with_d": len(meta["census_d"]),
        "n_stars": len(stars),
        "stars": stars,
        "star_d": star_d,
        "n_targets": len({r["target"] for r in rows}),
        "n_windows": len(rows),
        "n_hits": len(hits),
        "hits": hits,
        "n_pass": len(passed),
        "passed": passed,
        "n_vetted": len(vetted),
        "vetted": vetted,
        "n_likely": sum(1 for r in rows if r.get("likely")),
        "eirp_median": float(np.median([r["eirp"] for r in rows])),
        "eirp_min": min(r["eirp"] for r in rows),
        "eirp_max": max(r["eirp"] for r in rows),
        "union_ghz": unique_span_ghz([(r["lo"], r["hi"]) for r in rows]),
        "sum_bw_ghz": sum(r["bw"] for r in rows) / 1e9,
        "n_ctrl": int(np.median([r["n_ctrl_eff"] for r in rows])),
    }


# ======================================================================================
# FIGURE 1 -- sample_distance_distribution.pdf
# ======================================================================================

def fig_sample_distance(rows, census, meta, st, sizes, outdir):
    name = "sample_distance_distribution.pdf"
    fig = new_fig(name, sizes)
    ax = fig.add_subplot(111)

    d_cen = np.sort(np.array(list(meta["census_d"].values()), dtype=float))
    d_srch = np.sort(np.array([st["star_d"][s] for s in st["stars"]], dtype=float))
    dmax = 40.0

    for arr, colour, lw, lab in (
        (d_cen, GREY, 1.0,
         f"40 pc ALMA-crossmatched census (n={d_cen.size})"),
        (d_srch, BAND_COLOUR[3], 1.6,
         f"searched in this release (n={d_srch.size})"),
    ):
        if arr.size == 0:
            continue
        x = np.concatenate([[0.0], arr, [dmax]])
        y = np.concatenate([[0.0], np.arange(1, arr.size + 1), [arr.size]])
        ax.step(x, y, where="post", color=colour, lw=lw, label=lab)

    ax.axvline(20.0, color="k", ls="--", lw=0.8, alpha=0.7)
    ax.text(20.0, ax.get_ylim()[1] * 0.045, " former 20 pc limit",
            rotation=90, va="bottom", ha="left", fontsize=6.2, color="k", alpha=0.8,
            bbox=dict(fc="white", ec="none", alpha=0.75, pad=0.6))

    ax.set_xlim(0, dmax)
    ax.set_ylim(0, max(d_cen.size, d_srch.size) * 1.08 if d_cen.size else None)
    ax.set_xlabel("distance $d$ (pc)")
    ax.set_ylabel("cumulative number of stars, $N(<d)$")
    ax.legend(loc="upper left")

    if d_cen.size and d_srch.size:
        frac_in = 100.0 * np.sum(d_srch <= 20.0) / max(np.sum(d_cen <= 20.0), 1)
        frac_all = 100.0 * d_srch.size / d_cen.size
        ax.text(0.985, 0.045,
                f"searched fraction: {frac_all:.0f}% of the census "
                f"({frac_in:.0f}% within 20 pc)",
                transform=ax.transAxes, ha="right", va="bottom",
                fontsize=6.2, color="0.3")
    return save(fig, outdir, name)


# ======================================================================================
# FIGURE 2 -- star_coverage.pdf
# ======================================================================================

def fig_star_coverage(rows, st, sizes, outdir, warnings):
    name = "star_coverage.pdf"
    fig = new_fig(name, sizes)
    ax = fig.add_subplot(111)

    per_star = defaultdict(lambda: defaultdict(float))     # star -> band -> summed bw (GHz)
    spans = defaultdict(list)
    for r in rows:
        per_star[r["star_name"]][r["band"]] += r["bw"] / 1e9
        spans[r["star_name"]].append((r["lo"], r["hi"]))

    # nearest star at the BOTTOM -> sort descending in distance, plot bottom-up
    stars = sorted(per_star, key=lambda s: -st["star_d"][s])
    y = np.arange(len(stars))
    bands = bands_present(rows)

    left = np.zeros(len(stars))
    for b in bands:
        w = np.array([per_star[s].get(b, 0.0) for s in stars])
        ax.barh(y, w, left=left, height=0.72, color=BAND_COLOUR.get(b, "0.5"),
                edgecolor="none", label=band_label(b))
        left += w

    uniq = np.array([unique_span_ghz(spans[s]) for s in stars])
    ax.plot(uniq, y, ls="none", marker="|", ms=3.2, mew=0.7, color="k",
            label="unique sky coverage")

    labels = [f"{s}  ({st['star_d'][s]:.1f})" for s in stars]
    fs = 4.0
    step = 1
    if len(stars) > 110:                       # keep every bar, thin the labels
        step = int(math.ceil(len(stars) / 110.0))
        warnings.append(f"star_coverage: {len(stars)} stars -> labelling every {step}th star.")
    ax.set_yticks(y[::step])
    ax.set_yticklabels(labels[::step], fontsize=fs)
    ax.tick_params(axis="y", length=1.5, pad=1.2)
    ax.set_ylim(-0.8, len(stars) - 0.2)
    ax.set_xlim(0, left.max() * 1.02)
    ax.set_xlabel("searched frequency coverage per star (GHz)")
    ax.grid(axis="y", visible=False)
    ax.legend(loc="lower right", ncol=2, fontsize=5.6)
    ax.text(0.985, 0.985,
            f"{len(stars)} stars, {st['n_windows']} windows\n"
            "bars: summed window bandwidth (repeat epochs included)\n"
            "ticks: unique sky frequency covered",
            transform=ax.transAxes, ha="right", va="top", fontsize=5.4, color="0.3",
            bbox=dict(fc="white", ec="0.8", lw=0.4, alpha=0.92, pad=1.6))
    return save(fig, outdir, name)


# ======================================================================================
# FIGURE 3 -- eirp_continuum_vs_distance.pdf
# ======================================================================================

def fig_eirp_continuum(rows, st, sizes, outdir):
    name = "eirp_continuum_vs_distance.pdf"
    fig = new_fig(name, sizes)
    axes = fig.subplots(1, 2)
    bands = bands_present(rows)
    counts = Counter(r["band"] for r in rows)

    for b in bands:
        sub = [r for r in rows if r["band"] == b]
        x = [r["dist_pc"] for r in sub]
        axes[0].plot(x, [r["eirp"] for r in sub], ls="none", marker="v", ms=3.0,
                     mfc=BAND_COLOUR.get(b, "0.5"), mec="none", alpha=0.85,
                     label=band_label(b, counts[b]))
        # panel (b) shows a measurement, not a limit -> round markers, not triangles
        axes[1].plot(x, [r["rms"] for r in sub], ls="none", marker="o", ms=2.6,
                     mfc=BAND_COLOUR.get(b, "0.5"), mec="none", alpha=0.85)

    for ax in axes:
        ax.set_yscale("log")
        ax.set_xlabel("distance (pc)")
        ax.set_xlim(0, max(r["dist_pc"] for r in rows) * 1.05)
        ax.axvline(20.0, color="k", ls="--", lw=0.7, alpha=0.55)

    axes[0].set_ylabel(r"nominal EIRP$_{5\sigma}$ threshold (W)")
    axes[1].set_ylabel(r"per-channel noise $\sigma_{\rm rms}$ (mJy)")
    axes[0].set_title("(a) narrowband transmitter limit (upper limits)", fontsize=7.5)
    axes[1].set_title("(b) achieved spectral sensitivity", fontsize=7.5)
    axes[0].legend(loc="upper left", ncol=2, fontsize=6.0)

    # d^2 guide, normalised to the median window -- shows the geometric floor
    d = np.array([r["dist_pc"] for r in rows])
    e = np.array([r["eirp"] for r in rows])
    k = np.median(e / d**2)
    dd = np.linspace(max(d.min(), 0.5), d.max(), 50)
    axes[0].plot(dd, k * dd**2, color="k", ls=":", lw=0.8,
                 label=r"median $\propto d^{2}$ locus")
    axes[0].legend(loc="upper left", ncol=2, fontsize=6.0)
    axes[0].text(0.985, 0.03, "downward markers: 5$\\sigma$ upper limits",
                 transform=axes[0].transAxes, ha="right", va="bottom",
                 fontsize=5.8, color="0.35")
    axes[1].text(0.985, 0.03,
                 "round markers: measured noise, not limits",
                 transform=axes[1].transAxes, ha="right", va="bottom",
                 fontsize=5.8, color="0.35")
    return save(fig, outdir, name)


# ======================================================================================
# FIGURE 4 -- eirp_vs_frequency.pdf
# ======================================================================================

def fig_eirp_vs_frequency(rows, st, sizes, outdir):
    name = "eirp_vs_frequency.pdf"
    fig = new_fig(name, sizes)
    ax = fig.add_subplot(111)
    counts = Counter(r["band"] for r in rows)

    for b in bands_present(rows):
        sub = [r for r in rows if r["band"] == b]
        ax.plot([r["fc"] for r in sub], [r["eirp"] for r in sub], ls="none",
                marker=BAND_MARKER.get(b, "o"), ms=3.0, mfc=BAND_COLOUR.get(b, "0.5"),
                mec="none", alpha=0.85, label=band_label(b, counts[b]))

    if st["passed"]:
        ax.plot([r["fc"] for r in st["passed"]], [r["eirp"] for r in st["passed"]],
                ls="none", marker="*", ms=9, mfc="none", mec="k", mew=0.8,
                label=f"flagged windows ({st['n_pass']}; dispositioned, see text)")

    ax.axhline(BENCH_ARECIBO_W, color="#009E73", ls="--", lw=0.8,
               label="Arecibo planetary radar (power comparison only)")
    ax.set_yscale("log")
    ax.set_xlabel("window centre frequency (GHz)")
    ax.set_ylabel(r"nominal EIRP$_{5\sigma}$ threshold (W)")
    ax.set_xlim(min(r["lo"] for r in rows) - 10, max(r["hi"] for r in rows) + 10)
    ax.legend(loc="upper left", ncol=2, fontsize=6.0)
    return save(fig, outdir, name)


# ======================================================================================
# FIGURE 5 -- freq_coverage.pdf
# ======================================================================================

def fig_freq_coverage(rows, st, sizes, outdir):
    name = "freq_coverage.pdf"
    fig = new_fig(name, sizes)
    axes = fig.subplots(1, 2, width_ratios=[3.2, 1.0])
    ax, axb = axes

    lo_all = math.floor(min(r["lo"] for r in rows))
    hi_all = math.ceil(max(r["hi"] for r in rows))
    edges = np.arange(lo_all, hi_all + 1, 1.0)               # 1 GHz bins
    centres = 0.5 * (edges[:-1] + edges[1:])
    bands = bands_present(rows)

    stack = {b: np.zeros(centres.size) for b in bands}
    for r in rows:
        i0 = np.searchsorted(edges, r["lo"], side="right") - 1
        i1 = np.searchsorted(edges, r["hi"], side="left")
        i0 = max(i0, 0)
        i1 = min(max(i1, i0 + 1), centres.size)
        stack.setdefault(r["band"], np.zeros(centres.size))[i0:i1] += 1.0

    bottom = np.zeros(centres.size)
    for b in bands:
        ax.bar(centres, stack[b], bottom=bottom, width=1.0, align="center",
               color=BAND_COLOUR.get(b, "0.5"), edgecolor="none", label=band_label(b))
        bottom += stack[b]

    ax.set_xlim(lo_all - 2, hi_all + 2)
    ax.set_ylim(0, bottom.max() * 1.22)
    ax.set_xlabel("sky frequency (GHz)")
    ax.set_ylabel("windows covering $\\nu$")
    ax.legend(loc="upper left", ncol=3, fontsize=6.0)
    ax.text(0.995, 0.96,
            f"union coverage {st['union_ghz']:.1f} GHz  |  "
            f"summed window bandwidth {st['sum_bw_ghz']:.0f} GHz  |  "
            f"{st['n_windows']} windows, {st['n_stars']} stars",
            transform=ax.transAxes, ha="right", va="top", fontsize=6.2, color="0.25")

    per_band = {b: unique_span_ghz([(r["lo"], r["hi"]) for r in rows if r["band"] == b])
                for b in bands}
    yb = np.arange(len(bands))
    axb.barh(yb, [per_band[b] for b in bands], height=0.68,
             color=[BAND_COLOUR.get(b, "0.5") for b in bands], edgecolor="none")
    for i, b in enumerate(bands):
        axb.text(per_band[b], i, f" {per_band[b]:.1f}", va="center", ha="left", fontsize=6.0)
    axb.set_yticks(yb)
    axb.set_yticklabels([f"B{b}" for b in bands], fontsize=6.5)
    axb.set_xlim(0, max(per_band.values()) * 1.30)
    axb.set_xlabel("unique coverage (GHz)")
    axb.grid(axis="y", visible=False)
    return save(fig, outdir, name)


# ======================================================================================
# FIGURE 6 -- eirp_vs_linewidth.pdf
# ======================================================================================

def pick_representative(rows, cls):
    """Deterministic representative window of a channelisation class."""
    sub = [r for r in rows if r["res_class"] == cls]
    if not sub:
        return None
    key = (lambda r: (r["chanw"], r["eirp"], r["target"])) if cls != "coarse" else \
          (lambda r: (-r["chanw"], r["eirp"], r["target"]))
    return sorted(sub, key=key)[0]


def fig_eirp_vs_linewidth(rows, st, sizes, outdir, notes):
    name = "eirp_vs_linewidth.pdf"
    fig = new_fig(name, sizes)
    ax = fig.add_subplot(111)

    dnu = np.logspace(0, 9, 400)                 # 1 Hz .. 1 GHz

    def curve(r):
        return r["eirp"] * np.maximum(dnu, r["chanw"]) / r["chanw"]

    env = np.array([curve(r) for r in rows])
    ax.fill_between(dnu, env.min(axis=0), env.max(axis=0), color="0.85", lw=0,
                    label=f"envelope of all {len(rows)} window limits")

    chosen = []
    for cls, colour in (("fine", BAND_COLOUR[3]), ("medium", BAND_COLOUR[4]),
                        ("coarse", BAND_COLOUR[6])):
        r = pick_representative(rows, cls)
        if r is None:
            notes.append(f"eirp_vs_linewidth: no '{cls}' window in the data; curve omitted.")
            continue
        chosen.append((cls, r))
        cw = r["chanw"]
        cw_txt = f"{cw/1e6:.3g} MHz" if cw >= 1e6 else f"{cw/1e3:.4g} kHz"
        ax.plot(dnu, curve(r), color=colour, lw=1.4,
                label=f"{cls}: {r['star_name']} B{r['band']}, "
                      r"$\Delta\nu_{\rm ch}=$" + cw_txt)
        ax.plot([cw], [r["eirp"]], marker="o", ms=3.5, color=colour, ls="none")

    if chosen:
        rf = chosen[0][1]
        ideal = rf["eirp"] * np.sqrt(np.maximum(dnu, 1.0) / rf["chanw"])
        ax.plot(dnu, ideal, color="k", ls=":", lw=0.8,
                label=r"idealised re-channelisation of that window ($\propto\sqrt{\Delta\nu'}$)")

    ax.axhline(BENCH_ARECIBO_W, color="#009E73", ls="--", lw=0.8,
               label="Arecibo planetary radar (power comparison only)")
    ax.set_xscale("log")
    ax.set_yscale("log")
    ax.set_xlim(1, 1e9)
    ax.set_xlabel(r"assumed transmitter linewidth $\Delta\nu'$ (Hz)")
    ax.set_ylabel(r"EIRP$_{5\sigma}$ threshold (W)")
    ax.legend(loc="upper left", fontsize=6.0)
    return save(fig, outdir, name)


# ======================================================================================
# FIGURE 7 -- drift_acceleration.pdf
# ======================================================================================

def fig_drift(rows, st, sizes, outdir, notes):
    name = "drift_acceleration.pdf"
    fig = new_fig(name, sizes)
    ax = fig.add_subplot(111)

    fc = np.array([r["fc"] for r in rows])
    dr = np.array([r["drift_max"] for r in rows])

    for b in bands_present(rows):
        m = np.array([r["band"] == b for r in rows])
        ax.plot(fc[m], dr[m], ls="none", marker=BAND_MARKER.get(b, "o"), ms=3.0,
                mfc=BAND_COLOUR.get(b, "0.5"), mec="none", alpha=0.85, label=band_label(b))

    # the ceiling is a fixed |a| : nu_dot = nu * a / c.  Measure a from the data itself.
    a_ceiling = float(np.median(dr / (fc * 1e9))) * C_MS
    notes.append(f"drift ceiling corresponds to a constant acceleration "
                 f"|a| = {a_ceiling:.2f} m/s^2 (median of drift_max/nu x c).")

    nu = np.linspace(fc.min() * 0.9, fc.max() * 1.05, 200)

    # representative physical accelerations, all computed here rather than asserted
    r_t1b = (GM_SUN * 0.0898 * (1.510826 * DAY_S) ** 2 / (4 * math.pi ** 2)) ** (1.0 / 3.0)
    a_t1b = GM_SUN * 0.0898 / r_t1b ** 2
    curves = [
        (5.93e-3, "Earth's orbital acceleration", "#0072B2", "-"),
        (3.39e-2, "Earth's equatorial rotation", "#009E73", "-"),
        (a_t1b, "close-in planet (TRAPPIST-1 b analogue)", "#CC79A7", "-"),
    ]
    for a, lab, colour, ls in curves:
        ax.plot(nu, nu * 1e9 * a / C_MS, color=colour, ls=ls, lw=1.2,
                label=f"$|a|$ = {a:.3g} m s$^{{-2}}$: {lab}")

    ax.plot(nu, nu * 1e9 * a_ceiling / C_MS, color="k", ls="--", lw=1.0,
            label=f"survey drift ceiling ($|a|$ = {a_ceiling:.2f} m s$^{{-2}}$)")

    ax.set_yscale("log")
    ax.set_xlabel("window centre frequency (GHz)")
    ax.set_ylabel(r"maximum searched drift rate $|\dot{\nu}|$ (Hz s$^{-1}$)")
    ax.set_xlim(nu.min(), nu.max())
    ax.set_ylim(1.0, dr.max() * 4)
    ax.legend(loc="lower right", ncol=2, fontsize=5.8)

    # Honest statement of what the ceiling does and does not reach.  Both parts are
    # measured here, not asserted: n_below counts the reference accelerations the
    # ceiling clears at every frequency.
    cleared = [lab for a, lab, _c, _l in curves if a < a_ceiling]
    missed = [(a, lab) for a, lab, _c, _l in curves if a >= a_ceiling]
    msg = (f"the ceiling ($|a|$ = {a_ceiling:.2f} m s$^{{-2}}$) clears "
           f"{len(cleared)} of the {len(curves)} reference accelerations by "
           f"$\\sim$2 orders of magnitude")
    if missed:
        worst = max(missed)[0]
        msg += (f";\nit sits {100*(worst/a_ceiling - 1):.0f}% below the most extreme case "
                f"({max(missed)[1]}),\nso the very fastest close-in-planet drifts are only "
                "marginally outside the search")
    ax.text(0.985, 0.55, msg, transform=ax.transAxes, ha="right", va="top",
            fontsize=6.0, color="0.3",
            bbox=dict(fc="white", ec="0.85", lw=0.4, alpha=0.93, pad=2.0))
    if missed:
        notes.append(f"drift: ceiling {a_ceiling:.2f} m/s^2 does NOT reach "
                     f"{max(missed)[1]} ({max(missed)[0]:.2f} m/s^2) -- stated in the figure.")
    return save(fig, outdir, name)


# ======================================================================================
# FIGURE 8 -- symcdf.pdf
# ======================================================================================

def fig_symcdf(rows, st, sizes, outdir):
    name = "symcdf.pdf"
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

    # rug of the individual on-star peaks, inside the axes
    ax.plot(star, np.full(star.size, 0.012), marker="|", ls="none", ms=3.5, mew=0.5,
            color=BAND_COLOUR[6], alpha=0.55)

    nctrl = st["n_ctrl"]
    ax.axvline(5.0, color="k", ls="--", lw=0.7, alpha=0.6)
    ax.text(5.06, 0.42, r"$5\sigma$", fontsize=6.2, color="0.25")

    med_c, med_s = np.median(ctrl), np.median(star)
    frac_above = np.mean(star > np.quantile(ctrl, 0.95))
    try:
        from scipy.stats import ks_2samp
        ks = ks_2samp(star, ctrl)
        ks_txt = f"two-sample KS: $D$={ks.statistic:.3f}, $p$={ks.pvalue:.2f}\n"
    except Exception:                                    # scipy optional
        ks_txt = ""

    xhi = max(float(np.quantile(ctrl, 0.999)), float(np.quantile(star, 0.99))) * 1.05
    n_star_off = int(np.sum(star > xhi))
    n_ctrl_off = int(np.sum(ctrl > xhi))
    ax.text(0.975, 0.60,
            f"median: star {med_s:.2f} vs control {med_c:.2f}\n"
            f"{ks_txt}"
            f"{100*frac_above:.1f}% of stars exceed the control 95th pct (5% expected)\n"
            f"per-window $p$ floor $1/(1+{nctrl})$ = {1.0/(1+nctrl):.1e}\n"
            f"off scale: {n_star_off} star, {n_ctrl_off} control values",
            transform=ax.transAxes, ha="right", va="top", fontsize=5.6, color="0.25")

    ax.set_xlim(min(ctrl.min(), star.min()) * 0.95, xhi)
    ax.set_ylim(0, 1.02)
    ax.set_xlabel("peak S/N in window")
    ax.set_ylabel("empirical CDF")
    ax.legend(loc="lower right", fontsize=6.0)
    return save(fig, outdir, name)


# ======================================================================================
# FIGURE 9 -- aumic_control_maxima.pdf
# ======================================================================================

def fig_aumic(rows, st, sizes, outdir, notes):
    name = "aumic_control_maxima.pdf"
    fig = new_fig(name, sizes)
    ax = fig.add_subplot(111)

    cm = np.array([r["ctrl_max"] for r in rows], dtype=float)

    au_rows = [r for r in rows if str(r["target"]).startswith("AU_Mic_B6")]
    au = max(au_rows, key=lambda r: r["star_snr"]) if au_rows else None
    if au is None:
        notes.append("aumic_control_maxima: no AU_Mic_B6 row found; marker omitted.")

    xmax = np.quantile(cm, 0.95) * 1.10
    if au is not None:
        xmax = max(xmax, au["star_snr"] * 1.15, au["ctrl_max"] * 1.15)
    inside = cm[cm <= xmax]
    off = cm[cm > xmax]

    bins = np.arange(math.floor(cm.min() * 10) / 10.0, xmax + 0.1, 0.1)
    ax.hist(inside, bins=bins, color=BAND_COLOUR[8], edgecolor="white", lw=0.25,
            label=f"per-window control maxima ({cm.size} windows)")

    ax.axvline(5.0, color="k", ls="--", lw=0.9, label=r"formal $5\sigma$ threshold")
    if au is not None:
        n_ex = int(au["n_ge_star"])
        n_ct = int(au["n_ctrl_eff"])
        pct = 100.0 * np.mean(cm >= au["star_snr"])
        ax.axvline(au["star_snr"], color=BAND_COLOUR[6], lw=1.4,
                   label=f"AU Mic on-star peak ({au['star_snr']:.2f})")
        ax.axvline(au["ctrl_max"], color=BAND_COLOUR[6], lw=1.2, ls=":",
                   label=f"AU Mic own control max ({au['ctrl_max']:.2f})")
        ax.text(0.985, 0.70,
                f"AU Mic's on-star peak is exceeded by\n"
                f"{n_ex}/{n_ct} of its own control positions,\n"
                f"and by the control maximum of {pct:.0f}% of all windows",
                transform=ax.transAxes, ha="right", va="top", fontsize=6.0,
                color=BAND_COLOUR[6])
        notes.append(f"AU Mic window: star S/N {au['star_snr']:.2f}, own control max "
                     f"{au['ctrl_max']:.2f}, {n_ex}/{n_ct} controls exceed it.")

    if off.size:
        ax.text(0.985, 0.985,
                f"{off.size} windows off scale (control max up to {off.max():.1f}): " +
                ", ".join(f"{v:.1f}" for v in np.sort(off)[::-1][:6]) +
                ("" if off.size <= 6 else ", ..."),
                transform=ax.transAxes, ha="right", va="top", fontsize=5.8, color="0.35")

    ax.set_xlim(bins[0], xmax)
    ax.set_ylim(0, ax.get_ylim()[1] * 1.30)
    ax.set_xlabel("control-ring peak S/N")
    ax.set_ylabel("windows")
    ax.legend(loc="upper left", fontsize=6.0)
    return save(fig, outdir, name)


# ======================================================================================
# FIGURE 10 -- selection.pdf
# ======================================================================================

def selection_stages(rows, census, meta, st):
    """The funnel.  Every number is derived; returns [(label, value, unit_kind)]."""
    n_cov = len(meta["census_d"]) if meta["census_d"] else st["n_census"]
    return [
        ("40 pc candidate census", st["n_census"], "star"),
        ("with usable public ALMA coverage", st["n_census"], "star"),
        ("stars processed in this release", st["n_stars"], "star"),
        ("star--band datasets processed", st["n_targets"], "dataset"),
        ("spectral windows searched", st["n_windows"], "win"),
        (r"windows with a $>5\sigma$ on-star peak", st["n_hits"], "win"),
        ("passing the symmetric star-vs-control test", st["n_pass"], "win"),
        ("surviving spectral-line vetting", st["n_vetted"], "win"),
    ]


def fig_selection(rows, census, meta, st, sizes, outdir):
    name = "selection.pdf"
    fig = new_fig(name, sizes)
    ax = fig.add_subplot(111)

    stages = selection_stages(rows, census, meta, st)
    labels = [s[0] for s in stages]
    vals = np.array([s[1] for s in stages], dtype=float)
    kinds = [s[2] for s in stages]
    cols = {"star": BAND_COLOUR[3], "dataset": BAND_COLOUR[3], "win": BAND_COLOUR[6]}

    y = np.arange(len(stages))[::-1]
    ax.barh(y, vals, height=0.62, color=[cols[k] for k in kinds], edgecolor="none")

    # Count, then a retention percentage -- but ONLY where the previous stage counts the
    # same kind of object (stars vs windows), otherwise the ratio is meaningless.
    vmax = vals.max()
    prev_v = prev_k = None
    for yy, v, k, in zip(y, vals, kinds):
        txt = f"{int(v)}"
        if prev_v is not None and prev_k == k and prev_v > 0 and v <= prev_v:
            txt += f"   ({100.0 * v / prev_v:.0f}% of previous stage)"
        ax.text(v + vmax * 0.012, yy, txt, va="center", ha="left", fontsize=7.0)
        prev_v, prev_k = v, k

    ax.set_yticks(y)
    ax.set_yticklabels(labels, fontsize=7.2)
    ax.set_xlim(0, vmax * 1.10)
    ax.set_xlabel("count")
    ax.grid(axis="y", visible=False)
    ax.legend(handles=[Patch(color=cols["star"], label="stars / datasets"),
                       Patch(color=cols["win"], label="spectral windows")],
              loc="center right", fontsize=6.5)
    ax.text(0.995, 0.985,
            f"snapshot: {st['n_windows']} windows / {st['n_stars']} stars.  The census is\n"
            "itself the ALMA-crossmatched candidate list, so every census\n"
            "star has usable coverage by construction.",
            transform=ax.transAxes, ha="right", va="top", fontsize=5.8, color="0.4")
    return save(fig, outdir, name)


# ======================================================================================
# FIGURE 11 -- eirp_context.pdf
# ======================================================================================

def fig_eirp_context(rows, st, sizes, outdir):
    name = "eirp_context.pdf"
    fig = new_fig(name, sizes)
    axes = fig.subplots(1, 2)

    e_all = np.array([r["eirp"] for r in rows], dtype=float)
    best = {}
    for r in rows:
        s = r["star_name"]
        if s not in best or r["eirp"] < best[s]:
            best[s] = r["eirp"]
    e_star = np.array(list(best.values()), dtype=float)
    med = float(np.median(e_all))

    lo = min(e_all.min(), BENCH_ARECIBO_W) * 0.5
    hi = max(e_all.max(), BENCH_KARDASHEV_I_W) * 2.0
    bins = np.logspace(np.log10(lo), np.log10(hi), 46)

    panels = [
        (axes[0], e_all, BAND_COLOUR[6],
         f"all searched windows (n={e_all.size})", "(a) per-window thresholds"),
        (axes[1], e_star, BAND_COLOUR[3],
         f"deepest window per star (n={e_star.size})", "(b) best threshold per star"),
    ]
    for ax, vals, colour, lab, title in panels:
        ax.hist(vals, bins=bins, color=colour, edgecolor="white", lw=0.25, label=lab)
        ax.set_xscale("log")
        ax.set_xlim(lo, hi)
        ax.set_xlabel(r"nominal EIRP$_{5\sigma}$ threshold (W)")
        ax.set_title(title, fontsize=7.5)
        ax.axvline(BENCH_ARECIBO_W, color="#009E73", ls="--", lw=1.0)
        ax.axvline(BENCH_KARDASHEV_I_W, color="#CC79A7", ls="-.", lw=1.0)
        ax.axvline(med, color="k", ls=":", lw=1.0)
        top = ax.get_ylim()[1]
        ax.set_ylim(0, top * 1.75)
        # single-line rotated labels on a white ground: multi-line rotated text
        # collides with itself at these font sizes
        for xv, txt, col in (
            (BENCH_ARECIBO_W, "Arecibo planetary radar $2{\\times}10^{13}$ W", "#009E73"),
            (med, f"survey median {sci(med)} W", "k"),
            (BENCH_KARDASHEV_I_W, "Kardashev type-I reference $10^{17}$ W", "#CC79A7"),
        ):
            ax.text(xv, top * 1.68, " " + txt, rotation=90, va="top", ha="left",
                    fontsize=5.6, color=col,
                    bbox=dict(fc="white", ec="none", alpha=0.85, pad=0.8))
        ax.set_ylabel("number")
        ax.legend(loc="upper left", fontsize=6.2)

    fig.supxlabel("reference powers are shown for scale only; they are not survey limits "
                  "and are not sensitivity claims",
                  fontsize=5.8, color="0.4")
    return save(fig, outdir, name)


# ======================================================================================
# FIGURE 12 -- completeness.pdf  (sensitivity completeness, NOT injection recovery)
# ======================================================================================

def fig_completeness(rows, st, sizes, outdir, notes):
    name = "completeness.pdf"
    fig = new_fig(name, sizes)
    # reserve a strip at the bottom for the "this is not injection recovery" disclaimer
    fig.get_layout_engine().set(rect=(0.0, 0.075, 1.0, 0.925))
    axes = fig.subplots(2, 1)

    notes.append("completeness.pdf: NO injection-recovery data exists in this export; "
                 "the figure shows achieved-sensitivity completeness instead.")

    groups = [
        ("all windows", rows, "k", "-"),
        ("fine channels (<1 MHz)", [r for r in rows if r["res_class"] == "fine"],
         BAND_COLOUR[3], "-"),
        ("medium channels (1--5 MHz)", [r for r in rows if r["res_class"] == "medium"],
         BAND_COLOUR[4], "-"),
        ("coarse channels ($\\geq$5 MHz)", [r for r in rows if r["res_class"] == "coarse"],
         BAND_COLOUR[6], "-"),
    ]

    ax = axes[0]
    for lab, sub, colour, ls in groups:
        if not sub:
            continue
        x, f = ecdf([r["eirp"] for r in sub])
        x = np.concatenate([[x[0]], x])
        f = np.concatenate([[0.0], f])
        ax.step(x, f, where="post", color=colour, ls=ls,
                lw=1.5 if lab == "all windows" else 1.1,
                label=f"{lab} (n={len(sub)})")
    ax.set_xscale("log")
    ax.set_ylim(0, 1.02)
    ax.set_ylabel("fraction of windows reaching EIRP")
    ax.set_xlabel(r"EIRP$_{5\sigma}$ threshold (W)")
    ax.legend(loc="upper left", fontsize=6.2)
    ax.set_title("(a) per-window achieved sensitivity", fontsize=7.5)

    # per-star: the best (lowest) threshold each star attains, by channelisation class
    ax = axes[1]
    for lab, sub, colour, ls in groups:
        if not sub:
            continue
        best = {}
        for r in sub:
            s = r["star_name"]
            if s not in best or r["eirp"] < best[s]:
                best[s] = r["eirp"]
        x, f = ecdf(list(best.values()))
        x = np.concatenate([[x[0]], x])
        f = np.concatenate([[0.0], f])
        ax.step(x, f * len(best) / st["n_stars"], where="post", color=colour, ls=ls,
                lw=1.5 if lab == "all windows" else 1.1,
                label=f"{'any channelisation' if lab == 'all windows' else lab}"
                      f" ({len(best)} stars)")
    ax.set_xscale("log")
    ax.set_ylim(0, 1.02)
    ax.set_ylabel(f"fraction of the {st['n_stars']} searched stars")
    ax.set_xlabel(r"best EIRP$_{5\sigma}$ threshold attained per star (W)")
    ax.legend(loc="upper left", fontsize=6.2)
    ax.set_title("(b) per-star achieved sensitivity", fontsize=7.5)

    fig.text(0.5, 0.012,
             "Achieved-sensitivity completeness: the fraction of the searched sample for which a "
             "transmitter of a given EIRP\nwould exceed the $5\\sigma$ threshold. This is NOT an "
             "injection--recovery completeness; no injection data exist in this release.",
             ha="center", va="bottom", fontsize=6.2, color="0.25")
    return save(fig, outdir, name)


# ======================================================================================
# FIGURE 13 -- bpic_velocity_space.pdf
# ======================================================================================

def fig_velocity_space(rows, st, sizes, outdir, notes):
    name = "bpic_velocity_space.pdf"
    fig = new_fig(name, sizes)
    ax = fig.add_subplot(111)

    with_line = [r for r in rows if r["v_off"] is not None]
    if not with_line:
        notes.append("bpic_velocity_space: no rows carry a line identification.")
    v_all = np.array([r["v_off"] for r in with_line], dtype=float)

    hits = [r for r in st["hits"] if r["v_off"] is not None]
    pas = [r for r in st["passed"] if r["v_off"] is not None]
    pset = {id(r) for r in pas}

    vmask = 50.0                       # circumstellar velocity tolerance, km/s

    # symlog x: linear inside +/-100 km/s (where the astrophysical lines sit), log
    # outside, so a single far-offset window stays on scale without squashing the core.
    linthresh = 100.0
    ax.set_xscale("symlog", linthresh=linthresh, linscale=1.4)
    lim = max(500.0, 1.6 * max((abs(r["v_off"]) for r in hits), default=0.0))
    ax.set_xlim(-lim, lim)
    ticks = [t for t in (-1000, -300, -100, -50, 0, 50, 100, 300, 1000) if abs(t) <= lim]
    ax.set_xticks(ticks)
    ax.set_xticklabels([str(t) for t in ticks])

    ax.axvspan(-vmask, vmask, color=BAND_COLOUR[8], alpha=0.20, lw=0,
               label=f"circumstellar tolerance ($\\pm${vmask:.0f} km s$^{{-1}}$)")
    for s in (-vmask, vmask):
        ax.axvline(s, color=BAND_COLOUR[8], ls="--", lw=0.7)
    ax.axvline(0.0, color="k", lw=0.8)

    ax.plot(np.clip(v_all, -lim, lim), np.full(v_all.size, 0.07),
            ls="none", marker="|", ms=5, mew=0.5, color="0.6",
            label=f"all line-identified windows (n={v_all.size})")

    hv = np.array([r["v_off"] for r in hits if id(r) not in pset])
    if hv.size:
        ax.plot(np.clip(hv, -lim, lim), np.full(hv.size, 0.30), ls="none", marker="v",
                ms=5, mfc="none", mec=GREY, mew=0.9,
                label=f"$>5\\sigma$ on-star, control-rejected (n={hv.size})")

    ys = np.linspace(0.52, 0.86, max(len(pas), 1))
    for r, yy in zip(sorted(pas, key=lambda r: r["v_off"]), ys):
        xv = float(np.clip(r["v_off"], -lim, lim))
        ax.plot([xv], [yy], ls="none", marker="v", ms=7,
                mfc=BAND_COLOUR[6], mec="k", mew=0.6)
        right = xv < 0.35 * lim
        ax.annotate(f"{r['star_name']} B{r['band']}: {r['v_off']:+.1f} km s$^{{-1}}$"
                    f" from {r['line']}",
                    xy=(xv, yy), xytext=(9 if right else -9, 0),
                    textcoords="offset points", fontsize=5.9, va="center",
                    ha="left" if right else "right", color=BAND_COLOUR[6])

    ax.plot([], [], ls="none", marker="v", ms=6, mfc=BAND_COLOUR[6], mec="k", mew=0.6,
            label=f"flagged candidate windows (n={len(pas)})")

    ax.set_ylim(0, 1.0)
    ax.set_yticks([])
    ax.grid(axis="y", visible=False)
    ax.set_xlabel(r"stellar-frame velocity offset from the nearest catalogued line "
                  r"(km s$^{-1}$; symlog outside $\pm$100)")
    ax.legend(loc="upper left", fontsize=6.0)
    ax.text(0.995, 0.955,
            "$v = c\\,\\Delta\\nu/\\nu_{\\rm c}$ from the tabulated line offset",
            transform=ax.transAxes, ha="right", va="top", fontsize=5.8, color="0.4")

    n_in = int(np.sum(np.abs(np.array([r["v_off"] for r in pas])) < vmask)) if pas else 0
    notes.append(f"velocity space: {n_in}/{len(pas)} plotted flagged windows lie within "
                 f"+/-{vmask:.0f} km/s of a catalogued line (i.e. astrophysical).")
    n_noline = st["n_pass"] - len(pas)
    if n_noline:
        notes.append(f"velocity space: {n_noline} of the {st['n_pass']} flagged windows carry "
                     "no line identification and cannot be placed in velocity space; "
                     "they are absent from this figure by construction.")
    return save(fig, outdir, name)


# --------------------------------------------------------------------------------------
# driver
# --------------------------------------------------------------------------------------

def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--data", default=DEFAULT_DATA)
    ap.add_argument("--outdir", default=DEFAULT_OUTDIR)
    ap.add_argument("--sizes", default=DEFAULT_SIZES)
    args = ap.parse_args(argv)

    set_style()
    os.makedirs(args.outdir, exist_ok=True)

    rows, census, meta, warnings = load_data(args.data)
    st = survey_stats(rows, census, meta)
    sizes = target_sizes(args.sizes)
    notes = []

    print("=" * 78)
    print(f"ASTRA / 40 pc ALMA technosignature survey -- figure regeneration")
    print(f"  data      : {args.data}")
    print(f"  snapshot  : {meta['snapshot']}")
    print(f"  outdir    : {args.outdir}")
    print("=" * 78)

    print("\nSELECTION FUNNEL (figure 10, all values derived from the export)")
    print("-" * 78)
    stages = selection_stages(rows, census, meta, st)
    prev_v = prev_k = None
    for lab, val, kind in stages:
        clean = lab.replace("$>5\\sigma$", ">5 sigma").replace("--", "-")
        frac = ""
        if prev_v and prev_k == kind:
            frac = f"{100.0 * val / prev_v:6.1f}% of previous"
        elif prev_v:
            frac = "(different unit; ratio not meaningful)"
        print(f"  {clean:<48s} {val:6d}   {frac}")
        prev_v, prev_k = val, kind
    print("-" * 78)
    print(f"  union sky coverage        : {st['union_ghz']:.2f} GHz")
    print(f"  summed window bandwidth   : {st['sum_bw_ghz']:.1f} GHz")
    print(f"  EIRP_5sigma  min / median / max : "
          f"{st['eirp_min']:.3e} / {st['eirp_median']:.3e} / {st['eirp_max']:.3e} W")
    print(f"  windows flagged 'likely astrophysical' in the export : {st['n_likely']}")

    figs = []
    figs.append(fig_sample_distance(rows, census, meta, st, sizes, args.outdir))
    figs.append(fig_star_coverage(rows, st, sizes, args.outdir, warnings))
    figs.append(fig_eirp_continuum(rows, st, sizes, args.outdir))
    figs.append(fig_eirp_vs_frequency(rows, st, sizes, args.outdir))
    figs.append(fig_freq_coverage(rows, st, sizes, args.outdir))
    figs.append(fig_eirp_vs_linewidth(rows, st, sizes, args.outdir, notes))
    figs.append(fig_drift(rows, st, sizes, args.outdir, notes))
    figs.append(fig_symcdf(rows, st, sizes, args.outdir))
    figs.append(fig_aumic(rows, st, sizes, args.outdir, notes))
    figs.append(fig_selection(rows, census, meta, st, sizes, args.outdir))
    figs.append(fig_eirp_context(rows, st, sizes, args.outdir))
    figs.append(fig_completeness(rows, st, sizes, args.outdir, notes))
    figs.append(fig_velocity_space(rows, st, sizes, args.outdir, notes))

    print("\nFIGURES")
    print("-" * 78)
    print(f"  {'file':<36s} {'aspect':>7s} {'target':>7s} {'dev':>7s} {'kB':>7s}")
    for path in figs:
        base = os.path.basename(path)
        try:
            import pymupdf
            doc = pymupdf.open(path)
            rect = doc[0].rect
            got = rect.width / rect.height
            doc.close()
        except Exception:
            got = float("nan")
        tgt = sizes.get(base, (0, 0, float("nan")))[2]
        dev = 100.0 * (got - tgt) / tgt if tgt == tgt and tgt else float("nan")
        kb = os.path.getsize(path) / 1024.0
        print(f"  {base:<36s} {got:7.3f} {tgt:7.3f} {dev:6.2f}% {kb:7.1f}")

    if warnings:
        print("\nDATA WARNINGS")
        print("-" * 78)
        for w in warnings:
            print(f"  ! {w}")
    if notes:
        print("\nNOTES")
        print("-" * 78)
        for n in notes:
            print(f"  - {n}")
    print()
    return 0


if __name__ == "__main__":
    sys.exit(main())
