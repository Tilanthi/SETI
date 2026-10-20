# `deai_change_log.md` — Stage 4 (DEAI revision) of v4.25

`deai-revise`, 2026-10-19. Every edit below carries a **defect ID**, the **old → new** text, an
**improvement reason**, and its **approval status** (`applied` = inside this stage's remit;
`author` = referred, not applied). Order of work is §D's: science-wording → structure → paragraphs
→ sentences → words. The preserve-first ladder (RV-01) is the default: delete > cut clause >
reorder > replace word > rewrite sentence > rewrite paragraph.

**Mechanics.** Every batch is a JSON patch set under
`/workspace/SETI/deai/work/rev425/batches/`, applied by `referee_r24/apply_patch.py`, which asserts
each anchor occurs **exactly once in the target** and refuses to write otherwise. After every batch:
`deai/revise/measure.py` (metrics + the T-01 invariant set, including AD-10's (value, referent)
tuple register) and `deai/revise/compile.sh` (pdflatex, 0 errors). Receipts are in
[`deai_invariant_check.md`](deai_invariant_check.md).

**Baseline.** The stage opened on a tree byte-identical to the one the before-table was measured on:
`mkinputs.py` reproduced `flat.tex` `d6b9daed5453`, `resolved.tex` `47a28bd83ac3`, `prose.tex`
`b53f2141e83f` — the same three md5s the canon stage recorded at 19:49 UTC. Measured before-state
(this stage's own harness, which reproduces the before-table to rounding): 33,975 words, B-05 78
(2.296/1000), B-14 9 canonical / 30 widened, B-01 202 ` -- ` (5.946/1000), B-17 6, B-18b 75 of 208
(0.361), B-31 218 total / 165 body (4.857/1000), `\ref` 301, bare `flux` 22.

---

## BATCH 1 — `flux` where `flux density` is meant (§3.6 physics-wording, severity 2)

**Defect.** `PH-01` / before-table §3.6 row: a quantity in mJy is a flux **density**; the paper used
bare `flux` for it 22 times. A submillimetre referee reads this immediately.

**Adjudication, not substitution.** The 22 split into two populations and only one is wrong:

*Corrected (14 edits, all in hand-written `sections/`):* every use whose referent is $S$, a
flux density in mJy — the primary-beam factor that "turns a measured noise into a flux density at
the star" (§5.1 and Appendix A), $S_{\min}$ "measured in apparent flux density … quoted in true
flux density" (Appendix A), the inferred-flux-density error of the beam model, the apparent-flux
density extraction of Appendix C, the stacked and single-epoch **flux-density limits** (§5b, §7),
the amplitude a broad feature needs ($\times\ScNBroadRatio$, §6), the visibility diagnostic's "a
noise maximum at the star has flux density at the star" (§4), and the three
"persisting at the discovery flux density" statements (§5.3, Appendices I and J).

*Kept, with keep-reasons:* **§2's five uses and the Figure caption's "constant received flux"** are
an **integrated** flux in W\,m$^{-2}$, which §2 itself defines ($F_{\rm min}=S_{\rm
min}\,\delta\nu$) — the one place in the paper where the distinction is load-bearing, since the
literature comparison turns on it. **Appendix A's "trigger flux"** is the same W\,m$^{-2}$ quantity
(`\FluxTrigBest` is in W\,m$^{-2}$). **Appendix A's "an unresolved carrier's flux at a channel
centre"** is a power fraction, and the next clause says "total power". **"ALMA's flux transfer"** is
the field-standard name for the flux-scale transfer. One caption use, "its flux term is
band-dependent", became **"its flux-scale term"** — the term meant, at no cost in words.

**Consequence for the author decision.** `deai_author_decisions.md` §3 offered *one defining
sentence in §4* or *22 located changes*. Neither is needed as framed: once the 14 misuses are
corrected, the only surviving bare `flux` uses are the integrated-flux ones **that §2 already
defines in situ**, so the convention is stated where it is used and no sentence is added. This
round subtracts.

| ID | file | old → new | reason | status |
|---|---|---|---|---|
| FX1 | `04_method` | `has flux at the star` → `has flux density at the star` | mJy referent | applied |
| FX2 | `05_results` | `into a flux at the star` → `into a flux density at the star` | mJy referent | applied |
| FX3 | `05_results` (caption) | `its flux term is` → `its flux-scale term is` | names the term meant; 0 words | applied |
| FX4 | `05_results` | `at the discovery flux would have given` → `… flux density …` | the sentence prints 11.5 mJy | applied |
| FX5 | `05b_stack` | `the flux limit improves` → `the flux-density limit improves` | $S_{\min}$ limit; 0 words | applied |
| FX6 | `06_discussion` | `the flux for a feature` → `the flux density for a feature` | `\ScNBroadRatio` is an amplitude ratio | applied |
| FX7 | `07_conclusions` | `deepens the flux limit` → `deepens the flux-density limit` | $S_{\min}$ limit; 0 words | applied |
| FX8 | `app_A` | `into a flux at the star` → `into a flux density at the star` | mJy referent | applied |
| FX9 | `app_A` | `apparent flux … true flux` → `apparent flux density … true flux density` | $S_{\min}=5\sigma/A$ | applied |
| FX10 | `app_A` | `error in inferred flux` → `error in inferred flux density` | mJy referent | applied |
| FX11 | `app_C` | `in apparent flux` → `in apparent flux density` | mJy referent | applied |
| FX12 | `app_I` | `at the discovery flux would have given` → `… flux density …` | mJy referent | applied |
| FX13 | `app_J` | `at the discovery flux would have produced` → `… flux density …` | mJy referent | applied |
| FX14 | `app_N` | `the crossing's own flux` → `the crossing's own flux density` | mJy referent | applied |

**Receipt.** 14/14 anchors unique, +14 words (33,975 → 33,989), bare `flux` 22 → 10 (the 10 kept
with reasons above), **numbers and citations unchanged**, 7 sentences re-skeletoned with identical
value multisets, compile 0 errors / 41 pp / 0 overfull.

**Referred, not fixed (§M).** Three *generator* column glosses carry the same wording into the
deposit — `ledger_v410.py:1199`, `tolrecur_r21.py:1012` ("statistic a carrier persisting at the
discovery flux …") and `recur_v411.py:261`. Changing a deposited CSV's column description is a
reproducibility artefact, not prose: recorded in `deai_referee_report.md` §1, not edited here.

---

## BATCH 2 — the Abstract's pseudo-cleft, and the gate that forbade its repair

**Defect.** `B-14` / `P-01`. The Abstract closed *"What limits the search is coverage, not depth"* —
a pseudo-cleft (hard zero under T-07) **and** a contrastive reframe, which P-01 bans outright. The
**content is Referee 2's own** and had to survive: his suggested text ended on the coverage limit
and we adopted his structure, so only the construction could go.

| ID | file | old → new | reason | status |
|---|---|---|---|---|
| AB1 | `sections/abstract.tex` | `What limits the search is coverage, not depth;` → `Coverage limits this search more than depth does;` | removes the pseudo-cleft and the `, not X` reframe; keeps the referee's content; `this search` scopes the claim to this survey instead of searches in general (§C: quantifier/scope) | applied |

**Measured on the typeset page, before and after** (`abswords.py`, which reads the PDF text stream,
not the source): **243 words before, 243 words after**, against the 245 ceiling — the replacement is
word-for-word neutral (8 words for 8), so none of the two words of headroom was spent. Characters
1562 → 1565 of the arXiv field's 1920. The pasted transliteration in `OJA_SUBMISSION.md` was
re-synchronised in the same batch, because `absmeta.py` compares it with the typeset abstract
**character for character** and duly failed until it was (M3), and the two counts the file quotes of
itself were corrected 1564 → 1567 (M4 measures and compares them, so they are gate-held, not typed).

### ★ And the gate pinned the words, for the third time in this project

`absreq_r17.py`'s **B7** *required* the abstract to contain the literal `what limits the search`
and `not depth|rather than depth`. **A check that pins a construction forbids its own repair** —
the same defect as Ruling 5's B5 and Ruling 17's `censusacct` A4. Rewritten in the same patch as an
invariant, per the standing rule that *a gate may pin that a fact is stated, never the words that
state it*:

| ID | file | old → new | reason | status |
|---|---|---|---|---|
| AB2 | `absreq_r17.py` | B7's docstring | states the invariant and why it is not the old form of words | applied |
| AB3 | `absreq_r17.py` | drive 7: delete `What limits the search[^.]*\.` → delete the sentence containing `coverage` (case-insensitive) | a drive keyed on a form of words expires with that form | applied |
| AB4 | `absreq_r17.py` | B7: literal-string test → **one sentence of the abstract must name `coverage` and `depth` together under a limiting verb**, with `\ZcNoRepSys` and `line emission` still required | keyed on the fact; any construction that states it passes | applied |

**Receipt.** `absreq_r17.py` 7 checks / 0 FAILED, and **all ten drives fire** (1→B1, 2→B2, 3→B3,
4→B4, 5→B5, 6→B6, **7→B7**, 8→B1, 9→B5, 10→B5). Numbers and citations unchanged; 26 sentences
re-skeletoned with identical value multisets; `b14_wide` 30 → 29.

★ **My own first version of drive 7 was a check that could not fail.** Keyed on `coverage`
case-sensitively, it did not match the new sentence's capital `Coverage`, so the drive reported
*"DRIVE 7 DID NOT FAIL — the clause it exercises is vacuous"* about itself. Fixed with `flags=re.I`
and demonstrated firing. That is the eighteenth instance of the family in this tree and the second
time this round that the repair of a vacuous check was itself vacuous on its first attempt.

---

## BATCHES 3 and 4 — the pseudo-cleft census: **30 instances, now 0 on both readings**

**Defect.** `B-14`, a hard zero under T-07. The canonical regex permits only a 1–2-word gap and so
saw **9 of 29**; worked from the widened 1–4-word reading, the census was **30** (my harness sees one
more than the before-table because it also admits `are/was/were`). **Nine of the thirty are not in
`sections/*.tex` at a line-grep's reach at all** — they straddle the 76-column wrap, which is why
the first pass found 20 and the measured text found 30. Every edit below is the *same* proposition
with the cleft unwound: subject-first, no new claim, no claim withdrawn.

**Headings count.** `\subsection{What the expectation is conditioned on}` →
`\subsection{Conditions on the expectation}` (PC15), with `macromap.py`'s description of that
subsection re-synchronised in the same batch (PC21) so the map does not name a heading that no
longer exists.

**The three cleft run-in headings** became plain emphasised statements: *"What is inflated is the
field and not the star"* → *"The field is inflated and the star is not"* (PC4); *"What is left is
bounded, and the bounds are null"* → *"The remainder is bounded, and the bounds are null"* (PC17);
*"What follows is what the displacement is not"* → *"The paragraphs below say what the displacement
is not"* (PC13, where the surviving *"what the displacement is not"* is the object of a verb, an
ordinary indirect question and not a cleft).

**Two edits pay for themselves elsewhere.** PC8 removes a `rather than` as well as a cleft (*"the
narrowness belongs to the criterion rather than to the archive"* → *"and not to the archive"*), and
PC30 splits a 44-word sentence in two (*"Two things favour this band. Terrestrial transmitters
are sparse …"*), which is the ladder's *split clause* step rather than a rewrite.

**The third variant of the Abstract's sentence** (Conclusions item 7, *"What limits this search is
coverage and not depth"*) is now the same plain sentence as the Abstract's, PC9, so the two agree
word for word; a fourth variant in §6 (*"What limits the search is that inherited coverage"*) became
*"That inherited coverage sets the limit"* (PC27).

| ID | file | old → new |
|---|---|---|
| PC1 | `05_results` | `What is carried across is one dimensionless number per class` → `One dimensionless number per class is carried across` |
| PC2 | `05_results` | `What that establishes is consistency with` → `That establishes consistency with` |
| PC3 | `05_results` | `What the two numbers describe is a residual` → `The two numbers describe a residual` |
| PC4 | `05_results` | `\emph{What is inflated is the field and not the star.}` → `\emph{The field is inflated and the star is not.}` |
| PC5 | `05_results` | `What identifies the extended emission is therefore the \emph{level} …` → `The extended emission is therefore identified by the \emph{level} …` |
| PC6 | `05_results` | `What is claimed is weaker and safer` → `The claim is weaker and safer` |
| PC7 | `06_discussion` | `What is missing is not coverage but a candidate` → `The shortfall is not coverage but a candidate` |
| PC8 | `07_conclusions` | `What that excludes is narrow … rather than to the archive` → `That exclusion is narrow … and not to the archive` |
| PC9 | `07_conclusions` | `What limits this search is coverage and not depth.` → `Coverage limits this search more than depth does.` |
| PC10 | `07_conclusions` | `What applies at any inclination is the single-epoch limit, $\PxEirpSingle$\,W.` → `The single-epoch limit, $\PxEirpSingle$\,W, applies at any inclination.` |
| PC11 | `07_conclusions` | `What transfers beyond this archive is the obstacle:` → `The obstacle transfers beyond this archive:` |
| PC12 | `08_backmatter` | `What the released tables support is narrower:` → `The released tables support a narrower claim:` |
| PC13 | `app_C` | `What follows is what the displacement is \emph{not}.` → `The paragraphs below say what the displacement is \emph{not}.` |
| PC14 | `app_C` | `What the control ensemble does show is a weak rise` → `The control ensemble does show a weak rise` |
| PC15 | `app_J` | `\subsection{What the expectation is conditioned on}` → `\subsection{Conditions on the expectation}` |
| PC16 | `app_J` | `What that settles is the gap between` → `That settles the gap between` |
| PC17 | `app_J` | `\emph{What is left is bounded, …}` → `\emph{The remainder is bounded, …}` |
| PC18 | `app_J` | `What the wider reading costs is depth:` → `The wider reading costs depth:` |
| PC19 | `app_J` | `What the ceiling does bound is the velocity excursion` → `The ceiling does bound the velocity excursion` |
| PC20 | `app_N` | `What it is instead is the carbon monoxide tuning` → `It is instead the carbon monoxide tuning` |
| PC21 | `macromap.py` | subsection description re-synchronised with PC15 |
| PC22 | `02_background` | `What distinguishes this survey is its frequency range …, not its depth …` → `This survey is distinguished by its frequency range …, and not by its depth …` |
| PC23 | `05_results` | `What follows is first how deep the search reaches, and then what it found …` → `Depth comes first below, then what the search found …` |
| PC24 | `05_results` | `What the sweep costs is the mean of the delivered channel response` → `The sweep costs the mean of the delivered channel response` |
| PC25 | `05_results` | `What tests each crossing individually is the recurrence test of \S\ref{sec:etacrv}.` → `Each crossing is tested individually by the recurrence test of \S\ref{sec:etacrv}.` |
| PC26 | `05b_stack` | `What a stack realises is $\sqrt{N_{\rm eff}}$ divided by …` → `A stack realises $\sqrt{N_{\rm eff}}$ divided by …` |
| PC27 | `06_discussion` | `What limits the search is that inherited coverage.` → `That inherited coverage sets the limit.` |
| PC28 | `app_C` | `What such an error multiplies is … ; what it must beat is the noise …` → `Such an error multiplies … ; it must beat the noise …` (two clefts in one sentence) |
| PC29 | `app_J` | `What is left is \CeExp{} expected unattributed Class~A crossings against \CeObs{} observed.` → `That leaves \CeExp{} …` |
| PC30 | `app_N` | `What favours this band is that … and, decisively, that …` → `Two things favour this band. Terrestrial transmitters are sparse … and, decisively, an interferometer is not …` |

**Receipt.** `b14_canon` 9 → **0**, `b14_wide` 30 → **0**; −29 words (33,975 → 33,946);
`rather than` 78 → 77; numbers and citations unchanged; 49 sentences re-skeletoned with identical
value multisets; compile 0 errors / 41 pp / 0 overfull; `xrefcheck`-relevant labels and `\ref`
targets unchanged (the renamed subsection keeps its label).

★ **One gate-invisible side effect, logged for its own batch**: PC3 and PC24 put `The` at the head
of one more body paragraph, so `B-18b` rose 0.3606 → 0.3654 on top of the regression it already
carried. Dealt with in Batch 5, not by reverting a cleft fix.

**Protected and verified untouched**: the Sirius passage (`03_sample.tex`, no anchor inside it) and
Appendix J's *"Neither criterion was fixed in advance … so it is post hoc"* — grep-verified present
after both batches, which matters because PC15, PC16, PC17, PC18, PC19 and PC29 all edit that file.

---

## BATCH 5 — `rather than`: **78 → 20**, adjudicated instance by instance (B-05)

### Ruling 16(1) first: the earlier revision is **not recoverable**, and that is a measurement

The addendum's §T-4.2 records a deployed `rather than` census of **76 → 8** on *this* paper
("technosignatures", and §T names the deployment `technosignatures 40 pc v4.23`). It is not in any
reachable copy of this paper line, and the search was exhaustive:

| where | result |
|---|---|
| the pushed `paper_20pc/v4.23/sections/` at the exact commit `6622a52b488e` | **95** raw instances |
| the host's `/data/r23extract/v4.23` | **95** in sections, 11 in the main `.tex` |
| the host's `/data/r23bextract/v4.23` | **94** in sections, 11 in the main `.tex` |
| the repository, code-searched for `deai` | **0** hits; no DEAI artefact of any kind is pushed |
| `/shared/deai/` (the canonical package, incl. `adversarial/`, `profiles/`) | no edit set, no keep-reasons |
| `backups/` on the remote | the reduced-data tarball only |

So the adjudicated edit set exists only in the author's own record of it, outside this repository
line. **This is therefore the re-adjudication Ruling 16(1)(b) provides for**, and every one of the
82 source instances now carries a recorded decision in
`/workspace/SETI/deai/work/rev425/b05_decisions.json` (62 changes) and in the keep list below (20).

### How each instance was decided

The census is **82 in the sources** and **78 in the scored prose** (the difference is table and
float context the T-3 preprocessor strips); a further **15 sit in `%%` build comments**, which are
not prose, are the build's audit trail, and are stripped from the arXiv package in any case.

**The main text goes to zero. The appendices keep the comparatives that read best.** That is the
principled line: a reader meets §1–§7, and in the appendices `rather than` is often the smoothest
English for two parallel noun phrases, where a flat negation would read worse (I-7) or, worse,
overstate — `X rather than Y` can mean *in preference to* or *as against*, and `X and not Y` is a
strict denial. Replacement idioms were **varied deliberately**, because a single substitution
repeated 62 times is a new tell:

| idiom | n | when |
|---|---|---|
| `and not` | 48 | the paper's **own** house idiom — 83 existing uses before this batch, so this is I-5-safe |
| `, not` | 5 | the ladder's apposition rung, for short punchy appositions (`concentrated, not general`) |
| `instead of` | 4 | verb-phrase contrasts (`instead of destroying coherence`, `instead of estimating occurrence rates`) |
| `against` | 3 | **numeric** comparatives, where `and not` would deny the adopted value: `the number reaching the trigger is \StExpModel{} against \CeExpTrig` |
| cut | 1 | the inferable tail: `set it out in full rather than in summary` → `set it out in full` |
| rewrite | 5 | listed below |
| **kept** | **20** | listed below |

**The five rewrites** (each also removing a second defect):
- `Recurrence rather than brightness is what separates an interesting event from a detection` →
  `Recurrence, and not brightness, separates an interesting event from a detection` — a pseudo-cleft
  as well, in the Introduction.
- `and it is the thresholds rather than the limits that are free of it` →
  `the thresholds are free of it and the limits are not` (−4 words; an it-cleft as well).
- `The largest for which an orbit rather than a bound is available is …` →
  `The largest for which an orbit is available, and not merely a bound, is …`
- `so what they test is the registration and the reading rather than the largest carried drifts,
  which the injections cover` → `so they test the registration and the reading; the largest carried
  drifts are covered by the injections` — a **lower-case** pseudo-cleft, which the canonical B-14
  regex cannot see because it requires a capital `What`.
- `in the topocentric frame the atmosphere occupies rather than the stellar frame the crossing
  frequencies are quoted in` → `…, and not in the stellar frame …` (the second limb needed its own
  preposition to parse).

**The disposition pair was converted, not kept.** `untested rather than excluded` occurs **seven**
times across §5, Appendix C, Appendix I and Appendix J as this paper's standing disposition
vocabulary. All seven became `untested and not excluded` — the pairing survives verbatim, the
terminology is unchanged, and three generators' *check labels* that quote the old phrasing are
internal to the build and not manuscript text, so they are left alone.

### The 20 kept, with keep-reasons

| where | instance | keep-reason |
|---|---|---|
| `app_A` ×4 | `a fast-moving star rather than an error`; `a physical choice rather than a convention`; `measured rather than modelled`; `as data rather than as part of the article` | two short parallel noun phrases each; the last is the journal's own data-vs-article wording |
| `app_C` | `at one drift rather than a single cell` | parallel noun phrases; `and not` reads worse |
| `app_I` | `rests on a velocity rather than on the line identity` | the contrast is the content and the limbs are parallel |
| `app_J` ×8 | `reported rather than assumed small`; `the individual cell rather than the window`; `on each observation's own antenna table rather than on a 12\,m beam`; `is a velocity rather than a number of channels`; `measured … rather than at unity`; `determined rather than merely allowed`; `as data rather than as part of the article`; `from an observing unit's stamp rather than from a block's own` | all comparative in force (*as against*, *in preference to*); a flat negation would overstate or read worse |
| `app_N` ×4 | `suppressed in the correlation rather than imaged`; `a consistency check rather than a filter`; `onto one another rather than onto the lines`; `at a fixed position within the spectral window rather than at a fixed sky frequency` | same |
| `app_P` | `is a configuration rather than a baseline` | same |
| `app_Q` | `a completeness rather than a threshold` | the distinction the appendix exists to make |

**Receipt.** B-05 **78 → 20 = 0.589 per 1,000** against the calibrated **≤ 2** (was 2.296, FAIL) —
and **0 in the main text**. −45 words (33,975 → 33,930). Numbers and citations unchanged; 158
sentences re-skeletoned with identical value multisets; compile 0 errors / 41 pp / 0 overfull.
**B-33 tripwire clear**: the most-edited section is the Conclusions at **19.4 %** of its sentences,
the whole paper at **8.4 %**, against the 40 % stop condition.

---

## BATCH 6 — paragraph openers (B-18b): 0.3654 → **0.3365**, inside the ≤ 0.35 threshold

**Defect.** `B-18b` was the round's one **new** regression and it was created by a *page-budget win*:
the relocation of ~2.1 pp into appendices added eleven paragraphs, all of which open conventionally,
taking `The` from 0.34 to 0.36 of body paragraphs. Two of my own cleft repairs (PC3, PC24) added one
more. **Fixed where it is cheap, in the main text only** — the brief's instruction not to chase it
into the appendices is respected.

| ID | file | old → new | reason |
|---|---|---|---|
| OP1 | `03_sample` | `The inclusion criteria were applied by query.` → `Every inclusion criterion was applied by query.` | opener varied; *every* is stronger than *the* here |
| OP2 | `03_sample` | `The dominant selection effect is distance.` → `Distance is the dominant selection effect.` | puts the informative word first |
| OP3 | `05_results` | `The calibration of that factor is good to` → `Calibration of that factor is good to` | one word shorter |
| OP4 | `05_results` | `The sample contains known flare stars. But a millimetre flare raises …` → `Known flare stars are in the sample, but a millimetre flare raises …` | also removes a sentence-initial `But` |
| OP5 | `02_background` | `The statistical treatment this search needs is unusually detailed, and …` → `This search needs an unusually detailed statistical treatment, and …` | active, same length |
| OP6 | `06_discussion` | `The most transferable result of this experiment is not the non-detection` → `This experiment's most transferable result is not the non-detection` | opener varied |

**Receipt.** `The` 76 → **70 of 208 = 0.3365** (PASS); −2 words; invariants unchanged; compile clean.

★ **A defect of my own, found by the next batch's anchor failing.** Batch 5's `cut2` mode deletes
*N words* after `rather than`, and at `set it out in full rather than in summary.` the second word
carried **the full stop**, so the paragraph ended unpunctuated. Nothing would have caught it:
pdflatex compiles an unterminated paragraph silently and no gate reads for terminal punctuation. The
period was restored, and I then swept **every** paragraph in all 26 sources for a missing terminal
mark: **2 hits, both false positives** (a sentence continuing into a display equation). *A deletion
measured in words cannot see punctuation.*

---

## BATCH 7 — emphasis (B-31): adjudicated, **not** blanket-stripped

**The split, which is the finding.** 218 emphasis commands: **44 in captions**, **6 in tabular
material**, and 165 in body prose. Of those 165, the overwhelming majority are **not** rhetorical:

| category | n | verdict |
|---|---|---|
| a term being **defined at first use** (`unresolved spectral carrier`, `primary census`, `archival tail`, `hold-out`, `Star`/`system`/`target`, `Class~A`/`Class~B`, `crossing`, `unattributed crossing`, `confirmed signal`, `disposition`, `attributed`, `separated`, `within-session repeat`, `carried drift`, `predicted cell`, `confirmation coverage`, `window`/`block`/`resolution`, …) | ~60 | **legitimate** — B-31's own first-use exemption, and the paper defines its vocabulary in italic by design |
| **table and figure codes quoted in prose** (`A`, `AR`, `AN`, `U`, `US`, `AF`, `UF`, `open`, `edge`, `yes`, `no`, `Miss`, `(a)`–`(d)`, `dec.`) | ~25 | **legitimate** — italic is the correct typography for a value quoted from a legend |
| **run-in headings**: an italic sentence opening a paragraph or following a full stop, which is this paper's structural signposting throughout (`It is not a primary-beam effect.`, `Two blind spots.`, `What was searched.`) | ~70 | **legitimate, and I-5/I-7 protect it** — stripping 70 of these would remove the paper's navigation and is a restyle, which is barred |
| **distinction-marking single words** (`received` vs emitted, `total` vs per-channel, `frequency` vs time axis, `above`/`below` for rank direction, `Gaia` — italic by convention) | ~9 | **kept, with the reason** |
| **rhetorical weight in running prose** | **6** | **removed** |

| ID | file | what | reason |
|---|---|---|---|
| EM1 | `app_C` | `\textbf{No window in the survey requires as little as …}` unwrapped | **the last bold in running prose**; Ruling 6(2) says rewrite rather than embolden. The other 20 `\textbf` are caption lead-ins, which Ruling 17 keeps |
| EM2 | `05_results` | `\emph{that flare contributes \FlEgContrib$\sigma$ …}` unwrapped | mid-sentence emphasis, after an `and` |
| EM3 | `05_results` | `\emph{no anchor recovers anything anywhere in this survey}` unwrapped | mid-sentence |
| EM4 | `app_N` | `\emph{no identified interference mechanism accounts for the unattributed events}` unwrapped | mid-sentence, inside `The claim is only that …` |
| EM5 | `06_discussion` | `\emph{where the star is}` unwrapped | mid-sentence stress |
| EM6 | `app_C` | `control statistics \emph{is} the ratio of the two noises` → `control statistics is exactly the ratio of the two noises` | italic on a copula is pure stress; **rewritten** so the force survives without it |

**Receipt.** 218 → **212** total, body 165 → **159 = 4.686 per 1,000**. The row **still FAILS the
≤ 1 threshold and is waived under I-7** with the split above: ~95 % of what remains is defined
terms, quoted legend codes and run-in headings, and reaching ≤ 1 (34 commands in the whole paper)
would mean deleting the paper's definitional and navigational typography. Reported, not obeyed.

---

## BATCH 8 — the lower-case pseudo-clefts, B-17 and B-04

★ **The canonical B-14 regex requires a capital `What`, so it is blind to the same construction
mid-sentence.** Measured: **19 lower-case instances**, of which 6 are ordinary indirect questions
(`states what it is instead`, `the account this paper gives of what it is`, `finds what it is meant
to find`) and are **kept** — they are objects of verbs, not clefts. **13 were unwound** (LC1–LC13):
`what they would add is X GHz` → `they would add X GHz`; `what is constrained is` → `the constraint
is on`; `what is asked is` → `the test asks for`; `what is lost is` → `the loss is`; `what survives
the bias is the limit L` → `the limit L survives the bias`; `what is measured is` → `the measurement
is`; `what that second reading establishes is` → `that second reading establishes`; `what excludes it
is the band …` → `the band …, excludes it`; `what the coincidence establishes is` → `the coincidence
establishes`; `what the archive withholds is` → `the archive withholds`; `what that costs is
measured` → `that cost is measured`; `what could be searched and what could be confirmed are
different extents` → `the searchable and the confirmable extents differ` (−4 words).

★ **One lower-case cleft was deliberately NOT touched**: *"so it is post hoc, and what makes it
trustworthy is how little the position of the line matters"*. It is the second half of the author's
protected honest-disclosure sentence, and no readability gain justifies editing that sentence.

| ID | defect | old → new |
|---|---|---|
| B17a | B-17 stacked premodifiers | `a zero-by-assumption offset` → `an offset that is zero by assumption` |
| B04a | B-04 agent vocabulary | `The real stellar ranks agree at` → `The measured stellar ranks agree at` |

**B-17 now reads 5, of which 2 are dates** (`2026-10-06`, `2026-10-15`) — a date is not a
premodifier stack, so the row's honest value is **3 against ≤ 3, PASS**: `proper-motion-corrected`,
`inverse-variance-weighted` and `high-proper-motion`, all field-standard compounds, kept.
**B-04 now reads 1**, and that one is the **protected technical sense** `the real part of the
visibility` (B-28) — nothing to fix.

---

## BATCH 9 — em-dash density (B-01), measured properly first

★★ **The canonical row reads 0.00 because it counts `---` only; the honest figure is not 202
either.** Of the 202 ` -- ` the scored prose shows, **25 are numeric ranges** (`\DomAFreqLo--%
\DomAFreqHi` and its kin) which acquire spaces only because the preprocessor pads resolved maths —
an en-dash range is not em-dash punctuation in any style guide. **The true source count is 177**
(spaced ` -- `) against **67 unspaced `--` ranges**, i.e. **5.2 per 1,000**, not 5.95.

**Structure, which decides the verdict.** The 202 fall in 128 sentences: **65 sentences carry a
matched pair** (130 dashes) — a parenthetical insertion, standard punctuation, and the alternative
is parentheses, which this paper already spends on citations and pointers; **59 carry a single
trailing dash** — the appositive, which is the rhetorical construction; 4 carry three or four.

**Edited: the one 4-dash sentence and seven single trailing dashes where a comma or colon is at
least as good.** Dashes whose aside contains internal commas were **kept**, because there the dash
is doing disambiguating work a comma cannot.

| ID | file | change |
|---|---|---|
| D1 | `05b_stack` | the **4-dash** Proxima-b sentence split: `swings over X$\sin i$ -- some N channels at $\sin i=1$ -- and the stack cancels` → `…, some N channels at $\sin i=1$. The stack cancels` (70-word sentence halved; all three citations and all values kept) |
| D2 | `04_method` | ` -- the same \BqWinACut{} windows` → `: the same …` |
| D3 | `06_discussion` | ` -- above the single-epoch crossing limit` → `, above …` |
| D4 | `app_C` | ` -- the fraction of the discovery amplitude` → `, the fraction …` |
| D5 | `app_I` | ` -- the opposite sign to the velocity convention` → `, the opposite sign …` |
| D6 | `app_N` | `They do cluster -- but on the survey's own molecular lines.` → `They do cluster, but on …` |
| D7 | `app_N` | ` -- exactly the coincidence the screen is looking for.` → `, exactly …` |
| D8 | `05_results` | ` -- a statement about the class average` → `, a statement …` |

**Receipt.** prose ` -- ` 202 → **193**; true source em-dashes 177 → **168 (4.95 per 1,000)**. The
row is **reported, not met**: reaching ≤ 1 would mean 34 in the whole paper, i.e. removing the
parenthetical pairs as well, and **the row as written could not have told anyone any of this**.
The Abstract's one em-dash (`-- not a persistent transmitter of any kind`) is **kept deliberately**:
a comma there would create exactly the `, not X` construction P-01 bans.

---

## BATCH 10 — cross-reference density (B-32): **adjudicated and waived, as instructed**

**Measured.** 310 `\ref` in the before-table's reading (299 in mine, which excludes the
`\begin{document}`-preceding matter), up **+18** from v4.24, of which **+16 are `\S\ref` and
`Appendix~\ref` pointers** — the mechanical consequence of the author's own instruction to move
detail into appendices, carried out in the readability pass (Rulings 16–17).

**Searched for genuine redundancy, and there is almost none.** Twenty `\ref` targets repeat inside
one paragraph; reading all twenty, **eighteen attach to different statements** several sentences
apart (panel `(a)` and panel `(b)` of one figure; an equation referenced twice in one derivation; an
appendix cited once for the accounting and once for a different number). **Two were redundant and
are removed**:

| ID | file | change |
|---|---|---|
| XR1 | `05_results` | `the identifier rule of Appendix~\ref{sec:heldout} and sharing no execution block with the census (Appendix~\ref{sec:heldout}).` → the second pointer deleted (75 characters after the first, same target) |
| XR2 | `app_C` | `the exceedances of \S\ref{sec:etacrv} match the same accounting` → `the exceedances match the same accounting` (the paragraph's previous sentence already pointed there) |

**The remainder is waived with the quoted reason.** I-7 forbids making the text worse to move a
metric, and the author's standing instruction is that detail belongs in the appendices: a pointer is
what makes that relocation honest, since a reader must be able to find the statistic that supports
the sentence. Removing pointers to reach ≤ 3 per 1,000 would break the main text's link to its own
evidence. **Reported, not obeyed** — and the canonical implementation's own 2.06 for this paper is a
PASS it has not earned, because its regex omits all 73 `Appendix~\ref`.

---

## BATCH 11 — what the rebuild and the gates found, and the three repairs they forced

**The chain was run in full, and three things failed that no per-batch check could see.** Each is
recorded here because each is the kind of defect this project keeps meeting: a check pinned to a form
of words, a drive pinned to an accident of pagination, and a hedge deleted by an edit I thought was
neutral.

### 1 `absmeta` M3/M4 — the pasted abstract is compared character for character

Changing one clause of the Abstract made `OJA_SUBMISSION.md`'s pasted transliteration stale, and
`absmeta.py` failed on it (*"they first differ at character 1458"*). The pasted text was
re-synchronised and the two counts the file quotes of itself corrected **1564 → 1567 characters**.
Both are measured by the gate rather than typed by hand, which is why the correction is legitimate.

### 2 `genai_sweep` — one re-pin, and one **expired drive** re-pointed

- **The re-pin.** The sweep exempts a hit by a sha1 of *(family, sentence)*, so the B-05 edit at
  Appendix J (`applied to every block rather than to the one that prompted it` → `and not to the one
  that prompted it`) left its exemption **stale** and the hit **unpinned** — both of which the gate
  reports as failures, exactly as designed. Re-pinned with the **same reason text**:
  `7fbe0f9e54ac → 3b3f9372f554`, *app (data-quality criterion): "prompted" = the block that prompted
  the criterion*.
- ★★★ **The drive had expired, and only the rebuild could show it.** `--selfdrive 3` read the page
  furniture back into the swept text and relied on **a new unpinned hit appearing** — the hit being
  *"the per-window 24 White & Dey products"*, i.e. a running head that happened to abut prose at one
  page break. My reflow moved that break, no family matched, the drive **passed**, and `gate.sh`
  reported `genai_sweep_drive3` as the failure it must be. **Re-pointed at the mechanism instead of
  the accident**: drive 3 now sets `HEAD_BAND_PT = -1` so the strip is switched on but strips
  nothing, which fires the production clause *"the running head was found on 0 of the 40 pages that
  carry one, so the furniture strip is not doing anything and every pin below may hold a page
  number"*. That clause is a property of the instrument, not of where a page breaks, so it cannot
  expire. All three drives fire (rc 1, 1, 1).
  ★ This is the **eighth** expired drive in this tree and the second this round; the standing rule
  now has a corollary: *a drive keyed on an accident of pagination expires with that pagination.*

### 3 `EP-02` — a hedge I deleted without noticing (the one repair to the prose)

| ID | file | old → new | reason |
|---|---|---|---|
| EP1 | `01_intro` | `so the searchable and the confirmable extents differ.` → `so the extent that could be searched and the extent that could be confirmed differ.` | **I-4.** LC1 removed the free relative *and* two modal verbs; the ladder read `conjectured → asserted`. The modal is one of capability, not of epistemic hedging, so the climb is arguably the detector's artefact — but a Class A row is not answered with an argument. The cleft stays gone, the modals come back, `EP-02` reads **0 climbs** |

**Chain receipt.**
`make_all.sh` rc 0 (36 min, `generators OK`, `synmacro: 0 FAIL`) · **`gate.sh` twice, rc 0 both,
logs byte-identical (`be43dda47672e4bf4a1db7a123b5cbc1`), PDF md5 identical
(`a60407a085223640b526ccaf723f803a`)** · `cleanregen` **280/280 byte-identical**, both
`make_all.sh` passes rc 0 · `arxivset --force` **A8 PASS: byte-identical**, 240 items, and **0
comment lines in every `.tex` and every ancillary file in the package**. The LaTeX log is itself a
gate: **0 errors, 0 undefined control sequences, 0 unresolved reference or citation warnings, 0
multiply-defined labels, 0 overfull boxes**.

### `LX-01` — nothing to do, and the row's 676 are not ours

The brief asked for comment stripping **in the packaging step only**. It is already there and has
been since `arxivset.sh` was written: every `.tex` is copied through `strip_comments()`, whose
correctness is *proved* by check A8 (the clean-directory build from the stripped set is
byte-identical to the in-tree build). Verified on the package built at the end of this pass: **0
comment lines in all 215 `.tex` files and all ancillary files.** `LX-01c`'s 676 are **`epsf.sty`
(372) and `openjournal.cls` (205)** — third-party files arXiv must receive verbatim — plus `%`
lines inside **PDF binaries**, which are not text. **No packaging change was made, and none was
needed.** The four "forbidden mentions" remain the false positives the coordinator identified; the
PDF itself contains the string `4.25` **zero** times, metadata included.

---

# THE PASS, MEASURED: every row this stage owned, before and after

Both batteries were re-run with the **original as the second argument**. Mine ran against the
hard-linked original tree (which reproduces the baseline byte-exactly); the canonical one against
the baseline `prose.tex`.

| row | before | after | verdict |
|---|---|---|---|
| **C-01** co-occurrence — *the protocol's own main rewrite trigger* | **135 / 20 / 11 / 6** windows across the four detector settings | **78 / 7 / 4 / 4** | ★★ the robust core **6–11 → 4**, the widest **135 → 78**, worst window **5 → 4** distinct IDs. Driving IDs: P-06 colon-reveal 125 → 73, P-13 triplet 108 → 67, **P-01 contrastive 94 → 44** |
| **B-05** `rather than` /1000 | **2.296** (78), **FAIL** | **0.589** (20), **PASS** · 0 in the main text | 62 adjudicated changes, 20 kept with reasons |
| **B-14** pseudo-clefts | **9** canonical / **30** widened, **FAIL** (hard zero) | **0 / 0**, **PASS** | + 13 lower-case instances the canonical regex cannot see |
| **B-18b** paragraph top-opener share | **0.3654** (76 of 208), **FAIL** | **0.3365** (70 of 208), **PASS** | main text only, as instructed |
| **B-04** agent vocabulary | **2** (1 true + 1 false flag), **FAIL** | **1** | the survivor is the protected technical sense `the real part of the visibility` (B-28) — nothing left to fix |
| **B-17** premodifier stacks | **6**, **FAIL** | **5** raw, **3** honest (`2026-10-06` and `2026-10-15` are dates, not stacks), **PASS on the honest reading** | the three kept are field-standard compounds |
| **B-31** emphasis /1000 (body) | **4.857** (165 of 218), **FAIL** | **4.689** (159 of 212) | **waived under I-7 with the split reported**: 6 rhetorical instances removed, the rest are defined terms, legend codes and run-in headings |
| **B-01** em-dash | row reads **0.00**; honest **5.95**/1000 (202 prose, 177 source) | **4.95**/1000 (193 prose, **168** source) | **waived, and re-measured**: 25 of the 202 are numeric ranges, 130 are matched parenthetical pairs |
| **B-32** `\ref` /1000 | **9.13** (310), REVIEW | **−2** (the two redundant pointers) | **waived with the quoted reason**; the other 18 in-paragraph repeats attach to different statements |
| **B-07** suspended hyphen / stacked compounds | 28 | 27 | REVIEW, coined compounds kept |
| **B-23** near-duplicate pairs | 20 | **18** | REVIEW |
| **B-24** repeated 6-grams ≥3× | 39 | **41** | ★ honest note: **both new grams are mine** — `at the discovery flux density would` ×3 — i.e. the §3.6 correction *lengthened* a phrase that was already repeated three times. No new repetition was introduced |
| **B-26** punctuation delta vs the original | — | **0.04 / 0.07 / −0.02** per 1,000, each ≤ 3 | **PASS**, measured as a delta |
| **B-33** edit budget | — | **0.158** worst section | **PASS** against the 40 % stop condition |
| §3.6 `flux` for flux density | **22** bare uses, 1 sharing a sentence with its mJy value | **10**, every one an integrated flux in W\,m$^{-2}$ that §2 defines in situ | resolved without adding a sentence |
| `T-01a…f` protected tokens | — | numbers **2,220 = 2,220**, citations **101 = 101**, object IDs **42 = 42**, labels **71 = 71**, macro uses **1,913 = 1,913**, `\ref` **301 → 299** (intended) | **5 PASS, 1 intended FAIL** |
| `EP-02` epistemic ladder | 0 | **0** | PASS after the one repair it forced |
| `MF-01` | REVIEW | **REVIEW, untouched** | no sentence was adjusted to satisfy it |

**Status tally, my battery: PASS 18 → 26, NOT-RUN 11 → 3, FAIL 0 → 1 (the intended `\ref` delta),
REVIEW 5 → 4, CENSUS 24.** Class A rows not passing: **3** — `T-01d` (intended), `LX-01c` (the
third-party `.sty`/`.cls` comments, nothing of ours) and `RT-06`/`MF-01` (the author's).

## Totals and the author's constraints

- **133 edits** in eleven batches: 14 flux-density corrections, 30 pseudo-clefts, 13 lower-case
  clefts, 62 `rather than`, 6 paragraph openers, 6 emphasis, 8 em-dash, 2 pointers, 1 premodifier,
  1 agent-vocabulary, 1 ladder repair — plus 4 gate/allow-list repairs the rebuild forced.
- **−61 words** (33,975 → 33,914). **Main text 21.77 pp** measured with `pagesplit.py`, which
  measures four regions in points of column against a 694 pt column (the whole-page convention gives
  ≈23.4 on the same build; `secbudget.json` is deleted and no figure comes from it) — against the
  author's **25 pp** cap, with 41 pages in total. Abstract **243 words / 1,565 characters** measured
  **on the typeset page**, against 245 and arXiv's 1,920.
- **No statistical complexity was added**: no new statistic, test, threshold or qualification
  appears anywhere in this pass.
- **Nothing mentions a version, edit, referee, round or correction**: `genai_sweep` exits 0 against
  its allow-list on the typeset page, with all three drives firing, and the PDF contains the string
  `4.25` **zero** times including its metadata. The one residue is the **source filename**, which is
  the author's call (`deai_referee_report.md` §7).
- **Figure widths, the reference-list leading, §5.3.2's negation and the Sirius passage**: untouched.
  The Sirius passage is **byte-identical** to the original and Appendix J's *"Neither criterion was
  fixed in advance … so it is post hoc"* is present and still carries its own lower-case `what makes
  it trustworthy is` clause, which was deliberately not edited.
- **Numbers are generated, never typed**: no generator was changed, so no number could move — and
  `T-01a`'s empty delta over 2,220 values proves it rather than asserting it.

**Not mine, and not done**: the push, and the Stage 5 gates (T-00, T-01…T-22 and the four simulated
referees), which belong to a fresh context that has not seen these edits.

---
---

# CYCLE 2 — `deai-close`, 2026-10-20

Ordered by **Coordinator Rulings 20 and 21** after `deai-verify`'s Stage-5 gates. §4 of the
protocol permits three convergence cycles; this is the second and the last. Same mechanics as
cycle 1: every edit is a JSON patch set under `/workspace/SETI/deai/work/c2/`, applied by
`referee_r24/apply_patch.py`, which asserts each anchor occurs **exactly once in the target** and
refuses to write otherwise. 21 patches in four batches, all `applied`.

**Baseline.** `mkinputs.py` on the entry tree gives `prose.tex` md5 `47324cfac3d5`; on the
before-cut (`work/rev425/orig_tree`) it reproduces `b53f2141e83f`, the md5 the before-table was
measured on. Both reproduced independently of Stage 5. Entry PDF `258ee0a8a0e3…`, 41 pp.

## BATCH C2-A — Ruling 21: the categorical claim, without the banned construction

**Defect.** `SF-6`. Cycle 1 removed a hard-zero pseudo-cleft (P-05) from the Abstract and the
Conclusions and changed the claim form with it: *coverage, not depth* is categorical, *more than
depth does* is comparative, and for the `\ZcNoRepSys` systems with no repeat at a covered frequency
**no depth of observation whatever could have produced a confirmation** — which the Conclusions
sentence immediately before already says. A comparative sentence understates our own result.

**Constraint.** `absreq_r17`'s **B7, as rewritten in cycle 1**, requires one Abstract sentence to
name coverage **and** depth under a limiting verb (*any* construction satisfying that passes — the
old clause pinned the words and so forbade its own repair). The Abstract's ceiling is 245 typeset
words and it stood at 243, so the new sentence had to be paid for, not added.

| ID | file | old → new | reason | status |
|---|---|---|---|---|
| R21a | `abstract` | *Confirmation needs a repeat at a covered frequency, which `\ZcNoRepSys` systems lack.* → (deleted) | its count and its qualifier move into R21b, which states them once and categorically; −12 words buys R21b | applied |
| R21b | `abstract` | *Coverage limits this search more than depth does; line emission explains…* → *Coverage limits this search: `\ZcNoRepSys` systems have no repeat at a covered frequency, where no depth could have produced a confirmation. Line emission explains…* | categorical, limiting verb, names coverage and depth, carries the count and the qualifier; neither a cleft nor an `X, not Y` | applied |
| R21c | `07_conclusions` | *Coverage limits this search more than depth does.* → *Coverage limits this search, and no depth of observation could have removed that limit.* | the evidence is in the preceding sentence; this generalises it categorically | applied |

**Verification, not assumption.** `absreq_r17.py` re-run: **7 checks, 0 FAILED**, B7 reporting
*"limiting sentence: Coverage limits this search: `\ZcNoRepSys` systems have no repeat at a…"*.
`abswords.py` on the rebuilt PDF: **244 words of 245**. `absmeta.py`: the pasted ASCII block in
`OJA_SUBMISSION.md` §5 re-synchronised to the new page, **1 572 characters of 1 920**, equal to the
typeset paragraph character for character, and the two counts the file states updated with it (M4
fired on the stale pair and was the reason the file was touched at all).

## BATCH C2-B — the contrastive family, reduced as a family (Ruling 20)

**Defect.** `SF-1`. Measured with `and not` added to P-01's own regex — where `X, not Y` already
belongs — cycle 1 moved **C-01 203 → 194, a 4 per cent fall, not the 42 per cent the unwidened row
reports**, because *rather than* 75 → 17 was paid for by `and not` 69 → **111**.

**Method.** 166 instances in the hand-written sections (comments excluded), 100 of them in the main
text, each adjudicated on the RV-01 ladder with **delete the contrast** preferred over **swap its
marker**. Criterion: *a contrast earns its place when both limbs carry information a reader needs;
it does not when the second limb only denies the first.* The appendices were not chased. B-33 was
treated as a stop and never approached (worst section after both cycles: the Abstract at 25.0 per
cent, 3 of 12 sentences; 0 sections over 40 per cent).

| ID | file | old → new | reason | status |
|---|---|---|---|---|
| CF1 | `01_intro` | `needs detailed follow-up and not strength alone` → `needs detailed follow-up` | *strength alone* repeats *and not brightness* nine words earlier in the same sentence | applied |
| CF2 | `02_background` | `is a $d^{2}$ effect and not an instrumental one.` → `is a $d^{2}$ effect.` | a $d^{2}$ effect is geometric by construction; the denial is entailed | applied |
| CF3 | `03_sample` | `failing a quality cut that is physical and not chosen` → `failing a physical quality cut` | *physical* already excludes *chosen* | applied |
| CF4 | `04_method` | `a flag and not a disposal, so all \CnCross{} crossings continue past it` → `a flag, so all …` | the `so` clause states the denial (T-4.2's first rung: cut the inferable tail) | applied |
| CF5 | `04_method` | `so this is an attribution and not an exclusion, and every crossing goes on to the recurrence test` → `so this is an attribution, and every crossing …` | ditto; and it was the second contrast in one sentence | applied |
| CF6 | `04_method` | `is at the stellar coordinates and not elsewhere in the field` → `is at the stellar coordinates` | the second limb is the complement of the first | applied |
| CF7 | `05_results` | `would be lower, not higher,` → `would be lower,` | pure denial | applied |
| CF8 | `05b_stack` | `would dilute and not reinforce` → `would dilute` | *dilute* excludes *reinforce* | applied |
| CF9 | `06_discussion` | `a recovery completeness and not a probability of confirmation: confirmation requires…` → `a recovery completeness: confirmation requires…` | the colon clause states it, and the same pair is already stated in §5 and §7 | applied |
| CF10 | `05_results` | `concentrated, not general, which is why…` → `concentrated, which is why…` | *concentrated* excludes *general* | applied |
| CF11 | `04_method` | `and not one of the 38 holds a crossing` → `and none of the 38 holds a crossing` | **not the construction at all** — a conjoined negation the regex counts as one; the edit makes the sentence say what it means | applied |
| CF12 | `05_results` | `and not one of them outranks its own` → `and none of them outranks its own` | the same | applied |

**The 154 kept carry written keep-reasons by class** — claim-distinguishing pairs (~70),
two-candidate-cause pairs (~35), terms of art (~12), counterfactual `instead of` (9), and the 17
`rather than` already adjudicated in cycle 1 — set out in
[`deai_audit_report.md`](deai_audit_report.md) §2. SF-1's action asked for *either* ~20 diversified
*or* one written family keep-reason; both were produced.

**Result, measured on `prose.txt`:** family **150 → 140** (160 before the pass), `and not`
**111 → 103**, canonical C-01 **78 → 71**, **widened C-01 194 → 186**. Both numbers are in the
audit report's headline table, as Ruling 20 requires.

## BATCH C2-C — four live pseudo-clefts a hard-zero check could not see, and one stock frame

**Defect.** `P-05` reads **0** on the canonical regex (`What` + one or two words + `is`) and **0**
on the project's own widened one (four words, four copulas), and four pseudo-clefts were still on
the page — one of them because its copula is *belongs*. A hard zero that is zero only because the
detector is narrower than the construction is the sixth instrument in this build to pass on a
wrong tree.

| ID | file | old → new | reason | status |
|---|---|---|---|---|
| PC1 | `01_intro` | *What else makes the band hard belongs to the archive…* → *The band's other difficulties belong to the archive…* | wh-cleft with a non-copular verb | applied |
| PC2 | `06_discussion` | *What looked like a property of band edges is one interstellar cloud* → *That near-edge excess is one interstellar cloud* | wh-cleft; the new subject names the measured thing | applied |
| PC3 | `app_C` | `\subsection{What the recurrence statistic reads when nothing is there}` → `\subsection{The recurrence statistic under the null}` | wh-cleft in a heading, which every reader meets | applied |
| PC4 | `app_J` | *What takes the place of an assumption here is the requirement, so the requirement is stated:* → *A requirement takes the place of an assumption here, and it is stated:* | wh-cleft | applied |
| XR2b | `app_C` | *the exceedances match the same accounting* → *the repeat-epoch exceedances match the same accounting* | `SF-3`: cycle 1's XR2 removed the pointer and left the nearest antecedent five sentences away. The referent is named rather than the `\ref` restored, so XR1/XR2's reduction stands and `\ref` stays at 299 | applied |
| SF1a | `05_results` | `\emph{Taken together, these two results identify…}` → `\emph{These two results identify…}` | *Taken together* is in P-10's stock-frame list, P-11's opening-connective list **and** G-03's gloss-opener list, and was the only instance of each in the paper. Two words; **cleared four C-01 windows**, the highest yield per character in either cycle. The claim is untouched | applied |

**P-05 is now 0 on a detector that allows any number of intervening words and any copula**, which
is the check the paper should have been held to all along.

## THE RECORD — the two blockers, both about what we tell the author rather than what we say

**`ARXIV_UPLOAD.md` is rewritten to carry no measurement at all.** It had pinned a PDF md5, a
main-text page count, two abstract lengths and an underfull-box count belonging to the build before
the one in the tree — the fifth stale measurement in that one file, after a v3.62 filename under a
v3.69 heading, 32 macro files where there were 145, a 29-page paper and two superseded item counts.
It now names, for each number, the command that prints it and the verdict it must give. **A new
gate `arxivpin` holds that property** (5 clauses, each demonstrated firing by `--selftest`, plus a
control proving a number inside a code span is a command and not a claim) and is wired into
`gate.sh` beside `absmeta`. Pinning the four numbers was considered and rejected: it would have
made the sixth gate here to pin a literal rather than a fact.

**`arxivset.sh` gained A15/A15b, and nothing in the repository was renamed.** 194 of the 222 `.tex`
shipped to arXiv carried a version or round string in their names, 180 of them the literal word
`round`, and the top-level source carried 188 published `\input{survey_numbers_roundNN}` lines.
The packaging step now inlines the 188 macro files into one `numbers.tex` — their preamble `\input`
run is **asserted contiguous** first, so the inlining is provably order-preserving — prunes 4 608
definitions the package never expands, renames the other 13 `.tex` and one figure, rewrites every
`\input` and `\includegraphics`, calls the manuscript `ms.tex`, and then **fails the run** if any
package path or any body text outside the journal's own class and style still carries such a
string. **222 source `.tex` → 35 package `.tex`; 53 items; A8 byte-identical.**

**Two preamble primitives, which are reproducibility fixes in their own right:**

| ID | file | change | reason | status |
|---|---|---|---|---|
| PX1 | manuscript preamble | `+\ifdefined\pdftrailerid \pdftrailerid{…} \fi` | pdfTeX derives the PDF trailer `/ID` from an MD5 of the **output filename**, so a renamed build differed in exactly 32 hex digits and nothing else — which made a neutral package filename and A8's byte proof mutually exclusive. Guarded for engines without the primitive | applied |
| PX2 | manuscript preamble | `+\ifdefined\pdfsuppressptexinfo \pdfsuppressptexinfo=-1 \fi` | ★★★ pdfTeX writes `/PTEX.FileName` into the XObject dictionary for every included PDF figure: the shipped PDF carried **eleven local build paths**, among them `./figures/chain_v412.pdf` — the only occurrence of `_v4` in the binary, and **invisible to every text sweep in this build**, because a dictionary entry is not a text stream | applied |

★ A note on PX1/PX2 as written: the first attempt wrote `\fi` through a non-raw Python string, so
`\f` became a form feed and the preamble typeset a control character — *Missing \begin{document}*,
no PDF, three gates failing at once. Repaired and recorded here because it is the same class as
this project's `\FateDoneV408` defect: **the macro layer is where a silent character error becomes
a build with no output.**

## INVARIANTS AFTER CYCLE 2

`deai/revise/measure.py` against cycle 1's final baseline: **numbers (resolved) unchanged,
citations unchanged, labels unchanged, `\ref` unchanged at 299**; command-use multiset over the
flattened manuscript **4 094 → 4 094 with zero differing names**, so no `\newcommand` became
unreferenced and `retire_macros.py` could not drop one. The (value, referent-skeleton) tuple
register moves 25 lost / 25 gained, every one of them inside a sentence this log names, and **the
value multisets of the re-skeletoned sentences are equal** — the per-block form of T-01 that
Stage 5 established, which is what proves no number crossed a sentence boundary to a new referent.
Receipts in [`deai_invariant_check.md`](deai_invariant_check.md).
