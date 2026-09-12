# Paste-ready LaTeX for the v3.46 new results, on verified numbers

From `astra-pa`. Every macro used below is defined in `survey_numbers_round15.tex`
(generator `v346_calc.py`, inputs listed in its docstring). Nothing here is wired into
the manuscript; take what is useful. No em-dashes. Macro names are letters only.

To use the macros, add `\input{survey_numbers_round15}` after the other
`survey_numbers_*` inputs and `python3 v346_calc.py` to `make_all.sh` after
`localnull_calc.py`.

---

## A. The matched positive control (brief 1b), three blocks, not two

> \subsubsection*{A matched positive control: the $\beta$~Pictoris CO features recur}
>
> The retirement of CP$-$72~2713 rests on a feature failing to reappear, so the
> machinery that looked for it has to be shown capable of finding a repeat when one
> exists. The $\beta$~Pictoris CO windows provide that test on the same pipeline,
> unmodified. The member observing unit behind the Band~3 flag holds further public
> execution blocks that the per-target download budget declined; we have since
> calibrated and searched \BpRecThreeNBlocks{} of them at the same tuning. All
> \BpRecThreeNBlocks{} record a detection at the flagged frequency, with
> $T_\star=\BpRecThreeTList$ and \BpRecThreeHitsList{} channels above threshold, and
> in each the stellar statistic exceeds all \NCtrl{} controls. The three peak
> frequencies span \BpRecThreeSpreadMHz\,MHz, \BpRecThreeSpreadChan{} of a
> \BpRecThreeChanKHz\,kHz channel. The Band~6 window behaves the same way across its
> two blocks, $T_\star=\BpRecSixTList$ at an exact configuration match
> (\BpRecSixChanKHz\,kHz, \BpRecSixNChan{} channels), with integrated line fluxes of
> $\BpRecSixFluxOne\pm\BpRecSixErrOne$ and $\BpRecSixFluxTwo\pm\BpRecSixErrTwo$\,mJy\,MHz,
> a difference of $\BpRecSixFluxSig\sigma$; the Band~3 pair agrees to
> $\BpRecThreeFluxSig\sigma$ on the same measure.
>
> The residual frequency offsets are small, and the right way to read them is not the
> barycentric one. ALMA Doppler-sets the spectral window on each date, so the
> barycentric term is already absorbed by the tuning: for the Band~6 pair the predicted
> shift of a stationary line is 1.68\,MHz and the measured difference in the window
> tuning is 1.68\,MHz, agreeing to 2.5\,kHz. Corrected for the tuning, the two Band~6
> drift-search peaks differ by exactly three channels and the two line-profile peaks,
> which are the right measure for a stationary astrophysical line, by exactly one; the
> Band~3 peaks differ by exactly one channel. The stronger statement is frame-free:
> converted to the barycentric frame, the CO peaks of four independent execution
> blocks, in two bands and two transitions nine years apart, all fall within
> $0.8$\,km\,s$^{-1}$ of $\beta$~Pictoris' systemic velocity.
>
> Set against CP$-$72~2713, which does not reappear at its own frequency and drift in
> a deeper block of the same tuning, this is a matched pair of controls: the same
> statistic, the same pipeline and the same recurrence test return a repeat where the
> emission is real and no repeat where it is not.

**Guard rails, all three verified and all three easy to get wrong.**

1. The Band~6 window that recurs is at 230.528\,GHz in MOUS `uid://A002/X5a9a13/X58b`.
   That is a crossing, **not** one of the four stage-1 outliers. The Band~6 stage-1
   window is 230.516\,GHz in `uid://A001/X133d/Xbb5` and has no second block searched.
   Do not write "both $\beta$~Pic flags recur".
2. The second Band~3 block is **earlier** than the published one, not later. "Block",
   not "epoch 2".
2b. **Do not attach the 2.2 km/s barycentric difference to the frequency residual.** It
   is right as a number and it belongs to the B6 pair only (B3's is 0.087 km/s), but
   ALMA's per-date tuning has already removed it, so it cannot explain a 0.95 MHz
   residual. See `/shared/ASTRA/reviews/v3.46_evidence_bpic.md` section 5, which is the
   better analysis and supersedes my first draft of this paragraph.
3. `\BpRecThreeHitsOne` (17) and `\BpRecSixHitsOne` (32) are the published blocks;
   24 and 28 are the second blocks. They are not a matched pair.

## B. The exclusion accounting (brief 1a)

Replacement for the opening of \S\ref{sec:exclusions}, or a new short subsection:

> \subsubsection*{Most processing failures are stars ALMA never observed}
>
> An archive-metadata audit re-derived the pointing of every target/band that failed
> processing, comparing the catalogue position of the star with the nearest field
> centre of every candidate member observing unit. Of \NTargetBandFail{} failures,
> \NPointedTB{} have the star inside the primary beam, at most \SepPointedMax{} arcsec
> from a field centre. The other \NNotPointedTB{} lie between \SepDeadMin{} and
> \SepDeadMax{} arcsec from the nearest pointing, median \SepDeadMed{} arcsec
> (\SepDeadMedDeg{} degrees), with nothing in between. \NEphemTB{} of them observe the
> Sun, a planet, a moon or a comet, and for \NTpOnlyTB{} every candidate unit is
> total-power only. ALMA's archive reports a field of view for an ephemeris or solar
> delivery that can reach \FovHalfMaxDeg{} degrees of half-width, and the candidate
> crossmatch admitted a star anywhere inside it, so these entries were never
> observations of the star at all. Proper motion cannot close the gap: the fastest
> mover in the failed set runs at \PmFastestArcsecYr{} arcsec per year, so even the
> smallest separation would take about \PmYearsToClose{} years to close. They are
> catalogue-construction artefacts rather than processing failures, and the lesson is
> upstream: a candidate crossmatch must not accept the archive's field of view for a
> delivery whose field is an ephemeris target.
>
> \NNeverObsStars{} of the \NCoveredCand{} stars admitted to the candidate list are of
> this kind, so the sample searched here is \NSearchedStars{} of roughly
> $\NCoveredCand-\NNeverObsStars$ genuinely covered stars rather than
> \NSearchedStars{} of \NCoveredCand. The same audit tested, and rejected, the
> hypothesis that the per-target three-block limit caused failures by selecting blocks
> without calibration products: \NUntriedWithCal{} failures have untried blocks
> carrying such products, and in \NCapCause{} of them did the blocks actually tried
> lack them.

**Do not write "0 successes in 38 attempts".** Verified from the processing log:
**\NRetryAttempt{} re-attempts, \NRetrySuccess{} success, \NRetryFail{} failures**,
the success being \RetrySuccessName, which is outside Bands 3 to 8 and outside this
release. A safe sentence: "Re-attempting the failed target/bands on the current code
recovered \NRetryFail{} of \NRetryAttempt{} not at all, and the single recovery lies
outside this release's band range."

## C. The selection chain (brief 2.1, referee A3)

`tab:searchspace` row 1 currently reads "Census stars within 40\,pc & \NCensus", with
`\NCensus` = 168. Replace with two rows and keep the chain visible:

> Gaia\,DR3 reference census within 40\,pc & \NGaiaCensus{} \\
> \quad with qualifying public ALMA coverage & \NCoveredCand{} \\
> \quad\quad never actually pointed at (field-of-view artefact) & \NNeverObsStars{} \\
> Stars searched; independent systems & \NStars{}; \NSystems{} \\

## D. The coarse-noise defect (brief 2.17, referee B4)

> The defect is confined to \NDefectWin{} windows in \NDefectEBs{} execution blocks
> from \NDefectProjects{} projects, all \DefectArrays{} array and all at
> \DefectChanwMHz\,MHz channel width, so they share a correlator mode and an array but
> not a proposal. A gap-based exclusion invites the objection that smaller deflations
> survive it, and the radiometer relation answers it directly. Predicting
> $q\equiv\sigma\sqrt{t_{\rm on}\Delta\nu_{\rm ch}}$ from each block's band, array and
> antenna count as ${\rm SEFD}/\sqrt{N_{\rm bl}}$, the residuals of the
> \NSefdModelled{} retained windows are unimodal about a median of \SefdResidMed{} dex,
> \SefdResidLo{} to \SefdResidHi{} between the 16th and 84th percentiles (a factor
> \SefdResidSpreadFac), with \SefdResidPctHalfDex{} per cent inside half a decade of
> the median and no empty interval wider than \SefdResidGapDex\,dex inside the body of
> the distribution. The \NDefectWin{} excluded windows sit at \SefdResidDefLo{} to
> \SefdResidDefHi\,dex, \SefdResidDefGapDex\,dex below the lowest retained window, with
> nothing between. There is no continuum of smaller deflations to find.

(The median offset of \SefdResidMed\,dex from a textbook SEFD is a fixed efficiency
and polarisation bookkeeping factor and carries no information; the spread does.)

## E. The statistic-revision chronology (brief 2.15, referee B1)

> The revision postdates the flag, and the record says so. The AU~Mic control-maxima
> figure entered the release repository at 2026 September 9, 15:45:28\,UT
> (\texttt{157f92c08d}) alongside a manuscript that still carried AU~Mic as a
> candidate; the symmetric statistic was adopted at 16:14:07\,UT
> (\texttt{0c465f2661}) and again at 17:02:17\,UT (\texttt{bfe7d277f1}). We do not
> claim the estimator was settled before the crossing was seen. What carries the
> argument is algebraic and independent of these data: an $n_{\rm src}$-position
> maximum at the star compared with single-position controls inflates the
> false-positive rate by $n_{\rm src}/(n_{\rm src}+n_{\rm ctrl})$, and the symmetric
> form removes it. Table~\ref{tab:bothstats} audits every window the original
> statistic flagged, so the effect of the change can be read off rather than taken on
> trust.

## F. CP$-$72~2713 wording (brief 2.9)

Everywhere the retirement is stated, including the Conclusions and the abstract:

> The event fails the pre-defined recurrence criterion and is therefore retired as a
> candidate. The available data cannot distinguish a statistical or instrumental
> excursion from a non-repeating or intermittent astronomical or transmitted event.

The current wording "so the flag is retired as a noise excursion on the balance of two
independent measurements" asserts the classification the referee objects to, and the
manuscript itself says two epochs cannot separate the two cases.
