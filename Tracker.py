import cv2
class Tracker(object):
    CurrentImage = None
    PrevImage    = None
    Points       = None
    Mask         = None
    #copy points
    def __init__(self, p):
        Points = p
    #track points on the image
    def trak(self, image):
        if self.PrevImage is None:
            self.PrevImage = image
        else:
            self.PrevImage = self.CurrentImage
            self.CurrentImage = image
