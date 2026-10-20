# `deai_audit_report.md` — DEAI pass on v4.25, both cycles

`deai-close`, 2026-10-20. Supersedes the cycle-1 report of 19:59 UTC, which is kept verbatim as
`deai_audit_report_cycle1.md`. Cycle 1 = Stage 4 (`deai-revise`); cycle 2 = this file's own edits,
ordered by Coordinator Rulings 20 and 21 after `deai-verify`'s Stage-5 gates. §4 of the protocol
permits three cycles; two were used.

---

## 1. THE HEADLINE, AND IT IS AGAINST US

**Cycle 1's dominant edit relabelled a construction instead of reducing it, and the unwidened row
would have told the author the opposite.**

`B-05` is a real PASS: *rather than* fell **75 → 17** on `prose.tex`, zero in the main text. But the
construction did not leave the paper — it changed marker:

| measured on `prose.txt` (canonical `mkinputs.py`) | before the pass | after cycle 1 | **after cycle 2** |
|---|---|---|---|
| `rather than` | 75 | 17 | **17** |
| `and not X` | 69 | **111** | **103** |
| `, not X` | 12 | 13 | **11** |
| `instead of` | 4 | 9 | **9** |
| `as opposed to` | 0 | 0 | 0 |
| **contrastive family, total** | **160** | **150** | **140** |
| sentences carrying one | 162 / 1 100 | 154 / 1 101 | **148 / 1 101** |
| P-01 sentences, canonical regex | 91 | 36 | **34** |
| P-01 sentences, widened by `and not` | 160 | 148 | **142** |
| **C-01 windows, canonical** | 135 | 78 | **71** |
| **C-01 windows, widened by `and not`** | **203** | **194** | **186** |

`P-01`'s own canonical definition already carries `X, not Y`; `X and not Y` is that construction
with a conjunction, so adding it to the regex is faithful to the clause rather than a stretch of
it. **On the faithful reading cycle 1 moved the protocol's main rewrite trigger by 4 per cent, not
by the 42 per cent the unwidened row reports**, and `and not` at 111 uses had become the paper's
single most frequent contrastive formula where *rather than* (75) used to be — more concentrated,
not less. Cycle 2 takes the pair to **203 → 186 (−8.4 %)** and the family to **160 → 140
(−12.5 %)**. Both numbers are the honest ones and both are in this table; neither is in a footnote.

★ The revision never made the paper *worse* on this family: every widened measure moved the right
way at every step. The defect was in the **record**, and a record that would have misled the author
is what this protocol exists to prevent. This is the fifth gate in this build caught pinning a form
of words rather than a fact, after `absreq` B5 and B7 and `censusacct` A4; `LX-01c` (§4 below) is
the sixth.

## 2. WHAT CYCLE 2 ACTUALLY DID TO THE FAMILY, INSTANCE BY INSTANCE

166 instances live in the hand-written sections (comments excluded — a comment is never typeset);
100 of them in the main text, 66 in the appendices. Each was adjudicated on the RV-01 ladder with
*delete the contrast* preferred over *swap its marker*, and the budget (B-33) was a stop, not a
target. **12 were removed. The criterion was the brief's: a contrast earns its place when both
limbs carry information a reader needs, and does not when the second limb only denies the first.**

| # | file | removed | why it did not earn its place |
|---|---|---|---|
| CF1 | `01_intro` | `follow-up ~~and not strength alone~~` | *strength alone* repeats *and not brightness* nine words earlier in the same sentence |
| CF2 | `02_background` | `a $d^{2}$ effect ~~and not an instrumental one~~` | a $d^{2}$ effect is geometric by construction; the denial is entailed |
| CF3 | `03_sample` | `a quality cut that is physical ~~and not chosen~~` → *a physical quality cut* | *physical* already excludes *chosen* |
| CF4 | `04_method` | `a flag ~~and not a disposal~~, so all crossings continue past it` | the `so` clause states the denial |
| CF5 | `04_method` | `an attribution ~~and not an exclusion~~, and every crossing goes on to the recurrence test` | ditto, and it was the second contrast in one sentence |
| CF6 | `04_method` | `at the stellar coordinates ~~and not elsewhere in the field~~` | the second limb is the complement of the first |
| CF7 | `05_results` | `would be lower~~, not higher~~` | pure denial |
| CF8 | `05b_stack` | `would dilute ~~and not reinforce~~` | *dilute* excludes *reinforce* |
| CF9 | `06_discussion` | `a recovery completeness ~~and not a probability of confirmation~~: confirmation requires a second epoch` | the colon clause states it, and the same pair is stated in §5 and §7 |
| CF10 | `05_results` | `concentrated~~, not general~~, which is why…` | *concentrated* excludes *general* |
| CF11 | `04_method` | `and not one of the 38 holds a crossing` → `and **none** of the 38` | **not a contrast at all**: a conjoined negation the regex counts as one |
| CF12 | `05_results` | `and not one of them outranks` → `and **none** of them outranks` | the same; the edit makes the sentence say what it meant |

**The other 154 are kept, and here are the keep-reasons, by class** (RV-01 defaults to preserve;
P-01's own clause exempts *a technically essential distinction*):

1. **The claim-distinguishing pair (≈70 instances).** *a trigger threshold and not a detection
   significance*; *an attribution and not an exclusion*; *untested and not excluded*; *a flag and
   not a disposal*; *consistency and not a demonstration that the crossings are noise*; *a
   non-detection and not an exclusion*; *a ranking filter and not a significance test*; *a bound
   and not a clearance*; *a budget and not a measurement*; *a weak statement and not a strong one*.
   In a null-result paper the second limb names the specific claim a reader would otherwise infer,
   and naming it is the scientific content. Deleting these would weaken the paper's epistemic care,
   which is the one thing four rounds of refereeing have been spent building.
2. **The two-candidate-cause pair (≈35).** *the short track and not the channel width*; *a
   $d^{2}$ effect and not an instrumental one* (where it is not entailed); *by interstellar gas and
   not by a point source*; *the threshold and not the archive*; *the catalogue and not the sky*;
   *the window and not the star*; *coverage and not collecting area*. Both limbs are live
   hypotheses in the sentence's own context and the sentence exists to choose between them.
3. **Terms of art (≈12).** *necessary and not sufficient*; *stated and not folded in*; *reported,
   not acted on*; *for some systems and not others*; *coherent in frequency trajectory, not in
   electric-field phase*. These are fixed phrases; substituting a marker would obscure them.
4. **Counterfactual `instead of` (9).** *at its own measured factor instead of the class average*;
   *moves a carrier's dwell time between channels instead of destroying coherence inside one*.
   These compare a chosen procedure with an unchosen one and are not contrastive reframes.
5. **`rather than` (17, all in appendices).** Already adjudicated in cycle 1 with written
   keep-reasons; nothing in the main text.

★ **This is the honest answer and it is a small number.** The brief asked for the family to be
reduced as a family and it was, by 12.5 per cent over the two cycles. It was not reduced further
because the remaining instances pass the test the brief set, not because the budget ran out:
B-33's worst section, re-measured on the final build against the before-cut, is the Abstract at
**25.0 per cent** (3 of its 12 sentences) and no section exceeds 40 per cent
(`deai_b33_edit_budget.json`); the main-text sections sit far below it.

## 3. WHERE THE REMAINING C-01 ACTUALLY LIVES — and this changes what the number means

C-01 counts 4-sentence windows in which ≥3 distinct feature IDs fire. Decomposing the 186:

| the firing set | windows |
|---|---|
| **P-01 + P-06 + P-13** | **133** |
| P-06 + P-13 + S-02 | 19 |
| P-01 + P-06 + S-02 | 15 |
| P-01 + P-06 + P-13 + S-02 | 13 |
| everything else | 6 |

**Seventy per cent of the paper's C-01 is one combination: a contrast, a colon and a three-item
list.** P-06 is `[a-z]: [a-z]` — any lower-case colon — and P-13 is any three-item comma list. In
this paper those two fire overwhelmingly on *measured* content: a colon introducing an enumeration
of values, a comma list of stars or of numbers. So I re-ran C-01 with P-06 restricted to colons
that do **not** introduce a number, symbol, citation or cross-reference, and P-13 to lists with no
measured item in them — which is P-13's own written clause (*a three-part list whose length is set
by content, not rhythm, is kept*):

| | before the pass | after cycle 1 | after cycle 2 |
|---|---|---|---|
| C-01, widened | 203 | 194 | **186** |
| C-01, widened, with P-06/P-13 adjudicated as above | **59** | 52 | **48** |

★ **And this is the most important methodological statement in the report.** Of the four detectors
that produce this paper's C-01, **three (P-06, P-13, S-02) are thresholded at a corpus percentile
that this installation does not have** — the false-positive calibration corpus is NOT-RUN under §Q,
the protocol's own principal outstanding validation debt. Only P-01 carries an absolute ceiling
(max 1). So the number 186 is not comparable with anything; what is comparable is the direction it
moved, and the composition above. **Chasing it lower would mean deleting colons that introduce
measured values and lists whose length is set by the data** — W-01 run backwards. The pass stopped
instead, and says so.

## 4. GATES THAT FAIL ON A CORRECT TREE, AND THE ONE THAT PASSED ON A WRONG ONE

- **`B-29` is recorded REVIEW, not FAIL, with its confound stated.** RV-03 compares rewritten with
  unchanged sentences; on the widened P-01 the rewritten set reads **13.69 / 1000** against the
  unchanged set's 3.25, which is 4.2× worse and a FAIL as specified. But **the same sentences
  measured 16.32 / 1000 before the pass**: the edited set is exactly the set that carried the
  feature, so the denominator is chosen by the treatment. A 16 per cent improvement reported as a
  failure is not evidence of over-correction. Both numbers are printed in `deai_battery.md`.
- **`LX-01c` fails on a correct tree.** The authors' 222 `.tex` contain **zero** comments with text
  and 34 bare `%` line-joiners that are semantically required; the 676 comment lines are
  `openjournal.cls` (295) and `epsf.sty` (380), third-party files arXiv must receive verbatim; and
  all four "forbidden mentions" are false positives, two of them the **mandated** AI-assistance
  disclosure. Status: **NOT-A-DEFECT**.
- ★★ **And the asymmetry is the finding**: that sweep fired on everything in the package except the
  thing that mattered. **194 of the 222 `.tex` shipped to arXiv carried a version or round string
  in their names, 180 of them the literal word `round`**, plus 188 published lines of
  `\input{survey_numbers_roundNN}` — and `round` inside `round23` has no word boundary, so the
  regex saw none of it. Closed in the packaging step; see §6.
- ★★★ **A sixth blind spot, found in this cycle: four live pseudo-clefts survived a hard-zero
  check.** P-05 is 0 both canonically and on the project's own widened detector, and yet the paper
  still read *"What else makes the band hard belongs to the archive…"*, *"What looked like a
  property of band edges is one interstellar cloud"*, *"What takes the place of an assumption here
  is the requirement"* and a subsection titled *"What the recurrence statistic reads when nothing
  is there"*. The canonical regex requires `What` + one or two words + `is`; the project's widened
  one allows four words and four copulas. All four of these exceed both — one of them because its
  copula is *belongs*. All four are rewritten (§5). **P-05 is now zero on a detector that allows
  any number of intervening words and any copula.**
- **`T4-14`'s +1 short dramatic closer is a false flag**: *"The single-epoch limit, 1.5 × 10^15 W,
  applies at any inclination"* carries a measured value and a unit, which S-02 exempts.
- **S-02's 45 "short dramatic sentences" include 13 section headings and enumerated list labels**
  (*Author contributions.*, *Use of generative artificial intelligence.*, *First, clustering in sky
  frequency.*). A heading is not a sentence; the segmentation (§L, SG) puts them in the stream and
  the rule has no exemption for them. Reported, not edited.

## 5. THE CLAIM THAT CAME BACK (Ruling 21)

Cycle 1 removed a hard-zero pseudo-cleft from the Abstract and the Conclusions and, with it,
changed a **categorical** claim into a **comparative** one:

| | before | cycle 1 | **cycle 2** |
|---|---|---|---|
| `abstract` | *What limits the search is coverage, not depth* | *Coverage limits this search more than depth does* | *Coverage limits this search: **21** systems have no repeat at a covered frequency, where no depth could have produced a confirmation.* |
| `07_conclusions` | *What limits this search is coverage and not depth* | *Coverage limits this search more than depth does* | *Coverage limits this search, and no depth of observation could have removed that limit.* |

For the systems with no repeat at any searched frequency **no depth of observation whatever could
have produced a confirmation**, and the Conclusions sentence immediately before says so. A
comparative sentence understates our own result. The new wording is categorical, carries a limiting
verb, and is neither a pseudo-cleft nor an `X, not Y` reframe; `absreq` B7's rewritten invariant
(one sentence naming coverage **and** depth under a limiting verb) was checked, not assumed, and
passes. **The Abstract absorbed it inside the ceiling by merging the sentence that already carried
the same count**: 243 → **244 words of 245**, 1 572 characters in the ASCII field of 1 920.

The four pseudo-clefts of §4 were rewritten in the same batch: *The band's other difficulties
belong to…*; *That near-edge excess is one interstellar cloud*; *A requirement takes the place of
an assumption here, and it is stated:*; and the subsection becomes *The recurrence statistic under
the null*. One further edit, two words long, removed the paper's **only** stock frame: *Taken
together,* opened a sentence that fired **P-10, P-11 and G-03 simultaneously** and was the sole
instance of each in the paper. Deleting it cleared **four** C-01 windows — the highest yield per
character in either cycle.

## 6. THE RECORD, WHICH IS WHAT BOTH BLOCKERS WERE ABOUT

- **`ARXIV_UPLOAD.md` pinned the superseded build** (md5 `4dcb008f…`, 21.85 pp, 1562/1564
  characters, 30 underfull boxes) — the fifth stale measurement in that one file. It is rewritten
  to carry **no measurement at all**, naming instead the command that prints each number and the
  verdict each must give, and a new gate **`arxivpin`** holds that property (5 clauses, each
  demonstrated firing, plus a control proving a number inside a code span is a command and not a
  claim). Pinning the four numbers was rejected: it would have made the sixth gate here to pin a
  literal instead of a fact.
- **The arXiv package is now neutral, and it is proved rather than asserted.** `arxivset.sh` gained
  **A15**: the 188 macro files are inlined into one `numbers.tex` (their preamble `\input` run is
  asserted contiguous first), 4 608 dead definitions are pruned from it, 13 other `.tex` and one
  figure lose their version tokens, the manuscript becomes `ms.tex`, every `\input` and
  `\includegraphics` is rewritten, and A15 then **fails the run** if any package path or any body
  text outside the journal's own class and style still carries such a string. **222 source `.tex`
  → 35 package `.tex`; 53 items; A8 byte-identical.**
- ★★★★ **And the PDF itself carried one, where no text sweep could reach it.** pdfTeX writes
  `/PTEX.FileName` into the XObject dictionary for every included PDF figure, so the shipped file
  held eleven local build paths — among them `./figures/chain_v412.pdf`, the only occurrence of
  `_v4` anywhere in the binary. `pdftotext` cannot see a dictionary entry, so every text sweep in
  this build passed a PDF that named an internal revision. `\pdfsuppressptexinfo=-1` removes all
  eleven. The companion `\pdftrailerid` pin removes the other obstacle: pdfTeX derives the trailer
  `/ID` from an MD5 of the **output filename**, so before it a renamed build differed in exactly 32
  hex digits and a neutral package name and A8's byte proof were mutually exclusive. With both
  pins the PDF is a function of its source alone.

## 7. THE MAIN FINDING, AND THE SCORES THAT ARE NOT SCORES

**Main-finding sentence (T-06, upgraded on Ruling 20 to the blind reader's, which beat the stored
one):** *No confirmed narrowband carrier is found: of 56 threshold crossings 18 are attributable to
molecular lines and the 31 remaining unattributed ones are consistent with the 24.6 predicted by
the fields' own control positions (P = 0.13), while none of the 33 testable crossings recurred —
setting a typical single-epoch completeness limit of 1.5 × 10^15 W EIRP for the median system, with
coverage (21 systems have no repeat epoch) limiting the search more than depth.* A fresh blind
reader produced it from the Abstract, §1 and the Conclusions alone, and supplied the two things the
coordinator's stored sentence was flagged as lacking.

**No 0–100 score, no "AI probability", and no watermark claim is emitted anywhere in this pass**
(§R). DEAI measures human-visible stylistic distributions; it cannot detect, measure or certify the
removal of a key-based watermark, and a gate claiming otherwise would be unverifiable by
construction. Every verdict in `deai_manifest.md` is a status word.

**Severity-1 findings: none open.** Severity-2 findings are SF-1 (§1, closed by measurement and
disclosure), SF-6 (§5, closed by Ruling 21) and the two blockers (§6, closed with proof). Items
left to the author are in `deai_author_decisions.md`; items that are refereeing rather than editing
— and so may never be resolved by rewriting a sentence — are in `deai_referee_report.md`.

---

## 8. THE MERGED BEFORE/AFTER BATTERY TABLE, VERBATIM

Reproduced exactly as `deai_battery.py` wrote it into [`deai_battery.md`](deai_battery.md) on the
final build (PDF md5 `b99f8cc90abae9794fdb6cc54a298e21`, package `/workspace/tmp/arxivset`).
`before` is the before-cut at [`work/rev425/orig_tree`](/workspace/SETI/deai/work/rev425/orig_tree);
`after` is this tree. Nothing here is a score, an "AI probability" or a watermark claim (§R).

# `deai_battery.md` -- before/after (measured delta, B-26) pass

- target   : `/workspace/SETI/paper_20pc/v4.25`
- original : `work/rev425/orig_tree`
- flattened by: `manuscript.flat`
- 661 sentences of main+abstract, 488 of appendix, 18545 words, 6034 macros resolved

**Provenance notice.** The canonical package IS on this machine -- `/shared/deai/DEAI_PAPER_PROTOCOL.md` v3.0, `DEAI_v3_ADDENDUM.md` §A-§T and the canonical `deai_battery.py` / `deai_voice.py` / `adversarial/`, copied with hashes to `deai/canon/` -- and it GOVERNS; this suite is the control that was built before it arrived, kept because two independent measurements of one quantity are worth more than one. Every row below carries a provenance word -- `ORDER` (named with its content in the author's operating order), `INFER` (named there, measurement reconstructed here), `PROJECT` (wraps a gate this paper's build already owns) -- and every threshold the canonical body would have supplied is printed `uncalibrated`. No row is blank; nothing here is a score, an "AI probability" or a watermark claim.

status tally: CENSUS 24, FAIL 1, NOT-RUN 2, PASS 26, REVIEW 5

**Class A rows not passing: 3** (T-01d, LX-01c, RT-06)

| row | family | measures | cls | prov | before | after | delta | status | threshold (calibrated?) | note |
| `SG-01` | segmentation | abbreviation register honoured by the sentence splitter | A | INFER | 0 | 0 | 0 | **PASS** | no sentence ends on a register abbreviation, and the register is demonstrably exercised (>= 3 entries occur in the text) (calibrated) | bar for this document: >= 3 register entries present (1151 sentences); register 47 entries, 4 of them present in the text (Fig., Sect., Eq., et al.); 0 sentences end on a register abbreviation; 0 further period-abbreviation candidates reported for the human to add if real |
| `SG-02` | segmentation | fifty-sentence boundary check (machine proxy; the order wants a human read) | A | ORDER | 0 | 0 | 0 | **PASS** | at most 2 boundary errors in 50 sentences (order); the proxy threshold here is 0 mechanical suspects in the 50 drawn (**uncalibrated**) | 0 mechanical boundary suspects over the whole text, 0 of them inside the fifty drawn; fifty printed to sg02_fifty_sentences.md for the human read the order requires |
| `T-01a` | protected tokens (T-01) | numeric multiset (macro layer resolved, math included) | A | ORDER | 2220 | 2220 | 0 | **PASS** | delta against the original must be EMPTY (calibrated) | empty delta |
| `T-01b` | protected tokens (T-01) | citation-key multiset | A | ORDER | 101 | 101 | 0 | **PASS** | delta against the original must be EMPTY (calibrated) | empty delta |
| `T-01c` | protected tokens (T-01) | object / catalogue identifiers | A | ORDER | 42 | 42 | 0 | **PASS** | delta against the original must be EMPTY (calibrated) | empty delta |
| `T-01d` | protected tokens (T-01) | cross-reference keys (\ref) | A | ORDER | 301 | 299 | -2 | **FAIL** | delta against the original must be EMPTY (calibrated) | LOST {'sec:heldout': 1, 'sec:etacrv': 1} GAINED {} |
| `T-01e` | protected tokens (T-01) | label keys (\label) | A | ORDER | 71 | 71 | 0 | **PASS** | delta against the original must be EMPTY (calibrated) | empty delta |
| `T-01f` | protected tokens (T-01) | macro-use multiset (this paper's numbers live here) | A | ORDER | 1913 | 1913 | 0 | **PASS** | delta against the original must be EMPTY (calibrated) | empty delta |
| `T4-01` | LLM-tell census (§T-4) | contrastive reframe "not X but Y" | B | ORDER | 0.16 | 0.16 | 0.0 | **CENSUS** | census only -- rate reported, verdict NEVER automatic (**uncalibrated**) | 3 instances, 0.16 per 1000 words; the order names this first among this pipeline's habits |
| `T4-02` | LLM-tell census (§T-4) | "rather than" | B | ORDER | 2.2 | 0.16 | -2.04 | **CENSUS** | census only -- rate reported, verdict NEVER automatic (**uncalibrated**) | 3 instances, 0.16 per 1000 words; named in the order |
| `T4-03` | LLM-tell census (§T-4) | "not only ... but" | B | ORDER | 0.0 | 0.0 | 0.0 | **CENSUS** | census only -- rate reported, verdict NEVER automatic (**uncalibrated**) | 0 instances, 0.00 per 1000 words; named in the order |
| `T4-04` | LLM-tell census (§T-4) | trailing participial gloss ", suggesting/underscoring/..." | B | ORDER | 0.0 | 0.0 | 0.0 | **CENSUS** | census only -- rate reported, verdict NEVER automatic (**uncalibrated**) | 0 instances, 0.00 per 1000 words; the order names ", suggesting" explicitly; the rest are its family |
| `T4-05` | LLM-tell census (§T-4) | "it is worth noting" / "it should be noted" | B | ORDER | 0.0 | 0.0 | 0.0 | **CENSUS** | census only -- rate reported, verdict NEVER automatic (**uncalibrated**) | 0 instances, 0.00 per 1000 words; named in the order |
| `T4-06` | LLM-tell census (§T-4) | sentence-initial "Importantly/Notably/Crucially/Interestingly" | B | ORDER | 0.0 | 0.0 | 0.0 | **CENSUS** | census only -- rate reported, verdict NEVER automatic (**uncalibrated**) | 0 instances, 0.00 per 1000 words; "importantly" and "crucially" are named; the rest are the same adverb slot |
| `T4-07` | LLM-tell census (§T-4) | "serves to" / "serves as" | B | ORDER | 0.0 | 0.0 | 0.0 | **CENSUS** | census only -- rate reported, verdict NEVER automatic (**uncalibrated**) | 0 instances, 0.00 per 1000 words; named in the order |
| `T4-08` | LLM-tell census (§T-4) | "plays a (key/crucial) role" | B | ORDER | 0.0 | 0.0 | 0.0 | **CENSUS** | census only -- rate reported, verdict NEVER automatic (**uncalibrated**) | 0 instances, 0.00 per 1000 words; named in the order |
| `T4-09` | LLM-tell census (§T-4) | "in terms of" | B | ORDER | 0.0 | 0.0 | 0.0 | **CENSUS** | census only -- rate reported, verdict NEVER automatic (**uncalibrated**) | 0 instances, 0.00 per 1000 words; named in the order |
| `T4-10` | LLM-tell census (§T-4) | em/en-dash pairs in running prose | B | ORDER | 5.8 | 5.55 | -0.25 | **CENSUS** | census only -- rate reported, verdict NEVER automatic (**uncalibrated**) | 103 instances, 5.55 per 1000 words; the order asks for em-dash DENSITY; this paper uses " -- " as its house dash, 237 times in v4.24, so the rate is reported and never flagged |
| `T4-11` | LLM-tell census (§T-4) | triadic list "A, B and C" | B | ORDER | 1.77 | 1.78 | 0.01 | **CENSUS** | census only -- rate reported, verdict NEVER automatic (**uncalibrated**) | 33 instances, 1.78 per 1000 words; named in the order as "triadic lists" |
| `T4-12` | LLM-tell census (§T-4) | hollow intensifier ("very", "quite", "extremely", "highly") | B | INFER | 0.16 | 0.16 | 0.0 | **CENSUS** | census only -- rate reported, verdict NEVER automatic (**uncalibrated**) | 3 instances, 0.16 per 1000 words; INFER: not named, but it is the same register as the named families; report-only |
| `T4-13` | LLM-tell census (§T-4) | "a testament to" / "underscores the importance" | B | INFER | 0.0 | 0.0 | 0.0 | **CENSUS** | census only -- rate reported, verdict NEVER automatic (**uncalibrated**) | 0 instances, 0.00 per 1000 words; INFER: the strongest form of the T4-04 gloss |
| `T4-14` | LLM-tell census (§T-4) | short dramatic paragraph closers | B | ORDER | 3 | 3 | 0 | **CENSUS** | census only; a closer under 9 words carrying no number (**uncalibrated**) | each instance needs a keep-reason on the RV-01 ladder |
| `F-NOFUNC` | paragraph function | paragraphs whose purpose must be stated in one clause | B | ORDER | 118 | 118 | 0 | **NOT-RUN** | every body paragraph has a stated purpose; the statement is a human act, so the machine emits the worksheet (**uncalibrated**) | worksheet emitted for 118 body paragraphs (f_nofunc_worksheet.md); the purpose statements are the audit stage's work, not the battery's |
| `G-03` | paragraph function | closing gloss: a final sentence that only restates its paragraph | B | ORDER | 0 | 0 | 0 | **PASS** | content-word overlap >= 50 per cent with the paragraph, no number/citation/ref of its own, and a gloss opener (**uncalibrated**) | 0 candidate glosses; each is adjudicated, not auto-cut |
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
| `AB-01` | numerical consistency / hygiene (wrapped) | abswords.py -- abstract word count against the limit | B | PROJECT | - | 0 | - | **PASS** | the gate's own exit status (0 = pass) (calibrated) | abswords: 244 words in the typeset abstract of technosignatures_40pc_v4.25.pdf (limit 245) /   OK one paragraph, within the limit, measured on the page |
| `FARM-01` | instrument integrity | the wrapped gates wrote nothing into the target tree | A | INFER | - | 0 | - | **PASS** | 0 files in the target tree changed size or mtime while the wrapped gates ran (calibrated) | farm: 1010 files copied, 45 symlinked; the target tree is byte-stable across the gate phase |
| `MX-01` | numerical consistency | one macro name carrying two different values | B | INFER | 37 | 37 | 0 | **REVIEW** | 0 names with two distinct non-empty definitions (calibrated) | 37 names redefined to a DIFFERENT value across the 185 macro files (the `\providecommand{}{}\renewcommand{}{v}` idiom is not counted); several are deliberate round-to-round aliasings, so this is a REVIEW list, not a failure |
| `EP-01` | epistemic ladder | every claim classified observed / inferred / conjectured | B | ORDER | 37 | 37 | 0 | **CENSUS** | census; an unclassified sentence is a sentence the ladder cannot see, and its count is the honest limit of this row (**uncalibrated**) | observed 73 / asserted 917 / inferred 92 / conjectured 32 / unclassified 37 of 1151 sentences (the ladder is conjectured < inferred < asserted < observed; an "asserted" sentence states a fact without saying how it is known, and "unclassified" means no finite verb -- a fragment or a run-in heading) |
| `EP-02` | epistemic ladder | no sentence climbs the ladder relative to the original | A | ORDER | 0 | 0 | 0 | **PASS** | 0 climbs (calibrated) | no climb over 0 replaced sentences; 0 inserted sentences reported separately |
| `LX-01a` | hygiene | comments left in the shipped source (arXiv ships the source) | B | ORDER | 1132 | 1155 | 23 | **CENSUS** | 0 comments in the arXiv package; the version tree itself may carry them because `arxivset.sh` strips them (calibrated) | 1155 commented source lines in the tree. This is NOT a failure of the tree: `arxivset.sh` strips comments from the submission copies and proves the strip changes no output byte. The arXiv-package row is LX-01c. |
| `LX-01b` | hygiene | model / agent / version / round / referee / TODO mention in the TYPESET page | A | PROJECT | - | 0 | - | **PASS** | genai_sweep.py exit 0 against its allow-list (calibrated) |   [raw] assertion                    / That this sample is indepen- dent of the choice of statistic and of mask is an assertion of ours and not something a reader can check. /   [p27] assertion                    / That this sample is independent of the choice of statistic and of mask is an assertio |
| `LX-01c` | hygiene | the same sweep over the arXiv PACKAGE (source ships) | A | ORDER | - | 679 | - | **REVIEW** | 0 comments and 0 forbidden mentions in the package (calibrated) | 4 forbidden-mention lines and 675 comment lines in the package |
| `LX-07` | hygiene | PDF metadata carries no model / agent / round / version mention | A | ORDER | - | 0 | - | **PASS** | 0 forbidden mentions in Title/Author/Subject/Keywords/Creator/Producer (calibrated) | 41 pp; fields creator,producer clean |
| `AU-01` | hygiene | title block carries the authors correctly | A | ORDER | - | 2 | - | **PASS** | G. J. White present; ORCID 0000-0002-7126-691X if the class prints one (calibrated) | title block found (3 commands): White True, Dey True; ORCID 0000-0002-7126-691X in the source: False (the class may not typeset an ORCID -- that is a REVIEW point for the author, not a failure of the block) |
| `I-5` | stop conditions | [[TBD]] / TODO / FIXME markers in the source | A | ORDER | 0 | 0 | 0 | **PASS** | 0 markers -- the order says STOP and report, never guess (calibrated) | no markers |
| `RT-01a` | reader tests | mean words per sentence | B | ORDER | 28.16 | 28.06 | -0.1 | **CENSUS** | uncalibrated (no discipline corpus on this machine) (**uncalibrated**) | report-only: the order supplies no numeric threshold and no corpus exists here to fit one |
| `RT-01b` | reader tests | 90th-percentile sentence length | B | ORDER | 50 | 50 | 0 | **CENSUS** | uncalibrated (**uncalibrated**) | report-only: the order supplies no numeric threshold and no corpus exists here to fit one |
| `RT-01c` | reader tests | sentences over 40 words | B | ORDER | 139 | 137 | -2 | **CENSUS** | uncalibrated (**uncalibrated**) | report-only: the order supplies no numeric threshold and no corpus exists here to fit one |
| `RT-01d` | reader tests | Flesch reading-ease proxy | B | ORDER | 44.5 | 44.5 | 0.0 | **CENSUS** | uncalibrated; a PROXY (syllables are estimated by vowel groups) (**uncalibrated**) | report-only: the order supplies no numeric threshold and no corpus exists here to fit one |
| `RT-01e` | reader tests | passive constructions per 1000 words | B | ORDER | 11.34 | 11.27 | -0.07 | **CENSUS** | uncalibrated (**uncalibrated**) | report-only: the order supplies no numeric threshold and no corpus exists here to fit one |
| `RT-01f` | reader tests | nominalisations per 1000 words | B | ORDER | 34.38 | 34.89 | 0.51 | **CENSUS** | uncalibrated (**uncalibrated**) | report-only: the order supplies no numeric threshold and no corpus exists here to fit one |
| `RT-02` | reader tests | stumble candidates | B | ORDER | 145 | 142 | -3 | **REVIEW** | candidates for a human read; no numeric threshold (**uncalibrated**) | 142 candidates; the order's RT-02 is a reader's stumble log, so this list feeds that read rather than replacing it |
| `RT-03` | reader tests | acronym used but never expanded | B | INFER | 15 | 15 | 0 | **REVIEW** | 0 unexpanded acronyms outside the exempt list (**uncalibrated**) | 15 of 16 acronyms never parenthetically expanded: ASIAA, CDMS, CDS, HIP, JAO, KASI, MCC, MWA, NINS, NRC |
| `RT-04` | reader tests | paragraph length profile | B | INFER | - | 5.6 | - | **CENSUS** | report-only (**uncalibrated**) | 118 body paragraphs, mean 5.60 sentences, 6 one-sentence paragraphs, longest 25 |
| `RT-05` | reader tests | section openings state the section's point | B | ORDER | - | 10 | - | **NOT-RUN** | worksheet for the human read (**uncalibrated**) | openings listed for 10 sections in rt05_openings.md; whether an opening states the point is a reader's judgement |
| `RT-06` | reader tests | the stored main-finding sentence (for the later fresh-agent T-06 test) | A | ORDER | - | 8 | - | **REVIEW** | exactly one sentence, one number, one decisive observation (calibrated) | stored (author-supplied): 1 sentence(s), 8 number(s). the order asks for ONE sentence and ONE number; adjudicate |
| `B-33` | edit budget | fraction of body sentences changed, per section | A | ORDER | 0.0 | 0.25 | 0.25 | **PASS** | > 40 per cent in ANY section stops the run (calibrated) | worst section 'abstract' at 25.0 per cent (3 of 12 sentences); 0 section(s) over 40 per cent |
| `B-26` | convergence | measured delta against the original | A | ORDER | - | 38 | - | **PASS** | both columns present for every row (calibrated) | 38 of 57 rows carry both columns |

