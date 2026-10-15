# BUILD NOTES — v3.84: two referee reports, all required changes

Point-by-point reply in `REFEREE_RESPONSE_V384.md`.

## Two new analyses, both of which changed something

★★ **Visibility-domain test on all four unattributed events.** The
measurement sets had been reclaimed, so the four execution blocks were
re-downloaded and recalibrated from the raw archive (140 GB for CP−72's
block alone). Phase-rotating each event's own channel to the stellar
position: **none of the four is a point source at the star.** Largest real
part $+2.5\sigma$; 61 Vir below its own controls; HD 14055's imaginary
part $3.2\sigma$ from zero, which emission at the star cannot produce.

★★ **Local radial noise normalisation, the structural fix the referee
asked for instead of the m(0) debit.** Standardising each control probe
within its own radius bin removes the gradient by construction and needs
no free parameter. Of 13 stage-1 windows, 9 keep their flag and **4 lose
it — HD 48370, HD 14055, CP−72 2713, HD 23484 — exactly the marginal
cases, all already dispositioned on other grounds.** No disposition
changes and the stellar debit is no longer needed.

The two analyses agree with each other: the windows the local
normalisation demotes are the ones the visibility test finds no source in.

## Accounting, now one identity

656 progenitor blocks = 484 processed (404 science + 77 hold-out + 3 with
no surviving window) + 177 repeat coverage. Asserted in the build.
"Every public ALMA observation" and "the archive is exhausted" withdrawn.

## Structure

Class A named as the primary experiment in the abstract, the Results and
the conclusions. $P_{90}$ is the primary sensitivity everywhere, including
Fig. 1, whose ordinate now carries the "not a like-for-like axis" caveat.
The exchangeability failure opens §5.3 in bold and appears in the
candidate-flow figure. New §5.7 says what is and is not excluded. The
$2\times10^{-7}$ parameter-volume product is deleted.

Compression: four audit subsections and six CP−72 diagnostic paragraphs
moved to appendices; conclusions 9.0 → 2.4 kchar, four claims.

New figures: selection bias by spectral class; cumulative systems against
$P_{90}$ with epochs per system; the four unattributed events.

## Traps

★ `getcol('DATA')` reads the **entire** data column before slicing — 4096
channels × 544k rows. Use `getcolslice` with an explicit `incr`, and a
TaQL row selection.

★ A hard-coded EB cap (`SETI_MAX_EBS_PER_TARGET=3`) is applied **before**
the single-EB filter, so three of four recalibrations silently dropped the
block we wanted.

★ The search trims band edges, so its channel index is **not** the
measurement set's. Select by frequency.

## Gates

34 pages, 0 errors / 0 undefined / 0 multiply-defined / 0 overfull /
0 Type 3, 866 macros 0 unused, abstract 1916/1920, clean regeneration
**71/71 byte-identical**, audit 51 pass 0 fail, arXiv set clean.
