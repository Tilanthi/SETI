#!/usr/bin/env python3
"""R2-2 (v3.95): a known-answer test set that does NOT depend on this
paper's own injection code to generate the truth it is checked against.

Referee 2's point is exact: every validation in this paper shares one
codebase with the search, so none of them can catch a fault common to
both. The remedy they ask for is a small set of documented synthetic
vectors with analytically specified truth, so that someone who did not
write the pipeline can reproduce the recovery behaviour independently.

The vectors here are generated from first principles in this file --
Gaussian noise plus a closed-form drifting sinusoid -- with no import from
the search or injection modules. The expected detection statistic follows
from the matched-filter algebra stated in the header of each case, so a
third party can check the pipeline against arithmetic rather than against
our code.
"""
import hashlib
import json
import os

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, 'testvectors_v395')
os.makedirs(OUT, exist_ok=True)
RNG = np.random.default_rng(20260923)

NCHAN, NINT = 512, 64
CHANW_HZ = 488281.25
DT_S = 30.0

CASES = [
    dict(name='null', amp=0.0, drift_hz_s=0.0,
         note='pure noise; no carrier. Expect max |T| consistent with the '
              'extreme of NCHAN x NDRIFT standard normals.'),
    dict(name='stationary_5sigma', amp=5.0, drift_hz_s=0.0,
         note='stationary carrier at 5 sigma per-integration-stacked '
              'amplitude, centred in one channel. Expect T ~ 5 at zero '
              'drift, and a loss of ~sqrt(2) at half-channel offset.'),
    dict(name='drifting_5sigma', amp=5.0,
         drift_hz_s=CHANW_HZ / (NINT * DT_S) * 4.0,
         note='carrier drifting by four channels across the track. Expect '
              'T ~ 5 ONLY at the matching drift trial; stacking at zero '
              'drift must lose approximately sqrt(NINT/4).'),
    dict(name='drifting_offgrid', amp=5.0,
         drift_hz_s=CHANW_HZ / (NINT * DT_S) * 4.5,
         note='drift falling between two trial rates. Expect the recovered '
              'amplitude to be reduced relative to the on-grid case; this '
              'is the grid-loss term the completeness curve must capture.'),
]

man = []
for c in CASES:
    sig = RNG.standard_normal((NINT, NCHAN))
    if c['amp'] > 0:
        c0 = NCHAN // 2
        for i in range(NINT):
            shift = c['drift_hz_s'] * (i * DT_S) / CHANW_HZ
            ch = int(round(c0 + shift))
            if 0 <= ch < NCHAN:
                sig[i, ch] += c['amp'] / np.sqrt(NINT)
    f = os.path.join(OUT, c['name'] + '.npz')
    np.savez_compressed(f, spectra=sig.astype(np.float32),
                        chanw_hz=CHANW_HZ, dt_s=DT_S,
                        drift_hz_s=c['drift_hz_s'], amp_sigma=c['amp'])
    man.append(dict(file=os.path.basename(f), sha256=hashlib.sha256(
        open(f, 'rb').read()).hexdigest(), **{k: v for k, v in c.items()}))

readme = """Known-answer test vectors
=========================

These four datasets exist so that the recovery behaviour of the search can
be checked by someone who did not write it. They are generated in
make_testvectors_v395.py from first principles -- Gaussian noise plus a
closed-form drifting sinusoid -- and import nothing from the search or the
injection code, so the "truth" they encode does not come from the same
source as the thing being tested.

Each .npz holds:
    spectra      (n_int, n_chan) float32, per-integration spectra
    chanw_hz     channel width
    dt_s         integration time
    drift_hz_s   the true drift rate of the injected carrier
    amp_sigma    the injected amplitude, in sigma of the stacked spectrum

A correct implementation, stacking along a trial drift track and
normalising by the noise of the stacked spectrum, should recover the
stated amplitude at the matching drift trial and lose signal at others by
the amount the note for each case gives. The null case contains no
carrier and bounds the false-alarm behaviour of the stacking alone.

Reporting a disagreement with these expectations is more useful to us than
agreement: it is the only check in this release that is independent of our
own tooling.
"""
open(os.path.join(OUT, 'README.txt'), 'w').write(readme)
json.dump(man, open(os.path.join(OUT, 'manifest.json'), 'w'), indent=1)
print('wrote %d known-answer vectors to %s' % (len(man), os.path.basename(OUT)))
for m in man:
    print('   %-22s drift %10.3f Hz/s  amp %.1f sigma'
          % (m['file'], m['drift_hz_s'], m['amp']))
