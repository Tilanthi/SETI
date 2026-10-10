#!/usr/bin/env python3
"""Clean-regeneration test that needs no second copy of the paper directory.

The test this replaces copied the whole version folder elsewhere, re-ran
make_all.sh there and diffed. That costs ~150 MB per run, and on a volume
shared with other agents it failed part-way and produced a FALSE result:
`cp` ran out of space, several products were never written, and the
comparison duly reported six spurious differences.

Hashing is cheaper and cannot fail that way. Record a digest of every
generated product, re-run the generators IN PLACE, and compare digests. A
generator that depends on the state left by a previous run -- which is the
failure this test exists to catch -- still shows up, because the second run
starts from the first run's output exactly as a fresh checkout would not.

To be a true clean-room test the products are DELETED before the rebuild,
so nothing can survive by not being rewritten; the frozen macro files that
`make_all.sh` restores from `frozen_macros/` are exempt, since they are
inputs rather than products.

Usage:  cleanregen.py          -- record, delete, rebuild, compare
        cleanregen.py --keep   -- rebuild without deleting first
"""
import glob
import hashlib
import re
import os
import subprocess
import sys

os.chdir(os.path.dirname(os.path.abspath(__file__)))

PRODUCTS = (sorted(glob.glob('survey_numbers*.tex'))
            + ['tab_selection.tex', 'tab_perband.tex', 'peff_range_v372.tex']
            # v4.03: the ledger's machine-readable outputs are products too,
            # and two generators now READ them.  Leaving them out let
            # vispower_v400.py run before ledger_v403.py for a whole build
            # while reading the PREVIOUS run's ledger -- invisible to a test
            # that never deletes the file.  A product another generator
            # consumes is exactly the one this test must delete.
            + ['ledger_v403.json', 'ledger_v403.csv',
               'tab_ledger_v403.tex', 'tab_ledgersum_v403.tex',
               'ledger_legend_v403.tex']
            # v4.05: the released catalogue is itself a product, and it is the
            # one the largest number of other generators read -- five of this
            # cycle's six do.  It now carries the computed disposition columns,
            # so a generator that silently read a previous run's copy would
            # report the previous build's attributions.  Same reasoning as the
            # ledger above, one level further up the dependency chain.
            # ★ v4.11: `tab_maskladder_v405.tex` is GONE with its generator.
            # ladder_v405.py emitted a two-frame mask ladder nothing inputs
            # and is retired to `retired_generators/`; the single-frame
            # ladder and the robustness table are maskframe_v411.py's
            # (`tab_maskrobust_v411.tex`), which is listed below.
            + ['per_target_results_v3.99.csv',
               'tab_dispo_v405.tex',
               'appm_v405.json', 'freqocc_v405.json']
            # ★ v4.11: the round-10 products, including the two that other
            # generators READ -- `recurcols_v411.json` (the crossing ledger
            # reads it for Table 6's recurrence columns) and
            # `repaired_v409.csv` (the ledger reads it for the ADOPTED
            # statistic).  A product another generator consumes is exactly
            # the one this test must delete: leaving `repaired_v409.csv` out
            # would let the ledger read a previous run's copy, which is the
            # failure mode this file was written for.
            + ['recurcols_v411.json',
               'maskframe_v411.json', 'strata_v411.json',
               'pxapply_v411.json', 'ledger.json',
               'tab_ledger.tex', 'tab_ledgersum.tex', 'tab_blockledger.tex',
               'tab_maskrobust_v411.tex', 'tab_maskband_v411.tex',
               # ★ v4.12: 'tab_recurcols_v411.tex' REMOVED from this list.
               # `recur_v411.py` stopped writing it -- it was a second copy of
               # the ledger's own recurrence columns and was never \input --
               # so a clean regeneration deleted a file nothing rebuilds and
               # stopped before it began, reporting the product missing rather
               # than a product differing.  The name and the emission had to go
               # together, and only one half had.
               'tab_recurcand_v411.tex',
               'tab_visfit_v411.tex']
            # v4.06: the census file the exoplanet-host join reads, which
            # build_ranked_master40pc.py now writes with an explicit
            # is_exo_host for every entry it creates, plus its audit sidecar.
            # It is an INPUT to this version (the builder is not run by
            # make_all.sh), so it is listed for the record, not deleted --
            # see FROZEN below.
            + ['ranked_master40pc.csv', 'p90_r7_macros_v406.json']
            # v4.07: the census-repair audit sidecar, which selftest_census_v407
            # READS to reconstruct the pre-repair row set.  Same rule as the
            # ledger and the catalogue above: a product another generator
            # consumes is exactly the one this test must delete.
            + ['censusfix_v407_audit.json']
            # v4.09: the crossing-delta, clustering and tail tables, the
            # regenerated P90 budget table, and the machine-readable record
            # of the adopted repaired statistic.  The last one is a DEPOSITED
            # product another reader joins against the catalogue, so it is
            # exactly the kind of file this test must delete and rebuild.
            + ['tab_crossdelta_v409.tex', 'tab_clust_v409.tex',
               'tab_tail_v409.tex', 'tab_p90budget_v409.tex',
               'repaired_v409.csv', 'p90budget_v409.json']
            + sorted(glob.glob('figures/*.pdf')))


# ★★★★ r16-referee: THE HOLE THAT MADE THIS GATE VACUOUS FOR TEN TYPESET
# TABLES.  PRODUCTS above is a glob over `survey_numbers*.tex`, a glob over
# `figures/*.pdf` and a HAND-KEPT list of everything else.  The four round-16
# generators that were in no build script were caught here only because they
# happen to write `survey_numbers_round*.tex` and so fell inside the glob.  A
# generator whose only typeset output is a `tab_*.tex` fragment -- and five of
# the paper's numbered tables are exactly that -- was invisible: the file is
# never deleted, the stale copy survives the rebuild, and this test reports
# everything byte-identical.  `tab_counts.tex` (Table A2), `tab_pairs_v415.tex`
# (Table 5), `tab_budget_r11.tex` (Table 4), `tab_holdout_v412.tex` (Table 7),
# `tab_ledger_cont.tex` (Table D2), `tab_litthresh_r15.tex` (Table 1),
# `tab_maskspecies_v414.tex` (Table C1), `tab_projcodes_v400.tex` (Table A3),
# `tab_recurcand_v411.tex` and `regen_count.tex` were all outside it.
#
# So the list is no longer hand-kept for typeset fragments: ANY file the
# manuscript \input{}s that is not a section file is a product of this build
# and must be deleted and rebuilt.  That rule maintains itself -- a new
# fragment joins the test the moment the manuscript cites it -- which is the
# only kind of coverage that survives six agents editing at once.
def _typeset_inputs():
    seen, found = set(), set()

    def walk(rel):
        if rel in seen or not os.path.exists(rel):
            return
        seen.add(rel)
        txt = open(rel, errors='ignore').read()
        txt = re.sub(r'(?m)(?<!\\)%.*$', '', txt)
        for mm in re.finditer(r'\\input\{([^}]+)\}', txt):
            f = mm.group(1)
            f = f if f.endswith('.tex') else f + '.tex'
            if not f.startswith('sections/'):
                found.add(f)
            walk(f)

    cand = sorted(f for f in os.listdir('.')
                  if f.startswith('technosignatures_') and f.endswith('.tex'))
    assert len(cand) == 1, 'expected one manuscript .tex, found %r' % (cand,)
    walk(cand[0])
    # A gate that cannot fail is worse than no gate: if the expansion ever
    # comes back empty or implausibly small, that is a defect in the walker
    # and not a paper with no generated tables.
    assert len(found) > 100, 'the manuscript expansion found only %d generated \
inputs; the walker is broken' % len(found)
    return sorted(found)


_TYPESET = _typeset_inputs()
PRODUCTS = PRODUCTS + [f for f in _TYPESET if os.path.exists(f)]
_UNBUILT = [f for f in _TYPESET if not os.path.exists(f)]
if _UNBUILT:
    raise SystemExit('cleanregen: the manuscript \\input{}s %d file(s) that do '
                     'not exist: %s' % (len(_UNBUILT), _UNBUILT[:5]))
# restored by make_all.sh from frozen_macros/, so they are inputs
FROZEN = {'survey_numbers_round5.tex', 'survey_numbers_round6.tex',
          'survey_numbers_round7.tex',
          # v4.06: the census is built OUTSIDE this directory, by
          # /workspace/SETI/build_ranked_master40pc.py, so make_all.sh cannot
          # regenerate it.  Hashing it still catches a generator that writes
          # to it by accident, which is why it is in PRODUCTS at all.
          'ranked_master40pc.csv'}


def digest(path):
    h = hashlib.sha256()
    with open(path, 'rb') as fh:
        for blk in iter(lambda: fh.read(1 << 20), b''):
            h.update(blk)
    return h.hexdigest()


before = {}
# ★ v4.11: DEDUPE.  The list is assembled from eight separate blocks and
# `repaired_v409.csv` was added to two of them, so the delete loop removed
# it once and then raised FileNotFoundError on the second pass -- after it
# had already deleted part of the tree, which leaves the directory in a
# state where this test cannot even start.  A list built by concatenation
# must be made a set before it is used to delete anything.
_seen, _uniq = set(), []
for _p in PRODUCTS:
    if _p not in _seen:
        _seen.add(_p)
        _uniq.append(_p)
if len(_uniq) != len(PRODUCTS):
    print('cleanregen: %d duplicate product name(s) in the list, deduped'
          % (len(PRODUCTS) - len(_uniq)))
PRODUCTS = _uniq

missing = [p for p in PRODUCTS if not os.path.exists(p)]
if missing:
    raise SystemExit('not built yet, %d products missing: %s'
                     % (len(missing), missing[:4]))
for p in PRODUCTS:
    before[p] = digest(p)

if '--keep' not in sys.argv:
    for p in PRODUCTS:
        if os.path.basename(p) not in FROZEN:
            os.remove(p)

# ★ v4.12: keep the log.  When the clean rebuild fails it fails EARLY, on a
#   forward dependency that only this test can see, and discarding the output
#   left the operator with "rc=1" and nothing to act on.
_log = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                    'cleanregen_make.log')
with open(_log, 'w') as _fh:
    rc = subprocess.run(['bash', 'make_all.sh'],
                        stdout=_fh, stderr=subprocess.STDOUT).returncode
if rc != 0:
    print(open(_log, errors='ignore').read()[-3000:])
    raise SystemExit('make_all.sh failed (rc=%d) -- the regeneration is not '
                     'clean and the comparison below would be meaningless; '
                     'the log is cleanregen_make.log' % rc)

same, diff, gone = 0, [], []
for p in PRODUCTS:
    if not os.path.exists(p):
        gone.append(p)
    elif digest(p) == before[p]:
        same += 1
    else:
        diff.append(p)

print('CLEAN REGENERATION: %d/%d byte-identical' % (same, len(PRODUCTS)))
for p in diff:
    print('  DIFFERS     %s' % p)
for p in gone:
    print('  NOT REBUILT %s' % p)
if diff or gone:
    raise SystemExit(1)
