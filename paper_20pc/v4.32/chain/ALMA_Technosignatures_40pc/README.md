# Supplementary Data for an Archival ALMA Search for Technosignatures toward Stars within 40 pc

The machine-readable data and the code behind an archival search for
narrow-band radio technosignatures toward stars within 40 pc in public ALMA
observations. The article holds the method and the conclusions; this archive
holds what they were computed from and the programs that recompute them.

**Cite as:** White G. J. and Dey R., Supplementary Data for an Archival ALMA Search for Technosignatures toward Stars within 40 pc, Zenodo, doi:10.5281/zenodo.0000000, together with the article it supports.

## Contents

```
ALMA_Technosignatures_40pc/
  README.md
  catalogues/
    spectral_windows.csv                 1663 rows
    stellar_sample.csv                     90 rows
    execution_blocks.csv                  409 rows
    frequency_coverage.csv                 46 rows
    count_accounting.csv                   36 rows
    code_generations.csv                   12 rows
    window_code_generations.csv          2703 rows
    block_sessions.csv                    501 rows
  candidates/
    threshold_crossings.csv                51 rows
    molecular_line_matches.csv            111 rows
    recurrence_tests.csv                   25 rows
    drift_pair_accounting.csv              11 rows
    repeat_epoch_readings.csv              26 rows
  sensitivity/
    class_A_limits.csv                    405 rows
    class_B_limits.csv                   1258 rows
    class_A_limit_uncertainty.csv         405 rows
    system_limits.csv                      60 rows
    injection_recovery.csv               4032 rows
    injection_trials.csv                10332 rows
    completeness_parameters.csv             9 rows
    response_injection_trials.csv       19762 rows
    response_parameters.csv                 4 rows
    completeness_calibration.csv           15 rows
    sensitivity_resampling_windows.csv    390 rows
    sensitivity_resampling_pool.csv        49 rows
    sensitivity_resampling_parameters.csv      7 rows
    recombined_field_values.csv             4 rows
  statistics/
    control_field_statistics.csv          405 rows
    chance_resampling_windows.csv         810 rows
    chance_resampling_blocks.csv          256 rows
    chance_resampling_parameters.csv       50 rows
    recurrence_windows.csv                 93 rows
    look_elsewhere_groups.csv             228 rows
    recurrence_parameters.csv              11 rows
    above_threshold_cells.csv               7 rows
    null_distribution_tests.csv            39 rows
    recalibration_blocks.csv              285 rows
    extractor_version_sample.csv           61 rows
    extractor_reproduction.csv            288 rows
    article_values.csv                     73 rows
  figures/
    figure_data.csv                         7 rows
    figure_sources.csv                      7 rows
  documentation/
    column_descriptions.md                 42 tables described
  code/
    reproduce.py
    sensitivity_summary.py
    completeness.py
    response_ratio.py
    recurrence_expectation.py
    chance_expectation.py
    search_statistic.py
    control_positions.py
    injection_recovery.py
    line_mask.py
    requirements.txt
    pipeline/                          73 programs as run, SHA256SUMS, requirements.txt
```

`documentation/column_descriptions.md` describes every file and every column,
with units and joins; the files and their descriptions are generated from one
specification. Each `.csv` is comma-separated with one header row. Every row
carries the ALMA execution-block identifier and, where it applies, the project
code (cite as `ADS/JAO.ALMA#` followed by its value).

## Rebuilding the article's statistics

Python 3 with `numpy` and `scipy` (`code/requirements.txt` names the releases
the article was computed with) and nothing outside this archive:

```
cd code
python3 reproduce.py              # all of the below, compared with statistics/article_values.csv
python3 chance_expectation.py     # the chance comparison, both field readings
python3 completeness.py           # the Class A completeness factor and its intervals
python3 sensitivity_summary.py    # the per-system median, the count at 1e15 W, their resampling
python3 recurrence_expectation.py # the widened-window recurrence comparison and its two objects
python3 response_ratio.py         # the channel-response ratio and factor of every class and averaging mode
```

`reproduce.py` exits with status 0 when every quantity agrees with the
article. The tolerance is the article's own precision: a rebuilt quantity
agrees when, written to the digits the article prints, it is the article's
value. The Monte Carlo programs draw from the seeds in their parameter files
(chance comparison 310; completeness bootstrap 1800; sensitivity resampling 1300028); with those seeds and the NumPy release named there they repeat the
computation reported draw for draw, and `reproduce.py --seed-offset 1` shows
the size of the Monte Carlo error. The inputs are the three
`statistics/chance_resampling_*` tables (every window's control count and
exceedances, its attribution, the per-block exceedance counts, the
atmospheric counts), `sensitivity/injection_trials.csv` with
`completeness_parameters.csv` (10332 injection trials in 49
windows), and the three `sensitivity/sensitivity_resampling_*` tables. The
control positions of every window are reproducible from `ring_seed` in
`statistics/control_field_statistics.csv`, and blocks are grouped into
observing sessions by `catalogues/block_sessions.csv`.

Four reference implementations of the published definitions run their own
known-answer tests:

```
python3 search_statistic.py --demo
python3 control_positions.py --check ../statistics/control_field_statistics.csv
python3 line_mask.py --check ../candidates/threshold_crossings.csv ../candidates/molecular_line_matches.csv
python3 injection_recovery.py --compare ../sensitivity/injection_recovery.csv
```

## The search pipeline

`code/pipeline/` holds the programs that took the public execution blocks to
the per-window statistics, byte-identical to the copies that ran
(`code/pipeline/SHA256SUMS`), with the releases they ran under
(`code/pipeline/requirements.txt`, CASA included). They read calibrated
visibilities, which are not distributed here, so the search itself cannot be
re-run from this archive alone; it can be re-run from the ALMA Science Archive
with this code.

## Not here

The calibrated visibilities (of order a terabyte) and the per-window extracted
spectra. The dynamic spectra around each threshold crossing are a second file
of this record.

## Joins

* a **window** is (`target_id`, `eb`, `nu_lo_GHz`, `nu_hi_GHz`); all four
  fields are needed, because 14 stars share spectral windows of one
  block and (`eb`, `nu_lo_GHz`, `nu_hi_GHz`) alone repeats over 66
  rows of `catalogues/spectral_windows.csv` (35 windows would be lost);
* a **position** is `target_id`; `star` is the designation the components of a
  pair share;
* a **crossing** is (`eb`, `nu_topo_GHz`) and belongs to the window whose
  edges contain its frequency.

## Conventions

* Frequencies are topocentric, as the correlator delivered them, except where
  a column name says `nu_star` or a description says the star rest frame.
* A velocity offset is positive where the crossing lies above the transition.
* EIRP limits are at 90 per cent completeness for a carrier inside the
  searched drift range.
* Reaching the trigger is not a detection; the dispositions in
  `candidates/threshold_crossings.csv` say what each crossing is.

## Licence

Creative Commons Attribution 4.0 International (CC BY 4.0), as recorded on the archive landing page. The external survey limits in `figures/figure_data.csv` are the published values of the works cited in that file and are reproduced there with attribution.
