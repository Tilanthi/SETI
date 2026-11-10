#!/usr/bin/env python3
"""Equivalence check: visfit_r7x.py with VF_LEGACY=1 must reproduce
visfit_r7.py exactly, leaf value by leaf value.

visfit_r7.py is itself equivalence-checked against visfit_r6.py at zero
offset (vf_equiv_check.py, 468 leaves, 0 differ), so a pass here chains the
corrected estimator back to the round-6 one that produced the published
verdicts: every difference in the new results is then attributable to the
three repairs and to nothing else.

Usage: vf_equiv_r7x.py EVENTS.json DRIFT.json
"""
import json
import os
import subprocess
import sys
import tempfile

BIN = os.path.dirname(os.path.abspath(__file__))
ev, dr = sys.argv[1], sys.argv[2]
tmp = tempfile.mkdtemp(prefix='vfequiv_')
outs = {}
for name, script in (('r7', 'visfit_r7.py'), ('r7x', 'visfit_r7x.py')):
    out = os.path.join(tmp, name + '.json')
    env = dict(os.environ, VF_EVENTS=ev, VF_DRIFT=dr, VF_OUT=out)
    if name == 'r7x':
        env['VF_LEGACY'] = '1'
    else:
        env.pop('VF_LEGACY', None)
    rc = subprocess.call([sys.executable, os.path.join(BIN, script)], env=env)
    if rc != 0:
        raise SystemExit('%s exited %d' % (script, rc))
    outs[name] = json.load(open(out))

# Extra keys in r7x are allowed (dl_arcsec/dm_arcsec/r_arcsec on controls);
# every leaf r7 produces must be present and identical in r7x.
EXEMPT = set()
diff, n = [], 0


def walk(a, b, path):
    global n
    if isinstance(a, dict):
        if not isinstance(b, dict):
            diff.append((path, 'type', type(a), type(b)))
            return
        for k in a:
            if k not in b:
                diff.append((path + '/' + str(k), 'missing in r7x', a[k], None))
            else:
                walk(a[k], b[k], path + '/' + str(k))
    elif isinstance(a, list):
        if not isinstance(b, list) or len(a) != len(b):
            diff.append((path, 'list', len(a), len(b) if isinstance(b, list) else None))
            return
        for i, (x, y) in enumerate(zip(a, b)):
            walk(x, y, '%s[%d]' % (path, i))
    else:
        n += 1
        if path in EXEMPT:
            return
        if isinstance(a, float) and isinstance(b, float):
            if a != b:
                diff.append((path, 'value', a, b))
        elif a != b:
            diff.append((path, 'value', a, b))


walk(outs['r7'], outs['r7x'], '')
print('%d leaf values compared, %d differ' % (n, len(diff)))
for d in diff[:40]:
    print('  DIFF %s: %s  r7=%r  r7x=%r' % d)
print('EQUIVALENCE %s' % ('PASS' if not diff else 'FAIL'))
sys.exit(0 if not diff else 1)
