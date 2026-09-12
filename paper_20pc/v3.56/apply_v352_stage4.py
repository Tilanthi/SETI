#!/usr/bin/env python3
"""v3.54 stage 4: close the page on widow lines, not on evidence.

`widows.py` lists every paragraph whose last line carries only a word or two.
Each of those costs a whole line of column, and a paragraph with a 7 per cent
last line needs only about five characters removed to lose it.  Twenty of them
are worth a third of a page, which is what this version is over by, and none
of the cuts below removes a number, a caveat or a citation: they remove
qualifying clauses that the same sentence or the next one already carries.

This is far the cheapest lever the page budget has, and it was not used in the
previous five cycles, which spent thousands of characters of real prose to buy
what a few hundred buys here.  Measured after: see BUILD_NOTES.

Two appendix figures also lose about a tenth of their width.  `fig:waterfall`
is deliberately untouched: two referees have asked for it to be enlarged.
"""
import sys

PATH = sys.argv[1] if len(sys.argv) > 1 else 'technosignatures_20pc_v3.56.tex'
tex = open(PATH).read()
orig = tex
E = []


def sub(tag, old, new):
    E.append((tag, old, new))


sub('p9-e2e',
    r"""at 1, 3 and 10 times the per-integration rms returns $T_\star = 20.5$,
$65.3$ and $217.7$, each recovered within one channel of the injection.""",
    r"""at 1, 3 and 10 times the per-integration rms returns $T_\star = 20.5$,
$65.3$ and $217.7$, each within one channel of the injection.""")

sub('p3-composition',
    r"""\S\ref{sec:bias} gives the figures and says what
they cost the result.""",
    r"""\S\ref{sec:bias} gives the figures and their cost.""")

sub('p8-channelwidth',
    r"""threshold, which is the commonest confusion when technosignature limits are
compared across surveys.""",
    r"""threshold, and the commonest confusion when limits are compared across
surveys.""")

sub('p15-neighbours',
    r"""$T_\star=\CpRecT$ stands $\CpRecNbrSig\sigma$ above the ten neighbouring
channels (mean \CpRecNbrMean, standard deviation \CpRecNbrSd), the noise-only""",
    r"""$T_\star=\CpRecT$ stands $\CpRecNbrSig\sigma$ above its ten neighbours
(mean \CpRecNbrMean, standard deviation \CpRecNbrSd), the noise-only""")

sub('p18-accel',
    r"""drift ceiling in its edge-on worst case, on star--planet relative
accelerations $GM_\star/r^{2}$ from NASA Exoplanet Archive parameters
maximised over orbital phase and inclination.""",
    r"""drift ceiling in its edge-on worst case, on accelerations
$GM_\star/r^{2}$ from NASA Exoplanet Archive parameters maximised over phase
and inclination.""")

sub('p9-benchmark',
    r"""\BenchEffRatio. Thresholds are also compared throughout to an Arecibo-like
planetary radar""",
    r"""\BenchEffRatio. Thresholds are also compared to an Arecibo-like planetary
radar""")

sub('p8-primarybeam',
    r"""What decides between a retained bounded
correction and a withheld window is whether the Gaussian beam form is
defensible at the offset in question, and the offset by itself does not decide
it.""",
    r"""What decides between a retained correction and a
withheld window is whether the Gaussian beam form is defensible at that
offset, not the offset itself.""")

sub('p12-heldout-open',
    r"""\HOWindows{} spectral windows in all, with the frozen
pipeline and with no change of any kind to statistic, mask, threshold or
candidate rules after the first of them was searched;""",
    r"""\HOWindows{} spectral windows in all, with the frozen
pipeline and no change of any kind to statistic, mask, threshold or candidate
rules after the first was searched;""")

sub('p13-heldout-rank',
    r"""Windows inside a block share a calibration and blocks of a unit set share a
target, so the window-level figure""",
    r"""Windows inside a block share a calibration and blocks of a unit set a
target, so the window-level figure""")

sub('p14-exchange',
    r"""Exchangeability is the central assumption of the statistic, and it can fail
through spatially varying noise, sidelobes, correlated pixels or calibration
residuals localised at the phase centre.""",
    r"""Exchangeability is the statistic's central assumption, and it can fail
through spatially varying noise, sidelobes, correlated pixels or calibration
residuals at the phase centre.""")

# ------------------------------------------------------- appendix float width
sub('fig-completeness',
    r'\includegraphics[width=0.48\columnwidth]{figures/completeness.pdf}',
    r'\includegraphics[width=0.42\columnwidth]{figures/completeness.pdf}')
sub('fig-accel',
    r'\includegraphics[width=0.40\columnwidth]{figures/drift_acceleration.pdf}',
    r'\includegraphics[width=0.35\columnwidth]{figures/drift_acceleration.pdf}')

bad = [(t, tex.count(o)) for t, o, _ in E if tex.count(o) != 1]
if bad:
    for t, n in bad:
        print('FAIL %s: %d occurrences' % (t, n))
    raise SystemExit('nothing written')
for t, o, n in E:
    tex = tex.replace(o, n, 1)
print('stage 4: %d edits, NET %+d characters' % (len(E), len(tex) - len(orig)))
open(PATH, 'w').write(tex)
print('written', PATH)
