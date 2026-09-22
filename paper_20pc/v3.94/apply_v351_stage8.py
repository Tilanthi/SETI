#!/usr/bin/env python3
"""v3.51 stage 8: the de-AI sweep, and the compression that gets back to 29.

Stage 7's additions pushed the antithesis count from 38 to 54, almost all of
it my own new ``rather than'' constructions.  This stage removes them at
source, which also shortens the text, and compresses the two appendices that
grew.  Referee C's complaint about compressed, note-like sentences is
answered in the other direction: nothing here is compressed by dropping a
connective, only by dropping a repetition.
"""
import importlib.util

spec = importlib.util.spec_from_file_location('fz', '.fzsub2.py')
fz = importlib.util.module_from_spec(spec)
spec.loader.exec_module(fz)

TEX = 'technosignatures_20pc_v3.51.tex'
E = []


def sub(a, b):
    E.append((a, b))


# --------------------------------------------------- de-AI: antithesis out
sub(r"""instrumental spectral response, median $\times\HanFacMed$, which is the
largest of the five and is carried explicitly as $P_{\rm eff}$ by the boxed
rule below rather than left in the budget; and visibility calibration.""",
    r"""instrumental spectral response, median $\times\HanFacMed$, which is the
largest of the five and is carried explicitly as $P_{\rm eff}$ by the boxed
rule below; and visibility calibration.""")

sub(r"""drift grid and the thousands of channels apply identically to both, the
per-window trials factor is absorbed empirically rather than modelled. Under""",
    r"""drift grid and the thousands of channels apply identically to both, the
per-window trials factor is absorbed empirically. Under""")

sub(r"""observed, $P=\SbrPobs$ under an independent-Poisson approximation, and that
excess is astrophysical rather than statistical: genuine celestial line
emission sits at the stellar position in \SbrAstro{} of the \SbrN{}""",
    r"""observed, $P=\SbrPobs$ under an independent-Poisson approximation, and that
excess is astrophysical. Genuine celestial line emission sits at the stellar
position in \SbrAstro{} of the \SbrN{}""")

sub(r"""gives $D=\HOKsDAll$ ($p=\HOKsPAll$), the departure being the
astrophysical signal rather than a defect.""",
    r"""gives $D=\HOKsDAll$ ($p=\HOKsPAll$), and the departure is the astrophysical
signal.""")

sub(r"""That is the astrophysical line emission identified below rather than a
misbehaving ensemble, but the departure is genuine, so""",
    r"""That fits the astrophysical line emission identified below, with no
misbehaving ensemble, but the departure is genuine, so""")

sub(r"""The six share a signature rather than a programme: all are
\DefectArrays{} array,""",
    r"""The six share a signature. They are all \DefectArrays{} array,""")

sub(r"""(\StatSymHash, \StatSymDate), so the revision precedes
that flag rather than following it; and because the region maximum for that
window already lay on the star, both statistics return the same $T_\star$""",
    r"""(\StatSymHash, \StatSymDate), so the revision precedes that flag. And
because the region maximum for that window already lay on the star, both
statistics return the same $T_\star$""")

sub(r"""The survey's best case is therefore a few times
an Arecibo-class radar rather than one.""",
    r"""The survey's best case is therefore a few times Arecibo-class power.""")

sub(r"""a second block is often a baseline of hours
rather than of years, and which it is can be settled with one archive query
before any download.""",
    r"""a second block often supplies a baseline of only hours, and which it is can
be settled with one archive query before any download.""")

sub(r"""and those channels are unsearched by our choice rather than
inaccessible to ALMA.""",
    r"""and those channels are unsearched here because the analysis vetoes them,
while ALMA can see them perfectly well.""")

sub(r"""That work is under way rather than proposed:
\HOBlocks{} blocks toward \HOStars{} stars,""",
    r"""That work is under way: \HOBlocks{} blocks toward \HOStars{} stars,""")

sub(r"""so we report it as an open systematic rather than as settled:
the honest reading is that the crossing list is dominated by CO($2{\to}1$) at
230.5\,GHz toward disc hosts and that a residual excess of on-star chance
crossings at the tens-of-per-cent level cannot be excluded.""",
    r"""so we report it as an open systematic. The honest reading is that the
crossing list is dominated by CO($2{\to}1$) at 230.5\,GHz toward disc hosts,
and that a residual excess of on-star chance crossings at the
tens-of-per-cent level cannot be excluded.""")

sub(r"""The annulus cannot close that gap, and correlation widens it:
with $N_{\rm eff}\simeq30$--$43$ independent spatial trials the ensemble's real rank resolution is \RankEffLo--\RankEffHi{} rather than $\RankFloorVal$, so
the gap to the Bonferroni scale is a factor \BonfGapEffLo{} to
\BonfGapEffHi.""",
    r"""The annulus cannot close that gap, and correlation widens it. With
$N_{\rm eff}\simeq30$--$43$ independent spatial trials the ensemble can really
resolve only \RankEffLo--\RankEffHi, and the gap to the Bonferroni scale
becomes a factor \BonfGapEffLo{} to \BonfGapEffHi.""")

# --------------------------------------------- compression: app:provenance
sub(r"""This appendix holds the analysis
history: how the search statistic came to be what it is, the checks run on the
windows the old statistic flagged, the frame audit behind the CO attributions,
the line-mask repair, and the entries excluded from the released catalogue.
None of it changes a number in the main text, and it is collected here so the
main text can present the experiment rather than its history.

\subsection*{Chronology of the statistic revision} An earlier region-max
statistic maximised over an $n_{\rm src}=\RingNSrc$-position region centred on
the star against \NCtrl{} single-position controls, and under it a crossing
towards AU~Mic in Band~6 at 230.83\,GHz was carried as a candidate. The
released repository dates both steps. That flag is first committed on
\StatFlagDate{} (\texttt{\StatFlagHash}), in the manuscript of the day and in
its machine-readable aggregate. The asymmetry is identified and the symmetric
form of Eq.~\ref{eq:tstar} adopted as operative \StatGapDays{} days later, on
\StatSymDate{} (\texttt{\StatSymHash}). The redesign therefore postdates the
flag. The argument for it rests on algebra that owes nothing to these data:
under exchangeability an $n_{\rm src}$-position maximum at the star against
single-position controls ranks first with probability $n_{\rm src}/(n_{\rm
src}+\NCtrl)=\AsymExpectPct$ per cent, and the symmetric form removes that
inflation.""",
    r"""This appendix holds the analysis history: how the search statistic came to
be what it is, the checks run on the windows the old statistic flagged, the
frame audit behind the CO attributions, the line-mask repair, and the entries
excluded from the released catalogue. None of it changes a number in the main
text.

@@PARA@@\subsection*{Chronology of the statistic revision} An earlier
region-max statistic maximised over an $n_{\rm src}=\RingNSrc$-position region
centred on the star against \NCtrl{} single-position controls, and under it a
crossing towards AU~Mic in Band~6 at 230.83\,GHz was carried as a candidate.
The released repository dates both steps. That flag is first committed on
\StatFlagDate{} (\texttt{\StatFlagHash}), in the manuscript of the day and in
its machine-readable aggregate, and the symmetric form of Eq.~\ref{eq:tstar}
is adopted as operative \StatGapDays{} days later, on \StatSymDate{}
(\texttt{\StatSymHash}). The redesign therefore postdates the flag. Its
justification is algebra that owes nothing to these data, since under
exchangeability an $n_{\rm src}$-position maximum at the star against
single-position controls ranks first with probability
$n_{\rm src}/(n_{\rm src}+\NCtrl)=\AsymExpectPct$ per cent, which the
symmetric form removes.""")

sub(r"""The within-window
add-one rank of the AU~Mic crossing is $p=0.021$. That is a different quantity
from the survey-wide rate at which any window's ring maximum reaches 5.97,
$p=\AuP$, and both are far from the $1/\RankFloor$ floor. Under the three
treatments that decide the crossing, namely the frozen region-max products, a
fully symmetric reprocessing of the same first-epoch block, and the
second-epoch block of the same programme, the star statistic is 5.97, 4.93 and
4.77 against control maxima of 5.85, 7.70 and 6.78, with add-one star ranks
$p=0.81$ and $0.97$ in the latter two.""",
    r"""The within-window add-one rank of the AU~Mic crossing is $p=0.021$, a
different quantity from the survey-wide rate at which any window's ring
maximum reaches 5.97, $p=\AuP$, and both are far from the $1/\RankFloor$
floor. Under the three treatments that decide the crossing, the frozen
region-max products, a fully symmetric reprocessing of the same first-epoch
block, and the second-epoch block of the same programme, the star statistic is
5.97, 4.93 and 4.77 against control maxima of 5.85, 7.70 and 6.78, with
add-one star ranks $p=0.81$ and $0.97$ in the latter two.""")

sub(r"""\emph{Statistical scale.} The
on-source peak (5.97) sits at the \AuPct{}th percentile of the control-maxima
distribution over all \NWindows{} windows (median \CtrlMed, 90th percentile
\CtrlPninety): \AuNge{} windows (\AuFrac{} per cent) match or exceed it,
add-one empirical $p=\AuP$ before any multiple-testing correction. The
crossing matches no catalogued molecular transition
(Table~\ref{tab:bpicaudit}), and closure-phase vetting finds it point-source
consistent, which is one-sided evidence (Appendix~\ref{app:closure}). Two
astrophysical contexts are recorded for re-examination and neither grounds the
rejection. AU~Mic is an exceptionally active flare star, but the block's own
quiescent continuum (0.15\,mJy) rules out the later-epoch GHz-wide flares of
\citet{MacGregor2020} (16.8 and 6.1\,mJy): an 11\,mJy channel-confined excess
would sit ${\sim}70\times$ above a continuum that shows nothing. The controls
share the primary-beam footprint, so smooth structure such as the debris belt
raises star and controls alike and cannot alone produce a localised excess.""",
    r"""\emph{Statistical scale.} The on-source peak (5.97) sits at the \AuPct{}th
percentile of the control-maxima distribution over all \NWindows{} windows,
\AuNge{} of which (\AuFrac{} per cent) match or exceed it, add-one empirical
$p=\AuP$ before any multiple-testing correction. The crossing matches no
catalogued molecular transition (Table~\ref{tab:bpicaudit}), and closure-phase
vetting finds it point-source consistent, which is one-sided evidence
(Appendix~\ref{app:closure}). Two astrophysical contexts are recorded for
re-examination and neither grounds the rejection. AU~Mic is an exceptionally
active flare star, but the block's own quiescent continuum (0.15\,mJy) rules
out the later-epoch GHz-wide flares of \citet{MacGregor2020} (16.8 and
6.1\,mJy), since an 11\,mJy channel-confined excess would sit
${\sim}70\times$ above a continuum that shows nothing. And the controls share
the primary-beam footprint, so smooth structure such as the debris belt raises
star and controls alike and cannot by itself produce a localised excess.""")

fz.apply(TEX, E)
