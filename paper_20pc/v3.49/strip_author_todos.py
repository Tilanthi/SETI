#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""R2-E4: take the author TODO comment blocks out of the arXiv source.

arXiv distributes the LaTeX source, so a `%`-comment is public.  v3.48 shipped
six author-facing blocks, one of which reads "Cannot be authored by the
assistant -- awaiting the authors' wording" and another of which names the git
tag `submitted-v3.32` in a v3.48 paper.

The QUESTIONS are not closed by this script and must not be: they are the
authors'.  Each block is copied verbatim into AUTHOR_ACTIONS.md, with the
manuscript line it was attached to, before it is deleted.  Comment removal
changes no rendered character; the PDF is compared before and after.

Kept: the build note at l.11 (class template suppression) and the `%%`
provenance banners on the generated table fragments.  Neither is addressed to
the authors and neither is embarrassing in public source.
"""
import io, re, sys

TEX = 'technosignatures_20pc_v3.49.tex'
OUT = 'AUTHOR_ACTIONS.md'

# (id, heading, anchor text of the block, the manuscript line it attaches to)
BLOCKS = [
    ('A1', 'Affiliation 3 and the competing-interest statement (referee R2-m1)',
     "% TODO (AUTHOR INPUT, referee R2-m1): complete the VBRL Holdings Inc.\n"
     "% affiliation (city, country) and add an Acknowledgements/competing-interest\n"
     "% statement disclosing Robin Dey's employment relationship to VBRL and whether\n"
     "% VBRL funded or otherwise supported this work. Cannot be authored by the\n"
     "% assistant -- awaiting the authors' wording.\n",
     "\\altaffiltext{3}{VBRL Holdings Inc.}"),
    ('A2', 'The execution-block overlap with White (2026)',
     "% TODO (AUTHOR INPUT, for the editor's cross-check request): confirm the\n"
     "% EB-by-EB overlap between this paper and White (2026) -- which execution\n"
     "% blocks appear in both, and whether any number printed here is also\n"
     "% printed there. Draft statement below; verify against the White (2026)\n"
     "% manuscript before submission and complete the bracketed clause.\n",
     "No execution block is analysed in both papers: ... (Sec. 1)"),
    ('A3', 'The deliberate exception, if any, to that statement',
     "% AUTHOR: confirm the single deliberate exception, if any -- e.g.\\ shared\n"
     "% calibrator-only usage -- and state it here; otherwise delete this\n"
     "% bracket and the sentence stands as the complete answer.\n",
     "(same paragraph)"),
    ('A4', 'The two factual clauses of the competing-interest statement (R2-m2)',
     "% AUTHOR ACTION (referee R2-m2): confirm the two factual clauses above\n"
     "% -- VBRL's absence of stake and of funding -- and complete the VBRL\n"
     "% affiliation with city and country. Reword if either is inaccurate.\n",
     "Sec. Competing interests"),
    ('A5', 'The White (2026) arXiv identifier (R2-m3)',
     "% AUTHOR ACTION (referee R2-m3): supply the arXiv identifier for\n"
     "% White (2026) so referees can assess methodological continuity, and\n"
     "% flag the dependency to the handling editor.\n",
     "Sec. Competing interests / bibliography entry White (2026)"),
    ('A6', 'The CRediT role split (referee R1-8)',
     "% TODO (AUTHOR INPUT, referee R1-8): adjust the role split to the actual\n"
     "% contributions; the skeleton below reflects the paper's own structure\n"
     "% (pipeline and analysis vs.\\ programme leadership) and needs author\n"
     "% confirmation before submission.\n",
     "Sec. Author contributions (CRediT)"),
    ('A7', 'The submission git tag',
     "% TODO (AUTHOR ACTION, at submission): create the git tag\n"
     "% `submitted-v3.32` on the SETI repository commit that corresponds to the\n"
     "% submitted-analysis snapshot (the pipeline state that produced every number\n"
     "% in this paper) before the manuscript is submitted -- the Data Availability\n"
     "% statement names that tag as the snapshot identifier, and the short\n"
     "% commit hash it resolves to should be pasted into the sentence naming\n"
     "% the tag.\n",
     "Sec. Data Availability"),
]

src = io.open(TEX, encoding='utf-8').read()
orig = len(src)
bad = 0
for tag, _, block, _ in BLOCKS:
    n = src.count(block)
    if n != 1:
        print('!! %-3s block occurs %d times' % (tag, n))
        bad += 1
if bad:
    print('NOTHING WRITTEN'); sys.exit(1)

md = ["# Author actions outstanding for the v3.49 submission",
      "",
      "These are the authors' to settle; no referee and no assistant can close them.",
      "They were carried as `%` comments inside the manuscript until v3.49.  arXiv",
      "distributes the LaTeX source, so the comments were public; they are recorded",
      "here verbatim and removed from the `.tex` (R2-E4).  **Removing the comments",
      "does not answer the questions.**", ""]
for tag, head, block, where in BLOCKS:
    md += ['## %s. %s' % (tag, head), '', 'Attached to: `%s`' % where, '',
           '```', block.rstrip('\n'), '```', '']
    src = src.replace(block, '')
md += ['## Status of the prose these comments annotate', '',
       'The manuscript text they sit beside is drafted and builds; it is the',
       'factual content that needs author confirmation.  In particular',
       '`\\altaffiltext{3}{VBRL Holdings Inc.}` has no city or country, the',
       'competing-interest statement asserts two facts about VBRL that only the',
       'authors can confirm, the CRediT split is inferred from the structure of',
       'the paper, the White (2026) arXiv identifier is not yet known, the',
       'submission git tag is not yet made (the Data Availability prose is',
       'tag-agnostic, so only the tag itself is outstanding), and the sentence',
       '"No execution block is analysed in both papers" is an assertion that has',
       'not been verified EB by EB against the White (2026) manuscript.', '']

io.open(OUT, 'w', encoding='utf-8').write('\n'.join(md))
io.open(TEX, 'w', encoding='utf-8').write(src)
print('%d comment blocks moved to %s | source %d -> %d (%+d chars, 0 rendered)'
      % (len(BLOCKS), OUT, orig, len(src), len(src) - orig))
