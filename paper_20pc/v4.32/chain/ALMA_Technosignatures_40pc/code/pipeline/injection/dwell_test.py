#!/usr/bin/env python3
"""Does the pipeline suppress a temporally persistent, frequency-stationary
carrier in a COARSE window?  The paper asserts it does, via 'per-channel
temporal-median subtraction'.  This tests it, using the pipeline's OWN baseline
function (extracted verbatim from the source) over the retained per-integration
spectra, with a controllable dwell fraction."""
import numpy as np, json, glob, os, ast

SRC = open('/data/SETI/bin/seti_drift_search_generic.py').read()
ns = {'np': np}
for node in ast.parse(SRC).body:
    if isinstance(node, ast.FunctionDef) and node.name == 'spectral_baseline':
        exec(compile(ast.Module([node], []), '<pipeline>', 'exec'), ns)
    elif isinstance(node, ast.Assign) and getattr(node.targets[0], 'id', '') == 'MEDWIN':
        exec(compile(ast.Module([node], []), '<pipeline>', 'exec'), ns)
spectral_baseline, MEDWIN = ns['spectral_baseline'], ns['MEDWIN']
print('pipeline spectral_baseline extracted; MEDWIN =', MEDWIN)

def run(I_star, I_ctrl, ch=None, amp=0.0, dwell=1.0, rng=None):
    I = I_star.astype(np.float64).copy()
    nint, nch = I.shape
    med = np.nanmedian(I_ctrl, axis=1)
    mad = np.nanmedian(np.abs(I_ctrl - med[:, None, :]), axis=1)
    sigma = 1.4826 * mad
    sig_ref = float(np.nanmedian(sigma))
    if ch is not None and amp > 0:
        non = max(1, int(round(dwell * nint)))
        idx = np.sort(rng.choice(nint, size=non, replace=False))
        I[idx, ch] += amp * sig_ref
    resid = I - spectral_baseline(np.nan_to_num(I)[None, :, :], MEDWIN)[0]
    w = 1.0 / np.nanmean(sigma, axis=1) ** 2
    stack = np.nansum(resid * w[:, None], axis=0) / np.nansum(w)
    nz = 1.4826 * np.nanmedian(np.abs(stack - np.nanmedian(stack)))
    return stack, nz, sig_ref

cands = []
for res in glob.glob('/data/SETI/targets/*/products/*_result.json'):
    try: r = json.load(open(res))
    except Exception: continue
    if r.get('chanwidth_Hz', 0) > 5e6 and os.path.exists(res.replace('_result.json', '_srcspec.npz')):
        cands.append((res, r))
print('coarse windows with retained spectra:', len(cands))
res, r = sorted(cands, key=lambda x: -(x[1].get('n_int') or 0))[0]
print('using', os.path.basename(res), '| n_int=%s nchan=%s chanw=%.2f MHz'
      % (r.get('n_int'), r.get('n_chan'), r['chanwidth_Hz']/1e6))
z = np.load(res.replace('_result.json', '_srcspec.npz'), allow_pickle=True)
I_star = np.asarray(z['I_star'], float); I_ctrl = np.asarray(z['I_control_sample'], float)
nint, nch = I_star.shape
rng = np.random.default_rng(7)
ch = nch // 2
_, nz, sig_ref = run(I_star, I_ctrl)
print('nint=%d nch=%d  per-int sigma=%.4g  stacked noise=%.4g  ideal gain sqrt(nint)=%.1f'
      % (nint, nch, sig_ref, nz, np.sqrt(nint)))
print('\nrecovered S/N of the injected channel (mean of 5 realisations)')
print(' dwell      A=5      A=10     A=20   (amplitude in per-integration sigma)')
for dwell in (1.0, 0.75, 0.5, 0.4, 0.25, 0.10):
    row = []
    for A in (5, 10, 20):
        v = [ (run(I_star, I_ctrl, ch, A, dwell, rng)[0][ch] - 0.0) for _ in range(5) ]
        s, n, _ = run(I_star, I_ctrl, ch, A, dwell, rng)
        vals = []
        for _ in range(5):
            st, nn, _ = run(I_star, I_ctrl, ch, A, dwell, rng)
            vals.append((st[ch] - np.nanmedian(st)) / nn)
        row.append(np.mean(vals))
    print('  %4.2f   %7.1f  %7.1f  %7.1f' % (dwell, *row))
