# The submission, checked — Open Journal of Astrophysics + arXiv

OJA is an **arXiv overlay**: the published article *is* the arXiv PDF, there is no typesetting and
**no copy-editing at all**, so arXiv's rules bind as hard as the journal's and the proofreading is
entirely ours. Every journal requirement below was re-read from OJA's own author page on
**2026-10-13** and is recorded with its source in
[`referee_r18/OJA_ARXIV_FACTS_R18.md`](../../referee_r18/OJA_ARXIV_FACTS_R18.md); the two that bind
hardest are the **mandatory generative-AI declaration with a validation account** and **CC-BY
selected on arXiv**. The journal sets **no abstract limit and no page limit of any kind**; the one
external limit on the abstract is arXiv's **1920 characters**.

★ The one thing in it that is gated rather than advisory is the **plain-ASCII abstract block** in §5:
`absmeta.py` fails the build unless that block is the typeset abstract transliterated, character for
character, and unless the counts quoted beside it are the measured ones; §5a's title and comments are
checked against the PDF the same way. Both are regenerated, never edited by hand.

Every number below was measured on the final build of `technosignatures_40pc_v4.29.tex`
(**2026-10-31**; PDF md5 `26c78598dc639ca23fc336fcd559204b`). They go stale the moment the paper moves: the tools are the
authority, and they are re-run with

```
bash arxivset.sh --force               # the submission set, checks A1-A13
python3 minuscheck.py                  # hyphen-for-minus, source and PDF (also in gate.sh)
python3 genai_sweep.py technosignatures_40pc_v4.29.pdf    # the GenAI-evidence sweep (also in gate.sh)
python3 abschars.py                    # arXiv's 1920 characters and Ruling R7's 1500, on the typeset page
python3 abstract_limit.py              # the same limit by the independent source route
python3 absmeta.py                     # the plain-ASCII block (§5) and the title/comments (§5a)
python3 abswords.py                    # the word count (Ruling R7: 180)
```

---

## ★ FOR GLENN — the six things only you can do

1. **Select CC-BY on arXiv.** OJA requires it. It is a radio button on the arXiv submission form,
   under *License*, and **it cannot be changed after announcement**. Choose
   `Creative Commons Attribution 4.0 (CC BY 4.0)`.
2. **Choose the primary archive class.** Recommended `astro-ph.IM` (Instrumentation and Methods),
   cross-listed to `astro-ph.EP` and `astro-ph.SR`. Yours to overrule.
3. **Read and approve the Generative-AI declaration.** It is in the Acknowledgements, under *Use of
   generative artificial intelligence* and *Testing and validation of that analysis*. OJA requires both
   halves and both are there. It is a statement about how your paper was made, published under your
   name, so it needs your word and not ours.
4. **Confirm the references.** OJA rejects any paper showing *"direct evidence of the use of GenAI,
   such as hallucinated references"*, and the declaration says every reference has been checked against
   the published literature. The list has **67 entries**, every one cited and every citation resolved
   (`citegate`: 67 bibitems, 67 cited keys, 0 FAIL) — but the sentence needs your signature.
5. **Mint the Zenodo record and replace the placeholder DOI.** The paper cites White & Dey (2026) with
   `doi:10.5281/zenodo.0000000`, all zeros by design (`AUTHOR_ACTIONS.md`). The record holds two files:
   the deposit `ALMA_Technosignatures_40pc.zip` (sha256 `46b656647dd02fb40c7bfe1d3aa9464f529e462312bd3621db2972cbf2612e80`, 495,432 bytes) and the
   crossing dynamic spectra `ALMA_Technosignatures_40pc_crossing_spectra.zip` (sha256 `3e4e036b15e7f77292e9a9abb37a23cc1c7a53329f885db9f0d69c9d8c30ac82`,
   168,638,048 bytes, 169 MB as the paper says). Replace the DOI in the Data Availability paragraph
   and in its `\bibitem` together. **The paper may not go to arXiv citing a DOI of ours that resolves to nothing.**
6. **Paste the abstract, title and comments into the arXiv metadata fields in plain ASCII.** arXiv
   rejects unicode there and caps the abstract at 1920 characters. The transliterated abstract is in §5
   and the title and comments in §5a; do not retype them (a copy from the PDF flattens `10^15` to `1015`
   and loses hyphens at line breaks). Ruling R7's limits — **at most 180 words and 1,500 characters** —
   are enforced on the typeset page, from the source and on the pasted block.

Everything else below is done.

---

## 1. Journal requirements (Open Journal of Astrophysics)

| # | Requirement | Status |
|---|---|---|
| 1.1 | Posted on arXiv first; the article is an overlay on the arXiv entry | **author action** — nothing to prepare beyond the set in §3 |
| 1.2 | `openjournal.cls` "preferred for the final version" | **MET.** We use it, byte-identical to the one the journal serves |
| 1.3 | No page, word or length limit of any kind | **n/a.** **21 pp**, one self-contained PDF, inside the author's ~25-page budget (2026-10-28) |
| 1.4 | Generative-AI declaration in the acknowledgments | **MET.** "Use of generative artificial intelligence", inside the Acknowledgements |
| 1.5 | An account of validation, if GenAI touched analysis | **MET.** "Testing and validation of that analysis": no number typed, clean regeneration compared byte for byte, assertions made to fail on purpose first |
| 1.6 | No "direct evidence of GenAI … prompts in the text" | **MET, measured.** See §2 |
| 1.7 | CC-BY | **author action 1** |
| 1.8 | Appendices inside the one PDF | **MET.** All appendices inline and lettered; the machine-readable tables also go to arXiv as **5 ancillary files** in `anc/` (`arxivset` A13) |
| 1.9 | Data publication in the spirit of Chen et al. 2022 | **MET once the DOI is minted (author action 5).** The ALMA Science Archive and the execution-block identifiers are the provenance; the deposit and the software are archived on Zenodo and cited |

## 2. "No direct evidence of GenAI" — swept, on the typeset page

`genai_sweep.py` (a gate in `gate.sh`) reads the **rendered PDF text** in three renderings — as
extracted, with end-of-line hyphenation rejoined, and with every hyphen replaced by a space — over its
pattern families: prompt words, second-person address, imperatives, handoff phrasing, agent and model
names, round numbers, version strings, referee words, build vocabulary, filenames, absolute paths, stray
macro names, TODO markers, repository names, promises of online-only material and notebook voice.
**Result on the final build: 22 hit lines, 15 on the allow list and the rest pinned with their reasons, 0 unpinned, 0 stale** — every hit ordinary English or the declaration the journal
mandates, each pinned with its reason; its self-drives fail as they must, so the sweep is not passing
vacuously. On the text layer: *referee*, *revision*, *previous version*, *round* and *v4.* occur 0 times;
the one *revised* is "which the authors revised" in the declaration.

★ **The arXiv source bundle is served publicly too**, and the working tree's `.tex` files carry build
notes. `arxivset.sh` therefore copies **every `.tex` comment-stripped**, check A8 proves the strip changes
not one byte of the output, and `arxivvocab_r27.py` scans the assembled set: **50 files, 0 hits**.

## 3. arXiv source rules

Assembled and verified by `bash arxivset.sh --force` on the final build: **45 items (29 `.tex` -- the master as `ms.tex`, the section files and `numbers.tex` with 201 generated fragments inlined -- plus `openjournal.cls`, `epsf.sty`, 9 figure files and 5 ancillary files)**.

| check | Requirement | Status |
|---|---|---|
| — | (La)TeX source, not PDF-only | **MET** |
| A1 | every `\input`/`\include` resolved, recursively | **229 resolved, 0 missing** |
| A2–A6, A10–A13 | figures present and PDF only, no absolute path or `..`, safe filenames, no case clash, one `\documentclass`, no hidden file, no JavaScript, ancillary files promised in the text | **PASS** |
| A8 | **the clean-directory PDF is byte-identical to the in-tree PDF** | **PASS**, md5 `26c78598dc639ca23fc336fcd559204b`, **21 pp** |
| A9 | the tarball holds the manifest and nothing else | **PASS** |

Also checked, each against arXiv's current page: **`\pdfoutput=1` is not added** (arXiv detects
pdflatex itself); no `xr`/`\externaldocument`; **no `\today`** (the manuscript empties the class's
`\submitted{Version \today}`); **no `.bbl` or `.bib` needed** (a literal `thebibliography`); **no build
product in the set**; only the figures the paper includes are copied.

### The abstract, and the limits that govern it

| limit | source | where it is enforced | final build | status |
|---|---|---|---|---|
| 1920 characters | arXiv, the metadata field | `abschars.py`, the typeset page | **1199** | **MET** |
| 1920 characters | the same limit, independently | `abstract_limit.py`, the source with the macros expanded | **1186** | **MET** |
| 1920 characters | the same limit, on the text a human pastes | `absmeta.py`, the ASCII block in §5 | **1200** | **MET** |
| 1500 characters | Ruling R7 (Referee 2's ceiling) | `abschars.py`, the typeset page | **1199** | **MET** |
| 180 words | Ruling R7 (Referee 1's 150–180) | `abswords.py`, the typeset page | **177** | **MET** |

★ Neither 180 words nor 1,500 characters is a journal rule; OJA publishes none, and arXiv's binding
constraint is 1920 characters. The account of every clause of the abstract is in the comment block of
`sections/abstract.tex`.

### The keywords, which the PDF prints as "Subject headings"

**Paste these five, in this order, into the arXiv and OJA keyword fields.**

```
Technosignatures, Search for extraterrestrial intelligence, Submillimeter astronomy, Radio spectroscopy, Debris disks
```

They are **Unified Astronomy Thesaurus** concepts under their exact names (checked 2026-10-23 against the
`master` UAT.json and the `v6.0.0` release): Technosignatures (2128), Search for extraterrestrial
intelligence (2127), Submillimeter astronomy (1647), Radio spectroscopy (1359), Debris disks (363). The
numeric identifiers are deliberately not in `\keywords{}` (`prose_v412.py` P6 forbids typed digits in
`abstract.tex`); `openjournal.cls` typesets the list under the class's heading "Subject headings:".

## 4. Proofreading — ours entirely, since OJA does none

Measured on the typeset text of the final build (`pymupdf`, end-of-line hyphenation rejoined):
`toward` **37** / `towards` **0**; `per cent` in **73** uses, with `%` only inside
tables; `hold-out` **13** / `holdout` **0**; British spelling uniform (`colour`
2 / `color` 0, `analys-` 7 / `analyz-` 0, `normalis-` 2 /
`normaliz-` 0; the two `-meter` words are the UAT keyword "Submillimeter astronomy" and
"interferometer"). The word *version* occurs 2 times, both as software or arXiv versions.

**Hyphen-for-minus**: `minuscheck.py` (a gate) reports **0 hyphen-before-digit against 63 true minus signs on the typeset page, 0 FAIL**. **Type 3 fonts: 0.** Figures:
`figgate` 0 FAIL (9 figure files, floor 6.0 pt); `floatfit` 0 "float too large" warnings, pages log = PDF = measured = 21.
Captions: `capmeasure` **0 of 21 over the limit** (3 printed lines for a table, 6 for a figure).
LaTeX log: 0 errors, 0 undefined references or citations, 0 multiply defined, 0 overfull boxes, 45 underfull.

## 5. The abstract in plain ASCII, for the arXiv metadata field

**1200 characters, 178 words.** Paste verbatim. It is the typeset abstract transliterated, so it
moves with every macro in it; regenerate it rather than editing by hand, and `absmeta.py`
fails the build if this block and the page part company.

```
We searched 405 fine-channel archival ALMA windows toward 61 systems within 40 pc for narrowband, drifting radio carriers. They cover 47.7 GHz in 26 separate intervals; 1258 coarser windows constrain only unresolved emission. Drift-corrected spectra are compared with control positions in each field. Injection into 49 windows, transferred to the rest, gives a median single-epoch sensitivity of 1.8 x 10^15 W equivalent isotropic power at ninety per cent recovery, for a carrier narrower than the instrumental channel; recovery is not confirmation. Of 49 peaks reaching 5 times the scatter at control positions, 23 coincide with catalogued molecular lines, 16 with further evidence of line emission. The other 26 are consistent with chance, against 23.8 expected from control positions (P = 0.36), which does not exclude a smaller added population. No carrier is detected or confirmed: a non-detection, not an exclusion. Confirmation needs a repeat at a covered frequency, which 21 systems lack, and tests only a carrier returning to its predicted frequency. The archive usefully constrains detectable carriers, but heterogeneous spectral and temporal coverage, more than depth, limits confirmation.
```

The transliteration is `±`→`+/-`, `×`→`x`, `−`/`–`→`-`, `’`→`'`, and a flattened `10^15`
superscript restored. A repair whose artefact is not present in the current abstract is
reported by `absmeta.py` and does not fail it; what fails it is this block disagreeing with
the page, character for character.

## 5a. Title and comments, for the arXiv metadata fields

Paste these two fields as they stand. `absmeta.py` (M5) fails the build unless the title is the one
the PDF prints on page 1 (transliterated to ASCII: the en dash becomes `-`) and the page and figure
counts are the PDF's own (pages from the file, figures from the caption entries in the `.aux`).

```
Title: An Archival ALMA Search for Unresolved Spectral-Carrier Technosignatures toward Stars within 40 pc at 114-873 GHz
Comments: 21 pages, 8 figures
```

## 6. What is blocking submission

**One item, and it is the author's: the Zenodo DOI (FOR GLENN item 5).** No journal requirement is
otherwise unmet and no gate is red. The other five author actions above are choices or signatures.

### The build this was measured on (2026-10-31, the final v4.29 build)

| check | result |
|---|---|
| `make_all.sh` from the top | rc=0, "generators OK" |
| `gate.sh`, run **twice** | **ALL GATES PASS** both times, stdout **byte-identical** |
| the PDF | md5 `26c78598dc639ca23fc336fcd559204b`, **21 pages**, 8 figures; main text 12.24 pp, appendices 5.31 pp (`pagesplit2.py`) |
| `cleanregen.py` | **290/290 byte-identical**, two `make_all.sh` passes on a deleted product tree, both rc=0 |
| `arxivset.sh --force` | 45 items (29 `.tex` -- the master as `ms.tex`, the section files and `numbers.tex` with 201 generated fragments inlined -- plus `openjournal.cls`, `epsf.sty`, 9 figure files and 5 ancillary files); **A8 byte-identical** |
| the deposit | `zdeposit.py` -> `mkzip.py` -> `zverify.py`: **V1–V10 PASS**; `ALMA_Technosignatures_40pc.zip` 495,432 B, sha256 `46b656647dd02fb40c7bfe1d3aa9464f529e462312bd3621db2972cbf2612e80` |
| the version folder | **1,445 files** to push (plus `paper_20pc/CHANGELOG.md`); `chain/` holds 818 pushed entries, the macro layer in `chain/numbers/` |
