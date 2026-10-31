#!/usr/bin/env python3
"""How many pages the revision history actually occupies, measured.

R1 estimates 5-7 pages.  This builds a scratch copy with every sentence that
`purge_inventory.py` marks DELETE or REPHRASE removed, and reports the page
delta.  It is a MEASUREMENT of the volume, not a draft: sentences are cut
mechanically, so the result is the size of the material, not the text the
rewrite will produce.

Guards: a sentence is never cut if it carries structure (\\begin, \\end,
\\input, \\label, \\item, \\caption) -- those are measured by leaving them in,
which makes the figure conservative.
"""
import json
import os
import re
import shutil
import subprocess
import sys

import manuscript

HERE = os.path.dirname(os.path.abspath(__file__))
SCRATCH = os.path.join(os.path.dirname(HERE), '.v410_scratch_purge')
MAIN = manuscript.main_file()
ENVPIN = {'SOURCE_DATE_EPOCH': '1577836800', 'FORCE_SOURCE_DATE': '1'}
STRUCT = re.compile(r'\\(begin|end|input|label|item|caption|section|'
                    r'subsection|appendix|bibitem)\b')
SPLIT = re.compile(r'(?<=[.?!])\s+(?=[A-Z\\$])')
ABBR = re.compile(r'(?:e\.g|i\.e|cf|Fig|Figs|Tab|Sec|vs|approx|Ref|No|et al)\.$')


def build(d):
    env = dict(os.environ, **ENVPIN)
    for _ in range(2):
        subprocess.run(['pdflatex', '-interaction=nonstopmode', MAIN], cwd=d,
                       env=env, stdout=subprocess.DEVNULL,
                       stderr=subprocess.DEVNULL)
    log = open(os.path.join(d, MAIN[:-4] + '.log'), errors='ignore').read()
    m = re.search(r'Output written.*?\((\d+) pages', log)
    aux = open(os.path.join(d, MAIN[:-4] + '.aux'), errors='ignore').read()
    ap = re.search(r'\\newlabel\{page:appstart\}\{\{[^}]*\}\{(\d+)\}', aux)
    ap = int(ap.group(1)) if ap else None
    return (int(m.group(1)) if m else None, ap,
            len(re.findall(r'^! ', log, re.M)))


def sentences(par):
    """Split a paragraph into sentences, not breaking on abbreviations."""
    parts = SPLIT.split(par)
    out = []
    for p in parts:
        if out and ABBR.search(out[-1]):
            out[-1] = out[-1] + ' ' + p
        else:
            out.append(p)
    return out


def main():
    hits = json.load(open(os.path.join(HERE, 'purge_hits.json')))
    import purge_inventory as PI
    if os.path.exists(SCRATCH):
        shutil.rmtree(SCRATCH)
    os.makedirs(SCRATCH)
    subprocess.run('cp -a %s/. %s/' % (HERE, SCRATCH), shell=True, check=True)
    base = build(SCRATCH)
    print('baseline %s pages (appendix starts p.%s), %s errors' % base)

    cut_chars = kept_struct = 0
    ncut = 0
    perfile = {}
    for rel in manuscript.section_files():
        p = os.path.join(SCRATCH, rel)
        text = open(p, encoding='utf-8').read()
        pars = text.split('\n\n')
        newpars = []
        for par in pars:
            if par.lstrip().startswith('%'):
                newpars.append(par)
                continue
            keep = []
            for s in sentences(par):
                bad = None
                for name, rx, default in PI.COMPILED:
                    m = rx.search(s)
                    if m and PI.classify(name, default,
                                         s) in ('DELETE', 'REPHRASE'):
                        bad = name
                        break
                if bad and STRUCT.search(s):
                    kept_struct += len(s)
                    bad = None
                if bad:
                    cut_chars += len(s)
                    ncut += 1
                    perfile[rel] = perfile.get(rel, 0) + len(s)
                else:
                    keep.append(s)
            newpars.append(' '.join(keep) if keep else '')
        out = '\n\n'.join(newpars)
        # collapse the blank paragraphs the cut leaves behind
        out = re.sub(r'\n{3,}', '\n\n', out)
        open(p, 'w', encoding='utf-8').write(out)
    after = build(SCRATCH)
    print('after purge %s pages (appendix starts p.%s), %s errors' % after)
    body = re.sub(r'(?<!\\)%.*', '', manuscript.flat().split(
        r'\begin{document}')[-1].split(r'\begin{thebibliography}')[0])
    res = {'baseline_pages': base[0], 'baseline_appstart': base[1],
           'after_pages': after[0], 'after_appstart': after[1],
           'delta_pages': base[0] - after[0],
           'delta_main_pages': (base[1] - after[1]) if after[1] else None,
           'delta_appx_pages': ((base[0] - base[1]) - (after[0] - after[1]))
                               if after[1] else None,
           'sentences_cut': ncut, 'chars_cut': cut_chars,
           'chars_body': len(body),
           'chars_kept_for_structure': kept_struct,
           'per_file_chars': perfile,
           'latex_errors_after': after[2]}
    json.dump(res, open(os.path.join(HERE, 'purge_measure.json'), 'w'),
              indent=1)
    print('purge: %d sentences, %d chars = %.1f%% of the body; '
          'measured %d pages (main %s, appendix %s)'
          % (ncut, cut_chars, 100.0 * cut_chars / len(body),
             res['delta_pages'], res['delta_main_pages'],
             res['delta_appx_pages']))
    shutil.rmtree(SCRATCH)
    return 0


if __name__ == '__main__':
    sys.exit(main())
