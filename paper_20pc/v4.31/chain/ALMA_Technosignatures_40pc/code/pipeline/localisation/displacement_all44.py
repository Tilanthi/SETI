#!/usr/bin/env python3
"""The epoch displacement D of all 44 round-6 visibility fits, computed from
MEASURED elapsed spans wherever a measured span exists.

    D = |nudot| x (median(TIME) - min(TIME)) / chanw     [channels]

is the constant channel offset between the track visfit_r6.py follows and the
track the search's reported frequency defines. EPOCH_TENSION.md computed it
with `on_source_s` as a span proxy and found 35 of 44 above one channel and 26
above 2.8, which sits badly with 12 fits having localised. This recomputes it
with, in order of preference:

  1. the retained `*_srcspec.npz` of that very window -- `times` and `chanw` as
     the extraction wrote them, so the span is measured, not proxied;
  2. the retained calibrated measurement set, TIME of the rows the fit loads;
  3. `on_source_s` from the export, scaled by the measured ratio
     elapsed/on_source = 1.17 (median 0.815 the other way, over 23 units),
     and flagged as a proxy.

Channel width comes from the fit's own event where it carries `chanw_Hz`, else
from the srcspec, else from the export matched on block and window edges
(keyed on min/max of the edges: a descending window is exported with its
edges the other way round).

Usage: displacement_all44.py [out.json]
"""
import glob
import json
import os
import sys

import numpy as np

OUT = (sys.argv[1] if len(sys.argv) > 1
       else '/data/SETI/p90_r7/displacement_all44.json')
ELAPSED_OVER_ONSRC = 1.17          # measured, 23 units, see EPOCH_TENSION reply
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


srcspec = {}
for p in glob.glob('/data/SETI/targets/*/products/*_srcspec.npz'):
    b = os.path.basename(p)
    if '_spw' in b:
        srcspec.setdefault(b.split('_spw')[0], []).append(p)

exp = {}
for r in json.load(open('/data/SETI/mine2026/export_extension.json'))['rows']:
    lo, hi = sorted((float(r['flo']), float(r['fhi'])))
    exp[(r['eb'], round(lo, 4), round(hi, 4))] = r


def from_srcspec(eb, nu_hz):
    best = None
    for p in srcspec.get(eb, []):
        try:
            z = np.load(p, allow_pickle=True)
            fr = np.asarray(z['freqs'], float)
            if fr.size < 8 or not (fr.min() <= nu_hz <= fr.max()):
                continue
            if best is None or fr.size > best[0].size:
                best = (fr, z, p)
        except Exception:
            continue
    if best is None:
        return None
    fr, z, p = best
    t = np.asarray(z['times'], float)
    return dict(chanw=abs(float(np.asarray(z['chanw'], float))),
                t_half=float(np.median(t) - t.min()),
                t_elapsed=float(t.max() - t.min()), n_chan=int(fr.size),
                source='srcspec:' + os.path.basename(p), exact=True)


def from_ms(ms, nu_hz):
    if not ms or not os.path.isdir(ms):
        return None
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
        if pick is None:
            return None
        spw, cf = pick
        ddid = int(np.where(dd2 == spw)[0][0])
        tb.open(ms)
        sub = tb.query('DATA_DESC_ID==%d' % ddid)
        t = np.asarray(sub.getcol('TIME'), float)
        sub.close()
        tb.close()
        return dict(chanw=abs(float(np.median(np.diff(cf)))),
                    t_half=float(np.median(t) - t.min()),
                    t_elapsed=float(t.max() - t.min()), n_chan=int(cf.size),
                    source='measurement set TIME', exact=True)
    except Exception as e:
        return dict(error=repr(e))


def main():
    fits = {}
    fits.update(json.load(open('/data/SETI/visfit_r7/visfit_all_v385.json')))
    fits.update(json.load(open(
        '/data/SETI/visfit_r6/visfit_r6_result.json'))['fits'])
    final = {d['key']: d for d in
             json.load(open('/data/SETI/visfit_r7/final44.json'))}
    rows = []
    for key, f in fits.items():
        ev = f.get('event') or {}
        eb = ev.get('eb')
        nu = ev.get('freq_GHz')
        if nu is None:
            continue
        nu_hz = float(nu) * 1e9
        st = f.get('star') or {}
        g = from_srcspec(eb, nu_hz) or from_ms(ev.get('ms'), nu_hz)
        chanw = ev.get('chanw_Hz')
        if g and not g.get('error'):
            chanw = chanw or g['chanw']
            t_half, elapsed, exact = g['t_half'], g['t_elapsed'], True
            src = g['source']
        else:
            e = exp.get((eb, round(float(ev.get('flo_GHz') or 0), 4),
                         round(float(ev.get('fhi_GHz') or 0), 4)))
            if e is None:
                e = next((v for k, v in exp.items()
                          if k[0] == eb and k[1] <= nu <= k[2]), None)
            if e is None:
                rows.append(dict(key=key, eb=eb, freq_GHz=nu,
                                 localised=localised(f), chanw_Hz=chanw,
                                 displacement_chan=None,
                                 span_source='NO SPAN AVAILABLE'))
                continue
            chanw = chanw or float(e['chanw'])
            elapsed = float(e['onsrc']) * ELAPSED_OVER_ONSRC
            t_half, exact = elapsed / 2.0, False
            src = 'on_source_s x %.2f (PROXY)' % ELAPSED_OVER_ONSRC
        nudot = abs(float(f.get('drift_Hz_s') or ev.get('drift_Hz_s') or 0.0))
        D = nudot * t_half / chanw if chanw else None
        rows.append(dict(
            key=key, eb=eb, star=ev.get('tag'), band=ev.get('band'),
            freq_GHz=nu, chanw_Hz=chanw, drift_Hz_s=nudot,
            t_half_s=t_half, t_elapsed_s=elapsed, span_exact=exact,
            span_source=src, displacement_chan=D,
            sweep_chan=(nudot * elapsed / chanw) if chanw else None,
            snr_re=st.get('snr_re'), snr_im=st.get('snr_im'),
            localised=localised(f),
            line=(final.get(key) or {}).get('line'),
            dispo=(final.get(key) or {}).get('dispo')))

    have = [r for r in rows if r.get('displacement_chan') is not None]
    loc = [r for r in have if r['localised']]
    nloc = [r for r in have if r['localised'] is False]
    print('%d fits merged, %d with a displacement, %d localised'
          % (len(rows), len(have), len(loc)))
    hdr = ('%-34s %-16s %-3s %10s %9s %8s %7s %8s %8s %7s %7s %-28s'
           % ('block', 'star', 'bnd', 'chanw kHz', 'drift', 'elapsed', 'exact',
              'D chan', 'sweep', 'Re/s', 'Im/s', 'line'))

    def fmt(r):
        return ('%-34s %-16s %-3s %10.1f %9.1f %8.0f %7s %8.2f %8.2f %7.2f '
                '%7.2f %-28s'
                % (r['eb'], (r['star'] or '')[:16], r['band'] or '?',
                   (r['chanw_Hz'] or 0) / 1e3, r['drift_Hz_s'],
                   r['t_elapsed_s'], 'yes' if r['span_exact'] else 'PROXY',
                   r['displacement_chan'], r['sweep_chan'] or 0,
                   r['snr_re'] or 0, r['snr_im'] or 0, (r['line'] or '')[:28]))

    for label, group in (('LOCALISED', loc), ('NOT LOCALISED', nloc)):
        print('\n=== %s (%d) ===' % (label, len(group)))
        print(hdr)
        for r in sorted(group, key=lambda x: -x['displacement_chan']):
            print(fmt(r))
    if loc:
        d = [r['displacement_chan'] for r in loc]
        dn = [r['displacement_chan'] for r in nloc]
        print('\nlocalised   D: median %.2f  min %.2f  max %.2f  '
              '(%d of %d above 2.8 channels)'
              % (np.median(d), min(d), max(d), sum(1 for x in d if x > 2.8),
                 len(d)))
        print('not localised D: median %.2f  min %.2f  max %.2f  '
              '(%d of %d above 2.8 channels)'
              % (np.median(dn), min(dn), max(dn),
                 sum(1 for x in dn if x > 2.8), len(dn)))
    json.dump(dict(rows=rows, n_fits=len(rows), n_with_D=len(have),
                   elapsed_over_onsrc=ELAPSED_OVER_ONSRC), open(OUT, 'w'),
              indent=1)
    print('\nwritten', OUT)


if __name__ == '__main__':
    main()
