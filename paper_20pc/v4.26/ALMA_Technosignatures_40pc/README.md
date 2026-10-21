# Supplementary Data for an Archival ALMA Search for Technosignatures toward Stars within 40 pc

This archive holds the machine-readable data behind an archival search for
narrow-band radio technosignatures toward stars within 40 pc, carried out on
public ALMA observations. It is the supporting data for the article; the
article holds the method, the reasoning and the conclusions, and is the place
to read what these tables mean.

**Cite this archive as:** White G. J. and Dey R., Supplementary Data for an Archival ALMA Search for Technosignatures toward Stars within 40 pc, Zenodo, doi:10.5281/zenodo.0000000. Please cite the version-specific DOI printed on the record you downloaded, together with the article it supports.

Every row here can be traced back to an observation in the ALMA Science
Archive. The execution-block identifier and the ALMA project code travel with
the row, and the project code is cited as `ADS/JAO.ALMA#` followed by its
value.

## What is here

```
ALMA_Technosignatures_40pc/
  README.md
  catalogues/
    spectral_windows.csv                 1663 rows
    stellar_sample.csv                     90 rows
    execution_blocks.csv                  409 rows
    frequency_coverage.csv                 46 rows
    count_accounting.csv                   21 rows
  candidates/
    threshold_crossings.csv                56 rows
    molecular_line_matches.csv            111 rows
    recurrence_tests.csv                   33 rows
  sensitivity/
    class_A_limits.csv                    405 rows
    class_B_limits.csv                   1258 rows
    injection_recovery.csv               4032 rows
    completeness_calibration.csv           10 rows
  statistics/
    control_field_statistics.csv          405 rows
    above_threshold_cells.csv               7 rows
    null_distribution_tests.csv            39 rows
  figures/
    figure_data.csv                         7 rows
    figure_sources.csv                     11 rows
  documentation/
    column_descriptions.md                 17 tables described
  code/
    search_statistic.py
    control_positions.py
    injection_recovery.py
    line_mask.py
```

`documentation/column_descriptions.md` describes every file and every column,
with units. Each `.csv` is comma-separated with one header row, and the
documentation and the files are generated from one specification, so they
cannot disagree about what a column is.

**There is deliberately no separate methods document here. The article is that
document**, and it is the only account of the methods: a second description of
them inside the deposit would create a second place for them to disagree with
the first, which is the one failure this archive is designed not to have. Where
a definition is needed to use a column, `documentation/column_descriptions.md`
gives it and names the quantity the article prints; where a procedure is needed,
`code/` implements it.

The tables join on the identifiers rather than on row order:

* a **window** is (`eb`, `nu_lo_GHz`, `nu_hi_GHz`) -- its execution block and
  its frequency edges;
* a **position** is `target_id`, which distinguishes the components of a pair
  observed in one block, and `star` is the designation the components of a
  pair share;
* a **crossing** is (`eb`, `nu_topo_GHz`);
* a crossing belongs to the window whose edges **contain** its frequency. Two
  crossings lie at a frequency the narrower field reading never reported in
  the same window, so a join on a frequency column finds neither.

## What is not here, and what follows from that

The calibrated visibilities, the per-window extracted spectra and the search
pipeline that produced them are not distributed. **This execution of the
search therefore cannot be re-run from this archive.** What the archive
supports is narrower and is worth stating exactly: the published statistical
summaries can be rebuilt from these tables, row by row, and the definitions
the search rests on can be read, run and checked against them.

Two published quantities cannot be rebuilt from these tables alone, and the
article says so where it quotes them:

1. **the interval on the chance expectation.** The expectation itself rebuilds
   from `statistics/control_field_statistics.csv` -- sum each fine-channel
   window `p_trig_ctrl`, multiply each by one minus its `mask_attr_share` and
   by its `telluric_factor`. Its interval also folds in the resampling of the
   attributed share and the sub-trigger transfer band, and the resampling is
   over quantities that are not per-window.
2. **the per-window completeness of the directly injected windows.** Their
   injection was made into the retained per-integration spectra of real
   windows, and those spectra are not here. The trials of one campaign are
   deposited in `sensitivity/injection_recovery.csv`, and the calibration
   carried to every other window is in
   `sensitivity/completeness_calibration.csv`, but the measurement cannot be
   repeated from this archive.

## The code

`code/` holds four short programs. They are **reference implementations of the
published definitions**, written so that the definitions can be read, run and
checked against the tables deposited beside them. They are **not** the
pipeline that produced the survey, they do not read visibilities, and running
them does not reproduce the survey:

* `code/search_statistic.py` -- the search statistic of the published equation: the drift-aligned, inverse-variance-weighted stack, its noise scale, and the maximum over the channel-by-drift grid;
* `code/control_positions.py` -- the control-position generator: the annulus, scaled to each window's own primary beam, drawn uniform in area from a fixed seed;
* `code/injection_recovery.py` -- the injection-recovery harness: the deposition of a drifting carrier through the channel response at a random sub-channel phase, the reading, and the completeness curve;
* `code/line_mask.py` -- the attribution mask: the stellar-frame offset of a crossing from a catalogued transition, and the half-width test.

Each runs its own known-answer tests with no arguments and needs only Python 3
with `numpy`:

```
cd code
python3 search_statistic.py --demo
python3 control_positions.py --check ../statistics/control_field_statistics.csv
python3 line_mask.py --check ../candidates/threshold_crossings.csv \
                     ../candidates/molecular_line_matches.csv
python3 injection_recovery.py --compare ../sensitivity/injection_recovery.csv
```

Two of those checks read the deposited tables and report whether the rule, as
implemented here, returns what the tables carry: the control annulus of every
window, and the nearest masked transition of every crossing.

## Provenance of the inputs

The observations are public ALMA data, identified by the project codes and
execution blocks in `catalogues/execution_blocks.csv`. The astrometry is
*Gaia* DR3 and the stellar systemic velocities are from SIMBAD. The line list
of `candidates/molecular_line_matches.csv` comes from one query of the
catalogues named in its `line_catalogue` column, through Splatalogue. The
external survey limits in `figures/figure_data.csv` are attributed, value by
value, to the published work they are taken from, with the rescaling applied
to each shown beside it.

## Conventions

* Frequencies are topocentric, as the correlator delivered them, except where
  a column name says `nu_star` or a description says the star rest frame.
* A velocity offset is positive where the crossing lies **above** the
  transition in frequency.
* EIRP limits are at 90 per cent completeness for a carrier inside the
  searched drift range; the survey constrains nothing about a transmitter
  whose apparent acceleration exceeds that range.
* The search statistic is an absolute signal-to-noise ratio, not a local
  contrast, and is read identically at the star and at every control position.
* Reaching the trigger is not a detection. No crossing in this survey is
  offered as a detection, and the dispositions in
  `candidates/threshold_crossings.csv` say what each one is.

## Licence

Creative Commons Attribution 4.0 International (CC BY 4.0), as recorded on the archive landing page. The external survey limits in `figures/figure_data.csv` are the published values of the works cited in that file and are reproduced there with attribution.
