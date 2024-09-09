import enum
import os
import sys
from version import *
import platform
import utils.log_utils

log = utils.log_utils.logging_init(__file__)

root_dir = os.path.dirname(sys.modules['__main__'].__file__)
LD_PATH = root_dir + "/ext_binaries/"

FPGA_START_ID = 2

if platform.machine() in ('arm', 'arm64', 'aarch64'):
    if "pi5" in platform.node():  # pi5
        SU_PWD = 'workout13'
        ETH_DEV = 'end0'
    else:  # pi4-64
        SU_PWD = 'workout13'
        ETH_DEV = 'eth0'
else:
    # x86 base, you should define your own superuser password and eth device
    SU_PWD = 'workout13'
    ETH_DEV = 'enp55s0'

Version = (
    "{}{}{}_{}{}{}".format(Version_Year, Version_Month, Version_Date,
                           Version_Major, Version_Minor, Version_Patch))

if platform.machine() in ('arm', 'arm64', 'aarch64'):
    internal_media_folder = "/home/root/Videos"
else:
    internal_media_folder = "/home/venom/Videos"

ThumbnailFileFolder = "/.thumbnails/"
PlaylistFolder = "/.playlists/"
SubtitleFolder = "/.subtitle_data"


class play_type(enum.IntEnum):
    play_none = 0
    play_single = 1
    play_playlist = 2
    play_hdmi_in = 3
    play_cms = 4


'''class play_type(enum.IntEnum):
    play_none = 0
    play_single = 1
    play_playlist = 2
    play_hdmi_in = 3
    play_cms = 4'''


class frame_brightness_alog(enum.IntEnum):
    fix_mode = 0
    auto_time_mode = 1
    auto_als_mode = 2
    test_mode = 3


class sleep_mode(enum.IntEnum):
    disable = 0
    enable = 1


class icled_type(enum.IntEnum):
    anapex = 0
    aos = 1

'''icled_type = { 
                "ANAPEX": 0,
                "AOS":  1,
}'''

BRIGHTNESS_TIMER_INTERVAL = 1 * 1000

MIN_FRAME_BRIGHTNESS = 0
MAX_FRAME_BRIGHTNESS = 100

MIN_FRAME_GAMMA = 0
MAX_FRAME_GAMMA = 2.5
