import os

from astral import LocationInfo
from astral.sun import sun
from astral_hashmap import *
from _datetime import datetime
import utils.log_utils

from global_def import *

def get_sun_times(city):
	target_city = None
	for city_tmp in City_Map:
		# print(city_tmp.get("City"))
		if city_tmp.get("City") == city:
			target_city = city_tmp

	if target_city is None:
		return None, None

	city = LocationInfo(target_city.get("City"), target_city.get("Country"), target_city.get("Loc"), target_city.get("Latitude"), target_city.get("Longitude"))
	# print(city)
	# print(datetime.now(pytz.timezone(target_city.get("Loc"))))
	s = sun(city.observer, date=datetime.now(), tzinfo=city.tzinfo)
	'''print((
		f'Dawn:    {s["dawn"]}\n'
		f'Sunrise: {s["sunrise"]}\n'
		f'Noon:    {s["noon"]}\n'
		f'Sunset:  {s["sunset"]}\n'
		f'Dusk:    {s["dusk"]}\n'
	))'''

	return s["sunrise"], s["sunset"]


def get_time_zone(city):
	target_city = None
	for city_tmp in City_Map:
		# print(city_tmp.get("City"))
		if city_tmp.get("City") == city:
			target_city = city_tmp
			return target_city.get("Loc")

	if target_city is None:
		return None


def get_sleep_mode_enable():
	with open(os.getcwd() + "/astral_hashmap.py", "r") as f:
		lines = f.readlines()
	f.close()
	for line in lines:
		if "SLEEP_MODE_ENABLE" in line:
			if "True" in line:
				return True
			else:
				return False
	log.fatal("So SLEEP_MODE_ENABLE TAG!")
	return False


def get_default_city():
	return City_Map[0].get("City")


def check_city_valid(city):
	for c in City_Map:
		if c.get("City") == city:
			return True
	return False
