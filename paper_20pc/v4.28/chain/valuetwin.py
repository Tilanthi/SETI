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
    #: ★ r27 DELETED, as V3 instructs: ('CeCovPct', 'ScNearWinPct').  The
    #: length pass removed the last citation of \ScNearWinPct.
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
    #: ★ v4.26 DELETED: ('PxFracSampled', 'XlBandPct').  Sec. 5.7 keeps
    #: Proxima b's inclination condition and drops the phase-sampling
    #: fraction, so \PxFracSampled is no longer cited.
    #: ★★ v4.26, RE-KEYED A SECOND TIME, and by the OTHER mechanism: the
    #: ninety-eight-per-cent group lost `\PxFracSampled` to a cut and GAINED
    #: `\SfCensusColPct`, which has been computed by `selfunc_v411.py` since
    #: round 111 at this same value and became CITED only this round, in the
    #: sentence Sec. 3 now carries about the colour classification.  So the
    #: group was declared completely yesterday and incompletely today without
    #: any number moving -- the mechanism `r16` recorded for
    #: `\CdSpecBpWorst`, in the direction of a new citation rather than a new
    #: value.  ★ It surfaced only because no full `gate.sh` had run since the
    #: integration of 10-20 22:09; the citation and the failure were both
    #: already in the tree.
    #: ★ v4.27 DELETED, as V3 instructs rather than left stale:
    #: ('SfCensusColPct', 'XlBandPct').  \S2.1 now gives the colour rule's
    #: reach as a COUNT of census objects and no longer as a percentage of
    #: them, so \SfCensusColPct is not cited and the ninety-eight-per-cent
    #: collision cannot occur.  ★ This is the third time this one group has
    #: been re-keyed in two rounds -- v4.26 lost \PxFracSampled from it and
    #: gained \SfCensusColPct without any number moving -- which is the
    #: argument for keying these declarations on the CITED set and failing
    #: when it changes.
    # ★ r27 row 55: the field-repaired blocks move \StModelAgreePct 3 -> 2, onto
    # \BmDocAiryPct.  Unrelated: one is the per cent by which the null model's
    # trigger expectation agrees with the census sum, the other the bound on
    # CASA's documented primary-beam width error.
    #: ★ r27 merge: FT12's ('BmDocAiryPct', 'StModelAgreePct') DELETED as V3
    #: instructs -- the appendix cut removed \StModelAgreePct's last citation.
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
    #: ★ v4.27 RE-KEYED: \StkFapCeil OUT.  \S4.7's method is three sentences
    #: now and quotes the stacked false-alarm RATE measured at the controls
    #: without the ceiling it is compared against, so the macro is no longer
    #: cited.  Membership updated rather than a second entry added, which is
    #: what V3 asks for.
    #: ★ r27: \ZtFwPct LEFT this group (its last citation was cut).
    ('CdSpecBpWorst', 'DutyAttenDevPct', 'SensDecorPct'):
        'the worst-band bandpass accuracy specification, the duty-cycle '
        'attenuation residual, the decorrelation term of the budget, the '
        'largest disagreement between the applied smearing correction and '
        'the campaign re-scoring that validates it, and the declared '
        'family-wise false-alarm probability of the recurrence confirmation '
        'threshold: five quantities whose only common property is that each '
        'is one per cent',
    # ★ v4.20: an instrumental percentile and a success rate, both 21.
    #: ★★ v4.26, RE-KEYED: `\LsMaskAddPct` JOINS THIS GROUP, because A3
    #: moved it.  Taking sulphur monoxide out of the mask takes the
    #: two-frame mask's extra cost from 22 to 21 per cent, where the other
    #: two already sat -- a declaration keyed on a member tuple is
    #: invalidated by a value MOVING onto it exactly as it is by a cut
    #: removing one, which is the second way this round has found to expire
    #: one of these.  It is a coincidence of rounding and nothing else: the
    #: new member is the extra share of the Class A union the mask covers
    #: when it is evaluated in the LSR frame as well as the star's.
    #: ★★ v4.26 (A1), RE-KEYED A THIRD TIME, and by the first mechanism
    #: again: `\NmNetOptPct` LEAVES the group.  The net bias at the
    #: ninetieth percentile of the systems' own best windows is a statistic
    #: over best windows, and four systems have a different best window now
    #: that a window wholly inside the attribution mask cannot be one.  The
    #: remaining two are unchanged and still coincide.
    #: FLAGDECL: \FgLimDeepMaxPct joins -- the largest rms rise when ALMA's
    #: flags are applied, 21 per cent, from a third generator.
    ('FgLimDeepMaxPct', 'LsMaskAddPct', 'RpDecMatchHi'):
        'the extra share of the Class~A union the line mask covers when it '
        'is applied in the local standard of rest as well as in the star\'s '
        'frame; '
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
    #: ★ v4.26 DELETED: ('PxaShiftWinPct', 'RjDriftPct').  The annual-parallax
    #: term is now given by Table 4 with its range and direction instead of a
    #: median window shift in the prose, so \PxaShiftWinPct is no longer
    #: cited.
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
    #: ★ v4.27 RE-KEYED: \NmOwnDevPct OUT, \BmFloorTolPct BACK IN.
    #: \S4.1 keeps the transfer dispersion and drops the six-system
    #: re-scoring, so \NmOwnDevPct is no longer cited.
    #: ★★★ \BmFloorTolPct was taken OUT of this group on the assumption that
    #: \S2's primary-beam paragraph would point at Appendix A for the
    #: departure between the two beam forms and drop the measurement -- and
    #: `r26-cut-app` then ROUTED, in writing, that \BmFloorTolPct,
    #: \ExCWorstExt and \BmFloorC are cited ONLY in `03_sample.tex` and
    #: appear NOWHERE in Appendix A: the pointer would have been a dead end
    #: and the qualification would have been deleted rather than condensed.
    #: So the citation stays in \S2, and the declaration has to stay with it.
    #: THE GATE CAUGHT THIS EXACTLY AS WRITTEN -- V1 reported the ten-per-cent
    #: pair 'published under 2 names and declared nowhere' on the first run
    #: after the cut -- which is the whole argument for running the suite
    #: rather than reasoning about the cut.
    #: ★ ...and \CeRCritPct and \RingRhoBoundPct are OUT with it: a
    #: declaration must list exactly the CITED members, which is what makes
    #: V3 a measurement rather than a comment.  \CeRCritPct lost its site
    #: when R1 Sec. 2.1's conditionality rewrite replaced the critical-radius
    #: clause, and \RingRhoBoundPct when Sec. 4.5 came down to one paragraph.
    #: Two members left, both cited, from two generators neither of which
    #: reads the other.
    ('BmFloorTolPct', 'DutyCycleMinPct'):
        'the departure between the two primary-beam forms at which the '
        'retention floor is placed, and the smallest duty cycle the '
        'intermittency campaign injected: a model departure and an injected '
        'parameter, from two generators neither of which reads the other, '
        'both ten per cent',
    # ★ r18: both are measurements, from two generators neither of which
    # reads the other, and nothing connects them but the digits.
    #: ★ RESTORED, and the reason it was deleted is the defect R2-A6
    #: reported: v4.26 stopped citing \NmDecSysMedPct and left Sec. 4.1
    #: quoting the per-WINDOW median under the word "limit".  The
    #: per-system median is cited again, so the collision is back.
    #: ★ r27 DELETED AGAIN, as V3 instructs: ('NmDecSysMedPct',
    #: 'StModelAgreePct').  Restored in this round when \NmDecSysMedPct was
    #: cited again (R2-A6); the appendix length pass then removed the last
    #: citation of \StModelAgreePct, so the collision cannot occur.  The
    #: decorrelation median itself is still cited (Sec. 4.1, Table 4, App. F).
    # ★ r17: `\CeMaskPct` LEFT this group -- it was 20 and is now 29, because
    # r17-null re-measured it on the channels the control maxima actually
    # land on instead of on the share of the grid (R2-3).  `\CeUnifPct`
    # joined.  So this is the same declaration about a changed membership,
    # and the macro that left has its own entry below.
    #: ★ v4.22: `\CdSpecTsysHi` out, `\CySpecTsysHi` in -- the same
    #: specification, republished by the generator that now owns the
    #: amplitude paragraph.  Membership updated, not a second entry added.
    #: ★ r27: `\TwWinASharePct` JOINS -- the two objects' share of the
    #: Class A census, 20 per cent, from twostars_r27.py, which reads none of
    #: the other three.
    #: ★ r27: \CeUnifPct LEFT this group (its last typeset citation was cut).
    ('CySpecTsysHi', 'PlxAdqlPct', 'TwWinASharePct'):
        'the upper end of the residual T_sys specification, the uniform-'
        'channel share the chance expectation is compared against, and the '
        'parallax-error cut of the sample query; three different twenty per '
        'cents, from a specification, a measurement and a query, and the two '
        'objects\' share of the Class A census, a count',
    #: ★ v4.22, four new cross-generator groups, all of them digits.
    #: ★★ v4.27 DELETED, BOTH, as V3 instructs: ('ChanBModeMHz',
    #: 'ScBhChanMHz') and ('CvConfGHzYr', 'ScBhNewBandGHz').  \S3.1's
    #: drift-efficiency paragraph is two sentences now and no longer quotes
    #: the 38 drift-resolving Class B windows' own channel width or the
    #: frequency they would add outside the Class A union, so \ScBhChanMHz
    #: and \ScBhNewBandGHz are both uncited.  \ChanBModeMHz and \CvConfGHzYr
    #: keep their own citations; what has gone is the partner in each pair,
    #: so neither collision can arise.
    #: ►► IF A LATER ROUND PUTS EITHER NUMBER BACK, PUT ITS ENTRY BACK TOO:
    #: the declarations recorded real coincidences of rounding and are not
    #: wrong, only unreachable.
    ('McEuMax', 'XlEuMax'):
        'the upper-state energy ceiling of the frozen attribution mask, and '
        'the ceiling of the wider query the mask is compared against.  The '
        'comparison is deliberately made at the same cut, so the agreement '
        'is construction and not a twin -- but the two lists are built by '
        'different generators from different catalogues and neither reads '
        'the other',
    #: ★ v4.27 DELETED with ('ChanBModeMHz', 'ScBhChanMHz') above and for the
    #: same reason: \ScBhNewBandGHz is the frequency the 38 drift-resolving
    #: Class B windows would add outside the Class A union, and \S3.1 no
    #: longer quotes it.
    ('CeMaskPct', 'TrapPhaseHi'):
        'the share of the chance expectation the line attribution takes, '
        'measured on the channels the control maxima land on, and the larger '
        'of the two TRAPPIST-1 b phase fractions: an attribution share and '
        'an orbital phase, both twenty-nine per cent',
    #: ★ DELETED, as V3 instructs rather than left stale: ('WdAGrid',
    #: 'ZtALosHi').  \ZtALosHi is now the largest line-of-sight
    #: acceleration over the 33 tested crossings printed to two decimals
    #: (traj_v418.py), and no longer collides with the grid ceiling
    #: \WdAGrid at one decimal.  The old note called the agreement
    #: 'construction'; it was a gate pinned to today's rounding.
    #: ★ `\StkMadZScatterPct` and `\BmEpsAgreePct` have both LEFT this
    #: group, as V3 instructs rather than left stale.  The stacked z
    #: statistic's per-stack noise scatter was a validation result in Sec. 5.7
    #: and the stack section keeps the claim it supported (the gain is
    #: sqrt(N_eff), not sqrt(N)) with \StkGainVsN instead.  `\BmEpsAgreePct`
    #: was a SECOND recovery of the offset of the one window `\BmCensusWorstC`
    #: is measured on -- 0.8220665 lambda/D by inverting the stored response
    #: against 0.8216971 from the stored offset and beam width -- printed
    #: through `ceil` as 7 where `\BmCensusWorstPct` prints the same window as
    #: 6.2.  One window, one measurement, two roundings: the appendix now
    #: states it once and the macro is no longer cited.
        ('InjShortPct', 'SensDecorHiPct', 'TnCtrlCenHi'):
        'the shortfall of the injected channel response against the exact '
        'lag window, the upper decorrelation bracket, and the worst of the '
        'four displaced-window controls on the line-mask tuning: three '
        'unrelated eight per cents, from an injection, a bracket and a '
        'control.  \\SmcValWorstPct left this group when the integrated '
        'channel response was adopted and the two smearing routes came into '
        'one-per-cent agreement',
    #: ★ r27 DELETED, as V3 instructs rather than left stale:
    #: ('ScEdrMedPct', 'ScRsMedShiftPct').  \ScEdrMedPct is now measured over
    #: the same systems (R2-B5) and is 14.1 per cent, so the 5.5 per cent
    #: collision cannot occur.
    #: ★ v4.27 DELETED, as V3 instructs rather than left stale:
    #: ('PctDiscProposal', 'RcPowerLevel').  \RcPowerLevel -- the recovery
    #: level the recurrence probabilities are quoted at -- lost its last
    #: citation when A18 cut the single-cell recurrence report to the positive
    #: control plus one sentence, so the pair is no longer a cross-generator
    #: group and the ninety-per-cent collision cannot occur.  The note
    #: survives so that nobody re-adds the entry without re-adding a citation.
    #: ★★ v4.26 (A1), RE-KEYED: `\CvConfNuMaxDay` leaves and
    #: `\BenchFreqGHz` joins.  The coverage map is drawn over the windows
    #: that carry a limit, so its maximum moved one tuning, onto the round
    #: 230 GHz the engineering benchmark is stated at.  Both still land in
    #: the CO(2-1) band for the same reason -- it is where the archive
    #: points -- and neither is computed from the other.
    ('BenchFreqGHz', 'CovNuMaxAtRef'):
        'the frequency the illustrative engineering benchmark is stated '
        'at, a round number chosen for the example, and the frequency at '
        'which most systems are covered at the benchmark power, which is a '
        'maximum of a measured curve: a chosen tuning and a measured one, '
        'both in the CO(2-1) band because that is where the archive points',
    #: ★★ v4.26 (A1): THE GROUP IS GONE, and the reason is the result.
    #: `\FluxChanBestKHz` was the finest channel width in the survey
    #: because the window setting the best flux-density limit was the
    #: finest one; that window lies entirely inside the attribution mask
    #: and constrains nothing, so the best flux-density limit now comes
    #: from a coarser window and the two quantities have genuinely parted
    #: company.  Deleted rather than left, as V3 requires.
    # ★ `\CdSpecTsysRes` joined this group when it began printing its source
    # record's own fourth digit (31.25 where it had printed 31.2): the
    # resolution and the two channel widths were always the same number and
    # the rounding was hiding it.
    #: ★ v4.26: `\SbBoneChanMHz` LEFT this group -- the merged introduction
    #: states the Band 1 continuum mode as a RATIO to the narrowest channel
    #: searched (\SbBoneChanRatio) rather than as a width, which is the form
    #: the sentence needs.  The remaining two still collide.
    #: ★ r27 DELETED, as V3 instructs: ('CdSpecTsysRes', 'SzChanWidestMHz').
    #: The length pass removed the last citation of \CdSpecTsysRes.
    #: ★ v4.27 DELETED, as V3 instructs: ('ChanAMedKHz', 'EvAChanwkHz').
    #: \S4.5 is one paragraph now and the leading crossing's own channel
    #: width is read off Fig. 7 and Table 6 rather than quoted in prose, so
    #: \EvAChanwkHz is uncited and the median-against-one-draw collision
    #: cannot arise.
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
    ('FluxChanMedKHz', 'StkRefChanKHz'):
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
