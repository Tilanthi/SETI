# v3.97 — two referee reports

**Built 2026-09-23.** 42 pp. Gates: 0 errors, 0 undefined refs/cites,
0 multiply-defined, 0 overfull, 0 misplaced labels. Abstract 1909/1920.
Clean regeneration **81/81 byte-identical**. New gate `prosenum_v397.py`: 0.

---

## The two findings that matter

### 1. Referee 2's M3 is right, and our published explanation was wrong

The claim was that the control annulus is built from a 12 m primary beam for
every window, including ACA 7 m data. **Confirmed in the pipeline source**:

```
ALMA_DISH_M = 12.0
primary_beam_arcsec(f) = 1.22 * lambda / ALMA_DISH_M     # no array dependence
annulus = 0.14 .. 0.78 * primary_beam_arcsec
```

So an ACA window has its annulus placed at **58 %** of the correct radius. At
230 GHz the inner edge falls at **3.8″** instead of 6.6″, **inside** a typical
ACA synthesised main lobe (~7.3″). Those controls sit on the star's own
synthesised beam and collect its flux.

**Three measurements confirm the mechanism** (`acageom_v397.py`, round 61):

| | 12 m (correct geometry) | ACA 7 m (wrong geometry) |
|---|---|---|
| windows | 601 | 1054 |
| stellar-rank KS | D = 0.027, p = 0.77 | D = 0.10, p < 0.001 |
| inner-bin control excess | **+0.007** | **+0.108** |

The departure is confined to the stratum with the defect; the excess sits at
the inner edge where the contamination is; and the direction is right, since
inflated controls push the star *low*, which is what is observed. **A primary
beam effect would act on both arrays. This does not.** The
primary-beam-gradient narrative is withdrawn from the main text and both
appendices.

**A consequence the paper had backwards.** It said the 4-vs-1.3 stage-1 excess
was "an artefact of the position-dependent rank bias". The measured bias puts
the star *low*, which suppresses star-first outcomes rather than producing
them. The claim is withdrawn and the count is now described as a marginal
excess from which no inference is drawn.

**Referee 2 asked us to confirm the three events look like ACA windows. They
are.** 61 Vir, HD 23484 and HD 14055 are ACA; CP−72 2713 is 12 m. Because the
bias runs *against* flagging, these three were promoted despite an adverse
screen. New §6.4 *What rests on the ACA windows* states exactly what does and
does not depend on them: nothing in the sensitivity does, since the geometry
enters the screen and not the threshold.

### 2. Referee 2's M1 is right, and it invalidates a table we added ourselves

Only **4 of 13** stage-1 windows (and 20 of 75 crossings) have a stored
crossing frequency. For 61 Vir, HD 23484 and HD 14055 the pipeline recorded no
peak, so their Δv is a window-level number — HD 14055's reads
**−12 161 km s⁻¹**.

The v3.94 mask-robustness table was therefore built on the wrong quantity
*twice over*: on an uncorrected **sky-frame** offset when the disposition rule
is applied in the **stellar** frame (M5), and on offsets not measured at the
crossing for 9 of 13 windows. **The table is withdrawn**, with the reasoning
stated in the text. That is a retraction of our own addition from two rounds
ago.

---

## Other required changes

| Item | Action |
|---|---|
| R2-M2 | Deleted the single-channel, continuum-unsubtracted visibility table; one version of the test (drift-following, continuum-subtracted) now stands. Stated explicitly that the average runs over the MS's own rows, **not** the Hermitian completion, so the imaginary part carries information |
| R2-M6 | Fixed every stale count: three "one observed"/"the single unattributed" left from when the survey had one event; **Table 7's recurrence criterion**, which tested the trigger alone and so marked HD 14055 as recurring on a repeat that does not outrank its controls. Criterion now matches the stage-1 definition. New gate `prosenum_v397.py` checks prose literals against macros |
| R2-M7 | Harmonised the comparability statements. Appendix F was right: for a sub-channel carrier the plotted quantity is a physical total power. What differs is the **convention**, and it runs against us — we plot a 90 % recovery through the complete selection, most comparisons plot nominal thresholds |
| R2-M8 | Deleted the duplicate "In plain terms" paragraph in §1, the "About this paper" section, and **Appendix J (continuum lane)** with all five references reworked. "pre-registered" → "pre-specified" throughout |
| R2 minor 1 | **Polarisation physics corrected.** ALMA's feeds are linear, so a per-hand search helps only a carrier aligned with one feed, and parallactic rotation dilutes even that. A *circularly* polarised carrier — the β Pic b ECMI case — splits equally between XX and YY and gains nothing; it needs the cross-hands, which we do not extract |
| R2 minor 3 | ~10 GHz → ~30 GHz, the frequency above which only Mason et al. (2024) has searched |
| R2 minor 7 | Gaia DR3 → Gaia Collaboration, Vallenari et al. (2023, A&A, 674, A1) |
| R2 minor 10 | Deleted the duplicated line-mask row in Table 2 |
| R1-3 | Alternative-statistic and radius-correction detail condensed; main text keeps the failure of exchangeability, the mechanism, the prioritisation-only role and the hold-out |
| R1-4 | **Sensitivity is now a distribution** (`sensdist_v397.py`): of 60 systems, 3 reach 10¹⁴ W, 22 reach 10¹⁵ W, 55 reach 10¹⁶ W and all 60 reach 10¹⁷ W. In the abstract |
| R1-5 | §6.2 now opens with the temporal selection: **40 of 82 systems** have no independent epoch at all (27 single-block, 13 same-day). Asserted to close against the 42 with independent epochs |
| R1-6 | Title → *"…toward Nearby Stars"*; the abstract now says "unresolved within 15.3–1953 kHz channels, far coarser than Hz-resolution SETI, with which these limits are not comparable" |
| R1-7 | The combined union never appears without "of which only 47.7 GHz is drift-resolving" |
| R1-8 | §6.5 closes with an explicit refusal: no inference to the 40 pc population is attempted |
| R1-9 | The four events are now rejected **first** on physical grounds — no visibility localisation (max \|Re/σ\| = 0.93 against 5.9–9.5σ for β Pic CO) and no recurrence — with the chance count demoted to supporting information |
| R1-10 | Abstract restructured to sample → signal → calibrated sensitivity → result/limitation |

---

## Not done, and why

- **R2-M1's re-run** (52 blocks, 0.40 TB, ~18 h) and **R2-M3's ACA
  re-extraction** both need a full re-search from raw visibilities. Neither
  fits this revision. Both are now stated in the paper as the outstanding work,
  with the ACA re-extraction named as the single most useful next step on this
  dataset. Everything that rests on them is flagged rather than asserted.
- **R2-M4** (recompute P90^sel by counting injections against each window's
  ring maximum) is tractable from stored products and is the next thing I would
  do; it is not in this version. The definitional chain it asks for is
  partially addressed by the sensitivity distribution.
- **R1's Figure 3 redraw** as a branching diagram is not done.

## New this round

`acageom_v397.py` (round 61) — asserts the implemented inner radius lies inside
the ACA synthesised beam, and that the excess is confined to the ACA stratum.
`sensdist_v397.py` (round 62) — asserts the benchmark counts are consistent
with the quoted median. `prosenum_v397.py` — gate, prose literals vs macros.
`epochsplit_v397.py` — now asserts the temporal partition closes.
