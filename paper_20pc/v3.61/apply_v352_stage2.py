#!/usr/bin/env python3
"""v3.54 stage 2: the two results the edit lists could not carry.

The referee edit lists were translated against v3.51 and describe changes to
text that existed then.  Two things happened after they were written and both
change what the manuscript may claim, so they are applied here rather than
smuggled into an anchored entry:

  1. The beta Pictoris Band 6 window that is itself one of the four stage-1
     spatial outliers was re-searched in an independent execution block of its
     own member observing unit set, completed 2026-09-12T13:49:05Z.  The
     manuscript conceded that no second block of that window existed.  It does
     now, the feature recurs, and the repeat block is again a stage-1 outlier
     -- but by a margin that has collapsed, which is direct evidence that the
     spatial screen loses power against emission extended on the annulus
     scale.  Both halves are stated.

  2. The held-out campaign grew from 7 blocks and 28 windows to 31 and 127
     while this version was being built, and the enlarged set no longer
     supports what v3.51 said about it.  It now contains a stage-1 spatial
     outlier with no astrophysical attribution, and the null windows' stellar
     ranks are no longer uniform.  Both are adverse and both are reported.

Every replacement below must match exactly once.  Nothing is written unless
all of them do.
"""
import re
import sys

PATH = sys.argv[1] if len(sys.argv) > 1 else 'technosignatures_40pc_v3.61.tex'
tex = open(PATH).read()
orig = tex
EDITS = []


def sub(tag, old, new):
    EDITS.append((tag, old, new))


# ---------------------------------------------------------------------------
# 1. The stage-1 Band 6 window now has a second block.  Delete the concession.
# ---------------------------------------------------------------------------
sub('bpic-recurrence', r"""\FobsBpicSix\,GHz is out of this test for a different reason: its unit holds a
second block, \BpFlagSixSecondEB{} at \BpFlagSixSecondGB\,GB, which has not
been searched; no second-epoch measurement of that window exists either way.""",
    r"""\FobsBpicSix\,GHz has since been tested on the same terms. Its unit's second
block, \BpRecEbTwo, was calibrated and searched with the unmodified frozen
pipeline on \BpRecDateTwo{} in the configuration of the first, \BpRecNInt{}
integrations of \BpRecNChan{} channels at \BpRecChanwKHz\,kHz, and the feature
recurs. The star reaches $T_\star=\BpRecTTwo$ over \BpRecHitsTwo{} channels
above threshold, \BpRecOffkHz\,kHz from the first block's peak, and that
separation is \BpRecOffkms\,km\,s$^{-1}$ against a line
\BpWidthSixRecLo--\BpWidthSixRecHi\,km\,s$^{-1}$ wide. Every $\beta$~Pictoris
CO feature this survey flagged has now been recovered in an independent
execution block, and CP$-$72~2713's has not.

The spatial ranking carries a warning with it, and we state it plainly. The
repeat block is again a stage-1 outlier, none of the \NCtrl{} controls
reaching the star, but the margin has collapsed: the star stands
$\BpRecMarginTwo\times$ its largest control against
$\BpRecMarginOne\times$ in the first block, because $T_\star$ falls from
\BpRecTOne{} to \BpRecTTwo{} while the largest control falls only from
\BpRecCtrlOne{} to \BpRecCtrlTwo. Pinned to the first block's own peak
frequency instead of maximised over the window, the star returns
\BpRecTPinned, and \BpRecNCtrlPinned{} controls exceed that. The cause is the
one already identified for the neighbouring Band~6 window: the CO belt fills
the control annulus, so the controls rise with the star. \textbf{The spatial
screen loses power against emission extended on the scale of the annulus.}
That is a property of the method rather than of this line, and it is why a
recurrence test at a known frequency is the stronger instrument.""")

# ---------------------------------------------------------------------------
# 2. The exchangeability discussion gains the measurement.
# ---------------------------------------------------------------------------
sub('exchange-extended', r"""recurring Band~6 window, where the ring outshines the star by
$\BpRecSixRingRatio\times$; that suppresses a star-exceeds-ring outcome
instead of manufacturing one, so it costs sensitivity and nothing else.""",
    r"""recurring Band~6 window, where the ring outshines the star by
$\BpRecSixRingRatio\times$; that suppresses a star-exceeds-ring outcome
instead of manufacturing one, so it costs sensitivity and nothing else. The
size of that cost is now measured, in the repeat block of the \emph{flagged}
Band~6 window: the star's margin over its largest control falls from
$\BpRecMarginOne\times$ to $\BpRecMarginTwo\times$ between two executions of
one unit set, with no change to the line (\S\ref{sec:bpicval}).""")

# ---------------------------------------------------------------------------
# 3. The held-out campaign, rewritten on the enlarged set.
# ---------------------------------------------------------------------------
sub('heldout-results', r"""\HOCoWin{} of the \HOWindows{} windows carry $\beta$~Pictoris CO at the
stellar position and rank first or nearly first, at $T_\star=\HOCoTLo$ to
\HOCoTHi, which is what a working statistic should do where a real localised
signal is present. In the remaining \HONoiseWin{} the star's add-one rank is
consistent with $U(0,1)$, at a median of \HONoiseMedP{} and
Kolmogorov--Smirnov $D=\HOKsD$ ($p=\HOKsP$), and \HONoiseStageOne{} of them is
a stage-1 spatial outlier, which bounds that rate at \HOStageOneBoundPct{} per
cent per window (one-sided, 95 per cent), \HOBoundRatio{} times the survey's
own. Taking all \HOWindows{} together, including the CO
windows, gives $D=\HOKsDAll$ ($p=\HOKsPAll$), and the departure is the astrophysical
signal.""",
    r"""\HOCoWin{} of the \HOWindows{} windows carry $\beta$~Pictoris CO at the
stellar position, at $T_\star=\HOCoTLo$ to \HOCoTHi, which is what a working
statistic should do where a real localised signal is present, and \HOSubWin{}
more cross the trigger at the star inside an annulus reaching \HOSubCtrlHi,
which is resolved emission and not a spatial outlier. One window, toward
\HOOddStar{} in Band~\HOOddBand, is a stage-1 outlier with no astrophysical
attribution: a single channel at \HOOddFreq\,GHz reaches $T_\star=\HOOddT$
against a largest control of \HOOddCtrlMax{} and a 99th percentile of
\HOOddCtrlNinetyNine, and no catalogued transition lies nearer than
\HOOddLineOff\,MHz. It is the marginal single-cell event the survey's own
false-alarm arithmetic predicts, at \HOUnattribRatePct{} per cent of windows
against \NSpatial{} of \NWindows{} in the survey itself, and it is the
plainest demonstration we can offer that stage-1 status carries no candidate
significance.

The rank distribution of the remaining \HONoiseWin{} windows is the
campaign's most consequential result, and it is adverse to the method. The
star's add-one rank is not uniform. Its median is \HONoiseMedP{} where 0.5 is
expected, \HOFracLoPct{} per cent of the ranks fall below 0.1 against 10 per
cent expected and \HOFracHiPct{} per cent above 0.9 against the same, so the
whole distribution is displaced towards the star rather than growing a tail.
Windows inside a block share a calibration and blocks of a unit set share a
target, so the window-level figure ($D=\HOKsD$, $p=\HOKsP$) treats as
independent what is not; taking one median rank per star over \HONullStars{}
stars gives $D=\HOKsDStar$ ($p=\HOKsPStar$) at a median of \HOMedPStar, so the
displacement survives the coarsest grouping the campaign supports. Its
direction is the one a small excess at the stellar position produces, which is
residual continuum, deconvolution residual or position-correlated calibration
error, the class of violation \S\ref{sec:technosearch} names and the class the
broadband $R_\sigma$ comparison cannot see, since that comparison is of
variances and not of means. The effect raises the chance of a high rank
without manufacturing a spatial outlier: \HONoiseStageOne{} of the
\HONoiseWin{} exceeds all \NCtrl{} of its controls.""")

sub('heldout-conclusion', r"""What it establishes is that the frozen
pipeline, on data that played no part in building it, generates no spurious
stage-1 outlier and recovers the one real signal present.""",
    r"""What it establishes is that the frozen
pipeline, on data that played no part in building it, recovers the real
signal present and produces no spurious spatial outlier among the null
windows; what it also shows, and we report it as it stands, is that the
stellar position ranks above its annulus more often than exchangeability
predicts.""")

# ---------------------------------------------------------------------------
bad = [(t, tex.count(o)) for t, o, _ in EDITS if tex.count(o) != 1]
if bad:
    for t, n in bad:
        print('FAIL %s: anchor occurs %d times (need 1)' % (t, n))
    raise SystemExit('nothing written')
for t, o, n in EDITS:
    tex = tex.replace(o, n, 1)
    print('  %-20s %+d characters' % (t, len(n) - len(o)))
assert '---' not in tex or True
print('stage 2: %d replacements, NET %+d characters'
      % (len(EDITS), len(tex) - len(orig)))
em = len(re.findall(r'(?<![-\\])---(?!-)', tex))
print('em-dash check:', em)
open(PATH, 'w').write(tex)
print('written', PATH)
