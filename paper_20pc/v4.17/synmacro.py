#!/usr/bin/env python3
r"""GATE: two macros that mean the same thing may not carry two values.

★★★ WHY THIS EXISTS.  Every other gate in this tree compares a macro with
its own source.  `macrosyn` compares macros declared in advance to be the
same quantity; `consistency_v399` checks a trio that must sum; `prosenum`
compares a prose literal with the macro beside it; `intsweep` registers
integers.  **Nothing compares two macros that nobody declared.**

That gap cost four separate numbers in one round, and the worst of them
reached the typeset page: `selfunc_v411.py` re-measured the M-dwarf census
with every searched star classified and published `\SfMSearched` = 41, while
round 29's `\NMSearched` = 21 stayed live.  The manuscript then used BOTH --
section 3 said 41 of 89 searched stars are M dwarfs, section 6.4 said "only
21 of 5,908 catalogued M dwarfs have any coverage at all" -- one quantity,
two names, two values, eleven pages apart, on the very number Referee 2's
M12(c) told us to correct, in a round whose main purpose was to eliminate
exactly this.  And the stale copy was the FLATTERING one.

The check is mechanical and cheap.  This project names macros by convention:
a family prefix (`N…` a count, `Sf…` the selection function, `Ldg…` the
ledger, `Rc…` the recurrence test, `Str…` the strata, `Fr…` the frame,
`Vn…` the v4.09 extent, `Dq…` the data-quality rule, `Hz…` the
habitable-zone list, `Ho…` the hold-out, `Ext…` the archival extension) and
sometimes a class suffix (`A`/`B`).  So: take every macro the manuscript
actually cites, strip a known prefix and a known suffix, and group by what
is left.  Two macros that reduce to the same stem are candidates for being
one quantity.  Report the pair when the values differ; FAIL on any differing
pair that is not whitelisted with a one-line reason.

**The whitelist is the point.**  A Class A count legitimately differs from a
survey count, and the discipline this gate imposes is that somebody has to
write down, in one line, why.  That is the same discipline R1-5 asks of the
prose.  A whitelist entry whose pair no longer differs is itself reported, so
the list cannot silently go stale.

    python3 synmacro.py [--drive N] [--all]

`--all` reports every same-stem group including the ones that agree.
Exit 1 on any undeclared differing pair.  --drive 1..4 breaks one clause.
"""
import glob
import os
import re
import sys

import manuscript

HERE = os.path.dirname(os.path.abspath(__file__))

# Family prefixes, longest first so `NSys` reduces under `N` and not under
# nothing.  These are the prefixes this tree actually uses; a macro whose
# name begins with none of them is grouped under its whole name.
PREFIXES = ('Lg', 'Ldg', 'Sf', 'Rc', 'Str', 'Fr', 'Vn', 'Dq', 'Hz', 'Ho',
            'Ext', 'Camp', 'Rsev', 'Pxa', 'Px', 'Occ', 'Mason', 'Bud',
            'Scr', 'Stk', 'Sel', 'Pri', 'Rob', 'Eirp', 'Bench', 'Loc',
            'Stage', 'Cp', 'Bp', 'Bpic', 'Rfi', 'Ver', 'Clust', 'Fom',
            'Pb', 'Han', 'Mask', 'N')
# Class/stratum suffixes.
SUFFIXES = ('ClassA', 'ClassB', 'A', 'B')

# ---------------------------------------------------------------------------
# DECLARED DIFFERENCES.  A differing same-stem pair is legitimate only with a
# reason here, in one line.  Keyed on the sorted pair.
WHITELIST = {
    #: ★ round 600: the A/B suffix distinguishes two other people's
    #: papers here, not two classes of this search.
    ('SbPriorNStarA', 'SbPriorNStarB'):
        "the star counts of the TWO PUBLISHED SEARCHES above 30 GHz, not of two classes of this one: Steffes & DeBoer's 40 solar-type stars within 23 pc and Mauersberger et al.'s 17 Vega-like and solar-type targets.  The A/B suffix here distinguishes two other people's papers, which is the one case where the class heuristic means something else",
    # --- the channelisation split, which is the paper's primary division ---
    ('NWinA', 'NWinB'):
        'the window count split by channelisation class: A fine enough to '
        'resolve a drift, B not',
    ('EirpNinetyMultA', 'EirpNinetyMultB'):
        'the completeness multiplier measured separately per class, which is '
        'the whole point of measuring it per class',
    ('SurvFreqLo', 'SurvFreqLoA'):
        'the ARCHIVAL frequency extent, which the title states, against the '
        'Class A extent, which the abstract states inside it (R1-5)',
    # ★ RETIRED (v4.12): ('StkRegBpChanA', 'StkRegBpChanB') -- the
    #   cross-band registration sentence left Sec. 5.7 for length, so neither
    #   macro is cited.  It should not come back as it stood: the pair it
    #   printed differed by 0.03 km/s where the agreement claimed in the next
    #   clause was 0.087, because one of the two printed macros stood for a
    #   different quantity (the surviving stacked group's offset, not the
    #   15.3 kHz regression-test mean, which no macro ever carried).
    # --- populations that are deliberately different sets ------------------
    ('CampStars', 'HoStars', 'NStars'):
        'the injection campaign, the pre-registered hold-out and the primary '
        'census are three populations; each is named where it is used',
    ('CampWindows', 'NWindows'):
        'windows the injection campaign spans against windows in the primary '
        'census',
    # ★ RETIRED (v4.12): ('CampStageOne', 'HoStageOne') -- the hold-out's
    #   count is now published and cited by `holdout_v412.py` as part of its
    #   own subsection and the two no longer form a differing cited pair.
    ('HoWin', 'NWinA', 'NWinB'):
        'the hold-out window count beside the two census classes',
    ('DqNStar', 'MasonNStar', 'SfNStar', 'StkNStar'):
        'stars carrying a data-quality flag; Mason et al.\'s sample; the '
        'searched sample; the stars with a stellar-frame stack -- four sets, '
        'four counts',
    ('DqNWin', 'HoNWin', 'PbNWin'):
        'windows flagged by the data-quality rule; the reserved hold-out\'s '
        'windows; and the windows of the primary-beam audit, which is the '
        'whole release -- three sets, three counts.  \'ScrNWinA\' and '
        '\'PxaNWin\' left this group when Ruling 1 removed the screen cost '
        'from the paper and the parallax row from the budget',
    # --- round 11: the two search classes, published apart (R1-7) ---------
    ('CvUnionA', 'CvUnionB'):
        'union bandwidth of each search class.  The two classes do not cover '
        'the same frequencies, so a frequency with coarse but no fine '
        'coverage carries no drift-resolving limit; conclusion 2 quotes both '
        'side by side so the primary search is not read as the larger one',
    ('HoTMax', 'RcTMax'):
        'the largest stellar statistic reached in the hold-out against the '
        'largest reached at a predicted recurrence cell in the census: one '
        'is a search maximum over all windows, the other a single predicted '
        'channel, and they are not comparable numbers',
    ('HoStars', 'NStars'):
        'stars reached by the pre-registered hold-out against stars in the '
        'primary census.  ★ The two are disjoint in EXECUTION BLOCKS and not '
        'in stars -- H4 proves no shared block, and 27 of the 36 hold-out '
        'stars are census stars -- so neither count is a subset of the other '
        'and the out-of-sample claim the paper makes is about windows the '
        'pipeline had never seen, never about unseen stars',
    ('RcNTested', 'VerNTested'):
        'unattributed crossings tested for recurrence against windows '
        'matched to an ACA geometry-verification record -- different things '
        'counted, as queue entry 31 sets out',
    ('HoFracMax', 'RcFracMax'):
        'the largest fraction of the discovery amplitude the repeat coverage '
        'still excludes, in the pre-registered hold-out search against the '
        'primary census.  Two populations, and the difference is the point: '
        'every hold-out crossing is excluded at 0.47 of its amplitude or '
        'less, while in the census the individual limits run all the way to '
        '1.00, which is why the census median is reported as a median and '
        'never as a bound on the set',
    ('RcFracMed', 'RfiFracMed'):
        'TWO DIFFERENT FRACTIONS OF TWO DIFFERENT THINGS, and only the word '
        '"frac" is shared.  RcFracMed is the median fraction of the DISCOVERY '
        'AMPLITUDE that the repeat coverage excludes, over the crossings that '
        'carry an exclusion.  RfiFracMed is the median fractional POSITION of '
        'a released peak inside its own spectral window, which is the '
        'fixed-intermediate-frequency test of the interference appendix and '
        'is 0.50 because the positions are uniform.  Neither is a bound and '
        'they are not the same quantity in any sense',
}


def _stem(name):
    """The quantity a macro name reduces to, after prefix and suffix."""
    s = name
    for p in sorted(PREFIXES, key=len, reverse=True):
        if s.startswith(p) and len(s) > len(p) + 1:
            s = s[len(p):]
            break
    for q in sorted(SUFFIXES, key=len, reverse=True):
        if s.endswith(q) and len(s) > len(q) + 1:
            s = s[:-len(q)]
            break
    return s.lower()


def macro_values(skip_retirement_round=False):
    """{name: raw body} in the manuscript's own \\input order, aliases
    followed, so the value is what pdflatex would typeset."""
    mainsrc = open(os.path.join(HERE, manuscript.main_file()),
                   encoding='utf-8').read()
    order = [m + '.tex' for m in re.findall(
        r'\\input\{(survey_numbers[A-Za-z0-9_]*)\}', mainsrc)]
    have = {os.path.basename(p) for p in
            glob.glob(os.path.join(HERE, 'survey_numbers*.tex'))}
    files = [f for f in order if f in have] + sorted(have - set(order))
    if skip_retirement_round:
        # ★ the drive: read the macro layer as it stood BEFORE round 103's
        # aliases, which is the state the paper was actually in when
        # \NMSearched = 21 and \SfMSearched = 41 were both live and both
        # typeset.  Dropping the retirement round is the only faithful way
        # to show this gate detecting it, because the alias -- correctly --
        # makes the pair agree.
        files = [f for f in files if 'round103' not in f]
    pats = (re.compile(r'\\newcommand\{\\([A-Za-z]+)\}\{(.*)\}\s*$', re.M),
            re.compile(r'\\providecommand\{\\([A-Za-z]+)\}\{\}'
                       r'\\renewcommand\{\\\1\}\{(.*)\}\s*$', re.M),
            re.compile(r'^\\renewcommand\{\\([A-Za-z]+)\}\{(.*)\}\s*$', re.M))
    raw = {}
    for fn in files:
        txt = open(os.path.join(HERE, fn), encoding='utf-8').read()
        defs = []
        for pat in pats:
            for m in pat.finditer(txt):
                defs.append((m.start(), m.group(1), m.group(2)))
        for _, n, v in sorted(defs):
            raw[n] = v

    def resolve(name, seen=None):
        v = raw.get(name)
        if v is None:
            return None
        seen = seen or set()
        al = re.fullmatch(r'\s*\\([A-Za-z]+)\s*', v)
        if al and al.group(1) not in seen:
            return resolve(al.group(1), seen | {name})
        return v
    return {n: resolve(n) for n in raw}


_SCI = re.compile(r'^\$?([-+0-9.]+)\s*\\times\s*10\^\{?(-?\d+)\}?\$?$')


def numeric(v):
    if v is None:
        return None
    s = v.strip().replace('\\,', '').replace('$', '').replace('~', '')
    s = s.replace('\\%', '').strip()
    s = re.sub(r'^[=<>~]+\s*', '', s)
    m = _SCI.match(v.strip().replace('\\,', ''))
    if m:
        return float(m.group(1)) * 10.0 ** int(m.group(2))
    try:
        return float(s)
    except ValueError:
        return None


def main(argv):
    drive = 0
    for i, a in enumerate(argv):
        if a == '--drive':
            drive = int(argv[i + 1])
    # ★ --drive 4 stops following round 103's aliases.  With the alias in
    # place a retired name resolves to its replacement and the pair agrees,
    # which is the retirement working; the drive removes that layer so this
    # gate's own detection is demonstrated on the real names and the real
    # values -- \NMSearched = 21 against \SfMSearched = 41, which is the
    # state the paper was actually in.
    vals = macro_values(skip_retirement_round=(drive == 4))
    # Only macros the MANUSCRIPT cites: an uncited pair cannot mislead a
    # reader, and the tree holds hundreds of deposited-only macros.
    doc = re.sub(r'(?<!\\)%.*', '', manuscript.flat())
    cited = {n for n in vals
             if re.search(r'\\' + n + r'(?![A-Za-z])', doc)}
    if drive == 1:
        cited = set()

    groups = {}
    for n in sorted(cited):
        x = numeric(vals[n])
        if x is None:
            continue
        groups.setdefault(_stem(n), []).append((n, x))

    differing, agreeing = [], []
    for stem, members in sorted(groups.items()):
        if len(members) < 2:
            continue
        xs = {round(x, 10) for _, x in members}
        (differing if len(xs) > 1 else agreeing).append((stem, members))

    fail, declared = [], []
    for stem, members in differing:
        names = tuple(sorted(n for n, _ in members))
        reason = None
        for k, r in WHITELIST.items():
            if set(k) <= set(names):
                reason = r
                break
        if drive == 2 and reason:
            reason = None
        if reason:
            declared.append((stem, members, reason))
        else:
            fail.append((stem, members))

    # A whitelist entry whose pair no longer differs, or no longer exists, is
    # reported: the list must not be able to go stale and still look busy.
    stale = []
    for k in sorted(WHITELIST):
        here = [m for _s, ms in differing for m in ms if m[0] in k]
        if len({round(x, 10) for _, x in here}) < 2:
            stale.append(k)
    if drive == 3:
        stale = stale + [('DriveStale', 'DriveStale')]

    print('synmacro: %d cited macros with a numeric value, %d same-stem '
          'group(s) of two or more, %d differing' %
          (len(cited), len(groups) - sum(1 for _, m in groups.items()
                                         if len(m) < 2), len(differing)))
    for stem, members, reason in declared:
        print('  declared  %-22s %s' % (
            stem, '; '.join('\\%s = %g' % (n, x) for n, x in members)))
        print('            reason: %s' % reason)
    for stem, members in fail:
        print('  **FAIL**  %-22s %s' % (
            stem, '; '.join('\\%s = %g' % (n, x) for n, x in members)))
        print('            two names for one quantity, with two values, and '
              'no declared reason')
    for k in stale:
        print('  **FAIL**  stale whitelist entry %s: the pair no longer '
              'differs, or no longer exists' % (k,))
    if '--all' in argv:
        for stem, members in agreeing:
            print('  agree     %-22s %s' % (
                stem, '; '.join('\\%s = %g' % (n, x) for n, x in members)))
    if not cited:
        print('  **FAIL**  no cited macro has a numeric value, so this gate '
              'checked nothing')
    n_fail = len(fail) + len(stale) + (0 if cited else 1)
    print('synmacro: %d FAIL' % n_fail)
    return 1 if n_fail else 0


if __name__ == '__main__':
    sys.exit(main(sys.argv))
