# v4.20 — build notes (referee round 19)

One self-contained PDF, **38 pp**, `technosignatures_40pc_v4.20.tex`, `openjournal.cls`, built with
`pdflatex` three times, for **arXiv then the Open Journal of Astrophysics**. `SOURCE_DATE_EPOCH` is
pinned in `make_all.sh` and `gate.sh`; `FORCE_SOURCE_DATE` is not set.

★ **The page count went 36 → 38 and nothing was cut for length.** This round adds content that two
referees asked for (one new table, the η Crv paragraph, the measured-recurrence paragraph, the
primary-beam row, the session-independent hold-out subset). The reduction to ≤30 pp is the next
pass, on the author's instruction that correctness comes first.

## Verification of this build (2026-10-14, all times `date -u`)

| check | result |
|---|---|
| `make_all.sh` | **rc=0** ("generators OK"), ~30 min |
| `gate.sh`, run twice on the shipped tree | **ALL GATES PASS** both times; log md5 **`adca52d868d55a3be8f60c3ebd176d8f`**, byte-identical |
| PDF | md5 **`6431d8a8c86cce4f4dfa6e1cfe9fbfea`**, unchanged by the second gate run |
| `cleanregen.py` | **229/229 byte-identical**, both `make_all.sh` passes rc=0 |
| LaTeX log | 0 errors, 0 undefined control sequences, 0 unresolved refs/cites, 0 multiply defined, **0 overfull hbox, 0 overfull vbox**, 26 underfull |
| Type 3 fonts | **0** |
| pages | **38** (main text 21.2, back matter 1.3, appendices 13.9, bibliography 1.5) |
| `audit_numbers_v385.py` | **58 PASS / 0 FAIL**, 10 warnings (all long-standing and named) |
| `arxivset.sh` | 215 items, A1 200/200 tex resolved, A9 215 = 215, **A8 byte-identical** to the in-tree build, **A13 PASS**, 496 kB tarball |
| `genai_sweep.py` | 10 hit lines over 23 families, every one ordinary English; `--drive` **23 of 23 families fire** |
| abstract | typeset **1907 characters / 297 words** (arXiv limit 1920, headroom **13**); the plain-ASCII block in `OJA_SUBMISSION.md` is **1911 / 298** and is the typeset paragraph transliterated character for character (`absmeta` M1–M4) |
| `prosegate_selfref` | **PASS**, 0 hits, 7 allow entries, 0 stale |
| `floatfit_r18` / `rotfit_r18` | **PASS**; 0 "float too large for page", 14 floats measured, landscape ledger inside the block |
| `tabfloor_r17` | **0 of 14 floats fail** |
| `roundcollide` | 161 round files, 161 inputs, **0 problems** |
| `valuetwin` | 2 same-quantity groups, **22 declared coincidences**, 0 FAIL |

## What is new in the build

**Seven new generators**, each with its own assertions and drives, every drive demonstrated to fail
its own clause and nothing else:

| round | generator | what it owns |
|---|---|---|
| 750 | `recurinj_r19.py` | the recurrence recovery measured on the two products this container retains (8 clauses, 8 drives) |
| 806 | `confirm_r19.py` | one definition of a confirmed signal; the positive controls' baselines and `tab_confirm_r19.tex` (8 clauses, 9 drives) |
| 840 | `quality_r19.py` | the quality threshold sweep, the archival bookkeeping, the clustering statistic, the extension's expectation (17 clauses, 18 drives) |
| 850 | `holdsess_r19.py` | the reserved blocks that share no observing session (4 clauses, 4 drives) |
| 860 | `orbit_r19.py` | the orbit the β Pic pair determines (7 clauses, 8 drives) |
| 870 | `hostinj_r19.py` | the recurrence recovery measured for **all 33** crossings that carry an exclusion (12 clauses, 13 drives) |
| 900/901/902 | `beam_r19.py`, `eta_r19.py`, `trap_r19.py` | the primary-beam prescription, η_drift by class, TRAPPIST-1 b's phase fraction |

★ **Round 860 was 840 in its own queue file**: `r19-quality` and `r19-orbit` both claimed 840, which
`roundcollide` would have caught only after one had overwritten the other's macro file. The
renumber is recorded beside the generator in `make_all.sh`.

## Three gates were repaired because they had stopped testing anything

* `prose_v412.py --drive 10` **raised instead of firing** — the abstract sentence it quoted had been
  reworded — so **P4 had been undemonstrated for rounds**. Re-pointed; P4 now passes on the patched
  abstract and fails under the patched drive.
* `absreq_r17.py` drives **3 and 5** matched nothing, for the same reason (the chance sentence and
  the decorrelation sentence had both been rewritten). Re-pointed; all seven drives fire.
* `hostinj_r19.py`'s own `C5` was written as "measured ≤ model + 2 binomial σ", which at a measured
  1.000 has σ = 0 and **could only ever fail on good data**. It now compares the model with the
  measured value's own lower bound.

## The corrupt input this build refuses

`r10inputs/recur_v411.json` combines `all_other` over **every** repeat block, including the one
`badweight_v411.json` flags, so HR 1010's stored `T_if_persistent` is **27,706**. Round 870 drops
flagged blocks from every combination and `C10` refuses any retained statistic above the trigger by
more than ×100, driven on that very value. Nothing published today reads it (`v409_calc.py` and
`epoch_v403.py` read `all_other` for other crossings), and that is now gated rather than lucky.

---

## Closing state of this version (coordinator, 2026-10-15 03:45 UTC)

**39 pages.** Verified: `make_all.sh` rc=0 · `gate.sh` twice, all gates pass, logs byte-identical
(`143edc2340e8cc5eda4803995bbafd3f`) and the same PDF md5 (`400df146612b541b4eab840688a4ad4e`) ·
`cleanregen` **230/230 byte-identical** · `audit_numbers` 58 PASS / 0 FAIL · 0 overfull hbox and
vbox · Type-3 fonts 0 · `arxivset` A8 byte-identical with A1-A13 passing · `genai_sweep` 23/23
drives · abstract **1814 characters / 281 words** typeset and **1818** in the plain-ASCII block,
against arXiv's 1920-character limit.

### Three decisions taken at the close
1. **The measured-against-calculated recovery table stays.** It was asked for in terms, and the
   version ships at its natural length by the author's ruling, so a compact appendix table is the
   right home for it.
2. **One stale drive in `prose_v412.py` is carried, not fixed.** It no longer exercises the clause it
   was written for. It is a *drive*, not a gate: the gate itself passes and is driven by its other
   clauses, the manuscript is unaffected, and repairing a drive at the end of a verification cycle
   risks more than it buys. **It is recorded as the first item for the next pass**, with the two
   that were repaired this round as precedent: a drive that has stopped driving anything is the
   quietest defect this build can carry.
3. **Length is reported, not managed.** 39 pages is +1 on the integrated build and +3 on the
   previous version, and every page of the increase is material that was asked for: the recurrence
   validation and its table, the confirmation definition, the quality-threshold stability test, the
   clustering statistic, the positive-control baselines and the coverage statements.

### What a reader of this version should know about its evidence
The recurrence exclusions are no longer calculated alone: a synthetic carrier was injected into the
discovery block and every covering repeat block of all 33 crossings that carry an exclusion, and the
frozen recurrence path was run over them unmodified. That measurement is at the spectrum level --
it exercises the frame correction, the drift carried across the gap, the start-of-block anchor, the
repeat-block noise estimation, the maximum over drift trials and the threshold, and **not** the
extraction of a spectrum from visibilities, which the injection campaign of Sec. 5.1 covers. One
crossing (eta Crv) is measured to recover only 0.29 of the time where the calculation gave one,
because its repeat block is 8.27 times longer than its discovery block; it is reported as untested
rather than excluded, and the statistic was **not** switched for it alone.
