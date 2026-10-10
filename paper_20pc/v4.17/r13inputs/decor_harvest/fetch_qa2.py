#!/usr/bin/env python3
"""Download the (70 kB) QA2 report of every member OUS that exposes one."""
import json
import os
import urllib.request
from concurrent.futures import ThreadPoolExecutor

HERE = os.path.dirname(os.path.abspath(__file__))
L = json.load(open(os.path.join(HERE, 'qa_links.json')))
D = os.path.join(HERE, 'qa2')
os.makedirs(D, exist_ok=True)
jobs = []
for mous, rec in sorted(L.items()):
    for n, sz in rec.get('qa2', []):
        if not os.path.exists(os.path.join(D, n)):
            jobs.append(n)


def get(n):
    url = 'https://almascience.eso.org/dataPortal/' + n
    try:
        with urllib.request.urlopen(url, timeout=120) as r:
            d = r.read()
        open(os.path.join(D, n), 'wb').write(d)
        return n, len(d)
    except Exception as exc:                                     # noqa: BLE001
        return n, '%s: %s' % (type(exc).__name__, exc)


print('%d to fetch' % len(jobs))
with ThreadPoolExecutor(max_workers=6) as ex:
    for n, r in ex.map(get, jobs):
        if not isinstance(r, int):
            print('FAIL', n, r)
print('%d pdfs on disk' % len(os.listdir(D)))
