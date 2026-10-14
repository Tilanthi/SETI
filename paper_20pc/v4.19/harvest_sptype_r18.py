#!/usr/bin/env python3
r"""harvest_sptype_r18.py -- freeze SIMBAD's own spectral type and main
identifier for every star carrying an unattributed crossing.

WHY A HARVESTER AND NOT A LIVE QUERY.  The generator that uses these values
must be reproducible from the deposit, and a live query is not.  This script
is run once, writes `hosts_sptype_r18.json`, and `orbit_r18.py` reads only
that file.  The query key is the ledger's own star string, cleaned of the
Gaia designation the ledger appends to two of them, and SIMBAD's resolved
`main_id` is recorded beside it so a wrong resolution is visible.

Usage: harvest_sptype_r18.py
"""
import json
import os
import re
import sys
import urllib.parse
import urllib.request

V = '/workspace/SETI/paper_20pc/v4.18'
OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                   'hosts_sptype_r18.json')
URL = ('https://simbad.u-strasbg.fr/simbad/sim-id?output.format=ASCII'
       '&Ident=%s')
# The ledger writes one star without the sign SIMBAD needs.  The alias is
# declared here rather than silently resolved, and the resolved `main_id` is
# recorded so a wrong alias is visible in the frozen file.
ALIAS = {'BD05 1668': 'BD+05 1668'}

LED = json.load(open(os.path.join(V, 'ledger.json')))['rows']


def query(name):
    u = URL % urllib.parse.quote(name)
    txt = urllib.request.urlopen(u, timeout=60).read().decode('utf-8', 'replace')
    main = re.search(r'^Object (.+?)\s+---', txt, re.M)
    sp = re.search(r'^Spectral type:\s*(\S+)', txt, re.M)
    if sp is None:
        sp = re.search(r'---\s*([OBAFGKMLTY]\d[^ ]*)\s*---', txt)
    return (main.group(1).strip() if main else None,
            sp.group(1).strip() if sp else None,
            len(txt))


out = {}
for r in LED:
    s = r['star']
    if r['attributed']:
        continue
    q = s.split(' Gaia')[0].strip()
    q = ALIAS.get(q, q)
    if q in out:
        continue
    try:
        main, sp, n = query(q)
    except Exception as e:                       # noqa: BLE001
        main, sp, n = None, None, 0
        print('  %-30s QUERY FAILED %s' % (q, e))
    out[q] = dict(query=q, main_id=main, sp_type=sp, n_bytes=n,
                  ledger_names=sorted({x['star'] for x in LED
                                       if ALIAS.get(
                                           x['star'].split(' Gaia')[0].strip(),
                                           x['star'].split(' Gaia')[0].strip())
                                       == q}))
    print('  %-30s %-28s %s' % (q, main, sp))

json.dump(dict(source='SIMBAD sim-id ASCII, queried by harvest_sptype_r18.py',
               hosts=out), open(OUT, 'w'), indent=1)
print('%d hosts -> %s' % (len(out), OUT))
