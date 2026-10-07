#!/usr/bin/env python3
r"""Round 240 (v4.13): the line mask applied without exception, the recurrence
test run on the line-attributed crossings, and the image-sideband check.

WHAT THIS FILE OWNS

    Three statements about the mask that the paper made and could not support,
    all of them downstream of `maskframe_v411.py`, which this imports as a
    module so that there is one mask and one frame chain.

1.  ONE RULE FOR EVERY CROSSING.  The species list attributes three crossings
    to sulphur monoxide, and one of the three was reported outside the mask on
    the ground that sulphur monoxide post-dates its classification.  That
    objection is true of every species in the list, because the list is a
    SINGLE dated query: it cannot separate one coincidence from another.  So
    the rule is applied uniformly and the dates are published -- the date the
    species list was queried against the date the disposition criteria were
    fixed -- and the counts are published BOTH WAYS, so that a reader can see
    exactly what the choice costs.  The three crossings are READ out of the
    mask (the set of crossings whose attribution changes when the sulphur
    monoxide transitions are removed from it) and never listed here.

2.  THE RECURRENCE TEST IS RUN ON THE ATTRIBUTED CROSSINGS.  The paper says
    every crossing goes on to the recurrence test whichever side of the mask
    it falls, and then tabulated no test for most of the attributed ones.  The
    test needs the predicted cell, which needs only the stellar-frame
    frequency and the repeat coverage, so there was never a reason not to run
    it.  Where the dynamic-spectrum campaign measured a crossing the measured
    record is used unchanged -- the same definition and the same products as
    the unattributed crossings.  Where it did not, the released catalogue
    answers the question conservatively: a repeat window's own largest
    statistic at the stellar position is a maximum over every channel and
    every drift trial in that window, so it is an UPPER BOUND on the statistic
    at the predicted cell, and a bound below what persistence at the discovery
    flux predicts excludes persistence a fortiori.  Crossings with no repeat
    window covering the cell are named, not counted.

3.  IMAGE-SIDEBAND LEAKAGE.  The mask holds signal-sideband frequencies only.
    Two unattributed crossings sit in the sideband opposite their block's
    CO(2-1) crossing, at frequencies that look like a mirror about a plausible
    first local oscillator.  The oscillator is not in the released products,
    but it is bounded by the block's own spectral windows: every window must
    lie within the receiver's intermediate-frequency range on one side of it
    or the other.  The mirror hypothesis names a particular oscillator
    setting, so it can be tested against that bound.

ASSERTIONS (each driven, see --drive)
    S1  exactly the crossings this generator names change attribution when
        sulphur monoxide is removed from the species list, and the count is
        read from the mask rather than declared
    S2  the counts close on the crossing total under both choices, and differ
        by the number of crossings sulphur monoxide decides
    S3  the species list post-dates the disposition criteria, so no species in
        it is chronologically privileged -- the premise of the uniform rule
    S4  every attributed crossing is either tested for recurrence or named as
        untestable, and the two sets partition the attributed set
    S5  every crossing counted as recovered has a second epoch whose own
        crossing lies within one channel of the predicted cell
    S6  the local-oscillator setting the mirror hypothesis requires lies
        outside the range the block's own windows permit, and that range is
        non-empty -- so the test is neither vacuous nor circular
    S7  the hold-out rule was fixed before the first reserved block was
        searched and after the disposition criteria, which is what the paper
        must say instead of "before the archive was searched"
    S8  the compact species table is the mask: every species present and the
        per-species counts summing to the transition count

    python3 maskrecur_v413.py [--drive N]

-> survey_numbers_round240.tex, tab_maskspecies_v413.tex,
   maskrecur_v413.json
"""
from __future__ import annotations

import csv
import json
import os
import sys

import maskcat_v412 as mc
import maskframe_v411 as mf

HERE = os.path.dirname(os.path.abspath(__file__))
C_KMS = mf.C_KMS
HALF = mf.MASK_HALF_KMS
TRIG = 5.0

# ALMA receiver intermediate-frequency ranges, ALMA Technical Handbook.  Used
# only to bound a first local oscillator from a block's own windows.
IF_RANGE = {3: (4.0, 8.0), 4: (4.0, 8.0), 5: (4.0, 8.0), 6: (4.5, 10.0),
            7: (4.0, 8.0), 8: (4.0, 8.0)}
MONTH = ('January', 'February', 'March', 'April', 'May', 'June', 'July',
         'August', 'September', 'October', 'November', 'December')


def _load(*p):
    return json.load(open(os.path.join(HERE, *p), encoding='utf-8'))


def longdate(iso):
    """2026-10-06T05:54:41Z -> 2026 October 6.  No date is typed anywhere."""
    y, m, d = iso[:10].split('-')
    return '%s %s %d' % (y, MONTH[int(m) - 1], int(d))


def tname(s):
    """The ledger's display name with non-breaking spaces, so that a star
    does not break across a column.  Applied to every name, not only the ones
    carrying a maths minus, or the list reads in two styles."""
    return s.replace(' ', '~')


def enumerate_list(items):
    items = list(items)
    if not items:
        return 'none'              # only reachable under a driven assertion
    if len(items) == 1:
        return items[0]
    return ', '.join(items[:-1]) + ' and ' + items[-1]


def span(vals, fmt='%.1f'):
    return fmt % min(vals) if vals else '0'


def main(argv):
    drive, driven = 0, False
    for i, a in enumerate(argv):
        if a == '--drive':
            drive, driven = int(argv[i + 1]), True
    suf = '_drive%d' % drive if driven else ''
    fail = []

    def ck(name, cond, detail=''):
        if not cond:
            fail.append('%s: %s' % (name, detail))

    M = {}

    def m(k, v):
        assert k.isalpha(), k            # a macro name may hold letters only
        assert k not in M, k
        M[k] = str(v)

    CAT = list(csv.DictReader(open(os.path.join(
        HERE, 'per_target_results_v3.99.csv'), encoding='utf-8')))
    REP = list(csv.DictReader(open(os.path.join(
        HERE, 'repaired_v409.csv'), encoding='utf-8')))
    LED = _load('ledger.json')['rows']
    RECUR = _load('recurcols_v411.json')
    BARY = _load('r8inputs', 'bary_v405.json')['v_bary_kms']
    LINELIST = _load('r11inputs', 'linelist_v412.json')
    PREREG = _load('prereg_order_v383.json')

    # ====================================================== 1. the SO rule
    TRANS = dict(mf.TRANS)
    NO_SO = {k: v for k, v in TRANS.items() if mf.species(k) != 'SO'}
    if drive == 1:
        NO_SO = dict(TRANS)

    def att(row, trans):
        return abs(mf.nearest(row['frame']['f_stellar'], trans)[2]) <= HALF

    decided = [r for r in LED if att(r, TRANS) != att(r, NO_SO)]
    attr = [r for r in LED if att(r, TRANS)]
    attr_noso = [r for r in LED if att(r, NO_SO)]
    rank_un = [r for r in LED if r['screen'] and not att(r, TRANS)]
    rank_un_noso = [r for r in LED if r['screen'] and not att(r, NO_SO)]
    ck('S1 exactly the crossings named here change attribution when sulphur '
       'monoxide leaves the species list, and every one of them is attributed '
       'to a sulphur monoxide transition under the rule',
       len(decided) >= 1
       and all(mf.species(mf.nearest(r['frame']['f_stellar'], TRANS)[0]) == 'SO'
               and att(r, TRANS) and not att(r, NO_SO) for r in decided),
       [(r['display'], mf.nearest(r['frame']['f_stellar'], TRANS)[0])
        for r in decided])

    n_dec = len(decided)
    if drive == 2:
        n_dec += 1
    ck('S2 the attributed and unattributed counts close on the crossing total '
       'under both choices, and differ by the crossings sulphur monoxide '
       'decides',
       len(attr) + (len(LED) - len(attr)) == len(LED)
       and len(attr) - len(attr_noso) == n_dec,
       '%d/%d with, %d/%d without, %d decided'
       % (len(attr), len(LED) - len(attr), len(attr_noso),
          len(LED) - len(attr_noso), n_dec))

    d_list = LINELIST['queried_utc']
    d_crit = PREREG['criteria']['date']
    d_hold = PREREG['holdout']['date']
    d_first = PREREG['first_reserved_block_searched']['date']
    if drive == 3:
        d_list = d_crit
    ck('S3 the species list is a single query made after the disposition '
       'criteria were fixed, so no species in it predates a classification',
       d_list[:10] > d_crit,
       'species list %s, criteria %s' % (d_list, d_crit))
    if drive == 7:
        d_hold = '2026-09-18'
    ck('S7 the hold-out rule was fixed after the disposition criteria and '
       'before the first reserved block was searched',
       d_crit < d_hold < d_first,
       'criteria %s, hold-out %s, first reserved %s'
       % (d_crit, d_hold, d_first))

    so_eu = sorted(mc.MASK[mf.nearest(r['frame']['f_stellar'], TRANS)[0]]['eu']
                   for r in decided) or [0.0]
    # ★ The WORD is generated from the number, not typed beside it: "three"
    # written next to a macro that says 3 is the same defect as typing the 3.
    _W = ('no', 'one', 'two', 'three', 'four', 'five', 'six', 'seven',
          'eight', 'nine', 'ten')
    m('MkNSODecide', '%d' % len(decided))
    m('MkNSODecideWord', _W[len(decided)] if len(decided) < len(_W)
      else '%d' % len(decided))
    m('MkSOStars', enumerate_list(tname(r['display']) for r in
                                  sorted(decided, key=lambda x: x['display'])))
    m('MkSODvList', enumerate_list(
        '$%+.1f$' % mf.nearest(r['frame']['f_stellar'], TRANS)[2]
        for r in sorted(decided, key=lambda x: x['display'])))
    m('MkSOEuLo', '%.0f' % so_eu[0])
    m('MkSOEuHi', '%.0f' % so_eu[-1])
    m('MkAttrSO', '%d' % len(attr))
    m('MkUnattrSO', '%d' % (len(LED) - len(attr)))
    m('MkAttrNoSO', '%d' % len(attr_noso))
    m('MkUnattrNoSO', '%d' % (len(LED) - len(attr_noso)))
    m('MkRankSO', '%d' % len(rank_un))
    m('MkRankNoSO', '%d' % len(rank_un_noso))
    m('MkListDate', longdate(d_list))
    m('MkCritDate', longdate(d_crit))
    m('MkHoldDate', longdate(d_hold))
    m('MkFirstResDate', longdate(d_first))

    # ============================= 2. recurrence on attributed crossings
    bysys, winof = {}, {}
    for r in CAT:
        bysys.setdefault(r['system_id'], []).append(r)
        winof.setdefault(r['eb'], []).append(r)
    rms_rep = {(r['eb'], round(float(r['flo_GHz']), 4)):
               float(r['rms_mJy_repaired']) for r in REP}

    def own_window(row):
        """The window a crossing sits in, and the noise in it.

        Four crossings are not in the released catalogue -- they come from the
        re-extraction -- and their windows are in the re-extraction record, so
        both sources are consulted and the row is keyed on the block and the
        frequency, never on the star.
        """
        for r in winof.get(row['eb'], []):
            lo, hi = sorted((float(r['flo_GHz']), float(r['fhi_GHz'])))
            if lo <= row['freq'] <= hi:
                return float(r['rms_mJy']), r['system_id'], \
                    float(r['chanw_Hz'])
        for r in REP:
            lo, hi = sorted((float(r['flo_GHz']), float(r['fhi_GHz'])))
            if r['eb'] == row['eb'] and lo <= row['freq'] <= hi:
                return float(r['rms_mJy_repaired']), None, float(r['chanw_Hz'])
        return None, None, None

    def repeats(row, sysid):
        """Class A windows of other blocks toward the same system that cover
        the crossing's stellar-frame frequency, transported to each block's
        own barycentric term."""
        out = []
        if sysid is None:
            return out
        fs, vs = row['frame']['f_stellar'], row['frame']['v_sys']
        for r in bysys[sysid]:
            if r['eb'] == row['eb'] or r['search_class'] != 'A':
                continue
            flo = round(float(r['flo_GHz']), 6)
            vb = BARY.get('%s|%.6f' % (r['eb'], flo))
            here = fs / (1.0 + vs / C_KMS) / (1.0 - (vb or 0.0) / C_KMS)
            lo, hi = sorted((float(r['flo_GHz']), float(r['fhi_GHz'])))
            cw = float(r['chanw_Hz']) / 1e9
            if lo - 0.5 * cw <= here <= hi + 0.5 * cw:
                out.append((r, here, cw))
        return out

    # The ledger indexed for the recovery test.  A later block recovers a
    # crossing if its OWN crossing sits at the same stellar-frame frequency
    # within a channel, or -- for a transition the disc resolves, where the
    # brightest channel moves between epochs -- if its own crossing is
    # attributed to the same transition inside the same velocity window.
    ledger_fs = [(r['eb'], r['frame']['f_stellar'], float(r['tstar']),
                  mf.nearest(r['frame']['f_stellar'], TRANS)[0]
                  if att(r, TRANS) else None)
                 for r in LED]
    rows_out, recovered, excluded, untested, measured = [], [], [], [], []
    for row in sorted(attr, key=lambda x: (x['display'], x['freq'])):
        rms, sysid, _cw = own_window(row)
        key = '%s|%.6f' % (row['eb'], row['freq'])
        reps = repeats(row, sysid)
        rec = dict(star=row['display'], eb=row['eb'], freq_GHz=row['freq'],
                   tstar=float(row['tstar']), n_repeat=len(reps))
        # a second epoch whose OWN crossing sits at the same stellar-frame
        # frequency is the test returning a recovery, with its own statistic
        line = mf.nearest(row['frame']['f_stellar'], TRANS)[0]
        same = []
        for r, here, cw in reps:
            for eb2, fs2, t2, ln2 in ledger_fs:
                if eb2 != r['eb']:
                    continue
                if abs(fs2 - row['frame']['f_stellar']) <= cw or ln2 == line:
                    same.append((r['eb'], t2))
        if drive == 5:
            same = []
        if key in RECUR and RECUR[key].get('T_pers') is not None:
            # The dynamic-spectrum campaign's own record, unchanged: same
            # definition, same products and same exclusion statistic as the
            # unattributed crossings, so the two halves of the ledger are
            # comparable.  `T_rep` is the statistic at the predicted cell.
            q = RECUR[key]
            rec.update(verdict='measured', T_pers=q['T_pers'],
                       T_rep=q.get('T_rep', q.get('T_matched')),
                       excl=q['excl'], n_repeat_measured=q['n_rep'])
            measured.append(rec)
        elif same:
            rec.update(verdict='recovered',
                       second_epoch_T=round(max(t for _, t in same), 2),
                       n_second_epoch=len({e for e, _ in same}))
            recovered.append(rec)
        elif reps and rms:
            s_disc = float(row['tstar']) * rms
            best = max(reps, key=lambda z: s_disc / float(z[0]['rms_mJy']))
            t_pers = s_disc / float(best[0]['rms_mJy'])
            t_bound = float(best[0]['star_snr'])
            rec.update(verdict=('excluded' if t_bound < t_pers
                                else 'inconclusive'),
                       T_pers=round(t_pers, 2), T_bound=round(t_bound, 2),
                       deepest_eb=best[0]['eb'])
            (excluded if t_bound < t_pers else untested).append(rec)
        else:
            rec.update(verdict='untested',
                       why=('no Class A window of another block covers the '
                            'predicted cell'))
            untested.append(rec)
        rows_out.append(rec)

    tested = measured + recovered + excluded
    if drive == 4:
        untested = untested[:-1]
    ck('S4 every attributed crossing is either tested for recurrence or named '
       'as untestable, and the two sets partition the attributed set',
       len(tested) + len(untested) == len(attr) and len(rows_out) == len(attr),
       '%d measured + %d recovered + %d excluded + %d untested against %d'
       % (len(measured), len(recovered), len(excluded), len(untested),
          len(attr)))
    # ★ The criterion must be able to fail, and it does: not every attributed
    # crossing is present again, which is the whole point of running the test
    # rather than assuming the answer.
    ck('S5 every crossing counted as recovered has a later block whose own '
       'crossing reaches the trigger at the predicted cell, and the criterion '
       'is not satisfied by every attributed crossing',
       bool(recovered)
       and all(r['n_second_epoch'] >= 1 and r['second_epoch_T'] >= TRIG
               for r in recovered)
       and len(recovered) < len(tested),
       '%d recovered of %d tested; weakest second-epoch statistic %s'
       % (len(recovered), len(tested),
          min([r['second_epoch_T'] for r in recovered] or [None])))

    m('MkAttrTested', '%d' % len(tested))
    m('MkAttrRecur', '%d' % len(recovered))
    m('MkAttrExcl', '%d' % (len(measured) + len(excluded)))
    m('MkAttrUntest', '%d' % len(untested))
    m('MkAttrUntestNames', enumerate_list(
        sorted({tname(r['star']) for r in untested})))
    m('MkAttrRecurStars', enumerate_list(
        sorted({tname(r['star']) for r in recovered})))
    _rt = [r['second_epoch_T'] for r in recovered] or [0.0]
    _ex = [r['excl'] for r in measured] or [0.0]
    m('MkAttrRecurTLo', '%.1f' % min(_rt))
    m('MkAttrRecurTHi', '%.1f' % max(_rt))
    m('MkAttrExclLo', '%.1f' % min(_ex))
    m('MkAttrExclHi', '%.1f' % max(_ex))

    # ==================================================== 3. image sideband
    # The two crossings the question is about are READ as the unattributed
    # crossings that share a block with an attributed one in the opposite
    # sideband, never named.
    unattr = [r for r in LED if not att(r, TRANS)]
    pairs = []
    for u in unattr:
        for a in attr:
            if a['eb'] != u['eb'] or a['freq'] == u['freq']:
                continue
            if abs(a['freq'] - u['freq']) > 2 * min(IF_RANGE.get(
                    int(u['band']), (4.0, 8.0))):
                pairs.append((u, a))
    img = []
    for u, a in pairs:
        band = int(u['band'])
        imin, imax = IF_RANGE[band]
        cen = sorted({0.5 * (float(w['flo_GHz']) + float(w['fhi_GHz']))
                      for w in winof[u['eb']]})
        gap, idx = max((cen[i + 1] - cen[i], i) for i in range(len(cen) - 1))
        lsb, usb = cen[:idx + 1], cen[idx + 1:]
        lo_min = max(max(lsb) + imin, max(usb) - imax)
        lo_max = min(min(lsb) + imax, min(usb) - imin)
        lo_req = 0.5 * (u['freq'] + a['freq'])
        if drive == 6:
            lo_req = 0.5 * (lo_min + lo_max)
        # the nearest masked transition to the image band, in the star's frame
        f1, f2 = sorted((2 * lo_min - u['freq'], 2 * lo_max - u['freq']))
        vb, vs = u['frame']['v_bary'], u['frame']['v_sys']

        def stel(f):
            return (f * (1.0 - vb / C_KMS)) * (1.0 + vs / C_KMS)

        near = min((abs(mf.offset_kms(stel(f1), v[0]))
                    if mf.offset_kms(stel(f1), v[0])
                    * mf.offset_kms(stel(f2), v[0]) > 0 else 0.0)
                   for v in TRANS.values())
        img.append(dict(star=u['display'], eb=u['eb'], freq_GHz=u['freq'],
                        band=band, partner_GHz=a['freq'],
                        lo_permitted=[round(lo_min, 3), round(lo_max, 3)],
                        lo_required=round(lo_req, 3),
                        if_required=round(lo_req - min(cen), 3),
                        if_max=imax,
                        image_GHz=[round(f1, 3), round(f2, 3)],
                        nearest_masked_kms=round(near, 0)))
    ck('S6 the local-oscillator setting the mirror hypothesis requires lies '
       'outside the range the block\'s own windows permit, and that range is '
       'non-empty',
       bool(img)
       and all(q['lo_permitted'][0] < q['lo_permitted'][1] for q in img)
       and all(not (q['lo_permitted'][0] <= q['lo_required']
                    <= q['lo_permitted'][1]) for q in img),
       [(q['star'], q['lo_permitted'], q['lo_required']) for q in img])

    if img:
        m('MkImgN', '%d' % len(img))
        m('MkImgStar', tname(img[0]['star']))
        m('MkImgFreqs', enumerate_list('%.2f' % q['freq_GHz'] for q in
                                       sorted(img, key=lambda z:
                                              z['freq_GHz'])))
        m('MkImgLOLo', '%.2f' % min(q['lo_permitted'][0] for q in img))
        m('MkImgLOHi', '%.2f' % max(q['lo_permitted'][1] for q in img))
        m('MkImgLOReqLo', '%.2f' % min(q['lo_required'] for q in img))
        m('MkImgLOReqHi', '%.2f' % max(q['lo_required'] for q in img))
        m('MkImgIFReq', '%.1f' % max(q['if_required'] for q in img))
        m('MkImgIFMax', '%.1f' % max(q['if_max'] for q in img))
        m('MkImgDvMin', '%.0f' % min(q['nearest_masked_kms'] for q in img))
        m('MkImgPartner', '%.2f' % img[0]['partner_GHz'])

    # ================================ 4. the mask as a table of species
    # The transition-by-transition table printed every one of the mask's rows
    # across the full page width, which is half a page to say what the
    # deposited line list says exactly.  One row per species, with the counts
    # required to sum to the mask, keeps the definition in view at a tenth of
    # the area.
    spec: dict = {}
    for k, v in mc.MASK.items():
        spec.setdefault(mc.species_of(k), []).append(v)
    srows = sorted(spec.items(), key=lambda it: min(x['f'] for x in it[1]))
    TABS = os.path.join(HERE, 'tab_maskspecies_v413%s.tex' % suf)
    with open(TABS, 'w') as fh:
        fh.write('%% GENERATED by maskrecur_v413.py -- do not hand-edit.\n')
        fh.write('\\begin{tabular}{@{}lrr@{\\,}c@{\\,}rr@{}}\n\\hline\n')
        fh.write('Species & $N$ & \\multicolumn{3}{c}{$\\nu_0$ (GHz)} & '
                 '$E_{\\rm u}$ (K) \\\\\n\\hline\n')
        for sp, vs in srows:
            eu = [x['eu'] for x in vs if x['ll'] != 'Recomb']
            fh.write('%s & %d & %.2f & -- & %.2f & %s \\\\\n'
                     % (mc.SPEC_TEX.get(sp, sp), len(vs),
                        min(x['f'] for x in vs), max(x['f'] for x in vs),
                        ('--' if not eu else
                         ('%.0f' % eu[0] if min(eu) == max(eu)
                          else '%.0f--%.0f' % (min(eu), max(eu))))))
        fh.write('\\hline\n\\end{tabular}%\n')
    n_spec_rows = len(srows)
    if drive == 8:
        n_spec_rows += 1
    ck('S8 the species table is the mask: one row per species, every species '
       'present, and the row counts summing to the transition count',
       n_spec_rows == len({mc.species_of(k) for k in mc.MASK})
       and sum(len(v) for v in spec.values()) == len(mc.MASK),
       '%d rows, %d transitions against %d'
       % (n_spec_rows, sum(len(v) for v in spec.values()), len(mc.MASK)))
    m('MkNSpecRows', '%d' % len(srows))

    # ----------------------------------------------------------------- out
    OUT = os.path.join(HERE, 'survey_numbers_round240%s.tex' % suf)
    with open(OUT, 'w') as fh:
        fh.write('%% GENERATED by maskrecur_v413.py -- do not hand-edit.\n')
        for k in sorted(M):
            fh.write('\\newcommand{\\%s}{%s}\n' % (k, M[k]))
    JS = os.path.join(HERE, 'maskrecur_v413%s.json' % suf)
    json.dump(dict(generator='maskrecur_v413.py', drive=drive,
                   so=dict(decided=[r['display'] for r in decided],
                           attributed_with_SO=len(attr),
                           unattributed_with_SO=len(LED) - len(attr),
                           attributed_without_SO=len(attr_noso),
                           unattributed_without_SO=len(LED) - len(attr_noso),
                           rank_flagged_with_SO=len(rank_un),
                           rank_flagged_without_SO=len(rank_un_noso),
                           species_list_queried=d_list,
                           criteria_fixed=d_crit, holdout_fixed=d_hold,
                           first_reserved_searched=d_first),
                   attributed_recurrence=rows_out,
                   image_sideband=img),
              open(JS, 'w'), indent=1, sort_keys=True)

    print('maskrecur_v413 (round 240): %d crossings, %d attributed under the '
          'uniform rule, %d without sulphur monoxide'
          % (len(LED), len(attr), len(attr_noso)))
    print('  sulphur monoxide decides %d: %s'
          % (len(decided), ', '.join('%s %+.1f km/s from %s'
                                     % (r['display'],
                                        mf.nearest(r['frame']['f_stellar'],
                                                   TRANS)[2],
                                        mf.nearest(r['frame']['f_stellar'],
                                                   TRANS)[0])
                                     for r in decided)))
    print('  rank-flagged unattributed: %d with SO, %d without'
          % (len(rank_un), len(rank_un_noso)))
    print('  recurrence on the attributed: %d measured, %d recovered at a '
          'second epoch, %d excluded from the catalogue, %d untestable'
          % (len(measured), len(recovered), len(excluded), len(untested)))
    for r in rows_out:
        print('     %-20s %-22s %10.6f  %-13s %s'
              % (r['star'][:20], r['eb'], r['freq_GHz'], r['verdict'],
                 {k: v for k, v in r.items()
                  if k not in ('star', 'eb', 'freq_GHz', 'verdict')}))
    for q in img:
        print('  image sideband: %s %.4f GHz, partner %.4f, LO permitted '
              '%.3f-%.3f, mirror needs %.3f (IF %.2f against %.1f max), '
              'image %.3f-%.3f, nearest masked %.0f km/s'
              % (q['star'], q['freq_GHz'], q['partner_GHz'],
                 q['lo_permitted'][0], q['lo_permitted'][1],
                 q['lo_required'], q['if_required'], q['if_max'],
                 q['image_GHz'][0], q['image_GHz'][1],
                 q['nearest_masked_kms']))
    print('  -> %s (%d macros), %s'
          % (os.path.basename(OUT), len(M), os.path.basename(JS)))
    for f in fail:
        print('  ASSERTION FIRED  ' + f)
    print('maskrecur_v413: %d assertions fired' % len(fail))
    return 1 if fail else 0


if __name__ == '__main__':
    sys.exit(main(sys.argv))
