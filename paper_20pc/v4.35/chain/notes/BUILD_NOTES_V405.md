# v4.05 — the finished round-8 measurements, wired in

Built 2026-09-26 from `v4.04/` by `cp -a`. v4.04 pushed the round-8 prose and
structural pass but deliberately deferred a set of measurements that were
already finished; this version wires them in, each at its generator and each
with an assertion that can fail.

Binding decisions: [`referee_r8/DECISIONS_R8.md`](../../referee_r8/DECISIONS_R8.md)
D1–D15 (D4 and D9a in particular) and
[`referee_r7/DECISIONS_R7.md`](../../referee_r7/DECISIONS_R7.md) A1–A6.
Measurement index: [`referee_r8/V404_MEASUREMENTS.md`](../../referee_r8/V404_MEASUREMENTS.md).

★ **Glenn's standing directive remains in force: page length is deferred.**
Nothing scientific was deleted to save space, and length was measured but not
optimised: **main text 16.62 → 17.72 pp, total 46 → 48 pp.** Both referees'
≤15-page cap on the main text is therefore still not met, deliberately.

★ **Every $P_{90}$ macro is untouched, as instructed** — verified, not assumed:
of the 24 macros in the $P_{90}$/selection family, **0 changed value** between
v4.04 and v4.05. The only five macro values that moved in the whole build are
listed in §11.

---

## 1. Computed dispositions (D4) — and the hand literal was worse than documented

`v342_calc.py` now computes a disposition for **all \NHits{} = 56 threshold
crossings** from the frozen 15-transition mask (`CAT_OLD`) evaluated
**topocentrically** at the survey's own ±50 km s⁻¹ half-width, with no rank
gate. The catalogue ships **three** disposition columns instead of one:

| column | what it is |
|---|---|
| `disposition_computed` | the computed rule, all 56 rows, no rank gate |
| `disposition_hand` | the authors' evidence-based label, re-keyed on (star, block, window) |
| `disposition` | **unchanged** — the hand label gated on the rank screen, verbatim from Table 5 |

`NCatCols` 51 → 53. **Every pre-existing column is byte-identical**, checked row
by row against the v4.04 catalogue (0 rows with a changed old column).

**Counts: 16 attributed over crossings, 10 of those also rank-screened.** The
10 reproduces the paper's "10 molecularly attributed events" exactly; the 16 is
the same quantity over the crossing population rather than the stage-1 subset.
Both are now labelled with their denominator wherever they appear.

### 1.1 The disagreement list, crossing by crossing (`tab_dispo_v405.tex`)

Eight rows. **Six crossings the frozen mask attributes ship with a BLANK
disposition** — assertion **A1** fires on the released column and names all
six:

| star | block | B | T⋆ | computed line | Δv (km s⁻¹, topo) | shipped |
|---|---|:-:|--:|---|--:|---|
| ALMA J153702653−33192492 | `Xff0235_X8392` | 6 | 5.41 | CO(2–1) | −20.6 | *(blank)* |
| HD 285968 | `Xd98580_X3bf6` | 6 | 5.96 | CO(2–1) | −46.7 | *(blank)* |
| HD 285968 | `Xdb4b9a_X108f` | 6 | 5.83 | CO(2–1) | −36.4 | *(blank)* |
| HD 285968 | `Xdb7ab7_X5b4e` | 6 | 5.87 | CO(2–1) | −34.4 | *(blank)* |
| HIP 10679 | `Xa95c04_X14cd` | 6 | 5.46 | ¹³CO(2–1) | +26.5 | *(blank)* |
| β Pic | `X7116f1_X1785` | 6 | 9.68 | CO(2–1) | −14.1 | *(blank)* |

These are **not errors of attribution** — every one is correctly identified by
the computed rule. They are a **coverage gap**: only rank-screened windows were
ever dispositioned, so the released catalogue could not answer "what is this
crossing?" for the 44 it did not flag. Three of the six are the HD 285968
CO(2–1) events the round-6 campaign localised in three independent blocks.

The remaining two rows are the rank-screened crossings the mask does **not**
attribute — 61 Vir `Xc079b5_X82f` (CO(3–2), +448.9 km s⁻¹) and CP−72 2713
`Xff0235_X4a6d` (CO(3–2), −1323.2 km s⁻¹). **Not a disagreement in content**:
the hand string and the computed rule both say `unattributed`, and the hand
string carries the extra second-epoch evidence the mask cannot know. That is
exactly the material D4 says to keep in a separate labelled column.

### 1.2 ★★ (star, band) IS NOT A KEY — assertion A2 fires twice

β Pic Band 6 holds **7** crossings in **two** basebands **11 GHz** apart: five
on CO(2–1) at −12 to −29 km s⁻¹, and two at 241.553 GHz. Applied to every
crossing of the pairs it names — which is what a (star, band) literal literally
asserts — the old map labels those two **"circumstellar CO"** at **−3,793** and
**−3,898 km s⁻¹** from CS(5–4). The rank screen happened to hide it; one
`ctrl_max` fluctuation and the catalogue would have shipped it, and nothing in
the build would have complained. The hand map is re-keyed on
(star, execution block, lower window edge), 12 entries, every string verbatim.

| assertion | shipped release | hand literal, ungated | computed column |
|---|--:|--:|--:|
| **A1** attributed ⇒ disposition | **6 offenders (FAILS)** | 5 (FAILS) | 0 (passes) |
| **A2** molecular disposition ⇒ mask agrees | 0 (passes, via the rank gate) | **2 offenders (FAILS)** | 0 (passes) |

Both outcomes are asserted in the build, so the finding cannot lapse silently:
`assert len(_A1_shipped) == 6` and `assert len(_A2_hand_old) == 2`, plus
`assert all(abs(dv) > 3000 ...)` on the two mislabels.

### 1.3 ★★★ A TAUTOLOGICAL CHECK, CAUGHT BY THE GATE THAT EXISTS FOR IT

The first version of the re-keying assertion compared the shipped column
against `dhand` — but `dhand` is what the shipped column is *computed from*, so
the comparison could not fail. `selftest_v405.py` moved one hand key by 1 kHz
and the generator **exited 0**. It now compares the re-keyed map against the
**old (star, band) map** gated the same way, which is the column every earlier
release actually carried; the same perturbation now raises.

**Sixth instance of this family in this project** (v4.03 found three, v4.04 two).
*A check that compares a quantity with something derived from it is not a check.*

## 2. Appendix M's clustering test, replaced by a measured one (R2-9)

`appm_v405.py` (round 91) + `figures/appm_power.pdf` (3 panels) + 30 macros.
**The falsifier runs first**: the generator asserts it reproduces the shipped
1 MHz statistic — max multiplicity **4**, continuous null **2.44 ± 0.15**,
**p = 0.0095** — before criticising it. Three defects, then the replacement:

1. **It is not counting the crossings.** The 1,401 values are every window's own
   peak-SNR frequency, not the 56 threshold crossings, and **1,070** of them are
   coarse continuum windows whose "peak" is a noise maximum. Stated in the text.
2. **The null ignored the ALMA channel grid.** A peak can land only on one of its
   window's own channels, and two windows with the same standard tuning share an
   *identical* grid. On the grid null the mean is **5.06** and **p = 1.0000**.
   All four crowded bins are the same channel of the same tuning on four stars
   and **not one is a crossing**. ★★★ *The p = 0.009 was manufactured by a null
   that did not know ALMA has a channel grid, and the honest repair makes the
   interference evidence WEAKER, not stronger.*
3. **No power.** Over 156 MHz the 1 MHz statistic rejects **0.0 / 1.3 / 8.8 %**
   at 6 / 12 / 24 injected events — 24 events is half the crossing population.
   The scan statistic reaches **10.5 / 100 / 100 %** and is flat in width.

★ **The old test is described, not merely deleted.** Against a cluster *exactly*
one channel wide it beats the scan outright (**100 %** against **10.5 %** at six
events): it is a **channel-coincidence detector**, and the paper says so.

**What the replacement finds**: the crossings *do* cluster, at **p = 0.0042**
(12 observed against 7.34) in **230.423–230.723 GHz**, **9 of whose 12 members
are CO(2–1)**, falling to **p = 0.107** with the line-attributed removed. And
the same statement with no band or width chosen at all, which is what the text
leads on: **11 of the 51 released crossing frequencies lie inside the survey's
own ±50 km s⁻¹ tube against a matched grid null of 4.8, p = 0.0010.**

Asserts that can fail, all demonstrated: the falsifier (fires at 2.94 if the bin
width moves, 5.08 if the null is swapped); every peak on its window's grid
(worst 0.055 channel); the **power ordering at k = 12** (scan > 1 MHz) *and* the
**reverse ordering at 1 MHz** (1 MHz > scan), so both halves of the description
are machine-checked; size ≤ 0.05 for both statistics; no crossing in a crowded
bin; tube observed > tube null.

★ **Two defects found in the ported code.** `\AppMPowerNewWide` was emitted at
k = 24 while the prose sentence said *twelve*; redefined at k = 12 (same value,
100.0, but now true by construction). And `\AppMBandWidth` = 300 MHz is the top
rung of the ladder, so the maximal band is "≥ 300 MHz wide" — the width is not a
measurement and is not quoted.

## 3. ★★★ The occupancy result is WITHDRAWN and replaced by a screen that can fire

`freqocc_v405.py` (round 92), 52 macros, reading `occupancy_windows.csv` — a
frozen 9-column extract of the host's 3,027 per-window result files, copied into
the version directory with its provenance in the generator's header.

**The defect, in one sentence, as the paper now states it:** after the earlier
`[3]→[4]` index repair the module still keyed on the *product directory name*,
which for **2,529 of 3,027** records embeds the execution block, so a star's own
repeat observations counted as different targets and every persistent feature —
a real line most of all — entered as a cross-target coincidence.

| key | observed | grid null | z |
|---|--:|--:|--:|
| directory (`_B<n>_EB_<blk>`) — the withdrawn pass | 680 | 625.0 ± 12.8 | **4.28** |
| **star** (133 stars, not 749 directories) | **569** | **554.4 ± 13.3** | **1.09** |
| **star, peak > 5σ** | **4** | **5.2 ± 1.9** | **−0.60** |
| star, peak > 5σ, line-masked | 1 | 2.1 ± 1.3 | −0.80 |

**The corrected screen supports no interference claim** — which is what the
paper wants to say, now on a test that could have contradicted it. The generator
**reproduces the withdrawn z ≈ 4.3 first** and asserts both directions: the
directory key must give z > 3 *and* the star key |z| < 2, so "the whole of the
effect is the key" is machine-checked. **35 of the 109** significant windows sit
on a masked transition (CO(2–1) ×17, CO(1–0) ×10, CO(3–2) ×4, ¹³CO(2–1) ×3,
SiO(5–4) ×1) — a CO line lands at nearly the same *topocentric* frequency toward
every nearby star, so cross-star coincidence is exactly what real line emission
produces. Also withdrawn: the stored 2026-09-01 report's "0 coincidence
clusters over 144 windows", a separate indexing defect that made the module
incapable of reporting a coincidence at all.

★ **Found in the ported code**: `'%.2f' % 0.145` rounds *down* on the binary
representation, so the p would have printed 0.14 rather than 0.15 (fixed with a
half-up helper); the "2,294 coarse" figure was a binary fine/not-fine split that
swept in 5 medium and **9 rows with an empty resolution class** — the four
labels are now asserted to partition the 3,027, and those **9 unlabelled rows
are a defect in the host extract**; and `CAT_OLD` was a hard-coded literal,
now parsed out of `v342_calc.py` so it cannot drift from the search list.

★ Runtime was **8.9 s**, not the ~20 min estimated. Deliberately **not**
parallelised: keeping the single seeded stream in its original consumption order
is what makes every value bit-identical to the reviewed report, and Monte-Carlo
error on the null mean is ±0.67 — enough to flip `\RfiOccNull` 554 → 555.

## 4. The mask-width ladder, generated, in both frames (R1-7)

`ladder_v405.py` (round 93) + `tab_maskladder_v405.tex` + 34 macros. Falsifier
**F3** passes: the sky column reproduces R1-7's published **11/10/3/2/2** exactly
on the population R1-7 quoted, and the H2CO repair is asserted to change **no
cell**, so the ladder may honestly be quoted over all 56.

| half-width | sky attr/unattr/rank-fl. | stellar attr/unattr/rank-fl. |
|---|---|---|
| ±13 | 1 / 52 / **11** | 13 / 31 / **3** |
| ±20 | 3 / 50 / **10** | 14 / 30 / **2** |
| ±30 | 12 / 41 / **3** | 14 / 30 / **2** |
| **±50 (adopted)** | **16 / 37 / 2** | **14 / 30 / 2** |
| ±100 | 16 / 37 / **2** | 14 / 30 / **2** |

★★ **The answer to the post-hoc-tuning charge is a set identity, not a count**,
and it is asserted: `setof(50) == setof(100)` is True in **both** frames, and
the surviving pair is the **same pair** in both — 61 Vir `Xc079b5_X82f` and
CP−72 2713 `Xff0235_X4a6d`. The tube can be doubled, in either frame, and
nothing new appears. That is stronger than the sensitivity table R1-7 asked for.

★ **R1-7's premise is printed rather than papered over**: widening ±13 → ±50
costs **9 of 11** in the sky frame against **1 of 3** in the stellar frame, and
the generator asserts `lost_sky > lost_stel`. The wider tolerance is *not* free;
what it removes is the survey's own identified CO. Denominators are macros:
56 crossings / 53 sky-evaluable as released / 44 stellar-evaluable / 16
attributed at ±50 sky / 10 rank-screened / 12 stage-1 rows with a string.

The stellar column needs a per-(block, window) barycentric term, which cannot be
recomputed from the released catalogue; it is frozen as
`r8inputs/bary_v405.json` with a `_provenance` string and is used for **nothing
the survey published** — the search ran topocentrically.

**Two more "stellar frame" passages corrected**: §3's mask description and step
11 of the pipeline table. v4.04 fixed two; these were the remaining two.

## 5. The three corrections v4.04 called out of scope

### 5a ★ `\NExoHostsTab` 19 → **23**, `\NExoPlanetsTab` 42 → **50** (not 22/49)

Fixed at `make_tables_v328.py`. `is_exo_host` is a property of **how a star
entered the census**, not of the star: `build_ranked_master40pc.py` writes it
only for entries admitted through the exoplanet route, so **139 of the 168**
census rows carry it blank, and `make_tables` counted every blank as a non-host.
19 was a lower bound, not a count. **Fourth instance of the hard-coded-prose
bug family.** Replaced by a positional join, with the flag-based count computed
first and **asserted to reproduce the shipped 19 / 42** before any correction.

★★ **The measurement disagrees with `SMALL_FACTS.md`'s 22 / 49, and the
disagreement is reported rather than reconciled.** That pass's star list missed
one searched star. Mine is the paper's own join — the one that reproduces 19/42
— and it finds **four** additions, not three: BD+05 1668 = GJ 273 (2 planets),
Barnard's Star (4), HD 33793 = Kapteyn's Star (1), **and LP 736-15**
(`j1256-1257`, 8 searched windows), which sits **5.7″** from the archive host
VHS J125601.92−125723.9.

Both counts are published, on **one mechanical criterion applied to every match
alike** — the deuterium-burning limit, 13 M_Jup:

| | hosts | planets |
|---|--:|--:|
| shipped, flag-based | 19 | 42 |
| **positional, archive definition (published)** | **23** | **50** |
| positional, companions below 13 M_Jup only | 21 | 48 |

★ **The strict criterion SUBTRACTS as well as adds**, and that is the finding:
**HR 2562 b (~30 M_Jup) was already inside the published 19.** So the "22/49"
figure is not reachable by any uniform rule — it is 19 + 3 with one match
dropped by hand. Robustness: 23 for any radius from 60″ to 300″; all matches but
GJ 273's lie within 6″, and GJ 273's 59.8″ is its 3.7″ yr⁻¹ proper motion — so a
join filtering on distance agreement throws away exactly the nearest and
fastest-moving addition. **0** flagged hosts fail to find a counterpart
(asserted).

### 5b `\HostNMult` 1 → **0** (R2-m10), on a fresh SIMBAD query

`hosts_v399.py` tested membership of SIMBAD's **aggregated `otypes` bag**, which
accumulates every type any catalogue row for an object has ever carried. 61 Vir's
bag holds `**` only because the star is component A of WDS J13184−1819,
CCDM J13185−1818, BDS 6447 and IDS 13132−1745 — line-of-sight optical pairs.
Re-queried live (`--requery`, 2026-09-26): **`basic.otype` = `PM*`, 0 parents,
0 siblings, 3 children all `Pl`.** The frozen file stored neither the principal
type nor the hierarchy, which is why the defect survived; it now stores both, and
the build **fails** if it finds a file that predates the fix. Table 22 prints the
actual SIMBAD type, as R2 asked, instead of a summary word.

★★ **h_link's parents are NOT all binaries, and the naive fix was wrong.**
CPD−72 2713 has **11** parents, every one an `MGr` moving group, and one of them
has **3,340** members. Counting those as multiplicity would have replaced one
wrong answer with another — `\HostNMult` would still have come out 1, with a
*different* star. Only parents whose own principal type is a stellar multiple are
kept, and the discarded parent types are stored rather than dropped. The build
asserts the corrected count differs from the bag count **and** that it can only
decrease, so a fix that did nothing would fail.

### 5c Appendix B: the ×26 is wrong as well as mislabelled (R2-m11)

`occurrence_v399.py`, falsifier first: it reproduces the shipped
`\OccNuRelSurvey` = 0.097, `\OccNuRelSys` = 0.0037 and the ×26 (25.94) before
criticising them. Two defects:

1. Substituting a per-system ν_rel into Eq. 11 while holding N⋆ = 60 makes
   N⋆ν_rel count **neither** the survey's opportunities (heterogeneous) **nor**
   one system's (which needs N⋆ = 1). The referee is right: it is an
   **illustrative rescaling**, now labelled as one by a macro.
2. `nurel_sys = dnu_sys / nu_mid` divides **one system's** union by the
   **survey's** midpoint. Against each system's own midpoint the median is
   **0.0076**, about twice the shipped 0.0037.

The defensible figure needs no substitution — the star-bandwidth product itself,
Σᵢν_rel,i, which reduces to Eq. 11 under uniform coverage (new Eq. 
`eq:cwtfmhet`):

| quantity | value |
|---|--:|
| N⋆ν_rel, literature convention | 5.80 |
| **Σᵢν_rel,i, measured** | **0.628** |
| the convention's over-credit | **×9.2**, not ×26 |
| equivalent uniformly-covered systems | **6.5**, not 60 |
| **CWTFM at the median P₉₀^sel** | **2.3×10⁵** |
| CWTFM at the worst-case system | 5.5×10⁶ |

★ **×26 overstates the penalty** because it charges the median system's narrow
coverage to all 60; the sum charges each system its own. Conclusion unchanged:
some four orders of magnitude behind cm-wave SETI. Three asserts:
`starband_uniform > starband_sum` (the over-credit must run that way, and a
reversal would be physically impossible), the two per-system ν_rel definitions
must **differ** (or defect 2 was fixed elsewhere and this block is claiming a
repair it did not make), and no system's own fractional bandwidth may exceed the
survey's.

## 6. η_drift narrowed, not deleted (R2-m2)

`etadrift_v405.py` (round 94), 22 macros. **13 of 403** Class A windows
(3.2 per cent) have η_drift < 1, so the class-wide claim goes — but **0 of 12**
stage-1 flagged windows and **0 of 52** Class A threshold crossings are among
them, so Appendix J.3's sentence is **true as written** and is narrowed to the
population it can support, with a range attached:
η_drift = **6.9–422, median 20** over the 12. Symmetrically, **38 of 1,252**
Class B windows reach η_drift ≥ 1 (max 1.35). The classes are defined on native
channel width, which is the right thing to define them on; η_drift is a derived
property that crosses the boundary **both ways**, and the text now says so
symmetrically.

The 13 are a **track-length** effect, not a class-boundary one: every one is a
**60–181 s** on-source track against a Class A median of **2,389 s**, at the
coarsest fine channel widths (**488–977 kHz**). Asserted, so the explanation in
the text is checked: the low-η_drift windows must sit at the coarse end of the
class, and their longest track must be shorter than the class median.

★ **The report said "7 independent blocks"; it is 8** (`Xb25e1a_Xed74` carries
three stars sharing a field, and ALMA J1537−3319 contributes three blocks). The
macro is generated, so the paper says 8.

## 7. τ Ceti (D9a) — nothing added, deliberately

D9a permits one sentence "if it belongs anywhere at all". It does not: the
manuscript mentions τ Ceti only as a sample member in the exoplanet-host list
and in a calibration-reproducibility aside, and it **never** contains the
overstated "unexplained central excess, T_B ≈ 5800 K" claim. Nothing to correct,
so nothing was written. **For the record, binding on any future draft:**
MacGregor et al. (2016) say *"marginally higher"* — 0.69 against 0.60 mJy with a
5 per cent scale uncertainty, ≈1.7σ — and attribute it to a **hot chromosphere**.

## 8. New gate: `selftest_v405.py`

**60 cases, 60 demonstrated failing, 0 not demonstrated.** Every assertion added
in this cycle is driven, one at a time, with `cwd` at the version directory (so
reads resolve) and every write redirected through a shim on `builtins.open` —
a symlink farm would truncate the real products, because `open(p, 'w')` follows
a symlink. The released catalogue's checksum was verified unchanged after each
run. A perturbation that raises anything **other than** `AssertionError` is
reported as NOT DEMONSTRATED: it broke the generator rather than tripping its
check, and is no evidence the check works.

It earned its place immediately — see §1.3.

## 9. Two products added to `cleanregen.py`

`per_target_results_v3.99.csv` is now in the product set. It is the product the
largest number of other generators read — **five of this cycle's six** — and it
now carries the computed disposition columns, so a generator silently reading a
previous run's copy would report the previous build's attributions. Same
reasoning as the v4.03 ledger lesson, one level further up the dependency chain.
Also added: `tab_dispo_v405.tex`, `tab_maskladder_v405.tex`, `appm_v405.json`,
`freqocc_v405.json`.

## 10. Gates

| gate | result |
|---|---|
| pdflatex errors | **0** |
| undefined references / citations | **0** |
| multiply-defined labels | **0** |
| Overfull boxes | **0** |
| Type-3 fonts | **0** |
| `roundcollide.py` | **84 round files, 84 inputs, 0 problems** |
| `macrosyn.py` | **0 problems** (11 groups, 6 relations, 90 macro files, 9 deferred) |
| `consistency_v399.py` | **0 problems** |
| `prosenum_v399.py` | **0 literals disagreeing with a macro** |
| `macroleak.py` | **0 problems** |
| `intsweep.py` | **82 integers, 82 registered, 0 problems** |
| `audit_numbers_v385.py` | **49 PASS / 0 FAIL** (10 WARN, 7 SKIP) |
| `reproduce_from_catalogue_v385.py` | **22 pass / 0 FAIL**, 19 skipped |
| `selftest_v403.py` | 26 checks, **20 demonstrated failing, 0 undemonstrated** |
| `selftest_v404.py` | **46 cases, 46 demonstrated failing** |
| **`selftest_v405.py`** (new) | **60 cases, 60 demonstrated failing, 0 NOT demonstrated** |
| `xrefcheck.py` | 125 labels, 0 misplaced |
| **`cleanregen.py`** | **127/127 byte-identical** |

**Page split:** 48 pages — main text **17.72 pp**, back matter 0.06,
appendices 29.42, bibliography 0.28. By the `\label`-anchored count the appendix
starts on p. 19, so **main 18 pp / appendix 30 pp**.

**Abstract:** 1743 rendered characters, 276 words (arXiv limit 1920). Untouched.

Underfull boxes 60, unchanged in kind. Not a gate.

★ **Three gate catches worth recording.** `intsweep` — the gate v4.04 added —
immediately flagged **156 MHz** as an ungenerated quantity in the new Appendix M
prose; it is now `\AppMWideMHz`, emitted from the width the power curve was
actually measured at, so the sentence cannot name a width the curve does not
cover. The Type-3 gate caught the new figure missing
`pdf.fonttype = 42`, which every other figure generator here sets. And the
overfull gate forced both new tables to be **measured** with `\savebox` and
`\the\wd` rather than guessed: `tab_dispo_v405` is **397 pt** at `\footnotesize`
and still **373 pt** at `\scriptsize` against a **245.3 pt** column, so it takes
the full text measure as a `table*`; `tab_maskladder_v405` is **267.7 pt** at
normal size, so it is `\footnotesize` in a single column.

## 11. Every macro value that moved

Five, and no more — checked mechanically across all 90 macro files:

| macro | v4.04 | v4.05 |
|---|--:|--:|
| `\NCatCols` | 51 | **53** |
| `\NExoHostsTab` | 19 | **23** |
| `\NExoPlanetsTab` | 42 | **50** |
| `\HostNMult` | 1 | **0** |
| `\HostQueried` | 2026 September 22 | **2026 September 26** |

★ **0 of the 24 macros in the $P_{90}$/selection family changed.**

## 12. NOT IN THIS VERSION

- ★★★ **D14: $P^{\rm sel}_{90}$ redefined through trigger → visibility
  localisation.** A sibling owns this with the round-7 P90 campaign (46 of 56
  when last checked). Every $P_{90}$ macro here is untouched, verified in §11.
  Nothing written in v4.05 contradicts it: the rank screen is described only as
  a prioritisation screen and as the gate that *was* applied, never as the
  measurement path for completeness. **R1-4, R1-5, R2-3 and R2-5 all still wait
  on it.**
  ★★ **And so does the false-alarm control.** D14 notes that if the rank gate is
  not a filter, the chance expectation must be conditioned on trigger +
  localisation + attribution rather than trigger + rank. The 0.89 figure is
  conditioned on trigger **and rank** and is carried here unchanged — it must be
  **re-derived, not re-labelled**, when D14 lands. `\ClustStageMean` vs
  `\PriMean` remains a `macrosyn` DEFERRED entry.
- **D15: the stellar-frame multi-epoch stacked search.** Authorised and running;
  nothing in the manuscript yet, correctly.
- **R1-11 and R2-10's 25-page target.** Deferred by Glenn's directive. Main text
  grew 1.1 pp this cycle.
- **R2-10's appendix lettering**, and the deletions of the radius-corrected and
  detrended statistics and of Table 24. They interact with Appendices C and K,
  which R2-6 is also rewriting.
- **R2-6.** The catalogue column recording each window's control-annulus
  geometry, and the reconciliation of N_eff ≈ 30–43 against medians 229 (12 m)
  and 13 (ACA).
- **R1-8.** Single-epoch detectability and confirmation completeness as two
  explicitly different quantities.
- **The 51st visibility fit.** β Pic `Xd9668b_X3a90` and the CP−72 2713 refit.
  The ledger's fit input is a **glob**, so both are a re-run rather than an
  edit; the paper still says 50 fitted / 6 untested.
- **The closure-phase RFI record.** `rfi_ledger_r7.json` exists and is still not
  wired into a generator.
- **`visfit_v385_calc.py` and `visgain_v399.py`** are still not retired; five
  `macrosyn` DEFERRED entries name them.
- **R2-m12.** The Zenodo DOI is an author action (Glenn's account).
- **§6.5's habitable-zone list is still hard-coded prose.** v4.04 corrected the
  count five → six because BD+05 1668 forced it, but the list itself is not
  generated and will drift again. It wants a positional join of the planet table
  to the searched-star list with a citable habitable-zone flag per planet.

## 13. Noticed, out of scope, not changed

- ★★ **`build_ranked_master40pc.py` still writes a blank `is_exo_host`.** The
  repair in this version is downstream, in `make_tables_v328.py`. The builder
  itself should **assert that no census entry leaves with an empty flag**;
  otherwise the next consumer of that file repeats the bug for the fifth time.
- ★ **9 of the 3,027 rows in the occupancy host extract carry an empty
  resolution class**, and 5 are labelled `medium`. Neither is a paper number,
  but the extract's class column is not the binary fine/coarse split the rest of
  the pipeline assumes.
- ★ **`\CampUnOneT` remains a pre-repair record.** Flagged at v4.04, still true:
  the external calibration sample was scored before the ACA control-annulus
  repair, so its measured tail rate is a pre-repair rate and is usable only as
  an upper bound. The appendix says so; the number has not been re-measured.
- `tab_visibility_v384.tex` and `v385` still write `HD14055` rather than the
  SIMBAD form; `audit_numbers` warns twice.
- Eight figures are built and never `\includegraphics`'d.
- `sec:acalimit` is a label with no reference; 22 labels are defined and never
  referenced (a report, not a gate). `eq:cwtfmhet` is among them — the new
  equation is referred to by name in the prose but not by `\ref`.
- The version folder still carries `.aux`/`.log`/`.out`/`.pdf` from v3.87–v3.90
  and superseded `apply_v3xx_stage*.py`. The deposit is larger than the paper.
- **Disk**: `/workspace` sat at 99 per cent full (3.1–3.4 GB free) throughout.
  v4.02 was deleted after verifying its 568 files on the remote; `cleanregen.py`
  needs no copy, so it ran. A campaign of any size would not fit.

## 14. Frozen inputs added

| file | what it is |
|---|---|
| `r8inputs/bary_v405.json` | per-(block, window) barycentric correction, km s⁻¹, 1,602 entries, measured on the host during the round-8 line campaign. Used **only** for the stellar-frame column of the mask-width ladder; nothing published depends on it. |
| `occupancy_windows.csv` | 9-column extract of the host's 3,027 per-window result files: directory, window edges, channel count, peak frequency, peak SNR, resolution class. No re-processing, no fetch. |
