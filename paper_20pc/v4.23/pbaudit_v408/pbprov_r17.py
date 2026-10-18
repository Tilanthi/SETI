#!/usr/bin/env python3
"""THE PER-ROW PROVENANCE RECORD FOR THE TWELVE WINDOWS THAT ENTER THE CENSUS.

    python3 pbaudit_v408/pbprov_r17.py            # write pbprov_r17.json
    python3 pbaudit_v408/pbprov_r17.py --check     # verify, write nothing
    python3 pbaudit_v408/pbprov_r17.py --drive N   # N=1..4, each must FAIL

★★★ WHY THIS FILE EXISTS, AND WHY THE ASSERTION WAS NOT RELAXED.

`pbaudit_v408.py` refuses to run while any released catalogue row has no frozen
provenance record for its primary-beam attenuation:

    assert _prov.count(None) == 0, \\
        '%d released rows have no frozen provenance record'

`pbcat_v408.json` was harvested over the windows released at the time, so when
the twelve epsilon Eridani Band 6 windows enter the primary census it has
nothing for them and the refusal fires on exactly twelve rows.  The honest
answer to a missing record is to **write the record**, not to widen the
refusal: the data is all there, and the record is reconstructed here from the
delivered products by the same arithmetic the search itself used.

    > "Widening a refusal because it is inconvenient is the one thing you may
    >  not do."  -- the round-17 ruling.

★★ WHY A NEW FILE AND NOT TWELVE MORE LINES IN `pbcat_v408.json`.
`v342_calc.py` resolves these twelve windows through its own
`_pb_from_geometry` fallback, and it **asserts that the fallback fires** --
"a fallback that never fires would mean the clause above is untested".
Populating `pbcat_v408.json` would silence that clause.  So `pbcat` stays the
frozen harvest it is, this file is the per-row index the audit was missing, and
`pbaudit_v408.py` consults it after `pbcat`.  Neither record is weakened and
neither is mutated by a build.

★★★ AND THE 5 sigma / S_min "REPRODUCTION" TURNED OUT TO BE ARITHMETIC, SO A
SECOND CHECK HAD TO BE ADDED THAT IS NOT.
The ruling asked for four decimals.  The measured agreement is **2.2e-16** --
machine epsilon -- which means the export's S_min for these windows was itself
computed as 5 sigma / A from the same stored geometry in the same
floating-point path.  That is not a weak result, it is a different result: it
says we have recovered the *identical* number the search used, bit for bit,
rather than a model that agrees with it.  But it is NOT an independent test of
the geometry, and reporting it as one would be exactly the distinction
`pbaudit_v408.py` itself draws between its independent and its back-solved
rows.  So it is reported as the identity it is, and an independent clause is
added beside it:

  the stored beam width must reproduce 1.22 lambda / 12 m at the window's own
  median frequency, to a part in 100 000.

That compares the stored geometry against the frequency in the product header
and a convention, neither of which enters the response calculation.
★★ It also puts a known defect of the release ON THE RECORD rather than
leaving it implicit: `pb_arcsec` is the 12 m beam on **every** window the
search stored, including `A002_Xb9c01c_X2004`, which the archive records as a
**7 m** block.  The record therefore carries the array each block was taken
on, so a reader of the record cannot mistake the stored width for the dish.
This is the same defect `pbaudit_v408.py` section 2 measures and the reason
`sens_r11.py`'s own fallback reads the diameter from the archive metadata and
never from the stored width.

★ WHAT THE RECORD CARRIES, AND WHY IT IS A PROVENANCE AND NOT A MODEL.
For each window, `pbaudit_v408/pbgeom.json` stores what the search itself read
out of the measurement set: the phase centre, the stellar direction cosines at
that epoch, the beam width used, and the parallax.  So

    offset   = |(l_star, m_star)|                      -- from the product
    response = exp(-4 ln2 (offset / pb_arcsec)^2)       -- the search's own form

Nothing is assumed and nothing is fitted.  **And it is checked against a
number the pipeline measured independently**: the response must reproduce the
export's own 5 sigma / S_min for that window.  That quantity comes from the
image rms and the quoted point-source limit, neither of which is in this
calculation, so the agreement is a test and not a restatement.  The ruling
asked for four decimals and the measured worst case is reported.

Drives (each must FAIL):
  1  the direction cosines zeroed      -> the response goes to 1 and the
                                          5 sigma / S_min reproduction fails
  2  the beam width doubled            -> likewise, in the other direction
  3  a window dropped from pbgeom      -> the one-record-per-window assertion
  4  a window's key added to pbcat's
     coverage after the record is built -> the no-overlap clause
  5  the stored median frequency moved  -> the 1.22 lambda / 12 m clause
"""
import csv
import json
import math
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
ARCSEC = math.pi / 180.0 / 3600.0
C_M_S = 299792458.0
PB_FTOL = 0.01                      # GHz, the same window tolerance v342 uses
OUT = os.path.join(HERE, 'pbprov_r17.json')

#: the reproduction the ruling asks for: four decimals on 5 sigma / S_min.
TOL = 1e-4


def main(argv):
    drive = 0
    for i, a in enumerate(argv):
        if a == '--drive':
            drive = int(argv[i + 1])
    check = '--check' in argv

    geom = json.load(open(os.path.join(HERE, 'pbgeom.json')))
    meta = json.load(open(os.path.join(ROOT, 'archive_meta_v381.json')))['ebs']
    pbc = json.load(open(os.path.join(ROOT, 'pbcat_v408.json')))
    exp = json.load(open(os.path.join(ROOT, 'corrected_export_v399.json')))
    rows = exp['rows'] if isinstance(exp, dict) else exp
    # ★ SCOPE: the RELEASED CATALOGUE's own windows, and no others.  The
    # export carries 1721 rows -- the census, the pre-registered hold-out and
    # the archival extension -- and `pbaudit_v408.py` audits only what the
    # catalogue ships.  Writing a provenance for a window the audit never
    # reads would be padding the record, and the first version of this script
    # did exactly that: it tried to describe a 51 Eri hold-out window and
    # tripped its own one-record-per-window assertion.  The catalogue is used
    # ONLY to select the scope; every value below still comes from the product
    # geometry and the export.
    cat = os.path.join(ROOT, 'per_target_results_v3.99.csv')
    scope = set()
    for c in csv.DictReader(open(cat, newline='', encoding='utf8')):
        a, b = float(c['flo_GHz']), float(c['fhi_GHz'])
        scope.add((c['eb'], round(min(a, b), 3), round(max(a, b), 3)))
    rows = [r for r in rows
            if (r['eb'], round(min(float(r['flo']), float(r['fhi'])), 3),
                round(max(float(r['flo']), float(r['fhi'])), 3)) in scope]
    assert rows, 'no export row is in the released catalogue at all'

    by_eb = {}
    for g in geom:
        if drive == 3 and g['_stem'].endswith('_spw0'):
            continue                       # drive 3: a window goes missing
        by_eb.setdefault(g['_stem'].split('_spw')[0], []).append(g)

    # the rows pbcat does not cover.  Keyed on the block and the window edges,
    # never on the star name: the catalogue carries 'eps Eri' and pbcat's keys
    # carry the released name, and a name comparison between the two is how
    # this project has lost rows fourteen times.
    covered = set()
    for k, v in pbc.items():
        eb = k.rsplit('|', 1)[-1]
        for e in v:
            covered.add((eb, round(min(e['flo'], e['fhi']), 3),
                         round(max(e['flo'], e['fhi']), 3)))

    out, worst, worstw = [], 0.0, None
    for r in rows:
        lo = min(float(r['flo']), float(r['fhi']))
        hi = max(float(r['flo']), float(r['fhi']))
        key = (r['eb'], round(lo, 3), round(hi, 3))
        if key in covered:
            continue
        cand = [g for g in by_eb.get(r['eb'], ())
                if lo - PB_FTOL <= g['freqmed'] / 1e9 <= hi + PB_FTOL]
        assert len(cand) == 1, (
            '%d product geometry record(s) for %s %s %.4f-%.4f GHz -- the '
            'record cannot be written for a window it does not describe '
            'exactly once' % (len(cand), r.get('star_name'), r['eb'], lo, hi))
        g = cand[0]
        l_star = 0.0 if drive == 1 else g['l_star']
        m_star = 0.0 if drive == 1 else g['m_star']
        pb = g['pb_arcsec'] * (2.0 if drive == 2 else 1.0)
        off = math.hypot(l_star, m_star) / ARCSEC
        att = math.exp(-4.0 * math.log(2.0) * (off / pb) ** 2)
        # ---- the INDEPENDENT clause: the stored width against the product's
        # own median frequency and the 1.22 lambda / 12 m convention the
        # search used.  Neither quantity enters `att` above.
        fmed = g['freqmed'] * (1.5 if drive == 5 else 1.0)
        pred12 = 1.22 * C_M_S / fmed / 12.0 / ARCSEC
        assert abs(pred12 / g['pb_arcsec'] - 1.0) < 1e-5, (
            'the stored beam width for %s is %.4f arcsec, which is not '
            '1.22 lambda / 12 m at its own median frequency (%.4f arcsec); '
            'the geometry record cannot be vouched for'
            % (g['_stem'], g['pb_arcsec'], pred12))
        meas = (5.0 * r['rms'] / (r['smin'] * 1e3)
                if r.get('rms') and r.get('smin') else None)
        assert meas is not None, (
            'no rms/S_min for %s %s %.4f GHz, so the response cannot be '
            'checked against anything the pipeline measured, and an unchecked '
            'record is not a provenance' % (r.get('star_name'), r['eb'], lo))
        d = abs(att - meas)
        if d > worst:
            worst, worstw = d, (r['eb'], round(lo, 4))
        out.append(dict(
            eb=r['eb'], flo=lo, fhi=hi,
            pb_offset_arcsec=round(off, 4), pb_atten=round(att, 6),
            pb_source='product_geometry',
            star_ra=g['t1_ra'], star_dec=g['t1_dec'],
            parallax_mas=g['parallax'],
            theta_pb_arcsec=g['pb_arcsec'],
            theta_pb_convention='1.22 lambda / 12 m at the window median '
                                'frequency, as the search stored it',
            array=(meta.get(r['eb']) or {}).get('array'),
            freqmed_GHz=g['freqmed'] / 1e9,
            product=g['_stem'], product_dir=g['_dir'],
            smin_check=round(meas, 6)))

    if not out:
        print('pbprov: FAIL the record is empty -- either pbcat already covers '
              'every released row, in which case this file should be deleted '
              'rather than left, or the join found nothing, which is worse')
        return 1
    if worst > TOL:
        print('pbprov: FAIL the reconstructed response does not reproduce the '
              'pipeline own 5 sigma / S_min to %g: worst %.2e at %r'
              % (TOL, worst, worstw))
        return 1
    # no row may be in both records, or the audit would have two provenances
    # for one window and could prefer either.
    if drive == 4 and out:
        w = out[0]
        covered.add((w['eb'], round(w['flo'], 3), round(w['fhi'], 3)))
    both = [w for w in out
            if (w['eb'], round(w['flo'], 3), round(w['fhi'], 3)) in covered]
    if both:
        print('pbprov: FAIL %d window(s) are in pbcat_v408.json AND here, e.g. '
              '%s %.4f GHz -- one window, one provenance'
              % (len(both), both[0]['eb'], both[0]['flo']))
        return 1

    blocks = sorted({w['eb'] for w in out})
    print('pbprov: %d window(s) in %d block(s): %s'
          % (len(out), len(blocks), ', '.join(blocks)))
    print('pbprov: the response IS the pipeline own 5 sigma / S_min to %.2e '
          '(worst, at %r) -- an identity, not an independent agreement: the '
          'number recovered is bit-for-bit the one the search used'
          % (worst, worstw))
    print('pbprov: and independently, every stored beam width reproduces '
          '1.22 lambda / 12 m at its own median frequency to better than '
          '1e-5, on blocks the archive records as %s'
          % ', '.join('%s=%s' % (w['eb'], w['array'])
                      for w in sorted({w['eb']: w for w in out}.values(),
                                      key=lambda x: x['eb'])))
    print('pbprov: offsets %.2f-%.2f arcsec, responses '
          '%.4f-%.4f' % (
                         min(w['pb_offset_arcsec'] for w in out),
                         max(w['pb_offset_arcsec'] for w in out),
                         min(w['pb_atten'] for w in out),
                         max(w['pb_atten'] for w in out)))
    if drive:
        print('  DRIVE %d DID NOT FAIL -- the clause it exercises is vacuous'
              % drive)
        return 2
    if check:
        have = json.load(open(OUT)) if os.path.exists(OUT) else None
        same = have == out
        print('pbprov: --check %s' % ('the record on disk is current'
                                      if same else 'THE RECORD ON DISK IS NOT '
                                      'WHAT THE PRODUCTS GIVE'))
        return 0 if same else 1
    json.dump(out, open(OUT, 'w'), indent=1, sort_keys=True)
    print('pbprov: wrote %s' % OUT)
    return 0


if __name__ == '__main__':
    sys.exit(main(sys.argv))
