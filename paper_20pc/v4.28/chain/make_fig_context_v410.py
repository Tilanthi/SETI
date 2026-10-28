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
      --drive 5  the threshold-provenance check must fire (perturbation: Enriquez
                 et al. are assumed to be at 5 sigma, which is the error M8 found)
    A drive writes figures/*_driveN.pdf, never a production path (D36), and no
    drive writes tab_litthresh_r15.tex or survey_numbers_round570.tex.

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
import figfloor_r17 as ff                  # the type floor, the scale, the float
ff.pin_epoch()                             # before any savefig: see PIN below
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
#
# ★★★★ THE PANEL CALLED EVERY ONE OF THESE A 5-SIGMA THRESHOLD.  THREE OF THE FOUR ARE
# NOT.  A published EIRP limit is that programme's own detection threshold times a flux,
# and the thresholds drawn here differ by a factor of five between the strictest and the
# loosest:
#
#     Enriquez et al. (2017)   S/N = 25      Price et al. (2020)   S/N = 10
#     Margot   et al. (2023)   S/N = 10      Mason et al. (2025)   S/N =  5
#
# Smin is linear in the threshold -- Enriquez Eq. (4), Price Eq. (6), Margot Eq. (5) and
# Mason Eq. (8) are the same expression -- so EIRP_min is linear in it too, and a common
# basis is reached by multiplying each published limit by SNR_COMMON / snr.  `snr_src`
# holds the sentence each threshold was read from, in that paper's own words; no
# threshold here comes from another paper's summary of a third.
#
# One independent cross-check, which is not ours: Margot et al.'s own Table 4 recomputes
# the sensitivity of both Breakthrough Listen surveys and labels the rows "For S/N=25 in
# 300 s (Enriquez et al. 2017)" and "For S/N=10 in 300 s (Price et al. 2020)".
# --------------------------------------------------------------------------------------
SNR_COMMON = 5.0          # the common basis, and this survey's own trigger: T_star >= 5

LIT = {
    "enriquez2017": dict(
        label="Enriquez+17 (GBT, 692 stars)",
        pts=[(50.0, 5.2e12)],
        snr=25.0,
        snr_src="Enriquez et al. 2017, ApJ 849, 104, sec. 4: 'For the A stars, we only "
                "consider hits with an S/N greater than 25.  We reserve the S/N range "
                "between 20 and 25 for RFI signals'; and sec. 5.1: 'the minimum "
                "detectable flux density for a five-minute L-band observation with the "
                "GBT, at 3 Hz resolution for an S/N of at least 25 is 17 Jy'.  The "
                "pipeline trigger was 20; the limit is quoted at 25.",
        src="Enriquez et al. 2017, ApJ 849, 104, Tables 3-4 (arXiv combined table): "
            "'EIRP [W] 5.2x10^12' at 'Distance to Stars [pc] 50', which is the value "
            "their published CWTFM of 0.85 is computed from and the value Wright et al. "
            "2018 quote for them ('EIRP >~ 5.2x10^12 W').  Their abstract rounds this up "
            "to '~10^13 W'; the caption promises the deepest limit each paper reports, so "
            "the tabulated value is the one used.",
        chan_Hz=2.79, chan_label="2.8 Hz",
        chan_src="Enriquez et al. 2017 abstract: 'channelized into narrowband (3 Hz) "
                 "channels'; the BL high-spectral-resolution product is 2.79 Hz "
                 "(Lebofsky et al. 2019, Table 4).",
        freq_GHz=(1.10, 1.90),
        freq_src="Enriquez et al. 2017, title: '1.1-1.9 GHz Observations of 692 Stars'.",
        colour="#E69F00", marker="D", size=17,
    ),
    "margot2023": dict(
        # ★ r16-referee: thin space, not a comma.  Sec. 6.2 sets this very
        # number as `11 680` (\FomMargotN), so the figure legend and the
        # text were printing one quantity two ways.
        label="Margot+23 (GBT, 11 680 stars)",
        # ★ r16: the far point was plotted at 6135 pc and the comment below
        # said "20,000 ly = 6135 pc".  Margot et al. write **6132 pc** (sec.
        # 3.6, "transmitters located 20,000 ly (6132 pc) away"), and the
        # conversion agrees with them, not with us: 20000 x 0.3066013 =
        # 6132.0.  0.05 per cent in the plotted abscissa, but it is their
        # number and it is now computed from their own light-year figure
        # rather than restated.
        pts=[(100.0, 1.35e13), (20000.0 * 0.3066013, 5.08e16)],
        snr=10.0,
        snr_src="Margot et al. 2023, AJ 166, 206, sec. 3.6: 'Our usual detection "
                "threshold is set at S/N=10, such that signals with flux Sdet = 11.3 x "
                "10^-26 W/m2 are detectable ... transmitters located 326 ly (100 pc) "
                "away are detectable with 0.62 Arecibos (EIRP=1.35 x 10^13 W)'.  The "
                "two plotted limits are quoted in that same sentence, so they carry "
                "that threshold.",
        src="Margot et al. 2023, AJ 166, 206, sec. 3.6, which is where both plotted "
            "values are stated: 'transmitters located 326 ly (100 pc) away are detectable "
            "with 0.62 Arecibos (EIRP = 1.35 x 10^13 W), transmitters located 20,000 ly "
            "(6132 pc) away are detectable with 2323 Arecibos (EIRP = 5.08 x 10^16 W)'. "
            "Their abstract and conclusions round the same two limits to '>10^13 W' and "
            "'>5 x 10^16 W' for 100 pc and 20,000 ly respectively.  20000 x 0.3066013 = "
            "6132.0, which is their own figure.",
        chan_Hz=2.98, chan_label="3.0 Hz",
        # ★ the sentence cited here used to be the one in sec. 3.7 describing the
        # process that IMITATES Breakthrough Listen, not the UCLA search itself.  The
        # value is unchanged -- VEGAS splits the band into 3.125 MHz coarse channels
        # (sec. 3.1) and the transform length is 2^20, so 3.125e6 / 2^20 = 2.98 Hz --
        # but the provenance now points at the search this figure plots.
        chan_src="Margot et al. 2023, sec. 3.6: 'For the UCLA SETI program at the GBT, "
                 "we have ... Delta f ~= 3 Hz'; sec. 3.1 gives the 3.125 MHz VEGAS "
                 "coarse channel, so with the 2^20 transform the resolution is "
                 "3.125e6 / 2^20 = 2.98 Hz.",
        freq_GHz=(1.15, 1.73),
        freq_src="Margot et al. 2023, title: '... with the Green Bank Telescope at "
                 "1.15-1.73 GHz'.",
        colour="#00A0A0", marker="s", size=17,
    ),
    "mason2025": dict(
        label="Mason+25 (ALMA B3, 28 stars)",
        pts=[(1010.0, 6.91e17)],
        snr=5.0,
        snr_src="Mason et al. 2025, MNRAS 536, 2127, sec. 4: 'We assumed a Gaussian "
                "distribution for a pixel across all frequency channels and used SNR > "
                "5 as our detection threshold ... We estimated the minimum detectable "
                "flux density, Smin, as the SNR threshold multiplied by the r.m.s "
                "measured within the field of view of each calibrator.'  This is the "
                "one comparison programme already on the common basis.",
        src="Mason et al. 2025, MNRAS 536, 2127, sec. 4: 'the smallest minimum "
            "detectable power ... is 6.91 x 10^17 W for the closest target star'; that "
            "star's distance in their Table 2 is 1.010 kpc.",
        chan_Hz=30.52e3, chan_label="30.5 kHz",
        chan_src="Mason et al. 2025, sec. 3: 'The data were correlated with 3840 "
                 "frequency points, each channel being 30.52 kHz wide'.",
        freq_GHz=(84.0, 116.0),
        freq_src="Mason et al. 2025: ALMA Band 3 (84-116 GHz), delta-nu < 35 kHz.",
        colour="#7B3EAD", marker="^", size=19,
    ),
    "price2020": dict(
        label="Price+20 (GBT, Parkes, deepest)",
        pts=[(None, 2.1e12), (None, 9.1e12)],
        tick_names=["GBT", "Parkes"],
        snr=10.0,
        snr_src="Price et al. 2020, AJ 159, 86, sec. 3: 'we searched ... for narrowband "
                "signals with a S/N >=10'; and sec. 5.4: 'using a lower S/N cutoff (10 "
                "vs. 25).  The result is that our sensitivity is better by a factor of "
                "2.5x' -- which is 25/10, so the limit is linear in the threshold in "
                "their own arithmetic.",
        src="Price et al. 2020, AJ 159, 86, abstract: 'we find no evidence of putative "
            "radio transmitters above 2.1x10^12 W, and 9.1x10^12 W for Green Bank and "
            "Parkes observations, respectively'; repeated in sec. V.2 ('The EIRP_min for "
            "our GBT observations is 2.1x10^12 W, and 9.1x10^12 W for Parkes observations "
            "at the 50 pc maximum distance') and sec. V.3.  Deepest per-target limits, not "
            "a single sample distance, so drawn as left-edge ticks.",
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

# The order the comparison programmes are tabulated and labelled in, strictest native
# threshold first.  Derived from the data, so adding a programme cannot leave it out.
LIT_ORDER = sorted(LIT, key=lambda k: (-LIT[k]["snr"], k))


def scale_to_common(key):
    """The factor that puts a published EIRP limit on the SNR_COMMON basis.

    Smin -- and therefore EIRP_min = 4 pi d^2 Smin delta-nu -- is linear in the
    detection threshold in all four papers' own expressions, so the factor is just
    the ratio of thresholds.  It is computed, never written down, so a programme
    whose threshold is corrected cannot leave a stale factor in the figure or in
    the table.
    """
    return SNR_COMMON / LIT[key]["snr"]


def pts_common(key):
    """[(distance_pc, EIRP on the common basis)] for one programme."""
    f = scale_to_common(key)
    return [(d, y * f) for d, y in LIT[key]["pts"]]


def chan_span(rows):
    """(narrowest, widest, decades) over the comparison programmes' channels and
    this survey's own.  ONE owner, because panel (b) draws it and the caption
    states it, and those two must not be able to compute it differently."""
    cw = [float(r["chanw_Hz"]) for r in rows]
    lit_hz = [LIT[k]["chan_Hz"] for k in LIT]
    lo, hi = min(lit_hz + cw), max(lit_hz + cw)
    return lo, hi, math.log10(hi / lo)


def _hz(v, sep=" "):
    """A channel width as a number with the unit a reader expects for it."""
    for div, unit in ((1e6, "MHz"), (1e3, "kHz"), (1.0, "Hz")):
        if v >= div:
            return "%.3g%s%s" % (v / div, sep, unit)
    return "%.3g%sHz" % (v, sep)


def _lit_legend(key):
    """The legend entry: the programme, and the threshold it published at.

    Read from `snr`, so a legend cannot go on saying 5 sigma after a threshold
    is corrected -- which is the defect this whole block exists to repair.
    """
    return "%s, S/N %g" % (LIT[key]["label"], LIT[key]["snr"])


def assert_thresholds_sourced(drive=0):
    """Every comparison programme must carry a threshold AND the sentence it was
    read from, and the figure must not silently assume the common basis.

    This is the clause the caption's old claim -- 'all at their own 5 sigma
    thresholds' -- would have had to pass and could not.  Driven by --drive 5,
    which restores that assumption for Enriquez.
    """
    for k in LIT_ORDER:
        snr = 5.0 if (drive == 5 and k == "enriquez2017") else LIT[k]["snr"]
        assert snr > 0, k
        src = LIT[k]["snr_src"]
        # the number must appear AS A NUMBER, next to the words "S/N" or "SNR", in
        # the quoted sentence: "S/N greater than 25" does not support a threshold of
        # 5 merely because the character 5 occurs in 25.
        near = re.compile(r"(?:S/N|SNR)[^.]{0,30}?(?<![0-9])%d(?![0-9])" % int(snr))
        assert len(src) > 60 and near.search(src), (
            "the threshold S/N = %g for %s is not supported by the sentence quoted "
            "from that paper: %r" % (snr, k, src[:160]))
    # ...and at least one of them must differ from the common basis, or the whole
    # rescaling is decoration.  (If a future comparison set really were all at
    # 5 sigma this clause should be deleted deliberately, not silenced.)
    n_rescaled = sum(1 for k in LIT_ORDER
                     if abs(scale_to_common(k) - 1.0) > 1e-12)
    assert n_rescaled >= 1, "no comparison programme needs rescaling"
    return n_rescaled


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
    for f in sorted([_mgp for _mgp in glob.glob(os.path.join(HERE, "survey_numbers*.tex")) if '_drive' not in _mgp]):
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
        # ★ A WINDOW AND A LIMIT ARE NOT THE SAME POPULATION.  `_A` counts
        # the windows the carrier search covers, which the attribution mask
        # does not change; `_lim` marks the ones that carry a limit, which
        # excludes a window every channel of which lies inside the mask
        # (Sec. \ref{sec:lines}).  Panel (a) is a plot of limits.
        r["_lim"] = r["_A"] and _ae.limit_eligible(
            r, HERE)
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


# ★★ THE TYPE FLOOR.  FS_REQUIRED is what these two panels are HELD to and is
#    never perturbed; FS_FLOOR is what they are DRAWN at.  They are separate
#    so that a drive cannot move the check and the thing it checks together.
FS_REQUIRED = 6.5


def fs_floor(drive=0):
    return FS_REQUIRED if drive != 61 else 5.6     # 61: as the panels shipped


def set_style(drive=0):
    fs = fs_floor(drive)
    plt.rcParams.update({
        "font.family": "serif",
        "font.serif": ["STIXGeneral", "DejaVu Serif", "Times New Roman"],
        "mathtext.fontset": "stix",
        "font.size": 8.4, "axes.titlesize": 8.0, "axes.labelsize": 8.0,
        "xtick.labelsize": 7.0, "ytick.labelsize": 7.0, "legend.fontsize": fs,
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
    #
    # ★★★★ ...AND THE OTHER HALF OF THAT COMPARISON WAS WRONG TOO.  "Every
    # literature point is that programme's own bare 5 sigma flux threshold" is
    # true of one of the four.  Enriquez et al. quote their limit at S/N = 25,
    # Price et al. and Margot et al. at S/N = 10, Mason et al. at S/N = 5 (the
    # sentences are in LIT above).  Every published limit is therefore put on
    # the common 5 sigma basis before it is drawn, and the published value is
    # kept on the panel as a small open marker joined to it, so the reader can
    # see both the comparison and what was done to make it one.
    t = np.array([r["_trig"] for r in best.values()])
    o = np.argsort(d)
    # ★★★★ r22 (referee 2, point 8).  THE PANEL DREW COARSE-CHANNEL LIMITS AS
    #   CARRIER LIMITS.  The deepest window of 24 of the 90 stars is a Class B
    #   window -- the stars with no fine-channel coverage at all, Proxima,
    #   Barnard's Star and Wolf 359 among them -- and Table 3 says of Class B
    #   "never a carrier search".  Those 24 were plotted in the same blue
    #   circles as the 66 carrier searches, and their limits are the DEEPER
    #   ones (median 7.5e14 W against 1.4e15), so the panel made the carrier
    #   experiment look deeper than it is.  The two classes are now drawn with
    #   distinct markers and counted separately in the legend, and the class
    #   is the class of the PLOTTED WINDOW: a star whose deepest window is
    #   coarse belongs with the coarse ones whatever else it carries.
    isA = np.array([bool(r["_A"]) for r in best.values()])
    _anyA = {}
    for r in _ALLROWS:
        _anyA[r["_star"]] = _anyA.get(r["_star"], False) or bool(r["_A"])
    _cover = np.array([_anyA[s] for s in best])
    if drive == 70:                     # perturbation: the classes are mixed
        isA = ~isA
    assert (isA == _cover).all(), (
        "a star's deepest window is in one class and its coverage in the "
        "other, so the legend cannot describe the symbols: %s"
        % [s for s, a, c in zip(best, isA, _cover) if a != c][:4])
    o = np.argsort(d)
    d, e, t, isA = d[o], e[o], t[o], isA[o]
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
    # ★ The guide's label has moved from 2600 pc to 2 pc, and below the line
    #   rather than above it.  At the type floor the legend is wide enough to
    #   reach the old position, and the lower-left reach of the guide is the
    #   one stretch of it that crosses neither the legend nor the points.
    _D2X = 2.0 if drive != 65 else 2600.0        # 65: the position it had
    _d2lab = ax.text(_D2X, D2_NORM * _D2X ** 2 * (1 if drive != 65 else 1.6),
                     r"EIRP $\propto d^{2}$",
                     fontsize=fs_floor(drive), color="0.45", rotation=38,
                     rotation_mode="anchor", ha="left", va="top",
                     zorder=6)

    # the benchmark transmitter of Sec. 6 -- a power scale, not a model
    ax.axhline(bench, ls="--", lw=1.0, color="#009E73", zorder=2)
    ax.text(2.2e4, bench * 1.22, bench_lbl.replace(chr(92) + ",", " "),
            fontsize=fs_floor(drive), color="#009E73", ha="right", va="bottom",
            zorder=6,
            bbox=dict(facecolor="white", edgecolor="none", alpha=0.8, pad=0.6))
    if drive == 1:                      # perturbation: the old line comes back
        ax.text(1.0, 2.0e13, "Arecibo-like planetary radar",
                fontsize=fs_floor(drive))

    for _msk, _col, _mk, _sz in ((isA, "#0072B2", "o", 1.0),
                                 (~isA, "#7F7F7F", "v", 1.05)):
        if not _msk.any():
            continue
        ax.vlines(d[_msk], np.minimum(t, e)[_msk], np.maximum(t, e)[_msk],
                  lw=0.45, color=_col, alpha=0.40, zorder=3)
        ax.scatter(d[_msk], e[_msk], s=13 * _sz, marker=_mk, facecolor="none",
                   edgecolor=_col, linewidths=0.6, alpha=0.95, zorder=4)
        ax.scatter(d[_msk], t[_msk], s=11 * _sz, marker=_mk, facecolor=_col,
                   edgecolor="none", alpha=0.85, zorder=5)

    # ★ the comparison programmes, each rescaled to the common basis, with its own
    #   published value kept above it as a hollow marker on a hairline.
    for key in ("enriquez2017", "margot2023", "mason2025"):
        L = LIT[key]
        xs_ = [p[0] for p in L["pts"]]
        y_pub = [p[1] for p in L["pts"]]
        y_cmn = [p[1] for p in pts_common(key)]
        if scale_to_common(key) != 1.0:
            ax.vlines(xs_, y_cmn, y_pub, lw=0.5, color=L["colour"], alpha=0.75,
                      zorder=4)
            ax.scatter(xs_, y_pub, s=L["size"] * 0.75, marker=L["marker"],
                       facecolor="none", edgecolor=L["colour"], linewidths=0.6,
                       zorder=5)
        ax.scatter(xs_, y_cmn, s=L["size"] * 2.4, marker=L["marker"],
                   color="white", edgecolor="none", zorder=5)
        ax.scatter(xs_, y_cmn, s=L["size"] * 1.6, marker=L["marker"],
                   color=L["colour"], edgecolor="k", linewidths=0.8, zorder=6)
    L = LIT["price2020"]
    for (_, y_pub), (_, y_cmn), nm in zip(L["pts"], pts_common("price2020"),
                                          L["tick_names"]):
        ax.plot([xlo, xlo * 1.55], [y_pub, y_pub], lw=0.6, color=L["colour"],
                alpha=0.75, solid_capstyle="butt", zorder=4)
        ax.plot([xlo * 1.14, xlo * 1.14], [y_cmn, y_pub], lw=0.5,
                color=L["colour"], alpha=0.75, zorder=4)
        ax.plot([xlo, xlo * 1.55], [y_cmn, y_cmn], lw=1.4, color=L["colour"],
                solid_capstyle="butt", zorder=5)
        ax.text(xlo * 1.75, y_cmn, nm, fontsize=fs_floor(drive), color=L["colour"],
                ha="left", va="center", zorder=6)

    ax.set_xscale("log"); ax.set_yscale("log")
    ax.set_xlim(xlo, xhi); ax.set_ylim(ylo, yhi)
    ax.set_xlabel("distance (pc)", labelpad=1.0)
    ax.set_ylabel("minimum detectable EIRP (W)\n"
                  "rescaled to a common %g$\\sigma$ basis;\n"
                  "false-alarm rates are not matched"
                  % SNR_COMMON, fontsize=7.0, labelpad=1.5)
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
               Line2D([], [], ls="none", marker="v", mfc="#7F7F7F",
                      mec="none", ms=3.6),
               Line2D([], [], ls="none", marker="o", mfc="none", mec="#0072B2",
                      mew=0.6, ms=3.7),
               Line2D([], [], ls="--", color="#009E73", lw=1.0)]
    labels = ["this survey, carrier search (Class A, %d stars)"
              % int(isA.sum()),
              "this survey, unresolved excess only (Class B, %d)"
              % int((~isA).sum()),
              "   both at $\\mathrm{EIRP}_{90}$ (open), 5$\\sigma$ "
              "threshold (filled)",
              "benchmark transmitter, $%s$ W" % texval("BenchEirp")]
    for key in ("enriquez2017", "margot2023", "mason2025"):
        L = LIT[key]
        handles.append(Line2D([], [], ls="none", marker=L["marker"],
                              mfc=L["colour"], mec="k", mew=0.7, ms=4.4))
        labels.append(_lit_legend(key))
    handles.append(Line2D([], [], color=LIT["price2020"]["colour"], lw=1.4))
    labels.append(_lit_legend("price2020"))
    handles.append(Line2D([], [], ls="-", lw=0.5, color="0.45", marker="s",
                          mfc="none", mec="0.45", mew=0.6, ms=2.6))
    labels.append("   as published, at that programme's own threshold")
    leg = ax.legend(handles, labels, loc="upper left",
                    fontsize=fs_floor(drive),
                    handletextpad=0.5, borderpad=0.3, labelspacing=0.38,
                    borderaxespad=0.3, framealpha=0.93)
    leg.get_frame().set_linewidth(0.4)

    assert_no_arecibo(fig, drive)

    # the panel must reproduce the manuscript's own sensitivity numbers
    eA = np.array([eirp90(r, ma, mb) for r in rows if r["_lim"]])
    sysbest = {}
    for r in rows:
        if not r["_lim"]:
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
        "n_stars_class_A": int(isA.sum()),
        "n_stars_class_B_only": int((~isA).sum()),
        "eirp90_median_class_A_W": float(np.median(e[isA])),
        "eirp90_median_class_B_W": float(np.median(e[~isA])),
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
    # ★ A TIGHT BOUNDING BOX HAS NO WIDTH ANYONE CHOSE.  This panel was emitted
    #   at whatever its own labels happened to need -- 229.7 pt -- and placed at
    #   245.3, so every size in it was silently multiplied by 1.068.  fit_width
    #   solves for the canvas that trims to exactly the width the float gives.
    _target = ff.COL_PT if drive not in (60, 62) else ff.TEXT_PT
    if drive == 63:
        os.environ.pop("SOURCE_DATE_EPOCH", None)
    ff.save_to_width(fig, p, _target, format="pdf", pad_inches=0.015)
    # ★ ORDER: geometry first.  A wrong scale makes every size and every gap
    #   wrong at once, and a layout clause run first would report the collision
    #   and hide the geometry fault that caused it.
    # ★ tight=True: these panels are saved with a tight bounding box, so the
    #   FIT clause cannot fail on them and is declared not applicable rather
    #   than reported as passing.  Driving it was tried both ways -- an
    #   over-long label simply enlarges the canvas, and a clipped one is
    #   dropped from the PDF and cannot be measured there at all.
    ff.check(p, HERE, "figures/eirp_context_a.pdf", floor=FS_REQUIRED, tight=True,
             expect_env="figure*" if drive == 62 else "figure")
    # ★ The guide label and the legend are both inside the axes and neither is
    #   placed by the layout engine, so nothing but this can see them meet.
    ff.no_overlap(ax.get_xticklabels() + ax.get_yticklabels()
                  + [ax.xaxis.label, ax.yaxis.label, _d2lab]
                  + list(leg.get_texts()), fig, clear=0.0)
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
    _lo, _hi, span = chan_span(rows)

    fig = plt.figure(figsize=(3.45, 2.85))
    ax = fig.add_axes([0.165, 0.155, 0.815, 0.825])

    ax.scatter(fc[~fine], cw[~fine], s=6.5, marker="v", facecolor="none",
               edgecolor="0.55", linewidths=0.45, zorder=3)
    ax.scatter(fc[fine], cw[fine], s=4.5, marker="o", facecolor="#0072B2",
               edgecolor="none", alpha=0.55, zorder=4)
    for key in ("enriquez2017", "margot2023", "price2020", "mason2025"):
        L = LIT[key]
        ax.plot(L["freq_GHz"], [L["chan_Hz"]] * 2, lw=1.8, color=L["colour"],
                solid_capstyle="butt", zorder=5)

    for key, ty, lab in (("price2020", 2.0e6, "Price+20  2.79 Hz"),
                         ("enriquez2017", 2.0e5, "Enriquez+17  2.79 Hz"),
                         ("margot2023", 2.0e4, "Margot+23  2.98 Hz")):
        L = LIT[key]
        ax.text(1.05, ty, lab, fontsize=fs_floor(drive), color=L["colour"],
                ha="left", va="center", zorder=7)
        ax.plot([3.6, L["freq_GHz"][1] * 1.02], [ty * 0.60, L["chan_Hz"] * 1.35],
                lw=0.45, color=L["colour"], alpha=0.75, zorder=6)
    ax.text(5.5, 2.2e2, "Mason+25  30.5 kHz", fontsize=fs_floor(drive),
            color=LIT["mason2025"]["colour"], ha="left", va="center", zorder=7)
    ax.plot([34.0, 98.0], [3.4e2, 2.4e4], lw=0.45,
            color=LIT["mason2025"]["colour"], alpha=0.75, zorder=6)

    ax.scatter([], [], s=4.5, marker="o", facecolor="#0072B2", edgecolor="none",
               label="this survey, Class A (%d)" % int(fine.sum()))
    ax.scatter([], [], s=6.5, marker="v", facecolor="none", edgecolor="0.55",
               linewidths=0.45, label="this survey, Class B (%d)" % int((~fine).sum()))
    leg = ax.legend(loc="lower right", fontsize=fs_floor(drive),
                    handletextpad=0.4,
                    borderpad=0.3, labelspacing=0.35, framealpha=0.93)
    leg.get_frame().set_linewidth(0.4)

    # ★ minor 16.  The span annotation was a bare double-headed arrow between two
    #   typed ordinates, with "Dlog Dnu_ch ~ 7" written sideways beside it, and a
    #   reader could not tell what either end of it was.  The referee offers two
    #   remedies -- label both ends, or delete the annotation and put the figure
    #   in the caption.  Both ends cannot be labelled where the arrow stands: at
    #   the right-hand margin the upper label lands on the Class B points and the
    #   lower one on the legend, and moving the arrow puts it through the
    #   literature segments.  So the annotation GOES, and the span goes into the
    #   caption with both of its ends named, as \LtChanSpanDex, \LtChanNarrow and
    #   \LtChanWide.  The quantity is unchanged; only the place it is stated is.
    y_lo_span, y_hi_span = _lo, _hi

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
        "span_narrow_Hz": float(y_lo_span), "span_wide_Hz": float(y_hi_span),
    }
    name = "eirp_context_b" + ("_drive%d" % drive if drive else "")
    p = os.path.join(outdir, name + ".pdf")
    _target = ff.COL_PT if drive not in (60, 62) else ff.TEXT_PT
    if drive == 63:
        os.environ.pop("SOURCE_DATE_EPOCH", None)
    ff.save_to_width(fig, p, _target, format="pdf", pad_inches=0.015)
    ff.check(p, HERE, "figures/eirp_context_b.pdf", floor=FS_REQUIRED, tight=True,
             expect_env="figure*" if drive == 62 else "figure")
    ff.no_overlap(ax.get_xticklabels() + ax.get_yticklabels()
                  + [ax.xaxis.label, ax.yaxis.label], fig, clear=0.0)
    plt.close(fig)
    return p


def _sci(v, nd=2):
    """'1.35e13' -> '1.35\\times10^{13}', for a LaTeX macro body."""
    ex = int(math.floor(math.log10(abs(v))))
    m = v / 10.0 ** ex
    s = ("%." + str(nd) + "f") % m
    s = s.rstrip("0").rstrip(".") if "." in s else s
    return (r"%s\times10^{%d}" % (s, ex)) if s != "1" else r"10^{%d}" % ex


# ======================================================================================
# M8: the comparison table, and the macros the manuscript quotes it by
# ======================================================================================
def thresholds_table(rows, report, drive=0, texout=None):
    """Write `tab_litthresh_r15.tex` and `survey_numbers_round570.tex`.

    ★★★★ `texout` EXISTS BECAUSE A GATE WAS WRITING THESE TWO FILES INTO THE
    BUILD ROOT.  `fragstale.py`'s S3 re-runs a generator into a scratch
    directory and compares the fragment byte for byte; it decides a generator
    can take a destination by looking for the string "--out" in its source,
    and this file had only `--outdir`, of which `--out` is an unambiguous
    argparse prefix.  So S3 sent the FIGURES to its scratch directory and
    these two .tex products to the build root -- a test writing a path
    production reads, which is this project's fourteenth defect family and a
    standing rule against it.  The visible effect was worse than the
    principle: round 570 was rewritten AFTER `retire_macros.py` had run, so
    21 macros the retirement pass had just removed came back, and the macro
    layer differed between two consecutive `gate.sh` runs on an unchanged
    tree.  The destination now follows the flag.

    One row per comparison programme: its native threshold, the factor that puts
    it on the common basis, its channel width, and its published limit before and
    after.  Every cell is computed from LIT, so the table cannot disagree with the
    panel drawn from the same dictionary.
    """
    n_rescaled = assert_thresholds_sourced(drive)
    trows, macro = [], []
    for k in LIT_ORDER:
        L = LIT[k]
        f = scale_to_common(k)
        # the deepest (smallest) published limit of that programme, which is the
        # number its abstract leads with and the one the panel is read off
        y_pub = min(p[1] for p in L["pts"])
        y_cmn = min(p[1] for p in pts_common(k))
        cite = L["label"].split("+")[0].replace(" ", "")
        # the printed name is the citation and the year, taken from the legend
        # label so the table and the panel cannot name a programme differently
        nice = L["label"].split(" (")[0].replace("+", "\\,+\\,")
        trows.append(r"%s & %g & %.2f & %s & $%s$ & $%s$ \\"
                    % (nice, L["snr"], f, L["chan_label"].replace(" ", r"\,"),
                       _sci(y_pub), _sci(y_cmn)))
        macro.append((cite, L["snr"], f, L["chan_label"], y_pub, y_cmn))

    tab = "\n".join([
        "%% GENERATED by make_fig_context_v410.py -- do not hand-edit.",
        r"\begin{tabular}{@{}lccccc@{}}",
        r"\toprule",
        r"programme & S/N & factor & $\Delta\nu_{\rm ch}$ &"
        r" EIRP$_{\rm min}$ & at $%g\sigma$ \\" % SNR_COMMON,
        r" & & & & (W) & (W) \\",
        r"\midrule",
    ] + trows + [r"\bottomrule", r"\end{tabular}", ""])
    out_tab = os.path.join(texout or HERE, "tab_litthresh_r15.tex")
    if not drive:
        open(out_tab, "w").write(tab)

    M = []
    for cite, snr, f, ch, y_pub, y_cmn in macro:
        M.append(r"\newcommand{\Lt%sSnr}{%g}" % (cite, snr))
        M.append(r"\newcommand{\Lt%sScale}{%.2f}" % (cite, f))
        M.append(r"\newcommand{\Lt%sChan}{%s}" % (cite, ch.replace(" ", r"\,")))
        M.append(r"\newcommand{\Lt%sEirp}{%s}" % (cite, _sci(y_pub)))
        M.append(r"\newcommand{\Lt%sEirpFive}{%s}" % (cite, _sci(y_cmn)))
    M.append(r"\newcommand{\LtCommonSnr}{%g}" % SNR_COMMON)
    M.append(r"\newcommand{\LtNProg}{%d}" % len(LIT_ORDER))
    M.append(r"\newcommand{\LtNRescaled}{%d}" % n_rescaled)
    M.append(r"\newcommand{\LtScaleWorst}{%.2f}"
             % min(scale_to_common(k) for k in LIT_ORDER))
    # minor 16: the channel-width span, stated in the caption instead of drawn
    c_lo, c_hi, c_dex = chan_span(rows)
    M.append(r"\newcommand{\LtChanNarrow}{%s}" % _hz(c_lo, r"\,"))
    M.append(r"\newcommand{\LtChanWide}{%s}" % _hz(c_hi, r"\,"))
    M.append(r"\newcommand{\LtChanSpanDex}{%.0f}" % c_dex)
    if not drive:
        open(os.path.join(texout or HERE, "survey_numbers_round570.tex"),
             "w").write(
            "%% GENERATED by make_fig_context_v410.py -- do not hand-edit.\n"
            + "\n".join(M) + "\n")
    report["thresholds"] = {
        "common_snr": SNR_COMMON,
        "n_rescaled": n_rescaled,
        "programmes": {k: {"snr": LIT[k]["snr"],
                           "snr_src": LIT[k]["snr_src"],
                           "scale_to_common": scale_to_common(k),
                           "chan_Hz": LIT[k]["chan_Hz"],
                           "pts_published": LIT[k]["pts"],
                           "pts_common": pts_common(k)} for k in LIT_ORDER},
    }
    return tab, M


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--outdir", default=DEFAULT_OUTDIR)
    #: where the two .tex products go.  Named `--out` because that is
    #: what `fragstale.py`'s S3 passes, and because an option of that
    #: name must be an exact match rather than a prefix of --outdir.
    ap.add_argument("--out", default=HERE)
    ap.add_argument("--drive", type=int, default=0)
    args = ap.parse_args()
    # ★ r27 (CLUSTER_REBASELINE finding): a re-run with only `--out
    # <scratch>` (fragstale's S3) left --outdir at its default, so EVERY gate
    # run rewrote the published figures and figures_context_v410.json in the
    # build root -- unseen only because the bytes matched.  The figures now
    # follow --out unless --outdir is given explicitly.
    if (os.path.abspath(args.out) != os.path.abspath(HERE)
            and os.path.abspath(args.outdir) == os.path.abspath(DEFAULT_OUTDIR)):
        args.outdir = os.path.join(args.out, "figures")
    set_style(args.drive)
    os.makedirs(args.outdir, exist_ok=True)
    report = {"catalogue": os.path.basename(CAT),
              "multiplier_source": os.path.basename(M3A)}
    ma, mb, _mrep = multipliers(args.drive)
    report["multipliers"] = _mrep
    rows = catalogue(args.drive)
    thresholds_table(rows, report, args.drive, args.out)
    pa = panel_a(rows, ma, mb, args.outdir, report, args.drive)
    pb = panel_b(rows, args.outdir, report, args.drive)
    # ★ A drive that silently passes is worse than no drive: 60-64 are each
    #   expected to have broken a clause by now, so reaching this line with one
    #   set is itself a failure, and it keeps a drive out of the json below.
    assert args.drive not in (60, 61, 62, 63, 65), (
        "--drive %d reached the end of the generator: the clause it was "
        "written to break did not fire" % args.drive)
    print("wrote:", pa, pb)
    # ★★★★ r26-integrate, 2026-10-23 (Ruling 6 / Ruling 8): THE DESTINATION
    # FOLLOWS THE FLAG, FOR EVERY PRODUCT.  `fragstale.py`'s S3 re-runs a
    # generator with `--out <scratch>`, and `--out` is an unambiguous argparse
    # prefix of `--outdir`, so this generator WAS writing its figures to the
    # scratch directory and the products below into the build root -- a test
    # writing a path production reads, the fourteenth defect family here.
    # `make_fig_context_v410.py` fixed this for its .tex products at v4.16 and
    # the identical defect in THIS file was never looked for; the census found
    # it as `figures_context_v410.json`, outside `cleanregen`'s product list
    # and therefore invisible to the regeneration check.
    _dest = (HERE if os.path.abspath(args.outdir) == os.path.abspath(DEFAULT_OUTDIR)
             else args.out if os.path.abspath(args.out) != os.path.abspath(HERE)
             else args.outdir)
    #: relative paths, so the record does not embed the build directory
    #: (the cluster rebuild differed from the container in this file alone)
    _rel = lambda q: os.path.relpath(q, _dest) if isinstance(q, str) and \
        os.path.isabs(q) else q
    if not args.drive:
        with open(os.path.join(_dest, "figures_context_v410.json"), "w") as fh:
            json.dump({"figures": [_rel(pa), _rel(pb)], "numbers": report,
                       "literature": {k: {"pts": v["pts"], "src": v["src"],
                                          "chan_src": v["chan_src"],
                                          "freq_src": v["freq_src"],
                                          "snr": v["snr"],
                                          "snr_src": v["snr_src"],
                                          "scale_to_common": scale_to_common(k),
                                          "pts_common": pts_common(k)}
                                      for k, v in LIT.items()},
                       "common_snr": SNR_COMMON,
                       "d2_guide_norm_W_at_1pc": D2_NORM}, fh, indent=1)
    print(json.dumps(report, indent=1))


if __name__ == "__main__":
    main()
