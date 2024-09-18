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
    log.debug("type : ", type)
    if 'anapex' in type:
        self.media_engine.led_video_params.set_icled_type(0)
    elif 'aos' in type:
        self.media_engine.led_video_params.set_icled_type(1)


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
    log.debug("To be Implamented!")


def adjust_frame_height(self, h):
    log.debug("To be Implamented!")


def adjust_icled_type_gain(self, data):
    tmp = data.split(";")
    for s in tmp:
        if "icled_type" in s:
            s_icled_type = s.split(":")[1]
            if 'anapex' in s_icled_type:
                i_icled_type = 0
            elif 'aos' in s_icled_type:
                i_icled_type = 1
            else:
                i_icled_type = 0
            self.media_engine.led_video_params.set_icled_type(i_icled_type)
        elif "r_gain" in s:
            i_r_gain = int(s.split(":")[1])
            self.media_engine.led_video_params.set_led_red_gain(i_r_gain)
        elif "g_gain" in s:
            i_g_gain = int(s.split(":")[1])
            self.media_engine.led_video_params.set_led_red_gain(i_g_gain)
        elif "b_gain" in s:
            i_b_gain = int(s.split(":")[1])
            self.media_engine.led_video_params.set_led_red_gain(i_b_gain)


def adjust_still_image_period(self, data):
    period = data.split(":")[1]
    i_period = int(period) * 1000
    self.media_engine.led_video_params.set_still_image_period(i_period)


def adjust_res_fps(self, data):
    log.debug("data : %s", data)
    s_data = data.split(";")
    for s in s_data:
        if 'fr_w' in s:
            frame_width = s.split(":")[1]
            if int(frame_width) != self.media_engine.led_video_params.get_output_frame_width():
                log.debug("set_output_frame_width : %s", frame_width)
                self.media_engine.led_video_params.set_output_frame_width(int(frame_width))
        elif 'fr_h' in s:
            frame_height = s.split(":")[1]
            if int(frame_height) != self.media_engine.led_video_params.get_output_frame_height():
                log.debug("set_output_frame_height : %s", frame_height)
                self.media_engine.led_video_params.set_output_frame_height(int(frame_height))
        elif 'fr_fps' in s:
            frame_fps = s.split(":")[1]
            if int(frame_fps) != self.media_engine.led_video_params.get_output_fps():
                log.debug("set_output_fps %s", frame_fps)
                self.media_engine.led_video_params.set_output_fps(int(frame_fps))


def adjust_audio_preview(self, data):
    log.debug("data : %s", data)
    s_data = data.split(";")
    for s in s_data:
        if 'audio_enable' in s:
            audio_enable = s.split(":")[1]
            if int(audio_enable) != self.media_engine.led_video_params.get_play_with_audio():
                log.debug("set audio_enable : %s", audio_enable)
                self.media_engine.led_video_params.set_play_with_audio(int(audio_enable))
        elif 'preview_enable' in s:
            preview_enable = s.split(":")[1]
            if int(preview_enable) != self.media_engine.led_video_params.get_play_with_preview():
                log.debug("set preview_enable : %s", preview_enable)
                self.media_engine.led_video_params.set_play_with_preview(int(preview_enable))


def adjust_media_crop(self, data):
    log.debug("data : %s", data)
    s_data = data.split(";")
    for s in s_data:
        if 'media_crop_start_x' in s:
            media_file_start_x = s.split(":")[1]
            if int(media_file_start_x) != self.media_engine.led_video_params.get_media_file_start_x():
                log.debug("set media_file_start_x : %s", media_file_start_x)
                self.media_engine.led_video_params.set_media_file_start_x(int(media_file_start_x))
        elif 'media_crop_start_y' in s:
            media_file_start_y = s.split(":")[1]
            if int(media_file_start_y) != self.media_engine.led_video_params.get_media_file_start_y():
                log.debug("set media_file_start_y : %s", media_file_start_y)
                self.media_engine.led_video_params.set_media_file_start_y(int(media_file_start_y))
        elif 'media_crop_w' in s:
            media_file_crop_w = s.split(":")[1]
            if int(media_file_crop_w) != self.media_engine.led_video_params.get_media_file_crop_w():
                log.debug("set media_file_crop_w : %s", media_file_crop_w)
                self.media_engine.led_video_params.set_media_file_crop_w(int(media_file_crop_w))
        elif 'media_crop_h' in s:
            media_file_crop_h = s.split(":")[1]
            if int(media_file_crop_h) != self.media_engine.led_video_params.get_media_file_crop_h():
                log.debug("set media_file_crop_h : %s", media_file_crop_h)
                self.media_engine.led_video_params.set_media_file_crop_h(int(media_file_crop_h))


def adjust_hdmi_crop(self, data):
    log.debug("data : %s", data)
    s_data = data.split(";")
    for s in s_data:
        if 'hdmi_in_crop_start_x' in s:
            hdmi_in_start_x = s.split(":")[1]
            if int(hdmi_in_start_x) != self.media_engine.led_video_params.get_hdmi_in_start_x():
                log.debug("set hdmi_in_start_x : %s", hdmi_in_start_x)
                self.media_engine.led_video_params.set_hdmi_in_start_x(int(hdmi_in_start_x))
        elif 'hdmi_in_crop_start_y' in s:
            hdmi_in_start_y = s.split(":")[1]
            if int(hdmi_in_start_y) != self.media_engine.led_video_params.get_hdmi_in_start_y():
                log.debug("set hdmi_in_start_y : %s", hdmi_in_start_y)
                self.media_engine.led_video_params.set_hdmi_in_start_y(int(hdmi_in_start_y))
        elif 'hdmi_in_crop_w' in s:
            hdmi_in_crop_w = s.split(":")[1]
            if int(hdmi_in_crop_w) != self.media_engine.led_video_params.get_hdmi_in_crop_w():
                log.debug("set hdmi_in_crop_w : %s", hdmi_in_crop_w)
                self.media_engine.led_video_params.set_hdmi_in_crop_w(int(hdmi_in_crop_w))
        elif 'hdmi_in_crop_h' in s:
            hdmi_in_crop_h = s.split(":")[1]
            if int(hdmi_in_crop_h) != self.media_engine.led_video_params.get_hdmi_in_crop_h():
                log.debug("set hdmi_in_crop_h : %s", hdmi_in_crop_h)
                self.media_engine.led_video_params.set_hdmi_in_crop_h(int(hdmi_in_crop_h))


def play_single_file(self, data):
    log.debug("data : %s", data)

    for btn in self.ui_funcs_select_frame.btn_list:
        log.debug("btn : %s", btn.text())
        if btn.text() == 'Media_Files':
            btn.click()
            break
    file_uri = internal_media_folder + '/' + data
    log.debug("file_uri : %s", file_uri)
    self.media_engine.single_play(file_uri)


def play_playlist(self, data):
    log.debug("data : %s", data)

    for btn in self.ui_funcs_select_frame.btn_list:
        log.debug("btn : %s", btn.text())
        if btn.text() == 'Media_Files':
            btn.click()
            break
    playlist = internal_media_folder + PlaylistFolder + data
    log.debug("playlist : %s", playlist)
    self.media_engine.play_playlist(playlist)


def play_hdmi_in(self, data):
    log.debug("data : %s", data)
    # log.debug("demo_start_hdmi_in")
    for btn in self.ui_funcs_select_frame.btn_list:
        log.debug("btn : %s", btn.text())
        if btn.text() == 'HDMI_In':
            btn.click()
            break
    self.media_engine.hdmi_in_play()

def play_cms(self, data):
    log.debug("data : %s", data)
    # log.debug("demo_start_hdmi_in")
    for btn in self.ui_funcs_select_frame.btn_list:
        log.debug("btn : %s", btn.text())
        if btn.text() == 'CMS':
            btn.click()
            break
    self.right_frame_page_list[3].cms_start_btn.click()


cmd_function_map = {
    "play_file": play_single_file,
    "play_playlist": play_playlist,
    "play_hdmi_in": play_hdmi_in,
    "play_cms": play_cms,
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
    "set_frame_rate_res_values": adjust_res_fps,
    "set_image_period_values": adjust_still_image_period,
    "set_icled_type_gain": adjust_icled_type_gain,
    "set_audio_preview_mode": adjust_audio_preview,
    "set_media_crop_values": adjust_media_crop,
    "set_hdmi_crop_values": adjust_hdmi_crop,
}

""" handle the command from LocalServer"""


def parser_cmd_from_qlocalserver(self, data: dict) -> None:
    log.debug("data : %s", data)
    log.debug("len(self.fpga_list) : %d", len(self.fpga_list))
    try:
        for key in data:
            log.debug("i : %s, v: %s", key, data[key])
            self.cmd_function_map[key](self, data[key])
    except Exception as e:
        log.error(e)
