import enum
import os
import platform
import re
import signal
import subprocess
import time
import atexit
import select
from threading import Timer
from time import sleep

import numpy as np
import psutil
from PyQt5.QtCore import QObject, pyqtSignal, QMutex, QThread, pyqtSlot

import utils.utils_file_access
from ext_dev.tc358743 import TC358743
from ext_qt_widgets.playing_preview_widget import PlayingPreviewWindow
from media_engine.media_engine_def import PlayStatus, RepeatOption
from media_engine.sound_device import SoundDevices, mute_audio_sinks
from utils.utils_ffmpy import get_ffmpeg_cmd_for_media
from utils.utils_gst_pipeline import get_gstreamer_cmd_for_media, gstreamer_image_period_event
from utils.utils_file_access import get_file_list_in_playlist
from utils.utils_system import get_eth_interface
from media_configs.video_params import VideoParams
from global_def import log, root_dir, ETH_DEV, SU_PWD
import socket
from multiprocessing import shared_memory
from ctypes import *
from media_engine.linux_ipc_pyapi_sem import *
import gi
gi.require_version('Gst', '1.0')
gi.require_version('GstPbutils', '1.0')
from gi.repository import Gst,GstPbutils

# Initialize GStreamer
Gst.init(None)

class MediaEngine(QObject):
    signal_media_play_status_changed = pyqtSignal(int, str)
    hdmi_play_status_changed = pyqtSignal(int, str)
    cms_play_status_changed = pyqtSignal(int, str)
    signal_media_engine_status_changed = pyqtSignal(int, str)

    def __init__(self):
        super(MediaEngine, self).__init__()
        self.video_backend = VIDEO_BACKEND
        self.media_active_height = None
        self.media_active_width = None
        self.ffprobe_process = None
        self.ff_process = None
        self.gst_pipeline = None
        self.hdmi_sound = None
        self.headphone_sound = None
        self.pulse_audio_status = None
        self.output_streaming_fps = None
        self.output_streaming_height = None
        self.output_streaming_width = None
        self.play_single_file_thread = None
        self.play_single_file_worker = None
        self.play_playlist_thread = None
        self.play_playlist_worker = None
        self.play_hdmi_in_thread = None
        self.play_hdmi_in_worker = None
        self.play_cms_thread = None
        self.play_cms_worker = None


        log.debug("")

        self.led_video_params = VideoParams(True, 50, 2.2,
                                            15, 15, 15)
        self.led_video_params.install_video_params_changed_slot(self.video_params_changed)
        self.sync_output_streaming_resolution()
        self.playing_status = PlayStatus.Stop
        self.pre_playing_status = PlayStatus.Initial
        self.repeat_option = RepeatOption.Repeat_All

        self.play_change_mutex = QMutex()
        self.playing_preview_window = PlayingPreviewWindow(self.led_video_params.get_output_frame_width(),
                                                           self.led_video_params.get_output_frame_height())

        self.shm_sem_write_uri = "/shm_write_sem"
        self.shm_sem_read_uri = "/shm_read_sem"

        os.system("pkill -9 -f show_ffmpeg_shared_memory")

        self.image_period = self.led_video_params.get_still_image_period()
        self.media_file_start_y = self.led_video_params.get_media_file_start_x()
        self.media_file_start_x = self.led_video_params.get_media_file_start_y()
        self.media_file_crop_h = self.led_video_params.get_media_file_crop_h()
        self.media_file_crop_w = self.led_video_params.get_media_file_crop_w()
        self.hdmi_in_start_y = self.led_video_params.get_hdmi_in_start_x()
        self.hdmi_in_start_x = self.led_video_params.get_hdmi_in_start_y()
        self.hdmi_in_crop_h = self.led_video_params.get_hdmi_in_crop_h()
        self.hdmi_in_crop_w = self.led_video_params.get_hdmi_in_crop_w()
        self.preview_status = self.led_video_params.get_play_with_preview()
        self.audio_play_status = self.led_video_params.get_play_with_audio()

        self.sound_device = SoundDevices()
        self.pulse_audio_status = self.sound_device.pulse_audio_status()
        if not self.pulse_audio_status:
            self.pulse_audio_status = self.sound_device.start_pulse_audio()
        self.hdmi_sound = self.sound_device.capture_hdmi_rcv_devices()
        self.headphone_sound = self.sound_device.capture_Headphones_devices()

    def video_params_changed(self):
        need_restart_streaming = False
        if self.output_streaming_fps != self.led_video_params.get_output_fps():
            self.output_streaming_fps = self.led_video_params.get_output_fps()
            need_restart_streaming = True
        if self.output_streaming_width != self.led_video_params.get_output_frame_width():
            self.output_streaming_width = self.led_video_params.get_output_frame_width()
            need_restart_streaming = True
        if self.output_streaming_height != self.led_video_params.get_output_frame_height():
            self.output_streaming_height = self.led_video_params.get_output_frame_height()
            need_restart_streaming = True

        if self.image_period != self.led_video_params.get_still_image_period():
            self.led_video_params = self.led_video_params.get_still_image_period()
            need_restart_streaming = True

        if self.media_file_crop_w != self.led_video_params.get_media_file_crop_w():
            self.media_file_crop_w = self.led_video_params.get_media_file_crop_w()
            need_restart_streaming = True

        if self.media_file_crop_h != self.led_video_params.get_media_file_crop_h():
            self.media_file_crop_h = self.led_video_params.get_media_file_crop_h()
            need_restart_streaming = True

        if self.media_file_start_x != self.led_video_params.get_media_file_start_x():
            self.media_file_start_x = self.led_video_params.get_media_file_start_x()
            need_restart_streaming = True

        if self.media_file_start_y != self.led_video_params.get_media_file_start_y():
            self.media_file_start_y = self.led_video_params.get_media_file_start_y()
            need_restart_streaming = True

        if self.hdmi_in_crop_w != self.led_video_params.get_hdmi_in_crop_w():
            self.hdmi_in_crop_w = self.led_video_params.get_hdmi_in_crop_w()
            need_restart_streaming = True

        if self.hdmi_in_crop_h != self.led_video_params.get_hdmi_in_crop_h():
            self.hdmi_in_crop_h = self.led_video_params.get_hdmi_in_crop_h()
            need_restart_streaming = True

        if self.hdmi_in_start_x != self.led_video_params.get_hdmi_in_start_x():
            self.hdmi_in_start_x = self.led_video_params.get_hdmi_in_start_x()
            need_restart_streaming = True

        if self.hdmi_in_start_y != self.led_video_params.get_hdmi_in_start_y():
            self.hdmi_in_start_y = self.led_video_params.get_hdmi_in_start_y()
            need_restart_streaming = True

        if self.audio_play_status != self.led_video_params.get_play_with_audio():
            self.audio_play_status = self.led_video_params.get_play_with_audio()
            if self.play_single_file_worker is not None:
                need_restart_streaming = True
            elif self.play_hdmi_in_worker is not None:
                self.audio_playing(self.led_video_params.get_play_with_audio())

        if self.preview_status != self.led_video_params.get_play_with_preview():
            self.preview_status = self.led_video_params.get_play_with_preview()

        if need_restart_streaming is True:
            # if play status == 1, restreaming.
            if self.playing_status == 1:
                if self.play_single_file_worker is not None:
                    log.debug("re-play single play file uri: %s", self.play_single_file_worker.file_uri)
                    file_uri = self.play_single_file_worker.file_uri
                    self.stop_play()
                    self.single_play(file_uri)
                elif self.play_hdmi_in_worker is not None:
                    log.debug("HDMI-In re-play need to be test")
                    video_src = self.play_hdmi_in_worker.video_src
                    self.stop_play()
                    connected, width, height, fps = TC358743().get_current_timing_info()
                    if connected:
                        self.hdmi_in_play(video_src,
                                          active_width=int(width),
                                          active_height=int(height),
                                          )

    def install_signal_media_engine_status_changed_slot(self, slot_func):
        self.signal_media_engine_status_changed.connect(slot_func)

    def install_signal_media_play_status_changed_slot(self, slot_func):
        self.signal_media_play_status_changed.connect(slot_func)

    def install_hdmi_play_status_changed_slot(self, slot_func):
         self.hdmi_play_status_changed.connect(slot_func)

    def install_cms_play_status_changed_slot(self, slot_func):
        self.cms_play_status_changed.connect(slot_func)

    def set_output_streaming_resolution(self, w: int, h: int, fps: int):
        self.output_streaming_width = w
        self.output_streaming_height = h
        self.output_streaming_fps = fps

    def sync_output_streaming_resolution(self):
        '''str_w, str_h, str_fps = (
            get_led_config_from_file_uri("led_wall_resolution", "led_wall_width", "led_wall_height", "led_wall_fps"))
        self.output_streaming_width = int(str_w)
        self.output_streaming_height = int(str_h)
        self.output_streaming_fps = int(str_fps)'''
        self.output_streaming_width = int(self.led_video_params.get_output_frame_width())
        self.output_streaming_height = int(self.led_video_params.get_output_frame_height())
        self.output_streaming_fps = int(self.led_video_params.get_output_fps())

    def play_status_changed(self, status: int, playing_src: str):
        log.debug("play_status_changed : status=%d", status)
        self.play_change_mutex.lock()
        self.playing_status = status
        try:
            if status == PlayStatus.Stop:
                self.hdmi_play_status_changed.emit(status, "")
                self.cms_play_status_changed.emit(status, "")
                self.signal_media_play_status_changed.emit(status, "")
                self.signal_media_engine_status_changed.emit(status, "STOP PLAY")
            else :
                if "/dev/video" in playing_src:
                    self.hdmi_play_status_changed.emit(status, playing_src)
                    self.signal_media_engine_status_changed.emit(status, "HDMI-In")
                elif re.search(r":\d", playing_src):
                    self.cms_play_status_changed.emit(status, playing_src)
                    self.signal_media_engine_status_changed.emit(status, "CMS")
                else:
                    self.signal_media_play_status_changed.emit(status, playing_src)
                    self.signal_media_engine_status_changed.emit(status, "Media File")
        finally:
            self.play_change_mutex.unlock()

    def preview_pixmap_changed(self, raw_image_np_array):
        if self.led_video_params.get_play_with_preview() == 0:
            if self.playing_preview_window.isVisible() is True:
                self.playing_preview_window.setVisible(False)
            return

        if raw_image_np_array is None:
            log.error("raw_image_np_array is None")
            return
        if self.playing_status == PlayStatus.Stop:
            self.playing_preview_window.setVisible(False)
        else:
            if self.playing_preview_window.isVisible() is False:
                self.playing_preview_window.setVisible(True)

        self.playing_preview_window.refresh_image(raw_image_np_array)

    def single_play(self, file_uri, **kwargs):

        log.debug("single play file uri: %s", file_uri)
        if not os.path.exists(file_uri):
            log.debug("File missing: %s", file_uri)
            return

        # stop play first
        self.stop_play()
        self.play_single_file_thread = QThread()
        self.play_single_file_worker = PlaySingleFileWorker(self, file_uri)
        self.play_single_file_worker.install_play_status_slot(self.play_status_changed)
        self.play_single_file_worker.install_pixmap_refreshed_slot(self.preview_pixmap_changed)

        self.play_single_file_worker.moveToThread(self.play_single_file_thread)
        self.play_single_file_thread.started.connect(self.play_single_file_worker.run)
        self.play_single_file_worker.pysignal_single_file_play_finished.connect(self.play_single_file_thread.quit)
        self.play_single_file_worker.pysignal_single_file_play_finished.connect(
            self.play_single_file_worker.deleteLater)
        self.play_single_file_thread.finished.connect(self.play_single_file_thread.deleteLater)
        self.play_single_file_thread.start()

    def play_playlist(self, playlist_uri, **kwargs):
        log.debug("playlist uri: %s", playlist_uri)
        if os.path.exists(playlist_uri) is False:
            log.debug("no such playlist file")
            return
        if utils.utils_file_access.get_file_list_in_playlist(playlist_uri) is None:
            log.debug("No file in playlist")
            return

        self.stop_play()
        self.play_playlist_thread = QThread()
        self.play_playlist_worker = PlayPlaylistWorker(self, playlist_uri)
        self.play_playlist_worker.install_play_status_slot(self.play_status_changed)
        self.play_playlist_worker.install_pixmap_refreshed_slot(self.preview_pixmap_changed)
        self.play_playlist_worker.moveToThread(self.play_playlist_thread)
        self.play_playlist_thread.started.connect(self.play_playlist_worker.run)
        self.play_playlist_worker.pysignal_playlist_play_finished.connect(self.play_playlist_thread.quit)
        self.play_playlist_worker.pysignal_playlist_play_finished.connect(
            self.play_playlist_worker.deleteLater)
        self.play_playlist_thread.finished.connect(self.play_playlist_thread.deleteLater)
        self.play_playlist_thread.start()

    def play_cms(self, window_width, window_height, window_x, window_y, **kwargs):

        log.debug("play_cms")

        c_width = 0
        c_height = 0
        c_pos_x = 0
        c_pos_y = 0

        log.debug("window_width = %d", window_width)
        log.debug("window_height = %d", window_height)
        log.debug("window_x = %d", window_x)
        log.debug("window_y = %d", window_y)

        self.media_active_width = window_width
        self.media_active_height = window_height
        # log.debug("self.led_video_params.get_media_file_crop_w() = %d", self.led_video_params.get_media_file_crop_w())
        # log.debug("self.led_video_params.get_media_file_crop_h() = %d", self.led_video_params.get_media_file_crop_h())

        # if (self.led_video_params.get_media_file_crop_w() is not None
        #         and self.led_video_params.get_media_file_crop_h() is not None
        #         and active_width and active_height):
        #     c_width = min(self.led_video_params.get_media_file_crop_w(), active_width)
        #     c_height = min(self.led_video_params.get_media_file_crop_h(), active_height)
        #     c_pos_x = self.led_video_params.get_media_file_start_x()
        #     c_pos_y = self.led_video_params.get_media_file_start_y()

        log.debug("c_width = %d", c_width)
        log.debug("c_height = %d", c_height)
        log.debug("c_pos_x = %d", c_pos_x)
        log.debug("c_pos_y = %d", c_pos_y)
        self.stop_play()
        self.play_cms_thread = QThread()
        self.play_cms_worker = PlayCMSWorker(self, window_width, window_height, window_x, window_y,
                                             c_width=c_width, c_height=c_height, c_pos_x=c_pos_x, c_pos_y=c_pos_y)
        self.play_cms_worker.install_play_status_slot(self.play_status_changed)
        self.play_cms_worker.install_pixmap_refreshed_slot(self.preview_pixmap_changed)
        self.play_cms_worker.moveToThread(self.play_cms_thread)
        self.play_cms_thread.started.connect(self.play_cms_worker.run)
        self.play_cms_worker.pysignal_cms_play_finished.connect(self.play_cms_thread.quit)
        self.play_cms_worker.pysignal_cms_play_finished.connect(
            self.play_cms_worker.deleteLater)
        self.play_cms_thread.finished.connect(self.play_cms_thread.deleteLater)
        self.play_cms_thread.start()


    def stop_play(self):
        log.debug("enter stop_play!\n")

        if self.play_single_file_worker is not None:
            self.play_single_file_worker.stop()
            self.play_single_file_worker.terminate_pipeline(self.video_backend)
            time.sleep(1)
            try:
                if self.play_single_file_thread is not None:
                    self.play_single_file_thread.quit()
                for i in range(5):
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

        if self.play_playlist_worker is not None:
            self.play_playlist_worker.stop()
            self.play_playlist_worker.terminate_pipeline(self.video_backend)
            time.sleep(1)
            try:
                if self.play_playlist_thread is not None:
                    self.play_playlist_thread.quit()
                for i in range(5):
                    log.debug("self.play_playlist_thread.isFinished() = %d",
                              self.play_playlist_thread.isFinished())
                    if self.play_playlist_thread.isFinished() is True:
                        break
                    time.sleep(1)

                log.debug("single_file_worker is not None A2")
                self.play_playlist_thread.wait()
                self.play_playlist_thread.exit(0)
            except Exception as e:
                log.debug(e)
            self.play_playlist_worker = None
            self.play_playlist_worker = None

        if self.play_hdmi_in_worker is not None:
            self.resume_playing()
            self.play_hdmi_in_worker.stop()
            self.play_hdmi_in_worker.terminate_pipeline(self.video_backend)
            time.sleep(1)
            try:
                if self.play_hdmi_in_thread is not None:
                    self.play_hdmi_in_thread.quit()
                for i in range(5):
                    log.debug("self.play_hdmi_in_thread.isFinished() = %d",
                              self.play_hdmi_in_thread.isFinished())
                    if self.play_hdmi_in_thread.isFinished() is True:
                        break
                    time.sleep(1)

                log.debug("play_hdmi_in_worker is not None A2")
                self.play_hdmi_in_thread.wait()
                self.play_hdmi_in_thread.exit(0)
            except Exception as e:
                log.debug(e)
            self.play_hdmi_in_worker = None
            self.play_hdmi_in_worker = None

        if self.play_cms_worker is not None:
            self.resume_playing()
            self.play_cms_worker.stop()
            self.play_cms_worker.terminate_pipeline(self.video_backend)
            for i in range(5):
                if self.ff_process is not None:
                    try:
                        os.kill(self.ff_process.pid, signal.SIGTERM)
                    except ProcessLookupError:
                        log.debug("PID might have changed or process could have exited already")
                    except Exception as e:
                        log.debug(f"An error occurred when trying to kill the process: {e}")
                    finally:
                        self.ff_process = None
                        break
                time.sleep(1)
            try:
                if self.play_cms_thread is not None:
                    self.play_cms_thread.quit()
                for i in range(5):
                    log.debug("self.play_cms_thread.isFinished() = %d",
                              self.play_cms_thread.isFinished())
                    if self.play_cms_thread.isFinished() is True:
                        break
                    time.sleep(1)

                log.debug("play_play_cms_thread is not None A2")
                self.play_cms_thread.wait()
                self.play_cms_thread.exit(0)
            except Exception as e:
                log.debug(e)
            self.play_cms_worker = None
            self.play_cms_thread = None

        self.sound_device.stop_play()
        self.playing_preview_window.close_window()
        self.play_status_changed(PlayStatus.Stop, "")
        log.debug("exit stop_play!\n")

    def hdmi_in_play(self, video_src, **kwargs):

        if video_src is None:
            return

        self.media_active_width = kwargs.get('active_width')
        self.media_active_height = kwargs.get('active_height')
        self.play_hdmi_in_thread = QThread()
        self.play_hdmi_in_worker = Playing_HDMI_in_worker(self, video_src)
        self.play_hdmi_in_worker.install_play_audio_slot(self.play_hdmi_in_worker.handle_audio_playback)
        self.play_hdmi_in_worker.install_play_status_slot(self.play_status_changed)
        self.play_hdmi_in_worker.moveToThread(self.play_hdmi_in_thread)

        self.play_hdmi_in_thread.started.connect(self.play_hdmi_in_worker.run)
        self.play_hdmi_in_worker.pysignal_hdmi_play_finished.connect(self.play_hdmi_in_thread.quit)
        self.play_hdmi_in_worker.pysignal_hdmi_play_finished.connect(self.play_hdmi_in_worker.deleteLater)
        self.play_hdmi_in_thread.finished.connect(self.play_hdmi_in_thread.deleteLater)
        self.play_hdmi_in_worker.install_pixmap_refreshed_slot(self.preview_pixmap_changed)
        self.play_hdmi_in_thread.start()
        self.audio_playing(self.led_video_params.get_play_with_audio())

    def pause_playing(self):
        if self.playing_status != PlayStatus.Stop:
            log.debug("enter pause_play!\n")
            try:
                self.playing_status = PlayStatus.Pausing

                if self.video_backend == VideoBackendType.FFMPEG.value:
                    if self.ff_process is not None:
                        sub_ff_process = self.find_child(VideoBackendType.FFMPEG.value, self.ff_process.pid)
                        if sub_ff_process:
                            sub_ff_process.suspend()
                        else:
                            os.kill(self.ff_process.pid, signal.SIGSTOP)
                else:
                   if self.gst_pipeline is not None:
                        self.gst_pipeline.set_state(Gst.State.PAUSED)

                if self.sound_device.audio_process is not None:
                    mute_audio_sinks(True)
                if self.play_hdmi_in_worker is not None:
                    self.play_status_changed(self.playing_status, self.play_hdmi_in_worker.video_src)
                if self.play_single_file_thread is not None:
                    self.play_status_changed(self.playing_status, self.play_single_file_worker.file_uri)
                if self.play_playlist_thread is not None:
                   self.play_status_changed(self.playing_status, self.play_playlist_worker.files_in_playlist[self.play_playlist_worker.file_index])
                if self.play_cms_worker is not None:
                    self.play_status_changed(self.playing_status, self.play_cms_worker.video_src)

            except Exception as e:
                log.debug(e)

    def resume_playing(self):
        if self.playing_status != PlayStatus.Stop:
            log.debug("enter resume_play!\n")
            try:
                self.playing_status = PlayStatus.Playing
                if self.video_backend == VideoBackendType.FFMPEG.value:
                    if self.ff_process is not None:
                        sub_ff_process = self.find_child(VideoBackendType.FFMPEG.value, self.ff_process.pid)
                        if sub_ff_process:
                            sub_ff_process.resume()
                        else:
                            os.kill(self.ff_process.pid, signal.SIGCONT)
                else:
                    if self.gst_pipeline is not None:
                        self.gst_pipeline.set_state(Gst.State.PLAYING)

                if self.sound_device.audio_process is not None:
                    mute_audio_sinks(False)
                if self.play_hdmi_in_worker is not None:
                    self.play_status_changed(self.playing_status, self.play_hdmi_in_worker.video_src)
                if self.play_single_file_thread is not None:
                    self.play_status_changed(self.playing_status, self.play_single_file_worker.file_uri)
                if self.play_playlist_thread is not None:
                    self.play_status_changed(self.playing_status, self.play_playlist_worker.files_in_playlist[
                        self.play_playlist_worker.file_index])
                if self.play_cms_worker is not None:
                    self.play_status_changed(self.playing_status, self.play_cms_worker.video_src)

            except Exception as e:
                log.debug(e)

    def audio_playing(self, status: int):
        log.debug("enter audio_play!\n")
        if self.play_hdmi_in_worker is not None:
            self.play_hdmi_in_worker.pysignal_hdmi_play_audio.emit(status)

    def find_child(self, child_name, parent_pid):
        parent = psutil.Process(parent_pid)
        for child in parent.children(recursive=True):
            if child_name in child.name():
                return child
        return None

    def get_media_resolution(self, file_uri, backend):
        resolution = None

        if backend== VideoBackendType.FFMPEG.value:
            try:
                ffmpeg_cmd = ['ffprobe', '-v', 'error', '-select_streams', 'v:0', '-show_entries', 'stream=width,height',
                              '-of', 'csv=s=x:p=0', file_uri]
                self.ffprobe_process = subprocess.Popen(ffmpeg_cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                                                   text=True)
                output, error = self.ffprobe_process.communicate()
                # log.debug("output : %s", output)
                # log.debug("error : %s", error)
                match = re.search(r'(\d{2,5})x(\d{2,5})', output)
                if match:
                    width, height = map(int, match.groups())
                    if (0 < width <= 4096 and
                            0 < height <= 3112):
                        resolution = width, height
            except Exception as e:
                log.debug(f"Error processing video file: {str(e)}")
            finally:
                if self.ffprobe_process and self.ffprobe_process.poll() is None:
                    self.ffprobe_process.kill()
        else :
            result = subprocess.run(['gst-discoverer-1.0', file_uri], stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                                    text=True)
            match = re.search(r'Width:\s+(\d+)\s+Height:\s+(\d+)', result.stdout)
            if match:
                width, height = map(int, match.groups())
                if (0 < width <= 4096 and
                        0 < height <= 3112):
                    resolution = width, height

        return resolution

    def get_hdmi_resolution(self):
        # Evaluate whether to make modifications later @Hank
        if (0 < self.media_active_width <= 4096 and
                0 < self.media_active_height <= 3112):
            return self.media_active_width, self.media_active_height
        return None

    def get_cms_resolution(self):
        # Evaluate whether to make modifications later @Hank
        if (0 < self.media_active_width <= 4096 and
                0 < self.media_active_height <= 3112):
            return self.media_active_width, self.media_active_height
        return None

    def is_valid_file(self,file_path):
        # File does not exist or is not a valid file
        if not os.path.isfile(file_path):
            return False
        # File does not exist
        if not os.path.exists(file_path):
            return False
        # File is empty
        if os.path.getsize(file_path) == 0:
            return False,

        return True

class MediaIpc(QObject):
    def __init__(self, media_engine: MediaEngine):
        super().__init__()
        self.media_engine = media_engine
        self.output_width = media_engine.output_streaming_width
        self.output_height = media_engine.output_streaming_height
        self.shm_sem_write_uri = media_engine.shm_sem_write_uri
        self.shm_sem_read_uri = media_engine.shm_sem_read_uri
        self.shm = None
        self.shm_sem = None
        self.sem_read_flag = None
        self.sem_write_flag = None
        self.agent_process = None
        self.try_wait_write_count = 0

    def initialize_ipc_resources(self):
        """Main entry to set up shared memory and agent."""
        for _ in range(3):
            try:
                self.restart_agent_process()
                self.shm = self.create_shared_memory()
                if self.initialize_semaphores():
                    return True
            except Exception as e:
                log.fatal(f"Initialization failed: {e}")
                self.terminate_agent_process()
                time.sleep(1)
        return False

    def create_shared_memory(self):
        """Creates and returns a shared memory object."""
        return shared_memory.SharedMemory("posixsm", False, 0x400000)

    def initialize_semaphores(self):
        """Sets up read/write semaphores for shared memory access."""
        self.shm_sem = LinuxIpcSemaphorePyapi()
        self.sem_write_flag = self.open_semaphore(self.shm_sem_write_uri, 1)
        self.sem_read_flag = self.open_semaphore(self.shm_sem_read_uri, 0)
        return self.sem_write_flag is not None and self.sem_read_flag is not None

    def open_semaphore(self, uri, initial_value):
        """Helper to open a semaphore and handle failures."""
        sem = self.shm_sem.sem_open(uri, os.O_CREAT, 0x666, initial_value)
        if sem == 0:
            log.debug(f"Failed to create semaphore: {uri}")
            return None
        return sem

    # --- Agent Process Management ---
    def restart_agent_process(self):
        """Configures and starts the agent preview window."""
        self.terminate_agent_process()
        preview_pos_x, preview_pos_y = self.calculate_preview_position()
        os.environ['SDL_VIDEO_WINDOW_POS'] = f"{preview_pos_x},{preview_pos_y}"
        agent_cmd = f"{root_dir}/ext_binaries/show_ffmpeg_shared_memory {ETH_DEV} {self.output_width} {self.output_height} 0"
        self.agent_process = subprocess.Popen(agent_cmd, shell=True)
        log.debug(f"Agent process started with PID: {self.agent_process.pid}")
        time.sleep(1)

    def calculate_preview_position(self):
        """Calculates and returns agent preview window position."""
        line = os.popen("xdpyinfo | awk '/dimensions/{print $2}'").read()
        geo_w, geo_h = map(int, line.split("x"))
        return (geo_w - 640, 320) if self.output_width >= 1280 else (geo_w - self.output_width, 320)

    def terminate_agent_process(self):
        """Terminates the agent process to stop preview."""
        if self.agent_process:
            self.agent_process.kill()
            self.agent_process = None
        subprocess.Popen("pkill -9 -f show_ffmpeg_shared_memory", shell=True)
        time.sleep(1)

    # --- Shared Memory and Semaphore Operations ---
    def wait_sem_write_access(self):
        """Attempts to acquire write semaphore; handles retries and agent restarts if necessary."""
        if self.shm_sem.sem_trywait(self.sem_write_flag) == -1:
            self.try_wait_write_count += 1
            if self.try_wait_write_count > 500:
                log.debug("Missing agent! Restarting...")
                self.try_wait_write_count = 0
                self.terminate_agent_process()
                self.restart_agent_process()
            return False
        self.try_wait_write_count = 0
        return True

    def write_to_shared_memory(self, data):
        """Writes data to shared memory and posts read semaphore."""
        to_write = memoryview(data)
        self.shm._buf[:len(to_write)] = to_write[:]
        self.shm_sem.sem_post(self.sem_read_flag)

    def cleanup_ipc_resources(self):
        """Cleans up shared memory and semaphore resources."""
        if self.shm:
            self.shm.close()
            self.shm.unlink()
            self.shm = None
        if self.shm_sem:
            if self.sem_write_flag:
                self.shm_sem.sem_close(self.sem_write_flag)
                self.shm_sem.sem_unlink(self.shm_sem_write_uri)
                self.sem_write_flag = None
            if self.sem_read_flag:
                self.shm_sem.sem_close(self.sem_read_flag)
                self.shm_sem.sem_unlink(self.shm_sem_read_uri)
                self.sem_read_flag = None
            self.shm_sem = None

class PlayPlaylistWorker(QObject):
    pysignal_playlist_play_status_change = pyqtSignal(int, str)
    pysignal_playlist_play_finished = pyqtSignal()
    pysignal_refresh_image_pixmap = pyqtSignal(np.ndarray)
    pysignal_send_raw_frame = pyqtSignal(bytes)

    def __init__(self, media_engine: MediaEngine, playlist_uri):
        super().__init__()
        self.media_engine = media_engine
        self.media_ipc = MediaIpc(media_engine)
        self.crop_position_y = 0
        self.crop_position_x = 0
        self.crop_visible_area_height = 0
        self.crop_visible_area_width = 0
        self.media_active_height = 0
        self.media_active_width = 0
        self.image_period_timer = 5
        self.playlist_uri = playlist_uri
        self.video_params = self.media_engine.led_video_params
        self.force_stop = False
        self.worker_status = 0
        self.force_stop_mutex = QMutex()
        self.play_status = None
        self.files_in_playlist = get_file_list_in_playlist(self.playlist_uri)
        log.debug("file list in playlist: %s", self.files_in_playlist)
        self.file_index = 0
        # read playlist first
        self.play_status_change(PlayStatus.Initial, self.files_in_playlist[self.file_index])
        self.ff_process = self.media_engine.ff_process
        self.gst_pipeline = self.media_engine.gst_pipeline
        self.gst_appsink = None
        self.gst_image_period_event = None
        self.output_width = self.media_engine.output_streaming_width
        self.output_height = self.media_engine.output_streaming_height
        self.output_fps = self.media_engine.output_streaming_fps
        self.playing_source = None
        self.image_from_pipe = None
        self.raw_image = None
        self.preview_window = None
        # To be implemented

    def install_play_status_slot(self, slot_func):
        self.pysignal_playlist_play_status_change.connect(slot_func)

    def install_pixmap_refreshed_slot(self, slot_func):
        self.pysignal_refresh_image_pixmap.connect(slot_func)

    def install_send_raw_frame_slot(self, slot_func):
        self.pysignal_send_raw_frame.connect(slot_func)

    def play_status_change(self, status: int, src: str):
        self.play_status = status
        self.playing_source = src
        log.debug("self.playing_source : %s", self.playing_source)
        self.pysignal_playlist_play_status_change.emit(self.play_status, self.playing_source)

    def terminate_pipeline(self, backend):
        """Terminates playback pipeline based on backend (ffmpeg or GStreamer)."""
        if backend == VideoBackendType.FFMPEG.value:
            if self.ff_process is not None:
                self.ff_process.kill()
            self.ff_process = None
            self.media_engine.ff_process = self.ff_process
        else:
            if self.gst_pipeline is not None:
                self.gst_pipeline.set_state(Gst.State.NULL)
                self.gst_pipeline = None
                self.media_engine.gst_pipeline = self.gst_pipeline

                if self.gst_appsink and self.gst_appsink.handler_is_connected(
                        self.gst_appsink.connect('new-sample', self.process_gst_frame_sample)):
                    self.gst_appsink.disconnect_by_func(self.process_gst_frame_sample)

    def start_GStreamer_stream(self):
        # Loop to play through the playlist until completion or forced stop
        while True:

            # Fetch the video resolution for the current file in the playlist
            resolution = self.media_engine.get_media_resolution(
                file_uri=self.files_in_playlist[self.file_index],
                backend=self.media_engine.video_backend
            )

            # Update active media width and height if resolution is obtained
            if resolution:
                self.media_active_width, self.media_active_height = resolution

            # Debug output for active resolution
            log.debug("Active resolution - Width: %d, Height: %d", self.media_active_width, self.media_active_height)

            # Debug output for crop parameters
            log.debug("Configured crop dimensions - Width: %d, Height: %d",
                      self.video_params.get_media_file_crop_w(),
                      self.video_params.get_media_file_crop_h())

            # Configure cropping dimensions based on media and crop parameters
            if (self.video_params.get_media_file_crop_w() is not None and
                    self.video_params.get_media_file_crop_h() is not None and
                    self.media_active_width and self.media_active_height):
                self.crop_visible_area_width = min(self.video_params.get_media_file_crop_w(), self.media_active_width)
                self.crop_visible_area_height = min(self.video_params.get_media_file_crop_h(), self.media_active_height)
                self.crop_position_x = self.video_params.get_media_file_start_x()
                self.crop_position_y = self.video_params.get_media_file_start_y()

            # Debug output for final crop parameters
            log.debug("Crop configuration - Width: %d, Height: %d, Position X: %d, Position Y: %d",
                      self.crop_visible_area_width,
                      self.crop_visible_area_height,
                      self.crop_position_x,
                      self.crop_position_y)

            # Prepare audio and target frame rate settings
            audio_sink_str = 'default'
            if platform.machine() in ('arm', 'arm64', 'aarch64'):
                if self.media_engine.headphone_sound is not None:
                    sink_card, sink_device = self.media_engine.headphone_sound
                    audio_sink_str = f'hw:{sink_card},{sink_device}'
            target_fps_str = f"{self.output_fps}/1"

            # Construct GStreamer pipeline command
            gst_pipeline_str = get_gstreamer_cmd_for_media(
                self.files_in_playlist[self.file_index],
                width=self.output_width,
                height=self.output_height,
                target_fps=target_fps_str,
                image_period=self.image_period_timer,
                i_width=self.media_active_width,
                i_height=self.media_active_height,
                c_width=self.crop_visible_area_width,
                c_height=self.crop_visible_area_height,
                c_pos_x=self.crop_position_x,
                c_pos_y=self.crop_position_y,
                audio_sink=audio_sink_str,
                audio_on=self.video_params.get_play_with_audio()
            )
            log.debug("gst-launch-1.0 %s", gst_pipeline_str)

            # Parse and launch the GStreamer pipeline
            self.gst_pipeline = Gst.parse_launch(gst_pipeline_str)
            self.gst_appsink = self.gst_pipeline.get_by_name('appsink_sink')
            self.gst_appsink.set_property('emit-signals', True)
            self.gst_appsink.set_property('sync', True)
            self.gst_appsink.connect('new-sample', self.process_gst_frame_sample)
            self.media_engine.gst_pipeline = self.gst_pipeline

            # Set the pipeline to PLAYING state and start monitoring bus messages
            bus = self.gst_pipeline.get_bus()
            self.play_status_change(PlayStatus.Playing, self.files_in_playlist[self.file_index])
            self.gst_pipeline.set_state(Gst.State.PLAYING)

            # Create GStreamer image period event
            self.create_gst_image_period_event(self.files_in_playlist[self.file_index])

            # Main loop to check for playback status and handle errors/stream end
            while not self.force_stop:

                if self.play_status == PlayStatus.Stop:
                    self.gst_pipeline.set_state(Gst.State.NULL)
                    break

                # Check for any errors or end-of-stream events
                msg = bus.timed_pop_filtered(100 * Gst.MSECOND, Gst.MessageType.ERROR | Gst.MessageType.EOS | Gst.MessageType.STATE_CHANGED)
                if msg:

                    if msg.type == Gst.MessageType.STATE_CHANGED:
                        old_state, new_state, pending_state = msg.parse_state_changed()
                        # log.debug("old_state:%s , new_state:%s , pending_state:%s", old_state, new_state, pending_state)
                        if new_state == Gst.State.PAUSED:
                            if self.gst_image_period_event:
                                self.gst_image_period_event.pause()
                        elif new_state == Gst.State.PLAYING:
                            if self.gst_image_period_event:
                                self.gst_image_period_event.resume()

                    if msg.type == Gst.MessageType.EOS:
                        log.debug('End of stream')
                        if self.play_status == PlayStatus.Playing:
                            self.terminate_pipeline(self.media_engine.video_backend)

                            if self.media_engine.repeat_option == RepeatOption.Repeat_None:
                                if self.is_playlist_end():
                                    log.debug("Stop play due to end of repeat")
                                    return

                            # Find the next valid file to play
                            next_file_index = self.get_playlist_next_valid_file()
                            if next_file_index is None:
                                log.debug("No valid file found in the playlist.")
                                return
                            else:
                                # Update to the next valid file index and break to restart the pipeline
                                self.file_index = next_file_index
                                break
                    elif msg.type == Gst.MessageType.ERROR:
                        err, debug_info = msg.parse_error()
                        log.error(f"Error received: {err}, {debug_info}")
                        break

            log.debug("GStreamer playlist end")
            if self.force_stop:
                return

    def process_gst_frame_sample(self, sink=None):
        # Retrieve the video frame sample
        sample = sink.emit('pull-sample')
        buf = sample.get_buffer()
        result, self.image_from_pipe = buf.map(Gst.MapFlags.READ)

        self.worker_status = 1

        if result:
            try:
                # Convert video frame data to RGB and emit the updated frame
                self.raw_image = np.frombuffer(self.image_from_pipe.data, dtype=np.uint8).reshape(
                    (self.output_height, self.output_width, 3))
                self.pysignal_refresh_image_pixmap.emit(self.raw_image)

                if len(self.raw_image) <= 0:
                    log.debug("play end")
                    # self.media_ipc.terminate_agent_process()
                    return Gst.FlowReturn.EOS

                # Check if force stop is triggered
                if self.force_stop:
                    log.debug("self.force_stop is True, stopping gst_pipeline")
                    self.gst_pipeline.set_state(Gst.State.NULL)
                    return Gst.FlowReturn.EOS  # End processing

                # Check if image period is timeout
                if self.gst_image_period_event:
                    if self.gst_image_period_event.is_timed_out():
                        log.debug("image period is timeout")
                        return Gst.FlowReturn.EOS

                if not self.media_ipc.wait_sem_write_access():
                    pass
                else:
                    self.media_ipc.write_to_shared_memory(self.image_from_pipe.data)

            finally:
                buf.unmap(self.image_from_pipe)  # Ensure buffer is released

        return Gst.FlowReturn.OK

    def create_gst_image_period_event(self ,file_url):
        static_image_extensions = (".jpeg", ".jpg", ".png")
        # Check if the current file is a static image
        if file_url.lower().endswith(static_image_extensions):
            # If the event is already active, just restart the timer
            if self.gst_image_period_event:
                self.gst_image_period_event.reset_timer(self.image_period_timer)
            else:
                # Create a new event if it does not exist
                self.gst_image_period_event = gstreamer_image_period_event(self.image_period_timer)
            self.gst_image_period_event.start()
        else:
            # Stop and clear the event if the current file is not a static image
            self.terminate_gst_image_period_event()


    def terminate_gst_image_period_event(self):
        if self.gst_image_period_event:
            self.gst_image_period_event.stop()
            self.gst_image_period_event = None


    def start_ffmpeg_stream(self):

        while True:
            if self.play_status != PlayStatus.Stop:
                try:
                    if self.ff_process is not None:
                        if self.play_status == PlayStatus.Pausing:
                            os.kill(self.ff_process.pid, signal.SIGCONT)  # Continue process
                        else:
                            os.kill(self.ff_process.pid, signal.SIGTERM)  # Terminate process
                except Exception as e:
                    log.error(e)

            # Fetch the video resolution for the current file in the playlist
            resolution = self.media_engine.get_media_resolution(
                file_uri=self.files_in_playlist[self.file_index],
                backend=self.media_engine.video_backend
            )

            # Update active media width and height if resolution is obtained
            if resolution:
                self.media_active_width, self.media_active_height = resolution

            # Debug output for active resolution
            log.debug("Active resolution - Width: %d, Height: %d", self.media_active_width, self.media_active_height)

            # Debug output for crop parameters
            log.debug("Configured crop dimensions - Width: %d, Height: %d",
                      self.video_params.get_media_file_crop_w(),
                      self.video_params.get_media_file_crop_h())

            # Configure cropping dimensions based on media and crop parameters
            if (self.video_params.get_media_file_crop_w() is not None and
                    self.video_params.get_media_file_crop_h() is not None and
                    self.media_active_width and self.media_active_height):
                self.crop_visible_area_width = min(self.video_params.get_media_file_crop_w(), self.media_active_width)
                self.crop_visible_area_height = min(self.video_params.get_media_file_crop_h(), self.media_active_height)
                self.crop_position_x = self.video_params.get_media_file_start_x()
                self.crop_position_y = self.video_params.get_media_file_start_y()

            # Debug output for final crop parameters
            log.debug("Crop configuration - Width: %d, Height: %d, Position X: %d, Position Y: %d",
                      self.crop_visible_area_width,
                      self.crop_visible_area_height,
                      self.crop_position_x,
                      self.crop_position_y)

            audio_sink_str = 'default'
            if platform.machine() in ('arm', 'arm64', 'aarch64'):
                if self.media_engine.headphone_sound is not None:
                    sink_card, sink_device = self.media_engine.headphone_sound
                    audio_sink_str = f'hw:{sink_card},{sink_device}'
            target_fps_str = f"{self.output_fps}/1"

            ffmpeg_cmd = get_ffmpeg_cmd_for_media(self.files_in_playlist[self.file_index],
                                                  width=self.output_width, height=self.output_height,
                                                  target_fps=target_fps_str, image_period=self.image_period_timer,
                                                  c_width=self.crop_visible_area_width,
                                                  c_height=self.crop_visible_area_height,
                                                  c_pos_x=self.crop_position_x,
                                                  c_pos_y=self.crop_position_y,
                                                  audio_sink=audio_sink_str,
                                                  audio_on=self.video_params.get_play_with_audio()
                                                  )
            log.debug("ffmpeg_cmd : %s", ffmpeg_cmd)
            try:
                self.ff_process = subprocess.Popen(ffmpeg_cmd, stdout=subprocess.PIPE, bufsize=10 ** 8, shell=True)
                self.media_engine.ff_process = self.ff_process
            except Exception as e:
                log.error(e)
            # write__flag_tmp = self.shm_sem.sem_post(sem_write_flag)
            if self.ff_process.pid > 0:
                self.play_status_change(PlayStatus.Playing, self.files_in_playlist[self.file_index])
                self.image_from_pipe = None
                while self.ff_process.pid > 0:
                    self.image_from_pipe = self.ff_process.stdout.read(self.output_width * self.output_height * 3)
                    if len(self.image_from_pipe) <= 0:
                        log.debug("play end")
                        # self.media_ipc.terminate_agent_process()
                        break
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

                    if not self.media_ipc.wait_sem_write_access():
                        pass
                    else :
                        self.media_ipc.write_to_shared_memory(self.image_from_pipe)

            log.debug("single play end")

            if self.media_engine.repeat_option == RepeatOption.Repeat_None:
                if self.is_playlist_end():
                    log.debug("Stop play due to end of repeat")
                    break

            # Find the next valid file to play
            next_file_index = self.get_playlist_next_valid_file()
            if next_file_index is None:
                log.debug("No valid file found in the playlist.")
                break
            else:
                # Update to the next valid file index and break to restart the pipeline
                self.file_index = next_file_index

            if self.force_stop is True:
                break


    def run(self):
        self.media_engine.sync_output_streaming_resolution()  # venom for output resolution correction
        self.worker_status = 1
        # Initialize shared memory and agent preview for media player
        if self.media_ipc.initialize_ipc_resources():
            if self.media_engine.video_backend == VideoBackendType.FFMPEG.value:
                self.start_ffmpeg_stream()
            else:
                self.start_GStreamer_stream()
        else:
            log.debug("initialize_ipc_resources failed")

        # Cleanup after playback ends
        self.play_status_change(PlayStatus.Stop, "")
        self.terminate_pipeline(self.media_engine.video_backend)
        self.media_ipc.terminate_agent_process()
        self.media_ipc.cleanup_ipc_resources()
        self.pysignal_playlist_play_finished.emit()
        self.terminate_gst_image_period_event()
        self.worker_status = 0

        log.debug("play playlist worker finished")

    def stop(self):
        self.force_stop = True

    def get_worker_status(self):
        return self.worker_status

    def get_playlist_next_valid_file(self):
        attempt_count = 0
        playlist_len = len(self.files_in_playlist)
        while attempt_count < playlist_len:
            file_index = (self.file_index + 1) % playlist_len
            attempt_count += 1
            if os.path.isfile(self.files_in_playlist[file_index]):
                if os.path.getsize(self.files_in_playlist[file_index]) > 0:
                    return file_index  # Return the index if a valid file is found
        return None

    def is_playlist_end(self):
        return self.file_index == len(self.files_in_playlist)

class PlaySingleFileWorker(QObject):
    pysignal_single_file_play_status_change = pyqtSignal(int, str)
    pysignal_single_file_play_finished = pyqtSignal()
    pysignal_refresh_image_pixmap = pyqtSignal(np.ndarray)
    pysignal_send_raw_frame = pyqtSignal(bytes)

    def __init__(self, media_engine: MediaEngine, file_uri):
        super().__init__()
        self.media_engine = media_engine
        self.media_ipc = MediaIpc(media_engine)
        self.crop_position_y = 0
        self.crop_position_x = 0
        self.crop_visible_area_height = 0
        self.crop_visible_area_width = 0
        self.media_active_height = 0
        self.media_active_width = 0
        self.image_period_timer = 20
        self.file_uri = file_uri
        self.video_params = self.media_engine.led_video_params
        self.force_stop = False
        self.worker_status = 0
        self.force_stop_mutex = QMutex()
        self.play_status = None
        self.play_status_change(PlayStatus.Initial, self.file_uri)
        self.ff_process = self.media_engine.ff_process
        self.gst_pipeline = self.media_engine.gst_pipeline
        self.gst_appsink = None
        self.output_width = self.media_engine.output_streaming_width
        self.output_height = self.media_engine.output_streaming_height
        self.output_fps = self.media_engine.output_streaming_fps
        self.playing_source = None
        self.image_from_pipe = None
        self.raw_image = None
        self.preview_window = None

    def install_play_status_slot(self, slot_func):
        self.pysignal_single_file_play_status_change.connect(slot_func)

    def install_pixmap_refreshed_slot(self, slot_func):
        self.pysignal_refresh_image_pixmap.connect(slot_func)

    def install_send_raw_frame_slot(self, slot_func):
        self.pysignal_send_raw_frame.connect(slot_func)

    def terminate_pipeline(self, backend):
        """Terminates playback pipeline based on backend (ffmpeg or GStreamer)."""
        if backend == VideoBackendType.FFMPEG.value:
            if self.ff_process is not None:
                self.ff_process.kill()
            self.ff_process = None
            self.media_engine.ff_process = self.ff_process
        else:
            if self.gst_pipeline is not None:
                self.gst_pipeline.set_state(Gst.State.NULL)
                self.gst_pipeline = None
                self.media_engine.gst_pipeline = self.gst_pipeline

                if self.gst_appsink and self.gst_appsink.handler_is_connected(
                        self.gst_appsink.connect('new-sample', self.process_gst_frame_sample)):
                    self.gst_appsink.disconnect_by_func(self.process_gst_frame_sample)

    def start_GStreamer_stream(self):
        # Fetch the video resolution for the current file in the playlist
        resolution = self.media_engine.get_media_resolution(
            file_uri=self.file_uri,
            backend=self.media_engine.video_backend
        )

        # Update active media width and height if resolution is obtained
        if resolution:
            self.media_active_width, self.media_active_height = resolution

        # Debug output for active resolution
        log.debug("Active resolution - Width: %d, Height: %d", self.media_active_width, self.media_active_height)

        # Debug output for crop parameters
        log.debug("Configured crop dimensions - Width: %d, Height: %d",
                  self.video_params.get_media_file_crop_w(),
                  self.video_params.get_media_file_crop_h())

        # Configure cropping dimensions based on media and crop parameters
        if (self.video_params.get_media_file_crop_w() is not None and
                self.video_params.get_media_file_crop_h() is not None and
                self.media_active_width and self.media_active_height):
            self.crop_visible_area_width = min(self.video_params.get_media_file_crop_w(), self.media_active_width)
            self.crop_visible_area_height = min(self.video_params.get_media_file_crop_h(), self.media_active_height)
            self.crop_position_x = self.video_params.get_media_file_start_x()
            self.crop_position_y = self.video_params.get_media_file_start_y()

        # Debug output for final crop parameters
        log.debug("Crop configuration - Width: %d, Height: %d, Position X: %d, Position Y: %d",
                  self.crop_visible_area_width,
                  self.crop_visible_area_height,
                  self.crop_position_x,
                  self.crop_position_y)

        # Prepare audio and target frame rate settings
        audio_sink_str = 'default'
        if platform.machine() in ('arm', 'arm64', 'aarch64'):
            if self.media_engine.headphone_sound is not None:
                sink_card, sink_device = self.media_engine.headphone_sound
                audio_sink_str = f'hw:{sink_card},{sink_device}'
        target_fps_str = f"{self.output_fps}/1"

        # Construct GStreamer pipeline command
        gst_pipeline_str = get_gstreamer_cmd_for_media(
            self.file_uri,
            width=self.output_width,
            height=self.output_height,
            target_fps=target_fps_str,
            image_period=self.image_period_timer,
            i_width=self.media_active_width,
            i_height=self.media_active_height,
            c_width=self.crop_visible_area_width,
            c_height=self.crop_visible_area_height,
            c_pos_x=self.crop_position_x,
            c_pos_y=self.crop_position_y,
            audio_sink=audio_sink_str,
            audio_on=self.video_params.get_play_with_audio()
        )
        log.debug("gst-launch-1.0 %s", gst_pipeline_str)

        # Parse and launch the GStreamer pipeline
        self.gst_pipeline = Gst.parse_launch(gst_pipeline_str)
        self.gst_appsink = self.gst_pipeline.get_by_name('appsink_sink')
        self.gst_appsink.set_property('emit-signals', True)
        self.gst_appsink.set_property('sync', True)
        self.gst_appsink.connect('new-sample', self.process_gst_frame_sample)
        self.media_engine.gst_pipeline = self.gst_pipeline

        # Set the pipeline to PLAYING state and start monitoring bus messages
        bus = self.gst_pipeline.get_bus()
        self.play_status_change(PlayStatus.Playing, self.file_uri)
        self.gst_pipeline.set_state(Gst.State.PLAYING)

        # Main loop to check for playback status and handle errors/stream end
        while not self.force_stop:

            if self.play_status == PlayStatus.Stop:
                self.gst_pipeline.set_state(Gst.State.NULL)
                break

            # Check for any errors or end-of-stream events
            msg = bus.timed_pop_filtered(100 * Gst.MSECOND, Gst.MessageType.ERROR | Gst.MessageType.EOS)
            if msg:
                if msg.type == Gst.MessageType.EOS:
                    log.debug('End of stream, restarting...')
                    if self.play_status == PlayStatus.Playing:
                        if self.media_engine.repeat_option == RepeatOption.Repeat_None:
                            log.debug("Stop play due to end of repeat")
                            return
                        else:
                            # Restarting pipe
                            self.gst_pipeline.seek_simple(Gst.Format.TIME, Gst.SeekFlags.FLUSH | Gst.SeekFlags.KEY_UNIT, 0)

                elif msg.type == Gst.MessageType.ERROR:
                    err, debug_info = msg.parse_error()
                    log.error(f"Error received: {err}, {debug_info}")
                    break
        log.debug("GStreamer single play end")

    def process_gst_frame_sample(self, sink=None):
        # Retrieve the video frame sample
        sample = sink.emit('pull-sample')
        buf = sample.get_buffer()
        result, self.image_from_pipe = buf.map(Gst.MapFlags.READ)

        self.worker_status = 1

        if result:
            try:
                # Convert video frame data to RGB and emit the updated frame
                self.raw_image = np.frombuffer(self.image_from_pipe.data, dtype=np.uint8).reshape(
                    (self.output_height, self.output_width, 3))
                self.pysignal_refresh_image_pixmap.emit(self.raw_image)

                if len(self.raw_image) <= 0:
                    log.debug("play end")
                    # self.media_ipc.terminate_agent_process()
                    return Gst.FlowReturn.EOS

                # Check if force stop is triggered
                if self.force_stop:
                    log.debug("self.force_stop is True, stopping gst_pipeline")
                    self.gst_pipeline.set_state(Gst.State.NULL)
                    return Gst.FlowReturn.EOS  # End processing

                if not self.media_ipc.wait_sem_write_access():
                    pass
                else:
                    self.media_ipc.write_to_shared_memory(self.image_from_pipe.data)

            finally:
                buf.unmap(self.image_from_pipe)  # Ensure buffer is released

        return Gst.FlowReturn.OK

    def start_ffmpeg_stream(self):

        while True:
            if self.play_status != PlayStatus.Stop:
                try:
                    if self.ff_process is not None:
                        if self.play_status == PlayStatus.Pausing:
                            os.kill(self.ff_process.pid, signal.SIGCONT)  # Continue process
                        else:
                            os.kill(self.ff_process.pid, signal.SIGTERM)  # Terminate process
                except Exception as e:
                    log.error(e)

            # Fetch the video resolution for the current file in the playlist
            resolution = self.media_engine.get_media_resolution(
                file_uri=self.file_uri,
                backend=self.media_engine.video_backend
            )

            # Update active media width and height if resolution is obtained
            if resolution:
                self.media_active_width, self.media_active_height = resolution

            # Debug output for active resolution
            log.debug("Active resolution - Width: %d, Height: %d", self.media_active_width, self.media_active_height)

            # Debug output for crop parameters
            log.debug("Configured crop dimensions - Width: %d, Height: %d",
                      self.video_params.get_media_file_crop_w(),
                      self.video_params.get_media_file_crop_h())

            # Configure cropping dimensions based on media and crop parameters
            if (self.video_params.get_media_file_crop_w() is not None and
                    self.video_params.get_media_file_crop_h() is not None and
                    self.media_active_width and self.media_active_height):
                self.crop_visible_area_width = min(self.video_params.get_media_file_crop_w(), self.media_active_width)
                self.crop_visible_area_height = min(self.video_params.get_media_file_crop_h(), self.media_active_height)
                self.crop_position_x = self.video_params.get_media_file_start_x()
                self.crop_position_y = self.video_params.get_media_file_start_y()

            # Debug output for final crop parameters
            log.debug("Crop configuration - Width: %d, Height: %d, Position X: %d, Position Y: %d",
                      self.crop_visible_area_width,
                      self.crop_visible_area_height,
                      self.crop_position_x,
                      self.crop_position_y)
            audio_sink_str = 'default'

            if platform.machine() in ('arm', 'arm64', 'aarch64'):
                if self.media_engine.headphone_sound is not None:
                    sink_card, sink_device = self.media_engine.headphone_sound
                    audio_sink_str = f'hw:{sink_card},{sink_device}'
            target_fps_str = f"{self.output_fps}/1"

            ffmpeg_cmd = get_ffmpeg_cmd_for_media(self.file_uri,
                                                  width=self.output_width, height=self.output_height,
                                                  target_fps=target_fps_str, image_period=self.image_period_timer,
                                                  c_width=self.crop_visible_area_width,
                                                  c_height=self.crop_visible_area_height,
                                                  c_pos_x=self.crop_position_x,
                                                  c_pos_y=self.crop_position_y,
                                                  audio_sink=audio_sink_str,
                                                  audio_on=self.video_params.get_play_with_audio()
                                                  )
            log.debug("ffmpeg_cmd : %s", ffmpeg_cmd)
            try:
                self.ff_process = subprocess.Popen(ffmpeg_cmd, stdout=subprocess.PIPE, bufsize=10 ** 8, shell=True)
                self.media_engine.ff_process = self.ff_process
            except Exception as e:
                log.error(e)
            # write__flag_tmp = self.shm_sem.sem_post(sem_write_flag)
            if self.ff_process.pid > 0:
                self.play_status_change(PlayStatus.Playing, self.file_uri)
                self.image_from_pipe = None
                while self.ff_process.pid > 0:
                    self.image_from_pipe = self.ff_process.stdout.read(self.output_width * self.output_height * 3)
                    if len(self.image_from_pipe) <= 0:
                        log.debug("play end")
                        # self.media_ipc.terminate_agent_process()
                        break
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

                    if not self.media_ipc.wait_sem_write_access():
                        pass
                    else :
                        self.media_ipc.write_to_shared_memory(self.image_from_pipe)

            log.debug("single play end")
            if self.media_engine.repeat_option == RepeatOption.Repeat_None:
                log.debug("stop play cause play end")
                break
            if self.force_stop is True:
                break

    def run(self):
        self.media_engine.sync_output_streaming_resolution()  # venom for output resolution correction
        self.worker_status = 1

        if self.is_valid_file(self.file_uri):
            # Initialize shared memory and agent preview for media player
            if self.media_ipc.initialize_ipc_resources():
                if self.media_engine.video_backend == VideoBackendType.FFMPEG.value:
                    self.start_ffmpeg_stream()
                else:
                    self.start_GStreamer_stream()
            else :
                log.debug("initialize_ipc_resources failed")

        # Cleanup after playback ends
        self.play_status_change(PlayStatus.Stop, "")
        self.terminate_pipeline(self.media_engine.video_backend)
        self.media_ipc.terminate_agent_process()
        self.media_ipc.cleanup_ipc_resources()
        self.pysignal_single_file_play_finished.emit()
        self.worker_status = 0
        log.debug("single play worker finished")

    def stop(self):
        self.force_stop = True

    def get_worker_status(self):
        return self.worker_status

    def play_status_change(self, status: int, src: str):
        self.play_status = status
        self.playing_source = src
        log.debug("self.playing_source : %s", self.playing_source)
        self.pysignal_single_file_play_status_change.emit(self.play_status, self.playing_source)

    def is_valid_file(self,file_uri):
        if os.path.isfile(file_uri):
            if os.path.getsize(file_uri) > 0:
                return True  # Return the index if a valid file is found
        log.debug("single file exists or empty.")
        return False

class Playing_HDMI_in_worker(QThread):
    pysignal_hdmi_play_status_change = pyqtSignal(int, str)
    pysignal_hdmi_play_finished = pyqtSignal()
    pysignal_refresh_image_pixmap = pyqtSignal(np.ndarray)
    pysignal_hdmi_play_audio = pyqtSignal(int)

    def __init__(self, media_engine: MediaEngine,
                 video_src):
        super().__init__()

        self.media_engine = media_engine
        self.media_ipc = MediaIpc(media_engine)
        self.video_params = self.media_engine.led_video_params
        self.video_src = video_src
        self.media_active_width = None
        self.media_active_height = None
        self.crop_visible_area_width = None
        self.crop_visible_area_height = None
        self.crop_position_x = None
        self.crop_position_y = None
        self.playing_source = None
        self.ff_process = self.media_engine.ff_process
        self.gst_pipeline = self.media_engine.gst_pipeline
        self.gst_appsink = None
        self.play_status = self.media_engine.playing_status
        self.output_width = self.media_engine.output_streaming_width
        self.output_height = self.media_engine.output_streaming_height
        self.output_fps = self.media_engine.output_streaming_fps
        self.raw_image = None
        self.image_from_pipe = None
        self.force_stop = False
        self.worker_status = 0
        self.audio_mutex = QMutex()

        self.play_status_change(PlayStatus.Initial, self.video_src)
        #atexit.register(self.stop)
        log.debug("Playing_HDMI_in_worker Init")

    def install_play_status_slot(self, slot_func):
        self.pysignal_hdmi_play_status_change.connect(slot_func)

    def install_pixmap_refreshed_slot(self, slot_func):
        self.pysignal_refresh_image_pixmap.connect(slot_func)

    def install_play_audio_slot(self, slot_func):
        self.pysignal_hdmi_play_audio.connect(slot_func)

    def play_status_change(self, status: int, src: str):
        self.play_status = status
        self.playing_source = src
        log.debug("self.playing_source : %s self.status %s", self.playing_source, self.play_status)
        self.pysignal_hdmi_play_status_change.emit(self.play_status, self.playing_source)

    def get_worker_status(self):
        return self.worker_status

    def terminate_pipeline(self, backend):
        """Terminates playback pipeline based on backend (ffmpeg or GStreamer)."""
        if backend == VideoBackendType.FFMPEG.value:
            if self.ff_process is not None:
                self.ff_process.kill()
            self.ff_process = None
            self.media_engine.ff_process = self.ff_process
        else:
            if self.gst_pipeline is not None:
                self.gst_pipeline.set_state(Gst.State.NULL)
                self.gst_pipeline = None
                self.media_engine.gst_pipeline = self.gst_pipeline

                if self.gst_appsink and self.gst_appsink.handler_is_connected(
                        self.gst_appsink.connect('new-sample', self.process_gst_frame_sample)):
                    self.gst_appsink.disconnect_by_func(self.process_gst_frame_sample)

    def handle_audio_playback(self, audio_play_status):
        self.audio_mutex.lock()
        try:
            if audio_play_status:
                if self.media_engine.pulse_audio_status is True:
                    if self.media_engine.hdmi_sound is not None and self.media_engine.headphone_sound is not None:
                        source_card, source_device = self.media_engine.hdmi_sound
                        sink_card, sink_device = self.media_engine.headphone_sound
                        self.media_engine.sound_device.start_play(source_card, source_device, sink_card, sink_device)
            else:
                self.media_engine.sound_device.stop_play()
        finally:
            self.audio_mutex.unlock()

    def start_GStreamer_stream(self):
        # Fetch the video resolution for the current file in the playlist
        resolution = self.media_engine.get_hdmi_resolution()

        # Update active media width and height if resolution is obtained
        if resolution:
            self.media_active_width, self.media_active_height = resolution

        # Debug output for active resolution
        log.debug("Active resolution - Width: %d, Height: %d", self.media_active_width, self.media_active_height)

        # Debug output for crop parameters
        log.debug("Configured crop dimensions - Width: %d, Height: %d",
                  self.video_params.get_hdmi_in_crop_w(),
                  self.video_params.get_hdmi_in_crop_h())

        # Configure cropping dimensions based on media and crop parameters
        if (self.video_params.get_hdmi_in_crop_w() is not None and
                self.video_params.get_hdmi_in_crop_h() is not None and
                self.media_active_width and self.media_active_height):
            self.crop_visible_area_width = min(self.video_params.get_hdmi_in_crop_w(), self.media_active_width)
            self.crop_visible_area_height = min(self.video_params.get_hdmi_in_crop_h(), self.media_active_height)
            self.crop_position_x = self.video_params.get_hdmi_in_start_x()
            self.crop_position_y = self.video_params.get_hdmi_in_start_y()

        # Debug output for final crop parameters
        log.debug("Crop configuration - Width: %d, Height: %d, Position X: %d, Position Y: %d",
                  self.crop_visible_area_width,
                  self.crop_visible_area_height,
                  self.crop_position_x,
                  self.crop_position_y)

        # Prepare audio and target frame rate settings
        audio_sink_str = 'default'
        if platform.machine() in ('arm', 'arm64', 'aarch64'):
            if self.media_engine.headphone_sound is not None:
                sink_card, sink_device = self.media_engine.headphone_sound
                audio_sink_str = f'hw:{sink_card},{sink_device}'
        target_fps_str = f"{self.output_fps}/1"

        # Construct GStreamer pipeline command
        gst_pipeline_str = get_gstreamer_cmd_for_media(
            self.video_src,
            width=self.output_width,
            height=self.output_height,
            target_fps=target_fps_str,
            i_width=self.media_active_width,
            i_height=self.media_active_height,
            c_width=self.crop_visible_area_width,
            c_height=self.crop_visible_area_height,
            c_pos_x=self.crop_position_x,
            c_pos_y=self.crop_position_y,
            audio_sink=audio_sink_str,
            audio_on=self.video_params.get_play_with_audio()
        )
        log.debug("gst-launch-1.0 %s", gst_pipeline_str)

        # Parse and launch the GStreamer pipeline
        self.gst_pipeline = Gst.parse_launch(gst_pipeline_str)
        self.gst_appsink = self.gst_pipeline.get_by_name('appsink_sink')
        self.gst_appsink.set_property('emit-signals', True)
        self.gst_appsink.set_property('sync', True)
        self.gst_appsink.connect('new-sample', self.process_gst_frame_sample)
        self.media_engine.gst_pipeline = self.gst_pipeline

        # Set the pipeline to PLAYING state and start monitoring bus messages
        bus = self.gst_pipeline.get_bus()
        self.play_status_change(PlayStatus.Playing, self.video_src)
        self.gst_pipeline.set_state(Gst.State.PLAYING)

        # Main loop to check for playback status and handle errors/stream end
        while not self.force_stop:

            if self.play_status == PlayStatus.Stop:
                self.gst_pipeline.set_state(Gst.State.NULL)
                break

            # Check for any errors or end-of-stream events
            msg = bus.timed_pop_filtered(100 * Gst.MSECOND, Gst.MessageType.ERROR | Gst.MessageType.EOS)
            if msg:
                if msg.type == Gst.MessageType.EOS:
                    log.debug('End of stream, restarting...')
                    break
                elif msg.type == Gst.MessageType.ERROR:
                    err, debug_info = msg.parse_error()
                    log.error(f"Error received: {err}, {debug_info}")
                    break
        log.debug("GStreamer hdmi in play end")

    def process_gst_frame_sample(self, sink=None):
        # Retrieve the video frame sample
        sample = sink.emit('pull-sample')
        buf = sample.get_buffer()
        result, self.image_from_pipe = buf.map(Gst.MapFlags.READ)

        self.worker_status = 1

        if result:
            try:
                # Convert video frame data to RGB and emit the updated frame
                self.raw_image = np.frombuffer(self.image_from_pipe.data, dtype=np.uint8).reshape(
                    (self.output_height, self.output_width, 3))
                self.pysignal_refresh_image_pixmap.emit(self.raw_image)

                if len(self.raw_image) <= 0:
                    log.debug("play end")
                    #self.media_ipc.terminate_agent_process()
                    return Gst.FlowReturn.EOS

                # Check if force stop is triggered
                if self.force_stop:
                    log.debug("self.force_stop is True, stopping gst_pipeline")
                    self.gst_pipeline.set_state(Gst.State.NULL)
                    return Gst.FlowReturn.EOS  # End processing

                if not self.media_ipc.wait_sem_write_access():
                    pass
                else:
                    self.media_ipc.write_to_shared_memory(self.image_from_pipe.data)

            finally:
                buf.unmap(self.image_from_pipe)  # Ensure buffer is released

        return Gst.FlowReturn.OK
    def start_ffmpeg_stream(self):

        while True:
            if self.play_status != PlayStatus.Stop:
                try:
                    if self.ff_process is not None:
                        if self.play_status == PlayStatus.Pausing:
                            os.kill(self.ff_process.pid, signal.SIGCONT)  # Continue process
                        else:
                            os.kill(self.ff_process.pid, signal.SIGTERM)  # Terminate process
                except Exception as e:
                    log.error(e)

            # Fetch the video resolution from media engine
            resolution = self.media_engine.get_hdmi_resolution()

            # Update active media width and height if resolution is obtained
            if resolution:
                self.media_active_width, self.media_active_height = resolution

            # Debug output for active resolution
            log.debug("Active resolution - Width: %d, Height: %d", self.media_active_width, self.media_active_height)

            # Debug output for crop parameters
            log.debug("Configured crop dimensions - Width: %d, Height: %d",
                      self.video_params.get_hdmi_in_crop_w(),
                      self.video_params.get_hdmi_in_crop_h())

            # Configure cropping dimensions based on media and crop parameters
            if (self.video_params.get_hdmi_in_crop_w() is not None and
                    self.video_params.get_hdmi_in_crop_h() is not None and
                    self.media_active_width and self.media_active_height):
                self.crop_visible_area_width = min(self.video_params.get_hdmi_in_crop_w(), self.media_active_width)
                self.crop_visible_area_height = min(self.video_params.get_hdmi_in_crop_h(), self.media_active_height)
                self.crop_position_x = self.video_params.get_hdmi_in_start_x()
                self.crop_position_y = self.video_params.get_hdmi_in_start_y()

            # Debug output for final crop parameters
            log.debug("Crop configuration - Width: %d, Height: %d, Position X: %d, Position Y: %d",
                      self.crop_visible_area_width,
                      self.crop_visible_area_height,
                      self.crop_position_x,
                      self.crop_position_y)
            audio_sink_str = 'default'

            if platform.machine() in ('arm', 'arm64', 'aarch64'):
                if self.media_engine.headphone_sound is not None:
                    sink_card, sink_device = self.media_engine.headphone_sound
                    audio_sink_str = f'hw:{sink_card},{sink_device}'
            target_fps_str = f"{self.output_fps}/1"

            ffmpeg_cmd = get_ffmpeg_cmd_for_media(self.video_src,
                                                  width=self.output_width, height=self.output_height,
                                                  target_fps=target_fps_str,
                                                  c_width=self.crop_visible_area_width,
                                                  c_height=self.crop_visible_area_height,
                                                  c_pos_x=self.crop_position_x,
                                                  c_pos_y=self.crop_position_y,
                                                  audio_sink=audio_sink_str,
                                                  audio_on=self.video_params.get_play_with_audio()
                                                  )
            log.debug("ffmpeg_cmd : %s", ffmpeg_cmd)

            try:
                self.ff_process = subprocess.Popen(ffmpeg_cmd, stdout=subprocess.PIPE, bufsize=10 ** 8, shell=True)
                self.media_engine.ff_process = self.ff_process
            except Exception as e:
                log.error(e)
            # write__flag_tmp = self.shm_sem.sem_post(sem_write_flag)
            if self.ff_process.pid > 0:
                self.play_status_change(PlayStatus.Playing, self.video_src)
                self.image_from_pipe = None
                while self.ff_process.pid > 0:
                    self.image_from_pipe = self.ff_process.stdout.read(self.output_width * self.output_height * 3)
                    #if len(self.image_from_pipe) <= 0:
                    if not self.image_from_pipe:
                        log.debug("play end")
                        #self.media_ipc.terminate_agent_process()
                        break
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

                    if not self.media_ipc.wait_sem_write_access():
                        pass
                    else :
                        self.media_ipc.write_to_shared_memory(self.image_from_pipe)

            log.debug("single play end")
            if self.media_engine.repeat_option == RepeatOption.Repeat_None:
                log.debug("stop play cause play end")
                break
            if self.force_stop is True:
                break
    def run(self):
        self.media_engine.sync_output_streaming_resolution()  # venom for output resolution correction
        self.worker_status = 1

        # Enable or disable audio based on settings
        self.media_engine.sound_device.stop_play()
        self.media_engine.audio_playing(self.video_params.get_play_with_audio())

        # Initialize shared memory and agent preview for media player
        if self.media_ipc.initialize_ipc_resources():
            if self.media_engine.video_backend == VideoBackendType.FFMPEG.value:
                self.start_ffmpeg_stream()
            else:
                self.start_GStreamer_stream()
        else:
            log.debug("initialize_ipc_resources failed")

        # Cleanup after playback ends
        self.play_status_change(PlayStatus.Stop, self.video_src)
        self.terminate_pipeline(self.media_engine.video_backend)
        self.media_ipc.terminate_agent_process()
        self.media_ipc.cleanup_ipc_resources()
        self.pysignal_hdmi_play_finished.emit()
        self.worker_status = 0
        log.debug("hdmi play worker finished")

    def stop(self):
        self.force_stop = True

class PlayCMSWorker(QObject):
    pysignal_cms_play_status_change = pyqtSignal(int, str)
    pysignal_cms_play_finished = pyqtSignal()
    pysignal_refresh_image_pixmap = pyqtSignal(np.ndarray)
    pysignal_send_raw_frame = pyqtSignal(bytes)

    def __init__(self, media_engine: MediaEngine, window_width, window_height, window_x, window_y,
                 c_width: int, c_height: int, c_pos_x: int, c_pos_y: int, ):
        super().__init__()

        self.media_engine = media_engine
        self.media_ipc = MediaIpc(media_engine)
        self.video_params = self.media_engine.led_video_params
        self.force_stop = False
        self.worker_status = 0
        self.force_stop_mutex = QMutex()
        self.play_status = None
        self.video_src = os.environ.get("DISPLAY", ":0.0")
        self.window_width = window_width
        self.window_height = window_height
        self.window_x = window_x
        self.window_y = window_y

        self.play_status_change(PlayStatus.Initial, "CMS")
        self.ff_process = self.media_engine.ff_process
        self.output_width = self.media_engine.output_streaming_width
        self.output_height = self.media_engine.output_streaming_height
        self.output_fps = self.media_engine.output_streaming_fps
        self.crop_visible_area_width = c_width
        self.crop_visible_area_height = c_height
        self.crop_position_x = c_pos_x
        self.crop_position_y = c_pos_y
        self.gst_appsink = None
        self.gst_pipeline = None
        self.media_active_height = None
        self.media_active_width = None
        self.playing_source = None
        self.image_from_pipe = None
        self.raw_image = None
        self.preview_window = None
        log.debug("CMS Instruction!")
        # To be implemented

    def install_play_status_slot(self, slot_func):
        log.debug("install_play_status_slot!")
        self.pysignal_cms_play_status_change.connect(slot_func)

    def install_pixmap_refreshed_slot(self, slot_func):
        log.debug("install_pixmap_refreshed_slot!")
        self.pysignal_refresh_image_pixmap.connect(slot_func)

    def install_send_raw_frame_slot(self, slot_func):
        log.debug("install_send_raw_frame_slot!")
        self.pysignal_send_raw_frame.connect(slot_func)

    def play_status_change(self, status: int, src: str):
        self.play_status = status
        self.playing_source = src
        log.debug("self.playing_source : %s", self.playing_source)
        self.pysignal_cms_play_status_change.emit(self.play_status, self.playing_source)

    def start_GStreamer_stream(self):
        # Fetch the video resolution from media engine
        resolution = self.media_engine.get_cms_resolution()

        # Update active media width and height if resolution is obtained
        if resolution:
            self.media_active_width, self.media_active_height = resolution

        # Debug output for active resolution
        log.debug("Active resolution - Width: %d, Height: %d", self.media_active_width, self.media_active_height)

        # Debug output for crop parameters
        log.debug("Configured crop dimensions - Width: %d, Height: %d",
                  self.video_params.get_cms_crop_w(),
                  self.video_params.get_cms_crop_h())

        # Configure cropping dimensions based on media and crop parameters
        if (self.video_params.get_cms_crop_w() is not None and
                self.video_params.get_cms_crop_h() is not None and
                self.media_active_width and self.media_active_height):
            self.crop_visible_area_width = min(self.video_params.get_cms_crop_w(), self.media_active_width)
            self.crop_visible_area_height = min(self.video_params.get_cms_crop_h(), self.media_active_height)
            self.crop_position_x = self.video_params.get_cms_start_x()
            self.crop_position_y = self.video_params.get_cms_start_y()

        # Debug output for final crop parameters
        log.debug("Crop configuration - Width: %d, Height: %d, Position X: %d, Position Y: %d",
                  self.crop_visible_area_width,
                  self.crop_visible_area_height,
                  self.crop_position_x,
                  self.crop_position_y)

        # Prepare audio and target frame rate settings
        audio_sink_str = 'default'
        if platform.machine() in ('arm', 'arm64', 'aarch64'):
            if self.media_engine.headphone_sound is not None:
                sink_card, sink_device = self.media_engine.headphone_sound
                audio_sink_str = f'hw:{sink_card},{sink_device}'
        target_fps_str = f"{self.output_fps}/1"

        # Construct GStreamer pipeline command
        gst_pipeline_str = get_gstreamer_cmd_for_media(
            self.video_src,
            width=self.output_width,
            height=self.output_height,
            target_fps=target_fps_str,
            i_width=self.media_active_width,
            i_height=self.media_active_height,
            c_width=self.crop_visible_area_width,
            c_height=self.crop_visible_area_height,
            c_pos_x=self.crop_position_x,
            c_pos_y=self.crop_position_y,
            window_x=self.window_x,
            window_y=self.window_y,
            audio_sink=audio_sink_str,
            audio_on=self.video_params.get_play_with_audio()
        )
        log.debug("gst-launch-1.0 %s", gst_pipeline_str)

        # Parse and launch the GStreamer pipeline
        self.gst_pipeline = Gst.parse_launch(gst_pipeline_str)
        self.gst_appsink = self.gst_pipeline.get_by_name('appsink_sink')
        self.gst_appsink.set_property('emit-signals', True)
        self.gst_appsink.set_property('sync', True)
        self.gst_appsink.connect('new-sample', self.process_gst_frame_sample)
        self.media_engine.gst_pipeline = self.gst_pipeline

        # Set the pipeline to PLAYING state and start monitoring bus messages
        bus = self.gst_pipeline.get_bus()
        self.play_status_change(PlayStatus.Playing, self.video_src)
        self.gst_pipeline.set_state(Gst.State.PLAYING)

        # Main loop to check for playback status and handle errors/stream end
        while not self.force_stop:

            if self.play_status == PlayStatus.Stop:
                self.gst_pipeline.set_state(Gst.State.NULL)
                break

            # Check for any errors or end-of-stream events
            msg = bus.timed_pop_filtered(100 * Gst.MSECOND, Gst.MessageType.ERROR | Gst.MessageType.EOS)
            if msg:
                if msg.type == Gst.MessageType.EOS:
                    log.debug('End of stream, restarting...')
                    break
                elif msg.type == Gst.MessageType.ERROR:
                    err, debug_info = msg.parse_error()
                    log.error(f"Error received: {err}, {debug_info}")
                    break
        log.debug("GStreamer hdmi in play end")

    def process_gst_frame_sample(self, sink=None):
        # Retrieve the video frame sample
        sample = sink.emit('pull-sample')
        buf = sample.get_buffer()
        result, self.image_from_pipe = buf.map(Gst.MapFlags.READ)

        self.worker_status = 1

        if result:
            try:
                # Convert video frame data to RGB and emit the updated frame
                self.raw_image = np.frombuffer(self.image_from_pipe.data, dtype=np.uint8).reshape(
                    (self.output_height, self.output_width, 3))
                self.pysignal_refresh_image_pixmap.emit(self.raw_image)

                if len(self.raw_image) <= 0:
                    log.debug("play end")
                    #self.media_ipc.terminate_agent_process()
                    return Gst.FlowReturn.EOS

                # Check if force stop is triggered
                if self.force_stop:
                    log.debug("self.force_stop is True, stopping gst_pipeline")
                    self.gst_pipeline.set_state(Gst.State.NULL)
                    return Gst.FlowReturn.EOS  # End processing

                if not self.media_ipc.wait_sem_write_access():
                    pass
                else:
                    self.media_ipc.write_to_shared_memory(self.image_from_pipe.data)

            finally:
                buf.unmap(self.image_from_pipe)  # Ensure buffer is released

        return Gst.FlowReturn.OK

    def start_ffmpeg_stream(self):

        while True:
            if self.play_status != PlayStatus.Stop:
                try:
                    if self.ff_process is not None:
                        if self.play_status == PlayStatus.Pausing:
                            os.kill(self.ff_process.pid, signal.SIGCONT)  # Continue process
                        else:
                            os.kill(self.ff_process.pid, signal.SIGTERM)  # Terminate process
                except Exception as e:
                    log.error(e)


            # Fetch the video resolution from media engine
            resolution = self.media_engine.get_cms_resolution()

            # Update active media width and height if resolution is obtained
            if resolution:
                self.media_active_width, self.media_active_height = resolution

            # Debug output for active resolution
            log.debug("Active resolution - Width: %d, Height: %d", self.media_active_width, self.media_active_height)

            # Debug output for crop parameters
            log.debug("Configured crop dimensions - Width: %d, Height: %d",
                      self.video_params.get_cms_crop_w(),
                      self.video_params.get_cms_crop_h())

            # Configure cropping dimensions based on media and crop parameters
            if (self.video_params.get_cms_crop_w() is not None and
                    self.video_params.get_cms_crop_h() is not None and
                    self.media_active_width and self.media_active_height):
                self.crop_visible_area_width = min(self.video_params.get_cms_crop_w(), self.media_active_width)
                self.crop_visible_area_height = min(self.video_params.get_cms_crop_h(), self.media_active_height)
                self.crop_position_x = self.video_params.get_cms_start_x()
                self.crop_position_y = self.video_params.get_cms_start_y()

            # Debug output for final crop parameters
            log.debug("Crop configuration - Width: %d, Height: %d, Position X: %d, Position Y: %d",
                      self.crop_visible_area_width,
                      self.crop_visible_area_height,
                      self.crop_position_x,
                      self.crop_position_y)
            audio_sink_str = 'default'

            if platform.machine() in ('arm', 'arm64', 'aarch64'):
                if self.media_engine.headphone_sound is not None:
                    sink_card, sink_device = self.media_engine.headphone_sound
                    audio_sink_str = f'hw:{sink_card},{sink_device}'
            target_fps_str = f"{self.output_fps}/1"

            ffmpeg_cmd = get_ffmpeg_cmd_for_media(self.video_src,
                                                  width=self.output_width, height=self.output_height,
                                                  target_fps=target_fps_str,
                                                  c_width=self.crop_visible_area_width,
                                                  c_height=self.crop_visible_area_height,
                                                  c_pos_x=self.crop_position_x,
                                                  c_pos_y=self.crop_position_y,
                                                  window_x = self.window_x,
                                                  window_y = self.window_y,
                                                  audio_sink=audio_sink_str,
                                                  audio_on=self.video_params.get_play_with_audio()
                                                  )

            log.debug("ffmpeg_cmd : %s", ffmpeg_cmd)

            try:
                self.ff_process = subprocess.Popen(ffmpeg_cmd, stdout=subprocess.PIPE, bufsize=10 ** 8, shell=True)
                self.media_engine.ff_process = self.ff_process
            except Exception as e:
                log.error(e)
            # write__flag_tmp = self.shm_sem.sem_post(sem_write_flag)
            if self.ff_process.pid > 0:
                self.play_status_change(PlayStatus.Playing, self.video_src)
                self.image_from_pipe = None
                while self.ff_process.pid > 0:
                    self.image_from_pipe = self.ff_process.stdout.read(self.output_width * self.output_height * 3)
                    # if len(self.image_from_pipe) <= 0:
                    if not self.image_from_pipe:
                        log.debug("play end")
                        # self.media_ipc.terminate_agent_process()
                        break
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

                    if not self.media_ipc.wait_sem_write_access():
                        pass
                    else:
                        self.media_ipc.write_to_shared_memory(self.image_from_pipe)

            log.debug("cms play end")
            # if self.media_engine.repeat_option == RepeatOption.Repeat_None:
            #     log.debug("stop play cause play end")
            #     break
            if self.force_stop is True:
                break
    def run(self):
        log.debug("cms go run!")

        self.media_engine.sync_output_streaming_resolution()  # venom for output resolution correction
        self.worker_status = 1

        # Initialize shared memory and agent preview for media player
        if self.media_ipc.initialize_ipc_resources():
            if self.media_engine.video_backend == VideoBackendType.FFMPEG.value:
                self.start_ffmpeg_stream()
            else:
                self.start_GStreamer_stream()
        else:
            log.debug("initialize_ipc_resources failed")

        # Cleanup after playback ends
        self.play_status_change(PlayStatus.Stop, "")
        self.terminate_pipeline(self.media_engine.video_backend)
        self.media_ipc.terminate_agent_process()
        self.media_ipc.cleanup_ipc_resources()
        self.pysignal_cms_play_finished.emit()
        self.worker_status = 0
        log.debug("play CMS worker finished")

    def stop(self):
        self.force_stop = True

    def get_worker_status(self):
        return self.worker_status

    def terminate_pipeline(self, backend):
        """Terminates playback pipeline based on backend (ffmpeg or GStreamer)."""
        if backend == VideoBackendType.FFMPEG.value:
            if self.ff_process is not None:
                self.ff_process.kill()
            self.ff_process = None
            self.media_engine.ff_process = self.ff_process
        else:
            if self.gst_pipeline is not None:
                self.gst_pipeline.set_state(Gst.State.NULL)
                self.gst_pipeline = None
                self.media_engine.gst_pipeline = self.gst_pipeline

                if self.gst_appsink and self.gst_appsink.handler_is_connected(
                        self.gst_appsink.connect('new-sample', self.process_gst_frame_sample)):
                    self.gst_appsink.disconnect_by_func(self.process_gst_frame_sample)

def test(self):
    log.debug("")
