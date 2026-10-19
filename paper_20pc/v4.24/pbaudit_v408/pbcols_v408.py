#!/usr/bin/env python3
"""ITEM 2: ship `pb_offset_arcsec` and `pb_atten` in the catalogue.

`/workspace/SETI/paper_20pc/` is read-only for this worker, so the patch to
v342_calc.py is defined HERE as an exact source substitution, written out as a
unified diff for v4.08 to apply, and then DEMONSTRATED: the patched generator is
executed with `cwd` at the version directory and every write redirected through a
shim on `builtins.open`, so nothing under paper_20pc/ is modified.  (A symlink
farm would not do -- `open(p, 'w')` follows symlinks and would truncate the real
products.  Same lesson as selftest_v404.)

Checks afterwards:
  * the CSV gains exactly two columns and NCatCols goes 60 -> 62;
  * every other column of every row is byte-identical to the shipped release;
  * `smin == 5 rms / pb_atten` on every row whose A came from a product;
  * the assertion on the column count is driven BOTH WAYS.
"""
import builtins, difflib, io, json, csv, math, os, shutil, subprocess, sys, tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
V = os.path.normpath(os.path.join(HERE, '..', '..', 'paper_20pc', 'v4.07'))
GEN = os.path.join(V, 'v342_calc.py')
OUTDIR = os.path.join(tempfile.gettempdir(), 'pbcols_out')

# ----------------------------------------------------------------- the patch --
OLD_COLS = """        'scale_route_a', 'scale_route_b', 'n_search_cells', 'n_ind_cells',
        'trigger_1pct_window', 'trigger_1pct_survey']"""
NEW_COLS = """        'scale_route_a', 'scale_route_b', 'n_search_cells', 'n_ind_cells',
        'trigger_1pct_window', 'trigger_1pct_survey',
        # v4.08 (D29): the release paired an APPARENT rms with a
        # primary-beam-CORRECTED S_min and shipped no column for the response,
        # so on 91 windows smin != 5 rms and nothing in the deposit explained
        # the difference (x1.81 at worst).  These two columns close the chain:
        # smin_mJy == 5 * rms_mJy / pb_atten, exactly, on every window whose
        # product survives.  pb_atten is the response the pipeline APPLIED --
        # its Gaussian at 1.22 lambda/D -- not the better blocked-Airy value,
        # because it has to reproduce what was published; the <=7 per cent
        # model difference is stated in the text instead.  Note that
        # theta_pb_arcsec CANNOT be used to recompute pb_atten: it is
        # 1.22 lambda / 12 m for every window, including the 1054 ACA rows.
        'pb_offset_arcsec', 'pb_atten']"""

OLD_ROW = """DISPO_RECS = []"""
NEW_ROW = """DISPO_RECS = []
# v4.08 (D29): frozen input built by referee_r8/pbaudit/pbcat_v408.py, which
# resolves each released window to its product BY POSITION (the (eb, window)
# pair is not a key: two Gaia components share a block and their rms agree to
# the five decimals printed here) and recovers Wolf 28's missing offset from
# that product's own stored geometry.  Keyed on released_name(star), eb and the
# window to 1 MHz.
PBCAT = json.load(open('pbcat_v408.json'))
PB_FTOL = 0.002          # GHz; windows are ~2 GHz wide


def _pb(r):
    lo, hi = min(r['flo'], r['fhi']), max(r['flo'], r['fhi'])
    v = [e for e in PBCAT.get('%s|%s' % (released_name(r['star_name']), r['eb']), ())
         if abs(e['flo'] - lo) < PB_FTOL and abs(e['fhi'] - hi) < PB_FTOL]
    assert len(v) == 1, ('%d primary-beam entries for %s %s %.4f-%.4f GHz'
                         % (len(v), r['star_name'], r['eb'], lo, hi))
    return v[0]


for _r in GOOD:
    _r['pb'] = _pb(_r)"""

OLD_WRITE = """            ('%.4f' % r['t_win']) if r['t_win'] is not None else '',
            ('%.4f' % r['t_survey']) if r['t_survey'] is not None else '',
        ])"""
NEW_WRITE = """            ('%.4f' % r['t_win']) if r['t_win'] is not None else '',
            ('%.4f' % r['t_survey']) if r['t_survey'] is not None else '',
            '%.4f' % r['pb']['pb_offset_arcsec'],
            '%.6f' % r['pb']['pb_atten'],
        ])"""

OLD_NCAT = """M('NCatCols', '%d' % len(COLS))"""
NEW_NCAT = """M('NCatCols', '%d' % len(COLS))
# v4.08 (D29): the count is pinned with == so adding a column is a deliberate
# act.  Driven both ways in referee_r8/pbaudit/pbcols_v408.py.
assert len(COLS) == 62, 'catalogue column count moved to %d' % len(COLS)
assert 'pb_atten' in COLS and 'pb_offset_arcsec' in COLS"""

PATCHES = [(OLD_COLS, NEW_COLS), (OLD_ROW, NEW_ROW),
           (OLD_WRITE, NEW_WRITE), (OLD_NCAT, NEW_NCAT)]


def patched_source(ncols_override=None):
    s = open(GEN).read()
    for a, b in PATCHES:
        n = s.count(a)
        assert n == 1, 'patch anchor appears %d times: %r' % (n, a[:60])
        s = s.replace(a, b)
    if ncols_override is not None:                      # the reverse drive
        s = s.replace("assert len(COLS) == 62", "assert len(COLS) == %d" % ncols_override)
    return s


def run(src, tag):
    """execute with cwd at the deposit and every WRITE redirected"""
    os.makedirs(OUTDIR, exist_ok=True)
    real_open = builtins.open
    written = {}

    def shim(file, mode='r', *a, **k):
        # the one new INPUT lives here, not in the deposit (v4.08 will copy it in)
        if isinstance(file, str) and os.path.basename(file) == 'pbcat_v408.json' \
                and 'r' in str(mode):
            return real_open(os.path.join(HERE, 'pbcat_v408.json'), mode, *a, **k)
        if isinstance(file, (str, bytes, os.PathLike)) and \
                any(c in str(mode) for c in 'wxa+'):
            dst = os.path.join(OUTDIR, tag + '_' + os.path.basename(str(file)))
            written[os.path.basename(str(file))] = dst
            return real_open(dst, mode, *a, **k)
        return real_open(file, mode, *a, **k)

    cwd = os.getcwd()
    os.chdir(V)
    if V not in sys.path:
        sys.path.insert(0, V)
    builtins.open = shim
    buf = io.StringIO()
    so = sys.stdout
    try:
        sys.stdout = buf
        g = {'__name__': '__main__', '__file__': GEN}
        exec(compile(src, GEN, 'exec'), g)
        err = None
    except BaseException as e:
        err = '%s: %s' % (type(e).__name__, str(e)[:160])
    finally:
        sys.stdout = so
        builtins.open = real_open
        os.chdir(cwd)
    return err, written, buf.getvalue()


if __name__ == '__main__':
    # ---- 0. the patch, as a diff for v4.08 --------------------------------
    src = patched_source()
    d = ''.join(difflib.unified_diff(open(GEN).read().splitlines(True),
                                     src.splitlines(True),
                                     'v4.07/v342_calc.py', 'v4.08/v342_calc.py'))
    open(os.path.join(HERE, 'v342_calc_pbcols_v408.patch'), 'w').write(d)
    print('patch written: %d hunks, %d added lines'
          % (d.count('\n@@'), sum(1 for l in d.splitlines() if l.startswith('+'))))

    # ---- 1. baseline: the UNPATCHED generator, same shim ------------------
    err, w0, _ = run(open(GEN).read(), 'base')
    print('baseline run: %s' % (err or 'ok'))
    assert err is None, err

    # ---- 2. the patched generator ----------------------------------------
    err, w1, log = run(src, 'new')
    print('patched run : %s' % (err or 'ok'))
    assert err is None, err

    # ---- 3. compare the two catalogues -----------------------------------
    A = list(csv.reader(open(w0['per_target_results_v3.99.csv'])))
    B = list(csv.reader(open(w1['per_target_results_v3.99.csv'])))
    print('columns %d -> %d ; rows %d -> %d'
          % (len(A[0]), len(B[0]), len(A) - 1, len(B) - 1))
    assert len(B[0]) == len(A[0]) + 2 and len(A) == len(B)
    assert B[0][-2:] == ['pb_offset_arcsec', 'pb_atten']
    nd = sum(1 for i in range(len(A)) if A[i] != B[i][:len(A[0])])
    print('rows whose PRE-EXISTING columns changed: %d' % nd)
    assert nd == 0

    # ---- 4. NCatCols -----------------------------------------------------
    def ncat(path):
        for l in open(path):
            if '\\NCatCols}' in l:
                return l.strip()
    print('%s  ->  %s' % (ncat(w0['survey_numbers_round12.tex']),
                          ncat(w1['survey_numbers_round12.tex'])))
    assert ncat(w1['survey_numbers_round12.tex']).endswith('{62}')

    # ---- 5. the chain a reader can now run -------------------------------
    hdr = B[0]
    bad, worst = 0, 0.0
    for row in B[1:]:
        r = dict(zip(hdr, row))
        a, rms, smin = float(r['pb_atten']), float(r['rms_mJy']), float(r['smin_mJy'])
        worst = max(worst, abs(5 * rms / a - smin) / smin)
        if abs(5 * rms / a - smin) / smin > 2e-4:
            bad += 1
    print('rows where smin != 5 rms / pb_atten in the emitted csv: %d '
          '(worst residual %.2e)' % (bad, worst))
    assert bad == 0

    # ---- 6. drive the column-count assertion the other way ---------------
    err, _, _ = run(patched_source(ncols_override=61), 'rev')
    print('reverse drive (assert len(COLS)==61): %s' % (err or 'DID NOT FIRE'))
    assert err is not None and 'column count moved to 62' in err, err
    print('\nITEM 2 OK: two columns added, NCatCols 60 -> 62, nothing else moves, '
          'assertion driven both ways')
    shutil.rmtree(OUTDIR, ignore_errors=True)
