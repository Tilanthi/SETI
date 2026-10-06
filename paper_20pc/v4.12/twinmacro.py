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
    ('CvUnionA', 'CvUnionB'): 'union bandwidth of each search class; the two '
                              'classes cover different frequency sets, and '
                              'conclusion 2 quotes both side by side so that '
                              'the primary search is not read as the larger '
                              'one',
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
    ('ChnXrossA', 'ChnXrossB'):
        'threshold crossings in each search class.  Different sets by construction, '
        'summing to \\NCross, which blockq_v412.py asserts both ways; printing them '
        'apart is what R1-7 asks for, so that the two experiments stop being quoted '
        'as one.',
    ('ChnAttrA', 'ChnAttrB'):
        'line-attributed crossings in each class, the same two sets.  The Class B '
        'value is zero and that is itself the result: every Class B crossing is '
        'unattributed, and all of them come from the one execution block the '
        'block-quality criterion of Appendix D rejects.',
}


# ★★★ v4.12: THE STEM HEURISTIC CANNOT SEE THE PAIRS THE REFEREE FOUND.
# Referee 2 tabulated five pairs of numbers that mean one thing and differ --
# 1614 against 1645 "windows retaining a control vector", 447 against 455
# "windows with a control maximum at the trigger", "390" used for two
# different Class A populations, 14 against 12 windows where the star
# outranks every control, 12 against 4 against 8 disc-affected windows -- and
# `twinmacro` reported "OK no unexplained twin" on every one of them, because
# `StageNullAllWin` and `VerNTested` do not collapse to a common stem and
# never will.  A naming heuristic cannot find a pair that was never named
# alike.  So the pairs are DECLARED.
#
# SAME: two names for one quantity.  The values must agree.  These are
# load-bearing: three of them were different numbers when this table was
# written, and the arithmetic that made them agree is in `consist_v412.py`.
SAME = {
    ('CsNWinCtrlVec', 'NWindows'):
        'every released window retains a full 512-position control ensemble',
    ('StageNullAllWin', 'NWindows'):
        'the stage-1 null runs over the whole released catalogue; the '
        'published 1614 was the survivor count of a star-blind window key',
    ('CsNCtrlTrig', 'NCtrlWinObs'):
        'the windows whose control maximum reaches the trigger, counted from '
        'the stored ensembles and from the released scalar column',
    ('StageNullEligible', 'NCtrlWinObs'):
        'the same count inside the stage-1 null; 447 against 455 was the '
        'same key defect',
    ('CsNCtrlTrigA', 'StageNullEligibleA'): 'the Class A part of it',
    ('CsNCrossFreq', 'AppMNCrossF'):
        'crossings carrying a released peak frequency',
    ('CsNCrossFreq', 'IfPopNCross'):
        'the same set: the crossings inside the released-frequency '
        'population the fractional-position test runs over',
    ('IfPopNCrossAll', 'NCross'): 'every crossing in the catalogue',
    ('IfPopNCrossNoFreq', 'CsNCrossNoFreq'):
        'the crossings with no released frequency column',
    ('CsBpCoBlocksScreen', 'NStageOneBpicEb'):
        'beta Pic CO blocks in which the star also outranks every control',
    ('CsBpCoBlocks', 'BpicPanelNCo'):
        'beta Pic CO crossings, one per block, which is why the count of '
        'blocks and the count of plotted points are the same number',
    ('CsNDiscTen', 'StrNDiscWin'):
        'Class A windows whose control ring reaches the disc-stratum rule',
    ('CsNDiscFourteen', 'ScrNBright'):
        'Class A windows whose ring reaches 14 sigma, where the screen cost '
        'is paid',
    ('CsNRingFourteen', 'NsrBrightN'):
        'windows of EITHER class whose ring reaches 14 sigma',
    ('CsNRingFourteenB', 'StrNBrightB'):
        'the coarse-channel windows with a bright ring',
    ('CsNNoiseRing', 'StrNNoiseWin'):
        'Class A windows whose control ring is noise',
    ('CsNRankFirstA', 'NStageOneWin'):
        'windows where the star outranks every control AND crosses',
    ('CsNRankFirst', 'NsrFirstObs'):
        'windows where the star outranks every control, trigger or not',
}
# DIFFERENT: two names that look alike and are not.  No numeric assertion is
# made -- a coincidence of value is not an error, and a check that fires only
# when two independent numbers happen to agree is a check that can only fail
# on good data.  What IS required is that neither may be printed without its
# denominator, which is referee 1's closing minor point mechanised.
DENOM = {
    'CsNNoiseRing': 'NWinA',
    'CsNCtrlTrigA': 'NWinA',
    'CsNDiscTen': 'NWinA',
    'CsNDiscFourteen': 'NWinA',
    'CsNRankFirst': 'NWindows',
    'CsNCtrlTrig': 'NWindows',
    'CsNCrossFreq': 'NCross',
}
DIFFERENT_OK = {
    ('VerNTested', 'NWindows'):
        'the before/after rank comparison runs on the windows that have a '
        'row in BOTH exports under an order-free window-edge key, which is '
        '1645 of the 1651; the shortfall is a property of the earlier '
        'export and is stated in the appendix as such.',
}


def declared(vals, body):
    """The declared pairs: equal values where equality is claimed, and a
    denominator in the same sentence where distinctness is."""
    def norm(v):
        return re.sub(r'[\\,\s{}~]', '', v)

    bad = []
    for (a, b), why in sorted(SAME.items()):
        if a not in vals or b not in vals:
            continue
        if norm(vals[a][0]) != norm(vals[b][0]):
            bad.append('SAME  \\%s = %s but \\%s = %s  (%s)'
                       % (a, vals[a][0], b, vals[b][0], why))
    flat = re.sub(r'\s+', ' ', body)
    for mac, den in sorted(DENOM.items()):
        if mac not in vals:
            continue
        hits = [m.start() for m in re.finditer(r'\\%s(?![A-Za-z])' % mac, flat)]
        if not hits:
            continue                      # not cited: nothing to qualify
        for h in hits:
            win = flat[max(0, h - 320):h + 320]
            if re.search(r'\\%s(?![A-Za-z])' % den, win):
                break
        else:
            bad.append('DENOM \\%s is printed without \\%s anywhere near it; '
                       'every denominator must be stated at first occurrence'
                       % (mac, den))
    return bad


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

    decl = declared(vals, body)
    print('twinmacro: %d manuscript macros, %d stems with more than one name, '
          '%d declared pairs' % (len(used & set(vals)),
                                 sum(1 for g in groups.values() if len(g) > 1),
                                 len(SAME) + len(DENOM)))
    if decl:
        print('  FAIL declared pairs:')
        for line in decl:
            print('  ' + line)
    if noted:
        print('  whitelisted, differing for a stated reason:')
        for line, reason in noted:
            print(line + '\n      -- ' + reason)
    if bad:
        print('  FAIL two names for one quantity, with different values and no reason given:')
        for line, _ in bad:
            print(line)
        print('  Fix the stale one, or add the pair to TWINS_OK with a reason.')
    if bad or decl:
        sys.exit(1)
    print('  OK no unexplained twin, and every declared pair holds')


if __name__ == '__main__':
    main()
