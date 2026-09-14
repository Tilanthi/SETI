# Response to the three referee reports on v3.46

**Manuscript:** *An ALMA Archival Search for Spectral Technosignatures toward Stars
within 40 pc*, White & Dey. **Version:** v3.47.
**Reports answered:** `v3.47_referee1_radio.md`, `v3.47_referee2_radiostars.md`,
`v3.47_referee3_general.md`.

Every point below says what was **verified**, against what, before anything was
changed. Where a referee's number disagreed with ours, we re-derived it from a
product rather than adopting either figure. Two of the referees' own numbers did
not survive that check and are recorded as such at the end.

---

## Priority 1 — the β Pictoris systemic velocity

**All three referees found this independently, and they are right.**

*Verified.* The contradiction is in the code, not just the rendered text:
`round10_calc.py` carried `VSYS_BPIC = 16.84` for the stellar-frame column of
`tab:bpicaudit` while `v346_calc.py` carried `VSYS = 20.0` for the barycentric
concordance of the recurrence blocks. Two generators, two values, three
paragraphs apart in print.

*Verified.* Adopting +20.0 km s⁻¹ moves the three stellar-frame offsets from
−2.72 / −3.45 / −3.62 to **+0.44 / −0.29 / −0.46** km s⁻¹. We re-ran the
generator rather than doing the arithmetic by hand; the result reproduces
referee 2's prediction exactly. The correction therefore **strengthens** the
attribution, and we have said so.

*Done.* A new module `bpic_vsys.py` holds the adopted value, its uncertainty and
the reasons; `round10_calc.py` and `v346_calc.py` both import it, so the two
cannot diverge again. New macros `\VsysBpic` = +20.0 and `\VsysBpicErr` = 0.7.
The three hand-typed `+16.84` cells in `tab:bpicaudit` are now `\VsysBpic`. The
caption states the adopted value, its uncertainty, the source
(Matrà et al. 2017, who integrate 14–26 km s⁻¹ heliocentric, i.e. adopt 20.0)
and the reason for not preferring the catalogue value (A6V, v sin i ≈ 130 km s⁻¹,
inside the Gaia DR3 hot-star template regime; new bibitem Blomme et al. 2023).
Offsets now print signed, since on the adopted value they straddle zero.

*Propagated.* `tab:bpicaudit`, §5.3.3, §5.3.5 and Appendix E. Appendix E's
hand-typed "β Pic, −2.7 to −3.6 km s⁻¹ … 7 per cent of it" is now
`\BpicMaxAbsStel` = 0.46 and `\BpicMaskPct` = 0.9, both generated. The largest
attributed circumstellar excursion is now under 1 per cent of the mask
half-width, which is a considerably stronger statement than the one it replaced.

*Also corrected (referee 1, minor 7).* The `tab:bpicaudit` β Pic B3 row carried
a UTC start of 2022-03-02 23:14, which is within minutes of a **different** block
of the same unit. The released flagged block `A002_Xf5d76d_X32f1` starts
2022-03-03 21:49 UT; the row now names the block it describes. No number moves.

*Also corrected (referee 2, m1).* The sign convention is now stated once in the
table caption, and the recurrence paragraph says explicitly that it has switched
to the ordinary radial-velocity convention.

---

## Priority 2 — the two false statements

### 2.1 "The stage-1 Band 6 window has no second block in the archive"

*Verified false, twice over.* `archive_meta_v343.json` gives
`uid://A001/X133d/Xbb5` two progenitors, `A002_Xd9668b_X3a90` (45.2 GB,
searched) and **`A002_Xd9668b_Xa9df` (48.9 GB, not searched)**. We then checked
the processing host read-only: that block is queued and disk-gated
(`driver_full_0733.log`, `gate WAITING … 277 GB free < 297 GB required`,
unchanged from 07:33 to 08:01 UTC).

*Done.* The sentence now says exactly what is true: the unit holds a second
block, names it and its size, states that it has **not been searched**, and
concludes that no second-epoch measurement of that window exists either way.
**No result is claimed for it.**

### 2.2 A Class A fine window called "coarse"

*Verified.* In the released catalogue the 230.528134 GHz β Pic Band 6 window has
`chanw_Hz = 244140.625`, `resolution_class = fine`, `search_class = A`.

*Done.* Corrected in all four places, not the three the reports listed: the
`tab:bpicaudit` caption, the `tab:bpicaudit` footnote, §5.3.3
("the unflagged lower-resolution Band 6 window") and Appendix E's crossing
ledger. The recurrence paragraph now adds the point this was costing us — the
recurrence is demonstrated on a Class A window at the survey's finest drift
discrimination, which is a stronger control than a Class B one would be. The
three β Pic Band 6 windows are now distinguished by frequency throughout, as
referee 3 asked.

### 2.3 The Band 3 control is now exhaustive

*Verified on the host (read-only).* `/data/SETI/epoch_extension/verdicts.log`
and `state.json` record `A002_Xf5d76d_Xeb8` **SEARCHED 4/4 windows ok,
2026-09-12T07:03:41Z**. Its result file gives T★ = 30.76, 24 channels above
threshold, control maximum 7.34, `n_control_ge_star` = 0, `detection: true`.

*Done.* `bpic_epochs_v347.json` supersedes the v346 product and carries the
fourth block. The Band 3 unit is **4 of 4** and the Band 6 recurrence unit is
**2 of 2**; both denominators are stated and both are now called exhaustive,
which referee 2 correctly identified as a strength the paper was not claiming.
T★ across the four Band 3 blocks is 14.65, 17.29, 27.68, **30.76**, with the
control maximum below the star in every one (`\BpThreeRingMax` 7.34 against a
smallest `\BpThreeTmin` 14.65 — stated this way because
`n_control_ge_star` is null in the first block's product, referee 1 minor 15
and referee 2 m4).

*Also corrected (referee 1, M2).* The four Band 3 executions share one
scheduling block inside ~23 h, so they are one epoch repeated, not four epochs,
and the paper now says so. "Nine years" is replaced by the measured span,
`\BpBaselineYr` = **8.4 yr** (2013-10-06 to 2022-03-03). The bookkeeping
(blocks vs epochs vs years) is defined once at the head of the paragraph, per
referee 2 m3.

---

## Priority 3 — numbers that did not reproduce

Each was re-derived here before being changed, and each is now driven by a macro
from the new generator `v347_calc.py` → `survey_numbers_round16.tex`.

| Item | Verification | Outcome |
|---|---|---|
| **Parallax cut** | Referee 3 and an earlier evidence run agree independently: max σ_ϖ/ϖ = **2.48 %**, three entries above 0.8 %, all three among the searched 88. We confirmed here that all three (2MASS J05241914−1601153, HD 14055, j1256−1257) are in the released catalogue. | §3 now states the condition the archive query actually applied (ϖ ≥ 25 mas, parallax better than 20 per cent) and reports the realised worst case, `\PlxWorstPct` = 2.48 %, with `\NPlxOverEight` = 3 above 1 per cent. The sentence is corrected, not deleted. |
| **TRAPPIST-1** | `\OrbAccTrapd` = 1.07 and `\OrbAccTrapc` = 2.14 against a ceiling of 3.60–4.00; only b (4.00) reaches it, as §6.2 and the `fig:accel` caption already said. | §4.1 rewritten to the singular; c is now described as reaching the ceiling only at modest eccentricity. The abstract's inherited plural is fixed. |
| **N_eff = 995** | The ensemble has 512 members; the quantity computed is π(r_out²−r_in²)/1.133 θ_beam², a count of resolution elements. | Renamed **N_geom** in both places (§4.1 and Appendix G), capped: the 512 controls are effectively independent outside the most compact configurations, and 30–43 is the worst case. The clause that the rank test needs exchangeability rather than independence is added. |
| **η_drift** | Re-derived: with T = one 6 s dump the Class B value is 1.1×10⁻³; with the median 2087 s on-source track it is 0.384 against a printed 0.36. The printed values require the track. | Definition changed to "the full on-source track T", with one clause contrasting it against η_smear, which is the same ratio over one integration. |
| **Hanning ρ** | Re-derived analytically and by simulation (2×10⁶ samples): ρ₁ = 0.6667 (sim 0.6664), ρ₂ = 0.1667 (sim 0.1656), σ ratio 0.6124. | Corrected to ρ₁ = 2/3 with the lag-2 term stated. "The smoothing state is now measured" replaced: the archive figure is metadata, and the **measurement** is the retained spectra's lag-one autocorrelation, `\LNLagOne` = 0.65 against the Hanning prediction 0.667. The "a decomposition not made here" clause is deleted, because the decomposition is now made. |
| **False-alarm cell count** | Gumbel E[max] reproduces the printed predictions exactly (N = 2×10⁸ → 5.74; N = 2.4×10⁵ → 4.47). Dividing by 4 gives **5.50** and **4.17** against observed 5.77 and 4.41: **+5 %** and **+6 %**. | Appendix G now states that n_cells over-counts independent trials (Hanning in frequency, grid oversampling in drift), gives the corrected predictions and the residual excess in both classes, and says that this is why the rank test and not the Gaussian budget is operative. The comparison is kept. No conclusion moves, and we say so. |
| **Arecibo ν²** | 2×10¹³ × (230/2.38)² = **1.87×10¹⁷ W**. | Corrected to ≈2×10¹⁷ W with the arithmetic printed, and the aperture-efficiency convention now stated once for both benchmarks (the Arecibo figure carries the real efficiency; the 12-m benchmark is geometric). |
| **Sirius B median** | From the released catalogue: median with Sirius B **1.372×10¹⁵ W**, without **1.548×10¹⁵ W**. The printed "1.3 → 1.4" reproduces neither. | The sentence no longer denies a change and then prints one: it states that both endpoints and all conclusions are unchanged and that the median moves by one significant figure, `\EirpMedWithSirius` → `\EirpMedNoSirius`. |
| **fine 5.76 / coarse 4.42** | Catalogue medians are **5.7725** and **4.4134**. | Now `\CtrlMedFine` and `\CtrlMedCoarse`, generated. |
| **Worked example 0.244 mJy** | Eight G 272-61B Band 3 windows carry 0.24119–0.24752 mJy; **none rounds to 0.244**, and the example never said which window it was. | The example now names the window (deepest of the 8, execution block and lower edge given) and takes the rms and S_min from macros. |
| **"a 1.4σ difference that excludes a flare"** | A 1.4σ difference excludes nothing. | Restated in the form that does the work: both halves carry the feature against the persistent-source expectation, so an event confined to either half is excluded, and the 1.4σ difference is consistency. |
| **β Pic control vs T★ ≈ 6** | The β Pic control is at T★ = 10–28 and says nothing directly about sensitivity at CP−72's T★ ≈ 6. | The logical division is now explicit: the β Pic test establishes that the machinery preserves a real repeat; the T★ = 6.21 expectation establishes that *this* repeat would have been seen. |
| **CP−72 block separation** | `cp72_recurrence_v345.json`: gap 60.34 min, **start-to-start 2.046 h**, total span 3.07 h. The printed sentence contradicted its own two clock times. | Stated once and correctly, with `\CpRecStartSepH` restored. "An hour later" / "across an hour" changed to two hours in all three places, including the `fig:cp72ctrl` caption. |

---

## Priority 4 — the result sitting unused in the products

*Verified from the released catalogue and `bpic_epochs_v347.json`.* In the
recurring 230.528134 GHz window the control ring **outshines the star in both
blocks independently**: T★ = 10.16 / 9.95 against ring maxima **15.17 / 15.08**,
with **8 and 6** of 512 controls above the star. The annulus is
r_in = 3.818″, r_out = 21.270″, and β Pic's CO belt peaks near 85 au = **4.3″**
at the catalogue distance of 19.63 pc. **The control annulus sits on the CO belt.**

*Used, in three ways, as referee 2 asked.*

1. It explains physically, rather than statistically, why the recurring window
   is not a stage-1 outlier: the source fills the ring.
2. It localises the emission off the star from the frozen products alone —
   a transmitter is at the star, CO in an edge-on belt is at the ansae — which
   is a partial answer to a localisation the paper otherwise defers.
3. **Resolved astrophysical emission filling the annulus is now in the
   exchangeability-violation list**, which omitted the one violation that
   actually operates in a debris-disc archive. It is conservative (it suppresses
   a star-exceeds-ring outcome and never manufactures one), and the paper now
   says so and points at the two windows where it is measured.

The edge-on geometry is stated once and ties the four apparent coincidences
into one prediction: the sight line through the stellar position samples the
orbit where the radial velocity is near zero, so emission at the star is narrow
and centred on systemic while the ansae inside the annulus carry ±v_Kep.

**The two free external checks are both in.**

- *Cataldi et al. (2023) §C.5*: the HD 48370 disc is undetected in **both** CO
  and carbon, which removes the circumstellar alternative by citation. Their
  wording "potentially due to cloud contamination" is now quoted accurately
  (referee 2, m2), with our own kinematic confirmation stated as the stronger
  evidence.
- *Galactic rotation*: we re-derived it. At l = 214.55°, b = −3.19°, a flat
  curve with R₀ = 8.15 kpc and Θ₀ = 236 km s⁻¹ gives V_LSR = **+23.2 km s⁻¹**
  at 2 kpc against the **+23.9 km s⁻¹** our own LSR chain measures. In the paper.
- The recovered barycentric velocity **+41.2 km s⁻¹** against Cataldi et al.'s
  ≈41 is now printed, converting a claim into a measurement (referee 2, M8b).
- Referee 2's M8(d) is accepted: "a third window is consistent" was not
  supported by what followed. The Band 8 [C I] crossing is 129 km s⁻¹ from
  [C I], so it is not [C I] emission from anything; it is rewritten as an
  ordinary noise crossing dispositioned by its own ring, and the window's real
  contribution — no line at the star in this disc's carbon tuning, exactly what
  Cataldi et al. report — is now what the sentence says.

Referee 2's M9(a) and M9(b) are also in: the channel counts are converted to
line widths (Band 3 **10.8–15.2 km s⁻¹**, Band 6 **2.26 km s⁻¹**, against one
channel for a carrier), Matrà et al.'s CO 3−2/2−1 = 1.9 ± 0.3 is used to close
off excitation as an explanation for the 2−1/1−0 deficit, the two synthesised
beams are given from obscore, and the channel-width point is made in a clause.

---

## Priority 5 — length and prose

### Length

**The paper is 30 physical pages. This is the one requirement not met, and it is
reported rather than concealed.**

| | v3.46 | v3.47 |
|---|---|---|
| Main text | 20.75 | **20.91** |
| Back matter | 1.05 | 1.03 |
| Appendices | 6.88 | 6.85 |
| Bibliography | 0.31 | 0.36 |
| **Content total** | **28.99** | **29.14** |
| **Physical pages** | **29** | **30** |

The overflow is **721 rendered characters**, about ten reference lines, or
0.14 pp. Source text grew by **+196 words (+0.8 per cent)**.

**Every cut named by any of the three referees was applied**, and several were
taken further than asked:

- Referee 3's C1–C7 in full. §5.3.5's CP−72 material is down from 11,372 to
  **8,226 characters** against the ~1,750-character cut requested, so the
  subsection no longer outweighs the Discussion. Protected material is intact:
  the second-epoch measurement, the same-night qualification, the local-null
  values, the split-half test and the bandpass-ε bound.
- Referee 1's four named offsets (§4.4's duplicate screen paragraph, §4.1's
  repeated bandpass worked example, §5.3's masking-cost recapitulation,
  Appendix F's repeated 287 MHz offset).
- Referee 2's offsets 1–5, plus **offset 6**, which referee 2 offered only "if
  the authors need the margin". We did, so component (iv) is compressed (not
  deleted — it is prespecified, and its expectation and role are kept).
- Two further typographic reductions that cost no content: `tab:selfunc` and
  `tab:perband` are set at `\footnotesize` (changed in the generator, so it
  survives clean regeneration).

**Nothing on any of the three "must not cut" lists was touched.** All three
lists were honoured, including both boxed rules, `tab:nomenclature`,
`tab:bothstats` and the nine-day chronology, `tab:bpicaudit`, the HD 48370
local-null failure, the coarse-noise subsection, the dwell campaign, the
withdrawal statements, the polarisation-blindness paragraph, the per-window
catalogue description, `fig:ctrldiag`, `fig:cp72ctrl` with both epochs, the
"two epochs cannot separate" sentence, the HD 48370 near-tie, the mask
sensitivity ladder, `app:continuum`'s intrinsic-variability admission and the
"In plain terms" paragraph.

**Why the page was not recovered.** Every page from 1 to 29 is packed to
0.87–0.88 fill; there is no float whitespace to reclaim. The corrections the
three reports require are net additive — they add evidence (the fourth Band 3
block, the ring maxima and belt geometry, the Galactic-rotation check,
Cataldi's non-detection, the corrected trials accounting, the line widths) —
and the cut lists of the three reports overlap heavily, all three naming the
same CP−72 subsection. Closing the last 0.14 pp would mean deleting material
one of the three referees has explicitly asked to keep.

**Three costed options for the author**, in our order of preference:

1. **Accept 30 pages.** The paper is 0.14 pp over; nothing about the science or
   the referee responses changes.
2. **Cut Appendix H** (the conditional searched-domain transmitter fraction,
   ≈1.1 pp with `tab:occurrence`). No referee protects it and no headline
   number depends on it, but it is a result and was demoted to an appendix
   rather than removed at the author's own direction, so we did not take this
   decision unilaterally.
3. **Drop four referee-requested minors** (~760 characters): referee 1's
   residual-phase-decorrelation clause, the r_in < beam fraction, the
   dirty-map estimator definition, and the Data Availability note on the
   re-searched blocks. We recommend against it: each is something a future
   referee would ask for again.

### Prose

| Construction | v3.46 | v3.47 |
|---|---|---|
| antithesis family (", not" / "and not" / "rather than") | 24 | 31 → **31** (main 22) |
| "and no ⟨noun⟩", main | 11 | **5** |
| "and never", main | 7 | **6** |
| ", so", main | 114 | **112** |
| colon-explainer | 112 | 119 |
| em-dash | **0** | **0** |
| numeral list-opener | 5 | 6 |

Referee 3's P1 is done, and the arithmetic deserves a note: the "and no ⟨noun⟩"
count is down from 11 to 5 and "and never" from 7 to 6, but the measured
antithesis family **rises**, because the fix referee 3 prescribed — "take ten of
these back to 'not a'/'not'" — converts a construction `prosecount.py` does not
count into one it does. Where the positive form was as clear we dropped the
antithesis entirely rather than converting it, which is why the rise is 7 and not
16. The ungrammatical instances referee 3 listed (l. 490, 861, 1817, 1878, 2953,
3049) are all repaired.

P2 (", so") is reduced in the named clusters and, more to the point, in the new
prose, which had picked up the same tic: eight instances were removed from
material written for this version alone.

P3 is done: both half-page §4.1 paragraphs are split at the points referee 3
named. **P4**: one of the two didactic asides is gone with the C7 cut, and the
other is kept, as instructed.

**M6, the "lane × 46" phantom, is closed.** The true count is 17 (14 in main),
inflated by substring matches on "plane" and "planet". The three defined senses
are consistent and are not renamed. The fourth sense at l. 942, the
"machinery-only lane", is now "the machinery-only test". The deferred item can
be struck from `STATE.md`.

**M5 and M7 (structure).** `\label{sec:validation}` was orphaned inside §4.4 and
resolved to the wrong subsection; the Appendix B reference is retargeted to
`sec:ancillary` and the dead label removed, so the class of error the
"0 undefined references" gate cannot see is gone. `\input{tab_selection}` has
moved out of Appendix A (frequency conventions and smearing) to sit with the
per-target results.

---

## Referee statements we could not confirm

Recorded because they were checked and did not hold.

1. **Referee 1, M3 / referee 2, M7 both describe the CP−72 span correctly, but
   referee 1's "the total span … is 3.07 h" and referee 2's "2.05 hours" are the
   same fact stated two ways.** We print both: a 60-minute gap, a 2.05 h
   start-to-start separation and a 3.1 h total span, so no reader has to guess
   which is meant.
2. **Referee 2, M3 says the fourth Band 3 block `A002_Xf5d76d_Xeb8` is "not
   searched, not mentioned".** True when the report was written; it completed at
   07:03:41Z on 2026-09-12, and the paper now uses it. The unit is exhaustive.
3. **Referee 1, M2 gives the Band 3 block epochs as "all three inside ~23 hours"
   and the full span as 8.41 yr.** The span reproduces from the blocks that
   carry a recorded UT start. Only two of the four Band 3 blocks record one in
   the products available here, so the paper states the session-level fact
   (one scheduling block, within ~23 h) rather than four block times we cannot
   evidence. `A002_Xf5d76d_Xe19` and `A002_Xf5d76d_Xeb8` have no recorded
   observation date in any product reachable read-only; reading it would have
   required running code on the processing host, which the brief forbade.
4. **Referee 3, M8 says the UV Ceti Band 3 example has "four" candidate rows.**
   There are **eight** (0.24119–0.24752 mJy). The conclusion is unaffected:
   none rounds to 0.244.
5. **Referee 3, m1 reports the Data Availability naming
   `per_target_results_v3.45.csv`.** Confirmed, and it had survived one earlier
   attempt to fix it. The catalogue is renamed to `v3.47` in the generator, the
   file and the manuscript together.

## Not done, with reasons

- **Referee 2, M2's suggestion to search the 48.9 GB second block before
  submission.** It is queued on the processing host and disk-gated. The brief
  for this revision forbids starting compute there. The paper therefore states
  that the block exists and has not been searched, and claims nothing further.
- **Referee 2, m7 (is the β Pic CO J = 1−0 detection new?).** This needs a
  literature and project-code check we could not complete here, and a priority
  claim is the author's to make. Flagged for the author.
- **Referee 2, M10 (two integers for disc hosts and young-association members).**
  The counts are not in any product in this folder; §2 says the age and
  disc-hosting flags are documented qualitatively. Deriving them means a
  SIMBAD/literature pass per star. Deferred, not refused.
- **Referee 1, minor 10 (N_MOUS = 102 and N_EB = 102).** Flagged. The
  coincidence may be real, but we did not verify it and did not want to print a
  reassurance we had not checked.
- **Referee 3, m6 (move Table 4 into §3).** Offered as an option, not a request;
  it front-loads four result rows into the sample section. Left to the author.
- **Referee 3, m5 (seven small-caps-italic font warnings).** Cosmetic, arising
  in `openjournal.cls`; not touched.
- **Referee 3, m9 (six author TODOs).** Correctly left alone: the VBRL
  affiliation, the White (2026) arXiv identifier, the CRediT split, the
  `submitted-v3.32` git tag, the Zenodo DOI and the execution-block overlap
  statement. **The git tag still names v3.32 in a v3.47 paper and will look
  careless if it ships.**
- **`abstract_limit.py` ignores its command-line argument** (referee 3's
  footnote). Confirmed: it globs for the highest-numbered manuscript in the
  directory. Harmless here because the folder holds one version, and left alone
  because changing a gate mid-revision is worse than documenting it.

---

## Final state

- **30 pages.** Main 20.91, back matter 1.03, appendices 6.85, bibliography
  0.36; content total 29.14.
- **Gates: 0 errors, 0 undefined references or citations, 0 multiply-defined
  labels, 0 overfull boxes, 0 underfull boxes, 0 Type 3 fonts, 0 em-dashes.**
- **Abstract 1,907 of 1,920 rendered characters.**
- **583 macros, 0 unused.**
- **Clean regeneration:** every generated file deleted and rebuilt by
  `make_all.sh`; all `survey_numbers*.tex` and `tab_*.tex` reproduce
  byte-identically apart from the ordering of `retire_macros.py`'s own comment
  lines, and the rebuilt paper has the same page count and the same gates.
- **arXiv set:** 30 items, built from an empty directory, 0 errors, 0 missing
  files, 0 Type 3 fonts.
- **Not pushed.**
