#!/usr/bin/env python3
r"""Inventory every retained per-channel profile, with the metadata it carries.

Five profile sets exist, written by four campaigns, and they disagree about the
capitalisation of the same star's directory name (`tau_Cet` in one set,
`Tau_Cet` in another).  So the inventory is keyed on what the data say -- the
block, the spectral-window number, the two window edges and the profile's own
maximum -- and the directory name is carried only as provenance.  Nothing
downstream joins on it.

Usage: cells_inventory.py <outfile> <dir> [<dir> ...]
"""
import glob
import json
import os
import re
import sys

import numpy as np

OUT = sys.argv[1]
rows = []
for d in sys.argv[2:]:
    for p in sorted(glob.glob(os.path.join(d, '*_r8prof.npz'))):
        b = os.path.basename(p)
        m = re.search(r'(A002_[0-9A-Za-z]+_[0-9A-Za-z]+)_spw(\d+)_r8prof\.npz$',
                      b)
        if m:
            eb, spw = m.group(1), int(m.group(2))
        else:
            m = re.search(r'(A002_[0-9A-Za-z]+_[0-9A-Za-z]+)_r8prof\.npz$', b)
            if not m:
                print('  SKIPPED, no block in the name: %s' % b)
                continue
            eb, spw = m.group(1), None
        z = np.load(p)
        f = np.asarray(z['freqs'], dtype=np.float64) / 1e9
        st = np.asarray(z['star'], dtype=np.float64)
        rows.append(dict(path=p, dir=os.path.basename(d), file=b,
                         eb=eb, spw=spw,
                         lo=float(f.min()), hi=float(f.max()),
                         nch=int(st.size), star_peak=float(st.max()),
                         chanw=float(z['chanw']), nint=int(z['nint']),
                         n_drift=int(z['n_drift']),
                         n_ctrl=int(np.asarray(z['ctrl']).shape[0]),
                         star_name=str(z['star_name']),
                         star_peak_pub=(float(z['star_peak_pub'])
                                        if 'star_peak_pub' in z.files
                                        else None)))
json.dump(rows, open(OUT, 'w'), indent=1)
print('%d profiles inventoried over %d directories'
      % (len(rows), len(sys.argv) - 2))
