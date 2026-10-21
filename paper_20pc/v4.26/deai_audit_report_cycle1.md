# `deai_audit_report.md` — DEAI Stage 1 (scientific integrity) and Stage 2 (citations) on v4.25

`deai-canon`, 2026-10-19. Instrument: canonical `/shared/deai/` package (protocol v3.0 §0–10 +
addendum §A–§T, which wins on conflict); operating order
[`referee_r24/DEAI_SPEC_R24.md`](/workspace/SETI/referee_r24/DEAI_SPEC_R24.md).
Target: **v4.25** — main text 21.85 pp, 41 pp, abstract 243 words / 1,562 characters,
`gate.sh` ×4 byte-identical, PDF md5 `4dcb008f1938431749750bcc75bbc5cf`, `cleanregen` 280/280,
`audit_numbers` **58/0**, `arxivset` A8 byte-identical over 240 items.

**Order of work (binding).** The measured battery was computed first and is in
[`deai_battery.md`](deai_battery.md) — execution contract #1. The adversarial fixtures pass
(**23/23, exit 0**), which is the order's precondition for any revision. **No sentence of the paper
was edited to produce this report, and nothing in it may be fixed by rewording**: under **§M** every
scientific, statistical and reproducibility finding is routed to
[`deai_referee_report.md`](/workspace/SETI/deai/work/canon425/deai_referee_report.md) and
[`deai_author_decisions.md`](/workspace/SETI/deai/work/canon425/deai_author_decisions.md), staged
outside this tree because this stage owns only two files in it.

**No score, no "AI probability", no watermark claim (§R).** Verdicts are status words.

---

## 1. Stage 1 — scientific integrity

### 1.1 MF-01 — the main-finding test (§3.1), **REVIEW**
Stored sentence (`work/b424_before/main_finding.json`, `stored-by-coordinator`):

> *No confirmed carrier is found: the 31 unattributed crossings in the primary sample are consistent
> with the 24.6 expected by chance from the control positions, and none returned to its predicted
> frequency in a later observation.*

Measured against v4.25's replaced abstract: **every clause is supported and the numbers still
match** — the abstract prints 31 against 24.6 with *P* = 0.13, "No confirmed carrier is found", and
"None of the 33 testable crossings returned to its predicted stellar-frame cell".

**Finding (status REVIEW, not PASS).** §3.1 asks for one sentence containing *a number with
uncertainty or a limit*, plus the single decisive observation. The sentence has **two counts and no
uncertainty or limit**; the paper's limit (EIRP₉₀ = 1.5 × 10¹⁵ W for the median system, nine times
in ten by injection) is not in it. The decisive observation **is** named. Author decision; **T-06**
at the gate stage is tested against whatever he settles on, and if he overrules, MF-01 and T-06
re-run. (Row renamed from `RT-06`: canonical RT-06/B-32 is cross-reference density.)

### 1.2 Argument graph and F-NOFUNC (§3.2) — **NOT-RUN by design, worksheet delivered**
118 body paragraphs; the worksheet with each paragraph's location, sentence count and opening
sentence is at `work/b425_before/f_nofunc_worksheet.md`. **A machine cannot state a paragraph's
purpose, and a machine-written purpose would turn F-NOFUNC into a check that cannot fail** — so the
row is NOT-RUN with that reason, not zero.

Mechanical screen only (not a verdict): **59 of the 91 paragraph openings the worksheet parser
captured carry no number, citation or cross-reference.** Nearly all are legitimate topic sentences
("The band has physical advantages and physical costs."). One is a genuine **G-04 / D-11 candidate**:

> P011, `sections/02_background.tex:183` — *"The statistical treatment this search needs is unusually
> detailed, and the appendices se…"*

a paragraph whose opening describes the paper's own process rather than the science. Reported, not cut.

### 1.3 Claim–evidence (§3.3), mechanical members — `work/canon425/canon_sweeps.log`
| defect | count | reading |
|---|---|---|
| E-11 novelty claim | **22 candidates** | REVIEW list, not 22 claims: most are ordinal (`the first integration`, `the first proposals`). No `unprecedented`, no `never before` |
| E-12 "widely accepted" without citation | 0 | PASS |
| E-13 correlation narrated as causation | 0 | PASS |
| E-14 undefined operational term | 0 | PASS — `crossing`, `trigger`, `attributed` are all defined operationally |
| E-16 uncertainty not classified statistical/systematic/methodological | **4** | REVIEW: four uses of "uncertainty" with no classifier within 60 characters |
| E-19 artificial optimism | 0 | PASS |
| E-20 generic future work | 0 | PASS |
| P-09 universal significance | 0 | PASS |
| E-01…E-10, E-15, E-17, E-18 | — | **NOT-RUN**: each needs a reader and the research record; the canonical package ships no implementation |

### 1.4 Epistemic ladder (§3.4) — **CENSUS**
1,150 sentences: **observed 74 · asserted 917 · inferred 92 · conjectured 30 · unclassified 37.**
The ladder is `conjectured < inferred < asserted < observed`; an *asserted* sentence states a fact
without saying how it is known. **The 37 unclassified sentences are the honest limit of the row** —
they carry no finite verb the classifier can see. No climb can be measured on a before-pass
(`EP-02` = canonical **T-03** is NOT-RUN until an after-pass exists), and that is the row that will
catch a strengthened claim.

### 1.5 Numerical consistency (§3.5, N-01…N-07) — **PASS, leaning on the project's own gates**
Not re-implemented. The build's own gates re-derive every printed number from its source of truth,
and all of them pass on v4.25:

| canonical row | project gate | result |
|---|---|---|
| N-01 (same quantity, same value everywhere) | `prosenum_v399.py` | **0** literals disagreeing with a macro |
| N-02 (counts reconcile) | `macrosyn.py`, `consistency_v399.py` | **0** / **0** |
| N-04/N-05 (values possible; text matches the record) | **`audit_numbers_v385.py` — 58 PASS / 0 FAIL** | every printed number re-derived from catalogue, product list, harvest and control stores |
| N-06/N-07 (refs and citations resolve) | `xrefcheck.py`, `citegate.py` | **0** / **0**, G1–G3 PASS |
| abstract ↔ body | our `N-01`, `N-01b` | ★ **both moved REVIEW → PASS on v4.25**: all 22 distinct abstract numbers recur in the body and all 30 abstract macros are reused |

★ **The banked §M item is closed and independently re-measured.** The abstract de-drifting value and
§4.2 now print **the same macro, `\AccelCeilMed` = 3.60**; `\AccelCeilMin` survives only as a
definition carrying the identical value, so it is a same-value synonym and not a collision.

Standing warnings from `audit_numbers` (unchanged, residual, not v4.25 regressions):
`stratified_completeness.pdf` built but never `\includegraphics`; three stars in `tab_nearest_r21.tex`
written without the SIMBAD space (`HD14055`, `HD170773`, …).

**Still open: `MX-01` = 37 macro names carrying two different values** across the 185 macro files.
Unchanged from v4.24. Routed to author decisions with `\CeAddLimNear` vs `\FrNarrowAddLim` first,
because one keystroke separates them.

### 1.6 Astronomy-specific correctness (§3.6)
- ★ **`flux` where `flux density` is meant — 22 bare uses against 4 of "flux density", severity 2.**
  Every quantity involved is a monochromatic one measured in mJy (`a flux threshold`, `received
  flux`, `the flux limit`, `apparent flux` / `true flux`, `inferred flux`, `at the discovery flux`).
  §3.6 names this distinction first, and a referee reading the EIRP derivation will see it. The
  detector fired on one sentence on its own (the §3.6 row in the battery) because only there does
  the word share a sentence with its `11.5 mJy`; the systematic question is the 22. **Author
  decision**: define once that "flux" is used for flux density with its units, or change the 22.
  **This is not a rewording matter and is not in the revision brief.**
- `spectral index`: **one** occurrence, so no sign-convention inconsistency is possible; §3.6's
  "state the convention once" is satisfied vacuously and is recorded as such.
- `optically thin/thick`: **0** occurrences — the canonical AD-7 contradiction family cannot arise.
- `primary beam` **8** / `synthesised beam` **6**, used distinctly and correctly where checked
  (the primary-beam factor converting measured noise to a flux at the star; the synthesised beam for
  resolution). No resolution-vs-astrometric-accuracy conflation found.
- Units are the project's own house style throughout (`km s⁻¹`, `W`, `GHz`, `nHz`); `DEAI_SPEC_R24`
  forbids restyling, so MNRAS-specific clauses (`per cent` vs `%`, British spelling) are
  **NOT-APPLICABLE** here. `HS-01` ('%' in running text) is 0 in any case.

### 1.7 Structural rows bearing on Stage 1
`SG-01`/`SG-02` **PASS** (0 sentences end on a register abbreviation; 50 sentences printed, 0
mechanical suspects) — without this every sentence metric below would have been withheld.
`G-03` closing glosses **0**. `I-5` **PASS**: no `[[TBD]]`, `TODO`, `FIXME` or `[[…]]` marker
anywhere in the source, so the order's STOP condition does not fire.
`AU-01` **PASS**: the title block carries both authors; ORCID not typeset by the class (a REVIEW
point for the author, not a failure of the block).
`LX-07` **PASS**: PDF metadata carries no model, agent, round or version mention.
`LX-01b` **PASS**: `genai_sweep.py` (23 driven families) finds no forbidden mention on the typeset
page. ★ `LX-01c` **now runs** and is **REVIEW**: the arXiv package at `/workspace/tmp/arxivset`
(215 items) ships **676 comment lines**, and its 4 "forbidden mentions" are **all false positives or
required content** — an ALMA Technical Note bibitem, the OJA class's own boilerplate, and two lines
of the AI-assistance disclosure, which **I-7 forbids removing**. None of the 676 comments mentions a
round, referee, owner, agent, TODO or version string.

---

## 2. Stage 2 — citation audit

### 2.1 The delta, which is the whole of this round's new work
The bibliography was verified **entry by entry, field by field, against the published record in the
previous round, with three citing sentences corrected**. This pass therefore audits only the change,
and records the rest as **previously verified (2026-10-19, round 24 `r24-lit`)**.

| measurement | v4.24 | v4.25 | finding |
|---|---|---|---|
| `\bibitem` entries | 68 | **68** | **no entry added, changed or removed** — the key multiset is identical |
| `\cite*` commands | 83 | **84** | **exactly one new citing use** |
| the new use | — | `\citet{Enriquez2017}` ×1 | in the **new last appendix** (`app_Q_cwtfm.tex`): *"the continuous-waveform transmitter figure of merit of Enriquez (2017)"* |

**R-02 claim–source alignment on the one new use: PASS.** The CWTFM is the figure of merit defined
in Enriquez et al. (2017); the sentence attributes the metric to the paper that introduced it, which
is also **R-09** (method credited to its origin, not to an application) satisfied.

### 2.2 Printed labels — checked here because `citegate` checks keys, not labels
`r24-lit`'s §2 patch **has not landed in v4.25**: there is no 69th entry and there is a **single**
`Li et al.(2026)` bibitem (`FAST3IATLAS2025`), so the `2026a`/`2026b` relabelling is not yet needed.
Measured over all 68 entries: **0 duplicate printed labels, 0 duplicate keys, 0 first-author+year
collisions**. If the §2 patch lands later, this check must be re-run — a second `Li et al.(2026)`
would pass `citegate` and typeset two indistinguishable citations.

### 2.3 The rest of §4
| row | result |
|---|---|
| R-01 resolve every entry against ADS/Crossref | **NOT-RUN here** (no ADS token in this container) — and **not needed**: all 68 were verified entry by entry last round, and the delta is zero. `citegate` proves internal consistency both ways, which is **not** R-01 and is not reported as if it were |
| R-03 3+-citation blocks | **3**, REVIEW list |
| R-05 "numerous studies have…" | 0, PASS |
| R-11 flattery (`seminal`, `elegant`, `pioneering`) | 0, PASS |
| R-04, R-06, R-07, R-08, R-10 | **NOT-RUN**: each needs the cited sources read; no canonical implementation |
| **LT-01** 24-month literature sweep | **REVIEW — two expected-but-absent papers**, carried from the v4.24 cut and still absent in v4.25 (0 hits each): **Myburgh et al. 2026**, arXiv:2608.18275, Acta Astronautica — the first published 25–50 GHz SETI search; and **Mason et al. 2026**, arXiv:2610.22266, the ALMA2040 mm/sub-mm SETI white paper, submitted 15 October 2026. Ruling 16 §2 governs: content-check both at the source, then propose **at most one sentence and one citation each** in the §2 edit `r24-lit` already has open. **Never auto-cited** |
| OV-01 / B-35 text overlap | **NOT-RUN**: no cited full texts offline |

---

## 3. Severity ledger

| severity | item | route |
|---|---|---|
| **1** (blocks submission) | **none open** | — |
| 2 (a referee would raise it) | `flux` for flux density, 22 uses (§1.6) | referee report |
| 2 | LT-01's two absent papers in our own subfield (§2.3) | author decisions, Ruling 16 §2 |
| 2 | `MX-01` 37 macro names with two values (§1.5) | author decisions |
| 2 | B-05 `rather than` 2.30/1000 against a calibrated ≤ 2, with an adjudicated 76→8 revision of this paper recorded in §T-4.2 and absent from the tree | author decisions |
| 3 | B-14 pseudo-clefts: 9 canonical / 29 widened, 2 of them new in v4.25, one in the Abstract where P-01 is banned outright | revision brief |
| 3 | B-18b paragraph-opener share 0.36 against ≤ 0.35 — a **new** regression caused by the relocation | revision brief |
| 3 | B-31 162 body emphases (4.77/1000 against ≤ 1), B-04 one agent-register hit, B-07 28 stacked compounds, B-01 5.95/1000 house dashes, B-23 20 near-duplicate pairs, B-24 39 repeated 6-grams, C-01 6–135 windows | revision brief |
| 3 | one `itemize` inside `\section{Conclusions}` (§G forbids it; restyling is barred) | author decisions, Ruling 16 §3 |
| 4 | `LX-01c` 676 comments in the arXiv source package; `RT-03` 15 unexpanded acronyms; `E-16` 4 unclassified uncertainties; `E-11` 22 novelty candidates; `R-03` 3 citation blocks; HS-02 28 digit-initial sentences | author decisions |
| — | B-32 cross-references 9.13/1000 | **adjudicated, keep-reason recorded**: +16 of the +18 are section and appendix pointers created by moving 2.1 pp into appendices; removing them would make the text worse, which **I-7 forbids** |

**Nothing above is a licence to edit a number, a claim's strength, a citation or a scientific
statement.** Stage 4 is a separate reviser working from
[`/workspace/SETI/deai/REVISION_BRIEF.md`](/workspace/SETI/deai/REVISION_BRIEF.md); Stage 5's gates
go to a third, fresh context that has not seen the edits.

## 4. Execution manifest (§N) — this stage

| Test ID | Status | Input + version | Method | Result | Evidence | Action | Verification | Reason |
|---|---|---|---|---|---|---|---|---|
| battery before-pass | **PASS** | v4.25 | canonical ×3 + 58 project rows | complete; no blank row | `deai_battery.md` | Stage 4 may begin | v4.24 cut re-run for every movement | — |
| AD-1…AD-10 | **PASS** | canonical fixtures | `run_canon_fixtures.py` | 23/23, exit 0 | `work/canon425/canon_fixtures.log` | — | every fixture carries a control | — |
| MF-01 / §3.1 | **REVIEW** | stored sentence | clause-by-clause against the abstract | supported; no uncertainty or limit | §1.1 | author confirms or overrules | numbers re-checked in the resolved abstract | — |
| F-NOFUNC | **NOT-RUN** | 118 paragraphs | worksheet | screen only: 59 openings without a number | §1.2 | human pass | — | a machine cannot state a purpose |
| §3.3 E-sweep | **REVIEW** | `prose.txt` | 8 mechanical members | 22 / 4 candidates, rest 0 | `canon_sweeps.log` | author reviews lists | instances printed | 13 members need a reader |
| §3.4 ladder | **CENSUS** | 1,150 sentences | `EP-01` | 74/917/92/30, 37 unclassified | `ep01_ladder.json` | — | unclassified count published | no threshold by instruction |
| §3.5 numbers | **PASS** | v4.25 | 8 wrapped gates | `audit_numbers` 58/0; N-01/N-01b now PASS | §1.5 | — | gates run in a copy farm | — |
| §3.6 astronomy | **REVIEW** | `prose.txt` | targeted census | 22 bare `flux`; 1 `spectral index`; 0 `optically thin` | §1.6 | referee report | detector non-vacuous (AD-7) | — |
| Stage 2 delta | **PASS** | 68 bibitems | key multiset + cite-context diff | 0 entries changed; 1 new use, correctly attributed | §2.1 | — | printed labels checked independently | — |
| R-01 | **NOT-RUN** | 68 entries | — | previously verified 2026-10-19, delta zero | §2.3 | — | — | no ADS token here |
| LT-01 | **REVIEW** | live arXiv | 2 searches + 1 fetch | 2 absent papers, still absent in v4.25 | §2.3 | Ruling 16 §2 | both verified live | neither read beyond the abstract |
| SR-1…4 | **NOT-RUN** | — | — | — | — | route to another model family | — | §RV-04: one family here |
| FARM-01 | **PASS** | v4.25 tree | 1,299-file snapshot before/after | see §5 | `work/farm425_*.txt` | — | re-verified independently | `chmod a-w` ≠ root-proof |

## 5. Writes into this tree (FARM-01)

A full `mtime`+size snapshot of all **1,299** files was taken before the pass and compared after.
**The only files written are the two this stage owns**: `deai_battery.md` and
`deai_audit_report.md`. The wrapped project gates ran against a **copy farm** (994 files copied,
45 symlinked) and `FARM-01` confirms the tree was byte-stable across the gate phase. Everything
else — inputs, instances, logs, the referee report and the author-decisions file — is outside this
tree, under [`/workspace/SETI/deai/`](/workspace/SETI/deai/).
