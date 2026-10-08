#!/usr/bin/env python3
r"""GATE: two generators may not publish one quantity under two unrelated names.

★★★ WHY THIS EXISTS, AND WHY NOTHING ELSE IN THIS TREE COULD SEE IT.
On 2026-10-08 two agents published the SAME FOUR QUANTITIES fourteen minutes
apart.  Round 590 emitted `\PsSheikhNHz` = 200, `\PsDriftPctSheikh` = 6,
`\PsJupAccel` = 2.2 and `\PsAccelRotRatio` = 0.61 because the front matter
needed the drift ceiling in nanohertz; round 37 emitted `\AccelSheikhNHz`,
`\AccelSheikhPct`, `\AccelJupRot` and `\AccelJupPct` with the same values
because a figure caption needed them.  One referee point touched a caption and
the abstract, and the ownership table gave the item to one of the two agents.

Every gate in the build was blind to it:

  * `roundcollide` compares round FILENAMES and owners.  Two different rounds
    written by two different generators is exactly what it is designed to
    permit.
  * `twinmacro` and `synmacro` group macros by NAME STEM.  `Ps` and `Accel`
    are not related strings, so the two families never reduce to one stem, and
    `twinmacro` goes further and skips a same-stem group whose members AGREE:
    "same value under two names: harmless".  For a twin it is the opposite of
    harmless -- agreement today is what hides the divergence tomorrow.
  * `macrosyn` compares pairs declared in advance.  Nobody declares a pair
    that nobody knows exists.

So the hazard is not two agents claiming one round number.  It is **two agents
independently publishing one quantity under two names**, and the only signal
available to a mechanical check is that the two print the same number with the
same unit in the same document.

★ THE SIGNAL, AND WHY THE UNIT IS LOAD-BEARING.  Grouping cited macros by
value alone is useless in this tree: 139 cross-generator groups, almost all of
them small integers counting different sets (24 flagged crossings, 24 systems
at 10^15 W, 24 Band 8 windows).  A bare count's identity is carried by the
noun beside it, and `synmacro`, `intsweep` and `twinmacro`'s DENOM table
already work on counts.  What distinguishes a quantity is its UNIT, and the
unit is in the prose: the manuscript writes `\CvUnionA\,GHz`, `\LsLupDv
\,km\,s$^{-1}$`, `\SensMultA\,P_{\rm trig}`.  So this gate reads the unit from
the USE SITE, groups on (value, unit), and reports only groups whose members
come from more than one generator.  That brings 139 down to 17, every one of
which is worth a human sentence -- and the round-590 collision is three of
them.

★★ TWO WAYS TO RESOLVE A GROUP, AND THEY MEAN DIFFERENT THINGS.

  1.  **The names are one quantity.**  Then the right declaration is
      `twinmacro.SAME`, which REQUIRES THE VALUES TO AGREE for ever and is
      protected from retirement.  A group all of whose members are pairwise
      covered there is resolved here, because the equality is enforced by a
      gate that fails when it breaks.  Declaring it here instead would be a
      whitelist for the defect.
  2.  **The names are different quantities that happen to agree.**  Then the
      declaration belongs in `COINCIDENCE` below, with a one-line reason
      naming what each one is.  No numeric assertion is made: a check that
      fires only when two independent numbers happen to agree can only fail on
      good data, which is as useless as a check that cannot fail.

Anything else is a FAILURE, and the fix is a decision rather than an entry.

    python3 valuetwin.py [--drive N] [--all]

`--all` also lists the single-generator groups and the unit tally.
Exit 1 on any undeclared group, on a stale declaration, or if the sweep went
blind.  --drive 1..4 each break one clause and must fire.
"""
import collections
import glob
import os
import re
import sys

import manuscript

HERE = os.path.dirname(os.path.abspath(__file__))
DRIVE = 0
if '--drive' in sys.argv:
    DRIVE = int(sys.argv[sys.argv.index('--drive') + 1])
ALL = '--all' in sys.argv

# ---------------------------------------------------------------------------
# THE UNITS, DECLARED.  Longest first: `kHz` must not be read as `Hz`, and
# `km\,s^-1` must not be read as `m`.  A use whose tail matches none of these
# contributes nothing to a group, and V2 below requires the sweep to have
# recognised a unit for a substantial number of uses, so the list cannot
# silently go stale and leave the gate measuring nothing.
UNITS = [
    ('GHz', r'\\,?GHz'),
    ('MHz', r'\\,?MHz'),
    ('kHz', r'\\,?kHz'),
    ('nHz', r'\\,?nHz'),
    ('Hz s^-1', r'\\,?Hz\\,?s\$\^\{?-1'),
    ('Hz', r'\\,?Hz(?![A-Za-z])'),
    ('km s^-1', r'\\,?km\\,?s\$\^\{?-1'),
    ('m s^-2', r'\\,?m\\,?s\$\^\{?-2'),
    ('K km s^-1', r'\\,?K\\,?km\\,?s'),
    ('W m^-2', r'\\,?W\\,?m\$\^\{?-2'),
    ('MW', r'\\,?MW'),
    ('W', r'\\,?W(?![A-Za-z])'),
    ('mJy', r'\\,?mJy'),
    ('Jy', r'\\,?Jy(?![A-Za-z])'),
    ('per cent', r'\{?\}?\s*(?:per\s+cent|\\%)'),
    ('sigma', r'\$?\\sigma\$?'),
    ('P_trig', r'\\,?P_\{\\rm\s+trig\}'),
    ('arcsec', r'\\,?arcsec'),
    ('pc', r'\\,?pc(?![A-Za-z])'),
    ('au', r'\\,?au(?![A-Za-z])'),
    ('dex', r'\\,?dex'),
    ('GB', r'\\,?GB'),
    ('TB', r'\\,?TB'),
    ('K', r'\\,?K(?![A-Za-z])'),
    ('day', r'\\,?days?(?![A-Za-z])'),
    ('yr', r'\\,?yr(?![A-Za-z])'),
    ('h', r'\\,?h(?![A-Za-z])'),
    ('mm', r'\\,?mm(?![A-Za-z])'),
    ('m', r'\\,?m(?![A-Za-z])'),
    ('s', r'\\,?s(?![A-Za-z])'),
]

# ---------------------------------------------------------------------------
# COINCIDENCE: different quantities, equal value, equal unit.  One line each,
# saying what each member is.  Keyed on the sorted tuple of names.
COINCIDENCE = {
    ('BpicDvCoHi', 'LsLupDv'):
        'the largest offset of a beta Pic CO crossing from its transition, '
        'and the offset of the Lupus crossing from the foreground cloud '
        'velocity a published survey gives: two unrelated velocity residuals '
        'that both round to half a kilometre per second',
    ('DutyAttenDevPct', 'SensDecorPct', 'StkFapCeil', 'TrapPhaseLo'):
        'the duty-cycle attenuation residual, the decorrelation term of the '
        'budget, the stacked false-alarm ceiling and the smaller TRAPPIST-1 b '
        'phase fraction: four quantities whose only common property is that '
        'each is one per cent',
    ('DutyCycleMinPct', 'RingRhoBoundPct'):
        'the smallest duty cycle the intermittency campaign injected, and the '
        'bound on the star-to-ring correlation; both ten per cent',
    ('CdSpecTsysHi', 'CeMaskPct', 'PlxAdqlPct'):
        'the upper end of the residual T_sys specification, the share of the '
        'band the attribution windows occupy, and the parallax-error cut of '
        'the sample query; three different twenty per cents',
    ('LsMaskAddPct', 'SensCovWorstPct'):
        'the extra bandwidth the second mask frame costs, and the worst '
        'per-window coverage shortfall of the injection campaign',
    ('AccelSheikhPct', 'HOFracHiPct'):
        'the fraction of the recommended drift range this grid reaches, and '
        'the upper end of the hold-out exclusion fraction',
    ('InjShortPct', 'SensDecorHiPct', 'SmcValWorstPct'):
        'the shortfall of the injected channel response against the exact '
        'lag window, the upper decorrelation bracket, and the largest '
        'disagreement between the applied smearing correction and the '
        'campaign re-scoring that validates it',
    ('PctDiscProposal', 'RcPowerLevel'):
        'the share of the searched blocks whose proposals targeted discs, and '
        'the recovery level the recurrence probabilities are quoted at; both '
        'ninety per cent and neither derived from the other',
    ('CovNuMaxAtRef', 'CvConfNuMaxDay'):
        'the frequency at which most systems are covered at the benchmark '
        'power, and the frequency at which confirmation coverage peaks: two '
        'maxima of two different curves, both in the CO(2-1) band, so both '
        'land on the same tuning',
    ('SurvFreqHi', 'SurvFreqHiA'):
        'the archival extent, which the title states, and the Class A extent '
        'inside it (R1-5).  The two share their UPPER end and not their '
        'lower, which is why the pair cannot be declared one quantity; '
        'synmacro carries the lower-end pair for the same reason',
    ('DomAFreqHi', 'TlFreqHi'):
        'the top of the Class A coverage, and the top of the interval the '
        'telluric line list was built over -- the list was deliberately built '
        'to the coverage, so the agreement is construction and not a twin',
    ('FluxChanBestKHz', 'SzChanFinestKHz'):
        'the channel width of the window that sets the best flux-density '
        'limit, and the finest channel width anywhere in the survey.  They '
        'are the same window because the finest channel gives the best '
        'limit, and they are different quantities because either could move '
        'without the other',
    ('SbBoneChanMHz', 'SzChanWidestMHz'):
        'the channel width of the Band 1 continuum mode, and the widest '
        'channel in the survey: the same statement about different sets, and '
        'the Band 1 mode is widest only while no coarser mode is searched',
    ('ChanAMedKHz', 'EvAChanwkHz'):
        'the MEDIAN Class A channel width, and the channel width of the one '
        'window carrying the leading crossing; the second is one draw from '
        'the distribution the first summarises',
    ('BkEpsOnChanFineKHz', 'ChanFineKHz', 'FluxChanMedKHz', 'SqrtScaleChanKHz',
     'StkRefChanKHz', 'TjChanKHz'):
        'the fine-channel width in six roles -- the eps Eri flux-scale '
        'windows, the catalogue mode, the median of the flux-limit sample, '
        'the width the noise-scaling check is quoted at, the stacking '
        'reference and the channel the crossing pairs are resolved against.  '
        'All six are the same physical correlator setting and none is '
        'derived from another; they move apart the moment any one subset '
        'changes, which is the state this entry exists to make visible',
}


def _macro_layer():
    """{name: (value, generator)} in the manuscript's own \\input order, with
    one-level aliases followed, so the value is what pdflatex would typeset
    and the generator is the file whose header claims the round."""
    mainsrc = open(os.path.join(HERE, manuscript.main_file()),
                   encoding='utf-8').read()
    order = [m + '.tex' for m in re.findall(
        r'\\input\{(survey_numbers[A-Za-z0-9_]*)\}', mainsrc)]
    # ★ a leftover `--drive` product matches `survey_numbers*.tex` and would
    # join the layer silently, which is how a perturbed value could reach a
    # gate.  The agent rules call a stray drive output in the build root out
    # by name; this gate refuses to read one even if it is there.
    have = {os.path.basename(p) for p in
            glob.glob(os.path.join(HERE, 'survey_numbers*.tex'))
            if '_drive' not in os.path.basename(p)}
    files = [f for f in order if f in have] + sorted(have - set(order))
    pat = re.compile(r'\\(?:new|renew)command\{\\([A-Za-z]+)\}\{(.*)\}\s*$',
                     re.M)
    val, gen = {}, {}
    for f in files:
        txt = open(os.path.join(HERE, f), encoding='utf-8',
                   errors='ignore').read()
        m = re.search(r'GENERATED by ([A-Za-z0-9_.]+\.py)',
                      txt.split('\n', 1)[0])
        who = m.group(1) if m else f
        for nm, body in pat.findall(txt):
            if body.strip():
                val[nm], gen[nm] = body.strip(), who
    for _ in range(6):                      # follow \Alias -> \Target chains
        for nm, v in list(val.items()):
            a = re.fullmatch(r'\\([A-Za-z]+)', v.strip())
            if a and a.group(1) in val:
                val[nm] = val[a.group(1)]
                # the ALIAS keeps its own owner: round 103's retirement pass
                # is where an alias is declared, and attributing the value to
                # it would make every retirement look like a twin.
    return {nm: (val[nm], gen[nm]) for nm in val}


def _uses(body):
    """{name: {unit}} read from the use site, and the tally of uses whose
    tail matched no declared unit."""
    body = '\n'.join(re.sub(r'(?<!\\)%.*$', '', ln) for ln in body.split('\n'))
    units = [(u, re.compile(r'\s*' + rx)) for u, rx in UNITS]
    out, blind, total = collections.defaultdict(set), 0, 0
    for m in re.finditer(r'\\([A-Za-z]+)(?:\{\})?', body):
        nm = m.group(1)
        total += 1
        tail = body[m.end():m.end() + 30]
        for u, rx in units:
            if rx.match(tail):
                out[nm].add(u)
                break
        else:
            blind += 1
    return out, blind, total


def main():
    global UNITS
    if DRIVE == 2:
        # ★ drive 2: the UNITS list goes stale -- one unit spelling changes in
        # the manuscript and the sweep stops recognising it.  Without V2 the
        # gate would then report "0 cross-generator groups, 0 FAIL" for ever,
        # which is a check that cannot fail.  Emptying the list is the
        # extreme of that, and V2 must notice.
        UNITS = [('never', r'(?!x)x')]
    layer = _macro_layer()
    body = manuscript.flat()
    uses, blind, total = _uses(body)

    # the declared same-quantity pairs, read from the gate that enforces them
    import twinmacro
    same = set()
    for pair in twinmacro.SAME:
        same.add(tuple(sorted(pair)))
    if DRIVE == 3:
        same = set()                       # drive 3: forget the SAME table

    groups = collections.defaultdict(set)
    for nm, us in uses.items():
        if nm not in layer:
            continue
        v = re.sub(r'[\\,\s{}~$]', '', layer[nm][0])
        if not re.fullmatch(r'[-+]?\d+(?:\.\d+)?', v):
            continue
        for u in us:
            groups[(v, u)].add(nm)
    if DRIVE == 1:
        # ★ THE DRIVE THAT REPRODUCES THE DEFECT.  Put the round-590 family
        # back: a second name for the Sheikh fraction, from another generator.
        layer['PsDriftPctSheikh'] = (layer['AccelSheikhPct'][0], 'prose_r15.py')
        groups[(re.sub(r'[\\,\s{}~$]', '', layer['AccelSheikhPct'][0]),
                'per cent')].add('PsDriftPctSheikh')

    multi = {k: g for k, g in groups.items()
             if len(g) > 1 and len({layer[n][1] for n in g}) > 1}
    if DRIVE == 4:
        multi = {}                         # drive 4: the sweep finds nothing

    def covered_by_same(names):
        ns = sorted(names)
        return all(tuple(sorted((a, b))) in same
                   for i, a in enumerate(ns) for b in ns[i + 1:])

    bad, by_same, by_coin, used_coin = [], [], [], set()
    for k, g in sorted(multi.items()):
        key = tuple(sorted(g))
        if covered_by_same(g):
            by_same.append((k, key))
        elif key in COINCIDENCE:
            by_coin.append((k, key))
            used_coin.add(key)
        else:
            bad.append((k, key))

    stale = [k for k in COINCIDENCE if k not in used_coin]
    print('valuetwin: %d cited macros in the layer, %d macro uses, '
          '%d with a declared unit, %d (value, unit) groups, %d '
          'cross-generator'
          % (len(layer), total, total - blind, len(groups), len(multi)))
    if ALL:
        tal = collections.Counter(u for us in uses.values() for u in us)
        print('  units seen: ' + ', '.join('%s %d' % (u, n)
                                           for u, n in tal.most_common()))
    for (v, u), key in by_same:
        print('  SAME quantity, equality enforced by twinmacro: %s %s  %s'
              % (v, u, ' = '.join('\\' + n for n in key)))
    for (v, u), key in by_coin:
        print('  coincidence: %s %s  %s' % (v, u, ', '.join('\\' + n
                                                            for n in key)))
        print('      -- ' + COINCIDENCE[key])
    fails = []
    # V1: no undeclared cross-generator (value, unit) group.
    for (v, u), key in bad:
        fails.append('V1 %s %s published by %s under %d names and declared '
                     'nowhere: %s.  Decide: one quantity (declare in '
                     'twinmacro.SAME, which enforces the equality) or a '
                     'coincidence (declare in valuetwin.COINCIDENCE with a '
                     'reason).'
                     % (v, u, ' and '.join(sorted({layer[n][1]
                                                   for n in key})),
                        len(key), ', '.join('\\' + n for n in key)))
    # V2: the sweep must not have gone blind.  A unit list that stops matching
    # turns this gate into a check that cannot fail, so require that a
    # substantial number of uses carried a recognised unit AND that the
    # cross-generator sweep had something to look at.
    if total - blind < 150:
        fails.append('V2 only %d of %d macro uses carried a unit this gate '
                     'recognises; the UNITS list has gone stale and the '
                     'sweep is measuring almost nothing' % (total - blind,
                                                            total))
    if not groups:
        fails.append('V2 no (value, unit) group was formed at all')
    # V3: a declaration whose group no longer exists is removed, not left.
    for key in sorted(stale):
        fails.append('V3 COINCIDENCE declares %s, which is no longer a '
                     'cross-generator group; delete the entry rather than '
                     'leave it' % ', '.join('\\' + n for n in key))
    if fails:
        print('  FAIL:')
        for f in fails:
            print('    ' + f)
        print('valuetwin: %d FAIL' % len(fails))
        sys.exit(1)
    print('valuetwin: %d same-quantity group(s), %d declared coincidence(s), '
          '0 FAIL' % (len(by_same), len(by_coin)))


if __name__ == '__main__':
    main()
