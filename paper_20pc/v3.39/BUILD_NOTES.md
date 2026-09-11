# BUILD_NOTES — v3.39 (round 9)

Baseline: copy of v3.38 (tex + figures + survey_numbers* + scripts + frozen
export), version stamp bumped first, per the standing versioning rule.
v3.38 and all earlier folders untouched. Round 9 = both round-9 referee
reports (Report 3: R3-1–R3-11 + 15 required changes + abstract/Discussion/
Conclusions/Introduction prescriptions; Report 4: A1–A7 + B + C1–C5);
full mapping in `REFEREE_RESPONSE_ROUND9.md`. Round-8 letter written late
and also filed here (`REFEREE_RESPONSE_ROUND8.md`; v3.38's own folder
carries no round-8 letter — its BUILD_NOTES is a stale copy of v3.37's,
left untouched per the versioning rule).

## Result

- `pdflatex` ×2: **0 errors, 0 undefined references/citations, exactly
  38 pages, 0 overfull boxes** (v3.38's single 4.07 pt page-1 vbox —
  abstract growth — cleared by the round-9 abstract restructure; the
  round-8 Conclusions reflow cleared a later page-24 vbox).
- The four `Font shape T1/cmr/m/scit undefined` warnings only (benign,
  pre-existing).
- 23 tables, 14 figures; appendices A–Q unchanged in count, compressed in
  place (E one paragraph; P ~12 lines recovered; M/O tightened).
- 6 author TODO/ACTION markers intact — author input, do not resolve.
- No online-only material anywhere (standing user rule); C1 answered by
  in-place compression.

## Round-9 computation lane

- `round9_calc.py` → `survey_numbers_round9.tex` from
  `frozen_export_v3.31.json` (same freeze as rounds 5–8). Macro names
  letter-only (`CpTwo*`, `Conc*`, `Mask*`, `SearchedUnionGHz`).
  - `\Conc*` — window concentration in β Pic (15) / AU Mic (12) /
    TRAPPIST-1 (12): 39 windows, 9.0 per cent, 3 systems (R4-B §3).
  - `\MaskUnion*`/`\SearchedUnionGHz` — mask framing on the
    unique-frequency union: 93.1 − 4.96 = 88.2 GHz searched, 5.3 per cent
    deliberately excluded; gross 22.20/700.8 GHz = 3.2 per cent
    (R3-8). **Includes the mask-inconsistency correction:** the old
    typed 87.0 GHz / 5.7 per cent prose (an early `\EffBandGHz` renewal)
    disagreed with the generated tab:maskband arithmetic; `\EffBandGHz`
    is renewed to 88.2 and the prose now uses generated macros only.
  - `\CpTwo*` — CP−72 2713 Band-7 feature rows for tab:cp72props
    (frequency, T* 5.81, ring max 5.68, margin 0.13, line offset
    −1326 km/s, 129-trial drift grid, bandwidth, on-source s) (R3-3).

## Figures regenerated (system python3 — matplotlib 3.10.8)

1. **Fig 1 `eirp_context.pdf`** — full two-panel redesign (R3-7 Option A):
   (a) total-power trigger threshold vs distance; (b) native channel
   width vs frequency, all 431 windows + literature segments. Literature
   bands/channels web-verified and hard-coded with per-entry provenance
   (`LIT` dict in `make_figures_referee_v331.py`; Enriquez+17 2.79 Hz,
   Margot+23 2.98 Hz, Price+20 2.79 Hz, Mason+24 30.52 kHz). Run:
   `python3 make_figures_referee_v331.py --data frozen_export_v3.31.json`
   (also regenerates completeness_surface.pdf and
   figures_referee_numbers.json).
2. **Fig 2 `coverage_waterfall.pdf`** — legend relabelled to the R3-5
   class names, via importlib module load of make_figures_v328.py
   (`load_and_select('frozen_export_v3.31.json')`, `target_sizes('/nonexistent')`).
3. **Fig 9 `eirp_vs_distance.pdf`** — legend relabelled + **clip fix**:
   `make_fig_eirp.py` SRC patched to the frozen export; the first
   round-9 legend wording overflowed the page (word cut mid-string at
   3.1 pt); final labels "deepest window, Class B (N; completeness
   unmeasured)" / "Class A (N; completeness measured)" end ≤227 pt on the
   244.8 pt canvas.

## Clip audit (v3.34 gate) — method refinement

pymupdf venv `/tmp/r7clip` (system pythons lack it; `/tmp/r7clip` lacks
matplotlib — keep the split). Filter `get_drawings()` items by **paint op
type** (`'s'/'f'/'fs'`): clip-path geometry legitimately lies outside the
page without painting. Verified positions:

- `completeness_surface`: 490 `fs` items to 50.4 pt out — **identical in
  v3.38 and v3.39** (inherited mpl3d surface-quad geometry, not a
  regression; edges render clean).
- Rotated y-label word bboxes overshoot ≤2.1 pt in three figures —
  identical sets in v3.38 (bbox artifact at paper scale, invisible).
- `eirp_context`: 1 stroked item 1.0 pt out (v3.38: 3) — improved.
- `eirp_vs_distance`: 0 words out after the legend fix (was 2, worst
  3.1 pt). All four figures: 0 real paint-op clips.

**Lesson: always diff the audit against the prior version folder before
treating a hit as a regression.**

## Page-recovery ledger

Round-9 additions (inference-status box, CP−72 subsection + table,
β Pic subsection, chronology + promoted audit table, robustness
paragraphs, §6 reorganisation, two-panel Fig 1) initially cost ~1.5 pp.
Recovered to exactly 38 via: Introduction three-point rebuild (ML/
six-decades/ancillary compressions), Appendix E → one paragraph,
Appendix P narrative tightening, Conclusions rewrite to ~6 points,
caption de-argumentation (C5), caveat-tag collapse (C2), and —
decisively — **removal of a hard `\newpage` in §1 that was pure page
loss** (39→38 with no content change). That `\newpage` had been the
fallback lever for float placement; if float placement ever degrades,
re-adding it is the first thing to try.

## Editorial passes (C2/C3/C4, this round's close-out)

- **C2**: caveat stated once in the §4 boxed reading rule + short
  "(boxed rule, §4)" tags; collapsed three near-verbatim repeats
  (fig:eirp caption, fig:sens2d caption, Conclusions passage).
- **C3**: three worst main-text stacked sentences split (catalogue-entry
  accounting §3; UV Ceti ideal-gain §6.1; publish-at-22-per-cent §1).
- **C4**: glossary/nomenclature harmonised into one crossing (state 1) →
  stage-1 flag = star-exceeds-ring (state 2) → candidate (state 3)
  cascade; the divergent "crossing" definition unified on the cell-level
  one.

## One-shot scripts

- `restructure_discussion.py` — the Discussion/Conclusions surgery
  (R3 reorder + f95 demotion + how-to-cite). **Already applied; do not
  re-run** (anchors no longer match the current tex). Kept as the record
  of what moved where; pre-surgery backup `/tmp/before_restruct.tex`.
- `round9_calc.py` — regenerates `survey_numbers_round9.tex`; safe to
  re-run (asserts the 431-window freeze and the CP−72 row).

## Letters

`REFEREE_RESPONSE_ROUND2..7.md` copied forward from v3.38;
`REFEREE_RESPONSE_ROUND8.md` (concise; written this round — includes the
mask-inconsistency correction note closing round-8 B13) and
`REFEREE_RESPONSE_ROUND9.md` (full, both reports, declines with reasons:
visibility-level CP−72 tests / β Pic 3-panel figure / extra injection
configurations = cluster-gated; online-only appendices = standing user
refusal).
