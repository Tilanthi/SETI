# Who owns which file

## ★★★★ CURRENT — v4.17, round 16 (2026-10-09). READ THIS BLOCK, NOT THE v4.10 TABLE BELOW.

The v4.10 table further down is kept for the history of the split and **is now wrong in three
ways**: it lists eleven appendix files that no longer exist, it gives one owner per file where
round 16 split two files between two agents, and it does not mention the bibliography at all.
Those three gaps each cost an agent time this round, so they are closed here.

### ★★★ The appendix LETTER is not the appendix FILENAME

`PLAN.md` and every brief name appendices by their **printed letter**. The filenames are historical
and do not track it. A glob on `sections/app_C*` hits **Appendix B**, and one agent this round was
sent at the wrong file by exactly that.

| printed | file | contents |
|---|---|---|
| **A** | `sections/app_A_reproducibility.tex` | spectral response, frequency conventions, primary beam |
| **B** | `sections/app_C_spatialnorm.tex` | the spatial rank, the hold-out, the calibration mechanisms |
| **C** | `sections/app_I_linemask.tex` | the velocity-space line mask |
| **D** | `sections/app_J_falsealarm.tex` | the false-alarm expectation and the crossing ledger |
| **E** | `sections/app_N_rfi.tex` | radio-frequency interference |

There are **five** appendix files and **sixteen** prose sources in `sections/`. Anything the v4.10
table names and `ls` does not is gone.

### Round-16 ownership, as it actually was

| file | owner(s) |
|---|---|
| `sections/abstract.tex`, `01_intro.tex`, `07_conclusions.tex`, §6.3 of `06_discussion.tex` | `r16-prose` |
| `sections/02_background.tex` | **SPLIT**: Table 1's caption and the Mason sentence → `r16-fig`; Figure 1's caption → `r16-resp`. Nothing else was touched. |
| `sections/03_sample.tex`, `04_method.tex`, `05b_stack.tex`, `08_backmatter.tex`, `si_notice.tex` | integrator |
| `sections/05_results.tex` | **SPLIT**: §5.1 → `r16-resp`; §5.3 → `r16-chance`; §5.3.1 → `r16-calib`; §5.5, §5.6 → `r16-recur`; §5.6.1 → `r16-counts` |
| `sections/06_discussion.tex` | **SPLIT**: §6.2 → `r16-fig`; §6.3 → `r16-prose`; §6.1 and §6.4 → integrator |
| `sections/app_A_reproducibility.tex` (printed A) | `r16-resp` |
| `sections/app_C_spatialnorm.tex` (printed B) | `r16-calib` |
| `sections/app_I_linemask.tex` (printed C), `app_N_rfi.tex` (printed E) | `r16-mask` |
| `sections/app_J_falsealarm.tex` (printed D) | `r16-chance` |
| the `\begin{thebibliography}` block of the main `.tex` | **`r16-refs`** — not in `PLAN.md`'s table at all, and nobody else is given it |
| everything else, and every generator, gate and fragment | integrator |

**A split file is a hazard, not a convenience.** Two agents edited `02_background.tex` and five
edited `05_results.tex` on the same morning; `r16-refs` found the main `.tex` changed under it
mid-edit. The rule that made that survivable: **edit on exact strings, never on line numbers, and
re-read immediately before writing.**

---

# v4.10 — who owned which file (historical; see the block above)

**The rule: nobody edits a file they do not own.** Not one line. If you need a change in
someone else's file, write the request at the bottom of your own file as a `%% REQUEST:` comment
and the integrator will route it. Two agents editing one file is the merge disaster this split
exists to prevent.

A second rule, equally hard: **prose agents do not touch numbers.** Every number in the paper is
a macro (`\NWinA`, `\LgNCross`, …) emitted by a generator. You may move a macro, delete a
sentence containing one, or ask the numbers agent for a new one. You may **never** type a digit
where a macro should be, and you may **never** edit a `survey_numbers_round*.tex` file or any
`*_calc.py` / generator. `prosenum`, `intsweep` and `macrosyn` will catch it, and `retire_macros`
will silently delete a macro you stop referencing.

## Section files — one owner each

| file | contents (v4.09 state) | owner |
|---|---|---|
| `sections/abstract.tex` | abstract + `\keywords` | abstract-intro |
| `sections/01_intro.tex` | §1 Introduction | abstract-intro |
| `sections/02_background.tex` | §2 Background | abstract-intro |
| `sections/03_sample.tex` | §3 Sample selection | sample-method |
| `sections/04_method.tex` | §4 Data and methodology | sample-method |
| `sections/05_results.tex` | §5 Results through the crossing ledger (incl. β Pic, recurrence) | results |
| `sections/05b_stack.tex` | §5.4 the stellar-frame multi-epoch stacked search | stack-discussion |
| `sections/05c_limits.tex` | §5.5 what this experiment excludes, and what it does not | stack-discussion |
| `sections/06_discussion.tex` | §6 Discussion | stack-discussion |
| `sections/07_conclusions.tex` | §7 Conclusions | stack-discussion |
| `sections/08_backmatter.tex` | author contributions, funding, competing interests, acknowledgements, data availability, software | integrator |
| `sections/app_00_overview.tex` | unnumbered "What this paper did, and where the details are" | appendix-triage |
| `sections/app_A_reproducibility.tex` | App. A Reproducibility and provenance | appendix-triage |
| `sections/app_B_figofmerit.tex` | App. B The conventional figure of merit | appendix-triage |
| `sections/app_C_spatialnorm.tex` | App. C The spatial normalisation | appendix-triage |
| `sections/app_D_externalchecks.tex` | App. D External checks and the positive control | appendix-triage |
| `sections/app_E_notation.tex` | App. E Notation | appendix-triage |
| `sections/app_F_freqconventions.tex` | App. F Frequency conventions, linewidth, smearing | appendix-triage |
| `sections/app_G_injection.tex` | App. G Injection–recovery sensitivity validation | appendix-triage |
| `sections/app_H_pertarget.tex` | App. H Per-target results | appendix-triage |
| `sections/app_I_linemask.tex` | App. I The velocity-space line mask | appendix-triage |
| `sections/app_J_falsealarm.tex` | App. J False-alarm accounting | appendix-triage |
| `sections/app_K_provenance.tex` | App. K Analysis provenance and robustness checks | appendix-triage |
| `sections/app_L_recommendations.tex` | App. L Recommendations for a next-generation search | appendix-triage |
| `sections/app_M_repaired.tex` | App. M The repaired extraction, the archival tail, three re-derived results | appendix-triage |
| `sections/app_N_rfi.tex` | App. N Radio-frequency interference | appendix-triage |

`sections/05b_stack.tex` and `05c_limits.tex` are subsections of §5 carved out so the
stack-discussion agent owns its own material without reaching into the results file. They must
stay in this order; `\input` order is the document order.

## Files owned by the numbers agent — nobody else writes these

- every `survey_numbers*.tex`, `regen_count.tex`, `peff_range_v372.tex`, `ledger_legend_v403.tex`
- every generator and gate `.py`, and `make_all.sh`
- every `tab_*.tex` and `tables/*.tex` (generated table fragments)
- `figures/*.pdf` and the `make_fig*.py` that build them (figures agent coordinates through the
  numbers agent for anything that reads a macro)

**The macro layer is frozen for Phase 1.** No regeneration, no renaming, no new rounds until the
prose passes are in. The generators in `v4.10/` are byte-identical to the pushed v4.09 except for
the five path-visibility fixes listed below, and every product they emit has been verified
byte-identical to v4.09's.

## Files owned by the integrator

- `technosignatures_40pc_v4.10.tex` — now a preamble plus `\input` lines. Deleting a section means
  deleting its `\input` line **and** its file, in the same change.
- `manuscript.py`, `split_sections.py`, `gate.sh`, `floatsize.sh`, `CUTLIST.json`, `PURGE.md`,
  `BUDGET.md`, this file.

## The split, and what it forced

The manuscript is one file per section; the main `.tex` keeps the preamble, the title block, the
`\appendix` switch and the bibliography. Every `\input` is written `\input{sections/NAME}%` — the
trailing `%` suppresses the end-of-line space, so TeX concatenates the section files exactly as
they were adjacent lines. **The PDF is byte-identical to the pushed v4.09 PDF**, which is the only
acceptable proof that the split changed nothing.

Six tools read the manuscript's prose and would have gone **vacuous or false** against a 263-line
main file. They now read `manuscript.flat()`, which expands the `\input`s in place and is asserted
byte-exact against the monolithic original:

| file | why it had to change |
|---|---|
| `intsweep.py`, `prosenum_v399.py`, `macroleak.py`, `xrefcheck.py`, `consistency_v399.py`, `macrosweep.py`, `literalsweep.py`, `abstract_limit.py`, `measure.py`, `audit_numbers_v385.py` | prose gates: scanning the main file alone reported "0 problems" on 263 lines of preamble — a check that cannot fail |
| `retire_macros.py` | its consumer glob was `*.tex`, which does not include `sections/`. Unpatched, it would have judged every prose-only macro unreferenced and **deleted** it |
| `p90_budget_v409.py` (B10), `v409_calc.py` (V7c) | both assert the *manuscript references* a macro, precisely so `retire_macros` cannot strip it. Unpatched, B10 fails the build and V7c goes vacuous |
| `v352_calc.py` | asserts the manuscript names the released catalogue by filename |
| `roundcollide.py` | reads the `\input{survey_numbers_roundNN}` list (still in the main file, so unaffected — repointed anyway) |
| `selftest_v409.py` | its mutation harness runs a perturbed generator from a scratch directory; `import manuscript` needed the build directory on `sys.path`, or six drives report "did not fire" when in fact they could not start |

`manuscript.py --selftest` drives its own two assertions (a stray section file, a deleted section
file) and both fire.

**Stale tools that still assume a monolithic manuscript** and must not be run without being fixed
first: `inventory_v352.py`, `prosecount.py`, `subrun5_check.py`, `restructure_discussion.py`,
`strip_author_todos.py`, and the `apply_v3*.py` one-shot edit scripts. None is in `make_all.sh`
or `gate.sh`.

## ►► RULING 2026-10-04 08:2x — `05c_limits.tex` RETIRED (parent)

`05c_limits.tex` is **frozen and will be deleted at integration**. Its content folds into **§6.2 of
`06_discussion.tex`** (owner: `r9-stack-discussion`), absorbed from
`/workspace/SETI/referee_r9/handoff_05c_from_results.tex`, which holds `r9-results`' rewrite verbatim.
`r9-results` owns **`05_results.tex` only**, and keeps the sensitivity material it moved there.
**Nobody edits `05c_limits.tex` again.** Full reasoning: `/workspace/SETI/referee_r9/RULING_05c.md`.

## Phase-0 measurements and the tools that make them

| file | what it is |
|---|---|
| [`BUDGET.md`](BUDGET.md) | per-file page cost, measured, with the 22 + 10 target and the cumulative effect of the mechanical cuts |
| [`CUTLIST.json`](CUTLIST.json) | every float the referees ask to delete, with its measured typeset area AND the page delta of a real build without it |
| [`PURGE.md`](PURGE.md) | every trace of the revision history, file and line, grouped DELETE / REPHRASE / CHECK / LITERATURE / COMMENT |
| `secbudget.py` | per-section extent along the typeset flow, from the PDF |
| `floatinv.py` | every float's height from `\@largefloatcheck`, paired correctly and converted per column count |
| `cutmeasure.py` | one real build per proposed cut, plus the whole list together |
| `purge_inventory.py`, `purge_measure.py` | the history inventory and its page cost |
| `programme_measure.py` | the four cut stages, cumulative, measured |
| `budget.py` | writes `BUDGET.md` and `CUTLIST.json` from the above |

`/workspace/SETI/paper_20pc/.v410_base/` is the frozen baseline: v4.09 as pushed, split, nothing
else. **Do not edit it** — it is the reference the byte-identity proof rests on and the state every
measurement is relative to.

## Two hazards

1. ★ **Do not run `make_all.sh` while prose is in flux.** Its last step, `retire_macros.py`,
   deletes every macro the manuscript no longer references — and during a rewrite a macro is
   unreferenced for as long as the sentence quoting it is being rewritten. Run the generators only
   when the prose is settled, and read `retire_macros.py`'s report before accepting the result.
2. `figures_referee_numbers.json` records the **absolute path** of the figure it checked, so it is
   the one product that is not reproducible across directories. Harmless, but it will show up in
   any byte-comparison between build directories.
