# Referee report — round 3 of 5: method description, reproducibility and presentation

**Manuscript:** `technosignatures_40pc_v3.85.tex` / `.pdf`, 41 pp, two-column, 14 figures, 23 tables
**Release checked:** `per_target_results_v3.85.csv` (1655 rows x 50 columns), `make_all.sh`,
`reproduce_from_catalogue_v385.py`, `audit_numbers_v385.py`, `regen_count.py`, `figures/*.pdf`
**Scope of this round:** can a competent reader reproduce this; does the release contain what the
paper says it does; are the figures and tables necessary, legible and referred to; is the prose
readable; is the terminology stable; does the abstract work cold.
Rounds 1 (arithmetic) and 2 (inference) are not repeated. Where a round-3 check happens to expose a
number that is also an arithmetic defect, I say so and move on.

Line numbers are `technosignatures_40pc_v3.85.tex`. Printed values are quoted from `pdftotext`.

---

## 0. What is already good, and should not be touched

These are not courtesies; I checked each one.

- **The number-generation architecture is the best I have seen in a manuscript of this kind.**
  866 macros, `audit_numbers_v385.py` (51 checks) and `reproduce_from_catalogue_v385.py`
  (36 checks) both inside `make_all.sh`, both failing the build. I ran both: 51 pass / 0 fail and
  36 pass / 0 fail. The *design* is right; §2 below is about where its coverage stops, not about
  the idea.
- **`make_all.sh` is genuinely ordered, and the ordering hazards are documented in the file
  itself** ("`v358_inject.py` must precede `v352_calc.py`", "`make_fig_funnel.py` must follow
  `localnorm_all_v385.py`", "`regen_count.py` must be last but one"). Very few authors write this
  down at all.
- **Table 2 (nomenclature) and Table 1 (glossary) are the right idea and well executed.** A reader
  can look up `P_trig` / `P_eff` / `P_50` / `P_90` in one place. Table 6 (the statistical data
  path, 12 numbered steps) is the single most reproducibility-useful object in the paper.
- **The statistic is fully specified at the level that matters most**: Eq. 2 with its weights, the
  MAD-across-controls noise scale with its 1.4826, the block-median baseline with `W = 65` and the
  `max(2, n/65)` block rule, the `0.25/0.5/0.25` Hanning kernel, `theta_PB` coefficient, ring radii
  in `theta_PB`, the ring seed `20260825`. Most papers stop three levels above this.
- **The catalogue is internally consistent.** I verified
  `eirp_eff_total_W == eirp_nominal_W x c_response_smear` on 400 rows (0 failures), `n_ctrl == 512`
  on all 1655 rows, and the row/column counts against `\NCatRows` and `\NCatCols`.
- **Captions carry their own symbol definitions.** I could read Table 9, Table 11, Fig. 12 and
  Fig. 14 without the body text. That is rarer than it should be.
- **The paper says plainly what it did not do** (no cross-hand product, no per-integration RFI
  screen, no automated injection test on every pipeline change, `P_95` not determined). That
  honesty is the paper's strongest presentational asset and I would not trade any of it for length.
- 0 overfull boxes, 0 undefined references, no duplicate labels. The LaTeX hygiene is clean.

---
## 1. Could a competent reader reproduce this? — steps asserted but not specified

I read §4 and the appendices as an implementer, asking of each step: do I know what to type?
Fourteen places where I do not.

### P1 — MAJOR. The drift-grid *step size* rule is never given, only its endpoints.

> l.1178: "The grid is uniform in $\dot\nu$ over $n_{\rm drift}$ steps (2--1944 across windows,
> recorded per window), so a carrier midway between trial rates leaves a residual drift
> traversing at most 0.26 of a native channel over the longest fine-class track"

The ceiling is specified (§4.3, 12--13 Hz s^-1 GHz^-1 or the planet bound). The *number of steps*
is not: `n_drift` is reported per window but no rule generates it. Everything downstream depends on
it — the cell count `n_cells` (177 to 6 869 740), the over-count 5.3, the Bonferroni scale, and the
0.26-channel residual quoted in this very sentence. A reader cannot re-derive `n_drift` for a window
they choose themselves, so they cannot reproduce the trials accounting.
**Fix:** state the rule in one clause, e.g. "the grid is Nyquist-sampled at twice the rate at which
a trial drift moves a carrier one channel over the track, $\Delta\dot\nu = \Delta\nu_{\rm ch}/(2\tau_{\rm track})$,
truncated at the ceiling, giving $n_{\rm drift} = 2\lceil |\dot\nu|_{\max}\tau_{\rm track}/\Delta\nu_{\rm ch}\rceil + 1$."
One sentence, and the "oversampled two to one" claim in App. F then has a visible origin.

### P2 — MAJOR. Band-edge trimming is not described, and it changes the searched frequency union.

Nowhere in §4, Table 6 or App. A is there any statement about which channels of a spectral window
the search actually evaluates. The `flo_GHz`/`fhi_GHz` columns are described in the Data
Availability as "searched frequency range", and `\UnionGHz` = 118.1 GHz is built from them. If the
search trims edge channels — and a matched filter with a 65-channel median baseline and a drift
stack must trim something — then the union, the mask cost, the per-band table and the exposure
integral are all quoted over a slightly different domain than the one searched.
**Fix:** one sentence in §4.2 after step 3 of Table 6: how many channels are dropped at each edge
and why, and whether `flo_GHz`/`fhi_GHz` are pre- or post-trim.

### P3 — MAJOR. The eight visibility-domain control positions are unspecified.

> l.1885: "applied the test at the recorded peak frequency of each event, with eight control
> positions on the annulus the image-plane test uses"

Which eight of the 512? First eight in seed order? Eight drawn on a new seed? Eight at equal
azimuth? The `ctrl` column of Table 9 and the open circles of Fig. 7 are the *maximum* over these
eight, so the selection rule is the null distribution of that column. It is not stated and it is
not a catalogue column.
**Fix:** name the rule (and, if it is "the first eight in `probe_positions()` order", say so — that
is perfectly defensible and takes five words).

### P4 — MAJOR. The drift-following, continuum-subtracted visibility fit is never specified.

> l.1931: "a dedicated fit that follows the recovered drift and subtracts the local continuum,
> on the same 405 860 visibilities, gives 5.5 sigma with the best-fitting position on the star"

This is the estimator that reverses the CP-72 2713 verdict from the uniform test's 2.3 sigma, and it
is described in eleven words. What is the model (point source at free (l,m) plus a constant?), how
many free parameters, which channels enter the drift track, how is "local continuum" defined
(which channel range, fitted or median-subtracted?), and how is the 5.5 sigma obtained — from the
fit covariance, or by comparison with control positions? A referee cannot assess a number produced
by an unspecified estimator, and round 2 has already flagged its use asymmetrically.
**Fix:** a short App. G subsection: model equation, free parameters, channel selection, continuum
definition, and how the significance is computed.

### P5 — MAJOR. The window-selection rule under the 8-per-target cap is not given.

> l.1244: "Every spectral window of an observation enters the spectral-carrier search, capped at 8
> per target to bound compute cost; the cap bound one target/band, 61 Vir Band 7, and three further
> targets are represented by their deepest single window"

Two rules are missing. (i) When a target has more than 8 windows, *which* 8 are kept? If the choice
is by depth, the selection is not independent of the data and the null calibration inherits it; if
it is by identifier order, say so and the problem vanishes. (ii) "three further targets are
represented by their deepest single window" — that *is* a depth-dependent selection, applied to
three targets, and no rule is given for when it applies.
**Fix:** state both rules explicitly and say which catalogue column marks the affected rows (the
text says they are "marked in the released catalogue" but no column in the 50 does so — see P17).

### P6 — MINOR. The hold-out hash is under-specified by one bracket.

> l.2090: "A block is held out if and only if $\mathrm{sha256}(\textsc{uid})_{[:8]} \bmod 5 = 0$"

`[:8]` of what — the hex digest string, or the raw digest bytes? And then interpreted how, base 16?
And what exactly is UID: the `A002_Xd9398d_X37e8` form as it appears in `eb`, or the full
`uid://A002/...` form, and with what case? The paper says it "can be recomputed from the UIDs
alone"; as written it cannot, without guessing twice.
**Fix:** "the first eight hex characters of the SHA-256 digest of the execution-block UID in its
`uid://A002/Xhhhhhh/Xhhhh` form, read as a base-16 integer."

### P7 — MINOR. `probe_positions()` is named but its random-number generator is not.

> l.1035: "It holds 512 positions drawn uniform in area, $r=\sqrt{U(r_{\rm in}^2, r_{\rm out}^2)}$,
> and uniform in azimuth, from the fixed seed 20260825 re-applied per window."

Seed and distribution are given; the generator is not. `numpy.random.RandomState(20260825)` and
`numpy.random.default_rng(20260825)` give entirely different point sets from the same seed, as does
drawing radius-then-azimuth versus azimuth-then-radius. Since the paper elsewhere reconstructs the
geometry *from the code* and validates it by two indirect checks (the 135-position inner ring, the
CO radial correlation), the exact draw evidently matters.
**Fix:** one clause: generator, call order, and whether the 135 inner-ring positions are drawn from
the same stream before or after the 512.

### P8 — MINOR. The Class A / Class B boundary has no number in the text.

§4 argues at length that the boundary is immaterial because channelisation is bimodal with an empty
gap (l.759--765) — a good argument. But no numeric boundary is ever stated in the body; the only
place a number appears is the caption of Fig. 13, "fine (<5 MHz) against coarse". `resolution_class`
and `search_class` are catalogue columns whose construction is therefore not documented.
**Fix:** put the operative number in §4 where the classes are defined: "windows narrower than
5 MHz are Class A" — and then the bimodality argument explains why 5 is arbitrary.

### P9 — MINOR. "Usable channels" is used in the baseline rule but never defined.

> l.1014: "using $\max(2, n/65)$ blocks over $n$ usable channels"

Usable = unflagged? unflagged in more than some fraction of integrations? finite-weight? The block
count, and hence the baseline passband ceiling (32 MHz / 1.0 GHz), depends on it.

### P10 — MINOR. The treatment of flagged data inside the statistic is never stated.

The noise scale is `1.4826 MAD` across the 512 controls at each `(t, nu)`. What happens at a
`(t, nu)` where some controls are flagged — are they dropped from the MAD, zero-weighted in the
stack, or does a flagged channel kill the cell? The paper says "the archive's flagging carries
through untouched" (l.966), which describes provenance, not arithmetic. Given that §4.1 worries
explicitly about a lost polarisation hand, the flagging arithmetic deserves a sentence.

### P11 — MINOR. `s_min` and `rms_mJy` are two different quantities with one description.

App. D says the catalogue's per-channel flux threshold "uses the carrier lane's per-channel noise
rather than the tabulated `rms_mJy`, the two differing by $5\times G(r)$". So `rms_mJy` is *not*
the noise the trigger is set on. The Data Availability lists the column simply as "per-channel rms".
A reader who computes `5 x rms_mJy` and compares with `smin_mJy` will get a mismatch and not know
which is wrong.
**Fix:** say in the DA column list which of the two noise quantities each column is.

### P12 — MINOR. The de-duplication rule is stated but the release does not obey it uniquely.

> l.1723: "The retention rule is deterministic and quantity-independent, the key's first-listed row
> in the query's own identifier order"

Good rule, clearly stated. But 35 `(eb, flo_GHz, chanw_Hz)` keys still occur more than once in the
released 1655 rows (up to three times: `A002_Xb25e1a_Xed74` at 215.199158 GHz appears 3x). Either
the key in the rule is not the key I formed — in which case say what the key is — or de-duplication
is incomplete. The paper's own `\NDistinctDatasets` = 1616 against `\NWindows` = 1655 says 39 rows
are not distinct datasets, which is close to my 35 keys but not equal to it, and the DA statement
"1655 rows, one per searched window" does not mention the difference at all.
**Fix:** name the exact key, reconcile 1616/1655/35, and say in the DA that the file is one row per
*catalogue entry*, not per distinct dataset.

### P13 — MINOR. The masked transition list is characterised but not enumerated or version-stamped.

§5.3.7 gives the species (CO isotopologues, HCN, HCO+, CS, SiO, SO, CN, H2CO, [C I]) — that part is
good and objective. But "`\MaskNTransNew` transitions ... at full JPL/CDMS precision" does not
identify *which* transitions (upper-state energy cut? frequency range? all catalogued lines of
those species in 84--950 GHz?), and no catalogue version or access date is given for JPL/CDMS. The
DA says the deposit holds the mask, so the information exists; the paper should say enough for a
reader to rebuild it approximately without the deposit.

### P14 — MINOR. Two processing-order facts that matter are implied rather than stated.

(a) Primary-beam correction: "enters the quoted thresholds and fluxes ... and leaves untouched the
extracted amplitudes the statistic ranks" (l.962). That is the right design and is stated — but
Table 6 does not show it, so a reader implementing from Table 6 alone will apply it in the wrong
place. Add it as an explicit non-step, e.g. "(primary-beam correction applied to thresholds only,
after step 9)".
(b) The line mask is step 11, *after* the rank test at step 10. The text elsewhere calls the mask
"defined before any crossing is classified". Both are true, but a reader building the pipeline needs
Table 6's ordering to be the authoritative one, and it currently disagrees in spirit with §5.3.7's
framing. One clarifying clause in the Table 6 caption fixes it.

---

## 2. Data and code availability: does the release contain what the paper says?

I checked the Data Availability statement clause by clause against the actual files.

### P15 — MAJOR. **Four physical stars are in the release twice, under two names and two
`system_id` values. The title, the abstract and the statistical unit are all affected.**

This is the most consequential thing I found, and it is invisible from the manuscript alone.
Canonicalising `star_name` (strip a trailing `Gaia DR3 nnnn`, with or without brackets; case-fold)
collapses 94 distinct name strings to **90**, and 87 `system_id` values to **83**:

| physical star | string A (rows) | string B (rows) | distance |
|---|---|---|---|
| HD 207129 | `HD 207129 (Gaia DR3 6564091190988411520)` (4) | `HD 207129  Gaia DR3 6564091190988411520` (12) | 15.5590 |
| gamma Lup / HD 139664 | `* g Lup` (4) | `HD 139664` (3) | 17.3986 |
| eta Crv | `* eta Crv` (4) | `eta Crv` (20) | 18.2437 |
| HD 53143 | `HD53143 (Gaia DR3 5479222240596469632)` (4) | `HD53143  Gaia DR3 5479222240596469632` (20) | 18.3401 |

In every case the orphan string carries **exactly one execution block (4 windows)** that the main
string does not: `A002_Xb28642_Xcff3`, `A002_Xb2f730_X5b37`, `A002_X75bfbf_X1430`,
`A002_Xd9668b_X3f6e`. So the block count 404 and window count 1655 are right; what is wrong is the
*grouping*.

Consequences, all of which the manuscript asserts:

1. **The title says "94 Stars within 40 Parsecs".** It is 90.
2. **The abstract and Conclusion 1 say "94 catalogue stars in 87 systems".** It is 90 in 83.
3. **"The statistical unit is `system_id`" (Data Availability).** Four systems are split across two
   identifiers, so any system-clustered resampling treats them as eight independent units. This
   touches the star-clustered bootstrap of §5.3.1, the per-system `P_90` distribution of Fig. 6,
   and "0 systems reach the Arecibo benchmark".
4. **`\NSysOneEB` = 33 of 87 systems "have only one epoch"** (Conclusion 4, Fig. 6b). Four of those
   33 singletons are artefacts: each orphan is by construction a one-block system. The real
   single-epoch count is 29 of 83, and `\NSysClassAMulti` = 41 of 65 moves too.
5. **`* eta Crv`'s orphan block contains a threshold crossing** (`crossing = True` on one of its
   four rows). A repeat-block search keyed on `star_name` or `system_id` would not see the other
   20 eta Crv rows. No stage-1 flag is involved, so no disposition changes — but the recurrence
   machinery demonstrably has a blind spot of exactly the kind it is there to close.
6. **The paper explicitly claims this was fixed.** l.4422: *"''gamma Lupi'' resolves to HD 139664 at
   17.40 pc, not the naked-eye star; all such entries are relabelled and no measured value
   changes."* Four of the seven gamma Lup rows are still labelled `* g Lup`. The relabelling was
   applied to some rows and not others.

**Fix:** canonicalise `star_name` and `system_id` on a single identifier (the Gaia DR3 source id is
already present in several of them — use it as `system_id` and keep the human name in a separate
column), rebuild, and re-derive `\NStars`, `\NSystems`, `\NSysOneEB`, `\NSysClassA*`, the per-system
`P_90` quantiles and the title. Then add an assertion to `reproduce_from_catalogue_v385.py`:
*no two `system_id` values may share a `dist_pc`*. That single assertion catches all four.

### P16 — MAJOR. **A quasar is in the star sample.** `j1256-1257`, 8 windows, quoted as 21.15 pc.

`star_name = system_id = j1256-1257`, `dist_pc = 21.1536`, Band 7, 2 execution blocks, 8 rows. It is
plotted as a system row in Fig. 4 (I extracted the axis labels), and it is the *named example* in
the primary-beam floor argument, where it prints as a target:

> l.1263 (printed p.12): "the last retained window has response 0.55 at 0.46 theta_PB
> (**j1256-1257** Band 7, 1.81x)"

J1256-1257 is an ALMA calibrator designation, not a SIMBAD star within 40 pc (the nearby
well-known ALMA calibrator J1256-0547 is 3C 279). Either (a) a calibrator field has been ingested
as a target and given a neighbouring star's distance, in which case 8 windows and one of the 94
"stars" must come out and the `\PbMax` example must be renamed; or (b) it is a legitimate SIMBAD
entry under an unusual designation, in which case the paper must say what it is, because no reader
will accept an ALMA calibrator name in a 40-pc stellar sample without explanation. The same question
applies, less sharply, to `ALMA J153702653-33192492` (43 rows, 35.01 pc), the single largest
un-explained designation in the sample.
**Fix:** resolve both against SIMBAD/Gaia, print a proper designation, and add the resolved
identifier (Gaia DR3 source id) as a catalogue column so the question cannot recur.

### P17 — MAJOR. The Data Availability column list does not match the file.

Checked term by term against the real 50-column header:

- **Undisclosed columns.** `star_snr_regionmax` and `stage1_flag_regionmax` are a *third* statistic,
  not the "both" the DA promises ("the add-one rank under both the released and the
  radius-corrected normalisations and the stage-1 flag each implies"). They are mentioned in the
  Introduction but not in the DA list. `n_int`, `bandwidth_Hz`, `c_response_smear`,
  `eirp_eff_total_W`, `a_max_m_s2` are not in the list either.
- **Duplicate columns.** `n_ctrl` and `n_control` are *identical in all 1655 rows* (both 512). Two
  names for one quantity in a file advertised as "self-described".
- **Conditionally empty columns, undisclosed.** `disposition` is blank in **1645 of 1655** rows;
  the DA says the catalogue carries "the disposition verbatim from Table 11" with no hint that only
  10 rows have one. `n_int` is blank in 1200 rows, `eta_smear` in 1200 (the paper does say 455
  carry a value — good), `f_cross_GHz` in 1204, `line_offset_kms` in 29.
- **A claimed marking that does not exist.** §4.4 says three targets "are represented by their
  deepest single window and marked in the released catalogue" (P5). No column marks them.
- **"one row per searched window"** is not true of 35 keys (P12).

**Fix:** ship a `COLUMNS.md` data dictionary with the deposit — name, units, definition, the
`P_trig`/`P_eff`/`P_90`/`T_star` glossary term it corresponds to, and "blank when ..." — and shorten
the DA paragraph to point at it. That replaces a 131-word sentence (P33) with a pointer and makes
the claim checkable.

### P18 — MAJOR. "Rebuilding from the scripts alone reproduces all 68 products" is not true as
stated, in two independent ways.

> l.3241: "Deleting every generated table and figure and rebuilding from the scripts alone
> reproduces all \NRegenProducts{} products byte for byte."
> l.3215: "the repository commit tagged at submission ... reproduces every number, table and figure
> from the regeneration scripts shipped with it"

(a) **Three of the 68 are not regenerated; they are copied from a frozen store**, and `make_all.sh`
says so in its own comment: *"survey_numbers_round{5,6,7}.tex are FROZEN INPUTS: the rounds 5-7
generators were never shipped with the release, so nothing here can rebuild them."* That is 14
macros that no script in the release can produce and that neither audit can check:
`\MaskBWTwenty`, `\MaskBWHundred`, `\ExpoTopPct`, `\HdCorrectedT`, `\HdCorrectedRing`,
`\NonExcRingGe`, `\NonExcRingMed`, `\NonExcHitMed`, `\KsFine`, `\PsFlagMu`, `\OrbAccTrapb`,
`\OrbAccTrapc`, `\HaystackFrac`, `\DriftGridFineHalf`.
These are not decorative. `\HaystackFrac` is the Introduction's headline **6 x 10^-18 of the
haystack**. `\HdCorrectedT` / `\HdCorrectedRing` are the HD 48370 local-rescaling robustness result
in §4.2. `\OrbAccTrapb` / `\OrbAccTrapc` are the TRAPPIST-1 accelerations that the whole
drift-ceiling caveat turns on. `\DriftGridFineHalf` is the 0.26-channel grid residual of P1.
This is precisely the failure mode the paper's own machinery was built to prevent, and it is
currently exempted from it.

(b) **`\NRegenProducts` = 68 does not count the generated table fragments.** `regen_count.py` globs
`survey_numbers*.tex` (45) + 3 named files + `figures/*.pdf` (20) = 68. The 13 generated
`tab_*.tex` inputs (`tab_flagged_v380`, `tab_visibility_v385`, `tab_driftstrata_v385`,
`tab_p90budget_v385`, `tab_specclass_v385`, `tab_partitions_v385`, `tab_unattributed_v383`,
`tab_cprepeat_v383`, `tab_compcurve`, `tab_maskband`, `tab_ring`, `tab_occurrence`, `tab_smear`)
are excluded — so "every generated table" is exactly what the 68 does *not* cover.

**Fix, in order of value:** (i) write the three missing generators, or state in the DA that 14
numbers derive from a frozen intermediate and name them; (ii) extend the `regen_count.py` glob to
`tab_*.tex` and re-quote the number; (iii) change the sentence to what is actually demonstrated:
"a clean rebuild reproduces all N generated products byte for byte, with the exception of three
frozen macro files whose generators predate the release".

### P19 — MINOR. "opens the catalogue and nothing else" is literally false.

> l.3236: "`reproduce_from_catalogue_v385.py`, which opens the catalogue and nothing else and
> re-derives 36 of the paper's headline numbers from it, comparing each against the value typeset
> here"

It also opens the macro `.tex` files (line 27, `open(fn).read()`), as it must in order to compare.
The sentence is self-contradicting on a careful reading. **Fix:** "which derives 36 of the paper's
headline numbers from the catalogue alone and compares each with the typeset macro, exiting
non-zero on any disagreement."

### P20 — MINOR. Five checks are silently skipped and the count is quoted as if complete.

Running the script gives "36 pass, 0 FAIL, **5 skipped**": `NCatFlagGlobal`, `NCatFlagLocal`,
`LocAllFlagGlobal`, `RingThetaMin`, `RingThetaMax` are skipped as "macro absent -- retired or
renamed". The paper quotes 36 without the 5. `retire_macros.py` removing a macro therefore silently
retires its audit check — the same hazard the build notes already record for prose trimming.
**Fix:** make a skip a build failure unless the macro is on an explicit allow-list.

### P21 — MINOR. The four figures the release builds but the paper does not print are
under-declared.

> l.3245: "The release also builds diagnostic figures the paper does not print, among them the
> per-band noise-quality plot and the illustrative occurrence curve"

There are **six** unprinted figures in `figures/`, not two: `noise_qa.pdf`, `occurrence_duty.pdf`
(the two named), plus `completeness.pdf`, `completeness_sensitivity.pdf`, `selection.pdf`,
`symcdf.pdf`. Three of those four have names that suggest superseded versions of printed figures,
which a reader of the deposit will have to disambiguate. **Fix:** list all six, or move the
superseded ones to a `figures/superseded/` directory.

---

## 3. Figures and tables

37 floats (14 figures, 23 tables) in 41 pages. That is roughly one float per page, and the reader
meets four of them back to back on p.18 alone (Tables 9, 10, 11 and Fig. 7 on p.19).

### P22 — MAJOR. **Seven floats are never cross-referenced from anywhere in the paper.**

I extracted every `\label` and every `\ref`. These labels are defined once and never referenced —
and there are no hard-typed "Table N" / "Fig. N" strings in the source either, so the text never
points at them by any route:

| float | label | page | what it is |
|---|---|---|---|
| **Fig. 2** | `fig:selbias` | 5 | spectral-class composition, sample vs census |
| **Fig. 6** | `fig:classasens` | 15 | *what the primary experiment could have found* |
| **Fig. 7** | `fig:unattribvis` | 19 | the visibility test on all 13 stage-1 windows |
| **Fig. 9** | `fig:dwellsel` | 25 | the duty-cycle selection function |
| **Table 4** | `tab:specclass` | 4 | archival selection by spectral class |
| **Table 8** | `tab:chance` | 16 | the six chance expectations and what each assumes |
| **Table 13** | `tab:cprepeat` | 23 | the CP-72 2713 repeat test, both blocks |

Some of these are among the paper's best objects. Fig. 6 is the answer to "what could this survey
have found", Fig. 7 is the round-2 referee's own requested test drawn, and Table 8 is the single
table that disambiguates six competing chance numbers. Leaving them uncited means a reader with a
question walks past the figure that answers it, and most journals will return the manuscript for
this alone.
**Fix:** one `\ref` each, at the obvious place: Fig. 2 at l.478 ("over-representing F and G stars
and under-representing M dwarfs"); Fig. 6 at l.1630 ("the primary experiment is the fine-channel
search"); Fig. 7 at l.1907 ("on this test 0 of them shows emission at the star"); Fig. 9 at l.2734
("duty cycles below ~0.1 are essentially unconstrained"); Table 4 in §3; Table 8 at l.1801 ("the
answer depends on the reference class, and we give both"); Table 13 at l.2528.

### P23 — MAJOR. **Fig. 14 (`rank_cdf.pdf`) is unreadable in print.**

Drawn on a 504 pt canvas and included at `width=0.64\textwidth` = 327 pt, a **0.649x reduction**.
Measured printed font sizes (nominal x scale, character counts from the figure's own text objects):

| printed size | chars | what it is |
|---|---|---|
| 3.18 pt | 2 | superscripts |
| 3.77--3.89 pt | 128 | axis tick labels |
| 4.15 pt | 91 | legend |
| 4.54--4.67 pt | 192 | axis labels |

The body text is 10 pt. Nothing on this figure exceeds **4.7 pt**, i.e. under half the body size and
well below any journal's ~6 pt floor. It is the figure that carries the paper's central
methodological claim — "why the spatial control ensemble is a calibrated screen and not an
exchangeable rank test" — and no reader will read its axes.
**Fix:** it is a `figure*` in a two-column appendix; `width=\textwidth` costs nothing and takes the
scale to 1.01, putting everything at 5.8--7.2 pt. Better still, regenerate at `figsize` matching
511 pt with 8 pt fonts.

### P24 — MINOR. Three more figures sit below the legibility floor for their densest text.

Same measurement, same method:

| figure | canvas | width | scale | smallest bulk text |
|---|---|---|---|---|
| Fig. 4 `coverage_waterfall` | 504 pt | `0.84\textwidth` | 0.852 | **5.62 pt, 1449 characters** (every star label) |
| Fig. 3 `selection_funnel` | 492 pt | `0.80\textwidth` | 0.831 | **5.48 pt, 480 characters** (the ledger panel) |
| Fig. 1 `eirp_context` | 508 pt | `0.82\textwidth` | 0.826 | 5.37--5.70 pt, 627 characters |
| Fig. 11 `stratified_completeness` | 490 pt | `0.82\textwidth` | 0.856 | 5.14--5.99 pt |

Fig. 4 is the worst case by volume: 1449 characters — the entire 88-row system list — at 5.6 pt.
Fig. 3 is called "the roadmap" in the Introduction and its right-hand ledger panel is at 5.5 pt.
**Fix:** raise the three `figure*` widths from 0.80--0.84 to `\textwidth` (a free 20 per cent) and,
for Fig. 4, either enlarge to a full page in the appendix or move the star list to a table and keep
only the coverage histogram in the figure.
By contrast Figs. 5, 7, 2 and 6 are *enlarged* (scale 1.09--1.12) and are comfortable; the
single-column figures (8, 9, 10, 12, 13) are at scale ~1.0 and fine. The problem is confined to the
four `figure*`s drawn on a 490--508 pt canvas and then shrunk.

### P25 — MINOR. Fig. 4's axis labels are visibly corrupted, and the corruption is the P15/P16 bug.

Extracted row labels include: `HD 207129 ()` **and** `HD 207129`; `HD53143 ()` **and** `HD53143`;
`* eta Crv` **and** `eta Crv`; `* g Lup` **and** `HD 139664` — i.e. all four duplicates of P15,
drawn as eight separate system rows, two of them with empty brackets where a Gaia id was stripped.
Also `j1256-1257` (P16), and a set of names whose sign or suffix has been mangled:
`BD05 1668` (for BD+05 1668), `PM J034331958`, `LSR J18353259` (for LSR J1835+3259),
`WD 0407179`, `LP 476-207 384128`, `TWA 3A 696000`, `TWA 3A [576064]`, `HD 139084B 805632`,
`Barta 161 12`, `UCAC2 20312880`, and one truncated with an ellipsis,
`2MASS J05241914-1601153 55...`. The caption meanwhile says "1655 windows on 87 systems".
A reader who looks carefully at this figure will conclude the target list was never curated.
**Fix:** a single `display_name` mapping applied in the label generator — strip `Gaia DR3 nnn`,
restore `+` signs, use the Greek glyph consistently, and merge the duplicates of P15.

### P26 — MINOR. Three floats are reported "stuck" by LaTeX.

`technosignatures_40pc_v3.85.log` carries *"A float is stuck (cannot be placed)"* at input lines
531, 735 and 2118, twice each for the first two, plus two "Deferred float stuck during `\clearpage`
processing". The build is otherwise clean (0 overfull, 0 undefined), so these are the only
placement failures and they are all in the float-dense §3/§4 region. Worth resolving before
submission, since a stuck float can land pages away from its discussion.

### P27 — MINOR. Caption length. Seven captions exceed 120 words; two exceed 200.

Fig. 1: **206 words**. Table 11: **202 words**. Fig. 7: 180. Fig. 9: 157. Fig. 12: 151.
Table 9: 136. Table 10: 136. Total caption text is roughly 4000 words, about 13 per cent of the
manuscript's prose. Table 11's caption contains a complete explanation of the topocentric /
barycentric / stellar frame chain and why the printed column is topocentric — that is body text
living in a caption, and a reader who reads the body first meets the argument twice.
**Fix:** cap captions at ~90 words. Move Table 11's frame-chain explanation into §5.3 (it is
already half there) and Fig. 1's completeness-comparison caveat into §2, where the comparison is
made. Keep the symbol definitions in the caption — those are what make them stand alone.

### P28 — MINOR. Two floats duplicate content that is already in the text.

- **Table 6 (the data path) and §4.2's five-step "final logic" list** and the ten-step
  §4.6 summary and Fig. 3's right-hand ledger panel are four renderings of the same chain, at
  4, 5, 10 and 10 steps respectively. Three would be generous; four is confusing, because the step
  numbering does not correspond between them (Table 6's "step 10" is the rank test; §4.6's "step 7"
  is the rank test; Fig. 3's ledger has its own step 7 and step 8).
  **Fix:** renumber so that the summary list, Fig. 3's ledger and Table 6 share one numbering, or
  drop one of them. If one goes, drop §4.2's five-step list, which is the least specific.
- **Fig. 11 carries two `\label`s** (`fig:stratcomp`, `fig:completeness`) and Table 7 carries three
  (`tab:dwell`, `tab:classcomp`, `tab:compcurve`). That is legal and it works, but
  `\ref{tab:compcurve}` reads as though it points at a completeness *curve* table when it points at
  the completeness *matrix*. Rename to one label each.

### P29 — MINOR. Everything plotted is referred to *somewhere*, with one exception worth checking.

Table 5 ("The survey as searched, and the paper's headline numbers in one place") is referenced
twice, and it is the right object to have. But its caption claims "Every count quoted in this paper
reconciles with it", which after P15 and the 1.1--5.9 kHz s^-1 slip (P30) is a claim the build
cannot currently support. Either extend `audit_numbers_v385.py` to assert it row by row against the
macros, or soften the caption.

---

## 4. Numbers the build cannot see

The macro architecture is excellent (§0), which makes it all the more important to know where it
stops. I extracted every literal numeral in the prose (tables, figures, bibliography and
enumerate-option lengths excluded) and separated physical constants and round scales from
data-derived quantities. About **110 data-derived numbers are typed by hand** and are therefore
invisible to both `audit_numbers_v385.py` and `reproduce_from_catalogue_v385.py`. Three matter now.

### P30 — MAJOR (overlaps round 1's C3, but it is still in the PDF). The drift-ceiling range is
stale in the body and current everywhere else.

> l.1201 (printed p.13): "Across the 1655 windows maximum searched drift rates span
> **1.1--5.9 kHz s^-1**"

against `\DriftKHzHi` = **10.5**, which `reproduce_from_catalogue_v385.py` derives from the
catalogue as 10.4667 and passes, and which Table 5 and App. B both print ("10.5 kHz s^-1 at
872 GHz"). The body sentence is hard-typed and so the audit never sees it. Same sentence: "trial
drift rates per window **2--`\BpSixTrials`**" — the lower endpoint hard-typed, the upper a macro, in
one range.

### P31 — MAJOR. "seven windows against four" appears twice and contradicts the survey's own
13 / 66.

> l.1662 (printed p.14): "the symmetric form of Eq. 2 flags a strict subset of what the
> region-maximum form flags, **seven windows against four** (§G.4, Table 22)"
> and again in App. G.4: "the symmetric criterion flags a strict subset, seven windows against
> four, the three that drop out doing so because the stellar position never exceeded its own
> control ensemble"

The survey has `\NStageOneWin` = **13** symmetric flags and `\NRegionMaxFlag` = **66**
region-maximum flags (Introduction, Table 22 caption). Whatever 7 and 4 were, they are from an
earlier freeze, and as printed the sentence also has the inequality the wrong way round relative to
its own claim ("a strict subset ... seven against four" reads as the subset being *larger*).

### P32 — MINOR. A representative list of the other hand-typed, data-derived numbers.

Not exhaustive; these are the ones I would insist become macros, because each is a measured
quantity that a later round can move:

- l.1071 and l.3787 — `N_eff ~ 30--43` independent spatial trials, typed twice.
- l.1101--1102 and l.3652 — "17 of 57 target/bands", "57 measurements, 17 detections and 40 limits".
- l.1112 — the four local-to-global sigma ratios `0.97 / 1.29 / 0.93 / 1.02`.
- l.1178 — `n_drift` "2--1944" (and see P1).
- l.1356--1359, 1409, 3420 — `T_star = 20.5, 65.3, 217.7` typed **three times**, with "639
  integrations" and "sqrt(639) = 25".
- l.1677--1679 — the Barnard's Star / Wolf 359 EIRPs and continuum limits: `6.2--6.9e13`,
  `7.8--9.1e13`, `0.575`, `0.453` mJy. These are the paper's claim to two first limits; they should
  come from the catalogue.
- l.1730--1733 — "44 per cent", "5.10 and 4.95".
- l.1747 and l.2860 — `1.6e13 W` for UV Ceti "at 2.7 pc", while App. A gives the same star at
  **2.67 pc**.
- l.2519 — CP-72 2713's own headline pair, `T_star = 5.81` against ring maximum `5.68`.
- l.2690 — "131 of 1655 windows contain an in-band catalogued transition".
- l.3197 — "2013 October 6 to 2025 June 11 across 36 proposal codes" in the Acknowledgements.
- l.3328 — "up to 65 channels" where `\MedWin` exists.
- **l.3428 — the worst single instance**: "recovered **17**, `\RecThresh`, **58**, **75** and
  `\RecTwice` per cent at 4, 5, 6, 8 and 10 sigma" — a five-element list in which three elements are
  hard-typed and two are macros. If the campaign is ever re-run, three of the five will silently
  stay behind.
- l.4044--4045, 4091--4092, 4196, 4262 — App. G's region-max diagnostics (`3.7--4.9`, `6.7--7.7`,
  `p = 0.81--1.00`, `5.05 sigma`, `6.23`, `T_star = 5.11`, "the 16 inner probes").

**Fix:** the rule that already works elsewhere in this project — *a number derived from data is
emitted by a generator or asserted at the point of use*. A cheap 80 per cent solution is a CI check
that greps the prose for `\d+\.\d` outside math-only constants and fails on any new one.

---

## 5. Structure and readability

Glenn White has asked for the dense passages to be made readable without losing rigour. I have
ranked the worst 15, hardest first, by a combination of sentence length, number density and how
many distinct claims are packed into one grammatical unit. Each entry gives the printed text, the
specific reason it is hard, and a plainer version at the same rigour. **None of my rewrites drops a
number or a hedge**; they mostly split sentences and put the subject before the qualifications.

### P33 — MAJOR. #1 worst: the Data Availability column sentence. 131 words, 18 commas, one colon,
no full stop for eight lines.

> "The machine-readable catalogue, `per_target_results_v3.85.csv`, carries 1655 rows, one per
> searched window, in 50 self-described columns: identification and distance, band, execution block
> and searched frequency range, channel width, exposure and per-channel rms, the nominal EIRP_5sigma
> trigger with both response-corrected values (§4), P_90 for that window with the x0.48--x1.35
> bracket measured by the injection campaign, the drift ceiling, trial count, eta_drift and
> eta_smear, resolution and search class, the stellar and control peak statistics with the add-one
> rank under both the released and the radius-corrected normalisations and the stage-1 flag each
> implies, the crossing frequency and nearest catalogued transition, the full control geometry
> including its seed, and the disposition verbatim from Table 11."

A 50-item list rendered as prose is unreadable by construction, and (P17) it is also wrong. Plainer:

> "The machine-readable catalogue `per_target_results_v3.85.csv` has one row per searched window,
> 1655 rows in 50 columns, and ships with a data dictionary (`COLUMNS.md`) giving each column's
> definition, units and the symbol of Table 2 it corresponds to. The columns cover four things: what
> was observed (star, system, distance, band, execution block, frequency range, channel width,
> exposure, noise); what the search could reach (the trigger threshold, its two response
> corrections, P_90 with its measured bracket, the drift ceiling, trial count, eta_drift,
> eta_smear); what the search found (the stellar and control statistics, the add-one rank under
> both normalisations and the stage-1 flag each implies, the crossing frequency, the nearest
> catalogued transition); and how the control ensemble was placed (ring centre, radii, count,
> seed)."

### P34 — MAJOR. #2: the seven-limitation "Scope of the constraints" paragraph. 173 words in one
block, seven numbered claims, no line breaks.

> "*Scope of the constraints.* Seven limitations bound what this null result covers, and they are
> collected here so no reader has to assemble them. (1) The spatial screen is empirically
> calibrated, not exactly exchangeable, and the radial correction of §5.3.3 is derived on the
> calibration sample and therefore *not validated out of sample*; no disposition here depends on it.
> (2) The calibration is trustworthy for isolated point sources and not for beams filled by
> resolved circumstellar or foreground emission: in the HD 48370 case 12 per cent of null draws
> exceed every control, so for disc hosts whose CO happens to be fainter the screen is only
> approximately controlled. (3) ..."

The content is exactly right and the list is one of the most valuable things in the paper. The
problem is purely typographic: seven substantive caveats run together as one paragraph, in a
subsection titled *Dwell-fraction completeness* (see P48).
**Fix:** no rewriting needed at all — set it as an `enumerate` with one item per limitation, as the
"Nothing in this paper bounds the prevalence of" list immediately below it already is. That alone
will make it the most-quoted paragraph in the paper.

### P35 — MAJOR. #3: the response-factor sentence in §4's opening. 82 words, four different
multiplicative factors, and the conclusion arrives after the caveat.

> "Injecting unresolved tones of known amplitude into real visibilities and recovering them through
> the unmodified pipeline returns x2.02--x2.69 (median x2.31) across correlator modes, against the
> analytic x2.29 expected for the Hanning response (Appendix B), so P_eff = S_min dnu C_response
> C_smear recovers the injected power: the medians agree to one per cent, the quoted range being
> window-to-window variation in the correlator response and not an error on the estimator."

Plainer, three sentences, same numbers:

> "We calibrated the response correction by injecting unresolved tones of known amplitude into real
> visibilities and recovering them through the unmodified pipeline. The measured factor is x2.31 at
> the median, spanning x2.02--x2.69 across correlator modes, against x2.29 predicted analytically
> for the Hanning response (Appendix B): the medians agree to one per cent. The spread is
> window-to-window variation in the correlator response, not an error on the estimator, so
> P_eff = S_min dnu C_response C_smear recovers the injected power."

### P36 — MAJOR. #4: the five-term systematic budget as a single semicolon chain. 71 words.

> "Five terms enter the systematic budget, each multiplying S_min and hence EIRP_5sigma directly:
> the ALMA absolute flux scale, 5--10 per cent and band- and epoch-dependent; residual atmospheric
> phase after water-vapour correction and phase referencing; the primary-beam model at the stellar
> offset; visibility calibration; and the instrumental spectral response, median x2.29, the largest
> of the five and carried explicitly as P_eff by the reading rule below."

Two of the five carry a number and three do not, which is invisible in a semicolon chain. Plainer:
set the five as a short list, and give each a magnitude or say "not quantified":

> "Five terms enter the systematic budget, each multiplying S_min and so EIRP_5sigma directly:
> (i) the ALMA absolute flux scale, 5--10 per cent, band- and epoch-dependent; (ii) residual
> atmospheric phase after water-vapour correction and phase referencing, 5--20 per cent at
> 230--345 GHz; (iii) the primary-beam model at the stellar offset, median x1.00, 90th percentile
> x1.02; (iv) visibility calibration, not separately quantified here; and (v) the instrumental
> spectral response, median x2.29. The last is the largest by an order of magnitude and is carried
> explicitly as P_eff."

### P37 — MAJOR. #5: the out-of-sample rank paragraph, which ends on a bracket that excludes its
own median.

> "Windows inside a block share a calibration and blocks of a unit set a target, so the
> window-level figure (D = 0.08, **p =< 0.01**) treats as independent what is not; clustering
> removes neither the shift nor its significance, 99 of the 149 blocks having a mean rank below 0.5
> (sign test p < 0.001) and a star-clustered bootstrap placing the median at **0.405 (95 per cent
> interval 0.42--0.46)**."

Three separate problems in one sentence, and the second is a genuine defect I was able to trace to
its generator.

**(a) A typographic error.** `$p=\HOKsP$` with `\HOKsP` = `<0.01` prints as **"p =< 0.01"**, which
is not a relation. Emit the macro without the `$p=` prefix, or store `\HOKsP` as `0.01` and print
`p < \HOKsP`.

**(b) Two samples spliced into one sentence.** The median 0.405 does not lie in its own quoted
interval 0.42--0.46 — and the reason is that they are not computed on the same data. I traced both:

- `\HOBlockBelow`/`\HOBlockN` (99 of 149) and `\HOBootLo`--`\HOBootHi` (0.42--0.46) are written by
  `v353_heldout_cluster.py`, which reads `heldout_v352.json`: **603 windows in 150 execution
  blocks**, the *processing-order campaign* set. I recomputed its pooled median directly from that
  file: **0.427**, which sits comfortably inside 0.42--0.46.
- `\HoRankMed` = 0.405 is the **pre-registered reserved sample's** median — 315 windows, 77 blocks,
  36 stars — and at l.2104 it is correctly printed with *its* interval, `\HoRankMedLo`--`\HoRankMedHi`
  = **0.341--0.458**, which does contain it.

So one paragraph about the campaign (l.2191--2209, "The rank distribution of the remaining
`\HONoiseWin` windows is **the campaign's** most consequential result") quotes the *reserved
sample's* median three times, once inside the campaign's bootstrap interval. The number that belongs
there is 0.427.
This is why round 1's C11 and the disposition disagreed: the disposition checked the l.2104
occurrence, which is right, and the reviewer had read the l.2202 occurrence, which is not.
**Fix:** emit a `\CampRankMed` = 0.427 from `v353_heldout_cluster.py` alongside its interval, use it
at l.2193 and l.2202, and add an assertion to the audit that every median printed with an interval
lies inside it. That assertion is three lines and would have caught this class of error in round 1.

**(c) Density.** 58 words, four statistics, three of them parenthetical.

Plainer (with the campaign median restored):



> "Windows inside a block share a calibration, and blocks of a scheduling unit share a target, so
> the window-level statistic (D = 0.08, p < 0.01) treats as independent what is not. Clustering
> removes neither the shift nor its significance. 99 of the 149 blocks have a mean rank below 0.5
> (sign test, p < 0.001), and a star-clustered bootstrap puts the campaign median at 0.427, 95 per cent
> interval 0.42--0.46."

### P38 — MAJOR. #6: the primary-beam floor sentence. 62 words, six numbers, one of them a quasar
(P16), and a parenthesis inside a parenthesis.

> "*The offsets are bimodal and the floor sits in the gap*: the last retained window has response
> 0.55 at 0.46 theta_PB (j1256-1257 Band 7, 1.81x), the first window beyond it has response 0.35 at
> 0.62 theta_PB (2.88x), and nothing lies between them, so the rule binds prospectively without
> having been drawn around the present sample."

Plainer:

> "The offsets are bimodal, and the floor sits in the gap. The last window the rule retains has a
> primary-beam response of 0.55, at 0.46 theta_PB -- a correction of x1.81. The first window it
> excludes has a response of 0.35, at 0.62 theta_PB, a correction of x2.88. Nothing lies between
> them, so the rule binds prospectively rather than having been drawn around this sample."

(and drop the target name, or fix it per P16.)

### P39 — MINOR. #7: the pseudo-star paragraph. 70 words, two p-values, a subordinate clause that
reverses the argument mid-sentence.

> "Ranking each control against the other 512-1 by the rule used for the star gives 220 672
> pseudo-star ranks, uniform to the resolution the ensemble can express (p = 0.37) in every band and
> at both channelisations; that geometry cannot by itself detect a centre-versus-annulus asymmetry,
> so the test that can is the two-sample comparison of the 1655 real stellar ranks against the
> pooled pseudo-ranks, and it returns p = 0.38."

"512-1" printed as arithmetic in running text is jarring. Plainer:

> "Ranking each control against the other 511 by the rule used for the star gives 220 672
> pseudo-star ranks. They are uniform to the resolution the ensemble can express (p = 0.37), in
> every band and at both channelisations. That geometry cannot detect a centre-versus-annulus
> asymmetry on its own, so we also compare the 1655 real stellar ranks with the pooled pseudo-ranks
> as two samples; that test returns p = 0.38."

### P40 — MINOR. #8: the beta Pic Band 6 "trials load" sentence, which argues by pile-up.

> "The Band 6 window is a line tuning, 53.9 MHz wide at 15.26 kHz, so it holds 3533 channels like a
> wide window and searches 1944 trial drift rates against a survey median of 4, the largest trials
> load in the survey at eta_drift = 422: this rank is harder to earn than a typical one, not
> easier."

Six numbers and a conclusion in one sentence, with the point ("harder, not easier") last. Plainer:

> "That window is a narrow line tuning -- 53.9 MHz wide, 15.26 kHz channels -- so it holds 3533
> channels, as many as a wide window, and its drift grid runs to 1944 trial rates against a survey
> median of 4. At eta_drift = 422 it carries the largest trials load in the survey. A first rank
> there is harder to earn than a typical one, not easier."

### P41 — MINOR. #9: the CP-72 repeat-block comparison. 59 words, five matched quantities, and the
inference arrives in a subordinate clause.

> "It matches the first in tuning, channel width, channel count, integration count and on-source
> time, with frequency axes registered to 0.18 of a channel, and is the deeper of the two (1.964
> against 2.097 mJy), so a persistent emitter at the first block's flux would have appeared at
> T_star = 6.21, above both the trigger and that window's largest control 5.93."

Plainer:

> "The repeat block matches the first in tuning, channel width, channel count, integration count and
> on-source time, and their frequency axes register to 0.18 of a channel. It is also the deeper of
> the two, 1.964 mJy against 2.097. A persistent emitter at the first block's flux would therefore
> have appeared there at T_star = 6.21 -- above the trigger, and above that window's largest control
> at 5.93."

### P42 — MINOR. #10: the Hanning over-count derivation, which mixes a derivation, two predictions
and two observations in three sentences.

> "Hanning smoothing correlates neighbouring channels at rho_1 = 2/3, rho_2 = 1/6, so
> 1+2rho_1+2rho_2 = 2.67 grid channels carry one channel's information, and the drift grid is
> oversampled two to one, giving a combined over-count 2.67 x 2 = 5.3. Dividing n_cells by it lowers
> the predicted maxima from 5.74 to 5.45 in the fine class and from 4.47 to 4.10 in the coarse one,
> against 5.79 and 4.44 observed: a residual +6 and +8 per cent in the two classes independently."

The second sentence carries six numbers in two parallel comparisons and the reader has to hold
four of them to reach the conclusion. **Fix:** make it a three-row table (class, predicted before,
predicted after, observed, residual). Four numbers become a column and the sentence becomes one
line.

### P43 — MINOR. #11: the stratified injection campaign's configuration span, six ranges in one
clause. 59 words.

> "A drifting carrier was injected into the retained per-integration spectra of 28 further windows,
> one per star, spanning Bands 3--10, 15.3--977 kHz channels, 45--485 integrations, 7--1186 drift
> trials and both the 12 m array and the ACA, pushed through the pipeline's own baseline removal and
> de-drift stack on the search's drift grid: nine amplitudes, 4032 trials."

Plainer: keep the sentence but break the span out as a parenthetical list or a small table. The
ranges are the point of the paragraph — they are evidence of coverage — and they are currently
delivered at a rate the reader cannot absorb.

### P44 — MINOR. #12: the line-mask widening test, whose caveat interrupts its own result.

> "That half-width was widened after the beta Pictoris crossings had been seen, so the safeguard
> belongs here rather than in a later section: reclassifying all 75 crossings at +/-20, +/-30,
> +/-50 and +/-100 km s^-1 admits no new unattributed outlier -- a one-sided test, see §5.3.7 --
> and at every width CP-72 2713 remains the only unmasked one."

The em-dashed caveat sits between the verb and its object. Plainer:

> "The half-width was widened after the beta Pictoris crossings had been seen, so the safeguard
> belongs here rather than in a later section. Reclassifying all 75 crossings at +/-20, +/-30, +/-50
> and +/-100 km s^-1 admits no new unattributed outlier, and at every width CP-72 2713 remains the
> only unmasked one. That test is one-sided by construction (§5.3.7): widening the tube can only
> mask more."

### P45 — MINOR. #13: the five-step candidate definition. 105 words, five roman numerals, one
sentence.

> "The final logic is five steps, in order: (i) a channel x drift cell at the stellar position
> reaches T_star >= 5, a fixed trigger power and not a calibrated p-value; (ii) the stellar
> statistic exceeds all 512 controls, which prioritises the window for examination; (iii) the event
> survives line and instrumental vetting; (iv) the emission is an unresolved source *at the stellar
> position* in the visibilities, tested by phase-rotating the event's own channel to the star and
> requiring a positive real part with an imaginary part consistent with zero (§5.3); and (v) it
> recurs at the same tuning in an *independent epoch*, or acquires independent confirmation."

This is the most important sentence in the paper and it is one sentence. **Fix:** `enumerate` with
five items. Nothing else needs to change. (And see P28 on renumbering to match Table 6 and §4.6.)

### P46 — MINOR. #14: the intra-integration smearing paragraph, six counts with four different
denominators.

> "Intra-integration smearing is negligible for 446 of the 455 windows that carry a value: at most
> 1.10 channels, median 0.001. 9 windows have eta_smear < 0.99 (Appendix A); 5 of them, all 15.3 kHz
> Band 6 windows and so among the most drift-capable here, carry effective thresholds 1.65--1.74x
> nominal, and 2 are stage-1 outliers."

446, 455, 9, 5, 2 — nested subsets of subsets with no signposting, and a sentence beginning with a
numeral ("9 windows"). Plainer:

> "Of the 1655 windows, 455 carry a smearing value. Smearing is negligible in 446 of them: at most
> 1.10 channels, median 0.001. The remaining 9 have eta_smear < 0.99 (Appendix A). Five of those
> nine -- all 15.3 kHz Band 6 windows, and so among the most drift-capable here -- carry effective
> thresholds 1.65 to 1.74 times nominal; two of the nine are stage-1 outliers."

### P47 — MINOR. #15: the commit-timestamp defence, which is a paragraph about the authors rather
than about the experiment.

> "Local commit timestamps can be rewritten, so they are not by themselves evidence of anything: the
> dates above are corroborated by the GitHub server-side push times for the same commits, which the
> repository's API exposes and which the authors cannot alter, and by the Zenodo deposit's own
> minted date."

The substance is worth one clause; as written it invites the reader to imagine the accusation it is
pre-empting. Plainer:

> "The dates are corroborated by GitHub's server-side push times for the same commits, which the
> authors cannot alter, and by the Zenodo deposit's minted date."

---

### Structural items

### P48 — MAJOR. Three major topics are filed under a subsection whose title does not describe them.

§4.5 is titled **"Dwell-fraction completeness"** and runs 1708 words. It contains, after the dwell
material: *Interference rejection* ("which is an operative gate" — satellite constellations, ITU
5.340, the near-field emitter caveat), *Scope of the constraints* (the seven limitations of P34),
*What was searched* (the Class A and Class B domain statements), and *Nothing in this paper bounds
the prevalence of* (a ten-item list). A reader looking for the RFI argument or the scope of the
null result will not look under "Dwell-fraction completeness", and neither will a referee.
**Fix:** promote them. §4.5 Dwell-fraction completeness; §4.6 Interference rejection; §4.7 Scope of
the constraints (with the ten-item "does not bound" list inside it); then the summary. This is a
pure `\subsection` insertion and costs nothing in length.

### P49 — MAJOR. §4.2 is a 2576-word subsection with no internal signposts.

"Final candidate definition and statistical interpretation" is the longest block in the paper and
covers, in order: the five-step candidate logic; where the statistic is formed; Eq. 2 and its noise
scale; *why this form and not a region maximum*; the baseline filter and its passband ceiling; the
control ring geometry and seed; the reconstruction of the geometry from code; the primary-beam cost
of off-centre controls; N_eff and correlation; the rank resolution against the Bonferroni scale;
the residual-continuum asymmetry argument; the R_sigma test and the local sigma re-computation; and
the exchangeability argument restated. Thirteen topics, no headings. Several of them are restated
later (the region-maximum argument appears twice within the subsection alone, at l.980 and l.1128).
**Fix:** four `\paragraph` or `\subsubsection` breaks — *the statistic*, *the control ensemble*,
*why a single position and not a region*, *what could break exchangeability* — and delete the
second statement of the region-maximum argument.

### P50 — MINOR. `\label{sec:benchmarks}` has no section.

l.1284 is a bare `\label{sec:benchmarks}` sitting at the end of §4.4 *Frequency and velocity
reference frames*. The Arecibo and filled-aperture benchmarks that follow it are referenced from
three places as "§`\ref{sec:benchmarks}`", which resolves to §4.4 — a section whose title tells the
reader nothing about benchmarks. **Fix:** make it a real `\subsection{Power benchmarks}`.

### P51 — MINOR. §5.1 and Appendix D are mis-placed.

- **§5.1 "Barnard's Star and Wolf 359"** is a 67-word subsection about two stars, placed before the
  data-quality exclusions and before the search results. It is a nice result (apparently the first
  mm/submm limits for both) and it is currently the first thing in the Results section, ahead of the
  survey. **Fix:** move it to the end of §5, or into §6.1 where the "what could ALMA detect"
  case studies are.
- **Appendix D "Per-target results"** contains 97 words, Table 16 (the selection function vs the
  Gaia census), Fig. 12 (the drift/acceleration selection function) and Table 17 (per-band
  characterisation) — and no per-target results, which are in the CSV. **Fix:** retitle it
  "Sample and coverage tables", or move Fig. 12 next to the drift-ceiling discussion in §4.3 where
  it is actually cited from.

---

## 6. Terminology consistency

The paper is unusually disciplined about defining terms (Tables 1 and 2), and it explicitly
polices several of them ("`narrowband` describes the assumed intrinsically narrow transmitter and
never the resolving power of the data"; "Class B ... is never described as a narrowband search
anywhere in this paper"). I checked whether the discipline holds. Mostly it does. Six places where
it does not.

### P52 — MAJOR. The Class B channel width is stated three different ways.

- l.1635 (§5 opening): "their channels are **7.8--31.25 MHz** wide"
- l.1807 (§5.3): "a **15--31 MHz** channel dilutes a narrow feature"
- l.3929 (App. F): "A **15.6--31.25 MHz** channel dilutes a narrow circumstellar line"

Three ranges for one quantity, the second and third both used in the *same argument* (that a coarse
channel dilutes a narrow line). `\ChanBMinMHz`/`\ChanBMaxMHz` exist and are used in §4; these three
are hard-typed. **Fix:** one macro pair everywhere.

### P53 — MAJOR. The released catalogue's column names contradict the paper's own nomenclature.

Table 2 says "Every term and every power scale in this paper is defined here and nowhere else", and
§4.2 insists at length that `T` is *"not a detection significance"*, *"a trigger level and not a
tail probability"*, *"neither assumed nor shown to be Gaussian"*. The catalogue then calls it
**`star_snr`** and **`ctrl_max_snr`**. A reader who takes the file at its word will read a
signal-to-noise ratio, which is exactly the misreading §4.2 spends two paragraphs preventing.
Likewise `eirp_nominal_W` is `P_trig`, `eirp_eff_total_W` is `P_eff`, `eirp_p90_W` is `P_90`,
`c_response_smear` is `C_response C_smear` — none of these names appears in Table 2 and no mapping
is given.
**Fix:** either rename the columns (`t_star`, `t_ctrl_max`, `p_trig_W`, `p_eff_W`, `p90_W`) in a
versioned release, or — cheaper and just as good — add the mapping as a column of Table 2:
"symbol | meaning | catalogue column".

### P54 — MINOR. Five names for the hold-out.

"external calibration sample" (4, and the section title), "calibration sample" (10), "hold-out"
(14), "holdout" (3, unhyphenated), "reserved blocks" (6), plus "the campaign" (7) and
"the processing-order calibration set" (1) for the *different*, older set. Two distinct objects
share overlapping vocabulary: the pre-registered hold-out (77 blocks) and the processing-order
calibration set (1322 windows). In §5.3.1 they alternate paragraph by paragraph, and the reader
must infer which "calibration sample" is meant from context. The prior editorial rule recorded for
this project is *external calibration sample*, never "held-out"/"post-freeze" — but the current text
uses "hold-out" 14 times and the section is built around the reservation.
**Fix:** pick two names and never deviate: e.g. **"the reserved sample"** (pre-registered, 77
blocks) and **"the processing-order calibration set"** (1322 windows). Put both in Table 1.

### P55 — MINOR. Four names for one flagged object.

"stage-1 outlier" (33), "stage-1 spatial outlier" (9), "stage-1 window" (8), "flagged window" (12),
"stage-1 flag" (2). These all denote the same thing: a window whose `T_star` exceeds all 512
controls. Table 2 defines only one of them. "Flagged window" is the worst offender because the paper
also uses "flag"/"flagging" in the CASA sense — *"one that lost a hand **to flagging** inside QA2"*,
*"the measured 20.5 is that value less weighting and **flagging** losses"*, *"four chi^1 Ori Band 3
windows **flagged** as elevated"*. Two incompatible meanings of the same verb, sometimes on the same
page.
**Fix:** use **stage-1 outlier** for the object and **stage-1 flag** only for the boolean catalogue
column; reserve "flagging"/"flagged" for the data-quality sense, and say "promoted"/"selected"
elsewhere.

### P56 — MINOR. "screen" carries four jobs.

"screening statistic", "screening device", "candidate-generation screen", "spatial screen",
"spatial-outlier screen", "calibrated screen", "anomaly screen" (the *continuum* lane's, a different
thing entirely), "RFI screen", "repaired screen", "adopted screen". The Introduction's third
contribution is "spatial-control screen calibration"; the abstract says "the spatial-outlier
screen"; §5 says "that screening device selects a window for examination". **Fix:** one name —
**the spatial control screen** — everywhere, and rename the continuum lane's to "the continuum
anomaly test" so the word "screen" means one thing.

### P57 — MINOR. Two small ones.

- **"trigger" vs "threshold" vs "crossing".** Mostly disciplined (Table 1 defines `P_trig`; a
  crossing is a cell reaching `T_star >= 5`). But "threshold" appears 100 times in at least three
  senses: the trigger level (5 sigma), the EIRP threshold (a power), and the promotion gate. The
  phrase "nominal trigger thresholds span 5.1e13--9.1e16 W" uses two of them in three words.
  Suggest reserving **trigger** for the 5 sigma level, **threshold power** for the EIRP, and
  **gate** for the control maximum — all three already appear, they just need to be exclusive.
- **`\NCtrlCap` = 512 = `\NCtrl`.** l.1076 reads "the annulus contains far more resolution elements
  than the **512** positions drawn in all but those configurations", which implies a cap different
  from 512 and is printed identically to the ensemble size. If the cap is genuinely 512, say "than
  the 512 positions drawn"; if it is something else, the macro is wrong.

---

## 7. The abstract, read cold

I read it as a radio astronomer who has not read the paper. It is four paragraphs, 309 words,
1921 characters. Structurally it is good: what was searched, what the primary experiment is, what
was found, what the sample cannot speak for. The fourth paragraph in particular is the best thing in
it and I would not cut a word of it. Seven problems.

### P58 — MAJOR. **The abstract is one character over the arXiv limit.**

The paper's own tool says so: `abstract_limit.py` reports *"rendered abstract: 1921 characters,
309 words (arXiv limit 1920, headroom **-1**)"*. Whatever else is done, this has to be fixed, and
several of the cuts below do it several times over.

### P59 — MAJOR. "9 are carbon monoxide, 8 the beta Pictoris debris disc" reads as 17 of 13.

> "13 spectral windows pass the detection threshold and the spatial-outlier screen. 9 are
> circumstellar or foreground carbon monoxide, 8 the beta Pictoris debris disc, in two transitions
> and 8 blocks. The remaining 4 have no identification"

A cold reader sees 9 + 8 = 17 out of 13, and then "the remaining 4" (= 13 - 9) confirms the
arithmetic was the other one. The nesting is not marked.
**Fix:** "9 are circumstellar or foreground carbon monoxide — **8 of them** the beta Pictoris debris
disc, seen in two transitions and 8 execution blocks. The remaining 4 have no identification."
Costs two characters.

### P60 — MAJOR. Four pipeline terms are used before they exist.

"triggers the search", "the spatial screen", "promotion past", "pass the detection threshold and the
spatial-outlier screen". A reader who knows radio astronomy but not this paper does not know what a
"spatial screen" is, what "promotion" means, or what it is promotion *to*. In particular:

> "promotion past the spatial screen needs x1.16 more"

is, cold, unreadable: 1.16 times more than what, past what, to what end. **Fix:** either say what it
is — "a window is flagged only if the signal at the star also exceeds all 512 control positions
offset from it in the same field, which needs a further x1.16 in power" — or drop the clause, which
saves 56 characters and loses nothing a reader can use at this length. I would drop it, and keep it
in §5.4 where it is properly set up.

### P61 — MAJOR. The two chance expectations are given without telling the reader which to use.

> "The remaining 4 have no identification, against 3.2 expected by chance over all searched windows
> or 1.1 over the drift-resolving ones alone"

Cold, this reads as the authors declining to commit — and 4 against 1.1 is a very different
statement from 4 against 3.2. Round 2 has already criticised the *choice* of reference class; my
point here is presentational: whichever the paper settles on, the abstract must state one number and
say in four words why. **Fix (if the body's preferred figure is the block-resampled one):**
"against 3.2 expected by chance across all searched windows; restricted to the drift-resolving
windows, where all four lie, the expectation is 1.1 and the excess is about 2 sigma."

### P62 — MINOR. Nothing tells the reader what frequencies were searched.

The abstract says "118.1 GHz of unique sky frequency" and "113.3 GHz ... once molecular lines are set
aside", but never says *where* — no band range, no GHz span. For a submillimetre technosignature
search that is the first thing a reader wants. **Fix:** "covering ALMA Bands 3--10, 84--950 GHz,
with 118.1 GHz of unique sky frequency actually searched". That also justifies the paper's claim to
be extending the searched regime above ~115 GHz.

### P63 — MINOR. 2.4e15 W has no anchor.

A reader outside SETI has no idea whether 2.4 x 10^15 W is a strong limit or a weak one. The paper
has the anchor ready — the Arecibo planetary-radar EIRP scale, used throughout §4.4 and Fig. 1.
**Fix:** "...above 2.4 x 10^15 W of equivalent isotropic radiated power at the median window and
6.3 x 10^13 W at the deepest, i.e. from a few times to a few thousand times the EIRP of the Arecibo
planetary radar." One clause; it is what makes the number mean something.

### P64 — MINOR. What I would cut.

- **"4.1 TB of raw data"** — a property of the authors' disk, not of the experiment. (17 chars)
- **"and 3 left no usable window"** — a 3-of-484 bookkeeping detail. (28 chars)
- **"promotion past the spatial screen needs x1.16 more"** (P60). (56 chars)
- **"with a window-to-window scatter of x0.48--x1.35"** — keep the *fact* of a factor-two spread,
  drop the two-digit bracket: "with about a factor of two of window-to-window spread". (~8 chars,
  but a large gain in readability)
- **"in two transitions and 8 blocks"** — implied by "recovered blind"; cut if space is tight.

Those five cuts free roughly 110 characters, which more than pays for P59, P61, P62 and P63.

### P65 — MINOR. One dangling reference in the opening of the Introduction, worth fixing at the
same time.

> l.137: "The millimetre and submillimetre regime is very sparsely searched, and everything above
> **that axis's** ~115 GHz upper limit more sparsely still."

There is no axis. The antecedent is the "haystack of transmitter frequency, bandwidth, power and
duty cycle" two sentences earlier — the reader has to reconstruct that "that axis" means the
frequency axis of the haystack. The same construction recurs at l.2936 ("only Band 3 falls inside
that axis's 10 MHz--115 GHz span"). **Fix:** "everything above the ~115 GHz upper limit of the
surveyed frequency range more sparsely still."

---

## 8. Indexed summary

**65 points: 27 MAJOR, 38 MINOR.** Nothing here challenges the null result. The MAJOR items cluster
into four families: (a) a target-list curation failure that the release exposes and the manuscript
inherits (P15, P16, P25); (b) reproducibility claims that are stronger than the release supports
(P17, P18, P19); (c) method steps specified to five decimal places in some places and not at all in
others (P1--P5); (d) presentation defects a copy-editor would return the paper for (P22, P23, P52,
P58).

| ID | Rank | Where | Issue | Fix in one line |
|---|---|---|---|---|
| **P1** | MAJOR | l.1178 | drift-grid *step* rule never given, only endpoints | state `n_drift` formula |
| **P2** | MAJOR | §4.2, Tab. 6 | band-edge trimming undescribed; affects the frequency union | one sentence after step 3 |
| **P3** | MAJOR | l.1885 | "eight control positions" — which eight of 512? | name the selection rule |
| **P4** | MAJOR | l.1931 | drift-following visibility fit specified in 11 words | short App. G subsection |
| **P5** | MAJOR | l.1244 | 8-per-target cap: which 8? "deepest single window": when? | state both rules |
| P6 | MINOR | l.2090 | hold-out hash `[:8]` of what, base what, UID in what form | one clause |
| P7 | MINOR | l.1035 | `probe_positions()` RNG and draw order unstated | one clause |
| P8 | MINOR | §4.1 | Class A/B numeric boundary appears only in a caption | put 5 MHz in §4 |
| P9 | MINOR | l.1014 | "usable channels" undefined | define |
| P10 | MINOR | §4.2 | flagged-data arithmetic inside the MAD/stack unstated | one sentence |
| P11 | MINOR | App. D | `rms_mJy` is not the trigger noise; DA says it is | fix DA wording |
| P12 | MINOR | l.1723 | 35 `(eb, flo, chanw)` keys repeat; 1616 vs 1655 unexplained | name the key, reconcile |
| P13 | MINOR | §5.3.7 | masked transition list not enumerated or version-stamped | add cut + catalogue version |
| P14 | MINOR | Tab. 6 | pb-correction and mask ordering implied, not shown | add to Table 6 |
| **P15** | MAJOR | CSV / title / abstract | **4 stars duplicated under 2 names and 2 `system_id`s: 94/87 is really 90/83** | canonicalise; assert no two systems share a distance |
| **P16** | MAJOR | CSV / l.1263 / Fig. 4 | `j1256-1257` (ALMA calibrator designation) is one of the 94 "stars" | resolve or remove |
| **P17** | MAJOR | DA | column list disagrees with the file: 3 undisclosed statistics, a duplicate column, `disposition` blank in 1645/1655 | ship `COLUMNS.md` |
| **P18** | MAJOR | l.3241, l.3215 | "rebuilds all 68 byte for byte" — 3 are frozen copies (14 macros, incl. the haystack fraction), and the 68 excludes 13 generated tables | write generators or declare |
| P19 | MINOR | l.3236 | "opens the catalogue and nothing else" — it reads the macros too | reword |
| P20 | MINOR | audit | 5 checks silently skipped; 36 quoted | make skip a failure |
| P21 | MINOR | l.3245 | 6 unprinted figures, 2 declared | list or move |
| **P22** | MAJOR | 7 floats | **Figs. 2, 6, 7, 9 and Tables 4, 8, 13 are never referenced** | one `\ref` each |
| **P23** | MAJOR | Fig. 14 | `0.64\textwidth` on a 504 pt canvas: **all text 3.2--4.7 pt** | `width=\textwidth` |
| P24 | MINOR | Figs. 1, 3, 4, 11 | bulk text 5.1--5.7 pt printed | widen to `\textwidth` |
| P25 | MINOR | Fig. 4 | axis labels show the P15 duplicates, `HD 207129 ()`, mangled signs | `display_name` map |
| P26 | MINOR | log | 3 floats reported "stuck" | resolve placement |
| P27 | MINOR | captions | 7 over 120 words; Fig. 1 = 206, Tab. 11 = 202 | cap at ~90 |
| P28 | MINOR | §4.2/§4.6/Tab. 6/Fig. 3 | four renderings of one chain, four numberings | unify or drop one |
| P29 | MINOR | Tab. 5 | "every count reconciles with it" not asserted by the build | assert or soften |
| **P30** | MAJOR | l.1201 | "1.1--5.9 kHz s^-1" against the derived 1.1--10.5 | use the macro |
| **P31** | MAJOR | l.1662, l.4323 | "seven windows against four" against 13 / 66 | re-derive |
| P32 | MINOR | ~110 sites | hand-typed data-derived numbers invisible to both audits | macro-ise; CI grep |
| **P33** | MAJOR | DA | worst sentence in the paper: 131 words, 18 commas | split + data dictionary |
| **P34** | MAJOR | §4.5 | seven limitations as one 173-word paragraph | set as `enumerate` |
| **P35** | MAJOR | l.695 | response-factor sentence, 82 words, 4 factors | 3 sentences |
| **P36** | MAJOR | l.713 | 5-term budget as a semicolon chain, 2 of 5 quantified | list + magnitudes |
| **P37** | MAJOR | l.2199--2203 | prints "p =< 0.01"; **the reserved sample's median 0.405 is printed inside the campaign set's interval 0.42--0.46** (campaign median is 0.427) | emit `\CampRankMed`; assert median-in-interval |
| **P38** | MAJOR | l.1263 | pb-floor sentence, 62 words, nested parentheses, quasar | 4 sentences |
| P39 | MINOR | l.3906 | "the other 512-1" in running text | 511 |
| P40 | MINOR | l.2480 | 6 numbers before the point | reorder |
| P41 | MINOR | l.2529 | 5 matched quantities + inference in one sentence | split |
| P42 | MINOR | App. F | 6 numbers in 2 parallel comparisons | make it a table |
| P43 | MINOR | l.3451 | 6 ranges in one clause | break out |
| P44 | MINOR | l.789 | caveat between verb and object | move to its own sentence |
| P45 | MINOR | l.922 | the 5-step candidate definition as one 105-word sentence | `enumerate` |
| P46 | MINOR | l.1209 | 446/455/9/5/2 nested subsets, no signposts | restate with denominators |
| P47 | MINOR | l.2083 | commit-timestamp defence reads defensively | one clause |
| **P48** | MAJOR | §4.5 | RFI rejection + scope of constraints filed under "Dwell-fraction completeness" | promote to subsections |
| **P49** | MAJOR | §4.2 | 2576 words, 13 topics, no headings, one argument twice | 4 breaks; delete the repeat |
| P50 | MINOR | l.1284 | `sec:benchmarks` is a bare label inside §4.4 | make it a subsection |
| P51 | MINOR | §5.1, App. D | tiny 2-star subsection opens the Results; App. D has no per-target results | move / retitle |
| **P52** | MAJOR | l.1635/1807/3929 | Class B channel width stated as 7.8--31.25, 15--31 and 15.6--31.25 | one macro pair |
| **P53** | MAJOR | CSV vs Tab. 2 | `star_snr` for a statistic the paper insists is not an SNR; no symbol-to-column map | rename or map in Table 2 |
| P54 | MINOR | §5.3.1 | 5 names for the hold-out, 2 for the other calibration set, interleaved | fix two names |
| P55 | MINOR | throughout | 4 names for a stage-1 outlier; "flag" also means CASA flagging | one name each |
| P56 | MINOR | throughout | "screen" does 4 jobs, incl. the continuum lane's | one name |
| P57 | MINOR | throughout | trigger/threshold/gate overloaded; `\NCtrlCap` = `\NCtrl` | make exclusive |
| **P58** | MAJOR | abstract | **1921 chars against the 1920 arXiv limit** | see P64 |
| **P59** | MAJOR | abstract | "9 are CO, 8 the beta Pic disc" reads as 17 of 13 | "8 of them" |
| **P60** | MAJOR | abstract | trigger / screen / promotion used before they exist | define or drop |
| **P61** | MAJOR | abstract | two chance expectations, no guidance | commit to one |
| P62 | MINOR | abstract | no frequency range or band list | add "Bands 3--10, 84--950 GHz" |
| P63 | MINOR | abstract | 2.4e15 W with no anchor | compare with Arecibo |
| P64 | MINOR | abstract | 5 cuts freeing ~110 chars | see list |
| P65 | MINOR | l.137, l.2936 | "that axis's ~115 GHz" has no antecedent | name the axis |

### What I would insist on before acceptance

**P15, P16, P17, P18, P22, P23, P30, P31, P37, P52, P58.** Those eleven are either factual errors in
the release, claims the release does not support, or defects a production editor will bounce. The rest
are improvements, and the readability set (P33--P51) is where the paper will gain most per hour
spent.

### What I would not do

Do not cut scientific content to make room. The paper is long because it is honest about eleven
things most surveys leave out, and every one of those is worth its space. The length savings are
all in captions (P27), in the four-fold repetition of the processing chain (P28), and in the
2576-word subsection that says the region-maximum argument twice (P49) — roughly two pages, with no
loss of rigour.
