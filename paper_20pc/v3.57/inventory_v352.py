#!/usr/bin/env python3
"""Inventory: for every edit in the v3.54 EDITS lists, decide APPLIED / PENDING / AMBIG.

Test order:
  1. ANCHOR-BLOCK (or ANCHOR line) still present verbatim  -> PENDING
  2. NEW text present (whitespace-normalised)              -> APPLIED
  3. neither                                               -> AMBIG (inspect by hand)
"""
import re, sys, json

TEX = '/workspace/SETI/paper_20pc/v3.57/technosignatures_20pc_v3.57.tex'
FILES = ['/shared/ASTRA/reviews/v352_referee_E_EDITS.md',
         '/shared/ASTRA/reviews/v352_referee_F_EDITS.md']

tex = open(TEX).read()
norm = lambda s: re.sub(r'\s+', ' ', s).strip()
texn = norm(tex)


def parse(path):
    block = open(path).read()
    if '## EDITS' in block:
        block = block.split('## EDITS', 1)[1]
    out = []
    for m in re.finditer(r'^###\s+(\S+)\s*\[(MUST|SHOULD|DECLINE[^\]]*)\]([^\n]*)\n(.*?)(?=\n###\s|\Z)',
                         block, re.S | re.M):
        eid, lvl, title, body = m.group(1), m.group(2), m.group(3).strip(), m.group(4)
        a = re.search(r'^ANCHOR:\s*(.+)$', body, re.M)
        ab = re.search(r'^ANCHOR-BLOCK:\s*\n```\n(.*?)\n```', body, re.S | re.M)
        nw = re.search(r'^NEW:\s*\n```\n(.*?)\n```', body, re.S | re.M)
        ac = re.search(r'^ACTION:\s*(.+)$', body, re.M)
        c = re.search(r'^COST:\s*([+-]?\d+)', body, re.M)
        out.append(dict(file=path.split('/')[-1][14:15], id=eid, lvl=lvl, title=title,
                        anchor=a.group(1).strip() if a else None,
                        ablock=ab.group(1) if ab else None,
                        new=nw.group(1) if nw else None,
                        action=ac.group(1).strip() if ac else None,
                        cost=int(c.group(1)) if c else 0))
    return out


items = []
for f in FILES:
    items += parse(f)

res = []
for it in items:
    loc = it['ablock'] if it['ablock'] else it['anchor']
    state = 'AMBIG'
    detail = ''
    if loc:
        nloc = norm(loc)
        nloc_ct = texn.count(nloc)
        if nloc_ct >= 1:
            state = 'PENDING'
            detail = f'anchor x{nloc_ct}'
        elif it['new'] and norm(it['new']) and texn.count(norm(it['new'])) >= 1:
            state = 'APPLIED'
            detail = 'new present'
        elif it['action'] and 'delete' in it['action'].lower():
            state = 'APPLIED'
            detail = 'anchor gone, action=delete'
        else:
            state = 'AMBIG'
            detail = 'anchor gone, new absent'
    res.append((it['file'], it['id'], it['lvl'], state, it['cost'], detail, it['title'][:70]))

for r in sorted(res, key=lambda x: (x[0], int(re.sub(r'\D', '', x[1]) or 0))):
    print(f'{r[0]} {r[1]:<6} {r[2]:<8} {r[3]:<8} cost{r[4]:+6d}  {r[5]:<24} {r[6]}')

from collections import Counter
c = Counter(r[3] for r in res)
print('\nTOTALS', dict(c), 'of', len(res))
print('pending cost', sum(r[4] for r in res if r[3] == 'PENDING'))
json.dump([dict(zip(['file', 'id', 'lvl', 'state', 'cost', 'detail', 'title'], r)) for r in res],
          open('/workspace/SETI/paper_20pc/v3.57/inventory_v352.json', 'w'), indent=1)
