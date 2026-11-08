#!/bin/bash
# Shared resource-governor functions for the 100-star SETI search.
#
# This cluster is SHARED infrastructure. This search is an explicitly
# SECONDARY/background task: it must never meaningfully impinge on other
# users' ability to use disk, CPU, or the general cluster environment.
# Every script in this pipeline sources this file and calls these checks
# before doing anything expensive.
#
# Self-imposed limits (deliberately conservative, not just "whatever's free
# right now" -- other users can appear at any time with no warning):
#   - Never let /data free space drop below MIN_FREE_GB.
#   - Never use more than MAX_CORES cores for any single step.
#   - Everything runs at nice 19 / ionice idle, so the OS scheduler always
#     prefers any other user's process over ours automatically.
#   - Before starting a new target, require the 1-minute load average to be
#     below LOAD_CEILING (idle baseline on this 224-core box is ~0.1-3.0;
#     we use a generous but still bounded ceiling and back off if exceeded,
#     since sustained high load is the clearest sign someone else is using
#     the machine).

set -u

MIN_FREE_GB=${SETI_MIN_FREE_GB:-150}      # hard floor on /data free space
MAX_CORES=${SETI_MAX_CORES:-8}            # cap per processing step
LOAD_CEILING=${SETI_LOAD_CEILING:-20}     # 1-min load average ceiling
POLL_INTERVAL=${SETI_POLL_INTERVAL:-60}   # seconds between backoff re-checks

NICE="nice -n 19"
IONICE="ionice -c3"
export OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MKL_NUM_THREADS=1 NUMEXPR_NUM_THREADS=1

free_gb() { df --output=avail -BG /data | tail -1 | tr -dc 0-9; }
load1() { awk '{print int($1)}' /proc/loadavg; }

# Block (with logging) until BOTH disk and load are within bounds. Call
# this before every expensive step (download, import, calibration, imaging,
# search). Never proceeds silently past a violation -- always logs why it
# waited, so a human reviewing logs can see exactly when/why we backed off.
wait_for_headroom() {
  local label="${1:-step}"
  while true; do
    local fg lg reason=""
    fg=$(free_gb); lg=$(load1)
    if [ "$fg" -lt "$MIN_FREE_GB" ]; then
      reason="disk: ${fg}G free < ${MIN_FREE_GB}G floor"
    elif [ "$lg" -gt "$LOAD_CEILING" ]; then
      reason="load: 1-min load ${lg} > ${LOAD_CEILING} ceiling (someone else is busy)"
    fi
    if [ -z "$reason" ]; then
      echo "[governor] OK for '$label': free=${fg}G load1=${lg}"
      return 0
    fi
    echo "[governor] WAITING before '$label': $reason ($(date -u +%T))"
    sleep "$POLL_INTERVAL"
  done
}

# Wrap a command with nice/ionice and a hard core-count cap via taskset,
# so it can never grab more than MAX_CORES regardless of internal threading.
run_throttled() {
  local ncores="${1:-$MAX_CORES}"; shift
  if [ "$ncores" -gt "$MAX_CORES" ]; then ncores=$MAX_CORES; fi
  local cpulist
  cpulist=$(seq -s, 0 $((ncores-1)))
  $NICE $IONICE taskset -c "$cpulist" "$@"
}

log_disk() {
  echo "[disk] $(date -u +%FT%TZ) SETI_total=$(du -sh /data/SETI 2>/dev/null | cut -f1) free=$(free_gb)G"
}
