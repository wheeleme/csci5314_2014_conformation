# use OS for file IO and the like
import os
# use numpy for array operations
import numpy as np
# Use CSV for writing human readable files
import csv


class outputHelper:
    globalOutput = "../output"
    def __init__(self):
        self.Trial = "No Trial"
        self.fil = "No File" 
        self.st = "No Step"
    def setTrial(self,Trial):
        self.trial = Trial
    def setFile(self,File):
        self.fil = File
    def setStep(self,step):
        self.st = step
    def getOutputDir(self,path, fileName = ""):
        # path is a list of paths
        if (fileName == -1):
            fileName = self.st
        tmpPath = [ [self.trial, self.fil],path[:]]
        sepPath =np.concatenate(tmpPath)
        path = ensurePathExists(outputHelper.globalOutput,
                                sepPath)
        return path+fileName

globalIO = outputHelper()

def loadAll(folder,files):
    arr = []
    # loop through all the desired files and load them if we need them.
    for f in files:
        path = folder + f
        if (not os.path.isfile(path)):
            Utilities.ReportError(True,"In Utilities::loadAll, couldn't find " +
                                  path)
        # POST: path is to a valid filename
        arr.append(np.load(path))
    return arr

def takeSubset(original,indices):
    toReturn= original
    for arr in indices:
        toReturn = np.take(toReturn,arr)
    return toReturn

def ReportError(isFatal=False, description="None Given",source="-1"):
    ReportMessage("Error [" + description +"]",source)
    if (isFatal):
        print("\tError was fatal. Exiting.")
        exit(-1)

def ReportMessage(description="None Given",source="-1"):
    if (source == "-1"):
        source = globalIO.st
    print("Message [" + str(description) + "] Received by [" 
          + str(source) + "]")

def dirExists(directory):
    return os.path.exists(directory)

def ensureDirExists(directory):
    # make the directory if it isn't there!
    if not dirExists(directory):
        os.makedirs(directory)

def ensurePathExists(globalOutput,subPaths):
    ensureDirExists(globalOutput)
    path = globalOutput
    for nextPath in subPaths:
        path += '/' + nextPath
        ensureDirExists(path)
    return path + '/'

def normalize(arr,minV=-1,maxV=-1):
    if (minV < 0):
        minV = min(arr)
    if (maxV < 0):
        maxV = max(arr)
    return (arr-minV)/(maxV-minV)

def humanReadableSave(listToSave,fileName,header):
    # if opening a file object, use newline ='' , according to:
    # https://docs.python.org/3/library/csv.html#id2
    with open(fileName + ".csv","w",newline='') as f:
        writeObj = csv.writer(f)
        # XXX move this? right now, try and catch. prolly should just
        # check if the first element is a list.
        try:
            writeObj.writerows(listToSave)
        except csv.Error as e:
            ReportMessage(str(e) + ",probably just writing a single-element list. no worries."
                    ,"Utility::humanReadableSave")
            writeObj.writerow(listToSave)

def saveAll(matricesToSave,labels,thisPath):
    # matricesToSave: a list of N matrices to save
    # labels: a list of labels to put in the headers of the matrices
    # global output: a single, global output folder
    # thispath: a list of N strings giving sub-folders under the global output 
    path = globalIO.getOutputDir(thisPath)
    for i,mat in enumerate(matricesToSave):
        fName = path + labels[i]
        np.save(fName,mat)
        humanReadableSave(mat,fName,labels[i])
        # XXX: probably want somethng like this 
        # http://stackoverflow.com/questions/14037540/writing-a-python-list-of-lists-to-a-csv-file

def saveAllAtIndices(matricesToSave,labels,thisPath,indices):
    endMatrices = []
    for i,m in enumerate(matricesToSave):
        tmpArr = np.array(m)[indices]
        endMatrices.append(tmpArr)
    saveAll(endMatrices,labels,thisPath)
    return endMatrices






    
