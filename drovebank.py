#!/usr/bin/env python
# -*- mode: python; python-indent-offset: 4; indent-tabs-mode: nil; -*-
#
# sub class of AccoutActions
#
# should be called if the server has crashed before running any clients.
#
import os, sys
import logging
import argparse

from account_create import AccountCreate
from account_actions import AccountActions

# python doesn't have a switch statement so I
# emulated one using
class switch(object):
    def __init__(self, value):
        self.value = value
        self.fall = False

    def __iter__(self):
        """Return the match method once, then stop"""
        yield self.match
        raise StopIteration

    def match(self, *args):
        """Indicate whether or not to enter a case suite"""
        if self.fall or not args:
            return True
        elif self.value in args: # changed for v1.5, see below
            self.fall = True
            return True
        else:
            return False

class DroveBank(AccountActions):

    def __init__(self, dir=None):
        AccountActions.__init__(self, dir)
        self.client_list_dirty = True
        self.client_list = []

        #  create the index file
        if os.path.exists(self.dbdir) is False:
            logging.critical("DB0046 The data directory doesn't exist: %s", self.dbdir)
            print "The data directory doesn't exist: %s" % self.dbdir
            sys.exit(-1)

        # make the index file if needed
        index_filename = os.path.join(self.dbdir, "index.idx")
        if os.path.exists(index_filename) is False:
            logging.info("DB0011 making index file: %s", index_filename)
            f = open(index_filename, 'w')
            f.write('0\n')
            f.close()

    # public
    # transfers money from one account to another.
    # returns True on success False on failue
    # error string can be retrieved using get_error_string
    def run(self):
        should_exit = False

        self.__print_main_menu_text()

        while should_exit is False:
            command = raw_input('Command [toplevel]: ')
            for case in switch(command):
                if case('e'):
                    should_exit = True
                    print "Bye!"
                    break
                if case('q'):
                    should_exit = True
                    print "Bye!"
                    break
                if case('h'):
                    self.__print_main_menu_text()
                    break
                if case('l'):
                    self.__print_accounts()
                    break
                if case('c'):
                    self.__create_account()
                    break
                if case('w'):
                    self.__withdraw()
                    break
                if case('d'):
                    self.__deposit()
                    break
                if case('t'):
                    self.__transfer()
                    break
                if case():
                    print "Unknown command %s" % (command)

    def __create_account(self):
        print "Adding a client"
        print "At any time you want to exit hit 'q'\n"
        command = raw_input('First Name [account creation]: ')
        if command == 'q':
            return
        fname = command

        command = raw_input('Last Name [account creation]: ')
        if command == 'q':
            return
        lname = command

        aloop = True
        balance = 0
        while aloop:
            balance = raw_input('Starting Balance [account creation]: ')
            if balance == 'q':
                return
            if self.isfloat(balance) is False:
                print "Starting balance must be a number: %s" % balance
                continue
            aloop = False

        self.clear_errors()
        ac = AccountCreate(self.dbdir)
        # since we added an account we can't use the cached
        # version.
        self.client_list_dirty = True
        id = ac.create_account(fname, lname, balance)

        if id == -1:
            print "There was a problem creating your account"
            print ac.get_error_string()
        else:
            print "Account created successfully, id = %s"% id

    def __withdraw(self):
        print "Withdraw money from an account"
        print "At any time you want to exit hit 'q'\n"

        idloop = True
        ac_id = -1
        balance = 0
        while idloop is True:
            self.clear_errors()
            ac_id = raw_input('Account ID [withdraw]: ')
            if ac_id == 'q':
                return
            if self.isint(ac_id) is False:
                print "account id must be an integer"
                continue

            balance = self.__print_account_balance(ac_id)
            if balance == -1:
                print ac.get_error_string()
                continue
            idloop = False

        print "Old balance for id %s is %8.2f" % (ac_id, float(balance))

        wloop = True
        while wloop is True:
            self.clear_errors()
            withdraw = raw_input('Amount [withdraw]: ')
            if withdraw == 'q':
                return
            if self.isfloat(withdraw) is False:
                print "This field only accepts numbers"
                continue
            if (float(balance) - float(withdraw)) < 0.0:
                print "You can't withdraw more money than you have"
                continue

            new_balance = self.withdraw(ac_id, float(withdraw))
            if new_balance == -1:
                print ac.get_error_string()
            wloop = False

        print "New balance for id %s is %8.2f" % (ac_id, float(new_balance))

    def __deposit(self):
        print "Deposit money to an account"
        print "At any time you want to exit hit 'q'\n"

        idloop = True
        ac_id = 0
        while idloop is True:
            self.clear_errors()
            ac_id = raw_input('Account ID [deposit] : ')
            if ac_id == 'q':
                return
            if self.isint(ac_id) is False:
                print "account id must be an integer"
                continue
            idloop = False

        dloop = True
        while dloop is True:
            self.clear_errors()
            deposit = raw_input('Amount [deposit] : ')
            if deposit == 'q':
                return
            if self.isfloat(deposit) is False:
                print "This field only accepts numbers"
                continue

            new_balance = self.deposit(ac_id, float(deposit))
            if new_balance == -1:
                print ac.get_error_string()
                continue
            dloop = False
            print "New balance for id %s is %8.2f" % (ac_id, float(new_balance))

    def __transfer(self):
        print "Transfer money from one account to another"
        print "At any time you want to exit hit 'q'\n"

        idloop = True
        while idloop is True:
            self.clear_errors()
            from_id = raw_input('From ID [xfer]: ')
            if from_id == 'q':
                return
            to_id = raw_input('To ID [xfer]: ')
            if to_id == 'q':
                return
            from_balance = self.__print_account_balance(from_id)
            if from_balance == -1:
                print self.get_error_string()
                continue
            to_balance = self.__print_account_balance(to_id)
            if to_balance == -1:
                print self.get_error_string()
                continue
            print "Current Balances: %s = %8.2f to %s = %8.2f" % (from_id,
                                                            float(from_balance),
                                                                  to_id, float(to_balance))
            idloop = False

        xloop = True
        while xloop is True:
            self.clear_errors()
            amount = raw_input('Amount [xfer]: ')
            if amount == 'q':
                return

            if self.isfloat(amount) is False:
                print "This field only accepts numbers"
                continue

            new_balance = self.transfer_money(from_id, to_id, float(amount))
            if new_balance == -1:
                print ac.get_error_string()
                continue
            xloop = False
            fb = float(from_balance) - float(amount)
            tb = float(to_balance) + float(amount)
            print "New balances: %s = %8.2f to %s = %8.2f" % (from_id,
                                                              fb, to_id, tb)

    def __print_main_menu_text(self):
        print "Welcome to Drove Bank"
        print "This is the main menu"
        print "The following commands are available:"
        print "\tl - list the accounts"
        print "\tc - create an account"
        print "\tt - transfer money between two accounts"
        print "\td - deposit money to an account"
        print "\tw - withdraw money from an account"
        print "\th - prints this"
        print "\te - exit"

    def __print_accounts(self):
        if self.client_list_dirty is True:
            self.client_list = self.print_accounts()
            self.client_list_dirty = False
        for line in self.client_list:
            print line

    # returns the balance from the id
    def __print_account_balance(self, id):
        ac_info = self.get_account_info(id)
        if ac_info is None:
            print self.get_error_string()
            return -1

        balance = ac_info.balance
        return balance



def main():

    parser = argparse.ArgumentParser(description='Drove Bank Client')
    parser.add_argument('-d', '--dir', help='data directory', default=None)
    args = parser.parse_args()
    in_dir = args.dir
    DroveBank(in_dir).run()

if __name__ == "__main__":
  main()
