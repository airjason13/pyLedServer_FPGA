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

        # Add widgets to the HDMI input layout
        self.layout.addWidget(self.hdmi_in_widget)
        self.setLayout(self.layout)
        self.hdmi_in_layout.addWidget(self.preview_widget)
        self.hdmi_in_layout.addWidget(self.hdmi_info_group_box)
        self.hdmi_in_layout.addWidget(self.hdmi_ctrl_frame)

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
        self.media_engine.led_video_params.sync_video_param()
        if self.streamingStatus is True:
            self.stop_streaming(False)
            self.start_streaming()

    def hdmi_video_params_changed(self):
        log.debug("hdmi_video_params_changed")

        self.preview_control_btn.setIcon(QIcon(
            'materials/eyeOpenIcon.png' if self.media_engine.led_video_params.get_play_with_preview() == 1
            else 'materials/eyeCloseIcon.png'))
        self.sound_control_btn.setIcon(QIcon(
            'materials/soundOnIcon.png' if self.media_engine.led_video_params.get_play_with_audio() == 1
            else 'materials/soundOffIcon.png'))



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
