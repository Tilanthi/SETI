# Virtual peer review — round 4

**Remit.** Audit the fixes claimed in `VPR_DISPOSITION.md`, then hunt for further
instances of the bug families rounds 1–3 found, review the newly added content
cold, and read the paper front to back.

**Material examined.** `technosignatures_40pc_v3.85.tex` (4575 lines) and the
built PDF (41 pp, `pdftotext -layout`), `per_target_results_v3.85.csv` (1655
rows × 50 columns), all 63 `survey_numbers*.tex` macro files, all 24 `tab_*.tex`
fragments, the text layer of all 21 figure PDFs (`pymupdf`), `make_all.sh` and
the ~50 live generators, `frozen_export_v3.81_survey.json`,
`archive_meta_v381.json`, `canon_names_v381.json`, `catalogue_constants.json`,
`visfit_cp72_v358.json`, `blockboot_v385.json`,
`tables/table_numbers_v328.json`. `reproduce_from_catalogue_v385.py` and
`audit_numbers_v385.py` were executed. A SIMBAD TAP query was used to check four
designations. No manuscript file was edited.

> **One housekeeping note.** Running `reproduce_from_catalogue_v385.py`
> standalone rewrote `survey_numbers_round39.tex` (it is that script's output).
> I restored it byte-for-byte to `\newcommand{\NReproChecks}{41}`, the value the
> built PDF carries. See **Q25** — the fact that it *changed* when run is itself
> a finding.

---

## Summary

| | MAJOR | MINOR |
|---|---|---|
| Fixes that did not fully land | 8 | 3 |
| New instances of the round 1–3 bug families | 9 | 6 |
| Errors in the newly added content | 7 | 6 |
| Not previously raised | 3 | 4 |
| **Total** | **27** | **19** |

The single most important result of this round: **the star-count fix (P15) is
only about half applied.** Figure 1 — printed, on page 3 — still plots 94 stars,
and `\NStarBands` = 117 is still the alias-inflated count where the released
catalogue has 113. Three further statistics moved to the canonical names while
the statistics sitting next to them did not, so the paper now contains 90, 94,
83, 51, 53, 113 and 117 as counts of overlapping things.

The second most important: **the chance expectation for the four unattributed
events now takes five different values in the paper** (3.1, 3.2, 3.9, 4.4, 4.7),
the abstract and the conclusions quote the one the text explicitly says it does
*not* use, and Table 8 — the table added to fix precisely this — mislabels one
row and omits two of the five.

---

## Part A — verification of the claimed fixes

### A.1 Verified correct (I re-derived each from the released products)

| ID | Claim | Verified how | Verdict |
|---|---|---|---|
| **C1** | 200 of 404 blocks resolve; 198 deliver both hands; 2 single-hand = 8 Class B windows toward τ Ceti, none stage-1 | §4.5 text reads exactly this; consistent with `canon_names_v381.json` route counts | ✅ correct |
| **C2** | 75 crossings = 71 A + 4 B | catalogue: `crossing==True` → Counter({A: 71, B: 4}) | ✅ correct |
| **C3** | drift ceilings 1.1–10.5 kHz s⁻¹ | catalogue max `drift_max_Hz_s` = 10 466.7 Hz s⁻¹; `\DriftKHzHi`=10.5; Table 5 correct | ✅ in Table 5 — ❌ **not in §4.2, see Q9** |
| **C6** | Table 23's caption no longer claims to audit every region-max window | caption now reads "this table gives the pairs either statistic promotes to stage 1, not all 66 of them" | ✅ caption fixed — ❌ **three text claims survive, see Q11** |
| **C7** | radius-corrected statistic demoted to a robustness check | §5.3.2 "We do not adopt the radius-corrected statistic as the primary one, and we say why" | ✅ correct, and well argued |
| **C12** | 0.445 → 0.432 described as *away* from 0.5 | "it goes from 0.445 to 0.432, slightly further away" | ✅ correct |
| **C13/C55** | β Pic 8 blocks, 8.4 yr, 2 transitions | `\NStageOneBpicEb`=8; text "8 execution blocks, over 8.4 yr from 2013-10-06 to 2022-03-03" | ✅ correct |
| **C14** | 0 of 1655 and 16 of 1655 | §5.3.4 "matched or exceeded by 0 of the 1655 per-window control maxima and the Band 6 peak … by 16 of them" | ✅ correct, and now called ranks not p-values (O15/S11) |
| **C25** | Table 5's Peff rows are the per-window product, labelled as such | Table 5 row reads "Effective Peff = Ptrig Cresp Csmear, per window, Class A / Class B"; values 5.1e13–9.1e16 med 1.9e15 reproduce from the catalogue (`PeffWinLoA/MedA/HiA` all pass) | ✅ correct |
| **C26** | top three systems = BD+05 1668, Proxima Cen, HD 33793, 285 windows, 17.2 % | catalogue: 100+100+85 = 285; 285/1655 = 17.22 % | ✅ correct |
| **C30** | smearing negligible for 446 **of the 455** that carry a value | catalogue: 455 rows with `eta_smear`; 9 below 0.99; 455−9 = 446 | ✅ correct |
| **C34** | on-source median 2812 s | catalogue median `on_source_s` = 2812.32 | ✅ correct |
| **C36** | "none recurs" replaced by the correct statement for all four | "All four have a persistence test, and all four fail it" | ✅ correct in §5.3 — ❌ **contradicted in §5.3.6, see Q17** |
| **C51** | 1 900 star-hour-GHz | `sum(on_source × bandwidth)/3600/1e9` = 1 900.4 | ✅ correct |
| **C57** | 24 Band 8 windows toward three stars | catalogue `band=='8'` → 24; `\BandEightStars`=3 | ✅ correct |
| **S1** | all four unattributed events have repeats, 23 blocks, none recurs | `\NUnattRepeatBlocks`=23, `\NUnattRepeatLo/Hi`=1/16, Table 11 row sum 3+16+1+3 = 23 | ✅ arithmetic correct — ❌ **but see Q16, Q17** |
| **S2** | `blockboot` reads `obs` from the catalogue, giving 4 not 2 | ran the code path: `obs` = 4 | ✅ correct value — ⚠️ **by the fallback branch, see minor m12** |
| **S4** | null rebuilt; only block clustering resampled | code and text agree; text says so explicitly | ✅ correct |
| **S5** | Class A p quoted across 0.001–0.058 | `\BootPALo/\BootPAHi` = 0.001/0.058, printed in §5.3 | ✅ correct |
| **S6** | new P90,promote 8.7e13–1.4e17, median 2.8e15, ×1.16 | macros present, printed in abstract and §5.5; ×1.16 = 2.8e15/2.4e15 ✓ | ✅ correct |
| **S7** | decorrelation carried as a one-sided term | Table 15 row "+5/+20", §5.5 "every P90 in this paper is optimistic by that amount and cannot be optimistic in the other direction" | ✅ correct — ⚠️ **the same logic was not applied to pointing, Q27** |
| **S8** | the three candidate-manufacturing choices predate the reservation; the four later diagnostics named | §5.3.1 names all four and gives the reason none can promote | ✅ correct, and the commit-time corroboration argument is good |
| **S9** | Table 12/13 labels corrected to `survey` | Table 13(b) row "Sample: survey survey survey survey"; the withdrawal is stated in the caption and the text | ✅ correct |
| **S12** | ×0.48–1.35 called a transfer uncertainty and the largest budget term | Table 15 and §5.5 | ✅ correct |
| **S13** | 595 on P90 against a d² ratio of 6563 | §6.3 reads "∼649× lower in EIRP … the ratio of d² alone is ∼6563, so in received flux the present survey is the shallower" | ✅ correct in substance (the factor has regenerated to 649) |
| **S14** | duty-cycle function measured zero-drift, stated | Fig. 9 caption names the unmeasured cell | ✅ correct |
| **S15** | 41 of 65 Class A systems — now 42 of 61 | catalogue: 61 systems with a Class A window, 42 with >1 EB | ✅ correct, regenerated |
| **S18** | Table 12 caption says which frame each column is | caption does, and points at Table 22 | ✅ correct |
| **S19** | mask-width check stated as one-sided | §5.3.7 "That test is one-sided by construction" | ✅ correct |
| **S20/O13** | β Pic's role split from the injection campaign's | §5.3.4 "β Pictoris CO … is a positive control for localisation and recurrence and not for the carrier morphology" | ✅ correct, and clearly put |
| **O5/S16** | HD 14055's 3.2σ imaginary part withdrawn | §5.3 and Fig. 7 caption both withdraw it | ✅ in text and figure — ❌ **Table 9's verdict column does not, Q26** |
| **O6/S17** | 5.5σ CP−72 read as morphology, not significance | §G.5 | ✅ correct, and superseded by M1 |
| **P16** | `j1256-1257` → LP 736-15 | `NAME_REPAIR` maps it; catalogue carries LP 736-15 at 21.15 pc | ✅ correct |
| **P22** | seven uncited floats now cited | Figs. 6 and 7 both cited from the text | ✅ correct |
| **P23** | full-width figures at design size | Fig. 1 at `0.94\textwidth`, Fig. 7 at `0.94\textwidth`; no 0.65 scalings remain | ✅ correct |
| **M1** | drift-following fit on all 13; CP−72's 5.5σ withdrawn | Table 10 present; §G.5 and the conclusions both withdraw it | ✅ correct — ❌ **but the recovery summary is wrong, Q15** |

### A.2 Claimed fixes that did **not** land, or landed only partly

These are written up as Q1–Q3, Q6, Q9, Q11, Q15, Q17, Q26 below.

### A.3 A round-1 rebuttal that was wrong

**C11** was dismissed as "the interval is 0.341–0.458 and contains it". That is
true of the sentence on p. 20. It is not true of the *other* sentence, on p. 21:

> "a star-clustered bootstrap placing the median at **0.405** (95 per cent
> interval **0.42–0.46**)"

0.405 is outside 0.42–0.46. The reviewer was right about one of the two
instances; the rebuttal checked the other one. See **m2**.

---

## Part B — MAJOR findings

### Q1 — Figure 1 plots 94 stars; its caption says 90. MAJOR
**Evidence.** Text layer of `figures/eirp_context.pdf`:
`deepest window per star, Class B (25)` and `deepest window per star, Class A
(69)`. 25 + 69 = 94. The caption in the manuscript reads "for the deepest window
per star (**90 stars**, 1.30–39.63 pc)". `make_fig_context_v342.py:331`:

```python
def deepest_per_star(good):
    best = {}
    for r in good:
        s = r["star_name"]          # raw export string, not canon()
```

The file contains no `import star_alias` and no `canon`. The frozen export holds
95 raw name strings, 91 after alias merge, 90 after the eps Eri withhold.

**Problem.** The generator of the paper's first figure was never converted.
`VPR_DISPOSITION` P15 lists `survey_stats.py`, `v342_calc.py`, `v352_calc.py`,
`make_figures_v328.py` and `make_tables_v328.py` as converted;
`make_fig_context_v342.py` is not on the list and was not converted. The figure
therefore shows four duplicate points, and any reader who adds the legend counts
gets the pre-fix 94.

**Fix.** `from star_alias import canon` and key `best` on `canon(r["star_name"])`
in `deepest_per_star`. Then assert `len(best) == NStars` in the same function, so
the figure cannot silently disagree with its own caption again.

---

### Q2 — A released figure carries 94, 93 and 70 stars against "the 90 searched stars". MAJOR
**Evidence.** `figures/completeness_sensitivity.pdf`, panel (b): y-axis
`fraction of the 90 searched stars`; legend `any channelisation (94 stars)`,
`fine channels (<5 MHz) (70 stars)`, `coarse channels (≥5 MHz) (93 stars)`.
Derived from the catalogue with `canon()`: 90 / 66 / 89.
`make_figures_v328.py:596`: `best[r["star_name"]] = min(...)` — raw name again,
although lines 326, 335–336 of the same file *were* converted.

**Problem.** A partial conversion inside one file: `n_stars` moved to canonical
names, the per-star CDF did not. The figure is not printed in the manuscript,
but it ships in the release, and the Data Availability section explicitly claims
the extra figures "are products of the same generators and carry no number
quoted here" — this one carries the paper's headline star count, twice, wrong.

**Fix.** Same change at line 596, and at line 74 of `make_tables_v328.py`.
Better: make `star_alias.canon` the only way any generator may read
`star_name`, e.g. a helper `rows_canon()` that returns rows with the field
already replaced, and grep-ban the bare key.

---

### Q3 — `\NStarBands` = 117 is the alias-inflated count; the catalogue has 113. MAJOR
**Evidence.**
```
catalogue  len({(star_name, band)})                  = 113
catalogue  len({(canon(star_name), band)})           = 113
survey_stats.py:82  len({(r['star_name'], r['band_x']) for r in good}) = 117
```
The four surplus entries are exactly the four alias pairs:
`HD 207129 (Gaia …)` / `HD 207129  Gaia …` in B6, `HD53143 (…)` / `HD53143  …`
in B6, `* eta Crv` / `eta Crv` in B7, `* g Lup` / `HD 139664` in B6. Line 80 of
the same file uses `_canon`; line 82, two lines later, does not.
`make_tables_v328.py:74` repeats the same expression.

`\NStarBands` appears six times, including:
- §1: "117 target/band datasets mined from public data" — one of the paper's
  three stated contributions;
- Table 5, "Star/band datasets 117";
- §4.1, the statistical-units definition: "A target/band dataset is one entry in
  one ALMA band, 117 in all";
- §5.2, "117 target/bands are searched to completion and reported here";
- §5.3, "**All 117 star/band datasets** yielded at least one carrier-lane result".

**Problem.** The last of these is an "all N of the N" claim where N is wrong:
113 star/band datasets yielded a result, and the released catalogue cannot
produce 117 under any grouping. (117 is also the *pre-QA* count on raw names,
so it conflates two errors: the alias split and the QA cut.)

**Fix.** Canonicalise at line 82 and at `make_tables_v328.py:74`, then add
`chk('NStarBands', len({(r['star_name'], r['band']) for r in ROWS}))` to
`reproduce_from_catalogue_v385.py` so the build fails next time.

---

### Q4 — Table 3's "Stars" column reads 83 for the science sample. That is the system count. MAJOR
**Evidence.** `tab_partitions_v385.tex`:
```
Partition        & Blocks & Windows & Stars & Purpose ...
Science sample   & 404    & 1655    & 83    & the search reported here ...
Pre-specified hold-out & 77 & 315   & 36
Out-of-sample, beyond 40 pc & 47 & 198 & 22
```
The science sample has **90** stars in **83** systems. The other two rows (36,
22) are star counts (`\HoStars`=36, `\NOutSampleStars`=22).

**Problem.** The table that a reader consults to see what each partition
contains gives the wrong count for the only partition that matters, and mixes
units down the column. It also silently contradicts Table 5 four pages later
("Stars searched; independent systems 90; 83").

**Fix.** Print 90 in the Stars column, or add a Systems column and print 90 / 83.
Generated by `v381_calc.py:978`.

---

### Q5 — 51 vs 53 searched stars with a Gaia temperature. MAJOR
**Evidence.**
- §3: "The spectral-class proxy is `teff_gspphot`, available for **\NTeffStars**
  = 51 of 90 sample stars".
- Table 4 (`tab_specclass_v385.tex`), `N_searched` column: 1 + 9 + 16 + 6 + 21 =
  **53**.
- Table 5 (`tab_selection.tex`) spectral rows: same 53, and the percentages
  (1.9 / 17.0 / 30.2 / 11.3 / 39.6) sum to 100.0 on a denominator of 53.
- Fig. 2 legend (from the figure's own text layer): "searched here (**53**
  classified)".
- §6.3: "Among the **53** searched stars with a Gaia temperature, 21 are M
  dwarfs, 40 per cent".
- `tables/table_numbers_v328.json`: `n_sample_with_teff = 53`,
  `n_sample_teff_used = 53`.

Both numbers are generated. `v381_calc.py:846` matches the 90 released names
against `ranked_master40pc.csv` with a normaliser `_ck`; `make_tables_v328.py:162`
matches the same stars against the same census with a different normaliser
`norm`. The two disagree on two stars.

**Problem.** A reader who sums Table 4's `N_searched` column gets 53 and then
reads 51 in the text. Two independent name-matching implementations against one
census — the duplicate-implementation family again.

**Fix.** One matcher, in `star_alias.py`, used by both; then
`assert NUM['n_sample_teff_used'] == NTeffStars`.

---

### Q6 — `v342_calc.py` still carries its own `ALIAS`/`PAIRS`; four other generators still carry theirs. MAJOR
**Evidence.** `VPR_DISPOSITION` P15: "new shared `star_alias.py`;
`survey_stats.py`, `v342_calc.py`, `v352_calc.py`, `make_figures_v328.py` and
`make_tables_v328.py` all use it." In fact:

| file | imports `star_alias`? | local `ALIAS`/`PAIRS` still present? |
|---|---|---|
| `survey_stats.py` | yes (l. 59) | yes, l. 46 (dead) |
| `survey_stats_round10.py` | **no** | yes, l. 45 (live) |
| `survey_stats_systems.py` | **no** | yes, l. 10 |
| `v342_calc.py` | **no** | **yes, l. 141 and l. 150 — live, and it is the catalogue writer** |
| `v352_calc.py` | yes (l. 88) | yes, l. 226 |
| `make_figures_v328.py` | yes (l. 319/335, local imports) | yes, l. 110 |
| `make_tables_v328.py` | yes (l. 45) | — |
| `make_fig_context_v342.py` | **no** | — (uses raw names, Q1) |

**Problem.** The stated durable fix — "one place" — did not happen. Six copies of
the pair map remain, one of them in the generator that writes the released
catalogue. They agree today; nothing makes them agree tomorrow, and the P15
post-mortem says the last time three copies drifted the error was "consistent
everywhere and therefore invisible".

The identity offered as the defence, "no two systems may share a distance"
(`v342_calc.py:930`), does not cover this class: it compares distances rounded
to 3 dp, and two entries for the same field differ in the 3rd–4th decimal
(TWA 3A: 37.0547 vs 37.1301 pc), so it passes regardless. It also cannot detect
a *star* counted twice inside one system, which is what three of the seven
"pairs" are (Q7).

**Fix.** Delete the five surplus copies. Replace the distance identity with one
that can actually fail: assert that the set of `(system_id, star_name)` pairs in
the catalogue equals `{(sysname(n), released(n))}` recomputed from
`star_alias.py`, and that `len({released(n)}) == NStars`.

---

### Q7 — three of the seven "physically bound pairs" are one designation twice; TWA 3A is duplicated and merged nowhere. MAJOR
**Evidence.** `star_alias.PAIRS` — "physically bound pairs that share one
statistical unit":

| pair | same EB? | SIMBAD |
|---|---|---|
| `G 272-61A` / `G 272-61B` | same EB `A002_X877e41_X14c1` | two entries, π = 367.71 / 373.84 mas — a real binary (= UV Cet / BL Cet) ✓ |
| `GJ 2006A` / `GJ 2006B` | same EB | real binary ✓ |
| `V star TX PsA` / `V star WW PsA` | same EB | two stars ✓ |
| `NAME AT Mic AB  Gaia DR3 …` / `V AT Mic B` | same EB | "AB" already contains B — the components are double-counted |
| `2MASS J05241914-1601153 551040` / `… 717696` | same EB `A002_Xcf749a_X4871` | SIMBAD returns **one** object, `PM J05243-1601`, otype `**` |
| `LP 476-207 384128` / `… 783296` | same EB `A002_Xd10f82_X2635` | SIMBAD returns **one** object, `LP  476-207`, otype `SB*`, **π = 30.12 mas = 33.2 pc**, against the catalogue's 23.75 / 23.79 pc (π = 42.1 / 42.0 mas) |
| `HD 139084B 805632` / `… 921024` | same EB `A002_Xcd8029_Xb6b0` | SIMBAD returns **one** object, π = 25.4404 mas = 39.307 pc — which matches `805632` exactly; `921024` is at 38.716 pc, a different source |

And, not in `PAIRS` at all:

| `TWA 3A 696000` (37.0547 pc, 8 win) | `TWA 3A [576064]` (37.1301 pc, 4 win) | same EB `A002_Xd3607d_X6487` |

SIMBAD's TWA 3A has π = 26.9871 mas = **37.055 pc**, matching `696000` exactly.

**Problem, three layers.**
1. **Internal inconsistency.** Four ALMA fields produce two `target` strings that
   differ only by an undocumented integer suffix. Three of them are collapsed
   into one "bound pair"; the fourth, TWA 3A, is not collapsed at all and is
   counted as **two stars and two systems**. Whatever the truth is, the four
   identically-shaped cases are treated two different ways. If TWA 3A is merged
   like its siblings, the headline becomes 90 stars in **82** systems — and the
   system count is in the title's companion sentence, the abstract, Table 3,
   Table 5, Fig. 3, Fig. 4 and the conclusions.
2. **The designations are wrong, or unverifiable.** The paper says (§4.1) "A
   catalogue entry is one star **as SIMBAD designates it**". SIMBAD designates
   none of these objects `TWA 3A 696000`, `LP 476-207 384128` or
   `HD 139084B 921024`. In the LP 476-207 case *neither* released entry has the
   parallax SIMBAD gives for LP 476-207, so at least one — probably both — is a
   different Gaia source in that field, published under a name that is not its
   own. This is the same defect as P16 (`j1256-1257` → LP 736-15), found once
   and not swept for.
3. **The conclusions assert it.** Data Availability: "The statistical unit is
   `system_id`, with **seven bound pairs** sharing one identifier." Three of the
   seven are not bound pairs on any reading available to a reader.

**Fix.** Resolve each of the eight suffixed entries by position against Gaia
DR3/SIMBAD, give each its own designation, and re-derive `PAIRS` from the
resolved identities and separations rather than from string prefixes. If TWA 3A
`[576064]` is TWA 3B (separation 1.4″), merge it and republish 82 systems. In
either case the paper should state what the numeric suffix is. And the released
catalogue needs RA/Dec columns (see m18) so the question is answerable at all.

---

### Q8 — the released catalogue does not round-trip through `star_alias.py`. MAJOR
**Evidence.**
```python
from star_alias import sysname
len({sysname(r['star_name']) for r in catalogue}) == 84      # not 83
```
The catalogue's `star_name` column is written through `released()`, which does
`' '.join(n.split())` and collapses the double space; `PAIRS` keys still carry
the double space (`'NAME AT Mic AB  Gaia DR3 …'`). So the AT Mic pair no longer
maps, and a reader who applies the shipped module to the shipped catalogue gets
84 systems where the paper says 83.

**Problem.** §4.6 invites exactly this: "the survivor count at every step is a
column filter on the released catalogue". The `system_id` column rescues the
count, but the module the release ships does not reproduce the module's own
output.

**Fix.** Normalise whitespace in `canon`/`sysname` as well as in `released`, and
add a round-trip assertion to the catalogue writer.

---

### Q9 — §4.2 still prints the superseded drift range 1.1–5.9 kHz s⁻¹. MAJOR
**Evidence.** `technosignatures_40pc_v3.85.tex:1223`, a bare literal:
```latex
1.1--5.9\,kHz\,s$^{-1}$ and trial drift rates per window 2--\BpSixTrials{} ...
```
against `\DriftKHzLo--\DriftKHzHi` = 1.1–10.5 in Table 5 (line 655), and against
the catalogue (`max(drift_max_Hz_s)` = 10 466.7 Hz s⁻¹). C3's fix reached the
table and not the prose, because the prose value was never macroised.

**Problem.** The two values sit four pages apart and differ by ×1.8. This is the
round-1 bug family verbatim: a hand-typed literal beside a generated macro.
`audit_numbers_v385.py` (51 checks, 0 fail) cannot see it because it only checks
macro-to-macro and macro-to-product consistency, never bare literals in prose.

**Fix.** Replace the literal with `\DriftKHzLo--\DriftKHzHi`. Then add a prose
sweep to the audit: extract every number in the `.tex` body that is not inside a
macro and is not a citation year, and flag any that matches a macro value at an
earlier version — or, more cheaply, grep the body for the digit patterns of the
current macro set and require each headline quantity to appear only as a macro.

---

### Q10 — "seven windows against four" for a comparison that is now 13 against 66. MAJOR
**Evidence.** Two hard literals:
- §5, line 1691: "the symmetric form of Eq. 2 flags a strict subset of what the
  region-maximum form flags, **seven windows against four**";
- §G.4, line 4398: "the symmetric criterion flags a strict *subset*, **seven
  windows against four**, the three that drop out …".

Catalogue: `stage1_flag` = **13**, `stage1_flag_regionmax` = **66**, and the 13
are a strict subset of the 66 (verified row by row). §1 and Table 23's caption
both already say 66 and 13. So the paper states the same comparison twice with
numbers from an earlier sample, and in a direction a reader cannot parse ("flags
a strict subset, seven … against four" reads as subset = 7 > 4).

**Fix.** `\NStageOneWin` against `\NRegionMaxFlag`, and 53 that drop out.
`\NRegionMaxFlag` is already checked by `reproduce_from_catalogue_v385.py`, so
the value is there for the taking.

---

### Q11 — three surviving claims that Table 23 audits every window the region form flags. MAJOR
**Evidence.** C6's fix corrected the caption, which now says the table gives
"the pairs either statistic promotes to stage 1, **not all 66 of them**". But:
- §1, line 192: "… and Table 23 audits **every window the region form flags**";
- §4.2, line 1028: "§G.4 gives the comparison and Table 23 audits **every window
  either form flags**";
- §4.2, line ~1051: "§G.4 compares the two forms and audits **every window the
  asymmetric one flags**".

The table has 10 data rows.

**Fix.** Three sentences: "Table 23 lists the star–band pairs either statistic
promotes."

---

### Q12 — the chance expectation takes five values; the abstract quotes the one the text says it does not use; Table 8 mislabels a row and omits two. MAJOR
**Evidence.** Values in the paper, all describing "how many unattributed stage-1
outliers chance produces":

| macro | value | what it actually is | where printed |
|---|---|---|---|
| `\BootPoisson` | 3.1 | 1614/513 — the *bootstrap's* window count | Table 8, row "Poisson, all windows"; §3 |
| `\ExpStageOneAll` | 3.2 | **1655/513**, the naive exchangeable Poisson on all windows (`v381_calc.py:123`, `EXP = N/(NCTRL+1)`, `N = len(ROWS)` = 1655) | **abstract**, §4.6 step 9, Table 12 caption, **conclusions**, Fig. 3 step 9 |
| `\ExpStageOneTail` | 3.9 | 3.2 × the hold-out tail factor | Table 8 |
| `\BootMean` | 4.4 | block-resampled, all windows | §5.3 |
| `\BootMeanA` | 1.1 | block-resampled, Class A | abstract, §5.3 |
| — | 3.7 | calibration-sample rate × 1322 windows | Table 13(a) |
| `\PseudoExpFlags` | 4.7 | measured empirical false-alarm rate × windows (`v361_calc.py:122`) | §5.3.6, §6.2 |

Three specific errors follow.

**(a) Table 8's third row is mislabelled.** It reads
`Calibration sample rate | \ExpStageOneAll | measured on data the criteria were
not tuned on`. `\ExpStageOneAll` is 1655/513 — the ideal-exchangeability Poisson
on the full survey, computed from the catalogue with no calibration-sample input
whatsoever. Meanwhile the row labelled "Poisson, all windows" holds 1614/513.
The two rows' contents are effectively swapped, and neither label describes what
it holds.

**(b) The abstract quotes the wrong estimator and mis-describes it.**
> "against **3.2 expected by chance over all searched windows** or 1.1 over the
> drift-resolving ones alone"

3.2 is not the all-window figure the paper endorses — §5.3 says "Counting every
searched window as eligible … **4.4**" and Table 8 says "the block-resampled
figure is the one the text uses". So the abstract pairs a naive Poisson (3.2)
with a block-resampled Class A figure (1.1): two different estimators, side by
side, one mislabelled. The conclusions (item 2), §4.6 step 9, Fig. 3 step 9 and
Table 12's caption all repeat 3.2. `S3/S10`'s disposition says the fix was "both
reference classes now reported: 4.4 … and 1.1"; the fix reached §5.3 only.

**(c) Table 8 is incomplete on its own terms.** Its caption says it gives "The
chance expectations **quoted in this paper**". It omits 1.1 (quoted in the
abstract), 3.7 (Table 13) and 4.7 — and 4.7 is the figure the Discussion uses in
its most quotable sentence: "a genuine but weak transmitter seen in one epoch is
not separable from the **4.7 chance events the survey expects**".

**Fix.** Decide on one estimator per reference class, use it everywhere
including the abstract and Fig. 3, make Table 8 exhaustive with correct row
labels, and retire `\ExpStageOneAll` or rename it `\PoissonAllWin`. The
generator comment in `v381_calc.py` ("This is the comparison the paper has
always made; on 1956 windows …") is itself a fossil of an earlier sample size.

---

### Q13 — the two trial denominators are swapped in §3. MAJOR
**Evidence.** §3:
> "The 1655 rows comprise 1616 distinct (execution block, spectral window)
> datasets. **We use the larger number as the trials denominator throughout**,
> which is conservative and makes no practical difference: **it predicts 3.1
> chance outliers against 3.2 for the smaller.**"

1655/513 = 3.23 → 3.2 (the larger); 1616/513 = 3.15 → 3.1 (the smaller). The
sentence attributes each to the other. §4.1, on p. 9, gets it right: "The
survey-level flag expectation uses 1655 windows, which is conservative because
the 1616 distinct datasets are the smaller number."

**Fix.** Swap the two numbers, or better, print them as
`\NWindows/\RankFloor` and `\NDistinctWin/\RankFloor` so they cannot be
transposed.

---

### Q14 — the block-resampled null runs on 1614 windows and 394 Class A windows, printed beside 1655 and 403. MAJOR
**Evidence.** `blockboot_v385.json`: `n_windows: 1614`; `\BootWinA` = 394. §5.3
prints both:
> "95 per cent interval 1–9 over 404 blocks and **1614 windows**"
> "On that set the expectation is 1.1 over **394 windows**"

The loss comes from `blockboot_v385.py`'s key, `(eb, round(min(flo,fhi),4))`,
which is not unique over the catalogue: 1655 rows collapse to 1616 keys (35 keys
carry 2 rows, all of them the two-target fields of Q7), and two further windows
fail the `key not in CAT` test. So the reference class silently drops one
component of every bound pair plus two more.

**Problem.** Three window counts (1655, 1616, 1614) appear in a paper that
carefully explains only two, and the observed count (4, taken from the full
catalogue) is compared against a null generated over a smaller set. The Class A
mismatch is the visible one: every other sentence in the paper says 403.
Numerically the effect is small (the expectation should be 4.4 × 1655/1614 = 4.5
and 1.1 × 403/394 = 1.13) but a referee will stop on "394".

**Fix.** Key on `(eb, flo, fhi, star_name)` so the bootstrap resamples the same
1655 units the paper counts, and assert `nwin == NWindows` and
`nwinA == NFine`.

---

### Q15 — "recovers β Pictoris in 7 windows at 5.9–9.5σ" double-counts HD 48370. MAJOR
**Evidence.** `visfit_v385_calc.py:49`:
```python
REC = [(k, v) for k, v in att if v['star']['snr_re'] >= 3.0]
```
`att` is *every* CO-attributed event, i.e. the eight β Pic windows **and
HD 48370**. `\NFitAttRecov` = len(REC) = 7; `\FitAttReLo` = 5.9 = HD 48370's
5.93. From Table 10 itself, the β Pic rows are +8.13, +9.52, +2.42, +6.12,
+8.01, +8.47, +6.34, +0.00 — **six** at or above 5.9, spanning **6.12–9.52**.

The manuscript uses these macros in four places, each time naming β Pic and then
naming HD 48370 separately:
- §5.3 (l. 1970): "β Pictoris is recovered at the stellar position in 7 windows
  at 5.9–9.5σ, **and HD 48370 at 5.9σ** …";
- Table 10 caption (l. 2029);
- §4.6 step 10 (l. 1644): "the estimator that recovers β Pictoris at 5.9–9.5σ";
- **conclusions item 2** (l. 3236).

The generator's own docstring says something different again: "beta Pictoris is
recovered in **7 of its 8** windows at **6.1–9.5** sigma" — also wrong, since one
β Pic window returns +2.42 ("nothing at the star") and one is unreachable, so it
is 6 of 8.

**Problem.** The paper's strongest new evidence — the positive control that makes
the null on the four unattributed events believable — is overstated by one
window, and the lower end of its dynamic range belongs to the event the same
sentence classifies as *displaced*. In the conclusions this is the sentence a
reader will quote.

**Fix.** Split `REC` into `REC_BPIC` (`k.startswith('bet Pic')`) and the
HD 48370 case; emit `\NFitBpicRecov` = 6, `\FitBpicReLo/Hi` = 6.1/9.5, and keep
`\FitHdFortyRe` for HD 48370. Assert `NFitBpicRecov + 1 + NFitAttUnreachable +
len(bpic_null) == len(att)`.

---

### Q16 — Table 11, Table 13, Table 14 and Fig. 8 give conflicting repeat-block statistics. MAJOR
**Evidence.**

| event | Table 11 "repeat blocks" | Table 13(b) "T⋆ at the same tuning, further block" | Table 14 | Fig. 8 caption |
|---|---|---|---|---|
| CP−72 2713 | **4.70** (`\CpTstarTwo`) | **3.60** (`\CpRecT`) | **4.70** | **3.60** ("the star falls to 3.60") |
| 61 Vir | 4.83 | 4.83 | — | — |
| HD 14055 | **5.42** (`\UnattRepeatMaxT`) | **5.51** (`\CampUnTwoRepT`) | — | — |
| HD 23484 | 4.99 | 4.99 | — | — |

Two separate problems.

**(a) HD 14055 breaks a maximum.** §5.3 states "Across all 23 repeat windows the
largest stellar statistic is **T⋆ = 5.42**". Table 13(b) and §5.3.1 both report
**5.51** for HD 14055's repeat. A maximum cannot be smaller than a member.
`\UnattRepeatMaxT` comes from the rebuilt `_repeat_blocks()` (S1);
`\CampUnTwoRepT` comes from the older campaign generator. Both are in the paper.

**(b) Table 13(b) is not computed consistently across its own four columns.**
For CP−72 2713 the entry is the *pinned-channel, drift-maximised* value (3.60);
for the other three it is the window maximum. The column header — "T⋆ at the
same tuning, further block" — is the same for all four. That is the
numerator/denominator-mismatch family: four numbers in one row of one table,
three of them one quantity and one of them another.

**(c) The reader sees two values for the same cell.** Table 14's caption says
"A source at the first block's flux would have returned T⋆ = 6.21 there; **the
measured value is 4.70**", while Fig. 8, on the facing column, marks
"T⋆ epoch 2 = **3.60**". The distinction (window maximum vs pinned cell) is made
in the §5.3.6 prose but never attached to either number.

**Fix.** Regenerate `\CampUn*RepT` from the same `_repeat_blocks()` the S1 fix
built; label Table 13(b)'s row "largest T⋆ in any repeat block at this tuning"
and use that quantity for all four; and in Table 14 print both the window
maximum and the pinned value with their labels, since the argument uses the
pinned one.

---

### Q17 — §5.3.6 still says CP−72 2713 is the only one of the four with a second epoch. MAJOR
**Evidence.** §5.3.6, first paragraph:
> "It is one of the 4 unattributed stage-1 outliers of the completed sweep, and
> **the only one with a second epoch**."

Against §5.3, four pages earlier:
> "**All four have a persistence test, and all four fail it.** Each has at least
> one further execution block of the same star whose tuning covers the event's
> frequency: 1 to 16 of them, 23 in total."

This is the exact claim `S1` identified as false ("the paper had been
understating its own strongest evidence") and withdrew. The withdrawal reached
§5.3 and Table 11 and not §5.3.6.

**Fix.** "…and the only one whose repeat block matches it in tuning, channel
width and integration count" — which is true, and is the reason §5.3 gives for
examining it in detail.

---

### Q18 — the widened drift grid covers "5 windows" in one place and "56 windows" in another. MAJOR
**Evidence.** §4.5: "the generic value everywhere except the **56 windows** where
a known planet's own bound raises it." §6.4: "The grid takes 2 values, the wider
one used for the **5 windows** of TRAPPIST–1 alone."

Catalogue: `a_max_m_s2` takes exactly two values, 3.598 (1599 windows) and 3.999
(**56** windows, all TRAPPIST-1). `make_fig_accel2d.py:43` filters
`search_class == 'A'` before computing `\AccelNWide`, so 5 is the Class A subset.

**Problem.** Both sentences say "windows" without qualification, and they differ
by ×11. A reader concludes TRAPPIST-1 contributes 5 windows to the survey; it
contributes 56.

**Fix.** "the 5 Class A windows of TRAPPIST-1" in §6.4 (the appendix is about
the drift grid on the fine-channel search, so the Class A restriction is the
right one) — or emit two macros and use each in its place.

---

### Q19 — Table 12 prints ν = 0.0000 GHz, and the Δv for those rows is meaningless. MAJOR
**Evidence.** `tab_flagged_v380.tex`:
```
β Pic    & 3 & 5 & 0.0000  & 30.76 & 7.34 & -28    & circumstellar CO
61 Vir   & 7 & 1 & 0.0000  &  6.16 & 5.88 & +449   & unattributed
HD14055  & 7 & 1 & 0.0000  &  6.03 & 5.96 & -12161 & unattributed
HD 23484 & 6 & 1 & 0.0000  &  5.30 & 5.25 & +328   & unattributed
```
The caption calls the column "ν the crossing channel". The catalogue's
`f_cross_GHz` is empty for these rows (the pipeline stored a peak for only four
of the thirteen), and the generator formats the empty value as `0.0000`.

Table 11, describing the same four events, handles this correctly with a
footnote: "the released crossing frequency is stored only where the pipeline
recorded a peak; for these the window is given instead." Table 12 does not.

**Second half.** The Δv column for the no-peak rows derives from
`line_offset_kms`, which is itself computed against the nearest catalogued
transition irrespective of distance: for HD 14055 the nearest line is CO(3−2) at
345.796 GHz, 14.03 GHz away from a 330.4–332.2 GHz window, hence **−12 161
km s⁻¹**. The caption then states the disposition rule as "|Δv| ≤ 50 km s⁻¹",
inviting the reader to apply it to a column in which three of the four
unattributed entries are meaningless by construction.

**Fix.** Print the window range with Table 11's footnote, and blank Δv (or print
"no line in band") wherever the nearest transition lies outside the window. The
same guard should be applied to the released `nearest_line` /
`line_offset_kms` columns, which currently name a line 14 GHz away.

---

### Q20 — the recovery-fraction bracket multiplies a probability by a power ratio. MAJOR
**Evidence.** `v352_calc.py:655`:
```python
BRA_LO = StratTransferLo   # 0.64   -- a multiplier on P50
BRA_HI = StratTransferHi   # 1.13
for macro, src in (('RecTwice','RecTwice'), ('RecThresh','RecThresh')):
    v = texval('survey_numbers.tex', src)        # 42, a per cent recovery
    M(macro+'BraLo', '%.0f' % min(100.0, v * BRA_LO))    # 27
    M(macro+'BraHi', '%.0f' % min(100.0, v * BRA_HI))    # 47
```
Printed in §4.5 and §5.5: "nominal trigger thresholds whose measured recovery is
42 per cent, **27–47 per cent** under the measured 0.64–1.13× transfer."

**Problem.** `\StratTransferLo/Hi` is the window-to-window spread of $P_{50}$ —
a ratio of *powers*. Multiplying a *recovery fraction* by it has no defined
meaning; the correct operation is to re-evaluate the measured recovery curve at
a threshold scaled by that factor, which is strongly non-linear near 42 per cent
and cannot be obtained by scaling the ordinate. The `min(100.0, ...)` clamp is a
tell: the author already noticed the expression can produce a probability above
1.

**Fix.** Evaluate the curve: `pX(curve(trials), threshold * 1/BRA_LO)` and
`... * 1/BRA_HI`, using the same `inject_curve` machinery the budget already
imports. If the curve cannot be evaluated there, quote the bracket in threshold
units ("the trigger power itself moves by ×0.64–1.13") and drop the derived
percentage range.

---

### Q21 — "would exclude 19 of 20 crossings" — 20 is a stale crossing count, presented as the total. MAJOR
**Evidence.** §5.3.7: "a full Splatalogue selection … would exclude
`\NCrossWithCat` of `\NCrossQueried` crossings" = **19 of 20**. §G.5 repeats:
"the same query at the `\NCrossQueried` crossing frequencies returns a
transition within 60 km s⁻¹ for `\NCrossWithCat` of them."

The survey has **75** crossings (`\NHitsA` + `\NHitsB`, both checked against the
catalogue by `reproduce_from_catalogue_v385.py`). `\NCrossQueried` = 20 lives in
a frozen macro file with no live generator; it is the crossing count of an
earlier release.

**Problem.** Exactly the "all N of the N where N is a subset" pattern round 3
flagged: the sentence reads as a statement about the survey's crossings, and it
is a statement about 20 of them. It is also the evidential basis for the claim
that "'coincident with a known molecular line' is not a binary property", which
is a good argument that deserves the current sample.

**Fix.** Re-run the Splatalogue cross-query on all 75 crossings and regenerate,
or say "of the 20 crossings in the frozen v3.5x list" and explain why the
current 75 were not re-queried.

---

### Q22 — two incompatible values for the mask's cost on the frequency union, ten lines apart. MAJOR
**Evidence.** §5.3.7, consecutive paragraphs:
> "a full Splatalogue selection would mask 75.1 per cent of the union against
> **`\MaskOwnPctUnion` = 0.75 per cent** here"
> "… intersected with each window and merged: **`\MaskUnionPct` = 4.1 per cent**
> of the unique-frequency union and 4.7 per cent of the window-summed gross
> bandwidth"

`\MaskOwnPctUnion` is `veto_cost(CAT.values())` in `v352_calc.py:714`, with
`MASK_HALF_KMS = 50.0` and the catalogue's own islands — i.e. nominally the same
quantity as `\MaskUnionPct`. They differ by ×5.5.

**Problem.** The comparison "75.1 per cent against 0.75 per cent" is the
paragraph's punchline and uses the smaller of the two; the accounting paragraph
uses 4.1, as does §5.5 ("removes 4.1 per cent of the union from the inference")
and §6.2. A referee comparing them will ask which is the mask's cost.

**Fix.** Establish which definition each uses (my reading is that `veto_cost`
applies the tube at rest frequencies without the per-system radial-velocity
displacement, and `\MaskUnionPct` applies it after displacement) and either
reconcile them or state both definitions explicitly at the point of use.

---

### Q23 — §5.1's Barnard's Star / Wolf 359 numbers are stale, and the ordinal is self-inconsistent. MAJOR
**Evidence.** §5.1, entirely hand-typed:
> "Barnard's Star and Wolf 359 are the **second- and fourth-nearest** stellar
> systems. … The nominal EIRP₅σ trigger thresholds are **6.2–6.9 × 10¹³ W** for
> Barnard's Star **over four windows** and **7.8–9.1 × 10¹³ W** for Wolf 359,
> with continuum upper limits of 0.575 and 0.453 mJy."

Catalogue:

| star | windows | EBs | `eirp_nominal_W` range |
|---|---|---|---|
| NAME Barnards star | **12** | 3 | **6.15e13 – 9.25e13** |
| Wolf 359 | **12** | 3 | **7.28e13 – 1.07e14** |

**Problem.** Both ranges and the window count are from an earlier release (4
windows = 1 block). This is a section whose entire purpose is to stake a
priority claim ("these appear to be the first"), so the numbers in it will be
cited.

The ordinal is also internally inconsistent: under the convention in which
Barnard's Star is second-nearest (α Cen counted as one system), Wolf 359 is
**third**; under the convention in which Wolf 359 is fourth (Proxima counted
separately from α Cen AB), Barnard's Star is **third**. No convention makes them
2nd and 4th.

**Fix.** Generate all four numbers from the catalogue; say "second- and
third-nearest" (or "third- and fourth-"), and state the convention.

---

### Q24 — Data Availability claims a catalogue column that is three-quarters empty. MAJOR
**Evidence.** Data Availability: the catalogue carries "… the crossing
frequency, the nearest catalogued transition, and **the disposition verbatim
from Table 12**."

Catalogue `disposition` column: 10 non-empty of 1655. The 13 stage-1 rows carry
`circumstellar CO` ×8, `foreground CO` ×1, `unattributed; absent in epoch 2` ×1
— and **empty strings for 61 Vir, HD 14055 and HD 23484**, which Table 12 labels
`unattributed`. `v342_calc.py:920` writes `DISPOSITION.get(key, '')`, and the
`DISPOSITION` dict has no entry for those three.

**Problem.** Three of the four events the whole paper is about have no
disposition in the released catalogue, while the release notes say they do. It
also means the one piece of machinery that reads dispositions programmatically —
`blockboot_v385.py`'s fallback `'CO' not in disposition` — is counting blanks
(see m12).

**Fix.** Write `unattributed` for those three rows, and assert
`sum(1 for r if r['stage1_flag']=='True' and not r['disposition']) == 0`.

---

### Q25 — `\NReproChecks` is build-state dependent: 41 in `make_all.sh`, 36 when a reader runs the script. MAJOR
**Evidence.** The PDF says "re-derives **41** of the paper's headline numbers".
Running `python3 reproduce_from_catalogue_v385.py` on the shipped tree, exactly
as the paper invites, prints:
```
reproduced from per_target_results_v3.85.csv alone: 36 pass, 0 FAIL, 5 skipped
  skip NCatFlagGlobal / NCatFlagLocal / LocAllFlagGlobal / RingThetaMin / RingThetaMax
      (macro absent -- retired or renamed)
```
The five macros are stripped by `retire_macros.py`, which runs *after*
`reproduce_from_catalogue_v385.py` in `make_all.sh`. So the count the paper
prints is the count before retirement, and the count a reader reproduces is the
count after. (`VPR_DISPOSITION` C71 itself records "now 36", i.e. the
disposition was written from the standalone run and the paper from the build.)

**Problem, two parts.**
1. A referee who runs the script gets a different number from the one in the
   paper, in the section whose point is that the numbers reproduce. This is the
   `\NRegenProducts` defect again: a claim about the build made where the build
   can only see one of its two states.
2. `\NReproChecks = len(PASS)` counts only passes, and `SKIP` is silent. Any
   macro that is retired or renamed drops out of the reproducibility claim
   without failing anything. Five already have.

**Fix.** Run `reproduce_from_catalogue_v385.py` *after* `retire_macros.py`, so
the shipped number is the reproducible one; and make `SKIP` non-empty a build
failure unless the macro is on an explicit allow-list, so a silently vanishing
check cannot shrink the claim.

---

### Q26 — Table 9's verdict column asserts what §5.3 and Fig. 7 explicitly withdraw. MAJOR
**Evidence.** `tab_visibility_v385.tex` row 8:
```
HD14055 & 7 & 13\,365 & $+2.5$ & $+3.2$ & 1.00 & $+1.1$ & displaced: phase inconsistent
```
§5.3, on the same spread:
> "A source centred on the star would leave the imaginary part at zero, so at
> face value that excess is displaced; **but** a phase-calibration residual or a
> small astrometric error produces the same signature … **The defensible
> statement is that at this significance the uniform test does not localise the
> excess, not that it has localised it away from the star.**"

Fig. 7's caption follows the text. Table 9 does not.

**Problem.** `O5/S16`'s fix reached the prose and the figure and not the table,
so the paper's table of record still makes a 2.5σ/3.2σ claim the text calls
indefensible. The verdict rule in the generator (`|Im| > 2.5 and Re ≥ 3.0`) also
fires here on `Re = 2.5 < 3.0` — i.e. Table 9's verdicts are produced by a
different rule from Table 10's, which uses the same threshold correctly.

**Fix.** Add a significance gate to the verdict function, or print "not
localised" for events whose real part is below 3σ. Both tables should use one
verdict function.

---

### Q27 — pointing enters the P90 budget as a symmetric error; it is one-sided. MAJOR
**Evidence.** `p90_budget_v385.py`:
```python
E_POINT = float(np.max(1 - np.exp(-4*log(2)*(POINT_ARCSEC/THETA)**2)))
...
('Pointing', '0.6" on axis', '$\\pm%.1f$' % (100*E_POINT), 'quadrature')
E_COMB = sqrt(E_FLUX**2 + E_DIST_TYP**2 + E_MC**2 + E_POINT**2)
```

**Problem.** A pointing offset can only *reduce* the response at the star, hence
only *raise* the power needed — the loss is $1-\exp(\cdot) \ge 0$ by
construction, and the code takes its **maximum** over windows. It is then
tabulated as `±1.9` and combined in quadrature as if it were a symmetric random
error. This is precisely the argument S7 made about atmospheric decorrelation
("it is not symmetric … and it belongs in the budget as a one-sided term rather
than in quadrature") — applied to one term of the new table and not to another
term of the same table.

There is a second, smaller inconsistency in the same four rows: the distance
term uses the *typical* value (`E_DIST_TYP` = 0.2 %, with `E_DIST_WORST` = 5 %
computed and discarded) while the pointing term uses the *worst case*. The
combined ±8 % therefore mixes a typical-case and a worst-case input.

**Fix.** Move pointing to the "carried separately" block as `+0/+1.9`, or use a
representative rather than maximal offset and say which. State that ±8 % is a
typical-case combination and quote `\BudCombWorst` beside it.

---

## Part C — MINOR findings

**m1 — Table 5 cross-references the wrong table.** Line 674: "Threshold
crossings … 75 windows (71 Class A, 4 Class B; `Table~\ref{tab:specclass}`)" —
`tab:specclass` is the spectral-class table (Table 4). Should be
`tab:flagged`/`tab:bothstats`.

**m2 — a median outside its own interval.** §5.3.2: "a star-clustered bootstrap
placing the median at 0.405 (95 per cent interval **0.42–0.46**)". See A.3. The
p. 20 version, 0.405 with 0.341–0.458, is fine; this one is not. Either the
interval belongs to a different median (the survey's 0.445?) or the median
belongs to a different bootstrap.

**m3 — trial-drift range off by one.** §4.3: "(2–**1944** across windows)" and
§4.2 "2–`\BpSixTrials`"; the catalogue maximum is **1945** (β Pic B6,
`A002_Xd9668b_Xa9df`). `\BpSixTrials` is read from one named β Pic B6 window,
which happens not to be the maximal one, and is then used as a range endpoint.
The accompanying claim "the largest being the … β Pictoris Band 6 window" is
true of the star and band but not of the printed value.

**m4 — `\VisStarSnr` reused for the continuum significance.** §G.5 and §5.3:
"the window's own stellar continuum is **10.9 mJy at 5.5σ**". 5.5 is
`\VisStarSnr`, the *narrowband* fit's significance, used three lines earlier for
the narrowband fit. `visfit_cp72_v358.json` contains
`"continuum_snr": 5.777`, which is never exported as a macro. The correct value
is 5.8, and using 5.5 makes the coincidence the argument rests on look tighter
than it is. Appears twice (lines 1988 and 4474). Emit `\VisContSnr`.

**m5 — Fig. 3 caption says "three denominators" and lists four**: "the
catalogued population, the 168-entry ALMA-covered work list, the ∼115 stars a
public field genuinely contains, and the 90 searched."

**m6 — "1 systems of 83"** (§6.1). `\CaseDetCoarseNow` = 1 in a hard-coded
plural.

**m7 — typo** "(D = 0.08, **p =< 0.01**)" in §5.3.1.

**m8 — species count inconsistent within one paragraph.** §5.3.7: "The mask
applied holds 17 transitions of **11 species**", then lists **9** entries (CO
isotopologues, HCN, HCO⁺, CS, SiO, SO, CN, H₂CO, [C i]), then "every JPL
catalogued transition of the **9 frozen species**". `\MaskNSpecNew` and
`\MaskNSpecOld` are both live; the text does not say they differ.

**m9 — Fig. 9's arithmetic.** "×2.29 for the spectral response … and then by
×1.2 from the injection campaign, so a value of 1 here is **×2.81** the trigger
power." 2.29 × 1.2 = 2.75. The true ratio is 2.29 × 1.227 = 2.81; quoting the
factor rounded to 1.2 and the product to 2.81 makes the sentence fail its own
multiplication.

**m10 — a survey statement on an unstated subset.** §5.3.2: "the **31** windows
whose star happens to fall inside the annulus have median rank 0.495, against
0.460 for the **727** that do not." 31 + 727 = 758, not 1655 or 1614. The
restriction (presumably windows with recoverable geometry) is never stated.

**m11 — three trial counts for "the injection campaign".** §4.4 "1200 trials
across six window configurations"; Table 7 "1200 injection trials … and 3 888
dwell trials"; Table 15 "**4032** trials, bootstrap"; Fig. 11 "the pooled curve
over **4032** trials"; Data Availability "the 1200 injection, 3 888 dwell and
4032 stratified trials". The budget's bootstrap is over the 4032 stratified
trials but the table calls the row "Injection statistics", which §4.4 has just
defined as the 1200. A one-clause label ("stratified campaign, 4032 trials")
fixes it.

**m12 — `blockboot`'s observed count works by accident.** 
```python
obs = sum(1 for r in _cat if r['stage1_flag']=='True' and not r['nearest_line'])
if obs == 0:                      # no line column: fall back to disposition
    obs = sum(1 for r in _cat if r['stage1_flag']=='True'
              and 'CO' not in str(r['disposition']))
```
The primary rule returns **0** for every build, because `nearest_line` is the
*nearest* transition and is always populated (Q19). So the number is always
produced by the fallback, a substring match for `'CO'` against free text, which
today counts the three blank dispositions of Q24 plus `'unattributed; absent in
epoch 2'`. It gives 4, which is right. A future disposition string containing
"CO" — e.g. "unattributed; CO excluded" — would silently drop an event from the
null. Replace both with `disposition == 'unattributed'` once Q24 is fixed.

**m13 — a float sentinel for "unmeasurable".** `visfit_v385_calc.py:45`:
`failed(v) = abs(snr_re) < 0.01`. A genuine null of 0.004σ would be relabelled
"track too wide to reference". The unreachable row is also still printed with
`Re/σ = +0.00`, `Im/σ = +0.56` and `ctrl = +1.53`, which reads as a measurement.
Carry an explicit status field and print "—".

**m14 — the same system under two names.** §6.1 calls it "the **UV Ceti** pair at
2.7 pc"; the catalogue, Fig. 4 and every table call it **G 272-61A/B**. UV Ceti
appears nowhere else in the paper and G 272-61 appears nowhere in §6. A reader
cross-matching the deepest threshold (1.6 × 10¹³ W) to the catalogue cannot find
it.

**m15 — `tab_driftstrata_v385` presentation.** (a) Row order within two axes is
low, high, middle ("<1/3, >2/3, 1/3–2/3" and "<150, >350, 150–350"). (b) The
`61.0 kHz` channel-width stratum has P50 = 3.0 / P90 = 4.6 against 5.8–6.5 for
every neighbour, on 288 trials, and is not remarked on. (c) `\PhaseStratWorst` =
2.02 is the *smallest* response correction (carrier at channel centre) and
`\PhaseStratBest` = 2.69 the largest, so the names are inverted relative to
their physical meaning and the printed range "×2.69–×2.02" runs backwards.

**m16 — a failing consistency flag ships in the release.**
`tables/table_numbers_v328.json` contains
`"csv_n_ctrl_ge_star_consistent": false`. I traced it: 409 rows of the frozen
export carry `ctrl_all` but a null `n_ge_star`, and the check treats null as a
mismatch. The released catalogue is fine (`n_ctrl_ge_star` is recomputed, and
`p_rank_addone == (1+n)/513` for all 1655 rows). But a reader who opens the
shipped numbers file finds a consistency assertion recorded as false, with no
note. Either fix the check to skip nulls or drop it.

**m17 — HD 207129 is described as both attributed and unattributed.** §5.3.2:
"the one that enters, HD 207129, is a debris-disc host whose crossing lies
−150 km s⁻¹ from CO(2→1) in the stellar frame, **the same disposition the paper
reaches for the other disc hosts**" — but −150 km s⁻¹ is outside the ±50 km s⁻¹
rule, and the next sentence counts it among the "**2 unattributed**" under the
corrected statistic. One of the two readings has to go.

**m18 — the released catalogue has no coordinates.** 50 columns, none of them
RA/Dec. Combined with Q7's opaque designations, a reader cannot determine which
object several rows refer to, and cannot independently check the
proper-motion-propagated positions the whole method rests on. Two columns would
fix it.

**m19 — a foreground cloud counted as a disc false positive.** §6.4: "9 of the
13 stage-1 outliers are molecular emission toward disc hosts, arising in **2 of
the 69** debris-disc systems searched". The two are β Pic and HD 48370, but
HD 48370's CO is identified throughout the paper as *foreground*, not
circumstellar — it is a disc host with an unrelated cloud in front of it. As a
statement about the false-positive rate an archive proposed for disc science
carries, that is the wrong attribution; the sentence's own figure
"one flagged system in 34" rests on it.

---

## Part D — things worth saying that are not defects

- §5.3's two-reference-class treatment, §5.3.1's commitment-ordering argument
  and §5.3.2's refusal to adopt the statistic that flatters the result are, in my
  view, the best parts of the paper and should not be softened in revision. The
  ×0.48–1.35 transfer uncertainty being named "the largest term in the budget by
  a factor of several" is the kind of thing most papers bury.
- The Table 10 / Table 9 pair is genuinely decisive evidence and reads well; the
  only thing wrong with it is Q15 and Q26.
- `reproduce_from_catalogue_v385.py` is the right idea. Its weaknesses (Q25, and
  that `chk('NStars', len({star_name}))` is circular because the same generator
  writes both sides) are fixable without giving up the idea.
- The prose is disciplined throughout. Almost every defect above is a *number*,
  not an argument.

## Part E — the one structural recommendation

Every MAJOR in Part B except Q13, Q19, Q20 and Q27 is an instance of the same
mechanism: **a quantity that exists twice.** Twice in two generators (Q5, Q6,
Q16), twice as a macro and a literal (Q9, Q10, Q21, Q23), twice as a figure and
a caption (Q1, Q2), twice under two definitions with one name (Q12, Q14, Q18,
Q22), or twice in a table and the text that withdraws it (Q11, Q17, Q26).

Three checks would have caught most of them and none exists yet:

1. **A prose-literal sweep.** After the build, extract every numeric token in the
   `.tex` body that is not inside `\newcommand`, not a citation year, and not a
   float placement; compare against the macro set; fail on any exact match to a
   macro value or to any value in a *previous* version's macro set. Q9, Q10,
   Q21, Q23 and m3 are all bare literals that once were current.
2. **A figure/caption agreement check.** The build already extracts figure text
   with `pymupdf` (`audit_figures_v372.json`). Extend it: any integer appearing
   in a figure's text layer that also appears in its caption must match, and any
   figure legend of the form `(N stars)` must equal `\NStars`. Q1 and Q2 die
   here.
3. **One name, one definition.** Make `star_alias` the only route to
   `star_name`, and add the identity check of Q6. Then extend
   `reproduce_from_catalogue_v385.py` with `NStarBands`, `NTeffStars`,
   `BootWin`, `BootWinA`, `NSysOneEB`, `NAccelPlanet` and the Table 3 partition
   row — each of which is derivable from the catalogue and each of which is
   currently wrong or ambiguous.

---

*Report prepared by an independent reviewer pass, v3.85, 2026-09-21. No
manuscript, product or generator file was modified;
`survey_numbers_round39.tex` was rewritten by executing the shipped
reproducibility script and was restored to its pre-run contents.*
