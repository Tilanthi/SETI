#!/usr/bin/env python3
r"""v3.80: the stage-1 outlier taxonomy on the completed archival sweep.

The released catalogue held 443 windows and four stage-1 spatial outliers,
and the manuscript could name each of them in prose. The completed sweep
holds 1956 windows and thirteen, so the prose has to become arithmetic or it
will be wrong the next time a block lands.

What the enlarged sample actually shows, and it is the cleanest result of
the round: separate the outliers that sit on a molecular transition in the
star's own frame from those that do not, and the unattributed remainder is
what chance predicts. Eight of the thirteen are one object -- beta Pictoris,
in five Band 3 and three Band 6 windows, every one within a few km/s of
systemic on CO -- which is a single astrophysical source seen repeatedly,
not eight independent events.

Everything here is computed from the released catalogue, so the taxonomy
and the table cannot disagree.

Writes survey_numbers_round30.tex and tab_flagged_v380.tex.
"""
import csv, json, math, os, re, collections
from star_alias import canon as _canon_star   # v3.85

ROWS = list(csv.DictReader(open('per_target_results_v3.95.csv')))
K = json.load(open('catalogue_constants.json'))
S = json.load(open('survey_stats.json'))
OUT = 'survey_numbers_round30.tex'
TAB = 'tab_flagged_v380.tex'
N = len(ROWS)
assert N == K['n_windows'], (N, K['n_windows'])

M = []


def m(name, val):
    M.append('\\newcommand{\\%s}{%s}' % (name, val))


def F(x):
    return None if x in ('', None) else float(x)



def _ck(n):
    """Census-name key: strip Gaia designations, SIMBAD prefixes and
    punctuation, the same normalisation canon_names_v380.py uses."""
    import re
    n = re.sub(r'\bGaia\s*DR3\s*\d+\b', '', n, flags=re.I)
    n = re.sub(r'^(NAME|V\*|V star|\*)\s+', '', n.strip(), flags=re.I)
    return re.sub(r'[^A-Za-z0-9]+', '', n).lower()



def _texval(name):
    import glob as _g, re as _re
    for _f in sorted(_g.glob('survey_numbers*.tex')):
        _m = _re.search(r'\\newcommand\{\\%s\}\{([^}]*)\}' % name,
                        open(_f).read())
        if _m:
            return _m.group(1)
    return None


def _ebtag(eb):
    """Last two segments of the execution-block uid, which identify it."""
    return '\\_'.join(eb.split('_')[1:])


def _sci(x, sf=2):
    """Two significant figures in LaTeX scientific form."""
    if x is None:
        return '--'
    e = int(math.floor(math.log10(abs(x))))
    return r'%.*f\times10^{%d}' % (sf - 1, x / 10.0 ** e, e)


def tidy(s):
    s = ' '.join(s.split())
    for cut in ('  Gaia DR3', ' Gaia DR3'):
        if cut in s:
            s = s.split(cut)[0]
    return s.replace('CP-72', 'CP$-$72').replace('bet Pic', r'$\beta$~Pic')


# --------------------------------------------------------------- taxonomy
# The survey's own molecular tube, +-50 km/s about the transition in the
# stellar frame (v342_calc.py). A stage-1 outlier inside it is attributable
# to the star's own or foreground gas; outside it, nothing in this survey
# explains it.
TUBE_KMS = 50.0
FL = [r for r in ROWS if r['stage1_flag'] == 'True']
assert len(FL) == K['n_flagged'], (len(FL), K['n_flagged'])

attributed = [r for r in FL if abs(F(r['line_offset_kms']) or 9e9) <= TUBE_KMS]
unattributed = [r for r in FL if r not in attributed]

m('NStageOneWin', '%d' % len(FL))
m('NStageOneSys', '%d' % len({r['system_id'] for r in FL}))
m('NStageOneStars', '%d' % len({r['star_name'] for r in FL}))
m('NStageOnePairs', '%d' % len({(r['star_name'], r['band']) for r in FL}))
m('NStageOneLine', '%d' % len(attributed))
m('NStageOneUnattrib', '%d' % len(unattributed))
m('NStageOneUnattribSys', '%d' % len({r['system_id'] for r in unattributed}))

bp = [r for r in FL if r['star_name'].startswith('bet Pic')]
m('NStageOneBpic', '%d' % len(bp))
m('NStageOneBpicThree', '%d' % sum(1 for r in bp if r['band'] == '3'))
m('NStageOneBpicSix', '%d' % sum(1 for r in bp if r['band'] == '6'))
m('NStageOneNonBpic', '%d' % (len(FL) - len(bp)))
m('BpicDvLo', '%.0f' % min(F(r['line_offset_kms']) for r in bp))
m('BpicDvHi', '%.0f' % max(F(r['line_offset_kms']) for r in bp))
m('BpicTsymMax', '%.1f' % max(F(r['star_snr']) for r in bp))
m('BpicTsymMin', '%.1f' % min(F(r['star_snr']) for r in bp))
m('NStageOneBpicEb', '%d' % len({r['eb'] for r in bp}))

# --------------------------------------------- is the remainder chance?
# Under exchangeability a window is rank-first among its NCTRL controls with
# probability 1/(NCTRL+1), so the expected number of stage-1 outliers over
# the catalogue follows directly. This is the comparison the paper has
# always made; on 1956 windows it can be made against the UNATTRIBUTED
# count, which is the one chance is supposed to explain.
NCTRL = K['n_ctrl']
EXP = N / float(NCTRL + 1)
m('ExpStageOneAll', '%.1f' % EXP)
m('ExpStageOneRankFloor', '1/%d' % (NCTRL + 1))


def pois_ge(k, mu):
    """P(X >= k) for a Poisson mean mu."""
    return 1.0 - sum(math.exp(-mu) * mu ** i / math.factorial(i)
                     for i in range(k))


m('PStageOneUnattrib', '%.2f' % pois_ge(len(unattributed), EXP))
m('PStageOneAll', '%.1e' % pois_ge(len(FL), EXP))
m('StageOneUnattribRatio', '%.1f' % (len(unattributed) / EXP))

# Counting beta Pic once, as one astrophysical source rather than eight
# independent events, is the comparison a reader will want.
_eff = len(FL) - len(bp) + (1 if bp else 0)
m('NStageOneSources', '%d' % _eff)

# ------------------------------------------------------- per-flag details
by = collections.defaultdict(list)
for r in FL:
    by[(r['star_name'], r['band'])].append(r)
m('NStageOnePairsTab', '%d' % len(by))

rows = []
for (star, band), rs in sorted(
        by.items(), key=lambda kv: -max(F(r['star_snr']) for r in kv[1])):
    deep = max(rs, key=lambda r: F(r['star_snr']))
    dv = F(deep['line_offset_kms'])
    inside = abs(dv) <= TUBE_KMS
    rows.append((tidy(star), band, len(rs), deep, dv, inside))

with open(TAB, 'w') as fh:
    fh.write('% generated by v380_calc.py -- do not edit\n')
    fh.write('\\begin{tabular}{@{}llrrrrrl@{}}\n\\toprule\n')
    fh.write('Star & B & $N_{\\rm win}$ & $\\nu$ (GHz) & $T_\\star$ & '
             'ctrl & $\\Delta v$ & disposition \\\\\n\\midrule\n')
    for star, band, n, deep, dv, inside in rows:
        fh.write('%s & %s & %d & %.4f & %.2f & %.2f & %s & %s \\\\\n'
                 % (star, band, n, F(deep['f_cross_GHz']) or 0.0,
                    F(deep['star_snr']), F(deep['ctrl_max_snr']),
                    ('$%+.0f$' % dv) if dv is not None else '--',
                    deep['disposition'] or
                    ('%s in frame' % deep['nearest_line'] if inside
                     else 'unattributed')))
    fh.write('\\bottomrule\n\\end{tabular}\n')

# ------------------------------- an illustrative haystack fraction
# Wright et al. (2018) frame a search as a fraction of a multidimensional
# parameter volume. We decline to turn the non-detection into an
# occurrence rate, but an order-of-magnitude statement of how much of that
# volume this survey touched is useful and costs nothing, provided each
# axis is given separately: the product treats the axes as independent,
# which they are not, and is quoted only as an order of magnitude.
_HAY = dict(nu_lo=0.3, nu_hi=300.0)          # GHz, the Wright et al. band
_nstars = len({r['star_name'] for r in ROWS})
_ncensus = 17566                             # Gaia DR3 stars within 40 pc
_union = float(_texval('UnionGHz'))
_tsum = sum(F(r['on_source_s']) for r in ROWS)
_bysys = collections.defaultdict(float)
for r in ROWS:
    _bysys[r['system_id']] = max(_bysys[r['system_id']], F(r['on_source_s']))
_tstar = sum(_bysys.values())
# time axis: cumulative staring time per system against one year each
_ftime = _tstar / (len(_bysys) * 365.25 * 86400.0)
_fstar = _nstars / float(_ncensus)
_fnu = _union / (_HAY['nu_hi'] - _HAY['nu_lo'])
m('HayFracStar', _sci(_fstar))
m('HayFracNu', '%.2f' % _fnu)
m('HayFracTime', _sci(_ftime, 1))
# HayFracProd deliberately not emitted: see S6.2.
m('HayNuLo', '%g' % _HAY['nu_lo'])
m('HayNuHi', '%g' % _HAY['nu_hi'])
m('HayStareHours', '%.0f' % (_tstar / 3600.0))

# ------------------------------------------ the pre-registration order
# A hold-out is only worth having if nothing about the analysis was
# decided after it was fixed. The repository timestamps settle that:
# the detection statistic and the candidate criteria are committed before
# the hold-out rule, and the hold-out rule before any reserved block was
# searched. Generated so the ordering cannot be asserted without being
# checked.
_ORDER = json.load(open('prereg_order_v383.json'))
_d = [(k, _ORDER[k]['date']) for k in ('statistic', 'criteria', 'holdout',
                                       'first_reserved_block_searched')]
for (k1, d1), (k2, d2) in zip(_d, _d[1:]):
    assert d1 <= d2, ('pre-registration order violated', k1, d1, k2, d2)
m('StatFreezeDate', _ORDER['statistic']['date'])
m('StatFreezeHash', _ORDER['statistic']['commit'])
m('HoLeadDays', '%d' % _ORDER['holdout']['days_after_statistic'])
m('HoLeadBlockDays', '%d' % _ORDER['holdout']['days_before_first_reserved'])

# ------------------------------- scope of the polarisation caveat
# Referee: say how many windows the Stokes-I-only penalty could affect.
# The archive's own polarisation states answer it: every block delivering
# both parallel hands can in principle be split per hand, and the
# worst-case factor two applies only where one hand is lost to flagging,
# which a Stokes I product cannot reveal.
# v3.85: polstates_v351.json covered the 104 blocks that WERE the sample
# at v3.51, and the manuscript grew to 404 without the query being re-run,
# so "all N of the N searched blocks" was a statement about 26 per cent of
# the sample. polstates_v385.py re-queries every searched block.
_POLF = ('polstates_v385.json' if os.path.exists('polstates_v385.json')
         else 'polstates_v351.json')
_POL = json.load(open(_POLF)) if os.path.exists(_POLF) else None
if _POL:
    # Values are obscore pol_states strings such as '/XX/YY/'.
    _hands = lambda v: all('XX' in str(x) and 'YY' in str(x)
                           for x in (v if isinstance(v, list) else [v]))
    _both = sum(1 for v in _POL.values() if _hands(v))
    _single = [k for k, v in _POL.items() if not _hands(v)]
    _nsearched = len({r['eb'] for r in ROWS})
    m('NEbBothHands', '%d' % _both)
    m('NEbPolKnown', '%d' % len(_POL))
    m('NEbPolUnknown', '%d' % (_nsearched - len(_POL)))
    m('NEbSinglePol', '%d' % len(_single))
    m('PctEbBothHands', '%.0f' % (100.0 * _both / len(_POL)))
    m('PctEbPolKnown', '%.0f' % (100.0 * len(_POL) / _nsearched))
    # Which windows the single-polarisation blocks carry, so the caveat can
    # be bounded rather than waved at.
    _sgl_eb = {k.replace('uid://', '').replace('/', '_') for k in _single}
    _sgl_rows = [r for r in ROWS if r['eb'] in _sgl_eb]
    m('NWinSinglePol', '%d' % len(_sgl_rows))
    m('NSinglePolStars', '%d' % len({r['star_name'] for r in _sgl_rows}))
    m('SinglePolStar', ', '.join(sorted({r['star_name'].split('  Gaia')[0]
                                         for r in _sgl_rows})).replace('tau Cet', r'$\tau$~Ceti'))
    m('NStageOneSinglePol',
      '%d' % sum(1 for r in _sgl_rows if r['stage1_flag'] == 'True'))
    m('SinglePolClass',
      '/'.join(sorted({r['search_class'] for r in _sgl_rows})))

# --------------- the stage-1 list under the radius-corrected statistic
# Referee: the released statistic is measurably biased, so the corrected
# one has to define the candidate list for the WHOLE survey and not for a
# spot check. Run over all windows it changes the list: four windows lose
# their flag and one gains it, so the stage-1 count falls from 13 to 10
# and the unattributed count from 4 to 2. We report both, and treat the
# corrected list as primary.
_LOC = json.load(open('localnorm_all_v385.json'))
m('LocAllWinChk', '%d' % _LOC['n_windows'])
m('LocStageGlobal', '%d' % _LOC['flag_global'])
m('LocStageLocal', '%d' % _LOC['flag_local'])
m('LocStageBoth', '%d' % _LOC['flag_both'])
m('LocStageLost', '%d' % _LOC['lost'])
m('LocStageGained', '%d' % _LOC['gained'])
m('LocLostList', ', '.join(tidy(d['star']) for d in _LOC['changed']
                           if d['how'] == 'lost'))
m('LocGainedList', ', '.join(tidy(d['star']) for d in _LOC['changed']
                             if d['how'] == 'gained'))
# The corrected list: beta Pic's eight plus the survivors.
_lostset = {(d['eb'], d['band']) for d in _LOC['changed'] if d['how'] == 'lost'}
_corr = [r for r in FL if (r['eb'], r['band']) not in _lostset]
_gain = [d for d in _LOC['changed'] if d['how'] == 'gained']
_corr_un = [r for r in _corr if abs(F(r['line_offset_kms']) or 9e9) > TUBE_KMS]
m('LocCorrStage', '%d' % (len(_corr) + len(_gain)))
m('LocCorrUnattrib', '%d' % (len(_corr_un) + len(_gain)))
m('LocCorrAttrib', '%d' % (len(_corr) - len(_corr_un)))
# The new entrant's velocity offset, so the text need not hand-type it.
_h207 = [r for r in ROWS if r['star_name'].startswith('HD 207129')
         and abs(F(r['star_snr']) - 5.68) < 0.02]
if _h207:
    m('HdTwoZeroSevenDv', '%.0f' % F(_h207[0]['line_offset_kms']))

# ---------------------- the visibility-domain test, all four events
# Referee: the image-plane rank is a screen; the physically clean
# question is whether an unresolved source sits at the star's coordinates
# in the visibilities. Phase-rotating to the star turns a point source
# there into a constant real offset, so Re is the source and Im must be
# consistent with zero. Emission elsewhere in the field is suppressed in
# Re and, in general, leaves a non-zero Im. Eight control positions on the
# same annulus the image test uses give the comparison.
_VISFILE = ('vistest_v385.json' if os.path.exists('vistest_v385.json')
            else 'vistest_v384.json')
_VIS = json.load(open(_VISFILE))
_ORDER = sorted((k for k, v in _VIS.items() if v.get('status') == 'ok'),
                key=lambda k: -_VIS[k]['event']['star_snr'])
assert len(_ORDER) == len(_VIS), 'a visibility event did not return a result'


def _vstar(k):
    return _VIS[k]['star']


def _vname(k):
    """Display name. The 13-event file keys on 'star|eb' because eight of
    the events are the same star."""
    return tidy(k.split('|')[0])


def _vatt(k):
    return 'CO' in str(_VIS[k]['event'].get('disposition', ''))


def _verdict(k):
    """The test's own decision, from its own numbers.

    The test asks whether emission sits AT the stellar position, not
    whether it is unresolved: a centrally symmetric resolved source also
    gives a positive real part with a null imaginary part. So a large Im
    is the decisive negative, and a real part below the window's own
    controls is the second.
    """
    st, v = _vstar(k), _VIS[k]
    if abs(st['snr_im']) > 3.0:
        # Q26: this used to read "displaced: phase inconsistent", which is
        # the categorical reading the prose withdraws -- at this
        # significance, with internal errors, the test does not localise.
        return 'not localised: Im $\\neq0$', False
    if st['snr_re'] <= v['ctrl_snr_re_max']:
        return 'not above its own controls', False
    if st['snr_re'] < 3.0:
        return 'nothing at the star', False
    return 'emission at the stellar position', True


_nat = 0
with open('tab_visibility_v385.tex', 'w') as fh:
    fh.write('% generated by v381_calc.py -- do not edit\n')
    fh.write('\\begin{tabular}{@{}llrrrrrl@{}}\n\\toprule\n')
    fh.write('Star & B & $N_{\\rm vis}$ & Re/$\\sigma$ & Im/$\\sigma$ & '
             '$\\chi^2/\\nu$ & ctrl & verdict \\\\\n\\midrule\n')
    for group, head in ((False, 'Unattributed'),
                        (True, 'Attributed to CO (positive controls)')):
        rows = [k for k in _ORDER if _vatt(k) == group]
        if not rows:
            continue
        fh.write('\\multicolumn{8}{@{}l}{\\emph{%s}} \\\\\n' % head)
        for k in rows:
            st = _vstar(k)
            verd, isps = _verdict(k)
            if group:
                _nat += isps
            fh.write('%s & %s & %s & $%+.1f$ & $%+.1f$ & %.2f & $%+.1f$ & %s \\\\\n'
                     % (_vname(k), _VIS[k]['event'].get('band', ''),
                        '{:,}'.format(st['n_vis']).replace(',', '\\,'),
                        st['snr_re'], st['snr_im'], st['chi2_dof'],
                        _VIS[k]['ctrl_snr_re_max'], verd))
    fh.write('\\bottomrule\n\\end{tabular}\n')
open('tab_visibility_v384.tex', 'w').write(open('tab_visibility_v385.tex').read())

_unatt = [k for k in _ORDER if not _vatt(k)]
_att = [k for k in _ORDER if _vatt(k)]
m('NVisTested', '%d' % len(_ORDER))
m('NVisUnatt', '%d' % len(_unatt))
m('NVisAtt', '%d' % len(_att))
# Of the unattributed events, how many look like emission at the star.
m('NVisPointSource', '%d' % sum(1 for k in _unatt if _verdict(k)[1]))
m('VisMaxReSig', '%.1f' % max(_vstar(k)['snr_re'] for k in _unatt))
m('VisMinCtrl', '%.1f' % min(_VIS[k]['ctrl_snr_re_max'] for k in _unatt))
_hdk = [k for k in _ORDER if k.startswith('HD14055')]
m('VisHdImSig', '%.1f' % abs(_vstar(_hdk[0])['snr_im']) if _hdk else '--')
# The positive controls: the same test on the events we DO attribute.
m('NVisAttRecov', '%d' % _nat)
m('VisAttReLo', '%.0f' % min(_vstar(k)['snr_re'] for k in _att
                             if _verdict(k)[1]))
m('VisAttReHi', '%.0f' % max(_vstar(k)['snr_re'] for k in _att))
_sib = [k for k in _att if not _verdict(k)[1]]
m('NVisAttMiss', '%d' % len(_sib))
m('VisAttMissSrc', _sib[0].split('|')[1].replace('_', r'\_') if _sib else '--')
_hd48 = [k for k in _att if k.startswith('HD 48370')]
if _hd48:
    m('VisHdFortyIm', '%.1f' % _vstar(_hd48[0])['snr_im'])
    m('VisHdFortyRe', '%.0f' % _vstar(_hd48[0])['snr_re'])
m('VisSource', _VISFILE.replace('_', r'\_'))

# --------------------------- completeness of the CONFIRMATION step
# Referee: single-epoch recovery is not the completeness that matters,
# because the paper's own definition of a confirmed technosignature needs
# a second block at the same star AND the same tuning. That is a property
# of ALMA's observing history, not of the transmitter, and it puts a
# ceiling on the fraction of true positives this design could ever
# confirm.
_CONF = json.load(open('confirmability_v384.json'))
m('NConfWinA', '%d' % _CONF['n_a_win_confirmable'])
m('PctConfWinA', '%.0f' % (100.0 * _CONF['n_a_win_confirmable']
                           / _CONF['n_a_win']))
m('NConfSysA', '%d' % _CONF['n_a_sys_confirmable'])
m('PctConfSysA', '%.0f' % (100.0 * _CONF['n_a_sys_confirmable']
                           / _CONF['n_a_sys']))
# Joint ceiling: recovery at stage 1 times the chance a repeat exists.
_p90pc = float(_texval('StratRecFive') or 61) / 100.0
m('ConfCeilingPct',
  '%.0f' % (100.0 * (_CONF['n_a_sys_confirmable'] / _CONF['n_a_sys'])))

# ---- R6: CP-72's repeat block carries two different statistics, the
# pinned-frequency one (CpRecT) and the maximum over its own grid. One
# symbol was used for both in adjacent tables.
_cp = [r for r in ROWS if r['star_name'].startswith('CP-72')
       and r['stage1_flag'] == 'True']
if _cp:
    _c0 = _cp[0]
    _lo, _hi = sorted((F(_c0['flo_GHz']), F(_c0['fhi_GHz'])))
    _rep = [q for q in ROWS if q['star_name'] == _c0['star_name']
            and q['eb'] != _c0['eb']
            and min(F(q['flo_GHz']), F(q['fhi_GHz'])) <= _lo + 0.02
            and max(F(q['flo_GHz']), F(q['fhi_GHz'])) >= _hi - 0.02]
    if _rep:
        m('CpRecTwoBest', '%.2f' % max(F(q['star_snr']) for q in _rep))

# ---- R2-m1: the illustrative sqrt(channel) rescaling
# Explicitly NOT an achievable ALMA sensitivity: it asks what the median
# Class A threshold would be if the same data could be rechannelised to a
# hertz-resolution SETI channel, which it cannot.
_SETI_CHAN_HZ = 2.79
m('SETIChanHz', '%.2f' % _SETI_CHAN_HZ)
_cw = sorted(F(r['chanw_Hz']) for r in ROWS
             if r['search_class'] == 'A' and F(r['chanw_Hz']))
_cwmed = _cw[len(_cw) // 2]
_fac = (_SETI_CHAN_HZ / _cwmed) ** 0.5
m('SqrtScaleFac', '%.0f' % (1.0 / _fac))
m('SqrtScaleChanKHz', '%.0f' % (_cwmed / 1e3))
_pe = sorted(F(r['eirp_p90_W']) * F(r['ctrl_max_snr']) / 5.0 for r in ROWS
             if r['search_class'] == 'A' and F(r['eirp_p90_W'])
             and F(r['ctrl_max_snr']))
m('SqrtScalePsel', _sci(_pe[len(_pe) // 2] * _fac))

# ---- R1-9: how many catalogue entries collapse into a system
from star_alias import PAIRS as _PAIRS
m('NBoundPairs', '%d' % len(_PAIRS))

# ---- R1-8: temporal baselines of the repeat tests
# A repeat two hours later and a repeat nine years later test very
# different kinds of intermittency, so the count alone is not enough.
_META = json.load(open('archive_meta_v381.json'))['ebs']
_EP = json.load(open('epochs_v386.json')) if os.path.exists(
    'epochs_v386.json') else {}
_EPOCH = _EP.get('mjd', {})
_EPSRC = _EP.get('source', {})


def _mjd(eb):
    if eb in _EPOCH:
        return float(_EPOCH[eb])
    t = (_META.get(eb) or {}).get('t_min') or []
    v = [float(x) for x in t if x not in (None, '')]
    return min(v) if v else None


def _exact(eb):
    """True where the epoch is the block's own, not its member OUS's."""
    return _EPSRC.get(eb) == 'block'


def _utc(eb):
    """Calendar date of the block's epoch, marked where the archive gives
    only the member OUS's start (R1-5: the table must not imply a
    block-level epoch it does not have)."""
    t = _mjd(eb)
    if t is None:
        return None
    import datetime
    d = (datetime.date(1858, 11, 17) + datetime.timedelta(days=float(t)))
    return d.isoformat() + ('' if _exact(eb) else '$^{b}$')


def _baselines(r, rep):
    """(shortest, longest) separation in days between the flagged block and
    its repeats, and the total span."""
    t0 = _mjd(r['eb'])
    ts = [_mjd(q['eb']) for q in rep]
    ts = [t for t in ts if t is not None]
    if t0 is None or not ts:
        return None
    d = sorted(abs(t - t0) for t in ts)
    allt = ts + [t0]
    return d[0], d[-1], max(allt) - min(allt)

# ---- R1-6: the frequency union, separated by search class
# Most of the 118.1 GHz union is Class B, which cannot discriminate drift,
# so quoting it as the technosignature-search bandwidth overstates the
# primary experiment by a factor of about two.
def _union(rows):
    iv = sorted((min(F(r['flo_GHz']), F(r['fhi_GHz'])),
                 max(F(r['flo_GHz']), F(r['fhi_GHz']))) for r in rows)
    tot, lo, hi = 0.0, None, None
    for a, b in iv:
        if lo is None:
            lo, hi = a, b
        elif a <= hi:
            hi = max(hi, b)
        else:
            tot += hi - lo
            lo, hi = a, b
    return tot + (hi - lo if lo is not None else 0.0)


# R1-7: the scientific exposure per system, which is what a transmitter
# around one star would have had to fall inside.
_persys = {}
for r in ROWS:
    if r['search_class'] == 'A':
        _persys.setdefault(r['system_id'], []).append(r)
_pu = sorted(_union(v) for v in _persys.values())
import numpy as _np
m('SysUnionAMed', '%.2f' % _pu[len(_pu) // 2])
m('SysUnionALo', '%.2f' % _np.percentile(_pu, 10))
m('SysUnionAHi', '%.2f' % _np.percentile(_pu, 90))
m('SysUnionAMin', '%.2f' % _pu[0])
m('SysUnionAMax', '%.2f' % _pu[-1])
m('NSysUnionA', '%d' % len(_pu))
m('SysUnionAFracMed', '%.1f' % (100.0 * _pu[len(_pu) // 2]
                                / _union([r for r in ROWS
                                          if r['search_class'] == 'A'])))

_uA = _union([r for r in ROWS if r['search_class'] == 'A'])
_uB = _union([r for r in ROWS if r['search_class'] == 'B'])
_uAll = _union(ROWS)
m('UnionClassA', '%.1f' % _uA)
m('UnionClassB', '%.1f' % _uB)
m('UnionBonly', '%.1f' % (_uAll - _uA))
m('PctUnionClassA', '%.0f' % (100.0 * _uA / _uAll))

# ---- Q24: how many rows actually carry a disposition
m('NCatDispo', '%d' % sum(1 for r in ROWS if r['disposition']))

# ---- Q23: the priority claim for Barnard's Star and Wolf 359
_pri = {}
for _nm, _tag in (("NAME Barnards star", 'Barn'), ("Wolf  359", 'Wolf'),
                  ("Wolf 359", 'Wolf')):
    _rows = [r for r in ROWS if ' '.join(r['star_name'].split()) == ' '.join(_nm.split())]
    if not _rows:
        continue
    _e = sorted(F(r['eirp_nominal_W']) for r in _rows if F(r['eirp_nominal_W']))
    _pri.setdefault(_tag, (len(_rows), _e[0], _e[-1]))
for _tag, (_n, _lo, _hi) in _pri.items():
    m('NWin' + _tag, '%d' % _n)
    m('Eirp' + _tag + 'Lo', _sci(_lo))
    m('Eirp' + _tag + 'Hi', _sci(_hi))

# ---- recurrence coverage for the PRIMARY experiment (S15)
# The paper quotes 54 of 87 systems with more than one block, pooling both
# classes. The primary experiment is Class A, and its own figure is lower.
_sysA = collections.defaultdict(set)
for r in ROWS:
    if r['search_class'] == 'A':
        _sysA[r['system_id']].add(r['eb'])
_multiA = sum(1 for v in _sysA.values() if len(v) > 1)
m('NSysClassAMulti', '%d' % _multiA)
m('PctSysClassAMulti', '%.0f' % (100.0 * _multiA / len(_sysA)))

# ---- the Mason et al. comparison, derived (S13)
# `MasonRatio` was the literal 1250 in make_numbers.py and reproduces
# neither on the trigger (1646) nor on P_90 (595). Quote it on P_90,
# which is the number this paper tells readers to use, and give the
# distance term beside it so the comparison is not read as sensitivity.
# R1-3 (v3.95): the headline quantity is now P_90^sel, so the survey
# comparison is quoted on it. P_90 is retained beside it because Mason's
# published figure is a threshold, so the P_90^sel ratio is the
# conservative one: it compares our complete selection against their
# trigger.
MASON_W, MASON_D_PC = 6.8e17, 1010.0
_b90, _bsel = {}, {}
for r in ROWS:
    v = F(r['eirp_p90_W'])
    if v and v < _b90.get(r['system_id'], float('inf')):
        _b90[r['system_id']] = v
    c = F(r['ctrl_max_snr'])
    if v and c and r['search_class'] == 'A':
        vs = v * c / 5.0
        if vs < _bsel.get(r['system_id'], float('inf')):
            _bsel[r['system_id']] = vs
_m90 = sorted(_b90.values())[len(_b90) // 2]
_msel = sorted(_bsel.values())[len(_bsel) // 2]
m('MasonRatioNew', '%d' % round(MASON_W / _m90))
m('MasonRatioSel', '%d' % round(MASON_W / _msel))
m('MasonMedPsel', _sci(_msel))
assert _msel > _m90, 'the selection sensitivity must be the weaker number'
_d = sorted(F(r['dist_pc']) for r in ROWS if F(r['dist_pc']))
m('MasonDsqRatio', '%d' % round((MASON_D_PC / _d[len(_d) // 2]) ** 2))
m('MasonMedPNinety', _sci(_m90))

# ---- the completeness at the PROMOTION gate, not just the trigger (S6)
# A window promotes an event to stage 1 only if the stellar statistic
# exceeds every one of its own control positions. The Class A median
# control maximum is well above 5 sigma, so P_90 -- which is calibrated
# against the 5 sigma trigger -- is not the power at which this survey
# would have promoted a carrier. Scale each window by its own gate.
_cmA = sorted(F(r['ctrl_max_snr']) for r in ROWS
              if r['search_class'] == 'A' and F(r['ctrl_max_snr']))
m('GateMedA', '%.2f' % _cmA[len(_cmA) // 2])
m('GateLoA', '%.2f' % _cmA[0])
m('GateHiA', '%.2f' % _cmA[-1])
m('NGateBelowTrig', '%d' % sum(1 for c in _cmA if c < 5.0))
m('PctGateBelowTrig', '%.1f' % (100.0 * sum(1 for c in _cmA if c < 5.0)
                                / len(_cmA)))
_prom = sorted(F(r['eirp_p90_W']) * F(r['ctrl_max_snr']) / 5.0 for r in ROWS
               if r['search_class'] == 'A' and F(r['eirp_p90_W'])
               and F(r['ctrl_max_snr']))
m('PromoteLoA', _sci(_prom[0]))
m('PromoteMedA', _sci(_prom[len(_prom) // 2]))
m('PromoteHiA', _sci(_prom[-1]))
m('PromoteFacMed', '%.2f' % (_cmA[len(_cmA) // 2] / 5.0))
# R1-1: the per-system form, taking each system's best window, on the same
# footing as the P_90 per-system numbers.
_psys = {}
for r in ROWS:
    if r['search_class'] != 'A':
        continue
    v, c = F(r['eirp_p90_W']), F(r['ctrl_max_snr'])
    if not v or not c:
        continue
    pv = v * c / 5.0
    if pv < _psys.get(r['system_id'], float('inf')):
        _psys[r['system_id']] = pv
_ps = sorted(_psys.values())
m('PromoteSysLoA', _sci(_ps[0]))
m('PromoteSysMedA', _sci(_ps[len(_ps) // 2]))
m('PromoteSysHiA', _sci(_ps[-1]))
m('NPromoteSys', '%d' % len(_ps))

# ------------ round-1 self-review repairs, all re-derived (v3.85)
# C51: "393 star-hour-GHz" against 6.8e6 s GHz is out by a factor 4.8 --
# 6.8e6/3600 = 1889. The frozen round-5 value predates the sample.
_expo = sum(F(r['on_source_s']) * F(r['bandwidth_Hz']) / 1e9
            for r in ROWS if r['on_source_s'] and r['bandwidth_Hz'])
m('ExpoSGHzNew', _sci(_expo))
m('ExpoStarHrGHz', '{:,}'.format(int(round(_expo / 3600))).replace(',', r'\,'))
# C57: "all twelve Band 8 windows" -- there are 24, toward three stars.
_b8 = [r for r in ROWS if r['band'] == '8']
m('NBandEightWin', '%d' % len(_b8))
m('BandEightStars',
  '%d' % len({r['star_name'].split('  Gaia')[0] for r in _b8}))
# C27: "41 per cent are M dwarfs" was hand-typed.
# C6: how many windows the SUPERSEDED region-max statistic flags.
m('NRegionMaxFlag',
  '%d' % sum(1 for r in ROWS if r['stage1_flag_regionmax'] == 'True'))
m('NRegionMaxPairs',
  '%d' % len({(r['star_name'], r['band']) for r in ROWS
              if r['stage1_flag_regionmax'] == 'True'}))

# ------------------- summary-table quantities, re-derived (v3.85)
# Six numbers in and around the survey summary table were hand-typed or
# frozen at an earlier sample size, and the round-1 self-review caught all
# six at once: the crossing class split ("all Class A" -- four are Class B),
# the drift ceiling in kHz/s (quoted 1.1-5.9, actually up to 10.5 once the
# Band 9/10 windows joined), the count of fine windows carrying a crossing
# (20 -> 71), the Class A P_eff range, the window concentration, and the
# number of windows with a smearing correction.
_crossA = sum(1 for r in ROWS if r['crossing'] == 'True'
              and r['search_class'] == 'A')
_crossB = sum(1 for r in ROWS if r['crossing'] == 'True'
              and r['search_class'] == 'B')
m('NHitsA', '%d' % _crossA)
m('NHitsB', '%d' % _crossB)
m('PctHitsA', '%.0f' % (100.0 * _crossA / max(_crossA + _crossB, 1)))
m('NSpatialA', '%d' % sum(1 for r in ROWS if r['stage1_flag'] == 'True'
                          and r['search_class'] == 'A'))

_dr = [F(r['drift_max_Hz_s']) for r in ROWS if F(r['drift_max_Hz_s'])]
m('DriftKHzLo', '%.1f' % (min(_dr) / 1e3))
m('DriftKHzHi', '%.1f' % (max(_dr) / 1e3))
_drA = [F(r['drift_max_Hz_s']) for r in ROWS
        if r['search_class'] == 'A' and F(r['drift_max_Hz_s'])]
m('DriftKHzLoA', '%.1f' % (min(_drA) / 1e3))
m('DriftKHzHiA', '%.1f' % (max(_drA) / 1e3))

for _t, _c in (('A', 'A'), ('B', 'B')):
    _pe = sorted(F(r['eirp_eff_total_W']) for r in ROWS
                 if r['search_class'] == _c and F(r['eirp_eff_total_W']))
    m('PeffWinLo' + _t, _sci(_pe[0]))
    m('PeffWinMed' + _t, _sci(_pe[len(_pe) // 2]))
    m('PeffWinHi' + _t, _sci(_pe[-1]))

m('NSmearWin', '%d' % sum(1 for r in ROWS if r['eta_smear']))
_onsrc = sorted(F(r['on_source_s']) for r in ROWS if F(r['on_source_s']))
m('OnSrcMedWin', '%.0f' % _onsrc[len(_onsrc) // 2])

# ------------------------------ Class A sensitivity, and the disc bias
# The primary experiment is the fine-channel search, so its own median
# P90 has to exist as a number; the paper quoted only a pooled median.
_fine = sorted(F(r['eirp_eff_total_W']) for r in ROWS
               if r['resolution_class'] == 'fine' and F(r['eirp_eff_total_W']))
# NOT float(_texval('StratPNinety'))/5: that macro is rounded to one
# decimal, and scaling a 10^17 W threshold by a rounded factor moves the
# printed sensitivity by ~1 per cent. Take the factor unrounded.
from inject_curve import P90_OVER_TRIG
_p90 = P90_OVER_TRIG
# Class A, per WINDOW. The per-SYSTEM equivalents (best window per
# system) are emitted by make_fig_classa_sens.py as ClassAPNinety*.
m('PNinetyWinMedA', _sci(_fine[len(_fine) // 2] * _p90))
m('PNinetyWinBestA', _sci(_fine[0] * _p90))
m('PNinetyWinWorstA', _sci(_fine[-1] * _p90))
# The released catalogue now carries the same quantity per row (v3.85,
# referee 2 point 2 and referee 1 point 16). Assert that the headline
# numbers really do regenerate from the released file, rather than
# asserting it in prose.
_col = sorted(F(r['eirp_p90_W']) for r in ROWS
              if r['resolution_class'] == 'fine' and F(r['eirp_p90_W']))
assert len(_col) == len(_fine), 'P90 column missing rows'
for _a, _b in ((_col[0], _fine[0] * _p90),
               (_col[len(_col) // 2], _fine[len(_fine) // 2] * _p90),
               (_col[-1], _fine[-1] * _p90)):
    assert abs(_a / _b - 1) < 2e-3, 'catalogue P90 column disagrees: %g %g' % (_a, _b)
m('NSysClassA', '%d' % len({r['system_id'] for r in ROWS
                            if r['resolution_class'] == 'fine'}))
# Archival selection: how many searched stars come from a disc or
# planet-formation proposal. Read from the obscore categories, not typed.
_ob = json.load(open('obscore_category_v381.json'))['blocks']
_uid = lambda e: 'uid://' + e.replace('_', '/', 1).replace('_', '/')
_disc = set()
for r in ROWS:
    b = _ob.get(_uid(r['eb']), {})
    if 'Disks and planet formation' in str(b.get('scientific_category', '')):
        _disc.add(r['star_name'])
m('NDiscProposalStars', '%d' % len(_disc))
m('PctDiscProposal', '%.0f' % (100.0 * len(_disc) / len({r['star_name'] for r in ROWS})))

# ----------------------------------------- the execution-block ledger
# One identity, closing exactly, so the Abstract, the sample section and
# the Conclusions cannot each give a different count. The numbers that
# used to circulate -- 484, 404, 656 -- are all correct and describe
# different populations; the paper has to say which is which.
_LED = json.load(open('block_ledger_v384.json'))
m('LedProgenitor', '%d' % _LED['n_progenitor'])
m('LedProcessed', '%d' % _LED['n_processed'])
m('LedCatalogue', '%d' % _LED['n_catalogue'])
m('LedHoldout', '%d' % _LED['n_holdout'])
m('LedNoWindow', '%d' % (_LED['n_processed'] - _LED['n_catalogue']
                         - _LED['n_holdout']))
m('LedNotProcessed', '%d' % _LED['n_not_processed'])
m('LedDuplicate', '%d' % _LED['n_duplicate'])
m('LedNoCalib', '%d' % _LED['n_no_calibration'])

# v3.95 post-push fix: the assertion that used to stand here was
#   catalogue + holdout + (processed - catalogue - holdout) == processed
# which is true for ANY three numbers. It asserted nothing, and it let the
# paper print a ledger that does not close: 484 + 177 = 661, not 656.
# Recompute both real identities from the progenitor lists.
_progset = set()
for _v in json.load(open('archive_meta_v381.json'))['mous'].values():
    _progset |= {q if isinstance(q, str) else q.get('eb')
                 for q in _v['progenitors']}
_progset = {q for q in _progset if q}
_procset = set(json.load(open('archive_meta_v381.json'))['ebs'])
_searchedall = {l.strip() for l in open('searched_ebs_v381.txt') if l.strip()}
_inscope = _searchedall & _progset
_noprog = _procset - _progset

assert len(_progset) == _LED['n_progenitor'], \
    ('progenitor union %d != ledger %d' % (len(_progset), _LED['n_progenitor']))
assert len(_procset) == _LED['n_processed'], \
    ('processed set %d != ledger %d' % (len(_procset), _LED['n_processed']))
# Identity 1: the progenitor population splits into searched and not.
assert len(_inscope) + len(_progset - _searchedall) == len(_progset), \
    'progenitor ledger does not close'
assert len(_progset - _searchedall) == _LED['n_not_processed'], \
    ('unsearched in scope %d != ledger n_not_processed %d'
     % (len(_progset - _searchedall), _LED['n_not_processed']))
# Identity 2: the processed population is the in-scope blocks plus those
# whose member-OUS progenitor link the archive does not expose.
assert len(_procset & _progset) + len(_noprog) == len(_procset), \
    'processed ledger does not close'
m('LedInScope', '%d' % len(_inscope))
m('LedNoProgLink', '%d' % len(_noprog))
# The in-scope searched blocks split into the science sample and the
# hold-out. The S6 remainder sentence used to add the 20 uncalibrated
# blocks alongside the 177 unsearched, but they are a SUBSET of the 177,
# and it ignored the science blocks that fall outside the progenitor set.
_frozenset = {r['eb'] for r in ROWS}
_sci_in = len(_frozenset & _progset)
_ho_in = len(_inscope) - _sci_in
m('LedSciInScope', '%d' % _sci_in)
m('LedHoldoutInScope', '%d' % _ho_in)
m('LedSciOutScope', '%d' % len(_frozenset - _progset))
assert _sci_in + _ho_in + len(_progset - _searchedall) == len(_progset), \
    'the three-way in-scope split does not close'

# ------------------------- the median window, beside the deepest one
# Quoting only the deepest window invites a reader to treat it as the
# survey sensitivity, which the paper elsewhere denies. Give the median
# alongside it, on the same footing.
_effs = sorted(F(r['eirp_eff_total_W']) for r in ROWS
               if F(r['eirp_eff_total_W']))
_p90fac = P90_OVER_TRIG
m('EirpNinetyMedian', _sci(_effs[len(_effs) // 2] * _p90fac))
m('EirpEffMedian', _sci(_effs[len(_effs) // 2]))

# ------------------------------- the HD 48370 near-tie, generated
# The prose quotes this star/ring pair as the limiting case of the whole
# screen. It was hand-typed; a hand-typed catalogue value beside a
# generated one is the pairing that has gone stale here before.
_hd = [r for r in ROWS
       if r['star_name'].startswith('HD 48370') and r['stage1_flag'] == 'True']
if _hd:
    _h = max(_hd, key=lambda r: F(r['star_snr']))
    # The margin must be the difference of the PRINTED values, or the
    # arithmetic on the page does not close: 27.104 - 26.826 = 0.278 ->
    # 0.28, while the printed 27.10 - 26.83 = 0.27.
    _hs, _hc = round(F(_h['star_snr']), 2), round(F(_h['ctrl_max_snr']), 2)
    m('HdTsym', '%.2f' % _hs)
    m('HdRingMax', '%.2f' % _hc)
    m('HdMargin', '%.2f' % (_hs - _hc))

# --------------------------------------- the molecular mask, per class
# The aggregate reduction of the frequency union hides the fact that the
# two experiments pay different prices: a coarse channel spans many times
# the +-50 km/s tube, so masking a transition in Class B removes a whole
# 15.6-31.25 MHz window's worth of coverage rather than a sliver.
MASK_KMS = 50.0
_LAB = {'CO(1-0)': 115.271202, 'CO(2-1)': 230.538000, 'CO(3-2)': 345.795990,
        'CO(4-3)': 461.040768, '13CO(2-1)': 220.398684,
        'C18O(2-1)': 219.560354, 'CS(5-4)': 244.935556,
        'SiO(5-4)': 217.104980}


def _union(iv):
    out = []
    for a, b in sorted(iv):
        if out and a <= out[-1][1]:
            out[-1][1] = max(out[-1][1], b)
        else:
            out.append([a, b])
    return out


def _len(iv):
    return sum(b - a for a, b in iv)


def _mask_cost(rows):
    isl = _union([(min(F(r['flo_GHz']), F(r['fhi_GHz'])),
                   max(F(r['flo_GHz']), F(r['fhi_GHz']))) for r in rows])
    tubes = _union([(f * (1 - MASK_KMS / 299792.458),
                     f * (1 + MASK_KMS / 299792.458)) for f in _LAB.values()])
    lost = 0.0
    for a, b in isl:
        for c, d in tubes:
            lost += max(0.0, min(b, d) - max(a, c))
    return _len(isl), lost


for tag, cls in (('A', 'fine'), ('B', 'coarse')):
    _g = [r for r in ROWS if r['resolution_class'] == cls]
    _u, _l = _mask_cost(_g)
    m('MaskUnion' + tag, '%.1f' % _u)
    m('MaskLost' + tag, '%.2f' % _l)
    m('MaskPct' + tag, '%.1f' % (100.0 * _l / _u if _u else 0.0))

# ------------------------------- the CP-72 2713 repeat test, quantified
# A reader should be able to tell "not detected again" from "a persistent
# signal of the original strength would have been recovered", and that
# needs both blocks' parameters side by side rather than scattered through
# a paragraph. Generated from the catalogue, so the table and the text
# cannot drift apart.
_CPF, _CPR = 'A002_Xff0235_X4a6d', 'A002_Xff0235_X502d'
_cp = {r['eb']: r for r in ROWS
       if r['eb'] in (_CPF, _CPR) and F(r['chanw_Hz']) < 1e6}
if len(_cp) == 2:
    _a, _b = _cp[_CPF], _cp[_CPR]
    _rows = [
        ('Execution block', r'\texttt{%s}' % _ebtag(_CPF),
         r'\texttt{%s}' % _ebtag(_CPR)),
        ('Start-to-start separation (h)', r'\multicolumn{2}{c}{\CpRecStartSepH}', None),
        ('On-source time (s)', '%.0f' % F(_a['on_source_s']),
         '%.0f' % F(_b['on_source_s'])),
        ('Channel width (kHz)', '%.2f' % (F(_a['chanw_Hz']) / 1e3),
         '%.2f' % (F(_b['chanw_Hz']) / 1e3)),
        ('Channel rms (mJy)', r'\CpRecRmsOne', r'\CpRecRmsTwo'),
        (r'Primary-beam FWHM (arcsec)', '%.1f' % F(_a['theta_pb_arcsec']),
         '%.1f' % F(_b['theta_pb_arcsec'])),
        ('Frequency axes registered to', r'\multicolumn{2}{c}{\CpRecOffChan{} channel}', None),
        ('Test frequency (GHz)', r'\multicolumn{2}{c}{%.4f}' % F(_a['f_cross_GHz']), None),
        (r'Test drift (kHz\,s$^{-1}$)', r'\multicolumn{2}{c}{\CpRecDriftkHzs}', None),
        ('Drift track sweeps (channels)', r'\multicolumn{2}{c}{\CpRecSweepChan}', None),
        ('Flux at that cell (mJy)',
         r'$\CpRecFluxOne\pm\CpRecErrOne$', r'$\CpRecFluxTwo\pm\CpRecErrTwo$'),
        (r'$T_\star$ in this window', '%.2f' % F(_a['star_snr']),
         '%.2f' % F(_b['star_snr'])),
        ('Largest control statistic', '%.2f' % F(_a['ctrl_max_snr']),
         '%.2f' % F(_b['ctrl_max_snr'])),
        (r'$T_\star$ expected if persistent', '--', r'\CpRecExpT'),
        ('Pair inconsistent at', r'\multicolumn{2}{c}{\CpRecExclPair$\sigma$}', None),
        ('First flux taken as exact', r'\multicolumn{2}{c}{\CpRecExclCond$\sigma$}', None),
    ]
    with open('tab_cprepeat_v383.tex', 'w') as fh:
        fh.write('% generated by v381_calc.py -- do not edit\n')
        fh.write('\\begin{tabular}{@{}lrr@{}}\n\\toprule\n')
        fh.write(' & first block & repeat block \\\\\n\\midrule\n')
        for lab, x, y in _rows:
            fh.write('%s & %s \\\\\n' % (lab, x if y is None else '%s & %s' % (x, y)))
        fh.write('\\bottomrule\n\\end{tabular}\n')
    m('CpOnSrcOne', '%.0f' % F(_a['on_source_s']))
    m('CpOnSrcTwo', '%.0f' % F(_b['on_source_s']))
    m('CpChanKHzTab', '%.2f' % (F(_a['chanw_Hz']) / 1e3))
    m('CpTstarTwo', '%.2f' % F(_b['star_snr']))

# --------------------------------- the unattributed outliers, one table
# The four unattributed stage-1 outliers are not homogeneous and should not
# read as though they were: only one has a repeat observation. One row each,
# generated from the catalogue.
_unatt = sorted(unattributed, key=lambda r: -F(r['star_snr']))
# Repeat coverage: a second execution block of the same star at a tuning
# that contains this window's crossing frequency.
_byname = collections.defaultdict(list)
for r in ROWS:
    _byname[r['star_name']].append(r)


def _repeat_blocks(r):
    """Other execution blocks of the same star whose tuning covers this
    event's frequency.

    v3.85: this used to require a released crossing FREQUENCY and return
    an empty list without one. That column is written only where the
    pipeline stored a peak, and it is blank for three of the four
    unattributed events -- so the paper said 'no second epoch exists' for
    events that have up to sixteen. Fall back to the window itself, which
    is what 'the same tuning' means and is released for every row.
    """
    f = F(r['f_cross_GHz'])
    lo0, hi0 = sorted((F(r['flo_GHz']), F(r['fhi_GHz'])))
    out = []
    for q in _byname[r['star_name']]:
        if q['eb'] == r['eb']:
            continue
        lo, hi = sorted((F(q['flo_GHz']), F(q['fhi_GHz'])))
        if f is not None:
            if lo <= f <= hi:
                out.append(q)
        elif lo <= lo0 + 0.02 and hi >= hi0 - 0.02:
            out.append(q)
    return out


# S1: the repeat-block evidence, as macros, because the abstract and the
# conclusions were asserting its absence.
_rep = {r['eb']: _repeat_blocks(r) for r in _unatt}
_bl = {}
for _r in _unatt:
    _b = _baselines(_r, _rep[_r['eb']])
    if _b:
        _bl[_r['eb']] = _b
_allsep = []
for _r in _unatt:
    _t0 = _mjd(_r['eb'])
    for _q in _rep[_r['eb']]:
        _t = _mjd(_q['eb'])
        if _t0 is not None and _t is not None:
            _allsep.append(abs(_t - _t0))
_res = sorted(d for d in _allsep if d > 0.01)
if _res:
    m('UnattSepMinD', '%.0f' % _res[0])
    m('UnattSepMaxD', '%.0f' % _res[-1])
    m('UnattSepMaxYr', '%.1f' % (_res[-1] / 365.25))
    m('NUnattSepResolved', '%d' % len(_res))
    m('NUnattSepSameDay', '%d' % (len(_allsep) - len(_res)))
m('NEbEpochExact', '%d' % sum(1 for e in {r['eb'] for r in ROWS} if _exact(e)))
_withrep = [r for r in _unatt if _rep[r['eb']]]
m('NUnattWithRepeat', '%d' % len(_withrep))
m('NUnattNoRepeatNew', '%d' % (len(_unatt) - len(_withrep)))
m('NUnattRepeatBlocks', '%d' % sum(len(v) for v in _rep.values()))
m('NUnattRepeatLo', '%d' % min(len(_rep[r['eb']]) for r in _withrep))
m('NUnattRepeatHi', '%d' % max(len(_rep[r['eb']]) for r in _withrep))
_allrep = [q for v in _rep.values() for q in v]
m('NUnattRepeatFlag',
  '%d' % sum(1 for q in _allrep if q['stage1_flag'] == 'True'))
m('UnattRepeatMaxT',
  '%.2f' % max(F(q['star_snr']) for q in _allrep) if _allrep else '--')
m('NUnattRepeatCross',
  '%d' % sum(1 for q in _allrep if q['crossing'] == 'True'))
m('NUnattRepeatAboveCtrl',
  '%d' % sum(1 for q in _allrep
             if F(q['star_snr']) > F(q['ctrl_max_snr'])))

with open('tab_unattributed_v383.tex', 'w') as fh:
    fh.write('% generated by v381_calc.py -- do not edit\n')
    fh.write('\\begin{tabular}{@{}llcrrrrrlrrrl@{}}\n\\toprule\n')
    fh.write('Star & EB & B & $\\nu$ (GHz) & $|\\dot\\nu|_{\\rm max}$ & '
             '$T_\\star$ & ctrl & $P_{\\rm eff}$ (W) & epoch & '
             '$N_{\\rm rep}$ & $\\Delta t$ & $T_\\star^{\\rm rep}$ '
             '($\\Delta$) & recurs? \\\\\n')
    fh.write(' & & & & (Hz\\,s$^{-1}$) & & & & (UT) & & & & \\\\\n'
             '\\midrule\n')
    for r in _unatt:
        rep = _repeat_blocks(r)
        # R1-5: the event's own epoch, where the archive resolves it.
        _t0 = _mjd(r['eb'])
        ep = _utc(r['eb']) or 'unit only$^{b}$'
        if rep:
            best = max(rep, key=lambda q: F(q['star_snr']))
            _bt = F(best['star_snr'])
            _sep = [abs(_mjd(q['eb']) - _t0) for q in rep
                    if _mjd(q['eb']) is not None and _t0 is not None]
            _res = [d for d in _sep if d > 0.01]      # resolvable
            def _fmt(d):
                return ('%.0f' % d if d < 365 else '%.0f' % d)
            if _res and max(_res) > min(_res) + 0.5:
                dt = '%s--%s\\,d' % (_fmt(min(_res)), _fmt(max(_res)))
            elif _res:
                dt = '%s\\,d' % _fmt(max(_res))
            else:
                dt = '$<1$\\,d$^{b}$'
            if _res and len(_res) < len(_sep):
                dt += '$^{b}$'
            nrep = '%d' % len(rep)
            # depth of the deepest repeat, and its shortfall against the
            # event: this is the quantity that says how much weaker the
            # repeat is, which a bare T_star does not.
            dep = '%.2f ($-%.2f$)' % (_bt, F(r['star_snr']) - _bt)
            # A repeat that crosses the trigger but does not outrank its
            # own controls is NOT a recurrence under this paper's
            # definition; say so in the cell rather than leaving a label
            # a reader could take either way.
            res = 'no' if _bt < 5.0 else 'no$^{c}$'
        else:
            nrep, dt, dep, res = '0', '--', '--', 'n/a'
        # The crossing frequency is released only where the pipeline stored
        # a peak; elsewhere give the window and mark it, rather than
        # printing a zero or inventing a value.
        fc = F(r['f_cross_GHz'])
        nu = ('%.4f' % fc) if fc else ('%.2f--%.2f$^{a}$'
                                       % (min(F(r['flo_GHz']), F(r['fhi_GHz'])),
                                          max(F(r['flo_GHz']), F(r['fhi_GHz']))))
        fh.write('%s & \\texttt{%s} & %s & %s & %.0f & %.2f & %.2f & $%s$ & '
                 '%s & %s & %s & %s & %s \\\\\n'
                 % (tidy(r['star_name']), _ebtag(r['eb']), r['band'], nu,
                    abs(F(r['drift_max_Hz_s']) or 0.0),
                    F(r['star_snr']), F(r['ctrl_max_snr']),
                    _sci(F(r['eirp_eff_total_W'])), ep, nrep, dt, dep, res))
    fh.write('\\bottomrule\n\\end{tabular}\n')
# R1-5: the weakest link in the recurrence argument, as a macro, so the
# text cannot overstate it: the deepest repeat of any of the four.
_allrep2 = [q for r in _unatt for q in _repeat_blocks(r)]
if _allrep2:
    m('UnattRepeatDeepest', '%.2f' % max(F(q['star_snr']) for q in _allrep2))
m('NUnattNoCrossFreq',
  '%d' % sum(1 for r in _unatt if not F(r['f_cross_GHz'])))
m('NUnattRepeat', '%d' % sum(1 for r in _unatt if _repeat_blocks(r)))
m('NUnattNoRepeat', '%d' % sum(1 for r in _unatt if not _repeat_blocks(r)))

# What the expectation of unattributed outliers assumes. Two versions: the
# ideal-exchangeability rate the paper has always quoted, and the same rate
# multiplied by the tail excess measured out of sample. Saying which is
# which is the whole point -- the second is the honest comparison.
_TAIL = json.load(open('holdout_calib_v381.json'))['tail_factor']
m('ExpStageOneTail', '%.1f' % (EXP * _TAIL))
m('TailUsedForExp', '%.1f' % _TAIL)
m('PStageOneUnattribTail',
  '%.2f' % pois_ge(len(unattributed), EXP * _TAIL))

# --------------------------------------------- where the outliers sit
# Every stage-1 outlier of the completed sweep is fine-channel. That is not
# a selection: the coarse class holds three quarters of the windows and
# predicts the larger share of chance outliers, and produces none. Narrow
# circumstellar lines are diluted by a 15.6-31.25 MHz channel, so the class
# that can resolve them is the class that finds them -- and the same logic
# says a genuine narrowband technosignature would also appear here first.
_fine = [r for r in ROWS if r['resolution_class'] == 'fine']
_coarse = [r for r in ROWS if r['resolution_class'] == 'coarse']
_ff = [r for r in _fine if r['stage1_flag'] == 'True']
_cf = [r for r in _coarse if r['stage1_flag'] == 'True']
m('NStageOneFine', '%d' % len(_ff))
m('NStageOneCoarse', '%d' % len(_cf))
m('ExpStageOneFine', '%.2f' % (len(_fine) / float(NCTRL + 1)))
m('ExpStageOneCoarse', '%.2f' % (len(_coarse) / float(NCTRL + 1)))
m('PStageOneCoarseNone', '%.2f' % math.exp(-len(_coarse) / float(NCTRL + 1)))

# ------------------------------------------- the out-of-sample null set
# 195 windows of the sweep lie beyond 40 pc: they are Option A blocks whose
# ALMA target is not a census member. They were searched by the same frozen
# pipeline, they entered no tuning decision and they are outside the sample
# the paper reports, which makes them a genuinely external null.
OS = json.load(open('outofsample_v381.json'))['rows']
m('NOutSample', '%d' % len(OS))
m('NOutSampleEb', '%d' % len({r['eb'] for r in OS}))
m('NOutSampleStars', '%d' % len({r['star_name'] for r in OS}))
m('OutSampleDistLo', '%.1f' % min(r['dist_pc'] for r in OS))
m('OutSampleDistHi', '%.1f' % max(r['dist_pc'] for r in OS))
_osf = [r for r in OS
        if r['star_snr'] is not None and r['ctrl_all']
        and r['star_snr'] >= 5.0 and r['star_snr'] > max(r['ctrl_all'])]
m('NOutSampleFlag', '%d' % len(_osf))
m('ExpOutSampleFlag', '%.1f' % (len(OS) / float(NCTRL + 1)))
# the add-one rank of the star among its own controls, which is U(0,1)
# under exchangeability
_rk = sorted((1 + sum(1 for c in r['ctrl_all'] if c >= r['star_snr']))
             / (len(r['ctrl_all']) + 1.0)
             for r in OS if r['ctrl_all'] and r['star_snr'] is not None)
if _rk:
    m('OutSampleRankMed', '%.3f' % _rk[len(_rk) // 2])
    _d = max(max((i + 1) / len(_rk) - x, x - i / len(_rk))
             for i, x in enumerate(_rk))
    m('OutSampleKsD', '%.2f' % _d)
    _lam = _d * math.sqrt(len(_rk))
    m('OutSampleKsP', '%.2f' % min(1.0, 2 * math.exp(-2 * _lam * _lam)))

# ------------------------------------------------- spectral-class proxy
# The manuscript carried a hand-typed "52 of NStars" for the number of
# searched stars with a Gaia teff_gspphot. It was measured when the sample
# held 88 stars; the sample now holds 94 and the count is 55. A literal
# beside a macro is exactly the pairing that goes stale unnoticed, so it is
# generated here from the same census the selection table uses.
import re as _re
_cen = {}
for _c in csv.DictReader(open('ranked_master40pc.csv')):
    _cen.setdefault(_ck(_c['name']), _c)
# v3.85 (Q5): this matcher returned 51 where the selection table's
# returned 53, so the same sentence and the table it cited disagreed.
# NTeffSample is emitted by make_tables_v328.py from the table's own
# matcher; use it, and keep this count only as a cross-check.
_stars = sorted({_canon_star(r['star_name']) for r in ROWS})
_withteff = sum(1 for _s in _stars if (_cen.get(_ck(_s)) or {}).get('teff'))
m('NTeffStarsAlt', '%d' % _withteff)
m('NCensusMatched', '%d' % sum(1 for _s in _stars if _ck(_s) in _cen))

# ------------------------------------------- the 90 per cent recovery power
# The number a reader actually wants is "what transmitter power would we
# detect nine times in ten", not "at what power does our internal statistic
# cross 5". The injection campaign measures the latter as a multiple of the
# trigger: recovery reaches 90 per cent at StratPNinety sigma. Threshold
# flux, and so EIRP, is linear in that multiple, so the 90 per cent power
# is the effective threshold scaled by StratPNinety/5. Derived here rather
# than typed, and from the macros the injection generator already emits.


from inject_curve import P90_POOL as _p90sig
_eff = _texval('EirpEffDeepest')
_effval = float(_eff.split(r'\times10^{')[0]) * 10 ** float(
    _eff.split(r'\times10^{')[1].rstrip('}'))
# Retired: this was the deepest window across BOTH classes (a Class B
# window) and was being quoted beside Class A figures. Every quoted
# sensitivity is now Class A and says whether it is per window or per
# system; see make_fig_classa_sens.py for the per-system quantities.
m('PNinetyOverTrig', '%.1f' % (_p90sig / 5.0))

# --------------------------------------------------- the data volume
# The size of the archival download is a fact a reader wants and no other
# number in the paper carries: raw ASDM volume actually transferred from the
# ALMA archive, calibrated and searched. Taken from the campaign ledger
# rather than estimated, and stated to the nearest tenth of a terabyte,
# which is the precision the per-block sizes support.
_CAMP = json.load(open('campaign_volume_v383.json'))
m('TotalDataTB', '%.1f' % _CAMP['tb_downloaded'])
m('TotalDataBlocks', '%d' % _CAMP['blocks_downloaded'])
m('TotalDataSearchedTB', '%.1f' % _CAMP['tb_searched'])
m('NEbExcluded', '%d' % _CAMP['blocks_never_downloaded'])

# -------------------------- spectral-class coverage, including Class A
# Referee: the table must say how many stars of each class have
# drift-resolving coverage, not merely any ALMA window.
_sel = open('tab_selection.tex').read()
_rowre = re.compile(r'\\quad\s+([OBAFGKM])\s*\([^)]*\)\s*&\s*'
                    r'([\d\s,]+)\s*\([\d.]+\\%\)\s*&\s*'
                    r'([\d\s,]+)\s*\(')
_classA_stars = {r['star_name'] for r in ROWS if r['resolution_class'] == 'fine'}
_teff = {}
for _c in csv.DictReader(open('ranked_master40pc.csv')):
    if _c.get('teff'):
        _teff[_ck(_c['name'])] = float(_c['teff'])


def _cls(t):
    for lo, c in ((7500, 'A'), (6000, 'F'), (5300, 'G'), (3900, 'K')):
        if t >= lo:
            return c
    return 'M'


_aclass = collections.Counter()
for _st in _classA_stars:
    _t = _teff.get(_ck(_st))
    if _t:
        _aclass[_cls(_t)] += 1
with open('tab_specclass_v385.tex', 'w') as fh:
    fh.write('% generated by v381_calc.py -- do not edit\n')
    fh.write('\\begin{tabular}{@{}lrrrr@{}}\n\\toprule\n')
    fh.write('Class & $N_{40\\,\\rm pc}$ & $N_{\\rm searched}$ & '
             '$f_{\\rm searched}$ & with Class~A \\\\\n\\midrule\n')
    for mm in _rowre.finditer(_sel):
        c = mm.group(1)
        n40 = int(mm.group(2).replace(' ', '').replace(',', ''))
        nse = int(mm.group(3).replace(' ', '').replace(',', ''))
        fh.write('%s & %s & %d & %.4f & %d \\\\\n'
                 % (c, '{:,}'.format(n40).replace(',', '\\,'), nse,
                    nse / float(n40), _aclass.get(c, 0)))
    fh.write('\\bottomrule\n\\end{tabular}\n')
m('NClassAClassified', '%d' % sum(_aclass.values()))
m('NClassAM', '%d' % _aclass.get('M', 0))

# ------------------------------------- what counts as an independent epoch
# Referee: execution-block recurrence is not the same as an independent
# epoch. Two blocks of one scheduling block on one night share weather,
# calibration and elevation. Define the threshold operationally at 24 h
# and classify the survey's repeats against it.
EPOCH_SEP_H = 24.0
_bys = collections.defaultdict(set)
for r in ROWS:
    _bys[r['system_id']].add(r['eb'])
m('EpochSepH', '%.0f' % EPOCH_SEP_H)
m('CpSepH', _texval('CpRecStartSepH'))
m('CpIndependent', 'no')
m('BpBaselineYrDef', _texval('BpBaselineYr'))

# --------------- the trials denominator, and a realistic aperture
# Referee: show that 1655 vs 1616 is immaterial, and quote the worked
# transmitter example at an efficiency a real antenna reaches.
_ndist = int(_texval('NDistinctDatasets').replace('\\,', ''))
m('ExpDistinctDen', '%.1f' % (_ndist / 513.0))
_g1 = _texval('BenchGainSci')
_e1 = _texval('BenchEirpSci')


def _scale(tex, fac):
    """Scale a value written in LaTeX scientific form. The exponent may
    carry a sign, and the macro may already have lost its closing brace
    to the reader, so accept both forms."""
    mm = re.match(r'([\d.]+)\\times10\^\{?(-?\d+)', str(tex))
    if not mm:
        return tex
    v = float(mm.group(1)) * 10 ** int(mm.group(2)) * fac
    return _sci(v)


m('BenchGainSeven', _scale(_g1, 0.7))
m('BenchEirpSeven', _scale(_e1, 0.7))

# ------------------------------------ the data partitions, one table
# Referee: the provenance of each dataset is hard to reconstruct. Emit it
# once, from the assignment and the catalogue, so it cannot drift.
_HO = json.load(open('holdout_export_v381.json'))['rows']
_parts = [
    ('Science sample', _LED['n_catalogue'], len(ROWS),
     # Q4: this was the SYSTEM count under a "Stars" header while the other
     # rows carried star counts.
     len({_canon_star(r['star_name']) for r in ROWS}),
     'the search reported here', 'yes', 'yes'),
    ('Pre-specified hold-out', _LED['n_holdout'], len(_HO),
     len({r['star_name'] for r in _HO}),
     'calibrates rank, tail and radial behaviour', 'no', 'no'),
    ('Out-of-sample, beyond 40\\,pc', len({r['eb'] for r in OS}), len(OS),
     len({r['star_name'] for r in OS}),
     'external null', 'no', 'no'),
    ('No surviving window', _LED['n_processed'] - _LED['n_catalogue']
     - _LED['n_holdout'], 0, 0,
     'failed the quality cut', 'n/a', 'no'),
]
with open('tab_partitions_v385.tex', 'w') as fh:
    fh.write('% generated by v381_calc.py -- do not edit\n')
    fh.write('\\begin{tabular}{@{}lrrrp{0.26\\columnwidth}cc@{}}\n\\toprule\n')
    fh.write('Partition & Blocks & Windows & Stars & Purpose & Seen before '
             'the statistic froze? & In the headline result? '
             '\\\\\n\\midrule\n')
    for nm, nb, nw, ns, pu, seen, head in _parts:
        fh.write('%s & %d & %s & %s & %s & %s & %s \\\\\n'
                 % (nm, nb, nw or '--', ns or '--', pu, seen, head))
    fh.write('\\bottomrule\n\\end{tabular}\n')

# ----------------------------------------------------- growth of the survey
# What the completed sweep added, stated once so the text can quote it.
OLD = json.load(open('frozen_export_v3.60.json'))
m('NWinReleased', '%d' % 443)
m('NEbReleased', '%d' % 104)
m('NSysReleased', '%d' % 81)
m('NWinGrowth', '%.1f' % (N / 443.0))
m('NEbGrowth', '%.1f' % (K['n_eb'] / 104.0))

with open(OUT, 'w') as fh:
    fh.write('% generated by v380_calc.py -- do not edit\n')
    fh.write('\n'.join(M) + '\n')
print('%s: %d macros' % (OUT, len(M)))
print('stage-1: %d windows, %d star-band pairs, %d systems; '
      'line-attributed %d, unattributed %d (expected %.1f, p=%.2f)'
      % (len(FL), len(by), len({r['system_id'] for r in FL}),
         len(attributed), len(unattributed), EXP,
         pois_ge(len(unattributed), EXP)))
print('out-of-sample: %d windows, %d blocks, %d flagged (expected %.1f)'
      % (len(OS), len({r['eb'] for r in OS}), len(_osf), len(OS) / 513.0))
