# Response to the three final reports — v3.49, the submission version

**Manuscript:** *An ALMA Archival Search for Spectral Technosignatures toward
Stars within 40 pc*, White & Dey.
**Reports answered:** `v3.49_referee1_radio.md`, `v3.49_referee2_radiostars.md`,
`v3.49_referee3_general.md`, all three of which recommend **accept**.
**Built:** `technosignatures_20pc_v3.49.tex` -> **29 pages**, every gate zero.

All fourteen requested edits are applied: referee 1's E1--E6, referee 2's
E1--E4, referee 3's E1 and E3--E6. Referee 3's E2 is superseded by referee 1's
E2, which makes the same correction in the body's own words; see §2.

**Everything below is quoted from what a tool printed.** Referee 3 was right
that the last letter reported 45 edits where the script printed 44, and
−1,425 characters where the script printed −1,432 and the file delta was
−1,428. We re-ran that script here and record its own line (§6).

---

## 1. The four that mattered

### 1.1 An editorial marker was printing in the published body (R3-E1)

`\citep[][citation provisional]{White2026}` at l.164. The second optional
argument of `\citep` is a **post-note and it prints**: page 2 of the v3.48 PDF
read *"Our pilot (White 2026, citation provisional) extended that
methodology"*. Deleted. The bibliography already carries the honest flag,
"White G. J., 2026, MNRAS, submitted". Page 2 now reads "Our pilot (White 2026)
extended that methodology to TRAPPIST-1", verified in the rebuilt PDF.

The arXiv identifier this marker stood in for remains an **author action**
(§5.3).

### 1.2 A flux-density ratio was compared against a brightness-temperature LTE value, and the cited paper was inverted (R2-E1)

We accept both halves of this and have taken referee 2's replacement verbatim.
We also re-derived the physics rather than taking it on trust:

- The measured quantity is flux density per beam per channel
  (`\FluxBpicThree/Six` = `star_snr` × `rms_mJy`, `round10_calc.py` l.263--269).
  For that quantity the optically thin LTE ratio is
  $(A_{21}/A_{10})(g_2/g_1)e^{-11.07/T}$ = 15.99 $e^{-11.07/T}$: **9.2 at 20 K,
  6.4 at 12 K, 16.0 as $T\to\infty$.** We reproduce every entry of referee 2's
  table. The manuscript's $\simeq4$ is the brightness-temperature value.
- Matrà et al. (2017) §3 report **integrated line fluxes** (3.5 ± 0.4 and
  6.7 ± 0.7) × 10⁻²⁰ W m⁻², ratio 1.9 ± 0.3, whose LTE comparator is
  $7.59\,e^{-16.59/T}$ — we get 7.59 from $(A_{32}/A_{21})(g_3/g_2)(\nu_{32}/\nu_{21})$
  and $T_{\rm exc}$ = **11.98 K** from their ratio, i.e. the 12 ± 4 K they
  print. Subthermal excitation is that paper's headline result, so "only mildly
  subthermal" inverted it and the inference drawn from it ("excitation cannot
  account for a deficit that size") was unsupported.

The corrected sentence is friendlier to the paper than the one it replaces:
beam dilution and subthermal excitation both depress the ratio, so the observed
1.4 is consistent rather than deficient.

**On referee 2's optional strengthening** (at 12 K the point-source expectation
is 6.4 and the beam solid angles differ by $(1.09/2.71)^2$ = 0.162, giving
≈1.0 against the observed 1.4): we have checked the arithmetic and it holds,
but we have **not** printed it. It needs a generated macro, referee 2 declined
to request a generator change in the last round, and the claim it would make —
that the ratio positively *confirms* the CO reading — deserves a round of
review we no longer have. It is recorded here so a later version can take it.

### 1.3 `\NUVCetiWin` = 8 was wrong for the star it was attached to (R1-E3)

Fixed at the generator, and we verified the selection ourselves against the
released catalogue before changing anything:

| | Band 3 windows | min rms (mJy) | dist (pc) | EIRP (W) |
|---|---|---|---|---|
| G 272-61**A** | 4 | 0.24119 | 2.7195 | 1.67 × 10¹³ |
| G 272-61**B** | 4 | 0.24133 | 2.6749 | 1.62 × 10¹³ |

`'G 272-61' in star_name` matched both components, so the printed count was 8
and the row taken as "deepest" was **A's**, while the distance and EIRP printed
two lines later are **B's**. `v347_calc.py` l.203 now tests
`star_name == 'G 272-61B'`. Exactly one printed digit moves, 8 → 4:
`\UVCetiRms` (0.241), `\UVCetiSmin` (1.21), `\UVCetiFlo` (91.565) and
`\UVCetiEB` (`A002_X877e41_X14c1`) are unchanged, because B's own deepest
window rounds to the same printed values. The appendix now reads "the deepest
of its 4 windows in that band".

### 1.4 The unsearched second block was declined by de-duplication, not by the download budget (R1-E4)

Corrected at both sites (l.1721 and l.1834). We verified the mechanism
ourselves from `archive_meta_v343.json` rather than accepting the report:

- **102 observing units, 448 progenitor blocks, and the searched-blocks-per-unit
  distribution is `{1: 102}`** — every unit contributed exactly one block. A
  3-block per-target cap cannot produce that; a one-block-per-unit rule does.
  35 of the 102 units have more than three progenitors.
- **CP−72 2713 was searched in exactly two blocks in total**, B6
  `A002_Xc296d2_X148c` and B7 `A002_Xff0235_X4a6d`, which is **below** the cap.
  The cap cannot be what declined `A002_Xff0235_X502d`.

§3 already names spectral-window de-duplication as the second of the two
deliberate choices, so the corrected sentences now point at the paper's own
mechanism. The substance is unchanged: the block was not searched during the
survey, and it has been searched now.

*This error was in the previous response letter as well as in the manuscript.
We had repeated it to the author.*

---

## 2. The remaining referee edits

| edit | disposition | note |
|---|---|---|
| **R1-E1** comma splice in §4.1 | applied, 0 chars | PDF now reads "does not cancel. Smooth emission lives on short baselines". Verified out of the PDF, not the source. |
| **R1-E2** abstract vs §4.3 on TRAPPIST-1 b | applied, −6 | "TRAPPIST-1 b, the only sample planet to reach the drift ceiling, sits at it." |
| **R3-E2** same sentence, different wording | **superseded by R1-E2** | Both fix the same defect. R1's takes §4.3's own words ("sits at it"), which is what aligning four sites means; R3's introduces a fifth wording. R3's saving was 4 characters larger and we did not need them. |
| **R3-E3** "the case exceeding" → "the case that reaches" | applied, +3 | The fourth site. 4.00 m s⁻² equals the top of the 3.60--4.00 ceiling, so "exceeding" was false. All four sites now say reaches/sits at. |
| **R1-E5** single-source the LSR velocity | applied, +6 | `$-\VlsrHdLsr$` replaces a hand-typed −23.9 in the mask paragraph. |
| **R1-E6** one comma in §4.1 | applied, +1 | |
| **R2-E2** "gas-derived" $v_{\rm sys}$ | applied, −7 | Matrà et al. take 20.0 ± 0.7 km s⁻¹ as an **input** (Gontcharov 2006, stellar heliocentric RV). The caption now says "used by". The adoption and the *Gaia* DR3 hot-star argument are untouched. |
| **R2-E3** CO mass limit with no $T_{\rm ex}$ | applied, +42 | Now "in optically thin LTE at $T_{\rm ex}$ = 20--50 K". `\CoTempLo/Hi` already existed in `v344_calc.py` and were retired only because nothing cited them; they came back automatically. |
| **R2-E4** author TODO comments in the arXiv source | applied, 0 rendered | §3. |
| **R3-E4** `%.1f` → `%.2f` for `HanFacWorst` | applied at the generator | The abstract now reads "×2.00 to ×2.67 (median ×2.29)". |
| **R3-E5** `prosecount.py` joins lines with `"\n"` | applied | On joined text the main-text antithesis count is **23**, exactly the figure referee 3 recomputed by hand, and the gate no longer depends on where lines wrap. |
| **R3-E6** `apply_v348_edits.py` writes an undefined `\NSys` | applied, and verified | §6. |

---

## 3. The author TODO comments (R2-E4), and what we did **not** do

arXiv distributes the LaTeX source, so the seven author-facing `%` blocks were
public — one reading "Cannot be authored by the assistant -- awaiting the
authors' wording", another naming the git tag `submitted-v3.32` in a v3.48
paper. `strip_author_todos.py` copies each block **verbatim**, with the
manuscript line it was attached to, into
[`AUTHOR_ACTIONS.md`](AUTHOR_ACTIONS.md) and then deletes it from the `.tex`.

- The arXiv source now contains **no TODO and no author-addressed comment**
  (checked in the built tarball). What remains are the class build note and the
  `%% generated by ...` provenance banners on the macro files, which are
  appropriate in public source.
- The PDF text is **byte-identical before and after** the removal, page for
  page. Comment removal cannot move a rendered character, and we checked.
- **The questions are not answered by this.** They are listed in §5 and in
  `AUTHOR_ACTIONS.md`, and they are the real gate on submission.

One further comment was removed for the same reason: a generated macro file
carried `%% (referee A item 5)` into the public source, an internal review
label. Fixed in `localnull_calc.py`; no manuscript character moves.

---

## 4. A defect none of the five rounds could see: the abstract was over the arXiv limit

This is the one substantive finding of this cycle that no report contains, and
it would have stopped the submission at the upload form.

`abstract_limit.py` — the gate all three reports quote, and the gate that says
"1907 of 1920" — **stripped every control sequence to a space**, so the
*values* of the twenty generated macros the abstract cites were never counted.
The folder's other tool, `abschars.py`, reads the typeset abstract out of the
PDF and was dropped from `gate.sh` after v3.45. Run on v3.48 it prints:

```
rendered abstract: 1975 characters, 311 words (arXiv limit 1920, headroom -55)
```

arXiv's limit is hard: *"abstracts longer than 1920 characters will not be
accepted; abridge your abstract if necessary"* (info.arxiv.org/help/prep.html).
**v3.48 would have been refused.**

What we did:

1. **Fixed the counter.** `abstract_limit.py` now expands the generated macros
   from `survey_numbers*.tex` before counting, and renders the one-character
   math symbols as one character. It makes v3.48 **1971** against the PDF's
   1975 — the two independent measurements now agree to 4 characters.
2. **Put both counters in `gate.sh`**, permanently, so the source-side and
   PDF-side numbers are checked against each other on every build.
3. **Cut 94 source characters of duplication from the abstract**, documented in
   `apply_v349_abstract.py`:
   - "meeting our public-archive coverage criteria" → "with public-archive
     coverage" (the criteria are defined in §3, to which the sentence points);
   - the 1 MW / 12 m / 230 GHz benchmark, which §4.2 already states in full
     ("a 12-m aperture radiating 1 MW at 230 GHz, EIRP ...").

   **No evidence, no self-criticism and no number that appears nowhere else was
   removed.** Result: **1895 counted from the source, 1905 from the PDF.**

**A trap worth recording.** Three further cuts (−54 characters: the
"Only 118 of 431 windows" sentence, "pinned recurrence criterion", "The
completeness measured") were applied, built and **reverted**: a *shorter*
abstract pulls one more line of §1 onto the title page, where the fixed
affiliation footnote block leaves no room for it, and the build reports
`Overfull \vbox (1.38652pt too high) ... while \output is active`. Sweeping the
abstract length shows the page-1 residual is quantised by line — −60, −30 and
+20 characters about that point all give 0.31 pt, and only near +40 does it
reach zero. The wording we shipped sits in the clean band. This is the same
lesson as v3.48's `tab:nomenclature` font reduction: **a length change is free
in characters and not free in gates.**

**For the upload form.** Two paste-ready plain-text abstracts are in the
folder, both counted:

- `arxiv_abstract_v349.txt` — **1,911 characters**, verbatim the PDF abstract,
  ASCII-normalised (β → "beta", × → "x", superscripts as `10^13`). 9 characters
  of headroom; unicode β and × instead would give 1,903.
- `arxiv_abstract_v349_abridged.txt` — **1,870 characters**, the same text with
  the three reverted cuts applied to the metadata only, which arXiv explicitly
  permits. Use this if the form's own counter objects; it is known to count
  whitespace in ways `wc` does not.

---

## 5. Author actions outstanding — none of these can be closed by a referee or by us

Verbatim in [`AUTHOR_ACTIONS.md`](AUTHOR_ACTIONS.md). **These are the gate on
submission, not the manuscript.**

1. **Affiliation 3 is incomplete.** `\altaffiltext{3}{VBRL Holdings Inc.}` has
   no city and no country.
2. **The competing-interest statement asserts two facts we cannot verify** —
   that VBRL has no stake in the work and provided no funding. Both OJAp and
   arXiv expect this statement to be the authors'.
3. **The White (2026) arXiv identifier.** This is what the deleted "citation
   provisional" post-note stood in for. The bibliography entry says "MNRAS,
   submitted", which is honest and sufficient for posting, but a reader
   assessing methodological continuity needs the identifier.
4. **The CRediT split** is inferred from the structure of the paper, not from
   the authors.
5. **The submission git tag.** The Data Availability prose is tag-agnostic
   ("the repository commit tagged at submission"), so only the tag itself is
   outstanding; the stale `submitted-v3.32` name survived only in the comment
   that is now removed.
6. **"No execution block is analysed in both papers."** This sentence is an
   assertion that has never been verified execution block by execution block
   against the White (2026) manuscript. It is the only factual claim in the
   paper of which that is true. It must be confirmed or corrected before
   posting — and if there is a deliberate exception (shared calibrator usage,
   say), it belongs in that sentence.

Two further author judgements, raised by referee 2 and not defects:

- **The priority claim** ("Barnard's Star and Wolf 359 gain first millimetre
  technosignature limits", now in the abstract). Referee 1 searched the
  literature and found nothing prior; referee 2 agrees but says an abstract
  priority claim should be confirmed by an author. Note also that v3.48 cut the
  explicit centimetre-wave disclaimer; the surviving bound is "in an ALMA
  archival technosignature survey".
- **Whether to print referee 2's ≈1.0 beam-corrected expectation** (§1.2).

---

## 6. Provenance: the shipped script now reproduces the shipped manuscript (R3-E6)

`apply_v348_edits.py` emitted `\NSys`, which is defined nowhere; only
`\NSystems` exists. The build caught it, it was repaired by hand, and the
result was that the script in the folder no longer produced the manuscript it
documented. Corrected, and **verified rather than asserted**: a clean copy of
`technosignatures_20pc_v3.47.tex`, renamed and run through the fixed script,
now differs from the shipped v3.48 at **no line at all** except the released
catalogue's version-bumped filename. The script's own output line is

```
edits: 44 applied, 0 failed | NET -1428 source chars (191630 -> 190202)
```

which is exactly what referee 3 measured: **44 edits, −1,428 characters**. The
previous letter's "45 edits, −1,425" is withdrawn; the 45th was the hand
repair, and −1,425 was not a figure any tool printed. The script is marked
historical and cannot be run against v3.49 by accident (every anchor would
fail and nothing would be written).

This round's edits are in `apply_v349_edits.py` (12 manuscript edits) and
`apply_v349_abstract.py` (2), with the same anchor-exactly-once refusal. Their
own output lines:

```
edits: 12 applied, 0 failed | NET -37 source chars (190202 -> 190165)
abstract edits: 2 applied, 0 failed | NET -94 source chars (190165 -> 190071)
7 comment blocks moved to AUTHOR_ACTIONS.md | source 190071 -> 188098 (-1973 chars, 0 rendered)
```

Generator-level edits are not in those scripts, because they belong in
`make_all.sh`: `v347_calc.py` (R1-E3), `v342_calc.py` (R3-E4),
`prosecount.py` (R3-E5), `localnull_calc.py` (§3), `abstract_limit.py` (§4).
**`retire_macros.py` was run last**, after every generator, as referee 3
warned: re-running `v342_calc.py` resurrects the macros it had retired.

---

## 7. Verification

```
pages: 29 | errors: 0 | undef refs/cites: 0 | multdef: 0 | overfull: 0 | underfull: 0
Type3 fonts: 0
main 20.61  back 1.03  appendices 6.81  bib 0.31  TOTAL 28.76
abstract: 1895 rendered characters from the source (arXiv limit 1920) -- OK
rendered abstract: 1905 characters, 302 words (from the PDF, headroom 15)
macros defined: 595   consumers: 5   unused: 0
em-dashes in source: 0        main-text antithesis: 23 (joined-text count)
```

- **Clean regeneration**: every generated `.tex` fragment and the released
  catalogue deleted and rebuilt by `make_all.sh` — **27 of 27 byte-identical**.
  The 12 figure PDFs differ only in their embedded creation date and are
  **12 of 12 pixel-identical** at 72 dpi.
- **arXiv set**: `arxivset.sh` into an empty directory — **31 items** (24
  tex/cls/sty + 7 figures), builds there to 29 pages with 0 errors,
  0 undefined, 0 multiply-defined, 0 overfull, 0 underfull, 0 Type 3 fonts,
  0 missing files. **0 TODO or author-addressed comments** in the tarball.
- **Page split unchanged from v3.48 to the digit**, which is the point: the
  edits are net −131 source characters and referee 3 measured 0.24 pages of
  margin, so nothing needed to be cut to pay for them.
- The released catalogue is renamed `per_target_results_v3.49.csv` with the
  manuscript, and the Data Availability statement names it.

Every changed passage was read out of the **PDF**, not the source, which is how
referee 1's C9 comma splice was found last round.

**Not pushed**, per instruction.

— for the authors, 2026-09-12
