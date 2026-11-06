#!/usr/bin/env python3
"""Decide the drift reference epoch by experiment, not by reading code.

visfit_r6.py evaluates the drift track as nu(t) = nu0 + nudot (t - median(TIME)).
seti_drift_search_generic.py de-drifts with dt = times - times[0], so the
frequency it reports is the frequency at the FIRST retained integration. If
that is the mismatch, then fitting with t_ref = min(TIME) must recover the
injected flux independently of the drift rate, while fitting with
t_ref = median(TIME) must lose it in proportion to nudot x T_span.

The experiment injects tones of KNOWN drift into one real window and fits each
one both ways. It also compares a single-tone pass against a many-tone pass, to
size the only other suspect: the continuum reference channels of one tone
landing on its neighbours.

Nothing here is a free parameter. The prediction is quantitative and the
experiment either confirms it or does not.

Usage: tref_experiment.py <work dir>
"""
import json
import math
import os
import shutil
import subprocess
import sys

import numpy as np

W = sys.argv[1] if len(sys.argv) > 1 else '/data/SETI/p90_r7/tref'
MS = ('/data/SETI/targets/HD53143__Gaia_DR3_5479222240596469632__B6_EB_Xdc45'
      '/products/A002_X10a341d_Xdc45_target.ms')
SPW = 2
EB = 'A002_X10a341d_Xdc45'
BIN = '/data/SETI/bin'
ENV = dict(os.environ, CASASITECONFIG='/home/fetch-agi/.casa/config.py',
           OMP_NUM_THREADS='1')
ARCSEC = math.pi / 180.0 / 3600.0


def sh(cmd, env=None, log=None):
    with open(log or f'{W}/run.log', 'a') as fh:
        fh.write('\n=== %s\n' % ' '.join(cmd))
        fh.flush()
        return subprocess.call(cmd, env=env or ENV, stdout=fh,
                               stderr=subprocess.STDOUT)


def main():
    shutil.rmtree(W, ignore_errors=True)
    os.makedirs(f'{W}/products', exist_ok=True)
    os.makedirs(f'{W}/logs', exist_ok=True)
    env = dict(ENV, SETI_TARGET_DIR=W, SETI_STAR_NAME='HD53143',
               SETI_STAR_RA='104.99706286126714',
               SETI_STAR_DEC='-61.33500424765096',
               SETI_STAR_PMRA='-161.87264540008795',
               SETI_STAR_PMDEC='264.83561051555023',
               SETI_STAR_PARALLAX='54.52523915853711',
               SETI_STAR_PARALLAX_ERR='0.001', SETI_DRIFT_COEFF='12.0')

    assert sh(['python3', '-c',
               'import sys, os;'
               'os.environ.setdefault("CASASITECONFIG",'
               '"/home/fetch-agi/.casa/config.py");'
               'from casatasks import split;'
               'split(vis=sys.argv[1], outputvis=sys.argv[2], spw=sys.argv[3],'
               ' datacolumn="data", keepflags=False)',
               MS, f'{W}/clean.ms', str(SPW)], env) == 0, 'split failed'

    # baseline pass: threshold, drift bound, time span, stellar position
    assert sh(['python3', f'{BIN}/seti_extract_generic.py', EB, '16'],
              dict(env, SETI_MS=f'{W}/clean.ms', SETI_SFX='_tb')) == 0
    with np.load(f'{W}/products/{EB}_tb_waterfall.npz', allow_pickle=True) as z:
        l_star, m_star = float(z['l_star']), float(z['m_star'])
    assert sh(['python3', f'{BIN}/seti_drift_search_generic.py', EB, '16'],
              dict(env, SETI_MS=f'{W}/clean.ms', SETI_SFX='_tb')) == 0
    base = json.load(open(f'{W}/products/{EB}_tb_result.json'))
    s_trig = float(base['S_min_measured_Jy'])
    pb = float(base['primary_beam_fwhm_arcsec'])
    tspan = float(base['time_span_s'])
    dmax = float(base['drift_max_Hz_s'])
    chanw = float(base['chanwidth_Hz'])
    print('S_trig %.4g Jy  T_span %.0f s  drift_max %.0f Hz/s  chanw %.4g Hz'
          % (s_trig, tspan, dmax, chanw))
    print('a drift of drift_max would move the carrier %.2f channels in '
          'T_span/2' % (dmax * tspan / 2 / chanw))

    out = dict(base=dict(S_trig_Jy=s_trig, pb=pb, time_span_s=tspan,
                         drift_max_Hz_s=dmax, chanwidth_Hz=chanw),
               cases=[])
    amp = 20.0 * s_trig

    # Three passes: many tones with drift, many tones without, one tone with
    # drift. The third isolates neighbour contamination of the continuum
    # reference band from everything else.
    for case, ntone, dr in (('many_drift', 24, dmax), ('many_nodrift', 24, 0.0),
                            ('one_drift', 1, dmax)):
        pms = f'{W}/{case}.ms'
        shutil.rmtree(pms, ignore_errors=True)
        assert subprocess.call(['cp', '-a', f'{W}/clean.ms', pms]) == 0
        ij = f'{W}/{case}_inj.json'
        assert sh(['python3', f'{BIN}/inject_vis_v401.py', pms, '0', ij,
                   str(ntone), '910001'],
                  dict(env, INJ_L=repr(l_star), INJ_M=repr(m_star),
                       INJ_AMP_JY=repr(amp), INJ_DRIFT_MAX=repr(dr))) == 0
        inj = json.load(open(ij))
        sfx = '_' + case
        assert sh(['python3', f'{BIN}/seti_extract_generic.py', EB, '16'],
                  dict(env, SETI_MS=pms, SETI_SFX=sfx)) == 0
        assert sh(['python3', f'{BIN}/seti_drift_search_generic.py', EB, '16'],
                  dict(env, SETI_MS=pms, SETI_SFX=sfx)) == 0
        z = np.load(f'{W}/products/{EB}{sfx}_search.npz', allow_pickle=True)
        star = np.asarray(z['best_src'])[0]
        bdrift = np.asarray(z['best_drift'])[0]
        freqs = np.asarray(z['freqs'], float)
        df = abs(float(freqs[1] - freqs[0]))
        res = json.load(open(f'{W}/products/{EB}{sfx}_result.json'))

        ev, dr_map, meta = [], {}, {}
        avoid = [float(t['freq_GHz']) for t in inj['tones']]
        for j, t in enumerate(inj['tones']):
            f0 = float(t['freq_GHz']) * 1e9
            near = np.nonzero(np.abs(freqs - f0) <= 4 * df)[0]
            if near.size == 0:
                continue
            k = int(near[int(np.nanargmax(star[near]))])
            key = '%s_t%02d' % (case, j)
            ev.append(dict(tag='t%02d' % j, eb=key, ms=pms,
                           freq_GHz=float(freqs[k] / 1e9), theta_pb=pb,
                           l0_arcsec=l_star / ARCSEC, m0_arcsec=m_star / ARCSEC,
                           avoid_GHz=avoid, avoid_tol_GHz=8 * df / 1e9))
            dr_map[key] = float(bdrift[k])
            meta[key] = dict(snr=float(star[k]), drift_found=float(bdrift[k]),
                             drift_inj=float(t['drift_Hz_s']),
                             subchan=float(t['subchan']))
        json.dump(ev, open(f'{W}/{case}_ev.json', 'w'))
        json.dump(dr_map, open(f'{W}/{case}_dr.json', 'w'))

        fits = {}
        for mode in ('median', 'first'):
            o = f'{W}/{case}_fit_{mode}.json'
            assert sh(['python3', f'{BIN}/visfit_r7.py'],
                      dict(env, VF_EVENTS=f'{W}/{case}_ev.json',
                           VF_DRIFT=f'{W}/{case}_dr.json', VF_OUT=o,
                           VF_TREF=mode)) == 0, (case, mode)
            fits[mode] = json.load(open(o))

        rows = []
        for e in ev:
            k = '%s|%s' % (e['tag'], e['eb'])
            m = meta[e['eb']]
            row = dict(m, offset_chan=abs(m['drift_found']) * tspan / 2 / chanw)
            for mode in ('median', 'first'):
                f = fits[mode].get(k) or {}
                st = f.get('star') or {}
                row['re_over_amp_' + mode] = ((st.get('re') or 0.0) / amp)
                row['snr_re_' + mode] = st.get('snr_re')
                row['snr_im_' + mode] = st.get('snr_im')
                row['ctrl_pos_' + mode] = f.get('ctrl_pos_max')
                row['ctrl_freq_' + mode] = f.get('ctrl_freq_max')
                row['n_freq_ctrl_' + mode] = len(f.get('freq_controls') or [])
            rows.append(row)
        out['cases'].append(dict(case=case, ntone=ntone, drift_max=dr,
                                 amp_Jy=amp, n_int=res.get('n_int'),
                                 tones=rows))
        shutil.rmtree(pms, ignore_errors=True)

        print('\n--- %s (%d tones, drift up to %.0f Hz/s), injected %.4g Jy'
              % (case, ntone, dr, amp))
        print('  offset_ch  |drift|     Re/amp(median)  Re/amp(first)   '
              'ctrl_freq(med) ctrl_freq(first) nfc')
        for r in sorted(rows, key=lambda x: x['offset_chan']):
            print('  %8.2f %9.1f %15.3f %14.3f %14s %15s %4d'
                  % (r['offset_chan'], abs(r['drift_found']),
                     r['re_over_amp_median'], r['re_over_amp_first'],
                     '%.2f' % r['ctrl_freq_median']
                     if r['ctrl_freq_median'] is not None else '-',
                     '%.2f' % r['ctrl_freq_first']
                     if r['ctrl_freq_first'] is not None else '-',
                     r['n_freq_ctrl_first']))
        for mode in ('median', 'first'):
            v = [r['re_over_amp_' + mode] for r in rows]
            print('  median Re/amp (%s) = %.3f   min %.3f  max %.3f'
                  % (mode, float(np.median(v)), min(v), max(v)))
    json.dump(out, open(f'{W}/tref_experiment.json', 'w'), indent=1)
    print('\nwritten', f'{W}/tref_experiment.json')


if __name__ == '__main__':
    main()
