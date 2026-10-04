# Virtual referee round 1 — on v3.63 (32 pp)

Three independent reads. Every numbered point below was checked against the
manuscript source, the released catalogue or the frozen products; nothing is
asserted from memory.

---

## Referee A — statistics and internal consistency

**A1. The primary-beam response floor you just adopted excludes nothing, and as
written it looks fitted to the data.** §4.3 says a window is retained only where
the response is ≥ 0.5 and then says all 443 released windows satisfy it. A rule
that excludes zero objects is not a rule; a reader will assume it was drawn
around the data after the fact. *This is repairable and the repair strengthens
you*: I checked `pboffsets_v361.json` against the catalogue. The retained
windows stop at 0.46 θ_PB (×1.81); the four withheld ε Eri windows start at
0.618 θ_PB (×2.88) and run to 0.667 (×3.43). **The floor sits inside an empty
gap between ×1.81 and ×2.88.** Say that, with both numbers, and the rule becomes
a statement about where the data actually divide rather than a boundary drawn to
touch nothing.

**A2. Four load-bearing numbers in §4.2 are hand-typed with no generator.** The
local-to-global scale ratios "0.97 (CP−72 2713), 1.29 (HD 48370), 0.93 (β Pic
B3) and 1.02 (β Pic B6)" and "the continuum lane detecting 17 of 57
target/bands" appear as literals. This is precisely the failure class the paper
itself documents twice (the `OVERCOUNT = 4.0` constant, the 88.2 GHz literal,
the ×1000.13 correction). Either generate them or state in the text that they
are quoted from a named product and cannot be regenerated from the release.

**A3. The TRAPPIST-1 b inclination average is misleading for TRAPPIST-1.** You
now give 5–29 per cent of orbital phase edge-on and 0.3–10 per cent "averaged
over isotropic inclination". TRAPPIST-1 is a transiting system: its inclination
is known and is within a fraction of a degree of edge-on. Quoting an isotropic
average for a system whose inclination is measured invites exactly the
misreading you were trying to prevent. Give the edge-on figure, say the system
is transiting and therefore edge-on, and drop the isotropic number or move it to
a parenthesis about *unknown* systems.

**A4. "12 per cent" beside "13.3 GHz" of a 113.86 GHz union does not divide.**
13.264/113.855 = 11.6 per cent. Rounding to a whole number here is a false
economy: a reader who checks the arithmetic gets 11.6 and wonders which number
is wrong. Print one decimal.

**A5. The ×3.2 worst case in the abstract mixes two conventions.** The abstract
says the worst case "debits a nominal 5σ trigger by ×3.2", built from the median
response correction ×2.29 and the polarisation factor ×1.41. But ×2.29 is a
*median* and the paper's own worst-case compounded response-plus-smearing
penalty is ×4.6. Either call ×3.2 the *typical* combined debit (median response
× polarisation), or build a genuine worst case. As written the word "worst" is
doing work the arithmetic does not support.

**A6. Equation (1) is never cross-referenced.** `eq:etadrift`, `eq:drift`,
`eq:gain` and `eq:conditioning` are all numbered and never cited by number.
Either reference them where they are used or unnumber them.

---

## Referee B — instrument and archive

**B1. The expected rank-first counts in the new Table 14 are quoted under an
assumption the paper has spent two sections dismantling.** "Expected" is
$N_{\rm win}/513$ — the exchangeable rate. §5.4 establishes that the tail is
anti-conservative by ×1.4. The table should either quote both (exchangeable and
measured) or say in the caption that the expectation is the exchangeable one and
is therefore a lower bound. Right now the 12-m stratum's 3 observed against 0.59
expected looks like a 3σ excess when on the measured rate it is not.

**B2. The array assignment for the two Band 9/10 blocks is a string
heuristic.** You determine 12-m versus 7-m by counting `CM` substrings in
`antenna_arrays`. That is almost certainly right — ALMA's 7-m antennas carry CM
identifiers and Bands 9 and 10 are not offered on the ACA — but it is a string
match on a free-text column, and the paper should say what the test was rather
than assert the answer.

**B3. The solar-system check is incomplete as an argument.** Zero *known* minor
planets is not zero minor planets. The strong form of the argument is available
to you free: an unknown solar-system body has non-sidereal motion, and your two
blocks are 2 h apart at the same phase centre, so a moving body would not be at
the same position (nor at the same topocentric frequency) in both. Say that. It
converts "nothing catalogued was there" into "nothing that moves could have done
this".

**B4. The Software section now cites CASA, astropy, numpy and scipy, but the
analysis in this version also uses astroquery** (ALMA TAP for the Band 9/10
array determination, IMCCE SkyBoT for the minor-planet search). Cite it or
remove the dependency from the narrative.

**B5. §4.3 quotes the ε Eri exclusion as "beyond the first sidelobe
transition".** With the response floor now adopted, the sidelobe argument and
the floor are two different justifications for the same exclusion. Lead with the
floor; keep the sidelobe physics as the reason the floor is set where it is.

---

## Referee C — presentation, and whether the paper says one thing

**C1. You have half-renamed Class A.** §4.1 now says Class A is "the
fine-channel spectral-carrier search" and that "'drift-resolved' is used of the
class only where the two agree". But "drift-resolved" survives as a synonym for
Class A in nine places, including Table 1's glossary ("Class A/B — drift-resolved
/ unresolved-excess windows"), the Figure 1 legend, §5.1, §6.1, and — worst —
the new opening sentence of the Conclusions, "Within the 126 drift-resolving
windows". Either finish the rename or withdraw the §4.1 statement. At present
the paper contradicts itself within one page.

**C2. The abstract's new opening is vaguer than the number you have.** "The
subset of a larger archive-covered set that carries usable spectral data" —
you know that number: 88 of 115 genuinely covered stars, drawn from a 168-entry
candidate list. Give it.

**C3. Three names for one object.** "Spatial-control screen", "spatial screen",
"the control ensemble" and "the screen" are all used for the same construction.
Pick one and define it once.

**C4. The compressed §4.4 now opens with a sentence about itself** ("Everything
in this subsection is validation and robustness testing rather than candidate
generation"). That is the right signal for referee 1's restructuring request,
but it reads as scaffolding. Fold it into the first substantive sentence.

**C5. The page count is 32 and the last page holds bibliography only.** As
editor I would not accept "accept 32 pages" as the resolution while page 32 is
one-third full. Close it.

**C6. Appendix I now forwards to §6.2 for recurrence coverage, and §6.2 forwards
to Appendix I for the conditioning framework.** Circular cross-references are
tolerable but check that the reader is not sent back and forth for one number.
