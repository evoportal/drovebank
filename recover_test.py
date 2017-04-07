# -*- mode: python; python-indent-offset: 4; indent-tabs-mode: nil; -*-
import unittest
import os
import time

from recover import Recover

class AccountCreate_Test(unittest.TestCase):

    # setup
    def setUp(self):
        #unit tests run in the current directory
        self.dir  = os.getcwd()

        self.filelist = []

        # two xtmps
        self.filelist.append("1_AAAAAAAA.txt.xtmp")
        self.filelist.append("2_AAAAAAAA.txt.xtmp")

        # one xold and one xtmp
        self.filelist.append("2000_AAAAAAAB.txt.xtmp")
        self.filelist.append("20_AAAAAAAB.txt.xold")

        # two xold and two xtmp
        self.filelist.append("22_AAAAAAAC.txt.xtmp")
        self.filelist.append("23_AAAAAAAC.txt.xtmp")
        self.filelist.append("22_AAAAAAAC.txt.xold")
        self.filelist.append("23_AAAAAAAC.txt.xold")

        # one xold
        self.filelist.append("230000_DAAAAAAC.txt.xold")

        for fname in self.filelist:
            filename = os.path.join(self.dir, fname)
            self.__write_data_to_file(filename, 'wa\n')

    def tearDown(self):
        for fname in self.filelist:
            filename = os.path.join(self.dir, fname)
            os.remove(filename)

    def __write_data_to_file(self, fname, content):
        f = open(fname, 'w')
        f.write(content)
        f.flush()
        f.close()

    def test_find_pairs(self):
        r = Recover(self.dir)
        pair_hash = r.find_pairs()
        plen = len(pair_hash)
        self.assertEqual(plen, 4)
        pset = pair_hash['AAAAAAAA']
        self.assertEqual(len(pset), 2)
        listp = list(pset)
        id1 = listp[0]
        id2 = listp[1]

        # not sure how random the ordering is. so
        # don't rely on order
        self.assertTrue( (id1 != id2) )
        self.assertTrue( (id1 == 1 or id1 == 2) )
        self.assertTrue( (id2 == 1 or id2 == 2) )

        # make sure we found the lone one
        pset = pair_hash['DAAAAAAC']
        self.assertEqual(len(pset), 1)

        # make sure no one has more than 2
        for transid, pset in pair_hash.iteritems():
            self.assertTrue( (len(pset) < 3) )

if __name__ == '__main__':
    unittest.main()
