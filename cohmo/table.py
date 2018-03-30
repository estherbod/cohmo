from cohmo.history import Correction, HistoryManager
import enum
import time

class TableStatus(enum.IntEnum):
    CALLING = 0
    CORRECTING = 1
    IDLE = 2

# The coordination Table is the class that handles the queue of teams to
# be corrected from a single table.
#
# Its main properties are: table name, problem, coordinators. This properties
# should never change after the creation of the instance. A table is uniquely
# identified by its name.
#
# The internal state of a table is given by the queue (of teams to coordinate
# with) and by its status. The status can be one of: calling, correcting,
# idle. Idle means that the table is not correcting nor it is ready
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
            self.name = lines[0].strip()
            self.problem = lines[1].strip()
            self.coordinators = [coordinator.strip() for coordinator in lines[2].split(',')]
            self.history_manager = history_manager
            self.queue = [team.strip() for team in lines[3].split(',')]
            status_name = lines[4].strip()
            self.status = TableStatus[status_name]
            if self.status == TableStatus.CORRECTING:
                assert(len(lines) >= 7)
                self.current_coordination_team = lines[5].strip()
                self.current_coordination_start_time = int(lines[6].strip())
            else:
                self.current_coordination_start_time = None
                self.current_coordination_team = None

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
                table_file.write(self.current_coordination_team + '\n')
                table_file.write(str(self.current_coordination_start_time) + '\n')

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

    def swap_teams_in_queue(self, team1, team2):
        if team1 not in self.queue or team2 not in self.queue or team1 == team2:
            return False
        pos1 = self.queue.index(team1)
        pos2 = self.queue.index(team2)
        self.queue[pos1], self.queue[pos2] = team2, team1
        return True

    # Starts a coordination with team.
    # Returns whether the coordination started successfully.
    def start_coordination(self, team):
        if self.status == TableStatus.CORRECTING: return False
        self.status = TableStatus.CORRECTING
        self.current_coordination_team = team
        self.current_coordination_start_time = int(time.time())
        return True

    # Finish the current coordination and saves it in the history.
    # Moreover it recomputes the expected_duration of the table.
    # Returns whether the coordination was successfully finished.
    def finish_coordination(self):
        if self.status != TableStatus.CORRECTING: return False
        if not self.history_manager.add(self.current_coordination_team, self.name,
                                        self.current_coordination_start_time,
                                        int(time.time())): return False
        self.status = TableStatus.IDLE
        self.history_manager.compute_expected_duration(self.name)
        return True

    # Switch the status to calling.
    # Returns whether the status was succesfully changed.
    def switch_to_calling(self):
        if self.status != TableStatus.IDLE: return False
        self.status = TableStatus.CALLING
        return True

    # Switch the status to IDLE.
    # Returns whether the status was succesfully changed.
    def switch_to_idle(self):
        if self.status != TableStatus.CALLING: return False
        self.status = TableStatus.IDLE
        return True
        
