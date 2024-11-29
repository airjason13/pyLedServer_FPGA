import subprocess
from sqlite3 import connect

from global_def import *

class VideoCaptureCard:

    def __init__(self, **kwargs):
        super(VideoCaptureCard, self).__init__(**kwargs)
        self.connected = None
        self.width = 1920
        self.height = 1080
        self.fps = 60

        self.default_hdmi_usb_ch_device = None
        self.hdmi_connected = None
        self.video_device = None

    def set_video_out_timing(self, device, width, height, fps):
        try:
            subprocess.run(
                ['v4l2-ctl', f'--device={device}', f'--set-fmt-video=width={width},height={height},pixelformat=MJPG'],
                check=True)
            subprocess.run(['v4l2-ctl', f'--device={device}', f'--set-parm={fps}'], check=True)
            log.debug(f"Video output timing set: device={device}, width={width}, height={height}, fps={fps}")
        except subprocess.CalledProcessError as e:
            log.debug(f"Failed to set video output timing: {e}")

    def find_video_device(self, describe):
        result = subprocess.run(['v4l2-ctl', '--list-devices'], stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                                text=True)
        output = result.stdout.split('\n')

        device_index = -1
        for i, line in enumerate(output):
            if describe in line:
                device_index = i
                break

        if device_index != -1 and device_index + 1 < len(output):
            device_info = output[device_index + 1].strip()
            if '/dev/video' in device_info:
                return device_info.split()[0]

        return None

    def update_video_device(self, video_device):
        self.video_device = video_device

    def get_video_device(self):
        return self.video_device

    def set_usb_hdmi_connected_status(self,status):
        self.hdmi_connected = status

    def get_usb_hdmi_connected_status(self):
        return self.hdmi_connected

    def get_usb_hdmi_info(self):
        current_video_device  = self.find_video_device(HdmiChSwitchDeviceMap.GoFanCo_Prophecy.description)
        self.update_video_device(current_video_device)
        connected = current_video_device
        self.set_usb_hdmi_connected_status(True if connected else False)
        return self.hdmi_connected , self.width , self.height ,self.fps