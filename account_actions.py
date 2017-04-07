#!/usr/bin/env python
# -*- mode: python; python-indent-offset: 4; indent-tabs-mode: nil; -*-
#
# sub class of AccountUtil.
#
# provides the three account actions
#  - deposit
#  - withdrawl
#  - transfer
import os, sys, fnmatch
import shutil
import string
import random
import time
import logging
import re

from account_util import AccountUtil
from atomic_write import AtomicWrite
from collections import namedtuple

class AccountActions(AccountUtil):

    def __init__(self, dir=None):
        AccountUtil.__init__(self, dir)

    # public
    # transfers money from one account to another.
    # returns True on success False on failue
    # error string can be retrieved using get_error_string
    def transfer_money(self, from_id, to_id, amount):
        error = False
        self.clear_errors()

        # test args
        if self.isfloat(amount) == False:
            logging.warning("XFER0027 transfer amount is not a float: %s", amount)
            err = "amount to transfer is not a valid number: %s" % amount
            self.add_error(err)
            error = True
        elif float(amount) < 0.0:
            err = "amount to transfer cannont be a negative number: %s" % amount
            self.add_error(err)
            logging.warning("XFER0034 deposit is negative: %s", amount)
            error = True

        # test account ids
        if self.isint(from_id) == False or self.isint(to_id) is False:
            logging.warning("XFER0022 one of the account ids is not valie: %s %s", from_id, to_id)
            err = "account id is not a valid number: %s" % account_id
            self.add_error(err)
            error = True
        elif self.check_account_file(from_id) is False:
            err = "account from id is not valid: %s" % from_id
            self.add_error(err)
            logging.warning("XFER0046: from account number %s is not known", from_id)
            error = True
        elif self.check_account_file(to_id) is False:
            err = "account to id is not valid: %s" % to_id
            self.add_error(err)
            logging.warning("XFER0046: to account number %s is not known", to_id)
            error = True

        # this method returns the new balance and -1 on error
        if error is True:
            return False

        from_file = self.get_account_filename(from_id)
        to_file = self.get_account_filename(to_id)
        return self.__transfer_money(from_file, to_file, amount)

    # private
    # transfers money from one account to another. no error
    # checking on args.
    def __transfer_money(self, from_file, to_file, amount):

        from_aw = AtomicWrite(self.dbdir)
        to_aw = AtomicWrite(self.dbdir)

        # we want both account's temp files to have
        # the same trans id
        transid = from_aw.id_generator()
        from_aw.set_transid(transid)
        to_aw.set_transid(transid)

        # set different suffixes on tmp files to
        # differentiate transfer intermediate files
        # from deposit and withdraw
        from_aw.set_old_suffix("xold")
        to_aw.set_old_suffix("xold")
        from_aw.set_tmp_suffix("xtmp")
        to_aw.set_tmp_suffix("xtmp")

        # set the files
        from_aw.set_file_name(from_file)
        to_aw.set_file_name(to_file)

        from_aw.lock_file()
        to_aw.lock_file()


        #step 1 copy old files to tmp files
        shutil.copy2(from_file, from_aw.get_tmpfile())
        shutil.copy2(to_file, to_aw.get_tmpfile())

        from_info = self.__read_account_info(from_file)
        to_info = self.__read_account_info(to_file)

        from_balance = from_info.balance - amount
        if from_balance < 0:
            logging.warning("XFER0044 not enough money in source account")
            self.add_error("not enough money in source account")
            return False

        to_balance = to_info.balance + amount

        # step 2 write new values to tmp file
        from_content = "%s,%s,%s\n" % (from_info.fname, from_info.lname, from_balance)
        self.__write_content(from_aw.get_tmpfile(), from_content);
        to_content = "%s,%s,%s\n" % (to_info.fname, to_info.lname, to_balance)
        self.__write_content(to_aw.get_tmpfile(), to_content);

        #step 3 move orig file to old file
        shutil.move(from_file, from_aw.get_oldfile())
        shutil.move(to_file, to_aw.get_oldfile())

        # step 4 rename tmp file to orig file
        shutil.move(from_aw.get_tmpfile(), from_file)
        shutil.move(to_aw.get_tmpfile(), to_file)

        # step 4 we cant delete the old file now.
        # if it fails it will get cleaned up on recovery
        os.remove(from_aw.get_oldfile())
        os.remove(to_aw.get_oldfile())

        from_aw.unlock_file()
        to_aw.unlock_file()
        return True

    def __get_tmp_files(self, lockfile):
        # get the db txt files for the two lockfiles
        basename = lockfile[:-5]
        filename = basename + ".txt"
        transid = None
        #p = re.compile('(^\d+\w)(\w{8})')

        # find the files
        basename = os.path.basename(filename)
        prefix, suffix = os.path.splitext(basename)

        tmpfile = None
        tmpfiletest = prefix + "_*" + suffix + "." + self.tmpsuffix
        for tfile in self.ffind(tmpfiletest, self.dbdir):
            logging.debug("AA0155 found tmpfile %s", tfile)
            tmpfile = tfile

        # if we didn't find any tmp files look for old files
        # else use the matching old file
        oldfile = None
        if tmpfile is None:
            oldfiletest = prefix + "_*" + suffix + "." + self.oldsuffix
            for ofile in self.ffind(oldfiletest, self.dbdir):
                logging.debug("AA0169 found oldfile %s", ofile)
                oldfile = ofile
                tmpfile = oldfile.replace(self.oldsuffix, self.tmpsuffix)
        else:
            oldfile = tmpfile.replace(self.tmpsuffix, self.oldsuffix)

        Filelist = namedtuple('filelist', 'lockfile tmpfile oldfile filename')
        files = Filelist(lockfile, tmpfile, oldfile, filename)
        return files

    def __file_exists(self, fname):
        if fname is None:
            return False
        return os.path.exists(fname)

    # public
    #
    #  state: the server has crashed and the caller found the
    # two lockfiles involved in a transfer. this will only
    # happen is we have matching IDs in xtmp or xold files.
    def recover_transfer(self, lockfile_1, lockfile_2):

        print "%s %s" % (lockfile_1, lockfile_2)
        # since this is a transfer we need to set the suffix
        self.set_old_suffix("xold")
        self.set_tmp_suffix("xtmp")

        files_1 = self.__get_tmp_files(lockfile_1)
        files_2 = self.__get_tmp_files(lockfile_2)

        xtmp1_exists = self.__file_exists(files_1.tmpfile)
        xtmp2_exists = self.__file_exists(files_2.tmpfile)
        print "1 %s %s" % (xtmp1_exists, files_1.tmpfile)
        print "2 %s %s" % (xtmp2_exists, files_2.tmpfile)

        xold1_exists = self.__file_exists(files_1.oldfile)
        xold2_exists = self.__file_exists(files_2.oldfile)

        file1_exists = self.__file_exists(files_1.filename)
        file2_exists = self.__file_exists(files_2.filename)

        # first case
        # assumes moves are atomic
        # if we die during steps 3 and 4 we will have
        # either none or one actual files. In all cases
        # we would have finished step 2 so the tmp files
        # have good data. mv the tmp files to the actual files
        if file1_exists is False or file2_exists is False:
            logging.info("AA0214:RECOVER case 1. Moving tmp files to actual files")
            if xtmp1_exists is True:
                shutil.move(files_1.tmpfile, files_1.filename)
                xtmp1_exists = False
                file1_exists = True
            if xtmp2_exists is True:
                shutil.move(files_2.tmpfile, files_2.filename)
                xtmp1_exists = False
                file1_exists = True

        # in all other cases if the server has died what is
        # in the actual file is correct. it may be before or
        # after the transfer, the drovebank.log would say.
        # you could also add a transaction log to inform
        # the user but out of scope of the specification

        # cleanup
        self.__delete_filelist(files_1)
        self.__delete_filelist(files_2)

    def __delete_filelist(self, flist, includefilename=False):

        if includefilename is True:
            if flist.filename is not None and os.path.exists(flist.filename):
                os.remove(flist.filename)
        if flist.tmpfile is not None and os.path.exists(flist.tmpfile):
            os.remove(flist.tmpfile)
        if flist.oldfile is not None and os.path.exists(flist.oldfile):
            os.remove(flist.oldfile)
        if flist.lockfile is not None and os.path.exists(flist.lockfile):
            os.remove(flist.lockfile)

    # private
    # function that writes content to file
    # no arg checking
    # assumes caller has locked file
    def __write_content(self, filename, content):
        f = open(filename, 'w')
        f.write(content)
        f.flush()
        f.close()

    # private
    # function that reads account info
    # no arg checking
    def __read_account_info(self, filename):
        # read in file
        file = open(filename, 'r')
        file_contents = file.readline()
        file.close()

        vals = file_contents.split(',')
        balance = float(vals[2].strip())
        Account = namedtuple('Account', 'fname lname balance')
        account = Account(vals[0], vals[1], balance)
        return account
