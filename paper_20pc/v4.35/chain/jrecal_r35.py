#!/usr/bin/env python3
r"""jrecal_r35.py -- round 3530: the phase-centre leakage test for ALMA J153702653-33192492 (Referee 2 M3 (1)/(2), v4.35).

Reads the FROZEN measurement record r35inputs/jrecal/jrecal_r35.json (made on the cluster by the r35 J-recal subrun:
the two ACA blocks A002_Xfe62c1_X398 and A002_Xf8f6a9_X10359 re-downloaded and re-calibrated with the census pipeline
-- the re-flag lanes' calib_one_eb.py v5, select_finest_spw, seti_extract_generic, seti_drift_search_generic -- then
(i) the phase-centre field imaged (dirty cube, natural weighting, no cleaning) in each crossing's track channels +-10,
(ii) the extractor's DFT evaluated at the phase centre and the normalised dirty beam at the star's offset per integration,
(iii) the star and phase-centre point sources solved jointly per integration and channel, the search statistic recomputed
for the star alone, the phase centre and the predicted leak, (iv) the visibility fit visfit_r7y.py re-run unmodified with each
window's own drift) and ledger.json (the census crossings), and checks r35inputs/visfit_fix_r35.json against it.  Writes numbers/survey_numbers_round3530.tex and jrecal_r35.json.

  R1 the record covers exactly the unattributed census crossings of the object, and the re-calibration reproduces each:
     the same cell, T* equal to the ledger's to 1e-4, the star spectrum and the control maxima unchanged (|d| <= 1e-6).
  R2 leakage, per crossing: the dirty-beam response at the star to a phase-centre source is below 0.2 in every integration;
     the phase centre is dark on the track (|T_pc| < 3) and in the cube (peak within 7" < 4 rms in every channel); the
     predicted leak is |T| < 1; the star alone still crosses (T >= 5 at the printed precision); the de-drifted map peaks
     within half a synthesised beam of the star.  All five -> "excluded"; a crossing failing the star-alone or leak test
     -> "explains"; anything else -> "undecided".  The verdict count is printed.
  R3 the visibility fit with each window's own drift places every crossing at the star (Re >= 4 sigma, |Im| < 3 sigma,
     Re above every ring control), and the record's archived fits that did NOT use the window's own drift are exactly the
     ones the archive did not localise (the campaign keyed the drift on the execution block).
  R4 the controls: the largest dirty-beam response of a control position to a phase-centre source exceeds the star's
     (a source at the phase centre would light controls before the star).
  R5 r35inputs/visfit_fix_r35.json (the corrected-fit record other generators read) carries the same own-drift fits, and its
     scan of the census fit ledger finds no wrong-drift fit outside this object.

    python3 jrecal_r35.py [--drive N]     N = 1..7: each perturbs one input in memory, prints FAILED and exits 1
                                          without writing a production path
"""
import json
import math
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROUND = 3530
DRIVE = int(sys.argv[sys.argv.index('--drive') + 1]) if '--drive' in sys.argv else None
OUT, FAIL = {}, []
WORD = ('no', 'one', 'two', 'three', 'four', 'five', 'six', 'seven', 'eight', 'nine', 'ten')
word = lambda k: WORD[k] if k < len(WORD) else '%d' % k  # noqa: E731
STAR = 'ALMA J153702653-33192492'
THRESH = 5.0


def m(k, v):
    assert k.isalpha() and k not in OUT, k
    OUT[k] = v


def ck(label, ok, detail=''):
    print('  %-78s %s  %s' % (label[:78], 'PASS' if ok else 'FAIL', detail))
    if not ok:
        FAIL.append(label.split()[0])


def p2(x):
    return '%.2f' % x


print('jrecal_r35: round %d%s' % (ROUND, '' if DRIVE is None else '  (drive %d)' % DRIVE))
REC = json.load(open(os.path.join(HERE, 'r35inputs', 'jrecal', 'jrecal_r35.json')))
X = REC['crossings']
LED = [r for r in json.load(open(os.path.join(HERE, 'ledger.json')))['rows'] if r['star'] == STAR]
UNATT = [r for r in LED if not r.get('attributed')]
if DRIVE == 1:                      # the re-calibration reproduces one crossing's T* only to 0.01
    X[0] = dict(X[0], repro=dict(X[0]['repro'], T_recal=X[0]['repro']['T_recal'] + 0.01))
if DRIVE == 2:                      # the record covers only three of the object's unattributed crossings
    X = X[1:]
if DRIVE == 3:                      # the phase centre lit on one track: the leak predicts most of the star's statistic
    X[1] = dict(X[1], series_T=dict(X[1]['series_T'], phase_centre=12.0, leak_pred=2.5, star_deleaked=4.2))
if DRIVE == 4:                      # one own-drift visibility fit fails the imaginary-part criterion
    X[2] = dict(X[2], visfit=dict(X[2]['visfit'], own=dict(X[2]['visfit']['own'], im=3.4)))
if DRIVE == 5:                      # an archived fit that used its own drift but did not localise (defect premise broken)
    X[0] = dict(X[0], visfit=dict(X[0]['visfit'], archived=dict(X[0]['visfit']['archived'],
                                                                  drift_used=X[0]['visfit']['archived']['event_drift'])))
if DRIVE == 6:                      # every control less exposed to the phase centre than the star
    X = [dict(x, controls=dict(x['controls'], beam_mean_track_max=0.0)) for x in X]

# ---------------------------------------------------------------- R1 coverage and reproduction
key = lambda eb, f: (eb, round(float(f), 3))  # noqa: E731
_led = {key(r['eb'], r['freq']): r for r in UNATT}
_rec = {key(x['eb'], x['freq_GHz']): x for x in X}
ck('R1a the record covers exactly the object\'s unattributed census crossings',
   set(_led) == set(_rec) and len(_rec) == len(X), 'ledger %s vs record %s' % (sorted(_led), sorted(_rec)))
_bad = [k for k, x in _rec.items() if k in _led and not (
    x['repro']['cell_same'] == 1 and abs(x['repro']['T_recal'] - float(_led[k]['tstar'])) <= 1e-4
    and abs(x['repro']['T_recal'] - x['repro']['T_archived']) <= 1e-4
    and x['repro']['max_abs_dI_star_Jy'] <= 1e-6 and x['repro']['max_abs_dctrl_max'] <= 1e-6
    and x['repro']['n_ctrl_ge_star'][0] == x['repro']['n_ctrl_ge_star'][1])]
ck('R1b re-calibration reproduces every crossing (cell, T* to 1e-4 of the ledger, spectrum and controls)',
   not _bad, 'failing %s' % _bad)
_dT = max(abs(x['repro']['T_recal'] - x['repro']['T_archived']) for x in X)
_dI = max(x['repro']['max_abs_dI_star_Jy'] for x in X)

# ---------------------------------------------------------------- R2 leakage verdict per crossing
VERD = {}
for k, x in sorted(_rec.items()):
    b = x['beam_at_star']; s = x['series_T']; c = x['cube']; ti = x['track_image']
    syn_half = 0.5 * min(b['beam_tclean_arcsec'])
    beam_small = max(abs(b['min']), abs(b['max']), abs(b['psf_tclean'])) < 0.2
    pc_dark = abs(s['phase_centre']) < 3.0 and c['max_peak7_over_rms'] < 4.0 and c['max_abs_pc_over_rms'] < 4.0
    leak_small = abs(s['leak_pred']) < 1.0
    star_alone = round(s['star_deleaked'], 2) >= THRESH
    at_star = ti['peak_offset_from_star_arcsec'] <= syn_half
    if not star_alone or not leak_small and abs(s['leak_pred']) >= s['star_mine'] - THRESH:
        v = 'explains'
    elif beam_small and pc_dark and leak_small and star_alone and at_star:
        v = 'excluded'
    else:
        v = 'undecided'
    VERD[k] = v
    print('    %s %.3f GHz: |B|max %.3f  T_pc %+.2f  cube %.2f/%.2f rms  leak %+.2f  star alone %.2f  map peak %.2f" '
          '(half beam %.2f") -> %s' % (k[0][-6:], k[1], max(abs(b['min']), abs(b['max']), abs(b['psf_tclean'])),
                                       s['phase_centre'], c['max_peak7_over_rms'], c['max_abs_pc_over_rms'],
                                       s['leak_pred'], s['star_deleaked'], ti['peak_offset_from_star_arcsec'], syn_half, v))
NEX = sum(v == 'excluded' for v in VERD.values())
NEXPL = sum(v == 'explains' for v in VERD.values())
ck('R2 leakage from the phase centre is excluded for every crossing (beam < 0.2, phase centre dark, |leak T| < 1, '
   'star alone >= 5, map peak at the star)', NEX == len(X) and len(X) > 0, '%s' % VERD)

# ---------------------------------------------------------------- R3 the visibility fit with each window's own drift
_own = [x['visfit']['own'] for x in X]
_loc = [o for o, x in zip(_own, X) if o['re'] >= 4.0 and abs(o['im']) < 3.0 and o['re'] > o['ring_max']
        and abs(o['drift'] - x['drift_Hz_s']) < 0.01]
ck('R3a the own-drift visibility fit places every crossing at the star (Re >= 4, |Im| < 3, Re > every ring control)',
   len(_loc) == len(X), '%d of %d' % (len(_loc), len(X)))
_arch = [x['visfit']['archived'] for x in X]
_wrong = [a for a in _arch if abs(a['drift_used'] - a['event_drift']) > 0.01]
_archloc = [a for a in _arch if a['re'] >= 4.0 and abs(a['im']) < 3.0 and a['re'] > a['ring_max']]
ck('R3b the archived fits that did not use the window\'s own drift are exactly the archived non-localised ones',
   len(_wrong) + len(_archloc) == len(_arch) and all(a not in _archloc for a in _wrong) and len(_wrong) > 0,
   '%d wrong-drift, %d archived localised of %d' % (len(_wrong), len(_archloc), len(_arch)))

# ---------------------------------------------------------------- R4 the controls
_cb = max(x['controls']['beam_mean_track_max'] for x in X)
_sb = max(abs(x['controls']['beam_at_star_mean']) for x in X)
ck('R4 some control position is more exposed to a phase-centre source than the star',
   _cb > _sb, 'control max %.3f vs star %.3f' % (_cb, _sb))

# ---------------------------------------------------------------- R5 the corrected-fit record agrees with this one
FIX = json.load(open(os.path.join(HERE, 'r35inputs', 'visfit_fix_r35.json')))
if DRIVE == 7:                      # the corrected-fit record carries a different Re/sigma for one crossing
    FIX['fits'][0] = dict(FIX['fits'][0], corrected=dict(FIX['fits'][0]['corrected'], re=FIX['fits'][0]['corrected']['re'] + 0.5))
_fk = {key(f['eb'], f['f_cross_GHz']): f for f in FIX['fits']}
_agree = set(_fk) == set(_rec) and all(
    abs(_fk[k]['corrected'][q] - _rec[k]['visfit']['own'][q]) < 1e-4 for k in _rec if k in _fk for q in ('re', 'im', 'ring_max'))
_cw = {key(c['eb'], c['f']) for c in FIX['census_scan']['census_wrong_drift']}
_rw = {key(x['eb'], x['freq_GHz']) for x in X if abs(x['visfit']['archived']['drift_used'] - x['visfit']['archived']['event_drift']) > 0.01}
ck('R5 visfit_fix_r35.json carries this record\'s own-drift fits, and its census scan finds no wrong-drift fit outside this object',
   _agree and _cw == _rw and FIX['census_scan']['n_census_wrong_drift'] == len(_rw),
   'agree %s; census wrong-drift %d (%s) vs this object %d' % (_agree, len(_cw), sorted(_cw), len(_rw)))

if FAIL:
    print('\nFAILED: %s' % ', '.join(FAIL))
    sys.exit(1)
if DRIVE is not None:
    print('jrecal_r35: drive %d passed every check -- it did NOT fire' % DRIVE)
    sys.exit(0)

# ---------------------------------------------------------------- macros
_B = [abs(v) for x in X for v in x['beam_at_star']['per_int']] + [abs(x['beam_at_star']['psf_tclean']) for x in X]
_sa = [x['series_T']['star_deleaked'] for x in X]
_pc = [x['series_T']['phase_centre'] for x in X]
m('JrBeamAbsMax', p2(max(_B)))
m('JrPcTLo', '%.1f' % min(_pc)); m('JrPcTHi', '%.1f' % max(_pc))
m('JrCubeSnrMax', '%.1f' % max(max(x['cube']['max_peak7_over_rms'], x['cube']['max_abs_pc_over_rms']) for x in X))
m('JrLeakTMax', p2(max(abs(x['series_T']['leak_pred']) for x in X)))
m('JrAloneLo', p2(min(_sa))); m('JrAloneHi', p2(max(_sa)))
m('JrMapOffMax', '%.1f' % max(x['track_image']['peak_offset_from_star_arcsec'] for x in X))
m('JrCtrlBeamMax', p2(_cb))
_re = [o['re'] for o in _own]
m('JrVfReLo', '%.1f' % min(_re)); m('JrVfReHi', '%.1f' % max(_re))
m('JrVfImAbsMax', '%.1f' % max(abs(o['im']) for o in _own))
m('JrVfRingMax', '%.1f' % max(o['ring_max'] for o in _own))
m('JrVfNWrongDriftWord', word(len(_wrong)))
_wr = sorted(a['re'] for a in _wrong)
m('JrVfOldReLo', '%.1f' % _wr[0]); m('JrVfOldReHi', '%.1f' % _wr[-1])
with open(os.path.join(HERE, 'numbers/survey_numbers_round%d.tex' % ROUND), 'w') as fh:
    fh.write('%% GENERATED by jrecal_r35.py (round %d) -- do not hand-edit.\n' % ROUND)
    for k in sorted(OUT):
        fh.write('\\newcommand{\\%s}{%s}\n' % (k, OUT[k]))
json.dump(dict(generated_by='jrecal_r35.py', round=ROUND, verdicts={'%s|%.3f' % k: v for k, v in VERD.items()},
               macros=OUT), open(os.path.join(HERE, 'jrecal_r35.json'), 'w'), indent=1)
print('jrecal_r35: %d macros, verdicts %s' % (len(OUT), sorted(set(VERD.values()))))
