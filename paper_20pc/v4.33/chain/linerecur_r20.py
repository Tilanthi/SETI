#!/usr/bin/env python3
r"""round 920 -> survey_numbers_round920.tex: THE PREDICTED-CELL READING,
MEASURED ON REAL RECURRING LINES, AND WHAT EVERY INJECTED REALISATION WAS
INJECTED INTO (Referee 2 majors 2 and 3; Referee 1 issue 4).

TWO THINGS ARE ESTABLISHED HERE.

1. WHAT THE INJECTION CAMPAIGN WAS INJECTED INTO.  The manuscript says both
   that a carrier was injected into every covering repeat block of all 33
   crossings and that the per-integration repeat spectra survive for 2 of
   them.  The second statement is the false one.  Every block-role of the
   recurrence plan was stat'ed and read where the products live: 482 roles
   hold both `_srcspec.npz` and `_search.npz`, none is missing, each holds
   that block's own per-integration spectra, and the one role that does not
   survive is the DISCOVERY window of the single crossing that carries no
   exclusion for exactly that reason.  The campaign's own zero-amplitude
   realisations reproduce the published per-block readings to the last digit,
   which synthetic noise cannot do.  So the measurement is a measurement, and
   what needed correcting was two sentences of ours.

2. WHETHER THE PREDICTED CELL LANDS ON A REAL RECURRING SIGNAL.  The 33
   exclusions read ONE cell, reached through the barycentric correction, the
   systemic-velocity correction, the start-of-block anchor and the drift
   carried from the discovery fit.  The paper's positive control was a
   different quantity -- each repeat block's own window-maximum crossing --
   and the injections cannot close the gap, because an injected carrier is
   PLACED at the predicted cell and so assumes the computation under test.
   The frozen reading code was therefore run, unmodified, on the 13
   line-attributed crossings the criterion recovers and the 2 it does not,
   and the single-cell reading at the predicted cell is reported for every
   covering block, beside the channel that block's own search puts the line
   in.  A second run with the frame transform disabled -- the frozen path's
   own `--drive 6` -- says how much of the agreement the transform is
   responsible for.

Inputs (all tree-local):
  r20inputs/crossings_lines_r20.json     the 15 crossings, read from ledger.json
  r20inputs/plan_lines_r20.json          the frozen plan builder's own output
  r20inputs/recur_lines_r20.json.gz         the frozen reading, frozen plan
  r20inputs/recur_lines_ext_r20.json.gz     the frozen reading, one window supplied
  r20inputs/recur_lines_ext_d6_r20.json.gz  the same with the transform disabled
  r20inputs/index_lines_r20.json         each window's own search peak
  r20inputs/gt_probe_r20.json.gz          every block-role's products, stat'ed
  r20inputs/gt_content_r20.json.gz         every block-role's spectra, read
  r20inputs/hostnull_r19.jsonl           the campaign's zero-amplitude gate
  r19inputs/hostinj_r19.jsonl.gz         the campaign's realisation records
  r10inputs/recur_v411.json              the published readings and blocks
  r10inputs/badweight_v411.json          the flagged weight pathology

10 clauses (A0-A9), drives 1-9, each demonstrated to fail its own clause:
  python3 linerecur_r20.py --drive N
A drive writes `*_driveN.*` only and never a path production reads.
"""
import gzip
import json
import math
import os
import statistics
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
# ★ ROUND RENUMBERED 910 -> 920 BY THE INTEGRATOR: `r20-confirm` recorded a
# claim on 910-914 in ROUND_CLAIMS_R20.md at 07:55 and `confirm_r20.py` is
# in the tree on it; this generator and `vsyssweep_r20.py` (now 930) both
# claimed 910 in their own queue files, so three generators claimed one
# round in one round.  roundcollide resolves the filename from this
# constant, so the renumber is this line and the manuscript's \input.
ROUND = 920
DRIVE = int(sys.argv[sys.argv.index('--drive') + 1]) if '--drive' in sys.argv \
    else 0
SFX = '_drive%d' % DRIVE if '--drive' in sys.argv else ''
OUT = os.path.join(HERE, 'numbers/survey_numbers_round%d%s.tex' % (ROUND, SFX))
OUTJ = os.path.join(HERE, 'linerecur_r20%s.json' % SFX)

TRIG = 5.0                     # the trigger, as everywhere in this paper
BADEB = 'A002_Xc6b674_X28f5'   # the flagged weight pathology, dropped as the
#                                paper drops it
SUPPLIED = 'A002_Xd98580_X3bf6'

L, PROB = [], []


def m(name, val):
    assert name.isalpha(), 'a LaTeX macro name may contain letters only: %r' \
        % name
    assert not any(x.startswith('\\newcommand{\\%s}' % name) for x in L), \
        'macro defined twice: ' + name
    L.append('\\newcommand{\\%s}{%s}\n' % (name, val))


def ck(desc, cond, detail):
    print(('PASS  ' if cond else 'FAIL  ') + desc + '  [' + detail + ']')
    if not cond:
        PROB.append(desc)


def tname(display):
    out = display.replace('bet Pic', r'$\beta$~Pic')
    out = out.replace('HR 1010', 'HR~1010')
    out = out.replace('HD 285968', 'HD~285968')
    out = out.replace('ALMA J153702653-33192492',
                      r'ALMA~J153702653$-$33192492')
    return out.replace(' ', '~')


def jload(*parts):
    p = os.path.join(HERE, *parts)
    if p.endswith('.gz'):
        with gzip.open(p, 'rt') as fh:
            return json.load(fh)
    return json.load(open(p))


# =========================================================== the inputs
IN = 'r20inputs'
CROSS = jload(IN, 'crossings_lines_r20.json')
PLAN = jload(IN, 'plan_lines_r20.json')
RD = jload(IN, 'recur_lines_r20.json.gz')
RX = jload(IN, 'recur_lines_ext_r20.json.gz')
D6 = jload(IN, 'recur_lines_ext_d6_r20.json.gz')
IDX = {r['stem']: r for r in jload(IN, 'index_lines_r20.json')}
# ★ r28 (v4.29 fold, RR-lines): THE SUPPLIED WINDOW IS A SET THE PLAN DECLARES,
# NOT A CONSTANT.  r20 supplied X3bf6 spw3 by hand because the frozen
# identification refused its product (own peak 6.19 against the published
# 5.96).  In the re-flag fold the window's new product reproduces the
# catalogue (5.9862), the frozen plan identifies it, and nothing is supplied.
# Every flag below reads this set, so a block is marked 'supplied' only while
# the frozen plan actually refuses it.
SUPP_EBS = {p['eb'] for p in PLAN['plan']
            if p['eb'] == SUPPLIED and p['status'] != 'ok'}
GTP = jload(IN, 'gt_probe_r20.json.gz')
GTC = jload(IN, 'gt_content_r20.json.gz')
REC = jload('r10inputs', 'recur_v411.json')
PUB = REC['crossings']
NULL = [json.loads(x) for x in
        open(os.path.join(HERE, IN, 'hostnull_r19.jsonl')) if x.strip()]
RAW = []
with gzip.open(os.path.join(HERE, 'r19inputs', 'hostinj_r19.jsonl.gz'),
               'rt') as fh:
    for ln in fh:
        if ln.strip():
            RAW.append(json.loads(ln))

BYCID = {c['cid']: c for c in CROSS}
REC_CIDS = sorted(c['cid'] for c in CROSS if c['r20_verdict'] == 'recovered')
ABS_CIDS = sorted(c['cid'] for c in CROSS if c['r20_verdict'] == 'absent')
if DRIVE == 1:                 # A0: a positive control quietly dropped
    REC_CIDS = REC_CIDS[:-1]


def macro(name):
    """The manuscript's own value for a macro, read off the emitted files."""
    import glob
    import re
    pat = re.compile(r'\\newcommand\{\\%s\}\{(.*)\}\s*$' % name)
    for p in sorted(glob.glob(os.path.join(HERE, 'numbers/survey_numbers*.tex'))):
        if '_drive' in p:
            continue
        for line in open(p):
            mm = pat.match(line.strip())
            if mm:
                return mm.group(1)
    raise KeyError(name)


ck('A0 the crossings read out here are the manuscript\'s own positive '
   'controls -- every line-attributed crossing the criterion recovers, each '
   'naming the block that recovers it -- together with the two it does not',
   len(REC_CIDS) == int(macro('MkAttrRecur')) and len(ABS_CIDS) == 2
   and all(BYCID[c]['r20_recovered_eb'] for c in REC_CIDS)
   and all(BYCID[c]['line'] and BYCID[c]['attributed'] for c in BYCID),
   '%d recovered against the %s the manuscript counts, %d unrecovered'
   % (len(REC_CIDS), macro('MkAttrRecur'), len(ABS_CIDS)))

# =============================================== 1. THE CAMPAIGN'S OWN DATA
# the block-roles of the crossings that carry an exclusion
INJ_CIDS = sorted({r['cid'] for r in RAW})
ROLE_N, ROLE_MISS = 0, []
for p in GTP:
    for x in p['roles']:
        ROLE_N += 1
        if not (x['_srcspec.npz']['exists'] and x['_search.npz']['exists']):
            ROLE_MISS.append((p['cid'], x['role']))
if DRIVE == 2:                 # A2: a role with no retained spectra
    ROLE_MISS.append(('U01', 'repeat'))
NOSPEC = sorted(p['cid'] for p in GTP
                if p['status'] != 'ok' or not p['roles'])
CONT = {(c['cid'], c['role'], c['eb']): c for c in GTC}
NINT = sorted(c['nint'] for c in GTC)
# ★ r28 (v4.29 fold, RR): the parenthesis named round 10's U25 (discovery
# spectrum unsearched); in the fold that crossing is gone and the one unread
# crossing is a different one for a different reason (no other block covers
# it).  The clause is unchanged; its words now read the reason off the probe.
ck('A1 every block-role of the recurrence plan retains both products, and '
   'the only crossing the plan does not read is one that carries no '
   'exclusion because it has no reading of its own (its status names why: %s)'
   % ', '.join('%s %s' % (p['cid'], p['status']) for p in GTP
               if p['cid'] in NOSPEC),
   # v4.29 fold (stage-2 rehearsal): the unread crossing is a property of the population -- U25, then HIP 10679
   # (no repeat coverage), and on a later harvest HIP 10679 is ATTRIBUTED and none is unread.  Invariant: AT MOST one,
   # and an unread crossing never carries an exclusion; drive 2 (a role without spectra) still fires A1.
   not ROLE_MISS and len(NOSPEC) <= 1 and not (set(NOSPEC) & set(INJ_CIDS))
   and len(GTC) == ROLE_N,
   '%d roles, %d missing %s; no-spectrum crossings %s; %d read'
   % (ROLE_N, len(ROLE_MISS), ROLE_MISS or '', NOSPEC, len(GTC)))

# every realisation of the referee's own mode carried the full block list
MODES = sorted({r['mode'] for r in RAW})
PHASE_FULL, PHASE_SHORT = 0, []
CELL_SHORT, CELL_PAIRS, NCELL = 0, 0, 0
PERCID = {}
for cid in INJ_CIDS:
    nplan = len(PUB[cid]['blocks'])
    PERCID[cid] = dict(n_rep=nplan, n_phase=0, n_cell=0)
    for r in RAW:
        if r['cid'] != cid:
            continue
        if r['mode'] == 'phase':
            PERCID[cid]['n_phase'] += 1
            if r['n_blocks'] == nplan:
                PHASE_FULL += 1
            else:
                PHASE_SHORT.append((cid, r['idx'], r['n_blocks'], nplan))
        elif r['mode'] == 'cell':
            PERCID[cid]['n_cell'] += 1
            NCELL += 1
            if r['n_blocks'] < nplan:
                CELL_SHORT += 1
                CELL_PAIRS += nplan - r['n_blocks']
if DRIVE == 3:                 # A2: a realisation that missed a repeat block
    PHASE_SHORT.append(('U01', 0, 0, 3))
ck('A2 in the mode the referee specifies -- the crossing\'s own cell -- every '
   'realisation of every crossing that carries an exclusion was injected '
   'into the discovery block and into every covering repeat block',
   not PHASE_SHORT and PHASE_FULL > 0 and MODES == ['cell', 'phase'],
   '%d full-coverage realisations, %d short %s; modes %s'
   % (PHASE_FULL, len(PHASE_SHORT), PHASE_SHORT[:2] or '', MODES))

# the zero-amplitude gate: the real data read back unchanged
NULLB, NULLWORST = 0, 0.0
for r in NULL:
    assert r['mode'] == 'null' and r['amp_Jy'] == 0.0, r['idx']
    pub = {b['eb']: b for b in PUB[r['cid']]['blocks']}
    for b in r['blocks']:
        q = pub.get(b['eb'])
        if q is None:
            continue
        NULLB += 1
        NULLWORST = max(NULLWORST, abs(b['T_matched'] - q['T_matched']))
if DRIVE == 4:                 # A3: a sandbox that did not reproduce the data
    NULLWORST = 0.5
ck('A3 a zero-amplitude realisation reproduces the published reading of every '
   'block it covers exactly, which is what shows the carrier was added to the '
   'real retained spectra and not to a simulation of them',
   NULLB > 0 and NULLWORST == 0.0,
   '%d block readings over %d crossings, largest difference %.1e'
   % (NULLB, len({r['cid'] for r in NULL}), NULLWORST))

# ======================================== 2. THE READING ON REAL LINE SOURCES
def combine(blocks):
    bl = [b for b in blocks if b['eb'] != BADEB]
    w = [1.0 / b['sig_mJy'] ** 2 for b in bl]
    sbar = 1.0 / math.sqrt(sum(w))
    abar = sum(b['amp_mJy'] * x for b, x in zip(bl, w)) / sum(w)
    return abar / sbar, bl


def readout(R):
    out = {}
    for cid, c in R['crossings'].items():
        if c.get('status') != 'ok':
            continue
        T, bl = combine(c['blocks'])
        per = []
        for b in bl:
            ix = IDX.get(b['stem'], {})
            fpk = ix.get('star_peak_freq_GHz')
            dch = ((b['f_here_GHz'] - fpk) * 1e9 / b['chanw_Hz']
                   if fpk else None)
            dkms = ((b['f_here_GHz'] - fpk) / b['f_here_GHz'] * 299792.458
                    if fpk else None)
            per.append(dict(eb=b['eb'], T=b['T_matched'],
                            Tbd=b['T_bestdrift_pub'], chan=b['chan'],
                            dch=dch, dkms=dkms, chanw=b['chanw_Hz'],
                            peak_snr=ix.get('star_peak_snr'),
                            ctrl=b['ctrl_T_matched_max'],
                            supplied=bool(b['eb'] in SUPP_EBS),
                            sep_h=b['sep_from_discovery_h']))
        out[cid] = dict(cid=cid, star=c['star'], eb=c['eb'],
                        tstar=c['discovery']['T_matched'],
                        tstar_pub=c['discovery']['T_bestdrift_pub'],
                        gate_ok=c['discovery']['gate_ok'],
                        drift=c['discovery']['drift_Hz_s'],
                        T_rep=T, n_block=len(bl),
                        n_trig=sum(1 for p in per if p['T'] >= TRIG),
                        T_block_max=max(p['T'] for p in per), per=per)
    return out


A = readout(RX)
AF = readout(RD)
C6 = readout(D6)
if DRIVE == 5:                 # A4: a recovered line that does not read back
    A[REC_CIDS[0]]['T_rep'] = 1.0
    A[REC_CIDS[0]]['n_trig'] = 0

ck('A4 the frozen reading reproduces each line crossing\'s own published '
   'discovery statistic, so the chain under test is the published one',
   all(A[c]['gate_ok'] for c in A) and len(A) == len(CROSS),
   '%d of %d crossings read, %d reproduce their own discovery statistic'
   % (len(A), len(CROSS), sum(1 for c in A if A[c]['gate_ok'])))

NREC_TRIG = sum(1 for c in REC_CIDS if A[c]['T_rep'] >= TRIG)
NREC_BLOCK = sum(1 for c in REC_CIDS if A[c]['n_trig'] >= 1)
NABS_TRIG = sum(1 for c in ABS_CIDS if A[c]['T_rep'] >= TRIG)
ck('A5 the single-cell reading at the predicted cell reaches the trigger for '
   'every line crossing the criterion recovers, and for neither of the two '
   'it does not',
   NREC_TRIG == len(REC_CIDS) and NABS_TRIG == 0,
   '%d of %d recovered reach it (%d in at least one block), %d of %d '
   'unrecovered'
   % (NREC_TRIG, len(REC_CIDS), NREC_BLOCK, NABS_TRIG, len(ABS_CIDS)))

# the registration, against each block's own search peak
DCH = [abs(p['dch']) for c in REC_CIDS for p in A[c]['per']
       if p['dch'] is not None and p['T'] >= TRIG]
DKMS = [abs(p['dkms']) for c in REC_CIDS for p in A[c]['per']
        if p['dkms'] is not None and p['T'] >= TRIG]
# what the transform itself moves, so the agreement cannot be an identity
SHIFT = []
for c in A:
    for p in A[c]['per']:
        q = [x for x in C6.get(c, {}).get('per', []) if x['eb'] == p['eb']]
        if q:
            SHIFT.append(abs(p['chan'] - q[0]['chan']))
if DRIVE == 6:                 # A6: the agreement measured against itself
    DCH = [0.0 for _ in DCH]
    SHIFT = [0 for _ in SHIFT]
ck('A6 the predicted cell agrees with the channel each block\'s own search '
   'puts the line in, and the agreement is not an identity: the frame '
   'transform displaces that cell by far more than the residual',
   DCH and statistics.median(DCH) < 1.0
   and statistics.median(SHIFT) > 4 * statistics.median(DCH),
   'median |pred-obs| %.2f ch (max %.2f), median transform displacement '
   '%.0f ch (max %d)'
   % (statistics.median(DCH), max(DCH), statistics.median(SHIFT),
      max(SHIFT)))

NC6_TRIG = sum(1 for c in REC_CIDS if C6[c]['T_rep'] >= TRIG)
NB_TRIG = sum(A[c]['n_trig'] for c in REC_CIDS)
NB_TOT = sum(A[c]['n_block'] for c in REC_CIDS)
NB6_TRIG = sum(C6[c]['n_trig'] for c in REC_CIDS)
if DRIVE == 7:                 # A7: a control that is not worse
    NC6_TRIG, NB6_TRIG = len(REC_CIDS), NB_TRIG
ck('A7 with the frame transform disabled the same readings lose the line, so '
   'the recovery is the transform\'s and not the window\'s',
   NC6_TRIG < NREC_TRIG and NB6_TRIG < NB_TRIG,
   'with the chain %d of %d crossings and %d of %d block readings; without '
   'it %d and %d' % (NREC_TRIG, len(REC_CIDS), NB_TRIG, NB_TOT, NC6_TRIG,
                     NB6_TRIG))

# the scope: what this validates and what it does not
DR_LINE = sorted(abs(A[c]['drift']) for c in A)
DR_EXCL = sorted(abs(PUB[c]['discovery']['drift_Hz_s']) for c in PUB
                 if PUB[c].get('status') == 'ok'
                 and PUB[c]['discovery'].get('drift_Hz_s') is not None)
FR_LINE = sorted(abs(r['dchan_from_sky']) for r in RX['rows']
                 if r.get('status') == 'ok')
FR_EXCL = sorted(abs(r['dchan_from_sky']) for r in REC['rows']
                 if r.get('status') == 'ok')
if DRIVE == 8:                 # A8: a scope statement that is not true
    FR_LINE = [0.0]
# ★ GEN (v4.29 fold, coordinator D8): A8 RETIRED, not inverted.  It guarded a scope SENTENCE ("the real-source
#   test carries frame displacements at least as large as the exclusions do") that the r28 text phase cut: no \Lr*
#   macro and no such sentence remains in sections/ (checked).  On the fold population the comparison runs the
#   other way (6.94 ch here against 7.91 for the exclusions), so the sentence must not come back without a guard.
#   Both medians are still computed and printed below (and drive 8 still perturbs them), so a reader of this log
#   sees the measurement; the clause is reported, not asserted.
print('  A8 RETIRED (its sentence was cut): frame displacement median %.2f ch here against %.2f; carried drift '
      'median %.0f Hz/s here against %.0f'
      % (statistics.median(FR_LINE), statistics.median(FR_EXCL),
         statistics.median(DR_LINE), statistics.median(DR_EXCL)))

# the one window the frozen identification refuses
SUPP = [p for p in PLAN['plan']
        if p['eb'] == SUPPLIED and p['status'] != 'ok']
NFROZEN = len(AF)
# ★ r28 (RR-lines): was "exactly ONE supplied, and the frozen plan reads one
# fewer" -- true of the Oct-15 products, false once X3bf6's re-flag product
# reproduces the catalogue.  The invariant: the crossings the supplied
# reading adds to the frozen one are EXACTLY the declared supplied ones (none
# undeclared, none declared and missing), and there is at most the one.
_ADDED = sorted(set(A) - set(AF))
if DRIVE == 9:                 # A9: a supplied window not declared
    _ADDED = sorted(set(_ADDED) | {sorted(A)[0]})
ck('A9 every crossing the supplied reading adds to the frozen plan is a '
   'declared supplied window and every declared one is read, so the frozen '
   'plan alone reads out exactly as many crossings fewer as were supplied',
   _ADDED == sorted(p['cid'] for p in SUPP) and len(SUPP) <= 1
   and NFROZEN == len(A) - len(SUPP),
   '%d supplied (%s), frozen plan reads %d of %d; added by the supply %s'
   % (len(SUPP), ', '.join(p['eb'] for p in SUPP) or 'none',
      NFROZEN, len(A), _ADDED or 'none'))

# ============================================================ the macros
m('LrNCtl', '%d' % len(REC_CIDS))
m('LrNAbs', '%d' % len(ABS_CIDS))
# the one window supplied outside the frozen identification
# ★ r28 (RR-lines): published only while a window IS supplied (no section
# cites them; num_r22 B11 reads \LrSuppPct -- see RR.md L).
_sp = [p for p in PLAN['plan'] if p['eb'] in SUPP_EBS]
if _sp:
    _spd = _sp[0].get('diagnostic') or {}
    _sppub = float(_spd.get('published_tstar'))
    _spown = float((_spd.get('copies') or [[None, None]])[0][1])
    m('LrSuppPub', '%.4f' % _sppub)
    m('LrSuppOwn', '%.4f' % _spown)
    m('LrSuppPct', '%.1f' % (100.0 * (_spown / _sppub - 1.0)))
m('LrTrepLo', '%.1f' % min(A[c]['T_rep'] for c in REC_CIDS))
m('LrTrepHi', '%.1f' % max(A[c]['T_rep'] for c in REC_CIDS))
# ★ `minuscheck`: a negative value is emitted with a real minus at the EMIT
# step, or it typesets as a hyphen wherever the prose prints it.
def signed(x, fmt='%.2f'):
    return (r'\ensuremath{-}' + fmt % abs(x)) if x < 0 else fmt % x


m('LrAbsLo', signed(min(A[c]['T_rep'] for c in ABS_CIDS)))
m('LrAbsHi', signed(max(A[c]['T_rep'] for c in ABS_CIDS)))
m('LrDchMed', '%.2f' % statistics.median(DCH))
m('LrNoFrameCtl', '%d' % NC6_TRIG)
m('LrDriftMedLine', '%.0f' % statistics.median(DR_LINE))
m('LrDriftMedExcl', '%.0f' % statistics.median(DR_EXCL))
# ★ EVERY MACRO HERE IS PRINTED.  The quantities the prose does not print --
# the per-block readings, the velocity equivalents of the registration, the
# transform's own displacement, the no-transform block count, the longest
# baseline, the frame displacements of both populations -- are in
# `linerecur_r20.json`, which is deposited, rather than emitted as macros no
# `.tex` file references.
# item 1: the provenance of every realisation
m('GpNRole', '%d' % ROLE_N)
m('GpNRoleInj', '%d' % sum(1 + PERCID[c]['n_rep'] for c in INJ_CIDS))
m('GpNIntLo', '%d' % NINT[0])
m('GpNIntHi', '%d' % NINT[-1])
m('GpNullBlock', '%d' % NULLB)
m('GpNullStar', '%d' % len({r['cid'] for r in NULL}))


print('\n%-5s %-26s %-9s %7s %7s %8s %6s %8s %8s'
      % ('cid', 'star', 'verdict', 'T*', 'T_rep', 'blocks', '>=5',
         'dch_med', 'T_noframe'))
for cid in sorted(A):
    v = BYCID[cid]['r20_verdict']
    dd = [abs(p['dch']) for p in A[cid]['per'] if p['dch'] is not None]
    print('%-5s %-26s %-9s %7.3f %7.3f %8d %6d %8.2f %8.3f'
          % (cid, A[cid]['star'][:26], v, A[cid]['tstar'], A[cid]['T_rep'],
             A[cid]['n_block'], A[cid]['n_trig'],
             statistics.median(dd) if dd else float('nan'),
             C6[cid]['T_rep']))

assert not PROB, 'linerecur_r20: %d clause(s) FAILED: %s' % (len(PROB), PROB)
with open(OUT, 'w') as fh:
    fh.write('%% GENERATED by linerecur_r20.py (round %d) -- do not '
             'hand-edit.\n' % ROUND)
    fh.write('%% The predicted-cell reading measured on real recurring lines, '
             'and what each injected realisation was injected into.\n')
    fh.writelines(sorted(L))

# the table payload: one record per (crossing, named recovering block) for
# Table D2, and one per crossing for Table B1's provenance column
D2 = {}
for cid in sorted(A):
    named = BYCID[cid]['r20_recovered_eb']
    nm = [p for p in A[cid]['per'] if p['eb'] == named]
    D2['%s|%.6f' % (A[cid]['eb'], BYCID[cid]['freq_GHz'])] = dict(
        cid=cid, star=A[cid]['star'], eb=A[cid]['eb'],
        freq_GHz=BYCID[cid]['freq_GHz'], verdict=BYCID[cid]['r20_verdict'],
        recovering_eb=named,
        T_rep=nm[0]['T'] if nm else None,
        dchan=nm[0]['dch'] if nm else None,
        dkms=nm[0]['dkms'] if nm else None,
        chanw_Hz=nm[0]['chanw'] if nm else None,
        supplied=bool(named in SUPP_EBS or A[cid]['eb'] in SUPP_EBS),
        supplied_disc=bool(A[cid]['eb'] in SUPP_EBS),
        T_rep_combined=A[cid]['T_rep'], n_block=A[cid]['n_block'],
        n_block_trig=A[cid]['n_trig'])
B1 = {c: dict(n_rep=PERCID[c]['n_rep'], injected_into='real_perint_spectra',
              n_cell=PERCID[c]['n_cell'], n_phase=PERCID[c]['n_phase'])
      for c in INJ_CIDS}
json.dump(dict(generator=os.path.basename(__file__), round=ROUND, drive=DRIVE,
               frozen_sha=sorted({r['frozen_sha'] for r in RAW}),
               reading_code=RX['generator'], trigger=TRIG,
               table_d2=D2, table_b1=B1,
               crossings={c: {k: v for k, v in A[c].items() if k != 'per'}
                          for c in sorted(A)},
               per_block={c: A[c]['per'] for c in sorted(A)},
               no_frame={c: C6[c]['T_rep'] for c in sorted(C6)},
               roles=ROLE_N, roles_with_spectra=ROLE_N - len(ROLE_MISS),
               null_blocks=NULLB, null_worst=NULLWORST),
          open(OUTJ, 'w'), indent=1, default=float)
print('\nwrote %s (%d macros) and %s'
      % (os.path.basename(OUT), len(L), os.path.basename(OUTJ)))
