#!/bin/bash
set -u
B=/data/SETI/bin
SRC=/data/SETI/targets/HD172555_B7/products/A002_X107376c_X4442_spw0_search.ms
T=/data/SETI/injection_e2e
EB=A002_X107376c_X4442
export SETI_TARGET_DIR=$T SETI_MS=$SRC
export SETI_STAR_NAME="HD172555 (e2e injection test)"
export SETI_STAR_RA=281.3624218338677 SETI_STAR_DEC=-64.87192513545952
export SETI_STAR_PMRA=31.952325282703374 SETI_STAR_PMDEC=-149.7298949001875
export SETI_STAR_PARALLAX=34.7354715858406 SETI_STAR_PARALLAX_ERR=0.001
NC=6
RMS=0.008752907                    # Jy, per integration, from the baseline pass
FINJ=342960632885.85               # ~60 channels into the band
for MULT in 1 3 10; do
  AMP=$(python3 -c "print(f'{$RMS*$MULT:.9f}')")
  export SETI_SFX="_inj${MULT}"
  export SETI_INJECT="${AMP},0.0,${FINJ}"     # drift = 0  -> persistent, frequency-stationary
  echo "###### injecting ${MULT}x per-int rms = ${AMP} Jy, drift 0 (dwell 1.0) ######"
  nice -n 15 python3 $B/seti_extract_generic.py $EB $NC > $T/logs/inj${MULT}_extract.log 2>&1 || { echo EXTRACT_FAIL; tail -4 $T/logs/inj${MULT}_extract.log; continue; }
  nice -n 15 python3 $B/seti_drift_search_generic.py $EB $NC > $T/logs/inj${MULT}_search.log 2>&1 || { echo SEARCH_FAIL; tail -4 $T/logs/inj${MULT}_search.log; continue; }
  python3 - <<PY
import json,glob
f=sorted(glob.glob("$T/products/*_inj${MULT}_result.json"))
if not f: print("  no result json"); raise SystemExit
r=json.load(open(f[0]))
print("  RESULT mult=${MULT}: star_peak_snr=%.2f  peak_freq=%.6f GHz  peak_drift=%.1f Hz/s  n_hits=%s  detection=%s"%(
  r["star_peak_snr"], r["star_peak_freq_GHz"], r["star_peak_drift_Hz_s"],
  r.get("n_hits_above_threshold"), r.get("detection")))
print("  injected at %.6f GHz"%($FINJ/1e9))
PY
done
echo "### disk ###"; df -h /data | tail -1
