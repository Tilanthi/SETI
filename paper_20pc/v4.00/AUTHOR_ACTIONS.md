# Author actions before submission — v3.86

Three of these are hard blockers: the paper cannot be submitted with a
placeholder identifier in the Data Availability statement or the reference
list. The rest are decisions only the authors can make.

## Blockers

1. **Zenodo DOI.** §Data Availability refers to "the Zenodo deposit" and to
   its minted date, but no DOI is given. Mint the deposit and insert the DOI.
   Until then the reproducibility argument has no address.
2. **Submission git tag.** The same statement says the deposit "carries the
   exact commit that produced every number" and that "the repository tag
   resolving to that commit is named in the deposit". Create the tag at the
   submitted commit and name it.
3. **White (2026) identifier.** Cited in §1 as the pilot for this work and
   listed as `MNRAS, submitted`. Replace with the arXiv identifier or the
   accepted reference. If it is still unpublished at submission, say so
   explicitly in the citation rather than leaving "submitted".

## Decisions for the authors

4. **ALMA project codes.** The Acknowledgements give the generic
   `JAO.ALMA#XXXX.X.NNNNN.S` form and point at the machine-readable release
   for the actual codes. Some journals require the codes in the text; check
   the target journal's policy.
5. **Funding.** There is no funding acknowledgement. Add one or confirm that
   none is required.
6. **The VBRL affiliation, and the three new statements written around it.**
   A referee has asked directly what "VBRL Holdings, 50/5 Huay Kaew Road,
   Chang Phueak, Chiang Mai, Thailand" is, noting that it is not a
   recognisable academic or observatory affiliation and that a SETI null
   result attracts disproportionate attention. v3.86 therefore adds three
   sections — Author contributions, Funding, Competing interests — and each
   contains a `%% AUTHORS:` comment marking what you must confirm:
   - the division of work between G.J.W. and R.D. as I have described it;
   - that no grant supported the work;
   - that VBRL Holdings had no role in design, targets, analysis, the
     decision to publish, or the content. **I have written the competing-
     interests statement to be accurate only if that is true. If the company
     had any role, the wording must change before submission.**
   Consider also adding one clause to the affiliation itself identifying what
   the organisation is, which is what the referee actually asked for and
   which only you can supply.
7. **Author contributions.** No CRediT statement is present. Add one if the
   target journal requires it.

## Judgement calls the review flagged and did not settle

8. **The Class A chance expectation.** Over all searched windows the four
   unattributed events match expectation; over the drift-resolving class they
   are a $\sim2\sigma$ excess. The paper reports both and does not choose.
   The authors may prefer to lead with one.
9. **Page length.** 41 pages in the two-column style. If the target journal
   has a limit, the cheapest reductions are the four appendix tables that
   duplicate main-text content, not the evidence.

## v4.00 item: two execution blocks have no recoverable ALMA project code
`A002_X11d9ce7_X5257` and `A002_Xbf792a_X26ec` appear in the frozen catalogue but
carry no member OUS in the harvested archive metadata, and the ALMA TAP service
returned HTTP 400 for direct `asdm_uid` queries. The Acknowledgements currently
names them as unrepresented in the project-code list. Before submission these
two codes should be looked up by hand in the ALMA Science Archive web interface
and added to `projcodes_mous_v400.json`, after which the generator will fold them
in automatically and `\NProjCodeUnres` will fall to zero.
