#!/usr/bin/env python3
"""PRE-REGISTERED thresholds for the stellar-frame multi-epoch stack (D15).

Committed 2026-09-26, BEFORE any stacked stellar spectrum was computed.  The
registration validation of step 1 (regtest.py) was run first and is the only
thing that had been looked at.  Nothing in this file may be changed after the
stack has been run; if a threshold turns out to be wrong, the run is repeated
under a NEW file with the change and the reason stated, and both are reported.

Round 6's ordering -- calibration and line mask BEFORE wording -- is what
stopped this project retracting HD 285968.  Same ordering here.
"""

# --- what is searched ----------------------------------------------------
MIN_BLOCKS = 2          # a stack needs >= 2 distinct execution blocks
MIN_COMMON_CHAN = 64    # and >= 64 channels of common stellar-frame coverage
REGISTRATION = 'nearest-integer channel'   # primary; linear interp is secondary

# --- the detection criterion, all four clauses required ------------------
Z_STACK_MIN = 6.0       # stacked Z at some common channel
CTRL_CLAUSE = True      # star's Z_max must exceed all 8 stacked control Z_max
                        # in the same group
EPOCH_DOM_MAX = 0.60    # no single epoch may supply > 60 % of the weighted sum
                        # (a persistent carrier supplies ~1/N)
JACKKNIFE_MIN = 0.50    # dropping the strongest epoch must leave >= 50 % of the
                        # expected Z, i.e. Z_-1 >= 0.50 * Z * sqrt((N-1)/N)

# --- the null ------------------------------------------------------------
# The eight control positions are stacked with the SAME transformation, the same
# weights and the same channel grid as the star.  The empirical false-alarm rate
# is the fraction of control stacks whose Z_max exceeds Z_STACK_MIN, pooled over
# every group.  Committed ceiling: if the controls themselves exceed 6.0 more
# often than this, the threshold is not calibrated and NO detection may be
# claimed at 6.0 -- the empirical 99.9th percentile of the control Z_max is
# quoted instead and the run is reported as a limit only.
CTRL_FAP_CEILING = 0.01     # 1 % of control stacks, matching round 6's ceiling

# --- what would falsify a detection -------------------------------------
FALSIFIERS = [
    'the channel lies within +-50 km/s of a frozen-mask transition in the '
    'stellar frame (attribution, per the A3 chain)',
    'any of the eight stacked controls in the same group reaches the same Z',
    'one epoch supplies more than EPOCH_DOM_MAX of the weighted sum',
    'the jackknife (drop the strongest epoch) falls below JACKKNIFE_MIN',
    'the excess does not reproduce in an independent split of the epochs',
    'the control false-alarm rate at Z_STACK_MIN exceeds CTRL_FAP_CEILING',
]

# --- measured inputs, fixed before the run ------------------------------
# From regtest.py (step 1), on real lines:
REG_ERR_CHAN_488 = 0.351     # rms epoch-to-epoch registration error, channels,
                             # HD 285968 line, 488.281 kHz, 4 epochs
REG_ERR_KMS = (0.12, 0.31)   # rms registration error in velocity, all standards
# From the ALMA 0.25/0.5/0.25 smoothed channel response, with residual
# sub-channel offsets uniform in [-0.5, 0.5] (integer_registration_loss.py):
REG_LOSS = 0.875             # realised amplitude / ideal, independent of N
# Intra-block barycentric smearing, measured over 702 blocks:
INTRABLOCK_SWING_KMS = (0.072, 0.169)   # median, max

EXPECTED_GAIN = lambda n: REG_LOSS * (n ** 0.5)

if __name__ == '__main__':
    print('pre-registered: Z>=%.1f, ctrl clause %s, epoch dominance <=%.2f, '
          'jackknife >=%.2f, control FAP ceiling %.3f'
          % (Z_STACK_MIN, CTRL_CLAUSE, EPOCH_DOM_MAX, JACKKNIFE_MIN,
             CTRL_FAP_CEILING))
    for n in (2, 4, 9, 22, 28, 63):
        print('  N=%2d  expected gain %.2f (sqrt N = %.2f)' % (n, EXPECTED_GAIN(n), n ** 0.5))
