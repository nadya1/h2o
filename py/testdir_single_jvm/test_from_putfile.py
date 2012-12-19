import os, json, unittest, time, shutil, sys
sys.path.extend(['.','..'])
import h2o, h2o_cmd
import h2o_hosts
import h2o_browse as h2b
import h2o_import as h2i
import time, random

class Basic(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        h2o.build_cloud(1,java_heap_GB=14)

    @classmethod
    def tearDownClass(cls):
        h2o.tear_down_cloud()

    def test_B_putfile_files(self):
        timeoutSecs = 500

        #    "covtype169x.data",
        #    "covtype.13x.shuffle.data",
        #    "3G_poker_shuffle"
        #    "covtype20x.data", 
        #    "billion_rows.csv.gz",
        csvFilenameAll = [
            "covtype.data",
            "covtype20x.data",
            "covtype200x.data",
            "a5m.csv",
            "a10m.csv",
            "a100m.csv",
            "a200m.csv",
            "a400m.csv",
            "a600m.csv",
            "100million_rows.csv",
            "200million_rows.csv",
            "billion_rows.csv.gz",
            "new-poker-hand.full.311M.txt.gz",
            ]
        # csvFilenameList = random.sample(csvFilenameAll,1)
        csvFilenameList = csvFilenameAll

        # pop open a browser on the cloud
        h2b.browseTheCloud()

        for csvFilename in csvFilenameList:
            csvPathname = h2o.find_file('/home/0xdiag/datasets/' + csvFilename)

            # creates csvFilename and csvFilename.hex  keys
            parseKey = h2o_cmd.parseFile(csvPathname=csvPathname, key=csvFilename, timeoutSecs=500)
            print csvFilename, 'parse TimeMS:', parseKey['TimeMS']
            print "Parse result['Key']:", parseKey['Key']

            # We should be able to see the parse result?
            inspect = h2o_cmd.runInspect(key=parseKey['Key'])

            print "\n" + csvFilename
            start = time.time()
            # poker and the water.UDP.set3(UDP.java) fail issue..
            # constrain depth to 25
            RFview = h2o_cmd.runRFOnly(trees=1,depth=25,parseKey=parseKey,
                timeoutSecs=timeoutSecs)

            h2b.browseJsonHistoryAsUrlLastMatch("RFView")
            # wait in case it recomputes it
            time.sleep(10)

            sys.stdout.write('.')
            sys.stdout.flush() 

if __name__ == '__main__':
    h2o.unit_main()