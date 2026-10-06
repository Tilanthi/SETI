#!/usr/bin/env python3
r"""round 140 -> survey_numbers_round140.tex: EVERY STACK TOLERANCE FROM THAT
STACK'S OWN CHANNEL WIDTH, AND THE WEIGHT PATHOLOGY EXPLAINED.

Why this exists.  The stack subsection quoted ONE velocity tolerance for a
survey whose stacked channel widths span a factor of a thousand, and the two
widths then got mixed inside a single argument: the sentence named a
\StkRefChanKHz = 488 kHz channel and printed \StkProxTolKms = 20.9 km/s, which
is one 15.625 MHz channel.  A 488 kHz channel at CO(2-1) is 0.63 km/s.  The
"+-30 km/s = 23.1 MHz = 47 channels" count beside it was in fine channels,
where 23.1 MHz really is 47 channels; in the coarse channels of the tolerance
it is 1.5.  The drift tolerances quoted in the same breath are also one fine
channel, over 44 d and over 2868 d, and they do not describe Proxima's stack
at all.

HOW IT HAPPENED, which matters more than the sentence.  stack_v408.py computes
the reflex and drift tolerances from a SINGLE reference width -- the mode of
the sub-MHz stacked widths -- although every stack's width is read from its own
data.  One survey-wide scalar for a per-stack quantity is the defect its own
comment warns about for the inter-epoch span and then commits for the channel.
numbers_v410.py later computed the tolerance properly, per stack, from
Proxima's own width, retired the fine-channel macro and pointed the retirement
at the per-stack one.  That substitution is correct in the Proxima sentence and
wrong in the general one, and nothing could see it: the tolerance macro and the
width macro were independent names, so a tolerance could be printed beside any
width at all.  macrosyn compares values, not the pairing.

So this generator does three things.

 1. Computes each tolerance from a channel width it has READ -- the fine mode
    and the coarse mode of the stacked groups, and Proxima's own width from
    Proxima's own record -- and cross-checks each against the catalogue's
    independent channelisation macros (\ChanAMedKHz, \ChanBModeMHz).
 2. PAIRS every tolerance macro with the width macro it belongs to, and
    requires the two to appear in the SAME SENTENCE wherever the prose quotes
    them.  That is the only check that can stop this recurring: a velocity
    tolerance and a channel width must not be separable.
 3. Explains the weight pathology (referee 2, minor 13) with the measured
    numbers and with what excluding those products cost: four two-epoch
    groups, 372 selected groups -> \StkNGroup, every affected star keeping
    other stacks.

Emits:

    \StkTolFineKms        one \StkRefChanKHz kHz channel at CO(2-1), km/s
    \StkReflexChanCoarse  the +-30 km/s reflex swing in \ChanBModeMHz MHz
                          channels (it is 47 in fine ones)
    \StkProxDriftHzS      one of Proxima's own channels over Proxima's own
                          epoch span: the drift tolerance of THAT stack
    \StkProxEirpSingle    Proxima's best single epoch on the same
                          injection-calibrated convention as the stack, so
                          the stacking gain is a comparison of like with like
                          and not a comparison with the survey median, which
                          is mostly distance
    \StkBadWeightMax      the pathological visibility weight
    \StkBadWeightMed      the survey median weight
    \StkBadWeightRatio    their ratio -- the paper said "10^11 times the
                          median", which is the weight itself, not the ratio
    \StkBadGroupDrop      groups lost by excluding those products
    \StkProxDistPc        Proxima's distance, so the sentence that declines
                          to compare its limit with the survey median can say
                          plainly where the depth comes from

Eleven assertions, each naming the input that would make it fail, and twelve
drives (the pairing gate is driven in both directions).

    python3 stacktol_v411.py [--drive N]

--drive 1..12 breaks one assertion each and nothing else; --drive 0 means "no
perturbation, but do not write a path production reads".  Run after
stack_v408.py and after numbers_v410.py: both are read back out of the macro
layer here, so a disagreement is reported against the file that published it.
"""
import collections
import csv
import json
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
DATA = os.path.join(HERE, 'stack_v408')
sys.path.insert(0, DATA)
import criterion as CR

DRIVE = None
for _i, _a in enumerate(sys.argv):
    if _a == '--drive':
        DRIVE = int(sys.argv[_i + 1])
SUF = '' if DRIVE is None else '_drive%d' % DRIVE

C_KMS = 299792.458
CO21_HZ = 230.5380000e9          # the reference line, as in stack_v408.py
REFLEX_KMS = 30.0                # a close-in giant's reflex amplitude

R = [json.loads(l) for l in open(os.path.join(DATA, 'stack6_result.jsonl'))
     if 'err' not in l]
G = json.load(open(os.path.join(DATA, 'groups3.json')))
WIN = {w['path']: w for w in json.load(open(os.path.join(DATA,
                                                         'windows.json')))}
BAD = set(json.load(open(os.path.join(DATA, 'badweight.json'))))
STACKR9 = json.load(open(os.path.join(HERE, 'r9inputs', 'stackinj_r9.json')))
BW = json.load(open(os.path.join(HERE, 'r10inputs', 'badweight_v411.json')))

OUT, fail = [], []


def m(name, val):
    assert name.isalpha(), (
        'a LaTeX macro name may contain letters only: %r' % name)
    OUT.append('\\newcommand{\\%s}{%s}' % (name, val))


def ck(label, cond, detail=''):
    print('  %-66s %s  %s' % (label, 'PASS' if cond else 'FAIL', detail))
    if not cond:
        fail.append(label)


def sci(x, nd=1):
    e = 0
    while abs(x) >= 10:
        x /= 10.0
        e += 1
    while abs(x) < 1:
        x *= 10.0
        e -= 1
    return r'$%.*f \times 10^{%d}$' % (nd, x, e)


def texval(name):
    """Read a macro back out of the macro layer, last definition wins."""
    pat = re.compile(r'\\(?:provide|renew|new)command\{?\\%s\}?\{([^}]*)\}'
                     % name)
    got = None
    for f in sorted(os.listdir(HERE)):
        if not (f.startswith('survey_numbers') and f.endswith('.tex')):
            continue
        if f == 'survey_numbers_round140.tex':
            continue
        for mm in pat.finditer(open(os.path.join(HERE, f),
                                    errors='ignore').read()):
            if mm.group(1).strip():
                got = mm.group(1).strip()
    return got


# ------------------------------------------------- the two channelisations
# Read, never assumed, and split where the CATALOGUE splits its two search
# classes rather than at a round number of my own choosing.  ★ The widths are
# not two values but ALMA's factor-of-two ladder from 15 kHz to 31 MHz; what
# makes "fine" and "coarse" legitimate is that the ladder has an empty rung
# between the widest Class A window and the narrowest Class B one.  A split at
# 1 MHz, which is the obvious choice, would have put the catalogue's own
# 1.953 MHz Class A windows on the coarse side.
CAT = list(csv.DictReader(open(os.path.join(
    HERE, 'per_target_results_v3.99.csv'))))
A_MAX = max(float(r['chanw_Hz']) for r in CAT if r['search_class'] == 'A')
B_MIN = min(float(r['chanw_Hz']) for r in CAT if r['search_class'] == 'B')
GAP = B_MIN / A_MAX
fine = [r['chanw'] for r in R if r['chanw'] <= A_MAX]
coarse = [r['chanw'] for r in R if r['chanw'] >= B_MIN]
BETWEEN = [r for r in R if A_MAX < r['chanw'] < B_MIN]
CH_FINE = float(max(set(fine), key=fine.count))
CH_COARSE = float(max(set(coarse), key=coarse.count))

TOL_FINE = C_KMS * CH_FINE / CO21_HZ
TOL_COARSE = C_KMS * CH_COARSE / CO21_HZ
REFLEX_HZ = REFLEX_KMS / C_KMS * CO21_HZ
REFLEX_CH_FINE = REFLEX_HZ / CH_FINE
REFLEX_CH_COARSE = REFLEX_HZ / CH_COARSE

# ------------------------------------------------- Proxima, from its own record
PX = STACKR9['Proxima Cen']
px = [r for r in R if r['skey'] == 'Proxima Cen']
assert px, 'no Proxima groups: the star key moved'
PG = min(px, key=lambda x: x['eirp_stack_W'])        # the deepest of its spws
NU_C = (PG['sf_lo'] + PG['sf_hi']) / 2.0             # its own sky frequency
PX_TOL_PRED = C_KMS * PG['chanw'] / NU_C             # km/s in ONE of its own
PX_DRIFT = PG['chanw'] / (PG['span_d'] * 86400.0)    # one channel over its span
PX_EIRP_SINGLE = PG['eirp_single_W'] * PX['p90']     # same convention as stack
PX_GAIN = PG['smin_single_mjy'] / PG['smin_stack_mjy']
PX_NFINE = sum(1 for r in px if r['chanw'] <= A_MAX)  # Class A groups: must be 0
PX_DPC = PG['d_pc']
NEAREST = min(r['d_pc'] for r in R)                  # must be Proxima's own

# ------------------------------------------------- the weight pathology
W_RATIO = BW['weight_max'] / BW['weight_median_survey']
sel = [g for g in G if g['n_block'] >= CR.MIN_BLOCKS
       and g['common_chan'] >= CR.MIN_COMMON_CHAN]
seen, uniq = set(), []
for g in sel:
    k = (g['skey'], round(g['chanw']), round(g['sf_common_lo'] / 1e6, 1),
         round(g['sf_common_hi'] / 1e6, 1))
    if k not in seen:
        seen.add(k)
        uniq.append(g)
# the exclusion rule as the stack applies it: one window per block (most
# integrations), then drop the flagged products, then the two-block minimum
dropped = []
for g in uniq:
    byblk = {}
    for p in g['paths']:
        w = WIN[p]
        if w['block'] not in byblk or w['nint'] > byblk[w['block']]['nint']:
            byblk[w['block']] = w
    kept = [w for w in byblk.values() if w['path'] not in BAD]
    if len(byblk) >= CR.MIN_BLOCKS and len(kept) < CR.MIN_BLOCKS:
        dropped.append(g)
N_DROP = len(dropped)
surviving = collections.Counter(r['skey'] for r in R)
DROP_STARS = sorted({g['skey'] for g in dropped})
DROP_STARS_KEEP = [s for s in DROP_STARS if surviving.get(s, 0) > 0]

# ------------------------------------------------- the pairing of tolerance
# and width.  A velocity or drift tolerance may not be printed in a sentence
# that does not name the channel it came from.
PAIRS = {'StkTolFineKms': 'StkRefChanKHz',
         'StkDriftTolHzS': 'StkRefChanKHz',
         'StkDriftTolTightHzS': 'StkRefChanKHz',
         'StkProxTolKms': 'ChanBModeMHz',
         'StkProxDriftHzS': 'ChanBModeMHz'}
MINE = '05b_stack.tex'
# Files I do not own whose tolerance sentences are queued in
# INTEGRATION_QUEUE.md for their owner.  Each must STILL be unpaired: once the
# queued text lands the entry here is stale and has to go, which is what the
# second half of P2 says.
# ★ v4.11 integration: BOTH QUEUED EDITS HAVE LANDED, so both entries are
# stale and are removed, which is what the paragraph above says must happen.
# `07_conclusions.tex` now reads "... is $\StkProxEirpCal$\,W in
# \ChanBModeMHz\,MHz channels --- a Class~B limit on an unresolved excess,
# carrying no drift discrimination --- for an emitter steady in the stellar
# frame to \StkProxTolKms\,km\,s$^{-1}$", i.e. paired; and the abstract no
# longer cites \StkProxTolKms at all.  The dict is therefore EMPTY and the
# `stale` clause is dormant by design, not vacuous by accident: `--drive 11`
# re-arms it against a file that is paired and requires it to fire, so the
# mechanism is demonstrated even when it has nothing to wait for.
PENDING = {}
# Sentence boundaries only: an em-dash clause is part of its sentence, and
# splitting on it separated "steady in the stellar frame to \StkProxTolKms" from
# the "--- one \ChanBModeMHz MHz channel ---" that pairs it.
SENT = re.compile(r'(?<!\\)\.(?:\s|$)')


def unpaired(path):
    """Tolerance citations in this file with no width macro beside them."""
    txt = open(path, errors='ignore').read()
    txt = '\n'.join(l for l in txt.splitlines()
                    if not l.lstrip().startswith('%'))
    out = []
    for s in SENT.split(txt):
        for tol, wid in PAIRS.items():
            if re.search(r'\\%s(?![A-Za-z])' % tol, s) \
                    and not re.search(r'\\%s(?![A-Za-z])' % wid, s):
                out.append(tol)
    return out


secdir = os.path.join(HERE, 'sections')
state = {f: unpaired(os.path.join(secdir, f))
         for f in sorted(os.listdir(secdir)) if f.endswith('.tex')}
if DRIVE == 10:
    state[MINE] = ['StkTolFineKms']
if DRIVE == 11:
    # Re-arm the dormant `stale` clause: declare a file as pending whose
    # tolerance sentence is already paired.  That is precisely the condition
    # the clause exists to catch -- a queue entry left behind after the text
    # it asked for has landed -- and it must fire.
    PENDING = {'07_conclusions.tex': 'StkProxTolKms'}
queue = os.path.join(os.path.dirname(HERE), '..', 'referee_r10',
                     'INTEGRATION_QUEUE.md')
queue = os.path.normpath(queue)
qtxt = open(queue, errors='ignore').read() if os.path.exists(queue) else ''
loose = sorted(f for f, u in state.items() if u and f not in PENDING)
stale = sorted(f for f in PENDING if not state.get(f))
unqueued = sorted(f for f in PENDING if f not in qtxt)

# ------------------------------------------------------------- the assertions
print('\nchannelisation of the %d stacked groups, read from the groups; the '
      'class split is the catalogue\'s' % len(R))
print('  Class A <= %.3f MHz, Class B >= %.3f MHz, %d group(s) in the gap %s'
      % (A_MAX / 1e6, B_MIN / 1e6, len(BETWEEN),
         [b['star'] for b in BETWEEN]))
print('  fine mode   %9.3f kHz (%d of %d fine groups) -> %.4f km/s at '
      'CO(2-1)' % (CH_FINE / 1e3, fine.count(CH_FINE), len(fine), TOL_FINE))
print('  coarse mode %9.3f MHz (%d of %d) -> %.3f km/s at CO(2-1)'
      % (CH_COARSE / 1e6, coarse.count(CH_COARSE), len(coarse), TOL_COARSE))
print('  +-%.0f km/s reflex = %.2f MHz = %.1f fine channels = %.2f coarse'
      % (REFLEX_KMS, REFLEX_HZ / 1e6, REFLEX_CH_FINE, REFLEX_CH_COARSE))
print('\nProxima, from its own record')
print('  %.3f MHz channels at %.3f GHz -> %.4f km/s (record %.4f)'
      % (PG['chanw'] / 1e6, NU_C / 1e9, PX_TOL_PRED, PX['kms_per_chan']))
print('  one channel over its own %.0f d span -> %.4g Hz/s' % (PG['span_d'],
                                                               PX_DRIFT))
print('  best single epoch %.4g W, stack %.4g W, gain x%.3f (N %d, Neff %.1f)'
      % (PX_EIRP_SINGLE, PX['eirp_calibrated_W'], PX_GAIN, PG['N'],
         PG['n_eff']))
print('\nweight pathology')
print('  %d of %d products, max weight %.3g against a median %.0f = x%.3g'
      % (len(BAD), len(WIN), BW['weight_max'], BW['weight_median_survey'],
         W_RATIO))
print('  cost of excluding them: %d of %d selected groups, stars %s'
      % (N_DROP, len(uniq), DROP_STARS))

print('\nassertions')
ck('T1 the catalogue\'s own two search classes are separated by an empty '
   'rung of the channel ladder, which is what makes "fine" and "coarse" '
   'legitimate names',
   (GAP if DRIVE != 1 else 1.0) > 2.0
   and len(BETWEEN) < 0.01 * len(R),
   'widest Class A %.3f MHz, narrowest Class B %.3f MHz, gap x%.1f; '
   '%d stacked group(s) in the gap' % (A_MAX / 1e6, B_MIN / 1e6, GAP,
                                       len(BETWEEN)))
ck('T2 the fine tolerance is the one the catalogue\'s own Class A median '
   'width gives, to a Hz',
   abs(CH_FINE / 1e3 - float(texval('ChanAMedKHz')
                             if DRIVE != 2 else 1.0)) < 0.05,
   'stack mode %.3f kHz against catalogue %s kHz'
   % (CH_FINE / 1e3, texval('ChanAMedKHz')))
ck('T3 Proxima stacks the catalogue\'s Class B mode, so the width beside its '
   'tolerance may be quoted as that mode',
   abs(PG['chanw'] / 1e6 - float(texval('ChanBModeMHz')
                                 if DRIVE != 3 else 1.0)) < 1e-6,
   '%.6f MHz against %s MHz' % (PG['chanw'] / 1e6, texval('ChanBModeMHz')))
ck('T4 the published Proxima tolerance IS one of its own channels at its own '
   'sky frequency -- the check it never had',
   abs(PX_TOL_PRED - (PX['kms_per_chan'] if DRIVE != 4 else 0.635)) < 1e-3,
   'computed %.4f km/s against published %.4f' % (PX_TOL_PRED,
                                                 PX['kms_per_chan']))
ck('T5 the fine and coarse tolerances differ by more than an order of '
   'magnitude, which is why one may never stand for the other',
   (TOL_COARSE / TOL_FINE if DRIVE != 5 else 1.0) > 10.0,
   '%.3f km/s against %.4f = x%.0f' % (TOL_COARSE, TOL_FINE,
                                       TOL_COARSE / TOL_FINE))
ck('T6 Proxima has no fine-channel group, so its stacked limit is Class B '
   'and carries no drift discrimination',
   (PX_NFINE if DRIVE != 6 else 1) == 0,
   '%d of %d Proxima groups are sub-MHz' % (PX_NFINE, len(px)))
ck('T7 the single-epoch limit this gain is measured against is the SAME '
   'star\'s and on the same convention',
   abs(PX_EIRP_SINGLE / PX['eirp_calibrated_W']
       - (PX_GAIN if DRIVE != 7 else 1.0)) < 1e-6
   and abs(PX_GAIN - float(texval('StkProxGain'))) < 0.005,
   'ratio %.4f, published gain %s' % (PX_EIRP_SINGLE
                                      / PX['eirp_calibrated_W'],
                                      texval('StkProxGain')))
ck('T8 Proxima is the nearest stacked star, which is why the sentence may '
   'attribute the size of its limit to distance',
   abs(PX_DPC - (NEAREST if DRIVE != 12 else 0.1)) < 1e-9,
   '%.4f pc against a nearest stacked star at %.4f pc' % (PX_DPC, NEAREST))
ck('P1 the flagged products are the list the stack excluded, and the frozen '
   'measurement counts the same products',
   len(BAD) == (BW['n_products_flagged'] if DRIVE != 8 else 0)
   == int(texval('StkBadWeight'))
   and len(WIN) == BW['n_products_retained'],
   '%d flagged of %d retained' % (len(BAD), len(WIN)))
ck('P2 excluding them costs exactly the groups whose every epoch was '
   'flagged, and no star loses its stack',
   N_DROP == len(uniq) - len(R)
   and len(DROP_STARS_KEEP) == len(DROP_STARS if DRIVE != 9
                                   else DROP_STARS + ['nostack'])
   and all(g['n_block'] == CR.MIN_BLOCKS for g in dropped),
   '%d dropped, %d selected - %d stacked, stars keeping other stacks %d/%d'
   % (N_DROP, len(uniq), len(R), len(DROP_STARS_KEEP), len(DROP_STARS)))
ck('P3 no tolerance is printed in a sentence that does not name its channel '
   'width; the files queued for their owner are still unpaired and still '
   'queued',
   not loose and not stale and not unqueued,
   'unpaired %s | stale pending %s | pending but not queued %s'
   % (loose, stale, unqueued))

print('\nassertions failed: %d %s' % (len(fail), fail))
if fail and DRIVE is None:
    raise SystemExit('stacktol_v411: %d assertion(s) failed: %s'
                     % (len(fail), fail))

# ---------------------------------------------------------------- the macros
m('StkTolFineKms', '%.2f' % TOL_FINE)
m('StkReflexChanCoarse', '%.1f' % REFLEX_CH_COARSE)
m('StkProxDriftHzS', sci(PX_DRIFT))
m('StkProxEirpSingle', sci(PX_EIRP_SINGLE, 2).strip('$'))
m('StkProxDistPc', '%.2f' % PX_DPC)
m('StkBadWeightMax', sci(BW['weight_max'], 2))
m('StkBadWeightMed', '%.0f' % BW['weight_median_survey'])
m('StkBadWeightRatio', sci(W_RATIO))
m('StkBadGroupDrop', '%d' % N_DROP)

path = os.path.join(HERE, 'survey_numbers_round140%s.tex' % SUF)
with open(path, 'w') as fh:
    fh.write('%% GENERATED by stacktol_v411.py -- do not hand-edit.\n')
    fh.write('\n'.join(sorted(OUT)) + '\n')
print('\nwrote %s (%d macros)' % (os.path.basename(path), len(OUT)))
