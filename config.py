DEBUG = True

# Minimum number of significant corrections for the computation of the
# expected duration of the next correction.
# This means that, if less than this number of corrections have been done in
# the given table, fake corrections with duration APRIORI_DURATION (see below)
# are used to compute the expected duration.
NUM_SIGN_CORR = 5

# A priori duration of a correction in seconds.
APRIORI_DURATION = 20*60

# Positions lost when a team is removed from the top of the queue and
# reinserted in the queue.
LOST_POSITIONS = 3
