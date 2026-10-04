#!/usr/bin/env python3
"""GATE (v4.08): drive every assertion added in this cycle, one at a time, and
require it to FAIL.

A check that cannot fail is not a check, and this project has now shipped
EIGHT instances of one particular variant: a quantity selected on a TYPED key,
or typed outright, which disappears rather than goes wrong.  An absent macro
is neither empty nor NaN, so the generators' own "0 empty, 0 nan" gate cannot
see it.  The merge of D31 would have deleted nine \\StkProx* macros that way.

★ THE HEADLINE CASES here are therefore the two macro-count pins.  Both
generators now assert `len(M) == N` with `==`, and both are driven: change the
count and the build must stop.  Case 1 reinstates the exact defect -- the
literal `r['skey'] == 'proximacen'` -- and requires the new assertion to fire
by name rather than to pass silently with nine macros missing.

★ Where an assertion has two directions, BOTH are driven.  The attribution
window, the on-sky calibration of the parallax loss model, the apparent-flux
convention of the injection ladder and the predicted-depth monotonicity each
get a case in each direction, because a one-sided drive of a two-sided claim
is the same mistake in a different place.

Writes are redirected into a scratch directory by a shim on `builtins.open`,
so no released product can be touched; cwd is the version directory so every
READ resolves.  A symlink farm would not do -- `open(path, 'w')` follows a
symlink and would truncate the real product.
"""
import os
import subprocess
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))

CASES = [
    # ============ D31: the star key, and the macro that disappears ========
    # (1) ★★★ REINSTATE THE DEFECT.  Select Proxima on the search-time
    #     directory name again.  Under the merged keys that selection is
    #     empty, and without `assert px` nine macros would vanish in silence.
    ('stack_v408.py',
     "    px = [r for r in R if r['skey'] in _prox or r['skey'] == 'proximacen']",
     "    px = [r for r in R if r['skey'] == 'proximacen']"),
    # (2) ★★★ THE MACRO COUNT IS PINNED WITH ==.  Move the pin and the build
    #     must stop -- this is the only check that can see a macro that is
    #     absent rather than empty.
    ('stack_v408.py', "os.environ.get('STACK_NMACRO', '114')",
     "os.environ.get('STACK_NMACRO', '113')"),
    # (3) the identity map must actually be used for the persistence list: put
    #     the raw directory names back and the `_miss` tripwire must fire.
    ('stack_v408.py',
     "    PERSIST = sorted({_idmap.get(k, k) for k in PERSIST})",
     "    PERSIST = sorted(set(PERSIST))"),
    # (4) the merge must not lose or gain a star
    ('stack_v408.py',
     "        == len({r['skey'] for r in R}), 'the merge lost or gained a star'",
     "        == len({r['skey'] for r in R}) + 1, 'the merge lost or gained a star'"),
    # (5) ★★ the PREDICTED depth is the monotone quantity and may not degrade.
    #     Tighten the tolerance below the float-noise floor and it fires --
    #     which also demonstrates that the 1e-6 is not hiding a real case.
    ('stack_v408.py', "    _PRED_TOL = 1e-6", "    _PRED_TOL = 1e-12"),
    # (6) ... and the other direction: exactly one measured limit degraded,
    #     and it is NAMED.  Require two and the build stops.
    ('stack_v408.py', "    assert len(_worse_meas) == 1, _worse_meas",
     "    assert len(_worse_meas) == 2, _worse_meas"),
    # (7) the diagnosis of that one case -- predicted improved, madZ rose --
    #     must hold, or the explanation printed in the paper is wrong
    ('stack_v408.py',
     "    assert _m4[_w]['madZ'] < _ma[_w]['madZ'] < 1.2, _w",
     "    assert _m4[_w]['madZ'] > _ma[_w]['madZ'], _w"),
    # (8) the realisation term must be centred on unity: a biased madZ is a
    #     different statement from a noisy one
    ('stack_v408.py',
     "    assert abs(np.median(_mz) - 1) < _mzs, (np.median(_mz), _mzs)",
     "    assert abs(np.median(_mz) - 1) < 1e-6, (np.median(_mz), _mzs)"),
    # (9) ★★ the two-band positive control must agree to better than one
    #     channel of the coarser line.  It degraded 0.14 -> 0.46 km/s at the
    #     merge, so this clause is close to live and must be shown to bite.
    ('stack_v408.py',
     "        assert _cross < max(_chanw.values()), (",
     "        assert _cross < 0.2 * max(_chanw.values()), ("),
    # (10) ★★ "zero unattributed", driven the OTHER way from selftest_v406's
    #      case 37: the clause proving the count COULD have been non-zero must
    #      itself be able to fail.
    ('stack_v408.py',
     "    assert len(_unattributed(1.0)) == len(cand), (",
     "    assert len(_unattributed(500.0)) == len(cand), ("),

    # ============ D29: the catalogue columns ==============================
    # (11) ★★ the column count is pinned with ==, driven both ways: too few
    ('v342_calc.py', "assert len(COLS) == 62, 'catalogue column count moved to %d' % len(COLS)",
     "assert len(COLS) == 61, 'catalogue column count moved to %d' % len(COLS)"),
    # (12) ... and too many
    ('v342_calc.py', "assert len(COLS) == 62, 'catalogue column count moved to %d' % len(COLS)",
     "assert len(COLS) == 63, 'catalogue column count moved to %d' % len(COLS)"),
    # (13) the primary-beam join must be one-to-one: widen the frequency
    #      tolerance until a window matches more than one entry
    ('v342_calc.py', "PB_FTOL = 0.002          # GHz; windows are ~2 GHz wide",
     "PB_FTOL = 200.0          # GHz; windows are ~2 GHz wide"),

    # ============ D29/D31: the audit generator ============================
    # (14) ★★ its macro count is pinned with == too
    ('pbaudit_v408.py', "os.environ.get('PBAUDIT_NMACRO', '60')",
     "os.environ.get('PBAUDIT_NMACRO', '55')"),
    # (15) smin = 5 rms / A must close on every row.  This is the identity the
    #      two new columns exist to make checkable.
    ('pbaudit_v408.py', "assert worst < 1e-3, 'smin != 5 rms / A on some row",
     "assert worst < 1e-9, 'smin != 5 rms / A on some row"),
    # (16) ★ the justification for shipping pb_atten is that theta_pb_arcsec
    #      is the 12 m beam on the ACA rows.  Compute it with the RIGHT dish
    #      and the assertion must fire -- if it ever stops firing, the
    #      sentence in the paper has to be deleted.
    ('pbaudit_v408.py', "    th12 = 1.22 * (C / fmid) / 12.0 * 206264.806",
     "    th12 = 1.22 * (C / fmid) / 7.0 * 206264.806"),
    # (17) exactly one row had its offset recovered, and it is named
    ('pbaudit_v408.py', "assert nsrc['recovered'] == 1, nsrc",
     "assert nsrc['recovered'] == 2, nsrc"),
    # (18) ★★★ THE INJECTION BIAS.  s_trig must be the APPARENT 5 sigma on
    #      every unit, or A does not cancel and a systematic must be carried.
    ('pbaudit_v408.py',
     "n_app = sum(1 for u in inj if abs(u['strig'] - u['smin_app']) <= 1e-12 * u['strig'])",
     "n_app = sum(1 for u in inj if abs(u['strig'] - u['smin_corr']) <= 1e-12 * u['strig'])"),
    # (19) ... and the other direction: the test is only meaningful if some
    #      unit distinguishes the two conventions.  Raise the threshold past
    #      the largest difference and the vacuity check must fire.
    ('pbaudit_v408.py',
     "             if abs(u['smin_corr'] - u['smin_app']) > 1e-3 * u['smin_app'])",
     "             if abs(u['smin_corr'] - u['smin_app']) > 1e3 * u['smin_app'])"),
    # (20) the provenance gap runs in the CONSERVATIVE direction; reverse the
    #      comparison and the clause that states the direction must fire
    ('pbaudit_v408.py',
     "assert all(g['rms_published_mJy'] > g['rms_surviving_product_mJy'] for g in gap)",
     "assert all(g['rms_published_mJy'] < g['rms_surviving_product_mJy'] for g in gap)"),
    # (21) the gap must not have reached the attenuation columns
    ('pbaudit_v408.py',
     "assert max(g['smin_residual'] for g in gap) < 1e-4, (",
     "assert max(g['smin_residual'] for g in gap) < 1e-9, ("),
    # (22) exactly one crossing among the four, or the sentence naming it is
    #      about the wrong row
    ('pbaudit_v408.py', "assert len(xg) == 1, xg", "assert len(xg) == 2, xg"),
    # (23) ★ the release must carry the 7 m attenuation for ALMA J1537.  The
    #      whole paragraph says the release is RIGHT; assert it.
    ('pbaudit_v408.py', "and a_hi in _rel, \\", "and a_lo in _rel, \\"),
    # (24) the beam-model sensitivity must stay inside the gate's tolerance
    ('pbaudit_v408.py', "assert pbgate_v408.MODELMAX[0] < pbgate_v408.MODEL_TOL",
     "assert pbgate_v408.MODELMAX[0] < 1.01"),

    # ============ D30: the AU Mic on-sky calibration ======================
    # (25) ★★ the on-sky measurement must say the model is PESSIMISTIC.  Swap
    #      measured for predicted and the clause must fire, because an
    #      optimistic model would make the survey table anti-conservative.
    ('parallax_v404.py',
     "PESS = (1 - _may['ratio']) / (1 - _may['predicted_retained'])",
     "PESS = (1 - _may['predicted_retained']) / (1 - _may['ratio'])"),
    # (26) ★★ and the correction must be applied in the direction that REDUCES
    #      the fraction geometry explains.  Apply it the other way round.
    ('parallax_v404.py', "pred_corr = 1 - PESS * (1 - F['med'][i])",
     "pred_corr = 1 - (1 - F['med'][i]) / PESS"),
    # (27) the quoted absolute-scale bound may not be smaller than the
    #      measured residual -- the failure the typed '10' would have had
    ('parallax_v404.py', "m('PxScaleBoundPct', '%d' % math.ceil(100.0 * _resid_hi))",
     "m('PxScaleBoundPct', '10')"),
    # (28) ★ the January comparison is only a SCALE check if the geometry is
    #      negligible there.  Inflate the predicted loss and it must fire.
    ('parallax_v404.py',
     "assert (1 - _jan['predicted_retained']) < _jan['ratio_err'], (",
     "assert (1 - _jan['predicted_retained']) < 0.1 * _jan['ratio_err'], ("),
    # (29) the primary beam is not the term, on either epoch
    ('parallax_v404.py',
     "assert 1 - AU['primary_beam']['atten_at_may_offset'] < 1e-4, AU['primary_beam']",
     "assert 1 - AU['primary_beam']['atten_at_may_offset'] < 1e-9, AU['primary_beam']"),
    # (30) the residual must stay positive: the parallax term does NOT close
    #      the whole gap, which is the claim the appendix makes
    ('parallax_v404.py', "assert 0.0 < resid < 0.15, resid",
     "assert -1.0 < resid < 0.0, resid"),

    # ============ D23/D25: the P90 unit count =============================
    # (31) ★★ plan = record + truncated.  Five units were stopped part-way and
    #      the paper must not silently drop them from the denominator.
    ('p90r7_v406.py', "_plan, _done = 56, A['n_units_total']",
     "_plan, _done = 57, A['n_units_total']"),
    # (32) ★★ record = scored + failed + positive-control failures.  Through
    #      v4.07 three units were unaccounted for in exactly this difference.
    ('p90r7_v406.py', "_npc = len(A['positive_control_failures'])",
     "_npc = 0"),
    # (33) the collect record and the analysis must describe the same campaign
    ('p90r7_v406.py',
     "assert _COL['n_units_scored'] == A['n_units_scored'], 'collect/analysis disagree'",
     "assert _COL['n_units_scored'] == A['n_units_scored'] + 1, 'collect/analysis disagree'"),
    # ============ D32: R2-3 reverses, and R1-5 ============================
    # (34) ★★ the macro count of round 99 is pinned with ==, for the same
    #      reason the stack's is: this cycle's recurring failure is a macro
    #      that is ABSENT, which no value-level gate can see.
    ('p90r7_v406.py', "os.environ.get('P90R7_NMACRO', '115')",
     "os.environ.get('P90R7_NMACRO', '112')"),
    # (35) ★★★ THE TRACKING CLAIM, direction one: tighten the tolerance and
    #      the build must stop, so the 0.25 is not a tolerance that cannot
    #      bite.
    ('p90r7_v406.py', "assert max(abs(r - 1.0) for r in _rat) < 0.25, (",
     "assert max(abs(r - 1.0) for r in _rat) < 0.01, ("),
    # (36) ★★★ ... and direction two: feed it a quantity that does NOT track
    #      T* (the raw Re/sigma instead of the ratio) and it must fire.  A
    #      claim that the two estimators agree has to be able to see that they
    #      do not.
    ('p90r7_v406.py',
     "_rat = [bb['ratio_snrre_over_tstar'][1] for bb in ra['by_recovered_tstar']]",
     "_rat = [bb['snr_re'][1] for bb in ra['by_recovered_tstar']]"),
    # (37) the bin the events live in must be the bin the campaign reports
    ('p90r7_v406.py', "assert _b5['n'] == t5['n'], (_b5['n'], t5['n'])",
     "assert _b5['n'] == t5['n'] + 1, (_b5['n'], t5['n'])"),
    # (38) ★★★ EVERY TRANSCRIBED PERCENTILE IS CHECKED AGAINST THE DEPOSIT.
    #      Invert the side test and the build must stop: that is what makes
    #      the one transcribed set verifiable rather than trusted.
    ('p90r7_v406.py', "    assert (_reval > P16) == (_p > 16), (",
     "    assert (_reval > P16) != (_p > 16), ("),
    # (39) ... and the star keyed in the frozen input must exist in the
    #      ledger.  Break the match and the mis-keying fires by name, not by
    #      silently selecting nothing -- the alias-key family again.
    ('p90r7_v406.py', "for _star, _p in PCT.items():",
     "for _star, _p in [(_k + 'ZZ', _v) for _k, _v in PCT.items()]:"),
    # (40) the count of percentiles is pinned with ==
    ('p90r7_v406.py', "assert len(_pcts) == 6, len(_pcts)",
     "assert len(_pcts) == 7, len(_pcts)"),
    # (41) ★★ FALSIFIER, direction one: the observed events must sit above
    #      what the SUPERSEDED epoch produced for real sources.  Compare
    #      against the 84th percentile instead of the median and it fires --
    #      so the "not comparable" sentence rests on a test that can fail.
    ('p90r7_v406.py',
     "assert min(r['corrected']['re'] for r in _top) > t5['snr_re_r6epoch'][1], (",
     "assert min(r['corrected']['re'] for r in _top) > t5['snr_re_r6epoch'][2], ("),
    # (42) ★★★ FALSIFIER, direction two: at least one observed event must
    #      reach the injected 16th percentile, or "consistent, not excluded"
    #      is not what the data say.  Require ALL of them to and it fires.
    ('p90r7_v406.py',
     "assert max(r['corrected']['re'] for r in _top) > P16, (",
     "assert min(r['corrected']['re'] for r in _top) > P16, ("),
    # (43) the clean-pass census is only the point being made if a control
    #      above 5 is the DEFAULT in Class A ...
    ('p90r7_v406.py',
     "assert (_cc['classA']['n_with_control_ge5'] / _cc['classA']['n_windows']) > 0.5",
     "assert (_cc['classA']['n_with_control_ge5'] / _cc['classA']['n_windows']) > 0.95"),
    # (44) ... and the EXCEPTION in Class B.  Both directions.
    ('p90r7_v406.py',
     "assert (_cc['classB']['n_with_control_ge5'] / _cc['classB']['n_windows']) < 0.5",
     "assert (_cc['classB']['n_with_control_ge5'] / _cc['classB']['n_windows']) < 0.01"),
    # (45) and the median clean control maximum really does reach the trigger
    ('p90r7_v406.py', "assert a['ctrl_top_clean_median'] >= 5.0, a['ctrl_top_clean_median']",
     "assert a['ctrl_top_clean_median'] >= 6.0, a['ctrl_top_clean_median']"),
    # (46) ★★★ R1-5: \RsevNWinA WAS THE TYPED LITERAL 403 while \NWinA moved
    #      to 402 at v4.07.  It is now counted and PINNED with == against the
    #      catalogue macro; move the pin and the build stops.
    ('p90r7_v406.py', "assert _nwinA == _nwinA_macro, (",
     "assert _nwinA == _nwinA_macro + 1, ("),
    # (47) ★★ the WITHDRAWAL of "largest systematic" is itself asserted: the
    #      measured spread must be materially smaller than the bracket it
    #      replaces, or the sentence may not be written.
    ('p90r7_v406.py',
     "assert max(abs(_tlo - 1), abs(_thi - 1)) < 0.5 * max(abs(_old_lo - 1),",
     "assert max(abs(_tlo - 1), abs(_thi - 1)) < 0.05 * max(abs(_old_lo - 1),"),
    # ============ D33: the epsilon Eridani flux-scale check ===============
    # (48) macro count of round 84 pinned with ==
    ('parallax_v404.py', "os.environ.get('PARALLAX_NMACRO', '71')",
     "os.environ.get('PARALLAX_NMACRO', '70')"),
    # (49) ★★ "do not oversell it", direction one: the check must be
    #      CONSISTENT WITH UNITY or it is not a validation at all.
    ('parallax_v404.py', "assert abs(1.0 - _eps_ratio) < _eps_ratio_err, (",
     "assert abs(1.0 - _eps_ratio) < 0.01 * _eps_ratio_err, ("),
    # (50) ★★ ... direction two: it must be LESS precise than the January
    #      comparison, or the paper is quoting the weaker bound as the
    #      stronger one.
    ('parallax_v404.py', "assert _eps_ratio_err > _jan['ratio_err'], (",
     "assert _eps_ratio_err < _jan['ratio_err'], ("),
    # (51) and the two external checks are only INDEPENDENT if they share
    #      neither band nor array
    ('parallax_v404.py', "assert EPS['band'] != '3' and '7 m' in EPS['array'], (",
     "assert EPS['band'] != '6' and '7 m' in EPS['array'], ("),
    # (57) ★★ the OOM mechanism must be big enough to explain the kill and
    #      small enough to fit the machine, COMPUTED from the window's own
    #      shape.  Halve the per-sample size and the explanation stops
    #      explaining -- so the sentence rests on arithmetic, not on a note.
    ('p90r7_v406.py', "_bytes = 2 * FU['n_chan'] * FU['n_row'] * 16",
     "_bytes = 2 * FU['n_chan'] * FU['n_row'] * 2"),
    # (58) and the failed unit really is the search-stage failure the campaign
    #      recorded, by status and by signal
    ('p90r7_v406.py', "assert FU['status'] == 'failed_search_base' and FU['rc'] == -9, FU",
     "assert FU['status'] == 'failed_search_base' and FU['rc'] == -11, FU"),
    # ===== D29, second pass: the closure count was partly tautological =====
    # (52) ★★★ every released row must have a frozen provenance record, or the
    #      independent/tautological split is being made on a silent default.
    ('pbaudit_v408.py', "assert _prov.count(None) == 0, (",
     "assert _prov.count(None) == 1, ("),
    # (53) ★★ the back-solved rows must close to the column's own rounding and
    #      no worse: if they did not, the back-solve itself would be wrong.
    ('pbaudit_v408.py', "assert _worst_taut < 1e-6, _worst_taut",
     "assert _worst_taut < 1e-9, _worst_taut"),
    # (54) ★★★ ... and the two populations must be DISTINGUISHABLE, or the
    #      sentence the paper now prints -- that 1,641 rows are a test and 10
    #      are arithmetic -- is not a statement about the data.
    ('pbaudit_v408.py', "assert _worst_indep > 10 * _worst_taut, (",
     "assert _worst_indep > 1e5 * _worst_taut, ("),
    # (55) the decomposition is pinned with ==
    ('pbaudit_v408.py', "assert len(_taut) == nsrc['inverted'], (len(_taut), nsrc['inverted'])",
     "assert len(_taut) == nsrc['inverted'] + 1, (len(_taut), nsrc['inverted'])"),
    # (56) and the macro count of round 101 is pinned with ==, which is how the
    #      four new macros were caught being added
    # ===================== v4.09: both rank-flagged crossings are fitted ====
    # (57) ★★ the pin that FIRED when the CP-72 2713 fit landed.  Put the old
    #      singular back and it must fire again, so the paragraph in S5.2.2
    #      can never silently go back to naming one of two.
    ('p90r7_v406.py', "assert len(_s1) == 2, [r['star'] for r in _s1]",
     "assert len(_s1) == 1, [r['star'] for r in _s1]"),
    # (58) ... and the other direction: exactly ONE of the two may carry a
    #      deposited percentile, or the transcribed input is being joined to
    #      the wrong crossing.
    ('p90r7_v406.py', "assert len(_named) == 1, (",
     "assert len(_named) == 2, ("),
    # (59) ★★★ and in epoch_v403.py, the mirror assertion: BOTH must now be
    #      fitted.  This is the one that stopped the build and forced
    #      S5.2.3 to be rewritten rather than letting the count slide.
    ('epoch_v403.py', "assert all(r['fitted'] for r in END), (",
     "assert not all(r['fitted'] for r in END), ("),
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

TMP = tempfile.mkdtemp(prefix='selftest_v408_')
ok = bad = 0
for fn, old, new in CASES:
    src = open(os.path.join(HERE, fn)).read()
    if old not in src:
        print('  MISSING  %-22s %s' % (fn, old[:70]))
        bad += 1
        continue
    p = src.replace(old, new, 1)
    p = p.replace("HERE = os.path.dirname(os.path.abspath(__file__))",
                  "HERE = %r" % HERE)
    p = p.replace("DATA = os.path.join(HERE, 'stack_v408')",
                  "DATA = %r" % os.path.join(HERE, 'stack_v408'))
    p = ("import sys\nsys.path.insert(0, %r)\n" % HERE) + SHIM % (TMP,) + p
    tmp = os.path.join(TMP, '_pert_' + fn)
    open(tmp, 'w').write(p)
    r = subprocess.run([sys.executable, tmp], capture_output=True, text=True,
                       cwd=HERE)
    os.remove(tmp)
    if r.returncode != 0 and 'AssertionError' in r.stderr:
        ok += 1
    else:
        why = ('exited 0' if r.returncode == 0
               else (r.stderr.strip().splitlines() or ['?'])[-1][:90])
        print('  NOT DEMONSTRATED  %-20s %-44s %s' % (fn, old[:44], why))
        bad += 1

import shutil
shutil.rmtree(TMP, ignore_errors=True)
print('selftest_v408: %d cases, %d demonstrated failing, %d NOT demonstrated'
      % (len(CASES), ok, bad))
if bad:
    raise SystemExit(1)
