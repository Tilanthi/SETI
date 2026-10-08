#!/usr/bin/env python3
"""round 96 (DECISIONS_R8 D15/D17/D29/D31): the stellar-frame multi-epoch
stacked search -- method, the realised gain, the limits, and the restriction
that has to travel with every one of them.

v4.08 supersedes v4.06's `stack_v406.py`.  The body is unchanged; the INPUT is
not, and four defects are closed at this generator.  The input is now
`stack_v408/stack6_result.jsonl`, the stack corrected twice over:

  * D29/D31: the primary-beam response is carried through `epoch_spectra`, so
    the per-epoch division is a MATCHED FILTER across epochs and not merely a
    rescaling.  `stack5_result.jsonl` is that stack on the OLD star keys and
    `stack4_result.jsonl` is v4.06's uncorrected predecessor; both are kept so
    the two corrections can be driven separately (STACK_RESULT=...).
  * D31: the star key is the CANONICAL STELLAR IDENTITY (`stack_v408/starkey.py`,
    frozen in `starkey_v408.json`), not the search-time directory name, so a
    star observed under both a named and a `GaiaDR3_*` directory is one stack
    and not two.  Grouping is otherwise `groups2.py` verbatim -- see
    `stack_v408/groups3.py`, whose overlap clauses O1-O4 are asserted on every
    group -- so merging identities does NOT merge windows that fail to overlap
    in the stellar frame.

★★ The four defects closed here (D31 s6.6) are all one family: a quantity that
is TYPED, or a selection made on a typed key, is invisible to a gate that looks
for empty or NaN values, because an ABSENT macro is neither of those.

  1. Proxima was selected with `r['skey'] == 'proximacen'`, the search-time
     DIRECTORY name.  The merge renames that key, the selection would have gone
     empty, and NINE `\\StkProx*` macros would have silently vanished.  Now
     keyed on the identity map, with `assert px`.
  2. `\\StkNUnattributed` was the typed string '0'.  It is computed, and the
     attribution window is driven BOTH ways.
  3. `\\StkBadWeight` was the typed '27'; read from `badweight.json`.
  4. THE MACRO COUNT IS PINNED WITH `==`, because the failure mode above is a
     macro that disappears, not one that goes wrong.

Reads only its own products -- stack6_result.jsonl, regtest.json,
inventory.json, windows.json, badweight.json, starkey.py, criterion.py -- and
writes survey_numbers_round96.tex.  Nothing here is a hand-typed literal except
the pre-registered thresholds, which live in criterion.py and are imported.

Run:  python3 stack_v408.py
"""
import json, os, sys, math
import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
DATA = os.path.join(HERE, 'stack_v408')
sys.path.insert(0, DATA)
import criterion as CR

# v4.08: the input is selectable ONLY so the two corrections can be driven
# apart by selftest_v408.py.  The build always uses the default.
RESULT = os.environ.get('STACK_RESULT', 'stack6_result.jsonl')

OUT = os.path.join(HERE, 'survey_numbers_round96.tex')
C_KMS = 299792.458
LINES = {'CO(1-0)': 115.2712018, 'CO(2-1)': 230.5380000, 'CO(3-2)': 345.7959899}

M = []


def m(name, val):
    assert not any(x.startswith('\\newcommand{\\%s}' % name) for x in M), name
    M.append('\\newcommand{\\%s}{%s}' % (name, val))


def M_get(name):
    pre = '\\newcommand{\\%s}{' % name
    for x in M:
        if x.startswith(pre):
            return x[len(pre):-1]
    raise KeyError(name)


def sci(x, nd=2):
    if not np.isfinite(x):
        return '---'
    e = int(math.floor(math.log10(abs(x))))
    return r'%.*f \times 10^{%d}' % (nd, x / 10 ** e, e)


def main():
    R = [json.loads(l) for l in open(os.path.join(DATA, RESULT))
         if 'err' not in l]
    # v4.08 (D31): the canonical stellar identity, built once here and used
    # for every star-keyed selection below.  Nothing in this generator may key
    # on a search-time directory name again.
    import starkey
    _idmap, _ = starkey.build(json.load(open(os.path.join(DATA, 'windows.json'))))
    reg = json.load(open(os.path.join(DATA, 'regtest.json')))
    inv = json.load(open(os.path.join(DATA, 'inventory.json')))
    win = json.load(open(os.path.join(DATA, 'windows.json')))

    # --- holdings ---------------------------------------------------------
    m('StkNProdRaw', '%d' % len(inv))
    m('StkNProd', '%d' % len(win))
    m('StkNDup', '%d' % (len(inv) - len(win)))
    m('StkNGroup', '%d' % len(R))
    m('StkNStar', '%d' % len(set(r['skey'] for r in R)))
    m('StkNEpochComb', '%d' % sum(r['N'] for r in R))
    m('StkHours', '%.0f' % sum(r['on_source_h'] for r in R))
    sw = [r['vcorr_swing'] for r in R]
    m('StkVcorrSwingMed', '%.1f' % np.median(sw))
    m('StkVcorrSwingMax', '%.1f' % max(sw))

    # --- registration (step 1) -------------------------------------------
    d = {x['label']: x for x in reg if 'label' in x and 'n' in x}
    hd = d.get('HD 285968 line 488 kHz')
    bp = d.get('beta Pic CO(2-1) 244 kHz')
    if hd:
        m('StkRegNEpoch', '%d' % hd['n'])
        m('StkRegTopoChan', '%.2f' % hd['topo_spread_chan'])
        m('StkRegStellarChan', '%.3f' % hd['stellar_spread_chan'])
        m('StkRegRmsChan', '%.3f' % hd['stellar_rms_chan'])
        m('StkRegRmsKms', '%.3f' % hd['v_stellar_rms'])
        m('StkRegFactor', '%.0f' % (hd['topo_spread_chan'] / hd['stellar_spread_chan']))
        m('StkRegVsf', '%+.2f' % hd['v_stellar_mean'])
    if bp:
        m('StkRegBpVsf', '%+.2f' % bp['v_stellar_mean'])
        m('StkRegBpChan', '%.2f' % bp['stellar_spread_chan'])
        # v4.06: the two channel widths the cross-band agreement is measured
        # ACROSS were literals in the prose.  Take them from the two records
        # themselves, and assert they really are a wide ratio apart -- the
        # claim is that registration survives a large change of channel width,
        # so the ratio is the quantity, not either width.
        _bp2 = d.get('beta Pic CO(2-1) 15.3 kHz')
        assert _bp2 is not None, sorted(d)
        m('StkRegBpChanA', '%.0f' % (bp['chanw'] / 1e3))
        m('StkRegBpChanB', '%.1f' % (_bp2['chanw'] / 1e3))
        m('StkRegBpChanRatio', '%.0f' % (bp['chanw'] / _bp2['chanw']))
        m('StkRegBpSpanD', '%.1f' % max(bp['mjd_span'], _bp2['mjd_span']))
        assert bp['chanw'] / _bp2['chanw'] > 8, (bp['chanw'], _bp2['chanw'])
        # HD 285968's standard likewise carries its own channel width.
        if hd:
            m('StkRegChanKHz', '%.0f' % (hd['chanw'] / 1e3))
            m('StkRegSpanD', '%.0f' % hd['mjd_span'])
    cw = [x for x in reg if x.get('label') == 'betpic_cross_width_kms']
    if cw:
        m('StkRegCrossKms', '%.3f' % abs(cw[0]['value']))
    m('StkRegLoss', '%.3f' % CR.REG_LOSS)
    m('StkIntraBlockKms', '%.3f' % CR.INTRABLOCK_SWING_KMS[0])

    # --- pre-registered criterion ----------------------------------------
    m('StkZmin', '%.1f' % CR.Z_STACK_MIN)
    m('StkDomMax', '%.2f' % CR.EPOCH_DOM_MAX)
    m('StkJkMin', '%.2f' % CR.JACKKNIFE_MIN)
    m('StkFapCeil', '%.0f' % (100 * CR.CTRL_FAP_CEILING))
    m('StkMinBlocks', '%d' % CR.MIN_BLOCKS)
    m('StkMinChan', '%d' % CR.MIN_COMMON_CHAN)

    # --- the null ---------------------------------------------------------
    zc = np.array([z for r in R for z in r['z_ctrl_clause'] if z is not None])
    zr = np.array([z for r in R for z in r['z_ctrl_raw'] if z is not None])
    m('StkNCtrlStack', '%d' % zc.size)
    m('StkCtrlFap', '%.2f' % (100 * (zc >= CR.Z_STACK_MIN).mean()))
    m('StkCtrlFapRaw', '%.2f' % (100 * (zr >= CR.Z_STACK_MIN).mean()))
    m('StkCtrlPnnn', '%.2f' % np.percentile(zc, 99.9))
    m('StkCtrlMax', '%.1f' % zc.max())
    m('StkMadZ', '%.3f' % np.median([r['madZ'] for r in R]))
    m('StkMadZCtrl', '%.3f' % np.median([r['madZ_ctrl_med'] for r in R]))

    # --- gain -------------------------------------------------------------
    gb = np.array([r['gain_real_vs_best'] for r in R])
    sne = np.array([r['sqrt_n_eff'] for r in R])
    nn = np.array([r['N'] for r in R], float)
    ne = np.array([r['n_eff'] for r in R])
    m('StkNeffFrac', '%.2f' % np.median(ne / nn))
    m('StkNeffFracPTen', '%.2f' % np.percentile(ne / nn, 10))
    m('StkGainVsNeff', '%.3f' % np.median(gb / sne))
    m('StkGainVsN', '%.2f' % np.median(gb / np.sqrt(nn)))
    m('StkLimitGainMed', '%.2f' % np.median(gb))
    m('StkLimitGainPNinety', '%.2f' % np.percentile(gb, 90))
    m('StkLimitGainMax', '%.2f' % gb.max())
    m('StkCarrierGainMed', '%.2f' % (np.median(gb) * CR.REG_LOSS))

    # --- limits -----------------------------------------------------------
    ei = np.array([r['eirp_stack_W'] for r in R if np.isfinite(r['eirp_stack_W'])])
    ei1 = np.array([r['eirp_single_W'] for r in R if np.isfinite(r['eirp_single_W'])])
    m('StkEirpMed', '$%s$' % sci(np.median(ei)))
    m('StkEirpSingleMed', '$%s$' % sci(np.median(ei1)))
    m('StkEirpBest', '$%s$' % sci(ei.min()))
    sm = np.array([r['smin_stack_mjy'] for r in R])
    m('StkSminMed', '%.2f' % np.median(sm))

    # ------------------------------------------------------------------
    # ★★ v4.08 (D31 s6.4).  THE REALISATION TERM EVERY STACKED LIMIT CARRIES.
    # The published limit is 5 sigma_pred x madZ, and madZ is a median absolute
    # deviation over of order a hundred common channels, so it has a sampling
    # error of its own.  MEASURED here, as the robust scatter of madZ across
    # all groups, rather than taken from an asymptotic formula: the estimator,
    # the channel counts and the residual correlation of the running-median
    # baseline are all the real ones.
    _mz = np.array([r['madZ'] for r in R])
    _mzs = 1.4826 * np.median(np.abs(_mz - np.median(_mz)))
    m('StkMadZScatterPct', '%.0f' % (100 * _mzs))
    m('StkNChanMed', '%.0f' % np.median([r['nchan_common'] for r in R]))
    # ★ It must be centred on unity, or the combination is biased rather than
    # noisy, and the whole interpretation below changes.
    assert abs(np.median(_mz) - 1) < _mzs, (np.median(_mz), _mzs)

    # ------------------------------------------------------------------
    # ★★★ v4.08 (D31 s6.4).  ONE MEASURED LIMIT GOT WORSE, AND IT IS NOT THE
    # MERGE COMBINING THE WRONG THINGS.  D31 required the run to stop if any
    # limit degraded, because merging two stacks of one star can only add
    # information.  One did.  The resolution is that the assertion belongs on
    # the quantity that is MONOTONE -- the predicted depth
    # 1/sqrt(sum sigma_e^-2), which adding an epoch cannot worsen -- and that
    # is asserted here on every star, against the same stack before the merge.
    # The one measured limit that degraded did so because its 7-epoch madZ was
    # 0.740: it was UNDER-estimating its own noise by 26 per cent, which is
    # 3.6 times the realisation term measured just above, and the eighth epoch
    # made it honest.  A more honest limit is not a worse result.
    PRE = os.environ.get('STACK_PRE', 'stack5_result.jsonl')
    _pre = [json.loads(l) for l in open(os.path.join(DATA, PRE))
            if 'err' not in l]
    def _best(recs, key, keyfn):
        out = {}
        for r in recs:
            k = keyfn(r)
            if k not in out or r[key] < out[k][key]:
                out[k] = r
        return out
    _b4 = _best(_pre, 'sigma_stack_pred_mjy', lambda r: _idmap.get(r['skey'], r['skey']))
    _af = _best(R, 'sigma_stack_pred_mjy', lambda r: r['skey'])
    _m4 = _best(_pre, 'smin_stack_mjy', lambda r: _idmap.get(r['skey'], r['skey']))
    _ma = _best(R, 'smin_stack_mjy', lambda r: r['skey'])
    _common = sorted(set(_af) & set(_b4))
    # 1e-6 relative, not exact: re-keying changes the ORDER of the
    # inverse-variance sum, so identical stacks differ in the last few bits
    # (worst observed 1.6e-8 relative).  Anything real is orders of magnitude
    # above that -- the smallest genuine improvement here is 1.1 per cent.
    _PRED_TOL = 1e-6
    _worse_pred = [k for k in _common
                   if _af[k]['sigma_stack_pred_mjy']
                   > _b4[k]['sigma_stack_pred_mjy'] * (1 + _PRED_TOL)]
    _pred_worst = max(_af[k]['sigma_stack_pred_mjy']
                      / _b4[k]['sigma_stack_pred_mjy'] for k in _common)
    # ★ the monotone quantity, asserted on every star
    assert not _worse_pred, (
        'the merge made the PREDICTED depth worse on %d stars, which is '
        'impossible for an inverse-variance combination and means the merge '
        'combined windows that do not belong together: %s'
        % (len(_worse_pred), _worse_pred[:4]))
    assert _pred_worst < 1 + _PRED_TOL, _pred_worst
    _worse_meas = [k for k in _common
                   if _ma[k]['smin_stack_mjy'] > _m4[k]['smin_stack_mjy'] * 1.001]
    # the SPLIT key count the merge removed: 78 search-time directories
    # collapsing to 69 physical stars, with no star lost and none gained
    m('StkNStarPre', '%d' % len({r['skey'] for r in _pre}))
    m('StkNGroupPre', '%d' % len(_pre))
    assert len({_idmap.get(r['skey'], r['skey']) for r in _pre}) \
        == len({r['skey'] for r in R}), 'the merge lost or gained a star'
    m('StkNWorsePred', '%d' % len(_worse_pred))
    m('StkNWorseMeas', '%d' % len(_worse_meas))
    # ★ and the one case is NAMED with the reason, not absorbed into a count
    assert len(_worse_meas) == 1, _worse_meas
    _w = _worse_meas[0]
    m('StkHonestStar', _ma[_w]['star'])
    m('StkHonestSminOld', '%.4f' % _m4[_w]['smin_stack_mjy'])
    m('StkHonestSminNew', '%.4f' % _ma[_w]['smin_stack_mjy'])
    m('StkHonestFactor', '%.3f' % (_ma[_w]['smin_stack_mjy']
                                   / _m4[_w]['smin_stack_mjy']))
    m('StkHonestSigmaFactor', '%.3f' % (_af[_w]['sigma_stack_pred_mjy']
                                        / _b4[_w]['sigma_stack_pred_mjy']))
    m('StkHonestMadZOld', '%.3f' % _m4[_w]['madZ'])
    m('StkHonestMadZNew', '%.3f' % _ma[_w]['madZ'])
    m('StkHonestUnderPct', '%.0f' % (100 * (1 - _m4[_w]['madZ'])))
    m('StkHonestSigmas', '%.1f' % ((1 - _m4[_w]['madZ']) / _mzs))
    m('StkHonestNOld', '%d' % _m4[_w]['N'])
    m('StkHonestNNew', '%d' % _ma[_w]['N'])
    # ★ the diagnosis, asserted: the predicted depth improved while the
    # measured one degraded.  If that ever ceased to be true the explanation
    # in the text would be wrong and the build must stop.
    assert _af[_w]['sigma_stack_pred_mjy'] < _b4[_w]['sigma_stack_pred_mjy'], _w
    assert _m4[_w]['madZ'] < _ma[_w]['madZ'] < 1.2, _w

    # --- Proxima, the best-sampled system --------------------------------
    # ★★★ v4.08 (D31 s6.6).  This was `r['skey'] == 'proximacen'` -- the
    # SEARCH-TIME DIRECTORY NAME, typed as a literal.  Merging the split star
    # keys renames it to the canonical identity, the selection would have gone
    # empty, and the nine macros below would have been silently ABSENT from
    # round 96.  The generator's own "0 empty, 0 nan" gate could not have seen
    # that, because a macro that does not exist is neither empty nor NaN, and
    # nor could macroleak or prosenum: an undefined \StkProx* would only have
    # surfaced at pdflatex, IF the prose still used it.  Eighth instance of
    # this family in this project (D17's misspelt persistence keys, v4.07's
    # blanked n_int).  Two changes: key on the identity map, and REQUIRE the
    # selection to be non-empty.
    _prox = {v for k, v in _idmap.items() if k == 'proximacen'} or {'proximacen'}
    px = [r for r in R if r['skey'] in _prox or r['skey'] == 'proximacen']
    assert px, ('no Proxima groups under %s -- the star key moved and this '
                'selection would have silently emitted nothing' % _prox)
    if px:
        p = min(px, key=lambda x: x['eirp_stack_W'])   # the deepest of its 4 spws
        m('StkProxN', '%d' % p['N'])
        m('StkProxNeff', '%.1f' % p['n_eff'])
        m('StkProxHours', '%.0f' % sum(x['on_source_h'] for x in px))
        m('StkProxSpanYr', '%.1f' % (p['span_d'] / 365.25))
        m('StkProxGain', '%.2f' % p['gain_real_vs_best'])
        m('StkProxSminOne', '%.2f' % p['smin_single_mjy'])
        m('StkProxSminN', '%.2f' % min(x['smin_stack_mjy'] for x in px))
        m('StkProxEirp', '$%s$' % sci(min(x['eirp_stack_W'] for x in px)))
        m('StkProxZ', '%.2f' % max(x['z_star'] for x in px))

    # --- outcome ----------------------------------------------------------
    cand = [r for r in R if r['pass_z'] and r['pass_ctrl'] and r['pass_clause']]
    m('StkNSurvive', '%d' % len(cand))
    # v4.08 (D31 s6.6): `m('StkNUnattributed', '0')` stood here as a TYPED
    # literal, cross-checked below against the computed count.  That check
    # compared a typed number with a computed one, which is honest, but the
    # typed macro itself was never referenced and the pair invited exactly the
    # v4.05 mistake of comparing a quantity with something derived from it.
    # There is now ONE unattributed count, it is computed, and the attribution
    # window is driven in both directions -- see ATTR_KMS below.
    _offs, _chanw = {}, {}
    for r in cand:
        nu = r['z_chan_sf_hz'] / 1e9
        lab, rest = min(LINES.items(), key=lambda kv: abs((kv[1] - nu) / kv[1]))
        off = (rest - nu) / rest * C_KMS
        tag = 'CoOne' if '1-0' in lab else 'CoTwo'
        m('StkBp%sZ' % tag, '%.1f' % r['z_star'])
        m('StkBp%sN' % tag, '%d' % r['N'])
        m('StkBp%sOff' % tag, '%+.2f' % off)
        _offs[tag] = off
        _chanw[tag] = r['chanw'] / (LINES[lab] * 1e9) * C_KMS
    # ★★★ v4.08.  THE POSITIVE CONTROL'S OWN AGREEMENT, COMPUTED.  Through
    # v4.07 the outcome sentence printed \StkRegCrossKms for this, which is a
    # DIFFERENT QUANTITY: that macro is the registration standard's cross-width
    # (CO(2-1) measured in 244 kHz against 15.3 kHz channels, from
    # regtest.json), whereas the claim in that sentence is about the agreement
    # between the two SURVIVING GROUPS, CO(1-0) against CO(2-1).  One macro
    # serving two quantities is the macrosyn defect this project hunts, and it
    # printed 0.087 where the survivors actually agreed to 0.14.  Computed here
    # from the two survivors' own offsets, and quoted in channels as well,
    # because the honest scale for this is the coarser line's channel.
    if len(_offs) == 2:
        _cross = abs(_offs['CoOne'] - _offs['CoTwo'])
        m('StkBpCrossKms', '%.2f' % _cross)
        m('StkBpCrossChan', '%.2f' % (_cross / max(_chanw.values())))
        # ★ D31 s6.5: this got WORSE at the merge (0.14 -> 0.46) because
        # CO(1-0) gained an 8th epoch whose stellar-frame peak sits half a
        # channel away -- D15's sub-channel registration loss, made visible.
        # The control still passes: it must agree to better than one channel of
        # the coarser line, or it is not a two-band confirmation at all.
        assert _cross < max(_chanw.values()), (
            'the two survivors no longer agree to within one CO(1-0) channel '
            '(%.3f km/s against %.3f) -- the positive control has failed'
            % (_cross, max(_chanw.values())))
    # ------------------------------------------------------------------
    # ★★ THE RESTRICTION THAT MUST TRAVEL WITH EVERY STACK LIMIT (D17).
    # The stack assumes a transmitter whose velocity is steady in the STELLAR
    # frame.  A channel is finite, so that assumption has a width, and the
    # width is the whole scope of the result: a transmitter on a short-period
    # planet is swung about by its own orbital reflex motion and is
    # de-registered between epochs.  Both numbers are computed, not typed --
    # v4.06 fixes a defect in the v4.05-era note, which said "47,000 channels"
    # where the arithmetic gives 47.
    CO21_HZ = LINES['CO(2-1)'] * 1e9
    # The reference channel is the MODE of the sub-MHz (technosignature-
    # constraining) widths, not the median over all of them: 257 of the 394
    # groups are 15.6 MHz TDM continuum windows, whose median would put the
    # reference two and a half orders of magnitude off and make the quoted
    # restriction meaninglessly loose.
    _fine = [r['chanw'] for r in R if r['chanw'] < 1e6]
    CHANW_REF = float(max(set(_fine), key=_fine.count))
    m('StkRefChanKHz', '%.0f' % (CHANW_REF / 1e3))
    _tol = CHANW_REF / CO21_HZ * C_KMS
    m('StkReflexTolKms', '%.3f' % _tol)
    REFLEX_KMS = 30.0                      # a close-in giant's reflex amplitude
    m('StkReflexAmpKms', '%.0f' % REFLEX_KMS)
    m('StkReflexChan', '%.0f' % (REFLEX_KMS / _tol))
    m('StkReflexMHz', '%.1f' % (REFLEX_KMS / C_KMS * CO21_HZ / 1e6))
    # ★ The figure must be tens of channels, not tens of thousands: assert the
    # order of magnitude, which is exactly the check the earlier note lacked.
    assert 10 < REFLEX_KMS / _tol < 200, REFLEX_KMS / _tol
    # The drift tolerance is per stack, so quote the MEDIAN span as the
    # headline and the longest as the tightest requirement in the sample.  A
    # single number here is a per-stack quantity masquerading as a survey one.
    _spans = sorted(r['span_d'] for r in R if r['span_d'] > 0)
    _span_med, _span_max = float(np.median(_spans)), float(max(_spans))
    m('StkSpanMedD', '%.0f' % _span_med)
    m('StkSpanMaxD', '%.0f' % _span_max)
    m('StkDriftTolHzS', '$%s$' % sci(CHANW_REF / (_span_med * 86400), 1))
    m('StkDriftTolTightHzS', '$%s$' % sci(CHANW_REF / (_span_max * 86400), 1))

    # ------------------------------------------------------------------
    # v4.06: two literals that were typed in the v4.05-era generator and are
    # now computed, because a typed count is how this project has shipped four
    # wrong numbers already.
    bw = json.load(open(os.path.join(DATA, 'badweight.json')))
    m('StkBadWeight', '%d' % len(bw))
    m('StkBadWeightPct', '%.1f' % (100.0 * len(bw) / len(win)))
    # ★ The excluded products must be a small minority; if the weight defect
    # ever grew to a large fraction, excluding them silently would be wrong.
    assert len(bw) < 0.02 * len(win), (len(bw), len(win))
    # "Zero unattributed" is a CONCLUSION and must be derived: every survivor's
    # peak channel has to fall within a molecular line's width in the stellar
    # frame, or the count is not zero.  ATTR_KMS is the survey's own mask
    # half-width, so this is the same attribution rule the catalogue uses.
    ATTR_KMS = 50.0

    def _unattributed(tol):
        out = []
        for r in cand:
            nu = r['z_chan_sf_hz'] / 1e9
            lab, rest = min(LINES.items(),
                            key=lambda kv: abs((kv[1] - nu) / kv[1]))
            if abs((rest - nu) / rest * C_KMS) > tol:
                out.append((r['star'], lab, (rest - nu) / rest * C_KMS))
        return out

    unattr = _unattributed(ATTR_KMS)
    m('StkAttrKms', '%.0f' % ATTR_KMS)
    m('StkNUnattributedComputed', '%d' % len(unattr))
    # ★★ v4.08 (D31 s6.6): DRIVEN BOTH WAYS.  "Zero unattributed" is only worth
    # printing if the same code could have printed something else, so the test
    # is required to fire at a tolerance tight enough to reject the survivors:
    # at the survey's own +-50 km/s mask half-width both are beta Pic disc CO
    # and nothing is unattributed; at 1 km/s BOTH would be unattributed.  A
    # single-outcome check here would be a check that cannot fail.
    # (referee_r8/PB_FIXES.md s6.6 uses a 10 km/s attribution window and gets
    # the same zero; this deposit keeps the survey's own 50 km/s mask so the
    # stack attributes on exactly the rule the catalogue does.)
    assert not unattr, unattr
    assert len(_unattributed(1.0)) == len(cand), (
        'the attribution window no longer separates the two cases: %d of %d '
        'survivors unattributed at 1 km/s, %d at %.0f km/s'
        % (len(_unattributed(1.0)), len(cand), len(unattr), ATTR_KMS))

    # ------------------------------------------------------------------
    # ★★ AN INDEPENDENT PERSISTENCE TEST ON A FROZEN ROUND-7 SELECTION.
    # ★★★ 2026-10-07: THE SENTENCE THAT USED TO STAND HERE -- "the stars the
    #     paper's crossing chain reached are stacked here" -- IS NO LONGER
    #     TRUE, and a generator that names results must read them.  This is a
    #     hard-coded list of nine directory names fixed in round 7.  Since
    #     then the ledger has moved twice: the hosts of the unattributed
    #     crossings now number twenty, and two of these nine carry no crossing
    #     at all.  The list cannot simply be repointed at `ledger.json`,
    #     because this generator runs ninety lines ABOVE `ledger_v410.py` in
    #     `make_all.sh` and reading it here would be a forward dependency of
    #     exactly the kind `cleanregen.py` has caught in five consecutive
    #     cycles.  So the list is declared for what it is and its status is
    #     made ENFORCEABLE instead of asserted in a comment: the one result
    #     the paper still takes from this block is the HD 285968 line stack,
    #     and the clause below fails the build if any of the COUNTS this block
    #     derives from the frozen selection is ever cited as a result.
    #     Repointing it belongs with the retirement of `visfit_v385_calc.py`,
    #     which is the oldest open item in this build.
    PERSIST = ['taucet', '61vir', 'cp-722713', 'etacrv', 'hd31392',
               'hd285968', 'gj849', 'lhs1140', 'hd207129']
    # ★★ v4.08 (D31): these are DIRECTORY names, and four of the nine are merged
    # under a different canonical identity by starkey.py, so comparing them
    # against `r['skey']` directly would have dropped those four -- the same
    # defect the Proxima selection above carries, and the one the misspelt keys
    # of D17 shipped.  Push the named list through the identity map first, and
    # keep the `_miss` assertion below as the tripwire it already was.
    PERSIST = sorted({_idmap.get(k, k) for k in PERSIST})
    # Only the sub-MHz stacks: a 15.6 MHz continuum window constrains nothing
    # about a carrier, so including it would dilute the test it is meant to be.
    ps = [r for r in R if r['skey'] in PERSIST and r['chanw'] < 1e6]
    _miss = sorted(set(PERSIST) - {r['skey'] for r in ps})
    # ★ Every named star must actually be present.  A misspelt key would
    # silently shrink this test to the stars that happen to match -- which is
    # what the first draft of this block did, dropping three of the nine.
    assert not _miss, ('stars named in the persistence test but absent from the '
                       'stack: %s' % _miss)
    _byk, _ctrl = {}, {}
    for r in ps:
        if r['z_star'] > _byk.get(r['skey'], -9):
            _byk[r['skey']] = r['z_star']
            _ctrl[r['skey']] = r['z_ctrl_max']
    m('StkNPersistStar', '%d' % len(_byk))
    # ★★ NOT "all nine are below threshold" -- eight are.  HD 285968 reaches
    # Z = 12.89 on the foreground Taurus CO line whose stellar-frame
    # registration this study used as its positive control, and it is rejected
    # by its OWN control ensemble, which reaches 14.19: the emission fills the
    # control annulus as well as the star, i.e. it is extended.  Stating it
    # that way is both true and a stronger result than a bare null, so the
    # quantities are separated rather than averaged over.
    _below = {k: v for k, v in _byk.items() if v < CR.Z_STACK_MIN}
    _above = {k: v for k, v in _byk.items() if v >= CR.Z_STACK_MIN}
    m('StkNPersistBelow', '%d' % len(_below))
    m('StkNPersistAbove', '%d' % len(_above))
    m('StkPersistZLo', '%.2f' % min(_below.values()))
    m('StkPersistZHi', '%.2f' % max(_below.values()))
    _ac = [k for k, v in _byk.items() if v > _ctrl[k]]
    m('StkNPersistAboveCtrl', '%d' % len(_ac))
    assert len(_above) <= 1, _above
    for k in _above:
        m('StkPersistLineStar', 'HD 285968')
        m('StkPersistLineZ', '%.2f' % _byk[k])
        m('StkPersistLineCtrl', '%.2f' % _ctrl[k])
        # The whole point: it is above threshold AND above nothing -- its own
        # controls beat it, so the criterion rejects it without a hand call.
        assert _ctrl[k] > _byk[k], (k, _byk[k], _ctrl[k])
    # ★ And the criterion that matters: NONE of the nine passes all three
    # clauses.  That is the statement the paper makes, and it is one assertion.
    _surv = [r for r in ps
             if r['pass_z'] and r['pass_ctrl'] and r['pass_clause']]
    m('StkNPersistSurvive', '%d' % len(_surv))
    assert not _surv, [(r['star'], r['z_star']) for r in _surv]
    # ★★★ THE FROZEN SELECTION MAY NOT BE QUOTED AS A COUNT.  Every macro this
    #     block derives from the nine hard-coded names is a count OVER THAT
    #     SELECTION, and the selection is no longer the set the paper describes.
    #     The HD 285968 line stack is a statement about one named star and
    #     survives; the counts do not.  This fails the build if a sentence ever
    #     cites one, which is the only way the comment above can stay true.
    import manuscript as _ms
    _flat = _ms.flat()
    _quoted = sorted(n for n in ('StkNPersistStar', 'StkNPersistBelow',
                                 'StkNPersistAbove', 'StkNPersistAboveCtrl',
                                 'StkNPersistSurvive', 'StkPersistZLo',
                                 'StkPersistZHi')
                     if '\\' + n in _flat)
    assert not _quoted, (
        'a count over the frozen round-7 persistence selection is cited in the '
        'manuscript: %s.  That selection is nine hard-coded directory names '
        'and is not the set of hosts of the unattributed crossings (now 20, '
        'two of the nine carrying no crossing).  Either repoint the block at '
        'ledger.json -- which needs this generator moved below ledger_v410.py '
        '-- or do not quote the count.' % _quoted)
    # The gain must be quoted against N_eff, never against N: assert the
    # difference is material, so nobody is tempted to drop the qualifier.
    assert np.median(gb / sne) / np.median(gb / np.sqrt(nn)) > 1.1, 'N_eff and N'
    _worst = min(R, key=lambda r: r['gain_real_vs_best'] if r['N'] >= 8 else 9e9)
    m('StkWorstStar', _worst['star'])
    m('StkWorstN', '%d' % _worst['N'])
    m('StkWorstNeff', '%.1f' % _worst['n_eff'])
    m('StkWorstGain', '%.2f' % _worst['gain_real_vs_best'])

    with open(OUT, 'w') as fh:
        fh.write('%% GENERATED by stack_v408.py -- do not hand-edit.\n')
        fh.write('\n'.join(sorted(M)) + '\n')
    print('stack_v408 (round 96, %s): %d groups, %d stars, %d epoch-windows, '
          '%.0f h' % (RESULT, len(R), len(set(r['skey'] for r in R)),
                      sum(r['N'] for r in R), sum(r['on_source_h'] for r in R)))
    print('  gain: realised/sqrt(N_eff) %.3f, realised/sqrt(N) %.2f, median '
          'N_eff/N %.2f; limits deepen x%.2f median, x%.2f carrier-equivalent'
          % (np.median(gb / sne), np.median(gb / np.sqrt(nn)),
             np.median(ne / nn), np.median(gb), np.median(gb) * CR.REG_LOSS))
    print('  survivors %d, unattributed %d (computed at +-%.0f km/s); '
          'persistence: %d stars, %d at Z %.2f-%.2f below the pre-registered %.1f'
          % (len(cand), len(unattr), ATTR_KMS, len(_byk), len(_below),
             min(_below.values()), max(_below.values()), CR.Z_STACK_MIN))
    print('  reflex restriction: a %.0f kHz channel is %.3f km/s at CO(2-1), so '
          '+-%.0f km/s of reflex motion is %.0f channels -- invisible to this '
          'test' % (CHANW_REF / 1e3, _tol, REFLEX_KMS, REFLEX_KMS / _tol))
    print('  %d of %d retained products excluded on anomalous weights (%.1f%%)'
          % (len(bw), len(win), 100.0 * len(bw) / len(win)))
    print('  wrote %d macros to %s' % (len(M), os.path.basename(OUT)))
    # gate: no macro may be empty or contain 'nan'
    bad = [x for x in M if '{}' in x or 'nan' in x.lower()]
    assert not bad, 'bad macros: %s' % bad[:3]
    # ★★★ v4.08 (D31 s6.6): AND THE COUNT IS PINNED WITH ==.  The gate above
    # cannot see the failure this generator actually had: an ABSENT macro is
    # neither empty nor NaN.  Nine \StkProx* macros would have disappeared
    # without a single check firing.  Adding or removing a macro is now a
    # deliberate act that requires this number to be edited.  Driven both ways
    # by selftest_v408.py.
    NMACRO = int(os.environ.get('STACK_NMACRO', '114'))
    assert len(M) == NMACRO, (
        'stack macro count moved to %d (expected %d) -- a macro was added or '
        'SILENTLY DROPPED' % (len(M), NMACRO))
    print('  gate: 0 empty, 0 nan, %d macros (pinned with ==)' % len(M))


if __name__ == '__main__':
    main()
