#!/usr/bin/env python3
"""
Step 4: combine all execution blocks, produce the final limits and figures.

Reports
  * the deepest single-EB and the EB-combined EIRP_min at SNR>5
  * the Continuous Wave Transmitter Figure of Merit (Enriquez et al. 2017)
  * a comparison with Mason et al. 2024 (arXiv:2411.19827)
  * empirical false-alarm statistics from the control positions
"""
import os, glob, json
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

ROOT = '/data/SETI'
PROD = f'{ROOT}/products'
FIG  = f'{ROOT}/figures'
os.makedirs(FIG, exist_ok=True)

PC_M = 3.0856775814913673e16
SNR_THRESH = 5.0
EIRP_ARECIBO = 1e13          # W, Arecibo planetary radar
# Mason et al. 2024, ALMA Band 3 archival survey
REF = dict(name='Mason et al. 2024 (ALMA Band 3)', EIRP=6.91e17, N=28,
           nu_frac=(0.059 + 0.058) / 91.9, band='90.6/93.2 GHz')


def cwtfm(eirp, nstar, nufrac):
    """Normalised so CWTFM = 1 for 1000 stars, nu_frac=0.5, EIRP=1e13 W."""
    return (eirp / EIRP_ARECIBO) * (1000.0 * 0.5) / (nstar * nufrac)


def main():
    res = []
    for j in sorted(glob.glob(f'{PROD}/*_result.json')):
        if '_inj' in j:
            continue
        res.append(json.load(open(j)))
    if not res:
        raise SystemExit('no per-EB results yet')
    res.sort(key=lambda r: r['eb'])
    print(f'{len(res)} execution blocks\n')

    hdr = (f"{'EB':<20}{'Nint':>6}{'on-src(s)':>10}{'rms/int':>9}"
           f"{'rms comb':>10}{'EIRP_min(W)':>14}{'peakSNR':>9}{'ctrlSNR':>9}")
    print(hdr); print('-' * len(hdr))
    for r in res:
        print(f"{r['eb']:<20}{r['n_int']:>6}{r['on_source_s']:>10.0f}"
              f"{r['rms_per_int_mJy']:>9.2f}{r['rms_combined_mJy']:>10.3f}"
              f"{r['EIRP_min_W']:>14.3e}{r['star_peak_snr']:>9.2f}"
              f"{r['control_peak_snr']:>9.2f}")

    # ---- combined sensitivity: inverse-variance across EBs ----------------
    sig = np.array([r['rms_combined_mJy'] for r in res]) * 1e-3      # Jy
    sig_all = 1.0 / np.sqrt(np.sum(1.0 / sig**2))
    d_pc = res[0]['distance_pc']; d_err = res[0]['distance_pc_err']
    d_m = d_pc * PC_M
    chanw = res[0]['chanwidth_Hz']
    S_min = SNR_THRESH * sig_all
    # ALMA applies Hanning smoothing to FDM windows in the correlator, so the
    # effective spectral resolution is TWICE the channel spacing.  A
    # monochromatic transmitter therefore spreads its power over ~976.56 kHz,
    # not 488.28 kHz.  We quote the conservative (effective-resolution) limit
    # as the headline and the channel-spacing value for direct comparison with
    # Mason et al. 2024, who quote their channel width.
    HANNING = 2.0
    eirp_spacing = 4 * np.pi * d_m**2 * (S_min * 1e-26) * chanw
    eirp_all = eirp_spacing * HANNING
    eirp_best = min(r['EIRP_min_W'] for r in res) * HANNING

    bw = res[0]['bandwidth_Hz']
    nu0 = 0.5 * (res[0]['freq_lo_GHz'] + res[0]['freq_hi_GHz']) * 1e9
    nufrac = bw / nu0
    N = 1

    ndet = sum(r['n_hits_above_threshold'] for r in res)
    print(f"\nDistance                 {d_pc:.3f} +/- {d_err:.3f} pc (Gaia DR3 parallax)")
    print(f"Channel width            {chanw/1e3:.2f} kHz")
    print(f"Searched band            {res[0]['freq_lo_GHz']:.3f}-{res[0]['freq_hi_GHz']:.3f} GHz"
          f"  (nu_frac = {nufrac:.5f})")
    print(f"Total on-source          {sum(r['on_source_s'] for r in res)/3600:.2f} h")
    print(f"Drift search             +/-{res[0]['drift_max_Hz_s']:.0f} Hz/s in "
          f"{res[0]['n_drift_trials']} steps of {res[0]['drift_step_Hz_s']:.1f} Hz/s")
    print(f"\nCombined channel-map rms {sig_all*1e6:.1f} uJy/beam")
    print(f"S_min (5 sigma)          {S_min*1e6:.1f} uJy")
    print(f"\n    EIRP_min per channel spacing (Mason+24 convention) {eirp_spacing:.3e} W")
    print(f"*** EIRP_min (best EB, effective resolution)  {eirp_best:.3e} W")
    print(f"*** EIRP_min (all EBs, effective resolution)  {eirp_all:.3e} W")
    print(f"    = {eirp_all/EIRP_ARECIBO:.2f} x Arecibo planetary radar (1e13 W)")
    print(f"    Mason et al. 2024:   {REF['EIRP']:.3e} W  "
          f"-> improvement x{REF['EIRP']/eirp_all:.3g}")
    print(f"\nCWTFM (this work)        {cwtfm(eirp_all, N, nufrac):.3e}")
    print(f"CWTFM (Mason 2024)       {cwtfm(REF['EIRP'], REF['N'], REF['nu_frac']):.3e}")
    print(f"\nCandidates with SNR>{SNR_THRESH}: {ndet}")

    summary = dict(
        n_eb=len(res), distance_pc=d_pc, distance_pc_err=d_err,
        chanwidth_Hz=chanw, bandwidth_Hz=bw, nu_frac=nufrac, n_star=N,
        total_on_source_h=sum(r['on_source_s'] for r in res) / 3600,
        rms_combined_uJy=sig_all * 1e6, S_min_uJy=S_min * 1e6,
        EIRP_min_best_EB_W=eirp_best, EIRP_min_combined_W=eirp_all,
        EIRP_min_combined_channel_spacing_W=eirp_spacing,
        effective_resolution_Hz=chanw * HANNING,
        EIRP_over_arecibo=eirp_all / EIRP_ARECIBO,
        improvement_over_Mason2024=REF['EIRP'] / eirp_all,
        CWTFM=cwtfm(eirp_all, N, nufrac),
        CWTFM_Mason2024=cwtfm(REF['EIRP'], REF['N'], REF['nu_frac']),
        n_candidates=ndet, per_eb=res)
    json.dump(summary, open(f'{PROD}/FINAL_RESULT.json', 'w'), indent=1)

    # ------------------------------------------------------------ figures
    fig, ax = plt.subplots(2, 2, figsize=(13, 9))

    # (a) best-SNR spectrum at the star, all EBs
    for r in res:
        z = np.load(f"{PROD}/{r['eb']}_search.npz")
        ax[0, 0].plot(z['freqs'] / 1e9, z['best_src'][0], lw=0.4,
                      label=r['eb'][-5:])
    ax[0, 0].axhline(SNR_THRESH, color='r', ls='--', label='SNR = 5')
    ax[0, 0].set_xlabel('Frequency (GHz)')
    ax[0, 0].set_ylabel('de-drifted SNR at TRAPPIST-1')
    ax[0, 0].set_title('(a) Technosignature search spectrum')
    ax[0, 0].legend(fontsize=7, ncol=2)

    # (b) SNR distribution: star vs control positions vs Gaussian
    allsrc = np.concatenate([np.load(f"{PROD}/{r['eb']}_search.npz")['best_src'][0]
                             for r in res])
    allctl = np.concatenate([np.load(f"{PROD}/{r['eb']}_search.npz")['ctrl_max']
                             for r in res])
    bins = np.linspace(-6, max(8, allsrc.max() * 1.05), 80)
    ax[0, 1].hist(allsrc, bins=bins, histtype='step', density=True,
                  label='TRAPPIST-1 pixel')
    ax[0, 1].axvline(SNR_THRESH, color='r', ls='--')
    ax[0, 1].axvline(allctl.max(), color='g', ls=':',
                     label=f'control max = {allctl.max():.2f}')
    ax[0, 1].set_yscale('log')
    ax[0, 1].set_xlabel('de-drifted SNR'); ax[0, 1].set_ylabel('pdf')
    ax[0, 1].set_title('(b) SNR statistics vs control positions')
    ax[0, 1].legend(fontsize=8)

    # (c) EIRP comparison
    labels = ['This work\nALMA B7\nTRAPPIST-1', 'Mason+24\nALMA B3', 'Arecibo\nradar']
    vals = [eirp_all, REF['EIRP'], EIRP_ARECIBO]
    ax[1, 0].bar(labels, vals, color=['C0', 'C1', 'C2'])
    ax[1, 0].set_yscale('log'); ax[1, 0].set_ylabel(r'$EIRP_{min}$ (W)')
    ax[1, 0].set_title('(c) Minimum detectable transmitter power')
    for i, v in enumerate(vals):
        ax[1, 0].text(i, v * 1.3, f'{v:.1e}', ha='center', fontsize=8)

    # (d) per-EB rms
    ax[1, 1].bar([r['eb'][-5:] for r in res],
                 [r['rms_combined_mJy'] * 1e3 for r in res])
    ax[1, 1].set_ylabel(r'de-drifted channel rms ($\mu$Jy/beam)')
    ax[1, 1].set_title('(d) Sensitivity per execution block')
    ax[1, 1].tick_params(axis='x', rotation=45)

    plt.tight_layout()
    plt.savefig(f'{FIG}/trappist1_seti_summary.png', dpi=140)
    print(f'\nfigure -> {FIG}/trappist1_seti_summary.png')
    print(f'summary -> {PROD}/FINAL_RESULT.json')


if __name__ == '__main__':
    main()
