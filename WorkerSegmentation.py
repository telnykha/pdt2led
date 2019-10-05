# -*- coding: utf-8 -*-

from __future__ import division
__author__ = 'FiksII'

import time
import collections
from PyQt4 import QtCore
from grabCut import *
import cv2

class WorkerSegmentation(QtCore.QThread):
    image_segmented = QtCore.pyqtSignal(object)
    data=None
    q = collections.deque(maxlen=5)
    is_stop=False
    good_iterations={400:0, 660:0}
    total_iterations={400:0, 660:0}
    pauseCond = QtCore.QWaitCondition()
    sync = QtCore.QMutex()
    pause_state = False

    def __init__(self):
        QtCore.QThread.__init__(self)
        self.mutex=QtCore.QMutex()


    def ConvertTo8Bit(self, img, MaxVal):
        img = (img.astype(np.float) / MaxVal * 255).astype(np.uint8)
        return img

    def CalculateProperties(self, wavelength, experimental_data, parameters):
        Pr = experimental_data.properties

        if 'mask' in experimental_data.skin_data[wavelength]:
            skin_mask=experimental_data.skin_data[wavelength]['mask']
            skin_image=experimental_data.skin_data[wavelength]['image']
        else:
            skin_image = np.zeros((1,))
            skin_mask = np.zeros((1,))

        if skin_image is not None and skin_mask is not None:
            if skin_mask.sum()>0:
                Pr.skin_mean_intens[wavelength]=np.asarray(skin_image[skin_mask==1]).mean()
                Pr.skin_sum_intens[wavelength]=np.asarray(skin_image[skin_mask==1]).sum()
            else:
                Pr.skin_mean_intens[wavelength]=0
                Pr.skin_sum_intens[wavelength]=0
        else:
            Pr.skin_mean_intens[wavelength]=0
            Pr.skin_sum_intens[wavelength]=0

        tumor_mask = experimental_data.tumor_data[wavelength]['mask']
        tumor_image = experimental_data.tumor_data[wavelength]['image']

        if tumor_mask is not None and tumor_image is not None:
            if tumor_mask.sum()>0:
                Pr.tumor_sum_intens[wavelength] = np.sum(np.asarray(tumor_image[tumor_mask == 1]))
                Pr.tumor_mean_intens[wavelength] = np.mean(np.asarray(tumor_image[tumor_mask == 1]))
                Pr.tumor_max_intens[wavelength] = np.max(np.asarray(tumor_image[tumor_mask == 1]))

                contours, hierarchy = cv2.findContours(tumor_mask, cv2.RETR_LIST, cv2.CHAIN_APPROX_SIMPLE)
                Pr.tumor_area[wavelength] = 0
                for contour in contours:
                    Pr.tumor_area[wavelength] = Pr.tumor_area[wavelength] + cv2.contourArea(contour) * parameters.x_mm_in_pixel * parameters.y_mm_in_pixel
            else:
                Pr.tumor_sum_intens[wavelength] = 0
                Pr.tumor_mean_intens[wavelength] = 0
                Pr.tumor_area[wavelength] = 0
                Pr.tumor_max_intens[wavelength] = 0
        else:
                Pr.tumor_sum_intens[wavelength] = 0
                Pr.tumor_mean_intens[wavelength] = 0
                Pr.tumor_area[wavelength]=0
                Pr.tumor_max_intens[wavelength] = 0

        if experimental_data.image[0] is not None:
            Pr.fone_sum_intens = experimental_data.image[0].sum()
            Pr.fone_mean_intens = experimental_data.image[0].mean()
        else:
            Pr.fone_sum_intens = 0
            Pr.fone_mean_intens = 0

    def set_value_for_all_dictionary(dictionary,value):
        for key in dictionary:
            dictionary[key] = value

    def resume(self):
        self.sync.lock()
        self.pause_state = False
        self.sync.unlock()
        self.pauseCond.wakeAll()

    def pause(self):
        self.sync.lock()
        self.pause_state = True
        self.sync.unlock()
    # work with "0" image
    def processBackground(self, experimental_data, parameters, monitoring_data):
        experimental_data.image_cleared[0] = experimental_data.image[0]
        experimental_data.image_cleared_with_contours_rbg[0] = cv2.cvtColor(experimental_data.image[0],
                                                                            cv2.COLOR_GRAY2RGB)
        # этот код служит для поиска области в случае если не определен регион и включен лазер. или если включен режим слежения за терапевтическим лазером.
        if (parameters.tumor_shadowing_type == "glare" and "region not defined" in experimental_data.mode) and "laser on" in experimental_data.mode and len(
                experimental_data.image_glare_prev[0]) > 0:
            experimental_data.image_cleared[0] = experimental_data.image_glare_prev[0][0]
            experimental_data.image_cleared_with_contours_rbg[0] = cv2.cvtColor(
                experimental_data.image_glare_prev[0][0], cv2.COLOR_GRAY2RGB)

            for wl in (400, 660):
                if wl in monitoring_data.tumor_area and len(
                        monitoring_data.tumor_area[wl]) > 0 and "region defined" in experimental_data.mode:
                    glare_area = monitoring_data.tumor_area[wl][-1]
                    current_level = find_glare_level_for_image(experimental_data.image_glare_prev[0][0], glare_area,
                                                               parameters.x_mm_in_pixel, parameters.y_mm_in_pixel)
                    contour = contour_from_level(experimental_data.image_glare_prev[0][0], current_level)
                else:
                    contour = contour_from_level(experimental_data.image_glare_prev[0][0],
                                                 experimental_data.max_image_value - parameters.glare_parameters[
                                                     "dmin_glare_value"])
                tumor_poly = [[c[0][0], c[0][1]] for c in contour]
                if "mask" not in experimental_data.tumor_data[wl]:
                    experimental_data.tumor_data[wl]["mask"] = np.zeros(experimental_data.image_cleared[0].shape,
                                                                        np.uint8)

                # Сделать смещение маски кожи
                experimental_data.tumor_data[wl]["poly"] = tumor_poly
                experimental_data.tumor_data[wl]["mask"][:] = 0
                cv2.fillPoly(experimental_data.tumor_data[wl]["mask"],
                             [np.asarray(experimental_data.tumor_data[wl]["poly"])], 1)
        #work with 740 nm
    def process740(self, experimental_data):
        experimental_data.image_cleared[740] = experimental_data.image[740].astype(np.uint16)
        experimental_data.image_cleared[740] = self.ConvertTo8Bit(experimental_data.image_cleared[740],
                                                                  experimental_data.max_image_value)
        #update mask image 

    def run(self):
        while self.is_stop == False:
            if bool(self.q):
                qtask = self.q.popleft()
                task = qtask[0]
                experimental_data = qtask[1]
                parameters = qtask[2]
                wavelength = task.wavelength
                monitoring_data = qtask[3]
                #wait until experimental_data is locked
                while(experimental_data.is_locked):
                    time.sleep(0.1)
                #process backeground
                if wavelength == 0:
                    self.processBackground(experimental_data, parameters, monitoring_data)
                if wavelength == 740:
                        self.process740(experimental_data)
                #process 660 and 400 nm
                if wavelength in (660,400):
                    t1 = time.clock()
                    self.total_iterations[wavelength] += 1

                    image = experimental_data.image[wavelength].astype(np.float)

                    # Вычитание фона
                    if experimental_data.image[0] is not None:
                        experimental_data.image_cleared[wavelength] = image - parameters.use_black_image * experimental_data.image[0]
                        experimental_data.image_cleared[wavelength][experimental_data.image_cleared[wavelength] < 0] = 0
                    else:
                        experimental_data.image_cleared[wavelength] = image
                    # преобразование полутонового изображение в многоцветоное
                    experimental_data.image_cleared[wavelength] = experimental_data.image_cleared[wavelength].astype(np.uint16)
                    experimental_data.image_cleared_with_contours_rbg[wavelength] = cv2.cvtColor(experimental_data.image_cleared[wavelength].copy(),cv2.COLOR_GRAY2RGB)

                    self.good_iterations[wavelength]=self.good_iterations[wavelength]+1
                    #process monitoring
                    if "monitoring" not in experimental_data.mode:
                        # Вычисление опухоли
                        if "region defined" in experimental_data.mode:
                            # import ipdb; ipdb.set_trace()
                            if "poly" in experimental_data.skin_data[wavelength]:
                                cv2.polylines(experimental_data.image_cleared_with_contours_rbg[wavelength],[np.array(experimental_data.skin_data[wavelength]["poly"], np.int32)],False,experimental_data.skin_data["color"],experimental_data.skin_data["thickness"])
                                experimental_data.skin_data[wavelength]['image'] = experimental_data.image_cleared[wavelength]*experimental_data.skin_data[wavelength]['mask']
                                experimental_data.skin_data[wavelength]['image'] = experimental_data.skin_data[wavelength]['image'].astype(np.uint16)

                            cv2.polylines(experimental_data.image_cleared_with_contours_rbg[wavelength],[np.array(experimental_data.tumor_data[wavelength]["poly"], np.int32)],False,experimental_data.tumor_data["color"],experimental_data.tumor_data["thickness"])
                            experimental_data.tumor_data[wavelength]['image'] = experimental_data.image_cleared[wavelength]*experimental_data.tumor_data[wavelength]['mask']
                            experimental_data.tumor_data[wavelength]['image'] = experimental_data.tumor_data[wavelength]['image'].astype(np.uint16)

                    if "monitoring" in experimental_data.mode:
                        if "region defined" in experimental_data.mode:

                            if "mask" in experimental_data.skin_data[wavelength]:
                                experimental_data.skin_data[wavelength]['image'] = experimental_data.image_cleared[wavelength] * experimental_data.skin_data[wavelength]['mask']
                                experimental_data.skin_data[wavelength]['image'] = experimental_data.skin_data[wavelength]['image'].astype(np.uint16)
                                cv2.polylines(experimental_data.image_cleared_with_contours_rbg[wavelength],[np.array(experimental_data.skin_data[wavelength]["poly"], np.int32)],False,experimental_data.skin_data["color"],experimental_data.skin_data["thickness"])

                            experimental_data.tumor_data[wavelength]['image'] = experimental_data.image_cleared[wavelength] * experimental_data.tumor_data[wavelength]['mask']
                            experimental_data.tumor_data[wavelength]['image'] = experimental_data.tumor_data[wavelength]['image'].astype(np.uint16)
                            cv2.polylines(experimental_data.image_cleared_with_contours_rbg[wavelength],[np.array(experimental_data.tumor_data[wavelength]["poly"], np.int32)],False,experimental_data.tumor_data["color"],experimental_data.tumor_data["thickness"])

                    # Наложение
                    if experimental_data.image_cleared[740] is not None:
                        if "region defined" in experimental_data.mode and experimental_data.tumor_data[wavelength]['image'] is not None and experimental_data.tumor_data[wavelength]['mask'].sum()>0:
                            #TODO: понять почему надо инвертировать изображение
                            if wavelength in monitoring_data.tumor_mean:
                                max_value_monitoring = max(sum(monitoring_data.tumor_max.values(), []))
                                max_value = max(experimental_data.tumor_data[wavelength]['image'][experimental_data.tumor_data[wavelength]['mask'] == 1])
                                min_value = min(experimental_data.tumor_data[wavelength]['image'][experimental_data.tumor_data[wavelength]['mask'] == 1])
                            else:
                                max_value_monitoring = max(experimental_data.tumor_data[wavelength]['image'][experimental_data.tumor_data[wavelength]['mask'] == 1])
                                max_value = max(experimental_data.tumor_data[wavelength]['image'][experimental_data.tumor_data[wavelength]['mask'] == 1])
                                min_value = min(experimental_data.tumor_data[wavelength]['image'][experimental_data.tumor_data[wavelength]['mask'] == 1])
#
#                             # print max_value_monitoring, max_value, min_value
# #
                            tumor_image = (experimental_data.tumor_data[wavelength]['image'].astype(np.float) - min_value) / (max_value_monitoring - min_value)
                            tumor_image[tumor_image < 0] = 0
                            tumor_image[tumor_image > 1] = 1
                            tumor_image = self.ConvertTo8Bit(tumor_image, 1)
                            # tumor_image = tumor_image.astype(np.float) / 255 * max_value
                            # tumor_image = self.ConvertTo8Bit(tumor_image, max_value)

                            # print tumor_image.max(), tumor_image.min()

                            tumor_color = cv2.cvtColor(cv2.applyColorMap(tumor_image, cv2.COLORMAP_JET),cv2.COLOR_BGR2RGB)  #experimental_data.max_image_value-
                            experimental_data.image_superposition_rgb[wavelength] = cv2.cvtColor(experimental_data.image_cleared[740],cv2.COLOR_GRAY2RGB)
                            experimental_data.image_superposition_rgb[wavelength][experimental_data.tumor_data[wavelength]['mask'] == 1] = tumor_color[experimental_data.tumor_data[wavelength]['mask'] == 1]

                        else:
                            experimental_data.image_superposition_rgb[wavelength] = cv2.cvtColor(experimental_data.image_cleared[740], cv2.COLOR_GRAY2RGB)
                    else:
                        experimental_data.image_superposition_rgb[wavelength] = None

                    t2 = time.clock()
                    #print "Processing image wavelength={wavelength}, {t} s. Pool length {len_pool}".format(t=t2-t1, wavelength=wavelength, len_pool=len(self.q))
                    print len(experimental_data.image[740])


                    if "region defined" in experimental_data.mode:
                        self.CalculateProperties(wavelength, experimental_data, parameters)

                t2 = time.clock()
                self.image_segmented.emit((task))

        self.q.clear()

    def __del__(self):
        self.wait()

    def addjob(self,jobdata):
        self.q.append(jobdata)

    def clearjob(self):
        self.q.clear()

def find_glare_level_for_image(image, glare_area, x_mm_in_pixel, y_mm_in_pixel):
    min_level = 0.0
    max_level = image.max()
    cont = True
    while cont:
        current_level = (max_level + min_level) / 2
        contour = contour_from_level(image,current_level)
        current_area = cv2.contourArea(contour)*x_mm_in_pixel*y_mm_in_pixel

        if current_area > glare_area:
            min_level = current_level
        else:
            max_level = current_level

        if (max_level - min_level) < 1:
            cont = False

    return current_level


def contour_from_level(image,current_level):
    mask = np.zeros(image.shape,np.uint8)
    mask[image >= current_level] = 1
    contours, hierarchy = cv2.findContours(mask, cv2.RETR_LIST, cv2.CHAIN_APPROX_SIMPLE)

    contours.sort(key=lambda x: cv2.contourArea(x))
    contour = contours[-1]
    return contour
