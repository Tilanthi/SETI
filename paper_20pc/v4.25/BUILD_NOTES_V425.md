# v4.25 — build notes

One self-contained PDF, **41 pp**, main text **21.85 pp** (cap 25),
`technosignatures_40pc_v4.25.tex`, `openjournal.cls`, built with
`SOURCE_DATE_EPOCH=1577836800`. Target **arXiv then OJA**: no supporting
information, five ancillary files beside the PDF.

Built from v4.24 by `cp -a`, with the base diffed file by file against the
pushed blobs first (1,289 of 1,289 byte-identical) rather than trusted; the
stale `technosignatures_40pc_v4.24.{pdf,aux,log,out}` were removed, and the
two leftover `…Notes.bib` revtex stubs with them. `gate.sh`, `manuscript.py`
and `cleanregen.py` take the stem from `ls technosignatures_*.tex`, so the
rename needs no script edit.

★ **The main-text page figure is `pagesplit.py`'s**, which measures the four
regions in points of column between the ACKNOWLEDGEMENTS, APPENDIX and
REFERENCES headings instead of counting whole pages. On the same tool the
previous build measures **23.95 pp**, so the fall is **−2.10 pp (−8.8 %)** with
the total unchanged at 41. A different convention gives 23.48 for that build;
both are defensible and the number is quoted with its method wherever it
appears.

★ **`secbudget.json` is no longer in the tree.** It is a measurement of one
built PDF, nothing in `make_all.sh` writes it, and the copy that shipped with
the previous build described a 38-page PDF beside a 41-page one. `budget.py`
now exits with the command to re-measure instead of reading a stale file.

## Verification of this build
`make_all.sh` rc 0 · **`gate.sh` three times rc 0, ALL GATES PASS, logs
byte-identical, PDF md5 `4dcb008f1938431749750bcc75bbc5cf`** (two runs
back-to-back and a third after the clean regeneration) · **`cleanregen`
280/280 byte-identical**, both passes rc 0 · `audit_numbers` **58 PASS / 0 FAIL
/ 13 WARN** · **0 overfull boxes, 0 errors, 0 undefined control sequences, 0
unresolved references, 0 multiply-defined labels** · `arxivset --force` **A8
byte-identical**, **240 items** (222 tex + cls + sty + 11 figures + 5
ancillary), 520 kB tarball, 0 Type 3 fonts, A9 240/240, A2–A6 and A10–A13 pass
· `absreq_r17` **7/7, and all ten drives fail as they must** · `prose_v412`
**all 17 drives fail as they must** · `abswords` **243 words** (ceiling 245,
unchanged) · `abschars` **1,562 characters** (arXiv 1,920, headroom 358) ·
`absmeta` **OK, the pasted block is the typeset abstract character for
character**, 1,564 characters / 244 words · `prosegate_selfref` **PASS, 0
hits, 0 stale pins** · `genai_sweep` **9 hits, 8 allowed, 0 unpinned, 0
stale**, selfdrives 1–3 all fail · `censusacct_r17` 6/6, drives 1–8 all fire ·
`counts_r15` A1–A14 pass · `prosegate_r15` 8/8 · `roundcollide` 179/179 ·
`orphanround` 179/179 cited, 0 orphan · `citegate` 68/68 · `verpin` 19 pins,
19 guarded, 0 FAIL · `valuetwin` 0 FAIL · `floatfit` **ALL CLAUSES PASS** ·
`tabfloor_r17`, `rotfit`, `twinmacro`, `synmacro`, `macrosyn`, `macroleak`,
`consistency_v399`, `prosenum`, `intsweep`, `fragstale`, `figorphan`,
`wordcase`, `minuscheck`, `labelcheck` all pass.

## What changed, and why

### The abstract, and the gate that held the sentence in place
The decorrelation sentence now reads *"These limits omit atmospheric
decorrelation, making them underestimates, and an opposing channel-response
term; which dominates varies by window."* The wording it replaces implied that
the two systematics generally cancel, which §5.1 contradicts.
★ **`absreq_r17` B5 required the replaced wording**, and its drive deleted
exactly that string to prove the check fires, so the abstract could not be
fixed without the build failing. B5 is rewritten as the **invariant** it exists
to protect — decorrelation named, the channel-response term named, the window
dependence stated in the same sentence, and no claim that the two cancel — with
a new drive 10 that restores the cancelling wording and fires. **A gate may pin
that a fact is stated; it may not pin the words that state it.**
Also in the abstract: the *"25 of 33"* qualifier is back as a pair of counts,
the median displacement dressed as a tolerance is replaced by the criterion
§5.5 actually applies (half a channel), the narrower-field reading is quoted,
and the single-epoch-trigger-against-confirmation distinction is restored.
Five clauses were spent to pay for it, each named in the file's own comment
with where it now lives.

### The field the statistic is read over is now defined where σ is defined
§4.1 defined σ as the MAD over the control positions and never said where they
lie, while Appendix D already argued that *"a statistic read over part of a
beam is not the quantity §4.1 defines"*. The annulus description moves from
§4.2's rank paragraph into §4.1 and §4.2 points at it, so the argument rests on
the definition rather than on a sentence the paper did not contain. Measured
true in all 1,663 catalogue rows.

### Both readings of the census are now on the page
31 against 24.6 at P = 0.13 over the whole primary beam, **35 against 24.1 at
P = 0.027** over a narrower field, with the reason the first is the adopted one
— a narrower field drops integrations, so it is not the statistic §4.1 defines
— in §5.3, in the conclusions and in Appendix D. The added-population bound is
quoted for each reading: 17 and **22**.

### The two image-coincident unattributed crossings are named
ALMA J153702653−33192492 at 218.8729 GHz and HD 161868 at 345.6338 GHz, with
the radius each image position is bounded within and the measured reason an
image coincidence does not meet the attribution standard: each parent was
observed at its own frequency in the same block, nothing there reaches the
trigger, and the largest amplitude is 1.37 and 0.93 times the crossing's own
against the ×10 a leak at the quoted rejection would need. **The census does
not move.**

### Readability, which is the round's main task
The conclusions lead with the finding and print the two deductions that take 34
unattributed crossings to the 31 compared against 24.6, which nothing pinned
before. Statistical machinery moves out of §5 into the appendices rather than
being deleted — the decorrelation detail, the resampling that establishes the
absence of a selection bias, the registration readings, the pair accounting —
and four passages that were verbatim duplicates of appendix text are gone.
**The figure-of-merit arithmetic becomes an appendix of its own**, keeping a
three-sentence summary in §6.2; it is the last appendix, so no appendix letter
moves. **Ten bold phrases in running prose are unemphasised**, reviewed one at
a time; the seven that remain in those sections are all caption lead-ins.
★ The `\clearpage` before the bibliography is **back**, as the note beside it
asks whenever the appendices change: flowed on, the one web source — four lines
of URL the list cannot break — set 7 pt from the paper's edge, with two
overfull `\vbox` in the log. Re-measured both ways: the paper is **41 pages
either way**, so the margin is bought for nothing. The reference list still
sets at the class default leading, measured on the page at 8.72 pt (3.075 mm),
the same as the build before it.

### Referee 1's two substantive items
**Completeness transferred across untested configurations**: the four systems
whose best window lies in a band or channelisation holding no injected window
were already named; what is added is that the published ×0.80–1.58 dispersion
is **not** an empirical bound for them, in §5.1, in Table F1's caption, and in
the deposited catalogue's own column description, where the same pair of
factors sits on all 405 Class A rows. A subtraction, not a new budget.
**Reproducibility**: the claim that *"the method is specified in enough detail
to be reimplemented, which is the stronger test in any case"* is replaced by
what was measured — the principal statistics rebuild from the released tables,
row by row, and whether the description suffices to implement the search afresh
has not been tested. The backmatter also now names the atmospheric factor in
the expectation recipe (without it the stated sum gives 25.79, not 24.6) and
says which crossing the atmospheric screen removes, which the ledger does not
mark.

### ★★★ The deposited `si_recur.txt` did not join the way its own header says
Its header documents a join on `(star, eb, nu_topo_GHz)`; **20 of 33 rows
resolved** it, because eight star spellings were raw export strings
(`HD14055`, `bet Pic`, three carrying a trailing Gaia DR3 designation). The
star column now goes through the house recipe `plain(designation(s))` —
`designation(s, tex=False)` alone is not enough, it leaves `$\beta$~Pic`
standing — and the file joins **33 of 33**. A driven assertion (**R16**, drive
16) holds it there, because `cleanregen` compares a file with its own
regeneration and a wrong-but-stable string passes that for ever.

### Gate changes, all demonstrated
- **`absreq_r17` B5** rewritten as an invariant; drives 8 and 9 re-pointed, new
  drive 10. 7/7 PASS, drives 1–10 all fail.
- **`gate.sh` now runs both front-matter gates' drives** — `absreq_r17 --drive
  1..10` and `prose_v412 --drive 1..17`, each required to exit non-zero.
  `prose_v412`'s drives **4, 10 and 12 were expired in the previous build**, so
  three clauses were asserted there and demonstrated nowhere; nothing ran them.
  Re-pointed, and now a round cannot close without the expiry being visible.
- **`censusacct_r17` A4** pinned the words *"Class B crossings are the whole of
  that search's crossing population"* — a clause that is true by construction,
  deleted this round for carrying nothing. A4 now requires the sentence that
  carries the flagged count to say the set comes from the one execution block
  that fails the data-quality criterion; new drive 8 prints the count with no
  description and fires.
- **`consistency_v399`** gains the clause that would have caught the
  conclusions attributing a coincidence "at the star's own velocity": wherever
  one sentence carries both an attribution and the star's velocity it must also
  carry the mask half-width or the word *interstellar*. Drive 1 re-injects the
  defect, drive 2 removes the mask's own definition so the clause cannot go
  vacuous; both fire.
- **`genai_sweep` was reading the running head as prose.** `page.get_text()`
  returns the page furniture with the body, so a sentence straddling a page
  break came out with the next page's running head spliced into it — *"the
  per-window **24 White & Dey** products"* — and its pin therefore carried a
  page number and the author list. The head is removed **by position** (one
  block in the top 60 pt of every page but the first; body text begins at
  y ≥ 64.8), verified byte-identical to `get_text()` on all 41 pages when
  nothing is stripped. The strip reports what it removed and **fails if it
  removes nothing**; new `--selfdrive 3` reads the furniture back in and fires.
- **`blockledger_v411.py`** prints Table A1's note d as *"16 of their 32
  windows"*. The referee asked for "blocks", which is arithmetically impossible
  against a row whose block count is 8 — `\ExNOffAxis` counts windows.
- **`synmacro` and `twinmacro`** carry declared reasons for the five new
  image-crossing A/B pairs: the suffix is two crossings, not two channelisation
  classes — the third such case in each file.

## Known and deliberately not closed
- `\AccelCeilMin` is **uncited** after the abstract's m s$^{-2}$ clause was
  spent. It is a **duplicate** — `\AccelCeilMed` = `\AccelCeilMin` = 3.60 and
  §4.2 still prints 3.60 — so no number left the page. It joins the existing
  retirement backlog rather than being cited for the sake of being cited.
- `retire_macros.py` retires nothing (3,983 macros survive only because a
  generator writes them); deferred by standing decision.
- The nine declared `macrosyn` divergences are unchanged, five of them owned by
  "retire `visfit_v385_calc.py`".
- `\CeAddLimNear` (15) and `\FrNarrowAddLim` (22) are different quantities with
  similar names — the near-trigger sensitivity test against the narrow-field
  reading. Neither sentence is wrong; the names are one keystroke apart.
- The only item in the arXiv set whose **name** carries a version is the
  manuscript file itself. Three tools derive the stem from it, so it is
  deliberate in the tree; renaming at upload costs nothing and is the
  submitting author's call.

---

## DEAI CYCLE 2 (`deai-close`, 2026-10-20) — final state of v4.25

**PDF md5 `b99f8cc90abae9794fdb6cc54a298e21`, 41 pp, main text 21.65 pp of 25, abstract 244 words
of 245 and 1 572 characters of arXiv's 1 920.**

Gates: `make_all.sh` rc=0 · `gate.sh` **ALL GATES PASS twice, logs byte-identical, same PDF md5** ·
`cleanregen` **280/280 byte-identical, both passes** · `arxivset.sh --force` **A8 byte-identical,
A9 PASS, A1 222/0, A2–A6 and A10–A15 PASS** · `absreq_r17` 7/0 · `audit_numbers_v385` 58 PASS /
0 FAIL / 13 WARN · `latexlog` 0/0/0/0/0 overfull.

21 prose patches and two preamble primitives. The prose work, the measurements and the keep-reasons
are in [`deai_change_log.md`](deai_change_log.md) (CYCLE 2),
[`deai_audit_report.md`](deai_audit_report.md) and [`deai_manifest.md`](deai_manifest.md) Part E.
The four things a later reader of **this** file needs:

1. ★★ **`\pdftrailerid` and `\pdfsuppressptexinfo=-1` are now in the manuscript preamble and they
   are load-bearing.** pdfTeX derives the PDF trailer `/ID` from an MD5 of the **output filename**,
   and writes `/PTEX.FileName` into the PDF for every included figure. Without the first, a build
   under a different `.tex` name differs in exactly 32 hex digits, so `arxivset`'s A8 byte proof and
   a version-free package filename cannot both hold. Without the second, the shipped PDF carries
   eleven local build paths — one of them `./figures/chain_v412.pdf`, which no `pdftotext` sweep can
   see. **Do not remove either without re-reading `arxivset.sh` A8/A15.**
2. ★★ **`arxivset.sh` now neutralises the package and nothing else.** A15 inlines the 188 preamble
   macro files into one `numbers.tex` (asserting their `\input` run is contiguous first), A15b
   prunes the 4 608 definitions the package never expands, 13 other `.tex` and one figure lose their
   version tokens, the manuscript becomes `ms.tex`, and A15 **fails the run** on any residue outside
   the journal's own class and style files. **222 source `.tex` → 35 package `.tex`, 53 items.**
   The repository's filenames are untouched and must stay untouched — they are the audit trail.
3. ★ **`ARXIV_UPLOAD.md` carries no measurement at all**, by design, and the new gate `arxivpin`
   (wired into `gate.sh` beside `absmeta`, 5 clauses all demonstrated firing) holds that property.
   If you add a number to that file the build will fail, and that is the point: it had shipped a
   stale md5, page count and abstract length five times.
4. ★ **`deai_battery.py`'s "Reconstruction notice" is now conditional.** It had asserted the
   canonical DEAI package was absent for two rounds after the package arrived.

Superseded cycle-1 deliverables are kept beside the new ones:
`deai_battery_before.md`, `deai_battery_cycle1.md`, `deai_audit_report_cycle1.md`.
