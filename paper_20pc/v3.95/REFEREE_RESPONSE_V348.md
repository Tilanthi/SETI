# Response to referee cycle 5 — v3.47 → v3.48

**Outcome: 29 pages.** Main 20.61, back matter 1.03, appendices 6.81,
bibliography 0.31; content total 28.76. All gates zero (errors, undefined
references and citations, multiply-defined labels, overfull, underfull, Type 3
fonts). Abstract 1907 rendered characters against the 1920 arXiv limit.
593 macros defined, **0 unused**. Clean regeneration from an emptied folder
reproduces every generated `.tex` and the released catalogue byte-for-byte.
arXiv set 31 items, built in an empty directory: 29 pages, every gate zero,
0 missing files. Not pushed.

We are grateful to all three referees. The three reports agreed on the same
five defects independently, and two of them supplied edit sets they had
themselves applied to scratch copies and built. That made this the cheapest
cycle of the review so far: the merged set was applied mechanically
(`apply_v348_edits.py`, 45 edits, each anchor verified to occur exactly once),
and the work here was verification and conflict resolution rather than
re-derivation.

The page constraint that v3.47 missed is met. It was met **without deleting any
evidence on any must-not-cut list**: the recovery came from 1,425 source
characters of duplication that all three referees identified, plus four
non-evidence tables reset from `\small` to `\footnotesize`, which changes no
row, column or number.

---

## 1. The defect all three referees found: a width from the wrong window

**R1-N1 / R2-E1 / R3-E17 — accepted, fixed at the generator.**

`\BpWidthSixKms` = 2.26 km s⁻¹ is 114 crossings × 15.2588 kHz / 230.516128 GHz:
the **stage-1** Band 6 window's crossing count at the stage-1 window's channel
width. It was printed in the **recurrence** paragraph, whose window
(230.528134 GHz) has 244140.625 Hz channels and 32 and 28 channels above
threshold in `bpic_epochs_v347.json`, i.e. 10.16 and 8.89 km s⁻¹.

Verified from the released catalogue and the epoch product, then fixed where it
originates: `v347_calc.py` now emits `\BpWidthSixRecLo` 8.9 and
`\BpWidthSixRecHi` 10.2 from the recurring window's own two blocks. We adopted
referee 1's wording over referee 2's relabelling and referee 3's deletion,
because at 8.9–10.2 km s⁻¹ the two transitions agree with each other and with
$v_{\rm Kep}$ = 4.3 km s⁻¹ at 85 au (≈8.6 km s⁻¹ double-peaked for an edge-on
belt), so the corrected number strengthens the paragraph instead of removing
it. `\BpWidthSixKms` stays in use 1,200 lines earlier, where it is correct, and
now states a **floor** on the stage-1 feature's extent rather than a bound
(R1-E11).

**The cross-window audit the correction implies.** Every quantity printed in
the recurrence paragraph and in the stage-1 paragraph was traced to the product
it comes from:

| quantity | source | window |
|---|---|---|
| `BpRecSix{TList,RingList,NCtrlGe,ChanKHz,NChan,Flux*,TuneChanMax,Class}` | `bpic_epochs_v347.json['betPic_B6_CO21_mous2']` | recurring, 230.528134 |
| `BpRecSixRin/Rout`, `BpBeltArcsec`, `BpDistPc` | catalogue row at 230.528134 | recurring |
| `BeamBpicSixRec` 4.29″ | `archive_meta_v343.json`, EB `A002_X6f1341_X1484` | recurring |
| `BpWidthSixRecLo/Hi` | recurring blocks' own hits × own channel width | recurring (new) |
| `BpicBSixTsym` 11.68, `FluxBpicSix`, `BeamBpicSixFlag` 1.09″, `StelBpicSix`, `NCrossBpicSix` 114, `BpWidthSixKms` | catalogue row at 230.516128 | stage-1 |
| `BpFlagSixSecondEB/GB` | `archive_meta_v343.json`, MOUS `A001/X133d/Xbb5` | stage-1 |

**`\BpWidthSixKms` was the only crossing.** Two adjacent uses that look like
crossings are not: `\BpRecSixClass` is printed next to `\FobsBpicSixB`
(230.528134), which is the same window; and `\StelBpicCoarse` is selected in
`round10_calc.py` as the non-flagged β Pic Band 6 CO(2→1) row, which is the
recurring window — correct value, **stale macro name** ("Coarse": that window
is Class A / fine). The name is not printed; we flag it rather than churn the
generator.

---

## 2. Corrections accepted

| id | referee | what was wrong | what we verified |
|---|---|---|---|
| E2, E3 | R1 | the new edge-on-Keplerian passage claims narrow-at-the-star emission the window cannot see | `archive_meta_v343.json` gives EB `A002_X6f1341_X1484` a 4.29″ beam against a belt of radius 4.3″ (diameter 8.6″), and $r_{\rm in}$ = 3.82″ < 4.29″. The measured extent at the star is 8.9–10.2 km s⁻¹ — the whole double-peaked belt, contradicting the prediction three sentences later. Passage deleted; the localisation claim now carries the beam that made it. |
| E4 | R1 | $V_{\rm LSR}$ = +23.1 km s⁻¹ hand-typed, with no constants, and not reproducible | With $R_0$ = 8.15 kpc, $\Theta_0$ = 236 km s⁻¹, $l$ = 214.55°, $b$ = −3.19° we get **+23.18** at 2 kpc, not +23.1. Restated as referee 1 preferred: the flat curve reaches the measured +23.9 km s⁻¹ at a kinematic distance of **2.07 kpc** (bisection, residual < 10⁻⁶). Now generated, with $R_0$, $\Theta_0$ and the measured velocity single-sourced in `v348_calc.py`, so the printed velocity and the distance solved from it cannot diverge. This supersedes R2-E2 (which keeps a predicted velocity) and absorbs R2-E5. |
| E5 | R1 | a CO(2→1) mass limit "released with the catalogue" | Confirmed: the released catalogue has 41 columns, none of them a CO mass or an integrated-line limit. The claim is withdrawn and the number restored: $M_{\rm CO}$ < 1.6–2.4 × 10¹⁹ kg in optically thin LTE, from `\CoMassLo`/`\CoMassHi`, which `v344_calc.py` still emits. |
| E6 | R1 | the ring's own local-null $p$ had been deleted | Restored. The window's **ring** maximum has local-null $p$ = 3.0 × 10⁻³, only **1.9×** the star's — the most deflating number in the subsection, and on the must-not-cut list. The "every one of them" referent error is fixed with it ("all three"). |
| E13 | R1 | the striking half of a pair was kept and the deflating half cut | Restored: edge proximity is common across the survey, **32 of 490** recorded peak channels fall in the outer 3 per cent of their own window. |
| E7, E8, E9 | R1 | `≃` where only proportionality holds; the estimator's real part unstated | Accepted verbatim (three edits, +19 characters total). |
| E10 | R1 | the control seed is re-applied per window, which is what makes the two-epoch overlay legitimate | Accepted; the sentence now says so and points at Fig. 4. |
| E12 | R1 | "about 115 genuinely covered" is an upper bound | "at most about". |
| **E3** | **R2** | the astrophysical prior — the strongest argument in §5.3 — was asserted, not measured | **Re-ran the obscore query ourselves** over all 102 execution blocks of the released catalogue (`SELECT DISTINCT asdm_uid, scientific_category, science_keyword FROM ivoa.obscore`, ALMA TAP, 102 of 102 matched). **79 of the 88 stars** have at least one *Disks and planet formation* block; **73** carry the *Debris disks* keyword; **67 of the 81 systems**. The nine exceptions are exactly the nine referee 2 lists. Category census: 93 blocks *Disks and planet formation*, 7 *Stars and stellar evolution*, 2 *ISM and star formation*. The harvest is frozen as `obscore_category_v348.json` and the three integers are emitted by `v348_calc.py`, **not hand-typed**, as referee 2 required. |
| E4 | R2 | a non-detection bounds rather than forbids | Accepted: "excludes the circumstellar alternative to their sensitivity". |
| E6 | R2 | the `tab:flagged` caption promised that no disposition rests on a single test, which the CP−72 retirement contradicts | Deleted. |
| E14 | R3 | Table 4 still read "168" unqualified | Row added: genuinely pointed at 115; never observed 53, from existing macros, with the §5.2 pointer. |
| E15 | R3 | "∼1 per cent" rests on the uncorrected 168 | Now "≲1 per cent, and fewer once §5.2 removes those never in fact observed". |
| E16 | R3 | "crossing" is counted per window in the main text and per cell in the appendices | Nomenclature table now says so. |
| E18 | R3 | a median of observed maxima compared with a Gumbel expectation, unlabelled | Labelled. |
| E5 | R3 | Data Availability named `cp72_recurrence_v345.json` in a v3.47 paper | Fixed, and **the file itself renamed** to `cp72_recurrence.json` in the folder with every generator repointed, so the manuscript's statement is now true of the shipped product rather than true of a rename. |

---

## 3. Conflicts between the reports, and how each was resolved

1. **The β Pic Band 6 width** (R1-E1 vs R2-E1 vs R3-E17). Took R1: fix the
   number at the generator. R2 relabels the sentence to name the stage-1
   window, R3 deletes the Band 6 clause; both leave the paper without the
   comparison that makes the width argument work.
2. **The Galactic-rotation check** (R1-E4 vs R2-E2 + R2-E5). Took R1's
   kinematic distance. R1's anchor contains R2's two anchors, so this is one
   edit, not three; R2's +23.2 with constants would also have been defensible,
   but a distance is checkable and a coincidence is not.
3. **The ring/edge-on passage** (R1-E2 + R1-E3 vs R2-E7 vs R3-E3). Merged R2-E7
   (drop the "physical answer and not a statistical one" antithesis) with
   R1-E2 (delete the unsupported kinematics) and R1-E3 (add the beam
   qualifier). R3-E3 saves 35 characters more but keeps no beam qualifier, and
   referee 1 showed that the localisation claim needs one.
4. **$N_{\rm geom}$ in §4.1** (R1-C1 vs R3-E1). Took R1-C1 (−298 vs −138): it
   also repairs the dangling "which is the worst case". Appendix G carries the
   formula, the median and the interpretation, and `\NeffMed`/`\NeffHi` remain
   used there, so nothing is orphaned.
5. **The filled-beam mechanism in the HD 48370 paragraph** (R1-C4 vs R2-E10).
   These two cuts *justify each other* — each referee points at the other's
   sentence as the surviving statement. Applying both would delete the
   mechanism from the paragraph. We took R2-E10 (the decorative clause) and
   **declined R1-C4**, keeping the sentence that interprets the one-per-cent
   margin.
6. **Duplicates applied once**: R1-C2 = R3-E12 (the transmitter-model caveat),
   R1-C6 = R2-E13 (the channel width given twice), R1-C10/C11 ⊂ R2-E11 (float
   fonts). Nothing was double-applied; the merged set applies each anchor once
   and refuses to run if any anchor is not unique.

### Declined, with reasons

- **R1-C3** (compress the primary-beam-settled argument in §5.3.1, −180).
  Referee 2 asked in the same round for that sentence to be kept **exactly as
  written** — "the cleanest statement of that point the paper has had". The
  page closed without it.
- **R1-C4**: see conflict 5 above.
- **R3-E8** (replace the measured ring ratio with a cross-reference, −23).
  Referee 1 lists the ring-outshines-star result *and its place in the
  exchangeability-violation list* as must-not-cut, because it is the only
  violation that actually operates in a debris-disc archive and it is measured.
  23 characters is not worth converting a measurement into a pointer.
- **R2-E11a** (`tab:nomenclature` to `\footnotesize`). Applied, measured,
  **reverted**: at `\footnotesize` the $P(\text{false flag})$ cell breaks with
  an underfull hbox of badness 1226, and the underfull gate is zero-tolerance.
  The other four non-evidence tables took the change cleanly and the page still
  closed. This is the kind of thing only a build can tell you.
- **R2-E12** (the two evidence tables to `\footnotesize`): held in reserve and
  not needed — the paper is 29 pages without it.
- **R1 minor 5** (the abstract says the ceiling "does not cover" TRAPPIST-1 b
  while §4.3 says it "sits at" it, `\OrbAccTrapb` = 4.00 against a 3.60–4.00
  ceiling). Referee 1 advised not spending characters; the abstract is at
  1907/1920 and we agree, but it is a real inconsistency and it is recorded
  here for the author.
- **R1 minors 2–4** are generator hygiene, not manuscript text: the UV Ceti
  worked example selects the A+B pair (`\NUVCetiWin` = 8) while quoting B's
  distance and EIRP; `\PlxWorstPct`, `\NPlxOverEight` and `\PlxAdqlPct` are
  hard-coded strings whose values are right but whose provenance is not; and
  `NPlxOverEight` now counts entries above *one* per cent. None changes a
  printed digit. Left for the author.

---

## 4. A correction to our own previous response letter

The v3.47 letter reported that §5.3.5 fell from 11,372 to 8,226 characters.
Referee 3 recounted it and found that the two figures are taken at **different
subsection boundaries**. Like for like, §5.3.5 **grew by about 6 per cent**
between v3.46 and v3.47, while the CP−72 argument inside it fell by about
13 per cent. The growth is legitimate — it is the β Pic recurrence control,
which referee 2 asked for and which is new evidence — but the sentence as
written was wrong, and we would rather correct it than repeat it. We have not
quoted a subsection character count in this letter for the same reason: the
measurement that matters is the page split, which is reported at the top.

---

## 5. Verification performed, edit by edit

- **Anchors.** All 45 edits verified to occur exactly once in the v3.47 source
  before any was applied; the script writes nothing if any anchor is ambiguous
  (it caught one anchor whose trailing blank line the report had added, R3-E9).
  Net −1,425 source characters.
- **Numbers.** Every number introduced is generated: `\BpWidthSixRecLo/Hi`
  (`v347_calc.py`, from the recurring blocks), `\RzeroKpc`, `\ThetaZeroKms`,
  `\VlsrHdLsr`, `\KinDistKpc`, `\NDiskCatStars`, `\NDebrisKwStars`,
  `\NDebrisKwSys` (`v348_calc.py`, new, wired into `make_all.sh` before
  `retire_macros.py`). The restored macros (`\CoMassLo/Hi`, `\LNpCPRing`,
  `\LNCPRingRatio`, `\NPeakOuterThree`, `\NPeakRows`, `\BeamBpicSixRec`) came
  back through their own generators, not by hand.
- **Rendered text.** Each corrected passage was read back out of the PDF, not
  the source: 8.9–10.2 km s⁻¹; 2.07 kpc; 79/73/67; $M_{\rm CO}$ < 1.6–2.4 ×
  10¹⁹ kg; $p$ = 3.0 × 10⁻³, 1.9×; 32 of 490; 4.29-arcsec; "at most about 115";
  "115; 53" in Table 4; "≲1 per cent"; `cp72_recurrence.json`.
- **Cut sites.** Every deletion site was re-read for dangling text
  (`tab:flagged`'s caption, the Hanning kernel sentence, the drift-grid
  paragraph, the Introduction).
- **Table 5 spot-check.** The four hand-typed `tab:flagged` rows were checked
  against the released catalogue: 14.65/7.27, 11.68/9.12, 27.10/26.83,
  5.81/5.68 — all exact. They remain hand-typed, which is a standing
  single-sourcing violation in that table and in `tab:bothstats`; flagged, not
  fixed, because fixing it means a generator change no referee asked for.
- **Gates.** `gate.sh`, `pagesplit.py`, `abstract_limit.py`, `macrosweep.py`
  (0 unused of 593), `prosecount.py` (em-dashes **0**; main-text antithesis
  constructions 22, down from 41 at v3.45).
- **Clean regeneration.** A copy of the folder with every generated `.tex`,
  `tables/`, `figures/*.pdf`, the released catalogue and the build artefacts
  deleted was rebuilt by `make_all.sh` alone: all generated `.tex` and the
  catalogue came back **byte-identical**, and the rebuilt copy builds to 29
  pages with every gate zero. Figures differ only in their embedded creation
  timestamps.
- **arXiv set.** `arxivset.sh` into an empty directory: 31 items (24
  tex/cls/sty + 7 figures — one more than v3.47, the new
  `survey_numbers_round17.tex`), 29 pages, 0 errors, 0 undefined, 0
  multiply-defined, 0 overfull, 0 underfull, 0 Type 3, 0 missing files.

---

## 6. Open for the author

1. **The abstract/§4.3 TRAPPIST-1 b wording** (above). One word, 13 characters
   of headroom.
2. **`\StelBpicCoarse`** is correctly valued and misleadingly named.
3. **Hand-typed numbers in `tab:flagged` and `tab:bothstats`**, all verified
   correct today, none single-sourced.
4. **`\NUVCetiWin` and the parallax macros** (R1 minors 2–4).
5. The paper is **29 pages and not pushed**, per the brief.
