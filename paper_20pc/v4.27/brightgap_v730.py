#!/usr/bin/env python3
r"""Round 730: the stars inside the survey volume that no catalogue row admits.

WHY THIS FILE EXISTS

    Section 3 said that no star was excluded by any criterion other than the
    three stated.  That is not true.  The first criterion is a Gaia DR3
    parallax, and a Gaia DR3 parallax needs a Gaia DR3 source; the brightest
    stars in the sky have none, because they saturate the astrometric
    instrument.  The exclusion is therefore a property of the catalogue and
    not of the sky, it is invisible in the work list -- a star that never
    entered cannot be reported as removed -- and it falls on exactly the
    targets a reader of a within-40-pc archival search expects to find.

    Every candidate branch of the selection deduplicated on
    `gaia_source_id`, including the debris-disc branch, which resolved ALMA
    target positions against `gaiadr3.gaia_source` with `parallax > 0`.  The
    disc pool already held Fomalhaut, Vega, Sirius and alpha Centauri; the
    join dropped them without a row anywhere saying so.

WHAT IT MEASURES

    `r17inputs/brightgap_r17.json` is a frozen record of three live queries,
    taken under this survey's own criteria and no others:

      1. Hipparcos-2 (van Leeuwen 2007) stars whose own parallax is above
         25 mas and measured to better than 20 per cent -- the survey's
         distance and precision cuts, on independent astrometry.
      2. each of those propagated with its own proper motion to J2016.0 and
         matched to Gaia DR3 within 3 arcsec; the unmatched set is the gap.
      3. an ALMA ObsCore probe of every unmatched star, keeping only rows
         whose quoted field of view contains the star at the block's own
         epoch and whose primary-beam response there clears the survey's
         floor, evaluated on the adopted 1.13 lambda/D.

    The record also carries the geometry of the one case where the gap is
    visible inside this survey's own products: the three blocks that put
    Sirius B in the census are pointed at Sirius A.

ASSERTIONS (each driven, see --drive)
    B1  the magnitude bins account for the whole volume and the whole gap,
        and the gap is total at the bright end and small everywhere else
    B2  the names printed are read from the record, every one of them has an
        archive window that passes both sky criteria, and the printed list
        holds exactly as many stars as the record does
    B3  the window counts partition per star, and the fine-channel addition
        is real but a minority of the published Class A total
    B4  Sirius A's blocks are a subset of the blocks this survey searched,
        and in those blocks Sirius A is nearer the pointing centre than the
        companion the search did extract
    B5  the catalogue requirement is colour-selective in the direction
        claimed: it removes a larger fraction of the blue stars in the
        volume than of all the others
    B6  the manuscript references these macros, so the paragraph cannot be
        computed and then stripped as unreferenced
    B7  the pointings track the primary's catalogue position, the companion
        lies further off axis than it, and the source the continuum maps hold
        is a stellar photosphere displaced consistently across three blocks

    python3 brightgap_v730.py [--drive N]       N = 1..8
        8 moves the magnitude cut off a bin edge, so the gap no longer
        partitions and the new assertion in B1's block fires.

-> survey_numbers_round730.tex, brightgap_v730.json
"""
import csv
import glob
import json
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROUND = 730
REC = os.path.join(HERE, 'r17inputs', 'brightgap_r17.json')
FLD = os.path.join(HERE, 'r17inputs', 'siriusfield_r17.json')
SUF = ('_drive%d' % int(sys.argv[sys.argv.index('--drive') + 1])
       if '--drive' in sys.argv else '')
OUTNAME = 'survey_numbers_round730%s.tex' % SUF
assert OUTNAME.startswith('survey_numbers_round%d' % ROUND), OUTNAME

_W = ('no', 'one', 'two', 'three', 'four', 'five', 'six', 'seven', 'eight',
      'nine', 'ten', 'eleven', 'twelve')

# How each SIMBAD main identifier is spelled in an astronomy paper.  This is
# a spelling table and not a result: every star in the record must have an
# entry, which B2 asserts, so a star cannot be silently dropped from the
# printed list by being absent from here.
DISPLAY = {
    'alf CMa': 'Sirius~A',
    'alf Lyr': 'Vega',
    'alf PsA': 'Fomalhaut',
    'alf Cen A': r'$\alpha$~Centauri~A',
    'alf Cen B': r'$\alpha$~Centauri~B',
    'bet Leo': r'$\beta$~Leonis',
    'MCC 124': 'MCC~124',
}


def _w(n):
    return _W[n] if n < len(_W) else '%d' % n


def texval(name):
    """The value of a published macro, read from the round files."""
    pat = re.compile(r'\\(?:new|renew|provide)command\{\\%s\}\{([^{}]*)\}'
                     % name)
    v = None
    for f in sorted(glob.glob(os.path.join(HERE, 'survey_numbers*.tex'))):
        if re.search(r'_drive\d+\.tex$', f):
            continue
        for m in pat.finditer(open(f, encoding='utf-8').read()):
            if m.group(1).strip():
                v = m.group(1).strip()
    return v


def joinwords(xs):
    xs = [str(x) for x in xs]
    if not xs:
        return '--'
    if len(xs) == 1:
        return xs[0]
    return ', '.join(xs[:-1]) + ' and ' + xs[-1]


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
        print('  %-3s %s %s' % (name.split()[0], 'PASS' if cond else 'FAIL',
                                detail))

    M = {}

    def m(k, v):
        assert k.isalpha(), k          # a macro name may hold letters only
        assert k not in M, k
        M[k] = str(v)

    R = json.load(open(REC, encoding='utf-8'))
    STARS = list(R['stars'])
    BINS = list(R['bins'])

    print('brightgap_v730: the stars no catalogue row admits'
          + ('  [drive %d]' % drive if driven else ''))
    print('\nassertions')

    # =============================================== 1. the size of the gap
    # The bright end is read, not chosen: it is the faintest bin boundary up
    # to which every star in the volume is missing.
    complete = [b for b in BINS if b['n_volume'] == b['n_missing']]
    bright_mag = max(b['hi'] for b in complete) if complete else None
    n_bright = sum(b['n_volume'] for b in complete)
    faint = [b for b in BINS if b['lo'] >= 4]
    faint_pct = 100.0 * (sum(b['n_missing'] for b in faint)
                         / sum(b['n_volume'] for b in faint))
    if drive == 1:
        BINS = BINS + [dict(lo=20, hi=30, n_volume=7, n_missing=3)]
    ck('B1 the magnitude bins account for the whole volume and the whole '
       'gap, and the gap is total at the bright end and small elsewhere',
       sum(b['n_volume'] for b in BINS) == R['n_volume']
       and sum(b['n_missing'] for b in BINS) == R['n_missing']
       and complete and bright_mag <= 3 and faint_pct < 10.0,
       '%d of %d missing; complete to Hp %s (%d stars); %.1f per cent from '
       'fourth magnitude down'
       % (R['n_missing'], R['n_volume'], bright_mag, n_bright, faint_pct))

    m('BsNVol', R['n_volume'])
    m('BsNGap', R['n_missing'])
    m('BsNBright', n_bright)
    m('BsBrightMag', 'second' if bright_mag == 2 else _w(int(bright_mag)))
    # ★ MINOR 8: 22 bright stars cannot be 257 absences, and the bins say what
    #   the rest are.  The brightest bin is complete; the gap then falls to a
    #   flat few per cent that saturation does not explain.  The MECHANISM is
    #   not published, because it is not measured here.
    # ★ `%.1f` and not `%.0f` DELIBERATELY: rounded, this value is "5 per
    #   cent", which three other generators already print, and the paragraph
    #   that quotes it carries a 20 per cent parallax-precision cut two
    #   sentences earlier.  One decimal keeps two unrelated percentages apart.
    FAINTCUT = 4
    if drive == 8:
        # ★ 5 WOULD NOT HAVE FIRED, and the first version of this drive used
        #   it.  The bins are one magnitude wide at the bright end, so ANY
        #   integer on a bin edge partitions the gap exactly and the
        #   assertion below would have passed on a perturbed cut -- a drive
        #   that cannot fail, in the same file as the assertion it is meant
        #   to prove.  9 falls inside the Hp 8-10 bin, which is what the
        #   assertion is really about: the cut must lie on a bin edge.
        FAINTCUT = 9
    n_gap_bright = sum(b['n_missing'] for b in BINS if b['hi'] <= FAINTCUT)
    n_gap_faint = sum(b['n_missing'] for b in BINS if b['lo'] >= FAINTCUT)
    n_vol_faint = sum(b['n_volume'] for b in BINS if b['lo'] >= FAINTCUT)
    assert n_gap_bright + n_gap_faint == R['n_missing'], (
        'the magnitude cut Hp %s does not lie on a bin edge, so the two '
        'halves do not partition the gap: %d + %d against %d'
        % (FAINTCUT, n_gap_bright, n_gap_faint, R['n_missing']))
    m('BsGapMagCut', FAINTCUT)
    m('BsGapNBright', n_gap_bright)
    m('BsGapNFaint', n_gap_faint)
    m('BsGapFaintPct', '%.1f' % (100.0 * n_gap_faint / n_vol_faint))

    # ======================================= 2. which of them ALMA observed
    named = [s for s in STARS if s['name'] in DISPLAY]
    if drive == 2:
        named = named[:-1]
    disp = [DISPLAY[s['name']] for s in named]
    ck('B2 every star in the printed list is read from the record, has an '
       'archive window passing both sky criteria, and the list is complete',
       len(named) == len(STARS) == R['n_covered']
       and all(s['n_win_a'] + s['n_win_b'] > 0 for s in STARS)
       and all(s['pb_min'] >= 0.5 for s in STARS)
       and len(disp) == R['n_covered'],
       '%d named of %d covered: %s' % (len(named), R['n_covered'], disp))
    m('BsNAlmaWord', _w(R['n_covered']))
    m('BsStarList', joinwords(disp))

    # ============================================ 3. what they would supply
    nA = sum(s['n_win_a'] for s in STARS)
    nB = sum(s['n_win_b'] for s in STARS)
    pubA = int(texval('NWinA'))
    nofine = [DISPLAY[s['name']] for s in STARS if s['n_win_a'] == 0]
    fine = [s for s in STARS if s['n_win_a'] > 0]
    fine_a = [s for s in fine
              if s['sp_type'].strip().upper().startswith('A')]
    if drive == 3:
        nA = pubA + 1
    ck('B3 the window counts partition per star, and the fine-channel '
       'addition is real but a minority of the published Class A total',
       nA == R['tot_win_a'] and nB == R['tot_win_b']
       and 0 < nA < pubA and nB > 0
       and len(nofine) + len(fine) == R['n_covered'] and fine_a,
       '%d fine and %d coarse windows in %d blocks, against %d Class A '
       'windows searched; %d stars carry fine channels, %d of them A~stars'
       % (nA, nB, R['tot_eb'], pubA, len(fine), len(fine_a)))
    m('BsNWinA', nA)
    m('BsNWinB', nB)
    m('BsNEB', R['tot_eb'])
    m('BsRawTB', '%.1f' % (R['tot_raw_gb'] / 1000.0))
    m('BsNoFineList', joinwords(nofine))
    m('BsFineList', joinwords([DISPLAY[s['name']] for s in fine]))
    m('BsNFineWord', _w(len(fine)))
    m('BsNFineATypeWord', _w(len(fine_a)))

    # ============================= 4. Sirius, where the gap is visible here
    SEARCHED = {row['eb'] for row in csv.DictReader(
        open(os.path.join(HERE, 'per_target_results_v3.99.csv'),
             encoding='utf-8'))}
    sir = dict(R['sirius'])
    sirius_star = [s for s in STARS if s['name'] == 'alf CMa'][0]
    held = set(sirius_star['eb_already_searched'])
    if drive == 4:
        sir['a_sep_max'] = sir['b_off_max'] + 1.0
    ck('B4 Sirius A sits in blocks this survey already searched, nearer the '
       'pointing centre than the companion the search did extract',
       held and held <= SEARCHED and len(held) == sirius_star['n_eb']
       and sir['a_sep_max'] < sir['b_off_min']
       and sir['b_n_win'] == sirius_star['n_win_a'] + sirius_star['n_win_b'],
       'Sirius A within %.2f arcsec of %d pointing centres; the companion '
       'read %.2f--%.2f arcsec off axis in the same %d windows, '
       'response %.2f--%.2f'
       % (sir['a_sep_max'], len(held), sir['b_off_min'], sir['b_off_max'],
          sir['b_n_win'], sir['b_pb_min'], sir['b_pb_max']))
    m('BsSirNEBWord', _w(len(held)))
    m('BsSirOffLo', '%.1f' % sir['b_off_min'])
    m('BsSirOffHi', '%.1f' % sir['b_off_max'])
    m('BsSirNWin', sir['b_n_win'])

    # ======== 4b. the Sirius field, measured from this survey's own images
    # ★ `\BsSirSepA` IS NOW READ FROM THE DELIVERED PHASE CENTRE.  It had
    #   come from the archive's ObsCore `s_ra`/`s_dec`, which is the
    #   catalogue position of the *named target* and not the pointing the
    #   paper's own criterion uses.  The value is unchanged -- the two agree
    #   to a milliarcsecond for these rows, which B7 asserts -- but the
    #   provenance now matches the claim, and the claim itself had to change:
    #   0.4 arcsec is the distance to the primary's CATALOGUE POSITION, and
    #   the primary is 3 arcsec from that.
    F = json.load(open(FLD, encoding='utf-8'))
    FB = sorted(F['blocks'], key=lambda x: x['band'])
    # read from the record, not from `sir`: drive 4 perturbs `sir` to make
    # B4 fail, and a drive must fail one assertion only.
    _obs_vs_crval = abs(F['catA_phase_hi'] - R['sirius']['a_sep_max'])
    if drive == 7:
        F = dict(F, alpha=0.4)
    ck('B7 the pointings track the primary\'s catalogue position, the '
       'companion lies further off axis than it, and the source the continuum '
       'maps hold is a stellar photosphere displaced consistently across '
       'blocks',
       F['catA_phase_hi'] < F['catB_phase_lo']
       and abs(F['alpha'] - 2.0) < 0.3
       and F['centroid_scatter_arcsec'] < 1.0
       and (F['ab_sep_hi'] - F['ab_sep_lo']) < 1.0
       and F['cen_catA_lo'] > F['beam_hi']
       and _obs_vs_crval < 0.01
       and all(r['field'].startswith('Sirius') and not r['field'].endswith('B')
               for r in FB),
       'catalogue primary within %.3f arcsec of the phase centre against '
       '%.3f for the companion (archive target position agrees to %.4f); '
       'spectral index %.2f; the source sits %.2f-%.2f arcsec out against a '
       '%.2f arcsec beam, scatter %.3f; implied separation %.2f-%.2f arcsec; '
       'fields %s'
       % (F['catA_phase_hi'], F['catB_phase_lo'], _obs_vs_crval, F['alpha'],
          F['cen_catA_lo'], F['cen_catA_hi'], F['beam_hi'],
          F['centroid_scatter_arcsec'], F['ab_sep_lo'], F['ab_sep_hi'],
          sorted({r['field'] for r in FB})))
    m('BsSirSepA', '%.1f' % max(F['catA_phase_hi'], 0.05))
    m('BsSirAlpha', '%.1f' % F['alpha'])
    m('BsSirSnrLo', '%.0f' % F['snr_lo'])
    m('BsSirSnrHi', '%.0f' % F['snr_hi'])
    m('BsSirCenLo', '%.1f' % F['cen_catA_lo'])
    m('BsSirCenHi', '%.1f' % F['cen_catA_hi'])

    # ========================================= 5. the colour of the removal
    C = dict(R['colour'])
    if drive == 5:
        C['early_pct'], C['other_pct'] = C['other_pct'], C['early_pct']
    ck('B5 the catalogue requirement removes a larger fraction of the blue '
       'stars in the volume than of all the others',
       C['n_early_missing'] < R['n_missing']
       and C['n_early_volume'] < R['n_volume']
       and C['early_pct'] > C['other_pct'],
       '%d of %d bluer than B-V %.2f are missing, %.1f per cent, against '
       '%.1f per cent of the rest'
       % (C['n_early_missing'], C['n_early_volume'], C['bv_cut'],
          C['early_pct'], C['other_pct']))
    m('BsNEarly', C['n_early_missing'])
    m('BsNEarlyVol', C['n_early_volume'])
    # Published as a count out of a count and a RATIO, never as percentages:
    # 20 and 5 per cent are each already printed by other generators, and the
    # 20 would sit two sentences from the parallax-precision cut of 20 per
    # cent.  39 of 196 says the same thing and reads once.
    m('BsEarlyRatio', '%.1f' % (C['early_pct'] / C['other_pct']))

    # ====================== 6. the paragraph must survive retire_macros.py
    sys.path.insert(0, HERE)
    import manuscript
    body = manuscript.flat()
    if drive == 6:
        body = body.replace('\\BsStarList', 'XX')
    # ★ A SUBSTRING MATCH HERE IS A GATE THAT CANNOT FAIL.  `\BsNAlma` is a
    #   prefix of `\BsNAlmaWord`, so `'\\BsNAlma' in body` passed while the
    #   manuscript referenced only the second -- and `\BsNAlma` was then
    #   retired as unreferenced, which is the very thing this clause exists to
    #   prevent.  Match the macro name to a boundary, and require every macro
    #   emitted, not a chosen six.
    want = sorted(M)
    absent = [k for k in want
              if not re.search(r'\\%s(?![A-Za-z])' % k, body)]
    #: ★★★★ v4.26.  B6 USED TO FORBID A CUT OF THIS PARAGRAPH, and that is a
    #: gate dictating prose rather than protecting a fact -- the seventh in
    #: this project caught doing it.  Its purpose is sound: a quantity
    #: computed and then stripped from the page by `retire_macros` leaves no
    #: trace, which is how this paragraph lost a number once.  But
    #: "every macro emitted here is cited" makes shortening the paragraph a
    #: build failure, and round 25 shortens it on both referees' instruction:
    #: the Sirius A/B narrative goes to two sentences and the per-star fine
    #: window list with it.
    #: So the requirement becomes the one this project uses everywhere else
    #: it has a legitimate exception -- a DECLARATION with a written reason.
    #: A macro may leave the page only by being named here; anything else
    #: still fails, which is the case B6 was written for.
    RETIRED = {
        'BsSirAlpha': 'the Sirius A/B narrative is two sentences now; the '
                      'position-angle detail is in the deposited block list',
        'BsSirSepA': 'ditto -- the A-B separation',
        'BsSirCenLo': 'ditto -- the low end of the offsets from phase centre',
        'BsSirCenHi': 'ditto -- the high end',
        'BsSirOffLo': 'ditto -- the low end of the in-beam offsets',
        'BsSirOffHi': 'ditto -- the high end',
        'BsSirSnrLo': 'ditto -- the weakest Sirius B statistic',
        'BsSirSnrHi': 'ditto -- the strongest',
        'BsSirNWin': 'ditto -- the window count, which \\BsNWinA and '
                     '\\BsNWinB now carry for the whole set',
        'BsFineList': 'the per-star split of fine-channel windows: the '
                      'paragraph now gives the totals, \\BsNWinA and '
                      '\\BsNWinB, which is what the exclusion is about',
        'BsNFineWord': 'ditto -- the count of stars with a fine window',
        'BsNFineATypeWord': 'ditto -- the count of those that are early-type',
        'BsNoFineList': 'ditto -- the complementary list',
        #: ★★★ v4.27 (r26-cut-main's R26-S-04, declared by the integrator).
        #: Three macros left the page with the bright-Gaia paragraph's
        #: condensation and are declared rather than quietly stripped.  The
        #: other two B6 reported -- \BsNBright and \BsBrightMag -- were NOT
        #: declared: they carry the statement that the exclusion is COMPLETE
        #: at the bright end, which is the sharpest form of a limitation
        #: Referee 1 keep-lists by name, so the clause was restored to \S2
        #: instead.  B6 is the gate that forced that distinction to be made
        #: explicitly, one macro at a time, which is what it is for.
        'BsGapFaintPct': 'the steady per-bin incompleteness below '
                         'Hp \\BsGapMagCut: the paragraph now gives the '
                         'bright-end statement, which is complete and '
                         'therefore stronger, and the aggregate loss '
                         '\\BsNGap of \\BsNVol with its magnitude split, '
                         'so the per-bin rate is the third telling of the '
                         'same exclusion.  It is in the deposited bin table',
        'BsNEarly': 'the count of early-type stars among the missing: the '
                    'colour-selectivity of the Gaia requirement is quoted '
                    'in \\S2.1 as the RATE, \\BsEarlyRatio times its rate '
                    'among all the others, which is the form that bears on '
                    'the bias and is the one Table 2 is read against',
        'BsNEarlyVol': 'ditto -- the volume-limited denominator of that '
                       'count, which the rate already divides by',
    }
    assert all(v.strip() for v in RETIRED.values()), \
        'a declaration without a reason is a way of forgetting, not deciding'
    _undeclared = [k for k in absent if k not in RETIRED]
    _stale = [k for k in RETIRED
              if re.search(r'\\%s(?![A-Za-z])' % k, body)]
    if drive == 9:
        _undeclared = ['(drive 9) a macro stripped without a declaration']
    ck('B6 every macro this round emits is either referenced by the '
       'manuscript or declared here with the reason it left the page, so a '
       'quantity cannot be computed and then stripped as unreferenced',
       not _undeclared and not _stale,
       'missing from the manuscript and undeclared: %s; declared retired but '
       'still cited: %s; %d of %d emitted macros cited, %d declared'
       % (_undeclared or 'none', _stale or 'none',
          len(want) - len(absent), len(want), len(RETIRED)))

    # ------------------------------------------------------------------
    assert suf == SUF, (suf, SUF)
    with open(os.path.join(HERE, OUTNAME), 'w', encoding='utf-8') as fh:
        fh.write('%%%% GENERATED by brightgap_v%d.py -- do not hand-edit.\n'
                 % ROUND)
        for k in sorted(M):
            fh.write('\\newcommand{\\%s}{%s}\n' % (k, M[k]))
    json.dump(dict(macros=M, failed=fail,
                   stars=[dict(name=s['name'], display=DISPLAY.get(s['name']),
                               sp_type=s['sp_type'], v_mag=s['v_mag'],
                               dist_pc=s['dist_pc'], n_win_a=s['n_win_a'],
                               n_win_b=s['n_win_b'], n_eb=s['n_eb'],
                               raw_gb=s['raw_gb'], bands=s['bands'],
                               projects=s['projects'],
                               already=s['eb_already_searched'])
                          for s in STARS],
                   bins=R['bins'], colour=R['colour'], sirius=R['sirius']),
              open(os.path.join(HERE, 'brightgap_v%d%s.json' % (ROUND, suf)),
                   'w'), indent=1)
    print('%d macros, %d assertions failed %s' % (len(M), len(fail), fail))
    return 1 if fail else 0


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
