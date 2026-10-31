#!/usr/bin/env python3
r"""reflagfold_r29.py -- the v4.29 re-calibration fold: every census window whose block was re-calibrated
with ALMA's final flags (round-27 Ruling 29 patch) and re-searched with the deposited extractor takes the
NEW product's search statistic, and its limit is scaled by ONE factor q read from one frozen record.

**Imported and applied by `corrected_export_v399.py`, as its last step (after the field-selection and the
name-collision repairs), not run on its own** -- the same reason `fieldfix_v404.py` and `censusfix_v407.py`
live there: `v342_calc.py` rebuilds the catalogue from the export on every build, and 47 generators read the
export, so applying the fold inside the stage that writes it means not one read site changes.

INPUT  `r29inputs/reflag/reflag_census_r29.json` (frozen; built by the fold bundle's `build_fold.py` from the
re-flag harvest).  One entry per re-run census window:
  * `ship`  the shipped export row's identity AS THIS STAGE SEES IT: block, both edges and channel width
            exactly, distance, and the row's own statistic and control maximum (a content key: 45 windows hold
            two export rows of one star).  Never a name.
  * `schema` `acafull` (a corrected-geometry row: the record is an `acafull_v399.json` entry and is applied
            with that fold's own semantics) or `export` (a frozen-geometry row: the export mapping's measured
            columns).
  * `rec`   the new product's record in that schema; its edges are NOT used (Pipeline_Final trims one edge
            channel in ~a tenth of the windows; the shipped edges, bandwidth and identity are kept).
  * `q_rows` per matched export row, {'r33': {col: new product's col / this row's col for col in smin, eirp,
            rms}, 'r23': the flag effect S_min_new / S_min(fieldfix record) on all three columns for a
            field-repaired window, else = r33} (`n_dup` rows: duplicate export rows
            of one window -- two product directories of one star -- are all folded; `rec_rows`, when present,
            gives each of them its own record, `smin_new_rows` the S_min each must end at).
  * `codeversion`  true where the change is NOT a flag effect (the block's flags were not changed by the
            patch, or a production-equivalent re-run is byte-identical to the flagged one).

TWO SWITCHES (environment, read once):
  REFLAG_CODEVERSION = census (default) | declare
      census:  every re-run window takes its new statistic (the census rule: the deposited extractor's
               statistic on ALMA's flags; coordinator decision 2026-10-29, REFLAG_DECISION item 8).
      declare: windows marked `codeversion` keep the shipped statistic (their limit still takes q).
  REFLAG_LIMITREF = r23a (default; coordinator decision E2 = (a), FOLD_DECISIONS.md 2026-10-29) | r23 | r33
      r23a:    Ruling 23's convention, whole: a field-repaired window's export row is the LIMIT's row (narrow
               extraction, narrow on-source time); it keeps its narrow statistic and takes only the flags
               factor q (S_min_new / S_min(fieldfix record)); the recombined statistic enters through
               `fieldfix_v409.json`, which the bundle replaces with the re-run record (as in v4.28).  Every
               other window is folded exactly as under r23/r33.
      r23:     for field-repaired windows the limit stays on the narrow extraction scaled by the flag/flux
               effect alone (Ruling 23; the fold design of REFLAG.md 11:15); identical to r33 everywhere else.
      r33:     limits come from the new products, field recombination included (round-27 Ruling 33).  NOT
               BUILDABLE as it stands: v342_calc's primary-beam check (the response from the window geometry
               must reproduce the product's own 5 sigma / S_min to 1 %) fails on recombined mosaics (eps Eri
               X12189: 0.3281 vs 0.3192), and Ruling 33's completeness spot check has not been made.  FOLD.md.
  REFLAG_FOLD = 1 (default) | 0   -- 0 is a no-op, for A/B builds.

THE LIMIT IS SCALED HERE AND NOWHERE ELSE.  `smin`, `eirp` and `rms` of each re-run row are multiplied by q;
every limit generator reads them through the catalogue (`eirp_nominal_W`, `adopted_e90.per_window`), so a
change of one q moves every limit that depends on that window and nothing else (demonstrated by the bundle's
drive Q1).  `onsrc` follows the new product only for a field-repaired window under r33.

NO KEY IS ADDED TO ANY ROW.  The provenance of the fold is the audit `reflagfold_r29_audit.json`, so a fold
whose records reproduce the shipped ones leaves the export byte-identical (the bundle's self-test).
"""
import json
import os

HERE = os.path.dirname(os.path.abspath(__file__))
INPUT = os.path.join(HERE, 'r29inputs', 'reflag', 'reflag_census_r29.json')
AUDIT = os.path.join(HERE, 'reflagfold_r29_audit.json')

#: the export mapping's measured columns (= hostsrc/export_figdata.py; holdfix_r27.MEAS) minus the three the
#: limit scaling owns and `onsrc`, which is the limit's integration time
EXPORT_STAT = ('star_snr', 'src_snr', 'ctrl_max', 'ctrl_med', 'ctrl_p90', 'n_ge_star', 'n_ctrl', 'n_src',
               'drift_max', 'ndrift', 'res', 'line', 'line_off', 'likely', 'old_flag', 'ctrl_all')
LIMIT = ('smin', 'eirp', 'rms')


def mode():
    cv = os.environ.get('REFLAG_CODEVERSION', 'census')
    lr = os.environ.get('REFLAG_LIMITREF', 'r23a')
    on = os.environ.get('REFLAG_FOLD', '1')
    assert cv in ('census', 'declare'), 'REFLAG_CODEVERSION=%r' % cv
    assert lr in ('r33', 'r23', 'r23a'), 'REFLAG_LIMITREF=%r' % lr
    assert on in ('0', '1'), 'REFLAG_FOLD=%r' % on
    return cv, lr, on == '1'


def _lohi(a, b):
    a, b = float(a), float(b)
    return (a, b) if a <= b else (b, a)


def _match(rows, s):
    lo, hi = _lohi(s['flo'], s['fhi'])
    out = []
    for i, r in enumerate(rows):
        if r['eb'] != s['eb'] or float(r.get('chanw') or 0) != float(s['chanw']):
            continue
        if _lohi(r['flo'], r['fhi']) != (lo, hi):
            continue
        if abs(float(r['dist_pc']) - float(s['dist_pc'])) > 1e-3:
            continue
        if r['star_snr'] != s['star_snr'] or r['ctrl_max'] != s['ctrl_max']:
            continue
        out.append(i)
    return out


def _acafull(r, w):
    """corrected_export_v399.py's per-row overlay, statistic columns only (geometry is per block|spw and
    unchanged; the limit columns are the q scaling's)."""
    ca = w['ctrl_all']
    assert len(ca) == len(r['ctrl_all']), ('control ensemble size changed', r['eb'], len(ca))
    r['star_snr'] = w['star_snr']
    r['ctrl_all'] = ca
    s = sorted(ca)
    r['ctrl_max'] = max(ca)
    r['ctrl_med'] = s[len(s) // 2]
    r['ctrl_p90'] = s[int(0.9 * (len(s) - 1))]
    r['n_ge_star'] = int(w['n_ge'])
    r['n_ctrl'] = int(w['n_ctrl'])
    if w.get('src') is not None:
        r['src_snr'] = w['src']
    if w.get('line') is not None:
        r['line'] = w['line'] or None
    if w.get('line_off') is not None:
        r['line_off'] = w['line_off']
    if w.get('pkf'):
        r['f_cross'] = w['pkf']
    if w.get('pkd') is not None:
        r['drift_peak'] = w['pkd']
    if w.get('pb'):
        r['pb_arcsec'] = w['pb']
        r['r_out_arcsec'] = 0.78 * w['pb']


def _export(r, w):
    assert len(w['ctrl_all']) == len(r['ctrl_all']), ('control ensemble size changed', r['eb'])
    for f in EXPORT_STAT:
        r[f] = w[f]
    # the new product retains its peak cell (the frozen extraction did not; v342_calc then keeps it, as for a
    # corrected-geometry row, instead of the old extraction's peak snapshot) -- new side only
    if w.get('pkf'):
        r['f_cross'] = w['pkf']
    if w.get('pkd') is not None:
        r['drift_peak'] = w['pkd']


def apply(rows, path=INPUT, audit=AUDIT, verbose=True, qpatch=None):
    """Fold in place.  Returns the number of rows whose statistic was replaced.  `qpatch` (drives only):
    {entry index: multiplier on q}."""
    cv, lr, on = mode()
    # drive Q1 only (refold's q drive): REFLAG_QDRIVE="<entry index>:<factor>[,...]" multiplies those entries'
    # limit factors; recorded in the audit, and reflagdecl_r29 R7 stops any build that is not a declared drive
    if qpatch is None and os.environ.get('REFLAG_QDRIVE'):
        qpatch = {int(a.split(':')[0]): float(a.split(':')[1]) for a in os.environ['REFLAG_QDRIVE'].split(',')}
    if not on or not os.path.isfile(path):
        if verbose:
            print('reflagfold_r29: %s -- export unchanged' % ('REFLAG_FOLD=0' if not on else 'no input'))
        return 0
    D = json.load(open(path))
    E = D['entries']
    seen = {}
    n_stat = n_lim = n_cv_kept = 0
    qdev = []
    log = []
    for j, e in enumerate(E):
        m = _match(rows, e['ship'])
        # n_dup > 1: duplicate export rows of one window (two product dirs of one star; the catalogue keeps one);
        # all are folded, each row's own limit columns scaled by the same q
        assert len(m) == e.get('n_dup', 1), (
            'reflagfold_r29: entry %d (%s %s-%s) matches %d export rows (expected %d); the base this '
            'bundle was built on is not the tree it is applied to -- rebuild the bundle'
            % (j, e['ship']['eb'], e['ship']['flo'], e['ship']['fhi'], len(m), e.get('n_dup', 1)))
        for i in m:
            assert i not in seen, ('two entries fold onto one export row', j, seen[i])
            seen[i] = j
        # duplicate export rows of one window: v342_calc keeps the FIRST row unless a later one carries a line
        # annotation and it does not.  The new record gives every duplicate the same annotation, which would
        # flip that choice to a row the catalogue never shipped (alpha CMa B X579, beta Pic X32f1 and G 272-61
        # X14c1: the kept row's S_min carries the primary-beam response, the dropped one's does not).  So a
        # duplicate that shipped without an annotation keeps none: the choice stays the shipped one.
        _was_none = [rows[i].get('line') is None for i in m] if len(m) > 1 else []
        for n, i in enumerate(m):
            e['_n'] = n
            _fold_row(rows[i], i, e, j, cv, lr, qpatch, log, qdev, _q(e['q_rows'][n], lr))
        for i, wn in zip(m, _was_none):
            if wn:
                rows[i]['line'] = None
        n_lim += 1
        if _keep(e, cv, lr):
            n_cv_kept += 1
        else:
            n_stat += 1
    qd = [x for x in qdev if x is not None]
    rec = dict(mode=dict(REFLAG_CODEVERSION=cv, REFLAG_LIMITREF=lr), entries=len(E), statistic_replaced=n_stat,
               limit_scaled=n_lim, codeversion_kept=n_cv_kept,
               q_vs_record_max_reldev=max(qd) if qd else None, side=D.get('side'), built_from=D.get('meta'),
               qdrive={str(k): v for k, v in (qpatch or {}).items()},
               rows=log)
    json.dump(rec, open(audit, 'w'), indent=1)
    if verbose:
        print('reflagfold_r29 [%s, %s]: %d entries, %d statistics replaced, %d kept (codeversion or field-repaired limit row), %d limits '
              'scaled; |old*q/new - 1| max %s' % (cv, lr, len(E), n_stat, n_cv_kept, n_lim,
                                                   rec['q_vs_record_max_reldev']))
    return n_stat


def _fold_row(r, i, e, j, cv, lr, qpatch, log, qdev, q):
    """One export row: the statistic (unless declared), then the limit scaling by this row's q."""
    keep = _keep(e, cv, lr)
    n = e['_n']
    if not keep:
        rec = e['rec_rows'][n] if e.get('rec_rows') else e['rec']
        (_acafull if e['schema'] == 'acafull' else _export)(r, rec)
    k = qpatch.get(j, 1.0) if qpatch else 1.0
    for f in LIMIT:
        r[f] = r[f] * (q[f] * k)
    if lr == 'r33' and e.get('field_repaired') and not keep and e.get('onsrc_new') is not None:
        r['onsrc'] = e['onsrc_new']
    sn = (e.get('smin_new_rows') or [e.get('smin_new')] * (n + 1))[n]
    if sn is not None and (lr == 'r33' or not e.get('field_repaired')):
        qdev.append(abs(r['smin'] / sn - 1.0))
    log.append(dict(entry=j, row=i, eb=r['eb'], flo=r['flo'], fhi=r['fhi'], dist_pc=r['dist_pc'], q=q,
                    statistic=('kept (field-repaired: the limit row, r23a)' if lr == 'r23a' and e.get('field_repaired')
                               else 'kept (codeversion, declare)') if keep else 'new', schema=e['schema']))


def _q(qr, lr):
    """The row's limit factors.  r23a: ONE factor on all three columns, the noise ratio (the flags/flux effect);
    the primary-beam response stays the catalogue's own geometry, so `smin = 5 rms / A` (pbaudit_v408) keeps
    holding.  Per-column ratios differ only where the new product's response differs from the catalogue's
    (alpha CMa B X579, whose catalogue position follows the visual orbit and the extractor's does not: up to
    8.9 per cent; G 272-61 X14c1 0.15 per cent; every other row < 1e-3)."""
    if lr != 'r23a':
        return qr[lr]
    f = qr['r23']['rms']
    return dict(smin=f, eirp=f, rms=f)


def _keep(e, cv, lr):
    """True when the export row keeps its shipped statistic: a code-version window under `declare`, or a
    field-repaired window under r23a (its statistic is the recombined fieldfix record's, not this row's)."""
    return bool((cv == 'declare' and e.get('codeversion')) or (lr == 'r23a' and e.get('field_repaired')))


_NEW = None


def is_new(row, path=INPUT):
    """True when `row` (an export or catalogue-building row) carries a re-flagged product's statistic in THIS
    build: the fold is on, the input is the new side, the window's statistic was replaced (not kept under
    REFLAG_CODEVERSION=declare), and the row is at an entry's identity (block, both edges exactly, channel
    width, distance to 1e-3 pc).  Used by v342_calc.py so that a check meaningful only when the export and the
    old peak snapshot come from one extraction is not applied across two (as for corrected-geometry rows)."""
    global _NEW
    if _NEW is None:
        _NEW = {}
        cv, lr, on = mode()
        if on and os.path.isfile(path):
            D = json.load(open(path))
            if D.get('side') == 'new':
                for e in D['entries']:
                    if _keep(e, cv, lr):
                        continue
                    s = e['ship']
                    _NEW.setdefault((s['eb'],) + _lohi(s['flo'], s['fhi']) + (float(s['chanw']),), []).append(
                        float(s['dist_pc']))
    d = _NEW.get((row['eb'],) + _lohi(row['flo'], row['fhi']) + (float(row.get('chanw') or 0),))
    return bool(d) and any(abs(float(row['dist_pc']) - x) <= 1e-3 for x in d)


PINS = os.path.join(HERE, 'r29inputs', 'reflag', 'pins_r29.json')
PINLOG = os.path.join(HERE, 'pins_probe_r29.log')


def _active_new():
    cv, lr, on = mode()
    return on and os.path.isfile(INPUT) and json.load(open(INPUT)).get('side') == 'new'


def pin(name, got, literal):
    """The value a typed-literal pin must take in THIS build.  Several gates pin a count or a value to the
    population it was last re-anchored on ("re-anchored by hand whenever the census legitimately moves").  The
    fold is such a move, and its size depends on the fold mode, so each pin it moves is re-anchored here, per
    mode, from the frozen record r29inputs/reflag/pins_r29.json, which the bundle builds from a PROBE build
    (REFLAG_PINPROBE=1: every pin logs what it found to pins_probe_r29.log and is satisfied) and FOLD.md lists
    old -> new.  Without the fold, or on its self-test side, the literal is returned unchanged.  A pin the
    record does not carry for the active mode stops the build: it has not been re-anchored."""
    if not _active_new():
        return literal
    cv, lr, _ = mode()
    if os.environ.get('REFLAG_PINPROBE') == '1':
        # the FIRST evaluation of a pin in the probe build is the production run of its generator; every later one
        # (a selftest's perturbed re-run, a gate drive) must see THAT value, or the probe would make every drive of
        # the pin silent (found by the stage-1 rehearsal: selftest_v403 drop-crossing went SILENT)
        key = 'PIN29 %s|%s %s ' % (cv, lr, name)
        if os.path.isfile(PINLOG):
            for l in open(PINLOG):
                if l.startswith(key):
                    return json.loads(l[len(key):].rsplit(' literal=', 1)[0])
        with open(PINLOG, 'a') as f:
            f.write('PIN29 %s|%s %s %s literal=%s\n' % (cv, lr, name, json.dumps(got), json.dumps(literal)))
        return got
    P = json.load(open(PINS))
    m = P.get('pins', {}).get('%s|%s' % (cv, lr), {})
    assert name in m, ('reflagfold_r29.pin: %s is not re-anchored for mode %s|%s in pins_r29.json -- run the '
                       'probe build (refold.sh does) and rebuild the bundle' % (name, cv, lr))
    return m[name]


_OLD = None


def old_stat(row, path=INPUT):
    """The star statistic `row` carried BEFORE the fold (the shipped export row's), for joins whose other side is
    a measurement made on the OLD product and keyed on its statistic (v342_calc's per-window noise scale,
    r8inputs/scale_v406.jsonl): the scale, cell count and N_ind of a re-calibrated window are those measured on
    its earlier product, which is what the catalogue then states.  Rows the fold did not replace: their own."""
    global _OLD
    if not is_new(row, path):
        return row['star_snr']
    if _OLD is None:
        _OLD = {}
        for e in json.load(open(path))['entries']:
            s = e['ship']
            _OLD.setdefault((s['eb'],) + _lohi(s['flo'], s['fhi']) + (float(s['chanw']),), []).append(
                (float(s['dist_pc']), s['star_snr']))
    c = [t for d, t in _OLD[(row['eb'],) + _lohi(row['flo'], row['fhi']) + (float(row.get('chanw') or 0),)]
         if abs(float(row['dist_pc']) - d) <= 1e-3]
    assert len(set(c)) == 1, ('old_stat: %d candidate statistics' % len(set(c)), row['eb'])
    return c[0]


if __name__ == '__main__':
    raise SystemExit('reflagfold_r29 is applied by corrected_export_v399.py, which owns the export file.')
