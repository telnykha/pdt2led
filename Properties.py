__author__ = 'FiksII'
# -*- coding: utf-8 -*-


class Properties(object):
    skin_mean_intens = {}
    skin_sum_intens = {}
    tumor_sum_intens = {}
    tumor_mean_intens = {}
    tumor_max_intens = {}
    tumor_area = {}
    fone_sum_intens = None
    fone_mean_intens = None

    def __init__(self):
        self.skin_mean_intens = {}
        self.skin_sum_intens = {}
        self.tumor_sum_intens = {}
        self.tumor_mean_intens = {}
        self.tumor_max_intens = {}
        self.tumor_area = {}
        self.fone_sum_intens = None
        self.fone_mean_intens = None

    def make_string(self, wavelength):
        str = u""
        # try:
        # print (self.tumor_area[wavelength],self.tumor_mean_intens[wavelength],self.skin_mean_intens[wavelength],self.fone_mean_intens)

        if wavelength in self.tumor_area:
            if self.skin_mean_intens[wavelength] > 0:
                str = u"Площадь опухоли: %3.2f мм2 \nСр. интенс. опухоли: %3.2f a.u.\nСр. интенc. окр. ткани:" \
                      u" %3.2f a.u.\nУровень фона: %3.2f a.u." % (
                      self.tumor_area[wavelength], self.tumor_mean_intens[wavelength],
                      self.skin_mean_intens[wavelength], self.fone_mean_intens)
            else:
                str = u"Площадь опухоли: %3.2f мм2 \nСр. интенс. опухоли: %3.2f a.u.\n" \
                      u"Уровень фона: %3.2f a.u." % (
                      self.tumor_area[wavelength], self.tumor_mean_intens[wavelength], self.fone_mean_intens)
        return str
