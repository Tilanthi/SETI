# Response to the third referee round, v3.44 -> v3.45

White & Dey, *An ALMA Archival Search for Spectral Technosignatures toward
Stars within 40 pc*. Reports: `v3.45_referee1_radio.md`,
`v3.45_referee2_radiostars.md`, `v3.45_referee3_general.md`.

**Everything below states what was verified, and how.** Where a referee's
number could not be reproduced, that is said plainly and the reproduced value
is used instead. Where a request was declined or only partly met, that is said
too. Nothing here is a statement of intent.

---

## 0. State of the manuscript

| gate | v3.44 | v3.45 |
|---|---:|---:|
| pages | 29 | **29** |
| main text | 20.78 | **20.45** |
| back matter | 0.96 | 1.07 |
| appendices (ceiling 7.00) | 6.94 | **6.93** |
| bibliography | 0.31 | 0.31 |
| content total | 29.00 | **28.76** |
| LaTeX errors | 0 | **0** |
| undefined references / citations | 0 | **0** |
| multiply-defined labels | 0 | **0** |
| overfull boxes | 0 | **0** |
| underfull boxes | 0 | **0** |
| Type 3 fonts | 0 | **0** |
| em-dashes in source | 0 | **0** |
| macros defined / unused | 553 / **3** | 535 / **0** |
| rendered abstract | 2,682 char | **1,835 char** |
| `arxivset.sh` from empty directory | 27 items, clean | **27 items, clean** |

Word-diff against the file received, one script both sides (`worddiff.py`):
main **1,905 deleted, 1,754 inserted, net -151 tokens**; appendices -6; whole
file -157. The main text lost 0.33 pp while absorbing every measurement the
three reports asked for.

---

## 1. Tier 1, the blocking items

### 1.1 The retirement now reaches the whole paper (R1 C1, R2 2(f), R3 2.1)

Confirmed against the shipped PDF and the shipped catalogue: v3.44 carried the
retirement in Sec. 5.3 alone. Every place named by the three reports is now
corrected, and each was checked in the built PDF rather than in the source:

| where | v3.45 |
|---|---|
| abstract | "...the fourth, toward CP-72 2713, has no astrophysical attribution and does not recur in a second, deeper archival block at the same tuning, so it is retired as a noise excursion." |
| Sec. 3 (archive scope) | one clause recording that a block counted there as unsearched has since been searched, as the test of Sec. 5.3, and that the counts and trials budget are unchanged by it |
| Sec. 5.3 opener | "the fourth, towards CP-72 2713, never acquired one and is retired on a second archival epoch, below" |
| Table 4 (`tab:searchspace`) | row relabelled "unattributed, retired on non-recurrence"; `\NUnattrib` stays 1, which is now explained rather than bare (R3's second option) |
| Table 5 (`tab:flagged`) | disposition cell "unattributed; no recurrence" |
| Sec. 5.3 record sentence (old l. 1838) | the subsection is restructured: the pinned criteria and the outcome are stated in the opening paragraph, and the test follows immediately |
| Sec. 6.3 future work | rewritten around what was done; the spent recurrence reason is gone |
| Conclusions | the retirement, with the matched-drift fluxes, in two sentences |
| `per_target_results_v3.45.csv` | `disposition` = "unattributed; retired on second-epoch non-recurrence" for the CP-72 2713 Band 7 row; verified by reading the regenerated file |

`\NUnattrib` is deliberately left at 1. The window was never identified, so
"unattributed" remains true; what changed is its disposition, and the row now
says so.

### 1.2 The abstract is inside arXiv's limit (R3 N1)

Verified. `abschars.py` extracts the typeset abstract from page 1 and collapses
line breaks: **2,682 characters before, 1,835 after**, against arXiv's 1,920.
Because an author may paste the abstract with LaTeX math rather than as plain
text, the same abstract was also measured with all macros expanded and math
left in LaTeX form: **1,908 characters**. Both forms are inside the limit.

Kept, as instructed: the sample and scale; the control construction; the null;
the four flags and their dispositions including the retirement; the 1/513 floor
against the Bonferroni scale; the trigger-level framing stated as such; the
Class A and Class B ranges; the 73 per cent no-drift-discrimination figure; the
Hanning and completeness-transfer caveats; the archive-complete-but-not-in-
epochs qualification; and the honesty clause, unaltered.

Dropped: the Hanning peak-channel fractions, the class medians and
Hanning-corrected medians, the native channel widths, two of the three
CP-72 2713 local-null p-values, and the numerical F/G/M over-representation
factors (the qualitative statement stays).

### 1.3 `make_all.sh` and `ARXIV_UPLOAD.md` (R3 N5, R1 C3, R2 N10)

**R3's finding reproduces exactly.** Deleting `survey_numbers_recurrence.tex`
and running `make_all.sh` left it absent, and the manuscript then failed with
`File 'survey_numbers_recurrence.tex' not found`. `recurrence_calc.py` is now
in the chain, after `v344_calc.py` and before `retire_macros.py`.

**The same test found a second, larger instance nobody had reported.** Deleting
*every* generated file and running `make_all.sh` leaves
`survey_numbers_round{5,6,7}.tex` absent as well: the rounds 5-7 generators
were never shipped with the release, so nothing in the folder can rebuild them.
They are now kept in `frozen_macros/` and restored by `make_all.sh` as its
first step, with a comment saying why. A full clean regeneration (delete all 13
macro files, 6 table fragments, 12 figure PDFs, 2 stats JSONs and the
catalogue; run `make_all.sh`; rebuild) now completes and gives 29 pages with
every gate at zero.

On the manifest, one correction to the reports. All three state that
`ARXIV_UPLOAD.md` says "26 items" and omits `survey_numbers_recurrence.tex`.
**The copy in this folder says "Total 1.9 MB, 27 items" and does list
`survey_numbers_recurrence.tex`**, so those two specifics did not reproduce and
are not claimed as fixed. What was stale, and is fixed: the title said v3.44;
the stated size 1.9 MB is 1.5 MB measured; and the last bullet of the v3.43
section read "the item count falls 27 -> 26", contradicting the header on the
same page. `arxivset.sh` was correct throughout; re-run into an empty
directory it resolves **27 items** and builds clean.

---

## 2. Tier 2, the recurrence test

Every number below was re-derived here before use, by `cp72_verify.py` run
read-only on the processing host against the retained
`*_srcspec.npz` and `*_search.npz` of both epochs. It reimplements the release
statistic (4 per cent adaptive edge trim, 65-channel frequency-median baseline,
inverse-variance weighted de-drifted stack) from the star's own retained raw
spectrum plus the retained per-channel noise map.

**Gate first.** At the published channel (35) and drift (-2055.5 Hz/s) the
reimplementation returns `T* = 5.808912411` against the published
`5.80891227722168`: relative error **2.3e-8**. R2's own reimplementation
reached 1.2 per cent because it rebuilt the noise map; using the retained
`sigma` closes that gap, which is why the values below differ from R2's in the
third digit and are quoted from this run.

### Item 4, the matched-frequency, matched-drift comparison

**Confirmed, with one correction.** At 344.269746 GHz and the first epoch's own
fitted drift, the second epoch measures **-1.0 +/- 1.8 mJy, -0.6 sigma**
(R2: -0.9 +/- 1.8, -0.5 sigma). The first epoch's value at the same cell is
**11.3 +/- 2.0 mJy**, not the 12.2 mJy R2 quotes: 12.2 is `T*` times the
window-median combined rms, whereas the fitted flux at that channel carries its
own error, 1.95 mJy. The track sweeps **7.70 MHz = 15.8 channels** over the
block, as R2 states.

On "excluded at ~7 sigma", the paper now makes a distinction the reports did
not. Treating the two epochs as measurements of one constant amplitude, they
are inconsistent at **4.6 sigma**. Conditioning on the first epoch's fitted
flux as exact, which flatters the test because that flux is the largest value
anywhere in the window and so is biased high, the second epoch alone excludes
it at **6.8 sigma**. Both are printed, with the reason the second is the
weaker inference. The drift-maximised comparison the v3.44 text rested on is
worth **1.6 sigma**, and the text now says so.

### Item 5, depth

**Confirmed.** `rms_combined` 1.9640 mJy against 2.0970, i.e. **6.3 per cent
lower** (at the feature channel specifically, 1.826 against 1.951 mJy, 6.4 per
cent). A persistent emitter at the first epoch's fitted flux would have
appeared at **T* = 6.21**, computed from the two channel-local errors rather
than from the window medians; R1 and R2 both reached 6.20 by the other route.
In the text.

### Item 6, the frequency axes

**Confirmed.** Channel 35 is 344.269746084 GHz in epoch 1 and 344.269658449 GHz
in epoch 2: **87.6 kHz, 0.18 of a channel**. Printed, and "matches exactly" is
gone. The drift grids differ (129 against 128 trials); the first epoch's fitted
rate falls **0.12 channel** from the nearest second-epoch node, and evaluating
at that node instead changes the result from -1.04 to -1.03 mJy, so the text
says the difference costs nothing.

### Item 7, like-for-like

**Confirmed, both statements.** Against the ten neighbouring channels of the
second epoch (mean 3.226, standard deviation 0.629) the star's 3.604 is
**+0.6 sigma**. The window maximum 4.698 ranks **188 of 513** against the same
control ensemble, add-one p = 0.366. The v3.44 sentence comparing 3.60 at one
channel with 4.62, the median of per-control window maxima, is gone.

### Item 8, `\CpRecCtrlMax`

**Confirmed and used.** 5.9330 against the 5.80891 that raised the flag. The
text now says that in the second epoch the control annulus alone throws an
excursion bigger than the one that raised the flag. The macro is no longer
orphaned.

### Item 9, the same night

**Confirmed from the retained per-integration timestamps.** Epoch 1 runs
2022-10-02 00:40:03 to 01:42:28 UT, epoch 2 02:42:49 to 03:44:45 UT; the gap is
**60.3 min**, start to start 2.05 h. The paper now states the date, both UT
starts and the separation, and gives both consequences: the test is strong
against a static instrumental artefact (a spur, a fixed-channel bandpass
residual or a birdie would be at its most reproducible an hour later in the
same configuration and tuning) and silent about intermittency on any longer
timescale. AU Mic's ten-week separation is named in the same paragraph so the
two cases cannot be read in the same terms.

### Item 10, what carries the retirement

Stated plainly in the closing paragraph of the subsection: the
matched-frequency, matched-drift null of the second epoch, with the local null
that never placed the feature near the Bonferroni scale and the survey's trials
budget behind it; and the note that non-recurrence quoted the usual way,
maximised over drift, would carry only 1.6 sigma on its own. R3's 1.6-2.2 sigma
range is the same quantity computed two ways from the published numbers; this
run reproduces 1.56 sigma for the symmetric version and prints 1.6.

### Item 11, the pinned criterion

**Confirmed that v3.43 pinned it and v3.44 deleted it.** Restored, in the
opening paragraph of the subsection: *promote* on independent confirmation,
*retire* on a clean second epoch or on identification with catalogued emission.
The closing paragraph says the pinned criterion is met, so the retirement is
visibly the execution of a pre-stated rule.

### Item 12, the zero-drift datum

**Confirmed, with a corrected value.** At zero drift the first-epoch statistic
at 344.269746 GHz is **2.02 sigma** (3.95 +/- 1.95 mJy); R2's reimplementation
gave 2.10. The three-way excitation enumeration is **replaced**, not extended:
the E_u values and the n(H2) requirement are gone, and one sentence now says
that a catalogued transition is stationary in the observed frame to well within
a channel over an hour, so none can produce the feature whatever its
excitation. The SO / 34SO2 / Lovas U-line entries and the admission that the
mask would have caught the feature had SO been in it are kept in full. The
implied acceleration (1.79 m/s^2) was computed and verified but is not printed;
it was the weakest of the three arguments and the subsection had to shrink.

---

## 3. Tier 3

**Item 13, unused macros.** `\CpRecEb` and `\CpRecGB` are deleted at source, in
`recurrence_calc.py`, rather than retired: they duplicated `\CpEbUnsearched`
and `\CpEbUnsearchedGB`, which is the double-definition trap closed in v3.42.
`\CpRecCtrlMax` is used. `\CpRecNChan` is also gone, replaced by `\CpNChan`,
which closes R3's N9 (the same quantity set as "3534" and "3 534" on one page).
`macrosweep.py`: **535 defined, 0 unused**.

**Item 14, the released `star_name` column.** Confirmed and repaired in the
generator (`v342_calc.py`), not by hand-editing the catalogue. The upstream
directory-name sanitisation had stripped the sign from **four** designations,
one more than the reports found: `LSR J18353259`, `PM J034331958`, `WD 0407179`
and `BD05  1668`. Each replacement was checked against the row's own catalogue
distance before being made: LSR J1835+3259 at 5.69 pc, PM J03433+1958 at
20.76 pc, WD 0407-179 at 34.11 pc, BD+05 1668 (Luyten's Star) at 3.79 pc. Runs
of whitespace are collapsed, so `HD  33793`, `Wolf  219` and `Wolf   28`
resolve too. **Not repaired, and disclosed instead**: the rows carrying a
trailing Gaia DR3 or source-table identifier and the SIMBAD `NAME` / `V star`
prefixes are left as the archive supplies them, because inventing a canonical
form for those is a judgement the release should not make silently. Data
Availability now says all of this.

**Item 15, proportionality.** The subsection's prose falls from **1,391 to
1,254 words** as measured by one script on both files, and that number
understates the change: roughly 250 words of new, referee-required measurement
went *in* (the matched-drift comparison, the depth, the axis registration, the
like-for-like ranks, the epoch times, the other three windows, the trials-budget
exclusion), so the disposition argument itself is down by about 390 words.
`tab:cp72props` is **deleted**, which R1 priced at 125.7 pt and R2 explicitly
released; the two-epoch comparison it would have carried is in the text and in
the figure. `fig:cp72ctrl` now carries both epochs at **zero cost** (R3 N8):
the same canvas, the two control ensembles overplotted, both control maxima and
both values of `T*`. The second epoch's 512 control statistics come from its
own retained `ctrl_max` array, copied into `localnull_code/ctrlmax_eb2.json`
with its provenance inside the file, and the generator asserts that its maximum
equals the value the text prints.

**Item 16, length. Taken as far as it would go, and it did not reach 19.8.**
Main text **20.78 -> 20.45**, appendices 6.93 inside the 7.00 ceiling, total
28.76 pp of content on 29 pages. The measured ledger:

| change | measured |
|---|---|
| CP-72 subsection prose | -137 words net, about -390 words of disposition argument |
| `tab:cp72props` deleted | -125.7 pt |
| Sec. 5.3 ledger: (v) merged into (vi), (ii) and (iii) under one heading, the duplicated expected-flag restatement dropped | -60 words |
| Sec. 6.3 item 1 rewritten around what was done | -25 words |
| abstract | -847 characters |
| antithesis, colon and numeral-opener conversions across the main text | about -120 words |
| widow-killing, 13 paragraphs shortened by 1-4 words each | short last lines under 22 per cent of the measure: 31 -> 24 |
| Tier 2 additions | about +250 words |

R3's plan reaches 19.8 by costing the consistency edits at +120 words and the
new measurements at +60. Referees 1 and 2 between them asked for about twelve
lines of new measurement in the same subsection, which is roughly +250 words,
and R3's figure does not include them. R1's own estimate, made with those
additions in view, was 20.55 and the note "I cannot find the remaining ~384 pt
without deleting evidence a referee asked for"; R2's was 20.5, or 20.35 with
Table 6 released, which has now been done. **20.45 is where the honest cuts
end.** The two remaining blocks of the right size are `fig:cp72ctrl`
(227.1 pt = 0.33 pp), which the standing instruction forbids cutting, and
`tab:algorithm` (155.6 pt = 0.22 pp), the twelve-step reproduction summary that
no referee proposed removing and that the text points to as the way to
reimplement the statistic without the appendices. Both are the authors' call
and neither was taken here.

---

## 4. Tier 4, the prose pass

Counted by one script (`prosecount.py`) on the file received and on the file
produced, so the two columns are comparable with each other. The absolute
numbers differ from R3's because the scripts differ; the direction and the
proportions do not.

| construction | v3.44 main | v3.45 main | v3.44 app | v3.45 app |
|---|---:|---:|---:|---:|
| ", not" | 47 | **25** | 12 | 12 |
| "and not" | 12 | **5** | 1 | 1 |
| "rather than" | 14 | **11** | 3 | 3 |
| **antithesis total** | **73** | **41** | 16 | 16 |
| colon-as-explainer | 144 | **109** | 36 | 35 |
| paragraph-initial italic/bold label | 50 | **41** | 18 | 18 |
| numeral list-opener | 13 | **2** | 3 | 3 |
| em-dash | 0 | **0** | 0 | 0 |
| negative-definition sentence | 2 | **1** | 0 | 0 |

The antithesis family falls **44 per cent in the main text** and, critically,
**"rather than" falls too** (14 -> 11). R3's finding was that two rounds had
*migrated* the construction rather than retiring it; the test of whether that
happened again is whether the replacement phrase rose, and it did not. Where
the negation survives it is because a reader would otherwise make the mistake:
"such emitters are unconstrained, not excluded"; "the non-detection concerns
the epochs searched, not permanent activity"; "$P_{\rm trig}$ is a total-power
threshold set by ALMA's native channelisation, not a Hz-resolution
sensitivity"; the honesty clause itself.

Colon-explainers were reduced in the abstract, Sec. 1 and the Conclusions, as
R3 directed, and left alone in the methods where a colon before an enumeration
is doing honest work.

Five of the eight decorative italic lead-ins R3 named are gone, replaced by
topic sentences that carry the same content: *What the geometry costs.*, *Why
the statistic is symmetric.*, *The campaign measures completeness...*,
*Drift-ceiling caveat.*, *The mask as executed had four defects...*. The three
ancillary-results labels are kept, because each names a distinct released
product and the paragraph does not repeat the label.

Numeral list-openers fall 13 -> 2 in the main text; each conversion also
removed a colon.

**Aphoristic closers: four of the six are gone.** "We state the coincidence
rather than dismiss it" (deleted with the paragraph it closed), "...the most
honest one-number summary of this feature available", "...which is the point,
but", and "...remains the binding test for candidacy" (rewritten as
"candidacy still turns on the first-stage star-versus-control comparison").
**Two are kept**: "and we do not claim they do", which R3 asked to keep, and
"we do not claim tests we have not run", which R1 protects as the first
statement of a limitation; the latter is no longer a paragraph closer.

**Em-dashes stay at zero in the source.** The PDF shows **7**, one per figure,
all of them the `Fig. N.—` caption separator emitted by `openjournal.cls`.
They were not touched. The 11 spaced ` -- ` runs in the source are inside
LaTeX comments and CRediT role labels, as before.

No number, claim or caveat was changed by the prose pass, and no new hedging
was introduced while old hedging came out.

---

## 5. Other referee points taken

- **R1 minor 1 / R2 N7 / R3 N5.** The 49.5 against 49.3 GB download-budget
  comparison moves from Sec. 5.3, where it was evidence, to Data Availability,
  where it is provenance. Data Availability now also names the second-epoch
  products explicitly as item (x), with `cp72_recurrence_v345.json` and the
  script that derives it.
- **R1 C6 / R2 N8.** The text says the second block's four windows are a
  targeted follow-up and enter neither the 431-window trials budget nor the
  Bonferroni denominator, and reports the other three windows' peaks
  (2.65, 2.98, 4.47, zero crossings).
- **R2 N5 residual.** Data Availability item (vii) now names the serendipitous
  molecular-line catalogue file, `line_catalogue.json`, written by the
  pipeline's own continuum line-exclusion step. The file was located on the
  processing host and its contents inspected before it was named; no filename
  was invented.
- **A defect found here, not in the reports.** Component (iv) of the
  false-alarm ledger referred to "the Bonferroni reference of (v)", and
  component (v) contained no Bonferroni statement. The cross-reference is
  removed. Merging (v) into (vi) also reconciles the ledger with its own
  opening sentence, which says the false-alarm probability has *five*
  components while six were labelled.

## 6. Not done, and why

- **Main text is 20.45, not 20.0.** Section 3, item 16 above, with the ledger
  and the two remaining candidates named.
- **R1 C4** asked for four facts to be added to the shipped recurrence JSON.
  The shipped file is now `cp72_recurrence_v345.json`, written by
  `cp72_verify.py`, and carries all four (rms, S_min, the two UTC epoch ranges,
  the drift-trial count and `freqs[35]`) along with the matched-drift fluxes,
  the neighbour distribution, the rank of the window maximum and the other
  three windows' results. Releasing the second-epoch `*_result.json` itself is
  covered by the new Data Availability item (x).
- **R1 C5's `simbad_id` column** is not added. The four sign repairs and the
  whitespace fix make three of the named objects resolvable; a full identifier
  column would have to be built from a SIMBAD query that is not part of the
  frozen release, and inventing one row at a time is worse than disclosing the
  residue, which Data Availability now does.
- **R1 minor 3** (the drift grid does not contain exactly zero) is noted and no
  sentence in the paper claims that it does; the zero-drift statistic quoted in
  Sec. 5.3 is evaluated at zero drift directly, which over the block differs
  from the nearest node by less than a quarter channel.
- **R2 M10** (three beta Pic specifics), **R2 minors 4-7**, **R1 m3** and
  **R3 minor 10** are carried forward unchanged; each was declined in an
  earlier round with a reason, and this round's budget went to the blocking
  items and the length.
- **Author items** are untouched and still flagged in the source: the Data
  Availability TODO naming tag `submitted-v3.32`, the VBRL affiliation
  wording, the White (2026) arXiv identifier, the repository tag and the
  Zenodo DOI.
