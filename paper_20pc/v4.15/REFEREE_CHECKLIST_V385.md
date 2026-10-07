# v3.85 referee checklist — working state (update as each item closes)

Rule from Glenn: one item at a time, do not start the next until the previous is fixed.

## Referee 1
- [x] R1-5  block-level bootstrap null (`blockboot_v385.py`): 404 blocks, mean 3.5,
      95% 0-7, naive Poisson 3.1, P(>=2)=0.87
- [x] R1-7  molecular mask treated as a post-search *classification* exclusion:
      searched 118.1 GHz, exclusion domain 113.3 GHz; said in survey table
      (footnote b), conclusions and abstract
- [x] R1-8  C(P, f_dwell) contour figure (`make_fig_dwell2d.py`)
- [x] R1-1 DONE: all 13 events tested, Fig. 7 and Table 9 extended, test named as step (iv) of the candidate logic in 4.2
      candidate decision tree (Fig. 3 and 4.2).  9 blocks recalibrating on host
      (`/tmp/vis_recal3.sh`, log `/data/SETI/vistest_recal3.log`)
- [x] R1-3  `drift_strata_v385.py` + `tab_driftstrata_v385.tex` (round36).
      The campaign already had ZERO zero-drift trials (9-10344 Hz/s); it was
      only ever REPORTED pooled.  Resolved by drift tercile of each window's
      own ceiling: P90 6.13 / 6.51 / 5.92 sigma, spread 10 per cent, no trend,
      outer third not the worst.  92 per cent of detections return the
      injected drift TRIAL, median error 0.00 grid steps, 0.5 at p90.
      Sub-channel phase stratified in the response campaign (5 levels, 400
      trials, x2.02-x2.69) -- the one axis that does matter.
- [x] R1-9  new `make_fig_accel2d.py` -> two-panel `drift_acceleration.pdf`
      (acceleration vs frequency, and the same boundary in Hz/s where it is
      NOT flat), round37.  Old `fig_drift` in make_figures_v328.py RETIRED so
      only one generator writes the file.
      **The grid is built at constant ACCELERATION, 3.598 m/s^2, = 1.4 kHz/s
      at 115 GHz and 10.5 kHz/s at 872 GHz.  It clears Earth's rotation by
      x106.  Exactly two ceiling values exist; the wider one is TRAPPIST-1's
      5 windows alone, and it still stops 0.01 per cent short of planet b.**
- [x] R1-15 `p90_budget_v385.py` -> `tab_p90budget_v385.tex` (round38) +
      a new subsection "How well is P90 known?".  Independent terms combine
      to +-8 per cent (flux scale 7.5 band-weighted / 20 worst band; distance
      0.2; injection MC 2.0 from 400 bootstraps; pointing 1.9).  Sub-channel
      phase (-12/+17) and window-to-window spread (-52/+35) listed but NOT
      folded in -- they are not errors, and folding them would double-count
      against the catalogue's per-window bracket.
- [x] R1-16 catalogue now 50 columns: adds `eirp_p90_W/_lo_W/_hi_W` and
      `p_rank_local` + `stage1_flag_local`.  New shared `localnorm_core.py`
      (the catalogue writer runs before the analysis generator).  New
      `reproduce_from_catalogue_v385.py` opens ONLY the CSV and re-derives
      **26 headline numbers**, 0 fail; wired into make_all.sh so the build
      fails if the released file stops being sufficient.
      **BUG FOUND: I declared the new headers before `p_rank_addone` but
      wrote the values after it, shifting three columns.  The only symptom
      was `stage1_flag_local` all False.  v342_calc now re-reads its own
      output and asserts both flag columns are booleans and non-empty.**
- [x] R1-struct DONE (see entry below)
- [x] R1-abstract "N spectral windows pass the detection threshold and the
      spatial-outlier screen"; P90 now qualified as "an unresolved carrier
      drifting within the searched range"
- [x] R1-conclusions rewritten as exactly four numbered numerical statements
      (searched / found / excluded / what the sample can speak for); the
      non-numerical "what the archive teaches" paragraph folded into 4

## Referee 2
- [x] R2-1  local (radius-corrected) normalisation over the FULL sample
      (`localnorm_all_v385.py`): 13 global / 10 local / 9 both; lost 4 gained 1
- [x] R2-2  window-to-window completeness scatter: abstract + 6.1 quote
      x0.48-x1.35 (P90) and x0.64-x1.13 (P50) from the EXISTING measured
      `StratTransfer*`; catalogue gains `eirp_p90_W`, `eirp_p90_lo_W`,
      `eirp_p90_hi_W` (48 cols).  New shared module `inject_curve.py` removes
      a forward dependency (v342_calc runs long before v358_inject) and
      v358_inject cross-asserts against it.
      **BUG FOUND: every quoted P90 was scaling the trigger by the ROUNDED
      macro StratPNinety/5 = 1.22 instead of 1.2275; PNinetyWinBestA
      6.2e13 -> 6.3e13.  Caught only by asserting the catalogue column
      reproduces the headline macro.**
- [x] polarisation caveat: named as a blind spot in 5.x "not excluded"
      and attached to the quoted limit in the conclusions
- [x] "magic frequency" blindness stated plainly: none of 1420 MHz, its
      multiples, the water hole or pi/e multiples falls in an ALMA band, so
      a deliberately placed beacon there is outside the experiment
- [x] aphoristic meta-commentary trimmed (7 instances): "what the method
      looks like when it works", "we state it plainly", "worth stating
      plainly before the evidence", "worth saying what the second one is
      worth", "Nothing survives", the blind-spot lead-in, the M-dwarf
      peroration
- [x] Arecibo comparator in the abstract
- [x] 5.3.6 condensed 9,800 -> 4,871 chars by MOVING the beta Pic
      recurrence validation (4,686 chars) to the beta Pic positive-control
      subsection where it belongs.  Nothing deleted; each subsection is now
      about one thing.
- [x] "how to read a limit" moved to the end of the Introduction, rewritten
      to name the three powers in one sentence; methodology keeps the full
      definitions
- [x] Fig. 1: literature points enlarged with a heavy black edge and a
      white halo; legend rebuilt from proxies and split into "This survey"
      / "Other programmes"; moved to upper left with new y headroom, which
      also revealed that the old lower-right legend was SITTING ON the
      Enriquez and Margot points
- [x] glossary panel: tab:quantities relabelled "Glossary", moved to the
      Introduction with it, and extended with stage-1, hold-out, drift and
      add-one rank
- [x] abstract block arithmetic (404 + 77 + 3 = 484)
- [x] HD 14055 verdict reworded: "displaced from the stellar position
      rather than absent"
- [x] Fig. 9 caption spells out the chain: 5sigma trigger x2.29 response
      x1.23 campaign = x2.81, new macro PNinetyInTrig from the figure's own
      generator (round40)
- [x] 4.5 now states 197 of 403 Class A windows (49 per cent) differ from
      the demonstration configuration on at most one axis -- "about half and
      not most" -- in the MAIN text, not only the appendix
- [x] 6.3 names the five searched M dwarfs with a claimed habitable-zone
      planet (Proxima, TRAPPIST-1, LHS 1140, GJ 581, HN Lib) against the
      local M-dwarf census, with the model-dependence caveat
- [x] drift-rate units flagged in the glossary: Hz/s, kHz/s and the
      band-independent Hz/s/GHz, with 1 Hz/s/GHz = 1e-9 /s = 0.30 m/s^2

## Release
- [x] gates: 41 pp, 0 errors / undef / multdef / overfull / Type 3,
      1035 macros 0 unused, abstract 1878/1920, clean regen 81/81
      byte-identical, arXiv set 70 items, audit 51/0, catalogue
      reproduction 41 quantities
- [x] BUILD_NOTES_v385.md, VPR_DISPOSITION.md, CHANGELOG, AUTHOR_ACTIONS.md
- [x] push

## Glenn's instruction, received 2026-09-20 ~19:38 UTC
After the build: **five rounds of self virtual peer review**, correcting after
each round before starting the next, then **one single push** to GitHub with
everything in it.

- [x] VPR round 1 — 34 MAJOR verified; 22 real and fixed, 6 reviewer errors recorded. See VPR_DISPOSITION.md
- [x] VPR round 2 — 18 MAJOR verified; 20 real and fixed. M1 (all-event drift-following fit) running
- [x] VPR round 3 — 27 MAJOR verified; the star-count bug (94 -> 90) and M1 both closed
- [x] VPR round 4 — 27 MAJOR verified; the star count finished properly (90/82/113) and literalsweep.py added
- [x] VPR round 5 — 25 must-fix items; all the MAJOR ones closed
- [x] single push — `47f6dee491f8`, 2026-09-21T12:01:47Z, 388 files
