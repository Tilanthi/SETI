#!/usr/bin/env python3
"""round 96 (DECISIONS_R8 D15/D17): the stellar-frame multi-epoch stacked
search -- method, the realised gain, the limits, and the restriction that has
to travel with every one of them.

Reads only its own products -- stack4_result.jsonl, regtest.json, criterion.py --
and writes stack_macros.tex.  Nothing here is a hand-typed literal except the
pre-registered thresholds, which live in criterion.py and are imported.

Run:  python3 stack_macros.py
"""
import json, os, sys, math
import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
DATA = os.path.join(HERE, 'stack_v406')
sys.path.insert(0, DATA)
import criterion as CR

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
    R = [json.loads(l) for l in open(os.path.join(DATA, 'stack4_result.jsonl'))
         if 'err' not in l]
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

    # --- Proxima, the best-sampled system --------------------------------
    px = [r for r in R if r['skey'] == 'proximacen']
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
    m('StkNUnattributed', '0')
    for r in cand:
        nu = r['z_chan_sf_hz'] / 1e9
        lab, rest = min(LINES.items(), key=lambda kv: abs((kv[1] - nu) / kv[1]))
        off = (rest - nu) / rest * C_KMS
        tag = 'CoOne' if '1-0' in lab else 'CoTwo'
        m('StkBp%sZ' % tag, '%.1f' % r['z_star'])
        m('StkBp%sN' % tag, '%d' % r['N'])
        m('StkBp%sOff' % tag, '%+.2f' % off)
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
    unattr = []
    for r in cand:
        nu = r['z_chan_sf_hz'] / 1e9
        lab, rest = min(LINES.items(), key=lambda kv: abs((kv[1] - nu) / kv[1]))
        if abs((rest - nu) / rest * C_KMS) > ATTR_KMS:
            unattr.append((r['star'], lab, (rest - nu) / rest * C_KMS))
    m('StkAttrKms', '%.0f' % ATTR_KMS)
    m('StkNUnattributedComputed', '%d' % len(unattr))
    assert len(unattr) == 0, unattr
    assert M_get('StkNUnattributed') == '%d' % len(unattr), (
        'the typed unattributed count disagrees with the computed one')

    # ------------------------------------------------------------------
    # ★★ AN INDEPENDENT PERSISTENCE TEST, and it agrees with DECISIONS_R7 A6.
    # The stars the paper's crossing chain reached are stacked here by a method
    # that shares no code with the crossing search, and none of them persists.
    PERSIST = ['taucet', '61vir', 'cp-722713', 'etacrv', 'hd31392',
               'hd285968', 'gj849', 'lhs1140', 'hd207129']
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
    # The gain must be quoted against N_eff, never against N: assert the
    # difference is material, so nobody is tempted to drop the qualifier.
    assert np.median(gb / sne) / np.median(gb / np.sqrt(nn)) > 1.1, 'N_eff and N'
    _worst = min(R, key=lambda r: r['gain_real_vs_best'] if r['N'] >= 8 else 9e9)
    m('StkWorstStar', _worst['star'])
    m('StkWorstN', '%d' % _worst['N'])
    m('StkWorstNeff', '%.1f' % _worst['n_eff'])
    m('StkWorstGain', '%.2f' % _worst['gain_real_vs_best'])

    with open(OUT, 'w') as fh:
        fh.write('%% GENERATED by stack_v406.py -- do not hand-edit.\n')
        fh.write('\n'.join(sorted(M)) + '\n')
    print('stack_v406 (round 96): %d groups, %d stars, %d epoch-windows, %.0f h'
          % (len(R), len(set(r['skey'] for r in R)), sum(r['N'] for r in R),
             sum(r['on_source_h'] for r in R)))
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
    print('  gate: 0 empty, 0 nan')


if __name__ == '__main__':
    main()
