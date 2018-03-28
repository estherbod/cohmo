from cohmo.history import Correction, HistoryManager
import enum


NUM_SIGN_CORR = 5
APRIORI_DURATION = 20*60*60


class TableStatus(enum.Enum):
    CALLING = 0
    CORRECTING = 1
    NOTHING = 2

# The coordination Table is the class that handles the queue of teams to
# be corrected from a single table.
#
# Its main properties are: table name, problem, coordinators. This properties
# should never change after the creation of the instance. A table is uniquely
# identified by its name.
#
# The internal state of a table is given by the queue (of teams to coordinate
# with) and by its status. The status can be one of: calling, correcting,
# nothing. Nothing means that the table is not correcting nor it is ready
# to start a new coordination (i.e. the coordinators are playing football).
# The history manager, that saves past coordinations, is injected into the Table
# class and is automatically invoked whenever a coordination is finished.
class Table:
    # Constructs the table from a file.
    #
    # The format for the file is the following one:
    # table name
    # problem name
    # coordinators (separated by commas)
    # queue of teams (separated by commas)
    # status (calling, correcting, nothing)
    # start_time (needed only if status == CORRECTING) # Timestamp in seconds
    # current_team (needed only if status == CORRECTING)
    def __init__(self, path, history_manager):
        self.path = path
        with open(path, newline='') as table_file:
            lines = table_file.readlines()
            assert(len(lines) >= 5)
            self.name = lines[0].strip()
            self.problem = lines[1].strip()
            self.coordinators = [coordinator.strip() for coordinator in lines[2].split(',')]
            self.history_manager = history_manager
            queue = [team.strip() for team in lines[3].split(',')]
            status_name = lines[4].strip()
            self.status = TableStatus[status_name]
            if self.status == TableStatus.CORRECTING:
                assert(len(lines) >= 7)
                self.current_coordination_start_time = int(lines[5].strip())
                self.current_coordination_team = lines[6].strip()
            else:
                self.current_coordination_start_time = None
                self.current_coordination_team = None
            self.number_made_corrections = self.get_number_made_corrections()
            self.expected_duration = self.get_expected_duration()

    # Dumps the table to file. The format is the same as create_table_from_file.
    # It should be remarked that the current status of the table (whether it is
    # currently correcting is lost when doing this operation).
    def dump_to_file(self, path=None):
        if path is None: path = self.path
        with open(path, 'w', newline='') as table_file:
            table_file.write(self.name + '\n')
            table_file.write(self.problem + '\n')
            table_file.write(','.join(self.coordinators) + '\n')
            table_file.write(','.join(self.queue) + '\n')
            table_file.write(self.status.name + '\n')
            if self.status == TableStatus.CORRECTING:
                table_file.write(str(self.current_coordination_start_time) + '\n')
                table_file.write(self.current_coordination_team + '\n')

    # Adds a team to the queue in the given position (default is last).
    # If the team is already in the queue nothing is done and False is returned.
    # Otherwise True is returned.
    def add_to_queue(self, team, pos=-1):
        if team not in self.queue:
            if pos == -1: pos = len(self.queue)
            self.queue.insert(pos, team)
            return True
        else: return False

    # Removes the team from the queue.
    # Returns whether the team was in the queue.
    def remove_from_queue(self, team):
        if team in self.queue:
            self.queue.remove(team)
            return True
        else: return False

    # Starts a coordination with team.
    # Returns whether the coordination started successfully.
    def start_coordination(self, team):
        if self.status == TableStatus.CORRECTING: return False
        self.status = TablesStatus.CORRECTING
        self.current_coordination_team = team
        self.current_coordination_start_time = int(time.time())
        return True

    # Finish the current coordination and saves it in the history.
    # Updates the values of expected_duration and number_made_corrections.
    # Returns whether the coordination was successfully finished.
    def finish_coordination(self):
        if self.status != TableStatus.CORRECTING: return False
        time_now = int(time.time())
        self.history_manager.add(self.current_coordination_team, self.name,
                                 self.current_coordination_time,
                                 time_now)
        self.expected_duration *= max(number_made_corrections, NUM_SIGN_CORR)
        self.expected_duration += time_now - self.current_coordination_time
        number_made_corrections += 1
        self.expected_duration /= max(number_made_corrections, NUM_SIGN_CORR)
        self.status = TableStatus.NOTHING
        return True

    # Switch the status to calling.
    # Returns whether the status was succesfully changed to CALLING.
    def switch_to_calling(self):
        if self.status != TableStatus.NOTHING: return False
        self.status = TableStatus.CALLING
        return True

    # Returns the numbers of done corrections.
    def get_number_made_corrections(self):
        table_corrections = self.history_manager.get_corrections({'table': self.name})
        return len(table_corrections)

    # Compute the expected duration of the next correction of the table.
    # It is computed taking the arithmetic mean of the durations of the made
    # corrections.
    # If less than NUM_SIGN_CORR corrections have been done in the table,
    # it pretends there exist corrections with duration APRIORI_DURATION.
    def get_expected_duration(self):
        table_corrections = self.history_manager.get_corrections({'table': self.name})
        sorted(table_corrections, key = attrgetter('start_time'), reverse = True)
        expected_duration = 0
        for i in range(0, len(table_corrections)):
            expected_duration += table_coordinations[i].duration()
        expected_duration += max(NUM_SIGN_CORR - len(table_coordinations), 0) * APRIORI_DURATION;
        expected_duration /= max(NUM_SIGN_CORR, len(table_corrections);
        return expected_duration
        
