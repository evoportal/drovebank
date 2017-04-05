#!/usr/bin/env python
import os, sys, fnmatch
import shutil
import string
import random
import time
import logging

from drove_bank_constants import DroveBankConstants

class AtomicWrite(DroveBankConstants):

    def __init__(self, dir=None, filename=None):
        DroveBankConstants.__init__(self, dir)
        logging.basicConfig(filename='drovebank.log', level=logging.DEBUG)

        # set the dir for the file
        if dir is not None:
            self.dbdir = dir
        else:
            self.dbdir = '/home/tom/dbfiles'

        # set the filename in the constructor. can
        # set manually to reuse class
        if filename is not None:
            self.set_file_name(filename)
        else:
            self.filename = None

    # sets the filenames from the account id
    def set_account_id(self, account_id):
        fname = "%s.txt" % account_id
        filename = os.path.join(self.dbdir, fname)
        self.set_file_name(filename)

    # sets the filename
    def set_file_name(self, filename):
        if os.path.exists(filename) == False:
            logging.critical("input file %s doesn't exist!", filename)
            sys.exit(-1)
        self.filename = filename
        self.make_tmp_filenames()

    # makes the lock and tmp filenames
    def make_tmp_filenames(self):
        if os.path.isdir(self.dbdir) == False:
            logging.critical("DB file directory %s doesn't exist!", self.dbdir)
            sys.exit(-1)

        # get the file without any preceding path
        basename = os.path.basename(self.filename)
        prefix, suffix = os.path.splitext(basename)
        self.id = self.id_generator()
        tmpfile = prefix + "_" + self.id + suffix + ".tmp"
        oldfile = prefix + "_" + self.id + suffix + ".old"
        lockfile = prefix + ".lock"
        self.tmpfile = os.path.join(self.dbdir, tmpfile)
        self.oldfile = os.path.join(self.dbdir, oldfile)
        self.lockfilename = os.path.join(self.dbdir, lockfile)

    def id_generator(self):
        size=8
        chars=string.ascii_uppercase + string.digits
        return ''.join(random.choice(chars) for _ in range(size))

    def lock_file(self):
        loop = True
        while(loop):
            try:
                self.lockfile = open(self.lockfilename, 'wx')
                loop = False
            except IOError:
                logging.debug("AW0069 lock file exists. sleep 1 sec")
                time.sleep(1)

    def unlock_file(self):
        self.lockfile.close()
        os.remove(self.lockfilename)

    # writes content to file but assumes caller handles
    # file locking
    def write_content(self, content):
        #step 1 copy old file to tmp file
        shutil.copy2(self.filename, self.tmpfile)

        # step 2 write new data to tmpfile
        f = open(self.tmpfile, 'w')
        f.write(content)
        # don't forget to flush
        f.flush()
        f.close()

        #step 3 move orig file to old file
        shutil.move(self.filename, self.oldfile)

        # step 4 rename tmp file to orig file
        shutil.move(self.tmpfile, self.filename)

        # step 5 we cant delete the old file now.
        # if it fails it will get cleaned up on recovery
        os.remove(self.oldfile)


    #------------------------------------------------------------------------------
    # return a list of all matching files
    def ffind( self, pattern, path ):
        result = []
        for subdir, dirs, files in os.walk( path ):
            for fn in files:
                if fnmatch.fnmatch( fn, pattern ):
                    result.append( os.path.join( subdir, fn ))
                    return result

    # if lock file is there and only self.filename then we either crashed before
    # step 1 or after step 5. Either way just delete the lock file and move on.
    #
    # - If the self.filename is missing but old and tmp are there we crashed between
    # 3 and 4. Just redo step 4
    # - if self.filename is present and old is presnet then we crashed after step 4.
    # just remove the old file.
    # - if self.filename is present and tmp is present but not old we crashed before
    # step 3. remove tmp file. Transaction never happened.
    #
    def recover(self):
        # first lets look for lock files.
        for fn in self.ffind( "*.lock", self.dbdir):
            basename = fn[:-5]
            # this assumes the suffix is txt probably should make
            # this configurable
            filename = basename + ".txt"

            # for unit test has no affect on logic
            self.filename = filename

            # find the files
            basename = os.path.basename(filename)
            prefix, suffix = os.path.splitext(basename)

            tmpfile = None
            tmpfiletest = prefix + "_*" + suffix + ".tmp"
            for tfile in self.ffind(tmpfiletest, self.dbdir):
                logging.debug("AW0134 found tmpfile %s", tfile)
                tmpfile = tfile

            # if we didn't find any tmp files look for old files
            # else use the matching old file
            if tmpfile is None:
                oldfiletest = prefix + "_*" + suffix + ".old"
                for ofile in self.ffind(oldfiletest, self.dbdir):
                    logging.debug("AW0139 found oldfile %s", ofile)
                    oldfile = ofile
            else:
                oldfile = tmpfile.replace("tmp", "old")

            oldexists  = False
            if oldfile is not None and os.path.exists(oldfile):
                oldexists = True
                # for unit test has no affect on logic
                self.oldfile = oldfile

            tmpexists  = False
            if tmpfile is not None and os.path.exists(tmpfile):
                tmpexists = True
                # for unit test has no affect on logic
                self.tmpfile = tmpfile

            baseexists = os.path.exists(filename)

            # case 1 where we crashed before we could move the tmp file to the
            # new file. we know tmp file is valid because the old file was
            # created after the tmp file
            if baseexists is False and oldexists is True and tmpexists is True:
                logging.debug("AW0074 case 1 completing transaction by renaming tmp file %s to %s",
                              tmpfile, filename)
                shutil.move(tmpfile, filename)
                tmpexists = False
                basexists = True

            # all other cases we can only trust what is in the original file or
            # its case one
            if oldexists is True:
                logging.debug("AW0142 removing old file %s", oldfile)
                os.remove(oldfile)
            if tmpexists is True:
                logging.debug("AW0147 removing tmp file %s", tmpfile)
                os.remove(tmpfile)
            # delete the lock file
            logging.debug("AW0150 removing lock file %s", fn)
            os.remove(fn)

    # writes content to file with locks.
    def atomicwrite(self, content):
        self.lock_file()
        self.write_content(content)
        self.unlock_file()

    def set_dbdir(self, dbdir):
        self.dbdir = dbdir

    # for unit tests
    def get_id(self):
        return self.id
    def get_tmpfile(self):
        return self.tmpfile
    def get_oldfile(self):
        return self.oldfile
    def get_lockfilename(self):
        return self.lockfilename
