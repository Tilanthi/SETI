#!/usr/bin/env python3
r"""reduce_r21.py -- cut the two cluster read-outs down to the records the
generator needs, so what is deposited in the paper tree is the evidence and
not the scratch file.

The read-out `tol_r21.py` records the de-drifted stack at every channel within
+-1.5 km/s (exclusions) or +-3 km/s (positive controls) of the predicted cell.
The generator needs, per block reading: the channel width, the registered
frequency, the frozen single-cell statistic, and the amplitude and its error
at each offset inside the retained range.  Everything else -- the control-ring
maxima far from the cell, the integration counts, the stems -- is dropped, and
the arrays are written to 6 significant figures.

Usage: reduce_r21.py <in.json.gz> <out.json.gz> <half-range km/s>
"""
import gzip
import json
import sys

SRC, DST, RANGE = sys.argv[1], sys.argv[2], float(sys.argv[3])
C = 299792.458

d = json.load(gzip.open(SRC, 'rt'))
out = []
for r in d['rows']:
    K = r['K']
    dvch = C * r['chanw_Hz'] / (r['f_here_GHz'] * 1e9)      # km/s per channel
    kk = min(K, int(RANGE / dvch))
    sl = slice(K - kk, K + kk + 1)

    def cut(v):
        return [None if x is None else float('%.6g' % x) for x in v[sl]]
    out.append(dict(cid=r['cid'], star=r['star'], eb=r['eb'], stem=r['stem'],
                    chanw_Hz=r['chanw_Hz'], f_here_GHz=r['f_here_GHz'],
                    chan=r['chan'], drift_Hz_s=r['drift_Hz_s'],
                    sep_from_discovery_h=r['sep_from_discovery_h'],
                    t_start_mjdsec=r['t_start_mjdsec'],
                    t_end_mjdsec=r['t_end_mjdsec'],
                    n_int=r['n_int'],
                    star_peak_freq_GHz=r['star_peak_freq_GHz'],
                    star_peak_snr=r['star_peak_snr'],
                    T_frozen_single=r['T_frozen_single'],
                    k=kk, amp_mJy=cut(r['amp_mJy']), sig_mJy=cut(r['sig_mJy']),
                    T_ctrl_max=cut(r['T_ctrl_max'])))
with gzip.open(DST, 'wt') as fh:
    json.dump(dict(source=d['generator'], kms_recorded=d['kms'],
                   kms_kept=RANGE, gate_worst=d['gate_worst'],
                   n_rows=len(out), rows=out), fh)
print('%d rows -> %s' % (len(out), DST))
