#!/bin/bash
# End-to-end confirmation: does the FULL unmodified pipeline (visibility-level
# injection -> extract -> drift search) recover a temporally persistent,
# frequency-stationary carrier in a COARSE window?
set -u
B=/data/SETI/bin
SRC=/data/SETI/targets/HD172555_B7/products/A002_X107376c_X4442_spw0_search.ms
T=/data/SETI/injection_e2e
EB=A002_X107376c_X4442
mkdir -p $T/products $T/logs
export SETI_TARGET_DIR=$T SETI_MS=$SRC
export SETI_STAR_NAME="HD172555 (e2e injection test)"
export SETI_STAR_RA=281.3624218338677 SETI_STAR_DEC=-64.87192513545952
export SETI_STAR_PMRA=31.952325282703374 SETI_STAR_PMDEC=-149.7298949001875
export SETI_STAR_PARALLAX=34.7354715858406 SETI_STAR_PARALLAX_ERR=0.001
NC=6

echo "############ BASELINE (no injection) ############"
export SETI_SFX=_base; unset SETI_INJECT || true
nice -n 15 python3 $B/seti_extract_generic.py $EB $NC  > $T/logs/base_extract.log 2>&1 || { echo EXTRACT_FAIL; tail -5 $T/logs/base_extract.log; exit 1; }
nice -n 15 python3 $B/seti_drift_search_generic.py $EB $NC > $T/logs/base_search.log 2>&1 || { echo SEARCH_FAIL; tail -5 $T/logs/base_search.log; exit 1; }
python3 - <<PY
import json,glob
f=sorted(glob.glob("$T/products/*_base_result.json"))[0]
r=json.load(open(f))
print("BASELINE: star_peak_snr=%.2f  rms_per_int=%.4f mJy  n_int=%s nchan=%s chanw=%.2f MHz"%(
 r["star_peak_snr"],r["rms_per_int_mJy"],r["n_int"],r["n_chan"],r["chanwidth_Hz"]/1e6))
print("BASELINE_RMS_JY=%.9f"%(r["rms_per_int_mJy"]/1000.0))
print("FREQ_LO=%.9f"%(min(r["freq_lo_GHz"],r["freq_hi_GHz"])*1e9))
PY
