import os
import platform
import re
import pyudev
from pyudev import Context, Monitor, MonitorObserver
import signal
import subprocess
import time
from audioop import reverse

from PyQt5.QtCore import QSize

from PyQt5.QtGui import QFont, QIcon
from PyQt5.QtWidgets import QWidget, QLabel, QGridLayout, QPushButton, QLineEdit, QComboBox, QGroupBox, QHBoxLayout, \
    QRadioButton

from astral_hashmap import City_Map
from global_def import log, root_dir
from media_engine.media_engine import MediaEngine
from qt_ui_style.button_qss import QFont_Style_Default, QFont_Style_Size_L


class SystemPage(QWidget):

    WLAN0_ENABLE_TAG = "WLAN0_ENABLE"
    SSID_DEFAULT_TAG = "SSID_DEFAULT"
    BAND_DEFAULT_TAG = "BAND_DEFAULT"
    CHANNEL_DEFAULT_TAG = "CHANNEL_DEFAULT"

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

        self.label_wireless_bands = None

        self.device_map = {}
        self.sync_device_phy_map()

        self.wireless_devices = []
        self.label_wireless_devices = None
        self.combobox_wireless_devices = None
        self.label_wireless_bands = None
        self.wireless_band_list = []
        self.combobox_wireless_bands = None
        self.label_wireless_channels = None
        self.wireless_channel_list = []
        self.combobox_wireless_channels = None
        self.radiobtn_internal_wifi_disable = None
        self.btn_set_wireless = None
        self.label_hotspot_ssid = None
        self.lineedit_hotspot_ssid = None

        # self.combobox_wireless_bands = QComboBox(self.groupbox_hotspot_settings)
        # self.wireless_band_list.append("1")
        # self.combobox_wireless_bands.addItems(self.wireless_band_list)

        self.init_ui()

        self.get_wireless_device_name()
        self.sync_device_phy_map()
        self.init_usb_monitor()


    def init_usb_monitor(self):
        context = Context()
        monitor = Monitor.from_netlink(context)
        monitor.filter_by(subsystem='usb')
        observer = MonitorObserver(monitor,
                                   callback=self.show_device_event,
                                   name='monitor-observer')
        observer.daemon
        observer.start()

    def show_device_event(self, device):
        log.debug('background event {0.action}: {0.device_path}'.format(device))


    def init_ui(self):
        ''' Wifi Hotspot Settings '''
        self.groupbox_hotspot_settings = QGroupBox("Hotspot Settings")
        self.groupbox_hotspot_settings_gridlayout = QGridLayout()

        self.radiobtn_internal_wifi_disable = QRadioButton(self.groupbox_hotspot_settings)
        self.radiobtn_internal_wifi_disable.setText("OnBoard Wifi Disable")
        self.radiobtn_internal_wifi_disable.clicked.connect(self.radiobtn_internal_wifi_disable_clicked)
        # self.radiobtn_internal_wifi_disable.isChecked()

        self.label_wireless_devices = QLabel(self.groupbox_hotspot_settings)
        self.label_wireless_devices.setText("Wireless Devices:")

        self.combobox_wireless_devices = QComboBox(self.groupbox_hotspot_settings)
        self.wireless_devices = self.get_wireless_device_name()
        self.combobox_wireless_devices.addItems(self.wireless_devices)


        self.label_wireless_bands = QLabel(self.groupbox_hotspot_settings)
        self.label_wireless_bands.setText("Hotspot Bands:")

        self.combobox_wireless_bands = QComboBox(self.groupbox_hotspot_settings)
        self.wireless_band_list.append("2.4G")
        self.wireless_band_list.append("5G")
        self.combobox_wireless_bands.addItems(self.wireless_band_list)
        self.combobox_wireless_bands.currentIndexChanged.connect(self.change_wireless_bands)


        self.label_wireless_channels = QLabel(self.groupbox_hotspot_settings)
        self.label_wireless_channels.setText("Hotspot Channels:")

        self.combobox_wireless_channels = QComboBox(self.groupbox_hotspot_settings)
        self.wireless_channel_list = None
        self.wireless_channel_list = []
        self.combobox_wireless_channels.clear()
        if "2.4" in self.combobox_wireless_bands.itemText(
            self.combobox_wireless_bands.currentIndex()):
            for chan in self.get_24g_channel_list(phy_device="phy0"):
                self.wireless_channel_list.append(chan)
        else:
            for chan in self.get_5g_channel_list(phy_device="phy0"):
                self.wireless_channel_list.append(chan)
        self.combobox_wireless_channels.addItems(self.wireless_channel_list)

        self.label_hotspot_ssid = QLabel(self.groupbox_hotspot_settings)
        self.label_hotspot_ssid.setText("Hotspot SSID:")

        self.lineedit_hotspot_ssid = QLineEdit(self.groupbox_hotspot_settings)
        self.lineedit_hotspot_ssid.setText("GISTLED")


        self.btn_set_wireless = QPushButton(self.groupbox_hotspot_settings)
        self.btn_set_wireless.setText("Set Hotspot")
        self.btn_set_wireless.clicked.connect(self.btn_set_wireless_clicked)

        self.groupbox_hotspot_settings_gridlayout.addWidget(self.radiobtn_internal_wifi_disable, 0, 0)
        self.groupbox_hotspot_settings_gridlayout.addWidget(self.label_wireless_devices, 1, 0)
        self.groupbox_hotspot_settings_gridlayout.addWidget(self.combobox_wireless_devices, 1, 1)

        self.groupbox_hotspot_settings_gridlayout.addWidget(self.label_wireless_bands, 2, 0)
        self.groupbox_hotspot_settings_gridlayout.addWidget(self.combobox_wireless_bands, 2, 1)

        self.groupbox_hotspot_settings_gridlayout.addWidget(self.label_wireless_channels, 3, 0)
        self.groupbox_hotspot_settings_gridlayout.addWidget(self.combobox_wireless_channels, 3, 1)

        self.groupbox_hotspot_settings_gridlayout.addWidget(self.label_hotspot_ssid, 4, 0)
        self.groupbox_hotspot_settings_gridlayout.addWidget(self.lineedit_hotspot_ssid, 4, 1)

        self.groupbox_hotspot_settings_gridlayout.addWidget(self.btn_set_wireless, 5, 1)

        self.groupbox_hotspot_settings.setLayout(self.groupbox_hotspot_settings_gridlayout)

        self.grid_layout =  QGridLayout()
        self.grid_layout.addWidget(self.groupbox_hotspot_settings, 0, 0)
        self.setLayout(self.grid_layout)

        self.setFont(QFont(QFont_Style_Default, QFont_Style_Size_L))

        log.debug("System Page init_ui end")


    def change_wireless_bands(self):
        log.debug("combobox_wireless_bands : %s", self.combobox_wireless_bands.itemText(
            self.combobox_wireless_bands.currentIndex()))
        self.wireless_channel_list = None
        self.wireless_channel_list = []
        self.combobox_wireless_channels.clear()
        if "2.4" in self.combobox_wireless_bands.itemText(
            self.combobox_wireless_bands.currentIndex()):
            for chan in self.get_24g_channel_list(phy_device="phy0"):
                self.wireless_channel_list.append(chan)
        else:
            for chan in self.get_5g_channel_list(phy_device="phy0"):
                self.wireless_channel_list.append(chan)
        self.combobox_wireless_channels.addItems(self.wireless_channel_list)

    def radiobtn_internal_wifi_disable_clicked(self):
        log.debug("")
        if platform.machine() in ('arm', 'arm64', 'aarch64'):
            log.debug("self.device_map: %s", self.device_map)
            for k, v in self.device_map.items():
                if v == "phy0":
                    wlan_device = k
            log.debug("wlan_device: %s", wlan_device)
            if self.radiobtn_internal_wifi_disable.isChecked() is True:
                log.debug("Disable Wifi")
                os.popen("ifconfig {} down".format(wlan_device))
            else:
                log.debug("Enable Wifi")
                os.popen("ifconfig {} up".format(wlan_device))


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


    def get_24g_channel_list(self, phy_device: str):
        output = os.popen("iw {} info | grep dBm ".format(phy_device)).read()
        tmp = re.sub(r"[\t\* ]*", "", output)
        # log.debug("tmp : %s", tmp)
        tmp_list = tmp.strip().split("\n")
        channel_24g_list = []
        for chan in tmp_list:
            if chan.startswith("2"):
                channel_24g_list.append(chan)
        log.debug("channel_24g_list: %s", channel_24g_list)
        return channel_24g_list

    def get_5g_channel_list(self, phy_device: str):
        output = os.popen("iw {} info | grep dBm ".format(phy_device)).read()
        tmp = re.sub(r"[\t\* ]*", "", output)
        # log.debug("tmp : %s", tmp)
        tmp_list = tmp.strip().split("\n")
        channel_5g_list = []
        for chan in tmp_list:
            if chan.startswith("5"):
                channel_5g_list.append(chan)
        log.debug("channel_5g_list: %s", channel_5g_list)
        return channel_5g_list

    def get_hotspot_name(self):
        pass

    def sync_device_phy_map(self):
        self.device_map = {}
        phy_dev = ""
        if_name = ""
        output = os.popen("iw dev").read()
        log.debug("output:\n %s", output)
        output_list = output.split("\n")
        for tmp in output_list:
            if "phy" in tmp:
                phy_number = tmp.strip("phy#")
                log.debug("phy_number: %s", phy_number)
                phy_dev = "phy{}".format(str(phy_number))
                log.debug("phy_dev : %s", phy_dev)
            if "Interface" in tmp:
                if_name = tmp.strip().split(" ")[1]
                log.debug("if_name: %s", if_name)

            if len(if_name) != 0 and len(phy_dev) != 0:
                self.device_map[if_name] = phy_dev
                phy_dev = ""
                if_name = ""

        # device_map["wlo1"] = "phy0"
        # device_map["xxx1"] = "phy1"
        # device_map = {"wlo1": "phy0", "xxx2": "phy1"}
        # log.debug("phy of wlo1: %s", device_map.get("wlo1"))
        log.debug("device_map : %s", self.device_map)

    def btn_set_wireless_clicked(self):
        log.debug("")
        log.debug("combobox_wireless_devices : %s", self.combobox_wireless_devices.itemText(
            self.combobox_wireless_devices.currentIndex()))
        log.debug("combobox_wireless_bands : %s", self.combobox_wireless_bands.itemText(
            self.combobox_wireless_bands.currentIndex()))
        log.debug("combobox_wireless_channels : %s", self.combobox_wireless_channels.itemText(
            self.combobox_wireless_channels.currentIndex()))

        target_device = self.combobox_wireless_devices.itemText(self.combobox_wireless_devices.currentIndex())
        tmp_band = self.combobox_wireless_bands.itemText(self.combobox_wireless_bands.currentIndex())
        if tmp_band == "2.4G":
            target_band = "bg"
        else:
            target_band = "a"
        tmp_channel = self.combobox_wireless_channels.itemText(self.combobox_wireless_channels.currentIndex())
        target_channel = tmp_channel.split("[")[1].split("]")[0]
        target_ssid = self.lineedit_hotspot_ssid.text()

        log.debug("target_device: %s", target_device)
        log.debug("target_band: %s", target_band)
        log.debug("target_channel: %s", target_channel)
        log.debug("target_ssid: %s", target_ssid)

        self.modify_wifi_hotspot(target_device,
                                 target_band,
                                 target_channel,
                                 target_ssid
                                 )

    def modify_wifi_hotspot(self, device, bands, channels, ssid):
        log.debug("device: %s", device)
        log.debug("bands: %s", bands)
        log.debug("channels: %s", channels)
        log.debug("ssid: %s", ssid)
        lines = []
        led_config_dir = os.path.join(root_dir, 'led_config')
        with open(os.path.join(led_config_dir, "setup_wlan0_hotspot.sh.sample"), "r") as f:
            lines = f.readlines()
        f.close()

        try:
            with open(os.path.join(led_config_dir, "setup_wlan0_hotspot.sh.target"), "w") as target_file:
                for line in lines:
                    if line.startswith(self.WLAN0_ENABLE_TAG):
                        # line = self.WLAN0_ENABLE_TAG + "={}\n".format(device)
                        log.debug("Not Implemented for WLAN0 Enable or Not")
                    elif line.startswith(self.BAND_DEFAULT_TAG):
                        line = self.BAND_DEFAULT_TAG + "={}\n".format(bands)
                    elif line.startswith(self.CHANNEL_DEFAULT_TAG):
                        line = self.CHANNEL_DEFAULT_TAG + "={}\n".format(channels)
                    elif line.startswith(self.SSID_DEFAULT_TAG):
                        line = self.SSID_DEFAULT_TAG + "={}\n".format(ssid)
                    target_file.write(line)
                target_file.flush()
                target_file.truncate()
                target_file.close()
                os.popen("sync")
        except Exception as e:
            log.debug(e)

        if platform.machine() in ('arm', 'arm64', 'aarch64'):
            if "pi5" in platform.node():  # pi5
                log.debug("Pi 5 not implemented")
            else:  # pi4-64
                copy_cmd = "cp {} {}".format(
                                            os.path.join(led_config_dir, "setup_wlan0_hotspot.sh.target"),
                                                "/usr/bin/setup_wlan0_hotspot.sh")
                os.popen(copy_cmd)

                os.popen("sync")
                os.popen("sync")
                os.popen("sync")
                time.sleep(3)
                chmod_cmd = "chmod +x /usr/bin/setup_wlan0_hotspot.sh"
                os.popen(chmod_cmd)

                exec_cmd = "setup_wlan0_hotspot.sh"
                os.popen(exec_cmd)
                time.sleep(2)
                log.debug("setup_wlan0_hotspot ok")


        '''log.debug("default band: %s", self.get_wifi_hotspot_data(
            self.combobox_wireless_devices.itemText(self.combobox_wireless_devices.currentIndex()),
            self.BAND_DEFAULT_TAG))

        log.debug("default band: %s", self.get_wifi_hotspot_data(
            self.combobox_wireless_devices.itemText(self.combobox_wireless_devices.currentIndex()),
            self.CHANNEL_DEFAULT_TAG))

        log.debug("default band: %s", self.get_wifi_hotspot_data(
            self.combobox_wireless_devices.itemText(self.combobox_wireless_devices.currentIndex()),
            self.SSID_DEFAULT_TAG))'''




    def get_wifi_hotspot_data(self, device, tag)->str:
        log.debug("platform.node():%s", platform.node())
        led_config_dir = os.path.join(root_dir, 'led_config')
        lines = []
        try:
            if platform.machine() in ('arm', 'arm64', 'aarch64'):
                if "pi5" in platform.node():  # pi5
                    log.debug("Pi 5 not implemented")
                else:  # pi4-64
                    if self.combobox_wireless_devices.itemText(self.combobox_wireless_devices.currentIndex()) == "wlan0":
                        with open(os.path.join(led_config_dir, "setup_wlan0_hotspot.sh.sample"), "r") as f:
                            lines = f.readlines()
                        f.close()
                        log.debug("lines:%s", lines)
                        for line in lines:
                            log.debug("line:%s", line)
                            if line.startswith(tag):
                                return line.strip().split("=")[1]
                    else:
                        with open(os.path.join(led_config_dir, "setup_alfa_hotspot.sh"), "r") as f:
                            lines = f.readlines()
                        f.close()
                        log.debug("lines:%s", lines)
                        for line in lines:
                            log.debug("line:%s", line)
                            if line.startswith(tag):
                                return line.strip().split("=")[1]

            else:
                log.debug("X86 not implemented")
        except Exception as e:
            log.debug(e)
        return ""

