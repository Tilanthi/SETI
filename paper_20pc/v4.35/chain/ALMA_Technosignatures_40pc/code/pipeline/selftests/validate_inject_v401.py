#!/usr/bin/env python3
"""Validate inject_vis_v401.py ON REAL CALIBRATED VISIBILITIES.

The deposited profile is isolated by differencing the measurement set against
an untouched copy of itself, so nothing about the sky or the noise enters:
whatever the injector wrote is exactly diff = V_after - V_before.  The test
then asks the one question the v3.99 kernel got wrong -- how much of the flux
the PEAK channel holds as a function of sub-channel phase.  v3.99 split the
tone linearly and delivered 0.500 at channel centre but only ~0.375-0.39 at a
channel boundary; the correlator's own Hann lag window delivers 0.4244 there.

The injection for this test is made at the phase centre (INJ_L=INJ_M=0), so
the geometric phase factor is unity and the deposited value is real: any
imaginary residual would mean the deposition is not doing what it claims.

Usage: validate_inject_v401.py <clean.ms> <injected.ms> <inj.json> <out.json>
"""
import importlib.util
import json
import sys

import numpy as np
from casatools import table

clean, inj_ms, injjson, outp = sys.argv[1:5]
inj = json.load(open(injjson))
spw = int(inj['spw'])


def read(ms):
    tb = table()
    tb.open(ms + '/DATA_DESCRIPTION')
    dd = np.array(tb.getcol('SPECTRAL_WINDOW_ID'), int)
    tb.close()
    ddids = [i for i, s in enumerate(dd) if s == spw]
    tb.open(ms)
    ddcol = np.array(tb.getcol('DATA_DESC_ID'), int)
    rows = np.nonzero(np.isin(ddcol, ddids))[0]
    first = np.array(tb.getcell('DATA', int(rows[0])))
    npol, nch = first.shape
    out = np.empty((npol, nch, rows.size), np.complex128)
    for j, r in enumerate(rows):
        out[:, :, j] = np.array(tb.getcell('DATA', int(r)))
    tb.close()
    return out


a = read(clean)
b = read(inj_ms)
diff = (b - a).mean(axis=(0, 2))        # per-channel deposited amplitude, Jy
amp = float(inj['amp_Jy'])

sp = importlib.util.spec_from_file_location(
    'inj401', '/data/SETI/bin/inject_vis_v401.py')
m = importlib.util.module_from_spec(sp)
sp.loader.exec_module(m)

rows = []
for t in inj['tones']:
    c0, sub = int(t['chan']), float(t['subchan'])
    lo, hi = max(0, c0 - 8), min(diff.size, c0 + 9)
    seg = diff[lo:hi]
    pk = int(np.argmax(np.abs(seg.real)))
    order = np.sort(np.argsort(-np.abs(seg.real))[:3])
    ks = np.arange(-6, 7)
    w = m.resp(ks - sub)
    rows.append(dict(
        chan=c0, subchan=sub,
        peak_frac=float(seg.real[pk] / amp),
        sum3_frac=float(seg.real[order].sum() / amp),
        sumall_frac=float(seg.real.sum() / amp),
        peak_Jy=float(seg.real[pk]), sum3_Jy=float(seg.real[order].sum()),
        max_abs_imag_frac=float(np.max(np.abs(seg.imag)) / amp),
        peak_frac_pred=float(np.max(np.abs(w))),
        sum3_frac_pred=float(np.sort(np.abs(w))[-3:].sum()),
        profile=[float(x / amp) for x in seg.real]))
    rows[-1]['peak_frac_resid'] = rows[-1]['peak_frac'] - rows[-1]['peak_frac_pred']

ctr = [r for r in rows if abs(r['subchan']) < 0.08]
edg = [r for r in rows if abs(r['subchan']) > 0.42]
res = dict(ms=inj_ms, spw=spw, amp_Jy=amp, n_tone=len(rows),
           n_chan=int(diff.size), response=inj.get('response'),
           peak_frac_at_centre=[r['peak_frac'] for r in ctr],
           peak_frac_at_edge=[r['peak_frac'] for r in edg],
           max_abs_resid_vs_model=float(max(abs(r['peak_frac_resid'])
                                            for r in rows)),
           max_abs_imag_frac=float(max(r['max_abs_imag_frac'] for r in rows)),
           median_sum3_frac=float(np.median([r['sum3_frac'] for r in rows])),
           median_sumall_frac=float(np.median([r['sumall_frac'] for r in rows])),
           tones=rows)
json.dump(res, open(outp, 'w'), indent=1)
print('n_tone %d  amp %.3f Jy  nchan %d' % (len(rows), amp, diff.size))
print('peak fraction, |subchan|<0.08 (channel centre): %s'
      % ', '.join('%.4f' % r['peak_frac'] for r in ctr))
print('peak fraction, |subchan|>0.42 (channel edge)  : %s'
      % ', '.join('%.4f' % r['peak_frac'] for r in edg))
print('max |measured - tabulated response| over all tones: %.3e'
      % res['max_abs_resid_vs_model'])
print('max |imaginary| / injected flux: %.3e' % res['max_abs_imag_frac'])
print('median 3-channel sum / injected flux: %.4f   (17-ch sum: %.4f)'
      % (res['median_sum3_frac'], res['median_sumall_frac']))
print('written', outp)
