#!/usr/bin/env python3
r"""ONE determination of when every execution block was observed, and ONE
predicate for whether two of them are more than a day apart.

WHY THIS FILE EXISTS.  `epochs_v386.json` resolved the execution blocks the
archive does not index by `asdm_uid` through their **member OUS**, and the
value that comes back is the EARLIEST BLOCK IN THAT OBSERVING UNIT.  So a
system whose repeat blocks sit inside one scheduling unit has every interval
equal to zero and is classified "all within one day".  Measured: 252 of the
404 stored stamps are shared with another block, and of the 141 blocks whose
measurement sets survive and can be read directly, 90 disagree with the stored
stamp -- the worst by 246 days.

Four generators classified epoch separations out of that file independently --
`epochsplit_v399.py` (the split), `cover_v412.py` (the confirmable systems),
`maskso_v414.py` (the per-crossing intervals) and `epochfix_v415.py` (the
correction) -- so the defect had to be fixed in four places and the fix had to
agree in four places.  It lives here instead.  There is one epoch per block,
one threshold, one witness, and one `apart()`.

THE WITNESS, AND WHY IT IS CALIBRATED RATHER THAN CHOSEN.  Each block carries
its own barycentric velocity term, which moves by about 60 km/s over a year
and by at most a fraction of a km/s within a day.  Over the 738 block pairs for
which both measurement sets survive, a threshold of 1.5 km/s fires on 497 pairs
and is right every time -- zero false separations -- and the largest difference
seen among pairs genuinely taken within one day is 0.52 km/s.

★ THE PREDICATE IS ONE-SIDED BY CONSTRUCTION.  It can show that two blocks are
separated; it can never show that two were simultaneous.  So a count of systems
with no separated epoch is an UPPER bound and a count of systems with one is a
LOWER bound, and every caller must say so.

    import epochs_r14 as ep
    ep.apart(a, b)      # True where two blocks can be SHOWN to be > SEP apart
    ep.EPOCHS[eb]       # the measured epoch where one survives, else the stored
    ep.MS, ep.VB        # the two witnesses, for a caller that wants to report
    ep.SHARED, ep.WRONG # the defect itself, for a caller that measures it

    python3 epochs_r14.py --selftest
"""
import collections
import itertools
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))

#: the paper's own definition of an independent epoch, in days
SEP = 1.0
#: km/s on the barycentric witness; CALIBRATED below, never chosen
BARY_TOL = 1.5


def _load(*p):
    with open(os.path.join(HERE, *p), encoding='utf-8') as fh:
        return json.load(fh)


_CAT_ROWS = None


def _cat():
    global _CAT_ROWS
    if _CAT_ROWS is None:
        import csv
        with open(os.path.join(HERE, 'per_target_results_v3.99.csv'),
                  encoding='utf-8') as fh:
            _CAT_ROWS = list(csv.DictReader(fh))
    return _CAT_ROWS


# --------------------------------------------------------------- the stamps
_STORED = _load('epochs_v386.json')
#: the stored stamp per block, and where it came from.  KEPT, because the
#: defect has to be measurable and because 263 of the 404 blocks have no other
#: witness at all; `apart()` uses it only when it cannot be the OUS value.
MJD = _STORED['mjd']
SRC = _STORED['source']

# ------------------------------------------------- witness 1: the measurement sets
_MS = {}
for _src_name in (('r10inputs', 'recur_v411.json'),
                  ('r11inputs', 'events', 'recur_holdout.json')):
    for _v in _load(*_src_name)['crossings'].values():
        _d = _v.get('discovery') or {}
        if _d.get('t_start_mjdsec'):
            _MS.setdefault(_v['eb'], set()).add(_d['t_start_mjdsec'] / 86400.0)
        for _b in _v.get('blocks') or []:
            if _b.get('t_start_mjdsec'):
                _MS.setdefault(_b['eb'], set()).add(
                    _b['t_start_mjdsec'] / 86400.0)
#: a block read out of two measurement sets with two different start times
#: would make every interval through it arbitrary; the callers assert on this.
MS_MULTI = {k: sorted(v) for k, v in _MS.items() if len(v) > 1}
MS = {k: min(v) for k, v in _MS.items()}

# -------------------------------------- witness 2: each block's own barycentric term
_VBW = collections.defaultdict(list)
for _k, _v in _load('r8inputs', 'bary_v405.json')['v_bary_kms'].items():
    _VBW[_k.split('|')[0]].append(_v)
#: the largest spread of the term across the windows of one block.  The term is
#: a property of the block; if this were not small the witness would be a
#: property of the window and could not separate blocks at all.
VB_SPREAD = max(max(v) - min(v) for v in _VBW.values())
VB = {k: sum(v) / len(v) for k, v in _VBW.items()}

# ----------------------------------------------------------- the defect, measured
_BY_STAMP = collections.defaultdict(list)
for _k, _v in MJD.items():
    _BY_STAMP[_v].append(_k)
#: blocks sharing a stamp with at least one other block
SHARED = sorted(k for v, ks in _BY_STAMP.items() if len(ks) > 1 for k in ks)
NSTAMP = len(_BY_STAMP)
#: (block, stored, measured) wherever both exist, and the subset that disagree
CMP = [(e, MJD[e], MS[e]) for e in MS if e in MJD]
WRONG = [z for z in CMP if abs(z[1] - z[2]) > 0.05]
WORST_D = max(abs(z[1] - z[2]) for z in WRONG) if WRONG else 0.0

# ------------------------------------------- calibrating the barycentric witness
_WITHIN, _NTRUE, _NFALSE = [], 0, 0
_bysys = collections.defaultdict(set)
for _r in _cat():
    _bysys[_r['system_id']].add(_r['eb'])
for _sid, _ebs in _bysys.items():
    for _a, _b in itertools.combinations(
            sorted(e for e in _ebs if e in MS and e in VB), 2):
        _dt, _dvb = abs(MS[_a] - MS[_b]), abs(VB[_a] - VB[_b])
        if _dt <= SEP:
            _WITHIN.append(_dvb)
        if _dvb > BARY_TOL:
            _NTRUE += 1 if _dt > SEP else 0
            _NFALSE += 0 if _dt > SEP else 1
WITHIN = _WITHIN
WITHIN_MAX = max(_WITHIN)
NTRUE, NFALSE = _NTRUE, _NFALSE
NPAIR = NTRUE + NFALSE + len(WITHIN)


def apart(a, b):
    """True where two blocks can be SHOWN to be more than `SEP` days apart.

    One-sided: it never concludes that two blocks were simultaneous.  Three
    witnesses in order of authority -- the measurement sets, the barycentric
    term, and last the stored stamp, which is trusted only when the two blocks
    do not share it (a shared stamp is the OUS artefact itself).
    """
    if a in MS and b in MS and abs(MS[a] - MS[b]) > SEP:
        return True
    if a in VB and b in VB and abs(VB[a] - VB[b]) > BARY_TOL:
        return True
    if (a in MJD and b in MJD and abs(MJD[a] - MJD[b]) > SEP
            and MJD[a] != MJD[b]):
        return True
    return False


def apart_above(a, b, sep):
    """True where two blocks can be SHOWN to be more than `sep` days apart,
    for a `sep` the barycentric witness cannot resolve.

    The witness moves about 60 km/s over a year, so above a few days it cannot
    say how MUCH two blocks are separated by, only that they are.  For the
    paper's second threshold -- a year -- the epochs themselves are therefore
    the only witness, measured where a measurement set survives.  ★ Two blocks
    whose only witness is a stored stamp THEY SHARE are not two epochs: that
    shared stamp is the member-OUS artefact itself.
    """
    ta, tb = epoch(a), epoch(b)
    if ta is None or tb is None:
        return False
    if a not in MS and b not in MS and MJD.get(a) == MJD.get(b):
        return False
    return abs(ta - tb) > sep


def separated(ebs, sep=SEP):
    """True where some pair of these blocks is demonstrably more than `sep`
    days apart.  One-sided at every threshold."""
    ebs = sorted(set(ebs))
    if len(ebs) < 2:
        return False
    if sep <= SEP:
        return any(apart(a, b) for a, b in itertools.combinations(ebs, 2))
    return any(apart_above(a, b, sep)
               for a, b in itertools.combinations(ebs, 2))


def epoch(eb):
    """The best epoch available for one block: the measurement set where one
    survives, the stored stamp otherwise, `None` if neither."""
    if eb in MS:
        return MS[eb]
    return MJD.get(eb)


#: the measured epoch where one survives, the stored stamp elsewhere.  A
#: caller that needs an interval should prefer `apart()`, which does not have
#: to trust a stored stamp at all; `EPOCHS` is for binning and for reporting.
EPOCHS = {e: epoch(e) for e in set(MJD) | set(MS) if epoch(e) is not None}


def gap_days(ebs):
    """The largest gap between consecutive epochs of a set of blocks, on the
    best epoch available for each.  `None` where fewer than two are known."""
    ts = sorted(t for t in (epoch(e) for e in ebs) if t is not None)
    if len(ts) < 2:
        return None
    return max(ts[i + 1] - ts[i] for i in range(len(ts) - 1))


def span_days(ebs):
    ts = sorted(t for t in (epoch(e) for e in ebs) if t is not None)
    return (ts[-1] - ts[0]) if len(ts) >= 2 else None


def classify(ebs):
    """The paper's five-way temporal class for one system's blocks, on the
    measured epochs and the calibrated witness.

      one      -- a single block, so no separation can exist
      sameday  -- more than one block, none of them SHOWN to be separated
      days / months / years -- separated, binned by the measured span

    ★ `sameday` is "not shown to be separated", not "simultaneous": the
    witness is one-sided, so this class is an UPPER bound on itself.
    """
    ebs = sorted(ebs)
    if len(ebs) < 2:
        return 'one'
    if not any(apart(a, b) for a, b in itertools.combinations(ebs, 2)):
        return 'sameday'
    sp = span_days(ebs)
    if sp is None or sp < 30:
        return 'days'
    if sp < 365:
        return 'months'
    return 'years'


def split(groups):
    """`classify` over a mapping of system -> set of blocks."""
    cc = collections.Counter()
    for _k, _ebs in groups.items():
        cc[classify(_ebs)] += 1
    return cc


def _selftest():
    ok = True

    def say(tag, cond, detail):
        print('  %-62s %s  %s' % (tag, 'OK' if cond else 'WRONG', detail))
        return cond

    ok &= say('E1 no block is read out of two different start times',
              not MS_MULTI, '%d blocks read from measurement sets' % len(MS))
    ok &= say('E2 the barycentric term is a property of the block',
              VB_SPREAD < 0.05,
              'largest spread within one block %.4f km/s' % VB_SPREAD)
    ok &= say('E3 the stored stamps disagree with the measurement sets '
              'wherever both exist', len(WRONG) > 0.5 * len(CMP),
              '%d of %d disagree, worst %.0f d; %d of %d share a stamp'
              % (len(WRONG), len(CMP), WORST_D, len(SHARED), len(MJD)))
    ok &= say('E4 the witness never falsely separates two blocks taken '
              'within a day',
              NFALSE == 0 and NTRUE > 100 and WITHIN_MAX < 0.5 * BARY_TOL,
              '%d separated, %d falsely; largest within-day difference '
              '%.2f km/s against %.1f' % (NTRUE, NFALSE, WITHIN_MAX,
                                          BARY_TOL))
    #: the predicate must be one-sided: a block cannot be apart from itself,
    #: and a pair neither witness covers must come back False rather than
    #: raise or guess.
    _e = sorted(MS)[0]
    ok &= say('E5 the predicate is reflexive-false and total',
              not apart(_e, _e) and not apart('nosuchblock', 'nosuchother'),
              'apart(e, e) False; an unknown pair is False, not an error')
    #: and it must actually fire, or every caller is measuring nothing
    _n = sum(1 for a, b in itertools.combinations(sorted(MS)[:60], 2)
             if apart(a, b))
    ok &= say('E6 the predicate fires on real data', _n > 100,
              '%d of the first 60 blocks\' pairs are separable' % _n)
    return 0 if ok else 1


if __name__ == '__main__':
    if '--selftest' in sys.argv:
        raise SystemExit(_selftest())
    print('epochs_r14: %d stored stamps, %d measured, %d shared, %d wrong'
          % (len(MJD), len(MS), len(SHARED), len(WRONG)))
