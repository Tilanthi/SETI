# arXiv upload set

★ **Nothing in this file is a measurement.** Every number that used to be here
went stale: it named a v3.62 manuscript under a v3.69 heading, 32 macro files
where there were 145, a 29-page paper, then a 205-item set, then a 206-item
one, then — the reason this file was rewritten — an md5, a page count and two
abstract lengths belonging to the build *before* the one in the tree, so a
reader following it would have compared the tarball with the wrong hash and
concluded the package was corrupt. **A manifest kept by hand is a manifest
that goes wrong silently.** The set is generated, the measurement is printed
by the generator, and this file tells you how to take it and what to check.

## 1. Build the set and read its own measurement

```
cd <this directory>
bash gate.sh                            # the in-tree build first: it must say ALL GATES PASS
bash arxivset.sh --force                # assemble, check A1-A15, build, compare
cat ${TMPDIR:-/tmp}/arxivset_manifest.txt   # the item list, as assembled
```

`arxivset.sh` prints, in this order: the item count and its breakdown, every
figure and the name it takes in the package, the A15 notes (what was inlined,
renamed and pruned), `A2-A6, A10-A13`, `A9`, the clean-directory build's page
count and warning profile, and finally **A8** — two md5s and a verdict.

## 2. What to verify, and against what

| check | where the number comes from | what it must say |
|---|---|---|
| the package is the paper | `arxivset.sh` A8, last line | `A8 PASS: byte-identical` |
| the tarball is the set | `arxivset.sh` A9 | `A9 PASS`, counts equal |
| the tarball you upload | `md5sum ${TMPDIR:-/tmp}/arxivset.tar.gz` | — |
| the PDF the set builds | the `clean` md5 printed by A8 | equal to the `intree` md5 beside it |
| abstract, typeset | `python3 abswords.py` | at or under the house limit |
| abstract, metadata field | `python3 absmeta.py` | pure ASCII, under 1920, equal to the page |
| main-text length | `python3 pagesplit.py` | at or under the cap it prints |

★ **A8 is the only line that makes the set a submission rather than a hope.**
It builds the package in an empty directory, from nothing but the package, and
requires the resulting PDF to equal the working tree's **to the byte**. A
byte-unsafe comment strip still builds the whole paper with zero errors; only the
byte comparison catches it. If A8 fails, nothing else in this file matters.

★ **Do not copy an md5 out of this file — there is none to copy.** Take it
from the A8 line of the run you are about to upload, and compare it with the
`.pdf` in this directory.

## 3. What the packaging step does to the names, and why

The repository's filenames carry the round and version that produced them
(`survey_numbers_round23.tex`, `tab_edge_v423.tex`, `figures/chain_v412.pdf`).
That is the build's audit trail and it stays. **arXiv, however, publishes the
source**: it lists every filename and serves every byte, and the standing
constraint is that nothing we ship may mention versions, edits, referees,
rounds or corrections. Before `A15` existed, **194 of the 222 `.tex` in the
set carried such a string in their names, 180 of them the literal word
`round`**, and the top-level source carried 188 published lines of the form
`\input{survey_numbers_round23}`.

So `arxivset.sh` neutralises the package, and only the package:

- the macro files — the manuscript's contiguous run of preamble `\input`s — are
  **inlined into one `numbers.tex`** (contiguity is asserted, not assumed);
- dead definitions are **pruned** from it: a macro nothing in the package
  expands cannot change a byte of output, and A8 proves it;
- every other `.tex` and every figure **loses its version token**, and the
  `\input` and `\includegraphics` lines are rewritten to match;
- the manuscript becomes **`ms.tex`**;
- **A15 then fails the run** if any package path, any `\input` target, any
  `\includegraphics` target, or any body text outside the journal's own class
  and style files still carries one.

★ Two things in the manuscript's preamble exist only to make that possible,
and both are reproducibility fixes in their own right:
`\pdftrailerid` pins the PDF trailer `/ID`, which pdfTeX otherwise derives from
an MD5 of the **output filename** — so without it a renamed build differed in
exactly 32 hex digits, and a neutral package name and A8's byte proof were
mutually exclusive. `\pdfsuppressptexinfo=-1` suppresses the `/PTEX.FileName`
entries pdfTeX writes into the PDF for every included figure; the shipped file
used to carry **eleven local build paths**, one of them `./figures/chain_v412.pdf`
— a version string inside the published PDF that no text sweep could see,
because a dictionary entry is not a text stream.

## 4. What the set contains, and the three things that are not ours

The breakdown is printed by the run. Everything in it is a product of **this**
build except:

- **`openjournal.cls`** and **`epsf.sty`** — the journal's own class and a
  third-party style file, which arXiv must receive verbatim. Their comments
  (and the word *referee* in the class's template footer, and *Revision* in
  `epsf.sty`'s header) are not ours to edit and A15 exempts them by name.
- **the figure PDFs**, which carry matplotlib's own `Creator`/`Producer`
  strings (`Matplotlib v3.10.9`). That is the plotting library's version, not
  the paper's.

★ **The two machine-readable tables and three supporting files ship as arXiv
ancillary files**, in `anc/`. Check **A13** holds the set and the paper's Data
availability statement to each other in both directions, refuses TeX source in
`anc/`, and refuses an ancillary file the build references. Ancillary files are
supported **only for TeX submissions** and are **not refereed and not part of
the article** (info.arxiv.org/help/ancillary_files.html), which is why the
paper rests no claim on them.

★ **Select CC-BY at upload.** OJA: *"When asked which licence you wish to use,
you should select CC-BY."* The abstract to paste into the metadata field is in
[`OJA_SUBMISSION.md`](OJA_SUBMISSION.md) §5; `absmeta.py` fails the build if it
is not the typeset paragraph transliterated character for character, and prints
its length and the headroom against arXiv's 1920. Take the number from there.

**Every requirement, its status, and what is left for the authors by hand:
[`OJA_SUBMISSION.md`](OJA_SUBMISSION.md).**
