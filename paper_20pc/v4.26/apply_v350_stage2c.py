#!/usr/bin/env python3
"""v3.50 stage 2c: the analysis history moves into one appendix.

Referee A1.  Appendix app:exclusions is retitled "Analysis provenance and
robustness checks" and becomes the single home for the history.  It keeps
its old labels (app:exclusions, and now app:aumic) so that every existing
cross-reference still resolves and no \ref changes meaning; the AU Mic
appendix is folded into it rather than left as a second history section.

Moved in, not deleted: the chronology and commit hashes of the statistic
revision; the AU Mic three tests; the fully symmetric region-max check;
the beta Pic frame audit, flux-ratio and excitation argument, the
stellar-flare suppression argument and Table tab:bpicaudit; the HD 48370
Band 8 [C I] check; the line-mask repair history.

Left in the main text, per A1: the original statistic was asymmetric; the
final analysis uses the symmetric single-position statistic; all 431
windows were reassessed under it; the audit table (tab:bothstats, which is
on the must-not-cut list) shows that no result depends on the superseded
version.
"""
import sys
sys.path.insert(0, '.')
import importlib.util

spec = importlib.util.spec_from_file_location('fuzzysub', '.fuzzysub.py')
fz = importlib.util.module_from_spec(spec)
spec.loader.exec_module(fz)

TEX = 'technosignatures_20pc_v3.50.tex'
E = []


def sub(a, b):
    E.append((a, b))


# ============================================================ 1. section 5.4
sub(r"""\subsection{Changing the detection statistic, and the AU~Mic crossing}
\label{sec:aumic}

The estimator is justified on its own terms in \S\ref{sec:statistic},
from the exchangeability the rank test needs and independently of any
dataset, and the chronology of the change was as follows. An earlier region-max statistic
maximised over an $n_{\rm src}=\RingNSrc$-position region centred on the
star against \NCtrl{} single-position controls, and under it a crossing
towards AU~Mic in Band~6 at 230.83\,GHz was carried as a candidate. The
released repository dates both steps. That flag is first committed on
\StatFlagDate{} (\texttt{\StatFlagHash}), in the manuscript of the day and in
its machine-readable aggregate; the asymmetry is identified and the symmetric
form of Eq.~\ref{eq:tstar} adopted as operative \StatGapDays{} days later, on
\StatSymDate{} (\texttt{\StatSymHash}). The redesign postdates the flag, and we
do not claim otherwise. The argument therefore rests on the algebra, which owes
nothing to these data: under exchangeability an $n_{\rm src}$-position maximum
at the star against single-position controls ranks first with probability
$n_{\rm src}/(n_{\rm src}+\NCtrl)=\AsymExpectPct$ per cent, and the symmetric
form removes that inflation.

Table~\ref{tab:bothstats} audits every window the original statistic flagged, so the sequence can be checked. The symmetric criterion flags a strict \emph{subset},
seven before and four after. Both $\beta$~Pic windows and HD~48370 keep
their flags under either statistic; AU~Mic, ALMA~J1537$-$3319 and
HD~14055 drop out, in each case because the stellar position never
exceeded its own control ensemble, the one configuration a localised
transmitter cannot produce. Under a
decision rule fixed without reference to these data, the $1/\RankFloor$
rank test, AU~Mic fails on the same evidence: 10 of its \NCtrl{}
controls reach or exceed the stellar statistic. Because the statistic
was settled on these data, the false-alarm calibration here is
descriptive of them.""",
    r"""\subsection{The superseded statistic}
\label{sec:aumic}

An earlier region-max statistic maximised over a region centred on the star
against single-position controls, which inflates the star's rank. The
analysis reported here uses the symmetric single-position statistic of
Eq.~\ref{eq:tstar} throughout, and all \NWindows{} windows were reassessed
under it. Table~\ref{tab:bothstats} audits every window the original
statistic flagged. The symmetric criterion flags a strict \emph{subset},
seven windows before and four after, so no result here depends on the
superseded version. The three that drop out, among them a crossing towards
AU~Mic, do so because the stellar position never exceeded its own control
ensemble, which is the one configuration a localised transmitter cannot
produce. The redesign postdates the AU~Mic flag by \StatGapDays{} days and
we do not claim otherwise; Appendix~\ref{app:provenance} gives the
chronology with its commit hashes, the algebraic argument that owes nothing
to these data, and the three tests AU~Mic fails. Because the statistic was
settled on these data, the false-alarm calibration here is descriptive of
them, which is why the held-out check of \S\ref{sec:heldout} is reported
separately.""")

# ----------------------------------------------- 2. the two trailing paras
sub(r"""The within-window add-one rank is $p=0.021$, a different quantity from
the survey-wide rate at which any window's ring maximum reaches 5.97
($p=\AuP$, Appendix~\ref{app:aumic}), and far from the $1/\RankFloor$
floor either way. The crossing also fails two pre-named tests, localisation and
recurrence. Under the three treatments that decide it, the frozen
region-max products, a fully symmetric reprocessing of the same
first-epoch block and the second-epoch block of the same programme, the
star statistic is 5.97, 4.93 and 4.77 against control maxima of 5.85,
7.70 and 6.78, with add-one star ranks $p=0.81$ and $0.97$ in the latter
two.

Appendix~\ref{app:aumic} gives both in full: neither the reprocessed first epoch nor the
further public Band~6 block at 230.83\,GHz shows a
localised excess, the second epoch a clean non-recurrence. That rejects
a continuous or repeating source at this frequency and these epochs,
though not intermittent transmission. Each star was \emph{searched}
independently in one to three blocks, so the non-detection concerns
the epochs searched and not permanent activity; \NStarMoreEB{} stars hold
further public blocks this survey did not take (\S\ref{sec:sample}), and
\S\ref{sec:discussion} turns that structure into an epoch-activity constraint.""",
    r"""Each star was \emph{searched} independently in one to three blocks, so the
non-detection concerns the epochs searched and not permanent activity.
\NStarMoreEB{} stars hold further public blocks this survey did not take
(\S\ref{sec:sample}), and \S\ref{sec:discussion} turns that structure into
an epoch-activity constraint.""")

# ---------------------------------------- 3. the fully symmetric check out
sub(r"""\subsubsection*{The fully symmetric region-max check}

A fully symmetric region-max variant, applying identical
source-region, drift-rate and frequency maximisation at the star and at
every control, needs products the frozen release does not carry, so its
domain is seven locally reprocessed windows. All give
$T_\star=3.7$--$4.9$ against control maxima of 6.7--7.7, $p=0.81$--1.00,
so the star is exchangeable with its ring wherever the test runs at full
symmetry. The single-position calibration above remains the operative
release-wide criterion; the two are never interchanged
(Appendix~\ref{app:falsealarm}).

\subsubsection*{Astrophysical end-to-end validation: $\beta$~Pictoris CO}""",
    r"""A fully symmetric region-max variant, which maximises identically at the
star and at every control, can be run on only seven locally reprocessed
windows because the frozen release does not carry the products it needs. In
all seven the star is exchangeable with its ring
(Appendix~\ref{app:provenance}). The single-position calibration above
remains the operative release-wide criterion, and the two are never
interchanged.

\subsubsection*{Astrophysical end-to-end validation: $\beta$~Pictoris CO}""")

# ------------------------------------------------- 4. mask repair history
sub(r"""Four defects in the mask as executed are all repaired here. Its rest
frequencies were rounded to \MaskRestRoundMHz\,MHz, worth up to
\MaskRoundWorstKms\,km\,s$^{-1}$. It carried no atomic carbon, though every
Band~8 window here is a [C\,\textsc{i}] $^{3}P_{1}$--$^{3}P_{0}$ tuning, and
no hydrogen recombination line, though H30$\alpha$ falls in the standard
Band~6 tuning of much of the sample. It was also applied in the stellar frame
alone, the wrong frame for the Galactic foreground behind one of the three
line attributions. The repaired catalogue holds
\MaskNTransNew{} transitions of \MaskNSpecNew{} species at full JPL/CDMS
precision \citep{Pickett1998,CDMS2005}, including [C\,\textsc{i}] at
\MaskCIGHz\,GHz and H30$\alpha$ at \MaskHthirtyGHz\,GHz, against
\MaskNTransOld{} of \MaskNSpecOld{} before, and it is applied in the
LSR frame as well as the stellar frame. The species count also
reconciles the text with the products, which always used
\MaskNSpecOld{} species: earlier versions of this paper said eight,
omitting H$_2$CO.

Re-running the survey was not affordable, so the repaired mask is re-applied to
the frozen crossing list as a post-hoc filter, using each crossing channel's
own frequency as the pipeline recorded it. \textbf{No disposition changes.} The two
$\beta$~Pictoris crossings remain inside the stellar-frame tube, at
\StelBpicThree{} and \StelBpicSix\,km\,s$^{-1}$ from CO($1{\to}0$) and
CO($2{\to}1$). HD~48370's crossing remains inside it at
$-17.8$\,km\,s$^{-1}$ and is now caught by the LSR-frame tube as well,
at $-\VlsrHdLsr$\,km\,s$^{-1}$, which is the frame its foreground
attribution always implied. CP$-$72~2713's crossing lies $\DvCpSeven$\,km\,s$^{-1}$ from the nearest
masked transition in the topocentric frame and $-1300$\,km\,s$^{-1}$ in
the LSR frame, so no tube of this mask excludes it; a wider
catalogue does place entries inside the tube, which
\S\ref{sec:technosearch} treats on the physics. Across all \NCrossFreq{}
crossing windows the repaired catalogue moves the nearest transition in
exactly \MaskNewCoinc{} case, \CIcrossStar's Band~8 crossing at
\CIcrossGHz\,GHz, whose nearest entry changes from CO($4{\to}3$)
\CIcrossOldKms\,km\,s$^{-1}$ away to [C\,\textsc{i}] at
\CIcrossKms\,km\,s$^{-1}$. That is still outside the tube, and the frame corrections are at most a
few tens of km\,s$^{-1}$, so no frame masks it; it was never a
flag, its own control ensemble exceeding it. The two new transitions cost a further
\MaskExtraGHz\,GHz of unique searched frequency,
\MaskExtraPct{} per cent.

The masking cost uses one definition:""",
    r"""The mask as executed carried four defects, all repaired here and all
described in Appendix~\ref{app:provenance}: rounded rest frequencies, no
atomic carbon, no hydrogen recombination line, and application in the
stellar frame alone. The repaired catalogue holds \MaskNTransNew{}
transitions of \MaskNSpecNew{} species at full JPL/CDMS precision
\citep{Pickett1998,CDMS2005} and is applied in the LSR frame as well as the
stellar frame. Re-running the survey was not affordable, so it is re-applied
to the frozen crossing list as a post-hoc filter. \textbf{No disposition
changes.}

The masking cost uses one definition:""")

# ======================================================= 5. the appendix
sub(r"""\section{Analysis audit trail: excluded entries and the retired statistic}
\label{app:exclusions}

Five pre-freeze changes are logged with their effect on released products in
the repository change-log, and four are treated above. Only the replacement of the
asymmetric region-max statistic by the symmetric single-position form of
\S\ref{sec:statistic} (release re-run, criterion frozen) changes a
released number. Counted \emph{without} the $\geq5\sigma$ amplitude gate,
that is on rank alone, rank-first windows
\NRankFirstOld/\NWindows{} (\RateRankFirstOld{} per cent) become \NRankFirst/\NWindows{}
(\RateRankFirst{} per cent); counted \emph{with} the gate, which is the
stage-1 flag of the main text, \NSpatialOld{} become \NSpatial{} and
the AU~Mic crossing becomes unflagged. Under a pure-noise null the retired region maximum over $n_{\rm src}$
positions beats single controls with probability
$n_{\rm src}/(n_{\rm src}+n_{\rm ctrl})=\AsymExpectPct$ per cent, the
order of the measured region-max rate. Nothing derived from it enters an
operative false-alarm probability.""",
    r"""\section{Analysis provenance and robustness checks}
\label{app:provenance}
\label{app:exclusions}
\label{app:aumic}

This appendix holds the analysis history: how the search statistic came to
be what it is, the checks run on the windows the old statistic flagged, the
frame audit behind the CO attributions, the line-mask repair, and the
entries excluded from the released catalogue. None of it changes a number in
the main text, and it is collected here so the main text can present the
experiment rather than its history.

\subsection*{Chronology of the statistic revision}

An earlier region-max statistic maximised over an
$n_{\rm src}=\RingNSrc$-position region centred on the star against
\NCtrl{} single-position controls, and under it a crossing towards AU~Mic in
Band~6 at 230.83\,GHz was carried as a candidate. The released repository
dates both steps. That flag is first committed on \StatFlagDate{}
(\texttt{\StatFlagHash}), in the manuscript of the day and in its
machine-readable aggregate. The asymmetry is identified and the symmetric
form of Eq.~\ref{eq:tstar} adopted as operative \StatGapDays{} days later,
on \StatSymDate{} (\texttt{\StatSymHash}). The redesign therefore postdates
the flag. The argument for it rests on algebra that owes nothing to these
data: under exchangeability an $n_{\rm src}$-position maximum at the star
against single-position controls ranks first with probability
$n_{\rm src}/(n_{\rm src}+\NCtrl)=\AsymExpectPct$ per cent, and the
symmetric form removes that inflation.

Five pre-freeze changes are logged with their effect on released products in
the repository change-log. Only this one changes a released number. Counted
\emph{without} the $\geq5\sigma$ amplitude gate, that is on rank alone,
rank-first windows \NRankFirstOld/\NWindows{} (\RateRankFirstOld{} per cent)
become \NRankFirst/\NWindows{} (\RateRankFirst{} per cent). Counted
\emph{with} the gate, which is the stage-1 flag of the main text,
\NSpatialOld{} become \NSpatial{} and the AU~Mic crossing becomes unflagged.
Nothing derived from the retired statistic enters an operative false-alarm
probability.

\subsection*{AU~Mic: the three tests in full}

The within-window add-one rank of the AU~Mic crossing is $p=0.021$. That is
a different quantity from the survey-wide rate at which any window's ring
maximum reaches 5.97, $p=\AuP$, and both are far from the $1/\RankFloor$
floor. Under the three treatments that decide the crossing, namely the
frozen region-max products, a fully symmetric reprocessing of the same
first-epoch block, and the second-epoch block of the same programme, the
star statistic is 5.97, 4.93 and 4.77 against control maxima of 5.85, 7.70
and 6.78, with add-one star ranks $p=0.81$ and $0.97$ in the latter two.

\emph{Localisation.} Reprocessed from the raw science data model with the
observatory pipeline's own calibration recipe (310 integrations against the
release pipeline's 249, on a finer drift grid) and re-run through the
symmetric statistic of \S\ref{sec:statistic}, the crossing window's star
does not beat its control ensemble. The frozen products agree only
asymmetrically: the source-region peak exceeds the \NCtrl-control maximum by
0.12, below that statistic's window-to-window scatter, and the crossing
fails the single-position variant too.

\emph{Recurrence.} The one further public Band~6 block covering 230.83\,GHz,
the same programme executed 2014 June~5, was searched identically. No
channel within $\pm$10 of the first-epoch flagged channel exceeds 3.1, and
nothing is localised to the star. Its band rms (1.48\,mJy per 488-kHz
channel) matches the first epoch's 1.9\,mJy, so a comparable excess would
have been recovered, and the frequency recurs at no other target.
Intermittent or precisely-scheduled transmissions outside the sampled
windows stay unconstrained.

\emph{Statistical scale.} The on-source peak (5.97) sits at the \AuPct{}th
percentile of the control-maxima distribution over all \NWindows{} windows
(median \CtrlMed, 90th percentile \CtrlPninety): \AuNge{} windows
(\AuFrac{} per cent) match or exceed it, add-one empirical $p=\AuP$ before
any multiple-testing correction. The crossing matches no catalogued
molecular transition (Table~\ref{tab:bpicaudit}), and closure-phase vetting
finds it point-source consistent, which is one-sided evidence
(Appendix~\ref{app:closure}). Two astrophysical contexts are recorded for
re-examination and neither grounds the rejection. AU~Mic is an exceptionally
active flare star, but the block's own quiescent continuum (0.15\,mJy) rules
out the later-epoch GHz-wide flares of \citet{MacGregor2020} (16.8 and
6.1\,mJy): an 11\,mJy channel-confined excess would sit ${\sim}70\times$
above a continuum that shows nothing. The controls share the primary-beam
footprint, so smooth structure such as the debris belt raises star and
controls alike and cannot alone produce a localised excess.

\subsection*{The fully symmetric region-max check}

A fully symmetric region-max variant applies identical source-region,
drift-rate and frequency maximisation at the star and at every control. It
needs products the frozen release does not carry, so its domain is seven
locally reprocessed windows. All seven give $T_\star=3.7$--$4.9$ against
control maxima of 6.7--7.7, $p=0.81$--1.00, so the star is exchangeable with
its ring wherever the test runs at full symmetry. The single-position
calibration of \S\ref{sec:technosearch} remains the operative release-wide
criterion and the two are never interchanged
(Appendix~\ref{app:falsealarm}).

\subsection*{The $\beta$~Pictoris frame audit}

Table~\ref{tab:bpicaudit} carries the frame chain for the line-attributed
windows. It recovers the whole check list untuned: frequencies to the frame
chain's stated tolerance, velocity concordance across epochs and
transitions, localisation against the control ensemble, and drift class zero
to within the grid. The stage-1 Band~6 window carries \NCrossBpicSix{}
formal $\geq5\sigma$ crossings where a channel-confined carrier admits one.
The retained products do not record whether those channels are contiguous,
so the count sets a floor of \BpWidthSixKms\,km\,s$^{-1}$ on the feature's
extent without measuring it (Appendix~\ref{app:extended} for the tabulation
cap). Peak flux densities of \FluxBpicThree{} and \FluxBpicSix\,mJy per
channel, ratio \FluxRatioBpic, are the right order for this belt's spatially
integrated CO. They are per-beam peaks, the synthesised beams being
\BeamBpicThree{} and \BeamBpicSixFlag\,arcsec on emission resolved in both,
and \citet{Matra2017} find the gas subthermally excited
($T_{\rm exc}=12\pm4$\,K), so beam dilution and excitation both depress the
ratio below optically thin LTE. Since both channels are far narrower than
the line, the peak per channel is comparable across the two despite their
differing widths. Among the \NCtrlGeBpicBThree{} control maxima that match
or exceed the Band~3 peak is this star's own CO-filled Band~6 ensemble at
\BpicCoRingMax, the \BpicCoRingRank th largest control maximum in the
survey.

Stellar emission is a competing explanation for any flag towards an active
young star, and the search suppresses it twice. Gyrosynchrotron and
free-free emission from chromospheres and coronae are broadband, while the
block-median baseline of \S\ref{sec:statistic} removes everything broader
than its \MedWin-channel passband, ${\sim}32$\,MHz at the fine class, a
fractional bandwidth of ${\sim}10^{-4}$; \citet{MacGregor2020}'s AU~Mic
flares are coherent across the full 8\,GHz. Flares are also time-confined,
so the inverse-variance stack over all integrations dilutes them. What
survives is the multiplicative route of \S\ref{sec:statistic}, a flare
continuum times a spectral calibration residual, bounded there and measured
for CP$-$72~2713 in \S\ref{sec:technosearch}. The search is blind to the
time axis by construction, and the retained dynamic spectra are the only
handle on it.

\emph{HD~48370 in Band~8.} The carbon tuning says the same thing by
omission. All twelve Band~8 windows here belong to $\eta$~Crv, HD~48370 and
HD~61005 and are [C\,\textsc{i}] $^{3}P_{1}$--$^{3}P_{0}$ (\MaskCIGHz\,GHz)
tunings. HD~48370's carries a $5.05\sigma$ on-star crossing against a ring
maximum of 6.23, so it is not one of the four stage-1 flags. Its crossing
channel sits \CIcrossKms\,km\,s$^{-1}$ from [C\,\textsc{i}], so it is not
[C\,\textsc{i}] emission from the disc, the cloud or the star, and its own
ring dispositions it as an ordinary noise crossing. What the window does
show is no line at the star in this disc's carbon tuning, which is what
\citet{Cataldi2023} report. The crossing peak in the flagged window itself
is $\FluxHdFour$\,Jy in one 122-kHz channel with the ring at the same level.

\subsection*{The line mask as executed, and its repair}

Four defects in the mask as executed are all repaired in
\S\ref{sec:linecost}. Its rest frequencies were rounded to
\MaskRestRoundMHz\,MHz, worth up to \MaskRoundWorstKms\,km\,s$^{-1}$. It
carried no atomic carbon, though every Band~8 window here is a
[C\,\textsc{i}] tuning, and no hydrogen recombination line, though
H30$\alpha$ falls in the standard Band~6 tuning of much of the sample. It
was also applied in the stellar frame alone, the wrong frame for the
Galactic foreground behind one of the three line attributions. The repaired
catalogue adds [C\,\textsc{i}] at \MaskCIGHz\,GHz and H30$\alpha$ at
\MaskHthirtyGHz\,GHz, against \MaskNTransOld{} transitions of
\MaskNSpecOld{} species before. The species count also reconciles the text
with the products, which always used \MaskNSpecOld{} species; earlier
versions of this paper said eight, omitting H$_2$CO.

Re-application uses each crossing channel's own frequency as the pipeline
recorded it, and no disposition changes. The two $\beta$~Pictoris crossings
remain inside the stellar-frame tube. HD~48370's remains inside it at
$-17.8$\,km\,s$^{-1}$ and is now caught by the LSR-frame tube as well, at
$-\VlsrHdLsr$\,km\,s$^{-1}$, the frame its foreground attribution always
implied. CP$-$72~2713's lies $\DvCpSeven$\,km\,s$^{-1}$ from the nearest
masked transition in the topocentric frame and $-1300$\,km\,s$^{-1}$ in the
LSR frame, so no tube of this mask excludes it; a wider catalogue does place
entries inside the tube, which \S\ref{sec:technosearch} treats on the
physics. Across all \NCrossFreq{} crossing windows the repaired catalogue
moves the nearest transition in exactly \MaskNewCoinc{} case,
\CIcrossStar's Band~8 crossing at \CIcrossGHz\,GHz, whose nearest entry
changes from CO($4{\to}3$) \CIcrossOldKms\,km\,s$^{-1}$ away to
[C\,\textsc{i}] at \CIcrossKms\,km\,s$^{-1}$. That is still outside the
tube, and the frame corrections are at most a few tens of km\,s$^{-1}$, so
no frame masks it; it was never a flag, its own control ensemble exceeding
it. The two new transitions cost a further \MaskExtraGHz\,GHz of unique
searched frequency, \MaskExtraPct{} per cent.

\subsection*{Entries excluded from the released catalogue}""")

# --------------------------- 6. remove the now-duplicated app:aumic section
sub(r"""\section{AU~Mic: the three tests in full}
\label{app:aumic}

\emph{Localisation.} Reprocessed from the raw science data model with
the observatory pipeline's own calibration recipe (310 integrations
against the release pipeline's 249, on a finer drift grid) and re-run
through the symmetric statistic of \S\ref{sec:statistic}, the crossing
window's star does not beat its control ensemble. The frozen products
agree only asymmetrically: the source-region peak exceeds the
\NCtrl-control maximum by 0.12, below that statistic's window-to-window
scatter, and the crossing fails the single-position variant too.

\emph{Recurrence.} The one further public Band~6 block covering
230.83\,GHz, the same programme executed 2014 June~5, was searched
identically: no channel within $\pm$10 of the first-epoch flagged
channel exceeds 3.1, and nothing is localised to the star. Its band rms
(1.48\,mJy per 488-kHz channel) matches the first epoch's 1.9\,mJy, so a
comparable excess would have been recovered, and the frequency recurs at
no other target. Intermittent or precisely-scheduled transmissions
outside the sampled windows stay unconstrained.

\emph{Statistical scale.} The on-source peak (5.97) sits at the
\AuPct{}th percentile of the control-maxima distribution over all
\NWindows{} windows (median \CtrlMed, 90th percentile \CtrlPninety):
\AuNge{} windows (\AuFrac{} per cent) match or exceed it, add-one
empirical $p=\AuP$ before any multiple-testing correction: a survey-wide
window-level rate, distinct from the within-window rank of
\S\ref{sec:aumic}. The crossing matches no catalogued molecular
transition (Table~\ref{tab:bpicaudit}), and closure-phase vetting finds it
point-source consistent, which is one-sided evidence
(Appendix~\ref{app:closure}).

Two astrophysical contexts are recorded for re-examination;
neither grounds the rejection. AU~Mic is an exceptionally active flare
star, but the block's own quiescent continuum (0.15\,mJy) rules out the
later-epoch GHz-wide flares of \citet{MacGregor2020} (16.8 and
6.1\,mJy): an 11\,mJy channel-confined excess would sit ${\sim}70\times$
above a continuum that shows nothing. The controls share the primary-beam
footprint, so smooth structure such as the debris belt raises star and
controls alike and cannot alone produce a localised excess.

\section{The ancillary continuum lane}""",
    r"""\section{The ancillary continuum lane}""")

fz.apply(TEX, E)
