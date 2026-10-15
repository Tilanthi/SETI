#!/usr/bin/env python3
r"""round 250 -> survey_numbers_round250.tex, sens_r12.json

THREE THINGS THE SENSITIVITY SECTION ASSERTS AND DID NOT MEASURE.

1.  THE INTERMITTENCY CAMPAIGN.  The paper states a recovery fraction at a
    duty cycle of one tenth and nowhere says what was varied, at what power,
    or over how many windows.  Worse, the fraction invites exactly the wrong
    reading: a carrier on for a tenth of a track loses nine tenths of its
    de-drifted amplitude, so a recovery of seven in ten cannot be a statement
    about a carrier at the completeness limit.  It is not: the trials inject
    at amplitudes far above each window's own trigger, and the quantity that
    generalises is not the recovery fraction but the ATTENUATION, which this
    file measures and which comes out equal to the duty cycle itself.  That
    is the statement worth printing, because it converts directly into a
    power penalty of one over the duty cycle on every limit in the paper.

2.  THE DRIFT-ACCELERATION RELATION, CHECKED IN THE GRID AND NOT IN THE
    PROSE.  The non-relativistic Doppler relation is a_los = c nudot/nu.  The
    text prints it that way and so does the figure, but neither demonstrates
    that the searched grid was built with it, and the two readings differ by
    twenty orders of magnitude, so the check is worth having rather than
    assuming.  It is run here over every Class A window's own released drift
    ceiling and acceleration ceiling, and the inverted relation is evaluated
    beside it so the clause cannot pass vacuously.

3.  WHICH EPSILON ERIDANI DATA THE FLUX-SCALE CHECK USES.  The appendix
    withholds the epsilon Eri Band 6 search windows; the methodology section
    uses epsilon Eri as one of the two external flux-scale checks.  Both are
    true and the paper never said which data each refers to.  The withheld
    set is split here into the windows that need a large beam correction and
    the ones at the pointing centre that need none, and the check's own
    record is read for what it used.

NOTHING IS TYPED.  The duty cycle, injected amplitude, integration count and
recovered signal-to-noise come from the campaign's own trial table; the drift
and acceleration ceilings from the released catalogue; the flux-scale
provenance from the frozen record the comparison was computed from.

    python3 sens_r12.py [--out DIR] [--drive N]

--drive 1..7 breaks one assertion each and nothing else; --drive 0 means "no
perturbation, but do not write a path production reads".
"""
import collections
import csv
import json
import math
import os
import statistics
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROUND = 250

DRIVE = None
OUTDIR = HERE
for _i, _a in enumerate(sys.argv):
    if _a == '--drive':
        DRIVE = int(sys.argv[_i + 1])
    elif _a == '--out':
        OUTDIR = sys.argv[_i + 1]
# ★ D36: the suffix follows the FLAG, not the perturbation, so `--drive 0`
# never writes a path production reads.
SUF = '' if DRIVE is None else '_drive%d' % DRIVE

OUT, FAIL = [], []


def m(name, val):
    assert name.isalpha(), (
        'a LaTeX macro name may contain letters only: %r' % name)
    OUT.append('\\newcommand{\\%s}{%s}' % (name, val))


def ck(label, cond, detail=''):
    print('  %-74s %s  %s' % (label, 'PASS' if cond else 'FAIL', detail))
    if not cond:
        FAIL.append(label)


# ===================================================================== 1
# THE INTERMITTENCY CAMPAIGN, DESCRIBED BY ITS OWN TRIAL TABLE.
#
# One row per trial.  `dwell` is the fraction of the integrations of ONE
# execution block during which the carrier radiates -- a duty cycle within a
# track, not across epochs -- and `amp_sigma` is the injected amplitude in
# units of that window's per-integration noise.  The table carries no drift
# column and the recovered peak sits in the injected channel, so the trials
# are undrifted and the joint drifting-and-intermittent case is not measured.
_rd = csv.DictReader(open(os.path.join(
    HERE, 'dwell_campaign_trials_v3.32.csv')))
DW = list(_rd)
COLS = list(_rd.fieldnames)
for r in DW:
    r['_d'] = float(r['dwell'])
    r['_a'] = float(r['amp_sigma'])
    r['_n'] = int(r['n_int'])
    r['_snr'] = float(r['recovered_snr'])
    r['_det'] = r['detected'] == 'True'
    # the amplitude a continuous carrier of this strength reaches in the
    # de-drifted stack, in units of the window's own 5 sigma trigger
    r['_trig'] = r['_a'] * math.sqrt(r['_n']) / 5.0

DUTIES = sorted({r['_d'] for r in DW})
D_MIN = min(DUTIES)
N_WIN = len({r['window'] for r in DW})
N_STAR = len({r['target'].rsplit('_B', 1)[0] for r in DW})
N_TRIAL = len(DW)

# ★★★ THE ATTENUATION, WHICH IS THE QUANTITY THAT TRANSFERS.  The de-drifted
# stack is coherent over the whole track, so a carrier present for a fraction
# f of it contributes to a fraction f of the integrations and is recovered at
# f of its continuous amplitude.  Measured here as the ratio of each trial's
# recovered signal-to-noise to the SAME window, amplitude and noise
# realisation at unit duty cycle, so every instrumental factor divides out.
_full = {}
for r in DW:
    if r['_d'] == 1.0:
        _full[(r['window'], r['_a'], r['realisation'])] = r['_snr']
ATT = collections.defaultdict(list)
for r in DW:
    f = _full.get((r['window'], r['_a'], r['realisation']))
    if f and f > 0:
        ATT[r['_d']].append(r['_snr'] / f)
ATT_MED = {d: statistics.median(v) for d, v in ATT.items()}
ATT_DEV = max(abs(ATT_MED[d] / d - 1.0) for d in ATT_MED)
if DRIVE == 1:
    ATT_DEV = 0.40
ck('the recovered amplitude of an intermittent carrier is its duty cycle '
   'times the continuous one, at every duty cycle tested',
   ATT_DEV < 0.03,
   'worst departure %.1f per cent over %d duty cycles: %s'
   % (100 * ATT_DEV, len(ATT_MED),
      ', '.join('%.2f->%.3f' % (d, ATT_MED[d]) for d in sorted(ATT_MED))))

# ★★ AND THE CLAUSE THAT STOPS THE RECOVERY FRACTION BEING READ AS A
# STATEMENT ABOUT THE SURVEY'S OWN LIMIT.  The trials inject well above each
# window's trigger; a carrier AT the completeness limit and on for a tenth of
# a track is attenuated below the trigger and is not recovered at all.  The
# published fractions therefore describe bright carriers, and the honest
# statement about the survey is the power penalty, not the fraction.
TRIG_FACS = sorted(r['_trig'] for r in DW)
TRIG_LO, TRIG_HI = TRIG_FACS[0], TRIG_FACS[-1]
TRIG_MED = statistics.median(TRIG_FACS)
if DRIVE == 2:
    TRIG_MED = 1.0
ck('the intermittency trials inject far above each window own trigger, so '
   'their recovery fractions are not statements about the completeness limit',
   TRIG_MED > 5.0 and TRIG_LO > 1.0,
   'x%.1f-x%.0f of the trigger amplitude, median x%.0f'
   % (TRIG_LO, TRIG_HI, TRIG_MED))

# the power penalty a duty cycle imposes on every limit in the paper
POW_FAC = 1.0 / D_MIN
# Two independent signatures of an undrifted trial: the table declares no
# drift at all, and the recovered peak is found in the channel the carrier was
# injected into rather than displaced along a track.
_nodriftcol = not [k for k in COLS if 'drift' in k.lower()]
_atinj = sum(1 for r in DW if r['peak_chan'] == r['inj_chan'])
if DRIVE == 3:
    _nodriftcol = False
ck('the trials carry no drift, so the joint drifting-and-intermittent case '
   'is declared unmeasured rather than implied measured',
   _nodriftcol and _atinj > 0.9 * len(DW),
   'no drift column among %d, and the recovered peak sits in the injected '
   'channel in %d of %d trials' % (len(COLS), _atinj, len(DW)))

m('DutyNWin', '%d' % N_WIN)
m('DutyNStar', '%d' % N_STAR)
m('DutyNTrial', '{:,}'.format(N_TRIAL).replace(',', '\\,'))
m('DutyNCycle', '%d' % len(DUTIES))
m('DutyCycleMinPct', '%.0f' % (100 * D_MIN))
m('DutyAttenDevPct', '%.0f' % max(1.0, round(100 * ATT_DEV)))
m('DutyAmpTrigLo', '%.1f' % TRIG_LO)
m('DutyAmpTrigHi', '%.0f' % TRIG_HI)
m('DutyAmpTrigMed', '%.0f' % TRIG_MED)
m('DutyPowFac', '%.0f' % POW_FAC)

# ===================================================================== 2
# THE DRIFT GRID WAS BUILT WITH a_los = c nudot/nu, CHECKED IN THE RELEASE.
CAT = list(csv.DictReader(open(os.path.join(
    HERE, 'per_target_results_v3.99.csv'))))
CAT_A = [r for r in CAT if r['search_class'] == 'A']
C_MS = 299792458.0
_dev, _inv = [], []
for r in CAT_A:
    nu = 0.5 * (float(r['flo_GHz']) + float(r['fhi_GHz'])) * 1e9
    nud = float(r['drift_max_Hz_s'])
    a = float(r['a_max_m_s2'])
    _dev.append(abs(a / (C_MS * nud / nu) - 1.0))
    _inv.append(C_MS * nu / nud)
DRIFT_DEV = max(_dev)
INV_MIN = min(_inv)
if DRIVE == 4:
    DRIFT_DEV = 0.5
ck('the released acceleration ceiling of every Class A window is c nudot/nu '
   'on that window own drift ceiling, so the grid was built with that '
   'relation',
   DRIFT_DEV < 1e-3 and len(CAT_A) > 0,
   'worst departure %.1e over %d windows' % (DRIFT_DEV, len(CAT_A)))
ck('and the inverted reading is excluded by many orders of magnitude, so the '
   'clause above is not vacuous',
   INV_MIN > 1e12, 'the inverted relation would give at least %.1e m/s2'
   % INV_MIN)
_e = int(math.floor(math.log10(DRIFT_DEV)))
m('DriftRelDev', '%.0f\\times10^{%d}' % (DRIFT_DEV / 10.0 ** _e, _e))
m('DriftRelNWin', '%d' % len(CAT_A))

# ===================================================================== 3
# WHICH EPSILON ERIDANI DATA THE FLUX-SCALE CHECK USES.
EPS = [r for r in json.load(open(os.path.join(
    HERE, 'corrected_export_v399.json')))['rows']
    if r['star_name'] == 'eps Eri' and r['band'] == 6]
# 1/A, the beam correction the pipeline applied, read back from the two
# released quantities whose ratio it is
_corr = sorted(r['smin'] * 1e3 / (5.0 * r['rms']) for r in EPS)
N_OFF = sum(1 for c in _corr if c > 1.01)
N_ON = len(_corr) - N_OFF
SCALE = json.load(open(os.path.join(HERE, 'r8inputs',
                                    'epseri_scale_v408.json')))
if DRIVE == 5:
    N_OFF = len(_corr)
ck('the withheld epsilon Eri windows split into the ones needing a large '
   'beam correction and the ones at the pointing centre, and the two sum to '
   'the withheld count',
   N_OFF + N_ON == len(EPS) and 0 < N_ON < len(EPS) and N_OFF > 0,
   '%d off axis up to x%.1f, %d at unit response, %d withheld'
   % (N_OFF, _corr[-1], N_ON, len(EPS)))
_arr = SCALE['array']
if DRIVE == 6:
    _arr = '12 m'
ck('the flux-scale check names the array and the block count it used, and it '
   'is the compact array where no beam correction enters',
   '7' in _arr and SCALE['n_blocks'] > 1,
   '%d blocks on the %s, %.2f h, band %s'
   % (SCALE['n_blocks'], _arr, SCALE['on_source_h'], SCALE['band']))
m('EpsEriNOffAxis', '%d' % N_OFF)
m('EpsEriNOnAxis', '%d' % N_ON)
m('EpsEriCorrMax', '%.1f' % _corr[-1])

# ===================================================================== 3b
# ★ ONE TYPED LITERAL IN THE APPENDIX, REPLACED BY THE NUMBER IT WAS A
# TRANSCRIPTION OF.  "over those it reaches at most 1.10 channels" was the
# only number in the smearing paragraph with no macro behind it, and it is
# not independent: eta_smear = sinc(pi Delta / 2) is monotonic over the range
# the release occupies, so the worst excursion is fixed by the worst retained
# amplitude, which the catalogue carries.  Inverted here rather than typed.
_eta = [float(r['eta_smear']) for r in CAT
        if r['eta_smear'] not in ('', 'None')]


def _sinc(d):
    x = math.pi * d / 2.0
    return 1.0 if x == 0 else math.sin(x) / x


_lo, _hi = 0.0, 2.0 - 1e-9
for _ in range(200):
    _mid = 0.5 * (_lo + _hi)
    if _sinc(_mid) > min(_eta):
        _lo = _mid
    else:
        _hi = _mid
DELTA_MAX = _lo
if DRIVE == 7:
    DELTA_MAX = 1.9
ck('the worst intra-integration excursion inverts the worst retained '
   'amplitude the release carries, over the windows that have one',
   abs(_sinc(DELTA_MAX) - min(_eta)) < 1e-6 and 0.0 < DELTA_MAX < 1.2
   and len(_eta) > 0,
   '%.4f channels from eta_smear %.4f over %d windows'
   % (DELTA_MAX, min(_eta), len(_eta)))
m('SmearDeltaMax', '%.2f' % DELTA_MAX)
m('SmearNEta', '%d' % len(_eta))

# ===================================================================== 4
# ★ THE ROUND NUMBER IS LITERAL IN THE FILENAME ON PURPOSE.  Written
# 'survey_numbers_round%d%s.tex' % (ROUND, SUF) -- two operands -- the name is
# invisible to `roundcollide`'s template resolver, whose pattern allows one
# operand after the digits.  It reported no writer and no collision for round
# 250: a silent blind spot in the one gate that exists to stop two generators
# claiming one round.  Written this way the round is named and the suffix is
# the only operand, which is the shape numbers_v410.py and five others use.
TEXOUT = os.path.join(OUTDIR, 'survey_numbers_round250%s.tex' % SUF)
assert TEXOUT.endswith('round%d%s.tex' % (ROUND, SUF)), (ROUND, TEXOUT)
OUT_JSON = os.path.join(OUTDIR, 'sens_r12%s.json' % SUF)
json.dump(dict(generated_by=os.path.basename(__file__), round=ROUND,
               drive=DRIVE,
               duty=dict(n_win=N_WIN, n_star=N_STAR, n_trial=N_TRIAL,
                         cycles=DUTIES, attenuation_median=ATT_MED,
                         attenuation_worst_dev=ATT_DEV,
                         amp_over_trigger=[TRIG_LO, TRIG_MED, TRIG_HI],
                         power_penalty_at_min_cycle=POW_FAC,
                         undrifted=_nodriftcol,
                         n_peak_at_injected=_atinj),
               drift=dict(worst_rel_dev=DRIFT_DEV, n_win=len(CAT_A),
                          inverted_min_m_s2=INV_MIN,
                          relation='a_los = c nudot / nu'),
               epseri=dict(n_withheld=len(EPS), n_off_axis=N_OFF,
                           n_on_axis=N_ON, worst_correction=_corr[-1],
                           check=dict(array=SCALE['array'],
                                      n_blocks=SCALE['n_blocks'],
                                      band=SCALE['band'],
                                      on_source_h=SCALE['on_source_h'])),
               failures=FAIL),
          open(OUT_JSON, 'w'), indent=1)
with open(TEXOUT, 'w') as fh:
    fh.write('%% GENERATED by %s -- do not hand-edit.\n'
             % os.path.basename(__file__))
    fh.write('\n'.join(sorted(OUT)) + '\n')
print('\n%d macros -> %s' % (len(OUT), os.path.basename(TEXOUT)))
print('intermittency: %d windows of %d stars, %d trials, %d duty cycles; '
      'recovered amplitude = duty cycle to %.0f per cent; injected at '
      'x%.1f-x%.0f of the trigger'
      % (N_WIN, N_STAR, N_TRIAL, len(DUTIES), 100 * ATT_DEV, TRIG_LO,
         TRIG_HI))
print('drift grid: a_los = c nudot/nu closes to %.1e over %d windows'
      % (DRIFT_DEV, len(CAT_A)))
print('eps Eri: %d withheld Band 6 windows, %d off axis (to x%.1f), %d at '
      'the pointing centre; the flux-scale check uses %d %s blocks'
      % (len(EPS), N_OFF, _corr[-1], N_ON, SCALE['n_blocks'], SCALE['array']))
if FAIL:
    print('FAILURES: %s' % FAIL)
    sys.exit(1)
