#!/bin/bash
# mirror_pool_dl.sh -- weighted multi-mirror parallel downloader for the
# ALMA Science Archive, tuned empirically from a network location in
# Singapore (GCP asia-southeast1).  See /workspace/SETI/STATUS.md and
# /shared/kb/skills/alma-archive-download.md for the full writeup of how
# these numbers were measured and why.
#
# KEY FINDINGS THIS SCRIPT ENCODES:
#   1. A naive single curl stream gets ~0.7 MB/s from the ALMA archive
#      regardless of mirror -- always use a segmented downloader (aria2c).
#   2. Per FILE, per MIRROR, aria2c saturates around -x8 -s8 (8 connections);
#      -x16/-x32 buys effectively nothing more for one file.
#   3. Which mirror is "fastest" is about NETWORK GEOGRAPHY, not server
#      quality: from Singapore, NAOJ (Tokyo) beats ESO (Chile/Garching)
#      beats NRAO (Virginia) by a wide and repeatable margin (measured
#      37-58 MB/s NAOJ vs 26-31 MB/s ESO vs 20-21 MB/s NRAO, order-controlled,
#      x2 repeats). Re-benchmark before assuming this if running from a
#      different region.
#   4. Running many FILES concurrently through the SAME (fastest) mirror
#      scales almost linearly at first (56/119/213/371 MB/s at 1/2/4/6
#      concurrent files) then flattens (437 MB/s at 12x) -- this is
#      per-client server-side throttling on that one mirror, not our own
#      network ceiling.
#   5. Once the fastest mirror is saturated, ADDING the slower mirrors
#      *on top* (not instead) recovers real extra throughput, because each
#      mirror's throttle is independent: 6xNAOJ+3xESO+3xNRAO simultaneously
#      measured 507 MB/s vs 437 MB/s for 12xNAOJ alone (+16%) and vs 371 MB/s
#      for 6xNAOJ alone (+37%).
#   6. Therefore the right POOL policy is weighted round-robin: send the
#      first ~60% of concurrent jobs to the fastest mirror, then spill the
#      rest across the remaining mirrors in proportion to their measured
#      solo speed, rather than splitting every single file evenly across
#      all mirrors (that actively HURTS -- a single file split naively
#      across 3 mirrors of very different speed measured only 25-31 MB/s,
#      *worse* than the fast mirror alone, because the slow mirrors' low
#      per-connection cap drags the average down).
#   7. IMPORTANT CAVEAT discovered on a REAL full-length download (the short
#      25-30s benchmarks above are optimistic): under SUSTAINED multi-minute
#      load, a mirror can silently collapse an 8-connection download down to
#      1 connection (observed on ESO: "CN:8" -> "CN:1", throughput falling
#      from ~30 MB/s to ~15 MB/s) and NOT recover on its own, even though
#      aria2c is still nominally "working". Short bursts do not reveal this.
#      Fix: an external watchdog (below) monitors real on-disk growth rate
#      every WATCHDOG_INTERVAL seconds and force-restarts (kill + relaunch
#      with -c/continue, which resumes from the existing partial file and
#      re-opens a fresh full set of connections) any download whose rate
#      falls below WATCHDOG_MIN_MBPS. Always assume you need this for any
#      download expected to run longer than a minute or two.
#
# Usage:
#   mirror_pool_dl.sh <dest_dir> <remote_filename1> [remote_filename2] ...
#
# Each remote_filename is the bare ALMA archive filename (as returned by
# Alma.get_data_info), e.g.
#   2017.1.00215.S_uid___A002_Xd0e450_X1e19.asdm.sdm.tar
# Writes <dest_dir>/<remote_filename> and <dest_dir>/../logs/dl_<EBID>.done
# marker files (EBID = the uid___..._X....asdm token), compatible with
# pipeline_all.sh's existing wait-for-download logic.

set -u
DEST="$1"; shift
FILES=("$@")

NAOJ=https://almascience.nao.ac.jp/dataPortal
ESO=https://almascience.eso.org/dataPortal
NRAO=https://almascience.nrao.edu/dataPortal
# Weighted mirror order: repeat the fastest mirror more times in this list;
# files are assigned round-robin down the list. Ratio ~6:3:3 matches the
# empirically saturating combination (measured 507 MB/s).
MIRROR_CYCLE=("$NAOJ" "$NAOJ" "$ESO" "$NAOJ" "$NRAO" "$NAOJ" "$ESO" "$NAOJ" "$NRAO" "$NAOJ" "$ESO" "$NRAO")
LOGDIR="$(dirname "$DEST")/logs"
mkdir -p "$DEST" "$LOGDIR"

MAXPAR=${MIRROR_POOL_MAXPAR:-12}       # cap on simultaneous aria2c processes
WATCHDOG_INTERVAL=${MIRROR_POOL_WD_INTERVAL:-45}   # seconds between health checks
WATCHDOG_MIN_MBPS=${MIRROR_POOL_WD_MINRATE:-8}     # restart if slower than this

n=${#FILES[@]}
echo "[mirror_pool_dl] $n file(s) -> $DEST, weighted across $(printf '%s\n' "${MIRROR_CYCLE[@]}" | sort -u | wc -l) mirrors, maxpar=$MAXPAR, watchdog=${WATCHDOG_MIN_MBPS}MB/s per ${WATCHDOG_INTERVAL}s"

# One managed downloader per file: launches aria2c, then watches its own
# on-disk growth rate and self-restarts (via -c/continue) if it stalls.
# This is the fix for finding #7 above (mirrors silently collapsing to a
# single connection under sustained load and never recovering on their own).
download_one(){
  local f="$1" mirror="$2"
  local ebid out logf donef prevsz cursz rate attempt
  ebid=$(echo "$f" | sed -E 's/^.*_uid___//; s/\.asdm\.sdm\.tar$//')
  out="$DEST/$f"
  logf="$LOGDIR/dl_pool_${ebid}.log"
  donef="$LOGDIR/dl_${ebid}.done"
  : > "$logf"
  attempt=0
  while true; do
    attempt=$((attempt+1))
    aria2c -x8 -s8 -k40M --file-allocation=none --console-log-level=warn \
      --max-tries=8 --retry-wait=15 --lowest-speed-limit=1M \
      --connect-timeout=15 --timeout=30 \
      -c -d "$DEST" -o "$f" "${mirror}/${f}" >> "$logf" 2>&1 &
    local apid=$!
    prevsz=$(du -B1 "$out" 2>/dev/null | awk '{print $1}'); prevsz=${prevsz:-0}
    while kill -0 "$apid" 2>/dev/null; do
      sleep "$WATCHDOG_INTERVAL"
      kill -0 "$apid" 2>/dev/null || break
      cursz=$(du -B1 "$out" 2>/dev/null | awk '{print $1}'); cursz=${cursz:-0}
      rate=$(( (cursz - prevsz) / WATCHDOG_INTERVAL / 1000000 ))
      if [ "$rate" -lt "$WATCHDOG_MIN_MBPS" ]; then
        echo "[watchdog] $ebid stalled at ${rate} MB/s (attempt $attempt) -- restarting" >> "$logf"
        # IMPORTANT: SIGTERM, not SIGKILL. aria2c catches SIGTERM and
        # flushes/checkpoints its .aria2 resume-control-file safely before
        # exiting; SIGKILL does not, and testing showed this can corrupt
        # the resume state (a subsequent -c/continue relaunch then produces
        # a tar of the *correct final size* -- because aria2c pre-allocates
        # -- but with garbage/missing bytes in whichever byte range was
        # in flight at the moment of the kill, e.g. a missing ExecBlock.xml
        # despite the file "completing" without any reported error).
        kill -TERM "$apid" 2>/dev/null
        for _w in 1 2 3 4 5; do kill -0 "$apid" 2>/dev/null || break; sleep 1; done
        kill -9 "$apid" 2>/dev/null   # last-resort fallback only
        sleep 2
        break
      fi
      prevsz=$cursz
    done
    wait "$apid" 2>/dev/null
    # CRITICAL: only ever write the .done marker once the .aria2 resume
    # control file is gone -- that is aria2c's own definitive signal that
    # the file is complete. Writing .done for a partial file would let
    # pipeline_all.sh proceed to calibrate a truncated dataset. (This bug
    # was caught by testing: a watchdog-restarted download wrote a
    # premature .done at 40/52 GB before this fix.)
    if [ -f "$out" ] && [ ! -f "${out}.aria2" ]; then
      # Belt-and-braces integrity check: aria2c's own "no .aria2 file left"
      # signal is not 100% sufficient after a SIGKILL-based restart history
      # (see the SIGTERM note above) -- verify the tar itself is readable
      # end-to-end before trusting it. Cheap relative to the multi-GB
      # transfer, and catches silent corruption before it wastes an hour of
      # downstream CASA calibration on a truncated dataset.
      # NB: `tar tf` succeeding is NOT sufficient -- a watchdog-restart
      # history can leave a tar that is structurally well-formed (headers
      # parse fine sequentially) yet silently MISSING entries partway
      # through (observed: ExecBlock.xml absent despite `tar tf` exit 0
      # and no read error). Require both mandatory ASDM top-level files to
      # actually be present, not just a clean listing.
      _listing=$(tar tf "$out" 2>"${logf}.tarcheck")
      if [ $? -eq 0 ] \
         && echo "$_listing" | grep -q '/ASDM\.xml$' \
         && echo "$_listing" | grep -q '/ExecBlock\.xml$'; then
        rm -f "${logf}.tarcheck"
        echo "DONE $(date -u +%FT%TZ) $(du -B1 "$out" | awk '{print $1}')" > "$donef"
        break
      else
        echo "[integrity] $ebid failed verification -- missing ASDM.xml/ExecBlock.xml (attempt $attempt) -- redownloading" >> "$logf"
        rm -f "$out"
      fi
    fi
    if [ "$attempt" -ge 20 ]; then
      echo "GAVE UP after $attempt attempts $(date -u +%FT%TZ)" >> "$logf"
      break
    fi
  done
}

pids=()
running=0
i=0
for f in "${FILES[@]}"; do
  mirror="${MIRROR_CYCLE[$(( i % ${#MIRROR_CYCLE[@]} ))]}"
  echo "  [$i] $f  <-  $mirror"
  download_one "$f" "$mirror" &
  pids+=("$!")
  running=$((running+1)); i=$((i+1))
  if [ "$running" -ge "$MAXPAR" ]; then
    wait -n; running=$((running-1))
  fi
done
wait
echo "[mirror_pool_dl] all $n download(s) finished $(date -u +%T)"
for f in "${FILES[@]}"; do
  ebid=$(echo "$f" | sed -E 's/^.*_uid___//; s/\.asdm\.sdm\.tar$//')
  if [ -f "$LOGDIR/dl_${ebid}.done" ] && [ ! -f "$DEST/${f}.aria2" ]; then
    echo "  OK   $f"
  else
    echo "  MISSING/INCOMPLETE $f (check $LOGDIR/dl_pool_${ebid}.log)"
  fi
done
