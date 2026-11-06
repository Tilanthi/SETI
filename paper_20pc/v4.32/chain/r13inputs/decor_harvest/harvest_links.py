#!/usr/bin/env python3
"""Harvest, for every member OUS behind the released catalogue, the list of
small per-execution-block quality files the ALMA archive exposes
individually (QA0 and QA2 reports).  Writes qa_links.json; no bulk data.
"""
import json
import os
import sys
import warnings
from concurrent.futures import ThreadPoolExecutor

warnings.filterwarnings('ignore')
from astroquery.alma import Alma                                # noqa: E402

HERE = os.path.dirname(os.path.abspath(__file__))
M = json.load(open(os.path.join(HERE, 'map.json')))['mous2eb']
OUT = os.path.join(HERE, 'qa_links.json')
DONE = json.load(open(OUT)) if os.path.exists(OUT) else {}


def one(mous):
    if mous in DONE:
        return mous, DONE[mous]
    a = Alma()
    a.archive_url = 'https://almascience.eso.org'
    try:
        t = a.get_data_info(mous, expand_tarfiles=True)
    except Exception as exc:                                     # noqa: BLE001
        return mous, {'error': '%s: %s' % (type(exc).__name__, exc)}
    rec = {'qa0': [], 'qa2': [], 'n_files': len(t)}
    for r in t:
        u = str(r['access_url'])
        n = u.split('/')[-1]
        if 'qa0_report' in n:
            rec['qa0'].append([n, int(r['content_length'] or 0)])
        elif 'qa2_report' in n:
            rec['qa2'].append([n, int(r['content_length'] or 0)])
    return mous, rec


todo = [m for m in sorted(M) if m not in DONE and m != 'null']
print('%d member OUS to query (%d cached)' % (len(todo), len(DONE)))
with ThreadPoolExecutor(max_workers=6) as ex:
    for i, (m, rec) in enumerate(ex.map(one, todo)):
        DONE[m] = rec
        if i % 10 == 0:
            print('  %d/%d' % (i, len(todo)))
            sys.stdout.flush()
            json.dump(DONE, open(OUT, 'w'), indent=1)
json.dump(DONE, open(OUT, 'w'), indent=1)
nq2 = sum(1 for v in DONE.values() if v.get('qa2'))
nq0 = sum(1 for v in DONE.values() if v.get('qa0'))
print('%d member OUS: %d expose a QA2 report, %d expose QA0 reports'
      % (len(DONE), nq2, nq0))
