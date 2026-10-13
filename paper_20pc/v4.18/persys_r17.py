#!/usr/bin/env python3
r"""The per-system sensitivity table: one row per system of the carrier
search, carrying that system's best window.

WHY IT EXISTS.  The paper states that every limit it quotes is the
EIRP_90 of its own window, and then shows the distribution of those limits
only as a cumulative curve.  A curve cannot be read back: a reader who wants
the limit on one named system cannot get it from the paper at all.  So the
limits are tabulated, system by system, together with the three things that
decide what each limit means -- where in frequency it was obtained, over how
wide a channel, and whether the archive could ever have confirmed a crossing
at that system.

EVERY NUMBER IS A REDUCTION OF THE RELEASED CATALOGUE AND NOTHING ELSE.
There is no new measurement here.  The adopted per-window EIRP_90 is formed
by `adopted_e90.per_window`, which is the one place in the build that forms
it, and the printed value is additionally required to equal the catalogue's
own `eirp_p90_adopted_W` column for the same window -- joined on the
window's POSITION (block, both edges, channel width) and not on any name.

THE SIX ASSERTIONS, AND WHY EACH ONE CAN FAIL.
  P1  every printed limit equals `adopted_e90.per_window` for that row to
      machine precision, and equals the catalogue's own adopted column.
      Drives: perturb one catalogue cell.
  P2  the number of rows equals the published system count \NSysClassA, and
      the set of systems is exactly the set the catalogue's Class A rows
      define.  A table that quietly tabulated 59 of 60 systems would look
      perfectly well-formed.
  P3  the printed limit of each system is the MINIMUM over that system's
      Class A windows -- stated as "no window of this system has a smaller
      adopted value" rather than as a recomputation of the same expression,
      so a reduction over the wrong column cannot satisfy it.
  P4  the median of the printed limits reproduces the published
      \EirpNinetySysMedA, to the precision that macro is printed at.
  P5  the median covered bandwidth reproduces the published \SysUnionAMed,
      and the per-system unions are computed by the interval merge, so a
      system whose windows overlap cannot be credited twice.
  P6  the confirmability column reproduces the published \RcConfSysDay,
      \RcConfSysYr and \RcNoRepSys exactly, and the two confirmable sets are
      nested, so no system can be counted in both columns.

  python3 persys_r17.py             # write the table and the macros
  python3 persys_r17.py --selftest  # drive every assertion to fail
"""
import collections
import os
import re
import subprocess
import sys

import adopted_e90
import epochs_r14 as ep
import star_alias

HERE = os.path.dirname(os.path.abspath(__file__))
os.chdir(HERE)

TAB = 'tab_persys_r17.tex'
#: the exponent the limits are printed in units of
UNIT_EXP = 14

#: SIMBAD catalogue markers that are not part of a designation.  Handled
#: MECHANICALLY and not as a table of star names: a hand table fires on
#: every object the catalogue adds and fails by omission, which is the
#: defect `star_alias.designation` already documents for the "NAME "
#: marker.  "V star" is the export's rendering of SIMBAD's "V*".
_MARKER = re.compile(r'^(?:NAME|V\s*star|V\*|\*\*|\*)\s+')


def designation(name):
    """The printable designation, catalogue markers stripped.

    `star_alias.designation` strips the "NAME " marker and not the variable
    star marker "V*", because no table in the paper has had to print one
    before.  Stripping it here would be a second implementation, so the
    marker is removed from the input and the OUTPUT is then tested for
    shape.

    ★ THE POST-CONDITION IS DELIBERATELY NOT `_MARKER` AGAIN.  Testing the
    output with the same expression that stripped the input is circular: a
    marker the stripper does not know about passes both ways, which is
    exactly the case that matters.  So the condition is on the shape of a
    designation instead -- it begins with a letter or a digit, or with the
    maths escape a Bayer letter needs, and it does not begin with a
    catalogue word.  A marker the stripper misses fails that whatever it is.
    """
    out = star_alias.designation(_MARKER.sub('', str(name)))
    bad = (not out or not (out[0].isalnum() or out[0] == '$')
           or out.upper().split(' ')[0] in ('NAME', 'V', 'V*', 'VSTAR'))
    assert not bad, (
        'designation(%r) would print %r, which still carries a catalogue '
        'marker rather than an object name' % (name, out))
    return out


def wkey(r):
    """A released row's key: block, both edges as min/max, channel width, and
    the row's own star label.

    min/max because a descending spectral window writes its edges reversed,
    which is this project's standing window-key defect.

    ★ THE STAR LABEL IS NECESSARY AND IT IS NOT A NAME JOIN -- the same
    reasoning `adopted_e90.smear_key` records.  Block and window alone
    resolve only 1,616 of the released rows: 31 windows are shared by two
    components of one binary observed in a single block, and the components
    are at different distances, so a position-only key gives one of them the
    other's limit.  Found by this assertion firing on AT Mic AB, where the
    two values differ by 4 per cent.  Both sides of the join are the SAME
    released file, so the label is that file's own row identifier and not a
    name matched across sources, and the key count is asserted against the
    row count below.
    """
    a, b = float(r['flo_GHz']), float(r['fhi_GHz'])
    return (r['eb'], round(min(a, b), 6), round(max(a, b), 6),
            round(float(r['chanw_Hz']), 3), r['star_name'])


def union_ghz(rows):
    """Merged frequency coverage of a set of windows, in GHz.

    The same interval merge `v381_calc.py` publishes \\SysUnionAMed from, so
    a system observed twice at one frequency is credited once.
    """
    iv = sorted((min(float(r['flo_GHz']), float(r['fhi_GHz'])),
                 max(float(r['flo_GHz']), float(r['fhi_GHz'])))
                for r in rows)
    tot, lo, hi = 0.0, None, None
    for a, b in iv:
        if lo is None:
            lo, hi = a, b
        elif a <= hi:
            hi = max(hi, b)
        else:
            tot += hi - lo
            lo, hi = a, b
    return tot + (hi - lo if lo is not None else 0.0)


def confirmable(rows, sep):
    """True where two blocks more than `sep` days apart cover one frequency.

    The construction `cover_v412.py` publishes \\RcConfSysDay from: a common
    frequency interval, covered by two blocks that can be SHOWN to be more
    than `sep` days apart.  The predicate is one-sided -- it can show two
    blocks separated and can never show two simultaneous -- so a count of
    confirmable systems is a lower bound and the caption says so.
    """
    iv = [(min(float(r['flo_GHz']), float(r['fhi_GHz'])),
           max(float(r['flo_GHz']), float(r['fhi_GHz'])), r['eb'])
          for r in rows]
    pts = sorted({x for a, b, _ in iv for x in (a, b)})
    for i in range(len(pts) - 1):
        mid = 0.5 * (pts[i] + pts[i + 1])
        if ep.separated([e for a, b, e in iv if a <= mid <= b], sep):
            return True
    return False


def texval(name, catdir=HERE):
    """A published macro's value, in the manuscript's own \\input order."""
    return adopted_e90._texval(name, catdir)


def two_sf(x):
    """Two significant figures, no exponent, halves rounded up.

    The paper's own convention for a limit is two significant figures, so
    that is what the table prints: 0.87, 1.0, 13, 370.  `%.2g` is not it --
    it drops the trailing zero of 1.04 and prints `1` -- and `%.0f` rounds
    halves to even, so 12.5 would print 12 in one place and 13 in another.
    """
    import decimal
    if x == 0:
        return '0'
    d = decimal.Decimal(repr(float(x)))
    exp = d.adjusted()                      # floor(log10(|x|))
    q = decimal.Decimal(1).scaleb(exp - 1)  # the place of the 2nd figure
    v = d.quantize(q, rounding=decimal.ROUND_HALF_UP)
    return ('%.*f' % (max(0, 1 - exp), v))


def chanw_kHz(hz):
    k = float(hz) / 1e3
    return '%.0f' % k if k >= 100 else '%.1f' % k


# ---------------------------------------------------------------------------
def build(catdir=HERE, rows=None):
    """Everything the table and the macros need, computed once."""
    R = rows if rows is not None else adopted_e90.catalogue(catdir)
    E = adopted_e90.per_window(R, catdir)

    # P1a the catalogue's own adopted column, joined on POSITION.  Both
    #     sides are the same released file, so the join is an identity on
    #     its own rows and the count is asserted.
    col = {}
    for r in R:
        col.setdefault(wkey(r), []).append(float(r['eirp_p90_adopted_W']))
    assert sum(len(v) for v in col.values()) == len(R), 'lost rows in the join'
    assert len(col) == len(R), (
        '%d keys for %d released rows: the window key is not unique and some '
        'row would be given another row value' % (len(col), len(R)))

    A = [r for r in R if r['search_class'] == 'A']
    # P1 EVERY Class A window, not only the sixty that get printed.  The
    #    first form of this clause tested the printed row alone, which left
    #    342 of the 402 windows outside it -- and its own drive, which
    #    perturbed an arbitrary row, duly did not fire.  A clause that holds
    #    on a sixtieth of the population is not the identity it claims.
    #    ★ IT IS AN ORDERING CONSTRAINT AS WELL AS AN IDENTITY, and it has
    #    already fired as one: a correction term added to `adopted_e90` makes
    #    the module and the released column disagree until the catalogue is
    #    rebuilt, and tabulating one of them while the paper's other
    #    statistics come from the other is exactly what this clause exists to
    #    stop.  So this generator runs after the catalogue, and refuses if it
    #    has not.
    for r in A:
        v = col[wkey(r)][0]
        assert abs(v / E[id(r)] - 1.0) < 1e-9, (
            'window %s of %s is not the catalogue value for its own window: '
            '%.6e against %.6e.  Either a term has been added to adopted_e90 '
            'since the catalogue was built, in which case rebuild the '
            'catalogue first, or the two have genuinely parted company.'
            % (r['eb'], r['system_id'], E[id(r)], v))
    bysys = collections.defaultdict(list)
    for r in A:
        bysys[r['system_id']].append(r)

    out = []
    for sid, rr in bysys.items():
        bw = min(rr, key=lambda r: E[id(r)])
        e = E[id(bw)]
        # P1 the printed value is the catalogue's own value for this window.
        #    A window shared by two components of one binary appears twice in
        #    the catalogue with the same adopted value, so the comparison is
        #    against every value the position carries.
        for v in col[wkey(bw)]:
            assert abs(v / e - 1.0) < 1e-9, (
                'the printed EIRP_90 for %s is not the catalogue value for '
                'its own window: %.6e against %.6e' % (sid, e, v))
        # P3 no window of this system has a smaller adopted value.  Stated as
        #    a minimality condition over the system's own rows rather than as
        #    the same min() again.
        assert not [q for q in rr if E[id(q)] < e * (1.0 - 1e-12)], (
            'the row printed for %s is not that system best window' % sid)
        out.append(dict(
            sid=sid,
            name=designation(sid),
            e90=e,
            freq=0.5 * (float(bw['flo_GHz']) + float(bw['fhi_GHz'])),
            chanw=float(bw['chanw_Hz']),
            band=bw['band'],
            union=union_ghz(rr),
            conf_d=confirmable(rr, 1.0),
            conf_y=confirmable(rr, 365.0),
        ))
    out.sort(key=lambda d: d['e90'])
    return out, R, E


def checks(sysrows, R, E):
    """The published identities this table has to close on.

    ★ IT EMITS NO MACRO AT ALL, AND THAT IS THE POINT.  Every number the
    caption needs -- the system count, the adopted multiplier, the channel
    range, the median coverage, the three confirmability counts and the span
    of the limits -- is already published by the generator that owns it.  A
    second macro carrying the same quantity under a new name is how two
    numbers for one thing get into a paper, which is the defect `twinmacro`
    exists for.  So this function reads those macros and requires the table
    to agree with them, and the only values it introduces are the table's
    own cells, written by the generator rather than typed.
    """
    n = len(sysrows)
    # P2 the row count and the system SET are the catalogue's own.
    nsys = int(texval('NSysClassA'))
    assert n == nsys, ('%d rows against the published \\NSysClassA = %d'
                       % (n, nsys))
    assert {d['sid'] for d in sysrows} == {r['system_id'] for r in R
                                           if r['search_class'] == 'A'}, (
        'the tabulated systems are not the Class A systems of the catalogue')
    # P4 the median and the two extremes of the printed limits are the three
    #    the paper already publishes, each to the two figures it prints them
    #    at.  So the table cannot carry a different distribution from the
    #    sentences about it.
    vals = sorted(d['e90'] for d in sysrows)
    for nm, got in (('EirpNinetySysMedA', vals[len(vals) // 2]),
                    ('EirpNinetySysLoA', vals[0]),
                    ('EirpNinetySysHiA', vals[-1])):
        pub = texval(nm)
        m = re.match(r'([0-9.]+)\s*\\times\s*10\^\{?(-?\d+)\}?', pub or '')
        assert m, 'cannot read \\%s = %r' % (nm, pub)
        pubv = float(m.group(1)) * 10.0 ** int(m.group(2))
        assert abs(got / pubv - 1.0) < 0.05, (
            'the tabulated limits give %.4e for \\%s where the paper '
            'publishes %.4e' % (got, nm, pubv))
    # P5 the median covered bandwidth is the published one.
    u = sorted(d['union'] for d in sysrows)
    umed = u[len(u) // 2]
    upub = float(texval('SysUnionAMed'))
    assert abs(umed - upub) < 0.005, (
        'the median covered bandwidth is %.4f GHz against the published %.4f'
        % (umed, upub))
    # P6 the confirmability column is the published partition, and nested.
    nd = sum(1 for d in sysrows if d['conf_d'])
    ny = sum(1 for d in sysrows if d['conf_y'])
    assert not [d for d in sysrows if d['conf_y'] and not d['conf_d']], (
        'a system confirmable over a year but not over a day would be '
        'counted in both columns of the caption')
    for nm, got in (('RcConfSysDay', nd), ('RcConfSysYr', ny),
                    ('RcNoRepSys', n - nd)):
        want = int(texval(nm))
        assert got == want, ('the table gives %d for \\%s where the paper '
                             'publishes %d' % (got, nm, want))

    # P7 the channel widths the caption quotes are the published Class A
    #    range, and every printed width lies inside it, so the caption
    #    cannot describe a range the table leaves.
    lo, hi = float(texval('ChanLoA')), float(texval('ChanHiA'))
    for d in sysrows:
        k = d['chanw'] / 1e3
        assert lo * 0.99 <= k <= hi * 1.01, (
            '%s best window is %.2f kHz, outside the published '
            '%.1f--%.0f kHz' % (d['name'], k, lo, hi))
    return dict(n=n, nconf_d=nd, nconf_y=ny,
                lo=vals[0], med=vals[len(vals) // 2], hi=vals[-1],
                umed=umed)


_CONF = {(True, True): r'yr', (True, False): r'd', (False, False): '--'}


def cell(d):
    return ' & '.join((
        d['name'],
        two_sf(d['e90'] / 10.0 ** UNIT_EXP),
        '%.2f' % d['freq'],
        chanw_kHz(d['chanw']),
        two_sf(d['union']),
        _CONF[(d['conf_d'], d['conf_y'])]))


def write_table(sysrows, out=TAB):
    """Two systems per printed row, so 60 systems cost 30 lines of table."""
    rows = sorted(sysrows, key=lambda d: d['e90'])
    half = (len(rows) + 1) // 2
    left, right = rows[:half], rows[half:]
    blank = ' & '.join([''] * 6)
    lines = ['%% GENERATED by persys_r17.py -- do not hand-edit.',
             '%% One row per system of the carrier search, two systems per '
             'printed line,',
             '%% ordered by the limit.  Every value is computed from the '
             'per-window results.',
             r'\begin{tabular}{@{}l@{\hspace{5pt}}r@{\hspace{5pt}}'
             r'r@{\hspace{5pt}}r@{\hspace{5pt}}r@{\hspace{5pt}}c@{'
             r'\hspace{12pt}}l@{\hspace{5pt}}r@{\hspace{5pt}}'
             r'r@{\hspace{5pt}}r@{\hspace{5pt}}r@{\hspace{5pt}}c@{}}',
             r'\hline']
    head = (r'System & $\mathrm{EIRP}_{90}$ & $\nu$ & $\Delta\nu$ & '
            r'$\Delta\nu_{\rm cov}$ & conf.')
    unit = (r' & ($10^{%d}$\,W) & (GHz) & (kHz) & (GHz) & ' % UNIT_EXP)
    lines += [head + ' & ' + head + r' \\',
              unit + ' & ' + unit + r' \\',
              r'\hline']
    for i in range(half):
        a = cell(left[i])
        b = cell(right[i]) if i < len(right) else blank
        lines.append('%s & %s \\\\' % (a, b))
    lines += [r'\hline', r'\end{tabular}']
    with open(out, 'w') as fh:
        fh.write('\n'.join(lines) + '\n')
    return out


def main(outdir=None):
    sysrows, R, E = build()
    checks(sysrows, R, E)
    t = write_table(sysrows,
                    os.path.join(outdir, TAB) if outdir else TAB)
    print('persys_r17: %d systems -> %s' % (len(sysrows), t))
    print('  deepest %s at %s e%d W, shallowest %s at %s e%d W'
          % (sysrows[0]['name'], two_sf(sysrows[0]['e90'] / 10.0 ** UNIT_EXP),
             UNIT_EXP, sysrows[-1]['name'],
             two_sf(sysrows[-1]['e90'] / 10.0 ** UNIT_EXP), UNIT_EXP))
    nd = sum(1 for d in sysrows if d['conf_d'])
    ny = sum(1 for d in sysrows if d['conf_y'])
    print('  confirmable over a day %d, over a year %d, never %d'
          % (nd, ny, len(sysrows) - nd))


# ---------------------------------------------------------------------------
def _selftest():
    """Drive every assertion to fail on its own.

    Each drive perturbs ONE input in the direction the defect would actually
    take, in a scratch copy of the catalogue, and requires a refusal.  A
    drive writes `*_drive.csv`, never a path production reads.
    """
    fails = []

    def drive(name, mutate, expect):
        rows = [dict(r) for r in adopted_e90.catalogue()]
        mutate(rows)
        try:
            sysrows, R, E = build(rows=rows)
            checks(sysrows, R, E)
        except AssertionError as exc:
            ok = expect in str(exc)
            print('  drive %-44s %s' % (name, 'FIRES' if ok else
                                        'fired on the wrong clause: %s' % exc))
            if not ok:
                fails.append(name)
            return
        print('  drive %-44s DID NOT FIRE' % name)
        fails.append(name)

    def _firstA(rows):
        return next(r for r in rows if r['search_class'] == 'A')

    # P1 the catalogue's adopted column no longer matches the module.
    drive('P1 catalogue adopted column perturbed',
          lambda rows: _firstA(rows).__setitem__(
              'eirp_p90_adopted_W',
              '%.9e' % (1.3 * float(_firstA(rows)['eirp_p90_adopted_W']))),
          'not the catalogue value')

    # P2 a system dropped from the table.
    def _dropsys(rows):
        sid = _firstA(rows)['system_id']
        keep = [r for r in rows if not (r['search_class'] == 'A'
                                        and r['system_id'] == sid)]
        rows[:] = keep
    drive('P2 one Class A system removed', _dropsys,
          'against the published')

    # P4 the median moved away from the published one.
    drive('P4 every Class A limit scaled by 3',
          lambda rows: [r.__setitem__('eirp_nominal_W',
                                      '%.9e' % (3 * float(r['eirp_nominal_W'])))
                        for r in rows if r['search_class'] == 'A'],
          'not the catalogue value')

    # P5/P6 need the reduction to stay self-consistent, so they are driven
    # on the published macros rather than on the catalogue: a scratch copy of
    # this module with one published value changed must refuse.
    for name, old, new, expect in (
            ('P5 published median bandwidth changed',
             "upub = float(texval('SysUnionAMed'))", 'upub = 3.0',
             'median covered bandwidth'),
            ('P6 published confirmable count changed',
             "want = int(texval(nm))", 'want = 99',
             'where the paper publishes'),
            ('P2 published system count changed',
             "nsys = int(texval('NSysClassA'))", 'nsys = 59',
             'against the published'),
            # ★ P3 CANNOT BE DRIVEN FROM THE DATA.  Making one window deeper
            #   moves the module's value and not the catalogue column, so P1
            #   refuses first and the minimality clause is never reached.
            #   The defect it guards against is a reduction over the wrong
            #   end of the distribution, so that is what is perturbed.
            ('P3 the reduction takes the worst window',
             "bw = min(rr, key=lambda r: E[id(r)])",
             "bw = max(rr, key=lambda r: E[id(r)])",
             'not that system best window'),
            ('P7 published channel range narrowed',
             "lo, hi = float(texval('ChanLoA')), float(texval('ChanHiA'))",
             'lo, hi = 400.0, 600.0',
             'outside the published')):
        src = open(os.path.join(HERE, os.path.basename(__file__))).read()
        assert old in src, 'drive %s: perturbation site not found' % name
        tmp = os.path.join(HERE, '.persys_drive.py')
        open(tmp, 'w').write(src.replace(old, new))
        r = subprocess.run([sys.executable, tmp], cwd=HERE,
                           capture_output=True, text=True,
                           env=dict(os.environ, PERSYS_DRIVE='1'))
        os.remove(tmp)
        got = (r.stdout + r.stderr)
        ok = r.returncode != 0 and expect in got
        print('  drive %-44s %s' % (name, 'FIRES' if ok else
                                    'DID NOT FIRE (%s)' % got.strip()[-120:]))
        if not ok:
            fails.append(name)

    # The marker guard, driven the way it would actually be defeated: the
    # stripper does not know the marker.  Teach it one marker fewer and the
    # real catalogue name `V star TX PsA` must be refused rather than
    # printed.
    global _MARKER
    _keep = _MARKER
    try:
        _MARKER = re.compile(r'^(?:NAME|\*\*|\*)\s+')
        try:
            got = designation('V star TX PsA')
            print('  drive %-44s DID NOT FIRE (printed %r)'
                  % ('marker the stripper does not know', got))
            fails.append('marker')
        except AssertionError:
            print('  drive %-44s FIRES' % 'marker the stripper does not know')
    finally:
        _MARKER = _keep

    print('persys_r17 selftest: %d drive(s) failed to fire' % len(fails))
    return 1 if fails else 0


if __name__ == '__main__':
    if '--selftest' in sys.argv:
        sys.exit(_selftest())
    if '--out' in sys.argv:
        # fragstale S3: reproduce the fragment into a scratch directory and
        # write NOTHING in the build root.
        main(outdir=sys.argv[sys.argv.index('--out') + 1])
        sys.exit(0)
    if os.environ.get('PERSYS_DRIVE'):
        # a driven copy must not write a path production reads
        sysrows, R, E = build()
        checks(sysrows, R, E)
        print('persys_r17 drive: no refusal')
        sys.exit(0)
    main()
