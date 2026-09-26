#!/usr/bin/env python3
r"""Round 92 (v4.05): the cross-target frequency-occupancy screen, corrected,
and the withdrawal of the z = 3.5 "population-level excess".

`/data/SETI/bin/frequency_occupancy.py` is the pipeline's only module
dedicated to interference rejection.  As shipped it did

    target_dir = path.split('/')[3]

which, for "/data/SETI/targets/<TARGET>/products/<f>.json", is the literal
string 'targets'.  Every record received the same key, the module's
`len(targets_in_group) >= 2` test was never satisfiable, and the module
reported ZERO coincidence clusters FOR ANY INPUT.  Its stored report
(2026-09-01, \RfiOccStaleN{} windows, \RfiOccStaleClusters{} clusters) is
that bug, not a measurement, and is stale by a factor of 21 in window count.

The repaired `[3] -> [4]` pass reported a z = 3.5 excess of cross-target
sky-frequency coincidences.  THAT RESULT IS WITHDRAWN HERE, and the reason
is a third defect of the same family: index 4 is the target DIRECTORY, and
\RfiOccNEbDirs{} of the \RfiOccNWin{} records live in directories named
<star>_B<band>_EB_<execution block>.  \RfiOccNDirs{} directories correspond
to only \RfiOccNStars{} stars, so a star's own repeat blocks counted as
different "targets" -- and a persistent feature, a real molecular line most
of all, recurs across a star's own blocks at the same sky frequency.  The
direction of the error is to INFLATE the coincidence count.

This generator does three things, in order, and asserts each:

  1. it REPRODUCES the result it is withdrawing.  Keyed on the directory,
     as the repaired module is, the greedy statistic gives \RfiOccDirObs{}
     against \RfiOccDirNull{} +- \RfiOccDirNullSd{} (z = \RfiOccDirZ),
     confirming the arithmetic of that pass from an independent
     implementation;
  2. it re-keys on the STAR, by an explicit merge table and not a regex,
     giving \RfiOccObs{} against \RfiOccNull{} +- \RfiOccNullSd{}
     (z = \RfiOccZ) -- the whole of the effect was the key;
  3. it nulls on each window's own CHANNEL GRID rather than continuously,
     because all \RfiOccNWin{} peaks lie exactly on their window's grid.
     (Same defect as Appendix M; here it is worth <~0.5 in z, and is fixed
     rather than argued about.)

Among the \RfiOccSigN{} windows carrying a peak above 5 sigma the corrected
count is \RfiOccSigObs{} against \RfiOccSigNull{} +- \RfiOccSigNullSd{}
(z = \RfiOccSigZ), i.e. BELOW the null; \RfiOccMaskN{} of those windows sit
on a masked molecular transition, and with the +-50 km/s mask applied the
order-independent count is \RfiOccMskCoObs{} against \RfiOccMskCoNull{} +-
\RfiOccMskCoNullSd{}.  A CO line lands at nearly the same TOPOCENTRIC
frequency toward every nearby star, so cross-star frequency coincidence is
exactly what real line emission produces: the screen cannot tell that from
interference unless the mask is applied first.

The paper's sentence -- "no sky-frequency or intermediate-frequency
clustering of the crossing population" -- is therefore now actually
supported, and by a screen with a stated null rather than by a module that
could not report a coincidence.

_provenance
-----------
Input `occupancy_windows.csv` in THIS directory is a verbatim copy of the
9-column extract made on the host from its 3,027 per-window result files
`/data/SETI/targets/*/products/*_result.json` (columns: target directory,
execution block, window edges flo/fhi in GHz, nchan, chanw in Hz, peak
frequency peakf in GHz, peak SNR, resolution class).  It is an extract only:
no re-processing, no re-fetch, no filtering.  It was produced for the
round-8 referee item 5 investigation and copied here unchanged
(md5 6bfb854eac137ed9f9ee13757b9602cb) so that this generator is
self-contained inside the version directory.  Nothing outside this directory
is read; the 15-transition search list is parsed out of `v342_calc.py`, the
generator that owns it, so the two cannot drift apart.

-> survey_numbers_round92.tex, freqocc_v405.json
"""
import csv
import decimal
import json
import os
import random
import re
import statistics

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, 'survey_numbers_round92.tex')
JSONOUT = os.path.join(HERE, 'freqocc_v405.json')
SRC = os.path.join(HERE, 'occupancy_windows.csv')

TOL_MHZ = 5.0          # the module's own coincidence tolerance
NDRAW = 400            # null draws per subset
SIG = 5.0              # "significant peak" threshold, in sigma
MASK_HALF = 50.0       # the survey's frozen line-mask half-width, km/s
C_KMS = 299792.458

# ONE RNG, ONE STREAM, ONE FIXED SEED, CONSUMED IN A FIXED ORDER.
# `random.Random` rather than `numpy.random.default_rng` deliberately: this
# is a port of the round-8 measurement and the stream is kept identical to
# it, so every number in this file is bit-for-bit the number that was
# reported and reviewed.  A different generator would move the null mean by
# ~0.7 (the Monte Carlo error on 400 draws) and could flip \RfiOccNull
# between 554 and 555 without anything being wrong.  Determinism across
# runs -- what the clean-regeneration gate checks -- is guaranteed either
# way by the fixed seed and the fixed consumption order; this choice buys
# reproducibility against the REPORT as well as against the last build.
SEED = 20260926

# The stored report of the broken module, for the withdrawal sentence.
STALE = dict(n_windows=144, n_clusters=0, date='2026-09-01')

# The repaired-module pass whose z = 3.5 is being withdrawn.  Reproducing it
# is a precondition for withdrawing it: see the assertion below.
SHIPPED_DIRKEY = dict(observed=680, null_mean=630.6, null_sd=14.3, z=3.5)

# The four stars that appear under TWO Gaia source ids in the directory
# tree.  Merged by an EXPLICIT TABLE and not by a regex, because stripping
# every trailing numeric id collapses HD_10647, HD_285968, ... to the bare
# prefix 'HD' and all 45 GaiaDR3_* to 'GaiaDR3'.  That trap was hit during
# the round-8 work; it merges ~53 distinct stars and DEFLATES the count.
SAME_STAR = {
    '2MASS_J05241914-1601153_717696': '2MASS_J05241914-1601153_551040',
    'HD_139084B_921024': 'HD_139084B_805632',
    'LP_476-207_783296': 'LP_476-207_384128',
    'TWA_3A_696000': 'TWA_3A_576064',
}

M = {}


def m(k, v):
    M[k] = v


def tex(v, fmt='%.1f'):
    """A LaTeX-safe number.  These macros are used in TEXT mode, so a leading
    ASCII hyphen would typeset as a hyphen, not a minus.  House style is the
    math minus (cf. \\SmearList's `CP$-$72`)."""
    s = fmt % v
    return ('$' + s + '$') if s.startswith('-') else s


def pct2(p):
    """A Monte Carlo p-value to two places, rounded HALF UP.  '%.2f' % 0.145
    gives 0.14, because 0.145 is not representable; the tail fraction 58/400
    is exactly 0.145 and must print as 0.15."""
    return '%.2f' % (decimal.Decimal(repr(p)).quantize(
        decimal.Decimal('0.01'), rounding=decimal.ROUND_HALF_UP))


def base_key(target_dir):
    """The directory with the execution block and the band stripped -- the
    star, BEFORE the duplicate-source-id merge."""
    s = re.sub(r'_EB_[0-9A-Za-z]+$', '', target_dir)
    return re.sub(r'_B\d+$', '', s)


def star_key(target_dir):
    """THE MODULE'S KEY IS NOT THE STAR.  Strip the execution block and the
    band, then merge the four stars carrying two source ids."""
    return SAME_STAR.get(base_key(target_dir), base_key(target_dir))


def naive_star_key(target_dir):
    """The trap, kept live so the assertion below can show it is NOT used:
    strip every trailing numeric id with a regex."""
    return re.sub(r'_\d+$', '', base_key(target_dir))


def greedy_clusters(pairs):
    """The module's own statistic, reproduced exactly: sort by frequency,
    walk forward absorbing everything within TOL of the GROUP HEAD, count
    groups spanning >= 2 distinct keys."""
    pairs = sorted(pairs)
    n, used, out = len(pairs), [False] * len(pairs), 0
    for i in range(n):
        if used[i]:
            continue
        f0, k0 = pairs[i]
        grp, used[i], j = [k0], True, i + 1
        while j < n and (pairs[j][0] - f0) * 1e3 < TOL_MHZ:
            grp.append(pairs[j][1])
            used[j] = True
            j += 1
        if len(set(grp)) >= 2:
            out += 1
    return out


def coincident_windows(pairs):
    """Order-independent alternative: how many windows have their peak within
    TOL of the peak of a window belonging to a DIFFERENT key.  Symmetric, so
    insensitive to the greedy walk's arbitrary choice of group heads."""
    pairs = sorted(pairs)
    n, hit = len(pairs), [False] * len(pairs)
    for i in range(n):
        j = i + 1
        while j < n and (pairs[j][0] - pairs[i][0]) * 1e3 < TOL_MHZ:
            if pairs[j][1] != pairs[i][1]:
                hit[i] = hit[j] = True
            j += 1
    return sum(hit)


# =====================================================================
# the 15-transition search list, from the generator that owns it
# =====================================================================
_src = open(os.path.join(HERE, 'v342_calc.py')).read()
_i = _src.index('CAT_OLD = {')
_j = _src.index('}', _i)
CAT_OLD = eval(_src[_i + len('CAT_OLD = '):_j + 1])                # noqa: S307
# If this list ever stops being the list the SEARCH ran, the masked/unmasked
# split below stops meaning what the prose says it means.
assert len(CAT_OLD) == 15, len(CAT_OLD)
assert abs(CAT_OLD['CO(2-1)'] - 230.538) < 1e-9, CAT_OLD['CO(2-1)']

# =====================================================================
# the input extract
# =====================================================================
rows = []
for r in csv.DictReader(open(SRC)):
    try:
        lo, hi = float(r['flo']), float(r['fhi'])
        f, s = float(r['peakf']), float(r['peaksnr'])
    except (TypeError, ValueError):
        continue
    n = int(r['nchan'])
    w = (hi - lo) / (n - 1)        # SIGNED: descending spws have hi < lo
    rows.append(dict(dir=r['target'], star=star_key(r['target']),
                     lo=min(lo, hi), hi=max(lo, hi), f=f, snr=s, n=n,
                     f0=lo, dw=w, rescls=r['rescls'],
                     cls=('A' if r['rescls'].startswith('fine') else 'B')))

# The extract is the whole searched set.  If this shrinks, the screen is no
# longer "over all searched windows" and the prose must change with it.
assert len(rows) == 3027, len(rows)

# The peak must lie inside its own window, or the within-window null is not
# the right null for it.
strays = [r for r in rows if not (r['lo'] - 1e-6 <= r['f'] <= r['hi'] + 1e-6)]
assert not strays, 'peak outside its window: %d' % len(strays)

# THE NULL MUST LIVE ON THE SAME GRID AS THE STATISTIC.  Every peak must lie
# exactly on its window's channel grid f_k = flo + k (fhi - flo)/(nchan - 1),
# because the null below draws a CHANNEL.  If this ever fails, the null is
# continuous where the statistic is discrete -- precisely the defect that
# made Appendix M's p = 0.01 meaningless.
gridoff = [abs((r['f'] - r['f0']) / r['dw']
               - round((r['f'] - r['f0']) / r['dw'])) for r in rows]
GRID_WORST = max(gridoff)
assert GRID_WORST < 1e-3, GRID_WORST
n_ongrid = sum(1 for g in gridoff if g < 1e-3)
assert n_ongrid == len(rows), (n_ongrid, len(rows))

n_dirs = len({r['dir'] for r in rows})
n_stars = len({r['star'] for r in rows})
n_base = len({base_key(r['dir']) for r in rows})
n_naive = len({naive_star_key(r['dir']) for r in rows})
n_eb = sum(1 for r in rows if re.search(r'_EB_[0-9A-Za-z]+$', r['dir']))
# The resolution classes, counted as the catalogue labels them rather than
# through the binary fine/not-fine split the statistic uses: the screen is
# mostly a statement about continuum windows whose "peak" is a noise
# maximum, and that is only true because most windows are coarse.
n_coarse = sum(1 for r in rows if r['rescls'].startswith('coarse'))
n_fine = sum(1 for r in rows if r['rescls'].startswith('fine'))
n_medium = sum(1 for r in rows if r['rescls'].startswith('medium'))
n_unlab = sum(1 for r in rows if not r['rescls'].strip())
# If the four labels stop partitioning the extract, the sentence "2,294 of
# the 3,027 windows are coarse" has an unaccounted remainder.
assert n_coarse + n_fine + n_medium + n_unlab == len(rows), \
    (n_coarse, n_fine, n_medium, n_unlab)
assert n_coarse > len(rows) // 2, n_coarse
med_snr = statistics.median(r['snr'] for r in rows)

# THE KEY IS THE WHOLE POINT OF THIS GENERATOR, so the key must be checked.
# (i) the merge table must actually bite: all four duplicate ids must be
#     present in the unmerged key set, and the merge must remove exactly
#     four keys.  If a directory is ever renamed, this fails loudly rather
#     than silently reporting 137 stars.
for _dup, _canon in SAME_STAR.items():
    assert _dup in {base_key(r['dir']) for r in rows}, _dup
    assert _canon in {base_key(r['dir']) for r in rows}, _canon
assert n_stars == n_base - len(SAME_STAR), (n_stars, n_base)
# (ii) the naive regex must NOT be what is used.  If these ever agree, the
#      merge has silently become the trap and 50-odd distinct stars have
#      been collapsed into 'HD' and 'GaiaDR3'.
assert n_naive < n_stars - 40, (n_naive, n_stars)
assert naive_star_key('HD_10647_B6_EB_X161a') == 'HD', \
    naive_star_key('HD_10647_B6_EB_X161a')
assert naive_star_key('HD_285968_B6_EB_X22c') == 'HD'
assert star_key('HD_10647_B6_EB_X161a') == 'HD_10647'
assert star_key('HD_285968_B6_EB_X22c') == 'HD_285968'

# =====================================================================
# which peaks sit on a masked molecular transition
# =====================================================================
# A CO(2-1) line lands at nearly the SAME topocentric frequency toward every
# nearby star, so a cross-star frequency coincidence is exactly what real
# line emission produces.  The screen cannot tell that from interference
# unless the mask is applied, so the significant subset is decomposed.
for r in rows:
    best = min(CAT_OLD,
               key=lambda k: abs(C_KMS * (r['f'] - CAT_OLD[k]) / CAT_OLD[k]))
    r['line'] = best
    r['dv'] = C_KMS * (r['f'] - CAT_OLD[best]) / CAT_OLD[best]
    r['masked'] = abs(r['dv']) <= MASK_HALF

sig = [r for r in rows if r['snr'] > SIG]
sig_masked = [r for r in sig if r['masked']]
species = {}
for r in sig_masked:
    species[r['line']] = species.get(r['line'], 0) + 1
# The decomposition must not be vacuous in either direction: if NO
# significant window were masked the "it is line emission" explanation would
# be untested, and if ALL were, the masked subset would be empty.
assert 0 < len(sig_masked) < len(sig), (len(sig_masked), len(sig))
assert sum(species.values()) == len(sig_masked)

out = dict(seed=SEED, n_windows=len(rows), n_target_dirs=n_dirs,
           n_base_keys=n_base, n_stars=n_stars, n_naive_keys=n_naive,
           n_dirs_with_eb=n_eb, n_coarse=n_coarse, n_fine=n_fine,
           n_medium=n_medium, n_unlabelled_rescls=n_unlab,
           median_peak_snr=round(med_snr, 2), grid_worst_channel=GRID_WORST,
           tol_MHz=TOL_MHZ, n_draws=NDRAW, sig_threshold=SIG,
           mask_half_kms=MASK_HALF, stale_report=STALE,
           shipped_dirkey=SHIPPED_DIRKEY, n_sig=len(sig),
           n_sig_line_masked=len(sig_masked), sig_line_species=species,
           subsets={})

# =====================================================================
# the statistic and its null, five subsets
# =====================================================================
# Order fixed: the single RNG stream is consumed subset by subset, so the
# tuple below is part of the result's definition.  Do not reorder it.
rng = random.Random(SEED)
for tag, sub, key in (('all_windows', rows, 'star'),
                      ('peak_gt_5sigma', sig, 'star'),
                      ('peak_gt_5sigma_line_removed',
                       [r for r in sig if not r['masked']], 'star'),
                      ('all_windows_line_removed',
                       [r for r in rows if not r['masked']], 'star'),
                      ('all_windows_dirkey', rows, 'dir')):
    assert sub, tag
    obs_g = greedy_clusters([(r['f'], r[key]) for r in sub])
    obs_c = coincident_windows([(r['f'], r[key]) for r in sub])
    ng, nc, cg, cc = [], [], [], []
    for _ in range(NDRAW):
        # GRID null: draw a channel, not a frequency
        pg = [(r['f0'] + rng.randrange(r['n']) * r['dw'], r[key]) for r in sub]
        ng.append(greedy_clusters(pg))
        nc.append(coincident_windows(pg))
        # the module's implicit CONTINUOUS null, kept for comparison
        pc = [(rng.uniform(r['lo'], r['hi']), r[key]) for r in sub]
        cg.append(greedy_clusters(pc))
        cc.append(coincident_windows(pc))
    mg, sg = statistics.mean(ng), statistics.pstdev(ng)
    mc, sc = statistics.mean(nc), statistics.pstdev(nc)
    mcg, scg = statistics.mean(cg), statistics.pstdev(cg)
    mcc, scc = statistics.mean(cc), statistics.pstdev(cc)
    # A null with zero spread cannot support a z at all.  If a subset ever
    # degenerates this way, its z must not be quoted.
    assert sg > 0 and sc > 0, (tag, sg, sc)
    out['subsets'][tag] = dict(
        n=len(sub), key=key,
        continuous_null=dict(
            greedy_mean=round(mcg, 1), greedy_sd=round(scg, 1),
            greedy_z=round((obs_g - mcg) / scg, 2),
            coincident_mean=round(mcc, 1), coincident_sd=round(scc, 1),
            coincident_z=round((obs_c - mcc) / scc, 2)),
        greedy=dict(observed=obs_g, null_mean=round(mg, 1),
                    null_sd=round(sg, 1), z=round((obs_g - mg) / sg, 2),
                    p_ge_obs=sum(1 for v in ng if v >= obs_g) / NDRAW,
                    excess_pct=round(100 * (obs_g / mg - 1), 1)),
        coincident=dict(observed=obs_c, null_mean=round(mc, 1),
                        null_sd=round(sc, 1), z=round((obs_c - mc) / sc, 2),
                        p_ge_obs=sum(1 for v in nc if v >= obs_c) / NDRAW,
                        excess_pct=round(100 * (obs_c / mc - 1), 1)))

A = out['subsets']['all_windows']
B = out['subsets']['peak_gt_5sigma']
Cm = out['subsets']['peak_gt_5sigma_line_removed']
D = out['subsets']['all_windows_dirkey']

# =====================================================================
# the falsifiers that make the withdrawal a measurement
# =====================================================================
# (1) REPRODUCE BEFORE WITHDRAWING.  Keyed on the directory -- what the
#     repaired module does -- this independent implementation must recover
#     the pass being withdrawn: the same observed count, a null consistent
#     with its 630.6 +- 14.3, and an excess above 3 sigma.  If this fails we
#     are not withdrawing that result, we are contradicting it with an
#     implementation that does something else, and the withdrawal is not
#     supported.
assert D['greedy']['observed'] == SHIPPED_DIRKEY['observed'], \
    (D['greedy']['observed'], SHIPPED_DIRKEY['observed'])
assert abs(D['greedy']['null_mean'] - SHIPPED_DIRKEY['null_mean']) < 8.0, \
    D['greedy']['null_mean']
assert D['greedy']['z'] > SHIPPED_DIRKEY['z'], (D['greedy']['z'],)

# (2) THE WHOLE OF THE EFFECT IS THE KEY.  Same rows, same statistic, same
#     null, same tolerance: only the grouping key changes.  The directory
#     key must be significant and the star key must not.  If both were
#     significant the defect would not explain the excess and the paper
#     would have to report a real one; if neither were, there would be
#     nothing to withdraw.
assert D['greedy']['z'] > 3.0, D['greedy']['z']
assert abs(A['greedy']['z']) < 2.0, A['greedy']['z']
assert D['greedy']['observed'] > A['greedy']['observed'], \
    (D['greedy']['observed'], A['greedy']['observed'])

# (3) The claim the PAPER makes is about the significant subset, so it is
#     asserted separately: there the corrected count must not exceed its
#     null.  This is the sentence "finds no excess of cross-star
#     coincidences among the windows carrying a significant peak"; if it
#     ever fails, that sentence is false and must not be typeset.
assert B['greedy']['z'] < 1.0, B['greedy']['z']
assert Cm['coincident']['z'] < 1.0, Cm['coincident']['z']

# (4) The windows driving the residual all-window excess are noise, not
#     signal: their peak SNR median must sit far below the 5 sigma trigger.
assert med_snr < 4.0, med_snr

# =====================================================================
# macros
# =====================================================================
m('RfiOccNWin', '%d' % len(rows))
m('RfiOccNStars', '%d' % n_stars)
m('RfiOccNDirs', '%d' % n_dirs)
m('RfiOccNEbDirs', '%d' % n_eb)
m('RfiOccNaiveStars', '%d' % n_naive)
m('RfiOccNCoarse', '%d' % n_coarse)
m('RfiOccNFine', '%d' % n_fine)
m('RfiOccMedSnr', '%.1f' % med_snr)
m('RfiOccTol', '%g' % TOL_MHZ)
m('RfiOccNDraw', '%d' % NDRAW)
m('RfiOccMaskHalf', '%g' % MASK_HALF)

# all windows, star key -- the greedy (module's own) statistic
m('RfiOccObs', '%d' % A['greedy']['observed'])
m('RfiOccNull', '%.0f' % A['greedy']['null_mean'])
m('RfiOccNullSd', '%.0f' % A['greedy']['null_sd'])
m('RfiOccZ', tex(A['greedy']['z']))
m('RfiOccP', pct2(A['greedy']['p_ge_obs']))
m('RfiOccExcessPct', tex(A['greedy']['excess_pct']))
# all windows, star key -- the order-independent statistic.  It DISAGREES
# with the greedy one (z ~ 3 against z ~ 1) and is published rather than
# resolved: the symmetric count is the more sensitive to many small
# coincidences, the greedy one to large groups.
m('RfiOccCoObs', '%d' % A['coincident']['observed'])
m('RfiOccCoNull', '%.0f' % A['coincident']['null_mean'])
m('RfiOccCoNullSd', '%.0f' % A['coincident']['null_sd'])
m('RfiOccCoZ', tex(A['coincident']['z']))

# windows with a peak above 5 sigma -- the subset the paper depends on
m('RfiOccSigN', '%d' % B['n'])
m('RfiOccSigObs', '%d' % B['greedy']['observed'])
m('RfiOccSigNull', '%.1f' % B['greedy']['null_mean'])
m('RfiOccSigNullSd', '%.1f' % B['greedy']['null_sd'])
m('RfiOccSigZ', tex(B['greedy']['z']))
m('RfiOccSigP', pct2(B['greedy']['p_ge_obs']))
m('RfiOccSigCoObs', '%d' % B['coincident']['observed'])
m('RfiOccSigCoNull', '%.1f' % B['coincident']['null_mean'])
m('RfiOccSigCoNullSd', '%.1f' % B['coincident']['null_sd'])
m('RfiOccSigCoZ', tex(B['coincident']['z']))

# ... the same subset with the +-50 km/s line mask applied
m('RfiOccMaskN', '%d' % len(sig_masked))
m('RfiOccMskN', '%d' % Cm['n'])
m('RfiOccMskObs', '%d' % Cm['greedy']['observed'])
m('RfiOccMskNull', '%.1f' % Cm['greedy']['null_mean'])
m('RfiOccMskNullSd', '%.1f' % Cm['greedy']['null_sd'])
m('RfiOccMskZ', tex(Cm['greedy']['z']))
m('RfiOccMskCoObs', '%d' % Cm['coincident']['observed'])
m('RfiOccMskCoNull', '%.1f' % Cm['coincident']['null_mean'])
m('RfiOccMskCoNullSd', '%.1f' % Cm['coincident']['null_sd'])
m('RfiOccMskCoZ', tex(Cm['coincident']['z']))

# the directory key, kept so the paper can STATE the defect
m('RfiOccDirObs', '%d' % D['greedy']['observed'])
m('RfiOccDirNull', '%.1f' % D['greedy']['null_mean'])
m('RfiOccDirNullSd', '%.1f' % D['greedy']['null_sd'])
m('RfiOccDirZ', tex(D['greedy']['z']))
m('RfiOccDirCoObs', '%d' % D['coincident']['observed'])
m('RfiOccDirCoZ', tex(D['coincident']['z']))

# the stored report of the broken module
m('RfiOccStaleN', '%d' % STALE['n_windows'])
m('RfiOccStaleClusters', '%d' % STALE['n_clusters'])
m('RfiOccStaleDate', STALE['date'])
m('RfiOccPriorZ', '%.1f' % SHIPPED_DIRKEY['z'])

# the masked species behind the significant subset's apparent excess
_spec = sorted(species.items(), key=lambda kv: (-kv[1], kv[0]))
m('RfiOccSpeciesList',
  ', '.join('%s $\\times$%d' % (k.replace('13CO', '$^{13}$CO')
                                 .replace('-', '--'), v)
            for k, v in _spec))

out['macros'] = dict(sorted(M.items()))
out['verdict'] = (
    'Corrected, the cross-target frequency-occupancy screen supports NO '
    'interference claim and the prior z = %.1f is withdrawn. The directory '
    'key reproduces it (%d vs %.1f +- %.1f, z = %.2f); the STAR key, over '
    'the same %d windows toward %d stars with the same grid null, gives '
    '%d vs %.1f +- %.1f (z = %.2f). Among the %d windows with a peak above '
    '%g sigma the corrected count is %d against %.1f +- %.1f (z = %.2f), '
    'below the null; %d of those sit on a masked transition, and with the '
    'mask applied the order-independent count is %d against %.1f +- %.1f '
    '(z = %.2f). The residual %s per cent over all windows is not '
    'significant and those peaks are noise (median peak SNR %.1f).'
    % (SHIPPED_DIRKEY['z'], D['greedy']['observed'], D['greedy']['null_mean'],
       D['greedy']['null_sd'], D['greedy']['z'], len(rows), n_stars,
       A['greedy']['observed'], A['greedy']['null_mean'],
       A['greedy']['null_sd'], A['greedy']['z'], B['n'], SIG,
       B['greedy']['observed'], B['greedy']['null_mean'],
       B['greedy']['null_sd'], B['greedy']['z'], len(sig_masked),
       Cm['coincident']['observed'], Cm['coincident']['null_mean'],
       Cm['coincident']['null_sd'], Cm['coincident']['z'],
       A['greedy']['excess_pct'], med_snr))

with open(OUT, 'w') as fh:
    fh.write('%% GENERATED by freqocc_v405.py -- do not hand-edit.\n')
    for k in sorted(M):
        fh.write('\\newcommand{\\%s}{%s}\n' % (k, M[k]))
with open(JSONOUT, 'w') as fh:
    json.dump(out, fh, indent=1, sort_keys=False)
    fh.write('\n')

print('freqocc_v405: %d searched windows in %d directories = %d stars '
      '(%d carry an _EB_ block; the naive regex key would give %d, which is '
      'why the merge is a table)'
      % (len(rows), n_dirs, n_stars, n_eb, n_naive))
print('  all %d peaks lie on their own channel grid (worst %.2e channel), '
      'so the null draws a CHANNEL' % (n_ongrid, GRID_WORST))
for tag in ('all_windows_dirkey', 'all_windows', 'all_windows_line_removed',
            'peak_gt_5sigma', 'peak_gt_5sigma_line_removed'):
    d = out['subsets'][tag]
    print('  %-28s key=%-4s n=%4d | greedy %4d vs %6.1f+-%4.1f z=%+5.2f '
          'p=%.3f | coincident %4d vs %6.1f+-%4.1f z=%+5.2f'
          % (tag, d['key'], d['n'], d['greedy']['observed'],
             d['greedy']['null_mean'], d['greedy']['null_sd'],
             d['greedy']['z'], d['greedy']['p_ge_obs'],
             d['coincident']['observed'], d['coincident']['null_mean'],
             d['coincident']['null_sd'], d['coincident']['z']))
print('  FALSIFIER PASSES: the directory key reproduces the withdrawn pass '
      '(%d vs its %d, z=%.2f > %.1f) BEFORE the star key withdraws it '
      '(z=%.2f, |z|<2)'
      % (D['greedy']['observed'], SHIPPED_DIRKEY['observed'],
         D['greedy']['z'], SHIPPED_DIRKEY['z'], A['greedy']['z']))
print('  %d of the %d significant windows sit on a masked transition: %s'
      % (len(sig_masked), len(sig),
         ', '.join('%s x%d' % (k, v) for k, v in _spec)))
print('  median peak SNR over all windows %.2f; %d of %d windows are coarse '
      '(%d fine, %d medium, %d unlabelled)'
      % (med_snr, n_coarse, len(rows), n_fine, n_medium, n_unlab))
print('  the stored report (%s, %d windows, %d clusters) is the [3] bug, '
      'not a measurement' % (STALE['date'], STALE['n_windows'],
                             STALE['n_clusters']))
print('  -> %s (%d macros), %s'
      % (os.path.basename(OUT), len(M), os.path.basename(JSONOUT)))
