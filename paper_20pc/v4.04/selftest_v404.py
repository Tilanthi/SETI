#!/usr/bin/env python3
"""GATE (v4.04): drive every assertion added in this cycle, one at a time, and
require it to FAIL.  A check that cannot fail is not a
check, and v4.03 found three in code it had adopted.

Each case perturbs ONE literal or comparison in ONE generator, runs it with
its inputs and output redirected out of the way, and requires an
AssertionError.  A case that passes silently is reported as NOT DEMONSTRATED
and fails this gate.

★ The perturbation must be driven in whichever direction the literal can
move: tightening a tolerance that is already met exactly does nothing, which
is why several cases below loosen rather than tighten.
"""
import json
import os
import shutil
import subprocess
import sys
import tempfile
HERE=os.path.dirname(os.path.abspath(__file__))
CASES = [
 ('exposure_v404.py', "assert all(e in blk_max for e in AFF)", "assert all(e not in blk_max for e in AFF)"),
 ('exposure_v404.py', "assert len(rose) == 0", "assert len(rose) == 1"),
 ('exposure_v404.py', "assert disc > 0 and (old_mx - new_mx) > 0", "assert disc < 0 and (old_mx - new_mx) > 0"),
 ('exposure_v404.py', "assert abs(net_lo) < 0.5 * disc", "assert abs(net_lo) < 0.001 * disc"),
 ('exposure_v404.py', "assert tot_max >= tot_med > 0.9 * tot_max", "assert tot_max >= tot_med > 0.999 * tot_max"),
 ('exposure_v404.py', "assert aff_rows,", "assert not aff_rows,"),
 ('exposure_v404.py', "assert len(ROWS) == K['n_windows']", "assert len(ROWS) == K['n_windows'] + 1"),
 ('parallax_v404.py', "assert R['n'] == G['n']", "assert R['n'] == G['n'] + 1"),
 ('parallax_v404.py', "assert G['max'] > R['max']", "assert G['max'] < R['max']"),
 ('parallax_v404.py', "assert B['n_sys_le_1e15'] == C['n_sys_le_1e15']", "assert B['n_sys_le_1e15'] != C['n_sys_le_1e15']"),
 ('parallax_v404.py', "assert C['sys_med_sel'] > B['sys_med_sel']", "assert C['sys_med_sel'] < B['sys_med_sel']"),
 ('parallax_v404.py', "X = 0.245", "X = 0.2451"),
 ('parallax_v404.py', "assert 0.0 < resid < 0.10", "assert 0.0 < resid < 0.01"),
 ('parallax_v404.py', "assert 0.4 < frac < 0.9", "assert 0.9 < frac < 0.99"),
 ('flare_v404.py', "assert nloc > 0.5 * nfit", "assert nloc > 1.5 * nfit"),
 ('flare_v404.py', "assert n > 1 and abs(n - round(n)) / n < 0.01", "assert n > 1 and abs(n - round(n)) / n < 1e-9"),
 ('flare_v404.py', "assert F['obs_z_absmax'] < F['pred_z_lo']", "assert F['obs_z_absmax'] > F['pred_z_lo']"),
 ('flare_v404.py', "assert contrib < 0.2 * T", "assert contrib < 0.002 * T"),
 ('flare_v404.py', "assert C['boxcar_zmax_lo'] <= C['ctrl_zmax_hi']", "assert C['boxcar_zmax_lo'] > C['ctrl_zmax_hi']"),
 ('counts_v404.py', "post.get('provenance') == 'corrected-geometry'", "False"),
 ('counts_v404.py', "len(survive) == 1", "len(survive) == 2"),
 ('counts_v404.py', "r['post_c'] > r['post_t']", "r['post_c'] < r['post_t']"),
 ('counts_v404.py', "len(rows) == 3", "len(rows) == 4"),
 ('counts_v404.py', "< 1e-3", "< 1e0"),
 ('counts_v404.py', "assert post is not None", "assert post is None"),
 ('counts_v404.py', "assert st.mean(abs(x) for x in dctrl) > st.mean(abs(x) for x in dstar)", "assert st.mean(abs(x) for x in dctrl) < st.mean(abs(x) for x in dstar)"),
 ('fa_v404.py', "assert abs(_ef - mu) < 0.02", "assert abs(_ef - mu) < 1e-9"),
 ('fa_v404.py', "assert pois_tail(len(first), mu) < 1e-3", "assert pois_tail(len(first), mu) < 1e-9"),
 ('fa_v404.py', "assert pois_tail(resid, mu) > 0.05", "assert pois_tail(resid, mu) > 0.95"),
 ('fa_v404.py', "assert 'HoRankMed' in _v", "assert 'HoRankMedXYZ' in _v"),
 ('ledgers_v404.py', "assert in_snapshot == reported + withheld_blocks", "assert in_snapshot == reported + withheld_blocks + 1"),
 ('ledgers_v404.py', "assert int(_narrow) <= int(_wide)", "assert int(_narrow) > int(_wide)"),
 ('ledgers_v404.py', "assert proj < multi_arch", "assert proj > multi_arch"),
 ('ledgers_v404.py', "assert years / float(nsys) < 1 / 3.0", "assert years / float(nsys) < 1 / 30.0"),
 ('ledgers_v404.py', "assert int(texval('LedHoldout')) == len({r['eb'] for r in HOLD})", "assert int(texval('LedHoldout')) != len({r['eb'] for r in HOLD})"),
 ('maskframe_v404.py', "assert len(CAT_OLD) == 15", "assert len(CAT_OLD) == 17"),
 ('maskframe_v404.py', "if d > 0.5:", "if d > 0.0000001:"),
 ('maskframe_v404.py', "assert n_kms == n_mhz", "assert n_kms == n_mhz + 1"),
 ('maskframe_v404.py', "assert max(offs) > 10", "assert max(offs) > 1e9"),
 ('fields_v404.py', "assert len(cross) == len(in_blk) and len(cross) > 0", "assert len(cross) != len(in_blk)"),
 ('fields_v404.py', "assert _sib < 5.0", "assert _sib < 1.0"),
 ('fields_v404.py', "assert len(sir_cross) == 0", "assert len(sir_cross) == 1"),
 ('fields_v404.py', "assert B['n_ctrl_above_five'] == B['n_ctrl']", "assert B['n_ctrl_above_five'] != B['n_ctrl']"),
 ('fields_v404.py', "assert B['jackknife_err_Jy'] > 4 * B['thermal_err_Jy']", "assert B['jackknife_err_Jy'] > 400 * B['thermal_err_Jy']"),
 ('fields_v404.py', "assert len(med) > 500", "assert len(med) > 500000"),
 ('v342_calc.py', "_cands = [k for k in CAT_OLD if k.split('(')[0] == nl]", "_cands = [k for k in CAT_OLD if k.split('(')[0] == nl + 'X']"),
]
SHIM = """import builtins as _b, os as _o
_TMP = %r
_ro = _b.open


def _wo(file, mode='r', *a, **k):
    if isinstance(file, (str, bytes)) and any(c in mode for c in 'wax+'):
        file = _o.path.join(_TMP, _o.path.basename(
            file.decode() if isinstance(file, bytes) else file))
    return _ro(file, mode, *a, **k)


_b.open = _wo
"""

TMP = tempfile.mkdtemp(prefix='selftest_v404_')
ok = bad = 0
for fn, old, new in CASES:
    src = open(os.path.join(HERE, fn)).read()
    if old not in src:
        print('  MISSING  %-20s %s' % (fn, old)); bad += 1; continue
    p = src.replace(old, new, 1)
    # Run with cwd = the version directory, so every READ resolves, but
    # redirect every WRITE into a scratch directory.  Copying the directory
    # per case would be 135 MB x 45; a shim on builtins.open is exact and
    # free, and -- unlike a symlink farm -- it cannot truncate a real product.
    # The perturbed copy lives in the scratch directory, so __file__-derived
    # paths would point at it; pin them back at the version directory.
    p = p.replace("HERE = os.path.dirname(os.path.abspath(__file__))",
                  "HERE = %r" % HERE)
    p = p.replace("HERE = __file__.rsplit('/', 1)[0]", "HERE = %r" % HERE)
    # ... and let a generator that imports a sibling module find it.
    p = ("import sys\nsys.path.insert(0, %r)\n" % HERE) + SHIM % (TMP,) + p
    tmp = os.path.join(TMP, '_pert_' + fn)
    open(tmp, 'w').write(p)
    r = subprocess.run([sys.executable, tmp], capture_output=True, text=True,
                       cwd=HERE)
    os.remove(tmp)
    if r.returncode != 0 and 'AssertionError' in r.stderr:
        ok += 1
    else:
        print('  NOT DEMONSTRATED  %-20s %s -> rc=%d' % (fn, old[:50], r.returncode)); bad += 1
shutil.rmtree(TMP, ignore_errors=True)
print('selftest_v404: %d cases, %d demonstrated failing, %d NOT demonstrated'
      % (len(CASES), ok, bad))
sys.exit(1 if bad else 0)
