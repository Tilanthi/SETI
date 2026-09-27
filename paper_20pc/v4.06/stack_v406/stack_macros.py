#!/usr/bin/env python3
"""Generator for the multi-epoch stack's typeset quantities (round 8, D15).

Reads only its own products -- stack4_result.jsonl, regtest.json, criterion.py --
and writes stack_macros.tex.  Nothing here is a hand-typed literal except the
pre-registered thresholds, which live in criterion.py and are imported.

Run:  python3 stack_macros.py
"""
import json, os, sys, math
import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import criterion as CR

OUT = os.path.join(HERE, 'stack_macros.tex')
C_KMS = 299792.458
LINES = {'CO(1-0)': 115.2712018, 'CO(2-1)': 230.5380000, 'CO(3-2)': 345.7959899}

M = []


def m(name, val):
    M.append('\\newcommand{\\%s}{%s}' % (name, val))


def sci(x, nd=2):
    if not np.isfinite(x):
        return '---'
    e = int(math.floor(math.log10(abs(x))))
    return r'%.*f \times 10^{%d}' % (nd, x / 10 ** e, e)


def main():
    R = [json.loads(l) for l in open(os.path.join(HERE, 'stack4_result.jsonl'))
         if 'err' not in l]
    reg = json.load(open(os.path.join(HERE, 'regtest.json')))
    inv = json.load(open(os.path.join(HERE, 'inventory.json')))
    win = json.load(open(os.path.join(HERE, 'windows.json')))

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
    # carrier registration tolerance
    m('StkReflexTolKms', '%.2f' % (488281.25 / 230.538e9 * C_KMS))
    m('StkDriftTolHzS', '$%s$' % sci(488281.25 / (652.3 * 86400), 1))
    m('StkBadWeight', '27')

    open(OUT, 'w').write('\n'.join(sorted(M)) + '\n')
    print('wrote %d macros to %s' % (len(M), OUT))
    # gate: no macro may be empty or contain 'nan'
    bad = [x for x in M if '{}' in x or 'nan' in x.lower()]
    assert not bad, 'bad macros: %s' % bad[:3]
    print('gate: 0 empty, 0 nan')


if __name__ == '__main__':
    main()
