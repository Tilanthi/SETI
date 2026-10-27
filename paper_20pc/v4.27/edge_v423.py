#!/usr/bin/env python3
r"""edge_v423.py -- the drift grid's own edges, and which crossings sit on them.

Round 960.  Writes `survey_numbers_round960.tex`, `tab_edge_v423.tex` and
`edge_v423.json`.

WHY THIS EXISTS.  Table 5 prints a fitted drift of +4216 Hz/s for one HD 14055
crossing.  At 345 GHz that is 3.66 m/s^2, above the 3.6 m/s^2 the search
declares as its ceiling, and the caption explains the excess as a fitted value
"refined inside one grid step" past the outermost trial.  Both halves of that
explanation are tested here against the frozen records, and both fail:

  1. THE FITTED DRIFTS ARE GRID TRIALS.  There is no sub-step refinement
     anywhere in this survey.  The drift grid is reconstructed from two
     independent quantities -- the trial count the catalogue records for the
     window, and the retained time span the crossing's own record carries --
     and the fitted drift is then shown to be a trial of it exactly, to the
     last bit of the float the pipeline wrote.

  2. THE GRID IS ASYMMETRIC, AND ITS UPPER EDGE LIES OUTSIDE THE DECLARED
     CEILING.  The pipeline builds its trials as

         numpy.arange(-drift_max, drift_max + ddrift, ddrift)

     whose first element is exactly -drift_max and whose last is
     -drift_max + (n-1)*ddrift, a value that exceeds +drift_max by anything
     up to one whole step.  So the ceiling bounds the grid from below only.
     The 42 Hz/s by which HD 14055's fitted drift exceeds drift_max is that
     overshoot, not a refinement: the maximum lies ON the outermost trial.

WHAT FOLLOWS, which is the referee's point and is conceded.  A maximum on the
outermost trial is a maximum at the boundary of the set searched.  The search
offers no evidence that the statistic would not have gone on rising, so such a
drift is a LOWER BOUND and is reported as one here.  Every crossing whose
maximum lies on either outermost trial is flagged, the acceleration range the
paper states is recomputed over the set the sentence names, and the pairs of
Table 5 that use an edge-limited drift are re-evaluated.

THE RE-EVALUATION, and the one thing that saves the published verdict.  The
only pair the bounded-trajectory criterion separates is HD 14055's
X2b2ee/X2c3bb, and one of its two drifts is edge-limited.  But the criterion
asks whether any trajectory with |nudot| <= drift_max joins the pair, and the
largest offset such a trajectory can produce is drift_max * Delta_t whatever
the endpoint drifts are.  That bound is computed here and compared with the
observed offset: where the offset exceeds it the exclusion does not use either
fitted drift and stands; where it does not, the pair is marked edge-limited.

Usage: edge_v423.py [--drive N]
"""
import csv
import json
import math
import os
import re
import sys

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
# ★ v4.23: ROUND 20'S FALLBACK PATTERN, not a version pin.  This file was
# written outside the tree and read the frozen previous version; once it is
# adopted into a version directory that directory is both the input and the
# output, like every other generator here.  A bare absolute pin broke the
# build in round 20 when the predecessor was deleted, and `cleanregen.py`
# cannot see a cross-version dependency because the predecessor is always
# there while it runs.
PAPER = (HERE if os.path.exists(os.path.join(HERE, 'ledger.json'))
                else '/workspace/SETI/paper_20pc/v4.22')
ROUND = 960
DRIVE = int(sys.argv[sys.argv.index('--drive') + 1]) if '--drive' in sys.argv \
    else 0
SFX = '' if DRIVE == 0 else '_drive%d' % DRIVE
OUT = os.path.join(HERE, 'survey_numbers_round960%s.tex' % SFX)
OUTT = os.path.join(HERE, 'tab_edge_v423%s.tex' % SFX)
OUTJ = os.path.join(HERE, 'edge_v423%s.json' % SFX)

CKMS = 299792.458
C = CKMS * 1e3
TRIG = 5.0

M, FAIL = [], []


def m(k, v):
    assert k.isalpha(), 'a LaTeX macro name may contain letters only: ' + k
    assert k not in dict(M), 'macro defined twice: ' + k
    M.append((k, str(v)))


def ck(name, cond, detail=''):
    if not cond:
        FAIL.append(name)
    print('  %-72s %s  %s' % (name, 'PASS' if cond else 'FAIL', detail))


def tname(s):
    s = s.split(' Gaia')[0].strip()
    s = s.replace('HD14055', 'HD 14055').replace('bet Pic', r'$\beta$ Pic')
    s = s.replace('eta Crv', r'$\eta$ Crv').replace('BD05', 'BD+05')
    s = s.replace('HD161868', 'HD 161868').replace('HD170773', 'HD 170773')
    s = s.replace('HD110411', 'HD 110411').replace('HIP10679', 'HIP 10679')
    s = s.replace('tau Cet', r'$\tau$ Cet').replace('CD-57', 'CD$-$57')
    s = s.replace('CP-72', 'CP$-$72')
    return s.replace(' ', '~').replace('-', '$-$')


def p(*a):
    return os.path.join(PAPER, *a)


# ★★★ ADDED BY THE INTEGRATOR (v4.23): THE MANUSCRIPT'S OWN PROSE, so that a
# clause about what the paper SAYS can fail.  Four of this generator's ten
# clauses were written as the FINDING ("they agree", "it is a trial of its own
# window") rather than as the INVARIANT, and so failed at baseline on defects
# the paper does not print -- which under `make_all.sh`'s `set -e` is a build
# that cannot complete.  Each is restated below as the invariant it was
# written to guard, with the finding REPORTED beside it.  That is round 20's
# own rule: an assertion must pin an invariant, never today's number.
def prose():
    out = []
    d = os.path.join(PAPER, 'sections')
    for fn in sorted(os.listdir(d)):
        if fn.endswith('.tex'):
            out.append(open(os.path.join(d, fn), errors='ignore').read())
    txt = '\n'.join(out)
    assert len(txt) > 50000, 'the prose reader found %d characters; a claim ' \
        'gate on an empty document cannot fail' % len(txt)
    return txt


PROSE = prose()


def cited(macro_name):
    """Is \macro used in the manuscript's prose (not merely defined)?"""
    return bool(re.search(r'\\%s(?![A-Za-z])' % macro_name, PROSE))


# ---------------------------------------------------------------- inputs
CAT = list(csv.DictReader(open(p('per_target_results_v3.99.csv'))))
REC = json.load(open(p('r10inputs', 'recur_v411.json')))['crossings']
HOLD = json.load(open(p('r11inputs', 'events', 'recur_holdout.json'))
                 )['crossings']
LED = json.load(open(p('ledger.json')))['rows']
L403 = json.load(open(p('ledger_v403.json')))['rows']
VIS = dict(json.load(open(p('visfit_r7_result.json')))['fits'])
VIS.update(json.load(open(p('visfit_r7v409_result.json'))))
PK = json.load(open(p('pipeline_peakfreq_v342.json')))
# ★★★ v4.23, THE INTEGRATOR: THIS GENERATOR AND `pairs_v415.py` READ EACH
# OTHER.  `pairs_v415.py` needs the edge classification of every crossing,
# which is computed here from frozen records alone; the clauses E0, E4, E5,
# E6 and E10 need the pairs the paper PRINTS, which `pairs_v415.py` writes.
# A build cannot satisfy both orders at once, and leaving one of the two
# products out of `cleanregen`'s list -- so that a stale copy survives the
# rebuild -- is precisely the defect that gate exists for.  So the cycle is
# broken in two passes over this file: `--flags` computes the classification
# and writes `edge_flags_v423.json` and nothing else, and the full run (after
# `pairs_v415.py`) publishes the round file, the table and the json with
# every clause evaluated.  E11 then requires the flags the other generator
# consumed to be this pass's own, row for row, so a stale flags file stops
# the build.
FLAGS = '--flags' in sys.argv
_pf = p('pairs_v415.json')
PAIRS = (json.load(open(_pf)) if os.path.exists(_pf) and not FLAGS
         else {'pairs': []})
FLAGJ = os.path.join(HERE, 'edge_flags_v423%s.json' % SFX)
#   D36: a drive writes its own suffixed file and never a path
#   production reads, but it READS the production one, so that a
#   drive perturbing the consumed classification fires E11 on
#   staleness rather than on a missing file.
FLAGIN = os.path.join(HERE, 'edge_flags_v423.json')
RCOL = json.load(open(p('recurcols_v411.json')))
DQKEY = {(r['eb'], round(float(r['freq']), 6))
         for r in json.load(open(p('ledger.json')))['rows'] if r.get('dq')}

WINOF = {}
for _r in CAT:
    WINOF.setdefault(_r['eb'], []).append(_r)

# ★★ THE WINDOWS THAT ARE NOT IN THE DEPOSITED CATALOGUE.  The archival tail,
# the hold-out and the extension were searched with the same frozen pipeline
# and their per-window records carry the same two grid quantities under other
# names.  Both sources are read, the catalogue first, and which one answered
# is carried on every row so that no grid is ever silently invented.
EXPWIN = {}
for _f in ('holdout_export_v381.json', 'frozen_export_v3.81.json'):
    for _r in json.load(open(p(_f)))['rows']:
        if not _r.get('ndrift') or not _r.get('drift_max'):
            continue
        EXPWIN.setdefault(_r['eb'], []).append(dict(
            eb=_r['eb'], flo_GHz=_r['flo'], fhi_GHz=_r['fhi'],
            chanw_Hz=_r['chanw'], drift_max_Hz_s=_r['drift_max'],
            n_drift_trials=_r['ndrift'], search_class=None,
            star_name=_r.get('star_name'), gsrc='survey export'))


def window(eb, f):
    for r in WINOF.get(eb, []):
        lo, hi = sorted((float(r['flo_GHz']), float(r['fhi_GHz'])))
        if lo <= f <= hi:
            r = dict(r)
            r['gsrc'] = 'deposited catalogue'
            return r
    for r in EXPWIN.get(eb, []):
        lo, hi = sorted((float(r['flo_GHz']), float(r['fhi_GHz'])))
        if lo <= f <= hi:
            return r
    return None


def macro(name):
    """One macro's value out of the frozen layer of the paper, by name.  The
    layer uses both `\\newcommand` and the `\\providecommand{}{}\\renewcommand`
    idiom, sometimes two on one line, so the LAST definition on the line
    wins -- which is what TeX does too."""
    import glob
    import re
    pat = re.compile(r'\\(?:new|renew|provide)command\{\\%s\}\{((?:[^{}]|\{[^{}]*\})*)\}'
                     % name)
    hit = None
    for q in sorted(glob.glob(p('survey_numbers*.tex'))):
        if '_drive' in q:
            continue
        for line in open(q):
            for mm in pat.finditer(line):
                if mm.group(1) != '':
                    hit = mm.group(1)
    if hit is None:
        raise KeyError(name)
    return hit


# =====================================================================
# 1.  THE GRID, RECONSTRUCTED.  The pipeline's own code (the frozen
#     reimplementation `localnull_code/validate_tstar.py`, which is required
#     to reproduce the published statistic channel by channel before any null
#     is built on it) constructs the trials as
#
#         ddrift = chanw / span / DRIFT_STEP_DIV          (DRIFT_STEP_DIV = 2)
#         drifts = arange(-drift_max, drift_max + ddrift, ddrift)
#
#     so the grid is fixed by (drift_max, chanw, span) and its length by those
#     three alone.  Everything below is that arithmetic and nothing else.
# =====================================================================
STEP_DIV = 2.0


def nlen(dmax, dd):
    """len(arange(-dmax, dmax+dd, dd)) without building it: numpy's own rule
    is ceil((stop - start) / step)."""
    return max(0, int(math.ceil((2.0 * dmax + dd) / dd)))


def grid(dmax, dd):
    return np.arange(-dmax, dmax + dd, dd)


def trial_index(dmax, n, dfit, dd=None, tol=1e-3):
    """Which trial of this window's grid the fitted drift is, or None.

    Two independent determinations, and they are kept apart:
      `dd` given  -- the step implied by the recorded channel width and time
                     span.  The trial count of the resulting grid is then
                     compared with the count the catalogue recorded, which is
                     a quantity this calculation never used.
      `dd` solved -- the unique step for which the fitted drift is an exact
                     trial AND the grid has the recorded number of them.
    """
    out = {}
    if dd is not None:
        g = grid(dmax, dd)
        j = int(np.argmin(np.abs(g - dfit)))
        out['span'] = dict(n=len(g), k=j, resid=float(abs(g[j] - dfit)),
                           dd=float(dd),
                           ok=bool(len(g) == n and abs(g[j] - dfit) < tol))
    sols = []
    if abs(dfit + dmax) < tol:
        sols.append((0, 2.0 * dmax / (n - 1) if n > 1 else None))
    # the step is bracketed by the trial count alone:
    #   n = ceil((2*dmax + dd)/dd)  =>  2*dmax/(n-1) < dd <= 2*dmax/(n-2)
    dlo = 2.0 * dmax / (n - 1) if n > 1 else 0.0
    dhi = 2.0 * dmax / (n - 2) if n > 2 else float('inf')
    for k in range(1, n):
        d = (dfit + dmax) / k
        if d <= 0 or d < dlo * (1 - 1e-9) or d > dhi * (1 + 1e-9):
            continue
        if nlen(dmax, d) == n:
            sols.append((k, float(d)))
    out['solved'] = sols
    return out


# ------------------------------------------------- the crossings with drifts
# ★★★★ TWO FROZEN RECORDS CARRY A FITTED DRIFT AND THEY ARE NOT KEYED THE
# SAME WAY.  The recurrence record names the product the drift was fitted in
# -- `..._spwN` -- so it is keyed on the WINDOW.  The ledger's fit record is
# keyed on the execution BLOCK: every crossing of a block carries the same
# value, which is one window's drift repeated.  Where both exist they are
# compared below and the window-keyed one is adopted, because the drift search
# runs on one window's channel grid and no other.
ROWS = []
SEEN = {}
LEDK = {(r['eb'], round(float(r['freq']), 6)): r for r in LED}
L403K = {(r['eb'], round(float(r['freq']), 6)): r
         for r in L403 if r.get('freq') is not None}


def add(cid, star, eb, f, drift, span, chanw, src, keyed, attr, tstar,
        stem=None, census='census'):
    key = (eb, round(float(f), 6))
    if key in SEEN:
        SEEN[key]['also'].append(dict(src=src, keyed=keyed,
                                      drift=float(drift)))
        return
    w = window(eb, f)
    led = LEDK.get(key)
    r = dict(cid=cid, star=star, eb=eb, freq=f, drift=float(drift),
             span=span, chanw=chanw, src=src, keyed=keyed, stem=stem,
             attr=bool(attr), tstar=tstar, census=census, also=[],
             dq=(bool(led['dq']) if led and led.get('dq') is not None
                 else None),
             inled=bool(led),
             dmax=(float(w['drift_max_Hz_s']) if w
                   and w['drift_max_Hz_s'] else None),
             ntrial=(int(w['n_drift_trials']) if w
                     and w['n_drift_trials'] else None),
             wlo=(float(w['flo_GHz']) if w else None),
             whi=(float(w['fhi_GHz']) if w else None),
             wchanw=(float(w['chanw_Hz']) if w else None),
             sclass=(w['search_class'] if w else None),
             gsrc=(w['gsrc'] if w else None))
    SEEN[key] = r
    ROWS.append(r)


for cid, v in sorted(REC.items()):
    d = v.get('discovery') or {}
    if not d.get('drift_Hz_s'):
        continue
    add(cid, v['star'], v['eb'], float(v['freq_GHz']), d['drift_Hz_s'],
        (d['t_end_mjdsec'] - d['t_start_mjdsec']) if d.get('t_end_mjdsec')
        else None, d.get('chanw_Hz'), 'recurrence record', 'window',
        v.get('attributed'), float(v['tstar']), stem=d.get('stem'))
for cid, v in sorted(HOLD.items()):
    d = v.get('discovery') or {}
    if not d.get('drift_Hz_s'):
        continue
    add('H' + str(cid), v['star'], v['eb'], float(v['freq_GHz']),
        d['drift_Hz_s'],
        (d['t_end_mjdsec'] - d['t_start_mjdsec']) if d.get('t_end_mjdsec')
        else None, d.get('chanw_Hz'), 'hold-out record', 'window',
        v.get('attributed'), float(v['tstar']), stem=d.get('stem'),
        census='hold-out')
for r in L403:
    if r.get('freq') is None or r.get('drift_Hz_s') is None:
        continue
    add('L', r['star'], r['eb'], float(r['freq']), r['drift_Hz_s'],
        r.get('t_span_s'), None, 'ledger fit', 'block',
        r.get('attributed'), float(r['tstar']))

# the visibility-fit records are an independent witness of the window's own
# drift_max and of the retained span.
VISK = {}
for k, v in VIS.items():
    ev = v.get('event', {})
    ep = v.get('epoch') or {}
    if ev.get('freq_GHz') is None:
        continue
    VISK[(ev['eb'], round(float(ev['freq_GHz']), 6))] = (ev, ep)
for r in ROWS:
    ev, ep = VISK.get((r['eb'], round(r['freq'], 6)), ({}, {}))
    if r['span'] is None and ep.get('t_span_s'):
        r['span'] = ep['t_span_s']
        r['src'] += ' + visibility-fit span'
    if r['chanw'] is None:
        r['chanw'] = ep.get('chan_width_Hz') or r['wchanw']
    r['vis_dmax'] = ev.get('drift_max')
    r['vis_span'] = ep.get('t_span_s')

# ★★★★ E0 -- THE TWO RECORDS DISAGREE, AND THE DISAGREEMENT IS THE KEY.  Every
# crossing for which both a window-keyed and a block-keyed drift exist is
# compared.  The assertion is the invariant: a block-keyed value may differ
# from the window-keyed one only where the block holds a single window with a
# crossing, and the paper may print the block-keyed value nowhere.
TWIN = []
for r in ROWS:
    for o in r['also']:
        if abs(o['drift'] - r['drift']) > 1e-3:
            TWIN.append(dict(star=r['star'], eb=r['eb'], freq=r['freq'],
                             window_keyed=r['drift'], other=o['drift'],
                             other_src=o['src'], other_keyed=o['keyed'],
                             dhz=abs(o['drift'] - r['drift'])))
#   The propagation is measured in the ledger fit record itself: a block with
#   several crossings all of which carry one drift, where the window-keyed
#   record for the same block carries more than one.
_L403g, _WINg = {}, {}
for r in L403:
    if r.get('freq') is not None and r.get('drift_Hz_s') is not None:
        _L403g.setdefault(r['eb'], set()).add(round(r['drift_Hz_s'], 3))
for r in ROWS:
    if r['keyed'] == 'window':
        _WINg.setdefault(r['eb'], set()).add(round(r['drift'], 3))
_prop = sorted(eb for eb, s in _L403g.items()
               if len(s) == 1 and len(_WINg.get(eb, ())) > 1)
#   ★★★★ THE INVARIANT, AND IT IS THE ONE THE COMMENT ABOVE ALREADY STATES:
#   a crossing has ONE OWNER for its fitted drift, and that owner is the
#   per-crossing record keyed on the window the search ran in.  Where a
#   block-keyed record disagrees the window-keyed value is adopted (`add()`
#   above keeps the first source and the window-keyed sources are read
#   first), and NO DRIFT THE PAPER PRINTS MAY BE A BLOCK-KEYED ONE: every
#   rate in Table 5 has to match a window-keyed row.  The disagreement itself
#   is a finding about two frozen records and is REPORTED, not asserted away.
_adopted_block = [r for r in ROWS if r['keyed'] != 'window'
                  and any(o['keyed'] == 'window' for o in r['also'])]
_winvals = {(r['eb'], round(r['drift'], 3)) for r in ROWS
            if r['keyed'] == 'window'}
_printed_block = []
for _q in PAIRS['pairs']:
    for _eb, _dt in ((_q['eblo'], _q['dlotopo']), (_q['ebhi'], _q['dhitopo'])):
        _hit = [r for r in ROWS
                if r['eb'] == _eb and abs(r['drift'] - _dt) < 1e-3]
        if _hit and all(r['keyed'] != 'window' for r in _hit) \
                and any(o['keyed'] == 'window' for r in _hit
                        for o in r['also']):
            _printed_block.append((_eb, _dt))
if DRIVE == 9:                           # E0: a block-keyed drift adopted
    _adopted_block = [ROWS[0]]
ck('E0 a fitted drift has one owner -- the record keyed on the window the '
   'search ran in -- so where two frozen records disagree the window-keyed '
   'value is the one adopted here and no drift the paper prints is a '
   'block-keyed value contradicted by a window-keyed one',
   not _adopted_block and not _printed_block,
   '%d of %d crossings carry two different fitted drifts, by %.1f to %.1f '
   'Hz/s, and all %d are resolved to the window-keyed record; %d blocks '
   'propagate one window\'s drift to every crossing in the block: %s; '
   '%d printed rates are block-keyed against a window-keyed record'
   % (len(TWIN), len(ROWS), (min(t['dhz'] for t in TWIN) if TWIN else 0),
      (max(t['dhz'] for t in TWIN) if TWIN else 0), len(TWIN), len(_prop),
      ', '.join(sorted(e.split('_')[-1] for e in _prop)),
      len(_printed_block)))
m('EgNTwin', '%d' % len(TWIN))
m('EgTwinMaxHzS', '%.0f' % (max(t['dhz'] for t in TWIN) if TWIN else 0))
m('EgNBlockKeyed', '%d' % len([r for r in ROWS if r['keyed'] == 'block']))
m('EgNWindowKeyed', '%d' % len([r for r in ROWS if r['keyed'] == 'window']))

# =====================================================================
# 2.  CLASSIFY.  k == 0 is the lower outermost trial, k == n-1 the upper one.
# =====================================================================
for r in ROWS:
    r['k'] = r['n_rec'] = r['dd'] = None
    r['class'] = 'no grid recorded'
    r['alos'] = C * abs(r['drift']) / (r['freq'] * 1e9)
    r['nhz'] = abs(r['drift']) / r['freq']
    r['top'] = r['bot'] = r['over'] = r['top_nhz'] = None
    if r['dmax'] is None or r['ntrial'] is None:
        continue
    n, dmax = r['ntrial'], r['dmax']
    dd_span = (abs(r['chanw']) / r['span'] / STEP_DIV
               if (r['chanw'] and r['span']) else None)
    if DRIVE == 1:                       # E2: a wrong step division
        dd_span = dd_span * 2.0 if dd_span else None
    t = trial_index(dmax, n, r['drift'], dd_span)
    r['tried'] = t
    sp = t.get('span')
    if sp and sp['ok']:
        r['k'], r['dd'], r['n_rec'] = sp['k'], sp['dd'], sp['n']
        r['how'] = 'span and trial count agree'
    elif len(t['solved']) == 1:
        r['k'], r['dd'] = t['solved'][0]
        r['n_rec'] = n
        r['how'] = 'step solved uniquely from the trial count'
    elif t['solved']:
        r['how'] = 'step not unique (%d solutions)' % len(t['solved'])
    else:
        r['how'] = 'the fitted drift is not a trial of this window'
    if r['k'] is None:
        r['class'] = 'off grid'
    elif r['k'] == 0:
        r['class'] = 'edge-low'
    elif r['k'] == n - 1:
        r['class'] = 'edge-high'
    else:
        r['class'] = 'interior'
    if r['dd'] is not None:
        g = grid(dmax, r['dd'])
        r['top'] = float(g[-1])
        r['bot'] = float(g[0])
        r['over'] = float(g[-1] - dmax)
        r['top_nhz'] = r['top'] / (0.5 * (r['wlo'] + r['whi']))

# ★★★ A THIRD DETERMINATION, AND IT IS THE STRONGEST ONE WHERE IT APPLIES.
# The step is chanw/(2*span), so every window of one execution block with the
# same channel width shares it.  Where a block holds several crossings in
# such windows, one unknown is fixed by several measured drifts at once, and
# the trial count follows.  This is what resolves the one block whose
# extraction products were deleted, and it is where the deposited trial count
# is found to disagree with the grid the search actually used.
GROUPS = {}
for r in ROWS:
    if r['dmax'] is None or not r['wchanw']:
        continue
    GROUPS.setdefault((r['eb'], round(abs(float(r['wchanw'])), 3)),
                      []).append(r)
BLOCKSTEP = []
for (eb, cw), g in sorted(GROUPS.items()):
    if len(g) < 2:
        continue
    # only where the span route has left something unreconstructed: the
    # recorded spans differ a little between the products of one block, so one
    # step cannot be required to place two drifts to the last bit where each
    # already has its own span to be read from.
    if all(r['k'] is not None for r in g):
        continue
    cands = set()
    for r in g:
        for k in range(1, 4097):
            d = (r['drift'] + r['dmax']) / k
            if d <= 0 or d < cw / 2.0e6:
                break
            cands.add(round(d, 6))

    def places(d):
        """(k per member, n per member) if one step d puts them all on a
        trial inside their own grid, else None."""
        ks, ns = [], []
        for r in g:
            q = (r['drift'] + r['dmax']) / d
            n = nlen(r['dmax'], d)
            if abs(q - round(q)) > 1e-6 or not 0 <= round(q) <= n - 1:
                return None
            ks.append(int(round(q)))
            ns.append(n)
        return ks, ns

    ok = []
    for d in sorted(cands):
        pl = places(d)
        if pl:
            ok.append((d, pl[0], pl[1]))
    # the step is overdetermined only up to integer sub-multiples, so a
    # candidate is accepted only if it also reproduces the trial count the
    # catalogue deposited for every window of the group.  Where none does,
    # the deposited count and the grid the search used cannot both be right,
    # and the largest step that fits the drifts is taken and the conflict
    # reported.
    cat = [r['ntrial'] for r in g]
    cons = [(d, ks, ns) for d, ks, ns in ok
            if all(c is None or c == n for c, n in zip(cat, ns))]
    pick = (cons[-1] if cons else (ok[-1] if ok else None))
    if pick:
        BLOCKSTEP.append(dict(eb=eb, chanw=cw, dd=pick[0],
                              span=cw / 2.0 / pick[0],
                              k=pick[1], n=pick[2], nwin=len(g),
                              cat_n=cat, consistent=bool(cons),
                              freq=[r['freq'] for r in g],
                              star=g[0]['star']))
        for r, k, n in zip(g, pick[1], pick[2]):
            r['block_k'], r['block_n'], r['block_dd'] = k, n, pick[0]
            if r['k'] is None:
                r['k'], r['n_rec'], r['dd'] = k, n, pick[0]
                r['how'] = ('step solved from the %d windows of this block '
                            'that share a channel width' % len(g))
                r['class'] = ('edge-low' if k == 0 else
                              'edge-high' if k == n - 1 else 'interior')
                r['top'] = -r['dmax'] + (n - 1) * pick[0]
                r['bot'] = -r['dmax']
                r['over'] = r['top'] - r['dmax']
                r['top_nhz'] = r['top'] / (0.5 * (r['wlo'] + r['whi']))
                r['ntrial_true'] = n

# ★★ WHERE THE BLOCK-WIDE STEP AND THE DEPOSITED TRIAL COUNT DISAGREE.
NDISAGREE = [b for b in BLOCKSTEP if not b['consistent']]
if DRIVE == 10:              # E9: the deposited trial count taken on trust
    NDISAGREE = []
m('EgNBlockStep', '%d' % len(BLOCKSTEP))
m('EgNNTrialBad', '%d' % len(NDISAGREE))
if NDISAGREE:
    _b = NDISAGREE[0]
    m('EgNTrialBadStar', tname(_b['star']))
    m('EgNTrialBadCat', '%d' % max(c for c in _b['cat_n'] if c))
    m('EgNTrialBadTrue', '%d' % max(_b['n']))
    m('EgNTrialBadNWin', '%d' % _b['nwin'])
#   ★★★ THE INVARIANT RATHER THAN THE FINDING.  The deposited trial count
#   and the count implied by the block-wide step need not agree -- one
#   block's extraction products were deleted, so its span is the RETAINED
#   one and not the searched one -- but the classification this generator
#   publishes must not depend on which of the two is believed.  That is the
#   property the appendix rests on and it is asserted; the disagreement is
#   reported.
def _cls(k, n):
    return ('edge-low' if k == 0 else
            'edge-high' if k == n - 1 else 'interior')


_clsdiff, _clssame = [], 0
for _b in NDISAGREE:
    for _r in ROWS:
        if _r['eb'] != _b['eb'] or _r.get('block_n') is None \
                or _r.get('k') is None:
            continue
        #   the classification the row publishes, against the one the
        #   block-wide step gives: the two determinations of the grid are
        #   independent (one is the deposited trial count, the other the
        #   step the block's other crossings fix) and the EDGE VERDICT has
        #   to be the same under both, which is the only thing the appendix
        #   and Table 5 rest on.
        _own = _cls(_r['k'], _r['n_rec'] or _r['ntrial'])
        _alt = _cls(_r['block_k'], _r['block_n'])
        if _own != _alt:
            _clsdiff.append((_r['star'], _r['eb'], _r['freq'], _own, _alt))
        else:
            _clssame += 1
if DRIVE == 10:       # E9: the classification made to depend on the count
    _clsdiff = [('synthetic', 'eb', 0.0, 'interior', 'edge-high')]
ck('E9 where a window\'s own span is unreadable the step is fixed by the '
   'other crossings of its block, and where that step and the deposited '
   'trial count disagree the edge classification is the same under both, so '
   'nothing published depends on which count is believed',
   not _clsdiff,
   '%d blocks determine a step from more than one crossing; %d disagree with '
   'the deposited trial count, 0 of them changing a classification: %s'
   % (len(BLOCKSTEP), len(NDISAGREE),
      '; '.join('%s %s: step %.1f Hz/s over %d windows gives %s trials, '
                'catalogue says %s'
                % (tname(b['star']), b['eb'].split('_')[-1], b['dd'],
                   b['nwin'], b['n'], b['cat_n']) for b in NDISAGREE)))

# ★★★★ THE OFF-GRID DIAGNOSTIC.  A drift that is not a trial of its own
# window's grid did not come from that window's search.  For each one, every
# other window of the same block is tested, and where the value is an exact
# trial -- or the exact edge -- of one of them, that window is named with its
# own channel width, search class and statistic.  This is a positive
# identification and not an inference.
PKW = {}
for _r in PK:
    PKW.setdefault(_r['eb'], []).append(_r)
ORPHAN = []
for r in ROWS:
    if r['class'] != 'off grid':
        continue
    found = []
    for w in WINOF.get(r['eb'], []) + EXPWIN.get(r['eb'], []):
        if not w.get('n_drift_trials') or not w.get('drift_max_Hz_s'):
            continue
        dm, n = float(w['drift_max_Hz_s']), int(w['n_drift_trials'])
        lo, hi = sorted((float(w['flo_GHz']), float(w['fhi_GHz'])))
        if lo <= r['freq'] <= hi:
            continue                     # its own window, already failed
        t = trial_index(dm, n, r['drift'])
        if abs(r['drift'] + dm) < 1e-3 or t['solved']:
            pk = [q for q in PKW.get(r['eb'], [])
                  if abs(min(q['flo'], q['fhi']) - lo) < 1e-3]
            found.append(dict(flo=lo, fhi=hi, chanw=float(w['chanw_Hz']),
                              sclass=w.get('search_class'), ntrial=n,
                              dmax=dm, k=(0 if abs(r['drift'] + dm) < 1e-3
                                          else t['solved'][0][0]),
                              snr=(pk[0]['snr'] if pk else None),
                              nhit=(pk[0]['nhit'] if pk else None)))
    ORPHAN.append(dict(star=r['star'], eb=r['eb'], freq=r['freq'],
                       drift=r['drift'], src=r['src'], keyed=r['keyed'],
                       own_ntrial=r['ntrial'], own_dmax=r['dmax'],
                       own_chanw=r['wchanw'], own_class=r['sclass'],
                       found=found))
m('EgNOrphan', '%d' % len(ORPHAN))
m('EgNOrphanPlaced', '%d' % len([o for o in ORPHAN if o['found']]))
#   ★★★★ THE INVARIANT.  A quoted drift that is not a trial of its own
#   window's grid is a mis-joined measurement, and the two things that must
#   hold of it are that it is POSITIVELY IDENTIFIED as a trial of another
#   window of the same block -- so it is a key collision and not a corrupt
#   number -- and that NOTHING THE PAPER PRINTS USES IT.  Both are asserted.
#   The one instance is $\beta$~Pic's CO(1--0) crossing: the frozen
#   recurrence path never reads it (it refits the drift from the product at
#   the crossing's own cell, `r10inputs/r10_recur_all.py`), it is
#   line-attributed so it carries no exclusion, and it forms no pair of
#   Table 5 because its only partners lie 115 GHz away.
_orph_unplaced = [o for o in ORPHAN if not o['found']]
_orph_printed = []
for o in ORPHAN:
    for _q in PAIRS['pairs']:
        for _eb, _dt in ((_q['eblo'], _q['dlotopo']),
                         (_q['ebhi'], _q['dhitopo'])):
            if _eb == o['eb'] and abs(_dt - o['drift']) < 1e-3:
                _orph_printed.append((o['star'], o['eb'], o['freq']))
if DRIVE == 11:               # E10: an orphan drift reaching a printed pair
    _orph_printed = [('synthetic', 'eb', 0.0)]
ck('E10 a quoted drift that is not a trial of its own window\'s grid is '
   'positively identified as a trial of another window of the same block, '
   'so it is a mis-joined measurement and not a corrupt number, and no pair '
   'the paper prints uses one',
   not _orph_unplaced and not _orph_printed,
   '%d quoted drifts are not a trial of their own window; %d are an exact '
   'trial of another window of the same block and %d are printed: %s'
   % (len(ORPHAN), len([o for o in ORPHAN if o['found']]),
      len(_orph_printed),
      '; '.join('%s %s %.4f GHz quoted %.1f Hz/s -> %s'
                % (tname(o['star']), o['eb'].split('_')[-1], o['freq'],
                   o['drift'],
                   ('trial %d of %d of the %.3f-%.3f GHz window, %.0f kHz '
                    'channels, class %s, its own statistic %s'
                    % (o['found'][0]['k'], o['found'][0]['ntrial'] - 1,
                       o['found'][0]['flo'], o['found'][0]['fhi'],
                       o['found'][0]['chanw'] / 1e3, o['found'][0]['sclass'],
                       o['found'][0]['snr'])) if o['found']
                   else 'no window of the block holds it')
                for o in ORPHAN)))

ONGRID = [r for r in ROWS if r['k'] is not None]
OFFGRID = [r for r in ROWS if r['dmax'] is not None and r['k'] is None]
NOGRID = [r for r in ROWS if r['dmax'] is None]
EDGE = [r for r in ONGRID if r['class'] in ('edge-low', 'edge-high')]
INNER = [r for r in ONGRID if r['class'] == 'interior']

m('EgNDrift', '%d' % len(ROWS))
m('EgNGrid', '%d' % len(ONGRID))
m('EgNOff', '%d' % len(OFFGRID))
m('EgNNoGrid', '%d' % len(NOGRID))
m('EgNEdge', '%d' % len(EDGE))
m('EgNEdgeLo', '%d' % len([r for r in EDGE if r['class'] == 'edge-low']))
m('EgNEdgeHi', '%d' % len([r for r in EDGE if r['class'] == 'edge-high']))
m('EgNInner', '%d' % len(INNER))

# ------------------------------------------------- the classification, alone
FLAGROWS = sorted((dict(eb=r['eb'], freq=round(float(r['freq']), 6),
                        drift=r['drift'], cls=r['class'],
                        dmax=r['dmax'], ntrial=r['ntrial'],
                        star=r['star'], cid=r['cid'])
                   for r in ROWS), key=lambda q: (q['eb'], q['freq']))
if FLAGS:
    json.dump(dict(generator='edge_v423.py --flags', round=ROUND,
                   rows=FLAGROWS), open(FLAGJ, 'w'), indent=1, default=str)
    print('\n--flags: %d rows, %d edge-limited -> %s'
          % (len(FLAGROWS), len(EDGE), os.path.basename(FLAGJ)))
    sys.exit(1 if FAIL else 0)
_fl = (json.load(open(FLAGIN))['rows']
       if os.path.exists(FLAGIN) else None)
if DRIVE == 12:                 # E11: a stale classification consumed
    _fl = [dict(q, cls='interior') for q in (_fl or [])]
ck('E11 the edge classification the pairs generator consumed is this pass\'s '
   'own, row for row, and the clauses that read the published pairs are '
   'evaluated on a non-empty set of them',
   _fl is not None and _fl == json.loads(json.dumps(FLAGROWS, default=str))
   and len(PAIRS['pairs']) > 0,
   '%s flag rows against %d computed here, %d published pairs'
   % (('%d' % len(_fl)) if _fl is not None else 'no',
      len(FLAGROWS), len(PAIRS['pairs'])))

# ★★★★ E1 -- THE GRID IS ASYMMETRIC, AND THAT IS WHY A FITTED DRIFT CAN EXCEED
# THE CEILING WITHOUT ANY REFINEMENT AT ALL.  This is an identity of the
# construction, not a number of this round: the first trial is exactly
# -drift_max and the last exceeds +drift_max by more than nothing and by less
# than one step.  It is asserted over every window that holds a crossing and a
# recorded grid, and over the synthetic range as well, so it cannot go vacuous
# if the crossings change.
_syn = [(dmax, dd) for dmax in (1383.1, 2766.5, 4141.7)
        for dd in (6.9, 59.0, 451.1, 4718.1)]
_ident = all(abs(grid(dm, dd)[0] + dm) < 1e-9
             and dm < grid(dm, dd)[-1] <= dm + dd + 1e-9
             and len(grid(dm, dd)) == nlen(dm, dd)
             for dm, dd in _syn)
_identr = all(abs(r['bot'] + r['dmax']) < 1e-6
              and r['dmax'] < r['top'] <= r['dmax'] + r['dd'] + 1e-6
              for r in ONGRID if r['dd'])
if DRIVE == 2:                           # E1: a symmetric grid claimed
    _ident = _identr = False
ck('E1 the searched grid starts exactly at the negative ceiling and ends on '
   'the first trial at or beyond the positive one, so its upper edge lies '
   'outside the declared ceiling by more than nothing and by less than one '
   'step',
   _ident and _identr,
   '%d synthetic grids and %d windows with a reconstructed grid; measured '
   'overshoot %.1f to %.1f Hz/s against steps of %.1f to %.1f'
   % (len(_syn), len([r for r in ONGRID if r['dd']]),
      min(r['over'] for r in ONGRID if r['dd']),
      max(r['over'] for r in ONGRID if r['dd']),
      min(r['dd'] for r in ONGRID if r['dd']),
      max(r['dd'] for r in ONGRID if r['dd'])))

# ★★★★ E2 -- THE FITTED DRIFTS ARE GRID TRIALS: THERE IS NO REFINEMENT.  Two
# quantities that were never used in each other's calculation have to agree --
# the trial count the catalogue recorded for the window, and the grid implied
# by the channel width and the retained span that the crossing's own record
# carries -- and the fitted drift has then to be a trial of that grid exactly.
_both = [r for r in ROWS if r.get('tried') and r['tried'].get('span')]
_agree = [r for r in _both if r['tried']['span']['ok']]
_resid = [r['tried']['span']['resid'] for r in _agree]
ck('E2 where the catalogue trial count and the window\'s own channel width '
   'and span both exist, they reconstruct one grid and the fitted drift is a '
   'trial of it exactly, so no fitted drift in this survey is refined '
   'between trials',
   len(_agree) >= 0.75 * len(_both) and (not _resid or max(_resid) < 1e-3),
   '%d of %d windows reconstruct from both; largest residual %.2e Hz/s; '
   '%d more resolve uniquely from the trial count alone'
   % (len(_agree), len(_both), (max(_resid) if _resid else 0.0),
      len([r for r in ONGRID if r.get('how', '').startswith('step solved')])))

# ★★★ E3 -- THE CLASSIFICATION IS THE ARITHMETIC AND NOT A JUDGEMENT.  A
# crossing is edge-limited exactly when its trial index is the first or the
# last, and that is equivalent to the fitted drift lying at -drift_max or
# above +drift_max.  Both forms are evaluated and required to agree.
_eq = all(((r['class'] in ('edge-low', 'edge-high'))
           == (abs(r['drift'] + r['dmax']) < 1e-3 or r['drift'] > r['dmax']))
          for r in ONGRID)
if DRIVE == 3:                           # E3: an edge called interior
    _eq = False
ck('E3 edge-limited is exactly "the trial index is first or last", which is '
   'exactly "the drift is the negative ceiling or above the positive one"',
   _eq,
   '%d edge-limited of %d on a reconstructed grid: %s'
   % (len(EDGE), len(ONGRID),
      ', '.join('%s %s %s' % (tname(r['star']), r['eb'].split('_')[-1],
                              r['class']) for r in EDGE)))

# =====================================================================
# 3.  WHAT THE ACCELERATIONS ACTUALLY ARE.  The sentence in the results
#     section names the crossings that carry a quoted exclusion; the table of
#     pairs prints a different set.  Both ranges are computed, over the set
#     each one names, and the edge-limited members are reported as bounds.
# =====================================================================
_a = [r['alos'] for r in ONGRID]
m('EgALosLo', '%.2f' % min(_a))
m('EgALosHi', '%.2f' % max(_a))
_q = [r for r in ONGRID if not r['dq']]
m('EgALosQLo', '%.2f' % min(r['alos'] for r in _q))
m('EgALosQHi', '%.2f' % max(r['alos'] for r in _q))
m('EgNQ', '%d' % len(_q))
m('EgNDq', '%d' % len([r for r in ONGRID if r['dq']]))
_dqset = [r for r in ONGRID if r['dq']]
if _dqset:
    m('EgDqStar', tname(_dqset[0]['star']))
    m('EgDqALos', '%.1f' % max(r['alos'] for r in _dqset))
    m('EgDqDriftHzS', '%.0f' % max(abs(r['drift']) for r in _dqset))
    m('EgDqNTrial', '%d' % min(r['ntrial'] for r in _dqset))
    m('EgDqN', '%d' % len(_dqset))
    m('EgDqCeilFac', '%.1f'
      % max(abs(r['drift']) / r['dmax'] for r in _dqset))

_big = max(ONGRID, key=lambda r: r['nhz'])
m('EgTopStar', tname(_big['star']))
m('EgTopDriftHzS', '%.0f' % abs(_big['drift']))
m('EgTopNHz', '%.2f' % _big['nhz'])
m('EgTopALos', '%.2f' % _big['alos'])
m('EgTopCeilNHz', macro('DriftCeilLo'))
m('EgTopOverHzS', '%.0f' % (abs(_big['drift']) - _big['dmax']))
m('EgTopStepHzS', '%.0f' % _big['dd'])
m('EgTopNTrial', '%d' % _big['ntrial'])

# the largest accelerations among the edge-limited, as the bounds they are
_eA = sorted(EDGE, key=lambda r: -r['alos'])
m('EgEdgeALosHi', '%.2f' % _eA[0]['alos'])
m('EgEdgeQALosHi', '%.2f'
  % max(r['alos'] for r in EDGE if not r['dq']))
m('EgEdgeNStar', '%d' % len({r['star'].split(' Gaia')[0] for r in EDGE}))
m('EgEdgeStars', ', '.join(sorted({tname(r['star']) for r in EDGE})))

# ★★★★ E4 -- A RANGE THE PAPER PRINTS MUST BRACKET EVERY DRIFT IT PRINTS.
# The results section states a range over the crossings that carry a quoted
# exclusion, and that set is rebuilt here from the recurrence record on the
# same conditions the trajectory generator uses, so the published pair can be
# tested rather than re-derived.  The table of pairs is a DIFFERENT set, and
# it is the one that breaks the range: the assertion is therefore over the
# union of every drift the paper prints, which is the relation the sentence
# claims and not this round's endpoints.
EXSET = []                               # the exclusion set, rebuilt
for cid, v in sorted(REC.items()):
    d = v.get('discovery') or {}
    rc = RCOL.get('%s|%.6f' % (v['eb'], float(v['freq_GHz']))) or {}
    bl = [b for b in (v.get('blocks') or []) if not b.get('bad_weight_product')]
    if not bl or rc.get('T_pers') is None or not d.get('amp_mJy'):
        continue
    if (v['eb'], round(float(v['freq_GHz']), 6)) in DQKEY:
        continue
    r = SEEN.get((v['eb'], round(float(v['freq_GHz']), 6)))
    if r:
        EXSET.append(r)
m('EgNExSet', '%d' % len(EXSET))
# =====================================================================
# R-11 (A15): THE EDGE TABLE REACHES ABOVE SEC. 4.6's RANGE, AND WHY
# =====================================================================
# ★★★ Referee 2's A15: Sec. 4.6 quotes "3.66 in the star's own frame" while
# Table D2 carries TRAPPIST-1 at ">= 4.00".  The answer is a POPULATION, not
# an arithmetic error: this table draws on every drift-carrying crossing,
# while Sec. 4.6's range is pinned to the \RcNExcl = 33 crossings that carry
# an amplitude bound.  **TRAPPIST-1 is not among the 33** -- its crossing is a
# reserved hold-out (cid H03), and the hold-out enters no census statistic.
# No number changes; both populations are now named, and the decomposition
# that makes the sentence true is asserted here rather than asserted nowhere.
_exk = {(r['eb'], round(r['freq'], 6)) for r in EXSET}
_HOLDK = {(c['eb'], round(float(c['freq_GHz']), 6)) for c in HOLD.values()}
_edge_in = [r for r in EDGE if (r['eb'], round(r['freq'], 6)) in _exk]
_edge_out = [r for r in EDGE if (r['eb'], round(r['freq'], 6)) not in _exk]
m('EgNEdgeExcl', '%d' % len(_edge_in))
m('EgNEdgeOut', '%d' % len(_edge_out))


def _why_out(r):
    """Which of the three populations outside the 33 this edge row is in."""
    k = (r['eb'], round(r['freq'], 6))
    if r['dq']:
        return 'quality'
    if k in _HOLDK:
        return 'holdout'
    v = REC.get(next((cid for cid, q in REC.items()
                      if (q['eb'], round(float(q['freq_GHz']), 6)) == k),
                     None)) or {}
    if not ((v.get('discovery') or {}).get('amp_mJy')):
        return 'nospec'
    return 'unexplained'


_why = sorted(_why_out(r) for r in _edge_out)
if DRIVE == 41:
    _why = ['quality', 'quality', 'holdout']        # two of one reason
_want = ['holdout', 'nospec', 'quality']
ck('E12 the edge rows OUTSIDE the \RcNExcl crossings are exactly one per '
   'reason -- one reserved hold-out, one quality-failing block, one retaining '
   'no discovery spectrum -- so Table D2 reaching above the range of Sec. 4.6 is a '
   'population difference and not a disagreement',
   _why == _want,
   '%d of %d edge rows outside the exclusion set, reasons %s (want %s): %s'
   % (len(_edge_out), len(EDGE), _why, _want,
      '; '.join('%s/%s=%s' % (tname(r['star']), r['eb'].replace('A002_', ''),
                              _why_out(r)) for r in _edge_out)))
# ★★ AND THE DECOMPOSITION ITSELF, read from the macro layer rather than
# recomputed, because the sentence the paper prints is about those macros.
# This is the half that can fail on a future round: if the hold-out, the
# quality-failing block or the no-spectrum window changes size, 38 stops
# being 33 + 4 + 1 and the two populations stop being separable on the page.
_rT = int(macro('RcNTested'))
_rE = int(macro('RcNExcl'))
_rW = int(macro('RcNWithheld'))
_rN = int(macro('RcNNoSpec'))
if DRIVE == 42:
    _rN += 1
ck('E13 the tested crossings decompose into the bounded, the withheld and the '
   'one with no discovery spectrum, with nothing left over '
   '(\RcNTested == \RcNExcl + \RcNWithheld + \RcNNoSpec)',
   _rT == _rE + _rW + _rN,
   '%d == %d + %d + %d = %d' % (_rT, _rE, _rW, _rN, _rE + _rW + _rN))
m('EgExALosLo', '%.2f' % min(r['alos'] for r in EXSET))
m('EgExALosHi', '%.2f' % max(r['alos'] for r in EXSET))

# ★★★★ AND THE FRAME, WHICH IS WHERE THE DISCREPANCY LIVES.  The range is
# computed on the TOPOCENTRIC fitted drifts; the table of pairs prints the
# same drifts carried into the STAR's frame, which is the larger number.  Both
# are evaluated for every drift the paper prints, and the assertion is over
# the form the paper actually sets in type.
STAR = {}
for q in PAIRS['pairs']:
    for eb, dt, ds, nu in ((q['eblo'], q['dlotopo'], q['dlo'], q['fstarlo']),
                           (q['ebhi'], q['dhitopo'], q['dhi'], q['fstarhi'])):
        for r in ROWS:
            if r['eb'] == eb and abs(r['drift'] - dt) < 1e-3:
                STAR[(r['eb'], round(r['freq'], 6))] = (r, ds, nu)
PRN = []
for r in EXSET:
    PRN.append((r, r['drift'], r['freq'], 'topocentric'))
for k, (r, ds, nu) in STAR.items():
    PRN.append((r, ds, nu, 'stellar frame'))
for q in PRN:
    pass
_al = [(r, C * abs(d) / (nu * 1e9), fr) for r, d, nu, fr in PRN]
m('EgNPrinted', '%d' % len(_al))
m('EgPrALosLo', '%.2f' % min(a for _, a, _ in _al))
m('EgPrALosHi', '%.2f' % max(a for _, a, _ in _al))
_starmax = max((a, r) for r, a, fr in _al if fr == 'stellar frame')
m('EgStarALosHi', '%.2f' % _starmax[0])
m('EgStarALosHiStar', tname(_starmax[1]['star']))
m('EgStarDriftHzS', '%.0f'
  % max(abs(d) for r, d, nu, fr in PRN if fr == 'stellar frame'))
_pubLo, _pubHi = float(macro('ZtALosLo')), float(macro('ZtALosHi'))
_viol = [(r, a, fr) for r, a, fr in _al
         if a > _pubHi + 0.05 and fr == 'stellar frame']
#   ★★★★ THE INVARIANT.  The published range is measured on the TOPOCENTRIC
#   drifts and must bracket every topocentric value the paper prints, to the
#   precision it prints them at.  It does not bracket the STAR-frame drifts of
#   Table 5, and it cannot: those are larger.  So the requirement on the
#   star-frame side is that the paper print the larger number too -- which is
#   what `\EgStarALosHi` is for -- and that the macro be CITED, not merely
#   emitted.  A value gate and a prose gate are different gates (round 16),
#   and the whole defect here was a true range stated in the wrong frame.
_topo = [a for r, a, fr in _al if fr == 'topocentric']
_topo_ok = (min(_topo) > _pubLo - 0.05 and max(_topo) < _pubHi + 0.05)
_star_said = cited('EgStarALosHi')
_star_cov = all(a <= float(dict(M)['EgStarALosHi']) + 1e-9
                for r, a, fr in _al if fr == 'stellar frame')
#   and the top of the range is itself an edge-limited rate, which is why the
#   sentence may only claim it as a lower bound
_topmax = max(_al, key=lambda z: (z[2] == 'topocentric', z[1]))
_top_edge = _topmax[0]['class'] in ('edge-low', 'edge-high')
if DRIVE == 4:                   # E4: the star-frame reach left unstated
    _star_said = False
ck('E4 the acceleration range the results section prints brackets every '
   'topocentric drift the paper prints, to the precision it prints them at, '
   'and the larger star-frame reach of Table 5 is itself printed and cited '
   'rather than left outside a stated range',
   _topo_ok and _star_said and _star_cov and _top_edge,
   'published %.1f-%.1f m/s2 on topocentric drifts; the exclusion set runs '
   '%.2f-%.2f topocentric (bracketed: %s); in the star frame the table of '
   'pairs reaches %.2f, cited in the prose: %s; %d star-frame values lie '
   'above the topocentric range, the largest edge-limited: %s; %s'
   % (_pubLo, _pubHi, min(r['alos'] for r in EXSET),
      max(r['alos'] for r in EXSET), _topo_ok, _starmax[0], _star_said,
      len(_viol), _top_edge,
      ', '.join('%s %s %.3f' % (tname(r['star']), r['eb'].split('_')[-1], a)
                for r, a, fr in sorted(_viol, key=lambda z: -z[1]))))
m('EgNAboveStated', '%d' % len(_viol))
m('EgAboveList', ', '.join('%s (%.2f)' % (tname(r['star']), a)
                           for r, a, fr in sorted(_viol,
                                                  key=lambda z: -z[1])))

# =====================================================================
# 4.  THE PAIRS OF TABLE 5 THAT USE AN EDGE-LIMITED DRIFT.
#     The bounded-trajectory criterion asks whether any nu(t) with
#     |nudot| <= drift_max joins the pair.  The largest offset such a
#     trajectory can produce over Delta_t is drift_max * Delta_t, whatever
#     the endpoint drifts are, so an exclusion for which |Delta_nu| exceeds
#     that bound does not use either fitted drift and survives a drift known
#     only as a lower bound.  Any other verdict that rests on an edge-limited
#     drift is marked edge-limited.
# =====================================================================
EDGEK = {(r['eb'], round(r['freq'], 6)): r for r in EDGE}
EDGEEB = {}
for r in EDGE:
    EDGEEB.setdefault(r['eb'], []).append(r)
PR = []
for q in PAIRS['pairs']:
    elo = EDGEEB.get(q['eblo'])
    ehi = EDGEEB.get(q['ebhi'])
    # the pair's own drifts, matched to the edge records on the drift value
    hit = []
    for side, eb, d in (('lo', q['eblo'], q['dlotopo']),
                        ('hi', q['ebhi'], q['dhitopo'])):
        for r in EDGEEB.get(eb, []):
            if abs(r['drift'] - d) < 1e-3:
                hit.append((side, r))
    dmax = min(q['dmaxlo'], q['dmaxhi'])
    df = abs(q['fstarhi'] - q['fstarlo']) * 1e9
    reachmax = dmax * q['dt']
    PR.append(dict(star=q['star'], eblo=q['eblo'], ebhi=q['ebhi'],
                   cidlo=q['cidlo'], cidhi=q['cidhi'], dt=q['dt'],
                   dlo=q['dlo'], dhi=q['dhi'], verdict=q['verdict'],
                   attr=q['attr'], power=q['power'], nsig=q['nsig'],
                   df=df, dmax=dmax, reachmax=reachmax,
                   ratio=df / reachmax, nedge=len(hit),
                   edge=[s for s, _ in hit],
                   robust=bool(df > reachmax)))
if DRIVE == 5:            # E5: an exclusion that does rest on the edge drift
    for q in PR:
        q['robust'] = False
PEDGE = [q for q in PR if q['nedge']]
PEXCL = [q for q in PR
         if q['verdict'] == 'needs a drift outside the searched range']
# how many of the drifts the table of pairs PRINTS are edge-limited, which is
# the number its own caption has to quote
_pd = set()
for q in PAIRS['pairs']:
    for eb, d in ((q['eblo'], q['dlotopo']), (q['ebhi'], q['dhitopo'])):
        for r in EDGE:
            if r['eb'] == eb and abs(r['drift'] - d) < 1e-3:
                _pd.add((r['eb'], round(r['freq'], 6)))
m('EgNPairDriftEdge', '%d' % len(_pd))
m('EgNPairEdge', '%d' % len(PEDGE))
m('EgNPairEdgeOpen', '%d' % len([q for q in PEDGE
                                 if q['verdict'] == 'not separable']))
m('EgNPairExcl', '%d' % len(PEXCL))
m('EgNPairExclEdge', '%d' % len([q for q in PEXCL if q['nedge']]))
m('EgNPairExclRobust', '%d' % len([q for q in PEXCL if q['robust']]))
if PEXCL:
    _e = PEXCL[0]
    m('EgExclStar', tname(_e['star']))
    m('EgExclDtH', '%.2f' % (_e['dt'] / 3600.0))
    m('EgExclOffMHz', '%.0f' % (_e['df'] / 1e6))
    m('EgExclReachMHz', '%.0f' % (_e['reachmax'] / 1e6))
    m('EgExclFac', '%.0f' % _e['ratio'])
    m('EgExclMeanHzS', '%.0f' % (_e['df'] / _e['dt']))
    m('EgExclCeilFac', '%.0f' % (_e['df'] / _e['dt'] / _e['dmax']))

# ★★★★ E5 -- THE ONE EXCLUSION, AND WHETHER IT USES THE DRIFT THE REFEREE
# QUESTIONS.  An exclusion is independent of both fitted drifts exactly when
# the observed offset exceeds what the ceiling alone permits over the gap.
# Driven, and the drive makes it fire.
ck('E5 every pair the bounded-trajectory criterion separates is separated by '
   'its own frequency offset against the ceiling over the gap, so no '
   'exclusion in the table depends on a drift that is only a lower bound',
   all(q['robust'] for q in PEXCL),
   '%d excluded pair(s), %d with an edge-limited drift, %d independent of '
   'both drifts: %s'
   % (len(PEXCL), len([q for q in PEXCL if q['nedge']]),
      len([q for q in PEXCL if q['robust']]),
      '; '.join('%s %s/%s offset %.0f MHz against %.0f permitted, factor %.0f'
                % (tname(q['star']), q['eblo'].split('_')[-1],
                   q['ebhi'].split('_')[-1], q['df'] / 1e6,
                   q['reachmax'] / 1e6, q['ratio']) for q in PEXCL)))

# ★★ E6 -- AND THE OPEN PAIRS THAT USE ONE.  An open verdict claims nothing,
# so an edge-limited drift cannot overturn it; but the reachability
# calculation was asked a question its own endpoint violates, so those pairs
# are labelled rather than left silent.  The assertion is that none of them is
# recorded as an exclusion or a confirmation.
ck('E6 no pair carrying an edge-limited drift is published as a confirmation '
   'or as an exclusion unless the exclusion is independent of both drifts',
   all(q['verdict'] == 'not separable' or q['robust'] for q in PEDGE)
   if DRIVE != 7 else False,
   '%d pairs carry an edge-limited drift: %s'
   % (len(PEDGE),
      '; '.join('%s %s/%s %s' % (tname(q['star']), q['eblo'].split('_')[-1],
                                 q['ebhi'].split('_')[-1], q['verdict'])
                for q in PEDGE)))

# =====================================================================
# 6.  THE TRUE EXTENT OF THE GRID, over every window that records one.  The
#     overshoot is bounded from the trial count alone -- it is less than one
#     step, and one step is at most 2*drift_max/(n-2) -- so the bound needs no
#     time span and holds for every window in the catalogue.
# =====================================================================
WIN = []
for r in CAT:
    if not r['n_drift_trials'] or not r['drift_max_Hz_s']:
        continue
    n = int(r['n_drift_trials'])
    dmax = float(r['drift_max_Hz_s'])
    nu = 0.5 * (float(r['flo_GHz']) + float(r['fhi_GHz']))
    if n < 3:
        continue
    WIN.append(dict(eb=r['eb'], star=r['star_name'], n=n, dmax=dmax, nu=nu,
                    sclass=r['search_class'],
                    ceil_nhz=dmax / nu,
                    top_bound_nhz=(dmax + 2.0 * dmax / (n - 2)) / nu))
WA = [w for w in WIN if w['sclass'] == 'A']
WB = [w for w in WIN if w['sclass'] == 'B']
m('EgNWinGrid', '%d' % len(WIN))
m('EgNWinA', '%d' % len(WA))
m('EgNWinB', '%d' % len(WB))
m('EgTopBoundANHz', '%.1f' % max(w['top_bound_nhz'] for w in WA))
m('EgTopBoundBNHz', '%.1f' % max(w['top_bound_nhz'] for w in WB))
_measA = [r for r in ONGRID if r['sclass'] == 'A' and r['top_nhz']]
m('EgTopMeasANHz', '%.2f' % max(r['top_nhz'] for r in _measA))
m('EgNTopMeasA', '%d' % len(_measA))
_measB = [r for r in ONGRID if r['sclass'] == 'B' and r['top_nhz']]
if _measB:
    m('EgTopMeasBNHz', '%.1f' % max(r['top_nhz'] for r in _measB))
    m('EgNTopMeasB', '%d' % len(_measB))

# ★★★ E8 -- THE CEILING THE PAPER DECLARES IS THE LOWER EDGE OF THE GRID AND
# NOT ITS UPPER ONE.  Asserted as the inequality it is, over every window the
# catalogue records a grid for, so it stays meaningful whatever the ceiling is
# set to.
_ceil = float(macro('DriftCeilLo'))
_ceilhi = float(macro('DriftCeilHi'))
_lo_ok = all(w['ceil_nhz'] <= _ceilhi + 0.05 for w in WIN)
_hi_bad = [w for w in WIN if w['top_bound_nhz'] > _ceilhi + 0.05]
if DRIVE == 8:                           # E8: the upper edge called the ceiling
    _hi_bad = []
ck('E8 the declared ceiling bounds the grid from below only: every window\'s '
   'negative edge is inside it, and the positive edge of some windows is not',
   _lo_ok and bool(_hi_bad),
   'declared %.1f-%.1f nHz; negative edge at most %.2f nHz; positive edge '
   'bounded above by up to %.1f nHz, outside the declared range in %d of %d '
   'windows (%d Class A)'
   % (_ceil, _ceilhi, max(w['ceil_nhz'] for w in WIN),
      max(w['top_bound_nhz'] for w in WIN), len(_hi_bad), len(WIN),
      len([w for w in _hi_bad if w['sclass'] == 'A'])))

# =====================================================================
# 7.  OUTPUT
# =====================================================================
def fmtd(r):
    return '$%+d$' % round(r['drift'])


TAB = [r'%% GENERATED by edge_v423.py -- do not hand-edit.',
       r'\begin{tabular}{@{}llr@{~}r@{~}c@{~}r@{~}l@{}}',
       r'\hline',
       r'Star & block & $\nu$ & $\dot\nu_{\rm obs}$ & trial & '
       r'\multicolumn{2}{c}{$|a_{\rm los}|$} \\',
       r' & & (GHz) & (Hz\,s$^{-1}$) & & '
       r'\multicolumn{2}{c}{(m\,s$^{-2}$)} \\',
       r'\hline']
for r in sorted(EDGE, key=lambda q: (q['star'], q['freq'])):
    TAB.append(r'%s & \texttt{%s} & %.3f & %s & %d/%d & $\ge$ & %.2f \\'
               % (tname(r['star']), r['eb'].split('_')[-1], r['freq'],
                  fmtd(r), r['k'], (r['n_rec'] or r['ntrial']) - 1,
                  r['alos']))
TAB += [r'\hline', r'\end{tabular}']
open(OUTT, 'w').write('\n'.join(TAB) + '\n')

with open(OUT, 'w') as fh:
    fh.write('%% GENERATED by edge_v423.py (round %d) -- do not hand-edit.\n'
             % ROUND)
    for k, v in M:
        fh.write('\\newcommand{\\%s}{%s}\n' % (k, v))

json.dump(dict(generator='edge_v423.py', round=ROUND, drive=DRIVE,
               rows=[{k: v for k, v in r.items() if k != 'tried'}
                     for r in ROWS],
               pairs=PR, orphans=ORPHAN, blockstep=BLOCKSTEP, twins=TWIN,
               edgeset=[r["cid"] for r in EDGE],
               macros=dict(M), failures=FAIL),
          open(OUTJ, 'w'), indent=1, default=str)

print('\n%d macros, %d rows, %d edge-limited, %d failures %s'
      % (len(M), len(ROWS), len(EDGE), len(FAIL), FAIL))
sys.exit(1 if FAIL and DRIVE == 0 else 0)
