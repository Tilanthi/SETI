#!/usr/bin/env python3
"""Measure what each proposed cut actually saves, by building without it.

Page counts in this document are not monotone -- floats repack, a deleted
table can cost a page -- so every entry in CUTLIST.json carries a MEASURED
delta from a real build, not an estimate:

  * `page_cost`   the float's own typeset area, from floatinv.py (additive)
  * `delta_pages` total pages removed by deleting this one item, measured
  * `delta_main` / `delta_appx`  where the pages came from

and the whole cut list is then measured TOGETHER, because the sum of the
individual deltas is not the delta of the sum.

The scratch build lives beside the build directory (a reflink copy, so it
costs nothing until a file is modified) and is removed afterwards.  Nothing in
the real build directory is touched.

Usage:  python3 cutmeasure.py [--quick]
"""
import json
import os
import re
import shutil
import subprocess
import sys

import manuscript

HERE = os.path.dirname(os.path.abspath(__file__))
SCRATCH = os.path.join(os.path.dirname(HERE), '.v410_scratch_cut')
MAIN = manuscript.main_file()
ENVPIN = {'SOURCE_DATE_EPOCH': '1577836800', 'FORCE_SOURCE_DATE': '1'}

# R2's cut list, by float number
CUT_TABLES = [7, 8, 11, 12, 20, 21, 22, 25, 26, 27, 28, 31, 33]
CUT_FIGURES = [9, 10, 13, 14, 15, 16]


def stage():
    if os.path.exists(SCRATCH):
        shutil.rmtree(SCRATCH)
    os.makedirs(SCRATCH)
    subprocess.run('cp -a %s/. %s/' % (HERE, SCRATCH), shell=True, check=True)


def build():
    env = dict(os.environ, **ENVPIN)
    for _ in range(2):
        subprocess.run(['pdflatex', '-interaction=nonstopmode', MAIN],
                       cwd=SCRATCH, env=env, stdout=subprocess.DEVNULL,
                       stderr=subprocess.DEVNULL)
    log = open(os.path.join(SCRATCH, MAIN[:-4] + '.log'),
               errors='ignore').read()
    m = re.search(r'Output written.*?\((\d+) pages', log)
    if not m:
        return None, None, None, len(re.findall(r'^! ', log, re.M))
    pages = int(m.group(1))
    aux = open(os.path.join(SCRATCH, MAIN[:-4] + '.aux'),
               errors='ignore').read()
    ap = re.search(r'\\newlabel\{page:appstart\}\{\{[^}]*\}\{(\d+)\}', aux)
    ap = int(ap.group(1)) if ap else None
    # region split by column flow, as pagesplit.py does, but cheaply: the
    # appendix label's page is enough for a DELTA.
    return pages, (ap - 1) if ap else None, (pages - ap + 1) if ap else None, \
        len(re.findall(r'^! ', log, re.M))


def restore(paths):
    for rel in paths:
        src, dst = os.path.join(HERE, rel), os.path.join(SCRATCH, rel)
        if os.path.exists(src):
            shutil.copy2(src, dst)
        elif os.path.exists(dst):
            os.remove(dst)


def drop_float(f):
    """Delete the float's whole environment from its section file.

    The float ENVIRONMENT is in the section file even when the `tabular` is in
    a generated fragment, so deleting the \\input line alone would leave an
    empty table floating and measure nothing.  Lines come from floatinv.py.
    """
    rel = f['env_file']
    p = os.path.join(SCRATCH, rel)
    lines = open(p, encoding='utf-8').read().split('\n')
    a, b = f['env_begin'], f['env_end']
    assert lines[a - 1].strip().startswith('\\begin{%s}' % f['kind']), \
        (rel, a, lines[a - 1][:60])
    assert lines[b - 1].strip().startswith('\\end{%s}' % f['kind']), \
        (rel, b, lines[b - 1][:60])
    del lines[a - 1:b]
    open(p, 'w', encoding='utf-8').write('\n'.join(lines))
    return [rel]


def drop_section(rel):
    """Remove a whole section file (its \\input line)."""
    p = os.path.join(SCRATCH, MAIN)
    s = open(p, encoding='utf-8').read()
    new = re.sub(r'^\\input\{%s\}%%?\n' % re.escape(rel[:-4]), '', s,
                 flags=re.M)
    assert new != s, rel
    open(p, 'w', encoding='utf-8').write(new)
    return [MAIN]


def main():
    inv = json.load(open(os.path.join(HERE, 'floatinv.json')))
    want = {}
    for f in inv:
        if f['number'] is None:
            continue
        try:
            n = int(f['number'])
        except ValueError:
            continue
        kind = 'Table' if f['kind'].startswith('table') else 'Figure'
        if (kind == 'Table' and n in CUT_TABLES) or \
           (kind == 'Figure' and n in CUT_FIGURES):
            want.setdefault((kind, n), f)
    missing = ([('Table', n) for n in CUT_TABLES if ('Table', n) not in want]
               + [('Figure', n) for n in CUT_FIGURES
                  if ('Figure', n) not in want])
    stage()
    base = build()
    print('baseline: %s pages (main %s, appx %s), %s latex errors' % base)
    out = []
    items = sorted(want.items(), key=lambda kv: (kv[0][0], kv[0][1]))
    for (kind, n), f in items:
        touched = drop_float(f)
        pages, mn, ax, err = build()
        out.append({'item': '%s %d' % (kind, n), 'label': f['label'],
                    'kind': f['kind'],
                    'source': f.get('fragment') or f['env_file'],
                    'region': f['region'],
                    'height_pt': f['height_pt'],
                    'page_cost': f['page_cost'],
                    'delta_pages': base[0] - pages,
                    'delta_main': (base[1] - mn) if mn else None,
                    'delta_appx': (base[2] - ax) if ax else None,
                    'latex_errors': err,
                    'caption': f['caption'][:70]})
        print('%-10s %-20s cost %5.2f pp  measured delta %+d pp (main %+d, '
              'appx %+d)' % (out[-1]['item'], f['label'] or '?',
                             f['page_cost'], -out[-1]['delta_pages'],
                             -(out[-1]['delta_main'] or 0),
                             -(out[-1]['delta_appx'] or 0)))
        restore(touched)

    # --- whole sections --------------------------------------------------
    for rel in ['sections/app_M_repaired.tex',
                'sections/app_A_reproducibility.tex',
                'sections/app_B_figofmerit.tex']:
        touched = drop_section(rel)
        pages, mn, ax, err = build()
        out.append({'item': rel, 'label': None, 'kind': 'section',
                    'source': rel, 'region': 'APPX',
                    'height_pt': None, 'page_cost': None,
                    'delta_pages': base[0] - pages,
                    'delta_main': (base[1] - mn) if mn else None,
                    'delta_appx': (base[2] - ax) if ax else None,
                    'latex_errors': err, 'caption': 'whole appendix'})
        print('%-10s cost  -     measured delta %+d pp'
              % (rel, -(base[0] - pages)))
        restore(touched)

    # --- the whole cut list together -------------------------------------
    # Deleting several floats from one file must go BOTTOM UP, or the second
    # deletion uses line numbers the first one invalidated.
    stage()
    touched = []
    for (kind, n), f in sorted(items, key=lambda kv: (kv[1]['env_file'],
                                                      -kv[1]['env_begin'])):
        touched += drop_float(f)
    pages, mn, ax, err = build()
    together = {'item': 'ALL FLOATS IN THE CUT LIST', 'delta_pages':
                base[0] - pages, 'delta_main': (base[1] - mn) if mn else None,
                'delta_appx': (base[2] - ax) if ax else None,
                'latex_errors': err}
    print('together: %d floats removed -> %d pages (%+d), main %+d, appx %+d'
          % (len(items), pages, pages - base[0],
             (mn - base[1]) if mn else 0, (ax - base[2]) if ax else 0))
    touched += drop_section('sections/app_M_repaired.tex')
    pages2, mn2, ax2, err2 = build()
    together['with_app_M'] = {'pages': pages2, 'delta_pages': base[0] - pages2,
                              'delta_main': (base[1] - mn2) if mn2 else None,
                              'delta_appx': (base[2] - ax2) if ax2 else None,
                              'latex_errors': err2}
    print('together + Appendix M: %d pages (%+d)' % (pages2, pages2 - base[0]))
    json.dump({'baseline': {'pages': base[0], 'main': base[1],
                            'appx': base[2]},
               'items': out, 'together': together, 'missing': missing},
              open(os.path.join(HERE, 'cutmeasure.json'), 'w'), indent=1)
    if missing:
        print('NOT FOUND in the float inventory: %s' % missing)
    shutil.rmtree(SCRATCH)
    return 0


if __name__ == '__main__':
    sys.exit(main())
