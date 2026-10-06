#!/usr/bin/env python3
"""Two names, one quantity: the defect no other gate in this project can see.

`macrosyn` and `consistency` each compare a macro against the source it was
computed from, so both pass when two *different* macros describe the same
quantity and disagree.  That is how the manuscript came to say 41 M dwarfs in
Section 3 and 21 in Section 6, eleven pages apart, in a round whose whole
purpose was to remove exactly that kind of contradiction -- and the stale copy
was the flattering one.

The check is mechanical.  Strip the naming conventions this project uses as
prefixes (which generator family published it) and as suffixes (which class it
describes), and any two macros that collapse to the same stem are candidates
for being the same quantity.  Report them when their values differ.

Nothing is guessed: a differing pair must either be fixed or be listed in
TWINS_OK with a one-line reason.  Whitelisting is the point rather than a
loophole -- a Class A count legitimately differs from a survey count, and
being made to write down why is the same discipline the referees asked of the
prose.

Only macros actually used in the manuscript are considered.  An unused macro
cannot contradict anything a reader sees.
"""
import re
import glob
import sys

# Generator-family prefixes.  Order matters: longest first, so that "SfM" is
# stripped to "M" rather than "fM".
PREFIXES = ('Sf', 'Hz', 'Ldg', 'Bud', 'Stk', 'Cov', 'Fom', 'Scr', 'Px', 'Ep',
            'Fl', 'Bpic', 'Cp', 'Mason', 'Occ', 'Dispo', 'N')
# Class/variant suffixes.
SUFFIXES = ('A', 'B')

# Pairs that legitimately differ.  Each needs a reason, and the reason is read
# by a human, not by this script.
TWINS_OK = {
    ('NWinA', 'NWinB'): 'fine- and coarse-channel window counts: different sets by construction',
    ('EirpMinA', 'EirpMinB'): 'best limit in each class; the classes are different experiments',
    ('EirpMaxA', 'EirpMaxB'): 'worst limit in each class, as above',
    ('ChanLoA', 'ChanLoB'): 'channel-width range per class, as above',
    ('ChanHiA', 'ChanHiB'): 'channel-width range per class, as above',
    ('SurvFreqLoA', 'SurvFreqLo'): 'Class A span 114 GHz against the 90 GHz archival harvest; '
                                   'the distinction R1-5 requires',
    ('SurvFreqHiA', 'SurvFreqHi'): 'as above, upper edge',
    ('EirpNinetyMultA', 'EirpNinetyMultB'):
        'pooled completeness factor per class.  The Class A value is NOT the adopted '
        'per-window factor -- the adopted transfer is stratified on the control ring -- '
        'and every use of it in the text says so explicitly.  The name is legacy and '
        'should become EirpNinetyMultBlend at the next version bump.',
    ('MasonNStar', 'SfNStar', 'StkNStar'):
        'three different populations: the comparison programme\'s targets, the stars '
        'searched here, and the stars entering the multi-epoch stacks.',
    ('StkRegBpChanA', 'StkRegBpChanB'):
        'fine and coarse channel widths of the stacking registration grid.  These are '
        'the two widths whose conflation produced the velocity-tolerance error, so '
        'neither may ever be printed without its width named beside it.',
    ('StageNullEligible', 'StageNullEligibleA'):
        'windows eligible for the control null over both classes, and over Class A '
        'alone.  Both counts are quoted in the paper and each names its set.',
}


def stem(name):
    s = name
    for p in PREFIXES:
        if s.startswith(p) and len(s) > len(p) + 1:
            s = s[len(p):]
            break
    for x in SUFFIXES:
        if s.endswith(x) and len(s) > len(x) + 1:
            s = s[:-len(x)]
            break
    return s.lower()


def main():
    body = ''.join(open(f, encoding='utf8', errors='ignore').read()
                   for f in glob.glob('sections/*.tex'))
    body = re.sub(r'(?<!\\)%.*', '', body)
    used = set(re.findall(r'\\([A-Za-z]{3,})', body))

    vals = {}
    for f in glob.glob('survey_numbers*.tex'):
        txt = open(f, encoding='utf8', errors='ignore').read()
        for m, v in re.findall(r'\\(?:new|renew|provide)command\*?\{\\([A-Za-z]+)\}\{([^}]*)\}', txt):
            vals[m] = (v.strip(), f)

    groups = {}
    for m in sorted(used & set(vals)):
        groups.setdefault(stem(m), []).append(m)

    def norm(v):
        return re.sub(r'[\\,\s{}~]', '', v)

    bad, noted = [], []
    for st, names in sorted(groups.items()):
        if len(names) < 2:
            continue
        seen = {}
        for nm in names:
            seen.setdefault(norm(vals[nm][0]), []).append(nm)
        if len(seen) < 2:
            continue                       # same value under two names: harmless
        key = tuple(sorted(names))
        reason = None
        for k, r in TWINS_OK.items():
            # A whitelisted group covers the pair if the names found are all in
            # it, OR if it is wholly contained in them.  The first direction
            # matters: a three-name group whose third member stops being cited
            # must not start failing.  That happened within an hour of this
            # gate being written, when a retirement pass dropped one member and
            # the remaining pair no longer matched the entry that explained it.
            if set(names) <= set(k) or set(k) <= set(names):
                reason = r
                break
        line = '  %-34s %s' % (st, '  '.join('%s=%s' % (n, vals[n][0]) for n in names))
        (noted if reason else bad).append((line, reason))

    print('twinmacro: %d manuscript macros, %d stems with more than one name'
          % (len(used & set(vals)), sum(1 for g in groups.values() if len(g) > 1)))
    if noted:
        print('  whitelisted, differing for a stated reason:')
        for line, reason in noted:
            print(line + '\n      -- ' + reason)
    if bad:
        print('  FAIL two names for one quantity, with different values and no reason given:')
        for line, _ in bad:
            print(line)
        print('  Fix the stale one, or add the pair to TWINS_OK with a reason.')
        sys.exit(1)
    print('  OK no unexplained twin')


if __name__ == '__main__':
    main()
