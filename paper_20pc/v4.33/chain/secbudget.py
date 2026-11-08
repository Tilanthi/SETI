#!/usr/bin/env python3
"""Per-section page cost, measured from the built PDF.

The page is two columns of 694 pt, so a section's cost is its extent along the
typeset FLOW -- page by page, column by column -- divided by 1388 pt.  Counting
whole pages charges whichever section happens to own the top of a page for the
one before it; that is how a 60-page paper acquires a 22.07-page main text.

Headings are located by their text in the PDF, matched against the section
titles read out of the source, so the measurement needs no instrumentation of
the build.  Full-width (starred) floats interrupt the two-column flow; the
residual at the end of the table is the size of that effect and is printed.

Writes secbudget.json.
"""
import json
import os
import re
import sys

import pymupdf

import manuscript

# ★★ --drive N PERTURBS ONE THING AND THE RUN MUST THEN FAIL.  A measurement
# that reports its own blindness and exits zero is this project's commonest
# defect and this file was an instance of it, so the fix ships with the proof.
# Per the standing rule, the output SUFFIX FOLLOWS THE FLAG, not the
# perturbation: `--drive 0` applies nothing and still writes
# `secbudget_drive0.json`, so no drive can leave a file production reads.
DRIVE = 0
for _a in sys.argv[1:]:
    if _a.startswith('--drive'):
        DRIVE = int(_a.split('=')[1]) if '=' in _a else int(sys.argv[sys.argv.index(_a) + 1])
DRIVEN = any(a.startswith('--drive') for a in sys.argv[1:])

HERE = os.path.dirname(os.path.abspath(__file__))
TOP, BOT = 43.8, 737.6
H = BOT - TOP                      # one column
PAGE = 2 * H                       # one page of column measure


def titles():
    """[(flat_line, file, kind, title)] for every heading, in order.

    Titles are read with brace matching, not with a per-line regex: three of
    the appendix headings wrap onto a second source line, and a per-line regex
    silently drops them -- which is how a 370-line appendix came to be missing
    from the budget table.
    """
    L = manuscript.lines()
    out = []
    for n, line in enumerate(L, 1):
        # ★ THE REGEX USED TO BE r'\\(section\*?|subsection\*?|appendix)\b'.
        # In `\section*{...}` the \b sits between `*` and `{`, neither of
        # which is a word character, so there is no boundary there and the
        # alternative with the star never matched; the one without it matched
        # `\section`, left `*{...}` as the remainder, found it did not start
        # with `{` and skipped the heading.  Every STARRED section was
        # therefore invisible, which is all six of the back matter's -- 1.09
        # pp charged to the Conclusions, the section before it.  Anchoring on
        # the brace instead of on a word boundary cannot fail that way.
        if DRIVE == 2:      # drive 2: the pre-fix \b regex, stars invisible
            m = re.match(r'\\(section\*?|subsection\*?|appendix)\b()', line)
        else:
            m = re.match(r'\\(section|subsection)(\*?)\s*(?=\{)', line) or \
                re.match(r'\\(appendix)()\b', line)
        if not m:
            continue
        kind = m.group(1) + m.group(2)
        if kind == 'appendix':
            out.append({'line': n, 'file': manuscript.where(n),
                        'kind': kind, 'title': 'APPENDIX'})
            continue
        rest = line[m.end():]
        if not rest.lstrip().startswith('{'):
            continue
        buf, depth, k = '', 0, n - 1
        chunk = rest[rest.index('{'):]
        while True:
            for ch in chunk:
                if ch == '{':
                    depth += 1
                    if depth == 1:
                        continue
                elif ch == '}':
                    depth -= 1
                    if depth == 0:
                        break
                buf += ch
            if depth == 0:
                break
            k += 1
            if k >= len(L):
                break
            chunk = '\n' + L[k]
        out.append({'line': n, 'file': manuscript.where(n), 'kind': kind,
                    'title': buf.strip()})
    # The class typesets its own REFERENCES heading, so without a synthetic
    # entry the whole bibliography is charged to the last appendix -- 0.47 pp
    # onto Appendix E.  It is read from the source, not assumed: the
    # thebibliography environment must exist exactly once.
    bib = [n for n, line in enumerate(L, 1)
           if line.lstrip().startswith('\\begin{thebibliography}')]
    assert len(bib) == 1, 'expected one thebibliography, found %d' % len(bib)
    out.append({'line': bib[0], 'file': manuscript.where(bib[0]),
                'kind': 'section', 'title': 'References'})
    return out


LABEL = re.compile(r'^(?:APPENDIX\s+)?(?:[A-Z]|\d+)(?:\.\d+)*\.\s+')


def si_only_lines():
    """Flat line numbers the DEFAULT build does not typeset.

    Two headings in `sections/` are legitimately absent from the default PDF:
    the abstract has no sectioning command at all, and the Supporting
    Information notice sits inside `\\ifdefined\\SIPAPER`, which is undefined
    in the build every gate reads.  Exempting them by name would be a
    whitelist, and a whitelist is how a gate goes blind.  So the exemption is
    DERIVED: the conditional structure of the flattened document is walked and
    the unreachable lines are computed, with `\\begin{thebibliography}` --
    which is reachable -- asserted not to be among them.
    """
    L = manuscript.lines()
    start = next(n for n, l in enumerate(L, 1) if '\\begin{document}' in l)
    tok = re.compile(r'\\(ifdefined\s*\\([A-Za-z@]+)|if[a-zA-Z@]*|else|fi)')
    skip, stack = set(), []
    for n in range(start, len(L) + 1):
        line = L[n - 1]
        if line.lstrip().startswith('%'):
            continue
        if not all(stack):
            skip.add(n)
        for m in tok.finditer(line):
            if m.group(1).startswith('ifdefined'):
                # \SIPAPER and \SIAPPX are undefined in the default build;
                # anything else is assumed defined, which only ever makes this
                # set SMALLER and so cannot hide a heading by accident.
                stack.append(m.group(2) not in ('SIPAPER', 'SIAPPX'))
            elif m.group(1).startswith('if'):
                stack.append(True)
            elif m.group(1) == 'else':
                if stack:
                    stack[-1] = not stack[-1]
            else:
                if stack:
                    stack.pop()
        if not all(stack):
            skip.add(n)
    assert not stack, 'unbalanced conditionals: %d left open' % len(stack)
    bib = [n for n, l in enumerate(L, 1)
           if l.lstrip().startswith('\\begin{thebibliography}')]
    assert bib and bib[0] not in skip, \
        'the bibliography was computed to be unreachable -- the conditional ' \
        'walk is wrong, and this check would then excuse a real omission'
    return skip


def clean(t):
    t = re.sub(r'\\[a-zA-Z]+\s*', ' ', t).strip()
    # Drop the PRINTED section label.  `numberedappendix` made the appendix
    # letters typeset, so every appendix heading reaches the PDF as
    # "A. SPECTRAL RESPONSE..." while the source title is "Spectral
    # response...".  `clean` used to delete digits, which is why the numbered
    # MAIN headings went on matching and all thirteen appendix headings
    # stopped: a letter is not a digit.  The label is stripped here instead,
    # and only when it ends in a period and a space, so a title that begins
    # with a capital letter ("A stellar-frame multi-epoch...") is untouched.
    if DRIVE != 1:          # drive 1: the pre-fix behaviour, letters kept
        t = LABEL.sub('', t)
    t = re.sub(r'[^A-Za-z ]', ' ', t)
    return re.sub(r'\s+', ' ', t).strip().upper()


def main():
    pdf = os.path.join(HERE, manuscript.main_file()[:-4] + '.pdf')
    doc = pymupdf.open(pdf)
    mid = doc[0].rect.width / 2.0
    blocks = []
    for p in doc:
        for b in p.get_text('blocks'):
            x0, y0, x1, y1, txt = b[0], b[1], b[2], b[3], b[4]
            col = 0 if x0 < mid - 20 else 1
            wide = (x1 - x0) > 0.75 * doc[0].rect.width
            flow = ((p.number) * 2 + (0 if wide else col)) * H + (y0 - TOP)
            blocks.append((flow, p.number + 1, col, wide,
                           re.sub(r'\s+', ' ', txt).strip()))
    blocks.sort()
    heads = titles()
    found = []
    used = 0
    for h in heads:
        want = clean(h['title'])
        if not want:
            continue
        key = want[:40]
        hit = None
        for i in range(used, len(blocks)):
            t = clean(blocks[i][4])
            if len(t) < 6:
                continue
            # a heading may be broken over two or three PDF blocks
            joined = ' '.join(clean(blocks[j][4])
                              for j in range(i, min(i + 3, len(blocks))))
            if joined.startswith(key[:min(len(key), 12)]) and \
               (joined.startswith(key) or key.startswith(t[:len(key)])):
                hit = i
                break
        if hit is None:
            found.append(dict(h, flow=None, page=None))
            continue
        used = hit + 1
        found.append(dict(h, flow=blocks[hit][0], page=blocks[hit][1]))
    # bibliography and document end
    endflow = max(b[0] for b in blocks)
    rows = []
    seq = [f for f in found if f['flow'] is not None]
    for a, b in zip(seq, seq[1:] + [{'flow': endflow, 'title': 'END'}]):
        rows.append({'title': a['title'], 'file': a['file'], 'page': a['page'],
                     'pages': (b['flow'] - a['flow']) / PAGE})
    byfile = {}
    for r in rows:
        f = r['file'].split(':')[0]
        byfile[f] = byfile.get(f, 0.0) + r['pages']
    # a file whose first heading did not match in the PDF would silently
    # vanish from the budget; every section file must appear.
    # ★ `section_files()` is every .tex in sections/, so this check used to
    # demand that files the default build never typesets appear in a budget
    # measured from that build -- which is why it reported eight missing files
    # on every run and exited zero anyway.  The expected set is now derived:
    # a file counts if it holds a sectioning command on a line the default
    # build reaches.
    si = set() if DRIVE == 3 else si_only_lines()   # drive 3: no exemption
    # ★★ THE EXPECTED SET MUST NOT BE DERIVED FROM THE HEADING PARSER.  It was,
    # for one iteration of this fix, and drive 2 -- which restores the regex
    # that cannot see `\section*` -- then PASSED: with the parser blind, the
    # back matter had no headings, so it was not expected, so it was not
    # missing.  "A diagnostic that reads the same file as the thing it
    # diagnoses is circular" is on this project's own list.  The expectation
    # therefore comes from a second, deliberately crude scan -- a bare
    # substring for a sectioning command on a line the default build reaches
    # -- which shares no code with titles().
    L = manuscript.lines()
    SECT = re.compile(r'\\(?:sub)?section\b')
    expect, nsect = set(), 0
    for n in range(1, len(L) + 1):
        if n in si or L[n - 1].lstrip().startswith('%'):
            continue
        if not SECT.search(L[n - 1]):
            continue
        nsect += 1
        f = manuscript.where(n).split(':')[0]
        if f.startswith('sections/'):
            expect.add(f)
    missing = sorted(f for f in expect if f not in byfile)
    exempt = sorted(set(manuscript.section_files()) - expect)
    # and every one of those sectioning commands must have become a heading
    nhead = len([h for h in heads
                 if h['kind'] != 'appendix' and h['title'] != 'References'
                 and h['line'] not in si])
    out = 'secbudget_drive%d.json' % DRIVE if DRIVEN else 'secbudget.json'
    json.dump({'sections': rows, 'byfile': byfile, 'exempt': exempt,
               'total_pages': len(doc)},
              open(os.path.join(HERE, out), 'w'), indent=1)
    for r in rows:
        print('%6.3f pp  p%-3d %-11s %s'
              % (r['pages'], r['page'], r['file'].split(':')[0]
                 .replace('sections/', '').replace('.tex', '')
                 .replace('technosignatures_40pc_v', 'main v'), r['title'][:58]))
    print('--')
    for f in sorted(byfile):
        print('%6.2f pp  %s' % (byfile[f], f))
    tot = sum(r['pages'] for r in rows)
    print('sum of sections %.2f pp; PDF %d pp; first heading at flow %.0f pt'
          % (tot, len(doc), seq[0]['flow']))
    # ★ THIS USED TO BE TWO print() CALLS AND A `return 0`.  Its own docstring
    # says "a file whose first heading did not match in the PDF would silently
    # vanish from the budget; every section file must appear" -- and then it
    # passed anyway.  At v4.18 it was printing eight missing files and
    # thirteen unmatched headings on every run while charging all 10.65 pp of
    # appendix to the main .tex, and the page budget everyone quoted was wrong
    # by a third.  A measurement that reports its own blindness and exits zero
    # is the vacuous gate this project has found more than twenty times.
    print('exempt (no heading the default build typesets): %s' % exempt)
    unmatched = [f['title'][:40] for f in found
                 if f['flow'] is None and f['line'] not in si]
    bad = []
    if missing:
        bad.append('%d section file(s) absent from the budget: %s'
                   % (len(missing), missing))
    if unmatched:
        bad.append('%d heading(s) in the source were not found in the PDF: %s'
                   % (len(unmatched), unmatched))
    if abs(tot - sum(r['pages'] for r in rows)) > 1e-9:
        bad.append('internal inconsistency in the row sum')
    if not rows:
        bad.append('no headings matched at all')
    if nhead != nsect:
        bad.append('the heading parser found %d headings where a bare scan '
                   'for a sectioning command finds %d reachable ones -- the '
                   'parser is dropping headings' % (nhead, nsect))
    if bad:
        for b in bad:
            print('  FAIL ' + b)
        return 1
    if DRIVE:
        print('  DRIVE %d DID NOT FAIL -- the perturbation is not detected '
              'and the check it exercises is vacuous' % DRIVE)
        return 2
    print('  OK %d headings, %d files, every section file accounted for'
          % (len(rows), len(byfile)))
    return 0


if __name__ == '__main__':
    sys.exit(main())
