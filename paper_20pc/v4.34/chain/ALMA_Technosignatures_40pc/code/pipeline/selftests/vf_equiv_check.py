#!/usr/bin/env python3
"""Check that visfit_r7.py reproduces visfit_r6.py exactly when the stellar
offset is zero.

visfit_r7.py adds two things to the round-6 fit: a fitted position taken from
the event instead of hard-coded at the phase centre, and a per-measurement-set
cache of UVW and TIME. Neither may change a fitted number when the offset is
zero. If either did, every completeness figure this campaign reports would be
measured with a different estimator from the one the paper's candidate list was
dispositioned with, and the two could not be compared.

The test runs both scripts over the same events on the same measurement set,
with no l0_arcsec/m0_arcsec fields present at all, and requires every returned
float to agree exactly.

Usage: vf_equiv_check.py <ms> <freq_GHz,...> <theta_pb> <drift_Hz_s>
"""
import json
import os
import subprocess
import sys
import tempfile

ms, freqs, pb, drift = sys.argv[1], sys.argv[2], float(sys.argv[3]), float(sys.argv[4])
tmp = tempfile.mkdtemp(prefix='vfequiv_')
events, drifts = [], {}
for i, f in enumerate(freqs.split(',')):
    eb = 'equiv%02d' % i
    events.append(dict(tag='t%02d' % i, eb=eb, ms=ms,
                       freq_GHz=float(f), theta_pb=pb))
    drifts[eb] = drift
json.dump(events, open(f'{tmp}/ev.json', 'w'))
json.dump(drifts, open(f'{tmp}/dr.json', 'w'))

outs = {}
for name in ('visfit_r6.py', 'visfit_r7.py'):
    out = f'{tmp}/{name}.json'
    env = dict(os.environ, VF_EVENTS=f'{tmp}/ev.json', VF_DRIFT=f'{tmp}/dr.json',
               VF_OUT=out, CASASITECONFIG='/home/fetch-agi/.casa/config.py')
    r = subprocess.run(['python3', f'/data/SETI/bin/{name}'], env=env,
                       capture_output=True, text=True)
    if r.returncode != 0 or not os.path.exists(out):
        print(name, 'FAILED rc=%d' % r.returncode)
        print(r.stdout[-2000:], r.stderr[-2000:])
        raise SystemExit(1)
    outs[name] = json.load(open(out))

# Provenance-only keys visfit_r7.py adds. They record WHICH epoch was used;
# they are not fitted numbers. Listed explicitly so the exemption is visible
# and cannot quietly grow to cover a real difference.
PROVENANCE = {'t_ref_used'}


def strip(d):
    if isinstance(d, dict):
        return {k: strip(v) for k, v in d.items() if k not in PROVENANCE}
    if isinstance(d, list):
        return [strip(x) for x in d]
    return d


a, b = strip(outs['visfit_r6.py']), strip(outs['visfit_r7.py'])
assert sorted(a) == sorted(b), (sorted(a), sorted(b))
ndiff, nchk = 0, 0


def walk(x, y, path):
    global ndiff, nchk
    if isinstance(x, dict):
        assert sorted(x) == sorted(y), (path, sorted(x), sorted(y))
        for k in x:
            walk(x[k], y[k], path + '/' + str(k))
    elif isinstance(x, list):
        assert len(x) == len(y), (path, len(x), len(y))
        for i, (p, q) in enumerate(zip(x, y)):
            walk(p, q, '%s[%d]' % (path, i))
    else:
        nchk += 1
        if x != y:
            ndiff += 1
            print('DIFFER %s: %r vs %r' % (path, x, y))


for k in a:
    walk(a[k], b[k], k)
print('%d events, %d leaf values compared, %d differ' % (len(a), nchk, ndiff))
print('EQUIVALENT' if ndiff == 0 else 'NOT EQUIVALENT')
raise SystemExit(0 if ndiff == 0 else 1)
