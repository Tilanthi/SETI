#!/bin/bash
cd "$(dirname "$0")"
# ★ r27: A PRIVATE SCRATCH DIRECTORY PER BUILD.  TMPDIR was one shared
# directory for every build on the volume, and gate scripts (tabfloor_r17.py
# and others) write fixed names under it, so two concurrent builds overwrote
# each other's scratch.  Each TREE now gets its own, named by a hash of its
# path (deterministic, so a gate run's stdout is byte-identical run to run;
# two builds of ONE tree at once were never valid), emptied on entry and
# removed on exit.
_bt="${TMPDIR:-/tmp}/build.$(pwd -P | sha1sum | cut -c1-10)"
rm -rf "$_bt" && mkdir -p "$_bt" && export TMPDIR="$_bt"
trap 'rm -rf "$TMPDIR"' EXIT
# v4.09: pin the timestamp pdflatex stamps into the PDF (and writes into the
# log), as make_all.sh already does for the figures.  Without this the PDF is
# reproducible in content but not in bytes, so a gate re-run after a push left
# the deposited PDF differing from the one in the repository for no reason at
# all.  Same epoch as make_all.sh: 2020-01-01T00:00:00Z.
export SOURCE_DATE_EPOCH=1577836800
export FORCE_SOURCE_DATE=1
# ★ The stem is DERIVED, not typed: the manuscript filename carries the
# version, and hard-coding it here is why a version bump used to need
# thirteen edits and still broke something that failed late.  Exactly one
# manuscript .tex must exist in this directory, which is the same rule
# manuscript.main_file() enforces for the Python tools.
V=$(cd "$(dirname "$0")" && ls technosignatures_*.tex | sed 's/\.tex$//')
[ "$(printf %s "$V" | wc -l)" -eq 0 ] && [ -n "$V" ] || {
  echo "expected exactly one manuscript .tex, found: $V" >&2; exit 2; }
# ★★★ v4.11: THIS SUITE USED TO RETURN 0 WHATEVER IT PRINTED.
# There is no `set -e` (deliberately -- every gate should get to run, not
# just the ones before the first failure), so the exit status was whatever
# the LAST command happened to return.  A run printing `labelcheck: 1 FAIL`,
# `retired: 1 FAIL`, `FAIL: figure built and included nowhere`,
# `macrosyn: 1 problem(s)` and `prosenum: 1 literal(s) disagreeing` exited
# ZERO, and a 57-error LaTeX log exited zero with it.  A gate suite whose
# verdict is unreadable by anything but a human eye is a check that cannot
# fail -- the seventeenth instance of that family in this tree, and the one
# instance that was hiding all the others.
#
# So every gate is now run through `g`, which records a non-zero exit, and
# the LaTeX log's own error count is a gate in its own right.  The suite
# prints its tally and exits non-zero if anything failed.
GATEFAIL=0
FAILED=""
g() {
  local name="$1"; shift
  "$@"
  local rc=$?
  if [ $rc -ne 0 ]; then
    GATEFAIL=$((GATEFAIL+1)); FAILED="$FAILED $name"
    echo "    ^^^ GATE FAILED: $name (exit $rc)"
  fi
  return 0
}

# ★ r28 (integrate, note 14): A DRIVE THAT CRASHES IS NOT A DRIVE THAT FIRES.
# Every drive loop below used to ask only for a non-zero exit (or, for three
# families, a grep that a crash cannot satisfy but nothing said so), so a drive
# that RAISED counted as demonstrated: `prose_v412 --drive 15` had been raising
# an AssertionError ("is not driving") since v4.28 and the suite reported "all
# 20 drives fail as they must".  `drive_fired PATTERN cmd...` runs the drive
# and succeeds only if its output matches PATTERN (default FAIL, the word every
# family here prints when a clause fires) AND carries no Python traceback; a
# raising drive is named with its exception.  Demonstrated both ways on the
# integration copy (a raising drive is refused; a firing drive is accepted; a
# drive that passes is refused) -- see referee_r28/INTEGRATE.md.
drive_fired() {
  local pat="$1"; shift
  local out
  out=$("$@" 2>&1)
  DRIVE_RC=$?
  if printf '%s\n' "$out" | grep -q '^Traceback (most recent call last)'; then
    echo "    drive RAISED -- a crash is not a firing: $*"
    printf '%s\n' "$out" | grep -E '^[A-Za-z.]*(Error|Exception|Exit)' | tail -1 | sed 's/^/      /'
    return 1
  fi
  printf '%s\n' "$out" | grep -q -- "$pat"
}
# drive_fired_rc: the same, for the families whose contract is also a non-zero
# exit (a drive that exits 0 has not fired, whatever its output says).
drive_fired_rc() {
  drive_fired "$@" && [ "$DRIVE_RC" -ne 0 ]
}
for i in 1 2 3; do pdflatex -interaction=nonstopmode $V.tex > /dev/null 2>&1; done
python3 - "$V" <<'PY'
import re,sys
v=sys.argv[1]
log=open(v+'.log',errors='ignore').read()
pg=re.findall(r'Output written.*\((\d+) pages',log)
err=re.findall(r'^! .*',log,re.M)
print('pages:',pg,'| errors:',len(err),'| undef refs/cites:',len(re.findall(r'Warning: (?:Reference|Citation)',log)),
      '| multdef:',len(re.findall(r'multiply defined',log)),
      '| overfull:',len(re.findall(r'Overfull',log)),'| underfull:',len(re.findall(r'Underfull',log)))
for e in err[:8]: print('  ERR',e)
for w in re.findall(r'Warning: (?:Reference|Citation)[^\n]*',log)[:10]: print('  ',w)
for w in re.findall(r'(?:Overfull|Underfull)[^\n]*',log)[:12]: print('  ',w)
# appendix page split
try:
    import fitz
    d=fitz.open(v+'.pdf')
    t3=[(p.number+1,f[3]) for p in d for f in p.get_fonts(full=True) if f[2]=='Type3']
    print('Type3 fonts:',len(t3),t3[:6])
    # ★ v4.16: LOCATED IN THE RENDERED PDF, not looked up in the .aux.  This
    # searched for \newlabel{page:appstart}, which nobody had ever written, and
    # so printed "appendix starts p. None" for four versions -- a measurement
    # that reported nothing and said so in a word nobody read.  A \label would
    # be one labelcheck F4 refuses (never referenced, correctly), so the
    # divider the class itself typesets is what is found.  If it is not found
    # the split is reported as NOT FOUND, which is a visible failure of the
    # measurement rather than a silent None.
    ap=None
    for p in d:
        if any(b[4].strip()=='APPENDIX' for b in p.get_text('blocks')):
            ap=p.number+1; break
    if ap:
        print('appendix divider on p.',ap,'-> MAIN',ap-1,'pp, APPENDIX',len(d)-ap+1,'pp')
    else:
        print('appendix divider NOT FOUND in the PDF (none typeset, or the '
              'class no longer prints one): main/appendix split unmeasured')
except Exception as e: print('pdf introspection skipped:',e)
PY
python3 measure.py $V.tex
python3 pagesplit.py $V.pdf

echo "--- arXiv abstract limit ---"
# THE ABSTRACT'S LENGTH IS GOVERNED BY arXiv's 1920 CHARACTERS, by the ruling
# of 2026-10-13, and three gates enforce it in the three places it can be
# broken: from the source with the macros expanded, on the typeset page, and
# in the plain-ASCII text that is actually pasted into the submission form.
# The first two share no code on purpose; the third is the only one that sees
# the text a human copies, which is where a stale paragraph would be
# submitted from.  Each has been driven to fail on its own.
g abstract_limit python3 abstract_limit.py
g abschars python3 abschars.py $V.pdf
g absmeta python3 absmeta.py $V.pdf
# ★★★ v4.25: and the other file a human reads at submission time.  absmeta
# holds the pasted abstract against the page; NOTHING held `ARXIV_UPLOAD.md`,
# and it shipped a PDF md5, a page count and two abstract lengths from the
# build before the one in the tree -- the fifth stale measurement in that one
# file.  The gate holds a PROPERTY rather than four numbers, because pinning
# the numbers would make it the sixth gate here to pin a literal instead of a
# fact: the file may state no measurement at all, and must name the command
# that prints each one.  Five clauses, each demonstrated firing, plus a
# control proving a number inside a code span is a command and not a claim.
g arxivpin_self python3 arxivpin.py --selftest
g arxivpin python3 arxivpin.py
# ★ v4.11: the WORD count -- ours, not a journal's and not arXiv's -- measured
# on the typeset paragraph rather than on the source.  A comment in
# abstract.tex once claimed 245 words where the printed paragraph held 253 --
# an eight-word error in the one number a journal used to check mechanically.
# It fails rather than passes when it cannot find the abstract, because a
# length check that silently measures nothing reports success for a paper
# whose abstract it never saw.  It is a style alarm: it may not be used to
# justify cutting a measurement, and it is not switched off either.
g abswords python3 abswords.py
# Two names for one quantity.  macrosyn and consistency each compare a macro
# against its own source, so neither can see two macros that mean the same
# thing and disagree -- the defect that put 41 M dwarfs in one section and 21
# in another.  Driven: reintroducing that pair makes this gate exit 1.
g twinmacro python3 twinmacro.py

echo "--- the published counts partition each other (Ruling 9, round 25) ---"
# ★★★★ SIX OF REFEREE 2's FOURTEEN INCONSISTENCIES WERE ONE SHAPE: a count
# published by one generator that is the sum of counts published by others,
# with nothing anywhere comparing the two.  Every generator asserted its own
# arithmetic and every one of those assertions passed; what nothing checked
# was the arithmetic BETWEEN them, which is why fourteen inconsistencies
# survived five rounds of referees and were found by a reader.  This gate
# owns exactly that, reads the macro layer rather than recomputing anything,
# and requires each identity to close in integers.  Each identity is also
# checked for VACUITY, because a partition check that passes on a missing
# macro is the defect it exists to catch one level up.
g partition python3 partition_r25.py
echo "--- no clause is typeset verbatim in two files (Ruling 13, round 25) ---"
# ★★★★ The author has asked about unwarranted repetition for SEVEN rounds and
# every instance so far was found by a person reading the paper.  A 16-gram
# cross-file scan found four more still shipping -- one of them created by a
# ruling in the same round that cut four others -- and NO GATE IN THIS TREE
# COULD SEE ANY OF THEM.  It normalises whitespace before matching, because
# the clause that survived round 24 survived by wrapping across a source line
# break, and a wrap-blind version of this gate would have missed it too.
# Deliberate restatements live in `dupgate_allow.txt`, each with a written
# keep-reason; an entry without one is refused.
g dupgate python3 dupgate.py
g dupgate_drive drive_fired_rc FAIL python3 dupgate.py --drive 1
echo "--- generator/round-file ownership (v3.99: added after a silent overwrite) ---"
g roundcollide python3 roundcollide.py
g orphanround python3 orphanround.py

# ---------------------------------------------------------------------------
# These four gates were in make_all.sh only.  make_all.sh regenerates; gate.sh
# checks what is on disk -- so a build that skipped the regeneration (which is
# every build during a prose pass, by the standing rule that make_all.sh must
# not run while prose is in flux) ran NONE of them.  A stray build could
# therefore hide a duplicate label, a retired macro name, an orphan figure or
# a ledger that is not the adopted crossing list, which is exactly the class of
# defect each exists to catch.  They are cheap and they read only the tree.
echo "--- the reference layer (duplicate, dangling and aliased labels) ---"
g labelcheck python3 labelcheck.py "$V.tex" --aux "$V.aux"
echo "--- retired macro NAMES may not appear in the manuscript ---"
g retired python3 retired.py
echo "--- figures: none built-and-uncited, none cited-and-missing ---"
g figorphan python3 figorphan.py
# ★ drive 4, added v4.26: the captioned-orphan-fragment clause.  An orphan
# generated `tab_*.tex` that carries a caption is prose published and
# unmaintained -- `tab_maskband_v411.tex` shipped a caption asserting the
# superseded line mask, in a file no `\input` reads, so no prose gate in
# this tree could see it.
g figorphan_drive4 drive_fired_rc FAIL python3 figorphan.py --drive 4
echo "--- the typeset ledger IS the adopted crossing list ---"
# Pass the fragment the MANUSCRIPT inputs, not the gate's own default.  Its
# docstring says it reads "the fragment the manuscript inputs" and it does
# not -- it hard-codes tab_ledger.tex -- so while the manuscript inputs any
# other ledger fragment the gate passes on a table the reader never sees.
# Deriving the argument here makes the claim true from this side.
LEDGFRAG=$(python3 - <<'PYEOF'
import re, sys
sys.path.insert(0, '.')
import manuscript
# The manuscript inputs TWO ledger fragments -- the crossing ledger and its
# summary -- and the summary is \input first, so taking the first match
# handed the gate a table with no crossing rows and it reported 3 FAIL on a
# fragment it was never meant to read.  Take the per-crossing ledger: the
# exact name if present, otherwise the tab_ledger* fragment with the most
# rows, which is the one a reader reads crossing by crossing.
# ★ 2026-10-07: the ledger is typeset in PARTS now (a table* cannot break
# across a page, and the one that could not broke over the text under it).
# Hand the gate EVERY part the manuscript inputs, not the biggest one: the
# previous rule picked one fragment, so a split table would have been checked
# half at a time and the missing half reported as a row-count failure at
# best.  The summary table is excluded by name, as before.
# ★★★★ r20-final: THE ARTICLE NOW PRINTS A SAMPLE AND ATTACHES THE LEDGER AS
# DATA, so the fragment this gate must read is no longer one the manuscript
# \input{}s.  `tab_ledgersample` is excluded by name -- handed to
# `ledgergate.py` it would report 47 missing crossings against a sample that
# is correct -- and the fallback is the FULL generated fragment, which is the
# file the ancillary ledger is written from in the same loop.  So the check
# still reads one row per adopted crossing, and `ledger_v410.py` separately
# asserts that every printed sample row is a row of that fragment, cell for
# cell, in the sample's own columns.
cand = [c for c in re.findall(r'\\input\{(tab_ledger[A-Za-z0-9_]*)\}',
                             manuscript.flat())
        if not c.startswith(('tab_ledgersum', 'tab_ledgersample'))]
seen, out = set(), []
for c in cand:
    if c not in seen:
        seen.add(c)
        out.append(c + '.tex')
print(' '.join(out) or 'tab_ledger.tex')
PYEOF
)
echo "    ledger fragment(s) the manuscript inputs: $LEDGFRAG"
g ledgergate python3 ledgergate.py $LEDGFRAG

echo "--- cross-reference resolution (R2-t2) ---"
g xrefcheck python3 xrefcheck.py

echo "--- macro synonyms and ledger identities (referee 2, M2) ---"
echo "--- two macros that MEAN the same thing may not carry two values (v4.11) ---"
g synmacro python3 synmacro.py
g macrosyn python3 macrosyn.py
echo "--- primary-statistic consistency (referee 2, v3.99) ---"
g consistency python3 consistency_v399.py

echo "--- macro leakage (referee 2, v3.99) ---"
echo "--- prose literals vs macros (referee 2, M6) ---"
g prosenum python3 prosenum_v399.py
g macroleak python3 macroleak.py

echo "--- every integer in running prose is registered (referee 2, item 1) ---"
g intsweep python3 intsweep.py

echo "--- two generators publishing one quantity under two names (v4.16) ---"
# ★★★★ `twinmacro` and `synmacro` group macros by NAME STEM and `roundcollide`
# compares round FILENAMES, so none of the three can see two generators that
# publish one quantity under two UNRELATED names -- which happened twice this
# round, once with four quantities at once, fourteen minutes apart.  Worse,
# `twinmacro` skips a same-stem group whose members AGREE ("harmless"), and for
# a twin agreement today is exactly what hides the divergence tomorrow.
# `valuetwin` groups every cited macro by its printed value AND by the unit
# beside it at the use site, and fails on a cross-generator group declared
# neither one quantity (twinmacro.SAME, which enforces the equality) nor a
# coincidence of two different quantities.  Four drives, all demonstrated.
g valuetwin python3 valuetwin.py

echo "--- generated fragments older than the catalogue they describe ---"
# In make_all.sh only, so it ran on no prose-pass build at all -- and the eight
# fragments it caught this round were eight tables describing a catalogue that
# had been regenerated since.  Same argument as the four gates moved here at
# v4.11: make_all.sh regenerates, gate.sh checks what is on disk.
g fragstale python3 fragstale.py

echo "--- what round 15's prose claims is measured, not asserted (v4.16) ---"
# `prosegate_r15.py` publishes NOTHING -- no round file, no \input line,
# nothing for `roundcollide` to see -- so a suite that does not name it is a
# gate that never runs again.  Eight checks, all eight driven; drives 1 and 4
# each fire two, which is correct rather than sloppy: perturbing the
# recomputed drift ceiling must also break the published percentage derived
# from it.
g prosegate python3 prosegate_r15.py
for d in 1 2 3 4 5 6 7 8 9 10; do
  if ! drive_fired_rc FAIL python3 prosegate_r15.py --drive $d; then
    echo "    ^^^ GATE FAILED: prosegate_r15 --drive $d did NOT fail"
    GATEFAIL=$((GATEFAIL+1)); FAILED="$FAILED prosegate_drive$d"
  fi
done
echo "prosegate_r15: all 10 drives fail as they must"
for d in 14; do
  if ! drive_fired_rc FAIL python3 r1_r22.py --drive $d; then
    echo "    ^^^ GATE FAILED: r1_r22 --drive $d did NOT fail -- the"
    echo "        abstract half of A2 is no longer demonstrated"
    GATEFAIL=$((GATEFAIL+1)); FAILED="$FAILED r1_r22_drive$d"
  fi
  rm -f r1_r22_drive$d.json
done

echo "--- the reference layer in both directions ---"
# Nothing in this build swept CITATIONS.  xrefcheck does labels, figorphan does
# figures, macroleak does macros; the bibliography was the one layer with no
# owner, and the last two rounds each stranded an entry by hand and found it by
# hand.  An uncited \bibitem typesets silently and an undefined citation is a
# warning the build survives, so latexlog passes either way.
g citegate python3 citegate.py
echo "--- no unfulfilled promise of a deposit (Glenn, 2026-10-08) ---"
# ★★ INVERTED, AND THEREFORE IN THE SUITE FOR THE FIRST TIME.  This gate
# used to fail by design until an author minted a Zenodo DOI, and was kept
# out of every build because "a gate that blocks every build gets switched
# off".  Glenn has now instructed that there be no deposit, so it asserts
# the opposite: that the paper carries no unfulfilled promise of one, and
# that the honest content which replaced the promise is still there.  It is
# the only thing standing between a later prose pass and the return of "the
# data release holds...".  `--selftest` runs 20 cases of which 14 must FAIL.
# ★ If it fires, do not whitelist: either state the quantity in the paper or
# say nothing about it.
g doigate python3 doigate.py
# ★★★ ADDED v4.27 by r26-integrate.  `doigate.py --selftest` was printing
# **THE CHECK IS BROKEN** and exiting 1 in the PUSHED v4.26 tree -- one of
# its eleven cases substituted a string that is not in the manuscript, so
# the case could not fail -- and nothing saw it, because the suite ran the
# gate and never its self-test.  A self-test nothing runs is a check that
# cannot fail; the suite now runs it.  Same argument as `selftest_v409.py`
# being in here rather than in a README.
g doigate_selftest python3 doigate.py --selftest
# ★ r36 (N4, author ruling 2026-11-09 "the DOI will be added after acceptance"): doigate D4 RESTATED -- no
# placeholder and no unsupplied Zenodo DOI in the manuscript, the PDF text, the deposit (tree + zip), the
# metadata or the notes, with no acknowledged-blocker pass -- and D5 NEW (the "added on acceptance" statement
# present, once; no \SIdoi).  Each drive plants one defect in memory (1 bibitem placeholder, 2 deposit README,
# 3 PDF text, 4 metadata doi, 5 an invented Zenodo DOI, 6 the statement deleted, 7 a second "on acceptance",
# 8 an allowed DOI outside its bibitem) and must FAIL; drives write nothing.
for d in 1 2 3 4 5 6 7 8; do
  if ! drive_fired_rc "^FAILED: " python3 doigate.py --drive $d; then
    echo "    ^^^ GATE FAILED: doigate --drive $d did NOT fail"
    GATEFAIL=$((GATEFAIL+1)); FAILED="$FAILED doigate_drive$d"
  fi
done
echo "doigate: all 8 drives fail as they must"
# ★★★★ ADDED v4.27.  `make_all.sh` line 38 has claimed since v4.01 that
# *"macrosource.py fails the build if a frozen macro file ever reappears"*
# and THERE WAS NO macrosource.py.  It now exists and asserts the wider
# fact that matters: `adopted_e90._texval()` reads any macro file the
# manuscript does NOT \input AFTER every file it does, so such a file wins.
# 189 \input lines against 189 files on disk, M1-M4, three drives.
g macrosource python3 macrosource.py
# ★★★ ADDED v4.27.  `prosecount.py` did not compile in the pushed tree --
# `IndentationError`, the only one of ~370 shipped .py files in that state,
# and four REFEREE_RESPONSE documents name it as the tool that counted the
# prose quoted to a referee.  Every other gate reasons about CONTENT, and a
# file that cannot be parsed has no content to disagree with.
g pycompile python3 pycompile.py
# ★★★★ ADDED v4.27.  `zverify.py` was never in this suite, so "all 44 gates
# pass" has never said anything about the deposit the paper cites -- and in
# round 26 the zip went stale against its own tree while every gate stayed
# green.  V8 compares the archive with the tree member by member and V9
# compares each deposited quantity with the macro the article prints it from.
g zverify python3 zverify.py
# ★★★★ ADDED v4.27 (B4).  V5 IS THE JOIN GATE AND IT COULD NOT FAIL ON THE
# DEFECT THAT BREAKS A JOIN: it built both sides of the window key as `set`s,
# so a key duplicated over several rows -- 35 of 1663 in the shipped archive,
# which is what made the README's own join irreproducible -- was invisible to
# it, while a key present in NO window row was the only thing it could see.
# It now compares multisets on the documented four-field key, and both
# conditions are demonstrated here: drive 1 plants a duplicated key, drive 2
# removes the window a control row joins.  Neither writes anything.
for d in 1 2; do
  if ! drive_fired_rc FAIL python3 zverify.py --drive $d; then
    echo "    ^^^ GATE FAILED: zverify --drive $d did NOT fail -- the join"
    echo "        clause no longer sees a duplicated or an unjoinable key"
    GATEFAIL=$((GATEFAIL+1)); FAILED="$FAILED zverify_drive$d"
  fi
done
echo "zverify: both V5 drives fail as they must"
# round 28, Ruling R14: V10 -- every deposit path the article cites is in the
# zip.  Drive 3 removes one cited member from the zip's member list in memory;
# V10 itself (not some other clause) must report FAIL.
if ! drive_fired "^V10  FAIL" python3 zverify.py --drive 3; then
  echo "    ^^^ GATE FAILED: zverify --drive 3 did NOT fail V10 -- a cited deposit"
  echo "        path missing from the zip would ship unseen"
  GATEFAIL=$((GATEFAIL+1)); FAILED="$FAILED zverify_drive3"
fi
echo "zverify: V10 drive fails as it must"
# round 30, R1-3 + R2 M14: V10b (no pointer into an archive narrative), V11
# (a clean run from the unzipped deposit alone rebuilds the article's chance
# comparison, completeness factor and sensitivity summaries, unrounded values
# included), V12 (no narrative file in the archive; the pipeline is the
# production copy).  Each drive must make ITS OWN clause report FAIL:
#   4  one window's control exceedances raised in the unpacked copy  -> V11
#   8  one article value moved                                        -> V11
#   5  a narrative file planted in the listing                        -> V12
#   6  one pipeline file's recorded sum altered                       -> V12
#   7  a pointer to an archive narrative added                        -> V10b
#   9  one code generation dropped from the archive (v4.31)          -> V13
#  20  the deposit's reproduce.py made to fail (r35 N4): V11 must print FAIL, no NameError/traceback
for dc in "4:V11 " "8:V11 " "5:V12 " "6:V12 " "7:V10b" "9:V13 " "20:V11 "; do
  d=${dc%%:*}; c=${dc#*:}
  if ! drive_fired_rc "^$c FAIL" python3 zverify.py --drive $d; then
    echo "    ^^^ GATE FAILED: zverify --drive $d did NOT fail ${c% } -- the"
    echo "        clean-run / no-narrative / pipeline-identity clause is blind"
    GATEFAIL=$((GATEFAIL+1)); FAILED="$FAILED zverify_drive$d"
  fi
done
echo "zverify: V10b, V11, V12 and V13 drives fail as they must"
echo "--- no generated lower-case word may open a sentence ---"
# A generated English word is lower case by construction, so a sentence opening
# on one typesets a misspelling that every value-comparing gate here passes:
# "and 34 do not. three of the unattributed coincide with sulphur monoxide".
# prose_v412.py's P8c covers the four front-matter files; this covers all 26.
g wordcase python3 wordcase.py

echo "--- no self-reference, and no unnamed comparative (Glenn, 2026-10-13) ---"
# ★★★★ GLENN, 2026-10-13: "If this is something that refers to an earlier test
# we did, you were forbidden to refer to earlier tests -- the paper has to read
# as a completely fresh paper without evidence of going through earlier
# versions of refereeing", and -- on being told the sentence was about somebody
# else's test -- "If as you say it is someone elses test, then you need to make
# this clearer, as I misread it".  THE AUTHOR OF THE PAPER MISREAD HIS OWN
# SENTENCE, which settles it: an UNNAMED comparative is a defect whether or not
# it is factually about someone else.  Nothing in this build had ever looked,
# and the defect had reached a shipped PDF four rounds running.
# Two streams -- the source, and the typeset text a reader actually gets --
# because either alone is blind to half of it; HARD phrases fail outright,
# comparatives fail unless the antecedent is named in the same sentence or the
# one before, and every legitimate remainder is declared ONCE in
# prosegate_allow.txt and PINNED BY HASH to its sentence, so rewording lapses
# the pin and an exemption that matches nothing is itself a failure.  It writes
# nothing a production path reads.  Drives 1-5 must each fail; drive 0 passes.
pdftotext "$V.pdf" "${TMPDIR:-/tmp}/prosegate_pdftext.txt" 2>/dev/null
g prosegate_selfref python3 prosegate_selfref.py --version-dir . \
    --pdf-text "${TMPDIR:-/tmp}/prosegate_pdftext.txt" \
    --allow prosegate_allow.txt

echo "--- nothing in the TYPESET page, figures included, reads as machine narration (v4.24) ---"
# ★★★ THE ONE CHECK THAT SEES INSIDE A FIGURE, AND IT WAS NOT IN THIS SUITE.
# `genai_sweep.py` reads the PDF text layer in three renderings, so it sweeps
# figure interiors automatically -- which is the only automatic coverage this
# build has of the author's "no trace of refereeing, no version, no round
# number anywhere" rule inside a plot.  Until v4.24 it had to be REMEMBERED,
# and three figure generators print text.  A rule that depends on somebody
# remembering is not a rule.
#
# ★★ Its own docstring used to say "do not wire this into gate.sh": the
# objection was that the hits would be whitelisted inside a round and it would
# become one more gate that cannot fail.  That is true of a word-level
# whitelist and false of a SENTENCE PIN -- the distinction `prosegate_selfref`
# three lines above already makes.  Every one of the seven current hits is
# declared in `genai_allow.txt` by a sha1 of (family, sentence), so rewording
# any of them lapses the pin and the gate re-fires; an unpinned hit FAILS; an
# exemption matching nothing FAILS; and a PDF whose text layer is under
# 100 000 characters FAILS rather than passing as "clean".
# Both failure directions are demonstrated in the same run that passes:
# `--selfdrive 1` plants an unpinned hit, `--selfdrive 2` plants a stale
# exemption, and each must exit non-zero.
g genai_sweep python3 genai_sweep.py "$V.pdf" --allow genai_allow.txt
# ★ v4.25: drive 3 added with the furniture strip -- it reads the running head
# back into the page text, which is the state the gate was in when a sentence
# straddling a page break pinned with "24 White & Dey" inside it.
for d in 1 2 3; do
  if ! drive_fired_rc FAIL python3 genai_sweep.py "$V.pdf" --allow genai_allow.txt --selfdrive $d; then
    echo "    ^^^ GATE FAILED: genai_sweep --selfdrive $d did NOT fail -- the"
    echo "        clause it exercises is vacuous"
    GATEFAIL=$((GATEFAIL+1)); FAILED="$FAILED genai_sweep_drive$d"
  else
    echo "genai_sweep: --selfdrive $d fails as it must"
  fi
done


echo "--- the abstract carries every statement it is required to carry (r17) ---"
# ★★ Four of the seven statements the abstract must carry were gated by
# NOTHING: the count of crossings whose repeats cannot test them, the
# decorrelation disclosure, the dependence of the chance comparison on the
# reserved events, and the admissible-but-not-acting calibration residual.
# Each of the four is a QUALIFICATION -- the part of a sentence that can be
# deleted without the sentence becoming ungrammatical, which is exactly what a
# character budget reaches for first.  Keyed on the macro that carries each
# statement, not on a sentence; refuses to run if the extracted paragraph
# falls below a 900-character floor, so it cannot pass on an abstract it never
# read.  Seven checks, all seven driven.
g absreq python3 absreq_r17.py

echo "--- every clause of the two front-matter gates is DEMONSTRATED, not just asserted (v4.25) ---"
# ★★★★ THREE DRIVES WERE DEAD IN A SHIPPED BUILD AND NOTHING COULD SEE IT.
# `absreq_r17.py` and `prose_v412.py` each carry a `--drive N` for every clause
# they assert, and the whole point of a drive is that it must FAIL: a clause
# whose drive has stopped firing is a clause that is no longer demonstrated.
# But nothing ran them.  In v4.24 as pushed, `prose_v412.py` drives 4, 10 and
# 12 had all expired against their own sentences -- `perturb()` raised "made 0
# of 1 substitutions" rather than driving -- so P4's rank clause, P4's
# operational statement and P10's withdrawn-population ban were asserted in
# the build and demonstrated in none of it.  Expiry is the normal fate of a
# drive keyed on a form of words, and this file records SEVEN of them; the
# defect is not the expiry, it is that a round can close without noticing.
#
# ★ So both drive sets run here, and each drive must exit non-zero.  A drive
# that PASSES is reported as a failure of the suite, which is the only way the
# distinction "asserted" / "demonstrated" can be mechanical.  Drives write
# `*_driveN.*` and never a production path (the standing rule since v4.09), and
# the loop removes what they wrote so the tree is unchanged either way.
# r28-abstract (v4.29): drive 15 is B10, the abstract's arithmetic.
for d in 1 2 3 4 5 6 7 8 9 10 11 12 13 14 15 16; do
  if ! drive_fired_rc FAIL python3 absreq_r17.py --drive $d; then
    echo "    ^^^ GATE FAILED: absreq_r17 --drive $d did NOT fail -- the"
    echo "        clause it exercises is no longer demonstrated"
    GATEFAIL=$((GATEFAIL+1)); FAILED="$FAILED absreq_drive$d"
  fi
done
echo "absreq_r17: all 16 drives fail as they must"
for d in 1 2 3 4 5 6 7 8 9 10 11 12 13 14 15 16 17 18 19 20; do
  if ! drive_fired_rc FAIL python3 prose_v412.py --drive $d; then
    echo "    ^^^ GATE FAILED: prose_v412 --drive $d did NOT fail -- the"
    echo "        clause it exercises is no longer demonstrated"
    GATEFAIL=$((GATEFAIL+1)); FAILED="$FAILED prose_v412_drive$d"
  fi
  rm -f numbers/survey_numbers_round200_drive$d.tex
done
echo "prose_v412: all 20 drives fail as they must"
# ★★★★ ADDED v4.27 (S8, B1, S3).  THREE MORE CLAUSE SETS THAT WERE ASSERTED IN
# THE BUILD AND DEMONSTRATED IN NONE OF IT.  `chance_v414.py`'s A18 is the
# prose clause behind Ruling 9 -- and its drive 21 had been STALE SINCE v4.26,
# keyed on a phrase that round's rewrite deleted, so it perturbed nothing and
# reported a pass; `sens_r18.py`'s X15 and `r1_r22.py`'s A13 are new this round
# and must not join it.  chance_v414 prints FAILED and exits 0 under --drive by
# design (a drive is read from its output, not its status), so the test here is
# the printed verdict; the other two exit non-zero.  Every drive writes
# `*_driveN.*` only, and the loops remove what they wrote.
for d in 19 20 21 22 32; do
  if drive_fired "^FAILED: .*A18" python3 chance_v414.py --drive $d; then
    : # the clause is demonstrated
  else
    echo "    ^^^ GATE FAILED: chance_v414 --drive $d did NOT fail A18 -- the"
    echo "        prose clause of Ruling 9 is no longer demonstrated"
    GATEFAIL=$((GATEFAIL+1)); FAILED="$FAILED chance_v414_drive$d"
  fi
  rm -f numbers/survey_numbers_round310_drive$d.tex chance_v414_drive$d.json \
        chance_perwin_v422_drive$d.json
done
echo "chance_v414: all 5 A18 drives fail as they must"
# ★ r32 (R1-1): A31 -- the added-population bound is read off the LOWER tail and the deposited curve
# (statistics/chance_allowance_table.csv) is the one the page prints.  Drive 41 reads the "allowance"
# off the upper tail (the text defect the referee found); drive 42 builds the curve on the stepped
# expectation while the page prints the control-only one.  Both must fail A31.
for d in 41 42; do
  if ! drive_fired "^FAILED: .*A31" python3 chance_v414.py --drive $d; then
    echo "    ^^^ GATE FAILED: chance_v414 --drive $d did NOT fail A31"
    GATEFAIL=$((GATEFAIL+1)); FAILED="$FAILED chance_v414_drive$d"
  fi
  rm -f numbers/survey_numbers_round310_drive$d.tex chance_v414_drive$d.json \
        chance_perwin_v422_drive$d.json
done
echo "chance_v414: both A31 allowance drives fail as they must"
# r28 (integrate, note 2): A27 binds Appendix D.1's two direction sentences
# ("conclusion unchanged", "every ratio measured is an excess") to the values
# they read.  Drive 36 moves both across their verdicts; A27 must fail.
# r29 (apx): D.1 was halved and no longer prints either sentence, so A27 is
# vacuous by its own design; the drive runs whenever either sentence returns.
if cat sections/*.tex | tr '\n' ' ' | grep -q -e "conclusion is unchanged" -e "every ratio measured is an excess"; then
if ! drive_fired "^FAILED: .*A27" python3 chance_v414.py --drive 36; then
  echo "    ^^^ GATE FAILED: chance_v414 --drive 36 did NOT fail A27"
  GATEFAIL=$((GATEFAIL+1)); FAILED="$FAILED chance_v414_drive36"
fi
rm -f numbers/survey_numbers_round310_drive36.tex chance_v414_drive36.json \
      chance_perwin_v422_drive36.json
echo "chance_v414: the A27 direction drive fails as it must"
else
echo "chance_v414: A27 not exercised -- no direction sentence on the page (r29 apx)"
fi
# r28 (integrate, note 7): orbit_r18 K1 -- App. C's Keplerian speed is computed
# at the mass ceiling and must lie inside the mask half-width it justifies.
if ! drive_fired "^FAILED: .*K1" python3 orbit_r18.py --drive 8; then
  echo "    ^^^ GATE FAILED: orbit_r18 --drive 8 did NOT fail K1"
  GATEFAIL=$((GATEFAIL+1)); FAILED="$FAILED orbit_r18_drive8"
fi
rm -f numbers/survey_numbers_round803_drive8.tex orbit_r18_drive8.json
echo "orbit_r18: the K1 drive fails as it must"
# r29 (r29-recur, register rows 3-9): every check added for M1, M2, M4, M11,
# M12 and R1-5 is driven to fail on its own.  Each driven run writes
# `*_driveN.*` only; everything a drive wrote is removed by the stamp below.
_r29stamp=$(mktemp)
r29drive() {   # r29drive LABEL PATTERN cmd...
  local lab="$1"; shift
  if ! drive_fired "$@"; then
    echo "    ^^^ GATE FAILED: r29 drive $lab did NOT fire"
    GATEFAIL=$((GATEFAIL+1)); FAILED="$FAILED r29_$lab"
  fi
}
r29drive recur20 "assertions failed.*A19" python3 recur_v411.py --drive 20
r29drive recur21 "assertions failed.*A20" python3 recur_v411.py --drive 21
# ★ r36 (N1, Referee 2 R2-1): A21 (no catalogued covering block named and left unread) and A22 (the window setting
# the field leader's limit is among the separated blocks read).  Cleaned by the r29 stamp below (*_driveN.*).
r29drive recur22 "assertions failed.*A21" python3 recur_v411.py --drive 22
r29drive recur23 "assertions failed.*A22" python3 recur_v411.py --drive 23
r29drive holdout20 "assertions failed.*H20 (r29" python3 holdout_v412.py --drive 20
r29drive statunit8 "^FAILED: .*U10" python3 statunit_v426.py --drive 8
r29drive tolrecur7 "^FAILED: .*R10 " python3 tolrecur_r21.py --drive 7
r29drive tolrecur17 "^FAILED: .*R9 " python3 tolrecur_r21.py --drive 17   # r36 (N1): R9 restated (x5 -> x2)
r29drive pairs20 "P20 (r29.*FAIL" python3 pairs_v415.py --drive 20
r29drive confirm20_8 "^FAILED: .*K8" python3 confirm_r20.py --drive 8
r29drive twostars22 "FAIL .*T9b (r29" python3 twostars_r27.py --drive 22
r29drive twostars23 "FAIL .*TS (r29" python3 twostars_r27.py --drive 23
r29drive twostars24 "FAIL .*TJ (r29" python3 twostars_r27.py --drive 24
r29drive twostars25 "FAIL .*TK (r29" python3 twostars_r27.py --drive 25
r29drive twostars26 "FAIL .*TB2 (r29" python3 twostars_r27.py --drive 26
# r30 merge (Ruling R14): the widened window over separated sessions only --
# each of the four generators that forms the covering set, driven to admit the
# same-session windows, fails on its own clause or on the cross-generator
# identity that holds the four sets together.
r29drive recurnull23 "assertion(s) fired .*W10 (r30" python3 recurnull_v413.py --drive 23
# v4.33 (extractor fold): W9b -- "the" block is named only for a set of one (CP-72 2713 X502d has five)
r29drive recurnull32 "assertion(s) fired .*W9b" python3 recurnull_v413.py --drive 32
r29drive statunit9 "^FAILED: U1 " python3 statunit_v426.py --drive 9
r29drive pairacct8 "^FAILED: A1 " python3 pairacct_r23.py --drive 8
r29drive twostars27 "FAIL .*T2 the rebuilt" python3 twostars_r27.py --drive 27
for _d in 1 2 3 4 5; do
  _t=$(echo "T1 T3 T4 T2 T0" | cut -d' ' -f$_d)
  r29drive triple$_d "assertions failed.*$_t " python3 triple_r30.py --drive $_d
done
find . numbers r21inputs -maxdepth 1 -newer "$_r29stamp" -name '*_drive[0-9]*' -type f -delete
rm -f "$_r29stamp"
echo "r29-recur: the separation, control-rate, triple, drift and sigma drives fail as they must"
# r30 merge (v4.30): r29-counts' new checks (COUNTS.md flag 6) and the
# merger's Ruling R13(b) rounding-edge clauses, each driven to fail on its own.
# Every driven run writes `*_driveN.*` only; the stamp removes what they wrote.
_r30stamp=$(mktemp)
r29drive chance38 "^FAILED: .*A28 " python3 chance_v414.py --drive 38
r29drive chance39 "^FAILED: .*A29 " python3 chance_v414.py --drive 39
r29drive counts24 "^FAILED: .*A3k " python3 counts_r15.py --drive 24
r29drive counts25 "^FAILED: .*A3j " python3 counts_r15.py --drive 25
r29drive proxb8 "X8 the planet.*FAIL" python3 proxb_v423.py --drive 8
r29drive reflagdecl7 "R10 the recalibrated.*FAIL" python3 reflagdecl_r29.py --drive 7
g sens_r28_selftest python3 sens_r28.py --selftest
r29drive chance40 "^FAILED: .*A30 " python3 chance_v414.py --drive 40
r29drive fieldread10 "^FAILED: .*F9 " python3 fieldread_r23.py --drive 10
r29drive twostars28 "FAIL .*TE (r30" python3 twostars_r27.py --drive 28
r29drive twostars29 "FAIL .*TV (r35" python3 twostars_r27.py --drive 29   # r35 N2: the corrected J1537 fits apply only to the archived fits they name
r29drive bkg9 "^FAILED: .*A12 (r30" python3 bkg_r28.py --drive 9
r29drive appm1 "FAIL M1 (r30" python3 appm_v405.py --drive 1
r29drive quality21 "assertions failed.*Q17 (r30" python3 quality_r19.py --drive 21
r29drive freqocc1 "FAIL F1 (r30" python3 freqocc_v405.py --drive 1
r29drive calib10 "^FAIL T1 (r30" python3 calib_r15.py --drive 10
r29drive sens11_33 "FAILURES: .*SR1 (r30" python3 sens_r11.py --drive 33 --nofig
r29drive bookkeep14 "assertions failed: .*'B14'" python3 bookkeep_r13.py --drive 14
# fold30 (Ruling R16(c)): the broad-feature replicates' rounding-edge clause
r29drive screen16 "FAILED: .*S14" python3 screen_r23.py --drive 16
r29drive sens11_34 "FAILURES: .*R15a (fold30" python3 sens_r11.py --drive 34 --nofig
r29drive stackfix13 "assertions failed: [1-9].*'A11'" python3 stackfix_v413.py --drive 13
# ★ r35 (N4, A3): maskso_v414 S10 (the mask is App C's rule re-derived from the frozen query) and S11 (Table C1's N and n_t close
# on \FrNTrans / \McNRow); counts_r15 A3n (Table A1's "all"/"both" follow the counts) and A3m (\CtUncatStar == \OmXStar);
# sens_r11 SJ1 (injected windows joined on frequency + channel width, not the nearest ring); nofn_r35 N1-N4.
r29drive maskso10 "ASSERTION FIRED  S10 " python3 maskso_v414.py --drive 10
r29drive maskso11 "ASSERTION FIRED  S11 " python3 maskso_v414.py --drive 11
r29drive counts26 "^FAILED: .*A3n " python3 counts_r15.py --drive 26
r29drive counts27 "^FAILED: .*A3m " python3 counts_r15.py --drive 27
r29drive sens11_35 "FAILURES: .*SJ1 (r35" python3 sens_r11.py --drive 35 --nofig
# ★ r35 (N5, fresh read): sens_r11 SN4 (Table 3 names the N = 4 factor), linesupport_r18 A7 (\LnCoincStars re-counts to
# \LnAttrCoinc), edge_v423 E43 (App D.5 clause follows \EgNEdge / \EgNEdgeOut).
r29drive sens11_36 "FAILURES: .*SN4 (r35" python3 sens_r11.py --drive 36 --nofig
rm -f injected_windows_v422_drive36.json numbers/survey_numbers_round180_drive36.tex sens_r11_drive36.json tab_budget_r11_drive36.tex
r29drive linesupport8 "assertions failed .*A7 (r35" python3 linesupport_r18.py --drive 8
rm -f numbers/survey_numbers_round820_drive8.tex linesupport_r18_drive8.json
r29drive edge43 "^FAILED: E43 (r35" python3 edge_v423.py --drive 43
rm -f numbers/survey_numbers_round960_drive43.tex tab_edge_v423_drive43.tex edge_v423_drive43.json
for _d in 1:N1 2:N2 3:N3 4:N4; do
  if ! drive_fired_rc "^FAILED: .*${_d##*:}\b" python3 nofn_r35.py --drive ${_d%%:*}; then
    echo "    ^^^ GATE FAILED: nofn_r35 --drive ${_d%%:*} did NOT fail on ${_d##*:}"
    GATEFAIL=$((GATEFAIL+1)); FAILED="$FAILED nofn_r35_drive${_d%%:*}"
  fi
done
find . numbers r21inputs -maxdepth 1 -newer "$_r30stamp" -name '*_drive[0-9]*' -type f -delete
rm -f "$_r30stamp"
echo "r30 merge: the counts checks and the rounding-edge clauses fail as they must"
# r28 (register rows 5, 6, 26): bkg_r28.py's eleven assertions, eight drives.
# Like chance_v414 it prints FAILED and exits 0 under --drive, so the test is
# the printed verdict; drive 0 perturbs nothing and must pass.  Each drive
# writes `*_driveN.*` only, removed here.
if python3 bkg_r28.py --drive 0 2>&1 | grep -q "^FAILED"; then
  echo "    ^^^ GATE FAILED: bkg_r28 --drive 0 fails on unperturbed data"
  GATEFAIL=$((GATEFAIL+1)); FAILED="$FAILED bkg_r28_drive0"
fi
rm -f numbers/survey_numbers_round2820_drive0.tex bkg_r28_drive0.json
for d in 1 2 3 4 5 6 7 8; do
  if drive_fired "^FAILED: " python3 bkg_r28.py --drive $d; then
    : # demonstrated
  else
    echo "    ^^^ GATE FAILED: bkg_r28 --drive $d did NOT fail"
    GATEFAIL=$((GATEFAIL+1)); FAILED="$FAILED bkg_r28_drive$d"
  fi
  rm -f numbers/survey_numbers_round2820_drive$d.tex bkg_r28_drive$d.json
done
echo "bkg_r28: drive 0 passes and all 8 drives fail as they must"
# round 3130 (v4.31, author edit 2): the Arecibo benchmark, R1-R5, each driven.
# r34 (N1): + R6 (the x10 boundary, R2-13) and R7 (decorrelation-corrected distances, R2-4).
for d in 1 2 3 4 5 6 7; do
  if ! drive_fired_rc "^FAILED: " python3 arecibo_r31.py --drive $d; then
    echo "    ^^^ GATE FAILED: arecibo_r31 --drive $d did NOT fail"
    GATEFAIL=$((GATEFAIL+1)); FAILED="$FAILED arecibo_r31_drive$d"
  fi
  rm -f numbers/survey_numbers_round3130_drive$d.tex
done
echo "arecibo_r31: all 7 drives fail as they must"
# ★ r34 (N1, R2-1): tobs_r34 --summary T1-T7 -- the T_obs limits of the windows holding an unattributed crossing.
# Each drive writes nothing (no round-3400 file, no tobs_r34_summary.json) and exits 1.
for d in 1 2 3 4 5 6 7; do
  if ! drive_fired_rc "^FAILED: .*T$d\b" python3 tobs_r34.py --summary --drive $d; then
    echo "    ^^^ GATE FAILED: tobs_r34 --summary --drive $d did NOT fail on T$d"
    GATEFAIL=$((GATEFAIL+1)); FAILED="$FAILED tobs_r34_drive$d"
  fi
  rm -f numbers/survey_numbers_round3400_drive$d.tex
done
echo "tobs_r34: all 7 drives fail as they must"
# ★ r34 (N1, R2-4): decorhl_r34 D1-D4 -- the headline with the decorrelation divided out.
# ★ r36 (N2, R2-8): restated (the correction is ADOPTED; the values without it beside), + D5 (measured-only alternative).
for d in 1 2 3 4 5; do
  if ! drive_fired_rc "^FAILED: .*D$d\b" python3 decorhl_r34.py --drive $d; then
    echo "    ^^^ GATE FAILED: decorhl_r34 --drive $d did NOT fail on D$d"
    GATEFAIL=$((GATEFAIL+1)); FAILED="$FAILED decorhl_r34_drive$d"
  fi
  rm -f numbers/survey_numbers_round3401_drive$d.tex
done
echo "decorhl_r34: all 5 drives fail as they must"
# ★ r36 (N2, R2-8): adopted_e90 A4g -- the decorrelation term is exactly (1 + o) where an estimate exists, never a gain.
if ! drive_fired 'A4g .*FAIL' python3 adopted_e90.py --selftest --drive-decor; then
  echo "    ^^^ GATE FAILED: adopted_e90 --selftest --drive-decor did NOT fail A4g"
  GATEFAIL=$((GATEFAIL+1)); FAILED="$FAILED adopted_e90_A4g"
fi
# ★ r36 (N2, R2-4): offaxis_r36 O1-O6 (pointing slope, uncertainty, injected offset, diamond set, deepest limit on
# injected configurations, eps Eri marked); persys_r17 P14 (diamond) and P15 (dec. column = the factor applied);
# make_fig_context_v410 drive 72 (Fig. 1 label of the deepest injected-configuration limit).  Drives write nothing.
for d in 1 2 3 4 5 6; do
  if ! drive_fired_rc "^FAILED: .*O$d\b" python3 offaxis_r36.py --drive $d; then
    echo "    ^^^ GATE FAILED: offaxis_r36 --drive $d did NOT fail on O$d"
    GATEFAIL=$((GATEFAIL+1)); FAILED="$FAILED offaxis_r36_drive$d"
  fi
  rm -f numbers/survey_numbers_round3620_drive$d.tex offaxis_r36_drive$d.json
done
for d in 14 15; do
  if ! drive_fired_rc "^FAILED: P$d " python3 persys_r17.py --drive $d; then
    echo "    ^^^ GATE FAILED: persys_r17 --drive $d did NOT fail on P$d"
    GATEFAIL=$((GATEFAIL+1)); FAILED="$FAILED persys_drive$d"
  fi
done
_o=$(python3 make_fig_context_v410.py --out "${TMPDIR:-/tmp}/ctxdrive72" --drive 72 2>&1); _rc=$?
if [ $_rc -eq 0 ] || ! printf '%s\n' "$_o" | grep -qE '^AssertionError: panel \(a\) labels '; then
  echo "    ^^^ GATE FAILED: make_fig_context_v410 --drive 72 did NOT fire the label clause (rc $_rc)"
  GATEFAIL=$((GATEFAIL+1)); FAILED="$FAILED figctx_drive72"
fi
rm -rf "${TMPDIR:-/tmp}/ctxdrive72"
echo "r36 N2: adopted_e90 A4g, offaxis_r36 (6), persys_r17 P14/P15 and Fig. 1 drive 72 fail as they must"
# ★ r34 (N1, R2-1): persys_r17 P13 -- the Table F1 double bar lands on exactly the systems the T_obs factor moves.
if ! drive_fired_rc '^FAILED: P13 ' python3 persys_r17.py --drive 13; then
  echo "    ^^^ GATE FAILED: persys_r17 --drive 13 did NOT fail -- the Table F1 double-bar clause P13"
  GATEFAIL=$((GATEFAIL+1)); FAILED="$FAILED persys_drive13"
fi
# ★ r32 (R1-4): ctrlcorr_r32 C0-C5 -- the control-position correlation and the blocked resampling.
# drive 1 wrong probe seed (C1), 5 a vector swapped (C0), 2 one draw off (C2), 3 empty blocks dropped (C3),
# 4 binomial printed as the range end (C4), 6 a material shift (C5).  Each writes nothing and exits 1.
for d in 1 2 3 4 5 6; do
  if ! drive_fired_rc "^FAILED: " python3 ctrlcorr_r32.py --drive $d; then
    echo "    ^^^ GATE FAILED: ctrlcorr_r32 --drive $d did NOT fail"
    GATEFAIL=$((GATEFAIL+1)); FAILED="$FAILED ctrlcorr_r32_drive$d"
  fi
  rm -f numbers/survey_numbers_round3220_drive$d.tex ctrlcorr_r32_drive$d.json
done
echo "ctrlcorr_r32: all 6 drives fail as they must"
# ★ r34 (N2, R2-2/R2-5): chancegrid_r34 G1-G5 (8-cell grid, x4), H1-H3 (hold-out), S1-S4 (a_w) -- each driven to fail on
# its own label.  Drives read the variant JSONs of the last production run (no chance_v414 re-run) and write nothing.
for _d in 1:G1 2:G2 3:G2 4:H1 5:S3 6:G3 7:G4 8:G5 9:S1 10:S2 11:S4 12:H2 13:H3 14:G6 15:H4 16:G7 17:G8; do   # 17:G8 r35 N5 (B10)
  if ! drive_fired_rc "^FAILED: .*${_d##*:} " python3 chancegrid_r34.py --drive ${_d%%:*}; then
    echo "    ^^^ GATE FAILED: chancegrid_r34 --drive ${_d%%:*} did NOT fail on ${_d##*:}"
    GATEFAIL=$((GATEFAIL+1)); FAILED="$FAILED chancegrid_drive${_d%%:*}"
  fi
  rm -f numbers/survey_numbers_round3420_drive${_d%%:*}.tex tab_chancegrid_r34_drive${_d%%:*}.tex chancegrid_r34_drive${_d%%:*}.json
done
echo "chancegrid_r34: all 17 drives fail as they must"
# ★ r32 (R1-2): membership_r32 M1-M7 -- every printed count is the size of its set in
# statistics/event_membership.csv, and a crossing at an uncatalogued position is on neither side.
for d in 1 2 3 4; do
  if ! drive_fired_rc "^FAILED: " python3 membership_r32.py --drive $d; then
    echo "    ^^^ GATE FAILED: membership_r32 --drive $d did NOT fail"
    GATEFAIL=$((GATEFAIL+1)); FAILED="$FAILED membership_r32_drive$d"
  fi
  rm -f numbers/survey_numbers_round3210_drive$d.tex
done
echo "membership_r32: all 4 drives fail as they must"
# ★ r34 (N3, Referee 2 items 9/10/12/15/16/17): ledger_r34 Q1-Q7, each driven to fail on its own; drives write
# nothing (exit 1 before any write).  blockledger_v411 L16 (Table A1: every printed parent is the sum of its
# part rows): drive 21 drops a fate from row 3.2, drive 22 the residual row 3.1.4.
for _d in 1:Q1a 2:Q1b 3:Q2 4:Q3 5:Q4 6:Q5 7:Q6 8:Q7; do
  if ! drive_fired_rc "^FAILED: .*${_d##*:}\b" python3 ledger_r34.py --drive ${_d%%:*}; then
    echo "    ^^^ GATE FAILED: ledger_r34 --drive ${_d%%:*} did NOT fail on ${_d##*:}"
    GATEFAIL=$((GATEFAIL+1)); FAILED="$FAILED ledger_r34_drive${_d%%:*}"
  fi
done
for d in 21 22; do
  if ! drive_fired_rc "^FAILED: .*L16 " python3 blockledger_v411.py --drive $d; then
    echo "    ^^^ GATE FAILED: blockledger_v411 --drive $d did NOT fail L16"
    GATEFAIL=$((GATEFAIL+1)); FAILED="$FAILED blockledger_drive$d"
  fi
  rm -f numbers/survey_numbers_round110_drive$d.tex tab_blockledger_drive$d.tex blockledger_rows_drive$d.json
done
echo "ledger_r34 + blockledger L16: all 10 drives fail as they must"
# ★ r35 (N2, Referee 2 M3/M4/m8): jx_r35 Q1a-Q7b, each driven to fail on its own; drives write nothing (exit 1
# before any write).
for _d in 1:Q1a 2:Q2 3:Q3 4:Q4a 5:Q5 6:Q1b 7:Q7 8:Q4b 9:Q6 10:Q7b 11:Q1d; do
  if ! drive_fired_rc "^FAILED: .*${_d##*:}\b" python3 jx_r35.py --drive ${_d%%:*}; then
    echo "    ^^^ GATE FAILED: jx_r35 --drive ${_d%%:*} did NOT fail on ${_d##*:}"
    GATEFAIL=$((GATEFAIL+1)); FAILED="$FAILED jx_r35_drive${_d%%:*}"
  fi
done
echo "jx_r35: all 11 drives fail as they must"
# ★ r35 (N2b J-recal, Referee 2 M3 (1)/(2)): jrecal_r35 R1a-R4, each driven to fail on its own; drives write nothing
# (exit 1 before any write).
for _d in 1:R1b 2:R1a 3:R2 4:R3a 5:R3b 6:R4 7:R5; do
  if ! drive_fired_rc "^FAILED: .*${_d##*:}\b" python3 jrecal_r35.py --drive ${_d%%:*}; then
    echo "    ^^^ GATE FAILED: jrecal_r35 --drive ${_d%%:*} did NOT fail on ${_d##*:}"
    GATEFAIL=$((GATEFAIL+1)); FAILED="$FAILED jrecal_r35_drive${_d%%:*}"
  fi
done
echo "jrecal_r35: all 7 drives fail as they must"
# ★ r36 (N3, R2-3/R1-1/R1-2/R1-3): anycell_r36 X1-L2, each driven to fail on its own; drives write nothing
# (exit 1 before any write).
for _d in 1:X1 2:X1 3:X2 4:X3 5:X4 6:B1 7:P1 8:P2 9:L1 10:L2 11:X5; do
  if ! drive_fired_rc "^FAILED: .*${_d##*:}\b" python3 anycell_r36.py --drive ${_d%%:*}; then
    echo "    ^^^ GATE FAILED: anycell_r36 --drive ${_d%%:*} did NOT fail on ${_d##*:}"
    GATEFAIL=$((GATEFAIL+1)); FAILED="$FAILED anycell_r36_drive${_d%%:*}"
  fi
done
echo "anycell_r36: all 11 drives fail as they must"
# ★ r36 (N4, author ruling): titlerange_r36 T1-T7 (the title's frequency range, lowest searched edge rounded
# down; upper edge = the Class A one), each driven to fail on its own clause; drives write nothing.
for d in 1 2 3 4 5 6 7; do
  if ! drive_fired_rc "^FAILED: .*T$d\b" python3 titlerange_r36.py --drive $d; then
    echo "    ^^^ GATE FAILED: titlerange_r36 --drive $d did NOT fail on T$d"
    GATEFAIL=$((GATEFAIL+1)); FAILED="$FAILED titlerange_r36_drive$d"
  fi
  rm -f numbers/survey_numbers_round3660_drive$d.tex
done
echo "titlerange_r36: all 7 drives fail as they must"
# ★ r36 (N3, R2-7): every deposit path the PRINTED text names is a member of the deposit zip under that exact name
# (reads the gate's own PDF); D1 anti-vacuity, D2 membership; drive 1 drops a cited file from the archive list,
# drive 2 plants a misspelt path.
g depositpaths python3 depositpaths_r36.py
for _d in 1 2; do
  g depositpaths_drive$_d drive_fired_rc '^FAILED: D2' python3 depositpaths_r36.py --drive $_d
done
# ★ r35 (N3, Referee 2 M5/M1/m1/m2/m6/m7/m9): misc_r35 E1-W1, each driven to fail on its own (exit 1 before any
# write); blockledger_v411 L17 (Table A1 note b: the response floor removes none of the extension's eps Eri windows);
# selfunc_v411 S6d (Table 1's census cut where the sample is, G-limited extract).
for _d in 1:E1 2:E2 3:E3 4:E4 5:E5 6:E6 7:B1 8:B2 9:S1 10:S3 11:S4 12:K1 13:C1 14:W1; do
  if ! drive_fired_rc "^FAILED: .*${_d##*:}\b" python3 misc_r35.py --drive ${_d%%:*}; then
    echo "    ^^^ GATE FAILED: misc_r35 --drive ${_d%%:*} did NOT fail on ${_d##*:}"
    GATEFAIL=$((GATEFAIL+1)); FAILED="$FAILED misc_r35_drive${_d%%:*}"
  fi
done
if ! drive_fired_rc "^FAILED: L17 " python3 blockledger_v411.py --drive 23; then
  echo "    ^^^ GATE FAILED: blockledger_v411 --drive 23 did NOT fail L17"
  GATEFAIL=$((GATEFAIL+1)); FAILED="$FAILED blockledger_drive23"
fi
rm -f numbers/survey_numbers_round110_drive23.tex tab_blockledger_drive23.tex blockledger_rows_drive23.json
if ! drive_fired_rc "^FAILED: S6d " python3 selfunc_v411.py --drive 14; then
  echo "    ^^^ GATE FAILED: selfunc_v411 --drive 14 did NOT fail S6d"
  GATEFAIL=$((GATEFAIL+1)); FAILED="$FAILED selfunc_drive14"
fi
rm -f numbers/survey_numbers_round111_drive14.tex tab_selection_drive14.tex
# ★ r36 (N1, Referee 2 R2-2): selfunc_v411 S6e -- every searched object (HD 139084 B included) below the G limit.
if ! drive_fired_rc "^FAILED: S6e " python3 selfunc_v411.py --drive 15; then
  echo "    ^^^ GATE FAILED: selfunc_v411 --drive 15 did NOT fail S6e"
  GATEFAIL=$((GATEFAIL+1)); FAILED="$FAILED selfunc_drive15"
fi
rm -f numbers/survey_numbers_round111_drive15.tex tab_selection_drive15.tex
echo "misc_r35 + blockledger L17 + selfunc S6d/S6e: all 17 drives fail as they must"
# ★ v4.33 (extractor fold): xgen_r31 X2 (drive 1) and the re-extraction record X4-X6 (drives 4-6): an interim record,
# a re-extracted block's window left on its earlier product (a harvest that drops a finished block), a declared
# block that is in fact re-extracted.  xgen prints FAILED and keeps rc 0 under a drive, so the pattern is the test.
for d in 1:X2 4:X4 5:X5 6:X6; do
  if ! drive_fired "^FAILED: .*${d#*:}" python3 xgen_r31.py --drive ${d%%:*}; then
    echo "    ^^^ GATE FAILED: xgen_r31 --drive ${d%%:*} did NOT fail ${d#*:}"
    GATEFAIL=$((GATEFAIL+1)); FAILED="$FAILED xgen_r31_drive${d%%:*}"
  fi
  rm -f numbers/survey_numbers_round3120_drive${d%%:*}.tex
done
echo "xgen_r31: all 4 drives fail as they must"
# ★ r32 (R1-2): chance_v414 A32 -- the observed side is its eligible ledger rows; drive 43 puts an
# attributed crossing at an uncatalogued position on the observed side.
if ! drive_fired "^FAILED: .*A32" python3 chance_v414.py --drive 43; then
  echo "    ^^^ GATE FAILED: chance_v414 --drive 43 did NOT fail A32"
  GATEFAIL=$((GATEFAIL+1)); FAILED="$FAILED chance_v414_drive43"
fi
rm -f numbers/survey_numbers_round310_drive43.tex chance_v414_drive43.json chance_perwin_v422_drive43.json
echo "chance_v414: the A32 membership drive fails as it must"
# ★ r35 (N1, author's decision A1): the per-window attributed share is primary.  A33 -- the shares are the
# shrinkage estimator (drive 44) and the pooled check is on the primary's own draws (drive 45); A6 -- the r34
# construction (shrunk share carried with the pooled draw's relative scatter) understates the share's
# uncertainty and lets the transfer dominate the interval (drive 46).
for _d in 44:A33 45:A33 46:A6; do
  if ! drive_fired "^FAILED: .*${_d##*:} " python3 chance_v414.py --drive ${_d%%:*}; then
    echo "    ^^^ GATE FAILED: chance_v414 --drive ${_d%%:*} did NOT fail ${_d##*:}"
    GATEFAIL=$((GATEFAIL+1)); FAILED="$FAILED chance_v414_drive${_d%%:*}"
  fi
  rm -f numbers/survey_numbers_round310_drive${_d%%:*}.tex chance_v414_drive${_d%%:*}.json chance_perwin_v422_drive${_d%%:*}.json
done
echo "chance_v414: the r35 A33/A6 per-window share drives fail as they must"
# v4.32 (round 31): the new quantities, each driven.  confset_r18 C9/C10 (the split of the systems with
# no covering separated repeat), numbers_v410 C2g/C2h/C2k (the benchmark tuned to each system's best window,
# the rank-charged median; driven runs write to scratch only), sens_r18 X15b (the bounded-pair denominator).
_r31stamp=$(mktemp)
r29drive confset41 "^FAILED: .*C9 the systems" python3 confset_r18.py --drive 41
r29drive confset42 "^FAILED: .*C10 every system" python3 confset_r18.py --drive 42
_r31out=$(mktemp -d); mkdir -p "$_r31out/numbers"
for d in 61:C2g 62:C2h 63:C2k; do
  r29drive numbers${d%%:*} "ASSERTION FIRED  ${d##*:} " python3 numbers_v410.py --cat . --out "$_r31out" \
    --pick per_target_results_v3.99.csv --pick starrv_v399.json --pick bary_v405.json \
    --pick m3a_result_v400.json --pick freqocc_v405.json --drive ${d%%:*}
done
rm -rf "$_r31out"
find . numbers -maxdepth 1 -newer "$_r31stamp" -name '*_drive[0-9]*' -type f -delete
rm -f "$_r31stamp"
echo "r31: the confirmability split, the tuned benchmark and the rank-charged median drives fail as they must"
# r30 (author edit 3): Fig. 1 -- no legend over a plotted marker (66 panel a, 67 panel b) and no data point
# clipped off a panel (68).  The generator's clauses are asserts, so the firing is recognised by the clause's
# own message (a crash anywhere else does not match) and a non-zero exit; products go to scratch only.
for d in 66 67 68; do
  _o=$(python3 make_fig_context_v410.py --out "${TMPDIR:-/tmp}/ctxdrive$d" --drive $d 2>&1); _rc=$?
  if [ $_rc -eq 0 ] || ! printf '%s\n' "$_o" | grep -qE '^AssertionError: panel \((a|b)\): (a legend covers|[0-9]+ plotted point)'; then
    echo "    ^^^ GATE FAILED: make_fig_context_v410 --drive $d did NOT fire its clause (rc $_rc)"
    GATEFAIL=$((GATEFAIL+1)); FAILED="$FAILED figctx_drive$d"
  fi
  rm -rf "${TMPDIR:-/tmp}/ctxdrive$d"
done
echo "make_fig_context_v410: legend/marker drives 66-68 fail as they must"
for d in 16 18; do
  if ! drive_fired_rc FAIL python3 sens_r18.py --drive $d; then
    echo "    ^^^ GATE FAILED: sens_r18 --drive $d did NOT fail -- the"
    echo "        denominator clause X15 is no longer demonstrated"
    GATEFAIL=$((GATEFAIL+1)); FAILED="$FAILED sens_r18_drive$d"
  fi
  rm -f numbers/survey_numbers_round740_drive$d.tex sens_r18_drive$d.json
done
echo "sens_r18: the X15 denominator drive fails as it must"
# ★ r34 (N4): one population (57) for the summaries over systems -- sens_r18 X17 (drive 19: the decorrelation
# summaries over all 60 again; sens_r28 S21 is in its --selftest, drive 17); R2-7 make_fig_context_v410 span print
# (drive 71: three figures, 31.2 MHz); R2-8/R2-19 covmed_r34 K1-K4 (drives 1-4) and priorsearch_r15 P1-P7
# (drives 1-8; 8 = the factor from the rounded union again).  Driven runs write scratch / _driveN only.
if ! drive_fired_rc 'X17 (r34).*FAIL' python3 sens_r18.py --drive 19; then
  echo "    ^^^ GATE FAILED: sens_r18 --drive 19 did NOT fail -- the population clause X17 is not demonstrated"
  GATEFAIL=$((GATEFAIL+1)); FAILED="$FAILED sens_r18_drive19"
fi
rm -f numbers/survey_numbers_round740_drive19.tex sens_r18_drive19.json
_o=$(python3 make_fig_context_v410.py --out "${TMPDIR:-/tmp}/ctxdrive71" --drive 71 2>&1); _rc=$?
if [ $_rc -eq 0 ] || ! printf '%s\n' "$_o" | grep -qE '^AssertionError: span: '; then
  echo "    ^^^ GATE FAILED: make_fig_context_v410 --drive 71 did NOT fire the span clause (rc $_rc)"
  GATEFAIL=$((GATEFAIL+1)); FAILED="$FAILED figctx_drive71"
fi
rm -rf "${TMPDIR:-/tmp}/ctxdrive71"
for d in 1:K1 2:K2 3:K3 4:K4; do
  if ! drive_fired_rc "^FAILED: ${d##*:} " python3 covmed_r34.py --drive ${d%%:*}; then
    echo "    ^^^ GATE FAILED: covmed_r34 --drive ${d%%:*} did NOT fail ${d##*:}"
    GATEFAIL=$((GATEFAIL+1)); FAILED="$FAILED covmed_r34_drive${d%%:*}"
  fi
  rm -f numbers/survey_numbers_round3460_drive${d%%:*}.tex covmed_r34_drive${d%%:*}.json
done
for d in 1:P1 2:P2 3:P3 4:P4 5:P5 6:P6 7:P2b 8:P7; do
  if ! drive_fired_rc "^FAILED: ${d##*:}\$" python3 priorsearch_r15.py --drive ${d%%:*}; then
    echo "    ^^^ GATE FAILED: priorsearch_r15 --drive ${d%%:*} did NOT fail ${d##*:}"
    GATEFAIL=$((GATEFAIL+1)); FAILED="$FAILED priorsearch_r15_drive${d%%:*}"
  fi
  rm -f numbers/survey_numbers_round600_drive${d%%:*}.tex
done
echo "r34 N4: sens_r18 X17, the span print, covmed_r34 K1-K4 and priorsearch_r15 P1-P7 drives fail as they must"
for d in 12 13; do
  if ! drive_fired_rc FAIL python3 r1_r22.py --drive $d; then
    echo "    ^^^ GATE FAILED: r1_r22 --drive $d did NOT fail -- the"
    echo "        cardinal/noun agreement clause A13 is no longer demonstrated"
    GATEFAIL=$((GATEFAIL+1)); FAILED="$FAILED r1_r22_drive$d"
  fi
  rm -f r1_r22_drive$d.json
done
echo "r1_r22: both A13 agreement drives fail as they must"

echo "--- the crossing accounting closes, and the prose keeps citing its terms (R1-1/R1-3) ---"
# ★★ R1-1 is answered by an ARITHMETIC IDENTITY IN PROSE between five macros
# from three unrelated generators, and nothing in the build evaluated it.
# Three of the five moved in the previous round.  Five checks, all driven;
# drives 1 and 2 each fire two clauses because A1/A2/A3 are three routes
# through the same counts -- stated in its docstring, not hidden.
g censusacct python3 censusacct_r17.py

echo "--- every included figure is legible, scaled 1 and reproducible (r17) ---"
# ★★★ Nothing in this build had ever measured what size a figure's labels
# print at.  Six of eleven were below 6 pt, and one had been emitted at the
# full text width and placed in a single column, which left its labels at half
# size in the printed paper for several versions.  G3 also catches the cause of
# a defect that is certain to recur: a generator run BY HAND does not inherit
# make_all.sh's `export SOURCE_DATE_EPOCH`, and four shipped figures carried a
# date the build could not reproduce.  Four clauses, all driven.
g figgate python3 figgate_r17.py

echo "--- no table prints below the type floor the figures are held to (r17) ---"
# ★★★ Same argument, for tables, and the worse defect of the two: Table 4 and
# the appendix table were set at `\tiny`, which prints at 5.0 pt -- two points
# below the body text and a point and a half below the floor the figures' axis
# numerals are on -- and unlike an axis numeral that is running prose a reader
# has to read.  `figgate` walks \includegraphics, so a table is invisible to
# it.  Builds the manuscript twice in a scratch directory and writes nothing in
# the tree.  ★ Its COUNT clause knew only `table`/`table*` and went blind the
# moment the ledger became landscape -- 12/12 passing while measuring nothing;
# it now cross-checks the `\@writefile{lot}` lines the document writes itself.
# Seven drives, all demonstrated.
g tabfloor python3 tabfloor_r17.py . "${TMPDIR:-/tmp}/tabfloor_r17"

echo "--- the landscape float is on the page, not over its edge (r18) ---"
# ★★★★ THE DEFECT THIS CATCHES REACHED A SHIPPED PDF AND SIX CONSECUTIVE
# PASSES OF THIS SUITE.  `rotating` centres a sideways double float in \hsize,
# which this revtex-derived class leaves at the COLUMN width, so the crossing
# ledger was centred on column one: its caption began at x = -5.9 pt, off the
# left edge of the paper, with words missing from every line.  Rotation hides
# that from `Overfull \hbox`, so the log was clean and every gate passed.
# Measured here as ink against the text block, with the block itself measured
# from the upright pages rather than typed.  Three clauses, three drives, each
# demonstrated to fail; and the gate fails on the previous build's own PDF,
# which is the only proof that matters.
g rotfit python3 rotfit_r18.py

echo "--- no float is too large for its page, and no ink is off the paper (r18) ---"
# ★★★★ TWO OF THESE FIRED ON EVERY BUILD OF v4.19 AND NO GATE LOOKED.
# `LaTeX Warning: Float too large for page by X pt` is not an overfull box, so
# `latexlog` -- which Glenn's overlapping table turned into a build failure --
# never saw it: Table 3 overran its column by 54.38 pt and Table A2 by
# 21.94 pt, and in the PDF the first was ink down to y = 788.3 pt on a 792 pt
# page, 3.7 pt from the physical edge of the paper.  Table 3 is now a
# full-width float whose tabular is set to the full width, and Table A2's
# caption no longer carries the per-system paragraph, so both warnings are
# gone; this gate is what stops the next one shipping.  F2 measures ink as
# PIXELS against the media box, because every figure here is a Form XObject
# that the object model reports nothing useful about.  Three clauses, three
# drives, each demonstrated to fail -- and it fails on the build this round
# started from, which is the only proof that counts.
g floatfit python3 floatfit_r18.py

echo "--- every caption is inside the author's limit, in PRINTED LINES (r25) ---"
# ★★★★ ADDED v4.26.  THIS WAS THE ONE UNGUARDED CONSTRAINT IN A 38-GATE BUILD,
# and it was the author's most explicit and most often repeated instruction:
# "The table captions are too long -- they should be no more than about 3
# lines ... If you need the extra text, it has to go into the main paper ...
# but it cannot stay as it is", with eleven tables named by hand.  Round 25
# shortened them, verified the result IN CHARACTERS, and handed back a build
# with three of those eleven at 16, 16 and 15 printed lines and two of
# fourteen table captions inside the limit.  A character count cannot express
# a limit stated in lines, any more than a source-line count can express a
# page budget -- the same species of error, one round apart.
# ★ `capmeasure.py` counts DISTINCT BASELINES on the built page, so a
# justified line the extractor splits at a wide gap and a line split at an
# inline font change each count once.  It pins THE LIMIT and never today's
# counts; an over-length caption must be named in `capmeasure_allow.txt`
# WITH A WRITTEN REASON, and an allowance for a caption that is now inside
# the limit is itself a failure, so the allow list cannot become a licence.
# ★ Driven: `--selfdrive` measures against a limit of zero, which every
# caption must exceed, so a gate that had gone vacuous cannot pass.
g capmeasure python3 capmeasure.py
g capmeasure_drive python3 capmeasure.py --selfdrive

echo "--- no file reads another version directory by an unguarded path (r22) ---"
# ★★★ ADDED v4.23.  Round 20 broke the build by deleting a version folder a
# generator read by absolute path, and round 22 found ten such pins still in
# the tree -- four unguarded and NOT ONE VISIBLE TO ANY GATE, because
# `cleanregen.py` cannot see a cross-version dependency (the predecessor is
# always there while it runs).  `verpin.py` reports every pin, requires each
# to carry the existence-fallback pattern, and fails on a pin into a
# directory that no longer exists.  Its own `--selftest` writes three
# throwaway files and requires the two defective ones to be caught.
g verpinself python3 verpin.py --selftest
g verpin python3 verpin.py
echo "--- a hyphen may not be typeset where a minus sign belongs (r17) ---"
# ★★ WIRED NOW THAT THE FIX HAS LANDED, AND NOT BEFORE.  The gate measured 65
# hyphen-before-digit against 47 true minus signs on seven pages, and its
# author deliberately kept it out of the suite: a gate that is red from the
# moment it lands gets whitelisted, and this tree already carries twenty-plus
# dead gates from exactly that.  The glyph is now emitted as \ensuremath{-} by
# the six generators that produced all 65 -- `ledger_v410.py`,
# `holdout_v412.py`, `recurnull_v413.py`, `masklsr_v520.py`, `bookkeep_r13.py`
# and `flare_v404.py` -- applied at each one's EMIT step, so no use site
# changed and no value moved.  The PDF scan is the verdict; the source scan
# localises and reports round files whose macros are only ever used inside
# `$...$`, which is why its count is larger and is not the failure criterion.
g minuscheck python3 minuscheck.py
g fieldcover python3 fieldcover_r27.py   # row 55: every census window searched over every in-beam FIELD row of its pointing, or declared
echo "--- the LaTeX log is a gate too (v4.11) ---"
g latexlog python3 - "$V" <<'PYEOF'
import re, sys
log = open(sys.argv[1] + '.log', errors='ignore').read()
err = re.findall(r'^! .*', log, re.M)
und = len(re.findall(r'Undefined control sequence', log))
ref = len(re.findall(r'Warning: (?:Reference|Citation)', log))
mul = len(re.findall(r'multiply defined', log))
# ★★★ GLENN, 2026-10-06: "the bottom of Table 9 on Page 25 overlaps with
# text -- this must be adjusted."  It did, and this suite could not see it.
# A float too tall for its page is an `Overfull \vbox`, which pdflatex
# reports as a WARNING and after which the build succeeds; v4.12 shipped two
# of them and they were judged cosmetic at 0.8 pt of ink.  They were not
# cosmetic: they were a table written over the paragraph beneath it, which
# is the first thing a reader sees and which says the paper was never looked
# at.  An overfull box of EITHER kind is now a build failure.  ★ The cure for
# a tall float belongs in the generator that writes it -- `ledger_v410.py`
# emits the crossing ledger in parts of at most 28 rows -- and not in a
# \vspace here; this gate exists so that the next one cannot ship.
# ★ `Float too large for page` is NOT an overfull box and is not checked
# here: it has its own gate, `floatfit_r18.py`, which also measures the ink.
# Do not re-add it in this clause -- two gates for one defect, one of which
# only prints, is how a warning gets read as a note.
vb = re.findall(r'Overfull \\vbox[^\n]*', log)
hb = re.findall(r'Overfull \\hbox[^\n]*', log)
print('latexlog: %d error(s), %d undefined control sequence(s), %d '
      'unresolved reference/citation warning(s), %d multiply defined, '
      '%d overfull vbox, %d overfull hbox'
      % (len(err), und, ref, mul, len(vb), len(hb)))
for e in err[:6]:
    print('   ', e)
for w in (vb + hb)[:10]:
    print('    OVERFULL', w)
sys.exit(1 if (err or und or ref or mul or vb or hb) else 0)
PYEOF

echo "--- the arXiv set carries no refereeing, round or version vocabulary (row 41) ---"
# arXiv publishes the LaTeX source.  `arxivset.sh` strips comments from every
# .tex it packages, but the ancillary files and style files go up verbatim and
# nothing scanned them; prosegate_selfref reads only the typeset page.  This
# builds the set exactly as uploaded and reads every file in it, comments
# included.  Drives 1 and 2 plant a vocabulary line in a copy of the set (a
# .tex and an ancillary file) and must each fail.
bash arxivset.sh "${TMPDIR:-/tmp}/avset" --force > "${TMPDIR:-/tmp}/avset.log" 2>&1
g arxivset_build bash -c "tail -1 '${TMPDIR:-/tmp}/avset.log' >/dev/null; [ -s '${TMPDIR:-/tmp}/avset/ms.tex' ]"
g arxivvocab python3 arxivvocab_r27.py --set "${TMPDIR:-/tmp}/avset"
for d in 1 2; do
  # arxivvocab reports a firing as "N hit(s)" with N > 0, not as FAIL.
  g arxivvocab_drive$d drive_fired_rc '[1-9][0-9]* hit(s)' python3 arxivvocab_r27.py --set "${TMPDIR:-/tmp}/avset" --drive $d
done

echo "--- one stellar-frame mask predicate (frameconv_gate) ---"
# The +-50 km/s mask is applied in the star's own frame by ONE predicate
# in maskframe_v411; this gate fails if any other file compares a
# sky-frame offset with the mask half-width, if any census or hold-out
# crossing's recorded verdict disagrees with its own frame chain, and if
# the comparison has become unable to fail (G3).
g frameconv python3 frameconv_gate.py --tree .

echo "--- the macro layer lives in numbers/ (numbers_check, Ruling R25) ---"
# ★ v4.29: survey_numbers*.tex moved from chain/ into chain/numbers/ by
# numbers_move.py (chain/ was at 1,009 entries; GitHub lists 1,000).  After the
# move nothing else would notice a macro file written at the build root by a
# generator written the old way (TeX reads the numbers/ copy; every repointed
# reader ignores the stray).  This gate is numbers_move.py itself, run as a dry
# run: it must find nothing to move, nothing to repoint, nothing it cannot
# classify.  Drive 1: a macro file at the root; drive 2: a generator writing one.
# r33 (round-32 R1-3 / R1-5, rankcharge_r33 + extrap_r33): every new clause driven to fail on its own.
# rankcharge_r33 drives write rankcharge_r33_driveN.json only (removed below); persys_r17 --drive and
# r1_r22 --drive write nothing a build reads (r1_r22_drive15.json removed).
for _d in 1:RC1 2:RC2 3:RC3 4:RC4 5:RC5 6:RC6 7:RC7 8:RC8 9:RC9 10:RC10 11:NG1 12:NG2 13:NG3 14:NG4 15:RC11; do
  if ! drive_fired_rc "^FAILED: .*${_d##*:}\b" python3 rankcharge_r33.py --drive ${_d%%:*}; then
    echo "    ^^^ GATE FAILED: rankcharge_r33 --drive ${_d%%:*} did NOT fail on ${_d##*:}"
    GATEFAIL=$((GATEFAIL+1)); FAILED="$FAILED rankcharge_drive${_d%%:*}"
  fi
  rm -f rankcharge_r33_drive${_d%%:*}.json
done
if ! drive_fired_rc '^FAILED: P12 ' python3 persys_r17.py --drive 12; then
  echo "    ^^^ GATE FAILED: persys_r17 --drive 12 did NOT fail -- the Table F1 pilcrow clause P12"
  GATEFAIL=$((GATEFAIL+1)); FAILED="$FAILED persys_drive12"
fi
if ! drive_fired_rc 'A14 .*FAIL' python3 r1_r22.py --drive 15; then
  echo "    ^^^ GATE FAILED: r1_r22 --drive 15 did NOT fail -- the extrap_r33 agreement clause A14"
  GATEFAIL=$((GATEFAIL+1)); FAILED="$FAILED r1_r22_drive15"
fi
rm -f r1_r22_drive15.json
echo "r33: rankcharge_r33 (14), persys_r17 P12 and r1_r22 A14 drives fail as they must"
g numbers_check python3 numbers_check.py --check
for d in 1 2; do
  g numbers_check_drive$d drive_fired_rc 'numbers_check: FAIL' python3 numbers_check.py --check --drive $d
done
# toplevel --check also fails when chain/ holds >= 1,000 pushed entries; the
# drive lowers the limit below the tree's own count, so it must fire.
g toplevel_chainmax_drive drive_fired_rc 'pushed entries, at or above' python3 toplevel.py --check --chain-max 100

# ★★ v4.28 (r27-slim): THE TOP LEVEL IS OWNED BY THE CHAIN.  The build lives in
# chain/ and the version directory's top level shows the PDF and the deposit as
# COPIES.  A copy that can drift is the defect the re-root fixed (the file a
# reader sees must be the file the paper is), so the copies are written here,
# as the last step that can change the PDF, and then checked byte for byte --
# with the four wrappers and the README -- by a gate that is driven both ways.
# In a flat tree both lines say so and pass.
python3 toplevel.py --sync
g toplevel_self python3 toplevel.py --selftest
g toplevel python3 toplevel.py --check
echo "==========================================================="
if [ $GATEFAIL -eq 0 ]; then
  echo "gate.sh: ALL GATES PASS"
else
  echo "gate.sh: $GATEFAIL GATE(S) FAILED:$FAILED"
fi
exit $GATEFAIL
