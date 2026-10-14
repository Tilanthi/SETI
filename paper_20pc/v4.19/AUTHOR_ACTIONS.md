# Author actions before submission

**There are no identifier blockers left.** The Data Availability statement no
longer waits on anything (item 1), and the reference list carries no
placeholder. What remains below is decisions only the authors can make.

## Settled, recorded here so it cannot be reopened by accident

1. ~~**Zenodo DOI, and a reviewer link.**~~ **DECIDED BY THE AUTHOR, 2026-10-08.
   There will be no deposit, and the paper no longer offers one.** Verbatim:
   *"For the Zenodo deposit, remove all traces of this offer from the paper, I
   will not be doing it."* (G.J.W.) Independently confirmed the same day:
   Zenodo's API returns **0 records** for either author and 0 for the title, so
   the statement had been promising something that did not exist.
   - **63 traces in 10 files were removed**, including the whole deposit
     inventory, the "reference of record" sentence, and every "the data
     release holds…", "is deposited for every…", "the released catalogue"
     pointer in §3, §4, §5 and Appendices A–E.
   - **What the statement says now**: every observation is public in the ALMA
     Science Archive and is retrieved by the execution-block identifier the
     crossing ledger prints; the ancillary catalogues (Gaia DR3, the NASA
     Exoplanet Archive, CDMS/JPL through Splatalogue) are public; the derived
     results are the tables in the paper; **and no separate data deposit
     accompanies the paper.** The two pre-registration commits are named, and
     both were checked to resolve publicly on 2026-10-08.
   - **`doigate.py` is INVERTED and is now an invariant, not a countdown.** It
     used to fail until a DOI appeared; it now fails if any unfulfilled
     promise of a deposit reappears in the published text, or if the honest
     content that replaced it is deleted. `python3 doigate.py` passes;
     `python3 doigate.py --selftest` exercises 20 cases, 14 of which must
     fail — the seven real sentences the paper used to carry among them.
     It should be added to `gate.sh` (queued to the integrator), because it is
     now cheap and always true rather than a blocker that would be switched
     off.
   - ★ **Referee 2's minor 14 required us to insert the DOI. We are declining
     a referee requirement on the author's instruction.** The response letter
     must say so plainly rather than let the item look overlooked.
2. ~~**Submission git tag.**~~ **CLOSED 2026-10-08 with item 1.** It existed so
   that "the commit that produced the deposited products" would resolve. That
   sentence is gone. The two commits the paper *does* name are pre-registration
   identifiers, they are already exact, and both were verified to resolve.
3. ~~**White (2026).**~~ **CLOSED 2026-10-08, nothing to decide.** There is no
   `White2026` entry in the reference list and no citation of it anywhere
   outside the frozen `snapshots/`: round 370 deleted the `\bibitem`, and this
   item went on asking the authors to choose between citing and deleting a
   reference that no longer exists. `citegate` now sweeps the reference layer
   in both directions on every gate run, so an entry listed and uncited cannot
   survive a build and this item cannot come back as a decision. If the pilot
   paper is to be cited after all, that is a **new** decision: add the
   `\bibitem` with an arXiv identifier rather than `MNRAS, submitted`, and
   cite it beside the external flux-scale check.

## Blockers

3a. **Two hold-out windows carry an impossible noise.**
   `holdout_export_v381.json`, block `A002_Xbbdc51_X2cb6` toward
   HD 92945: two windows record rms = 4.1 × 10⁻⁴ mJy on 48.4 s of on-source
   time where their own companions in the same block, at the same channel
   width, record 0.28–0.35 mJy on 3320 s. Scaling a companion by √(3320/48.4)
   predicts 2.35 mJy, so the two rows are wrong by a factor of about 5800,
   and because the limit follows the noise they carry the two deepest EIRP
   limits in the hold-out, 1.8 × 10¹² W against 1.2 × 10¹⁵ for their siblings.
   The census minimum over all 1,651 windows is 0.082 mJy, which these are
   200 times below.
   ★ **Nothing printed in the paper rests on them**, and that is measured
   rather than assumed: no hold-out EIRP macro is cited anywhere in the
   manuscript, and `calib_r15.py` screens the two rows out by a within-block
   consistency test on rms·√t (its clause D9, driven both ways) and records
   them in `calib_r15.json` under `noise_rejected`. **With item 1 settled this
   is no longer a publication blocker** — no reader inherits the file — but it
   is still a defect in the working catalogue, and any statistic recomputed
   over the hold-out must use the screen. Correct the two rows at source.
   Found by `r15-calib` while measuring something else.

## Decisions for the authors

4. **ALMA project codes — now a real decision, not a pointer.** The
   Acknowledgements used to name the `NProjCodes` proposals by saying their
   codes were "recorded block by block in the data release". With item 1
   settled that sentence had to go, and it now simply thanks the proposals'
   teams. **The codes are therefore nowhere in the paper.** ALMA's data policy
   and several journals expect them in the text. `tab_projcodes_v400.tex` is
   already generated and is not `\input` anywhere; a compact comma-separated
   paragraph of 65 codes costs roughly a tenth of a page. **Recommendation:
   print them**, either as that paragraph in the Acknowledgements or as the
   existing table in Appendix A. Needs a numbers-owner macro and a float
   decision, so it is queued rather than done.
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

- ~~Put them in the Zenodo deposit and list their SHA-256 in its README.~~
  **CLOSED 2026-10-08 by item 1: there is no deposit, so that route is gone.**
  The only remaining way to give the statistic and the mask a resolvable
  identifier is to **push them to the public repository and name the commit**,
  exactly as the hold-out rule already is. That is an author decision about
  what to make public, not a writing task, and nothing in the paper claims it
  in the meantime.
- **Do not** invent a commit hash for either. This project has never written
  an identifier it could not resolve and must not start.

**The dated timeline table is deliberately not in the paper.** It would need
a verifiable date for each fixed choice *and* for each data set being
searched. Today only two rows of four have one, and a four-row table in
which half the dates read "not independently timestamped" is worse than no
table — it advertises the gap it was meant to close. If you want it, the
cheapest route now is to put the two missing files in the public repository
and give, per choice, the commit and the date it entered it
(`git log --follow --format='%H %cI' -- <path>`). ★ Note that the **search
dates** the other half of the table needs are no longer available to a reader
either: they were carried per block in the catalogue, and the paper gives only
the first and last primary-census block dates in §Acknowledgements.

**11. Reference list: ten entries are listed and cited nowhere.** Measured
both ways over the manuscript, all section files and all table fragments —
0 citations without an entry, 10 entries without a citation. Six have an
obvious home and four probably do not; none of this is in a file `r10-prose`
owns, so each is queued to its owner in `INTEGRATION_QUEUE.md` (entry P5).
The one *addition* a referee asked for is **Sheikh et al. (2019, ApJ, 884,
14), "Choosing a maximum drift rate in a SETI search"**, which is the
standard reference for the drift ceiling of §4 and is conspicuous by its
absence.

## 2026-10-06: the Data Availability statement, and what the front matter now claims

**12. SUPERSEDED 2026-10-08 by item 1: there is no Zenodo DOI and there will not be one.** What
this item said — keep the sentence "a single permanent Zenodo deposit, cited by its DOI" word for
word so that inserting the DOI stays a one-string edit — is exactly the sentence that has now been
deleted, and `doigate.py` has been inverted so that it fails if that sentence ever returns. The
rest of this item still stands, and matters more than it did: the pre-registration claims no
longer rest on a deposit at all, because three of the four carry an identifier that resolves
without one.

★ What *did* change is that the statement no longer rests on the DOI alone. Referee 2 objected
that the pre-registration claims are unverifiable without it, and three of them now carry an
identifier that resolves on its own:

| choice | identifier | verified |
|---|---|---|
| calibration hold-out rule + pre-registered block list | commit `c75069040eab52ec1336376a4dae62114bb281a3`, 2026-09-14T07:10:24Z | ✔ unchanged, as item 10 |
| the molecular-line list, and the ordering of its SO entry against the CP−72 2713 crossing | the crossing's own commit `f5f52e7804f1baad99515ea2d46ddd7e4e4cd546`, **2026-09-11T19:23:34Z**, plus the line list's query date | ✔ **new**; fetched from the GitHub API and read, not quoted from another agent's report. That commit's `per_target_results_v3.42.csv` carries `A002_Xff0235_X4a6d` at 344.269746 GHz with `crossing=True` and a disposition, and its `v342_calc.py` holds 17 transitions, none of them SO. |
| frozen search statistic (Eq. 1) | **still none** | ✘ as item 10. The statement used to say the statistic and the line list were deposited *as files in their own right*; **that sentence is deleted**, so nothing in the paper is now false about them, and nothing claims them either. |

**So item 10's table is now three rows of four, not two.** If you want the dated timeline it
describes, only the search statistic is missing an identifier.

**13. Item 3 (White 2026) is closed.** It is cited in §1, where the paper says that few searches
at any frequency reprocess existing interferometric archives, which is its natural home. The
reference still reads `MNRAS, submitted`: **replace that with the arXiv identifier before
submission**, or the citation points at nothing a reader can fetch.

**14. Item 11 (the reference list) is measured and reduced to one decision for you.** Nine
entries were listed and cited nowhere; 0 citations lacked an entry. Two are now cited
(`White2026`, `Sheikh2021`), one is queued to the owner of §5.3.3 (`AstudilloDefru2017`, the
host-activity sentence), and **six have no home left in the paper because the appendix or the
discussion paragraph that cited them was deleted in the length pass**: `Blomme2023`,
`Burton2024`, `GentileFusillo2021`, `PollutedWD2026`, `BpicbRadio2026`, `Starlink2024`. The
recommendation is to delete those six `\bibitem`s; the alternative is to cite each where it is
genuinely used, which is better but costs words. Exact list and reasoning in
`referee_r11/queue/QUEUE_prose.md` entry 4.

**15. Six references are being ADDED and none of them existed in the list**: the ALMA Technical
Handbook, the NASA Exoplanet Archive, Splatalogue, the ITU Radio Regulations, and the CloudSat
and EarthCARE radar papers — all five things Referee 2 says the paper uses and does not cite.
Full `\bibitem` text in `QUEUE_prose.md` entry 3. **Two of them are already cited from
§Acknowledgements, so that entry and the Acknowledgements must land in the same build.**

## 2026-10-07: the reference list after the §1 edit

**16. Item 3 is closed the other way, and item 13 above is now STALE.** Item 13 closed item 3 on
the grounds that `White2026` "is cited in §1". That citation no longer exists: the §1 sentence
about few searches reprocessing interferometric archives was replaced, and the only
`\citep{White2026}` in the paper went with it. A sweep of the manuscript, all 154 input files and
all table fragments finds **0 citations of it**, so the `\bibitem` has been removed — which is the
second of the two options item 3 itself offers, not a tidying-up. Consequences you should see:
- **The paper now cites its own companion paper nowhere.** If you want it cited, the external
  flux-scale check in §4 is its natural home (it is the only place the pilot's measurements are
  actually used), and the entry must come back *with an arXiv identifier*: `MNRAS, submitted` was
  never a reference a reader or a referee could fetch, which is why it was the one entry no audit
  has ever been able to verify.
- Nothing else in the paper depended on it. The claim it supported is gone, not unsourced.

**17. The reference list is 45 entries, 45 of them cited, and every journal entry has now been
confirmed in ADS's own index** by year, journal, volume, first page and first-author initial —
an index independent of the Crossref/OpenAlex checks used previously. Remaining caveats for you,
none of them blocking:
- `Morrison2023` (PASA 40, e019): the e-number is confirmed from Crossref's own
  `article-number` field and from Cambridge Core, but ADS serves no link for PASA e-numbered
  articles, so that one entry rests on publisher metadata alone.
- `ITU2024`: itu.int refuses automated requests; the 2024 edition was verified in the previous
  audit and was not re-reached this round.
- `BRaTs2026` is still `MNRAS, in press` with no DOI (arXiv comment: "MNRAS submitted and
  accepted"), and `SETIreview2025` is still a preprint (last revised 2026-10-02). Both should be
  re-checked at proof stage in case they acquire volume and page.
