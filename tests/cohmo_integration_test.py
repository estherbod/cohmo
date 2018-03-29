import os
import cohmo
import unittest
import tempfile

def generate_tempfile(content_rows):
    with tempfile.NamedTemporaryFile(delete=False) as t_file:
        t_file.write(('\n'.join(content_rows)).encode())
        return t_file.name

class CohmoTestCase(unittest.TestCase):
    def setUp(self):
        cohmo.app.config['TEAMS_FILE_PATH'] = generate_tempfile(['FRA,ITA,ENG,USA,CHN,IND,KOR'])
        cohmo.app.config['HISTORY_FILE_PATH'] = generate_tempfile([])
        cohmo.app.config['TABLE_FILE_PATHS'] = {
            'T2': generate_tempfile(['T2', '3', 'Franco Anselmi, Antonio Cannavaro', 'ITA, ENG, IND', 'NOTHING']),
            'T5': generate_tempfile(['T5', '6', 'Alessandro Maschi, Giovanni Muciaccia', 'IND, KOR, ENG, USA', 'CALLING'])
        }
        cohmo.app.testing = True
        self.client = cohmo.app.test_client()
        cohmo.init_chief()

    def tearDown(self):
        os.unlink(cohmo.app.config['TEAMS_FILE_PATH'])
        os.unlink(cohmo.app.config['HISTORY_FILE_PATH'])
        for table in cohmo.app.config['TABLE_FILE_PATHS']:
            os.unlink(cohmo.app.config['TABLE_FILE_PATHS'][table])

    def test_empty(self):
        self.assertTrue('T2' in cohmo.chief.tables and 'T5' in cohmo.chief.tables)

if __name__ == '__main__':
    unittest.main()
