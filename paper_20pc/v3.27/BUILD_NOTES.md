# Building technosignatures_20pc_v3.27

Self-contained: `openjournal.cls`, `epsf.sty`, `figures/`, and the `.bbl`
are all shipped in this folder.

    pdflatex technosignatures_20pc_v3.27.tex   # x3 (converges on the 3rd)

The shipped `.bbl` is used as-is; `bibtex` is not needed
(`...Notes.bib` is a placeholder with no entries).

## The one real gotcha: cm-super
`apt-get install cm-super`. The document is `\usepackage[T1]{fontenc}`, so it
needs T1-encoded EC fonts. Without `cm-super`, pdfTeX silently falls back to
**Type3 bitmap** fonts and STILL EXITS 0 - no error, no warning. The damage:
~8.5% of pixels differ, and the ToUnicode maps break, so copy-paste/search of
the PDF mangles ligatures and punctuation. Check with:

    python3 -c "import pymupdf;d=pymupdf.open('technosignatures_20pc_v3.27.pdf');print({f[3] for p in range(d.page_count) for f in d[p].get_fonts()})"

If any font is named a bare `F<number>`, cm-super is missing.

## v3.27 build state (verified)
| check | result |
|---|---|
| pages | 38 (same as v3.26) |
| undefined references / citations | 0 / 0 |
| multiply-defined labels | 0 |
| Type3 bitmap fonts | 0 |
| main text (Introduction -> Acknowledgements) | 88,655 chars, -20.0% vs v3.26 |
| main text pages | 15 (was 19) |
| printed article (to the Supplementary Material divider) | 20 pp (was 26) |

`make_figures.py` regenerates all 13 data figures from a single JSON export;
re-run it after refreshing the export from the cluster.
