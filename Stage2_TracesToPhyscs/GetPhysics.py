# use numpy for array operations
import numpy as np
# import sys for file and path stuff
import sys
sys.path.append('../Utilities')
# import the util file.
import Utilities as util
# import the plotting utility file
import PlotUtilities as plotUtil
# import cycling..
from itertools import cycle
import matplotlib.pyplot as plt
import scipy.cluster.vq as cluster 
from scipy import interpolate

def convertTimeToIndex(times,frameRate=0.1):
    return np.round(times / frameRate)

def getMinimumTime(values,times,value,lessThanBool=False):
    minimumTimes = -1 * np.ones((len(values),1))
    # the times to interpolate the times. XXX probably 
    # want to make this a constant of some kind.
    numPoints = 1000
    # get the bounds for interpolation
    # get the interpolation grid
    for i,listV in enumerate(values):
        timeRaw = times[i]
        timeGrid = np.linspace(0,np.max(timeRaw),numPoints)
        listTmp = np.interp(timeGrid,timeRaw,listV)
        # need to make sure we start below the lower bound
        # or send above the upper bound
        lessThan =(listTmp <= value)
        greaterThan = (listTmp >= value)        
        if (lessThanBool):
            toTest = lessThan
        else:
            toTest= greaterThan
        # if our condition isn't true for any time,
        # ignore the protein (ie: it wasn't ever less than
        # the lower bound or greater than the upper bound)
        if not np.any(toTest):
            continue
        # look for the lowest squared difference from the desired value.
        diffArr = (listTmp-value)**2
        firstIndex = np.argmin(diffArr)
        # get the best interpolated time.
        bestTime = timeGrid[firstIndex]
        minimumTimes[i] = bestTime
    return minimumTimes

def getDifferentialTime(valuesBefore,valuesAfter):
    # returns when we have a well-defined unfolding...
    numVals = len(valuesBefore)
    indices=  []
    diffTime = []
    for i in range(numVals):
        first = valuesBefore[i]
        second = valuesAfter[i]
        if (first < 0 or second < 0):
            continue
        if (first >= second):
            continue
        # POST: non negative, values 'match'
        indices.append(i)
        # append the proper diff time
        diffTime.append(second-first)
    return diffTime,indices

def getDistances(goodFRET,goodTimes):
    # goodFRET is defined by the API as the FRET ratio from GetTraces.
    # This essentially means it has been corrected for objects which have
    # ill-defined trajectories or difusion coeffs
    # RETURNS: the 'good' distances and time found, as well as the indexing array
    distances = []
    times = []
    indices = []
    nodeIndices = []
    count = 0
    for t,FRET in zip(goodTimes,goodFRET):
        # this is the trace, FRET, and diff for each protein
        # force some reason we have negative data? (Figure this out)
        # XXX make the ugly where thing into a find.
        # XXX figure out how to fix this..
        goodIndices = np.where(FRET > 0)[0]
        if ((len(goodIndices) == 0) or 
            (min(goodIndices) == max(goodIndices))):
            indices.append([])
            continue
        betterFRET = FRET[goodIndices]
        betterTime = t[goodIndices]
        betterTime -= np.min(betterTime)
        distanceValues = betterFRET**(1/6)
        distances.append(np.array(distanceValues))
        indices.append(np.array(goodIndices))
        times.append(np.array(betterTime))
        nodeIndices.append(count)
        count += 1
    return np.array(distances),np.array(times),np.array(indices),np.array(nodeIndices)


def GetPhysicsMain(goodTimes,goodFRET,goodDiff):
    source = 'Step2::GetPhysics'
    util.ReportMessage("Starting",source)
    colors = ['r','g','b','k','m','c','y','0.33','0.66']
    colorCycle = cycle(colors)
    count = 0
    fig = plotUtil.pFigure()
    # XXXfill all these in! based on video size
    frameRate = 0.1
    maxNumTimes = 30*10
    distances,times,definedDistancesIdx,nodeIdx =getDistances(goodFRET,goodTimes)
    # get just the 'nodes' with valid valued.
    # flatten the distances to get a notion of the 'all time'
    # distance information. We can use this and kmeans to find a 'folded
    # and unfolded sttae
    flattenDistances = np.concatenate(distances)
    # use two clusters; folded and unfolded
    numClusters = 2
    # lots of iterations (this number seems to work well; the 'smooth'
    # running time / convergence (?) of kmeans is polynomial
    # http://en.wikipedia.org/wiki/K-means_clustering
    numIters = int(1e3)
    clusters,ignore = cluster.kmeans(flattenDistances,numClusters,iter=numIters)
    # the clusters give us the 'folded' and 'unfolded' groups. between those, we have
    # a fairly undefined state.
    folded = min(clusters)
    unfolded = max(clusters)
    clusters = [unfolded,folded]
    
    folded = getMinimumTime(distances,times,folded,False)
    unfolded = getMinimumTime(distances,times,unfolded,True)
    diffTime, definedUnfoldingIdx = getDifferentialTime(folded,unfolded)

    goodDiff = util.takeSubset(goodDiff,
                                [nodeIdx,definedUnfoldingIdx])

    plt.xscale('log', nonposy='clip')
    plt.xlabel('Time since protein (seconds)')
    plt.ylabel('FRET d distance (arb)')
    fig = plotUtil.pFigure()
    numPlots = 2
    plotCount = 1
    fretLabel = 'FRET d Distance (arb)'
    ax = plt.subplot(numPlots,1,plotCount)
    plotUtil.histogramPlot(ax,fretLabel,'# Proteins',
                           'FRET Distance histogram',flattenDistances,
                           len(flattenDistances)/100,True,True)
    # plot guiding lines for the two clusters we found
    normalClusters = plotUtil.normalizeTo(flattenDistances,clusters)
    plt.axvline(normalClusters[0])
    plt.axvline(normalClusters[1])
    
    plotCount += 1
    ax = plt.subplot(numPlots,1,plotCount)
    plotUtil.histogramPlot(ax,'Unfolding time distribution','# Proteins',
                           'Unfolding time (seconds) ',diffTime,
                           len(diffTime)/100,True,True)


    plotUtil.saveFigure(fig,'tmp2')
    # return the good unfolding times and differential coefficients
    return diffTime,goodDiff

    
