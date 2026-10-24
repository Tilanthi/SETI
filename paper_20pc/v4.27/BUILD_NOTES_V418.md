# v4.18 — build notes

One PDF, **35 pp**, `technosignatures_40pc_v4.18.tex`, built with `pdflatex` three times.
`SOURCE_DATE_EPOCH` is pinned in both `make_all.sh` and `gate.sh`, so the PDF is reproducible in
bytes and not merely in content. There is no Supporting Information: the appendices, tables and
figures are inside the one file, which is what an arXiv-overlay journal publishes.

## Verification of this build (2026-10-13, 06:40–07:35 UTC)

| check | result |
|---|---|
| `make_all.sh` | rc=0, "generators OK" |
| `gate.sh`, twice | **ALL GATES PASS** both times; logs **byte-identical**, md5 `e66d6987d2c766d79039a3f6fc0a669f` |
| PDF | md5 `e954d4778bae792f9a3e524062c1471d`, unchanged by either gate run and by the clean-set build |
| LaTeX log | 0 errors, 0 undefined control sequences, 0 unresolved references or citations, 0 multiply defined, **0 overfull hbox, 0 overfull vbox**, 26 underfull |
| Type 3 fonts | **0** |
| pages | **35** |
| `audit_numbers_v385.py` | **58 PASS / 0 FAIL**, 10 warnings (all long-standing and named) |
| `cleanregen.py` | **212/212 byte-identical** on a deleted product tree, both `make_all.sh` passes rc=0 |
| `arxivset.sh` | A1 183/183 inputs, A2 11/11 figures, A9 196 = 196 items, **A8 byte-identical**, 2.6 MB set, 408 kB tarball |
| `minuscheck.py` | 0 hyphen-before-digit against 112 true minus signs on the page, 0 FAIL |
| `genai_sweep.py` | 9 hit lines across 23 pattern families; `--drive` fires **23 of 23** |
| other gates | roundcollide, orphanround, macrosyn, synmacro, twinmacro, valuetwin, prosenum, macroleak, intsweep, citegate 57/57, labelcheck, figorphan, wordcase, prodident, ledgergate, fragstale, censusacct, absreq, prosegate — all 0 FAIL |

## The abstract and arXiv's character limit

The journal sets no abstract limit; **arXiv's 1920 characters is the limit that governs it**, and
it is enforced in the three places it can be broken, each gate driven to fail on its own:

| gate | what it measures | value |
|---|---|---|
| `abschars.py` | the typeset paragraph, out of the PDF | **1856**, headroom 64 |
| `abstract_limit.py` | the source, with every macro expanded; shares no code with the above | **1845** |
| `absmeta.py` | the plain-ASCII block in `OJA_SUBMISSION.md` that is pasted into the submission form | **1860**, headroom 60 |
| `abswords.py` | the word count — **ours**, a style alarm and not a journal or arXiv rule | **294** against 310 |

★ The pasted text is **4 characters longer** than the typeset paragraph, because `±`→`+/-` and the
two restored superscripts add characters. So the page-side gate passing does not imply the
submitted field passes: `absmeta.py` is a separate limit, not a restatement. It also requires the
block to equal the current typeset abstract **character for character**, so a value that moves in
the paper and not in the block fails the build instead of being submitted, and it checks the two
counts the submission file quotes beside it.

## Data provenance

The ALMA Science Archive and the project codes listed in the paper. No deposit of ours is offered,
promised or cited, and no DOI of ours is quoted.
