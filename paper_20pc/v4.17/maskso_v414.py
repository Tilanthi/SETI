#!/usr/bin/env python3
r"""Round 330: the sulphur monoxide coincidences, the recurrence test on the
line-attributed crossings, and the image-sideband check.

WHAT THIS FILE OWNS

1.  THE SULPHUR MONOXIDE COINCIDENCES ARE A NOTE, ON PHYSICAL GROUNDS.
    Three crossings fall inside the mask of a sulphur monoxide transition.
    The offset is printed beside each of them and disposes of none of them,
    for two reasons that hold for the SPECIES and not for any one crossing:
    sulphur monoxide has never been reported in a debris disc, where the
    second-generation gas is CO, C and O; and in the one such window that
    also covers CO(3-2), that line is absent at a limit BELOW the crossing's
    own flux, so an SO line there would have to outshine an undetected
    CO(3-2) line in the same data.  A chronological argument would not do
    the work -- the species list is a single dated query and post-dates
    every classification equally -- and a physical one reaches all three
    alike.  The predicate lives in `maskframe_v411.note_reason`; the three
    crossings are READ out of the mask here and never listed.
    ★ The counts are published BOTH WAYS, so a reader can see what the
    choice costs: it moves three crossings and one rank-leading crossing.

2.  THE RECURRENCE TEST IS RUN ON THE ATTRIBUTED CROSSINGS, AND THE LEDGER
    PRINTS IT.  The test needs the predicted cell, which needs only the
    stellar-frame frequency and the repeat coverage, so there was never a
    reason not to run it -- and a ledger that claims to reproduce every
    disposition cannot leave the column blank on fifteen rows.  Where the
    dynamic-spectrum campaign measured a crossing its record is used
    unchanged.  Where it did not, a repeat window's own largest statistic at
    the stellar position is a maximum over every channel and every drift
    trial in that window, so it is an UPPER BOUND on the statistic at the
    predicted cell; such rows are published AS bounds, with the inequality
    carried into the exclusion.  Crossings with no covering repeat window
    are named, not counted.
    ★ `ledger_v410.py` imports `attributed_recurrence` from this module and
    fills Tables 8 and 9 from it, so the table and these macros are one
    computation and cannot disagree.

3.  IMAGE-SIDEBAND LEAKAGE.  The mask holds signal-sideband frequencies
    only.  Two unattributed crossings sit in the sideband opposite their
    block's CO(2-1) crossing, at frequencies that look like a mirror about a
    plausible first local oscillator.  The oscillator is not in the released
    products but is bounded by the block's own spectral windows, so the
    mirror hypothesis names a setting that can be tested against that bound.

4.  THE INJECTION BOOKKEEPING.  Three counts of "injections" appear in the
    paper -- 52, 49 and 40 -- and they are three different campaigns with
    three different denominators.  Each is named and given its denominator
    here so that no two can be read as one.

ASSERTIONS (each driven, see --drive)
    S1  the crossings whose coincidence is reported as a note are exactly
        those the noted species decides, and they are read from the mask
    S2  the counts close on the crossing total under both choices and differ
        by the number of crossings the noted species decides
    S3  the species list is one dated query made after the criteria were
        fixed, so no species in it is chronologically privileged -- which is
        why the note rests on physics instead
    S4  every crossing is either tested for recurrence or named as
        untestable, and the two sets partition the crossing list
    S5  every crossing counted as recovered has a later block whose own
        crossing reaches the trigger at the predicted cell, and not every
        attributed crossing does
    S6  the local-oscillator setting the mirror hypothesis requires lies
        outside the range the block's own windows permit, and that range is
        non-empty -- so the test is neither vacuous nor circular
    S7  the hold-out rule was fixed after the disposition criteria and
        before the first reserved block was searched
    S8  the compact species table is the mask: every species present and the
        per-species counts summing to the transition count
    S9  the three injection counts are three different sets, each smaller
        than its own denominator, and no two of them are the same set

    python3 maskso_v414.py [--drive N]

-> survey_numbers_round330.tex, tab_maskspecies_v414.tex, maskso_v414.json
"""
from __future__ import annotations

import csv
import json
import os
import sys

import maskcat_v412 as mc
import maskframe_v411 as mf

HERE = os.path.dirname(os.path.abspath(__file__))
ROUND = 330
C_KMS = mf.C_KMS
HALF = mf.MASK_HALF_KMS
TRIG = 5.0

# ALMA receiver intermediate-frequency ranges, ALMA Technical Handbook.  Used
# only to bound a first local oscillator from a block's own windows.
IF_RANGE = {3: (4.0, 8.0), 4: (4.0, 8.0), 5: (4.0, 8.0), 6: (4.5, 10.0),
            7: (4.0, 8.0), 8: (4.0, 8.0)}
MONTH = ('January', 'February', 'March', 'April', 'May', 'June', 'July',
         'August', 'September', 'October', 'November', 'December')
_W = ('no', 'one', 'two', 'three', 'four', 'five', 'six', 'seven', 'eight',
      'nine', 'ten')


def _load(*p):
    return json.load(open(os.path.join(HERE, *p), encoding='utf-8'))


def longdate(iso):
    """2026-10-06T05:54:41Z -> 2026 October 6.  No date is typed anywhere."""
    y, m, d = iso[:10].split('-')
    return '%s %s %d' % (y, MONTH[int(m) - 1], int(d))


def tname(s):
    """The ledger's display name with non-breaking spaces, so that a star
    does not break across a column."""
    return s.replace(' ', '~')


def enumerate_list(items):
    items = list(items)
    if not items:
        return 'none'              # only reachable under a driven assertion
    if len(items) == 1:
        return items[0]
    return ', '.join(items[:-1]) + ' and ' + items[-1]


def key_of(row):
    return '%s|%.6f' % (row['eb'], row['freq'])


# ==========================================================================
#  THE RECURRENCE TEST ON CROSSINGS THE DYNAMIC-SPECTRUM CAMPAIGN DID NOT
#  MEASURE.  Imported by `ledger_v410.py`, so the table and the appendix
#  come off one computation.
# ==========================================================================
def attributed_recurrence(rows, recurc, here=HERE):
    """Return {ledger key: record} for every crossing without a measured
    recurrence record, so the ledger's recurrence columns can be filled for
    all of them.

    `rows`     the ledger rows (ledger.json)
    `recurc`   recurcols_v411.json, the measured records

    A record carries the same quantities as a measured one -- n_rep, the
    repeat interval, T_pers, T_rep and the exclusion -- plus `bound`, which
    is True where T_rep is an upper bound on the statistic at the predicted
    cell rather than a reading of it.  A bound is published as a bound.
    """
    cat = list(csv.DictReader(open(os.path.join(
        here, 'per_target_results_v3.99.csv'), encoding='utf-8')))
    rep = list(csv.DictReader(open(os.path.join(
        here, 'repaired_v409.csv'), encoding='utf-8')))
    bary = _load('r8inputs', 'bary_v405.json')['v_bary_kms']
    # ★★★ ROUND 14: measured epochs.  The stored file gave HD 285968's three
    # census blocks one shared stamp -- they share a member OUS and only one is
    # indexed by the archive -- so every interval toward that star came out 0.0 d.
    mjd = __import__('epochs_r14').EPOCHS
    trans = dict(mf.TRANS)

    bysys, winof = {}, {}
    for r in cat:
        bysys.setdefault(r['system_id'], []).append(r)
        winof.setdefault(r['eb'], []).append(r)

    def own_window(row):
        """The window a crossing sits in and the noise in it.  Four crossings
        come from the re-extraction and are not in the released catalogue, so
        both sources are consulted; the row is keyed on the block and the
        frequency, never on the star.

        ★★★★ A WINDOW CAN APPEAR IN BOTH SOURCES, AND THEN THE NOISE MUST
        MATCH THE STATISTIC.  One window was extracted twice: the delivered
        extraction integrated 60.48 s of the track and the re-extraction
        2842.56 s of it, so their noises differ by a factor of 7.1.  The
        crossing statistic the ledger carries for that row is the
        re-extracted one -- `tstar_source` says so, and the delivered
        extraction puts it below the trigger -- but the catalogue row was
        reached first, so T_pers = T_star x sigma_own/sigma_repeat was formed
        from a statistic measured on 47 minutes of data and a noise measured
        on one, and came out 7.1 times too large.  The noise must come from
        the extraction the statistic came from.  The adopted value is
        checked against the sibling blocks of the same star at the same
        on-source time in `recurcond_v416.py` (Q4), which is an external
        test and not a preference."""
        repaired = None
        for r in rep:
            lo, hi = sorted((float(r['flo_GHz']), float(r['fhi_GHz'])))
            if r['eb'] == row['eb'] and lo <= row['freq'] <= hi:
                repaired = float(r['rms_mJy_repaired'])
                break
        for r in winof.get(row['eb'], []):
            lo, hi = sorted((float(r['flo_GHz']), float(r['fhi_GHz'])))
            if lo <= row['freq'] <= hi:
                if repaired is not None \
                        and row.get('tstar_source') == 'repaired':
                    return repaired, r['system_id']
                return float(r['rms_mJy']), r['system_id']
        if repaired is not None:
            return repaired, None
        return None, None

    def repeats(row, sysid):
        """Class A windows of other blocks toward the same system covering the
        crossing's stellar-frame frequency, each transported to its own
        block's barycentric term."""
        out = []
        if sysid is None:
            return out
        fs, vs = row['frame']['f_stellar'], row['frame']['v_sys']
        for r in bysys[sysid]:
            if r['eb'] == row['eb'] or r['search_class'] != 'A':
                continue
            vb = bary.get('%s|%.6f' % (r['eb'], round(float(r['flo_GHz']), 6)))
            here_f = fs / (1.0 + vs / C_KMS) / (1.0 - (vb or 0.0) / C_KMS)
            lo, hi = sorted((float(r['flo_GHz']), float(r['fhi_GHz'])))
            cw = float(r['chanw_Hz']) / 1e9
            if lo - 0.5 * cw <= here_f <= hi + 0.5 * cw:
                out.append((r, cw))
        return out

    # A later block recovers a crossing if its own crossing sits at the same
    # stellar-frame frequency within a channel, or -- for a transition the
    # disc resolves, where the brightest channel moves between epochs -- if
    # its own crossing is attributed to the same transition.
    ledger_fs = [(r['eb'], r['frame']['f_stellar'], float(r['tstar']),
                  r['line'] if r['line_coincident'] else None) for r in rows]

    out = {}
    for row in rows:
        k = key_of(row)
        if k in recurc and recurc[k].get('T_pers') is not None:
            continue
        # The dynamic-spectrum campaign declares its own exceptions, and one
        # crossing with no retained spectrum is one of them.  Filling it from
        # the catalogue here would give that campaign's published exception a
        # second answer from outside it, which is how one quantity acquires
        # two values.  This function fills the line-coincident rows, which
        # the campaign never covered at all.
        if not row.get('line_coincident'):
            continue
        rms, sysid = own_window(row)
        reps = repeats(row, sysid)
        t0 = mjd.get(row['eb'])
        dts = sorted(abs(mjd[r['eb']] - t0) for r, _ in reps
                     if t0 is not None and r['eb'] in mjd)
        rec = dict(n_rep=len(reps) or None,
                   dt_min_d=round(dts[0], 2) if dts else None,
                   dt_max_d=round(dts[-1], 2) if dts else None,
                   T_pers=None, T_rep=None, excl=None, bound=False)
        same = []
        for r, cw in reps:
            for eb2, fs2, t2, ln2 in ledger_fs:
                if eb2 != r['eb']:
                    continue
                if (abs(fs2 - row['frame']['f_stellar']) <= cw
                        or (ln2 is not None and ln2 == row['line']
                            and row['line_coincident'])):
                    same.append((r, t2))
        if same:
            # Present again.  The recurrence test has returned a recovery, so
            # no exclusion is formed: the quantity sigma_excl measures is the
            # significance at which persistence is ruled out, and persistence
            # is what has just been observed.  Forming it anyway would print
            # a positive exclusion against a line that demonstrably recurs,
            # because a resolved disc line does not scale with a point-source
            # noise between epochs of different array configuration.
            # ★★★ ROUND 14: THIS VALUE IS NOT A T_rep AND MUST NOT BE PRINTED
            # IN THE T_rep COLUMN.  `t_rep` here is the T_star of the
            # RECOVERING BLOCK'S OWN LEDGER ROW -- the strongest crossing that
            # block produced -- not a reading of the repeat at the predicted
            # stellar-frame cell, which is what every other row of that column
            # is.  On HD 285968, whose three census blocks each recover the
            # other two, the column printed +5.87/+5.96/+5.96 against the
            # rows' own statistics 5.956/5.868/5.835, so each row carried the
            # largest statistic of the OTHER rows under its own name.  A
            # referee found it in the typeset table.  It is a real quantity
            # and it keeps its own name; the column it does not belong in
            # stays blank, as it does for every other row with no exclusion.
            best, t_recov = max(same, key=lambda z: z[1])
            rec.update(verdict='recovered', T_recov=round(t_recov, 2),
                       recovered_eb=best['eb'])
        elif reps and rms:
            # Not present again.  A repeat window's own largest statistic at
            # the stellar position is a maximum over every channel and drift
            # trial in it, so it bounds the statistic at the predicted cell
            # from above and the exclusion from below.
            best = max(reps, key=lambda z: 1.0 / float(z[0]['rms_mJy']))[0]
            t_rep = float(best['star_snr'])
            t_pers = float(row['tstar']) * rms / float(best['rms_mJy'])
            denom = (1.0 + (t_pers / float(row['tstar'])) ** 2) ** 0.5
            rec.update(verdict='absent', bound=True,
                       T_pers=round(t_pers, 1), T_rep=round(t_rep, 2),
                       excl=round((t_pers - t_rep) / denom, 1),
                       deepest_eb=best['eb'])
        else:
            rec['verdict'] = 'untested'
            rec['why'] = ('no Class A window of another block covers the '
                          'predicted cell')
        out[k] = rec
    return out


# ==========================================================================
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

    LED = _load('ledger.json')['rows']
    RECUR = _load('recurcols_v411.json')
    LINELIST = _load('r11inputs', 'linelist_v412.json')
    PREREG = _load('prereg_order_v383.json')

    # ================================================ 1. the noted species
    TRANS = dict(mf.TRANS)

    def att_all(row):
        """Attributed if the uniform rule disposed of every coincidence."""
        return abs(mf.nearest(row['frame']['f_stellar'], TRANS)[2]) <= HALF

    def noted(row):
        rsn = mf.note_reason(row['frame']['line'], row['frame']['dv_stellar'])
        if drive == 1:
            return None
        return rsn

    dec = [r for r in LED if att_all(r) and noted(r)]
    attr = [r for r in LED if att_all(r) and not noted(r)]
    attr_alt = [r for r in LED if att_all(r)]
    rank = [r for r in LED if r['screen'] and not (att_all(r) and not
                                                   noted(r))]
    rank_alt = [r for r in LED if r['screen'] and not att_all(r)]
    ck('S1 the crossings whose coincidence is reported as a note are exactly '
       'those the noted species decides, and every one of them is inside the '
       'mask of a transition of that species',
       len(dec) >= 1
       and all(mf.species(mf.nearest(r['frame']['f_stellar'], TRANS)[0])
               in mf.NOTED_SPECIES for r in dec)
       and len(attr_alt) - len(attr) == len(dec),
       [(r['display'], mf.nearest(r['frame']['f_stellar'], TRANS)[0])
        for r in dec])

    n_dec = len(dec)
    if drive == 2:
        n_dec += 1
    ck('S2 the attributed and unattributed counts close on the crossing total '
       'under both choices, and differ by the crossings the noted species '
       'decides',
       len(attr) + (len(LED) - len(attr)) == len(LED)
       and len(attr_alt) - len(attr) == n_dec,
       '%d/%d adopted, %d/%d alternative, %d noted'
       % (len(attr), len(LED) - len(attr), len(attr_alt),
          len(LED) - len(attr_alt), n_dec))

    d_list = LINELIST['queried_utc']
    d_crit = PREREG['criteria']['date']
    d_hold = PREREG['holdout']['date']
    d_first = PREREG['first_reserved_block_searched']['date']
    if drive == 3:
        d_list = d_crit
    ck('S3 the species list is a single query made after the disposition '
       'criteria were fixed, so no species in it predates a classification '
       'and chronology cannot separate one coincidence from another',
       d_list[:10] > d_crit,
       'species list %s, criteria %s' % (d_list, d_crit))
    if drive == 7:
        d_hold = '2026-09-18'
    ck('S7 the hold-out rule was fixed after the disposition criteria and '
       'before the first reserved block was searched',
       d_crit < d_hold < d_first,
       'criteria %s, hold-out %s, first reserved %s'
       % (d_crit, d_hold, d_first))

    eu = sorted(mc.MASK[mf.nearest(r['frame']['f_stellar'], TRANS)[0]]['eu']
                for r in dec) or [0.0]
    dec_s = sorted(dec, key=lambda x: x['display'])
    m('MkNSODecide', '%d' % len(dec))
    m('MkNSODecideWord', _W[len(dec)] if len(dec) < len(_W) else '%d' % len(dec))
    m('MkSOStars', enumerate_list(tname(r['display']) for r in dec_s))
    m('MkSODvList', enumerate_list(
        '$%+.1f$' % mf.nearest(r['frame']['f_stellar'], TRANS)[2]
        for r in dec_s))
    m('MkSOEuLo', '%.0f' % eu[0])
    m('MkSOEuHi', '%.0f' % eu[-1])
    # The adopted pair, and the alternative pair beside it.
    m('MkAttr', '%d' % len(attr))
    m('MkUnattr', '%d' % (len(LED) - len(attr)))
    m('MkRankLead', '%d' % len(rank))
    m('MkRankLeadWord', _W[len(rank)] if len(rank) < len(_W) else '%d'
      % len(rank))
    m('MkAttrAlt', '%d' % len(attr_alt))
    m('MkUnattrAlt', '%d' % (len(LED) - len(attr_alt)))
    m('MkRankLeadAlt', '%d' % len(rank_alt))
    m('MkListDate', longdate(d_list))
    m('MkCritDate', longdate(d_crit))
    m('MkHoldDate', longdate(d_hold))
    m('MkFirstResDate', longdate(d_first))

    # ========================= 2. recurrence on every testable crossing
    EXTRA = attributed_recurrence(LED, RECUR)
    tested, untested, recovered, bounded = [], [], [], []
    for r in LED:
        k = key_of(r)
        q = RECUR.get(k) if RECUR.get(k, {}).get('T_pers') is not None \
            else EXTRA.get(k)
        nm = dict(star=r['display'], eb=r['eb'], freq_GHz=r['freq'],
                  tstar=float(r['tstar']),
                  attributed=bool(att_all(r) and not noted(r)))
        if q is None or (q.get('T_pers') is None
                         and q.get('verdict') != 'recovered'):
            nm['verdict'] = 'untested'
            untested.append(nm)
            continue
        nm.update({kk: vv for kk, vv in q.items() if kk != 'why'})
        tested.append(nm)
        if q.get('verdict') == 'recovered':
            recovered.append(nm)
        if q.get('bound'):
            bounded.append(nm)
    # ★ The partition alone is arithmetic and cannot fail.  What can fail,
    # and is the thing worth checking, is that a crossing reported as
    # untestable really has no covering repeat window: an untestable crossing
    # with coverage is a test that was not run and was counted as impossible.
    if drive == 4:
        untested[0]['n_rep'] = 1
    _wrong = [r for r in untested if r.get('n_rep')]
    ck('S4 every crossing is either tested for recurrence or named as '
       'untestable, the two sets partition the crossing list, and no '
       'crossing called untestable has a covering repeat window',
       len(tested) + len(untested) == len(LED) and not _wrong,
       '%d tested + %d untested against %d; %d untestable with coverage: %s'
       % (len(tested), len(untested), len(LED), len(_wrong),
          [(r['star'], r['eb']) for r in _wrong]))
    # ★ The criterion must be able to fail, and it does: not every attributed
    # crossing is present again, which is why the test is run rather than
    # assumed.
    if drive == 5 and recovered:
        recovered[0] = dict(recovered[0], T_recov=TRIG - 1.0)
    ck('S5 every crossing counted as recovered has a later block whose own '
       'crossing reaches the trigger, and the criterion is not satisfied by '
       'every attributed crossing',
       bool(recovered)
       and all(r.get('T_recov', 0.0) >= TRIG for r in recovered)
       and len(recovered) < len(tested)
       and not any(r.get('T_rep') is not None for r in recovered),
       '%d recovered of %d tested; weakest recovering-block statistic %s; '
       '%d of them carrying a T_rep they have not measured'
       % (len(recovered), len(tested),
          min([r.get('T_recov') for r in recovered] or [None]),
          sum(1 for r in recovered if r.get('T_rep') is not None)))

    att_tested = [r for r in tested if r['attributed']]
    att_untested = [r for r in untested if r['attributed']]
    att_excl = [r for r in att_tested if r not in recovered]
    m('MkAttrTested', '%d' % len(att_tested))
    m('MkAttrRecur', '%d' % len(recovered))
    m('MkAttrExcl', '%d' % len(att_excl))
    m('MkAttrUntest', '%d' % len(att_untested))
    m('MkAttrUntestNames', enumerate_list(
        sorted({tname(r['star']) for r in att_untested})))
    m('MkAttrRecurStars', enumerate_list(
        sorted({tname(r['star']) for r in recovered})))
    m('MkNBound', '%d' % len(bounded))
    _rt = [r['T_recov'] for r in recovered] or [0.0]
    m('MkAttrRecurTLo', '%.1f' % min(_rt))
    m('MkAttrRecurTHi', '%.1f' % max(_rt))
    # The exclusions reached on the noted coincidences, which is the number
    # that makes the choice of disposition immaterial to any conclusion.
    _dk = {key_of(r) for r in dec}
    _de = [r['excl'] for r in tested
           if '%s|%.6f' % (r['eb'], r['freq_GHz']) in _dk
           and r.get('excl') is not None]
    m('MkAttrExclLo', '%.1f' % min(_de or [0.0]))
    m('MkAttrExclHi', '%.1f' % max(_de or [0.0]))

    # ==================================================== 3. image sideband
    # The crossings the question is about are READ as the unattributed
    # crossings sharing a block with an attributed one in the opposite
    # sideband, never named.
    CATW = {}
    for r in csv.DictReader(open(os.path.join(
            HERE, 'per_target_results_v3.99.csv'), encoding='utf-8')):
        CATW.setdefault(r['eb'], []).append(r)
    unattr = [r for r in LED if not (att_all(r) and not noted(r))]
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
                      for w in CATW[u['eb']]})
        gap, idx = max((cen[i + 1] - cen[i], i) for i in range(len(cen) - 1))
        lsb, usb = cen[:idx + 1], cen[idx + 1:]
        lo_min = max(max(lsb) + imin, max(usb) - imax)
        lo_max = min(min(lsb) + imax, min(usb) - imin)
        lo_req = 0.5 * (u['freq'] + a['freq'])
        if drive == 6:
            lo_req = 0.5 * (lo_min + lo_max)
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
                        if_required=round(lo_req - min(cen), 3), if_max=imax,
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
    spec: dict = {}
    for k, v in mc.MASK.items():
        spec.setdefault(mc.species_of(k), []).append(v)
    srows = sorted(spec.items(), key=lambda it: min(x['f'] for x in it[1]))
    TABS = os.path.join(HERE, 'tab_maskspecies_v414%s.tex' % suf)
    with open(TABS, 'w') as fh:
        fh.write('%% GENERATED by maskso_v414.py -- do not hand-edit.\n')
        fh.write('\\begin{tabular}{@{}lrr@{\\,}c@{\\,}rr@{}}\n\\hline\n')
        fh.write('Species & $N$ & \\multicolumn{3}{c}{$\\nu_0$ (GHz)} & '
                 '$E_{\\rm u}$ (K) \\\\\n\\hline\n')
        for sp, vs in srows:
            eus = [x['eu'] for x in vs if x['ll'] != 'Recomb']
            fh.write('%s & %d & %.2f & -- & %.2f & %s \\\\\n'
                     % (mc.SPEC_TEX.get(sp, sp), len(vs),
                        min(x['f'] for x in vs), max(x['f'] for x in vs),
                        ('--' if not eus else
                         ('%.0f' % eus[0] if min(eus) == max(eus)
                          else '%.0f--%.0f' % (min(eus), max(eus))))))
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

    # ============================== 5. three injection campaigns, named
    # Minor 11.  "52", "49" and "40" are three campaigns with three jobs and
    # three denominators, and the paper printed them as though they were one.
    sel = _load('m3a_result_v400.json')
    sns = _load('sens_r11.json')
    pbr = _load('pbaudit_v408', 'p90_pb.json')['rows']
    sel_u, sel_tot = sel['n_units_scored'], sel['n_units_total']
    sel_fine = [s for s in sel['strata'] if s['stratum'].startswith('fine')][0]
    sel_coarse = [s for s in sel['strata']
                  if s['stratum'].startswith('coarse')][0]
    inj_a = set(sns['tags'])
    n_cls_a = sum(1 for r in csv.DictReader(open(os.path.join(
        HERE, 'per_target_results_v3.99.csv'), encoding='utf-8'))
        if r['search_class'] == 'A')
    pb_tags = {r['tag'] for r in pbr}
    sets = dict(selection=set(range(sel_u)), completeness=inj_a, beam=pb_tags)
    if drive == 9:
        pb_tags = set(inj_a)
        sets['beam'] = pb_tags
    ck('S9 the three injection counts are three different campaigns: each is '
       'a proper subset of its own denominator, and no two are the same set',
       sel_u < sel_tot and len(inj_a) < n_cls_a
       and not pb_tags <= inj_a and pb_tags != inj_a,
       'selection %d of %d, completeness %d of %d Class A, beam %d (%d of '
       'them also directly injected)'
       % (sel_u, sel_tot, len(inj_a), n_cls_a, len(pb_tags),
          len(pb_tags & inj_a)))
    m('MkInjSelUnit', '%d' % sel_u)
    m('MkInjSelTotal', '%d' % sel_tot)
    m('MkInjSelFine', '%d' % sel_fine['n_units'])
    m('MkInjSelCoarse', '%d' % sel_coarse['n_units'])
    m('MkInjSelToneFine', '{:,}'.format(sel_fine['n_tones']).replace(',',
                                                                     '\\,'))
    m('MkInjCompWin', '%d' % len(inj_a))
    m('MkInjCompDenom', '%d' % n_cls_a)
    m('MkInjBeamUnit', '%d' % len(pb_tags))
    m('MkInjBeamShared', '%d' % len(pb_tags & inj_a))

    # ----------------------------------------------------------------- out
    OUT = os.path.join(HERE, 'survey_numbers_round%d%s.tex' % (ROUND, suf))
    with open(OUT, 'w') as fh:
        fh.write('%% GENERATED by maskso_v414.py -- do not hand-edit.\n')
        for k in sorted(M):
            fh.write('\\newcommand{\\%s}{%s}\n' % (k, M[k]))
    JS = os.path.join(HERE, 'maskso_v414%s.json' % suf)
    json.dump(dict(generator='maskso_v414.py', drive=drive,
                   so=dict(noted=[r['display'] for r in dec],
                           reason=mf.NOTED_REASON,
                           attributed=len(attr),
                           unattributed=len(LED) - len(attr),
                           rank_leading_unattributed=len(rank),
                           attributed_alt=len(attr_alt),
                           unattributed_alt=len(LED) - len(attr_alt),
                           rank_leading_unattributed_alt=len(rank_alt),
                           species_list_queried=d_list,
                           criteria_fixed=d_crit, holdout_fixed=d_hold,
                           first_reserved_searched=d_first),
                   recurrence=tested + untested,
                   image_sideband=img,
                   injection=dict(
                       selection=dict(units=sel_u, attempted=sel_tot,
                                      fine=sel_fine['n_units'],
                                      coarse=sel_coarse['n_units']),
                       completeness=dict(windows=len(inj_a),
                                         class_A_windows=n_cls_a),
                       beam=dict(units=len(pb_tags),
                                 shared_with_completeness=len(pb_tags
                                                              & inj_a)))),
              open(JS, 'w'), indent=1, sort_keys=True)

    print('maskso_v414 (round %d): %d crossings, %d attributed / %d '
          'unattributed adopted; %d / %d if the coincidences disposed'
          % (ROUND, len(LED), len(attr), len(LED) - len(attr), len(attr_alt),
             len(LED) - len(attr_alt)))
    print('  noted (%s): %s' % ('/'.join(mf.NOTED_SPECIES),
                                ', '.join('%s %+.1f km/s from %s'
                                          % (r['display'],
                                             mf.nearest(r['frame']
                                                        ['f_stellar'],
                                                        TRANS)[2],
                                             mf.nearest(r['frame']
                                                        ['f_stellar'],
                                                        TRANS)[0])
                                          for r in dec)))
    print('  rank-leading unattributed: %d adopted, %d alternative'
          % (len(rank), len(rank_alt)))
    print('  recurrence: %d tested (%d of them bounds), %d untestable; of the '
          'attributed, %d tested / %d recovered / %d not present again / %d '
          'untestable'
          % (len(tested), len(bounded), len(untested), len(att_tested),
             len(recovered), len(att_excl), len(att_untested)))
    for r in sorted(tested + untested, key=lambda z: (z['star'],
                                                      z['freq_GHz'])):
        print('     %-24s %-20s %10.6f  %-12s %s'
              % (r['star'][:24], r['eb'].replace('A002_', ''), r['freq_GHz'],
                 r.get('verdict', '-'),
                 {k: v for k, v in r.items()
                  if k not in ('star', 'eb', 'freq_GHz', 'verdict')}))
    print('  injections: selection %d of %d attempted (%d fine / %d coarse); '
          'completeness %d of %d Class A windows; beam audit %d units, %d '
          'shared'
          % (sel_u, sel_tot, sel_fine['n_units'], sel_coarse['n_units'],
             len(inj_a), n_cls_a, len(pb_tags), len(pb_tags & inj_a)))
    print('  -> %s (%d macros), %s'
          % (os.path.basename(OUT), len(M), os.path.basename(JS)))
    for f in fail:
        print('  ASSERTION FIRED  ' + f)
    print('maskso_v414: %d assertions fired' % len(fail))
    return 1 if fail else 0


if __name__ == '__main__':
    sys.exit(main(sys.argv))
