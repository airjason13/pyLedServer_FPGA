import glob
import os
import re
import sys

from astral_hashmap import City_Map
from global_def import log, internal_media_folder, PlaylistFolder, play_type, root_dir

led_params_config_folder_name = "led_config"
led_params_config_file_name = "led_parameters"
led_reboot_config_file_name = "reboot_config"
ext_eth_config_file_name = "ext_eth_setting.dat"
cms_config_file_name = "cms_mode_url.dat"

mp4_extends = internal_media_folder + "/*.mp4"
jpeg_extends = internal_media_folder + "/*.jpeg"
jpg_extends = internal_media_folder + "/*.jpg"
png_extends = internal_media_folder + "/*.png"
webp_extends = internal_media_folder + '/*.webp'
playlist_extends = internal_media_folder + PlaylistFolder + "*.playlist"

WLAN0_ENABLE_TAG = "WLAN0_ENABLE"
SSID_DEFAULT_TAG = "SSID_DEFAULT"
BAND_DEFAULT_TAG = "BAND_DEFAULT"
CHANNEL_DEFAULT_TAG = "CHANNEL_DEFAULT"

band_channel_not_supported_list = [12, 13, 14, 38, 42, 46, 144]

def init_video_params():
    content_lines = [
        "led_brightness=50\n",
        "icled_type=0\n"
        "led_gamma=2.2\n",
        "led_r_gain=1\n",
        "led_b_gain=1\n",
        "led_g_gain=1\n",
        "sleep_mode_enable=1\n",
        "target_city_index=0\n",
        "frame_brightness_algorithm=0\n",
        "day_mode_frame_brightness=50\n",
        "night_mode_frame_brightness=30\n",
        "sleep_mode_frame_brightness=0\n",
        "image_period=6000\n",
        "hdmi_in_start_x=0\n",
        "hdmi_in_start_y=0\n",
        "hdmi_in_crop_w=0\n",
        "hdmi_in_crop_h=0\n",
        "media_file_start_x=0\n",
        "media_file_start_y=0\n",
        "media_file_crop_w=0\n",
        "media_file_crop_h=0\n",
        "output_frame_width=640\n",
        "output_frame_height=480\n",
        "output_fps=24\n",
        "play_with_audio=0\n",
        "play_with_preview=0\n",
    ]
    root_dir = os.path.dirname(sys.modules['__main__'].__file__)
    led_config_dir = os.path.join(root_dir, led_params_config_folder_name)
    file_uri = os.path.join(led_config_dir, led_params_config_file_name)
    config_file = open(file_uri, 'w')
    config_file.writelines(content_lines)
    config_file.close()
    os.system('sync')


def init_reboot_params():
    content_lines = [
        "reboot_mode_enable=0\n",
        "reboot_time=04:30\n",
    ]
    root_dir = os.path.dirname(sys.modules['__main__'].__file__)
    led_config_dir = os.path.join(root_dir, led_params_config_folder_name)
    file_uri = os.path.join(led_config_dir, led_reboot_config_file_name)
    config_file = open(file_uri, 'w')
    config_file.writelines(content_lines)
    config_file.close()
    os.system('sync')


def get_city_list() -> list:
    city_list = []
    for city in City_Map:
        city_list.append(city.get("City"))

    return city_list


def get_reboot_mode_default() -> str:
    reboot_mode = "Disable"
    root_dir = os.path.dirname(sys.modules['__main__'].__file__)
    led_config_dir = os.path.join(root_dir, led_params_config_folder_name)
    if os.path.isfile(os.path.join(led_config_dir, led_reboot_config_file_name)) is False:
        init_reboot_params()

    with open(os.path.join(led_config_dir, led_reboot_config_file_name), "r") as f:
        lines = f.readlines()
    f.close()
    for line in lines:
        if "reboot_mode_enable" in line:
            i_reboot_mode = line.strip("\n").split("=")[1]
            if i_reboot_mode == "1":
                reboot_mode = "Enable"
                # log.debug("reboot_mode : %s", reboot_mode)
                return reboot_mode
            else:
                # log.debug("reboot_mode : %s", reboot_mode)
                return reboot_mode
    log.debug("reboot_mode : %s", reboot_mode)
    return reboot_mode


def get_sleep_mode_default() -> str:
    sleep_mode = "Disable"
    root_dir = os.path.dirname(sys.modules['__main__'].__file__)
    led_config_dir = os.path.join(root_dir, led_params_config_folder_name)
    if os.path.isfile(os.path.join(led_config_dir, led_params_config_file_name)) is False:
        init_video_params()

    with open(os.path.join(led_config_dir, led_params_config_file_name), "r") as f:
        lines = f.readlines()
    f.close()
    for line in lines:
        tag = line.split("=")[0]
        if "sleep_mode_enable" == tag:
            i_sleep_mode = line.strip("\n").split("=")[1]
            if i_sleep_mode == "1":
                sleep_mode = "Enable"
                return sleep_mode
            else:
                return sleep_mode
    return sleep_mode


def get_target_city_default() -> str:
    city_index = 0
    target_city = City_Map[city_index].get("City")
    root_dir = os.path.dirname(sys.modules['__main__'].__file__)
    led_config_dir = os.path.join(root_dir, led_params_config_folder_name)
    if os.path.isfile(os.path.join(led_config_dir, led_params_config_file_name)) is False:
        init_video_params()

    with open(os.path.join(led_config_dir, led_params_config_file_name), "r") as f:
        lines = f.readlines()
    f.close()
    for line in lines:
        tag = line.split("=")[0]
        if tag == "target_city_index":
            city_index = int(line.strip("\n").split("=")[1])
            target_city = City_Map[city_index].get("City")
    return target_city


def get_brightness_mode_default() -> str:
    root_dir = os.path.dirname(sys.modules['__main__'].__file__)
    led_config_dir = os.path.join(root_dir, led_params_config_folder_name)

    str_ret = 'fix_mode'
    # log.debug("video_params file is %s: ", os.path.join(led_config_dir, ".video_params_config"))
    if os.path.exists(os.path.join(led_config_dir, led_params_config_file_name)) is False:
        init_video_params()

    with open(os.path.join(led_config_dir, led_params_config_file_name), "r+") as f:
        lines = f.readlines()
    for line in lines:
        if "frame_brightness_algorithm" in line:
            tmp = line.strip("\n").split("=")[1]
            if int(tmp) == 0:
                str_ret = 'Fix Mode'
            elif int(tmp) == 1:
                str_ret = 'Time Mode'
            elif int(tmp) == 2:
                str_ret = 'ALS Mode'
            elif int(tmp) == 3:
                str_ret = 'TEXT Mode'
    f.close()
    return str_ret


def get_frame_rate_res_default():
    root_dir = os.path.dirname(sys.modules['__main__'].__file__)
    led_config_dir = os.path.join(root_dir, led_params_config_folder_name)
    frame_rate_res_maps = {}

    if os.path.exists(os.path.join(led_config_dir, led_params_config_file_name)) is False:
        init_video_params()

    with open(os.path.join(led_config_dir, led_params_config_file_name), "r+") as f:
        lines = f.readlines()

    for line in lines:
        tag = line.split("=")[0]
        if "output_frame_width" == tag:
            str_fr_w = line.strip("\n").split("=")[1]
            frame_rate_res_maps["output_frame_width"] = str_fr_w
        elif "output_frame_height" == tag:
            str_fr_h = line.strip("\n").split("=")[1]
            frame_rate_res_maps["output_frame_height"] = str_fr_h
        elif "output_fps" == tag:
            str_fr_rate = line.strip("\n").split("=")[1]
            frame_rate_res_maps["output_fps"] = str_fr_rate

    f.close()

    return frame_rate_res_maps


def get_brightness_value_default():
    root_dir = os.path.dirname(sys.modules['__main__'].__file__)
    led_config_dir = os.path.join(root_dir, led_params_config_folder_name)
    brightness_values_maps = {}

    str_fr_br = "0"
    str_fr_br_day_mode = "0"
    str_fr_br_night_mode = "0"
    str_fr_br_sleep_mode = "0"
    if os.path.exists(os.path.join(led_config_dir, led_params_config_file_name)) is False:
        init_video_params()

    with open(os.path.join(led_config_dir, led_params_config_file_name), "r+") as f:
        lines = f.readlines()

    for line in lines:
        tag = line.split("=")[0]
        if "led_brightness" == tag:
            str_fr_br = line.strip("\n").split("=")[1]
            brightness_values_maps["frame_brightness"] = str_fr_br
        elif "day_mode_frame_brightness" == tag:
            str_fr_br_day_mode = line.strip("\n").split("=")[1]
            brightness_values_maps["day_mode_frame_brightness"] = str_fr_br_day_mode
        elif "night_mode_frame_brightness" == tag:
            str_fr_br_night_mode = line.strip("\n").split("=")[1]
            brightness_values_maps["night_mode_frame_brightness"] = str_fr_br_night_mode
        elif "sleep_mode_frame_brightness" == tag:
            str_fr_br_sleep_mode = line.strip("\n").split("=")[1]
            brightness_values_maps["sleep_mode_frame_brightness"] = str_fr_br_sleep_mode

    f.close()

    return brightness_values_maps


def get_default_play_mode_default():
    try:
        str_ret = ""
        with open(os.getcwd() + "/static/default_launch_type.dat", "r") as launch_type_config_file:
            tmp = launch_type_config_file.readline()
            log.debug("launch_type_config : %s", tmp)
            default_launch_type_int = int(tmp.split(":")[0])
            default_launch_params_str = tmp.split(":")[1]
            if default_launch_type_int == 0:
                str_ret = "none_mode"
            elif default_launch_type_int == 1:
                str_ret = "single_file_mode"
            elif default_launch_type_int == 2:
                str_ret = "playlist_mode"
            elif default_launch_type_int == 3:
                str_ret = "hdmi_in_mode"
            elif default_launch_type_int == 4:
                str_ret = "cms_mode"
            # log.debug("str_ret :%s", str_ret)
            return str_ret
    except Exception as e:
        log.debug(e)
    return "none_mode"


def get_playlist_list():
    playlist_list = []
    for playlist_tmp in sorted(glob.glob(playlist_extends)):
        # log.debug("playlist_tmp = %s", playlist_tmp)
        if os.path.isfile(playlist_tmp):
            fname_url = playlist_tmp.split("/")
            fname = fname_url[len(fname_url) - 1]
            # log.debug("fname : %s", fname)
            playlist_list.append(fname)
    if len(playlist_list) == 0:
        playlist_list.append("")
    return playlist_list


def get_playlist_default():
    try:
        with open(os.getcwd() + "/static/default_launch_type.dat", "r") as launch_type_config_file:
            tmp = launch_type_config_file.read()
            default_launch_type_int = int(tmp.split(":")[0])
            default_launch_type_params_str = tmp.split(":")[1]
            if default_launch_type_int == play_type.play_playlist:
                return default_launch_type_params_str
            else:
                return get_playlist_list()[0]
    except Exception as e:
        log.debug(e)

    return get_playlist_list()[0]

def get_wifi_devices_default():
    output = os.popen("nmcli --get-values GENERAL.DEVICE,GENERAL.TYPE device show | sed '/^wifi/!{h;d;};x'").read()

    devs = output.strip().split("\n")
    real_devs = []
    for i in range(len(devs)):
        log.debug("dev: %s", devs[i])
        if 'p2p' in devs[i]:
            pass
        else:
            real_devs.append(devs[i])

    log.debug("real_devs: %s", real_devs)
    return real_devs[0]

def get_wifi_bands_channels_default():

    target_channel = 0
    ret_channel = ""
    ''' get phy0 support channels '''
    output = os.popen("iw {} info | grep dBm ".format('phy0')).read()
    tmp = re.sub(r"[\t\* ]*", "", output)
    log.debug("tmp type : %s", type(tmp))
    channels_list = tmp.split("\n")
    log.debug("channels_list type : %s", type(channels_list))

    ''' get target config file definition'''
    led_config_dir = os.path.join(root_dir, 'led_config')
    with open(os.path.join(led_config_dir, "setup_wlan0_hotspot.sh.target"), "r") as f:
        lines = f.readlines()
    f.close()

    for line in lines:
        if line.startswith(CHANNEL_DEFAULT_TAG):
            log.debug("line: %s", line)
            target_channel = line.strip().split("=")[1]
    log.debug("target_channel: %s", target_channel)

    for channel in channels_list:
        if "MHz" in channel:
            # log.debug("channel: %s", channel)
            # log.debug("channel test %s", channel.split("[")[1].split("]")[0])
            if target_channel == channel.split("[")[1].split("]")[0]:
                log.debug("bingo, target_channel = %s", channel)
                ret_channel = channel

    return ret_channel

def get_wifi_bands_channels_tuple():
    tuple = []
    output = os.popen("iw {} info | grep dBm ".format('phy0')).read()
    tmp = re.sub(r"[\t\* ]*", "", output)
    # log.debug("tmp type : %s", type(tmp))
    channels_list = tmp.split("\n")
    # log.debug("channels_list type : %s", type(channels_list))
    for channel in channels_list:
        # log.debug("channel : %s", channel)
        if "[" in channel:
            tmp_str_channel_number = channel.split("[")[1].split("]")[0]
            tmp_int_channel_number = int(tmp_str_channel_number)
            if tmp_int_channel_number in band_channel_not_supported_list:
                pass
                # log.debug("channel %d not supported", tmp_int_channel_number)
            else:
                tuple.append((channel, channel))
    return tuple

def get_internal_wifi_ssid_default():
    # get target config file definition
    led_config_dir = os.path.join(root_dir, 'led_config')
    with open(os.path.join(led_config_dir, "setup_wlan0_hotspot.sh.target"), "r") as f:
        lines = f.readlines()
    f.close()
    for line in lines:
        if line.startswith(SSID_DEFAULT_TAG):
            tmp = line.strip().split("=")[1]
            if tmp == "GISTLED":
                default_ssid = tmp + "_SN"
            else:
                default_ssid = tmp
            return default_ssid

    return "default_wifi_ssid"


def get_ext_wifi_ssid_default():
    log.debug("To be implemented")
    return "ext_wifi_ssid"

def get_wifi_bands_default():
    log.debug("To be Implemented!")
    return "2.4G"

def get_wifi_channels_default():
    log.debug("To be Implemented!")
    return "11"


def get_icled_type_default():
    i_icled_type = 0
    s_icled_type = 'anapex'
    root_dir = os.path.dirname(sys.modules['__main__'].__file__)
    led_config_dir = os.path.join(root_dir, led_params_config_folder_name)
    if os.path.exists(os.path.join(led_config_dir, led_params_config_file_name)) is False:
        init_video_params()

    with open(os.path.join(led_config_dir, led_params_config_file_name), "r+") as f:
        lines = f.readlines()

    for line in lines:
        if 'icled_type' in line:
            i_icled_type = int(line.strip("\n").split("=")[1])
    if i_icled_type == 1:
        s_icled_type = 'aos'
    else:
        s_icled_type = 'anapex'
    log.debug("icled_type : %s", s_icled_type)
    f.close()
    return s_icled_type


def get_still_image_period_default():
    s_image_period = 0
    root_dir = os.path.dirname(sys.modules['__main__'].__file__)
    led_config_dir = os.path.join(root_dir, led_params_config_folder_name)
    if os.path.exists(os.path.join(led_config_dir, led_params_config_file_name)) is False:
        init_video_params()

    with open(os.path.join(led_config_dir, led_params_config_file_name), "r+") as f:
        lines = f.readlines()

    for line in lines:
        if 'image_period' in line:
            i_icled_type = int(line.strip("\n").split("=")[1])
            i_icled_type = i_icled_type / 1000
            s_image_period = str(i_icled_type)

    f.close()
    return s_image_period


def get_audio_enable_default():
    s_audio_enable = '0'
    root_dir = os.path.dirname(sys.modules['__main__'].__file__)
    led_config_dir = os.path.join(root_dir, led_params_config_folder_name)
    if os.path.exists(os.path.join(led_config_dir, led_params_config_file_name)) is False:
        init_video_params()

    with open(os.path.join(led_config_dir, led_params_config_file_name), "r+") as f:
        lines = f.readlines()

    for line in lines:
        if 'play_with_audio' in line:
            i_audio_enable = int(line.strip("\n").split("=")[1])
            s_audio_enable = str(i_audio_enable)

    f.close()
    return s_audio_enable


def get_preview_enable_default():
    s_preview_enable = '0'
    root_dir = os.path.dirname(sys.modules['__main__'].__file__)
    led_config_dir = os.path.join(root_dir, led_params_config_folder_name)
    if os.path.exists(os.path.join(led_config_dir, led_params_config_file_name)) is False:
        init_video_params()

    with open(os.path.join(led_config_dir, led_params_config_file_name), "r+") as f:
        lines = f.readlines()

    for line in lines:
        if 'play_with_audio' in line:
            i_preview_enable = int(line.strip("\n").split("=")[1])
            s_preview_enable = str(s_preview_enable)

    f.close()
    return s_preview_enable


def get_icled_current_gain_values_default():
    root_dir = os.path.dirname(sys.modules['__main__'].__file__)
    led_config_dir = os.path.join(root_dir, led_params_config_folder_name)
    current_gain_values_maps = {}

    if os.path.exists(os.path.join(led_config_dir, led_params_config_file_name)) is False:
        init_video_params()

    with open(os.path.join(led_config_dir, led_params_config_file_name), "r+") as f:
        lines = f.readlines()

    for line in lines:
        tag = line.split("=")[0]
        if "led_r_gain" == tag:
            str_led_r_gain = line.strip("\n").split("=")[1]
            current_gain_values_maps["led_r_gain"] = str_led_r_gain
        elif "led_g_gain" == tag:
            str_led_g_gain = line.strip("\n").split("=")[1]
            current_gain_values_maps["led_g_gain"] = str_led_g_gain
        elif "led_b_gain" == tag:
            str_led_b_gain = line.strip("\n").split("=")[1]
            current_gain_values_maps["led_b_gain"] = str_led_b_gain

    f.close()

    return current_gain_values_maps


def get_media_crop_values_default():
    root_dir = os.path.dirname(sys.modules['__main__'].__file__)
    led_config_dir = os.path.join(root_dir, led_params_config_folder_name)
    media_crop_values_maps = {}

    if os.path.exists(os.path.join(led_config_dir, led_params_config_file_name)) is False:
        init_video_params()

    with open(os.path.join(led_config_dir, led_params_config_file_name), "r+") as f:
        lines = f.readlines()

    for line in lines:
        tag = line.split("=")[0]
        if "media_file_start_x" == tag:
            str_media_file_start_x = line.strip("\n").split("=")[1]
            media_crop_values_maps["media_file_start_x"] = str_media_file_start_x
        elif "media_file_start_y" == tag:
            str_media_file_start_y = line.strip("\n").split("=")[1]
            media_crop_values_maps["media_file_start_y"] = str_media_file_start_y
        elif "media_file_crop_w" == tag:
            str_media_file_crop_w = line.strip("\n").split("=")[1]
            media_crop_values_maps["media_file_crop_w"] = str_media_file_crop_w
        elif "media_file_crop_h" == tag:
            str_media_file_crop_h = line.strip("\n").split("=")[1]
            media_crop_values_maps["media_file_crop_h"] = str_media_file_crop_h

    f.close()

    return media_crop_values_maps


def get_hdmi_crop_values_default():
    root_dir = os.path.dirname(sys.modules['__main__'].__file__)
    led_config_dir = os.path.join(root_dir, led_params_config_folder_name)
    hdmi_crop_values_maps = {}

    if os.path.exists(os.path.join(led_config_dir, led_params_config_file_name)) is False:
        init_video_params()

    with open(os.path.join(led_config_dir, led_params_config_file_name), "r+") as f:
        lines = f.readlines()

    for line in lines:
        tag = line.split("=")[0]
        if "hdmi_in_start_x" == tag:
            str_hdmi_file_start_x = line.strip("\n").split("=")[1]
            hdmi_crop_values_maps["hdmi_in_start_x"] = str_hdmi_file_start_x
        elif "hdmi_in_start_y" == tag:
            str_media_file_start_y = line.strip("\n").split("=")[1]
            hdmi_crop_values_maps["hdmi_in_start_y"] = str_media_file_start_y
        elif "hdmi_in_crop_w" == tag:
            str_hdmi_in_crop_w = line.strip("\n").split("=")[1]
            hdmi_crop_values_maps["hdmi_in_crop_w"] = str_hdmi_in_crop_w
        elif "hdmi_in_crop_h" == tag:
            str_hdmi_in_crop_h = line.strip("\n").split("=")[1]
            hdmi_crop_values_maps["hdmi_in_crop_h"] = str_hdmi_in_crop_h

    f.close()

    return hdmi_crop_values_maps

def get_sleep_start_time_default():
    sleep_start_time = "11:50"
    root_dir = os.path.dirname(sys.modules['__main__'].__file__)
    led_config_dir = os.path.join(root_dir, 'led_config')
    if os.path.isfile(os.path.join(led_config_dir, "sleep_time_config")) is False:
        init_sleep_time_params()
        # init_reboot_params()

    with open(os.path.join(led_config_dir, "sleep_time_config"), "r") as f:
        lines = f.readlines()
    f.close()
    for line in lines:
        if "sleep_start_time" in line:
            sleep_start_time = line.split("=")[1]
    # log.debug("sleep_start_time = %s", sleep_start_time)
    return sleep_start_time

def init_sleep_time_params():
    content_lines = [
        "sleep_start_time=00:30\n",
        "sleep_end_time=04:30\n",
    ]
    root_dir = os.path.dirname(sys.modules['__main__'].__file__)
    led_config_dir = os.path.join(root_dir, 'led_config')
    file_uri = os.path.join(led_config_dir, "sleep_time_config")
    config_file = open(file_uri, 'w')
    config_file.writelines(content_lines)
    config_file.close()
    os.system('sync')

def get_sleep_end_time_default():
    sleep_end_time = "11:50"
    root_dir = os.path.dirname(sys.modules['__main__'].__file__)
    led_config_dir = os.path.join(root_dir, 'led_config')
    if os.path.isfile(os.path.join(led_config_dir, "sleep_time_config")) is False:
        init_sleep_time_params()
        # init_reboot_params()

    with open(os.path.join(led_config_dir, "sleep_time_config"), "r") as f:
        lines = f.readlines()
    f.close()
    for line in lines:
        if "sleep_end_time" in line:
            sleep_end_time = line.split("=")[1]
    # log.debug("sleep_end_time = %s", sleep_end_time)
    return sleep_end_time

def get_internal_wifi_mode_default():
    internal_wifi_mode = "Enable"
    return internal_wifi_mode

def init_ext_eth_config_file():
    root_dir = os.path.dirname(sys.modules['__main__'].__file__)
    led_config_dir = os.path.join(root_dir, led_params_config_folder_name)
    with open(os.path.join(led_config_dir, "ext_eth_setting.dat"), "w") as f:
        f.write("static_ip:xxx.xxx.xxx.xxx/24\n")
        f.write("gateway:xxx.xxx.xxx.xxx\n")
        f.write("dns:xxx.xxx.xxx.xxx\n")
        f.truncate()
        f.flush()
        os.popen("sync")

def get_ext_eth_info_default():
    root_dir = os.path.dirname(sys.modules['__main__'].__file__)
    led_config_dir = os.path.join(root_dir, led_params_config_folder_name)
    ext_eth_info_maps = {}

    if os.path.exists(os.path.join(led_config_dir, ext_eth_config_file_name)) is False:
        init_ext_eth_config_file()

    with open(os.path.join(led_config_dir, ext_eth_config_file_name), "r") as f:
        lines = f.readlines()

    for line in lines:
        if line.startswith("static_ip"):
            ext_eth_info_maps["static_ip"] = line.strip().split(":")[1].split("/")[0]
        elif line.startswith("gateway"):
            ext_eth_info_maps["gateway"] = line.strip().split(":")[1]
        elif line.startswith("dns"):
            ext_eth_info_maps["dns"] = line.strip().split(":")[1]

    return ext_eth_info_maps

def get_ext_eth_method_default():
    root_dir = os.path.dirname(sys.modules['__main__'].__file__)
    led_config_dir = os.path.join(root_dir, led_params_config_folder_name)

    if os.path.exists(os.path.join(led_config_dir, ext_eth_config_file_name)) is False:
        init_ext_eth_config_file()

    with open(os.path.join(led_config_dir, ext_eth_config_file_name), "r") as f:
        lines = f.readlines()

    for line in lines:
        if "xxx" in line:
            return "DHCP"


    return "STATIC"

def init_cms_config_file():
    root_dir = os.path.dirname(sys.modules['__main__'].__file__)
    led_config_dir = os.path.join(root_dir, led_params_config_folder_name)
    with open(os.path.join(led_config_dir, cms_config_file_name), "w") as f:
        f.write("cms_mode=0\n")
        f.write("http://www.gis.com.tw\n")

        f.truncate()
        f.flush()
        os.popen("sync")

def get_cms_mode_default():
    log.debug("get_cms_mode_default")

    led_config_dir = os.path.join(root_dir, led_params_config_folder_name)

    if os.path.exists(os.path.join(led_config_dir, cms_config_file_name)) is False:
        init_cms_config_file()

    with open(os.path.join(led_config_dir, cms_config_file_name), "r") as f:
        lines = f.readlines()

    for line in lines:
        log.debug("test line : %s", line)
        if line.startswith("cms_mode"):
            log.debug("test line : %s", line.strip().split("cms_mode=")[1] )
            if line.strip().split("cms_mode=")[1] == "0":
                return "Default"

    return "Custom"

def get_cms_url_default():

    led_config_dir = os.path.join(root_dir, led_params_config_folder_name)
    cms_info_maps = {}

    if os.path.exists(os.path.join(led_config_dir, cms_config_file_name)) is False:
        init_cms_config_file()

    with open(os.path.join(led_config_dir, cms_config_file_name), "r") as f:
        lines = f.readlines()

    for line in lines:
        if line.startswith("http"):
            cms_info_maps["custom_url"] = line.strip()

    return cms_info_maps
