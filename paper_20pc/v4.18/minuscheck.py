#!/usr/bin/env python3
r"""minuscheck.py -- a hyphen used where a minus sign belongs.

★★★ WHY THIS EXISTS.  The journal does no copy-editing of any kind, so the
typography of the final PDF is entirely the authors'.  In text mode `-0.29`
typesets a HYPHEN: short, high, and visibly not a minus.  The minus is
`$-0.29$`, and the two sit a couple of points apart on the page.  Nothing in
the LaTeX log sees the difference, every gate passes, and the defect survives
every build.  It matters here because the paper already prints a true minus
48 times -- `km\,s$^{-1}$`, `$-1.97$`, `TRAPPIST$-$1` -- so the same column
of the same table can carry both conventions, and the crossing ledger does.

★★ TWO READINGS, AND THE PDF IS THE GROUND TRUTH.
  `--source`  walks the \input closure and names the file and line, which is
              what a fix needs.  It tracks maths mode by splitting each line
              on unescaped `$`, so a legitimate `$-1.97$` is never reported.
  `--pdf`     counts the glyphs actually set: U+002D before a digit against
              U+2212 before a digit, page by page.  A macro expansion, a
              generated table fragment and a hand-typed sentence are
              indistinguishable here, which is the point -- the source scan
              can only see what it can parse, and this sees what a reader
              sees.
Neither is a substitute for the other: the source scan localises and the PDF
scan cannot be fooled.  Both run by default.

★ WHAT IS DELIBERATELY NOT A HIT.  `--` and `---` (en and em dash);
`16--143` (a range); `line-of-sight` and every other compound word; a hyphen
inside an identifier such as `ALMA J153702653-33192492`, where the character
belongs to the name; and anything inside maths.  The pattern is a hyphen with
a digit to its right and neither a word character nor another hyphen to its
left.

Usage
    python3 minuscheck.py [master.tex] [--pdf FILE] [--source] [--drive N]

Exit status 0 if no text-mode hyphen-as-minus is typeset, 1 otherwise.
★ This gate FAILS on the manuscript as it stands: 64 of the 112 signed
numbers in the PDF are hyphens.  That is the finding, not a bug in the gate.

Drives (`--drive N`), each of which must change the verdict on its own:
    1  inject `-1.23` into a scratch copy of the master, in text mode
       -> the source scan must report exactly one new hit
    2  inject `$-1.23$` into the same place, in maths mode
       -> the source scan must report NO new hit.  A check that fires on a
          correct minus as well as a wrong one localises nothing.
    3  claim the PDF holds no hyphen-before-digit when it holds 64
       -> the PDF scan must disagree with the claim
"""
import os
import re
import sys

# a hyphen, with a digit to its right, and neither a word character, a
# closing bracket, nor another hyphen to its left; and not the first half of
# an en dash written as `--`.
PAT = re.compile(r'(?<![\w)\]}\-])-(?=\d)(?!\d*\s*--)')


def text_segments(line):
    """The non-maths parts of one source line.

    Maths mode is tracked by splitting on unescaped `$`.  `\\$` is a printed
    dollar and `\\%` a printed per-cent sign, so the scanner steps over a
    backslash and the character after it without reading either.
    """
    out, buf, inmath, i, n = [], [], False, 0, len(line)
    while i < n:
        c = line[i]
        if c == '\\':
            if not inmath:
                buf.append(line[i:i + 2])
            i += 2
            continue
        if c == '$':
            if not inmath:
                out.append(''.join(buf))
                buf = []
            inmath = not inmath
            i += 1
            continue
        if not inmath:
            buf.append(c)
        i += 1
    if not inmath:
        out.append(''.join(buf))
    return out


def uncomment(line):
    """Everything before the first unescaped `%`."""
    i, n = 0, len(line)
    while i < n:
        if line[i] == '\\':
            i += 2
            continue
        if line[i] == '%':
            return line[:i]
        i += 1
    return line


def closure(master):
    order, queue = [], [master]
    while queue:
        f = queue.pop(0)
        if f in order or not os.path.isfile(f):
            continue
        order.append(f)
        txt = '\n'.join(uncomment(l)
                        for l in open(f, errors='ignore').read().split('\n'))
        for t in re.findall(r'\\(?:input|include)\s*\{([^}]*)\}', txt):
            queue.append(t if t.endswith('.tex') else t + '.tex')
    return order


def scan_source(files, quiet=False):
    """(file, line, text) for every text-mode hyphen-as-minus."""
    hits = []
    for f in files:
        for n, line in enumerate(open(f, errors='ignore'), 1):
            code = uncomment(line)
            if not code.strip():
                continue
            if any(PAT.search(seg) for seg in text_segments(code)):
                hits.append((f, n, line.rstrip()))
    if not quiet:
        per = {}
        for f, n, _ in hits:
            per[f] = per.get(f, 0) + 1
        for f in sorted(per, key=lambda k: -per[k]):
            print('  %-30s %3d line(s)' % (f, per[f]))
    return hits


def scan_pdf(path, quiet=False):
    """(hyphen count, minus count, {page: hyphens}) for the typeset PDF."""
    import pymupdf
    doc = pymupdf.open(path)
    hy, mi, pages = 0, 0, {}
    for i, p in enumerate(doc, 1):
        t = p.get_text()
        h = len(re.findall(r'(?<![0-9A-Za-z])-(?=[0-9])', t))
        hy += h
        mi += len(re.findall(r'(?<![0-9A-Za-z])−(?=[0-9])', t))
        if h:
            pages[i] = h
    if not quiet:
        print('  typeset: %d hyphen-before-digit, %d true minus-before-digit'
              % (hy, mi))
        print('  pages: %s' % pages)
    return hy, mi, pages


def drive(n, master):
    """Each drive must change the verdict on its own."""
    import shutil
    import tempfile
    files = closure(master)
    base = len(scan_source(files, quiet=True))
    if n in (1, 2):
        tmp = tempfile.mkdtemp(prefix='minuscheck_drive')
        probe = os.path.join(tmp, os.path.basename(master))
        shutil.copy(master, probe)
        inject = 'A drifting carrier at -1.23 kHz.' if n == 1 \
            else 'A drifting carrier at $-1.23$ kHz.'
        with open(probe, 'a') as fh:
            fh.write('\n%% drive %d\n%s\n' % (n, inject))
        got = len(scan_source([probe], quiet=True)) \
            - len(scan_source([master], quiet=True))
        want = 1 if n == 1 else 0
        shutil.rmtree(tmp)
        ok = got == want
        print('drive %d: injected %-34s new hits %d, expected %d -> %s'
              % (n, inject, got, want, 'FIRES' if ok else 'DID NOT FIRE'))
        return 0 if ok else 1
    if n == 3:
        pdfs = [f for f in os.listdir('.')
                if f.startswith('technosignatures_') and f.endswith('.pdf')]
        if not pdfs:
            print('drive 3: SKIP, no built PDF here to read')
            return 0
        hy, mi, _ = scan_pdf(pdfs[0], quiet=True)
        print('drive 3: claim "the PDF holds no hyphen-before-digit"; '
              'measured %d (and %d true minus) -> %s'
              % (hy, mi, 'FIRES' if hy else 'DID NOT FIRE'))
        return 0 if hy else 1
    print('drive %d: no such drive' % n)
    return 1


def main(argv):
    master = next((a for a in argv[1:] if a.endswith('.tex')), None)
    if master is None:
        cand = [f for f in os.listdir('.')
                if f.startswith('technosignatures_') and f.endswith('.tex')]
        if len(cand) != 1:
            print('minuscheck: name the master .tex (found %s)' % cand)
            return 2
        master = cand[0]
    if '--drive' in argv:
        return drive(int(argv[argv.index('--drive') + 1]), master)

    pdf = None
    if '--pdf' in argv:
        pdf = argv[argv.index('--pdf') + 1]
    else:
        cand = [f for f in os.listdir('.')
                if f.startswith('technosignatures_') and f.endswith('.pdf')]
        pdf = cand[0] if len(cand) == 1 else None

    files = closure(master)
    print('minuscheck: %d source file(s)' % len(files))
    hits = scan_source(files)
    fail = 0
    if pdf:
        hy, _, _ = scan_pdf(pdf)
        fail = hy
    else:
        print('  no PDF found; source scan only, which is NOT the verdict')
        fail = len(hits)
    print('minuscheck: %s' % ('0 FAIL' if not fail else '%d FAIL' % fail))
    return 1 if fail else 0


if __name__ == '__main__':
    sys.exit(main(sys.argv))
