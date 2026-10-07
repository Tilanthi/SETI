#!/bin/bash
# NOTE: the catalogue is rebuilt from the corrected extraction before any
# generator runs; everything downstream therefore derives from it.
# Regenerate every number, table fragment and macro file from the frozen
# inputs, in dependency order.  Run from this directory.
set -e
cd "$(dirname "$0")"
# Matplotlib stamps a CreationDate into every PDF, so without this a
# clean regeneration is reproducible in content but not in bytes.  Pin
# it (2020-01-01T00:00:00Z) and the whole figure set is byte-identical
# run to run.  Found by the v3.50 clean-regeneration test.
export SOURCE_DATE_EPOCH=1577836800
# v4.01 (R2-M2): survey_numbers_round{5,6,7}.tex USED to be restored here
# from frozen_macros/, because the rounds 5-7 generators were never shipped
# and nothing in the build could rebuild them.  Their headers say they came
# from frozen_export_v3.31.json / per_target_results_v3.32.csv -- an
# extraction two revisions before the ACA control-annulus repair -- and 12 of
# their macros were still typeset.  That is literally the referee's "the
# manuscript mixes results from at least two extractions"; it mixed three.
# Every one of the 12 is now computed from the released catalogue, by
# exfrozen_v401.py (round 77), v361_calc.py (the mask half-width sweep),
# v343_calc.py (the drift-grid residual) and make_fig_accel2d.py (the
# TRAPPIST-1 accelerations), and the three frozen files are deleted.
# macrosource.py fails the build if a frozen macro file ever reappears.
# The pre-registered hold-out is applied FIRST, so everything downstream
# reads the survey split and never the full catalogue.
python3 cresp_v401.py               > /dev/null   # -> survey_numbers_round75.tex, cresp_v401.json (R2-M2/M3b: C_resp from the correlator's own lag window, validated against four documented ALMA numbers; NO data dependency, so it runs first and v342_calc can read it)
python3 apply_holdout_v381.py       > /dev/null   # also -> survey_numbers_round71.tex (R2-M7: the hold-out commit and date, so the provenance table cannot drift from the rule)   # -> frozen_export_v3.81_survey.json, holdout_export_v381.json
python3 corrected_export_v399.py   > /dev/null   # MUST FOLLOW apply_holdout (which writes the frozen export) and PRECEDE survey_stats/v342_calc: folds the repaired ACA extraction into the export everything downstream is built from
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
# v4.11: the `cp` is GONE.  tab_selection.tex at the top level -- the one the
# manuscript \inputs -- is selfunc_v411.py's, further down.  Two generators
# writing one typeset table is this project's commonest defect and fragstale's
# S4 clause exists for exactly it.
cp tables/tab_perband.tex   tab_perband.tex
python3 tailboot_v372.py            > /dev/null   # -> tailboot_v372.json (clustered tail CI)
python3 v363_calc.py                > /dev/null   # -> survey_numbers_round29.tex
# make_fig_context_v410.py REPLACES make_fig_context_v342.py and has MOVED to
# the round-103 block below: it reads \EirpNinetyMultA and \EirpNinetySys*A out
# of the macro layer, which did not exist at this point in the script.  Running
# it here is a crash on a clean tree, not a wrong number -- declared, not relied on.
python3 make_fig_missing_v344.py > /dev/null      # -> Figs 5 and 7
# ★★ v4.13 RETIRED: make_fig_hanning.py.  Figure 10 (fig:hanning) plotted the
# analytic 0.25/0.5/0.25 channel response against sub-channel phase, and every
# one of its five numbers (\HanBest, \HanWorst, \HanMed, \HanFacBest,
# \HanFacWorst) is in the paragraph beside it and in Table 2's channel-response
# row.  Measured cost of the figure: one full typeset page.  figures/
# hanning_response.pdf is declared in figorphan.py's PENDING list with its date
# and owner, which is the only way a built-and-uncited figure may survive.
python3 holdout_calib_v381.py       > /dev/null   # -> survey_numbers_round31.tex (out-of-sample calibration)
python3 v381_calc.py                > /dev/null   # -> survey_numbers_round30.tex, tab_flagged_v380.tex
python3 make_fig_selbias.py         > /dev/null   # -> figures/selection_bias.pdf
python3 localnorm_v384.py           > /dev/null   # -> survey_numbers_round33.tex
python3 localnorm_all_v385.py       > /dev/null   # -> survey_numbers_round34.tex (full-sample corrected statistic)
python3 blockboot_v385.py           > /dev/null   # -> survey_numbers_round35.tex (block-resampled null)
python3 drift_strata_v385.py        > /dev/null   # -> survey_numbers_round36.tex, tab_driftstrata_v385.tex (R1-3)
python3 stageonenull_v399.py        > /dev/null   # -> survey_numbers_round47.tex (R1-4: the null for UNATTRIBUTED STAGE-1 events, trigger condition included)
python3 falsealarm_v399.py          > /dev/null   # -> survey_numbers_round46.tex, tab_falsealarm_v399.tex (R1-1); must follow stageonenull
# ★ v4.11: occurrence_v399.py has MOVED to the round-103 block below.  It used
# to read the retired catalogue column `eirp_p90_sel_W` -- the rank-gated
# criterion, 2.876 x the nominal trigger -- which is why every figure of merit
# in the paper was x1.54 optimistic.  It now takes the ADOPTED per-window
# EIRP_90 from `adopted_e90.py`, which needs the stratified completeness and
# the applied parallax, so it can no longer run here.
python3 rfi_v399.py                 > /dev/null   # -> survey_numbers_round49.tex (R2-3: RFI vetting of the unattributed events).  v4.11: the unattributed stage-1 set is maskframe_v411's, in the STELLAR frame, and is asserted against the published \NStageOneUnattrib -- it used to re-derive it from the released sky-frame column and would have opened its sentence with one count and continued with another
python3 extension_v399.py           > /dev/null   # -> survey_numbers_round50.tex + tab_extension_v399.tex (v3.99: the PROSPECTIVE EPOCH EXTENSION; reads export_extension.json, applies the survey's eps Eri B6 withholding rule)
python3 primary_v399.py             > /dev/null   # -> survey_numbers_round51.tex (v3.99 R1-1/R2-2: RADIUS-CORRECTED statistic as PRIMARY, its own conditioned null, tail-factor uncertainty folded in, frozen statistic retained as robustness)
python3 radval_v399.py              > /dev/null   # -> survey_numbers_round52.tex (v3.99 R1-1: PROSPECTIVE out-of-sample validation of the radius correction. VERDICT: FAIL -- the corrected stellar rank is still non-uniform and the median moves further from 0.5, so the frozen screen stays primary and disposition rests on physics)
python3 freqdef_v399.py             > /dev/null   # -> survey_numbers_round53.tex (R1-4: the three frequency-union quantities, defined once and asserted: dnu_A, dnu_B full, dnu_AuB, dnu_B-only)
# ★★★ v4.12: maskcat_v412.py MOVED HERE, from above v343_calc.py.  FIFTH
# CONSECUTIVE CYCLE WITH A FORWARD DEPENDENCY THAT ONLY cleanregen.py CAN SEE,
# and the same shape as make_figures_v328.py's two notes above: its check M7
# ("the searched union this generator masks against is the published one")
# reads \DnuAB out of the macro layer, and freqdef_v399.py is what writes it --
# sixty lines further down than this generator used to run.  Every build in which
# the macro files already existed read the PREVIOUS run's round 53 and passed; a
# build from a clean tree died on `118.125 GHz against None`.  ★ It still precedes
# every generator that imports maskframe_v411.py, and that constraint is on the
# MODULE and not on the products: maskframe does `import maskcat_v412` and calls
# `_mc.MASK`, so what it needs is the file, not this run's output.  Nothing
# between the old position and this one reads round 170 or maskcat_v412.json
# (v352_calc.py emits its own MaskDb* family from the query, not from here).
python3 maskcat_v412.py            > /dev/null   # -> survey_numbers_round170.tex, tab_masklines_v412.tex, maskcat_v412.json.  THE LINE LIST THE MASK IS BUILT FROM: every transition of the twelve named species inside a searched island with E_u <= 150 K, from a frozen Splatalogue query of CDMS and JPL (r11inputs/linelist_v412.json), replacing the hand-kept fifteen-line dictionary that carried no J = 3-2 isotopologue, no HCN(4-3), no HCO+(4-3) and no SO 9_8-8_7.  8 assertions, 8 drives.  MUST PRECEDE every generator that imports maskframe_v411.py, which imports this as a module
# ★★ v4.11: make_figures_v328.py has MOVED to here, after freqdef_v399.py.
# PRE-EXISTING FORWARD DEPENDENCY, visible only to a clean regeneration: the
# coverage-waterfall figure asserts the union it draws against \DnuAB, which
# freqdef_v399.py writes into round 53 -- twenty-six lines further down the
# script than this generator used to run.  Every build in which the macro
# files already existed read the PREVIOUS run's round 53 and passed; a build
# from a clean tree died on `draws 118.125 where \DnuAB is None`.  Fourth
# consecutive cycle in which a forward dependency was caught only by deleting
# the products first, which is the whole argument for cleanregen.py.
python3 make_figures_v328.py --no-copy > /dev/null  # -> figures/*.pdf
python3 visextend_v399.py           > /dev/null   # -> survey_numbers_round54.tex (R1-1: cost of extending the visibility test to every threshold crossing)
python3 epochsplit_v399.py          > /dev/null   # -> survey_numbers_round56.tex (R1-8: repeat blocks vs TEMPORALLY INDEPENDENT epochs; 13 'multi-epoch' systems have all blocks within a day)
python3 stagetable_v386.py          > /dev/null   # -> survey_numbers_round45.tex, tab_stages_v386.tex (R1-4: every stage-1 event at every stage)
# make_fig_funnel.py must follow stagetable_v386.py too: its ledger panel
# reads NStageLocalised. Fourth consecutive round with a forward
# dependency that only the clean-regeneration test caught.
# make_fig_funnel.py must follow v381_calc.py (outlier taxonomy) AND
# localnorm_all_v385.py (the radius-corrected survivor count in step 8 of
# the ledger panel). v3.85: it was above localnorm_all and would have
# regenerated with a stale count from a clean tree.
python3 make_fig_funnel.py          > /dev/null   # -> figures_diagnostic/selection_funnel.pdf.  ONLINE MATERIAL since v4.12: the float drew the three counts the Sec. 3.1 sentence beside it already carried, so it joined the prose instead of replacing it
python3 make_fig_accel2d.py         > /dev/null   # -> survey_numbers_round37.tex, figures/drift_acceleration.pdf (R1-9)
python3 viscal_v399.py              > /dev/null   # -> survey_numbers_round55.tex (R2-1: EMPIRICAL bound on the visibility-calibration term).  # MUST PRECEDE p90_budget, which now folds this term into the combined budget
# v4.09: p90_budget_v385.py is RETIRED and p90_budget_v409.py replaces it,
# further down.  It cannot run here any more: the window-to-window transfer row
# that R1-5 is about is read out of p90r7_v406.py's \Rsev* macros, which are
# written in the v4.06 block below.  The predecessor computed that row from the
# CAMPAIGN interval instead -- the two were literally the same two numbers --
# which is why it could run before them.  make_fig_classa_sens.py reads
# \BudDecorHi out of round 38 and therefore moves with it.
python3 reproduce_from_catalogue_v385.py > /dev/null  # -> survey_numbers_round39.tex (R1-16); FAILS THE BUILD if the catalogue cannot reproduce a headline number
python3 ksrank_v385.py              > /dev/null   # -> survey_numbers_round41.tex (rank uniformity, recomputed on the release)
python3 visdilute_v385.py           > /dev/null   # -> survey_numbers_round42.tex (single-channel dilution of a drifting carrier)
python3 visfit_v385_calc.py         > /dev/null   # -> tab_visfit_v385.tex (v4.01: its TABLE is no longer typeset -- the ledger supersedes it -- but visgain_v399.py still reads the file. Repoint visgain at ledger_v401 and retire this.)
python3 make_fig_dwell2d.py         > /dev/null   # -> figures/dwell_selection.pdf
python3 ecmi_v399.py                > /dev/null   # -> survey_numbers_round57.tex (G-1: cyclotron ceiling vs our band edges, for the beta Pic b MeerKAT detection); asserts the ceiling reproduces the reported upper edge AND that our bands lie above it
python3 drifttrials_v400.py         > /dev/null   # -> survey_numbers_round70.tex (R2-num 22: drift-trial distribution and residual smear BY CLASS; the pooled median of 4 was a Class B number)
python3 blockfate_v409.py           > /dev/null   # -> survey_numbers_round69.tex (R1-8: the fate of every in-scope block the original work list missed -- searched, no archive calibration, legacy calibration failure, disk-infeasible, or reachable and not attempted)
python3 ctrlsep_v400.py             > /dev/null   # -> survey_numbers_round73.tex, tab_ctrlsep_v400.tex (R2-M3(1): the control ensemble redrawn at >=2 theta_syn separation; the rank resolution the field actually supports)
python3 m3a_v400.py                 > /dev/null   # -> survey_numbers_round68.tex, tab_m3a_v400.tex (R2-M2/R1-4: P90^sel measured END TO END through the trigger and the 512-control rank; ASSERTS the positive control and the zero null)
python3 projcodes_v400.py           > /dev/null   # -> survey_numbers_round67.tex, tab_projcodes_v400.tex, project_codes_v413.csv (the ALMA project codes, traceable per execution block IN THE DEPOSIT as ALMA policy requires -- they are no longer listed in the Acknowledgements, which is what Glenn asked for and what 65 codes of padding deserved; resolved EB -> member OUS -> proposal_id with the epoch and the epoch's provenance, and NAMES any block it cannot resolve)
python3 hosts_v399.py               > /dev/null   # -> survey_numbers_round58.tex, tab_hosts_v399.tex (R2-4: SIMBAD activity/multiplicity of the four unattributed hosts; reads the FROZEN hosts_v399.json, --requery to refresh)
python3 maskrobust_v399.py          > /dev/null   # -> survey_numbers_round59.tex, tab_maskrobust_v399.tex (R2-5: line-mask robustness; asserts the attributed/unattributed populations do not overlap and that the adopted half-width lies in the gap)
python3 visgain_v399.py             > /dev/null   # -> survey_numbers_round60.tex (R2-7: measured gain of the visibility statistic over the saturated rank statistic); MUST follow visfit_v385_calc (reads tab_visfit_v385.tex)
python3 acageom_v399.py             > /dev/null   # -> survey_numbers_round61.tex (R2-M3: ACA control-geometry defect; asserts the implemented inner radius lies inside the ACA synthesised beam)
python3 rfialloc_v399.py            > /dev/null   # -> survey_numbers_round63.tex (R2-M6: 94 GHz EESS radar band; ASSERTS no crossing or stage-1 event falls in it)
python3 acafix_v399.py              > /dev/null   # -> survey_numbers_round64.tex (R2-M3: the ACA re-extraction; ASSERTS the pre-registered p>0.05 criterion and stops the build if it ever fails)
python3 acaverify_v399.py           > /dev/null   # -> survey_numbers_round66.tex (R2-M3: honest before/after, computed from the FROZEN and CORRECTED exports separately, with bootstrap intervals and the KS resolution limit)
python3 katcheck_v401.py            > /dev/null   # -> survey_numbers_round79.tex (R2-m26: RUN the known-answer test vectors and report the result; Eq. 3 re-implemented here importing nothing from the search or injection code, which is the point)
python3 exfrozen_v401.py            > /dev/null   # -> survey_numbers_round77.tex (R2-M2: the ex-frozen quantities -- HD 48370 after local rescaling, the Appendix J crossing-ledger tail, the Appendix I mask near-miss bound and the haystack constant -- recomputed from the released catalogue, replacing the ungenerated frozen round5/6/7 files)
# v4.03: ledger_v401.py, make_fig_ledger.py, survey_numbers_round76.tex,
# tab_ledger_v401.tex and figures/ledger_vis.pdf are DELETED, not left beside
# these.  Two macro files defining \LgNCross are a multiply-defined error and
# a stale generator writing round 76 trips roundcollide, so the replacement
# and the removal are one change.  ledger_v403 reports BOTH epoch conventions
# (DECISIONS_R7 A1) and treats the visibility fit as a consistency check
# rather than a filter (A2); \LgNLocal is deliberately NOT redefined, so any
# surviving use of it fails the undefined-macro gate instead of printing a
# number whose meaning has changed.
python3 ledger_v403.py              > /dev/null   # -> survey_numbers_round80.tex, tab_ledger_v403.tex, tab_ledgersum_v403.tex, ledger_legend_v403.tex, ledger_v403.{json,csv} (R1-M4/R2-M1.5: the PRINCIPAL CROSSING LEDGER over all 56 crossings under both epoch conventions, with the A3 chain disposition; 26 checks, each naming the input that would make it fail)
python3 selftest_v403.py            > /dev/null   # GATE: drives 21 perturbed inputs through ledger_v403.py and requires the named check -- and no other -- to be the one that fires.  A check that cannot fail is not a check, and ledger_v401's `if not r['line']` is why this exists.
python3 make_fig_ledger_v403.py     > /dev/null   # -> figures/ledger_vis_v403.pdf (Fig. 5: the same fit under the two reference epochs, and the displacement that drives the difference); MUST follow ledger_v403.py, whose json it reads
python3 epoch_v403.py               > /dev/null   # -> survey_numbers_round81.tex (v4.03: the reference-epoch defect decided by 1,833 injected carriers fitted BOTH ways; what T*>=5 is worth, from the retained 512-control vectors of the catalogue's own windows; and every number about the eta Crv crossing that makes "zero unattributed localised crossings" false). MUST follow ledger_v403.py, whose json it reads
# ★ v4.11 RETIRED: make_fig_chain_v403.py and figures/chain_v403.pdf.  Fig. 7 is
# chain_v411.pdf (make_fig_chain_v411.py, below); nothing cites the v403 figure
# and `figorphan` was failing on it as built-and-included-nowhere.
python3 vispower_v400.py            > /dev/null   # -> survey_numbers_round74.tex, tab_vispower_v400.tex (R2-M5: the POWER of the visibility test, from first principles). MUST FOLLOW ledger_v403.py: v4.03 repointed it from the frozen single-channel fit file at the round-7 ledger, and it ran three dozen lines earlier for one build before the clean-regeneration test found it reading the PREVIOUS run's ledger_v403.json.
# ---------------------------------------------------------------- v4.04
python3 counts_v404.py              > /dev/null   # -> survey_numbers_round82.tex (R2-1: the stale "13 flagged / 4 unattributed" version reconciled against the released catalogue, and WHICH extraction change removed HD 14055 and HD 23484 -- joins the pre-repair frozen export to the post-repair corrected one on (block, window edges))
python3 exposure_v404.py            > /dev/null   # -> survey_numbers_round83.tex (D1+D11: the field-truncation loss (+19 h discarded) and the n_int x median(dt) over-count (-13 to -18.5 h) computed TOGETHER, because each alone misrepresents the survey's exposure in opposite directions). MUST follow v342_calc.py, whose catalogue it reads
python3 parallax_v404.py            > /dev/null   # -> survey_numbers_round84.tex (D6/D7: the omitted annual parallax as a measured per-window systematic, stated and NOT applied, with the direction explicit -- the injection campaign is blind to it, so the limits are optimistic -- and the AU Mic/Ross 154 absolute-scale check with its honest residual)
python3 flare_v404.py               > /dev/null   # -> survey_numbers_round85.tex (R1-9 inverted: 40 of 50 crossings DO localise, so stellar activity is the leading astrophysical alternative and is excluded by measurement instead of by the localisation argument the referee assumed). MUST follow ledger_v403.py, whose localisation count voids R1-9's premise
python3 fa_v404.py                  > /dev/null   # -> survey_numbers_round86.tex (R2-8: the rank-first arithmetic of Appendix J.3, recomputed from the released catalogue. The hand-typed \\SbrAstro/\\SbrResid neither subtracted correctly nor compared in the right direction, and correcting them REVERSES that paragraph's conclusion: the rank-first excess is astrophysical, not evidence of non-exchangeability). MUST follow v342_calc.py and make_numbers.py, whose \\ExpFlags it asserts against
python3 ledgers_v404.py             > /dev/null   # -> survey_numbers_round87.tex (R2-7: closes the extension ledger (136 = 115 + 8 + 13, the 13 processed after the export snapshot), separates the two uncalibrated-block counts by their denominators, and quotes recurrence coverage with its criterion attached instead of the bare 79 per cent). MUST follow blockfate_v409.py, extension_v399.py and v363_calc.py, whose macros it reads back
# ★ v4.11 RETIRED: maskframe_v404.py (round 88).  Its whole purpose was to PROVE
# the line mask is evaluated topocentrically -- which is the defect R2-M3 asks us
# to fix, not a result.  The mask is now evaluated in each star own rest frame by
# maskframe_v411.py (round 160), and \MaskNOffsetsMHz goes with the claim.
python3 fields_v404.py              > /dev/null   # -> survey_numbers_round89.tex (R2-4/R2-15: BD+05 1668's four crossings diagnosed to ONE defective ACA block, with the control MEDIAN named as the missing quality diagnostic; and the withdrawal of the alpha CMa B limit, whose extraction ignored the 50-year visual orbit. ASSERTS that no crossing depends on alpha CMa B before withdrawing it). MUST follow v342_calc.py
python3 selftest_v404.py            > /dev/null   # GATE: drives 45 perturbations through the v4.04 generators and requires each to raise. Writes are redirected by a shim on builtins.open, so no released product can be touched. A check that cannot fail is not a check.
# ---------------------------------------------------------------- v4.05
python3 dispo_v405.py               > /dev/null   # -> survey_numbers_round90.tex, tab_dispo_v405.tex (D4: the disposition computed for all 56 crossings from the frozen 15-line mask topocentrically, against the hand-assigned five-entry literal, with every disagreement printed crossing by crossing). MUST follow v342_calc.py, which owns the computation, the two new catalogue columns and assertions A1/A2
python3 appm_v405.py                > /dev/null   # -> survey_numbers_round91.tex, figures/appm_power.pdf (R2-9: the 1 MHz clustering test reproduced exactly, then shown to have a null that ignores the ALMA channel grid and no power against anything wider than a channel; replaced by a scale-aware scan with a measured power curve). MUST follow v342_calc.py, whose catalogue and CAT_OLD literal it reads
python3 freqocc_v405.py             > /dev/null   # -> survey_numbers_round92.tex (R2-9: the cross-target frequency-occupancy screen re-derived on the STAR rather than the execution-block directory, which WITHDRAWS the z = 3.5 excess -- and the corrected screen is what actually supports the paper's interference statement). Reads occupancy_windows.csv, a frozen 9-column host extract, and v342_calc.py's CAT_OLD
# ★ v4.11 RETIRED: ladder_v405.py (round 93, tab_maskladder_v405.tex).  It emits a
# two-frame mask ladder nothing inputs; the single-frame ladder and the robustness
# table are maskframe_v411.py's (tab_maskrobust_v411.tex, Table maskrobust).
python3 etadrift_v405.py            > /dev/null   # -> survey_numbers_round94.tex (R2-m2: 13 of 403 Class A windows are not drift-resolving, but 0 of 12 stage-1 windows and 0 of 52 Class A crossings, so Appendix J.3 is narrowed rather than deleted). MUST follow v342_calc.py
python3 selftest_v405.py            > /dev/null   # GATE: drives every assertion added in the v4.05 cycle, one at a time, and requires each to raise. Same write-shim discipline as selftest_v404.py.
# ---------------------------------------------------------------- v4.06
python3 numfmt_v406.py              > /dev/null   # GATE: half-up rounding for counted fractions, driven in BOTH directions ('%.2f' % 0.145 == '0.14' must be demonstrated wrong, and a non-tie must be demonstrated to agree).  Imported by freqocc_v405.py and trigunif_v406.py; run first so a broken rounder fails before anything uses it
python3 trigunif_v406.py            > /dev/null   # -> survey_numbers_round95.tex (D16: a flat 5 sigma is not a uniform criterion.  Cells per window span 4.8 decades, so 27-37 of the 51 measured crossings are EXPECTED at a flat 5 sigma and eta Crv is below its own window's requirement; carries the three measured NULLS and the one measured, unapplied matched-filter gain).  MUST FOLLOW v342_calc.py, whose catalogue columns it reads back rather than re-deriving
python3 stack_v408.py               > /dev/null   # -> survey_numbers_round96.tex (D15/D17 + D29/D31: the stellar-frame multi-epoch stacked search, now on the PRIMARY-BEAM-CORRECTED stack keyed on the CANONICAL STELLAR IDENTITY -- registration validated on real lines, gain against sqrt(N_eff) not sqrt(N), Proxima at 4.5e12 W over 66 blocks, the beta Pic two-band positive control (whose agreement DEGRADES to 0.46 km/s as CO(1-0) gains an 8th epoch), zero unattributed computed and driven both ways, and the reflex restriction).  Self-contained: reads only stack_v408/.  Supersedes stack_v406.py
python3 p90r7_v406.py               > /dev/null   # -> survey_numbers_round99.tex (D14: the round-7 completeness campaign, with P90^sel measured through trigger -> visibility localisation and the rank-gated value labelled superseded; AND the chance expectation RE-DERIVED on trigger + localisation + attribution, which is 39x the trigger+rank figure and must not be a relabelling).  MUST FOLLOW v342_calc.py (its D16 columns) and ledger_v403.py (the mask occupancy)
# ---------------------------------------------------------------- v4.07
python3 censusrep_v407.py           > /dev/null   # -> survey_numbers_round100.tex (the census name-collision repair, GENERATED: the 10.3 arcsec separation and the three genuine 0.44-1.55 arcsec collisions measured from the census itself, the two extractions' own statistics side by side, and the companion's unrepresented crossing with the shipped catalogue that still carries it named).  MUST FOLLOW v342_calc.py (the released catalogue) and corrected_export_v399.py (the overwrite counts)
python3 census_dupcheck_v407.py     > /dev/null   # GATE: C1 a census name collision wider than 3 arcsec must be declared with an externally resolved identity; C2 no one-extraction-two-names inside a physical window; C3 every row's EIRP consistent with the dist_pc printed beside it, against a constant computed from first principles and NOT fitted to the rows it tests.  C2 and C3 are independent routes to the same defect, which is the point
python3 selftest_census_v407.py     > /dev/null   # GATE: drives C1/C2/C3, censusfix_v407.apply() and the two new generator assertions in BOTH directions, including the pair of cases that prove the retained star is COMPUTED from the EIRP-implied distance and is not hard-keyed   # GATE: drives every assertion added in the v4.06 cycle, one at a time, and requires each to raise.  Same write-shim discipline as selftest_v404/v405.
# ---------------------------------------------------------------- v4.08
python3 pbaudit_v408.py             > /dev/null   # -> survey_numbers_round101.tex (D29/D31: THE PRIMARY-BEAM AUDIT AS A RESULT -- the offset is computed for every measurement set and the response applied exactly once, so smin = 5 rms / A closes on all 1651 rows; the two new catalogue columns and WHY they are needed (theta_pb_arcsec is the 12 m beam on all 1054 ACA rows); the injection campaign's blindness to A and the proof that the resulting bias is EXACTLY zero; the four-row provenance gap, disclosed and not reconciled; and the one window storing two attenuations against one offset).  MUST FOLLOW v342_calc.py, whose catalogue columns it reads, and imports pbgate_v408.py so the beam-model bound in the text is the one the gate enforces
python3 pbgate_v408.py              > /dev/null   # GATE (D29 item 5): no released window may be published with an uncomputed, zero-by-assumption or unverifiable star-to-phase-centre offset, and S_min must carry the response exactly once.  Reads the CATALOGUE'S OWN two new columns, so a referee can run it; keyed on the POSITION with no name comparison anywhere (position picks the star, rms picks the extraction).  Seven clauses each demonstrated firing, plus drive 8, the regression against the catalogue without the new columns, on which C1 fires on all 1651 rows
python3 selftest_v408.py            > /dev/null   # GATE: drives every assertion added in the v4.08 cycle, one at a time, in BOTH directions where the assertion has two.  Same write-shim discipline as selftest_v404/v405/v406
# ---------------------------------------------------------------- v4.09
# make_fig_classa_sens.py has MOVED to the round-103 block below: its band is
# now the combined interval \BudTotalLo/\BudTotalHi and its abscissa the adopted
# \EirpNinetyMultA, both of which round 103 defines.  It no longer reads
# \BudDecorHi, so the old dependency on p90_budget is gone with it.
python3 v409_calc.py                > /dev/null   # -> survey_numbers_round102.tex, tab_crossdelta_v409.tex, tab_clust_v409.tex, tab_tail_v409.tex, repaired_v409.csv (D35/D36: the repaired T* ADOPTED as the search statistic, so four released crossings fall below the trigger and one rises; the census as a four-step SEQUENCE closing on 1687 windows; referee 2's 345.5 GHz cluster dissolving to p = 0.019/0.82/0.78 with three of its six members among the fallen; eta Crv's crossing excluded as a persistent source at 11.6 sigma by the one other epoch that covers it; the two new HD 14055 crossings with their follow-up stratum declared separately; and D36's three re-runs on the fixed position key).  MUST FOLLOW v342_calc.py (the catalogue) and blockfate_v409.py
# ------------------------------------------------------- rounds 65 and 72
python3 strata_v411.py             > /dev/null   # -> survey_numbers_round65.tex, strata_v411.json, figures/sens_strata.pdf.  WHAT THE INJECTED CARRIERS DEPOSIT (the correlator's three-point channel response at random sub-channel phase, NOT a delta in one channel; 8 per cent short of the exact lag-window response in the phase average, i.e. conservative; and the recovered peak at the 90 per cent point is 1.93x the nominal trigger, which is the arithmetic showing the response is already inside the measured factor and cannot be applied twice), AND the completeness transferred WITHIN STRATA on a rule fixed in advance -- control ring at or above 10 sigma is disc-affected -- giving x3.4 for 390 of 402 Class A windows and a bound above x8 for the other 12, against a blanket x4.4 that is the completeness of no window.  Also measures the star's own leak out of the control ring and shows the apparent 12 m/ACA difference is entirely the four bright-ring windows.  10 assertions, 10 drives.  MUST PRECEDE numbers_v410.py, which reads strata_v411.json for the per-window multiplier
python3 pxapply_v411.py            > /dev/null   # -> survey_numbers_round72.tex, pxapply_v411.json.  THE OMITTED ANNUAL PARALLAX, APPLIED rather than stated: every window's limit divided by its own retained amplitude fraction (shallower, never deeper), and the corrected search run as the published drift-plane maxima against a per-window trigger of 5(1-loss), with the chance expectation recomputed at the SAME per-window trigger so the new crossings are compared with their own null.  Rebuilds one large-loss window from the catalogue's own columns.  8 assertions, 8 drives.  MUST PRECEDE numbers_v410.py, which reads pxapply_v411.json
# ★★ v4.11 (final verification): selfunc_v411.py MOVED UP, from after
# numbers_v410.py to before it.  Round 103 declares three retirements whose
# replacements -- SfMCensus, SfMClassAStars, SfMSearched -- are round 111's,
# and its assertion H2 checks every replacement against the macro layer ON
# DISK.  With the macro files already present that read the PREVIOUS run's
# round 111 and passed; from a clean tree H2 fired and the build stopped.
# Same forward-dependency class as p90_budget_v409.py below, and visible
# only to the clean-regeneration test.  selfunc_v411.py has no intra-tree
# dependency beyond per_target_results_v3.99.csv, written far above, so
# moving it up is safe; p90_budget_v409.py still follows round 103, which
# is what its own note requires.
# ★★ ROUND 14: selfunc_v411.py MOVED UP, from after sens_r11.py to before it.
# sens_r11.py now forms the instrumental term of Table 3 from the one flux
# specification (fluxspec_r14.py) and the macro layer's own parallax and
# visibility-scale terms, instead of reading a frozen round-9 copy of it -- which
# is how \SensFacLo/\SensFacHi went on quoting x0.91-x1.09 after Band 6's
# absolute flux accuracy was corrected from 5 to 10 per cent.  The parallax term
# is round 111's \SfPlxMedPct, so round 111 must exist first.  selfunc_v411.py
# has no intra-tree dependency beyond two catalogues frozen in r10inputs/, which
# is why it could already be moved once for the same class of reason.
python3 selfunc_v411.py            > /dev/null   # -> survey_numbers_round111.tex, tab_selection.tex (R2-M12: the selection function on one parallax cut, every searched star classified, confirmed planets from a dated catalogue; S11 propagates proper motion before matching SIMBAD, which is why it gets 89 of 89 where a position-only join got 77).  No intra-tree dependency; reads two external catalogues frozen in r10inputs/ with their provenance
# ★★★ ROUND 11 / RULING 1: sens_r11.py OWNS THE ADOPTED COMPLETENESS, and it is ONE
# factor measured through trigger + localisation at the star, with the 512-position
# rank -- which annotates a crossing rather than disposing of it -- NOT charged against
# it.  The two-stratum construction of strata_v411.py and its unmeasured 8-20 P_trig
# bound therefore leave the paper: the stratum existed because the rank's cost is a
# function of ring brightness, and trigger-alone recovery is not; the three windows that
# never reached ninety per cent through the rank come back at 3.15/3.24/3.33, inside the
# 2.41-3.36 range of the other eighteen.  adopted_e90.py and numbers_v410.py now read
# sens_r11.json, so this MUST PRECEDE both.  strata_v411.py still runs: pxapply_v411.py
# and sens_r11.py both read strata_v411.json, and sens_r11's own regression reproduces
# the frozen x4.4152 rank-charged criterion out of it, which is what makes the
# reconciliation of 7.99 / 4.42 / 3.06 unconditional rather than asserted.
python3 sens_r11.py                > /dev/null   # -> survey_numbers_round180.tex, sens_r11.json, tab_budget_r11.tex (Table 4), figures/sens_ring.pdf (Fig. 5), pb_atten_fwhm_r11.csv.  R1-2 (the direct injection campaign, stratified by band and array over execution blocks), R2-M3.2 (completeness without the rank: x3.06 P_trig for Class A), R2-M5 (the parallax term is inside each window's own limit or inside a re-extraction, so it leaves the budget) and Appendix A's pb_atten (the released column already uses each row's own dish; the 1.22 -> 1.13 lambda/D FWHM coefficient is the half the referee is right about).  31 assertion drives.  The decorrelation term of Table 3 is MEASURED block by block by decor_r13.py, from the residual path-length fluctuation each block's own QA0 report records on its phase calibrator (r13inputs/decor_r13.json, 279 of 404 blocks, nothing imputed to the rest); decor_r13.py writes no file and claims no macro round, so it is imported here and is not a line of its own.  MUST PRECEDE adopted_e90.py and numbers_v410.py, which read sens_r11.json
python3 sens_r12.py                > /dev/null   # -> survey_numbers_round250.tex, sens_r12.json.  R2-12 (the intermittency campaign: what was varied, at what power, and the measured attenuation = duty cycle), R1-2 (the searched grid obeys a_los = c nudot/nu, checked over all 402 Class A windows), R2-30 (which eps Eri data the flux-scale check uses), and the one typed literal in the smearing paragraph.  7 assertion drives.  Reads only the released catalogue and frozen records, so it has no intra-tree predecessor; it runs here so that round 250 exists before numbers_v410.py
# ---------------------------------------------------------------- round 103
python3 numbers_v410.py --cat . --out . \
  --pick per_target_results_v3.99.csv --pick starrv_v399.json \
  --pick bary_v405.json --pick m3a_result_v400.json \
  --pick freqocc_v405.json  > /dev/null   # -> survey_numbers_round103.tex, tab_maskladder.tex, tab_budget.tex, tab_hzhosts.tex.  ONE value per quantity for every number that was carried twice: the sensitivity on the adopted trigger-plus-screen criterion (EIRP_90, x5.70 Class A / x4.55 Class B, read from the campaign record), the stellar-frame attribution counts over all 56 crossings with the two windows still awaiting a frame term declared and asserted to be rank-flagged, the one benchmark computed from a 12 m dish rather than typed, one combined uncertainty interval with the uncorrected one-sided biases quoted APART from it, and the habitable-zone hosts as distinct stars.  It also RETIRES every superseded synonym by aliasing it to its replacement, so the superseded VALUE is unreachable from any route through the document; `retired.py` fails on the superseded NAME.  MUST BE THE LAST MACRO GENERATOR and the manuscript must \input it last, because its \renewcommands are what make the aliasing bite.  MUST FOLLOW v342_calc.py (the catalogue) and m3a (the campaign record it reads the multiplier from)
# ★★ v4.11: p90_budget_v409.py has MOVED here, after numbers_v410.py.
# PRE-EXISTING FORWARD DEPENDENCY, visible only to a clean regeneration:
# the budget table reads \EirpNinetyFacLo/Hi back out of the macro layer and
# round 103 writes them, fifteen lines further down than this generator used
# to run.  Every build with the macro files already on disk read the PREVIOUS
# run's round 103; a build from a clean tree stops with 'macro
# EirpNinetyFacLo is not generated anywhere'.  Nothing between the two
# positions reads its round 38 -- make_fig_classa_sens.py stopped reading
# \BudDecorHi at v4.09, which is recorded above.
# ★★ v4.11: selfunc_v411.py runs BEFORE p90_budget_v409.py, and the order is
# load-bearing.  The budget's parallax term used a position-only SIMBAD join
# covering 77 of the 89 stars and got a worst fractional error of 1.65 per
# cent; S11 here propagates proper motion before matching, resolves 89 of 89
# -- the twelve it recovers are the nearest, fastest stars, Barnard's Star and
# Proxima among them -- and measures 2.5 per cent.  The budget now reads both
# terms out of this round.  (It no longer needs to follow hzlist_v406.py:
# hzlist reads tables/tab_selection_v328.tex, its own generator's copy.)
python3 p90_budget_v409.py          > /dev/null   # -> survey_numbers_round38.tex, tab_p90budget_v409.tex (R1-15, VERDICT 9: supersedes p90_budget_v385.py.  The window-to-window transfer row R1-5 is about was COMPUTED AND THEN DROPPED by retire_macros.py as unreferenced and never reached the table; PLX_WORST was a typed claim about the sample that nothing compared to the sample (0.0248 against a measured 0.0165, worst star gam Tri = HD 14055); the decorrelation bracket is declared an external assumption; and \BudDominant was chosen from a set including two terms that are not in the quadrature sum it is attributed to).  MUST FOLLOW p90r7_v406.py, whose \RsevTransARange* and \RsevNTransferA it reads, and viscal_v399.py
# ★★ ROUND 14 (sensitivity owner): the ALMA band list, the archival Band 1
# question it raises, and the precision of the one EXTERNAL flux-scale
# check.  MUST FOLLOW p90_budget_v409.py, whose \BudComb it reads back and
# asserts the external check against, and parallax_v404.py, whose
# \PxEpsRatio/\PxJanRatio it reads.  Reads the frozen archive harvest
# r14inputs/band1_archive_r14.json, never the live archive.
python3 sens_r14.py                 > /dev/null   # -> survey_numbers_round460.tex, sens_r14.json (minors 17, 18: ALMA has TEN bands reaching 35 GHz, not eight reaching 84 -- Band 1 since Cycle 10, Band 2 since Cycle 13 -- and four stars of this sample DO have archival Band 1 coverage, in a 31.25 MHz continuum mode 2048x coarser than the narrowest channel searched here and proprietary until 2027.  Also separates the internal AU Mic extractor check from the one external eps Eri comparison, whose precision is +-28 per cent against a quoted +-9.  6 assertions, 6 drives
# ★★ v4.11: selftest_v409.py has MOVED here, with p90_budget_v409.py, which
# it drives.  A gate that drives a generator has to run after it, and the
# budget generator moved after round 103 because it reads \EirpNinetyFacLo
# back out of the macro layer.  Left in its old position on a clean tree it
# reported thirteen cases as CRASHED or NOT DEMONSTRATED -- every one of them
# a self-test whose perturbation never ran.
python3 selftest_v409.py            > /dev/null   # GATE: drives every assertion added in the v4.09 cycle, one at a time, in BOTH directions where the assertion has two.  ★ And it enforces D36's standing rule mechanically: every drive writes to `*_driveN.*`, so a test CANNOT land on a path production reads -- which is the fourteenth defect of the key family and the only one whose mechanism was the test itself
python3 mk_interesting.py tab_interesting.tex > /dev/null   # -> tab_interesting.tex (adopted at the sample owner's request).  Reads the released catalogue, the frozen census, the confirmed-planet table and the adopted multiplier out of the macro layer; eight assertions, five drives.  MUST FOLLOW numbers_v410.py, whose multiplier it reads
python3 ledger_v410.py --no-recur  > /dev/null   # PASS 1: ledger.json only.  recur_v411.py runs the recurrence test ON the adopted crossing list and writes recurcols_v411.json, which PASS 2 needs for Table 6's recurrence columns -- a two-pass dependency, declared here rather than tolerated by printing dashes.  Pass 1 deliberately does NOT write tab_ledger.tex: a provisional table on the path the manuscript \inputs is how a reader ends up with the wrong one
# ------------------------------------------------- rounds 110-160 (round 10)
# Every generator in this block reads the macro layer or the ledger back out,
# so each one must follow what it reads; the order below is that order and is
# stated per line.  ★ The five generators MOVED here from earlier in the
# script are marked MOVED: each of them read the retired catalogue column
# `eirp_p90_sel_W` and now takes the adopted per-window EIRP_90 from
# `adopted_e90.py`, which needs the stratified completeness (round 65) and
# the applied parallax (round 72), neither of which existed where they ran.
python3 adopted_e90.py --selftest  > /dev/null   # GATE: the adopted per-window EIRP_90 has ONE owner.  Asserts the retired `eirp_p90_sel_W` column is absent from the catalogue (so a genuine use raises KeyError rather than returning a number x1.54 too deep), that the superseded value is still deposited under a name that says so, that the adopted limit is at least as shallow as the retired one on every row, and that the median Class A ratio is the 4.42/2.876 = x1.54 by which every figure of merit in the paper was optimistic
python3 dqflag.py --selftest       > /dev/null   # GATE: the data-quality rule has ONE owner too.  Asserts it flags something and not everything, that it spans attributed and unattributed crossings (so it is not a relabelling of "unattributed"), that it is not a relabelling of "crossing", and that the threshold is the declared factor times the survey median
python3 maskframe_v411.py          > /dev/null   # -> survey_numbers_round160.tex, tab_maskrobust_v411.tex, tab_maskband_v411.tex, maskframe_v411.json.  THE MASK AND THE FRAME CHAIN, owned in one place: ledger_v410.py, numbers_v410.py, make_fig_bpic_v410.py, survey_stats.py, v381_calc.py, v362_calc.py, rfi_v399.py, extension_v399.py, primary_v399.py and exfrozen_v401.py all import it as a module, so the ledger table, the chain figure, the robustness ladder and six attribution counts cannot carry three different velocities for one crossing -- which is what they did.  MUST FOLLOW ledger_v410.py, whose ledger.json it reads back
python3 recur_v411.py              > /dev/null   # -> survey_numbers_round120.tex, tab_recurcand_v411.tex, tab_recurcols_v411.tex, tab_visfit_v411.tex, recurcols_v411.json (R2-M5/R1-6/R1-8: the stellar-frame recurrence test applied to EVERY unattributed crossing, and the separation of what the survey could search from what it could confirm).  MUST FOLLOW ledger_v410.py and numbers_v410.py, whose ledger.json and \NCtrl, \LNNRetained, \EpNVisCtrl, \MaskVWidth it reads back
# PASS 2: the ledger table, now with the recurrence columns recur_v411.py measured.
python3 ledger_v410.py             > /dev/null   # -> ledger.json, tab_ledger.tex.  THE CROSSING LEDGER ON THE ADOPTED STATISTIC AND IN THE STELLAR FRAME: the released rows minus the four that fall below the trigger, plus the one that rises, the one that is restored and the two the archival tail adds; one epoch convention, so there is no before and after; and dispositions that sum to the adopted attributed/unattributed split rather than the sky-frame one.  Every delta term is read from the generated delta fragment and the frozen per-crossing records, and the closure is asserted.  MUST FOLLOW numbers_v410.py
python3 prodident.py                             # GATE (v4.11): a frozen record that NAMES a product must prove it is the RIGHT product.  489 windows exist in two directories on the host and 372 of those pairs disagree about the window's own peak statistic, so a script that resolves the ambiguity by sort order is right only by luck -- the round-10 recurrence pass did that once and silently moved four crossings' statistics by 2-4 per cent.  575 of 575 released-tree records reproduce the catalogue's published peak; the re-extraction tree is declared as a different measurement; the three windows the deposited catalogue does not carry are named and pinned.  MUST FOLLOW recur_v411.py
python3 recurnull_v413.py          > /dev/null   # -> survey_numbers_round220.tex, recurnull_v413.json (RULINGS 1-3: the MEASURED null of the recurrence statistic at the predicted cell -- 511 one-cell readings, +0.014 +- 0.046 with unit variance -- which is what shows the +1.13 Referee 2 found to be a property of the printed COLUMN (a maximum over n_rep) and not of the statistic; the widened stellar-frame window set by the implied orbit, 28 exceedances in 320 covering windows against 27.4 by chance; and one definition of sigma_excl.  20 assertions, 19 drives.  MUST FOLLOW ledger_v410.py (pass 2) and recur_v411.py, whose ledger.json and recur_v411.json it asserts against
python3 maskso_v414.py            > /dev/null   # -> survey_numbers_round330.tex, tab_maskspecies_v414.tex, maskso_v414.json (RULING 2/Mo1/Mo5/minor 11: the three sulphur-monoxide coincidences reported as a NOTE on physical grounds, with the counts published both ways; the recurrence test run on the line-attributed crossings, which ledger_v410.py imports from here so Tables 8-9 and this appendix are one computation; the image-sideband test; and the three injection campaigns named apart with their denominators.  9 assertions, 9 drives.  MUST FOLLOW maskframe_v411.py, recur_v411.py and ledger_v410.py (pass 2), whose json and ledger it reads.  REPLACES maskrecur_v413.py (round 240), retired.
# ★★ v4.12 RETIRED: make_fig_chain_v411.py.  Figure 8 is make_fig_chain_v412.py's
# three-level chain (crossing -> unattributed crossing -> confirmed signal), which
# is what R1-1, R1-3 and R2-M3 between them require; chain_v411.pdf drew the rank
# as a step.  Both generators running left two figures built and one included, and
# figorphan fails on that -- correctly, because the deposit would carry a figure
# contradicting the paper's own chain.  The v412 generator runs in the round-11
# block below, after blockq_v412.py and census_v412.py.
python3 blockledger_v411.py        > /dev/null   # -> survey_numbers_round110.tex, tab_blockledger.tex (R2-M2(a)/R2-M12: the block and window ledger -- every set of execution blocks the paper uses, in rows that sum, each count ASSERTED equal to the macro the rest of the paper already uses for it).  MUST FOLLOW blockfate_v409.py, v381_calc.py, survey_stats.py, extension_v399.py, v363_calc.py and ledger_v410.py, all of whose macros it reads back (L11)
python3 statchain_v411.py          > /dev/null   # -> survey_numbers_round130.tex (R2-M8c/d the on-star noise ratio, R2-M8a the direction of the spatial rank, R2-M10b the data-quality disposition).  MUST FOLLOW survey_stats.py, rfi_v399.py and numbers_v410.py, whose \NCtrl, \NWindows, \NCross, \RfiNFrac and \MaskHalfKms it reads back
python3 make_fig_completeness_map.py > /dev/null # -> survey_numbers_round135.tex, figures/completeness_map.pdf (R1-4: the survey-completeness map N*(nu, EIRP)).  MUST FOLLOW numbers_v410.py, whose \EirpNinetyMultA it reads, and v343_calc.py and survey_stats.py, whose \DnuA, \DomAIslands, \NSysClassA and \NWinA it cross-asserts against
python3 stacktol_v411.py           > /dev/null   # -> survey_numbers_round140.tex (R2-M6: every stack tolerance computed from that stack own channel width, paired with the width macro so the two can never be printed apart, plus the stacking weight pathology).  MUST FOLLOW stack_v408.py and numbers_v410.py, whose \ChanAMedKHz, \ChanBModeMHz, \StkBadWeight and \StkProxGain it reads back and asserts against the products
python3 occurrence_v399.py          > /dev/null   # -> survey_numbers_round48.tex (R2-2/R1-9/R2-M11b: CWTFM, transmitter rate, hosting fraction); cross-asserts NSysClassA, UnionClassA, SysUnionAMed.  MOVED (v4.11) from before round 103: it read the retired `eirp_p90_sel_W` column, so EVERY figure of merit in the paper was x1.54 optimistic; it now takes the adopted per-window EIRP_90 from adopted_e90.py and must follow numbers_v410.py
python3 sensdist_v399.py            > /dev/null   # -> survey_numbers_round62.tex (R1-4: P90^sel distribution across systems; built exactly as make_fig_classa_sens does, and cross-asserted against the median).  MOVED (v4.11): same reason -- the adopted per-window value, not the retired column
python3 masoncmp_v401.py            > /dev/null   # -> survey_numbers_round78.tex (R2-M9.2: like-for-like comparison with Mason et al. 2025 in minimum detectable RECEIVED FLUX at matched channel width and matched completeness convention; asserts their published EIRP_min reproduces from their own distance, field rms and channel width)   # MOVED (v4.11)
python3 crespkey_v406.py            > /dev/null   # -> survey_numbers_round97.tex (D18: the delivered channel covariance as a FIFTH independent validation of the response model and the only one sensitive to the averaging factor; and the one mis-keyed window, 51 Eri, whose EIRP was overstated x1.26 in the conservative direction).  MUST FOLLOW v342_calc.py, which owns the keying and the n_chan_avg column   # MOVED (v4.11)
python3 hzlist_v406.py              > /dev/null   # -> survey_numbers_round98.tex (v4.06 residue: Sec. 6.5's habitable-zone M-dwarf list GENERATED -- the count, the searched-ness and the formatted list -- with the literature membership declared once and every named star asserted present in the released catalogue).  MUST FOLLOW v342_calc.py and make_tables_v328.py (tab_selection.tex)   # MOVED (v4.11)
# ★★ v4.11: selftest_v406.py has MOVED here, after crespkey_v406.py and
# hzlist_v406.py.  Both of those now take the ADOPTED per-window EIRP_90
# from adopted_e90.py, which reads strata_v411.json and pxapply_v411.json,
# so a gate that drives their source has to run after those records exist.
# Run from its old position on a clean tree it reported three cases as NOT
# DEMONSTRATED with a FileNotFoundError, which is a self-test passing
# because its perturbation could not run.
python3 selftest_v406.py            > /dev/null
# ★★ v4.12 RETIRED: screencost_v410.py (round 105).  Ruling 1 takes the
# 512-position spatial rank out of the disposition chain, so the completeness is
# no longer charged for it and there is no screen COST to publish: all nine of
# round 105's macros are unreferenced, and its S7 asserted that the adopted
# multiplier in the macro layer is the rank-charged one it computes against --
# which is now false by design.  The quantity that survives is the like-for-like
# rank cost, measured by sens_r11.py over the same injected windows as the
# completeness itself and cited in Sec. 5.1 as \SensCostLike; one generator, one
# campaign, one number, instead of two analyses of the same thing.
# =========================================================================
# ★★★ ROUND-11 GENERATORS.  None of these was in this script, so round 11's
# macro files were in the build root and nothing could rebuild them -- which is
# exactly the defect macrosyn's SOURCE clause exists for, eight times over.
# Every ordering constraint below is the owning agent's own, stated in its queue
# entry; each generator reads macros the ones above it write.
# =========================================================================
python3 blockq_v412.py              > /dev/null   # -> survey_numbers_round175.tex (R1-6: the block-quality criterion applied to the census, and the crossing/attribution counts published PER SEARCH CLASS so the two experiments stop being quoted as one).  MUST FOLLOW maskframe_v411.py and the second ledger_v410.py pass, whose ledger.json it reads; it fails the build on the crossing totals and prints STALE MACRO LAYER on an attribution divergence
python3 events_r12.py               > /dev/null   # -> survey_numbers_round230.tex, events_r12.json (RULING 4/R1-5/R2-4/R2-24/R2-25: the crossing census SPLIT -- the raw total, the four crossings of the one execution block that fails a predefined quality criterion, and the quality-passing population with its own attribution and rank counts -- plus the matched-statistic control maxima that answer R2-4 and the phase-centre test of its IF-spur suggestion.  6 assertions, 6 drives.  MUST FOLLOW ledger_v410.py (pass 2), appm_v405.py, blockq_v412.py and numbers_v410.py, whose ledger.json, appm_v405.json and \BqFailBlock/\ChnUnattrA/\NUnattrRankFlagged/\AppMBand* it reads back
python3 events_v412.py              > /dev/null   # -> survey_numbers_round190.tex, figures/event_crossings.pdf (R1-5/M7/M8: the two unattributed crossings that lead their own control fields, drawn and described from the ledger).  MUST FOLLOW the second ledger_v410.py pass, whose attribution and transition names it reads, so the figure cannot name a transition the ledger no longer names
python3 holdout_v412.py             > /dev/null   # -> survey_numbers_round191.tex, tab_holdout_v412.tex (R2-M8.1/M8.3: the reserved hold-out searched AS a search, the beyond-40 pc control, and the measured overlap of the external calibration sample with the census -- 263 census + 63 hold-out blocks, 0 outside both, which WITHDRAWS "data it had never seen").  MUST FOLLOW ledger_v410.py and maskframe_v411.py, which it imports
python3 cover_v412.py               > /dev/null   # -> survey_numbers_round185.tex, cover_v412.json (R2-M6: the TWO coverage definitions -- union bandwidth and summed window bandwidth -- the confirmation coverage, the benchmark beam and the stacked-search reconciliation).  MUST FOLLOW v343_calc.py, survey_stats.py, numbers_v410.py, stack_v408.py and recur_v411.py, whose macros it reads; C6 asserts the four per-system-sum "coverage" macros are absent from the layer, so it must follow recur_v411.py and not merely precede the build
# ★★★ ROUND 14.  Five new rounds, each after everything it reads back.
# scope_r14.py (410) reads epochsplit_v399.json -- now WRITTEN by
# epochsplit_v399.py rather than frozen -- plus sens_r11.json,
# pxapply_v411.json, \RcConfSysDay (round 120) and adopted_e90 as a module.
python3 scope_r14.py                > /dev/null   # -> survey_numbers_round410.tex, scope_r14.json (RULING 1 / R1-1 / R1-2 / R1-3 / R1-7 / R2-2: EIRP_90 is a SINGLE-EPOCH TRIGGER completeness and is now called one, with confirmation completeness stated separately and zero where the archive observed only once; the Class A restriction of the epoch split, which was computed and never cited, so Fig. 5(b) plotted the 82-system population beside a panel holding 60 Class A points and both referees quoted our own error back at us; and the per-window resampling of the completeness factor.  10 macros, 7 assertions, 7 drives.  MUST FOLLOW epochsplit_v399.py, sens_r11.py, pxapply_v411.py, recur_v411.py and numbers_v410.py
# pairs_v415.py (420) reads ledger.json (pass 2), recurcols_v411.json,
# ledger_v403.json and \WdHalfKms (round 220).
python3 pairs_v415.py               > /dev/null   # -> survey_numbers_round420.tex, tab_pairs_v415.tex, pairs_v415.json (RULING 2 / R2-1 / R2-2 / minors 10, 12, 13, 14: every cross-block pair of crossings within +-833 km/s tested against ONE bounded-acceleration trajectory -- 13 pairs over 5 stars, 0 consistent, the comparison resolving the interval for 7 of them -- with HD 285968's genuine 5-day recurrence as the positive control, which the same test accepts at 0.9 sigma.  6 assertions, 6 drives.  MUST FOLLOW ledger_v410.py (pass 2), recur_v411.py and recurnull_v413.py (round 220)
# epochfix_v415.py (421) reads round 410's \ScSys*, round 120's
# \RcConfSysDay, ledger.json and recurcols_v411.json, and it imports
# epochs_r14.py -- the module epochsplit_v399.py, recur_v411.py,
# cover_v412.py, maskso_v414.py and make_fig_confcov_v412.py also import.
python3 epochfix_v415.py            > /dev/null   # -> survey_numbers_round421.tex, epochfix_v415.json (THE BROKEN EPOCH JOIN: epochs_v386.json resolved every block the archive does not index by asdm_uid through its member OUS and returned the earliest block of that unit, so 252 of 404 stamps are shared and 90 of the 141 checkable ones are wrong, the worst by 246 d.  Measures the defect, calibrates the barycentric witness against 738 block pairs, and closes minors 10, 12, 13 and 14.  14 assertions, 14 drives.  MUST FOLLOW scope_r14.py, recur_v411.py and ledger_v410.py (pass 2)
python3 make_fig_confcov_v412.py    > /dev/null   # -> figures/confcoverage.pdf (R2-M6: Class A systems searchable, confirmable beyond a day and beyond a year, against sky frequency).  MUST FOLLOW cover_v412.py, against whose round 185 it asserts
python3 stack_v412.py               > /dev/null   # -> survey_numbers_round210.tex (R2-M9: WHICH POPULATION the multi-epoch stack describes -- 58 census stars in 58 systems against 11 stacked stars that are not census stars at all -- and the measured noise realisation that makes Proxima's realised 3.19 a 2.80 like-for-like gain).  MUST FOLLOW stack_v408.py, stacktol_v411.py and cover_v412.py, whose \StkNStar, \StkNGroup, \StkNEpochComb, \StkGainVsNeff, \StkProxGain, \SxProxEbCensus and \SxProxEbExt it reads back and asserts against the products
python3 stackfix_v413.py            > /dev/null   # -> survey_numbers_round270.tex (R2-10/R2-14/R2-17/R2-20/R2-32/R2-34: the Proxima limit over the PRIMARY CENSUS alone, so the headline stacked number is computed over the set Sec. 3 says every primary limit is computed over; the reflex tolerance labelled peak to peak; what the 41 non-census blocks actually are; the stacking gain with its noise term printed; and the channel-width span and distance ratios the paper overstated.  11 assertions, 12 drives.  MUST FOLLOW stack_v408.py, stacktol_v411.py, cover_v412.py, occurrence_v399.py, masoncmp_v401.py and stack_v412.py, all of whose macros it reads back
python3 consist_v412.py             > /dev/null   # -> survey_numbers_round195.tex (referee 2's section-3 inconsistency table and minors 1-9: the counts whose sets were never named, each now named beside its denominator).  MUST FOLLOW v342_calc.py, v343_calc.py, strata_v411.py, statchain_v411.py, mk_interesting.py and ledger_v410.py, whose \NCross, \NStageOneBpicEb, \NSmearLo, \NSmearOk and tab_interesting.tex it reads back and asserts against
python3 census_v412.py              > /dev/null   # -> survey_numbers_round205.tex, census_v412.json (ROUND 11 INTEGRATION: ONE owner for the crossing census -- 56 crossings, 20 attributed, 36 unattributed, 2 outranking all 512 controls, 0 recurring -- the 4/31/1 disposition split that ledger_v410.py printed to stdout and published as no macro, and the RECONCILIATION of the released catalogue's 35 Class A unattributed against the ledger's 32, with the three crossings named).  MUST FOLLOW ledger_v410.py, maskframe_v411.py, recur_v411.py, blockq_v412.py and p90r7_v406.py, all of whose counts it reads back
python3 bookkeep_r13.py             > /dev/null   # -> survey_numbers_round340.tex (R2 Mo2/Mo3/Mo4/Mo6 and minors 6, 7, 12, 13: the first-place count with and WITHOUT the trigger condition, which is how 14 against 3.2 and 12 + 0 against 0.78 + 2.43 are one quantity; the hold-out rank displacement compared STAR BY STAR, which is what shows the pooled non-overlap to be a weighting effect and not in-sample tuning; the external calibration sample recounted on the ADOPTED extraction (5 first-place crossings, 4 beta Pic CO, 1 unattributed, 0 in a reserved block) against the harvest figures the paper used to quote; the window-level data-quality flag stated apart from the block criterion built from it; limits from the 4 on-axis eps Eri Band 6 windows, which removes the unlisted exclusion rule; and the Gaia DR3 identity of the one target carried under an ALMA designation.  10 assertions, 10 drives.  MUST FOLLOW blockledger_v411.py and holdout_v412.py (reads \LdgExt*, \CalN*), statchain_v411.py (\NsrFirstObs, \DqSurvMed), sens_r12.py (\EpsEriNOnAxis), blockq_v412.py (\BqNFail) and v344_calc.py (\HanFacWorst, via the corrected \CompoundWorst), all of whose macros it reads back and asserts against.  It reads nothing from round 103, so its position relative to numbers_v410.py is free
python3 census_r12.py               > /dev/null   # -> survey_numbers_round300.tex, census_r12.json (ROUND 12 INTEGRATION: THE CENSUS CLOSURE.  Seven generators publish a count of the threshold crossings and every one of them derives it from ledger.json, which is the condition under which the counts drift apart -- a generator re-run at the wrong moment publishes a census of a ledger that no longer exists.  This reads the ledger once, forms the census as SETS, and requires all 34 published counts to equal the set each claims to be; it publishes the per-window occupancy of the attribution windows as the SUPERSEDED, crossing-conditioned figure that chance_v414.py reads back and measures the move from -- C5, which asserted the direction of that move, is RETIRED with the derivation it guarded, because the same ordering is now asserted by the generator that owns the live expectation (its A2).  7 assertions, 7 drives, the range pinned so a retired drive cannot pass silently.  MUST FOLLOW every generator that publishes a count: numbers_v410.py, blockq_v412.py, events_r12.py, maskframe_v411.py, maskso_v414.py, appm_v405.py and census_v412.py; and it must PRECEDE stats_v413.py, which reads its \CxOccPerWinPct
python3 stats_v413.py               > /dev/null   # -> survey_numbers_round260.tex, stats_v413.json (R1-6/R2-8/R2-9/R2-16/R2-26: ONE population for the chance comparison -- the expectation summed from each window's own measured control exceedance rate over the 402 Class A windows, against the unattributed Class A crossings inside those same windows -- exchangeability measured directly on the reserved blocks instead of rescaled by a rank factor, the cell budget demoted to a cross-check, and the two kinds of on-source hour separated.  ★ v4.14: the attribution mask, the product it formed, its Poisson scatter, the FLOOR built from the scatter and assertion S2b are all RETIRED here -- round 310 owns one chance expectation and one interval, and S2b's margin over the observed count had fallen to 0.8 events, so it would have failed the build on a correct paper the moment one more crossing went unattributed.  This generator now publishes only the TRIGGER sum that round 310 reads back.  6 assertions, 6 drives, the range pinned.  MUST FOLLOW census_v412.py and blockq_v412.py, whose \ChnUnattrA it reads, and v344_calc.py/trigunif_v406.py for \CtrlMaxRatioMed and \FaOverCount
python3 chance_v414.py              > /dev/null   # -> survey_numbers_round310.tex, chance_v414.json (R1-1/R1-2/R2-M2: ONE chance expectation, measured window by window over the census -- each window's own control exceedance rate times the share of its own channel grid the attribution mask does NOT cover, in that star's rest frame, so nothing in the null is conditioned on the crossings -- with ONE interval from resampled execution blocks carrying the finite control ensemble, the block dependence and the exchangeability calibration, and the two archival-tail HD 14055 crossings inside the population on both sides.  7 assertions, 7 drives.  MUST FOLLOW stats_v413.py, census_r12.py, ledger_v410.py and maskso_v414.py, whose macros and json it reads back, and it imports maskframe_v411.py as a module
python3 maskcost_v440.py            > /dev/null   # -> survey_numbers_round440.tex, maskcost_v440.json (RULINGS 5 and 6 / R1-5 / R2-5 / minor 11: a crossing IS the window maximum, verified window by window against the retained per-channel profiles; the price of a line-dominated window and the re-search that recovers all but 0.23 per cent of it; the mask cost against the CLASS A union, 3.05 of 47.7 GHz, not the 4.3 per cent over both classes; and the barycentric/systemic near-cancellation that makes one ledger row look untransformed.  7 assertions, 7 drives.  MUST FOLLOW ledger_v410.py (pass 2), maskframe_v411.py, cover_v412.py, events_r12.py, maskso_v414.py and chance_v414.py, whose ledger.json, \CvUnionA, \EvNAttrQp, \FrMaskLostGHz and \MkNSODecide it reads back
python3 ledger_r14.py               > /dev/null   # -> survey_numbers_round450.tex (R2-6 / R2-8 / minors 15, 16, 19: the smearing coverage of the census -- 1046 windows MEASURED and 605 BOUNDED, 0 neither, where the appendix had said the quantity could not be formed for 1200 of them; the window-level noise-defect cut stated as the cut it is, there being no integration-time cut at all; the eps Eri star-band withholding rule; and the 149-block set named as the epoch-extension campaign it is rather than the archival extension it is not.  39 macros, 12 assertions, 12 drives.  MUST FOLLOW numbers_v410.py, blockledger_v411.py, holdout_v412.py, sens_r12.py, rfi_v399.py and census_v412.py, whose \NWindows, \CsNDumpWin, \NDup, \NDefect, \NWithheld, \HanFacWorst, \PbFloorResp, \EpsEriNWin, \EpsEriNOnAxis, \EpsEriNOffAxis, \HOBlockN, \RfiOccNWin and \NSysEfifteen it reads back, and it imports adopted_e90
python3 stack_r13.py                > /dev/null   # -> survey_numbers_round350.tex (Mo8 + minors 9, 10: the stacked search described over the population it is actually formed on, with the drift tolerance, the median span and the reference channel width each paired with the quantity that sets it).  8 assertions, 8 drives.  MUST FOLLOW stack_v408.py, ledger_v410.py, epochsplit_v399.py, cover_v412.py and numbers_v410.py, whose \NCross, \NUnattributed, \EpMulti, \SxStkStarCensus, \StkDriftTolHzS, \StkSpanMedD, \StkRefChanKHz and \SurvFreqLoA it reads back, and PRECEDE retire_macros.py
python3 prose_v412.py               > /dev/null   # -> survey_numbers_round200.tex (the abstract's and the conclusions' own quantities and the three words of the disposition vocabulary).  MUST FOLLOW blockq_v412.py (round 175), cover_v412.py (round 185) and census_v412.py (round 205), whose \BqFailNCross, \CvUnionA, \CvConfGHzDay and census macros it reads, and maskframe_v411.py/ledger_v410.py for \NUnattrRankFlagged.  Exits 1 on any of its checks
python3 make_fig_chain_v412.py      > /dev/null   # -> figures/chain_v412.pdf (Fig. 8, R1-1/R1-3/M3: three levels -- crossing, unattributed crossing, confirmed signal -- with the count surviving each, the diagnostics drawn beside the middle level rather than inside it, and the reserved hold-out as a separate branch).  MUST FOLLOW blockq_v412.py and census_v412.py
# ★★ v4.12: fragstale.py MOVED DOWN, to below the round-11 generator block.
# It ran at its old position BEFORE blockq/events/holdout/cover/stack/consist/
# census/prose had run in the same pass, so it compared each of their fragments
# with inputs that this run had already rewritten and reported
# `tab_holdout_v412.tex is older than an input it depends on` -- true, and true of
# every round-11 fragment, because the gate was reading the previous run's copy.
# A staleness gate placed above the generators it checks is a check that fails on
# good data, which is as useless as one that cannot fail.
python3 fragstale.py               # GATE: no generated fragment may be older than the generator that owns it, than the catalogue, or than a frozen record that generator reads.  The ledger fragment and the mask ladder were the same failure one file apart -- a tab_*.tex still on disk from a run that happened before the inputs changed, internally consistent and disagreeing with the analysis the paper describes.  A timestamp comparison knows nothing about meaning, which is exactly why a fragment that is self-consistent and wrong cannot fool it; where the generator takes an output directory the fragment is also required to reproduce byte for byte
python3 ledgergate.py              # GATE: the typeset ledger must BE the adopted crossing list -- row count, every (star, block, frequency) both ways, the dispositions summing to the adopted split, and exactly one epoch convention.  Nothing compared these before, and the shipped fragment fails all four clauses
# The two figure generators that READ THE MACRO LAYER must run after it.  Both
# assert the multiplier they plot is not a retired one, so a stale macro layer
# fails here rather than reaching a reader.
python3 make_fig_context_v410.py    > /dev/null   # -> figures/eirp_context_a.pdf, eirp_context_b.pdf (Fig. 1, two panels drawn at the size each is used).  Replaces make_fig_context_v342.py, which now exits non-zero pointing here.  MUST FOLLOW numbers_v410.py: it reads \EirpNinetyMultA and \BenchEirp, and asserts no Arecibo-equivalent line is drawn on any panel
python3 make_fig_bpic_v410.py       > /dev/null   # -> figures/bpic_control.pdf, survey_numbers_round104.tex (the beta Pic positive control: the spatial screen in both directions, and the line-confusion plane the screen has to work in).  MUST FOLLOW numbers_v410.py, whose \MaskHalfKms it reads, AND ledger_v410.py, whose ledger.json it reads.  It was not in this script at all, so on a clean regeneration round 104 was never written, retire_macros.py found eleven \Bpic* macros undefined-and-unreferenced, and the figure's own caption lost every number in it -- 12 undefined control sequences in a build that still produced a PDF.
python3 make_fig_classa_sens.py     > /dev/null   # -> figures/classa_sensitivity.pdf, survey_numbers_round32.tex.  MUST FOLLOW numbers_v410.py (the adopted multiplier and the combined interval it shades) and epochsplit_v399.py (the epoch json behind panel b)
python3 figorphan.py               # GATE: every figures/*.pdf is included somewhere, or named in a dated PENDING list with an owner, and every \includegraphics names a file that exists.  A figure built, deposited and included nowhere is a product nobody can check; one typeset and uncited is a page nobody asked for
python3 labelcheck.py              # GATE: the reference layer.  Two \labels in one float are ONE target with two names, and every \ref to the second silently prints the first one's number -- no warning, no "multiply defined", a perfectly well-formed PDF.  Seven classes, checked at source and again against the .aux with a brace-counting reader, because a regex over \newlabel skips every row whose caption contains braces and the rows it skips are the long formatted captions where the aliases live
python3 wordcase.py                # GATE: NO MACRO WHOSE VALUE IS A LOWER-CASE ENGLISH WORD OR CLAUSE MAY OPEN A SENTENCE, anywhere in the manuscript.  A generated word is lower case by construction -- it is written to sit mid-sentence -- so a sentence that opens on one typesets a misspelling the value, the macro and the grammar are all innocent of: the page read 'and 34 do not. three of the unattributed coincide with sulphur monoxide'.  Every other gate here compares a macro with its source or with another macro and all of them pass; pdflatex cannot see a lower-case letter after a full stop either.  prose_v412.py's P8c catches it in the four front-matter files, where it was found twice in one round; this is the same rule over all 26 prose sources, because the two instances were in two agents' files and the macro behind the first belongs to a third.  Three clauses; W1 demonstrated firing in EVERY ONE of the 26 sources, plus the historic defect itself and a drive proving a commented instance does not count.  MUST FOLLOW every generator, since it reads the macro layer's values
python3 citegate.py                # GATE: the reference layer in BOTH directions -- every \bibitem is cited somewhere and every \cite has a \bibitem, with %-comments stripped so a commented-out citation cannot vouch for an orphan.  Nothing in this build swept citations: xrefcheck does labels, figorphan does figures, macroleak does macros, and the bibliography was the one layer with no owner, so the last two rounds each stranded an entry by hand and found it by hand (AstudilloDefru2017, then White2026).  An uncited bibitem typesets silently and an undefined citation is a WARNING that still produces a PDF, so latexlog passes either way.  Four clauses, each demonstrated firing by --selftest, plus the comment-stripping drive
python3 retired.py                 # GATE: a retired macro name may not appear in the manuscript.  The macro layer makes the superseded VALUE unreachable; this makes the NAME unreachable, and reports file and line so the sentence can be routed to its owner
python3 regen_count.py              > /dev/null   # -> regen_count.tex (must be last but one)
python3 synmacro.py                             # GATE (v4.11): TWO MACROS THAT MEAN THE SAME THING MAY NOT CARRY TWO VALUES.  Every other gate here compares a macro with its own source; nothing compared two macros nobody declared, and that gap put 41 and 21 for the M-dwarf count on the typeset page eleven pages apart -- R2-M2's defect on the number R2-M12(c) told us to correct, with the stale copy the flattering one.  Groups every cited macro by its name stem after a known family prefix and class suffix, reports a differing group, and FAILS on any that is not whitelisted with a one-line reason.  11 declared pairs, 0 undeclared.  MUST FOLLOW every generator
python3 macrosyn.py                 > /dev/null   # R2-M2 GATE: macros that claim to be the same quantity must agree, declared ledger identities must close, and no macro file may exist that no generator writes.  13 of the referee's 16 discrepancies were macro-vs-macro and no other tool compares those.
python3 audit_numbers_v385.py       > /dev/null   # forensic number audit; fails the build if any number is stale
python3 literalsweep.py             > literalsweep.txt  # prose literals that duplicate a macro (report, not a gate)
python3 retire_macros.py            > /dev/null   # drop unreferenced macros (run last)
echo "generators OK"
