# Publishing the data deposit on Zenodo — the author's one page

Everything is prepared; reserving and publishing the DOI is the only step that
needs the author's Zenodo account. Five steps, in this order.

**1. Reserve the DOI.** Log in at <https://zenodo.org>, choose *New upload*,
and under *Digital Object Identifier* answer "No" to "Do you already have a
DOI?" and press **Get a DOI now!**. Zenodo shows the reserved DOI, of the form
`10.5281/zenodo.NNNNNNN`. Leave the draft open (do not publish yet).

**2. Write it into the one place it lives.** In
the manuscript `chain/technosignatures_40pc_v*.tex`, just above the deposit's entry in the reference list,
change the single line

    \newcommand{\SIdoi}{10.5281/zenodo.0000000}

to the reserved DOI. Nothing else is edited: the article's reference
(White & Dey 2026) and the deposit's own README both read `\SIdoi`.

**3. Rebuild and pack.** From the version directory:

    bash make_all.sh && bash gate.sh
    python3 chain/zenodo_pack.py --spectra <path>/ALMA_Technosignatures_40pc_crossing_spectra.zip --out zenodo_upload

The spectra file is `/data/astra-pa-archive/r29_spectra/` on the cluster unless
the crossing set changed, in which case `zenodo_pack.py` says so and the file is
regenerated first (`fold29/gen/spectra/code/spectra_run.sh`). `zenodo_pack.py`
refuses to pack if the DOI is still the placeholder or if the two files do not
belong together. `python3 chain/doigate.py --submission` must then pass.

**4. Upload.** In the open Zenodo draft, upload the two zip files from
`zenodo_upload/` and fill the form from `zenodo_upload/zenodo_metadata.json`:
title, both creators with affiliations, description, keywords, licence
(CC BY 4.0), resource type *Dataset*. When the article has an arXiv identifier
or a journal DOI, add it under *Related works* as "is supplement to" (this can
also be added after publication without a new version).

**5. Publish.** Press *Publish*. That mints the DOI reserved in step 1. Check
that `https://doi.org/<DOI>` resolves, and that the SHA-256 Zenodo shows for each
file equals `zenodo_upload/SHA256SUMS`.

A referee or reader then rebuilds the article's statistics from the record with

    unzip ALMA_Technosignatures_40pc.zip
    cd ALMA_Technosignatures_40pc/code
    python3 reproduce.py

(Python 3 with numpy and scipy; exit status 0 when every quantity agrees with
the article.)
