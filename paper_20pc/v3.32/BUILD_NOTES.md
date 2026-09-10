# Building technosignatures_20pc_v3.31

    # 1. refresh the data from the live pipeline (see /shared/SHARED.md for the route)
    SSH="ssh -i /shared/keys/astra-climate.key fetch-agi@34.143.130.135"
    $SSH 'cd /data/SETI && python3 bin/export_figdata.py /data/SETI/logs/figdata_$(date +%Y%m%d).json'
    scp -i /shared/keys/astra-climate.key \
        fetch-agi@34.143.130.135:/data/SETI/logs/figdata_YYYYMMDD.json \
        /workspace/SETI/figwork/v331_data.json
    # 2. regenerate every derived quantity, in this order
    python3 survey_stats.py          # -> survey_stats.json
    python3 make_numbers.py          # -> survey_numbers.tex   (ALL numbers in the paper)
    python3 make_figures_v328.py --no-copy
    python3 make_fig_eirp.py ; python3 make_fig_sample.py
    python3 make_figures_referee_v331.py
    python3 make_tables_v328.py ; python3 make_referee2_artefacts.py
    # 3. build
    pdflatex technosignatures_20pc_v3.31.tex   # x3, converges on the third

## Single source of truth
The manuscript contains no typed digits for survey quantities. It `\input`s the
GENERATED `survey_numbers.tex` (72 macros: `\NWindows`, `\NStars`, `\NSystems`,
`\OccMeasured`, `\SbrN`, `\MasonRatio`, ...). **Never hand-edit a count** — change
the data, re-run the chain above, and the abstract, body, tables and captions all
follow. 316 macro calls in the current source.

**Macro names must contain letters only.** `\NSysIn20` silently breaks the build
(`Missing \begin{document}`), because TeX ends the command name at the digit; it is
`\NSysInTwenty`.

## Gotchas
* **`cm-super` must be installed**, or pdfTeX emits Type 3 bitmap fonts, exits 0 and
  warns about nothing. Verify with
  `python3 -c "import pymupdf;d=pymupdf.open('technosignatures_20pc_v3.31.pdf');print({f[2] for p in range(d.page_count) for f in d[p].get_fonts()})"`
  — must print only `{'Type1','Type0'}`. Test `f[2]=='Type3'`, not bare `F<n>` names.
* **A `DONE` marker on the cluster does not mean usable science.** Check for
  `products/*_result.json`; several targets carry `DONE` *and* `TRANSIENT_FAILURE`.
  Note `find -name "result*.json"` misses them — they are `<EB>_spwN_result.json`.
* Generators carry absolute paths. When branching a version, re-point them
  (`sed -i "s|v3.30/|v3.31/|g" *.py`) or they will silently read and write the old folder.

## v3.31 verified state
| check | result |
|---|---|
| pages | 38 (unchanged since v3.27) |
| data snapshot | 2026-09-10T06:43Z, 462 extracted rows |
| searched | 431 windows / 88 stars / 82 systems / 107 star-bands / 102 EBs |
| flagged / candidates | 4 / 0 |
| undefined refs / cites / multiply-defined / errors | 0 / 0 / 0 / 0 |
| Type 3 fonts | 0 |
| refs w/o label, missing figures, cites w/o bibitem | 0 / 0 / 0 |
