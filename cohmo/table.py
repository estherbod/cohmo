from cohmo.history import Correction, HistoryManager
import enum
import time
import shutil
import json

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
    # Constructs the table from a json file.
    #
    # The data contained in the file are:
    # table name
    # problem name
    # coordinators
    # queue of teams
    # status (calling, correcting, nothing)
    # current_team (needed only if status == CORRECTING)
    # start_time (needed only if status == CORRECTING) # Timestamp in seconds
    def __init__(self, path, history_manager):
        self.path = path
        with open(path, newline='') as table_file:
            table_as_dict = json.load(table_file)
            self.name = table_as_dict['name']
            self.problem = table_as_dict['problem']
            self.coordinators = table_as_dict['coordinators']
            self.history_manager = history_manager
            self.queue = table_as_dict['queue']
            status_name = table_as_dict['status']
            self.status = TableStatus[status_name]
            if self.status == TableStatus.CORRECTING:
                self.current_coordination_team = \
                    table_as_dict['current_coordination_team']
                self.current_coordination_start_time = \
                    table_as_dict['current_coordination_start_time']
            else:
                self.current_coordination_start_time = None
                self.current_coordination_team = None

    # Dumps the table to file. The format is the same as create_table_from_file.
    # It should be remarked that the current status of the table (whether it is
    # currently correcting is lost when doing this operation).
    def dump_to_file(self, path=None):
        if path is None:
            path = self.path
            # Before modifying the default file a backup is done.
            shutil.copyfile(path, path + '.backup')
        with open(path, 'w', newline='') as table_file:
            table_as_dict = self.to_dict()
            del table_as_dict['expected_duration']
            table_as_dict['status'] = self.status.name

            json.dump(table_as_dict, table_file, indent=4)

    def to_dict(self):
        return {
            'name': self.name,
            'problem': self.problem,
            'coordinators': self.coordinators,
            'queue': self.queue,
            'status': self.status,
            'current_coordination_team': self.current_coordination_team,
            'current_coordination_start_time': self.current_coordination_start_time,
            'expected_duration': self.history_manager.get_expected_duration(self.name),
        }


    # Adds a team to the queue in the given position (default is last).
    # If the team is already in the queue nothing is done and False is returned.
    # Otherwise True is returned.
    def add_to_queue(self, team, pos=-1):
        self.history_manager.operations_num += 1
        if team not in self.queue:
            if pos == -1: pos = len(self.queue)
            self.queue.insert(pos, team)
            self.dump_to_file()
            return True
        else: return False

    # Removes the team from the queue.
    # Returns whether the team was in the queue.
    def remove_from_queue(self, team):
        self.history_manager.operations_num += 1
        if team in self.queue:
            self.queue.remove(team)
            self.dump_to_file()
            return True
        else: return False

    def swap_teams_in_queue(self, team1, team2):
        self.history_manager.operations_num += 1
        if team1 not in self.queue or team2 not in self.queue or team1 == team2:
            return False
        pos1 = self.queue.index(team1)
        pos2 = self.queue.index(team2)
        self.queue[pos1], self.queue[pos2] = team2, team1
        self.dump_to_file()
        return True

    # Starts a coordination with team.
    # Returns whether the coordination started successfully.
    def start_coordination(self, team):
        self.history_manager.operations_num += 1
        if self.status == TableStatus.CORRECTING: return False
        self.status = TableStatus.CORRECTING
        self.current_coordination_team = team
        self.current_coordination_start_time = int(time.time())
        self.dump_to_file()
        return True

    # Finish the current coordination and saves it in the history_manager.
    # Moreover it recomputes the expected_duration of the table.
    # Returns whether the coordination was successfully finished.
    def finish_coordination(self):
        self.history_manager.operations_num += 1
        if self.status != TableStatus.CORRECTING: return False
        if not self.history_manager.add(self.current_coordination_team, self.name,
                                        self.current_coordination_start_time,
                                        int(time.time())): return False
        self.status = TableStatus.IDLE
        self.history_manager.compute_expected_duration(self.name)
        self.dump_to_file()
        return True

    # Switch the status to calling.
    # Returns whether the status was succesfully changed.
    def switch_to_calling(self):
        self.history_manager.operations_num += 1
        if self.status != TableStatus.IDLE: return False
        self.status = TableStatus.CALLING
        self.dump_to_file()
        return True

    # Switch the status to IDLE.
    # Returns whether the status was succesfully changed.
    def switch_to_idle(self):
        self.history_manager.operations_num += 1
        if self.status != TableStatus.CALLING: return False
        self.status = TableStatus.IDLE
        self.dump_to_file()
        return True
        
