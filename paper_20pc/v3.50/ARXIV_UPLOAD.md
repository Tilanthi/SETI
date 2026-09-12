# arXiv upload set — v3.50

Verified by `arxivset.sh`: copied into an **empty** directory and built there,
0 errors, 0 undefined references, 0 multiply-defined labels, 0 overfull,
0 underfull, 0 Type 3 fonts, 0 missing files, **29 pages**.

**33 items** (25 tex/cls/sty + 8 figures).

## Source, class and macro inputs
- `technosignatures_20pc_v3.50.tex`
- `openjournal.cls`
- `epsf.sty`
- `survey_numbers.tex`
- `survey_numbers_localnull.tex`
- `survey_numbers_pointing.tex`
- `survey_numbers_recurrence.tex`
- `survey_numbers_round10.tex`
- `survey_numbers_round11.tex`
- `survey_numbers_round12.tex`
- `survey_numbers_round13.tex`
- `survey_numbers_round14.tex`
- `survey_numbers_round15.tex`
- `survey_numbers_round16.tex`
- `survey_numbers_round17.tex`
- `survey_numbers_round18.tex`
- `survey_numbers_round5.tex`
- `survey_numbers_round6.tex`
- `survey_numbers_round7.tex`
- `survey_numbers_round8.tex`
- `survey_numbers_round9.tex`
- `tab_compcurve.tex`
- `tab_occurrence.tex`
- `tab_perband.tex`
- `tab_selection.tex`

## Figures
- `figures/completeness.pdf`
- `figures/control_diagnostics.pdf`
- `figures/coverage_waterfall.pdf`
- `figures/cp72_control_distribution.pdf`
- `figures/drift_acceleration.pdf`
- `figures/eirp_context.pdf`
- `figures/selection_funnel.pdf`
- `figures/sensitivity_2d.pdf`

## Not uploaded (present in the folder, not needed to build)
Generators (`*.py`, `make_all.sh`), gates (`gate.sh`, `pagesplit.py`,
`abstract_limit.py`, `macrosweep.py`, `prosecount.py`, `widows.py`,
`floatsize.sh`, `arxivset.sh`), the released catalogue
`per_target_results_v3.50.csv`, the frozen products (`*.json`, including the
new `heldout_v350.json`), the `frozen_macros/` restore set, the
`apply_v350_stage*.py` edit scripts, notes and referee responses.

Rebuild and re-verify with `bash arxivset.sh [dir]`. `make_all.sh` pins
`SOURCE_DATE_EPOCH`, so the figure PDFs are byte-reproducible and the whole
set regenerates identically from an empty directory.
