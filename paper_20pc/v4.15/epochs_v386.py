#!/usr/bin/env python3
"""Observation epochs for every searched execution block.

Referee 1, point 8: "23 repeat observations" says nothing about what kind
of intermittency has been tested. Repeats two hours apart and repeats nine
years apart are different experiments. This fetches the start time of every
block so the repeat tests can be quoted with their temporal baselines.

`archive_meta_v381.json` carries `t_min` for some blocks and not others, so
the missing ones are queried from the archive on `asdm_uid` -- the column
that indexes an execution block, which `obs_id` does not.
"""
import csv, json, os, sys

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, 'epochs_v386.json')
META = json.load(open(os.path.join(HERE, 'archive_meta_v381.json')))['ebs']
EBS = sorted({r['eb'] for r in
              csv.DictReader(open(os.path.join(HERE,
                                               'per_target_results_v3.99.csv')))})
UID = lambda e: 'uid://' + e.replace('_', '/', 1).replace('_', '/')

have, how = {}, {}
for e in EBS:
    t = (META.get(e) or {}).get('t_min') or []
    v = [float(x) for x in t if str(x) not in ('', 'None')]
    if v:
        have[e] = min(v)
        how[e] = 'block'

if os.path.exists(OUT) and '--force' not in sys.argv:
    _d = json.load(open(OUT))
    have.update(_d.get('mjd', _d))
    how.update(_d.get('source', {}))
    print('%s already holds %d epochs' % (os.path.basename(OUT), len(have)))
else:
    missing = [e for e in EBS if e not in have]
    print('%d of %d blocks already have a start time; querying %d'
          % (len(have), len(EBS), len(missing)))
    if missing:
        from astroquery.alma import Alma
        CH = 60
        for i in range(0, len(missing), CH):
            chunk = missing[i:i + CH]
            inlist = ', '.join("'%s'" % UID(e) for e in chunk)
            q = ("SELECT asdm_uid, t_min FROM ivoa.obscore "
                 "WHERE asdm_uid IN (%s)" % inlist)
            try:
                t = Alma.query_tap(q).to_table()
            except Exception as exc:
                print('  chunk %d failed: %s' % (i // CH, exc))
                continue
            for row in t:
                k = str(row['asdm_uid']).replace('uid://', '').replace('/', '_')
                try:
                    v = float(row['t_min'])
                except (TypeError, ValueError):
                    continue
                if k not in have or v < have[k]:
                    have[k] = v
                    how[k] = 'block'
            print('  %d/%d resolved' % (len(have), len(EBS)))
    # Not every block is indexed by asdm_uid. Where it is not, fall back to
    # the member OUS, whose epoch bounds the block's: repeats in different
    # OUSs are months to years apart and repeats within one are hours to
    # days, which is the distinction the baseline is being quoted for.
    still = [e for e in EBS if e not in have]
    if still:
        from astroquery.alma import Alma
        want = {}
        for e in still:
            for o in (META.get(e) or {}).get('member_ous') or []:
                want.setdefault(str(o), []).append(e)
        ous = sorted(want)
        print('  %d blocks unindexed; falling back to %d member OUS'
              % (len(still), len(ous)))
        got = {}
        for i in range(0, len(ous), 40):
            inlist = ', '.join("'%s'" % o for o in ous[i:i + 40])
            try:
                t = Alma.query_tap("SELECT member_ous_uid, t_min FROM "
                                   "ivoa.obscore WHERE member_ous_uid IN (%s)"
                                   % inlist).to_table()
            except Exception as exc:
                print('   chunk failed: %s' % exc)
                continue
            for row in t:
                k = str(row['member_ous_uid'])
                try:
                    v = float(row['t_min'])
                except (TypeError, ValueError):
                    continue
                if k not in got or v < got[k]:
                    got[k] = v
        nfb = 0
        for o, ebs in want.items():
            if o in got:
                for e in ebs:
                    if e not in have:
                        have[e] = got[o]
                        how[e] = 'ous'
                        nfb += 1
        print('  %d blocks dated from their member OUS' % nfb)
    json.dump({'mjd': have, 'source': how}, open(OUT, 'w'), indent=1)

print('epochs known for %d of %d searched blocks (%d at block level, '
      '%d only at member-OUS level)'
      % (len(have), len(EBS),
         sum(1 for v in how.values() if v == 'block'),
         sum(1 for v in how.values() if v == 'ous')))
if have:
    lo, hi = min(have.values()), max(have.values())
    print('  MJD %.3f to %.3f, a span of %.1f yr' % (lo, hi, (hi - lo) / 365.25))
