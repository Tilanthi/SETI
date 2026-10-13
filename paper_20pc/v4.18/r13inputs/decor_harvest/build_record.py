#!/usr/bin/env python3
"""Freeze the harvested per-block phase stability into the build's input set.

Writes v4.14/r13inputs/decor_r13.json: for every execution block of the
released catalogue whose QA0 report the archive exposes individually, the
residual path-length fluctuation the observatory measured on that block's
phase calibrator after the water-vapour-radiometer correction, together with
the quantities needed to check the reading.

Provenance of each number: the line

    Phase rms: <value> microns

in the Execution Block Summary of
<execblock>.qa0_report.pdf, fetched from the ALMA data portal.  The same
report prints the same quantity in degrees at the block's representative sky
frequency as "<x> deg (phaseCal)" wherever the AOS check ran, and the two
agree through the wavelength to the precision of the printed value; that pair
is carried here so the generator can check it rather than trust it.
"""
import glob
import json
import os
import re

HERE = os.path.dirname(os.path.abspath(__file__))
DEST = '/workspace/SETI/paper_20pc/v4.14/r13inputs'
os.makedirs(DEST, exist_ok=True)
LINKS = json.load(open(os.path.join(HERE, 'qa_links.json')))
FILE = {}
for _m, _rec in LINKS.items():
    for _n, _s in _rec.get('qa0', []):
        FILE[_n.split('.qa0')[0].replace('uid___', '')] = _n

blocks = {}
nofile = []
for path in sorted(glob.glob(os.path.join(HERE, 'qa0txt', '*.txt'))):
    eb = os.path.basename(path)[:-4]
    s = open(path).read()
    um = re.search(r'Phase rms:\s*([0-9.]+)\s*microns', s)
    if not um:
        nofile.append(eb)
        continue
    fr = re.search(r'Repr\. frequency\s*([0-9.]+)\s*GHz', s)
    fl = re.search(r'Phase fluctuations\s*:\s*([0-9.]+)\s*deg \(bandpass\)'
                   r'\s*([0-9.]+)\s*deg \(phaseCal\)', s)
    bl = re.search(r'Baselines\s+([0-9.]+)m\s*--\s*([0-9.]+)m', s)
    ar = re.search(r'Array\s+([0-9.]+)\s*\[m\]', s)
    rec = {'path_rms_um': float(um.group(1)),
           'qa0_report': FILE.get(eb)}
    if fr:
        rec['repr_freq_ghz'] = float(fr.group(1))
    if fl:
        rec['stated_phasecal_deg'] = float(fl.group(2))
        rec['stated_bandpass_deg'] = float(fl.group(1))
    if bl:
        rec['bl_min_m'] = float(bl.group(1))
        rec['bl_max_m'] = float(bl.group(2))
    if ar:
        rec['array_m'] = float(ar.group(1))
    blocks[eb] = rec

OUT = {
    '_doc':
        'THE DECORRELATION TERM, MEASURED.  An artificial carrier is added '
        'to visibilities that the ALMA pipeline has already phase- and '
        'amplitude-calibrated, so it carries no atmospheric coherence loss '
        'at all, while a real carrier carries the loss of the block that '
        'recorded it.  The quantity at issue is therefore the coherence of a '
        'point source at the phase centre, and that is what the observatory '
        'measures in every block on its phase calibrator.  This record '
        'carries, per execution block, the residual path-length fluctuation '
        '(micron) measured on the phase calibrator after the WVR correction, '
        'read from the block\'s own QA0 report.  Expressed as a path length '
        'it is frequency-independent, so the phase rms of any window follows '
        'from the window\'s own sky frequency and the band dependence is a '
        'consequence rather than an assumption.',
    '_relation':
        'phi_rms[deg] = 360 * dL[micron] / lambda[micron]; coherence = '
        'exp(-phi_rms[rad]**2 / 2) for a Gaussian phase error over the '
        'interval stacked.  ALMA Memo 620 (Richards et al. 2022) Eqs. 3 and '
        '6; Thompson, Moran & Swenson (2017) Ch. 7.2.8.  The limit must be '
        'divided by the coherence, so it is optimistic by 1/coherence - 1.',
    '_direction':
        'ONE-SIDED, and the sign is not a choice: a negative branch would '
        'assert that a real carrier is recovered better than an injected '
        'one, which the injection route cannot produce.',
    '_caveat':
        'Measured on the phase calibrator itself, so it does not include the '
        'interpolation of the solution onto the target or the '
        'calibrator-target separation; the loss a target suffers is at least '
        'this large.  ALMA Technical Handbook Sec. 10.4.11.',
    '_source': 'ALMA science archive, per-execution-block QA0 reports, '
               'harvested 2026-10-07; one file per block, named in each '
               'entry.  The three scripts that produced it are deposited '
               'beside it in r13inputs/decor_harvest/: harvest_links.py asks '
               'the archive which small per-block quality files each member '
               'OUS exposes individually, fetch_qa0.py downloads each report '
               'and keeps only the summary lines, build_record.py writes this '
               'file.  parse_qa2.py is deposited with them for the negative '
               'result described below.',
    '_rejected':
        'The QA2 report of a member OUS also carries a per-block column '
        'headed "Mean Phase RMS (deg)", footnoted as a WVR-corrected value '
        'averaged over all basebands and scans, and it is NOT the same '
        'quantity: over the 225 blocks where both exist the ratio of the two '
        'runs from 0.07 to 5.7, and the QA2 column gives 57-137 degrees for '
        'compact-array blocks whose longest baseline is 49 m, which is not '
        'physical.  It is therefore not used.  The QA0 figure used here is '
        'self-validating -- the report prints the same number in microns and '
        'in degrees and the two agree through the wavelength -- and it '
        'behaves like a tropospheric quantity, rising with baseline length.',
    'measured_here': True,
    'superseded_declaration': {
        '_was': 'a two-sided -12/+17 per cent bracket from a superseded '
                'campaign record, then a one-sided +0/+20 per cent declared '
                'with no reference at all',
        'declared_one_sided': [0.05, 0.20],
        'declared_two_sided': [-0.12438328424153167, 0.16683704409598876]},
    'blocks': blocks,
}
json.dump(OUT, open(os.path.join(DEST, 'decor_r13.json'), 'w'), indent=1,
          sort_keys=False)
print('%d blocks with a measured path rms; %d QA0 reports carried no numeric '
      'value (older report format)' % (len(blocks), len(nofile)))
