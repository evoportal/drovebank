# -*- mode: python; python-indent-offset: 4; indent-tabs-mode: nil; -*-
#
# Sub classes AtomicWrite. Creates an account file.
import os
import logging
import shutil

from atomic_write import AtomicWrite

class AccountCreate(AtomicWrite):

    def __init__(self, dir=None):
        AtomicWrite.__init__(self, dir)
        logging.basicConfig(filename='drovebank.log', level=logging.DEBUG)
        self.set_file_name(self.get_index_filename())

    # this will
    #   1. lock the account index file.
    #   2. read the latest (highest) account number
    #   3  increment it
    #   4  write it back to the file
    def get_account_number(self):
        self.lock_file()
        # read index file.
        file = open(self.filename, 'r')
        last_id = file.readline()
        file.close()
        next_id = int(last_id.strip()) + 1
        content = "%s\n" % (next_id)
        self.write_content(content)
        self.unlock_file()
        return next_id


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
        basename = self.filename[:-5]
        lockfile = basename + ".lock"

        tmpfile = None
        tmpfiletest = "index_*.txt.tmp"
        for tfile in self.ffind(tmpfiletest, self.dbdir):
            logging.debug("AC0054 found index tmpfile %s", tfile)
            tmpfile = tfile

        oldfile = None
        oldfiletest = "index_*.txt.old"

        if tmpfile is None:
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

        # now remove any tmp account files
        for atmp in self.ffind("*.atmp", self.dbdir):
            logging.debug("AC0054 found index tmpfile %s", atmp)
            os.remove(atmp)


    #  create account file.
    #    1. call get_account_number
    #    2. create account file: name number.txt
    #    3. format csv file: fname,lname,balance
    #    4. write to tmp file
    #    5. do atomic rename to account file.
    def create_account(self, fname, lname, starting_balance=0.0):

        # validate
        error = False
        if fname is None or len(fname) == 0:
            logging.warning("AC0050 fname is null or empty")
            error = True
        if lname is None or len(lname) == 0:
            logging.warning("AC0053 lname is null or empty")
            error = True

        # test float
        if self.isfloat(starting_balance) == False:
            logging.warning("AC0127 starting balance is not a float: %s", starting_balance)
            error = True
        elif float(starting_balance) < 0.0:
            logging.warning("AC0055 starting balance is negative: %s", starting_balance)
            error = True


        # returns -1 on error
        if error is True:
            return -1

        self.account_id = self.get_account_number()
        csv = "%s,%s,%s\n" % (fname, lname, starting_balance)
        logging.debug("AC0064 create account %s, %s,%s,%s", self.account_id, fname, lname, starting_balance)

        # write out account file. since we had a lock around the
        # account number creation we don't need to worry about
        # putting a mutex around this operation. However writes
        # are not atomic so we will write to a tmp file then do
        # an atomic rename
        fname = "%s.txt.atmp" % (self.account_id)
        # make it canonical
        fname = os.path.join(self.dbdir, fname)
        # create the true name
        afile = "%s.txt" % (self.account_id)
        self.account_file = os.path.join(self.dbdir, afile)

        # write out the tmp file
        f = open(fname, 'w')
        f.write(csv)
        f.close()

        # now do atomic rename
        shutil.move(fname, self.account_file)
        logging.debug("AC0086 create account %s completed. File: %s", self.account_id, self.account_file)
        return self.account_id

    def get_account_file(self):
        return self.account_file

    def get_account_id(self):
        return self.account_id
