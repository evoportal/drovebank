# -*- mode: python; python-indent-offset: 4; indent-tabs-mode: nil; -*-
import unittest
import os
import time

from account_create import AccountCreate

class AccountCreate_Test(unittest.TestCase):

    # setup
    def setUp(self):
        # make a test index file.
        fname = 'index.idx'
        self.dir  = os.getcwd()
        self.filename = os.path.join(self.dir, fname)

        # write out some stuff
        f = open(self.filename, 'w')
        f.write('69\n')
        # don't forget to flush
        f.flush()
        f.close()


    def tearDown(self):
        os.remove(self.filename)

    def test_get_account_number(self):
        ac = AccountCreate(self.dir)
        account_num = ac.get_account_number();
        # should be 70
        self.assertEqual(account_num, 70)

    def test_create_account(self):
        ac = AccountCreate(self.dir)

        fname = 'John'
        lname = 'Doe'
        balance = 100.0
        id = ac.create_account(fname, lname, balance)
        # should be 70
        self.assertEqual(id, 70)

        balance = -100.0
        id = ac.create_account(fname, lname, balance)
        # should be -1 because of negative account balance
        self.assertEqual(id, -1)

        balance = 'apricot'
        id = ac.create_account(fname, lname, balance)
        # should be -1 because of bad input
        self.assertEqual(id, -1)

if __name__ == '__main__':
    unittest.main()
