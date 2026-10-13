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

**Current measurement** — 189 items, 2.6 MB, 400 kB `.tar.gz`; 31 pages,
0 errors, 0 undefined control sequences, 0 unresolved references or citations,
0 multiply-defined labels, 0 overfull boxes, 0 missing files, 31 underfull
boxes (all short lines in the narrow two-column measure), **2 Type 3 fonts**
in `figures/sens_ring.pdf` — the only figure of the eleven that has any.

**Every requirement, its status, and what is left for the authors by hand:
[`OJA_SUBMISSION.md`](OJA_SUBMISSION.md).** The abstract already
transliterated to plain ASCII for the arXiv metadata field is in its §5.
