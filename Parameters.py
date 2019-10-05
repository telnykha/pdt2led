__author__ = 'FiksII'
# -*- coding: utf-8 -*-
import codecs
import os
from win32com.shell import shell, shellcon


class Parameters(object):

    def __init__(self):
        self.x_mm_in_pixel = 0.09
        self.y_mm_in_pixel = 0.09

        self.TimerLength = 50  # None
        self.is_logging = False  # None
        self.TimeBegin = 1  # None
        self.full_name = ""
        self.birthday_date = ""
        self.base_logging_folder = ""
        self.use_black_image = 0
        self.glare_coeff = 1.5
        self.glare_min_value = 0
        self.exposition = {}
        self.exposition[400] = 0
        self.exposition[660] = 0
        self.exposition[740] = 0
        self.exposition[0] = 0
        self.lighting_period = 0
        self.camera_exposition = 0
        self.camera_gain = 0
        self.camera_binning = None
        self.camera_bits = None
        self.image_size = None
        self.save_full_protocol = None

        self.tumor_shadowing_type = "None"

        self.all_binnings = {}

        self.grabcut_tumor_coeff = 1
        self.grabcut_skin_coeff = 0.25
        self.skin_good_iterations_calculate = {660: 2, 400: 2}  # сколько раз автоматически определять кожу
        self.tumor_good_iterations_rectangle_calculate = {660: 5, 400: 5}  # сколько раз автоматически определять прямоугольник
        #параметры обнаружения засветки терапевтическим лазером.
        #excess_count - пороговое число завеченных точек
        #dmin_glare_value - порог яркости пикселя
        self.glare_parameters = {"excess_count": 1000, "dmin_glare_value": 1000}

        self.alarm_levels = {660: 10, 400: 10}

        self.calibration_distance = 85  # mm
        self.livemode_leds = []
        self.additional_perion_of_single_frame = 1e6

        self.use_autolevel = None
        self.flip_images = True

        self.folder = (shell.SHGetFolderPath(0, shellcon.CSIDL_PERSONAL, None, 0) + u"\\Флуовизор\\").encode('cp1251', 'ignore')
        self.filename =  "Parameters.cfg"


    def save(self, Folder):
        try:
            Folder = Folder.encode('cp1251', 'ignore')
            if not os.path.exists(Folder):
                os.makedirs(Folder)
            text_file = codecs.open(Folder + "\\Parameters.txt", "w", "utf-8")
            text_file.writelines(u"Экспозиция 400 нм: %6.4f с\n" % self.exposition[400])
            text_file.writelines(u"Экспозиция 660 нм: %6.4f с\n" % self.exposition[660])
            text_file.writelines(u"Экспозиция 740 нм: %6.4f с\n" % self.exposition[740])
            text_file.writelines(u"Экспозиция без диода: %6.4f с\n" % self.exposition[0])
            text_file.writelines(u"Экспозиция камеры: %6.4f с\n" % self.camera_exposition)
            text_file.writelines(u"Период переключения диодов: %6.4f с\n" % self.lighting_period)
            text_file.writelines(u"Усиление камеры: %6.4f  дБ с\n" % self.camera_gain)
            text_file.writelines(u"Битность кадра: %d \n" % self.camera_bits)
            text_file.writelines(u"Вычитание  <<темного>> кадра: %d \n" % self.use_black_image)

            text_file.close()
        except:
            pass

if __name__ == '__main__':
    param = Parameters()
    param.save("")