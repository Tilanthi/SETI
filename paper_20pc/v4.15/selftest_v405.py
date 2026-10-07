#!/usr/bin/env python3
"""GATE (v4.05): drive every assertion added in this cycle, one at a time, and
require it to FAIL.

A check that cannot fail is not a check.  v4.03 found three such checks in code
it had adopted and v4.04 found two more, so every assertion added here is
demonstrated failing rather than declared to pass.

Each case perturbs ONE literal or comparison in ONE generator, runs it with
cwd at the version directory -- so every READ resolves -- and with every WRITE
redirected into a scratch directory by a shim on `builtins.open`.  A symlink
farm would not do: `open(path, 'w')` follows a symlink and would truncate the
real product.

★ The perturbation must be driven in whichever direction the literal can move.
Tightening a tolerance that is already met exactly does nothing; several cases
below therefore loosen, invert, or shift a key rather than tighten.
"""
import os
import subprocess
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))

CASES = [
    # ---- v342_calc.py: the computed dispositions and assertions A1/A2 ------
    ('v342_calc.py',
     "assert not _A1_computed, _A1_computed",
     "assert _A1_computed, _A1_computed"),
    ('v342_calc.py',
     "assert not _A2_computed, _A2_computed",
     "assert _A2_computed, _A2_computed"),
    ('v342_calc.py', "assert len(_A1_shipped) == 6",
     "assert len(_A1_shipped) == 7"),
    ('v342_calc.py', "assert len(_A2_hand_old) == 2",
     "assert len(_A2_hand_old) == 3"),
    ('v342_calc.py', "assert all(abs(o[5]) > 3000 for o in _A2_hand_old)",
     "assert all(abs(o[5]) > 30000 for o in _A2_hand_old)"),
    # move ONE key of the re-keyed hand map by 1 kHz: the re-keying assertion
    # must notice that the shipped column is no longer reproduced
    ('v342_calc.py', "('61 Vir', 'A002_Xc079b5_X82f', 344.872405)",
     "('61 Vir', 'A002_Xc079b5_X82f', 344.872406)"),
    ('v342_calc.py', "assert _oldkey_reach > 0", "assert _oldkey_reach > 100"),
    # and the H2CO normalisation the whole computed column rests on
    ('v342_calc.py',
     "_cands = [k for k in CAT_OLD if k.split('(')[0] == nl]",
     "_cands = [k for k in CAT_OLD if k.split('(')[0] == nl + 'X']"),

    # ---- dispo_v405.py ----------------------------------------------------
    ('dispo_v405.py', "assert len(attr) == 16", "assert len(attr) == 17"),
    ('dispo_v405.py', "assert len(blank_attr) == 6",
     "assert len(blank_attr) == 7"),
    ('dispo_v405.py', "assert len(shipped) == 12", "assert len(shipped) == 13"),
    ('dispo_v405.py', "assert len(rank_unattr) == 2",
     "assert len(rank_unattr) == 3"),
    ('dispo_v405.py', "assert not _conflict, _conflict",
     "assert _conflict, _conflict"),
    ('dispo_v405.py', "assert len(mislabel) == 2",
     "assert len(mislabel) == 3"),
    ('dispo_v405.py', "== 8, len(rows_tab)", "== 9, len(rows_tab)"),
    ('dispo_v405.py', "assert max(_bp) - min(_bp) > 5",
     "assert max(_bp) - min(_bp) > 500"),
    ('dispo_v405.py', "assert len(HAND_OLD) == 5 and len(HAND) == 12",
     "assert len(HAND_OLD) == 5 and len(HAND) == 13"),

    # ---- ladder_v405.py: RETIRED (v4.11) ---------------------------------
    # Moved to retired_generators/.  It emitted a two-frame mask ladder
    # nothing inputs, and the single-frame ladder plus the robustness table
    # are maskframe_v411.py's (tab_maskrobust_v411.tex), which carries its
    # own driven assertions.  Eight cases against a file that is not there
    # could only ever report MISSING, which is a self-test reporting a
    # pass because its perturbation no longer perturbs anything.

    # ---- etadrift_v405.py -------------------------------------------------
    ('etadrift_v405.py', "A_lo = [r for r in A if eta(r) < 1.0]",
     "A_lo = [r for r in A if eta(r) < 0.0]"),
    ('etadrift_v405.py', "S1_lo = [r for r in S1 if eta(r) < 1.0]",
     "S1_lo = [r for r in S1 if eta(r) < 1e9]"),
    ('etadrift_v405.py', "XA_lo = [r for r in XA if eta(r) < 1.0]",
     "XA_lo = [r for r in XA if eta(r) < 1e9]"),
    ('etadrift_v405.py', "B_hi = [r for r in B if eta(r) >= 1.0]",
     "B_hi = [r for r in B if eta(r) >= 1e9]"),
    ('etadrift_v405.py', ">= _cw_all[-1] / 4", ">= _cw_all[-1] * 4"),
    ('etadrift_v405.py',
     "assert max(float(r['on_source_s']) for r in A_lo) < _med_track",
     "assert max(float(r['on_source_s']) for r in A_lo) < 0.001 * _med_track"),

    # ---- make_tables_v328.py: the exoplanet-host census --------------------
    ('make_tables_v328.py', "== (19, 42)", "== (19, 43)"),
    ('make_tables_v328.py', "assert _n_blank_flag > 0",
     "assert _n_blank_flag > 1000"),
    ('make_tables_v328.py', "assert not _unsupported,",
     "assert _unsupported,"),
    ('make_tables_v328.py', "assert exo_sample > _exo_sample_flag",
     "assert exo_sample < _exo_sample_flag"),
    ('make_tables_v328.py', "DBL_MEARTH = 13.0 * 317.828",
     "DBL_MEARTH = 13000.0 * 317.828"),
    ('make_tables_v328.py', "assert NUM['exo_hosts_above_dbl_already_flagged']",
     "assert not NUM['exo_hosts_above_dbl_already_flagged']"),
    ('make_tables_v328.py', "EXO_RADIUS_ARCSEC = 180.0",
     "EXO_RADIUS_ARCSEC = 3.0"),

    # ---- hosts_v399.py: multiplicity on the principal type -----------------
    ('hosts_v399.py', "assert n_mult_bag != n_mult",
     "assert n_mult_bag == n_mult"),
    ('hosts_v399.py', "assert n_mult <= n_mult_bag",
     "assert n_mult > n_mult_bag"),
    ('hosts_v399.py', "assert not _stale,", "assert _stale,"),
    # the whole point of the fix: decide on the principal type, not the bag
    ('hosts_v399.py', "mul = [MULT[h['otype']]] if h['otype'] in MULT else []",
     "mul = [MULT[t] for t in h['otypes'] if t in MULT]"),

    # ---- occurrence_v399.py: the star-bandwidth product --------------------
    ('occurrence_v399.py', "assert starband_uniform > starband_sum",
     "assert starband_uniform < starband_sum"),
    ('occurrence_v399.py',
     "assert abs(nurel_sys_own - nurel_sys) > 0.1 * nurel_sys",
     "assert abs(nurel_sys_own - nurel_sys) > 100 * nurel_sys"),
    ('occurrence_v399.py',
     "assert max(_sys_own.values()) <= nurel_survey + 1e-12",
     "assert max(_sys_own.values()) <= 0.1 * nurel_survey"),
    # the defect itself: dividing a system's union by the SURVEY's midpoint
    ('occurrence_v399.py', "_sys_own[_sid] = union(_iv) / (0.5 * (_lo + _hi))",
     "_sys_own[_sid] = union(_iv) / nu_mid"),

    # ---- appm_v405.py: the clustering replacement --------------------------
    ('appm_v405.py', "assert GRID_WORST < 0.1", "assert GRID_WORST < 1e-9"),
    ('appm_v405.py', "assert obs_mm == SHIPPED['max_multiplicity']",
     "assert obs_mm != SHIPPED['max_multiplicity']"),
    ('appm_v405.py', "abs(mm_c.mean() - SHIPPED['null_mean']) < 0.15",
     "abs(mm_c.mean() - SHIPPED['null_mean']) < 1e-9"),
    ('appm_v405.py', "assert abs(p_c - SHIPPED['p']) < 0.006",
     "assert abs(p_c - SHIPPED['p']) < 1e-9"),
    ('appm_v405.py', "assert power['scan']['156'][_i12] > "
                     "power['one_mhz']['156'][_i12]",
     "assert power['scan']['156'][_i12] < power['one_mhz']['156'][_i12]"),
    ('appm_v405.py', "assert power['one_mhz']['1'][_i6] > "
                     "power['scan']['1'][_i6]",
     "assert power['one_mhz']['1'][_i6] < power['scan']['1'][_i6]"),
    ('appm_v405.py', "assert obs_in > out['tube_occupancy']['null_mean']",
     "assert obs_in < out['tube_occupancy']['null_mean']"),

    # ---- freqocc_v405.py: the withdrawn occupancy excess --------------------
    ('freqocc_v405.py', "assert len(rows) == 3027", "assert len(rows) == 3028"),
    ('freqocc_v405.py', "assert GRID_WORST < 1e-3",
     "assert GRID_WORST < 1e-30"),
    ('freqocc_v405.py', "assert D['greedy']['z'] > 3.0",
     "assert D['greedy']['z'] > 30.0"),
    ('freqocc_v405.py', "assert abs(A['greedy']['z']) < 2.0",
     "assert abs(A['greedy']['z']) < 0.2"),
    ('freqocc_v405.py', "assert n_naive < n_stars - 40",
     "assert n_naive > n_stars"),
    ('freqocc_v405.py', "assert 0 < len(sig_masked) < len(sig)",
     "assert 0 < len(sig_masked) < 2"),
    # the defect being withdrawn: keying on the directory rather than the star
    ('freqocc_v405.py', "assert D['greedy']['observed'] == "
                        "SHIPPED_DIRKEY['observed']",
     "assert D['greedy']['observed'] != SHIPPED_DIRKEY['observed']"),
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

TMP = tempfile.mkdtemp(prefix='selftest_v405_')
ok = bad = 0
notdemo = []
missing = []
for fn, old, new in CASES:
    src = open(os.path.join(HERE, fn)).read()
    if old not in src:
        print('  MISSING  %-22s %s' % (fn, old[:70]))
        missing.append((fn, old))
        bad += 1
        continue
    p = src.replace(old, new, 1)
    p = p.replace("HERE = os.path.dirname(os.path.abspath(__file__))",
                  "HERE = %r" % HERE)
    p = p.replace("HERE = __file__.rsplit('/', 1)[0]", "HERE = %r" % HERE)
    p = ("import sys\nsys.path.insert(0, %r)\n" % HERE) + SHIM % (TMP,) + p
    tmp = os.path.join(TMP, '_pert_' + fn)
    open(tmp, 'w').write(p)
    r = subprocess.run([sys.executable, tmp], capture_output=True, text=True,
                       cwd=HERE)
    os.remove(tmp)
    if r.returncode != 0 and 'AssertionError' in r.stderr:
        ok += 1
    else:
        # A perturbation that raises something OTHER than AssertionError has
        # broken the generator rather than tripped its check, and is no
        # evidence that the check works.
        why = ('exited 0' if r.returncode == 0
               else (r.stderr.strip().splitlines() or ['?'])[-1][:90])
        print('  NOT DEMONSTRATED  %-22s %-46s %s' % (fn, old[:46], why))
        notdemo.append((fn, old))
        bad += 1

import shutil
shutil.rmtree(TMP, ignore_errors=True)
print('selftest_v405: %d cases, %d demonstrated failing, %d NOT demonstrated'
      % (len(CASES), ok, bad))
if bad:
    raise SystemExit(1)
