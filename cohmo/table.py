from cohmo.history import Correction, HistoryManager
import enum

class TableStatus(enum.Enum):
    CALLING = 'calling'
    CORRECTING = 'correcting'
    NOTHING = 'nothing'

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
    def __init__(self, name, problem, coordinators, history_manager):
        assert(isinstance(name, str))
        assert(isinstance(problem, str))
        assert(1 <= len(name) <= 10)
        assert(1 <= len(problem) <= 10)
        self.name = name
        self.problem = problem
        self.coordinators = coordinators
        self.history_manager = history_manager # Dependency injection
        self.queue = []
        self.status = TableStatus.NOTHING
        self.current_coordination_start_time = None # Timestamp in seconds
        self.current_coordination_team = None

    # Adds a team to the queue in the given position (default is last).
    # If the team is already in the queue nothing is done and False is returned.
    # Otherwise True is returned.
    def add_to_queue(self, team, pos=-1):
        if team not in self.queue:
            if pos == -1: pos = len(self.queue)
            self.queue.insert(len(self.queue), team)
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
    # Returns whether the coordination was successfully finished.
    def finish_coordination(self):
        if self.status != TableStatus.CORRECTING: return False
        self.history_manager.add(self.current_coordination_team, self.name,
                                 self.current_coordination_time,
                                 int(time.time()))
        self.status = TableStatus.NOTHING
        return True

    # Switch the status to calling.
    # Returns whether the status was succesfully changed to CALLING.
    def switch_to_calling(self):
        if self.status != TableStatus.NOTHING: return False
        self.status = TableStatus.CALLING
        return True

# ACHTUNG: Why I am not saving everything to file?

# Returns a table created from the given file (with history_manager injected).
# The format for the file is the following one:
# table name
# problem name
# coordinators (separated by commas)
# queue of teams (separated by commas)
def create_table_from_file(path, history_manager):
    with open(path, newline='') as table_file:
        lines = table_file.readlines()
        assert(len(lines) >= 4)
        name = lines[0]
        problem = lines[1]
        coordinators = [coordinator.strip() for coordinator in lines[2].split(',')]
        queue = [team.strip() for team in lines[3].split(',')]
        table = Table(name, problem, coordinators, history_manager)
        for team in queue:
            table.add_to_queue(team)
        return table

# Dumps the table to file. The format is the same as create_table_from_file.
# It should be remarked that the current status of the table (whether it is
# currently correcting is lost when doing this operation).
def dump_table_to_file(table, path):
    with open(path, 'w', newline='') as table_file:
        table_file.write(table.name + '\n')
        table_file.write(table.problem + '\n')
        table_file.write(','.join(table.coordinators) + '\n')
        table_file.write(','.join(table.queue) + '\n')
