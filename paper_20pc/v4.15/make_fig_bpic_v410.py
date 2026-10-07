#!/usr/bin/env python3
r"""figures/bpic_control.pdf -- the beta Pictoris astrophysical positive control.

THE ONE QUESTION THIS FIGURE ANSWERS
    Does the blind search recover a real narrow line at a stellar position --
    and what are the strongest apparent signals in a millimetre survey when it
    does?

Both panels are drawn from the released catalogue, per_target_results_v3.99.csv,
one row per searched window.  Nothing is read from the processing host, nothing
is typed that the catalogue or the macro layer carries, and the retired column
eirp_p90_sel_W is not read at all.

(a) THE SPATIAL STATISTIC.  Every one of the survey's \NHits threshold
    crossings, plotted as the control-ring maximum over \NCtrl positions
    against the statistic at the star.  Noise crossings sit in a band at a ring
    maximum of 5-7 whatever the star does.  beta Pic's CO(1-0) crossings sit far
    to the right of that band with an ordinary ring: a compact source AT the
    star, recovered blind in five independent execution blocks.  Two cases sit
    the other way -- HD 48370's foreground CO(2-1), where the ring rises with
    the star as emission filling the primary beam does, and one beta Pic
    CO(2-1) block where the ring beats the star outright.  The same statistic
    that promotes compact circumstellar CO rejects extended CO.

(b) THE LINE CONFUSION, MADE QUANTITATIVE.  The same crossings by the absolute
    velocity offset from the nearest masked transition IN THE STAR'S OWN REST
    FRAME, against the +-\MaskVWidth km/s attribution mask.  The strongest
    crossings in the survey are the ones that land on a line.

    â The frame matters and this panel used to get it wrong.  It plotted the
    released TOPOCENTRIC offsets under a mask the paper evaluates in the
    stellar frame, so it placed every beta Pic CO crossing 12.5-28.6 km/s from
    CO while the ledger table gave 2-4 km/s and the body text gave 0.3.  Three
    numbers for one quantity.  The offsets are now taken from maskframe_v411,
    the module ledger_v410 also uses, and asserted equal to the ledger's own
    column -- so the figure and Table tab:ledger cannot disagree again.

WHAT IS ASSERTED (each with a drive that makes it fire)
    A1  the 5 sigma trigger is DERIVED from the catalogue, not typed: the set
        of rows with star_snr >= 5 is exactly the set flagged `crossing`
    A2  the flagged beta Pic counts and peak statistics reproduce
        \BpicNFlagThree / \BpicBThreeTsym and \BpicNFlagSix / \BpicBSixTsym
    A3  HD 48370 reproduces \HdTsym and \HdRingMax
    A4  the crossings plotted are the ones the released catalogue and the
        adopted ledger SHARE, \NCross less the four the ledger added, and
        neither the four added nor the four fallen is a beta Pic or HD 48370
        crossing -- so this figure's argument is invariant under the change
    A5  the mask half-width drawn is \MaskVWidth, resolved through round 103's
        aliases, and every beta Pic CO crossing falls inside it

USAGE
    python3 make_fig_bpic_v410.py [--outdir figures] [--drive N]
    A drive writes figures/bpic_control_driveN.pdf, never a production path.

MUST RUN AFTER numbers_v410.py (round 103): it reads \MaskVWidth, which that
round aliases.

Author: ASTRA PA (figures), for G. J. White.
"""
from __future__ import annotations

import argparse
import csv
import glob
import json
import os
import re

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt          # noqa: E402
import numpy as np                       # noqa: E402
import maskframe_v411 as mf             # noqa: E402
from matplotlib.ticker import FixedFormatter, FixedLocator, NullLocator  # noqa: E402

HERE = os.path.dirname(os.path.abspath(__file__))
CAT = os.path.join(HERE, "per_target_results_v3.99.csv")
DEFAULT_OUTDIR = os.path.join(HERE, "figures")

BPIC = "bet Pic"
HD = "HD 48370"


def texval(name, _seen=None):
    """Last literal definition of \\name, following round 103's aliases.

    LAST and alias-following, because round 103 retires a superseded name by
    \\renewcommand-ing it to its replacement; a reader that matches
    \\newcommand only, or stops at the first file, gets the superseded value or
    nothing at all.  That defect made the budget macro invisible to
    make_fig_classa_sens.py, which then drew a withdrawn band instead.
    """
    pat = re.compile(r"\\(?:new|renew|provide)command\{\\%s\}"
                     r"\{((?:[^{}]|\{[^{}]*\})*?)\}" % re.escape(name))
    out = None
    for f in sorted(glob.glob(os.path.join(HERE, "survey_numbers*.tex"))):
        for m in pat.finditer(open(f).read()):
            v = m.group(1).strip()
            if v:
                out = v
    seen = _seen or set()
    while out and re.fullmatch(r"\\[A-Za-z]+", out) and out not in seen:
        seen.add(out)
        out = texval(out[1:], seen)
    assert out is not None, (
        "\\%s is not defined; make_fig_bpic_v410.py must run after "
        "numbers_v410.py (round 103)" % name)
    return out


def texnum(name):
    return float(texval(name))


def rows(drive=0):
    R = list(csv.DictReader(open(CAT)))
    for r in R:
        r["_star"] = float(r["star_snr"])
        r["_ring"] = float(r["ctrl_max_snr"])
        r["_cross"] = r["crossing"] == "True"
        r["_dv_sky"] = (float(r["line_offset_kms"])
                        if r["line_offset_kms"] else None)
        _ft = mf.recover_ftopo(r["nearest_line"], r["line_offset_MHz"])
        _fr = mf.frame_row(r["eb"], r["star_name"], r["flo_GHz"], _ft)
        r["_dv"] = _fr["dv_stellar"] if _fr.get("ok") else None
        r["_line"] = _fr.get("line")
        r["_nge"] = int(r["n_ctrl_ge_star"]) if r["n_ctrl_ge_star"] else 0
    if drive == 1:          # perturbation: one flagged beta Pic window unflags
        for r in R:
            if (r["star_name"] == BPIC and r["nearest_line"] == "CO(1-0)"
                    and r["_cross"] and r["_nge"] == 0):
                r["_nge"] = 1
                break
    if drive == 4:          # perturbation: a crossing below the trigger
        for r in R:
            if r["_cross"] and r["_star"] > 30:
                r["_cross"] = False
                break
    if drive == 5:          # perturbation: a second block lets the ring win
        for r in R:
            if (r["star_name"] == BPIC and r["nearest_line"] == "CO(2-1)"
                    and r["_cross"] and r["_nge"] == 0):
                r["_nge"] = 7
                r["_ring"] = r["_star"] * 1.4
                break
    if drive == 3:          # perturbation: HD 48370's ring is mis-stated
        for r in R:
            if r["star_name"] == HD and r["_cross"]:
                r["_ring"] = 6.0
    return R


def trigger(R):
    """A1: derive the trigger from the catalogue rather than typing 5."""
    cr = {id(r) for r in R if r["_cross"]}
    for t in (5.0,):
        ge = {id(r) for r in R if r["_star"] >= t}
        if ge == cr:
            return t
    raise AssertionError(
        "the `crossing` flag is not the set of rows at or above any trigger "
        "this figure knows: %d flagged, %d at or above 5 sigma"
        % (len(cr), sum(1 for r in R if r["_star"] >= 5.0)))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--outdir", default=DEFAULT_OUTDIR)
    ap.add_argument("--drive", type=int, default=0)
    a = ap.parse_args()

    plt.rcParams.update({"pdf.fonttype": 42, "ps.fonttype": 42,
                         "font.family": "serif", "font.serif": ["DejaVu Serif"],
                         "mathtext.fontset": "dejavuserif"})
    R = rows(a.drive)
    TRIG = trigger(R)
    released = [r for r in R if r["_cross"]]

    # ★★ A4, rewritten 2026-10-04 09:1x, when ledger_v410.py adopted a new
    # crossing list.  The catalogue's `crossing` column is the RELEASED list;
    # the adopted list drops four of those and adds four others, and BOTH are
    # 56 long.  Asserting len(crossings) == \NCross would therefore have
    # passed on the wrong set -- the same count-for-set substitution that let
    # the chain figure print a sky-frame count under a stellar-frame heading.
    # So: plot the crossings the two lists share, identify the difference, and
    # require the difference to leave this figure's argument untouched.
    LED = json.load(open(os.path.join(HERE, "ledger.json")))
    added = [r for r in LED["rows"] if r["source"] != "released"]
    adopted_eb = {(r["eb"], str(r["band"])) for r in LED["rows"]}
    fell = [r for r in released
            if (r["eb"], str(r["band"])) not in adopted_eb]
    cross = [r for r in released if r not in fell]
    nD = LED["summary"]["delta"]
    assert len(added) == nD["added"] and len(fell) == nD["fell"], (
        "the catalogue and the ledger disagree about the delta: %d added, "
        "%d fallen, against %d/%d declared"
        % (len(added), len(fell), nD["added"], nD["fell"]))
    assert len(cross) == int(texnum("NCross")) - nD["added"], (
        "%d shared crossings against \\NCross %d less %d added"
        % (len(cross), texnum("NCross"), nD["added"]))

    # ★ the check the figure exists to survive: neither the four crossings
    # that fell nor the four that were added belongs to beta Pic or HD 48370,
    # so the adopted ledger leaves every point drawn here exactly where it was.
    _touched = [r for r in added + fell
                if str(r.get("star") or r.get("star_name")).startswith(
                    (BPIC, "bet Pic", HD))]
    assert not _touched, (
        "the adopted ledger moves a crossing this figure argues from: %s"
        % [(r.get("star") or r.get("star_name"), r["eb"]) for r in _touched])

    bp = [r for r in cross if r["star_name"] == BPIC]
    bp_co = [r for r in bp if r["nearest_line"].startswith("CO(")]
    b3 = [r for r in bp_co if r["nearest_line"] == "CO(1-0)"]
    b6 = [r for r in bp_co if r["nearest_line"] == "CO(2-1)"]
    hd = [r for r in cross if r["star_name"] == HD]
    other = [r for r in cross if r not in bp and r not in hd]

    # A2: "flagged" means the star outranks all \NCtrl controls.
    f3 = [r for r in b3 if r["_nge"] == 0]
    f6 = [r for r in b6 if r["_nge"] == 0]
    assert len(f3) == int(texnum("BpicNFlagThree")), (
        "%d flagged Band 3 windows against \\BpicNFlagThree %d"
        % (len(f3), texnum("BpicNFlagThree")))
    assert len(f6) == int(texnum("BpicNFlagSix")), (
        "%d flagged Band 6 windows against \\BpicNFlagSix %d"
        % (len(f6), texnum("BpicNFlagSix")))
    for got, name in ((max(r["_star"] for r in f3), "BpicBThreeTsym"),
                      (max(r["_star"] for r in f6), "BpicBSixTsym")):
        assert abs(got - texnum(name)) < 0.005, (
            "the peak drawn, %.2f, is not \\%s %.2f" % (got, name, texnum(name)))
    # A3
    assert len(hd) == 1, "HD 48370 should contribute exactly one crossing"
    for got, name in ((hd[0]["_star"], "HdTsym"), (hd[0]["_ring"], "HdRingMax")):
        assert abs(got - texnum(name)) < 0.005, (
            "HD 48370 is drawn at %.2f where \\%s is %.2f"
            % (got, name, texnum(name)))
    # A5
    MASK = texnum("MaskVWidth")
    if a.drive == 2:
        MASK = 0.1
    outside = [r for r in bp_co if abs(r["_dv"]) > MASK]
    assert not outside, (
        "a beta Pic CO crossing falls outside the +-%g km/s mask: %s"
        % (MASK, [(r["eb"], r["_dv"]) for r in outside]))

    # ★★ A6.  The figure and the ledger table must carry ONE offset per
    # crossing.  Join on the execution block and the crossing frequency --
    # not on the star name, and not on the released offset, which is the
    # quantity under repair -- and require every shared row to agree.
    _ledv = {(q["eb"], round(q["freq"], 4)): q["dv_stellar"]
             for q in LED["rows"]}
    _bad = []
    for r in cross:
        _ft = mf.recover_ftopo(r["nearest_line"], r["line_offset_MHz"])
        k = (r["eb"], round(_ft, 4))
        if k not in _ledv:
            _bad.append((r["eb"], _ft, "not in the ledger"))
        elif abs(_ledv[k] - r["_dv"]) > 0.05:
            _bad.append((r["eb"], _ledv[k], r["_dv"]))
    if a.drive == 6:
        _bad.append(("driven", 0.0, 1.0))
    assert not _bad, (
        "the figure and the ledger disagree about %d crossing offset(s): %s"
        % (len(_bad), _bad[:4]))

    # ★ Single-column geometry: the results owner placed this at
    # \columnwidth, and a 7-inch two-panel figure squeezed into 246 pt sets
    # its labels at about 3 pt.  Two stacked panels instead, drawn at the
    # size they are used.
    fig, axes = plt.subplots(2, 1, figsize=(3.4, 4.35),
                             gridspec_kw=dict(hspace=0.42))

    # ---------------------------------------------------- (a) star against ring
    ax = axes[0]
    lo, hi = 3.0, 40.0
    ax.plot([lo, hi], [lo, hi], color="0.75", lw=0.8, ls="-", zorder=1)
    ax.text(25.0, 27.0, "ring $=$ star", fontsize=5.2, color="0.5",
            rotation=40, rotation_mode="anchor", ha="center")
    ax.axvline(TRIG, color="#b03030", ls=":", lw=0.9, zorder=1)
    # ★ v4.11 (R1-1): the trigger is a threshold on T_star, not a sigma
    # level.  Labelling it "5 sigma" inside a panel is the shortest possible
    # version of the conflation Referee 1's first point is about.
    ax.text(TRIG * 1.05, 3.62, "trigger $T=%g$" % TRIG, fontsize=5.4,
            color="#b03030", va="bottom")
    ax.scatter([r["_star"] for r in other], [r["_ring"] for r in other],
               s=9, marker="o", facecolor="none", edgecolor="0.55",
               linewidths=0.5, zorder=3,
               label="other crossings (%d)" % len(other))
    ax.scatter([r["_star"] for r in b3], [r["_ring"] for r in b3],
               s=20, marker="o", color="#3a6ea5", zorder=5,
               label=r"$\beta$ Pic CO(1$-$0), %d blocks" % len(b3))
    ax.scatter([r["_star"] for r in b6], [r["_ring"] for r in b6],
               s=20, marker="^", color="#7bb0e0", edgecolor="#3a6ea5",
               linewidths=0.5, zorder=5,
               label=r"$\beta$ Pic CO(2$-$1), %d blocks" % len(b6))
    ax.scatter([r["_star"] for r in hd], [r["_ring"] for r in hd],
               s=30, marker="*", color="#d08c20", edgecolor="0.2",
               linewidths=0.4, zorder=6, label="HD 48370 foreground CO(2$-$1)")
    _ex = [r for r in bp_co if r["_nge"] > 0]
    for r in _ex:
        ax.annotate("ring wins: %d of %s controls\nabove the star"
                    % (r["_nge"], texval("NCtrl")),
                    xy=(r["_star"], r["_ring"]), xytext=(11.0, 3.72),
                    fontsize=5.2, color="0.25", ha="left",
                    arrowprops=dict(arrowstyle="-", lw=0.4, color="0.45"))
    ax.set_xscale("log"); ax.set_yscale("log")
    ax.set_xlim(lo, hi); ax.set_ylim(3.5, 30.0)
    ax.xaxis.set_major_locator(FixedLocator([5, 10, 20, 30]))
    ax.xaxis.set_major_formatter(FixedFormatter(["5", "10", "20", "30"]))
    ax.xaxis.set_minor_locator(NullLocator())
    ax.yaxis.set_major_locator(FixedLocator([4, 5, 7, 10, 15, 20, 30]))
    ax.yaxis.set_major_formatter(FixedFormatter(["4", "5", "7", "10", "15",
                                                 "20", "30"]))
    ax.yaxis.set_minor_locator(NullLocator())
    ax.set_xlabel(r"statistic at the star, $T_\star$", fontsize=7.6)
    ax.set_ylabel("maximum over the %s\ncontrol positions" % texval("NCtrl"),
                  fontsize=7.6)
    ax.set_title("(a) recovered blind, at the star, in every block",
                 fontsize=7.0, pad=3)
    ax.tick_params(labelsize=6.8)
    ax.grid(color="0.9", lw=0.4)
    leg = ax.legend(fontsize=5.2, frameon=True, framealpha=0.95, loc="upper left",
                    handletextpad=0.4, borderpad=0.25, labelspacing=0.3,
                    edgecolor="0.8")
    leg.get_frame().set_linewidth(0.3)

    # --------------------------------------- (b) offset from a catalogued line
    ax = axes[1]
    ax.axhspan(0.0, MASK, color="#3a6ea5", alpha=0.10, lw=0, zorder=1)
    ax.axhline(MASK, color="#3a6ea5", lw=0.8, ls="--", zorder=2)
    ax.text(33.0, MASK * 1.3, r"$\pm%g$ km s$^{-1}$ mask" % MASK,
            fontsize=5.6, color="#3a6ea5", ha="right")

    def dv(rs):
        return [max(abs(r["_dv"]), 0.3) for r in rs]

    ax.scatter([r["_star"] for r in other], dv(other), s=9, marker="o",
               facecolor="none", edgecolor="0.55", linewidths=0.5, zorder=3)
    ax.scatter([r["_star"] for r in b3], dv(b3), s=20, marker="o",
               color="#3a6ea5", zorder=5)
    ax.scatter([r["_star"] for r in b6], dv(b6), s=20, marker="^",
               color="#7bb0e0", edgecolor="#3a6ea5", linewidths=0.5, zorder=5)
    ax.scatter([r["_star"] for r in hd], dv(hd), s=30, marker="*",
               color="#d08c20", edgecolor="0.2", linewidths=0.4, zorder=6)
    _cs = [r for r in bp if r not in bp_co]
    if _cs:
        ax.scatter([r["_star"] for r in _cs], dv(_cs), s=16, marker="s",
                   facecolor="none", edgecolor="#3a6ea5", linewidths=0.6,
                   zorder=4)
        ax.annotate(r"$\beta$ Pic, %d windows %s km s$^{-1}$"
                    "\nfrom any catalogued line"
                    % (len(_cs), r"$\sim\!4000$"),
                    xy=(max(r["_star"] for r in _cs), max(dv(_cs))),
                    xytext=(9.0, 1.1e4), fontsize=5.0, color="0.25",
                    ha="left", arrowprops=dict(arrowstyle="-", lw=0.4,
                                               color="0.45"))
    ax.set_xscale("log"); ax.set_yscale("log")
    ax.set_xlim(lo, hi); ax.set_ylim(0.25, 1.0e5)
    ax.xaxis.set_major_locator(FixedLocator([5, 10, 20, 30]))
    ax.xaxis.set_major_formatter(FixedFormatter(["5", "10", "20", "30"]))
    ax.xaxis.set_minor_locator(NullLocator())
    ax.set_xlabel(r"statistic at the star, $T_\star$", fontsize=7.6)
    ax.set_ylabel("$|$offset$|$ from the nearest masked\ntransition, "
                  "stellar frame (km s$^{-1}$)", fontsize=7.6)
    ax.set_title("(b) the strongest crossings are the ones on a line",
                 fontsize=7.0, pad=3)
    ax.tick_params(labelsize=6.8)
    ax.grid(color="0.9", lw=0.4)

    for a_ in axes:
        for sp in ("top", "right"):
            a_.spines[sp].set_visible(False)

    # ------------------------------------------------------------ macros
    # ★ The caption should quote this figure's numbers, not gesture at them,
    # and the generator that draws them is the one that owns them.  Written
    # to survey_numbers_round104.tex, which the manuscript must \input (and a
    # caption must cite, or retire_macros.py deletes them -- which is what
    # happened to \BpicDvLo/\BpicDvHi earlier today).
    #
    # ★ \NStageOneBpicEb counts the blocks in which the STAR OUTRANKS EVERY
    # CONTROL; \BpicPanelNCo counts the beta Pic CO points DRAWN, which is
    # that number plus the one block where the ring wins.  They are different
    # counts of different things and the assertion below keeps them that way,
    # so neither can quietly be used for the other.
    _dv_co = sorted(abs(r["_dv"]) for r in bp_co)
    _dv_cs = sorted(abs(r["_dv"]) for r in _cs)
    _rw = _ex[0]
    assert len(_ex) == 1, "the figure argues from exactly one ring-wins block"
    assert len(bp_co) == int(texnum("NStageOneBpicEb")) + len(_ex), (
        "%d CO points drawn against \\NStageOneBpicEb %d star-outranks blocks "
        "plus %d ring-wins" % (len(bp_co), texnum("NStageOneBpicEb"), len(_ex)))
    assert len(other) + len(bp_co) + len(_cs) + len(hd) == len(cross), (
        "the drawn series do not partition the %d crossings plotted" % len(cross))
    M = ["%% GENERATED by make_fig_bpic_v410.py -- do not hand-edit.",
         "\\newcommand{\\BpicPanelNCo}{%d}" % len(bp_co),
         "\\newcommand{\\BpicPanelNCs}{%d}" % len(_cs),
         "\\newcommand{\\BpicPanelNOther}{%d}" % len(other),
         "\\newcommand{\\BpicDvCoLo}{%.1f}" % _dv_co[0],
         "\\newcommand{\\BpicDvCoHi}{%.1f}" % _dv_co[-1],
         "\\newcommand{\\BpicDvCsLo}{%.0f}" % _dv_cs[0],
         "\\newcommand{\\BpicPanelNDrawn}{%d}"
         % (len(other) + len(bp_co) + len(_cs) + len(hd)),
         "\\newcommand{\\BpicPanelNExcluded}{%d}" % nD["added"],
         "\\newcommand{\\BpicDvCsHi}{%.0f}" % _dv_cs[-1],
         "\\newcommand{\\BpicRingWinRing}{%.2f}" % _rw["_ring"],
         "\\newcommand{\\BpicRingWinStar}{%.2f}" % _rw["_star"],
         "\\newcommand{\\BpicRingWinNAbove}{%d}" % _rw["_nge"],
         "\\newcommand{\\BpicRingWinEb}{%s}"
         % _rw["eb"].replace("_", "\\_"),
         ""]
    if not a.drive:
        open(os.path.join(HERE, "survey_numbers_round104.tex"), "w").write(
            "\n".join(M))

    name = "bpic_control" + ("_drive%d" % a.drive if a.drive else "")
    path = os.path.join(a.outdir, name + ".pdf")
    fig.savefig(path, bbox_inches="tight", pad_inches=0.03)
    plt.close(fig)

    rep = {
        "question": "does the blind search recover a real narrow line at a "
                    "stellar position, and what are the strongest apparent "
                    "signals when it does",
        "source": os.path.basename(CAT),
        "trigger_sigma_derived": TRIG,
        "n_crossings_plotted": len(cross),
        "ledger_delta": nD,
        "delta_touches_this_figure": False,
        "bpic_CO10_blocks": len(b3), "bpic_CO21_blocks": len(b6),
        "bpic_flagged_CO10": len(f3), "bpic_flagged_CO21": len(f6),
        "bpic_Tstar_max_CO10": max(r["_star"] for r in b3),
        "bpic_Tstar_max_CO21_flagged": max(r["_star"] for r in f6),
        "bpic_ring_range_CO10": [min(r["_ring"] for r in b3),
                                 max(r["_ring"] for r in b3)],
        "bpic_dv_range_CO": [min(r["_dv"] for r in bp_co),
                             max(r["_dv"] for r in bp_co)],
        "bpic_ring_wins": [(r["eb"], r["_star"], r["_ring"], r["_nge"])
                           for r in _ex],
        "hd48370": [hd[0]["_star"], hd[0]["_ring"], hd[0]["_dv"]],
        "mask_half_width_kms": MASK,
    }
    if not a.drive:
        with open(os.path.join(HERE, "figures_bpic_v410.json"), "w") as fh:
            json.dump(rep, fh, indent=1)
    print("wrote:", path)
    print(json.dumps(rep, indent=1))


if __name__ == "__main__":
    main()
