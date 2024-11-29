from PyQt5.QtCore import QThread, pyqtSignal, QDateTime, QObject, QTimer, QMutex
import utils.log_utils
# import utils.net_utils
import os
import platform
import subprocess
from global_def import *


class TC358743(QObject):
    # connected, width, height, fps
    signal_refresh_tc358743_param = pyqtSignal(bool, int, int, int)

    def __init__(self, **kwargs):
        super(TC358743, self).__init__(**kwargs)

        self.connected = None
        self.width = None
        self.height = None
        self.fps = None

        self.res_set_dv_bt_timing = False
        self.video_device = self.get_video_device()
        if platform.machine() in ('arm', 'arm64', 'aarch64'):
            self.check_hdmi_status_mutex = QMutex()
        else:
            self.check_hdmi_status_mutex = None
        self.connected, self.width, self.height, self.fps = self.get_tc358743_dv_timing()
        self.res_set_dv_bt_timing = self.set_tc358743_dv_bt_timing()

    def reinit_tc358743_dv_timing(self):
        # log.debug("")
        self.connected, self.width, self.height, self.fps = self.get_tc358743_dv_timing()
        self.signal_refresh_tc358743_param.emit(self.connected, self.width, self.height, self.fps)

    def check_hdmi_status_lock(self):
        if self.check_hdmi_status_mutex is not None:
            self.check_hdmi_status_mutex.lock()

    def check_hdmi_status_unlock(self):
        if self.check_hdmi_status_mutex is not None:
            self.check_hdmi_status_mutex.unlock()

    def x86_get_video_timing(self):
        video_device = self.get_video_device()
        connected = False
        width = 0
        height = 0
        fps = 0

        p = os.popen("lsusb").read()
        if '322e:202c' not in p:
            return connected, width, height, fps

        if video_device is not None:
            connected = True
            result = subprocess.run(['v4l2-ctl', '--get-fmt-video', '-d', video_device], capture_output=True, text=True)
            if result.returncode == 0:
                lines = result.stdout.split('\n')
                count_max = 10
                for line in lines:
                    count_max = count_max - 1
                    if count_max == 0:
                        break
                    if "Width/Height" in line:
                        resolution = line.split(':')[1].strip()
                        parts = resolution.split('/')
                        if len(parts) == 2:
                            width, height = map(int, parts)
                        break

                result = subprocess.run(['v4l2-ctl', '--list-formats-ext', '-d', video_device], capture_output=True,
                                        text=True)
                if result.returncode == 0:
                    lines = result.stdout.split('\n')
                    count_max = 10
                    for line in lines:
                        count_max = count_max - 1
                        if count_max == 0:
                            break
                        if 'fps' in line:
                            try:
                                fps = int(float(line.split('(')[-1].split(' ')[0]))
                                break
                            except ValueError:
                                continue

        return connected, width, height, fps

    def get_tc358743_dv_timing(self):
        # log.debug("")
        connected = False
        width = 0
        height = 0
        fps = 0

        if platform.machine() in ('arm', 'arm64', 'aarch64'):
            pass
        else:
            connected, width, height, fps = self.x86_get_video_timing()
            return connected, width, height, fps
        self.check_hdmi_status_lock()
        dv_timings = os.popen("v4l2-ctl --query-dv-timings").read()
        self.check_hdmi_status_unlock()
        list_dv_timings = dv_timings.split("\n")

        if 'fail' in list_dv_timings[0]:
            log.debug("not connected")
            connected = False

            self.signal_refresh_tc358743_param.emit(connected, width, height, fps)
            return connected, width, height, fps
        else:
            connected = True
        if connected is True:
            for i in list_dv_timings:
                if 'Active width:' in i:
                    width = int(i.split(":")[1])
                if 'Active height:' in i:
                    height = int(i.split(":")[1])
                if 'Pixelclock' in i:
                    fps = int(float(i.split("(")[1].split(" ")[0]))

        # log.debug("width = %d", width)
        # log.debug("height = %d", height)
        # log.debug("fps = %d", fps)
        self.signal_refresh_tc358743_param.emit(connected, width, height, fps)
        return connected, width, height, fps

    def set_tc358743_dv_bt_timing(self):
        if platform.machine() in ('arm', 'arm64', 'aarch64'):
            pass
        else:
            return True
        self.check_hdmi_status_lock()
        res_set_dv_bt_timing = os.popen("v4l2-ctl --set-dv-bt-timings query").read()
        self.check_hdmi_status_unlock()
        # log.debug("res_set_dv_bt_timing = %s", res_set_dv_bt_timing)
        if 'BT timings set' in res_set_dv_bt_timing:
            # log.debug("set timing OK")
            return True
        log.debug("set timing NG")
        return False

    def get_tc358743_hdmi_info(self):
        connected = False
        width = 0
        height = 0
        fps = 0

        if platform.machine() in ('arm', 'arm64', 'aarch64'):
            pass
        else:
            p = os.popen("lsusb").read()
            # log.debug("lsusb : %s", p)
            if '322e:202c' not in p:
                log.debug("not connected")
                return connected, width, height, fps

        connected, width, height, fps = self.get_tc358743_dv_timing()

        return connected, width, height, fps


    def get_video_device(self):
        preferred_video = "/dev/video0" if platform.machine() in ('arm', 'arm64', 'aarch64') else "/dev/video10"
        if os.path.exists(preferred_video):
            return preferred_video
        else:
            return None

    def get_current_timing_info(self):
        return self.connected, self.width, self.height, self.fps
