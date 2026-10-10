#!/usr/bin/env python3
r"""Round 630 (v4.17): the channel-dependent calibration mechanism, redone on
the MEASURED continuum at the extraction position and on the STACKED noise.

WHY THIS FILE EXISTS.  Appendix B excluded a multiplicative, channel-dependent
calibration residual by amplitude, using each star's PHOTOSPHERIC continuum
extrapolated from its 2.2 micron flux.  That is the wrong quantity twice over.

 1. A multiplicative residual acts on the TOTAL continuum at the extraction
    position, and that position is a dirty-map amplitude which includes any
    dust emission inside the synthesised beam.  Most of this sample was
    observed because it has a bright disc.  `calib_r15.py`'s own numbers say
    how wrong the photosphere can be: for L 836-122 the measured continuum
    exceeds it by a factor of order ten thousand.

 2. The comparison must be against the noise of the de-drifted, block-combined
    spectrum, because a coherent residual stacks.  Here the paper was in fact
    already right -- `rms_mJy` of the catalogue IS that combined noise, and
    this generator asserts the identity smin = 5.sigma in both samples' own
    units -- but the appendix called it "single-channel noise", which does not
    say whether it is per integration or post-stacking, and a reader cannot
    tell.  The name is fixed in the prose and pinned here.

Both errors ran the same way: they made the mechanism look more impossible
than it is.  Redone on the right quantities the amplitude bound is GONE, and
that is reported as a result rather than buried:

  * CxNAdmit windows of CxNAdmitStar stars require a fractional error of only
    CxEpsAdmitLoPct-CxEpsAdmitHiPct per cent, inside the 5-20 per cent a
    coarse-mode Tsys calibration is documented to leave at an ozone line.
  * In every one of them the largest statistic anywhere in the window is at
    most CxAdmitTstarHi against a trigger of five, none holds a crossing, and
    the implied coherent residual at the extraction position is at most
    CxResidHiPct per cent -- CxResidBestPct per cent in the three deepest.
  * The crossings are not where the mechanism can act.  CxNCrossFine of the
    CxNCrossWin catalogued crossing windows are fine-channel windows, where
    reaching the observed statistic this way needs CxCrossNeedLo-CxCrossNeedHi
    mJy inside one beam of the star against CxContMax mJy at the brightest
    extraction position measured anywhere in this sample.
  * Within one star the pattern is the wrong way round: CxOneStar's
    CxOneStarNAdmit coarse windows would admit a residual of
    CxOneStarEpsLoPct-CxOneStarEpsHiPct per cent and produce nothing, while
    its one crossing sits in the fine window where the required error is
    CxOneStarCrossEpsPct per cent.

INPUTS -- all read, none typed.
  per_target_results_v3.99.csv            census windows (rank, T_star, rms)
  holdout_export_v381.json                hold-out windows
  r16inputs/calib/*_continuum.json        the measured continuum maps, verbatim
  r16inputs/calib/contprov_r16.json       their provenance and the rules above
  r15inputs/calib/calspec_r15.json        the external specifications
  r8inputs/aumic_scale_v408.json          AU Mic's own Band 3 continuum

OUTPUT  survey_numbers_round630.tex, calib_r16.json

    python3 calib_r16.py --selftest       # eight clauses, each demonstrated
"""
import collections
import csv
import json
import math
import os
import re
import sys

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, 'survey_numbers_round630.tex')
JSONOUT = os.path.join(HERE, 'calib_r16.json')
INP = os.path.join(HERE, 'r16inputs', 'calib')
SPEC = json.load(open(os.path.join(HERE, 'r15inputs', 'calib',
                                   'calspec_r15.json')))
PROV = json.load(open(os.path.join(INP, 'contprov_r16.json')))
AUMIC = json.load(open(os.path.join(HERE, 'r8inputs', 'aumic_scale_v408.json')))

CELL_ARCSEC = 0.5          # the continuum maps' pixel, from the provenance
FINE_HZ = 5e6              # the catalogue's own fine/coarse channel division

M = {}


def m(k, v):
    assert k.isalpha(), ('a LaTeX macro name may contain letters only: %r' % k)
    assert k not in M, ('duplicate macro %s' % k)
    M[k] = v


def _f(x):
    try:
        v = float(x)
        return None if v != v else v
    except (TypeError, ValueError):
        return None


# ===================================================== the windows and the noise
def load_windows():
    """Every window of the census and the hold-out, with the noise the search
    statistic divides by and the identifiers needed to join a continuum map."""
    W = []
    for r in csv.DictReader(open(os.path.join(
            HERE, 'per_target_results_v3.99.csv'))):
        W.append(dict(sample='census', star=r['star_name'], eb=r['eb'],
                      band=int(r['band']), flo=float(r['flo_GHz']),
                      fhi=float(r['fhi_GHz']), chanw=float(r['chanw_Hz']),
                      rms=float(r['rms_mJy']), smin=_f(r['smin_mJy']),
                      smin_unit='mJy', onsrc=float(r['on_source_s']),
                      pboff=_f(r['pb_offset_arcsec']),
                      nctrl=int(r['n_ctrl']), nge=int(r['n_ctrl_ge_star']),
                      tstar=float(r['star_snr']),
                      ctrlmax=_f(r['ctrl_max_snr']),
                      crossing=r['crossing'] == 'True'))
    for r in json.load(open(os.path.join(
            HERE, 'holdout_export_v381.json')))['rows']:
        if r['n_ge_star'] is None or r['rms'] is None:
            continue
        W.append(dict(sample='holdout', star=r['star_name'], eb=r['eb'],
                      band=int(r['band']), flo=r['flo'], fhi=r['fhi'],
                      chanw=r['chanw'], rms=r['rms'], smin=r.get('smin'),
                      smin_unit='Jy', onsrc=r['onsrc'], pboff=None,
                      nctrl=r['n_ctrl'], nge=r['n_ge_star'],
                      tstar=r['star_snr'], ctrlmax=r['ctrl_max'],
                      crossing=False))
    for w in W:
        w['rank'] = (w['nge'] + 1.0) / (w['nctrl'] + 1.0)
    # The noise screen of calib_r15.py, kept so the two generators describe the
    # same population: two windows of one block carry a noise smaller by a
    # factor of 700 on 69 times less data.
    grp = collections.defaultdict(list)
    for w in W:
        if w['onsrc']:
            grp[(w['eb'], round(w['chanw']))].append(w['rms']
                                                     * math.sqrt(w['onsrc']))
    for w in W:
        w['noise_ok'] = True
        g = grp[(w['eb'], round(w['chanw']))] if w['onsrc'] else []
        if len(g) < 2:
            continue
        med = float(np.median(g))
        if med > 0 and not (0.1 <= w['rms'] * math.sqrt(w['onsrc']) / med <= 10.0):
            w['noise_ok'] = False
    return [w for w in W if w['noise_ok']]


def check_noise_identity(W):
    """The published sigma is the de-drifted, block-combined noise, not the
    per-integration one.  Both files satisfy smin = 5.sigma, in their own
    units -- mJy in the catalogue, Jy in the hold-out export.  A per-
    integration noise would miss by the square root of the integration count,
    which is a factor of order twenty here, so this cannot pass by accident."""
    out = {}
    for samp, scale in (('census', 1.0), ('holdout', 1e3)):
        r = np.array([w['smin'] * scale / (5.0 * w['rms'])
                      for w in W if w['sample'] == samp and w['smin']
                      and w['rms']])
        out[samp] = dict(n=int(r.size), median=float(np.median(r)),
                         frac_within_one_pct=float((np.abs(r - 1) < 0.01).mean()),
                         lo=float(r.min()), hi=float(r.max()))
    return out


# ============================================ the measured continuum, and its join
GAIA = re.compile(r'Gaia DR3 (\d+)')
BANDTAG = re.compile(r'\[B(\d+)\]')


def norm_name(s):
    """A name reduced to comparable form: no Gaia token, no case, no runs of
    space, no punctuation that one catalogue writes and another does not."""
    s = GAIA.sub('', BANDTAG.sub('', s)).replace('(', ' ').replace(')', ' ')
    s = s.replace('_', ' ').replace('-', ' ')
    return re.sub(r'\s+', ' ', s).strip().lower()


def load_continuum():
    """The measured continuum at the extraction position, one record per map."""
    C = []
    for fn in sorted(os.listdir(INP)):
        if not fn.endswith('_continuum.json'):
            continue
        d = json.load(open(os.path.join(INP, fn)))
        g = GAIA.search(d['star_name'])
        b = BANDTAG.search(d['star_name'])
        det = bool(d['continuum_source_detected'])
        C.append(dict(file=fn, raw=d['star_name'], gaia=g.group(1) if g else None,
                      band=int(b.group(1)) if b else None,
                      name=norm_name(d['star_name']),
                      peak=float(d['image_peak_mJy']),
                      rms=float(d['image_rms_mJy']),
                      snr=float(d['peak_snr']),
                      offset=float(d['peak_offset_arcsec']), detected=det,
                      # the map maximum where it is a detection at the centre
                      # pixel, otherwise the map's own five-sigma upper limit:
                      # generous either way, which is the point.
                      s_mjy=float(d['image_peak_mJy']) if det
                      else 5.0 * float(d['image_rms_mJy']),
                      # the execution blocks the map was made from, where the
                      # product records them; used to check that a continuum
                      # is quoted on the data it was measured in.
                      ebs=sorted({e['eb'].replace('_target.ms', '') for e in
                                  (d.get('variability') or {}).get('epochs',
                                                                   [])})))
    return C


def join_continuum(W, C):
    """Attach a measured continuum to every window it legitimately covers.

    Keyed on the Gaia DR3 identifier wherever the catalogue's own star name
    carries one -- including the trailing-digit abbreviations the catalogue
    uses for resolved pairs -- and on the normalised name only where no
    identifier exists on either side.  A map is applied only to windows of
    its own band, and only where the star and the map maximum share the
    centre pixel.  The number of windows matched is published, and a map that
    matched two distinct catalogue identities stops the generator: applying
    one component's continuum to its companion is the join defect this
    project has produced thirteen times.
    """
    ids = {}
    for w in W:
        g = GAIA.search(w['star'])
        tail = w['star'].split()[-1]
        tailid = tail if tail.isdigit() and len(tail) >= 6 else None
        ids[w['star']] = (g.group(1) if g else None, tailid,
                          norm_name(w['star'][:-len(tail)] if tailid
                                    else w['star']),
                          norm_name(w['star']))
    for c in C:
        # Pass one, on identifiers.  The abbreviation branch demands BOTH the
        # trailing digits and the name, because 3291643148740384128 ends in
        # "28" as well as in "384128" and Wolf 28 is a different star.
        c['identities'] = {w['star'] for w in W
                           if (ids[w['star']][0] is not None
                               and ids[w['star']][0] == c['gaia'])
                           or (c['gaia'] is not None
                               and ids[w['star']][1] is not None
                               and c['gaia'].endswith(ids[w['star']][1])
                               and ids[w['star']][2] == c['name'])}
        # Pass two, only where the catalogue carries no identifier at all for
        # this star: the FULL name, abbreviating digits included, so that a
        # resolved pair written "<name> <gaia tail>" can never be reached this
        # way and must come through pass one or not at all.
        if not c['identities']:
            c['identities'] = {w['star'] for w in W
                               if ids[w['star']][0] is None
                               and ids[w['star']][3] == c['name']}
    for c in C:
        assert len(c['identities']) <= 1, (
            'A3: %s matches %d catalogue identities %s -- a continuum map must '
            'not be shared between resolved components'
            % (c['file'], len(c['identities']), sorted(c['identities'])))
    bystar = {sorted(c['identities'])[0]: c for c in C if c['identities']}
    nmatch = 0
    for w in W:
        w['s_meas'] = None
        c = bystar.get(w['star'])
        if c is None:
            continue
        if c['band'] is not None and c['band'] != w['band']:
            continue
        if c['offset'] > CELL_ARCSEC:
            continue
        if w['pboff'] is not None and w['pboff'] > CELL_ARCSEC:
            continue
        w['s_meas'] = c['s_mjy']
        w['c_file'] = c['file']
        nmatch += 1
    return bystar, nmatch


# ======================================================================= main
def run(write=True, eps_cap=None, drive=0):
    eps_cap = SPEC['tsys_residual_frac_hi'] if eps_cap is None else eps_cap
    W = load_windows()
    C = load_continuum()
    R = {}

    # ------------------------------------------------- 1 which noise, and say so
    ni = check_noise_identity(W)
    R['noise_identity'] = ni
    m('CxNoiseNWin', '%d' % sum(v['n'] for v in ni.values()))

    # ---------------------------------------- 2 the measured continuum and the join
    bystar, nmatch = join_continuum(W, C)
    # A4, taken first because everything below reads the joined rows: the join
    # must not be silently empty, and every matched window must carry the file
    # it matched.
    assert nmatch == len([w for w in W if w.get('s_meas')]), nmatch
    assert nmatch > 0 and all(w.get('c_file') for w in W if w.get('s_meas')), \
        'A4: the continuum join is empty'
    inside = [c for c in C if c['identities']]
    m('CxNMap', '%d' % len(C))
    m('CxNMapStar', '%d' % len(bystar))
    m('CxNMapWin', '%d' % nmatch)
    m('CxNMapDet', '%d' % len([c for c in inside if c['detected']]))
    cmax = max(inside, key=lambda c: c['s_mjy'])
    m('CxContMax', '%.0f' % cmax['s_mjy'])
    m('CxContMaxStar', cmax['raw'].split('(')[0].strip())
    m('CxContMaxSnr', '%.0f' % cmax['snr'])
    R['continuum'] = [dict((k, c[k]) for k in
                           ('file', 'raw', 'band', 's_mjy', 'snr', 'detected',
                            'offset')) for c in C]
    R['continuum_identities'] = {c['file']: sorted(c['identities']) for c in C}

    # The factor by which the photospheric extrapolation understates it.  The
    # photosphere is not recomputed here: the blackbody extrapolation and the
    # frozen SIMBAD photometry are imported from the generator that defines
    # them, so the two cannot disagree about a star's photosphere.
    import calib_r15 as _ph
    R['photospheric_source'] = 'calib_r15.s_continuum'
    ratio = {}
    for w in W:
        w['s_phot'] = None
        p = _ph.PHOT.get(w['star'])
        if p is None:
            continue
        s, _t = _ph.s_continuum(p['K'], p['V'],
                                0.5 * (w['flo'] + w['fhi']) * 1e9)
        if s is None:
            continue
        w['s_phot'] = s * 1e3
        if w.get('s_meas'):
            ratio.setdefault(w['star'], []).append(w['s_meas'] / w['s_phot'])
    ratio = {k: float(np.median(v)) for k, v in ratio.items()}
    def _pow10(x):
        e = int(math.floor(math.log10(x)))
        return '%.1f\\times10^{%d}' % (x / 10.0 ** e, e)
    m('CxRatioHi', _pow10(max(ratio.values())))
    m('CxRatioHiStar', max(ratio, key=ratio.get).split('  Gaia')[0]
      .split(' Gaia')[0])
    m('CxRatioMed', '%.0f' % float(np.median(list(ratio.values()))))
    R['ratio_hi_value'] = max(ratio.values())
    R['measured_over_photospheric'] = ratio

    # ------------------------------- 3 the error a crossing would need, per window
    for w in W:
        w['eps'] = (5.0 * w['rms'] / w['s_meas']
                    if w.get('s_meas') else None)
    adm = [w for w in W if w['eps'] is not None and w['eps'] <= eps_cap]
    admstars = sorted({w['star'] for w in adm})
    m('CxNAdmit', '%d' % len(adm))
    m('CxNAdmitStar', '%d' % len(admstars))
    # ★ r16-prose asked for these: the same two counts as English words, for
    # running prose.  "9 windows toward 2 stars would admit one" reads like a
    # table, and the only alternative -- a prose agent spelling them out by
    # hand -- breaks hard rule 2, so the word form has to come from here.
    # Same shape as `CxAdmitNCrossWord` below.  ★ `wordcase` will refuse
    # either of them at the head of a sentence, which is correct: both are
    # lower case by construction.
    _WORDS = ('no one two three four five six seven eight nine ten eleven '
              'twelve').split()
    m('CxNAdmitWord', _WORDS[len(adm)] if len(adm) < len(_WORDS)
      else '%d' % len(adm))
    m('CxNAdmitStarWord', _WORDS[len(admstars)] if len(admstars) < len(_WORDS)
      else '%d' % len(admstars))
    m('CxEpsCapPct', '%.0f' % (100.0 * eps_cap))
    R['admitting'] = [dict(star=w['star'], eb=w['eb'], band=w['band'],
                           ghz=0.5 * (w['flo'] + w['fhi']),
                           chanw_MHz=w['chanw'] / 1e6, rms_mJy=w['rms'],
                           s_meas_mJy=w['s_meas'], eps=w['eps'],
                           tstar=w['tstar'], ctrlmax=w['ctrlmax'],
                           rank=w['rank'], crossing=w['crossing'],
                           sample=w['sample']) for w in
                      sorted(adm, key=lambda w: w['eps'])]
    if adm:
        e = np.array([w['eps'] for w in adm])
        m('CxEpsAdmitLoPct', '%.1f' % (100.0 * e.min()))
        m('CxEpsAdmitHiPct', '%.0f' % (100.0 * e.max()))
        m('CxAdmitTstarHi', '%.1f' % max(w['tstar'] for w in adm))
        m('CxAdmitCtrlHi', '%.1f' % max(w['ctrlmax'] for w in adm
                                        if w['ctrlmax']))
        ncr = len([w for w in adm if w['crossing']])
        m('CxAdmitNCross', '%d' % ncr)
        m('CxAdmitNCrossWord', ['none', 'one', 'two', 'three'][ncr]
          if ncr < 4 else '%d' % ncr)
        m('CxAdmitRankMed', '%.2f' % float(np.median([w['rank'] for w in adm])))
        m('CxAdmitChanMHz', '%.1f' % float(np.median(
            [w['chanw'] / 1e6 for w in adm])))
        # The coherent residual those windows themselves bound: the largest
        # statistic anywhere in the window, in units of the continuum there.
        bd = np.array([w['tstar'] * w['rms'] / w['s_meas'] for w in adm])
        m('CxResidBestPct', '%.1f' % (100.0 * bd.min()))
        m('CxResidHiPct', '%.1f' % (100.0 * bd.max()))
        m('CxNAdmitFine', '%d' % len([w for w in adm if w['chanw'] < FINE_HZ]))
        wbest = min(adm, key=lambda w: w['tstar'] * w['rms'] / w['s_meas'])
        m('CxResidBestStar', wbest['star'])
        R['residual_bound'] = dict(best=float(bd.min()), worst=float(bd.max()),
                                   median=float(np.median(bd)),
                                   best_star=wbest['star'],
                                   best_eb=wbest['eb'],
                                   best_map=wbest['c_file'])
        # The tightest bound must come from a window whose own execution block
        # is one the map was made from, where the product records its blocks:
        # a continuum measured elsewhere bounds nothing here.
        cb = bystar[wbest['star']]
        m('CxResidBestSameBlock', 'yes' if wbest['eb'] in cb['ebs'] else 'no')
        R['residual_bound']['map_blocks'] = cb['ebs']

    # ------------------------- 4 one star in which the pattern is the wrong way round
    # Read, not named: the star with the most admitting windows that also holds
    # a crossing somewhere.
    cand = [(len([w for w in W if w['star'] == s and w['eps'] is not None
                  and w['eps'] <= eps_cap]), s) for s in admstars
            if any(w['crossing'] for w in W if w['star'] == s)]
    R['one_star_candidates'] = sorted(cand, reverse=True)
    if cand:
        n_one, one = max(cand)
        ws = [w for w in W if w['star'] == one and w['eps'] is not None]
        cr = [w for w in ws if w['crossing']]
        m('CxOneStar', one)
        m('CxOneStarNAdmit', '%d' % n_one)
        ea = [w['eps'] for w in ws if w['eps'] <= eps_cap]
        m('CxOneStarEpsLoPct', '%.0f' % (100.0 * min(ea)))
        m('CxOneStarEpsHiPct', '%.0f' % (100.0 * max(ea)))
        m('CxOneStarTstarHi', '%.1f' % max(w['tstar'] for w in ws
                                           if w['eps'] <= eps_cap))
        m('CxOneStarCrossEpsPct', '%.0f' % (100.0 * max(w['eps'] for w in cr)))
        m('CxOneStarCrossChanMHz', '%.2f' % (max(cr, key=lambda w: w['eps'])
                                             ['chanw'] / 1e6))
        m('CxOneStarAdmitChanMHz', '%.1f' % float(np.median(
            [w['chanw'] / 1e6 for w in ws if w['eps'] <= eps_cap])))
        R['one_star'] = dict(star=one, n_admit=n_one,
                             rows=[dict(ghz=0.5 * (w['flo'] + w['fhi']),
                                        chanw_MHz=w['chanw'] / 1e6,
                                        eps=w['eps'], tstar=w['tstar'],
                                        crossing=w['crossing']) for w in
                                   sorted(ws, key=lambda w: w['eps'])])

    # ------------------- 5 what the crossings' OWN windows would require instead
    cr = [w for w in W if w['crossing']]
    fine = [w for w in cr if w['chanw'] < FINE_HZ]
    need = np.array([w['tstar'] * w['rms'] / eps_cap for w in fine])
    m('CxNCrossWin', '%d' % len(cr))
    m('CxNCrossFine', '%d' % len(fine))
    m('CxCrossNeedLo', '%.0f' % need.min())
    m('CxCrossNeedMed', '%.0f' % float(np.median(need)))
    m('CxCrossNeedHi', '%.0f' % need.max())
    m('CxCrossNeedNBelow', '%d' % int((need <= cmax['s_mjy']).sum()))
    m('CxCrossNeedBelowStars', ', '.join(sorted(
        {w['star'].split('  Gaia')[0].split(' Gaia')[0]
         for w, v in zip(fine, need) if v <= cmax['s_mjy']})))
    R['crossing_requirement'] = dict(n=len(fine), lo=float(need.min()),
                                     median=float(np.median(need)),
                                     hi=float(need.max()),
                                     n_below_brightest=int(
                                         (need <= cmax['s_mjy']).sum()))

    # ------------------------------------------- 6 the one referee-named star we
    # have a continuum for, from this paper's own extractor.
    jan = AUMIC['january']
    au = [w for w in W if w['star'].startswith('AU Mic')
          and abs(0.5 * (w['flo'] + w['fhi']) - AUMIC['band_GHz']) < 20.0]
    m('CxAuStar', 'AU~Mic')
    m('CxAuContMJy', '%.1f' % jan['ours_mJy'])
    m('CxAuGHz', '%.0f' % AUMIC['band_GHz'])
    m('CxAuNWin', '%d' % len(au))
    m('CxAuEpsPct', '%.1f' % (100.0 * min(5.0 * w['rms'] / jan['ours_mJy']
                                          for w in au)))
    m('CxAuTstarHi', '%.1f' % max(w['tstar'] for w in au))
    R['aumic'] = dict(ours_mJy=jan['ours_mJy'], n_window=len(au),
                      eps_min=min(5.0 * w['rms'] / jan['ours_mJy'] for w in au),
                      tstar_max=max(w['tstar'] for w in au))

    # --------------------------------------- 7 the branch that still fails outright
    epsmin = min(w['eps'] for w in W if w['eps'] is not None)
    m('CxMarginBp', '%.0f' % (epsmin / SPEC['bandpass_amp_worst_band']))
    m('CxMarginBpNom', '%.0f' % (epsmin / SPEC['bandpass_amp_accuracy']))
    R['bandpass_margin'] = dict(eps_min=epsmin,
                                worst_band=epsmin / SPEC['bandpass_amp_worst_band'],
                                nominal=epsmin / SPEC['bandpass_amp_accuracy'])

    # ============================================================== the clauses
    # A1 the published sigma must BE the stacked noise.  smin = 5.sigma holds to
    # a fraction of a per cent in both files; a per-integration noise would miss
    # by a factor of order twenty.  Fails if either file is read in the other's
    # units, which is how this would go wrong.
    for samp, v in ni.items():
        assert abs(v['median'] - 1.0) < 1e-3, (samp, v)
        assert v['frac_within_one_pct'] > 0.90, (samp, v)
        # the discriminating clause: a per-integration noise would be larger
        # by roughly the square root of the integration count, so the ratio
        # would sit near a twentieth and nowhere near unity.
        assert v['lo'] > 0.5 and v['hi'] < 2.0, (samp, v)
        assert v['n'] > 100, (samp, v)
    # A2 the measured continuum must actually exceed the photospheric one by a
    # large factor somewhere, or the referee's premise is false and nothing
    # below is worth reporting.
    assert max(ratio.values()) > 100.0, sorted(ratio.items())
    # A3 (inside join_continuum) no map shared between two identities.
    # A4 is asserted above, before anything reads the joined rows.
    # A9 where a map records the execution blocks it was made from, at least
    # one of them must be a block of that star's own windows, and the tightest
    # residual bound must come from such a window.  Non-vacuous: the number of
    # maps that record their blocks is published and must exceed zero.
    chk = [(c, sorted(c['identities'])[0]) for c in C
           if c['ebs'] and c['identities']]
    m('CxNEbChecked', '%d' % len(chk))
    assert len(chk) > 0, 'A9: no map records its execution blocks'
    for c, st in chk:
        assert set(c['ebs']) & {w['eb'] for w in W if w['star'] == st}, \
            ('A9: %s records blocks %s, none of which is a block of %s'
             % (c['file'], c['ebs'], st))
    assert M.get('CxResidBestSameBlock') == 'yes', (
        'A9: the quoted residual bound rests on a continuum measured in a '
        'different execution block')
    # A5 counts are the length of their own set, never a remembered integer.
    assert int(M['CxNAdmit']) == len(adm)
    assert int(M['CxNAdmitStar']) == len(set(admstars))
    # A6 the verdict the prose rests on is READ: at least one window admits the
    # mechanism.  If this ever becomes false the two paragraphs of Appendix B
    # that report it must be rewritten, so it stops the build rather than
    # letting the prose and the measurement part company.
    assert len(adm) >= 1, (
        'A6: no window admits the mechanism any more -- Appendix B now claims '
        'something the data no longer say')
    # A7 the residual bound must be the identity it is quoted as, not a second
    # calculation of the same thing: T_star/5 times the required error.
    for w in adm:
        lhs = w['tstar'] * w['rms'] / w['s_meas']
        assert abs(lhs - w['tstar'] * w['eps'] / 5.0) < 1e-9, w['star']
    # A8 a map must never be used outside its own band, so no dust spectral
    # index and no assumed dust temperature can enter anywhere.  Checked
    # positively over a non-empty set, and every map actually used must carry
    # a band tag, so the clause cannot pass by having nothing to compare.
    # The selftest demonstrates it by relabelling the maps into a band the
    # survey does not observe, which empties the join.
    used = [(w, bystar[w['star']]) for w in W if w.get('s_meas')]
    assert used and all(c['band'] == w['band'] for w, c in used), 'A8'
    assert all(c['band'] is not None for w, c in used), 'A8 untagged map used'

    R['macros'] = dict(M)
    R['_provenance'] = dict(generator='calib_r16.py', round=630,
                            eps_cap=eps_cap, drive=drive,
                            specs=SPEC, continuum_provenance=PROV)
    if write:
        suffix = '' if not drive else '_drive%d' % drive
        out = OUT if not suffix else OUT.replace('.tex', suffix + '.tex')
        with open(out, 'w') as fh:
            fh.write('%% GENERATED by calib_r16.py (round 630) '
                     '-- do not hand-edit.\n')
            for k in sorted(M):
                fh.write('\\newcommand{\\%s}{%s}\n' % (k, M[k]))
        jout = JSONOUT if not suffix else JSONOUT.replace('.json',
                                                          suffix + '.json')
        with open(jout, 'w') as fh:
            json.dump(R, fh, indent=1, sort_keys=True)
    return R, M, W, C


# ===================================================================== selftest
def _selftest():
    ok_all = True

    def show(name, fired):
        nonlocal ok_all
        print('  %-62s %s' % (name, 'FIRES' if fired else 'DID NOT FIRE'))
        ok_all = ok_all and fired

    R, Mx, W, C = run(write=False)
    print('  baseline runs clean, %d macros' % len(Mx))

    def drive(patch, restore):
        try:
            M.clear()
            patch()
            run(write=False)
            return False
        except AssertionError:
            return True
        finally:
            restore()
            M.clear()

    # A1: read the hold-out's smin as though it were in mJy.
    orig_lw = load_windows

    def wrong_units():
        def f():
            Wx = orig_lw()
            for w in Wx:
                if w['sample'] == 'holdout' and w['smin']:
                    w['smin'] = w['smin'] * 1e3
            return Wx
        globals()['load_windows'] = f
    show('A1 the hold-out smin read in the wrong units stops the build',
         drive(wrong_units, lambda: globals().__setitem__('load_windows',
                                                          orig_lw)))

    # A1 again: a per-integration noise instead of the combined one.
    def per_int():
        def f():
            Wx = orig_lw()
            for w in Wx:
                if w['onsrc']:
                    w['rms'] = w['rms'] * math.sqrt(max(w['onsrc'], 1.0))
            return Wx
        globals()['load_windows'] = f
    show('A1 a per-integration noise in place of the stacked one stops it',
         drive(per_int, lambda: globals().__setitem__('load_windows', orig_lw)))

    # A2: put the measured continuum back at the photospheric level.
    orig_lc = load_continuum

    def photospheric():
        def f():
            Cx = orig_lc()
            for c in Cx:
                c['s_mjy'] = 1e-4
            return Cx
        globals()['load_continuum'] = f
    show('A2 a continuum no brighter than the photosphere stops the build',
         drive(photospheric,
               lambda: globals().__setitem__('load_continuum', orig_lc)))

    # A3: throw the identifiers away and let a name that ignores the
    # abbreviating digits do the joining -- which is how this project has
    # merged a resolved pair thirteen times.  LP 476-207's two components must
    # then collide and stop the build.
    orig_nn = norm_name

    def namekeyed():
        globals()['norm_name'] = lambda s: re.sub(r'\s*\d{6,}$', '',
                                                  orig_nn(s)).strip()

        def f():
            Cx = orig_lc()
            for c in Cx:
                c['gaia'] = None
                c['name'] = globals()['norm_name'](c['raw'])
            return Cx
        globals()['load_continuum'] = f

    def unname():
        globals()['norm_name'] = orig_nn
        globals()['load_continuum'] = orig_lc
    show('A3 a name-keyed join onto a resolved pair stops the build',
         drive(namekeyed, unname))

    # A6: raise the bar to zero admitted windows and the verdict clause must go.
    try:
        M.clear()
        run(write=False, eps_cap=1e-9)
        show('A6 a verdict with no admitting window stops the build', False)
    except AssertionError:
        show('A6 a verdict with no admitting window stops the build', True)
    M.clear()

    # A6 the other way: the drive at the published cap must NOT fire.
    try:
        M.clear()
        run(write=False)
        show('A6 drive at the published cap does not fire', True)
    except AssertionError:
        show('A6 drive at the published cap does not fire', False)
    M.clear()

    # A8: relabel every map into a band this survey does not observe and the
    # join must empty rather than extrapolate a continuum across bands.
    def wrongband():
        def f():
            Cx = orig_lc()
            for c in Cx:
                c['band'] = 1
            return Cx
        globals()['load_continuum'] = f
    show('A8 maps relabelled into another band empty the join and stop it',
         drive(wrongband,
               lambda: globals().__setitem__('load_continuum', orig_lc)))

    # A9: rename the blocks the maps record and the provenance clause must go.
    def wrongeb():
        def f():
            Cx = orig_lc()
            for c in Cx:
                c['ebs'] = [e + '_elsewhere' for e in c['ebs']]
            return Cx
        globals()['load_continuum'] = f
    show('A9 a continuum recorded in another block stops the build',
         drive(wrongeb,
               lambda: globals().__setitem__('load_continuum', orig_lc)))

    # A4: break the join and it must fire rather than publish zero quietly.
    orig_j = join_continuum

    def nojoin():
        globals()['join_continuum'] = lambda W_, C_: ({}, 0)
    show('A4 an empty continuum join stops the build',
         drive(nojoin, lambda: globals().__setitem__('join_continuum', orig_j)))

    return 0 if ok_all else 1


if __name__ == '__main__':
    if '--selftest' in sys.argv:
        raise SystemExit(_selftest())
    Rr, Mm, Ww, Cc = run()
    print('calib_r16: %d macros -> %s' % (len(Mm), os.path.basename(OUT)))
    for k in sorted(Mm):
        print('   %-24s %s' % (k, Mm[k]))
