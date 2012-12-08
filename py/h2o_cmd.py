import os, json, unittest, time, shutil, sys
import h2o
import h2o_browse as h2b

def parseFile(node=None, csvPathname=None, key=None, timeoutSecs=20):
    if not csvPathname: raise Exception('No file name specified')
    if not node: node = h2o.nodes[0]
    put = node.put_file(csvPathname, key=key)
    return node.parse(put['key'], put['key']+'.hex', timeoutSecs)

# don't need X..H2O default is okay (all X), but can pass it as kwargs
def runGLM(node=None,csvPathname=None,
        timeoutSecs=20,retryDelaySecs=2,**kwargs):
    parseKey = parseFile(node, csvPathname)
    glm = runGLMOnly(node, parseKey, timeoutSecs, retryDelaySecs,**kwargs)
    return glm

# don't need X..H2O default is okay (all X), but can pass it as kwargs
def runGLMOnly(node=None,parseKey=None,
        timeoutSecs=20,retryDelaySecs=2,**kwargs):
    if not parseKey: raise Exception('No file name for GLM specified')
    if not node: node = h2o.nodes[0]
    # FIX! add something like stabilize in RF
    # we currently don't use the retryDelaySecs
    return node.GLM(parseKey['Key'], timeoutSecs, **kwargs)

# You can change those on the URL line woth "&colA=77&colB=99"
# LinReg draws a line from a collection of points.  Only works if you have 2 or more points.
# will get NaNs if A/B is just one point.

# colA, colB? (kwargs?)
def runLR(node=None, csvPathname=None, timeoutSecs=20, **kwargs):
    parseKey = parseFile(node, csvPathname)
    return runLROnly(node, parseKey, timeoutSecs, **kwargs)

def runLROnly(node=None, parseKey=None, timeoutSecs=20, **kwargs):
    if not parseKey: raise Exception('No file name for LR specified')
    if not node: node = h2o.nodes[0]
    # FIX! add something like stabilize in RF to check results, and also retry/timeout
    return node.linear_reg(parseKey['Key'], timeoutSecs, **kwargs)

# there are more RF parameters in **kwargs. see h2o.py
def runRF(node=None, csvPathname=None, trees=5, 
        timeoutSecs=20, retryDelaySecs=2, **kwargs):
    parseKey = parseFile(node, csvPathname)
    return runRFOnly(node, parseKey, trees, timeoutSecs, retryDelaySecs, **kwargs)

# there are more RF parameters in **kwargs. see h2o.py
def runRFOnly(node=None, parseKey=None, trees=5,
        timeoutSecs=20, retryDelaySecs=2, **kwargs):
    if not parseKey: raise Exception('No parsed key for RF specified')
    if not node: node = h2o.nodes[0]
    #! FIX! what else is in parseKey that we should check?
    h2o.verboseprint("runRFOnly parseKey:", parseKey)
    Key = parseKey['Key']
    rf = node.random_forest(Key, trees, timeoutSecs, **kwargs)

    # if we have something in Error, print it!
    # FIX! have to figure out unexpected vs expected errors
    # {u'Error': u'Only integer or enum columns can be classes!'}

    # FIX! right now, the json doesn't always return the same dict keys
    # so have to look to see if Error is present
    if 'Error' in rf:
        if rf['Error'] is not None:
            print "Unexpected Error key/value in rf result:", rf

    # FIX! check all of these somehow?
    dataKey  = rf['dataKey']
    # if we modelKey was given to rf via **kwargs, remove it, since we're passing 
    # modelKey from rf. can't pass it in two places. (ok if it doesn't exist in kwargs)
    kwargs.pop('modelKey',None)
    modelKey = rf['modelKey']

    # same thing. if we use random param generation and have ntree in kwargs, get rid of it.
    kwargs.pop('ntree',None)
    ntree    = rf['ntree']

    # /ip:port of cloud (can't use h2o name)
    rfCloud = rf['h2o']
    # output class?
    rfClass= rf['class']

    # expect response to match the number of trees you asked for
    # FIX! I guess extra kwargs to RFView shouldn't hurt it??
    def test(n):
        # Only passing browse to this guy (and at the end)
        rfView = n.random_forest_view(dataKey, modelKey, ntree, timeoutSecs, **kwargs)
        modelSize = rfView['modelSize']
        if (modelSize!=trees and modelSize>0):
            # don't print the typical case of 0 (starting)
            print "Waiting for RF done: at %d of %d trees" % (modelSize, ntree)
        return modelSize==ntree

    node.stabilize(
            test,
            'random forest reporting %d trees' % ntree,
            timeoutSecs=timeoutSecs, retryDelaySecs=retryDelaySecs)

    # kind of wasteful re-read, but maybe good for testing
    rfView = node.random_forest_view(dataKey, modelKey, ntree, timeoutSecs, **kwargs)
    modelSize = rfView['modelSize']
    confusionKey = rfView['confusionKey']

    # FIX! how am I supposed to verify results, or get results/
    # touch all these just to do something
    cmInspect = node.inspect(confusionKey)
    modelInspect = node.inspect(modelKey)
    dataInspect = node.inspect(dataKey)

    return rfView
