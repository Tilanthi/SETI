#!/usr/bin/env python3
r"""Gate: a retired macro name may not appear in the manuscript.

Round 103 resolves several quantities that the manuscript carried under two
names with two values -- the sensitivity on two different selection criteria,
the attribution count under two different reference frames, the benchmark at
two different apertures. Each pair is now one number.

Keeping the superseded name alive as a synonym is not enough. This project
has four times lost a number to the opposite mechanism: a macro is computed,
nothing references it, `retire_macros.py` deletes it, and the value it was
meant to replace goes on typesetting unchallenged. The mirror failure is just
as cheap -- a prose agent writes the old name, it still expands, and the old
value ships.

So retirement is two layers, and this file is the second:

  1. the macro layer aliases every retired name to its replacement, so the
     superseded VALUE is unreachable from any route through the document;
  2. this gate fails on the retired NAME, naming the file and line, so the
     name cannot survive the revision either.

A retirement with no replacement cannot be aliased -- there is no correct
value to point it at -- so for those the gate is the only layer, and it must
report them rather than break a build whose owner cannot see why.

    python3 retired.py [--drive N]

Exit 1 if any retired name is used. --drive 1 plants a use, --drive 3 plants
an undeclared macro from a generator that touches the retired column,
--drive 4 plants a declaration that no longer matches what is emitted, and
--drive 2
empties the retired list; both must change the verdict, which is what makes
the pass a measurement rather than an absence of evidence.
"""
import os
import re
import sys

import manuscript

HERE = os.path.dirname(os.path.abspath(__file__))
ROUND = os.path.join(HERE, 'survey_numbers_round103.tex')


def retired_names():
    """Read the retired list from the round file that declares it.

    Deliberately not a literal here: the generator owns the list, and a
    second copy of it in the gate is a second thing to forget to update.
    """
    src = open(ROUND, errors='ignore').read()
    m = re.search(r'^%\s*RETIRED:\s*(.+)$', src, re.M)
    assert m, ('%s carries no "%% RETIRED:" line, so this gate has nothing '
               'to check and would pass vacuously' % os.path.basename(ROUND))
    names = m.group(1).split()
    assert names, 'the retired list is empty'
    aliased = set(re.findall(r'\\renewcommand\{\\([A-Za-z]+)\}\{\\[A-Za-z]+\}',
                             src))
    # ★★★ v4.11: SUPERSESSIONS DECLARED BY THE GENERATOR THAT OWNS THE
    # REPLACEMENT.  Round 103 can only retire names whose replacement it
    # emits itself, so a generator in another round that re-measures a
    # published quantity under a new name had no way to say so -- and
    # `selfunc_v411.py` did exactly that: it published \SfMSearched = 41 and
    # left round 29's \NMSearched = 21 live, after which the manuscript used
    # BOTH, eleven pages apart, for one quantity.  Nothing could see it,
    # because every other gate here compares a macro with its own source.
    #
    # The rule is now: whoever publishes the replacement names what it
    # supersedes, in a `%% SUPERSEDES: old=new ...` line in its own round
    # file, and this gate treats those old names exactly as it treats round
    # 103's retired list.  A declaration whose replacement no round file
    # defines is itself a failure, so the line cannot go stale.
    import glob as _g
    sup, badsup = {}, []
    _defined = set()
    for _f in sorted(_g.glob(os.path.join(HERE, 'survey_numbers*.tex'))):
        _t = open(_f, errors='ignore').read()
        _defined |= set(re.findall(
            r'\\(?:new|renew)command\{\\([A-Za-z]+)\}', _t))
        for _m in re.finditer(r'^%%\s*SUPERSEDES:\s*(.+)$', _t, re.M):
            for _tok in _m.group(1).split():
                if '=' not in _tok:
                    badsup.append((os.path.basename(_f), _tok))
                    continue
                _o, _n = _tok.split('=', 1)
                sup[_o] = _n
    for _o, _n in sorted(sup.items()):
        if _n not in _defined:
            badsup.append(('declaration',
                           '%s=%s (replacement undefined)' % (_o, _n)))
    return names, aliased, sup, badsup



# --------------------------------------------------------------------------
# R2's declared exceptions: generator -> macros it emits that are cited by the
# manuscript and are NOT the retired per-window sensitivity, with the reason.
# A pair not listed here FAILS, so a new macro out of one of these generators
# has to be looked at by a person rather than waved through.
NOT_A_LEAK = {
    'v381_calc.py': (
        'BenchEirpSeven',     # a Band-7 benchmark transmitter EIRP
        'BenchGainSeven',     # that benchmark's aperture gain
        'BpicDvLo', 'BpicDvHi',   # velocity offsets of the beta Pic crossings
        'CpSepH',             # hours between two CP-72 2713 blocks
        'ExpStageOneCoarse',  # Poisson expectation of stage-1 coarse windows
        'ExpStageOneFine',    # the same for fine windows
        'HdRingMax',          # a control-ring maximum, in sigma
        'HdTsym',             # T_star under the symmetric normalisation
        'HoLeadBlockDays',    # days between fixing the hold-out and searching
        'LedProcessed', 'LocStageGained', 'LocStageGlobal', 'LocStageLocal',
        'LocStageLost',       # counts through the localisation stage
        'NClassAM', 'NHitsA', 'NStageOneBpicEb', 'NStageOneCoarse',
        'NStageOneFine', 'NStageOneUnattrib', 'NSysClassA',
        'PctDiscProposal', 'SETIChanHz', 'SqrtScaleChanKHz', 'SqrtScaleFac',
        'SysUnionAMed', 'TotalDataTB', 'UnattSepMaxD', 'UnattSepMinD',
        'UnionClassA',        # counts, fractions and bandwidths
    ),
}


def main(argv):
    drive = 0
    for i, a in enumerate(argv):
        if a == '--drive':
            drive = int(argv[i + 1])
    names, aliased, sup, badsup = retired_names()
    if drive == 6:
        badsup = badsup + [('drive', 'planted')]
    names = list(dict.fromkeys(list(names) + sorted(sup)))
    if drive == 2:
        names = []
    lines = manuscript.flat().split('\n')
    if drive == 1:
        # ★ plant the use inside an EXISTING line, so the location reported
        # is a real location: a drive that appends past the end of the
        # document exercises the scanner but not the reporting, and the
        # reporting is half of what this gate is for.
        _j = next(i for i, l in enumerate(lines)
                  if l.strip() and not l.lstrip().startswith('%'))
        lines[_j] = lines[_j] + ' \\SdMed'

    hits = []
    for n in names:
        pat = re.compile(r'\\' + n + r'(?![A-Za-z])')
        for i, line in enumerate(lines, 1):
            # a request or a note about the retirement is not a use of it
            if re.match(r'\s*%', line):
                continue
            if pat.search(line):
                hits.append((n, manuscript.where(i), n in aliased))

    assert names or drive == 2, 'nothing to check'
    if not names:
        print('retired: the retired list is empty, so this gate cannot fail')
        return 1

    # ---- R2: the retired CATALOGUE COLUMN -------------------------------
    # `eirp_p90_sel_W` is the sensitivity on the superseded criterion, one
    # number per window, shipped in the released catalogue.  A generator
    # that reads it computes a retired quantity, and if the macro it emits
    # is still cited the retired value reaches the page by a route no macro
    # alias can close -- the value never passes through a macro name at all.
    # ★★★ v4.11: THE COLUMN IS NOW RENAMED IN THE CATALOGUE, and this clause
    # changed job.  Counting readers and printing a note was not enough and
    # never could be: fourteen generators read the old column, seven of them
    # fed macros the manuscript cites, every figure of merit in the paper
    # came out x1.54 optimistic, and this gate reported it as a note for two
    # cycles.  The column now carries its status in its own name, so a
    # genuine USE raises KeyError on the first row while a mention in a
    # comment, a docstring or an assertion about the retirement is untouched.
    #
    # Two clauses now.  The first is the old one, pointed at the NEW name, so
    # a generator that reads the superseded column AND feeds a cited macro
    # still has to be looked at by a person.  The second is the one that
    # cannot be argued with: the OLD name may not be INDEXED in a live line
    # of any generator, because such a line is either dead code or a crash
    # waiting for its branch to be taken.
    import adopted_e90 as _ae
    COL = _ae.RETIRED_COLUMN_RENAMED
    OLDCOL = _ae.RETIRED_COLUMN
    _old_live = []
    for g in sorted(os.listdir(HERE)):
        if not g.endswith('.py') or g in (os.path.basename(__file__),
                                          'adopted_e90.py'):
            continue
        for _i, _ln in enumerate(open(os.path.join(HERE, g),
                                      errors='ignore').read().split('\n'), 1):
            if OLDCOL not in _ln or COL in _ln:
                continue
            if _ln.lstrip().startswith('#'):
                continue
            if re.search(r"""\[\s*['"]%s['"]\s*\]""" % re.escape(OLDCOL), _ln):
                _old_live.append((g, _i, _ln.strip()[:88]))
    if drive == 5:
        _old_live.append(('drive', 0, 'planted'))
    print('retired: the superseded column is deposited as %s; the old name '
          '%s is indexed in %d live line(s)'
          % (COL, OLDCOL, len(_old_live)))
    for _g, _i, _ln in _old_live:
        hits.append((OLDCOL, '%s:%d' % (_g, _i), False))
        print('  R2b %-22s line %d indexes the OLD column name, which no '
              'longer exists in the catalogue: %s' % (_g, _i, _ln))
    readers, leaking = [], []
    for g in sorted(os.listdir(HERE)):
        if not g.endswith('.py'):
            continue
        gsrc = open(os.path.join(HERE, g), errors='ignore').read()
        live = [ln for ln in gsrc.split('\n')
                if COL in ln and not ln.lstrip().startswith('#')]
        if not live:
            continue
        readers.append(g)
        emits = set(re.findall(r"m\(\s*'([A-Za-z]+)'", gsrc))
        # ★ and R2 read the manuscript WITH its source comments, so a macro
        #   named only in a `%% REQUEST ...` note to another owner counted as
        #   cited -- which is how `PromoteMedA`, `PromoteSysMedA` and
        #   `SelRatioRank`, whose only appearances are in routing comments,
        #   looked like the retired sensitivity reaching the page.  A comment
        #   is not typeset.  R1 already strips them; R2 now does too.
        _doc = re.sub(r'(?<!\\)%.*', '', '\n'.join(lines))
        cited = sorted(n for n in emits
                       if re.search(r'\\' + n + r'(?![A-Za-z])', _doc))
        # ★★ ROUND 9 -- R2 KEYS ON THE FILE, NOT ON THE QUANTITY, and that is
        #    both too loud and, on its own, too quiet.
        #
        #    Too loud: it flags a generator because the FILE mentions the
        #    retired column, whatever the cited macro was computed from.  Six
        #    of `v381_calc.py`'s cited macros are a block separation in hours,
        #    two Poisson expectations of stage-1 windows, a symmetric-form
        #    statistic, a control-ring maximum and two velocity offsets.  None
        #    is a sensitivity.  Six failures a build, none of them actionable,
        #    which is how a reader is trained to ignore a gate.
        #
        #    ★ Too quiet: the one macro in that same file that genuinely WAS
        #    the retired sensitivity escaped it.  `SqrtScalePsel` printed "the
        #    median Class A selection power" from
        #    `median(eirp_p90_W * ctrl_max_snr / 5) * sqrt(dnu ratio)` -- the
        #    retired column's own DEFINITION rebuilt out of the two columns it
        #    was built from, so nothing keyed on the retired NAME could see
        #    it.  It was found by reading, not by a gate, and the clause it
        #    cited is now deleted from the manuscript.
        #
        #    So the pairs this clause can see are DECLARED, each with the
        #    reason it is not the retired quantity, and the clause fails on a
        #    pair that is NOT declared -- i.e. on a new macro from a generator
        #    that touches the retired column, which is the case a human must
        #    look at.  A declaration that stops matching also fails, so the
        #    list cannot quietly go stale.
        undeclared = sorted(set(cited) - set(NOT_A_LEAK.get(g, ())))
        if undeclared:
            leaking.append((g, undeclared))
        stale = sorted(set(NOT_A_LEAK.get(g, ())) - emits)
        if drive == 4 and g in NOT_A_LEAK:
            stale = stale + ['DriveNeverEmitted']
        if stale:
            leaking.append((g, ['DECLARED-BUT-NOT-EMITTED: ' + ', '.join(stale)]))
    if drive == 3:
        leaking.append(('drive', ['X']))
    print('retired: %d generator(s) read the retired catalogue column %s; '
          '%d of them emit a macro the manuscript still cites'
          % (len(readers), COL, len(leaking)))
    for g, cited in leaking:
        hits.append((COL, g, False))
        print('  R2 %-22s emits %s, which the manuscript cites: the '
              'superseded per-window sensitivity reaches the page without '
              'passing through a macro name' % (g, ', '.join(cited[:6])))

    for _f, _tok in badsup:
        hits.append(('SUPERSEDES', _f, False))
        print('  SUP %-22s malformed or dangling supersession declaration: %s'
              % (_f, _tok))
    print('retired: %d generator-declared supersession(s): %s'
          % (len(sup), ', '.join('%s->%s' % kv for kv in sorted(sup.items()))))
    print('retired: %d retired names, %d of them aliased to a replacement, '
          '%d uses in the manuscript' % (len(names), len(aliased), len(hits)))
    for n, where, al in sorted(hits):
        print('  %-18s %-42s %s' % (
            n, where,
            'aliased, so the value is already correct -- the NAME must go'
            if al else
            'NO replacement: the sentence must go, not the macro'))
    if hits:
        print('retired: %d FAIL' % len(hits))
    return 1 if hits else 0


if __name__ == '__main__':
    sys.exit(main(sys.argv))
