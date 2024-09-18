import os
import signal
import subprocess
import time
from audioop import reverse

from PyQt5.QtCore import QSize

from PyQt5.QtGui import QFont, QIcon
from PyQt5.QtWidgets import QWidget, QLabel, QGridLayout, QPushButton, QLineEdit, QComboBox, QGroupBox, QHBoxLayout

from astral_hashmap import City_Map
from global_def import log, icled_type, sleep_mode, frame_brightness_alog, MIN_FRAME_BRIGHTNESS, MAX_FRAME_BRIGHTNESS, \
    MIN_FRAME_GAMMA, MAX_FRAME_GAMMA
from media_engine.media_engine import MediaEngine
from qt_ui_style.button_qss import QFont_Style_Default, \
    QFont_Style_Size_L, QFont_Style_Size_M


class SystemPage(QWidget):
    def __init__(self, _main_window, _frame: QWidget, _name: str, media_engine: MediaEngine, **kwargs):
        super(SystemPage, self).__init__()
        log.debug("CMS Page Init")
        self.main_windows = _main_window
        self.frame = _frame
        self.media_engine = media_engine
        self.name = _name
        self.page_name_label = None
        self.grid_layout = None
        self.hotspot_name = ''

        self.groupbox_hotspot_settings = None
        self.groupbox_hotspot_settings_gridlayout = None

        self.wireless_devices = []
        self.label_wireless_devices = None
        self.combobox_wireless_devices = None
        # self. = None

        self.init_ui()

        self.get_wireless_device_name()


    def init_ui(self):
        ''' Wifi Hotspot Settings '''
        self.groupbox_hotspot_settings = QGroupBox("Hotspot Settings")
        self.groupbox_hotspot_settings_gridlayout = QGridLayout()

        self.label_wireless_devices = QLabel(self.groupbox_hotspot_settings)
        self.label_wireless_devices.setText("Wireless Devices:")

        self.combobox_wireless_devices = QComboBox(self.groupbox_hotspot_settings)
        self.wireless_devices = self.get_wireless_device_name()
        self.combobox_wireless_devices.addItems(self.wireless_devices)

        self.groupbox_hotspot_settings_gridlayout.addWidget(self.label_wireless_devices, 0, 0)
        self.groupbox_hotspot_settings_gridlayout.addWidget(self.combobox_wireless_devices, 0, 1)

        self.groupbox_hotspot_settings.setLayout(self.groupbox_hotspot_settings_gridlayout)

        self.grid_layout =  QGridLayout()
        self.grid_layout.addWidget(self.groupbox_hotspot_settings, 0, 0)
        self.setLayout(self.grid_layout)

        self.setFont(QFont(QFont_Style_Default, QFont_Style_Size_M))

        log.debug("System Page init_ui end")


    def get_wireless_device_name(self) -> []:

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
        return real_devs


    def get_hotspot_name(self):
        pass
