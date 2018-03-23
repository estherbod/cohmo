import sys
from base64 import b64encode
from os import urandom
import csv

# Simple class to store a correction.
class Correction:
    def __init__(self, team, table, start_time, end_time, identifier=None):
        assert(end_time >= start_time)
        self.team = team
        self.table = table
        self.start_time = start_time # timestamp in seconds
        self.end_time = end_time # timestamp in seconds
        if identifier: self.id = identifier
        else: self.id = b32encode(urandom(10)) # Generating a unique id

    # Returns the duration in seconds.
    def duration(self):
        return self.end_time - self.start_time

# The manager of the past corrections.
# The internal state is simply a list of corrections.
# It can load (and dump) the history from a csv file.
class HistoryManager:
    def __init__(self):
        self.corrections = []

    # Adds a single correction to the history.
    def add(self, team, table, start_time, end_time):
        self.corrections.append(Correction(team, table, start_time, end_time))

    # Loads the corrections from a file. The current corrections are deleted.
    # Can raise a ValueError if the file is malformed.
    # The file must be a csv file where each row contains a correction in the
    # form: team, table, start_time, end_time, id
    def load_from_file(self, path):
        try:
            with open(path, newline='') as history_file:
                history_reader = csv.reader(history_file, delimiter=',', quotechar='"')
                for row in history_reader:
                    assert(len(row) == 5)
                    self.corrections.append(Correction(*row))
        except AssertionError:
            raise ValueError('The file \'{0}\' is malformed.'.format(path))

    # Returns the correction with the desired id if it exists, None otherwise.
    def get_correction(self, correction_id):
        for correction in self.corrections:
            if correction.id == correction_id: return correction
        return None

    # Deletes a correction and returns True if it was succesfully deleted.
    def delete_correction(self, correction_id):
        for correction in self.corrections:
            if correction.id == correction_id:
                self.corrections.remove(correction)
                return True
        return False
