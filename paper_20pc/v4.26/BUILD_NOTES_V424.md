# v4.24 — build notes (referee round 23)

One self-contained PDF, **40 pp**, main text **23.47 pp** (cap 25),
`technosignatures_40pc_v4.24.tex`, `openjournal.cls`, built with
`SOURCE_DATE_EPOCH=1577836800`. Target **arXiv then OJA**: no supporting
information, five ancillary files beside the PDF.

Built from v4.23 by `cp -a --reflink=never`; the stale
`technosignatures_40pc_v4.23.{pdf,aux,log,out}` were removed, and every
`__pycache__/` with them. `gate.sh` and `arxivset.sh` take the stem from
`ls technosignatures_*.tex`, so the rename needs no script edit.

## Verification of this build
`make_all.sh` rc 0 · `gate.sh` twice rc 0, logs byte-identical, PDF md5
`52c7585e29f56fc06f1b89146e5ab7de` · **`cleanregen` 280/280 byte-identical**
(both passes rc 0; re-verified after the one prose deletion that followed it
by hashing all 518 products before and after a further `make_all` — **0
differ**) · `audit_numbers` **58 PASS / 0 FAIL / 13 WARN** · **0 overfull
boxes, 0 errors, 0 undefined control sequences** · `arxivset --force` **A8
byte-identical**, 239 items, 5 ancillary files · `genai_sweep` **7 hit lines
across 23 families, every one ordinary English**, `--drive` 23 of 23 ·
`absmeta` OK · `abswords` **245 words** (ceiling 245) · `abschars` **1,535
characters** (arXiv 1920, headroom 385) · `absreq_r17` 7/7 ·
`prosegate_selfref` **PASS, 0 hits, 0 stale pins** · `prosegate_r15` 8/8 ·
`roundcollide` 179/179, 0 problems · `orphanround` 179/179 · `citegate`
68/68, 0 FAIL · `verpin` 19 pins, 19 guarded, 0 FAIL · `valuetwin` 0 FAIL ·
`twinmacro`, `synmacro`, `macrosyn`, `macroleak`, `consistency_v399`,
`prosenum`, `fragstale`, `figorphan`, `censusacct_r17`, `wordcase`,
`minuscheck`, `tabfloor_r17`, `floatfit`, `rotfit` all pass.

## New in the build
| file | round | what |
|---|---|---|
| `screen_r23.py` | **980** | the atmosphere at a radius fixed from the frozen system-temperature specification (two 31.25 MHz channels = 62.5 MHz) and applied topocentrically; the image sideband measured over every Class A window rather than over crossings (8 hits against 10.1 expected, no excess and no clearance); and the response of the single-channel filter to a feature N channels wide, measured on Eq. 1 (exponent 0.81, ×32 at 69 channels, against ×8.5 for a matched filter) |
| `pairacct_r23.py` | **981** | the accounting that takes the widened recurrence window's above-trigger readings to the pairs the trajectory test is asked of: 29 − 11 − 2 = 16, one table, one appendix subsection |
| `senscal_r23b.py` | **982** | the completeness factor and the smearing retention as invariants: the retention enters every released window's limit with exponent one to 3.1e−5 over 404 windows, the one dimensionless multiplier per class that is transferred, both delivered response forms, and the calibration interval on the survey-wide median |
| `fieldread_r23.py` | **311** | which field the statistic is read over, and what the other reading gives, by running `chance_v414.py` twice through its new `--field` option |

## The numbers that moved, and why
- **The atmosphere is screened on both sides.** `chance_v414.py` fixes the
  radius from `calspec_r15.json` before counting and applies it in the
  topocentric frame to the crossings *and* to the control exceedances:
  `\CeObs` **32 → 31** (HD 69830, 321.200527 GHz, −25.15 MHz from H₂O),
  `\CeExp` **25.8 → 24.6** (10 of the 214 exceedances the molecular mask
  leaves, factor 0.9533, redrawn as its own binomial inside the bootstrap),
  `\CeProbNull` **0.14 → 0.13**, and `\CeAddLimNear` **15 (new this round)**.
  ★ **`\CeAddLim` did NOT move**: it was **17** in v4.23 and is **17** here
  (exact 17.459 → 17.504); the **15** is `\CeAddLimNear`, the same bound read
  at the grain of the individual cell, which had no v4.23 value at all. The
  bound inverts P(N ≤ N_obs | λ + add) ≥ 0.05 and **both** inputs moved — λ
  25.79 → 24.59, which raises it, and N_obs 32 → 31, which lowers it — so the
  two cancel to within 0.05 of a crossing. `CHANGELOG.md` has this right; this
  line used to read "`\CeAddLim` **15 → 17**" and was wrong. Screening one
  side only would have manufactured a deficit; `A23` is that symmetry and
  fails on either drive that breaks it.
- **The covering-window scan reads the adopted record**: `\WdNExc` **28 →
  29**, `\WdNEmpty` 300 → 299, `\WdMedKms` 448 → 447, `\WdExpect` unchanged
  at 28.3, and the chain closes 29 − 11 − 2 + 0 = **16** pairs.
- **The other field reading is a measurement, not an assertion**: 35
  crossings against 24.1 at P = 0.027, both sides screened, beside 31
  against 24.6 at P = 0.13.
- **CWTFM on one convention**: `\CwRatioEnriquez` 1.3e5 → **4.4e4**,
  `\CwRatioEnriquezFive` 6.7e5 → **2.2e5**, `\CwBandDex` 2.8 → 2.76,
  `\CwEirpDex` 2.4 → 2.58 (2.76 + 2.58 closes on 2.2e5 to −0.6 per cent).
- **`\BmArcsec` 34 → 25**: 34 arcsec was the top-hat equivalent diameter and
  the sentence called it a width; 25.32 arcsec is the half-power width at the
  coefficient the paper adopts everywhere else.
- **The title** carries `\SurvFreqLoA--\SurvFreqHiA` = 114–873 GHz, the range
  of the carrier search the title's own noun names; the abstract states the
  coverage down to 90 GHz in the sentence that describes the coarse windows.

## Ordering, which is the thing to read before moving anything
- `screen_r23.py` must follow `chance_v414.py` (it reads `chance_v414.json`
  back and requires its own reconstruction to agree **before and after** the
  screen) **and** precede `counts_r15.py`, whose Table A2 row for the
  atmospheric coincidence resolves `\ScRadMHz` out of the macro layer.
- `fieldread_r23.py` must follow `chance_v414.py`; it runs that generator
  twice as a sub-process, and **every path those runs write now carries the
  field suffix** — `PERWIN_OUT` did not, and a `--field` run therefore
  overwrote the deposited per-window factors with the narrower field's
  control ensembles. `si_r18.py`'s S13 caught it 300 lines later.
- `epsx_v423.py` **runs twice**: the first pass before `blockledger_v411.py`,
  whose Table A1 footnote d reads its macros, and a `--final` pass after
  `beam_r19.py`, whose `\BnBestResp` its E13 compares against. The first pass
  prints `E13 DEFER`; the second raises if the macro is absent.
- `pairacct_r23.py` and `senscal_r23b.py` must precede `fragstale.py` and
  `requestsweep.py` respectively — a fragment written after the staleness
  gate is the previous run's file when the gate reads it, and an `\input`
  written after `requestsweep` does not exist when it walks the manuscript.
- `r21_lines.py` and `counts_r15.py` both rebuild the comparison
  independently and both now carry the screen: `counts_r15.py` by executing
  `chance_v414.py`'s head and calling **its** `telluric()` predicate,
  `r21_lines.py` by reading the factor and the removed crossing's key out of
  `chance_v414.json`. Neither reimplements it.

## Round numbers, and a collision that was live
`screen_r23.py`, `pairacct_r23.py` and `senscal_r23b.py` were written in one
wave and **two of them claimed round 980 while a third claimed 981** — each
having checked the number was free against v4.23. Screen keeps 980, pairacct
is renumbered **981**, senscal **982**. `roundcollide` now also has a clause
for **drive** numbers: within one generator a drive number may guard only one
perturbation site, with a declared-reason whitelist for the files where one
perturbation is genuinely written twice.

## THE CLOSE PASS (r23-close, 2026-10-19) — what changed after integration reported green
The round's referee pass found two blockers and ten should-fixes, and five agents woke out of a
wedge and filed ten more items against the built v4.24. All of it was applied in **one** rebuild.

### The page count is 41, by one deliberate decision
- **The manuscript's override of the reference-list leading is DELETED.** It set
  `\bibbaselineskip` to 2.52 mm with an in-source comment admitting it was done so the list would
  not spill a page; the author's standing instruction is that the reference list may not be
  compressed for length, and no approval for it is recorded anywhere. **Measured both ways on the
  same tree: 40 pp with the override, 41 pp at the class default.** On the page the list sets at
  **8.720 pt (3.065 mm)** against the override's **7.660 pt (2.692 mm)** — a 12.2 per cent
  compression, larger than the 6.7 per cent first estimated, because this manuscript passes no
  `apj` option and the default in force is `openjournal.cls:68`'s **3.075 mm**, not line 71's 2.7 mm.
  **Main text is unchanged at 23.48 pp**, so the whole of the growth is in the reference list.
  Nothing was clawed back elsewhere: no figure resized, no table reset, no clause deleted.

### A measurement that was computed and never printed, and a word that was wrong
- `\ScNBroadExp` (0.81) and `\ScNBroadExpMatched` (0.50) were cited nowhere, so Appendix A read
  "spreading a fixed total power over $N$ channels lowers the statistic by **close to $N$** … so a
  feature \ScNBroadChan{} channels wide must carry \ScNBroadRatio$\times$ the power". With N = 69,
  "close to N" is 69×, not 32×. It now prints the exponent — **$N^{\ScNBroadExp}$**, and
  $N^{\ScNBroadExpMatched}$ for the matched filter — which is both exact and the measurement R2-4
  asked for.

### `retire_macros.py` is honest, and deliberately not yet fixed
- `GEN_PAIR` matches the macro-**write** shape `m('Name', value)`, which the file's own comment four
  lines above says must never be protected, naming the consequence ("a check that cannot fail").
  Measured: `macros written 6056, retired 0`. Repairing it would delete thousands of macros on a
  push day, so v4.24 makes it **honest** instead: the intended rule is written down as
  `GEN_PAIR_STRICT` and **asserted on 11 fixtures**, `--selftest` demonstrates the shipped wide
  pattern failing three of them, the **retirement backlog (3,983 macros) is printed on every
  build**, and `--strict` performs the retirement the strict rule implies and is documented as not
  for a push day. **Open item for the next round**: run `--strict --dry-run`, read the list, and
  retire with a full build behind it. One name on that list, `RsevNTransferA`, is read by
  `p90_budget_v409.py` through an accessor the strict pattern cannot see — which is exactly why this
  is not being let loose today.

### Gates added, repaired or re-aimed
- **`genai_sweep.py` is in `gate.sh`** — the one check that reads the PDF text layer, and therefore
  the only automatic coverage of the no-version/no-round/no-referee rule **inside a figure**. Its
  own docstring used to forbid gating it, on the grounds that the hits would be whitelisted; that
  objection is answered rather than ignored, with `prosegate_selfref`'s mechanism: every exemption
  in `genai_allow.txt` is a sha1 of (family, sentence), **an unpinned hit fails, a stale exemption
  fails**, a text layer under 100 000 characters fails, and `--selfdrive 1|2` demonstrate the two
  failure directions inside the passing run.
- **`absreq_r17` B5 no longer bans two words.** It required the abstract never to say
  "optimistic|conservative" — a word list standing in for a proposition — and passed for the wrong
  reason, since R2-1(a) requires a direction for the omission and the abstract gives one in a third
  word. It now requires the decorrelation sentence to give that direction **and to name the
  comparable channel-response term that offsets it**; new **drive 9** deletes only the offsetting
  term, which is the edit a length pass makes.
- **`censusacct_r17` A6** pins the four-term subtraction the abstract now invites the reader to do:
  `\MkUnattr − \EvNCrossFlag − \CeNTailCross − \CeTlObsCut == \CeObs` (38 − 4 − 2 − 1 = 31) and
  `\MkUnattr − \RcNExclPoss == 1`. Identities, never values; drives 6 and 7. ★ It was first written
  into `census_r12.py` and **failed the build at line 473**, because three of its terms are written
  by `chance_v414.py`, which runs later — a cross-generator identity belongs in a gate, where the
  whole layer is published, not in a generator, where it can only be as true as the build order.
- **`screen_r23.py` S6b restored** from the first-wave measurement the second patch set dropped,
  with `\ScNearWinPct`: no crossing is screened out without the share of its own window the radius
  covers being measured and published beside it. Drive 14.
- `chance_v414`'s **A19 relabelled**: it reads the undistributed `chance_perwin_v422.json`, so it
  proves the deposited factors are sufficient and says so; the claim about the file a reader holds
  is `si_r18.py`'s S13, which sums the shipped `si_catalogue.txt` off disk.
- `valuetwin.COINCIDENCE` declares `\CeCovPct` against `\ScNearWinPct` — a confidence level and a
  share of one window, equal only by rounding to 95. That gate caught this round's own new macro.

### Prose and record corrections
- **Table A2's caption no longer says the tabulated flag follows the narrow-field statistic** (X1b):
  the accompanying table carries the **adopted** flag, \MtCrossACen{} of them in the census, as its
  own header says. `grep -c "tabulated flag"` is 0.
- The abstract: "line emission explains the strongest **quality-passing** events" is restored (the
  four highest statistics in the survey are in the quality-failing block, so the sentence without
  that word is false); the drift ceiling is a **range**, `\AccelCeilMin--\AccelCeilMax`;
  `\citet{Sheikh2019}` is back as the attribution of the recommended ceiling; the chance bound has
  its object ("up to \CeAddLim{} further **crossings**"); the decorrelation sentence reads as
  English at no word cost. **242 words**, three inside the ceiling, which makes `abswords` a drift
  detector again.
- **The arXiv ASCII field**: the exponent repair's `(?<=x )` lookbehind required a space the
  `\times` glue may shrink to nothing, and `quality-passing` had no repair entry at all — so the
  field could ship `1.5x1015` and did ship `qualitypassing` on the first build of the repaired
  paragraph. Both fixed **in `absmeta.py` and `referee_r17/absascii_r17.py` together**, the final
  net widened to `x ?10\d` in both (only one was named in the queue), and the comment that excused
  a stale repair as catchable by M1/M3 is corrected: it is not — the block is produced by the same
  code, so a stale repair agrees with itself.
- Appendix B now says the screen is **not sharp where it fires** (the window is tuned on the line,
  \ScNearWinPct{} per cent of its own channels are inside the same radius), that what the
  coincidence establishes is that **this window cannot separate the two**, and that the two sides
  are screened by the same rule but **not the same estimator** — the control side as a pooled
  fraction, which is the larger, so the residual asymmetry runs **against** the null.
- Appendix D states that the control side is **recomputable from the file that ships**, row by row.
- `si_r18.py`'s column notes now say which response form the shipped limits use (the delivered
  channel response, not the sinc) and name the sum that rebuilds the expectation.
- `synmacro.py`'s five reason strings say "reserved hold-out", not "pre-registered hold-out".
- `GATE_LOG_V424.txt` is the log of **this** build, captured after the final `make_all.sh`.
