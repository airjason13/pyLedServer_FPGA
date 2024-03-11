import enum
import os
import platform
import signal
import subprocess
import time
import atexit

import numpy as np
from PyQt5.QtCore import QObject, pyqtSignal, QMutex, QThread

import utils.utils_file_access
from ext_qt_widgets.playing_preview_widget import PlayingPreviewWindow
from media_engine.media_engine_def import PlayStatus, RepeatOption
from utils.utils_ffmpy import get_ffmpeg_cmd_with_playing_media_file_
from utils.utils_file_access import get_led_config_from_file_uri, get_int_led_config_from_file_uri
from utils.utils_system import get_eth_interface
from media_configs.video_params import VideoParams
from global_def import log, root_dir, ETH_DEV, SU_PWD
import socket
from multiprocessing import shared_memory
from ctypes import *
from media_engine.linux_ipc_pyapi_sem import *


class MediaEngine(QObject):
    signal_media_play_status_changed = pyqtSignal(bool, str)
    hdmi_play_status_changed = pyqtSignal(bool, str)

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
        self.play_change_mutex = QMutex()

        self.playing_preview_window = PlayingPreviewWindow()

        self.shm_sem_write_uri = "/shm_write_sem"
        self.shm_sem_read_uri = "/shm_read_sem"

        os.system("pkill -f show_ffmpeg_shared_memory")

        self.play_single_file_thread = None
        self.play_single_file_worker = None
        self.play_hdmi_in_thread = None
        self.play_hdmi_in_worker = None

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
        self.play_change_mutex.lock()
        self.playing_status = status
        if self.playing_status == PlayStatus.Stop:
            self.playing_preview_window.setVisible(False)
        if playing_src == "/dev/video0":
            self.hdmi_play_status_changed.emit(status, playing_src)
        else:
            self.signal_media_play_status_changed.emit(status, playing_src)
        self.play_change_mutex.unlock()
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
        # stop play first
        self.stop_play()
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
        log.debug("enter stop_play!\n")
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

        if self.play_hdmi_in_worker is not None:
            self.resume_playing()
            self.play_hdmi_in_worker.stop()
            if self.ff_process is not None:
                os.kill(self.ff_process.pid, signal.SIGTERM)
            try:
                if self.play_hdmi_in_thread is not None:
                    self.play_hdmi_in_thread.quit()
                for i in range(10):
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

        self.playing_preview_window.close_window()
        log.debug("exit stop_play!\n")

    def install_hdmi_play_status_changed_slot(self, slot_func):
        self.hdmi_play_status_changed.connect(slot_func)

    def hdmi_in_play(self, video_src):
        self.play_hdmi_in_thread = QThread()
        self.play_hdmi_in_worker = Playing_HDMI_in_worker(self, video_src, with_audio=True, with_preview=True)
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
                    os.kill(self.ff_process.pid, signal.SIGSTOP)
                    self.playing_status = PlayStatus.Pausing
            except Exception as e:
                log.debug(e)

    def resume_playing(self):
        if self.playing_status != PlayStatus.Stop:
            log.debug("enter resume_play!\n")
            try:
                if self.ff_process is not None:
                    os.kill(self.ff_process.pid, signal.SIGCONT)
                    self.playing_status = PlayStatus.Playing
            except Exception as e:
                log.debug(e)


class PlaySingleFileWorker(QObject):
    pysignal_single_file_play_status_change = pyqtSignal(int, str)
    pysignal_single_file_play_finished = pyqtSignal()
    pysignal_refresh_image_pixmap = pyqtSignal(np.ndarray)
    pysignal_send_raw_frame = pyqtSignal(bytes)

    def __init__(self, media_engine: MediaEngine, file_uri, with_audio: bool, with_preview: bool):
        super().__init__()
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
        subprocess.Popen("pkill -f show_ffmpeg_shared_memory", shell=True)
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

                    subprocess.Popen("pkill -f show_ffmpeg_shared_memory", shell=True)
                    time.sleep(3)

                if self.shm != None:
                    break

            self.shm_sem = LinuxIpcSemaphorePyapi()
            # Init the write sem
            sem_write_flag = self.shm_sem.sem_open(self.media_engine.shm_sem_write_uri, os.O_CREAT, 0x666, 1)
            if sem_write_flag == 0:
                log.error("failed to create sem: %s", self.media_engine.shm_sem_write_uri)
                return -1

            # Init the read sem
            sem_read_flag = self.shm_sem.sem_open(self.media_engine.shm_sem_read_uri, os.O_CREAT, 0x666, 0)
            if sem_read_flag == 0:
                log.error("failed to create sem: %s", self.media_engine.shm_sem_read_uri)
                return -1

            ffmpeg_cmd = get_ffmpeg_cmd_with_playing_media_file_(self.file_uri,
                                                                 width=self.output_width, height=self.output_height,
                                                                 target_fps="24/1", image_period=20)
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

    def __init__(self, media_engine: MediaEngine, video_src, with_audio: bool, with_preview: bool):
        super().__init__()
        self.command = None
        self.playing_source = None
        self.media_engine = media_engine
        self.video_src = video_src
        self.play_with_audio = with_audio
        self.play_with_preview = with_preview
        self.ff_process = self.media_engine.ff_process
        self.play_status = self.media_engine.playing_status
        self.output_width = self.media_engine.output_streaming_width
        self.output_height = self.media_engine.output_streaming_height
        self.play_status_change(PlayStatus.Initial, self.video_src)
        self.raw_image = None
        self.image_from_pipe = None
        self.force_stop = False
        self.worker_status = 0

        atexit.register(self.stop)
        log.debug("Playing_HDMI_in_worker Init")

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

    def stop(self):
        # self.worker_status = 0
        self.force_stop = True
        if self.ff_process:
            self.ff_process.terminate()
            # self.ff_process.stdout.close()
            # self.ff_process = None
            self.play_status_change(PlayStatus.Stop, self.video_src)
            log.debug("FFmpeg process and pipe closed.")
    def exist(self,pid):
        try:
            os.kill(pid, 0)
        except OSError:
            return False  # process does not exist
        else:
            return True  # process exists

    def run(self):

        try:
            scale_factor = "scale=" + str(self.output_width) + ":" + str(self.output_height)
            self.command = ['ffmpeg', '-hide_banner', '-stream_loop', '-1', '-loglevel', 'error', '-hwaccel', 'auto',
                            '-i', self.video_src, '-f', 'image2pipe', '-pix_fmt', 'rgb24', '-vcodec', 'rawvideo', '-vf',
                            scale_factor, '-r', '27/1', '-']
            while True:
                self.ff_process = subprocess.Popen(self.command, stdout=subprocess.PIPE, bufsize=10 ** 8)
                self.media_engine.ff_process = self.ff_process

                if self.ff_process.pid > 0:
                    self.play_status_change(PlayStatus.Playing, self.video_src)
                    self.worker_status = 1

                while self.worker_status:

                    self.image_from_pipe = self.ff_process.stdout.read(self.output_width * self.output_height * 3)

                    if not self.image_from_pipe:
                        log.debug("No data read from the pipe.")
                        break

                    self.raw_image = np.frombuffer(self.image_from_pipe, dtype='uint8')
                    self.raw_image = self.raw_image.reshape((self.output_height, self.output_width, 3))

                    if self.ff_process is not None:
                        self.ff_process.stdout.flush()

                    if self.play_with_preview is True:
                        self.pysignal_refresh_image_pixmap.emit(self.raw_image)

                if self.force_stop is True:
                    log.debug("self.force_stop is True, ready to kill ff_process")
                    if self.ff_process is not None:
                        os.kill(self.ff_process.pid, signal.SIGTERM)
                    break

            self.pysignal_hdmi_play_finished.emit()
        except Exception as e:
            log.debug("Error in VideoThreadFFMpeg run method: %s", e)
        finally:
            self.stop()
def test(self):
    log.debug("")
