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
MINIMUM_DURATION = 10*60

# Maximum duration of a coordination.
MAXIMUM_DURATION = 40*60;


def generate_timestamp_from_time(time_str):
    coordination_day = '2018-04-10'
    timezone = 'UTC'
    date_format = '%Y-%m-%d %H:%M:%S %Z'
    date_template = coordination_day + ' {0} ' + timezone
    res = time.mktime(time.strptime(date_template.format(time_str), date_format))
    timezone_offset = -1 # offset in hours with respect to UTC
    return res + timezone_offset * 3600 

# Start time of coordinations.
START_TIME = generate_timestamp_from_time('9:30:00')

# Maximum time over which the coordination can not go.
MAXIMUM_TIME = generate_timestamp_from_time('23:00:00')

# Scheduled breaks.
BREAK_TIMES = [[generate_timestamp_from_time('12:30:00'),
                generate_timestamp_from_time('13:45:00')],
               [generate_timestamp_from_time('18:00:00'),
                generate_timestamp_from_time('18:20:00')]]
