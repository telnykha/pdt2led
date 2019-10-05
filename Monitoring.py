__author__ = 'FiksII'
# -*- coding: utf-8 -*-

import datetime
import xlwt

class Monitoring:
    # t = []
    # tumor_mean = {}
    # tumor_area = {}
    # tumor_max = {}
    # dt = []
    # frames_count = {}
    # skin_mean_intens = {}
    # fone_mean_intens = {}
    # contrast = {}
    # burn = {}
    #
    # stopwatch_laser_on = {}
    #
    # next_beep_value = None
    # next_beep_duration = 60 #s
    # beep_duration = 1.5  # s
    # max_excess_coeff = 1.5
    # max_diff = 10
    # max_dt = 5

    def __init__(self):
        self.t = {}
        self.dt = {}
        self.tumor_mean = {}
        self.tumor_area = {}
        self.tumor_max = {}
        self.frames_count = {}
        self.stopwatch_laser_on = {}

        self.t_start = None
        self.stopwatch_laser_on = {}
        self.stopwatch_laser_on['last_time'] = None
        self.stopwatch_laser_on['current_value'] = None
        self.frames_count = {}
        self.skin_mean_intens = {}
        self.fone_mean_intens = {}
        self.contrast = {}
        self.burn = {}

        self.next_beep_value = None
        self.next_beep_duration = None #s
        self.is_reset_beeping = None
        self.beep_duration = 1.5  # s
        self.max_excess_coeff = 1.5
        self.max_diff = 10
        self.max_dt = 5

    def append(self, prop, wavelenghts=None):
        if wavelenghts is None:
            wavelenghts = prop.tumor_area.keys()

        if not self.t:
            self.t_start = datetime.datetime.now()

        for wavelength in wavelenghts:
            if not (wavelength in self.tumor_area.keys()):
                self.tumor_area[wavelength] = []
                self.tumor_mean[wavelength] = []
                self.tumor_max[wavelength] = []
                self.t[wavelength] = []
                self.dt[wavelength] = []
                self.skin_mean_intens[wavelength] = []
                self.contrast[wavelength] = []
                self.burn[wavelength] = []

            if len(self.tumor_mean[wavelength]) > 1:
                t_curr = (datetime.datetime.now() - self.t_start).total_seconds()
                diff_t = (datetime.datetime.now() - self.t[wavelength][-1]).total_seconds()
                dlevel = prop.tumor_mean_intens[wavelength] \
                         - self.tumor_mean[wavelength][-1]

                diff = abs(dlevel/diff_t)

                if diff < self.max_diff or diff_t >= self.max_dt:
                    self.t[wavelength].append(datetime.datetime.now())
                    self.dt[wavelength].append(t_curr)

                    self.tumor_mean[wavelength].append(prop.tumor_mean_intens[wavelength])
                    self.tumor_area[wavelength].append(prop.tumor_area[wavelength])
                    self.skin_mean_intens[wavelength].append(prop.skin_mean_intens[wavelength])
                    self.tumor_max[wavelength].append(prop.tumor_max_intens[wavelength])
            else:
                self.t[wavelength].append(datetime.datetime.now())
                self.dt[wavelength].append((self.t[wavelength][-1] - self.t_start).total_seconds())
                self.tumor_mean[wavelength].append(prop.tumor_mean_intens[wavelength])
                self.tumor_area[wavelength].append(prop.tumor_area[wavelength])
                self.skin_mean_intens[wavelength].append(prop.skin_mean_intens[wavelength])
                self.tumor_max[wavelength].append(prop.tumor_max_intens[wavelength])

            print self.tumor_mean[wavelength][-1], self.tumor_mean[wavelength][0]
            print self.tumor_mean[wavelength]

            if self.skin_mean_intens[wavelength][-1] > 0:
                self.contrast[wavelength].append(self.tumor_mean[wavelength][-1]/self.skin_mean_intens[wavelength][-1])
            burn = 1 - self.tumor_mean[wavelength][-1]/self.tumor_mean[wavelength][0]
            self.burn[wavelength].append(burn)

    def frames_counter(self, wavelenghts):
        for wavelength in wavelenghts:
            if not (wavelength in self.frames_count.keys()):
                self.frames_count[wavelength] = 0

            self.frames_count[wavelength] += 1

    def start(self):
        if self.stopwatch_laser_on['current_value'] is None:
            self.stopwatch_laser_on['last_time'] = datetime.datetime.now()
            self.stopwatch_laser_on['current_value'] = 0

    def stop(self):
        pass

    def reset(self):
        self.__init__()
        self.stopwatch_laser_on['last_time'] = datetime.datetime.now()
        self.stopwatch_laser_on['current_value'] = 0
        self.next_beep_value = self.next_beep_duration

    def is_empty(self):
        return len(self.t.keys()) == 0

    def save(self, parameters, Folder):
        if not self.is_empty():
            font0 = xlwt.Font()
            font0.name = 'Times New Roman'
            font0.colour_index = 1
            font0.bold = True
            style0 = xlwt.XFStyle()
            style1 = xlwt.XFStyle()

            wb = xlwt.Workbook()

            keys = list(self.tumor_area.keys())
            for j in range(len(keys)):
                wavelength = keys[j]
                ws = wb.add_sheet(unicode('Results ' + unicode(str(wavelength)) + ' nm'))
                ws.write(0, 0, parameters.full_name, style0)
                ws.write(0, 1, parameters.birthday_date, style0)
                ws.write(1, 1, u'Время', style0)
                ws.write(1, 2, u'Время с начала старта, c', style0)
                ws.write(1, 3, u'Интенсивность, a.u.', style0)

                for i in range(len(self.t[wavelength])):
                    ws.write(i + 2, 1, unicode(str(self.t[wavelength][i])), style0)
                    ws.write(i + 2, 2, self.dt[wavelength][i], style0)
                    ws.write(i + 2, 3, self.tumor_mean[wavelength][i], style0)

            wb.save(Folder + 'monitoring_result.xls')

            pass
