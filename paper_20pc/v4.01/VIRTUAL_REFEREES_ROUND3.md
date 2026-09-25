# Virtual referee round 3 — on v3.65 (32 pp)

This round deliberately audits the *changes made in rounds 1 and 2* as well as
the paper, on the principle that revision is where errors enter.

---

## Referee G — audit of the new material

**G1. The sentence added to §5.3 about the β Pictoris Band 6 window is
backwards, and the correct version is better for you.** The revision says the
54-MHz window "carries far fewer trials than a typical entry, and its rank is
correspondingly easier to earn". From the released catalogue:

| | bandwidth | channel width | channels | drift trials | η_drift |
|---|---|---|---|---|---|
| β Pic B6 | 53.9 MHz | 15.26 kHz | 3533 | **1944** | **422.1** |
| survey median | 1.734 GHz | — | — | **4** | — |

It is narrow in frequency but finely channelised, so it has the *same* channel
count as a wide window and **the largest number of drift trials and the largest
η_drift in the entire survey**. Its rank is harder to earn, not easier. The
paper already prints the range "2–1944 (median 4)" in §4 without ever saying
which window the 1944 belongs to. Say it: the strongest positive control in the
survey is recovered in the window carrying the survey's heaviest trials factor.

I flag this as the most important point in my report not because of its size but
because of where it came from: it was introduced during revision, it sounded
plausible, and nothing in the build would have caught it.

**G2. Seven windows lie below 100 MHz of bandwidth** and the minimum, 53.9 MHz,
is shared by β Pic B6 and η Crv B7. The paper treats bandwidth heterogeneity
implicitly. One clause in §4 would cover it.

**G3. The abstract is 1888 of arXiv's 1920 characters.** Thirty-two characters
of headroom on a limit that truncates silently, in a paper whose own build notes
record having previously shipped an over-length abstract because the counter was
wrong. Buy margin.

**G4. Clean regeneration passes**: deleting every generated `.tex` and every
figure and rebuilding from the scripts reproduces 48 of 48 products byte for
byte, figures included. I record this because it is the claim that lets a reader
trust the rest, and it should be stated in the paper's data-availability
section with the number.

---

## Referee H — method

**H1. For a positive control you never state the drift at which it is
recovered.** You give the CP−72 2713 feature's drift (§5.3) but not β
Pictoris's, and β Pic B6 searches 1944 drift trials. A reader is entitled to
ask whether the CO was recovered at a drift consistent with zero, as an
astrophysical line must be. You have the answer already: the Band 3 crossings
recur across blocks to within `\BpRecThreeTuneChanMax` = 1.00 channel over nine
years once each block's own tuning is removed, which bounds any apparent drift
far below the grid. Make that link explicit — at present the recurrence result
and the drift-grid discussion never meet.

**H2. The primary-beam gap is quoted in offsets when the rule is in
responses.** §4.3 adopts a floor on the *response* (≥ 0.5) and then argues the
gap in units of θ_PB (0.46 versus 0.62). Those are the same statement only if
the reader does the Gaussian conversion. Quote the responses — 0.55 for the last
retained window and 0.29 for the first withheld one — beside the floor of 0.50,
and the argument becomes immediate.

**H3. Table 8's "survives" column is now labelled in σ and the caption explains
the convention, but the two reference debits (0.15 and 0.32) are still only in
prose.** Put them in the caption as a rule the reader can apply by eye, or add a
marker row.

---

## Referee I — production

**I1. Figure 8's new axis label is clipped.** I extracted the text-block
bounding boxes from `sensitivity_2d.pdf`: the second line, "(per window ×1.33 to
×3.98)", has a bbox reaching x = 504.4 pt on a 504.0 pt page. It runs off the
right edge. This is the same failure the build notes record from v3.50 — a
matplotlib axis label silently clipped by the figure's own bbox — and it has
recurred in the very fix that was meant to answer a referee. Rebuild with the
constrained-layout padding adjusted or the label shortened, then *re-extract the
text and check the bbox*, not the appearance.

**I2. The paper is 32 pages.** Three rounds of review have not closed it, and
each round added. If the 31-page target is the authors' own, say so and stop;
if it is a journal limit, something must go, and the honest candidate remains
the analysis-history material in §5.5.

**I3. The figures and the text now agree on terminology** — I re-extracted the
text from all fifteen built figures and found no remaining "drift-resolved"
label. The per-band noise plot's counts now match the released catalogue. Both
were wrong one round ago; both are right now. No action.

**I4. `\NEtaResolved` (132 windows resolve drift on the physical criterion) is
generated but referenced once.** For a paper that has just renamed its classes
away from the physical criterion, that number deserves to appear in the
Conclusions' first sentence too, so a reader who reads only the Conclusions
gets the honest version.
