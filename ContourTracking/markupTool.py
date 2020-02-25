# -*- coding: utf-8 -*-
import cv2 as cv
import numpy as np
from renamePictures import renamePictures
from loadPictures import getPictTrue
from constants import *

# MarkupTool требует на вход подготовленую, правильно именованную серию изображений:
#  - Изображения в формате .tiff
#  - Отсортированные по имени в том порядке, в котором они должны идти в серии
#  - Для серий флуоресцентных изображений - флажок

nRaw          = 0
nGoodFeatures = 1
nSubPix       = 2

def getABetterPointToTrack(x, y, searchType):
    if searchType == nRaw:
        return x, y
    if searchType == nGoodFeatures:
        mask = np.zeros(dictParams["shape"], np.uint8)
        mask[
        x - dictParams["kernelSize"] / 2: x + dictParams["kernelSize"] / 2 + 1,
        y - dictParams["kernelSize"] / 2: y + dictParams[
            "kernelSize"] / 2 + 1] = \
            dictParams["kernel"]
        return cv.goodFeaturesToTrack(dictParams["pictNormalized"], 1, 0.1, 0,
                                      mask=mask).reshape(2)[::-1]
    if searchType == nSubPix:
        point = np.array([x, y], np.float32).reshape(1, 2)
        criteria = (cv.TERM_CRITERIA_EPS + cv.TERM_CRITERIA_COUNT, 30, 0.001)
        cv.cornerSubPix(dictParams["pictNormalized"], point, tuple((5, 5)),
                        zeroZone=tuple((-1, -1)), criteria=criteria)
        return point.reshape(2)

# poly = [[x1,y1],...] = man_con()
def contourManual(pict, searchType=nSubPix):
    win = 'manual'
    cv.namedWindow(win, cv.WINDOW_NORMAL)

    global dictParams
    dictParams = {"color":          CLR_GREEN,
                  "pictNormalized": (pict.astype(np.float) / max(np.max(pict), 1)
                                     * maxIntensity).astype(np.uint8),
                  "poly":           [],
                  "shape":          pict.shape,
                  "flgDrawing":     False,
                  "thickness":      3,
                  "kernelSize":     kKernelSize}

    dictParams["kernel"] = np.ones((dictParams["kernelSize"], dictParams["kernelSize"]), np.uint8)
    dictParams["pictShow"] = cv.cvtColor(dictParams["pictNormalized"], cv.COLOR_GRAY2RGB)

    def onMouse(event, x, y, _flags, _param):
        global dictParams
        if event == cv.EVENT_LBUTTONDOWN:
            dictParams["flgDrawing"] = True
            dictParams["poly"] = dictParams["poly"] + [getABetterPointToTrack(x, y, searchType)]
            dictParams["pictShow"] = cv.cvtColor(dictParams["pictNormalized"], cv.COLOR_GRAY2RGB)
            cv.polylines(dictParams["pictShow"], [np.array(dictParams["poly"], np.int32)],
                         False, dictParams["color"], dictParams["thickness"])
            cv.imshow(win, dictParams["pictShow"])
        elif event == cv.EVENT_MOUSEMOVE:
            if dictParams['flgDrawing'] is True:
                dictParams["poly"] = dictParams["poly"] + [getABetterPointToTrack(x, y, searchType)]
                cv.line(dictParams["pictShow"], tuple(dictParams["poly"][-2]), tuple(dictParams["poly"][-1]),
                        dictParams["color"], dictParams["thickness"])
                cv.imshow(win, dictParams["pictShow"])
        elif event == cv.EVENT_LBUTTONUP:
            if dictParams['flgDrawing'] is True:
                dictParams["flgDrawing"] = False
                cv.line(dictParams["pictShow"], tuple(dictParams["poly"][0]), tuple(dictParams["poly"][-1]),
                        dictParams["color"], dictParams["thickness"])
                cv.imshow(win, dictParams["pictShow"])
        elif event == cv.EVENT_RBUTTONUP:
            dictParams["poly"] = []
            dictParams["flgDrawing"] = False
            dictParams["pictShow"] = cv.cvtColor(dictParams["pictNormalized"], cv.COLOR_GRAY2RGB)
            cv.imshow(win, dictParams["pictShow"])

    while not dictParams["poly"]:
        cv.imshow(win, dictParams["pictShow"])
        cv.setMouseCallback(win, onMouse)
        cv.waitKey(0)
    return dictParams["poly"]

def markupSeries(name, direc, quantity, shouldSubtractBg=False, searchType=nSubPix):
    for i in range(1, quantity):
        if (i - 1) % frequency == 0:
            print(str((i - 1) / frequency + 1) + '/' + str((quantity + 1) / frequency))
            filename = name + '_' + str(i) + '_' + str(740) + '.tiff'
            if shouldSubtractBg:
                pict = getPictTrue(filename, 740)
            else:
                pass
            # TODO: нужно будет изменить именование файлов
            np.save(direc + '\\' + 'cont' + str((i - 1) / frequency) + '.npy',
                    contourManual((pict *
                                  (maxIntensity /
                                   max(np.max(pict), 1).astype(np.float32))).astype(np.uint8), searchType))


if __name__ == '__main__':
    fullname, directory, numFrames = renamePictures(is740only=True)
    markupSeries(fullname + '_740', directory, numFrames, shouldSubtractBg=True)