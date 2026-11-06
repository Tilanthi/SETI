#!/usr/bin/env python3
r"""recombfold_r30.py -- the limits of the field-recombined windows come from the product the search read.

Round 29, register row 1 (R1-1, R2 m8): "the limits for these 8 systems describe data that were not searched.  Recompute
them from the searched data".  In the 44 census blocks whose in-beam FIELD rows were recombined (the field-truncation
repair), the census search has read the recombined product since v4.09 (`r8inputs/v409/fieldfix_v409.json`, one record
per window, the re-calibrated product where the block was re-run in v4.29), while the export row -- and with it every
limit -- stayed on the earlier, narrower extraction (round-27 Ruling 23).  This module ends that split for the LIMIT
columns: every export row at a field-repair record's identity takes the searched product's own S_min, EIRP, rms and
on-source time, and the drift grid that product was searched on (ceiling, number of trials).  The statistic columns are
not touched (the census reads them from fieldfix_v409.json, as before).

**Imported and applied by `corrected_export_v399.py` as its LAST step**, after the re-calibration fold, so a field-
repaired window's flags factor (reflagfold_r29, REFLAG_LIMITREF=r23a) is superseded by the product itself: the record
of a re-run block IS the re-run product.  Applying it in the stage that writes the export means no read site changes.

INPUT `r30inputs/20261104/recomb_r30.json` (frozen; r29-inject-recomb `mkrecord.py`): one entry per fieldfix_v409 record,
same order, read from the product files (path + md5): S_min, rms, EIRP, on-source time, integration count, the
reference pointing's offset and response (the product's own `primary_beam_atten`), the extractor's beam width and dish,
the position convention, and per kept field its offset, response, on-source time, integrations and summed weight.

THE RECORD IS TIED TO THE SEARCH, NOT TRUSTED: `entries()` refuses unless every entry's S_min and T* equal the
fieldfix_v409 record in the same position (the census's own record), and `apply()` refuses an export row whose
channel width differs or that two entries claim.

Also the one owner of three per-window facts other generators need for these rows:
  * `lookup(eb, flo, fhi, dist_pc)` -> the entry or None (block, sorted edges to 1e-3 GHz, distance to 1e-3 pc: the
    harvest's fold-in key, = fieldcons_r27's join);
  * `prefold(row)` -> the limit columns the row carried before this fold (v4.29's printed values), from the audit;
  * `pb(row)` -> the primary-beam record v342_calc writes for the row: the REFERENCE pointing's offset and response
    from the product's own stored geometry, CHECKED to reproduce the row's own 5 sigma / S_min to 1 per cent (the
    check `_pb_from_geometry` makes; r33 failed it on epsilon Eri X12189 because `pbaudit_v408/pbgeom.json` holds the
    NARROW product's star direction, 0.219 arcsec -- the star's annual parallax -- from the searched one's);
  * `eta_beam(entry, coef_doc, coef_null)` -> the documented-beam retention of the MOSAIC: field f measures A_f S and is
    divided by a_rel,f = A_f / A_ref and weighted by a_rel,f^2 (inverse variance), so under the documented beam the
    combined estimate is A_ref S sum_f w_f (A_doc,f / A_f) / sum_f w_f; the pipeline's 1 / A_ref correction leaves the
    weighted mean of the per-field retentions, w_f = the extractor's own summed integration weights.

    python3 recombfold_r30.py --selftest   (needs a built corrected_export_v399.json)
    python3 recombfold_r30.py --drive N    N=1 an entry duplicated -> R1; N=2 the narrow product's geometry
                                           (pbgeom.json) in place of the searched one -> R2 (the r33 failure);
                                           N=3 one entry's S_min no longer the census record's -> R3;
                                           N=4 a field's weight moved to the furthest pointing -> R4 (eta changes)
"""
import json
import math
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
INPUT = os.path.join(HERE, 'r30inputs', '20261104', 'recomb_r30.json')
FIELDFIX = os.path.join(HERE, 'r8inputs', 'v409', 'fieldfix_v409.json')
AUDIT = os.path.join(HERE, 'recombfold_r30_audit.json')
ARCSEC = math.pi / 180.0 / 3600.0
#: the limit columns, and the two that describe the SEARCH GRID of the searched product (drift ceiling and number
#: of drift trials): the integration time and the grid must come from one product, or a drift-grid quantity formed
#: from them (step x track) mixes two extractions
LIMIT = (('smin', 'smin_Jy'), ('eirp', 'eirp_W'), ('rms', 'rms_mJy'), ('onsrc', 'onsrc_s'),
         ('drift_max', 'drift_max_Hz_s'), ('ndrift', 'ndrift'))
PB_TOL = 0.01

_E = None
_IX = None


def _key(eb, a, b):
    a, b = float(a), float(b)
    return (eb, round(min(a, b), 3), round(max(a, b), 3))


def entries(path=INPUT, fieldfix=FIELDFIX, _drive=0):
    """The frozen entries, checked against the census's own field-repair records (same order)."""
    global _E
    if _E is not None and not _drive:
        return _E
    if os.environ.get('RECOMB_LIMITS', '1') == '0' or not os.path.isfile(path):
        _E = []
        return _E
    E = json.load(open(path))['entries']
    F = json.load(open(fieldfix))
    if _drive == 3:
        E = [dict(E[0], smin_Jy=E[0]['smin_Jy'] * 1.01)] + E[1:]
    assert len(E) == len(F), ('R3 %d recombined entries against %d field-repair records' % (len(E), len(F)))
    for e, f in zip(E, F):
        assert (e['eb'], e['spw']) == (f['eb'], f['spw']) and e['smin_Jy'] == f['smin'] \
            and e['star_snr'] == f['star_snr'], (
            'R3 the recombined record for %s spw%s is not the product the census searched (S_min %r vs %r, T* %r vs '
            '%r): rebuild r30inputs/20261104/recomb_r30.json from the current fieldfix_v409.json'
            % (e['eb'], e['spw'], e['smin_Jy'], f['smin'], e['star_snr'], f['star_snr']))
    if _drive == 1:
        E = E + [dict(E[0])]
    if not _drive:
        _E = E
    return E


def _index(E=None):
    global _IX
    if _IX is not None and E is None:
        return _IX
    ix = {}
    for e in (E if E is not None else entries()):
        ix.setdefault(_key(e['eb'], e['flo'], e['fhi']), []).append(e)
    if E is None:
        _IX = ix
    return ix


def lookup(eb, flo, fhi, dist_pc, E=None):
    c = [e for e in _index(E).get(_key(eb, flo, fhi), ())
         if abs(float(e['dist_pc']) - float(dist_pc)) <= 1e-3]
    assert len(c) <= 1, ('R1 %d recombined entries claim window %s %.3f-%.3f GHz at %.4f pc'
                         % (len(c), eb, min(float(flo), float(fhi)), max(float(flo), float(fhi)), float(dist_pc)))
    return c[0] if c else None


def lookup_row(r, E=None):
    """An export row (flo/fhi/dist_pc) or a catalogue row (flo_GHz/fhi_GHz/dist_pc)."""
    if 'flo_GHz' in r:
        return lookup(r['eb'], r['flo_GHz'], r['fhi_GHz'], r['dist_pc'], E)
    return lookup(r['eb'], r['flo'], r['fhi'], r['dist_pc'], E)


def apply(rows, audit=AUDIT, verbose=True):
    """Set the limit columns of every export row at a recombined record's identity.  Returns the count."""
    E = entries()
    if not E:
        if verbose:
            print('recombfold_r30: RECOMB_LIMITS=0 or no input -- export unchanged')
        return 0
    used, log = {}, []
    for i, r in enumerate(rows):
        e = lookup_row(r)
        if e is None:
            continue
        assert abs(float(r['chanw']) - float(e['chanw'])) < 1.0, ('R1 channel width', r['eb'], r['chanw'], e['chanw'])
        old = {a: r[a] for a, _ in LIMIT}
        for a, b in LIMIT:
            r[a] = e[b]
        used.setdefault(id(e), []).append(i)
        log.append(dict(row=i, eb=r['eb'], flo=r['flo'], fhi=r['fhi'], dist_pc=r['dist_pc'], spw=e['spw'],
                        old=old, new={a: r[a] for a, _ in LIMIT}, product=e['product']['path']))
    n_ent_used = len(used)
    rec = dict(entries=len(E), entries_used=n_ent_used, rows_set=len(log), rows=log,
               unused=[dict(eb=e['eb'], spw=e['spw'], star=e['star']) for e in E if id(e) not in used])
    json.dump(rec, open(audit, 'w'), indent=1)
    if verbose:
        print('recombfold_r30: %d export rows take the searched (recombined) product\'s S_min, EIRP, rms and on-source '
              'time, from %d of %d records (%d records carry no export row)'
              % (len(log), n_ent_used, len(E), len(E) - n_ent_used))
    return len(log)


_AUD = None


def prefold(r, audit=AUDIT):
    """The limit columns the export rows at row r's window carried BEFORE this fold (exactly what v4.29 printed),
    from the audit apply() wrote: a list (duplicate export rows of one window each have their own), first = the
    row the catalogue keeps.  Refuses a recombined row the audit does not hold."""
    global _AUD
    if _AUD is None:
        _AUD = {}
        for x in json.load(open(audit))['rows']:
            _AUD.setdefault(_key(x['eb'], x['flo'], x['fhi']), []).append(x)
    lo, hi = (r['flo_GHz'], r['fhi_GHz']) if 'flo_GHz' in r else (r['flo'], r['fhi'])
    c = [x['old'] for x in _AUD.get(_key(r['eb'], lo, hi), ())
         if abs(float(x['dist_pc']) - float(r['dist_pc'])) <= 1e-3]
    assert c, ('R1 no pre-fold record for recombined window %s %s' % (r['eb'], lo))
    return c


def pb(r, e=None, geom=None):
    """The primary-beam record for a recombined row: the reference pointing's offset and response from the searched
    product's own stored geometry, checked against the row's own 5 sigma / S_min.  `geom` (drives only) replaces the
    product's star direction with another record's (l_star, m_star, pb_arcsec)."""
    e = e or lookup_row(r)
    off, fw = e['pb_offset_arcsec'], e['pb_fwhm_arcsec']
    if geom is not None:
        off = math.hypot(geom['l_star'], geom['m_star']) / ARCSEC
        fw = geom['pb_arcsec']
    att = math.exp(-4.0 * math.log(2.0) * (off / fw) ** 2)
    smin = float(r['smin_mJy']) / 1e3 if 'smin_mJy' in r else float(r['smin'])
    rms = float(r['rms_mJy']) if 'rms_mJy' in r else float(r['rms'])
    meas = 5.0 * rms / (smin * 1e3)
    assert abs(att / meas - 1.0) < PB_TOL, (
        'R2 the response from the searched product\'s geometry, %.6f, does not reproduce the row\'s own 5 sigma / '
        'S_min for %s %s %.4f GHz, %.6f' % (att, r.get('star_name'), r['eb'],
                                              min(float(r.get('flo', r.get('flo_GHz'))),
                                                  float(r.get('fhi', r.get('fhi_GHz')))), meas))
    return dict(flo=min(float(e['flo']), float(e['fhi'])), fhi=max(float(e['flo']), float(e['fhi'])),
                pb_offset_arcsec=round(off, 4), pb_atten=round(att, 6), pb_source='recombined_product')


def _g(c, coef):
    return math.exp(-4.0 * math.log(2.0) * (c / coef) ** 2)


def eta_beam(e, coef_doc, coef_null, _drive=0):
    """Documented-beam retention of the mosaic (weighted mean of the per-field retentions) and its parts."""
    fl = e['fields']
    w = [f['weight'] for f in fl]
    if _drive == 4:
        k = max(range(len(fl)), key=lambda i: fl[i]['offset_arcsec'])
        w = [0.0] * len(fl)
        w[k] = 1.0
    eta, cs = [], []
    for f in fl:
        c = f['offset_arcsec'] * coef_null / e['pb_fwhm_arcsec']       # offset in lambda/D at the product's frequency
        assert abs(_g(c, coef_null) / f['pb_resp'] - 1.0) < 1e-9, ('R4 field response', e['eb'], f['field'])
        eta.append(_g(c, coef_doc) / _g(c, coef_null))
        cs.append(c)
    ref = [i for i, f in enumerate(fl) if f['field'] == e['ref_field']]
    assert len(ref) == 1
    sw = sum(w)
    assert sw > 0
    return dict(eta=sum(a * b for a, b in zip(w, eta)) / sw, eta_ref=eta[ref[0]], c_ref=cs[ref[0]],
                c_max=max(cs), n_fields=len(fl),
                w_share_max_offset=w[max(range(len(fl)), key=lambda i: cs[i])] / sw)


def _selftest(drive=0):
    sys.path.insert(0, HERE)
    import adopted_e90 as ae
    fails = []
    try:
        E = entries(_drive=drive)
        if drive == 1:
            for e in E:
                lookup(e['eb'], e['flo'], e['fhi'], e['dist_pc'], E)
    except AssertionError as x:
        fails.append(str(x)[:160])
    if not fails:
        CAT = ae.catalogue(HERE)
        G = {}
        for g in json.load(open(os.path.join(HERE, 'pbaudit_v408', 'pbgeom.json'))):
            G.setdefault(g['_stem'], g)
        cd, cn = float(ae._texval('RingPbCoef', HERE)), float(ae._texval('RingPbCoefCode', HERE))
        n = 0
        for r in CAT:
            e = lookup_row(r)
            if e is None:
                continue
            n += 1
            try:
                geom = G.get('%s_spw%s' % (e['eb'], e['spw'])) if drive == 2 else None
                if drive == 2 and geom is None:
                    continue
                p = pb(r, e, geom)
                if drive != 2:
                    assert abs(p['pb_atten'] - float(r['pb_atten'])) < 2e-6, ('R2 catalogue pb_atten', r['eb'])
                b = eta_beam(e, cd, cn, _drive=drive)
                eb = json.load(open(os.path.join(HERE, 'beam_record_r17.json')))['eta_beam'][ae.smear_key(r)]
                assert abs(b['eta'] - eb) < 1e-9, ('R4 the beam record\'s retention %.6f is not the mosaic\'s %.6f for '
                                                   '%s %s' % (eb, b['eta'], r['star_name'], r['eb']))
            except AssertionError as x:
                fails.append(str(x)[:200])
                if drive:
                    break
        print('recombfold_r30 selftest: %d catalogue rows checked' % n)
    for f in fails[:5]:
        print('FAIL', f)
    print('recombfold_r30: %s%s' % ('FAIL' if fails else 'PASS', ' [drive %d]' % drive if drive else ''))
    return 3 if fails else 0


if __name__ == '__main__':
    d = int(sys.argv[sys.argv.index('--drive') + 1]) if '--drive' in sys.argv else 0
    if '--selftest' in sys.argv or d:
        sys.exit(_selftest(d))
    raise SystemExit('recombfold_r30 is applied by corrected_export_v399.py, which owns the export file.')
