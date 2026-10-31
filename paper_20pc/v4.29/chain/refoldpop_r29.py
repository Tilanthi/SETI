#!/usr/bin/env python3
r"""refoldpop_r29.py -- the crossing population after the v4.29 re-calibration fold, for the generators that
were written around named crossings (FOLD_DECISIONS.md E3; round-28 Ruling R21: re-run windows take their new
products whatever moves).

Imported, never run.  It answers one question several generators need: is this window one that the fold
RE-RAN (its block re-calibrated with ALMA's flags and re-searched with the deposited extractor)?  A crossing
that leaves the population because its re-run statistic is below the trigger is RETIRED, not lost: frozen
records measured on its earlier product (visibility fits, recurrence readings, RFI notes) stay in the
deposit and stop being read as facts about a crossing.  Anything else that drops out of a join is still an
error, which is why every caller asserts that each record it retires is (a) in a re-run window and (b) not
a crossing in the catalogue it is reading.

The re-run set is read from `reflagfold_r29_audit.json`, which `corrected_export_v399.py` writes on every
build (one row per folded export row); a build without the fold (REFLAG_FOLD=0, or the self-test side) has
an audit whose rows reproduce the shipped ones -- the set is then still the re-run windows, and nothing they
hold has fallen, so nothing is retired.
"""
import json
import os

HERE = os.path.dirname(os.path.abspath(__file__))
AUDIT = os.path.join(HERE, 'reflagfold_r29_audit.json')

_RERUN = None


def wkey(eb, a, b, nd=3):
    a, b = float(a), float(b)
    return (eb, round(min(a, b), nd), round(max(a, b), nd))


def rerun_keys(nd=3):
    """(eb, lo, hi) of every export row the fold re-ran in this build (statistic replaced, or a field-repaired
    limit row whose statistic is the recombined fieldfix record).  Windows kept under REFLAG_CODEVERSION=declare
    are not re-run."""
    global _RERUN
    if _RERUN is None:
        assert os.path.isfile(AUDIT), ('refoldpop_r29: %s missing -- corrected_export_v399.py has not run in '
                                       'this build' % AUDIT)
        A = json.load(open(AUDIT))
        _RERUN = [(r['eb'], float(r['flo']), float(r['fhi'])) for r in A['rows']
                  if r['statistic'] != 'kept (codeversion, declare)']
    return {wkey(eb, a, b, nd) for eb, a, b in _RERUN}


def retire(keys, crossing_keys, what, nd=3):
    """Split `keys` (window keys of frozen records about crossings, built with `wkey(.., nd)`) into
    (kept, retired).  A key is retired only when it is NOT a crossing now AND its window was re-run by the
    fold; any other key that is not a crossing is returned in `kept`, so the caller's own orphan check still
    fires on it."""
    rr = rerun_keys(nd)
    kept, ret = [], []
    for k in keys:
        if k not in crossing_keys and k in rr:
            ret.append(k)
        else:
            kept.append(k)
    return kept, ret


INPUT = os.path.join(HERE, 'r29inputs', 'reflag', 'reflag_census_r29.json')
_PRE = None


def prefold_max(eb, a, b, nd=3):
    """The largest statistic any shipped (pre-fold) export row of this window carried, or None when the fold did
    not re-run it -- from the fold's own input (`ship`), so it is the value the catalogue held before the fold."""
    global _PRE
    if _PRE is None:
        _PRE = {}
        for e in json.load(open(INPUT))['entries']:
            s = e['ship']
            k = wkey(s['eb'], s['flo'], s['fhi'], nd)
            _PRE[k] = max(_PRE.get(k, -1e9), float(s['star_snr']))
    return _PRE.get(wkey(eb, a, b, nd))


def entered(eb, a, b, trigger=5.0, nd=3):
    """True when this window is one the fold re-ran AND it was below the trigger before the fold: a crossing in
    it ENTERED the population with the re-calibration (so no earlier per-crossing measurement can exist)."""
    p = prefold_max(eb, a, b, nd)
    return p is not None and p < trigger and wkey(eb, a, b, nd) in rerun_keys(nd)


_Q = None


def q_rms(eb, a, b, dist_pc, nd=3):
    """The flags factor the fold applied to this window's rms in THIS build (1.0 where it did not re-run it): an
    auxiliary record measured on the EARLIER product (pbgate's product inventory) reproduces the published rms
    after this factor, and only after it.  Keyed by window AND distance: two stars can share a window
    (G 272-61 A/B in X14c1)."""
    global _Q
    if _Q is None:
        _Q = {}
        for r in json.load(open(AUDIT))['rows']:
            k = wkey(r['eb'], r['flo'], r['fhi'], nd) + (round(float(r['dist_pc']), 3),)
            _Q.setdefault(k, set()).add(round(float(r['q']['rms']), 12))
    v = _Q.get(wkey(eb, a, b, nd) + (round(float(dist_pc), 3),))
    if not v:
        return 1.0
    assert len(v) == 1, ('two flags factors for one window and star', eb, a, b, sorted(v))
    return next(iter(v))


_PREC = None


def ctrl_max_prefold(row, nd=3):
    """A catalogue row's control maximum BEFORE the fold (the shipped export row's, from the fold input), or the
    row's own where the fold did not re-run it.  For joins whose other side was measured on the EARLIER product
    and matches on the control maximum (sens_r11's injected-window join): after the fold the row carries the new
    product's ring, so a nearest-ctrl join must be made on the value the campaign saw."""
    global _PREC
    if _PREC is None:
        _PREC = {}
        for e in json.load(open(INPUT))['entries']:
            s = e['ship']
            _PREC.setdefault(wkey(s['eb'], s['flo'], s['fhi'], nd) + (round(float(s['dist_pc']), 3),),
                             set()).add(float(s['ctrl_max']))
    v = _PREC.get(wkey(row['eb'], row['flo_GHz'], row['fhi_GHz'], nd) + (round(float(row['dist_pc']), 3),))
    if not v:
        return float(row['ctrl_max_snr'])
    assert len(v) == 1, ('two pre-fold control maxima for one window and star', row['eb'], sorted(v))
    return next(iter(v))


FIELDFIX = os.path.join(HERE, 'r8inputs', 'v409', 'fieldfix_v409.json')
_PK = None


def census_ftopo(eb, flo, fhi, chanw_Hz, f_topo, nd=3):
    """The census crossing frequency of a catalogue crossing row.  A field-repaired window's census statistic is
    its recombined record's (fieldfix_v409.json; E2 = (a)), and so is its crossing frequency: where the fold
    re-ran the block and the re-calibrated recombined record peaks more than two channels from the narrow
    catalogue row (eta Crv X1430: catalogue 345.540 GHz reads 4.09 on the new product, which peaks at 345.846
    GHz, T 5.008), the census crossing is the record's peak.  Everywhere else: `f_topo` unchanged.  One rule,
    used by ledger_v410.py and numbers_v410.py so their two attribution counts cannot diverge."""
    global _PK
    if _PK is None:
        _PK = {}
        rr = rerun_keys(nd)
        for f in json.load(open(FIELDFIX)):
            if f.get('flo') is None or not f.get('pkf'):
                continue
            k = wkey(f['eb'], f['flo'], f['fhi'], nd)
            if k in rr:
                _PK[k] = float(f['pkf'])
    pk = _PK.get(wkey(eb, flo, fhi, nd))
    if pk is None or f_topo is None or abs(pk - float(f_topo)) <= 2.0 * float(chanw_Hz) / 1e9:
        return f_topo
    return pk


def unfold_export(rows):
    """Undo the fold on a copy of the corrected export's rows, as far as the fold input records it: each folded row's
    limit columns are divided by the q the audit says it took, and a row whose statistic the fold replaced takes back
    the shipped statistic and control maximum (`ship`).  For selftests that reconstruct the row set an EARLIER stage
    of corrected_export_v399.py handled (censusfix runs before the fold).  Returns the number of rows touched."""
    A = json.load(open(AUDIT))
    E = json.load(open(INPUT))['entries']
    n = 0
    for a in A['rows']:
        r = rows[a['row']]
        assert r['eb'] == a['eb'] and r['flo'] == a['flo'], ('audit row index does not match the export', a['row'])
        for c in ('smin', 'eirp', 'rms'):
            r[c] = r[c] / a['q'][c]
        if a['statistic'] == 'new':
            s = E[a['entry']]['ship']
            r['star_snr'], r['ctrl_max'] = s['star_snr'], s['ctrl_max']
        n += 1
    return n
