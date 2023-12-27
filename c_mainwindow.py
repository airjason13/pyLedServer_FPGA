import logging

from PyQt5.QtCore import QThread, pyqtSignal, QDateTime, QObject, Qt
from PyQt5.QtWidgets import QMainWindow, QFrame, QSplitter, QGridLayout, QWidget, QStackedLayout, QPushButton, \
    QVBoxLayout
import pyqtgraph as pg
import platform
import os
import qdarkstyle

import utils.utils_file_access
from global_def import *
from PyQt5.QtWidgets import QApplication

from ui.ui_fpga_list_page import FpgaListPage
from ui.ui_functions_frame import UiFuncFrame
from ui.ui_sys_sw_info import UiSystemSoftware
from ui.ui_media_files_page import MediaFilesPage
from ui.ui_hdmi_in_page import HDMIInPage
from ui.ui_led_settings_page import LedSettingsPage
from ui.ui_test_page import TestPage
from ext_qt_widgets.media_file_list import MediaFileList

'''List of Page Selector Button Name '''
Page_Select_Btn_Name_List = ["FPGA_List", "Media_Files", "HDMI_In", "Led_Settings", "Test"]
Page_List = [FpgaListPage, MediaFilesPage, HDMIInPage, LedSettingsPage, TestPage]

Page_Map = dict(zip(Page_Select_Btn_Name_List, Page_List))


class MainUi(QMainWindow):

    def __init__(self):
        log.debug("Main Window Init!")
        super().__init__()
        pg.setConfigOptions(antialias=True)

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
        self.left_bottom_frame = None   # system and software information
        self.splitter_left_vertical_frame = None    # group of upon widgets
        self.right_frame = None     # multi pages of different functions(fpga receiver/media files/hdmi-in )
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

        ''' fpga_list initial '''
        self.fpga_list = []

        log.debug("%s", )

        self.init_ui_total()

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
        self.right_frame = QFrame(self)     # right frame with stack layout
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
                page = v(self, self.right_frame, k, self.fpga_list)
            else:
                page = v(self, self.right_frame, k)
            self.right_frame_page_list.append(page)
            self.right_layout.addWidget(page)

    def slot_right_frame_page_changed(self, tag: str):
        log.debug("tag : %s", tag)
        try:
            for i in range(len(self.right_frame_page_list)):
                if self.right_frame_page_list[i].name == tag:
                    self.right_layout.setCurrentIndex(i)
                    break
        except Exception as e:
            log.error(e)




