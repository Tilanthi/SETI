#!/usr/bin/env python3
"""v3.50 stage 2a: the Conclusions cut to four statements (referee A19),
and the "plain terms" paragraph condensed (A13).

A19 names the four: what was searched, what was found, the defensible
sensitivity and search domain, and the most important implication for
future ALMA archival SETI.  A20 says the 346 unsearched blocks are that
implication, so they become the fourth statement rather than a clause
inside the third.  Nothing on the must-not-cut list is touched: the
Scope-of-the-constraints pointer, the Hanning correction and the
conditional-fraction caveat all survive, and the Hanning range is now
given beside the nominal one (A18).
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


OLD_CONC = r"""The public ALMA archive already holds a technosignature search of
\NStars{} stars within 40\,pc over \UnionGHz\,GHz of unique sky
frequency between \UnionLo{} and \UnionHi\,GHz, raising a $5\sigma$
trigger at powers of roughly $10^{13}$ to $10^{17}$\,W EIRP. No signal
satisfying the survey's statistical, spatial, recurrence and
astrophysical-vetting criteria was found. This survey searched, within 40\,pc, every
star with public usable coverage, \NStarBands{} target/bands, \NStars{}
stars in \NSystems{} independent systems, ALMA-archive-complete and
audited for position and identity (\S\ref{sec:exclusions}), but covering
\PctSampleOfCensus{} per cent of the catalogued stars in that volume and
inheriting the archive's non-uniform targeting. The archive's channelisation
splits the search. \NWinA{} Class~A windows cover drift-resolved spectral
carriers and \NWinB{} Class~B windows only unresolved spectral excess, leaving
no
drift discrimination over \PctCoarse{} per cent of the survey
(\S\ref{sec:statistic}). Four windows raised a stage-1 statistical
screening flag. Three are consistent with, and very likely caused by, CO
emission, two circumstellar components towards $\beta$~Pictoris across
two transitions and three epochs and one previously reported foreground
cloud towards HD~48370 \citep{Cataldi2023}. The fourth, towards CP$-$72~2713 at
\FobsCpSeven\,GHz, never acquired an astrophysical attribution and was
marginal throughout. A second-stage local null on its own dynamic spectrum
gives $p=\LNpCP$, about \LNCPRatio{} times above the survey-wide Bonferroni
scale, and a second public execution block at the same tuning records
$\CpRecFluxTwo\pm\CpRecErrTwo$\,mJy at the feature's own frequency and drift
where the first epoch has $\CpRecFluxOne\pm\CpRecErrOne$\,mJy. It fails the recurrence criterion pinned
before the block was searched and is retired as a candidate, and the data cannot
separate a statistical or instrumental excursion from a non-repeating or
intermittent event (\S\ref{sec:technosearch}). None survives vetting, so we report
\NCandidates{} credible technosignatures. Barnard's Star and
Wolf~359 carry their first published mm/submm technosignature limits
(\S\ref{sec:barnardswolf}), and forty ancillary continuum measurements (median $5\sigma$ limit 0.52\,mJy)
are non-detections of unquantified power.

These EIRP$_{5\sigma}$ values are nominal trigger thresholds (boxed rule,
\S\ref{sec:method}), $\EirpMinA$--$\EirpMaxA$\,W over Class~A at
\ChanLoA--\ChanHiA\,kHz native resolution and
$\EirpMinB$--$\EirpMaxB$\,W over Class~B at
\ChanLoB--\ChanHiB\,MHz, deep enough for an unresolved carrier matching
the total power of an Arecibo-like planetary radar toward
\CaseDetCoarseNow{} of the \NSystems{} systems. The conditional
searched-domain transmitter fraction stays illustrative
(Appendix~\ref{app:population}). The \emph{Scope of the constraints} box of
\S\ref{sec:method} fixes what the non-detection binds, and outside it nothing
is bounded. \S\ref{sec:futurework} ranks the extensions that would enlarge it.
By-products ship with the data, a serendipitous molecular-line catalogue,
exoplanet-host and white-dwarf subsample limits, and a closure-phase
diagnostic demonstrated without discriminating power at these flux
densities."""

NEW_CONC = r"""\emph{What was searched.} The public ALMA archive already holds a
technosignature search of \NStars{} stars in \NSystems{} systems within
40\,pc: \NStarBands{} target/band datasets, \NWindows{} spectral windows and
\UnionGHz\,GHz of unique sky frequency between \UnionLo{} and \UnionHi\,GHz.
The sample is archive-target-complete but epoch-incomplete. Every star the
public archive covers is searched, in \PctEbSearched{} per cent of the
execution blocks those targets hold, and the stars themselves are
\PctSampleOfCensus{} per cent of the catalogued population in that volume.
Channelisation splits the search in two, \NWinA{} windows of drift-resolved
carrier search against \NWinB{} of unresolved spectral excess
(\S\ref{sec:statistic}).

\emph{What was found.} Nothing. Four windows raised a stage-1 spatial
screening flag, and three are CO emission: two circumstellar components
towards $\beta$~Pictoris and one previously reported foreground cloud
towards HD~48370 \citep{Cataldi2023}. The fourth, towards CP$-$72~2713,
never acquired an astrophysical attribution. A second public execution block
at the same tuning, searched after the retirement criterion had been pinned
in the released repository, shows no repeat at the feature's own frequency
and drift. We therefore find no evidence supporting a \emph{persistent}
technosignature, and report \NCandidates{} credible ones; two epochs cannot
separate a noise excursion from an intermittent emitter
(\S\ref{sec:technosearch}). Barnard's Star and Wolf~359 carry their first
published mm/submm limits (\S\ref{sec:barnardswolf}).

\emph{The defensible sensitivity and search domain.} EIRP$_{5\sigma}$ values
are nominal trigger powers, not completeness limits (boxed rule,
\S\ref{sec:method}). They run $\EirpMinA$--$\EirpMaxA$\,W over Class~A and
$\EirpMinB$--$\EirpMaxB$\,W over Class~B; corrected for the instrument's
Hanning response, which the nominal figures ignore, the same windows reach
$\EirpHanMinA$--$\EirpHanMaxA$\,W and $\EirpHanMinB$--$\EirpHanMaxB$\,W.
That is deep enough for an unresolved carrier matching the total power of an
Arecibo-like planetary radar toward \CaseDetCoarseNow{} of the \NSystems{}
systems. Sensitivity is calibrated end to end for one configuration only
(Appendix~\ref{app:inject}), $\sigma$ is estimated from the annulus and so
carries no variance belonging to the stellar position alone, and the
conditional searched-domain transmitter fraction stays illustrative
(Appendix~\ref{app:population}). The \emph{Scope of the constraints} box of
\S\ref{sec:method} fixes what the non-detection binds; outside it nothing is
bounded.

\emph{The implication for future ALMA archival SETI.} \NUnsearchedEB{} of
the \NProgenitorEB{} public execution blocks in scope have never been
searched. They need no allocation and no new observing time, and they would
turn much of this single-epoch experiment into a multi-epoch one over
\NStarMoreEB{} stars. That work has begun: \NEpochExtSearched{} further
$\beta$~Pictoris blocks and the CP$-$72~2713 second block are searched
(\S\ref{sec:technosearch}, Appendix~\ref{app:provenance}), and the campaign
is running. \S\ref{sec:futurework} ranks the other extensions."""

sub(OLD_CONC, NEW_CONC)

# ------------------------------------------------------------------ A13
sub(r"""In plain terms: as a by-product of other science, ALMA has stared at
\NStars{} of the nearest stars across parts of the millimetre and
submillimetre band that no technosignature search had examined. We
looked for a narrow, artificial-looking spectral line at each star, and
found none the surrounding sky could not also produce. The powers we
could have seen are enormous by human standards, and we could look only
in the few gigahertz and the few hours each star happened to be
observed. A non-detection on those terms says little about how common
transmitters are.""",
    r"""In plain terms, ALMA has stared at \NStars{} of the nearest stars as a
by-product of other science, across parts of the millimetre band no
technosignature search had examined. We looked for a narrow,
artificial-looking spectral line at each, and found none the surrounding sky
could not also produce. The constraint is conditional on the few gigahertz,
the few hours, the single morphology class and the duty cycles each star
happened to be observed with, and on those terms a non-detection says little
about how common transmitters are.""")

fz.apply(TEX, E)
