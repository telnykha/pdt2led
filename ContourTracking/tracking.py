# -*- coding: utf-8 -*-
import cv2 as cv
import os
import numpy as np
from pyqtgraph import FileDialog
import pyqtgraph
import time
from constants import *
from markupTool import markupSeries
from loadPictures import getPictsByNumber, getDirectoryFromFullPictName, getPictNumber
from MSE import getContourMSE, getIntensityMSE

ktrackType = 1
kwinSize = (30, 30)
kdelta = 30
kptsPartStay = 0.5
kmaxLevel = 6

# WRAPPER
def getInputInfo(fromBegin=False):
    app = pyqtgraph.GraphicsWindow().setBackground(None)
    begin = 1
    if fromBegin is False:
        filename = FileDialog().getOpenFileName(parent=app, caption='Choose the first series file',
                                                filter="*_740.tiff").toUtf8()
        filename = ''.join([l if not l == '/' else '\\' for l in filename])
        begin = getPictNumber(filename, 740)
        fullName = filename[:-10 - len(str(begin))]
        numOfPictures = int(FileDialog().getOpenFileName(parent=app,
                                                         caption='Choose the last series file',
                                                         filter="*_740.tiff").toUtf8()[len(fullName)+1:-9])
    else:
        filename = FileDialog().getOpenFileName(parent=app, caption='Choose the last series file',
                                                filter="*_740.tiff").toUtf8()
        filename = ''.join([l if not l == '/' else '\\' for l in filename])
        numOfPictures = getPictNumber(filename, 740)
        fullName = filename[:-10 - len(str(numOfPictures))]
    direc = getDirectoryFromFullPictName(fullName)
    return fullName, direc, begin, numOfPictures

# pict = cutHighIntensityPoints()
# WRAPPER
def cutHighIntensityPoints(pict, start):
    m, pict = cv.threshold(pict, start, maxIntensity, cv.THRESH_TOZERO_INV)
    return pict

# WRAPPER
def getQuantityHighIntensityPixels(pict):
    return np.sum(cv.calcHist([pict], [0], None, [maxIntensity + 1], [minIntensity, maxIntensity+1])[numHighIntensity:])

#pictThreshed = thresholdOtsu()
# WRAPPER
def thresholdOtsu(pict):
    m, pictThreshed = cv.threshold(pict, minIntensity, maxIntensity, cv.THRESH_BINARY | cv.THRESH_OTSU)
    print m
    return pictThreshed

# WRAPPER
def trackContourPyrLK(pictPrev, pictNext, ptsPrev, winSize, maxLevel):
    criteria = (cv.TERM_CRITERIA_EPS | cv.TERM_CRITERIA_COUNT, 10, 0.03)
    ptsTracked, _, _ = cv.calcOpticalFlowPyrLK(pictPrev, pictNext, #ptsPrev,
                                               #np.float32([tr[-1] for tr in ptsPrev]).reshape(-1, 1, 2),
                                               ptsPrev.reshape(-1, 1, 2), None,
                                               winSize=winSize, maxLevel=maxLevel,
                                               criteria=criteria)

    return ptsTracked


def get740picts(name, begin, end):
    return getPictsByNumber(name, begin, end, wl=740)

# cont = tr2p()
def trackOneStep(pictPrev, ptsPrev, pictNext, winSize, maxLevel, delta):
    ptsNext = trackContourPyrLK(pictPrev, pictNext, ptsPrev, winSize, maxLevel)
    ptsTrackedBack = trackContourPyrLK(pictNext, pictPrev, ptsNext, winSize, maxLevel)

    m, diff = cv.threshold(np.array([[(i ** 2 + j ** 2) ** (1 / 2.)]
                    for [i, j] in abs(ptsPrev - ptsTrackedBack).reshape(-1,2)]).astype(np.float32),
                           delta, 1, cv.THRESH_BINARY_INV)
    return np.around([i for (i, j) in zip(ptsNext.reshape(-1, 2), diff)
                      if j]).astype(np.int32).reshape((-1, 1, 2))


def trackOneStepMeanShift(pictPrev, ptsPrev, pictNext, winSize, maxLevel, delta, ptsPartStay):
    ptsNext = trackContourPyrLK(pictPrev, pictNext, ptsPrev, winSize, maxLevel)

    ptsTrackedBack = trackContourPyrLK(pictNext, pictPrev, ptsNext, winSize, maxLevel)
    m, mask = cv.threshold(np.array([[(i ** 2 + j ** 2) ** (1 / 2.)]
            for [i, j] in abs(ptsPrev - ptsTrackedBack).reshape(-1, 2)]).astype(np.float32),
                           delta, 1, cv.THRESH_BINARY_INV)
    if np.sum(mask) >= ptsPartStay * ptsPrev.shape[0] :  # everything OK, go to usual loop, null counters
        diff = np.array([i - j for (i, j, k) in zip(ptsNext.reshape(-1, 2), ptsPrev.reshape(-1, 2), mask) if k])
        numPoints = diff.shape[0]
        shift = [np.sum(diff[:, 0]) / numPoints, np.sum(diff[:, 1]) / numPoints]
        return shift
    else:
        return None


def trackSeriesCompare740(winSize, maxLevel, delta, ptsPartStay, trackType):
    name, direc, begin, end = getInputInfo(True)
    vctPicts = get740picts(name, begin, end)
    vctPictsToShow = [(p * (maxIntensity / max(np.max(p), 1).astype(np.float32))).astype(np.uint8)
                      for p in vctPicts]
    if not os.access(direc + '\\' + 'cont' + str(0) + '.npy', os.F_OK):
        markupSeries(name, direc, end - begin)
    contPrev = np.load(direc + '\\' + 'cont' + str(0) + '.npy')
    vctMSE = []

    numBadPictures = 0
    t1 = time.time()
    for i in range(1, len(vctPictsToShow)):
        print('frame: ' + str(i + 1))
        contNext = []
        if trackType is 0:
            contNext = trackOneStep(vctPictsToShow[i - numBadPictures - 1],
                                    contPrev, vctPictsToShow[i],
                                    winSize, maxLevel, delta)
            if contNext.shape[0] >= contPrev.shape[0] * ptsPartStay:  # everything OK, go to usual loop, null counters
                contPrev = contNext
                numBadPictures = 0
            else:  # bad picture, passing
                contNext = np.array([[[0, 0]]])
                numBadPictures = numBadPictures + 1
        elif trackType is 1:
            shift = trackOneStepMeanShift(vctPictsToShow[i - numBadPictures - 1],
                                          contPrev, vctPictsToShow[i], winSize, maxLevel, delta, ptsPartStay)
            if shift is not None:  # everything OK, go to usual loop, null counters
                contNext = (contPrev + shift)
                numBadPictures = 0
            else:  # bad picture, passing
                contNext = np.array([[[0, 0]]])
                numBadPictures = numBadPictures + 1

        if (i % frequency) == 0:
            contManual = np.load(direc + '\\' + 'cont' + str(i / frequency) + '.npy')
            MSE = getContourMSE(contManual, contNext, vctPictsToShow[i].shape)
            print(MSE)
            vctMSE.append(MSE)
    t2 = time.time()
    vctMSE.append(t2 - t1)
    np.save(direc + '\\' + 'MSE_' + str(trackType) + '_' + str(winSize) + '_' + str(delta) + '_' + str(maxLevel)
            + '.npy', np.array(vctMSE))


if __name__ == '__main__':

    trackSeriesCompare740(kwinSize, kmaxLevel, kdelta, kptsPartStay, ktrackType)
