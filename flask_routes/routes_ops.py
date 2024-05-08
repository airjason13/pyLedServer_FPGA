import os
import sys

from astral_hashmap import City_Map
from global_def import log

led_params_config_folder_name = "led_config"
led_params_config_file_name = "led_parameters"
led_reboot_config_file_name = "reboot_config"

def init_video_params():
    content_lines = [
        "frame_brightness=50\n", "led_gamma=2.2\n", "sleep_mode_enable=1\n", "target_city_index=0\n",
        "frame_brightness_algorithm=0\n", "day_mode_frame_brightness=50\n",
        "night_mode_frame_brightness=30\n", "sleep_mode_frame_brightness=0\n",
        "frame_gamma=2.2\n", "image_period=60\n",
        "hdmi_in_start_x=0\n", "hdmi_in_start_y=0\n", "hdmi_in_crop_w=0\n", "hdmi_in_crop_h=0\n",
        "media_file_start_x=0\n", "media_file_start_y=0\n",
        "media_file_crop_w=0\n", "media_file_crop_h=0\n",
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
        "reboot_mode_enable=1\n",
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
