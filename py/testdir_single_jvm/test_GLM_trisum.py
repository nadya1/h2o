import unittest
import random, sys, time, os
sys.path.extend(['.','..','py'])

import h2o, h2o_cmd, h2o_hosts, h2o_browse as h2b, h2o_import as h2i, h2o_glm

class Basic(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        global SEED
        SEED = random.randint(0, sys.maxint)

        # SEED = 
        random.seed(SEED)
        print "\nUsing random seed:", SEED
        global local_host
        local_host = not 'hosts' in os.getcwd()
        if (local_host):
            h2o.build_cloud(1,java_heap_GB=28)
        else:
            h2o_hosts.build_cloud_with_hosts()

    @classmethod
    def tearDownClass(cls):
        ### time.sleep(3600)
        h2o.tear_down_cloud()

    def test_many_cols_with_syn(self):
        if h2o.new_json:
            paramDict = {
                # 'key': ['cA'],
                # 'y': [11],
                'family': ['binomial'],
                # 'norm': ['ELASTIC'],
                'norm': ['L2'],
                'lambda_1': [1.0E-5],
                'lambda_2': [1.0E-8],
                'alpha': [1.0],
                'rho': [0.01],
                'max_iter': [50],
                'weight': [1.0],
                'threshold': [0.5],
                # 'case': [NaN],
                'case': ['NaN'],
                # 'link': [familyDefault],
                'xval': [1],
                'expand_cat': [1],
                'beta_eps': [1.0E-4],
                }
        else: 
            paramDict = {
                # 'key': ['cA'],
                # 'Y': [11],
                'family': ['binomial'],
                # 'norm': ['ELASTIC'],
                'norm': ['L2'],
                'lambda_1': [1.0E-5],
                'lambda_2': [1.0E-8],
                'alpha': [1.0],
                'rho': [0.01],
                'max_iter': [50],
                'weight': [1.0],
                'threshold': [0.5],
                # 'case': [NaN],
                'case': [None],
                # 'link': [familyDefault],
                'xval': [1],
                'expand_cat': [1],
                'beta_eps': [1.0E-4],
                }
        ### h2b.browseTheCloud()

        csvFilename = "logreg_trisum_int_cat_10000x10.csv"
        csvPathname = "smalldata/logreg/" + csvFilename
        key2 = csvFilename = ".hex"

        parseKey = h2o_cmd.parseFile(None, h2o.find_file(csvPathname), key2=key2, timeoutSecs=10)
        print csvFilename, 'parse time:', parseKey['response']['time']
        print "Parse result['destination_key']:", parseKey['destination_key']

        # We should be able to see the parse result?
        inspect = h2o_cmd.runInspect(None, parseKey['destination_key'])
        print "\n" + csvFilename

        paramDict2 = {}
        for k in paramDict:
            # sometimes we have a list to pick from in the value. now it's just list of 1.
            paramDict2[k] = paramDict[k][0]

        Y = 10
        # FIX! what should we have for case? 1 should be okay because we have 1's in output col
        kwargs = {'Y': Y, 'max_iter': 30, 'case': 'NaN'}
        kwargs.update(paramDict2)

        start = time.time()
        glm = h2o_cmd.runGLMOnly(parseKey=parseKey, timeoutSecs=20, **kwargs)
        print "glm end on ", csvPathname, 'took', time.time() - start, 'seconds'
        h2o_glm.simpleCheckGLM(self, glm, 8, **kwargs)

        if not h2o.browse_disable:
            h2b.browseJsonHistoryAsUrlLastMatch("Inspect")
            time.sleep(5)

if __name__ == '__main__':
    h2o.unit_main()
