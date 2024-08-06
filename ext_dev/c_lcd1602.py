import time
from array import array

from PyQt5.QtCore import QThread, pyqtSignal, QDateTime, QObject, QTimer
import socket
from global_def import *


class LCD1602(QObject):
    """lcd1602 server address"""
    server_address = '/tmp/uds_socket_i2clcd7'
    '''init'''
    def __init__(self, version_tag, info, lsversion, refresh_interval_0,  **kwargs):
        super(LCD1602, self).__init__(**kwargs)

        # line 1/2 refresh interval

        self.refresh_interval_0 = refresh_interval_0

        # line 0/1 content
        data = {"tag": version_tag, "d0": info, "d1": lsversion}
        self.lcd_data_l0 = []
        self.lcd_data_l0.append(data)
        log.debug("%s", self.lcd_data_l0[0].get("tag"))

        self.error_inform_l0 = []
        self.lcd_data_idx = 0
        self.error_inform_idx = 0

        # refresh timer setting
        self.refresh_timer_0 = QTimer(self)
        self.refresh_timer_0.timeout.connect(self.write_lcd_l0)

    def start(self):
        if platform.machine() in ('arm', 'arm64', 'aarch64'):
            try:
                self.refresh_timer_0.start(self.refresh_interval_0)
            except Exception as e:
                log.debug(e)
        else:
            log.debug("X86 does not support LCD1602")

    def write_lcd_l0(self):
        # pass data to lcd1602_server
        if platform.machine() not in ('arm', 'arm64', 'aarch64'):
            # log.error("Not on aarch64")
            return

        try:
            if len(self.error_inform_l0) != 0:
                self.socket = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
                self.socket.connect(self.server_address)
                message = "0:0:" + self.error_inform_l0[0]
                self.socket.sendall(message.encode())
                self.socket.close()
                self.lcd_data_idx += 1
            else:
                self.socket = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
                self.socket.connect(self.server_address)
                message_line0 = "0:0:" + self.lcd_data_l0[self.lcd_data_idx].get("d0")
                self.socket.sendall(message_line0.encode())
                self.socket.close()

                self.socket = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
                self.socket.connect(self.server_address)
                message_line1 = "0:1:" + self.lcd_data_l0[self.lcd_data_idx].get("d1")
                self.socket.sendall(message_line1.encode())
                self.socket.close()

                self.lcd_data_idx += 1
                if self.lcd_data_idx >= len(self.lcd_data_l0):
                    self.lcd_data_idx = 0
        except Exception as e:
            log.error(e)

    def add_data(self, tag, data0, data1):
        data = {"tag": tag, "d0": data0, "d1": data1}
        for i in range(len(self.lcd_data_l0)):
            if self.lcd_data_l0[i].get("tag") == tag:
                self.lcd_data_l0[i].update(data)
                log.debug("%s", self.lcd_data_l0)
                return

        self.lcd_data_l0.append(data)
        log.debug("%s", self.lcd_data_l0)

    def del_data(self, tag):
        for i in range(len(self.lcd_data_l0)):
            if self.lcd_data_l0[i].get("tag") == tag:
                self.lcd_data_l0.remove(self.lcd_data_l0[i])

