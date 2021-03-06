﻿__author__ = 'FiksII'
# -*- coding: utf-8 -*-

from PDTMainWindow import *
import sys
import QLed
from PyQt4 import QtGui, QtCore, Qt
import WorkerHardware
import WorkerSegmentation
import ExperimentalData
import Monitoring
import time
import Parameters
import datetime
import cPickle
from win32com.client import constants
import numpy
import pythoncom
from grabCut import *
import FastLine
import win32api
import tifffile as tiff
import copy
import winsound
import gzip
import FluoControllers
import pyqtgraph
import threading
import Queue
import itertools
import os



DEBUG_MODE = True

# engine = PyQtEngine()
# pyqtgraph.functions.USE_WEAVE = True

manual_input_parameters = {}

def background(f):
    def bg_f(*a, **kw):
        q = Queue.Queue()
        kw["queue_result"] = q
        threading.Thread(target=f, args=a, kwargs=kw).start()
        return q.get()
    return bg_f

class PDTMainWindowProc(QtGui.QWidget):
    worker_hardware = WorkerHardware.WorkerHardware()

    worker_segmentation = WorkerSegmentation.WorkerSegmentation()
    experimental_data = ExperimentalData.ExperimentalData()
    parameters = Parameters.Parameters()
    monitoring = Monitoring.Monitoring()

    logging_data_storage = {}

    def __init__(self, parent=None):
        super(PDTMainWindowProc, self).__init__(parent)
        self.ui = Ui_Form()
        self.ui.setupUi(self)

        self.fluocontrollers = None
        try:
            self.fluocontrollers = FluoControllers.FluoControllers()
            self.worker_hardware.fluocontrollers = self.fluocontrollers
        except:
            errorstr = u"Невозможно получить управление камерой. Скорее всего, запущена другая версия программы."
            QtGui.QMessageBox.about(self, "Warning", errorstr)
            self.change_param_working_state(False)

        # Form.setFixedSize(1920,1000)
        self.load_parameters()
        # self.ui.groupBoxFluor.setStyleSheet("QGroupBox {border:1px solid rgb(0, 0, 0); }")
        # self.ui.groupBoxMonitoring.setStyleSheet("QGroupBox {border:1px solid rgb(0, 0, 0); }")

        #self.ui.graph_image_superposition.ui.histogram.hide()
        self.ui.graph_image_superposition.ui.roiBtn.hide()
        self.ui.graph_image_superposition.ui.menuBtn.hide()
        self.ui.graph_image.ui.roiBtn.hide()
        self.ui.graph_image.ui.menuBtn.hide()


        self.ui.widget_led660.setOnColour(QLed.QLed.Red)
        self.ui.widget_led660.clicked.connect(self.ui.widget_led660.toggleValue)
        self.ui.widget_led660.toggleValue()

        self.ui.widget_led740.setOnColour(QLed.QLed.Red)
        self.ui.widget_led740.clicked.connect(self.ui.widget_led740.toggleValue)
        self.ui.widget_led740.toggleValue()

        self.ui.widget_led400.setOnColour(QLed.QLed.Blue)
        self.ui.widget_led400.clicked.connect(self.ui.widget_led400.toggleValue)
        self.ui.widget_led400.toggleValue()

        str = os.getcwdu() + '\\Additional\\RecordOFF.png'
        self.ui.pRecord.setIcon(QtGui.QIcon(str))
        self.ui.pRecord.setIconSize(QtCore.QSize(32, 32))

        str = os.getcwdu() + '\\Additional\\photo.png'
        self.ui.pSaveState.setIcon(QtGui.QIcon(str))
        self.ui.pSaveState.setIconSize(QtCore.QSize(60, 60))

        self.ui.pSaveState.clicked.connect(self.single_log_shot)

        self.ui.pRecord.clicked.connect(self.push_record_clicked)
        self.ui.pStart.clicked.connect(self.push_start_clicked)

        self.ui.pStartMonitoring.clicked.connect(self.push_start_monitoring_clicked)
        self.ui.pResetMonitoring.clicked.connect(self.push_reset_monitoring_clicked)
        self.ui.pStopMonitoring.clicked.connect(self.push_stop_monitoring_clicked)

        self.ui.combo_selected_image.currentIndexChanged.connect(self.combo_selected_image_changed)

        self.ui.edit_alarm400.textEdited.connect(self.edit_alarm_changed)
        self.ui.edit_alarm660.textEdited.connect(self.edit_alarm_changed)
        self.ui.e400Exposition.editingFinished.connect(self.exposition_changed)
        self.ui.e660Exposition.editingFinished.connect(self.exposition_changed)
        self.ui.e740Exposition.editingFinished.connect(self.exposition_changed)
        self.ui.ePeriod.editingFinished.connect(self.exposition_changed)
        self.ui.eCameraExposition.editingFinished.connect(self.exposition_changed)

        self.ui.cNoneNormilize.clicked.connect(self.check_use_black_image_clicked)

        self.ui.pBlueSingle.clicked.connect(self.push_single_frame_400_clicked)
        self.ui.pRedSingle.clicked.connect(self.push_single_frame_660_clicked)
        self.ui.pIRSingle.clicked.connect(self.push_single_frame_740_clicked)
        self.ui.pNoneSingle.clicked.connect(self.push_single_frame_black_clicked)

        self.ui.graph_image.getImageItem().scene().sigMouseMoved.connect(self.mouse_moved_on_graph_image)
        self.ui.pCalibration.clicked.connect(self.push_calibration_clicked)
        self.ui.pLiveMode.clicked.connect(self.push_livemode_clicked)
        self.ui.spinFrameNumber.valueChanged.connect(self.change_experimental_frame)
        self.ui.pSaveResults.clicked.connect(self.save_results_folder_dialog)

        self.ui.lcdNumber.setDigitCount(8)
        self.clock_timer = QtCore.QTimer(self)
        self.clock_timer.timeout.connect(self.update_time)
        self.ui.pManual.clicked.connect(self.push_manual_mode_clicked)
        self.ui.pResetRegion.clicked.connect(self.reset_region)

        self.ui.groupBeep.setEnabled(True)
        self.ui.pStartMonitoring.setEnabled(True)
        self.ui.pStopMonitoring.setEnabled(False)
        self.ui.pResetMonitoring.setEnabled(False)

        self.ui.label_status.setText(u"ВЫКЛ")
        self.ui.label_properties.setText("")

        self.parameters.all_binnings = {"1x1 (1280x960)": (960, 1280, constants.BIN_NONE),
                                        # "1x2 (1280x480)": (480, 1280, constants.BIN_1x2),
                                        # "1x3 (1280x320)": (320, 1280, constants.BIN_1x3),
                                        # "1x4 (1280x240)": (240, 1280, constants.BIN_1x4),
                                        # "1x4* (1280x240)": (240, 1280, constants.BIN_1x4V2)
                                        }

        self.ui.pLoadExperiment.clicked.connect(self.load_experiment)

        binning_keys = list(self.parameters.all_binnings.keys())
        binning_keys.sort()
        for key in binning_keys:
            self.ui.cCameraBinning.addItem(unicode(key))

        self.experimental_data_storage = {}
        self.experimental_data.mode.add("region not defined")
        self.experimental_data.mode.add("laser off")
        self.check_use_black_image_clicked()

        self.logging_data_storage = {}
        self.logging_data_storage['info'] = []

        self.parameters.livemode_leds = [(constants.LM_IR), (constants.LM_RED), (constants.LM_BLUE), (constants.LM_RED | constants.LM_BLUE), (constants.LM_NONE)]
        self.livemode_leds_enumerator = itertools.cycle(self.parameters.livemode_leds)
        self.livemode_block_buttons = False

        # self.set_permissions(os.path.dirname(os.path.abspath(__file__)))
        # self.set_permissions(self.parameters.filename)
        self.worker_hardware.image_received.connect(self.image_received)
        self.worker_segmentation.image_segmented.connect(self.image_segmented)
        self.worker_segmentation.start()


    def combo_selected_image_changed(self):
        self.update_data_on_screen(image_changed=True)

    def set_permissions(self, filename):
        # import win32security
        # import ntsecuritycon as con
        #
        # userx, domain, type = win32security.LookupAccountName("", "User X")
        # usery, domain, type = win32security.LookupAccountName("", "User Y")
        #
        # sd = win32security.GetFileSecurity(filename, win32security.DACL_SECURITY_INFORMATION)
        # dacl = sd.GetSecurityDescriptorDacl()  # instead of dacl = win32security.ACL()
        #
        # dacl.AddAccessAllowedAce(win32security.ACL_REVISION, con.FILE_GENERIC_READ | con.FILE_GENERIC_WRITE, userx)
        # dacl.AddAccessAllowedAce(win32security.ACL_REVISION, con.FILE_ALL_ACCESS, usery)
        #
        # sd.SetSecurityDescriptorDacl(1, dacl, 0)  # may not be necessary
        # win32security.SetFileSecurity(filename, win32security.DACL_SECURITY_INFORMATION, sd)
        os.chmod(filename, 0o644)


    def closeEvent(self, event):
        if self.ui.pStart.isChecked():
            self.fluorcontroller_stop()  # let the window close

        self.worker_segmentation.is_stop = True
        self.worker_hardware.is_stop = True
        self.clock_timer.stop()

        self.worker_segmentation.quit()
        self.worker_hardware.quit()
        if self.fluocontrollers is not None:
            self.fluocontrollers.__del__()


    def push_record_clicked(self):
        if self.ui.pRecord.isChecked():
            str = os.getcwdu() + '\\Additional\\RecordON.png'
            self.ui.pRecord.setIcon(QtGui.QIcon(str))
            self.parameters.is_logging = True
            self.parameters.TimeBegin = time.clock()
            self.parameters.TimerLength = self.ui.sTimer.value()
            self.parameters.base_logging_folder = unicode(self.ui.eLoggingFolder.text())
            self.parse_parameters_from_form()
            self.parameters.save(self.parameters.base_logging_folder+ "\\" + self.parameters.full_name)
            self.logging_data_storage['parameters'] = copy.copy(self.parameters)

            log_result = self.logging()
            if not log_result:
                errorstr = "Недостаточно места на диске. Сохранение будет отменено"
                QtGui.QMessageBox.about(self.ui.tabWidget, "Warning", errorstr)
                self.ui.pRecord.setChecked(False)
                self.push_record_clicked()
        else:
            str = os.getcwdu() + '\\Additional\\RecordOFF.png'
            self.ui.pRecord.setIcon(QtGui.QIcon(str))
            self.parameters.is_logging = False

            # pickleFile = open(self.parameters.base_logging_folder + "\\" + self.parameters.full_name + "\\Full\\logging_storage.pkl",'wb')
            # pickle.dump(self.logging_data_storage, pickleFile, pickle.HIGHEST_PROTOCOL)
            # pickleFile.close()

    def set_parameters_to_form(self):
        self.ui.edit_full_name.setText(str(self.parameters.full_name))
        self.ui.e400Exposition.setText(str(self.parameters.exposition[400]))
        self.ui.e660Exposition.setText(str(self.parameters.exposition[660]))
        self.ui.e740Exposition.setText(str(self.parameters.exposition[740]))
        self.ui.ePeriod.setText(str(self.parameters.lighting_period))
        self.ui.eCameraGain.setText(str(self.parameters.camera_gain))

        if self.parameters.isNormalize == 1:
            self.ui.cNoneNormilize.setChecked(True)
        else:
            self.ui.cNoneNormilize.setChecked(False)

        if self.ui.rShadowingGlare.isChecked() == True:
            self.ui.parameters.tumor_shadowing_type = "glare"

    def change_main_interface(self, value):
        if value == True:
            # srart pressed
            self.ui.pManual.setEnabled(False)
            self.ui.pResetRegion.setEnabled(False)
        else:
            self.ui.pManual.setEnabled(True)
            self.ui.pResetRegion.setEnabled(True)

    def push_start_clicked(self):
        if self.ui.pStart.isChecked() == True:
            self.worker_hardware.is_stop = False
            # self.parameters.base_logging_folder = os.getcwd() + "\\" + unicode(self.ui.eLoggingFolder.text())
            self.parameters.base_logging_folder = unicode(self.ui.eLoggingFolder.text())

            self.set_fluorcontroller_base_mode()
            self.change_param_interface_state(False)
            self.change_main_interface(True)
            self.worker_hardware.working_leds = self.experimental_data.working_leds
            self.ui.pStart.setText(u"СТОП")
            self.clock_timer.start(500)
        else:
            self.worker_hardware.is_stop = True
            self.ui.pRecord.setChecked(False)
            self.push_record_clicked()
            self.save_monitoring_data(self.parameters)

            self.fluorcontroller_stop()
            self.change_param_interface_state(True)
            self.change_main_interface(False)

            self.ui.pStart.setText(u"СТАРТ")
            self.worker_hardware.is_stop = True

            self.clock_timer.stop()
            self.save_parameters()

            if os.path.isfile("logging_storage.pkl"):
                os.remove("logging_storage.pkl")

    def mouse_moved_on_graph_image(self, evt):
        wavelength = self.get_selected_image_wavelength_on_graph_image()

        if wavelength is not None:
            if self.experimental_data.image_cleared[wavelength] is not None:
                pos = evt
                x = int(self.ui.graph_image.getImageItem().mapFromScene(pos).x())
                y = int(self.ui.graph_image.getImageItem().mapFromScene(pos).y())
                if x >= 0 and y >= 0 and x < self.experimental_data.image_cleared[wavelength].shape[0] and y < \
                        self.experimental_data.image_cleared[wavelength].shape[1]:
                    val = self.experimental_data.image_cleared[wavelength][x, y]
                    self.ui.groupBox.setTitle(u"Флуоресцентное изображение x=%d,y=%d, ур. = %4.1f" % (x, y, val))

    def check_glare(self, image):
        if len(np.where(image >= self.experimental_data.max_image_value - self.parameters.glare_parameters["dmin_glare_value"])[0]) > self.parameters.glare_parameters["excess_count"]:
            return True
        else:
            return False

    def image_segmented(self, args):  # изображение отсегментировано
        task = args
        wavelength = task.wavelength
        select_wavelength = self.get_selected_image_wavelength_on_graph_image()
        if wavelength == select_wavelength:
            self.update_data_on_screen()

        # self.experimental_data.image_superposition_rgb[wavelength] = cv2.cvtColor(self.experimental_data.image_cleared[740],
        #                                                                      cv2.COLOR_GRAY2RGB)
        # if wavelength == 660:
        #     self.experimental_data.image_superposition_rgb[wavelength][:, :, 1] = self.experimental_data.image_cleared[wavelength]




        if 'laser off' in self.experimental_data.mode and 'region defined' in self.experimental_data.mode and 'monitoring' in self.experimental_data.mode and wavelength in (400,660):
            self.monitoring.append(self.experimental_data.properties, [wavelength])
            self.update_monitoring_plots()

    def update_data_on_screen(self, **kwargs):
        if 'image_changed' in kwargs and kwargs['image_changed'] == True:
            image_changed = True
        else:
            image_changed = False

        wavelength = self.get_selected_image_wavelength_on_graph_image()
        if wavelength is None:
            return

        t1 = time.clock()

        image_labels = ['image_cleared_with_contours_rbg', 'image_superposition_rgb']
        graphs = [self.ui.graph_image, self.ui.graph_image_superposition]
        graphs_images_data = [self.experimental_data.graph_image_data, self.experimental_data.graph_image_superposition_data]

        for image_label, graph, graph_image_data in zip(image_labels, graphs, graphs_images_data):
            images = getattr(self.experimental_data, image_label)

            if wavelength == 0 and image_label == 'image_superposition_rgb':
                if 740 in self.experimental_data.image_cleared and self.experimental_data.image_cleared[740] is not None:
                    image = self.experimental_data.image_cleared[740]
            else:
                if wavelength in images and images[wavelength] is not None:
                    image = images[wavelength]
                else:
                    continue

            if 'levels' not in graph_image_data[wavelength]:
                if image_label == 'image_cleared_with_contours_rbg':
                    if self.parameters.use_autolevel:
                        graph_image_data[wavelength]['levels'] = [0, numpy.max(image)]
                    else:
                        # info = numpy.iinfo(image.dtype)
                        for w in graph_image_data.keys():
                            graph_image_data[w]['levels'] = [0, 1000]

                if image_label == 'image_superposition_rgb':
                    if self.parameters.use_autolevel:
                        graph_image_data[wavelength]['levels'] = [0, 256]
                    else:
                        # info = numpy.iinfo(image.dtype)
                        for w in graph_image_data.keys():
                            graph_image_data[w]['levels'] = [0, 256]

                graph.getHistogramWidget().item.setLevels(*graph_image_data[wavelength]['levels'])

            if self.parameters.use_autolevel:
                if image_changed:
                    graph.getHistogramWidget().item.setLevels(*graph_image_data[wavelength]['levels'])
                else:
                    graph_image_data[wavelength]['levels'] = graph.getHistogramWidget().item.getLevels()

            self.image_show(graph, image, autoRange=False, autoLevels=False, autoHistogramRange=False, autoDownsample=False)

        str_properties = self.experimental_data.properties.make_string(wavelength)

        if wavelength in self.experimental_data.tumor_data and 'rectangle' in self.experimental_data.tumor_data[wavelength] and self.experimental_data.tumor_data[wavelength]['rectangle'] is not None:
            x,y,w,h=self.experimental_data.tumor_data[wavelength]['rectangle']
            str_properties += u"\nРазмеры фл. области: ({w:4.2f},{h:4.2f}) мм".format(w=w * self.parameters.x_mm_in_pixel, h=h * self.parameters.y_mm_in_pixel)

        if self.monitoring.burn and wavelength in self.monitoring.burn and len(self.monitoring.burn[wavelength]) > 0:
            str_properties += u"\nВыгорание: {burn:3.2f}".format(burn=self.monitoring.burn[wavelength][-1])
        if self.monitoring.contrast and wavelength in self.monitoring.contrast and len(self.monitoring.contrast[wavelength]) > 0:
            str_properties += u"\nКонтраст: {contrast:3.2f}".format(contrast=self.monitoring.contrast[wavelength][-1])

        self.ui.label_properties.setText(str_properties)

        if 'laser on' in self.experimental_data.mode:
            self.ui.label_status.setText(u"<font color='red'>ВКЛ</font>")
        else:
            self.ui.label_status.setText(u"<font color='green'>ВЫКЛ</font>")

        if 'region not defined' in self.experimental_data.mode:
            self.ui.label_region_defined.setText(u"<font color='red'>Не задана</font>")
        else:
            self.ui.label_region_defined.setText(u"<font color='green'>Задана</font>")

    def image_show(self,where_show,what_show, **kwargs):
        # where_show.clear()
        where_show.getImageItem().setImage(what_show, **kwargs)       # autoRange=False, autoLevels=False, autoHistogramRange=False
        if 'levels' in kwargs:
            where_show.setLevels(kwargs['levels'][0],kwargs['levels'][1])

    def image_received(self, args):  # изображение получено
        task = copy.copy(args[0])
        image = copy.copy(args[1])

        if image is None:
            return

        if self.parameters.flip_images:
            image = image[-1::-1, -1::-1]

        if 'monitoring' in self.experimental_data.mode and image is not None:
            self.monitoring.frames_counter([task.wavelength])

        if task.wavelength == 0:
            self.experimental_data.image[0] = numpy.copy(image)
            self.worker_segmentation.addjob((task, self.experimental_data, self.parameters, self.monitoring))
            if self.check_glare(self.experimental_data.image[0]):               # есть засветка
                self.experimental_data.task_pool = []
                self.experimental_data.image_temp.clear()
                if "laser off" in self.experimental_data.mode:
                    self.experimental_data.mode.remove("laser off")
                    self.experimental_data.mode.add("laser on")
                    self.set_fluorcontroller_laser_on_mode()
                    self.ui.label_status.setText(u"ВКЛ")
                ### Старт только черный
            else:
                if "laser on" in self.experimental_data.mode:
                    self.experimental_data.image_temp.clear()
                    self.experimental_data.task_pool = []
                    self.experimental_data.mode.remove("laser on")
                    self.experimental_data.mode.add("laser off")
                    #if "region not defined" in self.experimental_data.mode:
                    #   self.experimental_data.mode.remove("region not defined")
                    #   self.experimental_data.mode.add("region defined")

                    self.ui.label_status.setText(u"ВЫКЛ")
                    self.set_fluorcontroller_base_mode()

                if "laser off" in self.experimental_data.mode:
                    self.experimental_data.image.update(self.experimental_data.image_temp.copy())

                    map(self.worker_segmentation.addjob, [(tp, self.experimental_data, self.parameters, self.monitoring) for tp in self.experimental_data.task_pool])

                    self.experimental_data.image_temp.clear()
                    self.experimental_data.task_pool = []
                    if self.parameters.is_logging is True:
                        curr_time = time.clock()
                        if curr_time - self.parameters.TimeBegin >= self.parameters.TimerLength:
                            self.parameters.TimerLength = self.ui.sTimer.value()
                            self.parameters.TimeBegin = time.clock()

                            log_result = self.logging()
                            if not log_result:
                                errorstr = u"Недостаточно места на диске. Сохранение будет отменено"
                                QtGui.QMessageBox.about(self.ui.tabWidget, "Warning", errorstr)
                                self.ui.pRecord.setChecked(False)
                                self.push_record_clicked()

        if task.wavelength == -1:
            if 'laser off' in self.experimental_data.mode:
                # self.ui.ePeriod.setText(str(self.parameters.lighting_period + 0.05))
                self.set_fluorcontroller_base_mode()
            if 'laser on' in self.experimental_data.mode:
                pass

        if task.wavelength == 740:
            self.experimental_data.image_temp[740] = numpy.copy(image)
            if self.ui.widget_led740.value == True:
                self.experimental_data.task_pool.append(task)

        if task.wavelength == 660:
            self.experimental_data.image_temp[660] = numpy.copy(image)
            if self.ui.widget_led660.value == True:
                self.experimental_data.task_pool.append(task)

        if task.wavelength == 400:
            self.experimental_data.image_temp[400] = numpy.copy(image)
            if self.ui.widget_led400.value == True:
                self.experimental_data.task_pool.append(task)

        if task.wavelength >= 0:
            # self.worker_segmentation.addjob((task,self.experimental_data,self.parameters,self.monitoring))
            if "laser on" in self.experimental_data.mode:
                self.experimental_data.image_glare_prev[0].append(image.copy())
            else:
                self.experimental_data.image_glare_prev[0].clear()

        QtGui.QApplication.processEvents()

    def reset_region(self):
        if "region defined" in self.experimental_data.mode:
            self.experimental_data.mode.remove("region defined")
            self.experimental_data.mode.add("region not defined")

        self.experimental_data.properties.__init__()
        self.experimental_data.Clear()
        self.update_data_on_screen()

    def push_manual_mode_clicked(self):
        wavelength = 740 #self.get_selected_image_wavelength_on_graph_image()
        image_for_manual_input = None
        if wavelength is not None:
            if self.experimental_data.image_cleared[wavelength] is not None:
                image_for_manual_input = self.experimental_data.image_cleared[wavelength].copy()
        else:
            return

        if image_for_manual_input is None:
            return

        self.experimental_data.is_locked = True
        cv2.namedWindow('input')
        cv2.moveWindow('input', 1, 1)

        global manual_input_parameters
        manual_input_parameters["tumor_color"] = self.experimental_data.tumor_data["color"]
        manual_input_parameters["skin_color"] = self.experimental_data.skin_data["color"]

        image_for_manual_input_base = image_for_manual_input.copy().transpose()
        manual_input_parameters["img_base_equalized"] = image_for_manual_input.copy()
        manual_input_parameters["image_for_manual_input_base"] = cv2.cvtColor(image_for_manual_input_base, cv2.COLOR_GRAY2RGB)
        manual_input_parameters["image_for_manual_input_normalized"] = cv2.cvtColor(image_for_manual_input_base, cv2.COLOR_GRAY2RGB)
        manual_input_parameters["mask"] = numpy.zeros(image_for_manual_input.shape[:2], dtype=numpy.uint8)

        levels = self.ui.graph_image.getHistogramWidget().item.getLevels()

        if map(int, levels) == [0, 1]:
            levels = (0, numpy.max(manual_input_parameters["image_for_manual_input_normalized"]))

        manual_input_parameters["image_for_manual_input_normalized"][manual_input_parameters["image_for_manual_input_normalized"] < levels[0]] = 0
        manual_input_parameters["image_for_manual_input_normalized"][manual_input_parameters["image_for_manual_input_normalized"] > levels[1]] = levels[1]
        manual_input_parameters["image_for_manual_input_normalized"] = (manual_input_parameters["image_for_manual_input_normalized"].astype(np.float) / levels[1] * 2 ** 8).astype(np.uint8)

        cv2.imshow('input', manual_input_parameters["image_for_manual_input_normalized"])

        # setting up flags
        manual_input_parameters["tumor_poly"] = []
        manual_input_parameters["skin_poly"] = []
        manual_input_parameters["drawing"] = False  # flag for drawing curves
        manual_input_parameters["is_tumor_poly_drawing"] = False  # flag for drawing polyline
        manual_input_parameters["is_tumor_poly_over"] = False  # flag to check if rect drawn
        manual_input_parameters["is_skin_poly_copy"] = False  # flag for drawing polyline
        manual_input_parameters["is_skin_poly_over"] = False  # flag to check if rect drawn
        manual_input_parameters["first_rigth_click_coords"] = []
        manual_input_parameters["thickness"] = 3  # brush thickness

        global mean_intensity_data
        mean_intensity_data = {}

        def onmouse(event, x, y, flags, param):
            global manual_input_parameters
            global mean_intensity_data
            # Draw Rectangle
            if event == cv2.EVENT_LBUTTONDOWN:
                manual_input_parameters["is_tumor_poly_drawing"] = True
                manual_input_parameters["tumor_poly"] = [[x, y]]
                manual_input_parameters["skin_poly"] = []
                manual_input_parameters["is_skin_poly_over"] = False
            if event == cv2.EVENT_MOUSEMOVE:
                if manual_input_parameters["is_tumor_poly_drawing"] == True:
                    manual_input_parameters["image_for_manual_input"] = manual_input_parameters["image_for_manual_input_normalized"].copy()
                    manual_input_parameters["tumor_poly"] = manual_input_parameters["tumor_poly"] + [[x, y]]
                    cv2.polylines(manual_input_parameters["image_for_manual_input"], [numpy.array(manual_input_parameters["tumor_poly"], numpy.int32)], False, manual_input_parameters["tumor_color"], manual_input_parameters["thickness"])
                    cv2.imshow('input', manual_input_parameters["image_for_manual_input"])
            if event == cv2.EVENT_LBUTTONUP:
                manual_input_parameters["is_tumor_poly_drawing"] = False
                manual_input_parameters["is_tumor_poly_over"] = True
                manual_input_parameters["tumor_poly"] = manual_input_parameters["tumor_poly"] + [[x, y]] + [manual_input_parameters["tumor_poly"][0]]

                # print len(manual_input_parameters["tumor_poly"])

                mean_intensity_data["tumor_mask"] = numpy.zeros(manual_input_parameters["image_for_manual_input_base"].shape, numpy.uint8)
                mean_intensity_data["tumor_poly"] = [[tx[0], tx[1]] for tx in manual_input_parameters["tumor_poly"]]

                cv2.fillPoly(mean_intensity_data["tumor_mask"], [numpy.asarray(mean_intensity_data["tumor_poly"])], 1)
                mean_intensity_data["tumor_mask"] = mean_intensity_data["tumor_mask"].astype(numpy.uint8)
                mean_intensity_data["tumor_data"] = manual_input_parameters["image_for_manual_input_base"].astype(numpy.uint16) * mean_intensity_data["tumor_mask"]

                mean_intensity_data["tumor_mean_intes"] = numpy.mean(
                    mean_intensity_data["tumor_data"][mean_intensity_data["tumor_mask"] == 1])

                cv2.polylines(manual_input_parameters["image_for_manual_input"], [numpy.array(manual_input_parameters["tumor_poly"], numpy.int32)], False, manual_input_parameters["tumor_color"], manual_input_parameters["thickness"])

                mean_intensity_data["tumor_poly_text_x"] = int(mean_intensity_data["tumor_poly"][0][0])
                mean_intensity_data["tumor_poly_text_y"] = int(min([ty[1] for ty in mean_intensity_data["tumor_poly"]])) - 10
                cv2.putText(manual_input_parameters["image_for_manual_input"], str("{:3.1f}".format(mean_intensity_data["tumor_mean_intes"])), (mean_intensity_data["tumor_poly_text_x"], mean_intensity_data["tumor_poly_text_y"]),
                            cv2.FONT_HERSHEY_SIMPLEX, 1, manual_input_parameters["tumor_color"])

                cv2.imshow('input', manual_input_parameters["image_for_manual_input"])

            if event == cv2.EVENT_RBUTTONDOWN:
                manual_input_parameters["is_skin_poly_copy"] = True
                manual_input_parameters["first_rigth_click_coords"] = [x, y]
            if event == cv2.EVENT_MOUSEMOVE:
                if manual_input_parameters["is_skin_poly_copy"] == True and manual_input_parameters["is_tumor_poly_over"] == True:
                    manual_input_parameters["image_for_manual_input"] = manual_input_parameters["image_for_manual_input_normalized"].copy()
                    cv2.polylines(manual_input_parameters["image_for_manual_input"], [numpy.array(manual_input_parameters["tumor_poly"], numpy.int32)], False, manual_input_parameters["tumor_color"], manual_input_parameters["thickness"])
                    dx = x - manual_input_parameters["first_rigth_click_coords"][0]
                    dy = y - manual_input_parameters["first_rigth_click_coords"][1]

                    cv2.polylines(manual_input_parameters["image_for_manual_input"],
                                  [numpy.array(manual_input_parameters["tumor_poly"], numpy.int32)], False,
                                  manual_input_parameters["tumor_color"], manual_input_parameters["thickness"])
                    cv2.putText(manual_input_parameters["image_for_manual_input"],
                                str("{:3.1f}".format(mean_intensity_data["tumor_mean_intes"])),
                                (mean_intensity_data["tumor_poly_text_x"], mean_intensity_data["tumor_poly_text_y"]),
                                cv2.FONT_HERSHEY_SIMPLEX, 1, manual_input_parameters["tumor_color"])

                    if manual_input_parameters["is_skin_poly_over"] is False:
                        manual_input_parameters["skin_poly"] = []
                        manual_input_parameters["skin_poly"] = [[tx[0] + dx, tx[1] + dy] for tx in manual_input_parameters["tumor_poly"]]
                    else:
                        manual_input_parameters["skin_poly"] = [[tx[0] + dx, tx[1] + dy] for tx in manual_input_parameters["skin_poly"]]
                        manual_input_parameters["first_rigth_click_coords"] = [x, y]

                    cv2.polylines(manual_input_parameters["image_for_manual_input"], [numpy.array(manual_input_parameters["skin_poly"], numpy.int32)], False, manual_input_parameters["skin_color"], manual_input_parameters["thickness"])
                    cv2.imshow('input', manual_input_parameters["image_for_manual_input"])
            if event == cv2.EVENT_RBUTTONUP:
                manual_input_parameters["is_skin_poly_copy"] = False
                manual_input_parameters["is_skin_poly_over"] = True

                cv2.polylines(manual_input_parameters["image_for_manual_input"], [numpy.array(manual_input_parameters["skin_poly"], numpy.int32)], False, manual_input_parameters["skin_color"], manual_input_parameters["thickness"])

                # отрисовка цифры у кожи
                mean_intensity_data["skin_mask"] = numpy.zeros(manual_input_parameters["image_for_manual_input_base"].shape)
                mean_intensity_data["skin_poly"] = [[x[0], x[1]] for x in manual_input_parameters["skin_poly"]]
                cv2.fillPoly(mean_intensity_data["skin_mask"], [numpy.asarray(mean_intensity_data["skin_poly"])], 1)
                mean_intensity_data["skin_mask"] = mean_intensity_data["skin_mask"].astype(numpy.uint8)
                mean_intensity_data["skin_data"] = manual_input_parameters["image_for_manual_input_base"].astype(numpy.uint16) * mean_intensity_data["skin_mask"]
                mean_intensity_data["skin_mean_intes"] = np.asarray(
                    mean_intensity_data["skin_data"][mean_intensity_data["skin_mask"] == 1]).mean()

                cv2.polylines(manual_input_parameters["image_for_manual_input"], [numpy.array(manual_input_parameters["skin_poly"], numpy.int32)], False, manual_input_parameters["skin_color"], manual_input_parameters["thickness"])
                cv2.putText(manual_input_parameters["image_for_manual_input"], str("{:3.1f}".format(mean_intensity_data["tumor_mean_intes"])), (mean_intensity_data["tumor_poly_text_x"], mean_intensity_data["tumor_poly_text_y"]),
                            cv2.FONT_HERSHEY_SIMPLEX, 1, manual_input_parameters["tumor_color"])

                mean_intensity_data["skin_poly_text_x"] = int(mean_intensity_data["skin_poly"][0][0])
                mean_intensity_data["skin_poly_text_y"] = int(min([ty[1] for ty in mean_intensity_data["skin_poly"]])) - 10
                cv2.putText(manual_input_parameters["image_for_manual_input"], str("{:3.1f}".format(mean_intensity_data["skin_mean_intes"])), (mean_intensity_data["skin_poly_text_x"], mean_intensity_data["skin_poly_text_y"]),
                            cv2.FONT_HERSHEY_SIMPLEX, 1, manual_input_parameters["skin_color"])
                cv2.imshow('input', manual_input_parameters["image_for_manual_input"])

        cv2.setMouseCallback('input', onmouse)
        cv2.waitKey()

        if manual_input_parameters["is_tumor_poly_over"] and manual_input_parameters["is_skin_poly_over"]:
            for wavelength in (400, 660, 740):
                if self.experimental_data.image_cleared[wavelength] is not None:
                    self.experimental_data.tumor_data[wavelength]["mask"] = numpy.zeros(self.experimental_data.image_cleared[wavelength].shape)
                    self.experimental_data.skin_data[wavelength]["mask"] = numpy.zeros(self.experimental_data.image_cleared[wavelength].shape)

                    self.experimental_data.tumor_data[wavelength]["poly"] = [[tx[1], tx[0]] for tx in manual_input_parameters["tumor_poly"]]

                    cv2.fillPoly(self.experimental_data.tumor_data[wavelength]["mask"], [numpy.asarray(self.experimental_data.tumor_data[wavelength]["poly"])], 1)
                    self.experimental_data.tumor_data[wavelength]["mask"] = self.experimental_data.tumor_data[wavelength]["mask"].astype(numpy.uint8)

                    # print numpy.sum(self.experimental_data.tumor_data[wavelength]['mask'])

                    self.experimental_data.skin_data[wavelength]["poly"] = [[tx[1], tx[0]] for tx in manual_input_parameters["skin_poly"]]
                    cv2.fillPoly(self.experimental_data.skin_data[wavelength]["mask"], [numpy.asarray(self.experimental_data.skin_data[wavelength]["poly"])], 1)
                    self.experimental_data.skin_data[wavelength]["mask"] = self.experimental_data.skin_data[wavelength]["mask"].astype(numpy.uint8)

                    if "region not defined" in self.experimental_data.mode:
                        self.experimental_data.mode.remove("region not defined")
                        self.experimental_data.mode.add("region defined")

            QtGui.qApp.processEvents()
        #todo: update UI
        if "region defined" in self.experimental_data.mode:
            self.update_data_on_screen()
        self.experimental_data.is_locked = False

    @background
    def logging(self, queue_result):
        if self.experimental_data.is_locked:
            queue_result.put(True)
            return
        try:

            Folder = self.parameters.base_logging_folder + "\\" + self.parameters.full_name + "\\Full\\"
            #Folder = Folder.encode('cp1251', 'ignore')
            if not os.path.exists(Folder):
                os.makedirs(Folder)
            if self.parameters.save_full_protocol:
                data_to_store = {'time': datetime.datetime.now(),
                                 'monitoring': copy.deepcopy(self.monitoring),
                                 'experimental_data': copy.deepcopy(self.experimental_data),
                                 'parameters': copy.deepcopy(self.parameters)
                                 }
                data_to_store['experimental_data'].image_cleared = {}
                data_to_store['experimental_data'].image_temp = {}

                data_filename = Folder + "data_dump_" + data_to_store['time'].strftime("%Y-%m-%d_%H-%M-%S")+".pkl"
                save_pickle_to_zip(data_to_store, data_filename)

                info_to_store = {'image_filenames': {},
                                 'image_filenames_rel': {},
                                 'image_superposition_filenames': {},
                                 'image_superposition_filenames_rel': {},
                                 'data_filename': data_filename}

            else:
                data_to_store = {'time': datetime.datetime.now(),
                                 'monitoring': copy.deepcopy(self.monitoring),
                                 'parameters': copy.deepcopy(self.parameters),
                                 'experimental_data': copy.deepcopy(self.experimental_data),
                                 }
                data_to_store['experimental_data'].image_cleared = {}
                data_to_store['experimental_data'].image_temp = {}
                data_to_store['experimental_data'].image = {}
                data_to_store['experimental_data'].image_cleared = {}
                data_to_store['experimental_data'].image_cleared_with_contours_rbg = {}
                data_to_store['experimental_data'].image_superposition_rgb = {}
                # data_to_store['experimental_data'].graph_image_data = {}
                # data_to_store['experimental_data'].graph_image_superposition_data = {}
                data_to_store['experimental_data'].skin_data = {}
                data_to_store['experimental_data'].tumor_data = {}

                data_filename = Folder + "data_dump_" + data_to_store['time'].strftime("%Y-%m-%d_%H-%M-%S") + ".pkl"
                save_pickle_to_zip(data_to_store, data_filename, compresslevel=0)

                info_to_store = {'image_filenames': {},
                                 'image_filenames_rel': {},
                                 'image_superposition_filenames': {},
                                 'image_superposition_filenames_rel': {},
                                 'data_filename': data_filename}

            t = datetime.datetime.now()
            for (key, img) in self.experimental_data.image.iteritems():
                if img is not None:
                    #img = self.convert_to_8bit(img, self.experimental_data.max_image_value)
                    filename = Folder + t.strftime("%Y-%m-%d %H-%M-%S") + "_" + str(key) + ".tiff"
                    filename_rel = u"\\Full\\" + t.strftime("%Y-%m-%d %H-%M-%S") + "_" + str(key) + ".tiff"
                    #tiff.imsave(filename, img.transpose(), compress=1)
                    tiff.imsave(filename, img, compress=1)
                    info_to_store['image_filenames'][key] = filename
                    info_to_store['image_filenames_rel'][key] = filename_rel

            temp_image_rgb = self.experimental_data.image_superposition_rgb.copy()
            for (key, img) in temp_image_rgb.iteritems():
                if img is not None:
                    filename = Folder + t.strftime("%Y-%m-%d %H-%M-%S") + "_superposition_" + str(key) + ".tiff"
                    filename_rel = "\\Full\\" + t.strftime("%Y-%m-%d %H-%M-%S") + "_superposition_" + str(key) + ".tiff"
                    #tiff.imsave(filename, img.transpose(), compress=1)
                    tiff.imsave(filename, img, compress=1)
                    info_to_store['image_superposition_filenames'][key] = filename
                    info_to_store['image_superposition_filenames_rel'][key] = filename_rel

            self.logging_data_storage['info'].append(info_to_store)

            Folder = self.parameters.base_logging_folder + "\\" + self.parameters.full_name + "\\"
            #Folder = Folder.encode('cp1251', 'ignore')
            if not os.path.exists(Folder):
                os.makedirs(Folder)

            filename = Folder + "logging_storage.pkl"
            save_pickle_to_zip(self.logging_data_storage, filename)

            queue_result.put(True)
        except Exception,e:
            print e.message
            queue_result.put(False)

    def single_log_shot(self):
        try:
            Folder = self.parameters.base_logging_folder + "\\" + self.parameters.full_name + "\\"
            self.parameters.save(Folder)
            #Folder = Folder.encode('cp1251', 'ignore')
            if not os.path.exists(Folder):
                os.makedirs(Folder)

            t = datetime.datetime.now()
            temp_image = self.experimental_data.image.copy()
            for (key, img) in temp_image.iteritems():
                if img is not None:
                    img = self.convert_to_8bit(img, self.experimental_data.max_image_value)
                    tiff.imsave(Folder + t.strftime("%Y-%m-%d %H-%M-%S") + "_" + str(key) + ".tiff", img.transpose(), compress=1)

            temp_image_rgb = self.experimental_data.image_superposition_rgb.copy()
            for (key, img) in temp_image_rgb.iteritems():
                if img is not None:
                    tiff.imsave(Folder + t.strftime("%Y-%m-%d %H-%M-%S") + "_superposition_" + str(key) + ".tiff", img.transpose(), compress=1)

        except Exception,e:
            print e.message

    def push_start_monitoring_clicked(self):

        if unicode(self.ui.edit_alarm660.text()) is not u"":
            self.parameters.alarm_levels[660] = float(unicode(self.ui.edit_alarm660.text()))
        else:
            self.parameters.alarm_levels[660] = 0

        if unicode(self.ui.edit_alarm400.text()) is not u"":
            self.parameters.alarm_levels[400] = float(unicode(self.ui.edit_alarm400.text()))
        else:
            self.parameters.alarm_levels[400] = 0

        self.monitoring.is_reset_beeping = self.ui.cResetBeepTimer.isChecked()
        self.monitoring.next_beep_duration = self.ui.sTimerBeep.value()
        self.experimental_data.mode.add('monitoring')
        self.ui.groupBeep.setEnabled(False)
        self.ui.pStartMonitoring.setEnabled(False)
        self.ui.pStopMonitoring.setEnabled(True)
        self.ui.pResetMonitoring.setEnabled(True)
        self.monitoring.start()


    def edit_alarm_changed(self):
        if unicode(self.ui.edit_alarm660.text()) is not u"":
            self.parameters.alarm_levels[660] = float(unicode(self.ui.edit_alarm660.text()))
        else:
            self.parameters.alarm_levels[660] = 0

        if unicode(self.ui.edit_alarm400.text()) is not u"":
            self.parameters.alarm_levels[400] = float(unicode(self.ui.edit_alarm400.text()))
        else:
            self.parameters.alarm_levels[400] = 0

    def push_stop_monitoring_clicked(self):
        self.monitoring.stop()
        if 'monitoring' in self.experimental_data.mode:
            self.experimental_data.mode.remove('monitoring')

        self.experimental_data.is_monitoring_mode = False
        self.ui.pManual.setEnabled(True)
        self.ui.groupBeep.setEnabled(True)
        self.ui.pStartMonitoring.setEnabled(True)
        self.ui.pStopMonitoring.setEnabled(False)
        self.ui.pResetMonitoring.setEnabled(False)

    def push_reset_monitoring_clicked(self):
        self.monitoring.reset()
        self.ui.graph_monitoring_plots.plotItem.clear()

    def save_monitoring_data(self, parameters):
        try:
            if not self.monitoring.is_empty():
                Folder = self.parameters.base_logging_folder + u"\\" + self.parameters.full_name + u"\\"
                #Folder = Folder.encode('cp1251', 'ignore')
                if not os.path.exists(Folder):
                    os.makedirs(Folder)
                self.monitoring.save(parameters, Folder)
        except:
            pass

    def update_monitoring_plots(self):
        colours = {660: (0xCF, 0xff, 0x9a),
                   400: (0x00, 0x03, 0x9a)}

        if "monitoring" in self.experimental_data.mode:
            self.ui.graph_monitoring_plots.plotItem.setLabel("bottom", "Время,c")
            self.ui.graph_monitoring_plots.plotItem.showGrid(True, True)
            self.ui.graph_monitoring_plots.plotItem.clear()

            for wavelength in self.monitoring.tumor_area.keys():
                if self.ui.__getattribute__("widget_led" + str(wavelength)).value == True:
                    if len(self.monitoring.dt[wavelength]) >= 2:
                        self.ui.graph_monitoring_plots.plotItem.addItem(
                            FastLine.FastLine(self.monitoring.dt[wavelength], self.monitoring.tumor_mean[wavelength],
                                              pen={'color': colours[wavelength], 'width': 2}))
                        if self.parameters.alarm_levels[wavelength] > 0:
                            self.ui.graph_monitoring_plots.plotItem.addItem(FastLine.FastLine(
                                [self.monitoring.dt[wavelength][0], self.monitoring.dt[wavelength][-1]],
                                [self.parameters.alarm_levels[wavelength], self.parameters.alarm_levels[wavelength]],
                                pen={'color': colours[wavelength], 'width': 1, 'style': QtCore.Qt.DashDotDotLine}))

                            if self.monitoring.tumor_mean[wavelength][-1] <= self.parameters.alarm_levels[wavelength]:
                                winsound.PlaySound(os.getcwd() + "\\Additional\\" + "Windows Notify Messaging.wav",
                                                   winsound.SND_FILENAME | winsound.SND_ASYNC)

                self.ui.graph_monitoring_plots.plotItem.setLabel("left", "Интенсивность флуоресценции, a.u.")

    def convert_to_8bit(self, img, MaxVal):
        img = (img.astype(numpy.float) / MaxVal * 255).astype(numpy.uint8)
        return img

    def save_parameters(self):
        self.parse_parameters_from_form()
        tmp = self.parameters.__dict__
        if not os.path.exists(self.parameters.folder):
            os.makedirs(self.parameters.folder)


        f = open(self.parameters.folder + self.parameters.filename, 'wb')
        cPickle.dump(tmp, f, cPickle.HIGHEST_PROTOCOL)
        f.close()

    def load_parameters(self):
        if not os.path.isfile(self.parameters.folder + self.parameters.filename):
            return
        f = open(self.parameters.folder + self.parameters.filename, 'rb')
        tmp = cPickle.load(f)
        f.close()

        self.ui.eLoggingFolder.setText(unicode(tmp['base_logging_folder']))
        self.ui.e400Exposition.setText(unicode(tmp['exposition'][400]))
        self.ui.e660Exposition.setText(unicode(tmp['exposition'][660]))
        self.ui.e740Exposition.setText(unicode(tmp['exposition'][740]))
        self.ui.eCameraGain.setText(unicode(tmp['camera_gain']))
        self.ui.cCameraBit.setEditText(unicode(tmp['camera_binning']))
        self.ui.cFullProtocolSave.setEnabled(tmp['save_full_protocol'])
        self.ui.cAutoLevel.setChecked(tmp['use_autolevel'])

        self.exposition_changed()
        self.parameters.base_logging_folder = tmp['base_logging_folder']
        self.parameters.x_mm_in_pixel = tmp['x_mm_in_pixel']
        self.parameters.y_mm_in_pixel = tmp['y_mm_in_pixel']

    def push_calibration_clicked(self):
        self.parse_parameters_from_form()
        if self.ui.pStart.isChecked() == True:
            self.fluorcontroller_stop()
            self.ui.pStart.setText(u"СТАРТ")
            self.worker_hardware.is_stop = True
            self.worker_hardware.quit()

        self.fluocontrollers.camera_controller.SetFormat(constants.DF_RAW8)
        self.fluocontrollers.lighting_controller.SetPeriod(int(0.07 * 1e6))
        self.fluocontrollers.camera_controller.SetExposureTime(int(0.001 * 1e6))
        MaxVal = 2 ** 8

        self.fluocontrollers.lighting_controller.SetLightingMode(0, constants.LM_IR, int(1 * 1e6))
        self.fluocontrollers.lighting_controller.SetModesNumber(1)
        self.fluocontrollers.camera_controller.SetGain(int(self.parameters.camera_gain))
        self.fluocontrollers.camera_controller.SetBinningMode(self.parameters.camera_binning)
        self.fluocontrollers.storage_controller.Clear()
        self.fluorcontroller_start()

        isDetected = False
        circles = None
        while isDetected is False:
            t1 = time.clock()

            if self.fluocontrollers.storage_controller.GetCount() > 0:  # storage_controller.GetCount()
                Frame = self.fluocontrollers.fluo_controller.GetFrame()
                FrameData = Frame.GetData()
                frame = numpy.frombuffer(FrameData, numpy.uint32)

                frame = frame.reshape(self.parameters.image_size)
                frame = frame.astype(numpy.uint8)
                if self.parameters.flip_images:
                    frame = cv2.flip(frame, -1)


                circles = cv2.HoughCircles(frame, method=cv2.cv.CV_HOUGH_GRADIENT, dp=1, minDist=25, param1=130, param2=35, minRadius=5, maxRadius=100)
                frame_color = cv2.cvtColor(frame,cv2.COLOR_GRAY2RGB)
                if circles is not None:
                    circles = circles[0]
                    # print circles
                    for circ in circles:
                        cv2.circle(frame_color, tuple(circ[0:2]), circ[2], (255, 0, 255), 1)

                    if len(circles) == 2:
                        isDetected = True
                        x, y, radius = circles[0]
                        center1 = numpy.asarray((x, y))
                        radius = int(radius)
                        x, y, radius = circles[1]
                        center2 = numpy.asarray((x, y))

                        pixel_dist = numpy.linalg.norm(center2 - center1)
                        self.parameters.x_mm_in_pixel = self.parameters.calibration_distance / pixel_dist
                        self.parameters.y_mm_in_pixel = self.parameters.calibration_distance / pixel_dist
                        self.save_parameters()

                cv2.imshow(u"Для выхода из калибровки нажмите ESC".encode("cp1251"), frame_color)

                if cv2.waitKey(10) == 0x1b:
                    cv2.destroyAllWindows()
                    self.fluorcontroller_stop()
                    return

        if isDetected:
            cv2.destroyAllWindows()
            cv2.imshow(u"Калибровка выполнена успешно".encode("cp1251"), frame_color)
            cv2.waitKey()
            self.fluorcontroller_stop()
            self.ui.pStart.setText(u"СТАРТ")

    def update_time(self):
        # print self.monitoring.next_beep_value
        if 'laser off' in self.experimental_data.mode:
            self.monitoring.stopwatch_laser_on['last_time'] = datetime.datetime.now()

        if self.monitoring.stopwatch_laser_on['current_value'] == 0 and 'monitoring' in self.experimental_data.mode:
            m, s = divmod(self.monitoring.stopwatch_laser_on['current_value'], 60)
            stopwatch_str="%02d:%02d" % (m, s)
            self.ui.lcdNumber.display(stopwatch_str)

        if 'laser on' in self.experimental_data.mode and 'monitoring' in self.experimental_data.mode:
            self.monitoring.stopwatch_laser_on['current_value'] += (datetime.datetime.now() - self.monitoring.stopwatch_laser_on['last_time']).total_seconds()
            self.monitoring.stopwatch_laser_on['last_time'] = datetime.datetime.now()
            m, s = divmod(self.monitoring.stopwatch_laser_on['current_value'], 60)
            stopwatch_str="%02d:%02d" % (m, s)
            self.ui.lcdNumber.display(stopwatch_str)
            if self.monitoring.next_beep_value is None:
                self.monitoring.next_beep_value = self.monitoring.next_beep_duration

            if self.monitoring.next_beep_value is not None and self.monitoring.stopwatch_laser_on['current_value'] >= self.monitoring.next_beep_value:
                if (self.monitoring.stopwatch_laser_on['current_value'] - self.monitoring.next_beep_value) < self.monitoring.beep_duration:
                    winsound.PlaySound(os.getcwd() + "\\Additional\\" + "pi.wav",
                                       winsound.SND_FILENAME | winsound.SND_ASYNC)
                else:
                    self.monitoring.next_beep_value += self.monitoring.next_beep_duration

        if 'laser off' in self.experimental_data.mode and 'monitoring' in self.experimental_data.mode and self.monitoring.is_reset_beeping:
            self.monitoring.next_beep_value = self.monitoring.stopwatch_laser_on['current_value'] + self.monitoring.next_beep_duration


    def fluorcontroller_start(self):
        try:
            self.fluocontrollers.fluo_controller.Start(constants.UNLIMITED)
        except pythoncom.com_error as error:
            strerr = win32api.FormatMessage(error.excepinfo[5])
            return
        except:
            QtGui.QMessageBox.about(self, "Warning",
                                    u"Невозможно получить управление камерой. Скорее всего, запущена другая версия программы.")
            return

    def fluorcontroller_stop(self):
        try:
            self.fluocontrollers.fluo_controller.Stop()
            self.fluocontrollers.storage_controller.Clear()
            self.experimental_data.task_pool = []
        except:
            QtGui.QMessageBox.about(self, "Warning",
                                    u"Невозможно получить управление камерой. Скорее всего, запущена другая версия программы.")
            return

    def set_fluorcontroller_base_mode(self):
        self.parse_parameters_from_form()
        if self.ui.pStart.isChecked():
            self.fluorcontroller_stop()
            self.worker_hardware.is_stop = True
            self.worker_hardware.quit()
            # self.worker_hardware.terminate()

        if self.parameters.camera_bits == 8:
            self.fluocontrollers.camera_controller.SetFormat(constants.DF_RAW8)
            self.experimental_data.max_image_value = 2 ** 8

        if self.parameters.camera_bits == 12:
            self.fluocontrollers.camera_controller.SetFormat(constants.DF_RAW12)
            self.experimental_data.max_image_value = 2 ** 12

        self.fluocontrollers.camera_controller.SetExposureTime(int(self.parameters.camera_exposition * 1e6))
        self.ui.combo_selected_image.clear()
        iTask = 0
        if self.ui.widget_led740.value == True:
            self.fluocontrollers.lighting_controller.SetLightingMode(iTask, constants.LM_IR, int(self.parameters.exposition[740] * 1e6))
            iTask = iTask + 1
            # self.ui.combo_selected_image.addItem(u"740 нм")
            self.experimental_data.working_leds.append(740)

        self.fluocontrollers.lighting_controller.SetLightingMode(iTask, constants.LM_NONE, int(self.parameters.exposition[0] * 1e6))
        self.experimental_data.working_leds.append(0)
        iTask = iTask + 1

        if self.ui.widget_led660.value == True:
            self.fluocontrollers.lighting_controller.SetLightingMode(iTask, constants.LM_RED, int(self.parameters.exposition[660] * 1e6))
            iTask = iTask + 1
            self.experimental_data.working_leds.append(660)
            self.ui.combo_selected_image.addItem(u"660 нм")

        if self.ui.widget_led400.value == True:
            self.fluocontrollers.lighting_controller.SetLightingMode(iTask, constants.LM_BLUE, int(self.parameters.exposition[400] * 1e6))
            iTask = iTask + 1
            self.experimental_data.working_leds.append(400)
            self.ui.combo_selected_image.addItem(u"400 нм")

        self.ui.combo_selected_image.addItem(u"темновой кадр")
        # self.fluocontrollers.lighting_controller.SetPeriod(int(1.5*float(self.ui.eCameraExposition.text())*1e6))
        self.fluocontrollers.lighting_controller.SetPeriod(int(self.parameters.lighting_period * 1e6))
        self.fluocontrollers.lighting_controller.SetModesNumber(iTask)
        self.fluocontrollers.camera_controller.SetGain(int(self.parameters.camera_gain))
        self.fluocontrollers.camera_controller.SetBinningMode(self.parameters.camera_binning)
        self.fluocontrollers.storage_controller.Clear()

        self.worker_hardware.image_size = self.parameters.image_size

        if self.ui.pStart.isChecked():
            self.fluorcontroller_start()
            self.worker_hardware.is_stop = False
            self.worker_hardware.start()

    def set_fluorcontroller_laser_on_mode(self):
        self.parse_parameters_from_form()
        if self.ui.pStart.isChecked():
            self.fluorcontroller_stop()
            self.worker_hardware.is_stop = True
            self.worker_hardware.quit() #terminate() #quit()()

        if self.parameters.camera_bits == 8:
            self.fluocontrollers.camera_controller.SetFormat(constants.DF_RAW8)
            self.experimental_data.max_image_value = 2 ** 8
            self.parameters.glare_min_value = 50

        if self.parameters.camera_bits == 12:
            self.fluocontrollers.camera_controller.SetFormat(constants.DF_RAW12)
            self.experimental_data.max_image_value = 2 ** 12
            self.parameters.glare_min_value = 500

        self.fluocontrollers.lighting_controller.SetLightingMode(0, constants.LM_NONE, int(0.1 * 1e6))
        self.fluocontrollers.camera_controller.SetExposureTime(int(0.1 * 1e6))
        self.fluocontrollers.lighting_controller.SetPeriod(int(0.5 * 1e6))
        self.fluocontrollers.lighting_controller.SetModesNumber(1)
        self.fluocontrollers.camera_controller.SetGain(int(self.parameters.camera_gain))
        self.fluocontrollers.camera_controller.SetBinningMode(self.parameters.camera_binning)

        self.worker_hardware.image_size = self.parameters.image_size
        self.ui.combo_selected_image.clear()
        self.ui.combo_selected_image.addItem(u"темновой кадр")

        if self.ui.pStart.isChecked() == True:
            self.fluorcontroller_start()
            self.worker_hardware.is_stop = False
            self.worker_hardware.start()

    def check_use_black_image_clicked(self):
        if self.ui.cNoneNormilize.isChecked() == True:
            self.parameters.use_black_image = 1
        else:
            self.parameters.use_black_image = 0

    def get_selected_image_wavelength_on_graph_image(self):
        wavelength = None
        combo_selected_image_text = unicode(self.ui.combo_selected_image.currentText())
        if combo_selected_image_text == u'400 нм':
            wavelength = 400
        if combo_selected_image_text == u'660 нм':
            wavelength = 660
        if combo_selected_image_text == u'740 нм':
            wavelength = 740
        if combo_selected_image_text == u'темновой кадр':
            wavelength = 0

        return wavelength

    def push_single_frame_400_clicked(self):
        self.parse_parameters_from_form()
        if self.ui.pStart.isChecked() == True:
            self.fluorcontroller_stop()
            self.ui.pStart.setText(u"СТАРТ")
            self.worker_hardware.is_stop = True
            self.worker_hardware.quit()

        if self.parameters.camera_bits == 8:
            self.fluocontrollers.camera_controller.SetFormat(constants.DF_RAW8)
            MaxVal = 2 ** 8
        if self.parameters.camera_bits == 12:
            self.fluocontrollers.camera_controller.SetFormat(constants.DF_RAW12)
            MaxVal = 2 ** 12

        self.fluocontrollers.lighting_controller.SetLightingMode(0, constants.LM_BLUE,
                                                                   int(self.parameters.exposition[400] * 1e6))
        self.fluocontrollers.lighting_controller.SetPeriod(
            max(self.parameters.additional_perion_of_single_frame + int(self.parameters.exposition[400] * 1e6), int(100 * 1e3)))
        self.fluocontrollers.lighting_controller.SetModesNumber(1)
        self.fluocontrollers.camera_controller.SetExposureTime(int(self.parameters.exposition[400] * 1e6))
        self.fluocontrollers.camera_controller.SetGain(int(self.parameters.camera_gain))
        self.fluocontrollers.camera_controller.SetBinningMode(self.parameters.camera_binning)
        self.fluocontrollers.storage_controller.Clear()

        t1 = time.clock()
        self.fluorcontroller_start()

        Cont = True
        while Cont:
            try:
                if self.fluocontrollers.storage_controller.GetCount() > 0:  # storage_controller.GetCount()
                    Frame = self.fluocontrollers.fluo_controller.GetFrame()
                    FrameData = Frame.GetData()
                    frame = numpy.frombuffer(FrameData, numpy.uint32)

                    frame = frame.reshape(self.parameters.image_size)
                    frame = frame.astype(numpy.uint16)
                    if self.parameters.flip_images:
                        frame = cv2.flip(frame, -1)

                    cv2.imshow("BLUE", self.convert_to_8bit(frame, MaxVal))

                    Cont = False

                    # Folder = os.getcwd() + "\\" + unicode(self.ui.eLoggingFolder.text()) + "\\_ОДИНОЧНЫЕ КАДРЫ"
                    Folder = unicode(self.ui.eLoggingFolder.text()) + "\\_ОДИНОЧНЫЕ КАДРЫ"
                    #Folder = Folder.encode('cp1251', 'ignore')
                    if not os.path.exists(Folder):
                        os.makedirs(Folder)

                    tiff.imsave(Folder + "\\BLUE_" + str(
                        int(self.parameters.exposition[400] * 1e3)) + "ms_" + datetime.datetime.now().strftime(
                        "%H-%M-%S") + ".tif", frame)
            except Exception, e:
                print e.message
                pass

        self.fluorcontroller_stop()
        t2 = time.clock()
        if DEBUG_MODE:
            print(t2-t1)
        self.ui.pStart.setText(u"СТАРТ")

    def push_single_frame_660_clicked(self):
        self.parse_parameters_from_form()
        if self.ui.pStart.isChecked() == True:
            self.fluorcontroller_stop()
            self.ui.pStart.setText(u"СТАРТ")
            self.worker_hardware.is_stop = True
            self.worker_hardware.quit()

        if self.parameters.camera_bits == 8:
            self.fluocontrollers.camera_controller.SetFormat(constants.DF_RAW8)
            MaxVal = 2 ** 8
        if self.parameters.camera_bits == 12:
            self.fluocontrollers.camera_controller.SetFormat(constants.DF_RAW12)
            MaxVal = 2 ** 12

        self.fluocontrollers.lighting_controller.SetLightingMode(0, constants.LM_RED,
                                                                   int(self.parameters.exposition[660] * 1e6))
        self.fluocontrollers.lighting_controller.SetPeriod(
            max(self.parameters.additional_perion_of_single_frame + int(self.parameters.exposition[660] * 1e6), int(100 * 1e3)))
        self.fluocontrollers.lighting_controller.SetModesNumber(1)
        self.fluocontrollers.camera_controller.SetExposureTime(int(self.parameters.exposition[660] * 1e6))
        self.fluocontrollers.camera_controller.SetBinningMode(self.parameters.camera_binning)
        self.fluocontrollers.camera_controller.SetGain(int(self.parameters.camera_gain))
        self.fluocontrollers.storage_controller.Clear()

        t1 = time.clock()
        self.fluorcontroller_start()

        Cont = True
        while Cont:
            try:
                if self.fluocontrollers.storage_controller.GetCount() > 0:  # storage_controller.GetCount()
                    Frame = self.fluocontrollers.fluo_controller.GetFrame()
                    FrameData = Frame.GetData()
                    frame = numpy.frombuffer(FrameData, numpy.uint32)

                    frame = frame.reshape(self.parameters.image_size)
                    frame = frame.astype(numpy.uint16)
                    if self.parameters.flip_images:
                        frame = cv2.flip(frame, -1)
                    cv2.imshow("RED", self.convert_to_8bit(frame, MaxVal))

                    Cont = False

                    # Folder = os.getcwd() + "\\" + unicode(self.ui.eLoggingFolder.text()) + u"\\_ОДИНОЧНЫЕ КАДРЫ"
                    Folder = unicode(self.ui.eLoggingFolder.text()) + "\\_ОДИНОЧНЫЕ КАДРЫ"
                    #Folder = Folder.encode('cp1251', 'ignore')
                    if not os.path.exists(Folder):
                        os.makedirs(Folder)

                    tiff.imsave(Folder + "\\RED_" + str(
                        int(self.parameters.exposition[660] * 1e3)) + "ms_" + datetime.datetime.now().strftime(
                        "%H-%M-%S") + ".tif", frame)
            except Exception, e:
                print e.message
                pass

        self.fluorcontroller_stop()
        t2 = time.clock()
        if DEBUG_MODE:
            print(t2-t1)

        self.ui.pStart.setText(u"СТАРТ")

    def push_single_frame_740_clicked(self):
        self.parse_parameters_from_form()
        self.fluorcontroller_stop()
        self.ui.pStart.setText(u"СТАРТ")
        if self.parameters.camera_bits == 8:
            self.fluocontrollers.camera_controller.SetFormat(constants.DF_RAW8)
            MaxVal = 2 ** 8
        if self.parameters.camera_bits == 12:
            self.fluocontrollers.camera_controller.SetFormat(constants.DF_RAW12)
            MaxVal = 2 ** 12

        self.fluocontrollers.lighting_controller.SetLightingMode(0, constants.LM_IR,
                                                                   int(self.parameters.exposition[740] * 1e6))
        self.fluocontrollers.lighting_controller.SetPeriod(
            max(self.parameters.additional_perion_of_single_frame +  int(self.parameters.exposition[740] * 1e6), int(100 * 1e3)))
        self.fluocontrollers.lighting_controller.SetModesNumber(1)
        self.fluocontrollers.camera_controller.SetExposureTime(int(self.parameters.exposition[740] * 1e6))
        self.fluocontrollers.camera_controller.SetBinningMode(self.parameters.camera_binning)
        self.fluocontrollers.camera_controller.SetGain(int(self.parameters.camera_gain))
        self.fluocontrollers.storage_controller.Clear()

        self.fluorcontroller_start()

        Cont = True
        while Cont:
            try:
                if self.fluocontrollers.storage_controller.GetCount() > 0:  # storage_controller.GetCount()
                    Frame = self.fluocontrollers.fluo_controller.GetFrame()
                    FrameData = Frame.GetData()
                    frame = numpy.frombuffer(FrameData, numpy.uint32)
                    frame = frame.reshape(self.parameters.image_size)
                    frame = frame.astype(numpy.uint16)
                    if self.parameters.flip_images:
                        frame = cv2.flip(frame, -1)

                    cv2.imshow("IR", self.convert_to_8bit(frame, MaxVal))

                    Cont = False

                    # Folder = os.getcwd() + "\\" + unicode(self.ui.eLoggingFolder.text()) + u"\\_ОДИНОЧНЫЕ КАДРЫ"
                    Folder = unicode(self.ui.eLoggingFolder.text()) + "\\_ОДИНОЧНЫЕ КАДРЫ"
                    #Folder = Folder.encode('cp1251', 'ignore')
                    if not os.path.exists(Folder):
                        os.makedirs(Folder)

                    tiff.imsave(Folder + "\\IR_" + str(
                        int(self.parameters.exposition[740] * 1e3)) + "ms_" + datetime.datetime.now().strftime(
                        "%H-%M-%S") + ".tif", frame)
            except Exception, e:
                print e.message
                pass

        self.fluorcontroller_stop()
        self.ui.pStart.setText(u"СТАРТ")

    def push_single_frame_black_clicked(self):
        self.parse_parameters_from_form()
        if self.ui.pStart.isChecked() == True:
            self.fluorcontroller_stop()
            self.ui.pStart.setText(u"СТАРТ")
            self.worker_hardware.is_stop = True
            self.worker_hardware.quit()

        if self.parameters.camera_bits == 8:
            self.fluocontrollers.camera_controller.SetFormat(constants.DF_RAW8)
            MaxVal = 2 ** 8
        if self.ui.cCameraBit.currentIndex() == 1:
            self.fluocontrollers.camera_controller.SetFormat(constants.DF_RAW12)
            MaxVal = 2 ** 12

        self.fluocontrollers.lighting_controller.SetLightingMode(0, constants.LM_NONE,
                                                                   int(self.parameters.exposition[0] * 1e6))
        self.fluocontrollers.lighting_controller.SetPeriod(int(self.parameters.exposition[0] * 1e6))
        self.fluocontrollers.lighting_controller.SetModesNumber(1)
        self.fluocontrollers.camera_controller.SetExposureTime(int(self.parameters.exposition[0] * 1e6))
        self.fluocontrollers.camera_controller.SetGain(int(self.parameters.camera_gain))
        self.fluocontrollers.camera_controller.SetBinningMode(self.parameters.camera_binning)
        self.fluocontrollers.storage_controller.Clear()
        self.fluorcontroller_start()

        Cont = True
        while Cont:
            try:
                if self.fluocontrollers.storage_controller.GetCount() > 0:  # storage_controller.GetCount()
                    Frame = self.fluocontrollers.fluo_controller.GetFrame()
                    FrameData = Frame.GetData()
                    frame = numpy.frombuffer(FrameData, numpy.uint32)

                    frame = frame.reshape(self.parameters.image_size)
                    frame = frame.astype(numpy.uint16)
                    if self.parameters.flip_images:
                        frame = cv2.flip(frame, -1)

                    cv2.imshow("NONE", self.convert_to_8bit(frame, MaxVal))

                    Cont = False

                    # Folder = os.getcwd() + "\\" + unicode(self.ui.eLoggingFolder.text()) + u"\\_ОДИНОЧНЫЕ КАДРЫ"
                    Folder = unicode(self.ui.eLoggingFolder.text()) + "\\_ОДИНОЧНЫЕ КАДРЫ"
                    #Folder = Folder.encode('cp1251', 'ignore')
                    if not os.path.exists(Folder):
                        os.makedirs(Folder)

                    tiff.imsave(Folder + "\\NONE_" + str(
                        int(self.parameters.exposition[0] * 1e3)) + "ms_" + datetime.datetime.now().strftime(
                        "%H-%M-%S") + ".tif", frame)
            except Exception, e:
                print e.message
                pass

        self.fluorcontroller_stop()
        self.ui.pStart.setText(u"СТАРТ")

    def parse_parameters_from_form(self):
        if unicode(self.ui.edit_full_name.text()) == u"":
            self.ui.edit_full_name.setText(u"Пациент " + unicode(datetime.datetime.now().strftime("%Y-%m-%d %H-%M-%S")))
        self.parameters.full_name = unicode(self.ui.edit_full_name.text())
        self.parameters.birthday_date = unicode(self.ui.dateEdit.text())
        self.parameters.exposition[400] = float(self.ui.e400Exposition.text())
        self.parameters.exposition[660] = float(self.ui.e660Exposition.text())
        self.parameters.exposition[740] = float(self.ui.e740Exposition.text())
        self.parameters.lighting_period = float(self.ui.ePeriod.text())
        self.parameters.camera_exposition = float(self.ui.eCameraExposition.text())
        self.parameters.exposition[0] = self.parameters.camera_exposition
        self.parameters.camera_gain = float(self.ui.eCameraGain.text())
        self.parameters.camera_binning = self.parameters.all_binnings[unicode(self.ui.cCameraBinning.currentText())][-1]
        self.parameters.image_size = self.parameters.all_binnings[unicode(self.ui.cCameraBinning.currentText())][0:2]
        self.parameters.save_full_protocol = self.ui.cFullProtocolSave.isChecked()
        self.parameters.use_autolevel = self.ui.cAutoLevel.isChecked()

        if self.ui.cCameraBit.currentIndex() == 0:
            self.parameters.camera_bits = 8

        if self.ui.cCameraBit.currentIndex() == 1:
            self.parameters.camera_bits = 12

        if self.ui.cNoneNormilize.isChecked():
            self.parameters.isNormalize = 1
        else:
            self.parameters.isNormalize = 0

        if self.ui.rShadowingNone.isChecked():
            self.parameters.tumor_shadowing_type = "None"

        if self.ui.rShadowingGlare.isChecked():
            self.parameters.tumor_shadowing_type = "glare"

        if self.ui.rShadowingContour.isChecked():
            self.parameters.tumor_shadowing_type = "contour"

    def load_experiment(self):
        filename = unicode(QtGui.QFileDialog.getOpenFileName(parent=self, caption='Open file', directory=self.ui.eLoggingFolder.text(), filter = "logging_storage.pkl"))
        if not filename:
            return
        obj = load_pickle_from_zip(filename)
        self.experimental_data_storage.update(obj)
        self.experimental_data_storage["basefolder"] = os.path.dirname(filename)
        self.experimental_data_storage['index'] = 0
        self.parameters = self.experimental_data_storage['parameters']

        self.change_param_working_state(False)
        self.ui.pSaveResults.setEnabled(False)
        self.apply_experimental_data_storage()

    def change_experimental_frame(self):
        if self.ui.spinFrameNumber.value() > self.ui.spinFrameNumber.maximum:
            self.ui.spinFrameNumber.setValue(self.ui.spinFrameNumber.maximum)
            return

        self.experimental_data_storage['index'] = self.ui.spinFrameNumber.value()
        self.apply_experimental_data_storage()

    def apply_experimental_data_storage(self):
        #self.ui.groupProtocol.resize(261, 101)
        self.ui.lExperimentFrame.setText(u"Кадр № ")
        self.ui.lExperimentFrame_2.setText(u" из {total}".format(total=len(self.experimental_data_storage['info']) - 1))
        self.ui.spinFrameNumber.maximum = len(self.experimental_data_storage['info']) - 1
        ind = self.experimental_data_storage['index']

        data_filename = self.experimental_data_storage['info'][ind]['data_filename']
        if os.path.exists(data_filename):
            data = load_pickle_from_zip(data_filename)
        else:
            filename = os.path.basename(data_filename)
            data_filename = self.experimental_data_storage["basefolder"] + "\\FULL\\"+filename
            data = load_pickle_from_zip(data_filename)

        if 'experimental_data' in data:
            self.experimental_data = data['experimental_data']
        else:
            self.experimental_data = ExperimentalData.ExperimentalData()

        self.parameters = data['parameters']
        wavelenghts = self.monitoring.tumor_area.keys()
        self.monitoring = data['monitoring']

        if not self.experimental_data.image:
            for wl in (0, 400, 660, 740):
                if os.path.exists(self.experimental_data_storage['info'][ind]['image_filenames'][wl]):
                    imagefilename = self.experimental_data_storage['info'][ind]['image_filenames'][wl]
                else:
                    imagefilename = self.experimental_data_storage["basefolder"] + self.experimental_data_storage['info'][ind]['image_filenames_rel'][wl]
                if os.path.exists(imagefilename):
                    self.experimental_data.image[wl] = tiff.imread(imagefilename)

            for wl in (400, 660):
                if os.path.exists(self.experimental_data_storage['info'][ind]['image_superposition_filenames'][wl]):
                    imagefilename = self.experimental_data_storage['info'][ind]['image_superposition_filenames'][wl]
                else:
                    imagefilename = self.experimental_data_storage["basefolder"] + self.experimental_data_storage['info'][ind]['image_superposition_filenames_rel'][wl]

                if os.path.exists(imagefilename):
                    self.experimental_data.image_superposition_rgb[wl] = cv2.imread(imagefilename.encode('cp1251', 'ignore')) #utf-8 cp1251



        if not self.experimental_data.graph_image_data:
            for wl in self.experimental_data.image.keys():
                self.experimental_data.graph_image_data[wl] = {}

        if not self.experimental_data.graph_image_superposition_data:
            for wl in self.experimental_data.image.keys():
                self.experimental_data.graph_image_superposition_data[wl] = {}


        for wl in self.experimental_data.image.iterkeys():
            image = self.experimental_data.image[wl]
            if image is not None:
                image = image.astype(np.float)

                # Вычитание фона
                if self.experimental_data.image[0] is not None:
                   self.experimental_data.image_cleared[wl] = image - self.parameters.use_black_image * self.experimental_data.image[0]
                   self.experimental_data.image_cleared[wl][self.experimental_data.image_cleared[wl] < 0] = 0
                else:
                    self.experimental_data.image_cleared[wl] = image.copy()
                self.experimental_data.image_cleared_with_contours_rbg[wl] = self.experimental_data.image_cleared[wl].copy()


        if self.ui.combo_selected_image.currentIndex() == -1:
            ind = 1
        else:
            ind = self.ui.combo_selected_image.currentIndex()

        self.ui.combo_selected_image.currentIndexChanged.disconnect(self.combo_selected_image_changed)
        self.ui.combo_selected_image.clear()

        if len(self.experimental_data.image_cleared_with_contours_rbg.keys()) == 0:
            self.ui.combo_selected_image.addItem(u"400 нм")
            self.ui.combo_selected_image.addItem(u"темновой кадр")
            self.ui.combo_selected_image.addItem(u"660 нм")

        for wavelenght in self.experimental_data.image_cleared_with_contours_rbg.keys():
            if wavelenght == 400:
                self.ui.combo_selected_image.addItem(u"400 нм")
            if wavelenght == 0:
                self.ui.combo_selected_image.addItem(u"темновой кадр")
            if wavelenght == 660:
                self.ui.combo_selected_image.addItem(u"660 нм")


        self.ui.combo_selected_image.setCurrentIndex(ind)
        self.ui.combo_selected_image.currentIndexChanged.connect(self.combo_selected_image_changed)

        self.update_data_on_screen(image_changed=False)
        self.update_monitoring_plots()

        if self.monitoring.stopwatch_laser_on['current_value'] is not None:
            m, s = divmod(self.monitoring.stopwatch_laser_on['current_value'], 60)
        else:
            m, s = (0, 0)
        stopwatch_str="%02d:%02d" % (m, s)
        self.ui.lcdNumber.display(stopwatch_str)

        wavelength = self.get_selected_image_wavelength_on_graph_image()

        str_properties = self.experimental_data.properties.make_string(wavelength)
        if wavelength in self.experimental_data.tumor_data and 'rectangle' in self.experimental_data.tumor_data[wavelength] and self.experimental_data.tumor_data[wavelength]['rectangle'] is not None:
            x,y,wl,h=self.experimental_data.tumor_data[wavelength]['rectangle']
            str_properties += u"\nРазмеры фл. области: ({w:4.2f},{h:4.2f}) мм".format(w=wl * self.parameters.x_mm_in_pixel, h=h * self.parameters.y_mm_in_pixel)

        if self.monitoring.burn and wavelength in self.monitoring.burn and len(self.monitoring.burn[wavelength]) > 0:
            str_properties += u"\nВыгорание: {burn:3.2f}".format(burn=self.monitoring.burn[wavelength][-1])
        if self.monitoring.contrast and wavelength in self.monitoring.contrast and len(self.monitoring.contrast[wavelength]) > 0:
            str_properties += u"\nКонтраст: {contrast:3.2f}".format(contrast=self.monitoring.contrast[wavelength][-1])

    def keyPressEvent(self, event):
        if event.key() == QtCore.Qt.Key_Left:
            if self.experimental_data_storage:
                self.previous_data()

        if event.key() == QtCore.Qt.Key_Right:
            if self.experimental_data_storage:
                self.next_data()

    def exposition_changed(self):
        exposition_leds_data = (('e400Exposition', 'pBlueSingle'), ('e660Exposition', 'pRedSingle'), ('e740Exposition', 'pIRSingle'))
        min_led_exposition = 0.001
        min_camera_exposition = 0.1

        expositions = []

        for (edit_exposition_name, push_single) in exposition_leds_data:
            edit_exposition = self.ui.__getattribute__(edit_exposition_name)
            exposition_text = str(edit_exposition.text())
            if exposition_text.replace('.','',1).isdigit():
                exposition = float(exposition_text)
                edit_exposition.setText(str(max(exposition,min_led_exposition)))
                expositions.append(float(edit_exposition.text()))
                edit_exposition.setStyleSheet("background-color: None")
                self.change_param_working_state(True)
                self.ui.__getattribute__(push_single).setEnabled(True)
            else:
                edit_exposition.setStyleSheet("background-color: red")
                self.change_param_working_state(False)

        expositions.append(min_camera_exposition)

        camera_exposition = max(expositions)
        camera_period = camera_exposition + 0.05
        self.ui.eCameraExposition.setText(str(camera_exposition))
        self.ui.ePeriod.setText(str(camera_period))

    def run_livemode(self, leds):
        self.parse_parameters_from_form()
        if self.parameters.camera_bits == 8:
            self.fluocontrollers.camera_controller.SetFormat(constants.DF_RAW8)
            MaxVal = 2 ** 8

        if self.parameters.camera_bits == 12:
            self.fluocontrollers.camera_controller.SetFormat(constants.DF_RAW12)
            MaxVal = 2 ** 12

        self.fluocontrollers.lighting_controller.SetPeriod(int(0.1 * 1e6))
        self.fluocontrollers.camera_controller.SetExposureTime(int(0.001 * 1e6))
        self.fluocontrollers.lighting_controller.SetLightingMode(0, leds, int(1 * 1e6))
        self.fluocontrollers.lighting_controller.SetModesNumber(1)
        self.fluocontrollers.camera_controller.SetGain(int(self.parameters.camera_gain))
        self.fluocontrollers.camera_controller.SetBinningMode(self.parameters.camera_binning)
        self.fluocontrollers.storage_controller.Clear()
        self.fluorcontroller_start()

        img = pyqtgraph.ImageItem(numpy.zeros((10,10)))

        Cont = True
        while Cont:
            try:
                if self.fluocontrollers.storage_controller.GetCount() > 0:  # storage_controller.GetCount()
                    Frame = self.fluocontrollers.fluo_controller.GetFrame()
                    FrameData = Frame.GetData()
                    frame = numpy.frombuffer(FrameData, numpy.uint32)

                    frame = frame.reshape(self.parameters.image_size)
                    frame = numpy.transpose(frame.astype(numpy.uint16))
                    if self.parameters.flip_images:
                        frame = cv2.flip(frame, -1)

                    img.setImage(self.convert_to_8bit(frame, MaxVal))

            except Exception, e:
                print e.message
                Cont = False
                pass

        self.fluorcontroller_stop()

    def fluorcontroller_start_single_led_with_parameters(self, light_period, camera_exposition, led, gain=15, binning=None):
        self.fluocontrollers.lighting_controller.SetPeriod(light_period)
        self.fluocontrollers.camera_controller.SetExposureTime(camera_exposition)
        self.fluocontrollers.lighting_controller.SetLightingMode(0, led, camera_exposition)
        self.fluocontrollers.lighting_controller.SetModesNumber(1)
        self.fluocontrollers.camera_controller.SetGain(gain)
        binning = constants.BIN_NONE if binning==None else binning
        self.fluocontrollers.camera_controller.SetBinningMode(binning)
        self.fluocontrollers.storage_controller.Clear()
        self.fluorcontroller_start()

    def push_livemode_clicked(self):
        self.parse_parameters_from_form()
        if self.parameters.camera_bits == 8:
            self.fluocontrollers.camera_controller.SetFormat(constants.DF_RAW8)
            MaxVal = 2 ** 8

        if self.parameters.camera_bits == 12:
            self.fluocontrollers.camera_controller.SetFormat(constants.DF_RAW12)
            MaxVal = 2 ** 12

        livemode_led_index = 0
        camera_exposition_denominator = {}
        camera_exposition_denominator[(constants.LM_IR)] = 150
        camera_exposition_denominator[(constants.LM_RED)] = 3
        camera_exposition_denominator[(constants.LM_BLUE)] = 3
        camera_exposition_denominator[(constants.LM_RED | constants.LM_BLUE)] = 10
        camera_exposition_denominator[(constants.LM_NONE)] = 10

        camera_exposition = lambda x: int(1.0/x * 1e6)
        led = self.parameters.livemode_leds[livemode_led_index]

        light_period = camera_exposition(camera_exposition_denominator[led]) + 1e5

        self.fluorcontroller_start_single_led_with_parameters(light_period=light_period, camera_exposition=camera_exposition(camera_exposition_denominator[led]), led=self.parameters.livemode_leds[livemode_led_index], gain=15, binning=constants.BIN_NONE)

        self.livemode_block_buttons = False
        Cont = True
        while Cont:
            try:
                if self.fluocontrollers.storage_controller.GetCount() > 0:  # storage_controller.GetCount()
                    Frame = self.fluocontrollers.fluo_controller.GetFrame()
                    FrameData = Frame.GetData()
                    frame = numpy.frombuffer(FrameData, numpy.uint32)

                    frame = frame.reshape(self.parameters.image_size)
                    frame = frame.astype(numpy.uint16)

                    if self.parameters.livemode_leds[livemode_led_index] == (constants.LM_IR):
                        caption = "IR led, "
                    if self.parameters.livemode_leds[livemode_led_index] == (constants.LM_RED):
                        caption = "RED led, "
                    if self.parameters.livemode_leds[livemode_led_index] == (constants.LM_BLUE):
                        caption = "BLUE led, "
                    if self.parameters.livemode_leds[livemode_led_index] == (constants.LM_RED | constants.LM_BLUE):
                        caption = "RED + BLUE leds, "
                    if self.parameters.livemode_leds[livemode_led_index] == (constants.LM_NONE):
                        caption = "Leds off, "

                    caption += "exposition {exposition:3.1f} s".format(exposition=camera_exposition(camera_exposition_denominator[led])/1e6)
                    # caption = caption.encode('cp1251', 'ignore')
                    # caption = unicode(caption.encode('cp1251', 'ignore')) #.decode("cp1251").encode()

                    frame = self.convert_to_8bit(frame, MaxVal)
                    if self.parameters.flip_images:
                        frame = cv2.flip(frame, -1)

                    color_frame = cv2.cvtColor(frame, cv2.COLOR_GRAY2BGR)
                    cv2.putText(img=color_frame, text=caption, org=(20,50), fontFace=cv2.FONT_HERSHEY_SIMPLEX, fontScale=1, color=[255,255,255])

                    cv2.imshow("Press Esc to exit... ", color_frame)
                    key = cv2.waitKey(10)
                    if key == 0x1b:  # ESC
                        Cont = False

                    if cv2.getWindowProperty("Press Esc to exit... ", 0) < 0:
                        Cont = False

                    if key == 2555904 and self.livemode_block_buttons is False:      # Right
                        self.livemode_block_buttons = True
                        self.fluorcontroller_stop()
                        livemode_led_index = (livemode_led_index + 1) % len(self.parameters.livemode_leds)
                        led = self.parameters.livemode_leds[livemode_led_index]
                        self.fluorcontroller_start_single_led_with_parameters(light_period=light_period, camera_exposition=camera_exposition(camera_exposition_denominator[led]), led=led, gain=15, binning=constants.BIN_NONE)

                    if key == 2424832 and self.livemode_block_buttons is False:      #Left
                        self.livemode_block_buttons = True
                        self.fluorcontroller_stop()
                        livemode_led_index = (livemode_led_index - 1) % len(self.parameters.livemode_leds)
                        led = self.parameters.livemode_leds[livemode_led_index]
                        self.fluorcontroller_start_single_led_with_parameters(light_period=light_period, camera_exposition=camera_exposition(camera_exposition_denominator[led]), led=led, gain=15, binning=constants.BIN_NONE)

                    if key == 2490368 and self.livemode_block_buttons is False:      #up
                        self.livemode_block_buttons = True
                        self.fluorcontroller_stop()
                        camera_exposition_denominator[led] -= 1
                        self.fluorcontroller_start_single_led_with_parameters(light_period=light_period, camera_exposition=camera_exposition(camera_exposition_denominator[led]), led=led, gain=15, binning=constants.BIN_NONE)

                    if key == 2621440 and self.livemode_block_buttons is False:          #down
                        self.livemode_block_buttons = True
                        self.fluorcontroller_stop()
                        camera_exposition_denominator[led] += 1
                        self.fluorcontroller_start_single_led_with_parameters(light_period=light_period, camera_exposition=camera_exposition(camera_exposition_denominator[led]), led=led, gain=15, binning=constants.BIN_NONE)

                    self.livemode_block_buttons = False
# Upkey : 2490368
# DownKey : 2621440
                    # LeftKey : 2424832
                    # RightKey: 2555904


            except Exception, e:
                print e.message
                pass

        cv2.destroyAllWindows()
        self.fluorcontroller_stop()
        self.ui.pStart.setText(u"СТАРТ")

    def save_results_folder_dialog(self):
        pathame = QtGui.QFileDialog.getExistingDirectory(self, 'Choose folder', '', QtGui.QFileDialog.ShowDirsOnly)
        if not pathame:
            return
        self.ui.eLoggingFolder.setText(unicode(pathame))

    def change_param_interface_state(self, state):
        self.ui.edit_full_name.setEnabled(state)
        self.ui.e400Exposition.setEnabled(state)
        self.ui.e660Exposition.setEnabled(state)
        self.ui.e740Exposition.setEnabled(state)
        # self.ui.ePeriod.setEnabled(state)
        # self.ui.eCameraExposition.setEnabled(state)
        self.ui.eCameraGain.setEnabled(state)
        self.ui.cCameraBinning.setEnabled(state)
        self.ui.cCameraBit.setEnabled(state)
        self.ui.groupBoxLedSources.setEnabled(state)
        self.ui.groupBoxProtocol.setEnabled(state)
        self.ui.groupWatch.setEnabled(state)
        #self.ui.groupInterface.setEnabled(state)

    def change_param_working_state(self,state):
        self.ui.pStart.setEnabled(state)
        self.ui.pCalibration.setEnabled(state)
        self.ui.pLiveMode.setEnabled(state)
        self.ui.pBlueSingle.setEnabled(state)
        self.ui.pRedSingle.setEnabled(state)
        self.ui.pNoneSingle.setEnabled(state)
        self.ui.pIRSingle.setEnabled(state)


def save_pickle_to_zip(obj, filename, protocol=cPickle.HIGHEST_PROTOCOL, compresslevel=1):
    import time
    try:
        t1 = time.time()
        file = gzip.GzipFile(filename, 'wb', compresslevel)
        t2 = time.time()
        cPickle.dump(obj, file, protocol)
        t3 = time.time()
        file.close()
        t4 = time.time()

        return True
    except Exception, e:
        print e
        return False

def load_pickle_from_zip(filename):
    """Loads a compressed object from disk
    """
    t1 = time.time()
    file = gzip.GzipFile(filename, 'rb')
    t2 = time.time()
    obj = cPickle.load(file)
    t3 = time.time()
    #
    # print "file = gzip.GzipFile(filename, 'rb): ", t2 - t1
    # print "obj = cPickle.load(file) ", t3 - t2

    file.close()
    return copy.deepcopy(obj)

