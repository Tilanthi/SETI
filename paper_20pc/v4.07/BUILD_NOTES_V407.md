# v4.07 build notes — the census name collision, and the star-blind overwrite behind it

**Built 2026-09-27 from v4.06 (`0386e357a56a`).** **52 pp, main text 19.69 pp** (appendix starts p. 21), unchanged from v4.06: the new prose is
one paragraph in the provenance appendix. The 15-page cap remains
**deliberately broken**, per Glenn's standing directive that page length is deferred until the
science is settled: length was **measured and not optimised**.

| gate | result |
|---|---|
| pages | **52**; main text **19.69 pp**; appendices 31.14 pp |
| pdflatex | **0 errors, 0 undefined refs/cites, 0 multiply defined, 0 overfull**, 67 underfull |
| Type 3 fonts | 0 |
| `roundcollide` | **90 / 90**, 0 problems |
| `macrosyn` | 0 problems (9 declared open divergences unchanged) |
| `consistency_v399` | 0 problems |
| `prosenum_v399` | 0 literals disagreeing with a macro |
| `macroleak` | 0 problems |
| `intsweep` | **81 integers in running prose, 81 registered, 0 stale, 0 problems** |
| `audit_numbers_v385` | **49 PASS / 0 FAIL**, 10 warn, 7 skip |
| `reproduce_from_catalogue_v385` | **22 pass / 0 FAIL**, 19 skipped |
| **`census_dupcheck_v407` (new)** | C1 3 collision groups, all < 3 arcsec; C2 **0** of 1,616 physical windows; C3 **0** of 1,651 rows; C0 lambda = 0.112 |
| `selftest_v403` | 26 checks, 20 demonstrated failing |
| `selftest_v404` | 46 / 46 demonstrated failing |
| `selftest_v405` | 60 / 60 demonstrated failing |
| `selftest_v406` | 65 / 65 demonstrated failing |
| **`selftest_census_v407` (new)** | **29 / 29 cases as specified** |
| `cleanregen` | **136 / 136 byte-identical** |
| arXiv abstract | 1884 rendered chars, 302 words (limit 1920, headroom 36) |

New in this version: `censusfix_v407.py` (applied inside `corrected_export_v399.py`),
`censusrep_v407.py` (round 100), and the two gates `census_dupcheck_v407.py` and
`selftest_census_v407.py`. Changed: `build_ranked_master40pc.py` (outside the version
directory, copy deposited in `census_fixtures/`), `v342_calc.py`, `corrected_export_v399.py`,
`fieldfix_v404.py`, `make_tables_v328.py`, `canon_names_v381.py`, `make_fig_sample.py`,
`star_alias.py`, `survey_stats_systems.py`, `survey_stats_round10.py`, `make_all.sh`.

---

## 1. ★★★ The defect is not a duplication. It is a misattribution, and it deleted a crossing.

The round-8 audit (`referee_r8/CENSUS_DUPLICATES.md`) read `HD 139084B [921024]` /
`HD 139084B [805632]` as one star entered twice, and prescribed: delete four duplicate rows and
rescale the survivor's EIRP by ×1.03078. **Both halves of that are wrong, and the evidence was
inside this deposit the whole time.**

- **The two entries are two different stars.** SIMBAD TAP, queried live: Gaia …921024 has
  pm (−54.602, −92.786) and ϖ = 25.829 → **HD 139084 = V343 Nor A, K0V, SB\***; Gaia …805632 has
  pm (−50.334, −100.036) and ϖ = 25.4404 → **HD 139084B, M5Ve**. Separation measured from the
  census's own coordinates: **10.32″**, against **0.44″, 1.40″ and 1.55″** for the three
  collisions in this census that really are one star with two Gaia solutions. A 7× gap, which is
  what makes a 3″ tolerance a usable rule rather than a guess.
- **Both were extracted, separately, at their own positions.** `/data/SETI/targets/` holds
  `HD_139084B_805632_B7` and `HD_139084B_921024_B7`, primary-beam offsets **5.092″ and 5.208″**,
  and their statistics differ in all four windows: T\* = 2.343 / 2.718 / 2.468 / **5.663** against
  2.405 / 2.491 / 2.330 / 4.153.
- **The release carries the primary's measurement under both names.** All four released
  `star_snr` values are the …921024 numbers, and the shared EIRP was computed at 38.7162 pc =
  …921024's distance. So the **EIRP is correct and the distance label is wrong**, the opposite
  of the audit's reading. Rescaling by 1.0308 would have published the K0V primary's data as an
  M5Ve limit.
- ★★★ **The mechanism is in this paper's own code.** `corrected_export_v399.py` matches the
  re-extraction harvest on `(eb, flo, fhi)` **with no star**, and `acafull_v399.json` carries no
  target field at all, so a product cannot be attributed to a star even in principle. The
  `n_amb` guard fires only when the harvest holds *two* products for a window; here it held one,
  for one of the two stars, and it was written onto both rows.
- ★★★ **It deleted a counted crossing.** `per_target_results_v3.81.csv`, `v3.84.csv` and
  `v3.72.csv` — all three shipped in this deposit — carry **HD 139084B …805632 at 345.1449 GHz,
  T\* = 5.6634, `crossing = True`**. `frozen_export_v3.81_survey.json` and
  `pipeline_peakfreq_v342.json` carry both extractions correctly. After v3.99 the crossing is
  gone from the catalogue. The same release moved the crossing count 75 → 56 for a dozen other
  reasons, so nothing reported it.

**Blast radius, measured:** 35 physical windows of the survey contain more than one catalogued
star; **31 were never re-extracted, and only this field had one product for two stars**, so
8 rows in 4 windows are affected and nothing else in the release is. ★★ But
**`fieldfix_v404.apply()` carries the identical star-blind key**, so the defect was armed for the
queued 42-block re-extraction: any multi-star field among the 42 would have been overwritten the
same way, silently.

## 2. What v4.07 ships, and what it deliberately does not

**Ships:** the census rename at its generator; the four rows kept **once, under `HD 139084`, at
38.7162 pc, with the EIRP untouched**; the seven corrected counts; the disclosure paragraph; and
three tripwires plus the multi-star overwrite guard.

**Does not ship, and it is a decision for Glenn / ASTRA, not for a presentational version:**
restoring HD 139084 B. The correct data state is to re-extract the companion under the corrected
control geometry from `A002_Xcd8029_Xb6b0` (the data are on disk, four windows), after which
`\NStars` returns to **90**, `\NWindows` to **1655**, and **the crossing count becomes 57**. That
crossing is 24.3 km s⁻¹ from CO(3−2), its own control ring reaches 17.65σ and `p_rank` = 47/512 =
0.094, so it is rank-screened, cannot become a candidate, and puts nothing about the null result
at risk — but it is a result-bearing count, and restoring the frozen row instead of re-extracting
would mix two control geometries inside one field, which is the referee's own objection.

## 3. The seven corrected counts, and the claim that nothing result-bearing moves

| macro | v4.06 | v4.07 |
|---|---|---|
| `\NStars` | 90 | **89** |
| `\NWindows` / `\NCatRows` / `\TuNWinAll` | 1655 | **1651** |
| `\NWinA` / `\NFine` | 403 | **402** |
| `\NWinB` / `\NCoarse` | 1252 | **1249** |
| `\NStarBands` | 113 | **112** |
| `\NWinTwelveM` | 601 | **597** |
| `\NStarTwelveM` | 70 | **69** |
| on-source hours | 1095.7 | **1094.2** |

**Verified independently, not assumed** (column-by-column diff of the released catalogue against
v4.06, 1,651 rows matched on the physical window):

- `\NSystems` **82**, `\NSysClassA` / `\NSysUnionA` **60**, crossings **56**, `\SbrN` **14**,
  `\NFlagged` **12**, `\NEB` **404**, the union bandwidth **118.1252 GHz**, `\NExoHostsTab` **23**
  and `\NExoPlanetsTab` **50**, the habitable-zone list and every per-system median: **unchanged.**
  The pair was already collapsed into one system by `star_alias.PAIRS`, which is why.
- Exactly **three** catalogue columns move: `star_name` and `system_id` on the four retained rows,
  and `trigger_1pct_survey` on 1,637 rows in the fourth decimal (5.4263 → 5.4259 at Proxima),
  because D16's survey-wide requirement depends on the total cell count and the survey now has
  four fewer windows. Nothing else in any of 60 columns changes anywhere.
- ★ The prose says the searched entries "comprise `\NSystems` systems, differing by seven
  designation-linked component pairs". 90 − 82 = 8; **89 − 82 = 7**. The repair makes the paper's
  own arithmetic close, where before it was off by one.

## 4. The repair, at the generators

1. **`build_ranked_master40pc.py`** (the census builder, outside the version directory; a copy is
   deposited in `census_fixtures/`). A display-name collision may be disambiguated by Gaia digits
   only if the members span less than **3″**; a wider one must be declared in
   `FIELD_NAME_COLLISIONS` with each member's externally resolved identity, and the declared name
   replaces the field name outright. An undeclared wide collision **stops the build**. The
   regenerated census is **byte-identical to the audit's repaired file**, and the builder
   reproduces v4.06's census byte-identically before the change — so the diff is exactly two
   names.
2. **`censusfix_v407.py`**, applied inside `corrected_export_v399.py` beside `fieldfix_v404`, for
   the reason recorded there: `v342_calc.py` rebuilds the catalogue from the export on every
   build, so a patch to the CSV is discarded, and `apply_holdout_v381.py` writes the export, so
   the repair cannot live upstream either. It renames both members, **computes** which star was
   measured, drops the other copy, repairs the export's embedded census list, and re-checks the
   EIRP ↔ distance identity on **every** remaining row.
   ★ **The attribution is computed, not declared**: the retained row is the one whose `dist_pc`
   reproduces the distance implied by the row's own EIRP, `d = √(EIRP / K S Δν)` with
   **K = 4π pc² × 10⁻²⁶ computed from first principles** — a constant fitted to the rows it then
   tests would make the check unfailable. Measured/theory = **1.00000000**; the identity holds on
   1,721 of 1,725 export rows to 4 × 10⁻¹⁶ and failed on exactly the four rows at issue, so the
   answer to "does any other row carry another star's EIRP" is **no, zero**.
3. **`v342_calc.py`**: the `(star, eb, window)` join into `pipeline_peakfreq_v342.json` is
   canonicalised on both sides. ★ **This is the defect the repair itself caused in its first
   build**: the pipeline's target directories carry the name as it stood when the search ran, so
   renaming a star silently left `n_int` blank, and with it `eta_smear`, `eirp_eff_total_W` and
   `c_response_smear` — the project's blank-field bug family, sixth instance. The number of
   searched windows with no integration count is now **pinned at 1,200 with `==`**, not bounded,
   so both a broken join (it rises) and a silent upstream repair (it falls) fire.
4. **`corrected_export_v399.py` and `fieldfix_v404.py`**: a harvest product may not be applied to
   rows of more than one `star_name` unless the case is declared, naming the star it belongs to
   and what becomes of the others. In `fieldfix` the requirement is stronger — the harvest must
   carry a target field — because that is the applier the queued campaign runs through.
5. **`make_tables_v328.py`, `canon_names_v381.py`, `make_fig_sample.py`**: the census is now read
   **from the deposit** instead of `/workspace/SETI/ranked_master40pc.csv`, with an assertion that
   refuses a path outside the version directory. ★ That hole had already opened: v4.06 regenerated
   the census into the version folder and left these three pointing at the older copy outside it,
   so the build read **two different censuses** and nothing said so. Repointing restores one
   searched star to the selection table (all **89** matched, `T_eff` for **53**, K class **6**),
   which the stale census had silently dropped. `canon_names_v381.py` also carries the audit's
   repointing of its deleted `v3.72` input, so it can run at all.
6. **`star_alias.py`** (and the two copies of `PAIRS` in `survey_stats_systems.py` and
   `survey_stats_round10.py`): the bound pair is written under the repaired names, and both
   pre-repair strings are aliased onto them, so a stale string self-heals instead of becoming an
   83rd system. The hold-out assignment and the survey split are **byte-identical** after the
   change, verified.

## 5. The tripwires, and both directions

`census_dupcheck_v407.py` — three always-strict checks, no lenient mode:
**C1** a census display-name collision wider than 3″ must be declared with an externally resolved
identity; **C2** within a physical window no two rows may agree in every column except
`star_name`/`dist_pc`; **C3** every row's `eirp_nominal_W` must be consistent with the `dist_pc`
printed beside it. **C2 and C3 are independent routes to the same defect**, so silencing one still
leaves the other firing — and C3 alone catches the case C2 cannot: dropping the duplicate row and
leaving the wrong distance behind. `C0` is not a check but a calibration: a permutation null gives
**λ = 0.112** chance `(eb, star_snr)` collisions over 2,678 within-block pairs, so **a single such
collision is a 1-in-10 event and proves nothing**; the evidence was full-row identity.

`selftest_census_v407.py` — **29 cases, 29 as specified**, in three groups: the checks in process
on the **actually published** pre-repair census and catalogue rows (deposited in
`census_fixtures/`); `censusfix_v407.apply()` on a reconstruction of the row set the build hands
it, which is itself verified against those published rows; and source perturbations of the two new
generator assertions, run in a subprocess with writes redirected by a shim on `builtins.open`.
★ **The two cases that matter most**: swap which distance the shared EIRP implies and the module
keeps the **other** star and trips its declaration cross-check; change the declaration to match
and it passes with the other star retained. Without that pair, "the retained row is the one the
EIRP was computed for" would be a claim rather than a check. Also driven: the pin lowered by one,
the canonicalisation reverted to the pre-v4.07 code, the declaration undeclared, the
first-principles constant moved 1 %, an unrelated window duplicated under a second name (so no
check is hard-wired to this star), and the eight genuine multi-star fields required to survive.

## 5a. Two stale prose claims the moved counts exposed, and one that came right

- ★★ **`\ClustPobs`: the paper said the clustered and Poisson tails "coincide to three
  significant figures", and after four windows left they are 7.0e-6 and 7.6e-6.** The
  assertion did not catch it because its tolerance is **15 per cent** — the CLAIM and the
  CHECK were different numbers, so the prose quoted a precision nothing tested. The
  generator now emits the **measured** agreement (`\ClustPoisAgreePct`, `\ClustPoisRatio`)
  and the sentence quotes that. Eighth instance of this family in three days, and the first
  where the check was *looser* than the claim rather than unfailable.
- ★ **`\CcMedEirpShiftPct` 0.22 -> 1.71 per cent.** Not an error: with an odd number of rows
  the per-window median is a single order statistic, and the mis-keyed window now sits on the
  other side of it, so the median steps to the adjacent window. The sentence said the shift
  was "far below the precision quoted anywhere"; it now says what actually happens.
- ★ **`\NExoBlankFlag` 139 -> 96, and 96 is the right number.** That macro is the count of
  census rows with a blank `is_exo_host`, i.e. the evidence for the defect the exoplanet-host
  correction repaired. 139 was the count in the **stale external census**; the deposited one,
  regenerated at v4.06 with an explicit flag for every created row, has 96. The paper was
  quoting a property of a file it does not ship. Repointing the reader fixes it.
- ★ `\EirpMedian` 7.2 -> 7.1e14 W is the only published headline whose printed digit moves:
  the true value goes 7.1734 -> 7.1157e14, a 0.8 per cent shift that happens to cross the
  rounding boundary at 7.15.

## 6. Noticed, out of scope, not changed

- **`make_tables_v328.py` prints `n_starbands tables=116  survey_stats=112  MISMATCH`** and does
  not assert on it. Pre-existing (116 vs 113 at v4.06): the census-side count uses the
  `alma_bands` column, the catalogue-side count the searched windows. One of them is wrong.
- **`acafull_v399.json` and the round-8 harvest carry no target field.** The guards added here
  refuse to apply a product blind, but the real fix is in the harvester.
- `\CampUnOneT` remains a pre-repair record (flagged at v4.04, v4.05, v4.06).
- `make_fig_sample.py` is still an orphan (eight dead figures ship in the deposit);
  `tab_visibility_v384/v385.tex` still write `HD14055`.
- The census entry for HD 139084 B keeps `status = needs_redo`; it is **covered but unsearched in
  this release** and belongs on the host queue behind the P90 campaign and the CP−72 refit.

## 7. Not in this version

- **Restoring HD 139084 B**, and with it the 57th crossing (§2). Decision pending.
- **The P90 refresh.** P90_PLACEHOLDER
- **R2-6** (the geometry column, the N_eff reconciliation); **R2-10's** Table 24 deletions and
  appendix re-lettering; **R1-8**; the 51st visibility fit; the closure-phase RFI record;
  `\CampUnOneT` re-measured; retiring `visfit_v385_calc.py`.
- **The matched filter is still deliberately not applied** (D16), and the trigger is still
  deliberately 5σ.
- **Page length**: measured, not optimised, by standing instruction.
