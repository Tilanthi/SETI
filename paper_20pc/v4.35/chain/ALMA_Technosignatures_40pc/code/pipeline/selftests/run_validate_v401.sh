#!/bin/bash
# Validate inject_vis_v401.py end to end on a real calibrated window.
# Uses the smallest retained ACA block so the check costs minutes, not hours.
set -u
MS=/data/SETI/targets/HD53143__Gaia_DR3_5479222240596469632__B6_EB_Xdc45/products/A002_X10a341d_Xdc45_target.ms
SPW=2
W=/data/SETI/p90_r7/validate
export CASASITECONFIG=/home/fetch-agi/.casa/config.py
rm -rf "$W"; mkdir -p "$W"
python3 -c "
import os,sys
os.environ.setdefault('CASASITECONFIG','/home/fetch-agi/.casa/config.py')
from casatasks import split
split(vis=sys.argv[1], outputvis=sys.argv[2], spw=sys.argv[3],
      datacolumn='data', keepflags=False)
" "$MS" "$W/clean.ms" "$SPW" || { echo SPLIT_FAILED; exit 1; }
cp -a "$W/clean.ms" "$W/inj.ms"
# 48 tones at 2.0 Jy, phase centre, no drift: the sub-channel phases are drawn
# at random so the whole response curve is sampled, centre and boundary alike.
INJ_L=0 INJ_M=0 INJ_AMP_JY=2.0 INJ_DRIFT_MAX=0 \
  python3 /data/SETI/bin/inject_vis_v401.py "$W/inj.ms" 0 "$W/inj.json" 48 70101 \
  || { echo INJECT_FAILED; exit 1; }
python3 /data/SETI/bin/validate_inject_v401.py "$W/clean.ms" "$W/inj.ms" \
  "$W/inj.json" "$W/validate_result.json"
