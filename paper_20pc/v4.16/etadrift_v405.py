#!/usr/bin/env python3
"""Round 94 (v4.05, referee 2 minor item 2): how many windows are not
drift-resolving, in BOTH classes.

The referee objects to the claim that all Class A windows are drift-resolving.
The objection is right, and so is the sentence the paper actually depends on;
they are different sentences and the paper conflated them.  Measured from the
released catalogue:

  * Class A spans eta_drift = 0.17-422 and 13 of its 402 windows are below 1.
    (v4.09: this docstring said 403 -- the same stale literal \RsevNWinA
    carried.  Every number this generator EMITS is counted from the
    catalogue; the comment was not, which is why it drifted.)
    The class-wide claim is false and is deleted.
  * But 0 of the 12 stage-1 flagged windows and 0 of the 52 Class A threshold
    crossings are among them, so Appendix J.3's statement is true as written
    and is NARROWED to the population it can support, with its range attached,
    rather than deleted.
  * Symmetrically, 38 of the 1,252 Class B windows have eta_drift >= 1.  The
    instrumental classes do not partition on eta_drift in either direction:
    they are defined on native channel width, which is the right thing to
    define them on, and eta_drift is a derived property that crosses the
    boundary both ways.

The 13 are not a class-boundary effect.  Every one is a short on-source track
(60-181 s) at the coarsest of the fine channel widths (488 or 977 kHz), so it
is the track length and not the class definition that fails: eta_drift =
|nudot_max| tau_track / dnu_ch, and a one-minute track at 977 kHz cannot carry
a carrier across a channel even at the search grid's drift ceiling.

-> survey_numbers_round94.tex
"""
import csv
import os
import statistics as st

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, 'survey_numbers_round94.tex')
ROWS = list(csv.DictReader(open(os.path.join(
    HERE, 'per_target_results_v3.99.csv'))))

M = {}


def m(k, v):
    M[k] = v


def eta(r):
    return float(r['eta_drift'])


A = [r for r in ROWS if r['resolution_class'] == 'fine']
B = [r for r in ROWS if r['resolution_class'] == 'coarse']
S1 = [r for r in ROWS if r['stage1_flag'] == 'True']
XA = [r for r in ROWS if r['crossing'] == 'True'
      and r['resolution_class'] == 'fine']
assert len(A) + len(B) == len(ROWS), (len(A), len(B), len(ROWS))

A_lo = [r for r in A if eta(r) < 1.0]
B_hi = [r for r in B if eta(r) >= 1.0]
S1_lo = [r for r in S1 if eta(r) < 1.0]
XA_lo = [r for r in XA if eta(r) < 1.0]

# ★ The class-wide claim the referee objects to must be FALSE, or there is
# nothing to correct and this generator is reporting a change that did not
# happen.
assert A_lo, 'no Class A window is below eta_drift = 1; the referee\'s ' \
             'objection would be void and the correction unnecessary'
# ★ The narrowed claim must be TRUE, or Appendix J.3 has to be deleted rather
# than narrowed and the prose below is wrong.
assert not S1_lo, S1_lo
assert not XA_lo, XA_lo
# ★ And the asymmetry must run both ways, or "the classes do not partition on
# eta_drift" is a one-sided statement dressed up as a symmetric one.
assert B_hi, 'no Class B window reaches eta_drift = 1'

m('EtaDriftNClassA', '%d' % len(A))
m('EtaDriftNClassB', '%d' % len(B))
m('EtaDriftALo', '%d' % len(A_lo))
m('EtaDriftALoPct', '%.1f' % (100.0 * len(A_lo) / len(A)))
m('EtaDriftBHi', '%d' % len(B_hi))
m('EtaDriftAMin', '%.2f' % min(map(eta, A)))
m('EtaDriftAMax', '%.0f' % max(map(eta, A)))
m('EtaDriftAMed', '%.1f' % st.median(list(map(eta, A))))
m('EtaDriftBMax', '%.2f' % max(map(eta, B)))
m('EtaDriftBMed', '%.2f' % st.median(list(map(eta, B))))
m('EtaDriftNStageOne', '%d' % len(S1))
m('EtaDriftStageOneMin', '%.1f' % min(map(eta, S1)))
m('EtaDriftStageOneMax', '%.0f' % max(map(eta, S1)))
m('EtaDriftStageOneMed', '%.0f' % st.median(list(map(eta, S1))))
m('EtaDriftNCrossA', '%d' % len(XA))
# Why the 13 are what they are: track length, not class boundary.
m('EtaDriftLoTrackMin', '%.0f' % min(float(r['on_source_s']) for r in A_lo))
m('EtaDriftLoTrackMax', '%.0f' % max(float(r['on_source_s']) for r in A_lo))
m('EtaDriftLoChanLo', '%.0f' % (min(float(r['chanw_Hz']) for r in A_lo) / 1e3))
m('EtaDriftLoChanHi', '%.0f' % (max(float(r['chanw_Hz']) for r in A_lo) / 1e3))
m('EtaDriftLoBlocks', '%d' % len({r['eb'] for r in A_lo}))
m('EtaDriftLoStars', '%d' % len({r['star_name'] for r in A_lo}))
# ★ The mechanism claim: the 13 sit at the TOP of the Class A channel-width
# range, not scattered through it.  If a 15 kHz window ever appears among
# them the explanation in the text is wrong.
_cw_all = sorted(float(r['chanw_Hz']) for r in A)
assert min(float(r['chanw_Hz']) for r in A_lo) >= _cw_all[-1] / 4, \
    'a low-eta_drift Class A window is not at the coarse end of the class'
# ★ ...and they are short tracks, against the class median.
_med_track = st.median([float(r['on_source_s']) for r in A])
m('EtaDriftTrackMedA', '%.0f' % _med_track)
assert max(float(r['on_source_s']) for r in A_lo) < _med_track, _med_track

with open(OUT, 'w') as fh:
    fh.write('%% GENERATED by etadrift_v405.py -- do not hand-edit.\n')
    for k in sorted(M):
        fh.write('\\newcommand{\\%s}{%s}\n' % (k, M[k]))

print('etadrift_v405 (round 94): Class A %d windows, eta_drift %.2f-%.0f '
      '(median %.1f), %d below 1 (%.1f per cent); Class B %d windows, %d at '
      'or above 1 (max %.2f)'
      % (len(A), min(map(eta, A)), max(map(eta, A)),
         st.median(list(map(eta, A))), len(A_lo), 100.0 * len(A_lo) / len(A),
         len(B), len(B_hi), max(map(eta, B))))
print('  stage-1 flagged windows: %d, eta_drift %.1f-%.0f (median %.0f), '
      '%d below 1; Class A threshold crossings: %d, %d below 1'
      % (len(S1), min(map(eta, S1)), max(map(eta, S1)),
         st.median(list(map(eta, S1))), len(S1_lo), len(XA), len(XA_lo)))
print('  the %d are %d blocks on %d stars, tracks %.0f-%.0f s (class median '
      '%.0f s) at %.0f-%.0f kHz'
      % (len(A_lo), len({r['eb'] for r in A_lo}),
         len({r['star_name'] for r in A_lo}),
         min(float(r['on_source_s']) for r in A_lo),
         max(float(r['on_source_s']) for r in A_lo), _med_track,
         min(float(r['chanw_Hz']) for r in A_lo) / 1e3,
         max(float(r['chanw_Hz']) for r in A_lo) / 1e3))
print('  -> %s (%d macros)' % (os.path.basename(OUT), len(M)))
