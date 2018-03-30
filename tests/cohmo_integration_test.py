import os
import cohmo
import unittest
import tempfile
from unittest import mock
from unittest.mock import *
import time

from cohmo.table import Table, TableStatus
from cohmo.history import HistoryManager

def generate_tempfile(content_rows):
    with tempfile.NamedTemporaryFile(delete=False) as t_file:
        t_file.write(('\n'.join(content_rows)).encode())
        return t_file.name

class CohmoTestCase(unittest.TestCase):
    def setUp(self):
        cohmo.app.config['TEAMS_FILE_PATH'] = generate_tempfile(['FRA,ITA,ENG,USA,CHN,IND,KOR'])
        cohmo.app.config['HISTORY_FILE_PATH'] = generate_tempfile(['USA,T2,5,10,ID1', 'ENG,T5,8,12,ID2', 'CHN,T5,13,17,ID3'])
        cohmo.app.config['TABLE_FILE_PATHS'] = {
            'T2': generate_tempfile(['T2', '3', 'Franco Anselmi, Antonio Cannavaro', 'ITA, ENG, IND', 'IDLE']),
            'T5': generate_tempfile(['T5', '6', 'Alessandro Maschi, Giovanni Muciaccia', 'IND, KOR, ENG, USA', 'CALLING']),
            'T8': generate_tempfile(['T8', '1', 'Marco Faschi, Giorgio Gigi', 'KOR, ENG, FRA', 'CORRECTING', 'USA', '10']),
        }
        cohmo.app.testing = True
        self.client = cohmo.app.test_client()

    def tearDown(self):
        os.unlink(cohmo.app.config['TEAMS_FILE_PATH'])
        os.unlink(cohmo.app.config['HISTORY_FILE_PATH'])
        for table in cohmo.app.config['TABLE_FILE_PATHS']:
            os.unlink(cohmo.app.config['TABLE_FILE_PATHS'][table])

    def test_chief_initialization(self):
        cohmo.init_chief()
        self.assertTrue('T2' in cohmo.chief.tables and 'T5' in cohmo.chief.tables and 'T8' in cohmo.chief.tables)
        self.assertEqual(cohmo.chief.teams, ['FRA', 'ITA', 'ENG', 'USA', 'CHN', 'IND', 'KOR'])
        self.assertEqual(cohmo.chief.tables['T2'].status, TableStatus.IDLE)
        self.assertEqual(cohmo.chief.tables['T5'].status, TableStatus.CALLING)
        self.assertEqual(cohmo.chief.tables['T8'].status, TableStatus.CORRECTING)
        self.assertEqual(cohmo.chief.tables['T8'].current_coordination_team, 'USA')
        self.assertEqual(cohmo.chief.tables['T8'].current_coordination_start_time,
                         10)
        self.assertEqual(len(cohmo.chief.history_manager.corrections), 3)

    def test_history(self):
        history = HistoryManager(cohmo.app.config['HISTORY_FILE_PATH'])
        self.assertTrue(history.add('ITA', 'T2', 10, 20))
        self.assertTrue(history.add('FRA', 'T8', 20, 30))
        self.assertTrue(history.add('KOR', 'T5', 15, 30))
        self.assertFalse(history.delete('ID_NOT_EXISTENT'))
        self.assertEqual(len(history.get_corrections({'identifier':'ID2'})), 1)
        self.assertTrue(history.delete('ID2'))
        self.assertEqual(history.get_corrections({'identifier':'ID2'}), [])
        self.assertEqual(len(history.corrections), 5)
        history.dump_to_file()

        # Constructing HistoryManager from the file written by dump_to_file.
        history = HistoryManager(cohmo.app.config['HISTORY_FILE_PATH'])
        self.assertEqual(len(history.corrections), 5)
        self.assertEqual(history.corrections[2].table, 'T2')
        self.assertEqual(history.corrections[2].team, 'ITA')
        self.assertTrue(history.add('ITA', 'T5', 20, 30))

        # Testing various calls to get_corrections.
        self.assertEqual(history.get_corrections({'table':'NOWAY'}), [])
        self.assertEqual(len(history.get_corrections({'table':'T5'})), 3)
        self.assertEqual(history.get_corrections({'identifier':'ID2'}), [])
        self.assertEqual(len(history.get_corrections({'table':'T2'})), 2)
        self.assertEqual(len(history.get_corrections({'table':'T8'})), 1)
        self.assertEqual(len(history.get_corrections({'table':'T5', 'team':'KOR'})), 1)
        self.assertEqual(history.get_corrections({'table':'T5', 'team':'ROK'}), [])
        self.assertEqual(len(history.get_corrections({'start_time':(-100,100)})), 6)
        self.assertEqual(len(history.get_corrections({'end_time':(15,25)})), 2)

    def test_table(self):
        history = HistoryManager(cohmo.app.config['HISTORY_FILE_PATH'])
        table = Table(cohmo.app.config['TABLE_FILE_PATHS']['T2'], history)
        self.assertEqual(table.queue, ['ITA', 'ENG', 'IND'])
        self.assertEqual(table.status, TableStatus.IDLE)
        self.assertTrue(table.switch_to_calling())
        self.assertEqual(table.status, TableStatus.CALLING)
        self.assertTrue(table.switch_to_idle())
        self.assertFalse(table.switch_to_idle())
        self.assertEqual(table.status, TableStatus.IDLE)
        self.assertTrue(table.start_coordination('IND'))
        self.assertEqual(table.status, TableStatus.CORRECTING)
        self.assertEqual(table.current_coordination_team, 'IND')
        self.assertGreater(table.current_coordination_start_time, 100)
        table.dump_to_file()
        self.assertTrue(table.remove_from_queue('ENG'))
        self.assertFalse(table.remove_from_queue('KOR'))
        self.assertEqual(table.queue, ['ITA', 'IND'])
        table.dump_to_file()

        # Constructing Table from the file written by dump_to_file.
        table = Table(cohmo.app.config['TABLE_FILE_PATHS']['T2'], history)
        self.assertEqual(table.queue, ['ITA', 'IND'])
        self.assertEqual(table.status, TableStatus.CORRECTING)
        self.assertEqual(table.current_coordination_team, 'IND')
        self.assertFalse(table.switch_to_calling())
        self.assertFalse(table.switch_to_idle())
        self.assertFalse(table.start_coordination('ITA'))
        self.assertEqual(len(history.get_corrections({'table':'T2', 'team':'IND'})), 0)
        self.assertTrue(table.finish_coordination())
        self.assertEqual(table.status, TableStatus.IDLE)
        self.assertEqual(len(history.get_corrections({'table':'T2', 'team':'IND'})), 1)

        # Testing the queue modifying APIs.
        self.assertTrue(table.add_to_queue('ENG'))
        self.assertFalse(table.add_to_queue('ITA'))
        self.assertTrue(table.add_to_queue('KOR', 0))
        self.assertTrue(table.add_to_queue('CHN', 2))
        self.assertEqual(table.queue, ['KOR', 'ITA', 'CHN', 'IND', 'ENG'])
        self.assertFalse(table.remove_from_queue('FRA'))
        self.assertTrue(table.remove_from_queue('ITA'))
        self.assertFalse(table.remove_from_queue('ITA'))
        self.assertFalse(table.swap_teams_in_queue('CHN', 'CHN'))
        self.assertFalse(table.swap_teams_in_queue('FRA', 'KOR'))
        self.assertTrue(table.swap_teams_in_queue('IND', 'KOR'))
        self.assertEqual(table.queue, ['IND', 'CHN', 'KOR', 'ENG'])


    mock_time = Mock()
    mock_time.side_effect = [3, 10, 5, 21]
    @patch('time.time', mock_time) 
    def test_get_expected_duration(self):
        cohmo.app.config['NUM_SIGN_CORR'] = 2
        cohmo.app.config['APRIORI_DURATION'] = 3
        history = HistoryManager(cohmo.app.config['HISTORY_FILE_PATH'])
        table = Table(cohmo.app.config['TABLE_FILE_PATHS']['T2'], history)
        self.assertEqual(history.corrections[0].duration(), 5)
        self.assertEqual(len(history.get_corrections({'table':'T2'})), 1)
        self.assertEqual(table.get_expected_duration(), 4)
        self.assertTrue(table.start_coordination('ITA'))
        self.assertEqual(table.get_expected_duration(), 4)
        self.assertTrue(table.finish_coordination())
        self.assertEqual(table.get_expected_duration(), 6)
        self.assertTrue(table.start_coordination('ENG'))
        self.assertTrue(table.finish_coordination())
        self.assertEqual(table.get_expected_duration(), 28/3)


if __name__ == '__main__':
    unittest.main()
