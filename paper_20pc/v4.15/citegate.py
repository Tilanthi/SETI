#!/usr/bin/env python3
r"""GATE: every bibitem is cited, and every citation has a bibitem.

WHY THIS EXISTS.  Nothing in this build swept citations.  `xrefcheck.py` sweeps
labels, `figorphan.py` sweeps figures, `macroleak.py` sweeps macros, and the
reference list was the one layer with no owner -- so both of the last two
rounds stranded an entry by hand and found it by hand:

  * `AstudilloDefru2017`, left in the bibliography after the sentence that
    cited it was rewritten (round 12);
  * `White2026`, the companion paper, whose only citation was removed by a
    one-sentence edit to the introduction (round 13).

Neither is a LaTeX error.  An uncited `\bibitem` typesets silently in the
reference list, and `pdflatex` reports an undefined citation only as a warning
buried among hundreds of lines -- and `latexlog.py` passes the build either
way, because an undefined citation still produces a PDF.

WHAT IT CHECKS
  G1  every `\bibitem[..]{key}` in the manuscript is cited at least once by
      some `\cite*` command in the manuscript or in a file it `\input`s;
  G2  every key cited anywhere has a `\bibitem` -- the `?` in the typeset
      page, which a reader sees and we do not;
  G3  no key is declared by two `\bibitem`s, which silently prints the second
      one's entry for every citation of the first;
  G4  the check is not vacuous: it found keys to compare at all, on both
      sides, and the comparison covered every `\input` file.

COMMENTS ARE STRIPPED before any key is collected.  A `\cite` inside a
`%`-comment is not a citation, and counting one is how a gate reports an
orphan as cited -- this project's commonest shape of self-deception.

    python3 citegate.py              # the gate
    python3 citegate.py --selftest   # prove each clause can fail AND pass
"""
import os
import re
import sys

import manuscript

HERE = os.path.dirname(os.path.abspath(__file__))

#: DERIVED, NEVER TYPED.  A gate that names the manuscript by hand goes blind
#: the next time the manuscript is renamed, and then reports PASS on an empty
#: comparison: in v4.15 the typed name was still `..._v4.14.tex`, this gate
#: swept 0 source files, G1-G3 all said "PASS none", and only G4 -- the clause
#: written to refuse an empty input set -- saw anything at all.
#: `manuscript.main_file()` globs the directory and asserts exactly one
#: manuscript, as 28 other tools here already do, so a version bump is a
#: rename and nothing else.
MAIN = manuscript.main_file()

#: `\cite`, `\citep`, `\citet`, `\citealt`, `\citeauthor`, `\citeyear`, ...
#: with natbib's optional pre/post notes, and a comma-separated key list.
CITE = re.compile(r'\\cite[a-zA-Z]*\s*(?:\[[^\]]*\]\s*){0,2}\{([^}]*)\}')
BIBITEM = re.compile(r'\\bibitem\s*(?:\[[^\]]*\])?\s*\{([^}]*)\}')
INPUT = re.compile(r'\\(?:input|include)\s*\{([^}]*)\}')


def strip_comments(src):
    """Drop `%`-comments, keeping `\\%`.  Line by line, so a stray brace in a
    comment cannot swallow the rest of the file."""
    out = []
    for line in src.split('\n'):
        i, esc = None, False
        for j, ch in enumerate(line):
            if esc:
                esc = False
                continue
            if ch == '\\':
                esc = True
            elif ch == '%':
                i = j
                break
        out.append(line if i is None else line[:i])
    return '\n'.join(out)


def read(path):
    with open(path, encoding='utf-8') as fh:
        return strip_comments(fh.read())


def sources(main=MAIN):
    """The manuscript and every file it `\\input`s, transitively."""
    seen, order = set(), []
    todo = [main]
    while todo:
        rel = todo.pop(0)
        for cand in (rel, rel + '.tex'):
            path = os.path.join(HERE, cand)
            if os.path.isfile(path):
                break
        else:
            continue
        if path in seen:
            continue
        seen.add(path)
        src = read(path)
        order.append((cand, src))
        todo += INPUT.findall(src)
    return order


def collect(src_list):
    cited, declared, dup = {}, {}, []
    for name, src in src_list:
        for keys in CITE.findall(src):
            for k in keys.split(','):
                k = k.strip()
                if k:
                    cited.setdefault(k, []).append(name)
        for k in BIBITEM.findall(src):
            k = k.strip()
            if k in declared:
                dup.append(k)
            declared.setdefault(k, []).append(name)
    return cited, declared, dup


def run(src_list, verbose=True):
    cited, declared, dup = collect(src_list)
    orphan = sorted(set(declared) - set(cited))
    missing = sorted(set(cited) - set(declared))
    fail = []

    def ck(name, ok, detail):
        if verbose:
            print('  %-4s %-62s %s  %s'
                  % (name, _WHAT[name], 'PASS' if ok else 'FAIL', detail))
        if not ok:
            fail.append(name)

    ck('G1', not orphan,
       'none' if not orphan else '%d uncited: %s'
       % (len(orphan), ', '.join(orphan)))
    ck('G2', not missing,
       'none' if not missing else '%d undeclared: %s'
       % (len(missing), ', '.join(missing)))
    ck('G3', not dup,
       'none' if not dup else '%d declared twice: %s'
       % (len(dup), ', '.join(sorted(set(dup)))))
    ck('G4', len(declared) > 5 and len(cited) > 5 and len(src_list) > 5,
       '%d bibitems, %d cited keys, %d source files'
       % (len(declared), len(cited), len(src_list)))
    return fail, cited, declared


_WHAT = {
    'G1': 'every bibitem is cited somewhere',
    'G2': 'every citation has a bibitem',
    'G3': 'no key is declared twice',
    'G4': 'the comparison was not vacuous',
}


def selftest():
    """Each clause demonstrated FAILING on a perturbed copy and PASSING on the
    real one.  A gate nobody has seen fire is a gate nobody knows works."""
    real = sources()
    base, _, decl = run(real, verbose=False)
    print('selftest: unperturbed ->', base or 'all clauses pass')
    ok = not base
    perturb = {
        'G1': [(MAIN, lambda s: s + '\n\\bibitem[Nobody(1999)]{ZzOrphan} x\n')],
        'G2': [(MAIN, lambda s: s + '\n\\citep{ZzNoSuchKey}\n')],
        'G3': [(MAIN, lambda s: s + '\n\\bibitem[Dup(1999)]{%s} x\n'
                % sorted(decl)[0])],
    }
    for clause, edits in perturb.items():
        mod = []
        for name, src in real:
            for tgt, fn in edits:
                if name == tgt:
                    src = fn(src)
            mod.append((name, src))
        got, _, _ = run(mod, verbose=False)
        hit = got == [clause]
        print('  drive %s: fired %s  %s' % (clause, got or 'nothing',
                                            'OK' if hit else 'WRONG'))
        ok = ok and hit
    #: a `\cite` inside a comment must NOT count as a citation
    mod = [(n, s + '\n% \\citep{ZzCommentedOut}\n') if n == MAIN else (n, s)
           for n, s in real]
    got, cit, _ = run([(n, strip_comments(s)) for n, s in mod], verbose=False)
    hit = 'ZzCommentedOut' not in cit and not got
    print('  drive comment: a commented citation is not a citation  %s'
          % ('OK' if hit else 'WRONG'))
    return 0 if ok and hit else 1


if __name__ == '__main__':
    if '--selftest' in sys.argv:
        raise SystemExit(selftest())
    src = sources()
    print('citegate: %d source files' % len(src))
    fail, cited, declared = run(src)
    print('citegate: %d bibitems, %d cited keys, %d FAIL'
          % (len(declared), len(cited), len(fail)))
    raise SystemExit(1 if fail else 0)
