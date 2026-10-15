# v4.19 — build notes

One self-contained PDF, **36 pp**, `technosignatures_40pc_v4.19.tex`, built with `pdflatex` three
times. ★★★★ **The class is `openjournal.cls` and the target journal is the Open Journal of
Astrophysics, with mandatory arXiv posting.** The journal is an **arXiv overlay**: the published
article *is* the arXiv PDF, so there is **no supporting information of any kind** and every appendix
is inside this one document. `SOURCE_DATE_EPOCH` is pinned in `make_all.sh` and `gate.sh`;
`FORCE_SOURCE_DATE` is **not** set and must not be — the preamble empties the class's own
`\submitted`/`\journalinfo`, so nothing dated is typeset at all.

★ The journal requirements were re-read from OJA's and arXiv's own pages on 2026-10-13 and are
recorded with every source URL in
[`referee_r18/OJA_ARXIV_FACTS_R18.md`](../../referee_r18/OJA_ARXIV_FACTS_R18.md). The class file in
this tree is **byte-identical to the one served from the journal's own download link**
(52,009 B, md5 `aa359396071034e4bd96379ff861deae`, "version September 6, 2015"), verified by
download the same day.

## Verification of this build (2026-10-14, after the eleven blocker fixes; all times `date -u`)

★★★★ **The numbers below replace the 2026-10-13 ones, which described a build two builds back.**
The round's own referee pass found **eleven blockers in the typeset PDF**, none of them a wrong
number and ten of them sentences; they are cleared in
[`referee_r18/BLOCKERS_REPORT_R18.md`](../../referee_r18/BLOCKERS_REPORT_R18.md), which records
each one, its fix, how it was verified, and the one strengthening that was deliberately declined.

| check | result |
|---|---|
| `make_all.sh` | **rc=0**, "generators OK", 19 min |
| `gate.sh`, run **three** times on this tree (and three more on the identical generator state before the last prose fix) | **ALL GATES PASS** every time; log md5 **`82e12e032e56390ec83720f65124aa8f`**, byte-identical |
| PDF | md5 **`e799fb287619b7a0a97172d5c7911530`**, 1,253,941 B — unchanged by every gate run and by the clean regeneration |
| `cleanregen.py` | **219/219 byte-identical**, both `make_all.sh` passes rc=0 |
| LaTeX log | 0 errors, 0 undefined control sequences, 0 unresolved refs/cites, 0 multiply defined, **0 overfull hbox, 0 overfull vbox**, 26 underfull |
| Type 3 fonts | **0** |
| pages | **36**; the APPENDIX divider is on p. 22, so **main 21 pp, appendices + references 15 pp**. `pagesplit`: main text 20.89 pp, back matter 0.32, appendices 12.66, bibliography 1.22 |
| `audit_numbers_v385.py` | **58 PASS / 0 FAIL**, 10 warnings (all long-standing and named) |
| `arxivset.sh` | **205 items = 190 tex + 1 cls (`openjournal.cls`) + 1 sty (`epsf.sty`) + 11 figures + 2 ancillary**; A1 190/190, A9 205 = 205, **A8 byte-identical**, 488 kB tarball, A13 PASS |
| `genai_sweep.py` | 10 hit lines over 23 families, every one ordinary English; `--drive` **23 of 23 families fire** |
| abstract | typeset **1665 characters / 259 words** (arXiv limit 1920, headroom 255; the journal sets no limit). `abswords` 259 against a house ceiling of 310. `absmeta`: the plain-ASCII block in `OJA_SUBMISSION.md` is **1669 characters / 260 words** and is the typeset paragraph transliterated **character for character** |
| `prosegate_selfref` | **PASS**, and drives 1–5 each **FAIL** on their own |
| `floatfit_r18` / `rotfit_r18` | **PASS**; 0 "float too large for page" warnings, 0 of 13 floats fail, landscape ledger inside the block on all four sides |
| `figgate_r17` | 11 figures, **scale 1**, floor 6.0 pt, 0 FAIL — and the 11 placed figure boxes are **unchanged to 0.01 pt**: no figure was resized by any of this round's fixes |
| `citegate` | **64 bibitems, 64 cited keys, 0 FAIL** (one entry added: the ALMA Knowledgebase article that states the bandpass figure) |
| page 1, **read out of the PDF** | title with its frequency range, both authors, all three affiliations, the e-mail `\thanks`, ABSTRACT and the key words — all present; and **no** class preprint slug, no `MNRAS` string anywhere in the PDF, no "supporting information" anywhere in the PDF |

## What changed in this build, journal-wise

The round was carried out against MNRAS and **reversed by the author on 2026-10-13**: the paper goes
to the arXiv and then to OJA. The MNRAS conversion is fully reverted — class, title block, running
heads, key words, the appendices before the bibliography, and the thirteen tools and gates the
conversion had repointed at `mnras.cls` geometry. **693.8/1388 pt, 245.26653/513.11743 pt,
675.83984 pt and the 6.5 pt table type floor were correct for this class all along**; they are
restored by reverting, not re-derived. `mnras.cls`, `mnras.bst`, `make_si.sh` and `si_labels.py` are
deleted from the tree.

The Supporting Information split is gone with it: **every appendix is inline**, and referee 2's
minor 11 is answered by **arXiv ancillary files** instead — `si_catalogue.txt` (1663 rows) and
`si_ledger.txt` (56 rows) are copied into `anc/` by `arxivset.sh`, checked by the new **A13**
(two-sided against the paper's own promise, no TeX in `anc/`, and not referenced by the build), and
described in Data availability through macros generated from the files' own headers.

Everything else this round produced is kept: the readability rewrite, the eight-item conclusions,
every referee-item patch, the driven self-reference gate, and the **247→259-word abstract** (three
statements restored, none of them for style: the words "union bandwidth" and the rank clause, each
required by a driven gate — `referee_r18/OJA_RESTORE_REPORT.md` §2c — and the scope qualifier "of
nearby stars" in the opening sentence, without which Sec. 2 and conclusion 1 of this same paper
falsify it).

## What the blocker pass changed in the text (2026-10-14)

Eleven sentences, one column separator and one bibliography entry; **no measurement moved, and no
figure was resized**. In order of weight:

1. **Conclusion 4 no longer puts the two tail crossings "in the archival extension"** — the macro in
   that slot has always been the *tail* count, and Sec. 5.6.2 measures the extension at zero
   unattributed crossings. `counts_r15.py` **A10** now fails the build if any sentence citing a tail
   macro says "extension", or any sentence citing an extension macro says "tail".
2. **Coincidence and attribution are told apart wherever both appear** — Sec. 5.4 prints 21 of 56
   coinciding and 18 of them attributed; conclusion 4, Fig. 4's flag note and Table A2 row 2.1 say
   which is which; Appendix C's "nearest a transition" sentence names the population its own
   generator measures. `counts_r15.py` **A11** and a nesting assertion in `make_fig_chain_v412.py`
   hold it.
3. **Sec. 5.6.1 no longer claims retuning is the difference between two counts that are both 40**;
   Table A2's confirmation rows each name the block set they are counted over.
4. **Figure 2's caption describes the one panel that prints** (the second was demoted to the online
   material at v4.12 and the caption was never touched); the colour key and the 24.1× sentence stay.
5. **Table 5's `no` row no longer collides**: two separators widened from `\,` (1.3 pt at
   `\scriptsize`) to 4 pt and 3.5 pt, measured in the rendered PDF.
6. **Three reference defects**: `bond2017` printed 8 of 14 authors with no "et al."; the ORB6 entry
   omitted its second author and credited a man who died in 1997; and the 1 per cent bandpass figure
   was cited to a technical note that contains 0.1 per cent, and now cites the ALMA Knowledgebase
   article that states it.
7. **Conclusion 1 carries the introduction's "at narrowband resolution" qualifier**, so the novelty
   ratio inherits a qualified claim.
8. **Sec. 4.2 sets the expectations against the 50 census crossings**, not against all 52, which is
   what Sec. 5.3.1, Appendix D.1 and Table A2 row 1.1.2 have always done.

## Open, and flagged rather than fixed

- **The page count is 36 and no content was deleted to reduce it.** The length decision is Glenn's:
  OJA sets no limit, and at this journal a page can only leave the count by deletion.
  ★ The build the blocker pass ran on was 35 pp, and the eleven fixes are net additive: a 64th
  bibliography entry, a count that was missing from four sentences, and the qualifiers two
  conclusions needed. The last page carries the final ten references, 501 characters; the
  references had ended exactly at the foot of p. 35 before, so any addition at all spills. **Nothing
  was shortened to chase that boundary**, which is the standing ruling of 2026-10-10.
- `retire_macros.py` **still retires nothing** (its pattern matches the write shape, so every macro
  is protected). Deliberately untouched this round — PLAN standing item 8.
- `tab_ledgersample.tex`, `tab_persys_sample.tex` and `tab_ctl_r18.tex` are **generated and `\input`
  by nothing**: residue of the abandoned split, declared in their generators, kept because
  `si_r18.py` reads the first to pin `\SiLdgSampN` and because deleting a write on the last day of a
  round breaks assertions. Tidy next round.
- `referee_r17/absascii_r17.py` is hard-coded to **v4.18**'s PDF; run without an explicit path it
  prints the previous version's abstract. Pass the PDF.
- `tabfloor_r17.py`'s floor is back to 6.5 pt with openjournal's own comment. The *generalisable*
  idea the MNRAS pass added — pin the floor between the class's `\tiny` and `\scriptsize` **as
  printed** — is worth re-landing with this class's measured sizes.
