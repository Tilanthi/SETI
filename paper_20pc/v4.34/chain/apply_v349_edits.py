#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Merged v3.49 edit set: referees 1, 2 and 3 (final round), conflicts resolved.

Every anchor is verbatim from technosignatures_20pc_v3.48.tex (= the v3.49 file
before this script runs) and must occur exactly once.  Run once; it is not
idempotent.  Nothing is written unless every anchor is unique.  The source of
each edit is named in the tag.

Generator-level edits are NOT in this script (they belong to make_all.sh):
  R1-E3  v347_calc.py  l.203   select G 272-61B only          (NUVCetiWin 8 -> 4)
  R3-E4  v342_calc.py  l.466   HanFacWorst '%.1f' -> '%.2f'   (2.7 -> 2.67)
  R3-E5  prosecount.py         join body lines with ' '       (gate hygiene)
  R3-E6  apply_v348_edits.py   NSys -> NSystems               (audit trail)
"""
import io, sys

TEX = 'technosignatures_20pc_v3.50.tex'
src = io.open(TEX, encoding='utf-8').read()
orig = len(src)
E = []


def e(tag, action, anchor, new=''):
    E.append((tag, action, anchor, new))


# ============================ PRINTED DEFECTS ===============================

# R3-E1: the second optional argument of \citep is a POST-NOTE and it prints.
# Page 2 of the v3.48 PDF reads "(White 2026, citation provisional)".  The
# bibliography already carries the honest flag ("MNRAS, submitted").
e('R3E1', 'replace',
  "Our pilot \\citep[][citation provisional]{White2026} extended that",
  "Our pilot \\citep{White2026} extended that")

# R1-E1: repair the comma splice left by v3.48's C9 (the deleted clause carried
# the sentence's full stop).  Rendered in the PDF as
# "does not cancel, Smooth emission lives on short baselines".
e('R1E1', 'replace',
  "position. Extended sky brightness does not cancel,\nSmooth emission",
  "position. Extended sky brightness does not cancel.\nSmooth emission")

# ======================== PHYSICS AND CITED LITERATURE ======================

# R2-E1: the measured quantity is flux density per beam per channel, for which
# the optically thin LTE ratio is (A21/A10)(g2/g1)exp(-11.07/T) = 9.2 at 20 K,
# 16.0 as T -> infinity, NOT 4 (which is the brightness-temperature value, and
# coincidentally the optically thick Rayleigh-Jeans one).  And Matra et al.
# (2017) report T_exc = 12 +- 4 K: subthermal excitation is their headline
# result, so "only mildly subthermal" inverted the cited paper and the
# inference drawn from it was unsupported.
e('R2E1', 'replace',
  "spatially integrated CO though below the optically thin LTE ratio\n"
  "($\\simeq4$). Excitation cannot account for a deficit that size, since\n"
  "\\citet{Matra2017} find this gas only mildly subthermal\n"
  "(CO $3{-}2/2{-}1=1.9\\pm0.3$ against 2.25 in LTE); beam dilution and\n"
  "resolved-out flux can, the synthesised beams being\n"
  "\\BeamBpicThree{} and \\BeamBpicSixFlag\\,arcsec; and since both channels are far",
  "spatially integrated CO. They are per-beam peaks, the synthesised beams being\n"
  "\\BeamBpicThree{} and \\BeamBpicSixFlag\\,arcsec on emission resolved in both, and\n"
  "\\citet{Matra2017} find the gas subthermally excited ($T_{\\rm exc}=12\\pm4$\\,K),\n"
  "so beam dilution and excitation both depress the ratio below optically thin\n"
  "LTE; and since both channels are far")

# R2-E2: Matra et al. (2017) take v_sys as an INPUT -- "the velocity of the star
# (20.0 +- 0.7 km/s in the heliocentric reference frame, Gontcharov 2006)" --
# and derive no systemic velocity from the gas.  The adoption is unchanged.
e('R2E2', 'replace',
  "we adopt the gas-derived\n$v_{\\rm sys}=\\VsysBpic\\pm\\VsysBpicErr$\\,km\\,s$^{-1}$ of\n\\citet{Matra2017}",
  "we adopt the\n$v_{\\rm sys}=\\VsysBpic\\pm\\VsysBpicErr$\\,km\\,s$^{-1}$ used by\n\\citet{Matra2017}")

# R2-E3: the 1.6-2.4 range is not an uncertainty, it is T_ex = 20 and 50 K
# (v344_calc.py l.229-236).  Both macros already exist; they were retired only
# because nothing cited them, so this edit restores them automatically.
e('R2E3', 'replace',
  "$M_{\\rm CO}<\\CoMassLo$--$\\CoMassHi\\times10^{19}$\\,kg in optically thin LTE.",
  "$M_{\\rm CO}<\\CoMassLo$--$\\CoMassHi\\times10^{19}$\\,kg in optically thin LTE at\n"
  "$T_{\\rm ex}=\\CoTempLo$--$\\CoTempHi$\\,K.")

# ============================ PROVENANCE ====================================

# R1-E4: the unsearched second block was declined by spectral-window
# de-duplication, not by the per-target download budget.  All 102 observing
# units have exactly one searched block of 448 progenitors, which a 3-block cap
# cannot produce; and CP-72 2713 was searched in two blocks in total, below
# that cap, so the cap cannot be what declined this one.  Stated twice.
e('R1E4a', 'replace',
  "\\texttt{\\CpEbUnsearched}, which the per-target\ndownload budget of \\S\\ref{sec:sample} declined.",
  "\\texttt{\\CpEbUnsearched}, which the\nde-duplication of \\S\\ref{sec:sample} declined.")
e('R1E4b', 'replace',
  "not independent epochs, and the download\nbudget of \\S\\ref{sec:sample} took one block per unit.",
  "not independent epochs, and the\nde-duplication of \\S\\ref{sec:sample} took one block per unit.")

# PA-1: the released catalogue is renamed with the manuscript at every version
# bump; the Data Availability statement names the file.
e('PA1', 'replace',
  "\\texttt{per\\_target\\_results\\_v3.48.csv}",
  "\\texttt{per\\_target\\_results\\_v3.49.csv}")

# ========================== CONSISTENCY =====================================

# R1-E2 (supersedes R3-E2, which reworded to "reaches" instead of taking
# Sec. 4.3's own "sits at it"): one statement about TRAPPIST-1 b.
# \OrbAccTrapb = 4.00 m s^-2 against a ceiling of 3.60-4.00 m s^-2, so the
# planet sits at the top of the range: covered by the best windows, outside the
# rest.  "Does not cover" was the only one of the four sites not defensible.
e('R1E2', 'replace',
  "polarisation-blind, and the drift ceiling does not cover\nTRAPPIST-1\\,b, the only sample planet to reach it.",
  "polarisation-blind, and TRAPPIST-1\\,b, the only sample planet to reach\nthe drift ceiling, sits at it.")

# R3-E3: the fourth site.  "Exceeding" is false for the best windows.
e('R3E3', 'replace',
  "the case exceeding the drift ceiling;",
  "the case that reaches the drift ceiling;")

# R1-E5: single-source the LSR velocity of the HD 48370 foreground feature, so
# a future change to the LSR chain cannot leave the two sites disagreeing.
# \VlsrHdLsr = 23.9 is printed in Sec. 5.3.4 with the radial-velocity sign.
e('R1E5', 'replace',
  "at $-23.9$\\,km\\,s$^{-1}$, which is the frame",
  "at $-\\VlsrHdLsr$\\,km\\,s$^{-1}$, which is the frame")

# R1-E6: "inside the beam and star and annulus rise together" reads as a
# three-item list until the verb arrives.  Pre-existing.
e('R1E6', 'replace',
  "nearly position-independent inside the beam and star and annulus rise",
  "nearly position-independent inside the beam, and star and annulus rise")

ONLY = set(sys.argv[1:])
total = bad = applied = 0
for tag, action, anchor, new in E:
    if ONLY and tag not in ONLY:
        continue
    n = src.count(anchor)
    if n != 1:
        print('!! %-8s anchor occurs %d times: %r' % (tag, n, anchor[:70]))
        bad += 1
        continue
    rep = '' if action == 'delete' else new
    total += len(rep) - len(anchor)
    applied += 1
    print('%-8s %-8s %+6d' % (tag, action, len(rep) - len(anchor)))
    src = src.replace(anchor, rep)

print('edits: %d applied, %d failed | NET %+d source chars (%d -> %d)'
      % (applied, bad, total, orig, len(src)))
if bad:
    print('NOTHING WRITTEN'); sys.exit(1)
io.open(TEX, 'w', encoding='utf-8').write(src)
print('written', TEX)
