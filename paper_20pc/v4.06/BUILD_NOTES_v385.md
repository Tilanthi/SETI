# BUILD NOTES — v3.85

Two referee reports worked one item at a time, then **five rounds of
independent self-review**, each verified against the released products
before any edit. Progress ledger: `REFEREE_CHECKLIST_V385.md`. Round
reports: `VPR_ROUND1..5.md`. What was done about each, including the
reviewer claims that turned out to be wrong: `VPR_DISPOSITION.md`.

## Gates

| gate | value |
|---|---|
| pages | 41 |
| LaTeX errors | 0 |
| undefined references / citations | 0 |
| multiply-defined labels | 0 |
| overfull boxes | 0 |
| Type 3 fonts | 0 |
| underfull boxes | 26 (the narrow two-column measure) |
| macros defined / unused | 1035 / 0 |
| abstract | 1878 characters (arXiv limit 1920) |
| clean regeneration | **81/81 byte-identical** |
| number audit | 51 pass, 0 fail |
| catalogue self-sufficiency | 41 headline quantities re-derived from the CSV alone, 0 fail |
| arXiv set | 70 items, 0 missing |

## The three findings that changed the paper

**The survey has 90 stars in 82 systems, not 94 in 87 — and the title said
94.** Four stars reached the frozen export under two name strings each
(SIMBAD's name route and its position route disagree on punctuation; two
entries carry a leading `* `), and TWA 3A's two Gaia components were in no
bound pair. Six generators each carried their own copy of the pair map, so
the count was consistently wrong everywhere and therefore invisible. One
shared `star_alias.py` now owns canonicalisation, the title is
`\NStars{} Stars within 40 Parsecs`, and the defence is an identity rather
than vigilance: **no two systems may share a distance**, asserted in the
catalogue writer. A related naming defect: the entry `j1256-1257` is the
ALMA field name for a field containing **LP 736-15**, whose Gaia parallax
of 47.27 mas is the 21.154 pc the catalogue already carried — real science
under the wrong name, now renamed.

**All four unattributed events have repeat coverage, and none recurs.** The
repeat-block finder required a crossing frequency the release stores only
sometimes, so it returned "no second epoch" for events with 3, 16 and 3
further blocks at the same tuning. There are 23 in all; the largest
stellar statistic anywhere in them is 5.42, none exceeds its own controls,
none is a stage-1 outlier. The paper had been understating its strongest
evidence.

**The drift-following, continuum-subtracted visibility fit was run on all
thirteen stage-1 events, and it closes the paper's loosest end.** It
recovers β Pictoris at the stellar position in 6 of its 8 windows at
6.1–9.5σ and reports HD 48370 as displaced, so the estimator works; and it
returns |Re/σ| ≤ 0.93 for all four unattributed events. It also returns
−0.86σ for CP−72 2713 where a simpler treatment of the same visibilities
gives 5.5σ: that window's stellar continuum is 10.9 mJy at 5.8σ, close to
the 10.4 mJy the simpler fit attributes to a narrowband excess, so the
excess is the continuum.

## Analyses added

- **Drift-resolved injection reporting** (`drift_strata_v385.py`). The
  campaign already had zero zero-drift trials; it had only ever been
  reported pooled. $P_{90}$ is 6.13 / 6.51 / 5.92σ across terciles of each
  window's own drift ceiling — a 10 per cent spread, no trend, and the
  outer third is not the worst. 92 per cent of detections return the
  injected drift *trial*.
- **The searched domain in acceleration** (`make_fig_accel2d.py`). The grid
  is built at constant acceleration, 3.598 m s⁻², which is 1.4 kHz s⁻¹ at
  115 GHz and 10.5 kHz s⁻¹ at 872 GHz. It clears Earth's rotation by ×106.
  Exactly two ceiling values exist, and the wider one — TRAPPIST-1's five
  windows — still stops 0.01 per cent short of planet b.
- **A systematic budget on $P_{90}$** (`p90_budget_v385.py`). Two-sided
  terms combine to ±8 per cent. Decorrelation (+5/+20) and pointing (+1.9)
  are one-sided biases that make $P_{90}$ optimistic and are carried
  separately; the window-to-window transfer (−52/+35) is the largest term
  and is an uncertainty for the windows the campaign never injected into.
- **$P_{90,\rm promote}$.** $P_{90}$ is calibrated against the 5σ trigger,
  but promotion also requires beating a control ring whose Class A median
  is 5.79σ. The power at which this survey would have *flagged* a carrier
  is 8.7×10¹³–1.4×10¹⁷ W, median 2.8×10¹⁵.
- **Rank uniformity, recomputed** (`ksrank_v385.py`). The claim that
  removing the fine crossings restores uniformity was true of a 431-window
  freeze and is false here: removing all 71 leaves $p=0.002$.
- **Both chance reference classes** (`blockboot_v385.py`). 4.4 over all
  searched windows, 1.1 over the drift-resolving class every stage-1
  outlier belongs to. The paper reports both and says plainly that on the
  narrow class the four unattributed events are a ~2σ excess.

## Withdrawn

The radius-corrected statistic is **no longer adopted as primary**: it was
built after the candidate list and moves the survey median away from the
exchangeable value, not toward it. It is a robustness check.

## New defences

`star_alias.py`, `inject_curve.py` and `localnorm_core.py` each exist to
make one quantity have one owner. `reproduce_from_catalogue_v385.py` opens
only the released CSV and re-derives 41 headline quantities, and runs
inside `make_all.sh`. `literalsweep.py` reports prose literals that
duplicate a generated macro — the mechanism behind almost every defect the
five rounds found.

## Author actions

Three submission blockers remain and are the authors': the Zenodo DOI, the
submission git tag and the White (2026) identifier. See
`AUTHOR_ACTIONS.md`.
