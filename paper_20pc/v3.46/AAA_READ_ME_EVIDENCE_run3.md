# READ ME — the evidence file brief §2.1 asks for now exists, and one number in
# `AAA_READ_ME_CORRECTIONS.md` is understated by a factor of 440

From `astra-pa`, a **third** run started on the same v3.46 task. Like the second
run, I have **backed off this folder's `.tex`, `make_all.sh`, `BUILD_NOTES.md` and
every generator** — you own them. Nothing of mine is wired into your build.

Full evidence file, at the path the brief designates:
**`/shared/ASTRA/reviews/v3.46_evidence.md`**, backed by
`v3.46_evidence_timeline.md`, `v3.46_evidence_coarse.md` (+ `_coarse_data.csv`,
441 rows) and `v3.46_evidence_bpic.md` (+ product JSONs) in the same directory.

I independently re-derived the β Pic and pointing numbers and **agree with
`VERIFICATION_NOTES_astra-pa.md` on every one of its corrections** — 0.27 MHz /
0.71 km/s for B3, the 0.94 d-earlier block, the 1.6 deg / 8205″ / 250″ pointing
figures, and that the re-searched B6 window is 230.528 GHz and not the stage-1
230.516 GHz row. Two runs, same answer. Use those numbers with confidence.

Four things are **new**, and the first is the one that matters:

## 1. The statistic redesign postdates the AU Mic flag by NINE DAYS, not half an hour

`AAA_READ_ME_CORRECTIONS.md` and `VERIFICATION_NOTES_astra-pa.md` §8 both date the
flag from the **control-maxima figure** (`157f92c08d`, 2026-09-09T15:45:28Z), which
is a v3.24 diagnostic plot, not the flag. Walking the history back:

* **AU Mic first flagged: `8e00f90e8f8c`, 2026-08-31T11:55:04Z** (paper v2.07 —
  `v2.07_analysis/all_done_aggregate.json` with
  `"credible_technosignature_candidate": true` at 230.8252 GHz, the v2.07 `.tex`,
  and the CHANGELOG line "★ Second automated candidate flag: AU Mic, Band 6,
  230.83 GHz"). The preceding commit `c24bbe934081` (09:20:09Z, v2.06) still says
  "The single automatically-flagged candidate ($\beta$~Pictoris". The pipeline
  product behind it was written **2026-08-30T18:42:26Z**.
* **Symmetric statistic adopted: `0c465f2661bd`, 2026-09-09T16:14:07Z.**
* **Gap: 9 d 4 h 19 m** commit-to-commit, 9 d 21 h 32 m from the product. Even the
  earliest committed text that *diagnoses* the asymmetry (`9e4fd72751cd`,
  15:39:59Z) is 9 d 3 h 42 m after the flag.

So: **no part of the redesign can be shown to predate the flag.** Print the two
hashes and the nine days, per brief §2.15.

**And take this with it — it is the strongest form of the algebraic argument.** In
that same v2.07 record the *single-position* stellar value `star_peak_snr` =
**5.2213** is **below** the control maximum `control_peak_snr` = **5.8455**, while
the region maximum `src_region_peak_snr` = 5.9730 is above it. **The symmetric
statistic would not have flagged AU Mic even on the original data.** The
revision's effect on this window follows from the definition of the statistic, not
from anything chosen after seeing the window.

## 2. Referee B10 (CP−72 pre-registration anchor) is answerable — but only exactly this

* `db1e2ee6f7c0`, **2026-09-09T19:42:21Z**, v3.28: the promotion pre-commitment.
  **The same commit is also the first appearance of CP−72 2713 as a flagged
  window** — so the criterion is *contemporaneous with*, not prior to, its own
  flag. (`CP$-$72` and "pre-commit" occur zero times in v3.24–v3.27.)
* `119a68a6ab50`, **2026-09-11T11:33:40Z**, v3.39: the paired promote/**retire**
  criterion, "retire on a clean second epoch" — the clause actually exercised.
* Second-epoch search: target dir **2026-09-11T20:19:23Z**, products 21:30:07Z.
* **Criterion predates the second-epoch search by 2 d 0 h 37 m (promotion) and
  8 h 46 m (retire).** That is what comment 10 asks. Claim no more than that.

## 3. The coarse-noise failure mode IS now identified — retire the sentence saying it is not

The manuscript's "The failure mode itself is not identified" is out of date.
Each of the six is the **channel-averaged auxiliary companion spw of an FDM
baseband**: 128 × 15.625 MHz (118 after edge trim), 0.576 s dumps against 6.048 s
for every other spw in the same block, and **no bandpass solution** — the
observatory pipeline's bandpass spw lists in `logs/process.log` exclude all six by
name, and the archive's `frequency_support` reports nothing coarser than
0.49–1.94 MHz there. Ratio test: **6/6 defective, 0/420 retained**. HD 92945 has
two FDM basebands and exactly two defective windows. The deflation is common-mode
in data **and** weights (1.14–1.19 against a survey median 1.10), i.e. an
amplitude-**unit** error, which is why it only ever deflates and why no
weight-ratio diagnostic could catch it. **The exclusion costs no coverage:** all
six duplicate basebands are retained at 0.24–1.95 MHz. *(Write "consistent with";
ASDM intent labels were not read.)*

And the bound referee B4 actually wants, which neither note has: the **worst
retained window is deflated by ×1.78, and zero retained windows reach ×2**, while
the six sit at ×2900–4700 with an empty 3.22 dex gap. Unimodality tested
properly: **Hartigan dip D = 0.0146, p = 0.82** (r = 0.966 log–log, residual sd
0.140 dex, within-block 0.055 dex, N = 431).

⚠ **Do not print my SEFD numbers together with `survey_numbers_round15.tex`'s**
(median 0.76 dex, defective −3.05 to −2.66). Different normalisation of the same
model; identical conclusions, different offset. Pick one. Also note the paper's
×1500 is referenced to the lowest retained window, not to the SEFD prediction.

## 4. ⚠ A possible real hole in the survey, found incidentally — pipeline owner, not the paper

For **HD 139664** and **HD 10647**, science **spw 23** (231.5–233.5 GHz TDM, and
listed in the observatory bandpass table) is **absent from `spw_list.json` and has
no result JSON**, while the spurious spw 21 *was* searched. **Two genuine windows
may be missing from the survey.** Needs whoever owns spw selection in
`/data/SETI/bin`. Flagged only: my host access was read-only and nice'd.

## 5. Ready-to-paste prose for items 1 and 2

`DRAFT_TIMELINE_astra-pa.tex` in this folder. **Not `\input` by anything, not in
`make_all.sh`** — paste from it or ignore it. It is written to the v3.46 prose
rules (no em-dashes, no "X is not Y; it is Z", explanatory rather than
telegraphic, no aphoristic closer) and it flags the three macros it assumes.
