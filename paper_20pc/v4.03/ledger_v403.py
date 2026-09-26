#!/usr/bin/env python3
"""The principal crossing ledger for v4.03: every threshold crossing, what the
chain of DECISIONS_R7 A3 says about it, and what the drift-following
visibility fit says alongside -- under BOTH epoch conventions.

This replaces `ledger_v401.py`, which is superseded for three reasons, all of
them findings rather than typos:

  1. It carried one epoch convention.  The convention is wrong: on 1,833
     injected unresolved carriers, above 2.8 channels of displacement
     `t0 = times[0]` recovers 0.293 of the injected flux and localises 76.0 %
     while `median(TIME)` recovers -0.012 and localises 0 of 167
     (referee_r7/EPOCH_DECIDED.md).  DECISIONS_R7 A1 adopts `times[0]` and
     requires BOTH be reported, because the difference between them is one of
     the findings.  Both are here, with the channel displacement D that drives
     the difference.
  2. It presented the visibility fit as a filter.  Under the corrected epoch,
     of the 44 crossings reaching Re/sigma >= 4, clauses 2 and 3 reject 4 --
     every one of them BD+05 1668, a single grossly displaced source with
     |Im/sigma| of 21-41, and 1 of 39 among the epoch-verified fits.  They
     reject nothing except that one source, and the control clause never
     rejects alone (`clause3-never-rejects-alone`).  REFIT_R7 S6's and
     DECISIONS_R7 A2's first wording, "reject nothing", is measurably too
     clean and is not what this generator computes.
     DECISIONS_R7 A2 makes the fit a position-and-epoch
     consistency check.  The chain that decides anything is
     crossing -> stellar-frame attribution -> rank screen -> recurrence, and
     the `chain` column follows it.  Nothing here is called a candidate.
  3. Its line-attribution guard could not fail.  `if not r['line']` is false
     for all 56 crossings -- every crossing has a nearest catalogued
     transition, one of them 20,255 km/s away -- so the count of unattributed
     localised crossings was zero by construction.  Every check below carries
     a one-line note naming an input that would make it fail, and
     `selftest_v403.py` demonstrates each one failing on a perturbed input.

Folding in the outstanding fits is a re-run, not an edit: the new-fit inputs
are a glob (`visfit_r7*_result.json`, later names superseding earlier ones),
untested rows are derived from the absence of a fit, and no count anywhere in
this file is a literal except the criterion thresholds and the pre-committed
ceilings, which must not be recomputed from the data they are applied to.

Usage:  python3 ledger_v403.py [--outdir DIR]
Env:    LEDGER_V403_INPUTS   extra input directory, searched first
        LEDGER_V403_FITS     explicit os.pathsep-separated new-fit files
        LEDGER_V403_PERTURB  selftest only; see PERTURBATIONS below

Writes, into --outdir (default: this directory):
    tab_ledger_v403.tex        the principal table, all 56 crossings
    tab_ledgersum_v403.tex     summary counts, observed against chance
    survey_numbers_round80.tex the macros
    ledger_v403.json           machine-readable ledger + summary
    ledger_v403.csv            the same, one row per crossing, for release
"""
import argparse
import csv
import importlib.util
import json
import math
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))

# ---------------------------------------------------------------------------
# The committed criterion.  LITERALS.  They must not be recomputed from the
# data they are applied to; that is the whole reason the round-6 campaign's
# result could be believed.  Provenance: referee_r6/LOCALISATION_CRITERION.md,
# written 2026-09-25T06:59:24Z, committed edfcc0d3d7db, BEFORE any fit ran.
RE_MIN = 4.0
IM_MAX = 3.0
MASK_KMS = 50.0                      # the survey's frozen line mask half-width
CRITERION_COMMIT = 'edfcc0d3d7db'
CRITERION_TIME = '2026-09-25T06:59:24Z'
# The false-alarm ceiling fixed before round 6: the full criterion must fire on
# under 1 % of event-free control samples.  Also a literal, also pre-committed.
FA_CEILING = 0.01
# Below this displacement the two epoch conventions are the same experiment.
# Set from the injection campaign's own resolution (EPOCH_DECIDED.md: the
# conventions agree below ~0.25 channels), not from these fits.
D_SAME_CH = 0.25
# The blocks whose windows are still losing the free-space gate on the host
# (REFIT_R7 S1).  A literal so that an untested crossing arising for any OTHER
# reason stops the build instead of being absorbed silently.
OUTSTANDING_EBS = {
    'A002_Xa7a216_X23e4',      # bet Pic B6, 1 window
    'A002_Xd9668b_Xa9df',      # bet Pic B6, 2 windows
    'A002_Xd9668b_X3a90',      # bet Pic B6, 2 windows
    'A002_Xff0235_X4a6d',      # CP-72 2713, 1 window
}

# ★ Of the unattributed crossings the rank screen flags, this many have no
# recurrence or second-epoch evidence at all.  It was 1 (61 Vir) until
# 2026-09-26, when the M10 harness measured both; it is now 0 and the
# terminal sentence in S5.2.3 was rewritten with it.  A LITERAL, so that
# closing the gap -- or opening a new one -- stops the build and forces the
# sentence to be rewritten deliberately rather than the count sliding.
N_RECUR_GAP_EXPECTED = 0

CHECKS = []          # (name, note naming an input that would make it fail)


def check(cond, name, note, detail=''):
    """One assertion, with the input that would make it fail recorded beside
    it.  A check whose note cannot be written is a check that cannot fail."""
    CHECKS.append((name, note))
    if not cond:
        raise AssertionError('CHECK FAILED [%s]: %s%s'
                             % (name, note, ('\n  ' + detail) if detail else ''))


# ---------------------------------------------------------------------------
# selftest hooks.  Every perturbation corrupts an INPUT, never a threshold.
PERTURBATIONS = {
    '': 'none',
    'mask-all-inside': 'every crossing dragged inside the +-50 km/s mask',
    'mask-all-outside': 'every crossing dragged outside the mask',
    'attr-by-presence': 'mask made equivalent to "has a nearest transition"',
    'orphan-fit': 'a fit relabelled to a block the catalogue does not carry',
    'flip-small-D': 'a verdict flipped where the two epochs are the same fit',
    'fa-inflate': 'control samples inflated past the 1 % ceiling',
    'etacrv-screened': 'eta Crv relabelled as passing the rank screen',
    'untracked-untested': 'a fit dropped from a block not recorded outstanding',
    'criterion-mismatch': 'the scorer\'s recorded threshold moved off 4.0',
    'scorer-mismatch': 'one fitted Re/sigma altered after the scorer ran',
    'drop-mask-macro': 'the mask-occupancy macro removed from its generator',
    'mask-null-far': 'every unattributed crossing loses its offset value',
    'attr-thin': 'all but two attributions pushed outside the mask',
    'kill-localisations': 'every adopted-epoch localisation removed',
    'recurrence-name': 'a recurrence block reassigned to another star',
    'recurrence-unjoined': 'a recurrence result pointing at no crossing',
    'strip-bound': 'an unverifiable epoch left with no bound on its residual',
    'strip-first': 'a result file written without its times[0] evaluation',
    'drop-crossing': 'one threshold crossing removed from the catalogue',
    'candidate-word': 'the disposition vocabulary loosened to say candidate',
    'recurrence-drop': 'a rank-flagged unattributed crossing losing its recurrence test',
}
PERTURB = os.environ.get('LEDGER_V403_PERTURB', '')
if PERTURB not in PERTURBATIONS:
    sys.exit('unknown LEDGER_V403_PERTURB %r; known: %s'
             % (PERTURB, ', '.join(sorted(k for k in PERTURBATIONS if k))))


# ---------------------------------------------------------------------------
def _dirs():
    d = []
    if os.environ.get('LEDGER_V403_INPUTS'):
        d.append(os.environ['LEDGER_V403_INPUTS'])
    d.append(HERE)                       # where they sit inside a paper version
    d.append(os.path.join(HERE, 'inputs'))   # where they sit in the scratch area
    return [x for x in d if os.path.isdir(x)]


def find(name):
    for d in _dirs():
        p = os.path.join(d, name)
        if os.path.exists(p):
            return p
    raise SystemExit('input not found on %s: %s' % (_dirs(), name))


def newfit_files():
    """Every round-7-generation result file, earlier names first.  The six
    windows still on the host land as an additional file (or as a rewritten
    one); either way folding them in is re-running this script."""
    if os.environ.get('LEDGER_V403_FITS'):
        return [p for p in os.environ['LEDGER_V403_FITS'].split(os.pathsep) if p]
    seen, out = set(), []
    for d in _dirs():
        for fn in sorted(os.listdir(d)):
            if re.fullmatch(r'visfit_r7[a-z0-9_]*_result\.json', fn) \
                    and fn not in seen:
                seen.add(fn)
                out.append(os.path.join(d, fn))
    return sorted(out, key=os.path.basename)


_spec = importlib.util.spec_from_file_location('star_alias', find('star_alias.py'))
star_alias = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(star_alias)


def wkey(eb, a, b):
    """Window key.  ALWAYS min/max of the two edges: a descending spectral
    window is delivered with flo > fhi and keying on the raw pair silently
    lost half the windows when this join was first written.  The key carries
    the window edges and not just the block, because round 6's `tag|eb` key
    collided and discarded one window in each of the three blocks that carry
    two crossings on the same star (REFIT_R7 S1)."""
    a, b = float(a), float(b)
    return (eb, round(min(a, b), 3), round(max(a, b), 3))


# ------------------------------------------------------------------ inputs
CAT = list(csv.DictReader(open(find('per_target_results_v3.99.csv'))))
CROSS = [r for r in CAT if r['crossing'].strip().lower() in ('true', '1')]

if PERTURB == 'mask-all-inside':
    for r in CROSS:
        r['line_offset_kms'] = '1.0'
elif PERTURB == 'mask-all-outside':
    for r in CROSS:
        r['line_offset_kms'] = '9999.0'
elif PERTURB == 'attr-by-presence':
    # the v4.01 bug expressed as data: every crossing has a nearest
    # transition, so if the mask admitted all of them, attribution would be
    # exactly "has a nearest transition" and would carry no information
    for r in CROSS:
        if r['nearest_line']:
            r['line_offset_kms'] = '3.0'
elif PERTURB == 'mask-null-far':
    for r in CROSS:
        if r['line_offset_kms'] and abs(float(r['line_offset_kms'])) > MASK_KMS:
            r['line_offset_kms'] = ''
elif PERTURB == 'attr-thin':
    _seen = 0
    for r in CROSS:
        if r['line_offset_kms'] and abs(float(r['line_offset_kms'])) <= MASK_KMS:
            _seen += 1
            if _seen > 2:
                r['line_offset_kms'] = '500.0'
elif PERTURB == 'drop-crossing':
    CROSS.pop()
elif PERTURB == 'etacrv-screened':
    for r in CROSS:
        if r['eb'] == 'A002_X122b6ff_X1041e':
            r['stage1_flag'] = 'True'

# the pre-round-7 fits, kept only so the ledger can say which verdicts moved.
# DECISIONS_R7 A4 withdraws round 6's REJECTIONS as evidence -- they were
# produced by an estimator evaluating a channel displaced by nudot*T_span/2 --
# so these values are reported as history, never as a disposition.
OLD = {}
for src, tag in (('visfit_all_v385.json', 'round 1'),
                 ('visfit_r6_result.json', 'round 6')):
    d = json.load(open(find(src)))
    for rec in (d['fits'] if 'fits' in d else d).values():
        if rec.get('status') != 'ok':
            continue
        ev = rec['event']
        rec['_round'] = tag
        OLD[wkey(ev['eb'], ev['flo_GHz'], ev['fhi_GHz'])] = rec

NEWF, NEWSTATUS, NEWSRC = {}, {}, {}
for path in newfit_files():
    d = json.load(open(path))
    for rec in (d['fits'] if 'fits' in d else d).values():
        ev = rec.get('event')
        if not ev:
            continue
        k = wkey(ev['eb'], ev['flo_GHz'], ev['fhi_GHz'])
        NEWSTATUS[k] = rec.get('status')
        if rec.get('status') == 'ok':
            NEWF[k] = rec               # a later file supersedes an earlier one
            NEWSRC[k] = os.path.basename(path)

if PERTURB == 'orphan-fit':
    k = sorted(NEWF)[0]
    NEWF[('A002_XdeadXbeef', k[1], k[2])] = NEWF[k]
elif PERTURB == 'untracked-untested':
    for k in sorted(NEWF):
        if k[0] not in OUTSTANDING_EBS:
            del NEWF[k]
            break
elif PERTURB == 'strip-first':
    for k in sorted(NEWF):
        ep = NEWF[k].get('epoch') or {}
        if ep.get('first'):
            NEWF[k]['epoch'] = {kk: vv for kk, vv in ep.items()
                                if kk != 'first'}
            break
elif PERTURB == 'strip-bound':
    for k in sorted(NEWF):
        ep = NEWF[k].get('epoch') or {}
        if not ep.get('search_product') and not ep.get('exact'):
            ep.pop('offset_channels_median_to_first', None)
            break
elif PERTURB == 'scorer-mismatch':
    k = sorted(NEWF)[0]
    NEWF[k]['star'] = dict(NEWF[k]['star'], snr_re=99.0)

SCORE = json.load(open(find('score_r7.json')))
if PERTURB == 'criterion-mismatch':
    SCORE['summary']['criterion']['re_min'] = 4.5

# Recurrence, where it has been evaluated.  A GLOB, for the same reason the
# fit inputs are one: closing a gap must be a re-run and not an edit.  Every
# `recur_*_verify*.json` / `*_verify_r7.json` written by the M10 harness is
# read, later basenames winning on a key clash; a crossing with no entry is
# reported as "recurrence not evaluated" and is never reported as having
# failed one.  ★ The files are keyed by a label, not by the star, and two of
# them carry two crossings of the same star ("61 Vir", "61 Vir second
# crossing") -- the join is on the execution block inside each record, and
# `recurrence-join-names-agree` checks the names afterwards.
RECUR = {}
for _d in _dirs():
    for _fn in sorted(os.listdir(_d)):
        if re.fullmatch(r'(recur_verify_\w+|\w+_verify(_r7)?)\.json', _fn) \
                and _fn not in ('score_r7.json',):
            try:
                _j = json.load(open(os.path.join(_d, _fn)))
            except Exception:
                continue
            if isinstance(_j, dict) and all(
                    isinstance(v, dict) and 'crossing_eb' in v
                    for v in _j.values()) and _j:
                RECUR.update(_j)
if PERTURB == 'recurrence-name':
    # ★ v4.03: this perturbation used to rename the dict KEY, and was silent.
    # It was written against a draft that took the star from the key; once the
    # star came from the record (LEDGER_V403_NOTES S4, defect 3) renaming the
    # key could not reach the join, so the driver reported the check as
    # demonstrated when nothing had been demonstrated.  A perturbation has to
    # corrupt the field the check actually reads.
    for _k in sorted(RECUR):
        RECUR[_k] = dict(RECUR[_k], star='Proxima Cen')
        break
elif PERTURB == 'recurrence-drop':
    # ★ v4.03: this perturbation used to ADD a recurrence record for a
    # rank-flagged unattributed crossing, because the expected gap was 1 and
    # adding one closed it.  Both gaps were measured on 2026-09-26 and the
    # expectation is now 0, so adding a record cannot change the count and
    # the perturbation went SILENT -- the driver reported a demonstrated
    # check where nothing was demonstrated, for the second time in this file.
    # A tripwire has to be driven in whichever direction the literal can move.
    _g = [r for r in CROSS
          if r['stage1_flag'].strip().lower() in ('true', '1')
          and (not r['line_offset_kms']
               or abs(float(r['line_offset_kms'])) > MASK_KMS)]
    _ebs = {r['eb'] for r in _g}
    for _k in sorted(RECUR):
        if RECUR[_k].get('crossing_eb') in _ebs:
            del RECUR[_k]
            break
elif PERTURB == 'recurrence-unjoined':
    for _k in sorted(RECUR):
        RECUR[_k] = dict(RECUR[_k], crossing_eb='A002_Xnosuchblock')
        break
RECUR_BY = {}
for star, rv in RECUR.items():
    blocks = [b for b in rv.get('blocks', []) if b.get('status') == 'ok']
    if not blocks:
        continue
    tmax = max(max(abs(b.get('T_matched_chan_matched_drift') or 0.0),
                   abs(b.get('T_matched_chan_best_drift') or 0.0))
               for b in blocks)
    # ★ keyed on the EXECUTION BLOCK, not on the star string: the recurrence
    # worker writes `HD 207129` where the catalogue writes `HD 207129 Gaia DR3
    # 6564091190988411520`, and a name join silently dropped that star's
    # recurrence evidence -- the same class of defect as the window-key
    # collision above.  The name agreement is checked below, not assumed.
    # ★ the star comes from the RECORD, not from the dict key: the two agree
    # in the file as written, and a perturbation that added an entry under a
    # different key exposed the assumption immediately
    RECUR_BY[rv['crossing_eb']] = dict(
        star=rv.get('star') or star, n_repeats=len(blocks), t_max=tmax,
        freq_GHz=rv.get('freq_GHz'),
        recurs=bool(tmax >= 5.0))       # the survey trigger, a literal

# the mask's occupancy of the searched band, for the chance column.  Read from
# the macro file that measures it rather than copied, so the two cannot drift.
# This dependency is one-directional -- the mask generator does not read the
# ledger -- which is the condition that the v4.01 item-5 circularity violated.
MASK_PCT = None
for d in _dirs():
    for fn in sorted(os.listdir(d)) + sorted(
            os.listdir(os.path.join(d, 'macros'))
            if os.path.isdir(os.path.join(d, 'macros')) else []):
        p = (os.path.join(d, fn) if os.path.exists(os.path.join(d, fn))
             else os.path.join(d, 'macros', fn))
        if not fn.startswith('survey_numbers') or not fn.endswith('.tex'):
            continue
        m = re.search(r'\\newcommand\{\\MaskUnionPct\}\{([0-9.]+)\}',
                      open(p, encoding='utf-8').read())
        if m and PERTURB != 'drop-mask-macro':
            MASK_PCT = float(m.group(1))


# ------------------------------------------------------------------ scoring
def ctrl_list(rec):
    """The twelve controls of one fit: 8 annulus positions and 4 off-event
    frequencies.  They are stored as pos_controls/freq_controls; an earlier
    read of a result file looked for `ctrl_snr_re_max`, found nothing, and
    briefly concluded the control stage had not run at all."""
    out = []
    for key in ('pos_controls', 'freq_controls'):
        for c in rec.get(key) or []:
            if c.get('snr_re') is not None:
                out.append(c)
    return out


def ctrl_max(rec):
    vals = [float(c['snr_re']) for c in ctrl_list(rec)]
    for key in ('ctrl_pos_max', 'ctrl_freq_max'):
        if rec.get(key) is not None:
            vals.append(float(rec[key]))
    return max(vals) if vals else None


def residual_ch(ep):
    """Displacement, in channels, between the first row this fit loaded and
    the first integration the EXTRACTION retained -- the instant the search's
    reported crossing frequency is actually referenced to.  Where the search
    product survives the result carries it; otherwise it is computed from the
    drift and the times, and where neither is possible only a bound exists."""
    sp = ep.get('search_product')
    if not sp or sp.get('t0_s') is None or not ep.get('drift_Hz_s'):
        return None
    return (ep['drift_Hz_s'] * (ep['t_min_s'] - sp['t0_s'])) / ep['chan_width_Hz']


def verdict(rec):
    """The committed three-clause criterion, applied unchanged."""
    if not rec or not rec.get('star'):
        return None
    st = rec['star']
    cm = ctrl_max(rec)
    re_s, im_s = float(st['snr_re']), float(st['snr_im'])
    c1 = bool(re_s >= RE_MIN)
    c2 = bool(abs(im_s) < IM_MAX)
    c3 = bool(cm is None or re_s > cm)
    return dict(re=re_s, im=im_s, cmax=cm, c1=c1, c2=c2, c3=c3,
                localised=bool(c1 and c2 and c3))


# ------------------------------------------------------------------ rows
ROWS = []
for r in CROSS:
    k = wkey(r['eb'], r['flo_GHz'], r['fhi_GHz'])
    loff = float(r['line_offset_kms']) if r['line_offset_kms'] else None
    row = dict(
        star=r['star_name'], display=star_alias.designation(r['star_name']),
        band=r['band'], eb=r['eb'],
        freq=float(r['f_cross_GHz']) if r['f_cross_GHz'] else None,
        flo=float(r['flo_GHz']), fhi=float(r['fhi_GHz']),
        chanw_Hz=float(r['chanw_Hz']) if r['chanw_Hz'] else None,
        tstar=float(r['star_snr']),
        screen=r['stage1_flag'].strip().lower() in ('true', '1'),
        rank_ctrl=float(r['ctrl_max_snr']) if r['ctrl_max_snr'] else None,
        line=r['nearest_line'] or '', loff=loff,
        released_dispo=r['disposition'] or '')
    # ATTRIBUTION IS THE MASK, NOT THE PRESENCE OF A NEAREST TRANSITION.
    row['attributed'] = (loff is not None and abs(loff) <= MASK_KMS)
    row['has_line'] = bool(row['line'])

    o = OLD.get(k)
    row['r6'] = dict(verdict(o), rnd=o['_round']) if o else None

    n = NEWF.get(k)
    if n is None:
        row.update(fitted=False, committed=None, corrected=None, exact=None,
                   adopted=None, epoch_verified=None,
                   dch=None, offset_arcsec=None, fit_source=None,
                   fit_status=NEWSTATUS.get(k))
    else:
        ep = n.get('epoch') or {}
        diag = n.get('diag') or {}
        first = ep.get('first')
        ex = ep.get('exact')
        # The ADOPTED verdict is at the extraction's own first retained
        # integration where that can be established: either the fit was
        # re-evaluated there, or the residual to times[0] is below 0.02
        # channels and the two are the same fit.  Where round 6 deleted the
        # `*_srcspec.npz` the residual is unknown and only a bound exists;
        # those rows are reported as PROVISIONAL, not dropped (REFIT_R7 S4
        # drops them, which loses two localisations from the table).
        _res = (ep.get('residual_channels_fit_first_to_extraction_first')
                if ep.get('search_product') else None)
        if _res is None:
            _res = residual_ch(ep)
        v_first = verdict(first)
        v_exact = verdict(ex) if isinstance(ex, dict) else None
        if v_exact is not None:
            adopted, verified, src = v_exact, True, 'own fit at extraction epoch'
        elif _res is not None and abs(_res) < 0.02:
            adopted, verified, src = v_first, True, 'identical to times[0]'
        else:
            adopted, verified, src = v_first, False, 'times[0], residual bounded'
        if adopted is None:
            # no times[0] evaluation at all: this is a gap, not a verification
            verified, src = False, 'no adopted-epoch evaluation in the result'
        row.update(
            fitted=True,
            committed=verdict(n),                     # t0 = median(TIME)
            corrected=v_first,                        # t0 = times[0]  (A1)
            exact=v_exact,
            adopted=adopted, epoch_verified=verified, epoch_source=src,
            dch=ep.get('offset_channels_median_to_first'),
            t_span_s=ep.get('t_span_s'),
            drift_Hz_s=ep.get('drift_Hz_s'),
            offset_arcsec=diag.get('offset_arcsec'),
            offset_source=diag.get('offset_source'),
            f_sci=diag.get('science_row_fraction'),
            theta_syn=diag.get('theta_syn_arcsec'),
            ann_lo=diag.get('ann_lo_arcsec'), ann_hi=diag.get('ann_hi_arcsec'),
            residual_ch=(ep.get(
                'residual_channels_fit_first_to_extraction_first')
                if ep.get('search_product') else None),
            residual_bound_ch=(None if ep.get('search_product') else
                               (abs(2.0 * ep['offset_channels_median_to_first'])
                                if ep.get('offset_channels_median_to_first')
                                is not None else None)),
            fit_source=NEWSRC.get(k), fit_status='ok')

    # five of the 56 carry no crossing frequency in the released catalogue;
    # the window centre is printed instead and the substitution is recorded,
    # rather than printing a bare dash in the column a reader uses to look the
    # window up
    row['freq_shown'] = (row['freq'] if row['freq'] is not None
                         else 0.5 * (row['flo'] + row['fhi']))
    row['freq_is_window_centre'] = row['freq'] is None

    rc = RECUR_BY.get(row['eb'])
    row['recurrence'] = rc

    # ---- the chain of DECISIONS_R7 A3:
    #   crossing -> stellar-frame attribution -> rank screen -> recurrence.
    # ★ The visibility fit is NOT a step in it (A2), so a crossing whose fit
    # is outstanding still has a chain disposition.  An earlier draft of this
    # generator wrote `untested` into the chain column for the six unfitted
    # windows, which silently promoted the consistency check back into the
    # chain and, worse, hid CP-72 2713's second-epoch result behind a disk
    # queue.  The untestedness lives in the fit columns, where it belongs.
    if row['attributed']:
        chain = 'attributed'
    elif not row['screen']:
        chain = 'unattributed; below rank screen'
    elif rc and not rc['recurs']:
        chain = 'unattributed; rank-flagged; tested and does not recur'
    elif row['released_dispo'] and 'epoch 2' in row['released_dispo']:
        chain = 'unattributed; rank-flagged; absent in second epoch'
    else:
        chain = 'unattributed; rank-flagged; recurrence not evaluated'
    row['chain'] = chain
    # a short code for the table column; the words stay in the JSON, the CSV
    # and the caption legend, because 56 rows x the full sentence is 290 pt
    # wider than a landscape page and the first draft of this table silently
    # ran off it
    row['chain_code'] = {
        'attributed': 'A',
        'unattributed; below rank screen': 'U1',
        'unattributed; rank-flagged; tested and does not recur': 'U2',
        'unattributed; rank-flagged; absent in second epoch': 'U3',
        'unattributed; rank-flagged; recurrence not evaluated': 'U4',
    }[chain]
    # the consistency check's own status, reported beside the chain
    row['vis'] = ('untested' if not row['fitted'] or not row['adopted'] else
                  ('localised' if row['adopted']['localised']
                   else 'not localised'))
    ROWS.append(row)

if PERTURB == 'kill-localisations':
    for row in ROWS:
        if row['fitted'] and row['adopted']:
            row['adopted'] = dict(row['adopted'], localised=False, c1=False,
                                  re=0.0)
elif PERTURB == 'candidate-word':
    for row in ROWS:
        if row['chain'].startswith('unattributed; rank-flagged'):
            row['chain'] = 'candidate'
            break

if PERTURB == 'flip-small-D':
    for row in ROWS:
        if (row['fitted'] and row['adopted'] and row['dch'] is not None
                and abs(row['dch']) < D_SAME_CH
                and row['committed']['localised']):
            row['adopted'] = dict(row['adopted'], re=1.0, c1=False,
                                  localised=False)
            break

N_CROSS = len(ROWS)
FITTED = [r for r in ROWS if r['fitted']]
UNTESTED = [r for r in ROWS if not r['fitted']]
ATTR = [r for r in ROWS if r['attributed']]
UNATTR = [r for r in ROWS if not r['attributed']]
HASLINE = [r for r in ROWS if r['has_line']]
SCREENED = [r for r in ROWS if r['screen']]
LOC_COM = [r for r in FITTED if r['committed'] and r['committed']['localised']]
LOC_COR = [r for r in FITTED if r['adopted'] and r['adopted']['localised']]
LOC_COM_UN = [r for r in LOC_COM if not r['attributed']]
LOC_COR_UN = [r for r in LOC_COR if not r['attributed']]
HAS_COR = [r for r in FITTED if r['adopted']]
# of the adopted-epoch localisations, those whose epoch residual is VERIFIED
# against a surviving extraction product, and those resting on a bound
LOC_COR_VER = [r for r in LOC_COR if r['epoch_verified']]
LOC_COR_PROV = [r for r in LOC_COR if not r['epoch_verified']]
PROV = [r for r in FITTED if r['adopted'] and not r['epoch_verified']]
MOVED = [r for r in FITTED if r['committed'] and r['adopted']
         and r['committed']['localised'] != r['adopted']['localised']]
# the chain's own counts
UNATTR_SCREENED = [r for r in UNATTR if r['screen']]
CONFIRMED = [r for r in UNATTR_SCREENED
             if r['recurrence'] and r['recurrence']['recurs']]
# recurrence was also evaluated OFF the chain, for the crossings the epoch
# correction moved (referee_r7/RECURRENCE_FIVE.md); reported, not hidden
RECUR_ROWS = [r for r in ROWS if r['recurrence']]
RECUR_ANY = [r for r in RECUR_ROWS if r['recurrence']['recurs']]
RECUR_TMAX = max((r['recurrence']['t_max'] for r in RECUR_ROWS), default=None)
RECUR_NREP = sum(r['recurrence']['n_repeats'] for r in RECUR_ROWS)

# A2, measured: how much work the second and third clauses do.  DECISIONS_R7
# A2 states that under the corrected epoch clauses 2 and 3 reject nothing;
# measured over ALL fitted crossings that is not quite true, and the exception
# is reported rather than smoothed -- see LEDGER_V403_NOTES.md.
COR_C1 = [r for r in HAS_COR if r['adopted']['c1']]
COR_C1_ONLY = [r for r in COR_C1 if not r['adopted']['localised']]
COM_C1 = [r for r in FITTED if r['committed'] and r['committed']['c1']]
COM_C1_ONLY = [r for r in COM_C1 if not r['committed']['localised']]
# and the same restricted to rows whose epoch residual is verified, which is
# the set REFIT_R7 S6 quoted
VER = [r for r in FITTED if r['epoch_verified'] and r['adopted']]
VER_C1 = [r for r in VER if r['adopted']['c1']]
VER_C1_ONLY = [r for r in VER_C1 if not r['adopted']['localised']]


# ------------------------------------------- false alarms on the controls
def fa(samples):
    n = len(samples)
    a = sum(1 for re_, im_ in samples if re_ >= RE_MIN)
    b = sum(1 for re_, im_ in samples if re_ >= RE_MIN and abs(im_) < IM_MAX)
    return dict(n=n, re_ge=a, rate_re=(a / n if n else None),
                full=b, rate_full=(b / n if n else None))


def samples_from(getter):
    out = []
    for k, n in NEWF.items():
        rec = getter(n)
        for c in ctrl_list(rec or {}):
            if c.get('snr_im') is not None:
                out.append((float(c['snr_re']), float(c['snr_im'])))
    return out


S_COM = samples_from(lambda n: n)
S_COR = samples_from(lambda n: (n.get('epoch') or {}).get('first'))
if PERTURB == 'fa-inflate':
    S_COM = [(6.0, 0.1)] * (len(S_COM) // 2) + S_COM[len(S_COM) // 2:]
FA_COM, FA_COR = fa(S_COM), fa(S_COR)
EXP_COM = (FA_COM['rate_full'] or 0.0) * len(FITTED)
EXP_COR = (FA_COR['rate_full'] or 0.0) * len(HAS_COR)
EXP_ATTR = (MASK_PCT / 100.0 * N_CROSS) if MASK_PCT is not None else None


# ============================================================== THE CHECKS
# Each check names an input that would make it fail.  selftest_v403.py drives
# that input and confirms the failure; a check it cannot make fail is removed.
check(N_CROSS == 56, 'n-crossings',
      'the catalogue no longer carries 56 threshold crossings -- fails if the '
      'export, the trigger or the hold-out changes', 'got %d' % N_CROSS)

check(len(FITTED) + len(UNTESTED) == N_CROSS, 'partition-fitted',
      'a crossing is neither fitted nor untested -- fails if a row is dropped '
      'from the join')

_orphan = sorted(k for k in NEWF if k not in
                 {wkey(r['eb'], r['flo_GHz'], r['fhi_GHz']) for r in CROSS})
check(not _orphan, 'no-orphan-fit',
      'a fit matches no threshold crossing, so the join or the window key is '
      'wrong -- fails if a fit is run on a window the survey does not contain',
      repr(_orphan[:3]))

check(len(ATTR) < len(HASLINE), 'mask-not-presence',
      'attribution has become equivalent to "has a nearest transition", which '
      'is true of all 56 crossings -- this is the v4.01 defect, and it fails '
      'if the mask stops rejecting any crossing that has a catalogued line',
      '%d attributed of %d with a nearest transition' % (len(ATTR), len(HASLINE)))

check(len(ATTR) > 0 and len(UNATTR) > 0, 'mask-discriminates',
      'the +-50 km/s mask admits all crossings or none, so attribution carries '
      'no information -- fails if every line_offset_kms is dragged inside or '
      'outside the mask',
      '%d attributed, %d unattributed' % (len(ATTR), len(UNATTR)))

_mask_far = max((abs(r['loff']) for r in ROWS if r['loff'] is not None),
                default=0.0)
check(_mask_far > MASK_KMS, 'mask-far-example',
      'no crossing lies outside the mask at all -- fails if the nearest '
      'transition is within 50 km/s for every crossing, which would make the '
      'attribution step vacuous even where the counts differ',
      'largest |dv| = %.1f km/s' % _mask_far)

_bad = [r['eb'] for r in UNTESTED if r['eb'] not in OUTSTANDING_EBS]
check(not _bad, 'untested-accounted',
      'a crossing is untested for a reason not recorded in OUTSTANDING_EBS -- '
      'fails when a fit disappears from a block not known to be blocked on '
      'host disk; it does NOT fail when the outstanding blocks land, which '
      'only shrinks the set', repr(sorted(set(_bad))))

check(all(r['committed'] is None and r['adopted'] is None for r in UNTESTED),
      'untested-carry-no-verdict',
      'an untested crossing carries a localisation verdict -- fails if a '
      'missing fit is ever defaulted to a non-detection')

_nobound = [r['display'] for r in PROV if r.get('residual_bound_ch') is None]
check(not _nobound, 'provisional-rows-bounded',
      'a crossing whose epoch residual could not be verified also carries no '
      'bound on it, so the adopted-epoch verdict would be unqualified -- '
      'fails if a fit is written without the epoch block, or if a search '
      'product is lost without the displacement being recorded',
      repr(_nobound))

check(all(r['adopted'] is not None for r in FITTED),
      'adopted-verdict-present',
      'a fitted crossing has no adopted-epoch verdict at all -- fails if the '
      '`first` evaluation is missing from a result file, which would silently '
      'reduce the denominator instead of showing as a gap')

_c = SCORE['summary']['criterion']
check(_c['re_min'] == RE_MIN and _c['im_max'] == IM_MAX
      and _c['mask_kms'] == MASK_KMS and _c['commit'] == CRITERION_COMMIT,
      'criterion-unmoved',
      'the thresholds here differ from those the scorer recorded -- fails if '
      'any threshold is retuned in one place and not the other',
      'scorer %r vs here %r' % (_c, dict(re_min=RE_MIN, im_max=IM_MAX,
                                         mask_kms=MASK_KMS,
                                         commit=CRITERION_COMMIT)))

_recomputed = [r for r in FITTED
               if r['committed'] and r['committed']['c1']
               and r['committed']['c2'] and r['committed']['c3']]
check(sorted(id(x) for x in _recomputed) == sorted(id(x) for x in LOC_COM),
      'criterion-is-conjunction',
      'the localised set is not exactly the conjunction of the three clauses '
      '-- fails if verdict() and the published clause flags drift apart')

check((FA_COM['rate_full'] or 0.0) <= FA_CEILING
      and (FA_COR['rate_full'] or 0.0) <= FA_CEILING,
      'false-alarm-ceiling',
      'the full criterion fires on more than the 1 %% of event-free control '
      'samples committed before round 6 -- fails if new blocks push the '
      'control tail up, and it must then be reported, not retuned',
      'committed %.4f, corrected %.4f'
      % (FA_COM['rate_full'] or 0, FA_COR['rate_full'] or 0))

check(len(LOC_COR) > 5.0 * max(EXP_COR, 1e-9), 'localisations-not-false-alarms',
      'the localisations are no longer clearly in excess of the annulus '
      'false-alarm expectation -- fails if a refit reduces the localised count '
      'or the control tail rises to meet it',
      '%d observed against %.2f expected' % (len(LOC_COR), EXP_COR))

_dis = [(r['display'], r['dch']) for r in MOVED
        if r['dch'] is not None and abs(r['dch']) < D_SAME_CH]
check(not _dis, 'epoch-change-is-displacement',
      'a verdict changes between the two epoch conventions where the '
      'displacement is under a quarter channel, i.e. where they are the same '
      'experiment -- fails if the difference between the conventions is not '
      'driven by displacement', repr(_dis))

check(MASK_PCT is not None, 'mask-occupancy-available',
      'the mask-occupancy macro MaskUnionPct is not in any survey_numbers '
      'file, so the chance column for attribution cannot be computed -- fails '
      'if that generator is renamed, dropped, or run after this one')

check(EXP_ATTR is None or len(ATTR) > EXP_ATTR, 'attribution-informative',
      'the attributed count is no larger than the mask would catch by chance '
      '-- fails if the mask grows to cover the band or the attributions thin '
      'out', '%d observed against %.2f expected' % (len(ATTR), EXP_ATTR or 0))

_c3only = [(r['display'], r['adopted']['im'], r['adopted']['cmax'])
           for r in COR_C1_ONLY if r['adopted']['c2'] and not r['adopted']['c3']]
check(not _c3only, 'clause3-never-rejects-alone',
      'the twelve-control clause rejected a crossing that the imaginary-part '
      'clause accepted -- fails the measurement behind DECISIONS_R7 A2, which '
      'is that a twelve-control screen resolves a rank of ~1/13 and is passed '
      'by anything above ~2 sigma; if it ever rejects alone, the fit is doing '
      'spatial work the A2 analysis says it cannot', repr(_c3only))

# ★ Two kinds of harmless disagreement, both named rather than tolerated in
# silence.  The catalogue writes `HD 207129 Gaia DR3 6564091190988411520`
# where the harness writes `HD 207129`, so the catalogue name may EXTEND the
# record's.  And one harness keys its plan by a label -- `61 Vir second
# crossing` -- and writes that label into the record's `star` field, so the
# record's name may extend the catalogue's.  Both are prefix relations and
# both are LISTED in the json as `recurrence_name_normalised`, so the
# looseness is visible; anything that is not a prefix relation still fails.
# The upstream defect (a plan label in a star field) belongs in the harness.
_norm, _rn = [], []
for r in RECUR_ROWS:
    a, b = star_alias.canon(r['recurrence']['star']), star_alias.canon(r['star'])
    if a == b or a == r['star']:
        continue
    if r['star'].startswith(r['recurrence']['star']) or a.startswith(b):
        _norm.append((r['display'], r['recurrence']['star']))
    else:
        _rn.append((r['display'], r['recurrence']['star']))
check(not _rn, 'recurrence-join-names-agree',
      'the recurrence file and the catalogue disagree about which star a '
      'block belongs to, and not by one name extending the other -- the join '
      'is on the execution block, so this fails if that block is ever reused '
      'for a different star, which is the only way an eb join can go wrong',
      repr(_rn))

check(len(RECUR_ROWS) == len(RECUR_BY), 'recurrence-fully-joined',
      'a recurrence result did not match any crossing in the ledger -- fails '
      'if the recurrence worker studies a block the catalogue does not carry '
      'a crossing for, or if a name-based join is reintroduced',
      '%d of %d joined' % (len(RECUR_ROWS), len(RECUR_BY)))

_vocab = {'untested', 'localised', 'not localised'}
check({r['vis'] for r in ROWS} <= _vocab, 'vis-status-vocabulary',
      'the visibility column carries a status outside the closed vocabulary '
      '-- fails if a fourth state is introduced without deciding whether it '
      'counts as tested')

_cand = [r['chain'] for r in ROWS if 'candidat' in r['chain'].lower()]
check(not _cand, 'no-candidate-word',
      'a disposition calls something a candidate -- fails the moment the '
      'vocabulary is loosened; under the A3 chain the count is zero and the '
      'ledger says so with counts, not with a label')

ETA = [r for r in ROWS if r['eb'] == 'A002_X122b6ff_X1041e']
check(len(ETA) == 1, 'etacrv-present',
      'the eta Crv crossing A002_X122b6ff_X1041e is not in the ledger -- fails '
      'if the block leaves the catalogue')
_e = ETA[0]
if _e['fitted']:
    check(_e['committed']['localised'] and _e['adopted']['localised']
          and not _e['attributed'] and not _e['screen']
          and 5.0 <= _e['tstar'] < 5.01 and abs(_e['dch']) < 0.5,
          'etacrv-facts',
          'the four facts DECISIONS_R7 A5 requires to be stated together about '
          'eta Crv no longer all hold: localised under BOTH conventions, '
          'unattributed, FAILS the rank screen, T* just over the trigger -- '
          'fails if any of them moves, e.g. if the rank screen flag changes',
          'loc %s/%s attr %s screen %s T* %.4f D %.2f'
          % (_e['committed']['localised'], _e['adopted']['localised'],
             _e['attributed'], _e['screen'], _e['tstar'], _e['dch']))

RECUR_GAP = [r for r in UNATTR_SCREENED
             if not r['recurrence']
             and 'epoch 2' not in (r['released_dispo'] or '')]
check(len(RECUR_GAP) == N_RECUR_GAP_EXPECTED, 'recurrence-gap-known',
      'the number of rank-flagged unattributed crossings with NO recurrence '
      'and no second-epoch evidence has changed -- fails both if a new gap '
      'opens and if the known one is closed, because the terminal claim of '
      'the chain has to be rewritten either way',
      '%d: %s' % (len(RECUR_GAP), [r['display'] for r in RECUR_GAP]))

# cross-check against the independently written scorer, window by window, so
# that a change of logic here cannot pass unnoticed.  Windows the scorer never
# saw (a later fit file) are skipped by construction, which is what lets the
# outstanding six be folded in without rescoring.
# ★ The key must carry the crossing FREQUENCY as well as the block: BD+05 1668
# has four crossings in `A002_Xc7fa6f_X28a8`, and keying on (star, eb) alone
# compared this ledger's four rows against whichever of the scorer's four the
# dict happened to keep -- three spurious mismatches, the same collision that
# made round 6 silently discard a window.
_SC = {(r['star'], r['eb'], round(r['freq'] or 0.0, 6)): r
       for r in SCORE['rows']}
assert len(_SC) == len(SCORE['rows']), 'scorer key still collides'
_mis = []
for r in FITTED:
    s = _SC.get((r['star'], r['eb'], round(r['freq'] or 0.0, 6)))
    if not s or not s.get('new'):
        continue
    for mine, theirs in ((r['committed'], s['new']),
                         (r['corrected'], s.get('new_first')),
                         (r['adopted'] if r['epoch_verified'] else None,
                          s.get('new_exact'))):
        if mine is None or theirs is None:
            continue
        for f in ('re', 'im'):
            if abs(float(mine[f]) - float(theirs[f])) > 1e-9:
                _mis.append((r['display'], r['eb'], f, mine[f], theirs[f]))
        if mine['localised'] != theirs['localised']:
            _mis.append((r['display'], r['eb'], 'localised',
                         mine['localised'], theirs['localised']))
check(not _mis, 'agrees-with-scorer',
      'this ledger and score_r7.py disagree on a window they both carry -- '
      'fails if either the join, the control set or the clause logic is '
      'changed in one and not the other', repr(_mis[:3]))


# ================================================================= outputs
def fmt(x, n=2):
    return '--' if x is None or (isinstance(x, float) and math.isnan(x)) \
        else ('%.*f' % (n, x))


def tx(s):
    return str(s).replace('_', r'\_').replace('&', r'\&')


ap = argparse.ArgumentParser()
ap.add_argument('--outdir', default=HERE)
ARGS = ap.parse_args()
OUTDIR = ARGS.outdir
os.makedirs(OUTDIR, exist_ok=True)


def out(name):
    return os.path.join(OUTDIR, name)


# ---- the principal table.  All 56 crossings, sorted so that the untested
# rows are visible rather than buried: by star, then frequency.
# MEASURED natural width (\savebox, openjournal.cls has \textwidth = 7.1in =
# 513 pt): 483 pt at \tiny, 561 pt at \scriptsize.  It therefore goes in a
# full-width `table*` at \tiny.  ★ Measure it that way, not by looking for an
# overfull warning in a scratch document: two tabulars \input into the same
# paragraph merge into one horizontal box and report a 900 pt overfull that
# belongs to neither of them.
SROWS = sorted(ROWS, key=lambda r: (r['display'].lower(), r['freq'] or 0.0))
L = ['% GENERATED by ledger_v403.py -- do not hand-edit.',
     '% One row per threshold crossing (R1-M4).  Both epoch conventions.',
     r'\begin{tabular}{@{}l@{~}l@{~}c@{~}r@{~}r@{~}c@{~}l@{~}r@{~~}'
     r'r@{~}r@{~}r@{~~}r@{~}r@{~}r@{~~}r@{~}r@{~}l@{}}',
     r'\hline',
     r'& & & & & & & & \multicolumn{3}{c}{committed $t_0=\mathrm{median}(T)$}'
     r' & \multicolumn{3}{c}{adopted $t_0=T_0$} & & & \\',
     r'Star & block & B & $\nu$ (GHz) & $T_\star$ & scr & line & $\Delta v$ &'
     r' Re/$\sigma$ & Im/$\sigma$ & ctrl &'
     r' Re/$\sigma$ & Im/$\sigma$ & ctrl & $D$ & off & ch \\',
     r'\hline']
for r in SROWS:
    def blk(v):
        if v is None:
            return (r'\emph{n.f.}', r'\emph{n.f.}', r'\emph{n.f.}')
        s = fmt(v['re'])
        return (r'\textbf{%s}' % s if v['localised'] else s,
                fmt(v['im']), fmt(v['cmax']))
    a = blk(r['committed'])
    b = blk(r['adopted'])
    if r['fitted'] and not r['epoch_verified']:
        # PROVISIONAL: round 6 deleted this block's extraction product, so the
        # residual between times[0] and the epoch the search referenced is
        # bounded, not known.  Marked, never dropped.
        b = (b[0] + r'$^{\dagger}$', b[1], b[2])
    L.append('%s & %s & %s & %s & %.3f & %s & %s & %s & %s & %s & %s & %s & '
             '%s & %s & %s & %s & %s \\\\'
             % (r['display'], tx(r['eb'].replace('A002_', '')), r['band'],
                fmt(r['freq_shown'], 4) + ('*' if r['freq_is_window_centre']
                                           else ''), r['tstar'],
                ('Y' if r['screen'] else '--'),
                (tx(r['line']) if r['attributed'] else '--'),
                fmt(r['loff'], 1), a[0], a[1], a[2], b[0], b[1], b[2],
                fmt(r['dch'], 2), fmt(r['offset_arcsec'], 3),
                r['chain_code']))
L += [r'\hline', r'\end{tabular}']
open(out('tab_ledger_v403.tex'), 'w').write('\n'.join(L) + '\n')

_CODES = {}
for r in ROWS:
    _CODES.setdefault(r['chain_code'], r['chain'])
# ★ Emitted as a ROBUST command, \input in the PREAMBLE, not \input inside
# the caption.  `\input` in a caption argument makes hyperref's \Hy@tempa
# read a runaway argument ("Argument of \Hy@tempa has an extra }"), because
# the caption is re-read when it is written to the .aux.  Same family as the
# \pv macro, which had to be \DeclareRobustCommand for the same reason.
open(out('ledger_legend_v403.tex'), 'w').write(
    '% GENERATED by ledger_v403.py -- \\input this in the PREAMBLE and use\n'
    '% \\LedgerLegend in the caption, so the legend cannot fall out of step\n'
    '% with the codes in the column and hyperref can still read the caption.\n'
    '\\DeclareRobustCommand{\\LedgerLegend}{%\n'
    + ' \\; '.join('\\textbf{%s} %s' % (c, _CODES[c].replace('; ', ', '))
                    for c in sorted(_CODES))
    + '. Frequencies marked * are window centres, the crossing frequency not '
      'being recorded. Block identifiers omit the constant \\texttt{A002\\_} '
      'prefix. Rows marked \\emph{n.f.} are UNTESTED: the visibility '
      'fit is outstanding, not negative. $^{\\dagger}$ marks an adopted-epoch '
      'verdict whose residual to the extraction epoch is bounded rather than '
      'verified.}\n')

# ---- the summary counts, observed beside expected by chance
# ★ THREE columns, not four.  The "chance model" column made the tabular
# 388 pt wide against a 251 pt text column, and promoting the float to a
# table* to fit it DOUBLED its page cost -- 0.27 pp for fourteen numbers.
# The models are short enough to live in the caption, which is set at
# column width anyway; the numbers stay here.  Measure the box with
# \savebox and \the\wd, not by waiting for an overfull warning.
def row(label, obs, exp, src=None):
    return '%s & %s & %s \\\\' % (label, obs, exp)


S = ['% GENERATED by ledger_v403.py -- do not hand-edit.',
     r'\begin{tabular}{@{}lrr@{}}', r'\hline',
     r'Quantity & Observed & Chance \\', r'\hline',
     row('Threshold crossings', '%d' % N_CROSS, '--',
         'the trigger defines them'),
     row('Fitted in the visibilities', '%d' % len(FITTED), '--',
         'host disk, not statistics'),
     row('Untested (fit outstanding)', '%d' % len(UNTESTED), '--',
         '%d blocks' % len({r['eb'] for r in UNTESTED})),
     row('Line-attributed ($|\\Delta v|\\leq%.0f$\\,km\\,s$^{-1}$)' % MASK_KMS,
         '%d' % len(ATTR),
         (fmt(EXP_ATTR, 1) if EXP_ATTR is not None else '--'),
         '%.1f\\%% mask occupancy $\\times$ %d' % (MASK_PCT or 0, N_CROSS)),
     row('Unattributed', '%d' % len(UNATTR),
         (fmt(N_CROSS - (EXP_ATTR or 0), 1) if EXP_ATTR is not None else '--'),
         'complement'),
     row('Localised, committed epoch', '%d' % len(LOC_COM), fmt(EXP_COM, 2),
         '%.2f\\%% of %d control samples $\\times$ %d'
         % (100 * (FA_COM['rate_full'] or 0), FA_COM['n'], len(FITTED))),
     row('Localised, adopted epoch', '%d' % len(LOC_COR), fmt(EXP_COR, 2),
         '%.2f\\%% of %d control samples $\\times$ %d'
         % (100 * (FA_COR['rate_full'] or 0), FA_COR['n'], len(HAS_COR))),
     row('\\quad epoch residual verified', '%d' % len(LOC_COR_VER), '--',
         'extraction product survives'),
     row('\\quad provisional ($^{\\dagger}$, residual bounded)',
         '%d' % len(LOC_COR_PROV), '--', 'product deleted in round 6'),
     row('\\quad of those, unattributed', '%d' % len(LOC_COR_UN), '--', ''),
     row('Rank-screen flagged', '%d' % len(SCREENED), '--', ''),
     row('Unattributed and rank-flagged', '%d' % len(UNATTR_SCREENED), '--', ''),
     row('Unattributed, rank-flagged, recurring', '%d' % len(CONFIRMED), '--',
         'end of the chain'),
     row('Crossings with a recurrence test', '%d' % len(RECUR_ROWS), '--',
         '%d repeat blocks, max $T_\\star$ %s'
         % (RECUR_NREP, ('%.2f' % RECUR_TMAX) if RECUR_TMAX else '--')),
     r'\hline', r'\end{tabular}']
open(out('tab_ledgersum_v403.tex'), 'w').write('\n'.join(S) + '\n')

# ---- macros.  Deliberately NOT re-using \LgNLocal: its meaning has changed
# (there are now two conventions), and a surviving use of the old name must
# fail the undefined-macro gate rather than print a stale number silently.
M = []
m = lambda k, v: M.append('\\newcommand{\\%s}{%s}' % (k, v))
m('LgNCross', '%d' % N_CROSS)
m('LgNFit', '%d' % len(FITTED))
m('LgNUntest', '%d' % len(UNTESTED))
m('LgNUntestBlocks', '%d' % len({r['eb'] for r in UNTESTED}))
m('LgFitPct', '%.0f' % (100.0 * len(FITTED) / N_CROSS))
m('LgNLocalCom', '%d' % len(LOC_COM))
m('LgNLocalCor', '%d' % len(LOC_COR))
m('LgNLocalCorVer', '%d' % len(LOC_COR_VER))
m('LgNLocalCorProv', '%d' % len(LOC_COR_PROV))
m('LgNProv', '%d' % len(PROV))
m('LgNCorEval', '%d' % len(HAS_COR))
m('LgNLocalComUnattr', '%d' % len(LOC_COM_UN))
m('LgNLocalCorUnattr', '%d' % len(LOC_COR_UN))
m('LgNAttr', '%d' % len(ATTR))
m('LgNUnattr', '%d' % len(UNATTR))
m('LgNScreen', '%d' % len(SCREENED))
m('LgNUnattrScreen', '%d' % len(UNATTR_SCREENED))
m('LgNConfirmed', '%d' % len(CONFIRMED))
m('LgNRecurGap', '%d' % len(RECUR_GAP))
m('LgRecurGapStar', RECUR_GAP[0]['display'] if RECUR_GAP else 'none')
m('LgNRecurTested', '%d' % len(RECUR_ROWS))
m('LgNRecurRepeats', '%d' % RECUR_NREP)
m('LgNRecurAny', '%d' % len(RECUR_ANY))
m('LgRecurTMax', ('%.2f' % RECUR_TMAX) if RECUR_TMAX is not None else '--')
m('LgNFreqWinCentre', '%d' % sum(1 for r in ROWS if r['freq_is_window_centre']))
m('LgNMoved', '%d' % len(MOVED))
m('LgReMin', '%.0f' % RE_MIN)
m('LgImMax', '%.0f' % IM_MAX)
m('LgMaskKms', '%.0f' % MASK_KMS)
m('LgCommit', r'\texttt{%s}' % CRITERION_COMMIT)
m('LgFaNCom', '%d' % FA_COM['n'])
m('LgFaNCor', '%d' % FA_COR['n'])
m('LgFaPctCom', '%.2f' % (100 * (FA_COM['rate_full'] or 0)))
m('LgFaPctCor', '%.2f' % (100 * (FA_COR['rate_full'] or 0)))
m('LgFaPctReCom', '%.2f' % (100 * (FA_COM['rate_re'] or 0)))
m('LgFaPctReCor', '%.2f' % (100 * (FA_COR['rate_re'] or 0)))
m('LgFaCeilPct', '%.0f' % (100 * FA_CEILING))
m('LgExpLocalCom', '%.2f' % EXP_COM)
m('LgExpLocalCor', '%.2f' % EXP_COR)
m('LgExpAttr', '%.1f' % (EXP_ATTR if EXP_ATTR is not None else float('nan')))
m('LgMaskOccPct', '%.1f' % (MASK_PCT or 0))
# A2: what the second and third clauses actually reject
m('LgNCorReFour', '%d' % len(COR_C1))
m('LgNCorReFourRejected', '%d' % len(COR_C1_ONLY))
m('LgNComReFour', '%d' % len(COM_C1))
m('LgNComReFourRejected', '%d' % len(COM_C1_ONLY))
m('LgNVerReFour', '%d' % len(VER_C1))
m('LgNVerReFourRejected', '%d' % len(VER_C1_ONLY))
m('LgVerRejectStar', VER_C1_ONLY[0]['display'] if VER_C1_ONLY else 'none')
m('LgDSame', '%.2f' % D_SAME_CH)
_dmax = max((abs(r['dch']) for r in FITTED if r['dch'] is not None), default=0)
m('LgDMax', '%.1f' % _dmax)
m('LgNChecks', '%d' % len(CHECKS))
open(out('survey_numbers_round80.tex'), 'w').write('\n'.join(M) + '\n')

# ---- machine-readable ledger and released CSV
summary = dict(
    generator='ledger_v403.py',
    criterion=dict(re_min=RE_MIN, im_max=IM_MAX, mask_kms=MASK_KMS,
                   commit=CRITERION_COMMIT, committed=CRITERION_TIME,
                   fa_ceiling=FA_CEILING, d_same_ch=D_SAME_CH),
    epoch_adopted='t0 = times[0] (DECISIONS_R7 A1)',
    fit_files=[os.path.basename(p) for p in newfit_files()],
    n_crossings=N_CROSS, n_fitted=len(FITTED), n_untested=len(UNTESTED),
    untested=[dict(star=r['display'], eb=r['eb'], freq=r['freq'])
              for r in UNTESTED],
    n_attributed=len(ATTR), n_unattributed=len(UNATTR),
    n_localised_committed=len(LOC_COM), n_localised_corrected=len(LOC_COR),
    n_localised_corrected_verified=len(LOC_COR_VER),
    n_localised_corrected_provisional=len(LOC_COR_PROV),
    n_provisional_epoch=len(PROV),
    provisional_epoch=[dict(star=r['display'], eb=r['eb'],
                            bound_ch=r.get('residual_bound_ch'))
                       for r in PROV],
    n_corrected_evaluated=len(HAS_COR),
    n_localised_unattributed_committed=len(LOC_COM_UN),
    n_localised_unattributed_corrected=len(LOC_COR_UN),
    localised_unattributed_committed=[r['display'] + ' ' + r['eb']
                                      for r in LOC_COM_UN],
    localised_unattributed_corrected=[r['display'] + ' ' + r['eb']
                                      for r in LOC_COR_UN],
    n_moved_by_epoch=len(MOVED),
    moved_by_epoch=[dict(star=r['display'], eb=r['eb'], dch=r['dch'],
                         committed=r['committed']['localised'],
                         corrected=r['adopted']['localised'],
                         re_committed=r['committed']['re'],
                         re_corrected=r['adopted']['re'])
                    for r in MOVED],
    n_screen=len(SCREENED), n_unattr_screen=len(UNATTR_SCREENED),
    n_confirmed=len(CONFIRMED),
    n_recurrence_gap=len(RECUR_GAP),
    recurrence_gap=[dict(star=r['display'], eb=r['eb']) for r in RECUR_GAP],
    recurrence=dict(n_crossings_tested=len(RECUR_ROWS),
                    n_repeat_blocks=RECUR_NREP, n_recurring=len(RECUR_ANY),
                    max_T_over_repeats=RECUR_TMAX, trigger=5.0),
    recurrence_name_normalised=_norm,
    chain_counts={c: sum(1 for r in ROWS if r['chain'] == c)
                  for c in sorted({r['chain'] for r in ROWS})},
    vis_counts={c: sum(1 for r in ROWS if r['vis'] == c)
                for c in sorted({r['vis'] for r in ROWS})},
    false_alarm_committed=FA_COM, false_alarm_corrected=FA_COR,
    expected_localised_committed=EXP_COM,
    expected_localised_corrected=EXP_COR,
    mask_occupancy_pct=MASK_PCT, expected_attributed=EXP_ATTR,
    clause_power=dict(corrected_re_ge_4=len(COR_C1),
                      corrected_rejected_by_clauses_2_3=len(COR_C1_ONLY),
                      committed_re_ge_4=len(COM_C1),
                      committed_rejected_by_clauses_2_3=len(COM_C1_ONLY),
                      verified_re_ge_4=len(VER_C1),
                      verified_rejected_by_clauses_2_3=len(VER_C1_ONLY),
                      rejected=[dict(star=r['display'], eb=r['eb'],
                                     re=r['adopted']['re'],
                                     im=r['adopted']['im'],
                                     cmax=r['adopted']['cmax'])
                                for r in COR_C1_ONLY]),
    checks=[dict(name=n, fails_if=t) for n, t in CHECKS],
)
json.dump(dict(summary=summary, rows=ROWS), open(out('ledger_v403.json'), 'w'),
          indent=1)

with open(out('ledger_v403.csv'), 'w', newline='') as fh:
    w = csv.writer(fh)
    w.writerow(['star', 'eb', 'band', 'f_cross_GHz', 'T_star', 'rank_screen',
                'nearest_line', 'line_offset_kms', 'attributed',
                're_committed', 'im_committed', 'ctrl_committed',
                'localised_committed',
                're_adopted', 'im_adopted', 'ctrl_adopted',
                'localised_adopted', 'epoch_verified', 'epoch_source',
                'displacement_ch', 'offset_arcsec', 'offset_source',
                'science_row_fraction', 'residual_ch', 'residual_bound_ch',
                're_round6', 'localised_round6', 'fit_source', 'chain',
                'visibility_status', 'recurrence_n_repeats',
                'recurrence_max_T'])
    for r in SROWS:
        c, d, o = r['committed'], r['adopted'], r['r6']
        w.writerow([r['star'], r['eb'], r['band'], r['freq'], r['tstar'],
                    r['screen'], r['line'], r['loff'], r['attributed'],
                    c and c['re'], c and c['im'], c and c['cmax'],
                    c and c['localised'],
                    d and d['re'], d and d['im'], d and d['cmax'],
                    d and d['localised'], r.get('epoch_verified'),
                    r.get('epoch_source'),
                    r['dch'], r.get('offset_arcsec'), r.get('offset_source'),
                    r.get('f_sci'), r.get('residual_ch'),
                    r.get('residual_bound_ch'),
                    o and o['re'], o and o['localised'],
                    r.get('fit_source'), r['chain'], r['vis'],
                    (r['recurrence'] or {}).get('n_repeats'),
                    (r['recurrence'] or {}).get('t_max')])

print('ledger_v403: %d crossings, %d fitted, %d untested in %d blocks'
      % (N_CROSS, len(FITTED), len(UNTESTED),
         len({r['eb'] for r in UNTESTED})))
print('  attributed %d (chance %.1f) / unattributed %d'
      % (len(ATTR), EXP_ATTR or float('nan'), len(UNATTR)))
print('  localised: committed %d (chance %.2f), adopted %d of %d (chance %.2f)'
      % (len(LOC_COM), EXP_COM, len(LOC_COR), len(HAS_COR), EXP_COR))
print('    of the adopted, %d epoch-verified and %d provisional'
      % (len(LOC_COR_VER), len(LOC_COR_PROV)))
print('  localised AND unattributed: committed %d, adopted %d'
      % (len(LOC_COM_UN), len(LOC_COR_UN)))
print('  verdict moved with the epoch: %d (max |D| %.1f ch)' % (len(MOVED), _dmax))
print('  clauses 2+3 reject %d of %d with Re/sigma>=4 (adopted epoch); '
      '%d of %d on epoch-verified rows'
      % (len(COR_C1_ONLY), len(COR_C1), len(VER_C1_ONLY), len(VER_C1)))
print('  chain: %d unattributed, %d of them rank-flagged, %d recurring'
      % (len(UNATTR), len(UNATTR_SCREENED), len(CONFIRMED)))
print('  recurrence tested on %d crossings / %d repeat blocks, max T* %.2f'
      % (len(RECUR_ROWS), RECUR_NREP, RECUR_TMAX or float('nan')))
print('  ★ recurrence NOT evaluated for %d rank-flagged unattributed '
      'crossing(s): %s'
      % (len(RECUR_GAP), ', '.join(r['display'] for r in RECUR_GAP)))
print('  false alarm: committed %.2f%% of %d, adopted %.2f%% of %d '
      '(ceiling %.0f%%)' % (100 * FA_COM['rate_full'], FA_COM['n'],
                            100 * FA_COR['rate_full'], FA_COR['n'],
                            100 * FA_CEILING))
print('  %d checks passed' % len(CHECKS))
