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
            + ['per_target_results_v3.99.csv',
               'tab_dispo_v405.tex', 'tab_maskladder_v405.tex',
               'appm_v405.json', 'freqocc_v405.json']
            # v4.06: the census file the exoplanet-host join reads, which
            # build_ranked_master40pc.py now writes with an explicit
            # is_exo_host for every entry it creates, plus its audit sidecar.
            # It is an INPUT to this version (the builder is not run by
            # make_all.sh), so it is listed for the record, not deleted --
            # see FROZEN below.
            + ['ranked_master40pc.csv', 'p90_r7_macros_v406.json']
            + sorted(glob.glob('figures/*.pdf')))
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

rc = subprocess.run(['bash', 'make_all.sh'],
                    stdout=subprocess.DEVNULL, stderr=subprocess.STDOUT).returncode
if rc != 0:
    raise SystemExit('make_all.sh failed (rc=%d) -- the regeneration is not '
                     'clean and the comparison below would be meaningless' % rc)

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
