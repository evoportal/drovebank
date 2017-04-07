#!/usr/bin/env python
# -*- mode: python; python-indent-offset: 4; indent-tabs-mode: nil; -*-
#
# unit tests for TransferMoney
#
import unittest
import os
import time
import shutil

from account_actions import AccountActions
from account_create import AccountCreate
from atomic_write import AtomicWrite

class AccountActions_Test(unittest.TestCase):

    # setup
    def setUp(self):

        #unit tests run in the current directory
        self.dir  = os.getcwd()
        # make a test index file.
        fname = 'index.idx'
        self.indexfile = os.path.join(self.dir, fname)

        # write out some stuff
        f = open(self.indexfile, 'w')
        f.write('69\n')
        f.flush()
        f.close()

        # make two accounts both with 100 dollars in them
        ac = AccountCreate(self.dir)

        fname = 'John'
        lname = 'Doe'
        balance = 100.0
        self.one_id = ac.create_account(fname, lname, balance)
        self.one_file = ac.get_account_file()

        fname = 'Bob'
        lname = 'Smith'
        self.two_id = ac.create_account(fname, lname, balance)
        self.two_file = ac.get_account_file()

    def tearDown(self):
        os.remove(self.two_file)
        os.remove(self.one_file)
        os.remove(self.indexfile)

    def test_transfer_money(self):

        aa = AccountActions(self.dir)

        # transfer 50 bucks
        result = aa.transfer_money(self.one_id, self.two_id, 50.00)
        self.assertTrue(result)

        # get the account balances
        one_info = aa.get_account_info(self.one_id)
        two_info = aa.get_account_info(self.two_id)
        self.assertEqual(one_info.balance, 50.00)
        self.assertEqual(two_info.balance, 150.00)

    def __write_data_to_file(self, fname, content):
        f = open(fname, 'w')
        f.write(content)
        f.flush()
        f.close()

    # dies right after lock
    def test_recover_step0(self):

        ffile = '200.txt'
        tfile = '300.txt'
        from_file = os.path.join(self.dir, ffile)
        to_file = os.path.join(self.dir, tfile)

        orig_content = 'original content\n'
        self.__write_data_to_file(from_file, orig_content)
        self.__write_data_to_file(to_file, orig_content)

        from_aw = AtomicWrite(self.dir)
        to_aw = AtomicWrite(self.dir)

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

        aa = AccountActions(self.dir)
        aa.recover_transfer(from_aw.get_lockfilename(), to_aw.get_lockfilename())

        # this should have the old content in both files
        self.__assert_content_equals(from_file, orig_content)
        os.remove(from_file)
        self.__assert_content_equals(to_file, orig_content)
        os.remove(to_file)


    # dies right after step 1
    def test_recover_step1(self):

        ffile = '201.txt'
        tfile = '301.txt'
        from_file = os.path.join(self.dir, ffile)
        to_file = os.path.join(self.dir, tfile)

        orig_content = 'original content\n'
        self.__write_data_to_file(from_file, orig_content)
        self.__write_data_to_file(to_file, orig_content)

        from_aw = AtomicWrite(self.dir)
        to_aw = AtomicWrite(self.dir)

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

        aa = AccountActions(self.dir)
        aa.recover_transfer(from_aw.get_lockfilename(), to_aw.get_lockfilename())

        # this should have the old content in both files
        self.__assert_content_equals(from_file, orig_content)
        os.remove(from_file)
        self.__assert_content_equals(to_file, orig_content)
        os.remove(to_file)

    # dies in the middle of step 3
    def test_recover_step2(self):

        ffile = '202.txt'
        tfile = '302.txt'
        from_file = os.path.join(self.dir, ffile)
        to_file = os.path.join(self.dir, tfile)

        orig_content = 'original content\n'
        self.__write_data_to_file(from_file, orig_content)
        self.__write_data_to_file(to_file, orig_content)

        from_aw = AtomicWrite(self.dir)
        to_aw = AtomicWrite(self.dir)

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


        new_content = 'new content\n'
        self.__write_data_to_file(from_aw.get_tmpfile(), new_content)
        self.__write_data_to_file(to_aw.get_tmpfile(), new_content)

        #step 3 move orig file to old file
        shutil.move(from_file, from_aw.get_oldfile())

        #dies in the middle of step 3
        aa = AccountActions(self.dir)
        aa.recover_transfer(from_aw.get_lockfilename(), to_aw.get_lockfilename())

        # this should have the new content in both files
        self.__assert_content_equals(from_file, new_content)
        os.remove(from_file)
        self.__assert_content_equals(to_file, new_content)
        os.remove(to_file)


    # dies right after step 3
    def test_recover_step3(self):

        ffile = '203.txt'
        tfile = '303.txt'
        from_file = os.path.join(self.dir, ffile)
        to_file = os.path.join(self.dir, tfile)

        orig_content = 'original content\n'
        self.__write_data_to_file(from_file, orig_content)
        self.__write_data_to_file(to_file, orig_content)

        from_aw = AtomicWrite(self.dir)
        to_aw = AtomicWrite(self.dir)

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

        new_content = 'new content\n'
        self.__write_data_to_file(from_aw.get_tmpfile(), new_content)
        self.__write_data_to_file(to_aw.get_tmpfile(), new_content)

        #step 3 move orig file to old file
        shutil.move(from_file, from_aw.get_oldfile())
        shutil.move(to_file, to_aw.get_oldfile())

        #dies after step 3
        aa = AccountActions(self.dir)
        aa.recover_transfer(from_aw.get_lockfilename(), to_aw.get_lockfilename())

        # this should have the new content in both files
        self.__assert_content_equals(from_file, new_content)
        os.remove(from_file)
        self.__assert_content_equals(to_file, new_content)
        os.remove(to_file)


    # dies right after lock
    def test_recover_step4(self):

        ffile = '204.txt'
        tfile = '304.txt'
        from_file = os.path.join(self.dir, ffile)
        to_file = os.path.join(self.dir, tfile)

        orig_content = 'original content\n'
        self.__write_data_to_file(from_file, orig_content)
        self.__write_data_to_file(to_file, orig_content)

        from_aw = AtomicWrite(self.dir)
        to_aw = AtomicWrite(self.dir)

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

        new_content = 'new content\n'
        self.__write_data_to_file(from_aw.get_tmpfile(), new_content)
        self.__write_data_to_file(to_aw.get_tmpfile(), new_content)

        #step 3 move orig file to old file
        shutil.move(from_file, from_aw.get_oldfile())
        shutil.move(to_file, to_aw.get_oldfile())

        # step 4 rename tmp file to orig file
        shutil.move(from_aw.get_tmpfile(), from_file)
        aa = AccountActions(self.dir)
        aa.recover_transfer(from_aw.get_lockfilename(), to_aw.get_lockfilename())

        # this should have the new content in both files
        self.__assert_content_equals(from_file, new_content)
        os.remove(from_file)
        self.__assert_content_equals(to_file, new_content)
        os.remove(to_file)

    # dies right after step 4
    def test_recover_step5(self):

        ffile = '205.txt'
        tfile = '305.txt'
        from_file = os.path.join(self.dir, ffile)
        to_file = os.path.join(self.dir, tfile)

        orig_content = 'original content\n'
        self.__write_data_to_file(from_file, orig_content)
        self.__write_data_to_file(to_file, orig_content)

        from_aw = AtomicWrite(self.dir)
        to_aw = AtomicWrite(self.dir)

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

        new_content = 'new content\n'
        self.__write_data_to_file(from_aw.get_tmpfile(), new_content)
        self.__write_data_to_file(to_aw.get_tmpfile(), new_content)

        #step 3 move orig file to old file
        shutil.move(from_file, from_aw.get_oldfile())
        shutil.move(to_file, to_aw.get_oldfile())

        # step 4 rename tmp file to orig file
        shutil.move(from_aw.get_tmpfile(), from_file)
        shutil.move(to_aw.get_tmpfile(), to_file)

        aa = AccountActions(self.dir)
        aa.recover_transfer(from_aw.get_lockfilename(), to_aw.get_lockfilename())

        # this should have the new content in both files
        self.__assert_content_equals(from_file, new_content)
        os.remove(from_file)
        self.__assert_content_equals(to_file, new_content)
        os.remove(to_file)

    # dies in middle of step 5
    def test_recover_step6(self):

        ffile = '206.txt'
        tfile = '306.txt'
        from_file = os.path.join(self.dir, ffile)
        to_file = os.path.join(self.dir, tfile)

        orig_content = 'original content\n'
        self.__write_data_to_file(from_file, orig_content)
        self.__write_data_to_file(to_file, orig_content)

        from_aw = AtomicWrite(self.dir)
        to_aw = AtomicWrite(self.dir)

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

        new_content = 'new content\n'
        self.__write_data_to_file(from_aw.get_tmpfile(), new_content)
        self.__write_data_to_file(to_aw.get_tmpfile(), new_content)

        #step 3 move orig file to old file
        shutil.move(from_file, from_aw.get_oldfile())
        shutil.move(to_file, to_aw.get_oldfile())

        # step 4 rename tmp file to orig file
        shutil.move(from_aw.get_tmpfile(), from_file)
        shutil.move(to_aw.get_tmpfile(), to_file)

        # step 5 we cant delete the old file now.
        # if it fails it will get cleaned up on recovery
        os.remove(from_aw.get_oldfile())
        aa = AccountActions(self.dir)
        aa.recover_transfer(from_aw.get_lockfilename(), to_aw.get_lockfilename())

        # this should have the new content in both files
        self.__assert_content_equals(from_file, new_content)
        os.remove(from_file)
        self.__assert_content_equals(to_file, new_content)
        os.remove(to_file)

    # that is it for recovery. if it dies after step 5 we are just left with the lock files
    # and the data file. there would be no ID to connect the two lock files
    def __assert_content_equals(self, fname, content):
        file = open(fname, 'r')
        file_content = file.readline()
        file.close()
        self.assertEquals(file_content, content)

if __name__ == '__main__':
    unittest.main()
