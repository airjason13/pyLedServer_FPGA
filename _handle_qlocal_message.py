from astral_hashmap import City_Map
from global_def import *


def adjust_gamma_value(self, gamma_value: str):
    log.debug("gamma_value : %s", gamma_value)
    for fpga in self.fpga_list:
        fpga.fpga_cmd_center.write_fpga_register(fpga.i_id, 'currentGammaTable',
                                                 str(gamma_value).replace(".", ""))


def adjust_brightness_value(self, brightness_value: str):
    log.debug("brightness_value : %s", brightness_value)
    self.media_engine.led_video_params.set_led_brightness(int(brightness_value))


def adjust_sleep_mode(self, sleep_mode_status: str):
    log.debug("sleep_mode_status : %s", sleep_mode_status)
    if "disable" in sleep_mode_status:
        self.media_engine.led_video_params.set_sleep_mode_enable(0)
    else:
        self.media_engine.led_video_params.set_sleep_mode_enable(1)


def adjust_brightness_algo(self, brightness_algo: str):
    log.debug("brightness_algo : %s", brightness_algo)
    if "Fix" in brightness_algo:
        self.media_engine.led_video_params.set_frame_brightness_algo(0)
    else:
        self.media_engine.led_video_params.set_frame_brightness_algo(1)


def adjust_target_city(self, target_city: str):
    log.debug("target_city : %s", target_city)
    for i in range(len(City_Map)):
        if City_Map[i].get('City') == target_city:
            self.media_engine.led_video_params.set_target_city_index(i)


def adjust_frame_brightness(self, data: str):
    """ data sample : fr_br:50;day_mode_fr_br:50;night_mode_fr_br:50;sleep_mode_fr_br:50 """
    tmp_str = data.split(";")
    i_day_mode_brightness = -1
    i_night_mode_brightness = -1
    i_sleep_mode_brightness = -1
    i_frame_brightness = -1
    for s in tmp_str:
        if "day_mode" in s:
            i_day_mode_brightness = int(s.split(":")[1])
            self.media_engine.led_video_params.set_day_mode_frame_brightness(int(s.split(":")[1]))
        elif "night_mode" in s:
            i_night_mode_brightness = int(s.split(":")[1])
            self.media_engine.led_video_params.set_night_mode_frame_brightness(int(s.split(":")[1]))
        elif "sleep_mode" in s:
            i_sleep_mode_brightness = int(s.split(":")[1])
            self.media_engine.led_video_params.set_sleep_mode_frame_brightness(int(s.split(":")[1]))
        else:
            i_frame_brightness = int(s.split(":")[1])
            self.media_engine.led_video_params.set_led_brightness(int(s.split(":")[1]))
    log.debug("i_frame_brightness : %d", i_frame_brightness)
    log.debug("i_day_mode_brightness : %d", i_day_mode_brightness)
    log.debug("i_night_mode_brightness : %d", i_night_mode_brightness)
    log.debug("i_sleep_mode_brightness : %d", i_sleep_mode_brightness)


def adjust_icled_type(self, type: str):
    if 'anapex' in type:
        self.media_engine.led_video_params.set_icled_type(icled_type.anapex)
    elif 'aos' in type:
        self.media_engine.led_video_params.set_icled_type(icled_type.aos)


def adjust_led_r_gain(self, red_gain: str):
    log.debug("")
    # if self.media_engine.led_video_params.get_led_red_gain():
    #    self.media_engine.led_video_params.set_led_red_gain()


def adjust_led_g_gain(self, red_gain: str):
    log.debug("")
    # if self.media_engine.led_video_params.get_led_green_gain():
    #    self.media_engine.led_video_params.set_led_green_gain()


def adjust_led_b_gain(self, red_gain: str):
    log.debug("")
    # if self.media_engine.led_video_params.get_led_blue_gain():
    #    self.media_engine.led_video_params.set_led_blue_gain()


def adjust_frame_width(self, w):
    log.debug("")


def adjust_frame_height(self, w):
    log.debug("")


def adjust_fps(self, w):
    log.debug("")


cmd_function_map = {
    "set_brightness": adjust_brightness_value,
    "set_gamma": adjust_gamma_value,
    "set_sleep_mode": adjust_sleep_mode,
    "set_brightness_algo": adjust_brightness_algo,
    "set_target_city": adjust_target_city,
    "set_frame_brightness_values_option": adjust_frame_brightness,
    "set_icled_type": adjust_icled_type,
    "set_led_r_gain": adjust_led_r_gain,
    "set_led_g_gain": adjust_led_g_gain,
    "set_led_b_gain": adjust_led_b_gain,
    "set_frame_width": adjust_frame_width,
    "set_frame_height": adjust_frame_height,
    "set_fps": adjust_fps,
}

""" handle the command from LocalServer"""


def parser_cmd_from_qlocalserver(self, data: dict) -> None:
    log.debug("data : %s", data)
    log.debug("len(self.fpga_list) : %d", len(self.fpga_list))
    for key in data:
        log.debug("i : %s, v: %s", key, data[key])
        self.cmd_function_map[key](self, data[key])
