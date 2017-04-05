# -*- mode: python; python-indent-offset: 4; indent-tabs-mode: nil; -*-
#
# Sub classes AtomicWrite. Can perform the following functions
# on an account:
#    - deposit
#    - withdraw
#
import os
import logging
from collections import namedtuple

from atomic_write import AtomicWrite

class AccountUtil(AtomicWrite):

    def __init__(self, dir=None):
        AtomicWrite.__init__(self, dir)
        logging.basicConfig(filename='drovebank.log', level=logging.DEBUG)

    # private function that gets account filename
    def __get_account_filename(self, account_id):
        fname = "%s.txt" % account_id
        return os.path.join(self.dbdir, fname)

    # private: check if account file exists.
    # no error checking on args
    def __check_account_file(self, account_id):
        return os.path.exists(self.__get_account_filename(account_id))

    # private: makes a deposit to an account. no eror checking
    # of inputs
    def __make_deposit(self, account_id, amount):

        # sets up the filenames
        self.set_account_id(account_id)

        # lock file
        self.lock_file()

        account_info = self.__read_account_info(account_id)
        logging.debug("AU0033 balance for account %s is %s\n", account_id, account_info.balance)
        balance = account_info.balance + amount
        content = "%s,%s,%s\n'" % (account_info.fname, account_info.lname, balance)
        self.write_content(content)

        #unlock file
        self.unlock_file()

        # write to log after done so if there is a failure we can see the unmatched
        # transaction
        logging.debug("AU0040 new balance for account %s is %s\n", account_id, balance)
        return balance

    # makes a deposit to account. returns balance or -1 on error.
    # call getError to get error string
    def deposit(self, account_id, amount):
        error = False
        self.clear_errors()

        # test args
        if self.isfloat(amount) == False:
            logging.warning("AU0022 deposit is not a float: %s", amount)
            err = "amount to deposit is not a valid number: %s" % amount
            self.add_error(err)
            error = True
        elif float(amount) < 0.0:
            err = "amount to deposit cannon be a negative number: %s" % amount
            self.add_error(err)
            logging.warning("AU0025 deposit is negative: %s", amount)
            error = True

        # test account id
        if self.isint(account_id) == False:
            logging.warning("AU0022 account id is not an int: %s", account_id)
            err = "account id is not a valid number: %s" % account_id
            self.add_error(err)
            error = True
        elif self.__check_account_file(account_id) is False:
            err = "account id is not valid: %s" % account_id
            self.add_error(err)
            logging.warning("AU0064: unknown account number %s", account_id)
            error = True

        # this method returns the new balance and -1 on error
        if error is True:
            return -1

        # call make deposit.
        balance = self.__make_deposit(account_id, amount)
        return balance

    # withdraw case from account
    def withdraw(self, account_id, amount):
        error = False
        self.clear_errors()
        # test args
        if self.isfloat(amount) == False:
            logging.warning("AU0083 withdraw is not a float: %s", amount)
            err = "amount to withdraw is not a valid number: %s" % amount
            self.add_error(err)
            error = True
        elif float(amount) < 0.0:
            logging.warning("AU0088 withdraw is negative: %s", amount)
            err = "amount to withdraw cannon be a negative number: %s" % amount
            self.add_error(err)
            error = True

        # test account id
        if self.isint(account_id) == False:
            logging.warning("AU0094 account id is not an int: %s", account_id)
            err = "account id is not a valid number: %s" % account_id
            self.add_error(err)
            error = True
        elif self.__check_account_file(account_id) is False:
            err = "account id is not valid: %s" % account_id
            self.add_error(err)
            logging.warning("AU0102: unknown account number %s", account_id)
            error = True

        # this method returns the new balance and -1 on error
        if error is True:
            return -1

        # call make deposit.
        balance = self.__make_withdraw(account_id, amount)
        return balance

    # private
    # withdraw case from account. no error checking of args
    # returns -1 on error or balance after withdraw
    # error updates getError
    def __make_withdraw(self, account_id, amount):

        # sets up the filenames
        self.set_account_id(account_id)

        # lock file
        self.lock_file()

        account_info = self.__read_account_info(account_id)
        logging.debug("AU0033 balance for account %s is %s\n", account_id, account_info.balance)
        balance = account_info.balance - amount
        if (balance < 0):
            err = "You can't withdraw more than your balance"
            self.add_error(err)
            logging.warning("AU0119 account %s trying to withdraw %s more than the balance %s",
                            account_id, amount, balance)
            # don't forget to unlock before returning
            self.unlock_file()
            return -1

        content = "%s,%s,%s\n" % (account_info.fname, account_info.lname, balance)
        self.write_content(content)

        #unlock file
        self.unlock_file()

        # write to log after done so if there is a failure we can see the unmatched
        # transaction
        logging.debug("AU0040 new balance for account %s is %s\n", account_id, balance)
        return balance

    # gets the account information. does not use locks
    def get_account_info(self, account_id):
        error = False

        # test account id
        if self.isint(account_id) == False:
            logging.warning("AU0022 account id is not an int: %s", account_id)
            err = "account id is not a valid number: %s" % account_id
            self.add_error(err)
            error = True
        elif self.__check_account_file(account_id) is False:
            err = "account id is not valid: %s" % account_id
            self.add_error(err)
            logging.warning("AU0064: unknown account number %s", account_id)
            error = True

        # this method returns the new balance and -1 on error
        if error is True:
            return None

        return self.__read_account_info(account_id)

    # private function that reads account info without error
    # checks
    def __read_account_info(self, account_id):
        filename = self.__get_account_filename(account_id)
        # read in file
        file = open(filename, 'r')
        file_contents = file.readline()
        file.close()

        vals = file_contents.split(',')
        balance = float(vals[2].strip())
        Account = namedtuple('Account', 'fname lname balance')
        account = Account(vals[0], vals[1], balance)
        return account
