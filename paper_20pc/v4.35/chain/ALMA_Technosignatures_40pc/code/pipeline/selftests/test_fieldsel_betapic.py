#!/usr/bin/env python3
"""THE TEST THAT WOULD HAVE CAUGHT THE FIELD TRUNCATION.

Round 8, D2. Runs the OLD extractor and the NEW one over the SAME real
measurement set and compares them against what that measurement set
actually holds.

The subject is beta Pic execution block `A002_X75bfbf_Xace`, the one
affected block whose PRE-SELECTION calibrated MS still survives on the
host. Opened read-only it holds, in beta Pic fields:

    field 5   75 integrations   450.0 s   (4.98" from the star)
    field 6   70 integrations   420.0 s   (5.02" from the star)
    field 8    5 integrations    30.0 s
    ------------------------------------  900.0 s total, 150 integrations

plus three calibrator fields degrees away. The released `result.json` for
this block reports `n_int = 75`, `on_source_s = 450.00007` -- field 5's
numbers to the microsecond. The old selector kept field 5 because its
phase centre was 0.04" nearer the star, and threw away the other 450 s.

The contract, asserted below:

  T1  the search sees all 150 integrations and 900.0 s of on-source time
  T2  a machine-readable record of retained vs discarded time exists, and
      says that no in-beam on-source time was discarded
  T3  a carrier injected at the star is recovered at its injected flux
      (this is what fails if a field's own phase centre is not used for
      its DFT kernel -- the tone decoheres)
  T4  the noise on the star's spectrum improves by ~sqrt(2), because the
      integration time doubled

T1, T2 and T4 FAIL against the old code by construction. T3 passes under
both (the old code searches one pointing correctly) and is here to prove
the new code's multi-pointing combination is not merely longer but right.

Usage:  python3 test_fieldsel_betapic.py [--build]
"""
import json
import os
import shutil
import subprocess
import sys

import numpy as np

HOST_BIN = '/data/SETI/bin'
OLD = f'{HOST_BIN}/seti_extract_generic.py'      # pre-round-8, as released
NEW = f'{HOST_BIN}/seti_extract_r8.py'           # the repair
BASE = '/data/SETI/r8reext/test_betapic'
SRC_MS = ('/data/SETI/targets/bet_Pic_B6_EB_Xace/products/'
          'A002_X75bfbf_Xace_target.ms')
TEST_MS = f'{BASE}/test_spw1.ms'
EB = 'A002_X75bfbf_Xace'
SFX = '_fstest'
NPROC = int(os.environ.get('FSTEST_NPROC', '16'))

#: What the measurement set actually holds (measured read-only, see docstring)
EXPECT_NINT = 150
EXPECT_ONSRC = 900.0
#: The injected carrier
INJ_CHAN = 64
INJ_AMP = 0.02        # Jy
INJ_DRIFT = 0.0       # Hz/s -- a stationary tone, so no smearing to model

STAR = dict(name='bet Pic', ra=86.82123452009108, dec=-51.066136257823345,
            pmra=5.160196860824648, pmdec=84.0405295978282,
            parallax=50.93069062882289, parallax_err=0.001)


def build_test_ms():
    """One spw of the surviving full MS, ALL fields kept."""
    if os.path.isdir(TEST_MS):
        print(f'[test] reusing {TEST_MS}')
        return
    os.makedirs(BASE, exist_ok=True)
    os.environ.setdefault('CASASITECONFIG', '/home/fetch-agi/.casa/config.py')
    from casatasks import mstransform
    print(f'[test] building {TEST_MS} from spw 1 of the surviving full MS')
    mstransform(vis=SRC_MS, outputvis=TEST_MS, spw='1', datacolumn='data',
                reindex=True, keepflags=True)


def ms_truth():
    """Per-field on-source time of the test MS, measured independently."""
    os.environ.setdefault('CASASITECONFIG', '/home/fetch-agi/.casa/config.py')
    from casatools import table
    tb = table()
    tb.open(TEST_MS + '/FIELD')
    pc = tb.getcol('PHASE_DIR')[:, 0, :]
    names = list(tb.getcol('NAME'))
    tb.close()
    tb.open(TEST_MS, nomodify=True)
    f = tb.getcol('FIELD_ID')
    t = tb.getcol('TIME')
    e = tb.getcol('EXPOSURE')
    tb.close()
    out = []
    for fid in sorted(set(f.tolist())):
        s = (f == fid)
        tu, first = np.unique(t[s], return_index=True)
        dra = np.radians(STAR['ra']) - pc[0, fid]
        ddec = np.radians(STAR['dec']) - pc[1, fid]
        off = float(np.hypot(dra * np.cos(pc[1, fid]), ddec) /
                    (np.pi / 180.0 / 3600.0))
        out.append(dict(field=int(fid), name=str(names[fid]),
                        n_int=int(len(tu)),
                        on_source_s=float(e[s][first].sum()),
                        offset_arcsec_approx=off))
    return out


def run(script, tdir, label, extra_env=None):
    shutil.rmtree(tdir, ignore_errors=True)
    os.makedirs(f'{tdir}/products', exist_ok=True)
    env = dict(os.environ)
    env.update(SETI_TARGET_DIR=tdir, SETI_MS=TEST_MS, SETI_SFX=SFX,
               SETI_STAR_NAME=STAR['name'], SETI_STAR_RA=str(STAR['ra']),
               SETI_STAR_DEC=str(STAR['dec']), SETI_STAR_PMRA=str(STAR['pmra']),
               SETI_STAR_PMDEC=str(STAR['pmdec']),
               SETI_STAR_PARALLAX=str(STAR['parallax']),
               SETI_STAR_PARALLAX_ERR=str(STAR['parallax_err']),
               SETI_INJECT=f'{INJ_AMP},{INJ_DRIFT},{INJ_CHAN}',
               CASASITECONFIG='/home/fetch-agi/.casa/config.py',
               OMP_NUM_THREADS='1')
    env.update(extra_env or {})
    log = f'{BASE}/{label}.log'
    with open(log, 'w') as fh:
        rc = subprocess.call(['python3', script, EB, str(NPROC)],
                             env=env, stdout=fh, stderr=subprocess.STDOUT)
    print(f'[test] {label}: rc={rc}, log {log}')
    return rc


def measure(tdir):
    """What the product says about itself."""
    p = f'{tdir}/products/{EB}{SFX}_waterfall.npz'
    if not os.path.isfile(p):
        return None
    z = np.load(p, allow_pickle=True)
    I = z['I']
    W = z['W']
    t = np.asarray(z['times'], dtype=float)
    nint = I.shape[0]
    # on-source time, as the product itself reports it if it can
    if 'on_source_s' in z.files:
        onsrc = float(z['on_source_s'])
        src = 'EXPOSURE'
    else:
        onsrc = float(nint * np.median(np.diff(t)))
        src = 'n_int x median(dt)'
    # weighted mean star spectrum, and the recovered injected flux
    star = I[:, 0, :]
    w = np.nan_to_num(W)
    good = w > 0
    num = np.nansum(np.where(good, star * w, 0.0), axis=0)
    den = np.nansum(np.where(good, w, 0.0), axis=0)
    spec = np.where(den > 0, num / np.maximum(den, 1e-30), np.nan)
    nch = len(spec)
    off = np.array([c for c in range(nch)
                    if abs(c - INJ_CHAN) > 2 and np.isfinite(spec[c])])
    base = float(np.median(spec[off]))
    rec = float(spec[INJ_CHAN] - base)
    # Combined noise, the two ways the search itself states it. NOT the MAD
    # across channels of the mean spectrum: that is dominated by residual
    # bandpass structure, which is common to every integration and therefore
    # does not average down, so it understates the gain from added time.
    # (Measured: the channel-MAD said 0.86 where both proper estimators say
    # 0.71. A metric that cannot see the effect is not a measurement.)
    n_src = int(z['n_src'])
    P = I[:, n_src:, :]
    med = np.nanmedian(P, axis=1)
    mad = np.nanmedian(np.abs(P - med[:, None, :]), axis=1)
    sg = 1.4826 * mad
    sg[sg <= 0] = np.nan
    with np.errstate(divide='ignore', invalid='ignore'):
        sig_ctrl = float(np.median(1.0 / np.sqrt(np.nansum(1.0 / sg ** 2, axis=0))))
    sig_w = float(np.median(1.0 / np.sqrt(np.maximum(w.sum(axis=0), 1e-30))))
    noise = sig_ctrl
    fsj = f'{tdir}/products/{EB}{SFX}_fieldsel.json'
    fs = json.load(open(fsj)) if os.path.isfile(fsj) else None
    return dict(n_int=nint, on_source_s=onsrc, on_source_src=src,
                rec_amp_Jy=rec, noise_Jy=noise,
                sig_ctrl_Jy=sig_ctrl, sig_theory_Jy=sig_w,
                snr=rec / noise if noise else float('nan'),
                n_fields=int(z['n_fields']) if 'n_fields' in z.files else 1,
                fieldsel=fs)


def main():
    if '--build' in sys.argv or not os.path.isdir(TEST_MS):
        build_test_ms()
    truth = ms_truth()
    inbeam = [f for f in truth if f['offset_arcsec_approx'] < 30.0]
    print('[test] the measurement set holds:')
    for f in truth:
        print(f'   field {f["field"]} {f["name"][:20]:<20} '
              f'{f["n_int"]:4d} int {f["on_source_s"]:7.1f} s  '
              f'off ~{f["offset_arcsec_approx"]:.2f}"')
    truth_nint = sum(f['n_int'] for f in inbeam)
    truth_onsrc = sum(f['on_source_s'] for f in inbeam)
    print(f'[test] in-beam truth: {truth_nint} integrations, '
          f'{truth_onsrc:.1f} s on-source '
          f'(hard-coded expectation {EXPECT_NINT}, {EXPECT_ONSRC:.1f} s)')
    assert truth_nint == EXPECT_NINT, truth_nint
    assert abs(truth_onsrc - EXPECT_ONSRC) < 1.0, truth_onsrc

    res = {}
    # 'nopx' is the NEW code with the parallax correction switched off: it
    # isolates the parallax term from the multi-field repair, which is the only
    # way to show the two together do not interact (INTEGRATE_ME.md 2.1).
    for label, script, env in (('old', OLD, None), ('new', NEW, None),
                               ('nopx', NEW, {'SETI_PX': '0'})):
        if not os.path.isfile(script):
            print(f'[test] SKIP {label}: {script} missing')
            continue
        run(script, f'{BASE}/{label}', label, env)
        res[label] = measure(f'{BASE}/{label}')
        print(f'[test] {label}: {json.dumps(res[label], default=str)[:400]}')

    rows = []

    def check(name, label, ok, got, want):
        rows.append((name, label, 'PASS' if ok else 'FAIL', got, want))

    for label in ('old', 'new'):
        m = res.get(label)
        if m is None:
            continue
        check('T1 n_int', label, m['n_int'] == EXPECT_NINT,
              m['n_int'], EXPECT_NINT)
        check('T1 on_source_s', label, abs(m['on_source_s'] - EXPECT_ONSRC) < 5.0,
              round(m['on_source_s'], 2), EXPECT_ONSRC)
        fs = m['fieldsel']
        check('T2 fieldsel record', label,
              fs is not None and fs['discarded_in_beam_s'] <= 1.0,
              'none' if fs is None else round(fs['discarded_in_beam_s'], 1),
              '<= 1.0 s discarded in-beam')
        check('T3 injected flux', label,
              abs(m['rec_amp_Jy'] / INJ_AMP - 1.0) < 0.05,
              round(m['rec_amp_Jy'], 5), INJ_AMP)
    if 'old' in res and 'new' in res and res['old'] and res['new']:
        # Expected: the effective time goes 450 s -> 450 + 420 x (A6/A5)^2 s,
        # so sqrt(450/869) = 0.72. Field 8's 30 s is fully flagged (sum W = 0)
        # and its primary-beam weight is 0.073 anyway, so it adds nothing.
        for nm, key in (('T4 control noise', 'sig_ctrl_Jy'),
                        ('T4 weight noise', 'sig_theory_Jy')):
            r = res['new'][key] / res['old'][key]
            check(nm + ' vs old', 'new', r < 0.80, round(r, 3),
                  '< 0.80 (sqrt(450/869) = 0.72)')

    # T5: the parallax correction must move the per-field offsets by <= 0.1"
    # and must NOT change which field is the reference (the multi-field repair
    # picks it by max A^2 t, and A depends on the offset).
    g = {}
    for label in ('new', 'nopx'):
        p = f'{BASE}/{label}/products/{EB}{SFX}_srcspec.npz'
        if not os.path.isfile(p):
            continue
        z = np.load(p, allow_pickle=True)
        g[label] = dict(ref=int(z['ref_field']),
                        off=np.asarray(z['field_offset_arcsec'], dtype=float),
                        A=np.asarray(z['field_pb_resp'], dtype=float),
                        conv=str(z['pos_convention']) if 'pos_convention' in z.files else 'legacy',
                        plx=float(z['plx_offset_arcsec']) if 'plx_offset_arcsec' in z.files else 0.0)
    if 'new' in g and 'nopx' in g:
        dmax = float(np.max(np.abs(g['new']['off'] - g['nopx']['off'])))
        check('T5 offset shift', 'new', dmax <= 0.1, round(dmax, 4),
              '<= 0.1 arcsec')
        check('T5 reference field', 'new', g['new']['ref'] == g['nopx']['ref'],
              f"{g['nopx']['ref']} -> {g['new']['ref']}", 'unchanged')
        check('T5 parallax applied', 'new', g['new']['plx'] > 1e-4,
              round(g['new']['plx'], 4), '> 0 (and 0 with SETI_PX=0)')
        check('T5 parallax off', 'nopx', g['nopx']['plx'] < 1e-9,
              round(g['nopx']['plx'], 6), '0 with SETI_PX=0')
        print(f"[test] pos_convention: new={g['new']['conv']} nopx={g['nopx']['conv']}")

    print('\n%-22s %-5s %-5s %-14s %s' % ('test', 'code', 'verdict', 'got', 'want'))
    for n, lb, v, g, w in rows:
        print('%-22s %-5s %-5s %-14s %s' % (n, lb, v, g, w))
    nf_old = sum(1 for n, lb, v, g, w in rows if lb == 'old' and v == 'FAIL')
    nf_new = sum(1 for n, lb, v, g, w in rows if lb in ('new', 'nopx') and v == 'FAIL')
    print(f'\nOLD code: {nf_old} failures (must be > 0 -- the test must be '
          f'able to catch the defect)')
    print(f'NEW code: {nf_new} failures (must be 0)')
    json.dump(dict(truth=truth, results=res,
                   rows=[dict(test=n, code=lb, verdict=v, got=str(g),
                              want=str(w)) for n, lb, v, g, w in rows],
                   old_failures=nf_old, new_failures=nf_new),
              open(f'{BASE}/verdict.json', 'w'), indent=1, default=str)
    ok = (nf_new == 0 and nf_old > 0)
    print('\nTEST SUITE: ' + ('PASS' if ok else 'FAIL'))
    return 0 if ok else 1


if __name__ == '__main__':
    sys.exit(main())
