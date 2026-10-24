# `deai_battery.md` — the authoritative DEAI **before-pass** on v4.25

`deai-canon`, 2026-10-19. Target **`/workspace/SETI/paper_20pc/v4.25/`** (main text 21.85 pp,
41 pp total, PDF md5 `4dcb008f1938431749750bcc75bbc5cf`, `gate.sh` ×4 byte-identical,
`cleanregen` 280/280, `audit_numbers` 58/0).

**This is a before-pass.** Protocol execution contract #1: the measured battery is computed and
written **before any revision**. No sentence of the paper was edited to produce it. Every row
carries a **before** value (v4.25 as it stands), an **after** value (`NOT-RUN — no revision exists
yet`, which is not a pass), a **status word**, a **provenance word** (`ORDER` / `INFER` /
`PROJECT` / `CANON`) and its **calibration flag**. No row is blank. **No row carries a 0–100 score,
an "AI probability", or any watermark claim (§R).**

The `v4.24` column is the same instrument run on the previous version 2.5 h earlier, so every
movement below is measured, not inferred.

- Instrument: canonical `/shared/deai/` package (protocol v3.0 §0–10 + addendum §A–§T, which wins on
  conflict), copied with hashes to [`/workspace/SETI/deai/canon/`](/workspace/SETI/deai/canon/);
  project operating order [`referee_r24/DEAI_SPEC_R24.md`](/workspace/SETI/referee_r24/DEAI_SPEC_R24.md).
- Reconciliation of this instrument against the earlier 58-row reconstruction, and the 15 defects
  found in the canonical package itself:
  [`/workspace/SETI/deai/CANON_ALIGNMENT.md`](/workspace/SETI/deai/CANON_ALIGNMENT.md).
- Evidence, instances and logs: [`/workspace/SETI/deai/work/canon425/`](/workspace/SETI/deai/work/canon425/)
  and [`/workspace/SETI/deai/work/b425_before/`](/workspace/SETI/deai/work/b425_before/).
- Text scored: `prose.tex` / `prose.txt` — the §T-3 preprocessed, **macro-resolved** prose
  (33,975 words; 6,055 macros resolved). Addendum §T-5.4: *DEAI scores the rendered text, never the
  macro layer.* Rows that need structure (captions, emphasis, cross-references, labels, comments)
  are read from `resolved.tex`/`flat.tex` and say so. A row read off the wrong text is marked
  **VACUOUS**, never a pass.

---

## Part A — canonical §5.13 + §O battery (`deai_battery.py`, `deai_battery_v3.py`, `deai_voice.py`, all unmodified)

| row | prov | threshold (calibrated?) | v4.24 | **v4.25 (before)** | after | status | note |
|---|---|---|---|---|---|---|---|
| B-01 em-dash /1000 | CANON | ≤ 1 (calibrated) | 0.00 | **0.00** | NOT-RUN | **PASS, VACUOUSLY** | the canonical regex counts `---` only. This paper's house dash is ` -- `: **202 instances, 5.95/1000** (181 with literal single spaces), down from 6.10. Read B-01 as **5.95 against ≤ 1 → REVIEW** |
| B-02 excess lexicon /1000 | CANON | ≤ 0.3, hard words 0 (calibrated) | 0.09 | **0.06** | NOT-RUN | **PASS** | 2 hits, both protected senses (`robust`, `comprehensive`) |
| B-03 reaction adverbs /1000 | CANON | ≤ 1 (calibrated) | 0.00 | **0.00** | NOT-RUN | **PASS** | broader than our `T4-06`: any position, not only sentence-initial |
| B-04 agent vocabulary | CANON | **0** (calibrated) | 2 | **2** | NOT-RUN | **FAIL** | unchanged: 1 true hit (`The real stellar ranks agree…`) + 1 **false flag** (`the real part of the visibility`, a protected technical sense — B-28) |
| B-05 "rather than" /1000 | CANON | **≤ 2** (calibrated) | 2.31 | **2.30** (78 instances) | NOT-RUN | **FAIL** | **unmoved.** 75 contiguous + 3 line-wrapped. §T-4.2 records this paper's deployed census as **76 → 8** at v4.23; see `deai_author_decisions.md` §1 |
| B-06 reasoning connectives /1000 | CANON | ≤ 4 (calibrated) | 0.77 | **0.68** | NOT-RUN | **PASS** | |
| B-07 suspended-hyphen / stacked compounds | CANON | ≤ 3, each checked for field-standard status (calibrated) | 28 | **28** | NOT-RUN | **REVIEW** | the canonical filter already excludes `line-of-sight`-class forms; the residue is this paper's coined compounds |
| B-08 This/These+noun openers /1000 | CANON | ≤ 8, not dominant (calibrated) | 0.44 | **0.47** | NOT-RUN | **PASS** | |
| B-09 reporting-verb top share | CANON | < 0.40, **descriptive only (§A)** | 0.23 | **0.23** | NOT-RUN | **PASS** | never a rewrite trigger by itself |
| B-10 top opener / top-3 share | CANON | < 0.35 / < 0.55 (calibrated) | 0.28 / 0.39 | **0.29 / 0.40** | NOT-RUN | **PASS** | `the` dominant |
| B-11 sentence-length CV | CANON | ≥ 0.40 (calibrated) | 0.60 | **0.60** | NOT-RUN | **PASS** | |
| B-12 mean sentence length | CANON | ≤ 30, flag > 40 (calibrated) | 28.3 | **28.5** | NOT-RUN | **PASS** | 35.6 on raw tex — the macro layer inflates it |
| B-13 contrastive reframes | CANON | ≤ 15 % of original count (calibrated, **relative**) | 95 | **93** | NOT-RUN | **NOT-RUN** | a relative threshold needs the pre-revision count, which this pass *is*; 93 is the baseline the after-pass is measured against |
| B-14 pseudo-clefts / questions / colon reveals | CANON | **0 / 0 / re-check** (calibrated) | 11 | **9** (canonical regex) · **29** (widened, see note) | NOT-RUN | **FAIL** | hard zero under T-07. Net −2, but **4 were removed and 2 NEW ones introduced** by the v4.25 rewrite (`What is claimed is`, `What that excludes is`). ★ The canonical regex allows only a 1–2-word gap and therefore sees **31 % of the construction**: widened to a 1–4-word gap the count is **29**, including **`What limits the search is coverage, not depth` in the Abstract** — where P-01 forbids a contrastive reframe outright — and a **third variant of the same sentence**, `What limits this search is coverage and not depth`, **new in v4.25**. The `\subsection{What the expectation is conditioned on}` heading survives |
| B-15 trailing ", -ing" clauses | CANON | ≤ 2 (calibrated) | 0 | **0** | NOT-RUN | **PASS** | |
| B-16 triadic lists | CANON | inspect (**uncalibrated**) | 2 / 133 | **2** (canonical regex) · **143** (`deai_voice.py` regex) | NOT-RUN | **REVIEW** | the canonical B-16 regex requires an Oxford comma; this paper writes British `A, B and C`, so the shipped row sees **2** of **143**. Use 143. (A whole-text variant of the same regex returns 287 and is unstable across sentence boundaries — do not quote it) |
| B-17 stacked premodifiers | CANON | ≤ 3 (calibrated) | 6 | **6** | NOT-RUN | **FAIL** | |
| B-18 paragraph-length CV | CANON | ≥ 0.35 (calibrated) | 0.69 / 0.78 | **0.64** (prose) / **0.76** (resolved) | NOT-RUN | **PASS** | |
| B-18b paragraph top-opener share | CANON | ≤ 0.35 (calibrated) | 0.34 (192 paras) | **0.36 (203 paras)** | NOT-RUN | **FAIL — NEW REGRESSION** | ★ crossed its threshold in v4.25: `The` opens 73 of 203 body paragraphs. The relocation of ~2.1 pp into appendices added 11 paragraphs and the new ones open conventionally. Gate-invisible |
| B-19 closing glosses | CANON (unimplemented canonically) | 0 (**uncalibrated**) | 0 | **0** (our `G-03`) | NOT-RUN | **PASS** | the canonical package ships no code for this row; ours fills it |
| B-20 captions / top first-word share | CANON | ≤ 0.45 (calibrated) | 26 / 0.31 | **26 / 0.31** (resolved) | NOT-RUN | **PASS** | **0 captions on `prose.tex` → that reading is VACUOUS.** The canonical extractor strips `\textbf` but leaves its brace, so `\textbf{The …}` buckets as `{The` and the top share is **under-counted** |
| B-21a p-value mentions /1000 | CANON | ≤ 2.5 (calibrated) | 0.18 | **0.18** | NOT-RUN | **PASS** | |
| B-21b/c restated enumerations, duplicated per-member statistics | CANON | 0 / 0 | — | **NOT-RUN** | NOT-RUN | **NOT-RUN** | no canonical implementation; our `N-02b` covers the caption-literal part (0) |
| B-22 hedge total /1000 | CANON | ≤ 2, **descriptive only (§A)** | 0.53 | **0.56** | NOT-RUN | **PASS** | the decomposition the row asks for is not implemented canonically |
| B-23 near-duplicate sentence pairs | CANON | 0 outside Abstract/Conclusions recap (calibrated) | 28 | **20** | NOT-RUN | **REVIEW** | −8: the conclusions rewrite removed real duplication |
| B-24 repeated prose 6-grams ≥ 3× | CANON | 0 outside protected terms (calibrated) | 52 | **39** | NOT-RUN | **REVIEW** | −13, same cause |
| B-25 section-shape uniformity | CANON | inspect | — | **NOT-RUN** | NOT-RUN | **NOT-RUN** | no canonical implementation |
| B-26 punctuation deltas vs original | CANON | each ≤ +3 /1000 (calibrated) | abs 7.19/4.35/5.06 | abs **7.15/4.62/5.33** (colon/semicolon/paren) | NOT-RUN | **NOT-RUN** | a delta needs the pre-revision text as `argv[2]`; these absolutes are that baseline |
| B-27 over-correction | CANON | 0 | — | **NOT-RUN** | NOT-RUN | **NOT-RUN** | undefined before an edit exists; no canonical implementation |
| B-28 protected-term scan, zero false flags | CANON (implemented here) | pass (calibrated) | 1 | **1** | NOT-RUN | **REVIEW** | `the real part of the visibility`. The term must enter the project protected list |
| B-29 new-text audit | CANON | no rate worse | — | **NOT-RUN** | NOT-RUN | **NOT-RUN** | the canonical script prints `none / ok` when `original == edited`; that is **vacuous**, not a pass |
| B-30 coined terms /1000; undefined in Abstract | CANON | ≤ 2; 0 (calibrated) | 414 | **415 candidates** | NOT-RUN | **REVIEW — unusable as emitted** | the ≥ 6× 2-gram rule returns `s math`, `sect ref`, `over the`; the real candidates (`control positions` 45, `class a` 46, `drift ceiling`, `primary census`) need the project protected-terms list applied first. **CT-04**: the title's `Spectral-Carrier` is kept with the Ruling 16 keep-reason |
| B-31 emphasis commands /1000 | CANON | ≤ 1, first-use definition exempt (calibrated) | 227 total, **173 body** = 5.12 | **216 total, 162 body = 4.77** | NOT-RUN | **FAIL** | ★ moved as predicted: the ten swept bold phrases are **−11 commands**, all from body prose (captions 43, run-in headings 5, tabular 6 — unchanged). Still 4.8× the threshold; 102 distinct strings, so most of the residue is repeat emphasis, not first-use definition |
| B-32 cross-references /1000 | CANON | ≤ 3 (calibrated) | 292 raw = 8.64 | **310 raw = 9.13** | NOT-RUN | **REVIEW, with a keep-reason (not a rewrite target)** | ★ rose by 18, and the decomposition says why: `\S\ref` 112 → **120**, `Appendix~\ref` 65 → **73**, `Table` 66 → 68, Equation 7 and Figure 5 unchanged. **+16 of the +18 are section and appendix pointers** — the mechanical consequence of moving 2.1 pp of statistics into appendices (Ruling 16/17). Removing pointers to move the metric would make the text worse: **I-7 forbids it.** Separately, the canonical implementation reads **2.06** here, because its regex only counts refs preceded by `Section\|Sect\|Fig\|Table\|equation` and therefore misses all **73** `Appendix~\ref` — a PASS it has not earned |
| B-33 edit budget per section | CANON | ≤ 40 % or author approval (calibrated) | — | **NOT-RUN** | NOT-RUN | **NOT-RUN** | vacuous with `original == edited`; the canonical script prints `0.00 ok` |
| B-34 acronym anomalies | CANON | 0 (calibrated) | 20 names | **20 names** | NOT-RUN | **REVIEW, polluted** | the list contains `MATH CITE REF` (preprocessor placeholders) and the catalogue prefixes `HD HR BD HIP CD CP LP UCAC`, all protected tokens. Real residue `ALMA EIRP SIMBAD CDMS JPL DR CO AU SO`. **Our `RT-03` (15 of 16, with an exempt list) is the better implementation** |
| B-35 text overlap ≥ 12-word runs | CANON | 0 outside quotes (calibrated) | NOT-RUN | **NOT-RUN** | NOT-RUN | **NOT-RUN** | no cited full texts offline; the canonical script declares this itself |
| B-36 segmentation spot-check | CANON | ≤ 2 errors in **50** (calibrated) | 18 of 20 | **16 of 20 "suspicious"** | NOT-RUN | **superseded by our `SG-02`** | the canonical script samples **20**, not 50, and its heuristic flags most of a clean text. `SG-02` printed the 50 the order asks for and found **0** mechanical suspects |
| B-37 manuscript voice distance | CANON | within the author-paper range — **conditional on S-01, which FAILED** | D = 1.037 | **D = 1.067** | NOT-RUN | **REPORT-ONLY** | macro-resolved prose. Worst features `hd:would` z 2.62 (2.64 vs 0.86), `O:in` 1.97, `Zreport` 1.85, `Slong` 1.62 (287 vs 162), `O:however` 1.60 (**0.00** vs 20.55). Through the canonical `preprocess_tex` (macros stripped to nothing) the same text reads **1.205** and `Ssd` explodes to z 4.00 — §T-5.4 settles it on the rendered text. §T-2.3 records S-01 **FAILED** for this profile (holdouts 0.89 vs controls 1.20, tails touch) ⇒ **the voice gate is permanently report-only; no voice number may move a sentence** |
| B-38 voice distance of changed vs unchanged | CANON | not worse | — | **NOT-RUN** | NOT-RUN | **NOT-RUN** | no revision exists |
| §T-4 tell census | CANON | census; verdict never automatic (**uncalibrated**) | — | `rather than` **75** · TRIADS **143** · `not only` **3** · `in summary` **1** · **16 of 20 canonical tells are 0** | NOT-RUN | **CENSUS** | `llm_tells` does not collapse whitespace, so it under-counts line-wrapped tells (3 of 78 here) |
| **C-01 co-occurrence** (§5.10, *the main rewrite trigger*) | CANON (implemented here; **no canonical code exists**) | ≥ 3 distinct IDs in a 4-sentence window ⇒ rewrite; C-03 ≤ P75 (**uncalibrated**) | 127 / 31 / 11 / 6 | **135 / 20 / 11 / 6 of 1,097 windows** | NOT-RUN | **REVIEW — report the band, never one number** | the four values drop the loosest detectors in turn (`P-06` colon-reveal → `P-13` British triads → `P-01`). **Robust core 6–11, unchanged; the widest reading rose by 8** because the relocation added colon-heavy pointer prose. Worst window now **5** distinct IDs (was 4). C-02 352 |
| **T-01 protected-token register as (value, referent) tuples** (§1, §3 item 4) | CANON (implemented here) | diff empty (calibrated) | 1,765 pairs | **1,774 pairs / 593 distinct values** | NOT-RUN | **NOT-RUN (diff undefined on a before-pass)** | the register is built and stored. A bare multiset — which is what the project's own `T-01a` is — **passes a number re-attached to a different referent**; canonical fixture AD-10 demonstrates it |
| §3.5 unit equivalence | CANON (implemented here) | reconcile, never contradict (calibrated) | 2 groups | **2 groups** | NOT-RUN | **PASS** | both printed-precision only (`12 km`/`12.0 km`, `1 GHz`/`1.0 GHz`) |
| §3.5 denominator guard | CANON (implemented here) | distinct denominators never merged (calibrated) | 12 | **12 groups** | NOT-RUN | **CENSUS** | e.g. `41 of 49` vs `41 of 90`; a consistency checker that merged any of these would be wrong |
| §3.6 physics candidates | CANON (implemented here) | flag for the author (**uncalibrated**) | 0 | **1 — NEW** | NOT-RUN | **REVIEW → referee report** | ★ *"…real carbon monoxide at the discovery **flux** would have given … at 11.5 **mJy**"*: a value in mJy is a flux **density**. §3.6's first named distinction. The phrase existed in v4.24 (2 occurrences) but only in v4.25 does it share a sentence with its mJy value, which is what the detector requires |
| AD-1…AD-10 adversarial fixtures | CANON | all pass **before** any revision (calibrated) | 23/23 | **23/23 PASS, exit 0** | re-run after | **PASS** | canonical required outcomes made machine-checkable, each with a control. Our ten detection fixtures: harness live, clean baseline clean, AD-8 and AD-10 fire (spot-check) |

---

## Part B — the 58 project/protocol rows (same instrument as the v4.24 cut, re-run on v4.25)

Generated verbatim by `python3 /workspace/SETI/deai/deai_battery.py /workspace/SETI/paper_20pc/v4.25
--out work/b425_before --pdf …v4.25.pdf --arxiv /workspace/tmp/arxivset --main-finding "…"`.
**Class A rows not passing: 11** (was 13 on v4.24) — `T-01a…f`, `EP-02`, `B-33`, `B-26` are NOT-RUN
for the structural reason that a before-pass has no original; `LX-01c` and `RT-06` now **run**.

### What moved against the v4.24 cut, and why

| row | v4.24 | v4.25 | reading |
|---|---|---|---|
| `N-01` abstract numbers recur in the body | REVIEW, 1 orphan (`3.60`) | **PASS, 0** — all 22 distinct abstract numbers recur | ★ the banked §M item is **resolved and independently re-measured**: the abstract now prints `\AccelCeilMed` (3.60) and §4.2 prints `\AccelCeilMed`, **the same macro and the same value**. `\AccelCeilMin` survives as a definition only (3.60, i.e. a same-value synonym, not a collision) |
| `N-01b` abstract macros reused in the body | REVIEW, 2 (`AccelCeilMin`, `CeTlObsCutWord`) | **PASS, 0** — 30 abstract macros, all reused | same cause |
| `LX-01c` arXiv package sweep | **NOT-RUN** (no package) | **REVIEW, 680** = 4 forbidden-mention lines + **676 comment lines** | ★ now runnable: `arxivset --force` left the package at `/workspace/tmp/arxivset` (215 items). **All 4 "forbidden mentions" are false positives or required content**: an ALMA Technical Note bibitem, the OJA class's own boilerplate, and **two lines of the AI-assistance disclosure itself** — which I-7 forbids removing. The substance is the 676 comments shipped in a source package arXiv publishes; **0 of them mention a round, referee, owner, agent, TODO or version string** |
| `RT-06` → **`MF-01`** main-finding sentence | NOT-RUN (not stored) | **REVIEW** — stored, 1 sentence, **2 numbers** | §3.1 asks for one sentence and *a number with uncertainty or a limit*; the stored sentence has two counts and no uncertainty or limit. Author decision; `T-06` is tested against whatever he settles on. **Row renamed**: canonical `RT-06`/`B-32` is cross-reference density |
| `T4-02` "rather than" | 2.39 | **2.20** /1000 (main+abstract basis) | the whole-prose count is unchanged at 78; the rate falls only because the main text shed words |
| `T4-10` house dash | 6.33 | **5.80** /1000 | same mechanism |
| `T4-11` triadic lists | 1.61 | **1.77** /1000 | up |
| `T-01c` object identifiers | 52 | **42** | 10 object names left the prose with the relocated statistics — a register movement, not a defect, but it is a protected-token change and is recorded as one |
| `T-01d` `\ref` keys | 283 | **301** | the B-32 movement, same cause |
| `LX-01a` comments in the tree | 1,112 | **1,132** | the tree may carry comments; `arxivset.sh` is the gate that matters, and `LX-01c` now measures it |
| `RT-01c` sentences > 40 words | 154 | **139** | the readability pass |
| `RT-02` stumble candidates | 157 | **145** | same |
| `RT-04` paragraphs | 120 at 6.12 sentences | **118 at 5.60** | same |
| `F-NOFUNC` body paragraphs awaiting a purpose statement | 120 | **118** | worksheet re-emitted |
| `RT-03` unexpanded acronyms | 16 of 17 | **15 of 16** | one fewer |
| `MX-01` macro names with two different values | 37 | **37** | ★ unchanged — see `deai_author_decisions.md` §2 (`\CeAddLimNear` vs `\FrNarrowAddLim`) |
| `AB-01` abstract length | 242 / 245 | **243 / 245** | PASS, measured on the page |
| `FARM-01` target tree byte-stable across the wrapped-gate phase | PASS | **PASS** — 994 files copied, 45 symlinked, 0 changed | `chmod a-w` does not stop root; copy-and-snapshot is the only guard that works |
| everything else | — | **unchanged** | `SG-01` `SG-02` PASS · `G-03` 0 · `N-02…N-07` `LX-02` `LX-01b` `LX-07` `AU-01` `I-5` PASS · `EP-01` census |

### The generated table, verbatim


- target   : `/workspace/SETI/paper_20pc/v4.25`
- original : **not supplied** -- every delta row is NOT-RUN with that reason
- flattened by: `manuscript.flat`
- 661 sentences of main+abstract, 487 of appendix, 18614 words, 6055 macros resolved

**Reconstruction notice.** The canonical `DEAI_PAPER_PROTOCOL.md` v3.0, `DEAI_v3_ADDENDUM.md` §A-§T and the canonical `deai_battery.py` / `deai_voice.py` / `adversarial/` are **not on this machine**. Every row below carries a provenance word -- `ORDER` (named with its content in the author's operating order), `INFER` (named there, measurement reconstructed here), `PROJECT` (wraps a gate this paper's build already owns) -- and every threshold the canonical body would have supplied is printed `uncalibrated`. No row is blank; nothing here is a score, an "AI probability" or a watermark claim.

status tally: CENSUS 24, NOT-RUN 11, PASS 18, REVIEW 5

**Class A rows not passing: 11** (T-01a, T-01b, T-01c, T-01d, T-01e, T-01f, EP-02, LX-01c, RT-06, B-33, B-26)

| row | family | measures | cls | prov | before | after | delta | status | threshold (calibrated?) | note |
|---|---|---|---|---|---|---|---|---|---|---|
| `SG-01` | segmentation | abbreviation register honoured by the sentence splitter | A | INFER | 0 | 0 | 0 | **PASS** | no sentence ends on a register abbreviation, and the register is demonstrably exercised (>= 3 entries occur in the text) (calibrated) | bar for this document: >= 3 register entries present (1150 sentences); register 47 entries, 4 of them present in the text (Fig., Sect., Eq., et al.); 0 sentences end on a register abbreviation; 0 further period-abbreviation candidates reported for the human to add if real |
| `SG-02` | segmentation | fifty-sentence boundary check (machine proxy; the order wants a human read) | A | ORDER | - | 0 | - | **PASS** | at most 2 boundary errors in 50 sentences (order); the proxy threshold here is 0 mechanical suspects in the 50 drawn (**uncalibrated**) | 0 mechanical boundary suspects over the whole text, 0 of them inside the fifty drawn; fifty printed to sg02_fifty_sentences.md for the human read the order requires |
| `T-01a` | protected tokens (T-01) | numeric multiset (macro layer resolved, math included) | A | ORDER | - | 2220 | - | **NOT-RUN** | delta against the original must be EMPTY (calibrated) | no <original> supplied: the register holds 2220 tokens and is stored, but a protected-token DIFF is undefined without a before-document |
| `T-01b` | protected tokens (T-01) | citation-key multiset | A | ORDER | - | 101 | - | **NOT-RUN** | delta against the original must be EMPTY (calibrated) | no <original> supplied: the register holds 101 tokens and is stored, but a protected-token DIFF is undefined without a before-document |
| `T-01c` | protected tokens (T-01) | object / catalogue identifiers | A | ORDER | - | 42 | - | **NOT-RUN** | delta against the original must be EMPTY (calibrated) | no <original> supplied: the register holds 42 tokens and is stored, but a protected-token DIFF is undefined without a before-document |
| `T-01d` | protected tokens (T-01) | cross-reference keys (\ref) | A | ORDER | - | 301 | - | **NOT-RUN** | delta against the original must be EMPTY (calibrated) | no <original> supplied: the register holds 301 tokens and is stored, but a protected-token DIFF is undefined without a before-document |
| `T-01e` | protected tokens (T-01) | label keys (\label) | A | ORDER | - | 71 | - | **NOT-RUN** | delta against the original must be EMPTY (calibrated) | no <original> supplied: the register holds 71 tokens and is stored, but a protected-token DIFF is undefined without a before-document |
| `T-01f` | protected tokens (T-01) | macro-use multiset (this paper's numbers live here) | A | ORDER | - | 1913 | - | **NOT-RUN** | delta against the original must be EMPTY (calibrated) | no <original> supplied: the register holds 1913 tokens and is stored, but a protected-token DIFF is undefined without a before-document |
| `T4-01` | LLM-tell census (§T-4) | contrastive reframe "not X but Y" | B | ORDER | - | 0.16 | - | **CENSUS** | census only -- rate reported, verdict NEVER automatic (**uncalibrated**) | 3 instances, 0.16 per 1000 words; the order names this first among this pipeline's habits |
| `T4-02` | LLM-tell census (§T-4) | "rather than" | B | ORDER | - | 2.2 | - | **CENSUS** | census only -- rate reported, verdict NEVER automatic (**uncalibrated**) | 41 instances, 2.20 per 1000 words; named in the order |
| `T4-03` | LLM-tell census (§T-4) | "not only ... but" | B | ORDER | - | 0.0 | - | **CENSUS** | census only -- rate reported, verdict NEVER automatic (**uncalibrated**) | 0 instances, 0.00 per 1000 words; named in the order |
| `T4-04` | LLM-tell census (§T-4) | trailing participial gloss ", suggesting/underscoring/..." | B | ORDER | - | 0.0 | - | **CENSUS** | census only -- rate reported, verdict NEVER automatic (**uncalibrated**) | 0 instances, 0.00 per 1000 words; the order names ", suggesting" explicitly; the rest are its family |
| `T4-05` | LLM-tell census (§T-4) | "it is worth noting" / "it should be noted" | B | ORDER | - | 0.0 | - | **CENSUS** | census only -- rate reported, verdict NEVER automatic (**uncalibrated**) | 0 instances, 0.00 per 1000 words; named in the order |
| `T4-06` | LLM-tell census (§T-4) | sentence-initial "Importantly/Notably/Crucially/Interestingly" | B | ORDER | - | 0.0 | - | **CENSUS** | census only -- rate reported, verdict NEVER automatic (**uncalibrated**) | 0 instances, 0.00 per 1000 words; "importantly" and "crucially" are named; the rest are the same adverb slot |
| `T4-07` | LLM-tell census (§T-4) | "serves to" / "serves as" | B | ORDER | - | 0.0 | - | **CENSUS** | census only -- rate reported, verdict NEVER automatic (**uncalibrated**) | 0 instances, 0.00 per 1000 words; named in the order |
| `T4-08` | LLM-tell census (§T-4) | "plays a (key/crucial) role" | B | ORDER | - | 0.0 | - | **CENSUS** | census only -- rate reported, verdict NEVER automatic (**uncalibrated**) | 0 instances, 0.00 per 1000 words; named in the order |
| `T4-09` | LLM-tell census (§T-4) | "in terms of" | B | ORDER | - | 0.0 | - | **CENSUS** | census only -- rate reported, verdict NEVER automatic (**uncalibrated**) | 0 instances, 0.00 per 1000 words; named in the order |
| `T4-10` | LLM-tell census (§T-4) | em/en-dash pairs in running prose | B | ORDER | - | 5.8 | - | **CENSUS** | census only -- rate reported, verdict NEVER automatic (**uncalibrated**) | 108 instances, 5.80 per 1000 words; the order asks for em-dash DENSITY; this paper uses " -- " as its house dash, 237 times in v4.24, so the rate is reported and never flagged |
| `T4-11` | LLM-tell census (§T-4) | triadic list "A, B and C" | B | ORDER | - | 1.77 | - | **CENSUS** | census only -- rate reported, verdict NEVER automatic (**uncalibrated**) | 33 instances, 1.77 per 1000 words; named in the order as "triadic lists" |
| `T4-12` | LLM-tell census (§T-4) | hollow intensifier ("very", "quite", "extremely", "highly") | B | INFER | - | 0.16 | - | **CENSUS** | census only -- rate reported, verdict NEVER automatic (**uncalibrated**) | 3 instances, 0.16 per 1000 words; INFER: not named, but it is the same register as the named families; report-only |
| `T4-13` | LLM-tell census (§T-4) | "a testament to" / "underscores the importance" | B | INFER | - | 0.0 | - | **CENSUS** | census only -- rate reported, verdict NEVER automatic (**uncalibrated**) | 0 instances, 0.00 per 1000 words; INFER: the strongest form of the T4-04 gloss |
| `T4-14` | LLM-tell census (§T-4) | short dramatic paragraph closers | B | ORDER | - | 3 | - | **CENSUS** | census only; a closer under 9 words carrying no number (**uncalibrated**) | each instance needs a keep-reason on the RV-01 ladder |
| `F-NOFUNC` | paragraph function | paragraphs whose purpose must be stated in one clause | B | ORDER | - | 118 | - | **NOT-RUN** | every body paragraph has a stated purpose; the statement is a human act, so the machine emits the worksheet (**uncalibrated**) | worksheet emitted for 118 body paragraphs (f_nofunc_worksheet.md); the purpose statements are the audit stage's work, not the battery's |
| `G-03` | paragraph function | closing gloss: a final sentence that only restates its paragraph | B | ORDER | - | 0 | - | **PASS** | content-word overlap >= 50 per cent with the paragraph, no number/citation/ref of its own, and a gloss opener (**uncalibrated**) | 0 candidate glosses; each is adjudicated, not auto-cut |
| `N-01` | numerical consistency | abstract numbers all present in the body | A | INFER | - | 0 | - | **PASS** | every numeric token in the abstract occurs in the body (macro-resolved) (calibrated) | all 22 distinct abstract numbers recur in the body |
| `N-01b` | numerical consistency | abstract macro uses all recur in the body | A | INFER | - | 0 | - | **PASS** | every macro used in the abstract is also used in the body (calibrated) | 30 macros in the abstract, all reused in the body |
| `N-02b` | numerical consistency | caption numbers come from the macro layer | B | INFER | - | 0 | - | **CENSUS** | a numeric literal in a caption that is not a macro value is a typed number, which this paper forbids (**uncalibrated**) | 0 caption literals with no matching macro value (many will be panel labels and powers of ten -- adjudicate, do not cut) |
| `N-04` | numerical consistency / hygiene (wrapped) | audit_numbers_v385.py -- every printed number re-derived from its source of truth | A | PROJECT | - | 0 | - | **PASS** | the gate's own exit status (0 = pass) (calibrated) |   warn     figure built but never \includegraphics: stratified_completeness.pdf dead output in the release deposit /   warn     star in tab_nearest_r21.tex not in SIMBAD form HD14055 HD 14055 /   warn     star in tab_nearest_r21.tex not in SIMBAD form HD170773 HD 170773 /   warn     star in tab_near |
| `N-03` | numerical consistency / hygiene (wrapped) | prosenum_v399.py -- a number typed in the prose that disagrees with its macro | A | PROJECT | - | 0 | - | **PASS** | the gate's own exit status (0 = pass) (calibrated) | prosenum: 0 literal(s) disagreeing with a macro |
| `N-05` | numerical consistency / hygiene (wrapped) | consistency_v399.py -- macro-to-macro arithmetic identities | A | PROJECT | - | 0 | - | **PASS** | the gate's own exit status (0 = pass) (calibrated) | frozen            12 = 11 + 1  OK /   radius-corrected  11 = 10 + 1  OK /   primary statistic   no explicit claim found /   abstract uses      neither /   attribution scope   8 sentence(s) give the mask half-width about the star; 0 attribute at its velocity alone / consistency_v399: 0 problem(s) |
| `N-06` | numerical consistency / hygiene (wrapped) | xrefcheck.py -- every \ref resolves | A | PROJECT | - | 0 | - | **PASS** | the gate's own exit status (0 = pass) (calibrated) |     sec:data                     -> 7 /     sec:discussion               -> 6 /     sec:intro                    -> 1 /     sec:newspace                 -> 6.2 /     sec:results                  -> 5 /   SHARED ANCHORS (deliberate aliases are fine): 0 |
| `N-07` | numerical consistency / hygiene (wrapped) | citegate.py -- every citation key resolves | A | PROJECT | - | 0 | - | **PASS** | the gate's own exit status (0 = pass) (calibrated) |   G1   every bibitem is cited somewhere                               PASS  none /   G2   every citation has a bibitem                                   PASS  none /   G3   no key is declared twice                                       PASS  none /   G4   the comparison was not vacuous               |
| `N-02` | numerical consistency / hygiene (wrapped) | macrosyn.py -- a macro whose value disagrees with its synonym | A | PROJECT | - | 0 | - | **PASS** | the gate's own exit status (0 = pass) (calibrated) |   [open]    \VisMaxReSig = 2.5; \FitUnattMaxAbs = 0.93 -- owner: retire visfit_v385_calc.py; repoint visgain_v399.py at ledger_v403 /   [open]    \SelTransFineLo = \EirpNinetyFacLo; \StratTransferNineLo = 0.48 -- owner: R2-M3.3: one transfer bracket, from the M3a campaign /   [open]    \SelTransFine |
| `LX-02` | numerical consistency / hygiene (wrapped) | macroleak.py -- a macro name leaking into the typeset page | A | PROJECT | - | 0 | - | **PASS** | the gate's own exit status (0 = pass) (calibrated) | macroleak: 0 problem(s) |
| `AB-01` | numerical consistency / hygiene (wrapped) | abswords.py -- abstract word count against the limit | B | PROJECT | - | 0 | - | **PASS** | the gate's own exit status (0 = pass) (calibrated) | abswords: 243 words in the typeset abstract of technosignatures_40pc_v4.25.pdf (limit 245) /   OK one paragraph, within the limit, measured on the page |
| `FARM-01` | instrument integrity | the wrapped gates wrote nothing into the target tree | A | INFER | - | 0 | - | **PASS** | 0 files in the target tree changed size or mtime while the wrapped gates ran (calibrated) | farm: 994 files copied, 45 symlinked; the target tree is byte-stable across the gate phase |
| `MX-01` | numerical consistency | one macro name carrying two different values | B | INFER | - | 37 | - | **REVIEW** | 0 names with two distinct non-empty definitions (calibrated) | 37 names redefined to a DIFFERENT value across the 185 macro files (the `\providecommand{}{}\renewcommand{}{v}` idiom is not counted); several are deliberate round-to-round aliasings, so this is a REVIEW list, not a failure |
| `EP-01` | epistemic ladder | every claim classified observed / inferred / conjectured | B | ORDER | - | 37 | - | **CENSUS** | census; an unclassified sentence is a sentence the ladder cannot see, and its count is the honest limit of this row (**uncalibrated**) | observed 74 / asserted 917 / inferred 92 / conjectured 30 / unclassified 37 of 1150 sentences (the ladder is conjectured < inferred < asserted < observed; an "asserted" sentence states a fact without saying how it is known, and "unclassified" means no finite verb -- a fragment or a run-in heading) |
| `EP-02` | epistemic ladder | no sentence climbs the ladder relative to the original | A | ORDER | - | - | - | **NOT-RUN** | 0 climbs (calibrated) | no <original> supplied: a climb is defined only against a before-document |
| `LX-01a` | hygiene | comments left in the shipped source (arXiv ships the source) | B | ORDER | - | 1132 | - | **CENSUS** | 0 comments in the arXiv package; the version tree itself may carry them because `arxivset.sh` strips them (calibrated) | 1132 commented source lines in the tree. This is NOT a failure of the tree: `arxivset.sh` strips comments from the submission copies and proves the strip changes no output byte. The arXiv-package row is LX-01c. |
| `LX-01b` | hygiene | model / agent / version / round / referee / TODO mention in the TYPESET page | A | PROJECT | - | 0 | - | **PASS** | genai_sweep.py exit 0 against its allow-list (calibrated) |   [raw] assertion                    / That this sample is indepen- dent of the choice of statistic and of mask is an assertion of ours and not something a reader can check. /   [p27] assertion                    / That this sample is independent of the choice of statistic and of mask is an assertio |
| `LX-01c` | hygiene | the same sweep over the arXiv PACKAGE (source ships) | A | ORDER | - | 680 | - | **REVIEW** | 0 comments and 0 forbidden mentions in the package (calibrated) | 4 forbidden-mention lines and 676 comment lines in the package |
| `LX-07` | hygiene | PDF metadata carries no model / agent / round / version mention | A | ORDER | - | 0 | - | **PASS** | 0 forbidden mentions in Title/Author/Subject/Keywords/Creator/Producer (calibrated) | 41 pp; fields creator,producer clean |
| `AU-01` | hygiene | title block carries the authors correctly | A | ORDER | - | 2 | - | **PASS** | G. J. White present; ORCID 0000-0002-7126-691X if the class prints one (calibrated) | title block found (3 commands): White True, Dey True; ORCID 0000-0002-7126-691X in the source: False (the class may not typeset an ORCID -- that is a REVIEW point for the author, not a failure of the block) |
| `I-5` | stop conditions | [[TBD]] / TODO / FIXME markers in the source | A | ORDER | - | 0 | - | **PASS** | 0 markers -- the order says STOP and report, never guess (calibrated) | no markers |
| `RT-01a` | reader tests | mean words per sentence | B | ORDER | - | 28.16 | - | **CENSUS** | uncalibrated (no discipline corpus on this machine) (**uncalibrated**) | report-only: the order supplies no numeric threshold and no corpus exists here to fit one |
| `RT-01b` | reader tests | 90th-percentile sentence length | B | ORDER | - | 50 | - | **CENSUS** | uncalibrated (**uncalibrated**) | report-only: the order supplies no numeric threshold and no corpus exists here to fit one |
| `RT-01c` | reader tests | sentences over 40 words | B | ORDER | - | 139 | - | **CENSUS** | uncalibrated (**uncalibrated**) | report-only: the order supplies no numeric threshold and no corpus exists here to fit one |
| `RT-01d` | reader tests | Flesch reading-ease proxy | B | ORDER | - | 44.5 | - | **CENSUS** | uncalibrated; a PROXY (syllables are estimated by vowel groups) (**uncalibrated**) | report-only: the order supplies no numeric threshold and no corpus exists here to fit one |
| `RT-01e` | reader tests | passive constructions per 1000 words | B | ORDER | - | 11.34 | - | **CENSUS** | uncalibrated (**uncalibrated**) | report-only: the order supplies no numeric threshold and no corpus exists here to fit one |
| `RT-01f` | reader tests | nominalisations per 1000 words | B | ORDER | - | 34.38 | - | **CENSUS** | uncalibrated (**uncalibrated**) | report-only: the order supplies no numeric threshold and no corpus exists here to fit one |
| `RT-02` | reader tests | stumble candidates | B | ORDER | - | 145 | - | **REVIEW** | candidates for a human read; no numeric threshold (**uncalibrated**) | 145 candidates; the order's RT-02 is a reader's stumble log, so this list feeds that read rather than replacing it |
| `RT-03` | reader tests | acronym used but never expanded | B | INFER | - | 15 | - | **REVIEW** | 0 unexpanded acronyms outside the exempt list (**uncalibrated**) | 15 of 16 acronyms never parenthetically expanded: ASIAA, CDMS, CDS, HIP, JAO, KASI, MCC, MWA, NINS, NRC |
| `RT-04` | reader tests | paragraph length profile | B | INFER | - | 5.6 | - | **CENSUS** | report-only (**uncalibrated**) | 118 body paragraphs, mean 5.60 sentences, 6 one-sentence paragraphs, longest 25 |
| `RT-05` | reader tests | section openings state the section's point | B | ORDER | - | 10 | - | **NOT-RUN** | worksheet for the human read (**uncalibrated**) | openings listed for 10 sections in rt05_openings.md; whether an opening states the point is a reader's judgement |
| `RT-06` | reader tests | the stored main-finding sentence (for the later fresh-agent T-06 test) | A | ORDER | - | 2 | - | **REVIEW** | exactly one sentence, one number, one decisive observation (calibrated) | stored (author-supplied): 1 sentence(s), 2 number(s). the order asks for ONE sentence and ONE number; adjudicate |
| `B-33` | edit budget | fraction of body sentences changed, per section | A | ORDER | - | - | - | **NOT-RUN** | > 40 per cent in ANY section stops the run (calibrated) | no <original> supplied: an edit budget is undefined without a before-document |
| `B-26` | convergence | measured delta against the original | A | ORDER | - | - | - | **NOT-RUN** | both columns present for every row (calibrated) | no <original> supplied: this is a BEFORE-pass table only, which is exactly what the order wants written before any edit |

## Status vocabulary

- `PASS` / `FAIL` -- a threshold that exists and was met / missed.
- `CENSUS` -- counted and reported; **the order forbids an automatic verdict** for this family.
- `REVIEW` -- instances exist and are adjudicated on the RV-01 preserve-first ladder, each with a keep-reason.
- `NOT-RUN` -- could not be sourced or needs an input that is absent; the reason is in the note. **Never a pass.**
- `STOP` -- the order says halt and report to the author.

---

## Provenance and calibration summary

- **Provenance**: `CANON` 38 rows (the canonical body and its three scripts), `ORDER` 39, `INFER` 10,
  `PROJECT` 9 (eight wrapped project gates + `genai_sweep`). A row may carry two words where the
  canonical row and a project gate measure the same thing; the project gate wins on numbers because
  it re-derives them from their source of truth.
- **Calibrated**: 32 canonical rows now carry a real threshold (see `CANON_ALIGNMENT.md` §9).
- **Still uncalibrated, with the reason printed in the row**: `RT-01d/e/f` (the canonical body
  supplies no number), **C-03** (needs the discipline corpus' P75), every "> P90" clause in §5.1–§5.8
  (no corpus on this machine), the voice band endpoints (the profile arrived without its
  175-document corpus; only §T-2.3's published means 0.89 / 1.20 exist), B-16 and the §T-4 census
  (census by instruction).
- **Class A rows not passing: 11**, every one of them `NOT-RUN` for a structural reason stated in its
  own note, or `REVIEW` with its instances listed. **No Class A row FAILS on evidence.**
- **Class B rows out of range: B-01 (real reading), B-04, B-05, B-14, B-17, B-18b, B-31, B-32, B-07,
  B-23, B-24, B-28, C-01.** Each must end *resolved or adjudicated with a written keep-reason* (§A),
  and under **I-7** none may be forced into range by making the text worse.

## What this before-pass authorises, and what it does not

It authorises Stage 4 (the controlled revision) to begin — execution contract #1 is satisfied, and
the adversarial fixtures pass, which is the order's precondition. It does **not** authorise any
change to a number, a claim's strength, a citation, or a scientific statement: those are in
`deai_audit_report.md`, `deai_referee_report.md` and `deai_author_decisions.md`, and under **§M**
they are **never** resolved by rewording.
