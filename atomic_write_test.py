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
        print "setup"
        fname = 'test.txt'
        self.dir = os.getcwd()
        self.filename = os.path.join(self.dir, fname)

        # write out some stuff
        f = open(self.filename, 'w')
        f.write('some stuff\n')
        # don't forget to flush
        f.flush()
        f.close()

    def tearDown(self):
        print "teardown"
        os.remove(self.filename)

    def test_idgenerator(self):
        print "test id"
        aw = AtomicWrite(self.dir, self.filename)

        id = aw.id_generator()
        idlen = len(id)

        # since it is random all we can check is the length
        self.assertEqual(idlen, 8)

    def test_make_tmp_filenames(self):
        print "test make tmp"
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
        print "done"
        return

    # test lock function by spinning off a thread
    # which locks the file for 3 seconds then
    # unlocks it. the main thread tries to lock
    # the file. If the file is indeed locked the
    # time elapsed should be more than 3 seconds
    def test_lock_file(self):
        print "test lock file"
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
        print "test atomic write"
        aw = AtomicWrite(self.dir, self.filename)
        content = 'testing atomic write\n'
        aw.atomicwrite(content)
        file = open(self.filename, 'r')
        file_content = file.readline()
        file.close()
        self.assertEquals(file_content, content)

    def test_recover_case1(self):

        aw = AtomicWrite(self.dir, self.filename)
        tmpfile = aw.get_tmpfile()
        oldfile = aw.get_oldfile()
        # create case 1 where we failed between
        # making the old file and renaming the
        # tmp file to the filename
        shutil.copy2(self.filename, tmpfile)

        newcontent = 'new content\n'
        f = open(tmpfile, 'w')
        f.write(newcontent)
        f.flush()
        f.close()

        #step 3 move orig file to old file
        shutil.move(self.filename, oldfile)

        lockfile = aw.get_lockfilename()
        # create a lock file
        f = open(lockfile, 'w')
        f.write(newcontent)
        f.close()

        # call recover
        aw.recover()

        # make sure all the files are cleaned up
        self.assertFalse(os.path.exists(oldfile))
        self.assertFalse(os.path.exists(tmpfile))
        self.assertFalse(os.path.exists(lockfile))
        self.assertTrue(os.path.exists(self.filename))

        # make sure the file content is correct
        file = open(self.filename, 'r')
        file_content = file.readline()
        file.close()
        self.assertEquals(file_content, newcontent)

if __name__ == '__main__':
    unittest.main()
