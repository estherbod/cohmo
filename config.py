import time

DEBUG = True

# Minimum number of significant corrections for the computation of the
# expected duration of the next correction.
# This means that, if less than this number of corrections have been done in
# the given table, fake corrections with duration APRIORI_DURATION (see below)
# are used to compute the expected duration.
NUM_SIGN_CORR = 5

# A priori duration of a correction in seconds.
APRIORI_DURATION = 20*60

# Positions skipped when the team does not appear during the call and the
# coordinators call the next team in queue.
SKIPPED_POSITIONS = 2

# Minimum duration of a coordination.
MINIMUM_DURATION = 5*60

# Maximum duration of a coordination.
MAXIMUM_DURATION = 40*60

# Start time of coordinations.
START_TIME = time.mktime(time.strptime('2018-04-06 20:30:00', '%Y-%m-%d %H:%M:%S'))

# Maximum time over which the coordination can not go.
MAXIMUM_TIME = time.mktime(time.strptime('2018-04-07 8:00:00', '%Y-%m-%d %H:%M:%S'))

# Scheduled breaks.
BREAK_TIMES = [[time.mktime(time.strptime('2018-04-07 00:00:00', '%Y-%m-%d %H:%M:%S')),
                time.mktime(time.strptime('2018-04-07 00:30:00', '%Y-%m-%d %H:%M:%S'))],
               [time.mktime(time.strptime('2018-04-07 02:00:00', '%Y-%m-%d %H:%M:%S')),
                time.mktime(time.strptime('2018-04-07 02:15:00', '%Y-%m-%d %H:%M:%S'))]]
