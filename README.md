# drovebank

- I use the anaconda python distro: https://www.continuum.io/downloads and haven't made the leap to 3.0 yet, so this code was developed on 2.7. It should work on the normal python distro.

- Design
  - the data store is one file per user, name format is ${USER_ID}.txt
  - inside the data file a single csv line: fname,lname,balance
  - using a lock file and the assumption that moves are atomic on your
    filesystem (they are on unix local filesystem) you can update
    the file using temporary files to ensure if the machine fails at
    any point in the code the system will recover. To view the
    process in detail I would look in the atomic_write_test.py unit
    test file. It has a test case for each possible failure point
  - you can run any number of drovebank.py processes on the box and
    as long as the user has write acccess to the data dir it will work.
  - using HDFS you could scale this to a very large number of users. From
    the HDFS webpage https://hadoop.apache.org/docs/stable/hadoop-project-dist/hadoop-common/filesystem/introduction.html#Core_Expectations_of_a_Hadoop_Compatible_FileSystem create and rename are atomic. For very large number of files
    I would move from one directory to nested based on the account id. i.e.
    account id 1 would be in 00/00/00/01.txt and
    account id 1001 would be in 00/00/10/01.txt and so on. Obviously the UI
    would need to change, needing paging of the account list and a search
    function

Running
   - First you need to create a data directory. There is one hardcoded in
     drove_bank_constants.py, you can change that or both applications can
     take the directory on the command line
   - To run the app just go ./drovebank.py (-d /path/to/datadir) there is
     help in the application
   - if the server has crashed, or a client process stopped in the middle
     of accessing the data files you can recover by running
     ./recover.py (-d /path/to/datadir)
   - you can run any unittest indiviually by just going python my_test.py or
     there is a shell script that runs them all

Stuff
   - it would be easy to have a transaction history in the csv file instead of
     just the last value
   - right now locks can deadlock, then you have to ctrl-c and run the
     recover.pl file. It would be nicer to have that throw and then
     catch it at the app level, write a /path/to/datadir/pain file.
     The client then can look for the pain file before each request for
     input, if it sees it the client tells the user the db is corrupted and
     exits. Then the sysadmin can run the recover. This way if the
     db store goes bad all the clients are notified and exit.
     