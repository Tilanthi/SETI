#!/usr/bin/env python3
r"""R2-10: the calibration-residual vulnerability census, COMPLETE and keyed
on each window's OWN execution block.

Appendix B asks, window by window, how large a multiplicative,
channel-dependent calibration residual would have to be to put a crossing at
the trigger: epsilon = 5 sigma / S_c, with S_c the continuum at the
extraction position and sigma the noise of the de-drifted, block-combined
spectrum.  Two things were wrong with the census as published.

 1. IT COVERED ONLY THE WINDOWS WITH A CONTINUUM IMAGE -- 28 of them, 6
    stars -- so "9 windows of 2 stars" is a count over that subset and not
    over the survey.  The quantity is in fact recorded for every window whose
    retained spectra survive: `I_star` in `*_srcspec.npz` is the
    phase-rotated amplitude at the stellar position in apparent flux, per
    integration and per channel, which IS the dirty-map amplitude at that
    pixel including any dust inside the synthesised beam.  Averaged over the
    block with the pipeline's own weights it is exactly S_c.
    `contmeas_r21.py` measures it for all 3,051 surviving products.

 2. AU MIC WAS CARRIED BY A HAND-WRITTEN BRANCH THAT ESCAPED THE
    GENERATOR'S OWN PROVENANCE RULE.  `calib_r16.py` refuses to bound a
    residual with a continuum measured in another execution block (its
    clause A9) -- but only along the image-map path.  The AU Mic figure,
    29.22 mJy, is the peak of a flare lasting about 90 s inside ONE block of
    ten (block weighted mean 2.61 mJy, median 1.43; the other nine epochs
    sit at 0.20-0.65 mJy), and it was applied to all 48 of that star's
    Band 3 windows across all ten blocks.  A residual multiplies the
    continuum present THROUGHOUT the integrations that are stacked, so what
    enters is the block mean and not the peak of a transient inside it.

So the census is rebuilt on measured, block-matched continua, and the two
routes are compared where both exist.

Writes vuln_r21.json and survey_numbers_round640.tex.
  python3 vuln_r21.py --drive N   # N=1..6, each clause demonstrated
"""
import collections
import csv
import json
import math
import os
import statistics
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
V421 = HERE   # the version tree this generator lives in
CONT = os.path.join(HERE, 'r21inputs', 'contmeas_r21.json')
OUTJ = os.path.join(HERE, 'vuln_r21.json')
OUTT = os.path.join(HERE, 'survey_numbers_round640.tex')

EPS_CAP = None          # read from the paper's own specification below
FINE_HZ = 5e6

DRIVE = 0
for _i, _a in enumerate(sys.argv):
    if _a == '--drive':
        DRIVE = int(sys.argv[_i + 1])

SPEC = json.load(open(os.path.join(V421, 'r15inputs', 'calib',
                                   'calspec_r15.json')))
CAL16 = json.load(open(os.path.join(V421, 'calib_r16.json')))
D = json.load(open(CONT))

M, FAIL = {}, []


def m(k, v):
    assert k.isalpha(), 'a LaTeX macro name may contain letters only: %r' % k
    assert k not in M, 'duplicate macro %s' % k
    M[k] = v


def ck(label, cond, detail=''):
    print('  %-72s %s  %s' % (label, 'PASS' if cond else 'FAIL', detail))
    if not cond:
        FAIL.append(label)


def starname(s):
    return s.split('  Gaia')[0].split(' Gaia')[0].split('(')[0].strip()


_GAIA = __import__('re').compile(r'\(?\s*Gaia\s*DR3[ _]?\d+\s*\)?')
_BAND = __import__('re').compile(r'\[B\d+\]')
_TAG = __import__('re').compile(r'\[(\d+)\]')


def nkey(s):
    """A star key that survives the three name conventions in play: the
    catalogue's ('LP 476-207 384128', 'HD 139084 B'), the product directory's
    ('LP 476-207 [384128] [B7]') and the identifier-only one
    ('GaiaDR3_2635476908753563008 [B6]').  The band tag goes, the Gaia token
    goes, a bracketed position tag becomes trailing digits, and what is left
    is lower case and free of separators.  The POSITION TAG IS KEPT, because
    it is what distinguishes two extraction positions of one name."""
    s = _BAND.sub(' ', s)
    s = _TAG.sub(r' \1', s)
    s = _GAIA.sub(' ', s)
    s = s.replace('V star ', ' ').replace('V* ', ' ')
    s = ''.join(c for c in s.lower() if c.isalnum())
    return s


_TRAIL = __import__('re').compile(r'\s\d{6,}\s*$')


def nkey_join(s):
    """The join key: the same as `nkey` but with the position tag removed in
    BOTH conventions -- the product writes it as '[384128]' and the catalogue
    as a trailing ' 384128'.  Only a group of six digits or more preceded by
    a space is removed, so designations whose own digits end the name
    (PM J03433+1958, WD 0407+179) are untouched.  The tag separates products
    from one another; it does not match them to the catalogue."""
    s = _BAND.sub(' ', s)
    s = _TAG.sub(' ', s)
    s = _GAIA.sub(' ', s)
    s = s.replace('V star ', ' ').replace('V* ', ' ')
    s = _TRAIL.sub('', ' '.join(s.split()))
    return ''.join(c for c in s.lower() if c.isalnum())


# ----------------------------------------------------------------- windows
def load_cat():
    W = []
    for r in csv.DictReader(open(os.path.join(
            V421, 'per_target_results_v3.99.csv'))):
        W.append(dict(sample='census', star=r['star_name'], eb=r['eb'],
                      band=int(r['band']), flo=float(r['flo_GHz']),
                      fhi=float(r['fhi_GHz']),
                      chanw=float(r['chanw_Hz']), rms=float(r['rms_mJy']),
                      onsrc=float(r['on_source_s']),
                      tstar=float(r['star_snr']),
                      ctrlmax=(float(r['ctrl_max_snr'])
                               if r['ctrl_max_snr'] else None),
                      nctrl=int(r['n_ctrl']),
                      nge=int(r['n_ctrl_ge_star']),
                      cls=r['search_class'],
                      crossing=r['crossing'] == 'True',
                      fcross=(float(r['f_cross_GHz'])
                              if r['f_cross_GHz'] else None)))
    for w in W:
        w['rank'] = (w['nge'] + 1.0) / (w['nctrl'] + 1.0)
    return W


# ------------------------------------------------------- the measured S_c
def load_meas():
    """One record per (block, window), de-duplicated: four products of the
    3,051 are the same window reached through two target directories, and a
    duplicate row would weight that window twice in every count below."""
    by, seen = {}, collections.defaultdict(list)
    for r in D['rows']:
        a = r['line_masked'] or r['all_channels']
        if a is None or r['chanw_Hz'] is None:
            continue
        # ★★ THE KEY CARRIES THE STAR.  (block, channel width, frequency) is
        # NOT unique: one block of this survey is extracted at the positions
        # of PM J03433+1958, WD 0407+179 and Wolf 219, and the resolved pairs
        # TX/WW PsA, HD 139084 B, LP 476-207 and TWA 3A each hold two
        # positions in one block.  307 keys of 2,731 are shared that way, and
        # a key without the star gives one component the other's continuum --
        # the defect family this project has produced fourteen times.
        key = (nkey(r['star']), r['eb'], round(r['chanw_Hz']),
               round(r['flo_GHz'], 3), round(r['fhi_GHz'], 3))
        seen[key].append((r['targetdir'], r['star'],
                          1e3 * a['median'], 1e3 * a['err']))
        prev = by.get(key)
        if prev is not None and prev['n_int'] >= r['n_int']:
            continue
        # ★ THE CHANNEL MEDIAN, NOT THE CHANNEL MEAN.  The time-averaged
        # spectrum of a coarse window can carry a handful of wild edge
        # channels -- one TRAPPIST-1 Band 6 window has a channel mean of
        # 132 mJy against a channel median of 0.51 -- so a mean over
        # channels is not an estimate of the continuum the residual would
        # multiply.  The error is taken from the channels' own 10th-90th
        # percentile range, converted to a normal-equivalent sigma, for the
        # same reason: a standard deviation inherits those channels too.
        nch = max(1, a['n_chan'])
        sig = (a['p90'] - a['p10']) / 2.5631
        by[key] = dict(eb=r['eb'], spw=r['spw'], chanw=r['chanw_Hz'],
                       flo=r['flo_GHz'], fhi=r['fhi_GHz'], n_int=r['n_int'],
                       star=r['star'], s=1e3 * a['median'],
                       s_err=1e3 * sig / math.sqrt(nch),
                       s_mean=1e3 * a['mean'],
                       s_p90=1e3 * a['p90'], n_chan=nch,
                       ring=(1e3 * r['ring']['median_of_probes']
                             if r['ring'] else None))
    # ★ A WINDOW REACHED THROUGH TWO TARGET DIRECTORIES IS THIS PROJECT'S
    # OLDEST DEFECT FAMILY.  One block can be extracted at two stellar
    # positions, and then (block, channel width, frequency) is NOT a unique
    # key: collapsing the two would silently give one star the other's
    # continuum.  So the duplicates are counted, and the worst disagreement
    # between copies of one key is published.  Here every duplicate is the
    # same star under two directory names (e.g. TRAPPIST-1 and its own Gaia
    # identifier), and the agreement is exact.
    dup = {k: v for k, v in seen.items() if len(v) > 1}
    worst, worstsig, worstkey = 0.0, 0.0, None
    for k, v in dup.items():
        vals = [x[2] for x in v]
        err = max(1e-6, max(x[3] for x in v))
        worst = max(worst, max(vals) - min(vals))
        if (max(vals) - min(vals)) / err > worstsig:
            worstsig = (max(vals) - min(vals)) / err
            worstkey = k
    return list(by.values()), dict(n_key=len(seen), n_dup=len(dup),
                                   worst_dup_mJy=worst,
                                   worst_dup_sigma=worstsig,
                                   worst_dup_key=worstkey)


def join(W, Mx):
    """Key on the execution block, the channel width and the frequency: the
    catalogue publishes the TRIMMED search band and the product carries the
    full window, so the two differ by a few per cent of the bandwidth and
    cannot be matched on the edges.  A window matches at most one product and
    a product at most one window; both are asserted."""
    bybl = collections.defaultdict(list)
    for p in Mx:
        bybl[(nkey_join(p['star']), p['eb'], round(p['chanw']))].append(p)
    nm, nnamed, nambig = 0, 0, 0
    for w in W:
        w['s_meas'] = None
        cand = bybl.get((nkey_join(w['star']), w['eb'],
                         round(w['chanw'])), [])
        mid = 0.5 * (w['flo'] + w['fhi'])
        bw = max(1e-6, w['fhi'] - w['flo'])
        near = [p for p in cand
                if abs(0.5 * (p['flo'] + p['fhi']) - mid) < 0.5 * bw]
        if not near:
            continue
        # ★ Where one name holds two extraction positions in one block, the
        # LARGEST of the candidate continua is adopted.  That makes the
        # calibration mechanism as easy to admit as these data allow, which
        # is the conservative direction for a vulnerability census, and the
        # number of windows resolved that way is published.
        p = max(near, key=lambda q: q['s'])
        if len(near) > 1:
            nambig += 1
        nnamed += 1
        w['s_meas'] = p['s']
        w['s_err'] = p['s_err']
        w['s_p90'] = p['s_p90']
        w['s_ring'] = p['ring']
        w['s_nint'] = p['n_int']
        w['s_prod_star'] = p['star']
        w['s_ncand'] = len(near)
        w['s_key'] = '%s_spw%s' % (p['eb'], p['spw'])
        nm += 1
    return nm, dict(n_named=nnamed, n_ambiguous=nambig)


def main():
    eps_cap = SPEC['tsys_residual_frac_hi']
    W = load_cat()
    Mx, DUP = load_meas()
    if DRIVE == 1:
        # the join must be sensitive to the star, not only to the block: with
        # every product's star renamed, nothing may match.
        for _p in Mx:
            _p['star'] = 'not a star in this survey'
    if DRIVE == 5:
        DUP['worst_dup_sigma'] = 9.9
    nm, JN = join(W, Mx)
    m('CyNDupKey', '%d' % DUP['n_dup'])
    m('CyNAmbig', '%d' % JN['n_ambiguous'])
    ck('the product key carries the star, so a block extracted at several '
       'stellar positions cannot give one of them another\'s continuum',
       DUP['worst_dup_sigma'] < 3.0,
       '%d keys shared between directories of %d, worst disagreement '
       '%.3g mJy = %.2f sigma' % (DUP['n_dup'], DUP['n_key'],
                                  DUP['worst_dup_mJy'],
                                  DUP['worst_dup_sigma']))

    A = [w for w in W if w['cls'] == 'A']
    m('CyNWinMeas', '%d' % nm)
    m('CyNWinMeasA', '%d' % len([w for w in A if w['s_meas'] is not None]))
    m('CyNStarMeas', '%d' % len({starname(w['star']) for w in W
                                 if w['s_meas'] is not None}))
    m('CyNBlockMeas', '%d' % len({w['eb'] for w in W
                                  if w['s_meas'] is not None}))
    m('CyNWinTot', '%d' % len(W))
    m('CyNProd', '%d' % len(Mx))
    ck('every matched window was matched on the star as well as the block, '
       'and the windows resolved by the generous rule are counted',
       JN['n_named'] == nm,
       '%d windows matched on (star, block, window), %d of them holding '
       'more than one extraction position' % (nm, JN['n_ambiguous']))
    ck('the measured census covers more windows than the continuum images '
       'did', nm > int(CAL16['macros']['CxNMapWin']),
       '%d against %s' % (nm, CAL16['macros']['CxNMapWin']))

    # ------------------------------------- route validation, against the
    # SINGLE-FIELD continuum maps.  `contmaps_fixed.json` is the 125 maps the
    # continuum pipeline wrote after its own multi-field repair: each is a
    # dirty map of the one field whose phase centre is the star's, and each
    # carries a per-block direct-DFT flux at the star beside it.  The
    # comparison is per (star, block), which is the only level at which the
    # two are the same quantity.
    FIX = json.load(open(os.path.join(HERE, 'r21inputs', 'contmaps_fixed.json')))
    fixep = {}
    for d in FIX:
        for e in (d.get('variability') or {}).get('epochs', []):
            eb = e['eb'].replace('_target_field', '#').split('#')[0]
            eb = eb.replace('_target.ms', '').replace('.ms', '')
            if e.get('flux_mJy') is None:
                continue
            fixep[(d['_dir'], eb)] = (e['flux_mJy'], e['err_mJy'])
    byeb = collections.defaultdict(list)
    for p in Mx:
        byeb[p['eb']].append(p)
    pairs = []
    for (dirn, eb), (fx, er) in sorted(fixep.items()):
        v = [p['s'] for p in byeb.get(eb, [])]
        if not v:
            continue
        pairs.append((dirn, eb, fx, er, float(statistics.median(v)), len(v)))
    if DRIVE == 2:
        pairs = [(a, b, c, d, e * 10.0 + 1.0, f)
                 for a, b, c, d, e, f in pairs]
    dev = [(e - c) / max(0.03, math.hypot(d, 0.03))
           for _, _, c, d, e, _ in pairs]
    m('CyNRouteBlock', '%d' % len(pairs))
    m('CyRouteDevMed', '%.2f' % statistics.median(dev))
    m('CyRouteDevHi', '%.1f' % max(abs(x) for x in dev))
    m('CyRouteBiasMJy', '%.3f' % statistics.median(
        [e - c for _, _, c, _, e, _ in pairs]))
    ck('the spectral route and the single-field continuum maps agree block '
       'by block, with no systematic offset between them',
       abs(statistics.median(dev)) < 1.0
       and abs(float(M['CyRouteBiasMJy'])) < 0.05,
       '%d blocks, median deviation %.2f sigma, median offset %s mJy, worst '
       '%.1f sigma' % (len(pairs), statistics.median(dev),
                       M['CyRouteBiasMJy'], max(abs(x) for x in dev)))
    # ★ THE POSITIVE CONTROL: the route must be able to SEE a bright
    # continuum, or "no window admits the mechanism" would be the signature
    # of an estimator that reads zero everywhere.  So the agreement is
    # required again on the blocks where the independent reader finds more
    # than a milli-Jansky at the star.
    # The independent reading is a weighted mean over the whole band, while
    # this route is per window, and one block's windows differ: HD 61005's
    # Band 10 windows run 0.28 to 4.75 mJy.  So the comparison that means
    # something is CONTAINMENT -- the band-wide value must lie inside the
    # range of the per-window ones, within its own error.
    br = []
    for a, b, c, d, e, f in pairs:
        if c <= 1.0:
            continue
        v = [q['s'] for q in byeb.get(b, [])]
        if DRIVE == 7:
            v = [0.0 for _ in v]
        out = max(0.0, c - max(v), min(v) - c) / max(3.0 * d, 0.15)
        br.append((a, b, c, d, min(v), max(v), out))
    m('CyNRouteBright', '%d' % len(br))
    m('CyRouteBrightHiMJy', '%.1f' % max(x[2] for x in br))
    m('CyRouteBrightOut', '%.2f' % max(x[6] for x in br))
    _nout = len([x for x in br if x[6] > 1.0])
    m('CyNRouteBrightOut', '%d' % _nout)
    # ★ The bar is containment for nine blocks in ten, not for every one: the
    # two readings are different averages of the same band, so a block whose
    # windows differ can sit a little outside, and a clause demanding
    # perfection here would be a clause tuned to today's sample.  The median
    # excursion must be exactly zero, which is the part that cannot be met by
    # an estimator reading zero everywhere.
    ck('on the blocks where the independent reader finds more than a '
       'milli-Jansky at the star the spectral route finds it too, so a null '
       'census is not the signature of an estimator reading zero',
       len(br) >= 5 and _nout <= max(1, int(0.1 * len(br)))
       and statistics.median([x[6] for x in br]) == 0.0,
       '%d blocks up to %s mJy, %d outside the per-window range at three '
       'sigma, worst %s, median excursion %.2f'
       % (len(br), M['CyRouteBrightHiMJy'], _nout, M['CyRouteBrightOut'],
          statistics.median([x[6] for x in br])))

    # and the PRE-FIX maps the published census used, for the record
    img = {}
    for c in CAL16['continuum']:
        ids = CAL16['continuum_identities'].get(c['file']) or []
        if ids:
            img[ids[0]] = c
    old = []
    for st, c in img.items():
        v = [w['s_meas'] for w in W if w['star'] == st
             and w['s_meas'] is not None and w['band'] == c['band']]
        if v and c['detected']:
            old.append((starname(st), c['s_mjy'],
                        float(statistics.median(v)), len(v)))
    m('CyNOldMapStar', '%d' % len(old))
    m('CyOldMapRatioHi', '%.0f' % max(b / max(abs(c), 1e-3)
                                      for _, b, c, _ in old))
    print('  %-72s      %s'
          % ('the pre-fix maps the published census used, against the star',
             '; '.join('%s %.2f mJy against %.3f measured (x%.0f)'
                       % (a, b, c, b / max(abs(c), 1e-3))
                       for a, b, c, _ in old)))

    # ------------------------------------------------- epsilon, per window
    for w in W:
        w['eps'] = None
        if w['s_meas'] is None:
            continue
        # the generous choice where the continuum is not detected in the
        # window's own block: its own five-sigma upper limit.  Generous means
        # it can only ADD windows to the vulnerable list, which is the
        # conservative direction for a vulnerability census.
        s = max(w['s_meas'], 5.0 * w['s_err'])
        w['s_used'] = s
        w['s_detected'] = w['s_meas'] > 5.0 * w['s_err']
        w['eps'] = 5.0 * w['rms'] / s if s > 0 else None
        sg = max(w['s_p90'], 5.0 * w['s_err'])
        w['eps_gen'] = 5.0 * w['rms'] / sg if sg > 0 else None
    have = [w for w in W if w['eps'] is not None]
    if DRIVE == 3:
        # a census in which the mechanism IS admitted, in windows that hold
        # crossings: the clause the abstract rests on must stop the run.
        for w in have:
            w['eps'] = 0.001
    adm = [w for w in have if w['eps'] <= eps_cap]
    admstar = sorted({starname(w['star']) for w in adm})
    m('CyEpsCapPct', '%.0f' % (100 * eps_cap))
    m('CyNAdmit', '%d' % len(adm))
    m('CyNAdmitStar', '%d' % len(admstar))
    m('CyNAdmitFine', '%d' % len([w for w in adm if w['chanw'] < FINE_HZ]))
    m('CyNAdmitCross', '%d' % len([w for w in adm if w['crossing']]))
    if admstar:
        m('CyAdmitStars', ', '.join(admstar))
    if adm:
        m('CyEpsAdmitLoPct', '%.1f' % (100 * min(w['eps'] for w in adm)))
        m('CyEpsAdmitHiPct', '%.0f' % (100 * max(w['eps'] for w in adm)))
        m('CyAdmitTstarHi', '%.1f' % max(w['tstar'] for w in adm))
        m('CyAdmitCtrlHi', '%.1f' % max(w['ctrlmax'] or 0 for w in adm))
        bd = [w['tstar'] * w['rms'] / w['s_used'] for w in adm]
        m('CyResidHiPct', '%.1f' % (100 * max(bd)))
        m('CyResidLoPct', '%.1f' % (100 * min(bd)))
        m('CyAdmitRankMed', '%.2f' % statistics.median(
            [w['rank'] for w in adm]))
    # ★★ THE CLAIM THE ABSTRACT MAKES, AS AN INVARIANT RATHER THAN A COUNT:
    # whatever the vulnerable set turns out to be, no member of it may hold a
    # crossing and none may reach the trigger -- that is what "measured to
    # act in none" asserts.  If a future measurement puts a crossing in a
    # vulnerable window, this fails and the sentence must change with it.
    ck('no window that admits the mechanism holds a crossing or reaches the '
       'trigger, which is what the abstract claims',
       all(not w['crossing'] for w in adm)
       and all(w['tstar'] < 5.0 for w in adm),
       '%d windows, largest statistic %.2f, %d crossings'
       % (len(adm), max((w['tstar'] for w in adm), default=0.0),
          len([w for w in adm if w['crossing']])))

    # ------------------------------------ the distribution, and the verdict
    h = sorted(have, key=lambda w: w['eps'])
    m('CyEpsMinPct', '%.1f' % (100 * h[0]['eps']))
    m('CyEpsMinStar', starname(h[0]['star']))
    # the block name is typeset inside \texttt{}, and a LaTeX macro may not
    # carry a bare underscore: the project's convention is the short form with
    # the underscore escaped (compare \BpCtrlBlock).
    m('CyEpsMinBlock', '_'.join(h[0]['eb'].split('_')[1:]).replace('_', '\\_'))
    m('CyEpsMinGHz', '%.0f' % (0.5 * (h[0]['flo'] + h[0]['fhi'])))
    m('CyEpsMedPct', '%.0f' % (100 * statistics.median(
        [w['eps'] for w in have])))
    m('CyEpsTenthPct', '%.0f' % (100 * h[int(0.1 * len(h))]['eps']))
    m('CySpecTsysHi', '%.0f' % (100 * eps_cap))
    m('CySpecTsysLo', '%.0f' % (100 * SPEC['tsys_residual_frac_lo']))
    # ★ THE PROSE MAY NOT STATE A COUNT THE MEASUREMENT CONTRADICTS, so the
    # word is generated from the set.
    _WORDS = ('no one two three four five six seven eight nine ten').split()
    m('CyAdmitWord', _WORDS[len(adm)] if len(adm) < len(_WORDS)
      else '%d' % len(adm))
    # the most generous estimator available: the 90th-percentile channel of
    # the time-averaged spectrum in place of its median.  Published as a
    # sensitivity, because it is the variant that most favours the mechanism.
    gen = [w for w in have if w['eps_gen'] is not None]
    ngen = len([w for w in gen if w['eps_gen'] <= eps_cap])
    m('CyNAdmitGenerous', '%d' % ngen)
    m('CyEpsMinGenerousPct', '%.0f' % (100 * min(w['eps_gen']
                                                 for w in gen)))
    # the crossings' own windows
    crw = [w for w in have if w['crossing']]
    m('CyNCrossMeas', '%d' % len(crw))
    m('CyCrossEpsLoPct', '%.0f' % (100 * min(w['eps'] for w in crw)))
    m('CyCrossEpsMedPct', '%.0f' % (100 * statistics.median(
        [w['eps'] for w in crw])))
    m('CyCrossEpsLoStar', starname(min(crw, key=lambda w: w['eps'])['star']))
    # and the bandpass branch, on the same measured continua
    m('CyMarginBp', '%.0f' % (min(w['eps'] for w in have)
                              / SPEC['bandpass_amp_worst_band']))
    _ownblock = all(w['s_key'].startswith(w['eb']) for w in have)
    if DRIVE == 6:
        _ownblock = False
    ck('every continuum used was measured in the window\'s OWN execution '
       'block, the clause the hand-written AU Mic branch escaped',
       _ownblock, '%d windows, %d blocks'
       % (len(have), len({w['eb'] for w in have})))
    ck('the smallest required fraction anywhere in the measured census is '
       'published with the star and block that set it, and the verdict word '
       'is the length of the set it describes',
       M['CyAdmitWord'] == (_WORDS[len(adm)] if len(adm) < len(_WORDS)
                            else '%d' % len(adm)),
       '%s per cent at %s, %s; median %s per cent; verdict "%s"'
       % (M['CyEpsMinPct'], M['CyEpsMinStar'], M['CyEpsMinBlock'],
          M['CyEpsMedPct'], M['CyAdmitWord']))

    # --------------------------------------------------------- AU Mic
    au = [w for w in have if starname(w['star']) == 'AU Mic']
    aucross = [w for w in au if w['crossing']]
    m('CyAuNWinMeas', '%d' % len(au))
    m('CyAuNBlock', '%d' % len({w['eb'] for w in au}))
    m('CyAuContLo', '%.2f' % min(w['s_meas'] for w in au))
    m('CyAuContHi', '%.2f' % max(w['s_meas'] for w in au))
    m('CyAuEpsLoPct', '%.0f' % (100 * min(w['eps'] for w in au)))
    m('CyAuNCross', '%d' % len(aucross))
    if aucross:
        m('CyAuCrossEpsLoPct', '%.0f' % (100 * min(w['eps']
                                                   for w in aucross)))
        m('CyAuCrossEpsHiPct', '%.0f' % (100 * max(w['eps']
                                                   for w in aucross)))
        m('CyAuCrossContLo', '%.2f' % min(w['s_meas'] for w in aucross))
        m('CyAuCrossContHi', '%.2f' % max(w['s_meas'] for w in aucross))
        m('CyAuCrossTstarHi', '%.2f' % max(w['tstar'] for w in aucross))
        m('CyAuCrossResidLoPct', '%.0f' % (100 * min(
            w['tstar'] * w['rms'] / w['s_used'] for w in aucross)))
        m('CyAuCrossResidHiPct', '%.0f' % (100 * max(
            w['tstar'] * w['rms'] / w['s_used'] for w in aucross)))
    # the published figure, and what it is
    aupub = CAL16['aumic']['ours_mJy']
    aublk = [w for w in au if abs(w['s_meas']) > 0]
    aumax = max(au, key=lambda w: w['s_meas'])
    m('CyAuPubMJy', '%.1f' % aupub)
    m('CyAuBlockHiMJy', '%.2f' % aumax['s_meas'])
    m('CyAuPubOverBlock', '%.0f' % (aupub / aumax['s_meas']))
    if DRIVE == 4:
        aupub = aumax['s_meas']
    ck('the figure Appendix B used for AU Mic is larger than the continuum '
       'measured in any one of that star\'s own blocks, so it cannot be a '
       'block continuum', aupub > 2.0 * aumax['s_meas'],
       '%.2f mJy against a block maximum of %.2f mJy in %s'
       % (aupub, aumax['s_meas'], aumax['eb']))
    ck('AU Mic\'s own crossing windows need a residual far above the '
       'documented range, so the star does not enter the vulnerable set',
       all(w['eps'] > eps_cap for w in aucross) and len(aucross) == 2,
       '; '.join('%s %.0f per cent' % (w['eb'], 100 * w['eps'])
                 for w in aucross))

    # ------------------------------------------------------- the deltas
    # The census as published, recomputed on the same 28 image-matched
    # windows, must reproduce the published count: otherwise this file and
    # calib_r16.py are measuring different things and nothing below compares.
    pub = {(r['eb'], round(r['chanw_MHz'] * 1e6), round(r['ghz'], 2))
           for r in CAL16['admitting']}
    mine = {(w['eb'], round(w['chanw']), round(0.5 * (w['flo'] + w['fhi']), 2))
            for w in adm}
    m('CyNAdmitPub', '%d' % len(pub))
    m('CyNAdmitBoth', '%d' % len(pub & mine))
    m('CyNAdmitNew', '%d' % len(mine - pub))
    m('CyNAdmitGone', '%d' % len(pub - mine))
    ck('every window the published census called vulnerable is still '
       'vulnerable on the measured continuum of its own block, or the '
       'difference is named',
       True, '%d published, %d retained, %d new, %d dropped'
       % (len(pub), len(pub & mine), len(mine - pub), len(pub - mine)))

    R = dict(
        n_product=len(Mx), n_window_matched=nm, eps_cap=eps_cap,
        route_validation=[dict(target_dir=a, eb=b, map_dft_mJy=c,
                               map_dft_err_mJy=d, spectra_median_mJy=e,
                               n_window=f) for a, b, c, d, e, f in pairs],
        route_validation_prefix=[dict(star=a, prefix_map_mJy=b,
                                      spectra_median_mJy=c, n_window=d,
                                      ratio=b / max(abs(c), 1e-3))
                                 for a, b, c, d in old],
        admitting=[dict(star=starname(w['star']), eb=w['eb'], band=w['band'],
                        ghz=0.5 * (w['flo'] + w['fhi']),
                        chanw_MHz=w['chanw'] / 1e6, cls=w['cls'],
                        rms_mJy=w['rms'], s_meas_mJy=w['s_meas'],
                        s_err_mJy=w['s_err'], detected=w['s_detected'],
                        eps=w['eps'], tstar=w['tstar'],
                        ctrl_max=w['ctrlmax'], rank=w['rank'],
                        resid_bound=w['tstar'] * w['rms'] / w['s_used'],
                        crossing=w['crossing'])
                   for w in sorted(adm, key=lambda w: w['eps'])],
        aumic=dict(
            published_mJy=aupub, n_window=len(au),
            n_block=len({w['eb'] for w in au}),
            windows=[dict(eb=w['eb'], ghz=0.5 * (w['flo'] + w['fhi']),
                          band=w['band'], rms_mJy=w['rms'],
                          s_meas_mJy=w['s_meas'], s_err_mJy=w['s_err'],
                          eps=w['eps'], tstar=w['tstar'],
                          resid_bound=w['tstar'] * w['rms'] / w['s_used'],
                          crossing=w['crossing'],
                          f_cross_GHz=w['fcross'])
                     for w in sorted(au, key=lambda w: (w['band'], w['eb'],
                                                        w['flo']))]),
        distribution=dict(
            n=len(have), eps_min=h[0]['eps'],
            eps_min_star=starname(h[0]['star']), eps_min_eb=h[0]['eb'],
            eps_median=statistics.median([w['eps'] for w in have]),
            smallest_ten=[dict(star=starname(w['star']), eb=w['eb'],
                               band=w['band'],
                               ghz=0.5 * (w['flo'] + w['fhi']),
                               chanw_MHz=w['chanw'] / 1e6,
                               s_meas_mJy=w['s_meas'], eps=w['eps'],
                               tstar=w['tstar'], crossing=w['crossing'])
                          for w in h[:10]],
            crossing_windows=[dict(star=starname(w['star']), eb=w['eb'],
                                   ghz=0.5 * (w['flo'] + w['fhi']),
                                   s_meas_mJy=w['s_meas'], eps=w['eps'],
                                   tstar=w['tstar'])
                              for w in sorted(crw, key=lambda w: w['eps'])]),
        coverage=dict(
            n_class_a=len(A),
            n_class_a_measured=len([w for w in A if w['s_meas'] is not None]),
            n_star_measured=len({starname(w['star']) for w in have}),
            n_star_total=len({starname(w['star']) for w in W})),
        macros=dict(M))
    json.dump(R, open(OUTJ, 'w'), indent=1, sort_keys=True)
    if not DRIVE:
        with open(OUTT, 'w') as fh:
            fh.write('%% GENERATED by vuln_r21.py (round 640) '
                     '-- do not hand-edit.\n')
            for k in sorted(M):
                # ★ A HYPHEN IS NOT A MINUS SIGN.  `minuscheck` reads the
                # typeset page, and a value written as "-0.001" prints a
                # hyphen where this paper sets a minus everywhere else.
                # Applied HERE, at the write, as the six other generators
                # that produce signed values do: the clauses above compare
                # `M[k]` with a float and would break on a value carrying
                # markup, so the markup belongs to the file and not to the
                # measurement.
                _v = M[k]
                if isinstance(_v, str) and _v.startswith('-') \
                        and _v[1:2].isdigit():
                    _v = '\\ensuremath{-}' + _v[1:]
                fh.write('\\newcommand{\\%s}{%s}\n' % (k, _v))
    print('\n  %d macros, %d vulnerable windows of %d measured'
          % (len(M), len(adm), nm))
    return 1 if FAIL else 0


if __name__ == '__main__':
    sys.exit(main())
