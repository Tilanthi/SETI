# Submission plan after the archive sweep (decision recorded 2026-09-14)

The authors have deferred submission until the full sweep is collected and
searched. v3.70 is an interim build. The release will be re-frozen at the
completed scope.

## The one design question that must be settled BEFORE the re-freeze

The paper's out-of-sample calibration rests on a sample **the design never saw**.
That is what licenses every empirically calibrated statement in it:

* the rank displacement (median add-one rank 0.425 against 0.5);
* the measured false-alarm tail factor (about 1.4, empirical range 1.1-2.2);
* the radial correction m(u);
* the statement that stage-1 status carries no candidate significance, evidenced
  by three independent non-recurring single-epoch events.

**If every block in scope is folded into one frozen release, no out-of-sample set
remains, and those statements lose the thing that makes them credible.** The
calibration would become in-sample, which is precisely the criticism referee 1
levelled at the radial repair and which the paper currently answers by pointing
at the external sample.

### Three ways to handle it

1. **Reserve a calibration hold-out before the re-freeze.** Choose a subset by a
   rule fixed in advance and independent of the data (e.g. every block whose
   execution-block UID hashes to a given residue, or all blocks of a randomly
   drawn third of the systems), freeze it, and keep it out of the headline
   survey. Costs sample size; preserves every calibrated claim. **Recommended.**
2. **Search everything and re-derive the calibration in-sample**, stating plainly
   that it is in-sample and carrying the residual as a systematic. Cheapest, but
   surrenders the paper's strongest methodological claim.
3. **Split the papers**: headline survey on the frozen 443 windows, the sweep as
   a separate multi-epoch recurrence paper which can then use the survey itself
   as its out-of-sample reference. Preserves both, at the cost of two papers.

Option 1 must be decided and the rule committed to the repository **before** the
sweep completes, because a hold-out chosen after seeing the results is not a
hold-out.
