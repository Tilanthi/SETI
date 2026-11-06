#!/usr/bin/env python3
r"""GATE: EVERY SHIPPED .py MUST COMPILE.

★★★ Found by accident on 2026-10-23 while fixing something else:
**`prosecount.py` does not compile, and has not compiled in the pushed tree.**
`def main():` was followed by `import manuscript` indented EIGHT spaces, so the
module raises `IndentationError` the moment anything imports or runs it.  It is
the only one of the tree's ~620 shipped `.py` files in that state, and four
`REFEREE_RESPONSE_*.md` documents name it as the tool that counted the prose
quoted to a referee.

Nothing in 44 gates could see it, for a reason worth stating: every other gate
reasons about the *content* of the build -- macros, literals, labels, captions,
pages -- and a file that cannot be parsed has no content to disagree with.
`cleanregen` only re-runs the generators `make_all.sh` actually invokes, and
this one is invoked by neither `make_all.sh` nor `gate.sh`, so its syntax error
was invisible precisely because it is unused -- which is also why it had to be
found by a compiler rather than by a check.

Two clauses, one drive.

  C1  every `*.py` in the build root compiles.
  C2  the scan is not measuring an empty set (>= 100 files), which is the
      failure mode the restructure census found in four gates: a PASS that has
      stopped looking because a glob stopped matching.

Usage: pycompile.py [--drive 1]
"""
import glob
import os
import py_compile
import shutil
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))


def scan(d):
    bad = []
    files = sorted(glob.glob(os.path.join(d, '*.py')))
    for f in files:
        try:
            py_compile.compile(f, cfile=os.path.join(
                tempfile.gettempdir(), 'pycompile_gate.pyc'), doraise=True)
        except py_compile.PyCompileError as e:
            bad.append((os.path.basename(f), str(e).strip().splitlines()[-1]))
        except Exception as e:                       # noqa: BLE001
            bad.append((os.path.basename(f), '%s: %s' % (type(e).__name__, e)))
    return files, bad


def main():
    if '--drive' in sys.argv:
        tmp = tempfile.mkdtemp(prefix='pycompile_drive_')
        try:
            for f in sorted(glob.glob(os.path.join(HERE, '*.py')))[:120]:
                shutil.copy(f, tmp)
            open(os.path.join(tmp, 'zz_planted.py'), 'w').write(
                'def main():\n        import os\n    return os\n')
            files, bad = scan(tmp)
            print('--drive 1: %d file(s) scanned, %d do not compile: %s'
                  % (len(files), len(bad), ', '.join(b[0] for b in bad)))
            ok = any(b[0] == 'zz_planted.py' for b in bad)
            print('DEMONSTRATED' if ok else
                  'NOT DEMONSTRATED: the planted IndentationError did not fire')
            return 0 if ok else 1
        finally:
            shutil.rmtree(tmp, ignore_errors=True)

    files, bad = scan(HERE)
    fails = 0
    print('%-4s C1 every shipped .py compiles' % ('ok' if not bad else 'FAIL'))
    print('     scanned %d file(s); %d failed' % (len(files), len(bad)))
    for n, e in bad:
        print('     %-34s %s' % (n, e))
    if bad:
        fails += 1
    enough = len(files) >= 100
    print('%-4s C2 the scan is not measuring an empty set' % ('ok' if enough else 'FAIL'))
    print('     %d file(s) >= 100' % len(files))
    if not enough:
        fails += 1
    print('\npycompile: %d clause(s) failed' % fails)
    return 1 if fails else 0


if __name__ == '__main__':
    sys.exit(main())
