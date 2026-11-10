# Three rounds of internal peer review: v3.63 → v3.66

Three rounds, three referees each, each round reading the build the previous
round produced. Reports are in `VIRTUAL_REFEREES_ROUND{1,2,3}.md`. Every point
was checked against the manuscript source, the released catalogue, the frozen
products or the typeset PDF; nothing was asserted from memory.

| | read | produced | pages | gates |
|---|---|---|---|---|
| Round 1 | v3.63 | **v3.64** | 32 | all 0 |
| Round 2 | v3.64 | **v3.65** | 32 | all 0 |
| Round 3 | v3.65 | **v3.66** | 32 | all 0 |

**Final build: v3.66.** 0 LaTeX errors, 0 undefined references or citations,
0 multiply-defined labels, 0 overfull boxes, 0 Type 3 fonts, 12 underfull
hboxes (the narrow two-column measure), 860 generated macros with 0 unused,
abstract 1850 of arXiv's 1920 characters, arXiv source set 46 items with 0
missing files, **clean regeneration 50/50 products byte-identical including all
15 figures**.

---

## The five findings that changed a claim

**1. (Round 3) A sentence added in Round 2 was backwards, and the truth is
better.** Round 2 added that β Pictoris's Band 6 window, being only 53.9 MHz
wide, "carries far fewer trials than a typical entry, and its rank is
correspondingly easier to earn". The catalogue says the opposite: the window is
narrow *and* finely channelised (15.26 kHz), so it holds 3533 channels like a
wide window and searches **1944 trial drift rates against a survey median of 4**
— the largest trials load in the survey, at η_drift = 422. The rank is *harder*
to earn, which strengthens the positive control. The numbers are now generated,
with an assertion that the window is still the survey maximum, so the claim
cannot be hand-written again.

*This is the finding I would keep if I could keep only one.* It entered during
revision, it sounded plausible, no gate would have caught it, and it took an
explicit audit of the revision itself to find. Rounds that only re-read the
original paper would have missed it.

**2. (Round 1) The new primary-beam response floor excluded nothing and looked
fitted to the data.** It now states the gap it sits in: the last retained window
has response 0.55 at 0.46 θ_PB (×1.81), the first window beyond it has response
0.29 at 0.62 θ_PB (×2.88), and nothing lies between. The floor of 0.50 sits in
that gap, so it binds prospectively. Round 3 added the responses beside the
offsets, since the rule is stated in response and was being argued in offsets.

**3. (Round 2) Figure 8's right-hand axis contradicted §4.** It read
"$P_{\rm eff} = 2.29\,P_{\rm trig}$" while $P_{\rm eff,total}$ is a per-window
catalogue column spanning ×1.33 to ×3.98. A reader taking a specific window's
threshold off that axis could be wrong by 40 per cent — exactly the error the
paper warns against. The axis is now labelled as the median scaling it is, and
the per-window range is generated into the caption.

**4. (Round 2) The figures had not been renamed with the text.** Figure 2 still
read "126 drift-resolved, 317 spectral-excess" and Figure 8's legend
"Class A: drift-search" after §4.1 had stopped using "drift-resolved" as a
synonym for Class A. Both generators were fixed and the text re-extracted from
every figure to confirm. The per-band noise-quality figure was also counting
four withheld ε Eri windows as "pass"; it now prints released counts.

**5. (Round 3) The reproducibility claim was itself not reproducible.** The
macro counting regenerated products was emitted by a generator that runs
*before* the figures are built, so on a clean regeneration it saw an empty
figure directory. The single file that failed the byte-identical test was the
one carrying the reproducibility number. Moved to `regen_count.py`, which runs
last. **The claim a paper makes about its own build is the claim most likely to
be made in the wrong place.**

---

## Everything else applied

*Round 1*: completed the Class A/B rename across nine text sites; abstract now
gives 88 of 115 archive-covered stars; ITU percentage printed to one decimal
(11.6, which divides); the ×3.2 debit no longer called a "worst case" it cannot
support; TRAPPIST-1 quoted edge-on only, because it transits and its inclination
is measured; the Table 14 expectation labelled as the exchangeable lower bound
it is; the ACA array assignment described as measured, not assumed; the
solar-system argument extended to *uncatalogued* bodies by non-sidereal motion;
astroquery cited; §4.4's self-describing opening folded away.

*Round 2*: the local-to-global scale ratios tied to the reproducible $R_\sigma$
test instead of advertising their own irreproducibility; Table 8's "survives"
column given units and a stated convention; the data-availability statement
now admits the release builds figures the paper does not print.

*Round 3*: the β Pictoris positive control now states the drift it is recovered
at, by linking to the cross-block frequency agreement of 1.00 channel over nine
years, which bounds any apparent drift far below the searched grid; the number
of windows narrower than 100 MHz given; Figure 8's axis label un-clipped
(verified by extracting text-block bounding boxes, not by eye); the
Conclusions' opening sentence now carries the physical drift-resolution count
alongside the class counts; abstract trimmed back to 70 characters of headroom.

---

## What three rounds did **not** fix

**The paper is 32 pages.** Content is 31.39 pp; page 32 carries bibliography
only. Every round added referee-required material and every round paid some of
it back. The main text is float-packed, so prose cuts no longer propagate —
measured this cycle at 0.04 pp for 3.8 kchars — and the remaining levers are
structural. Converting the scope table to a two-column float was tried and made
it *worse* (31.39 → 31.72) because a `table*` cannot share its page with text.

**Resolved by the authors on 2026-09-13: accept 32 pages.** The 31-page target
was the authors' own budget and not a journal limit, and the additions that
carried the paper past it are referee-required. The two structural
alternatives — moving §5.5 and Table 10 into Appendix H, or deleting
Appendix I — are not taken; each reversed an earlier referee's request. The
cover letter should state the length and the reason (`AUTHOR_ACTIONS.md`, A8).

**One cosmetic defect is recorded rather than fixed**: Figure 3's rotated
colourbar label overruns the figure bbox by 0.28 pt. I tried a font reduction,
measured it, and it did not help, so I reverted rather than leave an unverified
change. It is invisible at print size and Figure 3 must not be shrunk.

**Author items are unchanged** and are in `AUTHOR_ACTIONS.md`: the page budget
(A8), the printed commitment to request a third CP−72 2713 epoch (A9), the
Zenodo placeholder DOI (A10), affiliations and corresponding author (A11), plus
the older A1, A2 and A7.
