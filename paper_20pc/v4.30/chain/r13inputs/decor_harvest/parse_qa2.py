#!/usr/bin/env python3
"""Read the per-execution-block phase rms out of every QA2 report harvested.

The QA2 report of a member observation unit set carries an "Execution blocks
summary" table with one row per execution block: number of antennas, time on
source, elevation, mean precipitable water vapour, the WVR-corrected mean
phase rms in degrees averaged over all basebands and scans, and the baseline
extremes.  The phase rms is the quantity wanted.

Two deliveries of the same table exist in the archive, an HTML one and a PDF
one.  The HTML is a cell-delimited table and is parsed directly.  The PDF is
parsed from word bounding boxes, assigning each word to a column by the
x-centre of the column header.  Where both exist the two must agree, and
that is asserted rather than assumed.
"""
import glob
import json
import os
import re
import subprocess
import sys
import xml.etree.ElementTree as ET

HERE = os.path.dirname(os.path.abspath(__file__))
QA2 = os.path.join(HERE, 'qa2')
EBRE = re.compile(r'uid://A002/X[0-9a-f]+/X[0-9a-f]+', re.I)


# --------------------------------------------------------------- HTML route
def from_html(path):
    s = open(path, errors='replace').read()
    i = s.lower().find('execution blocks summary')
    if i < 0:
        return {}
    cells = [re.sub(r'\s+', ' ', re.sub(r'&nbsp;|&quot;', ' ', c)).strip()
             for c in re.sub(r'<[^>]+>', '\x00', s[i:]).split('\x00')]
    cells = [c for c in cells if c]
    # the header ends at 'EF'; the column index of the phase rms within a row
    try:
        h0 = cells.index('EB')
    except ValueError:
        return {}
    hdr = cells[h0:]
    try:
        hend = hdr.index('EF')
    except ValueError:
        return {}
    cols = [c for c in hdr[:hend + 1] if c != '*']
    try:
        k = next(j for j, c in enumerate(cols) if 'Phase RMS' in c)
    except StopIteration:
        return {}
    body = [c for c in hdr[hend + 1:] if c != '*']
    out = {}
    j = 0
    while j < len(body):
        if not EBRE.fullmatch(body[j]):
            j += 1
            continue
        row = body[j:j + len(cols)]
        if len(row) < len(cols):
            break
        try:
            out[row[0]] = float(row[k])
        except ValueError:
            pass
        j += len(cols)
    return out


# ---------------------------------------------------------------- PDF route
def from_pdf(path):
    xml = subprocess.run(['pdftotext', '-bbox-layout', path, '-'],
                         capture_output=True, text=True).stdout
    root = ET.fromstring(xml)
    ns = {'x': root.tag.split('}')[0].strip('{')} if '}' in root.tag else {}
    def words(page):
        for w in page.iter():
            if w.tag.endswith('word'):
                yield (float(w.get('xMin')), float(w.get('xMax')),
                       float(w.get('yMin')), (w.text or '').strip())
    out = {}
    for page in root.iter():
        if not page.tag.endswith('page'):
            continue
        W = sorted(words(page), key=lambda t: (round(t[2], 1), t[0]))
        if not any(w[3] == 'RMS' for w in W):
            continue
        # the column header is the word 'RMS' that sits directly under 'Phase'
        cand = [w for w in W if w[3] == 'RMS']
        ph = [w for w in W if w[3] == 'Phase']
        col = None
        for r in cand:
            for p in ph:
                if abs((r[0] + r[1]) / 2 - (p[0] + p[1]) / 2) < 25 \
                        and 0 < r[2] - p[2] < 40:
                    col = ((r[0] + r[1]) / 2, r[2])
        if col is None:
            continue
        xc, ytop = col
        # ★ A VALUE CAN BE WRAPPED OVER TWO LINES in this table ('137.56'
        # then '0' on the line below), and reading one line only silently
        # returns the fragment -- 0.0 for a block whose phase rms is the
        # worst in the sample.  So the tokens of the column are clustered
        # vertically first and concatenated, and only then matched to a row.
        toks = sorted([t for t in W if t[2] > ytop
                       and abs((t[0] + t[1]) / 2 - xc) <= 22
                       and re.fullmatch(r'[0-9][0-9.]*', t[3])],
                      key=lambda t: (t[2], t[0]))
        groups = []
        for t in toks:
            if groups and t[2] - groups[-1][-1][2] < 15:
                groups[-1].append(t)
            else:
                groups.append([t])
        uids = sorted([u for u in W if u[2] > ytop
                       and u[3].startswith('uid://A002')],
                      key=lambda t: t[2])
        if not uids:
            continue
        for g in groups:
            try:
                v = float(''.join(t[3] for t in g))
            except ValueError:
                continue
            y = sum(t[2] for t in g) / len(g)
            u = min(uids, key=lambda t: abs(t[2] - y))
            if abs(u[2] - y) > 30:
                continue
            uid = u[3]
            if not EBRE.fullmatch(uid):
                frag = [t for t in sorted(W, key=lambda t: (t[2], t[0]))
                        if 0 < t[2] - u[2] < 40 and t[0] < u[1] - 1
                        and re.fullmatch(r'[0-9a-f]+', t[3], re.I)]
                if frag:
                    uid += frag[0][3]
            out[uid] = v
    return out


def norm(u):
    return u.replace('uid://', '').replace('/', '_')


H, P = {}, {}
for f in sorted(glob.glob(os.path.join(QA2, '*.qa2_report.html'))):
    H[os.path.basename(f).split('.qa2')[0]] = from_html(f)
for f in sorted(glob.glob(os.path.join(QA2, '*.qa2_report.pdf'))):
    P[os.path.basename(f).split('.qa2')[0]] = from_pdf(f)

# ★ the two routes must agree wherever both deliver the same block.  This is
# the check that the PDF column assignment is right; it fails loudly if the
# bounding-box heuristic picks up the wrong column.
agree = dis = 0
bad = []
for m in sorted(set(H) & set(P)):
    for eb, v in H[m].items():
        if eb in P[m]:
            if abs(P[m][eb] - v) < 1e-6:
                agree += 1
            else:
                dis += 1
                bad.append((m, eb, v, P[m][eb]))
print('HTML x PDF cross-check: %d blocks agree, %d disagree' % (agree, dis))
for b in bad[:10]:
    print('   DISAGREE', b)

MERGED = {}
for src in (P, H):                     # HTML wins where both exist
    for m, d in src.items():
        for eb, v in d.items():
            MERGED.setdefault(norm(eb), {})[m] = v
flat = {eb: sorted(d.values())[len(d) // 2] for eb, d in MERGED.items()}
print('%d distinct execution blocks carry a phase rms' % len(flat))
json.dump({'phase_rms_deg': flat,
           'n_html': sum(len(v) for v in H.values()),
           'n_pdf': sum(len(v) for v in P.values()),
           'xcheck_agree': agree, 'xcheck_disagree': dis},
          open(os.path.join(HERE, 'qa2_phaserms.json'), 'w'), indent=1)
if dis:
    sys.exit('PDF and HTML disagree')
