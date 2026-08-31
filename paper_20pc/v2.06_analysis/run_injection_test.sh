#!/bin/bash
# Injection-recovery validation campaign: quantify the SETI pipeline's
# empirical completeness as a function of injected signal SNR, using
# Proxima Cen's already-validated MOUS (uid://A001/X2d1f/X30f), isolated
# in its own directory so as not to interfere with the live 120-target
# driver's own state/markers.
set -u
B=/data/SETI/bin
TDIR=/data/SETI/injection_test/ProximaCen_inj
source "$B/governor.sh"
LOG="$TDIR/logs/campaign.log"
exec > >(tee -a "$LOG") 2>&1

echo "=== injection-recovery campaign start $(date -u +%FT%TZ) ==="

if [ ! -f "$TDIR/logs/calibrate_status.json" ]; then
  wait_for_headroom "injtest:calibrate"
  run_throttled "$MAX_CORES" python3 "$B/calibrate_generic.py" "$TDIR" "uid://A001/X2d1f/X30f" "$MAX_CORES"
  if [ $? -ne 0 ]; then echo "CALIBRATION FAILED, aborting"; exit 1; fi
fi
echo "=== calibration done, selecting finest spw ==="
wait_for_headroom "injtest:spw_select"
run_throttled 2 python3 "$B/select_finest_spw.py" "$TDIR"
if [ ! -f "$TDIR/logs/spw_list.json" ]; then echo "spw selection failed"; exit 1; fi

EB=$(python3 -c "import json; print(json.load(open('$TDIR/logs/spw_list.json'))['spw_list'][0]['eb'])")
MS=$(python3 -c "import json; print(json.load(open('$TDIR/logs/spw_list.json'))['spw_list'][0]['ms'])")
echo "=== using EB=$EB MS=$MS for injection grid ==="

export SETI_TARGET_DIR="$TDIR"
export SETI_STAR_NAME="Proxima Cen (injection test)"
# Proxima Cen astrometry (from ranked_master20pc.csv rank 1)
export SETI_STAR_RA=217.39232147200883 SETI_STAR_DEC=-62.67607511676666
export SETI_STAR_PMRA=-3781.741008265163 SETI_STAR_PMDEC=769.4650146478623
export SETI_STAR_PARALLAX=768.1 SETI_STAR_PARALLAX_ERR=0.001
export SETI_MS="$MS"

# --- Step 0: baseline (no injection) run, to learn the true noise level ---
export SETI_SFX="_base"
unset SETI_INJECT
wait_for_headroom "injtest:baseline_extract"
run_throttled "$MAX_CORES" python3 "$B/seti_extract_generic.py" "$EB" "$MAX_CORES"
run_throttled "$MAX_CORES" python3 "$B/seti_drift_search_generic.py" "$EB" "$MAX_CORES"
BASE_JSON="$TDIR/products/${EB}_base_result.json"
RMS_JY=$(python3 -c "import json; d=json.load(open('$BASE_JSON')); print(d['rms_combined_mJy']/1000.0)")
NCH=$(python3 -c "import json; d=json.load(open('$BASE_JSON')); print(d['n_chan'])")
echo "=== baseline rms_combined = $RMS_JY Jy, n_chan=$NCH ==="

# --- Injection grid: SNR multiples of the baseline rms, at 3 channel
#     positions per amplitude to average over channel-to-channel noise
#     variation, drift = 0 Hz/s (recovered via the trial-drift grid like
#     any other signal). ---
SNR_LIST="1 2 3 4 5 6 8 10"
CH_FRACS="0.25 0.50 0.75"
RESULTS="$TDIR/logs/injection_results.jsonl"
> "$RESULTS"
for SNR in $SNR_LIST; do
  AMP=$(python3 -c "print($RMS_JY * $SNR)")
  for FRAC in $CH_FRACS; do
    CH=$(python3 -c "print(int($NCH * $FRAC))")
    export SETI_SFX="_inj_snr${SNR}_ch${CH}"
    export SETI_INJECT="${AMP},0.0,${CH}"
    wait_for_headroom "injtest:inj_snr${SNR}_ch${CH}"
    run_throttled "$MAX_CORES" python3 "$B/seti_extract_generic.py" "$EB" "$MAX_CORES"
    run_throttled "$MAX_CORES" python3 "$B/seti_drift_search_generic.py" "$EB" "$MAX_CORES"
    RJSON="$TDIR/products/${EB}${SETI_SFX}_result.json"
    if [ -f "$RJSON" ]; then
      python3 -c "
import json
d = json.load(open('$RJSON'))
rec = dict(snr_injected=$SNR, amp_jy=$AMP, chan=$CH,
           star_peak_snr=d['star_peak_snr'], detection=d['detection'],
           credible=d['credible_technosignature_candidate'],
           star_peak_chan=d['star_peak_chan'], star_peak_drift_Hz_s=d['star_peak_drift_Hz_s'])
open('$RESULTS','a').write(json.dumps(rec)+'\n')
"
      echo "SNR=$SNR ch=$CH -> recovered peak_snr=$(python3 -c "import json; print(json.load(open('$RJSON'))['star_peak_snr'])")"
    else
      echo "SNR=$SNR ch=$CH -> RESULT MISSING"
    fi
    # clean up this trial's bulky intermediate files immediately
    rm -f "$TDIR/products/${EB}${SETI_SFX}_waterfall.npz" "$TDIR/products/${EB}${SETI_SFX}_srcspec.npz" "$TDIR/products/${EB}${SETI_SFX}_search.npz"
  done
done
unset SETI_INJECT SETI_SFX

echo "=== injection-recovery campaign complete $(date -u +%FT%TZ) ==="
echo "=== cleaning up raw/calibrated MS (test data, not needed after this) ==="
rm -rf "$TDIR/raw" "$TDIR/work" "$TDIR"/products/*.ms
du -sh "$TDIR" 2>/dev/null
