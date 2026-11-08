#!/usr/bin/env python3
"""R2-M2 / R1-4: inject drifting carriers into CALIBRATED VISIBILITIES and
recover them through the unmodified pipeline.

Why this exists. The campaign that currently sets P90 injects into retained
per-integration spectra AFTER the baseline step, so it cannot see what the
baseline filter does to a signal, and it never passes through the control
ranking. This injects into the visibilities themselves and then runs the
ordinary extraction, baseline removal, de-drift stack, trigger and
512-control rank, scoring recovery with a single criterion.

Design note. Each pass injects SEVERAL tones into one measurement set at
well-separated frequencies, so a single extraction yields many independent
trials. The tones cannot interact through the median baseline filter at that
spacing, and each carries its own random sub-channel phase and drift rate.
Without this a campaign of the required size would need one copy of a
multi-gigabyte measurement set per trial.

A source of flux S at direction (l0, m0) contributes

    V += S * exp(-2i pi nu (u l0 + v m0) / c)

which is the conjugate of the phase factor the extractor applies, so that
real(V * exp(+2i pi ...)) returns S at that position. The sign convention is
taken from seti_extract_generic.py and must not be changed independently.

Usage:  inject_vis_v399.py <ms> <spw> <out.json> [ntone] [seed]

`<spw>` is the spectral-window id. A calibrated target measurement set holds
several windows of different channel counts, so the visibilities must be
selected per window: a bare getcol over the whole table fails with a shape
error, and getcol('CHAN_FREQ') likewise.
Environment: INJ_L, INJ_M (direction cosines, radians), INJ_AMP_JY,
             INJ_DRIFT_MAX (Hz/s).
"""
import json
import math
import os
import sys

import numpy as np

C = 299792458.0
SEP_CHAN = 64          # minimum channel separation between injected tones
EDGE_CHAN = 96         # keep tones clear of the band edges
HANN = (0.25, 0.5, 0.25)


def main():
    ms, spw, out_path = sys.argv[1], int(sys.argv[2]), sys.argv[3]
    ntone = int(sys.argv[4]) if len(sys.argv) > 4 else 16
    seed = int(sys.argv[5]) if len(sys.argv) > 5 else 20260924
    rng = np.random.default_rng(seed)

    from casatools import table
    tb = table()
    # per-window frequency axis; getcell, not getcol, because the windows
    # have different channel counts
    tb.open(ms + '/SPECTRAL_WINDOW')
    freqs = np.array(tb.getcell('CHAN_FREQ', spw), dtype=float)
    chanw = float(abs(np.array(tb.getcell('CHAN_WIDTH', spw), dtype=float)[0]))
    tb.close()
    nch = int(freqs.size)
    df = float(freqs[1] - freqs[0])

    # rows belonging to this window, via the data-description table
    tb.open(ms + '/DATA_DESCRIPTION')
    dd_spw = np.array(tb.getcol('SPECTRAL_WINDOW_ID'), dtype=int)
    tb.close()
    ddids = [i for i, s_ in enumerate(dd_spw) if s_ == spw]
    if not ddids:
        raise SystemExit('no data description maps to spw %d' % spw)
    tb.open(ms, nomodify=False)
    ddcol = np.array(tb.getcol('DATA_DESC_ID'), dtype=int)
    rows = np.nonzero(np.isin(ddcol, ddids))[0]
    if rows.size == 0:
        raise SystemExit('no rows for spw %d' % spw)
    # selectrows gives a view whose row order matches `rows`; query() does
    # not return a table object in this casatools build
    # Per-row cell access. Neither query() nor selectrows() returns a table
    # object in this casatools build, and a bare getcol('DATA') fails across
    # windows of different channel counts, so the rows of this window are
    # read and written one at a time. At ~10^3 rows per window this is fast
    # enough and cannot be tripped up by API differences.
    uvw_all = np.array(tb.getcol('UVW'), dtype=float)
    time_all = np.array(tb.getcol('TIME'), dtype=float)
    uvw = uvw_all[:, rows]
    times = time_all[rows]
    first = np.array(tb.getcell('DATA', int(rows[0])))
    npol = first.shape[0] if first.ndim == 2 else 1
    assert first.shape[-1] == nch or first.shape[0] == nch, (
        'DATA cell shape %s does not match the %d channels spw %d declares'
        % (first.shape, nch, spw))
    data = np.empty((npol, nch, rows.size), dtype=first.dtype)
    for j, r in enumerate(rows):
        c = np.array(tb.getcell('DATA', int(r)))
        data[:, :, j] = c if c.ndim == 2 else c[None, :]

    l0 = float(os.environ.get('INJ_L', '0'))
    m0 = float(os.environ.get('INJ_M', '0'))
    amp = float(os.environ.get('INJ_AMP_JY', '0.01'))
    drift_max = float(os.environ.get('INJ_DRIFT_MAX', '0'))

    dt = times - times.min()

    # scale the guard band and tone spacing to the window: a 128-channel
    # coarse window cannot host the same layout as a 4096-channel fine one
    edge = max(4, min(EDGE_CHAN, nch // 8))
    sep = max(4, min(SEP_CHAN, nch // 16))
    lo, hi = edge, nch - edge
    if hi - lo < sep * 2:
        raise SystemExit('window of %d channels is too narrow to host '
                         'separated tones' % nch)
    slots = list(range(lo, hi, sep))
    rng.shuffle(slots)
    slots = sorted(slots[:ntone])

    tones = []
    for c0 in slots:
        sub = float(rng.uniform(-0.5, 0.5))
        drift = float(rng.uniform(-drift_max, drift_max)) if drift_max else 0.0
        nu0 = float(freqs[c0]) + sub * df
        tones.append(dict(chan=int(c0), subchan=sub, drift_Hz_s=drift,
                          amp_Jy=amp, freq_GHz=nu0 / 1e9))

        nu_row = nu0 + drift * dt                       # per-row frequency
        fidx = (nu_row - freqs[0]) / df
        base = np.floor(fidx).astype(int)
        frac = fidx - base
        # geometric phase of a source at (l0, m0), per row, at its own tone
        # frequency
        ph = np.exp(-2j * math.pi * (nu_row / C)
                    * (uvw[0] * l0 + uvw[1] * m0)).astype(np.complex64)

        # linear split between the two straddled channels, then the
        # three-point Hanning kernel, so the deposited profile is what the
        # correlator would deliver rather than a delta in one channel
        for k in (-1, 0, 1, 2):
            w = np.zeros_like(frac)
            for j, hk in zip((-1, 0, 1), HANN):
                if k - j == 0:
                    w += hk * (1.0 - frac)
                elif k - j == 1:
                    w += hk * frac
            if not np.any(w):
                continue
            ci = base + k
            ok = (ci >= 0) & (ci < nch) & (w > 0)
            if not ok.any():
                continue
            # NB: a distinct name. `rows` holds the measurement-set row
            # numbers of this window; these are indices WITHIN that
            # selection. Reusing the name silently redirected the write-back
            # to rows 0..N and would have corrupted another window had the
            # channel counts happened to agree.
            sel = np.nonzero(ok)[0]
            val = (amp * w[ok] * ph[ok]).astype(data.dtype)
            for p in range(npol):
                np.add.at(data[p], (ci[ok], sel), val)

    for j, r in enumerate(rows):
        tb.putcell('DATA', int(r), data[:, :, j])
    tb.flush()
    tb.close()
    # Every tone's drift is referenced to the EARLIEST time in this window.
    # The search de-drifts to the first integration it RETAINS, which can
    # differ if it drops leading integrations; the resulting frequency
    # offset is drift x (that time difference). Record the time base so the
    # scorer can BOUND that offset rather than guess a channel tolerance.
    utimes = np.unique(times)
    json.dump(dict(ms=ms, spw=spw, n_tone=len(tones), seed=seed, amp_Jy=amp,
                   l0=l0, m0=m0, chanw_Hz=chanw, df_Hz=df, n_chan=nch,
                   n_times=int(utimes.size), t_min=float(times.min()),
                   median_dt_s=(float(np.median(np.diff(utimes)))
                                if utimes.size > 1 else 0.0),
                   tones=tones),
              open(out_path, 'w'), indent=1)
    print('injected %d tones at %.4g Jy into %s spw %d (%d chan, %.1f kHz)'
          % (len(tones), amp, ms, spw, nch, chanw / 1e3))


if __name__ == '__main__':
    main()
