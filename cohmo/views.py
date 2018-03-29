from cohmo import app, chief
from flask import Flask, request, jsonify #TODO where I have to put this thinks?



TABLE_NOT_EXIST = 'Table {0} does not exist.'
TEAM_NOT_EXIST = 'Team {0} does not exist.'
SPECIFY_TEAM = 'You have to specify a team.'


# API relative to a table

@app.route('/table/<string:table_name>/add_to_queue', methods = ['POST'])
def add_to_queue(table_name):
    if table_name not in chief.tables:
        return jsonify(ok = False, message = TABLE_NOT_EXIST.format(table_name))
    req_data = request.get_json()
    if 'team' not in req_data:
        return jsonify(ok = False, message = SPECIFY_TEAM)
    team = req_data['team']
    if team not in chief.teams:
        return jsonify(ok = False, message = TEAM_NOT_EXIST.format(team))
    if team in chief.tables[table_name].queue:
        return jsonify(ok = False,
                       message = 'Team {0} is already in queue at table {1}.'.format(team, table_name))
    if chief.tables[table_name].add_to_queue(team):
        return jsonify(ok = True)
    return jsonify(ok = False)

@app.route('/table/<string:table_name>/remove_from_queue', methods = ['POST'])
def remove_from_queue(table_name):
    if table_name not in chief.tables:
        return jsonify(ok = False, message = TABLE_NOT_EXIST.format(table_name))
    req_data = request.get_json()
    if 'team' not in req_data:
        return jsonify(ok = False, message = SPECIFY_TEAM)
    team = req_data['team']
    if team not in chief.teams:
        return jsonify(ok = False, message = TEAM_NOT_EXIST.format(team))
    if team not in chief.tables[table_name].queue:
        return jsonify(ok = False,
                       message = 'Team {0} is not in queue at table {1}.'.format(team, table_name))
    if chief.tables[table_name].remove_from_queue(team):
        return jsonify(ok = True)
    return jsonify(ok = False)

@app.route('/table/<string:table_name>/swap_teams_in_queue', methods = ['POST'])
def swap_teams_in_queue(table_name):
    if table_name not in chief.tables:
        return jsonify(ok = False, message = TABLE_NOT_EXIST.format(table_name))
    req_data = request.get_json()
    if 'teams' not in req_data:
        return jsonify(ok = False,
                       message = 'You have to specify the teams to be swapped.')
    teams = req_data['teams']
    if len(teams) != 2:
        return jsonify(ok = False,
                       message = 'You have to give exactly two teams to be swapped.')
    for team in teams:
        if team not in chief.teams:
            return jsonify(ok = False, message = TEAM_NOT_EXIST.format(team))
        if team not in chief.tables[table_name].queue:
            return jsonify(ok = False,
                           message = 'Team {0} is not in queue at table {1}.'.format(team, table_name))
    if chief.tables[table_name].swap_teams_in_queue(teams[0], teams[1]):
        return jsonify(ok = True)
    return jsonify(ok = False)

@app.route('/table/<string:table_name>/get_queue', methods = ['GET'])
def get_queue(table_name):
    if table_name not in chief.tables:
        return jsonify(ok = False, message = TABLE_NOT_EXIST.format(table_name))
    table_queue = chief.tables[table_name].queue
    return jsonify(ok = True, queue = table_queue)

@app.route('/table/<string:table_name>/start_coordination', methods = ['POST'])
def start_coordination(table_name):
    if table_name not in chief.tables:
        return jsonify(ok = False, message = TABLE_NOT_EXIST.format(table_name))
    req_data = request.get_json()
    if 'team' not in req_data:
        return jsonify(ok = False, message = SPECIFY_TEAM)
    team = req_data['team']
    if team not in chief.teams:
        return jsonify(ok = False, message = TEAM_NOT_EXIST.format(team))
    if team in chief.tables[table_name].queue:
        return jsonify(ok = False,
                       message = 'Team {0} is not in queue at table {1}.'.format(team, table_name))
    if chief.tables[table_name].start_coordination(team):
        return jsonify(ok = True)
    return jsonify(ok = False)

@app.route('/table/<string:table_name>/finish_coordination', methods = ['POST'])
def finish_coordination(table_name):
    if table_name not in chief.tables:
        return jsonify(ok = False, message = TABLE_NOT_EXIST.format(table_name))
    if chief.tables[table_name].finish_coordination():
        return jsonify(ok = True)
    return jsonify(ok = False)

@app.route('/table/<string:table_name>/pause_coordination', methods = ['POST'])
def pause_coordination(table_name):
    if table_name not in chief.tables:
        return jsonify(ok = False, message = TABLE_NOT_EXIST.format(table_name))
    team = chief.tables[table_name].current_coordination_team # TODO: maybe check this is not malformed
    if chief.tables[table_name].finish_coordination():
        if chief.tables[table_name].add_to_queue(team): # TODO: maybe put the team in a different position
            return jsonify(ok = True);
        return jsonify(ok = False)
    return jsonify(ok = False)

@app.route('/table/<string:table_name>/switch_to_calling', methods = ['POST'])
def switch_to_calling(table_name):
    if table_name not in chief.tables:
        return jsonify(ok = False, message = TABLE_NOT_EXIST.format(table_name))
    if chief.tables[table_name].switch_to_calling():
        return jsonify(ok = True)
    return jsonify(ok = False)

# APIs relative to the history

@app.route('/history/add', methods = ['POST'])
def history_add():
    req_data = request.get_json()
    if 'team' not in req_data:
        return jsonify(ok = False, message = SPECIFY_TEAM)
    team = req_data['team']
    if 'table' not in req_data:
        return jsonify(ok = False, message = 'You have to specify a table.')
    table = req_data['table']
    if 'start_time' not in req_data:
        return jsonify(ok = False, message = 'You have to specify a start time.')
    start_time = req_data['start_time']
    if 'end_time' not in req_data:
        return jsonify(ok = False, message = 'You have to specify an end time.')
    end_time = req_data['end_time']
    if chief.history_manager.add(team, table, start_time, end_time):
        return jsonify(ok = True)
    return jsonify(ok = False)

@app.route('/history/delete', methods = ['POST'])
def history_delete():
    req_data = request.get_json()
    if 'correction_id' not in req_data:
        return jsonify(ok = False, message = 'You have to specify a correction id.')
    correction_id = req_data['correction_id']
    if chief.history_manager.delete(correction_id):
        return jsonify(ok = True)
    return jsonify(ok = False)

@app.route('/history/get_corrections', methods = ['GET'])
def get_corrections():
    req_data = request.get_json()
    filters = {}
    if 'filters' in req_data:
        filters = req_data['filters']
    else:
        return jsonify(ok = False, message = 'You have to specify filters.')
    return jsonify(ok = True,
                   corrections = chief.history_manager.get_corrections(filters))
