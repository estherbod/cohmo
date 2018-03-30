from flask import Flask

app = Flask(__name__, instance_relative_config = True)
app.config.from_object('config')
app.config.from_pyfile('config.py')

from cohmo.chief import ChiefCoordinator

def get_chief():
    return ChiefCoordinator(app.config['TEAMS_FILE_PATH'],
                            app.config['TABLE_FILE_PATHS'],
                            app.config['HISTORY_FILE_PATH'],
                            app.config)


import cohmo.views
