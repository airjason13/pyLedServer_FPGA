import enum
import os
import platform
import re
import signal
import subprocess
import time
import atexit
import select

import numpy as np
import psutil
from PyQt5.QtCore import QObject, pyqtSignal, QMutex, QThread

import utils.utils_file_access
from ext_qt_widgets.playing_preview_widget import PlayingPreviewWindow
from media_engine.media_engine_def import PlayStatus, RepeatOption
from media_engine.sound_device import SoundDevices, mute_audio_sinks
from utils.utils_ffmpy import get_ffmpeg_cmd_for_media, get_media_resolution_from_ffmpeg
from utils.utils_file_access import get_led_config_from_file_uri, get_int_led_config_from_file_uri
from utils.utils_system import get_eth_interface
from media_configs.video_params import VideoParams
from global_def import log, root_dir, ETH_DEV, SU_PWD
import socket
from multiprocessing import shared_memory
from ctypes import *
from media_engine.linux_ipc_pyapi_sem import *


class MediaEngine(QObject):
    signal_media_play_status_changed = pyqtSignal(int, str)
    hdmi_play_status_changed = pyqtSignal(int, str)

    def __init__(self):
        super(MediaEngine, self).__init__()
        self.ff_process = None
        self.hdmi_sound = None
        self.headphone_sound = None
        self.pulse_audio_status = None
        self.output_streaming_fps = None
        self.output_streaming_height = None
        self.output_streaming_width = None
        self.play_single_file_thread = None
        self.play_single_file_worker = None
        self.play_hdmi_in_thread = None
        self.play_hdmi_in_worker = None
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
        self.hdmi_active_width = 0
        self.hdmi_active_height = 0

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

        if need_restart_streaming is True:
            # if play status == 1, restreaming.
            if self.playing_status == 1:
                if self.play_single_file_worker is not None:
                    log.debug("re-play single play file uri: %s", self.play_single_file_worker.file_uri)
                    file_uri = self.play_single_file_worker.file_uri
                    self.stop_play()
                    resolution = self.get_video_resolution(file_uri)
                    if resolution is not None:
                        media_active_width, media_active_height = resolution
                    self.single_play(file_uri,
                                     active_width=media_active_width,
                                     active_height=media_active_width,
                                     audio_active=self.led_video_params.get_play_with_audio(),
                                     preview_visible=True
                                     )
                elif self.play_hdmi_in_worker is not None:
                    log.debug("HDMI-In re-play need to be test")
                    video_src = self.play_hdmi_in_worker.video_src

                    # self.stop_play()
                    # self.hdmi_in_play(video_src, )

    def install_signal_media_play_status_changed_slot(self, slot_func):
        self.signal_media_play_status_changed.connect(slot_func)

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

        if "/dev/video" in playing_src:
            self.hdmi_play_status_changed.emit(status, playing_src)
        else:
            self.signal_media_play_status_changed.emit(status, playing_src)
        self.play_change_mutex.unlock()

    def preview_pixmap_changed(self, raw_image_np_array):
        # log.debug("preview_pixmap_changed")
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
            self.playing_preview_window.setVisible(True)
        self.playing_preview_window.refresh_image(raw_image_np_array)

    def single_play(self, file_uri, **kwargs):

        log.debug("single play file uri: %s", file_uri)
        audio_active = kwargs.get('audio_active', True)
        preview_visible = kwargs.get('preview_visible', True)
        active_width = kwargs.get('active_width', 0)
        active_height = kwargs.get('active_height', 0)
        c_width = 0
        c_height = 0
        c_pos_x = 0
        c_pos_y = 0

        log.debug("active_width = %d", active_width)
        log.debug("active_height = %d", active_height)
        log.debug("self.led_video_params.get_media_file_crop_w() = %d", self.led_video_params.get_media_file_crop_w())
        log.debug("self.led_video_params.get_media_file_crop_h() = %d", self.led_video_params.get_media_file_crop_h())

        if (self.led_video_params.get_media_file_crop_w() is not None
                and self.led_video_params.get_media_file_crop_h() is not None
                and active_width and active_height):
            c_width = min(self.led_video_params.get_media_file_crop_w(), active_width)
            c_height = min(self.led_video_params.get_media_file_crop_h(), active_height)
            c_pos_x = self.led_video_params.get_media_file_start_x()
            c_pos_y = self.led_video_params.get_media_file_start_y()

        # stop play first
        self.stop_play()
        self.play_single_file_thread = QThread()
        log.debug("c_width = %d", c_width)
        log.debug("c_height = %d", c_height)
        log.debug("c_pos_x = %d", c_pos_x)
        log.debug("c_pos_y = %d", c_pos_y)
        self.play_single_file_worker = PlaySingleFileWorker(self, file_uri,
                                                            with_audio=audio_active,
                                                            with_preview=preview_visible,
                                                            c_width=c_width, c_height=c_height,
                                                            c_pos_x=c_pos_x, c_pos_y=c_pos_y
                                                            )
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
        log.debug("enter stop_play!\n")

        if self.play_single_file_worker is not None:
            self.play_single_file_worker.stop()
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

        if self.play_hdmi_in_worker is not None:
            self.resume_playing()
            self.play_hdmi_in_worker.stop()
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
                if self.play_hdmi_in_thread is not None:
                    self.play_hdmi_in_thread.quit()
                for i in range(5):
                    log.debug("self.play_hdmi_in_thread.isFinished() = %d",
                              self.play_hdmi_in_thread.isFinished())
                    if self.play_hdmi_in_thread.isFinished() is True:
                        break
                    time.sleep(1)

                log.debug("play_hdmi_in_thread is not None A2")
                self.play_hdmi_in_thread.wait()
                self.play_hdmi_in_thread.exit(0)
            except Exception as e:
                log.debug(e)
            self.play_hdmi_in_worker = None
            self.play_hdmi_in_thread = None

        self.sound_device.stop_play()
        self.playing_preview_window.close_window()

        log.debug("exit stop_play!\n")

    def install_hdmi_play_status_changed_slot(self, slot_func):
        self.hdmi_play_status_changed.connect(slot_func)

    def hdmi_in_play(self, video_src, **kwargs):
        '''audio_active = kwargs.get('audio_active', True)
        preview_visible = kwargs.get('preview_visible', True)
        active_width = kwargs.get('active_width')
        active_height = kwargs.get('active_height')'''
        audio_active = self.led_video_params.get_play_with_audio()
        log.debug("preview visible need to be implement")
        preview_visible = self.led_video_params.get_play_with_audio()
        self.hdmi_active_width = kwargs.get('active_width')
        self.hdmi_active_height = kwargs.get('active_height')
        c_width = None
        c_height = None
        c_pos_x = 0
        c_pos_y = 0
        if (self.led_video_params.get_hdmi_in_crop_w() is not None
                and self.led_video_params.get_hdmi_in_crop_h() is not None):
            c_width = min(self.led_video_params.get_hdmi_in_crop_w(), self.hdmi_active_width)
            c_height = min(self.led_video_params.get_hdmi_in_crop_h(), self.hdmi_active_height)
            c_pos_x = self.led_video_params.get_hdmi_in_start_x()
            c_pos_y = self.led_video_params.get_hdmi_in_start_y()
        self.play_hdmi_in_thread = QThread()
        self.play_hdmi_in_worker = Playing_HDMI_in_worker(self, video_src,
                                                          with_audio=audio_active,
                                                          with_preview=preview_visible,
                                                          c_width=c_width, c_height=c_height,
                                                          c_pos_x=c_pos_x, c_pos_y=c_pos_y,
                                                          )
        self.play_hdmi_in_worker.install_play_status_slot(self.play_status_changed)
        self.play_hdmi_in_worker.moveToThread(self.play_hdmi_in_thread)

        self.play_hdmi_in_thread.started.connect(self.play_hdmi_in_worker.run)
        self.play_hdmi_in_worker.pysignal_hdmi_play_finished.connect(self.play_hdmi_in_thread.quit)
        self.play_hdmi_in_worker.pysignal_hdmi_play_finished.connect(self.play_hdmi_in_worker.deleteLater)
        self.play_hdmi_in_thread.finished.connect(self.play_hdmi_in_thread.deleteLater)
        self.play_hdmi_in_worker.install_pixmap_refreshed_slot(self.preview_pixmap_changed)
        self.play_hdmi_in_thread.start()

    def pause_playing(self):
        if self.playing_status != PlayStatus.Stop:
            log.debug("enter pause_play!\n")
            try:
                if self.ff_process is not None:
                    sub_ff_process = self.find_child("ffmpeg", self.ff_process.pid)
                    if sub_ff_process:
                        sub_ff_process.suspend()
                    else:
                        os.kill(self.ff_process.pid, signal.SIGSTOP)
                    self.playing_status = PlayStatus.Pausing
                if self.sound_device.audio_process is not None:
                    mute_audio_sinks(True)
                if self.play_hdmi_in_worker is not None:
                    self.play_status_changed(self.playing_status, self.play_hdmi_in_worker.video_src)
                if self.play_single_file_thread is not None:
                    self.play_status_changed(self.playing_status, self.play_single_file_worker.file_uri)

            except Exception as e:
                log.debug(e)

    def resume_playing(self):
        if self.playing_status != PlayStatus.Stop:
            log.debug("enter resume_play!\n")
            try:
                if self.ff_process is not None:
                    sub_ff_process = self.find_child("ffmpeg", self.ff_process.pid)
                    if sub_ff_process:
                        sub_ff_process.resume()
                    else:
                        os.kill(self.ff_process.pid, signal.SIGCONT)
                    self.playing_status = PlayStatus.Playing
                if self.sound_device.audio_process is not None:
                    mute_audio_sinks(False)
                if self.play_hdmi_in_worker is not None:
                    self.play_status_changed(self.playing_status, self.play_hdmi_in_worker.video_src)
                if self.play_single_file_thread is not None:
                    self.play_status_changed(self.playing_status, self.play_single_file_worker.file_uri)
            except Exception as e:
                log.debug(e)

    def find_child(self, child_name, parent_pid):
        parent = psutil.Process(parent_pid)
        for child in parent.children(recursive=True):
            if child_name in child.name():
                return child
        return None

    def get_video_resolution(self, file_uri):
        try:
            # fix blank file name
            # ffmpeg_cmd = get_media_resolution_from_ffmpeg(file_uri)
            ffmpeg_cmd = ['ffprobe', '-v', 'error', '-select_streams', 'v:0', '-show_entries', 'stream=width,height',
                          '-of', 'csv=s=x:p=0', file_uri]
            self.ff_process = subprocess.Popen(ffmpeg_cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                                               text=True)
            output, error = self.ff_process.communicate()
            # log.debug("output : %s", output)
            # log.debug("error : %s", error)
            match = re.search(r'(\d{2,5})x(\d{2,5})', output)
            if match:
                width, height = map(int, match.groups())
                if (0 < width <= 4096 and
                        0 < height <= 3112):
                    return width, height
            return None, None
        except Exception as e:
            log.debug(f"Error processing video file: {str(e)}")
            return None, None
        finally:
            if self.ff_process and self.ff_process.poll() is None:
                self.ff_process.kill()


class PlaySingleFileWorker(QObject):
    pysignal_single_file_play_status_change = pyqtSignal(int, str)
    pysignal_single_file_play_finished = pyqtSignal()
    pysignal_refresh_image_pixmap = pyqtSignal(np.ndarray)
    pysignal_send_raw_frame = pyqtSignal(bytes)

    def __init__(self, media_engine: MediaEngine, file_uri, c_width: int, c_height: int,
                 c_pos_x: int, c_pos_y: int, with_audio: bool, with_preview: bool):
        super().__init__()
        self.shm_sem = None
        self.shm = None
        self.agent_process = None
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
        self.output_fps = self.media_engine.output_streaming_fps
        self.crop_visible_area_width = c_width
        self.crop_visible_area_height = c_height
        self.crop_position_x = c_pos_x
        self.crop_position_y = c_pos_y
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

    def play_status_change(self, status: int, src: str):
        self.play_status = status
        self.playing_source = src
        log.debug("self.playing_source : %s", self.playing_source)
        self.pysignal_single_file_play_status_change.emit(self.play_status, self.playing_source)

    def run(self):
        try_wain_write_count_max = 5000
        if platform.machine() in ('arm', 'arm64', 'aarch64'):
            try_wain_write_count_max = 500
        try_wait_write_count = 0
        self.media_engine.sync_output_streaming_resolution()  # venom for output resolution correction
        subprocess.Popen("pkill -9 -f show_ffmpeg_shared_memory", shell=True)
        # kill_agent_cmd = "sudo -S pkill -f show_ffmpeg_shared_memory"
        # su_kill_agent_cmd = 'echo {} | '.format(SU_PWD) + kill_agent_cmd
        # log.debug("su_kill_agent_cmd : %s", kill_agent_cmd)
        # os.system(su_kill_agent_cmd)

        time.sleep(1)

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
            self.shm = None
            while True:
                try:
                    # find agent preview window pos
                    line = os.popen("xdpyinfo | awk '/dimensions/{print $2}'").read()
                    tmp = line.split("x")
                    geo_w = int(tmp[0])
                    geo_h = int(tmp[1])

                    if self.output_width >= 1280 or self.output_height >= 720:
                        preview_pos_x = geo_w - 640
                        preview_pos_y = 320
                    else:
                        preview_pos_x = geo_w - self.output_width
                        preview_pos_y = 320

                    # handle raw socket agent
                    os.environ['SDL_VIDEO_WINDOW_POS'] = "%d,%d" % (preview_pos_x, preview_pos_y)
                    ld_path = root_dir + "/ext_binaries"
                    agent_cmd = (
                            "%s/ext_binaries/show_ffmpeg_shared_memory %s %d %d 0 "
                            % (root_dir, ETH_DEV, self.output_width, self.output_height))
                    log.debug("agent_cmd : %s", agent_cmd)
                    self.agent_process = subprocess.Popen(agent_cmd, shell=True)
                    log.debug("self.agent_process.pid : %d", self.agent_process.pid)
                    time.sleep(1)
                    # self.agent_process = subprocess.Popen(agent_cmd, shell=True)
                    # log.debug("self.agent_process.pid = %d\n", self.agent_process.pid)
                    self.shm = shared_memory.SharedMemory("posixsm", False, 0x400000)
                except Exception as e:
                    log.fatal(e)

                    subprocess.Popen("pkill -9 -f show_ffmpeg_shared_memory", shell=True)
                    time.sleep(3)

                if self.shm is not None:
                    break

            self.shm_sem = LinuxIpcSemaphorePyapi()
            # Init write sem
            sem_write_flag = self.shm_sem.sem_open(self.media_engine.shm_sem_write_uri, os.O_CREAT, 0x666, 1)
            if sem_write_flag == 0:
                log.error("failed to create sem: %s", self.media_engine.shm_sem_write_uri)
                return -1

            # Init the read sem
            sem_read_flag = self.shm_sem.sem_open(self.media_engine.shm_sem_read_uri, os.O_CREAT, 0x666, 0)
            if sem_read_flag == 0:
                log.error("failed to create sem: %s", self.media_engine.shm_sem_read_uri)
                return -1

            audio_sink_str = 'default'
            if platform.machine() in ('arm', 'arm64', 'aarch64'):
                if self.media_engine.headphone_sound is not None:
                    sink_card, sink_device = self.media_engine.headphone_sound
                    audio_sink_str = f'hw:{sink_card},{sink_device}'
            target_fps_str = f"{self.output_fps}/1"

            ffmpeg_cmd = get_ffmpeg_cmd_for_media(self.file_uri,
                                                  width=self.output_width, height=self.output_height,
                                                  target_fps=target_fps_str, image_period=20,
                                                  c_width=self.crop_visible_area_width,
                                                  c_height=self.crop_visible_area_height,
                                                  c_pos_x=self.crop_position_x,
                                                  c_pos_y=self.crop_position_y,
                                                  audio_sink=audio_sink_str, audio_on=self.play_with_audio
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
                        if self.agent_process is not None:
                            self.agent_process.kill()
                        break

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

                    write_flag_tmp = self.shm_sem.sem_trywait(sem_write_flag)
                    if write_flag_tmp == -1:
                        try_wait_write_count += 1
                        if try_wait_write_count > 500:
                            try_wait_write_count = 0
                            log.error("missing agent!")
                            subprocess.Popen("pkill -f show_ffmpeg_shared_memory", shell=True)
                            '''kill_agent_cmd = "sudo -S pkill -f show_ffmpeg_shared_memory"
                            su_kill_agent_cmd = 'echo {} | '.format(SU_PWD) + kill_agent_cmd
                            log.debug("su_kill_agent_cmd : %s", kill_agent_cmd)
                            os.system(su_kill_agent_cmd)'''
                            time.sleep(1)
                            ld_path = root_dir + "/ext_binaries"
                            agent_cmd = (
                                    "%s/ext_binaries/show_ffmpeg_shared_memory %s %d %d 0 "
                                    % (root_dir, ETH_DEV, self.output_width, self.output_height))
                            log.debug("agent_cmd : %s", agent_cmd)
                            subprocess.Popen(agent_cmd, shell=True)
                            '''agent_cmd = (
                                    "LD_LIBRARY_PATH=%s %s/ext_binaries/show_ffmpeg_shared_memory %s %s %d %d 0 &"
                                    % (ld_path, root_dir, os.getlogin(), ETH_DEV, self.output_width, self.output_height))
                            # su_agent_cmd = 'echo {} | sudo -S '.format(SU_PWD) + agent_cmd
                            # os.system(su_agent_cmd)
                            su_agent_cmd = agent_cmd
                            os.system(su_agent_cmd)'''
                        continue
                    else:
                        try_wait_write_count = 0

                    to_write = memoryview(self.image_from_pipe)
                    self.shm._buf[:len(to_write)] = to_write[:]
                    # post the read
                    read_flag_tmp = self.shm_sem.sem_post(sem_read_flag)

            log.debug("single play end")
            if self.media_engine.repeat_option == RepeatOption.Repeat_None:
                log.debug("stop play cause play end")
                break
            if self.force_stop is True:
                break
        self.shm_sem.sem_close(sem_write_flag)
        self.shm_sem.sem_unlink(self.media_engine.shm_sem_write_uri)
        self.shm_sem.sem_close(sem_read_flag)
        self.shm_sem.sem_unlink(self.media_engine.shm_sem_read_uri)

        self.play_status_change(PlayStatus.Stop, "")
        self.worker_status = 0
        self.pysignal_single_file_play_finished.emit()
        self.ff_process.kill()
        self.ff_process = None
        if self.agent_process is not None:
            self.agent_process.kill()
            self.agent_process = None
        log.debug("single play worker finished")

    def stop(self):
        self.force_stop = True

    def get_worker_status(self):
        return self.worker_status


class Playing_HDMI_in_worker(QThread):
    pysignal_hdmi_play_status_change = pyqtSignal(int, str)
    pysignal_hdmi_play_finished = pyqtSignal()
    pysignal_refresh_image_pixmap = pyqtSignal(np.ndarray)

    def __init__(self, media_engine: MediaEngine,
                 video_src, c_width: int, c_height: int,
                 c_pos_x: int, c_pos_y: int, with_audio: bool,
                 with_preview: bool):
        super().__init__()
        self.ffmpeg_cmd = None
        self.agent_cmd = None
        self.agent_process = None
        self.sem_read_flag = None
        self.sem_write_flag = None
        self.shm_sem = None
        self.shm = None
        self.playing_source = None
        self.media_engine = media_engine
        self.video_params = self.media_engine.led_video_params
        self.video_src = video_src
        self.play_with_audio = with_audio
        self.play_with_preview = with_preview
        self.crop_visible_area_width = c_width
        self.crop_visible_area_height = c_height
        self.crop_position_x = c_pos_x
        self.crop_position_y = c_pos_y
        self.ff_process = self.media_engine.ff_process
        self.play_status = self.media_engine.playing_status
        self.output_width = self.media_engine.output_streaming_width
        self.output_height = self.media_engine.output_streaming_height
        self.output_fps = self.media_engine.output_streaming_fps
        self.play_status_change(PlayStatus.Initial, self.video_src)
        self.raw_image = None
        self.image_from_pipe = None
        self.force_stop = False
        self.worker_status = 0
        self.process_release_mutex = QMutex()

        atexit.register(self.stop)
        log.debug("Playing_HDMI_in_worker Init")
        self.setup_shared_memory_and_semaphore()

    def install_play_status_slot(self, slot_func):
        self.pysignal_hdmi_play_status_change.connect(slot_func)

    def install_pixmap_refreshed_slot(self, slot_func):
        self.pysignal_refresh_image_pixmap.connect(slot_func)

    def play_status_change(self, status: int, src: str):
        self.play_status = status
        self.playing_source = src
        log.debug("self.playing_source : %s self.status %s", self.playing_source, self.play_status)
        self.pysignal_hdmi_play_status_change.emit(self.play_status, self.playing_source)

    def get_worker_status(self):
        return self.worker_status

    def get_ff_pid(self):
        # Check if ff_process exists and is not None
        if self.ff_process and hasattr(self.ff_process, 'pid'):
            return self.ff_process.pid
        else:
            # If ff_process does not exist or does not have a pid attribute, return 0 to indicate an invalid PID
            return 0

    def setup_shared_memory_and_semaphore(self):
        # find agent preview window pos
        line = os.popen("xdpyinfo | awk '/dimensions/{print $2}'").read().strip()
        screen_width, screen_height = map(int, line.split("x"))
        preview_pos_x = screen_width - (
            640 if self.output_width >= 1280 or self.output_height >= 720 else self.output_width)
        preview_pos_y = 320
        # handle raw socket agent
        os.environ['SDL_VIDEO_WINDOW_POS'] = f"{preview_pos_x},{preview_pos_y}"
        self.agent_cmd = f"{root_dir}/ext_binaries/show_ffmpeg_shared_memory {ETH_DEV} {self.output_width} {self.output_height} 0"

    def restart_agent(self):
        # Terminate the current agent process and start a new one
        if self.agent_process:
            self.agent_process.terminate()
            self.agent_process.wait(timeout=5)
        self.agent_process = subprocess.Popen(self.agent_cmd, shell=True)
        log.debug("Agent process restarted with PID: {}".format(self.agent_process.pid))

    def init_shared_resources(self):
        # Initialize shared memory
        self.shm = shared_memory.SharedMemory("posixsm", False, 0x400000)
        if not self.shm:
            log.debug("Failed to initialize shared memory.")
            return

        # Initialize semaphores
        self.shm_sem = LinuxIpcSemaphorePyapi()
        self.sem_write_flag = self.shm_sem.sem_open(self.media_engine.shm_sem_write_uri, os.O_CREAT, 0o666, 1)
        if self.sem_write_flag == 0:
            log.debug("Failed to create write semaphore.")
            return
        self.sem_read_flag = self.shm_sem.sem_open(self.media_engine.shm_sem_read_uri, os.O_CREAT, 0o666, 0)
        if self.sem_read_flag == 0:
            log.debug("Failed to create read semaphore.")
            return

    def restart_shm_and_sem(self):
        # Reset shared memory and semaphores
        try:
            self.shm.close()
            self.shm.unlink()
        except AttributeError:
            pass  # Ignore if self.shm has not been initialized
        except Exception as e:
            log.debug("Error handling old shared memory: {}".format(e))

        # Create new shared memory and semaphores
        self.init_shared_resources()
        log.debug("Shared memory and semaphores restarted successfully.")

    def write_to_shm(self, data):
        if not self.shm:
            log.debug("Shared memory is not initialized.")
            self.restart_shm_and_sem()
            return False

        if self.shm_sem.sem_trywait(self.sem_write_flag) != -1:
            try:
                data_size = len(data)
                if data_size > self.shm.size:
                    log.debug(f"Data size ({data_size}) exceeds shared memory size ({self.shm.size}).")
                    return False

                self.shm.buf[:data_size] = data
                self.shm_sem.sem_post(self.sem_read_flag)
            except Exception as e:
                log.debug(f"Error writing to shared memory: {e}")
        else:
            if not self.agent_process or self.agent_process.poll() is not None:
                log.debug("Missing agent! Trying to restart the shared memory agent.")
                self.restart_agent()
                time.sleep(1)
                self.play_status_change(self.play_status, self.video_src)
                if not self.agent_process:
                    log.debug("Failed to restart the agent. Aborting write operation.")
                    return False
        return True

    def read_from_shm(self):
        if not self.shm:
            log.debug("Shared memory not initialized.")
            return None

        self.shm_sem.sem_wait(self.sem_read_flag)
        data = self.shm.buf[:self.output_width * self.output_height * 3]
        image = np.frombuffer(data, dtype=np.uint8).reshape((self.output_height, self.output_width, 3))
        self.shm_sem.sem_post(self.sem_write_flag)
        return image

    def cleanup_resources(self):
        self.process_release_mutex.lock()
        if self.shm:
            log.debug("shm closed.")
            self.shm.close()
            self.shm.unlink()
            self.shm = None
        if self.shm_sem:
            if self.sem_write_flag:
                log.debug("sem_write_flag closed.")
                self.shm_sem.sem_close(self.sem_write_flag)
                self.shm_sem.sem_unlink(self.media_engine.shm_sem_write_uri)
                self.sem_write_flag = 0
            if self.sem_read_flag:
                log.debug("sem_read_flag closed.")
                self.shm_sem.sem_close(self.sem_read_flag)
                self.shm_sem.sem_unlink(self.media_engine.shm_sem_read_uri)
                self.sem_read_flag = 0
            self.shm_sem = None
        if self.agent_process:
            log.debug("agent_process closed.")
            try:
                self.agent_process.terminate()
                self.agent_process.wait(timeout=3)
            except subprocess.TimeoutExpired:
                log.debug("agent process termination timed out. Forcing kill.")
                self.agent_process.kill()
            except Exception as e:
                log.debug(f"An error occurred while stopping the agent: {e}")
            finally:
                self.agent_process = None
        if self.ff_process:
            log.debug("ff_process closed.")
            try:
                self.ff_process.terminate()
                self.ff_process.wait(timeout=3)
            except subprocess.TimeoutExpired:
                log.debug("FFmpeg process termination timed out. Forcing kill.")
                self.ff_process.kill()
            except Exception as e:
                log.debug(f"An error occurred while stopping the ff_process: {e}")
            finally:
                self.ff_process = None
        self.play_status_change(PlayStatus.Stop, self.video_src)
        self.process_release_mutex.unlock()

    def run(self):
        if self.play_status != PlayStatus.Stop:
            p = subprocess.run(["pgrep", "ffmpeg"], capture_output=True, text=True)
            if p.stdout:
                subprocess.run(["pkill", "-9", "-f", "ffmpeg"])
        self.media_engine.sound_device.stop_play()
        time.sleep(1)
        self.restart_agent()
        time.sleep(1)
        self.restart_shm_and_sem()
        self.force_stop = False

        self.media_engine.sync_output_streaming_resolution()  # venom for output resolution correction

        try:
            target_fps_str = f"{self.output_fps}/1"
            self.ffmpeg_cmd = get_ffmpeg_cmd_for_media(self.video_src,
                                                       width=self.output_width,
                                                       height=self.output_height,
                                                       target_fps=target_fps_str,
                                                       c_width=self.crop_visible_area_width,
                                                       c_height=self.crop_visible_area_height,
                                                       c_pos_x=self.crop_position_x,
                                                       c_pos_y=self.crop_position_y,
                                                       )
            if self.play_with_audio is True:
                if self.media_engine.pulse_audio_status is True:
                    if self.media_engine.hdmi_sound is not None and self.media_engine.headphone_sound is not None:
                        source_card, source_device = self.media_engine.hdmi_sound
                        sink_card, sink_device = self.media_engine.headphone_sound
                        self.media_engine.sound_device.start_play(source_card, source_device, sink_card, sink_device)

            while True:

                if self.ff_process and self.ff_process.poll() is None:
                    self.ff_process.terminate()
                    try:
                        self.ff_process.wait(timeout=2)
                    except subprocess.TimeoutExpired:
                        log.debug("ff_process termination timeout.")
                    self.ff_process = None

                try:
                    self.ff_process = subprocess.Popen(self.ffmpeg_cmd.split(), stdout=subprocess.PIPE, bufsize=10 ** 8)
                    if self.ff_process.pid > 0:
                        log.debug(f"ff_process started: {self.ff_process.pid}")
                        self.play_status_change(PlayStatus.Playing, self.video_src)
                        self.worker_status = 1
                except Exception as e:
                    log.debug(f"ff_process Failed: {e}")

                self.media_engine.ff_process = self.ff_process

                while self.worker_status and self.force_stop is False:

                    data_ready, _, _ = select.select([self.ff_process.stdout], [], [], 3000)

                    if data_ready:
                        self.image_from_pipe = self.ff_process.stdout.read(self.output_width * self.output_height * 3)
                        if not self.image_from_pipe:
                            if self.agent_process is not None:
                                self.agent_process.kill()
                            log.debug("Pipe read attempt returned no data.")
                            break
                    else:
                        log.debug("No data available from pipe.")
                        break

                    self.raw_image = np.frombuffer(self.image_from_pipe, dtype='uint8')
                    self.raw_image = self.raw_image.reshape((self.output_height, self.output_width, 3))

                    if self.ff_process is not None:
                        self.ff_process.stdout.flush()

                    if self.image_from_pipe:
                        raw_image_array = np.array(self.raw_image)
                        self.write_to_shm(raw_image_array.tobytes())

                    if self.play_with_preview is True:
                        self.pysignal_refresh_image_pixmap.emit(self.raw_image)

                if self.force_stop is True:
                    log.debug("self.force_stop is True")
                    break

            self.cleanup_resources()
            self.pysignal_hdmi_play_finished.emit()

        except Exception as e:
            log.debug("Error in VideoThreadFFMpeg run method: %s", e)
        finally:
            self.stop()

    def stop(self):
        log.debug("FFmpeg process and pipe closed.")
        self.force_stop = True
        self.cleanup_resources()


def test(self):
    log.debug("")
