# Referee round 6 — plan

Two reports, received 2026-09-25 on v4.00 (`6e773abd4f74`). Both recommend
major revision. Both agree the null result survives.

**The reports disagree on the central design question. See
[`DISAGREEMENT.md`](DISAGREEMENT.md). Glenn must confirm the path before the
candidate chain is rebuilt.**

## Verified before acting

- **Referee 2's Poisson arithmetic is right.** The paper states
  "expectation 3.23, 14 observed, clustered permutation returns
  P(>=14) = 2.3e-1". For a Poisson mean of 3.23, P(>=14) = **7.8e-6**. The
  clustered permutation can legitimately give a far larger value — under
  block clustering the effective trial count is the number of blocks, not
  windows — but the paper must **say so**, because as written a reader
  checks it against Poisson and finds a discrepancy of four orders of
  magnitude. Action: explain the clustering, or correct the number.
- **HD 14055 and HD 23484 still appear 3 times** in the manuscript source.
  Same stale-data class as the Table 5 bug fixed in round 5, which was fixed
  at the generator; these remaining instances must be traced to their
  generators too, not hand-edited.

## Staged, not launched

The data needed is the same under **both** referees' designs, so it was
scoped regardless of the pending decision:

- `visfit_scope.json` — 56 crossings, 13 EBs already tested, **41 crossing
  windows in 36 EBs still untested**.
- `/data/SETI/mine2026/visfit_worklist_r6.json` on the fetch host — those
  36 EBs, **249 GB**, astrometry resolved for all of them, sorted smallest
  first.

**Not launched deliberately.** The host has 210 GB free against 249 GB to
fetch, so this cannot be a plain fetch-and-keep: it needs a
fetch -> calibrate -> visibility-fit -> delete loop with a bounded
footprint. That driver is not written. Launching a 15 h job with a
half-designed driver is the failure mode avoided at the start of the M3a
work, and it would stall on the disk floor within a few blocks.

**Next session: write the batched driver, then launch.**

## Order of work once the design is confirmed

1. **Batched visibility-fit driver** (fetch, calibrate, fit at the recorded
   cell, record, delete MS, next). ~15 h unattended.
2. **Commit the localisation criterion with a timestamp BEFORE running it**
   on the untested crossings. Referee 2 specifies: Re/sigma >= 4 at the
   stellar position, |Im/sigma| < 3, and Re/sigma above the maximum over the
   8 annulus positions and 4 off-event frequencies. Calibrate its false-alarm
   rate on the 77-block hold-out first. **This ordering is not optional —
   running first and committing after would repeat exactly the fault the
   mask half-width was criticised for.**
3. **Re-measure P90^sel through trigger + visibility fit**, retaining the
   injected measurement sets so it can be redone.
4. **M1 consistency sweep** — 13 conflicting quantities, each to one
   generated value, each added to the consistency gate so the build fails if
   they ever diverge again.
5. **M2 traceability** — one subsection describing the injection campaigns,
   one table listing all four with their purpose, and an explicit statement
   of whether the injected tones carry the instrumental response.
   ★ Referee 2 is right that this could move the headline by a factor of two.
6. **M3** — correct the Appendix A claim that correlation "costs resolution
   without touching the 1/513 floor"; reconcile 512 / 30-43 / 13 to one
   N_eff.
7. **Hann-window correlator response** replacing the 0.25/0.5/0.25 model.
   ★ We already computed this at v3.99 (`cresp_v399.py`): the true
   DFT-bin response gives 1.50-2.08 against the adopted 2.00-2.67, and we
   kept the conservative model deliberately. Referee 2 rejects that
   reasoning. **Adopt the measured response and recompute.**
8. M4 (one expectation), M5 (one visibility test), M6 (delete the occurrence
   bound), M7 (<=20 pp, appendix lettering, no revision history), then the
   17 minor items.

## Standing cautions carried into this round

- Fix at the **generator**, never the catalogue or the tex — the v3.99 lesson.
- `prosenum` and the consistency gate must cover every M1 quantity, or they
  will drift again.
- Clean regeneration must stay 100/100; use `cleanregen.py`, which needs no
  second copy.
