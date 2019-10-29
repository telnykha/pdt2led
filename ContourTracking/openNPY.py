import pyqtgraph
from pyqtgraph import FileDialog
import numpy as np

if __name__ == '__main__':
    app = pyqtgraph.GraphicsWindow().setBackground(None)
    filename = FileDialog().getOpenFileName(parent=app, caption='Choose the file',
                                            filter="MSE_*.npy").toUtf8()
    filename = ''.join([l for l in filename])
    vctMSE = np.load(filename)
    for MSE in vctMSE:
        print(str(MSE))