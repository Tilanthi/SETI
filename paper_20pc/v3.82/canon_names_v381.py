#!/usr/bin/env python3
"""Give every window in the new export a canonical star name.

Two ways the live export loses the star's identity:

1. `export_figdata.py:band_from_dir` matches a band tag only at the END of
   the directory name. The epoch-extension directories are named
   `<star>_B7_EB_X1ae`, so the tag is not at the end, the band is not
   stripped, and the star comes out as "61 Vir B7 EB X1ae". The same
   physical star then appears under as many names as it has execution
   blocks, and every per-star count in the paper -- stars, systems,
   deepest-EIRP-per-star, occurrence -- is inflated.

2. The Option A blocks were beam-matched to the census rather than
   name-matched, so their directories carry a Gaia DR3 source id.

Fix both here rather than in the exporter, so the frozen v3.72 export can
still be rebuilt byte-for-byte from the old code: strip the trailing
`_B<band>_EB_X<hex>`, then resolve what is left against the names already
in the released catalogue, the 168-star census, and finally the census
Gaia source ids and sky positions.

Writes frozen_export_v3.81_survey.json and canon_names_v381.json (the audit trail).
"""
import json, re, csv, math, collections

NEW = '/workspace/SETI/figdata_v381.json'
OLD = '/workspace/SETI/paper_20pc/v3.72/frozen_export_v3.60.json'
CEN = '/workspace/SETI/ranked_master40pc.csv'
WL = '/workspace/SETI/worklist_live.json'
OUT = '/workspace/SETI/frozen_export_v3.81.json'

d = json.load(open(NEW))
old = json.load(open(OLD))
cen = list(csv.DictReader(open(CEN)))
wl = {x['target_dir']: x for x in json.load(open(WL))}
# source_id -> astrometry, from every Option A worklist generation plus the
# live one, so a directory absent from the current worklist still resolves.
import glob as _glob
byid = {}
for _f in sorted(_glob.glob('/workspace/SETI/optionA_worklist_v37*.json')) + [WL]:
    for _x in json.load(open(_f)):
        _sid = str(_x.get('source_id') or '')
        _m = re.search(r'GaiaDR3[_ ](\d+)', str(_x.get('base_name') or ''))
        if not _sid and _m:
            _sid = _m.group(1)
        if _sid and _x.get('ra') and _sid not in byid:
            byid[_sid] = _x

oldnames = sorted({r['star_name'] for r in old['rows']})
STRIP = re.compile(r'^(.*?)[ _]B\d{1,2}[ _]EB[ _]X[0-9a-f]+$', re.I)


def base(n):
    m = STRIP.match(n)
    return (m.group(1) if m else n).strip()


def key(n):
    n = re.sub(r'\bGaia\s*DR3\s*\d+\b', '', n, flags=re.I)
    n = re.sub(r'^(NAME|V\*|V star|\*)\s+', '', n.strip(), flags=re.I)
    return re.sub(r'[^A-Za-z0-9]+', '', n).lower()


bykey = {}
for n in oldnames:
    bykey.setdefault(key(n), n)
for c in cen:
    bykey.setdefault(key(c['name']), c['name'])

bygaia = {str(c['gaia_source_id']): c['name'] for c in cen if c['gaia_source_id']}
cenpos = [(c['name'], float(c['ra']), float(c['dec'])) for c in cen
          if c['ra'] and c['dec']]


def nearest(ra, dec):
    """Closest census star, in arcsec. Used only as a last resort."""
    best, bd = None, 9e9
    cd = math.cos(math.radians(dec))
    for n, r, D in cenpos:
        dd = math.hypot((ra - r) * cd, dec - D) * 3600.0
        if dd < bd:
            best, bd = n, dd
    return best, bd


audit = collections.defaultdict(lambda: collections.Counter())
how = collections.Counter()
unresolved = collections.Counter()

for r in d['rows']:
    tdir = r['target']
    b = base(r['star_name'])
    name = bykey.get(key(b))
    route = 'name'
    if name is None:
        # The worklist is keyed on target_dir, but some directories were
        # created under an earlier naming scheme and are not in the live
        # worklist at all. The Gaia source id is in the directory name
        # itself, so fall back to that and to the Option A worklists, which
        # carry the astrometry I resolved when the list was built.
        w = wl.get(tdir)
        if w is None:
            m = re.search(r'GaiaDR3[_ ](\d+)', r['star_name'])
            if m:
                w = byid.get(m.group(1))
        if w:
            sid = str(w.get('source_id') or '')
            if sid and sid in bygaia:
                name, route = bygaia[sid], 'gaia_id'
            elif w.get('ra') and w.get('dec'):
                cand, sep = nearest(float(w['ra']), float(w['dec']))
                if sep < 30.0:
                    name, route = cand, 'position_%.1fas' % sep
    if name is None:
        unresolved[b] += 1
        name, route = b, 'kept_as_is'
    r['star_name'] = name
    r['canon_route'] = route
    how[route.split('_')[0]] += 1
    audit[name][route] += 1

# ---------------------------------------------------------------- scope
# 195 windows turned out to lie BEYOND 40 pc: they are Option A blocks whose
# ALMA target (e.g. HD 181327 at 47.8 pc) is not a census member, and they
# are exactly the rows whose names would not resolve against the census.
# The paper's sample is defined as the stars within 40 pc, so they do not
# belong in it. They are not waste either: they were searched by the same
# frozen pipeline and never entered any tuning decision, so they make a
# genuinely external null sample. Split, do not discard.
inside = [r for r in d['rows'] if (r.get('dist_pc') or 0) <= 40.0]
outside = [r for r in d['rows'] if (r.get('dist_pc') or 0) > 40.0]
assert len(inside) + len(outside) == len(d['rows'])
bad = [r for r in inside if r['canon_route'] == 'kept_as_is']
assert not bad, 'unresolved star name inside the 40 pc sample: %s' % bad[:3]

d['rows'] = inside
json.dump(d, open(OUT, 'w'))
json.dump({'snapshot': d['snapshot'], 'rows': outside},
          open('/workspace/SETI/outofsample_v381.json', 'w'))
json.dump({'routes': dict(how),
           'unresolved': dict(unresolved),
           'stars': {k: dict(v) for k, v in sorted(audit.items())}},
          open('/workspace/SETI/canon_names_v381.json', 'w'), indent=1)

print('rows total        : %d' % (len(inside) + len(outside)))
print('  within 40 pc    : %d   -> frozen_export_v3.81.json' % len(inside))
print('  beyond 40 pc    : %d   -> outofsample_v381.json (external null)' % len(outside))
print('resolution routes : %s' % dict(how))
print('stars  in sample  : %d  (was %d in the released catalogue)'
      % (len({r['star_name'] for r in inside}), len(oldnames)))
print('EBs    in sample  : %d  (was %d)'
      % (len({r['eb'] for r in inside}), len({r['eb'] for r in old['rows']})))
print('dist range        : %.2f - %.2f pc'
      % (min(r['dist_pc'] for r in inside), max(r['dist_pc'] for r in inside)))
