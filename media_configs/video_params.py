import os
import sys

from PyQt5.QtCore import QObject, pyqtSignal

from ext_qt_widgets.system_file_watcher import FileWatcher
from global_def import log


class VideoParams(QObject):
    signal_video_params_changed = pyqtSignal()

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
            self.led_r_gain = led_r_gain
            self.led_g_gain = led_g_gain
            self.led_b_gain = led_b_gain
            self.media_file_start_y = 0
            self.media_file_start_x = 0
            self.media_file_crop_h = 0
            self.media_file_crop_w = 0
            self.hdmi_in_start_y = 0
            self.hdmi_in_start_x = 0
            self.hdmi_in_crop_h = 0
            self.hdmi_in_crop_w = 0

    def install_video_params_changed_slot(self, slot):
        self.signal_video_params_changed.connect(slot)

    def init_video_param_file(self):
        content_lines = [
            "led_brightness=50\n", "led_gamma=2.2\n",
            "led_r_gain=15\n", "led_g_gain=15\n", "led_b_gain=15\n",
            "hdmi_in_crop_w=0\n", "hdmi_in_crop_h=0\n",
            "hdmi_in_start_x=0\n", "hdmi_in_start_y=0\n",
            "media_file_crop_w=0\n", "media_file_crop_h=0\n",
            "media_file_start_x=0\n", "media_file_start_y=0\n"
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
            elif tmp[0] == "led_r_gain":
                self.led_r_gain = int(tmp[1])
            elif tmp[0] == "led_g_gain":
                self.led_g_gain = int(tmp[1])
            elif tmp[0] == "led_b_gain":
                self.led_b_gain = int(tmp[1])
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

    def check_video_param_file_valid(self):
        ''' Not Implemented yet'''
        return True

    def sync_video_param_from_file_watcher(self):
        log.debug("")
        self.parse_init_config()
        self.signal_video_params_changed.emit()

    def sync_video_param(self):
        params_brightness = "led_brightness=" + str(self.led_brightness) + '\n'
        params_gamma = 'led_gamma=' + str(self.led_gamma) + '\n'
        params_red_gain = 'led_r_gain=' + str(self.led_r_gain) + '\n'
        params_green_gain = "led_g_gain=" + str(self.led_g_gain) + '\n'
        params_blue_gain = 'led_b_gain=' + str(self.led_b_gain) + '\n'
        params_hdmi_in_start_x = 'hdmi_in_start_x=' + str(self.hdmi_in_start_x) + '\n'
        params_hdmi_in_start_y = "hdmi_in_start_y=" + str(self.hdmi_in_start_y) + '\n'
        params_hdmi_in_crop_w = 'hdmi_in_crop_w=' + str(self.hdmi_in_crop_w) + '\n'
        params_hdmi_in_crop_h = 'hdmi_in_crop_h=' + str(self.hdmi_in_crop_h) + '\n'
        params_media_file_start_x = "media_file_start_x=" + str(self.media_file_start_x) + '\n'
        params_media_file_start_y = 'media_file_start_y=' + str(self.media_file_start_y) + '\n'
        params_media_file_crop_w = 'media_file_crop_w=' + str(self.media_file_crop_w) + '\n'
        params_media_file_crop_h = 'media_file_crop_h=' + str(self.media_file_crop_h) + '\n'
        content_lines = [params_brightness, params_gamma, params_red_gain, params_green_gain,
                         params_blue_gain, params_hdmi_in_start_x, params_hdmi_in_start_y, params_hdmi_in_crop_w,
                         params_hdmi_in_crop_h, params_media_file_start_x, params_media_file_start_y,
                         params_media_file_crop_w, params_media_file_crop_h
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

    def get_led_gamma(self):
        return self.led_gamma

    def set_led_red_gain(self, r_gain):
        self.led_r_gain = r_gain

    def get_led_red_gain(self):
        return self.led_r_gain

    def set_led_green_gain(self, g_gain):
        self.led_g_gain = g_gain

    def get_led_green_gain(self):
        return self.led_g_gain

    def set_led_blue_gain(self, b_gain):
        self.led_b_gain = b_gain

    def get_led_blue_gain(self):
        return self.led_b_gain

    def set_hdmi_in_start_y(self, start_y):
        self.hdmi_in_start_y = start_y

    def get_hdmi_in_start_y(self):
        return self.hdmi_in_start_y

    def set_hdmi_in_start_x(self, start_x):
        self.hdmi_in_start_x = start_x

    def get_hdmi_in_start_x(self):
        return self.hdmi_in_start_x

    def set_hdmi_in_crop_h(self, crop_h):
        self.hdmi_in_crop_h = crop_h

    def get_hdmi_in_crop_h(self):
        return self.hdmi_in_crop_h

    def set_hdmi_in_crop_w(self, crop_w):
        self.hdmi_in_crop_w = crop_w

    def get_hdmi_in_crop_w(self):
        return self.hdmi_in_crop_w

    def set_media_file_start_y(self, start_y):
        self.media_file_start_y = start_y

    def get_media_file_start_y(self):
        return self.media_file_start_y

    def set_media_file_start_x(self, start_x):
        self.media_file_start_x = start_x

    def get_media_file_start_x(self):
        return self.media_file_start_x

    def set_media_file_crop_h(self, crop_h):
        self.media_file_crop_h = crop_h

    def get_media_file_crop_h(self):
        return self.media_file_crop_h

    def set_media_file_crop_w(self, crop_w):
        self.media_file_crop_w = crop_w

    def get_media_file_crop_w(self):
        return self.media_file_crop_w




