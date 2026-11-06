# v4.03 — the round-7 ledger, the reference epoch, and the chain re-framed

Built 2026-09-26 from `v4.02/` by `cp -a`. Binding decisions:
[`referee_r7/DECISIONS_R7.md`](../../referee_r7/DECISIONS_R7.md) A1–A6, with the
A2 wording correction from
[`referee_r7/ledger_v403/LEDGER_V403_NOTES.md`](../../referee_r7/ledger_v403/LEDGER_V403_NOTES.md)
§2.4 and the gap closures from
[`referee_r7/GAPS_R7.md`](../../referee_r7/GAPS_R7.md).

**This version changes what the paper claims.** Three statements carried in
v4.02 are withdrawn, in the paper's own voice and not as a revision history:

1. *"Zero unattributed localised crossings."* False. Under the committed
   reference epoch there is one ($\eta$~Crv); under the adopted one there are
   30.
2. *"Emission at the stellar position is excluded at 3.3–6.1 $\sigma$ at the
   unattributed events"* — in the **abstract** and the conclusions. Withdrawn.
   Re-fitted at the correct epoch, 61 Vir returns Re/$\sigma$ = 5.26, which is
   0.97 of what a compact source at the star producing its trigger would give.
3. The three CO positive controls as validation of the visibility estimator,
   and round 6's rejections as evidence. Both withdrawn (A4).

None of that makes anything a candidate. The terminal count is still zero, but
it now rests on the rank screen and on recurrence, which is what A3 requires.

---

## 1. The ledger

`ledger_v401.py`, `make_fig_ledger.py`, `survey_numbers_round76.tex`,
`tab_ledger_v401.tex` and `figures/ledger_vis.pdf` are **deleted**, in the same
pass that adds `ledger_v403.py` and its products. Two macro files defining
`\LgNCross` are a multiply-defined error and a stale generator writing round 76
trips `roundcollide`, so the replacement and the removal are one change.

`\LgNLocal`, `\LgNLocalUnattr`, `\LgNMissed`, `\LgNScreenNotLocal` and
`\LgReMaxNotLocal` are deliberately **not** redefined. Their meanings changed
(there are now two conventions), so any surviving use had to fail the
undefined-macro gate rather than print a stale number. None survived.

**Table 3** is now `tab_ledger_v403` — all 56 crossings, both epochs, the
channel displacement $D$ between them, the rank flag, the stellar-frame
attribution and a chain disposition — at `\tiny` in a full-width `table*`
(measured box 483.2 pt against `\textwidth` 513.1 pt). **Table 4** is the new
`tab_ledgersum_v403`, counts against chance.

**Tables 4, 5 and 6 of v4.02 are deleted**: `tab_stages_v386` (the stage
funnel, now the chain figure plus the summary table), `tab_unattributed_v383`
(its two events are rows of the ledger, with their evidence) and
`tab_flagged_v380` (the rank screen is demoted to the `scr` column, R1-M4).
Nine `\ref`s to them were repointed at `tab:ledger`.

**Fig. 2** loses its right-hand panel. It drew the experiment as one nested
funnel ending in "localised at the star in the visibilities" → "independently
confirmed", which asserts exactly what A2 withdraws, and it ran the rank screen
*before* line attribution where the chain runs attribution first. It is now the
selection funnel alone, single-column. `funnel_steps.tex` went with it: a macro
counting how many steps are drawn is meaningless once none are.

**Fig. 5** is `figures/chain_v403.pdf`, the A3 chain with the visibility fit in
a box beside the column joined by a dashed connector. Every count is read from
`ledger_v403.json`, and `E[max of 12]` is read from `epoch_v403.py`'s
computation rather than hard-coded — it disagreed with the prose in the second
digit for one build.

**Fig. 15** (appendix) is `figures/ledger_vis_v403.pdf`: (a) the same fit under
the two reference epochs, joined per crossing; (b) the verdicts against $|D|$,
showing that every change of verdict happens above about one channel and none
below 0.25. It was in the main text until the page measurement; see §4.

## 2. What was rewritten

- **§4.6 (`sec:statistic`)**: the selection logic is now **four** steps —
  crossing, attribution, rank, recurrence — not five with localisation third.
  The visibility fit is described beside the chain. `tab:interpret` gains an
  Attribution row and demotes Localisation to "consistency check, reported
  alongside". The β Pictoris "internal positive control" sentence is deleted
  (A4).
- **§4.9 (`sec:summary`)**: the step list follows the chain and the counts come
  from the ledger.
- **§5.2**: "none of the four shows a source at the stellar position" replaced
  by what the corrected fits say; the twelve prose "four"s for the unattributed
  count are gone (`\NStageOneUnattrib` = 2). The remaining literal "four"s in
  the appendices refer to different sets and were checked individually.
- **§5.2.1 (`sec:vistest`)**, rewritten: the reference-epoch defect and its
  repair; the withdrawal of round 6's rejections and of the CO positive
  controls; the criterion; why clauses 2 and 3 reject nothing except one
  grossly displaced source (4 of 44, all BD+05 1668; 1 of 39 epoch-verified);
  twelve controls resolving 1/13 with E[max] = 1.63; the chain; and what a
  threshold crossing is worth on its own.
- **§5.2.2 (`sec:etacrv`)**, new: $\eta$~Crv `A002_X122b6ff_X1041e` in full,
  always with $T_\star$ = 5.0059 and its failed rank screen in the same
  sentence (A5); and the line-list caution, which generalises.
- **§5.2.3 (`sec:chaingap`)**, new: the end of the chain and the one bound that
  remains.
- **Abstract and Conclusions**: the exclusion claim replaced; the result stated
  over all 56 crossings; "among the crossings tested" everywhere.
- **Appendix A.3.1 (CP−72 2713)**: its visibility Re/$\sigma$ was from the
  broken-epoch estimator. The fit is outstanding and the text now says so.
- **Appendix J and Appendix K (the ACA control geometry)** — see §5.

## 3. Two general findings folded in, worth more than the crossing

**(a) The trigger carries no evidential weight on its own.** Measured on the
released catalogue's own windows (`ctrlrate_v403.json`, matched on block and
window edges so no epoch-extension block leaks in): over the 332 Class A
windows whose 512-element control vectors are retained, a single control
position reaches the survey's *smallest* crossing statistic, $T$ = 5.0059,
**8.8 per cent of the time** (median 6.5), against 0.11 per cent in the coarse
windows. Summing each window's own rate predicts 29 Class A windows whose star
reaches that value by chance; 49 are observed; extrapolated to all 403 Class A
windows the expectation is of order 35. *That is why the chain does not stop at
a crossing and why the rank screen exists.*

★ This is a refinement of `ETA_CRV.md` §4.1, which measured 9.0 per cent over
557 fine windows including epoch-extension blocks outside the released
catalogue. Restricting to the catalogue removes that caveat entirely.

**(b) A wide-line-list coincidence is not evidence.** At 357 GHz the survey's
own Splatalogue harvest holds 30 transitions per GHz, so a ±50 km s⁻¹ window
contains 3.6 of them on average and a **uniformly random** frequency in the
spectral window lands within the mask half-width of some harvested transition
**77.7 per cent of the time**. A hit is the default outcome. The manuscript was
checked for a wide-list coincidence used as evidence and does not contain one:
every attribution count is computed against the frozen 17-transition mask. The
paper now says which list is which and why.

## 4. Length

| | v4.02 | v4.03 |
|---|--:|--:|
| main text (§1–Conclusions) | 16.03 pp | **14.98 pp** |
| by the `\label`-anchored count in `gate.sh` | main 16 pp | **main 15 pp** (appendix starts p. 16) |
| appendices | 26.19 | 27.33 |
| total pages | 43 | 43 |

**Both referees' ≤15-page cap on the main text is met.** Deleting Tables 4, 5
and 6 did most of it; the rest was compression of §5.2 and §5.2.1 and moving
`fig:ledgervis` to Appendix K.

★ **The page split was re-measured after every pass, and it moved the wrong way
twice.** Deleting two redundant paragraphs took the reported main text from
15.07 to 15.92 pp because a float migrated across the Conclusions anchor;
the total was unchanged. Prose deletion below about 16 pp is not monotone.

★ `tab_ledgersum` was 388 pt wide at `\scriptsize` against a 251 pt column.
Promoting it to a `table*` to fit **doubled** its page cost, 0.13 → 0.27 pp, for
fourteen numbers. The chance-model column moved into the caption instead:
213.6 pt, one column. Measure with `\savebox` and `\the\wd`.

## 5. The stale ACA passages — verified, then rewritten

`BUILD_NOTES_V402.md` §5 flagged two passages describing the 12 m-beam control
geometry in the present tense, as unrepaired, while the same appendix quoted the
after-repair KS test. **Verified before editing, not guessed.**

`corrected_export_v399.py` stamps every row it replaces with
`provenance = corrected-geometry`, and `v342_calc.py` builds the released
catalogue from that export. Joining the catalogue to the export on
(block, window edges) and the array on `archive_meta_v381.json`:

- **1053 of the 1054 ACA windows in the released catalogue carry the repaired
  control geometry.** The one that does not is towards LHS 1140
  (`A002_Xd9d7c7_X6fd2`), outside the 278 re-extracted blocks.
- 64 of the 601 12 m windows are also from the re-extraction (the blocks holding
  threshold crossings).

So both passages were stale. `acafix_v399.py` now computes that split
(`\FixNCatAca`, `\FixNCatAcaFixed`, `\FixNCatAcaLeft`, `\FixCatAcaLeftStar`)
with an assert that fails the build if the repair ever stops covering
essentially all of them, and:

- the false-alarm appendix now says the *original* extraction carried the error,
  that it was removed at source, and how much of the release carries the repair;
- Appendix K's radial-gradient diagnosis is past-tensed throughout and points at
  the repair, which now has its own subsection (`sec:acarepair`) instead of
  sharing an anchor with the false-alarm conditioning subsection;
- Table 24's caption says the same.

## 6. Three defects found and fixed in the adopted code

1. ★ **`selftest_v403.py` reported a demonstrated check that was not
   demonstrated.** The `recurrence-name` perturbation renamed a dict *key*,
   but the star comes from the *record*, so it could not reach the join and the
   generator succeeded silently. `LEDGER_V403_NOTES.md` §4 lists it as `ok`;
   it was not. Fixed to corrupt the field the check reads. *Same class as the
   defect the selftest exists to catch, and the second instance in that file.*
2. ★ **The same thing happened again when the gap closed.** `recurrence-extra`
   ADDED a recurrence record, which worked while the expected gap was 1 and
   went silent the moment it became 0. Replaced by `recurrence-drop`, which
   removes one. *A tripwire must be driven in whichever direction its literal
   can move.*
3. ★ **`vispower_v400.py` read the previous run's ledger for one build.** It
   was repointed at `ledger_v403.json` but left at its old position, three
   dozen lines before `ledger_v403.py`. The clean-regeneration test found it
   only after `ledger_v403.json` was added to its product set — a product that
   another generator consumes is exactly the one that test must delete.

Also: `\input` inside a `\caption` breaks hyperref ("Argument of `\Hy@tempa`
has an extra }"), because the caption is re-read when written to the `.aux`.
The ledger legend is now a `\DeclareRobustCommand` `\input` in the preamble.
Same family as the `\pv` macro at v4.00.

## 7. The evidence gaps, closed while this was being built

`DECISIONS_R7` A3a forbade asserting the terminal zero until two gaps closed.
The sibling worker closed both, and they are folded in:

- **61 Vir `A002_Xc079b5_X82f`** — 7 covering repeat blocks, all searched, every
  one with the power to have seen it; largest statistic at its own channel and
  drift 2.94 against a trigger of 5. `sixtyone_verify.json`.
- **CP−72 2713 `A002_Xff0235_X4a6d`** — 5 covering repeats, max 3.60.
  `cp72_verify_r7.json`. Its *visibility fit* is still outstanding.

Recurrence is now evaluated for 10 crossings over 51 repeat blocks, max
$T_\star$ = 3.94. The ledger's recurrence input became a **glob** so that
closing a gap is a re-run and not an edit, and `N_RECUR_GAP_EXPECTED` moved
1 → 0 with the prose.

★ `sixtyone_verify.json` writes its *plan label* — `61 Vir second crossing` —
into the record's `star` field. `recurrence-join-names-agree` caught it. The
check now accepts a prefix relation in either direction and **lists** what it
normalised in `ledger_v403.json` (`recurrence_name_normalised`), rather than
tolerating it silently. **The upstream defect belongs in the M10 harness.**

The remaining bound is stated in §5.2.3 and nowhere weakened: 6 crossings in 4
blocks have no visibility fit, so the paper says *zero among the crossings
tested*.

## 8. Gates

| gate | result |
|---|---|
| pdflatex errors | **0** |
| undefined references / citations | **0** |
| multiply-defined labels | **0** |
| Overfull boxes | **0** |
| Type-3 fonts | **0** |
| `roundcollide.py` | **71 round files, 71 inputs, 0 problems** |
| `macrosyn.py` | **0 problems** (11 groups, 6 relations, 77 macro files, 9 deferred) |
| `consistency_v399.py` | **0 problems** |
| `prosenum_v399.py` | **0 literals disagreeing with a macro** |
| `macroleak.py` | **0 problems** |
| `audit_numbers_v385.py` | **49 PASS / 0 FAIL** (10 WARN, 7 SKIP) |
| `reproduce_from_catalogue_v385.py` | **22 pass / 0 FAIL**, 19 skipped |
| `selftest_v403.py` | **26 checks, 20 demonstrated failing, 6 structural, 0 undemonstrated** |
| `xrefcheck.py` | 117 labels, 0 misplaced |
| **`cleanregen.py`** | **108/108 byte-identical** |

**Page split:** 43 pages — main text **14.98 pp**, back matter 0.13,
appendices 27.33, bibliography 0.27. By the `\label`-anchored count: appendix
starts p. 16, so **main 15 pp / appendix 28 pp**.

**Abstract:** 1743 rendered characters, 276 words (arXiv limit 1920).

Underfull boxes 55, unchanged in kind from v4.02; they are not a gate.

## 9. What is NOT in this version

- **The round-7 P90 campaign.** Still running on the host (37 of 56 units at
  last check). Every $P_{90}$ macro is untouched, and the
  `\SelTransFine*`/`\StratTransferNine*` divergence remains a `macrosyn`
  DEFERRED entry. When it lands it will move the sensitivity numbers and
  nothing in this version.
- **The closure-phase RFI record.** `GAPS_R7.md` §3 found that a
  machine-readable per-window interference product *does* exist —
  `closure_phase_vetting` in the on-host result files, present for 13 of 56
  crossings and all 12 stage-1 events, and never mentioned in the paper. It is
  not wired into a generator here. The RFI appendix instead states plainly,
  per A3b, what screening exists and with what coverage, and that no
  per-channel interference flag of our own exists or can be recovered. **This
  is the obvious next generator** (`rfi_ledger_r7.json` is already written).
- **`visfit_v385_calc.py` and `visgain_v399.py`.** None of the five macros they
  generate is typeset any more; all are retired. The generators still run
  because `visgain_v399.py` reads the other's output. Retiring both is the fix
  the `macrosyn` DEFERRED entries now name.

## 10. Referee-round-8 findings folded in late

Two arrived from `referee_r8/BASELINE_ARTEFACTS.md` while this version was
being built, and were cheap enough to take.

**(a) Two denominators under one phrase.** The frozen $\pm50$\,km\,s$^{-1}$
mask attributes **16** of the 56 crossings; **10** is the attributed subset of
the 12 *stage-1 flagged windows*. Both are in the paper and both are now
explicitly labelled with their denominator — the abstract, §5.2.1 and the
chain figure say "of the \LgNCross{} crossings", §5.2 and the Discussion say
"of the \NStageOneWin{} stage-1 windows". No bare "10 molecularly attributed
events" survives.

**(b) CP$-$72 2713 and SO $8_8$--$7_7$.** Appendix A.3.1 said the crossing had
"no line within $\pm50$\,km\,s$^{-1}$ in the stellar frame". That is true of
the **frozen mask** and false of a wide catalogue: SO $8_8$--$7_7$ lies at
$-12.3$\,km\,s$^{-1}$ in this block's own stellar frame. The paragraph now
says which list is which, reports the coincidence, and calibrates it the same
way §5.2.2 calibrates $\eta$~Crv's: at 344\,GHz the harvest holds 39
transitions per GHz and a random frequency hits one 91 per cent of the time,
and the nearest transition here is an unidentified line rather than SO. Two
measurements close it independently of any line list — the feature is 3
channels wide at the recovered drift against 2 for the instrumental response,
and CO($3\to2$) is in the same window and absent below a limit fainter than
the crossing. **The disposition does not change.** The species list now spells
"silicon monoxide SiO", because the round-8 referee read SiO(5--4) as SO and
the misreading is the premise of the whole objection.

★ The "1323\,km\,s$^{-1}$" the ledger prints for that crossing is the offset
to the nearest **masked** transition and is correct as labelled; it is not a
claim that nothing lies nearby.

**Two further round-8 findings were taken because leaving them would have
shipped a false sentence, using no new number:**

- Appendix I claimed *"zero crossing frequencies lie 13--50 km s$^{-1}$ from
  their nearest masked transition"*, and concluded from it that a
  $\pm13$\,km\,s$^{-1}$ mask would have released the same windows. Both are
  false (15 of 53 in the sky frame, 1 in the stellar frame; and $\pm13$ would
  have released HD 48370's $T_\star=26.8$ CO(2--1) as unattributed). The claim
  and its conclusion are **deleted**; the replacement measurement is a v4.04
  item.
- Appendix K.4.3's *"admits no new unattributed outlier"* is false at
  $\pm13$--$\pm30$. It now says what is true and needs no new number: every
  crossing that narrowing releases is an identified CO line of this survey's
  own, the two rank-flagged unattributed crossings are the same pair at every
  half-width, and widening cannot suppress anything further.

### Deferred to v4.04

- **The frozen mask is 17 transitions in `v342_calc.py` and 15 in the search
  code's own veto list** (`KNOWN_LINES_GHZ` lacks [C\,\textsc{i}](1--0) and
  H30$\alpha$, added to the paper's mask at v3.46). Neither addition is near a
  crossing, so nothing moves, but one number is being used for two objects.
  **Being measured; not resolved here.** v4.03 removed its one *new* use of the
  count (§5.2.2 now says "the frozen mask" without a number); the pre-existing
  Appendix K.4.3 sentence is left alone rather than replaced with a guess.
- The measured replacement for Appendix I's deleted claim (15 of 53 sky frame,
  1 of 53 stellar frame), and the frame disagreement it exposes between the
  paper and the attribution code.
- The full mask-width ladder as a generated table.
- Appendix M's clustering test, which round 8 finds broken three ways
  (grid-respecting null gives $p=1.0000$; the right test finds clustering at
  $p=0.0025$ that is entirely the survey's own CO attributions).

★ **Amended after the push** (notes only; the manuscript, its products and every
gate result above are unchanged). Two of the items above were measured by the
sibling worker `edge-and-maskframe` within the hour, and the answers change what
v4.04 should do:

- **The near-edge false-alarm excess of $\times2.4$--$3.5$ is WITHDRAWN**
  (`referee_r8/EDGE_AND_MASKFRAME.md`). It is one window — HD 48370
  `Xc26103_X155a` spw16, which holds the survey's bright *resolved* CO(2--1)
  line 92 channels from the edge, where the control annulus sees it. Remove
  that window and the ratio is $\times1.003$ ($p=0.51$). CP$-$72 2713's own
  window has **zero** near-edge exceedances, so the "(e)" ground round 8
  offered for that crossing is gone. **Nothing in v4.03 asserts it** — it was
  listed here only as a v4.04 item, and it should now be struck.
- **The 17-versus-15 mask discrepancy is settled, and v4.03's decision not to
  guess was the right one.** They are two literals in `v342_calc.py`: the
  search ran `CAT_OLD`, 15 transitions rounded to 1 MHz and identical value for
  value to the search code's `KNOWN_LINES_GHZ`; `CAT` adds
  [C\,\textsc{i}](1--0) and H30$\alpha$ at v3.46 to make 17. **0 of 51 nearest
  transitions change between the two lists**, so it is a documentation defect
  and not a correctness one. Appendix K.4.3's "\MaskNTransNew{} transitions"
  is therefore correct about the paper's mask; v4.04 should say which list the
  *search* ran.
- ★★ **And the mask frame is TOPOCENTRIC, not stellar**: 51/51 `line_offset_MHz`
  and 48/48 `line_offset_kms` reproduce topocentrically, 0 barycentric, 0
  stellar. Appendix I's "the mask being evaluated in the stellar frame" is
  wrong and is a v4.04 item. **Nothing v4.03 states is false on this**, because
  0 of 44 attributions change between frames and the two stellar-frame offsets
  v4.03 quotes ($\eta$~Crv's 9929 km s$^{-1}$, CP$-$72 2713's $-12.3$) are
  computed quantities, correct in the frame they name.

## 11. Noticed, out of scope, not changed

- **`\LgVerRejectStar` (BD+05 1668) is rejected as instrumental on two
  independent grounds** and the paper only gives one. `RFI_EVIDENCE.md` finds
  the same coarse channel toward four unrelated stars, and two of its four
  crossings 8 channels from the band edge at identical fractional position in
  basebands exactly 2.000 GHz apart — a fixed intermediate frequency. The RFI
  appendix now names it as instrumental but does not carry that evidence.
- **`frequency_occupancy.py` in the search pipeline is broken** (`path.split('/')[3]`
  is the constant `targets`, so it can never report a cluster). Patched on the
  host by the gap worker; the paper does not depend on it.
- Eight figures are built and never `\includegraphics`'d, and
  `tab_visibility_v38*.tex` still writes `HD14055`. Unchanged from v4.02.
- `sec:acalimit` is a label with no reference (since v4.02).
- The version folder still carries `.aux`/`.log`/`.out`/`.pdf` from v3.87–v3.90
  and superseded `apply_v3xx_stage*.py`. The deposit is larger than the paper.
