#!/usr/bin/env python3
r"""Gate: no file in this tree may read another version directory by an
unguarded absolute path.

WHY THIS EXISTS.  Round 20 deleted a pushed-and-verified version folder to
free disk and broke the build: a generator read it by absolute path, and
`cleanregen.py` could not see the dependency because the predecessor is
always present while it runs.  Round 22 found ten such pins still in the
tree, four of them unguarded, and **not one of the ten was visible to any
gate**.  A pin is not itself a defect -- a generator written outside the tree
has to read the frozen previous version while it is being written -- but an
*unguarded* one is a time bomb, and the fix is always the same three lines:

    PAPER = (HERE if os.path.exists(os.path.join(HERE, <a file it reads>))
             else '/workspace/SETI/paper_20pc/vN.NN')

i.e. read THIS tree when the file sits in it, and the frozen one only from
outside.  That is `quality_r19.py`'s pattern and `orbit_r19.py` carries the
note explaining why.

WHAT IS CHECKED, for every `.py` and `.sh` file in the tree:
  V1  every occurrence of `paper_20pc/vN.NN` outside a comment lies in a file
      that also carries a guard -- `os.path.exists`, `os.environ.get` or a
      `--paper`/`--out` style override -- within GUARD_LINES lines of it;
  V2  a pin to a version directory that NO LONGER EXISTS is reported, and is
      a FAILURE if it is unguarded (that is the round-20 breakage exactly);
  V3  no file pins THIS version directory by absolute path: inside the tree
      the path is `HERE`, and a self-pin stops working the moment the folder
      is copied to the next version -- which is how every version of this
      paper is made.

★ A gate that cannot fail is worse than no gate: `--selftest` writes three
temporary files, one with an unguarded pin, one with a dead unguarded pin and
one with a self-pin, and requires each to be caught.

Usage:  python3 verpin.py [--selftest]
Exit status 1 on any failure.
"""
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
THIS = os.path.basename(HERE)
PIN = re.compile(r'paper_20pc/(v\d+\.\d+)')
GUARD = re.compile(r'os\.path\.exists|os\.path\.isdir|os\.environ\.get|getenv|'
                   r"--paper|--out|sys\.argv")
GUARD_LINES = 12
VERS = os.path.dirname(HERE)


def scan(root):
    out = []
    for dp, dn, fn in os.walk(root):
        dn[:] = [d for d in dn if d not in ('__pycache__',)]
        for f in sorted(fn):
            if not (f.endswith('.py') or f.endswith('.sh')):
                continue
            p = os.path.join(dp, f)
            rel = os.path.relpath(p, root)
            txt = open(p, errors='ignore').read()
            #   ★ A DOCSTRING IS A COMMENT FOR THIS PURPOSE.  The first
            #   version of this gate reported a pin inside the prose block
            #   of `make_figures_v328.py`, which is documentation and not a
            #   path the file opens.  Triple-quoted blocks are blanked
            #   line-for-line so that line numbers stay true.
            def _blank(mm):
                return re.sub(r'[^\n]', ' ', mm.group(0))
            txt = re.sub(r'(?s)""".*?"""|\'\'\'.*?\'\'\'', _blank, txt)
            lines = txt.splitlines()
            for n, ln in enumerate(lines):
                for m in PIN.finditer(ln):
                    code = ln.split('#')[0] if not ln.lstrip().startswith('#') \
                        else ''
                    if m.group(0) not in code:
                        continue            # a comment, which is a note
                    lo = max(0, n - GUARD_LINES)
                    hi = min(len(lines), n + GUARD_LINES + 1)
                    guarded = bool(GUARD.search('\n'.join(lines[lo:hi])))
                    out.append(dict(file=rel, line=n + 1, ver=m.group(1),
                                    guarded=guarded,
                                    exists=os.path.isdir(
                                        os.path.join(VERS, m.group(1))),
                                    selfpin=(m.group(1) == THIS),
                                    text=ln.strip()[:96]))
    return out


def report(rows, label='verpin'):
    bad = []
    for r in rows:
        why = []
        if not r['guarded']:
            why.append('V1 unguarded')
        if not r['exists'] and not r['guarded']:
            why.append('V2 pins a version directory that no longer exists')
        if r['selfpin']:
            why.append('V3 pins THIS version directory by absolute path')
        state = ('FAIL ' + '; '.join(why)) if why else 'ok  '
        if why:
            bad.append(r)
        print('  %-5s %-44s:%-5d %s  %s'
              % (state.split()[0], r['file'], r['line'], r['ver'],
                 '; '.join(why) or ('guarded' if r['guarded'] else '')))
    print('%s: %d pin(s) into another version directory, %d guarded, '
          '%d dead, %d FAIL'
          % (label, len(rows), sum(1 for r in rows if r['guarded']),
             sum(1 for r in rows if not r['exists']), len(bad)))
    return bad


def selftest():
    import shutil
    import tempfile
    d = tempfile.mkdtemp(prefix='verpin_st_')
    tree = os.path.join(d, 'v9.99')
    os.makedirs(tree)
    open(os.path.join(tree, 'a_unguarded.py'), 'w').write(
        "P = '/workspace/SETI/paper_20pc/v4.21'\n")
    open(os.path.join(tree, 'b_dead.py'), 'w').write(
        "P = '/workspace/SETI/paper_20pc/v0.01'\n")
    open(os.path.join(tree, 'c_guarded.py'), 'w').write(
        "import os\nP = (H if os.path.exists(H) else\n"
        "     '/workspace/SETI/paper_20pc/v4.21')\n")
    open(os.path.join(tree, 'd_comment.py'), 'w').write(
        "# was /workspace/SETI/paper_20pc/v4.21, now HERE\n")
    global THIS, VERS
    _t, _v = THIS, VERS
    THIS, VERS = 'v9.99', d
    rows = scan(tree)
    bad = report(rows, 'verpin --selftest')
    THIS, VERS = _t, _v
    shutil.rmtree(d)
    got = sorted(r['file'] for r in bad)
    want = ['a_unguarded.py', 'b_dead.py']
    ok = got == want
    print('  selftest: caught %s, expected %s -> %s'
          % (got, want, 'PASS' if ok else 'FAIL'))
    return 0 if ok else 1


if __name__ == '__main__':
    if '--selftest' in sys.argv:
        sys.exit(selftest())
    sys.exit(1 if report(scan(HERE)) else 0)
