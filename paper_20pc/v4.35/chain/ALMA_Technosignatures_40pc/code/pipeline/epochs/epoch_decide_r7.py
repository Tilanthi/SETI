#!/usr/bin/env python3
"""Three measurements that settle the reference-epoch question.

A. IS THE MEASURED WIDTH THE LINE, OR THE DRIFT SMEAR?  The width test found
   W ~ D for five localised crossings, which could mean either "the line
   happens to be that wide" or "what I measured is the feature smeared across
   the swept channels".  A static line occupies the same channels in the first
   third of the integrations as in the last third; a drifting feature does not.
   Measured on the retained `*_srcspec.npz` of each localised crossing.

B. WHICH EPOCH RECOVERS AN INJECTED UNRESOLVED CARRIER.  A broad CO line
   cannot decide this, because a scan across it peaks near its centroid either
   way.  An injected tone of known frequency, drift and epoch decides it
   outright.  Every completed campaign unit already carries, for every
   triggered tone, the fit under BOTH conventions, so this is a read of data
   already taken: recovered flux as a fraction of the injected flux, binned by
   that tone's own displacement D.

C. DOES THE FIT'S times[0] EQUAL THE SEARCH'S?  The fit loads the measurement
   set's rows; the search de-drifts to the first integration it RETAINS after
   flagging.  If those differ, a residual offset remains even with the epoch
   convention corrected.  Measured by comparing the retained spectrum's own
   `times` with the TIME column of the same window.

Writes three small tables. Nothing is printed that has to be read in bulk.

Usage: epoch_decide_r7.py <outdir>
"""
import glob
import json
import os
import sys

import numpy as np

OUTD = sys.argv[1] if len(sys.argv) > 1 else '/data/SETI/p90_r7/epoch'
os.makedirs(OUTD, exist_ok=True)
LOC_RE_MIN, LOC_IM_MAX = 4.0, 3.0


def spec_of(I, W, rows=None):
    if rows is not None:
        I, W = I[rows], W[rows]
    num = np.nansum(np.where(np.isfinite(I), I * W, 0.0), axis=0)
    den = np.nansum(np.where(np.isfinite(I), W, 0.0), axis=0)
    return np.where(den > 0, num / np.maximum(den, 1e-30), np.nan)


def run(spec, c0):
    """Contiguous channels through c0 above continuum + 3 sigma, and the whole
    above-threshold extent of the window."""
    fin = spec[np.isfinite(spec)]
    if fin.size < 16:
        return None
    cont = float(np.median(fin))
    sig = 1.4826 * float(np.median(np.abs(fin - cont)))
    if sig <= 0:
        return None
    lim = cont + 3 * sig
    hot = np.isfinite(spec) & (spec > lim)
    if not hot[c0]:
        lo = hi = None
    else:
        lo = c0
        while lo - 1 >= 0 and hot[lo - 1]:
            lo -= 1
        hi = c0
        while hi + 1 < spec.size and hot[hi + 1]:
            hi += 1
    idx = np.nonzero(hot)[0]
    return dict(cont=cont, sig=sig, lo=lo, hi=hi,
                w=(hi - lo + 1) if lo is not None else 0,
                hot_lo=int(idx.min()) if idx.size else None,
                hot_hi=int(idx.max()) if idx.size else None,
                n_hot=int(idx.size),
                peak_chan=int(np.nanargmax(np.where(hot, spec, -np.inf)))
                if idx.size else None)


# ------------------------------------------------------------------ A and C
def part_a_c():
    disp = {r['key']: r for r in
            json.load(open('/data/SETI/p90_r7/displacement_all44.json'))['rows']}
    fits = {}
    fits.update(json.load(open('/data/SETI/visfit_r7/visfit_all_v385.json')))
    fits.update(json.load(open(
        '/data/SETI/visfit_r6/visfit_r6_result.json'))['fits'])
    index = {}
    for p in glob.glob('/data/SETI/targets/*/products/*_srcspec.npz'):
        b = os.path.basename(p)
        if '_spw' in b:
            index.setdefault(b.split('_spw')[0], []).append(p)

    rows_a, rows_c = [], []
    for key, f in sorted(fits.items()):
        ev = f.get('event') or {}
        eb, nu = ev.get('eb'), ev.get('freq_GHz')
        if not eb or nu is None:
            continue
        nu_hz = float(nu) * 1e9
        best = None
        for p in index.get(eb, []):
            try:
                z = np.load(p, allow_pickle=True)
                fr = np.asarray(z['freqs'], float)
                if fr.size >= 8 and fr.min() <= nu_hz <= fr.max():
                    if best is None or fr.size > best[1].size:
                        best = (p, fr, z)
            except Exception:
                continue
        if best is None:
            continue
        p, fr, z = best
        I = np.asarray(z['I_star'], float)
        Wt = np.asarray(z['W'], float)
        tt = np.asarray(z['times'], float)
        chanw = abs(float(np.asarray(z['chanw'], float)))
        c0 = int(np.argmin(np.abs(fr - nu_hz)))
        n = tt.size
        k = max(1, n // 3)
        order = np.argsort(tt)
        r_all = run(spec_of(I, Wt), c0)
        r_1 = run(spec_of(I, Wt, order[:k]), c0)
        r_3 = run(spec_of(I, Wt, order[-k:]), c0)
        d = disp.get(key, {})
        st = f.get('star') or {}
        cs = [c for c in (f.get('ctrl_pos_max'), f.get('ctrl_freq_max'))
              if c is not None]
        loc = (f.get('status') == 'ok' and st.get('snr_re') is not None
               and st['snr_re'] >= LOC_RE_MIN
               and abs(st.get('snr_im') or 9) < LOC_IM_MAX
               and (not cs or st['snr_re'] > max(cs)))
        shift = None
        if r_1 and r_3 and r_1.get('peak_chan') is not None \
                and r_3.get('peak_chan') is not None:
            shift = r_3['peak_chan'] - r_1['peak_chan']
        rows_a.append(dict(
            key=key, eb=eb, star=ev.get('tag'), band=ev.get('band'),
            chanw_Hz=chanw, localised=bool(loc),
            D=d.get('displacement_chan'), sweep=d.get('sweep_chan'),
            W_all=(r_all or {}).get('w'), W_first3=(r_1 or {}).get('w'),
            W_last3=(r_3 or {}).get('w'),
            peak_first3=(r_1 or {}).get('peak_chan'),
            peak_last3=(r_3 or {}).get('peak_chan'),
            peak_shift_chan=shift,
            expected_shift_if_drifting=((d.get('sweep_chan') or 0) * 2.0 / 3.0),
            snr_re=st.get('snr_re'),
            width_kHz=((r_all or {}).get('w') or 0) * chanw / 1e3))
        # C: the extraction's first retained integration vs the MS's first row
        ms = ev.get('ms')
        if ms and os.path.isdir(ms):
            try:
                from casatools import table
                tb = table()
                tb.open(ms + '/DATA_DESCRIPTION')
                dd2 = np.asarray(tb.getcol('SPECTRAL_WINDOW_ID'), int)
                tb.close()
                tb.open(ms + '/SPECTRAL_WINDOW')
                pick = None
                for i in range(tb.nrows()):
                    cf = np.asarray(tb.getcell('CHAN_FREQ', i), float)
                    if cf.size >= 8 and cf.min() <= nu_hz <= cf.max():
                        if pick is None or cf.size > pick[1].size:
                            pick = (i, cf)
                tb.close()
                if pick is not None:
                    ddid = int(np.where(dd2 == pick[0])[0][0])
                    tb.open(ms)
                    sub = tb.query('DATA_DESC_ID==%d' % ddid)
                    mt = np.asarray(sub.getcol('TIME'), float)
                    sub.close()
                    tb.close()
                    dn = abs(float(f.get('drift_Hz_s') or 0.0))
                    rows_c.append(dict(
                        key=key, eb=eb, chanw_Hz=chanw,
                        srcspec_t0=float(tt.min()), ms_t0=float(mt.min()),
                        dt0_s=float(tt.min() - mt.min()),
                        srcspec_n=int(tt.size),
                        ms_n_unique=int(np.unique(mt).size),
                        residual_chan=dn * abs(float(tt.min() - mt.min()))
                        / chanw))
            except Exception as e:
                rows_c.append(dict(key=key, eb=eb, error=repr(e)))
    json.dump(rows_a, open(OUTD + '/part_a_width_static.json', 'w'), indent=1)
    json.dump(rows_c, open(OUTD + '/part_c_t0_residual.json', 'w'), indent=1)

    print('=== A. static or smeared: peak channel in the first vs last third')
    print('%-34s %-12s %4s %8s %8s %7s %7s %8s %9s %6s'
          % ('block', 'star', 'loc', 'D', 'sweep', 'W_all', 'W_1/3',
             'shift', 'if_drift', 'width_kHz'))
    for r in sorted(rows_a, key=lambda x: -(x['D'] or 0)):
        print('%-34s %-12s %4s %8.2f %8.2f %7s %7s %8s %9.1f %6.0f'
              % (r['eb'], (r['star'] or '')[:12], 'YES' if r['localised'] else '-',
                 r['D'] or 0, r['sweep'] or 0, r['W_all'], r['W_first3'],
                 r['peak_shift_chan'], r['expected_shift_if_drifting'],
                 r['width_kHz']))
    print('\n=== C. the extraction first retained integration minus the MS first row')
    for r in sorted(rows_c, key=lambda x: -(x.get('residual_chan') or 0))[:12]:
        if 'error' in r:
            print('%-34s ERROR %s' % (r['eb'], r['error'][:60]))
        else:
            print('%-34s dt0 = %8.1f s  -> residual %7.2f channels  '
                  '(n_int src %d, ms %d)'
                  % (r['eb'], r['dt0_s'], r['residual_chan'],
                     r['srcspec_n'], r['ms_n_unique']))
    if rows_c:
        v = [abs(r['residual_chan']) for r in rows_c if 'residual_chan' in r]
        d = [abs(r['dt0_s']) for r in rows_c if 'dt0_s' in r]
        print('residual: median %.3f channels, max %.3f; |dt0| median %.1f s, '
              'max %.1f s (n=%d)'
              % (np.median(v), max(v), np.median(d), max(d), len(v)))


# ---------------------------------------------------------------------- B
def part_b():
    rows = []
    for fp in sorted(glob.glob('/data/SETI/p90_r7/out/*.json')):
        r = json.load(open(fp))
        if r.get('status') not in ('ok', 'partial') or not r.get('rungs'):
            continue
        b = r['baseline']
        chanw = float(b['chanwidth_Hz'])
        t_half = 0.5 * float(b.get('time_span_s') or 0.0)
        for g in r['rungs']:
            for t in g['tones']:
                if not t.get('trig') or t.get('re_over_amp') is None:
                    continue
                if t.get('re_over_amp_r6') is None:
                    continue
                rows.append(dict(
                    unit=r['unit']['tag'], cls=r['unit']['res_class'],
                    amp_over_trig=g['amp_over_trig'],
                    D=abs(float(t['drift_found'])) * t_half / chanw,
                    first=float(t['re_over_amp']),
                    median=float(t['re_over_amp_r6']),
                    snr_re=t.get('snr_re'), snr_re_r6=t.get('snr_re_r6'),
                    loc=bool(t.get('localised')),
                    loc_r6=bool(t.get('localised_r6committed'))))
    json.dump(rows, open(OUTD + '/part_b_epoch_vs_D.json', 'w'), indent=1)
    if not rows:
        print('\n=== B. no scored tones yet')
        return
    D = np.array([r['D'] for r in rows])
    fi = np.array([r['first'] for r in rows])
    me = np.array([r['median'] for r in rows])
    lf = np.array([r['loc'] for r in rows])
    lm = np.array([r['loc_r6'] for r in rows])
    edges = [0, 0.25, 0.5, 1, 2, 2.8, 4, 6, 10, 20, 1e9]
    print('\n=== B. injected unresolved carriers: recovered flux / injected, '
          'by displacement (%d tones, %d units)'
          % (len(rows), len({r['unit'] for r in rows})))
    print('%12s %6s %14s %14s %12s %12s'
          % ('D (chan)', 'n', 'median t0=first', 'median t0=med',
             'localised f', 'localised m'))
    for a, b_ in zip(edges[:-1], edges[1:]):
        m = (D >= a) & (D < b_)
        if not m.any():
            continue
        print('%5.2f-%-6.2f %6d %14.3f %14.3f %11.3f %12.3f'
              % (a, min(b_, 999), m.sum(), np.median(fi[m]), np.median(me[m]),
                 lf[m].mean(), lm[m].mean()))
    hi = D > 2.8
    if hi.any():
        print('D > 2.8 channels: n=%d, median recovered fraction %.3f with '
              't0=first vs %.3f with t0=median; localised %.3f vs %.3f'
              % (hi.sum(), np.median(fi[hi]), np.median(me[hi]),
                 lf[hi].mean(), lm[hi].mean()))


if __name__ == '__main__':
    part_a_c()
    part_b()
