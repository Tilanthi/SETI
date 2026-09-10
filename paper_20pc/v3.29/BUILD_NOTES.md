# Building technosignatures_20pc_v3.29

    python3 survey_stats.py      # -> survey_stats.json
    python3 make_numbers.py      # -> survey_numbers.tex  (ALL numbers in the paper)
    pdflatex technosignatures_20pc_v3.29.tex   # x3, converges on the third

## Single source of truth for every number
From v3.29 the manuscript contains no typed digits for survey quantities. It
`\input`s `survey_numbers.tex`, a GENERATED file of `\newcommand` macros
(`\NWindows`, `\NStars`, `\NSystems`, `\NCandidates`, `\OccMeasured`, ...)
produced by `make_numbers.py` from `survey_stats.json`, `occurrence_v328.json`
and `nullcal.json`. A number therefore cannot disagree with itself between
sections, and refreshing the data export updates abstract, body, tables and
captions in one step. This was a referee requirement and it is also what stops
the recurring inconsistency bugs of v3.24-v3.28.

**When new data land: re-run `survey_stats.py`, then `make_numbers.py`, then the
figure and table scripts, then pdflatex. Do not hand-edit counts.**

| artefact | script |
|---|---|
| every survey number | `survey_stats.py` -> `survey_numbers.tex` via `make_numbers.py` |
| occurrence ladder | `survey_stats.py` (bandwidth-integrated completeness) |
| control-ring null calibration | `nullcal.json` (pseudo-star rank test) |
| main figure set | `make_figures_v328.py` |
| Fig. 1 and the completeness surface | `make_figures_referee.py` |
| EIRP vs distance | `make_fig_eirp.py` |
| data tables and released CSV | `make_tables_v328.py` |

## The one real gotcha: cm-super
`apt-get install cm-super`, or pdfTeX silently emits Type 3 bitmap fonts, exits
0, and prints no warning; PDF text extraction then breaks. Verify:

    python3 -c "import pymupdf;d=pymupdf.open('technosignatures_20pc_v3.29.pdf');print({f[2] for p in range(d.page_count) for f in d[p].get_fonts()})"

Must print only `{'Type1','Type0'}`. The check must test `f[2]=='Type3'`, not
just bare `F<number>` font names -- named Type 3 subsets inside included figure
PDFs slipped past that weaker check in v3.24-v3.27.

## v3.29 verified state
| check | result |
|---|---|
| pages | 38 (unchanged since v3.27) |
| undefined references / citations | 0 / 0 |
| multiply-defined labels | 0 |
| LaTeX errors | 0 |
| Type 3 fonts | 0 |
| refs with no label / missing figures / cites with no bibitem | 0 / 0 / 0 |
| literal digits disagreeing with a macro | 0 |
