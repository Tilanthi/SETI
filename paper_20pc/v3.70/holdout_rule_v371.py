#!/usr/bin/env python3
r"""PRE-REGISTERED CALIBRATION HOLD-OUT RULE.

Fixed and committed 2026-09-14, BEFORE the archive sweep completed and before
any of the reserved blocks was searched.  A hold-out chosen after seeing results
is not a hold-out; the point of this file is that it is timestamped in the
repository ahead of the data.

WHY A HOLD-OUT IS NEEDED
------------------------
Every empirically calibrated statement in the paper is licensed by a sample the
design never saw: the rank displacement (median add-one rank 0.425 against 0.5),
the measured false-alarm tail factor (about 1.4, empirical range 1.1-2.2), the
radial profile m(u), and the argument that stage-1 status carries no candidate
significance on its own.  Folding every block into one release would make all of
those in-sample, which is exactly the objection referee 1 raised against the
radial repair.

THE RULE
--------
The unit is the EXECUTION BLOCK, because that is the unit the paper's own
false-alarm accounting resamples: blocks share weather, calibration and
correlator setup, and the clustered bootstrap of `tailboot_v370.py` resamples
whole blocks.  Holding out at the block level therefore matches the independence
model already in use, and -- unlike holding out whole systems -- it costs the
survey no targets.

    h    = sha256(canonical execution-block UID).hexdigest()
    n    = int(h[:8], 16)
    HELD OUT  iff  n mod 5 == 0            (a nominal 20 per cent)

Canonical UID form is `uid://A002/Xnnnn/Xnnnn`; the underscored form used in
filenames is normalised to it first, so the assignment cannot depend on which
spelling a given file happens to use.

TWO GUARDS, BOTH FIXED IN ADVANCE
---------------------------------
(1) Blocks already in the v3.70 released catalogue are ALWAYS survey blocks.
    They are published; they cannot be un-published, and 11 of the 104 fall on
    the hold-out residue by chance.  This carve-out depends only on which
    blocks were already released -- a fact fixed before this rule was written --
    and on no measurement.
(2) If every block of a system would be held out, the block with the LOWEST n is
    released back to the survey, so no system is lost from the headline sample.
Both guards are deterministic and depend only on UIDs and the published list.

WHAT THE HOLD-OUT MAY AND MAY NOT BE USED FOR
---------------------------------------------
May: measuring the rank distribution, the pseudo-star first-rank rate, the tail
factor, the radial profile m(u), and the rate of unattributed single-epoch
events.
May NOT: contributing to the headline window/star/system counts, the frequency
union, the EIRP limits, or any candidate disposition.

Usage:  python3 holdout_rule_v371.py <uid-or-eb> ...      -> per-block verdict
        python3 holdout_rule_v371.py --assign blocks.json -> full assignment
"""
import hashlib, json, sys

MODULUS = 5          # nominal 20 per cent held out
RESIDUE = 0


def canonical(eb):
    """Normalise either spelling to `uid://A002/Xaaaa/Xbbbb`."""
    s = str(eb).strip()
    if s.startswith('uid://'):
        return s
    s = s.replace('___', '_')
    parts = [p for p in s.split('_') if p]
    if len(parts) >= 3:
        return 'uid://%s/%s/%s' % (parts[0], parts[1], parts[2])
    return s


def block_n(eb):
    h = hashlib.sha256(canonical(eb).encode()).hexdigest()
    return int(h[:8], 16)


def is_holdout(eb):
    return block_n(eb) % MODULUS == RESIDUE


def assign(blocks, published=()):
    """blocks: {eb: system_id}.  published: blocks already in the released
    catalogue, which are always survey blocks (guard 1).  Returns
    {eb: 'survey'|'holdout'} with both guards applied."""
    pub = {canonical(e) for e in published}
    out = {eb: ('survey' if canonical(eb) in pub
                else ('holdout' if is_holdout(eb) else 'survey'))
           for eb in blocks}
    bysys = {}
    for eb, sysid in blocks.items():
        bysys.setdefault(sysid, []).append(eb)
    for sysid, ebs in bysys.items():
        if all(out[e] == 'holdout' for e in ebs):
            keep = min(ebs, key=block_n)
            out[keep] = 'survey'
    return out


if __name__ == '__main__':
    if len(sys.argv) > 2 and sys.argv[1] == '--assign':
        blocks = json.load(open(sys.argv[2]))
        a = assign(blocks)
        n_h = sum(1 for v in a.values() if v == 'holdout')
        print('%d blocks: %d survey, %d hold-out (%.1f per cent)'
              % (len(a), len(a) - n_h, n_h, 100.0 * n_h / max(1, len(a))))
        json.dump(a, open('holdout_assignment_v371.json', 'w'), indent=1)
    else:
        for eb in sys.argv[1:]:
            print('%-28s n=%-12d %s' % (canonical(eb), block_n(eb),
                                        'HOLD-OUT' if is_holdout(eb) else 'survey'))
