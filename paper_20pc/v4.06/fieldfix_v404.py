#!/usr/bin/env python3
"""Fold the round-8 field-selection repair into the survey export.

Round 8, decision D1/D2 (`referee_r8/DECISIONS_R8.md`). `_select_best_field_ms()`
kept ONE field of every multi-`FIELD_ID` measurement set and discarded the rest,
on the premise that such a set is a mosaic. For 34 of the 42 affected released
blocks the premise is wrong -- they are a single pointing written as several
`FIELD` rows -- so the search ran on one scan group and threw the others away:
171 of 1,655 windows, 18 stars, 19.1-19.6 h of in-beam on-source time,
a median 1.73x flux penalty (`referee_r8/FIELD_TRUNCATION_LEDGER.md`).

**This module is imported and applied by `corrected_export_v399.py`, not run
on its own.** That is deliberate and it is the v3.99 ACA-repair lesson:

  * `v342_calc.py` rebuilds the released catalogue from the export on every
    build, so a patch applied to the catalogue CSV is silently discarded --
    that was tried in v3.99 and is recorded in `corrected_export_v399.py` so
    it is not tried again;
  * `apply_holdout_v381.py` *writes* the frozen export, so the repair cannot
    live upstream of it either;
  * the export is read by seventeen generators. Applying the repair inside the
    stage that already builds the export means **not one read site changes**,
    and every existing downstream cross-assertion still guards the result.

If the harvest file is absent -- before the re-extraction campaign has landed
-- `apply()` is a no-op returning 0, so the build is unaffected.

Row provenance after this pass:
    'frozen-geometry'     untouched by either repair
    'corrected-geometry'  ACA control-geometry re-extraction (v3.99)
    'field-repaired'      every in-beam field now in the search (round 8)
    'corrected+field-repaired'  both
"""
import json
import os

HERE = os.path.dirname(os.path.abspath(__file__))
HARVEST = os.path.join(HERE, 'fieldfix_r8.json')
AUDIT = os.path.join(HERE, 'fieldfix_v404_audit.json')

#: Columns the re-extraction re-measures, and which export column each sets.
#: Everything else in a matched row is left exactly as it was: this repair adds
#: integration time, it does not redefine any quantity.
REPLACE = (('star_snr', 'star_snr'), ('rms', 'rms'), ('smin', 'smin'),
           ('eirp', 'eirp'), ('onsrc', 'onsrc'), ('src_snr', 'src'),
           ('line', 'line'), ('line_off', 'line_off'))


def key(eb, a, b):
    """Match on sorted frequency bounds. The products store flo/fhi in tuning
    order, which is descending for half the windows; keying on the raw pair
    silently loses those (learned in `ctrlsep_v400.py`)."""
    lo, hi = (a, b) if a <= b else (b, a)
    return (eb, round(lo, 3), round(hi, 3))


def apply(rows, harvest=HARVEST, audit=AUDIT, verbose=True):
    """Update `rows` in place from the round-8 re-extraction. Returns the
    number of rows updated (0 if the harvest does not exist yet)."""
    if not os.path.isfile(harvest):
        if verbose:
            print('fieldfix_v404: no harvest yet -- export unchanged')
        return 0
    NEW = json.load(open(harvest))

    prod = {}
    for w in NEW:
        if w.get('flo') is None or w.get('star_snr') is None:
            continue
        prod.setdefault(key(w['eb'], w['flo'], w['fhi']), []).append(w)

    n_upd = n_amb = 0
    dt, drms, dsmin, dstar = [], [], [], []
    unmatched = sorted(prod)
    for r in rows:
        k = key(r['eb'], float(r['flo']), float(r['fhi']))
        cand = prod.get(k)
        if not cand:
            continue
        if len(cand) > 1:
            n_amb += 1
            continue
        w = cand[0]
        if k in unmatched:
            unmatched.remove(k)

        # The rank statistic's ensemble size must not change: every downstream
        # rank, KS and stage-one statistic assumes a fixed control count.
        ca = w.get('ctrl_all') or []
        if ca:
            assert len(ca) == len(r['ctrl_all']), (
                'control vector length changed for %s spw%s (%d -> %d)'
                % (w['eb'], w.get('spw'), len(r['ctrl_all']), len(ca)))

        # The star must not have moved: a re-extraction that picked a different
        # pointing would look like a sensitivity gain and be a different source.
        if w.get('pb_offset') is not None and r.get('pb_arcsec'):
            assert abs(float(w['pb_offset'])) < 2.0 * float(r['pb_arcsec']), (
                'star %.1f" from the phase centre in the re-extraction of %s'
                % (float(w['pb_offset']), w['eb']))

        # Round 8 adds integration time; it cannot remove any. A window whose
        # on-source time fell, or whose noise rose, means something other than
        # the field repair happened and must not be folded in silently.
        if r.get('onsrc') and w.get('onsrc'):
            assert float(w['onsrc']) >= 0.999 * float(r['onsrc']), (
                'on-source time FELL for %s spw%s: %.1f -> %.1f s'
                % (w['eb'], w.get('spw'), float(r['onsrc']), float(w['onsrc'])))
            dt.append(float(w['onsrc']) / float(r['onsrc']))
        if r.get('rms') and w.get('rms'):
            assert float(w['rms']) <= 1.05 * float(r['rms']), (
                'rms ROSE for %s spw%s: %.4f -> %.4f mJy'
                % (w['eb'], w.get('spw'), float(r['rms']), float(w['rms'])))
            drms.append(float(w['rms']) / float(r['rms']))
        if r.get('smin') and w.get('smin'):
            dsmin.append(float(w['smin']) / float(r['smin']))
        if r.get('star_snr') and w.get('star_snr'):
            dstar.append(float(w['star_snr']) / float(r['star_snr']))

        for dst, src in REPLACE:
            if w.get(src) is not None:
                r[dst] = w[src]
        if ca:
            s = sorted(ca)
            r['ctrl_all'] = ca
            r['ctrl_max'] = max(ca)
            r['ctrl_med'] = s[len(s) // 2]
            r['ctrl_p90'] = s[int(0.9 * (len(s) - 1))]
            if w.get('n_ge') is not None:
                r['n_ge_star'] = int(w['n_ge'])
            if w.get('n_ctrl') is not None:
                r['n_ctrl'] = int(w['n_ctrl'])
        if w.get('pkf'):
            r['f_cross'] = w['pkf']
        if w.get('pkd') is not None:
            r['drift_peak'] = w['pkd']
        # provenance of the repair itself, so the ledger is generated
        r['n_fields'] = w.get('n_fields')
        r['field_kept'] = w.get('kept_fields')
        r['field_retained_s'] = w.get('retained_s')
        r['field_retained_eff_s'] = w.get('retained_eff_s')
        r['field_discarded_s'] = w.get('discarded_s')
        r['onsrc_src'] = w.get('onsrc_src')
        prev = r.get('provenance') or 'frozen-geometry'
        r['provenance'] = ('corrected+field-repaired'
                           if prev == 'corrected-geometry' else 'field-repaired')
        n_upd += 1

    def q(x, f):
        x = sorted(x)
        return x[int(f * (len(x) - 1))] if x else None

    rec = dict(
        updated=n_upd, ambiguous=n_amb,
        harvest_windows=len(NEW),
        unmatched_harvest_keys=[list(k) for k in unmatched],
        on_source_ratio=dict(median=q(dt, 0.5), p10=q(dt, 0.1), p90=q(dt, 0.9),
                             max=q(dt, 1.0)),
        rms_ratio=dict(median=q(drms, 0.5), p10=q(drms, 0.1), p90=q(drms, 0.9)),
        smin_ratio=dict(median=q(dsmin, 0.5), p10=q(dsmin, 0.1),
                        p90=q(dsmin, 0.9)),
        star_snr_ratio=dict(median=q(dstar, 0.5), p10=q(dstar, 0.1),
                            p90=q(dstar, 0.9)),
        source='round-8 field-selection repair, 42 blocks re-extracted')
    json.dump(rec, open(audit, 'w'), indent=1)
    if verbose:
        print('fieldfix_v404: %d rows updated, %d ambiguous, %d harvest keys '
              'unmatched' % (n_upd, n_amb, len(unmatched)))
        if dt:
            print('  on-source x%.3f median, rms x%.3f, S_min x%.3f'
                  % (rec['on_source_ratio']['median'],
                     rec['rms_ratio']['median'] or 0,
                     rec['smin_ratio']['median'] or 0))
    return n_upd


if __name__ == '__main__':
    raise SystemExit('fieldfix_v404 is applied by corrected_export_v399.py, '
                     'which owns the export file; running it alone would '
                     'write nothing.')
