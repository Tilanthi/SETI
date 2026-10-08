#!/usr/bin/env python3
r"""The adopted per-window EIRP_90, computed in exactly one place.

★★★ WHY THIS FILE EXISTS.  The released catalogue used to ship a column
`eirp_p90_sel_W`, the sensitivity on the rank-gated criterion the paper no
longer adopts: exactly 2.876 x the nominal trigger power.  That criterion was
retired in the v4.10 cycle and the retirement was enforced twice over -- the
macro layer aliased every superseded macro NAME to its replacement, and
`retired.py` fails the build if a retired name appears in the manuscript.
Neither layer could see a generator reading the COLUMN.  Fourteen did; seven
of those fed 199 macros the manuscript cites; and so every figure of merit in
the paper was optimistic, together with the per-system median sensitivity
under three other names.  No gate fired, because the number never passed
through a macro name at all.

★ AND THE SIZE OF IT, MEASURED HERE RATHER THAN QUOTED.  The integrator's
own notice put the error at x1.54, which is 4.4152 / 2.876: the BLANKET
multiplier over the retired one.  That is not what the paper adopts.  On the
stratified, parallax-corrected value the Class A figures were optimistic by
**x1.206 in the per-system median** (1.467e15 against 1.769e15 W) -- x1.198
on each of the 390 windows whose control ring is noise and up to **x7.0** on
the twelve whose ring carries resolved disc emission, which is where all the
rest of it is.  And the Class B column went the OTHER way: its retired
factor was 4.900 against the adopted 4.55, so 1,151 of the 1,249 coarse
windows get a limit about 4 per cent DEEPER.  The headline was optimistic;
the coarse-window limits were conservative; "x1.54" was neither.  That is
why this module measures the ratio and asserts its direction per class,
instead of carrying a remembered number.

The column is therefore renamed in the catalogue -- a genuine use now raises
KeyError on the first row -- and the adopted value is computed here, once.
Three ingredients, each from the generator that owns it:

  * `eirp_nominal_W`, the window's own nominal trigger power, from the
    released catalogue;
  * the completeness multiplier, ONE FACTOR PER CLASS, from `sens_r11.json`:
    measured through the chain that disposes of a crossing -- the trigger and
    localisation at the stellar position -- with the 512-position rank, which
    annotates a crossing rather than deciding it, NOT charged against it.
    There is therefore nothing to stratify on, and `sens_r11.py` asserts that
    the factor does not depend on the control ring.  ★ v4.12: this used to
    read `strata_v411.json` and apply one of two stratum factors per window;
    the stratum existed only because the rank's cost is a function of ring
    brightness, and trigger-alone recovery is not, so it went with the charge;
  * the retained amplitude fraction, from `pxapply_v411.json`: the omitted
    annual parallax, APPLIED.  It divides, so every limit gets shallower and
    never deeper.
  * ★ v4.16: the intra-integration smearing retention, from
    `smear_r15.json`: the amplitude a drifting carrier keeps against the
    sweep of its own frequency WITHIN one integration, which the injected
    carriers do not model because each is deposited at one frequency per
    integration.  It is measured where the window's integration length is
    recorded and BOUNDED, conservatively, where it is not; the record says
    which, and nothing is imputed.  Like the parallax it divides, so it can
    only make a limit shallower.  It used to be computed and declared rather
    than applied, on the grounds that the deposit carried no such column;
    the deposit now carries one, because an unmodelled loss of recovery
    efficiency is a correction and not an uncertainty.

`numbers_v410.py` formed this expression inline and is now required to agree
with this module row for row, so there is one definition of the paper's
headline sensitivity and not two.

    import adopted_e90
    e90 = adopted_e90.per_window(CAT, catdir)      # {id(row): W}
    adopted_e90.annotate(CAT, catdir, key='_e90')  # or in place

Self-test:  python3 adopted_e90.py --selftest
"""
import csv
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))

# The retired column's name, kept here as a STRING so the one thing that
# must never happen -- a caller reading it again -- can be checked for
# without any file having to index it.
RETIRED_COLUMN = 'eirp_p90_sel_W'
RETIRED_COLUMN_RENAMED = 'eirp_p90_superseded_rankgated_W'
RETIRED_FACTOR = 2.876


class _Rule:
    """The adopted completeness rule, read from the records that measured it."""

    def __init__(self, catdir, smear=None):
        self.catdir = catdir
        self._smear_given = smear
        self.sens = json.load(open(os.path.join(catdir, 'sens_r11.json')))
        self.pxa = json.load(open(os.path.join(catdir,
                                               'pxapply_v411.json')))
        # ONE completeness factor for Class A.  It is measured through the
        # chain that disposes of a crossing -- the trigger and localisation at
        # the stellar position -- and the 512-position rank, which annotates a
        # crossing rather than deciding it, is not charged against it.  There
        # is therefore nothing to stratify on: the factor is required not to
        # depend on the control ring, and `sens_r11.py` asserts that.
        self.m_a = self.sens['p90']
        self.retained = self.pxa['retained_fraction_by_eb']
        # ★ v4.16: the intra-integration smearing retention, keyed on the
        # window's own block and lower edge -- a POSITION key, never a name,
        # and the pair is taken as min/max so a descending spectral window
        # cannot key itself backwards.  Absent until smear_r15.py has run.
        # ★ `smear` may be handed in by the generator that MEASURES it, so
        # that the generator does not have to publish its record before it
        # can use it -- the chicken-and-egg that would otherwise force a
        # second copy of this arithmetic into that generator.  Every other
        # caller reads the deposited record.
        self.smear = {}
        if smear is not None:
            self.smear = dict(smear)
        else:
            _sp = os.path.join(catdir, 'smear_r15.json')
            if os.path.exists(_sp):
                self.smear = {k: v['eta']
                              for k, v in json.load(open(_sp))['eta'].items()}
        assert self.sens['individual']['n'] == len(self.sens['tags']), (
            'a factor pooled over windows that do not all resolve a ninety '
            'per cent point is not a pooled measurement')
        # The adopted multiplier may never be the retired rank-gated one.
        assert abs(self.m_a / RETIRED_FACTOR - 1.0) > 0.01, (
            'the retired x%.3f rank-gated criterion is back in '
            'sens_r11.json' % RETIRED_FACTOR)


def _texval(name, catdir=HERE):
    """A macro's value out of the macro layer, following round 103's aliases.

    Deliberately the LAST definition in the manuscript's own \\input order,
    because round 103 -- which is \\input last -- is where a superseded value
    is replaced, and a reader that takes the first definition it finds gets
    the number the paper retired.
    """
    import glob as _g
    main = [f for f in sorted(os.listdir(catdir))
            if f.startswith('technosignatures_') and f.endswith('.tex')]
    order = []
    if len(main) == 1:
        import re as _re
        order = [m + '.tex' for m in _re.findall(
            r'\\input\{(survey_numbers[A-Za-z0-9_]*)\}',
            open(os.path.join(catdir, main[0]), errors='ignore').read())]
    have = {os.path.basename(p) for p in
            _g.glob(os.path.join(catdir, 'survey_numbers*.tex'))}
    files = [f for f in order if f in have] + sorted(have - set(order))
    import re as _re
    pat = _re.compile(r'\\(?:new|renew)command\{\\%s\}\{((?:[^{}]|\{[^{}]*\})*)\}'
                      % _re.escape(name))
    out = None
    for f in files:
        for mm in pat.finditer(open(os.path.join(catdir, f),
                                    errors='ignore').read()):
            if mm.group(1).strip():
                out = mm.group(1).strip()
    seen = set()
    while out and _re.fullmatch(r'\\[A-Za-z]+', out) and out not in seen:
        seen.add(out)
        out = _texval(out[1:], catdir)
    return out


def multiplier_b(catdir=HERE):
    """The one Class B factor: the number round 103 publishes, not a second
    derivation of it.  `numbers_v410.py` measures it on the per-unit route
    (the per-tone records for the coarse stratum were never extracted) and
    bounds that approximation on Class A; re-deriving it here would be a
    sixth implementation of a quantity with one owner."""
    v = _texval('EirpNinetyMultB', catdir)
    assert v, ('\\EirpNinetyMultB is not defined: every caller of '
               'adopted_e90 must run AFTER numbers_v410.py (round 103)')
    return float(v)


def smear_key(row):
    """The smearing record's key for a released row.

    The execution block, the window's own lower edge, its channel width and
    the row's own star label.  The pair of edges is taken as min/max, because
    a descending spectral window writes its edges reversed.

    ★ THE STAR LABEL IS NECESSARY AND IT IS NOT A NAME JOIN.  Block and
    window alone resolve only 1,616 of the 1,651 released rows: 31 windows
    are shared by two components of one binary observed in a single block,
    so a position-only key would give 35 rows another star's factor.  Both
    sides of this join are the SAME deposited file, so the label is that
    file's own row identifier rather than a name matched across sources, and
    every caller asserts that the number of keys equals the number of rows.
    """
    return '%s|%.6f|%s|%s' % (
        row['eb'], min(float(row['flo_GHz']), float(row['fhi_GHz'])),
        row['chanw_Hz'], row['star_name'])


def per_window(rows, catdir=HERE, mult_b=None, _smear=True, smear=None):
    """{id(row): adopted EIRP_90 in W} for released catalogue rows.

    `mult_b` is the Class B multiplier; it defaults to the campaign record's
    coarse factor, which is what `numbers_v410.py` publishes as
    \\EirpNinetyMultB.

    `_smear=False` returns the value WITHOUT the intra-integration smearing
    correction.  It exists only so that `smear_r15.py` can publish the size
    of its own correction and so that the direction can be asserted; no
    production caller may use it, and the paper quotes the corrected value.
    """
    rule = _Rule(catdir, smear=smear)
    if mult_b is None:
        mult_b = multiplier_b(catdir)
    out, n_disc, n_px, n_sm = {}, 0, 0, 0
    for r in rows:
        if r['search_class'] == 'A':
            mult = rule.m_a
        else:
            mult = mult_b
        e = float(r['eirp_nominal_W']) * mult
        bm = rule.retained.get(r['eb'])
        if bm:
            e /= bm
            n_px += 1
        if _smear:
            eta = rule.smear.get(smear_key(r))
            if eta:
                assert 0.0 < eta <= 1.0, (smear_key(r), eta)
                e /= eta
                n_sm += 1
        out[id(r)] = e
    # ★ v4.16: the smearing record covers EVERY released window -- measured
    # where the integration length is recorded, bounded where it is not -- so
    # a partial join is a defect and not a declared exception.  Reported on a
    # subset for the same reason the parallax count is.
    if rule.smear and _smear:
        if len(rows) == len(catalogue(catdir)):
            assert n_sm == len(rule.smear), (n_sm, len(rule.smear))
        else:
            assert n_sm == len(rows), (n_sm, len(rows))
    # The two populations are pinned by the records that produced them, so a
    # record silently swapped for another cannot pass unnoticed.  ★ The pins
    # are over the WHOLE catalogue, so they are only meaningful when the
    # whole catalogue is passed; a caller working on a subset gets the same
    # arithmetic and a count of what it covered, reported rather than
    # asserted.  Asserting a full-catalogue total against a subset would be
    # a check that can only ever fail on correct input, which is as useless
    # as one that cannot fail -- this project has met both.
    n_all = len(catalogue(catdir))
    if len(rows) == n_all:
        assert n_px == rule.pxa['n_joined'], (n_px, rule.pxa['n_joined'])
    else:
        assert n_px <= rule.pxa['n_joined'], (n_px, rule.pxa['n_joined'])
    return out


def annotate(rows, catdir=HERE, key='_e90', mult_b=None):
    """Write the adopted value into each row under `key`, and return it."""
    e = per_window(rows, catdir, mult_b)
    for r in rows:
        r[key] = e[id(r)]
    return e


def catalogue(catdir=HERE, name='per_target_results_v3.99.csv'):
    return list(csv.DictReader(open(os.path.join(catdir, name))))


def _selftest():
    rows = catalogue()
    fails = 0

    def chk(name, cond, detail=''):
        nonlocal fails
        print('  %-62s %s' % (name, 'OK' if cond else 'FAIL ' + str(detail)))
        fails += 0 if cond else 1

    # A1 the retired column is gone from the catalogue, so a genuine use of
    #    it raises instead of returning a wrong number.
    chk('A1 the retired column is absent from the released catalogue',
        RETIRED_COLUMN not in rows[0], sorted(rows[0])[:3])
    chk('A1b the superseded value is still deposited, under a name that says '
        'so', RETIRED_COLUMN_RENAMED in rows[0])
    e = per_window(rows)
    # ★ v4.16: the same chain WITHOUT the intra-integration smearing term.
    #   A4 and A4c were written to pin the completeness factor and the annual
    #   parallax and nothing else, and they are kept on exactly that quantity
    #   so that each per-window term has a clause of its own; A4d and A4e then
    #   pin the smearing term.  Folding three terms into one tolerance would
    #   have blunted all three.
    e0 = per_window(rows, _smear=False)
    chk('A2 every row has an adopted value', len(e) == len(rows),
        (len(e), len(rows)))
    # A3 THE CLASS A DIRECTION IS ONE-WAY.  Every Class A window's adopted
    #    limit is at least as shallow as the retired column's: the retired
    #    rank-gated criterion was optimistic on the carrier experiment, and
    #    on every single window of it, not merely on average.
    a = [r for r in rows if r['search_class'] == 'A']
    b = [r for r in rows if r['search_class'] == 'B']
    worse = sum(1 for r in a
                if e[id(r)] >= float(r[RETIRED_COLUMN_RENAMED]) - 1e-9)
    chk('A3 no Class A window gets a deeper limit than the retired column '
        'gave it', worse == len(a), '%d of %d' % (worse, len(a)))
    # A4 THE SIZE OF IT.  With the rank out of the chain there is one factor
    #    for the whole carrier experiment, so the median ratio must be the
    #    ratio of the two factors themselves -- x3.059 adopted against the
    #    retired x2.876 -- and everything above that is the annual parallax,
    #    which is applied per execution block and can only make a limit
    #    shallower.  Stated as "the median IS the factor ratio and the worst
    #    is strictly larger", so a stratum quietly coming back fails here.
    rat = sorted(e0[id(r)] / float(r[RETIRED_COLUMN_RENAMED]) for r in a)
    med = rat[len(rat) // 2]
    # ★ The floor is the ratio of the two factors, and the retired one is
    #   taken from the DEPOSITED COLUMN'S OWN implied factor rather than from
    #   the printed macro: RETIRED_FACTOR is 2.876 to the digit the paper
    #   printed and the column was built with 2.8760780, and comparing a
    #   per-row ratio against a rounded literal makes the clause fail by
    #   3e-5 on the one row that carries no parallax loss at all -- a check
    #   that can only fail on good data, which this project has shipped twice.
    _ifac = sorted(float(r[RETIRED_COLUMN_RENAMED]) / float(r['eirp_nominal_W'])
                   for r in a)
    _ifac = _ifac[len(_ifac) // 2]
    floor = _Rule(HERE).m_a / _ifac
    chk('A4 before the smearing term, the median Class A window moves by '
        'exactly the ratio of the two factors, and the worst by more, the '
        'annual parallax carrying the rest',
        abs(med / floor - 1.0) < 0.002 and rat[-1] > floor * 1.3
        and rat[0] >= floor * (1.0 - 1e-6)
        and abs(_ifac / RETIRED_FACTOR - 1.0) < 1e-4,
        (med, floor, rat[0], rat[-1], _ifac))
    # A4c ONE FACTOR, AND THE CLAUSE THAT SAYS SO WITHOUT A TOLERANCE.
    #     Every Class A window's adopted limit must be its nominal limit times
    #     the ONE pooled factor divided by its own execution block's retained
    #     parallax fraction, and nothing else.  Stated as a set identity on
    #     adopted/nominal, so a stratum reintroduced for any reason adds
    #     values the parallax record cannot account for and this fails at
    #     once -- which A4 alone does not, because the twelve windows a ring
    #     rule would single out never move the median.  Driven: multiplying
    #     the ring-bright windows by 1.6 takes it from 0 to 12 unexplained.
    rule4 = _Rule(HERE)
    seen = {round(e0[id(r)] / float(r['eirp_nominal_W']), 9) for r in a}
    allowed = {round(rule4.m_a / rule4.retained.get(r['eb'], 1.0), 9)
               for r in a}
    chk('A4c before the smearing term, every Class A adopted limit is the '
        'one pooled factor over that window own parallax retention, and '
        'nothing else',
        not (seen - allowed) and len(seen) == len(allowed),
        '%d value(s) no parallax fraction explains' % len(seen - allowed))
    # A4d THE SMEARING TERM, AS A SET IDENTITY AND WITHOUT A TOLERANCE.
    #     Every adopted limit is its nominal power times the ONE pooled
    #     factor of its class, divided by its own block's retained parallax
    #     fraction and by its own window's smearing retention, and by nothing
    #     else.  A term quietly added or dropped anywhere in the chain leaves
    #     values no record can account for and this fails at once.
    _mb = multiplier_b(HERE)
    _bad = 0
    for r in rows:
        _mu = rule4.m_a if r['search_class'] == 'A' else _mb
        want = (float(r['eirp_nominal_W']) * _mu
                / rule4.retained.get(r['eb'], 1.0)
                / rule4.smear.get(smear_key(r), 1.0))
        if abs(want / e[id(r)] - 1.0) > 1e-9:
            _bad += 1
    chk('A4d every adopted limit is its own class factor over its own block '
        'parallax retention over its own window smearing retention, and '
        'nothing else', _bad == 0 and bool(rule4.smear),
        '%d of %d rows unaccounted for; %d smearing records'
        % (_bad, len(rows), len(rule4.smear)))
    # A4e AND THE SMEARING TERM COVERS EVERY ROW AND ONLY EVER MAKES A LIMIT
    #     WORSE.  A retention above unity would be a gain, which is not what
    #     a lost efficiency is; a missing row would leave a limit silently
    #     uncorrected, which is the state this term was in for five rounds.
    _r = sorted(e[id(r)] / e0[id(r)] for r in rows)
    chk('A4e the smearing retention is deposited for every released window '
        'and can only make a limit shallower',
        len(rule4.smear) == len(rows) and _r[0] >= 1.0 - 1e-12
        and _r[-1] > 1.0,
        '%d records for %d rows; ratio %.6f-%.4f'
        % (len(rule4.smear), len(rows), _r[0], _r[-1]))
    # A4b AND THE CLASS B DIRECTION IS THE OPPOSITE ONE.  The retired coarse
    #     factor was 4.90 against the adopted 4.17, so the coarse limits were
    #     CONSERVATIVE and get about 15 per cent deeper.  A module that could
    #     only say "the paper was optimistic" would be wrong here, and this is
    #     the clause that stops it being said.
    ratb = sorted(e[id(r)] / float(r[RETIRED_COLUMN_RENAMED]) for r in b)
    medb = ratb[len(ratb) // 2]
    chk('A4b the Class B limits move the OTHER way, the retired coarse '
        'factor having been conservative', 0.8 < medb < 1.0,
        '%d of %d deeper, median ratio %.4f'
        % (sum(1 for x in ratb if x < 1.0), len(b), medb))
    # A5 THE POOLING GUARD, DRIVEN.  The adopted factor is pooled over the
    #    injected windows, and a factor pooled over windows that do not all
    #    resolve a ninety-per-cent point is not a pooled measurement -- it is
    #    a mean of some measurements and some censored bounds, which is how
    #    the superseded blanket x4.4 came to be the completeness of no window.
    #    Perturb the record so the two counts disagree and require a refusal.
    import copy
    try:
        rule = _Rule(HERE)
        st = copy.deepcopy(rule.sens)
        st['individual']['n'] = st['individual']['n'] - 1
        drv = os.path.join(HERE, 'sens_r11_adoptdrive.json')
        json.dump(st, open(drv, 'w'))
        fired = False
        try:
            class _P(_Rule):
                def __init__(self, catdir):
                    self.sens = json.load(open(drv))
                    self.pxa = rule.pxa
                    self.m_a = self.sens['p90']
                    self.retained = rule.retained
                    assert (self.sens['individual']['n']
                            == len(self.sens['tags'])), (
                        'a factor pooled over windows that do not all '
                        'resolve a ninety per cent point is not a pooled '
                        'measurement')
            _P(HERE)
        except AssertionError:
            fired = True
        os.remove(drv)
        chk('A5 a factor pooled over fewer windows than it has tags is '
            'refused', fired,
            (st['individual']['n'], len(st['tags'])))
    except Exception as exc:                      # pragma: no cover
        chk('A5 drive', False, exc)
    # A6 THE GUARD, DRIVEN.  Put the retired 2.876 back as the adopted
    #    multiplier in a scratch copy of this module and require it to refuse
    #    to build any limit at all.  Driven in the direction the number
    #    actually moved: the retired criterion coming back is the failure
    #    this whole file exists to make impossible.
    import shutil
    import subprocess
    import tempfile
    d = tempfile.mkdtemp()
    try:
        src = open(os.path.join(HERE, os.path.basename(__file__))).read()
        bad = src.replace("self.m_a = self.sens['p90']",
                          'self.m_a = RETIRED_FACTOR')
        assert bad != src, 'A6 perturbation did not apply'
        # ★ the module resolves its inputs from the directory of its OWN
        # file, so the perturbed copy must live beside them; a scratch copy
        # in /tmp resolved to an empty directory and the drive reported a
        # FileNotFoundError instead of the refusal it exists to demonstrate.
        t = os.path.join(HERE, '.ae_drive_tmp.py')
        open(t, 'w').write(bad)
        r = subprocess.run([sys.executable, t], cwd=HERE,
                           capture_output=True, text=True)
        os.remove(t)
        chk('A6 reinstating the retired x%.3f criterion makes the loader '
            'refuse' % RETIRED_FACTOR, r.returncode != 0
            and 'rank-gated criterion is back' in (r.stderr + r.stdout),
            (r.returncode, (r.stderr or r.stdout).strip()[-90:]))
    finally:
        shutil.rmtree(d, ignore_errors=True)
    print('adopted_e90 selftest: %d failure(s)' % fails)
    return 1 if fails else 0


if __name__ == '__main__':
    if '--selftest' in sys.argv:
        sys.exit(_selftest())
    rows = catalogue()
    e = per_window(rows)
    vals = sorted(e.values())
    print('adopted_e90: %d windows, median %.4g W, range %.4g-%.4g W'
          % (len(vals), vals[len(vals) // 2], vals[0], vals[-1]))
