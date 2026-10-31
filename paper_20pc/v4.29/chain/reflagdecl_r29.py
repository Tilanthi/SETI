#!/usr/bin/env python3
r"""reflagdecl_r29.py -- what is true of the calibration after the v4.29 re-calibration, as macros (round 2900).

Replaces flagdecl_r27.py (round 1290), whose statement -- "ALMA's pipeline and online flags were not applied
... the flux-scaling step was not run" -- described v4.28 (a checkpoint, Ruling 31) and is false for every
block re-calibrated since.  Reads:
  r29inputs/reflag/reflag_decl_r29.json   frozen (fold bundle's build_decl.py): every core block's fate --
                                          re-calibrated (and how), Pipeline_Final unrestorable, infeasible on
                                          our disks (measured or estimated peak), pending -- plus the
                                          measured bound on the chance expectation and the size of the
                                          extractor-version difference where flags did not change;
  r29inputs/reflag/reflag_census_r29.json the census fold's entries (what reflagfold_r29.py applied);
  reflagfold_r29_audit.json               what it did in THIS build (mode, counts, q check);
  \CeExp                                  from the macro layer (chance_v414.py), so it MUST FOLLOW that.
Emits survey_numbers_round2900.tex.  Facts are asserted, never words.
  R1 the fold applied every entry exactly once (statistic replaced or, under REFLAG_CODEVERSION=declare,
     kept for a code-version window) and scaled every entry's limit;
  R2 under REFLAG_LIMITREF=r33 the scaled S_min equals the new product's to 1e-9 (q is the new product);
  R3 the core blocks' fates partition the core list (every block has exactly one fate);
  R4 every census entry belongs to a block the record calls re-calibrated;
  R5 with REFLAG_FINAL=1, no core block is pending or unaccounted for;
  R6 the chance-bound interval contains its point estimate, and the bounded expectation contains \CeExp;
  R7 no q drive (REFLAG_QDRIVE) is active outside the declared drive sandbox;
  R8 every core block is re-calibrated or declared, and the two counts close on the core list.
  R9 the extractor-version sample (E8: lane A3's random draw) lies off the re-calibration list.
--drive N perturbs one input in memory and writes survey_numbers_round2900_driveN.tex only.
"""
import json
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROUND = 2900
DRIVE = int(sys.argv[sys.argv.index('--drive') + 1]) if '--drive' in sys.argv else None
SFX = '' if DRIVE is None else '_drive%d' % DRIVE
J = lambda p: json.load(open(os.path.join(HERE, p)))  # noqa: E731
D = J('r29inputs/reflag/reflag_decl_r29.json')
E = J('r29inputs/reflag/reflag_census_r29.json')
AUD = J('reflagfold_r29_audit.json')
FINAL = os.environ.get('REFLAG_FINAL', '0') == '1'


def texval(name):
    pat = re.compile(r'\\newcommand\{\\%s\}\{([^}]*)\}' % name)
    vals = []
    for f in sorted(os.listdir(os.path.join(HERE, 'numbers'))):
        if f.startswith('survey_numbers') and f.endswith('.tex') and '_drive' not in f:
            vals += pat.findall(open(os.path.join(HERE, 'numbers', f), errors='ignore').read())
    assert len(vals) == 1, ('macro %s defined %d times' % (name, len(vals)))
    return vals[0]


B = D['blocks']
core = [b for b in B if b['tier'] == '1-core']
if DRIVE == 1:      # an entry the fold did not apply
    AUD['statistic_replaced'] -= 1
if DRIVE == 2:      # the scaled limit is not the new product's
    AUD['q_vs_record_max_reldev'] = 1e-3
if DRIVE == 3:      # a core block with two fates
    core = core + [dict(core[0], fate='pending')]
if DRIVE == 4:      # a census entry from a block not re-calibrated
    E['entries'][0] = dict(E['entries'][0], ship=dict(E['entries'][0]['ship'], eb='A002_Xdrive_X1'))
if DRIVE == 5:
    FINAL = True
    core = core + [dict(core[0], eb='A002_Xdrive_X2', fate='pending')]
fail = []


def ck(name, ok, detail=''):
    print('  %-66s %s  %s' % (name, 'PASS' if ok else 'FAIL', detail))
    if not ok:
        fail.append(name)


mode = AUD['mode']
n = AUD['entries']
ck('R1 the fold applied every census entry exactly once and scaled every limit',
   n == len(E['entries']) and AUD['statistic_replaced'] + AUD['codeversion_kept'] == n
   and AUD['limit_scaled'] == n,
   '%d entries, %d replaced, %d kept (codeversion), %d limits scaled, mode %s'
   % (n, AUD['statistic_replaced'], AUD['codeversion_kept'], AUD['limit_scaled'], mode))
qd = AUD['q_vs_record_max_reldev']
ck('R2 under r33 the scaled S_min is the new product\'s (q is the new product)',
   mode['REFLAG_LIMITREF'] != 'r33' or E.get('side') != 'new' or (qd is not None and qd < 1e-9),
   'max |S*q/S_new - 1| = %s' % qd)
ebs = [b['eb'] for b in core]
FATES = ('recalibrated', 'pf_unrestorable', 'infeasible_measured', 'infeasible_estimated', 'pending',
         'not_attempted', 'not_reached')   # not_reached: the harvest was frozen before its recalibration finished
ck('R3 the core blocks\' fates partition the core list',
   len(ebs) == len(set(ebs)) and all(b['fate'] in FATES for b in core),
   '%d core blocks, %d distinct' % (len(ebs), len(set(ebs))))
rec = {b['eb'] for b in B if b['fate'] == 'recalibrated'}
orphan = sorted({e['ship']['eb'] for e in E['entries']} - rec)
ck('R4 every census entry belongs to a re-calibrated block', not orphan or E.get('side') != 'new',
   '%d orphan block(s) %s' % (len(orphan), orphan[:3]))
pend = [b for b in core if b['fate'] in ('pending', 'not_attempted')]
nreach = [b for b in core if b['fate'] == 'not_reached']
ck('R5 final build: no core block pending or unaccounted for', not FINAL or not pend,
   'REFLAG_FINAL=%d, %d pending/unaccounted' % (FINAL, len(pend)))
ck('R7 no q drive is active (REFLAG_QDRIVE is for the declared drive sandbox only)',
   not AUD.get('qdrive') or os.environ.get('REFLAG_QDRIVE_ALLOWED') == '1',
   'qdrive %s' % AUD.get('qdrive'))
cb = D['chance_bound']['all']
ce = float(texval('CeExp'))
ce_lo, ce_hi = ce * cb['lo'], ce * cb['hi']
ck('R6 the chance-bound interval contains its estimate and the bounded expectation contains CeExp',
   cb['lo'] <= cb['ratio'] <= cb['hi'] and ce_lo <= ce <= ce_hi,
   'ratio %.4f (%.4f-%.4f) -> %.2f-%.2f around %.1f' % (cb['ratio'], cb['lo'], cb['hi'], ce_lo, ce_hi, ce))

W = ('no', 'one', 'two', 'three', 'four', 'five', 'six', 'seven', 'eight', 'nine', 'ten', 'eleven', 'twelve')
word = lambda k: W[k] if k < len(W) else '%d' % k  # noqa: E731
Word = lambda k: word(k)[0].upper() + word(k)[1:]  # noqa: E731
recb = [b for b in B if b['fate'] == 'recalibrated']
notc = [b for b in core if b['fate'] != 'recalibrated']
infe = [b for b in notc if b['fate'] in ('infeasible_measured', 'infeasible_estimated')]
unr = [b for b in notc if b['fate'] == 'pf_unrestorable']
cv = D['codeversion']
A_ent = sum(1 for e in E['entries'] if e['cls'] == 'A')
recb_all = recb
recb = [b for b in recb_all if b['tier'] == '1-core']        # the statement is about the CORE blocks
by = lambda c: sum(1 for b in recb if b['how'] == c)  # noqa: E731
ck('R8 the core blocks are either re-calibrated or declared, and the counts close',
   len(recb) + len(notc) == len(core), '%d + %d = %d' % (len(recb), len(notc), len(core)))
# E8 (FOLD_DECISIONS 2026-10-29; Ruling R21): how different are the census windows NOT re-run?  Read from the
# random sample (lane A3: 10 census blocks off the target list, re-run with the deposited extractor and NO
# flags, so the code version is the only difference) -- not from the flags-unchanged re-run blocks above,
# which are selected (they include GL 3379 because it moved) and stay in the deposit only.
XS = J('r29inputs/reflag/extractor_sample_r29.json')
xr = XS['rows']
if DRIVE == 6:      # a sample window from a block on the target list (the sample must be off it)
    xr = xr + [dict(xr[0], eb=sorted(rec)[0])]
xd = sorted(abs(r['T_new'] - r['T_old']) for r in xr)
xblk = sorted({r['eb'] for r in xr})
ck('R9 the extractor-version sample is off the re-calibration list and is the frozen draw',
   not (set(xblk) & {b['eb'] for b in B}) and len(xblk) == XS['selection']['n_blocks'],
   '%d blocks, %d windows, %d on the list' % (len(xblk), len(xr), len(set(xblk) & {b['eb'] for b in B})))
x_rms = max(abs(r['rms_ratio'] - 1.0) for r in xr)
X_BIG = 0.1          # the threshold the sentence states (\RflXvBigTh)
x_big = sum(1 for d in xd if d >= X_BIG)
def _join(parts):
    return (parts[0] if len(parts) == 1 else ', '.join(parts[:-1]) + ' and ' + parts[-1]) if parts else ''


assert len(notc) == len(infe) + len(unr) + len(nreach) + len(pend), (
    'R8b the declared reasons do not partition the blocks that keep the delivered calibration')
M = {'RflNEb': '%d' % len(recb_all),
     'RflNEbCore': '%d' % len(recb),
     'RflNEbCoreAll': '%d' % len(core),
     'RflNEbExtra': '%d' % (len(recb_all) - len(recb)),
     'RflNEbPf': '%d' % by('pipeline_final'),
     'RflNEbInline': '%d' % by('replay_inline_no_pf'),
     'RflNEbInlineWord': word(by('replay_inline_no_pf')),
     'RflNEbRecon': '%d' % by('reconstructed_no_pf'),
     'RflNEbReconWord': word(by('reconstructed_no_pf')),
     'RflNEbLegacy': '%d' % (by('legacy_flux') + by('legacy_noflux')),
     'RflNEbLegacyWord': word(by('legacy_flux') + by('legacy_noflux')),
     'RflNEbLegacyFlux': '%d' % by('legacy_flux'),
     'RflNWinCensus': '%d' % len(E['entries']),
     'RflNWinCensusA': '%d' % A_ent,
     'RflNEbNot': '%d' % len(notc),
     'RflNEbNotWord': Word(len(notc)),
     'RflNEbInfeas': '%d' % len(infe),
     'RflNEbUnres': '%d' % len(unr),
     'RflNEbUnresWord': word(len(unr)),
     'RflNEbPending': '%d' % len(pend),
     'RflPendingClause': ('' if not pend else
                          ', and %s are still being recalibrated' % word(len(pend)))
                         + ('' if not nreach else
                            ', and in %s the recalibration did not finish in the time available' % word(len(nreach))),
     'RflNEbNotReached': '%d' % len(nreach),
     # the reasons the other blocks keep the delivered calibration, GENERATED: a reason with no block is omitted
     # (on the final harvest no block is Pipeline_Final-unrestorable any more -- CASA 5.1.1 restored them all -- and
     # "in no the final flags do not fit" would typeset; coordinator: the count is generated, never a typed word)
     'RflNotClause': _join([p for p in (
         ('%d exceed the disk space available' % len(infe)) if infe else '',
         ('in %s the final flags do not fit the imported data' % word(len(unr))) if unr else '',
         ('in %s the recalibration did not finish in the time available' % word(len(nreach))) if nreach else '',
         ('%s are still being recalibrated' % word(len(pend))) if pend else '') if p]),
     'RflNNotLim': '%d' % sum(1 for b in notc if b['carries_limit']),
     'RflNNotCross': '%d' % sum(1 for b in notc if b['carries_crossing']),
     'RflChRatio': '%.3f' % cb['ratio'],
     'RflChLo': '%.3f' % cb['lo'],
     'RflChHi': '%.3f' % cb['hi'],
     'RflChNWin': '%d' % cb['n_windows'],
     'RflChNBlk': '%d' % cb['n_blocks'],
     'RflCeLo': '%.1f' % ce_lo,
     'RflCeHi': '%.1f' % ce_hi,
     'RflCvNBlk': '%d' % cv['n_blocks'],
     'RflCvNBlkWord': word(cv['n_blocks']),
     'RflCvNWin': '%d' % cv['n_windows'],
     'RflCvMedDT': '%.2f' % cv['median_abs_dT'],
     'RflCvMaxDT': '%.1f' % cv['max_abs_dT'],
     'RflXvNBlk': '%d' % len(xblk),
     'RflXvNBlkWord': word(len(xblk)),
     'RflXvNWin': '%d' % len(xr),
     'RflXvMedDT': '%.2f' % __import__('statistics').median(xd),
     'RflXvMaxDT': '%.2f' % xd[-1],
     'RflXvBigTh': '%g' % X_BIG,
     'RflXvMaxGb': '%.1f' % XS['selection']['max_asdm_gb'],
     'RflXvNBig': '%d' % x_big,
     'RflXvNBigWord': word(x_big),
     'RflXvRmsPct': '%.1f' % max(0.1, 100.0 * x_rms) if x_rms < 0.01 else '%.0f' % (100.0 * x_rms)}
for k in M:
    assert k.isalpha(), k
out = ['%% GENERATED by reflagdecl_r29.py (round %d) -- do not hand-edit.' % ROUND]
out += ['\\newcommand{\\%s}{%s}' % kv for kv in sorted(M.items())]
open(os.path.join(HERE, 'numbers/survey_numbers_round%d%s.tex' % (ROUND, SFX)), 'w').write('\n'.join(out) + '\n')
print('reflagdecl_r29 [%s]: %d macros, %d assertion(s) failed %s' % (mode, len(M), len(fail), fail))
sys.exit(1 if fail else 0)
