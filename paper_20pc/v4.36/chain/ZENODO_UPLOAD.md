# Publishing the data deposit on Zenodo — the author's one page

**Author ruling, 2026-11-09: the Zenodo DOI is added after acceptance.** Until then
no DOI string is printed anywhere: the article cites the record as *White & Dey (2026),
Zenodo (DOI to be added on acceptance)*, its Data Availability statement says the DOI
"will be added on acceptance", the deposit's README cites it in the same words and the
Zenodo metadata record carries no DOI. `doigate.py` (D4/D5) fails the build if a
placeholder or any Zenodo DOI the author has not supplied appears in the manuscript, the
PDF, the deposit, the metadata or these notes.

Everything is prepared; uploading and publishing the record needs the author's
Zenodo account. Five steps.

**1. Rebuild and pack.** From the version directory:

    bash make_all.sh && bash gate.sh
    python3 chain/zenodo_pack.py --spectra <path>/ALMA_Technosignatures_40pc_crossing_spectra.zip --out zenodo_upload

The spectra file is `/data/astra-pa-archive/r29_spectra/` on the cluster unless
the crossing set changed, in which case `zenodo_pack.py` says so and the file is
regenerated first (`fold29/gen/spectra/code/spectra_run.sh`). `zenodo_pack.py`
refuses to pack if the two files do not belong together, or if a DOI string has been
written into the metadata or the deposit README before the record exists.

**2. Upload.** At <https://zenodo.org> choose *New upload*, answer "No" to "Do you
already have a DOI?" (Zenodo assigns one), upload the two zip files from
`zenodo_upload/` and fill the form from `zenodo_upload/zenodo_metadata.json`:
title, both creators with affiliations, description, keywords, licence
(CC BY 4.0), resource type *Dataset*. When the article has an arXiv identifier
or a journal DOI, add it under *Related works* as "is supplement to" (this can
also be added after publication without a new version).

**3. Publish** (when the author decides; at the latest on acceptance). Press *Publish*.
Check that `https://doi.org/<DOI>` resolves, and that the SHA-256 Zenodo shows for each
file equals `zenodo_upload/SHA256SUMS`.

**4. On acceptance, write the DOI into the article.** Three edits, made together:
the `\bibitem[White \& Dey(2026)]{SIdeposit}` entry of the manuscript (replace
"(DOI to be added on acceptance)" by the DOI), the Data Availability sentence in
`sections/08_backmatter.tex` ("whose DOI will be added on acceptance"), and the
deposit README's citation (`zdeposit.py`, `DOI_NOTE`). Then restate `doigate.py`
to the supplied DOI: add it to `ALLOWED_ZENODO` (owner `SIdeposit`) and replace D5's
"added on acceptance" requirement by "the supplied DOI is cited". The gate is written so
that this restatement is required: until it is made, the minted DOI fails D4.

**5. Rebuild and check.** `bash make_all.sh && bash gate.sh`; `python3 chain/doigate.py`
must pass.

A referee or reader then rebuilds the article's statistics from the record with

    unzip ALMA_Technosignatures_40pc.zip
    cd ALMA_Technosignatures_40pc/code
    python3 reproduce.py

(Python 3 with numpy and scipy; exit status 0 when every quantity agrees with
the article.)
