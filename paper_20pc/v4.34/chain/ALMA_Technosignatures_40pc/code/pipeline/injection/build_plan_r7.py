#!/usr/bin/env python3
"""Build the round-7 re-fit plan: every crossing that has ever been fitted in
the visibility domain, re-fitted once with the corrected estimator.

Scope, and why it is all 44 rather than the nine the audit flagged:

  * defect 1 (the fitted position) bites only the nine;
  * defects 2 and 3 (calibrator rows pooled into the fit, and a control
    annulus built from a hard-coded 12 m primary beam with no
    synthesised-beam floor) bite EVERY fit.  On the one block whose
    calibrated measurement set survived, HD 48370 `A002_Xc26103_X155a`,
    the two together move Re/sigma from 5.93 to 11.92 and Im/sigma from
    2.74 to 4.27 -- enough to change its verdict.

So a mixed set of nine corrected and thirty-five uncorrected fits could not
be scored by one criterion.  All 44 are re-fitted, plus the five blocks whose
calibration failed in round 6 (their ten crossings are currently recorded as
untestable; if they calibrate this time the coverage improves, and if they do
not, nothing is lost).

Units are execution blocks.  A block whose calibrated target measurement set
is already on disk is fitted in place and never re-fetched or deleted -- the
P90 campaign is using some of those.

Usage: build_plan_r7.py > plan_summary.txt
"""
import glob
import json
import os

ROOT = '/data/SETI/visfit_r7'
R6PLAN = '/data/SETI/visfit_r6/plan.json'
R6RES = '/data/SETI/visfit_r6/visfit_r6_result.json'
V385 = '/data/SETI/visfit_r7/visfit_all_v385.json'
FINAL44 = '/data/SETI/visfit_r7/final44.json'

# Star parameters: the exact values the pipeline passed to the extractor.
WORKLISTS = (glob.glob('/data/SETI/mine2026/*.json')
             + glob.glob('/data/SETI/mine2026/lane_*/worklist.json')
             + glob.glob('/data/SETI/epoch_extension/*.json')
             + glob.glob('/data/SETI/epoch_extension/*/worklist.json'))


def star_of(item):
    return dict(ra_deg=float(item['ra']), dec_deg=float(item['dec']),
                pmra=float(item['pmra']), pmdec=float(item['pmdec']),
                parallax=float(item['parallax']), rv_kms=0.0, epoch=2016.0)


def main():
    by_eb_item, by_name_item = {}, {}
    for f in WORKLISTS:
        try:
            d = json.load(open(f))
        except Exception:
            continue
        if not isinstance(d, list):
            continue
        for it in d:
            if not isinstance(it, dict) or 'ra' not in it or 'eb' not in it:
                continue
            by_eb_item.setdefault(it['eb'], it)
            bn = it.get('base_name') or it.get('star_name')
            if bn:
                by_name_item.setdefault(bn, it)

    # ---- events -------------------------------------------------------
    events_by_eb = {}
    r6plan = json.load(open(R6PLAN))
    for u in r6plan:
        events_by_eb.setdefault(u['eb'], []).extend(u['events'])
    v385 = json.load(open(V385))
    for key, r in v385.items():
        ev = dict(r['event'])
        ev.pop('ms', None)
        ev['drift_Hz_s'] = r['drift_Hz_s']
        events_by_eb.setdefault(ev['eb'], []).append(ev)

    # star name per EB for the blocks with no worklist entry of their own
    fallback_name = {'A002_Xf5d76d_X32f1': 'bet Pic',
                     'A002_Xff0235_X4a6d': 'CP-72 2713'}
    fallback_mous = {'A002_Xf5d76d_X32f1': 'uid://A001/X158f/X7c5',
                     'A002_Xff0235_X4a6d': 'uid://A001/X2d20/X2e25'}
    # ------------------------------------------------------------------
    # These are the ARCHIVE's own EB sizes, not placeholders.  The value
    # for A002_Xff0235_X4a6d used to read 3000000000 -- a 3 GB guess for a
    # 49.3 GB execution block.  epoch_extend.py:353 turns a work item's
    # size into a download budget, SETI_MAX_TARGET_DOWNLOAD_GB =
    # max(10.0, gb + 5); 3 + 5 = 8 -> 10, so calibrate_generic refused the
    # block's only EB in 2 s, four times, with 90-121 GB free:
    #   SKIPPING ...X4a6d.asdm.sdm.tar (49.3 GB): would exceed this
    #   target's 10 GB download budget
    # A wrong size does not look like a disk failure and does not look
    # like a bug; it looks like a block that will not calibrate.
    fallback_size = {'A002_Xf5d76d_X32f1': 13657802752,
                     'A002_Xff0235_X4a6d': 49461726208}
    # A fallback size must be an archive size.  Anything round enough to be
    # a guess, or small enough to make max(10.0, gb+5) bind at 10, is a
    # placeholder and must fail the build rather than the block.
    for _eb, _sz in fallback_size.items():
        assert _sz / 1e9 + 5 > 10.0, (
            'fallback_size[%s] = %d is below the 10 GB download-budget '
            'floor and will silently starve the fetch' % (_eb, _sz))
        assert _sz % 1000000000 != 0, (
            'fallback_size[%s] = %d is a round number, i.e. a placeholder, '
            'not an archive size' % (_eb, _sz))

    existing_ms = {}
    for p in glob.glob('/data/SETI/targets/*/products/*_target.ms'):
        existing_ms[os.path.basename(p).replace('_target.ms', '')] = p

    # ------------------------------------------------------------------
    # COVERAGE CHECK.  events_by_eb is seeded from round 6's plan and from
    # v385, i.e. from crossings that have ALREADY been fitted -- so a
    # crossing nobody ever fitted can never enter the plan.  Two did not:
    # bet Pic 241.553-241.984 GHz on Xa9df and on X3a90 are catalogue
    # crossings that appear in neither source, and the plan carried 54
    # window keys against the catalogue's 56 without saying so.  The right
    # seed is the catalogue; until that rewrite lands, the plan must at
    # least NAME what it is missing instead of losing it silently.
    _cat = os.environ.get(
        'VF_CATALOGUE',
        '/data/SETI/products/per_target_results_v3.99.csv')
    if os.path.exists(_cat):
        import csv
        have = {(e['eb'], round(min(float(e['flo_GHz']), float(e['fhi_GHz'])), 6))
                for evs in events_by_eb.values() for e in evs
                if 'flo_GHz' in e and 'fhi_GHz' in e}
        missing = []
        with open(_cat) as fh:
            for row in csv.DictReader(fh):
                if str(row.get('crossing', '')).strip().lower() not in (
                        'true', '1', 'yes'):
                    continue
                try:
                    k = (row['eb'],
                         round(min(float(row['flo_GHz']),
                                   float(row['fhi_GHz'])), 6))
                except (KeyError, ValueError):
                    continue
                if k not in have:
                    missing.append(k)
        print('COVERAGE: plan carries %d crossing windows; catalogue '
              'crossings absent from the plan: %d %s'
              % (len(have), len(missing), missing))
    else:
        print('COVERAGE: catalogue %s not readable -- coverage UNCHECKED'
              % _cat)

    units = []
    for eb, evs in sorted(events_by_eb.items()):
        item = by_eb_item.get(eb)
        if item is None:
            nm = fallback_name.get(eb)
            base = by_name_item.get(nm)
            if base is None:
                print('SKIP %s: no worklist entry and no fallback' % eb)
                continue
            item = dict(base)
            item.update(eb=eb, mous=fallback_mous[eb],
                        size_bytes=fallback_size[eb],
                        target_dir='%s_EB_%s' % (
                            (base.get('target_dir') or nm).rsplit('_EB_', 1)[0],
                            eb.split('_')[-1]),
                        searched_sibling=[])
        star = star_of(item)
        evs2 = []
        seen = set()
        for e in evs:
            k = (e['tag'], round(e['freq_GHz'], 6))
            if k in seen:
                continue
            seen.add(k)
            e = dict(e)
            e['star'] = star
            evs2.append(e)
        units.append(dict(eb=eb, item=item, events=evs2,
                          gb=(item.get('size_bytes') or 0) / 1e9,
                          preexisting_ms=existing_ms.get(eb)))

    # the nine unsafe verdicts first, then ascending size
    unsafe = {'A002_X75bfbf_X1430', 'A002_Xa95c04_X14cd', 'A002_Xc66ce1_X1345',
              'A002_Xc6a3db_X7b5b', 'A002_Xf8f6a9_X10359', 'A002_Xfe62c1_X398',
              'A002_Xff0235_X8392', 'A002_Xa42f75_X319', 'A002_X12209f7_X16edb'}
    for u in units:
        u['unsafe'] = u['eb'] in unsafe
    units.sort(key=lambda u: (0 if u['preexisting_ms'] else 1,
                              0 if u['unsafe'] else 1, u['gb']))
    os.makedirs(ROOT, exist_ok=True)
    json.dump(units, open(ROOT + '/plan.json', 'w'), indent=1)
    print('%d blocks, %.0f GB to fetch, %d crossing windows, %d unsafe, '
          '%d already on disk'
          % (len(units),
             sum(u['gb'] for u in units if not u['preexisting_ms']),
             sum(len(u['events']) for u in units),
             sum(1 for u in units if u['unsafe']),
             sum(1 for u in units if u['preexisting_ms'])))
    for u in units:
        print('%-22s %6.1f GB  %d ev  %s%s' %
              (u['eb'], u['gb'], len(u['events']),
               'UNSAFE ' if u['unsafe'] else '',
               'ON-DISK' if u['preexisting_ms'] else ''))


if __name__ == '__main__':
    main()
