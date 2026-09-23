# BUILD NOTES — v3.95: the radius-corrected statistic becomes primary

Two referee reports, 28 numbered items, worked in order. **13 are closed
in this increment, including both referees' central requirement and both
of Referee 2's stated conditions for acceptance that could be met without
new host computation.** The remaining 15 are listed at the end with what
each needs; `CHECKLIST_V395.md` is the live ledger.

## Gates

| gate | value |
|---|---|
| pages | 47 |
| LaTeX errors | 0 |
| undefined references / citations | 0 |
| multiply-defined labels | 0 |
| overfull boxes | 0 |
| Type 3 fonts | 0 |
| macros defined / unused | 1156 / 0 |
| abstract | **1918 characters** (arXiv limit 1920, both counters) |
| clean regeneration | **91/91 byte-identical** |
| number audit | 49 pass, 0 fail |
| catalogue self-sufficiency | 36 pass, 0 fail |
| round-file ownership | 47/47 |
| cross-reference resolution | 0 misplaced |

## The change that matters (R1-1, R2-2)

**The radius-corrected normalisation is now the primary statistic.** Both
referees required this and both were right.

The reasoning is stated in §5.3 and rests only on the demonstrated radial
dependence: images are primary-beam corrected, so the true noise rises
with distance from the pointing centre, while the search divides every
position by one global scale. The control probes therefore sit at
systematically different effective noise from the star, which is at the
phase centre. The displacement is measured three times independently — in
the pre-registered hold-out, in the radial profile of the control ensemble
itself, and in the prospectively searched extension — and pseudo-stars
reproduce it where no star is present at all.

New `primary_v395.py` reruns candidate selection and computes the
correctly conditioned null **for the corrected statistic**:

| | primary (corrected) | robustness (frozen) |
|---|---|---|
| stage-1 windows | **10** | 13 |
| attributed to CO | 8 | 9 |
| **unattributed** | **2** | 4 |
| expected | 1.26 | 1.26 |
| tail probability | **P ≈ 0.4** | P ≈ 0.04 |

**The apparent excess vanishes.** Four events lost (HD 23484, HD 14055,
HD 48370, CP−72 2713), one gained (HD 207129 B6). This is reported as a
methodological correction discovered during validation, with the frozen
list published beside it, and the manuscript states explicitly that the
decision does not depend on which events survive.

## Abstract rewritten to carry six requirements at once

R1-3, R1-6, R1-9, R2-2, R2-3 and R2-4 all land in the abstract, which has
a hard 1920-character limit. It now:

* leads with the **narrowband experiment** — 403 fine-channel windows, 60
  systems, 47.7 GHz — and describes the coarse search as secondary (R1-9);
* quotes only $P_{90}^{\rm sel}$, **per system on each system's best
  window**, median $1.5\times10^{15}$ W (R1-6);
* states in bold that this is **an upper bound on reach, not a central
  estimate**, with the ×0.48–1.35 transfer uncertainty and the one-sided
  +5/+20 per cent decorrelation bias given numerically (R2-3);
* explains the mis-normalisation, adopts the corrected statistic, and
  gives the corrected result **before** the old probability, which now
  appears only as an artefact that "does not survive correcting its
  measured position-dependent bias" (R1-3, R2-2);
* carries the sample caveat: disc/planet-formation programmes, 90 per
  cent, 21 of 5,908 M dwarfs, F/G-enriched, **"does not constrain the
  local habitable-zone planet population"** (R2-4).

Ten other phrases were trimmed to pay for it. Both the source-side and
PDF-side counters pass, with 2 characters of headroom.

## Also closed

* **R2-5** — probabilities to one significant figure throughout, with the
  1.2–1.9 tail-factor uncertainty folded into the quoted range rather
  than appended as a caveat. The three-way exchangeability comparison is
  replaced by primary-versus-robustness.
* **R1-8** — CWTFM demoted to "a literature convention only: it measures
  aggregate bandwidth, not the probability that a given transmitter
  frequency was observed". The per-system value $3.3\times10^{5}$ is now
  the preferred quantity.
* **R2-m4** — title is now *An Archival ALMA Search for Spectral
  Technosignatures toward 82 Stellar Systems within 40 Parsecs*.
* **R2-m3** — `REFEREE_VERIFICATION_v395.txt` ships the verbatim output of
  the regeneration and audit scripts, so the count chain can be checked
  mechanically. Referee 2 asked for exactly this.

## Still open, and what each needs

| item | needs |
|---|---|
| R1-2 | restructure §4.2 + §5.3 to one ordered procedure; retire overlapping use of "candidate" |
| R1-4 | elevate the visibility test to the principal spatial test, with a quantitative localisation sensitivity |
| R1-5 | **new host computation**: joint drift × dwell injection campaign |
| R1-7 | $N_{\rm eff}(P)=\sum_i C_i(P)$ and an $f_{95}(P)$ figure |
| R1-10 | search the full coverage and demote the line mask to a classification flag — a substantial reanalysis |
| R1-11 | $P(0\ {\rm repeats}\mid f_{\rm duty})$ from the 23 repeats' actual sampling |
| R1-12, R2-1 | the large restructure and de-jargonising, including the glossary |
| R2-6 | **new host computation**: per-hand polarisation on the 13 stage-1 windows |
| R2-m1 | Fig. 1(a) split or dropped |
| R2-m2 | White (2026) preprint or reduced reliance — author decision |
| R2-m5 | Appendix G.5/G.8/G.9 compressed to a table |

R1-5 and R2-6 require the pipeline host, which is currently saturated by
the archive-mining campaign; they are queued behind it rather than run
against a loaded machine.
