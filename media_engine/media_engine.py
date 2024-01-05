import enum
import os
import signal
import subprocess
import time

import numpy as np
from PyQt5.QtCore import QObject, pyqtSignal, QMutex, QThread

from ext_qt_widgets.playing_preview_widget import PlayingPreviewWindow
from media_engine.media_engine_def import PlayStatus, RepeatOption
from utils.utils_ffmpy import get_ffmpeg_cmd_with_playing_media_file_
from utils.utils_file_access import get_led_config_from_file_uri, get_int_led_config_from_file_uri
from media_configs.video_params import VideoParams
from global_def import log


class MediaEngine(QObject):
    signal_media_play_status_changed = pyqtSignal(bool, str)

    def __init__(self):
        super(MediaEngine, self).__init__()
        log.debug("")
        self.output_streaming_width, self.output_streaming_height = (
            get_int_led_config_from_file_uri("led_wall_resolution", "led_wall_width", "led_wall_height"))
        self.led_video_params = VideoParams(True, 50, 2.2,
                                            15, 15, 15)
        self.playing_status = PlayStatus.Stop
        self.pre_playing_status = PlayStatus.Initial
        self.repeat_option = RepeatOption.Repeat_All
        self.ff_process = None

        self.playing_preview_window = PlayingPreviewWindow()

        self.play_single_file_thread = None
        self.play_single_file_worker = None

    def install_signal_media_play_status_changed_slot(self, slot_func):
        self.signal_media_play_status_changed.connect(slot_func)

    def set_output_streaming_resolution(self, w: int, h: int):
        self.output_streaming_width = w
        self.output_streaming_height = h

    def sync_output_streaming_resolution(self):
        self.output_streaming_width, self.output_streaming_height = (
            get_led_config_from_file_uri("led_wall_resolution", "led_wall_width", "led_wall_height"))

    def play_status_changed(self, status: int, playing_src: str):
        log.debug("playing_src : %s", playing_src)
        self.playing_status = status
        if self.playing_status == PlayStatus.Stop:
            self.playing_preview_window.setVisible(False)
        self.signal_media_play_status_changed.emit(status, playing_src)

    def preview_pixmap_changed(self, raw_image_np_array):
        # log.debug("preview_pixmap_changed")
        if raw_image_np_array is None:
            log.error("raw_image_np_array is None")
            return
        if self.playing_preview_window.isVisible() is False:
            self.playing_preview_window.setVisible(True)
        self.playing_preview_window.refresh_image(raw_image_np_array)

    def single_play(self, file_uri):
        log.debug("single play file uri: %s", file_uri)
        self.play_single_file_thread = QThread()
        self.play_single_file_worker = PlaySingleFileWorker(self, file_uri, with_audio=True, with_preview=True)
        self.play_single_file_worker.install_play_status_slot(self.play_status_changed)
        self.play_single_file_worker.install_pixmap_refreshed_slot(self.preview_pixmap_changed)

        self.play_single_file_worker.moveToThread(self.play_single_file_thread)
        self.play_single_file_thread.started.connect(self.play_single_file_worker.run)
        self.play_single_file_worker.pysignal_single_file_play_finished.connect(self.play_single_file_thread.quit)
        self.play_single_file_worker.pysignal_single_file_play_finished.connect(
            self.play_single_file_worker.deleteLater)
        self.play_single_file_thread.finished.connect(self.play_single_file_thread.deleteLater)
        self.play_single_file_thread.start()

    def stop_play(self):
        if self.play_single_file_worker is not None:
            self.play_single_file_worker.stop()
            if self.ff_process is not None:
                os.kill(self.ff_process.pid, signal.SIGTERM)
            try:
                if self.play_single_file_thread is not None:
                    self.play_single_file_thread.quit()
                for i in range(10):
                    log.debug("self.play_single_file_thread.isFinished() = %d",
                              self.play_single_file_thread.isFinished())
                    if self.play_single_file_thread.isFinished() is True:
                        break
                    time.sleep(1)

                log.debug("single_file_worker is not None A2")
                self.play_single_file_thread.wait()
                self.play_single_file_thread.exit(0)
            except Exception as e:
                log.debug(e)
            self.play_single_file_worker = None
            self.play_single_file_thread = None


class PlaySingleFileWorker(QObject):
    pysignal_single_file_play_status_change = pyqtSignal(int, str)
    pysignal_single_file_play_finished = pyqtSignal()
    pysignal_refresh_image_pixmap = pyqtSignal(np.ndarray)

    def __init__(self, media_engine: MediaEngine, file_uri, with_audio: bool, with_preview: bool):
        super().__init__()
        self.media_engine = media_engine
        self.file_uri = file_uri
        self.play_with_audio = with_audio
        self.play_with_preview = with_preview
        self.video_params = self.media_engine.led_video_params
        self.force_stop = False
        self.worker_status = 0
        self.force_stop_mutex = QMutex()
        self.play_status = None
        self.play_status_change(PlayStatus.Initial, self.file_uri)
        self.ff_process = self.media_engine.ff_process
        self.output_width = self.media_engine.output_streaming_width
        self.output_height = self.media_engine.output_streaming_height
        self.playing_source = None
        self.image_from_pipe = None
        self.raw_image = None
        self.preview_window = None

    def install_play_status_slot(self, slot_func):
        self.pysignal_single_file_play_status_change.connect(slot_func)

    def install_pixmap_refreshed_slot(self, slot_func):
        self.pysignal_refresh_image_pixmap.connect(slot_func)

    def play_status_change(self, status: int, src: str):
        self.play_status = status
        self.playing_source = src
        log.debug("self.playing_source : %s", self.playing_source)
        self.pysignal_single_file_play_status_change.emit(self.play_status, self.playing_source)

    def run(self):
        while True:
            self.worker_status = 1
            if self.play_status != PlayStatus.Stop:
                try:
                    ''' 如果 ffprocess 存在'''
                    if self.ff_process is not None:
                        '''但是是暫停狀態, 則繼續播放?'''
                        if self.play_status == PlayStatus.Pausing:
                            os.kill(self.ff_process.pid, signal.SIGCONT)
                        else:
                            os.kill(self.ff_process.pid, signal.SIGTERM)
                except Exception as e:
                    log.error(e)
            ffmpeg_cmd = get_ffmpeg_cmd_with_playing_media_file_(self.file_uri,
                                                                 width=self.output_width, height=self.output_height,
                                                                 target_fps="24/1", image_period=20)
            log.debug("ffmpeg_cmd : %s", ffmpeg_cmd)
            self.ff_process = subprocess.Popen(ffmpeg_cmd, stdout=subprocess.PIPE, bufsize=10 ** 8, shell=True)
            if self.ff_process.pid > 0:
                self.play_status_change(PlayStatus.Playing, self.file_uri)
                while True:
                    self.image_from_pipe = self.ff_process.stdout.read(self.output_width * self.output_height * 3)
                    if self.play_with_preview:
                        try:
                            self.raw_image = np.frombuffer(self.image_from_pipe, dtype='uint8')
                            self.raw_image = self.raw_image.reshape((self.output_height, self.output_width, 3))
                            self.ff_process.stdout.flush()
                            self.pysignal_refresh_image_pixmap.emit(self.raw_image)
                        except Exception as e:
                            log.debug(e)
                            break
                    if self.force_stop is True:
                        log.debug("self.force_stop is True, ready to kill ff_process")
                        if self.ff_process is not None:
                            os.kill(self.ff_process.pid, signal.SIGTERM)
                        break
                    '''try:
                        res, err = self.ff_process.communicate()
                        log.debug("%s %s", res, err)
                        os.kill(self.ff_process.pid, 0)
                    except OSError:
                        log.debug("no such process, play end")
                        break
                    else:
                        log.debug("ff_process is still running")
                        pass'''
            if self.media_engine.repeat_option == RepeatOption.Repeat_None:
                log.debug("stop play cause play end")
                break
            if self.force_stop is True:
                break
        self.play_status_change(PlayStatus.Stop, "")
        self.worker_status = 0
        self.pysignal_single_file_play_finished.emit()
        self.ff_process = None
        log.debug("single play worker finished")

    def stop(self):
        self.force_stop = True

    def get_worker_status(self):
        return self.worker_status


def test(self):
    log.debug("")
