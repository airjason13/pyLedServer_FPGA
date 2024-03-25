import time
import subprocess
from PyQt5 import QtGui
from PyQt5 import QtWidgets
from PyQt5.QtCore import QObject, Qt, QSize, QTimer, pyqtSlot, QMutex
from PyQt5.QtGui import QFont, QPixmap

from PyQt5.QtWidgets import QTreeWidget, QTableWidget, QWidget, QVBoxLayout, QTableWidgetItem, QLabel, QGridLayout, \
    QPushButton, QLineEdit, QComboBox, QRadioButton, QGroupBox, QHBoxLayout, QStyle
from subprocess import Popen, PIPE

from media_engine.media_engine import MediaEngine, Playing_HDMI_in_worker
from media_configs.video_params import VideoParams
from media_engine.media_engine_def import PlayStatus
from ext_dev.tc358743 import TC358743
from global_def import *

from qt_ui_style.button_qss import *
from astral_hashmap import *
from qt_ui_style.ui_frame_page_def import *
import numpy as np
import signal
import os
import platform


def video_params_confirm_btn_clicked():
    log.debug("")


def hdmi_in_crop_disable():
    log.debug("")


def hdmi_in_crop_enable():
    log.debug("")


class HDMIInPage(QWidget):

    def __init__(self, _main_window, _frame: QWidget, _name, media_engine: MediaEngine, **kwargs):
        super(HDMIInPage, self).__init__(**kwargs)
        self.video_params_confirm_btn = None
        self.client_night_mode_brightness_edit = None
        self.client_night_mode_brightness_label = None
        self.client_sleep_mode_brightness_edit = None
        self.client_sleep_mode_brightness_label = None
        self.client_day_mode_brightness_edit = None
        self.client_day_mode_brightness_label = None
        self.client_gamma_edit = None
        self.radiobutton_sleep_mode_disable = None
        self.radiobutton_sleep_mode_enable = None
        self.combobox_target_city = None
        self.groupbox_sleep_mode_vboxlayout = None
        self.groupbox_sleep_mode = None
        self.radiobutton_client_br_method_test = None
        self.client_gamma_label = None
        self.radiobutton_client_br_method_als = None
        self.radiobutton_client_br_method_time = None
        self.radiobutton_client_br_method_fix = None
        self.groupbox_led_role_hboxlayout = None
        self.client_contrast_edit = None
        self.client_br_divisor_edit = None
        self.client_contrast_label = None
        self.client_br_divisor_label = None
        self.client_brightness_edit = None
        self.client_brightness_label = None
        self.blugain_label = None
        self.greengain_edit = None
        self.greengain_label = None
        self.redgain_edit = None
        self.redgain_label = None
        self.contrast_edit = None
        self.brightness_edit = None
        self.bluegain_edit = None
        self.groupbox_client_brightness_method = None
        self.brightness_label = None
        self.contrast_label = None
        self.setting_widget_layout = None
        self.setting_widget = None
        self.hdmi_in_crop_dummy_label = None
        self.hdmi_in_crop_enable_btn = None
        self.hdmi_in_crop_h_lineedit = None
        self.hdmi_in_crop_h_label = None
        self.hdmi_in_crop_w_lineedit = None
        self.hdmi_in_crop_w_label = None
        self.hdmi_in_crop_y_lineedit = None
        self.hdmi_in_crop_disable_btn = None
        self.hdmi_in_crop_y_label = None
        self.hdmi_in_crop_x_lineedit = None
        self.hdmi_in_crop_x_label = None
        self.hdmi_in_crop_status_h_res_label = None
        self.hdmi_in_crop_status_h_label = None
        self.crop_setting_widget_layout = None
        self.crop_setting_widget = None
        self.hdmi_in_crop_status_w_res_label = None
        self.hdmi_in_crop_status_w_label = None
        self.hdmi_in_crop_status_y_res_label = None
        self.hdmi_in_crop_status_y_label = None
        self.hdmi_in_crop_status_x_res_label = None
        self.hdmi_in_crop_status_x_label = None
        self.hdmi_in_crop_status_label = None
        self.hdmi_in_info_fps_res_label = None
        self.info_widget_layout = None
        self.info_widget = None
        self.hdmi_in_info_fps_label = None
        self.hdmi_in_info_height_res_label = None
        self.hdmi_in_info_height_label = None
        self.hdmi_in_info_width_res_label = None
        self.hdmi_in_info_width_label = None
        self.ffmpeg_pid_label = None
        self.hdmi_in_play_status_label = None
        self.preview_label = None
        self.preview_widget_layout = None
        self.preview_widget = None
        self.stop_action_btn = None
        self.play_action_btn = None
        self.hdmi_in_layout = None
        self.hdmi_in_widget = None
        self.main_windows = _main_window
        self.frame = _frame
        self.media_engine = media_engine
        self.video_device = TC358743.get_video_device(self)
        self.widget = QWidget(self.frame)
        self.name = _name
        self.prev_hdmi_info = None
        self.label_name = None
        self.layout = None
        self.play_hdmi_in_status = False
        self.measurement_tc358743 = None
        self.preview_status = False
        self.preview_mutex = QMutex()

        log.debug("start hdmi-in page")

        self.init_ui()
        self.media_engine.install_hdmi_play_status_changed_slot(self.media_play_status_changed)

        self.measurement_tc358743 = True
        self.check_tc358743_interval = 1000
        self.check_tc358743_timer = QTimer(self)
        self.check_tc358743_timer.timeout.connect(self.check_tc358743_timer_event)
        ensure_edid_validity(self)

        try:
            self.check_tc358743_timer.start(self.check_tc358743_interval)
        except Exception as e:
            log.debug(e)

        self.tc358743 = TC358743()
        self.tc358743.signal_refresh_tc358743_param.connect(self.refresh_tc358743_param)
        self.tc358743.get_tc358743_dv_timing()

    def init_ui(self):
        self.hdmi_in_widget = QWidget(self.frame)
        self.hdmi_in_layout = QVBoxLayout()
        self.hdmi_in_widget.setLayout(self.hdmi_in_layout)

        # self.main_windows.right_layout.addWidget(self.hdmi_in_widget)
        log.debug("self.hdmi_in_widget.height() = %d", self.hdmi_in_widget.height())
        self.preview_widget = QWidget(self.hdmi_in_widget)
        self.hdmi_in_layout.addWidget(self.preview_widget)

        self.preview_widget_layout = QGridLayout()
        self.preview_widget.setLayout(self.preview_widget_layout)

        self.preview_label = QLabel(self.preview_widget)
        self.preview_label.setText("HDMI-in Preview")
        self.preview_label.setFont(QFont(QFont_Style_Default, QFont_Style_Size_M))
        self.preview_label.setFixedHeight(160)
        self.preview_label.setScaledContents(True)
        self.frame.layout().addWidget(self.hdmi_in_widget)

        self.play_action_btn = QPushButton(self.preview_widget)
        self.play_action_btn.setText("Start Play")
        self.play_action_btn.setFont(QFont(QFont_Style_Default, QFont_Style_Size_M))
        self.play_action_btn.clicked.connect(self.pause_btn_clicked)
        self.play_action_btn.setStyleSheet(QPushButton_Style)

        self.stop_action_btn = QPushButton(self.preview_widget)
        self.stop_action_btn.setText("Stop Play")
        self.stop_action_btn.setFont(QFont(QFont_Style_Default, QFont_Style_Size_M))
        self.stop_action_btn.clicked.connect(self.stop_btn_clicked)
        self.stop_action_btn.setStyleSheet(QPushButton_Style)

        self.hdmi_in_play_status_label = QLabel(self.preview_widget)
        self.hdmi_in_play_status_label.setFont(QFont(QFont_Style_Default, QFont_Style_Size_M))
        self.hdmi_in_play_status_label.setText("Non-Streaming")

        self.ffmpeg_pid_label = QLabel(self.preview_widget)
        self.ffmpeg_pid_label.setFont(QFont(QFont_Style_Default, QFont_Style_Size_M))
        self.ffmpeg_pid_label.setText("ff pid:None")

        self.preview_widget_layout.addWidget(self.preview_label, 0, 0)
        self.preview_widget_layout.addWidget(self.play_action_btn, 2, 0, 1, 2)
        self.preview_widget_layout.addWidget(self.stop_action_btn, 2, 2, 1, 2)

        self.preview_widget_layout.addWidget(self.hdmi_in_play_status_label, 4, 0)
        self.preview_widget_layout.addWidget(self.ffmpeg_pid_label, 4, 2)

        # information of hdmi in
        self.info_widget = QWidget(self.hdmi_in_widget)
        self.info_widget_layout = QGridLayout()
        self.info_widget.setLayout(self.info_widget_layout)

        # width/height/fps
        self.hdmi_in_info_width_label = QLabel(self.info_widget)
        self.hdmi_in_info_width_label.setText("HDMI_In Width:")
        self.hdmi_in_info_width_label.setFont(QFont(QFont_Style_Default, QFont_Style_Size_M))
        self.hdmi_in_info_width_res_label = QLabel(self.info_widget)
        self.hdmi_in_info_width_res_label.setText("NA")
        self.hdmi_in_info_width_res_label.setFont(QFont(QFont_Style_Default, QFont_Style_Size_M))

        self.hdmi_in_info_height_label = QLabel(self.info_widget)
        self.hdmi_in_info_height_label.setText("HDMI_In Height:")
        self.hdmi_in_info_height_label.setFont(QFont(QFont_Style_Default, QFont_Style_Size_M))
        self.hdmi_in_info_height_res_label = QLabel(self.info_widget)
        self.hdmi_in_info_height_res_label.setText("NA")
        self.hdmi_in_info_height_res_label.setFont(QFont(QFont_Style_Default, QFont_Style_Size_M))

        self.hdmi_in_info_fps_label = QLabel(self.info_widget)
        self.hdmi_in_info_fps_label.setText("HDMI_In FPS:")
        self.hdmi_in_info_fps_label.setFont(QFont(QFont_Style_Default, QFont_Style_Size_M))
        self.hdmi_in_info_fps_res_label = QLabel(self.info_widget)
        self.hdmi_in_info_fps_res_label.setText("NA")
        self.hdmi_in_info_fps_res_label.setFont(QFont(QFont_Style_Default, QFont_Style_Size_M))

        self.hdmi_in_crop_status_label = QLabel(self.info_widget)
        self.hdmi_in_crop_status_label.setText("Crop Disable")
        self.hdmi_in_crop_status_label.setFont(QFont(QFont_Style_Default, QFont_Style_Size_M))

        self.hdmi_in_crop_status_x_label = QLabel(self.info_widget)
        self.hdmi_in_crop_status_x_label.setText("Crop Start X:")
        self.hdmi_in_crop_status_x_label.setFont(QFont(QFont_Style_Default, QFont_Style_Size_M))
        self.hdmi_in_crop_status_x_res_label = QLabel(self.info_widget)
        self.hdmi_in_crop_status_x_res_label.setText("NA")
        self.hdmi_in_crop_status_x_res_label.setFont(QFont(QFont_Style_Default, QFont_Style_Size_M))

        self.hdmi_in_crop_status_y_label = QLabel(self.info_widget)
        self.hdmi_in_crop_status_y_label.setText("Crop Start Y:")
        self.hdmi_in_crop_status_y_label.setFont(QFont(QFont_Style_Default, QFont_Style_Size_M))
        self.hdmi_in_crop_status_y_res_label = QLabel(self.info_widget)
        self.hdmi_in_crop_status_y_res_label.setText("NA")
        self.hdmi_in_crop_status_y_res_label.setFont(QFont(QFont_Style_Default, QFont_Style_Size_M))

        self.hdmi_in_crop_status_w_label = QLabel(self.info_widget)
        self.hdmi_in_crop_status_w_label.setText("Crop Width:")
        self.hdmi_in_crop_status_w_label.setFont(QFont(QFont_Style_Default, QFont_Style_Size_M))
        self.hdmi_in_crop_status_w_res_label = QLabel(self.info_widget)
        self.hdmi_in_crop_status_w_res_label.setText("NA")
        self.hdmi_in_crop_status_w_res_label.setFont(QFont(QFont_Style_Default, QFont_Style_Size_M))

        self.hdmi_in_crop_status_h_label = QLabel(self.info_widget)
        self.hdmi_in_crop_status_h_label.setText("Crop Height:")
        self.hdmi_in_crop_status_h_label.setFont(QFont(QFont_Style_Default, QFont_Style_Size_M))
        self.hdmi_in_crop_status_h_res_label = QLabel(self.info_widget)
        self.hdmi_in_crop_status_h_res_label.setText("NA")
        self.hdmi_in_crop_status_h_res_label.setFont(QFont(QFont_Style_Default, QFont_Style_Size_M))

        self.info_widget_layout.addWidget(self.hdmi_in_info_width_label, 0, 0)
        self.info_widget_layout.addWidget(self.hdmi_in_info_width_res_label, 0, 1)
        self.info_widget_layout.addWidget(self.hdmi_in_info_height_label, 0, 2)
        self.info_widget_layout.addWidget(self.hdmi_in_info_height_res_label, 0, 3)
        self.info_widget_layout.addWidget(self.hdmi_in_info_fps_label, 0, 4)
        self.info_widget_layout.addWidget(self.hdmi_in_info_fps_res_label, 0, 5)

        self.info_widget_layout.addWidget(self.hdmi_in_crop_status_label, 1, 0)
        self.info_widget_layout.addWidget(self.hdmi_in_crop_status_x_label, 1, 2)
        self.info_widget_layout.addWidget(self.hdmi_in_crop_status_x_res_label, 1, 3)
        self.info_widget_layout.addWidget(self.hdmi_in_crop_status_y_label, 1, 4)
        self.info_widget_layout.addWidget(self.hdmi_in_crop_status_y_res_label, 1, 5)

        self.info_widget_layout.addWidget(self.hdmi_in_crop_status_w_label, 2, 2)
        self.info_widget_layout.addWidget(self.hdmi_in_crop_status_w_res_label, 2, 3)
        self.info_widget_layout.addWidget(self.hdmi_in_crop_status_h_label, 2, 4)
        self.info_widget_layout.addWidget(self.hdmi_in_crop_status_h_res_label, 2, 5)

        # crop setting of hdmi in
        self.crop_setting_widget = QWidget(self.hdmi_in_widget)
        self.crop_setting_widget_layout = QGridLayout()
        self.crop_setting_widget.setLayout(self.crop_setting_widget_layout)

        self.hdmi_in_crop_x_label = QLabel(self.crop_setting_widget)
        self.hdmi_in_crop_x_label.setText("Crop Start X:")
        self.hdmi_in_crop_x_label.setFont(QFont(QFont_Style_Default, QFont_Style_Size_M))
        self.hdmi_in_crop_x_lineedit = QLineEdit(self.crop_setting_widget)
        self.hdmi_in_crop_x_lineedit.setFixedWidth(100)
        self.hdmi_in_crop_x_lineedit.setText("NA")
        self.hdmi_in_crop_x_lineedit.setFont(QFont(QFont_Style_Default, QFont_Style_Size_M))

        self.hdmi_in_crop_y_label = QLabel(self.crop_setting_widget)
        self.hdmi_in_crop_y_label.setText("Crop Start Y:")
        self.hdmi_in_crop_y_label.setFont(QFont(QFont_Style_Default, QFont_Style_Size_M))
        self.hdmi_in_crop_y_lineedit = QLineEdit(self.crop_setting_widget)
        self.hdmi_in_crop_y_lineedit.setFixedWidth(100)
        self.hdmi_in_crop_y_lineedit.setText("NA")
        self.hdmi_in_crop_y_lineedit.setFont(QFont(QFont_Style_Default, QFont_Style_Size_M))

        self.hdmi_in_crop_w_label = QLabel(self.crop_setting_widget)
        self.hdmi_in_crop_w_label.setText("Crop Width:")
        self.hdmi_in_crop_w_label.setFont(QFont(QFont_Style_Default, QFont_Style_Size_M))
        self.hdmi_in_crop_w_lineedit = QLineEdit(self.crop_setting_widget)
        self.hdmi_in_crop_w_lineedit.setFixedWidth(100)
        self.hdmi_in_crop_w_lineedit.setText("NA")
        self.hdmi_in_crop_w_lineedit.setFont(QFont(QFont_Style_Default, QFont_Style_Size_M))

        self.hdmi_in_crop_h_label = QLabel(self.crop_setting_widget)
        self.hdmi_in_crop_h_label.setText("Crop Height:")
        self.hdmi_in_crop_h_label.setFont(QFont(QFont_Style_Default, QFont_Style_Size_M))
        self.hdmi_in_crop_h_lineedit = QLineEdit(self.crop_setting_widget)
        self.hdmi_in_crop_h_lineedit.setFixedWidth(100)
        self.hdmi_in_crop_h_lineedit.setText("NA")
        self.hdmi_in_crop_h_lineedit.setFont(QFont(QFont_Style_Default, QFont_Style_Size_M))

        self.hdmi_in_crop_disable_btn = QPushButton(self.crop_setting_widget)
        self.hdmi_in_crop_disable_btn.setFixedWidth(100)
        self.hdmi_in_crop_disable_btn.setText("Disable")
        self.hdmi_in_crop_disable_btn.setFont(QFont(QFont_Style_Default, QFont_Style_Size_M))
        self.hdmi_in_crop_disable_btn.clicked.connect(hdmi_in_crop_disable)

        self.hdmi_in_crop_enable_btn = QPushButton(self.crop_setting_widget)
        self.hdmi_in_crop_enable_btn.setFixedWidth(100)
        self.hdmi_in_crop_enable_btn.setText("Enable")
        self.hdmi_in_crop_enable_btn.setFont(QFont(QFont_Style_Default, QFont_Style_Size_M))
        self.hdmi_in_crop_enable_btn.clicked.connect(hdmi_in_crop_enable)

        self.hdmi_in_crop_dummy_label = QLabel(self.crop_setting_widget)

        self.crop_setting_widget_layout.addWidget(self.hdmi_in_crop_x_label, 0, 0)
        self.crop_setting_widget_layout.addWidget(self.hdmi_in_crop_x_lineedit, 0, 1)
        self.crop_setting_widget_layout.addWidget(self.hdmi_in_crop_y_label, 0, 2)
        self.crop_setting_widget_layout.addWidget(self.hdmi_in_crop_y_lineedit, 0, 3)
        self.crop_setting_widget_layout.addWidget(self.hdmi_in_crop_dummy_label, 0, 4)
        self.crop_setting_widget_layout.addWidget(self.hdmi_in_crop_disable_btn, 0, 5)

        self.crop_setting_widget_layout.addWidget(self.hdmi_in_crop_w_label, 1, 0)
        self.crop_setting_widget_layout.addWidget(self.hdmi_in_crop_w_lineedit, 1, 1)
        self.crop_setting_widget_layout.addWidget(self.hdmi_in_crop_h_label, 1, 2)
        self.crop_setting_widget_layout.addWidget(self.hdmi_in_crop_h_lineedit, 1, 3)

        self.crop_setting_widget_layout.addWidget(self.hdmi_in_crop_enable_btn, 1, 5)

        # color setting of hdmi in
        self.setting_widget = QWidget(self.hdmi_in_widget)
        self.setting_widget_layout = QGridLayout()
        self.setting_widget.setLayout(self.setting_widget_layout)

        # brightness
        self.brightness_label = QLabel(self.setting_widget)
        self.brightness_label.setText("Brightness:")
        self.brightness_label.setFont(QFont(QFont_Style_Default, QFont_Style_Size_M))
        self.brightness_edit = QLineEdit(self.setting_widget)
        self.brightness_edit.setFixedWidth(100)
        # self.brightness_edit.setText(str(self.media_engine.media_processor.video_params.video_brightness))
        self.brightness_edit.setFont(QFont(QFont_Style_Default, QFont_Style_Size_M))

        # contrast
        self.contrast_label = QLabel(self.setting_widget)
        self.contrast_label.setText("Contrast:")
        self.contrast_label.setFont(QFont(QFont_Style_Default, QFont_Style_Size_M))
        self.contrast_edit = QLineEdit(self.setting_widget)
        self.contrast_edit.setFixedWidth(100)
        # self.contrast_edit.setText(str(self.main_windows.media_engine.media_processor.video_params.video_contrast))
        self.contrast_edit.setFont(QFont(QFont_Style_Default, QFont_Style_Size_M))

        # red gain
        self.redgain_label = QLabel(self.setting_widget)
        self.redgain_label.setText("Red Gain:")
        self.redgain_label.setFont(QFont(QFont_Style_Default, QFont_Style_Size_M))
        self.redgain_edit = QLineEdit(self.setting_widget)
        self.redgain_edit.setFixedWidth(100)
        # self.redgain_edit.setText(str(self.main_windows.media_engine.media_processor.video_params.video_red_bias))
        self.redgain_edit.setFont(QFont(QFont_Style_Default, QFont_Style_Size_M))

        # green gain
        self.greengain_label = QLabel(self.setting_widget)
        self.greengain_label.setText("Green Gain:")
        self.greengain_label.setFont(QFont(QFont_Style_Default, QFont_Style_Size_M))
        self.greengain_edit = QLineEdit(self.setting_widget)
        self.greengain_edit.setFixedWidth(100)
        # self.greengain_edit.setText(str(self.main_windows.media_engine.media_processor.video_params.video_green_bias))
        self.greengain_edit.setFont(QFont(QFont_Style_Default, QFont_Style_Size_M))

        # blue gain
        self.blugain_label = QLabel(self.setting_widget)
        self.blugain_label.setText("Blue Gain:")
        self.blugain_label.setFont(QFont(QFont_Style_Default, QFont_Style_Size_M))
        self.bluegain_edit = QLineEdit(self.setting_widget)
        self.bluegain_edit.setFixedWidth(100)
        # self.bluegain_edit.setText(str(self.main_windows.media_engine.media_processor.video_params.video_blue_bias))
        self.bluegain_edit.setFont(QFont(QFont_Style_Default, QFont_Style_Size_M))

        # client brightness adjust
        self.client_brightness_label = QLabel(self.setting_widget)
        self.client_brightness_label.setText("Client Br:")
        self.client_brightness_label.setFont(QFont(QFont_Style_Default, QFont_Style_Size_M))
        self.client_brightness_edit = QLineEdit(self.setting_widget)
        self.client_brightness_edit.setFixedWidth(100)
        # self.client_brightness_edit.setText(
        #    str(self.main_windows.media_engine.media_processor.video_params.frame_brightness))
        self.client_brightness_edit.setFont(QFont(QFont_Style_Default, QFont_Style_Size_M))

        # client brightness adjust
        self.client_br_divisor_label = QLabel(self.setting_widget)
        self.client_br_divisor_label.setText("Client BrDivisor:")
        self.client_br_divisor_label.setFont(QFont(QFont_Style_Default, QFont_Style_Size_M))
        self.client_br_divisor_edit = QLineEdit(self.setting_widget)
        self.client_br_divisor_edit.setFixedWidth(100)
        # self.client_br_divisor_edit.setText(
        #    str(self.main_windows.media_engine.media_processor.video_params.frame_br_divisor))
        self.client_br_divisor_edit.setFont(QFont(QFont_Style_Default, QFont_Style_Size_M))

        # client contrast(black level) adjust
        self.client_contrast_label = QLabel(self.setting_widget)
        self.client_contrast_label.setText("Client Black-Lv:")
        self.client_contrast_label.setFont(QFont(QFont_Style_Default, QFont_Style_Size_M))
        self.client_contrast_edit = QLineEdit(self.setting_widget)
        self.client_contrast_edit.setFixedWidth(100)
        # self.client_contrast_edit.setText(
        #    str(self.main_windows.media_engine.media_processor.video_params.frame_contrast))
        self.client_contrast_edit.setFont(QFont(QFont_Style_Default, QFont_Style_Size_M))

        # client brightness mode adjust
        self.groupbox_client_brightness_method = QGroupBox("Client Brightness Method")
        self.groupbox_led_role_hboxlayout = QHBoxLayout()
        self.groupbox_client_brightness_method.setLayout(self.groupbox_led_role_hboxlayout)
        self.radiobutton_client_br_method_fix = QRadioButton("Fix Mode")
        # self.radiobutton_client_br_method_fix.clicked.connect(
        #    self.main_windows.media_engine.media_processor.video_params.set_frame_brightness_mode_fix)
        self.radiobutton_client_br_method_fix.setFont(QFont(QFont_Style_Default, QFont_Style_Size_M))
        self.radiobutton_client_br_method_time = QRadioButton("Time Mode")
        # self.radiobutton_client_br_method_time.clicked.connect(
        #    self.main_windows.media_engine.media_processor.video_params.set_frame_brightness_mode_time)
        self.radiobutton_client_br_method_time.setFont(QFont(QFont_Style_Default, QFont_Style_Size_M))
        self.radiobutton_client_br_method_als = QRadioButton("ALS Mode")
        # self.radiobutton_client_br_method_als.clicked.connect(
        #    self.main_windows.media_engine.media_processor.video_params.set_frame_brightness_mode_als)
        self.radiobutton_client_br_method_als.setFont(QFont(QFont_Style_Default, QFont_Style_Size_M))
        self.radiobutton_client_br_method_test = QRadioButton("TEST Mode")
        # self.radiobutton_client_br_method_test.clicked.connect(
        #    self.main_windows.media_engine.media_processor.video_params.set_frame_brightness_mode_test)
        self.radiobutton_client_br_method_test.setFont(QFont(QFont_Style_Default, QFont_Style_Size_M))
        # log.debug("frame_brightness_algorithm : %d",
        #          self.main_windows.media_engine.media_processor.video_params.frame_brightness_algorithm)
        # if self.main_windows.media_engine.media_processor.video_params.frame_brightness_algorithm == frame_brightness_adjust.fix_mode:
        #    self.radiobutton_client_br_method_fix.setChecked(True)

        # elif self.main_windows.media_engine.media_processor.video_params.frame_brightness_algorithm == frame_brightness_adjust.auto_time_mode:
        #    self.radiobutton_client_br_method_time.setChecked(True)
        # elif self.main_windows.media_engine.media_processor.video_params.frame_brightness_algorithm == frame_brightness_adjust.auto_als_mode:
        #    self.radiobutton_client_br_method_als.setChecked(True)
        # elif self.main_windows.media_engine.media_processor.video_params.frame_brightness_algorithm == frame_brightness_adjust.test_mode:
        #    self.radiobutton_client_br_method_test.setChecked(True)

        self.groupbox_led_role_hboxlayout.addWidget(self.radiobutton_client_br_method_fix)
        self.groupbox_led_role_hboxlayout.addWidget(self.radiobutton_client_br_method_time)
        self.groupbox_led_role_hboxlayout.addWidget(self.radiobutton_client_br_method_als)
        self.groupbox_led_role_hboxlayout.addWidget(self.radiobutton_client_br_method_test)

        # sleep mode
        self.groupbox_sleep_mode = QGroupBox("Sleep Mode")
        self.groupbox_sleep_mode_vboxlayout = QHBoxLayout()
        self.groupbox_sleep_mode.setLayout(self.groupbox_sleep_mode_vboxlayout)
        self.radiobutton_sleep_mode_enable = QRadioButton("Enable")
        # self.radiobutton_sleep_mode_enable.clicked.connect(
        #    self.main_windows.media_engine.media_processor.video_params.set_sleep_mode_enable
        # )
        self.radiobutton_sleep_mode_disable = QRadioButton("Disable")
        # self.radiobutton_sleep_mode_disable.clicked.connect(
        #    self.main_windows.media_engine.media_processor.video_params.set_sleep_mode_disable
        # )
        self.radiobutton_sleep_mode_enable.setFont(QFont(QFont_Style_Default, QFont_Style_Size_M))
        self.radiobutton_sleep_mode_disable.setFont(QFont(QFont_Style_Default, QFont_Style_Size_M))

        # if self.main_windows.media_engine.media_processor.video_params.sleep_mode_enable == 1:
        #    self.radiobutton_sleep_mode_enable.setChecked(True)
        # if self.main_windows.media_engine.media_processor.video_params.sleep_mode_enable == 0:
        #    self.radiobutton_sleep_mode_disable.setChecked(True)

        self.groupbox_sleep_mode_vboxlayout.addWidget(self.radiobutton_sleep_mode_enable)
        self.groupbox_sleep_mode_vboxlayout.addWidget(self.radiobutton_sleep_mode_disable)

        # target city
        self.combobox_target_city = QComboBox(self.frame)
        for city in City_Map:
            self.combobox_target_city.addItem(city.get("City"))
        self.combobox_target_city.setFont(QFont(QFont_Style_Default, QFont_Style_Size_M))
        # self.combobox_target_city.setCurrentIndex(
        #    self.main_windows.media_engine.media_processor.video_params.target_city_index
        # )

        # client gamma adjust
        self.client_gamma_label = QLabel(self.setting_widget)
        self.client_gamma_label.setText("Client Gamma:")
        self.client_gamma_label.setFont(QFont(QFont_Style_Default, QFont_Style_Size_M))
        self.client_gamma_edit = QLineEdit(self.setting_widget)
        self.client_gamma_edit.setFixedWidth(100)
        # self.client_gamma_edit.setText(
        #    str(self.main_windows.media_engine.media_processor.video_params.frame_gamma))
        self.client_gamma_edit.setFont(QFont(QFont_Style_Default, QFont_Style_Size_M))

        self.client_day_mode_brightness_label = QLabel(self.frame)
        self.client_day_mode_brightness_label.setText("Day Mode Br:")
        self.client_day_mode_brightness_label.setFont(QFont(QFont_Style_Default, QFont_Style_Size_M))
        self.client_day_mode_brightness_edit = QLineEdit(self.frame)
        self.client_day_mode_brightness_edit.setFixedWidth(100)
        self.client_day_mode_brightness_edit.setFont(QFont(QFont_Style_Default, QFont_Style_Size_M))
        # self.client_day_mode_brightness_edit.setText(
        #    str(self.main_windows.media_engine.media_processor.video_params.day_mode_frame_brightness))

        self.client_night_mode_brightness_label = QLabel(self.frame)
        self.client_night_mode_brightness_label.setText("Night Mode Br:")
        self.client_night_mode_brightness_label.setFont(QFont(QFont_Style_Default, QFont_Style_Size_M))
        self.client_night_mode_brightness_edit = QLineEdit(self.frame)
        self.client_night_mode_brightness_edit.setFixedWidth(100)
        self.client_night_mode_brightness_edit.setFont(QFont(QFont_Style_Default, QFont_Style_Size_M))
        # self.client_night_mode_brightness_edit.setText(
        #    str(self.main_windows.media_engine.media_processor.video_params.night_mode_frame_brightness))

        self.client_sleep_mode_brightness_label = QLabel(self.frame)
        self.client_sleep_mode_brightness_label.setText("Sleep Mode Br:")
        self.client_sleep_mode_brightness_label.setFont(QFont(QFont_Style_Default, QFont_Style_Size_M))
        self.client_sleep_mode_brightness_edit = QLineEdit(self.frame)
        self.client_sleep_mode_brightness_edit.setFixedWidth(100)
        self.client_sleep_mode_brightness_edit.setFont(QFont(QFont_Style_Default, QFont_Style_Size_M))
        # self.client_sleep_mode_brightness_edit.setText(
        #    str(self.main_windows.media_engine.media_processor.video_params.sleep_mode_frame_brightness))

        self.video_params_confirm_btn = QPushButton(self.setting_widget)
        self.video_params_confirm_btn.setText("Set")
        self.video_params_confirm_btn.setFixedWidth(100)
        self.video_params_confirm_btn.clicked.connect(video_params_confirm_btn_clicked)
        self.video_params_confirm_btn.setFont(QFont(QFont_Style_Default, QFont_Style_Size_M))

        '''# self.setting_widget_layout.addWidget(self.test_btn, 0, 0)'''
        self.setting_widget_layout.addWidget(self.redgain_label, 0, 0)
        self.setting_widget_layout.addWidget(self.redgain_edit, 0, 1)
        self.setting_widget_layout.addWidget(self.greengain_label, 0, 2)
        self.setting_widget_layout.addWidget(self.greengain_edit, 0, 3)
        self.setting_widget_layout.addWidget(self.blugain_label, 0, 4)
        self.setting_widget_layout.addWidget(self.bluegain_edit, 0, 5)

        self.setting_widget_layout.addWidget(self.brightness_label, 1, 0)
        self.setting_widget_layout.addWidget(self.brightness_edit, 1, 1)
        self.setting_widget_layout.addWidget(self.contrast_label, 1, 2)
        self.setting_widget_layout.addWidget(self.contrast_edit, 1, 3)

        self.setting_widget_layout.addWidget(self.client_brightness_label, 4, 4)
        self.setting_widget_layout.addWidget(self.client_brightness_edit, 4, 5)
        self.setting_widget_layout.addWidget(self.client_br_divisor_label, 2, 2)
        self.setting_widget_layout.addWidget(self.client_br_divisor_edit, 2, 3)
        self.setting_widget_layout.addWidget(self.client_contrast_label, 2, 0)
        self.setting_widget_layout.addWidget(self.client_contrast_edit, 2, 1)
        self.setting_widget_layout.addWidget(self.client_gamma_label, 2, 4)
        self.setting_widget_layout.addWidget(self.client_gamma_edit, 2, 5)

        self.setting_widget_layout.addWidget(self.groupbox_client_brightness_method, 4, 0, 2, 4)
        self.setting_widget_layout.addWidget(self.groupbox_sleep_mode, 7, 0, 2, 2)
        self.setting_widget_layout.addWidget(self.combobox_target_city, 7, 2, 0, 2)

        self.setting_widget_layout.addWidget(self.client_day_mode_brightness_label, 9, 0)
        self.setting_widget_layout.addWidget(self.client_day_mode_brightness_edit, 9, 1)
        self.setting_widget_layout.addWidget(self.client_night_mode_brightness_label, 9, 2)
        self.setting_widget_layout.addWidget(self.client_night_mode_brightness_edit, 9, 3)
        self.setting_widget_layout.addWidget(self.client_sleep_mode_brightness_label, 9, 4)
        self.setting_widget_layout.addWidget(self.client_sleep_mode_brightness_edit, 9, 5)
        self.setting_widget_layout.addWidget(self.video_params_confirm_btn, 5, 5)

        self.hdmi_in_layout.addWidget(self.preview_widget)
        self.hdmi_in_layout.addWidget(self.info_widget)
        self.hdmi_in_layout.addWidget(self.crop_setting_widget)
        self.hdmi_in_layout.addWidget(self.setting_widget)

    def media_play_status_changed(self, status: int, src: str):
        if status == PlayStatus.Playing:
            self.play_action_btn.setText("Pause")
        elif status == PlayStatus.Pausing:
            self.play_action_btn.setText("Resume")
        elif (status == PlayStatus.Stop or
              status == PlayStatus.Initial):
            self.play_action_btn.setText("Start Play")
        if self.media_engine.play_hdmi_in_worker is not None:
            pid = self.media_engine.play_hdmi_in_worker.get_ff_pid()
            if pid is not None:
                self.ffmpeg_pid_label.setText("ff pid:" + str(pid))

    def start_streaming(self):
        if self.play_hdmi_in_status is False:
            self.media_engine.resume_playing()
            self.media_engine.stop_play()
            if self.media_engine.play_hdmi_in_worker is None:
                log.debug("Start streaming")
                self.media_engine.hdmi_in_play(self.video_device)
            self.play_hdmi_in_status = True
            self.measurement_tc358743 = True

    def stop_streaming(self, MeasurementEnable: False):
        self.measurement_tc358743 = MeasurementEnable
        self.media_engine.stop_play()
        self.play_hdmi_in_status = False
        self.refresh_tc358743_param(False)
        self.hdmi_in_play_status_label.setText("Non-Streaming")

    def stop_btn_clicked(self):
        self.stop_streaming(False)

    def pause_btn_clicked(self):
        if PlayStatus.Playing == self.media_engine.playing_status:
            self.media_engine.pause_playing()
            # self.hdmi_in_play_status_label.setText("Streaming-Pause")
        elif PlayStatus.Pausing == self.media_engine.playing_status:
            self.media_engine.resume_playing()
            # self.hdmi_in_play_status_label.setText("Streaming-Resume")
        elif (PlayStatus.Stop == self.media_engine.playing_status or
              PlayStatus.Initial == self.media_engine.playing_status):
            self.start_streaming()
            # self.hdmi_in_play_status_label.setText("Streaming")

    def check_tc358743_timer_event(self):
        # log.debug("enter check_tc358743_timer")
        self.preview_mutex.lock()
        if self.main_windows.right_frame_page_index != Page.HDMI_IN.value:
            # log.debug("Not in hdmi-in page")
            self.prev_hdmi_info = None
            self.preview_status = False
            self.measurement_tc358743 = True
            self.preview_mutex.unlock()
            return

        self.preview_mutex.unlock()

        current_hdmi_info = self.tc358743.get_tc358743_hdmi_info()

        (current_hdmi_connected, current_hdmi_hdmi_width,
         current_hdmi_height, current_hdmi_hdmi_fps) = current_hdmi_info

        try:

            if (self.prev_hdmi_info is None or
                    current_hdmi_info != self.prev_hdmi_info):

                if (current_hdmi_connected is True and
                        self.measurement_tc358743 is True):

                    if self.tc358743.set_tc358743_dv_bt_timing() is True:
                        self.start_hdmi_in_preview()
                        self.preview_status = True
                        self.preview_label.setText("HDMI-in connected")
                    else:
                        hdmi_info_list = list(current_hdmi_info)
                        hdmi_info_list[0] = False
                        current_hdmi_info = tuple(hdmi_info_list)
                        subprocess.Popen("pkill -f ffmpeg", shell=True)

                else:
                    if self.tc358743.hdmi_connected is True:
                        if current_hdmi_connected is False:
                            self.stop_hdmi_in_preview()
                            self.stop_streaming(True)
                            self.measurement_tc358743 = True
                            self.media_engine.stop_play()
                            subprocess.Popen("pkill -f ffmpeg", shell=True)
                            self.tc358743.reinit_tc358743_dv_timing()
                            self.preview_label.setText("HDMI-in Signal Lost")

            self.prev_hdmi_info = current_hdmi_info
            (self.tc358743.hdmi_connected, self.tc358743.hdmi_width,
             self.tc358743.hdmi_height, self.tc358743.hdmi_fps) = current_hdmi_info

        except Exception as e:
            log.debug(e)
            self.check_tc358743_timer.stop()
            self.check_tc358743_timer.start(self.check_tc358743_interval)
            self.preview_status = False
            self.prev_hdmi_info = None
            self.measurement_tc358743 = True
            self.preview_mutex.unlock()
            log.debug("restart check_tc358743_timer")

    def refresh_tc358743_param(self, connected=False, width="NA", height="NA", fps="NA"):

        # log.debug("connected = %d", connected)
        # video_params = self.media_configs.video_params
        if platform.machine() in ('arm', 'arm64', 'aarch64'):
            pass
        else:
            return

        self.hdmi_in_info_width_res_label.setText(str(width))
        self.hdmi_in_info_height_res_label.setText(str(height))
        self.hdmi_in_info_fps_res_label.setText(str(fps))

    def start_hdmi_in_preview(self):

        self.preview_mutex.lock()

        log.debug("start_hdmi_in_preview preview_status %s", self.preview_status)

        if self.preview_status is True:
            self.preview_mutex.unlock()
            return

        self.media_engine.stop_play()
        # find any ffmpeg process
        p = subprocess.run(["pgrep", "ffmpeg"],
                           capture_output=True, text=True)
        if p.stdout:
            subprocess.run(["pkill", "-f", "ffmpeg"])

        # find any show_ffmpeg_shared_memory process
        p = subprocess.run(["pgrep", "show_ffmpeg_shared_memory"],
                           capture_output=True, text=True)
        if p.stdout:
            subprocess.run(["pkill", "-f", "show_ffmpeg_shared_memory"])

        # find any ffprobe process
        p = subprocess.run(["pgrep", "ffprobe"],
                           capture_output=True, text=True)
        if p.stdout:
            subprocess.run(["pkill", "-f", "ffprobe"])

        if self.tc358743.set_tc358743_dv_bt_timing() is True:
            self.tc358743.reinit_tc358743_dv_timing()
            self.media_engine.hdmi_in_play(self.video_device)
        self.preview_mutex.unlock()

    def stop_hdmi_in_preview(self):
        if self.preview_status:
            self.preview_mutex.lock()
            self.preview_status = False
            self.preview_mutex.unlock()
        self.ffmpeg_pid_label.setText("ff pid:None")


def ensure_edid_validity(self):
    p = os.popen("v4l2-ctl --get-edid")
    preproc = p.read()
    if "failed" in preproc:
        p = os.popen("write_tc358743_edid.sh")
        time.sleep(5)
        p.close()
    p.close()
