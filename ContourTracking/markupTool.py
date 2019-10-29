from ContourTracking import *
from directory_processing import directory_processing

def markupSeries(fullname, directory, numFrames):
    for i in range(1, numFrames):
        if (i - 1) % frequency == 0:
            pict = getPictTrue(fullname, i, 740)
            np.save(directory + '\\' + 'cont' + str((i - 1) / frequency) + '.npy',
                    contourManual((pict *
                                  (maxIntensity /
                                   max(np.max(pict), 1).astype(np.float32))).astype(np.uint8)))


if __name__ == '__main__':
    fullname, directory, numFrames = directory_processing(is740only=True)
    markupSeries(fullname, directory, numFrames)