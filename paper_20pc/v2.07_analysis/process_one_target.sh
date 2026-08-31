#!/bin/bash
# Process ONE target end-to-end: calibrate -> SETI search -> continuum map
# -> cleanup. Every step is governed (disk/load checked, nice/ionice,
# core-capped) since this whole survey is an explicitly secondary/
# background task on shared infrastructure.
#
# Usage: process_one_target.sh <rank> <name> <mous_csv> <ra> <dec> <pmra> <pmdec> <parallax> <parallax_err>
#   mous_csv: one or more MOUS UIDs, comma-separated, best/finest first.
#   Older (pre-~2015) ALMA data is often delivered without the standard
#   pipeline casa_commands.log/calapply.txt this pipeline auto-replays
#   (manual/scriptForPI-era calibration instead) -- rather than give up on
#   a star entirely because its single highest-resolution dataset happens
#   to predate the modern pipeline, we try each candidate MOUS for that
#   star in turn (finest resolution first) until one calibrates cleanly.
set -u
RANK="$1"; NAME="$2"; MOUS_CSV="$3"; RA="$4"; DEC="$5"; PMRA="$6"; PMDEC="$7"; PLX="$8"; PLX_ERR="${9:-0}"

SAFE_NAME=$(echo "$NAME" | tr ' /()' '____' | tr -cd 'A-Za-z0-9_-')
B=/data/SETI/bin
TDIR="/data/SETI/targets/${SAFE_NAME}"
mkdir -p "$TDIR"/{raw,work,products,logs}

source "$B/governor.sh"

LOG="$TDIR/logs/process.log"
STATUS="$TDIR/logs/target_status.json"
exec > >(tee -a "$LOG") 2>&1

echo "############################################################"
echo "### [$RANK] $NAME  (candidates: $MOUS_CSV)  start $(date -u +%FT%TZ)"
echo "############################################################"

if [ -f "$TDIR/logs/DONE" ]; then
  echo "[$NAME] already complete (DONE marker present), skipping"
  exit 0
fi
if [ -f "$TDIR/logs/FAILED" ]; then
  echo "[$NAME] previously failed and marked permanent-skip, skipping"
  exit 0
fi

wait_for_headroom "target:$NAME:calibrate"
log_disk

export CASASITECONFIG=/home/fetch-agi/.casa/config.py

echo "--- calibration (trying candidates in order) ---"
CAL_RC=1
IFS=',' read -ra MOUS_ARR <<< "$MOUS_CSV"
for MOUS in "${MOUS_ARR[@]}"; do
  echo "  trying MOUS $MOUS ..."
  rm -rf "$TDIR/raw" "$TDIR/work"
  mkdir -p "$TDIR/raw" "$TDIR/work"
  run_throttled "$MAX_CORES" python3 "$B/calibrate_generic.py" "$TDIR" "$MOUS" "$MAX_CORES"
  CAL_RC=$?
  if [ $CAL_RC -eq 0 ]; then
    echo "  MOUS $MOUS calibrated successfully"
    break
  fi
  echo "  MOUS $MOUS failed (rc=$CAL_RC), trying next candidate if any"
done
if [ $CAL_RC -ne 0 ]; then
  echo "[$NAME] ALL candidate MOUS failed calibration -- cleaning up and marking permanent-skip"
  rm -rf "$TDIR/raw" "$TDIR/work"
  touch "$TDIR/logs/FAILED"
  log_disk
  exit 1
fi
log_disk

wait_for_headroom "target:$NAME:spw_select"
echo "--- finest-spw selection ---"
run_throttled 2 python3 "$B/select_finest_spw.py" "$TDIR"
if [ ! -f "$TDIR/logs/finest_spw.json" ]; then
  echo "[$NAME] spw selection FAILED -- cleaning up and marking permanent-skip"
  rm -rf "$TDIR/raw" "$TDIR/work"
  touch "$TDIR/logs/FAILED"
  exit 1
fi

# Updated 2026-08-30 per Glenn's instruction: loop over EVERY distinct
# spectral window select_finest_spw.py split out (previously only the
# single finest one was ever searched), each with its own EB/spw-tagged
# output filenames (via SETI_SFX) so results don't clobber one another.
N_SPW=$(python3 -c "import json; print(len(json.load(open('$TDIR/logs/spw_list.json'))['spw_list']))")
N_SPW_CONFIGURED=$(python3 -c "import json; print(json.load(open('$TDIR/logs/spw_list.json'))['n_spw_configured'])")
echo "--- SETI narrowband search: $N_SPW of $N_SPW_CONFIGURED distinct spws to search ---"
export SETI_TARGET_DIR="$TDIR"
export SETI_STAR_NAME="$NAME" SETI_STAR_RA="$RA" SETI_STAR_DEC="$DEC"
export SETI_STAR_PMRA="$PMRA" SETI_STAR_PMDEC="$PMDEC"
export SETI_STAR_PARALLAX="$PLX" SETI_STAR_PARALLAX_ERR="$PLX_ERR"

N_SPW_OK=0
for ((SPW_IDX=0; SPW_IDX<N_SPW; SPW_IDX++)); do
  read -r SPW_EB SPW_MS SPW_ID <<< "$(python3 -c "
import json
e = json.load(open('$TDIR/logs/spw_list.json'))['spw_list'][$SPW_IDX]
print(e['eb'], e['ms'], e['spw'])
")"
  echo "  spw $((SPW_IDX+1))/$N_SPW: EB=$SPW_EB spw=$SPW_ID"
  wait_for_headroom "target:$NAME:seti_search:spw$SPW_ID"
  export SETI_MS="$SPW_MS" SETI_SFX="_spw${SPW_ID}"
  run_throttled "$MAX_CORES" python3 "$B/seti_extract_generic.py" "$SPW_EB" "$MAX_CORES"
  EXTRACT_RC=$?
  SEARCH_RC=1
  if [ $EXTRACT_RC -eq 0 ]; then
    run_throttled "$MAX_CORES" python3 "$B/seti_drift_search_generic.py" "$SPW_EB" "$MAX_CORES"
    SEARCH_RC=$?
  fi
  if [ $EXTRACT_RC -eq 0 ] && [ $SEARCH_RC -eq 0 ]; then
    N_SPW_OK=$((N_SPW_OK+1))
  else
    echo "  spw $SPW_ID FAILED (extract_rc=$EXTRACT_RC search_rc=$SEARCH_RC)"
  fi
done
unset SETI_MS SETI_SFX

# Found 2026-08-26 (LP 876-10): a target can have a fully successful
# calibration + continuum map while its technosignature search silently
# failed (e.g. a genuine multi-field/mosaic MS the single-position search
# isn't designed for) -- previously nothing tracked this, so the target
# still ended up marked DONE/rc=0 with NO drift-search result at all,
# indistinguishable in the driver's bookkeeping from a real completed
# search. Flag it explicitly, same pattern as CONTINUUM_MAP_FAILED.
# Now (multi-spw): only flag as a full failure if EVERY spw failed; a
# partial success (some spws searched, others not) is noted but not
# treated as gating, since real, usable results still exist.
if [ "$N_SPW_OK" -eq 0 ]; then
  echo "[$NAME] WARNING: technosignature search FAILED for ALL $N_SPW attempted spws --" \
       "continuum map may still succeed below, but there is NO drift-search" \
       "result for this target. Flagging for follow-up (logs/SETI_SEARCH_FAILED)," \
       "NOT marking permanent-skip."
  touch "$TDIR/logs/SETI_SEARCH_FAILED"
elif [ "$N_SPW_OK" -lt "$N_SPW" ]; then
  echo "[$NAME] technosignature search: $N_SPW_OK/$N_SPW attempted spws succeeded" \
       "(partial) -- keeping the successful ones, not flagging as a full failure"
  rm -f "$TDIR/logs/SETI_SEARCH_FAILED"
else
  echo "[$NAME] technosignature search: $N_SPW_OK/$N_SPW attempted spws succeeded"
  rm -f "$TDIR/logs/SETI_SEARCH_FAILED"
fi

wait_for_headroom "target:$NAME:continuum_map"
echo "--- continuum map (line-excluded) ---"
run_throttled "$MAX_CORES" python3 "$B/continuum_map_generic.py" "$TDIR" "$NAME" "$RA" "$DEC" "$PMRA" "$PMDEC" "$PLX" "$MAX_CORES"
CMAP_RC=$?
if [ $CMAP_RC -ne 0 ]; then
  echo "[$NAME] WARNING: continuum map step FAILED (rc=$CMAP_RC) -- technosignature" \
       "search product is still valid, but the requested PNG map is MISSING for" \
       "this target. Flagging for follow-up (logs/CONTINUUM_MAP_FAILED), NOT" \
       "marking permanent-skip so it can be retried later."
  touch "$TDIR/logs/CONTINUUM_MAP_FAILED"
else
  rm -f "$TDIR/logs/CONTINUUM_MAP_FAILED"
fi

echo "--- cleanup (reclaim all transient disk) ---"
rm -rf "$TDIR/raw" "$TDIR/work"
rm -rf "$TDIR/products/"*.ms
# belt-and-suspenders: seti_drift_search_generic.py already deletes the
# (large, GB-scale) raw waterfall right after consuming it, but catch any
# leftovers here too (e.g. a step that errored before reaching that point)
rm -f "$TDIR/products/"*_waterfall.npz
du -sh "$TDIR" 2>/dev/null

# Fixed 2026-08-31 after finding this live (19 targets: BD+05 3409, EGGR 453,
# HD 45088, etc. -- all correctly aborted by the crossmatch/pointing sanity
# check in BOTH the narrowband search AND the continuum map, producing
# ZERO science products, yet were still unconditionally marked DONE below.
# This silently inflated completion counts and, worse, permanently
# prevented these targets from ever being retried (DONE is the very first
# check at the top of this script), even though a corrected MOUS
# assignment might one day let them succeed. DONE should mean "we have a
# result", not merely "we stopped trying" -- if BOTH steps produced
# nothing at all, leave this target WITHOUT a DONE marker so it remains
# eligible for a future retry (e.g. once the crossmatch is manually
# corrected), rather than silently and permanently disappearing from the
# survey's todo list. A quick, harmless repeat of the same fast crossmatch
# abort is a trivial cost if the underlying MOUS assignment truly never
# changes; the alternative (silently losing the star from the survey
# forever) is not.
if [ -f "$TDIR/logs/SETI_SEARCH_FAILED" ] && [ -f "$TDIR/logs/CONTINUUM_MAP_FAILED" ]; then
  echo "[$NAME] NOT marking DONE: both the narrowband search and the" \
       "continuum map failed for every attempt, so this target has zero" \
       "science products -- leaving it eligible for a future retry" \
       "instead of silently marking it complete."
else
  touch "$TDIR/logs/DONE"
  echo "[$NAME] DONE $(date -u +%FT%TZ)"
fi
log_disk
