#!/bin/bash
# arxivset.sh [DEST] -- assemble the arXiv submission set and PROVE it.
#
# ★★★ WHAT THIS IS FOR.  The journal is an arXiv overlay: the published
# article IS the arXiv PDF, built by arXiv from the source we upload, in a
# directory that contains nothing but what we uploaded.  So the only
# meaningful test of a submission is a build in an empty directory from
# nothing but the submission set, and a byte comparison against the build in
# the working tree.  A submission that only builds in its author's working
# directory is not a submission -- and this project has shipped generators
# that were in no build script, which only a clean checkout exposes.
#
# ★★ WHAT IT CHECKS, each one a real arXiv rule rather than folklore:
#   1  (La)TeX source, not PDF-only                         -- by construction
#   2  every \input/\include resolved, recursively           -- A1
#   3  every \includegraphics file present                   -- A2
#   4  all figures PDF/PNG/JPG, NO EPS mixed in under pdflatex -- A3
#   5  no absolute figure path, no `..` escape                -- A4
#   6  filenames restricted to a-zA-Z0-9_+-.,= and unique case-insensitively
#                                                            -- A5, A6
#   7  nothing the build needs left outside the set           -- the clean build
#   8  no file in the set the build does not need             -- A7
#   9  no .aux/.log/.pdf or other build product in the set     -- A9
#  10  exactly one \documentclass, so the top-level file is unambiguous -- A10
#  11  no hidden file (arXiv DELETES dotfiles on announcement) -- A11
#  12  no JavaScript or embedded action in any figure (auto-reject) -- A12
#  13  the clean-directory PDF is byte-identical to the in-tree PDF -- A8
#  14  the machine-readable tables the text promises are in anc/, are not TeX,
#      and are not part of the article                          -- A13
#
# ★ THREE arXiv RULES THAT ARE EASY TO GET BACKWARDS, so they are recorded
# here rather than guessed at again:
#   - `\pdfoutput=1` is NOT to be added.  arXiv recognises pdflatex
#     automatically and says plainly "you should not use \pdfoutput to change
#     the output format".  Old advice said the opposite.
#   - `xr`/`\externaldocument` is advised against outright: file locations
#     differ on their servers and cross-document links are lost.  The paper
#     used to load `xr` in its split build; it no longer does.
#   - `\today` is advised against because arXiv occasionally rebuilds the PDF
#     and the date would change.  `openjournal.cls` sets `\submitted{Version
#     \today}`; the manuscript empties it, so nothing dated is typeset.
#
# ★ The tarball is written BEFORE the build, so it can never contain the
# .aux/.log/.pdf the build leaves behind.  arXiv strips those anyway, but a
# submission one cannot inspect is a submission one cannot check.
#
# ★ The .tex files are copied COMMENT-STRIPPED.  arXiv serves the source
# bundle publicly, so every comment in it is published too, and this tree's
# comments are a working record rather than anything a reader should see.
# Stripping is byte-safe and is proved to be: a whole-line comment typesets
# nothing, and a trailing comment truncated to its bare `%' still eats the
# newline exactly as before.  Check A8 is what makes that a proof rather than
# a claim -- if the strip changed one space the PDF would differ.
#
# Usage:  bash arxivset.sh [DEST] [--force]
#         default DEST=${TMPDIR:-/tmp}/arxivset
set -u
cd "$(dirname "$0")"
SRC=$(pwd)
export SOURCE_DATE_EPOCH=1577836800
export FORCE_SOURCE_DATE=1
: "${TMPDIR:=/tmp}"
export TMPDIR
D=${1:-$TMPDIR/arxivset}
FORCE=no
for a in "$@"; do [ "$a" = "--force" ] && FORCE=yes; done
[ "$D" = "--force" ] && D=$TMPDIR/arxivset

STEM=$(ls technosignatures_*.tex 2>/dev/null | sed 's/\.tex$//')
[ "$(printf '%s\n' "$STEM" | wc -l)" = 1 ] && [ -n "$STEM" ] || {
  echo "A0 FAIL: expected exactly one technosignatures_*.tex here, found:" >&2
  printf '%s\n' "$STEM" >&2; exit 2; }

# ★★ A7: THE DESTINATION.  This script's third line used to be an
# unconditional `rm -rf "$D"`, and `$D` is the first argument -- so
# `bash arxivset.sh .` would have deleted the manuscript.  Refuse a
# destination that is the source tree, or contains it, or is inside it, and
# refuse a non-empty one unless --force.  Assembling into a directory that
# already holds files is how a build product reaches a submission.
DA=$(cd "$(dirname "$D")" 2>/dev/null && pwd)/$(basename "$D")
case "$SRC/" in "$DA"/*) echo "A7 FAIL: $DA contains the source tree" >&2
                         exit 2;; esac
case "$DA/" in "$SRC"/*) echo "A7 FAIL: $DA is inside the source tree" >&2
                         exit 2;; esac
[ "$DA" = "$SRC" ] && { echo "A7 FAIL: destination is the source tree" >&2
                        exit 2; }
if [ -e "$DA" ] && [ -n "$(ls -A "$DA" 2>/dev/null)" ]; then
  [ "$FORCE" = yes ] || {
    echo "A7 FAIL: $DA exists and is not empty." >&2
    echo "         Assembling over existing files is how a build product" >&2
    echo "         reaches a submission.  Re-run with --force to clear it." >&2
    exit 2; }
fi
rm -rf "$DA"; mkdir -p "$DA"; D=$DA
python3 - "$SRC" "$D" "$STEM" <<'PY' || exit 1
import os, re, shutil, string, sys

src, dest, stem = sys.argv[1], sys.argv[2], sys.argv[3]
fails, notes = [], []

# ---------------------------------------------------------------- strip
def strip_comments(text):
    """Remove LaTeX comments without changing one byte of output.

    A line whose first non-blank character is `%` typesets nothing at all --
    TeX skips the leading spaces and the `%` eats the rest of the line
    including its newline -- so the whole line goes.  A trailing comment is
    truncated to its bare `%`, which still eats the newline, so the spacing
    either side is untouched.  `\\%` is a printed per-cent sign and must
    survive; `\\\\%` is a line break followed by a comment and must not take
    the `%` with it.  Check A8 proves the result.
    """
    out = []
    for line in text.split('\n'):
        cut = None
        i, n = 0, len(line)
        while i < n:
            c = line[i]
            if c == '\\':
                i += 2          # skip the escaped character, whatever it is
                continue
            if c == '%':
                cut = i
                break
            i += 1
        if cut is None:
            out.append(line)
        elif line[:cut].strip() == '':
            continue            # whole-line comment: emit nothing
        else:
            out.append(line[:cut + 1])
    return '\n'.join(out)

# ------------------------------------------------- A1: the .tex closure
def decomment(t):
    return strip_comments(t)

order, queue, missing = [], [stem + '.tex'], []
while queue:
    f = queue.pop(0)
    if f in order or f in missing:
        continue
    p = os.path.join(src, f)
    if not os.path.isfile(p):
        missing.append(f)
        continue
    order.append(f)
    body = decomment(open(p, errors='ignore').read())
    for t in re.findall(r'\\(?:input|include)\s*\{([^}]*)\}', body):
        queue.append(t if t.endswith('.tex') else t + '.tex')
if missing:
    fails.append('A1 unresolved \\input/\\include: %s' % missing)

# ------------------------------------------------ A2/A3/A4: the figures
figs = {}
for f in order:
    body = decomment(open(os.path.join(src, f), errors='ignore').read())
    for m in re.finditer(r'\\includegraphics\s*(?:\[[^\]]*\])?\s*\{([^}]*)\}',
                         body):
        figs.setdefault(m.group(1), []).append(f)
OK_EXT = ('.pdf', '.png', '.jpg', '.jpeg')
figfiles = []
for g, where in sorted(figs.items()):
    if g.startswith('/'):
        fails.append('A4 absolute figure path: %s (%s)' % (g, where[0]))
        continue
    if '..' in g.split('/'):
        fails.append('A4 figure path escapes the tree: %s' % g)
        continue
    cands = [g] if os.path.splitext(g)[1] else [g + e for e in OK_EXT]
    hit = next((c for c in cands if os.path.isfile(os.path.join(src, c))), None)
    if hit is None:
        fails.append('A2 figure not found: %s (%s)' % (g, where[0]))
        continue
    if os.path.splitext(hit)[1].lower() not in OK_EXT:
        fails.append('A3 figure is not PDF/PNG/JPG: %s' % hit)
    figfiles.append(hit)
    if not os.path.splitext(g)[1]:
        notes.append('A3 extensionless \\includegraphics{%s} resolved to %s'
                     % (g, hit))
eps = [f for f in figfiles if f.lower().endswith(('.eps', '.ps'))]
if eps:
    fails.append('A3 EPS mixed into a pdflatex submission: %s' % eps)

# ---------------------------------------------- the class and style files
cls = ['openjournal.cls']
sty = []
clstxt = open(os.path.join(src, cls[0]), errors='ignore').read()
for m in re.finditer(r'\\RequirePackage(?:\[[^\]]*\])?\{([^}]*)\}', clstxt):
    for name in (x.strip() for x in m.group(1).split(',')):
        if os.path.isfile(os.path.join(src, name + '.sty')):
            sty.append(name + '.sty')
sty = sorted(set(sty))
notes.append('class requires a local .sty: %s' % (sty or 'none'))

# ------------------------------------------- A13: the ANCILLARY files (anc/)
# ★★★ arXiv's own mechanism for "raw data for tables and plots in the article"
# (info.arxiv.org/help/ancillary_files.html): files placed in a directory
# `anc` at the root of the submission package.  They are served beside the
# article, are NOT refereed and are NOT part of it, and they are the answer to
# referee 2's minor 11 at a journal that hosts no supporting information of
# its own.  Two rules from that page are checked here because breaking either
# is silent: TeX files may not go in `anc`, and an ancillary file is stored
# with one version of the article and cannot be changed independently of it --
# so it must be a product of THIS build and not a file left lying about.
# ★★ AND THE CHECK IS TWO-SIDED, like prose_v412's bandwidth clause: if the
# paper's data-availability statement promises ancillary files, the set must
# carry them; if the set carries them, the paper must say what they are.  A
# promise without a file and a file without a promise are both defects, and
# only the pair of them can be checked here.
# ★ v4.21, r20-final: `si_counts.txt` joins the two.  The article now prints
# the accounting rows of the master count table and the itemisation is in this
# file, written by the same generator that writes the table (its A14 pins the
# two together), so the promise and the file remain one object.
# ★ v4.22: `si_recur.txt` (every crossing's exclusion depth read over
# separated blocks alone and over the matched registration tolerance) and
# `si_recovery.txt` (the probability a carrier at the trigger amplitude
# would have satisfied the recurrence criterion) join the three.
ANC_SRC = ['si_catalogue.txt', 'si_counts.txt', 'si_ledger.txt',
           'si_recur.txt', 'si_recovery.txt']
anc = []
flat_src = ''.join(open(os.path.join(src, f), errors='ignore').read()
                   for f in order)
_promised = 'ancillary file' in flat_src
for a in ANC_SRC:
    p = os.path.join(src, a)
    if not os.path.isfile(p) or os.path.getsize(p) == 0:
        fails.append('A13 declared ancillary file missing or empty: %s' % a)
        continue
    if a.endswith(('.tex', '.sty', '.cls', '.bbl')):
        fails.append('A13 TeX source may not go in anc/ (arXiv rule): %s' % a)
        continue
    if os.path.basename(a) in flat_src:
        fails.append('A13 %s is referenced by the build, so it is part of the '
                     'article and not ancillary' % a)
        continue
    anc.append('anc/' + a)
if anc and not _promised:
    fails.append('A13 the set carries ancillary files %s but the manuscript '
                 'never says so' % anc)
if _promised and not anc:
    fails.append('A13 the manuscript promises ancillary files and the set '
                 'carries none')
notes.append('ancillary files in anc/: %s (promised in the text: %s)'
             % ([os.path.basename(a) for a in anc] or 'none', _promised))

# ----------------------------------------------- A15: a NEUTRAL package
# ★★★★ v4.25.  The author's constraint is that nothing -- "prose, caption,
# table, figure, printed comment, PDF metadata, arXiv source" -- may mention
# versions, edits, referees, rounds or corrections, and arXiv publishes the
# SOURCE: it lists every filename and serves every byte.  Measured on the set
# this script built before this clause existed: 194 of the 222 `.tex` carried
# a version or round string IN THEIR NAMES, 180 of them the literal word
# `round` (`survey_numbers_round8.tex` ... `survey_numbers_round200.tex`), and
# the top-level source carried 188 lines of the form
# `\input{survey_numbers_round23}`, which is published source TEXT.  No sweep
# in this build could see any of it: `round` inside `round23` has no word
# boundary, so the forbidden-mention regex missed every one.
#
# ★★ The names stay as they are IN THE REPOSITORY -- they are the build's
# audit trail, every generator is keyed to the file it writes, and renaming
# them there would destroy the one record of which round produced which
# number.  The fix belongs HERE, in the packaging step, and nowhere else.
#
# ★ The macro files are inlined into ONE `numbers.tex`, which is provably
# safe rather than hopefully safe: they are the manuscript's PREAMBLE inputs,
# they occupy a contiguous run of the preamble (asserted below -- not one
# non-comment, non-blank, non-input line falls between the first and the
# last), and definition order is preserved by concatenating them in closure
# order.  Everything else is renamed by stripping the version token, and the
# `\input` lines are rewritten to match.  A8's byte comparison is what proves
# the rewrite changed nothing: the clean build of the renamed, inlined package
# must produce the same PDF, to the byte, as the working tree's.
VTOK = re.compile(r'_v\d+(?:\.\d+)*|_round\d+|_r\d+(?=$|_)', re.I)
LEAK = re.compile(r'_v\d|_round\d|_r\d\d|v\d+\.\d+|round\s?\d|referee'
                  r'|revision', re.I)

main_txt = decomment(open(os.path.join(src, stem + '.tex'),
                          errors='ignore').read())
_bd = main_txt.find('\\begin{document}')
_pre = main_txt[:_bd if _bd >= 0 else len(main_txt)]
_inp = re.compile(r'\\(?:input|include)\s*\{([^}]*)\}')
numbers = [t if t.endswith('.tex') else t + '.tex'
           for t in _inp.findall(_pre)]
# the contiguity assertion: between the first and last preamble \input there
# must be nothing but \input lines and blank lines (comments are gone).
_pl = _pre.split('\n')
_at = [i for i, l in enumerate(_pl) if _inp.search(l)]
_gap = ([l for l in _pl[_at[0]:_at[-1] + 1]
         if l.strip() and not _inp.search(l)] if _at else [])
if _gap:
    fails.append('A15 the preamble \\input run is not contiguous (%d line(s) '
                 'between the first and the last, e.g. %r) -- inlining the '
                 'macro layer would move code, so it is refused'
                 % (len(_gap), _gap[0][:60]))
    numbers = []
numset = set(numbers)

# DEST name for every item.  Numbers files all collapse to one; the top-level
# manuscript loses its version; everything else loses its version token.
NEUTRAL_STEM = 'ms'
name = {}
for f in order:
    if f in numset:
        name[f] = 'numbers.tex'
    elif f == stem + '.tex':
        name[f] = NEUTRAL_STEM + '.tex'
    else:
        _d, _b = os.path.split(f)
        _root, _ext = os.path.splitext(_b)
        name[f] = os.path.join(_d, VTOK.sub('', _root) + _ext)
_rev = {}
for f in order:
    _rev.setdefault(name[f], []).append(f)
for n, fs in _rev.items():
    if n != 'numbers.tex' and len(fs) > 1:
        fails.append('A15 two source files map to one package name %s: %s'
                     % (n, sorted(fs)))
# the \input target a rewritten file must name, without the .tex
tgtname = {f: os.path.splitext(name[f])[0] for f in order}


# ★ Figures carry the same stems.  One of the eleven is `chain_v412.pdf`, and
# an `\includegraphics` target is published source text exactly as an `\input`
# target is, so the figure files are renamed in the package too and every
# reference to them rewritten.  The map is on the TARGET AS WRITTEN, because
# the source writes some of them without an extension and A3 resolves those.
figmap = {}            # package path for each source figure file
figtgt = {}            # package \includegraphics target for each raw target
for _g in figs:
    _d, _b = os.path.split(_g)
    _root, _ext = os.path.splitext(_b)
    figtgt[_g] = os.path.join(_d, VTOK.sub('', _root) + _ext)
for _f in figfiles:
    _d, _b = os.path.split(_f)
    _root, _ext = os.path.splitext(_b)
    figmap[_f] = os.path.join(_d, VTOK.sub('', _root) + _ext)
_fr = {}
for _f, _n in figmap.items():
    _fr.setdefault(_n, []).append(_f)
for _n, _fs in _fr.items():
    if len(_fs) > 1:
        fails.append('A15 two figures map to one package name %s: %s'
                     % (_n, sorted(_fs)))
_GRAPH = re.compile(r'(\\includegraphics\s*(?:\[[^\]]*\])?\s*\{)([^}]*)(\})')


def rewrite_graphics(text):
    return _GRAPH.sub(lambda m: m.group(1) + figtgt.get(m.group(2),
                                                        m.group(2))
                      + m.group(3), text)


def rewrite_inputs(text):
    r"""Rewrite this file's \input targets to their package names.  The first
    numbers input in a file becomes `\input{numbers}`; the rest are dropped,
    because one `\newcommand` seen twice is an error, not a no-op."""
    seen = {'n': False}

    def sub(m):
        t = m.group(1)
        k = t if t.endswith('.tex') else t + '.tex'
        if k in numset:
            if seen['n']:
                return ''
            seen['n'] = True
            return '\\input{numbers}'
        return '\\input{%s}' % tgtname.get(k, t)
    return _inp.sub(sub, text)


# ------------------------------------------------------------ copy it all
_pkg = [name[f] for f in order]
_texitems = list(dict.fromkeys(_pkg))
items = _texitems + cls + sty + [figmap[f] for f in figfiles] + anc
for f in order:
    tgt = os.path.join(dest, name[f])
    os.makedirs(os.path.dirname(tgt) or dest, exist_ok=True)
    body = rewrite_graphics(rewrite_inputs(strip_comments(
        open(os.path.join(src, f), errors='ignore').read())))
    if f in numset:
        with open(tgt, 'a') as fh:      # appended in closure order
            fh.write(body if body.endswith('\n') else body + '\n')
    else:
        open(tgt, 'w').write(body)
for f in figfiles:
    tgt = os.path.join(dest, figmap[f])
    os.makedirs(os.path.dirname(tgt) or dest, exist_ok=True)
    shutil.copy(os.path.join(src, f), tgt)
for f in cls + sty + anc:
    tgt = os.path.join(dest, f)
    os.makedirs(os.path.dirname(tgt) or dest, exist_ok=True)
    if f.startswith('anc/'):
        # ★ copied verbatim: an ancillary file is served exactly as supplied,
        # and its own header is the column description a reader gets.
        shutil.copy(os.path.join(src, f[len('anc/'):]), tgt)
    else:
        shutil.copy(os.path.join(src, f), tgt)
notes.append('A15 %d macro file(s) inlined into numbers.tex; %d other .tex '
             'renamed; top level %s.tex -> %s.tex'
             % (len(numbers),
                sum(1 for f in order if f not in numset and name[f] != f),
                stem, NEUTRAL_STEM))

# ★★★ A15b: PRUNE THE DEAD MACRO LAYER FROM THE PACKAGE.  Of the macro
# definitions the inlined `numbers.tex` carries, 4,428 of 6,020 are used
# NOWHERE in the submission -- not in the prose, not in a table, not inside
# another macro's body -- and three of them hold internal file versions as
# their VALUES (`vistest_v385.json`, `per_target_results_v3.84.csv`, `3.99`).
# A definition nothing expands cannot change one byte of output, so dropping
# it is provably safe rather than hopefully safe, and A8's byte comparison is
# the proof: the clean build of the pruned package must still equal the
# working tree's PDF exactly.
# ★ Dropped in chunks, not in lines, because `\DeclareRobustCommand` bodies
# run over several lines; iterated to a fixed point, because dropping one
# body can orphan the macro it used; and refused outright if the package
# builds any control-sequence name with `\csname`, where a textual use count
# would be a lie.
_csname = sum(open(os.path.join(dest, f), errors='ignore').read()
              .count('\\csname') for f in items if f.endswith('.tex'))
_numpath = os.path.join(dest, 'numbers.tex')
if numbers and _csname == 0 and os.path.exists(_numpath):
    _DEFH = re.compile(r'\\(?:newcommand|renewcommand|providecommand'
                       r'|DeclareRobustCommand)\s*\{?\\([A-Za-z]+)\}?')
    _CS = re.compile(r'\\([A-Za-z]+)')
    _others = [os.path.join(dest, f) for f in items
               if f.endswith('.tex') and f != 'numbers.tex']
    _otext = ''.join(open(p, errors='ignore').read() for p in _others)
    _num = open(_numpath, errors='ignore').read()
    _dropped, _rounds = 0, 0
    while True:
        _rounds += 1
        # split into chunks, each beginning at a definition head
        _at = [m.start() for m in _DEFH.finditer(_num)]
        if not _at:
            break
        _chunks = [(None, _num[:_at[0]])]
        for _i, _s in enumerate(_at):
            _e = _at[_i + 1] if _i + 1 < len(_at) else len(_num)
            _chunks.append((_DEFH.match(_num, _s).group(1), _num[_s:_e]))
        # use count over the whole package, minus each chunk's own head
        _use = {}
        for _n in _CS.findall(_otext):
            _use[_n] = _use.get(_n, 0) + 1
        for _n in _CS.findall(_num):
            _use[_n] = _use.get(_n, 0) + 1
        for _n, _c in _chunks:
            if _n is not None:
                _use[_n] = _use.get(_n, 0) - 1      # its own definition head
        _keep = [(n, c) for n, c in _chunks
                 if n is None or _use.get(n, 0) > 0]
        if len(_keep) == len(_chunks):
            break
        _dropped += len(_chunks) - len(_keep)
        _num = ''.join(c for _, c in _keep)
    open(_numpath, 'w').write(_num)
    notes.append('A15b %d dead macro definition(s) pruned from numbers.tex '
                 'in %d pass(es); %d definition(s) remain'
                 % (_dropped, _rounds, len(_DEFH.findall(_num))))
elif numbers:
    notes.append('A15b prune REFUSED: %d \\csname use(s) in the package, so a '
                 'textual use count is not a use count' % _csname)

# A15, the proof rather than the intention: no package PATH, no \input target,
# no \includegraphics target and no surviving macro VALUE inside the package
# may carry a version, round or referee string.
for f in items:
    if LEAK.search(f):
        fails.append('A15 package filename carries an internal string: %s' % f)
for f in items:
    if not f.endswith('.tex'):
        continue
    txt = open(os.path.join(dest, f), errors='ignore').read()
    for t in _inp.findall(txt):
        if LEAK.search(t):
            fails.append('A15 %s still inputs %s' % (f, t))
    for m in re.finditer(r'\\includegraphics\s*(?:\[[^\]]*\])?\s*\{([^}]*)\}',
                         txt):
        if LEAK.search(m.group(1)):
            fails.append('A15 %s still includes %s' % (f, m.group(1)))
    # ★ and the text itself, which is how the 180 `round` filenames hid: the
    # only exemption is the journal's own class and style files, which arXiv
    # must receive verbatim and whose wording is not ours to edit.
    if f not in cls + sty:
        for m in LEAK.finditer(txt):
            _ln = txt[:m.start()].count('\n') + 1
            fails.append('A15 %s:%d carries the internal string %r'
                         % (f, _ln, m.group(0)))
            break
open(os.path.join(dest, '.arxivset_stem'), 'w').write(NEUTRAL_STEM + '\n')

# -------------------------------------------------- A5/A6: the filenames
ALLOWED = set(string.ascii_letters + string.digits + '_+-.,=/')
lower = {}
for f in items:
    bad = sorted(set(f) - ALLOWED)
    if bad:
        fails.append('A5 filename character(s) %s not permitted: %s'
                     % (bad, f))
    lower.setdefault(f.lower(), []).append(f)
for k, v in lower.items():
    if len(set(v)) > 1:
        fails.append('A6 names differing only in case: %s' % sorted(set(v)))

# --------------------------------------------- A11: no hidden file
# ★ There is deliberately NO "is there anything unused in DEST" check here.
# DEST is created empty immediately above, so such a check could only ever
# find what this script itself copied: it would pass for ever and prove
# nothing.  The honest version is A9, which compares the TARBALL against the
# manifest after the tarball exists, and it fails if a build product gets in.
hidden = sorted(f for f in items if any(p.startswith('.')
                                       for p in f.split('/')))
if hidden:
    fails.append('A11 hidden file -- arXiv deletes these on announcement: %s'
                 % hidden)

# ------------------------------------------ A10: one and only one top level
tops = [f for f in order
        if re.search(r'^[^%\n]*\\documentclass',
                     open(os.path.join(src, f), errors='ignore').read(), re.M)]
if tops != [stem + '.tex']:
    fails.append('A10 expected exactly one \\documentclass, in %s.tex; found %s'
                 % (stem, tops))

# --------------------------- A12: no JavaScript or embedded action anywhere
BANNED = (b'/JavaScript', b'/JS', b'/Launch', b'/EmbeddedFile', b'/RichMedia',
          b'/Movie', b'/Screen')
for f in figfiles:
    blob = open(os.path.join(src, f), 'rb').read()
    found = sorted(t.decode() for t in BANNED if t in blob)
    if found:
        fails.append('A12 embedded action in %s: %s -- arXiv auto-rejects '
                     'these' % (f, found))

print('%d items: %d tex + %d cls + %d sty + %d figures + %d ancillary '
      '(assembled from %d source .tex, %d of them inlined into numbers.tex)'
      % (len(items), len(_texitems), len(cls), len(sty), len(figfiles),
         len(anc), len(order), len(numbers)))
for f in sorted(figfiles):
    print('    fig', f, '->', figmap[f])
for n in notes:
    print('    note:', n)
for f in fails:
    print('    ** ' + f)
open(os.path.join(dest, '.arxivset_manifest'), 'w').write(
    '\n'.join(sorted(items)) + '\n')
print('A1 %d tex resolved, 0 missing' % len(order) if not missing
      else 'A1 FAIL')
print('A2-A6, A10-A13', 'FAIL' if fails else 'PASS')
raise SystemExit(1 if fails else 0)
PY
rc=$?
MAN="$TMPDIR/arxivset_manifest.txt"
mv "$D/.arxivset_manifest" "$MAN" 2>/dev/null
# ★ v4.25: the package's own top-level stem, decided by A15 and read back here
# rather than typed, for the same reason $V is derived and not typed above.
# Removed from DEST before the tarball is made: a file that tells you what the
# set is called must not be IN the set (same rule as the manifest).
PSTEM=$(cat "$D/.arxivset_stem" 2>/dev/null)
rm -f "$D/.arxivset_stem"
[ -n "$PSTEM" ] || PSTEM="$STEM"
[ $rc -eq 0 ] || { echo "arxivset: assembly checks FAILED" >&2; exit 1; }

# ★ The tarball is made HERE, before anything is built in the directory, so
# it holds the submission and nothing else.  Written outside DEST for the
# same reason.  The manifest is kept outside DEST too: a file that documents
# the set must not be IN the set.
TAR="$D.tar.gz"
( cd "$D" && tar --sort=name --owner=0 --group=0 --numeric-owner \
      --mtime="@$SOURCE_DATE_EPOCH" -czf "$TAR" . )
echo "--- A9: the tarball holds the manifest and nothing else"
python3 - "$TAR" "$MAN" <<'PY' || exit 1
import subprocess, sys, tarfile
tar, man = sys.argv[1], sys.argv[2]
with tarfile.open(tar) as t:
    inside = sorted(m.name.lstrip('./') for m in t.getmembers() if m.isfile())
want = sorted(l.strip() for l in open(man) if l.strip())
extra = sorted(set(inside) - set(want))
short = sorted(set(want) - set(inside))
print('    %d file(s) in the tarball, %d in the manifest' % (len(inside), len(want)))
if extra:
    print('    ** A9 in the tarball and not in the manifest: %s' % extra[:12])
if short:
    print('    ** A9 in the manifest and not in the tarball: %s' % short[:12])
print('A9', 'FAIL' if (extra or short) else 'PASS')
raise SystemExit(1 if (extra or short) else 0)
PY
echo "--- tarball: $TAR  $(du -h "$TAR" | cut -f1)"

echo "--- A8: build in the clean directory, from nothing but the set (as $PSTEM.tex)"
cd "$D"
for i in 1 2 3; do
  pdflatex -interaction=nonstopmode "$PSTEM.tex" > /dev/null 2>&1
done
python3 - "$PSTEM" <<'PY'
import re, sys
stem = sys.argv[1]
log = open(stem + '.log', errors='ignore').read()
pages = re.findall(r'Output written.*\((\d+) pages', log)
print('pages: %s | errors: %d | undefined control seq: %d | '
      'unresolved ref/cite: %d | multiply defined: %d | overfull: %d | '
      'underfull: %d | missing file: %d'
      % (pages[-1] if pages else '-',
         len(re.findall(r'^! ', log, re.M)),
         len(re.findall(r'Undefined control sequence', log)),
         len(re.findall(r'Warning: (?:Reference|Citation)', log)),
         len(re.findall(r'multiply defined', log)),
         len(re.findall(r'Overfull', log)),
         len(re.findall(r'Underfull', log)),
         len(re.findall(r'LaTeX Error: File', log))))
try:
    import pymupdf
    d = pymupdf.open(stem + '.pdf')
    print('Type3 fonts:',
          sum(1 for p in d for f in p.get_fonts(full=True) if f[2] == 'Type3'))
except ImportError:
    pass
PY
echo "--- A8: byte comparison with the in-tree build"
if [ -f "$SRC/$STEM.pdf" ]; then
  A=$(md5sum "$D/$PSTEM.pdf"  | cut -d' ' -f1)
  B=$(md5sum "$SRC/$STEM.pdf" | cut -d' ' -f1)
  echo "clean  $A  ($PSTEM.pdf, built from the package)"
  echo "intree $B  ($STEM.pdf, built in the working tree)"
  # ★★ v4.25: these two can only be equal because the manuscript pins
  # \pdftrailerid.  pdfTeX derives the trailer /ID from an MD5 of the OUTPUT
  # FILENAME, so before the pin a renamed build differed in exactly those 32
  # hex digits and in nothing else -- which would have made A15's neutral
  # package name and A8's byte proof mutually exclusive.
  [ "$A" = "$B" ] && echo "A8 PASS: byte-identical" \
                  || { echo "A8 FAIL: the clean build differs" >&2; exit 1; }
else
  echo "A8 SKIP: no $STEM.pdf in the working tree to compare against."
  echo "          Build it there first, then re-run."
fi
echo "--- set size"
du -sh "$D"
echo "manifest: $MAN"
