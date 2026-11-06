#!/usr/bin/env python3
"""Coarse- and fine-channel injection campaign: recovery C(A, f_dwell).

Injects a narrowband carrier into the retained per-integration spectra of real
windows, with a controllable dwell fraction, and pushes it through the
pipeline's own spectral-baseline removal and inverse-variance de-drift stack.
Writes TRIAL-LEVEL records (one row per injection), as requested by referees.

Scope, stated honestly: injection is at the extracted-spectrum level, which is
where the baseline removal and the stack act.  It does not exercise calibration
or the visibility-to-spectrum extraction.
"""
import numpy as np, json, glob, os, ast, csv, sys, random

SRC = open('/data/SETI/bin/seti_drift_search_generic.py').read()
ns = {'np': np}
for node in ast.parse(SRC).body:
    if isinstance(node, ast.FunctionDef) and node.name == 'spectral_baseline':
        exec(compile(ast.Module([node], []), '<p>', 'exec'), ns)
    elif isinstance(node, ast.Assign) and getattr(node.targets[0], 'id', '') == 'MEDWIN':
        exec(compile(ast.Module([node], []), '<p>', 'exec'), ns)
spectral_baseline, MEDWIN = ns['spectral_baseline'], ns['MEDWIN']

AMPS   = [2, 3, 4, 5, 6, 8, 10, 15, 20]
DWELLS = [1.0, 0.75, 0.50, 0.40, 0.25, 0.10]
NREAL  = 6
THRESH = 5.0

def prep(I_ctrl):
    med = np.nanmedian(I_ctrl, axis=1)
    mad = np.nanmedian(np.abs(I_ctrl - med[:, None, :]), axis=1)
    sigma = 1.4826 * mad
    return sigma, float(np.nanmedian(sigma))

def statistic(I, sigma):
    resid = I - spectral_baseline(np.nan_to_num(I)[None, :, :], MEDWIN)[0]
    w = 1.0 / np.nanmean(sigma, axis=1) ** 2
    stack = np.nansum(resid * w[:, None], axis=0) / np.nansum(w)
    nz = 1.4826 * np.nanmedian(np.abs(stack - np.nanmedian(stack)))
    return stack, nz

def windows(res_glob, coarse, n):
    out = []
    for res in glob.glob(res_glob):
        try: r = json.load(open(res))
        except Exception: continue
        sp = res.replace('_result.json', '_srcspec.npz')
        if not os.path.exists(sp): continue
        cw = r.get('chanwidth_Hz', 0)
        if (cw > 5e6) != coarse: continue
        out.append((res, r, sp))
    random.Random(11).shuffle(out)
    return out[:n]

rows = []
for coarse in (True, False):
    sel = windows('/data/SETI/targets/*/products/*_result.json', coarse, 6)
    print('%s windows selected: %d' % ('coarse' if coarse else 'fine', len(sel)), flush=True)
    for res, r, sp in sel:
        try:
            z = np.load(sp, allow_pickle=True)
            I0 = np.asarray(z['I_star'], float); C = np.asarray(z['I_control_sample'], float)
        except Exception as e:
            print('  skip', os.path.basename(res), e); continue
        nint, nch = I0.shape
        if nint < 20 or nch < 40: continue
        sigma, sref = prep(C)
        if not np.isfinite(sref) or sref <= 0: continue
        rng = np.random.default_rng(abs(hash(res)) % 2**31)
        tgt = res.split('/targets/')[1].split('/')[0]
        for A in AMPS:
            for dw in DWELLS:
                for k in range(NREAL):
                    ch = int(rng.integers(MEDWIN, nch - MEDWIN)) if nch > 3*MEDWIN else nch//2
                    I = I0.copy()
                    non = max(1, int(round(dw*nint)))
                    idx = np.sort(rng.choice(nint, size=non, replace=False))
                    I[idx, ch] += A * sref
                    st, nz = statistic(I, sigma)
                    snr = float((st[ch] - np.nanmedian(st)) / nz) if nz > 0 else float('nan')
                    pk = int(np.nanargmax(st - np.nanmedian(st)))
                    rows.append(dict(trial=len(rows), target=tgt,
                        window=os.path.basename(res).replace('_result.json',''),
                        band=r.get('alma_band_inferred'), chanw_Hz=r.get('chanwidth_Hz'),
                        klass='coarse' if coarse else 'fine', n_int=nint, n_chan=nch,
                        inj_chan=ch, amp_sigma=A, dwell=dw, realisation=k,
                        sigma_per_int=sref, recovered_snr=snr, peak_chan=pk,
                        detected=bool(snr >= THRESH and abs(pk-ch) <= 1)))
        print('  done', tgt, os.path.basename(res)[:30], flush=True)

with open('/data/SETI/logs/dwell_campaign_trials.csv','w',newline='') as f:
    w = csv.DictWriter(f, fieldnames=list(rows[0].keys())); w.writeheader(); w.writerows(rows)
print('\ntrial-level records written: %d -> /data/SETI/logs/dwell_campaign_trials.csv' % len(rows))
print('\nRECOVERY FRACTION  C(A, dwell)   [detected = S/N>=5 and peak in the injected channel]')
for klass in ('coarse','fine'):
    sub=[x for x in rows if x['klass']==klass]
    if not sub: continue
    print('\n--- %s windows (%d trials) ---' % (klass, len(sub)))
    print('dwell  ' + ''.join('%7s'%('A=%d'%a) for a in AMPS))
    for dw in DWELLS:
        line='%5.2f  '%dw
        for A in AMPS:
            t=[x for x in sub if x['amp_sigma']==A and x['dwell']==dw]
            line += '%7s' % ('%.2f'%(sum(x['detected'] for x in t)/len(t)) if t else '-')
        print(line)
