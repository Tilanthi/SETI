#!/usr/bin/env python3
"""Re-search every window whose maximum is a line coincidence, with the
masked channels removed.

A crossing is the maximum of the window's per-channel, drift-maximised
statistic at the stellar position: the search records one number per window.
So in a window whose maximum sits on a catalogued transition, a weaker
carrier elsewhere in the same window was never recordable.  This re-reads the
retained per-channel profile of each such window, removes every channel
within +-50 km/s (stellar frame) of any transition of the mask, and takes the
maximum of what is left.

THE PROFILE IS RESOLVED ON THE STATISTIC, NOT ON A NAME.  Four of these
windows were re-extracted, two exist under two target directories for the
same block, and the directory names differ between profile sets.  A candidate
profile is accepted only if it holds the crossing frequency and its own
published peak reproduces the statistic the paper adopts for that crossing to
1e-4 relative.  Where no profile reproduces the published statistic the
nearest candidate is used and the row is marked `gate=false` with both
numbers printed: a window re-searched on a product that does not reproduce
the catalogue is reported as such, not quietly folded in.

Inputs:  research_jobs.json, the profile sets under /data/SETI/r8 and
         /data/SETI/r14mask.
Output:  mask_research_result.json
"""
import glob
import json
import os
import sys

import numpy as np

R8 = '/data/SETI/r8'
PROF = [os.path.join(R8, d) for d in
        ('prof_v409r', 'profall_v409', 'prof_v409', 'profall', 'prof')]
PROF.append('/data/SETI/r14mask')
JOBS = json.load(open(sys.argv[1]))
OUT = sys.argv[2]
HALF = JOBS['half']
C = JOBS['c']
TRANS = JOBS['trans']
TOL = 1e-4
TRIG = 5.0


def candidates(eb, freq, tstar):
    out = []
    for d in PROF:
        for p in sorted(glob.glob(os.path.join(d, '*%s_spw*_r8prof.npz' % eb))):
            try:
                z = np.load(p)
            except Exception:
                continue
            f = np.asarray(z['freqs'], dtype=np.float64) / 1e9
            if not (f.min() <= freq <= f.max()):
                continue
            pub = float(z['star_peak_pub'])
            out.append((abs(pub - tstar) / max(abs(tstar), 1e-12),
                        os.path.basename(d), p, pub))
    out.sort()
    return out


res = []
for j in JOBS['jobs']:
    rec = dict(j)
    cands = candidates(j['eb'], j['freq'], j['tstar'])
    rec['n_candidate_profiles'] = len(cands)
    rec['candidates'] = [dict(rel=c[0], dir=c[1], file=os.path.basename(c[2]),
                              pub=c[3]) for c in cands[:6]]
    if not cands:
        rec['status'] = 'no_profile'
        res.append(rec)
        continue
    good = [c for c in cands if c[0] < TOL]
    if good and len({round(c[3], 6) for c in good}) != 1:
        rec['status'] = 'candidate_profiles_disagree'
        res.append(rec)
        continue
    rel, d, p, pub = (good or cands)[0]
    z = np.load(p)
    star = np.asarray(z['star'], dtype=np.float64)
    ctrl = np.asarray(z['ctrl'], dtype=np.float64)
    freqs = np.asarray(z['freqs'], dtype=np.float64) / 1e9
    rec.update(profile=os.path.basename(p), profile_dir=d,
               n_profile_sets=len(good),
               nchan=int(star.size), nctrl=int(ctrl.shape[0]),
               chanw_Hz=float(z['chanw']), nint=int(z['nint']),
               n_drift=int(z['n_drift']),
               win_lo=float(freqs.min()), win_hi=float(freqs.max()),
               win_bw_GHz=float(freqs.max() - freqs.min()),
               star_peak_pub=pub, star_peak_prof=float(star.max()),
               gate_rel=rel, gate=bool(rel < TOL))

    fb = freqs * (1.0 - j['v_bary'] / C)
    fs = fb * (1.0 + j['v_sys'] / C)
    ipk = int(np.argmax(star))

    masked = np.zeros(star.size, dtype=bool)
    hits = []
    for name, frest in TRANS.items():
        dv = C * (fs - frest) / frest
        sel = np.abs(dv) <= HALF
        if sel.any():
            masked |= sel
            hits.append(dict(line=name, nchan=int(sel.sum()),
                             dv_at_peak=float(dv[ipk])))
    rec['lines_in_window'] = sorted(hits, key=lambda h: -h['nchan'])
    rec['n_masked_chan'] = int(masked.sum())
    rec['masked_frac'] = float(masked.sum()) / star.size
    rec['peak_is_masked'] = bool(masked[ipk])
    rec['dv_at_peak'] = float(min((C * (fs[ipk] - f) / f
                                   for f in TRANS.values()), key=abs))
    rec['peak_chan'] = ipk
    rec['f_peak_topo'] = float(freqs[ipk])
    rec['f_peak_stellar'] = float(fs[ipk])
    rec['peak_offset_chan'] = float(
        (freqs[ipk] - j['freq']) * 1e9 / float(z['chanw']))
    rec['bw_masked_GHz'] = float(masked.sum()) * float(z['chanw']) / 1e9

    keep = ~masked
    rec['n_keep_chan'] = int(keep.sum())
    rec['bw_keep_GHz'] = float(keep.sum()) * float(z['chanw']) / 1e9
    if keep.any():
        idx = int(np.flatnonzero(keep)[int(np.argmax(star[keep]))])
        rec.update(T_resid=float(star[idx]), resid_chan=idx,
                   f_resid_topo=float(freqs[idx]),
                   f_resid_stellar=float(fs[idx]),
                   resid_drift=float(np.asarray(z['star_drift'])[idx]))
        best = min(((n, C * (fs[idx] - f) / f) for n, f in TRANS.items()),
                   key=lambda t: abs(t[1]))
        rec['resid_nearest'], rec['resid_dv'] = best[0], best[1]
        cm = ctrl[:, keep].max(axis=1) if ctrl.size else np.array([])
        rec['T_resid_ctrl_max'] = float(cm.max()) if cm.size else None
        rec['n_ctrl_above_resid'] = int((cm >= rec['T_resid']).sum()) \
            if cm.size else None
        rec['second_crossing'] = bool(rec['T_resid'] >= TRIG)
        rec['status'] = 'ok'
    else:
        # every channel of the window lies inside the mask: the window is
        # wholly unsearchable for a carrier, and its bandwidth is lost
        rec['T_resid'] = None
        rec['second_crossing'] = False
        rec['status'] = 'wholly_masked'
    res.append(rec)

json.dump(res, open(OUT, 'w'), indent=1)
ok = [r for r in res if r['status'] in ('ok', 'wholly_masked')]
print('%d windows; %d reproduce the published statistic; %d wholly masked; '
      '%d hold a surviving cell at T>=%g'
      % (len(res), sum(1 for r in ok if r['gate']),
         sum(1 for r in res if r['status'] == 'wholly_masked'),
         sum(1 for r in res if r.get('second_crossing')), TRIG))
for r in res:
    if r['status'] == 'no_profile':
        print('  %-18s %-22s NO PROFILE' % (r['display'][:18], r['eb'][5:]))
        continue
    if r['status'] == 'wholly_masked':
        print('  %-18s %-22s T=%8.3f -> WHOLLY MASKED %d/%d chan, %.4f GHz'
              % (r['display'][:18], r['eb'][5:], r['star_peak_prof'],
                 r['n_masked_chan'], r['nchan'], r['bw_masked_GHz']))
        continue
    print('  %-18s %-22s T=%8.3f -> resid %6.3f at %+9.1f km/s (ctrl %5s, '
          '%s above)  masked %4d/%-5d gate=%d %s'
          % (r['display'][:18], r['eb'][5:], r['star_peak_prof'],
             r['T_resid'], r['resid_dv'], ('%.2f' % r['T_resid_ctrl_max'])
             if r['T_resid_ctrl_max'] is not None else 'n/a',
             r['n_ctrl_above_resid'], r['n_masked_chan'], r['nchan'],
             r['gate'], 'SECOND CROSSING' if r.get('second_crossing') else ''))
