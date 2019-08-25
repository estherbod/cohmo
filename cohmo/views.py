from cohmo import app, get_chief
from cohmo.authentication_manager import AuthenticationManager
from flask import Flask, request, json, jsonify, render_template, abort, redirect, url_for
from flask_httpauth import HTTPBasicAuth

auth = HTTPBasicAuth()
authentication_manager = None
def init_authentication_manager():
    global authentication_manager
    authentication_manager = AuthenticationManager(app.config['AUTHENTICATION_FILE_PATH'])

@auth.verify_password
def verify_password(username, password):
    return authentication_manager.verify_password(username, password)

chief = None
def init_chief():
    global chief
    chief = get_chief()

@app.cli.command('initchief')
def init_chief_command():
    init_chief()
    print('Initialized the chief coordinator object.')


TABLE_NOT_EXIST = 'Table {0} does not exist.'
TEAM_NOT_EXIST = 'Team {0} does not exist.'
SPECIFY_TEAM = 'You have to specify a team.'


# Available pages

@app.route('/table/<string:table_name>')
@auth.login_required
def table_admin(table_name):
    table_name = table_name.upper()
    if table_name not in chief.tables:
        abort(404)
    if not authentication_manager.is_authorized(auth.username(), table_name):
        abort(401)
    return render_template('table_admin.html', table_name=table_name)

@app.route('/')
def queues():
    return render_template('queues.html', START_TIME=chief.start_time,
                                          BREAK_TIMES=json.dumps(chief.break_times))

@app.route('/country/<string:country>')
def country_queues(country):
    return render_template('country_queues.html', country=country.upper(),
                           START_TIME=chief.start_time, BREAK_TIMES=json.dumps(chief.break_times))

@app.route('/schedule')
@auth.login_required
def schedule_admin():
    if not authentication_manager.is_admin(auth.username()): abort(401)
    return render_template('schedule_admin.html')

# API relative to a table

@app.route('/table/<string:table_name>/add_to_queue', methods=['POST'])
@auth.login_required
def add_to_queue(table_name):
    if not authentication_manager.is_authorized(auth.username(), table_name): abort(401)
    if table_name not in chief.tables:
        return jsonify(ok=False, message=TABLE_NOT_EXIST.format(table_name))
    req_data = json.loads(request.data)
    if 'team' not in req_data:
        return jsonify(ok=False, message=SPECIFY_TEAM)
    team = req_data['team']
    if team not in chief.teams:
        return jsonify(ok=False, message=TEAM_NOT_EXIST.format(team))
    if team in chief.tables[table_name].queue:
        return jsonify(ok=False,
                       message='Team {0} is already in queue at table {1}.'.format(team, table_name))
    if 'pos' in req_data and req_data['pos']:
        try: 
            pos = int(req_data['pos']);
            if 0 <= pos <= len(chief.tables[table_name].queue):
                if chief.tables[table_name].add_to_queue(team, pos):
                    return jsonify(ok = True)
        except ValueError:
            return jsonify(ok=False, message='The position variable must be an integer.')
    if chief.tables[table_name].add_to_queue(team):
        return jsonify(ok=True)
    return jsonify(ok=False, message='An error occurred while adding the team in the queue.')

@app.route('/table/<string:table_name>/remove_from_queue', methods=['POST'])
@auth.login_required
def remove_from_queue(table_name):
    if not authentication_manager.is_authorized(auth.username(), table_name): abort(401)
    if table_name not in chief.tables:
        return jsonify(ok=False, message=TABLE_NOT_EXIST.format(table_name))
    req_data = json.loads(request.data)
    if 'team' not in req_data:
        return jsonify(ok=False, message=SPECIFY_TEAM)
    team = req_data['team']
    if team not in chief.teams:
        return jsonify(ok=False, message=TEAM_NOT_EXIST.format(team))
    if team not in chief.tables[table_name].queue:
        return jsonify(ok=False,
                       message='Team {0} is not in queue at table {1}.'.format(team, table_name))
    if chief.tables[table_name].remove_from_queue(team):
        return jsonify(ok=True)
    return jsonify(ok=False, message='An error occurred while deleting the team from the queue.')

@app.route('/table/<string:table_name>/swap_teams_in_queue', methods=['POST'])
@auth.login_required
def swap_teams_in_queue(table_name):
    if not authentication_manager.is_authorized(auth.username(), table_name): abort(401)
    if table_name not in chief.tables:
        return jsonify(ok=False, message=TABLE_NOT_EXIST.format(table_name))
    req_data = json.loads(request.data)
    if 'teams' not in req_data:
        return jsonify(ok=False,
                       message='You have to specify the teams to be swapped.')
    teams = req_data['teams']
    if len(teams) != 2:
        return jsonify(ok=False,
                       message='You have to give exactly two teams to be swapped.')
    for team in teams:
        if team not in chief.teams:
            return jsonify(ok=False, message=TEAM_NOT_EXIST.format(team))
        if team not in chief.tables[table_name].queue:
            return jsonify(ok=False,
                           message='Team {0} is not in queue at table {1}.'.format(team, table_name))
    if chief.tables[table_name].swap_teams_in_queue(teams[0], teams[1]):
        return jsonify(ok=True)
    return jsonify(ok=False, message='An error occurred while swapping the teams in the queue.')

@app.route('/table/<string:table_name>/start_coordination', methods=['POST'])
@auth.login_required
def start_coordination(table_name):
    if not authentication_manager.is_authorized(auth.username(), table_name): abort(401)
    if table_name not in chief.tables:
        return jsonify(ok=False, message=TABLE_NOT_EXIST.format(table_name))
    req_data = json.loads(request.data)
    if 'team' not in req_data:
        return jsonify(ok=False, message=SPECIFY_TEAM)
    team = req_data['team']
    if team not in chief.teams:
        return jsonify(ok=False, message=TEAM_NOT_EXIST.format(team))
    if team not in chief.tables[table_name].queue:
        return jsonify(ok=False,
                       message='Team {0} is not in queue at table {1}.'.format(team, table_name))
    if chief.tables[table_name].start_coordination(team):
        if chief.tables[table_name].remove_from_queue(team):
            return jsonify(ok=True)
        return jsonify(ok=False, message='An error occurred removing the team from the queue.')
    return jsonify(ok=False, message='An error occurred while deleting the team from the queue.')

@app.route('/table/<string:table_name>/finish_coordination', methods=['POST'])
@auth.login_required
def finish_coordination(table_name):
    if not authentication_manager.is_authorized(auth.username(), table_name): abort(401)
    if table_name not in chief.tables:
        return jsonify(ok=False, message=TABLE_NOT_EXIST.format(table_name))
    if chief.tables[table_name].finish_coordination():
        return jsonify(ok=True)
    return jsonify(ok=False, message='An error occurred while finishing the coordination.')

@app.route('/table/<string:table_name>/pause_coordination', methods=['POST'])
@auth.login_required
def pause_coordination(table_name):
    if not authentication_manager.is_authorized(auth.username(), table_name): abort(401)
    if table_name not in chief.tables:
        return jsonify(ok=False, message=TABLE_NOT_EXIST.format(table_name))
    table = chief.tables[table_name]
    team = table.current_coordination_team
    if team not in chief.teams:
        return jsonify(ok=False, message=TEAM_NOT_EXIST.format(team))
    if table.finish_coordination(): # If only this is true there is a problem.
        if table.add_to_queue(team):
            return jsonify(ok=True);
        return jsonify(ok=False, message='The coordination has been paused, but there was an issue inserting the team again in the queue.')
    return jsonify(ok=False, message='There was an issue finishing the coordination.')

@app.route('/table/<string:table_name>/switch_to_calling', methods=['POST'])
@auth.login_required
def switch_to_calling(table_name):
    if not authentication_manager.is_authorized(auth.username(), table_name): abort(401)
    if table_name not in chief.tables:
        return jsonify(ok=False, message=TABLE_NOT_EXIST.format(table_name))
    if chief.tables[table_name].switch_to_calling():
        return jsonify(ok=True)
    return jsonify(ok=False, message='An error occured while switching the status to calling.')

@app.route('/table/<string:table_name>/call_team', methods=['POST'])
@auth.login_required
def call_team(table_name):
    if not authentication_manager.is_authorized(auth.username(), table_name): abort(401)
    if table_name not in chief.tables:
        return jsonify(ok=False, message=TABLE_NOT_EXIST.format(table_name))
    table = chief.tables[table_name]
    req_data = json.loads(request.data)
    if 'team' not in req_data:
        return jsonify(ok=False, message=SPECIFY_TEAM)
    team = req_data['team']
    if team not in chief.teams:
        return jsonify(ok=False, message=TEAM_NOT_EXIST.format(team))
    if team in table.queue:
        if not table.remove_from_queue(team):
            return jsonify(ok=False, message='There was an error removing the team from the queue.')
    if not table.add_to_queue(team, 0):
        return jsonify(ok=False, message='An error occurred placing the team first in the queue.')
    if table.status != 0:
        if not table.switch_to_calling():
            return jsonify(ok=False, message='An error occurred while switching the status to calling.')
    return jsonify(ok=True)

@app.route('/table/<string:table_name>/skip_to_next', methods=['POST'])
@auth.login_required
def skip_to_next(table_name):
    if not authentication_manager.is_authorized(auth.username(), table_name): abort(401)
    if table_name not in chief.tables:
        return jsonify(ok=False, message=TABLE_NOT_EXIST.format(table_name))
    table = chief.tables[table_name]
    if table.status != 0:
        return jsonify(ok=False,
                       message='You can not skip to call the next team if you are not calling.')
    if len(table.queue) == 0:
        return jsonify(ok=True, message='There are no teams to correct.')
    if len(table.queue) == 1:
        return jsonify(ok=True, message='There is only a team to correct yet.')
    team = table.queue[0]
    if not table.remove_from_queue(team):
        return jsonify(ok=False, message='Problem removing the team from queue.')
    if table.add_to_queue(team, min(chief.skipped_positions, len(table.queue))):
        return jsonify(ok=True);
    return jsonify(ok=False, message='An error occurred while adding the team in the queue.')

@app.route('/table/<string:table_name>/switch_to_busy', methods=['POST'])
@auth.login_required
def switch_to_busy(table_name):
    if not authentication_manager.is_authorized(auth.username(), table_name): abort(401)
    if table_name not in chief.tables:
        return jsonify(ok=False, message=TABLE_NOT_EXIST.format(table_name))
    if chief.tables[table_name].switch_to_busy():
        return jsonify(ok=True)
    return jsonify(ok=False, message='An error occurred while switching to busy.')

@app.route('/table/<string:table_name>/switch_to_vacant', methods=['POST'])
@auth.login_required
def switch_to_vacant(table_name):
    if not authentication_manager.is_authorized(auth.username(), table_name): abort(401)
    if table_name not in chief.tables:
        return jsonify(ok=False, message=TABLE_NOT_EXIST.format(table_name))
    if chief.tables[table_name].switch_to_vacant():
        return jsonify(ok=True)
    return jsonify(ok=False, message='An error occurred while switching to vacant.')

@app.route('/table/<string:table_name>/get_queue', methods=['GET'])
def get_queue(table_name):
    if table_name not in chief.tables:
        return jsonify(ok=False, message=TABLE_NOT_EXIST.format(table_name))
    table_queue = chief.tables[table_name].queue
    return jsonify(ok=True, queue=table_queue)

@app.route('/table/<string:table_name>/get_all', methods=['GET'])
def get_all(table_name):
    if table_name not in chief.tables:
        return jsonify(ok=False, message=TABLE_NOT_EXIST.format(table_name))
    table = chief.tables[table_name]
    
    table_data = json.dumps(table.to_dict())
    return jsonify(ok=True, table_data=table_data)

# Return the tables data if and only if a new operation happened since last
# update.
@app.route('/tables/get_all', methods=['GET'])
def get_tables_if_changed():
    last_update = -1
    if 'last_update' in request.args:
        try:
            last_update = int(request.args['last_update'])
        except ValueError:
            return jsonify(ok=True, message='The last_update variable must represent an integer.')
    if chief.history_manager.operations_num == last_update:
        return jsonify(ok=True, changed=False)

    all_tables_data = json.dumps([chief.tables[table].to_dict() for table in chief.tables])
    return jsonify(ok=True, changed=True,
                   last_update=chief.history_manager.operations_num,
                   tables=all_tables_data)
    
# APIs relative to the history

@app.route('/history/add', methods=['POST'])
@auth.login_required
def history_add():
    req_data = json.loads(request.data)
    if 'team' not in req_data:
        return jsonify(ok=False, message=SPECIFY_TEAM)
    team = req_data['team']
    if 'table' not in req_data:
        return jsonify(ok=False, message='You have to specify a table.')
    table = req_data['table']
    if 'start_time' not in req_data:
        return jsonify(ok=False, message='You have to specify a start time.')
    start_time = req_data['start_time']
    if 'end_time' not in req_data:
        return jsonify(ok=False, message='You have to specify an end time.')
    end_time = req_data['end_time']
    if chief.history_manager.add(team, table, start_time, end_time):
        return jsonify(ok=True)
    return jsonify(ok=False, message='An error occurred while adding the entry in the history.')

@app.route('/history/delete', methods=['POST'])
@auth.login_required
def history_delete():
    req_data = json.loads(request.data)
    if 'correction_id' not in req_data:
        return jsonify(ok=False, message='You have to specify a correction id.')
    correction_id = req_data['correction_id']
    if chief.history_manager.delete(correction_id):
        return jsonify(ok=True)
    return jsonify(ok=False, message='An error occurred while deleting the entry from the history.')

@app.route('/history/get_corrections', methods=['GET'])
def get_corrections():
    req_data = json.loads(request.data)
    filters = {}
    if 'filters' in req_data:
        filters = req_data['filters']
    else:
        return jsonify(ok=False, message='You have to specify filters.')
    corrections_data = chief.history_manager.get_corrections(filters)
    corrections = []
    for correction in corrections_data:
        corrections.append({'team': correction.team,
                            'table': correction.table,
                            'start_time': correction.start_time,
                            'end_time': correction.end_time,
                            'id': str(correction.id)})
    return jsonify(ok=True, corrections=corrections)
