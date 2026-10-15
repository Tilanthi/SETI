#!/usr/bin/env python3
r"""THE DECORRELATION TERM OF TABLE 3, MEASURED RATHER THAN DECLARED.

Imported by sens_r11.py, which owns Table 3 and the sensitivity section; run
directly it prints the measurement and nothing else, and writes no file, so
it claims no macro round and nothing in the build reads a path it writes.

WHAT THE TERM IS.  An artificial carrier is added to visibilities that the
pipeline has already phase- and amplitude-calibrated, so it carries no
atmospheric coherence loss at all.  A real carrier carries the loss of the
block that recorded it.  Every limit is therefore optimistic by that loss and
by nothing in the other direction, and the quantity at issue is precisely the
coherence of a point source at the phase centre.

WHY IT CAN BE MEASURED FROM OUR OWN DATA.  Every block observes a phase
calibrator, which IS a point source at the phase centre, and the observatory
records its residual path-length fluctuation after the water-vapour-radiometer
correction in that block's QA0 report.  Expressed as a path length the
quantity is frequency-independent, so each window's phase rms follows from
its own sky frequency:

    phi_rms[deg] = 360 * dL[micron] / lambda[micron],
    coherence    = exp(-phi_rms[rad]**2 / 2),

the second being the standard result for a Gaussian phase error over the
interval that is stacked (ALMA Memo 620, Richards et al. 2022, Eqs. 3 and 6;
Thompson, Moran & Swenson 2017, Ch. 7.2.8).  The band dependence is then a
consequence of the measurement and not a model: the same residual path costs
2.5 times more phase at 870 GHz than at 345 GHz.

WHAT REPLACED WHAT.  The published figure was "every limit is optimistic by
up to 20 per cent ... declared from the literature rather than measured
here", with no reference given, and before that a two-sided -12/+17 per cent
bracket taken from a superseded campaign record.  The measurement says the
flat bound was wrong in both directions at once: too pessimistic for the
median window, which is a compact-array Band 6 window and loses one per cent,
and far too optimistic for the long-baseline and high-frequency tail.

★ THREE THINGS THIS FILE REFUSES TO DO.
  1. It will not impute.  Blocks whose delivery does not expose a QA0 report
     individually have no value here and are counted as uncovered; the
     coverage is published.
  2. It will not fold the term into the two-sided calibration interval.  A
     one-sided bias and a symmetric error are different objects.
  3. It will not read the archive.  The per-block numbers are frozen in
     r13inputs/decor_r13.json, whose own provenance names the report each
     came from.

★ AND ONE THING IT CHECKS RATHER THAN ASSUMES.  Wherever the QA0 report also
printed the phase rms in degrees at the block's representative frequency, the
conversion above must reproduce it.  That is checked over every such block,
and it is the only evidence that the column being read means what the
docstring says it means.  Two further checks are physical: the residual path
must rise with the maximum baseline, as the tropospheric structure function
requires, and the compact array must sit below the twelve-metre array.
"""
import json
import math
import os
import statistics

HERE = os.path.dirname(os.path.abspath(__file__))
C_UM_GHZ = 299792.458          # micron * GHz
RECORD = os.path.join(HERE, 'r13inputs', 'decor_r13.json')
# The frequency above which the paper qualifies its limits.  It separates
# Bands 8, 9 and 10 -- the three the bound is least secure in, and the two the
# report singles out -- from Band 7 and below: Band 7 ends at 373 GHz and
# Band 8 begins at 385, so nothing in the survey lies within 15 GHz of it and
# no window can move across it.  A band edge, not a threshold chosen after
# seeing the answer.
HIBAND_GHZ = 400.0
# The tail the table reports: the share of windows whose limit is optimistic
# by more than this.  One fifth, i.e. the bound the paper used to declare.
TAIL = 0.20


def load(path=RECORD):
    return json.load(open(path))


def phase_deg(um, f_ghz):
    """Phase rms in degrees of a path rms of `um` micron at `f_ghz`."""
    return 360.0 * um / (C_UM_GHZ / f_ghz)


def optimism(um, f_ghz):
    """How much a limit must be RAISED, as a fraction, at this frequency."""
    phi = math.radians(phase_deg(um, f_ghz))
    return 1.0 / math.exp(-phi * phi / 2.0) - 1.0


def measure(cat, rec=None, perturb=None):
    """Per-window decorrelation over the released catalogue.

    `perturb` is the hook sens_r11.py's --drive uses; it names the one thing
    to break and nothing else.
    """
    rec = rec or load()
    blocks = dict(rec['blocks'])
    if perturb == 'impute':
        # the defect this file exists to refuse: give every uncovered block
        # the median of the covered ones, so the coverage disappears
        med_um = statistics.median(b['path_rms_um'] for b in blocks.values())
        for r in cat:
            blocks.setdefault(r['eb'], {'path_rms_um': med_um})
    if perturb == 'twosided':
        pass                                    # handled by the caller
    win = []
    for r in cat:
        b = blocks.get(r['eb'])
        if not b:
            continue
        f = 0.5 * (float(r['flo_GHz']) + float(r['fhi_GHz']))
        win.append({'eb': r['eb'], 'band': r['band'],
                    'cls': r['search_class'], 'f_ghz': f,
                    'deg': phase_deg(b['path_rms_um'], f),
                    'opt': optimism(b['path_rms_um'], f)})
    opts = sorted(w['opt'] for w in win)
    hi = sorted(w['opt'] for w in win if w['f_ghz'] > HIBAND_GHZ)
    if perturb == 'medianforhigh':
        hi = opts                               # quote the median as the bound
    bands = {}
    for b in sorted({w['band'] for w in win}, key=int):
        v = sorted(w['opt'] for w in win if w['band'] == b)
        d = sorted(w['deg'] for w in win if w['band'] == b)
        bands[b] = {'n_win': len(v), 'n_block':
                    len({w['eb'] for w in win if w['band'] == b}),
                    'opt_med': statistics.median(v), 'opt_max': v[-1],
                    'deg_med': statistics.median(d)}
    hiband = max(bands, key=int) if bands else None
    return {
        'n_win': len(win), 'n_win_cat': len(cat),
        'n_block': len({w['eb'] for w in win}),
        'n_block_cat': len({r['eb'] for r in cat}),
        'n_band': len(bands), 'n_band_cat': len({r['band'] for r in cat}),
        'opt_med': statistics.median(opts) if opts else 0.0,
        'opt_max': opts[-1] if opts else 0.0,
        'opt_hiband_med': statistics.median(hi) if hi else 0.0,
        'n_hiband_win': len(hi),
        'deg_med': statistics.median([w['deg'] for w in win]) if win else 0.0,
        'tail_frac': (sum(1 for o in opts if o > TAIL) / len(opts)
                      if opts else 0.0),
        'tail_level': TAIL,
        'hiband_ghz': HIBAND_GHZ,
        'top_band': hiband,
        'bands': bands,
        'windows': win,
        'measured_here': rec['measured_here'],
        'declared_superseded': rec['superseded_declaration'],
    }


def self_checks(rec=None):
    """Checks on the reading itself; returns a list of (label, ok, detail)."""
    rec = rec or load()
    B = rec['blocks']
    out = []
    # 1. the report's own degrees, where it printed them, must come back
    pairs = [(e, b) for e, b in B.items()
             if 'stated_phasecal_deg' in b and 'repr_freq_ghz' in b]
    worst, worst_eb = 0.0, None
    for e, b in pairs:
        p = phase_deg(b['path_rms_um'], b['repr_freq_ghz'])
        d = abs(p - b['stated_phasecal_deg']) / b['stated_phasecal_deg']
        if d > worst:
            worst, worst_eb = d, e
    out.append(('the path rms reproduces the phase rms the report states in '
                'degrees, over every block that printed both',
                bool(pairs) and worst < 0.05,
                '%d blocks, worst disagreement %.1f per cent (%s)'
                % (len(pairs), 100 * worst, worst_eb)))
    # 2. the residual path must grow with baseline length
    short = [b['path_rms_um'] for b in B.values()
             if b.get('bl_max_m', 0) < 100]
    longb = [b['path_rms_um'] for b in B.values()
             if b.get('bl_max_m', 0) >= 500]
    out.append(('the measured residual path rises with the maximum baseline, '
                'as a tropospheric origin requires',
                bool(short) and bool(longb)
                and statistics.median(longb) > statistics.median(short),
                '%.1f micron over %d blocks under 100 m against %.1f over '
                '%d blocks beyond 500 m'
                % (statistics.median(short), len(short),
                   statistics.median(longb), len(longb))))
    # 3. and the compact array must lie below the twelve-metre array
    aca = [b['path_rms_um'] for b in B.values() if b.get('array_m') == 7.0]
    tm = [b['path_rms_um'] for b in B.values() if b.get('array_m') == 12.0]
    out.append(('the compact array loses less coherence than the '
                'twelve-metre array',
                bool(aca) and bool(tm)
                and statistics.median(aca) < statistics.median(tm),
                '%.1f micron over %d compact blocks against %.1f over %d'
                % (statistics.median(aca), len(aca),
                   statistics.median(tm), len(tm))))
    return out


if __name__ == '__main__':
    import csv
    _cat = list(csv.DictReader(open(os.path.join(
        HERE, 'per_target_results_v3.99.csv'))))
    _r = load()
    _d = measure(_cat, _r)
    print('decor_r13: %d of %d execution blocks measured, %d of %d windows, '
          '%d of %d bands'
          % (_d['n_block'], _d['n_block_cat'], _d['n_win'], _d['n_win_cat'],
             _d['n_band'], _d['n_band_cat']))
    print('  median window: phase rms %.1f deg, limit optimistic by %.1f '
          'per cent' % (_d['deg_med'], 100 * _d['opt_med']))
    print('  above %.0f GHz (%d windows): %.1f per cent'
          % (_d['hiband_ghz'], _d['n_hiband_win'],
             100 * _d['opt_hiband_med']))
    print('  optimistic by more than %.0f per cent in %.1f per cent of '
          'windows; worst window %.0f per cent'
          % (100 * _d['tail_level'], 100 * _d['tail_frac'],
             100 * _d['opt_max']))
    for _b, _v in _d['bands'].items():
        print('  band %-2s %3d blocks %4d windows  phase rms %5.1f deg  '
              'optimism %5.1f per cent (worst %5.1f)'
              % (_b, _v['n_block'], _v['n_win'], _v['deg_med'],
                 100 * _v['opt_med'], 100 * _v['opt_max']))
    for _l, _ok, _det in self_checks(_r):
        print('  %-72s %s  %s' % (_l[:72], 'PASS' if _ok else 'FAIL', _det))
