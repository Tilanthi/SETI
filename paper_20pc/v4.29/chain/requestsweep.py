#!/usr/bin/env python3
r"""requestsweep.py -- GATE: no shipped `.tex` may carry an open work marker.

WHY THIS EXISTS.  Seven pieces of work were written into the manuscript source
as `%% REQUEST (... owner -> ... owner)` comment blocks, addressed to roles
that nobody held.  A comment is a channel with no reader and no owner, so none
of the seven was ever done and nobody knew any was outstanding.  One of them
was the observation that a figure's artwork had been emitted for the full page
width and then placed in a single column, which left its labels at about half
their intended size.  That request sat in the source, correct, for several
versions, and a reader of the printed paper could see the result.

THE RULE THIS ENFORCES.  A comment may record WHY code or text is the way it
is -- that is knowledge, and the source is the right place for it.  A comment
may NEVER record a task someone else has to do.  A task goes in the round's
queue, against a named owner, where somebody reads it.

So: `REQUEST`, `TODO`, `FIXME`, `XXX` and `PLEASE` are refused anywhere in the
shipped sources, in comments and in body text alike -- body text too, because
`PLEASE RE-EMIT` typeset into a caption would be worse than leaving it in a
comment, and because a gate that only looks at comments teaches people to
write their to-do list outside one.

HOW IT IS BOUNDED, AND WHY THAT MATTERS HERE.  This project has found more
than twenty gates that could not fail, one of them because its test string was
a SUBSTRING of the thing it was guarding, so it matched for the wrong reason
and passed for five rounds.  Every marker here is matched on word boundaries
and that is proved both ways: `--selftest` requires each marker to be found in
a string that holds it and requires `REQUESTED`, `TODOS`, `PLEASED`, `XXXVII`
and `FIXMEUP` -- which all CONTAIN a marker -- to be found in nothing.

WHICH FILES.  The transitive `\input` closure of the manuscript, walked from
the one `technosignatures*.tex` in this directory.  Not a glob: `retired/`,
`snapshots/` and `.r12sens_backup/` all hold old copies of the section files,
every one of them full of markers, and a glob would sweep those and let a
shipped file that is no longer `\input` escape.  A named input that does not
exist on disk is a FAILURE, not a skip -- the commonest way a sweep comes to
read nothing is that it quietly read nowhere.

DRIVES.  Every clause is made to fail on purpose before it is believed, and
none of them writes anything: the drives mutate the in-memory source map that
the production path reads, so a drive can never leave a marker on disk.

    --drive 1   a `%% TODO:` is injected into a shipped comment        C1 fires
    --drive 2   a bare `PLEASE` is injected into BODY text             C1 fires
    --drive 3   the closure is emptied                                 C2 fires
    --drive 4   only near-misses are injected (REQUESTED, TODOS, ...)  all pass
    --drive 5   a named `\input` is removed from disk                  C3 fires
    --selftest  the matcher alone, on strings, both directions

Usage: requestsweep.py [--drive N] [--selftest]
"""
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))

# The five markers.  Matched case-insensitively and on word boundaries: a
# lower-case "please" in a comment is the same request as an upper-case one,
# and "REQUESTED" is an ordinary English word that is not one.
MARKERS = ('REQUEST', 'TODO', 'FIXME', 'XXX', 'PLEASE')
PAT = re.compile(r'\b(%s)\b' % '|'.join(MARKERS), re.IGNORECASE)


def scan_text(text):
    """Every marker in one source, as (line number, marker, line)."""
    out = []
    for i, ln in enumerate(text.split('\n'), 1):
        for m in PAT.finditer(ln):
            out.append((i, m.group(1).upper(), ln.strip()))
    return out


def closure(drive=0):
    """The manuscript's transitive \\input closure, read into memory."""
    main = sorted(f for f in os.listdir(HERE)
                  if f.startswith('technosignatures') and f.endswith('.tex'))
    if len(main) != 1:
        raise SystemExit('requestsweep: expected one manuscript in %s, '
                         'found %r' % (HERE, main))
    src, missing, stack = {}, [], [main[0]]
    while stack:
        f = stack.pop(0)
        if f in src or f in missing:
            continue
        p = os.path.join(HERE, f)
        if drive == 5 and f == 'sections/05_results.tex':
            p = os.path.join(HERE, 'sections/no_such_file_drive5.tex')
        if not os.path.isfile(p):
            missing.append(f)
            continue
        src[f] = open(p, encoding='utf-8', errors='replace').read()
        for m in re.finditer(r'\\input\{([^}]+)\}', src[f]):
            t = m.group(1).strip()
            stack.append(t if t.endswith('.tex') else t + '.tex')
    return src, missing


def main():
    drive = (int(sys.argv[sys.argv.index('--drive') + 1])
             if '--drive' in sys.argv else 0)

    if '--selftest' in sys.argv:
        ok = True
        for mk in MARKERS:
            got = scan_text('a line with %s in it' % mk)
            if [g[1] for g in got] != [mk]:
                print('SELFTEST FAIL: %s not matched alone -> %r' % (mk, got))
                ok = False
            got = scan_text('a line with %s in it' % mk.lower())
            if [g[1] for g in got] != [mk]:
                print('SELFTEST FAIL: lower-case %s missed' % mk)
                ok = False
        # the substring trap, in both halves: each of these CONTAINS a marker
        # and none of them IS one.
        for near in ('REQUESTED', 'requests', 'TODOS', 'PLEASED', 'XXXVII',
                     'FIXMEUP', 'XXXX', 'untodo'):
            got = scan_text('a line with %s in it' % near)
            if got:
                print('SELFTEST FAIL: %r matched %r -- the match is a '
                      'substring match, not a word match' % (near, got))
                ok = False
        # and a line holding two of them reports two
        if len(scan_text('%% TODO and also PLEASE')) != 2:
            print('SELFTEST FAIL: two markers on one line counted once')
            ok = False
        print('requestsweep --selftest: %s'
              % ('PASS, %d markers, boundary-matched both ways' % len(MARKERS)
                 if ok else 'FAIL'))
        return 0 if ok else 1

    src, missing = closure(drive)

    if drive == 1:
        k = 'sections/05_results.tex'
        src[k] = '%% TODO: hand this to somebody.\n' + src[k]
    if drive == 2:
        k = 'sections/05_results.tex'
        src[k] = src[k].replace('\\section{Results}',
                                '\\section{Results} PLEASE re-emit this.', 1)
        if 'PLEASE' not in src[k]:          # the section heading moved
            src[k] += '\nPLEASE re-emit this.\n'
    if drive == 3:
        src = {}
    if drive == 4:
        k = 'sections/05_results.tex'
        src[k] = ('%% REQUESTED, TODOS, PLEASED, XXXVII, FIXMEUP, requests\n'
                  + src[k])

    fails = []

    # ---- C3: every named input exists.  A sweep that silently skips the one
    # file holding the markers is the failure mode this gate is here to avoid.
    if missing:
        fails.append('C3: %d \\input(s) named by the manuscript are not on '
                     'disk, so they were not swept: %s'
                     % (len(missing), ', '.join(sorted(missing))))

    # ---- C2: and it must not be reading nothing.  The manuscript is 180-odd
    # files; a closure that collapses to a handful means the walk broke, and a
    # broken walk passes this gate silently.
    nchar = sum(len(v) for v in src.values())
    if len(src) < 20 or nchar < 100000:
        fails.append('C2: the sweep read %d file(s) and %d characters, which '
                     'is not this manuscript.  A gate that reads nothing '
                     'passes for ever' % (len(src), nchar))

    # ---- C1: the markers themselves.
    hits = []
    for f in sorted(src):
        for ln, mk, text in scan_text(src[f]):
            hits.append((f, ln, mk, text))
    if hits:
        fails.append(
            'C1: %d open work marker(s) in the shipped source.  A task '
            'written where nobody reads it is a task that never happens; '
            'move it to the round queue against a named owner and delete '
            'the comment.' % len(hits))

    for f, ln, mk, text in hits:
        print('  %-34s %5d  %-8s %s' % (f, ln, mk, text[:88]))
    if fails:
        for msg in fails:
            print('requestsweep: FAIL -- %s' % msg)
        return 1
    print('requestsweep: %d shipped .tex, %d characters, 0 open %s markers'
          % (len(src), nchar, '/'.join(MARKERS)))
    return 0


if __name__ == '__main__':
    sys.exit(main())
