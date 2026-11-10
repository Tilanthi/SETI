#!/usr/bin/env python3
r"""orphanround -- fail the build if a generated macro file is never \input.

WHY THIS EXISTS.  A generator writes `survey_numbers_round<N>.tex`; the
manuscript must `\input` it or every macro it defines is undefined.  That has
now gone wrong FOUR times, each time discovered by a human noticing 21
undefined control sequences rather than by any check:

  * round 620/630/640/660 (r16): four generators were in no build script at
    all, so a clean checkout would have produced a PDF with every macro from
    them undefined.
  * round 700 (r17): the file was generated, `make_all.sh` ran it, and the
    master never cited it.

`roundcollide` guards the opposite direction -- two generators claiming one
round number -- and `cleanregen` guards staleness.  Neither can see a file
that exists, is current, and is simply not referenced.  This closes that gap.

WHAT IT CHECKS, both directions:

  1. ORPHAN   -- a `survey_numbers_round*.tex` on disk that nothing `\input`s.
                 This is the failure that has actually happened.
  2. DANGLING -- an `\input` of a `survey_numbers_round*` that is not on disk.
                 The symmetric failure, which would fail the build loudly, but
                 naming it here says which file rather than which macro.

HOW IT READS THE SOURCE.  Comments are stripped before scanning, because
`%% \input{survey_numbers_round700}` is not an input -- the same trap that made
`push_paper.py` refuse a good push on 2026-10-10, when it read the
manuscript's own commented-out build instructions as real dependencies.  An
unescaped `%` opens a comment to end of line; `\%` is a literal sign.

IT MUST NOT BE ABLE TO PASS VACUOUSLY.  A sweep that reads no files, or finds
no inputs, "passes" while checking nothing -- the single commonest defect in
this project's tooling, found more than twenty times.  So it asserts that it
read the master, that it found at least MIN_INPUTS inputs, and that at least
MIN_ROUNDS round files exist.  If the naming convention ever changes, this
gate fails rather than going quiet.

USAGE
    python3 orphanround.py              # gate: exit 1 on any problem
    python3 orphanround.py --drive 1    # orphan                -> must FAIL
    python3 orphanround.py --drive 2    # dangling input        -> must FAIL
    python3 orphanround.py --drive 3    # comment counted as an input -> FAIL
    python3 orphanround.py --drive 4    # vacuous (no files read)     -> FAIL
"""

import glob
import os
import re
import sys

MASTER_GLOB = 'technosignatures_*_v*.tex'
ROUND_GLOB = 'numbers/survey_numbers_round*.tex'
SECTION_GLOB = 'sections/*.tex'

#: Anti-vacuity floors.  Well below the real values (142 round files, 141
#: inputs at the time of writing) but far above zero, so a sweep that silently
#: stops working trips them instead of reporting success.
MIN_INPUTS = 50
MIN_ROUNDS = 50


def strip_comments(text):
    r"""Remove LaTeX comments.  `\%` is a literal percent, not a comment."""
    return re.sub(r'(?<!\\)%.*', '', text)


def find_master():
    cands = sorted(glob.glob(MASTER_GLOB))
    if len(cands) != 1:
        raise SystemExit('orphanround: expected exactly one manuscript matching '
                         '%s, found %r' % (MASTER_GLOB, cands))
    return cands[0]


def collect_inputs(master, keep_comments=False, read_sections=True):
    r"""Every `\input{...}` target in the master and its section files."""
    files = [master]
    if read_sections:
        files += sorted(glob.glob(SECTION_GLOB))
    inputs = set()
    for path in files:
        with open(path, encoding='utf-8', errors='replace') as fh:
            text = fh.read()
        if not keep_comments:
            text = strip_comments(text)
        inputs |= set(re.findall(r'\\input\{(?:numbers/)?([^}]*)\}', text))
    return inputs, files


def main(argv):
    drive = 0
    if '--drive' in argv:
        drive = int(argv[argv.index('--drive') + 1])

    master = find_master()
    inputs, read = collect_inputs(master, read_sections=(drive != 4))
    on_disk = {os.path.basename(p)[:-4] for p in glob.glob(ROUND_GLOB)}

    if drive == 1:
        # Simulate the failure that has happened four times: a round file
        # exists and nothing cites it.
        on_disk.add('survey_numbers_round99999')
    if drive == 3:
        # Drive 3 exercises the COMMENT-STRIPPING specifically, and it has to
        # construct its own case rather than rely on one being present.
        #
        # An earlier version of this drive merely re-ran the scan with
        # comments kept, and PASSED -- because at that moment no round file
        # was commented out, so keeping comments changed nothing.  A drive
        # that passes is not a drive; it is the "check that cannot fail"
        # defect this file exists to prevent, reproduced inside the gate
        # built to catch it.  The lesson, logged: a drive must CREATE the
        # condition it tests, never hope to find it.
        #
        # So: add an orphan, and add a COMMENTED input of it.  With comments
        # correctly stripped the orphan stands and this must FAIL.  If anyone
        # ever deletes strip_comments(), the commented line would be counted,
        # the orphan would look cited, and this drive would pass -- which is
        # exactly the regression it is here to catch.
        on_disk.add('survey_numbers_round99997')
        commented = '%% \\input{numbers/survey_numbers_round99997}\n'
        inputs |= set(re.findall(r'\\input\{(?:numbers/)?([^}]*)\}', strip_comments(commented)))
    if drive == 2:
        inputs.add('survey_numbers_round99998')
    if drive == 4:
        # Simulate the gate going blind: pretend the master defines nothing.
        inputs = set()

    orphans = sorted(on_disk - inputs)
    dangling = sorted(n for n in inputs
                      if n.startswith('survey_numbers_round') and n not in on_disk)

    print('orphanround: read %d file(s); %d \\input target(s); %d round file(s) on disk'
          % (len(read), len(inputs), len(on_disk)))

    problems = 0

    # --- anti-vacuity, checked before the result is believed -----------------
    if len(inputs) < MIN_INPUTS:
        print('orphanround: VACUOUS -- only %d \\input target(s) found, expected '
              'at least %d. The sweep is not reading what it thinks it is.'
              % (len(inputs), MIN_INPUTS))
        problems += 1
    if len(on_disk) < MIN_ROUNDS:
        print('orphanround: VACUOUS -- only %d round file(s) found, expected at '
              'least %d. Has the naming convention changed?'
              % (len(on_disk), MIN_ROUNDS))
        problems += 1

    for name in orphans:
        print('orphanround: ORPHAN   %s.tex is generated but never \\input -- '
              'every macro it defines will be undefined.' % name)
        problems += 1
    for name in dangling:
        print('orphanround: DANGLING %s is \\input but not on disk.' % name)
        problems += 1

    if problems:
        print('orphanround: %d FAIL' % problems)
        return 1
    print('orphanround: %d/%d round file(s) cited, 0 orphan, 0 dangling, 0 FAIL'
          % (len(on_disk & inputs), len(on_disk)))
    return 0


if __name__ == '__main__':
    raise SystemExit(main(sys.argv[1:]))
