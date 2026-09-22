# BUILD NOTES — v3.93: the prospective epoch extension

Glenn's instruction (2026-09-22): bring in all the newly downloaded and
analysed data and make every figure, table and number current.

## Gates

| gate | value |
|---|---|
| pages | 47 (main 29 / appendices 18) |
| LaTeX errors | 0 |
| undefined references / citations | 0 |
| multiply-defined labels | 0 |
| overfull boxes | 0 |
| Type 3 fonts | 0 |
| underfull boxes | 29 (narrow two-column measure) |
| macros defined / unused | 1149 / 0 |
| abstract | **1912 rendered characters** (arXiv limit 1920, both counters) |
| clean regeneration | **90/90 byte-identical, incl. 16/16 figures** |
| number audit | 49 pass, 0 fail |
| catalogue self-sufficiency | 36 pass, 0 fail |
| round-file ownership | 46/46, 0 collisions |
| cross-reference resolution | 0 misplaced labels |
| arXiv set | 87 items |
| em-dashes / antithesis | 68 / 188 (v3.87: 67 / 184) |

## The central decision: the new data is NOT merged into the science sample

123 public, in-scope execution blocks were searched that the frozen survey
never had. They existed because `make_worklist.py` was built against the
v3.43-era archive map (102 member OUS, 448 progenitors); the v3.81 map
(152 OUS, 656 progenitors) exposed them. They were searched with the
frozen pipeline **after** the detection statistic and the molecular-line
mask were fixed.

That ordering is their value, and merging would destroy it. Every
statistic in this paper rests on a denominator and a candidate list fixed
before the data were examined. So the frozen sample is **unchanged**, and
the new data is reported as a prospective extension (new
`\S`\,*A prospective epoch extension*, `sec:extension`) with its own null
and its own released file.

Anyone who wants to pool them can; the Data Availability statement says so
explicitly, and says why we do not.

## The extension, as measured

115 blocks, 463 windows (67 Class A), 16 stars, 16 systems, 57.6 GHz of
frequency (13.2 GHz Class A). Snapshot 2026-09-22 08:18 UTC.

**The survey's own withholding rule was applied, not bypassed.** All 32
eps Eri windows in the campaign are Band 6, where the star sits near 0.7
primary-beam FWHM and the Gaussian beam form used for the correction does
not hold (`survey_stats.py:40`). They are withheld, exactly as in the
frozen sample, and the count is printed.

### Three results

1. **The departure from exchangeability reproduces on unseen data.**
   Median add-one rank **0.409** over 463 prospectively searched windows
   where 0.5 is expected, $D=0.116$, $p<0.01$. That is a *third*
   independent measurement of the effect §5.3.2 and §5.3.3 report
   (hold-out 0.429, radius analysis 0.437), and it is the strongest
   support the paper has for using the spatial rank as a screen and never
   as a significance.
2. **The positive control recovers.** 3 windows reach stage 1 and all 3
   are the β Pictoris disc in CO(1–0), at $T_\star = 23.17$, 19.82 and
   19.39 against ring maxima below 6.21, within 8.8–9.0 MHz of the
   transition, **in three different previously unsearched execution
   blocks**.
3. **No new unattributed event.** 13 threshold crossings (2.81 % of
   windows), 4 rank-first against 1.3 expected, and **0 unattributed
   stage-1 events** against 0.21 expected on the 78 windows whose control
   maximum reaches the trigger. The paper's count of unattributed events
   therefore remains 4.

### The epoch gain is small, and the paper says so

Systems with more than one searched epoch: **55 → 56** of 82. Systems with
a single epoch: **27 → 26**. One system acquires a second epoch. This
matches the prediction §6.4 item (2) made before the campaign ran, and it
is reported as confirmation of that prediction rather than buried.

## What changed in the manuscript

* New `sec:extension` in §5.3 with the three results above.
* New generated `tab:extension` comparing the frozen sample and the
  extension **like for like** — every frozen-column number is recomputed
  from the released catalogue by the same definition applied to the
  extension, and the generator cross-asserts them against `NStageOneWin`,
  `NStageOneLine` and `NStageOneUnattrib`.
* Abstract: one sentence on the prospective extension, paid for by
  trimming ten other phrases. Both the source-side and PDF-side counters
  pass (1905 / 1912 of 1920).
* §5.3.2: the exchangeability displacement now cites its third measurement.
* §6.4 item (2): "this recommendation has since been acted on in part",
  with the measured epoch gain.
* Conclusions: the prospective test, and that it leaves the unattributed
  count at 4.
* Data Availability: `export_extension.json` released separately, with the
  reason it is not merged.

## New files

| file | purpose |
|---|---|
| `extension_v393.py` | the extension's coverage, null, positive control → round 50 + `tab_extension_v393.tex` |
| `export_extension.json` | 495 window records in the frozen-export schema, full 512-element control vector each |

## Traps hit this round

* **The rename `v387` → `v393` left `tab_falsealarm_v387.tex` orphaned.**
  It still satisfied the build (the file existed) but nothing regenerated
  it, so the **clean-regeneration test was the only thing that caught it**
  — 90/91 with one MISSING. Same lesson as v3.60's `make_all.sh` omissions:
  a renamed generator needs its output name changed too, and only the
  clean regen sees it.
* **Two abstract counters disagreed again.** `abstract_limit.py` said 1917
  (OK) while `abschars.py` read 1926 from the PDF. The PDF is what arXiv
  sees. Trimmed until both pass, as the v3.49 lesson requires.
* **`\num{}` is not available** — siunitx is not loaded in this class.
* **A macro used twice for two different quantities.** My first
  `tab:extension` put `\NStageOneWin` in the frozen column for both
  "rank-first windows" and "stage-1 events". Fixed by computing every
  frozen number from the catalogue and asserting against the published
  macros.
* **eps Eri is not in the catalogue at all**, because the survey withholds
  it. The name-matching step flagged it as unmatched rather than silently
  dropping it, which is how the withholding rule came to be applied
  instead of forgotten.

## Campaign state at this snapshot

121 of 174 unique blocks searched at the time of export; the campaign is
still running and the remaining large blocks will be a later increment.
13 blocks have no archive calibration, 11 fail the legacy Cycle 0/1
`scriptForCalibration` replay, and 1 is infeasible on this host — **all
three classes closed by author decision (see the runbook), so the
reachable population is about 149 of 174.** Any future coverage statement
must use that denominator.
