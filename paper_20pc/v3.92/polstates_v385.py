#!/usr/bin/env python3
"""Re-query ALMA's polarisation states for EVERY searched execution block.

`polstates_v351.json` holds 104 blocks -- the whole sample at v3.51 -- and
the manuscript grew to 404 without the query being re-run, so a statement
of the form "all N of the N searched blocks deliver both parallel hands"
was true of 26 per cent of the sample and typeset as though it covered all
of it.  This is the same failure as the 88.2 GHz literal and the 104+346
arithmetic: a number from a frozen input that a later round moved past.

Queries `ivoa.obscore.pol_states` over the execution-block UIDs in the
released catalogue, writes `polstates_v385.json`, and asserts that every
block the old file covered still gives the same answer.
"""
import csv, json, os, sys

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, 'polstates_v385.json')

EBS = sorted({r['eb'] for r in
              csv.DictReader(open(os.path.join(HERE, 'per_target_results_v3.92.csv')))})
UID = lambda e: 'uid://' + e.replace('_', '/', 1).replace('_', '/')

if os.path.exists(OUT) and '--force' not in sys.argv:
    got = json.load(open(OUT))
    print('%s already holds %d blocks (use --force to re-query)'
          % (os.path.basename(OUT), len(got)))
else:
    from astroquery.alma import Alma
    got = {}
    CH = 60
    UIDS = [UID(e) for e in EBS]
    for i in range(0, len(UIDS), CH):
        chunk = UIDS[i:i + CH]
        inlist = ', '.join("'%s'" % u for u in chunk)
        # The execution block appears in obscore as `asdm_uid`, not
        # `obs_id` (which is the member OUS). Querying obs_id returns
        # nothing at all, which is how this was caught.
        q = ("SELECT asdm_uid, pol_states FROM ivoa.obscore "
             "WHERE asdm_uid IN (%s)" % inlist)
        try:
            t = Alma.query_tap(q).to_table()
        except Exception as exc:                       # network, not logic
            print('  chunk %d failed: %s' % (i // CH, exc))
            continue
        for row in t:
            k = str(row['asdm_uid'])
            v = str(row['pol_states'])
            if v not in got.setdefault(k, []):
                got[k].append(v)
        print('  %d/%d blocks resolved' % (len(got), len(UIDS)))
    json.dump(got, open(OUT, 'w'), indent=1)

OLD = json.load(open(os.path.join(HERE, 'polstates_v351.json')))
both = sum(1 for v in got.values()
           if all('XX' in str(s) and 'YY' in str(s) for s in
                  (v if isinstance(v, list) else [v])))
cross = sum(1 for v in got.values()
            if any('XY' in str(s) or 'YX' in str(s) for s in
                   (v if isinstance(v, list) else [v])))
missing = [e for e in EBS if UID(e) not in got]

# The 104 blocks the old file covered must not change their answer.
disagree = []
for e, v in OLD.items():
    if e in got:
        o = all('XX' in str(s) and 'YY' in str(s) for s in
                (v if isinstance(v, list) else [v]))
        n = all('XX' in str(s) and 'YY' in str(s) for s in
                (got[e] if isinstance(got[e], list) else [got[e]]))
        if o != n:
            disagree.append(e)

print('searched blocks %d | resolved %d | unresolved %d'
      % (len(EBS), len(got), len(missing)))
print('both parallel hands %d of %d resolved (%.1f per cent)'
      % (both, len(got), 100.0 * both / max(len(got), 1)))
print('cross-hand products %d' % cross)
print('old file: %d blocks, %d of them disagree now' % (len(OLD), len(disagree)))
if missing[:5]:
    print('  first unresolved:', missing[:5])
assert not disagree, disagree
