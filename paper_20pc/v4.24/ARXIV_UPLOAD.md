# arXiv upload set

★ **This file used to carry a hand-maintained list of 46 items for v3.69 and
had not been touched since.** It named `technosignatures_40pc_v3.62.tex`
alongside a v3.69 heading, listed 32 macro files where there are now 145, and
described a 29-page paper. A manifest kept by hand is a manifest that goes
wrong silently, and this one had: the submission it described could not have
been built.

**The manifest is now generated, not written.** It is not kept here at all,
because a file that documents the set must not be *in* the set:

```
bash arxivset.sh                      # assemble, check A1-A12, build, compare
cat $TMPDIR/arxivset_manifest.txt     # the item list, as assembled
```

`arxivset.sh` resolves the `\input` closure and the `\includegraphics` closure
from the manuscript itself, adds `openjournal.cls` and whatever `.sty` the
class `\RequirePackage`s locally, copies every `.tex` **comment-stripped**,
writes the tarball **before** building anything, builds three times in the
empty destination, and then proves the clean-directory PDF is **byte-identical**
to the one built in the working tree. That last comparison is the only thing
that makes the set a submission rather than a hope: a byte-unsafe comment
strip still builds 31 pages with zero errors, and only the byte comparison
catches it.

**Current measurement** (2026-10-19 13:05 UTC, `arxivset.sh --force`, taken on the tree that
closes referee round 23) — **239 items = 221 tex + 1 cls (`openjournal.cls`) + 1 sty
(`epsf.sty`) + 11 figures + 5 ancillary**, 517 kB `.tar.gz`, 3.3 MB expanded; **41 pages**,
0 errors, 0 undefined control sequences, 0 unresolved references or citations, 0 multiply-defined
labels, **0 overfull boxes**, 0 missing files, 27 underfull boxes (short lines in the narrow
two-column measure), **0 Type 3 fonts**. A8 proves the clean-directory PDF **byte-identical** to
the in-tree one (md5 `2e62e8521101a7ba4b8ca1f124f550b0`), and **A13 passes in both directions**.
The abstract is **242 words / 1543 characters** typeset and **1552 characters** in the plain-ASCII
field of `OJA_SUBMISSION.md` §5, against arXiv's 1920.
★ The page count went 40 → 41 in this round for one reason, recorded so nobody tries to buy it
back: the manuscript's override of the reference-list leading was **deleted** (the author forbids
compressing the reference list for length), and the list now sets at the class default. Main text
is 23.48 pp of the 41.
★ **Do not hand-maintain the numbers in this block.** Re-run `arxivset.sh --force` and copy its
output; the measurement it replaced here (205 items, 36 pages, md5 `e799fb28…`, 2 ancillary) was
true of a build six versions back and of nothing since — in the one file whose only reader is the
submitting author.

★ The measurement this replaced — 206 items, 36 pages, md5 `099a56a6…` — was true of a build two
builds back and of neither since. A manifest is only true of the tree it was taken on, which is the
same lesson, on a different scale, as a reference audit that is only true of the version it ran on.

★ **The two machine-readable tables ship as arXiv ancillary files**, in `anc/`:
`si_catalogue.txt` (the per-window catalogue, 1663 rows) and `si_ledger.txt` (the crossing ledger,
56 rows). Check **A13** holds the set and the paper's Data availability statement to each other in
both directions, refuses TeX source in `anc/`, and refuses an ancillary file that the build
references. Ancillary files are supported **only for TeX submissions** and are **not refereed and
not part of the article** (info.arxiv.org/help/ancillary_files.html), which is why the paper rests
no claim on them.

★ **Select CC-BY at upload.** OJA: "When asked which licence you wish to use, you should select
CC-BY." The abstract to paste into the metadata field is in `OJA_SUBMISSION.md` §5; it is
**1552 characters** against arXiv's 1920 limit, pure ASCII, and `absmeta.py` fails the build if it
is not the typeset paragraph transliterated character for character. (The typeset paragraph itself
is **1543 characters / 242 words**; the pasted block is nine characters longer because the
transliteration spells out `+/-`, `x`, `10^15` and `km s^-1`, so passing one does not imply passing
the other. ★ Both numbers move with every build: take them from `abschars.py` and `absmeta.py`,
never from this sentence.)

**Every requirement, its status, and what is left for the authors by hand:
[`OJA_SUBMISSION.md`](OJA_SUBMISSION.md).** The abstract already
transliterated to plain ASCII for the arXiv metadata field is in its §5.
