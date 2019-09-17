__author__ = 'Fl'
from win32com.client import constants
import win32com.client
from win32com.client import gencache
import win32com.client.CLSIDToClass, pythoncom
import win32com.client.util
win32com.client.gencache.is_readonly=False
# win32com.client.gencache.GetGeneratePath()


class FluoControllers:
    fluo_controller = None
    camera_controller = None
    storage_controller = None
    lighting_controller = None

    def __init__(self):
        gencache.EnsureModule('{A9F10BB8-C2CA-4DC9-A034-9E0327384682}', 0, 1, 0)

        # self.fluo_controller = win32com.client.Dispatch(u"FluoController.FluoControl")#win32com.client.Dispatch(u"FluoController.FluoControl") #gencache.EnsureDispatch(u"FluoController.FluoControl") #win32com.client.Dispatch(u"FluoController.FluoControl")
        self.fluo_controller = gencache.EnsureDispatch(u"FluoController.FluoControl")

        print self.fluo_controller
        StorageDisp = self.fluo_controller._oleobj_.QueryInterface(
            "{2C0DEA94-1EA8-4AC2-98E7-A04C62AA9F1F}", pythoncom.IID_IDispatch)
        self.storage_controller = win32com.client.Dispatch(StorageDisp)
        CameraDisp = self.fluo_controller._oleobj_.QueryInterface(
            "{FAEA1FE6-813C-43BC-8478-933F5B6D74F4}", pythoncom.IID_IDispatch)
        self.camera_controller = win32com.client.Dispatch(CameraDisp)
        self.camera_controller.SetTriggerMode(constants.TRIG_ARD)
        self.camera_controller.SetFormat(constants.DF_RAW12)
        LightingDisp = self.fluo_controller._oleobj_.QueryInterface(
            "{30046501-A1A4-40BA-BDDA-9A50AB93A6F0}", pythoncom.IID_IDispatch)
        self.lighting_controller = win32com.client.Dispatch(LightingDisp)

    def __del__(self):
        del self.fluo_controller
        del self.storage_controller
        del self.camera_controller
        del self.lighting_controller