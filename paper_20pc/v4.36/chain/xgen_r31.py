#!/usr/bin/env python3
r"""Round 3120: WHICH CODE MADE THE PRODUCTS, AND WHAT RUNNING THE EARLIER CODE AGAIN SHOWS.

Some windows' products were made before the extractor and the search reached
their deposited form (blocks that were not recalibrated).  The earlier code is
in the deposit (code/pipeline/**/earlier/, zverify V12/V13), with a table of
which generation made each window's product (catalogues/window_code_generations.csv)
and the reproduction run (statistics/extractor_reproduction.csv).  This
generator publishes the counts the Data Availability sentence quotes, from the
same three frozen records zdeposit.py reads (r31inputs/20261105/):

  windows_version.json  r29-extract's per-window code generation (census join)
  cmp_Nall.json         the earlier code re-run on 9 freshly calibrated blocks
  versions_meta.json    the generations and their SHA-256
  and the array of each re-run block, from r29-extract's blockmeta.json,
  frozen below in CMP_ARRAYS (9 blocks).

X1 the census counts partition the census (E1 + E2 + E3 + unmatched = all);
X2 the earlier code reproduces every archived reading it was run on to the
   printed bound (|dT| < 1e-4, the bound printed is the maximum rounded up);
X3 the deposited extractor changes the statistic more on 12 m than on 7 m.

    python3 xgen_r31.py [--drive N]
"""
import collections
import json
import math
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROUND = 3120
D = os.path.join(HERE, 'r31inputs', '20261105')
DRIVE = None
for _i, _a in enumerate(sys.argv):
    if _a == '--drive':
        DRIVE = int(sys.argv[_i + 1])
OUT_TEX = os.path.join(HERE, 'numbers/survey_numbers_round3120.tex' if DRIVE is None
                       else 'numbers/survey_numbers_round3120_drive%d.tex' % DRIVE)

#: the array of each block of the reproduction sample (r29-extract blockmeta.json, frozen here)
CMP_ARRAYS = {
    'A002_X1119e64_X27e3': '12m', 'A002_X12235df_X7876': '12m', 'A002_X126787e_X1170': '7m',
    'A002_Xb999fd_X148': '7m', 'A002_Xcd97a1_X2377': '7m', 'A002_Xd3607d_X6487': '12m',
    'A002_Xd6ebab_X41a3': '12m', 'A002_Xd99ff3_X9611': '12m', 'A002_Xe4f0a6_X3658': '12m',
}

OUT, fail = [], []


def m(name, val):
    assert name.isalpha(), name
    OUT.append('\\newcommand{\\%s}{%s}' % (name, val))


def ck(label, cond, detail=''):
    print('  %-70s %s  %s' % (label[:70], 'PASS' if cond else 'FAIL', detail))
    if not cond:
        fail.append(label)


def sci1(x):
    """x rounded UP to one significant figure, as TeX."""
    e = int(math.floor(math.log10(x)))
    mnt = math.ceil(x / 10.0 ** e - 1e-12)
    if mnt == 10:
        mnt, e = 1, e + 1
    return r'%d\times10^{%d}' % (mnt, e)


WV = json.load(open(os.path.join(D, 'windows_version.json')))
CMP = json.load(open(os.path.join(D, 'cmp_Nall.json')))
META = json.load(open(os.path.join(D, 'versions_meta.json')))

cen = [w for w in WV if w['set'] == 'census']
cs = collections.Counter(w['gen_stat'] for w in cen)
cl = collections.Counter(w['gen_limit'] for w in cen)
ck('X1 the census windows partition by the generation of their statistic and of their limit',
   sum(cs.values()) == sum(cl.values()) == len(cen) and set(cs) | set(cl) <= {'E1', 'E2', 'E3', 'unmatched'},
   'stat %s, limit %s' % (dict(cs), dict(cl)))

missing = sorted({x['eb'] for x in CMP} - set(CMP_ARRAYS))
assert not missing, ('reproduction blocks without an array', missing)
rep, chg = [], collections.defaultdict(list)
for x in CMP:
    g = x['window']['gen']
    for k, v in x['variants'].items():
        if k.startswith(g + 's'):
            rep.append(abs(v['T'] - x['arch']['T']))
    v3 = x['variants'].get('E3sfinal')
    if v3:
        chg[CMP_ARRAYS[x['eb']]].append(abs(v3['T'] - x['arch']['T']))
rmax = max(rep)
if DRIVE == 1:
    rmax = 0.01
ck('X2 the earlier code reproduces every archived reading it was run on', rmax < 1e-4,
   '%d readings in %d windows, %d blocks, max |dT| %.3g' % (len(rep), len(CMP), len({x['eb'] for x in CMP}), rmax))
ck('X3 the deposited extractor changes the statistic more on 12 m than on 7 m',
   max(chg['12m']) > max(chg['7m']), 'max |dT| 12 m %.3f, 7 m %.3f' % (max(chg['12m']), max(chg['7m'])))

m('XgNWinStatEarly', '%d' % (cs['E1'] + cs['E2']))
m('XgNWinLimEarly', '%d' % (cl['E1'] + cl['E2']))
m('XgNWinStatEOne', '%d' % cs['E1'])
m('XgNWinStatETwo', '%d' % cs['E2'])
m('XgNWinAllStatEarly', '%d' % sum(1 for w in WV if w['gen_stat'] in ('E1', 'E2')))
m('XgReproNWin', '%d' % len(CMP))
m('XgReproNBlk', '%d' % len({x['eb'] for x in CMP}))
m('XgReproNRead', '%d' % len(rep))
m('XgReproMaxdT', sci1(rmax))
m('XgDTSevenMax', '%.2f' % max(chg['7m']))
m('XgDTTwelveMax', '%.2f' % max(chg['12m']))
# ★ v4.33 (the extractor fold): WHAT BECAME OF THE PRIORITY RE-EXTRACTION, from the frozen record of the lanes
# that ran it (r33inputs/20261107/extract_status_r33.json, made by mk_xstatus33.py after the lanes drained: every
# block planned for re-extraction with the final extractor on ALMA's flags, and for each one not re-extracted its
# measured reason).
#   X4 the record is final (nothing pending) and every block is re-extracted or carries a measured reason;
#   X5 every window of a re-extracted block is read from a final-extractor product in the generation record
#      (a finished block the harvest dropped -- the defect that kept X2b17's pre-repair product in v4.29 -- fires);
#   X6 every window of a block NOT re-extracted keeps an earlier extractor's product (the declared ones are real).
XS = json.load(open(os.path.join(HERE, 'r33inputs', '20261107', 'extract_status_r33.json')))
if DRIVE == 4:                      # a record made before the lanes drained
    XS = dict(XS, interim=True, pending=['A002_drive_pending'])
_xb = XS['blocks']
_wvb = collections.defaultdict(list)
for w in WV:
    _wvb[w['eb']].append(w)
_done = [b for b in _xb if b['status'] == 're-extracted']
_not = [b for b in _xb if b['status'] == 'not_re_extracted']
_REASONS = ('legacy_replay', 'flags_need_nonlazy', 'flags_unrestorable', 'disk_abort', 'calibration_failed',
            'not_reached')
ck('X4 the re-extraction record is final and every block is re-extracted or carries a measured reason',
   not XS['interim'] and not XS['pending'] and len(_done) + len(_not) == len(_xb)
   and all(b.get('reason_class') in _REASONS and b.get('why') for b in _not),
   '%d blocks: %d re-extracted, %d not (%s); pending %s' % (
       len(_xb), len(_done), len(_not),
       dict(collections.Counter(b['reason_class'] for b in _not)), XS['pending']))
if DRIVE == 5:                      # one window of a re-extracted block left on its earlier product
    _w0 = _wvb[_done[0]['eb']][0]
    _wvb[_done[0]['eb']][0] = dict(_w0, gen_stat='E1')
if DRIVE == 6:                      # one window of a declared block that is in fact on the final extractor
    _w0 = _wvb[_not[0]['eb']][0]
    _wvb[_not[0]['eb']][0] = dict(_w0, gen_stat='E3')
_x5 = [b['eb'] for b in _done if not _wvb.get(b['eb'])
       or any(w['gen_stat'] != 'E3' or w['gen_limit'] != 'E3' for w in _wvb[b['eb']])]
ck('X5 every window of a re-extracted block is read from a final-extractor product', not _x5,
   '%d re-extracted blocks, %d windows; offending %s' % (len(_done), sum(len(_wvb[b['eb']]) for b in _done), _x5))
_x6 = [b['eb'] for b in _not if not _wvb.get(b['eb']) or any(w['gen_stat'] == 'E3' for w in _wvb[b['eb']])]
ck('X6 every window of a block not re-extracted keeps an earlier extractor product', not _x6,
   '%d blocks, %d windows; offending %s' % (len(_not), sum(len(_wvb[b['eb']]) for b in _not), _x6))
_W = {1: 'one', 2: 'two', 3: 'three', 4: 'four', 5: 'five', 6: 'six', 7: 'seven', 8: 'eight', 9: 'nine',
      10: 'ten', 11: 'eleven', 12: 'twelve'}
_cnt = collections.Counter(b['reason_class'] for b in _not)
m('XgNBlkPlan', '%d' % len(_xb))
m('XgNBlkReDone', '%d' % len(_done))
m('XgNBlkNotRe', '%d' % len(_not))
m('XgNWinNotRe', '%d' % sum(len(_wvb[b['eb']]) for b in _not))
for _k, _nm in (('legacy_replay', 'Legacy'), ('flags_need_nonlazy', 'Nonlazy'), ('flags_unrestorable', 'PfNone'),
                ('disk_abort', 'DiskAbort'), ('calibration_failed', 'CalFail'), ('not_reached', 'NotReached')):
    m('XgNBlk' + _nm, '%d' % _cnt.get(_k, 0))
# ★ the reasons as ONE generated clause, so a reason that occurs zero times is not printed as "zero blocks ..." and
# a count word always agrees with its verb (prosenum reads count words): the Data Availability sentence cites it.
_PH = (('legacy_replay', 'older block would need its whole calibration replayed',
        'older blocks would need their whole calibration replayed'),
       ('flags_need_nonlazy', "restores ALMA's flags only through an import several times larger than the raw data",
        "restore ALMA's flags only through an import several times larger than the raw data"),
       ('flags_unrestorable', 'has flag tables that cannot be restored at all',
        'have flag tables that cannot be restored at all'),
       ('disk_abort', 'needed more disk than was available on every import tried',
        'needed more disk than was available on every import tried'),
       ('calibration_failed', 'failed to calibrate on the import that fits the disk',
        'failed to calibrate on the import that fits the disk'),
       ('not_reached', 'finished its recalibration only after this analysis was closed and is not included',
        'finished their recalibration only after this analysis was closed and are not included'))
_parts = ['%s %s' % (_W.get(_cnt[_k], '%d' % _cnt[_k]), _one if _cnt[_k] == 1 else _many)
          for _k, _one, _many in _PH if _cnt.get(_k)]
assert sum(_cnt.values()) == len(_not)
m('XgNotReClause', (', '.join(_parts[:-1]) + ' and ' + _parts[-1]) if len(_parts) > 1 else (_parts[0] if _parts else 'none'))

m('XgNGenExtract', '%d' % sum(1 for v in META if v['stage'] == 'extraction' and v['tag'] != 'E3'))
m('XgNGenSearch', '%d' % sum(1 for v in META if v['stage'] == 'search' and v['tag'] != 'final'))

if fail:
    print('\nFAILED: %s' % '; '.join(fail))
    if DRIVE is None:
        raise SystemExit(1)
hdr = ['%% GENERATED by xgen_r31.py (round %d) -- do not hand-edit.' % ROUND,
       '% The code that made each product and the earlier code run again.']
open(OUT_TEX, 'w').write('\n'.join(hdr + sorted(OUT)) + '\n')
print('xgen_r31: %d macros -> %s' % (len(OUT), os.path.basename(OUT_TEX)))
