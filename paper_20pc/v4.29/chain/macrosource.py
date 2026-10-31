#!/usr/bin/env python3
r"""GATE: EVERY MACRO FILE IN THIS DIRECTORY MUST BE ONE THE MANUSCRIPT ASKS
FOR, AND NOTHING ELSE MAY BE ABLE TO DEFINE A PUBLISHED NUMBER.

★★★★ WHY THIS FILE EXISTS AT ALL.  `make_all.sh` line 38 has said, since
v4.01, *"macrosource.py fails the build if a frozen macro file ever
reappears."*  **There was no `macrosource.py`.**  The sentence recorded a
guarantee the build did not have, in the one file a reader checks to find out
what the build guarantees -- and it sat there for twenty-six versions.  So
this is not a new idea; it is the missing half of a promise already made in
writing.  (Written by `r26-integrate`, 2026-10-23, round 26.)

★★★ WHAT MAKES IT MORE THAN HYGIENE.  `adopted_e90._texval()` -- the one
canonical macro reader, behind every `texval()` in the build -- resolves a
macro to its **LAST** definition in this order:

    files = [f for f in <the manuscript's own \input order> if f on disk] \
            + sorted(<every other survey_numbers*.tex on disk>)

The second term is the hazard.  **Any macro file that the manuscript does NOT
\input is read AFTER every file it does, so it silently WINS.**  Ruling 13
caught one instance -- a `_driveN` artefact overriding `\NSysALost` and costing
`r26-limits` a wrong failure to diagnose -- and the glob now filters `_drive`
at all 49 sites.  But the general case is wider than drives: a retired round
file, a half-finished file from another version, a copy made during a cut, or a
frozen pre-repair file restored by hand, all override the published value, from
the tail of that list, with nothing in 44 gates able to see it.

Three clauses, each with a drive.

  M1  no FROZEN macro file is present.  `survey_numbers_round{5,6,7}.tex` were
      generated from an extraction two revisions before the ACA
      control-annulus repair; twelve of their macros were typeset, which is
      literally Referee 2's *"the manuscript mixes results from at least two
      extractions"*.  They were deleted at v4.01 and every one of the twelve
      is now computed.  A reappearance is a regression to a retired
      extraction, and it would win, because the manuscript does not \input
      them.
  M2  every `survey_numbers*.tex` on disk is \input by the manuscript.  This
      is the general closure of the tail-wins hazard: if the set on disk
      equals the set the manuscript asks for, the resolution order is exactly
      the document's own and nothing can override from outside it.
  M3  no drive artefact (`*_drive*.tex`, `*_drive*.json`) is present in the
      build root.  D36's rule is that a test may not write a path production
      reads; this is the complementary rule -- a test's output may not still
      be lying around when production runs.  Also keeps `cleanregen`'s product
      set and `regen_count`'s tally honest.

Usage:  macrosource.py [--drive N]
        --drive 1   M1 fires: plant survey_numbers_round6.tex
        --drive 2   M2 fires: plant a macro file the manuscript never \inputs
        --drive 3   M3 fires: plant survey_numbers_round103_drive34.tex
A drive writes ONLY into a scratch directory; it never touches the build root.
"""
import os
import re
import shutil
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
FROZEN = ('survey_numbers_round5.tex', 'survey_numbers_round6.tex',
          'survey_numbers_round7.tex')
FAILS = []


def ck(label, ok, detail=''):
    print('%-4s %s' % ('ok' if ok else 'FAIL', label))
    if detail:
        print('     %s' % detail)
    if not ok:
        FAILS.append(label)


def main_tex(d):
    c = sorted(f for f in os.listdir(d)
               if f.startswith('technosignatures_') and f.endswith('.tex'))
    assert len(c) == 1, 'expected exactly one manuscript .tex, found %r' % (c,)
    return c[0]


def inputs_of(d):
    """The macro files the manuscript \\inputs, in document order."""
    s = open(os.path.join(d, main_tex(d)), errors='ignore').read()
    return [m + '.tex' for m in re.findall(
        r'\\input\{(?:numbers/)?(survey_numbers[A-Za-z0-9_]*)\}', s)]


def on_disk(d):
    return sorted(f for f in os.listdir(os.path.join(d, 'numbers'))
                  if f.startswith('survey_numbers') and f.endswith('.tex'))


def check(d):
    asked = inputs_of(d)
    have = on_disk(d)
    print('manuscript %s: \\inputs %d macro file(s); %d on disk'
          % (main_tex(d), len(asked), len(have)))

    # ---- M1
    back = [f for f in FROZEN if os.path.exists(os.path.join(d, 'numbers', f))]
    ck('M1 no frozen pre-repair macro file is present (rounds 5-7, deleted at '
       'v4.01; 12 of their macros were typeset from an extraction two '
       'revisions old)', not back,
       'PRESENT: %s' % ', '.join(back) if back else
       'checked %d name(s)' % len(FROZEN))

    # ---- M2
    extra = [f for f in have if f not in asked]
    missing = [f for f in asked if f not in have]
    ck('M2 every macro file on disk is one the manuscript \\inputs -- '
       'adopted_e90._texval() reads anything else LAST, so it would override '
       'the published value', not extra,
       'NOT \\input (these would WIN): %s' % ', '.join(extra) if extra else
       'checked %d file(s) on disk against %d \\input line(s)'
       % (len(have), len(asked)))
    # ★ --pre skips M2b.  macrosource runs TWICE in make_all.sh: once before
    # the first generator, where the hazard is a file that is ALREADY there
    # (frozen, retired or a drive artefact) and where a clean tree legitimately
    # has no macro file yet; and once at the end, where the set must be
    # complete.  A single-mode gate placed at the end cannot see a poisoned
    # input, and placed at the start it fails on every clean regeneration.
    if '--pre' not in sys.argv:
        ck('M2b every macro file the manuscript \\inputs exists on disk', not missing,
           'MISSING: %s' % ', '.join(missing) if missing else
           'checked %d \\input line(s)' % len(asked))
    else:
        print('---  M2b skipped: --pre (a clean tree has no macro file yet)')

    # ---- M3
    drv = sorted(f for f in os.listdir(d)
                 if '_drive' in f and (f.endswith('.tex') or f.endswith('.json')))
    ck('M3 no drive artefact is present in the build root (Ruling 13: a '
       '_driveN round file silently overrode a published macro)', not drv,
       'PRESENT: %s' % ', '.join(drv[:8]) if drv else
       'scanned %d entr(y|ies)' % len(([_e for _e in os.listdir(d) if _e != 'numbers'] + [os.path.join('numbers', _e) for _e in (os.listdir(os.path.join(d, 'numbers')) if os.path.isdir(os.path.join(d, 'numbers')) else [])])))

    # the gate must also be able to see its own premise, or it is decoration
    ck('M4 the manuscript does \\input at least one macro file (this gate is '
       'not measuring an empty set)', len(asked) > 0,
       '%d \\input line(s)' % len(asked))
    return FAILS


def drive(n):
    """Plant the defect in a scratch copy and require the gate to fail."""
    tmp = tempfile.mkdtemp(prefix='macrosource_drive%d_' % n)
    try:
        shutil.copy(os.path.join(HERE, main_tex(HERE)), tmp)
        for f in on_disk(HERE):
            shutil.copy(os.path.join(HERE, 'numbers', f), tmp)
        if n == 1:
            open(os.path.join(tmp, 'numbers/survey_numbers_round6.tex'), 'w').write(
                '\\newcommand{\\NWindows}{1651}\n')
        elif n == 2:
            open(os.path.join(tmp, 'numbers/survey_numbers_roundZZ.tex'), 'w').write(
                '\\newcommand{\\NWindows}{99999}\n')
        elif n == 3:
            open(os.path.join(tmp,
                              'numbers/survey_numbers_round103_drive34.tex'), 'w').write(
                '\\newcommand{\\NSysALost}{0}\n')
        else:
            raise SystemExit('macrosource.py: no drive %d' % n)
        del FAILS[:]
        f = check(tmp)
        want = {1: 'M1', 2: 'M2 ', 3: 'M3'}[n]
        hit = [x for x in f if x.startswith(want.strip())
               and (n != 2 or x.startswith('M2 '))]
        print('\n--drive %d: %d clause(s) failed: %s'
              % (n, len(f), ', '.join(x.split()[0] for x in f) or '-'))
        if not hit:
            print('NOT DEMONSTRATED: drive %d planted the defect and clause %s '
                  'did not fire' % (n, want.strip()))
            return 1
        print('DEMONSTRATED: clause %s fired on the planted defect'
              % want.strip())
        return 0
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


if __name__ == '__main__':
    if '--drive' in sys.argv:
        sys.exit(drive(int(sys.argv[sys.argv.index('--drive') + 1])))
    bad = check(HERE)
    print('\nmacrosource: %d clause(s) failed' % len(bad))
    sys.exit(1 if bad else 0)
