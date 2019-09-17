__author__ = 'FiksII'
import Queue
# -*- coding: utf-8 -*-
import time

import numpy
from PyQt4 import QtCore
from win32com.client import constants

import Task


class WorkerHardware(QtCore.QThread):
    image_received = QtCore.pyqtSignal(object)
    data=None
    q=Queue.Queue()
    is_stop=False
    is_pause = False
    fluocontrollers=None
    image_size=None

    working_leds = []

    def __init__(self):
        QtCore.QThread.__init__(self)
        self.iFrame=0
        self.mutex=QtCore.QMutex()

    def run(self):
        while self.is_stop==False:
            task = Task.Task()
            image = None
            if self.fluocontrollers.storage_controller.GetCount() > 40:
                self.fluocontrollers.storage_controller.Clear()

            if self.fluocontrollers.storage_controller.GetCount() > 0:
                t1 = time.clock()
                Frame = self.fluocontrollers.fluo_controller.GetFrame()
                FrameData = Frame.GetData()
                frame = numpy.frombuffer(FrameData, numpy.uint32)
                image = frame.reshape(self.image_size)
                image = image.transpose()
                image = image.astype(numpy.uint16)  # uint8
                t2 = time.clock()
                LightingCode = Frame.GetLighting()
                frame_num = Frame.GetFrameNumber() - 1

                # task.wavelength = self.working_leds[frame_num % len(self.working_leds)]
                # print "frame_num, task.wavelength: ",frame_num, task.wavelength
                print "Time of getting image from the setup {t} s. Camera buffer {buffer} frames".format(t=t2-t1, buffer=self.fluocontrollers.storage_controller.GetCount())
                LightingStr = str(frame_num) + ". lighting_controller is: "

                if LightingCode == constants.LM_NONE:
                    LightingStr += " NONE"
                    task.wavelength = 0
                if LightingCode == constants.LM_IR:
                    LightingStr += " IR"
                    task.wavelength = 740
                if LightingCode == constants.LM_RED:
                    LightingStr += " RED"
                    task.wavelength = 660
                    # image=image*0
                    # image[200:250,330:380]=250
                    # self.iFrame=self.iFrame+1
                if LightingCode == constants.LM_GREEN:
                    pass
                if LightingCode == constants.LM_BLUE:
                    LightingStr += " BLUE"
                    task.wavelength = 400
                if LightingCode == constants.LM_UNK:
                    task.wavelength = -1
                    print u"Рассинхронизация кадров"
            else:
                image = None
                task.wavelength = None
                time.sleep(0.05)

            self.image_received.emit((task, image))

    def __del__(self):
        self.wait()
