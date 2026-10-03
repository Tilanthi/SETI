# Response to the two referee reports

Both reports asked for the same three things in different words: resolve
the block accounting, make the fine-channel search the experiment, and
make the paper readable. Both also required one substantive new analysis.
We have done both analyses, and they agree with each other and with the
dispositions the paper already reached.

Every required change is implemented. Two of them changed a result.

---

## The two new analyses

**Visibility-domain test on all four unattributed events (Referee 1, §5).**
The measurement sets had been reclaimed after the search, so we
re-downloaded and recalibrated the four execution blocks from the raw
archive. For each event we phase-rotated every visibility in its own
channel to the stellar position and averaged: a point source at the star
gives a positive real part and an imaginary part consistent with zero,
while emission elsewhere in the field is suppressed in the real part and
generally leaves a non-zero imaginary part. Eight control positions on the
image-plane annulus give the comparison.

**None of the four is a point source at the star.** The largest real part
is $+2.5\sigma$; 61 Vir does not exceed its own controls; and HD 14055's
imaginary part is $3.2\sigma$ from zero, which emission at the stellar
position cannot produce. New Table 8 and Fig. 11.

**Local radial noise normalisation (Referee 2, §2).** We agree the global
noise scale was wrong at construction and that a post-hoc debit is the
weaker remedy. The control probes come from one fixed seed, so every
stored control value can be paired with its radius; standardising each
probe within its own radius bin, and the star on the innermost bin,
removes the gradient by construction and introduces no free parameter.

Re-ranking the 13 stage-1 windows this way leaves 9 unchanged and removes
the flag from 4: HD 48370, HD 14055, CP−72 2713 and HD 23484 — exactly the
marginal cases, and every one already dispositioned on other grounds.
$\beta$ Pictoris and 61 Vir keep their flags. **No disposition in the
paper changes, and the stellar debit is no longer needed.** Reported in
§5.3.2.

---

## Referee 1

1. **Block accounting.** One identity now, stated in the abstract, §3 and
   the conclusions, and asserted in the build: 656 public blocks in the
   parent observing-unit sets; 484 processed; of those 404 the frozen
   science sample, 77 the reserved hold-out, 3 left no surviving window;
   the remaining 177 are all repeat coverage of a star and tuning already
   taken. "Every public ALMA observation" and "the archive is exhausted"
   are withdrawn.
2. **Class A is the primary experiment.** Said in the abstract, at the
   head of the Results and in the conclusions. 1655 now appears only where
   it describes the archive processed.
3. **$P_{90}$ is the primary sensitivity.** Figure 1 now plots $P_{90}$
   per window for this survey, not the trigger, and the ordinate itself
   says the comparison is not like for like. $P_{90}$ leads the survey
   table and the abstract.
4. **Exchangeability failure promoted.** §5.3 now opens with it in bold,
   and the main candidate-flow figure carries the out-of-sample median
   rank next to the stage-1 box.
5. **Visibility test** — done, above.
6. **What this experiment excludes** — new §5.7, one paragraph of what is
   excluded and one of what is not.
7. **The $2\times10^{-7}$ product is deleted**; the three factors stay,
   with a sentence on why they are not multiplied.
8. **Compression.** Four audit subsections and six CP−72 diagnostic
   paragraphs moved to appendices; the conclusions cut from 9.0 to
   2.4 kchar and reduced to four claims.

Specific items 1–10 are all implemented: the abstract is rewritten in
plain language; "candidate event" and "confirmed technosignature" are
defined and used consistently; population fractions are quoted in systems;
a new figure gives the spectral-type composition against the census; a new
figure gives cumulative systems against $P_{90}$ and epochs per system;
118.1 and 113.3 GHz appear together; the impossibility of an
occurrence-rate limit is stated in one sentence with its three reasons;
$\beta$ Pictoris is named as the empirical positive control; and the four
unexplained events have their own figure.

## Referee 2

1. **The abstract's EIRP sentence** is rewritten and every quantity is
   traceable: $P_{90}$ for Class A at the median and deepest window, with
   the pooled figure removed. The stray "3.7×10¹³ W as a trigger" is gone.
2. **Local normalisation** — done, above.
3. **Confirmation completeness** — new subsection: 349 of 403 Class A
   windows (87 %) have a same-tuning repeat block, but only 40 of 65
   Class A systems (62 %) have one, so for the rest the recurrence test
   cannot be applied whatever the transmitter does. Stated as a structural
   ceiling on confirmable true positives.
4. **Accessibility** — plain-language abstract; a plain-language paragraph
   at the end of the Introduction; audit material moved to appendices.
5. **Duty cycle and disc bias in the abstract** — both now there.

Minor items: forward pointer to the catalogue edge cases; the
pre-registration timestamps are now stated to be corroborated by
server-side push times and the Zenodo minted date, not by local commit
dates alone; the Fig. 1 caveat is on the axis, not only in the caption;
the multiplied fraction is gone from the main text; the coarse-window
0/500 result is footnoted on the table row itself; the polarisation
caveat's scope is quantified (104 of 104 blocks deliver both parallel
hands); and the two-significant-figure convention is applied uniformly,
with one stated exception.

---

## Build state

34 pages; 0 errors, 0 undefined references, 0 multiply-defined, 0 overfull
boxes, 0 Type 3 fonts; 866 macros, 0 unused; abstract 1916 of 1920
characters; clean regeneration **71/71 byte-identical**; numerical audit
51 pass, 0 fail.
