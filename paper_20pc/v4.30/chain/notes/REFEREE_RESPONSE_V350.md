# Response to referees A and B — v3.50

Base: v3.49 (29 pages, main 20.61, abstract 1895/1920, all gates zero).
Result: **v3.50, 29 pages, all gates zero, abstract 1729/1920, 572 macros
with 0 unused, clean regeneration byte-identical, arXiv set 33 items clean
from an empty directory.**

| | v3.49 | v3.50 |
|---|---|---|
| pages | 29 | **29** |
| main text | 20.61 | **19.95** |
| back matter | 1.03 | 0.98 |
| appendices | 6.81 | 7.74 |
| bibliography | 0.31 | 0.31 |
| content total | 28.76 | 28.98 |
| abstract (rendered chars) | 1895 | **1729** |
| errors / undef / multdef / overfull / underfull / Type 3 | 0 | **0** |
| em-dashes in source | 0 | **0** |
| macros defined / unused | 588 / 0 | **572 / 0** |

Both reports are answered point by point. For each I state **what I
verified before acting**, because three referee statements in this round
turned out to be wrong about this manuscript and one manuscript statement
turned out to be wrong about itself.

---

## 1. Things I checked and found the referee was right about

### A/B: the "two orders of magnitude" arithmetic error — CONFIRMED, and it occurred TWICE

Verified: $1/\mathtt{RankFloor} = 1/513 = 1.949\times10^{-3}$; the
Bonferroni scale is $1.2\times10^{-4}$; the ratio is **16.2**, not 100.

Referee A cited line 533 (the `tab:nomenclature` caption). The same claim
also stood in the body of §4.1 — "a survey-wide Bonferroni scale over 431
windows is $1.2\times10^{-4}$, two orders of magnitude smaller". **Both are
fixed.** The ratio is now the generated macro `\BonfRankRatio`, computed in
`v350_calc.py` by reading `\RankFloor` and `\BonferroniThresh` back out of
the macro files that the manuscript itself uses, so the two cannot drift
apart again. The rank floor is now also printed as a number,
`\RankFloorVal` $=1.95\times10^{-3}$, so a reader can do the division.

Checked and left alone: line 783's "two orders of magnitude" is about drift
rates, and is correct.

### A2: "archive-complete" is misleading — CONFIRMED

Verified from the macros: 102 of 448 public execution blocks searched, 346
unsearched. Changed to **"archive-target-complete but epoch-incomplete"**
throughout, in all seven places the phrase occurred, and stated in the
abstract with the 102/448 split beside it.

### A4: exchangeability "by construction" — CONFIRMED and softened

The claim now reads that the 513 positions are *approximately* exchangeable
under a *restricted* noise-only null, that the argument covers thermal noise
and the primary beam only, and that residual calibration or continuum
systematics can occur preferentially at the phase centre. The reason that
matters is stated: every searched star but Wolf 219 is the pointed science
target of at least one block.

### A9: CP−72 2713 wording — CONFIRMED

"Retired as a candidate" no longer appears unqualified anywhere. The
disposition now reads: the pinned criterion is met, we find no repeat and
therefore no evidence supporting a *persistent* technosignature, the
first-epoch event remains unexplained, it is statistically unexceptional at
the survey level, and two epochs do not exclude an intermittent emitter.

### A19 / A20: Conclusions — CUT TO FOUR STATEMENTS

*What was searched* / *What was found* / *The defensible sensitivity and
search domain* / *The implication for future ALMA archival SETI*. A20's
346 unsearched blocks are now the fourth statement in their own right, with
the note that the campaign has begun and five blocks are already searched.

### A12: β Pic and HD 48370 — ONE PARAGRAPH EACH

β Pic is two short paragraphs (the disposition, and what it costs the
statistic) plus `tab:flagged`; HD 48370 is one. The velocity-frame audit,
`tab:bpicaudit`, the flux-ratio and excitation argument, the stellar-flare
suppression argument and the Band 8 [C I] check all moved to
Appendix "Analysis provenance and robustness checks".

### A18: Hanning-corrected ranges beside the nominal ones

New macros `\EirpHanMin{A,B}` and `\EirpHanMax{A,B}`, emitted by
`v342_calc.py` beside the existing `\EirpMin`/`\EirpMax` so they cannot go
stale. Both ranges now appear in the abstract and in the Conclusions:
nominal $2.3\times10^{13}$–$6.8\times10^{16}$ W (Class A) and
$1.6\times10^{13}$–$2.8\times10^{17}$ W (Class B), against
$4.7\times10^{13}$–$1.8\times10^{17}$ W and
$3.2\times10^{13}$–$7.4\times10^{17}$ W corrected.

### A5: the stellar-position noise limitation, promoted

It is now one of the two limitations named in the abstract, and it is named
again in the Conclusions' sensitivity statement. We did **not** re-extract
controls for the four flagged windows; referee A offered that as the
alternative and accepted the promotion instead.

### A13: the "plain terms" paragraph

"Enormous by human standards" is gone. The paragraph now ends on the
conditionality (frequencies, epochs, morphology class, duty cycle), which
is the stronger point the referee identified.

---

## 2. Things I checked and found the referee was wrong about

### B7: the two citation inconsistencies — NEITHER EXISTS IN v3.49 OR v3.50

I ran a full citation-key consistency check over the manuscript (39
`\bibitem`s, 38 cited keys):

* **cited but undefined: none**
* **defined but uncited: none** (`Drake1974` appears inside a
  `\citep[][...]{Drake1974,EarthDetectingEarth2025}`, which a naive regex
  misses)
* **label-year vs entry-year mismatches: none**
* **surname mismatches: none**

Specifically:

* `BRaTs2026` is `\bibitem[Garrett et al.(2026)]{BRaTs2026} Garrett M. A.,
  et al., 2026, MNRAS, accepted (arXiv:2605.10212)`. Label year and entry
  year both read 2026. The referee's "Garrett M. A., et al., 2023, PASA, 40,
  e038" is not in this bibliography at all; **PASA 40, e038 is the
  `Morrison et al. (2023)` entry**, which is almost certainly the source of
  the confusion.
* `GLOBULAR2025` is `\bibitem[Jacobson-Bell et al.(2025)]{GLOBULAR2025}
  Jacobson-Bell K., et al., 2025, AJ, 169, 233`. The string "Jacobsen"
  does not occur anywhere in the manuscript.

**Nothing was "corrected".** The check itself is new and is worth keeping.

### A16, option (b): the six coarse-noise windows

The referee offered re-extraction or a metadata demonstration. I took (b),
as instructed, and I did not have to weaken anything to do it: the
mechanism is now stated, not just the signature. All six are the
channel-averaged auxiliary companion window of a frequency-division science
baseband, each with a normally behaved finer-channelised sibling covering
the same frequencies in the same block; they carry a constant WEIGHT column
and so never received the science baseband's calibration; and the deflation
is **common mode in the data and in the weights alike**. That is why the
signal-to-noise ratio the search actually uses is untouched, why the defect
can only misstate a threshold and never manufacture a flag, and why
excluding the six costs no frequency coverage.

---

## 3. A manuscript error found while checking a referee's minor point

Referee B asked for the EIRP range the four withheld ε Eri Band 6 windows
would have covered. Computing it from the frozen export exposed a false
statement in v3.49: it said those windows "enter no number here but are
**released, flagged, in the catalogue**". **They are not in the released
catalogue.** `v342_calc.py` line 91 and `survey_stats.py` line 42 both drop
them, and `per_target_results_v3.50.csv` contains no `eps Eri` row (431
rows, 88 stars, checked by name).

Both halves are now fixed. The text says plainly that the four windows are
withheld and are not in the released catalogue, and it gives what the
referee asked for: they would have covered
$4.1\times10^{13}$–$2.4\times10^{14}$ W at 3.22 pc, the lower end being
among the deepest thresholds in the survey, which is exactly why we decline
to quote them on a beam model we cannot defend (correction
2.9–3.4×).

---

## 4. The held-out validation (B4), from data we already had

No new compute was started. The epoch-extension programme has searched, with
the **frozen** pipeline and after the statistic and mask were fixed, five
execution blocks that played no part in designing either: four β Pictoris
blocks (`A002_Xf5d76d_Xcc5`, `_Xe19`, `_Xeb8`, `A002_X7116f1_X1785`) and the
CP−72 2713 second block (`A002_Xff0235_X502d`). That is **20 windows**,
frozen here as `heldout_v350.json` and reduced by `v350_calc.py`.

**Result, reported honestly:**

* **4 of the 20** carry β Pictoris CO at the stellar position and rank
  first or nearly first, $T_\star = 10.0$ to $30.8$. That is the
  astrophysical positive control, not a noise draw.
* **In the other 16** the star's add-one rank is consistent with $U(0,1)$:
  median 0.62, range 0.04–0.93, Kolmogorov–Smirnov $D=0.17$ ($p=0.65$),
  2 below 0.05 against 0.8 expected, and **zero stage-1 spatial outliers**.
* Over all 20, $D=0.27$ ($p=0.09$); the departure is the signal.

**And the honest limits, stated in the paper:** 2 stars, 3 bands, windows
within one block share a calibration and are not independent, and 16
windows cannot resolve a rank departure smaller than about a tenth. What it
does establish is that the frozen pipeline, applied to data that played no
part in building it, generates no spurious stage-1 flag and recovers the
one real signal present. The existing audit table is, as the referee says,
by construction the set that motivated the redesign; this is not.

Verification note: the KS figures are computed by `v350_calc.py` with
`scipy.stats.kstest`. My own asymptotic implementation returned $p=0.67$
against the exact 0.65, so the generator requires scipy and says so.

---

## 5. The restructure (A1, A3, A15, B2)

**New appendix, "Analysis provenance and robustness checks"**
(`app:provenance`), which keeps the old labels `app:exclusions` and
`app:aumic` so every existing cross-reference still resolves and none
changes meaning. It absorbs, in this order: the chronology of the statistic
revision with its commit hashes; the AU Mic three tests in full (the
separate AU Mic appendix is folded in and deleted, one heading saved); the
fully symmetric region-max check; the β Pictoris frame audit with
`tab:bpicaudit`; the HD 48370 Band 8 [C I] check; the line-mask repair
history; and the entries excluded from the released catalogue.

**What stays in the main text** is exactly A1's list: the original statistic
was asymmetric, the final analysis uses the symmetric single-position
statistic, all 431 windows were reassessed under it, and `tab:bothstats`
shows that no result depends on the superseded version. `tab:bothstats` is
on the must-not-cut list and stays in the main text.

**New Figure 2** (`fig:funnel`), one combined two-panel `figure*`: the
selection funnel 17 566 → 168 → ~115 → 88 (81 systems) on the left, and the
decision flow 431 windows → 20 crossings → 4 stage-1 flags → 0 candidates on
the right, with the three gates (spatial screen, excluded frequency regions,
vetting/recurrence/local null) labelled between the boxes. Every number is
read from the generated macro files by `make_fig_funnel.py`, so the figure
cannot drift from the text. The caption says in as many words that the
512-control comparison is a candidate-generation screen.

---

## 6. Terminology, applied throughout

* "drift-resolved carrier search" / "unresolved spectral-excess search"
  (A7), with the A/B split (118 / 313) given wherever a combined number
  appears, including the abstract, the Conclusions and Figure 2.
* The molecular mask is a **predefined excluded frequency/velocity region**,
  never a veto (A10), and that is said at the point of first use.
* The ±20/30/50/100 km s⁻¹ insensitivity test now sits **next to the first
  description of the mask** in §4 (A11), not several sections later.
* "nominal 5σ trigger power" / "trigger threshold" throughout (A17);
  "detection" is reserved for the outcome of the whole chain.
* The 512-control design is called a candidate-generation screen and never
  a significance test (A3), in §4.1 and in the Figure 2 caption.

## 7. Completeness (A6, B3)

Reduced, as instructed, not re-measured. Appendix B now says in bold that
the curve is **a demonstration that the pipeline recovers a carrier in a
representative configuration, not a survey completeness function**, and the
new **Table 6 (`tab:configdist`)** gives, per axis, how far the 118
drift-resolved windows sit from the one configuration on which recovery was
measured (AU Mic, Band 6, 488 kHz, 1506 s on source, 49 drift trials, star
on the phase centre):

| axis | calibration value | windows matching |
|---|---|---|
| band | 6 | 63 of 118 |
| channel width | 488 kHz | 101 of 118 |
| on-source time | 1506 s | 98 of 118 |
| drift trials | 49 | 63 of 118 |
| offset from phase centre | 0 | 106 of 118 |

with the summary that 58 of 118 (49 per cent) differ on at most one axis.
Tolerance is a factor of two, or 0.2 θ_PB for the offset. Beam offset is
inverted from the catalogue's own primary-beam factor through the
pipeline's Gaussian, so the table needs no input the release does not ship.
Antenna count is not in the frozen products and is not an axis; the table
says so rather than pretending otherwise.

## 8. Sample bias (A14, B5)

New Discussion subsection **6.3, "What this sample can and cannot speak
for"**, which states the disc-programme dominance (79 of 88 stars under
*Disks and planet formation*, 73 carrying *Debris disks*, 67 of 81
systems), the M-dwarf deficit (41 against 69 per cent), and the window
concentration, and then says in bold that **the null result carries very
little weight for the habitable-zone or Sun-like-star question**. The §3
composition paragraph now points here instead of half-stating the same
thing.

## 9. Smaller items

* **B8 polarisation**: one sentence in §4 making the free-discriminant,
  not-free-sensitivity point, including that an artificial coherent carrier
  is more likely to be strongly polarised than the line and dust emission
  that fills this archive.
* **B, Table 11**: a bold warning at the head of Appendix J that the
  conditional fraction must not be quoted outside its conditioning.
* **B, Barnard's Star and Wolf 359**: the priority claim is now supported
  by an explicit statement that a literature and ADS search returns no
  prior mm/submm limit for either.
* **A8, Figure 1**: "native-channel total-power threshold, EIRP (W): not
  sensitivity to a 1 Hz carrier" is now the **y-axis label**, not only the
  caption. (A trap: the first two attempts were silently clipped by the
  figure's own bbox because the label lines were too long. Verified by
  extracting the text back out of the figure PDF, not by eye.)
* **B, CP−72 pre-registration**: the Data Availability statement now says
  that the commit hash and timestamp are part of the tagged repository
  snapshot, that this makes the pre-registration publicly verifiable, and
  that the Zenodo deposit covers it.
* **B, greyscale and colour-vision**: checked. Figure 1's six series are
  already distinguished by marker shape (open triangle, filled circle,
  star, diamond, square, filled triangle) and line style as well as by
  colour, so it survives both. No change needed.

---

## 10. Declined, with reasons

* **B, "the five-criterion usable-coverage definition should be an
  enumerated list".** Declined on the page budget. It is already an
  explicit five-part enumeration, (i) to (v), in running text; promoting it
  to a display list costs roughly 25 pt of vertical space, and the 29-page
  constraint left 0.02 pages of slack at the end of this round. If the
  editor will accept 30 pages this is the first thing to change.
* **A5's preferred option, "re-extract enough controls for the four flagged
  windows".** Declined: it needs products beneath the frozen release and
  would mean re-running the extraction. Referee A explicitly offered
  promotion to a principal limitation as the acceptable alternative, and
  that is what was done.
* **A6's and B3's preferred option, a second injection-recovery
  configuration.** Declined per the brief's ruling: the claim is reduced
  instead, and Table 6 makes the extrapolation inspectable.
* **B1's "cut the abstract to one or two standout numbers".** Partly
  declined. The abstract is down from 1895 to 1729 rendered characters and
  from 15 numerical claims to 9, but it gained the epoch-incompleteness
  figure (A2), the Hanning range (A18) and the stellar-position noise
  limitation (A5), all of which other referee points required to be there.
  It cannot be shorter without dropping one of those.

---

## 11. Prose density, measured (referee B1)

`prosecount.py` gained a new category G, which counts sentences carrying
three or more quantitative tokens, where a quantitative token is a bare
number in the source or a macro whose generated value begins with a digit.
Tabular bodies and the preamble are excluded; a table row is not a sentence.

Main text, v3.49 → v3.50:

| measure | v3.49 | v3.50 |
|---|---|---|
| sentences | 583 | 619 |
| **mean quantitative tokens per sentence** | **2.39** | **1.88** (−21 %) |
| **total quantitative tokens** | **1391** | **1162** (−16 %) |
| 95th percentile tokens in a sentence | 9 | 8 |
| sentences with ≥3 quantities | 198 | 169 |
| sentences with ≥4 quantities | 156 | 128 |
| colon-as-explainer | 81 | 77 |
| antithesis family | 23 | 22 |
| em-dashes | 0 | 0 |

**An honest caveat on the counts.** Splitting one sentence that carried 19
quantities into three that carry 6, 7 and 6 *reduces* density but can leave
the ≥3 count unchanged or higher. That happened here: one late splitting
pass moved the ≥3 count from 167 to 169 while lowering the mean. The mean
and the total are the meaningful numbers; the ≥3 and ≥4 counts are reported
because the previous rounds reported them.

The appendix counts rise (≥3: 70 → 78) because material moved into the
appendix by A1, not because anything got denser there.

---

## 12. What I measured about the page budget, for the next round

Worth recording, because it cost about forty minutes:

1. **Appendix prose cuts do not move the page count.** A 589-character cut
   to the appendix left the total at exactly 29.49 pages. The appendix
   region is float-quantised and the freed space is absorbed. Confirmed
   again at 230 characters. Main-text cuts do propagate, until the main
   region becomes float-packed too, after which they also stop.
2. **What actually closed the last page was float geometry, not prose.**
   Reducing the new Figure 2 from 2.05 to 1.78 inches and two appendix
   figures by about 12 per cent took the document from 30 pages to 29 in
   one step, having already absorbed roughly 9,000 characters of prose cuts
   with no page change at all.
3. **Moving a float between regions can help even when it saves nothing.**
   Moving `tab:configdist` from the appendix to §4.4 changed the content
   total by zero but filled 0.22 pages of main-region slack.
4. **A shorter abstract can create a new gate failure.** Cutting the
   abstract by 166 characters left `\enlargethispage{-\baselineskip}` on
   page 1 overshooting by 0.31 pt, which is an overfull vbox. Changed to
   `-2\baselineskip`.

## 13. A reproducibility defect found and fixed

The clean-regeneration test failed on first run. Cause: **matplotlib stamps
a CreationDate into every PDF it writes**, so the figure set was
reproducible in content but never in bytes, and previous rounds' claims of
byte-identical regeneration cannot have covered the figures.
`make_all.sh` now exports `SOURCE_DATE_EPOCH=1577836800`. Verified: two
successive `make_all.sh` runs, and one run after deleting every generated
file, all produce byte-identical macro files, table fragments and figure
PDFs, and leave the `.tex` unchanged.

---

## 14. Verification ledger

| checked | method | outcome |
|---|---|---|
| 1/513 vs 1.2e−4 | arithmetic, from the macro files | 16×, referee right, two occurrences |
| Garrett 2026 vs 2023 | full bibliography parse | referee wrong; PASA 40 e038 is Morrison 2023 |
| Jacobsen vs Jacobson-Bell | string search over the manuscript | referee wrong; "Jacobsen" does not occur |
| citation keys | 39 bibitems vs 38 cited | 0 undefined, 0 uncited, 0 year or surname mismatches |
| 102 of 448 blocks | `\NEB`, `\NProgenitorEB`, `\NUnsearchedEB` | confirmed |
| 79 of 88 disc programmes | `obscore_category_v348.json` via macros | confirmed |
| held-out rank uniformity | 20 windows, `heldout_v350.json`, scipy KS | 16 noise windows D=0.17 p=0.65, 0 stage-1 flags |
| Class A configuration distances | 431-row released catalogue, beam offset inverted from the PB factor | 58 of 118 within one axis |
| ε Eri withheld windows | `frozen_export_v3.31.json` | 4.1e13–2.4e14 W; **not in the released catalogue, contrary to the text** |
| clean regeneration | delete all generated files, `make_all.sh`, md5 | byte-identical after pinning SOURCE_DATE_EPOCH |
| arXiv set | `arxivset.sh` from an empty directory | 33 items, 29 pages, all gates 0 |

**Not pushed.**
