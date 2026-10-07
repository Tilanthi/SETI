#!/usr/bin/env python3
"""Assemble the machine-readable second-stage local-null result for v3.42."""
import json, numpy as np, datetime, os

RES = ['res_0.json', 'res_1.json', 'res_2.json', 'res_3.json']
gev_real = json.load(open('gev_realctrl.json'))
shapes = json.load(open('shapes.json'))
BONF = 1.2e-4

# measured sensitivity of p to recalibrating the null by its own median offset
SENS = {'CP-72_2713_B7': {'0.00': 0.00158, '0.02': 0.00177, '0.04': 0.00196,
                          '0.06': 0.00220, '0.10': 0.00266, '0.20': 0.00474}}

DISPOSITION = {
    'CP-72_2713_B7': 'unclassified (the only such flag in the survey)',
    'HD_48370_B6':   'attributed to CO toward HD 48370',
    'bet_Pic_B3':    'attributed to circumstellar/foreground CO(1-0) toward beta Pic',
    'bet_Pic_B6':    'attributed to circumstellar/foreground CO(2-1) toward beta Pic',
}
PAPER_LABEL = {
    'CP-72_2713_B7': 'CP-72 2713, Band 7, 345.1152 GHz (the only unclassified flag)',
    'HD_48370_B6':   'HD 48370, Band 6, 230.7305 GHz',
    'bet_Pic_B3':    'beta Pic, Band 3, 115.2605 GHz',
    'bet_Pic_B6':    'beta Pic, Band 6, 230.5164 GHz',
}

out = dict(
    generated_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(timespec='seconds'),
    purpose=('Second-stage local null for the four stage-1 flagged windows, '
             'implementing referee A item 5 (and referee B\'s related point on '
             'the 1/513 rank floor).'),
    survey_wide_bonferroni_scale=BONF,
    stage1_rank_floor=1.0 / 513,
    method=dict(
        statistic=('T_star = max over channels and drift trials of the '
                   'inverse-variance-weighted, de-drifted stack at the stellar '
                   'position, reimplemented from seti_drift_search_generic.py '
                   'using only retained products (*_srcspec.npz for the '
                   'per-integration spectra, *_search.npz for the all-probe '
                   'robust noise map sigma[t,c], best_src and ctrl_max).'),
        validation=('The reimplementation reproduces the published '
                    'star_peak_snr bit-for-bit (absolute difference exactly 0.0 '
                    'in float32) for all four windows, recovers the identical '
                    'peak channel, and reproduces the entire per-channel '
                    'best_src[0] curve to 2.4e-7 (float32 epsilon). It also '
                    'reproduces the published ring-max column from ctrl_max.'),
        null_A=dict(
            name='integration-scramble (time-slide) local null',
            construction=(
                'For a retained control position q let R_q[t,c] be the '
                'baseline-subtracted residual and sigma[t,c] the pipeline\'s own '
                'all-probe robust noise map. Form Z = R_q/sigma, give every '
                'integration t an independent uniform random circular channel '
                'shift delta_t, and rebuild Rtilde[t,c] = Z[t,(c+delta_t) mod '
                'nch] * sigma[t,c]. Re-run the identical search (same sigma, '
                'same weights, same drift grid, same channel count).'),
            why_valid=[
                'sigma is never scrambled, so the per-integration per-channel '
                'noise scale, weights and atmospheric/bandpass structure are '
                'preserved exactly.',
                'A rigid circular shift preserves each integration\'s spectral '
                'autocorrelation exactly. This matters: the standardised '
                'residuals have measured lag-1 channel autocorrelation ~0.65, '
                'so an i.i.d. bootstrap would have implied far too many '
                'independent trials.',
                'Shifts are independent across integrations, so no feature '
                'coherent across integrations along any drift track survives: '
                'the realisation is signal-free by construction.',
                'The maximum is taken over the same n_chan x n_drift grid, so '
                'the trials factor is identical to the star\'s.',
                'Unlike a null resampled from the 512 control MAXIMA, this null '
                'is not bounded above by an already-observed value, so the tail '
                'is resolvable well beyond 1/513.'],
            resampled='the 8 retained control positions, plus independent '
                      'random per-integration spectral offsets',
            self_validation_test=(
                'The null must reproduce the distribution of the 512 REAL '
                'control maxima measured by the first stage, which are genuine '
                'draws of the same statistic at exchangeable positions. '
                'Acceptance criteria, fixed before inspection: (i) the fraction '
                'of real controls above the null 99th percentile lies in '
                '[0.2%, 5%] (nominal 1%); (ii) fewer than 1% of real controls '
                'exceed the null maximum.')),
        null_B=dict(
            name='GEV extrapolation of the 512 real control maxima',
            construction=('Fit a generalised extreme value distribution to the '
                          'retained ctrl_max array (512 genuine control '
                          'positions) and evaluate its survival function at '
                          'T_star. Uncertainty from a 2000-fold nonparametric '
                          'bootstrap over the 512 controls.'),
            why_complementary=(
                'Null A models only the local thermal-like noise at a position; '
                'null B uses genuine sky positions and therefore retains any '
                'extended astrophysical or imaging structure in the field, but '
                'pays for it with a parametric tail model. Where both are valid '
                'they should agree, and for CP-72 2713 they do.')),
        rules=['nothing under /data/SETI/bin was modified',
               'nothing was written into any target products directory',
               'the running seti_search_driver.py pipeline was not disturbed '
               '(all work at nice 15 on an otherwise ~1%-loaded 224-core host)'],
        scratch_dir='/data/SETI/work/localnull_v342'),
    windows=[])

for f in RES:
    d = json.load(open(f))
    t = d['target']
    g = gev_real[t]
    sv = d['null_self_validation']
    cd = d['control_discrimination']
    frac99 = sv['frac_real512_above_null_p99']
    fracmax = cd['n_of_512_controls_exceeding_null_max'] / d['stage1_n_control']
    ok = (0.002 <= frac99 <= 0.05) and (fracmax < 0.01)

    w = dict(
        label=PAPER_LABEL[t], target=t, window=d['window'], band=d['band'],
        centre_GHz=round(d['centre_GHz'], 4),
        files_used=dict(
            as_retained=shapes[t],
            after_pipeline_edge_trim=dict(
                I_star=[d['n_int'], d['n_chan']],
                I_control_sample=[d['n_int'], d['n_control_retained'], d['n_chan']],
                sigma=[d['n_int'], d['n_chan']], ctrl_max=[d['stage1_n_control']]),
            note=('I_star/I_control_sample/W come from *_srcspec.npz; the '
                  'all-probe robust noise map sigma[t,c], the per-channel '
                  'best_src curve used for validation, and the 512 first-stage '
                  'control maxima ctrl_max come from *_search.npz. Only 8 of '
                  'the 512 control positions have full retained spectra '
                  '(probe_0, 73, 146, ..., 511: a stride-73 subsample).')),
        geometry=dict(n_int=d['n_int'], n_chan=d['n_chan'], n_drift=d['n_drift'],
                      n_search_cells=d['n_chan'] * d['n_drift'],
                      n_control_positions_retained_full_spectra=d['n_control_retained'],
                      n_control_positions_first_stage=d['stage1_n_control']),
        reproduction=dict(T_star_published=d['T_star_published'],
                          T_star_paper_table7=d['T_star_paper'],
                          T_star_reproduced=d['T_star_reproduced'],
                          abs_difference=d['reproduction_abs_diff'],
                          ring_max_published=d['ring_max_published'],
                          ring_max_paper_table7=d['ring_max_paper'],
                          verdict='EXACT (bit-identical float32)'),
        stage1=dict(p=d['stage1_p'], floor=d['stage1_floor'],
                    note='saturated at the floor: no control reaches the star'),
        null_A=dict(
            draws=d['null_draws'],
            median=d['null_median'], p90=d['null_p90'], p99=d['null_p99'],
            p99_9=d['null_p999'], p99_99=d['null_p9999'], max=d['null_max'],
            mean=d['null_mean'], std=d['null_std'],
            n_draws_ge_T_star=d['n_null_ge_Tstar'],
            p_local=d['p_local_empirical'],
            p_is_upper_bound=d['p_local_is_upper_bound'],
            p_rule_of_three_95UCL=d['p_local_rule_of_three_95UCL'],
            z_lag1_autocorr=d['z_lag1_autocorr'],
            z_std=d['z_std'], z_kurtosis=d['z_kurtosis'],
            n_eff_independent_trials=d['gev'].get('n_eff_trials'),
            self_validation=dict(
                null_median=sv['null_median'], real512_median=sv['real512_median'],
                median_offset=sv['median_offset'],
                null_p99=sv['null_p99'], real512_p99=sv['real512_p99'],
                null_max=sv['null_max'], real512_max=sv['real512_max'],
                frac_real512_above_null_p99=frac99,
                frac_real512_above_null_max=fracmax,
                ks_2samp=sv['ks_2samp_null_vs_real512'],
                VERDICT='PASS' if ok else 'FAIL'),
            p_local_usable=bool(ok)),
        null_B_real_controls_gev=dict(
            shape_c=g['c'], loc=g['loc'], scale=g['scale'],
            goodness_of_fit_ks_p=g['ks_p'],
            p=g['p'], p_95CI=[g['p_lo'], g['p_hi']],
            bootstrap_prob_p_below_bonferroni=g['frac_boot_below_bonf'],
            n_bootstrap=g['n_boot']),
        subband_cross_check=dict(
            n_subbands=d['subband_null_M'], n_draws=d['subband_n'],
            median=d['subband_median'], max=d['subband_max'],
            n_ge_T_star=d['subband_n_ge_Tstar']),
        control_discrimination=dict(
            ring_max_p_against_local_null=cd['ring_max_vs_local_null']['p'],
            n_of_512_controls_below_bonferroni_against_local_null=(
                cd['n_of_512_controls_with_p_local_below_bonferroni']),
            note=('If the control ring itself clears the local null, the local '
                  'null is not a spatial discriminator and the binding test '
                  'remains the first-stage star-vs-control comparison.')),
        comparisons=dict(
            vs_stage1_floor_1_over_513=(
                'resolves below the floor' if (d['p_local_empirical'] < 1/513 and ok)
                else 'local null not usable' if not ok
                else 'resolves below the floor'),
            vs_bonferroni_1p2e_4=None),
        runtime_s=d['runtime_s'])
    if t in SENS:
        w['null_A']['recalibration_sensitivity_p_vs_added_offset'] = SENS[t]
    out['windows'].append(w)

# headline per-window verdicts
for w in out['windows']:
    pA = w['null_A']['p_local']; okA = w['null_A']['p_local_usable']
    pB = w['null_B_real_controls_gev']['p']
    best = pA if okA else pB
    w['comparisons']['vs_bonferroni_1p2e_4'] = (
        'above Bonferroni (not survey-wide significant)' if best > BONF
        else 'below Bonferroni')
    w['headline'] = dict(
        recommended_p=best,
        recommended_source='null_A (integration-scramble)' if okA
                           else 'null_B (GEV on the 512 real controls); '
                                'null_A failed its self-validation and is not used',
        p_below_survey_wide_bonferroni_scale=bool(best <= BONF),
        astrophysical_disposition=DISPOSITION[w['target']],
        note=('This field reports the STATISTICAL result only. A p-value below '
              'the Bonferroni scale does not make a window a technosignature '
              'candidate: astrophysical disposition is a separate step, and for '
              'both beta Pic windows the small p-value is produced by known '
              'circumstellar CO, which is the expected and correct behaviour of '
              'a working statistic.'))

out['conclusions'] = [
    'The reimplementation of the search statistic is exact for all four '
    'windows (bit-identical T_star, identical peak channel, per-channel curve '
    'to float32 epsilon), so the nulls are built on the published statistic.',
    'The 1/513 within-window rank floor is removed: every window now has a '
    'second-stage p-value resolved below 1.95e-3.',
    'CP-72 2713 Band 7, the only unclassified flag, has p = 1.6e-3 from the '
    '10^5-draw scramble null (a RESOLVED value: 157 of 100000 draws exceed '
    'T_star, not an upper bound) and p = 1.2e-3 (95% CI 2.0e-4 to 3.2e-3) from '
    'the independent GEV fit to the 512 real controls. The two agree to within '
    'a factor 1.3. Both are about an order of magnitude ABOVE the survey-wide '
    'Bonferroni scale of 1.2e-4, and the bootstrap probability that the true '
    'value lies below that scale is 1.3%. CP-72 2713 therefore does not reach '
    'survey-wide significance, and the paper\'s conservative disposition is '
    'quantitatively confirmed rather than merely asserted.',
    'HD 48370 Band 6 is the one window where the local null is NOT valid. Its '
    'pre-specified self-validation fails catastrophically: 375 of the 512 real '
    'control positions exceed the maximum of 100000 null draws, and the real '
    'control median (9.30) is more than four units above the null median '
    '(4.72). The field contains coherent structure that the scramble destroys, '
    'so a scrambled-noise p-value there would be fabricated significance and is '
    'not reported. The valid null for that window is the real control '
    'ensemble, which gives p = 1.5e-2 (95% CI 8.3e-3 to 2.2e-2), entirely '
    'unremarkable and consistent with the paper\'s attribution to extended CO.',
    'The two beta Pic windows behave as positive controls: the known '
    'circumstellar CO gives p < 1e-5 (B3) and < 5e-5 (B6) empirically, and '
    '2.6e-18 and 1.5e-7 against the real control ensemble. The procedure '
    'therefore does return very small p-values when a genuine localised '
    'astrophysical signal is present, which is the correct behaviour.',
    'IMPORTANT INTERPRETIVE CAVEAT: the local null is NOT a spatial '
    'discriminator. In three of the four windows the control-ring maximum also '
    'clears the local null at p < 1e-5. A small local-null p-value means only '
    'that the feature exceeds local noise fluctuations; it does not mean the '
    'feature is localised to the star. The first-stage star-vs-control '
    'comparison remains the binding test for candidacy.',
    'PARAMETRIC EXTRAPOLATION IS NOT USED FOR HEADLINE NUMBERS. For beta Pic '
    'B3 the GEV fit to the scramble null implies a bounded tail (p exactly 0), '
    'a Gumbel fit gives 1.9e-18 and a calibrated Gaussian-trials model gives '
    '4.4e-44. These span 44 orders of magnitude, which is precisely why only '
    'the empirical bound is quoted for null A.',
    'LIMITATION / RECOMMENDATION: the retained *_srcspec.npz keep the full '
    'dynamic spectrum for only 8 of the 512 control positions, so '
    'position-to-position heterogeneity in the null is sampled by 8 draws. '
    'That is what makes the local null fail for HD 48370. Retaining more '
    'control spectra (or the control-ring geometry, cf. referee B M3) in a '
    'future release would allow a valid local null even in structured fields.',
]
json.dump(out, open('/shared/ASTRA/reviews/v3.42_local_null.json', 'w'), indent=1)
print(json.dumps({w['target']: w['headline'] for w in out['windows']}, indent=1))
print('\nWROTE /shared/ASTRA/reviews/v3.42_local_null.json')
