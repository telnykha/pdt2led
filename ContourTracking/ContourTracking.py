from PyQt5 import QtWidgets
import sys

from funcs import *

if __name__ == '__main__':
    app = QtWidgets.QApplication(sys.argv)
    filename, _ = QtWidgets.QFileDialog.getOpenFileName(parent=None,
                                                        caption='Choose the first series file with wl!=0 && wl!=740',
                                                        filter="*_400.tiff *_660.tiff")
    filename = ''.join([l if not l == '/' else '\\' for l in filename])
    fullname = filename[:-10]
    wl = int(filename[-8:-5])

    path = fullname[:]
    for l in fullname[::-1]:
        if l == '\\':
            break
        path = path[:-1]

    numOfPictures, _ = QtWidgets.QFileDialog.getOpenFileName(parent=None,
                                                             caption='Choose the last series file with the same wl',
                                                             directory=path,
                                                             filter="*_" + str(wl) + ".tiff")
    numOfPictures = int(numOfPictures[len(fullname):-9])
    trackSeriesCompare(winSize=(90, 90), maxLevel=6, delta=30, maxNumberBadPictures=10,
                       maxDotsOut=5, compare=True, name=fullname, wl=wl, end=numOfPictures)
