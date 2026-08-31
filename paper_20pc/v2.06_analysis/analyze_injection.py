import json

lines = """{"snr_injected": 1, "amp_jy": 0.0021667482797056437, "chan": 29, "star_peak_snr": 2.8919708728790283, "detection": false, "credible": false, "star_peak_chan": 113, "star_peak_drift_Hz_s": 3541.030517578125}
{"snr_injected": 1, "amp_jy": 0.0021667482797056437, "chan": 59, "star_peak_snr": 2.8919708728790283, "detection": false, "credible": false, "star_peak_chan": 113, "star_peak_drift_Hz_s": 3541.030517578125}
{"snr_injected": 1, "amp_jy": 0.0021667482797056437, "chan": 88, "star_peak_snr": 2.874725818634033, "detection": false, "credible": false, "star_peak_chan": 113, "star_peak_drift_Hz_s": 3541.030517578125}
{"snr_injected": 2, "amp_jy": 0.004333496559411287, "chan": 29, "star_peak_snr": 2.8919708728790283, "detection": false, "credible": false, "star_peak_chan": 113, "star_peak_drift_Hz_s": 3541.030517578125}
{"snr_injected": 2, "amp_jy": 0.004333496559411287, "chan": 59, "star_peak_snr": 2.8919708728790283, "detection": false, "credible": false, "star_peak_chan": 113, "star_peak_drift_Hz_s": 3541.030517578125}
{"snr_injected": 2, "amp_jy": 0.004333496559411287, "chan": 88, "star_peak_snr": 2.860856771469116, "detection": false, "credible": false, "star_peak_chan": 113, "star_peak_drift_Hz_s": 3541.030517578125}
{"snr_injected": 3, "amp_jy": 0.006500244839116931, "chan": 29, "star_peak_snr": 2.8919708728790283, "detection": false, "credible": false, "star_peak_chan": 113, "star_peak_drift_Hz_s": 3541.030517578125}
{"snr_injected": 3, "amp_jy": 0.006500244839116931, "chan": 59, "star_peak_snr": 2.8919708728790283, "detection": false, "credible": false, "star_peak_chan": 113, "star_peak_drift_Hz_s": 3541.030517578125}
{"snr_injected": 3, "amp_jy": 0.006500244839116931, "chan": 88, "star_peak_snr": 3.2534170150756836, "detection": false, "credible": false, "star_peak_chan": 83, "star_peak_drift_Hz_s": -2688.0}
{"snr_injected": 4, "amp_jy": 0.008666993118822575, "chan": 29, "star_peak_snr": 3.0535106658935547, "detection": false, "credible": false, "star_peak_chan": 24, "star_peak_drift_Hz_s": -611.656494140625}
{"snr_injected": 4, "amp_jy": 0.008666993118822575, "chan": 59, "star_peak_snr": 2.8919708728790283, "detection": false, "credible": false, "star_peak_chan": 113, "star_peak_drift_Hz_s": 3541.030517578125}
{"snr_injected": 4, "amp_jy": 0.008666993118822575, "chan": 88, "star_peak_snr": 4.0083417892456055, "detection": false, "credible": false, "star_peak_chan": 83, "star_peak_drift_Hz_s": -2688.0}
{"snr_injected": 5, "amp_jy": 0.010833741398528218, "chan": 29, "star_peak_snr": 4.022928237915039, "detection": false, "credible": false, "star_peak_chan": 24, "star_peak_drift_Hz_s": -611.656494140625}
{"snr_injected": 5, "amp_jy": 0.010833741398528218, "chan": 59, "star_peak_snr": 3.8141579627990723, "detection": false, "credible": false, "star_peak_chan": 54, "star_peak_drift_Hz_s": -611.656494140625}
{"snr_injected": 5, "amp_jy": 0.010833741398528218, "chan": 88, "star_peak_snr": 4.898303508758545, "detection": false, "credible": false, "star_peak_chan": 83, "star_peak_drift_Hz_s": -611.656494140625}
{"snr_injected": 6, "amp_jy": 0.013000489678233862, "chan": 29, "star_peak_snr": 4.998950958251953, "detection": false, "credible": false, "star_peak_chan": 24, "star_peak_drift_Hz_s": -611.656494140625}
{"snr_injected": 6, "amp_jy": 0.013000489678233862, "chan": 59, "star_peak_snr": 4.768152236938477, "detection": false, "credible": false, "star_peak_chan": 54, "star_peak_drift_Hz_s": -611.656494140625}
{"snr_injected": 6, "amp_jy": 0.013000489678233862, "chan": 88, "star_peak_snr": 5.874053001403809, "detection": true, "credible": true, "star_peak_chan": 83, "star_peak_drift_Hz_s": -611.656494140625}
{"snr_injected": 8, "amp_jy": 0.01733398623764515, "chan": 29, "star_peak_snr": 6.9404988288879395, "detection": true, "credible": true, "star_peak_chan": 24, "star_peak_drift_Hz_s": -611.656494140625}
{"snr_injected": 8, "amp_jy": 0.01733398623764515, "chan": 59, "star_peak_snr": 6.6704182624816895, "detection": true, "credible": true, "star_peak_chan": 54, "star_peak_drift_Hz_s": -611.656494140625}
{"snr_injected": 8, "amp_jy": 0.01733398623764515, "chan": 88, "star_peak_snr": 7.819782257080078, "detection": true, "credible": true, "star_peak_chan": 83, "star_peak_drift_Hz_s": -611.656494140625}
{"snr_injected": 10, "amp_jy": 0.021667482797056437, "chan": 29, "star_peak_snr": 8.875321388244629, "detection": true, "credible": true, "star_peak_chan": 24, "star_peak_drift_Hz_s": -611.656494140625}
{"snr_injected": 10, "amp_jy": 0.021667482797056437, "chan": 59, "star_peak_snr": 8.57792854309082, "detection": true, "credible": true, "star_peak_chan": 54, "star_peak_drift_Hz_s": -611.656494140625}
{"snr_injected": 10, "amp_jy": 0.021667482797056437, "chan": 88, "star_peak_snr": 9.755650520324707, "detection": true, "credible": true, "star_peak_chan": 83, "star_peak_drift_Hz_s": -611.656494140625}""".splitlines()

rows = [json.loads(l) for l in lines]
from collections import defaultdict
by_snr = defaultdict(list)
for r in rows:
    by_snr[r['snr_injected']].append(r)

print(f"{'SNR_inj':>8} {'n':>3} {'n_det':>6} {'frac':>6} {'mean_recovered':>15}")
for snr in sorted(by_snr):
    grp = by_snr[snr]
    ndet = sum(1 for g in grp if g['detection'])
    mean_rec = sum(g['star_peak_snr'] for g in grp)/len(grp)
    print(f"{snr:8d} {len(grp):3d} {ndet:6d} {ndet/len(grp)*100:5.0f}% {mean_rec:15.2f}")

# ratio recovered/injected at high SNR (8,10) where signal dominates over noise floor
ratios = [g['star_peak_snr']/g['snr_injected'] for g in rows if g['snr_injected'] in (8,10)]
print(f"\nrecovered/injected ratio at SNR 8,10: mean={sum(ratios)/len(ratios):.3f}")
