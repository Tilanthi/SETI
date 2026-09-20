# BUILD NOTES — v3.80: the completed archival sweep

Built 2026-09-19 from `frozen_export_v3.80.json` (snapshot 2026-09-19T20:41Z).

## What changed, in one line

The catalogue grew from **443 windows / 104 execution blocks / 88 stars / 81
systems** to **1956 windows / 479 blocks / 94 stars / 87 systems**, and the
paper is rebuilt on all of it.

| quantity | v3.72 | v3.80 |
|---|---|---|
| windows | 443 | **1956** |
| execution blocks | 104 | **479** |
| stars / systems | 88 / 81 | **94 / 87** |
| Class A / Class B windows | 126 / 317 | **459 / 1497** |
| systems with drift-resolving coverage | 58 | **65** |
| union bandwidth | 113.9 GHz | **125.1 GHz** |
| stage-1 spatial outliers | 4 | **13** (7 star–band pairs, 6 systems) |
| — line-attributed | 3 | **9** (8 of them β Pic) |
| — unattributed | 1 | **4**, against **3.8 expected**, *p* = 0.53 |
| systems at Arecibo-class effective EIRP | 0 | **0** |
| systems at twice it | 1 | **2** |
| occurrence limit at 1e16 W | 6.4 % | **5.9 %** |
| duty-cycle variant | 11.2 % | **7.6 %** |

## The result the enlarged sample makes possible

On 443 windows the survey had one unattributed stage-1 outlier and could only
say it was consistent with chance. On 1956 windows it has **four against 3.8
expected at the ensemble's own rank floor of 1/513** (Poisson *p* = 0.53).
Quadrupling the catalogue did not accumulate unexplained events: the
unexplained population scales with the number of windows searched, which is
what a false-alarm population must do and what a real one need not.

Two further structural facts fall out:

- **Every stage-1 outlier is fine-channel.** 13 of 459 Class A windows against
  0.89 expected; **0 of 1497** Class B against 2.92 expected. A
  15.6–31.25 MHz channel dilutes a narrow line, so the class that can resolve
  one is the class that finds it — and a genuine narrowband emitter would
  appear in Class A first.
- **β Pictoris is recovered eight times independently**, in five Band 3 and
  three Band 6 windows from six execution blocks, all within a few km/s of
  systemic on CO, by a pipeline that was never told the disc is there.

## A new external null

195 windows in 46 blocks toward stars at 40–50 pc were queued by a
beam-matching step that did not check distance. They are outside the sample
and excluded from every number in the paper, but they went through the
identical frozen pipeline and entered no tuning decision, which makes them an
external null in the strict sense: stellar add-one ranks median 0.502,
KS *p* = 0.96, and **0 stage-1 outliers against 0.4 expected**.

## Engineering: the literals are gone

Every generator used to carry the catalogue's size as a literal
(`assert len(good) == 431`). Those literals were this paper's most persistent
source of error — a later round enlarges the catalogue, one generator is
repointed and another is not, and two mutually inconsistent totals get printed
with an assertion passing in between. `survey_stats.py` now writes
**`catalogue_constants.json`** once and every generator asserts against it.
The check survives; the literal does not.

Three generators (`round8`, `round9`, `round10`) were still reading
`frozen_export_v3.31.json`, a 431-window snapshot three catalogues out of
date, and printing per-band counts, η_drift and a 93.1 GHz union beside a
headline computed from the current export. Repointed.

Metadata re-harvested for the full catalogue: `archive_meta_v380.json` (482
blocks, 152 member OUS, 656 progenitors) and `obscore_category_v380.json`.
obscore's `asdm_uid` is **not** a complete per-EB index — 130–132 blocks
resolve that way and the rest through their member OUS, which carries the same
spectral setup and proposal category. The same fact invalidated an earlier
diagnostic of mine: 262 of 460 campaign blocks are absent from an
`asdm_uid IN (...)` query and 247 of those have been calibrated and searched.

The Splatalogue line harvest was re-run over the new islands: 45 → **49
islands**, 4958 → **5406 transitions**.

## Gates

- 30 pages; 0 errors, 0 undefined references, 0 multiply-defined, 0 overfull,
  13 underfull (the narrow two-column measure)
- 0 Type 3 fonts
- abstract **1895 source / 1906 rendered** characters (arXiv limit 1920)
- 800 macros, **0 unused**
- clean regeneration **56/56 byte-identical**, figures included
- arXiv set **51 items**, 0 missing files
- em-dashes 0

## What is deliberately not claimed

- The velocity-frame chain is evaluated only for the four blocks whose
  pointing and mid-time were frozen in v3.42. obscore does not index the nine
  new blocks individually and the measurement sets have been reclaimed, so
  their offsets are reported from the catalogue's own columns instead of
  being invented.
- The local-scramble validation and the R_σ residual-scale test cover the four
  released windows only; the nine added windows have not had those diagnostics
  applied. Stated in the text as a limitation.
- 30 pages rather than 29. The page grew by the outlier taxonomy, the external
  null and the fine/coarse split, all of which are evidence.
