import cv2 as cv
import numpy as np

BTN_ESC = 27
BTN_CTRL_C = 3
CLR_RED = (0, 0, 255)
CLR_GREEN = (0, 255, 0)
minIntensity = 0
maxIntensity = 255
maxAllowedIntensity = 252
numHighIntensity = 230
maxAllowedNumberHighIntensityPixels = 30
GaussKernel = (5, 5)


# pict = cutHighIntensityPoints()
# WRAPPER
def cutHighIntensityPoints(pict, start):
    m, pict = cv.threshold(pict, start, maxIntensity, cv.THRESH_TOZERO_INV)
    return pict


#pictThreshed = thresholdOtsu()
# WRAPPER
def thresholdOtsu(pict):
    m, pictThreshed = cv.threshold(pict, minIntensity, maxIntensity, cv.THRESH_BINARY + cv.THRESH_OTSU)
    return pictThreshed


# WRAPPER
def getPictTrue(name, i, wl):
    pictFluo = cv.imread(name + str(i) + '_' + str(wl) + '.tiff', cv.IMREAD_GRAYSCALE)
    pictNull = cv.imread(name + str(i) + '_0.tiff', cv.IMREAD_GRAYSCALE)
    return pictFluo - pictNull


# WRAPPER
def showPict(pict, winName):
    pictShow = (pict * (maxIntensity / max(max(pict), 1))).astype(np.uint8)
    cv.imshow(winName, pictShow)


# WRAPPER
def trackContourPyrLK(pictPrev, pictNext, ptsPrev, winSize, maxLevel):
    ptsTracked, status, err = cv.calcOpticalFlowPyrLK(pictPrev, pictNext,
                                                      np.float32([tr[-1] for tr in ptsPrev]).reshape(-1, 1, 2),
                                                      None, winSize=winSize, maxLevel=maxLevel)
    return ptsTracked


# WRAPPER
def getIntensityInsideContour(pict, cont):
    mskCont = cv.fillPoly(np.zeros(pict.shape, np.uint8), [cont], 1)
    intensity = np.sum(pict * mskCont)
    return intensity, intensity / max(np.sum(mskCont), 1)


# WRAPPER
def getNumberHighIntensityPixels(pict):
    return np.sum(cv.calcHist([pict], [0], None, [maxIntensity + 1], [minIntensity, maxIntensity+1])[numHighIntensity:])


# picts(raw), threshs, conts = pictsconts()
def getPictsThreshsConts(name, wl, begin, end):
    vctPicts = []
    vctThreshs = []
    vctConts = []

    for i in range(begin, end+1):
        pictTrue = getPictTrue(name, i, wl)
        maxPictTrue = np.max(pictTrue)

        if maxPictTrue > maxAllowedIntensity:
            pictTrue = cutHighIntensityPoints(pictTrue, maxAllowedIntensity)

        pictBlur = cv.GaussianBlur(pictTrue, GaussKernel, 0)
        vctPicts.append(pictBlur)

        pictThreshed = thresholdOtsu(pictBlur)

        vctThreshs.append(pictThreshed)

        cont, hier = cv.findContours(pictThreshed, cv.RETR_TREE, cv.CHAIN_APPROX_SIMPLE)

        vctConts = vctConts + cont #если возвращается больше одного контура - не работает

        print(str(i) + '/' + str(end))
    return vctPicts, vctThreshs, vctConts


# None = shrpc()
def showRawPicts(name, wl, begin, end):
    cv.namedWindow('picture', cv.WINDOW_NORMAL)
    for i in range(begin, end + 1):
        pictTrue = getPictTrue(name, i, wl)
        showPict(pictTrue, 'picture')
        cv.setWindowTitle('picture', 'picture' + str(i))

        if cv.waitKey(0) == BTN_ESC:
            cv.destroyAllWindows()
            break


# None = shp()
def showAllPicts(name, wl, begin, end):
    cv.namedWindow('picture', cv.WINDOW_NORMAL)
    cv.namedWindow('threshblur', cv.WINDOW_NORMAL)
    for i in range(begin, end + 1):
        pictTrue = getPictTrue(name, i, wl)
        maxPictTrue = np.max(pictTrue)

        if maxPictTrue > maxAllowedIntensity:
            pictTrue = cutHighIntensityPoints(pictTrue, maxAllowedIntensity)

        pictBlur = cv.GaussianBlur(pictTrue, GaussKernel, 0)
        showPict(pictBlur, 'picture')
        cv.setWindowTitle('picture', 'picture' + str(i))

        pictThreshed = thresholdOtsu(pictBlur)
        cv.imshow('threshblur', pictThreshed)
        if cv.waitKey(0) == BTN_ESC:
            cv.destroyAllWindows()
            break


# cont = tr2p()
def trackOneStep(pictPrev, ptsPrev, pictNext, winSize, maxLevel, delta):
    ptsNext = trackContourPyrLK(pictPrev, pictNext, ptsPrev, winSize, maxLevel)

    ptsTrackedBack = trackContourPyrLK(pictNext, pictPrev, ptsNext, winSize, maxLevel)

    m, diff = cv.threshold(np.array([[(i ** 2 + j ** 2) ** (1 / 2)]
                                     for [i, j] in abs(ptsPrev - ptsTrackedBack).reshape(-1, 2)]),
                           delta, 1, cv.THRESH_BINARY_INV)
    return np.around([i for (i, j) in zip(ptsNext.reshape(-1, 2), diff) if j]).astype(np.int32).reshape((-1, 1, 2))


# None = ()
# на каждом шаге выводит количество оставшихся точек, n_i, n_sum

#def last

def trackSeriesCompare(winSize, maxLevel, delta, maxNumberBadPictures, maxDotsOut, name, wl, end, begin=1,
                       compare=False):
    vctPicts, vctThreshs, vctConts = getPictsThreshsConts(name, wl, begin, end)
    vctPictsToShow = [(p * (maxIntensity / max(np.max(p), 1))).astype(np.uint8) for p in vctPicts]

    cv.namedWindow('thresh', cv.WINDOW_NORMAL)
    cv.namedWindow('contoured_by', cv.WINDOW_NORMAL)
    cv.imshow('thresh', vctThreshs[0])

    contManual = contSaved = contFirst = np.array(contourManual((vctPictsToShow[0]))).reshape((-1, 1, 2))

    intensity, meanIntensity = getIntensityInsideContour(vctPicts[0], contManual)
    vctIntensity = [intensity]
    vctMean = [meanIntensity]

    pictToShow = cv.drawContours(cv.cvtColor(vctPictsToShow[0], cv.COLOR_GRAY2RGB), [contManual], -1, CLR_RED, 3)
    cv.imshow('contoured_by', pictToShow)
    print(str(1) + ': N_i = ' + str(contManual.shape[0]) + ', intensity = ', str(intensity))

    if cv.waitKey(0) == BTN_CTRL_C:
        cv.imwrite('Output\\' + name + str(1) + '_' + str(wl) + '.tiff', pictToShow)
        cv.waitKey(0)
    numBadPictures = numLazeredPictures = prcTotalLost = 0
    for i in range(1, len(vctPicts)):
        cv.setWindowTitle('contoured_by', 'contoured_by' + str(i + 1))
        
        cv.setWindowTitle('thresh', 'thresh' + str(i + 1))
        cv.imshow('thresh', vctThreshs[i])

        if getNumberHighIntensityPixels(vctPicts[i]) < maxAllowedNumberHighIntensityPixels:  # laser off
            contNext = trackOneStep(vctPictsToShow[i - numBadPictures - numLazeredPictures - 1], contManual, vctPictsToShow[i],
                                    winSize, maxLevel, delta)
            prcLostPoints = (contManual.shape[0] - contNext.shape[0]) * 100. / contManual.shape[0]
            if contManual.shape[0] - contNext.shape[0] <= maxDotsOut:  # everything OK, go to usual loop, null counters
                pictToShow = cv.drawContours(cv.cvtColor(vctPictsToShow[i], cv.COLOR_GRAY2RGB),
                                            [contNext], -1, CLR_RED, 3)
                intensity, meanIntensity = getIntensityInsideContour(vctPicts[i], contNext)
                vctIntensity.append(intensity)
                vctMean.append(meanIntensity)
                contSaved, contManual = contManual, contNext
                numBadPictures = numLazeredPictures = 0
                prcTotalLost += prcLostPoints
                print(str(i + 1) + ': N_i = ' + str(contNext.shape[0]) + ', n_i = ' + str(prcLostPoints) + ', n_s = '
                      + str(prcTotalLost) + ', intensity = ', str(intensity))
            else:  # bad picture, passing
                pictToShow = vctPictsToShow[i]
                vctIntensity.append(0)
                vctMean.append(0)
                numBadPictures = numBadPictures + 1
                print(str(i + 1) + ': N_i = ' + str(contNext.shape[0]) + ', n_i = ' + str(prcLostPoints) +
                      ', n_s = ' + str(prcTotalLost))
        else:  # laser on, passing
            pictToShow = vctPictsToShow[i]
            vctIntensity.append(0)
            vctMean.append(0)
            numLazeredPictures = numLazeredPictures + 1
        cv.imshow('contoured_by', pictToShow)
        ans = cv.waitKey(0)
        if ans == BTN_ESC:
            break
        elif ans == BTN_CTRL_C:
            cv.imwrite('Output\\' + name + str(i + 1) + '_' + str(wl) + '.tiff', pictToShow)
            if cv.waitKey(0) == BTN_ESC:
                break
    if compare:
        cv.namedWindow('firstpicture', cv.WINDOW_NORMAL)
        cv.imshow('firstpicture', cv.drawContours(cv.cvtColor(vctPictsToShow[0], cv.COLOR_GRAY2RGB),
                                                  [contFirst], -1, CLR_RED, 3))
        if cv.waitKey(0) == BTN_CTRL_C:
            cv.imwrite('Output\\' + name + str(1) + '_' + str(wl) + '.tiff', pictToShow)


# poly = [[x1,y1],...] = man_con()
def contourManual(pict):
    cv.namedWindow('input', cv.WINDOW_NORMAL)
    cv.moveWindow('input', 1, 1)

    dictParams = {"color":          CLR_GREEN,
                  "pictNormalized": (cv.cvtColor(pict, cv.COLOR_GRAY2RGB).astype(np.float)
                                     / max(np.max(cv.cvtColor(pict, cv.COLOR_GRAY2RGB)), 1)
                                     * maxIntensity).astype(np.uint8),
                  "poly":           [],
                  "flgDrawing":     False,
                  "thickness":      3}
    dictParams["pictShow"] = dictParams["pictNormalized"].copy()

    def onMouse(event, x, y, flags, param):
        nonlocal dictParams
        if event == cv.EVENT_LBUTTONDOWN:
            dictParams["flgDrawing"] = True
            dictParams["poly"] = dictParams["poly"] + [[x, y]]
            cv.polylines(dictParams["pictShow"], [np.array(dictParams["poly"], np.int32)],
                         False, dictParams["color"], dictParams["thickness"])
            cv.imshow('input', dictParams["pictShow"])
        elif event == cv.EVENT_MOUSEMOVE:
            if dictParams['flgDrawing'] is True:
                dictParams["poly"] = dictParams["poly"] + [[x, y]]
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
            dictParams["pictShow"] = dictParams["pictNormalized"].copy()
            cv.imshow('input', dictParams["pictShow"])

    while not dictParams["poly"]:
        cv.imshow('input', dictParams["pictShow"])
        cv.setMouseCallback('input', onMouse)
        cv.waitKey(0)
        cv.destroyWindow('input')
    return dictParams["poly"]
