from table import Table
from history import HistoryManager

# This class is the global handler of both the tables and the history.
# The name of the class is inspired from the real-world name of the person
# that is in charge of organizing and overseeing all the
# coordination-related tasks.
class ChiefCoordinator:
    def __init__(self, teams, tables):
        self.teams = teams
        self.tables = {}
        self.history_manager = HistoryManager()
        for table in tables:
            self.tables[table['name']] = Table(table['name'],
                                               table['problem'],
                                               table['coordinators'],
                                               self.history_manager)

#  chief = ChiefCoordinator(['ITA', 'FRA', 'SWE'],
    #  [{'name': 'A1', 'problem': '1', 'coordinators': ['Fede', 'Giada']}])
#  chief.tables['A1'].add_to_queue('ITA')
#  print(chief.tables['A1'].get_queue())
