from cohmo import app, chief
from flask import Flask, request, jsonify #TODO where I have to put this thinks?



table_not_exist = 'Table {0} does not exist.'
team_not_exist = 'Team {0} does not exist.'
specify_team = 'You have to specify a team.'



@app.route('/table/<string:table_name>/remove_from_queue', methods = ['POST'])
def remove_from_queue(table_name):
    if table_name not in chief.tables:
        return jsonify(ok = False, message = table_not_exist.format(table_name))
    req_data = request.get_json()
    if 'team' not in req_data:
        return jsonify(ok = False, message = specify_team)
    team = req_data['team']
    if team not in chief.teams:
        return jsonify(ok = False, message = team_not_exist.format(team))
    if team not in chief.tables[table_name].queue:
        return jsonify(ok = False, message = 'Team {0} is not in queue at table {1}.'.format(team, table_name))
    if chief.tables[table_name].remove_from_queue(team):
        return jsonify(ok = True)
    return jsonify(ok = False)

@app.route('/table/<string:table_name>/add_to_queue', methods = ['POST'])
def add_to_queue(table_name):
    if table_name not in chief.tables:
        return jsonify(ok = False, message = table_not_exist.format(table_name))
    req_data = request.get_json()
    if 'team' not in req_data:
        return jsonify(ok = False, message = specify_team)
    team = req_data['team']
    if team not in chief.teams:
        return jsonify(ok = False, message = team_not_exist.format(team))
    if team in chief.tables[table_name].queue:
        return jsonify(ok = False, message = 'Team {0} is already in queue at table {1}.'.format(team, table_name))
    if chief.tables[table_name].add_to_queue(team):
        return jsonify(ok = True)
    return jsonify(ok = False)

@app.route('/table/<string:table_name>/get_queue', methods = ['GET'])
def get_queue(table_name):
    if table_name not in chief.tables:
        return jsonify(ok = False, message = table_not_exist.format(table_name))
    table_queue = chief.tables[table_name].queue
    return jsonify(ok = True, queue = table_queue)

@app.route('/table/<string:table_name>/start_coordination', methods = ['POST'])
def start_coordination(table_name):
    if table_name not in chief.tables:
        return jsonify(ok = False, message = table_not_exist.format(table_name))
    req_data = request.get_json()
    if 'team' not in req_data:
        return jsonify(ok = False, message = specify_team)
    team = req_data['team']
    if team not in chief.teams:
        return jsonify(ok = False, message = team_not_exist.format(team))
    if team in chief.tables[table_name].queue:
        return jsonify(ok = False, message = 'Team {0} is not in queue at table {1}.'.format(team, table_name))
    if chief.tables[table_name].start_coordination(team):
        return jsonify(ok = True)
    return jsonify(ok = False)
