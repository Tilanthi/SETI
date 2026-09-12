#!/usr/bin/env python3
"""v3.50 stage 6: pay the remaining page debt out of triply stated material.

Referee A's assessment is that almost every objection has produced another
paragraph.  The clearest instances are the completeness numbers, which
v3.49 states in the boxed rule of section 4, again in section 4.3, again
in section 4.4 and again in Appendix B; and the ancillary lanes, which the
paper itself says carry no disposition.  Each survives once, in the place
that owns it.

  D1  Section 4.3's injection summary duplicates Appendix B and the boxed
      rule.  Reduced to what the main text depends on.
  D2  The ancillary continuum appendix loses its second statement of the
      error model, which is already given as an equation.
  D3  The Data Availability release inventory is compressed from a
      ten-clause list to four sentences.  No item is dropped.
  D4  Background: the pilot-overlap answer is one sentence, not four.
"""
import re
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


# -------------------------------------------------------------------- D1
sub(r"""\emph{Injection-recovery validation} (Appendix~\ref{app:inject}).
Synthetic tones of known amplitude were injected into real visibilities
and recovered with the unmodified pipeline: \NTrials{} trials across six
window configurations, three bands and both resolution classes. The
pipeline's baseline step is a per-integration block median along
\emph{frequency}
(Table~\ref{tab:algorithm}, step~4), which by construction cannot remove
a feature confined to one or two channels, and its de-drift step is an
inverse-variance-weighted sum over integrations, which accumulates a
persistent carrier coherently. Appendix~\ref{app:inject} tells one validation-history item in full. The
campaign's original report of 0 of 500 coarse-window recoveries was an
artefact of its recovery \emph{criterion} and never of the search
pipeline. The corrected
criterion has not been re-derived by an independent
implementation, and that cross-check is an open item
(\S\ref{sec:futurework}). The independent evidence is the dwell campaign
of \S\ref{sec:dwell}, which measures persistent near-static carriers as
\emph{recovered} (Table~\ref{tab:dwell}), reversing the artefact's reading.

The primary statistic has no automated injection test on every pipeline
change; three quantified checks bound undetected pipeline faults
instead: the machinery-only lane (fidelity $-9$/$+14$ per cent, the
bound that caught this artefact), the AU~Mic re-analyses of
\S\ref{sec:aumic} under three treatments, whose recomputation agrees
with the released products, and the pseudo-star rank uniformity
(\NPseudo{} pooled ranks uniform, mean \PseudoMean{} against 0.5, KS
$p=\PseudoKSp$), which any defect of the statistic itself would
displace. For the drifting class on the fine window, recovery is 17,
\RecThresh, 58, 75 and \RecTwice{} per cent at $4$, $5$, $6$, $8$ and
$10\sigma$, measured on the single calibration configuration of one
star and one Band~6 window and transferred by assumption to all \NWinA{}
Class~A windows, an error the bracketing of
Appendix~\ref{app:population} treats as a 0.5--2$\times$ rescaling. That
gives EIRP$_{50}=1.10\,$EIRP$_{5\sigma}$ and, as a bound,
EIRP$_{90}>2.0\,$EIRP$_{5\sigma}$, each with an unbounded transfer
systematic bracketed as $0.5$--$2\times$
(Fig.~\ref{fig:completeness}, Table~\ref{tab:classcomp}). Tables here
stay in nominal EIRP$_{5\sigma}$.""",
    r"""\emph{Injection-recovery validation} (Appendix~\ref{app:inject}).
Synthetic tones of known amplitude were injected into real visibilities and
recovered with the unmodified pipeline, \NTrials{} trials across six window
configurations, three bands and both resolution classes. Two properties of
the pipeline matter for reading the result. The baseline step is a
per-integration block median along \emph{frequency}
(Table~\ref{tab:algorithm}, step~4), which by construction cannot remove a
feature confined to one or two channels. The de-drift step is an
inverse-variance-weighted sum over integrations, which accumulates a
persistent carrier coherently. Appendix~\ref{app:inject} gives the measured
recovery curve, and the completeness it supports is stated once, in the
boxed rule of \S\ref{sec:method}. Tables here stay in nominal
EIRP$_{5\sigma}$.

One validation-history item is told in full in Appendix~\ref{app:inject}.
The campaign's original report of 0 of 500 coarse-window recoveries was an
artefact of its recovery \emph{criterion} and never of the search pipeline.
The corrected criterion has not been re-derived by an independent
implementation, and that cross-check is an open item
(\S\ref{sec:futurework}). The independent evidence is the dwell campaign of
\S\ref{sec:dwell}, which measures persistent near-static carriers as
\emph{recovered} and so reverses the artefact's reading.

The primary statistic has no automated injection test on every pipeline
change. Three quantified checks bound undetected pipeline faults instead:
the machinery-only lane, whose amplitude fidelity of $-9$/$+14$ per cent is
the bound that caught the artefact above; the AU~Mic re-analyses under
three treatments, whose recomputation agrees with the released products;
and the pseudo-star rank uniformity over \NPseudo{} pooled ranks
($p=\PseudoKSp$), which any defect of the statistic itself would
displace.""")

# -------------------------------------------------------------------- D2
sub(r"""The continuum lane is an exploratory by-product, with
57 measurements, 17 detections and 40 limits, a millimetre excess being
at best an indirect, model-dependent observable of waste-heat
technology. An ``upper limit'' is $5\times$ the
primary-beam-corrected map rms at the star's position, and the deepest
non-detection is towards TRAPPIST-1 in Band~3. Under the combined error
model sixteen of seventeen detections stay above $5\sigma$; the
exception ($\eta$~Corvi Band~7, $4.7\sigma$ combined) is marginal.
Bright far-from-target peaks fall outside the 3-arcsec tolerance and count
as non-detections.""",
    r"""The continuum lane is an exploratory by-product: 57 measurements, 17
detections and 40 limits. A millimetre excess is at best an indirect and
model-dependent observable of waste-heat technology. An ``upper limit''
here is $5\times$ the primary-beam-corrected map rms at the star's
position, and the deepest non-detection is towards TRAPPIST-1 in Band~3.
Under the combined error model sixteen of the seventeen detections stay
above $5\sigma$, the exception being $\eta$~Corvi Band~7 at $4.7\sigma$.""")

sub(r"""\emph{The anomaly screen.} Each star's flux is tested against its own
photospheric expectation (Planck function with Gaia DR3 parameters,
Pecaut \& Mamajek fallback where GSP-Phot is unavailable) and against
same-$T_{\rm eff}$ stars in coarse bins of at least five, by a robust
median/MAD statistic. The error model, evaluated before any flag,
is $\sigma_{\rm tot}^{2} = \sigma_{\rm map}^{2} + (f_{\rm cal}\,S_\nu)^{2}
+ \sigma_{\rm model}^{2}$, with $f_{\rm cal}$ 5 per cent in Bands~3--6
and 10 per cent in Bands~7--8 and $\sigma_{\rm model}$ propagated from
Gaia temperature and radius errors and the fallback relation's scatter.
The model has \emph{no intrinsic-variability term}, which is adequate for
a photosphere and wrong for an active M dwarf whose millimetre flux can
vary by factors of several, so the screen is uninformative for exactly
the stars a radio-stellar reader cares about, and at the five-star
minimum it flags for inspection, without testing per-star hypotheses.
One outlier results: $\chi^1$~Ori at Band~3 (excess ratio 2.52, resampled
tail probability 0.53 in its six-star bin), consistent with a spectroscopic
G0V binary's unresolved companion or a chromosphere.""",
    r"""\emph{The anomaly screen.} Each star's flux is tested by a robust
median/MAD statistic against its own photospheric expectation and against
same-$T_{\rm eff}$ stars in coarse bins of at least five. The error model,
fixed before any flag, adds the map noise, a calibration term of 5 per cent
in Bands~3--6 and 10 per cent in Bands~7--8, and a model term propagated
from the Gaia temperature and radius errors. It has \emph{no
intrinsic-variability term}. That is adequate for a photosphere and wrong
for an active M dwarf, whose millimetre flux can vary by factors of
several, so the screen is uninformative for exactly the stars a
radio-stellar reader cares about. It flags for inspection and tests no
per-star hypothesis. One outlier results, $\chi^1$~Ori at Band~3,
consistent with a spectroscopic G0V binary's unresolved companion or a
chromosphere.""")

# -------------------------------------------------------------------- D3
sub(r"""The complete release will also be deposited on Zenodo, with a DOI minted
on final acceptance and inserted here. It comprises (i) per-window
search products for all \NWindows{} windows: spectral extracts,
per-drift-trial peak statistics, the machine-readable line-exclusion
mask in both its frozen and repaired forms (\S\ref{sec:linecost}),
archive UID, epoch-propagated target coordinates and field centre,
primary-beam gain, channel frequencies and widths, the drift grid, and
the target statistic with all \NCtrl{} control statistics from which the
rank and $p$-value are recomputable; (ii) control-ensemble calibration
products at all \NCtrl{} positions; (iii) closure-phase and
population-anomaly outputs; (iv) the full injection-recovery campaign
products, all \NTrials{} trials of Appendix~\ref{app:inject} and all
\NDwellTrials{} dwell trials, together with the second-stage local-null
code, its per-window outputs and the retained null-draw arrays
(\S\ref{sec:technosearch}); (v) the frozen pipeline code and input
data snapshot with its change-log; (vi) the execution-block metadata and
integration-time audit tables; (vii) the serendipitous molecular-line catalogue,
\texttt{line\_catalogue.json}, written by the pipeline's own continuum
line-exclusion step; (viii) the
execution-block availability census of \S\ref{sec:sample}, from the ALMA
datalink service, with its per-star ledger and the annulus-geometry and
smearing-census table fragments generated for this paper; and (ix) the
retained per-integration dynamic spectra behind the time-domain and
continuum checks of \S\ref{sec:technosearch}, which are held on the
processing host rather than in the manuscript source bundle; and (x) the
second-epoch search products behind the CP$-$72~2713 retirement
(\S\ref{sec:technosearch}), the four
\texttt{A002\_Xff0235\_X502d\_spw\{0..3\}} result, search and source-spectrum
files, together with \texttt{cp72\_recurrence.json} and the script that
derives it. Data products carry the
Creative Commons Attribution 4.0 International licence (CC~BY~4.0), and
the pipeline code the MIT licence; neither author's employer asserts any
intellectual-property claim over the released code. Raw ALMA visibility
data are public from the ALMA Science Archive at
\url{https://almascience.org}.""",
    r"""The complete release will also be deposited on Zenodo, with a DOI minted
on final acceptance and inserted here. It carries the per-window search
products for all \NWindows{} windows, which is to say the spectral
extracts, per-drift-trial peak statistics, archive UID, epoch-propagated
coordinates and field centre, primary-beam gain, channel frequencies and
widths, the drift grid, and the target statistic with all \NCtrl{} control
statistics, from which every rank and $p$-value here is recomputable. It
carries the line-exclusion mask in both its frozen and repaired forms, the
serendipitous molecular-line catalogue, the closure-phase and
population-anomaly outputs, and the execution-block metadata,
integration-time audit and availability census of \S\ref{sec:sample} with
its per-star pointing ledger.

It carries the validation material in full: all \NTrials{} injection trials
and \NDwellTrials{} dwell trials, the second-stage local-null code with its
per-window outputs and retained null-draw arrays, and the frozen pipeline
code and input-data snapshot with its change-log. The second-epoch products
behind the CP$-$72~2713 retirement are included, as are the retained
per-integration dynamic spectra behind the time-domain and continuum
checks. The pre-registration of the promote and retire criteria is part of
the tagged repository snapshot, so the commit hash and timestamp quoted in
\S\ref{sec:technosearch} are publicly verifiable, and the Zenodo deposit
covers them.

Data products carry the Creative Commons Attribution 4.0 International
licence (CC~BY~4.0) and the pipeline code the MIT licence. Neither author's
employer asserts any intellectual-property claim over the released code.
Raw ALMA visibility data are public from the ALMA Science Archive at
\url{https://almascience.org}.""")

# -------------------------------------------------------------------- D4
sub(r"""No execution block is analysed in both papers: the pilot's 100-star
search products are superseded here, not re-used, and every
window here was re-reduced and re-searched from the raw archive data
with the pipeline of \S\ref{sec:method}. Where a star is treated in
both, the numbers to cite are this paper's frozen products, and any
discrepancy resolves in their favour.""",
    r"""No execution block is analysed in both papers. Every window here was
re-reduced and re-searched from the raw archive data with the pipeline of
\S\ref{sec:method}, so where a star is treated in both, the numbers to cite
are this paper's frozen products.""")

fz.apply(TEX, E)

s = open(TEX, encoding='utf-8').read()
s = re.sub(r'\s*@@PARA@@\s*', '\n\n', s)
open(TEX, 'w', encoding='utf-8').write(s)
