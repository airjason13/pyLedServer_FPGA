import json
import random
import subprocess
import time

import qdarkstyle
from PyQt5.QtCore import Qt, QTimer
from PyQt5.QtWidgets import QApplication
from PyQt5.QtWidgets import QMainWindow, QFrame, QSplitter, QGridLayout, QWidget, QStackedLayout, QVBoxLayout

import utils.utils_file_access
import utils.utils_system
from FPGA_protocol.gamma import init_gamma_table_list, gamma_table_list, max_gamma_value
from FPGA_protocol.protocol2 import FPGACmdCenter, protocolDict, FPGAJsonParams, fpga_test_value
from fpga.fpga_clients import FPGAClient
from global_def import *
from media_engine.media_engine import MediaEngine
from ui.ui_fpga_list_page import FpgaListPage
from ui.ui_functions_frame import UiFuncFrame
from ui.ui_hdmi_in_page import HDMIInPage
from ui.ui_led_settings_page import LedSettingsPage
from ui.ui_media_files_page import MediaFilesPage
from ui.ui_sys_sw_info import UiSystemSoftware
from ui.ui_test_page import TestPage

'''List of Page Selector Button Name '''
Page_Select_Btn_Name_List = ["FPGA_List", "Media_Files", "HDMI_In", "Led_Settings", "Test"]
Page_List = [FpgaListPage, MediaFilesPage, HDMIInPage, LedSettingsPage, TestPage]

Page_Map = dict(zip(Page_Select_Btn_Name_List, Page_List))


class MainUi(QMainWindow):
    from _handle_qlocal_message import parser_cmd_from_qlocalserver, cmd_function_map
    from _handle_brightness_by_time import check_brightness_by_date_timer, is_sleep_time, check_daymode_nightmode
    '''frame brightness test log'''
    brightness_test_log = False

    def __init__(self):
        log.debug("Venom Main Window Init!")
        super().__init__()

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
        self.media_engine.led_video_params.install_fpga_current_gain_changed_slot(self.fpga_current_gain_changed)
        self.media_engine.led_video_params.install_fpga_gamma_index_changed_slot(self.fpga_gamma_index_changed)

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

        ret, str_value = self.fpga_cmd_center.read_fpga_register(2, FPGAJsonParams.params_list[0])
        if ret == 0:
            log.debug("read device ID from id2, ret : %d, str_value: %s", ret, str_value)
        self.init_fpga_json_file()

        self.init_ui_total()
        log.debug("Init UI ok!")

        self.right_frame_page_list[0].sync_clients_table(self.fpga_list)

        self.init_fpga_gamma()

        # self.set_fpga_test_register()

        for fpga in self.fpga_list:
            fpga.fpga_cmd_center.write_fpga_register(fpga.i_id, 'currentGammaTable', str(22))

        self.sleep_start_time, self.sleep_end_time = utils.utils_file_access.get_sleep_time_from_file()
        log.debug("self.sleep_start_time = %s", self.sleep_start_time)
        log.debug("self.sleep_end_time = %s", self.sleep_end_time)
        self.i_sleep_start_time_hour = int(self.sleep_start_time.split(":")[0])
        self.i_sleep_start_time_min = int(self.sleep_start_time.split(":")[1])
        self.i_sleep_end_time_hour = int(self.sleep_end_time.split(":")[0])
        self.i_sleep_end_time_min = int(self.sleep_end_time.split(":")[1])

        self.date_timer = QTimer(self)
        self.date_timer.timeout.connect(self.check_brightness_by_date_timer)
        # self.date_timer.start(1*60*1000)
        try:
            self.date_timer.start(BRIGHTNESS_TIMER_INTERVAL)
        except Exception as e:
            log.debug(e)

        self.default_launch_type_int = 0
        self.default_launch_params_str = ""
        self.launch_default_type()
        # test frame brightness adjust
        # self.test_timer = QTimer(self)
        # self.test_timer.timeout.connect(self.test_timer_function)
        # self.test_timer.start(3*1000)

        '''target_gamma_table_list = [
            "gammaTable_r{}".format(str(0)),
            "gammaTable_g{}".format(str(0)),
            "gammaTable_b{}".format(str(0))
        ]
        for fpga in self.fpga_list:
            ret, reg_value = self.fpga_cmd_center.read_fpga_register(fpga.i_id, "gammaTable_r{}".format(str(0)))
            # log.debug("%s : %s",  "gammaTable_r{}".format(str(0)), str(reg_value))
            ret, reg_value = self.fpga_cmd_center.read_fpga_register(fpga.i_id, "gammaTable_g{}".format(str(0)))
            # log.debug("%s : %s", "gammaTable_g{}".format(str(0)), str(reg_value))
            ret, reg_value = self.fpga_cmd_center.read_fpga_register(fpga.i_id, "gammaTable_b{}".format(str(0)))
            # log.debug("%s : %s", "gammaTable_b{}".format(str(0)), str(reg_value))'''

    def launch_default_type(self):
        try:
            with open(os.getcwd() + "/static/default_launch_type.dat", "r") as launch_type_config_file:
                tmp = launch_type_config_file.readline()
                log.debug("launch_type_config : %s", tmp)

                self.default_launch_type_int = int(tmp.split(":")[0])
                self.default_launch_params_str = tmp.split(":")[1]
                log.debug("self.default_launch_type_int : %d", self.default_launch_type_int)
                log.debug("self.default_launch_params_str : %s", self.default_launch_params_str)
        except Exception as e:
            log.debug(e)

        if self.default_launch_type_int == play_type.play_single:
            try:
                QTimer.singleShot(5000, self.demo_start_play_single)
            except Exception as e:
                log.debug(e)
        elif self.default_launch_type_int == play_type.play_playlist:
            try:
                QTimer.singleShot(5000, self.demo_start_playlist)
            except Exception as e:
                log.debug(e)
        elif self.default_launch_type_int == play_type.play_hdmi_in:
            try:
                QTimer.singleShot(5000, self.demo_start_hdmi_in)
            except Exception as e:
                log.debug(e)

    def demo_start_play_single(self):
        log.debug("demo_start_play_single")
        for btn in self.ui_funcs_select_frame.btn_list:
            log.debug("btn : %s", btn.text())
            if btn.text() == 'Media_Files':
                btn.click()
                break
        file_uri = internal_media_folder + '/' + self.default_launch_params_str
        self.media_engine.single_play(file_uri)

    def demo_start_playlist(self):
        log.debug("demo_start_playlist")
        for btn in self.ui_funcs_select_frame.btn_list:
            log.debug("btn : %s", btn.text())
            if btn.text() == 'Media_Files':
                btn.click()
                break
        playlist = internal_media_folder + PlaylistFolder + self.default_launch_params_str
        self.media_engine.play_playlist(playlist)

    def demo_start_hdmi_in(self):
        log.debug("demo_start_hdmi_in")
        for btn in self.ui_funcs_select_frame.btn_list:
            log.debug("btn : %s", btn.text())
            if btn.text() == 'HDMI_In':
                btn.click()
                break

        # self.media_engine.hdmi_in_play()

    def utc_test(self):
        log.debug("self.utc_test_count : %d", self.utc_test_count)
        self.utc_test_count += 1
        s_utc_temp = str(random.randint(1000, 9999))
        for i in range(2, 4):  # send cmd to id 2/3
            start_time = time.time()
            ret = self.fpga_cmd_center.write_fpga_register(i, "UTC", s_utc_temp)
            log.debug("write time : %f", time.time() - start_time)
            log.debug("write fpga id:%d UTC ret : %d", i, ret)
        for i in range(2, 4):  # read cmd to id 2/3
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
            elif k == "Test":
                page = v(self, self.right_frame, k, media_engine=self.media_engine,
                         fpga_cmd_center=self.fpga_cmd_center, fpga_list=self.fpga_list)
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

    def get_fpga_panel_way(self):
        for i in range(FPGA_START_ID, FPGA_START_ID + self.fpga_total_num):
            ret, i_panel_way = self.fpga_cmd_center.read_fpga_register(i, "panelWay")
            log.debug("id : %d, i_panel_way : %d", ret, i_panel_way)

    @staticmethod
    def load_fpga_json_file():
        log.debug("load_fpga_json_file")
        with open(os.getcwd() + "/ori_dataFPGA.json", "r") as jsonFile:
            python_dict = json.load(fp=jsonFile)
            log.debug("python_dict : %s", python_dict)
            # print("type(python_dict) : ", type(python_dict))
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

        for i in range(FPGA_START_ID, FPGA_START_ID + self.fpga_total_num):
            params = {}
            for j in range(len(FPGAJsonParams.params_list)):
                log.debug("read id: %d, %s", i, FPGAJsonParams.params_list[j])
                if FPGAJsonParams.params_list[j] == "stringVersion":
                    ret, reg_value = self.fpga_cmd_center.read_fpga_register_bytes(
                        i, FPGAJsonParams.params_list[j])
                    if ret == 0:
                        str_value = reg_value.decode().replace('\u0000', '')
                        for fpga in self.fpga_list:
                            if fpga.i_id == i:
                                fpga.set_version(str_value)
                    else:
                        str_value = "unknown"
                else:
                    ret, str_value = self.fpga_cmd_center.read_fpga_register(i, FPGAJsonParams.params_list[j])

                if ret == 0:
                    params[FPGAJsonParams.params_list[j]] = str_value
                else:
                    params[FPGAJsonParams.params_list[j]] = "unknown"
            data["fpgaID"].append(params)
            params = None

        with open("dataFPGA.json", "w") as jsonFile:
            json.dump(data, jsonFile, indent=2)
            log.debug('write json')

    def set_fpga_test_register(self):
        for i in range(FPGA_START_ID, FPGA_START_ID + len(self.fpga_list)):
            for test_item, value in fpga_test_value[i - 2].items():
                if value is not None:
                    ret = self.fpga_cmd_center.write_fpga_register(i, test_item, value)
                    if ret < 0:
                        log.debug("write register failed!")

            if i == 2:
                for n in range(0, 4):
                    self.fpga_cmd_center.write_fpga_register(i, 'numberOfPixel_p{}'.format(str(n)), str(960))
                    self.fpga_cmd_center.write_fpga_register(i, 'startX_p{}'.format(str(n)), str(159))
                    self.fpga_cmd_center.write_fpga_register(i, 'startY_p{}'.format(str(n)), str(48 - ((n + 1) * 12)))
                    self.fpga_cmd_center.write_fpga_register(i, 'portWidth_p{}'.format(str(n)), str(80))
                    self.fpga_cmd_center.write_fpga_register(i, 'portHeight_p{}'.format(str(n)), str(12))
            elif i == 3:
                for n in range(0, 4):
                    self.fpga_cmd_center.write_fpga_register(i, 'numberOfPixel_p{}'.format(str(n)), str(960))
                    self.fpga_cmd_center.write_fpga_register(i, 'startX_p{}'.format(str(n)), str(0))
                    self.fpga_cmd_center.write_fpga_register(i, 'startY_p{}'.format(str(n)), str((n * 12) + 11))
                    self.fpga_cmd_center.write_fpga_register(i, 'portWidth_p{}'.format(str(n)), str(80))
                    self.fpga_cmd_center.write_fpga_register(i, 'portHeight_p{}'.format(str(n)), str(12))

    def init_fpga_gamma(self):
        init_gamma_table_list()
        # print("gamma_table_list[22] : ", gamma_table_list[22])
        log.debug("len(gamma_table_list[22]) : %d", len(gamma_table_list[22]))

        for fpga in self.fpga_list:
            #  for gamma_index in range(max_gamma_value):
            for gamma_index in range(max_gamma_value):
                if gamma_index < 2:
                    fpga.fpga_cmd_center.write_fpga_register_with_bytes(fpga.i_id,
                                                                        'gammaTable_r{}'.format(str(gamma_index)),
                                                                        gamma_table_list[22])
                    fpga.fpga_cmd_center.write_fpga_register_with_bytes(fpga.i_id,
                                                                        'gammaTable_g{}'.format(str(gamma_index)),
                                                                        gamma_table_list[22])
                    fpga.fpga_cmd_center.write_fpga_register_with_bytes(fpga.i_id,
                                                                        'gammaTable_b{}'.format(str(gamma_index)),
                                                                        gamma_table_list[22])
                else:
                    fpga.fpga_cmd_center.write_fpga_register_with_bytes(fpga.i_id,
                                                                        'gammaTable_r{}'.format(str(gamma_index)),
                                                                        gamma_table_list[gamma_index])
                    fpga.fpga_cmd_center.write_fpga_register_with_bytes(fpga.i_id,
                                                                        'gammaTable_g{}'.format(str(gamma_index)),
                                                                        gamma_table_list[gamma_index])
                    fpga.fpga_cmd_center.write_fpga_register_with_bytes(fpga.i_id,
                                                                        'gammaTable_b{}'.format(str(gamma_index)),
                                                                        gamma_table_list[gamma_index])

    def fpga_current_gain_changed(self):
        ''' check video params and send cmd to fpga '''
        ''' check r/g/b/ current gain '''
        if self.media_engine.led_video_params.get_icled_type() == icled_type.anapex:
            ''' set current gain '''
            log.debug("anapex set current gain")
            i_r_gain_value = int(self.media_engine.led_video_params.get_led_red_gain())
            i_g_gain_value = int(self.media_engine.led_video_params.get_led_green_gain())
            i_b_gain_value = int(self.media_engine.led_video_params.get_led_blue_gain())
            i_current_gain_value = i_r_gain_value << 16 | i_g_gain_value << 8 | i_b_gain_value
            for fpga in self.fpga_list:
                fpga.fpga_cmd_center.write_fpga_register(fpga.i_id, "currentGain",
                                                         str(i_current_gain_value))

    def fpga_gamma_index_changed(self):
        ''' set fpga gamma '''
        log.debug("fpga_gamma_index_changed")
        for fpga in self.fpga_list:
            fpga.fpga_cmd_center.write_fpga_register(fpga.i_id, 'currentGammaTable',
                                                     str(self.media_engine.led_video_params.get_led_gamma()))
