#!/usr/bin/env python3
"""Fetch the QA0 report of every execution block in the released catalogue
that has one, keep only the text of its summary page, and delete the PDF.

The quantity wanted is the line

    Phase rms: NN microns

in the Weather block of the Execution Block Summary: the residual
path-length fluctuation measured on the phase calibrator after the
water-vapour-radiometer correction.  The report also prints the same
quantity in degrees at the representative sky frequency, as

    Phase fluctuations : A deg (bandpass)  B deg (phaseCal)

and the two must agree through the wavelength; that is the check on the
reading, and it is applied in measure_decor.py rather than here.
"""
import json
import os
import re
import subprocess
import urllib.request

HERE = os.path.dirname(os.path.abspath(__file__))
W = json.load(open(os.path.join(HERE, 'qa0_wanted.json')))
TXT = os.path.join(HERE, 'qa0txt')
os.makedirs(TXT, exist_ok=True)
KEEP = re.compile(
    r'Repr\. frequency|Phase rms:|Phase fluctuations|Band *ALMA_RB|'
    r'Bandpass RMS|PhaseCal RMS|baseline-based phase rms|ExecBlock |'
    r'Baselines|Array |PWV|Mean Zenith PWV|QA0 Status|Amplitude fluctuations')
n_ok = n_skip = 0
for eb, name in sorted(W.items()):
    out = os.path.join(TXT, eb + '.txt')
    if os.path.exists(out):
        n_skip += 1
        continue
    pdf = os.path.join(HERE, '_tmp.pdf')
    try:
        with urllib.request.urlopen(
                'https://almascience.eso.org/dataPortal/' + name,
                timeout=180) as r:
            open(pdf, 'wb').write(r.read())
        t = subprocess.run(['pdftotext', '-layout', '-f', '1', '-l', '2',
                            pdf, '-'], capture_output=True, text=True).stdout
    except Exception as exc:                                     # noqa: BLE001
        print('FAIL', eb, type(exc).__name__, exc)
        continue
    finally:
        if os.path.exists(pdf):
            os.remove(pdf)
    lines = [ln.rstrip() for ln in t.splitlines() if KEEP.search(ln)]
    open(out, 'w').write('\n'.join(lines) + '\n')
    n_ok += 1
    if n_ok % 25 == 0:
        print('  %d fetched' % n_ok, flush=True)
print('%d fetched, %d already present, %d text files'
      % (n_ok, n_skip, len(os.listdir(TXT))))
