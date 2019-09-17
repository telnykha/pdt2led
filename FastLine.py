__author__ = 'FiksII'

import pyqtgraph
import numpy

class FastLine(pyqtgraph.QtGui.QGraphicsPathItem):
    def __init__(self, x, y, pen):
        """x and y are 1D arrays representing the line's coordinates"""
        x=numpy.asarray(x)
        y=numpy.asarray(y)
        self.path = pyqtgraph.arrayToQPath(x.flatten(), y.flatten())
        pyqtgraph.QtGui.QGraphicsPathItem.__init__(self, self.path)
        self.setPen(pyqtgraph.mkPen(pen))
    def shape(self): # override because QGraphicsPathItem.shape is too expensive.
        return pyqtgraph.QtGui.QGraphicsItem.shape(self)
    def boundingRect(self):
        return self.path.boundingRect()