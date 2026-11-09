#!/usr/bin/env python3
r"""Round 3210 (r32, R1-2): WHICH STATISTIC EVERY CROSSING ENTERS, CHECKED AGAINST THE PRINTED COUNTS.

The referee: HD 139084 B is one of the census crossings and yet "enters neither side" -- the accounting was
not shown.  `chance_v414.py` (A32) now writes every ledger row and every hold-out trigger event, with the
statistics it enters, to `membership_r32.json` (deposited by `zdeposit.py` as
statistics/event_membership.csv).  This generator runs AFTER the generators that print the counts and
requires every printed count to be the size of its set in that table:

  M1  census crossings              = \CsNCross      (rows with event 'census')
  M2  attributed census crossings   = \MkNCoinc      (attributed)
  M3  with evidence beyond the coincidence = \LnAttrSupp  (linesupport_r18.json rows with a route, joined
      to the attributed rows on block and frequency; every supported row must be an attributed census row)
  M4  the observed side of the chance comparison = \CeObs, and it is exactly the eligible rows
      (unattributed, not atmospheric, Class A, position catalogued, own unit on the expected side)
  M5  archival-tail crossings = \CeNTailCross, none on either side; hold-out trigger events = \StHoObs,
      none in a census statistic
  M6  every census crossing at a position the catalogue does not tabulate is on NEITHER side, whatever its
      attribution, and the window it lies in enters the expectation only through the catalogued unit

Macros (for the one sentence of Sec. 2 / App. D.1; nothing typed):
  \MbNUncat, \MbNUncatWord      census crossings at an uncatalogued position (1 -> "one")
  \MbUncatStar                  the star of the first of them (HD~139084~B)
  \MbUncatHost                  the catalogued star whose unit carries its window (HD~139084)
  \MbUncatAttrWord              "attributed" / "unattributed" -- generated, so a fold cannot leave it wrong
  \MbUncatTrans, \MbUncatDv     its transition and stellar-frame offset (km/s, signed, integer) if attributed
  \MbNEvents                    rows of the deposited membership table

    python3 membership_r32.py [--drive N]   (N = 1..3 each fail; gate.sh runs them; a drive writes nothing)
      1  a comparison row dropped from the table (M4 must fail)
      2  the uncatalogued crossing put on the observed side (M4 and M6 must fail)
      3  the attributed count read off the unattributed rows (M2 must fail)
      4  one more system without a limit (M7 must fail)
  M7  (R2-1) \NSysClassA = \NSysA = \NSysALost + \OmNFlag + \NSysALimSum: every Class A system has no limit, an
      unbounded position, or a bounded limit, and the three add up
"""
import json
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
os.chdir(HERE)
import adopted_e90 as ae  # noqa: E402  (the macro layer reader, in \input order)

ROUND = 3210
DRIVE = None
for _i, _a in enumerate(sys.argv):
    if _a == '--drive':
        DRIVE = int(sys.argv[_i + 1])
OUT_TEX = os.path.join(HERE, 'numbers/survey_numbers_round3210.tex' if DRIVE is None
                       else 'numbers/survey_numbers_round3210_drive%d.tex' % DRIVE)
WORDS = ['no', 'one', 'two', 'three', 'four', 'five', 'six', 'seven', 'eight', 'nine', 'ten']
OUT, fail = [], []


def m(name, val):
    assert name.isalpha(), name
    assert not any(x.startswith('\\newcommand{\\%s}' % name) for x in OUT), name
    OUT.append('\\newcommand{\\%s}{%s}' % (name, val))


def ck(label, cond, detail=''):
    print('  %-74s %s  %s' % (label[:74], 'PASS' if cond else 'FAIL', detail))
    if not cond:
        fail.append(label.split()[0])


def tv(name):
    v = ae._texval(name)
    assert v is not None, 'no generator publishes \\%s' % name
    return v


def tvi(name):
    return int(re.sub(r'[^0-9]', '', tv(name)))


D = json.load(open(os.path.join(HERE, 'membership_r32.json')))
R = D['rows']
LED = json.load(open(os.path.join(HERE, 'ledger.json')))['rows']
LS = json.load(open(os.path.join(HERE, 'linesupport_r18.json')))['rows']

if DRIVE == 1:
    _k = next(j for j, r in enumerate(R) if r['in_comparison'])
    R = R[:_k] + R[_k + 1:]
if DRIVE == 2:
    for r in R:
        if r['event'] == 'census' and not r['position_catalogued']:
            r['in_comparison'] = True
            break

CEN = [r for r in R if r['event'] == 'census']
TAIL = [r for r in R if r['event'] == 'archival_tail']
HOLD = [r for r in R if r['event'] == 'holdout']
ATTR = [r for r in CEN if r['attributed']] if DRIVE != 3 else [r for r in CEN if not r['attributed']]
CMP = [r for r in R if r['in_comparison']]
ELIG = [r for r in CEN if r['in_unattributed'] and r['window_class'] == 'A' and r['position_catalogued']
        and r['unit_in_expectation']]
UNC = [r for r in CEN if not r['position_catalogued']]


def key(r):
    return (r['eb'], round(float(r['nu_topo_GHz']), 6))


ck('M1 the census crossings are the census rows of the table', len(CEN) == tvi('CsNCross')
   and len(CEN) + len(TAIL) == len(LED),
   '%d census rows (\\CsNCross %s), %d tail, %d ledger rows' % (len(CEN), tv('CsNCross'), len(TAIL), len(LED)))
ck('M2 the attributed census crossings are its attributed rows', len(ATTR) == tvi('MkNCoinc'),
   '%d attributed (\\MkNCoinc %s)' % (len(ATTR), tv('MkNCoinc')))
_akeys = {key(r) for r in CEN if r['attributed']}
_sup = [x for x in LS if x.get('routes')]
_supk = {(x['eb'], round(float(x['freq']), 6)) for x in _sup}
ck('M3 the attributed crossings with evidence beyond the coincidence are attributed census rows',
   len(_supk) == len(_sup) == tvi('LnAttrSupp') and _supk <= _akeys,
   '%d supported (\\LnAttrSupp %s), all attributed census rows: %s'
   % (len(_sup), tv('LnAttrSupp'), _supk <= _akeys))
ck('M4 the observed side is exactly its eligible rows and is \\CeObs',
   [key(r) for r in CMP] == [key(r) for r in ELIG] and len(CMP) == tvi('CeObs') == D['n_observed'],
   '%d comparison, %d eligible, \\CeObs %s' % (len(CMP), len(ELIG), tv('CeObs')))
ck('M5 the tail and hold-out events are counted where printed and enter no census statistic',
   len(TAIL) == tvi('CeNTailCross') and not any(r['in_comparison'] or r['window_catalogued'] for r in TAIL)
   and len(HOLD) == tvi('StHoObs') and not any(r['in_comparison'] for r in HOLD),
   '%d tail (\\CeNTailCross %s), %d hold-out (\\StHoObs %s)'
   % (len(TAIL), tv('CeNTailCross'), len(HOLD), tv('StHoObs')))
ck('M6 a crossing at an uncatalogued position is on neither side; its window enters only through the '
   'catalogued unit',
   all(not r['in_comparison'] and not r['unit_in_expectation'] and r['window_catalogued']
       and r['window_catalogue_star'] for r in UNC),
   '; '.join('%s %s: %s, window via %s, expectation %s'
             % (r['star'], r['eb'], ('attributed ' + r['transition']) if r['attributed'] else 'unattributed',
                r['window_catalogue_star'], r['window_in_expectation']) for r in UNC) or 'none')

# R2-1: the systems of the carrier search are one partition -- no limit, an unbounded position, or bounded.
_nlost = tvi('NSysALost') if DRIVE != 4 else tvi('NSysALost') + 1
ck('M7 the Class A systems = no limit + unbounded position + bounded limit (61 = 1 + 3 + 57 in v4.32)',
   tvi('NSysClassA') == tvi('NSysA') == _nlost + tvi('OmNFlag') + tvi('NSysALimSum'),
   '\\NSysClassA %s, \\NSysA %s = \\NSysALost %d (%s) + \\OmNFlag %s + \\NSysALimSum %s'
   % (tv('NSysClassA'), tv('NSysA'), _nlost, tv('NSysALostName'), tv('OmNFlag'), tv('NSysALimSum')))

if fail:
    print('\nFAILED: %s' % '; '.join(fail))
    raise SystemExit(1)
if DRIVE is not None:
    print('drive %d did not fire' % DRIVE)
    raise SystemExit(0)

try:
    import star_alias
    _des = star_alias.designation
except Exception:
    def _des(s):
        return s


def tex_star(s):
    return _des(s).replace(' ', '~')


m('MbNEvents', '%d' % len(R))
m('MbNUncat', '%d' % len(UNC))
m('MbNUncatWord', WORDS[len(UNC)] if len(UNC) < len(WORDS) else '%d' % len(UNC))
if UNC:
    u = UNC[0]
    led = [x for x in LED if x['eb'] == u['eb'] and abs(float(x['freq']) - u['nu_topo_GHz']) < 1e-6]
    assert len(led) == 1, led
    m('MbUncatStar', led[0]['display'])
    m('MbUncatHost', tex_star(u['window_catalogue_star']))
    m('MbUncatAttrWord', 'attributed' if u['attributed'] else 'unattributed')
    m('MbUncatTrans', led[0]['line_tex'] if u['attributed'] else '--')
    m('MbUncatDv', ('%+.0f' % u['dv_star_kms']).replace('-', '$-$') if u['attributed'] else '--')
hdr = ['%% GENERATED by membership_r32.py (round %d) -- do not hand-edit.' % ROUND,
       '% Which statistic every crossing enters (statistics/event_membership.csv), checked against the counts.']
open(OUT_TEX, 'w').write('\n'.join(hdr + sorted(OUT)) + '\n')
print('membership_r32: %d events, %d macros -> %s' % (len(R), len(OUT), os.path.basename(OUT_TEX)))
