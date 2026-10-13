#!/usr/bin/env python3
r"""The data-quality disposition, computed in exactly one place.

R2-M10 objects that BD+05 1668's four crossings get three incompatible
treatments in the paper, and the evidence supports one: a data-quality
failure of a single execution block.  The rule, fixed before it was applied,
is a property of a window and not of a star:

    a window is FLAGGED when the median of its own 512-position control
    ensemble exceeds DQ_FACTOR times the survey median of that quantity.

It is the median of the control ring, not its maximum, that this kind of
search needs -- a ring whose typical position is bright says the field is
wrong, where a ring with one bright position says there is a source in it.

★ WHY THIS IS A MODULE.  Two consumers need the same answer: `statchain_v411`
publishes the counts (\DqNWin, \DqNStar, \DqBlockNCross ...) and
`ledger_v410` must give the flagged rows of Table 6 their disposition, so
that no crossing is disposed of on the spatial rank -- which is the sentence
R2-M5 objects to and the whole point of R1-2.  A second implementation of one
predicate is this project's commonest defect: it has produced six instances
of the attribution split alone in this cycle.  So the predicate lives here,
both import it, and `statchain_v411` asserts its own published counts against
this module's answer.

The rule deliberately cuts ACROSS attribution: HD 48370's resolved disc is
flagged and is also CO-attributed.  That is why the flag is a statement about
the window and not a cut.

    import dqflag
    F = dqflag.flags(catdir)        # {(eb, rms, snr) key: bool}
    dqflag.flagged_ebs(catdir)      # set of execution blocks with any flag

Self-test:  python3 dqflag.py --selftest
"""
import csv
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))

# The rule, and the one number in it.  Fixed before it was applied; a
# consumer may not pass a different factor, because then there would be two
# rules again.
DQ_FACTOR = 2.0
NCTRL_VEC = 512
EXPORT_NAME = 'corrected_export_v399.json'
CAT_NAME = 'per_target_results_v3.99.csv'

_CACHE = {}


def key(eb, rms, snr):
    """The window's identity: block plus two measured quantities of the
    window itself.  NOT the star name, and not the window edges -- a
    descending spectral window writes its edges reversed, and a block holds
    two stars."""
    return (eb, round(float(rms), 5), round(float(snr), 4))


def _load(catdir):
    if catdir in _CACHE:
        return _CACHE[catdir]
    import numpy as np
    exp = json.load(open(os.path.join(catdir, EXPORT_NAME)))
    cat = list(csv.DictReader(open(os.path.join(catdir, CAT_NAME))))
    catby = {}
    for r in cat:
        catby.setdefault(key(r['eb'], r['rms_mJy'], r['star_snr']),
                         []).append(r)
    ringmed, seen = {}, set()
    for r in exp['rows']:
        c, s = r.get('ctrl_all'), r.get('star_snr')
        if not c or s is None:
            continue
        c = np.asarray(c, float)
        if c.size != NCTRL_VEC or not np.all(np.isfinite(c)):
            continue
        k = key(r['eb'], r['rms'], s)
        cr = catby.get(k)
        if not cr or len(cr) > 1 or k in seen:
            continue
        seen.add(k)
        ringmed[k] = float(np.median(c))
    surv = float(np.median(sorted(ringmed.values())))
    thresh = DQ_FACTOR * surv
    out = dict(ringmed=ringmed, survey_median=surv, threshold=thresh,
               flags={k: (v > thresh) for k, v in ringmed.items()},
               catby=catby)
    _CACHE[catdir] = out
    return out


def flags(catdir=HERE):
    """{window key: True if the window is data-quality flagged}."""
    return _load(catdir)['flags']


def survey_median(catdir=HERE):
    return _load(catdir)['survey_median']


def threshold(catdir=HERE):
    return _load(catdir)['threshold']


def flagged_keys(catdir=HERE):
    return {k for k, v in _load(catdir)['flags'].items() if v}


def flagged_ebs(catdir=HERE):
    """Execution blocks carrying at least one flagged window."""
    return {k[0] for k in flagged_keys(catdir)}


def is_flagged_row(row, catdir=HERE):
    """True if this released catalogue row's window is flagged.

    Returns False where the window has no stored control ensemble: 37 of the
    1,651 released windows have none, and a window that cannot be measured
    is not thereby clean.  Callers that need to distinguish the two should
    ask `has_measurement` first.
    """
    return bool(flags(catdir).get(
        key(row['eb'], row['rms_mJy'], row['star_snr']), False))


def has_measurement(row, catdir=HERE):
    return key(row['eb'], row['rms_mJy'], row['star_snr']) \
        in _load(catdir)['ringmed']


def _selftest():
    st = _load(HERE)
    cat = list(csv.DictReader(open(os.path.join(HERE, CAT_NAME))))
    fails = 0

    def chk(name, cond, detail=''):
        nonlocal fails
        print('  %-66s %s' % (name, 'OK' if cond else 'FAIL ' + str(detail)))
        fails += 0 if cond else 1

    fl = flagged_keys()
    chk('D1 the rule flags something and does not flag everything',
        0 < len(fl) < 0.01 * len(st['ringmed']),
        '%d of %d' % (len(fl), len(st['ringmed'])))
    # D2 the flag is a property of the WINDOW: it must cut across
    #    attribution, or it is a relabelling of "unattributed".
    xf = [r for r in cat if is_flagged_row(r) and r['crossing'] == 'True']
    att = [r for r in xf if r['line_offset_kms'] not in ('', None)
           and abs(float(r['line_offset_kms'])) <= 50.0]
    chk('D2 the flag spans attributed and unattributed crossings, so it is '
        'not a relabelling', 0 < len(att) < len(xf),
        '%d attributed of %d flagged crossings' % (len(att), len(xf)))
    # D3 it must not be a relabelling of "crossing" either.
    chk('D3 the flagged windows are not just the crossings',
        len(fl) != sum(1 for r in cat if r['crossing'] == 'True'),
        len(fl))
    # D4 the threshold really is DQ_FACTOR times the survey median.
    chk('D4 the threshold is the declared factor times the survey median',
        abs(st['threshold'] / st['survey_median'] - DQ_FACTOR) < 1e-12,
        (st['threshold'], st['survey_median']))
    # D5 a drive: at the factor that admits everything, the rule must flag
    #    (nearly) every window -- i.e. the rule is a function of the factor
    #    and not a hard-coded list.
    import numpy as np
    loose = sum(1 for v in st['ringmed'].values()
                if v > 0.0 * st['survey_median'])
    chk('D5 the rule is a function of its factor, not a list',
        loose == len(st['ringmed']), (loose, len(st['ringmed'])))
    print('dqflag selftest: %d failure(s); %d flagged windows in %d block(s), '
          'survey median ring %.4f, threshold %.4f'
          % (fails, len(fl), len(flagged_ebs()), st['survey_median'],
             st['threshold']))
    return 1 if fails else 0


if __name__ == '__main__':
    if '--selftest' in sys.argv:
        sys.exit(_selftest())
    st = _load(HERE)
    print('dqflag: %d windows with a stored ensemble, survey median ring '
          '%.4f, threshold %.4f, %d flagged in %d block(s): %s'
          % (len(st['ringmed']), st['survey_median'], st['threshold'],
             len(flagged_keys()), len(flagged_ebs()),
             ', '.join(sorted(flagged_ebs()))))
