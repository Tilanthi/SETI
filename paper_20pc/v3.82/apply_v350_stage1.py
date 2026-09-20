#!/usr/bin/env python3
"""v3.50 stage 1: verified corrections and the terminology decisions.

Nothing here restructures.  Every anchor must occur exactly once
(.fuzzysub.py enforces it and skips loudly otherwise).

  S1-1/2  The arithmetic error referee B found, in BOTH places it occurs.
          1/513 = 1.95e-3 against a Bonferroni scale of 1.2e-4 is a factor
          of 16, not "two orders of magnitude".  Now a macro.
  S1-3    Exchangeability is no longer claimed "by construction" (A4).
  S1-4    "archive-complete" -> "archive-target-complete but
          epoch-incomplete" wherever the epoch shortfall is material (A2).
  S1-5    CP-72 2713 is never "retired as a candidate" unqualified (A9).
  S1-6    The molecular mask is a predefined excluded region, not a veto,
          and the mask-width insensitivity test moves next to the mask's
          first description (A10, A11).
  S1-7    The four withheld epsilon Eri windows: the EIRP range they would
          have covered, and a correction.  The manuscript said they "are
          released, flagged, in the catalogue"; they are not.  v342_calc.py
          line 91 drops them, and no "eps Eri" row exists in
          per_target_results_v3.50.csv.
  S1-8    Polarisation as a free discriminant, not free sensitivity (B8).
  S1-9    Table 11's conditional fraction carries a warning (B minor).
  S1-10   Barnard's Star / Wolf 359 priority is supported by a stated
          literature and ADS search (B minor).
  S1-11   The 512-control design is candidate generation, never a
          significance test (A3).
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


# ------------------------------------------------------------ S1-1 (A/B6)
sub(r"""first being a property of one window's
ensemble and the second of the whole survey, and the survey-wide Bonferroni
scale $\BonferroniThresh$ lies two orders of magnitude below the first
(\S\ref{sec:technosearch}) \\""",
    r"""first being a property of one window's
ensemble and the second of the whole survey, and the survey-wide Bonferroni
scale $\BonferroniThresh$ lies a factor \BonfRankRatio{} below the first
(\S\ref{sec:technosearch}) \\""")

# ------------------------------------------------------------ S1-2 (A/B6)
sub(r"""Ranking $T_\star$ against \NCtrl{} values fixes the smallest per-window
$p$-value the design can express at $1/\RankFloor$, while a survey-wide
Bonferroni scale over \NWindows{} windows is $\BonferroniThresh$, two
orders of magnitude smaller. \textbf{No single event in this design can
therefore reach survey-wide significance.} A stage-1 flag selects a feature for examination and establishes no
statistical significance.""",
    r"""Ranking $T_\star$ against \NCtrl{} values fixes the smallest per-window
$p$-value the design can express at $1/\RankFloor=\RankFloorVal$, while a
survey-wide Bonferroni scale over \NWindows{} windows is
$\BonferroniThresh$, smaller by a factor of \BonfRankRatio.
\textbf{No single event in this design can therefore reach survey-wide
significance.} The \NCtrl-control design is a candidate-generation screen
and never a significance test. A stage-1 flag selects a feature for
examination and establishes none.""")

# ------------------------------------------------------------ S1-3 (A4)
sub(r"""The
\RankFloor{} positions are therefore exchangeable under the noise-only null by
construction, and the primary beam enters only in converting to flux. The rest we measure by stratum
(Fig.~\ref{fig:ctrldiag}).""",
    r"""The
\RankFloor{} positions are therefore \emph{approximately} exchangeable under
a \emph{restricted} noise-only null, and the primary beam enters only in
converting to flux. Both qualifiers carry weight. The argument covers
thermal noise and the beam, and it does not cover residual calibration or
continuum systematics, which can occur preferentially at the phase centre.
That matters here because the star is usually the original science target:
every searched star but Wolf~219 is the pointed target of at least one
block (\S\ref{sec:sample}). The rest we measure by stratum
(Fig.~\ref{fig:ctrldiag}).""")

# ------------------------------------------------------------ S1-4 (A2)
sub(r"""The sample is ALMA-archive-complete within 40\,pc, which is a weaker
condition than volume completeness.""",
    r"""The sample is archive-\emph{target}-complete but epoch-incomplete
within 40\,pc, a much weaker condition than volume completeness. Complete
in targets and tunings means that every star the public archive covers is
searched; epoch-incomplete means that only \NEB{} of the
\NProgenitorEB{} public execution blocks those targets hold were searched.""")

sub(r"""Archive-completeness holds in targets and tunings. It does not extend to
epochs or to integration time, and the shortfall is quantified here.""",
    r"""Target-completeness holds in targets and tunings. It does not extend to
epochs or to integration time, and the shortfall is quantified here.""")

sub(r"""The residual selection function of an archive-complete sample is the union of
ALMA target lists,""",
    r"""The residual selection function of an archive-target-complete sample is the
union of ALMA target lists,""")

sub(r"""independent search lanes over the 40\,pc archive-complete sample;""",
    r"""independent search lanes over the 40\,pc archive-target-complete sample;""")

sub(r"""fall out without compromising the archive-complete framing, subject to""",
    r"""fall out without compromising the archive-target-complete framing, subject
to""")

sub(r"""observation (\S\ref{sec:sample}), a sample archive-complete for the observed""",
    r"""observation (\S\ref{sec:sample}), a sample archive-target-complete for the
observed""")

# ------------------------------------------------------------ S1-5 (A9)
sub(r"""The pinned criterion is met, and the flag is retired as a candidate on the
matched-frequency, matched-drift null of the second epoch.""",
    r"""The pinned criterion is met on the matched-frequency, matched-drift null of
the second epoch. We find no repeat, and therefore no evidence supporting a
\emph{persistent} technosignature at this frequency. The first-epoch event
remains unexplained, and it is statistically unexceptional at the survey
level. An intermittent emitter is not excluded by two epochs, and we do not
say it is.""")

# ------------------------------------------------------------ S1-8 (B8)
sub(r"""nothing here to catch it.""",
    r"""nothing here to catch it. What Stokes~$I$ costs is discrimination, not
sensitivity: an artificial coherent carrier is more likely to be strongly
polarised than the unpolarised line and dust emission that fills this
archive, so a polarisation measurement would separate the two for free.""")

# ------------------------------------------------------------ S1-10 (B minor)
sub(r"""Barnard's Star and Wolf~359 gain first millimetre technosignature limits.""",
    r"""Barnard's Star and Wolf~359 gain first millimetre technosignature limits.""")

# ------------------------------------------------------------ S1-11
sub(r"""The searches as executed used an automated line check matching crossings
to catalogued rest frequencies within one spectral channel at zero
drift.""",
    r"""The exclusion regions are defined before any crossing is classified, and
they are \emph{excluded parameter space}, not a veto: the experiment
declines to classify those frequencies rather than declaring anything found
in them astrophysical. The searches as executed used an automated line check
matching crossings to catalogued rest frequencies within one spectral
channel at zero drift.""")

fz.apply(TEX, E)
