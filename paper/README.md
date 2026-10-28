# Current manuscript

This folder holds the latest build of the paper and its supplementary archive.

| file | what it is |
|---|---|
| `technosignatures_40pc_v4.28.pdf` | the compiled manuscript, 25 pages |
| `ALMA_Technosignatures_40pc.zip` | the machine-readable supplement and data archive, intended for deposit with a DOI |

Both are byte-identical to the copies in `paper_20pc/v4.28/`, which is the authoritative build
directory (its build lives in `paper_20pc/v4.28/chain/`).

**v4.28 is a working checkpoint, not the submitted version.** It states two calibration defects
that are not yet fixed (ALMA's pipeline and online flags were not applied to the searched data, and
the flux-scaling step was not run on four legacy-script blocks), with their measured effect. The
next version recalibrates every block behind a printed limit or crossing.
