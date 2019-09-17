__author__ = 'FiksII'
# -*- coding: utf-8 -*-


from PDTMainWindow import *
import cPickle
import numpy
import cPickle


class PDTMainWindowProcAdditional(Ui_Form):
    def led600_clicked(self):
        if self.pStart.isChecked()==False:
            self.wLed660.toggleValue()

    def led400_clicked(self):
        if self.pStart.isChecked()==False:
            self.wLed400.toggleValue()

    def led740_clicked(self):
        if self.pStart.isChecked()==False:
            self.wLed740.toggleValue()

    def ConvertTo8Bit(self,img,MaxVal):
        img=(img.astype(numpy.float)/MaxVal*255).astype(numpy.uint8)
        return img

    def save_parameters(self):
        f = open(self.parameters.filename,'wt')
        cPickle.dump(self.parameters,f,cPickle.HIGHEST_PROTOCOL)
        f.close()

    def load_parameters(self):
        f = open(self.parameters.filename,'rt')
        tmp = cPickle.load(f)
        f.close()
        return tmp
