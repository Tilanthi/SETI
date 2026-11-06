# v4.22 — build notes (referee round 21)

One self-contained PDF, **38 pp**, `technosignatures_40pc_v4.22.tex`,
`openjournal.cls`, built with `SOURCE_DATE_EPOCH=1577836800`. Target **arXiv
then OJA**: no supporting information, five ancillary files beside the PDF.

Built from v4.21 (`ddcbbc4e939b`) by `cp -a --reflink=never`, proved identical
before anything changed: `gate.sh` ALL GATES PASS and PDF md5
`f5d4f0e47664d0aaba65fe8e2c0bbce2`, the pushed v4.21 PDF exactly.

## Verification of this build
`make_all.sh` rc 0 · `gate.sh` twice rc 0, logs byte-identical, PDF md5
`c967f4d3408467634356d2bcd89fa3f3` · **`cleanregen` 258/258 byte-identical** ·
`audit_numbers` 58 PASS / 0 FAIL · 0 overfull boxes · 0 Type-3 fonts ·
`arxivset --force` A8 byte-identical, 5 ancillary files · `absmeta` M1–M4 ·
`abswords` 235 words · `abschars` 1,450 characters ·
**`prosegate_selfref` PASS, 0 stale pins** · `roundcollide` 170/170/0.

## New in the build
| file | round | what |
|---|---|---|
| `vuln_r21.py` | 640 | the calibration-residual census over 1,557 windows / 86 stars / 383 blocks, on the continuum at the extraction position in each window's own block |
| `tolrecur_r21.py` | 940 | the registration of the predicted cell measured on real recurring lines; the exclusions at a matched tolerance; one drift model; the depths over separated blocks alone |
| `r21_scope.py` | 950 | Class A/B by channel width, the 14 and the 38, the drift-resolving subset |
| `r21_lines.py` | 951 | what "unattributed" means against a 225-species CDMS/JPL list |
| `r21_image.py` | 952 | the image sideband, bounded from each block's own windows |
| `sensnull_r21.py` | 953 | the injection scorer's measured match, the injection-free rate, the transfer's uninjected strata |

plus `transfer_r21.py`, `contmeas_r21.py`, `tol_r21.py`, `reduce_r21.py` and
the harvest scripts as provenance, and `r21inputs/` (six frozen records).

## Ordering, which is the thing to read before moving anything
`tolrecur_r21.py` **must follow `confirm_r20.py`** (it reads
`confirm_r20.json`), and `r21_scope.py` / `r21_lines.py` / `r21_image.py`
**must follow `eta_r19.py`** (round 901, `\EdrNWinA`, `\EdrNSys`,
`\EdrUnionGHz`, which `r21_scope.py` reproduces before it computes anything
new). Both were wrong on the first placement and **neither showed on five
consecutive full builds** — only `cleanregen`, which deletes the products
first, can see a forward dependency.

## Gates moved because they enforced a defect
`calib_r16.py` A2, A6 and A9; `absreq_r17.py` B4; `stack_v408.py`'s typed
1 km/s probe; `prose_v412.py` P4; and in passing `chance_v414.py` A18(d) and
`absmeta.py`'s mandatory repair. Each now pins an invariant, and
`calib_r16.py --selftest` runs 12 cases including the two negative controls
that could not previously pass. Full account in
`referee_r21/INTEGRATE_REPORT_R21.md` §1.

## Open at the end of the round
1. **38 pages against a 35-page target.** The paper holds 243.7 kB of typeset
   text, which at perfect packing is 34 pages; the shortfall is float slack
   plus about 15 kB that would have to be deleted. The costed proposal is in
   the integrate report §6: move Table F1 and Table D2 to the ancillary files
   on the pattern the crossing ledger already uses. **Needs Glenn's word.**
2. **The abstract is 235 words against R1's 200.** The twelve clauses and
   what each is required by are tabulated in the integrate report §7.
3. `sens_r11.py::is_cross` reads the released crossing flag where the deposit
   carries the adopted one (7 against 6.3 in print; 5 against 6.05 on the
   adopted flag). `r21-repro` found it and declined to move a published
   number; it is still open.
4. `referee_r17/absascii_r17.py` carries a hard-coded copy of an old abstract
   and is superseded: `OJA_SUBMISSION.md`'s block is now generated from the
   typeset page and gated by `absmeta.py`.
