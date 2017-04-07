# -*- mode: python; python-indent-offset: 4; indent-tabs-mode: nil; -*-
import unittest
import os
from threading import Thread
import time
import shutil

from atomic_write import AtomicWrite

class AtomicWrite_Test(unittest.TestCase):

    # setup
    def setUp(self):
        fname = '100.txt'
        self.dir = os.getcwd()
        self.filename = os.path.join(self.dir, fname)

        # write out some stuff
        f = open(self.filename, 'w')
        f.write('some stuff\n')
        f.flush()
        f.close()

    def tearDown(self):
        if os.path.exists(self.filename):
            os.remove(self.filename)

    def test_idgenerator(self):
        aw = AtomicWrite(self.dir, self.filename)

        id = aw.id_generator()
        idlen = len(id)
        # since it is random all we can check is the length
        self.assertEqual(idlen, 8)

        # test override
        aw.set_transid("AAAAAAAA")
        id = aw.id_generator()
        self.assertEquals(id, 'AAAAAAAA')

    def test_make_tmp_filenames(self):
        aw = AtomicWrite(self.dir, self.filename)
        # called by AtomicWrite.__init__
        #aw.make_tmp_filenames()
        tmplen = len(aw.get_tmpfile())
        outlen = len(aw.get_oldfile())
        self.assertTrue( (tmplen > 0) )
        self.assertTrue( (outlen > 0) )

    # worker thread for the lock test. just
    # locks a file for 3 seconds then unlocks it
    def worker(self, filename, dir):
        aw = AtomicWrite(dir, filename)
        aw.lock_file()
        time.sleep(3)
        aw.unlock_file()
        return

    # test lock function by spinning off a thread
    # which locks the file for 3 seconds then
    # unlocks it. the main thread tries to lock
    # the file. If the file is indeed locked the
    # time elapsed should be more than 3 seconds
    def test_lock_file(self):
        t = Thread(target=self.worker, args=(self.filename,self.dir,))

        start = time.time()
        t.start()

        # make sure the thread has time to lock the file
        time.sleep(1)

        # attempt to lock file in main thread
        aw = AtomicWrite(self.dir, self.filename)
        aw.lock_file()

        end = time.time()
        elapsed = end - start
        aw.unlock_file()
        self.assertTrue( (elapsed > 3.0) )

    def test_atomicwrite(self):
        aw = AtomicWrite(self.dir, self.filename)
        content = 'testing atomic write\n'
        aw.atomicwrite(content)
        file = open(self.filename, 'r')
        file_content = file.readline()
        file.close()
        self.assertEquals(file_content, content)


    # this case is just a lock file and nothing else.
    # this could be a failure just after the lock or
    # just after deleting the .old file. either way
    # the data in the file is correct. you can look
    # in the drovebank.log to see.
    def test_recover_case0(self):
        fname = '100.txt'
        filename = os.path.join(self.dir, fname)

        # write out some stuff
        f = open(filename, 'w')
        f.write('some stuff\n')
        f.flush()
        f.close()

        aw = AtomicWrite(self.dir, filename)

        # lock the file
        aw.lock_file()

        # call recover
        aw.recover_write()

        # make sure all the files are cleaned up
        self.assertFalse(os.path.exists(aw.get_lockfilename()))
        self.assertTrue(os.path.exists(filename))

        # make sure the file content is correct
        file = open(filename, 'r')
        file_content = file.readline()
        file.close()
        self.assertEquals(file_content, 'some stuff\n')
        os.remove(filename)

    # create case 1 failing after step 1
    # making the old file and renaming the
    # tmp file to the filename
    def test_recover_case1(self):
        # new filename. python can run these in paralled and
        # this will lock up the system if it uses the same
        # file as others
        fname = '101.txt'

        filename = os.path.join(self.dir, fname)
        # write out some stuff
        f = open(filename, 'w')
        content = 'some stuff\n'
        f.write(content)
        f.flush()
        f.close()

        aw = AtomicWrite(self.dir, filename)
        tmpfile = aw.get_tmpfile()
        oldfile = aw.get_oldfile()

        # lock the file
        aw.lock_file()

        #step 1 copy old file to tmp file
        shutil.copy2(filename, tmpfile)

        # call recover
        aw.recover_write()

        self.assertFalse(os.path.exists(tmpfile))
        self.assertFalse(os.path.exists(aw.get_lockfilename()))
        self.assertTrue(os.path.exists(filename))

        # make sure the file content is correct
        file = open(filename, 'r')
        file_content = file.readline()
        file.close()
        self.assertEquals(file_content, content)
        os.remove(filename)

    # create case 2 where we failed during or
    # after step 2. since writing is not atomic
    # we can't trust the tmp file and the data
    # file should have original content
    def test_recover_case2(self):
        # new filename. python can run these in paralled and
        # this will lock up the system if it uses the same
        # file as others
        fname = '102.txt'

        filename = os.path.join(self.dir, fname)
        # write out some stuff
        f = open(filename, 'w')
        content = 'some stuff\n'
        f.write(content)
        f.flush()
        f.close()

        aw = AtomicWrite(self.dir, filename)
        tmpfile = aw.get_tmpfile()
        oldfile = aw.get_oldfile()

        # lock the file
        aw.lock_file()

        #step 1 copy old file to tmp file
        shutil.copy2(filename, tmpfile)

        # step 2 write new data to tmpfile
        new_content = 'new content\n'
        f = open(tmpfile, 'w')
        f.write(new_content)
        f.flush()
        f.close()

        # call recover
        aw.recover_write()

        self.assertFalse(os.path.exists(tmpfile))
        self.assertFalse(os.path.exists(aw.get_lockfilename()))
        self.assertTrue(os.path.exists(filename))

        # make sure the file content is correct
        file = open(filename, 'r')
        file_content = file.readline()
        file.close()
        self.assertEquals(file_content, content)
        os.remove(filename)

    # create case 3 where we failed after
    # step 3. since step 3 is a move (an atomic
    # action) we can now trust the tmp file
    # and the content of the data file should
    # be the new content
    def test_recover_case3(self):
        # new filename. python can run these in paralled and
        # this will lock up the system if it uses the same
        # file as others
        fname = '103.txt'

        filename = os.path.join(self.dir, fname)
        # write out some stuff
        f = open(filename, 'w')
        content = 'some stuff\n'
        f.write(content)
        f.flush()
        f.close()

        aw = AtomicWrite(self.dir, filename)
        tmpfile = aw.get_tmpfile()
        oldfile = aw.get_oldfile()

        # lock the file
        aw.lock_file()

        #step 1 copy old file to tmp file
        shutil.copy2(filename, tmpfile)

        # step 2 write new data to tmpfile
        new_content = 'new content\n'
        f = open(tmpfile, 'w')
        f.write(new_content)
        f.flush()
        f.close()

        #step 3 move orig file to old file
        shutil.move(filename, oldfile)

        # call recover
        aw.recover_write()

        self.assertFalse(os.path.exists(oldfile))
        self.assertFalse(os.path.exists(tmpfile))
        self.assertFalse(os.path.exists(aw.get_lockfilename()))
        self.assertTrue(os.path.exists(filename))

        # make sure the file content is correct
        file = open(filename, 'r')
        file_content = file.readline()
        file.close()
        self.assertEquals(file_content, new_content)
        os.remove(filename)

    # create case 4 (last one!) where we failed after
    # step 4. we have been able to trust the tmp file
    # since step 3 so this is just more cleanup
    def test_recover_case4(self):
        # new filename. python can run these in paralled and
        # this will lock up the system if it uses the same
        # file as others
        fname = '104.txt'

        filename = os.path.join(self.dir, fname)
        # write out some stuff
        f = open(filename, 'w')
        content = 'some stuff\n'
        f.write(content)
        f.flush()
        f.close()

        aw = AtomicWrite(self.dir, filename)
        tmpfile = aw.get_tmpfile()
        oldfile = aw.get_oldfile()

        # lock the file
        aw.lock_file()

        #step 1 copy old file to tmp file
        shutil.copy2(filename, tmpfile)

        # step 2 write new data to tmpfile
        new_content = 'new content\n'
        f = open(tmpfile, 'w')
        f.write(new_content)
        f.flush()
        f.close()

        #step 3 move orig file to old file
        shutil.move(filename, oldfile)

        # step 4 rename tmp file to orig file
        shutil.move(tmpfile, filename)

        # call recover
        aw.recover_write()

        self.assertFalse(os.path.exists(oldfile))
        self.assertFalse(os.path.exists(tmpfile))
        self.assertFalse(os.path.exists(aw.get_lockfilename()))
        self.assertTrue(os.path.exists(filename))

        # make sure the file content is correct
        file = open(filename, 'r')
        file_content = file.readline()
        file.close()
        self.assertEquals(file_content, new_content)
        os.remove(filename)

if __name__ == '__main__':
    unittest.main()
