#!/usr/bin/env python3
r"""figorphan.py -- every deposited figure is included, every inclusion exists.

Two failure modes, both of which this manuscript has actually shipped:

  (1) an \includegraphics whose file is not there.  That is always a build
      error and is never tolerated.
  (2) a figure built into figures/ and included nowhere -- an orphan.  v4.09
      deposited eight of them, one of which (completeness.pdf) carried a label
      the manuscript had also put on a second anchor, so a \ref resolved to a
      float the reader could not see.  An orphan is a figure no caption
      controls, and nothing in the build could see one.

Orphans are a hard failure unless the file is named in PENDING with an owner
and a reason.  PENDING is deliberately short, printed on every run, and dated:
a figure that sits there is a figure somebody still has to place or delete.

Comments are stripped before scanning, so an \includegraphics on a commented
line does not count as an inclusion -- that is how a float can look alive in
the source while the PDF has no such figure.

USAGE
    python3 figorphan.py                 # the gate
    python3 figorphan.py --list          # what is included, what is pending
    python3 figorphan.py --drive 1       # missing-file clause must fire
    python3 figorphan.py --drive 2       # orphan clause must fire
    python3 figorphan.py --drive 3       # commented-out inclusion must not count
    python3 figorphan.py --drive 4       # undeclared captioned orphan fragment must fire
"""
from __future__ import annotations

import argparse
import glob
import os
import re
import sys

import manuscript

HERE = os.path.dirname(os.path.abspath(__file__))
FIGDIR = os.path.join(HERE, "figures")

# file -> (owner, why it is allowed to be unincluded today).  Dated entries
# only; this list is not a parking space.
# ★ 2026-10-07, INTEGRATION: `hanning_response.pdf` LEFT THIS LIST, and the
# reason is a defect that made `make_all.sh` FAIL FROM A CLEAN TREE for two
# versions without anyone seeing it.  Figure 10 was removed from Appendix A in
# the round-12 length pass (worth 1.0 pp measured; the channel-response kernel
# is analytic, 0.25/0.5/0.25, and all five of its numbers -- \HanBest,
# \HanWorst, \HanMed, \HanFacBest, \HanFacWorst -- are in the paragraph
# beside it and in Table 2's channel-response row), and `make_fig_hanning.py`
# was retired with it.  The PDF was then left in `figures/` and DECLARED here,
# which is the only way a built-and-uncited figure may survive.
#   But PENDING's contract is "this file exists and is not yet included", and a
# figure whose generator is retired cannot exist after a clean regeneration.
# `cleanregen.py` deletes every `figures/*.pdf` and re-runs the build; nothing
# rebuilt this one, and this gate correctly refused: "PENDING names a figure
# that is not built".  Every build since v4.13 passed only because the stale
# PDF was still on disk from a run made before the generator was retired --
# which is exactly the class of defect `cleanregen` exists to find, and the
# first thing it has found that stops the build outright.
# A retired generator's output is not a pending figure; it is not a product of
# this build at all.  So it is not declared, and it is not on disk.
PENDING = {
    "bpic_control.pdf": (
        "results (sections/05_results.tex, sec:bpicval)",
        "2026-10-04, AUTHORISED and BUILT: the beta Pictoris astrophysical "
        "positive control, requested by referee 1 by name. Needs a float and "
        "a caption; requirements in referee_r9/FIGURES_R9.md."),
    "control_diagnostics.pdf": (
        "appendix-triage", "2026-10-04 08:4x: orphaned by the appendix purge."),
    "rank_cdf.pdf": (
        "appendix-triage", "2026-10-04 08:4x: orphaned by the appendix purge."),
    "ledger_vis_v403.pdf": (
        "appendix-triage", "2026-10-04 08:4x: orphaned by the appendix purge; "
        "already uncited before it."),
    "appm_power.pdf": (
        "appendix-triage", "2026-10-04 08:4x: orphaned by the appendix purge."),
    "sensitivity_2d.pdf": (
        "appendix-triage", "2026-10-04 08:4x: orphaned by the appendix purge; "
        "fig:sens2d was already uncited before it."),
    "selection_bias.pdf": (
        "appendix-triage", "2026-10-04 08:4x: orphaned by the appendix purge; "
        "fig:selbias was already uncited before it."),
    "stratified_completeness.pdf": (
        "appendix-triage", "2026-10-04 08:4x: orphaned by the appendix purge."),
    # ★ 2026-10-08, ROUND 15: DELIBERATELY NOT A FIGURE OF THIS PAPER.
    # `calib_r15.py` draws the stellar rank against the continuum-to-noise
    # ratio -- the scatter behind Ruling 3's result -- and the result itself
    # is a correlation coefficient and a sentence, which is what Appendix B
    # carries.  The plot costs about 0.36 pp the paper has not got while
    # saying nothing the coefficient does not.  It satisfies PENDING's
    # contract -- `calib_r15.py` is in `make_all.sh`, so a clean regeneration
    # rebuilds it, which is the condition `hanning_response.pdf` could not
    # meet.
    # ★★ r15-deposit, same day.  This entry's reason USED TO READ "it is a
    # DEPOSIT PRODUCT, named in the data-availability inventory among 'the
    # diagnostic figures the printed paper refers to but does not reproduce'".
    # There is no deposit and that inventory is deleted, so the justification
    # is now simply that the paper does not need the figure.  A PENDING reason
    # that points at a deposit is a reason that does not resolve.
    "calib_cont.pdf": (
        "calibration (calib_r15.py, round 530)",
        "2026-10-08: built but not a figure of the paper; Ruling 3 asked for "
        "a coefficient and a sentence and Appendix B carries both.  It is "
        "not distributed anywhere -- see AUTHOR_ACTIONS.md item 1."),
}

#: Generated `tab_*.tex` fragments that carry a caption and are `\input`
#: nowhere.  Same contract as PENDING: an owner and a dated reason, and the
#: gate fails both on an undeclared one AND on a declaration that no longer
#: describes a captioned orphan, so this cannot become a parking space.
TAB_PENDING = {
    "tab_maskband_v411": (
        "mask (maskframe_v411.py, round 170)",
        "2026-10-20, round 25: the band-by-band mask cost. Superseded as an "
        "article table by Table C1 (tab_maskspecies_v414.tex), which is the "
        "mask by species, and the article states the cost as a single pair of "
        "figures. KEPT because `cleanregen.py` lists it as a product of "
        "`maskframe_v411.py` and retiring a product mid-close is a build "
        "change, not a prose change. ITS CAPTION IS CORRECT AND DERIVED: it "
        "no longer names SO, and it now reads \\FrMaskWorstBand and "
        "\\FrMaskWorstPct, which were computed and cited by no sentence in "
        "the paper. TO DO: retire the fragment or give it a float."),
}

INC = re.compile(r"\\includegraphics\s*(?:\[[^\]]*\])?\s*\{([^}]*)\}")


def strip_comments(txt):
    out = []
    for line in txt.split("\n"):
        i, esc = None, False
        for k, ch in enumerate(line):
            if esc:
                esc = False
                continue
            if ch == "\\":
                esc = True
            elif ch == "%":
                i = k
                break
        out.append(line if i is None else line[:i])
    return "\n".join(out)


def included(drive=0):
    raw = manuscript.flat() + "\n%% \\includegraphics{figures/ghost.pdf}\n"
    # drive 3 skips the comment stripping, so the commented ghost is counted
    # and the missing-file clause fires: the stripping is load-bearing, not
    # decoration.  Undriven, the same text must produce no finding.
    txt = raw if drive == 3 else strip_comments(raw)
    names = [os.path.basename(p) for p in INC.findall(txt)]
    if drive == 1:
        names.append("figures/no_such_figure.pdf")
    return names


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--list", action="store_true")
    ap.add_argument("--drive", type=int, default=0)
    a = ap.parse_args()

    inc = included(a.drive)
    built = sorted(os.path.basename(p) for p in glob.glob(os.path.join(FIGDIR, "*.pdf")))
    if a.drive == 2:
        built = built + ["an_orphan_that_is_not_pending.pdf"]

    missing = [n for n in inc if not os.path.exists(os.path.join(FIGDIR, os.path.basename(n)))]
    orphans = [b for b in built if b not in [os.path.basename(n) for n in inc]]
    unexpected = [o for o in orphans if o not in PENDING]
    stale_pending = [p for p in PENDING if p not in built]

    if a.list or True:
        print("included (%d):" % len(set(inc)))
        for n in sorted(set(inc)):
            print("   ", n)
        if orphans:
            print("orphaned (%d):" % len(orphans))
            for o in orphans:
                who, why = PENDING.get(o, ("--", "NOT PENDING"))
                print("    %-30s %-28s %s" % (o, who, why))
        png = sorted(os.path.basename(p) for p in glob.glob(os.path.join(FIGDIR, "*.png")))
        if png:
            print("note: %d .png sibling(s) in figures/ that LaTeX does not use: %s"
                  % (len(png), ", ".join(png)))

    # ★★★★ ADDED v4.26: AN ORPHAN GENERATED TABLE FRAGMENT THAT CARRIES A
    # CAPTION IS PROSE PUBLISHED AND UNMAINTAINED.  The round-25 referee pass
    # found `tab_maskband_v411.tex` shipping a caption that read "the loss is
    # concentrated in the bands where CO AND SO sit" -- a sentence asserting
    # the line mask the article had just stopped using -- in a file no
    # `\input` reads, so `dupgate`, `labelcheck` and `prosegate` could none of
    # them see it.  Same family as the orphan figures above: a generated
    # product that stopped being consumed and stopped being maintained while
    # still being published in the repository.
    # ★ THE CLAUSE IS NARROW ON PURPOSE.  There are 47 orphan `tab_*.tex`
    # fragments in this tree and exactly ONE of them carries a caption.  A
    # caption-less `tabular` fragment is inert data; a caption is a sentence
    # addressed to a reader, and an unmaintained sentence is the defect.
    # Turning all 47 into a build failure would be a gate dictating a round's
    # work, which this project has caught itself doing six times; the count
    # is therefore REPORTED and the captioned ones are GATED.
    frag_inp = set()
    for _p in (glob.glob(os.path.join(HERE, "sections", "*.tex"))
               + glob.glob(os.path.join(HERE, "technosignatures_*.tex"))):
        for _m in re.findall(r"\\input\{([^}]+)\}",
                             strip_comments(open(_p, errors="ignore").read())):
            frag_inp.add(os.path.basename(_m).replace(".tex", ""))
    orph_tab, orph_cap = [], []
    for _p in sorted(glob.glob(os.path.join(HERE, "tab_*.tex"))):
        _n = os.path.basename(_p)[:-4]
        if _n in frag_inp or re.search(r"_drive\d+$", _n):
            continue
        _t = open(_p, errors="ignore").read()
        orph_tab.append(_n)
        if _t.lstrip().startswith("%% GENERATED") and "\\caption{" in _t:
            orph_cap.append(_n)
    if a.drive == 4:
        orph_cap = orph_cap + ["a_captioned_orphan_v999"]
    print("orphan table fragments: %d not \\input anywhere, of which %d are "
          "generated AND carry a caption" % (len(orph_tab), len(orph_cap)))
    for _n in orph_cap:
        who, why = TAB_PENDING.get(_n, ("--", "NOT DECLARED"))
        print("    %-30s %-28s %s" % (_n, who, why))

    bad = []
    unexpected_tab = [o for o in orph_cap if o not in TAB_PENDING]
    stale_tab = [t for t in TAB_PENDING if t not in orph_cap]
    if unexpected_tab:
        bad.append("generated table fragment carrying a caption, included "
                   "nowhere, and not declared: %s" % ", ".join(unexpected_tab))
    if stale_tab:
        bad.append("TAB_PENDING names a fragment that is no longer a "
                   "captioned orphan: %s" % ", ".join(sorted(stale_tab)))
    if missing:
        bad.append("\\includegraphics with no file: %s" % ", ".join(sorted(set(missing))))
    if unexpected:
        bad.append("figure built and included nowhere, and not in PENDING: %s"
                   % ", ".join(unexpected))
    if stale_pending:
        bad.append("PENDING names a figure that is not built: %s"
                   % ", ".join(sorted(stale_pending)))
    if bad:
        for b in bad:
            print("FAIL:", b)
        sys.exit(1)
    print("figorphan: %d included, %d pending, 0 unexpected orphans, "
          "0 missing files" % (len(set(inc)), len(orphans)))


if __name__ == "__main__":
    main()
