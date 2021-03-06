# -*- coding: utf-8 -*-
from markupTool import *
import os
import cv2 as cv
import numpy as np
from pyqtgraph import FileDialog
import pyqtgraph

BTN_ESC = 27
BTN_CTRL_C = 3
CLR_RED = (0, 0, 255)
CLR_GREEN = (0, 255, 0)
minIntensity = 0
maxIntensity = 255.
maxAllowedIntensity = 252
numHighIntensity = 230
maxAllowedNumberHighIntensityPixels = 30
frequency = 3

KernelSize = 13
trackType = 1
winSize = (30, 30)
delta = 30
maxLevel = 6



# WRAPPER
def inputImages(fromBegin=False):
    app = pyqtgraph.GraphicsWindow().setBackground(None)
    begin = 1
    if fromBegin is False:
        filename = FileDialog().getOpenFileName(parent=app, caption='Choose the first series file',
                                                filter="*_740.tiff").toUtf8()
        filename = ''.join([l if not l == '/' else '\\' for l in filename])
        begin = ''
        for l in filename[-10::-1]:
            if l == '_':
                break
            begin += l
        fullname = filename[:-10 - len(begin)]
        begin = int(begin[::-1])
        numOfPictures = int(FileDialog().getOpenFileName(parent=app,
                                                         caption='Choose the last series file',
                                                         filter="*_740.tiff").toUtf8()[len(fullname)+1:-9])
    else:
        filename = FileDialog().getOpenFileName(parent=app, caption='Choose the last series file',
                                                filter="*_740.tiff").toUtf8()
        filename = ''.join([l if not l == '/' else '\\' for l in filename])
        numOfPictures = ''
        for l in filename[-10::-1]:
            if l == '_':
                break
            numOfPictures += l
        fullname = filename[:-10 - len(numOfPictures)]
        numOfPictures = int(numOfPictures[::-1])
    directory = fullname[:]
    for l in fullname[::-1]:
        if l == '\\':
            break
        directory = directory[:-1]
    return fullname, directory, begin, numOfPictures


# pict = cutHighIntensityPoints()
# WRAPPER
def cutHighIntensityPoints(pict, start):
    m, pict = cv.threshold(pict, start, maxIntensity, cv.THRESH_TOZERO_INV)
    return pict


#pictThreshed = thresholdOtsu()
# WRAPPER
def thresholdOtsu(pict):
    m, pictThreshed = cv.threshold(pict, minIntensity, maxIntensity, cv.THRESH_BINARY | cv.THRESH_OTSU)
    print m
    return pictThreshed


# WRAPPER
def getPictTrue(name, i, wl):
    pictFluo = cv.imread(name + '_' + str(i) + '_' + str(wl) + '.tiff', cv.IMREAD_UNCHANGED)
    pictNull = cv.imread(name + '_' + str(i) + '_0.tiff', cv.IMREAD_UNCHANGED)
    pictFluo = (pictFluo - pictNull) * (pictFluo > pictNull)
    return pictFluo

# WRAPPER
def trackContourPyrLK(pictPrev, pictNext, ptsPrev, winSize, maxLevel):
    criteria = (cv.TERM_CRITERIA_EPS | cv.TERM_CRITERIA_COUNT, 10, 0.03)
    ptsTracked, _, _ = cv.calcOpticalFlowPyrLK(pictPrev, pictNext, #ptsPrev,
                                               #np.float32([tr[-1] for tr in ptsPrev]).reshape(-1, 1, 2),
                                               ptsPrev.reshape(-1, 1, 2),
                                               winSize=winSize, maxLevel=maxLevel,
                                               criteria=criteria)

    return ptsTracked


# WRAPPER
def getQuantityHighIntensityPixels(pict):
    return np.sum(cv.calcHist([pict], [0], None, [maxIntensity + 1], [minIntensity, maxIntensity+1])[numHighIntensity:])


def get740picts(name, begin, end):
    vctPicts = []
    for i in range(begin, end + 1):
        vctPicts.append(getPictTrue(name, i, 740))
        print('frame ' + str(i) + ' (' + str(i-begin) + '/' + str(end-begin) + ')')
    return vctPicts


# cont = tr2p()
def trackOneStep(pictPrev, ptsPrev, pictNext, winSize, maxLevel, delta):
    ptsNext = trackContourPyrLK(pictPrev, pictNext, ptsPrev, winSize, maxLevel)
    ptsTrackedBack = trackContourPyrLK(pictNext, pictPrev, ptsNext, winSize, maxLevel)

    m, diff = cv.threshold(np.array([[(i ** 2 + j ** 2) ** (1 / 2.)]
                    for [i, j] in abs(ptsPrev - ptsTrackedBack).reshape(-1,2)]).astype(np.float32),
                           delta, 1, cv.THRESH_BINARY_INV)
    return np.around([i for (i, j) in zip(ptsNext.reshape(-1, 2), diff)
                      if j]).astype(np.int32).reshape((-1, 1, 2))


def trackOneStepMeanShift(pictPrev, ptsPrev, pictNext, winSize, maxLevel, delta):
    ptsNext = trackContourPyrLK(pictPrev, pictNext, ptsPrev, winSize, maxLevel)

    ptsTrackedBack = trackContourPyrLK(pictNext, pictPrev, ptsNext, winSize, maxLevel)
    m, mask = cv.threshold(np.array([[(i ** 2 + j ** 2) ** (1 / 2.)]
            for [i, j] in abs(ptsPrev - ptsTrackedBack).reshape(-1, 2)]).astype(np.float32),
                           delta, 1, cv.THRESH_BINARY_INV)
    if ptsPrev.shape[0] - np.sum(mask) <= 0.9*ptsPrev.shape[0] :  # everything OK, go to usual loop, null counters
        diff = np.array([i - j for (i, j, k) in zip(ptsNext.reshape(-1, 2), ptsPrev.reshape(-1, 2), mask) if k])
        numPoints = diff.shape[0]
        shift = [np.sum(diff[:, 0]) / numPoints, np.sum(diff[:, 1]) / numPoints]
        return shift
    else:
        print u"контур не найден"
        return []


def getRMSE(contManual, contPredicted, shape):
    maskTracked = np.zeros(shape, np.int8)
    maskManual = np.zeros(shape, np.int8)
    cv.fillPoly(maskTracked, [contPredicted.astype(np.int32)], 1)
    cv.fillPoly(maskManual, [contManual.astype(np.int32)], 1)
    return np.sqrt(np.sum(np.square(maskTracked - maskManual)).astype(np.float32) / maskTracked.size)


def trackSeriesCompare740(winSize, maxLevel, delta, trackType):
    name, directory, begin, end = inputImages(True)
    vctPicts = get740picts(name, begin, end)
    vctPictsToShow = [(p * (maxIntensity / max(np.max(p), 1).astype(np.float32))).astype(np.uint8)
                      for p in vctPicts]
    if not os.access(directory + '\\' + 'cont' + str(0) + '.npy', os.F_OK):
        markupSeries(name, directory, end - begin)
    contPrev = np.load(directory + '\\' + 'cont' + str(0) + '.npy')
    maxDotsOut = contPrev.shape[0] / 2
    vctMSE = []

    numBadPictures = 0
    for i in range(1, len(vctPictsToShow)):
        print('frame: ' + str(i + 1))
        contNext = []
        if trackType is 0:
            contNext = trackOneStep(vctPictsToShow[i - numBadPictures - 1],
                                    contPrev, vctPictsToShow[i],
                                    winSize, maxLevel, delta)
            if contPrev.shape[0] - contNext.shape[0] <= maxDotsOut:  # everything OK, go to usual loop, null counters
                contPrev = contNext
                numBadPictures = 0
            else:  # bad picture, passing
                contNext = np.array([[[0, 0]]])
                numBadPictures = numBadPictures + 1
        elif trackType is 1:
            shift = trackOneStepMeanShift(vctPictsToShow[i - numBadPictures - 1],
                                          contPrev, vctPictsToShow[i], winSize, maxLevel, delta)
            if not shift == []:  # everything OK, go to usual loop, null counters
                contNext = (contPrev + shift)
                numBadPictures = 0
            else:  # bad picture, passing
                contNext = np.array([[[0, 0]]])
                numBadPictures = numBadPictures + 1

        if (i % frequency) == 0:
            contManual = np.load(directory + '\\' + 'cont' + str(i / frequency) + '.npy')
            MSE = getRMSE(contManual, contNext, vctPictsToShow[i].shape)
            print(MSE)
            vctMSE.append(MSE)
    np.save(directory + '\\' + 'MSE_' + str(trackType) + str(winSize) + str(delta) + str(maxLevel)
            + '.npy', np.array(vctMSE))



def getABetterPointToTrackGoodFeatures(x, y):
    mask = np.zeros(dictParams["shape"], np.uint8)
    mask[x - dictParams["kernelSize"] / 2: x + dictParams["kernelSize"] / 2 + 1,
    y - dictParams["kernelSize"] / 2: y + dictParams["kernelSize"] / 2 + 1] = \
        dictParams["kernel"]
    return cv.goodFeaturesToTrack(dictParams["pictNormalized"], 1, 0.1, 0,
                                  mask=mask).reshape(2)[::-1]

def getABetterPointToTrackSubPix(x, y):
    point = np.array([x, y], np.float32).reshape(1, 2)
    criteria = (cv.TERM_CRITERIA_EPS + cv.TERM_CRITERIA_COUNT, 30, 0.001)
    cv.cornerSubPix(dictParams["pictNormalized"], point, tuple((5,5)), zeroZone=tuple((-1, -1)), criteria=criteria)
    return point.reshape(2)


# poly = [[x1,y1],...] = man_con()
def contourManual(pict):
    cv.namedWindow('manual', cv.WINDOW_NORMAL)
    cv.moveWindow('manual', 1, 1)

    global dictParams
    dictParams = {"color":          CLR_GREEN,
                  "pictNormalized": (pict.astype(np.float) / max(np.max(pict), 1)
                                     * maxIntensity).astype(np.uint8),
                  "poly":           [],
                  "shape":          pict.shape,
                  "flgDrawing":     False,
                  "thickness":      3,
                  "kernelSize":     KernelSize}

    dictParams["kernel"] = np.ones((dictParams["kernelSize"], dictParams["kernelSize"]), np.uint8)
    dictParams["pictShow"] = cv.cvtColor(dictParams["pictNormalized"], cv.COLOR_GRAY2RGB)

    def onMouse(event, x, y, _flags, _param):
        global dictParams
        if event == cv.EVENT_LBUTTONDOWN:
            dictParams["flgDrawing"] = True
            # dictParams["poly"] = dictParams["poly"] + [getABetterPointToTrackGoodFeatures(x, y)]
            dictParams["poly"] = dictParams["poly"] + [getABetterPointToTrackSubPix(x, y)]
            # dictParams["poly"] = dictParams["poly"] + [[x, y]]
            dictParams["pictShow"] = cv.cvtColor(dictParams["pictNormalized"], cv.COLOR_GRAY2RGB)
            cv.polylines(dictParams["pictShow"], [np.array(dictParams["poly"], np.int32)],
                         False, dictParams["color"], dictParams["thickness"])
            cv.imshow('manual', dictParams["pictShow"])
        elif event == cv.EVENT_MOUSEMOVE:
            if dictParams['flgDrawing'] is True:
                # dictParams["poly"] = dictParams["poly"] + [getABetterPointToTrackGoodFeatures(x, y)]
                # dictParams["poly"] = dictParams["poly"] + [[x, y]]
                dictParams["poly"] = dictParams["poly"] + [getABetterPointToTrackSubPix(x, y)]
                cv.line(dictParams["pictShow"], tuple(dictParams["poly"][-2]), tuple(dictParams["poly"][-1]),
                        dictParams["color"], dictParams["thickness"])
                cv.imshow('manual', dictParams["pictShow"])
        elif event == cv.EVENT_LBUTTONUP:
            dictParams["flgDrawing"] = False
            cv.line(dictParams["pictShow"], tuple(dictParams["poly"][0]), tuple(dictParams["poly"][-1]),
                    dictParams["color"], dictParams["thickness"])
            cv.imshow('manual', dictParams["pictShow"])
        elif event == cv.EVENT_RBUTTONUP:
            dictParams["poly"] = []
            dictParams["pictShow"] = cv.cvtColor(dictParams["pictNormalized"], cv.COLOR_GRAY2RGB)
            cv.imshow('manual', dictParams["pictShow"])

    while not dictParams["poly"]:
        cv.imshow('manual', dictParams["pictShow"])
        cv.setMouseCallback('manual', onMouse)
        cv.waitKey(0)
        cv.destroyWindow('manual')
    return dictParams["poly"]


if __name__ == '__main__':

    trackSeriesCompare740(winSize, maxLevel, delta, trackType)
