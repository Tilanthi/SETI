# Author actions outstanding for the v3.68 submission

These are the authors' to settle; no referee and no assistant can close them.
They were carried as `%` comments inside the manuscript until v3.49; last
regenerated for v3.51 and reviewed against the manuscript at v3.60.  arXiv
distributes the LaTeX source, so the comments were public; they are recorded
here verbatim and removed from the `.tex` (R2-E4).  **Removing the comments
does not answer the questions.**

## A1. Affiliation 3 and the competing-interest statement (referee R2-m1)

Attached to: `\altaffiltext{3}{VBRL Holdings Inc.}`

```
% TODO (AUTHOR INPUT, referee R2-m1): complete the VBRL Holdings Inc.
% affiliation (city, country) and add an Acknowledgements/competing-interest
% statement disclosing Robin Dey's employment relationship to VBRL and whether
% VBRL funded or otherwise supported this work. Cannot be authored by the
% assistant -- awaiting the authors' wording.
```

## A2. The execution-block overlap with White (2026)

Attached to: `Sec. 2, the paragraph on the pilot's superseded products`

```
% TODO (AUTHOR INPUT, for the editor's cross-check request): confirm the
% EB-by-EB overlap between this paper and White (2026) -- which execution
% blocks appear in both, and whether any number printed here is also
```

## A6. The CRediT role split (referee R1-8) — ~~OPEN~~ **MOOT at v3.57**

The author-contributions section was deleted at v3.57 on the authors'
instruction, so there is no role split to confirm unless it is reinstated.
The original item is kept below for the record.

Attached to: `Sec. Author contributions (CRediT)`

```
% TODO (AUTHOR INPUT, referee R1-8): adjust the role split to the actual
% contributions; the skeleton below reflects the paper's own structure
% (pipeline and analysis vs.\ programme leadership) and needs author
% confirmation before submission.
```

## A7. The submission git tag (NOTE: the block still names submitted-v3.32 in a v3.51 manuscript, so the tag name itself needs the authors decision)

Attached to: `Sec. Data Availability`

```
% TODO (AUTHOR ACTION, at submission): create the git tag
% `submitted-v3.32` on the SETI repository commit that corresponds to the
% submitted-analysis snapshot (the pipeline state that produced every number
% in this paper) before the manuscript is submitted -- the Data Availability
% statement names that tag as the snapshot identifier, and the short
% commit hash it resolves to should be pasted into the sentence naming
% the tag.
```

## Status of the prose these comments annotate

Reviewed at v3.61: A1, A2 and A7 are still open; A6 is moot (see above).

**NEW at v3.61 (referee 2, M9).** A \section*{Funding and competing interests}
now exists in the manuscript, because AAS/OJA policy requires one and the referee
asked for it. Its wording was written by the assistant and asserts three things no
analysis can verify:

* that the study used no dedicated funding;
* that the authors declare no competing financial or personal interests;
* that VBRL Holdings Inc. had no role in the design, analysis or decision to publish.

**Glenn and Robin must confirm or correct that paragraph before submission.**

**Added at v3.62 (referee 2, major 9).** The referee asks for a one-clause
description of what VBRL Holdings Inc.\ does, so that a company affiliation on a SETI
paper is not left unexplained. No analysis can supply this; please add a clause to
\altaffiltext{3}.

**Added at v3.62 (referee 1, point 16).** The Data Availability section now states
that the version of record is the Zenodo deposit rather than a GitHub branch, and
that the repository tag resolving to the publication commit is named in the deposit.
Two author actions follow: mint the DOI at acceptance and insert it, and create the
tag on the commit that produced the released products. If any
of it is wrong, the sentence to change is in the back matter immediately before
"About this paper". This supersedes nothing in A1, which still asks for the VBRL
city and country in the affiliation.
The Data Availability prose is tag-agnostic, so only the tag itself is
outstanding. The manuscript text they sit beside is drafted and builds; it is
the factual content that needs author confirmation.  In particular
`\altaffiltext{3}{VBRL Holdings Inc.}` has no city or country, the
competing-interest statement asserts two facts about VBRL that only the
authors can confirm, the CRediT split is inferred from the structure of
the paper, the White (2026) arXiv identifier is not yet known, the
submission git tag is not yet made (the Data Availability prose is
tag-agnostic, so only the tag itself is outstanding), and the sentence
"No execution block is analysed in both papers" is an assertion that has
not been verified EB by EB against the White (2026) manuscript.


---

# Added at v3.63

## A8. Page budget — CLOSED at v3.67

The paper is **29 pages**, down from 32. The authors' instruction to remove the
analysis-history material freed three pages, so the budget question no longer
arises and the 32-page acceptance recorded at v3.66 is moot.

## A9. The commitment to request a new ALMA epoch of CP-72 2713

Two referees have now asked for this, the second wanting the ALMA cycle named.
The manuscript says we intend to request a third epoch; **the authors must
confirm they will, and say in which cycle**, or the sentence must be softened
to state only that a third epoch is what would settle it.

## A9a. Original wording (referee 2, M3)

Section 5.3 now says in print: "Resolving the remaining ambiguity needs a third
epoch, and we intend to request one: a single Band 7 execution reproducing the
tuning would separate an intermittent emitter from a noise excursion." Referee
2 asked for exactly this statement. **It is a commitment the authors must be
willing to make.** If they are not, the sentence must be reworded to say only
that a third epoch is what would settle it.

## A10. Zenodo concept DOI for the review process (referee 2, minor 12)

The text says the DOI is "minted on acceptance". Referee 2 asks for a
placeholder concept DOI or a private/embargoed link to the frozen commit, so
that referees can check the numerical claims stated to be reproducible only
from the deposit. Author action: reserve a Zenodo concept DOI now.

## A11. Affiliation ordering and corresponding author (referee 2, minor 13)

Check RAL Space and VBRL Holdings Inc. ordering and formatting against OJA
style, and mark the corresponding author, which the manuscript currently does
not do. Related to A1.
