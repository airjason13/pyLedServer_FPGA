import utils.log_utils
from astral_hashmap import *
from datetime import datetime, time
from zoneinfo import ZoneInfo
from global_def import *
from utils import jholiday, astral_utils
import time


def check_daymode_nightmode(self, sunrise_time, sunset_time, now):
    if self.brightness_test_log is True:
        file_uri = os.getcwd() + "/test_log.dat"
        f = open(file_uri, "a+")

    if sunrise_time < now < sunset_time:
        if self.brightness_test_log is True:
            log.debug("day mode")

        # log.debug("day_mode_brightness = %d", day_mode_brightness)
        if self.media_engine.led_video_params.get_led_brightness() \
                != self.media_engine.led_video_params.get_day_mode_frame_brightness():
            self.media_engine.led_video_params.set_led_brightness(
                self.media_engine.led_video_params.get_day_mode_frame_brightness())

            '''clients = self.clients
            for c in clients:
                c.send_cmd(cmd_set_frame_brightness,
                           self.cmd_seq_id_increase(),
                           str(self.media_engine.media_processor.video_params.get_frame_brightness()))'''
        if self.brightness_test_log is True:
            log.debug("self.media_engine.led_video_params.frame_brightness = %d",
                      self.media_engine.led_video_params.get_led_brightness())

            data = self.city + " " + now.strftime("%Y-%m-%d %H:%M:%S")
            str_sunrise_time = sunrise_time.strftime("%Y-%m-%d %H:%M:%S")
            str_sunset_time = sunset_time.strftime("%Y-%m-%d %H:%M:%S")
            f.write(data + "==> day mode" + "==>br:" +
                    str(self.media_engine.led_video_params.get_led_brightness()) +
                    "==>sunrisetime:" + str_sunrise_time +
                    "==>sunrisetime:" + str_sunset_time + "\n")
            f.flush()
    else:
        if self.brightness_test_log is True:
            log.debug("night mode")
        if self.media_engine.led_video_params.get_led_brightness() \
                != self.media_engine.led_video_params.get_night_mode_frame_brightness():
            self.media_engine.led_video_params.set_led_brightness(
                self.media_engine.led_video_params.get_night_mode_frame_brightness())


            '''clients = self.clients
            for c in clients:
                c.send_cmd(cmd_set_frame_brightness,
                           self.cmd_seq_id_increase(),
                           str(self.media_engine.media_processor.video_params.get_frame_brightness()))'''
        if self.brightness_test_log is True:
            log.debug("self.media_engine.led_video_params.get_led_brightness() = %d",
                      self.media_engine.led_video_params.get_led_brightness())

            data = self.city + " " + now.strftime("%Y-%m-%d %H:%M:%S")
            str_sunrise_time = sunrise_time.strftime("%Y-%m-%d %H:%M:%S")
            str_sunset_time = sunset_time.strftime("%Y-%m-%d %H:%M:%S")
            f.write(data + "==> night mode" + "==>br:" +
                    str(self.media_engine.led_video_params.get_led_brightness()) +
                    "==>sunrisetime:" + str_sunrise_time +
                    "==>sunrisetime:" + str_sunset_time + "\n")
            f.flush()
    if self.brightness_test_log is True:
        f.close()


def client_reboot_timer(self):
    if 'Disable' in self.reboot_mode:
        return
    # log.debug("client_reboot_timer")
    i_reboot_hour = int(self.reboot_time.split(":")[0])
    i_reboot_min = int(self.reboot_time.split(":")[1])
    # log.debug("client_reboot_timer : %d:%d", i_reboot_hour, i_reboot_min)
    now = datetime.now().replace(tzinfo=ZoneInfo(utils.astral_utils.get_time_zone(self.city)))
    start_client_reboot_time = now.replace(hour=i_reboot_hour, minute=i_reboot_min, second=0, microsecond=0)
    end_client_reboot_time = now.replace(hour=i_reboot_hour, minute=i_reboot_min + 1, second=0, microsecond=0)
    if start_client_reboot_time < now < end_client_reboot_time:
        log.debug("It's time to trigger reboot cmd!")
        self.client_reboot_flags = True
        try:
            for i in range(10):
                self.server_broadcast_client_reboot()
                time.sleep(0.1)
        except Exception as e:
            log.debug(e)
        self.client_reboot_flags = False
        time.sleep(30)
        if platform.machine() in ('arm', 'arm64', 'aarch64'):
            os.popen("reboot")
        else:
            log.debug("SYSTEM fake reboot")


def is_sleep_time(self, now, light_start_time, light_end_time):
    # midnight_time = now.replace(hour=23, minute=59, second=59, microsecond=0)
    if light_end_time > light_start_time:
        if now < light_start_time or now > light_end_time:
            return True
    else:
        if light_end_time < now < light_start_time:
            return True
    return False


def check_brightness_by_date_timer(self):
    log.debug("")
    if jholiday.today_is_holiday_or_not() is True:
        log.debug("holiday, set brightness 0")
        self.media_engine.led_video_params.set_led_brightness(0)
        clients = self.clients
        '''for c in clients:
            c.send_cmd(cmd_set_frame_brightness,
                       self.cmd_seq_id_increase(),
                       str(self.media_engine.media_processor.video_params.get_frame_brightness()))'''
        return

    if self.brightness_test_log is True:
        log.debug("frame_brightness_algorithm = %d",
                  self.media_engine.led_video_params.get_frame_brightness_algo())
    if self.media_engine.led_video_params.get_frame_brightness_algo() \
            == frame_brightness_alog.fix_mode:
        '''clients = self.clients
        for c in clients:
            c.send_cmd(cmd_set_frame_brightness,
                       self.cmd_seq_id_increase(),
                       str(self.media_engine.media_processor.video_params.get_frame_brightness()))'''
        if self.brightness_test_log is True:
            log.debug("frame_brightness_adjust.fix_mode")
        return
    self.city = City_Map[self.media_engine.led_video_params.get_target_city_index()].get("City")
    sunrise_time, sunset_time = utils.astral_utils.get_sun_times(self.city)
    # now = datetime.now().replace(tzinfo=(pytz.timezone(utils.astral_utils.get_time_zone(self.city))))
    # pytz have +08:06 ??!! the min is 06??? strange!!!
    now = datetime.now().replace(tzinfo=ZoneInfo(utils.astral_utils.get_time_zone(self.city)))

    light_start_time = None
    light_end_time = None

    log.debug("get_sleep_mode_enable : %d",
    self.media_engine.led_video_params.get_sleep_mode_enable())
    if self.media_engine.led_video_params.get_sleep_mode_enable() == 1:
        # log.debug("Sleep Mode is True")
        # sleep start ==> train start
        light_start_time = now.replace(hour=self.i_sleep_end_time_hour, minute=self.i_sleep_end_time_min,
                                       second=0, microsecond=0)
        # sleep start ==> light_end
        light_end_time = now.replace(hour=self.i_sleep_start_time_hour, minute=self.i_sleep_start_time_min,
                                     second=0, microsecond=0)
    else:
        if self.brightness_test_log is True:
            log.debug("Sleep Mode is False")
        pass

    # now = test_hour.replace(hour=self.test_hour, minute=self.test_min, second=0, microsecond=0)

    # sunrise_time, sunset_time = utils.astral_utils.get_sun_times(self.city)
    if self.brightness_test_log is True:
        log.debug("sunrise_time: %s", sunrise_time)
        log.debug("sunset_time: %s", sunset_time)
    with open(os.getcwd() + "/static/sun_time.dat", "w+") as f:
        file_content = "sunrise_time:" + sunrise_time.strftime("%Y-%m-%d %H:%M:%S") + \
                       "\n" + "sunset_time:" + sunset_time.strftime("%Y-%m-%d %H:%M:%S")
        f.write(file_content)
        f.close()
    # train info stop
    if light_start_time is not None and light_end_time is not None:
        # if now < light_start_time or now > light_end_time:
        if self.is_sleep_time(now, light_start_time, light_end_time) is True:
            if self.brightness_test_log is True:
                file_uri = os.getcwd() + "/test_log.dat"
                f = open(file_uri, "a+")
                log.debug("sleep mode")
            if self.media_engine.led_video_params.get_led_brightness() \
                    != self.media_engine.led_video_params.get_sleep_mode_frame_brightness():
                self.media_engine.led_video_params.set_led_brightness(
                    self.media_engine.led_video_params.get_sleep_mode_frame_brightness())

                '''clients = self.clients
                for c in clients:
                    c.send_cmd(cmd_set_frame_brightness,
                               self.cmd_seq_id_increase(),
                               str(self.media_engine.media_processor.video_params.get_frame_brightness()))'''
            if self.brightness_test_log is True:
                log.debug("self.media_engine.led_video_params.get_led_brightness() = %d",
                          self.media_engine.led_video_params.get_led_brightness())

                data = self.city + " " + now.strftime("%Y-%m-%d %H:%M:%S")
                str_sunrise_time = sunrise_time.strftime("%Y-%m-%d %H:%M:%S")
                str_sunset_time = sunset_time.strftime("%Y-%m-%d %H:%M:%S")
                f.write(data + "==> sleep mode" + "==>br:" +
                        str(self.media_engine.led_video_params.get_led_brightness()) +
                        "==>sunrisetime:" + str_sunrise_time +
                        "==>sunrisetime:" + str_sunset_time + "\n")
                f.flush()
                f.close()
        else:
            self.check_daymode_nightmode(sunrise_time, sunset_time, now)
    else:
        self.check_daymode_nightmode(sunrise_time, sunset_time, now)
