# BUILD_NOTES — v3.41 (round 11: referee round + trim)

Baseline: `technosignatures_20pc_v3.41.tex` as received = v3.40 content
(226,360 bytes, 4,157 lines, 39 pages). v3.40 and earlier folders untouched.

**Round 11 is a referee round with a trim mandate.** It answers three
independent reports on v3.40 (`/shared/ASTRA/reviews/`), fixes five
independently verified production defects, and reduces the paper's length.
Point-by-point response: `REFEREE_RESPONSE_ROUND10.md`.

---

## 1. Result — build gates

| gate | v3.40 | v3.41 | note |
|---|---|---|---|
| pages | 39 | **36** | standing ceiling 38; editor's target band 34–36 |
| LaTeX errors | 0 | **0** | |
| undefined refs / cites | 0 | **0** | |
| multiply-defined labels | 0 | **0** | |
| overfull hboxes | 0 | **0** | |
| underfull hboxes | **10** (gate reported 0) | **0** | see §5 |
| overfull `\vbox` | 0 | **1** (1.57 pt) | see §5 |
| Type 3 fonts | **3** (gate reported 0) | **3** | inherited defect, see §4 |
| appendices | 17 | **14** | |
| `\includegraphics` calls | 14 | **11** | three duplicate figures deleted |

Build = `pdflatex -interaction=nonstopmode` ×3. The `.bbl` is inline
(`thebibliography`); bibtex is not run. `./gate.sh` runs the build and prints
every gate above plus the character budget.

---

## 2. Trim accounting

Measured on the `.tex` source, split at `\appendix` and at
`\begin{thebibliography}` (`measure.py`).

| region | v3.40 (chars) | v3.41 (chars) | net | mandate |
|---|---|---|---|---|
| main text + front matter | 153,938 | **148,763** | **−5,175 (−3.4 %)** | −10 % (−15,400) |
| appendices | 68,724 | **60,364** | **−8,360 (−12.2 %)** | −25 % (−17,250) |
| bibliography | 3,697 | 3,713 | +16 | — |
| **total** | 226,359 | **212,840** | **−13,519 (−6.0 %)** | |
| **pages** | **39** | **36** | **−3** | 34–36 |

**The page target is met; the character targets are not, and the shortfall is
real.** The honest accounting is gross, not net: roughly **11.4 kB was cut from
the main text and 12.9 kB from the appendices** (≈ −7.4 % and ≈ −18.7 %), and
about **10.7 kB was added back** as referee-required scientific content. The
additions, with sizes:

| addition | region | chars | driver |
|---|---|---|---|
| Hanning / spectral-response paragraph + withdrawal of the old check | App. C | ~1,870 | R1-M1 |
| "Four gaps in the frozen mask" ([C I], H30α, LSR frame, 1-MHz rounding) | App. I | ~1,680 | R2-M5/M6 |
| CP−72 2713 astrophysical context + CO non-detection | §5.3 | ~950 | R2-M3 |
| HD 48370 corroborations (flux, ¹³CO ring, [C I] window) | §5.3 | ~840 | R2-M11, R2-M6 |
| control-ring geometry: reproducibility gap + conditional bound | §4.1, §5.3 | ~875 | R1-M3 |
| exchangeability / N_eff caveats | §5.3 | ~580 | R1-M9 |
| disclosure of three released-table defects | Data Avail. | ~600 | R2-m8/m9/m12, §3(i) |
| Table 7 rebuild (S_peak column, ν_cross, caption) | §5.3 | ~595 | A4, R2-M1 |
| β Pic flux ratio + crossing multiplicity | §5.3 | ~530 | R2-M1 |
| R2-M10 correction paragraph (q range 0.33–96×) | §5.2 | ~385 | R2-M10 |
| smaller items (ν² benchmark, T_eff proxy caveat, τ Cet, ratios) | various | ~800 | R2-M8/M9, R1-M10 |

Every addition is a caveat, a correction or a disposition-strengthening
measurement; none is padding, and each was paid for by a cut elsewhere in the
same round. Reaching the full −10 %/−25 % *net* would have required cutting a
further ~21 kB, which on this paper's figure/table density projects to ~32
pages — below the editor's own 34-page floor. We stopped at the page band and
recorded the character shortfall rather than making the two targets agree by
cutting protected material.

### What was cut (the referees' convergent list)

**Deleted outright:** the spliced duplicate Background paragraph (defect A1);
the "trials chain, start to finish" box; the "Reading rule" box and the
inference-status box (folded into running text); Appendix L (serendipitous
molecular-line catalogue — content already in §5.5); Appendix M (lessons for
archival pipelines); Appendix N's "symmetric star-versus-control null in full"
subsection; seven glossary rows duplicated in Table 1; Fig. 11 (`symcdf`,
duplicate of Fig. 6) and Fig. 14 (`aumic_control_maxima`, 0.29 columnwidth,
one number already in the text); Fig. 9 (`eirp_vs_distance`, the same plot as
Fig. 1a); Appendix Q's "Which number is which" and "Series-level error control";
the uncited `BLMeerKAT2026` and `BLoverview` bibliography entries; duplicated
`make_tables_v328.py` banner lines.

**Merged:** Appendices E (closure phase) and F (chirp/periodicity) into one
*"Demonstrated diagnostics with no operative role in this release"*.

**Compressed:** §2 (fold and de-duplicate); §4.3 (heading removed, benchmark
folded); §4.6 (heading removed); the false-alarm components (i)–(ii); the
primary-beam azimuthal-gain analysis; §4.5's overlapping "three distinctions"
and "what this licenses"; §5.2's forensics; the line-exclusion definition/cost/
limits block (sensitivity ladder to one sentence, "two standing policies" and
the line-coincident-catalogue paragraph to pointers); the obscore availability
audit; §6.2's haystack and drift-ceiling restatements; the Conclusions;
Appendix Q's independence and transfer-error paragraphs; Appendix D's
criterion-artefact narrative; Appendix H's EIRP re-derivation; Appendix O's
method; Appendix P's retired-statistic diagnostics and defect forensics;
Appendix C's 1-Hz comparison and sub-channel restatement; the seven longest
captions (Fig. 1 1,061→~700, Fig. 4 1,244→~900, Table 12, Fig. 7, Fig. 8,
Fig. 13, Table 9 all capped).

**The 0-of-500 artefact is now told once in full** (Appendix D) with one
sentence in §4.4 and one Table 21 row, per all three referees.

---

## 3. Generator changes (single-source rule)

No survey quantity was hand-typed. Three generators changed:

* **`survey_stats_round10.py`** — the occurrence loop now also evaluates
  P = 3×10¹³ and 10¹⁴ and the duty grid p_epoch = 0.1 and 0.01, so the whole of
  Table `tab:occurrence` can be generated. Nothing else changed; it still
  reproduces 431/88/82/118/313, union 93.113 GHz, and every published value.
* **`round9_calc.py`** — the literal `GROSS_BW = 700.8` is replaced by a sum
  over the same frozen rows as everything else (716.654 GHz). This also moves
  `\MaskGrossPct` 3.2 → **3.1** %.
* **`round10_calc.py`** — a new v3.41 block emits
  `survey_numbers_round11.tex` (34 macros) and `tab_occurrence.tex` (both
  panels of Table `tab:occurrence`, generated). New macros: `\GrossBwGHz`,
  `\GaussCross`, `\PgeFourPct`, `\ExpNonBP`, `\PgeOneNonBPPct`,
  `\FluxBpicThree/Six`, `\FluxHdFour`, `\FluxCpSeven`, `\FluxRatioBpic`,
  `\MaskRestRoundMHz`, `\CatCOoneGHz`, `\LabCOoneGHz`, `\CatCOerrMHz`,
  `\CatCOerrKms`, `\CatWorstKms`, and per-flag `\Fobs*`, `\Fcen*`, `\Dnu*`,
  `\Dv*`, plus `\StelBpicThree/Six/Coarse`, `\BpicSpreadKms`,
  `\BpicPairSepKms`.

  **The freeze-drift guard is untouched and passes.** It still re-asserts
  `OccMeasured` 6.2, `NOccSystems` 59, `OccUnit` 3.6, `OccUniform` 8.6 and
  `DutyHalf` 10.8 and aborts on any drift.

**The v3.31 freeze is kept.** The refreshed 2026-09-11 export (459 windows /
91 stars / 85 systems, first Band 10 data) was **not** substituted: §1(iv)
pre-registers the unprocessed datasets as the held-out confirmatory sample.

### How the 1-MHz catalogue rounding was recovered

A crossing lies on its window's channel grid, so snapping (laboratory rest
frequency + released `line_off`) to that grid and subtracting the offset returns
the catalogue entry the pipeline used — without reference to anything printed in
the manuscript. Over the fine windows this gives CO(1−0) = 115.271000,
CO(2−1) = 230.538000, CO(3−2) = 345.796000, CO(4−3) = 461.041000,
SiO(5−4) = 217.105000: the frozen mask stores rest frequencies **rounded to
1 MHz**, worth up to ±1.3 km s⁻¹ at 115 GHz. The β Pic B3 crossing frequency
115.260644 GHz lands on the grid to 0.0013 of a channel, confirming it as the
measured channel; the laboratory-referred offset is therefore −10.558 MHz and
the stellar-frame offset −2.72 km s⁻¹, and the 0.9 km s⁻¹ three-epoch
concordance stands. Full working in `REFEREE_RESPONSE_ROUND10.md` §1 (A4).

`verify_referee.py` (new, in this folder) reproduces every numerical referee
claim we checked, straight from `frozen_export_v3.31.json`.

---

## 4. Type 3 fonts — known inherited defect, and the corrected gate

**3 Type 3 fonts, on page 6 only**: `EVICAO+DejaVuSans-Bold`,
`GCWXDV+DejaVuSans-Oblique`, `BMQQDV+DejaVuSans`. They are DejaVu glyphs
(σ, →, ≥) inside `figures/pipeline_schematic.pdf`, which was not generated with
`pdf.fonttype=42`. **Present in v3.39's and v3.40's released PDFs too**; the
generator for the schematic is not in the version folder, so it cannot be
regenerated here. `gs -dNoOutputFonts` removes them by converting text to
outlines and was tested (visually identical at 110 dpi, 40 kB → 237 kB) but is
**not applied**: it introduces faint glyph artefacts and loses text
selectability, which is an author's call.

**The gate wording, corrected.** BUILD_NOTES for v3.34–v3.40 reported
"0 Type 3 fonts". That statement was false, and it was false because the gate
described a different quantity: it inspected the *manuscript's own* font set
and did not enumerate fonts inherited from included figures. The gate is now:

> enumerate every font on every page of the output PDF
> (`pymupdf`: `page.get_fonts()`), count those whose type field `f[2]` is
> `'Type3'`, and report the count **with the page numbers and font names**.
> Do not report zero unless that enumeration returns zero.

Reported this way the correct v3.40 figure is 3, not 0, and so is v3.41's.

`pipeline_schematic.pdf` also carries **~12 hand-typed survey numbers**, which
violate the paper's single-source rule and will all be silently wrong if the
freeze is ever swapped. Regenerating it from the macros is an outstanding item.

---

## 5. The other two gates that were wrong, and the one that is not clean

* **Underfull hboxes.** v3.40's BUILD_NOTES claimed "0 underfull hboxes"; the
  v3.40 source in fact emits **10**, all from justified text in fixed-width
  `p{}` table columns (the scope-of-analyses table and the validation-changes
  table). Fixed properly: `array` is loaded, a `P{}` column type
  (`>{\raggedright\arraybackslash}p{#1}`) replaces `p{}` in both tables, and the
  count is now genuinely **0**.
* **Overfull `\vbox`, 1.57 pt.** One remains, emitted by the output routine
  around p. 22–23. It is a page-fitting warning, not an overfull hbox — no
  material is set into the margin — but the as-received source had none, so it
  is a regression introduced by this round's repagination. Local remedies
  (`\enlargethispage`, `\raggedbottom`, reflowing the neighbouring text) did not
  clear it; the value is rigid, which points at a float rather than a paragraph.
  Recorded rather than suppressed.

---

## 6. Open items for the authors

1. **The system count is probably 81, not 82.** `HD 139084B 805632` and
   `HD 139084B 921024` share execution block, spectral windows and on-source
   times but carry different system ids and distances, and follow exactly the
   naming pattern of the two component pairs that *are* in the de-duplication
   `PAIRS` list in `survey_stats_round10.py`. On that reading there are seven
   designation-linked pairs (as §3 already says) and the list is missing one.
   Fixing it changes `\NSystems` and every occurrence denominator, so it breaks
   the freeze and trips the drift guard — **it was not done here**. The defect
   is disclosed in the Data Availability section with its size (≲1.5 %).
2. **Two mask-loss computations disagree by ~7×.** `survey_stats_round10.py`
   gives `mask_loss_GHz` = 0.64 over 15 transitions; the generated Table
   `tab:maskband` gives 4.96 over 276 transitions of eight species, and
   `round9_calc.py` renews `\EffBandGHz` from the latter. Unreconciled.
3. **Release packaging.** `make_numbers.py` cannot be run as shipped
   (`duty_v331.json` absent) and `survey_stats.py` reads the absolute path
   `/workspace/SETI/figwork/v331_data.json`. Until both are fixed the Data
   Availability statement's "single `make paper` invocation" claim is not true.
4. **The seven author markers are deliberately still in the source**, at lines
   38, 187, 198, 2577, 2580, 2585, 2596: VBRL affiliation; White (2026) EB
   overlap and its exception clause; competing interests; arXiv ID for
   White (2026); CRediT roles; submission git tag. The Data Availability
   statement still depends on a tag that does not exist.
5. **Not recoverable from the frozen products, and now said so in print**: the
   control-ring radius and centre; the spectral-extraction operator; the
   running-median width W; the per-window Hanning/online-averaging state; the
   per-position noise records needed to test the coarse-noise defect.
6. `per_target_results_v3.32.csv` is still versioned v3.32 against a v3.41
   manuscript, `n_ant` is empty in all 462 rows, and its disposition strings
   differ from Table 7's. The first is cosmetic; the other two are now
   disclosed in the paper.

---

## 7. Files

* `technosignatures_20pc_v3.41.tex` — the manuscript (3,858 lines).
* `SNAPSHOT_v3.41_asreceived.tex` — the as-received v3.40 content, for diffing.
* `SNAPSHOT_v3.41_preA4.tex`, `SNAPSHOT_v3.41_pretrim.tex` — intermediate
  snapshots taken before the two scripted structural passes (the previous
  botched splice is exactly why this is a standing rule).
* `SNAPSHOT_round10_calc.py`, `SNAPSHOT_survey_stats_round10.py` — generators as
  received.
* `survey_numbers_round11.tex`, `tab_occurrence.tex` — generated this round.
* `verify_referee.py` — independent re-computation of the referees' numerical
  claims from the frozen export.
* `measure.py`, `gate.sh` — the length budget and the build gates.
* `REFEREE_RESPONSE_ROUND10.md` — point-by-point response to all three reports.
