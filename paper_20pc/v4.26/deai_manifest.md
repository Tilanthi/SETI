# `deai_manifest.md` — DEAI §N execution manifest for v4.25

`deai-verify`, 2026-10-20, Stage 5, **fresh context that did not make these edits**.
Target `/workspace/SETI/paper_20pc/v4.25`, PDF md5 `258ee0a8a0e3a81a483c2c3618157a56`, 41 pp.
Before-cut `deai/work/rev425/orig_tree`, validated: `mkinputs.py` on it reproduces the before-pass
`prose.tex` byte-identically (md5 `b53f2141e83f`).

**Every row carries a status word. No row carries a 0–100 score, an "AI probability", or any
watermark claim (§R).** Status vocabulary per §N: `PASS` · `REVIEW` · `NOT-APPLICABLE` ·
`NOT-RUN` · `FAIL`. Findings, with the numbers behind them, are in
[`/workspace/SETI/deai/STAGE5_REPORT.md`](/workspace/SETI/deai/STAGE5_REPORT.md) (BL = blocker,
SF = should-fix, N = noted).

---

## Part A — the Stage 5 gates (protocol §8, addendum T-14…T-22)

| Test | Status | Input + version | Method | Result | Evidence | Action | Verification | Reason / note |
|---|---|---|---|---|---|---|---|---|
| **T-00** battery complete, before AND after | **PASS** | `v4.25/deai_battery_after.md` | structural cell count, then independent re-run of `deai_battery.py <v4.25> <orig_tree> --arxiv --pdf` | 58 rows, before and after on every row, 0 blank cells, 0 scores, 0 probability, 0 watermark claim | `/tmp/pb2/deai_battery.md`; `diff` vs shipped = 8 lines (one path string, one whitespace) | none | reproduced independently, same status tally, same Class A list | N-3 |
| **T-01** protected-token diff | **PASS with two logged removals** | 18 section files, before vs after | per-section and whole-paper multisets over macro-resolved text; plus paragraph-block and sentence-block token conservation | numbers 2430→2430 (equal in **every** section); macro uses 2082→2082; cites 101→101; labels 71→71; objects 74→74; `\ref` **301→299** | my `/tmp/t01.py`; `deai_invariant_check.md` agrees (2220/101/42/301→299/71/1913) | restore XR2's pointer | 66 changed paragraph blocks and 121 changed sentence blocks, **0 token imbalance** — no number crossed a sentence boundary | N-14, SF-3 |
| **T-01d** `\ref` sub-row | **REVIEW** | `05_results`, `app_C` | diff of `\ref` keys | 2 removed: duplicate `Appendix~\ref{sec:heldout}`; `\S\ref{sec:etacrv}` | change log Batch 10 names both | XR1 accept, XR2 restore | no orphan labels (`sec:etacrv` 22 refs, `sec:heldout` 4) | SF-3, N-8 |
| **T-02** proposition map | **PASS** | before/after sentence alignment | difflib over 1,185 sentences; inspected all blocks of unequal length | 4 unequal blocks, all splits/merges; **0 new propositions, 0 dropped** | §T-02 worksheet in the report | none | token multisets conserved inside every one | N-14 |
| **T-03** epistemic ladder | **PASS** | 136 changed sentences | hedge / strength / quantifier token deltas per changed block | 2 deltas, both benign: *the inclusion criteria*→*every inclusion criterion*; *what that excludes*→*that exclusion* | report §T-03 | none | `EP-02` independently reads 0 climbs; it caught and forced the repair of a deleted modal during the pass | — |
| **T-04** N-01…N-07 | **PASS** | v4.25 build | **re-ran `audit_numbers_v385.py` myself** rather than re-implementing it, plus the gate's own `prosenum` / `consistency_v399` / `macrosyn` / `xrefcheck` / `citegate` | **58 PASS / 0 FAIL / 13 WARN / 0 SKIP**; prosenum 0; consistency 0; macroleak 0; citegate 68/68, 0 FAIL | my terminal run; `gateF2.log` | none | 13 WARNs are the long-standing SIMBAD-form names (`HD14055`) | N-11 |
| **T-05** R-01 + clean compile | **PASS** | `gateF1/gateF2.log`, `arxivsetF.log` | byte-compare the two gate logs; read the latex summary; confirm the PDF | `gateF1 ≡ gateF2` (`cmp`); 0 errors, 0 undefined, 0 unresolved, 0 multiply-defined, **0 overfull**, 0 Type-3; 41 pp; readable PDF present | logs in `deai/work/rev425/logs/` | none | A8 clean-directory build **byte-identical** to the in-tree PDF | N-13 |
| **T-06** fresh-agent main finding | **PASS** | Abstract, §1, Conclusions via `pdftotext` | blind sub-context, stored sentence withheld, all `deai*`/`main_finding` paths forbidden | agreement on all three limbs; reader additionally supplied `P = 0.13` and EIRP$_{90}$ $1.5\times10^{15}$ W | report N-1 | upgrade the stored §3.1 sentence | **the verifier's own blindness was lost at 00:52 UTC and is disclosed**; the test was re-run blind in a fresh context before any Stage-4 deliverable was opened | N-1 |
| **T-07** hard-zero features | **PASS for the hard zeros; P-01 REVIEW** | `prose.txt` after | `canon_extra.FEATURES` on before and after | P-02 0, P-03 0, P-04 0, **P-05 10→0**, P-07 0, P-08 0; L-04 **1, a false flag** (*the real part of the visibility*); **P-01 30 canonical / 142 widened vs a stated ≤ 1** | report N-16, SF-1 | adjudicate P-01 as a family | the true L-04 hit was removed; P-01's own clause exempts a technically essential distinction | SF-1 |
| **T-08** co-occurrence | **REVIEW** | `prose.txt` before/after | `canon_extra.cooccurrence`, 4-sentence window | canonical **C-01 135 → 78**; with `and not` added to P-01, **C-01 203 → 194**, worst window 5 → 4 features | report SF-1 | record the widened figure | the 42 % improvement is largely the regex's blind spot, not the prose's | SF-1 |
| **T-09** over-correction absent | **PASS** | whole pass | §1/I-7 tactics: padding, hedge-stripping, metric-chasing, voice flattening | no tactic found; 133 edits, −61 words; RV-01 ladder respected; appendix comparatives kept with reasons; emphasis adjudicated not stripped | change log Batches 5, 7, 10 | none | the one uniformity risk is SF-1, and the change log declares the idiom split deliberately | SF-1 |
| **T-10 / T-18** adversarial fixtures | **PASS** | both suites + clean baselines | `canon/adversarial/run_canon_fixtures.py`; `deai/adversarial/run_fixtures.py` | canonical **23 checks, 23 PASS, 0 FAIL**; project **10/10 fired, baseline CLEAN**; battery `--selftest` PASS | my terminal runs | none | includes AD-10b (bare multiset blind to re-attachment) and AD-10c clean control | N-15 |
| **T-11** journal limits | **PASS** | typeset page | `abswords.py`, `absmeta` | **243 words** of 245, one paragraph, measured on the page; ASCII field **1,567 characters** of arXiv's 1,920, held **character for character** against the typeset abstract | my run; `gateF2.log:39` | none | `ARXIV_UPLOAD.md` still quotes the pre-revision 1562/1564 | BL-1 |
| **T-12** AI-assistance disclosure | **PASS** | `08_backmatter`, typeset p. ~1688 of the text stream | read on the page | present, specific, accurate: names what the models did (scripts, pipeline, tests, generators, drafted text) and what the authors did; adds that no number is typed | `/tmp/p425.txt` | none | ST-04 satisfied; two of LX-01c's four "forbidden mentions" are this required statement | N-2 |
| **T-13** author sign-off | **NOT-RUN** | — | — | — | — | author to read Abstract, Introduction and Conclusions aloud | — | author action by definition; **two blockers are open and nothing should be submitted over them** |
| **T-14** B-33 edit budget | **PASS** | 18 section files | normalised edit distance > 0.3, per section | largest section **9.7 %** (Conclusions); whole paper **1.3 %**; any-change 136/1,185 = **11.5 %** | report N-14 | none | against the 40 % stop condition | — |
| **T-15** B-29 new-text audit | **REVIEW** | changed vs unchanged sentences | widened P-01 rate on each set, then the same set before the pass | rewritten **13.69/1000** vs unchanged **3.25/1000** (= FAIL as specified); **the same sentences were 16.32/1000 before** (= a 16 % improvement) | report SF-2 | record both numbers | the row's denominator is selected by the treatment; a confounded row is not evidence of over-correction | SF-2 |
| **T-16** coined-terminology register | **REVIEW — adjudicated** | title, body | CT-01…CT-06 register with a keep-reason per kept term | register delivered; **CT-04 overridden once**: *Spectral-Carrier* stands in the title with the stated keep-reason that it is this paper's precise term for the signal class searched | change log / audit report | author confirms the override | the only CT rule knowingly broken; title otherwise clean (14 words, no colon-subtitle, no gerund, ALMA is a facility name) | N-12 |
| **T-17** LX / FG / TB / ST hygiene | **REVIEW** | package + PDF | LX-01a/b/c, LX-03, LX-07, figure widths, bibliography leading | **LX-01c is a gate failing on a correct tree** — the authors' 222 `.tex` carry 0 comments with text; the 676 are `openjournal.cls` (295) + `epsf.sty` (380); all 4 "forbidden mentions" are false positives. **LX-03 is a real hit the gate cannot see: 194 shipped `.tex` filenames carry version/round strings, 180 containing the literal `round`.** LX-07 clean but Title/Author empty. One figure at `0.99\textwidth` | report BL-2, N-2, N-9, N-10 | packaging rename map; populate `pdftitle`/`pdfauthor` | A8 byte-identity would prove a rename changed nothing | BL-2 |
| **T-19** LT-01 list delivered | **REVIEW** | live arXiv sweep (by the before-pass) | 24-month topic/object/method sweep | delivered; **two expected-but-absent papers** named, still absent in v4.25 | `deai_audit_report.md`; `deai_author_decisions.md` §2 | author decides whether to cite | neither read beyond the abstract; never auto-cited | — |
| **T-20** OV-01 overlap | **NOT-RUN** | — | — | — | `deai_audit_report.md` | — | no cited full texts available offline; §M requires NOT VERIFIABLE rather than a pass | — |
| **T-21** SG segmentation validation | **PASS (machine proxy)** | `prose.txt` | SG-01 abbreviation register; SG-02 50-sentence boundary print | SG-01 honoured, 0 errors; SG-02 0 machine-detected boundary errors in 50 | `/tmp/pb2/sg02_fifty_sentences.md` | author or a human reader to read the fifty | the order asks for a **human** read; the machine proxy is not a substitute and is labelled as a proxy, not as zero | — |
| **T-22** B-37/B-38 voice model | **NOT-RUN** | — | §S/§T conditional on S-01 | no validated author corpus separating holdouts from controls | `canon/profiles/white_profile.json` exists but S-01 is not demonstrated | — | §T-3 forbids raw-tex scoring and §S makes the gate conditional | — |
| **SR-1…SR-4** four simulated referees | **NOT-RUN (deferred, §Q)** | — | — | — | — | run when a second model family is available | — | **§RV-04 requires a different model family for judging tasks and this installation has one.** Four personas of one model are not four referees and are not offered as such |

---

## Part B — the author's constraints, verified on the rebuilt artefacts

| Constraint | Status | Method (named) | Result | Reason / note |
|---|---|---|---|---|
| Main text ≤ 25 pp | **PASS** | `pagesplit.py`, four regions in points of column against a 694 pt column; `secbudget.json` is deleted and no figure comes from it | **21.77 pp** (back matter 1.30, appendices 16.97, bibliography 0.67; total 40.71 of 41 pages) | the whole-page convention gives ≈23.4 on the same build; the method is named because the two differ |
| Abstract ≤ 245 words, well inside 1,920 characters | **PASS** | `abswords.py` on the PDF text stream | **243 words**, one paragraph | word-for-word neutral across the Batch-2 rewrite |
| arXiv ASCII field = typeset abstract, character for character | **PASS** | `absmeta` M3/M4, gate-held | **1,567 characters, 244 words** of 1,920 | `OJA_SUBMISSION.md` was re-synchronised; **`ARXIV_UPLOAD.md` was not** → BL-1 |
| No mention of versions, edits, referees, rounds, corrections, "previously" — prose, caption, table, figure, printed comment, PDF metadata, arXiv source | **FAIL on the arXiv source; PASS everywhere else** | `genai_sweep` on the typeset page; my own sweeps of `pdftotext`, `pdfinfo`, `strings`, and the 240-item package | typeset page clean (the single `revised` is the required AI disclosure); PDF contains `4.25` **zero** times, metadata included; **but 194 shipped `.tex` filenames carry version/round strings, 180 containing `round`, and ~200 `\input{survey_numbers_roundNN}` lines are shipped source text** | BL-2 — author's call, fix lives in the packaging step |
| Figures at single- or double-column width | **REVIEW** | grep of all `\includegraphics` options | `\columnwidth` ×8, `\textwidth` ×2, **`0.99\textwidth` ×1** (`coverage_waterfall.pdf`) | pre-existing, untouched by this pass | 
| Reference list at the class default leading | **PASS** | grep for `bibbaselineskip` and class overrides | no override in force; the only occurrence is inside the comment recording its deletion | the 2.52 mm tightening stays deleted |
| §5.3.2's negation present | **PASS** | string check on the resolved prose, before and after | *"Neither criterion was fixed in advance. The condition was noticed in one block and the criterion written afterwards, so it is post hoc…"* — **byte-identical** to the before-cut | a phrase sweep cannot see a negation; this was checked as text, not as a metric |
| Sirius passage intact | **PASS** | diff of the passage, before vs after | **identical** | — |
| Numbers generated, never typed | **PASS** | macro-use multiset + `prosenum` + `audit_numbers` | 2,082 macro uses unchanged; no generator touched; 0 literals disagreeing with a macro | T-01a's empty delta over 2,220 values proves it rather than asserting it |

---

## Part C — deliverables (operating order §7 / protocol §9)

| File | Status | Note |
|---|---|---|
| revised `.tex` + fresh `.pdf` | **PASS** | 0 errors, 41 pp, main 21.77 pp |
| `deai_change_log.md` | **PASS** | 567 lines, 133 edits in 11 batches, old → new + defect ID + reason + status on each |
| `deai_audit_report.md` | **PASS** | before-table, Stage 1–2 findings, manifest skeleton |
| `deai_author_decisions.md` | **FAIL — misplaced** | exists only at `deai/work/canon425/`; §7 puts it in the version directory | 
| `deai_invariant_check.md` | **PASS** | 11 batch rows + the independent re-measurement; matches my own numbers exactly |
| `deai_referee_report.md` | **FAIL — misplaced** | exists only at `deai/work/canon425/`; the change log's own routing of the filename finding points at its §7 |
| `deai_battery.md` (before) / `deai_battery_after.md` | **PASS** | after-file reproduced independently to 8 diff lines |
| `deai_voice_comparison.md` | **NOT-APPLICABLE** | §5 did not run; B-37/B-38 NOT-RUN with reason |
| `deai_manifest.md` | **PASS** | this file |

---

## Summary of status words

**PASS 22 · REVIEW 7 · NOT-RUN 5 · NOT-APPLICABLE 1 · FAIL 3.**
The three FAILs are the arXiv-source constraint (BL-2) and the two misplaced deliverables (SF-5);
**no Class A failure was found in the manuscript itself.** Two blockers and six should-fixes are
open and are listed in [`STAGE5_REPORT.md`](/workspace/SETI/deai/STAGE5_REPORT.md); nothing here
was fixed by this stage, by instruction.

---
---

# Part E — CYCLE 2 (`deai-close`, 2026-10-20), the convergence cycle Ruling 20 ordered

Target `/workspace/SETI/paper_20pc/v4.25`, final PDF md5 **`b99f8cc90abae9794fdb6cc54a298e21`**,
41 pp, main text **21.65 pp of 25**. Before-cut unchanged and re-validated (`prose.tex`
`b53f2141e83f`). **Every row below carries a status word; none carries a score, an "AI
probability", or any watermark claim (§R).**

| Test | Status | Input + version | Method | Result | Evidence | Action | Verification | Reason / note |
|---|---|---|---|---|---|---|---|---|
| **C2-01** the widened C-01, re-measured independently | **PASS** | `prose.txt` before-cut / entry / final | `deai/work/c2/census.py` — canonical `canon_extra.cooccurrence`, plus the same function with `\band not [a-z]` appended to P-01's regex | canonical **135 → 78 → 71**; widened **203 → 194 → 186**; family **160 → 150 → 140** | `deai/work/c2/cycle2_final.json` | reported as the audit report's headline | reproduces every figure of Stage 5's SF-1 table to the digit, from an independently written instrument | Ruling 20 |
| **C2-02** contrastive family adjudicated instance by instance | **PASS** | 166 instances in `sections/*.tex`, comments excluded | RV-01 ladder, delete preferred over marker swap; keep-reason required for every instance kept | **12 removed**, 154 kept with keep-reasons by class | `deai_change_log.md` BATCH C2-B; `deai_audit_report.md` §2 | none | B-33 worst section **25.0 %** of 40 (`deai_b33_edit_budget.json`) | Ruling 20 |
| **C2-03** C-01 composition | **REVIEW** | 186 widened windows | decompose each window's firing set; then re-run with P-06 restricted to colons introducing no number/symbol/citation/ref and P-13 to lists with no measured item | **133 of 186 are P-01+P-06+P-13**; adjudicated C-01 **59 → 52 → 48** | `deai/work/c2/adjudicated_c01.txt`, `clusters_base.txt`, `lever.py` | reported to the author | three of the four detectors behind C-01 are "> P90 of corpus" and **the corpus is NOT-RUN under §Q**, so 186 is comparable with nothing | audit report §3 |
| **C2-04** the categorical claim restored | **PASS** | `abstract`, `07_conclusions` | rewrite with a limiting verb, no cleft, no `X, not Y`; then run the gate rather than assume it | `absreq_r17`: **7 checks, 0 FAILED**, B7 satisfied by the new wording | `deai_change_log.md` BATCH C2-A | none | abstract **244 words of 245** (`abswords.py`, on the page), ASCII field **1 572 of 1 920** (`absmeta.py`) | Ruling 21 |
| **C2-05** P-05 on a detector wider than the construction | **PASS (after 4 repairs)** | `prose.txt` | sweep for `What …` + ANY copula at ANY distance | **4 live pseudo-clefts** that both the canonical (`≤2` words, `is`) and the project's widened (`≤4` words, 4 copulas) regexes missed; all 4 rewritten; **P-05 now 0 on the wide detector** | `deai_change_log.md` BATCH C2-C | none | one of them escaped because its copula is *belongs* | sixth blind spot |
| **C2-06** the only stock frame in the paper | **PASS** | `05_results` | P-10 / P-11 / G-03 census | **1 sentence fired all three and was the sole instance of each**; two words deleted; **4 C-01 windows cleared** | `deai_change_log.md` SF1a | none | the claim is untouched | audit report §5 |
| **SF-2 / B-29** new-text audit | **REVIEW, confound stated** | 135 rewritten vs 1 052 unchanged sentences | full battery on the inserted/rewritten sentences alone | rewritten **13.69 /1000**, unchanged 3.25 /1000 → 4.2× worse, which is a FAIL as specified | Stage 5 SF-2; `deai_audit_report.md` §4 | record as REVIEW | **the same sentences measured 16.32 /1000 before the pass** — a 16 % improvement; the denominator is chosen by the treatment | SF-2 |
| **SF-3 / XR2** the sentence left without a referent | **PASS** | `app_C_spatialnorm` | name the referent rather than restore the pointer | *the exceedances* → *the repeat-epoch exceedances* | `deai_change_log.md` XR2b | none | `\ref` stays at **299**, so XR1/XR2's reduction stands | SF-3 |
| **SF-4** `flux` → `flux density` | **PASS, action NONE by measurement** | `prose.txt` | re-census the 10 survivors in context | **7 genuinely bare, every one an integrated flux in W m⁻² that §2 defines in situ**; 3 were `flux-density`/`flux-scale` and only ever a hyphen artefact | `deai_author_decisions.md` §1.1 | author confirmation | Ruling 19 reached the same verdict independently | SF-4 |
| **SF-5** the two missing §7 deliverables | **PASS** | `work/canon425/` | move into the version directory and extend | `deai_author_decisions.md`, `deai_referee_report.md` now in `v4.25/`, each with a cycle-2 section | this directory | none | `deai_voice_comparison.md` also written (§T-6), **REPORT-ONLY** | SF-5 |
| **BL-1** `ARXIV_UPLOAD.md` pinned a superseded build | **PASS** | `ARXIV_UPLOAD.md` | rewrite to carry **no measurement at all**, naming the command that prints each number; add a gate on that property | 0 prose measurements, 0 instructions missing | `arxivpin.py`; `gate.sh` | none | `arxivpin --selftest`: **5 clauses, all demonstrated firing**, plus a control proving a number inside a code span is a command | BL-1 |
| **BL-2** version/round strings in the arXiv source | **PASS, proved** | `/workspace/tmp/arxivset` | `arxivset.sh` A15/A15b: inline, prune, rename, rewrite, then **fail on any residue** | **222 source `.tex` → 35 package `.tex`**; 188 inlined; **4 608 dead macro definitions pruned**; 13 `.tex` + 1 figure renamed; `ms.tex`; **53 items** | `deai/work/c2/arxivsetZ.log` | author decides on the two third-party residues | **A8 byte-identical** (`b99f8cc9…` both sides) — the proof that none of it changed the document | BL-2 |
| **C2-07** the PDF itself | **PASS** | `technosignatures_40pc_v4.25.pdf` | binary sweep for version strings, then `pdftotext` sweep | `/PTEX.FileName` carried **11 local build paths**, one of them `./figures/chain_v412.pdf` — **invisible to every text sweep in this build**; `\pdfsuppressptexinfo=-1` removes all 11 | `deai_change_log.md` PX2 | none | after: `_v4` 0, `_v3` 0, `round` 0, `referee` 0 in the binary; `pdftotext` sweep clean | seventh blind spot |
| **C2-08** my own independent package sweep | **REVIEW, 3 residues, none ours** | 53 package items | own regex over names, `\input`/`\includegraphics` targets, body text and figure binaries | `openjournal.cls` *referee* (journal template footer), `epsf.sty` *Revision* (third-party header), figure PDFs *Matplotlib v3.10.9* (library metadata); 9 `correction` hits are **primary-beam and field corrections** | §8 of this manifest | author decision | my sweep is deliberately wider than A15's and its own hits are reported as false positives rather than hidden | author decisions §3.1 |
| **C2-09** `make_all.sh` | **PASS** | v4.25 | full generator chain | rc=0, `generators OK`, 0 FAIL from any generator gate | `deai/work/c2/make_all_c2.log` | none | run before every gate run | — |
| **C2-10** `gate.sh` twice | **PASS** | v4.25 | two consecutive runs, logs byte-compared | **ALL GATES PASS** both times; `cmp` → **byte-identical**; same PDF md5 both times | `gateZ1.log`, `gateZ2.log` | none | `SOURCE_DATE_EPOCH` pinned; the new `\pdftrailerid` makes the PDF independent of its filename too | — |
| **C2-11** `cleanregen` | **PASS** | v4.25 | delete all 280 products, two full `make_all.sh` passes, re-digest | **280/280 byte-identical**, both passes rc=0 | `deai/work/c2/cleanregen_final.log` | none | ★ an earlier run read **232/280** — its baseline was a tree my own timed-out first attempt had left half-rebuilt, **not a defect in the edits**: the PDF md5 was unchanged across it, and the clean re-run is 280/280 | see §9 |
| **C2-12** `arxivset --force` A8 | **PASS** | final build | clean-directory build from the package alone, three passes, byte comparison | **A8 PASS: byte-identical**; A9 PASS; A1 222/0 missing; A2–A6, A10–A13 PASS; 41 pp, 0 errors, 0 overfull, 0 Type-3 | `deai/work/c2/arxivsetZ.log` | none | byte identity is what proves the inline, the prune and the renames changed nothing | — |
| **C2-13** page and abstract budgets on the rebuilt artefacts | **PASS** | final PDF | `pagesplit.py` (column points between the ACKNOWLEDGEMENTS, APPENDIX and REFERENCES headings), `abswords.py`, `abschars.py`, `absmeta.py` | main text **21.65 pp of 25**; back matter 1.26; appendices 17.13; bibliography 0.67; 41 pp; abstract **244 words of 245**, **1 572 characters of 1 920** | `deai/work/c2/` logs | none | the method is named, as required, and all four read the PDF rather than the source | — |
| **C2-14** figure widths and reference leading | **PASS, untouched** | `sections/*.tex`, `openjournal.cls` | count `\includegraphics` widths; look for `bibbaselineskip` | 8 `\columnwidth`, 2 `\textwidth`, 1 at `0.99\textwidth` (pre-existing, N-10); leading is the class default 3.075 mm and `bibbaselineskip` survives only inside the comment recording its deletion | — | author decision on the 0.99 figure | neither cycle touched either | N-10 |
| **C2-15** §5.3.2's negation and the Sirius passage | **PASS** | `05_results`, `03_sample` | locate and compare with the before-cut | negation present: *"The field is inflated and the star is not."*; **Sirius byte-identical to the before-cut in both files** | `deai/work/c2/` | none | checked against `orig_tree`, not against a memory of it | — |
| **C2-16** the dead macro layer, as a measurement | **PASS** | package `numbers.tex` | count definitions and uses over the whole package, iterate to a fixed point | **6 020 definitions, 4 608 expanded nowhere**; pruned; 1 629 remain | `arxivsetZ.log` A15b note | none | refused outright if the package used `\csname` (it uses it 0 times), and A8 is the proof | — |
| **B-37/B-38** voice distance | **REPORT-ONLY (S-01 FAILED)** | `prose.txt`, `flat.tex`, main `.tex` | `deai_voice.py score` against `white_profile.json` | **D 1.067 → 1.071 → 1.072** on macro-resolved prose; 1.131 → 1.140 on unresolved flat; 2.603 on the main `.tex` alone | `deai_voice_comparison.md` | none, ever | §T-2.3: holdouts 0.89 vs controls 1.20, **tails touch**, so the gate is permanently REPORT-ONLY and **no sentence was moved by a distance** | §T-6 |
| **B-38 sub-row** changed vs unchanged | **NOT-RUN** | 136 changed sentences | — | — | `deai_voice_comparison.md` §2 | none | a 5 300-word sub-corpus against a document-level profile would have no calibration; §Q forbids a silent skip | §Q |
| **SR-1…SR-4** four simulated referees | **NOT-RUN** | — | — | — | Stage 5 disclosure 2 | none available locally | §RV-04 wants a different model family and this installation has one; four personas of one model are not four referees | §Q |
| **N-4** the battery's own false statement | **PASS** | `deai_battery.py` | make the reconstruction notice conditional on the canonical package actually being absent | it is present, so the file now prints a **provenance** notice that is true | `deai_battery.md` line 8 | none | `deai_battery.py --selftest`: PASS | N-4 |

## §8 — the three residues my own sweep found, and why each is reported rather than removed

| residue | where | status | reason |
|---|---|---|---|
| the word *referee* | `openjournal.cls` line 875, the journal's own template footer | **NOT-A-DEFECT (author decision)** | third-party class file; arXiv must receive it verbatim; it is the journal advertising its own review process, not a statement about this paper. It does not appear in the typeset text of this build |
| the word *Revision* | `epsf.sty` line 105, the style file's header | **NOT-A-DEFECT** | third-party, verbatim |
| `Matplotlib v3.10.9` | `Creator`/`Producer` of all 11 figure PDFs | **NOT-A-DEFECT** | the plotting library's version, not the paper's |
| *correction* ×9 | 8 section files + `anc/si_recovery.txt` | **NOT-A-DEFECT** | every one is a primary-beam or field **correction** — physics. My sweep was deliberately wider than A15's and this is its own false-positive set, reported rather than hidden |

## §9 — what went wrong in this cycle, recorded because a clean report is not the same as a true one

1. ★★ **I wrote through a hard link and overwrote the before-cut snapshot's copy of
   `deai_audit_report.md`** — exactly Stage 5's N-5 hazard, which I had read. Detected by `stat`,
   repaired from the untouched third copy (`work/rundir-v4.25/`, md5 `014d7c4e261f…` verified on
   all three paths), the link broken, and the three remaining hard-linked deliverables unlinked
   before they were edited. The snapshot's `.tex` files were never touched and still reproduce the
   before-cut prose byte-exactly. **Status: repaired, verified.**
2. ★ **My first `\pdftrailerid` patch wrote `\fi` through a non-raw Python string**, so `\f` became
   a form feed in the preamble: *Missing \begin{document}*, no PDF, `macroleak` + `tabfloor` +
   `latexlog` failing together. Repaired; it is the same class as this project's `\FateDoneV408`
   defect. **Status: repaired, gates green.**
3. ★ **My first `cleanregen` was killed by a 58-minute timeout mid-rebuild**, which left the tree
   half-regenerated; the next run therefore compared a clean rebuild against a corrupt baseline and
   read **232/280**. The PDF md5 never moved across it, and a clean re-run reads **280/280**.
   **Status: resolved — the lesson is that `cleanregen` must be run detached, never under a
   timeout, because a killed run poisons the next run's baseline.**
4. **My own first package sweep fired on `sections/02_background.tex`** because `background`
   contains `round` — the mirror image of the blind spot that let 180 `round*` filenames through.
   **Status: regex tightened; both directions now recorded.**
