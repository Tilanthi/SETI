#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
make_referee2_artefacts.py -- the three tables (and one figure) added or
rebuilt for the SECOND referee round of the 0-40 pc ALMA technosignature
paper.

USAGE
-----
    python3 make_referee2_artefacts.py [--data PATH] [--tabdir tables]
                                       [--figdir figures] [--no-figure]

WHAT IT WRITES
--------------
    tables/tab_bothstats.tex     NEW   label tab:bothstats
    tables/tab_allhits.tex       NEW   label tab:allhits
    tables/tab_flagged_v331.tex  REPLACEMENT for the in-manuscript tab:flagged
    tables/referee2_numbers.json every number the three tables assert
    figures/eirp_context.pdf     REBUILT with native channel width exposed
                                 (delegated to make_figures_referee_v331.py;
                                  the previous file is backed up first)

WHY EACH TABLE EXISTS
---------------------
tab:bothstats -- Section "Changing the detection statistic, and the AU Mic
    crossing" already says "Table~\\ref{tab:bothstats} lists every window the
    original statistic flagged, under both statistics".  In v3.30 that
    reference is UNDEFINED: the table was promised in prose and never built.
    Referee 2 asks whether revising the statistic was an AU-Mic-specific
    intervention.  The table answers it by auditing all seven originally
    flagged windows side by side.  The visible fact is that the three windows
    that dropped out are exactly the three in which the region maximum was NOT
    at the stellar position (5.97 -> 5.22, 5.83 -> 5.09, 5.80 -> 5.22), while
    CP-72 2713 is numerically unchanged (5.81 -> 5.81) because there the region
    maximum already sat on the star.

tab:allhits -- the funnel is quoted only at its endpoint (4 spatially
    significant windows).  This lists all 18 windows with an on-star crossing,
    so a reader can see the 18 -> 4 narrowing rather than its result.

tab:flagged (v3.31) -- identical in structure, caption intent and columns to
    the existing four-row table, plus one new column: the frequency offset
    from the nearest masked transition in MHz.  The manuscript currently
    spells the km/s <-> MHz conversion out in prose for beta Pic only.

PROVENANCE
----------
Every survey quantity is recomputed here from the frozen export by exec'ing
the prologue of survey_stats.py, so the selection rules (band reconstruction,
de-duplication, the physical noise-defect cut, the withheld eps Eri Band 6
windows) cannot drift from the paper's.  Nothing about the survey is typed in.
The only hand-entered content is editorial: display spellings of star names,
the four disposition strings carried over verbatim from the existing
tab:flagged, and the literature channel widths in the figure module (each
carrying its source sentence).

Author: ASTRA PA, for G. J. White.  Re-runnable; no state outside --data.
"""

from __future__ import annotations

import argparse
import collections          # noqa: F401  (used by the exec'd prologue)
import itertools            # noqa: F401  (ditto)
import json
import math                 # noqa: F401  (ditto)
import os
import re
import shutil
import statistics as st     # noqa: F401  (ditto)

HERE = os.path.dirname(os.path.abspath(__file__))
DEFAULT_DATA = "/workspace/SETI/figwork/v333_data.json"


# ======================================================================================
# survey selection -- exec the prologue of survey_stats.py verbatim
# ======================================================================================

def survey_rows(data_path):
    """Return the list `good` exactly as survey_stats.py builds it, plus sysn()."""
    src = open(os.path.join(HERE, "survey_stats.py")).read()
    head = src.split("S=collections.OrderedDict()")[0]
    head = head.replace("SRC='/workspace/SETI/figwork/v333_data.json'",
                        "SRC=%r" % data_path)
    ns = {"__name__": "survey_stats_prologue"}
    exec(compile(head, "survey_stats.py[prologue]", "exec"), ns)
    return ns["good"], ns["sysn"]


# ======================================================================================
# LaTeX helpers
# ======================================================================================

def tex_escape(s):
    """As make_tables_v328.py: escape the fragile characters, then collapse the
    runs of multiple spaces that occur in SIMBAD identifiers (TeX collapses
    them anyway; doing it explicitly keeps the source readable)."""
    out = []
    for ch in str(s):
        if ch in "%&#$":
            out.append("\\" + ch)
        elif ch == "_":
            out.append("\\_")
        elif ch == "~":
            out.append("\\textasciitilde{}")
        elif ch == "^":
            out.append("\\textasciicircum{}")
        else:
            out.append(ch)
    return re.sub(r"\s+", " ", "".join(out)).strip()


# Display spellings.  EDITORIAL ONLY -- these are the forms the manuscript
# already uses in prose and in tab:flagged.  Anything not listed falls back to
# tex_escape() of the released identifier, so a new star cannot vanish.
DISPLAY = {
    "bet Pic":                   r"$\beta$~Pic",
    "HD 48370":                  r"HD~48370",
    "CP-72 2713":                r"CP$-$72~2713",
    "HD14055":                   r"HD~14055",
    "AU Mic":                    r"AU~Mic",
    "ALMA J153702653-33192492":  r"ALMA~J1537$-$3319",
    "HD 285968":                 r"HD~285968",
    "HD 10647":                  r"HD~10647",
    "HD170773":                  r"HD~170773",
    "CD-57 1054":                r"CD$-$57~1054",
    "LHS 1140":                  r"LHS~1140",
    "NAME Barnards star":        r"Barnard's star",
}

# identifiers whose display form is abbreviated and therefore needs expanding
# in the caption so the released machine-readable table can still be joined
LONGFORM = {"ALMA J153702653-33192492": r"ALMA~J1537$-$3319"}


def star_tex(name):
    return DISPLAY.get(name, tex_escape(name))


_LINE_RE = re.compile(r"^(?P<iso>\d*)(?P<sp>[A-Za-z][A-Za-z0-9]*?)"
                      r"(?:\((?P<u>\d+)-(?P<l>\d+)\))?$")


def line_tex(line):
    """'CO(2-1)' -> 'CO\\,$2{\\to}1$';  'H2CO' -> 'H$_2$CO';
       '13CO(2-1)' -> '$^{13}$CO\\,$2{\\to}1$'.  Unrecognised -> escaped."""
    if line is None:
        return "---"
    m = _LINE_RE.match(str(line).strip())
    if not m:
        return tex_escape(line)
    iso, sp, u, l = m.group("iso"), m.group("sp"), m.group("u"), m.group("l")
    # subscript the digits inside a species name (H2CO -> H_2CO)
    sp_t = re.sub(r"(\d+)", lambda mm: "$_{%s}$" % mm.group(1), sp)
    head = (r"$^{%s}$" % iso if iso else "") + sp_t
    if u is None:
        return head
    return r"%s\,$%s{\to}%s$" % (head, u, l)


def fnum(x, nd):
    """Fixed-point with a TeX minus sign."""
    s = "%.*f" % (nd, x)
    return s.replace("-", "$-$")


def dv_tex(v):
    """Velocity offset: one decimal below 100 km/s, integer above."""
    if v is None:
        return "---"
    return fnum(v, 1) if abs(v) < 100 else fnum(v, 0)


def doff_tex(x):
    """Frequency offset in MHz: two decimals below 100 MHz, one above."""
    if x is None:
        return "---"
    return fnum(x, 2) if abs(x) < 100 else fnum(x, 1)


_WORDS = ["zero", "one", "two", "three", "four", "five", "six", "seven",
          "eight", "nine", "ten"]


def word(n):
    """House style: spell out counts up to ten in captions, digits above."""
    return _WORDS[n] if 0 <= n <= 10 else str(n)


HEADER = ("%% Generated by make_referee2_artefacts.py -- do not edit by hand.\n"
          "%% Every survey number below is recomputed from the frozen export\n"
          "%% through the prologue of survey_stats.py.\n")


# ======================================================================================
# TABLE 1 -- tab:bothstats
# ======================================================================================

def tab_bothstats(good, tabdir, rep):
    seven = sorted([r for r in good if r["cross"] and r["sbr_old"]],
                   key=lambda r: -r["src_snr"])
    n_ctrl = int(st.median(r["n_ctrl"] for r in good))
    n_src = int(st.median(r["n_src"] for r in good))
    n_sym = sum(1 for r in seven if r["sbr"])

    rows = []
    for r in seven:
        rows.append(dict(
            star=r["star_name"], star_tex=star_tex(r["star_name"]),
            band=r["band_x"], f_GHz=round(0.5 * (r["flo"] + r["fhi"]), 4),
            src_snr=round(r["src_snr"], 2), ctrl_max=round(r["ctrl_max"], 2),
            star_snr=round(r["star_snr"], 2),
            ring_max=round(r["ctrl_max_all"], 2),
            flagged_sym=bool(r["sbr"]),
            region_max_on_star=bool(abs(r["src_snr"] - r["star_snr"]) < 5e-3),
        ))
    dropped = [x for x in rows if not x["flagged_sym"]]
    onstar = [x for x in rows if x["region_max_on_star"]]
    rep["tab_bothstats"] = dict(
        n_rows=len(rows), n_windows=len(good), n_ctrl=n_ctrl, n_src=n_src,
        n_flagged_old=len(seven), n_flagged_sym=n_sym,
        symmetric_is_subset=all(r["sbr_old"] for r in good
                                if r["cross"] and r["sbr"]),
        dropped=[x["star"] for x in dropped],
        region_max_on_star=[x["star"] for x in onstar],
        rows=rows)

    def _lst(vals, fmt="%.2f"):
        vals = [fmt % v for v in vals]
        return ", ".join(vals[:-1]) + " and " + vals[-1]

    L = [HEADER, r"\begin{table}", r"\centering", r"\small",
         r"\setlength{\tabcolsep}{4pt}",
         (r"\caption{Every window flagged by the original region-max "
          r"statistic, shown under both statistics, so the effect of the "
          r"revision can be audited across all of them rather than taken on "
          r"trust for one target. $S_{\rm reg}$ is the maximum of "
          r"Eq.~\ref{eq:tstar} over the $n_{\rm src}=%d$-position source "
          r"region, `ctrl max' the largest of the \NCtrl{} single-position "
          r"controls it was compared with; $T_\star$ is the symmetric "
          r"single-position statistic at the propagated stellar position and "
          r"`ring max' the largest of the same window's \NCtrl{} control "
          r"statistics. $\nu$ is the window centre. The symmetric criterion "
          r"flags a strict subset, %s of the %s. In the %s that drop out the "
          r"stellar position never exceeded its own control ring "
          r"($T_\star$ of %s against ring maxima %s): the region-max statistic "
          r"cleared the ring only by maximising over the source region. For "
          r"%s the region maximum already lay on the star, so the two "
          r"statistics coincide exactly and nothing about it changes.}"
          % (n_src, word(n_sym), word(len(seven)), word(len(dropped)),
             _lst([x["star_snr"] for x in dropped]),
             _lst([x["ring_max"] for x in dropped]),
             " and ".join(x["star_tex"] for x in onstar) or "no window")),
         r"\label{tab:bothstats}",
         r"\begin{tabular}{@{}llr rr rr l@{}}",
         r"\toprule",
         (r"& & & \multicolumn{2}{c}{region-max statistic} & "
          r"\multicolumn{2}{c}{symmetric statistic} & \\"),
         r"\cmidrule(lr){4-5}\cmidrule(lr){6-7}",
         (r"Star & Band & $\nu$ (GHz) & $S_{\rm reg}$ & ctrl max & "
          r"$T_\star$ & ring max & Symmetric outcome \\"),
         r"\midrule"]
    for x in rows:
        L.append(r"%s & %d & %.4f & %.2f & %.2f & %.2f & %.2f & %s \\"
                 % (x["star_tex"], x["band"], x["f_GHz"], x["src_snr"],
                    x["ctrl_max"], x["star_snr"], x["ring_max"],
                    r"flagged" if x["flagged_sym"] else r"not flagged"))
    L += [r"\bottomrule", r"\end{tabular}", r"\end{table}"]
    p = os.path.join(tabdir, "tab_bothstats.tex")
    open(p, "w").write("\n".join(L) + "\n")
    return p


# ======================================================================================
# TABLE 2 -- tab:allhits
# ======================================================================================

def tab_allhits(good, tabdir, rep):
    hits = sorted([r for r in good if r["cross"]], key=lambda r: -r["star_snr"])
    n_spatial = sum(1 for r in hits if r["sbr"])
    n_ctrl = int(st.median(r["n_ctrl"] for r in good))

    rows = []
    for r in hits:
        rows.append(dict(
            star=r["star_name"], star_tex=star_tex(r["star_name"]),
            band=r["band_x"], f_GHz=round(0.5 * (r["flo"] + r["fhi"]), 4),
            star_snr=round(r["star_snr"], 2),
            ring_max=round(r["ctrl_max_all"], 2),
            spatial=bool(r["sbr"]),
            line=r["line"],
            line_off_MHz=(round(r["line_off"], 2)
                          if r["line_off"] is not None else None),
            vel_kms=(round(r["vel_off"], 1)
                     if r["vel_off"] is not None else None)))
    rep["tab_allhits"] = dict(
        n_rows=len(rows), n_windows=len(good), n_spatial=n_spatial,
        n_ctrl=n_ctrl,
        n_no_line=sum(1 for x in rows if x["line"] is None),
        n_within_50kms=sum(1 for x in rows if x["vel_kms"] is not None
                           and abs(x["vel_kms"]) <= 50),
        rows=rows)

    longnote = "; ".join(r"%s is %s in the released table"
                         % (v, tex_escape(k)) for k, v in LONGFORM.items()
                         if any(x["star"] == k for x in rows))
    L = [HEADER, r"\begin{table}", r"\centering", r"\small",
         r"\setlength{\tabcolsep}{4pt}",
         (r"\caption{The full crossing funnel: every one of the %d windows, "
          r"of \NWindows{}, containing a $\geq5\sigma$ crossing at the "
          r"propagated stellar position, ordered by $T_\star$. `Ring max' is "
          r"the largest of that window's \NCtrl{} control statistics, and a "
          r"window is spatially significant (bold, %s of the %d) when "
          r"$T_\star$ exceeds it. $\Delta\nu$ and $\Delta v$ are the offsets "
          r"of the crossing from the nearest catalogued transition of the "
          r"eight masked species, topocentric; the $\pm50$\,km\,s$^{-1}$ mask "
          r"applies in the stellar frame after the conversion chain of "
          r"Appendix~\ref{app:conventions}. $\nu$ is the window centre, not "
          r"the crossing frequency, so it is not $\Delta\nu$ from the "
          r"transition. A dash means the released products record no nearest "
          r"masked transition for that window. %s.}"
          % (len(rows), word(n_spatial), len(rows),
             longnote or "Star names are those of the released table")),
         r"\label{tab:allhits}",
         r"\begin{tabular}{@{}llr rr c lrr@{}}",
         r"\toprule",
         (r"Star & Band & $\nu$ (GHz) & $T_\star$ & ring max & Spatial & "
          r"Nearest masked & $\Delta\nu$ & $\Delta v$ \\"),
         (r"& & & & & & transition & (MHz) & (km\,s$^{-1}$) \\"),
         r"\midrule"]
    for x in rows:
        # bold only the pure-text/number cells: \textbf around a display name
        # containing math (e.g. $\beta$~Pic) would bold half of it
        bf = (lambda s: r"\textbf{%s}" % s) if x["spatial"] else (lambda s: s)
        L.append(r"%s & %d & %.4f & %s & %s & %s & %s & %s & %s \\"
                 % (x["star_tex"], x["band"], x["f_GHz"],
                    bf("%.2f" % x["star_snr"]), "%.2f" % x["ring_max"],
                    bf("yes") if x["spatial"] else "---",
                    line_tex(x["line"]), doff_tex(x["line_off_MHz"]),
                    dv_tex(x["vel_kms"])))
    L += [r"\bottomrule", r"\end{tabular}", r"\end{table}"]
    p = os.path.join(tabdir, "tab_allhits.tex")
    open(p, "w").write("\n".join(L) + "\n")
    return p


# ======================================================================================
# TABLE 3 -- tab:flagged, v3.31 replacement
# ======================================================================================

# EDITORIAL, carried over verbatim from the existing tab:flagged in
# technosignatures_20pc_v3.30.tex, together with that table's row order.
# Keyed by (released star identifier, band).  If the flagged set ever changes,
# the assertion below fails loudly rather than silently dropping a row.
DISPOSITION = collections.OrderedDict([
    (("bet Pic", 3),     "circumstellar CO"),
    (("bet Pic", 6),     "circumstellar CO"),
    (("HD 48370", 6),    "CO cloud emission"),
    (("CP-72 2713", 7),  "control-ensemble background"),
])


def tab_flagged(good, tabdir, rep):
    fl = [r for r in good if r["cross"] and r["sbr"]]
    keys = {(r["star_name"], r["band_x"]) for r in fl}
    missing = keys - set(DISPOSITION)
    extra = set(DISPOSITION) - keys
    if missing or extra:
        raise SystemExit(
            "tab:flagged -- the flagged set no longer matches the dispositions "
            "carried over from v3.30.  New: %s.  Gone: %s.  A human must "
            "decide the disposition text; refusing to guess."
            % (sorted(missing), sorted(extra)))
    order = {k: i for i, k in enumerate(DISPOSITION)}
    fl.sort(key=lambda r: order[(r["star_name"], r["band_x"])])
    n_ctrl = int(st.median(r["n_ctrl"] for r in good))

    rows = []
    for r in fl:
        rows.append(dict(
            star=r["star_name"],
            window_tex=r"%s B%d" % (star_tex(r["star_name"]), r["band_x"]),
            band=r["band_x"], f_GHz=round(0.5 * (r["flo"] + r["fhi"]), 4),
            star_snr=round(r["star_snr"], 2),
            ring_max=round(r["ctrl_max_all"], 2),
            p_emp=round(r["p_emp"], 5),
            line=r["line"],
            line_off_MHz=(round(r["line_off"], 2)
                          if r["line_off"] is not None else None),
            vel_kms=(round(r["vel_off"], 1)
                     if r["vel_off"] is not None else None),
            chanw_kHz=round(r["chanw"] / 1e3, 3),
            disposition=DISPOSITION[(r["star_name"], r["band_x"])]))
    # 1 MHz expressed in km/s at each band represented, derived not typed
    C_KMS = 299792.458
    perband = collections.OrderedDict()
    for x in sorted(rows, key=lambda y: y["band"]):
        perband.setdefault(x["band"], C_KMS * 1e-3 / x["f_GHz"])
    conv = ", ".join("%.2g" % v for v in list(perband.values())[:-1])
    conv = "%s and %.2g" % (conv, list(perband.values())[-1])
    bands = ", ".join(str(b) for b in list(perband)[:-1])
    bands = "%s and~%d" % (bands, list(perband)[-1])

    rep["tab_flagged_v331"] = dict(n_rows=len(rows), n_ctrl=n_ctrl,
                                   rank_floor=n_ctrl + 1,
                                   kms_per_MHz_by_band={
                                       b: round(v, 4) for b, v in perband.items()},
                                   rows=rows)

    L = [HEADER, r"\begin{table}", r"\centering", r"\small",
         r"\setlength{\tabcolsep}{4pt}",
         (r"\caption{The %s windows containing a spatially significant hit and "
          r"the evidence dispositioning each. $T_\star$ is the search "
          r"statistic at the stellar position (Eq.~\ref{eq:tstar}), `ring max' "
          r"the largest of that window's \NCtrl{} control statistics. "
          r"$\Delta\nu$ and $\Delta v$ are the same offset of the crossing "
          r"from the nearest of the eight masked species' catalogued "
          r"transitions, in frequency and in velocity, topocentric; the "
          r"$\pm50$\,km\,s$^{-1}$ mask applies in the stellar frame after the "
          r"conversion chain of Appendix~\ref{app:conventions}. Giving both "
          r"makes the conversion explicit for every row rather than for "
          r"$\beta$~Pic alone: at these window frequencies 1\,MHz is "
          r"%s\,km\,s$^{-1}$ in Bands~%s respectively. No disposition rests "
          r"on a single test.}" % (word(len(rows)), conv, bands)),
         r"\label{tab:flagged}",
         r"\begin{tabular}{@{}lrrrrrl@{}}",
         r"\toprule",
         (r"Window & $\nu$ (GHz) & $T_\star$ & ring max & $\Delta\nu$ (MHz) & "
          r"$\Delta v$ (km\,s$^{-1}$) & Disposition \\"),
         r"\midrule"]
    for x in rows:
        L.append(r"%s & %.4f & %.2f & %.2f & %s & %s (%s) & %s \\"
                 % (x["window_tex"], x["f_GHz"], x["star_snr"], x["ring_max"],
                    doff_tex(x["line_off_MHz"]), dv_tex(x["vel_kms"]),
                    line_tex(x["line"]), x["disposition"]))
    L += [r"\bottomrule", r"\end{tabular}", r"\end{table}"]
    p = os.path.join(tabdir, "tab_flagged_v331.tex")
    open(p, "w").write("\n".join(L) + "\n")
    return p


# ======================================================================================

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--data", default=DEFAULT_DATA)
    ap.add_argument("--tabdir", default=os.path.join(HERE, "tables"))
    ap.add_argument("--figdir", default=os.path.join(HERE, "figures"))
    ap.add_argument("--no-figure", action="store_true")
    args = ap.parse_args()

    os.makedirs(args.tabdir, exist_ok=True)
    good, _sysn = survey_rows(args.data)
    rep = {"data": args.data, "n_windows_searched": len(good)}

    paths = [tab_bothstats(good, args.tabdir, rep),
             tab_allhits(good, args.tabdir, rep),
             tab_flagged(good, args.tabdir, rep)]

    if not args.no_figure:
        import make_figures_referee_v331 as figmod
        os.makedirs(args.figdir, exist_ok=True)
        target = os.path.join(args.figdir, "eirp_context.pdf")
        backup = os.path.join(args.figdir, "eirp_context_prechannel.pdf.bak")
        if os.path.exists(target) and not os.path.exists(backup):
            shutil.copy2(target, backup)
            print("backed up:", backup)
        figmod.set_style()
        paths.append(figmod.fig_eirp_context(good, args.figdir, rep))

    for p in paths:
        print("wrote:", p)
    j = os.path.join(args.tabdir, "referee2_numbers.json")
    json.dump(rep, open(j, "w"), indent=1, default=str)
    print("wrote:", j)


if __name__ == "__main__":
    main()
