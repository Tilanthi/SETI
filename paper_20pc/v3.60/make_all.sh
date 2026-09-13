#!/bin/bash
# Regenerate every number, table fragment and macro file from the frozen
# inputs, in dependency order.  Run from this directory.
set -e
cd "$(dirname "$0")"
# Matplotlib stamps a CreationDate into every PDF, so without this a
# clean regeneration is reproducible in content but not in bytes.  Pin
# it (2020-01-01T00:00:00Z) and the whole figure set is byte-identical
# run to run.  Found by the v3.50 clean-regeneration test.
export SOURCE_DATE_EPOCH=1577836800
# survey_numbers_round{5,6,7}.tex are FROZEN INPUTS: the rounds 5-7 generators
# were never shipped with the release, so nothing here can rebuild them.  They
# are kept under frozen_macros/ and restored first, which is what makes a clean
# regeneration from this folder possible at all.  Found by deleting every
# generated file and re-running this script (v3.46); before that, a clean
# regeneration left the manuscript unable to compile.
cp frozen_macros/survey_numbers_round5.tex survey_numbers_round5.tex
cp frozen_macros/survey_numbers_round6.tex survey_numbers_round6.tex
cp frozen_macros/survey_numbers_round7.tex survey_numbers_round7.tex
python3 survey_stats.py            > /dev/null   # -> survey_stats.json
python3 survey_stats_round10.py    > /dev/null   # -> survey_stats_round10.json
python3 make_numbers.py            > /dev/null   # -> survey_numbers.tex
python3 round8_calc.py             > /dev/null   # -> survey_numbers_round8.tex
python3 round9_calc.py             > /dev/null   # -> survey_numbers_round9.tex
python3 round10_calc.py            > /dev/null   # -> survey_numbers_round10/11.tex, tab_compcurve/occurrence.tex
python3 v342_calc.py               > /dev/null   # -> survey_numbers_round12.tex, tab_ring.tex, per_target_results_v3.54.csv
python3 v343_calc.py             > /dev/null   # -> survey_numbers_round13.tex
python3 v344_calc.py               > /dev/null   # -> survey_numbers_round14.tex
python3 recurrence_calc.py         > /dev/null   # -> survey_numbers_recurrence.tex
python3 localnull_calc.py          > /dev/null   # -> survey_numbers_localnull.tex
python3 pointing_calc.py           > /dev/null   # -> survey_numbers_pointing.tex
python3 v346_calc.py               > /dev/null   # -> survey_numbers_round15.tex
python3 v347_calc.py               > /dev/null   # -> survey_numbers_round16.tex
python3 v348_calc.py                > /dev/null   # -> survey_numbers_round17.tex
python3 v350_calc.py                > /dev/null   # -> survey_numbers_round18.tex
python3 v351_calc.py                > /dev/null   # -> survey_numbers_round19.tex
python3 bpic_ctrl_calc.py           > /dev/null   # -> survey_numbers_bpicctrl.tex
python3 hd23484_calc.py             > /dev/null   # -> survey_numbers_hd23484.tex
# v3.52-v3.60 generators.  v358_inject.py must precede v352_calc.py: the latter
# reads \StratTransferLo/Hi back out of survey_numbers_round23.tex.  All four
# were missing from this script until v3.60 -- only the clean-regeneration test
# catches that, and it is the same defect as the v3.51 round (make_all.sh did
# not run the round's own generator).
python3 v358_inject.py              > /dev/null   # -> round23/24/25/26, stratified_completeness.pdf
python3 v352_calc.py                > /dev/null   # -> survey_numbers_round20.tex (needs round23)
python3 v353_heldout_cluster.py     > /dev/null   # -> survey_numbers_round21.tex
python3 v357_rankcal.py             > /dev/null   # -> survey_numbers_round22.tex, rank_cdf.pdf
python3 make_tables_v328.py        > /dev/null   # -> tables/tab_selection.tex, tables/tab_perband.tex
cp tables/tab_selection.tex tab_selection.tex
cp tables/tab_perband.tex   tab_perband.tex
python3 make_figures_v328.py --no-copy > /dev/null  # -> figures/*.pdf
python3 make_fig_context_v342.py > /dev/null       # -> figures/eirp_context.pdf (Fig. 1)
python3 make_fig_missing_v344.py > /dev/null      # -> Figs 5 and 7
python3 make_fig_funnel.py > /dev/null      # -> figures/selection_funnel.pdf (Fig. 2)
python3 retire_macros.py            > /dev/null   # drop unreferenced macros (run last)
echo "generators OK"
