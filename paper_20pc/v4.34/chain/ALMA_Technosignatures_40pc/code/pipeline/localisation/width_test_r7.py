#!/usr/bin/env python3
"""Width test of possibility 3 of EPOCH_TENSION.md.

For every round-6 visibility fit, measure the contiguous emission width W in
channels around its crossing channel, from the retained per-integration
on-source spectrum the pipeline itself wrote, and compare it with that
crossing's own epoch displacement

    D = |nudot| x (median(times) - min(times)) / chanw.

The prediction was written to referee_r7/WIDTH_TEST.md before this was run.
Definitions are fixed there and are not adjustable here.

Usage: width_test_r7.py [out.json]
"""
import glob
import json
import os
import sys

import numpy as np

R6 = '/data/SETI/visfit_r6/visfit_r6_result.json'
R5 = '/data/SETI/visfit_r7/visfit_all_v385.json'   # the 13 already-fitted
OUT = sys.argv[1] if len(sys.argv) > 1 else '/data/SETI/p90_r7/width_test_r7.json'

LOC_RE_MIN, LOC_IM_MAX = 4.0, 3.0


def localised(f):
    if f.get('status') != 'ok':
        return None
    st = f.get('star') or {}
    a, b = st.get('snr_re'), st.get('snr_im')
    if a is None or b is None:
        return None
    cs = [c for c in (f.get('ctrl_pos_max'), f.get('ctrl_freq_max'))
          if c is not None]
    return bool(a >= LOC_RE_MIN and abs(b) < LOC_IM_MAX
                and (not cs or a > max(cs)))


# index every surviving source spectrum by execution block
index = {}
for p in glob.glob('/data/SETI/targets/*/products/*_srcspec.npz'):
    base = os.path.basename(p)
    if '_spw' not in base:
        continue
    eb = base.split('_spw')[0]
    index.setdefault(eb, []).append(p)


def spectrum_for(eb, nu_hz):
    """The retained spectrum of the window holding nu, with its own axes."""
    best = None
    for p in index.get(eb, []):
        try:
            z = np.load(p, allow_pickle=True)
            fr = np.asarray(z['freqs'], float)
            if fr.size < 8 or not (fr.min() <= nu_hz <= fr.max()):
                continue
            if best is None or fr.size > best[1].size:
                best = (p, fr, z)
        except Exception:
            continue
    return best


def width_of(spec, c0):
    """Contiguous run of channels through c0 above continuum + 3 sigma."""
    finite = spec[np.isfinite(spec)]
    if finite.size < 16:
        return None, None, None
    cont = float(np.median(finite))
    sig = 1.4826 * float(np.median(np.abs(finite - cont)))
    if sig <= 0:
        return None, cont, 0.0
    lim = cont + 3.0 * sig
    if not np.isfinite(spec[c0]) or spec[c0] <= lim:
        return 0, cont, sig
    lo = c0
    while lo - 1 >= 0 and np.isfinite(spec[lo - 1]) and spec[lo - 1] > lim:
        lo -= 1
    hi = c0
    while hi + 1 < spec.size and np.isfinite(spec[hi + 1]) and spec[hi + 1] > lim:
        hi += 1
    return int(hi - lo + 1), cont, sig


def main():
    # all 44: the 13 fitted before round 6 and the 31 round 6 added. The two
    # β Pic 15.3 kHz blocks that carry the largest displacement of the whole
    # set are in the FIRST file, so reading only the round-6 result misses
    # exactly the crossings the test exists to examine.
    fits = {}
    fits.update(json.load(open(R5)))
    fits.update(json.load(open(R6))['fits'])
    rows, missing = [], []
    for key, f in sorted(fits.items()):
        ev = f.get('event') or {}
        eb = ev.get('eb') or (key.split('|')[-1] if '|' in key else None)
        loc = localised(f)
        st = f.get('star') or {}
        row = dict(key=key, eb=eb, star=ev.get('tag'), band=ev.get('band'),
                   freq_GHz=ev.get('freq_GHz'),
                   drift_Hz_s=f.get('drift_Hz_s', ev.get('drift_Hz_s')),
                   status=f.get('status'), localised=loc,
                   snr_re=st.get('snr_re'), snr_im=st.get('snr_im'),
                   ctrl_pos_max=f.get('ctrl_pos_max'),
                   ctrl_freq_max=f.get('ctrl_freq_max'))
        got = (spectrum_for(eb, float(ev['freq_GHz']) * 1e9)
               if (eb and ev.get('freq_GHz')) else None)
        if got is None:
            row['srcspec'] = None
            missing.append(key)
            rows.append(row)
            continue
        path, fr, z = got
        I = np.asarray(z['I_star'], float)
        Wt = np.asarray(z['W'], float)
        times = np.asarray(z['times'], float)
        chanw = float(np.asarray(z['chanw'], float))
        num = np.nansum(np.where(np.isfinite(I), I * Wt, 0.0), axis=0)
        den = np.nansum(np.where(np.isfinite(I), Wt, 0.0), axis=0)
        spec = np.where(den > 0, num / np.maximum(den, 1e-30), np.nan)
        nu0 = float(ev['freq_GHz']) * 1e9
        c0 = int(np.argmin(np.abs(fr - nu0)))
        w, cont, sig = width_of(spec, c0)
        dt_half = float(np.median(times) - np.min(times))
        nudot = abs(float(row['drift_Hz_s'] or 0.0))
        D = nudot * dt_half / abs(chanw)
        sweep = nudot * float(np.max(times) - np.min(times)) / abs(chanw)
        row.update(srcspec=os.path.basename(path), n_chan=int(fr.size),
                   chanwidth_Hz=abs(chanw), n_int=int(times.size),
                   t_elapsed_s=float(np.max(times) - np.min(times)),
                   t_half_s=dt_half,
                   displacement_chan=D, sweep_chan=sweep,
                   width_chan=w, continuum=cont, noise=sig,
                   peak_over_noise=(float((spec[c0] - cont) / sig)
                                    if sig and np.isfinite(spec[c0]) else None),
                   width_over_displacement=(w / D) if (w and D > 0) else None,
                   width_over_sweep=(w / sweep) if (w and sweep > 0) else None)
        rows.append(row)

    have = [r for r in rows if r.get('width_chan') is not None]
    loc = [r for r in have if r['localised']]
    nloc = [r for r in have if r['localised'] is False]
    out = dict(n_fits=len(rows), n_with_spectrum=len(have),
               n_localised_with_spectrum=len(loc),
               n_missing_spectrum=len(missing), missing=missing, rows=rows)

    def fmt(r):
        return ('%-34s %-14s %-3s %8.1f kHz %6.2f GHz %9.1f Hz/s %7.0f s '
                '%9.2f %9.2f %7s %8s  Re/s %7.2f Im/s %6.2f'
                % (r['eb'], (r['star'] or '')[:14], r['band'] or '?',
                   r['chanwidth_Hz'] / 1e3, r['freq_GHz'],
                   r['drift_Hz_s'] or 0, r['t_elapsed_s'],
                   r['displacement_chan'], r['sweep_chan'],
                   r['width_chan'],
                   ('%.1f' % r['width_over_displacement'])
                   if r['width_over_displacement'] else '-',
                   r['snr_re'] or 0, r['snr_im'] or 0))

    print('%d fits, %d with a surviving source spectrum, %d of those localised'
          % (len(rows), len(have), len(loc)))
    print('\n=== LOCALISED (the twelve the round-6 run recorded) ===')
    print('%-34s %-14s %-3s %12s %10s %14s %8s %9s %9s %7s %8s'
          % ('block', 'star', 'bnd', 'chanw', 'freq', 'drift', 'elapsed',
             'D(chan)', 'sweep', 'W(chan)', 'W/D'))
    for r in sorted(loc, key=lambda x: -(x['displacement_chan'] or 0)):
        print(fmt(r))
    print('\n=== NOT LOCALISED ===')
    for r in sorted(nloc, key=lambda x: -(x['displacement_chan'] or 0)):
        print(fmt(r))

    if loc:
        wd = [r['width_over_displacement'] for r in loc
              if r['width_over_displacement'] is not None]
        ws = [r['width_over_sweep'] for r in loc
              if r['width_over_sweep'] is not None]
        bad = [r['key'] for r in loc
               if r['width_chan'] is not None
               and r['displacement_chan'] is not None
               and r['width_chan'] <= 2.0 * r['displacement_chan']]
        out.update(localised_W_over_D_min=min(wd) if wd else None,
                   localised_W_over_D_median=(float(np.median(wd)) if wd
                                              else None),
                   localised_W_over_sweep_min=min(ws) if ws else None,
                   localised_failing_W_gt_2D=bad,
                   prediction_holds=bool(not bad))
        print('\nlocalised: min W/D = %s, median W/D = %s, min W/sweep = %s'
              % (('%.1f' % min(wd)) if wd else '-',
                 ('%.1f' % float(np.median(wd))) if wd else '-',
                 ('%.2f' % min(ws)) if ws else '-'))
        print('localised crossings with W <= 2D (would REFUTE possibility 3): '
              '%d %s' % (len(bad), bad))
    json.dump(out, open(OUT, 'w'), indent=1)
    print('\nwritten', OUT)


if __name__ == '__main__':
    main()
