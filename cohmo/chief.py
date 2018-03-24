from cohmo.table import Table, create_table_from_file, dump_table_to_file
from cohmo.history import HistoryManager

# This class is the global handler of both the tables and the history.
# The name of the class is inspired from the real-world name of the person
# that is in charge of organizing and overseeing all the
# coordination-related tasks.
# It is constructed directly reading information from files.
# teams_path and history_path are paths, whereas table_paths is a dictionary
# of the form: table_name: table_path.
class ChiefCoordinator:
    def __init__(self, teams_path, table_paths, history_path):
        self.teams_path = teams_path
        self.table_paths = table_paths
        self.history_path = history_path

        with open(teams_path, newline='') as teams_file:
            lines = teams_file.readlines()
            assert(len(lines) >= 1)
            self.teams = [team.strip() for team in lines[0].split(',')]
        self.history_manager = HistoryManager()
        self.history_manager.load_from_file(history_path)

        self.tables = {}
        for name in table_paths:
            self.tables[name] = create_table_from_file(
                table_paths[name], self.history_manager)

    # Saves the current states of tables and history to the given files.
    # The default files are the ones passed to the constructor.
    def dump_to_file(self, table_paths=None, history_path=None):
        if table_paths is None: table_paths = self.table_paths
        if history_path is None: history_path = self.history_path
        self.history_manager.dump_to_file(history_path)
        for name in table_paths:
            dump_table_to_file(self.tables[name], table_paths[name])

#  chief = ChiefCoordinator('../test_data/teams.txt',
    #  {'T1':'../test_data/T1.txt', 'T8': '../test_data/T8.txt'},
    #  '../test_data/history.txt')
#  chief.tables['T1'].add_to_queue('ITA')
#  print(chief.tables['T1'].queue)
