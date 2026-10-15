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
import star_alias


# ★★ A HYPHEN IS NOT A MINUS SIGN.  In text mode `-0.29` typesets U+002D:
# short, raised to x-height and visibly not a minus, and the journal does no
# copy-editing, so the typography of the final PDF is entirely ours.  The
# paper already prints a true minus wherever a value sits inside `$...$`, so
# the same table column carried both conventions.  `\ensuremath{-}` is
# correct in text AND in maths, so a value already inside `$...$` is
# unchanged and a bare one starts printing a minus.
# ★ Applied at the EMIT step and nowhere else: every in-process read of a
# value stays numeric, no use site changes, and no value is altered -- only
# the glyph.  `minuscheck.py` is wired into `gate.sh` and fails the build if
# a hyphen-before-digit is typeset again.
_MINUS = re.compile(r'(?<=[\s&])-(?=\d)')


def _minus(s):
    """Every hyphen that opens a number in a typeset cell, as a minus sign."""
    return _MINUS.sub(r'\\ensuremath{-}', s)


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
    # ★★★★ THE CONTROL MAXIMUM MUST COME FROM THE SAME EXTRACTION AS THE
    # STATISTIC IT STANDS BESIDE.  The adopted statistic is the re-extracted
    # one, and for eight rows it is -- but the control column went on
    # printing the RELEASED ensemble maximum, or a dash.  On BD+05 1668 that
    # put 73.398 beside 19.73 and so stated, in the table's own notation,
    # that the star outran all 512 control positions of its window.  It does
    # not: re-extracted on the same integrations the ensemble peaks at
    # 74.687 and a control still exceeds the star.  Two statistics in one
    # row is not a small error -- it reverses what the row says.
    #
    # Both re-extractions deposit their own 512-position ensemble, so the
    # matched value exists for all eight rows and no dash is needed:
    # `fieldfix_v409.json` for the field-corrected windows and
    # `hd14055_results.json` for the two archival-extension windows.  The
    # join is interval containment on the window's own edges, taken as
    # min/max because a descending spectral window writes them reversed.
    FIELDCTRL = {}
    for _fn, _mk, _nk, _vk, _tag in (
            (os.path.join('r8inputs', 'v409', 'fieldfix_v409.json'),
             'ctrl_max', 'n_ge', 'n_ctrl', 'field-corrected'),
            (os.path.join('r8inputs', 'v409', 'hd14055_results.json'),
             'ctrl', 'nh', 'nctrl', 'archival extension')):
        for _r in json.load(open(os.path.join(HERE, _fn))):
            FIELDCTRL.setdefault(_r['eb'], []).append(
                (min(float(_r['flo']), float(_r['fhi'])),
                 max(float(_r['flo']), float(_r['fhi'])),
                 float(_r[_mk]), int(_r[_nk]), int(_r[_vk]), _tag))

    def _adopted_ctrl(eb, f):
        """The control maximum of the window this crossing sits in, read out
        of the re-extraction the adopted statistic itself comes from.
        Returns None where no re-extracted ensemble exists, so that a caller
        cannot mistake silence for agreement."""
        hit = [c for c in FIELDCTRL.get(eb, [])
               if c[0] - 0.02 <= f <= c[1] + 0.02]
        assert len(hit) <= 1, (
            'the crossing at %.6f GHz in %s falls in %d re-extracted '
            'windows; this join is meant to be unique' % (f, eb, len(hit)))
        return hit[0] if hit else None
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

    # ---- one extraction per row ------------------------------------------
    # Every row tabulated at a re-extracted statistic takes its control
    # maximum from that same re-extraction.  `--drive 26` leaves the
    # released value in place, which is the state the four BD+05 1668 rows
    # and the four added rows were in, and L10 then fires eight times.
    for r in out:
        r['ctrl_source'] = 'released'
        r['ctrl_nge'] = None
        if r['tstar_source'] != 'repaired' or drive == 26:
            continue
        c = _adopted_ctrl(r['eb'], r['freq'])
        if c is not None:
            r['rank_ctrl'], r['ctrl_nge'], r['ctrl_source'] = c[2], c[3], c[5]
    _mixed = [(r['display'], r['eb'], r['tstar'], r['rank_ctrl'],
               r['ctrl_source']) for r in out
              if r['tstar_source'] == 'repaired'
              and r['ctrl_source'] == 'released']
    ck('L10 no row pairs a re-extracted statistic with a control maximum '
       'from a different extraction, and none is left without one',
       not _mixed, '%d row(s): %s' % (len(_mixed), _mixed[:4]))
    # ★ The clause that would have caught the defect in the first place, and
    # it is a check that can fail: the rank verdict the paper publishes and
    # the two numbers it prints must say the same thing.  On the released
    # control column the four BD+05 1668 rows read "does not outrank" beside
    # 73.398 against 19.73, and this fires.
    _disagree = [(r['display'], r['eb'], r['tstar'], r['rank_ctrl'],
                  bool(r['screen'])) for r in out
                 if r['rank_ctrl'] is None
                 or bool(r['screen']) != (r['tstar'] > float(r['rank_ctrl']))]
    ck('L10b every row carries a control maximum, and the published rank '
       'verdict agrees with the two statistics printed beside it',
       not _disagree, '%d row(s): %s' % (len(_disagree), _disagree[:4]))

    n_dq = n_norecur = n_nospec = 0
    # ---- dispositions, in the stellar frame ------------------------------
    for row in out:
        d = row['dv_stellar']
        # ★ The mask coincides with three crossings whose coincidence is
        # reported as a note and not as a disposition, on the physical ground
        # set out in `maskframe_v411`: the species is one no debris disc has
        # been shown to carry, and in the one such window that also covers
        # CO(3-2) that line is absent below the crossing's own flux.  The
        # predicate is on the SPECIES, so it reaches all three alike; the
        # offset itself is printed unchanged, and the counts under the other
        # choice are published beside the adopted ones.
        row['line_note'] = (mf.note_reason(row.get('line'), d)
                            or mf.withheld_reason(row['eb'], row.get('freq')))
        row['line_coincident'] = (d is not None and abs(d) <= MASK_HALF_KMS)
        row['attributed'] = (row['line_coincident']
                             and row['line_note'] is None)
    n_att = sum(1 for r in out if r['attributed'])
    n_una = len(out) - n_att
    ADOPT = MASKR9['adopted']
    if drive == 2:
        n_att = n_att - 1
    # ★★ The crossing COUNT must still close on the frozen one -- that is the
    # delta, and nothing here may change it.  The attributed split may and
    # does move, so it is required to close on its own parts instead.
    ck('L6 the ledger reproduces the adopted crossing count',
       len(out) == ADOPT['n_crossings'],
       'ledger %d against %d' % (len(out), ADOPT['n_crossings']))
    # ★ The mask is a catalogue query of the named species rather than a
    # hand-kept list, so in transitions it is a superset of the frozen one
    # and can only move crossings INTO coincidence.  Coincidence is not
    # disposition: the crossings coincident with the noted species are
    # reported with the offset and disposed of as unattributed, so the
    # attributed count is the coincident count less the noted ones.  Both
    # halves are required, and the noted set must be non-empty -- an empty
    # one would make this arithmetic true of nothing.
    n_coin = sum(1 for r in out if r['line_coincident'])
    n_note = sum(1 for r in out if r['line_note'] is not None)
    ck('L6b the rebuilt mask moves crossings only into coincidence, and the '
       'attributed count is the coincident count less the crossings whose '
       'coincidence is reported as a note',
       n_coin >= ADOPT['attributed'] and n_att == n_coin - n_note
       and n_note >= 1 and len(mf.WITHHELD) == 0,
       'coincident %d, noted %d, attributed %d, unattributed %d, against '
       'the hand-kept mask %d/%d'
       % (n_coin, n_note, n_att, n_una, ADOPT['attributed'],
          ADOPT['unattributed']))
    nrf = sum(1 for r in out if not r['attributed'] and r['screen'])
    nrf_coin = sum(1 for r in out if r['line_note'] is not None
                   and r['screen'])
    nrf_uni = sum(1 for r in out if not r['line_coincident'] and r['screen'])
    if drive == 3:
        nrf_coin = 0
    # ★ The count of unattributed crossings leading their own control fields
    # grows by exactly the noted crossings that lead theirs, and by nothing
    # else -- and it DOES grow, which is why the paper must give the count
    # under both choices and write the sentence in the plural.  The previous
    # form of this check asserted that the count "does not grow", which was
    # right while every coincidence disposed and would now fail only on the
    # correct answer.
    ck('L7 the unattributed crossings leading their own control fields are '
       'the crossings coincident with nothing plus exactly the noted '
       'crossings that lead theirs, and the noted ones change the count',
       nrf == nrf_uni + nrf_coin and nrf_coin >= 1,
       '%d = %d coincident with nothing + %d noted'
       % (nrf, nrf_uni, nrf_coin))
    # ★★ THE RECURRENCE COLUMNS ARE FILLED FOR EVERY TESTABLE CROSSING, NOT
    # ONLY THE UNATTRIBUTED ONES.  The caption says every disposition in the
    # paper can be reproduced from this table, and fifteen attributed rows
    # carried a dash in all five recurrence columns -- two of them rows the
    # appendix does not list as untestable.  The test needs the predicted
    # cell, which needs the stellar-frame frequency and the repeat coverage
    # and nothing else, so it runs on them too.  `maskso_v414` computes it
    # and is imported rather than copied, so the appendix's counts and this
    # table are one computation; where the value available is an upper bound
    # on the statistic at the cell rather than a reading of it, the bound is
    # printed AS a bound.
    if not norecur:
        import maskso_v414
        _extra = maskso_v414.attributed_recurrence(out, RECURC, HERE)
        if drive == 23:
            _extra = {}
        _before = len(RECURC)
        RECURC = dict(RECURC, **_extra)
        _blank = [(r['display'], r['eb'], round(r['freq'], 4))
                  for r in out
                  if (RECURC.get('%s|%.6f' % (r['eb'], r['freq'])) or {})
                  .get('n_rep') is None]
        ck('L7b every crossing with a covering repeat window carries the '
           'recurrence test in this table, and the rows that do not are '
           'named rather than left as a dash nobody has to explain',
           len(RECURC) > _before and len(_blank) <= 4,
           '%d rows without a recurrence measurement: %s'
           % (len(_blank), _blank))
    # ★ one star contributed two rows under the superseded statistic and
    # contributes one under the adopted one; assert that no star has more
    # rows than it has distinct blocks carrying a crossing, which is the
    # shape of that defect rather than a count of it.
    dup = [k for k, v in
           {(r['star'], r['eb'], round(r['freq'], 4)): 1 for r in out}.items()
           if sum(1 for q in out if (q['star'], q['eb'],
                                     round(q['freq'], 4)) == k) > 1]
    ck('L8 no two ledger rows are the same crossing', not dup, dup)
    # ★★ v4.12.  `numbers_v410.py` counts the same split from the released
    # catalogue plus the delta, and publishes it as \NAttributed and
    # \NUnattributed.  Two implementations of one number is this project's
    # commonest defect, so the published pair is read back and required to be
    # this one.  The check lives here because this generator runs after that
    # one; the reverse direction would be a stale read.
    def _pub(nm):
        import glob as _g
        v = None
        for f in sorted(_g.glob(os.path.join(HERE, 'survey_numbers*.tex'))):
            for mm in re.finditer(
                    r'\\(?:new|renew|provide)command\{\\%s\}\{([0-9]+)\}' % nm,
                    open(f, errors='ignore').read()):
                v = int(mm.group(1))
        return v
    _pa, _pu, _pr = (_pub('NAttributed'), _pub('NUnattributed'),
                     _pub('NUnattrRankFlagged'))
    if drive == 4:
        _pa = (_pa or 0) + 1
    ck('L8b the attributed split this ledger closes on is the one the macro '
       'layer publishes',
       (_pa, _pu, _pr) == (n_att, n_una, nrf)
       or (_pa is None and _pu is None),
       'published %s/%s/%s against ledger %d/%d/%d'
       % (_pa, _pu, _pr, n_att, n_una, nrf))

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
    # ★★★ GLENN, 2026-10-06: "THE BOTTOM OF TABLE 9 ON PAGE 25 OVERLAPS WITH
    # TEXT."  It did, and nothing in the build could see it: a float too tall
    # for its page is an `Overfull \vbox`, which pdflatex reports as a
    # WARNING and which every gate here ignored.  The cause is structural --
    # a `table*` float cannot break across pages, and this one is a row per
    # threshold crossing, so it grows with the survey.  Nudging the float, or
    # shrinking the type until it happened to fit, would have left the next
    # crossing to put it back.
    #
    # So the table is emitted in PARTS, each short enough to fit a page with
    # its caption, and the section places each part in its own float with a
    # "continued" caption.  The split is made here, where the row count is
    # known, and the cap is asserted: if the ledger ever outgrows the parts
    # the build STOPS and names the fix, instead of a reader finding the
    # table written over the text underneath it.
    #
    # ★★★★ r18, AND THE REASON THE SPLIT IS NOW ONE PART AGAIN.  A
    # `sidewaystable*` occupies a WHOLE PAGE whatever its row count, so two
    # parts cost two pages for 56 rows that need 464 pt of a page's 513.  Two
    # measurements settle it, both taken on the real build:
    #   * the rotated float's own budget is the page WIDTH, 513.12 pt, and a
    #     row of this table at \scriptsize is 8.2 pt of it.  Header, rules and
    #     a two-line caption take 48 pt, so 56 rows need 507 pt: it fits, on
    #     one page, with nothing shrunk and no row dropped;
    #   * the two-part build was ALSO over its budget and nobody could see it.
    #     `rotating` centres a sideways double float in \hsize, and under this
    #     revtex-derived class \hsize is the COLUMN width at that point, so
    #     part one was centred on column one and its 19-line caption ran off
    #     the left edge of the paper with words missing from every line.  That
    #     is fixed in the preamble (`\end@rotdblfloat`, patched), and
    #     `rotfit_r18.py` now fails the build on any ink outside the text
    #     block of a landscape page, so the next overrun is a failure and not
    #     a reader's discovery.
    # The caption's method prose moved into Appendix D's own text with this
    # change, which is what makes a two-line caption honest rather than thin.
    #: rows per float.  Measured as above: 56 rows of 8.2 pt plus 48 pt of
    #: header, rules and caption against 513.12 pt of page width.  The cap is
    #: 57 and not 60 BECAUSE it is measured: at 58 rows the table reaches the
    #: margin, and the fix then is to restore the second part file and its
    #: float -- not to raise this number, and not to shrink the type, which
    #: `tabfloor_r17.py` refuses below 6.5 pt in any case.
    ROWS_PER_PART = 57
    PART_FILES = ['tab_ledger%s.tex' % suf]
    _body = sorted(out, key=lambda z: (-z['tstar'],))
    _parts = [_body[i:i + ROWS_PER_PART]
              for i in range(0, len(_body), ROWS_PER_PART)] or [[]]
    assert len(_parts) <= len(PART_FILES), (
        'the crossing ledger has grown to %d rows, which needs %d floats and '
        'this generator writes %d.  Restore the second part file here AND a '
        'second float in sections/app_J_falsealarm.tex -- do not raise '
        'ROWS_PER_PART, which is what makes the table overrun its page, and '
        'do not shrink the type.'
        % (len(_body), len(_parts), len(PART_FILES)))
    assert all(len(p) <= ROWS_PER_PART for p in _parts)
    while len(_parts) < len(PART_FILES):
        _parts.append([])

    # ★★★★ v4.21: THE TYPESET COLUMN CARRIES A CODE AND THE DATA FILE CARRIES
    # THE WORDS.  Seven distinct strings occupied 96.41 pt of a table that
    # needed 109.7 pt taken out of it, and the legend belongs in Section D.5,
    # which already defines every column here.
    # ★ THE CODES ARE CHOSEN SO THAT THE ATTRIBUTED/UNATTRIBUTED DISTINCTION
    # IS A PREFIX: every attributed row starts `A` and every unattributed row
    # starts `U`, which is what keeps this generator's own summary and
    # `ledgergate`'s G3 able to count the column -- dropping the word would
    # quietly move four crossings out of the unattributed total, and a prefix
    # test preserves exactly the distinction that note protects.
    # ★ The flag is `AF`/`UF` and NOT a dagger: this table already prints
    # `$^{\dagger}$` in the $\Delta v_\star$ column for a different fact, and
    # one mark meaning two things in one table is how a reader is misled by
    # something nobody typed wrongly.
    # ★★ r20-final: the words and the codes are declared HERE, above the
    # sample's selection, because that selection has to know a row's
    # disposition in order to lead with the rows that matter.  The row loop
    # below calls the same function.
    DISPO_CODE = {'attributed': 'A',
                  'attributed; recurs': 'AR',
                  'attributed; not recovered': 'AN',
                  'attributed; flagged': 'AF',
                  'unattributed; no recurrence': 'U',
                  'unattributed; no spectrum': 'US',
                  'unattributed; flagged': 'UF'}

    def _dispo_words(r_, rc_, notest_):
        """The disposition of one composed row, in words.

        The words are the ledger's own and are what the machine-readable file
        carries; `DISPO_CODE` turns them into the typeset column.
        """
        if r_['attributed']:
            return ('attributed; flagged' if r_['dq']
                    else 'attributed; recurs'
                    if rc_.get('verdict') == 'recovered'
                    else 'attributed; not recovered'
                    if rc_.get('verdict') == 'absent'
                    else 'attributed')
        if r_['dq']:
            return 'unattributed; flagged'
        if notest_:
            return 'unattributed; no spectrum'
        return 'unattributed; no recurrence'

    # ★★★★ v4.21, r20-final: THE ARTICLE NOW PRINTS THIS SAMPLE AND THE FULL
    # LEDGER IS ATTACHED AS DATA.  The fragment was written in r18 for exactly
    # this build and sat `\input` by nothing for two rounds; the length pass of
    # round 20 measured the full table out of the typeset article (the two
    # tables it took out are worth one page between them), and what stays
    # behind is this sample plus the machine-readable ledger in `anc/`, which
    # is not refereed and is not part of the article.  Every row of all
    # \EvNCrossRaw{} crossings is still a row of a file that ships with the
    # paper, and the full LaTeX table is still generated, so restoring it to
    # the article is one `\input` and a caption.
    # It is written from the same composed rows and through the same row
    # formatter as the full table, because the alternative -- a second
    # generator, or a hand-copied fragment -- is how a sample ends up
    # disagreeing with the table it is a sample of.  It is a SAMPLE and not a
    # PART: `_written` below counts the parts only, so the
    # "every crossing typeset exactly once" assertion still means what it
    # says, and `ledgergate.py` and `census_r12.py` name the two part files
    # explicitly rather than globbing, so neither can mistake this for one.
    #
    # ★★★★ AND THE SAMPLE IS NO LONGER "THE FIRST EIGHT ROWS".  Ordered by
    # $T_\star$ the first rows are four crossings of the one block that fails
    # the quality criterion and four CO rows of one star -- a reader meeting
    # the ledger through them learns nothing about the two events that lead
    # their own control fields or the handful the recurrence test cannot
    # reach, which are the rows every disposition in the paper turns on.  So
    # the selection is COMPUTED, in three groups, and it leads with the rows
    # that matter:
    #   (1) the unattributed crossings that lead their own control fields --
    #       the same predicate as `nrf` above, which is \EvNRankQp;
    #   (2) the crossings with no recurrence reading at all, which are the
    #       rows L7b names rather than leaves as a dash;
    #   (3) enough of the remaining rows, in the table's own order, that every
    #       disposition code the ledger uses appears in the sample, so the
    #       legend in Sec. D.5 describes nothing a reader cannot see.
    # Nothing here is a list of names: each group is a predicate over the
    # composed rows, so a sample row cannot survive the measurement that put
    # it there changing.
    SAMPLE_FILE = 'tab_ledgersample%s.tex' % suf

    def _rc_of(r_):
        return RECURC.get('%s|%.6f' % (r_['eb'], r_['freq'])) or {}

    def _dispo_of(r_):
        rc_ = _rc_of(r_)
        return DISPO_CODE[_dispo_words(
            r_, rc_, rc_.get('note') is not None or not rc_)]

    _lead = [r for r in _body if not r['attributed'] and r['screen']]
    _untest = [r for r in _body if _rc_of(r).get('n_rep') is None]
    _pick, _ids = [], set()

    def _add(r_):
        if id(r_) not in _ids and len(_pick) < 10:
            _ids.add(id(r_))
            _pick.append(r_)

    for _r in _lead + _untest:
        _add(_r)
    _NLEADUNTEST = len(_pick)
    for _r in _body:                      # group 3, in the table's own order
        if {_dispo_of(x) for x in _pick} >= {_dispo_of(x) for x in _body}:
            break
        if _dispo_of(_r) not in {_dispo_of(x) for x in _pick}:
            _add(_r)
    SAMPLE_ROWS = len(_pick)
    assert 5 <= SAMPLE_ROWS <= 10, SAMPLE_ROWS
    assert SAMPLE_ROWS <= len(_body), (SAMPLE_ROWS, len(_body))
    # ★ The three groups are asserted, not assumed, and each assertion is the
    # invariant rather than the count this run happens to give.
    assert len(_lead) == nrf and _lead == _pick[:len(_lead)], (
        'the sample must lead with the %d unattributed crossings that lead '
        'their own control fields' % nrf)
    assert all(id(r) in _ids for r in _untest), (
        'every crossing with no recurrence reading must be in the sample: '
        '%d of them, %d sample rows' % (len(_untest), SAMPLE_ROWS))
    assert ({_dispo_of(r) for r in _pick} == {_dispo_of(r) for r in _body}), (
        'the sample must show every disposition code the ledger uses: %r '
        'against %r' % (sorted({_dispo_of(r) for r in _pick}),
                        sorted({_dispo_of(r) for r in _body})))
    # ★★★ AND THE SAMPLE CARRIES TEN OF THE FIFTEEN COLUMNS, UPRIGHT.
    # MEASURED, not chosen: the full ledger is fifteen columns and 605 pt wide
    # at \scriptsize against a page's 513 pt, which is why it is set
    # landscape -- and a `sidewaystable*` occupies a WHOLE PAGE whatever its
    # row count, so an eight-row sample set the same way costs the paper the
    # page the relocation was meant to save (measured: 27 pp with it, 26
    # without).  \tiny would fit upright and is refused by `tabfloor_r17.py`'s
    # 5.95 pt floor, correctly.  So the sample shows the columns that identify
    # a crossing and dispose of it, the caption says which are left out, and
    # the full table with every column is the online one.  The five dropped
    # are the recurrence test's own readings (n_rep, dt, T_pers, T_rep,
    # sigma_excl), which are the ones a reader checks against the exclusion
    # rather than reads a crossing from.
    # ★ v4.21: RENUMBERED with the header, which lost `$\nu_\star$` (old
    # index 4) -- this tuple indexes `_HEAD` and filters the header, the
    # alignment and every row by the same object, so leaving it alone would
    # have silently printed the disposition under `$\sigma_{\rm excl}$`.
    # ★★★★ r20-final: THE BLOCK IDENTIFIER (old index 1) IS OUT OF THE
    # PRINTED SAMPLE, AND THE REASON IS MEASURED.  With all nine columns the
    # sample is 298.0 pt wide at `\scriptsize` against a column's 245.27, so
    # it can only be set as a full-width `table*` -- and a full-width float
    # here costs the paper a whole page (37 against 36, measured both ways,
    # with every other difference held fixed), because a `table*` can sit
    # only at the top of a page and the text it displaces does not pack back
    # in.  Dropping the block takes the tabular to 238.8 pt, which fits a
    # single column with 6.5 pt to spare; `line` instead leaves it 2.7 pt too
    # wide even with the gaps halved, and nothing else is big enough.
    # ★ It is the right column to lose of the two: the block is the ARCHIVE
    # KEY, not evidence about the crossing, and it is still in the ancillary
    # ledger for all \EvNCrossRaw{} rows, in Table 5 for the two events that
    # lead their own control positions, and in Table D2 for every recovery.
    # What stays is every column a reader disposes of a crossing with.
    SAMPLE_COLS = (0, 2, 3, 4, 5, 6, 7, 13)

    _written = 0
    _mr = []                              # the machine-readable ledger's rows
    for _ipart, (_fn, _rows) in enumerate(
            list(zip(PART_FILES, _parts))
            + [(SAMPLE_FILE, _pick)]):
      _issample = _fn == SAMPLE_FILE
      with open(os.path.join(HERE, _fn), 'w') as fh:
        fh.write('%% GENERATED by ledger_v410.py -- do not hand-edit.\n')
        fh.write('%% One row per threshold crossing, one epoch convention, '
                 'stellar-frame attribution.\n')
        if _issample:
            fh.write('%%%% %d rows of %d: the %d unattributed crossings that '
                     'lead their own control fields, then the %d with no '
                     'recurrence reading, then enough of the rest, in the '
                     'full table\'s own order, to show every disposition '
                     'code.  This is the fragment the article prints; the '
                     'full %d-row ledger accompanies it as data.\n'
                     % (len(_rows), len(_body), len(_lead), len(_untest),
                        len(_body)))
        else:
            fh.write('%%%% part %d of %d, %d rows; the split is made in the '
                     'generator so the float cannot outgrow its page.\n'
                     % (_ipart + 1, len(PART_FILES), len(_rows)))
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
        # ★ Sixteen columns, and the preamble is BUILT FROM THE HEADER
        # rather than typed beside it.  This table grew from twelve columns
        # to sixteen in one change, and a preamble one specifier short of
        # its header is an "extra alignment tab" on row one and nothing
        # else -- a whole-table failure from a single missing letter.
        # ★★★ The header is now a LIST, and the preamble is built from it, so
        # that the comment above is true of the code rather than only of the
        # intention.  It was not: `_ALIGN` was a typed literal of 14 letters
        # sitting beside a header of 15 cells, and the assertion below
        # compared it against the literal 14 instead of against the header --
        # so the check whose stated job was "one specifier per header cell"
        # could not fail when a column was added, and in fact FROZE the error
        # in place.  A column was added; the table then failed to compile at
        # all, which is the cheapest possible outcome and the only reason it
        # was caught.  Add a column by adding a (title, alignment) pair here
        # and nowhere else.
        _HEAD = [('Star', 'l'),
                 ('block', 'l'),
                 ('B', 'c'),
                 (r'$\nu_{\rm topo}$ (GHz)', 'r'),
                 # ★★ v4.21: `$\nu_\star$` IS GONE FROM THE TYPESET TABLE AND
                 # NOT FROM THE DATA.  It follows from `nu_topo`, `line` and
                 # `$\Delta v_\star$`, which are the three columns beside it
                 # -- that derivability is why Eq. B1 can be recomputed across
                 # this table at all -- and `nu_star_GHz` is a column of the
                 # ancillary `si_ledger.txt` in its own right.  Dropping it is
                 # 30.16 pt of the 109.7 pt that lets all 56 rows stand
                 # upright in a two-column float instead of rotated on a page
                 # of their own.
                 (r'$T_\star$', 'r'),
                 (r'$T_{\rm ctrl}$', 'r'),
                 ('line', 'l'),
                 (r'$\Delta v_{\star}$', 'r'),
                 (r'$n_{\rm rep}$', 'r'),
                 (r'$\Delta t$ (d)', 'r'),
                 (r'$T_{\rm pers}$', 'r'),
                 (r'$T_{\rm rep}$', 'r'),
                 (r'$\sigma_{\rm excl}$', 'r'),
                 ('disp.', 'l')]
        # ★ r18: the sample keeps SAMPLE_COLS of these, in this order, and
        # the header, the alignment and every row are filtered by the same
        # tuple, so a column cannot be dropped from one of the three and kept
        # in the others.
        _NFULL = len(_HEAD)               # cells the row formatter writes
        _KEEP = (tuple(range(_NFULL)) if not _issample else SAMPLE_COLS)
        assert list(_KEEP) == sorted(set(_KEEP)) and _KEEP[-1] < len(_HEAD), (
            'the sample columns must be a strictly increasing subsequence of '
            'the header: %r' % (_KEEP,))
        _HEAD = [_HEAD[i] for i in _KEEP]
        _ALIGN = ''.join(a for _, a in _HEAD)
        # ★ The gap between columns is set in ems, so it grows with the type
        # instead of staying where a narrower setting left it.  At 0.9 pt it
        # was the width of a thin space -- the same gap `\,` puts INSIDE a
        # value -- so a reader had nothing to tell a column boundary from a
        # space, and `0.9--113 n/a +0.15 n/a` ran together as one field.
        # 0.33 em is twice the thin space and half an interword space, which
        # is what `tabfloor_r17.py` measures between the printed tokens of
        # every row of this table.  The ledger is landscape, so the width
        # this costs (14 gaps, about 20 pt) is available.
        fh.write('\\begin{tabular}{@{}'
                 + '@{\\hspace{0.33em}}'.join(_ALIGN) + '@{}}\n\\hline\n')
        # ★★★ v4.12, R1's definitive ledger: every rejection reproducible
        # from one table.  Three things were missing and one was ambiguous.
        #
        #  * `T_ctrl`, the largest statistic among the window's control
        #    positions.  R1 asks for "the spatial-rank result", and this is
        #    that result as a measurement rather than as a verdict: a reader
        #    compares it with $T_\star$ in the column beside it and sees for
        #    himself whether the star led.  Nothing in the paper turns on it.
        #  * `\Delta t`, the interval over which recurrence was tested.
        #    Without it "does not recur" has no time attached, and the
        #    intervals run from an hour to nearly two years.
        #  * `T_{\rm pers}`, the statistic a carrier persisting at the
        #    discovery flux would have produced at the predicted cell.  It
        #    was dropped once as a third reading of one measurement; it is
        #    back because the exclusion cannot be checked without it.
        #  * ★★ `T_{\rm max}` was AMBIGUOUS, and that is R2-M7's second
        #    bullet.  It held the MATCHED-drift statistic while the event
        #    table printed the ALL-DRIFT maximum under the same words, so
        #    the two tables disagreed by a factor of two on both events.
        #    Both are now printed, in both tables, under names that say
        #    which is which.  ★ Only the MATCHED value is a column here:
        #    sixteen columns did not fit a two-column page, and the
        #    all-drift maximum is a maximum over about 120 trials that
        #    cannot be read beside a trigger as though it were one
        #    measurement.  It is published for both rank-leading events in
        #    their own table, as a survey-wide maximum in the text, and for
        #    every crossing in `recurcols_v411.json`.
        fh.write(' & '.join(t for t, _ in _HEAD) + ' \\\\\n\\hline\n')
        # The alignment and the header are now the same object, so this can
        # only fail if a row disagrees with them -- which is the comparison
        # worth making.  Checked against the body below, not against a number.
        assert len(_ALIGN) == len(_HEAD), 'one specifier per header cell'
        for r in _rows:
            rc = RECURC.get('%s|%.6f' % (r['eb'], r['freq'])) or {}
            notest = rc.get('note') is not None or not rc
            # ★★ R2-M7, FOURTH BULLET, AND THE REFEREE IS RIGHT.  One
            # execution block is declared defective on its own control
            # statistics, and its four crossings were nevertheless
            # published with exclusions of 849.9 and 487.7 sigma.  An
            # exclusion is the discovery amplitude divided by the combined
            # noise of the repeats, so it inherits the discovery
            # amplitude -- and that amplitude comes from the block we call
            # broken.  Both quantities that use it, $T_{\rm pers}$ and the
            # exclusion, are therefore withheld on those rows.  The repeat
            # measurements themselves are sound and are still printed:
            # they are made on other blocks.
            dqhide = bool(r['dq'])

            # ★ Where the repeat reading is a window maximum rather than a
            # reading at the predicted cell, it bounds the statistic there
            # from above and the exclusion from below.  Both are printed as
            # inequalities, because a bound set in a column of measurements
            # without a sign is a measurement as far as any reader is
            # concerned.
            _bnd = {'T_rep': '$<$', 'excl': '$>$'} if rc.get('bound') else {}

            def _c(k, fmt, hide=()):
                v = rc.get(k)
                if k in hide:
                    return 'n/a'
                return '--' if v is None else _bnd.get(k, '') + fmt % v

            def _dt():
                a, b = rc.get('dt_min_d'), rc.get('dt_max_d')
                # ★★ A SEPARATION IS NEVER PRINTED AS A ZERO, AND ONE THE
                # ARCHIVE DOES NOT RECORD IS NEVER PRINTED AS A NUMBER.  At
                # one decimal a measured 0.019 d -- 27 minutes, a real
                # within-session repeat -- printed as "0.0", which reads as no
                # interval at all; and the same "0.0" stood for an interval
                # that is not recorded anywhere.  Two decimals below a tenth
                # of a day, and the unrecorded repeats carry a dagger.
                u = '$^{\\ddagger}$' if rc.get('dt_unrec') else ''
                if a is None or b is None:
                    return 'n/r' if u else '--'
                f = (lambda x: ('%.2f' % x) if x < 0.1
                     else ('%.1f' % x) if x < 10 else '%.0f' % x)
                return (f(a) if abs(b - a) < 0.005
                        else '%s--%s' % (f(a), f(b))) + u
            # ★ The disposition keeps the word "attributed" or
            # "unattributed", because the ledger's own summary and
            # `ledgergate` count the typeset column -- a row dispositioned
            # as a data-quality failure is still a crossing no line
            # explains, and dropping the word would have quietly moved four
            # crossings out of the unattributed total.  What it no longer
            # says is "below rank screen".
            # ★★ r18: THE THREE COUNTERS ARE GUARDED BY `_issample`.  The
            # sample float is written by a second turn of this same loop over
            # the first rows of the body, so an unguarded `+= 1` here would
            # count those rows twice and the three dispositions printed at the
            # end of the run would be wrong by the sample's content -- a
            # counter incremented in a loop that now runs one extra time is
            # this project's commonest shape of defect, and it is guarded
            # rather than hoped about.
            # ★★ r20-final: THE WORDS COME FROM `_dispo_words` ABOVE, which the
            # sample's own selection calls as well.  Two implementations of one
            # disposition -- one for the table, one for the selection that
            # decides which rows of it the article prints -- is the shape of
            # defect this project has met oftenest; there is one.
            _count = not _issample
            dispo = _dispo_words(r, rc, notest)
            if dispo == 'unattributed; flagged':
                n_dq += _count
            elif dispo == 'unattributed; no spectrum':
                n_nospec += _count
            elif dispo == 'unattributed; no recurrence':
                n_norecur += _count
            # ★★★★ v4.21: THE TYPESET COLUMN CARRIES A CODE AND THE DATA FILE
            # CARRIES THE WORDS.  Seven distinct strings occupied 96.41 pt of
            # a table that needed 109.7 pt taken out of it, and the legend
            # belongs in Section D.5, which already defines every column here.
            # ★ THE CODES ARE CHOSEN SO THAT THE ATTRIBUTED/UNATTRIBUTED
            # DISTINCTION IS A PREFIX: every attributed row starts `A` and
            # every unattributed row starts `U`, which is what keeps this
            # generator's own summary and `ledgergate`'s G3 able to count the
            # column -- the standing note below this block says that dropping
            # the word would quietly move four crossings out of the
            # unattributed total, and a prefix test preserves exactly the
            # distinction that note protects.
            # ★ The flag is `AF`/`UF` and NOT a dagger: this table already
            # prints `$^{\dagger}$` in the $\Delta v_\star$ column for a
            # different fact, and one mark meaning two things in one table is
            # how a reader is misled by something nobody typed wrongly.
            dispo_tex = DISPO_CODE[dispo]
            assert dispo_tex.startswith('A') == bool(r['attributed']), (
                'the code must carry the attribution as its first letter: '
                '%r for attributed=%r' % (dispo_tex, r['attributed']))
            # Withheld on the flagged rows -- NOT because of the block,
            # which is the reason the caption used to give and which does
            # not apply to the HD 48370 row: the predicate is the WINDOW
            # flag (`dqflag`), and in a window whose control ring stands as
            # high as its star the discovery amplitude cannot be assigned to
            # a point source there, so T_pers and the exclusion built from
            # it are not measurements of a carrier.  Also withheld on the
            # recovered rows, where the exclusion is not formed at all
            # because what it would exclude has just been observed.
            _hide = (('T_pers', 'excl')
                     if dqhide or rc.get('verdict') == 'recovered' else ())
            # ★★★ r18, REFEREE 2's MINOR 11: THE MACHINE-READABLE LEDGER IS
            # ACCUMULATED HERE, in the loop that writes the typeset one, from
            # the same composed row and the same disposition.  The referee
            # asks for the ledger as a machine-readable supplementary table so
            # that the paper's counts can be checked against it; a second
            # generator reading the same inputs could answer that and then
            # drift from the table, and a parser of the typeset LaTeX would
            # have to undo \ensuremath, the dagger and the inequality signs.
            # A withheld value is written as an EMPTY field and not as a zero,
            # exactly as the typeset table prints "n/a" rather than 0.0.
            # ★★★★ v4.22: THE STAR COLUMN OF A DEPOSITED FILE IS A KEY, SO IT
            # IS THE PLAIN DESIGNATION AND NOT THE TYPESET STRING.  This
            # column used to be `r['display']`, which carries LaTeX
            # (`$\beta$~Pic`, `CP$-$72 2713`) and carries ONE star under TWO
            # spellings -- `HD 14055` and `HD~14055` typeset identically and
            # are two keys to any program, so grouping the 56 rows by star
            # returned 6 and 2 where the paper states 8, and the file could
            # not be joined to the per-window catalogue at all.  Written from
            # the export's own string through `star_alias.designation`, which
            # is the same function the catalogue's column is written with, and
            # checked against the de-TeX of the string the page prints (L14).
            _star_plain = star_alias.designation(r['star'], tex=False)
            if drive == 28:            # the defect itself, both halves of it
                _star_plain = r['display']
            if not _issample:
                _mr.append(dict(
                    star=_star_plain, eb=r['eb'] or '', band=r['band'],
                    nu_topo_GHz='%.6f' % r['freq'],
                    nu_star_GHz='%.6f' % r['freq_stellar'],
                    T_star='%.4f' % r['tstar'],
                    T_ctrl=('' if r['rank_ctrl'] is None
                            else '%.4f' % float(r['rank_ctrl'])),
                    line=r['line'] or '',
                    dv_star_kms=('' if r['dv_stellar'] is None
                                 else '%+.3f' % r['dv_stellar']),
                    mask_coincident_not_attributed=(
                        '1' if (r['line_note'] and r['line_coincident'])
                        else '0'),
                    n_rep=('' if rc.get('n_rep') is None
                           else '%d' % rc['n_rep']),
                    dt_min_d=('' if rc.get('dt_min_d') is None
                              else '%.3f' % rc['dt_min_d']),
                    dt_max_d=('' if rc.get('dt_max_d') is None
                              else '%.3f' % rc['dt_max_d']),
                    # ★★ v4.22: THE MARK THE APPENDIX PROMISES, IN THE FILE
                    # THAT IS PROMISED TO CARRY IT.  Table D2's caption said
                    # "the ledger carries the same mark on those" and the
                    # deposited ledger had no such field -- the typeset
                    # sample has no $\Delta t$ column at all, so the promise
                    # was true nowhere.  It is a column here rather than a
                    # deleted clause, because a reader joining the file needs
                    # to know which of these intervals is measured from an
                    # observing unit's stamp and which from a block's own.
                    dt_from_unit_stamp=(
                        '0' if drive == 29
                        else ('1' if rc.get('dt_unrec') else '0')),
                    T_pers=('' if ('T_pers' in _hide
                                   or rc.get('T_pers') is None)
                            else '%.3f' % rc['T_pers']),
                    T_rep=('' if rc.get('T_rep') is None
                           else '%+.4f' % rc['T_rep']),
                    T_rep_is_upper_bound='1' if rc.get('bound') else '0',
                    sigma_excl=('' if ('excl' in _hide
                                       or rc.get('excl') is None)
                                else '%.3f' % rc['excl']),
                    attributed='1' if r['attributed'] else '0',
                    quality_flagged='1' if r['dq'] else '0',
                    disposition=dispo))
            _fmt = ('%s & %s & %s & %.4f & %.3f & %s & %s & %s & '
                    '%s & %s & %s & %s & %s & %s \\\\\n')
            # ★ The row format must carry one field per header cell.  Checked
            # against the header itself, every row, because the failure this
            # replaces was a format string and a header that disagreed by one
            # and an assertion that compared neither of them to the other.
            assert _fmt.count('&') + 1 == _NFULL, (
                'row format has %d cells, header has %d'
                % (_fmt.count('&') + 1, _NFULL))
            _row = (_minus(_fmt
                     % (r['display'],
                        (r['eb'] or '--').replace('A002_', '')
                        .replace('_', '\\_'),
                        r['band'], r['freq'], r['tstar'],
                        ('--' if r['rank_ctrl'] is None
                         else '%.2f' % float(r['rank_ctrl'])),
                        r['line_tex'] or r['line'] or '--',
                        # ★ A row inside the mask and still unattributed
                        # needs its reason on the page.  Three crossings sit
                        # within a few km/s of a transition and are not
                        # attributed, because the species is one the paper
                        # reports and does not act on; unmarked, the
                        # Delta v column and the disposition column read as a
                        # contradiction.  The mark is placed from
                        # `line_note`, the same predicate that decides the
                        # disposition, so the two cannot drift apart.
                        '--' if r['dv_stellar'] is None
                        else ('%+.1f$^{\\dagger}$' % r['dv_stellar']
                              if r['line_note'] and r['line_coincident']
                              else '%+.1f' % r['dv_stellar']),
                        _c('n_rep', '%d'), _dt(),
                        _c('T_pers', '%.1f', _hide),
                        # ★ The inverse-variance COMBINATION of the repeat
                        # epochs, not the maximum over them.  The column used
                        # to print `T_matched`, whose null is the null of a
                        # maximum and so sits above zero by construction --
                        # that is the whole of the +1.13 offset the table
                        # appeared to show.  `T_matched_max` keeps the maximum
                        # under a name that says what it is.
                        _c('T_rep', '%+.2f'),
                        _c('excl', '%.1f', _hide), dispo_tex)))
            # ★ One row, written whole and then FILTERED BY `_KEEP`, so the
            # sample's cells are literally the full table's cells and not a
            # second formatting of the same values.  The split is on the
            # separator the formatter itself writes; the cell count is
            # asserted against the header on every row, so a value that ever
            # contained one would stop the build rather than shift a column.
            _END = ' \\\\\n'              # exactly what `_fmt` ends with
            assert _row.endswith(_END), _row
            _cells = _row[:-len(_END)].split(' & ')
            assert len(_cells) == _NFULL, (
                'row split into %d cells against %d in the header: %r'
                % (len(_cells), _NFULL, _row))
            fh.write(' & '.join(_cells[i] for i in _KEEP) + _END)
        fh.write('\\hline\n\\end{tabular}\n')
        if not _issample:
            _written += len(_rows)
    # ★ Every crossing is typeset exactly once across the parts.  Splitting a
    # table is the obvious way to lose a row, so the split is checked against
    # the body it came from rather than trusted.  `ledgergate.py` then reads
    # ALL the parts and checks them against the adopted crossing list.
    # ★ r18: the sample is excluded from this count by construction above --
    # it is rows of the body OVER AGAIN, in the float the submitted paper
    # carries in place of the full table, so counting it here would make the
    # assertion fail on a correct build.
    assert _written == len(_body) == len(out), (
        '%d rows written across %d parts against %d crossings'
        % (_written, len(PART_FILES), len(out)))
    # ★★ And every row of the sample must really be a row OF THE FULL TABLE,
    # cell for cell in the sample's own columns -- the check that fails if the
    # sample is ever generated from a different formatter, a different
    # measurement or a stale pass.  It used to read "the first N rows, in
    # order", which was the stronger statement while the sample was the head
    # of the table; the sample now leads with the rows a reader needs, so the
    # ordering is asserted where it is decided (the three group assertions
    # above) and the content is asserted here.  Both halves are kept: a
    # membership test alone would pass on a sample in any order, including an
    # order that buried the two rank-leading events.
    def _bodyrows(p_):
        return [l for l in open(os.path.join(HERE, p_), encoding='utf-8')
                if l.rstrip().endswith('\\\\')][1:]      # [0] is the header
    _samp, _first = _bodyrows(SAMPLE_FILE), _bodyrows(PART_FILES[0])
    assert len(_samp) == SAMPLE_ROWS, (len(_samp), SAMPLE_ROWS)

    def _filt(l_):
        c_ = l_[:-len(' \\\\\n')].split(' & ')
        return ' & '.join(c_[i] for i in SAMPLE_COLS) + ' \\\\\n'
    _fullfilt = [_filt(l_) for l_ in _first]
    assert all(s_ in _fullfilt for s_ in _samp), (
        'a sample row is not a row of the full ledger in the sample\'s own '
        'columns: %r'
        % [s_ for s_ in _samp if s_ not in _fullfilt][:2])
    for _i, _lr in enumerate(_lead):
        assert (_samp[_i].startswith(_lr['display'] + ' &')
                and ('%.4f' % _lr['freq']) in _samp[_i]), (
            'sample row %d is not the %r crossing at %.4f GHz that leads its '
            'own control field: %r'
            % (_i + 1, _lr['display'], _lr['freq'], _samp[_i]))
    assert len(set(_samp)) == len(_samp), 'a sample row is printed twice'
    assert all(len(l_.split(' & ')) == len(SAMPLE_COLS) for l_ in _samp)
    print('ledger_v410: table split %s across %d floats (<= %d rows each), '
          'plus the %d-row sample in %s that the article prints (%d control-'
          'field leaders, %d untested, %d to complete the legend)'
          % ('/'.join(str(len(p_)) for p_ in _parts), len(PART_FILES),
             ROWS_PER_PART, len(_samp), SAMPLE_FILE, len(_lead),
             len(_untest), len(_samp) - _NLEADUNTEST))

    # ---- the machine-readable ledger (Referee 2, minor 11) ---------------
    # The ledger as a machine-readable file, to accompany the arXiv
    # submission as an ANCILLARY FILE (`anc/` in the submission package;
    # info.arxiv.org/help/ancillary_files.html, whose first listed intended
    # use is "raw data for tables and plots in the article").  An ancillary
    # file is not refereed and is not part of the article, so it carries no
    # claim of its own and the paper promises only what is in it: the
    # description of the columns is therefore in the file, the separator is a tab, every
    # row has the same number of fields and a withheld value is an empty
    # field.  One row per threshold crossing, in the order of the typeset
    # table.
    _MRDOC = [
        ('star', 'star name as in the paper, in plain text: one spelling per '
                 'star, Bayer letters spelled out, and the same string the '
                 'per-window catalogue is keyed on'),
        ('eb', 'ALMA execution block (asdm) identifier'),
        ('band', 'ALMA receiver band'),
        ('nu_topo_GHz', 'crossing frequency as delivered by the correlator'),
        ('nu_star_GHz', 'the same frequency in the star\'s rest frame'),
        ('T_star', 'de-drifted search statistic at the stellar position'),
        ('T_ctrl', 'largest statistic among the window\'s control positions'),
        ('line', 'nearest masked transition in the stellar frame'),
        ('dv_star_kms', 'stellar-frame offset from that transition, km/s'),
        ('mask_coincident_not_attributed',
         '1 where the crossing lies inside the mask and is not attributed'),
        ('n_rep', 'number of covering repeat execution blocks'),
        ('dt_min_d', 'shortest interval to a covering repeat, days'),
        ('dt_max_d', 'longest interval to a covering repeat, days'),
        ('dt_from_unit_stamp',
         '1 where an interval above is measured from the observing unit\'s '
         'stamp rather than from the blocks\' own, as the double dagger '
         'marks in the paper'),
        ('T_pers', 'statistic a carrier persisting at the discovery flux '
                   'would give at the predicted cell (empty where withheld)'),
        ('T_rep', 'statistic measured at that cell at the carried drift'),
        ('T_rep_is_upper_bound',
         '1 where T_rep is a window maximum and so bounds the cell from '
         'above, which bounds sigma_excl from below'),
        ('sigma_excl', 'exclusion of a persisting carrier (empty where '
                       'withheld)'),
        ('attributed', '1 where the crossing is attributed to the mask'),
        ('quality_flagged', '1 where the window is data-quality flagged'),
        ('disposition', 'the disposition printed in the ledger'),
    ]
    assert len(_mr) == len(out) and _mr, (len(_mr), len(out))
    assert [k for k, _ in _MRDOC] == list(_mr[0]), (
        'the column description and the rows disagree: %r vs %r'
        % ([k for k, _ in _MRDOC], list(_mr[0])))
    _mrfile = 'si_ledger%s.txt' % suf
    with open(os.path.join(HERE, _mrfile), 'w') as fh:
        fh.write('# The crossing ledger of the ALMA 40 pc technosignature '
                 'search: one row per threshold crossing.\n')
        fh.write('# Accompanies the arXiv submission as an ancillary file '
                 '(anc/).  '
                 'Tab-separated; an empty field is a value withheld, not a '
                 'zero.\n#\n# Columns:\n')
        for _i, (_k, _d) in enumerate(_MRDOC, 1):
            fh.write('#  %2d  %-32s %s\n' % (_i, _k, _d))
        fh.write('#\n')
        fh.write('\t'.join(k for k, _ in _MRDOC) + '\n')
        for _row in _mr:
            _vals = [_row[k] for k, _ in _MRDOC]
            assert not any('\t' in v for v in _vals), _row
            fh.write('\t'.join(_vals) + '\n')
    print('ledger_v410: %s written, %d rows x %d columns'
          % (_mrfile, len(_mr), len(_MRDOC)))

    # ★ The typeset table must mark every row that lies inside the mask and
    # is still unattributed, and no other row.  Counted in the FILES, not in
    # the variable that wrote them, because the defect being guarded against
    # is a mark that does not reach the page.
    _typeset = sum(open(p_, encoding='utf-8').read().count('$^{\\dagger}$')
                   for p_ in PART_FILES)
    _want = sum(1 for r in out if r['line_note'] and r['line_coincident'])
    if drive == 24:
        _want += 1
    ck('L12 the typeset ledger marks exactly those rows that lie inside the '
       'mask and are not attributed, and there is at least one',
       _typeset == _want and _want >= 1,
       '%d marks typeset against %d rows inside the mask and unattributed'
       % (_typeset, _want))

    # ★★ THE TEXT DESCRIBES A NOTATION, SO THE TABLE MUST CARRY IT.  Sec. D.5
    # and Table D2's caption both promised `n/r` in this table, which it has
    # never printed: `_dt()` reaches that branch only when BOTH ends of the
    # interval are absent, and these rows keep a recorded maximum, so the
    # information is carried by the double dagger instead.  The complaint
    # behind the instruction -- an unrecorded separation printed as `0.0` --
    # IS answered, and this clause is what keeps it answered and keeps the
    # prose describing what is on the page.  Counted in the typeset files,
    # not in the variables that wrote them.
    _ddag = sum(open(p_, encoding='utf-8').read().count('$^{\\ddagger}$')
                for p_ in PART_FILES)
    _dwant = sum(1 for r in out
                 if (RECURC.get('%s|%.6f' % (r['eb'], r['freq'])) or {}
                     ).get('dt_unrec'))
    _dtcol = [l_.split('&')[10].strip() for p_ in PART_FILES
              for l_ in open(p_, encoding='utf-8').read().splitlines()
              if l_.count('&') >= 14]
    if drive == 27:
        _dtcol = _dtcol + ['0.0']
    _zero = [v for v in _dtcol if v in ('0', '0.0', '0.00')]
    _nr = [v for v in _dtcol if 'n/r' in v]
    ck('L13 every repeat interval taken from an observing unit\'s stamp '
       'carries the double dagger the appendix describes, no interval prints '
       'as a zero, and none prints a notation the text does not use',
       _ddag == _dwant and _dwant >= 1 and not _zero and not _nr,
       '%d daggers typeset against %d rows from a unit stamp, over %d '
       'intervals read off the page; zeros %s; n/r %s'
       % (_ddag, _dwant, len(_dtcol), _zero or 'none', _nr or 'none'))

    # ★★★★ L14/L15 READ THE DEPOSITED FILE BACK OFF THE DISK, which is the
    # only place the defect they guard could be seen: the star column was
    # correct in every variable in this generator and carried LaTeX, two
    # spellings of one star and no join key the moment it was written out.
    # ★ L14 compares two INDEPENDENT routes to the same string -- the
    # export's designation (what is written) against the de-TeX of the
    # typeset display (what the page prints) -- so neither a lost component
    # letter nor a lost sign can pass, and it counts the stars in the FILE,
    # not in `_mr`.
    _mrlines = [l_.rstrip('\n') for l_ in
                open(os.path.join(HERE, _mrfile), encoding='utf-8')
                if not l_.startswith('#')]
    _mrhead, _mrbody = _mrlines[0].split('\t'), _mrlines[1:]
    _starcol = [l_.split('\t')[_mrhead.index('star')] for l_ in _mrbody]
    _tex = [s for s in _starcol if re.search(r'[\\${}~^]', s)]
    # ★ Compared as MULTISETS and not row by row: the table is written in its
    # own order, and a check that assumed the two sequences were aligned
    # would report a false disagreement the day the ledger is re-sorted --
    # while the multiset still catches a merged, split or lost name.
    _printed = sorted(star_alias.plain(r['display']) for r in out)
    _route = sorted(_starcol) != _printed
    ck('L14 the deposited ledger\'s star column is plain text, one spelling '
       'per star, and agrees with the de-TeX of the printed designation',
       not _tex and not _route and len(_starcol) == len(out),
       '%d rows, %d distinct stars; %d fields carrying LaTeX; the column %s '
       'the printed designations%s'
       % (len(_starcol), len(set(_starcol)), len(_tex),
          'disagrees with' if _route else 'reproduces',
          '' if not _tex else ': %r' % _tex[:2]))

    # ★★ L15: THE FLAG TABLE D2's CAPTION PROMISES IS IN THE FILE IT NAMES,
    # on exactly the rows the double dagger marks on the page.  Counted in
    # the file and in the typeset fragments, not in the variable that wrote
    # both -- the promise that failed was "the ledger carries the same mark
    # on those" against a file with no such field at all.
    _flag = [l_.split('\t')[_mrhead.index('dt_from_unit_stamp')]
             for l_ in _mrbody]
    ck('L15 the deposited ledger flags every repeat interval taken from an '
       'observing unit\'s stamp, on the same rows the page double-daggers',
       _flag.count('1') == _dwant and _dwant >= 1
       and set(_flag) <= {'0', '1'},
       '%d rows flagged in the file against %d from a unit stamp and %d '
       'daggers typeset' % (_flag.count('1'), _dwant, _ddag))

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
                  if (_rc[id(r)].get('T_anydrift') or 0.0) >= 5.0)
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
       '%d of %d tested reach T_anydrift >= 5' % (n_recur, len(_tested)))
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
