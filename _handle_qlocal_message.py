from datetime import time
from global_def import *
from set_qstyle import *
from c_new_playlist_dialog import NewPlaylistDialog
from commands_def import *
from PyQt5 import QtCore
from global_def import *
import utils.log_utils
from astral_hashmap import *

def test_qlocal_message(self):
	log.debug("AAAAAA")


""" handle the command from qlocalserver"""
def parser_cmd_from_qlocalserver(self, data):
	if data.get("play_file"):
		now_time = time.time()
		if now_time - self.web_cmd_time < web_cmd_interval:
			log.debug("cmd too quick")
			return
		self.web_cmd_time = time.time()
		got_lock = self.web_cmd_mutex.tryLock()
		if got_lock is False:
			log.debug("Cannot get lock!")
			return
		else:
			pass
		try:
			self.func_file_contents()
			log.debug("play single file : %s!", data.get("play_file"))
			self.medialist_page.right_clicked_select_file_uri = \
				internal_media_folder + "/" + data.get("play_file")
			log.debug("file_uri :%s",
			          self.medialist_page.right_clicked_select_file_uri)
			self.media_engine.play_single_file(
				self.medialist_page.right_clicked_select_file_uri)
		except Exception as e:
			log.debug(e)
		self.web_cmd_mutex.unlock()
	elif data.get("play_cms"):
		now_time = time.time()
		if now_time - self.web_cmd_time < web_cmd_interval:
			log.debug("cmd too quick")
			return
		self.web_cmd_time = time.time()
		got_lock = self.web_cmd_mutex.tryLock()
		if got_lock is False:
			log.debug("Cannot get lock!")
			return
		else:
			pass
		try:
			log.debug("got play_cms ")
			self.func_cms_setting()
			self.cms_page.start_play_cms()
		except Exception as e:
			log.debug(e)
		self.web_cmd_mutex.unlock()
	elif data.get("play_playlist"):
		now_time = time.time()
		if now_time - self.web_cmd_time < web_cmd_interval:
			log.debug("cmd too quick")
			return
		self.web_cmd_time = time.time()
		got_lock = self.web_cmd_mutex.tryLock()
		if got_lock is False:
			log.debug("Cannot get lock!")
			return
		else:
			pass
		try:
			self.func_file_contents()
			log.debug("play playlist")
			self.media_engine.play_playlist(data.get("play_playlist"))
		except Exception as e:
			log.debug(e)
		self.web_cmd_mutex.unlock()
	elif data.get("play_hdmi_in"):
		now_time = time.time()
		if now_time - self.web_cmd_time < web_cmd_interval:
			log.debug("cmd too quick")
			return
		self.web_cmd_time = time.time()
		got_lock = self.web_cmd_mutex.tryLock()
		if got_lock is False:
			log.debug("Cannot get lock!")
			return
		else:
			pass
		try:
			self.func_hdmi_in_contents()
			if "start" in data.get("play_hdmi_in"):
				log.debug("play_hdmi_in start")
				# self.hdmi_in_page.play_action_btn.click()
				self.hdmi_in_page.send_to_led_parser()
			elif "stop" in data.get("play_hdmi_in"):
				log.debug("play_hdmi_in stop")
				self.hdmi_in_page.stop_send_to_led()

		except Exception as e:
			log.debug(e)
		self.web_cmd_mutex.unlock()
	elif data.get("play_text"):
		now_time = time.time()
		if now_time - self.web_cmd_time < web_cmd_interval:
			log.debug("cmd too quick")
			return
		self.web_cmd_time = time.time()
		got_lock = self.web_cmd_mutex.tryLock()
		if got_lock is False:
			log.debug("Cannot get lock!")
			return
		else:
			pass
		try:
			self.func_file_contents()
			log.debug("play_text")
			utils.file_utils.change_text_content(data.get("play_text"))
			self.medialist_page.right_clicked_select_file_uri = internal_media_folder + SubtitleFolder + subtitle_blank_jpg
			log.debug("file_uri :%s", self.medialist_page.right_clicked_select_file_uri)
			self.media_engine.play_single_file(self.medialist_page.right_clicked_select_file_uri)
		except Exception as e:
			log.debug(e)
		self.web_cmd_mutex.unlock()
	elif data.get("set_text_size"):
		log.debug("set_text_size")
		utils.file_utils.change_text_size(data.get("set_text_size"))
	elif data.get("set_text_speed"):
		log.debug("set_text_speed")
		utils.file_utils.change_text_speed(data.get("set_text_speed"))
	elif data.get("set_text_position"):
		log.debug("set_text_position")
		utils.file_utils.change_text_position(data.get("set_text_position"))
	elif data.get("set_text_period"):
		log.debug("set_text_period")
		utils.file_utils.change_text_period(data.get("set_text_period"))
	elif data.get("set_repeat_option"):
		log.debug("set_repeat_option")
		if data.get("set_repeat_option") == "Repeat_Random":
			self.medialist_page.play_option_repeat = repeat_option.repeat_random
			self.medialist_page.btn_repeat.setText("Repeat Random")
		elif data.get("set_repeat_option") == "Repeat_All":
			self.medialist_page.play_option_repeat = repeat_option.repeat_all
			self.medialist_page.btn_repeat.setText("Repeat All")
		elif data.get("set_repeat_option") == "Repeat_One":
			self.medialist_page.play_option_repeat = repeat_option.repeat_one
			self.medialist_page.btn_repeat.setText("Repeat One")
		elif data.get("set_repeat_option") == "Repeat_None":
			self.medialist_page.play_option_repeat = repeat_option.repeat_none
			self.medialist_page.btn_repeat.setText("Repeat None")
		self.mainwindow.repeat_option_set(self.medialist_page.play_option_repeat)
	elif data.get("set_frame_brightness_option"):
		log.debug("set_frame_brightness_option")
		self.media_engine.media_processor.set_frame_brightness_value(int(data.get("set_frame_brightness_option")))
		# print("type(self.media_engine.media_processor.video_params.get_frame_brightness()):", self.media_engine.media_processor.video_params.get_frame_brightness())
		self.hdmi_in_page.client_brightness_edit.setText(
			str(self.media_engine.media_processor.video_params.get_frame_brightness()))
		self.medialist_page.client_brightness_edit.setText(
			str(self.media_engine.media_processor.video_params.get_frame_brightness()))

		clients = self.clients
		for c in clients:
			c.send_cmd(cmd_set_frame_brightness,
			           self.cmd_seq_id_increase(),
			           str(self.media_engine.media_processor.video_params.frame_brightness))
	elif data.get("set_sleep_mode"):
		log.debug("recv : %s ", data.get("set_sleep_mode"))
		if data.get("set_sleep_mode") == "Enable":
			log.debug("sleep_mode_set_enable")
			self.media_engine.media_processor.set_sleep_mode(1)
			log.debug("sleep_mode_set_enableA")
			self.medialist_page.radiobutton_sleep_mode_enable_set()
			log.debug("sleep_mode_set_enableB")
			self.hdmi_in_page.radiobutton_sleep_mode_enable_set()
			log.debug("sleep_mode_set_enableC")
		else:
			log.debug("sleep_mode_set_disable")
			self.media_engine.media_processor.set_sleep_mode(0)
			self.medialist_page.radiobutton_sleep_mode_disable_set()
			self.hdmi_in_page.radiobutton_sleep_mode_disable_set()
		self.check_brightness_by_date_timer()
	elif data.get("set_reboot_mode"):
		log.debug("set_reboot_mode")
		reboot_time = utils.file_utils.get_reboot_time_default_from_file()
		if data.get("set_reboot_mode") == "Enable":
			log.debug("set_reboot_mode : Enable")
			utils.file_utils.set_reboot_params(True, reboot_time)
		else:
			log.debug("set_reboot_mode : Disable")
			utils.file_utils.set_reboot_params(False, reboot_time)
		self.reboot_mode = utils.file_utils.get_reboot_mode_default_from_file()
		self.reboot_time = utils.file_utils.get_reboot_time_default_from_file()
	elif data.get("set_reboot_time"):
		log.debug("set_reboot_time: %s", data.get("set_reboot_time"))
		reboot_mode = utils.file_utils.get_reboot_mode_default_from_file()
		if reboot_mode is "Enable":
			utils.file_utils.set_reboot_params(True, data.get("set_reboot_time"))
		else:
			utils.file_utils.set_reboot_params(False, data.get("set_reboot_time"))
		self.reboot_time = utils.file_utils.get_reboot_time_default_from_file()
		self.reboot_mode = utils.file_utils.get_reboot_mode_default_from_file()
	elif data.get("set_sleep_time"):
		log.debug("set_sleep_time: %s", data.get("set_sleep_time"))
		time_tmp = data.get("set_sleep_time")
		self.sleep_start_time = time_tmp.split(";")[0]
		self.sleep_end_time = time_tmp.split(";")[1]
		utils.file_utils.set_sleep_params(self.sleep_start_time, self.sleep_end_time)
		self.i_sleep_start_time_hour = int(self.sleep_start_time.split(":")[0])
		self.i_sleep_start_time_min = int(self.sleep_start_time.split(":")[1])
		self.i_sleep_end_time_hour = int(self.sleep_end_time.split(":")[0])
		self.i_sleep_end_time_min = int(self.sleep_end_time.split(":")[1])

	elif data.get("set_target_city"):
		log.debug("recv : %s ", data.get("set_target_city"))
		if utils.astral_utils.check_city_valid(data.get("set_target_city")) is False:
			log.debug("City Invalid")
			return
		# self.city = data.get("set_target_city")
		c = 0
		city_index = 0
		for city in City_Map:
			if city.get("City") == data.get("set_target_city"):
				city_index = c
				break
			c += 1
		self.medialist_page.combobox_target_city_change(city_index)
		self.city = City_Map[self.media_engine.media_processor.video_params.get_target_city_index()].get("City")

	elif data.get("set_brightness_algo"):
		log.debug("recv : %s ", data.get("set_brightness_algo"))
		if "Fix Mode" == data.get("set_brightness_algo"):
			self.medialist_page.radiobutton_client_br_method_fix_mode_set()
			self.hdmi_in_page.radiobutton_client_br_method_fix_mode_set()
		elif "Time Mode" == data.get("set_brightness_algo"):
			self.medialist_page.radiobutton_client_br_method_time_mode_set()
			self.hdmi_in_page.radiobutton_client_br_method_time_mode_set()
		elif "ALS Mode" == data.get("set_brightness_algo"):
			self.medialist_page.radiobutton_client_br_method_als_mode_set()
			self.hdmi_in_page.radiobutton_client_br_method_als_mode_set()
		elif "TEST Mode" == data.get("set_brightness_algo"):
			self.medialist_page.radiobutton_client_br_method_test_mode_set()
			self.hdmi_in_page.radiobutton_client_br_method_test_mode_set()
	elif data.get("set_frame_brightness_values_option"):
		log.debug("recv : %s", data.get("set_frame_brightness_values_option"))
		data_tmp = data.get("set_frame_brightness_values_option")
		fr_br = data_tmp.split(";")[0].split(":")[1]
		day_mode_fr_br = data_tmp.split(";")[1].split(":")[1]
		night_mode_fr_br = data_tmp.split(";")[2].split(":")[1]
		sleep_mode_fr_br = data_tmp.split(";")[3].split(":")[1]
		log.debug("fr_br : %s", fr_br)
		log.debug("day_mode_fr_br : %s", day_mode_fr_br)
		log.debug("night_mode_fr_br : %s", night_mode_fr_br)
		log.debug("sleep_mode_fr_br : %s", sleep_mode_fr_br)
		self.media_engine.media_processor.set_frame_brightness_value(int(fr_br))
		self.media_engine.media_processor.set_day_mode_frame_brightness_value(int(day_mode_fr_br))
		self.media_engine.media_processor.set_night_mode_frame_brightness_value(int(night_mode_fr_br))
		self.media_engine.media_processor.set_sleep_mode_frame_brightness_value(int(sleep_mode_fr_br))
		self.hdmi_in_page.client_brightness_edit.setText(
			str(self.media_engine.media_processor.video_params.get_frame_brightness()))
		self.medialist_page.client_brightness_edit.setText(
			str(self.media_engine.media_processor.video_params.get_frame_brightness()))
		self.hdmi_in_page.client_day_mode_brightness_edit.setText(
			str(self.media_engine.media_processor.video_params.get_day_mode_frame_brightness()))
		self.medialist_page.client_day_mode_brightness_edit.setText(
			str(self.media_engine.media_processor.video_params.get_day_mode_frame_brightness()))
		self.hdmi_in_page.client_night_mode_brightness_edit.setText(
			str(self.media_engine.media_processor.video_params.get_night_mode_frame_brightness()))
		self.medialist_page.client_night_mode_brightness_edit.setText(
			str(self.media_engine.media_processor.video_params.get_night_mode_frame_brightness()))
		self.hdmi_in_page.client_sleep_mode_brightness_edit.setText(
			str(self.media_engine.media_processor.video_params.get_sleep_mode_frame_brightness()))
		self.medialist_page.client_sleep_mode_brightness_edit.setText(
			str(self.media_engine.media_processor.video_params.get_sleep_mode_frame_brightness()))

		self.check_brightness_by_date_timer()

	elif data.get("set_ledclients_reboot_option"):
		log.debug("set_ledclients_reboot_option")
		# clients = self.clients

		self.client_reboot_flags = True
		try:
			for i in range(10):
				self.server_broadcast_client_reboot()
				time.sleep(0.1)
		except Exception as e:
			log.debug(e)
		self.client_reboot_flags = False

	elif data.get("start_color_test"):
		log.debug("start_color_test")
		clients = self.clients
		for c in clients:
			c.send_cmd(cmd_set_test_color,
			           self.cmd_seq_id_increase(),
			           str(data.get("start_color_test")))
	elif data.get("stop_color_test"):
		log.debug("stop_color_test")
		clients = self.clients
		for c in clients:
			c.send_cmd(cmd_set_test_color,
			           self.cmd_seq_id_increase(),
			           str(data.get("stop_color_test")))
	elif data.get("set_default_play_mode_option"):
		log.debug("set_default_play_mode_option")
		tmp = data.get("set_default_play_mode_option")
		default_mode = "0"
		default_params = ""
		try:
			if "none_mode" in tmp:
				default_mode = "0"
				default_params = ""
			elif "single_file_mode" in tmp:
				default_mode = "1"
				default_params = tmp.split(":")[1]
			elif "playlist_mode" in tmp:
				default_mode = "2"
				default_params = tmp.split(":")[1]
			elif "hdmi_in_mode" in tmp:
				default_mode = "3"
				default_params = ""
			elif "cms_mode" in tmp:
				default_mode = "4"
				default_params = ""
		except Exception as e:
			log.debug(e)

		str_tmp = default_mode + ":" + default_params
		log.debug("str_tmp = %s", str_tmp)

		try:
			with open(os.getcwd() + "/static/default_launch_type.dat", "w") as launch_type_config_file:
				launch_type_config_file.write(str_tmp)
				launch_type_config_file.flush()
				launch_type_config_file.truncate()
				launch_type_config_file.close()
		except Exception as e:
			log.debug(e)

	elif data.get("sync_playlist"):
		log.debug("sync_playlist")
		self.internaldef_medialist_changed()


