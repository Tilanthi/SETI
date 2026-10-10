#!/usr/bin/env python3
r"""Round 660: the interference screens of the appendix on radio-frequency
interference, scoped to the attribution the paper adopts, and the arithmetic
that reconciles that appendix's densest band with the crossing ledger.

WHY THIS FILE EXISTS

    Three statements in that appendix were each true of a different set.

    (a)  The cross-target occupancy screen is sharpest on the crossings that
         outrank every control position in their own window and that the mask
         does not attribute.  The appendix said there was ONE such crossing.
         There are two, and the paper says so everywhere else: the adopted
         attribution set reports the sulphur-monoxide coincidences rather
         than acting on them, so CP-72 2713 is unattributed, while the
         predicate the screen was reaching for counted it as attributed.
         The screen is therefore run here for BOTH, from the released
         catalogue, and the population is asserted against the published
         count rather than described.

    (b)  The densest band of the clustering test holds twelve crossings and
         the ledger holds fourteen in the same interval.  That is correct --
         the two are different sets -- but the appendix explained the
         difference by saying the two extra rows have no measured peak
         frequency, and only one of them is of that kind.  The other is a
         window the released catalogue does not record as a crossing at all.
         The ledger already carries the distinction, in `f_topo_source`, so
         the reasons are read from it and not asserted by hand.

    (c)  Five crossings carry no measured peak frequency, all of them carbon
         monoxide toward beta Pictoris.  The ledger nevertheless prints a
         topocentric frequency for every row, so a reader comparing the two
         finds ten beta Pictoris carbon-monoxide crossings with frequencies
         and a sentence saying five have none.  Both are true: for those five
         the frequency is RECOVERED from the released line offset, which is
         exactly why the clustering test cannot use them.  The counts and
         the transition split are published so the sentence can say it.

WHAT IT OWNS

    Nothing physical.  Every number here is a recount over products other
    generators own -- `per_target_results_v3.99.csv`, `ledger.json`,
    `appm_v405.json` -- and the macros exist so that the appendix's three
    sentences are generated instead of remembered.

ASSERTIONS (each driven, see --drive)
    X1  the adopted rank-passing unattributed population is the published
        one: the stage-1 rows the adopted set does not attribute number
        \EvNRankQp, and every one of them carries a measured crossing
        frequency, so the screen below is not run on a reconstruction
    X2  the sulphur-monoxide choice is what moves the count: with the noted
        species attributing, the same population is smaller, and the
        difference is exactly the rows whose nearest transition is that
        species
    X3  the screen is a test that could have failed: every event's frequency
        is covered by other windows toward other stars in other blocks, and
        the same-channel count is reported from those windows and not from
        an empty set
    X4  the ledger's band and the clustering test's band differ by exactly
        the rows the test cannot contain, and every extra row's reason is
        read from the ledger's own provenance field
    X5  the crossings with no measured peak frequency are all one star's
        carbon monoxide, the split across transitions accounts for all of
        them, and the published total agrees with \CsNCrossNoFreq

    python3 maskrfi_v660.py [--drive N]

-> survey_numbers_round660.tex, maskrfi_v660.json
"""
import csv
import glob
import json
import os
import re
import sys

import maskframe_v411 as mf

HERE = os.path.dirname(os.path.abspath(__file__))
ROUND = 660
HALF = mf.MASK_HALF_KMS
SUF = ('_drive%d' % int(sys.argv[sys.argv.index('--drive') + 1])
       if '--drive' in sys.argv else '')
OUTNAME = 'survey_numbers_round660%s.tex' % SUF
assert OUTNAME.startswith('survey_numbers_round%d' % ROUND), OUTNAME
_W = ('no', 'one', 'two', 'three', 'four', 'five', 'six', 'seven', 'eight',
      'nine', 'ten', 'eleven', 'twelve')


def _w(n):
    return _W[n] if n < len(_W) else '%d' % n


def texval(name):
    """The value of a published macro, read from the round files."""
    pat = re.compile(r'\\(?:new|renew|provide)command\{\\%s\}\{([^{}]*)\}'
                     % name)
    v = None
    for f in sorted(glob.glob(os.path.join(HERE, 'survey_numbers*.tex'))):
        for m in pat.finditer(open(f, encoding='utf-8').read()):
            if m.group(1).strip():
                v = m.group(1).strip()
    return v


def tname(s):
    s = re.sub(r'\s+Gaia DR3 \d+$', '', s)
    s = s.replace('BD05', 'BD$+$05').replace('BD+05', 'BD$+$05')
    s = s.replace('CP-72', 'CP$-$72').replace('CD-57', 'CD$-$57')
    s = s.replace('bet Pic', r'$\beta$~Pic').replace('eta Crv',
                                                     r'$\eta$~Crv')
    return re.sub(r'\s+', '~', s.strip())


def _f(x):
    try:
        return float(x)
    except (TypeError, ValueError):
        return None


def lohi(r):
    return (min(_f(r['flo_GHz']), _f(r['fhi_GHz'])),
            max(_f(r['flo_GHz']), _f(r['fhi_GHz'])))


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
    D = {}

    def m(k, v):
        assert k.isalpha(), k          # a macro name may hold letters only
        assert k not in M, k
        M[k] = str(v)

    ROWS = list(csv.DictReader(open(os.path.join(
        HERE, 'per_target_results_v3.99.csv'), encoding='utf-8')))
    LED = json.load(open(os.path.join(HERE, 'ledger.json'),
                         encoding='utf-8'))['rows']
    APPM = json.load(open(os.path.join(HERE, 'appm_v405.json'),
                          encoding='utf-8'))

    # ================= 1. the rank-passing crossings the mask leaves alone
    # The predicate is the ADOPTED one: inside the mask in the star's own
    # rest frame, and the coincidences with the noted species reported
    # rather than acted on.  Both clauses come from `maskframe_v411`, which
    # owns the frame chain and the species list, so this generator cannot
    # reach a different answer from the ledger's.
    S1 = [r for r in ROWS if r['stage1_flag'] == 'True']
    adopted, noted, inside_all = [], [], []
    for r in S1:
        dv, line = mf.row_dv_stellar(r)
        assert dv is not None, (r['eb'], line)
        if abs(dv) > HALF:
            continue
        inside_all.append(r)
        if mf.species(line) in mf.NOTED_SPECIES:
            noted.append(r)
        else:
            adopted.append(r)
    EV_RAW = [r for r in S1 if r not in adopted]
    EV = EV_RAW[:1] if drive == 1 else list(EV_RAW)
    _pub = int(texval('EvNRankQp'))
    _meas = [r for r in EV if (r['f_cross_GHz'] or '').strip()]
    ck('X1 the adopted rank-passing unattributed population is the published '
       'one, and every event in it carries a measured crossing frequency',
       len(EV) == _pub and len(_meas) == len(EV),
       '%d events against the published %d, %d with a measured frequency: %s'
       % (len(EV), _pub, len(_meas),
          [(r['star_name'].split(' Gaia')[0], r['eb']) for r in EV]))

    _ev_alt = [r for r in S1 if r not in adopted and r not in noted]
    if drive == 2:
        noted = []
    ck('X2 the noted-species choice is what moves this count: reading those '
       'coincidences as attributions makes the population smaller by exactly '
       'the rows whose nearest transition is that species',
       len(noted) > 0 and len(EV_RAW) - len(_ev_alt) == len(noted),
       '%d events adopted against %d if %s attributed; %d noted row(s) '
       'toward %s'
       % (len(EV_RAW), len(_ev_alt), '/'.join(mf.NOTED_SPECIES), len(noted),
          [r['star_name'].split(' Gaia')[0] for r in noted]))

    EV = sorted(EV, key=lambda r: -float(r['star_snr']))
    m('MxNRankWord', _w(len(EV)))
    m('MxRankStars', joinwords([tname(r['star_name']) for r in EV]))
    m('MxRankFreqs', joinwords(['%.3f' % _f(r['f_cross_GHz']) for r in EV]))
    D['MxRankTStar'] = [float(r['star_snr']) for r in EV]
    D['MxRankBlocks'] = [r['eb'] for r in EV]

    # ================= 2. the cross-target screen, for every one of them
    # Interference belongs to the observatory, so a terrestrial carrier at a
    # fixed sky frequency should recur toward unrelated stars.  For each
    # event: the other windows that cover its frequency, the stars and
    # blocks they belong to, and -- the sharp form -- whether any of them
    # holds a crossing in the same channel.
    per = []
    for r in EV:
        fc = _f(r['f_cross_GHz'])
        cw = (_f(r['chanw_Hz']) or 0.0) / 1e9
        lo, hi = lohi(r)
        wins, stars, blocks, same = 0, set(), set(), []
        for q in ROWS:
            if q['eb'] == r['eb'] and lohi(q) == (lo, hi):
                continue
            qlo, qhi = lohi(q)
            if not (qlo <= fc <= qhi):
                continue
            if q['star_name'] == r['star_name']:
                continue
            wins += 1
            stars.add(q['star_name'])
            blocks.add(q['eb'])
            qf = _f(q['f_cross_GHz'])
            if (q['crossing'] == 'True' and qf is not None
                    and abs(qf - fc) <= max(cw, 1e-6)):
                same.append((q['star_name'], q['eb'], qf))
        per.append(dict(star=r['star_name'].split(' Gaia')[0], eb=r['eb'],
                        freq=fc, n_win=wins, n_star=len(stars),
                        n_block=len(blocks), n_same=len(same),
                        same=same[:5]))
    if drive == 3:
        per[0]['n_win'] = 0
    ck('X3 the screen is a test the population could have failed: every '
       'event\'s frequency is covered by other windows toward other stars '
       'in other blocks, and the same-channel count is read from those '
       'windows; the per-event lists stay in the order the prose names them',
       all(p['n_win'] > 0 and p['n_star'] > 0 and p['n_block'] > 0
           for p in per)
       and [p['eb'] for p in per] == [r['eb'] for r in EV],
       '; '.join('%s %.3f GHz: %d windows, %d stars, %d blocks, %d same '
                 'channel' % (p['star'], p['freq'], p['n_win'], p['n_star'],
                              p['n_block'], p['n_same']) for p in per))
    m('MxOtherWinRange', joinwords([p['n_win'] for p in per]))
    m('MxOtherStarsRange', joinwords([p['n_star'] for p in per]))
    m('MxOtherBlocksRange', joinwords([p['n_block'] for p in per]))
    _ns = sum(p['n_same'] for p in per)
    m('MxSameChanClause',
      'none of them carries a crossing in the same channel' if _ns == 0
      else '%s of them carries a crossing in the same channel' % _w(_ns))

    # ================= 3. the ledger band against the clustering band
    _blo, _bhi = float(texval('AppMBandLo')), float(texval('AppMBandHi'))
    members = APPM['scan']['crossings']['members']
    mkey = {(x['eb'], round(x['f'], 3)) for x in members}
    band = [r for r in LED if _blo <= r['freq'] <= _bhi]
    extra = [r for r in band if (r['eb'], round(r['freq'], 3)) not in mkey]
    # The reason is the ledger's own provenance field, not a list here.
    REASON = (
        ('recovered from the released offset',
         'whose peak frequency the release records only as an offset '
         'from the line'),
        ('adopted list',
         'whose window the release does not record as a crossing at all'),
    )
    ORDER = [k for k, _ in REASON]
    groups = {}
    for r in extra:
        groups.setdefault(r['frame']['f_topo_source'], []).append(r)
    if drive == 4:
        groups = {'catalogue': extra}
    ck('X4 the ledger band and the clustering band differ by exactly the '
       'rows the test cannot contain, and each extra row carries a reason '
       'the ledger itself records',
       len(members) == int(texval('AppMBandN'))
       and len(band) == int(texval('EvTubeLedgerN'))
       and len(extra) == int(texval('EvTubeExtra'))
       and sum(len(v) for v in groups.values()) == len(extra)
       and all(k in ORDER for k in groups),
       '%d ledger rows against %d members, %d extra: %s'
       % (len(band), len(members), len(extra),
          [(r['display'], r['frame']['f_topo_source']) for r in extra]))
    m('MxExtraWord', _w(len(extra)))
    m('MxExtraClause',
      joinwords(['%s %s' % (_w(len(groups[k])) if len(groups[k]) > 1
                            else 'one', why)
                 for k, why in REASON if groups.get(k)]))

    # ================= 4. the crossings with no measured peak frequency
    nofreq = [r for r in LED
              if r['frame']['f_topo_source']
              == 'recovered from the released offset']
    stars = {r['display'] for r in nofreq}
    bycross = {}
    for r in nofreq:
        bycross.setdefault(r['line'], []).append(r)
    _same_star_co = [r for r in LED if r['display'] in stars
                     and (r['line'] or '').startswith('CO(')]
    if drive == 5:
        nofreq = nofreq[:-1]
        stars = {'x', 'y'}
    ck('X5 the crossings with no measured peak frequency are one star\'s '
       'carbon monoxide, the split across transitions accounts for all of '
       'them, and the total is the published one',
       len(stars) == 1 and len(nofreq) == int(texval('CsNCrossNoFreq'))
       and sum(len(v) for v in bycross.values()) == len(nofreq)
       and all((k or '').startswith('CO(') for k in bycross),
       '%d rows toward %s, %s; %d of that star\'s carbon-monoxide crossings '
       'in the ledger' % (len(nofreq), sorted(stars),
                          {k: len(v) for k, v in bycross.items()},
                          len(_same_star_co)))
    m('MxBpNCoWord', _w(len(_same_star_co)))
    m('MxBpNoFreqClause',
      joinwords(['%s in %s' % (_w(len(v)), mf.tex_label(k))
                 for k, v in sorted(bycross.items(),
                                    key=lambda kv: -len(kv[1]))]))

    # ------------------------------------------------------------------
    assert suf == SUF, (suf, SUF)
    with open(os.path.join(HERE, OUTNAME), 'w', encoding='utf-8') as fh:
        fh.write('%%%% GENERATED by maskrfi_v%d.py -- do not hand-edit.\n'
                 % ROUND)
        for k in sorted(M):
            fh.write('\\newcommand{\\%s}{%s}\n' % (k, M[k]))
    json.dump(dict(macros=M, diagnostics=D, failed=fail, events=per,
                   band=dict(lo_GHz=_blo, hi_GHz=_bhi,
                             n_members=len(members), n_ledger=len(band),
                             extra=[dict(star=r['display'], eb=r['eb'],
                                         freq=r['freq'],
                                         reason=r['frame']['f_topo_source'])
                                    for r in extra]),
                   nofreq=[dict(star=r['display'], eb=r['eb'],
                                freq=r['freq'], line=r['line'])
                           for r in nofreq]),
              open(os.path.join(HERE, 'maskrfi_v%d%s.json' % (ROUND, suf)),
                   'w'), indent=1)
    print('%d macros, %d assertions failed %s' % (len(M), len(fail), fail))
    return 1 if fail else 0


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
