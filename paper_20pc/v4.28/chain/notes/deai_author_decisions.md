# `deai_author_decisions.md` — what the DEAI pass could not decide

`deai-close`, 2026-10-20, consolidating the cycle-1 file of 21:15 UTC with cycle 2's items. §M is
binding: **science and statistics findings are never resolved by rewriting the sentence.** They are
here, or in [`deai_referee_report.md`](deai_referee_report.md), and they wait for the author.

Each item: what was found, what (if anything) the pass did, and the decision that is the author's.

---

## 1. CLOSED BY MEASUREMENT — the pass's own offer was unnecessary, and says so

### 1.1 `flux` → `flux density`
Offered in cycle 1: *one defining sentence in §4*, or *22 located changes*. **Neither was needed.**
Of the 22 bare uses, 14 had an mJy referent and were corrected; the remaining **10 were re-measured
by me and 7 are genuinely bare** — and every one is an **integrated** flux in W m⁻², the quantity
§2 itself defines in situ as $F_{\rm min}=S_{\rm min}\,\delta\nu$ (the other 3 are `flux-density`
and `flux-scale`, which my first regex missed over the hyphen). Two further uses are field-standard
names (*ALMA's flux transfer*, *a window's trigger flux*) and one is a power fraction whose next
clause says *total power*.
**Action taken: none, deliberately.** The convention is stated where it is used.
**Author decision: confirm that is right**, since it is §3.6 physics wording and not style. If you
want the defining sentence anyway, it is one line in §4 and costs ~15 words of the page budget.

### 1.2 The main-finding sentence
Ruling 20 resolved the §3.1 annotation in the blind reader's favour. The sentence now of record is
in `deai_audit_report.md` §7. **Author decision: none required**, but it is the sentence a referee
will be told the paper makes, so it is worth reading once aloud (T-13).

---

## 2. TAKEN BY THE COORDINATOR, RECORDED HERE BECAUSE THEY TOUCH A CLAIM

### 2.1 The categorical limit (Ruling 21) — **a lowering that was reversed**
Cycle 1 removed a hard-zero pseudo-cleft and, with it, turned *"What limits the search is coverage,
not depth"* into *"Coverage limits this search more than depth does"* — categorical to comparative.
Under §3.4 a lowering must be approved, and this one understated our own result: for the
`\ZcNoRepSys` systems with no repeat at a covered frequency, **no depth of observation whatever
could have produced a confirmation**. Cycle 2 restores the categorical form in both places without
restoring either banned construction (`deai_audit_report.md` §5).
**Author decision: read the Abstract's new last two sentences.** They cost one word of the 245 and
they carry the paper's headline qualifier.

### 2.2 The Abstract absorbed the change by merging a sentence
To stay inside the ceiling, *"Confirmation needs a repeat at a covered frequency, which 21 systems
lack"* was folded into the final sentence, which now carries the same count in the same words. No
proposition was lost; one was moved from the methods half of the paragraph to its conclusion.
**Author decision: confirm the move is what you want**, since it changes where a reader meets the
confirmability shortfall.

### 2.3 One stock frame deleted, two words
*"Taken together,"* opened a sentence in §5 that fired three separate protocol features at once and
was the only instance of each in the paper. The sentence's claim — *these two results identify the
dominant obstacle for millimetre technosignature searches, and it is not sensitivity* — is
untouched.
**Author decision: none expected.**

---

## 3. OPEN, AND ONLY THE AUTHOR CAN CLOSE THEM

### 3.1 ★ The top-level source filename, and the one place a referee string still prints
The package now ships as `ms.tex` with every internal version and round string removed from names,
`\input` lines, `\includegraphics` targets and body text — **proved, not asserted**, by A15 and by
A8's byte comparison. Two residues remain and neither is ours:
- **`openjournal.cls`** prints the journal's own footer, *"…making the reviewing process simpler
  for authors and **referees** alike"*, and `epsf.sty`'s header says *Revision*. These are
  third-party files arXiv must receive verbatim. (The footer does not appear in the typeset text of
  this build; the string is in the class source, which arXiv serves.)
- **the figure PDFs** carry matplotlib's own `Creator`/`Producer` strings (`Matplotlib v3.10.9`).
**Author decision: accept both, or say so and they will be removed** — the class footer can only go
by editing the journal's class, and the figure metadata only by post-processing eleven PDFs, both
of which cost more than they are worth and neither of which is a statement about this paper.

### 3.2 Three macro values that named internal files
`\VisSource` = `vistest_v385.json`, `\CenLostCatalogue` = `per_target_results_v3.84.csv`,
`\CenLostVersion` = `3.99`. None is used by the manuscript; all three shipped in the arXiv source
until A15b pruned the dead macro layer (4 608 definitions, none of them expanded anywhere in the
package, removed with A8 byte-identity as the proof).
**Author decision: none needed for the submission.** But in the repository these three are the
record of which deposited file a number came from, and they are now invisible to anyone reading the
submitted source. If you want provenance in the paper, it belongs in the Data availability
statement, not in an unused macro.

### 3.3 One figure is not at a column or text width
`figures/coverage_waterfall.pdf` is included at `width=0.99\textwidth`; the other ten are
`\columnwidth` ×8 and `\textwidth` ×2. Pre-existing, untouched by either cycle, and strictly
outside *"figures at single- or double-column width"*.
**Author decision: leave at 0.99, or let it go to `\textwidth`** (which will reflow the page it
sits on and must be re-gated).

### 3.4 PDF metadata is clean but empty
Title, Subject, Keywords and Author are blank; Creator `LaTeX with hyperref`, Producer
`pdfTeX-1.40.22`, CreationDate pinned. LX-07 asks for metadata *clean and correct*; blank is clean
and not correct. Setting `pdftitle`/`pdfauthor` costs one rebuild and changes the PDF md5.
**Author decision: set them, or record that blank is intended.**

### 3.5 Pre-existing REVIEW items, unchanged by this pass
`MX-01` 37 macro names carrying two values; `RT-03` 15 acronyms used but never expanded (AC-01/B-34
wants 0); `RT-02` 146 stumble candidates; `audit_numbers` 13 WARNs, all the long-standing SIMBAD
naming in `tab_visibility_v384/385.tex` and `tab_nearest_r21.tex` (`HD14055` for `HD 14055`).
**Author decision: these are not language defects and the pass did not touch them.**

### 3.6 `CT-04`, knowingly overridden
*Spectral-Carrier* stands in the title, with the keep-reason that it is this paper's precise term
for the signal class it searches. Title otherwise clean: 14 words, no colon subtitle, no gerund, no
question, and the one acronym (ALMA) is a facility name.
**Author decision: confirm the override.**

### 3.7 One `itemize` inside `\section{Conclusions}`
§G of the protocol forbids a list environment in the Conclusions, and §I-7 bars restyling, so the
two rules point opposite ways and neither stage may act. The list is the eight-item structure the
readability pass wrote to the author's own instruction that the conclusions be "easy for a human to
see past the walls of statistical coverage", and it is the single change that instruction most
clearly produced: each item opens with what it is about (*What was found.*, *What the repeat
observations exclude.*) and the finding leads. Converting it back to running prose would undo that.
**Author decision: keep the list (recommended, with §G waived and the reason recorded), or convert
it to eight short paragraphs with the same lead-ins in italic.** No stage will act without his word.

### 3.8 What the protocol itself could not run here
`SR-1…SR-4` (four simulated referees) are **NOT-RUN under §Q**: §RV-04 wants a different model
family for judging tasks and this installation has one, and four personas of one model are not four
referees. The false-positive calibration corpus and the three validation experiments are likewise
NOT-RUN — the protocol's own principal outstanding validation debt. **This is why three of the four
detectors behind C-01 have no threshold here** (`deai_audit_report.md` §3), and it is the single
largest limitation on what any number in this pass means.
**Author decision: none available locally.** If a second model family is ever reachable, the
judging tasks should be re-run there first.
