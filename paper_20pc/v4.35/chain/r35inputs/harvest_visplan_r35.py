#!/usr/bin/env python3
"""harvest_visplan_r35.py -- (cluster, read-only) freeze the visibility-fit campaign's block plan and the
per-block outcome it recorded (/data/SETI/visfit_r7/plan.json, out/<eb>.json status), so that jx_r35.py can say
why a census crossing was never fitted.  Writes r35inputs/jx_visplan_r35.json.

    python3 harvest_visplan_r35.py VF_ROOT OUT_JSON
"""
import glob, hashlib, json, os, sys
root, out = sys.argv[1], sys.argv[2]
plan = json.load(open(os.path.join(root, 'plan.json')))
st = {}
for f in sorted(glob.glob(os.path.join(root, 'out', '*.json'))):
    if f.endswith('.fit.json'):
        continue
    d = json.load(open(f))
    st[d['eb']] = dict(status=d.get('status', 'ok' if d.get('fit_rc') == 0 else ''),
                       cells=sorted(d.get('fit', {}).keys()) if isinstance(d.get('fit'), dict) else [])
json.dump(dict(harvester='harvest_visplan_r35.py', root=root,
               plan_sha256=hashlib.sha256(open(os.path.join(root, 'plan.json'), 'rb').read()).hexdigest(),
               plan_ebs=sorted({p['eb'] for p in plan}), outcome=st), open(out, 'w'), indent=0)
print('wrote %s: %d planned blocks, %d outcomes' % (out, len(plan), len(st)))
