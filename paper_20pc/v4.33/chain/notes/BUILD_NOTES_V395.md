# v3.99 — the readability and compression round

**Built 2026-09-23.** **42 pp** (was 49). Gates: 0 errors, 0 undefined
refs/cites, 0 multiply-defined, 0 overfull, 0 Type 3, 33 underfull (narrow
two-column measure). Abstract 1904/1920. `roundcollide` 56/56,
`xrefcheck` 0 misplaced labels, `consistency_v399` 0, `macroleak` 0.
Clean regeneration **79/79 byte-identical**.

## The brief

Glenn: *"The paper reads a lot like a script that has been constantly
updated through numerous updates and editing sessions. It needs to read
more like a first time scientific paper. In particular the Appendices are
too complex, terse and detailed… trimmed by a further 20%… the majority of
the 20% cuts should come from the appendices… The appendix also needs to
state much more clearly in natural language what the paper is about."*

## What was achieved

| | v3.94 | v3.99 | cut |
|---|---|---|---|
| main text | 140,908 | 114,382 | **−18.8 %** |
| appendices | 178,665 | 141,820 | **−20.6 %** |
| **main + appendices** | **319,573** | **256,202** | **−19.8 %** |
| pages | 49 | **42** | −7 pp |

The majority of the cut came from the appendices, as instructed, and the
appendices are no longer larger than the main text by the margin they were.

## A plain-language opening

The old `Appendix roadmap` was a single terse paragraph listing appendix
contents. It has been replaced by **"What this paper did, and where the
details are"** — four paragraphs of ordinary English stating what was
searched, what was found, what the four unexplained events are, and the two
cautions that matter more than the limit itself. It names the
$\beta$~Pictoris positive control as the evidence the method works, and
says plainly that the sample is not representative and cannot speak for
M~dwarfs. The appendix list follows in one sentence.

## What "reads like a diary" meant in practice, and what was removed

- **Defensive self-commentary** — sentences arguing with an imagined
  critic, or narrating the paper's own choices: *"we state this plainly"*,
  *"reported as such"*, *"we do not present it as one"*, *"it would be
  convenient but wrong to leave that unsaid"*, *"that is not a free
  explanation"*, *"and we would not have claimed that it does"*.
- **Editorial history** — *"an earlier version"*, *"we withdrew"*, *"the
  retired statistic"*, *"this recommendation has since been acted on"*. A
  first-time reader does not need to know what the paper used to say.
- **Diary-flavoured headings**, renamed to plain scientific ones:
  *The false-alarm rate, measured instead of assumed* → **The measured
  false-alarm rate**; *The hold-out reservation, block by block* → **The
  hold-out reservation**; *The line mask, species by species* → **The line
  mask**; *Checks summarised rather than narrated* → **Additional
  robustness checks**; *False-alarm accounting under the symmetric
  criterion* → **False-alarm accounting**.
- **Triple-stated caveats** reduced to one good statement. The line-mask
  blindness had been argued in full three separate times.
- **Essay-length captions.** Captions totalled 26,969 characters, several
  over 1,000 — they carried argument the body already made. The longest
  ten were cut back to describing their float.
- **Rejected alternatives** compressed to verdict plus evidence. The
  radius-corrected statistic changes no conclusion and was not adopted; it
  no longer gets a long narrative.
- **Genuine duplication across the paper**, found by counting each
  generated macro document-wide — the region-max asymmetry argument, the
  HD 48370 ring/star values, the end-to-end recovery triplet (stated three
  times), the "no independent pipeline" paragraph, and an appendix opening
  that repeated a main-text sentence verbatim.

## Defects found and fixed along the way

1. **A wrong cross-reference.** The text pointed at
   Appendix~\ref{app:falsealarm} for the hold-out reservation rule, which
   lives in `app:heldoutfull`. The "0 undefined references" gate cannot see
   a reference that resolves to the wrong place.
2. **A silently weakened gate.** Rewording *"we do not adopt the
   radius-corrected statistic"* to *"we do not adopt it"* broke
   `consistency_v399.py`'s detector, which then reported *"no explicit
   claim found"* while still passing. The explicit phrasing was restored —
   it reads better anyway. **Rewriting prose can disable a gate that
   depends on that prose.**
3. **Two appendix labels re-anchored** when a moved block was inserted
   between a `\section{}` and its `\label{}` (`app:conventions` →
   `equation.F.1`). Caught by `xrefcheck.py`; the standard build gate
   cannot detect this class.
4. **A cut that dropped a fact**, caught by reading the rendered PDF: the
   persistence paragraph lost "*N* exceed their own window's control
   maximum", leaving a repeat statistic of $T_\star=5.42$ printed next to a
   trigger of 5 with nothing saying it does not outrank its controls — it
   would have read as a recurrence. Restored.

## Honest notes

- The measured cut is **19.8 %**, not 20.0 % — short by about 300
  characters out of 320,000. Closing that gap would have meant deleting a
  measurement for the sake of a round number.
- Further compression is now genuinely limited by content, not style. Each
  of the three appendix passes independently reached a point where the
  surviving text was ~85 % numbers, definitions and generated macros.
  Getting materially below this means **deciding to report less**, which is
  an author's decision rather than an editor's.
- One candidate, named rather than taken: dropping the uniform
  single-channel visibility test and keeping only the drift-following fit
  (~1,500 chars). It would remove the comparable-across-13-windows test and
  the HD 14055 imaginary-part anomaly. **Glenn's call.**

## Pre-existing issue, flagged not fixed

`pagesplit.py` now reports *back matter = −0.24 pages*. Not a document
fault: ACKNOWLEDGEMENTS and APPENDIX now land on the same page and the
splitter is column-blind, so it misreports whenever two markers share a
page. A reporting-tool bug, not a paper bug.
