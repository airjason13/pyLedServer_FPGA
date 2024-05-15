import os
import sys

from PyQt5.QtCore import QObject, pyqtSignal

from ext_qt_widgets.system_file_watcher import FileWatcher
from global_def import log, frame_brightness_alog


class VideoParams(QObject):
    signal_video_params_changed = pyqtSignal()
    signal_fpga_current_gain_changed = pyqtSignal()
    signal_fpga_gamma_index_changed = pyqtSignal()
    signal_output_res_fps_changed = pyqtSignal()

    def __init__(self, from_config, led_brightness, led_gamma, led_r_gain, led_g_gain, led_b_gain, **kwargs):
        super(VideoParams, self).__init__(**kwargs)

        root_dir = os.path.dirname(sys.modules['__main__'].__file__)
        led_config_dir = os.path.join(root_dir, 'led_config')
        self.video_params_file_uri = os.path.join(led_config_dir, "led_parameters")

        self.configs_file_watcher = FileWatcher([self.video_params_file_uri])
        self.configs_file_watcher.install_file_changed_slot(self.sync_video_param_from_file_watcher)

        if from_config is True:
            self.parse_init_config()
        else:
            self.led_brightness = led_brightness
            self.led_gamma = led_gamma
            self.icled_type = 0
            self.led_r_gain = led_r_gain
            self.led_g_gain = led_g_gain
            self.led_b_gain = led_b_gain
            self.frame_brightness_algorithm = frame_brightness_alog.fix_mode
            self.sleep_mode_enable = 0
            self.target_city_index = 0
            self.day_mode_frame_brightness = 0
            self.night_mode_frame_brightness = 0
            self.sleep_mode_frame_brightness = 0
            self.image_period = 6000
            self.media_file_start_y = 0
            self.media_file_start_x = 0
            self.media_file_crop_h = 0
            self.media_file_crop_w = 0
            self.hdmi_in_start_y = 0
            self.hdmi_in_start_x = 0
            self.hdmi_in_crop_h = 0
            self.hdmi_in_crop_w = 0
            self.output_frame_width = 640
            self.output_frame_height = 480
            self.output_fps = 24
            self.sync_video_param()

    def install_video_params_changed_slot(self, slot):
        self.signal_video_params_changed.connect(slot)

    def install_fpga_current_gain_changed_slot(self, slot):
        self.signal_fpga_current_gain_changed.connect(slot)

    def install_fpga_gamma_index_changed_slot(self, slot):
        self.signal_fpga_gamma_index_changed.connect(slot)

    def init_video_param_file(self):
        content_lines = [
            "led_brightness=50\n",
            "icled_type=0\n"
            "led_gamma=2.2\n",
            "led_r_gain=1\n",
            "led_b_gain=1\n",
            "led_g_gain=1\n",
            "sleep_mode_enable=1\n",
            "target_city_index=0\n",
            "frame_brightness_algorithm=0\n",
            "day_mode_frame_brightness=50\n",
            "night_mode_frame_brightness=30\n",
            "sleep_mode_frame_brightness=0\n",
            "image_period=6000\n",
            "hdmi_in_start_x=0\n",
            "hdmi_in_start_y=0\n",
            "hdmi_in_crop_w=0\n",
            "hdmi_in_crop_h=0\n",
            "media_file_start_x=0\n",
            "media_file_start_y=0\n",
            "media_file_crop_w=0\n",
            "media_file_crop_h=0\n",
            "output_frame_width=640\n",
            "output_frame_height=480\n",
            "output_fps=24\n",
        ]
        config_file = open(self.video_params_file_uri, 'w')
        config_file.writelines(content_lines)
        config_file.close()
        os.system('sync')

    def parse_init_config(self):
        if os.path.exists(self.video_params_file_uri) is False:
            log.debug("video_params config file_uri does not exist")
            self.init_video_param_file()
        else:
            ''' Check file content is ok or not '''
            b_ret = self.check_video_param_file_valid()
            if b_ret is False:
                self.init_video_param_file()
            else:
                pass

        config_file = open(self.video_params_file_uri, 'r')
        content_lines = config_file.readlines()

        for line in content_lines:
            tmp = line.split("=")
            if tmp[0] == "led_brightness":
                self.led_brightness = int(tmp[1])
            elif tmp[0] == "led_gamma":
                self.led_gamma = float(tmp[1])
            elif tmp[0] == "icled_type":
                self.icled_type = float(tmp[1])
            elif tmp[0] == "led_r_gain":
                self.led_r_gain = int(tmp[1])
            elif tmp[0] == "led_g_gain":
                self.led_g_gain = int(tmp[1])
            elif tmp[0] == "led_b_gain":
                self.led_b_gain = int(tmp[1])
            elif tmp[0] == "frame_brightness_algorithm":
                self.frame_brightness_algorithm = int(tmp[1])
            elif tmp[0] == "sleep_mode_enable":
                self.sleep_mode_enable = int(tmp[1])
            elif tmp[0] == "target_city_index":
                self.target_city_index = int(tmp[1])
            elif tmp[0] == "day_mode_frame_brightness":
                self.day_mode_frame_brightness = int(tmp[1])
            elif tmp[0] == "night_mode_frame_brightness":
                self.night_mode_frame_brightness = int(tmp[1])
            elif tmp[0] == "sleep_mode_frame_brightness":
                self.sleep_mode_frame_brightness = int(tmp[1])
            elif tmp[0] == "image_period":
                self.image_period = int(tmp[1])
            elif tmp[0] == "hdmi_in_crop_w":
                self.hdmi_in_crop_w = int(tmp[1])
            elif tmp[0] == "hdmi_in_crop_h":
                self.hdmi_in_crop_h = int(tmp[1])
            elif tmp[0] == "hdmi_in_start_x":
                self.hdmi_in_start_x = int(tmp[1])
            elif tmp[0] == "hdmi_in_start_y":
                self.hdmi_in_start_y = int(tmp[1])
            elif tmp[0] == "media_file_crop_w":
                self.media_file_crop_w = int(tmp[1])
            elif tmp[0] == "media_file_crop_h":
                self.media_file_crop_h = int(tmp[1])
            elif tmp[0] == "media_file_start_x":
                self.media_file_start_x = int(tmp[1])
            elif tmp[0] == "media_file_start_y":
                self.media_file_start_y = int(tmp[1])
            elif tmp[0] == "output_frame_width":
                self.output_frame_width = int(tmp[1])
            elif tmp[0] == "output_frame_height":
                self.output_frame_height = int(tmp[1])
            elif tmp[0] == "output_fps":
                self.output_fps = int(tmp[1])


    def check_video_param_file_valid(self):
        ''' Not Implemented yet'''
        return True

    def sync_video_param_from_file_watcher(self):
        log.debug("")
        self.parse_init_config()
        self.signal_video_params_changed.emit()

    def sync_video_param(self):
        params_led_brightness = "led_brightness=" + str(self.led_brightness) + '\n'
        params_led_gamma = 'led_gamma=' + str(self.led_gamma) + '\n'
        params_led_type = 'icled_type=' + str(self.icled_type) + '\n'
        params_red_gain = 'led_r_gain=' + str(self.led_r_gain) + '\n'
        params_green_gain = "led_g_gain=" + str(self.led_g_gain) + '\n'
        params_blue_gain = 'led_b_gain=' + str(self.led_b_gain) + '\n'
        sleep_mode_enable = 'sleep_mode_enable=' + str(self.sleep_mode_enable) + '\n'
        target_city_index = 'target_city_index=' + str(self.target_city_index) + '\n'
        frame_brightness_algorithm = 'frame_brightness_algorithm=' + str(self.frame_brightness_algorithm) + '\n'
        day_mode_frame_brightness = 'day_mode_frame_brightness=' + str(self.day_mode_frame_brightness) + '\n'
        night_mode_frame_brightness = 'night_mode_frame_brightness=' + str(self.night_mode_frame_brightness) + '\n'
        sleep_mode_frame_brightness = 'sleep_mode_frame_brightness=' + str(self.sleep_mode_frame_brightness) + '\n'
        image_period = 'image_period=' + str(self.image_period) + '\n'
        params_hdmi_in_start_x = 'hdmi_in_start_x=' + str(self.hdmi_in_start_x) + '\n'
        params_hdmi_in_start_y = "hdmi_in_start_y=" + str(self.hdmi_in_start_y) + '\n'
        params_hdmi_in_crop_w = 'hdmi_in_crop_w=' + str(self.hdmi_in_crop_w) + '\n'
        params_hdmi_in_crop_h = 'hdmi_in_crop_h=' + str(self.hdmi_in_crop_h) + '\n'
        params_media_file_start_x = "media_file_start_x=" + str(self.media_file_start_x) + '\n'
        params_media_file_start_y = 'media_file_start_y=' + str(self.media_file_start_y) + '\n'
        params_media_file_crop_w = 'media_file_crop_w=' + str(self.media_file_crop_w) + '\n'
        params_media_file_crop_h = 'media_file_crop_h=' + str(self.media_file_crop_h) + '\n'
        params_output_frame_width = 'output_frame_width=' + str(self.output_frame_width) + '\n'
        params_output_frame_height = 'output_frame_height=' + str(self.output_frame_height) + '\n'
        params_output_fps = 'output_fps=' + str(self.output_fps) + '\n'
        content_lines = [
            params_led_brightness,
            params_led_gamma,
            params_led_type,
            params_red_gain,
            params_green_gain,
            params_blue_gain,
            sleep_mode_enable,
            target_city_index,
            frame_brightness_algorithm,
            day_mode_frame_brightness,
            night_mode_frame_brightness,
            sleep_mode_frame_brightness,
            image_period,
            params_hdmi_in_start_x,
            params_hdmi_in_start_y,
            params_hdmi_in_crop_w,
            params_hdmi_in_crop_h,
            params_media_file_start_x,
            params_media_file_start_y,
            params_media_file_crop_w,
            params_media_file_crop_h,
            params_output_frame_width,
            params_output_frame_height,
            params_output_fps,
        ]

        log.debug("content_lines :%s", content_lines)
        file_uri = self.video_params_file_uri  # internal_media_folder + init_config_file
        config_file = open(file_uri, 'w')
        config_file.writelines(content_lines)
        config_file.close()
        os.system('sync')

    def set_led_brightness(self, br_level):
        if self.led_brightness != br_level:
            self.led_brightness = br_level
            self.sync_video_param()

    def get_led_brightness(self):
        return self.led_brightness

    def set_led_gamma(self, gamma_value):
        if self.led_gamma != gamma_value:
            self.led_gamma = gamma_value
            self.sync_video_param()
            self.signal_fpga_gamma_index_changed.emit()

    def get_led_gamma(self):
        return self.led_gamma

    def set_icled_type(self, type):
        if self.icled_type != type:
            self.icled_type = type
            self.sync_video_param()

    def get_icled_type(self):
        return self.icled_type

    def set_led_red_gain(self, r_gain):
        if self.led_r_gain != r_gain:
            self.led_r_gain = r_gain
            self.sync_video_param()
            self.signal_fpga_current_gain_changed.emit()

    def get_led_red_gain(self):
        return self.led_r_gain

    def set_led_green_gain(self, g_gain):
        if self.led_g_gain != g_gain:
            self.led_g_gain = g_gain
            self.sync_video_param()
            self.signal_fpga_current_gain_changed.emit()

    def get_led_green_gain(self):
        return self.led_g_gain

    def set_led_blue_gain(self, b_gain):
        if self.led_b_gain != b_gain:
            self.led_b_gain = b_gain
            self.sync_video_param()
            self.signal_fpga_current_gain_changed.emit()

    def get_led_blue_gain(self):
        return self.led_b_gain

    def set_target_city_index(self, city_index):
        if self.target_city_index != city_index:
            self.target_city_index = city_index
            self.sync_video_param()

    def get_target_city_index(self):
        return self.target_city_index

    def set_frame_brightness_algo(self, algo: int):
        if self.frame_brightness_algorithm != algo:
            self.frame_brightness_algorithm = algo
            self.sync_video_param()

    def get_frame_brightness_algo(self):
        return self.frame_brightness_algorithm

    def set_sleep_mode_enable(self, status: int):
        if self.sleep_mode_enable != status:
            self.sleep_mode_enable = status
            self.sync_video_param()

    def get_sleep_mode_enable(self):
        return self.sleep_mode_enable

    def set_day_mode_frame_brightness(self, val: int):
        if self.day_mode_frame_brightness != val:
            self.day_mode_frame_brightness = val
            self.sync_video_param()

    def get_day_mode_frame_brightness(self):
        return self.day_mode_frame_brightness

    def set_night_mode_frame_brightness(self, val: int):
        if self.night_mode_frame_brightness != val:
            self.night_mode_frame_brightness = val
            self.sync_video_param()

    def get_night_mode_frame_brightness(self):
        return self.night_mode_frame_brightness

    def set_sleep_mode_frame_brightness(self, val: int):
        if self.sleep_mode_frame_brightness != val:
            self.sleep_mode_frame_brightness = val
            self.sync_video_param()

    def get_sleep_mode_frame_brightness(self):
        return self.sleep_mode_frame_brightness

    def set_hdmi_in_start_y(self, start_y):
        if self.hdmi_in_start_y != start_y:
            self.hdmi_in_start_y = start_y
            self.sync_video_param()

    def get_hdmi_in_start_y(self):
        return self.hdmi_in_start_y

    def set_hdmi_in_start_x(self, start_x):
        if self.hdmi_in_start_x != start_x:
            self.hdmi_in_start_x = start_x
            self.sync_video_param()

    def get_hdmi_in_start_x(self):
        return self.hdmi_in_start_x

    def set_hdmi_in_crop_h(self, crop_h):
        if self.hdmi_in_crop_h != crop_h:
            self.hdmi_in_crop_h = crop_h
            self.sync_video_param()

    def get_hdmi_in_crop_h(self):
        return self.hdmi_in_crop_h

    def set_hdmi_in_crop_w(self, crop_w):
        if self.hdmi_in_crop_w != crop_w:
            self.hdmi_in_crop_w = crop_w
            self.sync_video_param()

    def get_hdmi_in_crop_w(self):
        return self.hdmi_in_crop_w

    def set_media_file_start_y(self, start_y):
        self.media_file_start_y = start_y

    def get_media_file_start_y(self):
        return self.media_file_start_y

    def set_media_file_start_x(self, start_x):
        if self.media_file_start_x != start_x:
            self.media_file_start_x = start_x
            self.sync_video_param()

    def get_media_file_start_x(self):
        return self.media_file_start_x

    def set_media_file_crop_h(self, crop_h):
        if self.media_file_crop_h != crop_h:
            self.media_file_crop_h = crop_h
            self.sync_video_param()

    def get_media_file_crop_h(self):
        return self.media_file_crop_h

    def set_media_file_crop_w(self, crop_w):
        if self.media_file_crop_w != crop_w:
            self.media_file_crop_w = crop_w
            self.sync_video_param()

    def get_media_file_crop_w(self):
        return self.media_file_crop_w

    def set_output_frame_width(self, width):
        if self.output_frame_width != width:
            self.output_frame_width = width
            self.sync_video_param()

    def get_output_frame_width(self):
        return self.output_frame_width

    def set_output_frame_height(self, height):
        if self.output_frame_height != height:
            self.output_frame_height = height
            self.sync_video_param()

    def get_output_frame_height(self):
        log.debug("self.output_frame_height : %d", self.output_frame_height)
        return self.output_frame_height

    def get_output_frame_res(self):
        return self.output_frame_width, self.output_frame_height

    def get_output_frame_res_str(self):
        return str(self.output_frame_width), str(self.output_frame_height)

    def set_output_fps(self, fps):
        if self.output_fps != fps:
            self.output_fps = fps
            self.sync_video_param()

    def get_output_fps(self):
        return self.output_fps

