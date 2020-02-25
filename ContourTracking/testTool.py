import os
import numpy as np
# import time
from constants import *
from tracking import trackOneStep, trackOneStepMeanShift, getContourMSE
from loadPictures import getPictTrue

address = "F:\Chura\Series"
ktrackType = 1
kw = 30
kwinSize = (kw, kw)
kdelta = 30
kPtsPartStay = 0.5
kmaxLevel = 1

dw = 1
dd = 1
da = 0.01

def getPictsTest(pth):
    vctPicts = []
    files = {}
    for f in os.listdir(pth):
        if f.startswith('frame') and f.endswith('740.tiff'):
            number = ''
            for l in f[6:]:
                if l.isdigit():
                    number = number + l
                else: break
            files[f] = int(number)
    sortedFiles = [k for (k, v) in sorted(files.items(), key=lambda kv: (kv[1], kv[0]))]
    for f in sortedFiles:
        vctPicts.append(getPictTrue(pth + '\\' + f, '740'))
        print('\t\t\tget ' + f)
    return vctPicts

def trackSeriesCompare740Test(wnSize, maxLevel, dlta, ptsPrtStay, trckType, dirc):
    pth = address + "\\" + dirc + "\Full\Test"
    MSEpath = address + '\\MSE\\' + str(trckType) + '_' \
              + str(wnSize) + '_' + str(dlta) + '_' + str(ptsPrtStay) + '_' \
              + str(maxLevel)
    vctPicts = getPictsTest(pth)
    vctPictsNormalized = [(p * (maxIntensity / max(np.max(p), 1).astype(np.float32))).astype(np.uint8)
                      for p in vctPicts]
    contPrev = np.load(pth + '\\' + 'cont' + str(0) + '.npy').reshape(-1, 1, 2)
    vctMSE = []

    numBadPictures = 0
    # t1 = time.time()
    for j in range(1, len(vctPictsNormalized)):
        print('\t\t\tframe: ' + str(j + 1))
        if trckType is 0:
            contNext = trackOneStep(vctPictsNormalized[j - numBadPictures - 1],
                                    contPrev, vctPictsNormalized[j],
                                    wnSize, maxLevel, dlta)
            if contNext.shape[0] >= ptsPrtStay * contPrev.shape[0]:  # everything OK, go to usual loop, null counters
                contPrev = contNext
                numBadPictures = 0
            else:  # bad picture, passing
                contNext = np.array([[[0, 0]]])
                numBadPictures = numBadPictures + 1
        elif trckType is 1:
            shift = trackOneStepMeanShift(vctPictsNormalized[j - numBadPictures - 1],
                                          contPrev, vctPictsNormalized[j], wnSize, maxLevel, dlta, ptsPrtStay)
            if shift is not None:  # everything OK, go to usual loop, null counters
                contNext = (contPrev + shift)
                numBadPictures = 0
            else:  # bad picture, passing
                contNext = np.array([[[0, 0]]])
                numBadPictures = numBadPictures + 1
        else: return -1

        if (j % frequency) == 0:
            contManual = np.load(pth + '\\' + 'cont' + str(j / frequency) + '.npy').reshape(-1, 1, 2)
            MSE = getContourMSE(contManual, contNext,
                                vctPictsNormalized[j].shape)
            vctMSE.append(MSE)
    # t2 = time.time()
    # vctMSE.append(t2 - t1)
    np.save(MSEpath + '\\' + 'MSE_'  + dirc + '.npy', np.array(vctMSE))

def averaging(path):
    MSEs = os.listdir(path)
    avgMSE = np.empty((1, 2))
    for f in MSEs:
        vctMSE = np.load(path + '\\' + f)
        j = -1
        for MSE in vctMSE:
            j +=1
            if j + 1 > avgMSE.shape[0]:
                avgMSE.resize((j + 1, 2))
            avgMSE[j, 0] += MSE
            avgMSE[j, 1] += 1
    return [s / n for [s, n] in avgMSE]

def testParams(wnSize, dlta, PtsPrtStay):
    MSEpath = address + '\\MSE\\' + str(ktrackType) + '_' \
              + str(wnSize) + '_' + str(dlta) + '_' + str(PtsPrtStay) + '_' \
              + str(kmaxLevel)
    if not os.access(MSEpath + '.npy', os.F_OK):
        print("\tTESTING parameters: " + str(ktrackType) + '_'
              + str(wnSize) + '_' + str(dlta) + '_' + str(PtsPrtStay) + '_'
              + str(kmaxLevel))
        j = 0
        directories = os.listdir(address)
        directories.remove("MSE")
        for direc in directories:
            j += 1
            print('\t\tTEST ' + str(j) + '/' + str(len(directories)))
            if not os.access(MSEpath, os.F_OK):
                os.makedirs(MSEpath)
            trackSeriesCompare740Test(wnSize, kmaxLevel, dlta, PtsPrtStay,
                                      ktrackType, direc)
        vctMSE = averaging(MSEpath)
        np.save(MSEpath + '.npy', np.array(vctMSE))
    else:
        print("\tLOAD parameters: " + str(ktrackType) + '_'
              + str(wnSize) + '_' + str(dlta) + '_' + str(PtsPrtStay) + '_'
              + str(kmaxLevel))
        vctMSE = np.load(MSEpath + '.npy')
    vctMSE = np.array([0] + list(vctMSE))
    p = np.polyfit(range(0, vctMSE.shape[0]), vctMSE, 1)
    print("\tAvg MSE increase: " + str(p[0]))
    return p[0]

def gradient(wsize, dlt, alpha):
    return ((testParams((wsize + dw, wsize + dw), dlt,      alpha)      - testParams((wsize, wsize), dlt, alpha)) / dw,
            (testParams((wsize, wsize),           dlt + dd, alpha)      - testParams((wsize, wsize), dlt, alpha)) / dd,
            (testParams((wsize, wsize),           dlt,      alpha + da) - testParams((wsize, wsize), dlt, alpha)) / da)


if __name__ == '__main__':
    wsaved = wsaved1 = w = kw
    winSize = (w, w)
    dsaved = dsaved1 = delta = kdelta
    asaved = asaved1 = PtsPartStay = kPtsPartStay

    i = 0

    while True:
        i += 1
        print("step " + str(i))
        (d_dw, d_dd, d_da) = gradient(w, delta, PtsPartStay)
        print("gradient: " + str((d_dw, d_dd, d_da)))
        if w - np.sign(d_dw)                > 2    : w           -= int(np.sign(d_dw))
        if delta - np.sign(d_dd)            > 2    : delta       -= int(np.sign(d_dd))
        if PtsPartStay - da * np.sign(d_da) > 0.05 : PtsPartStay -= da * np.sign(d_da)
        if i > 2:
            if w == wsaved and delta == dsaved and PtsPartStay == asaved:
                break
            else:
                wsaved = wsaved1
                wsaved1 = w
                dsaved = dsaved1
                dsaved1 = delta
                asaved = asaved1
                asaved1 = PtsPartStay
        print("new params: w=" + str(w) + ", delta=" + str(delta) + ", percent=" + str(PtsPartStay))
    print('Finished')
    print("params: w=" + str(w) + ", delta=" + str(delta) + ", percent=" + str(PtsPartStay))


    # print(gradient(w, delta, PtsPartStay))
    #values: (0.0023168430004513194, 0.0023041253102788449, 0.46083879999193705)

    # testParams(trackType, winSize, delta, PtsPartStay, kmaxLevel)

