import json
import logging
import random
import subprocess
import time

from PyQt5.QtCore import QThread, pyqtSignal, QDateTime, QObject, Qt, QTimer
from PyQt5.QtWidgets import QMainWindow, QFrame, QSplitter, QGridLayout, QWidget, QStackedLayout, QPushButton, \
    QVBoxLayout
import pyqtgraph as pg
import platform
import os
import qdarkstyle

import utils.utils_file_access
import utils.utils_system
from fpga.fpga_clients import FPGAClient
from global_def import *
from PyQt5.QtWidgets import QApplication

from media_engine.media_engine import MediaEngine
from ui.ui_fpga_list_page import FpgaListPage
from ui.ui_functions_frame import UiFuncFrame
from ui.ui_sys_sw_info import UiSystemSoftware
from ui.ui_media_files_page import MediaFilesPage
from ui.ui_hdmi_in_page import HDMIInPage
from ui.ui_led_settings_page import LedSettingsPage
from ui.ui_test_page import TestPage
from ext_qt_widgets.media_file_list import MediaFileList
from utils.utils_file_access import determine_file_match_platform, run_cmd_with_su
from FPGA_protocol.protocol2 import FPGACmdCenter, protocolDict, dataAddressDict, FPGAJsonParams

'''List of Page Selector Button Name '''
Page_Select_Btn_Name_List = ["FPGA_List", "Media_Files", "HDMI_In", "Led_Settings", "Test"]
Page_List = [FpgaListPage, MediaFilesPage, HDMIInPage, LedSettingsPage, TestPage]

Page_Map = dict(zip(Page_Select_Btn_Name_List, Page_List))


class MainUi(QMainWindow):

    def __init__(self):
        log.debug("Venom A Main Window Init!")
        super().__init__()
        pg.setConfigOptions(antialias=True)

        # run_cmd_with_su('sudo -S cp /usr/bin/test /usr/bin/testA', sudo_password='workout13')
        # run_cmd_with_su('cp /usr/bin/test /usr/bin/testC')

        eth_if_promisc_cmd = os.popen("ifconfig {} promisc".format(ETH_DEV))
        eth_if_promisc_cmd.close()

        utils.utils_file_access.set_os_environ()
        utils.utils_file_access.check_and_rebuild_binaries()

        if platform.machine() in ('arm', 'arm64', 'aarch64'):
            # keep the screen on for cms
            keep_screen_alive = os.popen("xset s off -dpms")
            keep_screen_alive.close()

            # open pulseaudio with root
            pulseaudio_with_root = os.popen("pulseaudio -D")
            pulseaudio_with_root.close()

            # export DISPLAY
            export_display = os.popen("export DISPLAY=:0")
            export_display.close()
        self.screen = QApplication.primaryScreen()

        '''main 3 object in window '''
        self.left_top_frame = None  # page selector
        self.left_bottom_frame = None  # system and software information
        self.splitter_left_vertical_frame = None  # group of upon widgets
        self.right_frame = None  # multi pages of different functions(fpga receiver/media files/hdmi-in )
        self.right_layout = None
        self.left_top_frame_layout = None
        self.left_bottom_frame_layout = None
        self.ui_funcs_select_frame = None
        self.ui_sys_sw_info_frame = None

        ''' each pages of right frame'''
        self.right_frame_page_list = []
        self.right_frame_page_index = 0

        self.splitter_horizontal_frame = None  # group of main window widgets
        self.main_window_layout = None
        self.main_window_widget = None

        self.media_engine = MediaEngine()

        ''' Jason for test FPGA read/write '''
        self.fpga_cmd_center = FPGACmdCenter(ETH_DEV, protocolDict["sourceAddress"])
        self.fpga_cmd_center.set_fpga_id_broadcast(FPGA_START_ID)

        ''' fpga_list initial '''
        self.fpga_json_data = []
        self.fpga_total_num = self.get_fpga_total_num()
        log.debug("self.fpga_total_num : %d", self.fpga_total_num)
        self.fpga_list = []
        for i in range(FPGA_START_ID, FPGA_START_ID + self.fpga_total_num):
            fpga_tmp = FPGAClient(i, self.fpga_cmd_center)
            self.fpga_list.append(fpga_tmp)

        self.init_ui_total()
        log.debug("Init UI ok!")

        self.right_frame_page_list[0].sync_clients_table(self.fpga_list)

        ret, str_value = self.fpga_cmd_center.read_fpga_register(2, FPGAJsonParams.params_list[0])
        if ret == 0:
            log.debug("read device ID from id2, ret : %d, str_value: %s", ret, str_value)
        self.init_fpga_json_file()

        # self.right_frame_page_list[0].cmd_frame_res_test()
        # self.fpga_cmd_center.set_fpga_write_flash()
        # time.sleep(1)
        # self.fpga_cmd_center.set_fpga_read_flash()
        # self.init_fpga_json_file()
        '''self.utc_test_count = 0
        self.test_timer = QTimer(self)
        self.test_timer.timeout.connect(self.utc_test)
        self.test_timer.start(3 * 1000)'''

    def utc_test(self):
        log.debug("self.utc_test_count : %d", self.utc_test_count)
        self.utc_test_count += 1
        s_utc_temp = str(random.randint(1000, 9999))
        for i in range(2, 4):   # send cmd to id 2/3
            start_time = time.time()
            ret = self.fpga_cmd_center.write_fpga_register(i, "UTC", s_utc_temp)
            log.debug("write time : %f", time.time() - start_time)
            log.debug("write fpga id:%d UTC ret : %d", i, ret)
        for i in range(2, 4):   # read cmd to id 2/3
            start_time = time.time()
            ret, id_utc = self.fpga_cmd_center.read_fpga_register(i, "UTC")
            log.debug("read time : %f", time.time() - start_time)
            # log.debug("read fpga id:%d UTC ret : %d, id%d_UTC : %s", i, ret, i, id_utc)
            # log.debug("len(s_utc_temp) : %d", len(s_utc_temp))
            # log.debug("len(id2_utc) : %d", len(str(id2_utc)))
            if ret == 0:
                if s_utc_temp == str(id_utc):
                    log.debug("read OK")
                else:
                    log.debug("UTC read/write failed!")
            else:
                log.debug("UTC read/write failed!")



    def init_ui_total(self):
        self.setWindowTitle("GIS FPGA LED Server")
        self.setWindowOpacity(1.0)  # 窗口透明度
        self.setStyleSheet(qdarkstyle.load_stylesheet_pyqt5())

        log.debug("self.screen.size() : %s", self.screen.size())
        self.resize(self.screen.size())

        self.left_top_frame = QFrame(self)
        self.left_top_frame_layout = QVBoxLayout()
        self.left_top_frame.setLayout(self.left_top_frame_layout)
        self.left_bottom_frame = QFrame(self)
        self.left_bottom_frame_layout = QVBoxLayout()
        self.left_bottom_frame.setLayout(self.left_bottom_frame_layout)
        self.right_frame = QFrame(self)  # right frame with stack layout
        self.splitter_left_vertical_frame = QSplitter(Qt.Vertical)
        self.splitter_left_vertical_frame.addWidget(self.left_top_frame)
        self.splitter_left_vertical_frame.addWidget(self.left_bottom_frame)
        self.splitter_horizontal_frame = QSplitter(Qt.Horizontal)
        self.splitter_horizontal_frame.addWidget(self.splitter_left_vertical_frame)
        self.splitter_horizontal_frame.addWidget(self.right_frame)

        self.main_window_layout = QGridLayout()
        self.main_window_layout.addWidget(self.splitter_horizontal_frame)
        self.main_window_widget = QWidget(self)
        self.main_window_widget.setLayout(self.main_window_layout)
        self.setCentralWidget(self.main_window_widget)

        ''' handle right frame layout '''
        self.right_layout = QStackedLayout()
        self.right_frame.setLayout(self.right_layout)

        self.init_system_and_software_info()
        self.init_page_selector()

        '''Initial each page in stack layout of right frame'''
        self.init_pages_on_right_frame()

        self.right_layout.setCurrentIndex(0)

    def init_page_selector(self):
        self.ui_funcs_select_frame = UiFuncFrame(self, self.left_top_frame,
                                                 Page_Select_Btn_Name_List,
                                                 self.slot_right_frame_page_changed)

    def init_system_and_software_info(self):
        self.ui_sys_sw_info_frame = UiSystemSoftware(self, self.left_bottom_frame)

    def init_pages_on_right_frame(self):
        for k, v in Page_Map.items():
            if k == "FPGA_List" or k == "Led_Settings":
                page = v(self, self.right_frame, k, media_engine=self.media_engine, fpga_list=self.fpga_list)
            else:
                page = v(self, self.right_frame, k, media_engine=self.media_engine)
            self.right_frame_page_list.append(page)
            self.right_layout.addWidget(page)

    def slot_right_frame_page_changed(self, tag: str):
        log.debug("tag : %s", tag)
        try:
            for i in range(len(self.right_frame_page_list)):
                if self.right_frame_page_list[i].name == tag:
                    self.right_layout.setCurrentIndex(i)
                    self.right_frame_page_index = i
                    break
        except Exception as e:
            log.error(e)

    def get_fpga_total_num(self):
        num = 0
        for i in range(FPGA_START_ID, 255):
            ret, id_utc = self.fpga_cmd_center.read_fpga_register(i, "UTC")
            if ret != 0:
                num = i - 2
                break
        log.debug("fpga num : %d", num)
        return num

    def load_fpga_json_file(self):
        log.debug("load_fpga_json_file")
        with open(os.getcwd() + "/ori_dataFPGA.json", "r") as jsonFile:
            python_dict = json.load(fp=jsonFile)
            log.debug("python_dict : %s", python_dict)
            print("type(python_dict) : ", type(python_dict))
            python_dict["fpgaID"][2]["UTC"] = str(1111)
            log.debug("python_dict : %s", python_dict)

    def init_fpga_json_file(self):
        data = dict()
        data["frameWidth"] = '0'
        data["frameHeight"] = '0'
        data["softwareVersion"] = 'LC_G3_240220_D1'
        data["lcdVersion"] = 'LS240305001'
        data["fpgaID"] = []
        params = {}
        '''for i in range(2):
            params["deviceID"] = "2"
            params["UTC"] = "test"
            params["MD5"] = "test"
            data["fpgaID"].append(params)
        # data["fpgaID"][self.fpga_total_num] = dict()'''

        for i in range(FPGA_START_ID, FPGA_START_ID + self.fpga_total_num):
            params = {}
            for j in range(len(FPGAJsonParams.params_list)):
                log.debug("read id: %d, %s", i , FPGAJsonParams.params_list[j])
                ret, str_value = self.fpga_cmd_center.read_fpga_register(i, FPGAJsonParams.params_list[j])

                if ret == 0:
                    params[FPGAJsonParams.params_list[j]] = str_value
                else:
                    params[FPGAJsonParams.params_list[j]] = "unknown"
            data["fpgaID"].append(params)
            params = None

        with open("dataFPGA.json", "w") as jsonFile:
            json.dump(data, jsonFile, indent=2)
            print('write json')
