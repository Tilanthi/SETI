#!/usr/bin/env python3
"""
Cross-target frequency-occupancy check (Glenn's Tier-1 item 1,
2026-08-30): our single-pointing archival survey has no ON/OFF cadence
to reject RFI the way single-dish surveys do, but it has something else
-- many independent, UNRELATED stars, at different distances and
different Doppler/velocity contexts, several of which happen to share
near-identical correlator setups (many of our Band 6 targets use the
same 223-225/225-227/239-241/241-243 GHz spw scheme). A narrowband
feature that recurs at the same observed frequency across several
unrelated targets is essentially certain to be RFI or an instrumental
artefact -- a real transmitter at a fixed topocentric frequency, seen
towards stars at different distances/velocities, would be an absurd
coincidence.

Uses only each target's already-computed *_result.json (star_peak_freq_GHz,
star_peak_snr, hit_freqs_GHz) -- no new data, no re-processing.

Usage: frequency_occupancy.py
Writes: /data/SETI/targets/frequency_occupancy_report.json
"""
import glob, json, re
from collections import defaultdict

TOL_MHZ = 5.0   # coincidence tolerance (generous vs typical <1 MHz chanwidths,
                 # deliberately conservative to catch near-but-not-exact matches)

records = []
for path in sorted(glob.glob('/data/SETI/targets/*/products/*_result.json')):
    try:
        d = json.load(open(path))
    except Exception:
        continue
    target_dir = path.split('/')[3]
    if 'star_peak_freq_GHz' not in d:
        continue
    records.append(dict(
        target_dir=target_dir, path=path, eb=d.get('eb'),
        chanwidth_Hz=d.get('chanwidth_Hz'),
        star_peak_freq_GHz=d['star_peak_freq_GHz'],
        star_peak_snr=d.get('star_peak_snr'),
        hit_freqs_GHz=d.get('hit_freqs_GHz', []),
        n_hits=d.get('n_hits_above_threshold', 0),
    ))

print(f"Loaded {len(records)} target/spw results")

# --- (A) peak-channel coincidence: does the SAME frequency show up as the
# top channel for >=2 DIFFERENT target directories? ---
by_freq = []
for r in records:
    by_freq.append((r['star_peak_freq_GHz'], r['target_dir'], r['star_peak_snr'], r['path']))
by_freq.sort()

clusters = []
used = [False] * len(by_freq)
for i in range(len(by_freq)):
    if used[i]:
        continue
    f0, t0, s0, p0 = by_freq[i]
    group = [(f0, t0, s0, p0)]
    used[i] = True
    j = i + 1
    while j < len(by_freq) and (by_freq[j][0] - f0) * 1e3 < TOL_MHZ:
        group.append(by_freq[j])
        used[j] = True
        j += 1
    targets_in_group = set(g[1] for g in group)
    if len(targets_in_group) >= 2:
        clusters.append(group)

print(f"\nPeak-channel coincidence clusters (>=2 distinct targets within {TOL_MHZ} MHz):")
for g in clusters:
    freqs = [x[0] for x in g]
    print(f"  {min(freqs):.5f}-{max(freqs):.5f} GHz : "
          f"{', '.join(f'{t} (SNR={s:.2f})' for f, t, s, p in g)}")

# --- (B) formal hit (SNR>5) coincidence across targets ---
hit_recs = []
for r in records:
    for hf in r['hit_freqs_GHz']:
        hit_recs.append((hf, r['target_dir']))
hit_recs.sort()
hit_clusters = []
used2 = [False] * len(hit_recs)
for i in range(len(hit_recs)):
    if used2[i]:
        continue
    f0, t0 = hit_recs[i]
    group = [(f0, t0)]
    used2[i] = True
    j = i + 1
    while j < len(hit_recs) and (hit_recs[j][0] - f0) * 1e3 < TOL_MHZ:
        group.append(hit_recs[j]); used2[j] = True; j += 1
    targets_in_group = set(g[1] for g in group)
    if len(targets_in_group) >= 2:
        hit_clusters.append(group)

print(f"\nTotal formal hits (SNR>5) across all targets: {len(hit_recs)}")
print(f"Formal-hit coincidence clusters across >=2 targets: {len(hit_clusters)}")
for g in hit_clusters:
    print(' ', g)

report = dict(
    n_target_spw_results=len(records),
    tolerance_MHz=TOL_MHZ,
    n_peak_coincidence_clusters=len(clusters),
    peak_coincidence_clusters=[
        dict(freq_lo_GHz=min(x[0] for x in g), freq_hi_GHz=max(x[0] for x in g),
             members=[dict(target=x[1], snr=x[2]) for x in g])
        for g in clusters],
    n_formal_hits=len(hit_recs),
    n_formal_hit_coincidence_clusters=len(hit_clusters),
)
json.dump(report, open('/data/SETI/targets/frequency_occupancy_report.json', 'w'), indent=1)
print("\nSaved report to /data/SETI/targets/frequency_occupancy_report.json")
