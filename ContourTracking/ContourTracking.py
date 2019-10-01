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
GaussKernel = (13, 13)


#WRAPPER
def inputImages():
    app = pyqtgraph.GraphicsWindow().setBackground(None)
    filename = FileDialog().getOpenFileName(parent=app, caption='Choose the first series file',
                                            filter="*_740.tiff").toUtf8()
    filename = ''.join([l if not l == '/' else '\\' for l in filename])
    begin = ''
    for l in filename[-10::-1]:
        if l == '_':
            break
        begin += l
    fullname = filename[:-9 - len(begin)]
    begin = int(begin[::-1])


    path = fullname[:]
    for l in fullname[::-1]:
        if l == '\\':
            break
        path = path[:-1]

    numOfPictures = FileDialog().getOpenFileName(parent=app, caption='Choose the last series file',
                                                 filter="*_740.tiff").toUtf8()
    numOfPictures = int(numOfPictures[len(fullname):-9])
    return fullname, begin, numOfPictures


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
    pictFluo = cv.imread(name + str(i) + '_' + str(wl) + '.tiff', cv.IMREAD_UNCHANGED)
    pictNull = cv.imread(name + str(i) + '_0.tiff', cv.IMREAD_UNCHANGED)
    pictFluo = (pictFluo - pictNull) * (pictFluo > pictNull)
    #return np.array([i if j else 0 for (k, l) in zip((pictFluo - pictNull), (pictFluo > pictNull)) for (i, j) in zip(k, l)]).reshape(shape)
    #return np.array([i if j else 0 for (i, j) in zip((pictFluo - pictNull).reshape(-1), (pictFluo > pictNull).reshape(-1))]).reshape(shape)
    # for i in range(pictFluo.shape[0]):
    #     for j in range(pictFluo.shape[1]):
    #         if pictFluo[i, j] < pictNull[i, j]:
    #             pictFluo[i, j] = 0
    #         else:
    #             pictFluo[i, j] -= pictNull[i, j]
    return pictFluo

# WRAPPER
def trackContourPyrLK(pictPrev, pictNext, ptsPrev, winSize, maxLevel):
    ptsTracked, status, err = cv.calcOpticalFlowPyrLK(pictPrev, pictNext,
                                                      np.float32([tr[-1] for tr in ptsPrev]).reshape(-1, 1, 2),
                                                      None, winSize=winSize, maxLevel=maxLevel)
    return ptsTracked


# WRAPPER
def getNumberHighIntensityPixels(pict):
    return np.sum(cv.calcHist([pict], [0], None, [maxIntensity + 1], [minIntensity, maxIntensity+1])[numHighIntensity:])


def get740picts(name, begin, end):
    vctPicts = []
    for i in range(begin, end + 1):
        vctPicts.append(getPictTrue(name, i, 740))
        print(str(i) + '/' + str(end))
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
    if ptsPrev.shape[0] - np.sum(mask) <= ptsPrev.shape[0] / 2:  # everything OK, go to usual loop, null counters
        diff = np.array([i - j for (i, j, k) in zip(ptsNext.reshape(-1, 2), ptsPrev.reshape(-1, 2), mask) if k])
        numPoints = diff.shape[0]
        shift = [np.sum(diff[:, 0]) / numPoints, np.sum(diff[:, 1]) / numPoints]
        return shift
    else:
        return []


def trackSeriesCompare740(winSize, maxLevel, delta, compare=False):
    name, begin, end = inputImages()
    vctPicts = get740picts(name, begin, end)
    vctPictsToShow = [(p * (maxIntensity / max(np.max(p).astype(np.float32), 1).astype(np.float32))).astype(np.uint8) for p in vctPicts]


    cv.namedWindow('contoured', cv.WINDOW_NORMAL)

    contPrev = contFirst = np.array(contourManual((vctPictsToShow[0]))).reshape((-1, 1, 2))

    maxDotsOut = contPrev.shape[0] / 2

    pictToShow = cv.cvtColor(vctPictsToShow[0], cv.COLOR_GRAY2RGB)
    cv.drawContours(pictToShow, [contPrev.astype(np.int32)], -1, CLR_RED, 3)
    cv.imshow('contoured', pictToShow)

    if cv.waitKey(0) == BTN_CTRL_C:
        cv.imwrite('Output\\' + name + str(1) + '.tiff', pictToShow)
        cv.waitKey(0)
    numBadPictures = numLazeredPictures = 0
    for i in range(1, len(vctPicts)):
        print('frame: ' + str(i + 1))

        # shift = trackOneStepMeanShift(vctPictsToShow[i - numBadPictures - numLazeredPictures - 1],
        #                         contPrev, vctPictsToShow[i], winSize, maxLevel, delta)
        # if not shift == []:  # everything OK, go to usual loop, null counters
        #     contNext = (contPrev + shift)
        contNext = trackOneStep(vctPictsToShow[i - numBadPictures - numLazeredPictures - 1],
                                contPrev, vctPictsToShow[i],
                                winSize, maxLevel, delta)
        if contPrev.shape[0] - contNext.shape[0] <= maxDotsOut:  # everything OK, go to usual loop, null counters
            pictToShow = cv.cvtColor(vctPictsToShow[i], cv.COLOR_GRAY2RGB)
            cv.drawContours(pictToShow, [contNext.astype(np.int32)], -1, CLR_RED, 3)

            contPrev = contNext
            numBadPictures = numLazeredPictures = 0
        else:  # bad picture, passing
            numBadPictures = numBadPictures + 1
            pictToShow = vctPictsToShow[i]
        cv.imshow('contoured', pictToShow)
        ans = cv.waitKey(0)
        if ans == BTN_ESC:
            break
        elif ans == BTN_CTRL_C:
            cv.imwrite('Output\\' + name + str(i + 1) + '.tiff', pictToShow)
            if cv.waitKey(0) == BTN_ESC:
                break


    if compare:
        cv.namedWindow('firstpicture', cv.WINDOW_NORMAL)
        pictFirst = cv.cvtColor(vctPictsToShow[0], cv.COLOR_GRAY2RGB)
        cv.drawContours(pictFirst, [contFirst.astype(np.int32)], -1, CLR_RED, 3)
        cv.imshow('firstpicture', pictFirst)
        if cv.waitKey(0) == BTN_CTRL_C:
            cv.imwrite('Output\\' + name + str(1) + '.tiff', pictToShow)


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
    cv.namedWindow('input', cv.WINDOW_NORMAL)
    cv.moveWindow('input', 1, 1)

    global dictParams
    dictParams = {"color":          CLR_GREEN,
                  "pictNormalized": (pict.astype(np.float) / max(np.max(pict), 1)
                                     * maxIntensity).astype(np.uint8),
                  "poly":           [],
                  "shape":          pict.shape,
                  "flgDrawing":     False,
                  "thickness":      3,
                  "kernelSize":     11}

    dictParams["kernel"] = np.ones((dictParams["kernelSize"], dictParams["kernelSize"]), np.uint8)
    dictParams["pictShow"] = cv.cvtColor(dictParams["pictNormalized"], cv.COLOR_GRAY2RGB)

    def onMouse(event, x, y, flags, param):
        global dictParams
        if event == cv.EVENT_LBUTTONDOWN:
            dictParams["flgDrawing"] = True
            # dictParams["poly"] = dictParams["poly"] + [getABetterPointToTrackGoodFeatures(x, y)]
            dictParams["poly"] = dictParams["poly"] + [getABetterPointToTrackSubPix(x, y)]
            # dictParams["poly"] = dictParams["poly"] + [[x, y]]
            dictParams["pictShow"] = cv.cvtColor(dictParams["pictNormalized"], cv.COLOR_GRAY2RGB)
            cv.polylines(dictParams["pictShow"], [np.array(dictParams["poly"], np.int32)],
                         False, dictParams["color"], dictParams["thickness"])
            cv.imshow('input', dictParams["pictShow"])
        elif event == cv.EVENT_MOUSEMOVE:
            if dictParams['flgDrawing'] is True:
                # dictParams["poly"] = dictParams["poly"] + [getABetterPointToTrackGoodFeatures(x, y)]
                # dictParams["poly"] = dictParams["poly"] + [[x, y]]
                dictParams["poly"] = dictParams["poly"] + [getABetterPointToTrackSubPix(x, y)]
                cv.line(dictParams["pictShow"], tuple(dictParams["poly"][-2]), tuple(dictParams["poly"][-1]),
                        dictParams["color"], dictParams["thickness"])
                cv.imshow('input', dictParams["pictShow"])
        elif event == cv.EVENT_LBUTTONUP:
            dictParams["flgDrawing"] = False
            cv.line(dictParams["pictShow"], tuple(dictParams["poly"][0]), tuple(dictParams["poly"][-1]),
                    dictParams["color"], dictParams["thickness"])
            cv.imshow('input', dictParams["pictShow"])
        elif event == cv.EVENT_RBUTTONUP:
            dictParams["poly"] = []
            dictParams["pictShow"] = cv.cvtColor(dictParams["pictNormalized"], cv.COLOR_GRAY2RGB)
            cv.imshow('input', dictParams["pictShow"])

    while not dictParams["poly"]:
        cv.imshow('input', dictParams["pictShow"])
        cv.setMouseCallback('input', onMouse)
        cv.waitKey(0)
        cv.destroyWindow('input')
    return dictParams["poly"]


if __name__ == '__main__':

    trackSeriesCompare740(winSize=(30, 30), maxLevel=6, delta=30, compare=True)
