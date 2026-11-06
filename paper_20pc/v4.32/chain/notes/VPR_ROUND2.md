# Referee report — round 2 of 5: scientific validity of the inference

Manuscript: `technosignatures_40pc_v3.85.tex` / `.pdf` (39 pp), catalogue
`per_target_results_v3.85.csv` (1655 rows, 50 columns).

Round 1 covered arithmetic and internal consistency. This round is confined to
whether the **inference** is sound: the statistical chain from a threshold
crossing to a null result, the status of the spatial screen, the sensitivity and
completeness propagation, the attribution of the flagged events, overclaiming,
and missing controls. Style, typography and cross-references are out of scope.

Every claim below was checked against the released catalogue, the generated
macro files, the generator scripts and the frozen export, not against the prose
alone. Where I could not reproduce a number I say so. Where I checked a claim
and it **held**, I say that too — §8 collects those, and it is not a short list.

**Verdict.** The paper's methodological self-criticism is unusually good: it
diagnoses the failure of exchangeability itself, refuses to adopt a statistic
chosen after the candidate list, and declines to convert the null into an
occurrence fraction. That is the work of authors who are trying not to fool
themselves. But the inference has four load-bearing defects that a hostile
referee will find, and three of them run into the abstract:

1. the claim that three of the four unattributed events admit no recurrence
   test is **contradicted by the released catalogue**, which carries 4, 17 and 3
   further blocks at the same tuning for them (**S1**);
2. the headline chance comparison is run against the **wrong observed count**
   (2 instead of 4), and against an expectation the paper elsewhere disowns
   (**S2**, **S3**);
3. the "block-resampled null" that Table 8 says the text uses is **degenerate** —
   its per-window rate is identically 1/512 by construction (**S4**);
4. the quoted completeness **P90 is measured against the 5σ trigger**, but the
   survey's operative gate is "beat the maximum of 512 controls", whose median
   in Class A is 5.79σ; in 99.3 per cent of Class A windows the trigger is not
   the binding constraint (**S6**).

12 MAJOR and 10 MINOR issues follow.

---

## 1. Statistical logic: from crossing to null

### S1 — MAJOR. "The other three have no second epoch" is false against the released catalogue

**Text.** Abstract: *"The remaining 4 have no identification, against 3.2
expected by chance, and none is independently confirmed."* §4.6, step 10:
*"Of the 4, the one with a second epoch of the same tuning does not recur in it,
and the other three have no second epoch, so no recurrence test exists for
them."* Conclusion 2: *"the other three have no second epoch."*
Table 10, column "repeat blocks": `none / none / 1; T⋆=4.70 / none`.

**What the data say.** Filtering `per_target_results_v3.85.csv` for other
execution blocks of the same star whose window covers the same frequency range:

| event | further blocks at the same tuning | their T⋆ at the star |
|---|---|---|
| 61 Vir B7 344.87–346.71 | **4** | 4.83, 4.81, 4.82, 4.56 (119–310 controls above the star) |
| HD 14055 B7 330.39–332.23 | **17** | 4.47–5.42; four of them are ≥5σ crossings, none rank-first |
| HD 23484 B6 229.61–231.45 | **3** | 4.99, 4.34, 4.20 (21–325 controls above the star) |
| CP−72 2713 B7 | 1 | 4.70 |

**Cause.** `v381_calc.py:651`, `_repeat_blocks()`:

```python
def _repeat_blocks(r):
    f = F(r['f_cross_GHz'])
    if f is None:
        return []
```

The crossing frequency is blank for exactly these three rows (the same reason
Table 10 prints the window range with footnote *a*), so the function returns an
empty list and the table prints `none`. The absence of a *stored peak frequency*
has been typeset as the absence of a *repeat observation*.

**Why it matters scientifically.** This is the recurring-bug family of this
project and it has escaped into the abstract. It is also the wrong way round:
the data are *better* than the claim. Three of the four unattributed events do
have repeat coverage at the same tuning — seventeen blocks in the HD 14055 case
— and in every one of them the star falls back into the body of its own control
distribution. §5.3.1 already reports exactly these numbers ("4.83 with 119
controls above the star, 5.51 with 5, and 4.99 with 21") and is the only place
in the paper that is right. The correct statement, *"none of the four recurs,
and for three of them the non-recurrence is measured over 3–17 further blocks
of the same tuning"*, is a materially stronger null result than the one
printed.

**Fix.** Match repeats on window overlap when `f_cross_GHz` is absent, as the
catalogue filter above does. Rewrite Table 10's column, the abstract, §4.6 step
10 and Conclusion 2. Reconcile §5.3.1's "5.51 with 5" for HD 14055 with the
catalogue, where the deepest further block is 5.42 with 20 controls above.

---

### S2 — MAJOR. The headline chance comparison uses the wrong observed count

**Text.** §5.3: *"Resampling whole execution blocks with replacement … a survey
of this shape produces 3.5 unattributed stage-1 outliers on average, with a 95
per cent interval of 0–7 … **2 are observed, and P(≥2) = 0.87** on the resampled
null. The unexplained population is what chance predicts."*

**What the data say.** `blockboot_v385.py:63`:

```python
obs = 2          # unattributed stage-1 outliers under the primary statistic
```

Hard-coded. Under the primary statistic the paper reports **4** unattributed
stage-1 outliers, in the same section, four paragraphs earlier. `2` is the count
under the **radius-corrected** statistic (`\LocCorrUnattrib` = 2, §5.3.2: *"8
attributed … and 2 unattributed"*). So the sentence compares the corrected
statistic's yield against the released statistic's null, and concludes that the
unexplained population is what chance predicts.

On the same bootstrap, P(≥4) ≈ 0.46 rather than 0.87. The qualitative
conclusion survives, but the sentence as written is not a valid comparison and
the macro is mis-wired.

**Fix.** Set `obs` from the catalogue (`stage1_flag` and `disposition`), not by
hand; regenerate `\BootP`; add an assertion in `audit_numbers_v385.py` that the
bootstrap's observed count equals `\NUnattributed`.

---

### S3 — MAJOR. Six chance expectations, and the abstract quotes the one the paper disowns

The paper carries, for the same quantity, all of:

| where | value | basis |
|---|---|---|
| Abstract, §4.6 step 9, Table 11 caption, Conclusion 2 | **3.2** | 1655/513, ideal exchangeability |
| Table 8 row 1 | 3.1 | same, on 1614 distinct datasets |
| Table 8 row 2 | 3.9 | 3.2 × hold-out tail factor 1.2 |
| Table 8 row 3 | 3.2 | calibration-sample measured rate |
| Table 8 row 4, §5.3 | **3.5** | block resampling (see **S4**) |
| §G.3.3, §5.3.6, §6.2 | **4.7** | pseudo-star rate × 1.4 propagated to 1655 windows |
| Appendix F (Class A stratum) | **0.79** | 403/513, the class that carries every flag |

Table 8's caption says *"the block-resampled figure is the one the text uses,
because it is the only one that respects the dependence structure of the
survey"*. The text does not use it: the abstract, §4.6, Table 11 and the
conclusions all use 3.2. §G.3.3 goes further and instructs the reader that
*"Every per-window probability quoted in this paper should be read as multiplied
by 1.4"* — which the abstract does not do.

**Why it matters.** The answer to "is 4 what chance predicts?" depends on which
number is operative:

| null | P(≥4) |
|---|---|
| Poisson 3.2 (abstract) | 0.40 |
| Poisson 4.5 = 3.2 × 1.4 (the paper's own instruction) | 0.66 |
| Poisson 0.79 (Class A only, exchangeable) | 0.009 |
| Poisson 1.1 (Class A only, × measured tail 1.4) | 0.026 |

The last two matter because **all 13 stage-1 outliers are Class A** (the
catalogue confirms: `search_class == 'A'` for all 13; Appendix F states the
coarse stratum predicts 2.44 and contains 0). Pooling 1252 coarse windows that
have never produced a flag into the denominator of a comparison whose numerator
is four Class A events inflates the expectation by a factor 4. Appendix F makes
exactly this comparison for the fine class — *"13 of them contain an on-star peak
above their own control maximum against 0.79 expected"* — and calls it a
departure from uniformity; the main text makes the pooled comparison and calls
it consistency. Both cannot be the operative null.

**Fix.** Choose one null, state it once, and compute it on the windows that can
produce the event being counted:

> *N* unattributed Class A stage-1 outliers against *E* = (403/513) × (measured
> tail factor) × (1 − line-coincidence fraction) expected, with the tail factor
> and its interval quoted from the pre-registered hold-out.

Then live with the answer. If that number comes out near 2σ, say so — it is
still not a detection (the events do not recur, do not localise, and one has 17
blocks of non-recurrence behind it), and a candid "mild, unexplained excess" is
a far more defensible position than a comparison whose denominator was chosen
after the fact.

Related, smaller: **3.2 is the expectation for *all* rank-first windows and is
compared with the *unattributed* subset.** The attribution filter can only
reduce it; §5.3.7 reports that 17 of 75 crossings fall inside a mask tube, so
the expectation for the unattributed subset is roughly 0.77 of the expectation
for all.

---

### S4 — MAJOR. The "block-resampled null" preserves no dependence structure

**Text.** Table 8: *"Block resampling | 3.5 | within-block correlation preserved;
no independence assumed."* §5.3: *"We therefore estimate the null empirically,
preserving that structure … drawing each window's no-signal rate from its own
512 control positions."*

**What the code does.** `blockboot_v385.py`:

```python
idx   = RNG.choice(NPROBE, size=32, replace=False)
hits  = sum(1 for i in idx if c[i] > np.delete(c, i).max())
byblock[r['eb']].append(hits / 32.0)
```

`c[i] > max(rest)` is true iff probe *i* is the strict maximum of the 512. I
verified on `frozen_export_v3.81_survey.json` that **every one of the 1698
matched windows has exactly one strict maximum, with zero ties.** Therefore
exactly one probe per window satisfies the condition, and the per-window
"empirically measured no-signal rate" is **identically 1/512 in every window**.
The 32-probe subsample estimates that constant with a ±390 per cent per-window
relative error, so the realised sum over 1614 windows is 3.49 where the exact
value is 1614/512 = 3.15 — the 0.3 difference is Monte Carlo noise in the
estimator, not a property of the survey.

Consequently the block bootstrap is Binomial(1614, 1/512) with the blocks having
no effect, because the quantity being resampled is a constant. The docstring's
intent — *"instead use the empirical tail excess this window shows"* — is not
what the code computes; the construction cannot see a tail excess, because
ranking a control against the other controls is exactly the exchangeable null.

The paper's conclusion *"the dependence structure widens the null without moving
its centre"* is therefore vacuous: nothing was measured about dependence.

**Fix.** Either delete the row and the paragraph, or replace them with a null
that can see the effect: the **pseudo-star** construction of §G.3.3, which
promotes an *inner-annulus* probe to the star's role and ranks it against the
remaining 511. That one is genuinely informative — it is what yields the 1.2–1.5
tail factor — and it can be block-clustered honestly. Note also that the honest
version will *raise* the expectation, which is in the authors' favour.

---

### S5 — MAJOR. The tail excess does not replicate in the pre-registered hold-out; the body does

This is the single most important distinction in §5.3.1 and it is not drawn.

From `holdout_calib_v381.json` (the **pre-registered** 77-block, 315-window
hold-out):

* **body**: median add-one rank 0.405 against 0.5, KS *D* = 0.109, *p* = 0.0011.
  Replicates convincingly.
* **tail**: 12 pseudo-star first ranks in 5040 trials → factor **1.219**,
  bootstrap interval **0.61–1.87**. *This interval contains 1.* The
  pre-registered sample does **not** establish a tail excess.
* stage-1 outliers in the hold-out: 0 against 0.61 expected.

The factor the paper actually propagates everywhere (*"read as multiplied by
1.4"*; the 4.7 expectation) comes from the **processing-order calibration
sample** — 1326 windows, 327 blocks, 21 216 trials, factor 1.5 (1.2–1.9) — which
§5.3.1 itself describes as *"a weak guarantee, because that set is defined by
processing order rather than in advance."*

§G.3.3 already contains the sentence that makes this matter: *"The tail is
mildly anti-conservative where the body is strongly displaced, and **it is the
tail the candidate screen uses**."* So the paper's strongest pre-registered
result (the body displacement) is not the quantity the screen depends on, and
the quantity the screen depends on is calibrated only on the weak sample.

**Fix.** State it plainly in §5.3.1: the body displacement replicates out of
sample; the tail excess is consistent with unity in the pre-registered sample
(0.61–1.87 on 5040 trials) and is measured at 1.5 (1.2–1.9) only on the
processing-order sample. Then either (a) increase the pre-registered pseudo-star
trial count — every hold-out window retains all 512 probes, so 315 × 512 ≈ 161 000
trials are available rather than 5040, which would tighten the interval by ~5× at
zero cost — or (b) quote the tail factor with the weak-sample caveat attached
everywhere it is used, including §G.3.3's 4.7.

Option (a) is cheap, decisive and entirely within the released products. I would
make it a condition of acceptance.

---

### S6 — MAJOR. P90 is a trigger completeness; the survey's operative gate is the control ring

**Text.** §5.5, *Excluded*: *"For a continuously transmitting, unresolved carrier
… the fine-channel search recovers the signal at least nine times in ten above
P90."* Conclusion 3 repeats it. Appendix B: recovery is defined as *"a threshold
crossing at the injected frequency"*.

**What the data say.** From the released `ctrl_max_snr` column, Class A
(*n* = 403):

| quantity | value |
|---|---|
| median control-ring maximum | **5.79σ** |
| fraction of windows whose ring maximum is **below 5σ** | **0.7 per cent** |
| fraction below 6.1σ (the campaign's pooled P90, Appendix B) | **83 per cent** |
| fraction below 7.5σ | 95 per cent |

So in 99.3 per cent of Class A windows the 5σ trigger is **not** the binding
constraint: step (ii) of the five-step chain, "exceeds all 512 controls", is.
A carrier injected at exactly P90 triggers nine times in ten, but is rank-first
only ~83 per cent of the time, so its probability of reaching even the
*prioritisation* stage is ≈ 0.75, not 0.90. In the worst 5 per cent of windows
(ring max > 7.5σ) a source at P90 would essentially never be promoted.

This is not a small bookkeeping point. The paper's own logic is that a rank-first
outcome is a *necessary* step toward any claim; it follows that the exclusion
statement must be quoted at the completeness of the gate the survey actually
applies, not at the completeness of an internal trigger the paper elsewhere
insists is "not a sensitivity to compare with a transmitter".

**Fix.** Define and quote **P90,promote**: the injected power at which 90 per
cent of trials both cross the trigger *and* exceed that window's own
`ctrl_max_snr`. Every ingredient is already released — the 4032 stratified
trials and the per-window control maxima — so this is an afternoon's work and no
new processing. My rough estimate from the distribution above is a shift of
×1.1–1.3 at the median and considerably more in the upper quartile of windows;
the point is that it is not zero and not currently stated.

Keep P90 as well, clearly labelled as the trigger completeness, since it is what
Fig. 1 needs for comparison with other surveys' 5σ statistics.

---

### S7 — MAJOR. The P90 error budget omits two of the five terms §4 declares, and one of them is a bias

**Text.** §4: *"Five terms enter the systematic budget, each multiplying Smin and
hence EIRP5σ directly: the ALMA absolute flux scale, 5–10 per cent …; residual
atmospheric phase after water-vapour correction and phase referencing; the
primary-beam model at the stellar offset; visibility calibration; and the
instrumental spectral response … The atmospheric term is a coherent point-source
loss exp(−σφ²/2), **5–20 per cent at 230–345 GHz**, common to star and annulus
within the isoplanatic patch and so no threat to exchangeability."*

**Table 14** contains: flux scale ±7, distance ±0.2, injection statistics ±2.0,
pointing ±1.9, combined ±8; then sub-channel phase and window-to-window spread
"carried separately". `p90_budget_v385.py` contains no decorrelation term and no
visibility-calibration term — I grepped for `decorrel|coheren|atmospher|sigma_phi`
and found nothing.

**Two problems, in increasing severity.**

(a) The decorrelation term is 5–20 per cent and is simply missing from the ±8
per cent total. Adding it in quadrature at 10 per cent gives ±13 per cent and at
20 per cent gives ±22 per cent, so the quoted budget understates the
uncertainty by a factor 1.6–2.7. "Common to star and annulus, so no threat to
exchangeability" is true and irrelevant: it is a threat to *sensitivity*, which
is what Table 14 is a budget for.

(b) Worse, it is a **bias and not an error**. Both injection campaigns add the
synthetic tone as a coherent constant, either to already-calibrated visibilities
(Appendix B end-to-end) or to retained per-integration spectra (stratified and
dwell campaigns). An injected tone therefore suffers **no** atmospheric
decorrelation, while a real celestial carrier vector-averages with the residual
phase scatter and loses exp(−σφ²/2) of its amplitude. The measured recovery
curve is consequently optimistic by that factor for a real transmitter, by
5–20 per cent, systematically and in one direction. Note that §5.3.2's
compensating +2 per cent radial term is correctly reported as running "the safe
way"; this one runs the other way and is ten times larger.

**Fix.** Add both terms to Table 14. Better, measure the coherence loss rather
than assuming it: the continuum lane already has 17 detections (Appendix E), and
comparing their image-plane extracted amplitude with a visibility-domain fit
(the machinery now exists — §5.3 ran it on 13 blocks) bounds the decorrelation
empirically on this exact archive. Then correct P90 rather than budgeting it.

Also: the pointing term assumes *"the star sits at the phase centre, where the
beam is flat"*, but §4.3 says 87 of 1655 windows exceed a 2 per cent primary-beam
correction and 73 exceed 10 per cent, with the last retained window at ×1.81.
For those the budget's beam-model term is not negligible and there isn't one.

---

### S8 — MAJOR. "No analysis choice in this paper postdates the reservation"

**Text.** §5.3.1: *"the hold-out rule 5 days after the statistic, and the first
reserved block was searched 3 days after that. **No analysis choice in this
paper postdates the reservation.**"*

This is false as written, and the paper knows it. The local radial
normalisation (`localnorm_all_v385.py`), the visibility-domain test
(`make_vistest_events_v385.py`, `vistest_v385.json`), the drift-strata split
(`drift_strata_v385.py`), the dilution calculation (`visdilute_v385.py`) and the
P90 budget (`p90_budget_v385.py`) all postdate 2026-09-14, and §5.3.2 says so
explicitly of the radius correction: *"It was built after the candidate list was
in hand."*

The sentence is doing important rhetorical work — it is the paper's
pre-registration claim — and a referee who finds one counter-example will
discount the whole passage.

**Fix.** Narrow it to what is true and sufficient: *"No choice that determines
the frozen candidate list postdates the reservation. The radial normalisation,
the visibility-domain test and the sensitivity budget were all built afterwards;
they are reported as robustness checks and no disposition rests on them."* That
is both accurate and adequate.

---

### S9 — MAJOR. Three of the four "unattributed" events are placed in the wrong partition

**Text.** §5.3.1: *"The remaining 3 have no astrophysical attribution: 61 Vir,
HD 14055 and HD 23484 … **One arose in the sample that defined the statistic and
3 in a sample that could not have**, and the measured tail rate predicts 3.7 such
events over 1322 windows against the 3 seen."*
Table 12(b) header row: `Sample: survey | calib. | calib. | calib.`

**What the data say.** `holdout_assignment_v381.json` assigns all four blocks to
the **survey** partition:

```
A002_Xc079b5_X82f   (61 Vir)     -> survey
A002_Xfff3d8_Xd46   (HD 14055)   -> survey
A002_X10b22d7_X2445 (HD 23484)   -> survey
A002_Xff0235_X4a6d  (CP-72 2713) -> survey
```

and all four appear as `stage1_flag = True` rows of `per_target_results_v3.85.csv`,
which is the 1655-window **science sample**, with exactly the T⋆ values quoted in
Table 12 (6.1558, 6.0319, 5.2957, 5.8089).

So the claim that three of the four events arose *out of sample* — which is the
argument that stage-1 status carries no candidate significance, and the reason
§5.3.1 says the finding is *"a result of this work rather than a caveat on it"* —
does not hold as stated. All four are in-sample.

I suspect the history is that these blocks were searched during the
epoch-extension campaign, out of sample at the time, and then absorbed into the
science sample when the sweep completed. If so, the honest framing is that
**they cannot serve both roles**: a window that calibrates the screen cannot also
be a survey event counted against that calibration. Either exclude them from the
science sample and report the survey's unattributed count as 1 (which is what
§5.3.6 and §G.3.3 say — *"the survey expects 4.7 such events and has one"*), or
keep them in the survey and withdraw the out-of-sample argument. The paper
currently does both, in adjacent sections, and the two are not compatible.

**Fix.** Decide. Then make `reproduce_from_catalogue_v385.py` assert that every
event described as calibration-sample is absent from the released catalogue, and
vice versa.

---

## 2. The spatial control screen: does every downstream statement respect its status?

Mostly yes at the level of individual dispositions, and that is genuinely well
done — see §8. The screen is used as a test in exactly one place, and it is the
headline.

### S10 — MAJOR. The aggregate count is a test, and it is the one the abstract makes

Every per-event statement respects the rule. §5.3: *"in 3 of the 4 windows the
control-ring maximum clears it too, so candidacy still turns on the first-stage
star-versus-control comparison."* §5.3.5, HD 48370: *"The rank statistic
identifies nothing here, a stated limitation."* §4.6 steps 7 and 8 both say
"prioritisation, not a test". Good.

But the abstract's *"The remaining 4 have no identification, **against 3.2
expected by chance**"* and Conclusion 2's repetition of it are a **collective
test of the null using the screen**: 3.2 = 1655/513 is the exchangeable rank
expectation, and the sentence asserts that the observed number of rank-first
windows is what that expectation predicts. A screen whose null is admitted to be
wrong by a measured factor of 1.2–1.9, and whose class-conditional expectation
differs by a factor 4 from the pooled one, cannot supply the yardstick for its
own yield without saying which yardstick it is using (**S3**).

This is not fatal — a collective calibration is a legitimately different thing
from a per-window significance, and the paper has the material to do it properly.
But the abstract currently reads as though the screen is calibrated, and §5.3.2
spends two pages showing it is not.

**Fix.** In the abstract, replace the bare comparison with the measured one and
name it: *"…against 4–5 expected from the measured false-alarm rate of the
control screen, which is 1.2–1.9 times the exchangeable rate."* Or drop the
number from the abstract entirely and let §5.3 carry it, which is what the
paper's own epistemics suggest.

### S11 — MINOR. Two places where the screen is quietly re-promoted

* §5.3.4: *"Against the survey background the Band 3 peak T⋆ = 30.76 is matched
  or exceeded by 0 of the 1655 per-window control maxima, **add-one p = 0.001**,
  and the Band 6 peak T⋆ = 11.68 by 16 of them, **p = 0.010**."* I reproduce both
  counts exactly from the catalogue (0 and 16 of 1655). But this is a rank
  against *other windows'* control maxima — windows with different
  channelisation, integration time, band and field, i.e. a reference set that is
  emphatically not exchangeable with the β Pic Band 3 window. Calling the result
  a *p*-value contradicts the paper's own rule. It is also unnecessary: β Pic's
  attribution rests on velocity coincidence across two transitions and eight
  blocks, which is overwhelming. Recommend deleting the two *p*-values or
  relabelling them "rank among the survey's control maxima".
* Data Availability: *"It holds the per-window search products for all 1655
  windows, each with its 512 control statistics, so **every rank and p-value in
  this paper is recomputable**."* The catalogue column is literally named
  `p_rank_addone`. Rename to `rank_addone` and drop "p-value" from the sentence;
  otherwise a reader who takes the column at face value does the exact thing
  §4.2 and Table 2 spend paragraphs forbidding.

---

## 3. Sensitivity and completeness

### S12 — MAJOR. The window-to-window bracket is "not an error" in Table 14 and a factor two of spread in §5.5

Table 14 lists *"Window-to-window spread, not an error: −52/+35 per cent"* and
its caption says folding it into the total *"would double-count them against the
per-window bracket in the catalogue"*. §5.5 says *"a single quoted threshold
should be read with a factor of about two of spread around it"*. Conclusion 3
says *"That threshold carries a ±8 per cent calibration budget **and** a
window-to-window spread of ×0.48–×1.35."*

These are not the same stance, and the difference is not cosmetic. The
×0.48–×1.35 bracket is measured as the dispersion of the recovery curve's
position across the 28 injected configurations. For a window that *was* injected,
it is a dispersion. For the other 375 Class A windows — including, by Appendix B's
own accounting, the ones the bracket *extrapolates* to — it is an **uncertainty
on the transfer**, i.e. an error on that window's P90, and it dominates the ±8
per cent by a factor five.

Abstract wording compounds this: *"with a window-to-window scatter of
×0.48–×1.35"*. A reader will take "window-to-window scatter" to mean the spread
of thresholds between windows, which is three decades (6.3×10¹³ to 1.1×10¹⁷ W)
and already given per window in the catalogue. It is neither that nor ±8 per
cent; it is the transfer uncertainty on the completeness function.

**Fix.** Use one name for it throughout — *completeness-transfer uncertainty* —
say once that it is an error for un-injected windows and a measured dispersion
for injected ones, and quote the total uncertainty on a single window's P90 as
the quadrature combination for injected windows and the bracket for the rest.
Appendix B already knows which windows are interpolated and which extrapolated
(*"the transfer bracket should be read as measured for the 113 windows and
assumed for the rest"*) — carry that distinction into the catalogue as a flag.

### S13 — MAJOR. "∼1250× deeper than Mason et al." is not like-for-like, and is hard-coded

§6.2: *"Against the sole prior ALMA-archival search (Mason et al. 2024, 28
bycatch targets at ≥1.01 kpc), the 87 systems here reach median per-target
thresholds ∼1250× deeper."*

`make_numbers.py:116`: `('MasonRatio', '1250')` — a typed constant, not derived.

Three problems:

1. **Which quantity, and it does not reproduce.** The obvious constructions from
   the catalogue give 7×10¹⁷ / (median per-system best nominal trigger
   4.1×10¹⁴) = **1695**, or 7×10¹⁷ / (median nominal trigger over all windows
   7.1×10¹⁴) = **990**. Neither is 1250. Whatever the intended construction, it
   is on the **nominal trigger** — the quantity §4 forbids quoting (*"The two
   numbers to quote are Peff and P90"*). On the per-system P90 median of
   1.3×10¹⁵ W the ratio is ≈ 540; on the per-window P90 median of 2.4×10¹⁵ W it
   is ≈ 290.
2. **It is the d² factor, and less than it.** The median searched system is at
   19.6 pc, so (1010 pc / 19.6 pc)² = **2646**. A ratio of 1250 (or even 1695)
   against a geometric expectation of 2646 means this survey is, in *received
   flux density*, roughly 1.5–2 times **shallower** than Mason et al. That is an
   entirely respectable position for a multi-band archival sweep at 4× the
   frequency and should be stated, not buried.
3. Fig. 1 goes to admirable lengths — a caveat printed on the ordinate itself —
   to stop exactly this comparison being read as like-for-like. §6.2 then makes
   it in one clause with no caveat. The two are inconsistent in tone and the
   text one will be quoted.

**Fix.** Derive the ratio from the catalogue at P90, state the distance
decomposition in the same sentence, and cross-reference Fig. 1's caveat.

Related, and in the abstract: *"…6.3 × 10¹³ W at the deepest, with a
window-to-window scatter of ×0.48–×1.35; **the Arecibo planetary radar radiated
2.0 × 10¹³ W**."* The juxtaposition invites the reading that the survey is within
a factor three of Arecibo. §4.3 and §6.1 correctly explain that this is a
2.38 GHz power scale, that gain scales as ν², that the same aperture and
transmitter at 230 GHz radiates ~2×10¹⁷ W, and that read on Peff *zero* systems
reach the Arecibo figure. The abstract has the raw number and none of the
qualification. Either qualify it in one clause or drop it.

### S14 — MINOR. Duty-cycle and drift selection functions are measured on classes other than the one they are applied to

* **Duty cycle.** Fig. 9 and the 3888-trial dwell campaign use *non-drifting*
  carriers — §4.5: *"The injected carriers do not drift, so what is measured
  across 12 configurations is the persistent and partial-dwell non-drifting
  class."* Table 7 is scrupulous: the "Class A drifting / dwell" cell reads
  **no**. The abstract is not: *"Sensitivity also falls steeply below a duty
  cycle of about a tenth"* is stated unconditionally, and §5.5's *"or on for less
  than about a tenth of the time"* sits in the *Excluded/Not excluded* box for
  the primary experiment. The transfer from non-drifting to drifting is
  plausible — dwell enters through Eq. 5's √(f·N) and the de-drift stack is the
  same sum — but it is a transfer and is not flagged where it is used.
* **Near-static Class A.** Table 7's "Class A near-static / threshold" cell reads
  **no** (measured after the baseline step only). §5.5's *Excluded* box covers
  *"a continuously transmitting, unresolved carrier … inside the linear-drift
  grid"*, which includes zero drift. So the exclusion claim covers a morphology
  whose threshold completeness Table 7 declares unmeasured.

**Fix.** One sentence in §5.5 and one in the abstract restricting the duty-cycle
statement to the measured class, and one in §5.5 noting that the ν̇ ≈ 0 corner of
Class A inherits its completeness from the Class B measurement.

### S15 — MINOR. Recurrence coverage is quoted for the wrong sample

§6.2: *"only 54 of the 87 systems, 62 per cent, were searched in more than one
execution block."* Conclusion 4: *"33 of 87 systems have only one epoch."*

Both are correct for the whole sample (I reproduce 54/87 from the catalogue). But
the confirmation test that defines a candidate applies to the **primary
experiment**, and there the figure is **41 of 65 Class A systems** with more than
one Class A block — and by the paper's own `confirmability_v384.json`, **40 of 65
systems** and 349 of 403 windows are confirmable. The relevant figure is smaller
still if the repeat must cover the same *tuning*, which is what a recurrence test
requires.

**Fix.** Quote the Class A figure in §6.2 and Conclusion 4, with the whole-sample
figure in parentheses. `confirmability_v384.json` already has it.

---

## 4. Attribution of the flagged events

### S16 — MAJOR. HD 14055's "displaced" verdict is over-read, and the visibility test is used asymmetrically

**Text.** §5.3: *"HD 14055's imaginary part is 3.2σ from zero, **which emission at
the stellar position cannot produce**, so that excess is displaced from the
stellar position rather than absent."* Repeated in Table 9 ("displaced: phase
inconsistent"), Fig. 7's caption, and §4.2 (*"an imaginary part inconsistent with
zero is positive evidence that the excess lies somewhere other than the star"*).

Four objections, in order of force.

(a) **The statement is too strong.** Emission at the stellar position produces a
zero imaginary part only under perfect phase calibration and a perfectly known
position. Residual antenna-based phase error, a small astrometric error in the
proper-motion propagation, and any *other* emission in the field all put signal
into the imaginary part. The test measures "is there a phase-coherent excess at
the assumed coordinates", not "is the excess at the star".

(b) **σ is internal.** Every one of the 13 rows in Table 9 reports χ²/ν = 1.00
exactly. That is the signature of an uncertainty estimated as the standard error
over the visibilities themselves, in which case χ²/ν = 1 by construction, the
quoted σ contains no systematic phase term, and it assumes the 12 375–405 860
visibilities are independent. They are not: the same sky structure and the same
antenna phase errors are common to all baselines and all times in a block, so
the effective N is far smaller than the nominal one and every significance in
Table 9 — including the 3.2σ, the 7.9σ and the 53σ — is inflated by an unknown
factor.

(c) **Trials.** Thirteen events × two quantities = 26 numbers. A two-sided 3.2σ
has p = 1.4×10⁻³; over 26 looks the expected number at that level is 0.036, so
one 3.2σ deviation is a ~3.5 per cent post-trials event. Defensible, but it is a
*marginal* result being used to assign a categorical verdict.

(d) **The asymmetry is the real problem.** The paper's own §5.3 establishes that
*"a uniform single-channel test can lose such a carrier by as much as ×2.0–×4.7
in signal-to-noise"* for a drifting carrier, and uses this to decline to draw any
conclusion from the other three null results. HD 14055 has the **largest real
part of the four** (+2.5σ, against its controls' +1.1). Under the paper's own
dilution factor, +2.5σ diluted corresponds to a 5–12σ undiluted source — which
would make HD 14055 the *most* star-like of the four, not the one that is ruled
out. The paper applies the dilution caveat to the three nulls and not to the one
positive-looking real part, and reaches a verdict from the imaginary part of the
same under-sensitive estimator.

**Fix.** Run the drift-following, continuum-subtracted fit — the one that gave
CP−72 2713 its 5.5σ — on all four events. §5.3 already says *"A successor
analysis should run the drift-following, continuum-subtracted fit on every
candidate from the start; **the machinery now exists**."* All four blocks have
already been recalibrated for Table 9. There is no reason to defer it to a
successor, and a referee will ask for it (see **M1**). Until then, HD 14055's
verdict should read *"a 2.5σ real part with a 3.2σ imaginary part; a uniform
single-channel test at this significance does not localise the excess"*, and the
categorical "displaced" should be withdrawn.

### S17 — MAJOR. The CP−72 2713 5.5σ fit is not independent evidence, and Conclusion 2 reads as though it were

**Text.** Conclusion 2: *"the one event given a drift-following fit **does show a
source at the star at 5.5σ**."* §5.3, in bold: *"for the one unattributed event
tested with the more sensitive estimator, the visibility domain does not exclude
a point source at the star — it supports one."*

The fit is performed on the same 405 860 visibilities, in the same channel, at
the same drift, at the same position, at a cell that was **selected as the
maximum over ~2.6×10⁵ channel×drift cells** by the image-plane statistic that
produced the 5.81σ in the first place. It is therefore not an independent
measurement and it carries the full search trials factor, uncorrected. §G.5 shows
the authors understand the danger — *"At 4 control frequencies the statistic at
the star never exceeds 1.7σ while the maximum over 961 trial positions reaches
4.4–5.4σ"* — but that control addresses the *position* grid, not the
*frequency×drift* grid that selected the cell.

What the fit legitimately establishes is **morphology**: the excess that the
image plane found is consistent with a point source at the stellar coordinates
rather than with extended emission, a sidelobe or a deconvolution residual. That
is a real and useful result, and it is the one Conclusion 2 should state.

**Fix.** Rephrase to *"the excess is point-source-like and centred on the star,
as an image-plane extraction at that position would require; this confirms the
morphology of the excess but is measured on the same visibilities and adds no
independent significance."*

### S18 — MAJOR. Table 11's ∆v is not the quantity its caption and disposition rule describe

Table 11's caption: *"∆v the offset of that channel from the nearest laboratory
rest frequency of the masked species **in the star's frame** … A pair is
dispositioned as circumstellar or foreground emission when |∆v| ≤ 50 km s⁻¹ and
independent evidence exists."*

Table 11 gives β Pic B3 ∆v = −28 and β Pic B6 ∆v = −28. **Table 21 gives the
stellar-frame offsets for the same two windows as −0.39 and −0.29 km s⁻¹**, after
the topocentric → barycentric → stellar chain. The catalogue's
`line_offset_kms` matches Table 11 (−27.76, −28.44), i.e. Table 11 is carrying
the **topocentric** offset, before the barycentric term (−7.9 km s⁻¹) and the
systemic velocity (+20.0 km s⁻¹) are applied.

Consequences:

* a reader applying the caption's own rule to the caption's own column gets the
  right answers only by accident (|−28| ≤ 50 happens to hold);
* HD 14055's −12 161 km s⁻¹, 61 Vir's +449 and HD 23484's +328 are topocentric
  offsets from the *nearest catalogued transition of the masked species*, which
  is not a physically meaningful discriminant and invites the reading that these
  events are wildly far from any line when the stellar-frame figure is what
  matters;
* the mask itself is applied correctly (§5.3.7, Appendix D), so no disposition
  moves. This is a presentational defect with inferential force, not a
  processing error.

**Fix.** Add the stellar-frame offset as a column (Table 21's chain already
computes it for four windows; the frame chain is in the pipeline) or retitle the
column "topocentric offset" and state the rule against the correct quantity.

### S19 — MAJOR. The line-mask robustness check is one-sided

§4 and §5.3.7: *"reclassifying all 75 crossings at ±20, ±30, ±50 and ±100 km s⁻¹
**admits no new unattributed outlier**, and at every width CP−72 2713 remains the
only unmasked one."*

The check tests only whether narrowing/widening the mask *adds* unattributed
events among the unflagged crossings. It does not test whether narrowing *removes
attributions from the nine events that have them*. On the ∆v column as tabulated
(and see **S18** for what that column is), at ±20 km s⁻¹:

* HD 48370 (∆v = −34) falls outside the mask;
* five β Pic Band 3 windows (−23.3 to −27.8) fall outside;
* two β Pic Band 6 windows (−28.4, −28.6) fall outside.

That would take the unattributed count from 4 to as many as 12 on the mask
criterion alone. The paper's actual attributions survive, because they rest on
independent evidence (Cataldi et al. for HD 48370; Matrà et al. and Dent et al.
plus the stellar-frame concordance for β Pic) rather than on the mask — which is
exactly what Table 11's caption requires ("and independent evidence exists"). But
the robustness sentence as written claims something the check did not test, and
the ±50 km s⁻¹ half-width was, by the paper's own disclosure, *"adopted after the
β Pictoris crossings had been seen"*. A hostile referee will join those two
sentences.

**Fix.** Run the check in both directions and report it as such: *"at every width
from ±20 to ±100 km s⁻¹ no new unattributed outlier is admitted; narrowing to
±20 km s⁻¹ removes the mask-based component of N attributions, all of which
retain their independent astrophysical evidence, so no disposition depends on the
half-width."* Since **S18** shows the tabulated ∆v is topocentric, re-run the
check on the stellar-frame offsets, where β Pic sits at 0.9 per cent of the
tolerance and the conclusion will be much cleaner.

### S20 — the β Pictoris positive control: valid for localisation, invalid for what §5.3.4's opening sentence claims

§5.3.4 opens: *"**A search that finds nothing must show that it could have found
something, and this is where that is done.** β Pictoris is the survey's positive
control."*

β Pic CO demonstrates, convincingly: that the extraction lands on the right sky
position; that the frame chain is right to sub-km s⁻¹; that the frozen pipeline
recovers the same feature blind in two transitions across 8 blocks and 8.4 yr;
and that the recurrence machinery preserves a genuine repeat. Those are real and
the paper is right to lean on them. §5.3 states the scope correctly: *"a positive
control for localisation … and not for narrowband-carrier sensitivity."*

But the thing the survey is looking for is an **unresolved, channel-confined,
drifting carrier**, and β Pic CO is none of those: it is resolved (it fills the
control annulus — §5.3.4 notes the ring outshines the star by 1.5× in the
repeating Band 6 window), it is 8.9–15.2 km s⁻¹ wide (114 formal ≥5σ crossings in
one window, §G.3), and it has zero drift. It therefore controls neither the
sensitivity to the target morphology nor the *screen's* behaviour toward it — in
fact it demonstrates the screen behaving in the opposite way, losing power
against extended emission.

The opening sentence promises more than the section delivers, and the object that
actually discharges the promise is the injection campaign, which is in an
appendix. MINOR as a scientific matter, MAJOR as a matter of where a referee's
attention gets directed.

**Fix.** *"A search that finds nothing must show that it could have found
something. For the target morphology that is the injection campaign (§4.5,
Appendix B); for the astrometry, the frame chain and the recurrence machinery it
is β Pictoris, and this section is the latter."*

### HD 48370 — the foreground argument is sound

I looked hard for a way to break it and could not. It is over-determined:

* velocity coincidence with Cataldi et al. (2023)'s reported CO(2→1) at
  v_bary ≈ 41 km s⁻¹, recovered independently at +41.2 km s⁻¹ through this
  paper's own frame chain;
* a flat rotation curve reaches that velocity only at a kinematic distance of
  2.07 kpc, so nothing circumstellar can produce it;
* the same block's ¹³CO(2→1) window has a control maximum of 20.4 against 4.6
  at the star, i.e. bright ¹³CO in the field and none at the star, resolved
  1.7 beams away;
* Cataldi et al. report the disc itself undetected in CO and in C, and the Band 8
  [C i] tuning shows no line at the star (§G.5);
* the visibility test returns a 53σ real part with a 7.9σ imaginary part, the
  displaced-source signature;
* the radial-noise correction removes the flag entirely, and the local scramble
  test fails outright for the documented reason (extended coherent emission).

Six independent handles, all agreeing. I would accept this disposition without
further work. The one caveat worth keeping is the honest one the paper already
makes: the rank statistic contributes nothing here, and the case is a
demonstration that the screen cannot handle beam-filling emission.

---

## 5. Overclaiming: sentence by sentence

Only claims that exceed the evidence are listed. Sentences I checked and found
properly supported are in §8.

| # | Sentence | Why it exceeds the evidence | Supportable version |
|---|---|---|---|
| O1 | *(Abstract)* "The remaining 4 have no identification, **against 3.2 expected by chance**" | 3.2 is the exchangeable rate the paper measures to be wrong by ×1.2–1.9, pooled over a class that produces no flags. See **S3**, **S10** | "against 4–5 expected from the screen's measured false-alarm rate" — or drop the number from the abstract |
| O2 | *(Abstract; §4.6 step 10; Concl. 2)* "the other three have no second epoch, so no recurrence test exists for them" | False; 4, 17 and 3 further blocks exist at the same tuning. See **S1** | "none of the four recurs; for three of them the non-recurrence is measured over 3–17 further blocks of the same tuning" |
| O3 | *(Abstract)* "an unresolved carrier drifting within the searched range **is recovered nine times in ten above** 2.4×10¹⁵ W" | P90 is trigger completeness; promotion also requires beating a ring whose Class A median is 5.79σ. See **S6** | "…triggers the search nine times in ten above 2.4×10¹⁵ W; the power at which it would also have been promoted past the spatial screen is P90,promote" |
| O4 | *(Abstract)* "…6.3×10¹³ W at the deepest …; **the Arecibo planetary radar radiated 2.0×10¹³ W**" | Bare juxtaposition; §6.1 shows that on the comparison a transmitter power calls for, 0 of 87 systems reach it | Add "at 2.38 GHz; scaled to these frequencies at fixed aperture the same transmitter radiates ~2×10¹⁷ W" or delete |
| O5 | *(§5.3; Table 9; Fig. 7)* "HD 14055's imaginary part is 3.2σ from zero, **which emission at the stellar position cannot produce**" | Phase-calibration residual, astrometric error and co-located field emission all produce one; σ is internal and assumes independent visibilities; ×2–4.7 dilution is not applied to this event. See **S16** | "a 2.5σ real part with a 3.2σ imaginary part; at this significance the uniform test does not localise the excess" |
| O6 | *(Concl. 2)* "the one event given a drift-following fit **does show a source at the star at 5.5σ**" | Same visibilities, same cell, selected by the image-plane maximum over ~2.6×10⁵ cells. See **S17** | "…is consistent with a point source at the stellar position; this confirms the morphology, not the significance" |
| O7 | *(§5.3.1)* "**No analysis choice in this paper postdates the reservation**" | The radial normalisation, visibility test, drift strata and P90 budget all do. See **S8** | "No choice that determines the frozen candidate list postdates the reservation" |
| O8 | *(§5.3.1; Table 12)* "One arose in the sample that defined the statistic and **3 in a sample that could not have**" | All four blocks are `survey` in `holdout_assignment_v381.json` and all four rows are in the released catalogue. See **S9** | Either exclude them from the survey count, or withdraw the out-of-sample claim |
| O9 | *(§5.3)* "**2 are observed**, and P(≥2)=0.87 on the resampled null. The unexplained population is what chance predicts" | Observed count hard-coded at 2; the paper reports 4. See **S2** | "4 are observed, and P(≥4) = 0.46" |
| O10 | *(Table 8 caption)* "**the block-resampled figure is the one the text uses**, because it is the only one that respects the dependence structure" | The text uses 3.2 everywhere; and the block resampling respects no dependence, its per-window rate being identically 1/512. See **S3**, **S4** | Delete the row, or replace with a block-clustered pseudo-star null |
| O11 | *(§4; §5.3.7)* "Reclassifying all 75 crossings at ±20 to ±100 km s⁻¹ … **admits no new unattributed outlier**" | Only tested in the direction of gains; at ±20 several attributed windows lose their mask coincidence. See **S19** | State the two-sided result |
| O12 | *(§6.2)* "the 87 systems here reach median per-target thresholds **∼1250× deeper**" | Hard-coded; on the trigger not P90; smaller than the d² ratio, so in received flux this survey is the shallower of the two. See **S13** | Derive at P90 and give the distance decomposition |
| O13 | *(§5.3.4)* "**A search that finds nothing must show that it could have found something, and this is where that is done.** β Pictoris is the survey's positive control" | β Pic CO is resolved, 9–15 km s⁻¹ wide and undrifting — none of the target morphology. See **S20** | Split the claim between the injection campaign and β Pic |
| O14 | *(Abstract; §5.5)* "Sensitivity also falls steeply below a duty cycle of about a tenth" | Measured on non-drifting injections only; Table 7 marks the Class A drifting × dwell cell unmeasured. See **S14** | Restrict to the measured class, or state the transfer |
| O15 | *(§5.3.4)* "add-one p = 0.001 … p = 0.010" for β Pic against the survey's control maxima | A rank in a non-exchangeable reference set, called a p-value. See **S11** | Relabel as a rank, or delete — the attribution does not need it |

---

## 6. Missing controls: what a hostile referee will demand

Ranked by how much each would change my confidence, with a judgement on whether
it is possible with the data described.

### M1 — Drift-following, continuum-subtracted visibility fit on **all four** unattributed events. *Possible now.*

This is the first thing I would ask for and I do not think the paper can be
accepted without it. §5.3 concedes that the uniform single-channel test is
under-sensitive by ×2.0–×4.7 to the very morphology the survey is searching for;
it then reports "0 of 4 show emission at the star" using that test, while the one
event measured with the *sensitive* estimator turns out to show a 5.5σ point
source on the star. The obvious inference — that the uniform test may be hiding
the same thing in the other three — is not excluded anywhere.

All four blocks have already been recalibrated from the raw archive for Table 9
(§5.3: *"We recalibrated all 13 stage-1 execution blocks from the raw archive
data"*), and §5.3 states that *"the machinery now exists"*. There is no barrier.
The result would either close the four events properly or produce the paper's
most interesting figure.

### M2 — Class-conditional, measured-rate null with the correct observed count. *Possible now, from released products.*

Replace the six competing expectations (**S3**) with one: Class A windows only,
per-window pseudo-star rate measured on the pre-registered hold-out, block
clustered, compared against the observed 4. Every input is in
`frozen_export_v3.81_survey.json` and `holdout_export_v381.json`. The answer may
well be uncomfortable (P(≥4) ≈ 0.03 on the Class A null), and reporting it
honestly would be stronger than the present arrangement.

### M3 — Completeness at the promotion gate, not the trigger. *Possible now.*

Rescore the 4032 stratified trials against each window's own `ctrl_max_snr` and
publish P90,promote alongside P90 (**S6**). No new processing.

### M4 — A displaced-position negative control run end to end. *Partially possible.*

The pseudo-star test ranks a control probe against the other controls, which
cannot see a centre-versus-annulus asymmetry (Appendix F concedes this: *"that
geometry cannot by itself detect a centre-versus-annulus asymmetry"*). The test
that can is to re-run the **entire pipeline** — extraction, baseline, de-drift,
ranking — with the nominal "stellar" position displaced by a fixed few arcsec,
on a sample of windows, and count the stage-1 flags that result. That measures
the flag rate at a position with the star's *radial* placement but no star, which
is precisely the quantity §5.3.2 needs and currently infers from an
extrapolation of the radial profile inward from u = 0.14 to u = 0.003.

It requires re-extraction from the measurement sets, so it is not possible
survey-wide from the frozen products; but it is possible on the 13 recalibrated
stage-1 blocks and on any subset the authors are willing to re-download. Even 50
windows would bound the extrapolation.

### M5 — Per-hand (XX/YY) split on the four unattributed events. *Possible now, four blocks.*

The paper makes the argument itself (§4, §6.4): a coherent artificial carrier is
more likely to be polarised than the astrophysical background, and 198 of 200
resolved blocks deliver both parallel hands. For a *noise* excursion the two
hands are independent and the excess should appear in one; for a real celestial
signal it should appear in both at the right ratio. All four blocks are already
recalibrated. This is the cheapest discriminating test available and it is
deferred to §6.4 as future work.

### M6 — Coherent-loss (decorrelation) measurement against the continuum detections. *Possible now.*

Bounds the bias in **S7** empirically on this archive: 17 continuum detections
exist; compare the image-plane extracted amplitude with a visibility-domain
point-source fit for each, and the ratio is the coherence loss the injections do
not carry.

### M7 — Stacked search across the repeat blocks of HD 14055. *Possible now.*

The catalogue shows 18 science-sample windows of HD 14055 at the same B7 tuning,
of which four besides the flagged one cross 5σ at the star. A persistent carrier
would stack up across them; noise would not. This is the strongest recurrence
test available anywhere in the survey and the paper does not know it has it
(**S1**).

### M8 — Blind injection audit. *Possible, but expensive.*

Inject signals into a randomly chosen, analyst-blind subset of real windows at a
range of powers, run the full unmodified chain including the screen and the
disposition rules, and unblind at the end. This is the only test that measures
the *whole* procedure — including human classification — rather than one stage
of it, and its absence is why Table 7's cells must be read individually. I would
not require it for this paper, but I would require the paper to say it has not
been done, which §4.5 nearly does.

---

## 7. Residual items from round 1 that bear on the inference

Raised here only because they change what a number means, not for arithmetic.

* **S21 — MINOR.** §5.3.1: *"a star-clustered bootstrap placing the median at
  0.405 (95 per cent interval 0.42–0.46)"*. Macros `\HoRankMed` = 0.405,
  `\HOBootLo` = 0.42, `\HOBootHi` = 0.46 — the interval excludes its own point
  estimate, which no percentile bootstrap of the same statistic on the same
  sample can do. The block-clustered interval quoted three paragraphs earlier
  (0.341–0.458) does contain it. Round 1's C11 was dismissed on the basis of the
  block-clustered interval; the star-clustered pair is still typeset. One of the
  two is computed on a different sample than the median it is attached to.
* **S22 — MINOR.** Table 11's caption gives *p* = 0.40 for "4 unattributed
  consistent with 3.2 expected". I reproduce it as P(≥4 | Poisson 3.2) = 0.398.
  It is a one-sided tail probability: a *failure to reject*, not evidence of
  agreement, and it is computed on the null the paper disowns (**S3**). On the
  Class A null with the measured tail it is 0.026. The word "consistent" should
  not do this much work in a caption.

---

## 8. What survived scrutiny

I want this on the record, because the list is long and several of these are
better than the field's norm.

**Sensitivity chain.**

* The **P_trig → P_eff → P90 chain is internally consistent and correctly
  reasoned.** I checked the one place it could have gone wrong: whether the ×1.2
  from the injection campaign multiplies the trigger or the response-corrected
  threshold. Appendix A states that the injections *"deposit an unsmoothed
  delta-in-channel tone, so the recovery curves … carry the same bias and the
  end-to-end check cannot see it"*, which means the injected amplitude is
  post-response and P90 = 1.2 P_eff is right, not 1.2 P_trig. This is a subtle
  trap and the paper is on the correct side of it, explicitly.
* **The Hanning response factor is measured, not assumed**: ×2.02–×2.69 by
  injection against ×2.29 analytic, agreeing at the median to 1 per cent, with
  the lag-1 autocorrelation of the retained residuals (0.65 measured against
  0.667 predicted) as an independent confirmation of the smoothing state. That is
  a proper closure.
* **Fig. 1 is exemplary.** Printing "NOT a like-for-like sensitivity axis" on the
  ordinate, plotting the channel-width panel beside it, and stating "We know of
  no way to convert the published values to a common completeness" is exactly
  right, and more honest than most published EIRP-versus-distance plots. The
  problem is §6.2 (**S13**), not the figure.
* The **withheld ε Eri windows** — declining to quote among the deepest
  thresholds in the survey because the beam model cannot be defended past the
  first sidelobe — is a decision made against the authors' own interest, on a
  rule that binds prospectively (response floor 0.5, with the data bimodal and
  nothing in the gap). Exactly right.
* The **ν̇ grid at constant acceleration** rather than constant drift rate, so the
  boundary is one number across the band, is the correct physical
  parameterisation, and Fig. 12 presents it as a selection function rather than a
  prior.
* The **linewidth convention** (Eq. A1) and the refusal to project an
  Hz-resolution sensitivity by √∆ν scaling over six decades.

**Statistical design.**

* The **region-maximum argument is correct and decisive.** Under any noise
  distribution, a region maximum over n_src positions ranked against n_ctrl
  single positions exceeds them with probability n_src/(n_src+n_ctrl); with
  135 and 512 that is 21 per cent, a floor. It is combinatorial, refers to no
  window, and the symmetric single-position form is therefore the conservative
  choice. Table 22 audits the difference window by window, and §G.2's fully
  symmetric variant on seven reprocessed windows (T⋆ = 3.7–4.9 against control
  maxima 6.7–7.7, p = 0.81–1.00) supports the choice. I checked the catalogue:
  both statistics are released per window, so the dependence on the choice is
  auditable, as claimed.
* The **refusal to adopt the radius-corrected statistic** after seeing the
  candidate list, on the grounds that *"a detection statistic chosen once the data
  are seen is the kind of choice this paper argues against elsewhere"*, and the
  reporting that it moves the survey median *away* from 0.5 (0.445 → 0.432). This
  is the paper reporting a result that hurts it, and reporting it in the
  direction the measurement gives.
* The **exchangeability failure is presented as a finding rather than a caveat**,
  with the mechanism identified (radial noise normalisation), an independent
  confirmation (pseudo-stars displaced as far as real stars, so the effect is
  positional and not stellar), and a correct conclusion about the remedy being
  physical rather than statistical.
* The **pre-registration ordering is properly documented and externally
  corroborated** — statistic 2026-09-09, criteria 2026-09-11, hold-out rule
  2026-09-14, first reserved block searched 3 days later, with the caveat that
  local commit timestamps are rewritable and the appeal to server-side push times
  and the Zenodo mint date. That is the right level of paranoia. The hold-out rule
  itself (`sha256(uid)[:8] mod 5`, block-level, with two identifier-only guards)
  is sound and recomputable from the UIDs alone; I confirmed the assignment file
  has 484 entries, 77 held out, 15.9 per cent.
* The **refusal to convert the null into an occurrence fraction**, with the
  reason given (the per-system union is 1.7 GHz against ALMA's ~75 GHz of tuning
  range, so the bound vanishes under any broader prior). Many SETI papers cannot
  resist this; this one explicitly declines.
* The **trials decomposition in Table 19** — separating cell multiplicity within a
  crossing window (3.0, predicted by the 2.67 Hanning over-count) from the
  window-level factor (1.9) — is a clean piece of accounting, and the closure
  against the control maxima (477 predicted, 471 observed, 1 per cent) is a real
  empirical check of the budget.
* Recognising that **"5σ" is a trigger and not a tail probability**, that
  T(x) is not shown to be Gaussian or χ-distributed, and carrying that
  consistently into the glossary and Table 2.

**The CP−72 2713 case.**

* The construction **"a persistent emitter at the first block's flux would have
  appeared at T⋆ = 6.21"** is exactly the right way to convert a non-detection
  into a statement about what would have been seen, and Table 13 gives the reader
  both sides. So is the distinction between the 4.6σ two-measurement inconsistency
  and the 6.8σ obtained by taking the first flux as exact, *with the note that the
  latter flatters the test because that flux is the window maximum and biased
  high*. That is a level of care I rarely see.
* The refusal to call two blocks 2.05 h apart independent epochs, and the
  repeated, unambiguous statement that *"two executions cannot separate a noise
  excursion from an intermittent emitter, and we do not claim they do."*
* The solar-system check, with the control that the same SkyBoT query on the
  ecliptic returns 118–444 objects, so a null return measures the field and not a
  broken query.

**Scope statements.**

* The ten-item *"Nothing in this paper bounds the prevalence of…"* list in §5.5 is
  the best part of the paper and should not be trimmed.
* The M-dwarf demographic caveat (21 of 5908 within 40 pc; *"This result therefore
  carries very little demographic weight for the local habitable-zone planet
  population"*), stated in the abstract as well as the conclusions.
* Treating the line mask as **excluded search space rather than a veto**, with the
  cost quantified per band (Table 18) and the explicit observation that the fine
  experiment pays three times the fractional price because its coverage is
  concentrated in line-tuned windows. The accompanying recommendation — that a
  successor should attach a lower prior rather than delete channels — is the right
  design advice.
* The **Stokes-I disclosure**, including the unusually candid *"one that lost a
  hand would be √2 less sensitive than its threshold implies, with nothing here
  to catch it."*
* *"work-list complete, archive-incomplete"* and the explicit refusal of
  "target-complete", with the 656/484/404/177 ledger closing.

**Attribution.**

* **HD 48370** — sound and over-determined; see §4 above. I would accept it.
* **β Pictoris as a localisation and recurrence control** — valid for those two
  things, and the velocity concordance (+19.6 to +20.7 km s⁻¹ across 4 blocks and
  8.4 yr, within 0.7 km s⁻¹ of systemic, in two transitions) is as clean an
  astrophysical identification as this kind of work produces. The three
  independent arguments in §5.3.4 (frequencies agree to 1.00 channel after
  removing each block's tuning; velocities agree across transitions and epochs;
  the lines are 10.8–15.2 km s⁻¹ wide against the single channel a carrier
  occupies) are each sufficient and together decisive.
* The observation that the screen **loses** power against emission filling the
  annulus, demonstrated on the β Pic repeat block where the margin collapses from
  1.28× to 1.06× and the ring maxima stand at 9.12 and 8.41 against 99th
  percentiles of 6.11 and 5.99 — reported as a limitation of the method rather
  than glossed.
* The insistence that *"a detection statistic should not know whether its target
  is astrophysically interesting, or a real transmitter would be penalised for the
  company it keeps"* (§6.4). Correct, and worth keeping verbatim.

---

## 9. Indexed summary

| ID | Rank | Area | Issue | Fixable from released products? |
|---|---|---|---|---|
| S1 | MAJOR | attribution | "no second epoch" for 3 of 4 events; catalogue has 4, 17 and 3 repeat blocks. Generator returns `[]` when `f_cross_GHz` is blank | Yes |
| S2 | MAJOR | statistics | Block-bootstrap observed count hard-coded at 2; the survey reports 4. P(≥2)=0.87 should be P(≥4)≈0.46 | Yes |
| S3 | MAJOR | statistics | Six competing chance expectations (0.79 / 3.1 / 3.2 / 3.5 / 3.9 / 4.7); abstract uses the exchangeable one the paper disowns; pooling Class B inflates it ×4 | Yes |
| S4 | MAJOR | statistics | The "block-resampled null" is degenerate — per-window rate identically 1/512, verified on 1698/1698 windows; preserves no dependence | Yes |
| S5 | MAJOR | statistics | Tail excess does **not** replicate in the pre-registered hold-out (1.22, CI 0.61–1.87); the propagated 1.4–1.5 comes from the processing-order sample | Yes — 161 000 trials available vs 5040 used |
| S6 | MAJOR | sensitivity | P90 is trigger completeness; the operative gate is the ring maximum (Class A median 5.79σ; only 0.7 % of windows have it below 5σ) | Yes |
| S7 | MAJOR | sensitivity | Table 14 omits atmospheric decorrelation (5–20 %) and visibility calibration; decorrelation is a *bias*, since injected tones are coherent and real carriers are not | Partly — bound via the 17 continuum detections |
| S8 | MAJOR | pre-registration | "No analysis choice postdates the reservation" is false (radial norm., visibility test, drift strata, P90 budget) | Yes |
| S9 | MAJOR | pre-registration | 61 Vir / HD 14055 / HD 23484 described as calibration-sample; all three blocks are `survey` and all three rows are in the released catalogue | Yes |
| S10 | MAJOR | screen | Every per-event statement respects "prioritisation not test"; the abstract's aggregate comparison does not | Yes |
| S11 | MINOR | screen | β Pic "add-one p = 0.001/0.010" against other windows' control maxima; catalogue column named `p_rank_addone` | Yes |
| S12 | MAJOR | sensitivity | ×0.48–×1.35 is "not an error" in Table 14, "a factor two of spread" in §5.5, "window-to-window scatter" in the abstract; it is a completeness-transfer uncertainty and dominates the ±8 % | Yes |
| S13 | MAJOR | comparison | "∼1250× deeper than Mason et al." hard-coded, does not reproduce (990 or 1695), on the trigger not P90, and smaller than the d² ratio of 2646 | Yes |
| S14 | MINOR | completeness | Duty-cycle curve measured on non-drifting carriers, applied to the drifting primary experiment; Class A near-static threshold unmeasured but inside the *Excluded* box | Statement only |
| S15 | MINOR | completeness | Recurrence coverage quoted as 54/87 systems; the primary experiment's figure is 41/65 (40/65 confirmable) | Yes |
| S16 | MAJOR | attribution | HD 14055 "displaced" verdict over-read: internal σ (χ²/ν ≡ 1.00), 26 looks, and the ×2–4.7 dilution caveat applied asymmetrically | Needs M1 |
| S17 | MAJOR | attribution | CP−72 2713's 5.5σ fit is the same visibilities at a search-selected cell; Conclusion 2 reads as corroboration | Statement only |
| S18 | MAJOR | attribution | Table 11's ∆v is topocentric, not stellar-frame as the caption and the disposition rule say (β Pic: −28 tabulated vs −0.39 in Table 21) | Yes |
| S19 | MAJOR | attribution | Mask robustness tested only in the direction of gains; at ±20 km s⁻¹ several attributed windows lose their mask coincidence | Yes |
| S20 | MINOR→MAJOR | attribution | β Pic is a localisation/recurrence control, not a control for the searched morphology; §5.3.4's opening sentence claims the latter | Statement only |
| S21 | MINOR | statistics | Hold-out median 0.405 with a star-clustered interval 0.42–0.46 that excludes it | Yes |
| S22 | MINOR | statistics | Table 11's *p* = 0.40 is a failure to reject on a disowned null; 0.026 on the Class A null | Yes |

**Missing controls**, in order of what I would insist on: **M1** drift-following
visibility fit on all four events (possible now, four blocks already
recalibrated); **M2** class-conditional measured-rate null with the right
observed count (possible now); **M3** completeness at the promotion gate
(possible now); **M4** displaced-position end-to-end negative control (possible
on a subset only); **M5** per-hand split on the four events (possible now);
**M6** decorrelation bound from the 17 continuum detections (possible now);
**M7** stacked search over HD 14055's 18 same-tuning blocks (possible now);
**M8** blind injection audit (possible, expensive; state its absence).

**Recommendation.** Major revision. The null result itself is not in doubt and I
expect it to survive every item above; what is in doubt is whether the quoted
numbers mean what the paper says they mean. **S1**, **S2**, **S6** and **M1** are
the four I would make conditions of acceptance — the first two because they are
wrong, the third because it changes the headline sensitivity, and the fourth
because the paper already concedes the test is needed and already has the data
in hand.
