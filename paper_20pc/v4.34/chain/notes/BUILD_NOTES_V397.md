# v3.99 — two referee reports

**Built 2026-09-23.** 42 pp. Gates: 0 errors, 0 undefined refs/cites,
0 multiply-defined, 0 overfull, 0 misplaced labels, `roundcollide` 59/59,
`prosenum` 0, `macroleak` 0, `consistency` 0. Abstract 1918/1920.
Clean regeneration **82/82 byte-identical**.

Done entirely by hand, no subagents, at Glenn's instruction.

---

## Four errors of ours that the referees caught

### 1. A regression I introduced in v3.96: the `\appendix` command was gone
Referee 2 (M8): *"Sections 8–20 follow the Conclusions but are numbered as
main sections, cited as 'Appendix 12', and have sub-sections numbered
'10.0.2'."* Checking v3.94 → v3.99, the `\appendix` command was present
through v3.95 and **absent from v3.96**: my deletion of the "About this
paper" section in v3.96 used `s.index('\section', i+10)` as the end anchor
and swallowed the `\appendix` line that sat between. Restored; appendices
now letter **A–E**, and six orphan `\subsubsection`s promoted so no label
prints as `C.0.1`. Verified: 0 labels now print `X.0.Y`.

### 2. The line-mask percentages were computed on two different masks
Referee 2 (S1): 0.9 % of the Class A union and 0.3 % of Class B *"cannot be
reconciled with 4.1 per cent of the total union"*. Correct. `MaskPctA/B`
were built in `v381_calc.py` from `_LAB`, a stale list of **8 transitions**,
while the adopted mask — and `MaskUnionPct` — uses **17 transitions of 11
species** at database precision. The per-class cost is now computed in
`v361_calc.py` on the adopted tube set:

| | old (8 transitions) | **correct (adopted mask)** |
|---|---|---|
| Class A union | 0.9 % | **7.4 %** (3.53 of 47.7 GHz) |
| Class B union | 0.3 % | **3.1 %** (2.84 of 90.5 GHz) |

The Class A mask cost was understated **eightfold**. The claim that the
fine-channel experiment "pays three times the fractional price" is now the
computed `MaskPctRatioAB` = **2.4**, and the text states why the parts
exceed the total (the classes overlap in frequency).

### 3. The abstract quoted a positive-control range that included a
    *displaced* source
Referee 2 (minor 1): 5.9σ is HD 48370, which this paper classes as
displaced. My `visgain` generator selected "at the star" by a numeric cut
(Re/σ ≥ 5), sweeping it in. It now selects on the table's **verdict
column** and asserts every such row exceeds 6σ. Range corrected to
**6.1–9.5σ**, matching §5.2.1. The null set is likewise restricted to the
unattributed events, so `VgNullMax` is again 0.93 and not a β Pic window.

### 4. Two generators computed the same headline median differently
Referee 2 (minor 2): 1.4 × 10¹⁵ W in the abstract against 1.5 × 10¹⁵ W
everywhere else. `sensdist` reconstructed P₉₀ as
`eirp_eff_total_W × PNinetyOverTrig`, which is ~2.4 % below the catalogue's
own stored `eirp_p90_W` that `v381_calc` uses. Now built from the stored
column with the same median convention, and **cross-asserted against
`PromoteSysMedA`** so the two can never diverge again.

---

## Other required changes

| Item | Action |
|---|---|
| R2-M6 | **RFI allocation statement corrected.** "Above every allocated terrestrial service" was false: RR Article 5 carries active allocations throughout 90–275 GHz and WRC-19 identified parts of 275–450 GHz. New `rfialloc_v399.py` answers the specific question and **asserts** it: 1 of 1655 windows overlaps the 94.0–94.1 GHz EESS (active) cloud-radar band, with **0 crossings and 0 stage-1 events**, so no overpass timing needs checking |
| R2-M7 (part) | White (2026, submitted) removed entirely — text and bibliography. Hallinan (2015) and Moór (2020) were uncited bibitems; removed |
| R2-M8 | `\appendix` restored (above); version history removed from §4.1, §4 and §5.2; commit-hash/script-name/seed/build-date provenance removed from six places; "byte for byte" claim dropped from the text |
| R2-S3 | **Imaginary-part argument corrected.** The real part carries the detection; the imaginary part is a discriminant against *displaced* emission only, since for pure noise it is centred on zero whether or not a source is present |
| R2-S6 | One statement of commensurability: limits are commensurable as total powers for a sub-channel carrier, but channel widths differ by ~7 decades. "Not comparable" removed |
| R2 minor 3 | One frequency (~30 GHz) throughout; and the honest comparator stated — against the only prior millimetre search the increase is **×9**, not two orders of magnitude |
| R2 minor 27 | Missing unit supplied: a *factor* of 388–743 in noise |
| R2 minor 28 | "factor of 106" → "approximately 106 (about one hundred, not 10⁶)" |
| R2 minor 30 | **Star designations cleaned.** Our own repair table had the **wrong sign** — WD 0407**+**179, not −179. New `display()` in `star_alias.py` fixes signs, strips target-ID suffixes (696000, 805632, 384128 …) and normalises case, applied to figure labels. Verified in the figure PDF |
| R2 minor 33 | Gaia DR3 → Vallenari et al. (2023) already done in v3.96; uncited references removed |
| R1-5 / R2 | **Non-recurrence reframed** everywhere: "not independently confirmed … none recurs in the available repeats, whose sampling constrains intermittent emission weakly". Localisation is stated as the stronger reason |
| R1-6 | **New Table 1, "How to interpret a candidate"** — four levels (detection / screen / localisation / recurrence) with a boxed statement that the control rank is not a significance or *p*-value |
| R1-8 | Novelty reframed: two gaps, not three. The paper no longer implies it samples the 40 pc population |
| R1-10 | Conclusions now carry the misquotation guard: limits apply to carriers unresolved by 15.3–1953 kHz channels and are not equivalent to Hz-resolution SETI |
| R1-12 | **Polarisation claim softened** as requested: no polarimetric discrimination is performed, and strict "polarisation blindness" is explicitly not claimed given parallactic sampling, unequal hand flagging and leakage |
| R1-13 | Conclusions end with the three requested sentences |

---

## Not done, and why

**Everything outstanding traces to one queued job.** Referee 2's M1 (re-run
the frozen search on the 75 crossings' blocks) and M2/M3 (re-extract the
ACA windows on the correct 7 m geometry, then measure P₉₀ˢᵉˡ through the
full selection including the rank gate) require a re-search from raw
visibilities. That work is **specified and queued as task 0** in
`OPEN_TASKS.md` — 278 blocks, 739 GB, 9–13 h wall clock — waiting on the
present downloads. Depending on it and therefore not in this version:

- **R2-M3(a)**, measured P₉₀ˢᵉˡ through the rank gate. The abstract's
  "calibrated by injection and recovery" wording has been softened from
  "through the complete selection" pending that measurement.
- **R2-M3(b)**, recomputing *C*resp from the ALMA correlator response
  rather than the adopted kernel.
- **R1-3**, the stellar-frame line-mask audit for every crossing, which
  needs the retained (ν, ν̇) cells.
- **R1-4**, enlarging the injection grid across the Class A axes.
- **R2-M4**, adding α Cen, Sirius A, Fomalhaut and ε Eri via Hipparcos and
  handling mosaics — a re-run of target selection and a new search.
- **R2-M7**, the independent CASA `tclean` cross-check, which needs the
  measurement sets.
- **R2-S2**, re-running the TRAPPIST-1 windows at a higher drift ceiling.

Also not done: **R1-7/R2-M8's cut to 15–20 pages**. v3.95 already removed
19.8 %, and the remaining main text is largely measurement. A further cut
of that size now means deciding to report less, which is an author's call.
**R1-11** (simplified main-text Figure 4) and **R2 minor 5** (Figure 1
redraw) are presentational work not attempted here.
