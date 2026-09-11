#!/bin/bash
# Regenerate every number, table fragment and macro file from the frozen
# inputs, in dependency order.  Run from this directory.
set -e
cd "$(dirname "$0")"
python3 survey_stats.py            > /dev/null   # -> survey_stats.json
python3 survey_stats_round10.py    > /dev/null   # -> survey_stats_round10.json
python3 make_numbers.py            > /dev/null   # -> survey_numbers.tex
python3 round8_calc.py             > /dev/null   # -> survey_numbers_round8.tex
python3 round9_calc.py             > /dev/null   # -> survey_numbers_round9.tex
python3 round10_calc.py            > /dev/null   # -> survey_numbers_round10/11.tex, tab_compcurve/occurrence.tex
python3 v342_calc.py               > /dev/null   # -> survey_numbers_round12.tex, tab_ring.tex, per_target_results_v3.42.csv
python3 localnull_calc.py          > /dev/null   # -> survey_numbers_localnull.tex
python3 make_tables_v328.py        > /dev/null   # -> tables/tab_selection.tex, tables/tab_perband.tex
cp tables/tab_selection.tex tab_selection.tex
cp tables/tab_perband.tex   tab_perband.tex
python3 make_figures_v328.py --no-copy > /dev/null  # -> figures/*.pdf
python3 make_fig_context_v342.py > /dev/null       # -> figures/eirp_context.pdf (Fig. 1)
echo "generators OK"
