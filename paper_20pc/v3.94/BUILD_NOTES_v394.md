# BUILD NOTES — v3.94: prose, disclosure and independent verifiability

Two referee reports, worked in order.

## Gates

| gate | value |
|---|---|
| pages | 48 (main 24, appendices 24) |
| errors / undefined / multiply-defined / overfull / Type 3 | 0 / 0 / 0 / 0 / 0 |
| macros defined / unused | 1109 / 0 |
| abstract | 1918 characters (limit 1920) |
| clean regeneration | **98/98 byte-identical** |
| number audit | 49 / 0 |
| consistency / macro-leak / round-ownership / cross-reference | 0 / 0 / 0 / 0 |

## The artifact Referee 2 found was mine, and it is now gated

`\textbf{We` rendered as literal `extbfWe` on p. 29. The cause was my own
v3.92 bold-stripping script, which wrote its replacement through a path
that interpreted backslash escapes, so `\t` became a TAB. LaTeX compiled
without error because `extbf` is just a word, and nothing in `gate.sh`
could see it.

New `macroleak.py` checks the source for control characters followed by
letters and for bare `extbf`/`extit`/`mph` fragments, and checks the
extracted PDF text for macro names that should never survive typesetting.
It is now in `gate.sh`.

## Required changes, in order

* **R2-1 (highest priority)** — 14 free-standing sentence-fragment
  "headers" in the main text folded into ordinary topic sentences, and
  three more rewritten. Enumerated list items were left alone, being
  genuine enumerations. Manuscript self-commentary removed: no more
  "an earlier version of this paper", "we have since", or "will be
  reported separately".
* **R2-3** — the post-hoc widening of the line mask is now disclosed in
  bold *where the mask is introduced*, together with the resolution: a
  ±13 km/s Keplerian-only tolerance, which could have been pre-registered,
  suppresses and releases exactly the same windows. Both now appear in the
  same place.
* **R2-4** — §5.2 opens by stating that two non-exchangeable conventions
  are carried, which is primary and why (pre-registration, not statistical
  superiority), and that the conclusion is identical either way.
* **R2-2** — the "no independent validation" limitation is now a named
  Discussion subsection, and the release carries **known-answer test
  vectors** generated from first principles with no import from the search
  or injection code, so a third party can check the pipeline against
  arithmetic rather than against our tooling.
* **R2-5 / R1-5** — Figure 7a now carries a shaded band combining the
  ×0.48–1.35 transfer bracket with the one-sided +20 per cent
  decorrelation term. It is asymmetric by construction, because the
  decorrelation bias can only make the quoted power optimistic.
* **R1-7** — Figure 7b is rebuilt as the temporal selection function:
  systems by longest epoch separation, with the 40 systems for which
  independent confirmation was never possible marked off explicitly.
* **R1-4** — one convention, stated once: "sensitivity" means
  $P_{90}^{\rm sel}$ unless another quantity is named.
* Minors: ALMA expanded at first use; the headline finding front-loaded in
  the abstract; non-kinematic transmitter drift acknowledged as unmodelled;
  CP−72 2713's role as a worked example stated at first mention.

## Trap

`make_fig_classa_sens.py` gained reads of the transfer bracket, the
decorrelation term and `epochsplit_v394.json`, but ran before two of them
existed — the **fifth** forward dependency in this project's history, and
the fifth caught only by the clean-regeneration test (27/98 on the first
attempt). The pattern is consistent: adding an input to an existing
generator is exactly as dangerous as adding a new generator.
