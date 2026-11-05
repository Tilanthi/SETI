# BUILD NOTES — v3.81: the pre-registered hold-out, applied

Built 2026-09-20 from the final export (snapshot 2026-09-20T06:36Z), after the
archival sweep closed at **460/460 worklist items terminal**.

## What this round does

v3.80 reported the completed sweep. This round splits it on a rule that was
**fixed before the data existed** and reports the headline on one half and
every empirical calibration on the other.

`holdout_rule_v371.py`, committed **2026-09-14T07:10:24Z** as `c75069040eab`:

    held out  iff  sha256(canonical execution-block UID)[:8] mod 5 == 0

with two guards depending only on identifiers and the already-published block
list — previously released blocks stay in the survey, and no system may lose
every block.

| | v3.80 | **v3.81** |
|---|---|---|
| blocks processed | 479 | **484** |
| — headline survey | 479 | **404** |
| — **reserved hold-out** | 0 | **77 (15.9 %)** |
| headline windows | 1956 | **1655** |
| headline stars / systems | 94 / 87 | **94 / 87** (unchanged) |
| Class A / B | 459 / 1497 | **403 / 1252** |
| stage-1 outliers | 13 | **13** (all in survey) |
| — unattributed vs expected | 4 vs 3.8, *p* = 0.53 | **4 vs 3.2, *p* = 0.40** |

**The reservation costs no star and no system.** That is what guard two is
for, and it is asserted in `apply_holdout_v381.py` rather than hoped for.

## The point: every calibration is now out of sample

Measured on the 77 reserved blocks and nothing else (`holdout_calib_v381.py`):

| quantity | out-of-sample value |
|---|---|
| median stellar add-one rank | **0.405** (block-clustered 95 % 0.341–0.458) |
| KS against U(0,1) | *D* = 0.109, *p* = 0.0011 over 315 windows |
| false-alarm tail factor | **1.2** (block-clustered 95 % 0.6–1.9, 5040 trials) |
| stage-1 outliers | **0** against 0.61 expected |
| radial profile, inner→outer | +0.12, +0.10, +0.12, +0.16 |

The rank displacement — the single most consequential empirical claim in the
paper, and the one referee 1 objected was in-sample — **is reproduced on data
the design never saw**, at very nearly the in-sample value (0.405 against
0.419). The tail factor is consistent with the in-sample 1.5.

**One honest negative.** The steep inner-edge excess seen in sample is *not*
reproduced: the out-of-sample profile is flat to mildly rising outward
(mean per-window slope +0.03 ± 0.01). The text now presents the radial
correction as one demonstrated mechanism for the displacement rather than the
whole of it. A hold-out that only ever confirms is not a hold-out.

## Occurrence guard re-anchored, and the direction is the check

Reserving 77 blocks removes coverage, so the bandwidth-weighted mean
completeness per system falls and the limit **loosens**: 5.86 → 5.84 per cent
at 10¹⁶ W, duty-cycle variant 7.61 → 7.75. Holding data back cannot make a
survey more complete; had the guard moved the other way, the split would be
wrong.

## Also in this round

- `survey_stats_systems.py`: the system-grouping rule extracted into one
  module, so the hold-out's second guard groups systems by exactly the rule
  the headline counts use. Two definitions of "system" would make the guard
  protect something the paper does not report.
- Metadata topped up for the last blocks; Splatalogue harvest re-run over the
  survey islands (46 islands, 5114 transitions).
- The out-of-sample >40 pc set grew to 198 windows in 46 blocks, still with
  0 stage-1 outliers.

## Gates

30 pages · 0 errors / 0 undefined / 0 multiply-defined / 0 overfull / 0 Type 3
· 13 underfull (the narrow measure) · **820 macros, 0 unused** · abstract
**1897/1920** · clean regeneration **61/61 byte-identical** · arXiv set built
clean.

## Campaign, closed

460/460 worklist items terminal: 428 searched, 20 excluded (the archive holds
no pipeline calibration for them), 12 failed. Both of the two final retries
failed terminally — one legacy replay that produces no final measurement set,
one whose block the archive never calibrated. 3.97 of 4.28 TB downloaded,
calibrated and searched.
