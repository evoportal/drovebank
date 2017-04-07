#!/usr/bin/env python
# -*- mode: python; python-indent-offset: 4; indent-tabs-mode: nil; -*-
#
# sub class of AccoutActions
#
# should be called if the server has crashed before running any clients.
#
import os, sys, fnmatch
import shutil
import string
import random
import time
import logging
import re
import argparse

from account_util import AccountUtil
from account_actions import AccountActions
from atomic_write import AtomicWrite
from collections import namedtuple

try:
    mode=int(raw_input('Input:'))
except ValueError:
    print "Not a number"
class Recover(AccountActions):

    def __init__(self, dir=None):
        AccountActions.__init__(self, dir)

    # public
    # transfers money from one account to another.
    # returns True on success False on failue
    # error string can be retrieved using get_error_string
    def recover(self):
        self.__recover_transfers()
        self.recover_write()

    def __recover_transfers(self):
        pair_hash = self.find_pairs()
        for transid, pset in pair_hash.iteritems():

            # look for sole survior (should only happen
            # if crashed in the middle of step 4
            if len(pset) == 1:
                self.__handle_sole_pset(transid, pset)
                continue

            plist = list(pset)
            lockfile_1 = self.__make_lock_filename(plist[0])
            lockfile_2 = self.__make_lock_filename(plist[1])

            # AccountActions.recover_transfer will clean up
            # this transfer
            aa = AccountActions(self.dbdir)
            aa.recover_transfer(lockfile_1, lockfile_2)


    # find the pairs of transactions
    def find_pairs(self):
        self.set_tmp_suffix("xtmp")
        self.set_old_suffix("xold")

        pair_hash = {}
        p = re.compile('(^\d+\w)(\w{8})')

        tmpfile = None
        tmpfiletest = "*." + self.tmpsuffix
        for tfile in self.ffind(tmpfiletest, self.dbdir):
            tmpfile = tfile
            basename = os.path.basename(tmpfile)

            # use regex to extract transid and pid
            m = p.match(basename)
            transid = m.group(2)
            pid = int(m.group(1).replace("_", ""))
            logging.debug("RCVR0050 tfile = %s pid = %s transid = %s", tfile, pid, transid)

            # build pairs of pids using a set
            if transid in pair_hash:
                pset = pair_hash[transid]
                if pid not in pset:
                    pset.add(pid)
            else:
                pset = set()
                pset.add(pid)
                pair_hash[transid] = pset


        # if we didn't find any tmp files look for old files
        # else use the matching old file
        oldfile = None
        oldfiletest = "*." + self.oldsuffix
        for ofile in self.ffind(oldfiletest, self.dbdir):
            oldfile = ofile
            basename = os.path.basename(oldfile)

            # use regex to extract transid and pid
            m = p.match(basename)
            transid = m.group(2)
            pid = int(m.group(1).replace("_", ""))

            # build pairs of pids using a set
            logging.debug("RCVR0072 ofile = %s pid = %s transid = %s", ofile, pid, transid)
            if transid in pair_hash:
                pset = pair_hash[transid]
                if pid not in pset:
                    pset.add(pid)
            else:
                pset = set()
                pset.add(pid)
                pair_hash[transid] = pset

        return pair_hash

    # there be private utility functions down here.
    def __make_lock_filename(self, pid):
        basename = "%d.lock" % pid
        fname = os.path.join(self.dbdir, basename)

        logging.debug("RCVR0103 making lock filename %s", fname)

        return fname

    def __safe_os_remove(self, filename):
        if os.path.exists(filename) is True:
            os.remove(filename)

    def __handle_sole_pset(self, transid, pset):
        pid = list(pset)[0]
        logging.debug("RCVR011 handle sole pset %s %d", transid, pid)

        lockfile = self.__make_lock_filename(pid)

        oldbase = "%d_%s.txt.xold" % (pid, transid)
        oldfile = os.path.join(self.dbdir, oldbase)

        tmpbase = "%d_%s.txt.xtmp" % (pid, transid)
        tmpfile = os.path.join(self.dbdir, tmpbase)

        self.__safe_os_remove(tmpfile)
        self.__safe_os_remove(oldfile)
        self.__safe_os_remove(lockfile)

def main():
  parser = argparse.ArgumentParser(description='recover db from system crash')
  parser.add_argument('-d', '--dir', help='data directory', default=None)
  args = parser.parse_args()
  in_dir = args.dir
  Recover(in_dir).recover()

if __name__ == "__main__":
  main()
