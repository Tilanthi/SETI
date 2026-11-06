#!/usr/bin/env python3
r"""r21_splat.py -- the shared Splatalogue helpers for round 21.

Separated from the harvest scripts for one reason, learnt the hard way: a
harvest script is a SCRIPT, so `from r21_harvest import query` re-ran the
whole harvest, re-queried the service and rewrote its own output with a new
query date.  A module that is imported must do nothing when imported.
"""
import re
import time

import astropy.units as u
from astroquery.splatalogue import Splatalogue

EU_MAX = 150.0            # K, the referee's own cut and the mask's own cut
C_KMS = 299792.458


def clean(s):
    """Splatalogue returns HTML; a species name is what is left of it."""
    s = re.sub(r'<[^>]*>', '', str(s))
    s = s.replace('&Delta;', 'D').replace('&nbsp;', ' ')
    return re.sub(r'\s+', ' ', s).strip()


def molecule(name):
    """The molecule, with the vibrational/torsional state label removed, so
    that a CDMS entry and the Lovas entry that records the detection of the
    same molecule carry one key.  Isotopologues stay distinct, which is
    right: a detected isotopologue is its own species."""
    s = clean(name)
    s = re.sub(r'\s*,?\s*v\s*[a-z]?\s*=\s*[^,]*$', '', s, flags=re.I)
    s = re.sub(r'\s*,?\s*v\s*[a-z]?\s*[<>]\s*\S+$', '', s, flags=re.I)
    s = re.sub(r'\s*,?\s*D\s*v\s*[<>]\s*\S+$', '', s, flags=re.I)
    return s.strip().rstrip(',').strip()


def num(v):
    m = re.search(r'-?\d+\.?\d*', str(v).replace('<span', ' '))
    return float(m.group()) if m else float('nan')


def freq_ghz(row):
    """The transition frequency in GHz.

    ★ READ `orderedfreq` (a float, in MHz) FIRST.  `orderedFreq` is HTML, and
    for the NRAO-recommended lines -- CO(2-1) among them -- it is an EMPTY
    coloured span, so a parser that takes the first number out of the markup
    reads 143 out of the colour code `#DC143C`.  That silently dropped the
    brightest lines in the band from the first harvest, and the assertion
    requiring the frozen mask to be recovered is what caught it.
    """
    try:
        f = float(row['orderedfreq'])          # MHz
        if f == f and f > 0:
            return f / 1000.0
    except (TypeError, ValueError):
        pass
    f = num(clean(row['orderedFreq']))         # GHz, tags stripped first
    if f == f and f > 0:
        return f / 1000.0 if f > 1000.0 else f
    f = num(clean(row['measFreq']))
    return f / 1000.0 if f > 1000.0 else f


def query(a, b, **kw):
    # ★ cache=False deliberately: astroquery's on-disk cache grew to 119 MB on
    # a root filesystem with 1.5 MB free and the harvest died of it.  A line
    # list queried once and frozen to json needs no second cache.
    for att in range(5):
        try:
            return Splatalogue.query_lines(a * u.GHz, b * u.GHz, cache=False,
                                           **kw)
        except Exception as e:
            print('   retry %d  %.3f-%.3f  %s' % (att, a, b, e), flush=True)
            time.sleep(3 + 5 * att)
    raise SystemExit('QUERYFAIL %.3f-%.3f' % (a, b))


def union(iv):
    out = []
    for a, b in sorted((min(x, y), max(x, y)) for x, y in iv):
        if out and a <= out[-1][1]:
            out[-1][1] = max(out[-1][1], b)
        else:
            out.append([a, b])
    return out
