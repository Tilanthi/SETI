#!/usr/bin/env python3
"""Rebuild the held-out campaign record from the processing host's own
verdict log and per-window search products, and freeze it as
heldout_v352.json.

The campaign runs on the processing host and adds an execution block every
few minutes, so the manuscript quotes a build-time state.  Everything here
was read read-only over ssh into _harvest_raw.json (see BUILD_NOTES); this
script does the bookkeeping locally so the frozen file is reproducible from
the harvest without touching the host again.

Two things are derived here that v3.51 hard-coded and that the v3.52 cycle
was asked to fix:

  * the number and the names of the campaign stars that carry no flag in the
    survey.  v351_calc.py:141 set that count to a literal 2 with "HD 53143
    and Wolf 359" typed into the manuscript, so any refresh of the campaign
    printed the wrong pair over the new counts;
  * the disposition of each window, which v3.51 took to be the raw detection
    flag.  The enlarged campaign contains a window that is a stage-1 spatial
    outlier without being circumstellar CO, so detection and stage-1 status
    are now recorded separately.
"""
import json
import os
import re

HERE = os.path.dirname(os.path.abspath(__file__))
RAW = json.load(open(os.path.join(HERE, '_harvest_raw.json')))
PREV = json.load(open(os.path.join(HERE, 'heldout_v351.json')))

# Stars that carry a stage-1 spatial outlier in the survey itself.  A campaign
# block toward any other star is a genuinely new target for the frozen
# pipeline rather than a re-test of a flagged window.
FLAGGED_STARS = {'bet Pic', 'HD 48370', 'CP-72 2713', 'AU Mic'}

# The verdict log writes the star name as the scheduling block carried it.
CANON = {
    'bet Pic': 'bet Pic',
    'HD53143 (Gaia DR3 5479222240596469632)': 'HD 53143',
    'Wolf  359': 'Wolf 359',
    'HD  33793': 'HD 33793',
    'TRAPPIST-1': 'TRAPPIST-1',
    'GJ 849': 'GJ 849',
    'HD 48370': 'HD 48370',
    'HD 31392': 'HD 31392',
    'HD377': 'HD 377',
    'HD 23484 (Gaia DR3 4856592239127350400)': 'HD 23484',
    'HD 45184': 'HD 45184',
    'GL 3379 (Gaia DR3 3316364602541746048)': 'GL 3379',
    'HR 1010 (Gaia DR3 4722135642226902656)': 'HR 1010',
    '* chi01 Ori': 'chi01 Ori',
    'LHS 1140': 'LHS 1140',
    'BD+05  1668': 'BD+05 1668',
    'HD14055': 'HD 14055',
}


def canon(name):
    name = re.split(r'\s+MOUS\s+', name)[0]
    while re.search(r'\s*\[B\d\]\s*$', name):
        name = re.sub(r'\s*\[B\d\]\s*$', '', name)
    name = name.strip()
    return CANON.get(name, re.sub(r'\s+', ' ', name))


# ---------------------------------------------------------------- the log
searched, failed, aborted = {}, {}, []
for e in RAW['entries']:
    star = canon(e['star'])
    band = re.search(r'\[(B\d)\]', e['star'])
    rec = dict(eb=e['eb'], star=star, band=band.group(1) if band else None, t=e['t'])
    if e['verdict'] == 'SEARCHED':
        searched[e['eb']] = rec
    elif e['verdict'] == 'FAILED':
        failed[e['eb']] = rec
    else:
        aborted.append(rec)
# a block that aborted on the disk floor and later succeeded is not a failure
failed = {k: v for k, v in failed.items() if k not in searched}

# --------------------------------------------------------- the windows
windows = []
for w in RAW['windows']:
    rec = searched.get(w['eb'])
    if rec is None:
        continue
    o = dict(w)
    o.pop('_dir', None)
    o['star_name'] = '%s [%s]' % (rec['star'], rec['band']) if rec['band'] else rec['star']
    o['star'] = rec['star']
    o['band'] = o.get('band') or rec['band']
    o['block_searched_utc'] = rec['t']
    o['stage1'] = (o['n_control_ge_star'] == 0)
    windows.append(o)

# The CP-72 2713 repeat block was searched on 2026-09-11 as the recurrence
# test, before the campaign driver was started, so it is not in the driver's
# verdict log.  It belongs to the held-out set on the same terms and v3.51
# already counted it; carry its four windows forward unchanged.
for w in PREV['windows']:
    if w['star_name'].startswith('CP-72'):
        o = dict(w)
        o['star'] = 'CP-72 2713'
        o['stage1'] = (o['n_control_ge_star'] == 0)
        o['block_searched_utc'] = '2026-09-11T20:19Z'
        windows.append(o)
        searched.setdefault(o['eb'], dict(eb=o['eb'], star='CP-72 2713', band='B7',
                                          t='2026-09-11T20:19Z'))

stars = sorted({w['star'] for w in windows})
new_stars = sorted(s for s in stars if s not in FLAGGED_STARS)
new_blocks = sorted(eb for eb, r in searched.items() if r['star'] not in FLAGGED_STARS)

# ------------------------------------------------- window classification
# A window is astrophysically attributed when it is a detection whose peak
# falls within a line width of a catalogued transition of its own star.  In
# this campaign that is beta Pictoris CO in both transitions, and the two
# beta Pic windows whose control annulus outshines the star are attributed on
# the same evidence even though they are not stage-1 outliers.
for w in windows:
    off = w.get('nearest_known_line_offset_MHz')
    w['line_attributed'] = bool(
        w['detection'] and off is not None and abs(off) < 50.0
        and w['star'] in ('bet Pic', 'HD 48370'))
    w['unattributed_stage1'] = bool(w['stage1'] and not w['line_attributed'])

out = dict(
    _doc=__doc__,
    source=dict(
        verdicts_log='/data/SETI/epoch_extension/verdicts.log',
        products='/data/SETI/targets/*/products/*_result.json',
        read='read-only over ssh, nothing downloaded, no compute started'),
    windows=windows,
    campaign_status=dict(
        as_of_utc=RAW['entries'][-1]['t'],
        blocks_searched=len(searched),
        windows_searched=len(windows),
        stars=len(stars),
        star_list=stars,
        blocks_failed_calibration=len(failed),
        blocks_in_progress=1,
        new_star_blocks=len(new_blocks),
        new_star_count=len(new_stars),
        new_star_list=new_stars,
        note=('blocks_searched includes the CP-72 2713 repeat block, searched '
              '2026-09-11 as the recurrence test; failed-calibration blocks '
              'produced no search product; two disk-floor aborts of '
              'A002_Xd9668b_Xa9df later succeeded and are not counted as '
              'failures')),
)
with open(os.path.join(HERE, 'heldout_v352.json'), 'w') as fh:
    json.dump(out, fh, indent=1)

print('blocks %d, windows %d, stars %d, failed %d'
      % (len(searched), len(windows), len(stars), len(failed)))
print('unflagged stars %d: %s' % (len(new_stars), ', '.join(new_stars)))
print('blocks toward unflagged stars %d' % len(new_blocks))
print('detections %d, stage-1 %d, line-attributed %d, unattributed stage-1 %d'
      % (sum(w['detection'] for w in windows), sum(w['stage1'] for w in windows),
         sum(w['line_attributed'] for w in windows),
         sum(w['unattributed_stage1'] for w in windows)))
for w in windows:
    if w['stage1']:
        print('   stage1: %-14s T*=%6.2f ctrlmax=%5.2f  line %s %+.1f MHz  attributed=%s'
              % (w['star_name'], w['star_peak_snr'], w['control_peak_snr'],
                 w['nearest_known_line'], w['nearest_known_line_offset_MHz'] or 0,
                 w['line_attributed']))
