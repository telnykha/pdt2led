#sys.path.append(sys.path[-1]+'\\ContourTracking')

from funcs import *

if __name__ == '__main__':

    trackSeriesCompare(winSize=(30, 30), maxLevel=6, delta=30, maxNumberBadPictures=10, compare=True)
