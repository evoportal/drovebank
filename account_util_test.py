#!/usr/bin/env python
# -*- mode: python; python-indent-offset: 4; indent-tabs-mode: nil; -*-
#
# unit tests for AccountUtil
#
import unittest
import os
import time

from account_util import AccountUtil
from account_create import AccountCreate

class AccountUtil_Test(unittest.TestCase):

    # setup
    def setUp(self):
        fname = "index.txt"
        self.dir  = os.getcwd()
        self.indexname = os.path.join(self.dir, fname)
        # name the account will create
        self.fname = os.path.join(self.dir, "70.txt")
        # write and index file so we can create an account.
        f = open(self.indexname, 'w')
        f.write('69\n')
        f.close()

        # make an account with 100 dollars in it
        ac = AccountCreate(self.dir)

        fname = 'John'
        lname = 'Doe'
        balance = 100.0
        id = ac.create_account(fname, lname, balance)

    def tearDown(self):
        os.remove(self.indexname)
        if (os.path.exists(self.fname)):
            os.remove(self.fname)

    def test_get_account_info(self):
        au = AccountUtil(self.dir)
        account_info = au.get_account_info(70);
        self.assertTrue( (account_info is not None) )
        self.assertEqual(account_info.fname, "John")
        self.assertEqual(account_info.lname, "Doe")
        self.assertEqual(account_info.balance, 100.00)

    def test_withdraw(self):
        au = AccountUtil(self.dir)

        # test bad args
        balance = au.withdraw(100, "shinyobject")
        self.assertEqual(balance, -1)

        # test withdraw more then in account
        balance = au.withdraw(70, 200.00)
        self.assertEqual(balance, -1)

        # test withdraw negative number
        balance = au.withdraw(70, -1.00)
        self.assertEqual(balance, -1)

        # test withdraw of 50 bucks
        balance = au.withdraw(70, 50.00)
        self.assertEqual(balance, 50.00)

    def test_deposit(self):
        au = AccountUtil(self.dir)

        # test bad args
        balance = au.deposit(100, "shinyobject")
        self.assertEqual(balance, -1)

        # test deposit negative number
        balance = au.deposit(70, -1.00)
        self.assertEqual(balance, -1)

        # test deposit of 500 bucks
        balance = au.deposit(70, 500.00)
        self.assertEqual(balance, 600.00)

if __name__ == '__main__':
    unittest.main()
