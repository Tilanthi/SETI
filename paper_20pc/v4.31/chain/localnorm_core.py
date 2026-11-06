#!/usr/bin/env python3
"""The radius-corrected (locally normalised) rank statistic, in one place.

Two generators need it: the catalogue writer, which must put it in a column
so that a reader can reproduce the candidate list from the released file
alone (referee 1, point 16), and the analysis generator, which reports how
the candidate list changes under it (referee 2, point 1).  The catalogue
writer runs first, so the arithmetic lives here and both import it.

The control probes are drawn once from a fixed seed, identically in every
window, so each stored control value can be paired with the fractional
radius it was drawn at.  Standardising each probe within its own radius bin
removes the radial gradient in the control level by construction, with no
free parameter.  The star is standardised on the innermost bin, which is
the bin closest to its own position at the phase centre.
"""
import numpy as np

R_IN, R_OUT, NPROBE, SEED, NBIN = 0.14, 0.78, 512, 20260825, 8

_rng = np.random.default_rng(SEED)
#: fractional radii of the 512 control probes, identical in every window
RADII = np.sqrt(_rng.uniform(R_IN ** 2, R_OUT ** 2, NPROBE))
_edges = np.quantile(RADII, np.linspace(0, 1, NBIN + 1))
BINID = np.clip(np.digitize(RADII, _edges[1:-1]), 0, NBIN - 1)
SEL = [BINID == b for b in range(NBIN)]

#: the smallest add-one rank a window can attain: rank-first among 512+1
FLOOR = 1.0 / (NPROBE + 1)


def _mad(x):
    md = np.median(x)
    return md, (1.4826 * np.median(np.abs(x - md)) or 1.0)


def local_rank(star_snr, ctrl):
    """Add-one rank of the star against radius-standardised control probes.

    Returns None when the window does not carry the full control vector.
    """
    c = np.asarray([] if ctrl is None else ctrl, float)
    if c.size != NPROBE or star_snr is None:
        return None
    z = np.empty_like(c)
    for b in range(NBIN):
        s = SEL[b]
        md, sd = _mad(c[s])
        z[s] = (c[s] - md) / sd
    md0, sd0 = _mad(c[SEL[0]])
    zs = (float(star_snr) - md0) / sd0
    return (1 + int((z >= zs).sum())) / (z.size + 1.0)


def global_rank(star_snr, ctrl):
    """The released statistic: add-one rank against unstandardised probes."""
    c = np.asarray([] if ctrl is None else ctrl, float)
    if c.size == 0 or star_snr is None:
        return None
    return (1 + int((c >= float(star_snr)).sum())) / (c.size + 1.0)


if __name__ == '__main__':
    print('probes %d, seed %d, radii %.3f-%.3f theta_PB in %d bins'
          % (NPROBE, SEED, RADII.min(), RADII.max(), NBIN))
    print('rank floor %.6f' % FLOOR)
