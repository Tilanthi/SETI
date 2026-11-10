# v4.21 — build notes (referee round 20)

One self-contained PDF, **37 pp**, `technosignatures_40pc_v4.21.tex`, `openjournal.cls`, built with
`pdflatex` three times, for **arXiv then the Open Journal of Astrophysics**. `SOURCE_DATE_EPOCH` is
pinned in `make_all.sh` and `gate.sh`.

★ **39 → 37 pages while the round adds content.** Referee 2 is a major revision whose every point is
about what we say our numbers are, so this round adds a column to three tables, a read-out on real
sources, a per-system decorrelation column and about twenty corrections — and the paper is two pages
shorter. The two pages come from the crossing ledger standing upright (it was a landscape float with
a page of its own) and from the sixteen appendix paragraphs no referee point names.
★★ **36 was the coordinator's target and it is one page away**: the plan's 36 assumed every caption
capped at the last sentence boundary before 900 characters, and that cut is **not available** — see
§"the caption cap" below. Nothing a referee asked for was deleted.

## What this round answers

| point | outcome |
|---|---|
| **R2-2** | **Nothing was simulated.** All 33 crossings were injected into real retained per-integration spectra, 362 windows, 482 of 482 block-roles. Two sentences of ours said the data were gone; they were the defect. Table B1 gains `n_rep` and its caption names the data |
| **R2-3** | **The predicted-cell chain is validated on real sources**: 13 of 13 recovered line crossings reach the trigger at the predicted cell, registration median 0.05 channel, and with the frame transform off only 5 of 13 survive. Table D2 gains `T_rep` and `Δc` |
| **R2-4** | The **integrated-response** retention replaces `sinc(πΔ/2)`: systems reaching 10¹⁵ W **25 → 26**, deepest limit **8.7 → 7.1 × 10¹³ W** (β Pic, not LP 876-10). Decorrelation is **not** applied and is tabulated per system in Table F1. The net bias is of **either sign** by window |
| **R2-5** | One criterion: **a different observing session AND more than one day**. The unconfirmable count **does not move (21)**; the confirmable frequency coverage does, **24.7 → 24.0 GHz (52 → 50 %)** |
| **R2-6** | One expectation, **25.8**; 27.0 is a labelled sensitivity test. Two numbers leave the paper |
| **R2-7** | ε Eri's two limits are two window sets in three blocks, named; the annual parallax is uncorrected on its census windows and bounded at ≤9 % |
| **R2-8** | **Not a bug**: HD 139084 B's +4.55 km/s is catalogued (Zúñiga-Fernández et al. 2021, now cited) and the sweep finds **one** agreement in **1 162** comparisons, the next closest at 0.13 |
| **R2-9 — R2-11, R1-2 — R1-7** | as filed; §6.1's "the strongest events" corrected to the two **weakest** attributed crossings |

## Verification of this build (2026-10-15, all times `date -u`)

| check | result |
|---|---|
| `make_all.sh` | **rc=0** ("generators OK"), 39 min |
| `cleanregen.py` | **236/236 byte-identical**, both `make_all.sh` passes rc=0 |
| `gate.sh`, run twice on the shipped tree | **ALL GATES PASS** both times; log md5 **`6827590402486eb158af779aad31acff`**, byte-identical |
| PDF | md5 **`c6f535421e6055d02173d15e62e363f3`**, unchanged by the second gate run |
| pages | **37** (main text 21.94, back matter 1.25, appendices 12.31, bibliography 1.25; measured content 36.74) |
| `audit_numbers_v385.py` | **58 PASS / 0 FAIL**, 10 warnings (all long-standing and named) |
| LaTeX log | 0 errors, 0 undefined control sequences, 0 unresolved refs/cites, 0 multiply defined, **0 overfull hbox, 0 overfull vbox**, 26 underfull |
| Type 3 fonts | **0** |
| `arxivset.sh` | **219 items** (204 tex + cls + sty + 11 figures + 2 ancillary), A1 204/204 resolved, A9 219 = 219, **A8 byte-identical**, A2-A6 and A10-A13 PASS, 496 kB tarball |
| `genai_sweep.py` | 9 hit lines over 23 families, every one ordinary English; `--drive` **23 of 23 families fire** |
| abstract | typeset **1870 characters / 294 words**; the plain-ASCII block in `OJA_SUBMISSION.md` is **1874 / 294** and is the typeset paragraph transliterated character for character (`absmeta` M1-M4). ►► **Not final: the abstract pass takes it to <=250 words and <=1600 characters** |
| `prosegate_selfref` | **PASS**, 0 hits, 7 allow entries, 0 stale |
| `floatfit_r18` / `rotfit_r18` | **PASS**; `rotfit` now asserts a DECLARED landscape-page count of **0** -- the crossing ledger stands upright from this version |
| `roundcollide` / `orphanround` | 164 round files, 164 inputs, **0 problems**; 0 orphan, 0 dangling |
| `valuetwin` | 2 same-quantity groups, **21 declared coincidences**, 0 FAIL |
| `selftest_v409` | **54 cases, 54 demonstrated** |

## Every published value that moved

Measured by comparing the two emitted macro layers, not by reading the prose: **32 values moved, 81
macros added, 12 retired** (v4.20 5 369 -> v4.21 5 438 definitions). The ones a reader will notice:

| macro | v4.20 | v4.21 | why |
|---|---|---|---|
| `\NSysEfifteen` | 25 | **26** | R2-4, the integrated-response retention |
| `\EirpNinetySysLoA`, `\EirpNinetyWinLoA`, `\SdMin`, `\CovEirpBest` | 8.7e13 | **7.1e13** | the deepest system becomes beta Pic, not LP 876-10 |
| `\SmcFacWorst` | 1.53 | **1.05** | the applied factor; `\NmSincFacWorst` = 1.53 is now the counterfactual |
| `\SmcNAbove` / `\SmcNAboveStar` | 13 / 6 | **9 / 4** | windows the sweep costs anything in |
| `\SmcLostStars` / `\SmcNLost` | HIP 10679 / 1 | **none / 0** | nothing drops out of the 10^15 W set now |
| `\CvConfGHzDay` / `\CvConfPctDay` | 24.7 / 52 | **24.0 / 50** | R2-5, the only published number the stricter criterion moves |
| `\ZcAddSupDayMHz` | 1.1 | **1.0** | the same |
| `\SfWDRatio` | 3.3 | **3.4** | R2-10(g), one rule in both columns of the degenerate row |
| `\BmEpsEirpBound` / `\BmEpsPenMax` | 1.8e14 / 1.57 | **1.7e14 / 1.45** | R2-7, through the retention |
| new | -- | `\FateCalDeliv` **159**, `\EtaDriftAOk` **391**, `\ZtHalfStepMed` **34**, `\RqHalfChanKHz` **244**, `\VsNComp` **1162**, `\NmNetConsPct` **7**, `\NmNetOptPct` **21**, `\NmNetOptMaxPct` **55**, `\BmEpsPxBoundPct` **9** | R2-10(b), R1-5, R2-9, R2-10(a), R2-8, R2-4, R2-7 |
| retired | `\QcConfAddCen(Word)`, `\NmRespFacWorst`, `\PxaMissingStar/Eb`, `\EvA/EvB` EIRP pair, `\LNLagOne` | -- | zero by construction; a second name for one quantity; `MISSING[0]` printed as the whole set; a caption restating its own table; a deleted paragraph |

**`\ZcNoRepSys` is 21, `\CeExp` is 25.8, `\CeAddLim` is 17 and `\RcNExcl` is 33, all unchanged** --
which is the point of R2-5 and R2-6: the criterion and the expectation are now the ones their own
rationales describe, and no count moved with them.

## The caption cap, measured on what the sentences ARE

`r20-length` measured that capping every caption at the last sentence boundary before 900 characters
removes 7 584 characters and buys two pages. **Applied to this paper it removes 228.** Every other
sentence it reaches is one of:
- a **legend** for a mark the table prints (`†`, `‡`, the dagger on Table F1's measured systems);
- a **colour or panel key** (`Orange, Enriquez 2017; aqua, Margot 2023`; `(a)`, `(b)`, `(c)`, `(d)`);
- a **column definition** (Table 5's `miss`, Table 6's chance row, Table D1's blanks);
- or a sentence **a referee asked for**, including seven this round added.
Deleting any of those is not a length cut but a content cut, and two of them would leave a printed
mark with nothing anywhere to define it. The one cut taken is Fig. 4's last two sentences, which
restate the two powers Table 6 prints beside them. **The stock is 228 characters, which is the same
answer `dupsent20.py` gives for repeated statements (234).**

## What is new in the build

**Three new generators**, each with its own assertions and drives, every drive demonstrated to fail
its own clause and nothing else:

| round | generator | what it owns |
|---|---|---|
| 910 | `confirm_r20.py` | what the second conjunct of the confirmation criterion costs: 31 same-session pairs over 15 systems rejected, 0 systems moved, 0.7 GHz of confirmable support lost (11 clauses, 11 drives) |
| 920 | `linerecur_r20.py` | the predicted-cell reading measured on the 13 real recurring lines and the 2 that are not recovered, and what each injected realisation was injected into (10 clauses, 9 drives) |
| 930 | `vsyssweep_r20.py` | every adopted systemic velocity against the barycentric correction of every block its star was observed in (5 clauses, 5 drives) |

★ **Three generators claimed round 910 in three queue files.** `confirm_r20.py` holds the recorded
claim; the other two were renumbered to 920 and 930 by the integrator. `roundcollide` resolves the
output filename from each generator's own `ROUND` constant, so it would have caught the collision
only after one had overwritten another's macro file — which is what happened at 840 one round ago.

`respint_r20.py` is a shared implementation and writes nothing (the `decor_r13.py` pattern);
`make_epsx_r20.py` is out-of-build (it needs astropy) and its frozen product is
`r20inputs/epsx_r20.json`.

## Six gates were repaired, and five of them had stopped being able to fail honestly

* ★★★★ **`absreq_r17.py` B5 required the abstract to call the limits optimistic** — the claim R2-1d
  withdraws. Restated: the limits must be said to exclude atmospheric decorrelation and **no
  direction** may be claimed for the net bias. Its drive 5 had gone vacuous for the second time in
  two rounds, keyed on a form of words; it is keyed on the word the clause requires now.
* ★★★★ **`confirm_r20.py` K9/K10 asserted the values the WITHDRAWN rule gave** (24.7 GHz, 52 per
  cent): they were written against a tree where `cover_v412.py` had not been re-run. Restated as
  *every published coverage macro is the one the adopted criterion gives*.
* ★★★ **`smear_r15.py` Q9 and `ledger_r14.py` L11** required the smearing correction to reduce the
  count at 10^15 W, an outcome written in as a requirement (`r20-corr`).
* ★★ **`rotfit_r18.py` R2** required at least one landscape page; the count is now declared (zero)
  and two-sided, and its drive inverted.
* ★★ **`selftest_v409.py`** expected two clauses to fail under `blockfate` drive 2 where three now
  do, and because its output goes to `/dev/null` the build died with an empty log.
* ★ **`beam_r17.py` §5b and `chance_v414.py` A17** could only run on a tree that had already been
  built: both read a macro layer that does not exist on a clean one. Both declared and deferred.
  **`cleanregen` is the only instrument that can see this, and it is the last one anyone runs.**

`make_all.sh` now carries an **`ERR` trap** naming the failing line and command: twelve gates in it
are redirected to `/dev/null`, so `set -e` on one of them used to leave no trace at all.

## Still open

- **the point-by-point referee letter** for round 20, which should be written against what ships;
- **the abstract**: ≤250 words and ≤1600 characters in the arXiv metadata form, a separate pass;
- **the page count**: 37 against the 30 the author has asked for twice. The measured content is
  36.74 pages; after the sixteen discretionary appendix paragraphs there is nothing left to delete
  that a referee point does not name. The two steps that would reach 33 are **the crossing ledger
  and Table A2 out of the printed article**, both still shipped as the ancillary files the
  submission list requires — Referee 2 recomputed Eq. B1 across the ledger, so that is an author's
  decision and not a builder's;
- ~~`\MkCancVSys` still prints **+4.5500**~~ — **CLOSED by `r20-blockers`, 2026-10-15**:
  `maskcost_v440.py` now formats it `%+.2f`, so the paper prints **+4.55** beside the 0.01 km/s
  uncertainty it quotes in the same sentence. The barycentric correction beside it keeps its four
  decimals (it is computed, not catalogued) and `\VsAgreeKms` is unchanged at 0.0339;
- 42 of the 56 `tab_*.tex` fragments in the tree are **orphans** that `arxivset.sh` still ships;
- the three unattempted blocks and the one infeasible one, each needing >246 GB (unchanged).

---

## r20-final, Thu Oct 15 17:59:11 UTC 2026 (`date -u`): **36 PAGES**, the ledger and Table A2 out of the typeset article, and the abstract inside both referees' limits

★★★★ **The author approved "the 33 page version". It does not exist by this route, and the
measurement that offered it was wrong by three pages.** Measured out of tree on this very build
(real copy, baseline reproducing 37 pp / 0 overfull): the crossing ledger and Table A2 are worth
**one page between them**, not four — 37 → **36** with an in-paper remnant of each, and **36 again
with both floats deleted outright, captions and all**. `LENGTH_PLAN_R20.md` §9's ladder costs the
pair at 36 → 35 → 33. The three further pages were never in these two tables; the only stock left
that would pay for them is the ≈20 000 characters of Appendices A–E and §5 that both referees'
reports instruct us to make *more* precise.

★★★★ **AND THE PAGE CAME FROM A FLOAT'S WIDTH, NOT FROM PROSE.** With the nine columns of r18's
sample the tabular is **298.0 pt** wide at `\scriptsize` against a column's **245.27**, so it can
only be set as a full-width `table*` — and a full-width float here costs a **whole page** (37
against 36, every other difference held fixed), because a `table*` can stand only at the top of a
page and the text it displaces does not pack back in. Dropping the **execution-block column** takes
it to **238.8 pt**, which fits a single column with 6.5 pt to spare; `line` instead leaves it 2.7 pt
too wide even with the inter-column gaps halved, and `\tiny` is refused by `tabfloor_r17`. The
block is the archive key rather than evidence about a crossing, and it is still in the ancillary
ledger for all \EvNCrossRaw{} rows, in Table 5 for the two leading events and in Table D2 for every
recovery. ★ `tighten`, five float placement options, gutting both captions and gutting Table A2's
notes each bought **nothing**: 37 pages every time.

### What the article prints now
- **Table D1 is a `table` (not a `table*`) carrying 9 computed rows of the ledger**: the 2
  unattributed crossings that lead their own control positions, the 4 the recurrence test cannot
  reach, then enough of the rest, in the full table's own order, that every one of the seven
  disposition codes appears. Four new assertions in `ledger_v410.py`, **each demonstrated firing**;
  the old "the sample is the first N rows, in order" assertion is replaced by a pair (the lead rows
  are the rank-leading set; every sample row is a row of the full table cell for cell), not dropped.
- **Table A2 keeps its 14 accounting rows** and sheds 6 itemisation rows. The rows are declared
  **once** in `counts_r15.py` with a printed flag, and the LaTeX table and the new ancillary file are
  written from that one list. New: **A12** (a printed continuation row must have its parent printed
  — row 3.1.1's label is written out in full because its parent moved to the file), **A13** (no
  printed note may point at a row the article does not print; row 2.2's note points at two),
  **A14** (the file carries every row with the value the article prints, resolved to plain text with
  no LaTeX left in it). Drives 16, 17, 18.
- **`si_counts.txt`** joins `arxivset.sh`'s `ANC_SRC` — 220 items now, 3 ancillary. ★ And
  `si_catalogue.txt` and `si_ledger.txt` **were outside `cleanregen` altogether**: the two files
  that ship beside the PDF were never proved rebuildable. All three are in its product list now
  (240/240 byte-identical).
- The caption of each says, in bold, that the full content accompanies the paper **as data rather
  than as part of the article**. ★ The **filenames are deliberately not in the LaTeX**: A13 fails the
  build on any ancillary basename that appears in the sources, on arXiv's own rule that a file the
  build references is part of the article.

### Two guards fired on a correct build and were adapted, not weakened
`census_r12`'s C7 and `gate.sh`'s `LEDGFRAG` both derive "the ledger" from what the manuscript
`\input`s. With the full table out, one asserted *"the manuscript inputs no ledger fragment"* and
the other would have handed `ledgergate` a 9-row sample to check against 56 crossings. Both now
exclude the sample by name and fall back to the full generated fragment — the file the ancillary
ledger is written from in the same loop — so C7 still reads 56 rows against 56 adopted crossings.

### The abstract
**1 519 characters / 246 words typeset; 1 525 / 246 in the pasted metadata block** (R1 ≤250 words,
R2 ≤250 words and ≤1 600 metadata characters, arXiv ≤1 920 with 395 to spare), from 1 870/294.
`abswords.py`'s ceiling is **310 → 250**: a gate that permits what the journal's referees refuse is
worse than none. R2's 1b–1f are all in: the opening literature claim deleted (it is made with both
citations in §1 and conclusion 1), no injection attributed to the median system's own window, no
direction claimed for the decorrelation bias, the recurrence tolerance as a **range with its
median**, and the **title now reads 90–873 GHz** — with §6.1 carrying the Class A union's own
114–873 GHz extent, which is also what keeps `valuetwin`'s declared \SurvFreqHi/\SurvFreqHiA pair
live (V3 refused a declaration that no longer described anything).
★ **Five drives had expired against their own sentences** — `prose_v412`'s 4, 10, 11 and
`absreq_r17`'s 4 — and `prose_v412`'s **drive 12 was already dead on the tree handed over**, so P10
had gone undemonstrated. All five are re-pointed at the clause each check requires rather than at
the wording that carries it, and all five fire.
★ **A11 caught a real conflation in my first draft** ("18 coincide with a catalogued transition":
18 are attributed, 21 coincide), and "trigger amplitude" stays in the paragraph only because B1
requires it — the clause defining a threshold crossing as *a channel reaching the trigger* is what
makes it readable.

### Hand-back
`make_all.sh` rc=0 · `cleanregen` **240/240 byte-identical**, both passes rc=0 · `gate.sh` twice
**ALL GATES PASS**, log md5 `a3acf9bf0d2b7419038c23c333114463` identical, PDF md5
`b379b0304780458e5e1c6606506fd44d` unchanged · **36 pages**, 0 errors, 0 undefined, 0 unresolved,
0 overfull hbox/vbox, 22 underfull · Type-3 **0** · `audit_numbers` **58 PASS / 0 FAIL** (10
long-standing warnings) · `arxivset --force` **220 items**, A1 204/204, **A8 byte-identical**, A13
PASS, A9 PASS · `genai_sweep` 9 ordinary-English hits over 23 families, **drives 23/23** ·
`absmeta` M1–M4 PASS, drives 1–5 all fire · `floatfit`/`rotfit` PASS (0 landscape pages) ·
`ledgergate` 56/56 · `valuetwin`/`synmacro`/`macrosyn` 0 FAIL · tree **1 214 files**
(= 1 213 + `si_counts.txt`). **Nothing pushed, nothing committed.**
★ `technosignatures_40pc_v4.21Notes.bib` is written by the class on every build and deleted again
here; it is a revtex control file, not a product.


---

## r20-blockers, Thu 15 Oct 2026 21:2x UTC (`date -u`): the ten blockers of `REFEREE_PASS_R20.md`, and **37 pages**

**Green, and nothing pushed.** `make_all.sh` rc=0 · `gate.sh` run twice from a deleted `.aux`,
**ALL GATES PASS** both times with **byte-identical logs** and PDF md5
`f5d4f0e47664d0aaba65fe8e2c0bbce2` · `cleanregen` **240/240 byte-identical** (two `make_all.sh`
passes on a deleted product tree) · `audit_numbers` **58 PASS / 0 FAIL** · **0 overfull boxes**,
Type-3 **0** · `arxivset --force` **A8 byte-identical** and **A13 PASS** with three ancillary files,
A1 204/0, A9 220 = 220 · `genai_sweep` 9 ordinary-English hits over 23 families, `--drive`
**23 of 23** · `absmeta` M1–M3 PASS · abstract **1519 characters / 246 words** typeset (arXiv 1920,
headroom 401; the pasted ASCII block 1525) · `citegate` 65 bibitems / 65 cited / 0 FAIL.

★★★★ **THE PAPER IS 37 PAGES AGAIN, AND THE PAGE WAS PAID FOR ON PURPOSE.** Appendix D.2 had lost
the definition of the **window-level quality flag** in this round's length pass while §5.4, §D.5 and
Table D1's `AF`/`UF` codes all still sent the reader there — and HD 48370 is withheld from the
amplitude tests on that rule, which is Referee 2's point 10(e). The definition is restored (one
paragraph, trimmed), and with §4's one-clause statement of the β Pic velocity exception it costs the
page the referee pass authorised paying. No measured content was deleted to buy it back; no float
placement recovers it (probed four ways, all 37 pp).

★★★★ **AND THE RESTORED PARAGRAPH EXPOSED A DEFECT NO GATE IN THIS TREE HAD EVER BEEN ABLE TO SEE:
INK IN THE MARGIN THAT IS NOT AN OVERFULL BOX.** With the REFERENCES heading 23 pt from the foot of
a column, the one web entry — four lines of URL the list cannot break any further — was set **37 pt
below the text block, 18 pt from the paper's edge**, and pdflatex reported **no overfull box at all**
because the bibliography is ragged-bottom. Only `floatfit_r18.py`'s ink measurement caught it.
`\clearpage` before `thebibliography` fixes it **at the same 37 pages**, so the old comment there
("a `\clearpage` would waste one") is no longer true at this length and now says so.
★★ The layout around it is a **float bifurcation**: with the restored paragraph and the default
`[tbp]`, Table D2 overran its page by 6.3 pt from one `.aux` and 19.6 pt from another, and
`tabfloor`'s probe/plain comparison disagreed by one rendered line depending on how warm its own
output directory was. Judge any layout measurement here **from a deleted `.aux`**, and expect the
page count to be insensitive while the overfull is not.

### What else changed, by item of the pass
- **B2** the smearing comparison printed "46 per cent **less**" where the generator defines the
  macro as an excess (`sens_r18.py:591`) and prints "per cent **more**": ×1.53 against ×1.05 is
  46 per cent more, and ×1.05 is 31 per cent less. Restructured, not word-swapped.
- **B3** the new radial-velocity clause asserted SIMBAD for every star; we adopt **+20 km/s** for
  β Pic (the gas value, `bpic_vsys.py`, SIMBAD gives 16.84). The exception is now named and cited
  (`Matra2017`) with its own blocks' agreement, and "zero where the catalogues give none" added.
- **B4** §5.6.1 pointed at a Table A2 row that this round's cut moved to the ancillary file.
- **B5**/**B9**/**B10** one clause each: the ledger sample's caption says **unattributed**
  rank-leaders; Table D2's caption now points at a flag the ledger file really carries; and the
  second expectation (`\CeExpSurv` 25.9, distinct from the adopted `\CeExp` 25.8) says which set
  it runs over.
- **B6**/**B7** the two orphaned openings left by the length pass are re-stitched ("Second," with no
  "First"; "the second reading" with no antecedent).
- **B8** **the two deposited files can now be joined on star.** `ledger_v410.py` writes the star
  column through `star_alias.designation(..., tex=False)` instead of the typeset string, so
  `$\beta$~Pic` is `beta Pic` and the two spellings of `HD 14055` are one: grouping the 56 rows by
  star now gives the **8** the paper prints. `si_r18.py` writes the catalogue's column the same way
  and keeps the export's own identifier as a new **`target_id`** column — the printable designation
  **merges 11 rows** of three bound pairs observed in one block, so the ROW key is the identifier
  and the JOIN key is the star. New clauses: **L14** (plain text, one spelling, agreeing with the
  de-TeX of the printed designation), **L15** (the unit-stamp flag, on the rows the page
  double-daggers), **S11** (no LaTeX in **all three** deposited files — in `si_r18.py` and not in
  `counts_r15.py`, which runs *before* the other two files are written and would have scanned a
  stale catalogue), **S12** (the join, with the one component the catalogue counts under its
  primary, and `\MtTopStarNCross` reproduced from the file). Drives 28–29 and 11–13, each
  demonstrated firing.
- **Improvements 1–4**: `\MkCancVSys` to two decimals; Table D2's dagger clause true of all three
  marked readings; the five block fates credited to Table A1, not A2; and the project-code caption
  pointing at the ledger **file** for the 33 crossings the printed sample omits.
- **Two source comments corrected, because the reason was wrong even though the outcome is right**:
  arXiv does **not** forbid naming an ancillary file in prose (it forbids TeX in `anc/` and pointers
  from the code, and lists the files by name on its own abstract page), so `arxivset`'s A13 is
  stricter than the rule it cites and the paragraph is defended on its merits instead.
- `OJA_SUBMISSION.md` regenerated against this build (it was quoting 1814 characters, 282 words, a
  310-word ceiling and 64 references against the live 1519 / 246 / 250 / 65).
