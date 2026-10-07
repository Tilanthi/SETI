#!/usr/bin/env python3
r"""Round 210: WHICH POPULATION THE MULTI-EPOCH STACK DESCRIBES, AND WHAT THE
STACKING GAIN ACTUALLY IS.

WHY THIS EXISTS
---------------
1. THE STACK'S STARS ARE NOT THE SURVEY'S STARS.  Section 5.7 said
   "\StkNStar of the surveyed stars hold more than one searched execution
   block".  69 is the number of stars entering the stacks, and ELEVEN OF THEM
   ARE NOT PRIMARY-CENSUS STARS: ten are beyond-40 pc out-of-sample control
   stars and the eleventh, eps Eri, is covered only by archival Band 6 blocks
   that the ledger withholds from the extension row it reports.  So an eighth
   of the stars in the paper's deepest limit came from outside the sample the
   rest of the paper is about, and the aggregate gain was quoted over the
   union.  The census-only statistics are emitted here, and they differ: the
   median gain over the census stars is larger than over the union, because
   the out-of-sample stars are shallow two-epoch control stacks.

   ★ THE SPLIT IS ESTABLISHED ON EXECUTION BLOCKS, NOT ON NAMES.  A name join
   is what this project's commonest defect looks like, and a stacked star
   carrying a Gaia directory name where the catalogue carries an HD number
   would be misclassified by one.  S2 requires that no star called
   non-census shares a single execution block with the census, and that every
   star called census owns at least one -- so the classification is keyed on
   an identifier and the row counts are asserted.

2. THE REALISED GAIN IS NOT A SEPARATE MEASUREMENT FROM sqrt(N_eff).  For
   every one of the 368 groups,

       gain_real_vs_best  ==  sqrt(N_eff) / madZ                        (S4)

   exactly, where madZ is the MEASURED noise of the stacked spectrum in units
   of the inverse-variance prediction.  Two consequences.  \StkGainVsNeff =
   0.992 is therefore the median of 1/madZ and nothing else: it says that
   inverse-variance propagation predicts the measured noise of a stacked
   spectrum to about one per cent IN THE MEDIAN, with a per-stack spread of
   \StkMadZScatterPct per cent -- it is not independent evidence that the
   combination is ideal for any individual stack.  And Proxima's realised
   3.19 over sqrt(N_eff) = 2.80 is that star's own noise realisation, 0.88,
   which lies inside twice the published spread.  The like-for-like gain is
   2.80 = 0.998 sqrt(N_eff); the rest is the noise of a finite stack.

Reads the stack products, the released catalogue, the four non-census block
exports and the published macro layer; writes survey_numbers_round210.tex.
Nothing is typed: every count is len(set) and every ratio is recomputed.

    python3 stack_v412.py [--drive N]       N = 0..8

--drive 0 writes no production path and perturbs nothing; 1..8 break one
assertion each.  Run after stack_v408.py, stacktol_v411.py and cover_v412.py:
all three are read back out of the macro layer, so a disagreement is reported
against the file that published it.
"""
import collections
import csv
import glob
import json
import math
import os
import re
import sys

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
DATA = os.path.join(HERE, 'stack_v408')
sys.path.insert(0, DATA)
import starkey                                              # noqa: E402

ROUND = 210

# D36: a test must never write to a path production reads.  The suffix follows
# the FLAG, not the perturbation.
DRIVE = int(sys.argv[sys.argv.index('--drive') + 1]) if '--drive' in sys.argv \
    else None
SUF = '' if DRIVE is None else '_drive%d' % DRIVE

# --------------------------------------------------------------- macro layer
_VALS = {}
for _f in sorted(glob.glob(os.path.join(HERE, 'survey_numbers*.tex'))):
    if '_drive' in os.path.basename(_f):
        continue
    for _n, _v in re.findall(
            r'\\(?:new|renew|provide)command\*?\{\\([A-Za-z]+)\}\{([^}]*)\}',
            open(_f, encoding='utf8', errors='ignore').read()):
        _VALS[_n] = _v.strip()


def texval(name):
    if name not in _VALS:
        raise SystemExit('stack_v412: macro \\%s is not published' % name)
    return _VALS[name]


def texnum(name):
    return float(re.sub(r'[^0-9.eE+-]', '', texval(name).replace(
        r'\times10^{', 'e').replace(r'\times 10^{', 'e')))


# ------------------------------------------------------------------- inputs
WIN = json.load(open(os.path.join(DATA, 'windows.json')))
IDMAP, _ = starkey.build(WIN)
R = [json.loads(l) for l in open(os.path.join(DATA, 'stack6_result.jsonl'))]
R = [r for r in R if 'err' not in r]
CAT = list(csv.DictReader(open(os.path.join(
    HERE, 'per_target_results_v3.99.csv'))))

# The four sets of execution blocks that are NOT the primary census, named as
# tab:blockledger names them.  Read from the same exports the ledger reads.
SETS = {
    'census': {r['eb'] for r in CAT},
    'holdout': {r['eb'] for r in json.load(open(os.path.join(
        HERE, 'holdout_export_v381.json')))['rows']},
    'oos': {r['eb'] for r in json.load(open(os.path.join(
        HERE, 'outofsample_v381.json')))['rows']},
    'extension': {r['eb'] for r in json.load(open(os.path.join(
        HERE, 'export_extension.json')))['rows']},
}

# ---------------------------------------------------- the population split
# Blocks per canonical stellar identity, from the windows the stack consumed.
BLOCKS = collections.defaultdict(set)
for w in WIN:
    BLOCKS[IDMAP.get(w['skey'], w['skey'])].add(w['block'])


def norm(s):
    return re.sub(r'[^a-z0-9]', '', s.lower())


SYSOF = {norm(r['star_name']): r['system_id'] for r in CAT}
SKEYS = sorted({r['skey'] for r in R})
IN_CENSUS = [s for s in SKEYS if norm(s) in SYSOF]
OUT_CENSUS = [s for s in SKEYS if norm(s) not in SYSOF]
STK_SYS = {SYSOF[norm(s)] for s in IN_CENSUS}

# Where each non-census stacked star's blocks come from.  A star is counted
# under 'oos' only if EVERY one of its stacked blocks is an out-of-sample
# block; anything else is reported as 'other archival' rather than guessed at.
PROV = {}
for s in OUT_CENSUS:
    bs = BLOCKS[s]
    PROV[s] = sorted(k for k, v in SETS.items() if bs & v) or ['unlisted']
OOS_ONLY = [s for s in OUT_CENSUS if PROV[s] == ['oos']]
OTHER_OUT = [s for s in OUT_CENSUS if PROV[s] != ['oos']]

# Blocks of the non-census stars that are census blocks.  Must be empty: that
# is the identifier-keyed form of the classification the names gave.
LEAK = {s: sorted(BLOCKS[s] & SETS['census']) for s in OUT_CENSUS}
LEAK = {s: v for s, v in LEAK.items() if v}
NO_OWN = [s for s in IN_CENSUS if not (BLOCKS[s] & SETS['census'])]

# ------------------------------------------------------- census statistics
CEN = [r for r in R if norm(r['skey']) in SYSOF]
OUT = [r for r in R if norm(r['skey']) not in SYSOF]
GB = np.array([r['gain_real_vs_best'] for r in CEN])
GB_ALL = np.array([r['gain_real_vs_best'] for r in R])
N_CEN_EPOCH = sum(r['N'] for r in CEN)
H_CEN = sum(r['on_source_h'] for r in CEN)

G_MED = float(np.median(GB))
G_P90 = float(np.percentile(GB, 90))
G_MAX = float(GB.max())
G_MED_ALL = float(np.median(GB_ALL))

# ------------------------------------------------------- the gain identity
SNE = np.array([r['sqrt_n_eff'] for r in R])
MADZ = np.array([r['madZ'] for r in R])
IDENT = float(np.abs(GB_ALL - SNE / MADZ).max())

PX = min((r for r in R if r['skey'] == 'Proxima Cen'),
         key=lambda x: x['eirp_stack_W'])
PX_NOISE = PX['madZ']
PX_SQ = math.sqrt(PX['n_eff'])
SPREAD = texnum('StkMadZScatterPct') / 100.0

# The deepest stacked limit in the paper, and whose it is.
DEEPEST = min(R, key=lambda r: r['eirp_stack_W'])
PX_EB_CENSUS = {r['eb'] for r in CAT if r['star_name'] == DEEPEST['skey']}

# Stars the section names through the macro layer.  DISCOVERED, not listed:
# every macro the section cites whose published value is one of the stacked
# stars.  A hard-coded list here would stop seeing a newly named star, which
# is the way this family of defect always arrives.
_SKNORM = {norm(s): s for s in SKEYS}
_SECTXT = open(os.path.join(HERE, 'sections', '05b_stack.tex'),
               errors='ignore').read()
_CITED = set(re.findall(r'\\([A-Za-z]{3,})', re.sub(r'(?<!\\)%.*', '',
                                                  _SECTXT)))
NAMEMAC = sorted(n for n in _CITED & set(_VALS) if norm(_VALS[n]) in _SKNORM)
NAMED = [_VALS[n] for n in NAMEMAC]

# ------------------------------------- the population-pairing gate (S8)
# An aggregate stack statistic computed over all 69 stars may not be printed
# in a sentence that does not also name how many of them lie outside the
# census.  This is the same discipline as round 140's tolerance/width pairing,
# applied to the population instead of the channel.
ALLPOP = ('StkNStar', 'StkNGroup', 'StkHours', 'StkNEpochComb',
          'StkLimitGainMed', 'StkLimitGainPNinety', 'StkLimitGainMax')
POPMARK = 'SxStkStarOutside'
MINE = '05b_stack.tex'
# Files I do not own whose aggregate sentence is queued for its owner.  Each
# must STILL be unpaired; once the queued text lands, the entry here is stale.
# ★ v4.12 INTEGRATION: the queued text has landed.  `07_conclusions.tex`
#   conclusion 6 now quotes the census-only median \SyStkGainMed and no
#   longer prints an all-69 aggregate, so the exception is stale and this
#   dict is empty -- which is the state the clause is written to reach.  The
#   mechanism stays demonstrated by `--drive 8`, which puts an unpaired
#   aggregate back into the file this generator does own, exactly as round
#   140's P3 does after its own list empties.
PENDING = {}
SENT = re.compile(r'(?<!\\)\.(?:\s|$)')


def unpaired(path):
    txt = '\n'.join(l for l in open(path, errors='ignore').read().splitlines()
                    if not l.lstrip().startswith('%'))
    out = []
    for s in SENT.split(txt):
        if re.search(r'\\%s(?![A-Za-z])' % POPMARK, s):
            continue
        for mm in ALLPOP:
            if re.search(r'\\%s(?![A-Za-z])' % mm, s):
                out.append(mm)
    return sorted(set(out))


SECDIR = os.path.join(HERE, 'sections')
STATE = {f: unpaired(os.path.join(SECDIR, f))
         for f in sorted(os.listdir(SECDIR)) if f.endswith('.tex')}
if DRIVE == 8:
    STATE[MINE] = ['StkLimitGainMed']
# The queue lives beside the paper tree, not inside it.  Search upward rather
# than hard-coding a depth: a hard-coded '../..' silently disarms this clause
# in any relocated copy of the build, which is the same "check that cannot
# fail" this project keeps rediscovering.  If it is genuinely not found the
# clause FAILS and says where it looked.
def _find_queue():
    if os.environ.get('R11_QUEUE'):
        return os.environ['R11_QUEUE']
    d = HERE
    tried = []
    for _ in range(6):
        d = os.path.dirname(d)
        c = os.path.join(d, 'referee_r11', 'INTEGRATION_QUEUE.md')
        tried.append(c)
        if os.path.exists(c):
            return c
    return tried


QPATH = _find_queue()
if isinstance(QPATH, list):
    QTXT, QWHERE = '', 'NOT FOUND, looked in %s' % QPATH
else:
    QTXT, QWHERE = open(QPATH, errors='ignore').read(), QPATH
LOOSE = sorted(f for f, u in STATE.items() if u and f not in PENDING)
STALE = sorted(f for f in PENDING if not STATE.get(f))
UNQUEUED = sorted(f for f in PENDING
                  if f not in QTXT or PENDING[f] not in QTXT)

# --------------------------------------------------------------- assertions
fail = []


def ck(name, ok, detail=''):
    print('  %-4s %s  %s' % ('PASS' if ok else 'FAIL', name, detail))
    if not ok:
        fail.append(name.split()[0])


print('the stacked population, keyed on execution block')
for s in OUT_CENSUS:
    print('  %-14s %2d blocks  %s' % (s, len(BLOCKS[s]), '+'.join(PROV[s])))
print('  census %d stars / %d systems / %d groups; outside %d stars / %d '
      'groups' % (len(IN_CENSUS), len(STK_SYS), len(CEN), len(OUT_CENSUS),
                  len(OUT)))
print('\nassertions')

_v = len(IN_CENSUS) + len(OUT_CENSUS) if DRIVE != 1 else len(IN_CENSUS)
ck('S1 the census and non-census stacked stars partition the published '
   'total, and so do their groups and epoch-windows',
   _v == int(texnum('StkNStar'))
   and len(CEN) + len(OUT) == int(texnum('StkNGroup'))
   and N_CEN_EPOCH + sum(r['N'] for r in OUT) == int(texnum('StkNEpochComb'))
   and len(OOS_ONLY) + len(OTHER_OUT) == len(OUT_CENSUS),
   '%d + %d = %s stars, %d + %d = %s groups, %d + %d = %s epoch-windows'
   % (len(IN_CENSUS), len(OUT_CENSUS), texval('StkNStar'), len(CEN),
      len(OUT), texval('StkNGroup'), N_CEN_EPOCH,
      sum(r['N'] for r in OUT), texval('StkNEpochComb')))

_leak = LEAK if DRIVE != 2 else {OUT_CENSUS[0]: ['A002_forced']}
ck('S2 the split is keyed on execution blocks and not on names: no '
   'non-census stacked star shares a block with the census, and every '
   'census one owns at least one',
   not _leak and not NO_OWN,
   'leaking stars %s | census stars with no census block %s'
   % (sorted(_leak), NO_OWN))

_v = DEEPEST['skey'] if DRIVE != 3 else OUT_CENSUS[0]
ck('S3 the deepest stacked limit in the paper belongs to a census star, and '
   'its census blocks are the number the systems table prints',
   norm(_v) in SYSOF
   and len(PX_EB_CENSUS) == int(texnum('SxProxEbCensus'))
   and (int(texnum('SxProxEbCensus')) + int(texnum('SxProxEbExt'))
        == int(texnum('StkProxN'))),
   '%s, %d census blocks (%s) + %s extension = %s stacked'
   % (DEEPEST['skey'], len(PX_EB_CENSUS), texval('SxProxEbCensus'),
      texval('SxProxEbExt'), texval('StkProxN')))

_v = IDENT if DRIVE != 4 else 1.0
ck('S4 the realised gain is sqrt(N_eff) divided by the measured noise of the '
   'stacked spectrum, identically, so \\StkGainVsNeff is the median of that '
   'noise term and not a second measurement',
   _v < 1e-9
   and abs(np.median(1.0 / MADZ) - texnum('StkGainVsNeff')) < 5e-4,
   'max |gain - sqrt(Neff)/madZ| = %.2g over %d groups; median 1/madZ '
   '%.4f against %s' % (IDENT, len(R), np.median(1.0 / MADZ),
                        texval('StkGainVsNeff')))

_v = PX_NOISE if DRIVE != 5 else 1.0
ck('S5 Proxima\'s excess over sqrt(N_eff) is its own noise realisation, and '
   'that realisation is inside twice the published per-stack spread',
   abs(PX_SQ / _v - texnum('StkProxGain')) < 0.005
   and abs(1.0 - PX_NOISE) < 2 * SPREAD,
   'sqrt(Neff) %.4f / madZ %.4f = %.4f (published %s); |1-madZ| %.3f against '
   '2x%.2f' % (PX_SQ, PX_NOISE, PX_SQ / PX_NOISE, texval('StkProxGain'),
               abs(1 - PX_NOISE), SPREAD))

_v = G_MED if DRIVE != 6 else G_MED_ALL
ck('S6 the census-only gain really differs from the union, by more than the '
   'precision it is printed to, and is the larger of the two',
   abs(_v - G_MED_ALL) >= 0.005 and _v > G_MED_ALL,
   'census %.4f against all %.4f over %d and %d groups'
   % (G_MED, G_MED_ALL, len(CEN), len(R)))

_v = NAMED if DRIVE != 7 else NAMED + [OUT_CENSUS[0]]
ck('S7 every star this section names through the macro layer is a '
   'primary-census star, and at least one such star is named',
   len(NAMEMAC) > 0 and all(norm(s) in SYSOF for s in _v),
   '%s' % ', '.join('%s=%s (%s)' % (n, _VALS[n], norm(_VALS[n]) in SYSOF)
                    for n in NAMEMAC) if NAMEMAC else 'none found')

ck('S8 no aggregate computed over all the stacked stars is printed in a '
   'sentence that does not say how many of them are outside the census; the '
   'file queued for its owner is still unpaired and still queued',
   not LOOSE and not STALE and not UNQUEUED,
   'unpaired %s | stale pending %s | pending but not queued %s | queue %s'
   % (LOOSE, STALE, UNQUEUED, QWHERE))

print('\nassertions failed: %d %s' % (len(fail), fail))
if fail and DRIVE is None:
    raise SystemExit('stack_v412: %d assertion(s) failed: %s'
                     % (len(fail), fail))

# ------------------------------------------------------------------ macros
OUTM = []


def m(name, val):
    assert not any(x.startswith('\\newcommand{\\%s}' % name) for x in OUTM), name
    assert name.isalpha(), name          # a macro name may contain letters only
    OUTM.append('\\newcommand{\\%s}{%s}' % (name, val))


m('SyStkNGroup', '%d' % len(CEN))
m('SyStkNEpochComb', '%d' % N_CEN_EPOCH)
m('SyStkHours', '%.0f' % H_CEN)
m('SyStkGainMed', '%.2f' % G_MED)
m('SyStkGainPNinety', '%.2f' % G_P90)
m('SyStkGainMax', '%.2f' % G_MAX)
m('SyStkStarOos', '%d' % len(OOS_ONLY))
m('SyStkStarOther', '%d' % len(OTHER_OUT))
m('SyProxNoiseMeas', '%.2f' % PX_NOISE)

PATH = os.path.join(HERE, 'survey_numbers_round210%s.tex' % SUF)
with open(PATH, 'w') as fh:
    fh.write('%% GENERATED by stack_v412.py (round %d) -- do not hand-edit.\n'
             % ROUND)
    fh.write('\n'.join(sorted(OUTM)) + '\n')
print('\nwrote %s (%d macros)' % (os.path.basename(PATH), len(OUTM)))
