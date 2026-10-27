# `deai_invariant_check.md` — I-1…I-7 and the T-01 register, batch by batch (v4.25, Stage 4)

`deai-revise`, 2026-10-19. One row per batch. **HARD** means the stage aborts on a change:
numeric multiset of the **macro-resolved** text, and the citation-key multiset. **soft** means
reported and adjudicated: labels, `\ref` targets, and AD-10's (value, referent-skeleton) tuple
register, which *must* change when a sentence carrying a number is reworded — what may not change
is the **multiset of values** attached to the re-skeletoned sentences, and that equality is
asserted automatically by `deai/revise/measure.py`.

**Why the tuple register and not the multiset.** AD-10: a number re-attached to a *different*
referent leaves the plain multiset unchanged. The register holds 1,727 (value, sentence-skeleton)
pairs for this paper.

**Invariants in force** (protocol §I, with §B's amendment to I-1):
- **I-1** quantities, units and their referents — protected. §B: the *quantity*, not the printed
  string; but **this project's rule is stricter and binds**: numbers are generated, never typed, so
  no precision change may be made by hand in a section file at all.
- **I-2** citations and their claims · **I-3** the argument's logical structure · **I-4** hedges and
  limits · **I-5** the author's voice where it is his own · **I-6** figure/table content ·
  **I-7** no edit may make the text worse to move a metric.
- Author constraints that outrank every battery row: main text ≤ 25 pp; no mention anywhere of
  versions, edits, referees, rounds or corrections (prose, captions, tables, figures, printed
  comments **and the arXiv source package**); figure widths unchanged; reference-list leading at the
  class default; **§5.3.2's negation ("Neither criterion was fixed in advance … so it is post hoc")
  is not to be deleted**; the Sirius passage is not to be touched.

| batch | HARD numbers | HARD cites | labels | refs | tuples (lost/gained, values equal) | compile | words |
|---|---|---|---|---|---|---|---|
| baseline | — | — | — | — | 1,727 pairs | 0 err, 41 pp, 0 overfull | 33,975 |
| 1 `flux density` | unchanged | unchanged | unchanged | unchanged | 25/25, **equal** | 0 err, 41 pp, 0 overfull | 33,989 |
| 2 Abstract + gate B7 | unchanged | unchanged | unchanged | unchanged | 26/26, **equal** | 0 err, 41 pp, 0 overfull | 33,989 |
| 3 pseudo-clefts (21) | unchanged | unchanged | unchanged | unchanged | 44/44, **equal** | 0 err, 41 pp, 0 overfull | 33,963 |
| 4 pseudo-clefts (9) | unchanged | unchanged | unchanged | unchanged | 49/49, **equal** | 0 err, 41 pp, 0 overfull | 33,946 |
| 5 `rather than` (62) | unchanged | unchanged | unchanged | unchanged | 158/158, **equal** | 0 err, 41 pp, 0 overfull | 33,930 |
| 6 paragraph openers (6) | unchanged | unchanged | unchanged | unchanged | 154/154, **equal** | 0 err, 41 pp, 0 overfull | 33,928 |
| 7 emphasis (6) | unchanged | unchanged | unchanged | unchanged | 160/160, **equal** | 0 err, 41 pp, 0 overfull | 33,929 |
| 8 lower-case clefts + B-17 + B-04 (15) | unchanged | unchanged | unchanged | unchanged | 182/182, **equal** | 0 err, 41 pp, 0 overfull | 33,913 |
| 9 em-dashes (8) | unchanged | unchanged | unchanged | unchanged | 188/188, **equal** | 0 err, 41 pp, 0 overfull | 33,912 |
| 10 redundant pointers (2) | unchanged | unchanged | unchanged | **2 lost, 0 gained** (intended) | 193/193, **equal** | 0 err, 41 pp, 0 overfull | 33,907 |
| 11 EP-02 modal restored (1) | unchanged | unchanged | unchanged | unchanged | 193/193, **equal** | 0 err, 41 pp, 0 overfull | 33,914 |

## Standing checks re-verified at the baseline
- §5.3.2's negation present: verified by grep before the first edit and re-checked at the end of
  every batch that touches `05_results.tex`.
- The Sirius passage: untouched by every patch anchor in this stage (no anchor lies inside it).
- No patch writes outside `/workspace/SETI/paper_20pc/v4.25` (asserted by `apply_patch.py`).

## The independent re-measurement at the end of the pass

The battery was re-run with **the original tree as its second argument**, so every protected-token
row carries a measured before and after. The original tree is a hard-linked copy of v4.25 whose 18
section files and main `.tex` are the pre-edit originals; it reproduces the baseline **byte-exactly**
(`flat.tex` md5 `d6b9daed5453`), which is what makes it a legitimate control.

| row | measures | before | after | verdict |
|---|---|---|---|---|
| `T-01a` | numeric multiset, macro layer resolved, math included | 2,220 | 2,220 | **PASS, empty delta** |
| `T-01b` | citation-key multiset | 101 | 101 | **PASS** |
| `T-01c` | object / catalogue identifiers | 42 | 42 | **PASS** |
| `T-01d` | cross-reference keys (`\ref`) | 301 | 299 | **FAIL by design** — the two redundant pointers of Batch 10, each named in the change log. No other `\ref` moved |
| `T-01e` | label keys (`\label`) | 71 | 71 | **PASS** |
| `T-01f` | macro-use multiset (this paper's numbers live here) | 1,913 | 1,913 | **PASS** |
| `EP-02` | no sentence climbs the epistemic ladder | 0 | **0** | **PASS after a repair** (below) |
| `B-26` | punctuation delta against the original | — | 38 | PASS |

★★ **`EP-02` caught a real I-4 risk in one of my own edits, and it was right to.** LC1 rewrote
*"so what could be searched and what could be confirmed are different extents"* as *"so the
searchable and the confirmable extents differ"* — which deletes **two modal verbs**, and the ladder
duly moved that sentence `conjectured → asserted`. The modal there is one of **capability**, not of
epistemic hedging, so the climb is arguably a detector artefact; but **I-4 protects hedges and
limits, and the honest response to a Class A row is not an argument**. Re-written as *"so the extent
that could be searched and the extent that could be confirmed differ"*: the free relative is still
gone, the modal is back, and the row reads **0 climbs**. *A row that fires on an edit I believed was
neutral is the row earning its place.*

★ **`T-01a`'s empty delta over 2,220 numbers is the strongest single statement this stage can make**:
193 sentences were re-skeletoned across eleven batches and **not one number changed, not one moved
to a different referent** (AD-10's tuple check, asserted automatically per batch), and not one
citation key changed over 101.

---

# CYCLE 2 RECEIPTS — `deai-close`, 2026-10-20

21 patches in four batches (C2-A Ruling 21, C2-B the contrastive family, C2-C the pseudo-clefts
and SF-3, PX1/PX2 the two preamble primitives). Measured on `mkinputs.py` output: entry
`prose.tex` `47324cfac3d5` → final `64e0123dfba8`; `resolved.tex` `6230f8a9b372` → `4b7faa422b04` at the point the edits were measured, and
`7f013603c0eb` after the clean regeneration rebuilt the macro layer from nothing — **`prose.tex`
is `64e0123dfba8` in both**, so every number in this file and in the audit report was re-confirmed
on the final tree rather than carried forward;
`flat.tex` `5a760bb8d502` → `34397c023e43`. Before-cut reproduced at `b53f2141e83f`, the md5 the
before-table was taken on, by an independent run.

## T-01 — the protected-token register

| register, on `resolved.tex` | entry (cycle-1 final) | after cycle 2 | verdict |
|---|---|---|---|
| numbers (multiset) | 2 717 | **2 717** | **equal, 0 lost, 0 gained** |
| citation keys (multiset) | 84 `\cite` groups | **84** | **equal** |
| `\label` (set) | 71 | **71** | **equal** |
| `\ref` (multiset) | 299 | **299** | **equal** |
| command uses over `flat.tex` (multiset) | 4 094 | **4 094** | **equal, 0 differing names** |
| alphabetic words of `prose.txt` | 33 910 | 33 873 | **−37** |

★ The command-use multiset is the one that protects the build rather than the text: a single
`\newcommand` falling to zero references would be deleted by `retire_macros.py` on the next
`make_all.sh`, silently, and this project has lost a table row that way before. Zero names differ.

## T-01, the per-block form (Stage 5's improvement, applied here)

A context-skeleton register churns on any rewording, so conservation is checked **per changed
block** instead. `difflib` over the sentence streams: **19 changed blocks, 19 sentences out and 19
in**, token multisets (numbers, `CITE`, `REF`, `MATH`) conserved in **17 of 19**.

★ **The two imbalanced blocks are the one declared move, and they are declared here:** `21`
(`\ZcNoRepSys`) leaves the Abstract's sentence 5 in R21a and arrives in the sentence R21b writes.
At Abstract scope the multiset is **equal, 0 lost, 0 gained** — the number did not change referent,
it changed sentence, and both sentences are about the same systems. No other number moved at all.

## T-02 / T-03 — propositions and the ladder

- **T-02.** One proposition deleted and re-asserted (R21a→R21b: the `\ZcNoRepSys` systems lack a
  repeat at a covered frequency). Twelve contrastive second limbs removed, each entailed by its own
  first limb or restated by the adjacent clause — logged as removed redundancy in
  `deai_change_log.md`, item by item. Four pseudo-clefts and one stock-frame opener rewritten with
  no change of content. **No new proposition.**
- **T-03.** **One ladder movement, and it is upward to where the evidence already was**: the
  headline qualifier returns from comparative to categorical (Ruling 21). Under §3.4 that is not a
  *lowering* needing approval but a *restoration* that was ordered; it is recorded in
  `deai_author_decisions.md` §2.1 all the same, because it touches the paper's headline claim.
  No other claim moved. W-04 held: *consistent with* never became *demonstrates*.

## T-04 / T-05 — the build

`gate.sh`: **ALL GATES PASS** (the run that rejected the first attempt at PX1 is kept: a non-raw
Python `\f` wrote a form feed into the preamble, LaTeX reported *Missing \begin{document}*, and
`macroleak`, `tabfloor` and `latexlog` failed together — recorded rather than quietly fixed).
`latexlog`: 0 errors, 0 undefined control sequences, 0 unresolved references or citations, 0
multiply defined, 0 overfull boxes. `audit_numbers_v385.py`: 58 PASS / 0 FAIL / 13 WARN (the 13 are
the carried SIMBAD-form naming). `absreq_r17`: 7 checks, 0 FAILED, **B7 satisfied by the new
wording and checked rather than assumed**. `absmeta`: the pasted ASCII abstract equals the typeset
paragraph character for character, 1 572 of 1 920. `abswords`: 244 of 245.

## The one thing that went wrong in this cycle, and it is mine

★★ **I overwrote the before-cut snapshot through a hard link** — the hazard Stage 5's N-5 had
written down and I had read. `v4.25/deai_audit_report.md` and
`work/rev425/orig_tree/deai_audit_report.md` shared an inode, so writing the new report wrote
through into the snapshot. Detected immediately by `stat` (link count 2), repaired from the
untouched third copy at `work/rundir-v4.25/` (md5 `014d7c4e261f…`, verified equal on all three
paths), the link broken, and the remaining hard-linked deliverables (`deai_change_log.md`,
`deai_battery.md`, `deai_invariant_check.md`) unlinked before they were edited. **The snapshot's
`.tex` files were never touched** and still reproduce the before-cut prose byte-exactly, which is
the only property the snapshot has to have. *A snapshot that must survive a rebuild has to copy its
files, not link them* — and an agent that has read that sentence will still trip over it unless it
checks the link count before writing.
