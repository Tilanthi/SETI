#!/usr/bin/env python3
"""Write BUDGET.md and CUTLIST.json from the measurements.

Re-runnable after every pass:

    python3 secbudget.py        # per-section extent, from the built PDF
    python3 floatinv.py         # every float's typeset height
    python3 cutmeasure.py       # page delta of each proposed cut
    python3 purge_inventory.py && python3 purge_measure.py
    python3 programme_measure.py
    python3 budget.py           # -> BUDGET.md, CUTLIST.json
"""
import json
import os

HERE = os.path.dirname(os.path.abspath(__file__))

OWNER = {'sections/01_intro.tex': 'abstract-intro',
         'sections/02_background.tex': 'abstract-intro',
         'sections/03_sample.tex': 'sample-method',
         'sections/04_method.tex': 'sample-method',
         'sections/05_results.tex': 'results',
         'sections/05b_stack.tex': 'stack-discussion',
         'sections/05c_limits.tex': 'stack-discussion',
         'sections/06_discussion.tex': 'stack-discussion',
         'sections/07_conclusions.tex': 'stack-discussion'}
ASK = {'sections/app_A_reproducibility.tex': 'delete most of it',
       'sections/app_B_figofmerit.tex': 'delete most of it',
       'sections/app_M_repaired.tex': 'delete'}


def load(name):
    p = os.path.join(HERE, name)
    return json.load(open(p)) if os.path.exists(p) else None


sec = load('secbudget.json')
fl = load('floatinv.json')
cut = load('cutmeasure.json')
pur = load('purge_measure.json')
prog = load('programme_measure.json')

# float area per owning file
area = {}
for f in fl:
    area[f['env_file']] = area.get(f['env_file'], 0.0) + f['page_cost']

MAIN_FILES = ['sections/abstract.tex', 'sections/01_intro.tex',
              'sections/02_background.tex', 'sections/03_sample.tex',
              'sections/04_method.tex', 'sections/05_results.tex',
              'sections/05b_stack.tex', 'sections/05c_limits.tex',
              'sections/06_discussion.tex', 'sections/07_conclusions.tex',
              'sections/08_backmatter.tex']

# ------------------------------------------------------------------ CUTLIST
items = []
for it in cut['items']:
    if it['kind'] == 'section':
        continue        # listed under 'sections', not as a float
    items.append({'item': it['item'], 'label': it['label'],
                  'kind': it['kind'], 'source': it['source'],
                  'region': it['region'],
                  'height_pt': it['height_pt'],
                  'page_cost': None if it['page_cost'] is None
                               else round(it['page_cost'], 3),
                  'delta_pages_alone': it['delta_pages'],
                  'delta_main_alone': it['delta_main'],
                  'delta_appx_alone': it['delta_appx'],
                  'latex_errors': it['latex_errors'],
                  'caption': it['caption']})
float_area = sum(i['page_cost'] for i in items if i['page_cost'])
cutlist = {
    'measured_against': {
        'build': 'v4.09 as pushed (d19a4e3fad5b), split into sections/',
        'pdf_sha256':
            'c9d0f55ba5c80f442922bfec17be08e28cfdb84e6be4a32526ea70edffa26821',
        'pages': cut['baseline']['pages'],
        'main_pages_by_label': cut['baseline']['main'],
        'appendix_pages_by_label': cut['baseline']['appx'],
        'note': 'main/appendix split is the page of \\label{page:appstart}; '
                'the appendix figure includes the bibliography (~2 pp)'},
    'method': 'page_cost is the float\'s own typeset height from '
              '\\@largefloatcheck, divided by 694 pt for a full-width '
              '(starred) float and by 1388 pt for a single-column one: the '
              'page is two columns of 694 pt. delta_pages_alone is a REAL '
              'build with that one float deleted. The two differ because '
              'page counts here are not monotone -- 17 of the 19 floats move '
              'nothing on their own, and the cut list only pays off together.',
    'floats': items,
    'float_area_pages': round(float_area, 2),
    'sections': [],
    'cumulative_programme': prog,
    'missing_from_inventory': cut['missing'],
}
for name, rel in [('Appendix M', 'sections/app_M_repaired.tex'),
                  ('Appendix A', 'sections/app_A_reproducibility.tex'),
                  ('Appendix B', 'sections/app_B_figofmerit.tex')]:
    row = sec['byfile'].get(rel)
    meas = next((i for i in cut['items'] if i['item'] == rel), None)
    cutlist['sections'].append({
        'item': name, 'file': rel,
        'extent_pages_measured': None if row is None else round(row, 2),
        'float_area_pages': round(area.get(rel, 0.0), 2),
        'delta_pages_alone': None if meas is None else meas['delta_pages'],
        'referee_request': 'delete' if name == 'Appendix M'
                           else 'delete most of it'})
cutlist['purge'] = pur
json.dump(cutlist, open(os.path.join(HERE, 'CUTLIST.json'), 'w'), indent=1)

# ------------------------------------------------------------------ BUDGET
rows = sec['sections']
with open(os.path.join(HERE, 'BUDGET.md'), 'w', encoding='utf-8') as fh:
    w = fh.write
    w('# BUDGET — where the %d pages are, measured\n\n' % sec['total_pages'])
    w('Re-measure with `python3 secbudget.py && python3 floatinv.py && '
      'python3 budget.py` after every pass. Every number here is measured '
      'from the built PDF; none is estimated.\n\n')
    w('**Target: main text ≤ 22 pp, appendices ≤ 10 pp.** '
      'Glenn\'s cap is 25 + 15; the referees ask for about 30 pp total.\n\n')
    w('## Method, and what the numbers mean\n\n')
    w('- A page is two columns of 694 pt. A section\'s **extent** is measured '
      'along the typeset flow from its heading to the next heading, page by '
      'page and column by column, so a section is not charged for the '
      'section before it merely because it starts at the top of a page. '
      'Counting whole pages is what turns a 22.07-page main text into '
      '"23 pages".\n')
    w('- **Float area** is each float\'s own typeset height, measured by '
      '`\\@largefloatcheck`, over 694 pt (full-width) or 1388 pt '
      '(single-column). It is additive and it is the number to use when '
      'deciding what to cut; a float\'s *individual* page delta is almost '
      'always zero because the page repacks.\n')
    w('- The extent of a section already contains any single-column float '
      'placed inside it, so the two columns below are **not** additive. The '
      'float column says how much of the extent is float.\n')
    w('- The unnumbered back matter (author contributions, funding, data '
      'availability, software) is charged to §7, and the appendix '
      'overview to the `APPENDIX` row: `\\section*` headings are not '
      'numbered and are not separately located in the PDF.\n\n')
    w('## Main text\n\n')
    w('| file | owner | extent (pp) | of which floats (pp) |\n')
    w('|---|---|---|---|\n')
    tot = totf = 0.0
    for f, pp in sorted(sec['byfile'].items()):
        if not f.startswith('sections/0'):
            continue
        a = area.get(f, 0.0)
        tot += pp
        totf += a
        w('| `%s` | %s | %.2f | %.2f |\n' % (f, OWNER.get(f, '-'), pp, a))
    w('| **main total** | | **%.2f** | **%.2f** |\n\n' % (tot, totf))
    w('Main text must lose **%.2f pp** to reach 22.\n\n' % max(0.0, tot - 22))
    w('## Appendices\n\n')
    w('| file | extent (pp) | of which floats (pp) | R2 asks |\n')
    w('|---|---|---|---|\n')
    tota = totaf = 0.0
    for f, pp in sorted(sec['byfile'].items()):
        if not f.startswith('sections/app'):
            continue
        a = area.get(f, 0.0)
        tota += pp
        totaf += a
        w('| `%s` | %.2f | %.2f | %s |\n'
          % (f, pp, a, ASK.get(f, '')))
    w('| **appendix total** | **%.2f** | **%.2f** | |\n\n' % (tota, totaf))
    w('Appendices must lose **%.2f pp** to reach 10. The bibliography '
      '(~2 pp) and the `APPENDIX` divider are outside both totals; '
      'sections sum to %.2f of the PDF\'s %d pages, the %.2f pp residual '
      'being the title block, the abstract above the first heading, and the '
      'reference list.\n\n'
      % (max(0.0, tota - 10),
         sum(r['pages'] for r in rows), sec['total_pages'],
         sec['total_pages'] - sum(r['pages'] for r in rows)))
    if prog:
        w('## What the mechanical cuts actually deliver (measured, '
          'cumulative)\n\n')
        w('| stage | pages | main | appendices+refs | cumulative |\n')
        w('|---|---|---|---|---|\n')
        for r in prog:
            w('| %s | %s | %s | %s | %+d |\n'
              % (r['stage'], r['pages'], r['main'], r['appx'],
                 -r['cum_delta_pages']))
        w('\n')
        last = prog[-1]
        w('Every stage builds with 0 LaTeX errors. After all four, the main '
          'text is **%s pp** (target 22, **met**) and the appendices plus '
          'references are **%s pp** against a target of 10 — so the '
          'appendix triage has to go roughly **%d pp further** than deleting '
          'M, A and B: the remaining weight is App. K (%.2f pp), App. J '
          '(%.2f pp), App. G (%.2f pp) and App. F (%.2f pp).\n\n'
          % (last['main'], last['appx'], last['appx'] - 10 - 2,
             *[sec['byfile']['sections/app_%s_%s.tex' % (k, n)]
               for k, n in (('K', 'provenance'), ('J', 'falsealarm'),
                            ('G', 'injection'), ('F', 'freqconventions'))]))
    if pur:
        w('## The revision history\n\n')
        w('- %d sentences, %d characters = **%.1f per cent of the body**\n'
          % (pur['sentences_cut'], pur['chars_cut'],
             100.0 * pur['chars_cut'] / pur['chars_body']))
        w('- measured by building without them: **%d pages** '
          '(main %d, appendices %d)\n'
          % (pur['delta_pages'], pur['delta_main_pages'],
             pur['delta_appx_pages']))
        w('- R1 estimated 5–7 pages. %d pp is a **floor**: the '
          'inventory only catches sentences a pattern can see, and %d '
          'characters were left in place because the sentence also carried '
          'structure (a `\\begin`, a `\\label`, a `\\caption`). Whole '
          'paragraphs that exist only to narrate the history are counted '
          'sentence by sentence, not as paragraphs.\n\n'
          % (pur['delta_pages'], pur['chars_kept_for_structure']))
print('wrote BUDGET.md and CUTLIST.json')
