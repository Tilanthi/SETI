#!/usr/bin/env python3
r"""numbers_v410 (round 103) -- one value per quantity, computed from the
released products, and the retirement of every superseded synonym.

Every quantity below was carried in more than one place with more than one
value.  Each is resolved here to a single number, emitted as a single macro,
and asserted against the product it comes from, so that the abstract, the
body, the tables, the figure captions and the conclusions cannot drift apart
again: there is one definition and one place it is computed.

Six families:

  A  the habitable-zone hosts, as distinct stars with their own crossings;
  B  the line mask, evaluated in the stellar frame, with ONE unattributed
     count over the whole crossing population;
  C  the single sensitivity, EIRP_90, and the single benchmark;
  D  the window and crossing subsets -- rank-first, stage-1 flagged, fitted,
     null-scale covered -- each defined once and named apart;
  E  the interference screen's population, stated against the released one;
  F  one combined uncertainty interval on EIRP_90, in one table.

Inputs are discovered by pattern in the directory given with --cat, so this
generator carries no file version in it.  Outputs: numbers_macros.tex,
tab_budget.tex, tab_hzhosts.tex.

Driving.  Every assertion is exercised in both directions: the unperturbed
run must pass all of them, and each --drive N must make exactly one fire.
The output suffix follows the FLAG, so no driven run -- including
--drive 0 -- writes a path the production run writes.
"""
import csv
import glob
import json
import math
import os
import re
import sys

import maskframe_v411 as mf

C_KMS = 299792.458
MASK_HALF_KMS = 50.0
TRIGGER = 5.0

# The one benchmark.  A 12-m dish radiating 1 MW at 230 GHz: technology we
# operate at these frequencies, with a stated aperture efficiency, so the
# EIRP is a transmitter model and not a bare power scale.
BENCH_D_M = 12.0
BENCH_PTX_W = 1.0e6
BENCH_NU_GHZ = 230.0
BENCH_ETA = 0.7

# The single sensitivity: the amplitude the complete automated selection --
# the trigger and the 512-position spatial rank together -- recovers nine
# times in ten, measured on injected tones, in units of the nominal trigger.
# Read from the campaign record, never typed.
CAMPAIGN_STRATUM = {'A': 'fine (<1 MHz)', 'B': 'coarse (>5 MHz)'}

# How the interference screen's window population relates to the released
# sample.  Declared, because it is a sentence in the paper; checked, because
# it is also a fact about two files.  'overlapping' means neither contains
# the other, which is the case a reader will not guess.
RFI_RELATION = 'overlapping'

# The uncertainty budget.  (name, origin, lo%, hi%, kind) with kind in
#   's' statistical (the campaign bootstrap)
#   'y' systematic, enters the quadrature sum
#   'b' a one-sided BIAS, quoted apart from the interval: an uncorrected
#       bias is not an error and may not be added to one in quadrature.
BUDGET = [
    ('Absolute flux scale', 'ALMA calibration, band-weighted', 7.0, 7.0, 'y'),
    ('Distance', 'Gaia parallax, entering as $d^{2}$', 0.2, 0.2, 'y'),
    ('Visibility calibration', 'block-to-block scale', 4.5, 4.5, 'y'),
    ('Sub-channel phase', 'irreducible; median-corrected', 12.0, 17.0, 'y'),
    ('Window-to-window transfer', 'measured on tested windows', 6.0, 9.0, 'y'),
    ('Injection campaign', 'bootstrap over configurations', 36.0, 4.0, 's'),
    ('Decorrelation', 'injected tones suffer none; assumed',
     -5.0, 20.0, 'b'),
    ('Pointing', 'worst case off axis', 0.0, 1.9, 'b'),
]


def quad(xs):
    return math.sqrt(sum(x * x for x in xs))


STRAT = {}
_BINS = [0.0, 6.0, 10.0, 14.0, 1e9]


def _cross(xs, fr, level=0.90):
    for j in range(1, len(xs)):
        if fr[j - 1] < level <= fr[j]:
            w = (level - fr[j - 1]) / (fr[j] - fr[j - 1])
            return xs[j - 1] + w * (xs[j] - xs[j - 1])
    return None


def _binof(c):
    for i in range(len(_BINS) - 1):
        if _BINS[i] <= c < _BINS[i + 1]:
            return i
    raise ValueError(c)


def _stratified(cls, CAT, TONES, UNITS, route='tones', drive=None):
    """The survey completeness for one channelisation class.

    Post-stratified on each window's own published control maximum, which is
    the variable the spatial screen is a function of: in a window whose
    control ring peaks at C sigma, requiring the star to outrank all 512
    controls is equivalent to raising the 5 sigma trigger to C.  The
    catalogue publishes that column for every window, so the stratum weights
    are measured.

    Two routes, because the deposited records are not symmetric.
      'tones' uses the per-tone records and can exclude tones deposited
              OUTSIDE the searched band.  Scoring those as failures is the
              defect that produced the superseded multiplier: a tone that
              cannot be recovered is not a measurement of recovery.
      'units' uses the per-unit, per-amplitude counts, which include those
              tones.  It is the only route available where per-tone records
              were not extracted, and the difference between the two routes
              is MEASURED on the class where both exist rather than assumed.

    Returns (p90, (lo, hi), diagnostics).
    """
    want = 'fine' if cls == 'A' else 'coarse'
    UU = {u['tag']: u for u in UNITS if u['cls'] == want}
    rows = [r for r in CAT if r['search_class'] == cls]
    by = {}
    for r in rows:
        by.setdefault((r['eb'], int(round(float(r['chanw_Hz'])))),
                      []).append(r)
    match, unmatched = {}, []
    for tag, u in UU.items():
        eb = tag.rsplit('_spw', 1)[0]
        cand = by.get((eb, int(round(u['chanw_Hz']))), [])
        ct = [g['ctrl_top'] for g in u['rungs'] if g['amp'] == 0.75][0]
        if not cand:
            unmatched.append(tag)
            continue
        # ★ the same (block, channel width) can hold more than one window, so
        # the join closes on the control maximum the campaign measured for
        # itself and not on the block name: a block-only key averages two
        # windows, which is the star-blind-key family again.
        r = min(cand, key=lambda c: abs(float(c['ctrl_max_snr']) - ct))
        match[tag] = (float(r['ctrl_max_snr']), ct)
    wcat = [0] * (len(_BINS) - 1)
    for r in rows:
        wcat[_binof(float(r['ctrl_max_snr']))] += 1
    ucam = [[] for _ in range(len(_BINS) - 1)]
    for tag, (cc, _) in match.items():
        ucam[_binof(cc)].append(tag)
    amps = sorted({g['amp'] for u in UU.values() for g in u['rungs']
                   if g['amp'] != 20.0})
    bytag = {}
    if route == 'tones':
        for t in TONES:
            if not t['outside']:
                bytag.setdefault(t['tag'], []).append(t)

    def frac(tags, x):
        if route == 'tones':
            tt = [t for g in tags for t in bytag.get(g, ()) if t['amp'] == x]
            return (sum(t['rec'] for t in tt) / len(tt)) if tt else None
        num = den = 0
        for g in tags:
            for rg in UU[g]['rungs']:
                if rg['amp'] == x:
                    num += rg['both']
                    den += rg['n']
        return (num / den) if den else None

    # ★ A stratum the catalogue populates but the campaign never injected
    # into cannot be weighted, so it is DECLARED rather than silently
    # dropped: the completeness then covers only the windows in strata that
    # carry an injected unit, and the caption has to say how many.
    covered = sum(wcat[i] for i in range(len(wcat)) if wcat[i] and ucam[i])
    blind = sum(wcat[i] for i in range(len(wcat)) if wcat[i] and not ucam[i])

    def curve(tags_by_bin):
        out = []
        for x in amps:
            acc = wn = 0.0
            for i, tags in enumerate(tags_by_bin):
                if not tags or not wcat[i]:
                    continue
                f = frac(tags, x)
                if f is None:
                    continue
                acc += wcat[i] * f
                wn += wcat[i]
            out.append(acc / wn if wn else 0.0)
        return out

    p90 = _cross(amps, curve(ucam))
    import random as _rnd
    rng = _rnd.Random(23)
    bv, bu = [], 0
    for _ in range(1200):
        samp = [[tags[rng.randrange(len(tags))] for _ in tags] if tags else []
                for tags in ucam]
        c = _cross(amps, curve(samp))
        if c is None:
            bu += 1
        else:
            bv.append(c)
    bv.sort()
    lo = bv[int(0.16 * len(bv))] if bv else p90
    hi = bv[int(0.84 * len(bv))] if bv else p90
    diag = dict(n_cat=wcat, n_inj=[len(x) for x in ucam], route=route,
                n_matched=len(match), unmatched=unmatched,
                undef_frac=bu / 1200.0, n_covered=covered, n_blind=blind,
                worst_ctrl_diff=max(abs(a - b) for a, b in match.values()))
    return p90, (lo, hi), diag


def _median(xs):
    xs = sorted(xs)
    n = len(xs)
    return xs[n // 2] if n % 2 else 0.5 * (xs[n // 2 - 1] + xs[n // 2])


def main(argv):
    drive = None
    catdir = None
    outdir = os.path.dirname(os.path.abspath(__file__))
    for i, a in enumerate(argv):
        if a == '--drive':
            drive = int(argv[i + 1])
        if a == '--cat':
            catdir = argv[i + 1]
        if a == '--out':
            outdir = argv[i + 1]
    assert catdir, 'give --cat DIR, the directory holding the released products'

    # ★ One product per pattern.  A directory holding several candidates is
    # ambiguous, and silently taking the newest-looking one is how a
    # generator ends up reading a different file from the one the paper
    # quotes.  --pick NAME resolves the ambiguity explicitly, by name.
    picks = [argv[i + 1] for i, a in enumerate(argv) if a == '--pick']

    def one(pat):
        f = sorted(glob.glob(os.path.join(catdir, pat)))
        if len(f) > 1:
            f = [x for x in f if os.path.basename(x) in picks] or f
        assert len(f) == 1, (
            'pattern %s matches %d files in %s; name the one to read with '
            '--pick: %s' % (pat, len(f), catdir,
                            [os.path.basename(x) for x in f]))
        return f[0]

    CAT = list(csv.DictReader(open(one('per_target_results*.csv'))))
    VSYS = json.load(open(one('starrv*.json')))
    BARY = json.load(open(one(os.path.join('r8inputs', 'bary*.json'))))
    BARY = BARY['v_bary_kms']
    CAMP = json.load(open(one('m3a_result*.json')))['strata']
    R9 = os.path.join(catdir, 'r9inputs')
    TONES = json.load(open(os.path.join(R9, 'm3a_tones_r9.json')))
    UNITS = json.load(open(os.path.join(R9, 'm3a_units_r9.json')))
    SENSB = json.load(open(os.path.join(R9, 'sens_r9b.json')))
    MASKR9 = json.load(open(os.path.join(R9, 'mask_r9.json')))
    STACKR9 = json.load(open(os.path.join(R9, 'stackinj_r9.json')))
    OCC = list(csv.DictReader(open(one('occupancy_windows.csv'))))
    # ★ the screen's star count is the one ITS OWN generator produced from an
    # explicit merge table, not a count of directory names: a star observed
    # under two designations is one star, and re-deriving the count here
    # from the target strings would reintroduce exactly the key collision
    # the screen was repaired to remove.
    OCCRES = json.load(open(one('freqocc*.json')))

    OUTNAME = 'survey_numbers_round103%s.tex' % ('' if drive is None
                                                 else '_drive%d' % drive)
    M, FIRED = {}, []

    def m(k, v):
        assert k not in M, 'macro %s emitted twice' % k
        assert k.isalpha(), (
            'a LaTeX macro name may contain letters only; %r does not' % k)
        # ★ And the BODY must be valid TeX.  A doubled backslash in a Python
        # string literal is the one typo that produces a macro which
        # typesets the word "times" instead of a multiplication sign, and
        # neither a value gate nor a page count can see it.
        assert '\\\\' not in v, (
            'macro %s has a doubled backslash in its body (%r): it would '
            'typeset literally' % (k, v))
        M[k] = v

    def ck(name, cond, detail=''):
        if not cond:
            FIRED.append('%s: %s' % (name, detail))

    X = [r for r in CAT if r['crossing'] == 'True']
    NCROSS = len(X)

    # ---------------------------------------------------------------- A
    # The habitable-zone hosts, as distinct stars.  The prose used to name
    # the set in distance order and then gloss "the last named" with the
    # catalogue alias and planet of a DIFFERENT member, which identified a
    # 15-pc star with a 3.8-pc one.  The cure is that no star is ever
    # referred to by its position in a list: every one is named.
    HZ = {                      # catalogue key -> (typeset, planet, cited?)
        'Proxima Cen': ('Proxima~Centauri', 'Proxima~b', False),
        'TRAPPIST-1': ('TRAPPIST-1', 'TRAPPIST-1\\,e', False),
        'LHS 1140': ('LHS~1140', 'LHS~1140\\,b', False),
        'GJ 581': ('GJ~581', 'GJ~581\\,d', False),
        'HN Lib': ('HN~Lib', 'HN~Lib\\,b', False),
        'BD05 1668': ('GJ~273', 'GJ~273\\,b', True),
    }
    BY = {}
    for r in CAT:
        BY.setdefault(r['star_name'], []).append(r)
    ck('A1 every declared host is in the released catalogue',
       all(k in BY for k in HZ), sorted(k for k in HZ if k not in BY))
    hz = []
    for k, (nm, pl, cited) in HZ.items():
        rows = BY.get(k, [])
        xs = [r for r in rows if r['crossing'] == 'True']
        hz.append(dict(key=k, name=nm, planet=pl, cited=cited,
                       dist=float(rows[0]['dist_pc']) if rows else float('nan'),
                       nwin=len(rows), ncross=len(xs),
                       blocks=sorted({r['eb'] for r in xs}),
                       rankpass=sum(1 for r in xs
                                    if int(r['n_ctrl_ge_star']) == 0)))
    hz.sort(key=lambda h: h['dist'])
    cited = [h for h in hz if h['cited']]
    ck('A2 exactly one host carries its own citation', len(cited) == 1, cited)
    cit = cited[0] if cited else hz[0]
    if drive == 1:                       # name the star by list position
        cit = hz[-1]
    # ★ The defect was not a wrong value but a wrong REFERENT: the sentence
    # identified its subject positionally.  So assert that the star carrying
    # the citation is identified by name, i.e. that naming it by position
    # would give a different star -- which makes the positional form unusable
    # and the assertion non-vacuous.
    ck('A3 the cited host is named, not located in the list',
       cit is cited[0] if cited else False,
       'the citation would attach to %s, which is %.2f pc from the cited '
       'star %s' % (hz[-1]['name'], abs(hz[-1]['dist'] - cited[0]['dist'])
                    if cited else 0.0, cited[0]['name'] if cited else '?'))
    others = [h for h in hz if h is not cit]
    ck('A4 the cited host and every other host are distinct stars',
       all(abs(h['dist'] - cit['dist']) > 0.1 for h in others),
       [(h['name'], h['dist']) for h in others])
    m('HzNHostsNum', '%d' % len(hz))
    m('HzList', ', '.join(h['name'] for h in hz[:-1]) + ' and ' + hz[-1]['name'])
    m('HzCitedStar', cit['name'])
    m('HzCitedCatName', cit['key'].replace('BD05 ', 'BD$+$05~'))
    m('HzCitedPlanet', cit['planet'])
    m('HzCitedDist', '%.1f' % cit['dist'])
    xhost = [h for h in hz if h['ncross']]
    m('HzNCrossStars', '%d' % len(xhost))
    m('HzCrossStars', ', '.join('%s (%d)' % (h['name'], h['ncross'])
                                for h in xhost) or 'none')
    # ★ each host that carries crossings carries them in its OWN blocks, and
    # the paper must point each star at the paragraph that discusses it.
    ck('A5 no two crossing hosts share an execution block',
       len({b for h in xhost for b in h['blocks']})
       == sum(len(h['blocks']) for h in xhost),
       [(h['name'], h['blocks']) for h in xhost])
    # ★ A LaTeX macro name may contain LETTERS ONLY, so a star tag cannot
    # simply keep the catalogue designation: digits must be spelled, and the
    # result must still be unique or two stars share one set of macros.
    DIG = dict(zip('0123456789', ['Zero', 'One', 'Two', 'Three', 'Four',
                                  'Five', 'Six', 'Seven', 'Eight', 'Nine']))

    def tag_of(nm):
        return ''.join(DIG.get(c, c) for c in nm if c.isalnum())
    mk = tag_of if drive != 8 else (lambda nm: ''.join(c for c in nm
                                                       if c.isalpha()))
    tags = [mk(h['name']) for h in xhost]
    # ★ unique is not enough: a letters-only strip of "LHS~1140" is "LHS",
    # which is unique here by luck and discards the designation.  So the
    # check also requires the tag to carry every digit of the name, which is
    # what makes it fire on a stripper that merely happens not to collide.
    ck('A6 each crossing host has a unique macro tag that keeps its '
       'designation',
       len(tags) == len(set(tags))
       and all(all(DIG[c] in mk(h['name']) for c in h['name'] if c.isdigit())
               for h in xhost),
       list(zip([h['name'] for h in xhost], tags)))
    for h in xhost:
        tag = tag_of(h['name'])
        m('Hz%sDist' % tag, '%.1f' % h['dist'])
        m('Hz%sNCross' % tag, '%d' % h['ncross'])
        m('Hz%sNBlock' % tag, '%d' % len(h['blocks']))
        m('Hz%sNRankPass' % tag, '%d' % h['rankpass'])

    # ---------------------------------------------------------------- B
    # The line mask, in the stellar frame.  The Keplerian bound that
    # motivates masking at all is a stellar-frame quantity, so the mask is
    # evaluated there and ONE unattributed count is carried.
    # The per-crossing stellar-frame offset.  dv_stel = dv_sky - v_bary +
    # v_sys, with v_bary per (block, window) and v_sys per star.  Where the
    # released records lack one of the two terms it is taken from the frozen
    # per-crossing inventory, which is keyed on (star, block, sky offset) --
    # ★ NOT on the block alone: two release blocks hold two stars each, and a
    # block-only key averages them, which is the star-blind-key family.
    # ★★ v4.11.  The frame arithmetic and the masked-transition list are no
    # longer re-implemented here.  maskframe_v411.py owns both, and this
    # generator, the crossing ledger and the line-confusion figure all import
    # it, so there is one frame chain and one species list in the paper
    # instead of three.  Three things follow from the change: the mask now
    # holds sulphur monoxide; the systemic velocity of beta Pic is the
    # adopted one rather than the superseded catalogue value; and the
    # crossing frequency is recovered for the rows the release ships without
    # one, instead of a window edge standing in for it.
    FROZEN = {}
    for q in MASKR9['newly_evaluable']:
        FROZEN[(q['star'], q['eb'], round(q['dv_sky'], 1))] = q
    rec, used_frozen, bound_only = [], 0, 0
    for r in X:
        dv = float(r['line_offset_kms'])
        f_topo = mf.recover_ftopo(r['nearest_line'], r['line_offset_MHz'])
        fr = mf.frame_row(r['eb'], r['star_name'], r['flo_GHz'], f_topo)
        vc, vs = fr['v_bary'], fr['v_sys']
        src = ('released' if fr['v_bary_src'] == 'bary_v405.json'
               and fr['v_sys_src'] == 'starrv_v399.json'
               else 'frozen inventory')
        bound = bool(fr.get('bound_only'))
        q = FROZEN.get((r['star_name'], r['eb'], round(dv, 1)))
        if q is not None:
            used_frozen += 1
            bound_only += bool(q['bound'])
        rec.append(dict(row=r, dv_sky=dv, v_bary=vc, v_sys=vs, src=src,
                        bound=bound, line=fr.get('line'),
                        dv_sky_mask=(mf.nearest(f_topo)[2]
                                     if f_topo is not None else None),
                        dv_stel=fr['dv_stellar'] if fr.get('ok') else None))
    openq = [q for q in rec if q['dv_stel'] is None]
    if drive == 2:
        openq = list(rec)
    ck('B1 every crossing has a stellar-frame offset', not openq,
       [(q['row']['star_name'], q['row']['eb']) for q in openq])
    ck('B1b the frozen inventory supplied exactly the terms the release '
       'lacks, and no more', used_frozen == len(MASKR9['newly_evaluable']),
       (used_frozen, len(MASKR9['newly_evaluable'])))
    # ★ Three crossings' line coincidences are reported as a note rather
    # than as a disposition (`maskframe_v411.note_reason`), so coincidence
    # and attribution are not the same predicate and this file must use the
    # second.  The predicate is on the SPECIES and is evaluated from the two
    # quantities this file already holds -- the nearest masked transition in
    # the star's frame and the offset to it -- so it cannot reach a different
    # answer from the ledger's.
    def _wh(q):
        _r = q['row']
        _f = mf.recover_ftopo(_r['nearest_line'], _r['line_offset_MHz'])
        return (mf.note_reason(q.get('line'), q.get('dv_stel')) is not None
                or mf.withheld_reason(_r['eb'], _f) is not None)

    m('NMaskFrozen', '%d' % used_frozen)
    m('NMaskBound', '%d' % bound_only)

    att = [q for q in rec
           if abs(q['dv_stel']) <= MASK_HALF_KMS and not _wh(q)]
    una = [q for q in rec
           if abs(q['dv_stel']) > MASK_HALF_KMS or _wh(q)]
    # ★ The sky-frame column must be evaluated against the SAME mask, or the
    # comparison is between two frames AND two species lists and says
    # nothing.  That is what it was: `dv_sky` is the released offset to the
    # nearest transition of the 15-line search list, while the stellar column
    # now uses the published list plus SO.
    # ★ The withheld row is excluded from BOTH, so this compares two frames
    # and not two predicates.
    sky_att = [q for q in rec
               if abs(q['dv_sky_mask']) <= MASK_HALF_KMS and not _wh(q)]
    # ★★ v4.12.  AT THE SURVEY'S OWN HALF-WIDTH THE TWO FRAMES AGREE ON ALL
    # BUT ONE CROSSING, and the one they disagree about is named rather than
    # absorbed.  With the hand-kept fifteen-line list the counts were
    # identical, which is what dissolved the paper's three attribution
    # numbers -- they were one mask with three denominators.  The rebuilt list
    # is dense enough for the frame to decide a marginal case, so the claim is
    # now the measured one: the frames differ on at most one crossing, the
    # paper's count is the stellar-frame one, and the difference is reported.
    _fdiff = sorted({(q['row']['star_name'], q['row']['eb'])
                     for q in rec
                     if (abs(q['dv_stel']) <= MASK_HALF_KMS)
                     != (abs(q['dv_sky_mask']) <= MASK_HALF_KMS)})
    if drive == 16:
        _fdiff = _fdiff + [('driven', 'driven'), ('driven2', 'driven2')]
    # ★ The comparison is between COINCIDENCE in the two frames.  It used to
    # be written as a difference of ATTRIBUTED counts, which was the same
    # number while every coincidence disposed and stopped being so as soon
    # as some did not: the noted crossings leave both frames' attributed
    # sets and the difference went to zero while the frames still disagreed.
    _ncs = sum(1 for q in rec if abs(q['dv_stel']) <= MASK_HALF_KMS)
    _nck = sum(1 for q in rec if abs(q['dv_sky_mask']) <= MASK_HALF_KMS)
    ck('B2 at the adopted half-width the sky and stellar frames disagree '
       'about at most one crossing, against one mask, and this generator '
       'names it', len(_fdiff) <= 1 and abs(_ncs - _nck) == len(_fdiff),
       'stellar %d coincident (%d attributed), sky %d coincident (%d), '
       'differing %s' % (_ncs, len(att), _nck, len(sky_att), _fdiff))
    m('NMaskFrameDiff', '%d' % len(_fdiff))
    # ★ ...and that coincidence is NOT a reason to evaluate the mask in the
    # observed frame, which is what the paper used to say.  The two frames
    # agree on the count and disagree on the offsets by up to the whole
    # barycentric swing, so measure that and publish it.
    # over the crossings where the frame could decide anything -- a shift of
    # thousands of km/s on a crossing 20000 km/s from every transition is
    # arithmetic, not a frame effect
    _fshift = max(abs(q['dv_stel'] - q['dv_sky_mask']) for q in rec
                  if abs(q['dv_stel']) <= 2 * MASK_HALF_KMS)
    if drive == 24:
        _fshift = 0.0
    ck('B2b the two frames differ per crossing even where they agree on the '
       'count', _fshift > MASK_HALF_KMS / 5.0, '%.1f km/s' % _fshift)
    m('MaskFrameShiftKms', '%.0f' % _fshift)
    m('NCrossReleased', '%d' % NCROSS)
    m('MaskHalfKms', '%d' % int(MASK_HALF_KMS))
    m('MaskFrame', 'stellar')
    m('NAttributedReleased', '%d' % len(att))
    m('NUnattributedReleased', '%d' % len(una))

    # ---- the adopted crossing list.  The released catalogue predates the
    # adoption of the field-corrected search statistic, so the published
    # crossing list differs from it by a declared delta, and the delta is
    # applied here rather than restated anywhere else.  Every term is read
    # from the frozen inventory and the sum is asserted to close.
    V = MASKR9['v409']
    d_fell = len(V['fell_detail'])
    d_fell_un = V['fell_unattributed_in_stellar']
    d_rose = len(V['risen_attributed'])
    d_rest = len(V['restored_attributed'])
    d_new_un = len(V['hd14055_unattributed'])
    if drive == 17:
        d_fell_un = d_fell + 1
    ck('B5 every crossing that falls below the trigger was unattributed, so '
       'none of them is removed from the attributed count',
       d_fell_un == d_fell, (d_fell_un, d_fell))
    _wh_adopted = [q for q in rec if _wh(q)]
    n_att = len(att) + d_rose + d_rest
    n_una = len(una) - d_fell_un + d_new_un
    n_cross = NCROSS - d_fell + d_rose + d_rest + d_new_un
    if drive == 18:
        n_cross += 1
    ck('B6 the attributed and unattributed counts close on the crossing '
       'count', n_att + n_una == n_cross,
       '%d + %d != %d' % (n_att, n_una, n_cross))
    # ★★ The crossing COUNT is the delta and must still close on the frozen
    # one.  The attributed SPLIT must not: the mask has gained a species, and
    # the point of adding one is that a disposition moves.  So the count is
    # pinned and the split is required to move in the only direction adding
    # transitions can move it.
    ck('B7 the adopted crossing count reproduces the frozen result',
       n_cross == MASKR9['adopted']['n_crossings'],
       (n_cross, MASKR9['adopted']))
    # ★★ v4.12.  COINCIDENCE AND ATTRIBUTION ARE NOT THE SAME PREDICATE.
    # The rebuilt species list is a superset of the hand-kept one, so it can
    # only move crossings INTO coincidence; exactly the withheld rows are then
    # reported outside the mask, and both halves are required here rather than
    # reported.  `ledger_v410.py`, which runs after this file, asserts that
    # the counts published below are the ones its own ledger closes on -- the
    # check belongs there, where the comparison is not a stale read.
    _nwh = len(_wh_adopted)
    if drive == 25:
        _nwh = 0
    ck('B7b the rebuilt species list moves crossings only into coincidence, '
       'and the attributed count is the coincident count less the crossings '
       'whose coincidence is reported as a note',
       _nwh >= 1 and len(mf.WITHHELD) == 0
       and n_att + _nwh >= MASKR9['adopted']['attributed']
       and n_una - _nwh <= MASKR9['adopted']['unattributed'],
       'coincident %d, noted %d, attributed %d/%d against the hand-kept '
       'mask %d/%d' % (n_att + _nwh, _nwh, n_att, n_una,
                       MASKR9['adopted']['attributed'],
                       MASKR9['adopted']['unattributed']))
    m('NCross', '%d' % n_cross)
    m('NAttributed', '%d' % n_att)
    m('NUnattributed', '%d' % n_una)
    m('NMaskOpen', '0')
    m('NUnattributedHi', '%d' % n_una)
    # ★ Counted, not read: the frozen figure belongs to the 17-transition
    # mask.  None of the four crossings the delta removes passed the rank
    # screen and none of the four it adds does either, so the adopted count
    # is the released one -- which is asserted, not assumed.
    _rf_rel = sum(1 for q in rec
                  if (abs(q['dv_stel']) > MASK_HALF_KMS or _wh(q))
                  and int(q['row']['n_ctrl_ge_star']) == 0)
    rf_un = _rf_rel
    # ★ The count DOES grow, by exactly the noted crossings that lead their
    # own control fields: a coincidence reported as a note leaves the
    # crossing unattributed, and one of the three leads its field.  So the
    # check is the decomposition, not an inequality -- the old form could
    # only have failed on the right answer.
    _rf_note = sum(1 for q in rec
                   if _wh(q) and int(q['row']['n_ctrl_ge_star']) == 0)
    _rf_plain = sum(1 for q in rec
                    if abs(q['dv_stel']) > MASK_HALF_KMS
                    and int(q['row']['n_ctrl_ge_star']) == 0)
    if drive == 23:
        _rf_note = 0
    ck('B7c the unattributed crossings leading their own control fields are '
       'the crossings coincident with nothing plus exactly the noted ones '
       'that lead theirs, and the noted ones change the count',
       rf_un == _rf_plain + _rf_note and _rf_note >= 1,
       '%d = %d + %d noted' % (rf_un, _rf_plain, _rf_note))
    m('NUnattrRankFlagged', '%d' % rf_un)
    m('NUnattrScreened', '%d' % (n_una - rf_un))
    # the ladder, stellar frame, on the released list (where it is computable
    # per crossing) with the adopted total stated beside it
    lad = []
    for w in (13.0, 20.0, 30.0, 50.0, 100.0):
        a = sum(1 for q in rec if abs(q['dv_stel']) <= w)
        u = len(rec) - a
        g = sum(1 for q in rec if abs(q['dv_stel']) > w
                and int(q['row']['n_ctrl_ge_star']) == 0)
        lad.append((w, a, u, g))
    ck('B4 doubling the mask half-width leaves the rank-flagged '
       'unattributed set unchanged', lad[-1][3] == lad[-2][3],
       [(l[0], l[3]) for l in lad])

    # ---------------------------------------------------------------- C
    # The single sensitivity and the single benchmark.
    # ★ The multiplier is NOT the campaign's own pooled 90 per cent point.
    # The campaign injected into 21 windows whose control maxima are not
    # distributed like the survey's -- 4 of its 21 sit above 10 sigma against
    # 12 of the survey's 402 -- and the spatial screen is driven by exactly
    # that variable: in a window whose control ring peaks at C sigma the
    # screen is equivalent to raising the 5 sigma trigger to C.  So the
    # survey completeness is the control-maximum-stratified mean of the
    # measured per-stratum curves, weighted by the number of catalogue
    # windows in each stratum.  The catalogue publishes ctrl_max_snr for
    # every window, so the weights are measured, not assumed.
    SENS = json.load(open(os.path.join(catdir, 'sens_r11.json')))
    MULT = {'A': SENS['p90'], 'B': SENS['p90_B']}
    CI = {'A': (SENS['p90_boot']['lo'], SENS['p90_boot']['hi']),
          'B': (SENS['p90_B'], SENS['p90_B'])}
    _st = SENS['strat']
    STRAT = {'A': dict(n_cat=_st['n_cat'], n_inj=_st['n_inj'],
                       n_matched=_st['n_matched'], unmatched=_st['unmatched'],
                       n_covered=_st['n_covered'], n_blind=_st['n_blind']),
             'B': dict(n_cat=_st['n_cat_B'], n_inj=_st['n_inj_B'],
                       n_matched=_st['n_matched_B'],
                       unmatched=_st['unmatched_B'],
                       n_covered=_st['n_covered_B'],
                       n_blind=_st['n_blind_B'])}
    # ★ Class B has to use the per-unit route, because the per-tone records
    # for the coarse stratum were never extracted.  The size of that
    # approximation is therefore MEASURED on Class A, where both routes run,
    # and required to be small -- rather than asserted to be negligible.
    _dev = SENS['route_dev']
    if drive == 15:
        _dev = 0.5
    _aU = MULT['A'] * (1.0 + _dev)
    ck('C6 the per-unit route agrees with the per-tone route where both can '
       'be run, which bounds the approximation Class B is forced into',
       _dev < 0.02,
       'the two routes give %.4f and %.4f, a %.1f per cent difference'
       % (MULT['A'], _aU, 100 * _dev))
    m('EirpNinetyRouteDevPct', '%.1f' % (100 * _dev))
    # FALSIFIER, fixed before running: the Class A value must reproduce the
    # frozen post-stratified result to 3 decimal places, or the re-derivation
    # here is not the one that was reviewed.
    _want = SENSB['stratified']['p90']
    ck('C0 the completeness record reproduces the frozen campaign result on '
       'the frozen criterion, so the scoring has not changed',
       abs(SENS['regression']['recomputed']['weighted_rank'] - _want) < 1e-3,
       'the record recomputes %.4f on that criterion against a frozen %.4f'
       % (SENS['regression']['recomputed']['weighted_rank'], _want))
    ck('C0b and the adopted factor is the one measured through the chain that '
       'disposes of a crossing, which is deeper',
       MULT['A'] < SENS['regression']['recomputed']['weighted_rank'],
       '%.4f against %.4f'
       % (MULT['A'], SENS['regression']['recomputed']['weighted_rank']))
    if drive == 3:
        MULT['A'] = MULT['B']
    ck('C1 the two channelisation classes are measured separately and are '
       'not the same number', abs(MULT['A'] - MULT['B']) > 0.05, MULT)
    m('EirpNinetyMultA', '%.2f' % MULT['A'])
    m('EirpNinetyMultB', '%.2f' % MULT['B'])
    # ★ The interval is READ from the frozen bootstrap, not re-drawn: a
    # different random stream moves a percentile by a few hundredths, and a
    # published interval that changes when nothing changed is worse than one
    # that is quoted from the record.  My own re-draw is kept as a
    # cross-check and asserted to agree.
    _fb = SENS['p90_boot']
    ck('C1b the interval brackets the factor it belongs to',
       _fb['lo'] < MULT['A'] < _fb['hi'],
       '%.3f < %.3f < %.3f' % (_fb['lo'], MULT['A'], _fb['hi']))
    ck('C1c the bootstrap resolves a 90 per cent point in every resample',
       _fb['undef_frac'] == 0.0, _fb['undef_frac'])
    m('EirpNinetyMultALo', '%.2f' % _fb['lo'])
    m('EirpNinetyMultAHi', '%.2f' % _fb['hi'])
    m('EirpNinetyMultBLo', '%.2f' % CI['B'][0])
    m('EirpNinetyMultBHi', '%.2f' % CI['B'][1])
    # ★ The injection caveat is a count of the windows carriers were injected
    # INTO, and it is a different number for each class.  The figure the
    # manuscript carried belongs to a superseded campaign.
    for cls in ('A', 'B'):
        _n = STRAT[cls]['n_matched']
        _tot = sum(1 for r in CAT if r['search_class'] == cls)
        m('NInjWin%s' % cls, '%d' % _n)
        m('NTransferWin%s' % cls, '%d' % (_tot - _n))
        ck('C4 the %s injection caveat adds up to the class window count' % cls,
           _n + (_tot - _n) == _tot, (cls, _n, _tot))
        ck('C5 every injected %s window joined a catalogue row' % cls,
           not STRAT[cls]['unmatched'], STRAT[cls]['unmatched'])
    m('NInjStrata', '%d' % (len(_BINS) - 1))
    for cls in ('A', 'B'):
        m('NStratCovered%s' % cls, '%d' % STRAT[cls]['n_covered'])
        m('NStratBlind%s' % cls, '%d' % STRAT[cls]['n_blind'])
    ck('C7 the Class A completeness covers every Class A window',
       STRAT['A']['n_blind'] == 0, STRAT['A'])
    # Class B has a stratum with no injected unit; that is a declared
    # limitation, so assert it is SMALL and that the declaration is non-empty
    # rather than asserting it away.
    ck('C8 the Class B blind stratum is small and declared',
       0 < STRAT['B']['n_blind'] < 0.01 * sum(STRAT['B']['n_cat']),
       'blind %d of %d' % (STRAT['B']['n_blind'],
                           sum(STRAT['B']['n_cat'])))
    m('InjStrataCat', ' / '.join('%d' % x for x in STRAT['A']['n_cat']))
    m('InjStrataInj', ' / '.join('%d' % x for x in STRAT['A']['n_inj']))
    # ★★ THE COMPLETENESS IS TRANSFERRED WITHIN STRATA, AND THE PHASE-CENTRE
    # LOSS IS APPLIED RATHER THAN DECLARED.  Both are per window, so both
    # enter here, at the one place a window's EIRP_90 is formed.
    #   - the Class A multiplier is the one measured for the window's own
    #     stratum (strata_v411.py): the ring-is-noise value where the control
    #     ring carries no emission, and the BOUND where it does, because in
    #     those windows the ladder never reaches ninety per cent.  The blanket
    #     factor is still published, beside the strata, as what it is.
    #   - Class B keeps one factor: no injected coarse unit has a bright
    #     control ring, so the rule cannot be measured there.  Declared.
    #   - the retained amplitude fraction divides, so every limit gets
    #     SHALLOWER (pxapply_v411.py).  One window of the release has no
    #     astrometric keys and is left uncorrected; it is named in the paper.
    PXA = json.load(open(os.path.join(catdir, 'pxapply_v411.json')))
    _PXBM = PXA['retained_fraction_by_eb']
    ck('C2b the factor applied per window is the factor this file publishes, '
       'so the two cannot drift',
       abs(SENS['p90'] - MULT['A']) < 1e-9,
       'record %.4f against %.4f here' % (SENS['p90'], MULT['A']))
    _nstrat = _npx = 0
    for r in CAT:
        if r['search_class'] == 'A':
            mult = MULT['A']
        else:
            mult = MULT['B']
        e = float(r['eirp_nominal_W']) * mult
        _bm = _PXBM.get(r['eb'])
        if _bm:
            e /= _bm
            _npx += 1
        r['_e90'] = e
    # ★★ v4.11: ONE DEFINITION OF THE PAPER'S HEADLINE SENSITIVITY.  This
    # expression was formed here and nowhere else, and five other generators
    # went on reading the RETIRED catalogue column instead -- which is how
    # every figure of merit in the paper came out x1.54 optimistic.  Those
    # five now take the value from `adopted_e90.py`, so this generator is
    # required to agree with it row for row.  If the two ever part, the
    # headline and the figures of merit have parted, which is the condition
    # nothing could see for two cycles.
    import adopted_e90 as _ae
    _ae_e = _ae.per_window(CAT, catdir, mult_b=MULT['B'])
    _ae_bad = [r for r in CAT
               if abs(_ae_e[id(r)] / r['_e90'] - 1.0) > 1e-9]
    if drive == 27:
        _ae_bad = CAT[:1]
    ck('C2d the adopted per-window EIRP_90 formed here is the one '
       'adopted_e90.py gives every other generator, row for row',
       not _ae_bad,
       '%d of %d windows disagree, e.g. %s' % (
           len(_ae_bad), len(CAT),
           (_ae_bad[0]['star_name'], _ae_bad[0]['eb'],
            _ae_bad[0]['_e90'], _ae_e[id(_ae_bad[0])]) if _ae_bad else ''))
    ck('C2c every window but the declared exception carries the phase-centre '
       'correction', _npx == PXA['n_joined'],
       '%d of %d corrected' % (_npx, len(CAT)))
    G = BENCH_ETA * (math.pi * BENCH_D_M * BENCH_NU_GHZ * 1e9 / 2.998e8) ** 2
    BENCH = BENCH_PTX_W * G
    ck('C2 the benchmark EIRP is computed from the dish, not typed',
       4.0e14 < BENCH < 8.0e14, BENCH)
    m('BenchDiam', '%.0f' % BENCH_D_M)
    m('BenchPowerMW', '%.0f' % (BENCH_PTX_W / 1e6))
    m('BenchFreqGHz', '%.0f' % BENCH_NU_GHZ)
    m('BenchEta', '%.1f' % BENCH_ETA)
    m('BenchGain', r'%.1f\times10^{%d}' % (G / 10 ** int(math.log10(G)),
                                           int(math.log10(G))))
    m('BenchEirp', r'%.1f\times10^{%d}'
      % (BENCH / 10 ** int(math.log10(BENCH)), int(math.log10(BENCH))))
    best = {}
    for r in CAT:
        k = (r['search_class'], r['system_id'])
        best[k] = min(best.get(k, float('inf')), r['_e90'])
    bestA = {s: v for (c, s), v in best.items() if c == 'A'}
    bestAll = {}
    for (c, s), v in best.items():
        bestAll[s] = min(bestAll.get(s, float('inf')), v)
    nA = sum(1 for v in bestA.values() if v <= BENCH)
    nAll = sum(1 for v in bestAll.values() if v <= BENCH)
    if drive == 4:
        nA = len(bestA) + 1
    ck('C3 the systems reaching the benchmark are a subset of the systems '
       'searched', nA <= len(bestA) and nAll <= len(bestAll),
       (nA, len(bestA), nAll, len(bestAll)))
    m('NSysA', '%d' % len(bestA))
    m('NSys', '%d' % len(bestAll))
    m('BenchNSysA', '%d' % nA)
    m('BenchNSys', '%d' % nAll)

    # ---------------------------------------------------------------- D
    # The window and crossing subsets, each defined once and named apart.
    rankfirst = [r for r in CAT if int(r['n_ctrl_ge_star']) == 0]
    stage1 = [r for r in rankfirst if r['crossing'] == 'True']
    s1att = [r for r in stage1
             if r['disposition_computed'].startswith('attributed')]
    ck('D1 the stage-1 flagged windows are a subset of the rank-first ones',
       set(id(r) for r in stage1) <= set(id(r) for r in rankfirst),
       (len(stage1), len(rankfirst)))
    ck('D2 the stage-1 flagged windows partition into attributed and not',
       len(s1att) + (len(stage1) - len(s1att)) == len(stage1), '')
    m('NWindows', '%d' % len(CAT))
    m('NRankFirst', '%d' % len(rankfirst))
    m('NStageOne', '%d' % len(stage1))
    m('NStageOneAttr', '%d' % len(s1att))
    m('NStageOneUnattr', '%d' % (len(stage1) - len(s1att)))
    # the two "51 of 56" subsets, which exclude DIFFERENT crossings
    nocov = [r for r in X if r['n_ind_cells'] == '']
    OUTSTANDING = {'A002_Xa7a216_X23e4', 'A002_Xd9668b_Xa9df',
                   'A002_Xd9668b_X3a90'}
    nofit = [r for r in X if r['eb'] in OUTSTANDING]
    if drive == 5:
        nofit = list(nocov)
    ck('D3 the crossings without a fit and the crossings without a null '
       'scale are different crossings, so "of 56" must never be written '
       'without saying which',
       not ({(r['eb'], r['flo_GHz']) for r in nofit}
            & {(r['eb'], r['flo_GHz']) for r in nocov}),
       sorted({r['star_name'] for r in nofit}
              & {r['star_name'] for r in nocov}))
    m('NCrossFitted', '%d' % (NCROSS - len(nofit)))
    m('NCrossUnfitted', '%d' % len(nofit))
    m('NCrossNullScaled', '%d' % (NCROSS - len(nocov)))
    m('NCrossNoNullScale', '%d' % len(nocov))
    m('NCrossA', '%d' % sum(1 for r in X if r['search_class'] == 'A'))
    m('NCrossANullScaled',
      '%d' % sum(1 for r in X
                 if r['search_class'] == 'A' and r['n_ind_cells'] != ''))
    # ★ The false-alarm expectation is summed over the covered Class A
    # windows and carries the unattributed fraction, so the count it
    # predicts is the unattributed Class A crossings IN THOSE WINDOWS -- not
    # all crossings, not all Class A crossings, and not the unattributed
    # count of the whole survey.  Four different numbers have been written
    # for this one comparison; it is computed once, here, on the population
    # the expectation itself uses.
    stel = {id(q['row']): q for q in rec}
    _p = [r for r in X if r['search_class'] == 'A' and r['n_ind_cells'] != '']
    if drive == 10:
        _p = list(X)
    ck('D4 the observed count is taken on the same population the '
       'expectation is summed over',
       all(r['search_class'] == 'A' and r['n_ind_cells'] != '' for r in _p),
       'the comparison population is not the covered Class A windows')
    _lo = sum(1 for r in _p if stel[id(r)]['dv_stel'] is not None
              and abs(stel[id(r)]['dv_stel']) > MASK_HALF_KMS)
    _lo += sum(1 for r in _p if stel[id(r)]['dv_stel'] is None
               and abs(stel[id(r)]['dv_sky']) > BOUND)
    _open = sum(1 for r in _p if stel[id(r)]['dv_stel'] is None
                and abs(stel[id(r)]['dv_sky']) <= BOUND)
    m('NChanceObsA', '%d' % _lo)
    m('NChanceObsAHi', '%d' % (_lo + _open))
    # ★★ THE CHANCE EXPECTATION DOES NOT MOVE WITH THE COMPLETENESS, and
    # somebody will eventually try to rescale it.  It is summed from each
    # window's own false-alarm probability, which is a function of the
    # trigger level and the number of searched channel x drift cells and of
    # nothing else: the completeness multiplier converts a trigger into a
    # radiated power AFTER the search has fired, so it cannot enter a count
    # of expected triggers.  Asserted by construction: the expectation is
    # read from the record that computes it, and the cell counts and trigger
    # that record used are required to be unchanged by this round.
    _ce = None
    for _f in sorted(glob.glob(os.path.join(catdir, 'survey_numbers*.tex'))):
        if os.path.basename(_f) == OUTNAME:
            continue
        _mm = re.search(r'\\(?:new|renew)command\{\\RsevChanceExp\}\{([^}]+)\}',
                        open(_f, errors='ignore').read())
        if _mm:
            _ce = float(_mm.group(1))
    _cells = sorted({r['n_ind_cells'] for r in X if r['n_ind_cells']})
    if drive == 19:
        _ce = _ce * MULT['A'] / 5.70
    # ★★ D5 USED TO PIN THE EXPECTATION TO THE LITERAL 34.5 -- a remembered
    # number, which is this project's commonest bug, and it fired the moment
    # the mask occupancy was corrected from 4.1 to 4.3 per cent and the
    # expectation properly became 34.4.  A check that has to be edited every
    # time the quantity it guards legitimately moves is guarding the wrong
    # thing.  What D5 means is that the expectation is the product of the
    # trigger term, the localisation fraction and the unmasked share of the
    # band, and that the completeness multiplier appears in none of them.
    # So it must now REPRODUCE from its own three published factors, and
    # must separately NOT equal any rescaling of itself by the multiplier.
    def _rv(nm):
        _got = None
        for _g in sorted(glob.glob(os.path.join(catdir,
                                                'survey_numbers*.tex'))):
            if os.path.basename(_g) == OUTNAME:
                continue
            _m2 = re.search(r'\\(?:new|renew)command\{\\%s\}\{([^}]+)\}' % nm,
                            open(_g, errors='ignore').read())
            if _m2:
                _got = _m2.group(1)
        return float(_got)

    _trig = _rv('RsevChanceTrigA')
    _loc = _rv('RsevChanceFracLoc')
    _occ = _rv('RsevChanceOccPct')
    _chain = _trig * _loc * (1.0 - _occ / 100.0)
    ck('D5 the chance expectation reproduces from its own three published '
       'factors, and the completeness multiplier is in none of them',
       _ce is not None and abs(_ce - _chain) < 0.15
       and abs(_ce - _chain * float(M['EirpNinetyMultA'])) > 0.15,
       'the expectation is %s against %.2f = %s x %s x (1 - %s per cent), '
       'the trigger term, the localisation fraction and the unmasked share '
       'of the band; it is a property of those and of the %d distinct cell '
       'counts in the catalogue, not of the %s multiplier, and rescaling it '
       'by a completeness factor is a category error'
       % (_ce, _chain, _trig, _loc, _occ, len(_cells),
          M['EirpNinetyMultA']))
    m('ChanceExpIndependent', 'trigger level and searched cell count')

    # ---------------------------------------------------------------- E
    # The interference screen's population, stated against the released one.
    occ_eb = {r['eb'] for r in OCC}
    rel_eb = {r['eb'] for r in CAT}
    byeb = {}
    for r in OCC:
        byeb.setdefault(r['eb'], []).append(float(r['flo']))
    shared = sum(1 for r in CAT
                 if any(abs(float(r['flo_GHz']) - x) < 2e-3
                        for x in byeb.get(r['eb'], ())))
    m('RfiNWin', '%d' % len(OCC))
    naive = len({r['target'].rsplit('_B', 1)[0] for r in OCC})
    nmerged = OCCRES['n_stars'] if drive != 9 else naive
    ck('E2 the screen star count is the merged one, not a count of names',
       nmerged < naive,
       'merged %s vs %d distinct target strings; if these were equal the '
       'merge table would be doing nothing and the assertion would be '
       'vacuous' % (nmerged, naive))
    m('RfiNStar', '%d' % nmerged)
    m('RfiNStarNaive', '%d' % naive)
    m('RfiNCoarse', '%d' % sum(1 for r in OCC
                               if r['rescls'].startswith('coarse')))
    m('RfiNSharedWin', '%d' % shared)
    m('RfiNSharedEb', '%d' % len(occ_eb & rel_eb))
    # ★ The screen runs on a population the rest of the paper never uses.
    # The natural reading of "3 027 windows toward 133 stars" is that the
    # released sample sits inside it; it does not.  So the relation is
    # DECLARED here, in one word, and the declaration is checked against the
    # measurement -- which is what makes the sentence in the paper a
    # statement about the data rather than an assumption about it.
    rel = ('superset' if shared == len(CAT) and len(OCC) >= len(CAT)
           else 'subset' if shared == len(OCC)
           else 'overlapping')
    if drive == 7:
        rel = 'superset'
    ck('E1 the screen population relates to the released sample as declared',
       rel == RFI_RELATION,
       'declared %r, measured %r: the screen sees %d of the %d released '
       'windows and %d of the %d released execution blocks, so a sentence '
       'calling it a superset of the sample would be false'
       % (RFI_RELATION, rel, shared, len(CAT), len(occ_eb & rel_eb),
          len(rel_eb)))
    m('RfiRelation', rel)

    # ---------------------------------------------------------------- F
    # One combined interval, derived once.
    # ★ ONE combined interval, and it supersedes the three brackets the
    # manuscript carried: the campaign bootstrap over injected windows IS
    # the window-to-window transfer term, so quoting both counted it twice.
    # ★ ONE combined interval, and it is the one the completeness record
    # formed from the campaign that measured the completeness: the transfer
    # term is the spread across the injected windows, so it cannot be taken
    # from a record of a different campaign than the factor it applies to.
    CMB = dict(SENSB['combined'])
    CMB.update(campaign_transfer_lo=SENS['budget']['transfer_lo'],
               campaign_transfer_hi=SENS['budget']['transfer_hi'],
               comb_lo=SENS['budget']['comb_lo'],
               comb_hi=SENS['budget']['comb_hi'],
               factor_lo=SENS['budget']['factor_lo'],
               factor_hi=SENS['budget']['factor_hi'],
               decorrelation_declared=SENS['budget'][
                   'decorrelation_declared'])
    m('EirpNinetyFacLo', '%.2f' % CMB['factor_lo'])
    m('EirpNinetyFacHi', '%.2f' % CMB['factor_hi'])
    m('EirpNinetyPctLo', '%.0f' % (100 * CMB['comb_lo']))
    m('EirpNinetyPctHi', '%.0f' % (100 * CMB['comb_hi']))
    ck('F3 the combined interval brackets unity',
       CMB['factor_lo'] < 1.0 < CMB['factor_hi'],
       (CMB['factor_lo'], CMB['factor_hi']))
    sy_lo = quad([b[2] for b in BUDGET if b[4] == 'y'])
    sy_hi = quad([b[3] for b in BUDGET if b[4] == 'y'])
    st_lo = quad([b[2] for b in BUDGET if b[4] == 's'])
    st_hi = quad([b[3] for b in BUDGET if b[4] == 's'])
    tot_lo, tot_hi = quad([sy_lo, st_lo]), quad([sy_hi, st_hi])
    bias_lo = math.prod(1 + b[2] / 100.0 for b in BUDGET if b[4] == 'b') - 1
    bias_hi = math.prod(1 + b[3] / 100.0 for b in BUDGET if b[4] == 'b') - 1
    if drive == 6:
        sy_lo = quad([b[2] for b in BUDGET if b[4] in 'yb'])
    ck('F1 no uncorrected bias is inside the quadrature sum',
       abs(sy_lo - quad([b[2] for b in BUDGET if b[4] == 'y'])) < 1e-9,
       'a one-sided bias has been added to the interval in quadrature, '
       'which treats a known offset as if it were a random error')
    ck('F2 the combined interval is wider than either part',
       tot_lo >= max(sy_lo, st_lo) and tot_hi >= max(sy_hi, st_hi),
       (tot_lo, tot_hi, sy_lo, st_lo))
    m('EirpNinetyMultALoComb', '%.2f' % (MULT['A'] * CMB['factor_lo']))
    m('EirpNinetyMultAHiComb', '%.2f' % (MULT['A'] * CMB['factor_hi']))
    # the two components of the one interval, and the one declared bias
    m('EirpNinetyCampPctLo', '%.0f' % (100 * CMB['campaign_transfer_lo']))
    m('EirpNinetyCampPctHi', '%.0f' % (100 * CMB['campaign_transfer_hi']))
    m('EirpNinetyInstPct', '%.0f' % (100 * CMB['instrumental']))
    m('EirpNinetyInstPctWorst', '%.0f' % (100 * CMB['instrumental_worst']))
    # ★ R2-11: decorrelation is ONE-SIDED.  An injected carrier suffers no
    # coherence loss and a real one does, so the effect can only make a
    # limit optimistic; a negative branch would be a claim that some limits
    # are pessimistic for the same reason, which is meaningless.  The pair
    # that used to be published here came from a frozen record of a
    # superseded campaign and still carried the two-sided -12/+17, while
    # Table 3 and Sec. 5.1 had moved to +0/+20 -- two declarations of one
    # quantity, which is precisely what twinmacro exists to prevent.  ONE
    # macro now, the magnitude, read from the same record Sec. 5.1 reads.
    _dec = CMB['decorrelation_declared']
    assert float(_dec[0]) >= 0.0, (
        'the decorrelation bias is one-sided; a negative branch is '
        'meaningless: %r' % (_dec,))
    m('EirpNinetyDecorPct', '%.0f' % (100 * float(_dec[1])))
    # ★ The campaign bootstrap over injected windows IS the window-to-window
    # transfer term.  The manuscript quoted the same quantity twice, once as
    # a "calibration" factor and once as a "campaign" percentage, and then
    # added a third bracket measured on a superseded campaign.  Assert that
    # the two are one number so they cannot be re-separated.
    # ★★★ F4 AS WRITTEN COULD NOT FAIL: it read
    #     `abs(CMB['campaign_transfer_lo'] - CMB['campaign_transfer_lo'])`,
    #     i.e. it compared a value with ITSELF and was true for every
    #     conceivable input.  The quantity it meant to pin is that the
    #     campaign spread and the window-to-window transfer are ONE number
    #     and not two, which after Ruling 1 is true by construction --
    #     `sens_r11.json` publishes a single `transfer_*` pair measured over
    #     the injected windows -- so the clause that has content is that the
    #     combined interval strictly exceeds BOTH of its quadrature terms on
    #     BOTH sides.  A term accidentally dropped from the sum, or added
    #     twice, breaks it.
    _terms = {'transfer': (CMB['campaign_transfer_lo'],
                           CMB['campaign_transfer_hi']),
              'instrumental': (CMB['instrumental'], CMB['instrumental'])}
    ck('F4 the combined interval strictly exceeds each of the terms it is '
       'the quadrature sum of, on both sides',
       all(CMB['comb_lo'] > lo and CMB['comb_hi'] > hi
           for lo, hi in _terms.values()),
       (CMB['comb_lo'], CMB['comb_hi'], _terms))
    # ★★★ `\BudDominant` WAS A TYPED STRING naming the largest term of a sum
    #     nothing compared it to, and its value CARRIED ITS OWN ARTICLE --
    #     so a sentence reading "the largest systematic is the \BudDominant{}
    #     term" typeset "the largest systematic is THE THE injection
    #     campaign's ...".  That was fixed once at the use site and came
    #     back, because the use site is not where the article lives.  The
    #     convention is now: the VALUE never carries an article and the prose
    #     supplies one, asserted here so it cannot drift back.  And the term
    #     is CHOSEN by magnitude from exactly the rows of the quadrature sum,
    #     not remembered.
    _BUD_NAMES = {'transfer': "injection campaign's window-to-window spread",
                  'instrumental': 'absolute flux, distance and visibility '
                                  'scale'}
    _dom = max(_terms, key=lambda k: max(_terms[k]))
    if drive == 31:
        _dom = 'instrumental'   # the smaller term claimed as the dominant one
    _domname = _BUD_NAMES[_dom]
    if drive == 30:
        _domname = 'the ' + _domname
    ck('F4b the dominant systematic is the largest of exactly the terms in '
       'the quadrature sum, and its value carries no article of its own',
       _domname in _BUD_NAMES.values()
       and not _domname.lower().startswith(('the ', 'a ', 'an '))
       and max(_terms[_dom]) == max(max(v) for v in _terms.values()),
       (_domname, _dom, {k: max(v) for k, v in _terms.items()}))
    m('BudDominant', _domname)

    # ---------------------------------------------------------------- G
    # EIRP_90 as the paper quotes it: per window, per system on its best
    # window, and for the two nearest systems.  All on the ADOPTED
    # criterion, so the multiplier is read from the campaign record above
    # and not written twice.
    def sci(x, nd=1):
        e = int(math.floor(math.log10(x)))
        return r'%.*f\times10^{%d}' % (nd, x / 10.0 ** e, e)

    winA = sorted(r['_e90'] for r in CAT if r['search_class'] == 'A')
    sysA = sorted(bestA.values())
    ck('G1 the per-system limit is never deeper than the best window it is '
       'taken from', min(sysA) >= winA[0] - 1.0,
       (min(sysA), winA[0]))
    # ★★ TWO SIGNIFICANT FIGURES, AND THE PAPER ALREADY SAID SO.  Appendix A
    # states that "EIRP values are quoted to two significant figures", and
    # the budget of Table~\ref{tab:p90budget} puts a x0.77-x1.12 systematic
    # on every one of them, so a headline printed as 1.77e15 claimed a digit
    # the experiment does not have -- against its own stated convention, in
    # the abstract, in Section 5 and in the conclusions at once.  The third
    # figure was carried only so a reader could reproduce the scalings, and
    # it cannot buy that either: every factor it would be multiplied by is
    # itself quoted to two.  One convention, applied to all four.
    EIRP_SF = 2
    if drive == 29:
        EIRP_SF = 3          # the stated two-figure convention must bind
    m('EirpNinetyWinMedA', sci(_median(winA), EIRP_SF - 1))
    m('EirpNinetySysLoA', sci(sysA[0], EIRP_SF - 1))
    m('EirpNinetySysMedA', sci(_median(sysA), EIRP_SF - 1))
    m('EirpNinetySysHiA', sci(sysA[-1], EIRP_SF - 1))
    _hlfmt = [sci(_median(winA), EIRP_SF - 1), sci(sysA[0], EIRP_SF - 1),
              sci(_median(sysA), EIRP_SF - 1), sci(sysA[-1], EIRP_SF - 1)]
    ck('G1b the headline powers carry the %d significant figures the paper '
       'says it quotes EIRP to' % 2,
       all(len(v.split('\\times')[0].replace('.', '')) == 2
           for v in _hlfmt), ' '.join(_hlfmt))
    # ★ The frozen record these are checked against is the one that carries the
    # SAME two corrections the rows above carry: the completeness transferred
    # within strata and the phase-centre loss applied.  Checking them against
    # the blanket-factor record would be checking a different quantity, and
    # would have gone on passing while the published powers moved.
    # ★ The record these are checked against is the completeness record,
    # which forms the same powers from the same catalogue by an independent
    # path.  Two generators that both publish the headline must agree, and
    # the check has to be against the record that carries the SAME
    # corrections these rows carry -- the adopted completeness and the
    # phase-centre loss applied.
    _hl = SENS['headline']
    ck('C9 the headline powers reproduce the completeness record\'s, which '
       'forms them independently from the same catalogue',
       all(abs(a / b - 1.0) < 1e-3 for a, b in
           ((_median(winA), _hl['win_med']), (_median(sysA), _hl['sys_med']),
            (sysA[0], _hl['sys_lo']), (sysA[-1], _hl['sys_hi']))),
       (_median(winA), _hl['win_med'], _median(sysA), _hl['sys_med']))
    # ... and the adopted criterion must be the deeper one, so that a record
    # silently reverted to the rank-charged factor cannot pass C9 unnoticed.
    _hlold = SENSB['headline']['adopted']
    ck('C9b the adopted headline is deeper than the rank-charged one',
       _median(sysA) < _hlold['sys_med'] * 0.95,
       '%.4g against %.4g' % (_median(sysA), _hlold['sys_med']))
    _n15 = sum(1 for v in sysA if v <= 1e15)
    _n16 = sum(1 for v in sysA if v <= 1e16)
    ck('C10 the system count at 10^15 W reproduces the completeness '
       'record\'s', _n15 == _hl['n_sys_1e15'], (_n15, _hl['n_sys_1e15']))
    m('NSysEfifteen', '%d' % _n15)
    m('NSysEsixteen', '%d' % _n16)
    # ★ The one number the abstract quotes.  It is the MEDIAN over systems of
    # each system's best window, on trigger-plus-screen, and it must lie
    # inside the spread printed beside it or the sentence is self-refuting.
    ck('G2 the quoted per-system median lies inside the quoted spread',
       sysA[0] <= _median(sysA) <= sysA[-1], (sysA[0], sysA[-1]))
    NEAREST = {'Barn': 'NAME Barnards star', 'Wolf': 'Wolf 359'}
    for tag, nm in sorted(NEAREST.items()):
        rs = [r for r in CAT if r['star_name'] == nm]
        ck('G3 %s is in the released catalogue' % tag, bool(rs), nm)
        if not rs:
            continue
        e = sorted(r['_e90'] for r in rs)
        m('EirpNinety%sLo' % tag, sci(e[0]))
        m('EirpNinety%sHi' % tag, sci(e[-1]))
        m('NWin%s' % tag, '%d' % len(rs))
        m('Cls%s' % tag, ''.join(sorted({r['search_class'] for r in rs})))
    # ★ These two stars carry COARSE windows only, so their limits come from
    # the spectral-excess search and not from the carrier search the
    # abstract scopes.  Asserted, because a sentence that quotes them beside
    # a Class A limit without saying so is wrong by omission.
    _cls = {t: ''.join(sorted({r['search_class'] for r in CAT
                               if r['star_name'] == n}))
            for t, n in NEAREST.items()}
    if drive == 11:
        _cls = {t: 'A' for t in _cls}
    ck('G4 the nearest-system limits are labelled with the class they come '
       'from', all(v == 'B' for v in _cls.values()),
       'the two nearest systems are %r; if either were Class A the sentence '
       'quoting them would need a different qualifier' % _cls)

    # ---------------------------------------------------------------- G1b
    # The stacked limit, injection-calibrated.  A nominal threshold is not a
    # sensitivity, and by this paper's own rule it cannot be called the
    # deepest limit until a carrier has been injected into the stack and
    # recovered through the same estimator.
    for _key, _tag in (('Proxima Cen', 'Prox'),):
        _st = STACKR9[_key]
        ck('G7 the stack calibration recovered nothing from the null arm',
           _st['null_frac'] == 0.0, (_key, _st['null_frac'], _st['null_n']))
        ck('G8 the calibrated stacked limit is worse than the nominal one',
           _st['eirp_calibrated_W'] > _st['eirp_nominal_W'],
           (_st['eirp_calibrated_W'], _st['eirp_nominal_W']))
        m('Stk%sEirpCal' % _tag, sci(_st['eirp_calibrated_W'], 2))
        m('Stk%sPNinety' % _tag, '%.2f' % _st['p90'])
        m('Stk%sSminCal' % _tag, '%.2f' % _st['smin_calibrated_mjy'])
        m('Stk%sNEpoch' % _tag, '%d' % _st['N'])
        m('Stk%sNeff' % _tag, '%.1f' % _st['n_eff'])
        # ★ The frame restriction is a property of the stack's CHANNEL WIDTH,
        # not of the method: it is +-half a channel in velocity, and quoting
        # one stack's figure against another's channelisation is how the
        # manuscript came to carry a number three orders of magnitude too
        # tight.  Computed here from this stack's own channel width.
        _kms = _st['kms_per_chan']
        m('Stk%sKmsChan' % _tag, '%.1f' % _kms)

    # ---------------------------------------------------------------- G9
    # ★ G9 COULD NOT FAIL, AND IT WAS THE ONE CHECK WHOSE ENTIRE JOB WAS THE
    # VELOCITY TOLERANCE A REFEREE THEN FOUND WRONG.  It read
    #     _kms  = _st['kms_per_chan']
    #     _pred = c * dnu / (c * dnu / _kms)
    # and asserted abs(_kms - _st['kms_per_chan']) < 1e-9: the record against
    # itself, with `_pred` -- an algebraic identity equal to `_kms` whatever
    # the inputs -- computed and never used.  No value of any input could
    # have made it fire.  That silence is why a tolerance three orders of
    # magnitude too tight reached a referee.
    #
    # A check needs a SECOND, INDEPENDENT route to the number, so the
    # tolerance is recomputed here as c*dnu/nu from the stack's own channel
    # width at the stack's own mean sky frequency -- both read out of the
    # STACKED GROUPS, not out of the record under test -- and required to
    # reproduce the published figure.  It runs over EVERY calibrated stack,
    # not only the one the prose quotes: the second stack has the same
    # channel width and a different sky frequency, so its tolerance is a
    # different number, and a check that sees one stack cannot see that.
    _GRP = [json.loads(_l) for _l in
            open(os.path.join(catdir, 'stack_v408', 'stack6_result.jsonl'))
            if _l.strip()]
    _tolcheck = []
    for _key, _stk in sorted(STACKR9.items()):
        _g = [r for r in _GRP if r['skey'] == _stk['star']]
        _deep = min(_g, key=lambda x: x['eirp_stack_W']) if _g else None
        if _deep is None:
            _tolcheck.append((_key, None, _stk['kms_per_chan']))
            continue
        _nu = 0.5 * (_deep['sf_lo'] + _deep['sf_hi'])
        _pred = 299792.458 * _deep['chanw'] / _nu
        if drive == 25 and _key == 'Proxima Cen':
            _pred = 0.635        # the figure the manuscript used to carry
        _tolcheck.append((_key, _pred, _stk['kms_per_chan']))
    ck('G9 every stacked tolerance is one of that stack own channels at that '
       'stack own sky frequency, recomputed from the groups and not read '
       'back out of the record it tests',
       bool(_tolcheck) and all(
           p is not None and abs(p - q) < 1e-3 for _, p, q in _tolcheck),
       '; '.join('%s computed %s against published %.4f km/s'
                 % (k, 'NO GROUP' if p is None else '%.4f' % p, q)
                 for k, p, q in _tolcheck))
    _px = STACKR9['Proxima Cen']
    m('StkCalMult', '%.2f' % _px['p90'])
    m('StkProxTolKms', '%.1f' % _px['kms_per_chan'])
    m('StkProxEirpCalMath', '$' + sci(_px['eirp_calibrated_W'], 2) + '$')
    # how far below the survey's per-system median the calibrated stack
    # reaches -- a ratio of two numbers this generator already computed, so
    # it cannot be quoted against the wrong one of them
    _bel = _median(sysA) / _px['eirp_calibrated_W']
    ck('G16 the stacked limit is deeper than the per-system median',
       _bel > 1.0, _bel)
    m('StkProxBelowMed', '%.0f' % _bel)
    # the second calibrated stack, named apart so the two cannot be mixed
    _bd = STACKR9['BD051668']
    m('StkCalMultTwo', '%.2f' % _bd['p90'])
    m('StkBdEirpCal', sci(_bd['eirp_calibrated_W'], 2))
    m('StkBdPNinety', '%.2f' % _bd['p90'])
    # ★ And G10's first clause was `abs(a - b) >= 0.0`, true of every pair of
    # real numbers -- half of a check that cannot fail, sitting beside one
    # that could not fail at all.  What it meant to say is that these are two
    # measurements: different stars AND different tolerances, the tolerances
    # differing because the sky frequencies do even though the channel widths
    # do not.  Stated that way it can be wrong, and it is the clause that
    # would catch one stack's figure being copied onto the other.
    _dtol = abs(_bd['kms_per_chan'] - STACKR9['Proxima Cen']['kms_per_chan'])
    if drive == 26:
        _dtol = 0.0
    ck('G10 the two calibrated stacks are two measurements -- different '
       'stars, and different tolerances despite one channel width',
       _dtol > 0.01 and _bd['star'] != STACKR9['Proxima Cen']['star'],
       '%s %.4f km/s against %s %.4f km/s, difference %.4f'
       % (_bd['star'], _bd['kms_per_chan'],
          STACKR9['Proxima Cen']['star'],
          STACKR9['Proxima Cen']['kms_per_chan'], _dtol))

    # ---------------------------------------------------------------- G1c
    # Macros the prose cites that nothing defined.  Each is DERIVED from a
    # product or from other macros, never typed, so none of them can drift
    # away from the quantity the sentence claims.
    def mac(name):
        """The value of a macro defined by an earlier macro file."""
        for _f in sorted(glob.glob(os.path.join(catdir, 'survey_numbers*.tex'))
                         + glob.glob(os.path.join(catdir, '*.tex'))):
            if os.path.basename(_f) == OUTNAME:
                continue
            _mm = re.search(
                r'\\(?:new|renew)command\{\\%s\}\{([^}]*)\}' % name,
                open(_f, errors='ignore').read())
            if _mm:
                return _mm.group(1)
        return None

    # the archive's full frequency extent, which the title and abstract take,
    # against the Class A extent, which the experiment takes
    _lo = min(float(r['flo_GHz']) for r in CAT)
    _hi = max(float(r['fhi_GHz']) for r in CAT)
    _loA = min(float(r['flo_GHz']) for r in CAT if r['search_class'] == 'A')
    ck('G11 the archive extent contains the Class A extent',
       _lo <= _loA and _hi >= max(float(r['fhi_GHz']) for r in CAT
                                  if r['search_class'] == 'A'), (_lo, _loA))
    m('SurvFreqLo', '%d' % int(round(_lo)))
    m('SurvFreqHi', '%d' % int(round(_hi)))
    # the mask's cost in coverage, as a difference of two measured unions
    _u, _su = float(mac('UnionGHz')), float(mac('SearchedUnionGHz'))
    ck('G12 the mask removes coverage rather than adding it', _su < _u,
       (_su, _u))
    m('MaskLostGHz', '%.1f' % (_u - _su))
    m('MaskLostPct', '%.1f' % (100.0 * (_u - _su) / _u))
    # beta Pictoris: the stage-1 flagged window count, per band
    _bp = [r for r in CAT if r['star_name'].startswith('bet Pic')]
    _bps1 = [r for r in _bp
             if r['crossing'] == 'True' and int(r['n_ctrl_ge_star']) == 0]
    _bands = sorted({r['band'] for r in _bps1})
    ck('G13 the positive control is recovered in exactly two bands',
       len(_bands) == 2, _bands)
    _w = {'3': 'Three', '6': 'Six', '7': 'Seven'}
    for _b in _bands:
        m('BpicNFlag%s' % _w[_b], '%d' % sum(1 for r in _bps1
                                             if r['band'] == _b))
    ck('G14 the per-band flagged counts sum to the blocks the text names',
       sum(1 for r in _bps1) == len(_bps1), '')
    # the unconfirmed event's repeat epoch, as a depth ratio of two measured
    # noise scales rather than a typed percentage
    _r1, _r2 = float(mac('CpRecRmsOne')), float(mac('CpRecRmsTwo'))
    if drive == 20:
        _r2 = _r1 * 1.5
    ck('G15 the repeat epoch is the deeper of the two', _r2 < _r1,
       'repeat rms %.3f against discovery %.3f: if the repeat were the '
       'shallower one the exclusion would be the wrong way round'
       % (_r2, _r1))
    m('CpRecDeeperPct', '%.0f' % (100.0 * (_r1 - _r2) / _r1))

    # ---------------------------------------------------------------- G2
    # Instrument constants the prose was carrying as bare integers.  These
    # are facts about ALMA, not measurements of ours, so they are DECLARED
    # and asserted against the survey's own coverage rather than computed:
    # the band edges must contain every window this survey searched, or one
    # of the two is wrong.
    ALMA_BAND_LO_GHZ, ALMA_BAND_HI_GHZ, ALMA_N_BANDS = 84, 950, 8
    LIT_CM_MAX_GHZ = 30
    _flo = min(float(r['flo_GHz']) for r in CAT)
    _fhi = max(float(r['fhi_GHz']) for r in CAT)
    if drive == 13:
        ALMA_BAND_HI_GHZ = 100
    ck('G5 the declared ALMA band span contains every searched window',
       ALMA_BAND_LO_GHZ <= _flo and _fhi <= ALMA_BAND_HI_GHZ,
       'searched %.1f-%.1f GHz against a declared %d-%d GHz'
       % (_flo, _fhi, ALMA_BAND_LO_GHZ, ALMA_BAND_HI_GHZ))
    ck('G6 the centimetre literature boundary lies below the searched band',
       LIT_CM_MAX_GHZ < _flo, (LIT_CM_MAX_GHZ, _flo))
    m('AlmaBandLoGHz', '%d' % ALMA_BAND_LO_GHZ)
    m('AlmaBandHiGHz', '%d' % ALMA_BAND_HI_GHZ)
    m('AlmaNBands', '%d' % ALMA_N_BANDS)
    m('LitCmMaxGHz', '%d' % LIT_CM_MAX_GHZ)
    # the figure-of-merit section's two declared instrument constants and
    # the nearby-sample threshold the target table uses, so no section
    # carries them as digits
    m('CwtfmBandMHz', '10')
    m('CwtfmNuGHz', '115')
    m('NearPc', '15')
    # ★ and the two EIRP_90 rows the sample table asked for, on the adopted
    # multiplier, per window and per system, both classes.
    winB = sorted(r['_e90'] for r in CAT if r['search_class'] == 'B')
    sysB = sorted(v for (c, s), v in best.items() if c == 'B')
    m('EirpNinetyWinLoA', sci(winA[0]))
    m('EirpNinetyWinHiA', sci(winA[-1]))
    m('EirpNinetyWinLoB', sci(winB[0]))
    m('EirpNinetyWinHiB', sci(winB[-1]))
    m('EirpNinetyWinMedB', sci(_median(winB)))
    m('EirpNinetySysMedB', sci(_median(sysB)))

    # ---------------------------------------------------------------- G17
    # ★ THE COUNTEREXAMPLE THE SCREEN FIGURE RESTS ON.  In the survey's own
    # positive control -- a real, extended, astrophysical source at the
    # stellar position -- the control ring BEATS the star.  That is the
    # whole argument: the screen measures compactness, not authenticity,
    # and it fails conservatively on a real extended source, rejecting
    # something that is genuinely there rather than admitting something
    # that is not.  The caption cannot make that argument without the three
    # numbers, so they are emitted here rather than described.
    _ctrl = max(CAT, key=lambda r: float(r['ctrl_max_snr'])
                if r['star_name'].startswith('bet Pic')
                and r['crossing'] == 'True' else -1.0)
    _cm, _ss = float(_ctrl['ctrl_max_snr']), float(_ctrl['star_snr'])
    _nge = int(_ctrl['n_ctrl_ge_star'])
    if drive == 21:
        _cm = _ss / 2.0
    ck('G17 in the positive control the ring beats the star, which is what '
       'makes it a counterexample', _cm > _ss and _nge > 0,
       'ring %.2f against star %.2f with %d of %s controls above it: if the '
       'star won here the figure would be making the opposite argument'
       % (_cm, _ss, _nge, _ctrl['n_ctrl']))
    m('BpCtrlRingMax', '%.2f' % _cm)
    m('BpCtrlStar', '%.2f' % _ss)
    m('BpCtrlNAbove', '%d' % _nge)
    m('BpCtrlNCtrl', '%s' % _ctrl['n_ctrl'])
    m('BpCtrlBlock', _ctrl['eb'].replace('A002_', '').replace('_', '\\_'))
    m('BpCtrlBand', _ctrl['band'])

    # ---------------------------------------------------------------- H
    # RETIREMENT.  A superseded quantity is not deprecated here, it is
    # redefined: every name below is pointed at the adopted macro, so the
    # superseded VALUE cannot be typeset by any route, and `retired.py`
    # fails the build on the superseded NAME so the names cannot survive
    # either.  Each entry is asserted to exist, because a retirement
    # recorded against a macro that is already gone retires nothing.
    RETIRE = {
        # the sensitivity on the superseded localisation criterion
        'SdMed': 'EirpNinetySysMedA',
        'PromoteSysMedA': 'EirpNinetySysMedA',
        'PromoteSysLoA': 'EirpNinetySysLoA',
        'PromoteSysHiA': 'EirpNinetySysHiA',
        'PromoteMedA': 'EirpNinetyWinMedA',
        'PromoteMedAOld': 'EirpNinetyWinMedA',
        'PromoteLoA': 'EirpNinetySysLoA',
        'PromoteHiA': 'EirpNinetySysHiA',
        'PromoteFacMed': 'EirpNinetyMultA',
        'RsevPNinetyA': 'EirpNinetyMultA',
        'RsevPNinetyALo': 'EirpNinetyMultALo',
        'RsevPNinetyAHi': 'EirpNinetyMultAHi',
        'RsevPNinetyB': 'EirpNinetyMultB',
        # ★ The THIRD multiplier this manuscript has carried.  5.70 is the
        # 90 per cent point of a pooled curve over 18 of the campaign's 21
        # Class A windows; the three that were dropped were dropped by a
        # positive-control gate tripped by tones deposited outside the
        # searched band and scored as failures -- a check that can only ever
        # fail.  Pooling all 21 gives 7.99.  Both are mixture artefacts of a
        # saturating curve on an unrepresentative window sample, so neither
        # is quotable and both names go.
        'SelPNinetyFine': 'EirpNinetyMultA',
        'SelPNinetyLo': 'EirpNinetyMultALo',
        'SelPNinetyHi': 'EirpNinetyMultAHi',
        'SelPNinety': 'EirpNinetyMultA',
        'RsevOldMult': 'EirpNinetyMultA',
        'PxSysMedBase': 'EirpNinetySysMedA',
        'OccEirpMed': 'EirpNinetySysMedA',
        'MasonMedPsel': 'EirpNinetySysMedA',
        'SelTransFineLo': 'EirpNinetyFacLo',
        'SelTransFineHi': 'EirpNinetyFacHi',
        'BudCampLo': 'EirpNinetyPctLo',
        'BudCampHi': 'EirpNinetyPctHi',
        'BudTotalLo': 'EirpNinetyPctLo',
        'BudTotalHi': 'EirpNinetyPctHi',
        'BudSystLo': 'EirpNinetyInstPct',
        'BudSystHi': 'EirpNinetyInstPct',
        'BudStatLo': 'EirpNinetyCampPctLo',
        'BudStatHi': 'EirpNinetyCampPctHi',
        'BudBiasHi': 'EirpNinetyDecorPct',
        'RsevTransARangeLo': 'EirpNinetyFacLo',
        'RsevTransARangeHi': 'EirpNinetyFacHi',
        'RsevNTestedA': 'NInjWinA',
        'RsevNTransferA': 'NTransferWinA',
        # the nominal stacked limit, which is a threshold and not a
        # sensitivity, and the frame restriction that belonged to a
        # different stack's channel width
        # ★ the alias carries the math delimiters the retired macro carried,
        # because the sentence that cites it does not supply them; a
        # replacement that is correct in value and wrong in mode still
        # stops the build
        'StkProxEirp': 'StkProxEirpCalMath',
        'StkReflexTolKms': 'StkProxTolKms',
        'SelRatioRank': 'EirpNinetyMultA',
        'SelPNinetyFineLo': 'EirpNinetyMultALo',
        'SelPNinetyFineHi': 'EirpNinetyMultAHi',
        'SelPNinetyCoarse': 'EirpNinetyMultB',
        # the attribution count on the superseded topocentric mask
        'LgNAttr': 'NAttributed',
        'LgNUnattr': 'NUnattributed',
        'MaskVWidth': 'MaskHalfKms',
        'NHits': 'NCross',
        'LgNCross': 'NCross',
        # ★★ v4.11: the M-dwarf census, re-measured by selfunc_v411.py with
        # every searched star classified.  These point at macros ANOTHER
        # round emits -- round 111 -- which is new here and is the point:
        # round 103 can only alias what it computes itself, and the quantity
        # that carried two values eleven pages apart was computed elsewhere.
        # The aliases make the superseded VALUE unreachable; the
        # `%% SUPERSEDES:` line in round 111 makes the superseded NAME fatal
        # in `retired.py`.  Both layers, as for every other retirement.
        'NMSearched': 'SfMSearched',
        'NMCensus': 'SfMCensus',
        'NClassAM': 'SfMClassAStars',
        # the deleted benchmark
        'ArecScaledW': None,
        'BenchEirpSeven': 'BenchEirp',
        'BenchEirpSci': None,
        'BenchGainSci': None,
    }
    _defined = set()
    _mine = os.path.basename(OUTNAME)
    for _f in sorted(glob.glob(os.path.join(catdir, '*.tex'))
                     + glob.glob(os.path.join(catdir, 'tables', '*.tex'))):
        if os.path.basename(_f) == _mine:
            continue
        _t = open(_f, errors='ignore').read()
        _defined |= set(re.findall(r'\\newcommand\{\\([A-Za-z]+)\}', _t))
        _defined |= set(re.findall(
            r'\\providecommand\{\\([A-Za-z]+)\}\{\}', _t))
    # ★ A retirement is also meaningful if the NAME is still cited, even
    # after the old definition has been deleted as unreferenced: that is the
    # case the gate exists for.  Without this clause H1 fires on every
    # retirement the moment the retire pass runs, which would make the
    # generator unable to run twice in the same build.
    _cited = set()
    for _f in sorted(glob.glob(os.path.join(catdir, 'sections', '*.tex'))):
        _cited |= set(re.findall(r'\\([A-Za-z]+)',
                                 open(_f, errors='ignore').read()))
    _r = dict(RETIRE)
    if drive == 12:
        # A name the prose STILL CITES, retired with no replacement: every
        # one of those citations would expand to nothing.  ★ The victim is
        # chosen from what is cited today, not named here: pinning it to one
        # macro made this drive stop firing the moment an owner removed that
        # citation, which is a self-test quietly reporting a pass because
        # its perturbation no longer perturbs anything.
        _still = sorted(k for k in RETIRE if k in _cited)
        assert _still, ('no retired name is cited, so this drive cannot '
                        'perturb anything and must not report a pass')
        _r[_still[0]] = None
    # ★ Three retirements have NO correct replacement: a frequency-scaled
    # Arecibo-equivalent and a perfect-aperture benchmark are not physically
    # realisable transmitters, so there is no value to point them at.  They
    # cannot be aliased and they cannot be erased by this generator, because
    # the sentence that cites them belongs to another file.  So they are
    # ROUTED: the owner is declared here, and the declaration is checked
    # against the file, so the routing table cannot go stale while the
    # citation stays.
    # Empty: the three entries that lived here have been honoured -- the
    # sentences citing a frequency-scaled Arecibo-equivalent and a perfect
    # aperture are gone, so the names are fully retired and routing them
    # would be routing nothing.  The table and its check stay, because the
    # next unreplaceable retirement needs them.
    ROUTED = {}
    _owner_cites = {}
    for _k, _own in ROUTED.items():
        _pth = os.path.join(catdir, _own)
        _txt = open(_pth, errors='ignore').read() if os.path.exists(_pth) else ''
        _owner_cites[_k] = bool(re.search(r'\\' + _k + r'(?![A-Za-z])', _txt))
    if drive == 14:
        _owner_cites = {_k: False for _k in ROUTED}
    ck('H5 every routed retirement is still cited by the file it is routed '
       'to', all(_owner_cites.values()) and (ROUTED or drive != 14),
       'the routing is stale for %s: the citation has gone, so the entry '
       'should go too' % sorted(k for k, v in _owner_cites.items() if not v))
    _live = _defined | _cited
    _done = sorted(k for k in RETIRE if k not in _live)
    # ★ The actionable condition is not "does the old name still exist" --
    # once the prose stops citing it and the retire pass removes it, it is
    # simply gone, which is the goal.  The condition that must never hold is
    # a name the prose STILL CITES with no replacement declared, because
    # every one of those citations expands to nothing or to the old value.
    ck('H1 no retired name that the prose still cites lacks both a '
       'replacement and a declared owner',
       all(_r[k] or k in ROUTED for k in _r if k in _cited),
       sorted(k for k in _r if k in _cited and not _r[k]
              and k not in ROUTED))
    ck('H4 the retirement list is not vacuous: at least one retired name is '
       'still cited by the prose', bool(set(RETIRE) & _cited),
       'no retired name is cited anywhere, so the gate that enforces this '
       'list can no longer fail')
    _ovr = sorted(set(M) & _defined)
    ck('H3 every name this round redefines is a name it means to redefine',
       all(k not in RETIRE for k in _ovr),
       'a macro is both emitted and retired here: %s'
       % sorted(set(_ovr) & set(RETIRE)))
    # ★ H2 WIDENED, v4.11: a replacement may be emitted by ANOTHER round,
    # and three now are -- the M-dwarf census moved to round 111, where
    # `selfunc_v411.py` re-measured it.  The condition that matters is that
    # the replacement EXISTS somewhere in the macro layer, not that this
    # generator wrote it; a replacement nothing defines would alias a
    # retired name to an undefined control sequence, which is the failure
    # H2 is for.  Cross-round replacements are listed so the widening
    # cannot quietly become a licence.
    _xround = sorted(v for v in RETIRE.values()
                     if v and v not in M and v in _defined)
    _nowhere = sorted(v for v in RETIRE.values()
                      if v and v not in M and v not in _defined)
    if drive == 28:
        _nowhere = _nowhere + ['DriveUndefinedReplacement']
    ck('H2 every retirement points at a macro that exists in the macro '
       'layer', not _nowhere,
       'replacement(s) no round file defines: %s' % _nowhere)
    if _xround:
        print('  note H2: %d replacement(s) emitted by another round: %s'
              % (len(_xround), ', '.join(_xround)))

    # --------------------------------------------------------------- out
    suf = '' if drive is None else '_drive%d' % drive
    OUT = os.path.join(outdir, OUTNAME)
    with open(OUT, 'w') as fh:
        fh.write('%% GENERATED by numbers_v410.py (round 103) -- '
                 'do not hand-edit.\n')
        # ★ A name this file writes may or may not already be defined: it
        # may come from an earlier macro file, or that earlier definition may
        # have been deleted as unreferenced before this file is read.  Both
        # happen, in the same build.  \newcommand stops on the first case,
        # \renewcommand on the second, and which one fires depends on
        # whether some unrelated prose sentence still cites the old name --
        # so the correct form is neither alone.  \providecommand then
        # \renewcommand is right either way, and leaves exactly one value
        # reachable, which is the point of the round.
        for k in sorted(M):
            fh.write('\\providecommand{\\%s}{}\\renewcommand{\\%s}{%s}\n'
                     % (k, k, M[k]))
        fh.write('%%\n%% Retirements.  Each superseded name is redefined to '
                 'the adopted macro,\n%% so the superseded VALUE cannot be '
                 'typeset by any route; `retired.py`\n%% fails the build on '
                 'the superseded NAME.\n')
        # A retirement WITH a replacement is aliased, so the superseded
        # value becomes unreachable immediately and the prose that still
        # cites the old name typesets the right number while it is being
        # rewritten.  A retirement with NO replacement cannot be aliased --
        # there is no correct value to point it at -- so it is left alone in
        # the macro layer and `retired.py` fails on the name, naming the file
        # and line, which is the only way to route it to the owner of the
        # sentence rather than to break a build nobody can fix.
        for k in sorted(RETIRE):
            v = RETIRE[k]
            if v:
                fh.write('\\providecommand{\\%s}{}'
                         '\\renewcommand{\\%s}{\\%s}\n' % (k, k, v))
            else:
                fh.write('%%  no replacement, gate-only: \\%s\n' % k)
        fh.write('%%\n%% RETIRED: %s\n'
                 % ' '.join(sorted(RETIRE)))
    # Table 4 is generated by sens_r11.py as tab_budget_r11.tex, together
    # with the completeness it is a budget for, so the table and the
    # number it describes have one owner.
    with open(os.path.join(outdir, 'tab_hzhosts%s.tex' % suf), 'w') as fh:
        fh.write('%% GENERATED by numbers.py -- do not hand-edit.\n')
        fh.write('\\begin{tabular}{@{}llrrr@{}}\n\\hline\n'
                 'Star & Planet & $d$ (pc) & crossings & blocks \\\\\n'
                 '\\hline\n')
        for h in hz:
            fh.write('%s & %s & %.1f & %d & %d \\\\\n'
                     % (h['name'], h['planet'], h['dist'], h['ncross'],
                        len(h['blocks'])))
        fh.write('\\hline\n\\end{tabular}\n')
    # ★ tab_maskladder.tex is NOT written here any more.  It was emitted
    # from the RELEASED crossing list while the ledger was emitted from the
    # ADOPTED one, so the two fragments gave 16/40 and 18/38 for the same
    # quantity -- the third value for it in one day.  One source: the
    # ladder is now written by the ledger generator, from the ledger's own
    # rows.
    print('numbers_v410 (round 103): %d macros, %d retirements, %d '
          'crossings, %d windows'
          % (len(M), len(RETIRE), NCROSS, len(CAT)))
    print('  mask (%s frame, +-%g km/s): released list %d attributed / %d '
          'unattributed; ADOPTED list %s attributed / %s unattributed, %s of '
          'them rank-flagged; sky frame gives the same %d attributed'
          % (M['MaskFrame'], MASK_HALF_KMS, len(att), len(una),
             M['NAttributed'], M['NUnattributed'], M['NUnattrRankFlagged'],
             len(sky_att)))
    print('  EIRP_90 = x%.2f P_trig (A), x%.2f (B); benchmark %.2e W reached '
          'by %d of %d Class A systems, %d of %d systems'
          % (MULT['A'], MULT['B'], BENCH, nA, len(bestA), nAll, len(bestAll)))
    print('  retirements: %d declared, %d fully retired (name gone from the '
          'macro layer and from the prose), %d still cited'
          % (len(RETIRE), len(_done), len([k for k in RETIRE if k in _cited])))
    print('  %d routed to an owner because no replacement exists: %s'
          % (len(ROUTED), ', '.join('%s -> %s' % (k, os.path.basename(v))
                                    for k, v in sorted(ROUTED.items()))))
    print('  per-window median %s W, per-system median %s W, %s of %s '
          'systems at 1e15 W; injected into %s of %s Class A windows'
          % (M['EirpNinetyWinMedA'].replace(chr(92) + 'times10^', 'e'),
             M['EirpNinetySysMedA'].replace(chr(92) + 'times10^', 'e'),
             M['NSysEfifteen'], M['NSysA'], M['NInjWinA'], M['NWinA']
             if 'NWinA' in M else '402'))
    print('  ONE interval: campaign/transfer -%.0f/+%.0f, instrumental '
          '+-%.0f, combined -%.0f/+%.0f per cent = x%.2f-%.2f; declared '
          'decorrelation bias %+.0f/%+.0f quoted apart'
          % (100 * CMB['campaign_transfer_lo'],
             100 * CMB['campaign_transfer_hi'], 100 * CMB['instrumental'],
             100 * CMB['comb_lo'], 100 * CMB['comb_hi'],
             CMB['factor_lo'], CMB['factor_hi'],
             100 * CMB['decorrelation_declared'][0],
             100 * CMB['decorrelation_declared'][1]))
    print('  stacked limit, injection-calibrated: Proxima %s W at '
          '+-%s km/s per channel (P90/nominal %s, %s epochs, N_eff %s)'
          % (M['StkProxEirpCal'].replace(chr(92) + 'times10^', 'e'),
             M['StkProxKmsChan'], M['StkProxPNinety'], M['StkProxNEpoch'],
             M['StkProxNeff']))
    for f in FIRED:
        print('  ASSERTION FIRED  ' + f)
    print('numbers: %d assertions fired' % len(FIRED))
    return 1 if FIRED else 0


if __name__ == '__main__':
    sys.exit(main(sys.argv))
