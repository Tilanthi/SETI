#!/bin/bash
# Autonomous ALMA archive processing driver, v2.
#
# v1 (used for the TRAPPIST-1 Band-7 run, Aug 2026) downloaded each EB
# serially through a single mirror THEN calibrated it -- download and
# compute never overlapped, even though download (~50GB @ ~50MB/s = ~15min
# single-mirror, or ~1-2min with the multi-mirror pool below) is now much
# shorter than CASA calibration (~30min/EB, single-threaded). v2 fixes
# this: it PREFETCHES EB[i+1] in the background (via the weighted
# multi-mirror pool downloader, see mirror_pool_dl.sh) while EB[i] is
# being calibrated/searched, so network time is hidden behind compute time
# rather than adding to it.
#
# Disk is still the binding constraint for CALIBRATION (transient peak per
# EB ~= unpacked ASDM 44GB + full MS 90GB + compact MS 60GB), so EBs are
# still calibrated one at a time; only the DOWNLOAD of the next EB overlaps.
# See /workspace/SETI/STATUS.md and /shared/kb/skills/alma-archive-download.md
# for the full network-benchmarking writeup this design is based on.
#
# Usage: pipeline_all.sh <ALMA_PROJECT_CODE> EBID [EBID ...]
#   e.g. pipeline_all.sh 2017.1.00215.S A002_Xd0e450_X1e19 A002_Xd0e450_X259b ...
set -u
export CASASITECONFIG=/home/fetch-agi/.casa/config.py
export OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MKL_NUM_THREADS=1 NUMEXPR_NUM_THREADS=1
L=/data/SETI/logs; B=/data/SETI/bin; P=/data/SETI/products; R=/data/SETI/raw
mkdir -p "$L" "$B" "$P" "$R"
free_gb(){ df --output=avail -BG /data | tail -1 | tr -dc 0-9; }

PROJECT="$1"; shift
EBS=("$@")
filename_for(){ echo "${PROJECT}_uid___${1}.asdm.sdm.tar"; }

# Launch (or no-op if already done/running) a background prefetch of one EB
# via the weighted multi-mirror pool downloader.
prefetch(){
  local eb="$1"
  [ -f "$L/dl_${eb}.done" ] && return
  pgrep -f "mirror_pool_dl.sh $R $(filename_for "$eb")" >/dev/null 2>&1 && return
  echo "  [prefetch] launching background download of $eb $(date -u +%T)"
  setsid bash "$B/mirror_pool_dl.sh" "$R" "$(filename_for "$eb")" \
    >> "$L/dl_pool_driver_${eb}.log" 2>&1 </dev/null &
  disown
}

# DISK_GATE accounts for BOTH the current EB's calibration transient peak
# (~200GB) AND a concurrently-downloading next EB's raw tar (up to ~53GB).
DISK_GATE=${SETI_DISK_GATE_GB:-230}

for idx in "${!EBS[@]}"; do
  EB="${EBS[$idx]}"
  NEXT="${EBS[$((idx+1))]:-}"
  echo "########## $EB start $(date -u +%T)  free=$(free_gb)G ##########"

  prefetch "$EB"
  while [ ! -f "$L/dl_${EB}.done" ]; do
      echo "  waiting for download of $EB ... $(date -u +%T)  free=$(free_gb)G"; sleep 30
  done

  while [ "$(free_gb)" -lt "$DISK_GATE" ]; do
      echo "  wait disk (need ${DISK_GATE}G) $(date -u +%T) free=$(free_gb)G"; sleep 60
  done

  mkdir -p /data/SETI/run/$EB && cd /data/SETI/run/$EB
  if [ ! -d "$P/${EB}_trappist1_fdm.ms" ]; then
      python3 $B/step1b_calibrate.py $EB --import >> $L/run_${EB}.log 2>&1 \
        || { echo "  STEP1b FAILED"; continue; }
  fi

  # The next EB's download is network-bound; this EB's remaining steps are
  # CPU/disk-bound -- overlap them.
  [ -n "$NEXT" ] && prefetch "$NEXT"

  python3 $B/step2_extract.py $EB 40 >> $L/run_${EB}.log 2>&1 || { echo "  STEP2 FAILED"; continue; }
  python3 $B/step3_search.py  $EB 48 >> $L/run_${EB}.log 2>&1 || { echo "  STEP3 FAILED"; continue; }
  [ -d "$P/${EB}_trappist1_phasecal.ms" ] && python3 $B/validate_phasecal.py $EB >> $L/run_${EB}.log 2>&1

  rm -rf "$P/${EB}_trappist1_fdm.ms" "$P/${EB}_trappist1_phasecal.ms" /data/SETI/work/${EB}_compact.ms*
  rm -f  "$R/$(filename_for "$EB")"
  touch "$L/chain_${EB}.done"
  echo "########## $EB DONE $(date -u +%T)  free=$(free_gb)G ##########"
done

echo "ALL EBs FINISHED $(date -u +%T)"
python3 $B/step4_combine.py > $L/combine.log 2>&1
