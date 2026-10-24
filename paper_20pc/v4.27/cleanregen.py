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

# ►►►► `--verdict` READS AN EXISTING LOG AND SAYS WHETHER THE LAST CLEAN
# REGENERATION COMPLETED.  It is the first thing in this file because the rest
# of it DELETES THE PRODUCT SET, and an agent resuming after a container stop
# needs this answer precisely when it must not run the destructive path.
# ★ That question has been answered wrong twice in round 25 alone, both times
# by reading a timestamp and a trailing header (see the note at `_PASSES`), and
# both times it cost a full chain re-run.  It is a string comparison, not an
# inference, so it is now available as one.
if '--verdict' in sys.argv:
    _vp = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                       'cleanregen_make.log')
    if not os.path.exists(_vp):
        print('cleanregen --verdict: no cleanregen_make.log -- no clean '
              'regeneration has been run in this tree')
        raise SystemExit(2)
    _vt = open(_vp, errors='ignore').read()
    _beg = re.findall(r'===== cleanregen pass (\d) of (\d) BEGIN =====', _vt)
    _end = re.findall(r'===== cleanregen pass (\d) of (\d) END rc=(-?\d+) =====',
                      _vt)
    #: a log written before the marker fix carries bare headers and cannot be
    #: adjudicated at all -- say so rather than guess, which is the whole point
    _old = re.findall(r'===== cleanregen pass (\d) of (\d) =====[ \t]*$',
                      _vt, re.M)
    if not _beg and _old:
        print('cleanregen --verdict: UNDETERMINABLE -- this log predates the '
              'BEGIN/END markers (%d bare header(s)).  Its trailing header is '
              'NOT evidence of a cut: before the fix the headers were flushed '
              'after their own pass, so a COMPLETE run also ended on one. '
              'Re-run `python3 cleanregen.py` to get an adjudicable log.'
              % len(_old))
        raise SystemExit(3)
    _npass = int(_beg[0][1]) if _beg else 0
    _ok = (len(_beg) == _npass and len(_end) == _npass
           and all(e[2] == '0' for e in _end))
    print('cleanregen --verdict: %d BEGIN, %d END of %d pass(es), rc %s -> %s'
          % (len(_beg), len(_end), _npass,
             ','.join(e[2] for e in _end) or '-',
             'COMPLETE' if _ok
             else 'INCOMPLETE -- still running, cut, or failed.  These three '
                  'are not distinguishable from a log and this tool will not '
                  'guess between them; what is certain is that the product set '
                  'is NOT a verified fixed point, so do not resume inside it'))
    raise SystemExit(0 if _ok else 1)

os.chdir(os.path.dirname(os.path.abspath(__file__)))

PRODUCTS = (sorted([_mgp for _mgp in glob.glob('survey_numbers*.tex') if '_drive' not in _mgp])
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
            # ★★★★ v4.21, r20-final: THE ANCILLARY FILES WERE OUTSIDE THIS
            # TEST ALTOGETHER, and they are the files that ship beside the
            # PDF.  `si_catalogue.txt` and `si_ledger.txt` have been promised
            # in the data availability statement since r18 and nothing proved
            # either could be rebuilt from the frozen inputs; a stale
            # ancillary file is exactly the defect this gate exists for,
            # because `arxivset.sh` ships whatever is on disk and A13 only
            # asks that the file be non-empty.  `si_counts.txt` -- the
            # itemisation of the master count table, which the article now
            # prints only the accounting rows of -- is this pass's own and
            # joins them.
            # ★ v4.22: `si_recur.txt` and `si_recovery.txt` join them -- the
            # per-crossing exclusion depths and the per-crossing recovery
            # probabilities, both ancillary files that ship beside the PDF.
            + ['si_catalogue.txt', 'si_counts.txt', 'si_ledger.txt',
               'si_recur.txt', 'si_recovery.txt']
            # ★ v4.21: this round's three new json products.
            # `linerecur_r20.json` is the one that matters: `confirm_r19.py`
            # READS it for Table D2's two new columns, so it is precisely the
            # "product another generator consumes" case this list exists for
            # -- left out, a stale copy would survive a rebuild and the table
            # would carry the previous run's readings.  The other two are
            # read by nobody and are here because a product that nothing
            # consumes today is consumed tomorrow.
            + ['linerecur_r20.json', 'confirm_r20.json',
               'vsyssweep_r20.json']
            # ★ v4.22: this round's products.  `r21inputs/tolsep_r21.json` is
            # the one that matters -- `recur_v411.py` reads it for Table 6's
            # two new rows, so it is the "product another generator consumes"
            # case again, and it lives under `r21inputs/` only because that is
            # where the generator that writes it puts its records.  The four
            # tsv/tex/json products beside it are read by nobody today.
            + ['tolrecur_r21.json', 'r21inputs/tolsep_r21.json',
               'vuln_r21.json', 'transfer_r21.json', 'sensnull_r21.json',
               'r21_scope.json', 'r21_lines.json', 'r21_image.json',
               'si_nearest_r21.tsv', 'tab_nearest_r21.tex']
            # ★★★ v4.23: round 22's products.  `edge_flags_v423.json` is the
            # one that matters -- `pairs_v415.py` READS it for the edge
            # column of Table 5, and it is written by an earlier pass of the
            # same generator, so a stale copy is exactly the hazard this
            # list exists for (edge_v423.py's E11 would catch it, but only
            # if the file is deleted and rebuilt here).  `edge_v423.json` is
            # read by nobody today.  ★ `epsx_v423.json` and its csv are the
            # eps Eri per-window record; `num_r22.json` and `r1_r22.json`
            # are read by nobody and are here because a product nothing
            # consumes today is consumed tomorrow.
            + ['edge_flags_v423.json', 'edge_v423.json', 'proxb_v423.json',
               'epsx_v423.json', 'epsx_v423.csv', 'num_r22.json',
               'r1_r22.json']
            # ★★★ v4.24: round 23's products.  `chance_v414.json` is the one
            # that matters -- `screen_r23.py` READS it back for the count
            # before and after the atmospheric screen, so a stale copy would
            # let the independent reconstruction agree with the previous
            # run's answer.  `fieldread_r23.json` and `screen_r23.json` are
            # read by nobody today and are here for the same reason the rows
            # above are.
            + ['chance_v414.json', 'fieldread_r23.json', 'screen_r23.json',
               'pairacct_r23.json']
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
# ★★★★ v4.18: TWO PASSES ON THE DELETED TREE, AND THAT IS A STRONGER TEST.
# This chain has a genuine BOOTSTRAP CYCLE that only a from-nothing tree can
# expose, and round 17 walked straight into it:
#   `sens_r11.py --prepass` writes `pb_atten_fwhm_r11.csv`
#     -> `beam_r17.py` reads it and solves the retention level \BmFloorResp
#        and needs \EirpNinetyMultB from round 103
#          -> `numbers_v410.py` writes round 103 and reads `smin_ratio` out of
#             `pb_atten_fwhm_r11.csv`
#   while `v363_calc.py` (step 73) and `sens_r11.py` itself want
#   \BmFloorResp, which is solved at step 272.
# No ordering of one pass satisfies all of that, because the cycle is real:
# the beam level is measured from the sensitivity chain and the sensitivity
# chain is corrected by the beam level.  The generators that sit inside the
# cycle now DEFER their comparison with a printed note when the macro they
# want is not there yet, and a later generator owns each one -- the pattern
# `smear_r15.py` has used since v4.16.
# ★ So the clean-room test runs `make_all.sh` TWICE on the deleted tree.  The
# first pass bootstraps the layer, the second is the one whose output is
# compared, and the claim being tested is stronger than before: not merely
# "a rebuild reproduces the products" but "the whole product set is
# reachable from no products at all, and is a FIXED POINT once reached."
# ★★ A generator that depends on the state left by a previous run -- the
# failure this test exists to catch -- is still caught, and more sharply:
# such a generator would make pass 2 differ from the recorded digests.
# ►►►► ★★★★ THE PASS HEADERS IN THIS LOG USED TO LAND AFTER THE OUTPUT THEY
# LABEL, AND IT COST THIS ROUND TWO FULL CHAIN RE-RUNS.
# `_fh.write(...)` goes into Python's userspace buffer; `subprocess.run` writes
# to the raw file DESCRIPTOR.  The subprocess therefore reached the file first
# and Python flushed the header behind it, so every header sat AFTER its own
# pass and the file ALWAYS ended on "===== cleanregen pass 2 of 2 =====" --
# on a completely successful run.  Demonstrated in three lines:
#     with open(p,'w') as fh:
#         fh.write('HEADER\n'); subprocess.run(['bash','-c','echo X'], stdout=fh)
#     -> "X" then "HEADER"
# ★★★★ So the one diagnostic everybody reads this file for was INVERTED: a
# trailing pass-2 header is proof the regeneration COMPLETED, and a cut pass 2
# would end mid-output with no header at all.  Ruling 20 read a cut from it and
# restarted the chain; the round-25 close brief read a cut from the 10-20 20:49
# log and ordered the chain restarted again.  Neither tree had been cut.
# ★ Fixed at the mechanism (flush before handing the fd over), and then made
# UNAMBIGUOUS rather than merely correct: each pass now writes a BEGIN marker
# before its output and an END marker with the return code after it, so
# "complete" and "cut" are different strings in the file instead of the same
# one read two ways.  A reader never has to infer liveness from a timestamp.
_PASSES = 2
rc = 0
for _pass in range(1, _PASSES + 1):
    with open(_log, 'w' if _pass == 1 else 'a') as _fh:
        _fh.write('\n===== cleanregen pass %d of %d BEGIN =====\n'
                  % (_pass, _PASSES))
        _fh.flush()          # ★ the header must reach the fd before the child
        rc = subprocess.run(['bash', 'make_all.sh'],
                            stdout=_fh, stderr=subprocess.STDOUT).returncode
        _fh.write('\n===== cleanregen pass %d of %d END rc=%d =====\n'
                  % (_pass, _PASSES, rc))
        _fh.flush()
    print('cleanregen: make_all.sh pass %d of %d -> rc=%d'
          % (_pass, _PASSES, rc))
    if rc != 0:
        break
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
