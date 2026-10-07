#!/usr/bin/env python3
"""Round 87 (v4.04, referee 2 item 7): close the sample ledgers.

Three arithmetic objections, all correct as stated, all with the same root
cause -- two populations being described with one phrase.

(1) THE EXTENSION LEDGER DOES NOT CLOSE.  136 in-scope blocks were processed,
    115 are reported as searched, 8 were withheld by the survey's own eps Eri
    rule: 13 are unaccounted for.  They are not missing.  The extension
    ANALYSIS is a snapshot (`export_extension.json`, 2026-09-22) taken while
    the mining campaign was still running, and the block-fate ledger is a
    later snapshot (2026-09-24).  13 blocks were processed between the two
    and are not in the extension analysis.  That is a statement about when
    two frozen files were cut, and it is now printed rather than left as a
    residue.

(2) 20 VERSUS 17 UNCALIBRATED.  Both numbers are right and they count
    different sets: \\LedNoCalib is over the 177 in-scope blocks the original
    work list missed, \\FateNoCal is over the 41 of those that remain
    unsearched.  The second is a subset of the first.

(3) "79 PER CENT" IS NOT THE SAME QUANTITY AS "42 OF 82".  79 per cent is the
    fraction of systems holding more than one ARCHIVED execution block, of any
    separation.  42 of 82 is the fraction whose SEARCHED epochs are more than
    a day apart.  Extending the search to every archived block cannot deliver
    the first as if it were the second: on the searched blocks only a fraction
    of multi-block systems clear the one-day bar, and applying that fraction
    to the archived count gives the realistic figure, which is close to the
    referee's own 63 per cent.  Both numbers are now printed with their
    criterion attached.

Everything is recomputed from the released catalogue and the two frozen
campaign records; nothing is transcribed.

-> survey_numbers_round87.tex
"""
import collections
import csv
import json
import os

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, 'survey_numbers_round87.tex')

ROWS = list(csv.DictReader(open(os.path.join(HERE,
                                             'per_target_results_v3.99.csv'))))
EXT = json.load(open(os.path.join(HERE, 'export_extension.json')))
BF = json.load(open(os.path.join(HERE, 'blockfate_v400.json')))
EX = json.load(open(os.path.join(HERE, 'extension_v399.json')))

M = {}


def m(k, v):
    M[k] = v


# ------------------------------------------------------ (1) the 13 blocks
processed = BF['counts']['done']
in_snapshot = EXT['n_blocks']
reported = EX['n_blocks']
withheld_blocks = len({r['eb'] for r in EXT['rows']
                       if r['star_name'] == 'eps Eri'
                       and int(r.get('band') or 0) == 6})
later = processed - in_snapshot

m('LgxProcessed', '%d' % processed)
m('LgxSnapshot', '%d' % in_snapshot)
m('LgxReported', '%d' % reported)
m('LgxWithheld', '%d' % withheld_blocks)
m('LgxLater', '%d' % later)
m('LgxSnapDate', EXT['snapshot'].split('T')[0])

# The identity the appendix now prints.  Both halves are asserted: the
# snapshot must close exactly, and the remainder must be non-negative --
# a later snapshot with FEWER processed blocks than the earlier one would
# mean one of the two records is not what it says it is.
assert in_snapshot == reported + withheld_blocks, \
    (in_snapshot, reported, withheld_blocks)
assert later >= 0, later
assert processed == reported + withheld_blocks + later, \
    (processed, reported, withheld_blocks, later)

# ------------------------------------------------- (2) 20 versus 17
# Read both from the generated macro files rather than retyping, and assert
# the containment the prose claims.
def texval(name):
    for fn in sorted(os.listdir(HERE)):
        if fn.startswith('survey_numbers') and fn.endswith('.tex'):
            for line in open(os.path.join(HERE, fn)):
                if line.startswith('\\newcommand{\\%s}{' % name):
                    return line.split('}{', 1)[1].rsplit('}', 1)[0]
    return None


_wide = texval('LedNoCalib')
_narrow = texval('FateNoCal')
assert _wide is not None and _narrow is not None, (_wide, _narrow)
m('LgxNoCalWide', _wide)
m('LgxNoCalNarrow', _narrow)
assert int(_narrow) <= int(_wide), (_narrow, _wide)

# ------------------------------------ (1b) the hold-out, stated once
# The OTHER out-of-sample set.  Its size is computed from the frozen hold-out
# export so that the three numbers the manuscript quotes for it (blocks,
# windows, stars) cannot drift apart.
HOLD = json.load(open(os.path.join(HERE, 'holdout_export_v381.json')))['rows']
m('HoldWinN', '%d' % len(HOLD))
m('HoldStarN', '%d' % len({r['star_name'] for r in HOLD}))
m('HoldBlockN', '%d' % len({r['eb'] for r in HOLD}))
assert int(texval('LedHoldout')) == len({r['eb'] for r in HOLD}), \
    (texval('LedHoldout'), len({r['eb'] for r in HOLD}))

# --------------------------------------- (3) recurrence coverage, two ways
sysb = collections.defaultdict(set)
for r in ROWS:
    sysb[r['system_id']].add(r['eb'])
nsys = len(sysb)
multi_searched = sum(1 for s in sysb if len(sysb[s]) > 1)
_ao = texval('NSysRecArchOnly')
assert _ao is not None, (
    'NSysRecArchOnly is missing.  retire_macros.py strips macros the '
    'manuscript does not reference, so this generator must run inside '
    'make_all.sh after v363_calc.py, and the manuscript must keep at least '
    'one \\NSysRecArchOnly reference alive.')
arch_only = int(_ao)
multi_arch = multi_searched + arch_only
indep = int(texval('EpIndep'))
years = int(texval('EpYears'))

m('LgxNSys', '%d' % nsys)
m('LgxMultiSearched', '%d' % multi_searched)
m('LgxMultiSearchedPct', '%.0f' % (100.0 * multi_searched / nsys))
m('LgxMultiArch', '%d' % multi_arch)
m('LgxMultiArchPct', '%.0f' % (100.0 * multi_arch / nsys))
m('LgxIndepPct', '%.0f' % (100.0 * indep / nsys))
m('LgxYearsPct', '%.0f' % (100.0 * years / nsys))

# What fraction of multi-block systems actually clear the one-day bar, and
# what that implies for extending the search to every archived block.  This
# is the number the referee computed as 63 per cent by a different route.
frac = indep / float(multi_searched)
proj = multi_arch * frac
m('LgxDayFracPct', '%.0f' % (100.0 * frac))
m('LgxProjN', '%.0f' % proj)
m('LgxProjPct', '%.0f' % (100.0 * proj / nsys))

# ★ The point of the correction is that the projected figure is materially
# BELOW the bare archived fraction; if it ever were not, the sentence saying
# so would be false and the build should stop.
assert proj < multi_arch, (proj, multi_arch)
assert indep <= multi_searched <= multi_arch <= nsys, \
    (indep, multi_searched, multi_arch, nsys)
# ... and the year-baseline figure really is below a third, which is the
# claim the prose attaches to it.
assert years / float(nsys) < 1 / 3.0, (years, nsys)

with open(OUT, 'w') as fh:
    fh.write('%% GENERATED by ledgers_v404.py -- do not hand-edit.\n')
    for k in sorted(M):
        fh.write('\\newcommand{\\%s}{%s}\n' % (k, M[k]))

print('ledgers_v404: extension %d processed = %d reported + %d withheld + '
      '%d processed after the %s snapshot'
      % (processed, reported, withheld_blocks, later, M['LgxSnapDate']))
print('  uncalibrated: %s over the 177 in scope, %s over the %d unsearched'
      % (_wide, _narrow, 41))
print('  recurrence: %d of %d systems have >1 searched block (%.0f%%), '
      '%d have >1 archived (%.0f%%), %d have searched epochs >1 d apart '
      '(%.0f%%); projected if all archived blocks were searched %.0f (%.0f%%)'
      % (multi_searched, nsys, 100 * multi_searched / nsys, multi_arch,
         100 * multi_arch / nsys, indep, 100 * indep / nsys, proj,
         100 * proj / nsys))
print('  -> %s (%d macros)' % (os.path.basename(OUT), len(M)))
