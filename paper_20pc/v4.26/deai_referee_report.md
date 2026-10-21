# `deai_referee_report.md` — §M findings on v4.25 (editing ≠ refereeing)

`deai-canon`, 2026-10-19. **Staged here, not in `v4.25/`**, because this stage owns only
`deai_battery.md` and `deai_audit_report.md` in that tree; move it in when the tree's owner says so.

Addendum **§M** is the whole point of this file: statistical, provenance and reproducibility
findings, and anything about the science itself, **are never resolved by rewriting the sentence**.
Each item below names the measurement, the clause it answers to, and what it would take to close it.
No item here is an instruction to the reviser.

---

## 1. `flux` where `flux density` is meant — 22 uses, severity 2 (§3.6)

**Measured** (`work/canon425/canon_sweeps.log`, census over the macro-resolved prose): **22** bare
uses of `flux` against **4** of `flux density`; every quantity involved is monochromatic and carried
in mJy — `a flux threshold`, `received flux`, `the flux limit`, `apparent flux` / `true flux`,
`inferred flux`, `at the discovery flux`. `Jy beam⁻¹` does not appear; `mJy` appears 4 times.

The §3.6 detector fired on exactly one sentence, because only there does the word share a sentence
with its value:

> *"…against the \<MATH\> that real carbon monoxide at the discovery **flux** would have given — a
> disagreement of 2.1 \<MATH\> once the window's noise is measured over the 47 minutes it integrates,
> at **11.5 mJy**, where its sibling blocks also lie."*

A quantity in Jy is a flux **density** (W m⁻² Hz⁻¹); `flux` is the integrated quantity (W m⁻²). The
distinction is the first one §3.6 names, and it sits directly in the EIRP chain, which multiplies a
flux density by a bandwidth. Some of the 22 are defensible as written (a *received flux* integrated
over one channel), which is exactly why this is a referee-report item and not a find-and-replace.

**To close it** the author chooses one of: (a) a single sentence in §4 defining that "flux" is used
for flux density throughout, with units — cheapest and sufficient; or (b) 22 located changes. Either
is his call. **Not in the revision brief.**

## 2. `MX-01` — 37 macro names carrying two different values, severity 2

Unchanged from v4.24: **37** names are redefined to a *different* non-empty value somewhere across
the 185 macro files (the `\providecommand{}{}\renewcommand{}{v}` idiom is excluded from the count).
Several are deliberate round-to-round aliasings, which is why the row is REVIEW and not FAIL.

★ **`\CeAddLimNear` against `\FrNarrowAddLim` first**, because one keystroke separates them and the
build has already produced one wrong-key join this round (`r21_image.py:311`, the 14th, whose hiding
mechanism is now confirmed: `vbary` misses the window-low-edge key and falls through to a per-block
frozen value, returning a plausible number instead of failing).

**Reproducibility ladder: partial.** A name with two values is a single-source violation; nothing in
`macrosyn`, `consistency` or `audit_numbers` can see it, because each compares *values* against
sources, never *names* against each other. The instrument that found it is ours and it is a list,
not a gate.

**To close it**: each of the 37 is either (a) a deliberate alias, which should be declared in the
macro file with a one-line comment, or (b) a collision, which needs a rename and a rebuild. Neither
is a prose edit.

## 3. `r21_image.py:311` — still owned by nobody (carried, not new)

Recorded here because §M covers reproducibility: the one-line repair moves published
image-sideband numbers, so it needs an owner, a re-run and a re-audit. Ruling 17 already records
that it is not a push blocker because the two verdicts it touches were measured independently.
**No DEAI stage may touch it.**

## 4. Residual `audit_numbers` warnings (severity 4, carried)

`stratified_completeness.pdf` is built and never `\includegraphics`-ed — a dead output in the
release deposit; three stars in `tab_nearest_r21.tex` are written without the SIMBAD space
(`HD14055`, `HD170773`, and one more). Both are deposit-hygiene items, not prose.

## 5. What the before-pass can and cannot support (provenance, §M)

- **P1 measured / verified**: every printed number in the paper — `audit_numbers_v385.py` re-derives
  58 of them from catalogue, product list, harvest and control stores, 58 PASS / 0 FAIL.
- **P1 measured / in-principle reproducible**: the battery rows in `deai_battery.md`; the tools and
  inputs are on disk and the three-input comparison is published, so a fresh agent can re-derive
  every value.
- **NOT VERIFIABLE here, and reported as such rather than passed**: R-01 (ADS resolution of the 68
  entries — no token in this container; previously verified entry by entry, delta zero this round),
  OV-01/B-35 (text overlap: no cited full texts offline), FG-01 beyond what `audit_numbers` checks,
  ST-01/02/03 (facility, software and data-availability wording against current policy pages),
  SR-1…4 (four simulated referees: §RV-04 requires a **different model family**, and this
  installation has one — a `Subrun` would be the reviser judging itself).
- **The voice model is REPORT-ONLY by the addendum's own ruling**: §T-2.3 records S-01 FAILED for
  this profile (author holdouts 0.89 vs controls 1.20, tails touch). D = 1.067 on v4.25 against
  1.037 on v4.24 is a diagnostic, never a verdict, and **no sentence may be moved by it**. §R applies
  in full: the voice model measures style, not watermark presence or absence, and **no claim about a
  watermark appears anywhere in this pass**.

---

# ADDED BY THE REVISION STAGE (`deai-revise`, 2026-10-19) — findings it refused to fix by rewording

## 6. The deposit's own column glosses say `flux` where `flux density` is meant (severity 3)

§1's 22 prose uses were adjudicated and 14 corrected (see `v4.25/deai_change_log.md`, Batch 1).
Three **generators** carry the same wording into deposited products, and that is a reproducibility
artefact, not prose, so it is **not** touched here:

- `ledger_v410.py:1199` and `tolrecur_r21.py:1012` — the column description *"statistic a carrier
  persisting at the discovery flux would have produced"*, shipped as a column gloss;
- `recur_v411.py:261` — the same wording in a docstring that documents the deposited cell.

The quantity is $S$ in mJy in all three, so the gloss should read **flux density**. Changing a
deposited column description changes a deposited artefact: it needs an owner, a regeneration and a
re-audit, exactly as the §M rule says.

**And the paper no longer needs the defining sentence the author was offered.** Option (a) of
`deai_author_decisions.md` §3 was *one sentence in §4 stating that "flux" means flux density*. Once
the 14 misuses are corrected, every surviving bare `flux` in the paper is an **integrated** flux in
W\,m$^{-2}$ — the Mason comparison, the trigger flux, the carrier's power fraction — and §2 already
defines that quantity in situ as $F_{\rm min}=S_{\rm min}\,\delta\nu$. So the honest fix costs
**nothing in length**, which matters for a round whose instruction was to subtract. The decision
item becomes: *accept the 14 located corrections and the 10 keep-reasons, or require the sentence as
well.*

## 7. The manuscript filename carries a version string, and it ships to arXiv (severity 3, author's call)

The author's standing constraint is that **nothing anywhere** may mention versions, edits, referees,
rounds or corrections, and that the arXiv package ships the LaTeX source. The **PDF is clean**:
`v4.25` and even `4.25` occur **zero** times in its bytes, metadata included. But the top-level
source file is `technosignatures_40pc_v4.25.tex`, and arXiv lists source filenames publicly. That is
not prose, a caption, a table, a figure or a comment, so it is outside the letter of the constraint,
and it is **not** something a revision stage may change unilaterally: `gate.sh`, `arxivset.sh` and
`manuscript.main_file()` all **derive** the version from that filename by design (it is why a version
bump needs one edit instead of thirteen). **Author's call**: rename at packaging time only (a new
failure mode — the packaged stem would stop matching the tree), or accept it.

## 8. What the canonical instrument could not have told anyone, measured on this paper

These are findings about the **instrument**, for the author who wrote it, and they are the reason
three rows in the before-table could not simply be obeyed:

- **B-01 counts `---` only, and the honest ` -- ` count is itself inflated.** The paper's house dash
  is ` -- ` (177 in the sources). The scored prose shows **202**, because the preprocessor pads
  resolved maths and so turns **25 numeric ranges** (`114--873` and kin) into spaced dashes. A range
  is not em-dash punctuation. The row as written reads **0.00**; the honest figure is **5.2 per
  1,000**, of which **130 of 202 are matched parenthetical pairs**, i.e. ordinary punctuation.
- **B-14's regex requires a capital `What`.** It therefore cannot see the same construction
  mid-sentence: **19 lower-case instances** existed, 13 of them genuine pseudo-clefts (now unwound),
  6 ordinary indirect questions that must not be touched. A hard-zero row that sees only one
  capitalisation of its own target is a check that cannot fail in the way that matters.
- **B-17 counts dates.** Of its 6 hits, `2026-10-06` and `2026-10-15` are dates, not premodifier
  stacks; the honest count is 3 field-standard compounds against a threshold of 3.
- **B-31 has no notion of a run-in heading or of a legend code quoted in prose.** Of 165 body
  emphasis commands, ~60 are terms defined at first use, ~25 are table codes (`A`, `AR`, `U`, `open`,
  `edge`) and ~70 are italic run-in headings, this paper's navigation. **Six** were rhetorical and
  were removed. Reaching ≤ 1 per 1,000 would mean 34 commands in the whole paper.
- **`LX-01c`'s 676 comments are not ours.** Every `.tex` and every ancillary file in the package is
  **already comment-free** — `arxivset.sh` has stripped `.tex` comments since it was written, and
  check A8 proves the strip changes no output byte. The 676 are `epsf.sty` (372) and
  `openjournal.cls` (205), which are third-party files arXiv must receive verbatim, plus `%` lines
  inside **PDF binaries**, which are not text at all. **No packaging change was needed or made.**

---

# ADDED BY THE CLOSE STAGE (`deai-close`, 2026-10-20) — cycle 2

## 9. §1 and §6 are CLOSED by measurement, and §7 is closed by proof

- **§1 / §6 (`flux`)** — of the 22 bare uses, 14 carried an mJy referent and were corrected; the
  remaining 10 were re-measured in this cycle and **7 are genuinely bare, every one an integrated
  flux in W m⁻² that §2 defines in situ** (the other 3 read `flux-density` and `flux-scale` and
  were only ever a regex artefact of the hyphen). Two of the seven are field-standard names
  (*ALMA's flux transfer*, *a window's trigger flux*) and one is a power fraction whose next clause
  says *total power*. The defining sentence the coordinator had authorised was unnecessary and was
  not written. **Status: closed, action none, by measurement rather than by edit.**
- **§7 (the filename)** — closed in the packaging step, and the scope of the defect was 180× what
  this section reported. See item 10.

## 10. ★★★ The defect §7 named was one file; measured, it was 194 of 222 — and the PDF too

`deai_referee_report.md` §7 raised **the single top-level filename** and correctly called it the
author's call. Measured on the package this build actually produced:

- **194 of the 222 `.tex` carried a version or round string in their names**, 180 of them the
  literal word `round` (`survey_numbers_round8.tex` … `survey_numbers_round200.tex`);
- the top-level source carried **188 published lines** of the form
  `\input{survey_numbers_round23}`, which is source *text*, listed and served by arXiv;
- and the **PDF itself** carried `./figures/chain_v412.pdf` in a `/PTEX.FileName` entry, one of
  eleven embedded local build paths. **No text sweep in this build could see any of it**: `round`
  inside `round23` has no word boundary, and a PDF dictionary entry is not a text stream.

This is a *reproducibility-and-record* finding, not a prose one, which is why it is here: the fix
is in `arxivset.sh` (A15/A15b) and in two preamble primitives, and **none of it touches the
repository's own filenames**, which are the build's audit trail and must stay. Verification is A8's
byte comparison plus an independent sweep of the assembled package, both reported in
`deai_audit_report.md` §6 and `deai/CLOSE_REPORT.md`.

**Reproducibility ladder: verified.** `bash arxivset.sh --force` reproduces every claim above from
the tree.

## 11. Three macro VALUES named internal files, and nothing used them

`\VisSource` = `vistest_v385.json`, `\CenLostCatalogue` = `per_target_results_v3.84.csv`,
`\CenLostVersion` = `3.99` — defined in the macro layer, expanded nowhere in the manuscript, and
shipped to arXiv. They are the one place in the submitted source where a deposited file's version
was named, and they were named by accident rather than as provenance.

**Claim provenance: P1 (measured), but orphaned** — a value with no reader is not evidence of
anything. **Status: removed from the package by A15b's prune (4 608 dead definitions, A8
byte-identical after), kept in the repository.** If the author wants provenance for a deposited
file it belongs in the Data availability statement, where a reader can act on it. Author decision,
`deai_author_decisions.md` §3.2.

## 12. Three detectors without thresholds, and what that does to C-01

Not a defect in the paper; a limit on what this pass can assert about it, and it belongs in a
referee report rather than in a style table.

C-01, the protocol's own main rewrite trigger, counts windows where ≥3 feature IDs co-fire. In this
paper **133 of 186 such windows are the same triple: P-01 + P-06 + P-13**. Of those three, P-01 has
an absolute ceiling (max 1); **P-06 and P-13 are both defined as "> P90 of corpus", and the
false-positive calibration corpus is NOT-RUN under §Q** — as is S-02's per-section rate in
practice. So three of the four detectors producing this paper's headline style number have no
threshold in this installation.

Restricting P-06 to colons that introduce no number, symbol, citation or reference, and P-13 to
lists holding no measured item — which is P-13's own written clause — takes C-01 from **186 to 48**
and leaves the two cycles' movement (59 → 52 → 48) intact in direction and smaller in size.

**Reproducibility ladder: verified** (`deai/work/c2/census.py`, `clusters.py`, `lever.py`).
**NOT VERIFIABLE, and recorded as such**: whether 48 is high, low or normal for this author in this
journal. Nothing on this machine can say, and no gate here should be read as saying it.
