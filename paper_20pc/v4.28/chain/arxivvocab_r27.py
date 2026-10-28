#!/usr/bin/env python3
"""arxivvocab_r27.py -- the arXiv set may carry no refereeing, round or
version vocabulary, IN ANY FILE, comments included.

Row 41 (round 27): arXiv publishes the LaTeX source, so a comment is
published text.  `prosegate_selfref.py` reads the typeset PDF and strips
comments, so it cannot see one.  This gate does not reason about what the
packager would strip: it BUILDS the arXiv set with `arxivset.sh` into a
private directory and reads every file that would be uploaded -- .tex
(comments and all), ancillary files, class and style files, bibliography --
exactly as uploaded.  A gate on the set is a gate on what ships.

  python3 arxivvocab_r27.py            build the set, scan it, exit 1 on a hit
  python3 arxivvocab_r27.py --set DIR  scan an already-assembled set
  python3 arxivvocab_r27.py --drive 1  plant a vocabulary comment in a COPY
                                       of the assembled set (must fail)
  python3 arxivvocab_r27.py --drive 2  plant it in an ancillary file (must fail)
Nothing is written outside the private scratch directory.
"""
import os
import re
import shutil
import subprocess
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
#: word-bounded, so "rounded", "around" and "revisit" are not hits
VOCAB = [
    (r'\breferee(?:s|\'s|ing)?\b', 'referee'),
    (r'\brefereed\b', 'refereed'),
    (r'\brevision(?:s)?\b', 'revision'),
    (r'\bprevious (?:version|draft|submission)\b', 'previous version'),
    (r'\b(?:this|last|previous|next|earlier) round\b', 'round (process)'),
    (r'\bround[ -]?\d{1,3}\b', 'round N'),
    (r'\bv\d\.\d{2}\b', 'version number'),
    (r'\br\d{1,2}-[a-z]+\b', 'agent/round tag'),
    (r'\bR[12][-–]\d', 'referee item'),
]
#: binary or third-party files are not ours to word
SKIP_EXT = ('.pdf', '.png', '.jpg', '.eps', '.gz', '.tar',
            # the packager's own verification compile (A8) leaves these in
            # the directory; they are not uploaded
            '.log', '.aux', '.out', '.blg')
#: verbatim third-party files: their history is their authors', not ours
THIRD_PARTY = ('openjournal.cls', 'epsf.sty')


def scan(setdir):
    hits = []
    for root, _d, files in os.walk(setdir):
        for f in files:
            if f.endswith(SKIP_EXT) or f in THIRD_PARTY:
                continue
            p = os.path.join(root, f)
            try:
                t = open(p, encoding='utf-8', errors='replace').read()
            except OSError:
                continue
            for i, line in enumerate(t.split('\n'), 1):
                for pat, what in VOCAB:
                    if re.search(pat, line, re.I if what != 'referee item'
                                 else 0):
                        hits.append((os.path.relpath(p, setdir), i, what,
                                     line.strip()[:100]))
    return hits


def main(argv):
    drive = int(argv[argv.index('--drive') + 1]) if '--drive' in argv else 0
    tmp = tempfile.mkdtemp(prefix='arxivvocab.')
    try:
        if '--set' in argv:
            src = argv[argv.index('--set') + 1]
        else:
            src = os.path.join(tmp, 'set')
            r = subprocess.run(['bash', os.path.join(HERE, 'arxivset.sh'), src],
                               cwd=HERE, stdout=subprocess.PIPE,
                               stderr=subprocess.STDOUT, text=True)
            if r.returncode != 0:
                print(r.stdout[-2000:])
                print('arxivvocab: FAIL -- the arXiv set could not be built')
                return 1
        setdir = src
        if drive:
            setdir = os.path.join(tmp, 'driven')
            shutil.copytree(src, setdir)
            texs = sorted(os.path.join(r_, f) for r_, _d, fs in os.walk(setdir)
                          for f in fs if f.endswith('.tex'))
            others = sorted(os.path.join(r_, f) for r_, _d, fs in os.walk(setdir)
                            for f in fs if f.endswith(('.txt', '.csv')))
            tgt = texs[0] if drive == 1 or not others else others[0]
            with open(tgt, 'a') as fh:
                fh.write('\n%% as the referee asked in round 26\n')
        n = sum(1 for _r, _d, fs in os.walk(setdir) for _f in fs)
        assert n > 5, 'the arXiv set holds %d files: the scan measured nothing' % n
        hits = scan(setdir)
        for h in hits[:40]:
            print('  HIT %s:%d [%s] %s' % h)
        print('arxivvocab: %d file(s) scanned, %d hit(s)%s'
              % (n, len(hits), '' if not drive else '  (drive %d)' % drive))
        return 1 if hits else 0
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
