#!/usr/bin/env python3
"""Build the event list for the visibility-domain test over ALL stage-1
windows (referee 1, point 1).

v3.84 tested the four unattributed events.  The referee requires the same
test on every stage-1 window, so that its behaviour can be seen on events
we DO attribute: the beta Pictoris CO windows are a positive control for it
(resolved belt emission, which must NOT look like a point source at the
star) and the HD 48370 foreground line is a second negative control.

The test needs one number per event that the frozen release does not carry
for every window -- the sky frequency of the flagged cell.  Its provenance
is recorded per event rather than assumed, because three different sources
are needed:

  measured    the value used in the v3.84 run, reproduced exactly so the
              four already-tested events give byte-comparable answers
  hitlist     the >=5 sigma cell frequencies harvested in v3.61
              (`hitfreqs_v361.json`), restricted to this window
  sibling     for two beta Pictoris blocks that predate the harvest, the
              median peak of the other blocks of the same star and
              transition.  The recurrence analysis shows those peaks agree
              to about one channel once each block's own tuning is removed,
              so this is a justified substitution and it is labelled as one.

Writes vistest_events_v385.json, to be copied to the processing host.
"""
import csv, json, os
import statistics as st

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, 'vistest_events_v385.json')
MSROOT = '/data/SETI/vistest'

CAT = [r for r in csv.DictReader(open(os.path.join(HERE, 'per_target_results_v3.95.csv')))
       if r['stage1_flag'] == 'True']
HITS = {h[0]: h[3] for h in json.load(open(os.path.join(HERE, 'hitfreqs_v361.json')))}
PK = {}
for p in json.load(open(os.path.join(HERE, 'pipeline_peakfreq_v342.json'))):
    PK[(p['eb'], round(min(p['flo'], p['fhi']), 3))] = p
PREV = {}
if os.path.exists(os.path.join(HERE, 'vistest_v384.json')):
    for tag, d in json.load(open(os.path.join(HERE, 'vistest_v384.json'))).items():
        if isinstance(d, dict) and d.get('event'):
            PREV[d['event']['eb']] = d['event']

rows = []
for r in CAT:
    lo, hi = sorted((float(r['flo_GHz']), float(r['fhi_GHz'])))
    freq, src = None, None
    if r['eb'] in PREV:
        freq, src = PREV[r['eb']]['freq_GHz'], 'measured'
    elif (r['eb'], round(lo, 3)) in PK:
        freq, src = PK[(r['eb'], round(lo, 3))]['pk'], 'peakfreq'
    else:
        inw = [f for f in HITS.get(r['eb'], []) if lo <= f <= hi]
        if inw:
            freq, src = float(st.median(inw)), 'hitlist'
    rows.append(dict(
        tag=r['star_name'].split('  Gaia')[0].strip(),
        eb=r['eb'], band=r['band'],
        ms='%s/%s/products/%s_target.ms' % (MSROOT, r['eb'], r['eb']),
        spw=PREV.get(r['eb'], {}).get('spw'),
        chan=PREV.get(r['eb'], {}).get('chan'),
        freq_GHz=freq, freq_source=src,
        flo_GHz=lo, fhi_GHz=hi,
        chanw_Hz=float(r['chanw_Hz']),
        star_snr=float(r['star_snr']), ctrl=float(r['ctrl_max_snr']),
        theta_pb=float(r['theta_pb_arcsec']),
        # The disposition column is populated only where a verdict was
        # recorded; the three unattributed events without a repeat block
        # carry none, and must not be mislabelled as attributed.
        disposition=(r['disposition'] or
                     ('circumstellar/foreground CO' if r['nearest_line'] and
                      r['line_offset_kms'] and abs(float(r['line_offset_kms'])) <= 50
                      else 'unattributed')),
        stage1_local=r['stage1_flag_local'],
    ))

# Fill the gaps from siblings of the same star and band, which the
# recurrence analysis shows agree to about a channel.
by_sb = {}
for d in rows:
    if d['freq_GHz']:
        by_sb.setdefault((d['tag'], d['band']), []).append(d['freq_GHz'])
for d in rows:
    if d['freq_GHz'] is None:
        sib = by_sb.get((d['tag'], d['band']))
        if sib:
            d['freq_GHz'], d['freq_source'] = float(st.median(sib)), 'sibling'

rows.sort(key=lambda d: -d['star_snr'])
missing = [d['tag'] for d in rows if d['freq_GHz'] is None]
json.dump(rows, open(OUT, 'w'), indent=1)

print('%d stage-1 events -> %s' % (len(rows), os.path.basename(OUT)))
for d in rows:
    print('  %-12s B%-2s %-20s f=%s [%-8s] T*=%6.2f  %s'
          % (d['tag'][:12], d['band'], d['eb'],
             ('%.6f' % d['freq_GHz']) if d['freq_GHz'] else '    --      ',
             d['freq_source'] or 'NONE', d['star_snr'], d['disposition']))
print('\nblocks %d | frequency provenance: %s'
      % (len({d['eb'] for d in rows}),
         ', '.join('%s %d' % (s, sum(1 for d in rows if d['freq_source'] == s))
                   for s in ('measured', 'peakfreq', 'hitlist', 'sibling'))))
if missing:
    raise SystemExit('no frequency for: %s' % ', '.join(missing))
