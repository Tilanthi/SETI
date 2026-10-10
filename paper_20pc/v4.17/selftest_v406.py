#!/usr/bin/env python3
"""GATE (v4.06): drive every assertion added in this cycle, one at a time, and
require it to FAIL.

A check that cannot fail is not a check.  Six instances were found in this
project on 2026-09-26 alone -- one of them inside a sibling's own newly written
assertion, which compared a shipped column against the map that column is
computed from and therefore could not fail at all.  So every assertion added in
the v4.06 cycle is demonstrated failing here rather than declared to pass.

★ The perturbation must be driven in whichever direction the literal can move.
Tightening a bound that is already met by a wide margin proves nothing, so the
cases below loosen, invert, swap a key, or reintroduce the superseded code.

★ THE HEADLINE CASE is the C_resp keying: `selftest` reinstates the binary
`abs(fs_ratio - 2.0) >= HAN_RATIO_TOL` flag that v4.05 shipped and requires the
new assertion to fire on it, naming 51 Eri.  That is the tripwire driven in the
direction its literal actually moved.

Writes are redirected into a scratch directory by a shim on `builtins.open`,
so no released product can be touched; cwd is the version directory so every
READ resolves.  A symlink farm would not do -- `open(path, 'w')` follows a
symlink and would truncate the real product.
"""
import os
import subprocess
import sys
import shutil
import tempfile

import manuscript

HERE = os.path.dirname(os.path.abspath(__file__))

CASES = [
    # ================= D18: the C_resp averaging key (v342_calc.py) ========
    # (1) REINSTATE the superseded binary flag.  The new assertion must fire
    #     and name the mis-keyed window.  This is the whole point of the fix.
    ('v342_calc.py',
     """    r['n_avg'] = (1 if r['fs_ratio'] is None
                  else min(_FWN, key=lambda n: abs(r['fs_ratio'] - _FWN[n])))
    r['han_avg'] = r['n_avg'] != 1""",
     """    r['han_avg'] = (r['fs_ratio'] is not None
                    and abs(r['fs_ratio'] - HAN_RATIO) >= HAN_RATIO_TOL)
    r['n_avg'] = N_AVG if r['han_avg'] else 1"""),
    # (2) the "matches SOME modelled factor" clause: drop n = 4 from the
    #     modelled set and the 1953 kHz window matches nothing within 3 %.
    ('v342_calc.py',
     "_FWN = {int(n): float(v) for n, v in _CR['fwhm_by_n'].items()}",
     "_FWN = {int(n): float(v) for n, v in _CR['fwhm_by_n'].items() "
     "if int(n) != 4}"),
    # (3) invert the mis-key assertion, so a real disagreement passes silently
    ('v342_calc.py', "assert not _mis, (", "assert _mis, ("),
    # (4) the third state must be OCCUPIED in the catalogue (crespkey_v406)
    ('crespkey_v406.py', "assert len(KEYED[4]) == 1, len(KEYED[4])",
     "assert len(KEYED[4]) == 2, len(KEYED[4])"),
    # (5) the covariance branches must be far apart, or the validation cannot
    #     distinguish them -- collapse the prediction and it must fire
    ('crespkey_v406.py', "assert PRED[1][0] / PRED[4][0] > 4.0, PRED",
     "assert PRED[1][0] / PRED[4][0] > 40.0, PRED"),
    # (6) the closed-form n = 1 prediction, which the paper quotes as 2/3
    ('crespkey_v406.py', "TAPER = np.array([0.25, 0.50, 0.25])",
     "TAPER = np.array([0.20, 0.60, 0.20])"),
    # (7) every measured window must confirm its own key.  Swap the measured
    #     n = 4 record's channel width onto the n = 2 population's and the
    #     agreement assertion must break.
    ('crespkey_v406.py',
     "    rows.append((int(r['n_chan_avg']), d, r))",
     "    rows.append((2 if int(r['n_chan_avg']) == 4 "
     "else int(r['n_chan_avg']), d, r))"),
    # (8) the sample must contain a channel width in two averaging classes,
    #     else it cannot demonstrate that channel width is not a key
    ('crespkey_v406.py', "assert _both, (", "assert not _both, ("),
    # (9) the mis-keyed window must carry no crossing -- if it did, this would
    #     be a candidate-list change and not a limits correction
    ('crespkey_v406.py', "assert FOUR['crossing'] != 'True', FOUR['crossing']",
     "assert FOUR['crossing'] == 'True', FOUR['crossing']"),
    # (10) the system limit must really move, i.e. the window must be the
    #      system's deepest; otherwise the 51 Eri sentence is wrong
    ('crespkey_v406.py', "assert _deep_new == _eirp_now, (_deep_new, _eirp_now)",
     "assert _deep_new != _eirp_now, (_deep_new, _eirp_now)"),
    # (11) P90^sel must be a pure multiple of the nominal power, i.e. free of
    #      the response correction.  Fold the correction in and it must fire.
    # ★ v4.11: the retired column is renamed in the catalogue, and crespkey
    # now reads it through `adopted_e90.RETIRED_COLUMN_RENAMED` -- the one
    # remaining legitimate use of it, an assertion ABOUT the superseded
    # column rather than a publication of it.  The perturbation is the same:
    # fold the response correction into the denominator and the clause must
    # fire.
    ('crespkey_v406.py',
     '_sel_ratio = {round(float(r[_SUPCOL]) / float(r["eirp_nominal_W"]), 4)',
     '_sel_ratio = {round(float(r[_SUPCOL]) / '
     'float(r["eirp_eff_total_W"]), 4)'),
    # (12) the pooled lag-1 must sit on the n = 1 branch, which is what makes
    #      the matched-filter gain an n = 1 gain
    ('crespkey_v406.py',
     "assert abs(np.median(_all1) - np.median(_n1)) < 0.05, (np.median(_all1),",
     "assert abs(np.median(_all1) - np.median(_n1)) < 0.0005, (np.median(_all1),"),

    # ================= D16: the trigger-uniformity reframing ===============
    # (13) the coverage gap must stay small, or the catalogue columns ship
    #      mostly blank -- the fifth instance of the blank-field family
    ('v342_calc.py', "assert len(_SC_UNCOV) < 0.05 * len(GOOD), (",
     "assert len(_SC_UNCOV) < 0.0005 * len(GOOD), ("),
    # (14) two windows that the join cannot tell apart must be counted, not
    #      resolved by picking one
    ('v342_calc.py', "assert len(_SC_AMBIG) <= 5, (",
     "assert len(_SC_AMBIG) <= 0, ("),
    # (15) the cell count must span decades, or this whole section is a fuss
    #      about nothing.  Collapse it by keying every window to the median.
    ('trigunif_v406.py',
     "CELLS = np.array([float(r['n_search_cells']) for r in COV])",
     "CELLS = np.array([354.0 for r in COV])"),
    # (16) the broken-window count must be independent of the cut
    ('trigunif_v406.py',
     "assert len({len(both[t]) for t in FLAGTH}) == 1, {t: len(both[t])",
     "assert len({len(either[t]) for t in FLAGTH}) == 1, {t: len(both[t])"),
    # (17) ... and must be exactly one
    ('trigunif_v406.py', "assert len(both[1.2]) == 1, [r['star_name']",
     "assert len(both[1.2]) == 2, [r['star_name']"),
    # (18) the flat threshold must be wrong in BOTH directions; force every
    #      window's requirement above 5 and the clause must fire
    ('trigunif_v406.py',
     "TW = np.array([float(r['trigger_1pct_window']) for r in COV])",
     "TW = np.array([float(r['trigger_1pct_window']) + 10.0 for r in COV])"),
    # (19) the three routes must AGREE: a bracket whose ends differ by a
    #      factor 2 is not a bracket
    ('trigunif_v406.py', "assert max(_routes) / min(_routes) < 1.5, _routes",
     "assert max(_routes) / min(_routes) < 1.05, _routes"),
    # (20) the survey-wide requirement is the stricter one
    ('trigunif_v406.py',
     "    return sum(1 for r in XC if float(r['star_snr']) < float(r[col]))",
     "    return sum(1 for r in XC if float(r['star_snr']) > float(r[col]))"),
    # (21)+(22) eta Crv must be below BOTH of its own requirements
    ('trigunif_v406.py',
     "assert float(_eta['star_snr']) < float(_eta['trigger_1pct_window']), _eta",
     "assert float(_eta['star_snr']) > float(_eta['trigger_1pct_window']), _eta"),
    ('trigunif_v406.py',
     "assert float(_eta['star_snr']) < float(_eta['trigger_1pct_survey']), _eta",
     "assert float(_eta['star_snr']) > float(_eta['trigger_1pct_survey']), _eta"),
    # (23) the morphology item must be reported as a null, i.e. a factor > 1
    ('trigunif_v406.py',
     "assert N['morph']['p90_factor'] > 1.0, 'this item is reported as a null'",
     "assert N['morph']['p90_factor'] < 1.0, 'this item is reported as a null'"),
    # (24) the "62/85/98 per cent of false alarms" figures must reproduce from
    #      the measured slope, not be transcribed
    ('trigunif_v406.py', "_pred = 1.0 - np.exp(-_sl * N['morph']['thresh_old']",
     "_pred = 1.0 - np.exp(-2.0 * _sl * N['morph']['thresh_old']"),
    # (25) the falsifier: the width cut must reject resolved lines EVERY time
    ('trigunif_v406.py',
     "assert N['morph']['reject_resolved_line'] == N['morph']['reject_resolved_line_n']",
     "assert N['morph']['reject_resolved_line'] > N['morph']['reject_resolved_line_n']"),
    # (26) the quantisation net must be at or below unity on both sides
    ('trigunif_v406.py', "assert Q['net'] <= 1.0 and Q['net_rank'] <= 1.0, Q",
     "assert Q['net'] >= 1.0 and Q['net_rank'] >= 1.0, Q"),
    # (27) THE DOUBLE-CORRECTION TRIPWIRE: the campaigns must draw drift
    #      continuously, or the loss is NOT already inside P90^sel
    ('trigunif_v406.py',
     "assert Q['injection_draws_continuous'] is True, Q",
     "assert Q['injection_draws_continuous'] is False, Q"),
    # (28) our yield must move the OPPOSITE way to the TurboSETI artefact
    ('trigunif_v406.py',
     "assert D['yield_ratio_double'] >= 1.0, 'the sign is the opposite",
     "assert D['yield_ratio_double'] <= 1.0, 'the sign is the opposite"),
    # (29) no deduplication window may exist in our search
    ('trigunif_v406.py',
     "assert D['dedup_windows_in_our_code'] == 0, D",
     "assert D['dedup_windows_in_our_code'] == 1, D"),
    # (30) the two matched filters must coincide at a channel centre
    ('trigunif_v406.py',
     "assert abs(F['gain_at_centre'] - F['gain_fixed_at_centre']) < 1e-9, F",
     "assert abs(F['gain_at_centre'] - F['gain_fixed_at_centre']) < -1.0, F"),
    # (31) the offset-matched bank cannot be worse than one fixed filter
    ('trigunif_v406.py',
     "assert F['gain_matched_mean_offset'] >= F['gain_fixed_mean_offset'], F",
     "assert F['gain_matched_mean_offset'] <= F['gain_fixed_mean_offset'], F"),
    # (32) the naive figure must be exactly sqrt(3/2) -- the point of quoting it
    ('trigunif_v406.py',
     "assert abs(F['naive_lag1_only'] - np.sqrt(1.5)) < 1e-9, F",
     "assert abs(F['naive_lag1_only'] - np.sqrt(2.5)) < 1e-9, F"),
    # (33) the fixed filter must be a LOSS at a channel boundary
    ('trigunif_v406.py', "assert F['gain_fixed_at_boundary'] < 1.0, (",
     "assert F['gain_fixed_at_boundary'] > 1.0, ("),

    # ================= D17: the multi-epoch stack =========================
    # (34) the reflex-motion figure must be TENS of channels.  The defect this
    #      replaces stated 47,000; shrink the channel and the clause fires.
    ('stack_v408.py', "assert 10 < REFLEX_KMS / _tol < 200, REFLEX_KMS / _tol",
     "assert 10000 < REFLEX_KMS / _tol < 200000, REFLEX_KMS / _tol"),
    # (35) the reference channel must be the MODE of the sub-MHz widths, not
    #      the median over all of them -- 257 of 394 groups are 15.6 MHz TDM
    ('stack_v408.py', "_fine = [r['chanw'] for r in R if r['chanw'] < 1e6]",
     "_fine = [r['chanw'] for r in R]"),
    # (36) the excluded anomalous-weight products must be a small minority
    ('stack_v408.py', "assert len(bw) < 0.02 * len(win), (len(bw), len(win))",
     "assert len(bw) < 0.002 * len(win), (len(bw), len(win))"),
    # (37) "zero unattributed" must be COMPUTED.  Shrink the mask half-width
    #      to 0.1 km/s and both beta Pic CO survivors become unattributed.
    ('stack_v408.py', "    ATTR_KMS = 50.0", "    ATTR_KMS = 0.1"),
    # (38) ... and the clause that proves "zero unattributed" COULD have come
    #      out otherwise must itself be able to fail.  v4.06 drove the typed
    #      \StkNUnattributed against the computed count; v4.08 deleted that
    #      typed macro (D31 s6.6) and replaced it with a both-ways drive, so
    #      what is driven here is the FALSIFYING direction -- widen the tight
    #      tolerance until it stops rejecting the survivors, and the clause
    #      must fire.
    ('stack_v408.py', "    assert len(_unattributed(1.0)) == len(cand), (",
     "    assert len(_unattributed(200.0)) == len(cand), ("),
    # (39) every star named in the persistence list must be present.  Misspell
    #      one key -- exactly the bug this assertion exists to catch.
    ('stack_v408.py', "PERSIST = ['taucet', '61vir', 'cp-722713',",
     "PERSIST = ['tauceti', '61vir', 'cp-722713',"),
    # (40) at most one of the nine may exceed the pre-registered threshold
    ('stack_v408.py', "assert len(_above) <= 1, _above",
     "assert len(_above) <= 0, _above"),
    # (41) the one that does must be beaten by its OWN controls
    ('stack_v408.py', "assert _ctrl[k] > _byk[k], (k, _byk[k], _ctrl[k])",
     "assert _ctrl[k] < _byk[k], (k, _byk[k], _ctrl[k])"),
    # (42) none of the nine may pass the full criterion
    ('stack_v408.py',
     "assert not _surv, [(r['star'], r['z_star']) for r in _surv]",
     "assert _surv, [(r['star'], r['z_star']) for r in _surv]"),
    # (43) N_eff and N must differ materially, or the qualifier is decoration
    ('stack_v408.py',
     "assert np.median(gb / sne) / np.median(gb / np.sqrt(nn)) > 1.1,",
     "assert np.median(gb / sne) / np.median(gb / np.sqrt(nn)) > 2.0,"),
    # (44) the survivors' attribution must be against a real line list
    ('stack_v408.py',
     "LINES = {'CO(1-0)': 115.2712018, 'CO(2-1)': 230.5380000,",
     "LINES = {'CO(1-0)': 15.2712018, 'CO(2-1)': 30.5380000,"),

    # ================= residue =============================================
    # (45) the derived resolution class must AGREE with the stored label
    #      wherever one exists -- the repair rests on that
    ('freqocc_v405.py', "FINE_MAX_HZ = 1e6", "FINE_MAX_HZ = 1e8"),
    # (46) ... and it must MOVE something, or it is a no-op dressed as a fix
    ('freqocc_v405.py', "assert n_relabelled > 0, n_relabelled",
     "assert n_relabelled > 100, n_relabelled"),
    ('freqocc_v405.py', "assert n_fine_derived > n_fine, (n_fine_derived,",
     "assert n_fine_derived < n_fine, (n_fine_derived,"),
    # (47) every habitable-zone star named in Sec. 6.5 must be in the
    #      catalogue.  Misspell one -- the defect the typed list allowed.
    ('hzlist_v406.py', "    'LHS 1140':     ('LHS~1140'",
     "    'LHS 1140b':    ('LHS~1140'"),
    # (48) the formatted list and the count must not drift apart
    ('hzlist_v406.py', "assert M['HzList'].count(',') == len(order) - 2",
     "assert M['HzList'].count(',') == len(order) - 1"),
    # (49) exactly one entry carries its own citation in the prose
    ('hzlist_v406.py', "assert len(_cited) == 1, _cited",
     "assert len(_cited) == 2, _cited"),
    # (50) the crossings among them must sit in a bounded number of blocks
    ('hzlist_v406.py', "assert len(_xblocks) <= 3, _xblocks",
     "assert len(_xblocks) <= 1, _xblocks"),
    # (51) the M-dwarf census row must be found in the generated table
    ('hzlist_v406.py', r"\\quad M \(\$<3900\$\\,K\) & (\d+) \([^)]*\) & (\d+) ",
     r"\\quad M \(\$<3800\$\\,K\) & (\d+) \([^)]*\) & (\d+) "),
    # (52) half-up rounding: the naive printf form must be DEMONSTRATED wrong
    ('numfmt_v406.py', "((58, 400), 2, '0.15', '0.14'),",
     "((58, 400), 2, '0.14', '0.14'),"),
    # (53) ... and at least one case must actually differ, or the module
    #      is solving nothing
    ('numfmt_v406.py',
     "             [(c[0], c[1], c[2], c[3]) for c in CASES]), 'no case differs'",
     "             [(c[0], c[1], c[2], c[3]) for c in CASES][-1:]), "
     "'no case differs'"),

    # ================= D14: the P90^sel redefinition =======================
    # (54) localisation is a FURTHER requirement, so it cannot make a carrier
    #      easier to find; invert the clause and it must fire
    ('sel_curve.py', "assert SEL[_c] >= TRIG[_c] - 1e-9, (_c, TRIG[_c], SEL[_c])",
     "assert SEL[_c] <= TRIG[_c] - 1e-9, (_c, TRIG[_c], SEL[_c])"),
    # (55) the redefinition must MOVE the Class A limit by about a factor two,
    #      or it is not the change D14 describes
    ('sel_curve.py', "assert 1.5 < GAIN['fine'] < 2.5, GAIN",
     "assert 2.5 < GAIN['fine'] < 3.5, GAIN"),
    # (56) ★ and the rank gate must be the REASON: the two campaigns'
    #      trigger-only points must agree, or the factor is a difference
    #      between campaigns and not between criteria.  This is the clause that
    #      stops 5.70 (M3a, rank) being divided by 2.88 (round 7, localised)
    #      and the quotient being called the cost of the rank screen.
    ('sel_curve.py',
     "assert abs(TRIG['fine'] / TRIG_M3A['fine'] - 1.0) < 0.10, (TRIG['fine'],",
     "assert abs(TRIG['fine'] / TRIG_M3A['fine'] - 1.0) < 0.001, (TRIG['fine'],"),
    # (57) the campaign's pre-committed null ceiling
    ('sel_curve.py',
     "assert _R7['gates']['null_frac_localised'] < _R7['gates'][",
     "assert _R7['gates']['null_frac_localised'] > _R7['gates']["),
    # (58) MOVED (v4.11).  The guard that the retired x2.876 criterion
    # cannot come back now lives where the adopted value is formed, in
    # `adopted_e90.py`, and is driven by `adopted_e90.py --selftest`
    # (clause A6) rather than from here: this file runs before
    # strata_v411.py and pxapply_v411.py write the records that module
    # reads, so a case here could only ever report a FileNotFoundError
    # on a clean tree -- a self-test reporting a pass because its
    # perturbation never ran.
    # (59) the three-clause and single-clause localisation rates must agree,
    #      or "localisation rejects nothing" is a claim about one clause
    ('p90r7_v406.py', "assert abs(F_LOC - F_LOC_THREE) < 0.015, (F_LOC, F_LOC_THREE)",
     "assert abs(F_LOC - F_LOC_THREE) < 0.0001, (F_LOC, F_LOC_THREE)"),
    # (60) ★★ THE RE-DERIVATION, not a relabelling: the two expectations must
    #      differ by more than an order of magnitude
    ('p90r7_v406.py', "assert E_CHAIN / _old > 10.0, (",
     "assert E_CHAIN / _old > 100.0, ("),
    # (61) the expectation is a NULL, so it may not exceed what was observed by
    #      a factor that would make it absurd
    ('p90r7_v406.py', "assert 0.5 * E_CHAIN <= len(_xAcov), (E_CHAIN, len(_xAcov))",
     "assert 5.0 * E_CHAIN <= len(_xAcov), (E_CHAIN, len(_xAcov))"),
    # (62) the computed disposition column must still say 'unattributed', or the
    #      comparison population is silently empty
    ('p90r7_v406.py',
     "         if r['disposition_computed'].strip() == 'unattributed']",
     "         if r['disposition_computed'].strip() == 'unattributedX']"),
    # (63) the mask occupancy must be a real fraction
    ('p90r7_v406.py', "assert 0.0 < _occ < 1.0, _occ",
     "assert 0.0 < _occ < 0.001, _occ"),
    # (64) was a SOURCE perturbation of roundcollide.py's writer pattern, and
    #      it is gone.  See BEHAVIOUR_CASES below: the string it edited no
    #      longer exists, because roundcollide was defeated a third time and
    #      fixed twice over -- the name list was widened AND a second,
    #      independent route was added that reads each round file's own
    #      "GENERATED by" header.  So perturbing the name list can no longer
    #      produce a "NO WRITER" at all: the case could not fire, reported
    #      MISSING, exited 1, and KILLED make_all.sh with no output, because
    #      every generator before it is redirected to /dev/null.
    #      ★ A self-test keyed on a source string of the thing it tests does
    #      not merely go stale when that thing is correctly fixed -- it stops
    #      the build.  Re-keyed on the gate's BEHAVIOUR instead.
]

# ---------------------------------------------------------------------------
# BEHAVIOUR CASES.  A case here does not edit its subject's source: it builds
# an input that the gate is supposed to reject and requires the gate to reject
# it.  That survives any reimplementation of the gate, which is the whole
# point -- the source-perturbation form above tests how a gate is written, and
# this form tests what it does.
#
# ★ D36's standing rule is honoured by construction: NOTHING is written into
# the production directory.  The scratch tree is a symlink farm over it, so
# `os.listdir`/`glob` see every real file by name while the only REAL files in
# it are the ones this test makes.  roundcollide.py takes its HERE from
# `__file__`, so running the symlinked copy makes the scratch tree its world.
def _behaviour_roundcollide_collision():
    """Two generators writing one round file must be reported as a COLLISION.

    This is the condition roundcollide.py exists for, and the one the old
    case 64 was trying to reach by crippling the gate's writer detection.
    """
    import glob as _g
    d = tempfile.mkdtemp(prefix='selftest_v406_behav_')
    try:
        for f in os.listdir(HERE):
            src = os.path.join(HERE, f)
            dst = os.path.join(d, f)
            if not os.path.exists(dst):
                os.symlink(src, dst)
        # a round file number no real round uses, so nothing real is shadowed
        rnd = 'survey_numbers_round997.tex'
        with open(os.path.join(d, rnd), 'w') as fh:
            fh.write('%% GENERATED by _collide_a_v406.py -- scratch\n')
        for stub in ('_collide_a_v406.py', '_collide_b_v406.py'):
            with open(os.path.join(d, stub), 'w') as fh:
                fh.write("OUT = '%s'\n" % rnd)
                fh.write("open(OUT, 'w').write('')\n")
        # and the manuscript must \input it, or the file is an ORPHAN rather
        # than a collision and we would be demonstrating the wrong clause.
        main = os.path.basename(manuscript.main_file())
        txt = open(os.path.join(HERE, main)).read().replace(
            '\\input{regen_count}',
            '\\input{survey_numbers_round997}\n\\input{regen_count}', 1)
        os.remove(os.path.join(d, main))
        open(os.path.join(d, main), 'w').write(txt)
        r = subprocess.run([sys.executable, os.path.join(d, 'roundcollide.py')],
                           capture_output=True, text=True, cwd=d)
        hit = ('COLLISION %s' % rnd) in r.stdout
        raised = r.returncode != 0 and 'AssertionError' in r.stderr
        if hit and raised:
            return True, ''
        return False, ('collision reported=%s, raised=%s | %s'
                       % (hit, raised,
                          (r.stdout + r.stderr).strip().splitlines()[-1][:80]
                          if (r.stdout + r.stderr).strip() else '(silent)'))
    finally:
        shutil.rmtree(d, ignore_errors=True)


BEHAVIOUR_CASES = [
    ('roundcollide.py', 'two generators writing one round file are a '
     'COLLISION', _behaviour_roundcollide_collision),
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

TMP = tempfile.mkdtemp(prefix='selftest_v406_')
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
        # A perturbation that raises something OTHER than AssertionError has
        # broken the generator rather than tripped its check, and is no
        # evidence that the check works.
        why = ('exited 0' if r.returncode == 0
               else (r.stderr.strip().splitlines() or ['?'])[-1][:90])
        print('  NOT DEMONSTRATED  %-22s %-46s %s' % (fn, old[:46], why))
        notdemo.append((fn, old))
        bad += 1

shutil.rmtree(TMP, ignore_errors=True)

for _sub, _what, _fn in BEHAVIOUR_CASES:
    _good, _why = _fn()
    if _good:
        ok += 1
    else:
        print('  NOT DEMONSTRATED  %-22s %-46s %s' % (_sub, _what[:46], _why))
        notdemo.append((_sub, _what))
        bad += 1

print('selftest_v406: %d cases (%d source, %d behaviour), '
      '%d demonstrated failing, %d NOT demonstrated'
      % (len(CASES) + len(BEHAVIOUR_CASES), len(CASES), len(BEHAVIOUR_CASES),
         ok, bad))
if bad:
    raise SystemExit(1)
