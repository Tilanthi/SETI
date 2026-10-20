#!/usr/bin/env python3
r"""GATE: two generators may not publish one quantity under two unrelated names.

★★★ WHY THIS EXISTS, AND WHY NOTHING ELSE IN THIS TREE COULD SEE IT.
On 2026-10-08 two agents published the SAME FOUR QUANTITIES fourteen minutes
apart.  Round 590 emitted `\PsSheikhNHz` = 200, `\PsDriftPctSheikh` = 6,
`\PsJupAccel` = 2.2 and `\PsAccelRotRatio` = 0.61 because the front matter
needed the drift ceiling in nanohertz; round 37 emitted `\AccelSheikhNHz`,
`\AccelSheikhPct`, `\AccelJupRot` and `\AccelJupPct` with the same values
because a figure caption needed them.  One referee point touched a caption and
the abstract, and the ownership table gave the item to one of the two agents.

Every gate in the build was blind to it:

  * `roundcollide` compares round FILENAMES and owners.  Two different rounds
    written by two different generators is exactly what it is designed to
    permit.
  * `twinmacro` and `synmacro` group macros by NAME STEM.  `Ps` and `Accel`
    are not related strings, so the two families never reduce to one stem, and
    `twinmacro` goes further and skips a same-stem group whose members AGREE:
    "same value under two names: harmless".  For a twin it is the opposite of
    harmless -- agreement today is what hides the divergence tomorrow.
  * `macrosyn` compares pairs declared in advance.  Nobody declares a pair
    that nobody knows exists.

So the hazard is not two agents claiming one round number.  It is **two agents
independently publishing one quantity under two names**, and the only signal
available to a mechanical check is that the two print the same number with the
same unit in the same document.

★ THE SIGNAL, AND WHY THE UNIT IS LOAD-BEARING.  Grouping cited macros by
value alone is useless in this tree: 139 cross-generator groups, almost all of
them small integers counting different sets (24 flagged crossings, 24 systems
at 10^15 W, 24 Band 8 windows).  A bare count's identity is carried by the
noun beside it, and `synmacro`, `intsweep` and `twinmacro`'s DENOM table
already work on counts.  What distinguishes a quantity is its UNIT, and the
unit is in the prose: the manuscript writes `\CvUnionA\,GHz`, `\LsLupDv
\,km\,s$^{-1}$`, `\SensMultA\,P_{\rm trig}`.  So this gate reads the unit from
the USE SITE, groups on (value, unit), and reports only groups whose members
come from more than one generator.  That brings 139 down to 17, every one of
which is worth a human sentence -- and the round-590 collision is three of
them.

★★ TWO WAYS TO RESOLVE A GROUP, AND THEY MEAN DIFFERENT THINGS.

  1.  **The names are one quantity.**  Then the right declaration is
      `twinmacro.SAME`, which REQUIRES THE VALUES TO AGREE for ever and is
      protected from retirement.  A group all of whose members are pairwise
      covered there is resolved here, because the equality is enforced by a
      gate that fails when it breaks.  Declaring it here instead would be a
      whitelist for the defect.
  2.  **The names are different quantities that happen to agree.**  Then the
      declaration belongs in `COINCIDENCE` below, with a one-line reason
      naming what each one is.  No numeric assertion is made: a check that
      fires only when two independent numbers happen to agree can only fail on
      good data, which is as useless as a check that cannot fail.

Anything else is a FAILURE, and the fix is a decision rather than an entry.

    python3 valuetwin.py [--drive N] [--all]

`--all` also lists the single-generator groups and the unit tally.
Exit 1 on any undeclared group, on a stale declaration, or if the sweep went
blind.  --drive 1..4 each break one clause and must fire.
"""
import collections
import glob
import os
import re
import sys

import manuscript

HERE = os.path.dirname(os.path.abspath(__file__))
DRIVE = 0
if '--drive' in sys.argv:
    DRIVE = int(sys.argv[sys.argv.index('--drive') + 1])
ALL = '--all' in sys.argv

# ---------------------------------------------------------------------------
# THE UNITS, DECLARED.  Longest first: `kHz` must not be read as `Hz`, and
# `km\,s^-1` must not be read as `m`.  A use whose tail matches none of these
# contributes nothing to a group, and V2 below requires the sweep to have
# recognised a unit for a substantial number of uses, so the list cannot
# silently go stale and leave the gate measuring nothing.
UNITS = [
    ('GHz', r'\\,?GHz'),
    ('MHz', r'\\,?MHz'),
    ('kHz', r'\\,?kHz'),
    ('nHz', r'\\,?nHz'),
    ('Hz s^-1', r'\\,?Hz\\,?s\$\^\{?-1'),
    ('Hz', r'\\,?Hz(?![A-Za-z])'),
    ('km s^-1', r'\\,?km\\,?s\$\^\{?-1'),
    ('m s^-2', r'\\,?m\\,?s\$\^\{?-2'),
    ('K km s^-1', r'\\,?K\\,?km\\,?s'),
    ('W m^-2', r'\\,?W\\,?m\$\^\{?-2'),
    ('MW', r'\\,?MW'),
    ('W', r'\\,?W(?![A-Za-z])'),
    ('mJy', r'\\,?mJy'),
    ('Jy', r'\\,?Jy(?![A-Za-z])'),
    ('per cent', r'\{?\}?\s*(?:per\s+cent|\\%)'),
    ('sigma', r'\$?\\sigma\$?'),
    ('P_trig', r'\\,?P_\{\\rm\s+trig\}'),
    ('arcsec', r'\\,?arcsec'),
    ('pc', r'\\,?pc(?![A-Za-z])'),
    ('au', r'\\,?au(?![A-Za-z])'),
    ('dex', r'\\,?dex'),
    ('GB', r'\\,?GB'),
    ('TB', r'\\,?TB'),
    ('K', r'\\,?K(?![A-Za-z])'),
    ('day', r'\\,?days?(?![A-Za-z])'),
    ('yr', r'\\,?yr(?![A-Za-z])'),
    ('h', r'\\,?h(?![A-Za-z])'),
    ('mm', r'\\,?mm(?![A-Za-z])'),
    ('m', r'\\,?m(?![A-Za-z])'),
    ('s', r'\\,?s(?![A-Za-z])'),
]

# ---------------------------------------------------------------------------
# COINCIDENCE: different quantities, equal value, equal unit.  One line each,
# saying what each member is.  Keyed on the sorted tuple of names.
COINCIDENCE = {
    # ★ v4.24: two unrelated 95 per cents, and the collision is a
    # coincidence of rounding.  \CeCovPct is a CONFIDENCE LEVEL -- the
    # coverage of the interval the chance comparison quotes.
    # \ScNearWinPct is the share of the screened crossing's OWN WINDOW
    # that lies within the telluric radius of the same water line, which
    # is the measurement behind the paper's statement that the screen is
    # not sharp where it fires.  Neither is derived from the other and
    # neither moves with it.
    ('CeCovPct', 'ScNearWinPct'):
        'the coverage of the quoted chance interval, and the fraction of '
        'the one screened crossing\'s own window inside the same telluric '
        'radius of the same transition: a confidence level and a share of '
        'a window, both rounding to ninety-five per cent',
    # ★★ v4.23: three groups opened by round 961 (Proxima b against the
    # stacked limit's tolerance).  Each is a per cent of a different thing,
    # and none is derived from any other member; they are declared rather
    # than whitelisted so that a member drifting apart stays visible.
    ('PxIsoPct', 'SfPlxWorstPct'):
        'the fraction of randomly oriented orbits face-on enough for the '
        'stacked limit to apply to Proxima b, and the largest fractional '
        'parallax error in the sample: an orientation fraction and a '
        'measurement error, both two and a half per cent',
    ('AccelSheikhPct', 'PxBlockPct'):
        'the drift ceiling searched here as a fraction of a recommended '
        'one, and the velocity a transmitter on Proxima b gains inside the '
        'longest stacked block as a fraction of one channel: a fraction of '
        'somebody else\'s recommendation and a fraction of our own channel',
    ('PxFracSampled', 'XlBandPct'):
        'the share of Proxima b\'s velocity excursion the stacked epochs '
        'sample at the least favourable phase, and the share of the '
        'searched band covered by a differently chosen line list: two '
        'coverage fractions of unrelated things',
    ('BpicDvCoHi', 'LsLupDv'):
        'the largest offset of a beta Pic CO crossing from its transition, '
        'and the offset of the Lupus crossing from the foreground cloud '
        'velocity a published survey gives: two unrelated velocity residuals '
        'that both round to half a kilometre per second',
    # ★ r16: `\CdSpecBpWorst` joined this group.  It has existed since round
    # 530 but was uncited until Appendix B quoted it this round, and
    # `valuetwin` groups CITED macros, so a declaration that was complete
    # yesterday became a V1 and a stale V3 at once.  That is the gate working:
    # the fifth member is the one specification in the group that an external
    # document sets, so it is exactly the member whose drifting away from one
    # per cent must be visible rather than absorbed.
    # ★ v4.20: and a FIFTH member arrived the same round the fifth one left.
    # `\TrapPhaseLo` is no longer cited (the TRAPPIST-1 b phase fraction is
    # not robust in sign and the text no longer prints it), and `\ZtFwPct`
    # -- the family-wise false-alarm probability the recurrence confirmation
    # threshold is now derived from -- took its place at one per cent.  It is
    # the only member of the group this paper CHOOSES; the other four are
    # measured or specified, so its drifting away from one per cent is a
    # decision and must stay visible.
    # ★ r20: \SmcValWorstPct JOINED this group, from the eight-per-cent one
    # below.  It is the largest disagreement between the applied smearing
    # correction and the campaign re-scoring that validates it, and adopting
    # the integrated channel response in place of the transform-limited form
    # took it from eight per cent to one: the two routes now agree far more
    # closely, which is a consequence of the adoption and not a coincidence
    # with anything in this group.
    ('CdSpecBpWorst', 'DutyAttenDevPct', 'SensDecorPct', 'SmcValWorstPct',
     'StkFapCeil', 'ZtFwPct'):
        'the worst-band bandpass accuracy specification, the duty-cycle '
        'attenuation residual, the decorrelation term of the budget, the '
        'largest disagreement between the applied smearing correction and '
        'the campaign re-scoring that validates it, the '
        'stacked false-alarm ceiling and the declared family-wise '
        'false-alarm probability of the recurrence confirmation threshold: '
        'six quantities whose only common property is that each is one per '
        'cent',
    # ★ v4.20: an instrumental percentile and a success rate, both 21.
    ('HjEtaFracOkPct', 'NmNetOptPct', 'RpDecMatchHi'):
        'the share of injected realisations in which the drift fitted to '
        'eta Crv\'s discovery block lands within half a grid step of the '
        'truth in its much longer repeat block, the optimism of the net bias '
        'at the ninetieth percentile of the systems\' own best windows, and '
        'the upper end of the matched decorrelation bracket: a success rate '
        'of a drift fit, a net bias and a phase-loss percentile.  The second '
        'and third are both built from the decorrelation measurement, which '
        'is why they are not independent -- but one is a percentile of the '
        'correction over unmeasured blocks and the other the NET of two '
        'opposed terms over the systems\' headline windows, and either moves '
        'without the other',
    # ★ v4.20: both are a fraction of a statistic lost to a half-step error,
    # and they are not the same statistic, the same stage or the same error.
    ('PxaShiftWinPct', 'RjDriftPct'):
        'the median deepening of a Class A window limit on applying the '
        'annual-parallax retention alone, and the fraction of the recurrence '
        'statistic that half a step of a window own drift grid costs when it '
        'is carried into the repeat reading: a limit shift in the '
        'sensitivity chain and a drift-fit loss in the recurrence chain, '
        'from two generators that do not read each other, both 0.4 per cent',
    # ★ r16: both arrived this round, from two generators that do not read
    # each other, and nothing connects them but the digits.
    #: ★ v4.22: `\CxResidBestPct` LEFT THIS GROUP -- Appendix B's amplitude
    #: paragraph is written from the whole-survey census of round 640 now and
    #: that macro has no citation, so the pair is no longer a cross-generator
    #: group at all.  The entry is deleted rather than kept, which is what V3
    #: asks for; the note survives here so that nobody re-adds it.
    # ★ r17: `\BmFloorTolPct` (round 720) joined this group -- the same
    # mechanism the r16 note above records, a macro that existed and became
    # cited.  Membership updated rather than a second entry added, which is
    # what V3 is for.
    # ★ r18: `\NmOwnDevPct` (round 740) joined it, by the same mechanism
    # again; membership updated rather than a second entry added.
    # ★ `\CeRCritPct` (round 310) joined it, by the mechanism the notes above
    # record for the third time; membership updated rather than a second
    # entry added.
    ('BmFloorTolPct', 'CeRCritPct', 'DutyCycleMinPct', 'NmOwnDevPct',
     'RingRhoBoundPct'):
        'the departure between the two primary-beam forms at which the '
        'retention floor is placed, the smallest duty cycle the '
        'intermittency campaign injected, the bound on the star-to-ring '
        'correlation, the largest departure of an injected window\'s own '
        'recovery factor from the class average over the six systems whose '
        'headline window was injected into, and the DEFICIT at the star that '
        'the observed count would need in order to stand above chance; five '
        'unrelated ten per cents, one a chosen tolerance, one an injected '
        'parameter, two measured and one the inversion of a comparison',
    # ★ r18: both are measurements, from two generators neither of which
    # reads the other, and nothing connects them but the digits.
    ('NmDecSysMedPct', 'StModelAgreePct'):
        'the median decorrelation correction over the systems\' own best '
        'windows, and the agreement between the stacked-sensitivity model '
        'and the stack it describes: two different three per cents',
    # ★ r17: `\CeMaskPct` LEFT this group -- it was 20 and is now 29, because
    # r17-null re-measured it on the channels the control maxima actually
    # land on instead of on the share of the grid (R2-3).  `\CeUnifPct`
    # joined.  So this is the same declaration about a changed membership,
    # and the macro that left has its own entry below.
    #: ★ v4.22: `\CdSpecTsysHi` out, `\CySpecTsysHi` in -- the same
    #: specification, republished by the generator that now owns the
    #: amplitude paragraph.  Membership updated, not a second entry added.
    ('CeUnifPct', 'CySpecTsysHi', 'PlxAdqlPct'):
        'the upper end of the residual T_sys specification, the uniform-'
        'channel share the chance expectation is compared against, and the '
        'parallax-error cut of the sample query; three different twenty per '
        'cents, from a specification, a measurement and a query',
    #: ★ v4.22, four new cross-generator groups, all of them digits.
    ('WdBandKms', 'XlLupNamedDv'):
        'the half-width in velocity over which a carrier is counted as '
        'within the searched band, and the offset of the one OCS transition '
        'that reaches a Lupus crossing: a search tolerance and a measured '
        'line offset, both fifteen kilometres per second',
    ('ChanBModeMHz', 'ScBhChanMHz'):
        'the modal Class B channel width over the whole coarse sample, and '
        'the channel width of the 38 coarse windows that satisfy the drift '
        'criterion.  The second is a subset of the first and takes the same '
        'value because the subset is selected on track length and not on '
        'channelisation; either could move without the other the moment the '
        'coarse sample gains a mode',
    ('McEuMax', 'XlEuMax'):
        'the upper-state energy ceiling of the frozen attribution mask, and '
        'the ceiling of the wider query the mask is compared against.  The '
        'comparison is deliberately made at the same cut, so the agreement '
        'is construction and not a twin -- but the two lists are built by '
        'different generators from different catalogues and neither reads '
        'the other',
    ('CvConfGHzYr', 'ScBhNewBandGHz'):
        'the confirmable frequency coverage lost when the confirmation '
        'criterion is read over a year rather than a day, and the frequency '
        'the 38 drift-resolving Class B windows would add outside the '
        'Class A union: a coverage loss and a coverage gain, in different '
        'sections and from different data, both eight and a half gigahertz',
    ('CeMaskPct', 'TrapPhaseHi'):
        'the share of the chance expectation the line attribution takes, '
        'measured on the channels the control maxima land on, and the larger '
        'of the two TRAPPIST-1 b phase fractions: an attribution share and '
        'an orbital phase, both twenty-nine per cent',
    # ★★ NOT a coincidence of digits: a DRIFT SEARCH CANNOT FIT A DRIFT
    # BEYOND ITS OWN GRID.  `\WdAGrid` is the smallest per-window
    # acceleration ceiling the grid reached and `\ZtALosHi` is the largest
    # line-of-sight acceleration actually fitted among the tested crossings
    # (3.6388 m s^-2), and `recurnull_v413.py` asserts that the second does
    # reach the first -- which is why the ceiling is the honest place to put
    # the bound.  They agree at one decimal place by construction and they
    # are still two quantities: the grid could be widened without any
    # crossing moving, and a slower crossing population would leave the
    # ceiling untouched.  Declared here, with the direction stated, rather
    # than in twinmacro.SAME, which would wrongly enforce equality.
    ('WdAGrid', 'ZtALosHi'):
        'the drift grid\'s own acceleration ceiling and the largest '
        'line-of-sight acceleration fitted to a tested crossing.  The fitted '
        'maximum sits AT the grid edge -- 3.6388 m s^-2 against a smallest '
        'per-window ceiling that rounds to the same 3.6 -- so the agreement '
        'is construction and not numerology, and either could move without '
        'the other',
    ('BmEpsAgreePct', 'NmNetConsPct', 'StkMadZScatterPct'):
        'the worst departure between the Gaussian and blocked-aperture beam '
        'forms over the restored epsilon Eridani offsets, the conservatism '
        'of the net bias in the median window, and the median-'
        'absolute-deviation scatter of the stacked z statistic: a beam-model '
        'agreement, a net bias and a noise scatter, all three seven per '
        'cent',
    ('LsMaskAddPct', 'SensCovWorstPct'):
        'the extra bandwidth the second mask frame costs, and the worst '
        'per-window coverage shortfall of the injection campaign',
    # ★ RETIRED (v4.21): ('AccelSheikhPct', 'HOFracHiPct') -- the hold-out
    #   exclusion fraction was cited only in Appendix B's rank-displacement
    #   paragraph, which went with this round's discretionary appendix
    #   paragraphs, so the two are no longer a cross-generator group.  Both
    #   quantities are unchanged and both are still computed.
    ('InjShortPct', 'SensDecorHiPct', 'TnCtrlCenHi'):
        'the shortfall of the injected channel response against the exact '
        'lag window, the upper decorrelation bracket, and the worst of the '
        'four displaced-window controls on the line-mask tuning: three '
        'unrelated eight per cents, from an injection, a bracket and a '
        'control.  \\SmcValWorstPct left this group when the integrated '
        'channel response was adopted and the two smearing routes came into '
        'one-per-cent agreement',
    ('PctDiscProposal', 'RcPowerLevel'):
        'the share of the searched blocks whose proposals targeted discs, and '
        'the recovery level the recurrence probabilities are quoted at; both '
        'ninety per cent and neither derived from the other',
    ('CovNuMaxAtRef', 'CvConfNuMaxDay'):
        'the frequency at which most systems are covered at the benchmark '
        'power, and the frequency at which confirmation coverage peaks: two '
        'maxima of two different curves, both in the CO(2-1) band, so both '
        'land on the same tuning',
    ('SurvFreqHi', 'SurvFreqHiA'):
        'the archival extent, which the title states, and the Class A extent '
        'inside it (R1-5).  The two share their UPPER end and not their '
        'lower, which is why the pair cannot be declared one quantity; '
        'synmacro carries the lower-end pair for the same reason',
    ('DomAFreqHi', 'TlFreqHi'):
        'the top of the Class A coverage, and the top of the interval the '
        'telluric line list was built over -- the list was deliberately built '
        'to the coverage, so the agreement is construction and not a twin',
    #: ★ v4.22: `\RgOffMaxChanKHz` joined -- the channel width of the block
    #: holding the largest entry of Table D2's offset column, which is the
    #: finest-channel block for the same reason the best flux limit is.
    ('FluxChanBestKHz', 'RgOffMaxChanKHz', 'SzChanFinestKHz'):
        'the channel width of the window that sets the best flux-density '
        'limit, the channel width of the block with the largest predicted-'
        'cell offset, and the finest channel width anywhere in the survey.  '
        'They are the same width because the finest channelisation is what '
        'makes an offset largest in channels and a limit best in flux, and '
        'they are different quantities because any of the three could move '
        'without the others',
    # ★ `\CdSpecTsysRes` joined this group when it began printing its source
    # record's own fourth digit (31.25 where it had printed 31.2): the
    # resolution and the two channel widths were always the same number and
    # the rounding was hiding it.
    ('CdSpecTsysRes', 'SbBoneChanMHz', 'SzChanWidestMHz'):
        'the resolution at which the system temperature is measured, the '
        'channel width of the Band 1 continuum mode, and the widest channel '
        'in the survey: one is a property of the calibration mode and the '
        'other two of the searched data, and any of the three could move '
        'without the others -- the first because a system temperature can be '
        'measured on any channelisation, the last two because they are the '
        'extremes of sets that change with the sample',
    ('ChanAMedKHz', 'EvAChanwkHz'):
        'the MEDIAN Class A channel width, and the channel width of the one '
        'window carrying the leading crossing; the second is one draw from '
        'the distribution the first summarises',
    # ★ r16: `\SqrtScaleChanKHz` REMOVED from this key, not whitelisted away.
    # Appendix A.1's illustrative "rechannelising to a dedicated narrowband
    # search" sentence was cut for length, so that macro is no longer cited
    # and the group is five, not six.  The gate named the fix itself.
    # ★ r17: and `\BkEpsOnChanFineKHz` has now left it the same way.  The
    # epsilon Eridani limits are quoted as EIRP_90 from round 720 instead of
    # as the nominal trigger powers `bookkeep_r13.py` published, so the
    # `\BkEpsOn...` family is uncited and the group is four.
    #: ★ v4.21: TWO NAMES NOW, NOT FOUR.  `\TjChanKHz` was cited in the one
    #: sentence R2-10(a) rewrote -- it quoted a full channel width where the
    #: tolerance is half a channel, and the sentence now prints
    #: `\RqHalfChanKHz` instead -- so the macro lost its only citation and
    #: was retired; `\ChanFineKHz` is uncited as well.  The entry is kept
    #: rather than deleted because the two that remain still form a group,
    #: and they are the state this entry exists to make visible.
    #: ★ v4.22: `\RgWalkChanKHz` joined -- the channel width of the block
    #: whose carried-drift walk is largest, which is the modal fine width
    #: again and from a third generator.
    ('FluxChanMedKHz', 'RgWalkChanKHz', 'StkRefChanKHz'):
        'the fine-channel width in three roles -- the median of the flux-'
        'limit sample, the channel of the block with the longest drift walk, '
        'and the stacking reference.  Both are the same physical '
        'correlator setting and neither is derived from the other; they move '
        'apart the moment either subset changes, which is the state this '
        'entry exists to make visible',
}


def _macro_layer():
    """{name: (value, generator)} in the manuscript's own \\input order, with
    one-level aliases followed, so the value is what pdflatex would typeset
    and the generator is the file whose header claims the round."""
    mainsrc = open(os.path.join(HERE, manuscript.main_file()),
                   encoding='utf-8').read()
    order = [m + '.tex' for m in re.findall(
        r'\\input\{(survey_numbers[A-Za-z0-9_]*)\}', mainsrc)]
    # ★ a leftover `--drive` product matches `survey_numbers*.tex` and would
    # join the layer silently, which is how a perturbed value could reach a
    # gate.  The agent rules call a stray drive output in the build root out
    # by name; this gate refuses to read one even if it is there.
    have = {os.path.basename(p) for p in
            glob.glob(os.path.join(HERE, 'survey_numbers*.tex'))
            if '_drive' not in os.path.basename(p)}
    files = [f for f in order if f in have] + sorted(have - set(order))
    pat = re.compile(r'\\(?:new|renew)command\{\\([A-Za-z]+)\}\{(.*)\}\s*$',
                     re.M)
    val, gen = {}, {}
    for f in files:
        txt = open(os.path.join(HERE, f), encoding='utf-8',
                   errors='ignore').read()
        m = re.search(r'GENERATED by ([A-Za-z0-9_.]+\.py)',
                      txt.split('\n', 1)[0])
        who = m.group(1) if m else f
        for nm, body in pat.findall(txt):
            if body.strip():
                val[nm], gen[nm] = body.strip(), who
    for _ in range(6):                      # follow \Alias -> \Target chains
        for nm, v in list(val.items()):
            a = re.fullmatch(r'\\([A-Za-z]+)', v.strip())
            if a and a.group(1) in val:
                val[nm] = val[a.group(1)]
                # the ALIAS keeps its own owner: round 103's retirement pass
                # is where an alias is declared, and attributing the value to
                # it would make every retirement look like a twin.
    return {nm: (val[nm], gen[nm]) for nm in val}


def _uses(body):
    """{name: {unit}} read from the use site, and the tally of uses whose
    tail matched no declared unit."""
    body = '\n'.join(re.sub(r'(?<!\\)%.*$', '', ln) for ln in body.split('\n'))
    units = [(u, re.compile(r'\s*' + rx)) for u, rx in UNITS]
    out, blind, total = collections.defaultdict(set), 0, 0
    for m in re.finditer(r'\\([A-Za-z]+)(?:\{\})?', body):
        nm = m.group(1)
        total += 1
        tail = body[m.end():m.end() + 30]
        for u, rx in units:
            if rx.match(tail):
                out[nm].add(u)
                break
        else:
            blind += 1
    return out, blind, total


def main():
    global UNITS
    if DRIVE == 2:
        # ★ drive 2: the UNITS list goes stale -- one unit spelling changes in
        # the manuscript and the sweep stops recognising it.  Without V2 the
        # gate would then report "0 cross-generator groups, 0 FAIL" for ever,
        # which is a check that cannot fail.  Emptying the list is the
        # extreme of that, and V2 must notice.
        UNITS = [('never', r'(?!x)x')]
    layer = _macro_layer()
    body = manuscript.flat()
    uses, blind, total = _uses(body)

    # the declared same-quantity pairs, read from the gate that enforces them
    import twinmacro
    same = set()
    for pair in twinmacro.SAME:
        same.add(tuple(sorted(pair)))
    if DRIVE == 3:
        same = set()                       # drive 3: forget the SAME table

    groups = collections.defaultdict(set)
    for nm, us in uses.items():
        if nm not in layer:
            continue
        v = re.sub(r'[\\,\s{}~$]', '', layer[nm][0])
        if not re.fullmatch(r'[-+]?\d+(?:\.\d+)?', v):
            continue
        for u in us:
            groups[(v, u)].add(nm)
    if DRIVE == 1:
        # ★ THE DRIVE THAT REPRODUCES THE DEFECT.  Put the round-590 family
        # back: a second name for the Sheikh fraction, from another generator.
        layer['PsDriftPctSheikh'] = (layer['AccelSheikhPct'][0], 'prose_r15.py')
        groups[(re.sub(r'[\\,\s{}~$]', '', layer['AccelSheikhPct'][0]),
                'per cent')].add('PsDriftPctSheikh')

    multi = {k: g for k, g in groups.items()
             if len(g) > 1 and len({layer[n][1] for n in g}) > 1}
    if DRIVE == 4:
        multi = {}                         # drive 4: the sweep finds nothing

    def covered_by_same(names):
        ns = sorted(names)
        return all(tuple(sorted((a, b))) in same
                   for i, a in enumerate(ns) for b in ns[i + 1:])

    bad, by_same, by_coin, used_coin = [], [], [], set()
    for k, g in sorted(multi.items()):
        key = tuple(sorted(g))
        if covered_by_same(g):
            by_same.append((k, key))
        elif key in COINCIDENCE:
            by_coin.append((k, key))
            used_coin.add(key)
        else:
            bad.append((k, key))

    stale = [k for k in COINCIDENCE if k not in used_coin]
    print('valuetwin: %d cited macros in the layer, %d macro uses, '
          '%d with a declared unit, %d (value, unit) groups, %d '
          'cross-generator'
          % (len(layer), total, total - blind, len(groups), len(multi)))
    if ALL:
        tal = collections.Counter(u for us in uses.values() for u in us)
        print('  units seen: ' + ', '.join('%s %d' % (u, n)
                                           for u, n in tal.most_common()))
    for (v, u), key in by_same:
        print('  SAME quantity, equality enforced by twinmacro: %s %s  %s'
              % (v, u, ' = '.join('\\' + n for n in key)))
    for (v, u), key in by_coin:
        print('  coincidence: %s %s  %s' % (v, u, ', '.join('\\' + n
                                                            for n in key)))
        print('      -- ' + COINCIDENCE[key])
    fails = []
    # V1: no undeclared cross-generator (value, unit) group.
    for (v, u), key in bad:
        fails.append('V1 %s %s published by %s under %d names and declared '
                     'nowhere: %s.  Decide: one quantity (declare in '
                     'twinmacro.SAME, which enforces the equality) or a '
                     'coincidence (declare in valuetwin.COINCIDENCE with a '
                     'reason).'
                     % (v, u, ' and '.join(sorted({layer[n][1]
                                                   for n in key})),
                        len(key), ', '.join('\\' + n for n in key)))
    # V2: the sweep must not have gone blind.  A unit list that stops matching
    # turns this gate into a check that cannot fail, so require that a
    # substantial number of uses carried a recognised unit AND that the
    # cross-generator sweep had something to look at.
    if total - blind < 150:
        fails.append('V2 only %d of %d macro uses carried a unit this gate '
                     'recognises; the UNITS list has gone stale and the '
                     'sweep is measuring almost nothing' % (total - blind,
                                                            total))
    if not groups:
        fails.append('V2 no (value, unit) group was formed at all')
    # V3: a declaration whose group no longer exists is removed, not left.
    for key in sorted(stale):
        fails.append('V3 COINCIDENCE declares %s, which is no longer a '
                     'cross-generator group; delete the entry rather than '
                     'leave it' % ', '.join('\\' + n for n in key))
    if fails:
        print('  FAIL:')
        for f in fails:
            print('    ' + f)
        print('valuetwin: %d FAIL' % len(fails))
        sys.exit(1)
    print('valuetwin: %d same-quantity group(s), %d declared coincidence(s), '
          '0 FAIL' % (len(by_same), len(by_coin)))


if __name__ == '__main__':
    main()
