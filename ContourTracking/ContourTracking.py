from funcs import *

trackSeriesCompare(winSize=(90, 90), maxLevel=6, delta=30, maxNumberBadPictures=10,
                   maxDotsOut=5, compare=True, name='3_1_', wl=400, end=85)


# TODO: возможно, использ. эту ф-ю
# cv.goodFeaturesToTrack() - функция для отыскания углов

# nextPts, status, err = cv.calcOpticalFlowPyrLK(threshs[0], threshs[1],
#                                                np.float32([tr[-1] for tr in conts[0]]).reshape(-1, 1, 2), None)
# cv.namedWindow('contoured_by', cv.WINDOW_NORMAL)
# cv.imshow('contoured_by', cv.drawContours(cv.cvtColor(thgauss, cv.COLOR_GRAY2RGB),
#                                           [np.int32(np.around(nextPts))], -1, (0, 0, 255), 3))
# cv.waitKey(0)
pass
# TODO: найти оптимальный Гаусс
# import cv2 as cv
# import numpy as np
# import matplotlib.pyplot as plt
#
# name = 'T'
# # i = 1
# wl = 400
#
# picts = []
# conts = []
#
# i = 1
#
# pfluor = cv.imread('Test\\' + name + str(i) + '_' + str(wl) + '.tiff', cv.IMREAD_GRAYSCALE)
# p0 = cv.imread('Test\\' + name + str(i) + '_0.tiff', cv.IMREAD_GRAYSCALE)
# p = pfluor - p0
# ma1 = np.max(p)
# pshow = (p * (255 / ma1)).astype(np.uint8)
# cv.namedWindow('picture', cv.WINDOW_NORMAL)
# cv.imshow('picture', pshow)
# cv.waitKey(0)
#
# cv.namedWindow('picture1', cv.WINDOW_NORMAL)
# for i in (range(10)):
#     blur = cv.GaussianBlur(p, (i * 2 + 1, i * 2 + 1), 0)
#     blurshow = (blur * (255 / ma1)).astype(np.uint8)
#
#     cv.imshow('picture1', blurshow)
#     cv.waitKey(0)


# m, th = cv.threshold(picts[56], 11, 255, cv.THRESH_TOZERO_INV)
# cv.namedWindow('14', cv.WINDOW_NORMAL)
# cv.imshow('14', (th * (255 / np.max(th))).astype(np.uint8))
# cv.waitKey(0)
# cv.destroyAllWindows()