import numpy as np
import cv2 as cv

def getContourMSE(contManual, contPredicted, shape):
    maskTracked = np.zeros(shape, np.int8)
    maskManual = np.zeros(shape, np.int8)
    cv.fillPoly(maskTracked, [contPredicted.astype(np.int32)], 1)
    cv.fillPoly(maskManual, [contManual.astype(np.int32)], 1)
    return np.sqrt(np.sum(np.square(maskTracked - maskManual)).astype(np.float32) / maskTracked.size)

def getIntensityMSE(contManual, contPredicted, img):
    shape = img.shape
    maskTracked = np.zeros(shape, np.int8)
    maskManual = np.zeros(shape, np.int8)
    cv.fillPoly(maskTracked, [contPredicted.astype(np.int32)], 1)
    cv.fillPoly(maskManual, [contManual.astype(np.int32)], 1)
    return np.square(np.sum(maskTracked * img) - np.sum(maskManual * img)).astype(np.float32) / np.sum(maskManual * img)
