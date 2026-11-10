#!/usr/bin/env python3
"""
Step 5: combine results across ALL bands/checks into one final report.

Bands/checks recognised by filename suffix:
  {EB}_result.json                 Band 7 (2017.1.00215.S), original search
  {EB}_deep_result.json            Band 7, widened/finer drift search (robustness check)
  {EB}_calcheck_phasecal_result.json  Band 7, same search run on the phase calibrator
  {EB}_calcheck_bpcal_result.json     Band 7, same search run on the bandpass calibrator
  {EB}_B6_result.json              Band 6 (2024.A.00040.S)
  {EB}_B3_result.json              Band 3 (2017.1.00986.S)
"""
import os, glob, json
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

ROOT = '/data/SETI'
PROD = f'{ROOT}/products'
FIG = f'{ROOT}/figures'
os.makedirs(FIG, exist_ok=True)

PC_M = 3.0856775814913673e16
SNR_THRESH = 5.0
EIRP_ARECIBO = 1e13
REF = dict(EIRP=6.91e17, N=28, nu_frac=(0.059 + 0.058) / 91.9)


def load(pattern, exclude=()):
    out = []
    for j in sorted(glob.glob(f'{PROD}/{pattern}')):
        if any(x in j for x in exclude):
            continue
        out.append(json.load(open(j)))
    return out


def combine_band(res, label, hanning=1.0):
    if not res:
        return None
    sig = np.array([r['rms_combined_mJy'] for r in res]) * 1e-3
    sig_all = 1.0 / np.sqrt(np.sum(1.0 / sig**2))
    d_pc = res[0]['distance_pc']
    d_m = d_pc * PC_M
    chanw = res[0]['chanwidth_Hz']
    S_min = SNR_THRESH * sig_all
    eirp_spacing = 4 * np.pi * d_m**2 * (S_min * 1e-26) * chanw
    eirp_eff = eirp_spacing * hanning
    ndet = sum(r['n_hits_above_threshold'] for r in res)
    ctrl_peak = max(r['control_peak_snr'] for r in res)
    star_peak = max(r['star_peak_snr'] for r in res)
    total_hrs = sum(r['on_source_s'] for r in res) / 3600
    print(f"\n=== {label}: {len(res)} EB(s), {total_hrs:.2f} h on-source ===")
    print(f"  channel width {chanw/1e3:.2f} kHz, band "
          f"{res[0]['freq_lo_GHz']:.2f}-{res[0]['freq_hi_GHz']:.2f} GHz")
    print(f"  combined rms {sig_all*1e6:.1f} uJy -> EIRP_min "
          f"(x{hanning:.0f} eff.res.) = {eirp_eff:.3e} W")
    print(f"  star peak SNR {star_peak:.2f} vs control ceiling {ctrl_peak:.2f}, "
          f"{ndet} hit(s) above SNR {SNR_THRESH}")
    return dict(label=label, n_eb=len(res), total_on_source_h=total_hrs,
                chanwidth_Hz=chanw, freq_lo_GHz=res[0]['freq_lo_GHz'],
                freq_hi_GHz=res[0]['freq_hi_GHz'],
                rms_combined_uJy=sig_all * 1e6, EIRP_min_W=eirp_eff,
                distance_pc=d_pc, star_peak_snr=star_peak,
                control_peak_snr=ctrl_peak, n_hits=ndet,
                detection=bool(star_peak > ctrl_peak and ndet > 0),
                per_eb=res)


def main():
    b7 = load('*_result.json', exclude=('_inj', '_deep', '_calcheck', '_B6', '_B3'))
    b7_deep = load('*_deep_result.json')
    b7_cal_phase = load('*_calcheck_phasecal_result.json')
    b7_cal_bp = load('*_calcheck_bpcal_result.json')
    b6 = load('*_B6_result.json')
    b3 = load('*_B3_result.json')

    summary = {}
    summary['band7'] = combine_band(b7, 'Band 7 (2017.1.00215.S) -- original search', hanning=2.0)
    summary['band7_deep'] = combine_band(b7_deep, 'Band 7 -- widened/finer drift search (+/-12000 Hz/s)', hanning=2.0)
    summary['band6'] = combine_band(b6, 'Band 6 (2024.A.00040.S)', hanning=1.0)
    summary['band3'] = combine_band(b3, 'Band 3 (2017.1.00986.S)', hanning=1.0)

    # calibrator systematics check (not a new EIRP limit; SNR-only report)
    print("\n=== Band 7 calibrator-field systematics check ===")
    cal_report = []
    for tag, res in (('phase calibrator (J2301-0158)', b7_cal_phase),
                      ('bandpass calibrator (varies per EB)', b7_cal_bp)):
        for r in res:
            flag = 'ANOMALY' if r['star_peak_snr'] > r['control_peak_snr'] and r['n_hits_above_threshold'] > 0 else 'clean'
            print(f"  {r['eb']:<22} {tag:<38} peak SNR {r['star_peak_snr']:.2f} "
                  f"vs control {r['control_peak_snr']:.2f}  [{flag}]")
            cal_report.append(dict(eb=r['eb'], field=tag,
                                    star_peak_snr=r['star_peak_snr'],
                                    control_peak_snr=r['control_peak_snr'],
                                    n_hits=r['n_hits_above_threshold'],
                                    hit_freqs_GHz=r.get('hit_freqs_GHz', []),
                                    flag=flag))
    summary['calibrator_check'] = cal_report

    json.dump(summary, open(f'{PROD}/MULTIBAND_FINAL_RESULT.json', 'w'), indent=1)

    # ------------------------------------------------------------ figure
    bands = [(k, v) for k, v in [('Band 3', summary['band3']),
                                  ('Band 6', summary['band6']),
                                  ('Band 7', summary['band7'])] if v]
    fig, ax = plt.subplots(1, 2, figsize=(12, 5))
    labels = [b[0] for b in bands] + ['Mason+24\n(ALMA B3)', 'Arecibo\nradar']
    vals = [b[1]['EIRP_min_W'] for b in bands] + [REF['EIRP'], EIRP_ARECIBO]
    colors = ['C0', 'C1', 'C2', 'C3', 'C4'][:len(vals)]
    ax[0].bar(labels, vals, color=colors)
    ax[0].set_yscale('log'); ax[0].set_ylabel(r'$EIRP_{min}$ (W)')
    ax[0].set_title('Minimum detectable transmitter power by band')
    for i, v in enumerate(vals):
        ax[0].text(i, v * 1.3, f'{v:.1e}', ha='center', fontsize=8, rotation=90)
    ax[0].tick_params(axis='x', rotation=30)

    freqs_ghz = [(b[1]['freq_lo_GHz'] + b[1]['freq_hi_GHz']) / 2 for b in bands]
    eirps = [b[1]['EIRP_min_W'] for b in bands]
    ax[1].scatter(freqs_ghz, eirps, s=80, c=['C0', 'C1', 'C2'][:len(bands)])
    for (lbl, _), f, e in zip(bands, freqs_ghz, eirps):
        ax[1].annotate(lbl, (f, e), textcoords="offset points", xytext=(8, 5))
    ax[1].set_yscale('log'); ax[1].set_xlabel('Frequency (GHz)')
    ax[1].set_ylabel(r'$EIRP_{min}$ (W)')
    ax[1].set_title('TRAPPIST-1 technosignature sensitivity vs frequency')

    plt.tight_layout()
    plt.savefig(f'{FIG}/multiband_summary.png', dpi=140)
    print(f'\nfigure -> {FIG}/multiband_summary.png')
    print(f'summary -> {PROD}/MULTIBAND_FINAL_RESULT.json')


if __name__ == '__main__':
    main()
