import os
import cohmo
from cohmo import app
import unittest
import tempfile
# ~ from unittest import mock
from unittest.mock import *
import time
from flask import json, jsonify

from cohmo.table import Table, TableStatus
from cohmo.history import HistoryManager
from cohmo.views import init_chief

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
        #  self.client = cohmo.app.test_client()

    def tearDown(self):
        os.unlink(cohmo.app.config['TEAMS_FILE_PATH'])
        os.unlink(cohmo.app.config['HISTORY_FILE_PATH'])
        for table in cohmo.app.config['TABLE_FILE_PATHS']:
            os.unlink(cohmo.app.config['TABLE_FILE_PATHS'][table])

    def test_chief_initialization(self):
        chief = cohmo.get_chief()
        self.assertTrue('T2' in chief.tables and 'T5' in chief.tables and 'T8' in chief.tables)
        self.assertEqual(chief.teams, ['FRA', 'ITA', 'ENG', 'USA', 'CHN', 'IND', 'KOR'])
        self.assertEqual(chief.tables['T2'].status, TableStatus.IDLE)
        self.assertEqual(chief.tables['T5'].status, TableStatus.CALLING)
        self.assertEqual(chief.tables['T8'].status, TableStatus.CORRECTING)
        self.assertEqual(chief.tables['T8'].current_coordination_team, 'USA')
        self.assertEqual(chief.tables['T8'].current_coordination_start_time,
                         10)
        self.assertEqual(len(chief.history_manager.corrections), 3)

    def test_history(self):
        history = HistoryManager(cohmo.app.config['HISTORY_FILE_PATH'], app.config)
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
        history = HistoryManager(cohmo.app.config['HISTORY_FILE_PATH'], app.config)
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
        history = HistoryManager(cohmo.app.config['HISTORY_FILE_PATH'], app.config)
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
        self.assertTrue(table.swap_teams_in_queue('KOR', 'IND'))
        self.assertEqual(table.queue, ['IND', 'CHN', 'KOR', 'ENG'])


    # Testing get_expected_duration.
    mock_time = Mock()
    mock_time.side_effect = [3, 10, 5, 21]
    @patch('time.time', mock_time) 
    def test_get_expected_duration(self):
        cohmo.app.config['NUM_SIGN_CORR'] = 2
        cohmo.app.config['APRIORI_DURATION'] = 3
        history = HistoryManager(cohmo.app.config['HISTORY_FILE_PATH'], app.config)
        table = Table(cohmo.app.config['TABLE_FILE_PATHS']['T2'], history)
        self.assertEqual(history.corrections[0].duration(), 5)
        self.assertEqual(len(history.get_corrections({'table':'T2'})), 1)
        self.assertAlmostEqual(history.get_expected_duration('T2'), 4)
        self.assertAlmostEqual(history.get_expected_duration('T8'), 3)
        self.assertTrue(table.start_coordination('ITA'))
        self.assertAlmostEqual(history.get_expected_duration('T2'), 4)
        self.assertTrue(table.finish_coordination())
        self.assertAlmostEqual(history.get_expected_duration('T2'), 6)
        self.assertTrue(history.add('ENG', 'T2', 5, 21))
        self.assertAlmostEqual(history.get_expected_duration('T2'), 28/3)
        self.assertTrue(history.delete('ID1'))
        self.assertEqual(len(history.get_corrections({'table':'T2'})), 2)
        self.assertAlmostEqual(history.get_expected_duration('T2'), 23/2)
        self.assertEqual(len(history.get_corrections({'table':'T2', 'team':'ITA'})), 1)
        id_corr_ITA = history.get_corrections({'table':'T2', 'team':'ITA'})[0].id
        self.assertTrue(history.delete(id_corr_ITA))
        self.assertAlmostEqual(history.get_expected_duration('T2'), 19/2)

    def test_views_table_queue_modifications(self):
        cohmo.views.init_chief()
        client = cohmo.app.test_client()

        # Testing add_to_queue.
        resp = json.loads(client.post('/table/T1/add_to_queue',
                                      data=json.dumps({'team': 'ITA'})).data)
        self.assertTrue('ok' in resp and resp['ok'] == False and
                        resp['message'] == 'Table T1 does not exist.')
        resp = json.loads(client.post('/table/T2/add_to_queue',
                                      data=json.dumps({'pippo': 'USA'})).data)
        self.assertTrue('ok' in resp and resp['ok'] == False and
                        resp['message'] == 'You have to specify a team.')
        resp = json.loads(client.post('/table/T2/add_to_queue',
                                      data=json.dumps({'team': 'VAT'})).data)
        self.assertTrue('ok' in resp and resp['ok'] == False and
                        resp['message'] == 'Team VAT does not exist.')
        resp = json.loads(client.post('/table/T2/add_to_queue',
                                      data=json.dumps({'team': 'ENG'})).data)
        self.assertTrue('ok' in resp and resp['ok'] == False and
                        resp['message'] == 'Team ENG is already in queue at table T2.')
        resp = json.loads(client.post('/table/T2/add_to_queue',
                                      data=json.dumps({'team': 'CHN'})).data)
        self.assertTrue('ok' in resp and resp['ok'] == True)        
        resp = json.loads(client.get('/table/T2/get_queue').data)
        self.assertTrue('ok' in resp)
        self.assertEqual(resp['queue'], ['ITA', 'ENG', 'IND', 'CHN'])

        # Testing remove_from_queue.
        resp = json.loads(client.post('/table/T1/remove_from_queue',
                                      data=json.dumps({'team': 'ITA'})).data)
        self.assertTrue('ok' in resp and resp['ok'] == False and
                        resp['message'] == 'Table T1 does not exist.')
        resp = json.loads(client.post('/table/T2/remove_from_queue',
                                      data=json.dumps({'pippo': 'USA'})).data)
        self.assertTrue('ok' in resp and resp['ok'] == False and
                        resp['message'] == 'You have to specify a team.')
        resp = json.loads(client.post('/table/T2/remove_from_queue',
                                      data=json.dumps({'team': 'VAT'})).data)
        self.assertTrue('ok' in resp and resp['ok'] == False and
                        resp['message'] == 'Team VAT does not exist.')
        resp = json.loads(client.post('/table/T2/remove_from_queue',
                                      data=json.dumps({'team': 'KOR'})).data)
        self.assertTrue('ok' in resp and resp['ok'] == False and
                        resp['message'] == 'Team KOR is not in queue at table T2.')
        resp = json.loads(client.post('/table/T2/remove_from_queue',
                                      data=json.dumps({'team': 'CHN'})).data)
        self.assertTrue('ok' in resp and resp['ok'] == True)        
        resp = json.loads(client.get('/table/T2/get_queue').data)
        self.assertTrue('ok' in resp)
        self.assertEqual(resp['queue'], ['ITA', 'ENG', 'IND'])

        # Testing swap_teams_in_queue.
        resp = json.loads(client.post('/table/T1/swap_teams_in_queue',
                                      data=json.dumps({'teams': ['ITA', 'ENG']})).data)
        self.assertTrue('ok' in resp and resp['ok'] == False and
                        resp['message'] == 'Table T1 does not exist.')
        resp = json.loads(client.post('/table/T2/swap_teams_in_queue',
                                      data=json.dumps({'pippo': ['USA']})).data)
        self.assertTrue('ok' in resp and resp['ok'] == False and
                        resp['message'] == 'You have to specify the teams to be swapped.')
        resp = json.loads(client.post('/table/T2/swap_teams_in_queue',
                                      data=json.dumps({'teams': ['VAT']})).data)
        self.assertTrue('ok' in resp and resp['ok'] == False and
                        resp['message'] == 'You have to give exactly two teams to be swapped.')
        resp = json.loads(client.post('/table/T2/swap_teams_in_queue',
                                      data=json.dumps({'teams': ['VAT', 'ENG']})).data)
        self.assertTrue('ok' in resp and resp['ok'] == False and
                        resp['message'] == 'Team VAT does not exist.')
        resp = json.loads(client.post('/table/T2/swap_teams_in_queue',
                                      data=json.dumps({'teams': ['ITA', 'KOR']})).data)
        self.assertTrue('ok' in resp and resp['ok'] == False and
                        resp['message'] == 'Team KOR is not in queue at table T2.')
        resp = json.loads(client.post('/table/T2/swap_teams_in_queue',
                                      data=json.dumps({'teams': ['ENG', 'ITA']})).data)
        self.assertTrue('ok' in resp and resp['ok'] == True)        
        resp = json.loads(client.get('/table/T2/get_queue').data)
        self.assertTrue('ok' in resp)
        self.assertEqual(resp['queue'], ['ENG', 'ITA', 'IND'])

    def test_views_table_coordination_management(self):
        cohmo.views.init_chief()
        client = cohmo.app.test_client()

        # Testing start_coordination.
        resp = json.loads(client.post('/table/T1/start_coordination',
                                      data=json.dumps({'team': 'ITA'})).data)
        self.assertTrue('ok' in resp and resp['ok'] == False and
                        resp['message'] == 'Table T1 does not exist.')
        resp = json.loads(client.post('/table/T2/start_coordination',
                                      data=json.dumps({'pippo': 'USA'})).data)
        self.assertTrue('ok' in resp and resp['ok'] == False and
                        resp['message'] == 'You have to specify a team.')
        resp = json.loads(client.post('/table/T2/start_coordination',
                                      data=json.dumps({'team': 'VAT'})).data)
        self.assertTrue('ok' in resp and resp['ok'] == False and
                        resp['message'] == 'Team VAT does not exist.')
        resp = json.loads(client.post('/table/T2/start_coordination',
                                      data=json.dumps({'team': 'KOR'})).data)
        self.assertTrue('ok' in resp and resp['ok'] == False and
                        resp['message'] == 'Team KOR is not in queue at table T2.')
        resp = json.loads(client.post('/table/T2/start_coordination',
                                      data=json.dumps({'team': 'ITA'})).data)
        self.assertTrue('ok' in resp and resp['ok'] == True)
        resp = json.loads(client.get('/table/T2/get_queue').data)
        self.assertTrue('ok' in resp)
        self.assertEqual(resp['queue'], ['ENG', 'IND'])
        resp = json.loads(client.get('/table/T2/get_all').data)
        self.assertTrue('ok' in resp and 'table_data' in resp)
        table_data = json.loads(resp['table_data'])
        self.assertEqual(table_data['status'], 1)

        # Testing finish_coordination.
        resp = json.loads(client.post('/table/T1/finish_coordination').data)
        self.assertTrue('ok' in resp and resp['ok'] == False and
                        resp['message'] == 'Table T1 does not exist.')
        resp = json.loads(client.post('/table/T2/finish_coordination').data)
        self.assertTrue('ok' in resp and resp['ok'] == True)
        resp = json.loads(client.get('/table/T2/get_queue').data)
        self.assertTrue('ok' in resp)
        self.assertEqual(resp['queue'], ['ENG', 'IND'])
        resp = json.loads(client.get('/table/T2/get_all').data)
        self.assertTrue('ok' in resp and 'table_data' in resp)
        table_data = json.loads(resp['table_data'])
        self.assertEqual(table_data['status'], 2)
        resp = json.loads(client.post('/table/T2/finish_coordination').data)
        self.assertTrue('ok' in resp and resp['ok'] == False)

        # Testing pause_coordination.
        resp = json.loads(client.post('/table/T2/start_coordination',
                                      data=json.dumps({'team': 'ENG'})).data)
        self.assertTrue('ok' in resp and resp['ok'] == True)
        resp = json.loads(client.get('/table/T2/get_queue').data)
        self.assertTrue('ok' in resp)
        self.assertEqual(resp['queue'], ['IND'])
        resp = json.loads(client.post('/table/T1/pause_coordination').data)
        self.assertTrue('ok' in resp and resp['ok'] == False and
                        resp['message'] == 'Table T1 does not exist.')
        resp = json.loads(client.post('/table/T2/pause_coordination').data)
        self.assertTrue('ok' in resp and resp['ok'] == True)
        resp = json.loads(client.get('/table/T2/get_queue').data)
        self.assertTrue('ok' in resp)
        self.assertEqual(resp['queue'], ['IND', 'ENG'])

        # Testing switch_to_calling.
        resp = json.loads(client.post('/table/T1/switch_to_calling',
                                      data=json.dumps({'team': 'ITA'})).data)
        self.assertTrue('ok' in resp and resp['ok'] == False and
                        resp['message'] == 'Table T1 does not exist.')
        resp = json.loads(client.post('/table/T2/switch_to_calling').data)
        self.assertTrue('ok' in resp and resp['ok'] == True)
        resp = json.loads(client.get('/table/T2/get_all').data)
        self.assertTrue('ok' in resp and 'table_data' in resp)
        table_data = json.loads(resp['table_data'])
        self.assertEqual(table_data['status'], 0)

        # Testing switch_to_idle.
        resp = json.loads(client.post('/table/T1/switch_to_idle',
                                      data=json.dumps({'team': 'ITA'})).data)
        self.assertTrue('ok' in resp and resp['ok'] == False and
                        resp['message'] == 'Table T1 does not exist.')
        resp = json.loads(client.post('/table/T2/switch_to_idle').data)
        self.assertTrue('ok' in resp and resp['ok'] == True)
        resp = json.loads(client.get('/table/T2/get_all').data)
        self.assertTrue('ok' in resp and 'table_data' in resp)
        table_data = json.loads(resp['table_data'])
        self.assertEqual(table_data['status'], 2)

    def test_views_table_get(self):
        cohmo.views.init_chief()
        client = cohmo.app.test_client()

        # Testing get_queue.
        resp = json.loads(client.get('/table/T1/get_queue').data)
        self.assertTrue('ok' in resp and resp['ok'] == False and
                        resp['message'] == 'Table T1 does not exist.')
        resp = json.loads(client.get('/table/T2/get_queue').data)
        self.assertTrue('ok' in resp)
        self.assertEqual(resp['queue'], ['ITA', 'ENG', 'IND'])

        # Testing get_all.
        resp = json.loads(client.get('/table/T1/get_all').data)
        self.assertTrue('ok' in resp and resp['ok'] == False and
                        resp['message'] == 'Table T1 does not exist.')
        resp = json.loads(client.get('/table/T2/get_queue').data)
        self.assertTrue('ok' in resp)
        self.assertEqual(resp['queue'], ['ITA', 'ENG', 'IND'])
        resp = json.loads(client.get('/table/T2/get_all').data)
        self.assertTrue('ok' in resp and 'table_data' in resp)
        table_data = json.loads(resp['table_data'])
        self.assertTrue(table_data['name'] == 'T2' and
                        table_data['problem'] == '3' and
                        table_data['coordinators'] == ['Franco Anselmi', 'Antonio Cannavaro'] and
                        table_data['queue'] == ['ITA', 'ENG', 'IND'] and
                        table_data['status'] == 2)

    def test_views_history(self):
        cohmo.app.config['NUM_SIGN_CORR'] = 2
        cohmo.app.config['APRIORI_DURATION'] = 3
        cohmo.views.init_chief()
        client = cohmo.app.test_client()

        # Testing history_add.
        resp = json.loads(client.post('/history/add',
                                      data=json.dumps({'pippo': 'ITA'})).data)
        self.assertTrue('ok' in resp and resp['ok'] == False and
                        resp['message'] == 'You have to specify a team.')
        resp = json.loads(client.post('/history/add',
                                      data=json.dumps({'team': 'ITA'})).data)
        self.assertTrue('ok' in resp and resp['ok'] == False and
                        resp['message'] == 'You have to specify a table.')
        resp = json.loads(client.post('/history/add',
                                      data=json.dumps({'team': 'ITA',
                                                       'table': 'T8'})).data)
        self.assertTrue('ok' in resp and resp['ok'] == False and
                        resp['message'] == 'You have to specify a start time.')
        resp = json.loads(client.post('/history/add',
                                      data=json.dumps({'team': 'ITA',
                                                       'table': 'T8',
                                                       'start_time': 10})).data)
        self.assertTrue('ok' in resp and resp['ok'] == False and
                        resp['message'] == 'You have to specify an end time.')
        resp = json.loads(client.post('/history/add',
                                      data=json.dumps({'team': 'ITA',
                                                       'table': 'T8',
                                                       'start_time': 10,
                                                       'end_time': 25})).data)
        self.assertTrue('ok' in resp and resp['ok'] == True)

        # Testing history_delete.
        resp = json.loads(client.post('/history/delete',
                                      data=json.dumps({'pippo': 'ITA'})).data)
        self.assertTrue('ok' in resp and resp['ok'] == False and
                        resp['message'] == 'You have to specify a correction id.')
        resp = json.loads(client.post('/history/delete',
                                      data=json.dumps({'correction_id': 'ID2'})).data)
        self.assertTrue('ok' in resp and resp['ok'] == True)

        # Testing history_get_corrections.
        resp = json.loads(client.get('/history/get_corrections',
                                     data=json.dumps({'pippo': 'USA'})).data)
        self.assertTrue('ok' in resp and resp['ok'] == False and
                        resp['message'] == 'You have to specify filters.')
        resp = json.loads(client.get('/history/get_corrections',
                                     data=json.dumps({'filters': {'team':'USA'}})).data)
        self.assertTrue('ok' in resp and resp['ok'] == True and
                        'corrections' in resp and len(resp['corrections']) == 1)
        correction = resp['corrections'][0]
        self.assertTrue(correction['team'] == 'USA' and
                        correction['table'] == 'T2' and
                        correction['start_time'] == 5 and
                        correction['end_time'] == 10 and
                        correction['id'] == 'ID1')

        # Testing get_expected_duration.
        resp = json.loads(client.get('/history/get_expected_duration',
                                     data=json.dumps({'pippo': 'T2'})).data)
        self.assertTrue('ok' in resp and resp['ok'] == False and
                        resp['message'] == 'You have to specify a table.')
        resp = json.loads(client.get('/history/get_expected_duration',
                                     data=json.dumps({'table': 'T2'})).data)
        self.assertTrue('ok' in resp and resp['ok'] == True)
        self.assertAlmostEqual(resp['expected_duration'], 4)
        

if __name__ == '__main__':
    unittest.main()
