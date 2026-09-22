# BUILD NOTES — v3.90: the radius correction fails its own validation

Two referee reports. This increment closes the two items both reports
treat as conditions for acceptance, and they turn out to be the same
question: **which statistic is primary, and can it be justified?**

## Gates

| gate | value |
|---|---|
| pages | 47 |
| LaTeX errors / undefined / multiply-defined / overfull / Type 3 | 0 / 0 / 0 / 0 / 0 |
| macros defined / unused | 1173 / 0 |
| abstract | **1910 characters** (limit 1920, both counters) |
| clean regeneration | **92/92 byte-identical** |
| number audit | 49 / 0 |
| **primary-statistic consistency (new gate)** | **0 problems** |
| round-file ownership | 48/48 |
| cross-reference resolution | 0 misplaced |

## 1. Referee 2 was right: the paper contradicted itself, and a count was wrong

Both defects confirmed exactly as described.

* §4.2 said the radius-corrected statistic was primary; Appendix G.10.2
  said in terms that it was not. v3.89 changed the front of the paper and
  left the back of it stating the opposite.
* The conclusions printed the **frozen** CO count (9) beside the
  **corrected** totals (10 stage-1, 2 unattributed), so 9 + 2 = 11 did not
  equal 10.

Both are fixed, and a new gate, `consistency_v390.py`, now asserts that
both count identities close, that the text does not simultaneously adopt
and reject the corrected statistic, and that the abstract's counts come
from whichever statistic the paper declares primary. Nothing in `gate.sh`
could previously see any of this.

## 2. Referee 1's condition: the radius correction fails out of sample

Referee 1 required the correction be frozen and applied unmodified to
independent data, with the verdict decided in advance, and specified what
to do if it failed. New `radval_v390.py` does exactly that on
**778 windows** the correction played no part in building — the
pre-registered hold-out and the prospective extension — at a level fixed
beforehand ($p \geq 0.05$).

**It fails.**

| stellar rank, out of sample | median | $D$ | $p$ |
|---|---|---|---|
| uncorrected | 0.409 | 0.105 | $<10^{-4}$ |
| radius-corrected | 0.407 | 0.097 | $<10^{-4}$ |

The departure from uniformity is essentially undiminished and the median
moves **further from** 0.5, not toward it. The result holds in each sample
separately.

A methodological point worth recording: the pseudo-star test Referee 1
suggested does **not** discriminate. Probe-against-probe ranks are
near-uniform with or without the correction (uncorrected $p = 0.16$
pooled), because every probe is drawn from the same radial distribution.
The star is at the phase centre, inside the annulus, and only the
**stellar** rank tests the asymmetry the correction exists to repair. Both
tests are reported; the verdict rests on the discriminating one.

## 3. What follows, and it is what both referees pointed to

Per Referee 1's own instruction, the corrected statistic is therefore
**not** primary. The frozen screen returns as the primary
candidate-generation device — it at least was fixed in advance — described
consistently as a prioritisation and never as a significance test. Every
disposition now rests on physical evidence: visibility-domain
localisation, stellar-frame line coincidence, and recurrence.

Counts are consistent throughout at **13 flagged / 9 CO / 4
unattributed**, with the corrected **10 / 8 / 2** as a documented
robustness comparison. Appendix G.10.2's position, which v3.89 had
overridden, was correct; its justification is now empirical rather than
procedural.

I over-corrected in v3.89 on the previous round's instruction. The
validation that this round's Referee 1 demanded has settled it, which is
the system working as intended.

## 4. Abstract rewritten to specification

Referee 1 asked for four things in order and for the $P\simeq0.04$ versus
$P\simeq0.4$ discussion to be removed; Referee 2 asked for plain,
self-contained language with one headline number and one headline result.
The abstract now states the sample and method, the single sensitivity
($P_{90}^{\rm sel}$ per system, median $1.5\times10^{15}$ W, with the
dominant transfer uncertainty), the single result, and the
representativeness caveat — with R1-11 ("narrowband" means narrow relative
to an ALMA channel, 15.3–1953 kHz) and R1-7 ("the ALMA archive-selected
stellar sample within 40 pc") folded in. The tail probabilities are gone
from it entirely.

## Still open

The presentational programme both reports ask for — cutting 20–25 per cent
of main-text prose, moving the audit narrative and Appendix G.5/G.7–G.9 to
supplementary material, relocating Table 1, restructuring around Figure 3,
and the remaining figure moves — plus R1-2 (stratified end-to-end
injection through the selection gate), R1-3 (the effective-exposure
occurrence likelihood), R1-6 (the time-domain completeness figure) and
R2-6 from the previous round (per-hand polarisation). R1-2 and R2-6 need
the pipeline host, still occupied by the archive-mining campaign.
