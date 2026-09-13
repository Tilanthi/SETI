#!/usr/bin/env python3
"""Extend the v3.48 obscore category harvest to the two Band 9/10 execution
blocks folded into the catalogue in v3.60.

`obscore_category_v348.json` covered the 102 execution blocks of the frozen
431-window catalogue.  The v3.60 catalogue has 104 blocks, because the two
blocks carrying the Band 9 and Band 10 windows were invisible to the exporter's
band regexp until that bug was fixed.  `v348_calc.py` asserts the harvest is
complete, so it must be extended rather than by-passed.

Read-only against the archive; writes only the JSON it extends (idempotent).
"""
import json, os, sys, warnings
warnings.filterwarnings('ignore')
from astroquery.alma import Alma

HERE = os.path.dirname(os.path.abspath(__file__))
PATH = os.path.join(HERE, 'obscore_category_v348.json')
NEW = ['uid://A002/X11d9ce7/X5257', 'uid://A002/Xbf792a/X26ec']

D = json.load(open(PATH))
todo = [u for u in NEW if u not in D['blocks']]
if not todo:
    print('already present: %d blocks' % len(D['blocks']))
    sys.exit(0)

Alma.archive_url = 'https://almascience.eso.org'
Alma.TIMEOUT = 600
q = ("SELECT DISTINCT asdm_uid, scientific_category, science_keyword "
     "FROM ivoa.obscore WHERE asdm_uid IN (%s)"
     % ','.join("'%s'" % u for u in todo))
t = Alma.query_tap(q).to_table()
got = {str(r['asdm_uid']): dict(
    scientific_category=str(r['scientific_category']),
    science_keyword=str(r['science_keyword'])) for r in t}
missing = [u for u in todo if u not in got]
assert not missing, 'TAP returned nothing for %r' % missing
D['blocks'].update(got)
D['_doc'] += (' v3.60: extended to the two Band 9/10 execution blocks '
              '(%s), 104 of 104 EBs matched.' % ', '.join(todo))
D['harvested_utc_v360'] = __import__('datetime').datetime.utcnow().strftime(
    '%Y-%m-%dT%H:%M:%SZ')
json.dump(D, open(PATH, 'w'), indent=1)
for u in todo:
    print(u, got[u])
print('blocks now %d' % len(D['blocks']))
