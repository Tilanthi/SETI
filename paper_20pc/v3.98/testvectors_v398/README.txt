Known-answer test vectors
=========================

These four datasets exist so that the recovery behaviour of the search can
be checked by someone who did not write it. They are generated in
make_testvectors_v393.py from first principles -- Gaussian noise plus a
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
