# v3.43 archive-and-code verification log (run e4cac251, "v343-revision")

Baseline: `technosignatures_20pc_v3.43.tex` seeded byte-identical from v3.42
(29 pp: main 21.03, back matter 0.90, appendices 6.70, bibliography 0.33;
all gates zero). Reports: `/shared/ASTRA/reviews/v3.43_referee{1_radio,
2_radiostars,3_general}.md`; constraints `STANDING_RULES.md`.
The v3.42 notes are preserved verbatim in `BUILD_NOTES_v3.42.md`.

## Verification log (running; written as work proceeds)

Every item below was checked against the released code on the processing host
or against the shipped catalogue before any text was touched. "CONFIRMED"
means I reproduced the referee's claim; "CORRECTED" means the referee is
right that the text is wrong but their replacement number differs from mine;
"NOT REPRODUCED" means the claim does not hold.

### R1-M1 (statistic and noise estimator) - CONFIRMED, in full
`/data/SETI/bin/seti_drift_search_generic.py:357-386`:
```
I -= spectral_baseline(np.nan_to_num(I), MEDWIN)     # frequency-axis, per int
med   = np.nanmedian(I[:, probe, :], axis=1)         # median ACROSS positions
mad   = np.nanmedian(np.abs(I[:, probe, :] - med[:, None, :]), axis=1)
sigma = 1.4826 * mad                                 # (n_int, n_chan)
invvar = 1/sigma**2 ;  X = I * invvar
```
and `one_drift()` forms `num = sum_t X_t(shifted)`, `den = sum_t invvar_t`,
`snr = num/sqrt(den)`. So sigma is **per integration and per channel**,
estimated from the dispersion **across the 512 control probes** and shared by
star and controls: global in position, local in frequency, the exact inverse
of the manuscript's sentence. The statistic is an inverse-variance-weighted
de-drifted stack, not amplitude/MAD. `med` is used only to centre the MAD and
is **not** subtracted from the numerator.

### R1-M5 (baseline filter) - CONFIRMED, and W computed for all 431 windows
`spectral_baseline()` is a **block median with linear interpolation**, not a
running median: `nb = max(2, n // 65)` blocks, medians at block centres,
linear interpolation between them. From `pipeline_peakfreq_v342.json`'s own
per-window trimmed channel count: W = n/nb is 65.0-73.7 channels for the
windows with more than 130 usable channels, and n/2 = 30-59 channels for the
coarse TDM windows (n = 60-118), whose block count collapses to 2. So the
manuscript's "a single fixed channel count for all 431 windows" is true for
the fine class and false for the coarse one. Frequency ceilings: ~32 MHz at
488 kHz channelisation, ~0.9 GHz at 15.625 MHz.

### R1-M6 (smearing census) - CONFIRMED exactly
`per_target_results_v3.43.csv`: **nine** windows at eta_smear < 0.99, not
three; five at 0.574-0.606 (penalties 1.65-1.74), all 15.26 kHz Band 6.

### R1-M7 (primary beam) - CONFIRMED, with one number of the referee's not
reproduced. smin/(5 rms) over the 431 retained rows: median 1.00004, 90th
percentile **1.0180** (the paper's 1.012 does not reproduce), **41** rows
above 1.02, largest **j1256-1257 B7 at 1.8109**, offset 8.13 arcsec =
0.463 theta_PB(1.22 lambda/D) = 0.50 FWHM(1.13). Sirius B (alf CMa B) spans
**1.036-1.186**, i.e. 3.6-18.6 per cent, at 0.11-0.25 theta_PB; the paper's
"3.6-16 per cent" understates the top of the range, and the referee's
"4.6 per cent" lower end does not reproduce from the released catalogue.
The correction uses theta_PB = 1.22 lambda/12 m (`seti_drift_search_generic.py:520-527`),
i.e. the Airy first-null coefficient in the place of the FWHM, confirmed.

### R1-M8 (beta Pic empirical significance) - CONFIRMED
Two control maxima exceed 20.31 (HD 48370 B6 26.826, its 13CO window 20.369),
so add-one p = 3/432 = 0.0069, not < 0.0044. 15.17 is the fifth largest
control maximum, not the largest. Symmetric T_star = 14.654 (B3) and 11.681
(B6); five control maxima are at or above 14.654, add-one p = 6/432 = 0.0139.

### R2-1 (CP-72 2713 line query) - CONFIRMED and extended
Splatalogue, transitions observed in space, over 344.10-344.45 GHz, pushed
through the paper's own frame chain (BC = -15.31, v_sys = +7.985, LSR term):
SO 3Sigma v=0 8(8)-7(7) at 344.310792 GHz -> -12.4 stellar / -12.9 LSR;
U-344288.4 -> +7.1 / +6.6; 34SO2 10(4,6)-10(3,7) (E_u = 88.5 K) -> +44.5 /
+44.1. Three catalogued transitions inside the +/-50 km/s tube in both frames.
CO(3-2) reproduces the paper's -1323.2 / -1300. H13CN(4-3) is -194.95 km/s
from the **superseded window centre** and -928.9 km/s from the real crossing.
**Beyond the referee:** the same query at the superseded 345.1152 GHz returns
CH3OCH3 at -12.1, SO2 5(5,1)-6(4,2) at -29.3 and 34SO2 at -46.4 km/s
topocentric, so "closest entry H13CN at -195 km/s" was wrong at the old
frequency too. And repeating the query at each of the 20 crossing
frequencies returns at least one catalogued transition within 60 km/s
(topocentric) for **19 of the 20**, median 3 transitions. A bare
catalogue-proximity argument has no discriminating power at these
frequencies; the disposition has to be physical.

### R2-3 (ACA) - CONFIRMED and much larger than stated
ALMA obscore `antenna_arrays` for all 102 execution blocks: **38 of 102 EBs,
and 141 of the 431 windows (33 per cent), are ACA 7 m**, not "several rows".
theta_PB is 1.22 lambda/12 m throughout, so for those windows the annulus
sits at 0.082-0.455 of the true 7 m primary beam and the primary-beam gains
are 0.98 falling to 0.56, not 0.95 to 0.19. **130 of 431 windows have
r_in below the synthesised beam.** Of the four stage-1 flags only **one**
(HD 48370 B6, 9 x 7 m, 5.53 arcsec beam against r_in = 3.81 arcsec) is ACA;
beta Pic B3, beta Pic B6 and CP-72 2713 B7 are all 12 m. The referee's
"two of the four flags are ACA" is wrong; their identification of
HD 48370 B6/B8, CP-72 2713 B6 and the beta Pic third epoch is right.
N_eff from pi(r_out^2 - r_in^2)/(1.133 theta_beam^2) spans 39 to 1.5e5 with
median 1032 (ACA median 53, 12 m median 2086), so the blanket 30-43 is the
compact/ACA case only.

### R1-M11 / R2-M6 (Hanning state) - HARVESTED, claim of unavailability retired
obscore `frequency_support` gives the archive's effective spectral resolution
per window. Against the measurement sets' own channel separation the ratio is
**exactly 2.00 in 403 of the 431 windows** - in both correlator modes,
including 309 of the 313 coarse TDM windows - which is ALMA's default online
Hanning smoothing. 27 windows report 1.156 and one 0.993, the signature of
online channel averaging, where the peak-channel loss is smaller. So the
blanket factor is correct and is now evidenced, not assumed.

### R2-2 (second execution block) - CONFIRMED, and the cause is in the log
ALMA obscore does not expose it, but the datalink service for member OUS
uid://A001/X2d20/X2e25 lists **two** raw ASDM progenitors,
`uid___A002_Xff0235_X4a6d` (49.33 GB, searched) and
`uid___A002_Xff0235_X502d` (49.46 GB, **not** searched). The survey's own
calibration log records exactly why:
```
[calibrate_generic] 2 EB(s) for uid://A001/X2d20/X2e25
[calibrate_generic]   SKIPPING ..._X502d.asdm.sdm.tar (49.5 GB): would exceed
                      this target's 85 GB download budget (49.3 GB queued)
```
**Beyond the referee:** running the same datalink audit over all 102 searched
member OUSs shows they contain **448** public execution blocks between them,
of which 102 were searched. 75 of the 102 OUSs hold more than one EB; 304 of
the 431 windows (71 per cent), covering 62 of the 88 stars, sit in an OUS
that holds at least one further unsearched block. Two code-level causes,
both deliberate: `calibrate_generic.py`'s `SETI_MAX_EBS_PER_TARGET = 3` plus
the 85 GB download budget, and `select_finest_spw.py`, which deduplicates
spectral windows **by spw_id across execution blocks**, so repeated epochs of
one correlator setup are never searched independently. The survey is
archive-complete in targets and tunings, not in epochs or integration time.

