#!/usr/bin/env python3
"""Generators for the two figures that shipped without one.

Referee 3 (cycle 2, minor 5) pointed out that `cp72_control_distribution.pdf`
(Fig. 5) and `sensitivity_2d.pdf` (Fig. 7) are in the upload set with no script
in the release folder that rebuilds them, which is the condition that retired
`pipeline_schematic.pdf` in v3.42.  Both are reconstructible from products
shipped here:

  Fig. 5  <- localnull_code/ctrlmax.json   (the window's 512 control statistics)
            per_target_results_v3.50.csv   (T_star and the ring maximum)
  Fig. 7  <- per_target_results_v3.50.csv  (window centre, nominal EIRP, class)

Canvas sizes and the plotting style match the shipped PDFs (302.4 x 216.0 pt
and 504.0 x 244.8 pt) so the manuscript's `\\includegraphics` widths are
unchanged.  Usage: python3 make_fig_missing_v344.py [outdir]
"""
import csv, json, math, os, sys

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = sys.argv[1] if len(sys.argv) > 1 else os.path.join(HERE, "figures")
GREY = "0.55"

plt.rcParams.update({
    "font.family": "serif",
    "font.serif": ["STIXGeneral", "DejaVu Serif", "Times New Roman"],
    "mathtext.fontset": "stix",
    "font.size": 8, "axes.labelsize": 8,
    "xtick.labelsize": 7, "ytick.labelsize": 7,
    "legend.fontsize": 6.5, "legend.frameon": True, "legend.framealpha": 0.9,
    "legend.edgecolor": "0.7",
    "axes.grid": True, "grid.color": "0.85", "grid.linewidth": 0.4,
    "axes.axisbelow": True, "axes.linewidth": 0.6,
    "xtick.major.width": 0.6, "ytick.major.width": 0.6,
    "lines.linewidth": 1.1, "figure.dpi": 200,
    "pdf.fonttype": 42, "ps.fonttype": 42,      # never Type 3
})

ROWS = list(csv.DictReader(open(os.path.join(HERE, "per_target_results_v3.50.csv"))))
f = lambda r, k: float(r[k])


def fig_cp72_controls():
    """Both epochs, at referee 3's request (N8): the same window an hour later.

    The second epoch's 512 control statistics come from its own retained
    `*_search.npz` `ctrl_max` array, copied into
    `localnull_code/ctrlmax_eb2.json` with its provenance recorded inside the
    file.  Canvas size is unchanged, so the figure still costs what it cost.
    """
    ctrl = json.load(open(os.path.join(HERE, "localnull_code/ctrlmax.json")))
    v = np.asarray(ctrl["CP-72_2713_B7"], dtype=float)
    eb2 = json.load(open(os.path.join(HERE, "localnull_code/ctrlmax_eb2.json")))
    v2 = np.asarray(eb2["CP-72_2713_EB2_B7"], dtype=float)
    row = [r for r in ROWS if r["star_name"].startswith("CP-72")
           and r["stage1_flag"] == "True"][0]
    tstar, ringmax = f(row, "star_snr"), f(row, "ctrl_max_snr")
    assert abs(ringmax - v.max()) < 1e-3, (ringmax, v.max())
    rec = json.load(open(os.path.join(HERE, "cp72_recurrence.json")))
    t2 = rec["e2_drift_max_at_ch35"]["T"]
    assert len(v2) == len(v), (len(v2), len(v))
    assert abs(v2.max() - rec["windowmax"]["e2"]["ctrl_max"]) < 1e-3

    fig = plt.figure(figsize=(302.4 / 72.0, 216.0 / 72.0), layout="constrained")
    fig.get_layout_engine().set(w_pad=0.012, h_pad=0.012)
    ax = fig.add_subplot(111)
    ax.grid(False)
    bins = np.linspace(min(v.min(), v2.min()), max(v.max(), v2.max()), 33)
    ax.hist(v, bins=bins, color="0.75", edgecolor="0.35", linewidth=0.4,
            label="epoch 1 controls")
    ax.hist(v2, bins=bins, histtype="step", color="#1f77b4", linewidth=0.9,
            label="epoch 2 controls")
    ax.axvline(ringmax, color="0.25", ls="--", lw=1.0,
               label="largest control, epoch 1 = %.2f" % ringmax)
    ax.axvline(v2.max(), color="#1f77b4", ls="--", lw=1.0,
               label="largest control, epoch 2 = %.2f" % v2.max())
    ax.axvline(tstar, color="k", ls="-", lw=1.4,
               label=r"$T_\star$ epoch 1 = %.2f" % tstar)
    ax.axvline(t2, color="k", ls=":", lw=1.4,
               label=r"$T_\star$ epoch 2 = %.2f" % t2)
    ax.set_xlabel("single-position control statistic", fontsize=10)
    ax.set_ylabel("number of control positions", fontsize=10)
    ax.tick_params(labelsize=9)
    ax.legend(loc="upper right", fontsize=6.0, borderpad=0.3,
              handlelength=1.6, labelspacing=0.25)
    path = os.path.join(OUT, "cp72_control_distribution.pdf")
    fig.savefig(path, format="pdf")
    plt.close(fig)
    return path, len(v)


def fig_sensitivity_2d():
    fig = plt.figure(figsize=(504.0 / 72.0, 244.8 / 72.0), layout="constrained")
    fig.get_layout_engine().set(w_pad=0.012, h_pad=0.012)
    ax = fig.add_subplot(111)
    ax.grid(False)
    # Class A open circles in C0, Class B small filled grey points, matching
    # the colours of the figure this generator replaces.
    for cls, lab, kw in (
            ("B", "Class B: amplitude-only (drift undiscriminated)",
             dict(s=7, marker="o", facecolor=GREY, edgecolor="none", zorder=2)),
            ("A", "Class A: drift-search (drifting-class recovery measured)",
             dict(s=18, marker="o", facecolor="none",
                  edgecolor="#1f77b4", linewidth=0.8, zorder=3))):
        sel = [r for r in ROWS if r["search_class"] == cls]
        x = [0.5 * (f(r, "flo_GHz") + f(r, "fhi_GHz")) for r in sel]
        y = [f(r, "eirp_nominal_W") for r in sel]
        ax.scatter(x, y, label=lab, **kw)
    # the grey lines the caption names: the median searched window centre in
    # each of the three bands that carry the survey, computed from the
    # catalogue rather than drawn by hand
    for band in ("3", "6", "7"):
        c = sorted(0.5 * (f(r, "flo_GHz") + f(r, "fhi_GHz"))
                   for r in ROWS if r["band"] == band)
        ax.axvline(c[len(c) // 2], color="0.85", lw=0.6, zorder=0)
    ax.axhline(2e13, color="tab:red", ls=":", lw=0.9, zorder=1)
    ax.annotate("Arecibo-like planetary radar", xy=(0.015, 2e13),
                xycoords=("axes fraction", "data"), xytext=(0, 3),
                textcoords="offset points", fontsize=8.5, va="bottom",
                color="tab:red")
    ax.set_yscale("log")
    ax.set_xlabel("window centre frequency (GHz)", fontsize=10)
    ax.set_ylabel(r"nominal EIRP$_{5\sigma}$ threshold (W)", fontsize=10)
    ax.tick_params(labelsize=9)
    h, l = ax.get_legend_handles_labels()
    ax.legend(h[::-1], l[::-1], loc="upper left", fontsize=8.5,
              borderpad=0.4, frameon=False)
    path = os.path.join(OUT, "sensitivity_2d.pdf")
    fig.savefig(path, format="pdf")
    plt.close(fig)
    return path, len(ROWS)


if __name__ == "__main__":
    for p, n in (fig_cp72_controls(), fig_sensitivity_2d()):
        print("%-46s %d points" % (p, n))
