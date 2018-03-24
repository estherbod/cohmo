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

    # Deletes a correction and returns True if it was succesfully deleted.
    def delete(self, correction_id):
        for correction in self.corrections:
            if correction.id == correction_id:
                self.corrections.remove(correction)
                return True
        return False

    # Returns a (eventually empty) list of corrections that satisfies all the
    # given properties. If all corrections are desired, no property should be
    # specified.
    # The properties have to be passed as keywords arguments and the possible
    # arguments are:
    # identifier: The unique id of the correction.
    # table: The table that performed the correction.
    # team: The team concerned by the correction.
    # start_time: A pair of timestamps. All corrections that start in that range
    #             are returned.
    # end_time: Exactly as start_time, but the corrections that END in that
    #           range re returned.
    def get_corrections(self, **properties):
        result = []
        for correction in self.corrections:
            filtered_correction = True
            if 'identifier' in properties:
                filtered_correction &= correction.id == properties['identifier']
            if 'table' in properties:
                filtered_correction &= correction.table == properties['table']
            if 'team' in properties:
                filtered_correction &= correction.team == properties['team']
            if 'start_time' in properties:
                filtered_correction &= (
                    properties['start_time'][0]
                    <= correction.start_time
                    <= properties['start_time'][1])
            if 'end_time' in properties:
                filtered_correction &= (
                    properties['end_time'][0]
                    <= correction.end_time
                    <= properties['end_time'][1])
            
            if filtered_correction: result.append(correction)
        return result

    # Loads the corrections from a file. The current corrections are deleted.
    # Can raise a ValueError if the file is malformed.
    # The file must be a csv file where each row contains a correction in the
    # form: team, table, start_time, end_time, id
    def load_from_file(self, path):
        try:
            with open(path, newline='') as history_file:
                history_reader = csv.reader(
                    history_file, delimiter=',', quotechar='"')
                for row in history_reader:
                    if not row: continue
                    assert(len(row) == 5)
                    self.corrections.append(Correction(*row))
        except AssertionError:
            raise ValueError('The file \'{0}\' is malformed.'.format(path))

    # Dumps all the corrections to a file. The format is the same used by
    # load_from_file, see the header comments of that method for the
    # specifications.
    def dump_to_file(self, path):
        with open(path, 'w', newline='') as history_file:
            history_writer = csv.writer(history_file, delimiter=',',
                                        quotechar='"',
                                        quoting=csv.QUOTE_MINIMAL)
            for correction in corrections:
                history_writer.writerow([correction.team, correction.table,
                                        correction.start_time,
                                        correction.end_time, correction.id])
