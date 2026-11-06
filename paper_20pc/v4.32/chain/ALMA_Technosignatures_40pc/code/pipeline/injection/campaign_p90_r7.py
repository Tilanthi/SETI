#!/usr/bin/env python3
"""Round 7: measure the survey's completeness through the NEW candidate chain.

    injected carrier  ->  threshold recovery  ->  visibility localisation

Why this replaces the round-4 measurement.  The campaign that set P90^sel in
v4.00 scored recovery as "trigger AND the star outranks all 512 control
positions".  Both referees reject that gate: the control ensemble is
demonstrably non-exchangeable, its effective size is 13 for the ACA stratum
rather than 512, and it costs Class A a further factor 1.9 in sensitivity
while adding no evidence.  Referee 2's design moves the rank out of candidate
generation entirely and sends every threshold crossing to the drift-following,
continuum-subtracted visibility fit.  This campaign measures the completeness
of that chain, for both of its stages separately, so the paper can quote
trigger-only and trigger+localisation.

THE UNIT OF WORK is one (execution block, spectral window) pair.  For each:

  0. split that window out of the retained calibrated target measurement set,
     once, so the amplitude ladder copies a compact single-window MS rather
     than a multi-gigabyte multi-window one;
  1. run the clean, uninjected pass to get that window's own trigger flux
     S_trig = 5 sigma_combined, its drift bound, its primary-beam width and
     the star's direction cosines;
  2. walk an amplitude ladder in units of that window's own trigger flux,
     injecting several well-separated tones per pass with
     inject_vis_v401.py -- which deposits the correlator's own Hann lag-window
     response, validated on real visibilities at 0.500 of the flux in the peak
     channel at sub-channel phase 0 and 0.4244 at a channel boundary -- and
     run the UNMODIFIED extraction and drift search on each pass;
  3. for every tone that crosses the threshold, run the round-6 visibility fit
     at the cell the search actually found, and score it against the
     localisation criterion committed before the round-6 campaign was run.

THE LOCALISATION CRITERION IS FIXED AND IS NOT RETUNED HERE.  It is
referee_r6/LOCALISATION_CRITERION.md, repository commit edfcc0d3d7db of
2026-09-25T06:59:24Z: Re/sigma >= 4 at the stellar position, |Im/sigma| < 3,
and Re/sigma strictly greater than the maximum over the 8 annulus control
positions and the 4 off-event control frequencies.  The three constants below
are that criterion and nothing in this file may adjust them.

Two mandatory checks, both evaluated before any completeness number is
quoted:

  * the NULL.  The clean pass is scored at every rung's tone cells, so the
    same cells are tested with no signal present.  It must recover
    essentially nothing.
  * the POSITIVE CONTROL at 20x threshold.  A unit that cannot recover a
    20-sigma carrier deposited at its own stellar position is not evidence
    about anything, most obviously because the sign of the geometric phase
    cannot be tested by a source at the phase centre.  Such a unit is flagged,
    not folded into the curve.

Usage:  campaign_p90_r7.py plan     -- build the work plan
        campaign_p90_r7.py work     -- run as one lane (claims units)
        campaign_p90_r7.py collect  -- aggregate finished units
"""
import glob
import json
import math
import os
import shutil
import subprocess
import sys
import time

import numpy as np

BIN = '/data/SETI/bin'
ROOT = os.environ.get('P90R7_ROOT', '/data/SETI/p90_r7')
PLAN = f'{ROOT}/plan.json'
CLAIMS = f'{ROOT}/claims'
OUT = f'{ROOT}/out'
WORK = f'{ROOT}/work'
LOGS = f'{ROOT}/logs'
INJREC = f'{ROOT}/injrec'          # every deposition record, retained
KEEPMS = f'{ROOT}/keepms'          # one worked example per class, retained

# ------------------------------------------------------------------ criterion
# referee_r6/LOCALISATION_CRITERION.md, commit edfcc0d3d7db, 2026-09-25T06:59:24Z.
# Do not change these. If they are ever changed the campaign is no longer a
# measurement of the committed criterion and must not be reported as one.
LOC_RE_MIN = 4.0
LOC_IM_MAX = 3.0
LOC_MUST_BEAT_CONTROLS = True
SNR_THRESH = 5.0                   # the survey's own trigger, 5 sigma

# Amplitude ladder, in units of each window's own 5-sigma trigger flux, so
# windows of wildly different depth contribute to one curve. Steps of 0.5 in
# 1.0-4.0 because that is where the round-4 campaign found the 90 per cent
# point of the trigger (3.0 Class A, 4.1 Class B) and the localisation stage
# can only move it upwards. The last rung is a positive control, not a
# measurement point.
# The amplitude ladder.  Overridable per LANE (never for `collect`, which must
# keep the full default so that len(rungs) still classifies a complete unit)
# because DECISIONS_R8 D1a sanctions dropping the 5.0 and 6.0 rungs for units
# started late: they lie ABOVE the measured 90 per cent point and only shape
# the plateau, whereas 1.0-4.0 bracket it and the 20x positive control is not
# droppable at all.  A unit run this way reports 9 rungs and is scored as
# 'partial', which is exactly the audit trail that reduction needs.
LADDER = ([float(x) for x in os.environ['P90R7_LADDER'].split(',')]
          if os.environ.get('P90R7_LADDER') else
          [1.0, 1.5, 2.0, 2.5, 3.0, 3.5, 4.0, 5.0, 6.0, 8.0])
POSCTRL = 20.0
NTONE = int(os.environ.get('P90R7_NTONE', 24))
NPROC = int(os.environ.get('P90R7_NPROC', 8))
TOL_CHAN = int(os.environ.get('P90R7_TOL_CHAN', 4))
DISK_FLOOR_GB = float(os.environ.get('P90R7_DISK_FLOOR_GB', 60))
BASE_SEED = 701000
ARCSEC = math.pi / 180.0 / 3600.0
KEEP_MS_TAGS = set(x for x in os.environ.get('P90R7_KEEP_MS_TAGS', '').split(',')
                   if x)


def free_gb(path='/data'):
    s = os.statvfs(path)
    return s.f_bavail * s.f_frsize / 1e9


def wait_for_disk(tag, need=DISK_FLOOR_GB):
    waited = 0
    while free_gb() < need:
        if waited % 300 == 0:
            print(f'[{tag}] waiting for disk: {free_gb():.0f} GB free, '
                  f'floor {need:.0f} GB', flush=True)
        time.sleep(30)
        waited += 30


def run(cmd, env, logpath, timeout=14400):
    with open(logpath, 'a') as fh:
        fh.write('\n===== %s %s =====\n'
                 % (' '.join(cmd), time.strftime('%FT%TZ', time.gmtime())))
        fh.flush()
        p = subprocess.Popen(cmd, env=env, stdout=fh, stderr=subprocess.STDOUT)
        try:
            return p.wait(timeout=timeout)
        except subprocess.TimeoutExpired:
            p.kill()
            return 124


# --------------------------------------------------------------------- plan
def _astrometry():
    astro = {}
    for f in glob.glob('/data/SETI/mine2026/lane_*/worklist.json'):
        try:
            for x in json.load(open(f)):
                if 'pmra' in x:
                    astro.setdefault(x['eb'], x)
        except Exception:
            continue
    for f in ('/data/SETI/mine2026/aca_worklist.json',
              '/data/SETI/mine2026/worklist_mine2026.json',
              '/data/SETI/mine2026/visfit_worklist_r6.json'):
        if os.path.exists(f):
            try:
                for x in json.load(open(f)):
                    if 'pmra' in x:
                        astro.setdefault(x['eb'], x)
            except Exception:
                continue
    return astro


def _rows_per_spw(ms):
    """Number of data rows carried by each spectral window.

    SPECTRAL_WINDOW keeps every window the original observation defined even
    after a split has thrown most of them away, so a window can be listed with
    the right channel count and width and still hold no data at all: four
    windows of one retained block were planned that way and every one of them
    aborted with MSSelectionNullSelection. A window is only real if rows point
    at it."""
    from casatools import table
    tb = table()
    tb.open(ms + '/DATA_DESCRIPTION')
    dd2spw = np.asarray(tb.getcol('SPECTRAL_WINDOW_ID'), int)
    tb.close()
    tb.open(ms)
    ddc = np.asarray(tb.getcol('DATA_DESC_ID'), int)
    tb.close()
    n = {}
    for d in np.unique(ddc):
        if 0 <= d < dd2spw.size:
            n[int(dd2spw[d])] = n.get(int(dd2spw[d]), 0) + int((ddc == d).sum())
    return n


def _spws_from_ms(ms):
    """Science windows read from the measurement set itself, for blocks whose
    spw_list.json did not survive. The filter is the one the survey's own
    window list implies: at least 64 channels and a channel width between
    30 kHz and 20 MHz, which admits every ALMA correlator mode the survey
    searched and excludes WVR and channel-average windows."""
    from casatools import table
    tb = table()
    tb.open(ms + '/SPECTRAL_WINDOW')
    out = []
    for i in range(tb.nrows()):
        cf = np.asarray(tb.getcell('CHAN_FREQ', i), float)
        cw = np.asarray(tb.getcell('CHAN_WIDTH', i), float)
        if cf.size < 64:
            continue
        w = float(abs(cw[0]))
        if not (3e4 <= w <= 2e7):
            continue
        out.append(dict(spw=int(i), n_chan=int(cf.size), chanwidth_Hz=w))
    tb.close()
    return out


def build_plan():
    astro = _astrometry()
    units, dishes = [], {}
    roots = ['/data/SETI/targets', '/data/SETI/vistest']
    seen_eb = set()
    for root in roots:
        for ms in sorted(glob.glob(f'{root}/*/products/*target.ms')):
            tdir = ms.split('/products/')[0]
            eb = os.path.basename(ms)[:-len('_target.ms')]
            if eb in seen_eb:
                print(f'SKIP {eb} at {root}: same block already planned')
                continue
            a = astro.get(eb)
            if a is None:
                print(f'SKIP {eb}: no astrometry in any worklist')
                continue
            spwf = f'{tdir}/logs/spw_list.json'
            if os.path.exists(spwf):
                spws = [e for e in json.load(open(spwf)).get('spw_list', [])
                        if e.get('eb') == eb]
                src = 'spw_list.json'
            else:
                spws = _spws_from_ms(ms)
                src = 'measurement set'
            if not spws:
                print(f'SKIP {eb}: no science windows')
                continue
            nrows = _rows_per_spw(ms)
            keep = []
            for e in spws:
                if nrows.get(int(e['spw']), 0) < 1:
                    print(f'SKIP {eb} spw{e["spw"]}: the window is declared but '
                          f'carries no rows in the retained measurement set')
                    continue
                keep.append(e)
            spws = keep
            if not spws:
                print(f'SKIP {eb}: no window carries rows')
                continue
            from casatools import table
            tb = table()
            tb.open(ms + '/ANTENNA')
            dish = float(np.median(np.asarray(tb.getcol('DISH_DIAMETER'), float)))
            tb.close()
            size = int(subprocess.run(['du', '-sb', ms], capture_output=True,
                                      text=True).stdout.split()[0])
            nch_tot = sum(int(e.get('n_chan') or 0) for e in spws) or 1
            seen_eb.add(eb)
            dishes[eb] = dish
            for e in spws:
                # Windows the survey itself could not search: the extractor
                # aborts when the nearest field phase centre is more than
                # twice the primary beam from the star. Skipping them here
                # rather than spending a split and an extract rediscovering it.
                olog = f'{tdir}/logs/extract_spw{e["spw"]}.log'
                if os.path.exists(olog):
                    txt = open(olog, errors='replace').read()
                    if 'from the ALMA phase centre' in txt:
                        print(f'SKIP {eb} spw{e["spw"]}: star off the observed '
                              f'field (the survey extract aborted here too)')
                        continue
                cw = float(e.get('chanwidth_Hz') or 0)
                units.append(dict(
                    tag=f'{eb}_spw{e["spw"]}', eb=eb, spw=int(e['spw']),
                    target_ms=ms, target_dir=tdir, spw_source=src,
                    n_chan=int(e.get('n_chan') or 0), chanwidth_Hz=cw,
                    res_class=('A' if cw < 5e6 else 'B'),
                    array=('ACA 7 m' if dish < 10 else '12 m'),
                    dish_m=dish,
                    est_bytes=int(size * (int(e.get('n_chan') or 0) / nch_tot)),
                    star_name=a.get('star_name', a.get('base_name', 'target')),
                    ra=float(a['ra']), dec=float(a['dec']),
                    pmra=float(a['pmra']), pmdec=float(a['pmdec']),
                    parallax=float(a['parallax']),
                    parallax_err=float(a.get('parallax_err') or 0.001),
                    drift_coeff=float(a.get('drift_coeff') or 12.0)))
    units.sort(key=lambda u: u['est_bytes'])
    os.makedirs(ROOT, exist_ok=True)
    json.dump(units, open(PLAN, 'w'), indent=1)
    na = sum(1 for u in units if u['res_class'] == 'A')
    print(f'{len(units)} units ({na} class A, {len(units) - na} class B) from '
          f'{len({u["eb"] for u in units})} blocks; '
          f'{sum(u["est_bytes"] for u in units) / 1e9:.0f} GB of split MS; '
          f'{len(units) * (len(LADDER) + 2)} pipeline passes')
    for k in ('array',):
        vals = {}
        for u in units:
            vals.setdefault(u[k], 0)
            vals[u[k]] += 1
        print(' ', k, vals)
    return units


# ------------------------------------------------------------------ scoring
def score_pass(npz_path, inj, result, tol_chan=TOL_CHAN):
    """Score one pass, tone by tone, IN FREQUENCY.

    Channel INDEX is not a safe key. The search trims a fixed 4 % of each spw
    edge and then extends that trim adaptively until it reaches a channel with
    >50 % weighted integrations, and saves the TRIMMED frequency axis, so the
    array it writes is re-indexed relative to the measurement set the
    injection was written into. Matching on frequency is immune to that, and
    also tells us when a tone fell in the trimmed-away band and is not
    testable at all.

    The search de-drifts to the first integration it RETAINS. If it dropped
    leading integrations the recovered frequency is offset by the tone's drift
    times that time difference; the injector records the window's time base so
    that offset is bounded rather than guessed.
    """
    z = np.load(npz_path, allow_pickle=True)
    star = np.asarray(z['best_src'])[0]
    bdrift = np.asarray(z['best_drift'])[0]
    ctrl = np.asarray(z['ctrl_max'], dtype=float)
    freqs = np.asarray(z['freqs'], dtype=float)
    df = abs(float(freqs[1] - freqs[0]))
    ctrl_top = float(ctrl.max())
    n_drop = max(0, int(inj.get('n_times', 0)) - int(result.get('n_int', 0)))
    dt_bound = n_drop * float(inj.get('median_dt_s', 0.0))
    rows, n_outside = [], 0
    for j, t in enumerate(inj['tones']):
        f0 = float(t['freq_GHz']) * 1e9
        tol_hz = tol_chan * df + abs(float(t['drift_Hz_s'])) * dt_bound
        near = np.nonzero(np.abs(freqs - f0) <= tol_hz)[0]
        if near.size == 0 or not np.isfinite(star[near]).any():
            n_outside += 1          # trimmed away: untestable, not a failure
            continue
        k = int(near[int(np.nanargmax(star[near]))])
        snr = float(star[k])
        rows.append(dict(
            i_tone=j, chan_inj=int(t['chan']), chan_found=k, snr=snr,
            trig=bool(snr >= SNR_THRESH),
            outranks_all=bool(snr > ctrl_top),   # the retired rank gate, kept
            drift_inj=float(t['drift_Hz_s']),    # as a released comparison
            drift_found=float(bdrift[k]),
            subchan=float(t['subchan']),
            df_found_Hz=float(freqs[k] - f0),
            tol_Hz=float(tol_hz),
            freq_GHz=float(freqs[k] / 1e9),
            freq_inj_GHz=float(t['freq_GHz'])))
    return dict(ctrl_top=ctrl_top,
                ctrl_p50=float(np.percentile(ctrl, 50)),
                n_chan_searched=int(freqs.size),
                n_int=int(result.get('n_int', 0)),
                n_dropped_int=n_drop, dt_bound_s=dt_bound,
                n_outside_trim=n_outside,
                star_band_max=float(np.nanmax(star)), tones=rows)


def localised(fit):
    """The committed criterion, and only it."""
    if not fit or fit.get('status') != 'ok':
        return False
    st = fit.get('star') or {}
    re_s, im_s = st.get('snr_re'), st.get('snr_im')
    if re_s is None or im_s is None:
        return False
    if not (re_s >= LOC_RE_MIN):
        return False
    if not (abs(im_s) < LOC_IM_MAX):
        return False
    if LOC_MUST_BEAT_CONTROLS:
        cs = [c for c in (fit.get('ctrl_pos_max'), fit.get('ctrl_freq_max'))
              if c is not None]
        if cs and not (re_s > max(cs)):
            return False
    return True


def annotate(tones, fits, fits_r6, amp_Jy):
    """Attach both fits to each tone and apply the criterion to each.

    `localised` is the corrected reference epoch and is what the campaign
    reports. `localised_r6committed` is the epoch visfit_r6.py used, kept so the
    paper can state the completeness of the estimator that actually
    dispositioned the round-6 candidate list."""
    for t in tones:
        fit = fits.get(t['i_tone']) if t['trig'] else None
        f6 = fits_r6.get(t['i_tone']) if t['trig'] else None
        t['fit_status'] = (fit or {}).get('status') if t['trig'] \
            else 'not_fitted_no_trigger'
        if fit and fit.get('status') == 'ok':
            st = fit['star']
            t.update(snr_re=st['snr_re'], snr_im=st['snr_im'],
                     re_Jy=st['re'], sig_re_Jy=st['sig_re'],
                     n_vis=st['n_vis'],
                     re_over_amp=(st['re'] / amp_Jy) if amp_Jy else None,
                     ctrl_pos_max=fit.get('ctrl_pos_max'),
                     ctrl_freq_max=fit.get('ctrl_freq_max'),
                     n_freq_ctrl=len(fit.get('freq_controls') or []))
        if f6 and f6.get('status') == 'ok':
            st6 = f6['star']
            t.update(snr_re_r6=st6['snr_re'], snr_im_r6=st6['snr_im'],
                     re_over_amp_r6=(st6['re'] / amp_Jy) if amp_Jy else None)
        t['localised'] = bool(localised(fit)) if t['trig'] else False
        t['localised_r6committed'] = bool(localised(f6)) if t['trig'] else False
        t['recovered_trig'] = bool(t['trig'])
        t['recovered_full'] = bool(t['trig'] and t['localised'])
        t['recovered_full_r6'] = bool(t['trig'] and t['localised_r6committed'])


def extraction_t0(wdir, eb, sfx):
    """The first integration the EXTRACTION retained, for this pass.

    This is the epoch the search's reported frequency refers to: the search
    de-drifts with `dt = times - times[0]` over the integrations it keeps. It is
    NOT min(TIME) of the measurement set, because the fit loads rows the
    extraction discarded -- a difference that reaches 6.5 channels on one round-6
    block in four, as large as that crossing's whole displacement
    (referee_r7/EPOCH_DECIDED.md). Returns None if the product is absent, in
    which case the fit falls back to min(TIME) and the residual is bounded by
    the dropped-integration count the scorer already records."""
    for cand in (f'{wdir}/products/{eb}{sfx}_srcspec.npz',
                 f'{wdir}/products/{eb}{sfx}_waterfall.npz'):
        if not os.path.exists(cand):
            continue
        try:
            with np.load(cand, allow_pickle=True) as z:
                if 'times' not in z.files:
                    continue
                t = np.asarray(z['times'], float)
                if t.size:
                    return float(np.min(t))
        except Exception:
            continue
    return None


def fit_triggered(wdir, rung_label, pms, tones, pb_arcsec, l_as, m_as, inj,
                  env, log, t_ref=None):
    """Run the visibility fit at the found cell of every tone that crossed the
    threshold. Tones that did not cross are never fitted: in the chain being
    measured, localisation is applied to threshold crossings.

    The fit is run TWICE, under both drift reference epochs:

      'explicit' -- the first integration the EXTRACTION retained for this very
                  pass, read from its own product. This is the epoch the
                  search's reported frequency refers to. min(TIME) of the rows
                  the fit loads is NOT that epoch when the extraction dropped
                  leading integrations, and the residual reaches 2.2 channels
                  within this campaign and 6.5 channels on a round-6 science
                  block (referee_r7/EPOCH_DECIDED.md);
      'median' -- median(TIME), which is what visfit_r6.py does and therefore
                  what dispositioned the round-6 candidate list.

    Both are reported. The difference is not cosmetic: on a 2118 s Band 8
    window the 'median' convention recovers nothing at all from a carrier
    drifting fast enough to move three channels in half the observation, while
    'first' recovers the full deposited amplitude.

    Every tone frequency of the pass is passed as `avoid_GHz`, so an off-event
    control frequency is never placed on another injected tone. In the survey
    a window carries at most one carrier and the controls are event-free by
    construction; without this the injection pass breaks that property and the
    star fails criterion 3 for a reason the data cannot produce."""
    want = [t for t in tones if t['trig']]
    if not want:
        return {}, {}, 0.0
    tag = os.path.basename(wdir).rpartition('.')[0]
    evd = f'{wdir}/vf_{rung_label}_events.json'
    drd = f'{wdir}/vf_{rung_label}_drift.json'
    events, drift, keyof = [], {}, {}
    avoid = [float(t['freq_GHz']) for t in inj['tones']]
    tol_ghz = 8.0 * abs(float(inj['df_Hz'])) / 1e9
    for t in want:
        et = 't%03d' % t['i_tone']
        ek = f'{tag}|{rung_label}|{et}'
        events.append(dict(tag=et, eb=ek, ms=pms,
                           freq_GHz=t['freq_GHz'], theta_pb=pb_arcsec,
                           l0_arcsec=l_as, m0_arcsec=m_as,
                           avoid_GHz=avoid, avoid_tol_GHz=tol_ghz,
                           **({} if t_ref is None
                              else dict(t_ref_mjds=float(t_ref)))))
        drift[ek] = t['drift_found']
        # the fit keys its output '<tag>|<eb>'; build that here rather than
        # re-deriving it downstream, where a format change would silently
        # turn every fit into a miss and every tone into a non-detection
        keyof[t['i_tone']] = '%s|%s' % (et, ek)
    json.dump(events, open(evd, 'w'))
    json.dump(drift, open(drd, 'w'))
    out = {}
    t0 = time.time()
    for mode in ('explicit', 'median'):
        outd = f'{wdir}/vf_{rung_label}_fit_{mode}.json'
        rc = run(['python3', f'{BIN}/visfit_r7.py'],
                 dict(env, VF_EVENTS=evd, VF_DRIFT=drd, VF_OUT=outd,
                      VF_TREF=mode), log, timeout=21600)
        if rc != 0 or not os.path.exists(outd):
            return {'__rc__': rc}, {'__rc__': rc}, time.time() - t0
        fits = json.load(open(outd))
        missing = [i for i, k in keyof.items() if k not in fits]
        if missing:
            raise RuntimeError('visfit output is missing %d of %d requested '
                               'keys (first %r); the key convention has drifted'
                               % (len(missing), len(keyof), keyof[missing[0]]))
        out[mode] = {i: fits[k] for i, k in keyof.items()}
    return out['explicit'], out['median'], time.time() - t0


# ---------------------------------------------------------------- one unit
def do_unit(u):
    tag = u['tag']
    # The working directory is keyed by the LANE as well as the unit. Two lanes
    # must never share one: do_unit begins by deleting it, so if they did, each
    # would destroy the other's products and neither would ever finish. That
    # happened once -- an orphan-claim sweep run while lanes were alive released
    # live claims, a second lane took each unit, and the campaign made zero
    # progress for an hour while looking perfectly healthy. A claim is not
    # enough on its own; the directory must be private.
    wdir = f'{WORK}/{tag}.{os.getpid()}'
    shutil.rmtree(wdir, ignore_errors=True)
    os.makedirs(f'{wdir}/products', exist_ok=True)
    os.makedirs(f'{wdir}/logs', exist_ok=True)
    os.makedirs(f'{INJREC}/{tag}', exist_ok=True)
    log = f'{LOGS}/{tag}.log'
    t0 = time.time()
    rec = dict(unit=u, started=time.strftime('%FT%TZ', time.gmtime()))

    env = dict(os.environ)
    env.update(SETI_TARGET_DIR=wdir, SETI_STAR_NAME=u['star_name'],
               SETI_STAR_RA=str(u['ra']), SETI_STAR_DEC=str(u['dec']),
               SETI_STAR_PMRA=str(u['pmra']), SETI_STAR_PMDEC=str(u['pmdec']),
               SETI_STAR_PARALLAX=str(u['parallax']),
               SETI_STAR_PARALLAX_ERR=str(u['parallax_err']),
               SETI_DRIFT_COEFF=str(u['drift_coeff']),
               CASASITECONFIG='/home/fetch-agi/.casa/config.py',
               OMP_NUM_THREADS='1')

    # ---- 0. split the window out once
    wait_for_disk(tag)
    clean = f'{wdir}/clean.ms'
    rc = run(['python3', '-c',
              'import sys, os; os.environ.setdefault("CASASITECONFIG", '
              '"/home/fetch-agi/.casa/config.py");'
              'from casatasks import split;'
              'split(vis=sys.argv[1], outputvis=sys.argv[2], spw=sys.argv[3],'
              ' datacolumn="data", keepflags=False)',
              u['target_ms'], clean, str(u['spw'])], env, log, timeout=10800)
    if rc != 0 or not os.path.isdir(clean):
        rec.update(status='failed_split', rc=rc)
        shutil.rmtree(wdir, ignore_errors=True)
        return rec

    # ---- 1. clean pass: threshold, drift bound, beam, stellar position
    sfx = '_r7base'
    rc = run(['python3', f'{BIN}/seti_extract_generic.py', u['eb'], str(NPROC)],
             dict(env, SETI_MS=clean, SETI_SFX=sfx), log)
    wf = f'{wdir}/products/{u["eb"]}{sfx}_waterfall.npz'
    if rc != 0 or not os.path.exists(wf):
        rec.update(status='failed_extract_base', rc=rc)
        shutil.rmtree(wdir, ignore_errors=True)
        return rec
    with np.load(wf, allow_pickle=True) as z:      # read BEFORE the search
        l_star = float(z['l_star'])                # consumes and deletes it
        m_star = float(z['m_star'])
    rc = run(['python3', f'{BIN}/seti_drift_search_generic.py', u['eb'],
              str(NPROC)], dict(env, SETI_MS=clean, SETI_SFX=sfx), log)
    basejsn = f'{wdir}/products/{u["eb"]}{sfx}_result.json'
    if rc != 0 or not os.path.exists(basejsn):
        rec.update(status='failed_search_base', rc=rc)
        shutil.rmtree(wdir, ignore_errors=True)
        return rec
    base = json.load(open(basejsn))
    s_trig = float(base['S_min_measured_Jy'])
    drift_max = float(base['drift_max_Hz_s'])
    pb = float(base.get('primary_beam_fwhm_arcsec') or 0.0)
    if pb <= 0:
        rec.update(status='no_primary_beam')
        shutil.rmtree(wdir, ignore_errors=True)
        return rec
    l_as, m_as = l_star / ARCSEC, m_star / ARCSEC
    base_t_ref = extraction_t0(wdir, u['eb'], sfx)
    rec.update(baseline=base, l_star=l_star, m_star=m_star,
               l_arcsec=l_as, m_arcsec=m_as, pb_fwhm_arcsec=pb,
               S_trig_Jy=s_trig, drift_max_Hz_s=drift_max,
               star_offset_arcsec=float(np.hypot(l_as, m_as)),
               base_t_ref_mjds=base_t_ref)

    # ---- 2. the ladder. The split MS has exactly one window, id 0.
    rungs = []
    for i, f in enumerate(LADDER + [POSCTRL]):
        wait_for_disk(tag)
        pms = f'{wdir}/pass.ms'
        shutil.rmtree(pms, ignore_errors=True)
        if subprocess.run(['cp', '-a', clean, pms]).returncode != 0:
            rec.update(status='failed_copy', rung=i)
            break
        ijsn = f'{INJREC}/{tag}/inj_{i}.json'
        ienv = dict(env, INJ_L=repr(l_star), INJ_M=repr(m_star),
                    INJ_AMP_JY=repr(f * s_trig),
                    INJ_DRIFT_MAX=repr(drift_max))
        rc = run(['python3', f'{BIN}/inject_vis_v401.py', pms, '0', ijsn,
                  str(NTONE), str(BASE_SEED + i)], ienv, log, timeout=7200)
        if rc != 0 or not os.path.exists(ijsn):
            rec.update(status='failed_inject', rung=i, rc=rc)
            break
        inj = json.load(open(ijsn))
        psfx = f'_r7p{i}'
        penv = dict(env, SETI_MS=pms, SETI_SFX=psfx)
        rc = run(['python3', f'{BIN}/seti_extract_generic.py', u['eb'],
                  str(NPROC)], penv, log)
        if rc == 0:
            rc = run(['python3', f'{BIN}/seti_drift_search_generic.py',
                      u['eb'], str(NPROC)], penv, log)
        snpz = f'{wdir}/products/{u["eb"]}{psfx}_search.npz'
        if rc != 0 or not os.path.exists(snpz):
            shutil.rmtree(pms, ignore_errors=True)
            rec.update(status='failed_pass', rung=i, rc=rc)
            break
        pres = json.load(open(f'{wdir}/products/{u["eb"]}{psfx}_result.json'))
        sc = score_pass(snpz, inj, pres)

        # ---- the second stage, on this pass's own injected measurement set
        t_ref = extraction_t0(wdir, u['eb'], psfx)
        fits, fits_r6, vfs = fit_triggered(wdir, f'p{i}', pms, sc['tones'], pb,
                                           l_as, m_as, inj, env, log, t_ref)
        sc_t_ref = t_ref
        vf_rc = fits.pop('__rc__', 0) if isinstance(fits, dict) else 0
        fits_r6.pop('__rc__', None)
        annotate(sc['tones'], fits, fits_r6, f * s_trig)

        if tag in KEEP_MS_TAGS and f == POSCTRL:
            os.makedirs(KEEPMS, exist_ok=True)
            subprocess.run(['cp', '-a', pms, f'{KEEPMS}/{tag}_rung{i}.ms'])
        shutil.rmtree(pms, ignore_errors=True)
        os.remove(snpz)
        for junk in (f'{wdir}/products/{u["eb"]}{psfx}_waterfall.npz',
                     f'{wdir}/products/{u["eb"]}{psfx}_srcspec.npz'):
            if os.path.exists(junk):
                os.remove(junk)   # t_ref already read; these are large

        sc.update(rung=i, amp_over_trig=f, amp_Jy=f * s_trig,
                  t_ref_mjds=sc_t_ref,
                  t_ref_source=('extraction' if sc_t_ref is not None
                                else 'min(TIME) fallback'),
                  is_positive_control=(f == POSCTRL and i == len(LADDER)),
                  visfit_s=round(vfs, 1), visfit_rc=vf_rc, result=pres)
        rungs.append(sc)
        n = len(sc['tones'])
        kt = sum(t['recovered_trig'] for t in sc['tones'])
        kf = sum(t['recovered_full'] for t in sc['tones'])
        print(f'[{tag}] rung {i} ({f:.2f} x S_trig = {f * s_trig * 1e3:.3f} mJy): '
              f'trig {kt}/{n}, trig+loc {kf}/{n}  '
              f'(fit {vfs:.0f} s, total {time.time() - t0:.0f} s)', flush=True)
    rec['rungs'] = rungs

    # ---- 3. the clean pass scored at every rung's cells: the null
    cnpz = f'{wdir}/products/{u["eb"]}{sfx}_search.npz'
    null = []
    if os.path.exists(cnpz):
        for i in range(len(rungs)):
            ijsn = f'{INJREC}/{tag}/inj_{i}.json'
            if not os.path.exists(ijsn):
                continue
            inj_i = json.load(open(ijsn))
            s = score_pass(cnpz, inj_i, base)
            # any null cell that crosses the threshold is fitted too, so the
            # null is measured through BOTH stages, not just the first
            fits, fits_r6, vfs = fit_triggered(wdir, f'n{i}', clean, s['tones'],
                                               pb, l_as, m_as, inj_i, env, log,
                                               base_t_ref)
            fits.pop('__rc__', None)
            fits_r6.pop('__rc__', None)
            annotate(s['tones'], fits, fits_r6, float(inj_i['amp_Jy']))
            s['rung'] = i
            s['visfit_s'] = round(vfs, 1)
            null.append(s)
    rec['null'] = null

    if 'status' not in rec:
        rec['status'] = 'ok' if len(rungs) == len(LADDER) + 1 else 'partial'
    rec['runtime_s'] = round(time.time() - t0, 1)
    rec['finished'] = time.strftime('%FT%TZ', time.gmtime())
    shutil.rmtree(wdir, ignore_errors=True)
    return rec


# -------------------------------------------------------------------- lanes
def worker():
    units = json.load(open(PLAN))
    # A lane may be restricted to named units, or told to take the largest
    # first. The plan is ordered smallest-first so that lanes fill up on cheap
    # units and peak disk stays low at the start; but the one unit that sets
    # the campaign's critical path is the largest, so it has to be started at
    # the beginning rather than picked up last.
    only = set(x for x in os.environ.get('P90R7_ONLY', '').split(',') if x)
    if only:
        units = [u for u in units if u['tag'] in only]
    if os.environ.get('P90R7_REVERSE'):
        units = units[::-1]
    for d in (CLAIMS, OUT, WORK, LOGS, INJREC):
        os.makedirs(d, exist_ok=True)
    n = 0
    for u in units:
        if os.path.exists(f'{OUT}/{u["tag"]}.json'):
            continue
        try:
            os.mkdir(f'{CLAIMS}/{u["tag"]}')          # atomic claim
        except FileExistsError:
            continue
        # record the owner, so a sweep can tell a live claim from an orphan
        with open(f'{CLAIMS}/{u["tag"]}/owner', 'w') as fh:
            fh.write('%d %s\n' % (os.getpid(), time.strftime('%FT%TZ',
                                                             time.gmtime())))
        print(f'=== claimed {u["tag"]} ({u["est_bytes"] / 1e9:.2f} GB est, '
              f'class {u["res_class"]}, {u["array"]})', flush=True)
        try:
            rec = do_unit(u)
        except Exception as e:
            import traceback
            rec = dict(unit=u, status='exception', error=repr(e),
                       traceback=traceback.format_exc())
            shutil.rmtree(f'{WORK}/{u["tag"]}.{os.getpid()}',
                          ignore_errors=True)
        json.dump(rec, open(f'{OUT}/{u["tag"]}.json', 'w'), indent=1)
        n += 1
        print(f'=== {u["tag"]}: {rec.get("status")} '
              f'({rec.get("runtime_s", 0):.0f} s)', flush=True)
    print(f'lane done, {n} units')


# ------------------------------------------------------------------ collect
def band_of(ghz):
    for lo, hi, b in ((84, 116, '3'), (125, 163, '4'), (163, 211, '5'),
                      (211, 275, '6'), (275, 373, '7'), (385, 500, '8'),
                      (602, 720, '9'), (787, 950, '10')):
        if lo <= ghz <= hi:
            return b
    return '?'


def collect():
    recs = [json.load(open(f)) for f in sorted(glob.glob(f'{OUT}/*.json'))]
    ok = [r for r in recs if r.get('status') in ('ok', 'partial')
          and r.get('rungs')]
    bad = [r for r in recs if r not in ok]

    # positive control first: a unit that cannot recover a 20-sigma carrier
    # at its own star position is not evidence about anything else
    good, failed_pc = [], []
    for r in ok:
        pc = [g for g in r['rungs'] if g.get('is_positive_control')]
        if not pc:
            failed_pc.append((r['unit']['tag'], 'no positive control rung'))
            continue
        ts = pc[0]['tones']
        ft = sum(t['recovered_trig'] for t in ts) / max(1, len(ts))
        ff = sum(t['recovered_full'] for t in ts) / max(1, len(ts))
        if ft < 0.95:
            failed_pc.append((r['unit']['tag'],
                              'positive control trigger %.2f' % ft))
        elif ff < 0.95:
            # a unit whose 20-sigma carrier triggers but will not localise is
            # not evidence about the localisation stage either: the sign of the
            # geometric phase cannot be tested by a source at the phase centre,
            # and this is where such an error would show
            failed_pc.append((r['unit']['tag'],
                              'positive control localisation %.2f' % ff))
        else:
            r['_pc_trig'], r['_pc_full'] = ft, ff
            good.append(r)

    def curve_of(units, key):
        curve = {}
        for r in units:
            for g in r['rungs']:
                if g.get('is_positive_control'):
                    continue
                a = g['amp_over_trig']
                c = curve.setdefault(a, [0, 0])
                c[0] += sum(t[key] for t in g['tones'])
                c[1] += len(g['tones'])
        return curve

    def p90_of(curve):
        xs = sorted(curve)
        ys = [curve[a][0] / curve[a][1] if curve[a][1] else 0.0 for a in xs]
        for j in range(1, len(xs)):
            if ys[j - 1] < 0.9 <= ys[j]:
                w = (0.9 - ys[j - 1]) / (ys[j] - ys[j - 1])
                return xs[j - 1] + w * (xs[j] - xs[j - 1])
        return None       # never reaches 0.9 on the ladder: a bound, not a value

    def boot_ci(units, key, nboot=2000, seed=20260925):
        # cluster bootstrap over UNITS, not tones: tones within one window
        # share its noise realisation, its beam and its controls, so a
        # tone-level interval would be far too narrow
        rng = np.random.default_rng(seed)
        vals = []
        for _ in range(nboot):
            samp = [units[i] for i in rng.integers(0, len(units), len(units))]
            v = p90_of(curve_of(samp, key))
            if v is not None:
                vals.append(v)
        if len(vals) < 50:
            return None, 1.0 - len(vals) / nboot
        return ([float(np.percentile(vals, 16)),
                 float(np.percentile(vals, 84))], 1.0 - len(vals) / nboot)

    def per_unit_p90(units, key):
        """P90 of each configuration on its own: the transfer spread."""
        out = []
        for r in units:
            v = p90_of(curve_of([r], key))
            out.append((r['unit']['tag'], v))
        return out

    def summarise(units, label):
        if not units:
            return None
        ct = curve_of(units, 'recovered_trig')
        cf = curve_of(units, 'recovered_full')
        c6 = curve_of(units, 'recovered_full_r6')
        xs = sorted(ct)
        if not xs:
            return None
        p90t, p90f, p906 = p90_of(ct), p90_of(cf), p90_of(c6)
        cit, undt = boot_ci(units, 'recovered_trig')
        cif, undf = boot_ci(units, 'recovered_full')
        ci6, und6 = boot_ci(units, 'recovered_full_r6')
        nullkt = nullkf = nulln = 0
        nullby = {}
        for r in units:
            for s in r.get('null', []):
                nullkt += sum(t['recovered_trig'] for t in s['tones'])
                k = sum(t['recovered_full'] for t in s['tones'])
                nullkf += k
                nulln += len(s['tones'])
                if k:
                    # Where a null cell fires, say where. A clean pass can carry
                    # real emission: every null recovery in this campaign is one
                    # CO(2-1) line in one window, not a property of the method,
                    # and that is only visible if the frequencies are reported.
                    d = nullby.setdefault(r['unit']['tag'],
                                          dict(n=0, freq_GHz=[],
                                               chanwidth_Hz=r['unit']['chanwidth_Hz'],
                                               res_class=r['unit']['res_class']))
                    d['n'] += k
                    d['freq_GHz'] += [round(t['freq_GHz'], 6)
                                      for t in s['tones']
                                      if t['recovered_full']]
        pu_t = [v for _, v in per_unit_p90(units, 'recovered_trig')
                if v is not None]
        pu_f = [v for _, v in per_unit_p90(units, 'recovered_full')
                if v is not None]
        pc = [g for r in units for g in r['rungs']
              if g.get('is_positive_control')]
        nfit = sum(1 for r in units for g in r['rungs'] for t in g['tones']
                   if t.get('fit_status') == 'ok')
        nfitfail = sum(1 for r in units for g in r['rungs'] for t in g['tones']
                       if t['trig'] and t.get('fit_status') not in (None, 'ok'))
        return dict(
            stratum=label, n_units=len(units), n_tones=sum(ct[a][1] for a in xs),
            n_blocks=len({r['unit']['eb'] for r in units}),
            arrays=sorted({r['unit']['array'] for r in units}),
            bands=sorted({band_of(0.5 * (r['baseline']['freq_lo_GHz']
                                         + r['baseline']['freq_hi_GHz']))
                          for r in units}),
            ladder=[dict(amp_over_trig=a,
                         n=ct[a][1],
                         frac_trigger=ct[a][0] / ct[a][1],
                         frac_trigger_and_localised=cf[a][0] / cf[a][1],
                         frac_trigger_and_localised_r6committed=(
                             c6[a][0] / c6[a][1]),
                         n_trigger=ct[a][0], n_full=cf[a][0],
                         n_full_r6=c6[a][0]) for a in xs],
            P90_over_trigger=p90t,
            P90_ci68=cit,
            P90_bootstrap_undefined_frac=undt,
            P90_loc_over_trigger=p90f,
            P90_loc_ci68=cif,
            P90_loc_bootstrap_undefined_frac=undf,
            P90_loc_r6committed_over_trigger=p906,
            P90_loc_r6committed_ci68=ci6,
            P90_loc_r6committed_bootstrap_undefined_frac=und6,
            median_re_over_amp_at_top_rung=float(np.median(
                [t['re_over_amp'] for r in units for g in r['rungs']
                 if g.get('is_positive_control') for t in g['tones']
                 if t.get('re_over_amp') is not None] or [float('nan')])),
            median_re_over_amp_at_top_rung_r6committed=float(np.median(
                [t['re_over_amp_r6'] for r in units for g in r['rungs']
                 if g.get('is_positive_control') for t in g['tones']
                 if t.get('re_over_amp_r6') is not None] or [float('nan')])),
            transfer_spread_trigger=dict(
                n_defined=len(pu_t), n_units=len(units),
                p16=float(np.percentile(pu_t, 16)) if pu_t else None,
                median=float(np.median(pu_t)) if pu_t else None,
                p84=float(np.percentile(pu_t, 84)) if pu_t else None,
                min=float(min(pu_t)) if pu_t else None,
                max=float(max(pu_t)) if pu_t else None),
            transfer_spread_loc=dict(
                n_defined=len(pu_f), n_units=len(units),
                p16=float(np.percentile(pu_f, 16)) if pu_f else None,
                median=float(np.median(pu_f)) if pu_f else None,
                p84=float(np.percentile(pu_f, 84)) if pu_f else None,
                min=float(min(pu_f)) if pu_f else None,
                max=float(max(pu_f)) if pu_f else None),
            per_unit_P90_trigger=dict(per_unit_p90(units, 'recovered_trig')),
            per_unit_P90_loc=dict(per_unit_p90(units, 'recovered_full')),
            ladder_top=max(xs),
            null_recovered=nullkt, null_recovered_localised=nullkf,
            null_n=nulln, null_recovered_by_unit=nullby,
            null_frac=(nullkt / nulln) if nulln else None,
            null_frac_localised=(nullkf / nulln) if nulln else None,
            positive_control_frac=(
                sum(t['recovered_trig'] for g in pc for t in g['tones'])
                / max(1, sum(len(g['tones']) for g in pc))),
            positive_control_frac_localised=(
                sum(t['recovered_full'] for g in pc for t in g['tones'])
                / max(1, sum(len(g['tones']) for g in pc))),
            positive_control_frac_localised_r6committed=(
                sum(t['recovered_full_r6'] for g in pc for t in g['tones'])
                / max(1, sum(len(g['tones']) for g in pc))),
            n_fits_ok=nfit, n_fits_failed=nfitfail,
            # the injected source leaks into the control ring through the
            # dirty beam, so the retired rank test gets harder as the signal
            # gets brighter. Reported, not hidden.
            rank_gate_frac_at_top_rung=(
                sum(t['outranks_all'] for g in pc for t in g['tones'])
                / max(1, sum(len(g['tones']) for g in pc))),
            ctrl_top_clean=float(np.median(
                [r['baseline']['control_peak_snr'] for r in units])),
            ctrl_top_at_top_rung=float(np.median([g['ctrl_top'] for g in pc]))
            if pc else None)

    strata = {'all': list(good)}
    for r in good:
        strata.setdefault('class %s' % r['unit']['res_class'], []).append(r)
        strata.setdefault(r['unit']['array'], []).append(r)
        b = band_of(0.5 * (r['baseline']['freq_lo_GHz']
                           + r['baseline']['freq_hi_GHz']))
        strata.setdefault('band %s' % b, []).append(r)
    out = dict(
        generated=time.strftime('%FT%TZ', time.gmtime()),
        chain='injected carrier -> threshold recovery (T>=5 at the injected '
              'cell) -> visibility-domain localisation',
        criterion=dict(
            source='referee_r6/LOCALISATION_CRITERION.md, commit edfcc0d3d7db, '
                   '2026-09-25T06:59:24Z, fixed before any of this was run',
            snr_threshold=SNR_THRESH, loc_re_min=LOC_RE_MIN,
            loc_abs_im_max=LOC_IM_MAX,
            loc_must_exceed_all_12_controls=LOC_MUST_BEAT_CONTROLS),
        estimator=dict(
            reported='drift track referenced to min(TIME), which is the epoch '
                     'seti_drift_search_generic.py de-drifts to (dt = times - '
                     'times[0]) and therefore the epoch its reported frequency '
                     'refers to',
            r6committed='drift track referenced to median(TIME), which is what '
                        'visfit_r6.py does and therefore what dispositioned '
                        'the round-6 candidate list; it is in error by '
                        'nudot x T_span / 2 and loses a fast-drifting carrier '
                        'in a fine window entirely',
            control_frequencies='moved off every injected tone of the pass, so '
                                'that they are event-free as they are by '
                                'construction in the survey, where a window '
                                'carries at most one carrier'),
        injector=dict(script='inject_vis_v401.py',
                      response='hann_lag_window_v401',
                      peak_fraction_centre=0.500, peak_fraction_edge=0.4244),
        ladder=LADDER, positive_control=POSCTRL, n_tone_requested=NTONE,
        n_units_total=len(recs), n_units_scored=len(good),
        n_units_failed=len(bad),
        failed=[dict(tag=r['unit']['tag'], status=r.get('status'),
                     rung=r.get('rung')) for r in bad],
        positive_control_failures=failed_pc,
        strata=[s for s in (summarise(v, k) for k, v in strata.items()) if s])
    top = next(s for s in out['strata'] if s['stratum'] == 'all')
    out['P90_over_trigger'] = top['P90_over_trigger']
    out['P90_loc_over_trigger'] = top['P90_loc_over_trigger']
    out['P90_loc_r6committed_over_trigger'] = \
        top['P90_loc_r6committed_over_trigger']
    out['n_tones_total'] = top['n_tones']
    # The null standard is the one fixed BEFORE any of this was run:
    # LOCALISATION_CRITERION.md sets a ceiling of 1 per cent per crossing on the
    # criterion's false-alarm rate. Requiring exactly zero would be a stricter
    # test invented after seeing the data, and would fail the campaign for
    # finding real emission -- which is what it found: every null recovery is
    # one CO(2-1) line in one window. Both the count and the rate are reported.
    out['null_ceiling_prefixed'] = 0.01
    out['null_frac_localised'] = top['null_frac_localised']
    out['null_ok'] = bool((top['null_frac_localised'] or 0.0) < 0.01)
    out['null_zero'] = bool(top['null_recovered_localised'] == 0)
    out['positive_control_ok'] = bool(top['positive_control_frac'] >= 0.95
                                      and top['positive_control_frac_localised']
                                      >= 0.95)
    out['campaign_valid'] = bool(out['null_ok'] and out['positive_control_ok'])
    os.makedirs(ROOT, exist_ok=True)
    json.dump(out, open(f'{ROOT}/p90_r7_result.json', 'w'), indent=1)

    def f(v, top_):
        return ('%.2f' % v) if v is not None else '>%.0f' % top_

    for s in out['strata']:
        print('%-14s %3d u %2d blk %6d tones | trig %s %s | trig+loc %s %s | '
              'r6cmt %s | null %d/%d (loc %d) | pc %.3f/%.3f/%.3f'
              % (s['stratum'], s['n_units'], s['n_blocks'], s['n_tones'],
                 f(s['P90_over_trigger'], s['ladder_top']),
                 ('[%.2f,%.2f]' % tuple(s['P90_ci68'])) if s['P90_ci68'] else '-',
                 f(s['P90_loc_over_trigger'], s['ladder_top']),
                 ('[%.2f,%.2f]' % tuple(s['P90_loc_ci68']))
                 if s['P90_loc_ci68'] else '-',
                 f(s['P90_loc_r6committed_over_trigger'], s['ladder_top']),
                 s['null_recovered'], s['null_n'],
                 s['null_recovered_localised'],
                 s['positive_control_frac'],
                 s['positive_control_frac_localised'],
                 s['positive_control_frac_localised_r6committed']))
    print('campaign_valid =', out['campaign_valid'],
          '(null_ok', out['null_ok'], ', positive_control_ok',
          out['positive_control_ok'], ')')
    return out


if __name__ == '__main__':
    mode = sys.argv[1] if len(sys.argv) > 1 else 'work'
    if mode == 'plan':
        build_plan()
    elif mode == 'work':
        worker()
    elif mode == 'collect':
        collect()
    else:
        raise SystemExit(__doc__)
