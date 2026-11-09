#!/usr/bin/env python3
"""Round-7 P90 campaign: the analysis the round-8 referees asked for.

Reads the campaign's own unit records and its own collect() output.  Adds
nothing to the measurement and retunes nothing; every constant here is either
read from the campaign or is a referee's own number quoted for comparison.

THE GATES ARE NOT REIMPLEMENTED HERE.  This script refuses to emit a single
number unless campaign_p90_r7.py collect has already asserted
  * null_ok                -- the clean pass recovered essentially nothing, and
  * positive_control_ok    -- every folded-in unit recovered its own 20x carrier
and those asserts stay where they are, as literals.
"""
import glob
import json
import os
import sys

import numpy as np

ROOT = os.environ.get('P90R7_ROOT', '/data/SETI/p90_r7')
COLLECT = os.environ.get('P90R7_COLLECT', f'{ROOT}/p90_r7_result.json')
OUTJSON = os.environ.get('P90R7_ANALYSIS', f'{ROOT}/p90_r7_analysis.json')

res = json.load(open(COLLECT))
if not res.get('campaign_valid'):
    sys.exit('REFUSING: campaign_valid is False (null_ok=%s positive_control_ok=%s)'
             % (res.get('null_ok'), res.get('positive_control_ok')))

recs = [json.load(open(f)) for f in sorted(glob.glob(f'{ROOT}/out/*.json'))]
bad = [r for r in recs if r.get('status') not in ('ok', 'partial')
       or not r.get('rungs')]
pcfail = {t for t, _ in res['positive_control_failures']}
scored = [r for r in recs if r not in bad and r['unit']['tag'] not in pcfail]
assert len(scored) == res['n_units_scored'], (len(scored), res['n_units_scored'])

st = {s['stratum']: s for s in res['strata']}


def tones(units, want_fit=False, posctrl=False):
    for r in units:
        for g in r['rungs']:
            if bool(g.get('is_positive_control')) != posctrl:
                continue
            for t in g['tones']:
                if want_fit and t.get('fit_status') != 'ok':
                    continue
                yield r, g, t


def q(a, ps=(16, 50, 84)):
    a = np.asarray([x for x in a if x is not None and np.isfinite(x)], float)
    if not len(a):
        return None
    return [float(np.percentile(a, p)) for p in ps]


# ------------------------------------------------------------------ 1. R2-5
# Does the 90 per cent point exist at all, and is it bracketed in every
# bootstrap resample?  Referee 2: "In 26 per cent of bootstrap resamples the
# Class A curve never reaches 90 per cent, and recovery saturates at 0.945."
sat = {}
for label in ('all', 'class A', 'class B'):
    s = st.get(label)
    if not s:
        continue
    lad = s['ladder']
    xs = [d['amp_over_trig'] for d in lad]
    d = {}
    for key, col in (('trigger', 'frac_trigger'),
                     ('trigger_and_localised', 'frac_trigger_and_localised'),
                     ('trigger_and_localised_r6epoch',
                      'frac_trigger_and_localised_r6committed')):
        ys = [x[col] for x in lad]
        ymax = max(ys)
        # where it plateaus: the first ladder point from which the curve never
        # again improves by more than 0.005
        plateau = None
        for i in range(len(xs)):
            if all(ys[j] - ys[i] <= 0.005 for j in range(i, len(ys))):
                plateau = xs[i]
                break
        d[key] = dict(
            ladder_amp=xs, frac=ys, max_frac=ymax, plateau_amp=plateau,
            reaches_90=bool(ymax >= 0.90),
            asymptote_note=('saturates at %.3f below 0.90: P90 does not exist '
                            'for this selection' % ymax) if ymax < 0.90 else '')
    d['P90_trigger'] = s['P90_over_trigger']
    d['P90_trigger_ci68'] = s['P90_ci68']
    d['P90_trigger_bootstrap_undefined_frac'] = s['P90_bootstrap_undefined_frac']
    d['P90_loc'] = s['P90_loc_over_trigger']
    d['P90_loc_ci68'] = s['P90_loc_ci68']
    d['P90_loc_bootstrap_undefined_frac'] = s['P90_loc_bootstrap_undefined_frac']
    d['P90_loc_r6epoch'] = s['P90_loc_r6committed_over_trigger']
    d['P90_loc_r6epoch_bootstrap_undefined_frac'] = \
        s['P90_loc_r6committed_bootstrap_undefined_frac']
    d['n_units'] = s['n_units']
    d['n_tones'] = s['n_tones']
    d['ladder_top'] = s['ladder_top']
    d['rank_gate_frac_at_20x'] = s['rank_gate_frac_at_top_rung']
    d['ctrl_top_clean_median'] = s['ctrl_top_clean']
    d['ctrl_top_at_20x_median'] = s['ctrl_top_at_top_rung']
    sat[label] = d

# ------------------------------------------------------------------ 2. R2-3
# Re/sigma recovered against injected amplitude, and against recovered T*.
def relation(units, label):
    rows = []
    for _, g, t in tones(units, want_fit=True):
        rows.append((g['amp_over_trig'], t['snr'], t['snr_re'],
                     t.get('snr_im'), t.get('snr_re_r6'), t.get('re_over_amp')))
    rows = np.array([r[:3] + (r[3] if r[3] is not None else np.nan,
                              r[4] if r[4] is not None else np.nan,
                              r[5] if r[5] is not None else np.nan)
                     for r in rows], float) if rows else np.zeros((0, 6))
    byamp = []
    for a in sorted(set(rows[:, 0])):
        m = rows[:, 0] == a
        byamp.append(dict(amp_over_trig=float(a), n=int(m.sum()),
                          snr_re=q(rows[m, 2]), tstar=q(rows[m, 1]),
                          snr_im=q(rows[m, 3]),
                          snr_re_r6epoch=q(rows[m, 4])))
    # against recovered T*, in T* bins
    edges = [5, 6, 7, 8, 10, 13, 17, 25, 40, 1e9]
    bytstar = []
    for lo, hi in zip([0] + edges[:-1], edges):
        m = (rows[:, 1] >= lo) & (rows[:, 1] < hi)
        if m.sum() < 8:
            continue
        bytstar.append(dict(tstar_lo=lo, tstar_hi=(hi if hi < 1e8 else None),
                            n=int(m.sum()), tstar=q(rows[m, 1]),
                            snr_re=q(rows[m, 2]),
                            ratio_snrre_over_tstar=q(rows[m, 2] / rows[m, 1])))
    # the band that matters: recovered T* matching the survey's crossings
    m5 = (rows[:, 1] >= 4.5) & (rows[:, 1] < 6.0)
    at5 = dict(n=int(m5.sum()),
               snr_re=q(rows[m5, 2]),
               snr_re_mean=float(np.mean(rows[m5, 2])) if m5.sum() else None,
               snr_re_sd=float(np.std(rows[m5, 2], ddof=1)) if m5.sum() > 1 else None,
               tstar=q(rows[m5, 1]),
               amp_over_trig=q(rows[m5, 0]),
               frac_amp_below_1=float(np.mean(rows[m5, 0] < 1.0)) if m5.sum() else None,
               snr_re_r6epoch=q(rows[m5, 4]),
               frac_localised_re_ge4=float(np.mean(rows[m5, 2] >= 4.0))
               if m5.sum() else None)
    # how much of the scatter is the epoch defect: same tones, both epochs
    ok = np.isfinite(rows[:, 4])
    epoch = dict(n=int(ok.sum()),
                 snr_re_correct=q(rows[ok, 2]), snr_re_r6epoch=q(rows[ok, 4]),
                 median_ratio=float(np.median(rows[ok, 4] / rows[ok, 2]))
                 if ok.sum() else None,
                 frac_r6epoch_below_4_while_correct_above=float(np.mean(
                     (rows[ok, 2] >= 4) & (rows[ok, 4] < 4))) if ok.sum() else None)
    return dict(label=label, n_fits=len(rows), by_amp=byamp,
                by_recovered_tstar=bytstar, at_tstar_5=at5, epoch=epoch)


rel = {'all': relation(scored, 'all'),
       'class A': relation([r for r in scored if r['unit']['res_class'] == 'A'],
                           'class A')}

# ------------------------------------------------------------------ 3. R1-5
# directly tested against transferred, per class
transfer = {}
for label in ('all', 'class A', 'class B'):
    s = st.get(label)
    if not s:
        continue
    tr = s['transfer_spread_loc']
    trt = s['transfer_spread_trigger']
    transfer[label] = dict(
        n_units_directly_tested=s['n_units'],
        n_blocks_directly_tested=s['n_blocks'],
        per_unit_P90_loc_defined=tr['n_defined'],
        per_unit_P90_loc_median=tr['median'], p16=tr['p16'], p84=tr['p84'],
        min=tr['min'], max=tr['max'],
        per_unit_P90_trigger_median=trt['median'],
        transfer_factor_p16_over_median=(tr['p16'] / tr['median'])
        if tr['median'] else None,
        transfer_factor_p84_over_median=(tr['p84'] / tr['median'])
        if tr['median'] else None,
        transfer_factor_min_over_median=(tr['min'] / tr['median'])
        if tr['median'] else None,
        transfer_factor_max_over_median=(tr['max'] / tr['median'])
        if tr['median'] else None)

# ------------------------------------------------------------------ 4. R1-4
# per-window EIRP at the measured multiplier, for the units actually tested
eirp = []
for r in scored:
    b = r['baseline']
    eirp.append(dict(tag=r['unit']['tag'], star=r['unit']['star_name'],
                     res_class=r['unit']['res_class'],
                     array=r['unit']['array'],
                     dist_pc=b.get('distance_pc'),
                     EIRP_trigger_W=b.get('EIRP_min_W'),
                     S_trig_Jy=r.get('S_trig_Jy'),
                     freq_GHz=0.5 * (b['freq_lo_GHz'] + b['freq_hi_GHz']),
                     bandwidth_Hz=b.get('bandwidth_Hz'),
                     chanwidth_Hz=r['unit']['chanwidth_Hz'],
                     drift_max_Hz_s=b.get('drift_max_Hz_s'),
                     on_source_s=b.get('on_source_s'),
                     time_span_s=b.get('time_span_s')))

out = dict(
    generated=res['generated'],
    source_collect=COLLECT,
    gates=dict(campaign_valid=res['campaign_valid'], null_ok=res['null_ok'],
               null_zero=res['null_zero'],
               null_frac_localised=res['null_frac_localised'],
               null_ceiling_prefixed=res['null_ceiling_prefixed'],
               positive_control_ok=res['positive_control_ok'],
               positive_control_frac=st['all']['positive_control_frac'],
               positive_control_frac_localised=
               st['all']['positive_control_frac_localised']),
    n_units_total=res['n_units_total'], n_units_scored=res['n_units_scored'],
    n_units_failed=res['n_units_failed'], failed=res['failed'],
    positive_control_failures=res['positive_control_failures'],
    saturation=sat, relation=rel, transfer=transfer, eirp_windows=eirp)
json.dump(out, open(OUTJSON, 'w'), indent=1)

# ------------------------------------------------------------------- summary
print('gates: valid=%s null=%d/%d loc (%.4f%%, ceiling %.0f%%) pc=%.3f/%.3f'
      % (res['campaign_valid'], st['all']['null_recovered_localised'],
         st['all']['null_n'], 100 * (res['null_frac_localised'] or 0),
         100 * res['null_ceiling_prefixed'],
         st['all']['positive_control_frac'],
         st['all']['positive_control_frac_localised']))
for k, d in sat.items():
    for key in ('trigger', 'trigger_and_localised',
                'trigger_and_localised_r6epoch'):
        e = d[key]
        print('%-8s %-30s max %.3f plateau %s reaches90 %s'
              % (k, key, e['max_frac'], e['plateau_amp'], e['reaches_90']))
    print('%-8s P90trig %s ci %s undef %.3f | P90loc %s ci %s undef %.3f'
          % (k, d['P90_trigger'], d['P90_trigger_ci68'],
             d['P90_trigger_bootstrap_undefined_frac'], d['P90_loc'],
             d['P90_loc_ci68'], d['P90_loc_bootstrap_undefined_frac']))
for k, d in rel.items():
    a = d['at_tstar_5']
    print('%-8s fits %d | T*in[4.5,6): n=%d Re/sig %s mean %.2f sd %.2f '
          'amp %s frac(amp<1) %.3f frac(Re/sig>=4) %.3f'
          % (k, d['n_fits'], a['n'], ['%.2f' % x for x in (a['snr_re'] or [])],
             a['snr_re_mean'] or float('nan'), a['snr_re_sd'] or float('nan'),
             ['%.2f' % x for x in (a['amp_over_trig'] or [])],
             a['frac_amp_below_1'] or 0, a['frac_localised_re_ge4'] or 0))
for k, d in transfer.items():
    print('%-8s transfer: %d units, per-unit P90loc %s  x%.2f-x%.2f of median'
          % (k, d['n_units_directly_tested'],
             ['%.2f' % x for x in (d['per_unit_P90_loc_median'],
                                   d['p16'], d['p84'])
              if x is not None] if d['per_unit_P90_loc_median'] else None,
             d['transfer_factor_p16_over_median'] or 0,
             d['transfer_factor_p84_over_median'] or 0))
print('-> %s' % OUTJSON)
