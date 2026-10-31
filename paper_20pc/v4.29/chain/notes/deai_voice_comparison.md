# `deai_voice_comparison.md` — §T-6 deliverable, **REPORT-ONLY**

`deai-close`, 2026-10-20. Instrument: canonical `/shared/deai/` → `deai/canon/deai_voice.py`,
profile `deai/canon/profiles/white_profile.json` (25 topic-robust features, Fisher-selected per
§T-2.1, sd-floored per §T-2.2).

---

## 0. THE GATE IS OFF, AND THIS FILE SAYS SO BEFORE IT SAYS ANYTHING ELSE

**B-37/B-38 are CONDITIONAL on S-01, and S-01 FAILED for this profile.** §T-2.3 records the
deployment result: the held-out author papers and the matched other-author controls **separate in
the mean (0.89 against 1.20) but their tails touch**, so a single distance cannot tell an author
paper from a control. The addendum's own ruling follows: **the voice gate is permanently
REPORT-ONLY for this profile**, B-37/B-38 produce diagnostics with keep-reasons, and **no sentence
in this paper was moved because of a distance.** None was.

★ §R in full: this is a stylometric distance between distributions a human can see. It cannot
detect, measure, or certify the removal of a key-based statistical watermark, and **no claim about
a watermark appears anywhere in this pass**. No 0–100 score and no "AI probability" is emitted.

---

## 1. Distance D, and why there are two of them

| text scored | D |
|---|---|
| **v4.24**, `prose.txt` — macro-resolved, §T-3 preprocessed | **1.037** |
| **v4.24**, the manuscript `.tex` through the tool's own strip | **1.205** |
| v4.25 before the DEAI pass, `prose.txt` | 1.067 |
| v4.25 after cycle 1, `prose.txt` | 1.071 |
| **v4.25 after cycle 2, `prose.txt`** | **1.072** |
| v4.25 before the pass, `flat.tex` (unresolved, tool-stripped) | 1.131 |
| v4.25 after cycle 2, `flat.tex` | 1.140 |
| v4.25 after cycle 2, the 263-line main `.tex` alone | 2.603 |
| author holdout band (S-01 validation) | mean 0.89 |
| other-author control band (S-01 validation) | mean 1.20 |

**The two numbers for one text are the whole methodological point.** `prose.txt` is built by
`mkinputs.py`: it resolves the 6,034-value macro layer to its *values* and then applies the §T-3
preprocessor. The canonical preprocessor alone does not resolve macros — **it strips them to
nothing** — so a sentence like *"The median system's best window triggers on `\EirpNinetySysMedA`
W nine times in ten"* loses its subject, and sentences that are mostly macro collapse to
fragments. The visible symptom is in the per-feature breakdown: scoring the raw main `.tex`,
**`Ssd` (sentence-length standard deviation) is z = 12.49 and `Sshort` z = 7.38**, both artefacts
of a document reduced to `\input` lines and preamble. On v4.24's inlined manuscript the same
mechanism put `Ssd` at z = 4.00 and carried D from **1.037 to 1.205**.

★ **So 1.037 / 1.072 is the honest figure and 1.205 / 2.603 is an instrument artefact**, and
addendum §T-5.4 settles which text is the subject: *"a macro-dense source is build engineering, not
an AI-prose tell — DEAI scores the rendered text, never the macro layer."* §T-3's own symptom note
(Dr 2.60 → 1.22 after stripping) is the same observation from the other side.

## 2. What the two cycles did to D — essentially nothing, and that is the correct result

**1.067 → 1.071 → 1.072.** The pass moved the manuscript's voice distance by **+0.005**, which is
0.4 per cent and is inside the noise of a 25-feature mean-|z|. That is what RV-01 (default to
preserve, 136 of 1,185 sentences touched, B-33 worst section 9.7 %) should do to a stylometric
distance, and it is the evidence that the revision edited features rather than rewriting the
author's hand.

**B-38** (changed vs unchanged sentences) is **NOT-RUN**: the changed set is 136 sentences of
~5,300 words, and this profile's features are rates per 1,000 words over documents of ~34,000.
Scoring a 5,300-word sub-corpus against a document-level profile would produce a number with no
calibration behind it, and §Q is explicit that a deferred test is recorded, never silently passed.
The sentence-level evidence that the new text is not worse is `B-29` (next file,
`deai_battery.md`), reported with its selection confound.

## 3. Per-tell rates, before and after, with edit counts (§T-4.1)

Measured by `deai_voice.py --tells` on the macro-resolved prose.

| tell | before | after | edits | per 1,000 words, after |
|---|---|---|---|---|
| `rather than` | **75** | **17** | 58 changed, 20 kept with written reasons | 0.51 (was 2.22) |
| `not only` | 3 | 3 | 0 | 0.09 |
| `in summary` | 1 | **0** | 1 | 0.00 |
| triads (`a, b, and c`) | 143 | **149** | 0 | 136.95 |

★ **And the row that matters is not in this table, because the tool has no detector for it.** The
58 `rather than` edits moved the construction rather than removing it: `and not` went **69 → 111**
in cycle 1 before cycle 2 brought it to **103**, and the contrastive family as a whole went
**160 → 150 → 140**. The full accounting, measured on a widened P-01 regex, is the headline of
[`deai_audit_report.md`](deai_audit_report.md) §1 and must be read with this table, not instead of
it. A per-tell census that counts only the markers it was given will always report a substitution
as a success.

★ The triad count **rose by 6** and no triad was written by the pass. `--tells` counts any
`a, b, and c` on the page, and this paper's are lists of stars, of frequencies and of execution
blocks whose length is set by the data; P-13's own clause keeps those. The rise is a side effect of
sentence splits and merges elsewhere redistributing commas, not of new rhythm.

## 4. Residuals, with keep-reasons (§T-6.6)

The five features furthest from the profile, after:

| feature | value | profile | z | keep-reason |
|---|---|---|---|---|
| `hd:would` | 2.65 | 0.86 | 2.63 | *would have produced / would have been confirmed* is the counterfactual this paper is about: a completeness limit is a statement about what **would** have been detected. Removing the modal would change the claim (I-4; EP-02 caught cycle 1 deleting two such modals and they were restored). |
| `O:in` | 8.27 | 51.71 | 1.97 | sentence-initial *In…* openers. The author's corpus opens on them far more often; this paper opens on its subject instead, which W-06 asks for. Moving toward the profile here would mean adding connectives. |
| `Zreport` | 6.66 | 12.66 | 1.84 | reporting verbs (*we find, we report*). A null-result paper reports fewer results; the rate follows the content. |
| `Slong` | 286.8 | 162.0 | ~1.6 | long sentences, driven by the numeric clauses this paper cannot do without (*31 against 24.6 expected, P = 0.13, over 399 windows*). S-01 being failed, there is no threshold to hold this against. |
| `O:however` | 0.00 | 20.55 | 1.60 | the paper uses **no** sentence-initial *However*. That is a distance **from** the author's habit and toward journal style; the pass did not create it and will not create one to close it. |

## 5. Honest verdict (§T-6, §R wording rules)

**What the voice work did:** it measured the manuscript three ways against a 25-feature profile
built from the author's own corpus, showed the two DEAI cycles moved the distance by +0.005, and
produced the per-tell census that exposed cycle 1's substitution — the single most useful thing it
did, and it did it by being read against a different instrument rather than on its own.

**What it did not do, and cannot:** it did not validate. S-01 failed, so the distance has no
decision threshold here, and nothing in this file is a pass or a fail. It did not move a sentence.
It did not, and could not, say anything about watermarking. And it is not evidence that the prose
is or is not machine-assisted — that question is answered by the disclosure in §8 of the paper,
which is the mandated and only honest mechanism (ST-04).

**Reproduce every number above:**

```
python3 deai/canon/mkinputs.py <tree> --out <dir>            # flat / resolved / prose
python3 deai/canon/deai_voice.py score deai/canon/profiles/white_profile.json <dir>/prose.txt
python3 deai/canon/deai_voice.py score deai/canon/profiles/white_profile.json <dir>/prose.txt --tells
```

The preprocessed dumps this file was scored on are kept at `deai/work/c2/{before,base,after}/`
(§T-6.7), beside the strip script that made them.
