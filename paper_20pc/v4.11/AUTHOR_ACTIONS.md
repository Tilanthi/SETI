# Author actions before submission

Three of these are hard blockers: the paper cannot be submitted with a
placeholder identifier in the Data Availability statement or the reference
list. The rest are decisions only the authors can make.

## Blockers

1. **Zenodo DOI, and a reviewer link.** The Data Availability statement now
   has the shape the journal version needs and is missing exactly one string:
   the DOI. Three steps, in this order.
   1. Upload the deposit to Zenodo and **reserve the DOI** (Zenodo issues one
      before publication, under *Reserve DOI* in the record's DOI field).
   2. Insert it into the first sentence of §Data Availability, so that the
      sentence reads "...a single permanent Zenodo deposit, **DOI
      10.5281/zenodo.NNNNNNN**, which carries every number...". Then run
      **`python3 doigate.py`**: it fails while no DOI is present, fails on a
      placeholder spelling (`XXXX`, `NNNN`, `TBD`, all zeros), and fails if
      the deposit inventory in that paragraph has been lost. It is not in
      `make_all.sh` on purpose — it would block every build and be switched
      off — so it has to be run by hand before submission.
   3. Create a **private reviewer link** for the record (*Share → Create
      link*, access "restricted") and give it in the cover letter. The
      manuscript does not promise one, because it may not claim something
      that does not yet exist; the cover letter is the right place anyway.
      A DOI minted at acceptance cannot be checked during review, which is
      the whole of the objection.
2. **Submission git tag.** §Data Availability says the deposit carries "the
   commit that produced the deposited products". Create an annotated tag at
   the submitted commit, name it in the deposit's README, and check the tag
   resolves in a fresh clone.
3. **White (2026).** This reference is **no longer cited anywhere in the
   text** (see the citation sweep in item 11), while still appearing in the
   reference list as `MNRAS, submitted`. Decide one of two things: cite it
   where it belongs — it is the pilot for this work, and §1 or the external
   flux-scale check in §4 is its natural home — and replace "submitted" with
   the arXiv identifier; or delete the `\bibitem`. Do not leave it listed and
   uncited.

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

## v4.01 item: our own campaigns destroyed retained survey products (2026-09-25)

**The release contains fewer per-window spectra than the paper has been assuming,
and the shortfall was caused by this project's own follow-up campaigns, not by
the archive.**

`visfit_campaign_r6.py` ends each execution block with

```python
    for p in (tdir, home):
        shutil.rmtree(p, ignore_errors=True)
```

where `tdir` is the block's directory under `/data/SETI/targets/`. For any block
the original survey had already searched, that directory also holds the block's
retained `*_srcspec.npz`, `*_search.npz` and `*_result.json`. The round-6
visibility campaign fetched 36 blocks on the morning of 2026-09-25 and removed
36 such directories; the round-7 refit inherited the same line and removed a
further five before it was caught and fixed.

Evidence, two independent lines (`referee_r7/SRCSPEC_ATTRITION.md`):

- The phase-centre audit read srcspec at ~14:12 on 2026-09-25, between the two
  campaigns. Of the **31** crossings round 6 had fitted, **9** still had a
  readable srcspec; of the **13** crossings round 6 never touched, **13** did.
- A file-level inventory of 1,036 srcspec paths taken on **2026-09-13** shows
  **1,016 still present and 20 gone** — 16 on blocks both campaigns fetched,
  4 on blocks only round 7 fetched, **0 on blocks neither touched**.

**Numbers.** The figure of **3,022** retained `*_srcspec.npz`, recorded
2026-09-24, predates the round-6 campaign and was never a stable baseline. The
host-wide count is now **2,889**.

**Author actions.**

1. Any statement in the Data Availability section, or anywhere else, about what
   the release contains per window must be written against the products that
   actually exist at release time, counted at that time — not against 3,022.
2. Decide whether the destroyed products are to be regenerated. They are
   recoverable only by re-fetching and re-extracting those blocks; nothing else
   is lost, because the catalogue, the frozen export and every downstream number
   were derived before the deletions.
3. Referee 2's M6 panel A is **not** blocked: of the three stars it names,
   61 Vir survives through its other execution block `A002_Xc067f7_X822`, and
   CP-72 2713 and beta Pic both survive.
4. The bug is fixed in `visfit_campaign_r7.py::reclaim_dir()` and in
   `r7_janitor.py`, both of which remove only `raw/`, `work/` and measurement
   sets and never a target directory. **`visfit_campaign_r6.py` still carries
   it**; do not re-run that script as it stands.

## ★★★★ 2026-09-26 — URGENT, GLENN'S OWN AU MIC LETTER MAY CARRY THE PARALLAX DEFICIT

Six AU Microscopii Band 3 blocks in this survey's catalogue are **ALMA 2024.1.01095.S**
(confirmed live on the ALMA TAP service) — the programme behind Glenn's submitted MNRAS letter
*"Impulsive millimetre flares from the planet-host M dwarf AU Microscopii at 106 GHz"*.

`PARALLAX_LOSS.md` predicts a **retained amplitude of 0.69–0.74** for those blocks, because the
extraction phase-rotates to the star's **barycentric** position and omits the annual parallax.
If the letter's photometry used a **fixed-position visibility average** — which is what
"per-scan parallel-hand Re⟨XX⟩" describes — then its **29.4 and 10.9 mJy flare peaks and its
0.294 ± 0.017 mJy quiescent flux are low by 26–45 per cent**, and the radiated energies scale
with them. **Imaging or `uvmodelfit` is immune**, because both solve for or integrate over
position.

**One question settles it**: how were those flux densities measured — CASA imaging /
`uvmodelfit`, or a phase-rotated visibility average at an assumed fixed position (and if the
latter, was the assumed position barycentric or apparent)?

If it is the latter, we hold the products and the repaired routine
(`referee_r8/parallax/star_lm_apparent.py`, 10 checks, 4 demonstrated failing against the
shipped code) and can re-measure all twelve executions and hand back corrected light curves,
peaks, e-folding times and energies. **This is time-critical: the letter is under review.**

## 2026-10-04: the pre-registration identifiers, and the timeline table

**10. What is timestamped, what is not, and the one table that cannot yet be
printed.** A referee asked for "the deposit DOI or timestamped commit hash
for: the hold-out rule; the block list; the frozen statistic; the frozen
mask", and separately for a dated timeline showing when each analysis choice
was fixed relative to each data set being searched. Here is exactly how much
of that is recoverable today, checked against the repository rather than
remembered.

| choice | identifier | verified |
|---|---|---|
| calibration hold-out rule (`holdout_rule_v371.py`) | commit `c75069040eab52ec1336376a4dae62114bb281a3`, **2026-09-14T07:10:24Z**, message "PRE-REGISTER the calibration hold-out rule" | ✔ fetched from the GitHub API; the commit contains the rule, `holdout_assignment_v371.json` and the block list |
| pre-registered block list (`searched_ebs_v370.txt`, 398 execution blocks) | the **same** commit | ✔ same commit, 7941 bytes, sha256 `e9c0a1a4…` |
| frozen search statistic (Eq. 1) | **none** | ✘ the pipeline source is not in the public repository (`Tilanthi/SETI` holds `paper_20pc/`, `search/`, `targets/`, `results/`, `backups/` only) |
| frozen line mask (species list, rest frequencies, half-width) | **none** | ✘ same reason; `r9inputs/mask_r9.json` is a frozen *result* record and carries no timestamp |

Both identifiers are now in §Data Availability. For the other two:

- **Do this**: put the statistic module and the frozen rest-frequency list in
  the Zenodo deposit as files in their own right, and list their SHA-256 in
  the deposit README. Once the DOI exists it *is* the timestamped identifier
  for both, which is what the referee asked for; no manuscript change is
  needed beyond the DOI of item 1.
- **Do not** invent a commit hash for either. This project has never written
  an identifier it could not resolve and must not start.

**The dated timeline table is deliberately not in the paper.** It would need
a verifiable date for each fixed choice *and* for each data set being
searched. Today only two rows of four have one, and a four-row table in
which half the dates read "not independently timestamped" is worse than no
table — it advertises the gap it was meant to close. If you want it, the
cheapest route is: after the deposit exists, add a `PROVENANCE.md` to it
giving, per choice, the file, its SHA-256, and the date it entered the
repository (`git log --follow --format='%H %cI' -- <path>`), and cite that
file from §Data Availability in one sentence. The search dates themselves are
already in the release, per block.

**11. Reference list: ten entries are listed and cited nowhere.** Measured
both ways over the manuscript, all section files and all table fragments —
0 citations without an entry, 10 entries without a citation. Six have an
obvious home and four probably do not; none of this is in a file `r10-prose`
owns, so each is queued to its owner in `INTEGRATION_QUEUE.md` (entry P5).
The one *addition* a referee asked for is **Sheikh et al. (2019, ApJ, 884,
14), "Choosing a maximum drift rate in a SETI search"**, which is the
standard reference for the drift ceiling of §4 and is conspicuous by its
absence.
