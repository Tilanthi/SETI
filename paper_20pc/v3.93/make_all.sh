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
# The pre-registered hold-out is applied FIRST, so everything downstream
# reads the survey split and never the full catalogue.
python3 apply_holdout_v381.py       > /dev/null   # -> frozen_export_v3.81_survey.json, holdout_export_v381.json
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
python3 radial_null_v361.py         > /dev/null   # -> radial_null_v361.json (before the figure that uses it)
python3 v357_rankcal.py             > /dev/null   # -> survey_numbers_round22.tex, rank_cdf.pdf
python3 v361_calc.py                > /dev/null   # -> survey_numbers_round27.tex, tab_maskband.tex
python3 radius_matched_v362.py      > /dev/null   # -> radius_matched_v362.json (the repaired null)
python3 v362_calc.py                > /dev/null   # -> survey_numbers_round28.tex
python3 radius_matched_v363.py      > /dev/null   # -> radius_matched_v363.json (repair + LOO)
python3 v363_inputs.py              > /dev/null   # -> trappist_phase / itu5340 frozen inputs
# make_tables_v328.py must precede v363_calc.py: the latter reads the
# M-dwarf row out of tab_selection.tex (v3.72, referee 2 M1).
python3 make_tables_v328.py        > /dev/null   # -> tables/tab_selection.tex, tables/tab_perband.tex  (+ survey_numbers_round43.tex)
cp tables/tab_selection.tex tab_selection.tex
cp tables/tab_perband.tex   tab_perband.tex
python3 tailboot_v372.py            > /dev/null   # -> tailboot_v372.json (clustered tail CI)
python3 v363_calc.py                > /dev/null   # -> survey_numbers_round29.tex
python3 make_figures_v328.py --no-copy > /dev/null  # -> figures/*.pdf
python3 make_fig_context_v342.py > /dev/null       # -> figures/eirp_context.pdf (Fig. 1)
python3 make_fig_missing_v344.py > /dev/null      # -> Figs 5 and 7
python3 make_fig_hanning.py > /dev/null   # -> figures/hanning_response.pdf
python3 holdout_calib_v381.py       > /dev/null   # -> survey_numbers_round31.tex (out-of-sample calibration)
python3 v381_calc.py                > /dev/null   # -> survey_numbers_round30.tex, tab_flagged_v380.tex
python3 make_fig_selbias.py         > /dev/null   # -> figures/selection_bias.pdf
python3 localnorm_v384.py           > /dev/null   # -> survey_numbers_round33.tex
python3 localnorm_all_v385.py       > /dev/null   # -> survey_numbers_round34.tex (full-sample corrected statistic)
python3 blockboot_v385.py           > /dev/null   # -> survey_numbers_round35.tex (block-resampled null)
python3 drift_strata_v385.py        > /dev/null   # -> survey_numbers_round36.tex, tab_driftstrata_v385.tex (R1-3)
python3 stageonenull_v393.py        > /dev/null   # -> survey_numbers_round47.tex (R1-4: the null for UNATTRIBUTED STAGE-1 events, trigger condition included)
python3 falsealarm_v393.py          > /dev/null   # -> survey_numbers_round46.tex, tab_falsealarm_v393.tex (R1-1); must follow stageonenull
python3 occurrence_v393.py          > /dev/null   # -> survey_numbers_round48.tex (R2-2: CWTFM / Transmitter Rate / hosting fraction); cross-asserts NSysClassA, UnionClassA, SysUnionAMed
python3 rfi_v393.py                 > /dev/null   # -> survey_numbers_round49.tex (R2-3: RFI vetting of the unattributed events)
python3 extension_v393.py           > /dev/null   # -> survey_numbers_round50.tex + tab_extension_v393.tex (v3.93: the PROSPECTIVE EPOCH EXTENSION; reads export_extension.json, applies the survey's eps Eri B6 withholding rule)
python3 primary_v393.py             > /dev/null   # -> survey_numbers_round51.tex (v3.93 R1-1/R2-2: RADIUS-CORRECTED statistic as PRIMARY, its own conditioned null, tail-factor uncertainty folded in, frozen statistic retained as robustness)
python3 radval_v393.py              > /dev/null   # -> survey_numbers_round52.tex (v3.93 R1-1: PROSPECTIVE out-of-sample validation of the radius correction. VERDICT: FAIL -- the corrected stellar rank is still non-uniform and the median moves further from 0.5, so the frozen screen stays primary and disposition rests on physics)
python3 freqdef_v393.py             > /dev/null   # -> survey_numbers_round53.tex (R1-4: the three frequency-union quantities, defined once and asserted: dnu_A, dnu_B full, dnu_AuB, dnu_B-only)
python3 visextend_v393.py           > /dev/null   # -> survey_numbers_round54.tex (R1-1: cost of extending the visibility test to every threshold crossing)
python3 epochsplit_v393.py          > /dev/null   # -> survey_numbers_round56.tex (R1-8: repeat blocks vs TEMPORALLY INDEPENDENT epochs; 13 'multi-epoch' systems have all blocks within a day)
python3 stagetable_v386.py          > /dev/null   # -> survey_numbers_round45.tex, tab_stages_v386.tex (R1-4: every stage-1 event at every stage)
# make_fig_funnel.py must follow stagetable_v386.py too: its ledger panel
# reads NStageLocalised. Fourth consecutive round with a forward
# dependency that only the clean-regeneration test caught.
# make_fig_funnel.py must follow v381_calc.py (outlier taxonomy) AND
# localnorm_all_v385.py (the radius-corrected survivor count in step 8 of
# the ledger panel). v3.85: it was above localnorm_all and would have
# regenerated with a stale count from a clean tree.
python3 make_fig_funnel.py          > /dev/null   # -> figures/selection_funnel.pdf (Fig. 3)
python3 make_fig_accel2d.py         > /dev/null   # -> survey_numbers_round37.tex, figures/drift_acceleration.pdf (R1-9)
python3 p90_budget_v385.py          > /dev/null   # -> survey_numbers_round38.tex, tab_p90budget_v385.tex (R1-15)
python3 make_fig_classa_sens.py     > /dev/null   # -> figures/classa_sensitivity.pdf, round32   # MUST follow p90_budget (round38) and epochsplit (json)
python3 viscal_v393.py              > /dev/null   # -> survey_numbers_round55.tex (R2-1: EMPIRICAL bound on the visibility-calibration term, previously 'not separately quantified'; folds into the combined budget)   # MUST follow p90_budget: reads round38
python3 reproduce_from_catalogue_v385.py > /dev/null  # -> survey_numbers_round39.tex (R1-16); FAILS THE BUILD if the catalogue cannot reproduce a headline number
python3 ksrank_v385.py              > /dev/null   # -> survey_numbers_round41.tex (rank uniformity, recomputed on the release)
python3 visdilute_v385.py           > /dev/null   # -> survey_numbers_round42.tex (single-channel dilution of a drifting carrier)
python3 visfit_v385_calc.py         > /dev/null   # -> survey_numbers_round44.tex, tab_visfit_v385.tex (M1: drift-following fit, all 13 events)
python3 make_fig_dwell2d.py         > /dev/null   # -> figures/dwell_selection.pdf
python3 make_fig_unattrib.py        > /dev/null   # -> figures/unattributed_vis.pdf
python3 regen_count.py              > /dev/null   # -> regen_count.tex (must be last but one)
python3 audit_numbers_v385.py       > /dev/null   # forensic number audit; fails the build if any number is stale
python3 literalsweep.py             > literalsweep.txt  # prose literals that duplicate a macro (report, not a gate)
python3 retire_macros.py            > /dev/null   # drop unreferenced macros (run last)
echo "generators OK"
