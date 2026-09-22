# Response to the two reports on v3.61 — changes in v3.62

**Manuscript**: `technosignatures_40pc_v3.62.tex`, **31 pages, unchanged from v3.61**
(the page budget was held: every addition below is paid for by a cut listed at the
end). Two-column OJA layout, 0 LaTeX errors, 0 undefined references, 0
multiply-defined labels, 0 overfull boxes, 0 Type 3 fonts, 817 macros with 0 unused,
abstract 1857 of arXiv's 1920 characters, clean regeneration **52/52 generated files
byte-identical**, arXiv set 47 items building from an empty directory.

Both reports make the same principal request in different words: referee 1 asks us to
**repair the spatial null and rerun the candidate generation**, and referee 2 asks us
to make the **non-circularity of the statistic revision** checkable rather than
assertable. Both are done, with new computation, and both come out in the paper's
favour.

---

## Referee 1

### 1 (principal) — repair the spatial-control statistic and rerun the survey

Done. `radius_matched_v362.py` rescores all \NWindows{} windows from the stored
control vectors, using two independent repairs, and the result is a new subsection
(§5.3, *The survey rescored with a repaired null*) and Table 8.

* **Radius-matched screen.** The probes come from one fixed seed, so their fractional
  radii are identical in every window; ranking the star against only the 54 probes
  with $u\le0.30$ is the closest approach to an iso-primary-beam comparison the frozen
  products allow. It returns 5 windows, the released 4 plus one Class A window at
  $T_\star=5.11$, against **8.1 expected by chance** at that screen's coarser
  resolution (1/55 rather than 1/513).
* **Radially detrended screen (adopted).** Keep all 512 probes and remove the measured
  trend: subtract $s\,m(u_k)$ from each control and $s\,m(0)$ from the star, with
  $m(u)$ measured **on the held-out windows**, which played no part in defining the
  statistic. Resolution is unchanged. It returns **exactly the released set: 4
  windows, none added, none lost.**

Because $m(0)$ is the one free choice, we report the disposition as a function of it
rather than arguing for a value. The conservative choice (innermost measured bin) is
0.15σ; the debit that centres the held-out rank distribution on 0.5 is 0.32σ. Table 8
gives the largest debit each window survives:

| window | $T_\star$ | survives a debit up to |
|---|---|---|
| β Pic B3 | 14.65 | 25.8σ |
| β Pic B6 | 11.68 | 10.8σ |
| CP−72 2713 B7 | 5.81 | 0.61σ |
| HD 48370 B6 | 27.10 | 0.21σ |

**No window is promoted by any repair or any debit.** The two β Pictoris windows
survive by one to two orders of magnitude. CP−72 2713 survives twice the calibrated
debit. HD 48370, already dispositioned as foreground CO, falls between the two choices
— which is physically sensible, since its stellar peak stands only 0.27 above a ring
maximum of 26.83 precisely because the emission is extended. **The number of
unattributed stage-1 outliers is one for every repair and every debit from 0 to
0.61σ**, so no disposition in the paper depends on the defect.

We also report honestly what the repair does *not* do: detrending moves the held-out
median from 0.429 to 0.437 and the survey median from 0.466 to 0.474. Radius is part
of the story and not all of it, which is why §6.4 now puts visibility-domain
localisation ahead of further repair of a position-ranking statistic.

On the second option (a visibility-domain statistic throughout): that requires
retained visibilities, which this survey did not keep, and re-downloading and
recalibrating 104 execution blocks is a different experiment rather than a revision.
The one window where it mattered was done (CP−72 2713, §5.3), it is named as the first
change for a successor, and Eq. 6 now states the statistic.

### 3 — the execution-block arithmetic

The referee is right and the cause was a stale harvest. `archive_meta_v343.json` was
built from the MOUSs of the 102 blocks the pre-Band 9/10 catalogue held, so it knew
nothing of the two Band 9/10 blocks or their MOUSs: 448 − 102 = 346, while the
catalogue holds 104 blocks. We queried the two missing MOUSs (ALMA TAP; they hold 3
public blocks between them), folded them in at the generator, and **asserted that the
searched count equals the number of distinct execution blocks in the released
catalogue**, so this class of error cannot recur. The reconciliation is now printed in
§3 exactly as the referee suggests:

**451 = 104 (frozen analysis) + 150 (searched since) + 197 (remaining)**.

### 4 — Table 4 omitted Bands 9 and 10

Fixed, also at the generator. The row came from `round8_calc.py`, which reads the
v3.31 freeze and therefore knew only Bands 3–8; the counts now come from the released
catalogue as two macros, read **3/4/5/6/7/8/9/10 = 40/4/4/216/155/12/4/8**, with an
assertion that they sum to 443.

### 5 — do not present $P_{\rm eff}=2.29P_{\rm trig}$ as universal

Adopted, in the referee's own words. The abstract now reads "for the standard
Hanning-smoothed response the median unresolved-tone correction is ×2.29, and a
window-specific combined response and smearing correction is released with the
catalogue". The catalogue carries two new columns, `eirp_eff_total_W` and
`c_response_smear`, giving

$$P_{\rm eff,total}=P_{\rm trig}\,C_{\rm resp}\,C_{\rm smear}$$

per window (range 1.33–3.98, median 2.29).

### 6 — one compact table of the sensitivity/completeness quantities

Added as Table 2, early in §4, with exactly the columns requested plus the two
correction factors, and it states which quantity the abstract and conclusions quote
($P_{\rm eff}$).

### 7 — separate Class A from Class B more sharply

Done. The abstract now reports Class A first and names the 126 windows and 59 systems
before mentioning Class B; the scope-of-constraints box gives **separate Class A and
Class B searched domains** (islands, union, frequency range, channel widths,
accelerations); and the conclusions keep the two apart.

### 8 — a simple statement of the searched parameter space

Done, in the form suggested and split by class (§4.4). Class A: 25 islands,
43.2 GHz union, 89.6–873.1 GHz, channels 0.02–1.95 MHz, $|a|\le3.6$–4.0 m s⁻². Class
B: 36 islands, 89.9 GHz, 15.6–31.25 MHz channels. The abstract also now carries the
113.9 GHz unique-frequency figure beside the 89.6–873.1 GHz range, so the coverage
cannot be read as continuous.

### 9 — the molecular-line mask

Table 9 (band-by-band excluded bandwidth) was added in v3.61 and stays. v3.62 adds the
sensitivity statement referee 2 also asked for: of the 20 crossings, 7 fall inside a
mask tube, 3 of them are the stage-1 outliers already dispositioned as CO, and the
other 4 do not exceed their own control ensembles — **no masked crossing would have
entered candidate generation had the mask been absent**. We agree with the "detect
everything, flag coincidence, classify separately" design and recommend it explicitly
for a successor (§5.3).

### 10 — CP−72 2713 is over-long

Cut by about half, as asked. The main text now keeps only the chain the referee lists
(detected → marginal outlier → point-source-like at the star → deeper repeat → absent
→ statistically unsurprising → no persistent emission). The neighbouring-channel
statistics, the second-stage local null, the edge-channel and ring-margin details, and
the belt/split-half/continuum checks are now in Appendix H.

### 11 — "What was found. Nothing."

Replaced by **"No credible technosignature candidate survives the analysis."**

### 12 — the Arecibo comparison

Every occurrence now reads "the numerical EIRP of the Arecibo planetary radar" rather
than "Arecibo-class", and the $\nu^2$ gain-scaling caveat sits in the same paragraph as
the benchmark (§4.3).

### 13 — sensitivity limits versus population limits

Title changed as suggested: **"An ALMA Archival Search for Spectral Technosignatures
toward 81 Stellar Systems within 40 pc"**. The conclusions now also carry the "not an
occurrence rate" warning in full (see referee 2, major 7).

### 14 — do not down-weight disc hosts before detection

Agreed, and withdrawn. The v3.61 recommendation is replaced by the opposite: "a
detection statistic should not know whether its target is astrophysically interesting,
or a real transmitter would be penalised for the company it keeps. Disc membership
belongs in classification." What replaces it is the *rate* (referee 2, major 4) and
the procedural remedy of running the continuum lane before promotion.

### 15 — polarisation diagnostic for the four stage-1 events

Not done, and here is the obstacle rather than a reason. The per-hand products do not
survive: the pipeline forms Stokes $I$ during extraction and the calibrated
measurement sets are deleted after processing (disk). A per-hand test therefore means
re-downloading and recalibrating the four blocks, ≈45 GiB and ~1 h each, which we did
once for CP−72 2713's visibility fit and cannot repeat inside this revision.
What the paper now states instead is the exact scope: all 104 blocks deliver both
parallel hands and **none delivers a cross-hand product**, so no Stokes Q, U or V is
recoverable from the archive for any searched window; Stokes $I$ recovers a fully
polarised carrier at full power but with up to ×1.41 less signal-to-noise than a
per-hand search, and a one-hand flagging loss would be worth a factor two in power.
Polarisation is its own bullet in the scope box and is now named in the abstract.

### 16 — freeze the exact release

The Data Availability section now states that the version of record is the Zenodo
deposit and not a branch: it carries the exact commit that produced every number,
table and figure, the 443-row catalogue, the control statistics, the injection
records and **the held-out campaign as a separately labelled product**, with the
repository tag named in the deposit. The DOI is minted at acceptance; the tag and
commit hash are author actions recorded in `AUTHOR_ACTIONS.md`.

### Restructuring

Partially adopted. Main text is now 20.4 pages of the 31, with the survey-level
false-alarm calibration (v3.61) and the CP−72 diagnostics (v3.62) moved to appendices.
We did not renumber into the proposed six-section skeleton: the existing structure
already matches it in content, and rewiring 200+ internal references carries more risk
than the gain.

---

## Referee 2

### 1 — the abstract

Rewritten to the structure requested: sample and reach, then the headline result with
one EIRP number, then the methodological contribution, then the few supporting
numbers. The rank statistic, the 1.4× tail factor and the revision chronology are gone
from it; the polarisation limitation is now in it (major 6). 1857 characters, down
from 1877, with the numeric density roughly halved.

### 2 — the non-circularity of the statistic revision

Three things were asked for; all three are done.

* **The exchangeability argument now sits where the statistic is defined** (§4.2,
  immediately after Eq. 2), derived without reference to any window: a region maximum
  over $n_{\rm src}$ positions against single-position controls exceeds all $N_{\rm
  ctrl}$ of them with probability $n_{\rm src}/(n_{\rm src}+N_{\rm ctrl})$, which for
  135 and 512 is 21 per cent rather than 0.2 — a floor under which most crossings flag
  whatever the data contain.
* **Whether we knew AU Mic would drop**: the paper states plainly that the revision
  postdates the first flag it removes, gives both dates and both commit hashes, and
  now adds the survey-wide consequence, which is the check a reader can make
  independently: the superseded statistic flags **27 of its 119 crossings (23 per
  cent, i.e. its own floor)** against 4 under the symmetric statistic. The revision
  removes a systematic inflation affecting about seven times as many windows as the
  one candidate whose disposition changed.
* **Table 10 (both statistics, every window the original flagged)** stays in the main
  results section, and the released catalogue carries `star_snr_regionmax` and
  `stage1_flag_regionmax` **for all 443 windows**, so the audit is not limited to
  seven.

### 3 — proportion of §5.3

Done: see referee 1, point 10. The main-text CP−72 2713 discussion is about half its
former length and the derivations are in Appendix H, parallel to the β Pictoris audit.

### 4 — the natural false-positive rate from disc CO

Quantified, as requested, in §6.4: **3 of the 4 stage-1 outliers are molecular
emission toward disc hosts, arising in 2 of the 67 debris-disc systems searched — one
flagged system in 34, or 2.4 per cent of Class A windows.** That is the vetting burden
a disc-selected archive carries, and it is stated as the number a future survey should
plan around.

### 5 — the mask's cost in candidates

Added: 7 of the 20 crossings fall inside a tube, 3 are the already-dispositioned CO
outliers, and the remaining 4 do not exceed their own control ensembles, so the mask
cost no candidates (§5.3).

### 6 — polarisation prominence

Now in the abstract's last sentence, as well as in the scope box (own bullet) and
§4.2. See referee 1, point 15 for why no new polarimetric analysis is included.

### 7 — the conditional transmitter fraction

The warning is repeated in the conclusions with the worked example of misuse the
referee asks for: it cannot be set beside the completeness fractions of
Enriquez et al. (2017) or Price et al. (2020), which condition on a different
frequency range, morphology and sample; the only defensible comparison is between
EIRP thresholds, which is what Fig. 1 plots.

### 8 — comparative context

Added at the end of §2: this survey extends the searched frequency range by nearly an
order of magnitude and reaches EIRP thresholds comparable with cm-wave archival work
for the nearest systems, while sampling far fewer stars, far fewer epochs and a
channelisation seven orders of magnitude coarser — complementary to those surveys
rather than a deeper version of them.

### 9 — the VBRL affiliation

We have flagged this to the authors as the one item an analysis cannot settle; a
one-clause description of the company is theirs to supply, and is recorded in
`AUTHOR_ACTIONS.md` beside the competing-interests wording.

### Minor points

* **Transitions in §§4–5**: a light pass was made on paragraph openings in the
  rewritten sections; the colloquial "belong here", "ships with" and "ships as
  catalogue columns" are gone.
* **Figure 3**: it became a full-width float in the two-column conversion (v3.61) and
  is now about 57 per cent larger than in v3.60. We did not split it: the point of the
  figure is that coverage is clustered, and splitting it by distance hides that.
* **Figure 8**: decluttered. The three-line in-panel note is gone; its numbers are in
  the caption and the panel keeps one short label.
* **Table count**: two more tables moved to appendices this round (survey-level
  calibration material and the CP−72 diagnostics). Every remaining main-text table is
  one the argument uses.
* **"119 crossings" versus "27 windows"**: §1 now spells the relation out —
  "flags 27 windows, 23 per cent of its 119 crossings, against 4 under the symmetric
  statistic".
* **Harmonics and intermodulation products**: promoted from a scope caveat to an
  explicit bullet (ix) in the scope box.
* **Table 6 caption** now defines the sign convention of the topocentric offset
  adjacent to the table, as Table 14 already did.
* **All-caps run-in headings** are the `openjournal` class's rendering of
  `\subsubsection*`, not a LaTeX artefact; we have left them as the style file
  produces them.
* **Preprint citations**: White (2026) is flagged "submitted"; the others carry arXiv
  identifiers. One real error was found and fixed in v3.61: the Sardinia Radio
  Telescope paper is Manunza et al. (2025), Acta Astronaut., 233, 155.

---

## The page budget

Additions this round: the repaired-null subsection and Table 8, the quantity table
(Table 2), the class-split searched domain, the exchangeability argument at Eq. 2, the
disc false-positive rate, the mask-candidate statement, the occurrence-rate warning,
the comparative context, the harmonics bullet and the release-freeze statement.

Paid for by: the CP−72 2713 main text (halved, diagnostics to Appendix H), the radial
diagnosis (compressed now that the repair carries the conclusion), the trials-budget
prose in Appendix G (superseded by Table 13), the rank-calibration appendix block, the
Background section, the ancillary-results paragraph, the illustrative-appendix prose,
four bibliography entries that wrapped, and two figure captions.

Net: **31 pages in, 31 pages out.**
