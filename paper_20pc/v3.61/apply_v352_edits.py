#!/usr/bin/env python3
"""Apply the referee E and F machine-mergeable edit lists to the manuscript.

The edit lists are the product of the translation stage: each entry carries a
locator that occurs exactly once in the `.tex`, the exact replacement LaTeX,
its character cost and the evidence for it.  This script does nothing but
apply them, so that the editor's judgement is spent on the entries themselves
rather than on finding anchors.

Every anchor is required to occur EXACTLY ONCE.  If any does not, nothing is
written at all: a half-applied edit set is worse than none, because the next
run cannot tell which half it is looking at.  That is the same failure mode
`.fuzzysub.py` had, and the reason `.fzsub2.py` was written to fail loudly.

Usage:  apply_v352_edits.py <paper.tex> <edits1.md> [edits2.md ...] [--dry]
        apply_v352_edits.py <paper.tex> <edits.md> --only E1,E2,F14
        apply_v352_edits.py <paper.tex> <edits.md> --skip E53
"""
import re
import sys

SKIP = set()
ONLY = None
args = []
for i, a in enumerate(sys.argv[1:]):
    if a.startswith('--skip='):
        SKIP = set(a.split('=', 1)[1].split(','))
    elif a.startswith('--only='):
        ONLY = set(a.split('=', 1)[1].split(','))
    else:
        args.append(a)
DRY = '--dry' in args
args = [a for a in args if not a.startswith('--')]

texpath = args[0]
tex = open(texpath).read()
orig = tex


def fenced(body, key):
    """Return the fenced block that follows `key:`, or the inline remainder."""
    m = re.search(r'^%s:[ \t]*\n```\n(.*?)\n```' % key, body, re.S | re.M)
    if m:
        return m.group(1)
    m = re.search(r'^%s:[ \t]*(\S.*)$' % key, body, re.M)
    return m.group(1) if m else None


items = []
for path in args[1:]:
    block = open(path).read()
    if '## EDITS' in block:
        block = block.split('## EDITS', 1)[1]
    block = block.split('\n## DECLINED', 1)[0]
    for m in re.finditer(r'^###\s*(\S+)\s*\[(MUST|SHOULD)\]([^\n]*)\n(.*?)(?=\n###|\Z)',
                         block, re.S | re.M):
        eid, level, title, body = m.group(1), m.group(2), m.group(3).strip(), m.group(4)
        anchor = re.search(r'^ANCHOR:[ \t]*(.+)$', body, re.M)
        if not anchor:
            continue
        anchor = anchor.group(1).rstrip('\n')
        target = fenced(body, 'ANCHOR-BLOCK') or anchor
        action = re.search(r'^ACTION:[ \t]*(\S+)', body, re.M)
        action = action.group(1) if action else 'replace'
        new = fenced(body, 'NEW')
        cost = re.search(r'^COST:[ \t]*([+-]?\d+)', body, re.M)
        items.append(dict(src=path.split('/')[-1], id=eid, level=level, title=title,
                          anchor=anchor, target=target, action=action, new=new,
                          cost=int(cost.group(1)) if cost else 0))

if ONLY is not None:
    items = [i for i in items if i['id'] in ONLY]
items = [i for i in items if i['id'] not in SKIP]

# ----------------------------------------------------------------- validate
bad = []
for it in items:
    n_anchor = tex.count(it['anchor'])
    n_target = tex.count(it['target'])
    if n_anchor != 1:
        bad.append((it, 'ANCHOR occurs %d times' % n_anchor))
    elif n_target != 1:
        bad.append((it, 'ANCHOR-BLOCK occurs %d times' % n_target))
    elif it['action'] in ('replace', 'insert-after') and it['new'] is None:
        bad.append((it, 'action %s with no NEW block' % it['action']))
if bad:
    for it, why in bad:
        print('FAIL %s:%s  %s\n     %r' % (it['src'], it['id'], why, it['anchor'][:70]))
    raise SystemExit('%d entries unusable; nothing written' % len(bad))

# overlap check: two entries must not act on the same region
spans = []
for it in items:
    s = tex.index(it['target'])
    spans.append((s, s + len(it['target']), it))
spans.sort()
for (a0, a1, x), (b0, b1, y) in zip(spans, spans[1:]):
    if b0 < a1:
        raise SystemExit('OVERLAP: %s:%s and %s:%s act on the same region'
                         % (x['src'], x['id'], y['src'], y['id']))

# ----------------------------------------------------------------- apply
applied, net = 0, 0
for it in items:
    before = len(tex)
    if it['action'] == 'delete':
        tex = tex.replace(it['target'], '', 1)
    elif it['action'] == 'insert-after':
        tex = tex.replace(it['target'], it['target'] + it['new'], 1)
    else:
        tex = tex.replace(it['target'], it['new'], 1)
    applied += 1
    net += len(tex) - before

# A deleted float leaves a run of blank lines behind; in LaTeX one blank line
# is a paragraph break and more than one is the same thing, but the source
# should not accumulate them.
tex = re.sub(r'\n{4,}', '\n\n\n', tex)

print('edits: %d applied, %d failed | NET %+d characters (list predicted %+d)'
      % (applied, 0, len(tex) - len(orig), sum(i['cost'] for i in items)))
by = {}
for it in items:
    by.setdefault(it['src'], []).append(it['id'])
for k, v in by.items():
    print('  %s: %d (%s)' % (k, len(v), ' '.join(v)))

if DRY:
    print('DRY RUN: nothing written')
else:
    open(texpath, 'w').write(tex)
    print('written', texpath)
