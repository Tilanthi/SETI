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
        m = re.match(r'\\(section\*?|subsection\*?|appendix)\b', line)
        if not m:
            continue
        kind = m.group(1)
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
    return out


def clean(t):
    t = re.sub(r'\\[a-zA-Z]+\s*', ' ', t)
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
    missing = [f for f in manuscript.section_files() if f not in byfile]
    json.dump({'sections': rows, 'byfile': byfile,
               'total_pages': len(doc)},
              open(os.path.join(HERE, 'secbudget.json'), 'w'), indent=1)
    for f in sorted(byfile):
        print('%6.2f pp  %s' % (byfile[f], f))
    tot = sum(r['pages'] for r in rows)
    print('sum of sections %.2f pp; PDF %d pp; first heading at flow %.0f pt'
          % (tot, len(doc), seq[0]['flow']))
    print('files missing from the budget: %s' % missing)
    print('unmatched headings: %s'
          % [f['title'][:30] for f in found if f['flow'] is None])
    return 0


if __name__ == '__main__':
    sys.exit(main())
