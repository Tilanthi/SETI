#!/usr/bin/env python3
"""Inventory every float in the manuscript with its MEASURED typeset height.

Column height is 694 pt and the document is two-column, so a single-column
float of height h costs h/1388 of a page and a starred (full-width) float
costs h/694.  floatsize.sh reported h/694 for both, which overstates every
single-column float by exactly a factor two; that is fixed here.

Heights come from \\@largefloatcheck, which LaTeX calls once per float in
source order, so the heights pair with the floats found in the flattened
source.  Writes floatinv.json.
"""
import json
import os
import re
import shutil
import subprocess
import sys

import manuscript

HERE = os.path.dirname(os.path.abspath(__file__))
SCRATCH = os.path.join(os.path.dirname(HERE), '.v410_scratch_float')
PATCH = r'''\makeatletter
\let\astra@lfc\@largefloatcheck
\def\@largefloatcheck{\typeout{ASTRAFLOAT ht=\the\ht\@currbox}\astra@lfc}
\makeatother
'''
ENV = re.compile(r'\\(begin|end)\{(table\*?|figure\*?)\}')


def expanded():
    """[(file, line, text)] for the flattened document with every
    \\input{tab_*} / \\input{tables/*} fragment expanded in place.

    The float ENVIRONMENT lives in the section file and the `tabular` lives in
    the fragment, so a scanner that stops at the \\input line splits every
    generated table in half and then pairs the heights with the wrong floats.
    """
    out = []
    for n, line in enumerate(manuscript.lines(), 1):
        m = re.match(r'^(\s*)\\input\{(tab_[^}]+|tables/[^}]+)\}(.*)$', line)
        path = os.path.join(HERE, (m.group(2) + '.tex')) if m else None
        if m and os.path.exists(path):
            frag = m.group(2) + '.tex'
            for j, sl in enumerate(open(path, encoding='utf-8').read()
                                   .split('\n'), 1):
                out.append((frag, j, sl))
            if m.group(3).strip():
                f, fl = manuscript.where(n).split(':')
                out.append((f, int(fl), m.group(3)))
        else:
            f, fl = manuscript.where(n).split(':')
            out.append((f, int(fl), line))
    return out


ENV2 = re.compile(r'\\(begin|end)\{(table\*?|figure\*?)\}')


def source_floats():
    """Floats in the order TeX meets them, with the file they live in."""
    rows = expanded()
    out, stack = [], []
    for idx, (f, ln, text) in enumerate(rows):
        for m in ENV2.finditer(text):
            if m.group(1) == 'begin':
                stack.append((idx, f, ln, m.group(2)))
            elif stack:
                i0, f0, ln0, kind = stack.pop()
                body = '\n'.join(r[2] for r in rows[i0:idx + 1])
                lab = re.search(r'\\label\{([^}]*)\}', body)
                cap = re.search(r'\\caption\{(.{0,80})', body, re.S)
                frag = None
                for r in rows[i0:idx + 1]:
                    if r[0].startswith('tab') or r[0].startswith('tables/'):
                        frag = r[0]
                        break
                endf, endl = rows[idx][0], rows[idx][1]
                out.append({'env_file': f0, 'env_begin': ln0,
                            'env_end_file': endf, 'env_end': endl,
                            'kind': kind,
                            'label': lab.group(1) if lab else None,
                            'caption': re.sub(r'\s+', ' ', cap.group(1))
                                       if cap else '',
                            'origin': '%s:%d' % (f0, ln0),
                            'fragment': frag})
    return out


def heights():
    if os.path.exists(SCRATCH):
        shutil.rmtree(SCRATCH)
    os.makedirs(SCRATCH)
    # reflink-copy the build; only the main .tex is modified
    subprocess.run(['cp', '-a'] + [os.path.join(HERE, f) for f in
                                   os.listdir(HERE)] + [SCRATCH], check=True)
    mf = manuscript.main_file()
    p = os.path.join(SCRATCH, mf)
    s = open(p, encoding='utf-8').read()
    s = s.replace(r'\begin{document}', PATCH + r'\begin{document}', 1)
    open(p, 'w', encoding='utf-8').write(s)
    env = dict(os.environ, SOURCE_DATE_EPOCH='1577836800',
               FORCE_SOURCE_DATE='1')
    subprocess.run(['pdflatex', '-interaction=nonstopmode', mf],
                   cwd=SCRATCH, env=env, stdout=subprocess.DEVNULL)
    log = open(os.path.join(SCRATCH, mf[:-4] + '.log'),
               errors='ignore').read()
    hts = [float(x) for x in re.findall(r'ASTRAFLOAT ht=([\d.]+)pt', log)]
    shutil.rmtree(SCRATCH)
    return hts


def main():
    fl = source_floats()
    ht = heights()
    if len(fl) != len(ht):
        print('WARNING: %d floats in source, %d heights logged'
              % (len(fl), len(ht)))
    # float numbers and pages from the aux
    aux = open(os.path.join(HERE, manuscript.main_file()[:-4] + '.aux'),
               errors='ignore').read()
    num = {lab: (n, int(pg)) for lab, n, pg in
           re.findall(r'\\newlabel\{([^}]+)\}\{\{([^{}]*)\}\{(\d+)\}', aux)}
    flat = manuscript.flat()
    appline = flat.split('\n').index('\\appendix')
    for f, h in zip(fl, ht):
        f['height_pt'] = h
        f['cols'] = 2 if f['kind'].endswith('*') else 1
        f['page_cost'] = h / (694.0 if f['cols'] == 2 else 1388.0)
        n, pg = num.get(f['label'], (None, None))
        f['number'], f['page'] = n, pg
        f['region'] = 'APPX' if (pg or 0) >= 34 else 'MAIN'
    json.dump(fl, open(os.path.join(HERE, 'floatinv.json'), 'w'), indent=1)
    tm = sum(f['page_cost'] for f in fl if f['region'] == 'MAIN')
    ta = sum(f['page_cost'] for f in fl if f['region'] == 'APPX')
    for f in fl:
        print('%-7s %4s p%-3s %7.1fpt %5.2f pp  %-22s %s'
              % (f['kind'], f['number'], f['page'], f['height_pt'],
                 f['page_cost'], f['label'],
                 f.get('fragment') or f['origin']))
    print('float area: MAIN %.2f pp, APPX %.2f pp, total %.2f pp over %d floats'
          % (tm, ta, tm + ta, len(fl)))


if __name__ == '__main__':
    sys.exit(main())
