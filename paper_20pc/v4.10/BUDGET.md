# BUDGET -- live state, PDF cut (round 9, Phase 2)

Measured in COLUMN POINTS from `technosignatures_40pc_v4.09.pdf` by `measure_integ.py`.
One column is 693.8 pt; one page is 1387.6 pt; a full-width float is charged at twice its height.
Whole-page counting cannot detect a change in this document and must not be used.

| | col-pt | pp | cap (pp) | unspent (pp) |
|---|--:|--:|--:|--:|
| main text | 21519.9 | 15.51 | 22 | 6.49 |
| appendices | 9805.9 | 7.07 | 10 | 2.93 |
| sections total | 31325.7 | 22.58 | | |
| PDF | | 23 | | |

Per file:

| file | col-pt | pp |
|---|--:|--:|
| `sections/01_intro.tex` | 1389.6 | 1.00 |
| `sections/02_background.tex` | 1640.1 | 1.18 |
| `sections/03_sample.tex` | 2034.3 | 1.47 |
| `sections/04_method.tex` | 3977.4 | 2.87 |
| `sections/05_results.tex` | 5088.4 | 3.67 |
| `sections/05b_stack.tex` | 2761.5 | 1.99 |
| `sections/06_discussion.tex` | 3041.5 | 2.19 |
| `sections/07_conclusions.tex` | 1574.8 | 1.13 |
| `sections/app_A_reproducibility.tex` | 3114.8 | 2.24 |
| `sections/app_C_spatialnorm.tex` | 1920.3 | 1.38 |
| `sections/app_I_linemask.tex` | 988.9 | 0.71 |
| `sections/app_J_falsealarm.tex` | 2144.5 | 1.55 |
| `sections/app_N_rfi.tex` | 1637.3 | 1.18 |
| `technosignatures_40pc_v4.09.tex` | 12.3 | 0.01 |

`abstract.tex` and `08_backmatter.tex` carry only `\section*` headings, which step no counter
and are not separately located in the PDF: the abstract falls in the residual and the back matter is
charged to the conclusions.

PDF cut 2026-10-04: 23 pages, 1 080 737 bytes, md5 `9917866ea9da118e82d603536e13d018`, reproduced
byte-identically by a second `gate.sh` run with `SOURCE_DATE_EPOCH` pinned.  Copy at
`../v4.10_pdf/technosignatures_40pc_v4.10.pdf`.  NOT pushed.

Baseline (`.v410_base/`, v4.09 as pushed plus the section split): main 31 673.5 col-pt / 22.83 pp,
appendices 50 515.1 / 36.40 pp, 60 pages. The history purge alone accounts for 5 395.1 col-pt
(3.89 pp), measured by building the baseline without its sentences.

---

<details><summary>Pre-integration baseline measurement, kept for reference</summary>

# BUDGET — where the 60 pages are, measured

Re-measure with `python3 secbudget.py && python3 floatinv.py && python3 budget.py` after every pass. Every number here is measured from the built PDF; none is estimated.

**Target: main text ≤ 22 pp, appendices ≤ 10 pp.** Glenn's cap is 25 + 15; the referees ask for about 30 pp total.

> **Measured against the frozen baseline**, not against the live tree: `/workspace/SETI/paper_20pc/.v410_base/` is v4.09 as pushed (`d19a4e3fad5b`) with the section split applied and nothing else, and its PDF is byte-identical to the deposited v4.09 PDF (`c9d0f55b…`). Re-run the tools in *this* directory to measure the live state; re-run them in `.v410_base/` to reproduce these numbers.

## Method, and what the numbers mean

- A page is two columns of 694 pt. A section's **extent** is measured along the typeset flow from its heading to the next heading, page by page and column by column, so a section is not charged for the section before it merely because it starts at the top of a page. Counting whole pages is what turns a 22.07-page main text into "23 pages".
- **Float area** is each float's own typeset height, measured by `\@largefloatcheck`, over 694 pt (full-width) or 1388 pt (single-column). It is additive and it is the number to use when deciding what to cut; a float's *individual* page delta is almost always zero because the page repacks.
- The extent of a section already contains any single-column float placed inside it, so the two columns below are **not** additive. The float column says how much of the extent is float.
- The unnumbered back matter (author contributions, funding, data availability, software) is charged to §7, and the appendix overview to the `APPENDIX` row: `\section*` headings are not numbered and are not separately located in the PDF.

## Main text

| file | owner | extent (pp) | of which floats (pp) |
|---|---|---|---|
| `sections/01_intro.tex` | abstract-intro | 1.03 | 0.00 |
| `sections/02_background.tex` | abstract-intro | 0.86 | 0.18 |
| `sections/03_sample.tex` | sample-method | 0.71 | 0.51 |
| `sections/04_method.tex` | sample-method | 4.71 | 0.67 |
| `sections/05_results.tex` | results | 7.34 | 1.97 |
| `sections/05b_stack.tex` | stack-discussion | 1.61 | 0.00 |
| `sections/05c_limits.tex` | stack-discussion | 2.37 | 0.18 |
| `sections/06_discussion.tex` | stack-discussion | 2.04 | 0.12 |
| `sections/07_conclusions.tex` | stack-discussion | 1.66 | 0.00 |
| **main total** | | **22.34** | **3.63** |

Main text must lose **0.34 pp** to reach 22.

## Appendices

| file | extent (pp) | of which floats (pp) | R2 asks |
|---|---|---|---|
| `sections/app_A_reproducibility.tex` | 5.00 | 0.42 | delete most of it |
| `sections/app_B_figofmerit.tex` | 0.67 | 0.00 | delete most of it |
| `sections/app_C_spatialnorm.tex` | 0.95 | 0.00 |  |
| `sections/app_D_externalchecks.tex` | 3.52 | 0.93 |  |
| `sections/app_E_notation.tex` | 0.01 | 1.08 |  |
| `sections/app_F_freqconventions.tex` | 2.98 | 0.50 |  |
| `sections/app_G_injection.tex` | 3.24 | 0.71 |  |
| `sections/app_H_pertarget.tex` | 0.48 | 0.29 |  |
| `sections/app_I_linemask.tex` | 1.14 | 0.00 |  |
| `sections/app_J_falsealarm.tex` | 3.80 | 0.73 |  |
| `sections/app_K_provenance.tex` | 8.12 | 2.57 |  |
| `sections/app_L_recommendations.tex` | 1.37 | 0.00 |  |
| `sections/app_M_repaired.tex` | 2.98 | 0.14 | delete |
| `sections/app_N_rfi.tex` | 2.15 | 0.11 |  |
| **appendix total** | **36.40** | **7.47** | |

Appendices must lose **26.40 pp** to reach 10. The bibliography (~2 pp) and the `APPENDIX` divider are outside both totals; sections sum to 59.23 of the PDF's 60 pages, the 0.77 pp residual being the title block, the abstract above the first heading, and the reference list.

## What the mechanical cuts actually deliver (measured, cumulative)

| stage | pages | main | appendices+refs | cumulative |
|---|---|---|---|---|
| 0 v4.09 as shipped | 60 | 23 | 37 | +0 |
| 1 + the 19 floats on R2 cut list | 55 | 22 | 33 | -5 |
| 2 + Appendix M deleted | 53 | 22 | 31 | -7 |
| 3 + Appendices A and B deleted | 47 | 22 | 25 | -13 |
| 4 + the revision history purged | 44 | 20 | 24 | -16 |

Every stage builds with 0 LaTeX errors. After all four, the main text is **20 pp** (target 22, **met**) and the appendices plus references are **24 pp** against a target of 10 — so the appendix triage has to go roughly **12 pp further** than deleting M, A and B: the remaining weight is App. K (8.12 pp), App. J (3.80 pp), App. G (3.24 pp) and App. F (2.98 pp).

## The revision history

- 112 sentences, 31696 characters = **8.0 per cent of the body**
- measured by building without them: **4 pages** (main 2, appendices 2)
- R1 estimated 5–7 pages. 4 pp is a **floor**: the inventory only catches sentences a pattern can see, and 1073 characters were left in place because the sentence also carried structure (a `\begin`, a `\label`, a `\caption`). Whole paragraphs that exist only to narrate the history are counted sentence by sentence, not as paragraphs.


</details>
