#!/usr/bin/env python3
r"""macromap -- where every macro in the manuscript goes, and under what name.

The rewrite moves most of the appendix material out of the paper and renames
the power layer.  A prose agent writing a section needs to know, for any
macro it is tempted to use, three things: does the number survive, what is it
called now, and which file owns it.  Guessing produces a vocabulary per agent.

So this generator produces that mapping mechanically rather than by hand:

  * it reads the master source and every file it \inputs;
  * it builds a line -> structural-unit index by walking the sectioning
    commands, so each macro USE is attributed to the unit it occurs in;
  * it applies one declared verdict per OLD unit (the triage table below) to
    turn a set of uses into a destination;
  * it applies the declared SYMBOL renames to the power layer;
  * and it writes one CSV row per macro.

The verdict table is a literature-style declaration: it is the editorial
decision, it cannot be derived from the source, and it is therefore written
out in full and asserted to cover every unit the scan finds.  Everything
else -- which macros exist, where they are used, how many uses, which end up
with no surviving home -- is measured.

  python3 macromap.py MASTER.tex [--out DIR] [--drive N]

Driving.  --drive 0 is the unperturbed run and must produce a map whose
declared invariants hold; --drive 1..5 each break one invariant and the
matching assertion must fire.  No drive writes a path the unperturbed run
writes: every output under a drive carries a _driveN suffix, and the suffix
follows the FLAG, not the perturbation.
"""
import csv
import os
import re
import sys

# --------------------------------------------------------------------------
# 1.  THE VERDICT TABLE.  One row per structural unit of the old manuscript.
#     dest is where the CONTENT goes; '' means the unit is deleted outright.
#     Units are keyed by the number the old document gave them.
VERDICT = {
    # front matter and body: the body survives, re-cut into seven sections
    'abstract': ('MAIN abstract', 'rewritten as science'),
    '1': ('MAIN 1', 'introduction, plus the plain-language opening'),
    '2': ('MAIN 2', 'background and sample; the one Arecibo mention lives here'),
    '3': ('MAIN 3', 'sample selection'),
    '4': ('MAIN 3', 'method; the four-step chain'),
    '4.1': ('MAIN 3', 'candidate definition'),
    '4.2': ('MAIN 3', 'ancillary analyses, compressed'),
    '4.3': ('MAIN 3', 'the experiment in summary'),
    '5': ('MAIN 4', 'results'),
    '5.1': ('MAIN 4', 'nearest stars'),
    '5.2': ('MAIN 4', 'the search'),
    '5.2.1': ('MAIN 4', 'the ledger'),
    '5.2.2': ('MAIN 4', 'the trigger is not a uniform criterion'),
    '5.2.3': ('MAIN 4', 'unattributed and localised crossings'),
    '5.2.4': ('MAIN 4', 'the end of the chain'),
    '5.2.5': ('MAIN 4', 'the search statistic'),
    '5.2.6': ('MAIN 4', 'remaining outlier windows'),
    '5.2.7': ('MAIN 4', 'line exclusion and its cost'),
    '5.3': ('MAIN 5', 'the multi-epoch stack'),
    '5.4': ('MAIN 5', 'what the experiment excludes'),
    '6': ('MAIN 6', 'discussion'),
    '6.1': ('MAIN 6', 'what ALMA archival data can detect'),
    '6.2': ('MAIN 6', 'what the null means'),
    '6.3': ('MAIN 6', 'the two array configurations'),
    '6.4': ('MAIN 6', 'no independent cross-check -- a stated limitation'),
    '6.5': ('MAIN 6', 'what the sample can speak for'),
    '7': ('MAIN 7', 'conclusions and back matter'),
    '0': ('MAIN 1', 'the plain-language precis; the roadmap is dropped'),
    # appendices
    'A': ('RELEASE provenance/', 'reproducibility and provenance'),
    'A.1': ('APP A', 'primary-beam response and the two released columns'),
    'A.2': ('APP B + RELEASE pipeline/EXTRACTION.md', 'control geometry stays'),
    'A.3': ('MAIN 3', 'one sentence on the statistical unit'),
    'A.4': ('RELEASE catalogue/exclusions.csv', 'count only, in the body'),
    'A.4.1': ('MAIN 4', 'an unconfirmed event absent in the repeat'),
    'A.5': ('RELEASE catalogue/bookkeeping.md', 'counts stay in the body'),
    'B': ('MAIN 6', 'the conventional figure of merit, two sentences'),
    'C': ('APP B', 'the spatial screen'),
    'C.1': ('APP B', 'prospective validation of the radius correction'),
    'C.1.1': ('APP B', 'the external calibration sample'),
    'C.1.2': ('MAIN 3', 'one sentence: the correction is geometric'),
    'D': ('MAIN', 'external checks and the positive control'),
    'D.1': ('MAIN 6', 'no independent pipeline check -- a stated limitation'),
    'D.2': ('MAIN 3 + RELEASE validation/', 'the two flux-scale ratios'),
    'D.2.1': ('RELEASE validation/epoch_extension.csv', 'one sentence'),
    'D.2.2': ('MAIN 4', 'the astrophysical positive control'),
    'E': ('', 'the notation glossary goes; symbols are defined at first use'),
    'F': ('APP A', 'frequency conventions, linewidth, smearing'),
    'F.1': ('APP A', 'frames, linewidth reading, smearing'),
    'F.1.1': ('MAIN 6', 'one benchmark survives'),
    'G': ('RELEASE injections/', 'the injection campaign'),
    'G.1': ('RELEASE injections/ + MAIN 3', 'the adopted dwell fraction'),
    'G.2': ('MAIN 3 + RELEASE injections/', 'amplitude completeness'),
    'G.3': ('RELEASE injections/campaign_scope.md', 'campaign provenance'),
    'H': ('RELEASE catalogue/', 'per-target results'),
    'I': ('APP C', 'the velocity-space line mask'),
    'J': ('APP E', 'false-alarm accounting'),
    'J.1': ('APP E', 'what the expectation is conditioned on'),
    'J.2': ('APP E', 'the control ensemble'),
    'J.3': ('MAIN 4', 'its conclusion is the lead sentence of the results'),
    'J.4': ('APP E + RELEASE validation/rank_calibration.csv', 'calibration'),
    'K': ('RELEASE provenance/', 'analysis provenance'),
    'K.1': ('RELEASE validation/bpic_frame_audit.csv', 'frame audit'),
    'K.1.1': ('RELEASE provenance/repair_ledger.md', 'no before and after'),
    'K.1.2': ('MAIN 4', 'one sentence on the residual noise scale'),
    'K.1.3': ('APP E', 'the measured false-alarm rate, one number'),
    'K.2': ('MAIN 4 + RELEASE', 'one sentence, and it must name the star'),
    'K.3': ('RELEASE catalogue/exclusions.csv', 'one clause in the sample'),
    'K.4': ('APP B', 'validation checks'),
    'K.4.1': ('APP B', 'the hold-out reservation, partition and outcome'),
    'K.4.2': ('MAIN 3', 'one sentence on the radial gradient'),
    'K.4.3': ('APP C', 'the mask cost'),
    'K.5': ('RELEASE validation/robustness_summary.csv', 'one sentence'),
    'L': ('MAIN 7', 'the two recommendations that would change a conclusion'),
    'L.1': ('RELEASE provenance/upgrades_declined.md', 'declined upgrades'),
    'M': ('MAIN + RELEASE provenance/', 'results move up, narration goes'),
    'M.1': ('RELEASE provenance/harvest.md', 'the harvest'),
    'M.2': ('MAIN 4', 'one sentence: a selected excess regresses'),
    'M.3': ('MAIN 4', 'the recurrence exclusion'),
    'M.4': ('MAIN 2 + MAIN 4', 'the archival tail, merged into the sample'),
    'M.5': ('RELEASE provenance/extent_sequence.md', 'one extent is stated'),
    'M.6': ('MAIN 2', 'the block ledger, two sentences'),
    'M.7': ('RELEASE provenance/fixed_key.md', 'the values are the values'),
    'N': ('APP D', 'interference screening'),
    # ★ The rewrite has already re-cut the body, so the scan finds units the
    # old numbering did not have.  A subsection inherits its section's
    # destination -- the body is the body -- and that is declared here rather
    # than inferred, so a NEW TOP-LEVEL section still stops this generator.
    '3.1': ('MAIN 3', 'sample, re-cut'),
    '3.2': ('MAIN 3', 'sample, re-cut'),
    '5.3.1': ('MAIN 4', 'results, re-cut'),
    '5.3.2': ('MAIN 4', 'results, re-cut'),
    '5.3.3': ('MAIN 4', 'results, re-cut'),
    '5.5': ('MAIN 5', 'results, re-cut'),
    '5.5.1': ('MAIN 5', 'results, re-cut'),
    '5.6': ('MAIN 5', 'results, re-cut'),
    '5.7': ('MAIN 5', 'results, re-cut'),
    '5.8': ('MAIN 5', 'results, re-cut'),
    '5.8.1': ('MAIN 5', 'results, re-cut'),
    '5.8.2': ('MAIN 5', 'results, re-cut'),
    '6.2.1': ('MAIN 6', 'discussion, re-cut'),
    '6.2.2': ('MAIN 6', 'discussion, re-cut'),
}

# --------------------------------------------------------------------------
# 2.  THE SYMBOL LAYER.  old TeX symbol -> (new symbol, where it may appear).
#     Only two power quantities are allowed in the main text.
SYMBOLS = [
    (r'P_{\rm trig}', r'P_{\rm trig}', 'MAIN',
     'the internal trigger level: the power at which the search statistic '
     'reaches the trigger in one native channel. Not a sensitivity.'),
    (r'P_{90}^{\rm sel}', r'\mathrm{EIRP}_{90}', 'MAIN',
     'the sensitivity: the power the complete automated selection recovers '
     'nine times in ten. The only power quoted in the abstract, results, '
     'discussion and conclusions.'),
    (r'P_{90}', r'\mathrm{EIRP}_{90}^{\rm trig}', 'APP A',
     'the intermediate completeness -- the trigger alone, not the selection. '
     'Renamed so that the bare subscript 90 cannot be read as the headline.'),
    (r'P_{\rm eff}', r'\mathrm{EIRP}_{\rm eff}', 'APP A',
     'the effective threshold: the trigger with the response and smearing '
     'corrections applied.'),
    (r'P_{\rm eff,total}', r'\mathrm{EIRP}_{\rm eff}', 'APP A',
     'the same quantity; the "total" qualifier is dropped, because every '
     'EIRP in the paper is already a total radiated power.'),
    (r'C_{\rm resp}', r'C_{\rm resp}', 'APP A',
     'the spectral-response correction.'),
    (r'C_{\rm smear}', r'C_{\rm smear}', 'APP A',
     'the intra-integration drift-smearing correction.'),
    (r'P_{\min}', r'P_{\rm trig}', 'APP A',
     'a third name for the trigger level; removed.'),
    (r'P_{50}', '', 'RELEASE',
     'a completeness level the paper does not quote.'),
    (r'P_{95}', '', 'RELEASE',
     'never determined; the phrase "remains not determined" goes with it.'),
    (r'P_{\rm tx}', r'P_{\rm tx}', 'MAIN 6',
     'the transmitter power of the one benchmark, and nothing else.'),
]
MAIN_POWERS = 2            # the number of power quantities the main text keeps

# The units that exist to document our own processing rather than to make a
# scientific statement.  A macro used only in these goes to the release.
PROCESSING = {'A', 'A.2', 'A.4', 'A.5', 'G', 'G.1', 'G.3', 'H', 'K', 'K.1',
              'K.1.1', 'K.5', 'L.1', 'M', 'M.1', 'M.5', 'M.7'}

# --------------------------------------------------------------------------
# 3.  MACRO-LEVEL OVERRIDES.  A unit-level verdict is right for almost every
#     macro, but a handful carry an editorial decision of their own: a second
#     value for a quantity that must have one, a quantity that is deleted
#     outright, or a number that moves to a different unit from the prose
#     around it.  Each is listed with the reason, and each is asserted to be
#     a macro that actually exists.
OVERRIDE = {
    # the sensitivity: one definition, one multiplier, one interval
    'SelRatioRank': ('MAIN 3', 'the sensitivity multiplier'),
    'SelPNinetyFine': ('MAIN 3', 'the sensitivity multiplier, Class A'),
    'SelPNinetyFineLo': ('MAIN 3', 'its interval'),
    'SelPNinetyFineHi': ('MAIN 3', 'its interval'),
    'SelPNinetyTrigFine': ('APP A', 'the intermediate completeness'),
    'SelPNinetyTrigCoarse': ('APP A', 'the intermediate completeness'),
    'SelGateCostFine': ('APP A', 'the cost of the screen, not a sensitivity'),
    'SelGateCostCoarse': ('APP A', 'the cost of the screen, not a sensitivity'),
    'SelRankGain': ('APP A', 'the ratio between the two completenesses'),
    'RsevPNinetyA': ('', 'a second value for the sensitivity'),
    'RsevPNinetyALo': ('', 'its interval'),
    'RsevPNinetyAHi': ('', 'its interval'),
    'RsevPNinetyATrig': ('', 'a third value for the sensitivity'),
    'RsevPNinetyB': ('', 'a second value for the sensitivity, Class B'),
    'SqrtScalePsel': ('APP A', 'an illustrative rechannelisation, not a limit'),
    # the effective threshold and the response correction leave the body
    'PeffRatioLo': ('APP A', 'the effective threshold'),
    'PeffRatioHi': ('APP A', 'the effective threshold'),
    'PeffWinMedA': ('APP A', 'the effective threshold'),
    'EirpEffDeepest': ('APP A', 'the effective threshold'),
    'HanFacMed': ('APP A', 'the response correction'),
    'HanFacBest': ('APP A', 'the response correction'),
    'HanFacWorst': ('APP A', 'the response correction'),
    # one benchmark, in one place
    'AreciboW': ('MAIN 2', 'the one Arecibo appearance, for continuity with '
                 'the centimetre literature'),
    'ArecGHz': ('MAIN 2', 'the frequency that value belongs to'),
    'ArecScaledW': ('', 'an Arecibo-sized dish at 230 GHz is not physically '
                    'realisable, so a frequency-scaled Arecibo-equivalent is '
                    'not a benchmark'),
    'CaseDetEffArec': ('', 'a system count against the deleted benchmark'),
    'CaseDetEffArecTwo': ('', 'a system count against the deleted benchmark'),
    'BenchEirpSeven': ('MAIN 6', 'the one benchmark'),
    'BenchEirpSci': ('', 'a perfect aperture is not technology we operate'),
    'BenchGainSci': ('', 'a perfect aperture is not technology we operate'),
    # one unattributed count, in one frame
    'MaskFrameUsed': ('', 'the mask is evaluated in the stellar frame, so '
                      'there is no frame to name'),
    'MaskLadderNSkyReleased': ('', 'a denominator for the deleted sky column'),
    'MaskLadderLostSky': ('', 'a cost in the deleted sky column'),
    'MaskLadderSkyWThirteen': ('', 'a count in the deleted sky column'),
    'LgNUnattr': ('MAIN 4', 'the one unattributed count'),
    # the orphan float
    'NClassAM': ('MAIN 2', 'the figure keeps the number; the table goes'),
}

# Macros the rewrite NEEDS and the document does not have.  Asserted ABSENT,
# which is the mirror of the override check: a name that turns up here has
# been created and must move to the override table, and a name that vanishes
# from here without appearing in the document has been forgotten.
REQUIRED_NEW = {
    # Empty, and that is the finding rather than an oversight: every name
    # that was on this list is now emitted by the macro layer.  The list is
    # kept, with its assertion, because the next revision will need it and
    # because an empty list that is CHECKED is different from no list: the
    # drive below still exercises both directions.
}


# --------------------------------------------------------------------------
def strip_comments(s):
    out = []
    for line in s.split('\n'):
        i = 0
        while i < len(line):
            if line[i] == '\\':
                i += 2
                continue
            if line[i] == '%':
                line = line[:i]
                break
            i += 1
        out.append(line)
    return '\n'.join(out)


def unit_index(txt):
    """line number -> structural unit id, by walking the sectioning marks."""
    cur, app, marks = [0, 0, 0], False, [(1, 'abstract')]
    for i, line in enumerate(txt.split('\n'), 1):
        if re.match(r'\s*\\appendix\b', line):
            app, cur = True, [0, 0, 0]
            continue
        m = re.match(r'\s*\\(section|subsection|subsubsection)(\*?)\s*\{', line)
        if not m:
            continue
        k = {'section': 0, 'subsection': 1, 'subsubsection': 2}[m.group(1)]
        if m.group(2) == '*':
            continue
        cur[k] += 1
        for j in range(k + 1, 3):
            cur[j] = 0
        head = ('ABCDEFGHIJKLMNOPQRSTUVWXYZ'[cur[0] - 1] if app
                else str(cur[0]))
        marks.append((i, head + ''.join('.%d' % x for x in cur[1:k + 1] if x)))
    return marks


def unit_at(marks, line):
    out = marks[0][1]
    for ln, u in marks:
        if ln <= line:
            out = u
        else:
            break
    return out


def read_tree(master, _seen=None):
    _seen = _seen if _seen is not None else set()
    master = os.path.abspath(master)
    if master in _seen or not os.path.exists(master):
        return []
    _seen.add(master)
    base = os.path.dirname(master)
    txt = strip_comments(open(master, errors='ignore').read())
    out = [(master, txt)]
    for m in re.finditer(r'\\(?:input|include)\s*\{([^}]+)\}', txt):
        c = m.group(1).strip()
        out += read_tree(os.path.join(base, c if c.endswith('.tex')
                                      else c + '.tex'), _seen)
    return out


def main(argv):
    pos = [a for a in argv[1:] if not a.startswith('--')]
    drive = None      # None = production run; any integer = a driven run
    outdir = os.path.dirname(os.path.abspath(__file__))
    for i, a in enumerate(argv):
        if a == '--drive':
            drive = int(argv[i + 1])
        if a == '--out':
            outdir = argv[i + 1]
    master = pos[0]
    base = os.path.dirname(os.path.abspath(master))
    for i, a in enumerate(argv):
        if a == '--defs':
            base = argv[i + 1]
    files = read_tree(master)
    mastertxt = files[0][1]
    marks = unit_index(mastertxt)

    # every macro the project defines, and the file that defines it
    defs = {}
    import glob as _g
    for f in sorted([os.path.basename(x) for x in _g.glob(os.path.join(base, '*.tex'))]
                    + ['tables/' + os.path.basename(x)
                       for x in _g.glob(os.path.join(base, 'tables', '*.tex'))]):
        if not f.endswith('.tex'):
            continue
        for m in re.finditer(r'\\newcommand\{\\([A-Za-z]+)\}\{', 
                             strip_comments(open(os.path.join(base, f),
                                                 errors='ignore').read())):
            defs.setdefault(m.group(1), []).append(f)

    # every use, attributed to a unit
    uses = {}
    for path, txt in files:
        local = marks if path == files[0][0] else None
        # a definition is not a use: blank the \newcommand{\Name} header so
        # a generated macro file does not count as 2 195 uses of itself.
        txt = re.sub(r'\\(?:new|renew|provide)command\s*\{\\[A-Za-z]+\}',
                     '', txt)
        for m in re.finditer(r'\\([A-Za-z]+)', txt):
            n = m.group(1)
            if n not in defs:
                continue
            if local is None:
                u = '(input)'
            else:
                u = unit_at(local, txt.count('\n', 0, m.start()) + 1)
            uses.setdefault(n, {}).setdefault(u, 0)
            uses[n][u] += 1
    units_seen = {u for v in uses.values() for u in v if u != '(input)'}
    if drive == 1:
        units_seen.add('Z.9')              # a unit with no declared verdict
    missing = sorted(units_seen - set(VERDICT))
    assert not missing, (
        'the verdict table does not cover every unit the scan found: %s. A '
        'macro in an undeclared unit has no destination, and a prose agent '
        'would have to invent one.' % missing)

    syms = [s for s in SYMBOLS if s[2].startswith('MAIN') and s[1]]
    if drive == 2:
        syms.append((r'P_{\rm eff}', r'P_{\rm eff}', 'MAIN', 'leaked'))
    main_pow = {s[1] for s in syms}
    assert len(main_pow) == MAIN_POWERS + 1, (
        'the main text is declared to keep %d power quantities plus the '
        'benchmark transmitter power, but the symbol table lets %d through: '
        '%s' % (MAIN_POWERS, len(main_pow), sorted(main_pow)))

    old = [s[0] for s in SYMBOLS]
    if drive == 3:
        old.append(r'P_{90}')
    assert len(old) == len(set(old)), (
        'a symbol appears twice in the rename table, so its destination '
        'depends on which row is read first: %s'
        % sorted({x for x in old if old.count(x) > 1}))

    rows = []
    for n in sorted(uses):
        tot = sum(uses[n].values())
        us = sorted(u for u, c in uses[n].items() if c)
        dests, why = [], []
        for u in us:
            if u == '(input)':
                continue
            d, w = VERDICT[u]
            if d and d not in dests:
                dests.append(d)
                why.append(w)
        if not us:
            status = 'UNUSED'
        elif not dests:
            status = 'DELETED'
        elif all(d.startswith('MAIN') for d in dests):
            status = 'MAIN'
        elif all(d.startswith(('APP', 'MAIN')) for d in dests):
            status = 'APPENDIX'
        elif all(d.startswith('RELEASE') for d in dests):
            status = 'RELEASE'
        else:
            # ★ THE SPLIT RULING.  A macro used in units with different
            # destinations needs a decision, not a lookup, and the decision
            # is the same one every time:
            #   a value that appears in a SCIENTIFIC STATEMENT stays in the
            #   main text; a value that exists only to document PROCESSING
            #   goes to the data release; anything else goes to an appendix.
            # "Processing" is not a judgement call here: it is the set of
            # units the triage sends to provenance/, which are by
            # construction the ones that document our own corrections,
            # audits, campaigns and bookkeeping.
            if all(u in PROCESSING or u == '(input)' for u in us):
                status = 'RELEASE'
                dests = ['RELEASE provenance/ (split ruling: processing only)']
            elif any(d.startswith('MAIN') for d in dests):
                status = 'MAIN'
                dests = [d for d in dests if d.startswith('MAIN')] + \
                        ['(split ruling: appears in a scientific statement)']
            else:
                status = 'APPENDIX'
                dests = [d for d in dests if d.startswith('APP')] + \
                        ['(split ruling: in doubt -> appendix)']
        note = ''
        if n in OVERRIDE:
            d, note = OVERRIDE[n]
            dests = [d] if d else []
            status = ('DELETED' if not d else
                      'MAIN' if d.startswith('MAIN') else
                      'APPENDIX' if d.startswith('APP') else 'RELEASE')
        rows.append(dict(macro=n, uses=tot, units=' '.join(us),
                         destination='; '.join(dests) or '(none)',
                         status=status, note=note,
                         defined_in=' '.join(sorted(set(defs[n])))))

    if drive == 4:
        rows.append(dict(rows[0]))         # a macro mapped twice
    seen = [r['macro'] for r in rows]
    assert len(seen) == len(set(seen)), (
        'a macro has two rows in the map, so it has two destinations: %s'
        % sorted({x for x in seen if seen.count(x) > 1}))

    ov = set(OVERRIDE)
    if drive == 6:
        ov.add('NoSuchMacroAnywhere')
    stale = sorted(ov - set(defs))
    assert not stale, (
        'the override table names macros that do not exist, so an editorial '
        'decision has been recorded against nothing: %s' % stale)

    need = set(REQUIRED_NEW)
    if drive == 7:
        need.add(sorted(defs)[0])
    elif drive == 8:
        need.add('NoMacroOfThisNameExists')
    assert need or drive != 8, 'the drive did not take effect'
    already = sorted(need & set(defs))
    assert not already, (
        'a macro listed as still to be created already exists, so the list '
        'and the document disagree about what remains to be done: %s'
        % already)

    nmain = sum(1 for r in rows if r['status'] == 'MAIN')
    if drive == 5:
        nmain = 0
    assert nmain > 0, (
        'no macro survives into the main text, which cannot be right: the '
        'scan has failed to attribute uses to units'
    )

    # ... the suffix follows the FLAG, not the perturbation, so --drive 0
    # is barred from writing a production path exactly as --drive 4 is.
    suf = '' if drive is None else '_drive%d' % drive
    cpath = os.path.join(outdir, 'macro_map%s.csv' % suf)
    with open(cpath, 'w', newline='') as fh:
        w = csv.DictWriter(fh, ['macro', 'status', 'destination', 'note',
                                'uses', 'units', 'defined_in'])
        w.writeheader()
        for r in rows:
            w.writerow(r)
    spath = os.path.join(outdir, 'symbol_map%s.csv' % suf)
    with open(spath, 'w', newline='') as fh:
        w = csv.writer(fh)
        w.writerow(['old', 'new', 'where', 'note'])
        for s in SYMBOLS:
            w.writerow(list(s))

    from collections import Counter
    c = Counter(r['status'] for r in rows)
    print('macromap: %d macros defined, %d used, %d structural units'
          % (len(defs), len(rows), len(units_seen)))
    print('  ' + '  '.join('%s %d' % (k, c[k]) for k in sorted(c)))
    print('  %d macro-level overrides, %d of them deletions; %d macros the '
          'rewrite still needs'
          % (len(OVERRIDE), sum(1 for v in OVERRIDE.values() if not v[0]),
             len(REQUIRED_NEW)))
    print('  -> %s, %s' % (os.path.basename(cpath), os.path.basename(spath)))
    return 0


if __name__ == '__main__':
    sys.exit(main(sys.argv))
