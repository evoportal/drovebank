# -*- mode: python; python-indent-offset: 4; indent-tabs-mode: nil; -*-
#
# Constants
import logging
import os

class DroveBankConstants:

    def __init__(self, dir=None):
        logging.basicConfig(filename='drovebank.log', level=logging.DEBUG)

        # set the dir for the file
        if dir is not None:
            self.dbdir = dir
        else:
            self.dbdir = '/home/tom/dbfiles'

        self.index_filename = os.path.join(self.dbdir, 'index.idx')
        self.errors = []

    def get_index_filename(self):
        return self.index_filename

    def isfloat(self, value):
        try:
            float(value)
            return True
        except ValueError:
            return False

    def isint(self, value):
        try:
            int(value)
            return True
        except ValueError:
            return False

    def clear_errors(self):
        self.errors = []

    def add_error(self, errorstring):
        self.errors.append(errorstring)

    def get_error_string(self):
        errorstring = ""
        for err in self.errors:
            errorstring = "%s\n%s" % (errorstring, err)
        return errorstring

    def set_dbdir(self, dbdir):
        self.dbdir = dbdir

    def get_dbdir(self):
        return self.dbdir
