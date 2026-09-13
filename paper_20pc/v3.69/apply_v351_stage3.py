#!/usr/bin/env python3
"""v3.51 stage 3: the spectral-response-corrected threshold becomes the
principal physical number (referees C3 and D2), and the three sensitivity
quantities are named and kept apart throughout (referee D1).

The nominal 5 sigma value keeps exactly one job, the pipeline trigger
P_trig.  Wherever a physical transmitter power is compared, the number
quoted is the effective unresolved-carrier threshold
P_eff = HanFacMed x P_trig, with the 2.00-2.67 placement envelope stated.
This changes an answer: at the deepest window the corrected threshold is
EirpEffDeepest W, so no system in the survey reaches Arecibo-class total
power once the instrument's spectral response is included.  That is said
plainly rather than buried.

  S3-1  Abstract: both numbers, the corrected one against the benchmark,
        the 0.5-2x completeness-transfer bracket, and the Class B share.
  S3-2  The boxed reading rule: P_trig, C(P), P_90/P_95 defined together.
  S3-3  Table 2 gains the effective threshold rows.
  S3-4  The benchmark paragraph, recomputed on P_eff.
  S3-5  The three detectability cases, recomputed on P_eff.
  S3-6  Conclusions: corrected numbers and the transfer bracket.
  S3-7  Sec. 4.1's systematic budget: the response term named as the one
        that is now carried rather than merely listed.
"""
import importlib.util

spec = importlib.util.spec_from_file_location('fz', '.fzsub2.py')
fz = importlib.util.module_from_spec(spec)
spec.loader.exec_module(fz)

TEX = 'technosignatures_20pc_v3.51.tex'
E = []


def sub(a, b):
    E.append((a, b))


# ------------------------------------------------------------------ S3-1
sub(r"""We have searched \NWindows{} archival ALMA spectral windows,
\UnionLo--\UnionHi\,GHz (Bands~3--8), toward \NStars{} stars in
\NSystems{} systems within 40\,pc for unresolved spectral carriers,
comparing each stellar position with \NCtrl{} control positions in an
annulus around it. \textbf{No credible technosignature is found.}
The sample is every star within 40\,pc with public-archive coverage. It is
archive-target-complete but \emph{epoch}-incomplete: only \NEB{} of the
\NProgenitorEB{} public execution blocks those targets hold were searched
(\S\ref{sec:sample}). It holds \PctSampleOfCensus{} per cent of that
volume's stars, over-representing F and G types and under-representing
M~dwarfs, so the null bears only weakly on the habitable-zone question.
Barnard's Star and Wolf~359 gain first millimetre technosignature limits.
Four windows are stage-1 spatial outliers. Two toward $\beta$~Pic and one
toward HD~48370 match known circumstellar or foreground CO. The fourth,
toward CP$-$72~2713, has no astrophysical attribution and does not recur in
a second, deeper block at the same tuning, so we find no evidence for a
persistent transmitter; two epochs cannot exclude an intermittent one.
Thresholds are nominal trigger levels, not completeness limits. They span
$\EirpMinA$--$\EirpMaxA$\,W EIRP over the \NWinA{} drift-resolved windows
and $\EirpMinB$--$\EirpMaxB$\,W over the \NWinB{} unresolved-spectral-excess
ones, and $\EirpHanMinA$--$\EirpHanMaxA$\,W and
$\EirpHanMinB$--$\EirpHanMaxB$\,W once the instrument's spectral response is
included. Two limitations bind. The noise scale comes from the annulus, so
it carries no variance belonging to the stellar position alone. And the
statistic and line mask were defined on these data, so the rank figures
describe this dataset; a held-out check on \HOWindows{} later-searched
windows is reported separately. The search is polarisation-blind.""",
    r"""We have searched \NWindows{} archival ALMA spectral windows,
\UnionLo--\UnionHi\,GHz (Bands~3--8), toward \NStars{} stars in \NSystems{}
systems within 40\,pc for unresolved spectral carriers, comparing each stellar
position with \NCtrl{} control positions in an annulus around it. \textbf{No
credible technosignature is found.} The sample is every star we identify as
having qualifying public ALMA coverage: archive-target-complete but
\emph{epoch}-incomplete, only \NEB{} of the \NProgenitorEB{} public execution
blocks those targets hold being searched (\S\ref{sec:sample}). It holds
\PctSampleOfCensus{} per cent of that volume's stars, over-representing F and
G types and under-representing M~dwarfs, so the null bears only weakly on the
habitable-zone question. Barnard's Star and Wolf~359 gain first millimetre
technosignature limits. Four windows are stage-1 spatial outliers. Two toward
$\beta$~Pic and one toward HD~48370 match known circumstellar or foreground
CO. The fourth, toward CP$-$72~2713, has no astrophysical attribution and is
absent from a second, deeper block at the same tuning, so we find no evidence
for a persistent transmitter; two epochs cannot exclude an intermittent one.
Two thresholds should be distinguished. The nominal $5\sigma$ trigger spans
$\EirpMinA$--$\EirpMaxA$\,W EIRP over the \NWinA{} drift-resolved windows and
$\EirpMinB$--$\EirpMaxB$\,W over the \NWinB{} unresolved-spectral-excess ones,
which are \PctCoarse{} per cent of the sample and carry no drift
discrimination. The effective threshold for an unresolved carrier, which is
the number to compare with a transmitter power, is $\times\HanFacMed$ higher
under ALMA's spectral response, $\EirpEffMinA$--$\EirpEffMaxA$\,W and
$\EirpEffMinB$--$\EirpEffMaxB$\,W; on that basis no system here reaches
Arecibo-class total power. Neither is a completeness limit: recovery is
calibrated on one configuration and transfers to the rest only within a
factor $0.5$--$2$. Two limitations bind. The statistic and line mask were
defined on these data, so the rank figures describe this dataset, and a
held-out check on \HOWindows{} windows searched afterwards is reported
separately. The search is polarisation-blind.""")

# ------------------------------------------------------------------ S3-2
sub(r"""\noindent\textbf{How to read every limit in this paper.}
\emph{Every EIRP$_{5\sigma}$ value here is a nominal, local
instrumental detection threshold, the \emph{trigger power}
$P_{\rm trig}$: five times the per-channel rms of
the searched window, at that window's native channel width, for a transmitter at the star's position matching the searched
spectral morphology, with a measured recovery rising with the fraction
of the track the carrier occupies its channel, highest for a continuous
one (\S\ref{sec:ancillary},
Appendix~\ref{app:inject}). A calibrated completeness limit is a different
quantity, the power $P_x$ at which recovery reaches $x$ per cent.
$P_{50}=1.10\,P_{\rm trig}$ and $P_{90}>2\,P_{\rm trig}$ for the
calibration configuration's drifting class, both carrying an
\emph{unbounded} transfer systematic to any other configuration
(bracketed as $0.5$--$2\times$, Appendix~\ref{app:population}), where
they are \emph{not determined}; $P_{\rm trig}$ is quoted throughout. ALMA's
native channelisation sets it, so it is a total-power threshold and no measure
of Hz-resolution sensitivity, optimistic by $\times\HanFacBest$ to
$\times\HanFacWorst$ under the
instrument's Hanning response (Appendix~\ref{app:conventions}). Every
headline EIRP is quoted beside its native channel width, and the
machine-readable catalogue carries the nominal threshold and both
Hanning-corrected values per window. The same reading applies to
every subsequent ``5$\sigma$''.}""",
    r"""\noindent\textbf{How to read every limit in this paper.}
\emph{Three quantities are kept apart throughout, and only the first is what
the pipeline acts on.}

@@PARA@@\emph{The \textbf{trigger power} $P_{\rm trig}$ is the nominal
EIRP$_{5\sigma}$: five times the searched window's per-channel rms, at that
window's native channel width, for a transmitter at the star's position
matching the searched morphology. It is the level at which the search fires,
it is what every ``$5\sigma$'' below means, and it is what the figures label
as the nominal trigger.}

@@PARA@@\emph{The \textbf{effective unresolved-carrier threshold}
$P_{\rm eff}$ is $P_{\rm trig}$ corrected for the instrument's spectral
response. ALMA applies online Hanning smoothing, which leaves only
\HanWorst{} to \HanBest{} of a sub-channel tone's power in the peak channel
depending on where in the channel it falls, median \HanMed{}
(Appendix~\ref{app:conventions}). Nominal thresholds are therefore optimistic
by $\times\HanFacBest$ to $\times\HanFacWorst$, median $\times\HanFacMed$, and
$P_{\rm eff}=\HanFacMed\,P_{\rm trig}$ is the number to compare with any
transmitter power. It is not a small correction and we treat it as the
principal physical threshold.}

@@PARA@@\emph{The \textbf{completeness limit} $P_x$, the power at which
measured recovery reaches $x$ per cent, is a different quantity again and is
determined here for one configuration only:
$P_{50}=1.10\,P_{\rm trig}$ and $P_{90}>2\,P_{\rm trig}$ on the calibration
window's drifting class (Appendix~\ref{app:inject}). Transferring that curve
to a window observed in another band, channelisation or integration time is
an assumption, bracketed at $0.5$--$2\times$ (Appendix~\ref{app:population});
elsewhere $P_{90}$ and $P_{95}$ are \emph{not determined}. What this survey
has is a measured reference recovery function of incompletely established
transferability, and not a measured Class~A completeness function.}

@@PARA@@\emph{Every headline EIRP is quoted beside its native channel width,
and the machine-readable catalogue carries $P_{\rm trig}$ and both
response-corrected values per window.}""")

# ------------------------------------------------------------------ S3-3
sub(r"""Nominal $P_{\rm trig}$, Class A (\ChanLoA--\ChanHiA\,kHz) & $\EirpMinA$--$\EirpMaxA$\,W (median $\EirpMedA$) \\
Nominal $P_{\rm trig}$, Class B (\ChanLoB--\ChanHiB\,MHz) & $\EirpMinB$--$\EirpMaxB$\,W (median $\EirpMedB$) \\
\quad worst-case Hanning-corrected medians & $\EirpHanMedA$ / $\EirpHanMedB$\,W \\""",
    r"""Nominal trigger $P_{\rm trig}$, Class A (\ChanLoA--\ChanHiA\,kHz) & $\EirpMinA$--$\EirpMaxA$\,W (median $\EirpMedA$) \\
Nominal trigger $P_{\rm trig}$, Class B (\ChanLoB--\ChanHiB\,MHz) & $\EirpMinB$--$\EirpMaxB$\,W (median $\EirpMedB$) \\
Effective $P_{\rm eff}=\HanFacMed\,P_{\rm trig}$, Class A & $\EirpEffMinA$--$\EirpEffMaxA$\,W (median $\EirpEffMedA$) \\
\quad Class B & $\EirpEffMinB$--$\EirpEffMaxB$\,W (median $\EirpEffMedB$) \\""")

# ------------------------------------------------------------------ S3-4
sub(r"""The EIRP thresholds are compared throughout to an Arecibo-like planetary
radar \citep[][EIRP $2\times10^{13}$\,W]{Drake1974,EarthDetectingEarth2025},
which is a technological \emph{power} scale carrying no transmitter model. It is an \ArecGHz\,GHz number, and aperture gain scales as
$\nu^{2}$, so the same aperture and transmitter power at 230\,GHz would
radiate $2\times10^{13}\times(230/\ArecGHz)^{2}\simeq\ArecScaledW\times10^{17}$\,W.
The Arecibo figure carries that dish's real aperture efficiency; the
frequency-matched benchmark below is geometric. That benchmark is a
12-m aperture radiating 1\,MW at 230\,GHz, EIRP
${\approx}8\times10^{14}$\,W, within a factor of two of the median
Class~A threshold $\EirpMedA$\,W.""",
    r"""The thresholds are compared throughout to an Arecibo-like planetary radar
\citep[][EIRP $\AreciboW$\,W]{Drake1974,EarthDetectingEarth2025}, which is a
technological \emph{power} scale carrying no transmitter model. It is an
\ArecGHz\,GHz number, and aperture gain scales as $\nu^{2}$, so the same
aperture and transmitter power at 230\,GHz would radiate
$\AreciboW\times(230/\ArecGHz)^{2}\simeq\ArecScaledW\times10^{17}$\,W. Because
this comparison is between physical transmitter powers, it must use
$P_{\rm eff}$ and not the trigger: on the nominal figure the deepest window in
the survey sits below Arecibo-class power, and on the effective one it does
not, the deepest becoming $\EirpEffDeepest$\,W, so \CaseDetEffArec{} systems
reach that scale and \CaseDetEffArecTwo{} reaches twice it. A second, more
intuitive benchmark is frequency-matched and purely geometric: a 12-m aperture
radiating 1\,MW at 230\,GHz, EIRP ${\approx}8\times10^{14}$\,W, which the
median Class~A effective threshold $\EirpEffMedA$\,W misses by a factor
\BenchEffRatio.""")

# ------------------------------------------------------------------ S3-5
sub(r"""\emph{(i) A continuous, frequency-stationary carrier} in a coarse channel is
the best case. The UV~Ceti pair at 2.7\,pc has a deepest window of
$1.6\times10^{13}$\,W, and a channel-confined carrier there is recovered at
near-ideal $\sqrt{N}$ gain (\S\ref{sec:dwell}). A carrier matching the
\emph{total} EIRP of an Arecibo-like planetary radar (\S\ref{sec:benchmarks})
is therefore detectable toward the nearest systems at 15.625-MHz resolution:
\CaseDetCoarseNow{} system of \NSystems{} qualifies, and
\CaseDetCoarseTwoNow{} at twice the power.""",
    r"""\emph{(i) A continuous, frequency-stationary carrier} in a coarse channel is
the best case. The UV~Ceti pair at 2.7\,pc has a deepest window whose trigger
is $1.6\times10^{13}$\,W and whose effective threshold is
$\EirpEffDeepest$\,W, and a channel-confined carrier there is recovered at
near-ideal $\sqrt{N}$ gain (\S\ref{sec:dwell}). Read on the trigger,
\CaseDetCoarseNow{} system of \NSystems{} reaches Arecibo-class total power
and \CaseDetCoarseTwoNow{} reach twice it; read on the effective threshold,
which is the comparison a transmitter power calls for, \CaseDetEffArec{} do
and \CaseDetEffArecTwo{} does. The survey's best case is therefore a few times
an Arecibo-class radar rather than one.""")

# ------------------------------------------------------------------ S3-6
sub(r"""\emph{The defensible
sensitivity and search domain.} EIRP$_{5\sigma}$ values are nominal trigger
powers, not completeness limits (boxed rule, \S\ref{sec:method}). They run
$\EirpMinA$--$\EirpMaxA$\,W over Class~A and $\EirpMinB$--$\EirpMaxB$\,W over
Class~B; corrected for the instrument's Hanning response, which the nominal
figures ignore, the same windows reach $\EirpHanMinA$--$\EirpHanMaxA$\,W and
$\EirpHanMinB$--$\EirpHanMaxB$\,W. That is deep enough for an unresolved
carrier matching the total power of an Arecibo-like planetary radar toward
\CaseDetCoarseNow{} of the \NSystems{} systems. Sensitivity is calibrated end
to end for one configuration only (Appendix~\ref{app:inject}), $\sigma$ is
estimated from the annulus and so carries no variance belonging to the stellar
position alone, and the conditional searched-domain transmitter fraction stays
illustrative (Appendix~\ref{app:population}). The \emph{Scope of the
constraints} box of \S\ref{sec:method} fixes what the non-detection binds;
outside it nothing is bounded.""",
    r"""\emph{The defensible sensitivity and search domain.} The nominal
EIRP$_{5\sigma}$ values are trigger powers and not completeness limits (boxed
rule, \S\ref{sec:method}). They run $\EirpMinA$--$\EirpMaxA$\,W over Class~A
and $\EirpMinB$--$\EirpMaxB$\,W over Class~B. The number to set against a
transmitter is the effective unresolved-carrier threshold, $\times\HanFacMed$
higher under the instrument's spectral response, $\EirpEffMinA$--$\EirpEffMaxA$
and $\EirpEffMinB$--$\EirpEffMaxB$\,W, and on that scale \CaseDetEffArec{} of
the \NSystems{} systems reach the total power of an Arecibo-like planetary
radar. Neither figure is a completeness limit: recovery is calibrated end to
end on one configuration (Appendix~\ref{app:inject}) and transfers to the
others only within a bracket of $0.5$--$2\times$, so what the survey holds is
a reference recovery function whose transferability is incompletely
established. The conditional searched-domain transmitter fraction stays
illustrative (Appendix~\ref{app:population}), and the \emph{Scope of the
constraints} box of \S\ref{sec:method} fixes what the non-detection binds.""")

# ------------------------------------------------------------------ S3-7
sub(r"""They are the ALMA absolute flux
scale, 5--10 per cent and band- and epoch-dependent; residual atmospheric
phase after water-vapour correction and phase referencing; the primary-beam
model at the stellar offset; the instrumental spectral response, median
$\times\HanFacMed$ by the boxed rule below; and visibility calibration.""",
    r"""They are the ALMA absolute flux scale, 5--10 per cent and band- and
epoch-dependent; residual atmospheric phase after water-vapour correction and
phase referencing; the primary-beam model at the stellar offset; the
instrumental spectral response, median $\times\HanFacMed$, which is the
largest of the five and is carried explicitly as $P_{\rm eff}$ by the boxed
rule below rather than left in the budget; and visibility calibration.""")

fz.apply(TEX, E)
