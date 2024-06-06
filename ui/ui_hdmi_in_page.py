import time
import subprocess
from PyQt5 import QtGui
from PyQt5 import QtWidgets
from PyQt5.QtCore import QObject, Qt, QSize, QTimer, pyqtSlot, QMutex
from PyQt5.QtGui import QFont, QPixmap, QIcon

from PyQt5.QtWidgets import QTreeWidget, QTableWidget, QWidget, QVBoxLayout, QTableWidgetItem, QLabel, QGridLayout, \
    QPushButton, QLineEdit, QComboBox, QRadioButton, QGroupBox, QHBoxLayout, QStyle, QFrame
from subprocess import Popen, PIPE

import media_configs.video_params
from astral_hashmap import City_Map
from media_engine.media_engine import MediaEngine, Playing_HDMI_in_worker
from media_configs.video_params import VideoParams
from media_engine.media_engine_def import PlayStatus
from ext_dev.tc358743 import TC358743
from global_def import *

from qt_ui_style.button_qss import *
from qt_ui_style.ui_frame_page_def import *
import numpy as np
import signal
import os
import platform


class HDMIInPage(QWidget):

    def __init__(self, _main_window, _frame: QWidget, _name, media_engine: MediaEngine, **kwargs):
        super(HDMIInPage, self).__init__(**kwargs)
        self.video_adj_br_ga_btn = None
        self.output_fps_lineedit = None
        self.output_fps_label = None
        self.output_frame_height_lineedit = None
        self.output_frame_height_label = None
        self.output_frame_width_lineedit = None
        self.output_frame_width_label = None
        self.icled_type_combobox = None
        self.icled_type_label = None
        self.led_b_gain_lineedit = None
        self.led_b_gain_label = None
        self.led_g_gain_lineedit = None
        self.led_g_gain_label = None
        self.led_r_gain_lineedit = None
        self.led_r_gain_label = None
        self.sleep_mode_brightness_lineedit = None
        self.sleep_mode_brightness_label = None
        self.night_mode_brightness_lineedit = None
        self.night_mode_brightness_label = None
        self.day_mode_brightness_lineedit = None
        self.day_mode_brightness_label = None
        self.target_city_combobox = None
        self.target_city_label = None
        self.sleep_mode_enable_combobox = None
        self.sleep_mode_enable_label = None
        self.video_params_setting_layout = None
        self.video_params_setting_widget = None
        self.brightness_algo_combobox = None
        self.brightness_algo_label = None
        self.video_gamma_lineedit = None
        self.video_brightness_lineedit = None
        self.video_gamma_label = None
        self.video_brightness_label = None
        self.hdmi_in_crop_h_lineedit = None
        self.hdmi_in_crop_w_lineedit = None
        self.hdmi_in_crop_y_lineedit = None
        self.hdmi_in_crop_x_lineedit = None
        self.crop_setting_widget_layout = None
        self.crop_setting_widget = None
        self.hdmi_ctrl_frame = None
        self.hdmi_info_group_box = None
        self.process_status_layout = None
        self.process_status_frame = None
        self.hdmi_in_info_fps_res_label = None
        self.hdmi_out_info_fps_res_label = None
        self.info_widget_layout = None
        self.info_widget = None
        self.hdmi_in_info_fps_label = None
        self.hdmi_in_info_height_res_label = None
        self.hdmi_in_info_height_label = None
        self.hdmi_in_info_width_res_label = None
        self.hdmi_in_info_width_label = None
        self.hdmi_out_info_fps_label = None
        self.hdmi_out_info_height_res_label = None
        self.hdmi_out_info_height_label = None
        self.hdmi_out_info_width_res_label = None
        self.hdmi_out_info_width_label = None
        self.pid_status_label = None
        self.hdmi_in_play_status_label = None
        self.preview_label = None
        self.preview_widget_layout = None
        self.preview_widget = None
        self.stop_action_btn = None
        self.play_action_btn = None
        self.sound_control_btn = None
        self.preview_control_btn = None
        self.adj_ctrl_param_btn = None
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
        self.measurement_tc358743 = None
        self.streamingStatus = False
        self.streamStateMutex = QMutex()

        log.debug("start hdmi-in page")

        self.init_ui()
        self.media_engine.install_hdmi_play_status_changed_slot(self.media_play_status_changed)

        self.measurement_tc358743 = True
        self.check_tc358743_interval = 1000
        self.check_tc358743_timer = QTimer(self)
        self.check_tc358743_timer.timeout.connect(self.check_tc358743_timer_event)
        if platform.machine() in ('arm', 'arm64', 'aarch64'):  # Venom add for script not found
            ensure_edid_validity(self)

        try:
            self.check_tc358743_timer.start(self.check_tc358743_interval)
        except Exception as e:
            log.debug(e)

        self.tc358743 = TC358743()
        self.tc358743.signal_refresh_tc358743_param.connect(self.refresh_tc358743_param)
        self.tc358743.get_tc358743_dv_timing()
        subprocess.Popen("pkill -9 -f ffmpeg", shell=True)
        # install media_engine.video_params video_params_changed slot
        self.media_engine.led_video_params.install_video_params_changed_slot(self.hdmi_video_params_changed)

    def init_ui(self):
        # Initialize the main HDMI input widget and layout
        self.layout = QVBoxLayout()
        self.hdmi_in_widget = QWidget(self.frame)
        self.hdmi_in_layout = QVBoxLayout(self.hdmi_in_widget)

        # Initialize and configure the preview widget
        self.setup_preview_widget()

        # Initialize and configure the HDMI information widget
        self.setup_hdmi_info_widget()

        # Initialize and configure the HDMI control widget
        self.setup_hdmi_ctrl_widget()

        # setup video params widget
        self.setup_video_params_widget()

        # Place hdmi_ctrl_frame and video_params_setting_widget side by side in a horizontal layout."
        hdmi_ctrl_and_video_params_layout = QHBoxLayout()
        hdmi_ctrl_and_video_params_layout.addWidget(self.hdmi_ctrl_frame)
        hdmi_ctrl_and_video_params_layout.addWidget(self.video_params_setting_widget)

        # Add widgets to the HDMI input layout
        self.layout.addWidget(self.hdmi_in_widget)
        self.setLayout(self.layout)
        self.hdmi_in_layout.addWidget(self.preview_widget)
        self.hdmi_in_layout.addWidget(self.hdmi_info_group_box)
        self.hdmi_in_layout.addLayout(hdmi_ctrl_and_video_params_layout)

        # Set the size policy to ensure proper resizing
        self.hdmi_in_widget.setSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Expanding)
        self.video_params_setting_widget.setSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Expanding)

    def setup_hdmi_ctrl_widget(self):
        self.hdmi_ctrl_frame = QFrame(self.hdmi_in_widget)
        self.hdmi_ctrl_frame.setFrameShape(QFrame.StyledPanel)
        self.hdmi_ctrl_frame.setFrameShadow(QFrame.Raised)

        hdmi_ctrl_layout = QGridLayout(self.hdmi_ctrl_frame)

        # Setup Sound action button
        self.sound_control_btn = QPushButton("Sound", self.hdmi_ctrl_frame)
        if self.media_engine.led_video_params.get_play_with_audio() == 1:
            self.sound_control_btn.setIcon(QIcon('materials/soundOnIcon.png'))
        else:
            self.sound_control_btn.setIcon(QIcon('materials/soundOffIcon.png'))
        self.sound_control_btn.setIconSize(QSize(32, 32))
        self.sound_control_btn.setCheckable(True)
        self.sound_control_btn.setChecked(not self.media_engine.led_video_params.get_play_with_audio())
        self.sound_control_btn.clicked.connect(self.sound_btn_clicked)

        # Setup Preview action button
        self.preview_control_btn = QPushButton("Preview", self.hdmi_ctrl_frame)

        if self.media_engine.led_video_params.get_play_with_preview() == 1:
            self.preview_control_btn.setIcon(QIcon('materials/eyeOpenIcon.png'))
        else:
            self.preview_control_btn.setIcon(QIcon('materials/eyeCloseIcon.png'))

        self.preview_control_btn.setIconSize(QSize(32, 32))
        self.preview_control_btn.setCheckable(True)
        self.preview_control_btn.setChecked(not self.media_engine.led_video_params.get_play_with_preview())
        self.preview_control_btn.clicked.connect(self.preview_btn_clicked)

        # Add control buttons to the layout
        hdmi_ctrl_layout.addWidget(self.preview_control_btn, 0, 0)
        hdmi_ctrl_layout.addWidget(self.sound_control_btn, 0, 1)

        # Setup crop widget and layout for controls
        self.crop_setting_widget = QWidget(self.hdmi_ctrl_frame)
        self.crop_setting_widget_layout = QGridLayout(self.crop_setting_widget)

        # Initializing the line edit widgets to be used in the loop
        self.hdmi_in_crop_x_lineedit = QLineEdit(self.crop_setting_widget)
        self.hdmi_in_crop_y_lineedit = QLineEdit(self.crop_setting_widget)
        self.hdmi_in_crop_w_lineedit = QLineEdit(self.crop_setting_widget)
        self.hdmi_in_crop_h_lineedit = QLineEdit(self.crop_setting_widget)

        self.hdmi_in_crop_x_lineedit.setText(str(self.media_engine.led_video_params.get_hdmi_in_start_x()))
        self.hdmi_in_crop_y_lineedit.setText(str(self.media_engine.led_video_params.get_hdmi_in_start_y()))
        self.hdmi_in_crop_w_lineedit.setText(str(self.media_engine.led_video_params.get_hdmi_in_crop_w()))
        self.hdmi_in_crop_h_lineedit.setText(str(self.media_engine.led_video_params.get_hdmi_in_crop_h()))

        edits = [self.hdmi_in_crop_x_lineedit, self.hdmi_in_crop_y_lineedit, self.hdmi_in_crop_w_lineedit,
                 self.hdmi_in_crop_h_lineedit]

        labels = ["Crop Start X:", "Crop Start Y:", "Crop Width:", "Crop Height:"]
        for i, label in enumerate(labels):
            lbl = QLabel(label, self.crop_setting_widget)
            lbl.setFont(QFont(QFont_Style_Default, QFont_Style_Size_M))
            edit = edits[i]
            edit.setFixedWidth(100)
            edit.setFont(QFont(QFont_Style_Default, QFont_Style_Size_M))
            self.crop_setting_widget_layout.addWidget(lbl, i + 1, 0)
            self.crop_setting_widget_layout.addWidget(edit, i + 1, 1)

        # Adding a button to adjust control parameters
        self.adj_ctrl_param_btn = QPushButton("Adjust Parameter", self.crop_setting_widget)
        self.adj_ctrl_param_btn.setFont(QFont(QFont_Style_Default, QFont_Style_Size_M))
        self.adj_ctrl_param_btn.clicked.connect(self.adj_hdmi_ctrl_param)

        self.crop_setting_widget_layout.addWidget(self.adj_ctrl_param_btn, 5, 0, 1, 2)

        # Adding the crop settings widget to the main layout
        self.crop_setting_widget.setLayout(self.crop_setting_widget_layout)
        hdmi_ctrl_layout.addWidget(self.crop_setting_widget, 6, 0, 1, 4)

        # Set the frame layout
        self.hdmi_ctrl_frame.setLayout(hdmi_ctrl_layout)
        self.hdmi_in_layout.addWidget(self.hdmi_ctrl_frame)

    def setup_video_params_widget(self):

        self.video_params_setting_widget = QWidget(self.hdmi_in_widget)
        self.video_params_setting_layout = QGridLayout(self.video_params_setting_widget)

        self.video_brightness_label = QLabel(self.video_params_setting_widget)
        self.video_brightness_label.setFont(QFont(QFont_Style_Default, QFont_Style_Size_M))
        self.video_brightness_label.setText("Frame Brightness:")
        self.video_gamma_label = QLabel(self.video_params_setting_widget)
        self.video_gamma_label.setFont(QFont(QFont_Style_Default, QFont_Style_Size_M))
        self.video_gamma_label.setText("Frame Gamma:")

        self.video_brightness_lineedit = QLineEdit(self.video_params_setting_widget)
        self.video_brightness_lineedit.setFixedWidth(100)
        self.video_brightness_lineedit.setFont(QFont(QFont_Style_Default, QFont_Style_Size_M))
        self.video_brightness_lineedit.setText(str(self.media_engine.led_video_params.get_led_brightness()))

        self.video_gamma_lineedit = QLineEdit(self.video_params_setting_widget)
        self.video_gamma_lineedit.setFixedWidth(100)
        self.video_gamma_lineedit.setFont(QFont(QFont_Style_Default, QFont_Style_Size_M))
        self.video_gamma_lineedit.setText(str(self.media_engine.led_video_params.get_led_gamma()))

        self.brightness_algo_label = QLabel(self.video_params_setting_widget)
        self.brightness_algo_label.setFont(QFont(QFont_Style_Default, QFont_Style_Size_M))
        self.brightness_algo_label.setText("Brightness Method:")
        self.brightness_algo_combobox = QComboBox(self.video_params_setting_widget)
        self.brightness_algo_combobox.setFont(QFont(QFont_Style_Default, QFont_Style_Size_M))
        for i in frame_brightness_alog:
            if '.' in str(i):
                self.brightness_algo_combobox.addItem(str(i).split(".")[1])
            else:
                self.brightness_algo_combobox.addItem(str(i))
        self.brightness_algo_combobox.setCurrentIndex(self.media_engine.led_video_params.get_frame_brightness_algo())

        self.sleep_mode_enable_label = QLabel(self.video_params_setting_widget)
        self.sleep_mode_enable_label.setFont(QFont(QFont_Style_Default, QFont_Style_Size_M))
        self.sleep_mode_enable_label.setText("Sleep Mode:")
        self.sleep_mode_enable_combobox = QComboBox(self.video_params_setting_widget)
        self.sleep_mode_enable_combobox.setFont(QFont(QFont_Style_Default, QFont_Style_Size_M))
        for i in sleep_mode:
            if '.' in str(i):
                self.sleep_mode_enable_combobox.addItem(str(i).split(".")[1])
            else:
                self.sleep_mode_enable_combobox.addItem(str(i))
        self.sleep_mode_enable_combobox.setCurrentIndex(self.media_engine.led_video_params.get_sleep_mode_enable())

        self.target_city_label = QLabel(self.video_params_setting_widget)
        self.target_city_label.setFont(QFont(QFont_Style_Default, QFont_Style_Size_M))
        self.target_city_label.setText("City:")
        self.target_city_combobox = QComboBox(self.video_params_setting_widget)
        self.target_city_combobox.setFont(QFont(QFont_Style_Default, QFont_Style_Size_M))
        for city in City_Map:
            self.target_city_combobox.addItem(city.get("City"))
        self.target_city_combobox.setCurrentIndex(int(self.media_engine.led_video_params.get_target_city_index()))

        self.day_mode_brightness_label = QLabel(self.video_params_setting_widget)
        self.day_mode_brightness_label.setFont(QFont(QFont_Style_Default, QFont_Style_Size_M))
        self.day_mode_brightness_label.setText("Day Mode Brightness:")
        self.day_mode_brightness_lineedit = QLineEdit(self.video_params_setting_widget)
        self.day_mode_brightness_lineedit.setFont(QFont(QFont_Style_Default, QFont_Style_Size_M))
        self.day_mode_brightness_lineedit.setText(
            str(self.media_engine.led_video_params.get_day_mode_frame_brightness()))

        self.night_mode_brightness_label = QLabel(self.video_params_setting_widget)
        self.night_mode_brightness_label.setFont(QFont(QFont_Style_Default, QFont_Style_Size_M))
        self.night_mode_brightness_label.setText("Night Mode Brightness:")
        self.night_mode_brightness_lineedit = QLineEdit(self.video_params_setting_widget)
        self.night_mode_brightness_lineedit.setFont(QFont(QFont_Style_Default, QFont_Style_Size_M))
        self.night_mode_brightness_lineedit.setText(
            str(self.media_engine.led_video_params.get_night_mode_frame_brightness()))

        self.sleep_mode_brightness_label = QLabel(self.video_params_setting_widget)
        self.sleep_mode_brightness_label.setFont(QFont(QFont_Style_Default, QFont_Style_Size_M))
        self.sleep_mode_brightness_label.setText("Sleep Mode Brightness:")
        self.sleep_mode_brightness_lineedit = QLineEdit(self.video_params_setting_widget)
        self.sleep_mode_brightness_lineedit.setFont(QFont(QFont_Style_Default, QFont_Style_Size_M))
        self.sleep_mode_brightness_lineedit.setText(
            str(self.media_engine.led_video_params.get_sleep_mode_frame_brightness()))

        self.led_r_gain_label = QLabel(self.video_params_setting_widget)
        self.led_r_gain_label.setFont(QFont(QFont_Style_Default, QFont_Style_Size_M))
        self.led_r_gain_label.setText("Led R Gain:")
        self.led_r_gain_lineedit = QLineEdit(self.video_params_setting_widget)
        self.led_r_gain_lineedit.setFont(QFont(QFont_Style_Default, QFont_Style_Size_M))
        self.led_r_gain_lineedit.setText(
            str(self.media_engine.led_video_params.get_led_red_gain()))

        self.led_g_gain_label = QLabel(self.video_params_setting_widget)
        self.led_g_gain_label.setFont(QFont(QFont_Style_Default, QFont_Style_Size_M))
        self.led_g_gain_label.setText("Led G Gain:")
        self.led_g_gain_lineedit = QLineEdit(self.video_params_setting_widget)
        self.led_g_gain_lineedit.setFont(QFont(QFont_Style_Default, QFont_Style_Size_M))
        self.led_g_gain_lineedit.setText(
            str(self.media_engine.led_video_params.get_led_green_gain()))

        self.led_b_gain_label = QLabel(self.video_params_setting_widget)
        self.led_b_gain_label.setFont(QFont(QFont_Style_Default, QFont_Style_Size_M))
        self.led_b_gain_label.setText("Led G Gain:")
        self.led_b_gain_lineedit = QLineEdit(self.video_params_setting_widget)
        self.led_b_gain_lineedit.setFont(QFont(QFont_Style_Default, QFont_Style_Size_M))
        self.led_b_gain_lineedit.setText(
            str(self.media_engine.led_video_params.get_led_blue_gain()))

        self.icled_type_label = QLabel(self.video_params_setting_widget)
        self.icled_type_label.setFont(QFont(QFont_Style_Default, QFont_Style_Size_M))
        self.icled_type_label.setText("ICLed Type:")
        self.icled_type_combobox = QComboBox(self.video_params_setting_widget)
        self.icled_type_combobox.setFont(QFont(QFont_Style_Default, QFont_Style_Size_M))
        for str_type in icled_type:
            if '.' in str(str_type):
                self.icled_type_combobox.addItem(str(str_type).split(".")[1])
            else:
                self.icled_type_combobox.addItem(str(str_type))
        self.icled_type_combobox.setCurrentIndex(int(self.media_engine.led_video_params.get_icled_type()))

        self.output_frame_width_label = QLabel(self.video_params_setting_widget)
        self.output_frame_width_label.setFont(QFont(QFont_Style_Default, QFont_Style_Size_M))
        self.output_frame_width_label.setText("Frame Width:")
        self.output_frame_width_lineedit = QLineEdit(self.video_params_setting_widget)
        self.output_frame_width_lineedit.setFont(QFont(QFont_Style_Default, QFont_Style_Size_M))
        self.output_frame_width_lineedit.setText(str(self.media_engine.led_video_params.get_output_frame_width()))

        self.output_frame_height_label = QLabel(self.video_params_setting_widget)
        self.output_frame_height_label.setFont(QFont(QFont_Style_Default, QFont_Style_Size_M))
        self.output_frame_height_label.setText("Frame Height:")
        self.output_frame_height_lineedit = QLineEdit(self.video_params_setting_widget)
        self.output_frame_height_lineedit.setFont(QFont(QFont_Style_Default, QFont_Style_Size_M))
        self.output_frame_height_lineedit.setText(str(self.media_engine.led_video_params.get_output_frame_height()))

        self.output_fps_label = QLabel(self.video_params_setting_widget)
        self.output_fps_label.setFont(QFont(QFont_Style_Default, QFont_Style_Size_M))
        self.output_fps_label.setText("FPS:")
        self.output_fps_lineedit = QLineEdit(self.video_params_setting_widget)
        self.output_fps_lineedit.setFont(QFont(QFont_Style_Default, QFont_Style_Size_M))
        self.output_fps_lineedit.setText(str(self.media_engine.led_video_params.get_output_fps()))

        self.video_adj_br_ga_btn = QPushButton("Adjust Brightness Parameter", self.video_params_setting_widget)
        self.video_adj_br_ga_btn.setFont(QFont(QFont_Style_Default, QFont_Style_Size_M))
        self.video_adj_br_ga_btn.clicked.connect(self.adj_video_br_ga_param)

        self.video_params_setting_layout.addWidget(self.video_brightness_label, 0, 2)
        self.video_params_setting_layout.addWidget(self.video_gamma_label, 1, 2)
        self.video_params_setting_layout.addWidget(self.video_brightness_lineedit, 0, 3)
        self.video_params_setting_layout.addWidget(self.video_gamma_lineedit, 1, 3)
        self.video_params_setting_layout.addWidget(self.brightness_algo_label, 2, 2)
        self.video_params_setting_layout.addWidget(self.brightness_algo_combobox, 2, 3)
        self.video_params_setting_layout.addWidget(self.target_city_label, 3, 2)
        self.video_params_setting_layout.addWidget(self.target_city_combobox, 3, 3)

        self.video_params_setting_layout.addWidget(self.sleep_mode_enable_label, 0, 4)
        self.video_params_setting_layout.addWidget(self.sleep_mode_enable_combobox, 0, 5)
        self.video_params_setting_layout.addWidget(self.day_mode_brightness_label, 1, 4)
        self.video_params_setting_layout.addWidget(self.day_mode_brightness_lineedit, 1, 5)
        self.video_params_setting_layout.addWidget(self.night_mode_brightness_label, 2, 4)
        self.video_params_setting_layout.addWidget(self.night_mode_brightness_lineedit, 2, 5)
        self.video_params_setting_layout.addWidget(self.sleep_mode_brightness_label, 3, 4)
        self.video_params_setting_layout.addWidget(self.sleep_mode_brightness_lineedit, 3, 5)

        self.video_params_setting_layout.addWidget(self.icled_type_label, 0, 6)
        self.video_params_setting_layout.addWidget(self.icled_type_combobox, 0, 7)
        self.video_params_setting_layout.addWidget(self.led_r_gain_label, 1, 6)
        self.video_params_setting_layout.addWidget(self.led_r_gain_lineedit, 1, 7)
        self.video_params_setting_layout.addWidget(self.led_g_gain_label, 2, 6)
        self.video_params_setting_layout.addWidget(self.led_g_gain_lineedit, 2, 7)
        self.video_params_setting_layout.addWidget(self.led_b_gain_label, 3, 6)
        self.video_params_setting_layout.addWidget(self.led_b_gain_lineedit, 3, 7)

        self.video_params_setting_layout.addWidget(self.output_frame_width_label, 0, 8)
        self.video_params_setting_layout.addWidget(self.output_frame_width_lineedit, 0, 9)
        self.video_params_setting_layout.addWidget(self.output_frame_height_label, 1, 8)
        self.video_params_setting_layout.addWidget(self.output_frame_height_lineedit, 1, 9)
        self.video_params_setting_layout.addWidget(self.output_fps_label, 2, 8)
        self.video_params_setting_layout.addWidget(self.output_fps_lineedit, 2, 9)

        self.video_params_setting_layout.addWidget(self.video_adj_br_ga_btn, 4, 2, 1, 8)

    def setup_preview_widget(self):
        self.preview_widget = QWidget()
        self.preview_widget_layout = QGridLayout(self.preview_widget)

        # Setup preview label
        self.preview_label = QLabel("HDMI-in Preview", self.preview_widget)
        self.preview_label.setFont(QFont(QFont_Style_Default, QFont_Style_Size_M))
        self.preview_label.setFixedHeight(160)
        self.preview_label.setScaledContents(True)

        # Setup play action button
        self.play_action_btn = QPushButton("Start Play", self.preview_widget)
        self.play_action_btn.setFont(QFont(QFont_Style_Default, QFont_Style_Size_M))
        self.play_action_btn.clicked.connect(self.pause_btn_clicked)
        self.play_action_btn.setStyleSheet(QPushHdmiPlayButton_Style)

        # Setup stop action button
        self.stop_action_btn = QPushButton("Stop Play", self.preview_widget)
        self.stop_action_btn.setFont(QFont(QFont_Style_Default, QFont_Style_Size_M))
        self.stop_action_btn.clicked.connect(self.stop_btn_clicked)
        self.stop_action_btn.setStyleSheet(QPushHdmiStopButton_Style)

        # Setup process status frame
        self.process_status_frame = QFrame(self.preview_widget)
        self.process_status_frame.setFrameShape(QFrame.Box)
        self.process_status_frame.setLineWidth(2)
        self.process_status_frame.setStyleSheet("border-color: #808080; border-radius: 5px;")
        self.process_status_layout = QVBoxLayout(self.process_status_frame)

        # Setup HDMI play status label
        self.hdmi_in_play_status_label = QLabel("Non-Streaming", self.process_status_frame)
        self.hdmi_in_play_status_label.setFont(QFont(QFont_Style_Default, QFont_Style_Size_M))

        # Setup process status label
        self.pid_status_label = QLabel("None", self.process_status_frame)
        self.pid_status_label.setFont(QFont(QFont_Style_Default, QFont_Style_Size_M))

        self.process_status_layout.addWidget(self.hdmi_in_play_status_label)
        self.process_status_layout.addWidget(self.pid_status_label)

        # Add widgets to the layout
        self.preview_widget_layout.addWidget(self.preview_label, 0, 0, 1, 4)
        self.preview_widget_layout.addWidget(self.play_action_btn, 2, 0, 1, 2)
        self.preview_widget_layout.addWidget(self.stop_action_btn, 2, 2, 1, 2)
        self.preview_widget_layout.addWidget(self.process_status_frame, 4, 0, 1, 2)

    def setup_hdmi_info_widget(self):
        self.hdmi_info_group_box = QGroupBox("HDMI Information")
        self.hdmi_info_group_box.setFont(QFont(QFont_Style_Default, QFont_Style_Size_M))

        info_widget_layout = QGridLayout()

        # Setup HDMI input/output width label and value
        self.hdmi_in_info_width_label = QLabel("HDMI_In Width:")
        self.hdmi_in_info_width_label.setFont(QFont(QFont_Style_Default, QFont_Style_Size_M))
        self.hdmi_in_info_width_res_label = QLabel("NA")
        self.hdmi_in_info_width_res_label.setFont(QFont(QFont_Style_Default, QFont_Style_Size_M))

        self.hdmi_out_info_width_label = QLabel("HDMI_Out Width:")
        self.hdmi_out_info_width_label.setFont(QFont(QFont_Style_Default, QFont_Style_Size_M))
        self.hdmi_out_info_width_res_label = QLabel("NA")
        self.hdmi_out_info_width_res_label.setFont(QFont(QFont_Style_Default, QFont_Style_Size_M))

        # Setup HDMI input/output height label and value
        self.hdmi_in_info_height_label = QLabel("HDMI_In Height:")
        self.hdmi_in_info_height_label.setFont(QFont(QFont_Style_Default, QFont_Style_Size_M))
        self.hdmi_in_info_height_res_label = QLabel("NA")
        self.hdmi_in_info_height_res_label.setFont(QFont(QFont_Style_Default, QFont_Style_Size_M))

        self.hdmi_out_info_height_label = QLabel("HDMI_Out Height:")
        self.hdmi_out_info_height_label.setFont(QFont(QFont_Style_Default, QFont_Style_Size_M))
        self.hdmi_out_info_height_res_label = QLabel("NA")
        self.hdmi_out_info_height_res_label.setFont(QFont(QFont_Style_Default, QFont_Style_Size_M))

        # Setup HDMI input/output FPS label and value
        self.hdmi_in_info_fps_label = QLabel("HDMI_In FPS:")
        self.hdmi_in_info_fps_label.setFont(QFont(QFont_Style_Default, QFont_Style_Size_M))
        self.hdmi_in_info_fps_res_label = QLabel("NA")
        self.hdmi_in_info_fps_res_label.setFont(QFont(QFont_Style_Default, QFont_Style_Size_M))

        self.hdmi_out_info_fps_label = QLabel("HDMI_Out FPS:")
        self.hdmi_out_info_fps_label.setFont(QFont(QFont_Style_Default, QFont_Style_Size_M))
        self.hdmi_out_info_fps_res_label = QLabel("NA")
        self.hdmi_out_info_fps_res_label.setFont(QFont(QFont_Style_Default, QFont_Style_Size_M))

        # Add labels and values to the layout
        info_widget_layout.addWidget(self.hdmi_in_info_width_label, 0, 0)
        info_widget_layout.addWidget(self.hdmi_in_info_width_res_label, 0, 1)
        info_widget_layout.addWidget(self.hdmi_in_info_height_label, 1, 0)
        info_widget_layout.addWidget(self.hdmi_in_info_height_res_label, 1, 1)
        info_widget_layout.addWidget(self.hdmi_in_info_fps_label, 2, 0)
        info_widget_layout.addWidget(self.hdmi_in_info_fps_res_label, 2, 1)

        info_widget_layout.addWidget(self.hdmi_out_info_width_label, 0, 2)
        info_widget_layout.addWidget(self.hdmi_out_info_width_res_label, 0, 3)
        info_widget_layout.addWidget(self.hdmi_out_info_height_label, 1, 2)
        info_widget_layout.addWidget(self.hdmi_out_info_height_res_label, 1, 3)
        info_widget_layout.addWidget(self.hdmi_out_info_fps_label, 2, 2)
        info_widget_layout.addWidget(self.hdmi_out_info_fps_res_label, 2, 3)

        info_widget_layout.setContentsMargins(10, 20, 10, 20)
        self.hdmi_in_layout.addWidget(self.hdmi_info_group_box)
        self.hdmi_info_group_box.setLayout(info_widget_layout)

    def media_play_status_changed(self, status: int, src: str):
        if status == PlayStatus.Playing:
            self.play_action_btn.setText("Pause")
            self.hdmi_in_play_status_label.setText("Streaming")
        elif status == PlayStatus.Pausing:
            self.play_action_btn.setText("Resume")
            self.hdmi_in_play_status_label.setText("Paused")
        elif (status == PlayStatus.Stop or
              status == PlayStatus.Initial):
            self.hdmi_in_play_status_label.setText("Stopped")
            self.play_action_btn.setText("Start Play")
        else:
            self.hdmi_in_play_status_label.setText("Non-Streaming")
        self.update_process_info()

    def start_streaming(self):
        self.streamStateMutex.lock()
        if self.streamingStatus is False:
            self.media_engine.resume_playing()
            self.media_engine.stop_play()
            if self.media_engine.play_hdmi_in_worker is None:
                log.debug("Start streaming")
                self.media_engine.hdmi_in_play(self.video_device,
                                               active_width=int(self.tc358743.hdmi_width),
                                               active_height=int(self.tc358743.hdmi_height),
                                               )
                self.streamingStatus = True
            self.measurement_tc358743 = True
        self.streamStateMutex.unlock()

    def stop_streaming(self, MeasurementEnable: False):
        self.streamStateMutex.lock()
        self.streamingStatus = False
        self.measurement_tc358743 = MeasurementEnable
        self.media_engine.stop_play()
        self.refresh_tc358743_param(False, self.tc358743.hdmi_width, self.tc358743.hdmi_height, self.tc358743.hdmi_fps)
        self.update_process_info()
        self.streamStateMutex.unlock()

    def stop_btn_clicked(self):
        self.stop_streaming(False)

    def pause_btn_clicked(self):
        if PlayStatus.Playing == self.media_engine.playing_status:
            self.media_engine.pause_playing()
        elif PlayStatus.Pausing == self.media_engine.playing_status:
            self.media_engine.resume_playing()
        elif (PlayStatus.Stop == self.media_engine.playing_status or
              PlayStatus.Initial == self.media_engine.playing_status):
            self.start_streaming()

    def check_tc358743_timer_event(self):
        # log.debug("enter check_tc358743_timer")
        self.streamStateMutex.lock()
        if self.main_windows.right_frame_page_index != Page.HDMI_IN.value:
            # log.debug("Not in hdmi-in page")
            self.prev_hdmi_info = None
            self.streamingStatus = False
            self.measurement_tc358743 = True
            self.streamStateMutex.unlock()
            return

        self.streamStateMutex.unlock()

        current_hdmi_info = self.tc358743.get_tc358743_hdmi_info()

        (current_hdmi_connected, current_hdmi_hdmi_width,
         current_hdmi_height, current_hdmi_hdmi_fps) = current_hdmi_info

        try:

            if (self.prev_hdmi_info is None or
                    current_hdmi_info != self.prev_hdmi_info):

                if (current_hdmi_connected is True and
                        self.measurement_tc358743 is True):

                    if self.tc358743.set_tc358743_dv_bt_timing() is True:
                        if self.media_engine.play_hdmi_in_worker is None:
                            self.handleHdmiStreamStart()
                            self.streamingStatus = True
                            self.preview_label.setText("HDMI-in connected")
                    else:
                        hdmi_info_list = list(current_hdmi_info)
                        hdmi_info_list[0] = False
                        current_hdmi_info = tuple(hdmi_info_list)
                        self.stop_streaming(True)
                        subprocess.Popen("pkill -9 -f ffmpeg", shell=True)

                else:
                    if self.tc358743.hdmi_connected is True:
                        if current_hdmi_connected is False:
                            self.stop_streaming(True)
                            subprocess.Popen("pkill -9 -f ffmpeg", shell=True)
                            self.tc358743.reinit_tc358743_dv_timing()
                            self.preview_label.setText("HDMI-in Signal Lost")

            self.prev_hdmi_info = current_hdmi_info
            (self.tc358743.hdmi_connected, self.tc358743.hdmi_width,
             self.tc358743.hdmi_height, self.tc358743.hdmi_fps) = current_hdmi_info

        except Exception as e:
            log.debug(e)
            self.check_tc358743_timer.stop()
            self.check_tc358743_timer.start(self.check_tc358743_interval)
            self.streamingStatus = False
            self.prev_hdmi_info = None
            self.measurement_tc358743 = True
            self.streamStateMutex.unlock()
            log.debug("restart check_tc358743_timer")

    def refresh_tc358743_param(self, connected=False, width="NA", height="NA", fps="NA"):

        self.hdmi_out_info_width_res_label.setText(str(self.media_engine.output_streaming_width))
        self.hdmi_out_info_height_res_label.setText(str(self.media_engine.output_streaming_height))
        self.hdmi_out_info_fps_res_label.setText(str(self.media_engine.output_streaming_fps))

        self.hdmi_in_info_width_res_label.setText(str(width))
        self.hdmi_in_info_height_res_label.setText(str(height))
        self.hdmi_in_info_fps_res_label.setText(str(fps))

    def handleHdmiStreamStart(self):

        self.streamStateMutex.lock()

        log.debug("handleHdmiStreamStart")

        if self.streamingStatus is True:
            self.streamStateMutex.unlock()
            return

        self.media_engine.stop_play()
        # find any ffmpeg process
        p = subprocess.run(["pgrep", "ffmpeg"],
                           capture_output=True, text=True)
        if p.stdout:
            subprocess.run(["pkill", "-9", "-f", "ffmpeg"])

        # find any show_ffmpeg_shared_memory process
        p = subprocess.run(["pgrep", "show_ffmpeg_shared_memory"],
                           capture_output=True, text=True)
        if p.stdout:
            subprocess.run(["pkill", "-9", "-f", "show_ffmpeg_shared_memory"])

        # find any ffprobe process
        p = subprocess.run(["pgrep", "ffprobe"],
                           capture_output=True, text=True)
        if p.stdout:
            subprocess.run(["pkill", "-9", "-f", "ffprobe"])

        # find any arecord process
        p = subprocess.run(["pgrep", "arecord"],
                           capture_output=True, text=True)
        if p.stdout:
            subprocess.run(["pkill", "-9", "-f", "arecord"])

        if self.tc358743.set_tc358743_dv_bt_timing() is True:
            self.tc358743.reinit_tc358743_dv_timing()
            self.media_engine.hdmi_in_play(self.video_device,
                                           active_width=int(self.tc358743.hdmi_width),
                                           active_height=int(self.tc358743.hdmi_height),
                                           )
        self.streamStateMutex.unlock()

    def sound_btn_clicked(self):
        log.debug("")
        if self.sound_control_btn.isChecked():
            self.media_engine.led_video_params.set_play_with_audio(0)
            self.sound_control_btn.setIcon(QIcon('materials/soundOffIcon.png'))
        else:
            self.media_engine.led_video_params.set_play_with_audio(1)
            self.sound_control_btn.setIcon(QIcon('materials/soundOnIcon.png'))

    def preview_btn_clicked(self):
        log.debug("")
        if self.preview_control_btn.isChecked():
            self.media_engine.led_video_params.set_play_with_preview(0)
            self.preview_control_btn.setIcon(QIcon('materials/eyeCloseIcon.png'))
        else:
            self.media_engine.led_video_params.set_play_with_preview(1)
            self.preview_control_btn.setIcon(QIcon('materials/eyeOpenIcon.png'))

    def update_process_info(self):
        try:
            result = subprocess.run(["ps", "-elf"], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
            output = result.stdout

            ffmpeg_pids = []
            shared_memory_pids = []
            record_pids = []

            for line in output.splitlines():
                if 'show_ffmpeg_shared_memory' in line:
                    pid = parse_pid(line)
                    if pid: shared_memory_pids.append(pid)
                elif 'ffmpeg' in line and 'grep' not in line:
                    pid = parse_pid(line)
                    if pid: ffmpeg_pids.append(pid)
                elif 'arecord' in line and 'grep' not in line:
                    pid = parse_pid(line)
                    if pid: record_pids.append(pid)

            self.pid_status_label.setText(
                f"ff PIDs: {', '.join(ffmpeg_pids)}\n"
                f"Agent PIDs: {', '.join(shared_memory_pids)}\n"
                f"Recorder PIDs: {', '.join(record_pids)}"
            )
        except Exception as e:
            log.debug("Error updating process label:", e)

    def adj_hdmi_ctrl_param(self):
        self.media_engine.led_video_params.set_hdmi_in_crop_w(int(self.hdmi_in_crop_w_lineedit.text()))
        self.media_engine.led_video_params.set_hdmi_in_crop_h(int(self.hdmi_in_crop_h_lineedit.text()))
        self.media_engine.led_video_params.set_hdmi_in_start_x(int(self.hdmi_in_crop_x_lineedit.text()))
        self.media_engine.led_video_params.set_hdmi_in_start_y(int(self.hdmi_in_crop_y_lineedit.text()))

    def hdmi_video_params_changed(self):
        log.debug("hdmi_video_params_changed")

        self.preview_control_btn.setIcon(QIcon(
            'materials/eyeOpenIcon.png' if self.media_engine.led_video_params.get_play_with_preview() == 1
            else 'materials/eyeCloseIcon.png'))
        self.sound_control_btn.setIcon(QIcon(
            'materials/soundOnIcon.png' if self.media_engine.led_video_params.get_play_with_audio() == 1
            else 'materials/soundOffIcon.png'))

        self.video_brightness_lineedit.setText(str(self.media_engine.led_video_params.get_led_brightness()))
        self.video_gamma_lineedit.setText(str(self.media_engine.led_video_params.get_led_gamma()))
        self.brightness_algo_combobox.setCurrentIndex(self.media_engine.led_video_params.get_frame_brightness_algo())

        self.sleep_mode_enable_combobox.setCurrentIndex(self.media_engine.led_video_params.get_sleep_mode_enable())
        self.target_city_combobox.setCurrentIndex(self.media_engine.led_video_params.get_target_city_index())
        self.day_mode_brightness_lineedit.setText(
            str(self.media_engine.led_video_params.get_day_mode_frame_brightness()))
        self.night_mode_brightness_lineedit.setText(
            str(self.media_engine.led_video_params.get_night_mode_frame_brightness()))
        self.sleep_mode_brightness_lineedit.setText(
            str(self.media_engine.led_video_params.get_sleep_mode_frame_brightness()))

        self.icled_type_combobox.setCurrentIndex(int(self.media_engine.led_video_params.get_icled_type()))
        self.led_r_gain_lineedit.setText(str(self.media_engine.led_video_params.get_led_red_gain()))
        self.led_g_gain_lineedit.setText(str(self.media_engine.led_video_params.get_led_green_gain()))
        self.led_b_gain_lineedit.setText(str(self.media_engine.led_video_params.get_led_blue_gain()))

        self.output_frame_width_lineedit.setText(str(self.media_engine.led_video_params.get_output_frame_width()))
        self.output_frame_height_lineedit.setText(str(self.media_engine.led_video_params.get_output_frame_height()))
        self.output_fps_lineedit.setText(str(self.media_engine.led_video_params.get_output_fps()))

        self.hdmi_in_crop_x_lineedit.setText(str(self.media_engine.led_video_params.get_media_file_start_x()))
        self.hdmi_in_crop_y_lineedit.setText(str(self.media_engine.led_video_params.get_media_file_start_y()))
        self.hdmi_in_crop_w_lineedit.setText(str(self.media_engine.led_video_params.get_media_file_crop_w()))
        self.hdmi_in_crop_h_lineedit.setText(str(self.media_engine.led_video_params.get_media_file_crop_h()))

    def adj_video_br_ga_param(self):
        if (int(self.video_brightness_lineedit.text()) < MIN_FRAME_BRIGHTNESS
                or int(self.video_brightness_lineedit.text()) > MAX_FRAME_BRIGHTNESS):
            self.video_brightness_lineedit.setText(str(self.media_engine.led_video_params.get_led_brightness()))
            return
        if (float(self.video_gamma_lineedit.text()) < MIN_FRAME_GAMMA
                or float(self.video_gamma_lineedit.text()) > MAX_FRAME_GAMMA):
            self.video_gamma_lineedit.setText(str(self.media_engine.led_video_params.get_led_gamma()))
            return

        if (int(self.day_mode_brightness_lineedit.text()) < MIN_FRAME_BRIGHTNESS
                or int(self.day_mode_brightness_lineedit.text()) > MAX_FRAME_BRIGHTNESS):
            self.day_mode_brightness_lineedit.setText(
                str(self.media_engine.led_video_params.get_day_mode_frame_brightness()))

        if (int(self.night_mode_brightness_lineedit.text()) < MIN_FRAME_BRIGHTNESS
                or int(self.night_mode_brightness_lineedit.text()) > MAX_FRAME_BRIGHTNESS):
            self.night_mode_brightness_lineedit.setText(
                str(self.media_engine.led_video_params.get_night_mode_frame_brightness()))

        if (int(self.sleep_mode_brightness_lineedit.text()) < MIN_FRAME_BRIGHTNESS
                or int(self.sleep_mode_brightness_lineedit.text()) > MAX_FRAME_BRIGHTNESS):
            self.sleep_mode_brightness_lineedit.setText(
                str(self.media_engine.led_video_params.get_sleep_mode_frame_brightness()))

        ''' set led brightness '''
        if self.media_engine.led_video_params.get_led_brightness() != int(self.video_brightness_lineedit.text()):
            self.media_engine.led_video_params.set_led_brightness(int(self.video_brightness_lineedit.text()))
        ''' set led gamma '''
        if self.media_engine.led_video_params.get_led_gamma() != float(self.video_gamma_lineedit.text()):
            # send_message(set_gamma=self.video_gamma_lineedit.text()) # for test
            self.media_engine.led_video_params.set_led_gamma(float(self.video_gamma_lineedit.text()))

        ''' set icled type '''
        if self.media_engine.led_video_params.get_icled_type() != int(self.icled_type_combobox.currentIndex()):
            self.media_engine.led_video_params.set_icled_type(int(self.icled_type_combobox.currentIndex()))

        ''' set led rgb gain '''
        if self.media_engine.led_video_params.get_led_red_gain() != int(self.led_r_gain_lineedit.text()):
            self.media_engine.led_video_params.set_led_red_gain(int(self.led_r_gain_lineedit.text()))
        if self.media_engine.led_video_params.get_led_green_gain() != int(self.led_g_gain_lineedit.text()):
            self.media_engine.led_video_params.set_led_green_gain(int(self.led_g_gain_lineedit.text()))
        if self.media_engine.led_video_params.get_led_blue_gain() != int(self.led_b_gain_lineedit.text()):
            self.media_engine.led_video_params.set_led_blue_gain(int(self.led_b_gain_lineedit.text()))

        ''' set brightness algo '''
        if (self.media_engine.led_video_params.get_frame_brightness_algo() !=
                self.brightness_algo_combobox.currentIndex()):
            log.debug("brightness_algo changed")
            self.media_engine.led_video_params.set_frame_brightness_algo(self.brightness_algo_combobox.currentIndex())

        ''' set sleep mode enable '''
        if (self.media_engine.led_video_params.get_sleep_mode_enable() !=
                self.sleep_mode_enable_combobox.currentIndex()):
            log.debug("sleep_mode changed")
            self.media_engine.led_video_params.set_sleep_mode_enable(self.sleep_mode_enable_combobox.currentIndex())

        ''' set target city'''
        if (self.media_engine.led_video_params.get_target_city_index() !=
                self.target_city_combobox.currentIndex()):
            log.debug("target city changed")
            self.media_engine.led_video_params.set_target_city_index(self.target_city_combobox.currentIndex())

        ''' set led day mode brightness '''
        if (self.media_engine.led_video_params.get_day_mode_frame_brightness() !=
                int(self.day_mode_brightness_lineedit.text())):
            self.media_engine.led_video_params.set_day_mode_frame_brightness(
                int(self.day_mode_brightness_lineedit.text()))

        ''' set led night mode brightness '''
        if (self.media_engine.led_video_params.get_night_mode_frame_brightness() !=
                int(self.night_mode_brightness_lineedit.text())):
            self.media_engine.led_video_params.set_night_mode_frame_brightness(
                int(self.night_mode_brightness_lineedit.text()))

        ''' set led sleep mode brightness '''
        if (self.media_engine.led_video_params.get_sleep_mode_frame_brightness() !=
                int(self.sleep_mode_brightness_lineedit.text())):
            self.media_engine.led_video_params.set_sleep_mode_frame_brightness(
                int(self.sleep_mode_brightness_lineedit.text()))

        ''' Frame width/height/fps'''
        if self.media_engine.led_video_params.get_output_frame_width() != int(self.output_frame_width_lineedit.text()):
            self.media_engine.led_video_params.set_output_frame_width(int(self.output_frame_width_lineedit.text()))

        if (self.media_engine.led_video_params.get_output_frame_height() !=
                int(self.output_frame_height_lineedit.text())):
            self.media_engine.led_video_params.set_output_frame_height(int(self.output_frame_height_lineedit.text()))

        if self.media_engine.led_video_params.get_output_fps() != int(self.output_fps_lineedit.text()):
            self.media_engine.led_video_params.set_output_fps(int(self.output_fps_lineedit.text()))


def ensure_edid_validity(self):
    p = os.popen("v4l2-ctl --get-edid")
    preproc = p.read()
    if "failed" in preproc:
        p = os.popen("write_tc358743_edid.sh")
        time.sleep(5)
        p.close()
    p.close()


def parse_pid(line):
    parts = line.split()
    return parts[3] if len(parts) > 3 else None
