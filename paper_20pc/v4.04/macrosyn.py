#!/usr/bin/env python3
r"""Gate: macros that claim to be the same quantity must agree.

Referee 2's M2 lists sixteen quantities the manuscript prints with more than
one value.  Thirteen of the sixteen are **two macros that claim to be the
same quantity**, and no tool in the build could see them:

  * `prosenum_v399.py` compares a prose literal to one of two named macros;
  * `consistency_v399.py` asserts three fixed relations;
  * `audit_numbers_v385.py` compares each macro to *its own* source file, so
    `\PromoteSysMedA` = 2.9e15 and `\MasonMedPsel` = 1.9e15 were each audited
    against their own construction and both passed;
  * `literalsweep.py` is a report with no notion of which macro a literal
    ought to match.

Nothing compared two macros with each other.  This does.

Three checks, all fatal:

  GROUPS     -- declared sets of macros that must carry the same value, to a
                stated tolerance.
  RELATIONS  -- declared arithmetic identities between macros: a ledger that
                must close.
  SOURCES    -- every macro file the manuscript reads must be written by a
                generator in this folder.  `survey_numbers_round{5,6,7}.tex`
                were restored by `cp` from `frozen_macros/` and carried a
                v3.32 extraction into a v4.01 paper; nothing could rebuild
                them, and twelve of their macros were typeset.

and one non-fatal report:

  DEFERRED   -- pairs known to disagree, each with the owner of the fix.  If
                a deferred pair is found to AGREE, that is reported too, so
                it gets promoted to GROUPS rather than lingering.

Run from gate.sh and from make_all.sh (before retire_macros.py).
"""
import glob
import os
import re
import sys

os.chdir(os.path.dirname(os.path.abspath(__file__)))

# =====================================================================
# the declared table
# =====================================================================
#: sets of macros that must agree.  `tol` is a RELATIVE tolerance; the
#: default of 0 means the values must be equal as written.
GROUPS = [
    dict(name='stage-1 windows',
         macros=['NStageOneWin', 'NStageTableRows', 'VgNFlag',
                 'SepNFlagFull', 'NSpatial'],
         why='R2-M2 row 1: 12 in Tables 1/4/6 and Fig. 2, 13 in S5.2.1'),
    dict(name='unattributed stage-1 events',
         macros=['NUnattrib', 'NStageOneUnattrib', 'RobNUnattrib',
                 'MaskCrossOutStageOne'],
         why='R2-M2 row 2: 2 in the abstract, 4 in S5.2 and Table 3'),
    dict(name='per-system median P90^sel',
         macros=['PromoteSysMedA', 'SdMed', 'MasonMedPsel', 'OccEirpMed'],
         why='R2-M2 row 9: 2.9e15 in the abstract, 1.9e15 in S6.2 and App. B'),
    dict(name='rank-only chance expectation of flagged windows',
         macros=['ExpFlags', 'RankCalExpIdeal', 'ExpDistinctDen'],
         tol=0.02,
         why='R2-M2 row 8: the same 1655/513 printed as 3.23, 3.23 and 3.2'),
    dict(name='Class A window count',
         macros=['NWinA', 'NFine'],
         why='two names for the fine-channel stratum'),
    dict(name='default drift ceiling',
         macros=['AccelCeilMed', 'AccelCeilLo', 'DomAAccelLo'],
         tol=0.01,
         why='R1-9: the caption compared TRAPPIST-1 b against the widened '
             'ceiling under the median ceiling\'s name'),
    dict(name='widened drift ceiling',
         macros=['AccelCeilMax', 'AccelCeilHi', 'DomAAccelHi'],
         tol=0.01, why='R1-9, as above'),
    dict(name='TRAPPIST-1 b line-of-sight acceleration',
         macros=['AccelWorstVal', 'OrbAccTrapb'],
         why='R1-9: one was a frozen v3.31 literal, one the figure\'s own '
             'orbital model'),
    dict(name='line-mask cost at the adopted half-width',
         macros=['MaskGrossPct', 'MaskBWFifty'],
         why='the half-width sweep must reproduce the adopted value'),
    dict(name='in-mask crossings that did not reach stage 1',
         macros=['MaskCrossInNoFlag', 'MaskCrossInNoFlagN'],
         why='R2-M2 row 13: computed independently by v362_calc and '
             'exfrozen_v401'),
    dict(name='in-mask crossings that reached stage 1',
         macros=['MaskCrossInStageOne', 'MaskCrossInStageOneN'],
         why='R2-M2 row 13, as above'),
]

#: arithmetic identities.  Each is a python expression over macro names.
RELATIONS = [
    dict(name='the crossing ledger closes',
         expr='NHits == NSpatial + MaskCrossInNoFlag + NonExcRingGe',
         why='R2-M2 S17.4: App. J read 56 - 12 - 2 = 16'),
    dict(name='stage-1 crossings split by the mask',
         expr='NSpatial == MaskCrossInStageOne + MaskCrossOutStageOne',
         why='R2-M2 row 13'),
    dict(name='in-mask crossings split by the screen',
         expr='MaskCrossIn == MaskCrossInStageOne + MaskCrossInNoFlag',
         why='R2-M2 row 13: "16, of which 10 stage-1 and 6 others"'),
    dict(name='windows split by array',
         expr='NWindows == NWinTwelveM + NWinSevenM',
         why='R2-M2 rows 11 and 12: 601 + 1071 = 1672, neither 1655 nor 1725'),
    dict(name='windows with a recoverable control draw split by array',
         expr='SepNWin == SepNTwelveWin + SepNSevenWin',
         why='R2-M2 row 12: Table 8 never said its denominator was smaller'),
    dict(name='the rank-uniformity test covers the released catalogue',
         expr='VerNTested + VerNUnmatched == NWindows',
         why='R2-M2 row 11: the KS ran on the raw export, 1071 ACA windows'),
]

#: known disagreements, with the owner of the fix.  NOT fatal.  Listing one
#: here is a statement that it is someone's open item, not that it is fine.
DEFERRED = [
    # v4.03: the chain rewrite HAS happened.  ledger_v403.py now covers all
    # 56 crossings and NONE of the macros below is typeset any more -- every
    # one is dropped by retire_macros.py.  They are kept here because their
    # GENERATORS still run (visfit_v385_calc.py, whose output visgain_v399.py
    # reads), so the divergence is still reachable and must stay visible
    # until those generators are retired.  Do NOT delete these entries as
    # "fixed": the fix is deleting the generators, not the prose.
    dict(macros=['NStageOneWin', 'NVisTested'],
         owner='retire visfit_v385_calc.py; repoint visgain_v399.py '
               'at ledger_v403',
         why='the frozen single-channel visibility set covered 13 windows '
             'against 56 crossings in the v4.03 ledger; NOT TYPESET since '
             'v4.03'),
    dict(macros=['NStageOneUnattrib', 'NVisUnatt'],
         owner='retire visfit_v385_calc.py; repoint visgain_v399.py '
               'at ledger_v403',
         why='the frozen vistest file still carries HD 14055 and HD 23484, '
             'which the ACA repair removed; NOT TYPESET since v4.03'),
    dict(macros=['NStageOneLine', 'NVisAtt'],
         owner='retire visfit_v385_calc.py; repoint visgain_v399.py '
               'at ledger_v403',
         why='R2-M2 S17.6: 9 in the frozen visibility set, 10 in the '
             'catalogue; NOT TYPESET since v4.03'),
    dict(macros=['VisHdFortyRe', 'FitHdFortyRe'],
         owner='retire visfit_v385_calc.py; repoint visgain_v399.py '
               'at ledger_v403',
         why='R2-M2 row 5: two estimators reported under the same words; '
             'neither is typeset since v4.03'),
    dict(macros=['VisMaxReSig', 'FitUnattMaxAbs'],
         owner='retire visfit_v385_calc.py; repoint visgain_v399.py '
               'at ledger_v403',
         why='R2-M2 row 7: the 2.5 belongs to a retired window; neither is '
             'typeset since v4.03'),
    dict(macros=['SelTransFineLo', 'StratTransferNineLo'],
         owner='R2-M3.3: one transfer bracket, from the M3a campaign',
         why='R2-M2 row 10: a bootstrap over configurations against the '
             'min/max spread of a different campaign'),
    dict(macros=['SelTransFineHi', 'StratTransferNineHi'],
         owner='R2-M3.3, as above', why='R2-M2 row 10'),
    dict(macros=['ClustStageMean', 'PriMean'],
         owner=('R2-8 CLOSED at v4.04: 0.89 is the survey\'s single chance '
                'expectation; 1.3 is the same quantity with the measured tail '
                'factor applied and is labelled in the text as a comparison, '
                'not a second expectation. 4.7 and 3.23 are no longer quoted '
                'as expected CANDIDATE counts anywhere'),
         why='R2-M2 row 8: the same quantity, block-clustered and '
             'trigger-conditioned, with and without the x1.4 '
             'non-exchangeability tail factor; both are now labelled as such '
             'in App. J but two generators still compute it'),
    dict(macros=['FlagTVir', 'CampUnOneT'],
         owner='RC-3: campaign_v372.json is a pre-repair record',
         why='R2-M2 row 3: 61 Vir T* is 5.96 in the catalogue and 6.16 in '
             'the held-out campaign file'),
]


def declared_macros():
    """Every macro name this gate needs.  retire_macros.py must not drop
    them merely because the manuscript does not typeset them: a macro read
    by a gate is referenced."""
    out = set()
    for g in GROUPS:
        out |= set(g['macros'])
    for d in DEFERRED:
        out |= set(d['macros'])
    for r in RELATIONS:
        out |= set(re.findall(r'[A-Za-z]+', r['expr']))
    return out


def main():
    # =====================================================================
    # reading the macro set
    # =====================================================================
    MACFILES = sorted(glob.glob('survey_numbers*.tex'))
    RAW, WHERE = {}, {}
    for fn in MACFILES:
        for m in re.finditer(r'\\newcommand\{\\([A-Za-z]+)\}\{(.*)\}\s*$',
                             open(fn, encoding='utf-8').read(), re.M):
            RAW[m.group(1)] = m.group(2)
            WHERE[m.group(1)] = fn

    _SCI = re.compile(r'^\$?([-+0-9.]+)\s*\\times\s*10\^\{?(-?\d+)\}?\$?$')


    def value(name):
        """The numeric value of a macro, or None if it is not a bare number."""
        v = RAW.get(name)
        if v is None:
            return None
        s = v.strip().replace('\\,', '').replace('$', '').replace('~', '')
        s = s.replace('\\%', '').strip()
        s = re.sub(r'^[=<>]+\s*', '', s)            # \pv-style relation prefixes
        m = _SCI.match(v.strip().replace('\\,', ''))
        if m:
            return float(m.group(1)) * 10.0 ** int(m.group(2))
        try:
            return float(s)
        except ValueError:
            return None


    FAIL, NOTE = [], []

    # =====================================================================
    # (1) GROUPS
    # =====================================================================
    for g in GROUPS:
        vals = {n: value(n) for n in g['macros']}
        missing = [n for n, v in vals.items() if v is None]
        have = {n: v for n, v in vals.items() if v is not None}
        if missing:
            NOTE.append('group %-46s not defined: %s'
                        % (g['name'], ', '.join(missing)))
        if len(have) < 2:
            continue
        tol = g.get('tol', 0.0)
        ref = max(have.values(), key=abs)
        bad = {n: v for n, v in have.items()
               if abs(v - ref) > tol * max(abs(ref), 1e-300) + 1e-12}
        if bad:
            FAIL.append('GROUP  %s\n         %s\n         (%s)'
                        % (g['name'],
                           '; '.join('\\%s = %s' % (n, RAW[n]) for n in have),
                           g['why']))

    # =====================================================================
    # (2) RELATIONS
    # =====================================================================
    for r in RELATIONS:
        names = sorted(set(re.findall(r'[A-Za-z]+', r['expr'])))
        env = {n: value(n) for n in names}
        if any(v is None for v in env.values()):
            NOTE.append('relation %-43s not evaluable: %s'
                        % (r['name'],
                           ', '.join(n for n in names if env[n] is None)))
            continue
        if not eval(r['expr'], {'__builtins__': {}}, env):      # noqa: S307
            FAIL.append('RELATION  %s\n            %s\n            %s\n            (%s)'
                        % (r['name'], r['expr'],
                           '; '.join('\\%s = %s' % (n, RAW[n]) for n in names),
                           r['why']))

    # =====================================================================
    # (3) SOURCES -- every macro file must have a generator that writes it
    # =====================================================================
    PYSRC = {}
    for py in sorted(glob.glob('*.py')):
        if os.path.basename(py) == os.path.basename(__file__):
            continue
        PYSRC[py] = open(py, encoding='utf-8', errors='ignore').read()

    # roundcollide.py already enforces exactly-one-writer for the numbered round
    # files, with a write-context heuristic that copes with `OUT = ...` idioms.
    # What it could NOT see, and what this adds, is the escape hatch it granted:
    # a macro file with no generator at all, restored by `cp` in make_all.sh.
    MAKEALL = open('make_all.sh', encoding='utf-8').read()
    for fn in MACFILES:
        named = [py for py, src in PYSRC.items() if fn in src]
        copied = re.search(r'^\s*cp\s+\S*%s' % re.escape(fn), MAKEALL, re.M)
        if copied:
            FAIL.append('SOURCE  %s is restored by `cp` in make_all.sh. A macro '
                        'file the build cannot recompute is a second extraction '
                        '(R2-M2); give it a generator or delete it.' % fn)
        elif not named:
            FAIL.append('SOURCE  %s is typeset but no .py in this folder names '
                        'it, so nothing can rebuild it (R2-M2).' % fn)

    # =====================================================================
    # (4) DEFERRED -- reported, never fatal
    # =====================================================================
    DEF_OUT = []
    for d in DEFERRED:
        vals = {n: value(n) for n in d['macros']}
        have = {n: v for n, v in vals.items() if v is not None}
        if len(have) < 2:
            DEF_OUT.append('  [gone]    %s -- %s'
                           % (' vs '.join(d['macros']), d['owner']))
        elif len(set(have.values())) == 1:
            DEF_OUT.append('  [AGREES]  %s = %s -- promote to GROUPS (%s)'
                           % (' vs '.join(d['macros']),
                              list(have.values())[0], d['owner']))
        else:
            DEF_OUT.append('  [open]    %s -- owner: %s'
                           % ('; '.join('\\%s = %s' % (n, RAW[n]) for n in have),
                              d['owner']))

    print('macrosyn: %d groups, %d relations, %d macro files, %d deferred'
          % (len(GROUPS), len(RELATIONS), len(MACFILES), len(DEFERRED)))
    for n in NOTE:
        print('  note   %s' % n)
    if DEF_OUT:
        print('  known divergences, not enforced:')
        for d in DEF_OUT:
            print(d)
    for f in FAIL:
        print('  **FAIL** %s' % f)
    print('macrosyn: %d problem(s)' % len(FAIL))
    sys.exit(1 if FAIL else 0)


if __name__ == '__main__':
    main()
