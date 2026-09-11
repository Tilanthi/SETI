# arXiv upload set for v3.41

Verified 2026-09-11: these files, and only these, build the paper from an empty
directory — `pdflatex` x3, **0 errors, 0 undefined references/citations,
36 pages**. Nothing else in this folder is needed by arXiv (the `.py`
generators, `.json`/`.csv` data products, referee letters and BUILD_NOTES are
provenance, not build inputs).

Total 2.6 MB, 19 items:

- `technosignatures_20pc_v3.41.tex`   (bibliography is inline; no .bbl/.bst needed)
- `openjournal.cls`                   (Open Journal of Astrophysics class)
- `epsf.sty`
- `survey_numbers.tex`, `survey_numbers_round5.tex` ... `survey_numbers_round11.tex`
- `tab_compcurve.tex`, `tab_occurrence.tex`
- `figures/`  (24 PDFs)

## Known issue for the arXiv/OJAp version

`figures/pipeline_schematic.pdf` embeds **3 Type 3 fonts** (DejaVu glyphs
sigma, ->, >=) because it was not generated with `pdf.fonttype=42`. Inherited
from v3.39; arXiv accepts it, but it is a production wart. The generator is not
in the version folder. `gs -dNoOutputFonts` removes it (tested: visually
identical at 110 dpi, 40 kB -> 237 kB) at the cost of faint glyph artefacts and
selectable text — an author's call, deliberately not applied.

That schematic also carries ~12 hand-typed survey numbers, which are correct
for the current freeze but are not macro-sourced and will not follow if the
freeze is ever swapped.
