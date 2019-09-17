__author__ = 'FiksII'
import sys
from PDTMainWindowProc import PDTMainWindowProc
from PyQt4 import QtGui
from win32api import GetSystemMetrics


# -*- coding: utf-8 -*-

def main():
    try:
        app = QtGui.QApplication(sys.argv)
        MainWindow = PDTMainWindowProc()
        #### MainWindow.resize(GetSystemMetrics(0),GetSystemMetrics(1)-100)
        MainWindow.setGeometry(5, 25, GetSystemMetrics(0), GetSystemMetrics(1)-100)
        MainWindow.show()
        sys.exit(app.exec_())
    except Exception as e:
        print (e.message)

if __name__ == '__main__':
    main()



