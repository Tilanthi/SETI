#!/usr/bin/env python3
r"""dupgate.py -- GATE: no clause of the manuscript is typeset verbatim in two files.

WHY THIS FILE EXISTS (round 25, Ruling 13)

    The author has asked about unwarranted repetition for seven rounds, and
    every instance found so far was found by a person READING the paper.
    Round 24's Ruling 4 cut four verbatim main-text/appendix duplicates and
    called them "the cheapest page in the paper"; Ruling 6.1, in the same
    round, created a fifth by moving the figure-of-merit arithmetic into a new
    appendix and leaving its closing clause in the main text as well.  Nothing
    in this tree could see any of them.

    A one-line `grep` cannot do it, and that is the sharpest part of the
    lesson: the §6.2 copy of the haystack clause wrapped as `a far` /
    `smaller haystack`, so `grep "a far smaller haystack"` over sections/
    returned ONE hit for a clause that was on the page twice.  The same
    line-break blindness is why round 24 recorded a false claim as deleted
    while it was still in the shipped PDF.  So this gate normalises
    whitespace and strips comments before it matches anything.

WHAT IT DOES

    Reads the manuscript's own \input closure over sections/, strips LaTeX
    comments, collapses whitespace, and slides a 16-word window over each
    file.  Any n-gram that occurs in more than one file is a FAIL unless an
    allowlist entry covers it, and every allowlist entry carries a written
    keep-reason -- the `genai_allow.txt` discipline, for the same reason: a
    deliberate restatement is a decision, and a decision should be recorded
    where the next reader will meet it.

    A restatement inside ONE file is not reported.  Saying something twice in
    one section is a judgement for a writer; saying it twice in two files is
    the thing that survives a cut of either one.

    Reported with the clause, the files, and the first line of each, so a
    FAIL names the pages rather than the measure.

DRIVE (`--drive 1`): copies a 20-word clause out of one section into another
    and requires the gate to fail.  Without it this is one more check that
    cannot fail, which is the defect family this project has sixteen
    instances of.

Usage:  dupgate.py [--allow dupgate_allow.txt] [--n 16] [--drive 1]
"""
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
NGRAM = 16

COMMENT = re.compile(r'(?<!\\)%.*')
WS = re.compile(r'\s+')


def _args():
    a = sys.argv[1:]
    allow = os.path.join(HERE, 'dupgate_allow.txt')
    n = NGRAM
    drive = None
    for i, x in enumerate(a):
        if x == '--allow':
            allow = a[i + 1]
        elif x == '--n':
            n = int(a[i + 1])
        elif x == '--drive':
            drive = int(a[i + 1])
    return allow, n, drive


def manuscript_files():
    """The files the manuscript \\inputs, not a glob: retired/ and snapshots/
    hold old copies of whole sections and a glob would sweep those in and
    report every one of them as a duplicate of the live file."""
    main = [f for f in sorted(os.listdir(HERE))
            if f.startswith('technosignatures_') and f.endswith('.tex')]
    assert len(main) == 1, main
    src = open(os.path.join(HERE, main[0]), encoding='utf-8').read()
    src = COMMENT.sub('', src)
    out = []
    for m in re.finditer(r'\\input\{([^}]+)\}', src):
        p = m.group(1)
        if not p.startswith('sections/'):
            continue
        f = p if p.endswith('.tex') else p + '.tex'
        if os.path.exists(os.path.join(HERE, f)):
            out.append(f)
    return out


def words(path):
    t = open(os.path.join(HERE, path), encoding='utf-8').read()
    t = COMMENT.sub('', t)
    return WS.sub(' ', t).strip().split(' ')


def load_allow(path):
    """Each non-comment line is `<keep-reason> :: <clause>`.  An entry without
    a reason is rejected: an allowlist whose entries do not say why is a way
    of forgetting, not a way of deciding."""
    out = {}
    if not os.path.exists(path):
        return out
    for ln in open(path, encoding='utf-8'):
        ln = ln.strip()
        if not ln or ln.startswith('#'):
            continue
        assert '::' in ln, 'allowlist entry carries no keep-reason: %r' % ln
        why, clause = ln.split('::', 1)
        assert why.strip(), 'empty keep-reason: %r' % ln
        out[WS.sub(' ', clause).strip()] = why.strip()
    return out


def main():
    allowf, n, drive = _args()
    files = manuscript_files()
    assert len(files) > 5, files
    W = {f: words(f) for f in files}
    if drive == 1:
        #: the perturbation is the defect itself: one clause of one section
        #: copied verbatim into another, which is what the gate exists to
        #: catch and what no other check in this tree can see.
        src = sorted(W, key=lambda f: -len(W[f]))[0]
        dst = sorted(W, key=lambda f: -len(W[f]))[1]
        W[dst] = W[dst] + W[src][100:130]
    allow = load_allow(allowf)

    seen = {}
    for f, ws in W.items():
        local = set()
        for i in range(len(ws) - n + 1):
            g = ' '.join(ws[i:i + n])
            if g in local:
                continue
            local.add(g)
            seen.setdefault(g, []).append((f, i))

    dups = {g: v for g, v in seen.items()
            if len({f for f, _ in v}) > 1 and g not in allow}
    # ★ Report each duplicated CLAUSE once, not every overlapping window of
    # it.  A 40-word duplicate contains 25 duplicated 16-grams, and printing
    # all 25 hides how many distinct duplications there are -- which is the
    # number a length pass needs.  Runs of consecutive duplicated offsets in
    # one file are merged into the maximal clause they span.
    byfile = {}
    for g, v in dups.items():
        for f, i in v:
            byfile.setdefault(f, set()).add(i)
    clauses = {}
    for f, idx in byfile.items():
        for i in sorted(idx):
            if i - 1 in idx:
                continue
            j = i
            while j + 1 in idx:
                j += 1
            txt = ' '.join(W[f][i:j + n])
            clauses.setdefault(txt, set()).add(f)
    # a clause wholly contained in a longer reported one is not a second find
    grown = []
    for txt in sorted(clauses, key=lambda x: (-len(x), x)):
        if any(txt in t for t, _ in grown):
            continue
        grown.append((txt, sorted(clauses[txt])))

    print('dupgate: %d section file(s), %d-word window, %d allowlisted '
          'clause(s)' % (len(files), n, len(allow)))
    for ext, hits in grown:
        print('  DUPLICATE in %d file(s): %s' % (len(hits), ' | '.join(hits)))
        print('    "%s%s"' % (ext[:300], '...' if len(ext) > 300 else ''))
    if grown:
        print('dupgate: FAIL -- %d clause(s) typeset verbatim in more than '
              'one file.  Cut the copy, or add an allowlist entry WITH A '
              'KEEP-REASON to %s' % (len(grown), os.path.basename(allowf)))
        return 1
    print('dupgate: PASS -- no clause of %d words or more is typeset in two '
          'files' % n)
    return 0


if __name__ == '__main__':
    sys.exit(main())
