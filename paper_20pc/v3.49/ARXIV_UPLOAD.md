# arXiv upload set — v3.49

Verified by `arxivset.sh`: copied into an **empty** directory and built there,
0 errors, 0 undefined references, 0 multiply-defined labels, 0 overfull,
0 underfull, 0 Type 3 fonts, 0 missing files, **29 pages**.

**31 items** (24 tex/cls/sty + 7 figures).

## Source, class and macro inputs
- `technosignatures_20pc_v3.49.tex`
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
- `figures/sensitivity_2d.pdf`

## Not uploaded (present in the folder, not needed to build)
Generators (`*.py`, `make_all.sh`), gates (`gate.sh`, `pagesplit.py`,
`abstract_limit.py`, `macrosweep.py`, `prosecount.py`, `widows.py`,
`floatsize.sh`, `arxivset.sh`), the released catalogue
`per_target_results_v3.49.csv`, the frozen products (`*.json`), the
`frozen_macros/` restore set, notes and referee responses.

Rebuild and re-verify with `bash arxivset.sh [dir]`.

## The abstract for the submission form (v3.49)

arXiv's limit is **hard**: "abstracts longer than 1920 characters will not be
accepted; abridge your abstract if necessary" (info.arxiv.org/help/prep.html).
Until v3.49 the folder's gate did not count the values of the generated macros
and reported 1907 while the typeset abstract was **1975** — v3.48 would have
been refused at the form. Both counters now run in `gate.sh`.

Paste one of these, not the PDF text:

- **`arxiv_abstract_v349.txt` — 1,911 characters.** Verbatim the PDF abstract,
  ASCII-normalised (β → "beta", × → "x", superscripts as `10^13`). 9 characters
  of headroom. Keeping unicode β and × instead gives 1,903.
- **`arxiv_abstract_v349_abridged.txt` — 1,870 characters.** The same text with
  three sentences compressed for the metadata only, which arXiv explicitly
  permits. Use this if the form's counter objects; it counts whitespace in ways
  `wc` does not.

## Author comments

The arXiv tarball carries **no TODO and no author-addressed comment** (verified
in the built set). The seven blocks that shipped inside v3.48 are recorded
verbatim in `AUTHOR_ACTIONS.md`, and the questions they raise are still open —
see `REFEREE_RESPONSE_V349.md` §5.
