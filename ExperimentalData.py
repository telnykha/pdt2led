__author__ = 'FiksII'
# -*- coding: utf-8 -*-
import Properties
import collections

class ExperimentalData(object):

    def __init__(self):
        self.image = {}
        self.image_temp = {}
        self.image_glare_prev = {}
        self.image_cleared = {}
        self.image_cleared_with_contours_rbg = {}  # Цветное изображние (сегментированнное)
        self.skin_data = {}
        self.tumor_data = {}
        self.image_superposition_rgb = {}
        self.is_first_image = {}
        self.mode = set()
        self.graph_image_data = {}
        self.graph_image_superposition_data = {}
        self.glare_status = collections.deque(maxlen=2)
        self.task_pool = []
        self.motion_data = {}
        self.max_image_value = 0
        self.working_leds = []
        self.properties = Properties.Properties()
        self.is_locked = False

        self.image[0]=None
        self.image[400]=None
        self.image[660]=None
        self.image[740]=None

        self.image_temp[400]=None
        self.image_temp[660]=None
        self.image_temp[740]=None

        self.image_glare_prev[0] = collections.deque(maxlen=5)

        self.image_cleared[0]=None
        self.image_cleared[400]=None
        self.image_cleared[660]=None
        self.image_cleared[740]=None

        self.image_cleared_with_contours_rbg[0]=None
        self.image_cleared_with_contours_rbg[400]=None
        self.image_cleared_with_contours_rbg[660]=None
        self.image_cleared_with_contours_rbg[740]=None

        self.skin_data[400]={}
        self.skin_data[660]={}

        self.tumor_data[400]={}
        self.tumor_data[660]={}

        self.image_superposition_rgb[400]=None
        self.image_superposition_rgb[660]=None

        self.is_first_image[0]=True
        self.is_first_image[400]=True
        self.is_first_image[660]=True
        self.is_first_image[740]=True

        self.tumor_data["color"] = [0, 255, 0]#[0xCF, 0xff, 0x9a]
        self.tumor_data["thickness"] = 5
        self.skin_data["color"]  = [255, 255, 255]
        self.skin_data["thickness"] = 5

        self.graph_image_data[0] = {}
        self.graph_image_data[400] = {}
        self.graph_image_data[660] = {}

        self.graph_image_superposition_data[0] = {}
        self.graph_image_superposition_data[400] = {}
        self.graph_image_superposition_data[660] = {}
