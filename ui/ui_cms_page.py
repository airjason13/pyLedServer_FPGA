import os
import signal
import subprocess
import time

from PyQt5.QtCore import QSize
from PyQt5.QtGui import QFont, QIcon
from PyQt5.QtWidgets import QWidget, QLabel, QGridLayout, QPushButton, QLineEdit, QComboBox

from astral_hashmap import City_Map
from global_def import log, icled_type, sleep_mode, frame_brightness_alog, MIN_FRAME_BRIGHTNESS, MAX_FRAME_BRIGHTNESS, \
    MIN_FRAME_GAMMA, MAX_FRAME_GAMMA
from media_engine.media_engine import MediaEngine
from qt_ui_style.button_qss import QFont_Style_Default, \
    QFont_Style_Size_L, QFont_Style_Size_M


class CMSPage(QWidget):
    def __init__(self, _main_window, _frame: QWidget, _name: str, media_engine: MediaEngine, **kwargs):
        super(CMSPage, self).__init__()
        log.debug("CMS Page Init")
        self.main_windows = _main_window
        self.frame = _frame
        self.media_engine = media_engine
        self.widget = QWidget(self.frame)
        self.name = _name
        self.name_label = None
        self.cms_start_btn = None
        self.cms_stop_btn = None
        self.grid_layout = None
        self.browser_process = None


        self.x_padding = 4
        self.y_padding = 29
        self.chromium_pos_x = 10
        self.chromium_pos_y = 10
        self.chromium_width = 640
        self.chromium_height = 480

        self.video_crop_x_lineedit = None
        self.video_crop_y_lineedit = None
        self.video_crop_w_lineedit = None
        self.video_crop_h_lineedit = None
        self.media_adj_crop_btn = None

        self.video_brightness_label = None
        self.video_gamma_label = None
        self.video_brightness_lineedit = None
        self.video_gamma_lineedit = None
        self.video_adj_br_ga_btn = None

        self.brightness_algo_label = None
        self.brightness_algo_combobox = None
        self.sleep_mode_enable_label = None
        self.sleep_mode_enable_combobox = None
        self.target_city_label = None
        self.target_city_combobox = None

        self.day_mode_brightness_label = None
        self.day_mode_brightness_lineedit = None
        self.night_mode_brightness_label = None
        self.night_mode_brightness_lineedit = None
        self.sleep_mode_brightness_label = None
        self.sleep_mode_brightness_lineedit = None

        self.icled_type_label = None
        self.icled_type_combobox = None

        self.led_r_gain_label = None
        self.led_r_gain_lineedit = None
        self.led_g_gain_label = None
        self.led_g_gain_lineedit = None
        self.led_b_gain_label = None
        self.led_b_gain_lineedit = None

        self.output_frame_width_label = None
        self.output_frame_width_lineedit = None
        self.output_frame_height_label = None
        self.output_frame_height_lineedit = None
        self.output_fps_label = None
        self.output_fps_lineedit = None

        self.video_params_setting_layout = None

        self.preview_control_btn = None
        self.sound_control_btn = None

        '''media control panel'''
        self.media_control_panel = None
        self.media_control_panel_layout = None

        ''' media param panel '''
        self.media_crop_panel = None
        self.media_crop_panel_layout = None

        self.video_params_setting_widget = None
        self.video_params_setting_layout = None

        self.init_ui()
        log.debug("CMS Page")


    def init_ui(self):
        log.debug("CMS Page init_ui")
        self.name_label = QLabel(self.widget)
        self.name_label.setText(self.name + "\n" + "Status: Standby")
        self.name_label.setFont(QFont(QFont_Style_Default, QFont_Style_Size_L))

        self.cms_start_btn = QPushButton(self.widget)
        self.cms_start_btn.setText("Start CMS")
        # self.cms_start_btn.setFixedSize(256, 128)
        self.cms_start_btn.clicked.connect(self.cms_start_btn_clicked)
        self.cms_stop_btn = QPushButton(self.widget)
        # self.cms_stop_btn.setFixedSize(256, 128)
        self.cms_stop_btn.setText("Stop CMS")
        self.cms_stop_btn.clicked.connect(self.cms_stop_btn_clicked)

        self.cms_start_btn.setFont(QFont(QFont_Style_Default, QFont_Style_Size_L))
        self.cms_stop_btn.setFont(QFont(QFont_Style_Default, QFont_Style_Size_L))

        self.sound_control_btn = QPushButton()

        if self.media_engine.led_video_params.get_play_with_audio() == 1:
            self.sound_control_btn.setIcon(QIcon('materials/soundOnIcon.png'))
        else:
            self.sound_control_btn.setIcon(QIcon('materials/soundOffIcon.png'))

        self.sound_control_btn.setIconSize(QSize(32, 32))
        self.sound_control_btn.setCheckable(True)
        self.sound_control_btn.setChecked(not self.media_engine.led_video_params.get_play_with_audio())
        self.sound_control_btn.clicked.connect(self.sound_btn_clicked)

        self.preview_control_btn = QPushButton()

        if self.media_engine.led_video_params.get_play_with_preview() == 1:
            self.preview_control_btn.setIcon(QIcon('materials/eyeOpenIcon.png'))
        else:
            self.preview_control_btn.setIcon(QIcon('materials/eyeCloseIcon.png'))

        self.preview_control_btn.setIconSize(QSize(32, 32))
        self.preview_control_btn.setCheckable(True)
        self.preview_control_btn.setChecked(not self.media_engine.led_video_params.get_play_with_preview())
        self.preview_control_btn.clicked.connect(self.preview_btn_clicked)

        # handle play/stop, preview/sound
        self.media_control_panel = QWidget()
        self.media_control_panel_layout = QGridLayout()
        self.media_control_panel_layout.addWidget(self.cms_start_btn, 0, 0, 1, 2)
        self.media_control_panel_layout.addWidget(self.cms_stop_btn, 0, 2, 1, 2)
        self.media_control_panel_layout.addWidget(self.preview_control_btn, 1, 0, 1, 2)
        self.media_control_panel_layout.addWidget(self.sound_control_btn, 1, 2, 1, 2)
        self.media_control_panel.setLayout(self.media_control_panel_layout)

        self.media_crop_panel = QWidget()
        self.media_crop_panel_layout = QGridLayout()
        self.media_crop_panel.setLayout(self.media_crop_panel_layout)
        self.crop_control_widget_init()

        self.video_params_setting_widget = QWidget()
        self.video_params_setting_layout = QGridLayout()
        self.video_params_setting_widget.setLayout(self.video_params_setting_layout)
        self.media_params_panel_widgets_init()


        self.grid_layout = QGridLayout()
        self.grid_layout.addWidget(self.name_label, 0, 0, 1, 4)
        self.grid_layout.addWidget(self.media_control_panel, 1, 0, 1, 10)
        self.grid_layout.addWidget(self.media_crop_panel, 2, 0, 5, 2)
        self.grid_layout.addWidget(self.video_params_setting_widget, 2, 2, 5, 8)
        self.setLayout(self.grid_layout)
        log.debug("CMS Page init_ui end")

    def cms_start_btn_clicked(self):
        log.debug("cms_start_btn_clicked!")
        subprocess.Popen("pkill chromium", shell=True)
        self.launch_chromium()
        time.sleep(5)  # self.launch_chromium()
        self.media_engine.resume_playing()
        self.media_engine.stop_play()
        if self.media_engine.play_cms_worker is None:
            log.debug("Start streaming to led")
            self.media_engine.play_cms(self.chromium_width, self.chromium_height,
                                       self.chromium_pos_x + self.x_padding + 1,
                                       self.chromium_pos_y + self.y_padding)

    def cms_stop_btn_clicked(self):
        log.debug("cms_stop_btn_clicked!")
        try:
            self.media_engine.resume_playing()
            self.media_engine.stop_play()
            subprocess.Popen("pkill chromium", shell=True)
            if self.browser_process is not None:
                os.kill(self.browser_process.pid, signal.SIGTERM)
                self.browser_process = None

        except Exception as e:
            log.error(e)

    def launch_chromium(self):
        try:
            if self.browser_process is not None:
                os.kill(self.browser_process.pid, signal.SIGTERM)
                self.browser_process = None
            open_chromium_cmd = "speedup_chromium.sh &"
            self.browser_process = subprocess.Popen(open_chromium_cmd, shell=True)
            log.debug("self.browser_process.pid = %d", self.browser_process.pid)
        except Exception as e:
            log.error(e)

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

    def crop_control_widget_init(self):
        self.video_crop_x_lineedit = QLineEdit(self.media_crop_panel)
        self.video_crop_y_lineedit = QLineEdit(self.media_crop_panel)
        self.video_crop_w_lineedit = QLineEdit(self.media_crop_panel)
        self.video_crop_h_lineedit = QLineEdit(self.media_crop_panel)

        self.video_crop_x_lineedit.setText(str(self.media_engine.led_video_params.get_media_file_start_x()))
        self.video_crop_y_lineedit.setText(str(self.media_engine.led_video_params.get_media_file_start_y()))
        self.video_crop_w_lineedit.setText(str(self.media_engine.led_video_params.get_media_file_crop_w()))
        self.video_crop_h_lineedit.setText(str(self.media_engine.led_video_params.get_media_file_crop_h()))

        edits = [self.video_crop_x_lineedit, self.video_crop_y_lineedit, self.video_crop_w_lineedit,
                 self.video_crop_h_lineedit]

        labels = ["Crop Start X:", "Crop Start Y:", "Crop Width:", "Crop Height:"]
        for i, label in enumerate(labels):
            lbl = QLabel(label, self.media_crop_panel)
            lbl.setFont(QFont(QFont_Style_Default, QFont_Style_Size_M))
            edit = edits[i]
            edit.setFixedWidth(100)
            edit.setFont(QFont(QFont_Style_Default, QFont_Style_Size_M))
            self.media_crop_panel_layout.addWidget(lbl, i, 0)
            self.media_crop_panel_layout.addWidget(edit, i, 1)

        self.media_adj_crop_btn = QPushButton("Adjust Crop Parameter", self.media_crop_panel)
        self.media_adj_crop_btn.setFont(QFont(QFont_Style_Default, QFont_Style_Size_M))
        self.media_adj_crop_btn.clicked.connect(self.adj_media_ctrl_param)
        self.media_crop_panel_layout.addWidget(self.media_adj_crop_btn, len(labels), 0, 1, 2)


    def media_params_panel_widgets_init(self):
        ''' Brightness Setting '''
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
        # self.video_params_setting_layout.addWidget(self.media_adj_crop_btn, 4, 0, 1, 2)

    def adj_media_ctrl_param(self):
        self.media_engine.led_video_params.set_media_file_crop_w(int(self.video_crop_w_lineedit.text()))
        self.media_engine.led_video_params.set_media_file_crop_h(int(self.video_crop_h_lineedit.text()))
        self.media_engine.led_video_params.set_media_file_start_x(int(self.video_crop_x_lineedit.text()))
        self.media_engine.led_video_params.set_media_file_start_y(int(self.video_crop_y_lineedit.text()))

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