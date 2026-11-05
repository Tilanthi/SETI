#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""v3.49 abstract cuts: the arXiv character limit, honestly measured.

WHY THIS EXISTS.  `abstract_limit.py` stripped every control sequence to a
space, so the VALUES of the twenty generated macros the abstract cites were
never counted.  It reported 1907 of 1920 for v3.48 while the typeset abstract
(`abschars.py`, read from the PDF) was 1975, and the corrected counter makes
the same source 1971.  The abstract had been over arXiv's hard limit since at
least v3.45 and would have been refused at submission ("abstracts longer than
1920 characters will not be accepted", info.arxiv.org/help/prep.html); five
referee reports quoted the broken gate.

WHAT IS CUT.  Duplication only, as the page constraint was closed at v3.48.
No evidence, no self-criticism, no number that appears nowhere else.

  A1  "meeting our public-archive coverage criteria" -> "with public-archive
      coverage".  Same fact; the criteria are defined in Sec. 3, to which the
      sentence already points.                                    -16 source
  A5  the 1 MW / 12 m / 230 GHz benchmark, which Sec. 4.2 already states
      ("a 12-m aperture radiating 1 MW at 230 GHz, EIRP ...").     -78 source

  Result: 1895 counted from the source, 1905 from the PDF, 29 pages, every
  gate zero.

WHAT WAS MEASURED AND REVERTED.  Three further cuts were applied, built and
reverted, because a SHORTER abstract pulls one more line of Sec. 1 onto the
title page, where the fixed affiliation footnote block leaves no room for it:

  A2  "Only \\NWinA{} of \\NWindows{} windows discriminate drift; the rest
      search for unresolved spectral excess." -> "The coarse windows search for
      unresolved spectral excess instead."                         -39
  A3  "the pinned recurrence criterion" -> "the pinned criterion"   -11
  A4  "The completeness measured" -> "Completeness measured"         -4

  With all five, the abstract is 1854/1864 but the build reports
  `Overfull \\vbox (1.38652pt too high) ... while \\output is active` on page 1.
  Sweeping the abstract length shows the page-1 residual is quantised by line:
  -60, -30 and +20 characters about that point all give 0.31 pt, and only at
  about +40 does it reach zero.  A1+A5 alone sits in the clean band.
  (Same trap family as v3.48's `tab:nomenclature` font change: a length change
  is free in characters and not free in gates.  Measure, do not assume.)

  If more arXiv headroom is ever wanted, A2--A4 are worth 54 rendered
  characters together and the wording is above; they must be re-measured
  against the page-1 vbox, and the three of them together may need a fourth
  cut to re-enter the clean band.
"""
import io, sys

TEX = 'technosignatures_20pc_v3.50.tex'
src = io.open(TEX, encoding='utf-8').read()
orig = len(src)
E = []


def e(tag, anchor, new=''):
    E.append((tag, anchor, new))


e('A1',
  "The sample is every star within 40\\,pc meeting our public-archive\n"
  "coverage criteria: complete in targets and tunings, not in epochs\n"
  "(\\S\\ref{sec:sample}).",
  "The sample is every star within 40\\,pc with public-archive coverage:\n"
  "complete in targets and tunings, not in epochs (\\S\\ref{sec:sample}).")

e('A5',
  ", against\n1\\,MW on a 12\\,m aperture at 230\\,GHz (${\\approx}8\\times10^{14}$\\,W). A sub-channel carrier makes them optimistic by",
  ". A sub-channel carrier makes them optimistic by")

total = bad = applied = 0
for tag, anchor, new in E:
    n = src.count(anchor)
    if n != 1:
        print('!! %-4s anchor occurs %d times: %r' % (tag, n, anchor[:70]))
        bad += 1
        continue
    total += len(new) - len(anchor)
    applied += 1
    print('%-4s %+6d' % (tag, len(new) - len(anchor)))
    src = src.replace(anchor, new)

print('abstract edits: %d applied, %d failed | NET %+d source chars (%d -> %d)'
      % (applied, bad, total, orig, len(src)))
if bad:
    print('NOTHING WRITTEN'); sys.exit(1)
io.open(TEX, 'w', encoding='utf-8').write(src)
print('written', TEX)
