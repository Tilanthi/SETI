# Building technosignatures_20pc_v3.28

    pdflatex technosignatures_20pc_v3.28.tex   # x3, converges on the third

Self-contained: `openjournal.cls`, `epsf.sty`, `figures/`, `.bbl` all ship here.

## The one real gotcha: cm-super
`apt-get install cm-super`. Without it pdfTeX silently emits **Type 3 bitmap**
fonts, exits 0, and prints no warning; copy-paste and text extraction from the
PDF then break. Verify with:

    python3 -c "import pymupdf;d=pymupdf.open('technosignatures_20pc_v3.28.pdf');print({f[2] for p in range(d.page_count) for f in d[p].get_fonts()})"

Must print only `{'Type1','Type0'}`. NOTE: v3.24-v3.27 shipped with Type 3
fonts embedded inside `figures/pipeline_schematic.pdf` and
`figures/sample_composition.pdf`, which this check missed because it only
looked for bare `F<number>` names. Both were converted to outlines with
`gs -dNoOutputFonts` for v3.28.

## Regenerating everything
| what | script |
|---|---|
| every survey number quoted in the text | `survey_stats.py` -> `survey_stats.json` |
| occurrence limits (bandwidth-integrated completeness) | `survey_stats.py`, `occurrence_v328.json` |
| all figures | `make_figures_v328.py`, plus `make_fig_eirp.py` |
| the three data tables and the released CSV | `make_tables_v328.py` |

All read one frozen export, `/workspace/SETI/figwork/v326_data.json`, so the
text, tables and figures cannot drift apart. Re-run all four after refreshing
the export.

## v3.28 verified state
| check | result |
|---|---|
| pages | 38 (same as v3.27) |
| undefined references / citations | 0 / 0 |
| multiply-defined labels | 0 |
| LaTeX errors | 0 |
| Type 3 fonts | 0 |
| refs with no label / missing figure files / cites with no bibitem | 0 / 0 / 0 |
| residual "within 20 pc" scope text | 0 |
| residual manuscript-version history | 0 |
