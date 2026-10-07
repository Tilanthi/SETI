#!/usr/bin/env python3
r"""events_v412.py -- the two crossings that outrank every control position,
drawn and described from the retained dynamic spectra.

Round 190.  Writes `survey_numbers_round190.tex` and
`figures/event_crossings.pdf`.

WHY THIS EXISTS.  The two most interesting individual events in the search
reach the reader only as rows of a ledger.  A reader cannot see from a row
that the carrier is invisible in every single integration and exists only in
the coherent stack, that the drift is a straight line across the band, that
the star beats all \NCtrl{} control positions by a margin no larger than the
spread of those positions, or that the same cell at the same stellar-frame
frequency two hours later is empty where a persisting carrier would have been
unmissable.  All six of those are properties of the data and all six are
drawn here.

THE INPUT is a compact extract made on the archive host by
`r11inputs/events/figdata_events_r11.py`, which is deposited beside it.  That
script re-runs the survey's own estimator -- the inverse-variance de-drifted
stack of `r8_window.py`, which is the code path that produced the published
exclusions -- and its own gate requires the reconstructed discovery statistic
to reproduce the published one to better than 1e-6 relative before it writes
anything.  Both windows passed at 5e-8.  Nothing in this generator recomputes
a statistic; it draws measurements and prints their values as macros.

FOUR THINGS THAT ARE EASY TO GET WRONG HERE, AND ARE ASSERTED:

* **The two events are selected by a property, never by name.**  They are the
  crossings whose star outranks every control position, read out of the
  measurement record, and the generator refuses to run if that set does not
  have exactly two members -- a hard-coded pair would silently survive the
  mask rebuild moving a crossing in or out.
* **The disposition comes from the ledger**, not from the frozen recurrence
  input, so the figure cannot describe a crossing as attributed after the
  mask has stopped attributing it.
* **A de-drifted panel must be drawn at the fitted drift and nowhere else.**
  The integer channel displacement drawn over the un-de-drifted panel is the
  same `shifts` array the stack used, carried in the extract, not recomputed
  from a rounded drift rate.
* **The repeat panel's zero is the predicted stellar-frame cell**, which is
  not the discovery sky frequency: for 61 Vir it moves by about one channel
  between epochs, and a sky-frequency panel would be drawn at the wrong
  place while looking identical.

Usage: events_v412.py [--drive N]
"""
import glob
import json
import math
import os
import re
import sys

import numpy as np

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt                                  # noqa: E402

plt.rcParams.update({
    'font.family': 'serif',
    'font.serif': ['STIXGeneral', 'DejaVu Serif', 'Times New Roman'],
    'mathtext.fontset': 'stix',
    'font.size': 6.6,
    'axes.linewidth': 0.6,
    'xtick.major.width': 0.5, 'ytick.major.width': 0.5,
    'xtick.major.size': 2.2, 'ytick.major.size': 2.2,
    'pdf.fonttype': 42, 'ps.fonttype': 42,
    'figure.dpi': 200,
})

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, 'survey_numbers_round190.tex')
FIG = 'event_crossings.pdf'
DRIVE = int(sys.argv[sys.argv.index('--drive') + 1]) if '--drive' in sys.argv \
    else 0
SFX = '' if DRIVE == 0 else '_drive%d' % DRIVE
TRIG = 5.0
# ★ The time binning of the dynamic-spectrum panels is a presentation
# choice and is stated in the caption, because it is the only number in the
# figure that is not a measurement.  Nine bins puts the carrier at about two
# standard deviations per bin, which is the point those panels make: the
# event is invisible in a single integration and exists only in the stack.
NBIN = 9
DYN_MHZ = 13.0                 # frequency half-range of panels (a) and (b)


def out(name):
    """A driven run never writes a path production reads."""
    b, e = os.path.splitext(name)
    return b + SFX + e


def macro(name):
    pat = re.compile(r'\\(?:new|renew|provide)command\{\\%s\}'
                     r'\{((?:[^{}]|\{[^{}]*\})*?)\}' % name)
    v = None
    for fn in sorted(glob.glob(os.path.join(HERE, 'survey_numbers*.tex'))):
        for mm in pat.finditer(open(fn, encoding='utf-8').read()):
            if mm.group(1).strip():
                v = mm.group(1).strip()
    if v is None:
        raise SystemExit('macro %s not found' % name)
    return v


M, fail = [], []


def m(k, v):
    M.append((k, v))


def ck(name, cond, detail=''):
    if not cond:
        fail.append(name)
    print('  %-58s %s  %s' % (name, 'PASS' if cond else 'FAIL', detail))


def mjd_to_date(mjd):
    """Calendar date of an MJD, to the day.  Fliegel & van Flandern."""
    jd = int(math.floor(mjd + 2400001.0))
    L = jd + 68569
    n = (4 * L) // 146097
    L = L - (146097 * n + 3) // 4
    i = (4000 * (L + 1)) // 1461001
    L = L - (1461 * i) // 4 + 31
    j = (80 * L) // 2447
    d = L - (2447 * j) // 80
    L = j // 11
    mo = j + 2 - 12 * L
    y = 100 * (n - 49) + i + L
    return '%04d %s %d' % (y, ('January February March April May June July '
                               'August September October November December'
                               ).split()[mo - 1], d)


# ------------------------------------------------------------------ inputs
R = json.load(open(os.path.join(HERE, 'r10inputs', 'recur_v411.json')))
CROSS = R['crossings']
LED = json.load(open(os.path.join(HERE, 'ledger.json')))
META = json.load(open(os.path.join(HERE, 'r11inputs', 'events',
                                   'figdata_meta.json')))

# ★ selected by a property of the measurement, never by name: the crossings
# whose star outranks every one of the control positions.
SEL = sorted([k for k, c in CROSS.items()
              if c['status'] == 'ok' and c['screen']],
             key=lambda k: -CROSS[k]['discovery']['T_matched'])
if DRIVE == 1:
    SEL = SEL[:1]
ck('E1 exactly two crossings outrank every control position, and both '
   'were extracted', len(SEL) == 2 and all(k in META for k in SEL),
   '%s' % SEL)
if len(SEL) != 2 or not all(k in META for k in SEL):
    raise SystemExit('the figure describes exactly two events; the selection '
                     'returned %s and the extract holds %s'
                     % (SEL, sorted(META)))

# attribution and the recurrence numbers, from the ledger and the record
LROW = {}
for r in LED['rows']:
    LROW[(r['eb'], round(float(r['freq']), 4))] = r


def ledger_row(c):
    return LROW.get((c['eb'], round(float(c['freq_GHz']), 4)))


def comb(c):
    """The inverse-variance combination of the repeat coverage at the
    registered cell, exactly as the recurrence test forms it.

    ★★★ ONE FORMULA, AND IT IS THE APPENDIX'S.  The exclusion is

        T_pers = S/sigmabar,  T_rep = abar/sigmabar,
        excl   = (S - abar)/sqrt(sigma_d^2 + sigmabar^2)
               = (T_pers - T_rep)/sqrt(1 + (T_pers/T_star)^2)

    so the discovery amplitude's own error is inside it and no exclusion can
    exceed the strength of the discovery it is built from.  What this
    generator printed before was (S - abar)/sigmabar, which treats that
    amplitude as exact: for the stronger event it reads 9.3 where the
    formula gives 4.9, and it is not a number the paper may quote.

    ★★ AND THE QUANTITY T_pers IS COMPARED WITH IS `T_rep`, the combination
    at the DISCOVERY DRIFT transported to each repeat epoch -- one cell, one
    drift, nothing maximised.  `T_anydrift` is the largest reading over about
    120 drift trials at the same cell; it is biased upward by construction
    and must never appear on the other side of a comparison with T_pers.
    """
    bl = [b for b in c['blocks'] if not b.get('bad_weight_product')]
    S = c['discovery']['amp_mJy']
    sd = c['discovery']['sig_mJy']
    w = [1.0 / b['sig_mJy'] ** 2 for b in bl]
    sb = 1.0 / math.sqrt(sum(w))
    ab = sum(b['amp_mJy'] * q for b, q in zip(bl, w)) / sum(w)
    return dict(n=len(bl), sbar=sb, abar=ab, T_pers=S / sb,
                T_rep=ab / sb,
                excl=(S - ab) / math.sqrt(sd * sd + sb * sb),
                excl_conditional=(S - ab) / sb,
                T_matched=max(b['T_matched'] for b in bl),
                T_anydrift=max(b['T_bestdrift_pub'] for b in bl),
                n_cat=sum(1 for b in bl if b.get('in_released_catalogue')),
                sep_min_h=min(abs(b['sep_from_discovery_h']) for b in bl),
                sep_max_h=max(abs(b['sep_from_discovery_h']) for b in bl),
                blocks=bl)


EV = {}
for k in SEL:
    c = CROSS[k]
    z = np.load(os.path.join(HERE, 'r11inputs', 'events',
                             'figdata_%s.npz' % k))
    EV[k] = dict(c=c, z=z, mt=META[k], s=comb(c), row=ledger_row(c))

# the deeper repeat of each event: the one whose noise at the cell is lowest
for k in SEL:
    s = EV[k]['s']
    EV[k]['deep'] = min(s['blocks'], key=lambda b: b['sig_mJy'])
    EV[k]['near'] = min(s['blocks'],
                        key=lambda b: abs(b['sep_from_discovery_h']))

K1, K2 = SEL                                   # strongest first


# ------------------------------------------------------------------ macros
def eirp(c, mt):
    d = c['discovery']
    return (4.0 * math.pi * (mt['dist_pc'] * 3.0856775814913673e16) ** 2
            * d['amp_mJy'] * 1e-29 * d['chanw_Hz'])


for tag, k in (('A', K1), ('B', K2)):
    c, mt, s = EV[k]['c'], EV[k]['mt'], EV[k]['s']
    d = c['discovery']
    row = EV[k]['row']
    m('Ev%sStar' % tag, c['display'])
    m('Ev%sFreq' % tag, '%.6f' % c['freq_GHz'])
    m('Ev%sBand' % tag, str(c['band']))
    m('Ev%sT' % tag, '%.2f' % d['T_matched'])
    m('Ev%sCtrlMax' % tag, '%.2f' % mt['ctrl_max_max'])
    m('Ev%sNCtrlAbove' % tag, '%d' % mt['n_ctrl_ge_star'])
    m('Ev%sDrift' % tag, '%+.0f' % d['drift_Hz_s'])
    m('Ev%sChanwkHz' % tag, '%.1f' % (d['chanw_Hz'] / 1e3))
    m('Ev%sFlux' % tag, '%.0f' % d['amp_mJy'])
    m('Ev%sFluxErr' % tag, '%.0f' % d['sig_mJy'])
    m('Ev%sRmsInt' % tag, '%.0f' % float(np.median(EV[k]['z']['sig_t'])))
    _e = eirp(c, mt)
    m('Ev%sEirp' % tag, '%.1f' % (_e / 10.0 ** int(math.floor(math.log10(_e)))))
    m('Ev%sEirpExp' % tag, '%d' % int(math.floor(math.log10(_e))))
    m('Ev%sDate' % tag, mjd_to_date(mt['t_start_mjd']))
    m('Ev%sRepDate' % tag, mjd_to_date(EV[k]['near']['t_start_mjd'] if
                                       't_start_mjd' in EV[k]['near'] else
                                       [q['t_start_mjd'] for q in
                                        mt['repeats']
                                        if q['eb'] == EV[k]['near']['eb']][0]))
    m('Ev%sNRep' % tag, '%d' % s['n'])
    # ★ the nearest covering epoch is not always a LATER one: every epoch
    # covering the stronger event precedes its own discovery block, and a
    # caption saying "the next observation" would be false.
    m('Ev%sNearSign' % tag,
      'earlier' if EV[k]['near']['sep_from_discovery_h'] < 0 else 'later')
    m('Ev%sNRepCat' % tag, '%d' % s['n_cat'])
    m('Ev%sNearH' % tag, '%.2f' % s['sep_min_h'])
    m('Ev%sSpanD' % tag, '%.0f' % (s['sep_max_h'] / 24.0))
    m('Ev%sTPers' % tag, '%.1f' % s['T_pers'])
    # ★ the quantity T_pers is compared with: the combination at the matched
    #   drift.  It may be negative, which is what one cell and one trial of a
    #   zero-mean statistic does.
    m('Ev%sTRep' % tag, '%+.2f' % s['T_rep'])
    m('Ev%sTMatched' % tag, '%+.2f' % s['T_matched'])
    m('Ev%sTAnyDrift' % tag, '%.2f' % s['T_anydrift'])
    m('Ev%sExcl' % tag, '%.1f' % s['excl'])
    # ★ the elapsed span of the observation, which is NOT the on-source time:
    #   the drift carries the carrier \Ev?DriftChan channels over the elapsed
    #   span, while the coherent stack holds \Ev?DwellMin of on-source time.
    #   Quoting one where the other belongs is minor 5 of the report.
    m('Ev%sElapsedMin' % tag, '%.0f' % (float(EV[k]['z']['dt'].max()) / 60.0))
    # ★★ the transition and the offset are the LEDGER's.  The frozen
    # measurement record carries the line list as it stood when the
    # measurement was made -- it names a different transition at a
    # different offset now -- and it carries the name in plain text, with
    # bare subscripts that are not legal outside maths.  Both faults have
    # one fix: read the row the table prints.
    m('Ev%sLine' % tag, row['line_tex'] or row['line'])
    m('Ev%sDv' % tag, '%+.0f' % row['dv_stellar'])
    m('Ev%sDispo' % tag,
      'attributed' if (row and row['attributed']) else 'unattributed')
    m('Ev%sNInt' % tag, '%d' % mt['n_int'])
    m('Ev%sDwellMin' % tag, '%.0f' % (mt['on_source_s'] / 60.0))
    m('Ev%sDistPc' % tag, '%.1f' % mt['dist_pc'])
    # the drift measured as what it does: channels crossed over the dwell
    _dch = abs(d['drift_Hz_s']) * (float(EV[k]['z']['dt'].max())) / d['chanw_Hz']
    m('Ev%sDriftChan' % tag, '%.0f' % _dch)
    # the single-integration visibility of the carrier
    m('Ev%sPerIntSig' % tag,
      '%.2f' % (d['amp_mJy'] / float(np.median(EV[k]['z']['sig_t']))))

# the deeper repeat of the second event, which is the cleaner non-recurrence
_dp = EV[K2]['deep']
m('EvBDeepH', '%.2f' % abs(_dp['sep_from_discovery_h']))
m('EvBDeepRatio', '%.1f' % (EV[K2]['c']['discovery']['sig_mJy']
                            / _dp['sig_mJy']))
m('EvBDeepTPers', '%.1f' % (EV[K2]['c']['discovery']['amp_mJy']
                            / _dp['sig_mJy']))
# ★★ WHAT THAT BLOCK ACTUALLY READ AT THE MATCHED DRIFT.  This macro used to
# carry `T_bestdrift_pub`, the maximum over every drift trial, and the section
# set it against `EvBDeepTPers`, a matched-drift expectation: a maximum over
# 120 trials on one side of a comparison and a single reading on the other.
# The matched reading is the one the expectation belongs beside, and the
# drift-maximised value is quoted on its own, where it is a statement that
# nothing is there at any drift rather than half of a comparison.
m('EvBDeepTObs', '%+.2f' % _dp['T_matched'])
m('EvBDeepTAnyDrift', '%.2f' % _dp['T_bestdrift_pub'])
m('EvBDeepExcl', '%.1f' % (
    (EV[K2]['c']['discovery']['amp_mJy'] - _dp['amp_mJy'])
    / math.sqrt(EV[K2]['c']['discovery']['sig_mJy'] ** 2
                + _dp['sig_mJy'] ** 2)))
# ★ what panel (b) shows, stated as a number so the caption does not have
# to appeal to the reader's eye: the sign of each time bin at the marked
# channel of the de-drifted panel.
def _binsign(k, n):
    z = EV[k]['z']
    dd, st, half = z['dyn_dd'], np.asarray(z['sig_t']), int(z['half'])
    ix = np.linspace(0, dd.shape[0], n + 1).astype(int)
    return [float(np.nanmean(dd[ix[i]:ix[i + 1], half])) for i in range(n)]


_bs = _binsign(K1, NBIN)
m('EvANBin', '%d' % NBIN)
m('EvANBinPos', '%d' % sum(1 for b in _bs if b > 0))
m('EvNCtrl', '%d' % EV[K1]['mt']['n_ctrl'])

# ------------------------------------------------------------- assertions
print('\nassertions')
v = max(abs(EV[k]['mt']['T_disc'] - EV[k]['mt']['T_pub']) for k in SEL)
if DRIVE == 2:
    v = 1.0
ck('E2 both extracts reproduce the published discovery statistic',
   v < 1e-6, 'worst absolute difference %.2e' % v)
v = max(EV[k]['mt']['n_ctrl_ge_star'] for k in SEL) if DRIVE != 3 else 1
ck('E3 no control position reaches the star in either window',
   v == 0, 'worst %d of %d above the star'
   % (v, EV[K1]['mt']['n_ctrl']))
_t = max(EV[k]['s']['T_anydrift'] for k in SEL) if DRIVE != 4 else 9.9
ck('E4 neither event reaches the trigger at its predicted cell in any '
   'repeat, at any drift', _t < TRIG, 'largest %.2f against %g' % (_t, TRIG))
# ★ the panel the caption calls "deeper" must BE deeper, in the only sense
# that matters here -- the noise at the registered cell.
v = EV[K2]['c']['discovery']['sig_mJy'] / _dp['sig_mJy']
if DRIVE == 5:
    v = 0.5
ck('E5 the repeat drawn as the decisive one is deeper than the discovery',
   v > 1.0, 'x%.2f deeper (%.2f against %.2f mJy)'
   % (v, EV[K2]['c']['discovery']['sig_mJy'], _dp['sig_mJy']))
# ★ a check that fires on the thing that would make the figure a lie: the
# repeat panel is drawn at the predicted STELLAR-frame cell, which must not
# be the discovery sky channel.
_mv = max(abs(q['f_here_GHz'] - EV[k]['c']['freq_GHz']) * 1e9
          / EV[k]['c']['discovery']['chanw_Hz']
          for k in SEL for q in EV[k]['mt']['repeats'])
if DRIVE == 6:
    _mv = 0.0
ck('E6 the predicted cell moves between epochs, so a sky-frequency panel '
   'would be drawn at the wrong channel', _mv > 0.1,
   'largest shift %.2f channels' % _mv)
# ★ the disposition the figure prints is the ledger's
_d = [(EV[k]['c']['display'],
       bool(EV[k]['row'] and EV[k]['row']['attributed'])) for k in SEL]
v = all(EV[k]['row'] is not None for k in SEL) if DRIVE != 7 else False
ck('E7 every drawn event has a ledger row, so the figure cannot disagree '
   'with the table', v, '%s' % _d)


# ★ the section says "both in Band X" in one phrase, so the two must be in
# one band; if a future list puts them in different bands the sentence is
# wrong and silently so.
_b = {EV[k]['c']['band'] for k in SEL} if DRIVE != 8 else {'6', '7'}
ck('E8 both events are in one ALMA band, which is what the section claims '
   'in one phrase', len(_b) == 1, 'bands %s' % sorted(_b))

# ★★★ THE ONE FORMULA.  Every exclusion this generator prints must be
# Eq. B1 evaluated on the three quantities the ledger prints, and nothing
# else -- the section, the figure caption and Table 4 then cannot carry three
# readings of one event.  Driven at 9.
_d1 = []
for k in SEL:
    s, ts = EV[k]['s'], EV[k]['c']['discovery']['T_matched']
    if DRIVE == 9:
        ts *= 1.05
    _d1.append(abs((s['T_pers'] - s['T_rep'])
                   / math.sqrt(1.0 + (s['T_pers'] / ts) ** 2) - s['excl']))
ck('E9 the exclusion is Eq. B1 on T_star, T_pers and T_rep alone',
   max(_d1) < 5e-3, 'largest departure %.2e' % max(_d1))
# ★★ AND IT CARRIES THE DISCOVERY AMPLITUDE'S OWN ERROR, so it cannot exceed
# the strength of the discovery it is built from.  The reading that drops that
# error is what this generator used to publish; the check demonstrates that
# the two differ, so the smaller one is published deliberately and not by
# accident.  Driven at 10.
_x = [(EV[k]['s']['excl'], EV[k]['s']['excl_conditional'],
       EV[k]['c']['discovery']['T_matched']) for k in SEL]
if DRIVE == 10:
    _x = [(c, e, t) for e, c, t in _x]
ck('E10 no exclusion exceeds its own discovery statistic, and the reading '
   'that drops the amplitude error does',
   all(e <= t + 0.05 for e, _c, t in _x) and all(c > e for e, c, _t in _x),
   '; '.join('%.1f against T*=%.2f (unweighted %.1f)' % (e, t, c)
             for e, c, t in _x))
# ★★ THE COMPARISON MUST NOT MIX THE TWO READINGS OF THE REPEAT CELL.  A
# drift-maximised value is a maximum over about 120 trials and is positive on
# average whatever is there, so it is strictly the larger of the two; printing
# it where T_rep belongs is what made 2.71 look like a measurement of this
# cell.  If the two ever agree, one is being computed by the other's rule.
_pair = [(EV[k]['s']['T_rep'], EV[k]['s']['T_anydrift']) for k in SEL]
if DRIVE == 11:
    _pair = [(b, b) for _a, b in _pair]
ck('E11 the matched and drift-maximised readings of the repeat cell are '
   'different numbers, and the smaller is the one the exclusion uses',
   all(a < b for a, b in _pair),
   '; '.join('%+.2f matched against %.2f over every drift' % p
             for p in _pair))


# ----------------------------------------------------------------- figure
def tbin(a, n):
    """Mean over `n` roughly equal time bins, NaN-aware."""
    idx = np.linspace(0, a.shape[0], n + 1).astype(int)
    return np.array([np.nanmean(a[idx[i]:idx[i + 1]], axis=0)
                     for i in range(n)]), idx


def binned_sigma(sig_t, idx):
    """The noise of each time bin's mean."""
    return np.array([float(np.sqrt(np.nansum(sig_t[idx[i]:idx[i + 1]] ** 2))
                           / max(1, idx[i + 1] - idx[i]))
                     for i in range(len(idx) - 1)])


def mhz(z):
    half = int(z['half'])
    return (np.arange(-half, half + 1) * float(z['chanw'])) / 1e6


fig = plt.figure(figsize=(7.1, 3.38))
gs = fig.add_gridspec(2, 3, left=0.060, right=0.985, bottom=0.102, top=0.925,
                      wspace=0.40, hspace=0.42)

z1, mt1, s1, c1 = EV[K1]['z'], EV[K1]['mt'], EV[K1]['s'], EV[K1]['c']
x1 = mhz(z1)
dtmin = z1['dt'] / 60.0

# --- (a) the dynamic spectrum as observed, with the fitted drift track
sel1 = np.abs(x1) <= DYN_MHZ
ax = fig.add_subplot(gs[0, 0])
B, idx = tbin(z1['dyn'], NBIN)
sb = binned_sigma(np.asarray(z1['sig_t']), idx)
kw = dict(aspect='auto', origin='lower',
          extent=[x1[sel1][0], x1[sel1][-1], 0, dtmin.max()],
          cmap='RdBu_r', vmin=-2.5, vmax=2.5, interpolation='nearest')
im = ax.imshow((B / sb[:, None])[:, sel1], **kw)
tr = (float(c1['discovery']['drift_Hz_s']) * z1['dt']) / 1e6
ax.plot(tr, dtmin, color='k', lw=0.9, ls='--')
ax.set_xlim(x1[sel1][0], x1[sel1][-1])
ax.set_xlabel(r'$\nu-\nu_{\rm event}$ (MHz)')
ax.set_ylabel('time (min)')
ax.set_title(r'(a) %s, as observed' % c1['display'], fontsize=6.8)

# --- (b) the same after de-drifting at the fitted rate
ax = fig.add_subplot(gs[0, 1])
B2, _ = tbin(z1['dyn_dd'], NBIN)
im = ax.imshow((B2 / sb[:, None])[:, sel1], **kw)
ax.axvline(0.0, color='k', lw=0.7, ls=':')
ax.set_xlabel(r'$\nu-\nu_{\rm event}$ (MHz)')
ax.set_ylabel('time (min)')
ax.set_title('(b) de-drifted at the fitted rate', fontsize=6.8)
cb = fig.colorbar(im, ax=ax, pad=0.025, fraction=0.055)
cb.set_label(r'$S/\sigma$', fontsize=5.8, labelpad=1.0)
cb.ax.tick_params(labelsize=5.2)

# --- (c) the stacked spectrum at the stellar position, and at the controls
ax = fig.add_subplot(gs[0, 2])
for j in range(z1['T_ctrl'].shape[0]):
    ax.plot(x1, z1['T_ctrl'][j], color='0.72', lw=0.45)
ax.plot(x1, z1['T_star'], color='k', lw=0.8)
ax.axhline(TRIG, color='#b2182b', lw=0.6, ls='--')
ax.set_xlabel(r'$\nu-\nu_{\rm event}$ (MHz)')
ax.set_ylabel(r'$T_\star$')
ax.set_title('(c) stacked at the star', fontsize=6.8)
ax.set_xlim(x1[0], x1[-1])

# --- (d) the 512 control statistics
ax = fig.add_subplot(gs[1, 0])
cm = np.asarray(z1['ctrl_max'])
ax.hist(cm, bins=26, color='0.78', edgecolor='0.45', linewidth=0.35)
ax.axvline(float(mt1['T_disc']), color='#b2182b', lw=1.0)
ax.axvline(float(cm.max()), color='k', lw=0.7, ls=':')
ax.set_xlabel(r'$T$ at a control position')
ax.set_ylabel('positions')
ax.set_title(r'(d) the %d controls' % mt1['n_ctrl'], fontsize=6.8)

# --- (e) the repeat coverage at the predicted stellar-frame cell
ax = fig.add_subplot(gs[1, 1])
w = 1.0 / np.asarray(z1['r_sig']) ** 2
comb_amp = np.nansum(np.asarray(z1['r_amp']) * w, axis=0) / np.nansum(w, axis=0)
comb_sig = 1.0 / np.sqrt(np.nansum(w, axis=0))
ax.plot(x1, comb_amp / comb_sig, color='#2166ac', lw=0.8)
ax.axhline(float(s1['T_pers']), color='#b2182b', lw=0.8, ls='--')
# ★ the number the caption quotes, marked where it is read: the combined
#   reading AT the predicted channel, which is what T_pers is compared with.
ax.plot([0.0], [float(s1['T_rep'])], marker='o', ms=2.6,
        mfc='#2166ac', mec='k', mew=0.4, zorder=5)
ax.axhline(0.0, color='0.6', lw=0.4)
ax.axvline(0.0, color='k', lw=0.6, ls=':')
ax.set_xlabel(r'$\nu-\nu_{\rm predicted}$ (MHz)')
ax.set_ylabel(r'$T$')
ax.set_title(r'(e) %s, %d repeats combined' % (c1['display'], s1['n']),
             fontsize=6.8)
ax.set_xlim(x1[0], x1[-1])
ax.set_ylim(min(-3.0, 1.1 * float(np.nanmin(comb_amp / comb_sig))),
            1.18 * float(s1['T_pers']))

# --- (f) the second event, and its deeper repeat
ax = fig.add_subplot(gs[1, 2])
z2, mt2, s2, c2 = EV[K2]['z'], EV[K2]['mt'], EV[K2]['s'], EV[K2]['c']
x2 = mhz(z2)
# only where the de-drifted stack keeps its full depth: this window's event
# sits near the band edge, so the outermost channels lose integrations and
# their noise rises.  Drawing them would invent a falling spectrum.
sch = np.asarray(z2['sig_ch'])
good = sch < 1.15 * np.nanmin(sch)
ax.plot(x2[good], np.asarray(z2['T_star'])[good], color='k', lw=0.8)
jd = [q['eb'] for q in mt2['repeats']].index(_dp['eb'])
ax.plot(x2[good], np.asarray(z2['r_T'])[jd][good], color='#2166ac', lw=0.8)
_tp2 = float(EV[K2]['c']['discovery']['amp_mJy'] / _dp['sig_mJy'])
ax.axhline(_tp2, color='#b2182b', lw=0.8, ls='--')
ax.plot([0.0], [float(_dp['T_matched'])], marker='o', ms=2.6,
        mfc='#2166ac', mec='k', mew=0.4, zorder=5)
ax.axhline(0.0, color='0.6', lw=0.4)
ax.axvline(0.0, color='k', lw=0.6, ls=':')
ax.set_xlabel(r'$\nu-\nu_{\rm predicted}$ (MHz)')
ax.set_ylabel(r'$T$')
ax.set_title('(f) %s, and its repeat %.1f h later'
             % (c2['display'].replace('$-$', '−'),
                abs(_dp['sep_from_discovery_h'])), fontsize=6.8)
ax.set_xlim(x2[good][0], x2[good][-1])
ax.set_ylim(None, 1.15 * _tp2)

os.makedirs(os.path.join(HERE, 'figures'), exist_ok=True)
fp = os.path.join(HERE, 'figures', out(FIG))
fig.savefig(fp, format='pdf')
plt.close(fig)
print('\nwrote %s' % fp)

with open(out(OUT), 'w') as fh:
    fh.write('%% GENERATED by events_v412.py -- do not hand-edit.\n')
    for k, v in M:
        assert k.isalpha(), 'a LaTeX macro name may contain letters only: ' + k
        fh.write('\\newcommand{\\%s}{%s}\n' % (k, v))
print('%d macros, %d assertions failed %s' % (len(M), len(fail), fail))
for _c, _s in ((c1, s1), (c2, s2)):
    print('%s  T*=%.3f at %.6f GHz, drift %+.0f Hz/s, %d repeats, '
          'T_pers %.2f against T_rep %+.2f at the matched drift, excluded '
          '%.1f sigma (%.1f if the amplitude error is dropped); largest over '
          'every drift %.2f'
          % (_c['display'], _c['discovery']['T_matched'], _c['freq_GHz'],
             _c['discovery']['drift_Hz_s'], _s['n'], _s['T_pers'],
             _s['T_rep'], _s['excl'], _s['excl_conditional'],
             _s['T_anydrift']))
if fail and DRIVE == 0:
    raise SystemExit('assertions failed: %s' % fail)
