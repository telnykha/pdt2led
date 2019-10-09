# -*- coding: utf-8 -*-
import numpy as np
import cv2
from ContourTracking import ContourTracking
class Tracker(object):
    CurrentImage = None
    PrevImage    = None
    Points       = None
    SPoints      = None
    Mask         = None
    Result       = None
    #copy points
    def __init__(self):
        self.winSize  = (90,90)
        self.maxLevel = 3
        self.delta    = 30
    #track points on the image
    def track(self, image):
        if len(self.Points) == 0:
            return
        if self.PrevImage is None:
            self.PrevImage = image
            self.CurrentImage = image
            self.Mask      = np.zeros(self.PrevImage.shape[:2], dtype=np.uint8)
            return
        else:
            self.PrevImage = self.CurrentImage
            self.CurrentImage = image
            p = np.array(self.Points, np.float32).reshape(-1, 2)
            shift = ContourTracking.trackOneStepMeanShift(self.PrevImage, p, self.CurrentImage, self.winSize, self.maxLevel, self.delta)
            if not shift == []:  # everything OK, go to usual loop, null counters
                 self.Result = (p + shift)
                 self.Points = self.Result.tolist()
                 self.Mask = np.zeros(self.PrevImage.shape[:2], dtype=np.uint8)
                 cv2.fillPoly(self.Mask, [np.array(self.Points, np.int32)], 1)
    def Clear(self):
        self.Mask = None
        self.CurrentImage = None
        self.Points = None
        self.PrevImage = None