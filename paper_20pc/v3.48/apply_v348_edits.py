#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Merged v3.48 edit set: referees 1, 2 and 3, conflicts resolved.

Every anchor is verbatim from technosignatures_20pc_v3.47.tex (= the v3.48 file
before this script runs) and must occur exactly once.  Run once; it is not
idempotent.  Source of each edit is named in the tag.
"""
import io, sys

TEX = 'technosignatures_20pc_v3.48.tex'
src = io.open(TEX, encoding='utf-8').read()
orig = len(src)
E = []


def e(tag, action, anchor, new=''):
    E.append((tag, action, anchor, new))


# ============================== CORRECTIONS =================================

# R1-E1 (supersedes R2-E1 and R3-E17): the width belongs to the recurring window
e('R1E1', 'replace',
  "Band~3 and \\BpWidthSixKms\\,km\\,s$^{-1}$ in Band~6, CO linewidths for this belt,\nwhere a carrier occupies one channel.",
  "Band~3 and \\BpWidthSixRecLo--\\BpWidthSixRecHi\\,km\\,s$^{-1}$ in Band~6, both an\norder of magnitude above the one channel a carrier occupies.")

# R2-E7 + R1-E3 combined (supersedes R3-E3): drop the antithesis, qualify the
# localisation with the beam that made it.
e('R2E7+R1E3', 'replace',
  "because the source fills the ring, which is a physical answer and not a\nstatistical one, and the frozen products already place this emission off the\nstar.",
  "because the source fills the ring, and the frozen products place it off the\nstar, though only coarsely: the window's \\BeamBpicSixRec-arcsec synthesised\nbeam exceeds $r_{\\rm in}$, so the innermost controls are not resolved from it.")

# R1-E2: the beam cannot support the edge-on kinematic claim
e('R1E2', 'delete',
  " A transmitter sits at the star; CO in an edge-on belt sits at the ansae,\nand the sight line through the stellar position samples the orbit where the\nradial velocity is near zero. Emission at the star is therefore narrow and\ncentred on systemic while the ansae inside the annulus carry $\\pm v_{\\rm Kep}$.")

# R1-E4 (supersedes R2-E2 and R2-E5), macroised: state the kinematic distance
e('R1E4', 'replace',
  "where a flat rotation curve\npredicts $V_{\\rm LSR}=+23.1$\\,km\\,s$^{-1}$ for gas a couple of kpc away,\nagainst the $+23.9$\\,km\\,s$^{-1}$ our own LSR chain measures. That is what\nGalactic rotation gives for a foreground cloud in that direction and nothing\nlocal could produce it.",
  "where a flat rotation curve\n($R_{0}=\\RzeroKpc$\\,kpc, $\\Theta_{0}=\\ThetaZeroKms$\\,km\\,s$^{-1}$) reaches the\n$+\\VlsrHdLsr$\\,km\\,s$^{-1}$ our own LSR chain measures at a kinematic distance\nof \\KinDistKpc\\,kpc, which nothing local could produce.")

# R1-E5: do not claim a limit the catalogue does not carry
e('R1E5', 'replace',
  "feature; the corresponding CO($2{\\to}1$) mass limit comes from that star's\nBand~6 window and is released with the catalogue.",
  "feature; that star's Band~6 window bounds circumstellar CO($2{\\to}1$) at\n$M_{\\rm CO}<\\CoMassLo$--$\\CoMassHi\\times10^{19}$\\,kg in optically thin LTE.")

# R1-E6: restore the control ring's own local null (protected self-criticism)
e('R1E6', 'replace',
  "an extreme-value fit to this window's \\NCtrl{} control maxima, every one of\nthem above the Bonferroni scale. The",
  "an extreme-value fit to this window's \\NCtrl{} control maxima, all three above\nthe Bonferroni scale; the window's \\emph{ring} maximum has local-null $p$ of\n\\LNpCPRing, only \\LNCPRingRatio{} times the star's. The")

# R1-E7 / R1-E8: proportionality, not equality
e('R1E7', 'replace',
  "$\\sigma\\simeq{\\rm SEFD}/\\sqrt{N_{\\rm bl}\\Delta\\nu_{\\rm ch}t_{\\rm on}}$, in the",
  "$\\sigma\\propto{\\rm SEFD}/\\sqrt{N_{\\rm bl}\\Delta\\nu_{\\rm ch}t_{\\rm on}}$, in the")
e('R1E8', 'replace',
  "$q\\equiv\\sigma\\sqrt{t_{\\rm on}\\Delta\\nu_{\\rm ch}}\\simeq{\\rm SEFD}/\\sqrt{N_{\\rm\nbl}}$",
  "$q\\equiv\\sigma\\sqrt{t_{\\rm on}\\Delta\\nu_{\\rm ch}}\\propto{\\rm SEFD}/\\sqrt{N_{\\rm\nbl}}$")

# R1-E9: the estimator keeps the real part
e('R1E9', 'replace',
  "step~3), and returns the weighted vector average of the phase-shifted",
  "step~3), and returns the real part of the weighted vector average of the phase-shifted")

# R1-E10: the seed is re-applied per window, which is what buys the two-epoch test
e('R1E10', 'replace',
  "out}^{2})}$, and uniform in azimuth, from the fixed seed \\RingSeed, so\nthe layout is reproducible.",
  "out}^{2})}$, and uniform in azimuth, from the fixed seed \\RingSeed, re-applied\nper window, so all windows share one pattern in units of $\\theta_{\\rm PB}$ and\ntwo windows of one tuning sample identical sky positions\n(Fig.~\\ref{fig:cp72ctrl}).")

# R1-E11: a crossing count is a floor on extent, not a bound
e('R1E11', 'replace',
  "contiguous, so the count bounds the feature's extent at\n\\BpWidthSixKms\\,km\\,s$^{-1}$ without measuring it",
  "contiguous, so the count sets a floor of \\BpWidthSixKms\\,km\\,s$^{-1}$ on the\nfeature's extent without measuring it")

# R1-E12: the covered denominator is an upper bound
e('R1E12', 'replace',
  "here is \\NStars{} of about \\NGenuinelyCovered{} genuinely covered stars",
  "here is \\NStars{} of at most about \\NGenuinelyCovered{} genuinely covered stars")

# R1-E13: restore the survey-wide edge-proximity context (protected)
e('R1E13', 'replace',
  "into its own window. $T_\\star$ exceeds the ring maximum by \\CpTwoMargin,",
  "into its own window, though edge proximity is common across the survey,\n\\NPeakOuterThree{} of \\NPeakRows{} recorded peak channels falling in the outer\n3 per cent of their own. $T_\\star$ exceeds the ring maximum by \\CpTwoMargin,")

# R2-E3, macroised: measure the debris-disc prior instead of asserting it
e('R2E3', 'replace',
  "The searched sample is, to a good\napproximation, the ALMA debris-disc and young-moving-group archive, the\nworst case for astrophysical false positives at millimetre wavelengths,\nso the flags concentrate where the foreground is richest.",
  "The searched sample is a debris-disc archive in the\narchive's own terms: \\NDiskCatStars{} of the \\NStars{} stars were observed\nunder proposals categorised \\emph{Disks and planet formation} and\n\\NDebrisKwStars{} carry the \\emph{Debris disks} science keyword\n(\\NDebrisKwSys{} of \\NSys{} systems). That is the worst case for astrophysical\nfalse positives at millimetre wavelengths, so the flags concentrate where the\nforeground is richest.")

# R2-E4: a non-detection bounds, it does not forbid
e('R2E4', 'replace',
  "report the HD~48370 disc undetected in both CO and carbon, so none of this\nemission can be circumstellar;",
  "report the HD~48370 disc undetected in both CO and carbon, which excludes the\ncircumstellar alternative to their sensitivity;")

# R2-E6: the caption contradicts the CP-72 disposition
e('R2E6', 'delete', "No disposition rests on a single\ntest. ")

# R3-E14: the headline table must carry the corrected denominator
e('R3E14', 'replace',
  "Stars within 40\\,pc with qualifying public ALMA coverage & \\NCensus{} \\\\",
  "Stars within 40\\,pc with qualifying public ALMA coverage & \\NCensus{} \\\\\n\\quad genuinely pointed at; never observed (\\S\\ref{sec:exclusions}) & \\NGenuinelyCovered{}; \\NNeverObsStars{} \\\\")

# R3-E15: the ~1 per cent rests on the uncorrected 168
e('R3E15', 'replace',
  "solar-neighbourhood catalogue (17\\,566 stars within 40\\,pc) they are\n${\\sim}1$ per cent.",
  "solar-neighbourhood catalogue (17\\,566 stars within 40\\,pc) they are\n$\\lesssim$1 per cent, and fewer once \\S\\ref{sec:exclusions} removes those\nnever in fact observed.")

# R3-E16: "crossing" is counted two ways
e('R3E16', 'replace',
  "crossing & one channel$\\times$drift cell at the stellar position with\n$T\\geq5$: a threshold crossing (state 1) \\\\",
  "crossing & one channel$\\times$drift cell at the stellar position with\n$T\\geq5$: a threshold crossing (state 1); counted per window in the main\ntext and per cell in Appendix~\\ref{app:falsealarm} \\\\")

# R3-E18: say which statistic is compared with which
e('R3E18', 'replace',
  "\\CtrlMedFine{} observed against \\FaPredFine{} predicted, coarse\n\\CtrlMedCoarse{} against \\FaPredCoarse.",
  "median observed control maxima \\CtrlMedFine{} against an expected maximum\n\\FaPredFine, coarse \\CtrlMedCoarse{} against \\FaPredCoarse.")

# R3-E5: stale v3.45 product name, and the third statement of the download budget
e('R3E5', 'replace',
  "files, together with \\texttt{cp72\\_recurrence\\_v345.json} and the script that\nderives it. That block was declined during the survey by the per-target\ndownload budget of \\S\\ref{sec:sample}, at \\CpEbUnsearchedGB\\,GB against\n\\CpEbSearchedGB\\,GB for the block that was taken. Data products carry the",
  "files, together with \\texttt{cp72\\_recurrence.json} and the script that\nderives it. Data products carry the")

# ============================== OFFSETTING CUTS =============================

# R1-C1 (supersedes R3-E1): Appendix G carries the formula and the median
e('R1C1', 'replace',
  "spatial trials in the compact configurations where the symmetric\nreprocessing runs measure it, which is the worst case. On each window's own\narchived synthesised beam the annulus \\emph{contains}\n$N_{\\rm geom}=\\pi(r_{\\rm out}^{2}-r_{\\rm in}^{2})/1.133\\,\\theta_{\\rm beam}^{2}$\nresolution elements, median \\NeffMed{} and reaching\n\\NeffHi{} (Appendix~\\ref{app:falsealarm}). That counts what the annulus could support,\nnever what was drawn, so outside the most compact\nconfigurations the \\NCtrlCap{} controls are effectively independent and\n$N_{\\rm eff}\\rightarrow\\NCtrlCap$. The rank test needs exchangeability rather\nthan independence in any case, and correlation among controls costs resolution\nwithout touching the $1/\\RankFloor$ floor. The",
  "spatial trials in the compact configurations where the symmetric\nreprocessing runs measure it. That is the worst case, the annulus containing\nfar more resolution elements than the \\NCtrlCap{} positions drawn in all but\nthose configurations (Appendix~\\ref{app:falsealarm}). The rank test needs\nexchangeability rather than independence in any case, and correlation among\ncontrols costs resolution without touching the $1/\\RankFloor$ floor. The")

# R1-C2 = R3-E12: the caveat is six lines above in the same paragraph
e('R1C2', 'delete', " Neither benchmark implies a transmitter model.")

# R1-C5: the same interpretation is in the fig:cp72ctrl caption, which keeps it
e('R1C5', 'replace',
  "controls the first epoch topped, add-one $p=\\CpRecRankP$, and the largest\ncontrol reaches \\CpRecCtrlMax, so the annulus alone now throws an excursion\nbigger than the \\CpTwoTstar{} that raised the flag.",
  "controls the first epoch topped, add-one $p=\\CpRecRankP$.")

# R1-C6 = R2-E13: the channel width twice in two sentences
e('R1C6', 'replace',
  "It is Class~\\BpRecSixClass{} at\n\\BpRecSixChanwKHz\\,kHz, so the recurrence is demonstrated at the survey's\nfinest drift discrimination.",
  "It is Class~\\BpRecSixClass, so the recurrence is\ndemonstrated at the survey's finest drift discrimination.")

# R1-C7: contradicts Sec. 4.3 and Appendix G
e('R1C7', 'delete',
  " A signal drifting midway between\nadjacent trial rates accumulates at most 0.03 channels of residual drift\nacross the grid as realised, so no significant sensitivity is lost\nbetween them.")

# R1-C8: the kernel is named three lines above
e('R1C8', 'replace',
  "Under the $0.25/0.5/0.25$ kernel a\nsub-channel tone keeps",
  "A sub-channel tone keeps")

# R1-C9: filler clause
e('R1C9', 'delete', "\nand the interferometric mechanism is specific.")

# R2-E8: the survey-ranking aside
e('R2E8', 'replace',
  ", below HD~48370's\nCO($2{\\to}1$) ring at \\CtrlMaxSurveyMax{} and its $^{13}$CO ring at\n\\CtrlMaxSurveySecond.",
  ".")

# R2-E9: the blocks-versus-epochs preamble
e('R2E9', 'replace',
  "Bookkeeping first, since blocks and epochs are not the same thing: an\nobserving unit holds several execution blocks, the download budget of\n\\S\\ref{sec:sample} took one per unit, and blocks of one unit are not\nindependent epochs.",
  "Blocks of one observing unit are not independent epochs, and the download\nbudget of \\S\\ref{sec:sample} took one block per unit.")

# R2-E10 (R1-C4 declined: the two cuts justify each other, only one is taken)
e('R2E10', 'replace',
  "with the ring at the same level, which is a bright line\nfilling the beam.",
  "with the ring at the same level.")

# R3-E2: the closing summary restates the subsection and the Conclusions
e('R3E2', 'replace',
  "What carries the retirement is the matched-frequency, matched-drift null of\nthe second epoch, with the local null that never placed the feature near the\nBonferroni scale and the trials budget of the survey behind it. The pinned\ncriterion is met, so the flag is retired as a candidate on the balance of two\nindependent measurements.",
  "The pinned criterion is met, and the flag is retired as a candidate on the\nmatched-frequency, matched-drift null of the second epoch.")

# R3-E4: naming meta-commentary
e('R3E4', 'replace',
  "Turning it into a fraction of systems requires a per-system\ndetection probability, which is not a demographic occurrence rate. We\ncall it the \\emph{conditional searched-domain transmitter fraction}\nthroughout, never ``occurrence'' or ``transmitter fraction''\nunqualified, and keep its evaluation out of the interpretive argument:\nthe framework, the demonstration and its sensitivity analysis sit in\nAppendix~\\ref{app:population}, labelled \\emph{illustrative\ncalculation only} and among no headline quantity\n(Table~\\ref{tab:searchspace}). The result of this paper is the search\nsensitivity, the exposure and the null.",
  "Turning it into a fraction of systems requires a per-system detection\nprobability, which is not a demographic occurrence rate. We call it the\n\\emph{conditional searched-domain transmitter fraction} throughout, and its\nframework, demonstration and sensitivity analysis sit in\nAppendix~\\ref{app:population} as an \\emph{illustrative calculation only},\namong no headline quantity. The result of this paper is the search\nsensitivity, the exposure and the null.")

# R3-E6: two time figures determine the third
e('R3E6', 'replace',
  "\\CpRecUTtwo\\,UT with a \\CpRecGapMin-minute gap between them, so the second\nmeasurement is \\CpRecStartSepH\\,h after the first and the pair spans\n\\CpRecTotalSpanH\\,h. That makes the test strong",
  "\\CpRecUTtwo\\,UT, a \\CpRecGapMin-minute gap that puts the second measurement\n\\CpRecStartSepH\\,h after the first. That makes the test strong")

# R3-E7: Appendix A defines eta_smear in full
e('R3E7', 'replace',
  "The track is the right time-scale, the\nde-drift step accumulating coherently along it; $\\eta_{\\rm smear}$\n(Appendix~\\ref{app:conventions}) is the same ratio taken over one integration,\nand the two are not interchangeable.",
  "The track is the right time-scale, the de-drift step accumulating coherently\nalong it; $\\eta_{\\rm smear}$ (Appendix~\\ref{app:conventions}) is the same ratio\nover one integration.")

# R3-E9: the Introduction states what Sec. 4.1, the boxed rule and Sec. 4.4 state
e('R3E9', 'delete',
  " A continuous carrier is the best case and a short-duty\nfast-drifting emitter the worst, while coarse-channel windows retain\nsensitivity to persistent unresolved excess power alone.")

# R3-E10: the ancillary-analysis sentence
e('R3E10', 'replace',
  "No ancillary analysis carries a technosignature disposition. The\ncontinuum screen alone feeds an argument in the primary lane\n(\\S\\ref{sec:statistic}), and closure-phase vetting, the chirp and\nperiodicity re-analysis and the frequency-occupancy check are capability\ndemonstrations (\\S\\ref{sec:ancillary}).",
  "No ancillary analysis carries a technosignature disposition, the continuum\nscreen alone feeding an argument in the primary lane\n(\\S\\ref{sec:statistic}, \\S\\ref{sec:ancillary}).")

# R3-E11: the second priority disclaimer
e('R3E11', 'replace',
  "The three contributions listed in \\S\\ref{sec:intro} are new, to our\nknowledge, \\emph{in an ALMA archival technosignature survey}; the four further\ndiagnostics there gate nothing, and we claim no wider priority over their\ncentimetre-wave counterparts.",
  "The three contributions listed in \\S\\ref{sec:intro} are new, to our knowledge,\n\\emph{in an ALMA archival technosignature survey}.")

# R3-E13: the mosaic clause
e('R3E13', 'replace',
  "The star need not sit at\nthe pointing centre, since mosaics and wide pointings serendipitously cover\nmore than one catalogued star. Disc, planet and\nspectral type enter as descriptive metadata only.",
  "The star need not sit at the pointing centre. Disc, planet and\nspectral type enter as descriptive metadata only.")

# =================== FLOAT FONTS (R2-E11 = R1-C10 + R1-C11 + three more) ====
# R2-E11a (tab:nomenclature) is DECLINED: at \footnotesize the
# P(false flag) cell breaks with an underfull hbox (badness 1226), and the
# underfull gate is zero-tolerance.  Reverted after measuring; the page holds.
for tag, cap in (
        ('R2E11b', "\\caption{The statistical data path, in order."),
        ('R2E11c', "\\caption{The dwell campaign."),
        ('R2E11e', "\\caption{Amplitude completeness at the trigger, by window class and")):
    e(tag, 'replace', "\\small\n" + cap, "\\footnotesize\n" + cap)
e('R2E11d', 'replace',
  "\\small\n\\setlength{\\tabcolsep}{4pt}\n\\caption{Every window flagged by the original region-max",
  "\\footnotesize\n\\setlength{\\tabcolsep}{4pt}\n\\caption{Every window flagged by the original region-max")

# add the new macro file to the preamble
e('INPUT', 'replace',
  "\\input{survey_numbers_round16}",
  "\\input{survey_numbers_round16}\n\\input{survey_numbers_round17}")

ONLY = set(sys.argv[1:])
total = bad = 0
for tag, action, anchor, new in E:
    if ONLY and tag not in ONLY:
        continue
    n = src.count(anchor)
    if n != 1:
        print('!! %-10s anchor occurs %d times: %r' % (tag, n, anchor[:70]))
        bad += 1
        continue
    rep = '' if action == 'delete' else new
    total += len(rep) - len(anchor)
    print('%-10s %-8s %+6d' % (tag, action, len(rep) - len(anchor)))
    src = src.replace(anchor, rep)

print('edits: %d applied, %d failed | NET %+d source chars (%d -> %d)'
      % (len(E) - bad, bad, total, orig, len(src)))
if bad:
    print('NOTHING WRITTEN'); sys.exit(1)
io.open(TEX, 'w', encoding='utf-8').write(src)
print('written', TEX)
