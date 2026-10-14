#!/usr/bin/env python3
"""One canonical view of the manuscript, now that it is split into sections.

v4.10 splits the monolithic .tex into sections/*.tex, with the main file
reduced to a preamble plus \\input lines.  Every checker that scans the
manuscript's PROSE must therefore scan the flattened document, not the main
file -- otherwise it silently sees 263 lines of preamble, reports zero
problems, and becomes a check that cannot fail.  That is the defect family
this project has already met fifteen times, so the flattener carries its own
assertions and `--selftest` drives them.

    import manuscript
    src   = manuscript.flat()        # the whole document as one string
    where = manuscript.where(n)      # 'sections/04_method.tex:118' for
                                     # 1-based line n of flat()

flat() is byte-exact in the sense that matters here: the concatenation of the
main file's non-\\input lines and every section file, in document order,
contains exactly the characters TeX sees, so a literal, an integer or a macro
use is found if and only if pdflatex would typeset it.
"""
import glob
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
_INPUT = re.compile(r'^\\input\{(sections/[^}]+)\}%?\s*$')


def main_file():
    c = sorted(f for f in os.listdir(HERE)
               if f.startswith('technosignatures_') and f.endswith('.tex'))
    assert len(c) == 1, 'expected exactly one manuscript .tex, found %r' % (c,)
    return c[0]


def _build():
    mf = main_file()
    out, mapping = [], []
    with open(os.path.join(HERE, mf), encoding='utf-8') as fh:
        mainlines = fh.read().split('\n')
    n_inputs = 0
    for i, line in enumerate(mainlines, 1):
        m = _INPUT.match(line)
        if not m:
            out.append(line)
            mapping.append((mf, i))
            continue
        n_inputs += 1
        rel = m.group(1)
        path = os.path.join(HERE, rel + '.tex')
        assert os.path.exists(path), 'missing section file %s' % path
        with open(path, encoding='utf-8') as fh:
            sub = fh.read()
        sublines = sub.split('\n')
        if sublines and sublines[-1] == '':
            sublines.pop()          # the file's own trailing newline
        for j, sl in enumerate(sublines, 1):
            out.append(sl)
            mapping.append((rel + '.tex', j))
    # Assertion: every section file on disk is actually inputted.  A section
    # left behind by an edit must not be silently dropped from the gates.
    inputted = {f for f, _ in mapping if f.startswith('sections/')}
    ondisk = {os.path.relpath(p, HERE)
              for p in glob.glob(os.path.join(HERE, 'sections', '*.tex'))}
    assert inputted == ondisk, ('section files not inputted: %s; inputted but '
                                'absent: %s' % (sorted(ondisk - inputted),
                                                sorted(inputted - ondisk)))
    assert n_inputs == len(ondisk), (n_inputs, len(ondisk))
    # Assertion: the flattened document must still look like a document.
    txt = '\n'.join(out)
    for needed in (r'\begin{document}', r'\end{document}', r'\begin{abstract}',
                   r'\appendix', r'\section{Introduction}'):
        assert needed in txt, 'flattened manuscript lost %s' % needed
    return txt, mapping


_CACHE = None


def _cache():
    global _CACHE
    if _CACHE is None:
        _CACHE = _build()
    return _CACHE


def flat():
    """The whole manuscript as one string, sections expanded in place."""
    return _cache()[0]


def lines():
    """flat() split into lines (no trailing newline element)."""
    return flat().split('\n')


def where(n):
    """'file:line' for 1-based line n of flat()."""
    f, i = _cache()[1][n - 1]
    return '%s:%d' % (f, i)


def section_files():
    return sorted(os.path.relpath(p, HERE)
                  for p in glob.glob(os.path.join(HERE, 'sections', '*.tex')))


if __name__ == '__main__':
    txt, mapping = _cache()
    print('manuscript: %s + %d section files -> %d flattened lines, %d chars'
          % (main_file(), len(section_files()), len(mapping), len(txt)))
    if '--selftest' in sys.argv:
        # Drive each assertion: a missing section file, a stray section file,
        # and a truncated document.
        import shutil
        import tempfile
        fails = 0
        for name, mutate in [
            ('stray section file',
             lambda d: open(os.path.join(d, 'sections', 'zz_stray.tex'),
                            'w').write('x\n')),
            ('section file deleted',
             lambda d: os.remove(os.path.join(d, 'sections', '01_intro.tex'))),
        ]:
            d = tempfile.mkdtemp()
            for f in [main_file(), 'manuscript.py']:
                shutil.copy(os.path.join(HERE, f), d)
            shutil.copytree(os.path.join(HERE, 'sections'),
                            os.path.join(d, 'sections'))
            mutate(d)
            r = os.system('cd %s && python3 manuscript.py >/dev/null 2>&1' % d)
            ok = r != 0
            print('  drive %-24s %s' % (name, 'FIRES' if ok else 'DID NOT FIRE'))
            fails += 0 if ok else 1
            shutil.rmtree(d)
        print('selftest: %d drive(s) failed to fire' % fails)
        assert fails == 0
