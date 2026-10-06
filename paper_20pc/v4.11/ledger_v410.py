#!/usr/bin/env python3
r"""The crossing ledger, on the adopted search statistic and in the stellar
frame.

The shipped ledger fragment is keyed to the superseded statistic.  It carries
four crossings that fall below the trigger once the field correction is part
of the statistic, it lacks the one that rises and the one that is restored,
it gives one star two rows where one survives, and its dispositions sum to
the sky-frame attribution count.  It also prints two epoch conventions side
by side, which is a record of how the analysis changed rather than a result.

This generator produces the ledger the paper publishes:

  * one row per crossing of the ADOPTED list -- the released rows, minus the
    four that fall, plus the one that rises, the one that is restored and the
    two the archival tail adds;
  * one epoch convention, the adopted one, so there is no before and after;
  * attribution in the STELLAR frame, which is the frame the Keplerian bound
    that motivates masking is expressed in, so the dispositions sum to the
    adopted attributed/unattributed split and not to the sky-frame one;
  * a machine-readable `ledger.json` that the chain figure reads, so the
    figure and the table cannot disagree.

Every delta term is read from the generated delta fragment and from the
frozen per-crossing records -- none is typed here -- and the closure
`released - fell + rose + restored + added == adopted` is asserted, as is
agreement with the frozen mask result.

    python3 ledger_v410.py [--drive N]

-> ledger.json, tab_ledger.tex, tab_ledgersum.tex
"""
import csv
import glob
import json
import math
import os
import re
import sys

import maskframe_v411 as mf

HERE = os.path.dirname(os.path.abspath(__file__))
MASK_HALF_KMS = mf.MASK_HALF_KMS


def main(argv):
    drive = None
    norecur = '--no-recur' in argv
    for i, a in enumerate(argv):
        if a == '--drive':
            drive = int(argv[i + 1])
    suf = '' if drive is None else '_drive%d' % drive

    OLD = json.load(open(os.path.join(HERE, 'ledger_v403.json')))
    MASKR9 = json.load(open(os.path.join(HERE, 'r9inputs', 'mask_r9.json')))
    ADD = json.load(open(os.path.join(HERE, 'r8inputs', 'v409',
                                      'v409_addprof.json')))['added']
    CAT = list(csv.DictReader(open(os.path.join(
        HERE, 'per_target_results_v3.99.csv'))))
    DELTA = open(os.path.join(HERE, 'tab_crossdelta_v409.tex')).read()
    # ★★★ v4.11, THREE NEW INPUTS, EACH CLOSING A DEFECT OF THE SAME FAMILY.
    #
    # (1) `repaired_v409.csv`: THE ADOPTED STATISTIC, per re-extracted window.
    #     The paper adopts the field-corrected statistic -- that is what makes
    #     four crossings fall and one rise -- and the rows that neither fell
    #     nor rose were still tabulated at their RELEASED value.  BD+05 1668's
    #     four crossings printed 11.87 / 10.14 / 17.52 / 8.78 where the
    #     repaired extraction gives 48.30 / 41.35 / 73.40 / 39.59, a factor
    #     of four, in the same table as HR 1010 at its repaired 5.4097 and
    #     HD 139084 B at 5.7635.  One table, two statistics.
    # (2) `recurcols_v411.json`: the stellar-frame recurrence test, run on
    #     every unattributed crossing with repeat coverage.  Without it the
    #     disposition column says "below rank screen", which disposes of a
    #     crossing on a statistic Appendix B says is not used as evidence --
    #     the exact sentence R2-M5 objects to.
    # (3) `dqflag`: the data-quality disposition, so the five flagged windows
    #     are reported as a failure of one execution block rather than as
    #     ordinary unattributed crossings.  The predicate is the module's,
    #     shared with `statchain_v411`, because two implementations of one
    #     rule is how this project loses numbers.
    import dqflag
    REPAIRED = {}
    with open(os.path.join(HERE, 'repaired_v409.csv')) as _fh:
        for _r in csv.DictReader(_fh):
            if not _r['star_peak_snr_repaired'] or not _r['flo_GHz']:
                continue
            REPAIRED[(_r['eb'], round(float(_r['flo_GHz']), 2),
                      round(float(_r['chanw_Hz'])))] = _r
    # ★★★ v4.11: A TWO-PASS DEPENDENCY, MADE EXPLICIT INSTEAD OF TOLERATED.
    # This generator needs `recurcols_v411.json` for Table 6's recurrence
    # columns, and `recur_v411.py` -- which writes it -- needs `ledger.json`,
    # which this generator writes.  That is a cycle, and the only honest
    # resolutions are to break it or to run two passes.  Two passes, because
    # the rows do not depend on the recurrence test at all: the test is run
    # ON the adopted crossing list.
    #
    #   pass 1   `--no-recur`: writes ledger.json ONLY, so recur_v411.py has
    #            the adopted list to work on.  It does NOT write the table,
    #            because a provisional table on the path the manuscript
    #            \inputs is how a reader ends up with the wrong one.
    #   pass 2   the default: requires recurcols_v411.json and writes the
    #            table.  A MISSING record is a failure here, not a column of
    #            dashes -- a silent degradation would print "---" for every
    #            crossing and read as "never tested".
    if norecur:
        RECURC = {}
    else:
        _rcp = os.path.join(HERE, 'recurcols_v411.json')
        assert os.path.exists(_rcp), (
            'recurcols_v411.json is missing: run `ledger_v410.py --no-recur` '
            'first, then recur_v411.py, then this.  Printing dashes instead '
            'would read as "tested and absent" for every crossing.')
        RECURC = json.load(open(_rcp))
    DQFLAG = dqflag.flags(HERE)
    fail = []

    def ck(name, cond, detail=''):
        if not cond:
            fail.append('%s: %s' % (name, detail))

    # ---- the delta, parsed from the fragment that declares it -------------
    rows = [(a, b, c, e, f, g) for a, b, c, d, e, f, g in re.findall(
        r'^\$([+-])\$\s*&\s*(.+?)\s*&\s*([\d.]+)\s*&\s*(.*?)\s*&\s*'
        r'\$\\to\$\s*&\s*([\d.]+)\s*&\s*(\d+)\s*&\s*(.+?)\s*\\\\$',
        DELTA, re.M)]
    fell = [r for r in rows if r[0] == '-']
    rose = [r for r in rows if r[0] == '+']
    ck('L1 the delta fragment declares both directions',
       len(fell) >= 1 and len(rose) >= 1, (len(fell), len(rose)))
    ck('L2 every falling crossing falls below the trigger and every rising '
       'one rises above it',
       all(float(r[3]) < 5.0 for r in fell)
       and all(float(r[3]) >= 5.0 for r in rose), rows)

    # ---- the stellar-frame record for every released crossing ------------
    # ★★ The frame arithmetic is NOT done here.  It lives in
    # maskframe_v411.py, which this generator imports and the chain figure
    # and the robustness table read back, so the table, the figure and the
    # ladder cannot carry three different velocities for one crossing --
    # which is exactly what they did.  Three things change with it:
    #
    #  (a) the crossing frequency is RECOVERED for the five rows the release
    #      ships without one, by inverting the offset that was computed from
    #      it.  Those rows used to be tabulated at their window's LOWER EDGE,
    #      unmarked, 1150 and 554 km/s from the transition the same row
    #      attributes them to;
    #  (b) the frame is applied as a chain on the frequency -- topocentric to
    #      barycentric at the block's own epoch, then to the stellar rest
    #      frame -- and not as an additive velocity correction, so the table
    #      can print the stellar-frame frequency the offset is measured from;
    #  (c) the systemic velocity comes from the resolver that knows which
    #      value this paper adopts.  The catalogue table still holds the
    #      superseded Gaia DR3 value for beta Pic and this generator was
    #      reading it, which is why the ledger's beta Pic offsets disagreed
    #      with the body text's by 3 km/s.
    XC = {}
    for r in CAT:
        # ★ no f_cross guard: five crossings ship without a crossing
        # frequency, and excluding them here is exactly how they would lose
        # their attribution silently.
        if r['crossing'] != 'True':
            continue
        dv = float(r['line_offset_kms'])
        f_topo = mf.recover_ftopo(r['nearest_line'], r['line_offset_MHz'])
        q = mf.frame_row(r['eb'], r['star_name'], r['flo_GHz'], f_topo)
        q['f_topo_source'] = ('catalogue' if r['f_cross_GHz']
                              else 'recovered from the released offset')
        # ★ keyed on (block, released line offset), not on the frequency:
        # a ledger row whose crossing frequency was never stored carries a
        # window edge in the frequency field, so a frequency key silently
        # misses it and the row falls through to "no stellar offset" --
        # which would move it from attributed to unattributed without
        # anything saying so.
        XC[(r['eb'], round(dv, 3))] = q

    # ★ the catalogue row behind a released ledger row, keyed on (block,
    # released line offset) exactly as XC is -- the only key that works for
    # the five crossings shipped without a crossing frequency.
    _CATX = {}
    for _r in CAT:
        if _r['crossing'] == 'True':
            _CATX[(_r['eb'], round(float(_r['line_offset_kms']), 3))] = _r

    def _catrow(eb, loff):
        return _CATX.get((eb, round(float(loff), 3)))

    # ---- build the adopted list ------------------------------------------
    fell_f = {round(float(r[2]), 6) for r in fell}
    out = []
    for row in OLD['rows']:
        # one released row carries no frequency; it cannot be matched against
        # the delta by frequency, and it is not one of the four that fall.
        _f = None if row['freq'] is None else round(float(row['freq']), 6)
        if _f is not None and _f in fell_f:
            continue
        fr = XC.get((row['eb'], round(float(row['loff']), 3)))
        ck('L3b every released ledger row joins to a frame record',
           fr is not None and fr.get('ok'),
           '%s %s' % (row['star'], row['eb']))
        # ★ THE ADOPTED STATISTIC, not the released one.  The row is matched
        # to the re-extraction on (block, lower window edge, channel width)
        # -- the interval, so a descending spectral window cannot miss --
        # and where the repair touched the window its repaired T_star is
        # what the table prints.  Both values are kept on the row so the
        # table can be checked against the release.
        _cr = _catrow(row['eb'], float(row['loff']))
        _t, _tsrc, _trel = float(row['tstar']), 'released', None
        if _cr is not None:
            _rk = (_cr['eb'], round(min(float(_cr['flo_GHz']),
                                        float(_cr['fhi_GHz'])), 2),
                   round(float(_cr['chanw_Hz'])))
            _rp = REPAIRED.get(_rk)
            if _rp:
                _trel, _t, _tsrc = _t, float(
                    _rp['star_peak_snr_repaired']), 'repaired'
                if drive == 20:
                    # the defect itself: keep the RELEASED value while
                    # recording that a repaired one exists, which is exactly
                    # the state BD+05 1668's four rows were in
                    _t = _trel
        out.append(dict(star=row['star'], display=row['display'],
                        band=row['band'], eb=row['eb'],
                        freq=fr['f_topo'], freq_stellar=fr['f_stellar'],
                        tstar=_t, tstar_released=_trel, tstar_source=_tsrc,
                        screen=row['screen'],
                        rank_ctrl=row['rank_ctrl'], line=fr['line'],
                        line_tex=fr['line_tex'],
                        dq=(bool(DQFLAG.get(dqflag.key(
                            _cr['eb'], _cr['rms_mJy'], _cr['star_snr'])))
                            if _cr is not None else False),
                        dv_stellar=fr['dv_stellar'], frame=fr,
                        source='released'))
    ck('L3 exactly the declared number of rows was removed',
       len(OLD['rows']) - len(out) == len(fell),
       '%d removed against %d declared' % (len(OLD['rows']) - len(out),
                                           len(fell)))

    # the rows the adopted list adds.  Star, frequency, statistic and
    # control count come from the delta fragment; the execution block and
    # the transition come from the frozen per-window records, joined on the
    # frequency, because the fragment does not carry a block name and a
    # name-only join is the defect family this project keeps meeting.
    byf = {}
    for a in ADD:
        byf[round(float(a['fcross']), 4)] = a
    for r in CAT:
        if r['crossing'] == 'True' or not r['f_cross_GHz']:
            continue
    # ★★ The four added rows used to take their offset from whichever frozen
    # record happened to carry one, and those records were NOT all in one
    # frame: the two HD 14055 offsets were stellar-frame, while the risen
    # HR 1010 crossing and the restored HD 139084 B crossing carried
    # TOPOCENTRIC values (-32.0 and +24.3) in a column headed stellar.  All
    # four now go through the same chain as the other 52, which needs each
    # one's own block, window edge and star key -- not a star name parsed out
    # of a LaTeX fragment.
    for sign, star, f_old, t_new, nctrl, note in rose:
        f = round(float(f_old), 6)
        a = byf.get(round(f, 4))
        eb, line, flo, skey = ((a['eb'], a['lines'][0], a['lo'], a['star'])
                               if a else (None, None, None, None))
        if eb is None:
            # the risen crossing is a window the release already carries, so
            # its block is in the catalogue: join on the window that contains
            # the frequency, not on the star name.
            cand = [c for c in CAT
                    if float(c['flo_GHz']) <= f <= float(c['fhi_GHz'])
                    and abs(float(c['eirp_nominal_W'])) > 0
                    and star.replace('~', ' ').replace('$', '')
                    .split()[0].lower() in c['star_name'].lower()]
            if cand:
                eb, line, flo, skey = (cand[0]['eb'], cand[0]['nearest_line'],
                                       cand[0]['flo_GHz'],
                                       cand[0]['star_name'])
        ck('L4 every added crossing resolves to an execution block',
           eb is not None, '%s at %s has no block' % (star, f_old))
        fr = mf.frame_row(eb, skey, flo, f)
        fr['f_topo_source'] = 'adopted list'
        ck('L4b every added crossing resolves to a frame record',
           fr.get('ok'), '%s %s %s' % (star, eb, skey))
        out.append(dict(star=star.replace('~', ' '), display=star,
                        band='7' if f > 300 else '6', eb=eb, freq=f,
                        freq_stellar=fr.get('f_stellar'),
                        tstar=float(t_new), tstar_released=None,
                        tstar_source='repaired', screen=(int(nctrl) == 0),
                        rank_ctrl=None, line=fr.get('line', line),
                        line_tex=fr.get('line_tex'), dq=False,
                        dv_stellar=fr.get('dv_stellar'), frame=fr,
                        source='adopted list'))

    n_rel, n_fell, n_rose = len(OLD['rows']), len(fell), len(rose)
    if drive == 1:
        out = out[:-1]
    ck('L5 the row count closes on the declared delta',
       len(out) == n_rel - n_fell + n_rose,
       '%d rows against %d - %d + %d' % (len(out), n_rel, n_fell, n_rose))

    n_dq = n_norecur = n_nospec = 0
    # ---- dispositions, in the stellar frame ------------------------------
    for row in out:
        d = row['dv_stellar']
        row['attributed'] = (d is not None and abs(d) <= MASK_HALF_KMS)
    n_att = sum(1 for r in out if r['attributed'])
    n_una = len(out) - n_att
    ADOPT = MASKR9['adopted']
    if drive == 2:
        # a crossing LEAVING attribution: the one direction adding a species
        # to the mask cannot produce
        n_att = ADOPT['attributed'] - 1
    # ★★ The crossing COUNT must still close on the frozen one -- that is the
    # delta, and nothing here may change it.  The attributed split must not:
    # the mask now holds sulphur monoxide, and the whole point of adding a
    # species is that a disposition moves.  So the count is asserted and the
    # split is REPORTED against the frozen one, with the direction required:
    # adding transitions can only move crossings from unattributed to
    # attributed, never the other way.
    ck('L6 the ledger reproduces the adopted crossing count',
       len(out) == ADOPT['n_crossings'],
       'ledger %d against %d' % (len(out), ADOPT['n_crossings']))
    ck('L6b adding a species moves crossings only into attribution',
       n_att >= ADOPT['attributed'] and n_una <= ADOPT['unattributed'],
       'ledger %d/%d against the 17-transition mask %d/%d'
       % (n_att, n_una, ADOPT['attributed'], ADOPT['unattributed']))
    nrf = sum(1 for r in out if not r['attributed'] and r['screen'])
    if drive == 3:
        nrf = ADOPT['rank_flagged_unattributed'] + 1
    ck('L7 the rank-flagged unattributed count does not grow',
       nrf <= ADOPT['rank_flagged_unattributed'],
       '%d against %d' % (nrf, ADOPT['rank_flagged_unattributed']))
    # ★ one star contributed two rows under the superseded statistic and
    # contributes one under the adopted one; assert that no star has more
    # rows than it has distinct blocks carrying a crossing, which is the
    # shape of that defect rather than a count of it.
    dup = [k for k, v in
           {(r['star'], r['eb'], round(r['freq'], 4)): 1 for r in out}.items()
           if sum(1 for q in out if (q['star'], q['eb'],
                                     round(q['freq'], 4)) == k) > 1]
    ck('L8 no two ledger rows are the same crossing', not dup, dup)

    # ---- outputs ----------------------------------------------------------
    summ = dict(generator='ledger_v410.py', n_crossings=len(out),
                n_attributed=n_att, n_unattributed=n_una,
                n_rank_flagged_unattributed=nrf,
                frame='stellar', mask_half_kms=MASK_HALF_KMS,
                epoch_conventions=1,
                delta=dict(released=n_rel, fell=n_fell, added=n_rose))
    with open(os.path.join(HERE, 'ledger%s.json' % suf), 'w') as fh:
        json.dump(dict(summary=summ, rows=out), fh, indent=1)
    if norecur:
        print('ledger_v410 (pass 1, --no-recur): ledger%s.json written; the '
              'table is pass 2\'s' % suf)
        for f in fail:
            print('  ASSERTION FIRED  ' + f)
        return 1 if fail else 0
    with open(os.path.join(HERE, 'tab_ledger%s.tex' % suf), 'w') as fh:
        fh.write('%% GENERATED by ledger_v410.py -- do not hand-edit.\n')
        fh.write('%% One row per threshold crossing, one epoch convention, '
                 'stellar-frame attribution.\n')
        # ★ Three frequency columns in place of one, which is what makes the
        # table checkable: the frequency the correlator delivered, the same
        # frequency in the star's rest frame, and the offset from the nearest
        # masked transition measured in that frame.  A reader can now
        # reproduce the third column from the second and a rest frequency.
        # ★★★ v4.11: THE `scr` COLUMN IS GONE AND FOUR RECURRENCE COLUMNS
        # TAKE ITS PLACE.  `scr` was the control rank, printed as a column of
        # the disposition table, which presents the rank as a gate -- and
        # R2-M5 is precisely that the rank must not be presented as a gate,
        # while Appendix B says it is not used as evidence.  The rank has not
        # been hidden: \NUnattrRankFlagged counts it, Fig. 7 annotates it,
        # and the candidate table carries it for the one crossing it decides
        # anything about.  What replaces it is the measurement that DOES
        # dispose of these crossings: the number of covering repeat blocks,
        # the largest statistic found at the predicted stellar-frame cell,
        # the statistic a carrier persisting at the discovery flux would have
        # given, and the resulting exclusion.  One row has none of the four,
        # because its discovery dynamic spectrum was not retained; it prints
        # "---" in all four rather than a zero, which would read as a
        # measured non-detection.
        fh.write('\\begin{tabular}{@{}l@{~}l@{~}c@{~}r@{~}r@{~}r@{~}'
                 'l@{~}r@{~~}r@{~}r@{~}r@{~}l@{}}\n\\hline\n')
        # ★ THREE recurrence columns, not four.  `T_pers` -- the statistic a
        # carrier persisting at the discovery flux would have given -- is
        # dropped on the recurrence owner's own recommendation: with
        # `T_max` and the exclusion beside it, it is the third reading of
        # one measurement, and on the data-quality-flagged rows it prints
        # 850.0 against an exclusion of 849.9.  It stays in
        # `recurcols_v411.json` for the deposit.  Thirteen columns also did
        # not fit: the preamble has twelve, which is how this was found.
        fh.write('Star & block & B & $\\nu_{\\rm topo}$ (GHz) & '
                 '$\\nu_{\\star}$ (GHz) & $T_\\star$ & '
                 'line & $\\Delta v_{\\star}$ & '
                 '$n_{\\rm rep}$ & $T_{\\rm max}$ & '
                 '$\\sigma_{\\rm excl}$ & disposition \\\\\n\\hline\n')
        for r in sorted(out, key=lambda z: (-z['tstar'],)):
            rc = RECURC.get('%s|%.6f' % (r['eb'], r['freq'])) or {}
            notest = rc.get('note') is not None or not rc
            def _c(k, fmt):
                v = rc.get(k)
                return '---' if v is None else fmt % v
            # ★ The disposition keeps the word "attributed" or
            # "unattributed", because the ledger's own summary and
            # `ledgergate` count the typeset column -- a row dispositioned
            # as a data-quality failure is still a crossing no line
            # explains, and dropping the word would have quietly moved four
            # crossings out of the unattributed total.  What it no longer
            # says is "below rank screen".
            if r['attributed']:
                dispo = ('attributed; data-quality flagged' if r['dq']
                         else 'attributed')
            elif r['dq']:
                dispo = 'unattributed; data-quality flagged'
                n_dq += 1
            elif notest:
                dispo = 'unattributed; spectrum not retained'
                n_nospec += 1
            else:
                dispo = 'unattributed; does not recur'
                n_norecur += 1
            fh.write('%s & %s & %s & %.4f & %.4f & %.3f & %s & %s & '
                     '%s & %s & %s & %s \\\\\n'
                     % (r['display'],
                        (r['eb'] or '--').replace('A002_', '')
                        .replace('_', '\\_'),
                        r['band'], r['freq'], r['freq_stellar'], r['tstar'],
                        r['line_tex'] or r['line'] or '--',
                        ('%+.1f' % r['dv_stellar'])
                        if r['dv_stellar'] is not None else '--',
                        _c('n_rep', '%d'), _c('T_max', '%.2f'),
                        _c('excl', '%.1f'), dispo))
        fh.write('\\hline\n\\end{tabular}\n')

    # ★ The mask ladder is NOT emitted here any more.  maskframe_v411.py owns
    # it, because the ladder, this table and the chain figure must come off
    # one set of velocities, and because the paper now PRINTS the ladder
    # instead of asserting in prose that widening the tube changes nothing.

    # ---- the summary table, from the same rows ---------------------------
    # ★ The recurrence line was the literal 0.  It is now counted, and the
    # count is only allowed to stand if every crossing it is a count OVER
    # was actually tested -- otherwise a crossing with no repeat coverage
    # would be silently reported as "did not recur".
    # ★★★ v4.11: THE RECURRENCE LINE IS NOW OVER EVERY UNATTRIBUTED
    # CROSSING, which is R2-M5.  It used to count over the rank-PASSING
    # unattributed rows alone -- two of them -- and the paper then concluded
    # that none of the unattributed crossings recurs, which was a statement
    # about two of thirty-seven.  `recurcols_v411.json` carries the test for
    # all of them: the number of covering repeat blocks, the largest
    # statistic at the predicted stellar-frame cell, and the exclusion.
    _un = [r for r in out if not r['attributed']]
    _rc = {}
    for r in _un:
        _rc[id(r)] = RECURC.get('%s|%.6f' % (r['eb'], r['freq'])) or {}
    _tested = [r for r in _un if _rc[id(r)]
               and _rc[id(r)].get('note') is None]
    _untested = [r for r in _un if r not in _tested]
    n_recur = sum(1 for r in _tested
                  if (_rc[id(r)].get('T_max') or 0.0) >= 5.0)
    if drive == 21:
        _tested = _tested[:-1]
    ck('L9 every unattributed crossing but the declared exceptions was '
       'tested for recurrence in the star own frame, and the recurrence '
       'line counts over exactly those',
       len(_tested) + len(_untested) == len(_un) and len(_untested) <= 1,
       '%d tested + %d untested against %d unattributed'
       % (len(_tested), len(_untested), len(_un)))
    if drive == 22:
        n_recur = 1
    ck('L9b no tested crossing reaches the trigger at its own predicted '
       'cell, which is what "does not recur" in the disposition column '
       'means', n_recur == 0,
       '%d of %d tested reach T_max >= 5' % (n_recur, len(_tested)))
    # ★ and the adopted statistic really is what the table prints: every
    # re-extracted crossing's T_star must be the repaired one, not the
    # released one.  This is the clause BD+05 1668 failed silently.
    _supersed = [(r['display'], r['eb'], r['tstar'], r['tstar_released'])
                 for r in out if r['tstar_released'] is not None
                 and abs(r['tstar'] - r['tstar_released']) < 1e-9]
    ck('L9c every re-extracted crossing is tabulated at its REPAIRED '
       'statistic, which is the one the paper adopts',
       not _supersed, '%d row(s) still carry the released value: %s'
       % (len(_supersed), _supersed[:4]))
    _nrep = sum(1 for r in out if r['tstar_source'] == 'repaired')
    print('ledger_v410: %d of %d rows tabulated at the repaired statistic, '
          '%d of the unattributed tested for recurrence, %d untested'
          % (_nrep, len(out), len(_tested), len(_untested)))
    with open(os.path.join(HERE, 'tab_ledgersum%s.tex' % suf), 'w') as fh:
        fh.write('%% GENERATED by ledger_v410.py -- do not hand-edit.\n')
        fh.write('\\begin{tabular}{@{}lr@{}}\n\\hline\n'
                 'Quantity & Observed \\\\\n\\hline\n')
        for lab, val in (
                ('Threshold crossings', len(out)),
                ('Line-attributed ($|\\Delta v|\\leq%g$\\,km\\,s$^{-1}$, '
                 'stellar frame)' % MASK_HALF_KMS, n_att),
                ('Unattributed', n_una),
                ('\\quad outranking all spatial controls', nrf),
                ('\\quad tested for recurrence in the star\'s own frame',
                 len(_tested)),
                ('\\quad present again at a second epoch', n_recur)):
            fh.write('%s & %d \\\\\n' % (lab, val))
        fh.write('\\hline\n\\end{tabular}\n')

    print('ledger_v410: dispositions -- %d data-quality flagged, %d do not '
          'recur, %d spectrum not retained' % (n_dq, n_norecur, n_nospec))
    print('ledger_v410: %d crossings = %d released - %d fell + %d added; '
          '%d attributed / %d unattributed (stellar frame, +-%g km/s), '
          '%d of the unattributed rank-flagged'
          % (len(out), n_rel, n_fell, n_rose, n_att, n_una, MASK_HALF_KMS,
             nrf))
    for f in fail:
        print('  ASSERTION FIRED  ' + f)
    print('ledger_v410: %d assertions fired' % len(fail))
    return 1 if fail else 0


if __name__ == '__main__':
    sys.exit(main(sys.argv))
