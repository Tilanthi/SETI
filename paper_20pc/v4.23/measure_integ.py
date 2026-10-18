#!/usr/bin/env python3
"""Per-section extent in COLUMN POINTS, measured from a PDF given on the
command line.

Why this exists rather than `secbudget.py`: `secbudget.main()` reads the PDF
beside the master `.tex`, i.e. the SHARED job name, which `BUILD_RULE.md`
makes read-only precisely so that two agents cannot measure each other's
build.  An agent working under its own job name therefore cannot use it, and
the obvious workaround -- copying a probe PDF onto the shared path -- is the
collision the rule exists to prevent.  The measurement logic is secbudget's,
imported, not re-derived.

    python3 measure_integ.py build_integrator/r9-integ-probe.pdf

Reports column points as well as pages, because this document held at 60
pages through a complete rewrite of one section and a 27-word cut to the
abstract: a page here is a quantity the column filler absorbs, so page
counting cannot detect the work.  One column is 693.8 pt and one page is two
of them; a full-width float is charged at twice its height.
"""
import json
import os
import re
import sys

import pymupdf

import manuscript
import secbudget as SB

HERE = os.path.dirname(os.path.abspath(__file__))


def measure(pdf):
    doc = pymupdf.open(pdf)
    mid = doc[0].rect.width / 2.0
    blocks = []
    for p in doc:
        for b in p.get_text('blocks'):
            x0, y0, x1, _y1, txt = b[0], b[1], b[2], b[3], b[4]
            col = 0 if x0 < mid - 20 else 1
            wide = (x1 - x0) > 0.75 * doc[0].rect.width
            flow = (p.number * 2 + (0 if wide else col)) * SB.H + (y0 - SB.TOP)
            blocks.append((flow, p.number + 1, col, wide,
                           re.sub(r'\s+', ' ', txt).strip()))
    blocks.sort()
    heads = SB.titles()
    found, used = [], 0
    for h in heads:
        want = SB.clean(h['title'])
        if not want:
            continue
        key = want[:40]
        hit = None
        for i in range(used, len(blocks)):
            t = SB.clean(blocks[i][4])
            if len(t) < 6:
                continue
            joined = ' '.join(SB.clean(blocks[j][4])
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
    endflow = max(b[0] for b in blocks)
    rows, seq = [], [f for f in found if f['flow'] is not None]
    for a, b in zip(seq, seq[1:] + [{'flow': endflow, 'title': 'END'}]):
        rows.append({'title': a['title'], 'file': a['file'], 'page': a['page'],
                     'pt': b['flow'] - a['flow'],
                     'pages': (b['flow'] - a['flow']) / SB.PAGE})
    byfile = {}
    for r in rows:
        f = r['file'].split(':')[0]
        byfile[f] = byfile.get(f, 0.0) + r['pt']
    missing = [f for f in manuscript.section_files() if f not in byfile]
    return doc, rows, byfile, missing


def main(argv):
    pdf = argv[1] if len(argv) > 1 else 'build_integrator/r9-integ-probe.pdf'
    doc, rows, byfile, missing = measure(pdf)
    unmatched = [r for r in rows if r['pt'] is None]
    print('measure_integ: %s -- %d pages, 1 column = %.1f pt, '
          '1 page = %.1f pt' % (pdf, len(doc), SB.H, SB.PAGE))
    if missing:
        print('  ** %d section file(s) did not match a heading in the PDF '
              'and are NOT in this table: %s' % (len(missing), missing))
    if unmatched:
        print('  ** %d heading(s) unmatched' % len(unmatched))
    def _is_app(f):
        return os.path.basename(f).startswith('app_')
    main_f = [f for f in sorted(byfile) if not _is_app(f)]
    app_f = [f for f in sorted(byfile) if _is_app(f)]
    tot = {}
    for label, group in (('MAIN', main_f), ('APPENDIX', app_f)):
        print('\n%-34s %10s %8s' % (label, 'col-pt', 'pp'))
        s = 0.0
        for f in group:
            print('  %-32s %10.1f %8.2f' % (f, byfile[f], byfile[f] / SB.PAGE))
            s += byfile[f]
        print('  %-32s %10.1f %8.2f' % ('-- total', s, s / SB.PAGE))
        tot[label] = s
    resid = len(doc) * SB.PAGE - tot['MAIN'] - tot['APPENDIX']
    print('\nTOTAL sections %.1f col-pt = %.2f pp; PDF %d pp; residual '
          '%.1f col-pt = %.2f pp (title block, abstract above the first '
          'heading, reference list)'
          % (tot['MAIN'] + tot['APPENDIX'],
             (tot['MAIN'] + tot['APPENDIX']) / SB.PAGE, len(doc),
             resid, resid / SB.PAGE))
    json.dump({'pdf': pdf, 'col_pt_per_page': SB.PAGE, 'byfile': byfile,
               'sections': rows, 'main_pt': tot['MAIN'],
               'appendix_pt': tot['APPENDIX'], 'pdf_pages': len(doc)},
              open(os.path.join(HERE, 'measure_integ.json'), 'w'), indent=1)
    return 1 if (missing or unmatched) else 0


if __name__ == '__main__':
    sys.exit(main(sys.argv))
