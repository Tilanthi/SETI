#!/usr/bin/env python3
"""v3.51 stage 4: the campaign, the held-out set, and the star-versus-control
residual variance.

  S4-1  The out-of-sample check is restated on the campaign as it stands at
        build time (referees C-major-4, D4, D7 and the author's
        instruction): how many blocks and windows have been processed, that
        the pipeline was frozen before any of them was searched, and that
        the campaign continues.  Two of the seven blocks are toward stars
        that carry no flag, which is what makes the check something other
        than a re-test of the flagged windows.
  S4-2  A new subsection measuring R_sigma for the four stage-1 windows
        (referee D3), with what eight controls can and cannot establish.
  S4-3  Sec. 4.1's statement that this measurement cannot be made is
        replaced by a pointer to the measurement.
  S4-4  Sec. 6.2 no longer calls the unsearched blocks an untaken resource,
        since they are being taken; Conclusions likewise.
  S4-5  Sec. 3's epoch-shortfall paragraph, updated to the campaign.
"""
import importlib.util

spec = importlib.util.spec_from_file_location('fz', '.fzsub2.py')
fz = importlib.util.module_from_spec(spec)
spec.loader.exec_module(fz)

TEX = 'technosignatures_20pc_v3.51.tex'
E = []


def sub(a, b):
    E.append((a, b))


# ------------------------------------------------------------------ S4-1
sub(r"""\subsubsection*{An out-of-sample check} \label{sec:heldout}

The statistic and the mask were settled on these data, so the rank figures
above describe this dataset. A check that does not share that weakness needs
windows the design never saw. \HOBlocks{} execution blocks supply \HOWindows{}
of them: \NEpochExtSearched{} further $\beta$~Pictoris blocks and the
CP$-$72~2713 second block, all searched with the frozen pipeline after the
statistic and mask were fixed, and none of them used in setting either.
\HOCoWin{} of the \HOWindows{} carry $\beta$~Pictoris CO at the stellar
position and rank first or nearly first, at $T_\star=\HOCoTLo$ to \HOCoTHi,
which is what a working statistic should do where a real localised signal is
present. In the remaining \HONoiseWin{} the star's add-one rank is consistent with
$U(0,1)$, at a median of \HONoiseMedP{} and Kolmogorov--Smirnov $D=\HOKsD$
($p=\HOKsP$). None of the \HONoiseWin{} is a stage-1 spatial outlier. Taking all \HOWindows{} together, including the CO windows,
gives $D=\HOKsDAll$ ($p=\HOKsPAll$), the departure being the astrophysical
signal.

This is a small check and we do not present it as more. It
covers \HOStars{} stars in three bands, windows within one block share a
calibration and are not independent, and \HONoiseWin{} windows cannot resolve
a rank departure of less than about a tenth. What it does establish is that
the frozen pipeline, applied to data that played no part in building it,
generates no spurious stage-1 flag and recovers the one real signal present.""",
    r"""\subsubsection*{An out-of-sample check on blocks searched after the
pipeline froze} \label{sec:heldout}

@@PARA@@The statistic and the mask were settled on these data, so the rank
figures above describe this dataset and cannot also validate it. A check free
of that weakness needs windows the design never saw, and the unsearched
blocks of \S\ref{sec:sample} are exactly that. Processing them is now under
way. At the time of writing the campaign has searched \HOBlocks{} execution
blocks toward \HOStars{} stars, \HOWindows{} spectral windows in all, with the
frozen pipeline and with no change of any kind to statistic, mask, threshold
or candidate rules after the first of them was searched; a further \HOFailCal{}
blocks failed calibration and produced no search product, \HORunning{} are
running, and the campaign continues. \HONewStars{} of the \HOBlocks{} blocks
are toward stars that carry no flag in the survey, HD~53143 and Wolf~359,
which is what makes this something other than a re-test of the flagged
windows.

@@PARA@@\HOCoWin{} of the \HOWindows{} windows carry $\beta$~Pictoris CO at
the stellar position and rank first or nearly first, at $T_\star=\HOCoTLo$ to
\HOCoTHi, which is what a working statistic should do where a real localised
signal is present. In the remaining \HONoiseWin{} the star's add-one rank is
consistent with $U(0,1)$, at a median of \HONoiseMedP{} and
Kolmogorov--Smirnov $D=\HOKsD$ ($p=\HOKsP$), and \HONoiseStageOne{} of them is
a stage-1 spatial outlier. Taking all \HOWindows{} together, including the CO
windows, gives $D=\HOKsDAll$ ($p=\HOKsPAll$), the departure being the
astrophysical signal rather than a defect.

@@PARA@@This is a partial result and we do not present it as more. It covers
\HOStars{} stars in three bands, windows within one block share a calibration
and are not independent epochs, and \HONoiseWin{} effectively null windows
cannot resolve a rank departure smaller than about a tenth. What it does
establish is that the frozen pipeline, applied to data that played no part in
building it, generates no spurious stage-1 spatial outlier and recovers the
one real signal present. The number of blocks quoted here is the number
processed at the build date of this version (\HOAsOf); the release will carry
the campaign's state at submission.""")

# ------------------------------------------------------------------ S4-2
sub(r"""\subsubsection*{Survey-level false-alarm calibration}""",
    r"""\subsubsection*{Does the stellar position carry its own noise?}
\label{sec:rsigma}

@@PARA@@The noise scale of Eq.~\ref{eq:tstar} is built across the annulus, so
by construction it carries no variance peculiar to the stellar position, which
is where residual continuum, deconvolution or self-calibration residuals and
position-correlated calibration error would concentrate. That is the largest
untested assumption in the method, and the retained products allow a direct,
if limited, test of it. For each of the four stage-1 windows we take the
pipeline's own baseline-subtracted per-integration residuals at the star and
at the \RsigNCtrl{} control positions the release keeps, standardise them by
the pipeline's own noise map $\sigma(t,\nu)$, and form a robust scale over the
(integration, channel) plane with the channels around the crossing excluded at
every position alike. The ratio $R_\sigma =
\sigma_{\star,\rm resid}/\mathrm{median}(\sigma_{\rm ctrl,resid})$ is then
unity if the stellar position is no noisier than its annulus.

@@PARA@@It is: $R_\sigma = \RsigCP$ (CP$-$72~2713), \RsigHD{} (HD~48370),
\RsigBpThree{} ($\beta$~Pic~B3) and \RsigBpSix{} ($\beta$~Pic~B6), a range of
\RsigLo{} to \RsigHi. The star agrees with its controls to better than
\RsigBoundPct{} per cent in every window at 95 per cent confidence, and the
one window where the star is measurably \emph{quieter} than its ring is
HD~48370, whose ring is full of CO. This matters most for CP$-$72~2713.
Because $T_\star$ scales inversely with the noise the star is divided by, an
unmodelled broadband excess of \RsigNeedCPPct{} per cent at the stellar
position would be enough to bring that window's $T_\star$ below its own ring
maximum and dissolve the flag; the measurement bounds any such excess an order
of magnitude below that.

@@PARA@@What eight controls cannot do is give the distribution referee
opinion would prefer. They estimate the position-to-position scatter of the
scale from eight draws, which is why the bound above is at the level of a per
cent and not a tenth of one, and the spread among them is itself only
\RsigCtrlSpreadPct{} per cent. More important, this is a \emph{broadband}
variance test: it is sensitive to a stellar position that is noisier
throughout, and it is not sensitive to an artefact confined to one or two
channels, which is the morphology the search is built to find and which would
raise $T_\star$ while leaving the robust scale untouched. The channel-confined
case is addressed instead by the second-stage local null below and by
recurrence, and retaining all \NCtrl{} control spectra
(\S\ref{sec:futurework}) would let both tests be done properly.

@@PARA@@\subsubsection*{Survey-level false-alarm calibration}""")

# ------------------------------------------------------------------ S4-3
sub(r"""A direct
comparison of the star's own residual variance against the controls'
would be the sharper test. The release retains full dynamic spectra for
the star and for only 8 of the \NCtrl{} controls per flagged window, too few
to calibrate a variance ratio, and this is the one gap these products cannot
close. What they do allow is a measurement of the scale's frequency
dependence. Re-extracting the four flagged windows'""",
    r"""The sharper test is a direct comparison of the star's own residual
variance against the controls', which the \RsigNCtrl{} retained control
spectra per window support for the broadband scale and not for a
channel-confined artefact; \S\ref{sec:rsigma} makes it and reports both what
it settles and what it leaves open. A second measurement, of the scale's
frequency dependence, comes from the same products. Re-extracting the four
flagged windows'""")

# ------------------------------------------------------------------ S4-4
sub(r"""Coverage eligibility
and search completeness differ, and an EB-level selection does lie
behind the \NEB{} searched blocks: \S\ref{sec:sample} gives the datalink audit
that counts \NProgenitorEB{} public execution blocks in scope against the
\NEB{} searched. Those unsearched blocks are the survey's largest single
untaken resource, and \S\ref{sec:futurework} ranks them.""",
    r"""Coverage eligibility and search completeness differ, and an EB-level
selection does lie behind the \NEB{} searched blocks: \S\ref{sec:sample} gives
the datalink audit that counts \NProgenitorEB{} public execution blocks in
scope against the \NEB{} searched. Those unsearched blocks were the survey's
largest single untaken resource, and they are now being taken: the campaign of
\S\ref{sec:heldout} is working through them with the frozen pipeline, and
\S\ref{sec:futurework} ranks what else the archive would support.""")

sub(r"""\emph{The implication for future ALMA archival
SETI.} \NUnsearchedEB{} of the \NProgenitorEB{} public execution blocks in
scope have never been searched. They need no allocation and no new observing
time, and they would turn much of this single-epoch experiment into a
multi-epoch one over \NStarMoreEB{} stars. That work has begun:
\NEpochExtSearched{} further $\beta$~Pictoris blocks and the CP$-$72~2713
second block are searched (\S\ref{sec:technosearch},
Appendix~\ref{app:provenance}), and the campaign is running.
\S\ref{sec:futurework} ranks the other extensions.""",
    r"""\emph{The implication for future ALMA archival SETI.} \NUnsearchedEB{} of
the \NProgenitorEB{} public execution blocks in scope had never been searched
when this analysis was frozen. They need no allocation and no new observing
time, and they would turn much of this single-epoch experiment into a
multi-epoch one over \NStarMoreEB{} stars. That work is under way rather than
proposed: \HOBlocks{} blocks toward \HOStars{} stars, \HOWindows{} windows,
have been through the frozen pipeline since, they generate no spurious stage-1
spatial outlier and they recover the one real signal among them
(\S\ref{sec:heldout}). The campaign continues, and \S\ref{sec:futurework}
ranks the other extensions.""")

# ------------------------------------------------------------------ S4-5
sub(r"""Every epoch statement here, the epoch-activity bound of
Appendix~\ref{app:population} included, therefore concerns searched epochs,
and the archive would support a stronger one. \NEpochExtSearched{} of those
blocks have since been searched, as the recurrence tests of
\S\ref{sec:technosearch}. They are targeted follow-ups outside the survey, leaving the counts in this
section and the trials budget of \S\ref{sec:technosearch} unchanged.""",
    r"""Every epoch statement here, the epoch-activity bound of
Appendix~\ref{app:population} included, therefore concerns searched epochs,
and the archive would support a stronger one. \HOBlocks{} of those blocks have
since been searched, as the recurrence tests of \S\ref{sec:technosearch} and
as the out-of-sample check of \S\ref{sec:heldout}. They sit outside this
frozen release, so the counts in this section and the trials budget of
\S\ref{sec:technosearch} are unchanged by them.""")

fz.apply(TEX, E)
