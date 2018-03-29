from flask import Flask

app = Flask(__name__, instance_relative_config = True)
app.config.from_object('config')
app.config.from_pyfile('config.py')

from cohmo.chief import ChiefCoordinator
chief = None

def init_chief():
    global chief
    chief = ChiefCoordinator(app.config['TEAMS_FILE_PATH'],
                             app.config['TABLE_FILE_PATHS'],
                             app.config['HISTORY_FILE_PATH'])

@app.cli.command('initchief')
def init_chief_command():
    init_chief()
    print('Initialized the chief coordinator object.')


import cohmo.views
