#!/usr/bin/env python3
"""The whole round-9 reduction programme, measured cumulatively.

Each stage is a real build on a scratch copy, because the sum of the
individual deltas is not the delta of the sum: floats repack, and a single
0.2-page table usually moves nothing on its own.

  0  v4.09 as shipped
  1  + R2's float cut list (19 floats)
  2  + Appendix M deleted
  3  + Appendices A and B deleted (upper bound on "most of A and B")
  4  + every sentence the purge inventory marks DELETE or REPHRASE

Writes programme_measure.json.
"""
import json
import os
import re
import shutil
import subprocess
import sys

import cutmeasure as CM
import manuscript
import purge_measure as PM

HERE = os.path.dirname(os.path.abspath(__file__))
SCRATCH = CM.SCRATCH


def pages():
    p, ap, err = PM.build(SCRATCH)
    return {'pages': p, 'main': (ap - 1) if ap else None,
            'appx': (p - ap + 1) if ap else None, 'latex_errors': err}


def main():
    inv = json.load(open(os.path.join(HERE, 'floatinv.json')))
    want = []
    for f in inv:
        try:
            n = int(f['number'])
        except (TypeError, ValueError):
            continue
        if f['kind'].startswith('table') and n in CM.CUT_TABLES:
            want.append(f)
        elif f['kind'].startswith('figure') and n in CM.CUT_FIGURES:
            want.append(f)
    CM.stage()
    out = [('0 v4.09 as shipped', pages())]

    for f in sorted(want, key=lambda f: (f['env_file'], -f['env_begin'])):
        CM.drop_float(f)
    out.append(('1 + the %d floats on R2 cut list' % len(want), pages()))

    CM.drop_section('sections/app_M_repaired.tex')
    out.append(('2 + Appendix M deleted', pages()))

    CM.drop_section('sections/app_A_reproducibility.tex')
    CM.drop_section('sections/app_B_figofmerit.tex')
    out.append(('3 + Appendices A and B deleted', pages()))

    # the purge, applied to what is left
    hits = json.load(open(os.path.join(HERE, 'purge_hits.json')))
    import purge_inventory as PI
    for rel in manuscript.section_files():
        p = os.path.join(SCRATCH, rel)
        if not os.path.exists(p):
            continue
        text = open(p, encoding='utf-8').read()
        newpars = []
        for par in text.split('\n\n'):
            if par.lstrip().startswith('%'):
                newpars.append(par)
                continue
            keep = []
            for s in PM.sentences(par):
                bad = None
                for name, rx, default in PI.COMPILED:
                    m = rx.search(s)
                    if m and PI.classify(name, default,
                                         s) in ('DELETE', 'REPHRASE'):
                        bad = name
                        break
                if bad and PM.STRUCT.search(s):
                    bad = None
                if not bad:
                    keep.append(s)
            newpars.append(' '.join(keep) if keep else '')
        open(p, 'w', encoding='utf-8').write(
            re.sub(r'\n{3,}', '\n\n', '\n\n'.join(newpars)))
    out.append(('4 + the revision history purged', pages()))

    base = out[0][1]
    rows = []
    for name, r in out:
        rows.append({'stage': name, **r,
                     'cum_delta_pages': base['pages'] - r['pages'],
                     'cum_delta_main': (base['main'] - r['main'])
                                       if r['main'] else None,
                     'cum_delta_appx': (base['appx'] - r['appx'])
                                       if r['appx'] else None})
        print('%-42s %3s pp  (main %3s, appx %3s)  cum %+d'
              % (name, r['pages'], r['main'], r['appx'],
                 -(base['pages'] - r['pages'])))
    json.dump(rows, open(os.path.join(HERE, 'programme_measure.json'), 'w'),
              indent=1)
    shutil.rmtree(SCRATCH)
    return 0


if __name__ == '__main__':
    sys.exit(main())
