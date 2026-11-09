# BUDGET — where the 38 pages are, measured

Re-measure with `python3 secbudget.py && python3 floatinv.py && python3 budget.py` after every pass. Every number here is measured from the built PDF; none is estimated.

**Target: main text ≤ 22 pp, appendices ≤ 10 pp.** Glenn's cap is 25 + 15; the referees ask for about 30 pp total.

## Method, and what the numbers mean

- A page is two columns of 694 pt. A section's **extent** is measured along the typeset flow from its heading to the next heading, page by page and column by column, so a section is not charged for the section before it merely because it starts at the top of a page. Counting whole pages is what turns a 22.07-page main text into "23 pages".
- **Float area** is each float's own typeset height, measured by `\@largefloatcheck`, over 694 pt (full-width) or 1388 pt (single-column). It is additive and it is the number to use when deciding what to cut; a float's *individual* page delta is almost always zero because the page repacks.
- The extent of a section already contains any single-column float placed inside it, so the two columns below are **not** additive. The float column says how much of the extent is float.
- The unnumbered back matter (author contributions, funding, data availability, software) is charged to §7, and the appendix overview to the `APPENDIX` row: `\section*` headings are not numbered and are not separately located in the PDF.

## Main text

| file | owner | extent (pp) | of which floats (pp) |
|---|---|---|---|
| `sections/01_intro.tex` | abstract-intro | 0.72 | 0.00 |
| `sections/02_background.tex` | abstract-intro | 1.02 | 0.56 |
| `sections/03_sample.tex` | sample-method | 1.90 | 0.25 |
| `sections/04_method.tex` | sample-method | 4.12 | 1.09 |
| `sections/05_results.tex` | results | 9.51 | 2.21 |
| `sections/05b_stack.tex` | stack-discussion | 1.80 | 0.00 |
| `sections/06_discussion.tex` | stack-discussion | 2.30 | 0.34 |
| `sections/07_conclusions.tex` | stack-discussion | 0.90 | 0.00 |
| `sections/08_backmatter.tex` | - | 1.12 | 0.00 |
| **main total** | | **23.38** | **4.44** |

Main text must lose **1.38 pp** to reach 22.

## Appendices

| file | extent (pp) | of which floats (pp) | R2 asks |
|---|---|---|---|
| `sections/app_A_reproducibility.tex` | 2.22 | 1.17 | delete most of it |
| `sections/app_C_spatialnorm.tex` | 2.90 | 0.32 |  |
| `sections/app_I_linemask.tex` | 2.41 | 0.14 |  |
| `sections/app_J_falsealarm.tex` | 2.76 | 0.97 |  |
| `sections/app_N_rfi.tex` | 2.12 | 0.00 |  |
| `sections/app_P_persys.tex` | 0.08 | 0.59 |  |
| **appendix total** | **12.49** | **3.19** | |

Appendices must lose **2.49 pp** to reach 10. The bibliography (~2 pp) and the `APPENDIX` divider are outside both totals; sections sum to 36.91 of the PDF's 38 pages, the 1.09 pp residual being the title block, the abstract above the first heading, and the reference list.

## What the mechanical cuts actually deliver (measured, cumulative)

| stage | pages | main | appendices+refs | cumulative |
|---|---|---|---|---|
| 0 v4.09 as shipped | 60 | 23 | 37 | +0 |
| 1 + the 19 floats on R2 cut list | 55 | 22 | 33 | -5 |
| 2 + Appendix M deleted | 53 | 22 | 31 | -7 |
| 3 + Appendices A and B deleted | 47 | 22 | 25 | -13 |
| 4 + the revision history purged | 44 | 20 | 24 | -16 |

