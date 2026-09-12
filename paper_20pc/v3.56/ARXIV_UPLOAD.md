# arXiv upload set — v3.51

Verified by `arxivset.sh`: copied into an **empty** directory and built there,
0 errors, 0 undefined references, 0 multiply-defined labels, 0 overfull,
0 underfull, 0 Type 3 fonts, 0 missing files, **29 pages**.

**34 items** (26 tex/cls/sty + 8 figures). The `.tex` carries no author
`%` comments; the four outstanding author questions are in `AUTHOR_ACTIONS.md`.

## Source, class and macro inputs
- `technosignatures_20pc_v3.51.tex`
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
- `survey_numbers_round19.tex`
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

## Notes

- The bibliography is inline (`thebibliography`); no `.bbl` or `.bib` is needed.
- `survey_numbers_round19.tex` is new in this version (`v351_calc.py`).
- Figures are byte-reproducible: `make_all.sh` exports
  `SOURCE_DATE_EPOCH=1577836800`, without which matplotlib stamps a
  CreationDate into every PDF. Verified: 13 of 13 figures regenerate
  byte-identical from an emptied folder.
- The abstract is 1888 source-expanded / 1893 rendered characters against
  arXiv's 1920-character metadata limit, so it can be pasted verbatim.
