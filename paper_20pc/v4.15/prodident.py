#!/usr/bin/env python3
r"""GATE: a record that names a product must prove it is the RIGHT product.

★★★ THE DEFECT.  489 of the 2,729 retained windows exist in more than one
directory on the host -- `<star>_B7/products/` and
`<star>_B7_EB_<tag>/products/` hold the same execution block with the same
integration count -- and **372 of those pairs disagree about the window's own
peak statistic**.  The released catalogue carries the per-block `_EB_` copy.
A measurement script that resolves the ambiguity by sort order, or by
preferring one directory shape, is therefore right only by luck: the
round-10 recurrence pass did exactly that on its first run and silently
moved four crossings' statistics by 2 to 4 per cent.

The fix is not a better preference.  It is to make the identification a
MEASUREMENT -- the product is the one that reproduces the statistic the
paper prints for that window -- and `r10_recur_all.py` now records
`window_peak_pub` for every product it opens and `gate_rel` for the
discovery windows.  That rule is what this gate generalises, so that the
next frozen record naming a product is not believed merely because it
exists:

  P1  every record that names a product and claims a published window peak
      says whether that window is in the released catalogue;
  P2  every such record that IS in the released catalogue reproduces the
      catalogue's own published statistic for that window.  Measured
      against the CATALOGUE, not against the record's own copy of the
      number: a record checked against itself is the circular diagnostic
      this project has met before;
  P3  no two records naming the same (block, spectral window) carry
      different published peaks -- i.e. the two-directory ambiguity was
      resolved the same way everywhere, and not per call site;
  P4  the gate is not vacuous: it must find records, it must find windows
      that ARE in the catalogue, and it must find at least one product
      reached under a per-block `_EB_` stem, which is the shape the
      ambiguity lives in.

    python3 prodident.py [--drive N]

Exit 1 on any failure.  --drive 1..4 breaks one clause each.
"""
import csv
import glob
import json
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
CAT_NAME = 'per_target_results_v3.99.csv'
TOL = 1e-4          # relative; the records agree to 1e-8

# ★ THE PRODUCT TREES, DECLARED.  A product under the released tree must
# reproduce the catalogue's published statistic, because the catalogue was
# built from it.  A product under the field-truncation RE-EXTRACTION tree
# must NOT: it is a different measurement of the same window, which is the
# whole point of the repair -- BD+05 1668's four crossings go from 8.8-17.5
# to 39.6-73.4 there.  So the comparison is made per tree, and a tree that
# is not declared here FAILS rather than being silently exempt.  Carving out
# an exception by path is how a gate stops meaning anything; declaring the
# trees is how it keeps meaning something when a new one appears.
TREES = {
    '/data/SETI/targets': ('released', 'the products the released catalogue '
                           'was built from; must reproduce it'),
    '/data/SETI/r8reext/targets': (
        'reextracted', 'the field-truncation re-extraction; a DIFFERENT '
        'measurement of the same window by construction, so its peak must '
        'not be required to match the released catalogue'),
}


def tree_of(stem):
    for root in sorted(TREES, key=len, reverse=True):
        if stem.startswith(root + '/'):
            return root
    return None


def _walk(x):
    if isinstance(x, dict):
        yield x
        for v in x.values():
            for y in _walk(v):
                yield y
    elif isinstance(x, list):
        for v in x:
            for y in _walk(v):
                yield y


def _eb_of(stem):
    m = re.search(r'(A002_X[0-9a-f]+_X[0-9a-f]+)', stem)
    return m.group(1) if m else None


def _spw_of(stem):
    m = re.search(r'_spw(\d+)$', stem)
    return int(m.group(1)) if m else None


def records():
    """Every frozen record that names a product AND claims its window's
    published peak.  Discovered by SHAPE, not from a list of filenames:
    enumerating names has failed in this tree five times."""
    out = []
    for path in sorted(glob.glob(os.path.join(HERE, '*.json'))
                       + glob.glob(os.path.join(HERE, 'r10inputs', '*.json'))
                       + glob.glob(os.path.join(HERE, 'r8inputs', '**',
                                                '*.json'), recursive=True)
                       + glob.glob(os.path.join(HERE, 'r9inputs', '*.json'))):
        try:
            doc = json.load(open(path, errors='ignore'))
        except Exception:
            continue
        for d in _walk(doc):
            if not isinstance(d, dict) or 'stem' not in d:
                continue
            pk = d.get('window_peak_pub', d.get('T_bestdrift_pub'))
            if pk is None:
                continue
            out.append((os.path.relpath(path, HERE), d, float(pk)))
    return out


def main(argv):
    drive = 0
    for i, a in enumerate(argv):
        if a == '--drive':
            drive = int(argv[i + 1])
    CAT = list(csv.DictReader(open(os.path.join(HERE, CAT_NAME))))
    # the published statistic, keyed on (block, channel width): the stem
    # carries the spectral-window number and the catalogue does not, so the
    # comparison is "this value is one of the published peaks of this block
    # at this channel width", which is what a reproduction check can claim
    # without inventing a join.
    pub = {}
    for r in CAT:
        pub.setdefault((r['eb'], round(float(r['chanw_Hz']))),
                       []).append(float(r['star_snr']))

    recs = records()
    if drive == 4:
        recs = []
    fail, n_incat, n_ok, multi, n_other = [], 0, 0, 0, 0
    tail = []
    byspw = {}
    for src, d, pk in recs:
        stem = d['stem']
        if re.search(r'_EB_[^/]*/products/', stem):
            multi += 1
        incat = d.get('in_released_catalogue')
        if incat is None:
            incat = d.get('gate_ok')
        if incat is None:
            fail.append('P1 %s names product %s with a published window peak '
                        'and does not say whether the window is in the '
                        'released catalogue' % (src, stem))
            continue
        if drive == 1 and n_incat == 0:
            fail.append('P1 %s (driven) does not say whether its window is '
                        'in the released catalogue' % src)
        k = (tree_of(stem), _eb_of(stem), _spw_of(stem))
        byspw.setdefault(k, set()).add(round(pk, 6))
        root = tree_of(stem)
        if root is None:
            fail.append('P2b %s names product %s under a product tree this '
                        'gate does not know, so whether its peak should '
                        'reproduce the released catalogue is undeclared'
                        % (src, stem))
            continue
        if TREES[root][0] != 'released':
            n_other += 1
            continue
        if not incat:
            continue
        n_incat += 1
        cand = pub.get((_eb_of(stem), round(float(d['chanw_Hz']))), [])
        got = pk if drive != 2 or n_incat != 1 else pk * 1.05
        if not cand:
            # ★ The block and channel width are not in the DEPOSITED
            # catalogue at all.  Those windows exist: the deposited
            # catalogue stays at 1,651 rows while the survey's own extent is
            # 1,687, the difference being the archival tail and the restored
            # companion, and the record's `in_released_catalogue` evidently
            # means "in the census" rather than "in the deposited csv".
            # That is a declared divergence of this project, not a defect of
            # the record -- so it is NAMED and PINNED, and a fifth one is a
            # failure rather than another line of commentary.
            tail.append((_eb_of(stem), _spw_of(stem)))
            continue
        if any(abs(x - got) <= TOL * max(1.0, abs(x)) for x in cand):
            n_ok += 1
        else:
            fail.append('P2 %s product %s claims a published peak of %.6f '
                        'which is not one the catalogue publishes for block '
                        '%s at %g Hz channels (%s)'
                        % (src, stem, got, _eb_of(stem),
                           float(d['chanw_Hz']),
                           ['%.4f' % x for x in sorted(cand)[:4]]))
    split = {k: v for k, v in byspw.items() if len(v) > 1 and k[1] and
             k[2] is not None}
    if drive == 3:
        split[('/drive', 'A002_Xdrive_X0', 0)] = {1.0, 2.0}
    for k, v in sorted(split.items(), key=lambda t: str(t[0]))[:6]:
        fail.append('P3 block %s spw %s under %s is named with %d different '
                    'published peaks (%s) -- the two-directory ambiguity was '
                    'resolved differently in different places'
                    % (k[1], k[2], k[0], len(v),
                       ['%.4f' % x for x in sorted(v)]))
    # P2c: the windows the deposited catalogue does not carry, pinned.
    TAIL_DECLARED = {('A002_X1190de8_Xd526', 3), ('A002_X11adad7_X25c5e', 3),
                     ('A002_Xc6b674_X28f5', 0)}
    tails = set(tail)
    if drive == 5:
        tails = tails | {('A002_Xdrive_X0', 0)}
    if tails != TAIL_DECLARED:
        fail.append('P2c the windows named by a record and absent from the '
                    'deposited catalogue are %s; the declared set is the '
                    'archival tail %s.  A new one is a window the paper '
                    'cannot be checked on.'
                    % (sorted(tails), sorted(TAIL_DECLARED)))
    if not recs:
        fail.append('P4 no record naming a product was found, so this gate '
                    'checked nothing')
    if not n_incat:
        fail.append('P4 no record names a window that is in the released '
                    'catalogue, so nothing could be compared with it')
    if not multi:
        fail.append('P4 no product is reached under a per-block `_EB_` stem, '
                    'so the ambiguity this gate exists for is not present '
                    'and a pass is evidence of nothing')
    print('prodident: %d record(s) naming a product; %d under the released '
          'tree and in the catalogue, %d of those reproducing its published '
          'statistic; %d under the re-extraction tree, which must not; %d '
          'reached under a per-block stem'
          % (len(recs), n_incat, n_ok, n_other, multi))
    print('prodident: %d window(s) named by a record and absent from the '
          'deposited catalogue (the declared archival tail): %s'
          % (len(tails), sorted(tails)))
    for f in fail[:12]:
        print('  FAIL ' + f)
    if len(fail) > 12:
        print('  ... and %d more' % (len(fail) - 12))
    print('prodident: %d FAIL' % len(fail))
    return 1 if fail else 0


if __name__ == '__main__':
    sys.exit(main(sys.argv))
