import os
import sys

from PyQt5.QtCore import QObject

from ext_qt_widgets.system_file_watcher import FileWatcher
from global_def import log


class VideoParams(QObject):

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

    def init_video_param_file(self):
        content_lines = [
            "led_brightness=50\n", "led_gamma=2.2\n",
            "led_r_gain=15\n", "led_g_gain=15\n", "led_b_gain=15\n"
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

    def check_video_param_file_valid(self):
        ''' Not Implemented yet'''
        return True

    def sync_video_param_from_file_watcher(self):
        log.debug("")
        self.parse_init_config()
