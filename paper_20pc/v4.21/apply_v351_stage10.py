#!/usr/bin/env python3
"""v3.51 stage 10: terminology, and the compression that pays for it.

  S10-1 CP-72 2713 is described throughout in referee D6's standard form,
        an unattributed first-epoch threshold event that is absent in the
        second epoch.  Nothing anywhere says or implies that its
        non-recurrence identifies the first event as noise.  The catalogue
        disposition string moves with the table, since Data Availability
        promises they agree.
  S10-2 ``Flag'' as a noun for the screening state is replaced by
        ``stage-1 spatial outlier'', abbreviated ``stage-1 outlier'' after
        first use in a section, and the nomenclature table records the
        abbreviation.  ``Flagged'' survives only where it means the act of
        another author flagging something, or per-correlation flagging of
        visibilities.
  S10-3 Compression to pay for both.
"""
import importlib.util

spec = importlib.util.spec_from_file_location('fz', '.fzsub2.py')
fz = importlib.util.module_from_spec(spec)
spec.loader.exec_module(fz)

TEX = 'technosignatures_20pc_v3.51.tex'
E = []


def sub(a, b):
    E.append((a, b))


# ------------------------------------------------------------------ S10-3
sub(r"""The paper's three contributions are systematic exploitation of
archival ALMA stellar fields, \NStarBands{} target/band datasets mined
from public data with no new observing time; spatial-control null
calibration for interferometric SETI, the same statistic evaluated at
the star and at \NCtrl{} control positions so the false-alarm rate is
measured; and a quantitative accounting of the frequency, EIRP and drift
domain actually searched, which gives the non-detection explicit
boundaries.""",
    r"""Three contributions follow. The first is the systematic exploitation of
archival ALMA stellar fields, \NStarBands{} target/band datasets mined from
public data with no new observing time. The second is spatial-control null
calibration for interferometric SETI, in which the same statistic is evaluated
at the star and at \NCtrl{} control positions so that the false-alarm rate is
measured and not assumed. The third is a quantitative accounting of the
frequency, power and drift domain actually searched, which gives the
non-detection explicit boundaries.""")

sub(r"""A further \NAudit{} candidate target/bands were selected but never delivered a
searchable product, and the cause lies in the selection step. Re-running the
crossmatch against the archive shows that \NNotPointed{} of them were
never observed at all, since no observing unit offered to those entries
contains the star. They sit a median \SepMedianDeg{} degrees from the nearest
field centre, because the observations were pointed at solar-system targets
whose quoted field of view is enormous, and a candidate crossmatch that trusts
that quantity will admit stars far outside any real primary beam. The
per-star pointing ledger is released. The remaining \NPointed{} entries are genuine processing
failures; re-running the failed set on the current code returned
\NRetryFail{} further failures in \NRetryAttempt{} attempts, its one recovery
falling outside Bands~3 to~8 and outside this release. A positional
crossmatch must not use the quoted field of view of an ephemeris or solar
delivery as a search radius.""",
    r"""A further \NAudit{} candidate target/bands were selected but never delivered
a searchable product, and the cause lies in the selection step. Re-running the
crossmatch shows that \NNotPointed{} of them were never observed at all, no
observing unit offered to those entries containing the star: they sit a median
\SepMedianDeg{} degrees from the nearest field centre, because the
observations were pointed at solar-system targets whose quoted field of view
is enormous, and a crossmatch that trusts that quantity admits stars far
outside any real primary beam. The remaining \NPointed{} entries are genuine
processing failures, and re-running them on the current code returned
\NRetryFail{} further failures in \NRetryAttempt{} attempts. A positional
crossmatch must not use the quoted field of view of an ephemeris or solar
delivery as a search radius, and the per-star pointing ledger is released so
that the error can be audited.""")

sub(r"""The AU~Mic crossing window of
\S\ref{sec:aumic} comes from the 2014 August~18 block of project
2012.1.00198.S, and one further public block of that project
(uid://A002/X7d80c7/X15c6, 2014 June~5) also covers the 230.83\,GHz
window and is the second epoch of its recurrence test.""",
    r"""The two blocks behind the AU~Mic recurrence test of \S\ref{sec:aumic} are
from project 2012.1.00198.S, executed 2014 August~18 and 2014 June~5.""")

# ------------------------------------------------------------------ S10-1
sub(r"""CP$-$72~2713 B7 & \FobsCpSeven & 5.81 & 5.68 & \FluxCpSeven &
\DnuCpSeven; \DvCpSeven{} (CO\,$3{\to}2$) & unattributed; no recurrence \\""",
    r"""CP$-$72~2713 B7 & \FobsCpSeven & 5.81 & 5.68 & \FluxCpSeven &
\DnuCpSeven; \DvCpSeven{} (CO\,$3{\to}2$) & unattributed; absent in epoch~2 \\""")

sub(r"""\quad unattributed, retired on non-recurrence & \NUnattrib{} \\""",
    r"""\quad unattributed, absent in a second epoch & \NUnattrib{} \\""")

sub(r"""\subsubsection*{CP$-$72~2713: an unattributed flag, and its retirement}

The fourth flag, towards CP$-$72~2713 in Band~7, never acquired an
astrophysical attribution and was marginal throughout.""",
    r"""\subsubsection*{CP$-$72~2713: an unattributed first-epoch event, absent in
the second epoch}

@@PARA@@The fourth stage-1 outlier, towards CP$-$72~2713 in Band~7, never
acquired an astrophysical attribution and was marginal throughout, its
$T_\star=5.81$ standing against a ring maximum of 5.68.""")

sub(r"""We recorded the window as an unattributed stage-1 flag,
a statistical or astrophysical feature rather than candidate evidence, under
criteria pinned in advance:""",
    r"""We recorded the window as an unattributed stage-1 spatial outlier, a
statistical or astrophysical feature and not candidate evidence, under
criteria pinned in advance:""")

sub(r"""The pinned criterion is met on the matched-frequency, matched-drift null of
the second epoch. We find no repeat, and therefore no evidence supporting a
\emph{persistent} technosignature at this frequency. The first-epoch event
remains unexplained, and it is statistically unexceptional at the survey
level. An intermittent emitter is not excluded by two epochs, and we do not
say it is.""",
    r"""The pinned criterion is met on the matched-frequency, matched-drift null of
the second epoch. The standing description of this window is therefore an
unattributed first-epoch threshold event that is absent in the second epoch.
We find no repeat and so no evidence supporting a \emph{persistent}
technosignature at this frequency; the first-epoch event itself remains
unexplained, it is statistically unexceptional at the survey level, and its
absence two hours later does not identify it as noise. An intermittent emitter
is not excluded by two epochs, and we do not say it is.""")

# ------------------------------------------------------------------ S10-2
sub(r"""stage-1 spatial outlier & a window whose $T_\star$ exceeds all \NCtrl{}
control statistics (``star-exceeds-ring''), a screening
device that carries no candidate significance (state 2) \\""",
    r"""stage-1 spatial outlier & a window whose $T_\star$ exceeds all \NCtrl{}
control statistics (``star-exceeds-ring''), a screening device that carries no
candidate significance (state 2); shortened to ``stage-1 outlier'' after first
use \\""")

sub(r"""A \emph{candidate} is a stage-1 flag
surviving every veto, and there are none. Three of the four flags have
independent CO evidence,""",
    r"""A \emph{candidate} is a stage-1 outlier surviving every veto, and there are
none. Three of the four have independent CO evidence,""")

sub(r"""None of the \NSpatial{} stage-1 flags exceeds this survey's own calibration or
separates from the empirical background and known astrophysical emission.""",
    r"""None of the \NSpatial{} stage-1 outliers exceeds this survey's own
calibration or separates from the empirical background and known astrophysical
emission.""")

sub(r"""\NSmearWorst{} of them, all
\SmearWorstChanKHz\,kHz Band~6 windows and so among the most drift-capable
here, carry effective thresholds
\SmearWorstPenLo--\SmearWorstPenHi$\times$ nominal, and \NSmearFlagged{}
are stage-1 flags.""",
    r"""\NSmearWorst{} of them, all \SmearWorstChanKHz\,kHz Band~6 windows and so
among the most drift-capable here, carry effective thresholds
\SmearWorstPenLo--\SmearWorstPenHi$\times$ nominal, and \NSmearFlagged{} are
stage-1 outliers.""")

sub(r"""\subsubsection*{Dispositions of the remaining flagged windows}

The third flag, towards HD~48370 in Band~6,""",
    r"""\subsubsection*{Dispositions of the remaining outlier windows}

@@PARA@@The third stage-1 outlier, towards HD~48370 in Band~6,""")

sub(r"""The flags also concentrate where the astrophysical
foreground is richest:""",
    r"""The outliers also concentrate where the astrophysical foreground is
richest:""")

sub(r"""which is where the
flags of \S\ref{sec:technosearch} concentrate,""",
    r"""which is where the stage-1 outliers of \S\ref{sec:technosearch}
concentrate,""")

sub(r"""No width admits a new
unattributed flag, and at every one of them CP$-$72~2713 is the only unmasked
unattributed flag.""",
    r"""No width admits a new unattributed outlier, and at every one of them
CP$-$72~2713 is the only unmasked one.""")

sub(r"""reclassifying all \NHits{} crossings at
$\pm20$, $\pm30$, $\pm50$ and $\pm100$\,km\,s$^{-1}$ admits no new
unattributed flag, and at every width CP$-$72~2713 remains the only unmasked
one.""",
    r"""reclassifying all \NHits{} crossings at $\pm20$, $\pm30$, $\pm50$ and
$\pm100$\,km\,s$^{-1}$ admits no new unattributed outlier, and at every width
CP$-$72~2713 remains the only unmasked one.""")

sub(r"""Four windows raised a stage-1 spatial screening
flag, and three are CO emission:""",
    r"""Four windows are stage-1 spatial outliers, and three of those are CO
emission:""")

sub(r"""and the crossing
fails the single-position variant too.""",
    r"""and the crossing fails the single-position variant too.""")

fz.apply(TEX, E)

# the released catalogue's disposition string must match Table 5
import re
gen = open('v342_calc.py', encoding='utf-8').read()
a = "'unattributed; retired on second-epoch non-recurrence'"
b = "'unattributed; absent in epoch 2'"
assert gen.count(a) == 1
open('v342_calc.py', 'w', encoding='utf-8').write(gen.replace(a, b))
print('catalogue disposition string aligned with Table 5')
