#!/usr/bin/env python3
"""THE ONE OWNER OF THE STAR-BAND WITHHOLDING RULE.

    import census_rule
    withheld = census_rule.withheld(kept)
    good = [r for r in kept if r not in withheld]

and, as a gate:

    python3 census_rule.py            # R1-R3 over the live generators
    python3 census_rule.py --drive N   # N=1..3, each must FAIL

★★★ WHY THIS FILE EXISTS.
The rule that set aside the epsilon Eridani Band 6 windows was written out
**seven times** in live generators -- `survey_stats.py`,
`survey_stats_round10.py`, `round8_calc.py`, `round9_calc.py`,
`round10_calc.py`, `v352_calc.py` and `make_figures_v328.py` -- each
recomputing the census from the same export, with no owner.  One rule, seven
copies.  That is the same defect family as the fourteen name-keyed joins: not
a wrong line, but a line that has to be found seven times to be changed once,
and that therefore drifts.  Withdrawing it in round 17 meant editing seven
files, and a reader of any one of them could not tell whether it was the
authority or a copy.

So the rule lives here, once, and the gate below fails the build if a
generator grows its own copy again.

★★ AND THE RULE IS NOW EMPTY, WHICH IS NOT THE SAME AS ABSENT.
`beam_r17.py` measured the premise false: those pointings put the star
0.75-0.82 lambda/D off axis, the blocked aperture does not reach its first
null until 1.36 lambda/D, so they are inside the main lobe where the two beam
forms agree to 7 per cent -- and four of the twelve put the star AT the
pointing centre, where no beam argument applies to them at all.  The category
is therefore kept and asserted EMPTY rather than deleted, because
`\\NWithheld` is a published count and a denominator in the block ledger: a
deleted category would make the ledger silently stop summing, while an empty
one makes it sum to the same total with a visible zero.

Clauses:
  R1  no live generator carries its own copy of a star-band withholding rule;
      the only occurrence of the pattern is in this file.
  R2  every generator that forms a census selection imports this module --
      so R1 cannot pass merely because a generator stopped selecting at all.
  R3  the sweep is not vacuous: it read a known number of generators, and the
      pattern it searches for is demonstrated to match a reintroduced copy.
"""
import ast
import glob
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))

#: ★ The reason, in one place, so that a generator does not have to carry it
#: as a comment seven times over.
REASON = ('the eps Eri Band 6 star-band rule is withdrawn: those pointings '
          'are inside the main lobe (beam_r17.py measures 0.75-0.82 lambda/D '
          'against a first null at 1.36) and four of the twelve put the star '
          'at the pointing centre, so nothing was excluded on a beam '
          'argument that holds')

#: the generators that form a census selection and must use this module.
#: ★ NINE, not the seven the round-17 report listed.  `v346_calc.py` and
#: `blockledger_v411.py` were found by this gate's own first run: the first
#: was STILL WITHHOLDING after the census change, so it published
#: \NSearchedStars over 89 stars while \NStars said 90; the second holds the
#: separate extension-stratum rule.  A hand-written list of copies is exactly
#: what this module exists to replace, so the list below is the list of
#: CONSUMERS -- generators required to import the owner -- and R1's sweep is
#: what finds a copy, over every .py in the build.
CONSUMERS = ('survey_stats.py', 'survey_stats_round10.py', 'round8_calc.py',
             'round9_calc.py', 'round10_calc.py', 'v352_calc.py',
             'make_figures_v328.py', 'v346_calc.py', 'blockledger_v411.py')

#: ★★ A STAR-BAND WITHHOLDING RULE, AND NOT MERELY A STAR-BAND SELECTION.
#: My first pattern was "a star name beside a band test", and it fired on
#: thirteen generators -- correctly, in the sense that all thirteen DO select
#: a star-band subset, and wrongly, because selecting one is a legitimate
#: operation.  `v343_calc.py` and `round9_calc.py` pick CP-72 2713's Band 7
#: rows to fit them; `beam_r17.py`, `extension_v399.py` and `sens_r12.py` pick
#: the eps Eri Band 6 rows precisely in order to REPORT on them.  None of
#: those is the defect.
#: The defect is a star-band test whose result REMOVES rows from the census,
#: and it had exactly two shapes in the seven copies:
#:    withheld = [r for r in kept if r['star_name'] == 'eps Eri' and r['band_x'] == 6]
#:    GOOD     = [r for r in kept if not (r['star_name'] == 'eps Eri' and r['band_x'] == 6)]
#: i.e. assigned to a withholding name, or negated.  Those two are what this
#: searches for.  A gate that fires on a legitimate operation gets switched
#: off, which is a way of having no gate; a gate narrowed until it passes is
#: worse.  This is narrowed to the shape of the defect and is driven on it.
_STARBAND = r"""star_name['"]?\s*\]?\s*==\s*['"][^'"]+['"][^\n]{0,80}band"""
#: ★★★★ AND A THIRD SHAPE, FOUND BY THE BUILD AND NOT BY THIS PATTERN:
#: THE RULE BEHIND A NAMED PREDICATE.  `ledger_r14.py` carried
#:     def _is_eps(r):
#:         return r['star_name'] == 'eps Eri' and (r['band'] or 0) == 6
#:     WITHHELD = [r for r in KEPT if _is_eps(r)]
#: -- a TENTH copy.  Neither of the two shapes above can see it: the call site
#: names no star and no band, and the predicate assigns nothing.  So a
#: `return` or `lambda` carrying the star-band test is the third shape, and it
#: is the one that hides best, because at the use site it reads as a tidy
#: abstraction.  ► The general lesson: a sweep for a RULE has to look where
#: the rule is WRITTEN, not where it is applied.
RULE = re.compile(
    r'(?:'
    r'(?:withheld|withhold|WITHHELD|setaside|set_aside)\s*=\s*\[[^\n]{0,200}'
    + _STARBAND +
    r')|(?:'
    r'not\s*\([^\n]{0,60}' + _STARBAND +
    r')|(?:'
    r'(?:return|lambda[^:]{0,40}:)\s*[^\n]{0,40}' + _STARBAND +
    r')', re.I)

#: ★★★ THE PREDICATE IS THE RULE, SO THE OWNER EXPORTS IT.
#: `beam_r17.py` and `ledger_r14.py` each defined their own
#:     def is_eps(r): return r['star_name'] == 'eps Eri' and (r['band'] or 0) == 6
#: -- and `beam_r17.py`'s is entirely legitimate: it SELECTS the star-band in
#: order to report on it.  Allowlisting the two files would have been the easy
#: answer and the wrong one, because the star name and the band number would
#: then still be written in three places.  Exporting the predicate means no
#: file spells the rule and R1 needs no exception.
STAR, BAND = 'eps Eri', 6


def is_star_band(r):
    """True if `r` is a window of the star-band this rule is about.

    Accepts either the catalogue's `band` (a string) or the export's
    `band_x`/`band` (an int or None), because the two differ and a caller
    should not have to know which it holds.
    """
    b = r.get('band_x', r.get('band'))
    try:
        b = int(b) if b not in (None, '') else 0
    except (TypeError, ValueError):
        b = 0
    return r.get('star_name') == STAR and b == BAND


def withheld(rows):
    """The star-band windows set aside from the census: none.

    Returns a list so that callers written for the old code
    (`good = [r for r in kept if r not in withheld]`) are unchanged.
    """
    return []


def withheld_extension(rows):
    """The eps Eri Band 6 windows set aside from the ARCHIVAL EXTENSION set.

    ★★ THIS IS A DIFFERENT RULE FROM `withheld()` ABOVE AND IT IS STILL IN
    FORCE.  The round-17 ruling admitted the TWELVE census-scope eps Eri
    Band 6 windows to the primary census.  The other thirty-two are
    archival-extension scope, and the coordinator's own words are that they
    "are a separate question" -- so nothing here decides it.

    What this function changes is only that the rule now has an owner.  It
    was found by `census_rule.py`'s own gate as an EIGHTH copy, in
    `blockledger_v411.py`, after a report that listed seven; leaving it as a
    comprehension inside that file is exactly the drift this module exists to
    stop.  The behaviour is unchanged and no published number moves.

    ► OPEN ITEM for a later round: whether the 32 extension windows are
    admitted too.  If they are, this function is deleted and its one caller
    passes `rows` through; the decision then lives in one place.
    """
    return [r for r in rows
            if r['star_name'] == 'eps Eri' and int(r.get('band') or 0) == 6]


def assert_empty(n_withheld):
    """For a caller that publishes the count."""
    assert n_withheld == 0, (
        'the withholding category is not empty (%d), but no star-band rule is '
        'in force: %s' % (n_withheld, REASON))


# ------------------------------------------------------------------ the gate
def main(argv):
    drive = 0
    for i, a in enumerate(argv):
        if a == '--drive':
            drive = int(argv[i + 1])

    srcs = sorted(p for p in glob.glob(os.path.join(HERE, '*.py'))
                  if os.path.basename(p) != 'census_rule.py')
    # the gate's own file is excluded by name, and that exclusion is checked
    # below (R3) by requiring the pattern to match THIS file.
    copies, missing, read = [], [], 0
    for p in srcs:
        txt = open(p, errors='ignore').read()
        read += 1
        body = re.sub(r'(?m)^\s*#.*$', '', txt)      # comments are allowed to
        if drive == 1 and os.path.basename(p) == CONSUMERS[0]:
            # ★ the drive must inject one of the TWO SHAPES R1 searches for.
            # My first version assigned to `w`, which is a star-band
            # SELECTION and not a withholding, so the drive stopped firing
            # the moment the pattern was correctly narrowed -- the drive was
            # testing the loose pattern, not the gate.
            body += ("\ngood = [r for r in kept if not "
                     "(r['star_name'] == 'eps Eri' and r['band_x'] == 6)]\n")
        if RULE.search(body):                        # describe the old rule
            copies.append(os.path.basename(p))
    for c in CONSUMERS:
        p = os.path.join(HERE, c)
        if not os.path.exists(p):
            missing.append('%s is not on disk, so the consumer list is stale'
                           % c)
            continue
        txt = open(p, errors='ignore').read()
        if drive == 2 and c == CONSUMERS[1]:
            txt = txt.replace('import census_rule', 'pass')
        # ★★ AST, NOT A REGEX.  R2 used to grep for the import line, and that
        # is how my own first insertion passed it while sitting INSIDE
        # v352_calc.py's module docstring, where "from a stated definition in
        # the code beside it" matched an import pattern.  The generator then
        # died with NameError at run time on a check that had just said yes.
        # A top-level `ast.Import` node is the thing being claimed, so it is
        # the thing tested.
        try:
            tree = ast.parse(txt)
        except SyntaxError as exc:
            missing.append('%s does not parse (%s), so nothing about it can '
                           'be checked' % (c, exc))
            continue
        if not any(isinstance(n, ast.Import)
                   and any(a.name == 'census_rule' for a in n.names)
                   for n in tree.body):
            missing.append('%s forms a census selection and has no top-level '
                           'import of census_rule (a matching line inside a '
                           'docstring or a function does not count)' % c)

    fails = []
    for c in copies:
        fails.append('R1 %s carries its own star-band withholding rule; the '
                     'rule has one owner (census_rule.py) and this is a '
                     'second copy' % c)
    fails += ['R2 ' + m for m in missing]
    # R3, anti-vacuity, both directions.
    if read < 50:
        fails.append('R3 the sweep read only %d generator(s); it is not '
                     'looking at the build' % read)
    if len(CONSUMERS) < 9:
        fails.append('R3 the consumer list has shrunk to %d; a generator that '
                     'stopped selecting should be removed deliberately, with '
                     'a note' % len(CONSUMERS))
    _self = open(__file__, errors='ignore').read()
    if drive == 3:
        _self = 'nothing here matches'
    if not RULE.search(_self):
        fails.append('R3 the pattern R1 searches for does not match the rule '
                     'as written in this file, so R1 is searching for '
                     'something that no longer exists and cannot fire')

    print('census_rule: %d generator(s) swept, %d consumer(s) required, '
          'withheld category is empty by measurement' % (read, len(CONSUMERS)))
    for f in fails:
        print('  FAIL ' + f)
    print('census_rule: %d FAIL' % len(fails))
    if drive and not fails:
        print('  DRIVE %d DID NOT FAIL -- the clause it exercises is vacuous'
              % drive)
        return 2
    return 1 if fails else 0


if __name__ == '__main__':
    sys.exit(main(sys.argv))
