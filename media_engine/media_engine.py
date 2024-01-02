import enum

from PyQt5.QtCore import QObject, pyqtSignal

from media_engine.media_engine_def import PlayStatus, RepeatOption
from utils.utils_file_access import get_led_config_from_file_uri
from media_configs.video_params import VideoParams
from global_def import log


class MediaEngine(QObject):
    signal_media_play_status_changed = pyqtSignal(bool, int)

    def __init__(self):
        super(MediaEngine, self).__init__()
        log.debug("")
        self.output_streaming_width, self.output_streaming_height = (
            get_led_config_from_file_uri("led_wall_resolution","led_wall_width", "led_wall_height"))
        self.led_video_params = VideoParams(True, 50, 2.2,
                                            15, 15, 15)
        self.playing_status = PlayStatus.Stop
        self.pre_playing_status = PlayStatus.Initial
        self.repeat_option = RepeatOption.Repeat_All



    def set_output_streaming_resolution(self, w, h):
        self.output_streaming_width = w
        self.output_streaming_height = h

    def sync_output_streaming_resolution(self):
        self.output_streaming_width, self.output_streaming_height = (
            get_led_config_from_file_uri("led_wall_resolution", "led_wall_width", "led_wall_height"))

    def test(self):
        log.debug("")

