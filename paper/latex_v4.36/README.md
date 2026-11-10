# LaTeX source for v4.36 — compiles stand-alone

This folder holds every file the LaTeX build of `technosignatures_40pc_v4.36.pdf` reads (the list was taken
from pdflatex's own `-recorder` file record), and nothing else:

- `technosignatures_40pc_v4.36.tex` — the main file (the reference list is written into it; no BibTeX run is needed)
- `sections/` — the 16 section and appendix files
- `numbers/` — the 216 generated macro files that hold every number printed in the paper
- `tab_*.tex`, `ledger_legend_v403.tex`, `peff_range_v372.tex`, `regen_count.tex` — generated table fragments
- `figures/` — the five figure files
- `openjournal.cls`, `epsf.sty` — the Open Journal of Astrophysics class and a style file it uses

To compile (any TeX Live 2019 or later with the standard packages):

    pdflatex technosignatures_40pc_v4.36.tex
    pdflatex technosignatures_40pc_v4.36.tex
    pdflatex technosignatures_40pc_v4.36.tex

Three passes settle the cross-references. Run with `SOURCE_DATE_EPOCH=1577836800` set in the environment, and
the PDF is byte-identical to `paper/technosignatures_40pc_v4.36.pdf`. Without it, only the embedded date differs.

The full build — the generators that write `numbers/` and the tables, and the checks — is in
`paper_20pc/v4.36/` (see `make_all.sh` and `gate.sh` there).
