# Column descriptions

Every table in this archive is described here: what each file holds, how it joins the others, and what every column means and is measured in. The descriptions and the files are generated together from one specification, so a documented column that the file does not have, or a column the documentation does not mention, is not possible.

A blank unit means the quantity is a count, a flag, a name or a ratio. A flag is written 1 or 0 and never as a word. An empty field means the value does not apply or is withheld, and never zero; each file header says which.

## `catalogues/spectral_windows.csv`

1663 rows, 42 columns.

One row per searched spectral window: the window-level measurement every count in the article is formed from.

A window is identified by its target identifier, its execution block and its frequency edges; those four fields are unique over the table.

Two readings of the trigger are given. The adopted statistic is read over the whole primary beam (trigger_whole_beam) and is the one the crossing table is built on; trigger_narrow_field is the same statistic read over the narrower extraction field, which drops the integrations whose pointing falls outside it. They differ on six rows, which trigger_flags_agree selects without recomputation.

An empty field is a value that does not apply, never a zero: the control terms are measured on the fine-channel windows and are empty on the coarse ones.

**Joins.** star joins stellar_sample.csv; eb joins execution_blocks.csv; (eb, nu_lo_GHz, nu_hi_GHz) joins the sensitivity tables; a crossing is tied to its window by frequency CONTAINMENT in (nu_lo_GHz, nu_hi_GHz), not by equality with crossing_nu_topo_GHz.

| column | unit | description |
|---|---|---|
| `star` | -- | star designation, as used throughout the article and in every file here |
| `system` | -- | system identifier; the components of a bound pair share it |
| `target_id` | -- | identifier the window was extracted under, which distinguishes the components of a pair observed in one execution block |
| `ra_deg` | deg | right ascension of the extraction position, ICRS |
| `dec_deg` | deg | declination of the extraction position, ICRS |
| `eb` | -- | ALMA execution block (ASDM) identifier; with the project code this retrieves the original data from the ALMA Science Archive |
| `project_code` | -- | ALMA project code, cited as ADS/JAO.ALMA# followed by this value |
| `date_utc` | date | UTC date of the execution block |
| `t_start_mjd` | d | adopted start epoch of the execution block, MJD |
| `band` | -- | ALMA receiver band |
| `nu_lo_GHz` | GHz | lower edge of the spectral window, topocentric as delivered |
| `nu_hi_GHz` | GHz | upper edge of the spectral window, topocentric as delivered |
| `chan_width_Hz` | Hz | delivered channel width |
| `on_source_s` | s | on-source integration time at this position |
| `n_int` | -- | integrations retained at this position |
| `rms_mJy` | mJy | per-channel noise at the extraction position |
| `smin_mJy` | mJy | amplitude limit at the trigger, five times the noise divided by the primary-beam response |
| `theta_pb_arcsec` | arcsec | primary-beam FWHM recorded for this window; the compact array is identifiable by it |
| `pb_offset_arcsec` | arcsec | angular offset of the star from the phase centre |
| `pb_atten` | -- | primary-beam response at the star, between 0 and 1 |
| `dist_pc` | pc | distance adopted for the star |
| `search_class` | -- | A where the window resolves a carrier in one channel, B where the channel is coarse |
| `drift_max_Hz_s` | Hz/s | largest drift rate searched in this window |
| `a_max_m_s2` | m/s2 | line-of-sight acceleration that corresponds to it |
| `n_drift_trials` | -- | drift trials searched |
| `n_search_cells` | -- | search cells in this window, channels times drift trials |
| `n_ind_cells` | -- | independent cells after the correlation between neighbouring drift trials is accounted for |
| `eirp_p90_W` | W | adopted 90 per cent completeness EIRP limit; the smearing retention divided out is the one measured on the delivered channel response, not the transform-limited form |
| `eirp_p90_lo_W` | W | lower end of its interval: the dispersion measured between the directly injected windows, the same pair of factors on every row, and not a bound measured in this window's own band and channelisation |
| `eirp_p90_hi_W` | W | upper end of that interval, on the same basis |
| `completeness_basis` | -- | injected where this window carries its own injection ladder, transferred where its completeness comes from the calibration of completeness_calibration.csv |
| `T_star_narrow_field` | -- | de-drifted search statistic at the stellar position, read over the narrower extraction field |
| `T_ctrl_max_narrow_field` | -- | largest statistic among the window control positions, same field |
| `n_ctrl` | -- | control positions in this window ensemble |
| `n_ctrl_trig` | -- | how many of them reach the trigger |
| `mask_attr_share` | -- | share of those control exceedances the attribution mask takes, in the star rest frame |
| `telluric_factor` | -- | factor by which the remaining exceedances are reduced by the atmospheric screen, applied to the crossings on the same radius and in the same topocentric frame |
| `trigger_whole_beam` | -- | 1 where this window holds a threshold crossing under the adopted whole-beam statistic |
| `trigger_narrow_field` | -- | 1 where it holds one under the narrower extraction field |
| `trigger_flags_agree` | -- | 1 where the two readings agree, 0 on the six rows where they do not |
| `crossing_nu_topo_GHz` | GHz | frequency of the adopted crossing this window holds, empty where it holds none; it can differ from the narrower field's own peak in the same window |
| `disposition` | -- | disposition carried in the crossing table, where there is one |

## `catalogues/stellar_sample.csv`

90 rows, 19 columns.

One row per searched target identifier: the sample the survey was carried out on, with what was searched toward each position.

There are 90 identifiers over 87 designations and 83 systems; the difference is the components of bound pairs, which share a designation and sometimes a system but were extracted at their own positions. The article count of searched stars is a count of these identifiers.

Two archival-tail execution blocks lie outside the window extent of this deposit; the two crossings they hold are in threshold_crossings.csv and are not counted in the per-star window totals here.

**Joins.** target_id joins spectral_windows.csv and the sensitivity tables; star joins threshold_crossings.csv and recurrence_tests.csv.

| column | unit | description |
|---|---|---|
| `star` | -- | star designation, as used throughout the article |
| `system` | -- | system identifier; the components of a bound pair share it |
| `target_id` | -- | identifier the windows were extracted under; unique over this table |
| `ra_deg` | deg | right ascension of the extraction position, ICRS |
| `dec_deg` | deg | declination of the extraction position, ICRS |
| `dist_pc` | pc | distance adopted for the star |
| `n_blocks` | -- | execution blocks searched toward this position |
| `n_windows` | -- | spectral windows searched toward it |
| `n_windows_class_A` | -- | of those, windows that resolve a carrier in one channel |
| `n_windows_class_B` | -- | of those, windows with a coarse channel |
| `bands` | -- | ALMA receiver bands with at least one searched window, joined by + |
| `nu_min_GHz` | GHz | lowest window edge searched toward this position |
| `nu_max_GHz` | GHz | highest window edge searched toward it |
| `on_source_h` | h | summed on-source time over its windows; windows of one block overlap in time, so this is a window total and not an observing duration |
| `eirp_p90_min_W` | W | deepest 90 per cent completeness EIRP limit among its windows |
| `eirp_p90_median_W` | W | median of that limit over its windows |
| `n_crossings_whole_beam` | -- | threshold crossings in its windows under the adopted whole-beam statistic |
| `n_crossings_narrow_field` | -- | the same count under the narrower extraction field |
| `project_codes` | -- | ALMA project codes its blocks belong to, joined by + |

## `catalogues/execution_blocks.csv`

409 rows, 18 columns.

One row per execution block of the primary census: the archival accounting that ties every searched window to a retrievable observation.

The block identifier and the project code together retrieve the original data from the ALMA Science Archive, where the project code is cited as ADS/JAO.ALMA# followed by its value.

epoch_source records where the epoch was read: block means the block's own recorded start, and any other value means it was resolved through the member observing unit instead.

Two rows are archival-tail blocks. Each holds a threshold crossing and lies outside the window extent of this archive, so every window column of theirs is empty and their project code is not resolved here; the block identifier alone retrieves them from the archive. They are present so that every crossing names a block this table has.

The block sets outside these two -- the reserved hold-out, the archival extension, the out-of-sample control beyond 40 pc, and the blocks that were not searched and why -- are accounted for in the article's own block ledger, which this table does not duplicate.

**Joins.** eb joins spectral_windows.csv, threshold_crossings.csv and recurrence_tests.csv.

| column | unit | description |
|---|---|---|
| `eb` | -- | ALMA execution block (ASDM) identifier |
| `project_code` | -- | ALMA project code; cite as ADS/JAO.ALMA# followed by this value |
| `date_utc` | date | UTC date of the block |
| `epoch_mjd` | d | adopted start epoch, MJD |
| `epoch_source` | -- | block where the epoch is the block's own recorded start, otherwise the route by which it was resolved |
| `bands` | -- | ALMA receiver bands searched in this block, joined by + |
| `n_targets` | -- | target identifiers searched in it |
| `targets` | -- | their star designations, joined by + |
| `n_windows` | -- | spectral windows searched in it |
| `n_windows_class_A` | -- | of those, fine-channel windows |
| `n_windows_class_B` | -- | of those, coarse-channel windows |
| `nu_min_GHz` | GHz | lowest window edge searched in it |
| `nu_max_GHz` | GHz | highest window edge searched in it |
| `on_source_h` | h | largest on-source time among its windows, which is the block's own on-source duration at that position |
| `theta_pb_median_arcsec` | arcsec | median recorded primary-beam FWHM of its windows; the compact array is identifiable by it |
| `n_crossings_whole_beam` | -- | threshold crossings in it under the adopted whole-beam statistic |
| `n_crossings_narrow_field` | -- | the same count under the narrower extraction field |
| `set_name` | -- | the block set this row belongs to: primary census, or archival tail for the two blocks that lie outside the window extent of this archive |

## `catalogues/frequency_coverage.csv`

46 rows, 14 columns.

One row per contiguous island of searched frequency: the union the windows cover, with what was searched in each part of it.

Islands are formed by merging the topocentric edges of all searched windows, so the widths here sum to the searched union and not to the sum of the window widths, which double-counts the frequencies two blocks share.

masked_GHz is the width inside the island covered by the attribution mask, computed as the adopted half-width about every transition of molecular_line_matches.csv WITH in_mask = 1. The 15 rows of that file the mask leaves out (SO) are not included, and including them would give a larger masked width than the article publishes. The survey constrains nothing inside the masked width.

**Joins.** nu_lo_GHz and nu_hi_GHz bracket the windows of spectral_windows.csv that fall in the island; the transitions are those of molecular_line_matches.csv with in_mask = 1 and a rest frequency inside it.

| column | unit | description |
|---|---|---|
| `island` | -- | island number, ordered by frequency |
| `nu_lo_GHz` | GHz | lower edge of the island, topocentric |
| `nu_hi_GHz` | GHz | upper edge of the island, topocentric |
| `width_GHz` | GHz | its width |
| `bands` | -- | ALMA receiver bands contributing to it, joined by + |
| `n_windows` | -- | searched windows lying inside it |
| `n_windows_class_A` | -- | of those, fine-channel windows |
| `n_windows_class_B` | -- | of those, coarse-channel windows |
| `n_targets` | -- | target identifiers with a window inside it |
| `n_blocks` | -- | execution blocks with a window inside it |
| `masked_GHz` | GHz | width inside the island covered by the attribution mask |
| `masked_fraction` | -- | that width as a fraction of the island width |
| `n_masked_transitions` | -- | transitions of the MASK (molecular_line_matches.csv with in_mask = 1) whose rest frequency lies inside it; the rows the mask leaves out are not counted |
| `n_crossings_whole_beam` | -- | threshold crossings inside it under the adopted statistic |

## `candidates/threshold_crossings.csv`

56 rows, 41 columns.

One row per threshold crossing: every cell in the survey whose de-drifted search statistic reached the trigger at a stellar position, under the adopted whole-beam statistic.

trigger_whole_beam is 1 on every row by construction, because this is the adopted set; trigger_narrow_field records whether the same window also holds a crossing under the narrower extraction field, and it is 0 on two rows. Four further windows hold a narrow-field crossing and no adopted one; they are in spectral_windows.csv with trigger_flags_agree = 0.

atmospheric_flag marks the one crossing the atmospheric screen removes from both sides of the chance comparison. It is a crossing, it is unattributed, and it is tested for recurrence; what the flag records is that it is excluded from the comparison with chance, because the control side is screened on the same radius in the same topocentric frame.

masked_transition and masked_dv_kms give the nearest transition of the attribution mask in the star rest frame. nearest_transition gives the nearest catalogued transition of any species in the wider query, which is a different quantity: a crossing can be far from any masked line and close to an unmasked one.

An empty field is a value withheld, not a zero.

**Joins.** star_in_sample joins stellar_sample.csv; (eb, nu_topo_GHz) is unique and joins recurrence_tests.csv; the window is the row of spectral_windows.csv with the same eb whose edges CONTAIN nu_topo_GHz -- two crossings lie at a frequency the narrower field never reported in the same window, so a join on a frequency column finds neither; two further crossings lie in archival-tail blocks outside the window catalogue and carry in_window_catalogue = 0.

| column | unit | description |
|---|---|---|
| `star` | -- | star designation of the position the crossing was found at |
| `star_in_sample` | -- | designation under which the sample table counts that position; it differs from star for the one component whose extractions are second readings of windows the sample counts under its primary |
| `eb` | -- | ALMA execution block (ASDM) identifier of the discovery block |
| `project_code` | -- | its ALMA project code, empty for the two archival-tail blocks; cite as ADS/JAO.ALMA# followed by this value |
| `date_utc` | date | UTC date of that block |
| `band` | -- | ALMA receiver band |
| `nu_topo_GHz` | GHz | crossing frequency as delivered by the correlator |
| `nu_star_GHz` | GHz | the same frequency in the star rest frame |
| `window_nu_lo_GHz` | GHz | lower edge of the window that holds it, empty for the archival-tail crossings |
| `window_nu_hi_GHz` | GHz | upper edge of that window |
| `search_class` | -- | class of that window, A fine or B coarse |
| `in_window_catalogue` | -- | 1 where the host window is in spectral_windows.csv, 0 for the two crossings in archival-tail blocks outside its extent |
| `T_star` | -- | de-drifted search statistic at the stellar position, the quantity of Eq. 1 |
| `T_ctrl_max` | -- | largest statistic among that window control positions |
| `rms_mJy` | mJy | per-channel noise of the host window at the extraction position |
| `eirp_p90_W` | W | that window 90 per cent completeness EIRP limit |
| `masked_transition` | -- | nearest transition of the attribution mask in the star rest frame |
| `masked_dv_kms` | km/s | stellar-frame offset from it, positive where the crossing lies above the transition in frequency |
| `mask_coincident_not_attributed` | -- | 1 where the crossing lies inside the mask and is not attributed |
| `attributed` | -- | 1 where the crossing is attributed to a catalogued transition |
| `nearest_transition` | -- | species of the nearest catalogued transition of any species, from the wider catalogue query; empty where the query is not deposited |
| `nearest_transition_qn` | -- | its quantum numbers as the catalogue gives them |
| `nearest_transition_GHz` | GHz | its rest frequency |
| `nearest_transition_dv_kms` | km/s | stellar-frame offset of the crossing from it |
| `nearest_transition_catalogue` | -- | the line catalogue the entry was taken from |
| `atmospheric_flag` | -- | 1 on the crossing the atmospheric screen removes from both sides of the chance comparison; it remains a crossing and remains unattributed |
| `atmospheric_species` | -- | the atmospheric species responsible |
| `atmospheric_line_GHz` | GHz | its transition frequency, topocentric |
| `atmospheric_offset_MHz` | MHz | offset of the crossing from it, inside the screening radius |
| `trigger_whole_beam` | -- | 1 on every row: this table is the adopted whole-beam set |
| `trigger_narrow_field` | -- | 1 where the host window also holds a crossing under the narrower extraction field |
| `quality_flagged` | -- | 1 where the host window is data-quality flagged |
| `n_rep` | -- | covering repeat execution blocks |
| `dt_min_d` | d | shortest interval to a covering repeat |
| `dt_max_d` | d | longest interval to a covering repeat |
| `dt_from_unit_stamp` | -- | 1 where an interval is measured from the observing unit stamp rather than from the blocks' own |
| `T_pers` | -- | statistic a carrier persisting at the discovery flux would give at the predicted cell |
| `T_rep` | -- | statistic measured at that cell at the carried drift |
| `T_rep_is_upper_bound` | -- | 1 where T_rep is a window maximum and so bounds the cell from above |
| `sigma_excl` | -- | depth at which a carrier persisting at the discovery flux is excluded at the predicted cell; it tests a carrier whose stellar-frame frequency is unchanged between epochs |
| `disposition` | -- | disposition carried in the article's own crossing ledger |

## `candidates/molecular_line_matches.csv`

111 rows, 16 columns.

One row per transition of the dated catalogue QUERY, which is not the same list as the attribution mask: the query is deposited whole so that it can be inspected, and in_mask says which of its rows the mask holds.

The query is every transition of the named species that falls inside a searched island below the adopted upper-state energy cut, together with the hydrogen recombination series, taken from one query of the catalogues named in line_catalogue.

The MASK is the query less the species named in mask_exclusion_reason (SO): 96 of the 111 rows, over 11 species. Those 15 rows carry no attribution window, so their mask_ columns are empty, and they are excluded from the masked bandwidth of frequency_coverage.csv. The article reports a crossing nearest one of them as unattributed, with its offset printed beside it.

A crossing is attributed where its stellar-frame frequency lies within the adopted half-width of a transition WITH in_mask = 1. Applying the same rule to every row of the query attributes more crossings than the article reports, and code/line_mask.py measures both counts and names the difference. The identification of each individual crossing is in threshold_crossings.csv; this table is the list and the accounting, not the identification.

**Joins.** transition joins the masked_transition column of threshold_crossings.csv; nu_rest_GHz falls inside the island of frequency_coverage.csv whose edges bracket it.

| column | unit | description |
|---|---|---|
| `transition` | -- | transition label, as used in threshold_crossings.csv |
| `species` | -- | chemical species |
| `quantum_numbers` | -- | quantum numbers as the line catalogue gives them |
| `nu_rest_GHz` | GHz | rest frequency |
| `e_upper_K` | K | upper-state energy; zero for the recombination series, which the catalogues give without one |
| `a_ij_s` | 1/s | Einstein A coefficient where the catalogue gives one |
| `line_catalogue` | -- | the catalogue the entry was taken from |
| `in_mask` | -- | 1 where the attribution mask holds this transition; 0 where the query returned it and the mask leaves it out |
| `mask_exclusion_reason` | -- | why the mask leaves it out, where it does; empty where in_mask is 1 |
| `mask_half_width_kms` | km/s | adopted half-width of the attribution window about the transition; empty where in_mask is 0, which has no attribution window |
| `mask_nu_lo_GHz` | GHz | lower edge of that window |
| `mask_nu_hi_GHz` | GHz | upper edge of that window |
| `mask_width_GHz` | GHz | its width; summed over the searched islands and over the rows with in_mask = 1 this is the bandwidth the mask costs |
| `inside_searched_island` | -- | 1 where the rest frequency lies inside a searched island |
| `n_crossings_attributed` | -- | threshold crossings attributed to this transition |
| `n_crossings_coincident_not_attributed` | -- | crossings lying inside its window that are not attributed to it |

## `candidates/recurrence_tests.csv`

33 rows, 23 columns.

One row per threshold crossing carrying a repeat-observation measurement: what the covering repeat blocks say about it, read three ways.

sigma_excl_single_cell is the depth at which a carrier persisting at the discovery flux is excluded at one predicted cell. What it tests is a carrier whose stellar-frame frequency is unchanged between epochs; every crossing here has a fitted drift, which disfavours that model, so a null at this cell bears little on an accelerating carrier.

The separated columns repeat the reading over covering blocks that satisfy the confirmation criterion alone -- a different observing session more than a day away -- and the tol columns repeat it over a cell tolerance matched to the measured stellar-frame registration.

p_recovery_measured is the probability the criterion is satisfied by a carrier at the trigger amplitude, measured by injecting that carrier into the retained per-integration spectra of every covering repeat block. tested is 0 where that probability is too low for the reading to be a test, and such a crossing is reported as untested rather than excluded.

An empty field is a value withheld or inapplicable, not a zero: a crossing with no separated covering block has no separated reading.

**Joins.** (eb, nu_topo_GHz) joins threshold_crossings.csv, where star carries the same spelling.

| column | unit | description |
|---|---|---|
| `star` | -- | star designation, as in threshold_crossings.csv |
| `eb` | -- | ALMA execution block identifier of the discovery block |
| `nu_topo_GHz` | GHz | crossing frequency as delivered by the correlator |
| `nu_star_GHz` | GHz | the same frequency in the star rest frame |
| `n_rep` | -- | covering repeat execution blocks the published depth combines |
| `sigma_excl_single_cell` | -- | exclusion depth at the single predicted cell, for a carrier whose stellar-frame frequency is unchanged |
| `n_rep_separated` | -- | of the covering repeats, blocks in a different session more than a day from the discovery block |
| `T_pers_separated` | -- | statistic a persisting carrier would give at the predicted cell over those blocks alone |
| `T_rep_separated` | -- | statistic measured there, at the carried drift |
| `f5_separated` | -- | fraction of the discovery amplitude still excluded at the trigger over those blocks alone; values above 1 exclude nothing |
| `p_trigger_separated` | -- | recovery probability at the trigger amplitude over those blocks alone |
| `k_tol_channels` | channel | half-width of the matched registration tolerance, in channels of the finest covering block |
| `n_cells_tol` | -- | cells read over that tolerance |
| `threshold_tol` | -- | threshold at which those cells carry the single cell's own false-alarm probability |
| `f5_tol` | -- | fraction of the discovery amplitude excluded when the reading is the worst cell of that tolerance; values above 1 exclude nothing |
| `p_trigger_tol` | -- | recovery probability at the trigger amplitude at that threshold |
| `p_recovery_calculated` | -- | probability the criterion is satisfied by a carrier at the trigger amplitude, from the model of the reading |
| `p_recovery_measured` | -- | the same probability measured by injection into the covering repeat blocks |
| `p_recovery_lo` | -- | lower end of its 68 per cent interval |
| `p_recovery_hi` | -- | upper end of that interval |
| `n_realisations` | -- | realisations the measurement is formed from |
| `n_rep_blocks_injected` | -- | covering repeat blocks injected into |
| `tested` | -- | 1 where the measured recovery probability reaches the level required of a test, 0 where the crossing is reported as untested rather than excluded |

## `sensitivity/class_A_limits.csv`

405 rows, 31 columns.

One row per fine-channel spectral window: the sensitivity measurement for the windows that resolve a carrier in one channel.

The limit closes on the columns beside it. eirp_nominal_W times p90_mult_adopted, divided by eta_px_retained, eta_smear_adopted and eta_beam_retained, reproduces eirp_p90_W on every row to better than one part in a million, which is the printed precision of the factors.

The interval is not the same kind of quantity on every row. On a window with its own injection ladder it is that window measurement; on a transferred window it is the observed spread between the injected windows, so it is the same pair of factors on every such row and is not a bound measured in that window's own band and channelisation.

The limit is an EIRP at 90 per cent completeness for a carrier inside the searched drift range. It constrains nothing about a transmitter whose apparent acceleration exceeds that range.

**Joins.** (eb, nu_lo_GHz, nu_hi_GHz) joins spectral_windows.csv and control_field_statistics.csv; target_id joins stellar_sample.csv.

| column | unit | description |
|---|---|---|
| `star` | -- | star designation, as in stellar_sample.csv |
| `target_id` | -- | identifier the window was extracted under |
| `eb` | -- | ALMA execution block (ASDM) identifier |
| `project_code` | -- | its ALMA project code; cite as ADS/JAO.ALMA# followed by this value |
| `band` | -- | ALMA receiver band |
| `nu_lo_GHz` | GHz | lower edge of the spectral window, topocentric |
| `nu_hi_GHz` | GHz | upper edge of the spectral window, topocentric |
| `chan_width_Hz` | Hz | delivered channel width |
| `dist_pc` | pc | distance adopted for the star |
| `on_source_s` | s | on-source integration time at this position |
| `n_int` | -- | integrations retained at this position |
| `rms_mJy` | mJy | per-channel noise at the extraction position |
| `smin_mJy` | mJy | amplitude limit at the trigger: five times the noise divided by the primary-beam response |
| `pb_atten` | -- | primary-beam response at the star, between 0 and 1 |
| `theta_pb_arcsec` | arcsec | recorded primary-beam FWHM for this window |
| `drift_max_Hz_s` | Hz/s | largest drift rate searched |
| `n_drift_trials` | -- | drift trials searched |
| `eta_drift` | -- | fraction of the drift range over which a carrier is recovered at full amplitude |
| `c_response_smear` | -- | combined spectral-response and intra-channel smearing factor applied to the nominal power |
| `eirp_nominal_W` | W | EIRP of a carrier at the trigger amplitude, before any completeness or retention factor |
| `eirp_eff_total_W` | W | the same power with the spectral response and smearing applied |
| `p90_mult_adopted` | -- | adopted multiplier from the trigger amplitude to 90 per cent completeness, from completeness_calibration.csv |
| `eta_px_retained` | -- | fraction of the integrations retained after the phase-centre cut |
| `eta_smear_adopted` | -- | adopted smearing retention for this window |
| `eta_smear_basis` | -- | measured where the retention was measured on this window's own integrations, bounded where it is a bound |
| `eta_beam_retained` | -- | fraction of the applied primary-beam response that the observatory's documented beam retains, clamped at unity |
| `eirp_p90_W` | W | adopted 90 per cent completeness EIRP limit; equals eirp_nominal_W times p90_mult_adopted divided by the three retentions |
| `eirp_p90_lo_W` | W | lower end of its interval: for a window with its own injection ladder this is its own measurement, and for a transferred one it is the observed spread between the injected windows, the same pair of factors on every transferred row |
| `eirp_p90_hi_W` | W | upper end of that interval, on the same basis |
| `completeness_basis` | -- | injected where this window carries its own injection ladder, transferred otherwise |
| `trigger_whole_beam` | -- | 1 where the window holds a threshold crossing under the adopted statistic |

## `sensitivity/class_B_limits.csv`

1258 rows, 31 columns.

One row per coarse-channel spectral window: the same sensitivity measurement for the windows whose channel does not resolve a carrier.

The columns, the closure identity and the meaning of the interval are those of class_A_limits.csv.

The completeness multiplier of these windows is a blend and is declared as one in completeness_calibration.csv: no injected coarse window has a bright control ring, so the stratified rule cannot be applied to them.

**Joins.** (eb, nu_lo_GHz, nu_hi_GHz) joins spectral_windows.csv; target_id joins stellar_sample.csv.

| column | unit | description |
|---|---|---|
| `star` | -- | star designation, as in stellar_sample.csv |
| `target_id` | -- | identifier the window was extracted under |
| `eb` | -- | ALMA execution block (ASDM) identifier |
| `project_code` | -- | its ALMA project code; cite as ADS/JAO.ALMA# followed by this value |
| `band` | -- | ALMA receiver band |
| `nu_lo_GHz` | GHz | lower edge of the spectral window, topocentric |
| `nu_hi_GHz` | GHz | upper edge of the spectral window, topocentric |
| `chan_width_Hz` | Hz | delivered channel width |
| `dist_pc` | pc | distance adopted for the star |
| `on_source_s` | s | on-source integration time at this position |
| `n_int` | -- | integrations retained at this position |
| `rms_mJy` | mJy | per-channel noise at the extraction position |
| `smin_mJy` | mJy | amplitude limit at the trigger: five times the noise divided by the primary-beam response |
| `pb_atten` | -- | primary-beam response at the star, between 0 and 1 |
| `theta_pb_arcsec` | arcsec | recorded primary-beam FWHM for this window |
| `drift_max_Hz_s` | Hz/s | largest drift rate searched |
| `n_drift_trials` | -- | drift trials searched |
| `eta_drift` | -- | fraction of the drift range over which a carrier is recovered at full amplitude |
| `c_response_smear` | -- | combined spectral-response and intra-channel smearing factor applied to the nominal power |
| `eirp_nominal_W` | W | EIRP of a carrier at the trigger amplitude, before any completeness or retention factor |
| `eirp_eff_total_W` | W | the same power with the spectral response and smearing applied |
| `p90_mult_adopted` | -- | adopted multiplier from the trigger amplitude to 90 per cent completeness, from completeness_calibration.csv |
| `eta_px_retained` | -- | fraction of the integrations retained after the phase-centre cut |
| `eta_smear_adopted` | -- | adopted smearing retention for this window |
| `eta_smear_basis` | -- | measured where the retention was measured on this window's own integrations, bounded where it is a bound |
| `eta_beam_retained` | -- | fraction of the applied primary-beam response that the observatory's documented beam retains, clamped at unity |
| `eirp_p90_W` | W | adopted 90 per cent completeness EIRP limit; equals eirp_nominal_W times p90_mult_adopted divided by the three retentions |
| `eirp_p90_lo_W` | W | lower end of its interval: for a window with its own injection ladder this is its own measurement, and for a transferred one it is the observed spread between the injected windows, the same pair of factors on every transferred row |
| `eirp_p90_hi_W` | W | upper end of that interval, on the same basis |
| `completeness_basis` | -- | injected where this window carries its own injection ladder, transferred otherwise |
| `trigger_whole_beam` | -- | 1 where the window holds a threshold crossing under the adopted statistic |

## `sensitivity/injection_recovery.csv`

4032 rows, 24 columns.

One row per injection trial: a carrier of known amplitude, channel and drift rate put into the retained per-integration spectra of a real window and read back by the unchanged search path.

These trials are PART of the campaign the completeness transfer is calibrated on, not all of it: they cover 28 of the 49 directly injected Class A windows. The trials span the configurations of the survey -- both arrays, four receiver bands, channel widths from the finest to the coarsest -- and at each amplitude the recovered fraction over the realisations is the completeness at that amplitude.

★ THE 90 PER CENT POINT OF THESE TRIALS IS NOT THE PUBLISHED MULTIPLIER, and reading one against the other is the one mistake this table invites. The article publishes 3.03 P_trig, which factorises as x2.29 for the channel response and x1.325 for the margin a peak channel needs above the nominal trigger. The channel response is ALREADY INSIDE these trials -- each carrier is deposited at a random sub-channel phase through the correlator response, whose central channel receives 0.4375 of it on average -- so a curve formed from these rows measures the MARGIN TERM ALONE and lands near x1.2 of the trigger. code/injection_recovery.py prints the arithmetic beside the number.

What is measured is the reading: the de-drifting, the drift trials, the control normalisation and the threshold. It is not the step from calibrated visibilities to a spectrum, which is upstream of the injection point and is not tested here.

detected is the search's own verdict, which requires the recovered statistic to reach the trigger; drift_matched records separately whether the recovered drift trial was the injected one, and a trial can be detected without it.

**Joins.** (eb, window_nu_lo_GHz, window_nu_hi_GHz) joins the sensitivity tables and spectral_windows.csv. One window is shared by two extraction positions; its rows carry the window and leave target_id and star empty rather than assign the trial to one of them.

| column | unit | description |
|---|---|---|
| `eb` | -- | ALMA execution block the injected window belongs to |
| `target_id` | -- | identifier of the extraction position, empty where one window serves two |
| `star` | -- | its star designation, empty on the same rows |
| `window_nu_lo_GHz` | GHz | lower edge of the injected window |
| `window_nu_hi_GHz` | GHz | upper edge of the injected window |
| `band` | -- | ALMA receiver band |
| `array` | -- | 12m for the main array, ACA for the compact array |
| `chan_width_Hz` | Hz | delivered channel width of the window |
| `n_int` | -- | integrations the injection was made into |
| `n_chan` | -- | channels in the window |
| `span_s` | s | time span of those integrations |
| `n_drift_trials` | -- | drift trials the reading searched |
| `theta_pb_arcsec` | arcsec | recorded primary-beam FWHM of the window |
| `amp_sigma` | -- | injected amplitude in units of the per-channel noise |
| `realisation` | -- | realisation index at that amplitude; channel and drift are redrawn for each |
| `inj_flux_Jy` | Jy | injected flux density |
| `inj_channel` | -- | channel the carrier was injected at |
| `inj_drift_Hz_s` | Hz/s | drift rate it was injected with |
| `rec_statistic` | -- | de-drifted search statistic recovered at the injected cell |
| `rec_channel` | -- | channel it was recovered at |
| `rec_drift_Hz_s` | Hz/s | drift rate it was recovered at |
| `window_max_statistic` | -- | largest statistic anywhere in the window on that trial |
| `drift_matched` | -- | 1 where the recovered drift trial is the injected one |
| `detected` | -- | 1 where the trial satisfies the search's own detection condition |

## `sensitivity/completeness_calibration.csv`

10 rows, 11 columns.

How the completeness of the survey was measured, and how it was carried to the windows that were not tested directly.

Only a minority of windows carry their own injection ladder; every other window takes a multiplier calibrated on those that do, and the table records which windows were tested, the rule that defines each stratum, the measured multiplier and its interval.

The interval on a transferred limit is one pair of factors over every transferred row, because it is the dispersion observed between the injected windows. It is not a bound measured in any one window's own band and channelisation, and it does not describe a window that lies in a configuration no injection visited.

One stratum carries a bound rather than a measurement, and says so: in windows with a bright control position the carrier is recovered in every trial at the positive control, so the multiplier is bounded from above and not determined.

**Joins.** completeness_basis and search_class in the sensitivity tables select the windows each row applies to; the trials themselves are in injection_recovery.csv.

| column | unit | description |
|---|---|---|
| `stratum` | -- | the set of windows this row calibrates |
| `selection_rule` | -- | the rule that defines that set, in terms of the deposited columns |
| `quantity` | -- | what is being given |
| `value` | -- | its value |
| `lo` | -- | lower end of its interval where it has one |
| `hi` | -- | upper end of its interval where it has one |
| `n_catalogue_windows` | -- | windows in the stratum |
| `n_injected_windows` | -- | of those, windows carrying their own injection ladder |
| `n_injected_windows_deposited` | -- | of those, windows whose individual trials are deposited in injection_recovery.csv; the rest were injected but their per-trial rows are not released, so a curve formed from the deposited rows is formed over this subset |
| `applies_to` | -- | the windows the value is applied to |
| `note` | -- | the qualification that travels with the value; where a value is a bound or a blend rather than a measurement, this column says so |

## `statistics/control_field_statistics.csv`

405 rows, 24 columns.

One row per window with a control ensemble: the control-field measurement the chance comparison is built from.

The control positions lie in an annulus placed in each window's own synthesised and primary beams, so that none sits on the star and all lie inside the field the statistic is defined over. ring_r_in_arcsec and ring_r_out_arcsec are that annulus for the window.

p_trig_ctrl is the window's own probability that a position in its field reaches the trigger, measured as the fraction of its control positions that do. The sum of that probability over the fine-channel windows, each reduced by the share the attribution mask takes and by the atmospheric factor, is the chance expectation of null_distribution_tests.csv.

p_rank is the rank of the stellar statistic among the control positions of the same window, formed with the add-one correction. It is a diagnostic and not a significance test.

The control channels are transformed to the same stellar rest frame as the star's own reading before the attribution mask is applied to them, so the two sides of the comparison are screened in one frame.

**Joins.** (eb, nu_lo_GHz, nu_hi_GHz) joins spectral_windows.csv and the sensitivity tables.

| column | unit | description |
|---|---|---|
| `star` | -- | star designation |
| `target_id` | -- | identifier the window was extracted under |
| `eb` | -- | ALMA execution block identifier |
| `project_code` | -- | its ALMA project code |
| `nu_lo_GHz` | GHz | lower edge of the window |
| `nu_hi_GHz` | GHz | upper edge of the window |
| `search_class` | -- | A fine or B coarse |
| `rms_mJy` | mJy | per-channel noise at the stellar position |
| `theta_pb_arcsec` | arcsec | recorded primary-beam FWHM |
| `ring_r_in_arcsec` | arcsec | inner radius of the control annulus |
| `ring_r_out_arcsec` | arcsec | outer radius of the control annulus |
| `ring_centre` | -- | what the annulus is centred on |
| `ring_seed` | -- | seed the control positions were drawn with, so the ensemble is reproducible |
| `n_ctrl` | -- | control positions in the ensemble |
| `T_star` | -- | de-drifted search statistic at the stellar position |
| `T_ctrl_max` | -- | largest statistic among the control positions |
| `n_ctrl_ge_star` | -- | control positions whose statistic reaches the stellar one |
| `p_rank` | -- | rank of the stellar statistic among them, with the add-one correction; a diagnostic and not a significance test |
| `n_ctrl_trig` | -- | control positions reaching the trigger |
| `p_trig_ctrl` | -- | the window's own probability that a position in its field reaches the trigger |
| `mask_attr_share` | -- | share of its control exceedances the attribution mask takes, in the star rest frame |
| `telluric_factor` | -- | factor by which the remaining exceedances are reduced by the atmospheric screen |
| `n_search_cells` | -- | search cells in the window |
| `n_ind_cells` | -- | independent cells after the correlation between neighbouring drift trials is accounted for |

## `statistics/above_threshold_cells.csv`

7 rows, 6 columns.

The number of search cells above each level, counted at the stellar positions and at the control positions, from well below the trigger up to it.

The ratio of the two, normalised by the number of positions on each side, is the step from a control position rate to a stellar position rate. The article adopts the control rate -- the smaller of the two and the more demanding of the count under test -- and carries this step only as a sensitivity test; these are the counts that step is formed from.

The ratio is empty at the highest level, where neither side holds a cell. A ratio formed from a handful of cells at the top of the ladder carries the uncertainty of those counts and nothing here hides it: the counts are given so that uncertainty can be formed.

These counts are measured over the fine-channel windows of the released extent at the time the ladder was built, which is the number in n_windows.

The adopted band is one pair of these rungs differenced. The step quoted in null_distribution_tests.csv is formed over 4 <= T < 5, and its two cell counts are this table's 4 rows less its 5 rows on each side; its ratio is the same arithmetic. The ratio rises monotonically toward the trigger, which is why the band adopted is the one adjacent to it and not a wider one further below: a wider band measures the quantity where it is smaller.

**Joins.** the levels are in units of the per-channel noise, the same units as the T_star columns; the step this table supports is in null_distribution_tests.csv.

| column | unit | description |
|---|---|---|
| `threshold_sigma` | -- | level, in units of the per-channel noise |
| `n_star_cells` | -- | search cells above that level at the stellar positions |
| `n_control_cells` | -- | search cells above it at the control positions, pooled over the ensemble |
| `ratio` | -- | stellar rate divided by control rate at that level, normalised by the number of positions on each side; empty where neither side holds a cell |
| `n_windows` | -- | fine-channel windows the counts are formed over |
| `basis` | -- | what is counted |

## `statistics/null_distribution_tests.csv`

39 rows, 6 columns.

The chance comparison and the tests around it, term by term: what was expected, what was observed, and on what assumptions.

The comparison is made twice, over two fields, and both readings are here. The adopted reading is the whole primary beam, which is the field the statistic is defined over; the other reads both sides over the narrower extraction field, which drops the integrations whose pointing falls outside it. Neither is a reading of the other.

value is the figure the article prints, at the precision it prints it. exact is the figure the record carries before rounding, where there is one. A quantity the article does not print has an empty value and an exact figure.

The expectation can be rebuilt from control_field_statistics.csv: sum each fine-channel window p_trig_ctrl, multiply each by one minus its mask_attr_share and by its telluric_factor. The interval on it cannot, because it folds in the transfer band of above_threshold_cells.csv and the resampling of the attributed share.

What the comparison establishes is consistency with the expectation these fields' own control positions set, under the assumptions recorded here. It does not establish that the unattributed crossings are noise.

**Joins.** the per-window terms are in control_field_statistics.csv; the cell counts behind the sub-trigger step are in above_threshold_cells.csv, and its band_lo and band_hi rows name the two rungs of that table they are differenced from, so the two files quote one band and not two; the crossings counted on the observed side are the rows of threshold_crossings.csv with attributed = 0.

| column | unit | description |
|---|---|---|
| `test` | -- | the test or quantity group the row belongs to |
| `reading` | -- | the field the quantity is read over, or the block set it is measured on |
| `quantity` | -- | what is given |
| `value` | -- | the figure the article prints, at the precision it prints it; empty where the article does not print it |
| `exact` | -- | the figure the analysis record carries before rounding, where there is one |
| `note` | -- | what the quantity is and the assumption it rests on |

## `catalogues/count_accounting.csv`

21 rows, 5 columns.

The master accounting of the survey: one row per published count, with the sub-counts each one partitions into.

Every count in the article appears here, and so do the itemised rows the article does not have room for; in_article records which is which.

The indented row numbers are a partition: the sub-rows of a row sum to it. Where a count appears under two parents the note says so, because a count that is reached by two routes and does not agree is a defect and not a nuance.

**Joins.** the crossing counts are the rows of threshold_crossings.csv under the selections the notes give; the window counts are those of spectral_windows.csv.

| column | unit | description |
|---|---|---|
| `row` | -- | row number; the sub-rows of a row partition it |
| `count` | -- | what is counted |
| `value` | -- | the published value |
| `what_it_counts` | -- | the qualification that travels with the count |
| `in_article` | -- | 1 where the article prints this row, 0 where it is itemisation the article has no room for |

## `figures/figure_data.csv`

7 rows, 14 columns.

The numerical data behind the figures that is in no other table here.

Most of the figures are drawn from columns deposited in this archive, and for those figure_sources.csv names the file and the columns rather than copying the numbers, so that a figure and the table behind it cannot disagree.

What is left is the external material the context figure compares the survey against: the deepest limit each published survey reports, the threshold it was set at, and the factor that puts it on a common threshold with this one. The note column gives the source of each value in the words of the paper it is taken from.

A rescaled limit is not that survey published number and is not attributable to its authors as such; it is this work rescaling of it, and the factor applied is beside it.

**Joins.** figure_sources.csv names, for every figure, the deposited file and columns it is drawn from.

| column | unit | description |
|---|---|---|
| `figure` | -- | the figure, named by what it shows rather than by a number, since numbering is a property of the typeset article |
| `panel` | -- | panel within it |
| `series` | -- | the series the point belongs to |
| `point` | -- | point index within the series |
| `x` | -- | abscissa |
| `x_quantity` | -- | what the abscissa is |
| `x_unit` | -- | its unit |
| `y` | -- | ordinate |
| `y_quantity` | -- | what the ordinate is |
| `y_unit` | -- | its unit |
| `y_rescaled` | -- | the ordinate rescaled to a common threshold, where the rescaling applies |
| `y_rescaled_quantity` | -- | what that rescaling is |
| `scale_factor` | -- | the factor applied |
| `note` | -- | the source of the value, quoted from the work it is taken from |

## `figures/figure_sources.csv`

11 rows, 5 columns.

One row per figure panel of the article: what it plots and which deposited columns it is plotted from.

Figures are named by what they show. A figure number is a property of the typeset article and would not survive a change of layout, so it is not used as an identifier here.

A panel whose data is not in any other deposited table has its series in figure_data.csv, and this table points there as well.

**Joins.** the file column names files in this archive and the columns column names their columns.

| column | unit | description |
|---|---|---|
| `figure` | -- | the figure, named by what it shows |
| `panel` | -- | panel within it, empty where there is one |
| `shows` | -- | what is plotted |
| `file` | -- | the deposited files the panel is drawn from, separated by semicolons |
| `columns` | -- | the columns within them, separated by semicolons |
