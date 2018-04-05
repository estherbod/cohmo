import json

# This class handles the authentication of users.
# It is constructed directly from a JSON files containing users, passwords
# and authorizations.
class AuthenticationManager:
    def __init__(self, auth_path):
        with open(auth_path) as auth_file:    
            self.users = json.load(auth_file)

    def verify_password(self, user, password):
        if user not in self.users: return False
        return self.users[user]['password'] == password

    def is_authorized(self, user, table):
        if user not in self.users: return False
        return self.is_admin(user) or table in self.users[user]['authorizations']

    def is_admin(self, user):
        if user not in self.users: return False
        return ('admin' in self.users[user]) and self.users[user]['admin']
