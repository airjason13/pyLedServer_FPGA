from global_def import *


def adjust_gamma_value(self, gamma_value: str):
    log.debug("gamma_value : %s", gamma_value)
    for fpga in self.fpga_list:
        fpga.fpga_cmd_center.write_fpga_register(fpga.i_id, 'currentGammaTable',
                                                 str(gamma_value).replace(".", ""))


def adjust_brightness_value(self, brightness_value: str):
    log.debug("brightness_value : %s", brightness_value)
    self.media_engine.led_video_params.set_led_brightness(int(brightness_value))


cmd_function_map = {
    "set_brightness": adjust_brightness_value,
    "set_gamma": adjust_gamma_value,
}

""" handle the command from qlocalserver"""


def parser_cmd_from_qlocalserver(self, data: dict) -> None:
    log.debug("data : %s", data)
    log.debug("len(self.fpga_list) : %d", len(self.fpga_list))
    for key in data:
        log.debug("i : %s, v: %s", key, data[key])
        self.cmd_function_map[key](self, data[key])
