#!/usr/bin/env python3
"""
Given the calibrated per-EB target MeasurementSets produced by
calibrate_generic.py, find EVERY distinct spectral window configured in
the correlator setup (for the narrowband SETI search) and split each out
into its own compact MS. Also records the full set of available continuum
spws (for the separate continuum-imaging step) without needing to re-open
the MSes later.

Updated 2026-08-30 per Glenn's instruction: previously this only kept the
SINGLE finest-channel spectral window and searched nothing else, silently
leaving the other spws configured alongside it (typically 3 more, up to
23 more for spectral-scan observations) completely unsearched. Now
selects every DISTINCT spw (deduplicated across repeated EBs of the same
setup, by spw_id), splits each into its own search MS, and writes a
prioritised (finest-first) list for process_one_target.sh to loop over.
Capped at MAX_SPW_SEARCHED to bound worst-case compute for rare,
extreme spectral-scan setups (observed: up to 24 spws for one target) --
the cap always keeps the finest-resolution (most narrowband-sensitive)
windows first, so nothing of particular value is dropped for the more
typical 4-spw case.

Fixed 2026-08-30 (post-deployment validation, live target LSR J1835+3259):
some ALMA spectral-scan setups list spws in SPECTRAL_WINDOW that carry
NO data rows for the target field in a given EB (e.g. bandpass/pointing-
only spws, or spws for which per-EB calibration failed and the applycal'd
column is entirely absent for that spw) -- attempting to split() such a
spw raises MSSelectionNullSelection and, unguarded, previously killed
spw-selection for the ENTIRE target. Each split() is now wrapped in
try/except so a single bad spw is skipped (logged) rather than fatal,
and the search continues down the finest-first candidate list (beyond
the nominal cap if needed) until MAX_SPW_SEARCHED spws are successfully
split or candidates are exhausted.

Usage: select_finest_spw.py <target_dir>
"""
import os, sys, json, glob, shutil, traceback
os.environ.setdefault('CASASITECONFIG', '/home/fetch-agi/.casa/config.py')
os.environ.setdefault('OMP_NUM_THREADS', '1')

TARGET_DIR = sys.argv[1]
PROD = f'{TARGET_DIR}/products'
LOGD = f'{TARGET_DIR}/logs'
MAX_SPW_SEARCHED = int(os.environ.get('SETI_MAX_SPW_SEARCHED', 8))

status = json.load(open(f'{LOGD}/calibrate_status.json'))
ebs = {k: v for k, v in status['ebs'].items() if v.get('ok')}
if not ebs:
    print('[select_finest_spw] no calibrated EBs available', flush=True)
    sys.exit(1)

from casatools import table
tb = table()

candidates = []   # (chanwidth_Hz, nchan, eb, spw_id, freq_lo, freq_hi, ms)
for eb, info in ebs.items():
    ms = info['ms']
    tb.open(ms + '/SPECTRAL_WINDOW')
    nspw = tb.nrows()
    for i in range(nspw):
        freqs = tb.getcol('CHAN_FREQ', startrow=i, nrow=1)[:, 0]
        cw = abs(float(tb.getcol('CHAN_WIDTH', startrow=i, nrow=1)[0, 0]))
        nch = len(freqs)
        if nch < 8:      # exclude pointing/WVR/CH_AVG-style single-channel spws
            continue
        candidates.append((cw, nch, eb, i, float(freqs.min()), float(freqs.max()), ms))
    tb.close()

if not candidates:
    print('[select_finest_spw] no usable (>=8 channel) spw found in any EB', flush=True)
    sys.exit(1)

# Deduplicate across EBs that share the same spw_id (repeated epochs of the
# same correlator setup) -- keep whichever EB has the finest chanwidth for
# that spw_id (should normally be identical across EBs of the same setup;
# this is just a defensive tiebreak).
by_spwid = {}
for c in candidates:
    cw, nch, eb, spw_i, flo, fhi, ms = c
    if spw_i not in by_spwid or cw < by_spwid[spw_i][0]:
        by_spwid[spw_i] = c

full_distinct = sorted(by_spwid.values(), key=lambda c: c[0])  # finest chanwidth first
n_total_distinct = len(full_distinct)
if n_total_distinct > MAX_SPW_SEARCHED:
    print(f'[select_finest_spw] {n_total_distinct} distinct spws configured -- '
          f'targeting the {MAX_SPW_SEARCHED} finest-resolution *usable* ones '
          f'(SETI_MAX_SPW_SEARCHED={MAX_SPW_SEARCHED})', flush=True)

from casatasks import split
spw_list = []
n_skipped_empty = 0
for cw, nch, eb, spw_i, flo, fhi, ms in full_distinct:
    if len(spw_list) >= MAX_SPW_SEARCHED:
        break
    out = f'{PROD}/{eb}_spw{spw_i}_search.ms'
    shutil.rmtree(out, ignore_errors=True)
    try:
        split(vis=ms, outputvis=out, spw=str(spw_i), datacolumn='data', keepflags=False)
    except Exception as e:
        n_skipped_empty += 1
        shutil.rmtree(out, ignore_errors=True)
        print(f'[select_finest_spw] spw {spw_i} (EB={eb}) has no usable data for '
              f'the target field -- skipping ({type(e).__name__}: {e})', flush=True)
        continue
    print(f'[select_finest_spw] spw {spw_i}: EB={eb} chanwidth={cw/1e3:.2f} kHz '
          f'nchan={nch} freq={flo/1e9:.3f}-{fhi/1e9:.3f} GHz -> {out}', flush=True)
    spw_list.append(dict(eb=eb, ms=out, spw=spw_i, chanwidth_Hz=cw, n_chan=nch,
                          freq_lo_GHz=flo/1e9, freq_hi_GHz=fhi/1e9))

if not spw_list:
    print(f'[select_finest_spw] all {n_total_distinct} distinct spw(s) were '
          f'unsplittable (no target-field data) -- nothing to search', flush=True)
    sys.exit(1)

if n_skipped_empty:
    print(f'[select_finest_spw] {n_skipped_empty} distinct spw(s) skipped '
          f'(no target-field data); {len(spw_list)} spw(s) successfully split', flush=True)

# Backward-compatible single-best record (some downstream tooling/analysis
# still reads this for the "primary" spw) plus the new full list and an
# honest record of how many distinct spws existed in total vs. were
# actually searched.
best = spw_list[0]
meta = dict(eb=best['eb'], ms=best['ms'], spw=best['spw'],
            chanwidth_Hz=best['chanwidth_Hz'], n_chan=best['n_chan'],
            freq_lo_GHz=best['freq_lo_GHz'], freq_hi_GHz=best['freq_hi_GHz'],
            all_spws=[dict(eb=e, ms=v['ms']) for e, v in ebs.items()],
            n_spw_configured=n_total_distinct, n_spw_searched=len(spw_list))
json.dump(meta, open(f'{LOGD}/finest_spw.json', 'w'), indent=1)
json.dump(dict(spw_list=spw_list, n_spw_configured=n_total_distinct),
          open(f'{LOGD}/spw_list.json', 'w'), indent=1)
print(f'[select_finest_spw] wrote {len(spw_list)} spw(s) to search '
      f'(of {n_total_distinct} distinct spws configured)', flush=True)
