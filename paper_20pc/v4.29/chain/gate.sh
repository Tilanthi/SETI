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
for d in 1 2 3 4 5 6 7 8 9 10 11 12 13 14 15; do
  if ! drive_fired_rc FAIL python3 absreq_r17.py --drive $d; then
    echo "    ^^^ GATE FAILED: absreq_r17 --drive $d did NOT fail -- the"
    echo "        clause it exercises is no longer demonstrated"
    GATEFAIL=$((GATEFAIL+1)); FAILED="$FAILED absreq_drive$d"
  fi
done
echo "absreq_r17: all 15 drives fail as they must"
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
# r28 (integrate, note 2): A27 binds Appendix D.1's two direction sentences
# ("conclusion unchanged", "every ratio measured is an excess") to the values
# they read.  Drive 36 moves both across their verdicts; A27 must fail.
if ! drive_fired "^FAILED: .*A27" python3 chance_v414.py --drive 36; then
  echo "    ^^^ GATE FAILED: chance_v414 --drive 36 did NOT fail A27"
  GATEFAIL=$((GATEFAIL+1)); FAILED="$FAILED chance_v414_drive36"
fi
rm -f numbers/survey_numbers_round310_drive36.tex chance_v414_drive36.json \
      chance_perwin_v422_drive36.json
echo "chance_v414: the A27 direction drive fails as it must"
# r28 (integrate, note 7): orbit_r18 K1 -- App. C's Keplerian speed is computed
# at the mass ceiling and must lie inside the mask half-width it justifies.
if ! drive_fired "^FAILED: .*K1" python3 orbit_r18.py --drive 8; then
  echo "    ^^^ GATE FAILED: orbit_r18 --drive 8 did NOT fail K1"
  GATEFAIL=$((GATEFAIL+1)); FAILED="$FAILED orbit_r18_drive8"
fi
rm -f numbers/survey_numbers_round803_drive8.tex orbit_r18_drive8.json
echo "orbit_r18: the K1 drive fails as it must"
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
for d in 16; do
  if ! drive_fired_rc FAIL python3 sens_r18.py --drive $d; then
    echo "    ^^^ GATE FAILED: sens_r18 --drive $d did NOT fail -- the"
    echo "        denominator clause X15 is no longer demonstrated"
    GATEFAIL=$((GATEFAIL+1)); FAILED="$FAILED sens_r18_drive$d"
  fi
  rm -f numbers/survey_numbers_round740_drive$d.tex sens_r18_drive$d.json
done
echo "sens_r18: the X15 denominator drive fails as it must"
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
